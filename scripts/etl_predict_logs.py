"""ETL: predictions.jsonl → predict_logs PostgreSQL table.

v3.6 PR15 (Phase 2 P0 차단 해소):
서버 `_log_prediction()` 이 작성한 JSONL 을 batch 로 PostgreSQL `predict_logs`
table 에 적재. Phase 2 monitoring SQL (010~020) 이 운영 가능 상태가 됨.

설계:
- decoupled: server 는 PostgreSQL 직접 INSERT 안 함 (latency / DB 의존 차단)
- idempotent: request_id PK 충돌 시 SKIP (재실행 안전)
- alias drop: predicted_krw / price_range_low|high / total_ms 등 deprecated
  필드는 적재 안 함 (DDL 에 column 없음)
- type cast: matched/is_saatchi_warm/slug_in_warm_set → BOOLEAN, timestamp ISO →
  TIMESTAMPTZ, year_made_used → INT
- offset tracking: 마지막 ingest line offset 을 별도 file 에 저장 (재실행 시 그 후만)

운영:
- cron (예: */5 * * * *): `python -m scripts.etl_predict_logs --jsonl /app/logs/predictions.jsonl`
- env: PG_DSN (예: postgresql://user:pwd@host:5432/db)

Dependency: psycopg (v3, libpq) — pip install psycopg[binary]
optional: pyproject.toml 의 price-engine-api 또는 별도 etl extra 로 추가.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# DDL 의 25 column. logging row 의 alias / 추가 field 는 적재 안 함.
PREDICT_LOGS_COLUMNS: tuple[str, ...] = (
    "request_id",                 # row['id']
    "timestamp",                  # row['ts']
    "rollout_cohort",
    "matched",
    "match_profile_source",
    "slug_in_warm_set",
    "is_saatchi_warm",
    "external_collector_source",
    "year_made_route",
    "year_made_used",
    "enrichment_latency_ms",
    "predict_total_latency_ms",
    "artwork_id",
    "artwork_url",
    "predicted_price_krw",
    "predicted_range_low_krw",
    "predicted_range_high_krw",
    "confidence_grade",
    "model_variant",
    "artifact_version",
    "warm_artist_slugs_version",
    "rollout_rule_version",
    "server_instance",
    "worker_instance_id",
    "cache_epoch",
)

def map_row_to_columns(row: dict[str, Any]) -> dict[str, Any]:
    """JSONL row → predict_logs INSERT row.

    - alias / 추가 field drop
    - id → request_id, ts → timestamp 이름 변경
    - 누락 column 은 None
    """
    out: dict[str, Any] = {}
    # remap-aware lookup
    for col in PREDICT_LOGS_COLUMNS:
        if col == "request_id":
            out[col] = row.get("id") or row.get("request_id")
        elif col == "timestamp":
            out[col] = row.get("ts") or row.get("timestamp")
        else:
            out[col] = row.get(col)
    return out


def iter_jsonl_after_offset(
    jsonl_path: Path, offset: int,
) -> Iterator[tuple[int, dict[str, Any] | None]]:
    """JSONL 의 byte offset 이후 line 을 (new_offset, row) 로 yield.

    v3.6 PR15a (코덱스 PR15 review P1):
    - newline 으로 안 끝나는 마지막 line 은 partial append 가능성 → 그 line 은
      yield 안 함 (offset 전진 X) → 다음 run 에서 완성된 line 으로 다시 read.
    - parse 실패 (malformed) → row=None yield + offset 전진 (caller 가 dead-letter
      에 원본 line 저장 + counter 증가).
    """
    if not jsonl_path.exists():
        return
    with jsonl_path.open("rb") as f:
        f.seek(offset)
        while True:
            line = f.readline()
            if not line:
                break
            # partial append 보호: newline 없으면 incomplete (server flush 직전).
            # offset 전진 안 하고 break → 다음 run 에서 같은 자리부터 재시도.
            if not line.endswith(b"\n"):
                logger.debug("partial line at offset %d, defer to next run", f.tell())
                break
            new_offset = f.tell()
            try:
                row = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("malformed line at offset %d: %s", new_offset, e)
                # row=None 표식 — caller 가 dead-letter 저장 (원본 line 보존)
                yield new_offset, {"__malformed__": line.decode("utf-8", errors="replace")}
                continue
            yield new_offset, row


def insert_rows(cursor, rows: Iterable[dict[str, Any]]) -> int:
    """predict_logs 에 row INSERT (ON CONFLICT DO NOTHING — idempotent).

    Returns: 실제 inserted row 수 (PG rowcount).
    """
    cols_csv = ", ".join(PREDICT_LOGS_COLUMNS)
    placeholders = ", ".join(f"%({c})s" for c in PREDICT_LOGS_COLUMNS)
    sql = (
        f"INSERT INTO predict_logs ({cols_csv}) VALUES ({placeholders}) "
        f"ON CONFLICT (request_id) DO NOTHING"
    )
    n_inserted = 0
    for row in rows:
        if not row:
            continue
        mapped = map_row_to_columns(row)
        if not mapped["request_id"]:
            logger.warning("skip row without request_id: %s", row.get("ts"))
            continue
        cursor.execute(sql, mapped)
        if cursor.rowcount > 0:
            n_inserted += cursor.rowcount
    return n_inserted


def read_offset(offset_path: Path) -> int:
    if not offset_path.exists():
        return 0
    try:
        return int(offset_path.read_text().strip() or "0")
    except ValueError:
        logger.warning("invalid offset file %s, restart from 0", offset_path)
        return 0


def write_offset(offset_path: Path, offset: int) -> None:
    offset_path.write_text(str(offset))


def _record_malformed(dead_letter_path: Path, raw_line: str, offset: int) -> None:
    """malformed line 을 dead-letter file 에 추가 (원본 + offset)."""
    dead_letter_path.parent.mkdir(parents=True, exist_ok=True)
    with dead_letter_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"offset": offset, "line": raw_line}) + "\n")


def run_etl(
    jsonl_path: Path,
    offset_path: Path,
    *,
    pg_dsn: str | None,
    dry_run: bool = False,
    batch_size: int = 500,
    dead_letter_path: Path | None = None,
) -> dict[str, int]:
    """ETL run: 마지막 offset 이후 line 을 읽어 batch INSERT.

    v3.6 PR15a (코덱스 PR15 review P1):
    - partial 마지막 line 은 offset 전진 X (다음 run 으로 미룸).
    - malformed line → dead-letter file 에 원본 보존 + counter.
    - dead_letter_path None 이면 default `<jsonl>.dead_letter`.

    Returns: {"lines_read": int, "inserted": int, "malformed": int, "new_offset": int}
    """
    start_offset = read_offset(offset_path)
    logger.info("ETL start: jsonl=%s, offset=%d, dry_run=%s", jsonl_path, start_offset, dry_run)

    if dead_letter_path is None:
        dead_letter_path = jsonl_path.with_suffix(jsonl_path.suffix + ".dead_letter")

    lines_read = 0
    malformed = 0
    last_offset = start_offset
    rows_buffer: list[dict[str, Any]] = []

    def _handle_line(new_offset: int, row: dict[str, Any]) -> dict[str, Any] | None:
        """malformed → dead-letter 저장. valid row 반환, malformed 면 None."""
        nonlocal malformed
        if "__malformed__" in row:
            malformed += 1
            if not dry_run:
                _record_malformed(dead_letter_path, row["__malformed__"], new_offset)
            return None
        return row

    if dry_run:
        for new_offset, row in iter_jsonl_after_offset(jsonl_path, start_offset):
            lines_read += 1
            last_offset = new_offset
            valid = _handle_line(new_offset, row)
            if valid:
                map_row_to_columns(valid)  # validate mapping
        logger.info(
            "dry-run: lines_read=%d, malformed=%d, new_offset=%d",
            lines_read, malformed, last_offset,
        )
        return {
            "lines_read": lines_read, "inserted": 0,
            "malformed": malformed, "new_offset": last_offset,
        }

    if pg_dsn is None:
        raise RuntimeError("pg_dsn required for non-dry-run")

    import psycopg

    inserted = 0
    with psycopg.connect(pg_dsn) as conn, conn.cursor() as cur:
        for new_offset, row in iter_jsonl_after_offset(jsonl_path, start_offset):
            lines_read += 1
            last_offset = new_offset
            valid = _handle_line(new_offset, row)
            if valid:
                rows_buffer.append(valid)
            if len(rows_buffer) >= batch_size:
                inserted += insert_rows(cur, rows_buffer)
                conn.commit()
                write_offset(offset_path, last_offset)
                rows_buffer.clear()
        if rows_buffer:
            inserted += insert_rows(cur, rows_buffer)
            conn.commit()
        write_offset(offset_path, last_offset)

    logger.info(
        "ETL done: lines_read=%d, inserted=%d, malformed=%d, new_offset=%d",
        lines_read, inserted, malformed, last_offset,
    )
    return {
        "lines_read": lines_read, "inserted": inserted,
        "malformed": malformed, "new_offset": last_offset,
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="ETL predictions.jsonl → predict_logs")
    parser.add_argument("--jsonl", required=True, type=Path, help="JSONL log file")
    parser.add_argument(
        "--offset-file", type=Path, default=None,
        help="offset state file (default: <jsonl>.offset)",
    )
    parser.add_argument(
        "--dsn", default=os.getenv("PG_DSN"),
        help="PostgreSQL DSN (env: PG_DSN)",
    )
    parser.add_argument("--dry-run", action="store_true", help="parse only, no INSERT")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args(argv)

    offset_path = args.offset_file or args.jsonl.with_suffix(args.jsonl.suffix + ".offset")
    result = run_etl(
        jsonl_path=args.jsonl,
        offset_path=offset_path,
        pg_dsn=args.dsn,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
    print(json.dumps(result))  # operator-facing
    return 0


if __name__ == "__main__":
    sys.exit(main())
