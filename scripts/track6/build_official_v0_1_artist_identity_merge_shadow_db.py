#!/usr/bin/env python3
"""Create a shadow DB with the artist identity merge dry-run map applied.

The operational SQLite DB is never modified. The shadow DB is used to inspect
how candidate artist resolution and same-artist price history would change if
the reviewed canonical artist_key map were applied.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SRC_DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
MERGE_MAP_CSV = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_artist_identity_merge_dry_run"
    / "artist_identity_merge_map_dry_run.csv"
)
COMPONENTS_CSV = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_artist_identity_merge_dry_run"
    / "artist_identity_merge_components_dry_run.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_artist_identity_merge_shadow"
SHADOW_DB = OUT_DIR / "price_prediction_v0_1_identity_merge_shadow.sqlite"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_merge_shadow.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_merge_shadow.md"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")

ARTIST_KEY_COLUMNS = {
    "artist_aliases": ["artist_key"],
    "artist_profile_snapshots": ["artist_key"],
    "artist_search_feature_snapshots": ["artist_key"],
    "artwork_price_observations": ["artist_key"],
    "cold_feature_snapshots": ["artist_key"],
    "external_feature_review_queue": ["artist_key"],
    "prediction_events": ["artist_key"],
    "similar_artwork_stats_cache": ["artist_key"],
    "training_candidates": ["artist_key"],
    "warm_feature_snapshots": ["artist_key"],
    "similar_artist_cache": ["target_artist_key", "candidate_artist_key"],
}


def load_json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone() is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(conn, table):
        return False
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    return column in columns


def median_optional(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def mode_optional(values: list[Any]) -> Any | None:
    cleaned = [value for value in values if value is not None and str(value).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def rebuild_registry_aggregates(conn: sqlite3.Connection, canonical_keys: set[str]) -> None:
    for artist_key in sorted(canonical_keys):
        rows = conn.execute(
            """
            SELECT price_krw, log_area, medium_category, support_category
            FROM artwork_price_observations
            WHERE artist_key = ?
            """,
            (artist_key,),
        ).fetchall()
        prices = [int(row["price_krw"]) for row in rows if row["price_krw"] and int(row["price_krw"]) > 0]
        log_areas = [float(row["log_area"]) for row in rows if row["log_area"] is not None]
        mediums = [row["medium_category"] for row in rows]
        supports = [row["support_category"] for row in rows]
        conn.execute(
            """
            UPDATE artist_registry
            SET valid_price_count = ?,
                primary_medium_category = ?,
                primary_support_category = ?,
                median_price_krw = ?,
                median_log_area = ?,
                updated_at = ?
            WHERE artist_key = ?
            """,
            (
                len(prices),
                mode_optional(mediums),
                mode_optional(supports),
                int(round(median(prices))) if prices else None,
                median_optional(log_areas),
                CREATED_AT,
                artist_key,
            ),
        )


def candidate_count(conn: sqlite3.Connection, alias_normalized: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT r.artist_key)
        FROM artist_aliases a
        JOIN artist_registry r ON r.artist_key = a.artist_key
        WHERE a.alias_normalized = ?
        """,
        (alias_normalized,),
    ).fetchone()
    return int(row[0] or 0)


def create_shadow_db(mapping: dict[str, str]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_DB, SHADOW_DB)
    canonical_keys = set(mapping.values())
    source_keys = set(mapping.keys())
    update_counts: dict[str, int] = {}
    with sqlite3.connect(SHADOW_DB) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = OFF")
        for table, columns in ARTIST_KEY_COLUMNS.items():
            if not table_exists(conn, table):
                continue
            for column in columns:
                if not column_exists(conn, table, column):
                    continue
                count = 0
                for source, canonical in mapping.items():
                    cur = conn.execute(
                        f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                        (canonical, source),
                    )
                    count += int(cur.rowcount or 0)
                if count:
                    update_counts[f"{table}.{column}"] = count
        rebuild_registry_aggregates(conn, canonical_keys)
        deleted = conn.execute(
            f"DELETE FROM artist_registry WHERE artist_key IN ({','.join('?' for _ in source_keys)})",
            tuple(source_keys),
        ).rowcount
        conn.commit()
    return {
        "shadow_db": str(SHADOW_DB.relative_to(REPO)),
        "updated_columns": update_counts,
        "deleted_source_artist_registry_rows": int(deleted or 0),
    }


