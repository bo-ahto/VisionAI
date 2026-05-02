"""v3.6 PR15: ETL JSONL → predict_logs 단위 테스트.

검증 (psycopg 의존성 X — INSERT path 만 mock cursor):
- map_row_to_columns: alias drop, id→request_id, ts→timestamp 변환
- iter_jsonl_after_offset: byte offset 기반 incremental read
- insert_rows: ON CONFLICT DO NOTHING idempotent + missing request_id skip
- offset state 파일 read/write
- dry-run mode (DB connection 없이도 동작)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from scripts.etl_predict_logs import (
    PREDICT_LOGS_COLUMNS,
    insert_rows,
    iter_jsonl_after_offset,
    map_row_to_columns,
    read_offset,
    run_etl,
    write_offset,
)

# ---- map_row_to_columns ----


def test_map_row_basic_remap():
    """id → request_id, ts → timestamp."""
    row = {
        "id": "00000000-0000-0000-0000-000000000001",
        "ts": "2026-05-03T08:00:00Z",
        "matched": True,
        "is_saatchi_warm": True,
        "predicted_price_krw": 1_000_000,
    }
    out = map_row_to_columns(row)
    assert out["request_id"] == "00000000-0000-0000-0000-000000000001"
    assert out["timestamp"] == "2026-05-03T08:00:00Z"
    assert out["matched"] is True
    assert out["predicted_price_krw"] == 1_000_000


def test_map_row_drops_aliases():
    """deprecated alias (predicted_krw / price_range_low|high / total_ms) drop."""
    row = {
        "id": "x",
        "ts": "2026-05-03T08:00:00Z",
        "predicted_price_krw": 1000,
        "predicted_krw": 1000,           # alias
        "price_range_low": 800,           # alias
        "price_range_high": 1200,         # alias
        "total_ms": 50,                   # alias
        # 추가 logging field — DDL 외
        "artist_id": 42,
        "artist_matched": "Kim",
    }
    out = map_row_to_columns(row)
    assert "predicted_krw" not in out
    assert "price_range_low" not in out
    assert "price_range_high" not in out
    assert "total_ms" not in out
    assert "artist_id" not in out
    assert "artist_matched" not in out
    # spec column 만
    assert set(out.keys()) == set(PREDICT_LOGS_COLUMNS)


def test_map_row_missing_fields_become_none():
    """logging row 에 없는 column 은 None."""
    row = {"id": "x", "ts": "2026-05-03T00:00:00Z", "predicted_price_krw": 100}
    out = map_row_to_columns(row)
    assert out["matched"] is None
    assert out["rollout_cohort"] is None
    assert out["worker_instance_id"] is None


# ---- iter_jsonl_after_offset ----


def test_iter_jsonl_yields_rows_after_offset(tmp_path: Path):
    jsonl = tmp_path / "log.jsonl"
    rows_data = [
        {"id": "a", "ts": "2026-05-03T01:00:00Z"},
        {"id": "b", "ts": "2026-05-03T01:01:00Z"},
        {"id": "c", "ts": "2026-05-03T01:02:00Z"},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in rows_data) + "\n")

    yielded = list(iter_jsonl_after_offset(jsonl, 0))
    assert len(yielded) == 3
    assert yielded[0][1]["id"] == "a"
    assert yielded[2][1]["id"] == "c"
    final_offset = yielded[-1][0]

    # 두 번째 run: final_offset 부터 → 빈 yield
    yielded2 = list(iter_jsonl_after_offset(jsonl, final_offset))
    assert yielded2 == []


def test_iter_jsonl_skips_malformed(tmp_path: Path):
    jsonl = tmp_path / "log.jsonl"
    content = (
        json.dumps({"id": "a", "ts": "x"}) + "\n"
        + "not valid json\n"
        + json.dumps({"id": "b", "ts": "y"}) + "\n"
    )
    jsonl.write_text(content)

    yielded = list(iter_jsonl_after_offset(jsonl, 0))
    # 3 line, malformed 는 빈 dict yield (offset 진행)
    assert len(yielded) == 3
    assert yielded[0][1]["id"] == "a"
    assert yielded[1][1] == {}
    assert yielded[2][1]["id"] == "b"


def test_iter_jsonl_nonexistent_file(tmp_path: Path):
    yielded = list(iter_jsonl_after_offset(tmp_path / "absent.jsonl", 0))
    assert yielded == []


# ---- insert_rows ----


def test_insert_rows_calls_execute_per_row():
    cursor = MagicMock()
    cursor.rowcount = 1
    rows = [
        {"id": "a", "ts": "2026-05-03T00:00:00Z", "predicted_price_krw": 100},
        {"id": "b", "ts": "2026-05-03T00:01:00Z", "predicted_price_krw": 200},
    ]
    n = insert_rows(cursor, rows)
    assert n == 2
    assert cursor.execute.call_count == 2
    # SQL 내용 검증
    sql = cursor.execute.call_args_list[0][0][0]
    assert "INSERT INTO predict_logs" in sql
    assert "ON CONFLICT (request_id) DO NOTHING" in sql


def test_insert_rows_skips_missing_request_id():
    cursor = MagicMock()
    cursor.rowcount = 1
    rows = [
        {"id": "a", "ts": "x", "predicted_price_krw": 100},
        {"ts": "no_id_row", "predicted_price_krw": 200},  # missing id
        {"id": "c", "ts": "y", "predicted_price_krw": 300},
    ]
    n = insert_rows(cursor, rows)
    assert n == 2  # 첫 + 셋째
    assert cursor.execute.call_count == 2


def test_insert_rows_skips_empty_rows():
    cursor = MagicMock()
    cursor.rowcount = 1
    n = insert_rows(cursor, [{}, {"id": "a", "ts": "x", "predicted_price_krw": 1}])
    assert n == 1


def test_insert_rows_idempotent_when_rowcount_zero():
    """ON CONFLICT 시 cursor.rowcount=0 → inserted 카운트 증가 X."""
    cursor = MagicMock()
    cursor.rowcount = 0  # PK 충돌 시뮬
    rows = [{"id": "a", "ts": "x", "predicted_price_krw": 1}]
    n = insert_rows(cursor, rows)
    assert n == 0
    assert cursor.execute.call_count == 1


# ---- offset state ----


def test_offset_read_write_roundtrip(tmp_path: Path):
    p = tmp_path / "state.offset"
    assert read_offset(p) == 0  # missing
    write_offset(p, 12345)
    assert read_offset(p) == 12345


def test_offset_corrupted_returns_zero(tmp_path: Path):
    p = tmp_path / "state.offset"
    p.write_text("not_a_number")
    assert read_offset(p) == 0


# ---- run_etl dry-run (no DB) ----


def test_run_etl_dry_run_parses_without_db(tmp_path: Path):
    jsonl = tmp_path / "log.jsonl"
    rows = [
        {"id": "a", "ts": "2026-05-03T00:00:00Z", "predicted_price_krw": 100},
        {"id": "b", "ts": "2026-05-03T00:01:00Z", "predicted_price_krw": 200},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    offset_path = tmp_path / "log.jsonl.offset"

    result = run_etl(jsonl, offset_path, pg_dsn=None, dry_run=True)
    assert result["lines_read"] == 2
    assert result["inserted"] == 0
    assert result["new_offset"] > 0
    # dry-run 은 offset state file 안 쓴다 (production offset 보존)
    assert not offset_path.exists()


def test_run_etl_resumes_from_offset(tmp_path: Path):
    jsonl = tmp_path / "log.jsonl"
    line1 = json.dumps({"id": "a", "ts": "x", "predicted_price_krw": 1}) + "\n"
    line2 = json.dumps({"id": "b", "ts": "y", "predicted_price_krw": 2}) + "\n"
    jsonl.write_text(line1 + line2)

    offset_path = tmp_path / "state"
    # 첫째 line offset 까지 적힌 상태 모사
    write_offset(offset_path, len(line1.encode("utf-8")))

    result = run_etl(jsonl, offset_path, pg_dsn=None, dry_run=True)
    assert result["lines_read"] == 1  # line2 만
