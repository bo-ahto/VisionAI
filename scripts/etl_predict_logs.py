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

# JSONL row → DDL column 매핑 (이름 다른 경우만)
ROW_KEY_REMAP: dict[str, str] = {
    "id": "request_id",
    "ts": "timestamp",
}


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


def iter_jsonl_after_offset(jsonl_path: Path, offset: int) -> Iterator[tuple[int, dict[str, Any]]]:
    """JSONL 의 byte offset 이후 line 을 (new_offset, row) 로 yield.

    parse 실패 line 은 skip + warning. caller 가 last good offset 을 저장.
    """
    if not jsonl_path.exists():
        return
    with jsonl_path.open("rb") as f:
        f.seek(offset)
        line_no = 0
        while True:
            line = f.readline()
            if not line:
                break
            line_no += 1
            new_offset = f.tell()
            try:
                row = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("skip malformed line at offset %d: %s", new_offset, e)
                yield new_offset, {}  # offset 진행, row 빈 dict
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


def run_etl(
    jsonl_path: Path,
    offset_path: Path,
    *,
    pg_dsn: str | None,
    dry_run: bool = False,
    batch_size: int = 500,
) -> dict[str, int]:
    """ETL run: 마지막 offset 이후 line 을 읽어 batch INSERT.

    Returns: {"lines_read": int, "inserted": int, "new_offset": int}
    """
    start_offset = read_offset(offset_path)
    logger.info("ETL start: jsonl=%s, offset=%d, dry_run=%s", jsonl_path, start_offset, dry_run)

    lines_read = 0
    last_offset = start_offset
    rows_buffer: list[dict[str, Any]] = []

    if dry_run:
        # parse + map 만, INSERT 안 함
        for new_offset, row in iter_jsonl_after_offset(jsonl_path, start_offset):
            lines_read += 1
            last_offset = new_offset
            if row:
                map_row_to_columns(row)  # validate mapping
        logger.info("dry-run: lines_read=%d, new_offset=%d", lines_read, last_offset)
        return {"lines_read": lines_read, "inserted": 0, "new_offset": last_offset}

    if pg_dsn is None:
        raise RuntimeError("pg_dsn required for non-dry-run")

    import psycopg

    inserted = 0
    with psycopg.connect(pg_dsn) as conn, conn.cursor() as cur:
        for new_offset, row in iter_jsonl_after_offset(jsonl_path, start_offset):
            lines_read += 1
            last_offset = new_offset
            if row:
                rows_buffer.append(row)
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
        "ETL done: lines_read=%d, inserted=%d, new_offset=%d",
        lines_read, inserted, last_offset,
    )
    return {"lines_read": lines_read, "inserted": inserted, "new_offset": last_offset}


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
