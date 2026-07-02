#!/usr/bin/env python3
"""Rebuild post-merge caches on a shadow DB for official v0.1.

This is a dry-run/staging script. It copies the identity-merge shadow DB and
rebuilds the caches that must be refreshed before any canonical artist_key merge
can be applied to the operational DB.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_official_v0_1_artist_external_feature_cache import (  # noqa: E402
    EXTERNAL_JOIN_COLUMNS,
    aggregate_artist,
    build_external_row_map,
)
from build_price_prediction_official_v0_1_db import (  # noqa: E402
    SNAPSHOT_VERSION,
    insert_similar_artists,
    insert_similar_artwork_stats,
    price_to_ho,
    size_bucket,
    stable_id,
)


SOURCE_DB = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
IDENTITY_SHADOW_DB = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_artist_identity_merge_shadow"
    / "price_prediction_v0_1_identity_merge_shadow.sqlite"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_artist_identity_post_merge_cache_rebuild"
REBUILT_SHADOW_DB = OUT_DIR / "price_prediction_v0_1_post_merge_cache_rebuild_shadow.sqlite"
EXTERNAL_CACHE_CSV = OUT_DIR / "official_v0_1_artist_external_feature_cache_post_merge_candidate.csv"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_post_merge_cache_rebuild.md"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")


def table_count(conn: sqlite3.Connection, table: str) -> int:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    if not exists:
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def mode_or_none(values: list[Any]) -> Any | None:
    cleaned = [value for value in values if value is not None and str(value).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def median_or_none(values: list[Any]) -> float | None:
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float).tolist()
    if not numeric:
        return None
    return float(median(numeric))


def int_or_none(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def snapshot_counts(db_path: Path) -> dict[str, int]:
    with sqlite3.connect(db_path) as conn:
        return {
            "artist_registry": table_count(conn, "artist_registry"),
            "artist_aliases": table_count(conn, "artist_aliases"),
            "artist_profile_snapshots": table_count(conn, "artist_profile_snapshots"),
            "similar_artwork_stats_cache": table_count(conn, "similar_artwork_stats_cache"),
            "similar_artist_cache": table_count(conn, "similar_artist_cache"),
            "artist_search_feature_snapshots": table_count(conn, "artist_search_feature_snapshots"),
            "external_feature_review_queue": table_count(conn, "external_feature_review_queue"),
        }


def copy_shadow_db() -> None:
    if not IDENTITY_SHADOW_DB.exists():
        raise FileNotFoundError(IDENTITY_SHADOW_DB)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if REBUILT_SHADOW_DB.exists():
        REBUILT_SHADOW_DB.unlink()
    shutil.copy2(IDENTITY_SHADOW_DB, REBUILT_SHADOW_DB)


def deduplicate_aliases(conn: sqlite3.Connection) -> dict[str, int]:
    before = table_count(conn, "artist_aliases")
    aliases = pd.read_sql_query("SELECT * FROM artist_aliases", conn)
    if aliases.empty:
        return {"before": before, "after": 0, "removed": before}
    aliases["confidence"] = pd.to_numeric(aliases["confidence"], errors="coerce").fillna(0.0)
    aliases = aliases.sort_values(
        ["artist_key", "alias_normalized", "confidence", "source", "alias_text"],
        ascending=[True, True, False, True, True],
    )
    aliases = aliases.drop_duplicates(subset=["artist_key", "alias_normalized"], keep="first").copy()
    aliases["alias_id"] = aliases.apply(
        lambda row: stable_id("alias", row["artist_key"], row["alias_normalized"]),
        axis=1,
    )
    conn.execute("DELETE FROM artist_aliases")
    columns = [
        "alias_id",
        "artist_key",
        "alias_text",
        "alias_normalized",
        "alias_type",
        "source",
        "confidence",
        "created_at",
    ]
    conn.executemany(
        f"INSERT INTO artist_aliases ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        aliases[columns].where(pd.notna(aliases[columns]), None).values.tolist(),
    )
    after = table_count(conn, "artist_aliases")
    return {"before": before, "after": after, "removed": before - after}


def rebuild_profile_snapshots(conn: sqlite3.Connection) -> dict[str, int]:
    before = table_count(conn, "artist_profile_snapshots")
    registry = pd.read_sql_query("SELECT * FROM artist_registry", conn)
    profiles = pd.read_sql_query("SELECT * FROM artist_profile_snapshots", conn)
    profile_groups = {key: group.copy() for key, group in profiles.groupby("artist_key", dropna=False)}
    conn.execute("DELETE FROM artist_profile_snapshots")
    rows: list[tuple[Any, ...]] = []
    for _, artist in registry.iterrows():
        artist_key = str(artist["artist_key"])
        group = profile_groups.get(artist_key, pd.DataFrame())
        feature_json = {
            "primary_medium_category": artist.get("primary_medium_category"),
            "primary_support_category": artist.get("primary_support_category"),
            "median_price_krw": int_or_none(artist.get("median_price_krw")),
            "median_log_area": None if pd.isna(artist.get("median_log_area")) else float(artist.get("median_log_area")),
            "valid_price_count": int_or_none(artist.get("valid_price_count")),
        }
        rows.append(
            (
                stable_id("profile", artist_key, SNAPSHOT_VERSION),
                artist_key,
                SNAPSHOT_VERSION,
                int_or_none(artist.get("birth_year")),
                median_or_none(group["career_age"].tolist()) if not group.empty else None,
                mode_or_none(group["career_stage"].tolist()) if not group.empty else None,
                int_or_none(median_or_none(group["total_works"].tolist())) if not group.empty else None,
                int_or_none(median_or_none(group["for_sale_works"].tolist())) if not group.empty else None,
                int_or_none(median_or_none(group["followers"].tolist())) if not group.empty else None,
                median_or_none(group["for_sale_ratio"].tolist()) if not group.empty else None,
                int(pd.to_numeric(group["is_p1"], errors="coerce").fillna(0).max()) if not group.empty else None,
                int(pd.to_numeric(group["has_international"], errors="coerce").fillna(0).max()) if not group.empty else None,
                mode_or_none(group["source"].tolist()) if not group.empty else None,
                json.dumps(feature_json, ensure_ascii=False, sort_keys=True),
                CREATED_AT,
            )
        )
    conn.executemany(
        """
        INSERT INTO artist_profile_snapshots (
          snapshot_id, artist_key, snapshot_version, birth_year, career_age,
          career_stage, total_works, for_sale_works, followers,
          for_sale_ratio, is_p1, has_international, source, feature_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    after = table_count(conn, "artist_profile_snapshots")
    return {"before": before, "after": after, "removed": before - after}


def normalized_rows_from_observations(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    observations = pd.read_sql_query(
        """
        SELECT artist_key, price_krw, log_price_krw, area_cm2, log_area,
               medium_category, support_category
        FROM artwork_price_observations
        """,
        conn,
    )
    rows: list[dict[str, Any]] = []
    for _, row in observations.iterrows():
        price = int(row["price_krw"]) if pd.notna(row["price_krw"]) else None
        area = float(row["area_cm2"]) if pd.notna(row["area_cm2"]) else None
        rows.append(
            {
                "artist_key": row.get("artist_key"),
                "price_krw": price,
                "log_price_krw": float(row["log_price_krw"]) if pd.notna(row["log_price_krw"]) else None,
                "area_cm2": area,
                "log_area": float(row["log_area"]) if pd.notna(row["log_area"]) else None,
                "medium_category": row.get("medium_category"),
                "support_category": row.get("support_category"),
                "size_bucket": size_bucket(area),
                "krw_per_ho": price_to_ho(price, area),
            }
        )
    return rows


def artists_from_db(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    data = pd.read_sql_query(
        """
        SELECT r.artist_key, r.name_ko, r.name_en, r.birth_year, r.nationality,
               r.valid_price_count, r.primary_medium_category, r.primary_support_category,
               r.median_price_krw, r.median_log_area, p.career_stage
        FROM artist_registry r
        LEFT JOIN artist_profile_snapshots p
          ON p.artist_key = r.artist_key
         AND p.snapshot_version = ?
        """,
        conn,
        params=(SNAPSHOT_VERSION,),
    )
    rows: dict[str, dict[str, Any]] = {}
    for _, row in data.iterrows():
        artist_key = str(row["artist_key"])
        rows[artist_key] = {
            "artist_key": artist_key,
            "name_ko": row.get("name_ko"),
            "name_en": row.get("name_en"),
            "birth_year": int_or_none(row.get("birth_year")),
            "nationality": row.get("nationality"),
            "career_stage": row.get("career_stage"),
            "valid_price_count": int_or_none(row.get("valid_price_count")) or 0,
            "primary_medium_category": row.get("primary_medium_category"),
            "primary_support_category": row.get("primary_support_category"),
            "median_price_krw": int_or_none(row.get("median_price_krw")),
            "median_log_area": None if pd.isna(row.get("median_log_area")) else float(row.get("median_log_area")),
        }
    return rows


def rebuild_similarity_caches(conn: sqlite3.Connection) -> dict[str, int]:
    before_stats = table_count(conn, "similar_artwork_stats_cache")
    before_artists = table_count(conn, "similar_artist_cache")
    conn.execute("DELETE FROM similar_artwork_stats_cache")
    conn.execute("DELETE FROM similar_artist_cache")
    insert_similar_artwork_stats(conn, normalized_rows_from_observations(conn))
    insert_similar_artists(conn, artists_from_db(conn))
    after_stats = table_count(conn, "similar_artwork_stats_cache")
    after_artists = table_count(conn, "similar_artist_cache")
    return {
        "similar_artwork_stats_before": before_stats,
        "similar_artwork_stats_after": after_stats,
        "similar_artist_before": before_artists,
        "similar_artist_after": after_artists,
    }


def build_external_cache_candidate() -> dict[str, Any]:
    with sqlite3.connect(REBUILT_SHADOW_DB) as conn:
        obs = pd.read_sql_query(
            """
            SELECT track6_row_id, artist_key
            FROM artwork_price_observations
            WHERE track6_row_id IS NOT NULL
              AND artist_key IS NOT NULL
            """,
            conn,
        )
        artists = pd.read_sql_query(
            """
            SELECT artist_key, name_ko, name_en, birth_year, nationality
            FROM artist_registry
            """,
            conn,
        )
    obs["track6_row_id"] = pd.to_numeric(obs["track6_row_id"], errors="coerce").astype("Int64")
    obs = obs.dropna(subset=["track6_row_id", "artist_key"]).copy()
    obs["track6_row_id"] = obs["track6_row_id"].astype(int)
    artist_map = obs.merge(artists, on="artist_key", how="left")
    external = build_external_row_map()
    merged = external.merge(artist_map, left_on="_track6_row_id", right_on="track6_row_id", how="inner")
    if merged.empty:
        raise RuntimeError("No row-level external features matched post-merge shadow DB observations.")
    rows = [aggregate_artist(group) for _, group in merged.groupby("artist_key", sort=True)]
    out = pd.DataFrame(rows)
    expected = [
        "artist_key",
        "name_ko",
        "name_en",
        "birth_year",
        "nationality",
        "artist_name_ko_normalized",
        "artist_name_en_normalized",
        "external_feature_row_count",
        *EXTERNAL_JOIN_COLUMNS,
        "feature_cache_version",
        "created_at",
    ]
    for col in expected:
        if col not in out.columns:
            out[col] = np.nan
    out = out[expected]
    out.to_csv(EXTERNAL_CACHE_CSV, index=False)
    return {
        "external_source_rows": int(len(external)),
        "external_matched_rows": int(len(merged)),
        "external_artist_count": int(out["artist_key"].nunique()),
        "external_cache_csv": str(EXTERNAL_CACHE_CSV.relative_to(REPO)),
        "external_available_gallery_artist_count": int((out["gallery_tier_any_available_flag"].fillna(0) > 0).sum()),
        "external_available_exhibition_artist_count": int((out["artist_exhibition_available_count"].fillna(0) > 0).sum()),
    }


def compare_counts(before: dict[str, int], after: dict[str, int]) -> dict[str, dict[str, int]]:
    keys = sorted(set(before) | set(after))
    return {
        key: {
            "before": int(before.get(key, 0)),
            "after": int(after.get(key, 0)),
            "delta": int(after.get(key, 0) - before.get(key, 0)),
        }
        for key in keys
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "- 없음\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any]) -> None:
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    count_rows = [
        {"table": key, **value}
        for key, value in payload["count_diff"].items()
    ]
    md = [
        "# 공식 v0.1 작가 병합 후 cache 재집계 dry-run",
        "",
        f"- 작성일: {payload['created_at']}",
        "- 운영 DB 수정 여부: 수정하지 않음",
        f"- 재집계 Shadow DB: `{payload['rebuilt_shadow_db']}`",
        f"- 외부 피처 cache 후보: `{payload['external_cache_csv']}`",
        "",
        "## 1. 결론",
        "",
        "- 작가 식별자 병합 후보를 적용한 shadow DB에서 운영 적용 전 필요한 cache 재집계를 수행했다.",
        "- 재집계 대상은 alias, 작가 프로필, 유사작품 통계, 유사작가 cache, 작가 단위 외부 피처 cache다.",
        "- 운영 DB와 운영 외부 피처 cache 파일은 수정하지 않았다.",
        "- 실제 적용 전에는 이 dry-run 결과를 기준으로 P0/P1 병합 승인 여부를 확정하고, 재집계된 cache로 예측 영향 감사를 다시 실행해야 한다.",
        "",
        "## 2. 재집계 순서",
        "",
        "```text",
        "1. 검수 승인된 canonical artist_key 병합 map 적용",
        "2. artist_aliases 중복 제거",
        "3. artist_registry 집계 확인 및 artist_profile_snapshots 재생성",
        "4. artwork_price_observations 기준 similar_artwork_stats_cache 재집계",
        "5. 갱신된 artist_registry 기준 similar_artist_cache 재집계",
        "6. row-level 전시/갤러리 피처를 canonical artist_key 기준으로 재집계",
        "7. 외부 피처 검수 큐와 promotion impact 감사 재실행",
        "```",
        "",
        "## 3. 주요 수치",
        "",
        f"- alias 중복 제거: {payload['alias_dedup']['before']:,} -> {payload['alias_dedup']['after']:,}",
        f"- 작가 프로필 재생성: {payload['profile_rebuild']['before']:,} -> {payload['profile_rebuild']['after']:,}",
        f"- 유사작품 통계 cache: {payload['similar_cache_rebuild']['similar_artwork_stats_before']:,} -> {payload['similar_cache_rebuild']['similar_artwork_stats_after']:,}",
        f"- 유사작가 cache: {payload['similar_cache_rebuild']['similar_artist_before']:,} -> {payload['similar_cache_rebuild']['similar_artist_after']:,}",
        f"- 외부 피처 cache 작가 수: {payload['external_artist_count']:,}",
        "",
        "## 4. 테이블 row 변화",
        "",
        markdown_table(count_rows, ["table", "before", "after", "delta"]),
        "",
        "## 5. 산출물",
        "",
        f"- Shadow DB: `{payload['rebuilt_shadow_db']}`",
        f"- External cache CSV: `{payload['external_cache_csv']}`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ]
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    copy_shadow_db()
    before_counts = snapshot_counts(SOURCE_DB)
    with sqlite3.connect(REBUILT_SHADOW_DB) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = OFF")
        alias_dedup = deduplicate_aliases(conn)
        profile_rebuild = rebuild_profile_snapshots(conn)
        similar_rebuild = rebuild_similarity_caches(conn)
        conn.commit()
    external_summary = build_external_cache_candidate()
    after_counts = snapshot_counts(REBUILT_SHADOW_DB)
    payload = {
        "created_at": CREATED_AT,
        "source_db": str(SOURCE_DB.relative_to(REPO)),
        "identity_shadow_db": str(IDENTITY_SHADOW_DB.relative_to(REPO)),
        "rebuilt_shadow_db": str(REBUILT_SHADOW_DB.relative_to(REPO)),
        "operational_db_modified": False,
        "alias_dedup": alias_dedup,
        "profile_rebuild": profile_rebuild,
        "similar_cache_rebuild": similar_rebuild,
        **external_summary,
        "count_diff": compare_counts(before_counts, after_counts),
    }
    write_outputs(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
