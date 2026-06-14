#!/usr/bin/env python3
"""PP-H11D ②: 라이브 serving DB의 검색 스냅샷 테이블만 surgical in-place 갱신.

표준 DB 빌더(build_price_prediction_official_v0_1_db)는 connect_rebuilt가 DB를
통째로 unlink·재생성하므로, 런타임 누적 데이터(prediction_events 641건=실서비스
라우팅 로그, sale_price_feedback, 검수 큐)가 전부 삭제된다. 따라서 전체 재빌드
대신 `artist_search_feature_snapshots` 테이블만 교체한다:

  1) 기존 행에서 normalized→artist_key 매핑 보존
  2) 해당 테이블만 DELETE
  3) 빌더의 실제 insert_search_features로 재삽입(스키마/ID/로직 동일 보장)

다른 모든 테이블은 손대지 않는다. 기본 dry-run, --write 시에만 커밋.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "scripts" / "track6"
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
REGEN_SNAPSHOT = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "regenerated_operational_snapshot_latest.csv"
)

GUARDED_RUNTIME_TABLES = [
    "prediction_events",
    "prediction_calculation_steps",
    "sale_price_feedback",
    "artist_identity_review_queue",
    "external_feature_review_queue",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="DB에 실제 커밋")
    args = ap.parse_args()

    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import build_price_prediction_official_v0_1_db as db

    regen_rows = db.read_csv(REGEN_SNAPSHOT)
    print(f"regenerated snapshot rows: {len(regen_rows)}")

    conn = sqlite3.connect(DB_PATH)
    # 가드: 런타임 테이블 현재 카운트 기록(갱신 후 불변 확인용)
    before = {
        t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        for t in GUARDED_RUNTIME_TABLES
    }
    before["artist_search_feature_snapshots"] = conn.execute(
        "SELECT COUNT(*) FROM artist_search_feature_snapshots"
    ).fetchone()[0]

    # 기존 normalized -> artist_key 매핑 보존(작가 linkage 유지)
    alias_to_artist: dict[str, str] = {}
    for normalized, artist_key in conn.execute(
        "SELECT artist_search_name_normalized, artist_key FROM artist_search_feature_snapshots"
    ):
        if normalized is not None:
            alias_to_artist[str(normalized)] = artist_key

    # 갱신 전 핵심 카운트 샘플(검증용)
    sample_before = dict(
        conn.execute(
            "SELECT artist_search_name, search_exhibition_context_count "
            "FROM artist_search_feature_snapshots "
            "ORDER BY search_exhibition_context_count DESC LIMIT 5"
        ).fetchall()
    )

    conn.execute("DELETE FROM artist_search_feature_snapshots")
    db.insert_search_features(conn, regen_rows, alias_to_artist)

    after = {
        t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        for t in GUARDED_RUNTIME_TABLES
    }
    after["artist_search_feature_snapshots"] = conn.execute(
        "SELECT COUNT(*) FROM artist_search_feature_snapshots"
    ).fetchone()[0]
    placeholders = ",".join("?" * len(sample_before))
    sample_after = dict(
        conn.execute(
            "SELECT artist_search_name, search_exhibition_context_count "
            "FROM artist_search_feature_snapshots "
            f"WHERE artist_search_name IN ({placeholders})",
            list(sample_before.keys()),
        ).fetchall()
    )

    # 가드 검증: 런타임 테이블 불변
    runtime_ok = all(before[t] == after[t] for t in GUARDED_RUNTIME_TABLES)
    print("\n-- runtime tables (must be unchanged) --")
    for t in GUARDED_RUNTIME_TABLES:
        flag = "OK" if before[t] == after[t] else "!!CHANGED!!"
        print(f"  {t:38s} {before[t]} -> {after[t]}  {flag}")
    print(
        f"  artist_search_feature_snapshots        {before['artist_search_feature_snapshots']} -> "
        f"{after['artist_search_feature_snapshots']}"
    )
    print("\n-- top exhibition-count artists (before -> after dedup) --")
    for name, bv in sample_before.items():
        print(f"  {name:24s} {bv} -> {sample_after.get(name)}")

    if not runtime_ok:
        conn.rollback()
        conn.close()
        raise SystemExit("ABORT: runtime table row count changed — rolled back, no write.")

    if args.write:
        conn.commit()
        print("\nCOMMITTED search snapshot update to live DB.")
    else:
        conn.rollback()
        print("\n[dry-run] rolled back (use --write to commit).")
    conn.close()


if __name__ == "__main__":
    main()