def build_impact(mapping: dict[str, str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    components = pd.read_csv(COMPONENTS_CSV)
    with sqlite3.connect(SRC_DB) as before, sqlite3.connect(SHADOW_DB) as after:
        before.row_factory = sqlite3.Row
        after.row_factory = sqlite3.Row
        before_registry = pd.read_sql_query("SELECT artist_key, valid_price_count FROM artist_registry", before)
        after_registry = pd.read_sql_query("SELECT artist_key, valid_price_count FROM artist_registry", after)
        before_counts = before_registry.set_index("artist_key")["valid_price_count"].to_dict()
        after_counts = after_registry.set_index("artist_key")["valid_price_count"].to_dict()
        rows: list[dict[str, Any]] = []
        for _, row in components.iterrows():
            keys = load_json_list(row.get("component_artist_keys_json"))
            aliases = load_json_list(row.get("aliases_for_review_json"))
            canonical = str(row.get("canonical_artist_key"))
            before_candidate_max = max([int(before_counts.get(key, 0) or 0) for key in keys] or [0])
            after_canonical_count = int(after_counts.get(canonical, 0) or 0)
            before_alias_candidates = max([candidate_count(before, alias) for alias in aliases] or [0])
            after_alias_candidates = max([candidate_count(after, alias) for alias in aliases] or [0])
            rows.append({
                "component_id": row.get("component_id"),
                "priority_tiers_json": row.get("priority_tiers_json"),
                "canonical_artist_key": canonical,
                "component_artist_keys_json": json.dumps(keys, ensure_ascii=False),
                "normalized_aliases_json": json.dumps(aliases, ensure_ascii=False),
                "before_max_valid_price_count": before_candidate_max,
                "after_canonical_valid_price_count": after_canonical_count,
                "valid_price_count_gain": after_canonical_count - before_candidate_max,
                "before_alias_candidate_count": before_alias_candidates,
                "after_alias_candidate_count": after_alias_candidates,
                "candidate_count_reduced": before_alias_candidates > after_alias_candidates,
                "resolved_to_single_candidate": after_alias_candidates == 1,
            })
    frame = pd.DataFrame(rows).sort_values(
        ["valid_price_count_gain", "before_alias_candidate_count"],
        ascending=[False, False],
    ).reset_index(drop=True)
    payload = {
        "evaluated_merge_groups": int(len(frame)),
        "resolved_to_single_candidate_groups": int(frame["resolved_to_single_candidate"].sum()) if not frame.empty else 0,
        "candidate_count_reduced_groups": int(frame["candidate_count_reduced"].sum()) if not frame.empty else 0,
        "total_valid_price_count_gain_vs_previous_max": int(frame["valid_price_count_gain"].sum()) if not frame.empty else 0,
    }
    return frame, payload


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "- 없음\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].head(max_rows).iterrows():
        values = [str(row.get(col, "")).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(frame: pd.DataFrame, payload: dict[str, Any]) -> dict[str, Any]:
    impact_csv = OUT_DIR / "artist_identity_merge_shadow_impact.csv"
    frame.to_csv(impact_csv, index=False)
    payload = {
        "created_at": CREATED_AT,
        **payload,
        "impact_csv": str(impact_csv.relative_to(REPO)),
    }
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# 공식 v0.1 작가 식별자 병합 shadow DB 영향 감사",
        "",
        f"- 작성일: {CREATED_AT}",
        "- 운영 DB 수정 여부: 수정하지 않음",
        f"- Shadow DB: `{payload['shadow_db']}`",
        f"- 평가 병합 그룹: {payload['evaluated_merge_groups']:,}건",
        f"- 단일 작가 후보로 정리되는 그룹: {payload['resolved_to_single_candidate_groups']:,}건",
        f"- 작가 후보 수가 감소하는 그룹: {payload['candidate_count_reduced_groups']:,}건",
        f"- 기존 최대 이력 대비 증가 이력 합계: {payload['total_valid_price_count_gain_vs_previous_max']:,}건",
        "",
        "## 1. 결론",
        "",
        "- 병합 후보를 shadow DB에만 적용해 작가 후보 중복과 같은 작가 가격 이력 변화를 확인했다.",
        "- 실제 운영 DB와 운영 feature cache는 수정하지 않았다.",
        "- 유사작품 통계 cache는 완전 재집계가 필요하므로, 이 shadow 감사는 작가 식별자/이력 수 영향 확인 용도다.",
        "",
        "## 2. 상위 영향 그룹",
        "",
        markdown_table(
            frame,
            [
                "component_id",
                "priority_tiers_json",
                "canonical_artist_key",
                "normalized_aliases_json",
                "before_max_valid_price_count",
                "after_canonical_valid_price_count",
                "valid_price_count_gain",
                "before_alias_candidate_count",
                "after_alias_candidate_count",
                "resolved_to_single_candidate",
            ],
            30,
        ),
        "",
        "## 3. 산출물",
        "",
        f"- Impact CSV: `{payload['impact_csv']}`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ]
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    merge_map = pd.read_csv(MERGE_MAP_CSV)
    mapping = dict(zip(merge_map["from_artist_key"].astype(str), merge_map["to_canonical_artist_key"].astype(str)))
    shadow_payload = create_shadow_db(mapping)
    impact, impact_payload = build_impact(mapping)
    payload = write_outputs(impact, {**shadow_payload, **impact_payload})
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
