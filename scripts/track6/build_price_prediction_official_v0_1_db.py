#!/usr/bin/env python3
"""Build the official price prediction v0.1 local SQLite DB/cache.

This script creates the DB foundation required before the report-level
Warm/Cold models can be connected to raw user input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_schema.sql"
TRAIN_PATH = REPO / "models" / "track6" / "price_prediction_v0.1" / "data" / "training" / "track6_split" / "track6_train.csv"
SEARCH_FEATURE_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_snapshot_latest.csv"
SEARCH_RESULT_PATH = REPO / "data" / "track6" / "external_search" / "operational" / "track6_artist_search_operational_standardized_latest.csv"
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
SUMMARY_JSON_PATH = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_db_build_summary.json"
SUMMARY_MD_PATH = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_db_build_summary.md"

SERVICE_VERSION = "price_prediction_v0.1"
SNAPSHOT_VERSION = "official_v0_1_initial_cache"
CREATED_AT = "2026-06-12T00:00:00+09:00"
HO_AREA_CM2 = 220.5


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "||".join("" if part is None else str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def normalize_name(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)
    return text


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def to_float(value: Any) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def to_int(value: Any) -> int | None:
    number = to_float(value)
    if number is None:
        return None
    return int(round(number))


def to_flag(value: Any) -> int:
    text = str(value or "").strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return 1
    if text in {"0", "false", "f", "no", "n", ""}:
        return 0
    number = to_float(text)
    return 1 if number and number != 0 else 0


def first_non_empty(values: list[Any]) -> str | None:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return None


def most_common_non_empty(values: list[Any]) -> str | None:
    counter = Counter(clean_text(value) for value in values if clean_text(value))
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def median_optional(values: list[float | int | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return float(median(cleaned))


def percentile(sorted_values: list[float], q: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[int(pos)]
    return sorted_values[lo] * (hi - pos) + sorted_values[hi] * (pos - lo)


def price_to_ho(price_krw: int | None, area_cm2: float | None) -> int | None:
    if not price_krw or not area_cm2 or area_cm2 <= 0:
        return None
    ho = max(area_cm2 / HO_AREA_CM2, 1.0)
    return int(round(price_krw / ho))


def size_bucket(area_cm2: float | None) -> str:
    if area_cm2 is None or area_cm2 <= 0:
        return "unknown"
    if area_cm2 < 1200:
        return "small"
    if area_cm2 < 3000:
        return "medium"
    if area_cm2 < 7000:
        return "large"
    return "xlarge"


def coverage_tier(count: int) -> str:
    if count >= 20:
        return "high"
    if count >= 5:
        return "medium"
    return "low"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def connect_rebuilt(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def build_artist_aggregates(train_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in train_rows:
        artist_key = clean_text(row.get("artist_key"))
        if artist_key:
            grouped[artist_key].append(row)

    artists: dict[str, dict[str, Any]] = {}
    for artist_key, rows in grouped.items():
        prices = [to_int(row.get("price_krw")) for row in rows]
        log_areas = [to_float(row.get("log_area")) for row in rows]
        valid_prices = [price for price in prices if price and price > 0]
        artists[artist_key] = {
            "artist_key": artist_key,
            "rows": rows,
            "name_ko": first_non_empty([row.get("artist_name_ko") for row in rows])
            or first_non_empty([row.get("artist_name_standardized") for row in rows]),
            "name_en": None,
            "birth_year": most_common_non_empty([row.get("artist_meta_birth_year") for row in rows]),
            "nationality": most_common_non_empty([row.get("artist_meta_nationality") for row in rows]),
            "nationality_ko": most_common_non_empty([row.get("artist_meta_nationality_ko") for row in rows]),
            "entity_suffix": most_common_non_empty([row.get("artist_entity_suffix") for row in rows]),
            "is_homonym": max(to_flag(row.get("is_homonym")) for row in rows),
            "valid_price_count": len(valid_prices),
            "primary_medium_category": most_common_non_empty([row.get("medium_category") for row in rows]),
            "primary_support_category": most_common_non_empty([row.get("support_category") for row in rows]),
            "median_price_krw": int(round(median(valid_prices))) if valid_prices else None,
            "median_log_area": median_optional(log_areas),
            "career_age": most_common_non_empty([row.get("artist_meta_career_age") for row in rows]),
            "career_stage": most_common_non_empty([row.get("artist_meta_career_stage") for row in rows]),
            "total_works": most_common_non_empty([row.get("artist_meta_total_works") for row in rows]),
            "for_sale_works": most_common_non_empty([row.get("artist_meta_for_sale_works") for row in rows]),
            "followers": most_common_non_empty([row.get("artist_meta_followers") for row in rows]),
            "for_sale_ratio": most_common_non_empty([row.get("artist_meta_for_sale_ratio") for row in rows]),
            "is_p1": max(to_flag(row.get("artist_meta_is_p1")) for row in rows),
            "has_international": max(to_flag(row.get("artist_meta_has_international")) for row in rows),
            "source": most_common_non_empty([row.get("artist_meta_source") for row in rows]),
        }
    return artists


def insert_artists(conn: sqlite3.Connection, artists: dict[str, dict[str, Any]]) -> dict[str, str]:
    cur = conn.cursor()
    alias_to_artist: dict[str, str] = {}
    for artist in artists.values():
        cur.execute(
            """
            INSERT INTO artist_registry (
              artist_key, name_ko, name_en, birth_year, nationality, nationality_ko,
              entity_suffix, is_homonym, valid_price_count, primary_medium_category,
              primary_support_category, median_price_krw, median_log_area,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artist["artist_key"],
                artist["name_ko"],
                artist["name_en"],
                to_int(artist["birth_year"]),
                artist["nationality"],
                artist["nationality_ko"],
                artist["entity_suffix"],
                artist["is_homonym"],
                artist["valid_price_count"],
                artist["primary_medium_category"],
                artist["primary_support_category"],
                artist["median_price_krw"],
                artist["median_log_area"],
                CREATED_AT,
                CREATED_AT,
            ),
        )

        alias_candidates = []
        for row in artist["rows"]:
            alias_candidates.extend(
                [
                    row.get("artist_name_ko"),
                    row.get("artist_name_ko_orig"),
                    row.get("artist_name_standardized"),
                ]
            )
        seen_aliases: set[str] = set()
        for alias_text in alias_candidates:
            alias = clean_text(alias_text)
            normalized = normalize_name(alias)
            if not alias or not normalized or normalized in seen_aliases:
                continue
            seen_aliases.add(normalized)
            alias_to_artist.setdefault(normalized, artist["artist_key"])
            cur.execute(
                """
                INSERT INTO artist_aliases (
                  alias_id, artist_key, alias_text, alias_normalized,
                  alias_type, source, confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id("alias", artist["artist_key"], normalized),
                    artist["artist_key"],
                    alias,
                    normalized,
                    "training_name",
                    "track6_train",
                    1.0,
                    CREATED_AT,
                ),
            )

        feature_json = {
            "primary_medium_category": artist["primary_medium_category"],
            "primary_support_category": artist["primary_support_category"],
            "median_price_krw": artist["median_price_krw"],
            "median_log_area": artist["median_log_area"],
            "valid_price_count": artist["valid_price_count"],
        }
        cur.execute(
            """
            INSERT INTO artist_profile_snapshots (
              snapshot_id, artist_key, snapshot_version, birth_year, career_age,
              career_stage, total_works, for_sale_works, followers,
              for_sale_ratio, is_p1, has_international, source, feature_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stable_id("profile", artist["artist_key"], SNAPSHOT_VERSION),
                artist["artist_key"],
                SNAPSHOT_VERSION,
                to_int(artist["birth_year"]),
                to_float(artist["career_age"]),
                artist["career_stage"],
                to_int(artist["total_works"]),
                to_int(artist["for_sale_works"]),
                to_int(artist["followers"]),
                to_float(artist["for_sale_ratio"]),
                artist["is_p1"],
                artist["has_international"],
                artist["source"],
                json.dumps(feature_json, ensure_ascii=False, sort_keys=True),
                CREATED_AT,
            ),
        )
    return alias_to_artist


def insert_artworks(conn: sqlite3.Connection, train_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    cur = conn.cursor()
    normalized_rows: list[dict[str, Any]] = []
    for row_number, row in enumerate(train_rows, start=1):
        artist_key = clean_text(row.get("artist_key"))
        price_krw = to_int(row.get("price_krw"))
        area_cm2 = to_float(row.get("area_cm2"))
        normalized = {
            "artist_key": artist_key,
            "price_krw": price_krw,
            "log_price_krw": to_float(row.get("ln_price_krw")),
            "area_cm2": area_cm2,
            "log_area": to_float(row.get("log_area")),
            "medium_category": clean_text(row.get("medium_category")),
            "support_category": clean_text(row.get("support_category")),
            "size_bucket": size_bucket(area_cm2),
            "krw_per_ho": price_to_ho(price_krw, area_cm2),
            "source_row": row,
        }
        normalized_rows.append(normalized)
        is_training_candidate = to_flag(row.get("is_training_candidate"))
        exclude_reasons = clean_text(row.get("cleaning_exclude_reasons"))
        label_quality_tier = "usable" if is_training_candidate and not exclude_reasons else "review"
        cur.execute(
            """
            INSERT INTO artwork_price_observations (
              observation_id, track6_row_id, source_artwork_id, source_name,
              artwork_url, image_url, artist_key, artist_name_ko, title,
              price_krw, log_price_krw, width_cm, height_cm, depth_cm,
              area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate,
              medium_category, support_category, medium_support_bucket,
              is_training_candidate, label_quality_tier, split_name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stable_id("obs", row.get("_track6_row_id") or row_number, row.get("source_artwork_id")),
                to_int(row.get("_track6_row_id")) or row_number,
                clean_text(row.get("source_artwork_id")),
                clean_text(row.get("track4_source")),
                clean_text(row.get("artwork_url")),
                clean_text(row.get("image_url")),
                artist_key,
                clean_text(row.get("artist_name_ko")),
                clean_text(row.get("title_raw")),
                price_krw,
                normalized["log_price_krw"],
                to_float(row.get("width_cm")),
                to_float(row.get("height_cm")),
                to_float(row.get("depth_cm")),
                area_cm2,
                normalized["log_area"],
                to_float(row.get("aspect_ratio")),
                to_flag(row.get("has_depth")),
                to_flag(row.get("is_3d_candidate")),
                normalized["medium_category"],
                normalized["support_category"],
                clean_text(row.get("medium_support_bucket")),
                is_training_candidate,
                label_quality_tier,
                "train",
                CREATED_AT,
            ),
        )
    return normalized_rows


def insert_search_features(
    conn: sqlite3.Connection,
    search_rows: list[dict[str, str]],
    alias_to_artist: dict[str, str],
) -> dict[str, str]:
    cur = conn.cursor()
    name_to_snapshot_id: dict[str, str] = {}
    for row in search_rows:
        name = clean_text(row.get("artist_search_name"))
        normalized = normalize_name(name)
        artist_key = alias_to_artist.get(normalized)
        snapshot_id = stable_id("searchsnap", SNAPSHOT_VERSION, normalized)
        name_to_snapshot_id[normalized] = snapshot_id
        cur.execute(
            """
            INSERT INTO artist_search_feature_snapshots (
              search_snapshot_id, snapshot_version, artist_key, artist_search_name,
              artist_search_name_normalized, search_result_count, search_source_count,
              provider_coverage_count, query_success_count, search_art_context_count,
              search_exhibition_context_count, search_gallery_context_count,
              search_market_context_count, search_social_context_count,
              search_homonym_context_count, search_trusted_domain_count,
              search_name_match_ratio, search_art_match_ratio, search_exhibition_ratio,
              search_quality_score, search_quality_grade, search_homonym_risk_grade,
              search_success_flag, search_collected_flag, raw_feature_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                SNAPSHOT_VERSION,
                artist_key,
                name,
                normalized,
                to_int(row.get("search_result_count")),
                to_int(row.get("search_source_count")),
                to_int(row.get("provider_coverage_count")),
                to_int(row.get("query_success_count")),
                to_int(row.get("search_art_context_count")),
                to_int(row.get("search_exhibition_context_count")),
                to_int(row.get("search_gallery_context_count")),
                to_int(row.get("search_market_context_count")),
                to_int(row.get("search_social_context_count")),
                to_int(row.get("search_homonym_context_count")),
                to_int(row.get("search_trusted_domain_count")),
                to_float(row.get("search_name_match_ratio")),
                to_float(row.get("search_art_match_ratio")),
                to_float(row.get("search_exhibition_ratio")),
                to_float(row.get("search_quality_score")),
                clean_text(row.get("search_quality_grade")),
                clean_text(row.get("search_homonym_risk_grade")),
                to_flag(row.get("search_success_flag")),
                to_flag(row.get("search_collected_flag")),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
                CREATED_AT,
            ),
        )
    return name_to_snapshot_id


def insert_search_results(
    conn: sqlite3.Connection,
    result_rows: list[dict[str, str]],
    name_to_snapshot_id: dict[str, str],
) -> None:
    cur = conn.cursor()
    for idx, row in enumerate(result_rows, start=1):
        name = clean_text(row.get("artist_search_name"))
        normalized = normalize_name(name)
        snapshot_id = name_to_snapshot_id.get(normalized)
        cur.execute(
            """
            INSERT INTO artist_search_results (
              result_id, search_snapshot_id, artist_search_name, provider,
              query_text, rank, title, snippet, url, domain, source_group,
              has_result, is_art_context, is_exhibition_context,
              is_gallery_context, is_market_context, is_homonym_context,
              artist_name_in_result, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stable_id("searchres", row.get("collector_run_id"), name, row.get("provider"), row.get("rank"), row.get("url"), idx),
                snapshot_id,
                name,
                clean_text(row.get("provider")),
                clean_text(row.get("query_text")),
                to_int(row.get("rank")),
                clean_text(row.get("title")),
                clean_text(row.get("snippet")),
                clean_text(row.get("url")),
                clean_text(row.get("domain")),
                clean_text(row.get("source_group")),
                to_flag(row.get("has_result")),
                to_flag(row.get("is_art_context")),
                to_flag(row.get("is_exhibition_context")),
                to_flag(row.get("is_gallery_context")),
                to_flag(row.get("is_market_context")),
                to_flag(row.get("is_homonym_context")),
                to_flag(row.get("artist_name_in_result")),
                clean_text(row.get("collected_at")),
            ),
        )


def insert_similar_artwork_stats(conn: sqlite3.Connection, normalized_rows: list[dict[str, Any]]) -> None:
    cur = conn.cursor()
    rows = [row for row in normalized_rows if row["price_krw"] and row["price_krw"] > 0]
    group_specs = [
        ("same_artist_medium_support_size", ("artist_key", "medium_category", "support_category", "size_bucket")),
        ("same_artist_medium_support", ("artist_key", "medium_category", "support_category")),
        ("cross_artist_medium_support_size", ("medium_category", "support_category", "size_bucket")),
        ("cross_artist_medium_support", ("medium_category", "support_category")),
        ("market_size", ("size_bucket",)),
        ("market_global", ()),
    ]
    for scope, keys in group_specs:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = tuple(row.get(field) for field in keys)
            if any(value is None for value in key):
                continue
            grouped[key].append(row)

        for key, members in grouped.items():
            prices = sorted(float(member["price_krw"]) for member in members)
            log_prices = sorted(
                float(member["log_price_krw"]) for member in members if member.get("log_price_krw") is not None
            )
            log_areas = [
                float(member["log_area"]) for member in members if member.get("log_area") is not None
            ]
            per_ho = sorted(float(member["krw_per_ho"]) for member in members if member.get("krw_per_ho") is not None)
            key_map = dict(zip(keys, key))
            cur.execute(
                """
                INSERT INTO similar_artwork_stats_cache (
                  stats_id, cache_version, scope, artist_key, medium_category,
                  support_category, size_bucket, log_area_min, log_area_max,
                  sample_count, median_price_krw, q25_price_krw, q75_price_krw,
                  median_log_price, median_krw_per_ho, q25_krw_per_ho,
                  q75_krw_per_ho, coverage_tier, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id("simstat", SNAPSHOT_VERSION, scope, *key),
                    SNAPSHOT_VERSION,
                    scope,
                    key_map.get("artist_key"),
                    key_map.get("medium_category"),
                    key_map.get("support_category"),
                    key_map.get("size_bucket"),
                    min(log_areas) if log_areas else None,
                    max(log_areas) if log_areas else None,
                    len(members),
                    int(round(percentile(prices, 0.50) or 0)),
                    int(round(percentile(prices, 0.25) or 0)),
                    int(round(percentile(prices, 0.75) or 0)),
                    percentile(log_prices, 0.50),
                    int(round(percentile(per_ho, 0.50))) if per_ho else None,
                    int(round(percentile(per_ho, 0.25))) if per_ho else None,
                    int(round(percentile(per_ho, 0.75))) if per_ho else None,
                    coverage_tier(len(members)),
                    CREATED_AT,
                ),
            )


def insert_similar_artists(conn: sqlite3.Connection, artists: dict[str, dict[str, Any]]) -> None:
    cur = conn.cursor()
    eligible = [
        artist
        for artist in artists.values()
        if artist["valid_price_count"] >= 5 and artist["median_price_krw"]
    ]
    for target in eligible:
        scored: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
        for candidate in eligible:
            if target["artist_key"] == candidate["artist_key"]:
                continue
            cat_hits = {
                "nationality": target["nationality"] and target["nationality"] == candidate["nationality"],
                "career_stage": target["career_stage"] and target["career_stage"] == candidate["career_stage"],
                "medium": target["primary_medium_category"] and target["primary_medium_category"] == candidate["primary_medium_category"],
                "support": target["primary_support_category"] and target["primary_support_category"] == candidate["primary_support_category"],
            }
            categorical_similarity = sum(1 for hit in cat_hits.values() if hit) / len(cat_hits)
            birth_target = to_int(target["birth_year"])
            birth_candidate = to_int(candidate["birth_year"])
            birth_similarity = 0.5
            if birth_target and birth_candidate:
                birth_similarity = max(0.0, 1.0 - abs(birth_target - birth_candidate) / 60.0)
            price_similarity = 0.5
            if target["median_price_krw"] and candidate["median_price_krw"]:
                gap = abs(math.log(target["median_price_krw"]) - math.log(candidate["median_price_krw"]))
                price_similarity = max(0.0, 1.0 - gap / 2.5)
            area_similarity = 0.5
            if target["median_log_area"] and candidate["median_log_area"]:
                gap = abs(target["median_log_area"] - candidate["median_log_area"])
                area_similarity = max(0.0, 1.0 - gap / 2.0)
            numeric_similarity = 0.35 * birth_similarity + 0.45 * price_similarity + 0.20 * area_similarity
            score = 0.55 * numeric_similarity + 0.45 * categorical_similarity
            if score < 0.45:
                continue
            reasons = {
                "same_nationality": bool(cat_hits["nationality"]),
                "same_career_stage": bool(cat_hits["career_stage"]),
                "same_primary_medium": bool(cat_hits["medium"]),
                "same_primary_support": bool(cat_hits["support"]),
                "birth_year_gap": abs(birth_target - birth_candidate) if birth_target and birth_candidate else None,
                "median_price_ratio": (
                    candidate["median_price_krw"] / target["median_price_krw"]
                    if target["median_price_krw"] and candidate["median_price_krw"]
                    else None
                ),
            }
            scored.append((score, candidate, {"numeric": numeric_similarity, "categorical": categorical_similarity, "reasons": reasons}))

        scored.sort(key=lambda item: (item[0], item[1]["valid_price_count"]), reverse=True)
        for rank, (score, candidate, detail) in enumerate(scored[:8], start=1):
            cur.execute(
                """
                INSERT INTO similar_artist_cache (
                  similar_artist_id, cache_version, target_artist_key,
                  candidate_artist_key, similarity_score, numeric_similarity,
                  categorical_similarity, price_history_count, match_reasons_json,
                  created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_id("simartist", SNAPSHOT_VERSION, target["artist_key"], candidate["artist_key"]),
                    SNAPSHOT_VERSION,
                    target["artist_key"],
                    candidate["artist_key"],
                    round(score, 6),
                    round(detail["numeric"], 6),
                    round(detail["categorical"], 6),
                    candidate["valid_price_count"],
                    json.dumps({"rank": rank, **detail["reasons"]}, ensure_ascii=False, sort_keys=True),
                    CREATED_AT,
                ),
            )


def insert_model_registry(conn: sqlite3.Connection) -> None:
    rows = [
        {
            "artifact_id": "official_v0_1_warm_target_pp258",
            "route": "warm",
            "artifact_role": "target_report_model",
            "display_name": "history_based_micro_correction",
            "internal_trace_id": "PP258 balanced final micro correction",
            "artifact_path": "experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission",
            "feature_schema_version": SNAPSHOT_VERSION,
            "metrics": {"fixed_test_n": 607, "MdAPE": 0.140976, "MAPE": 0.269888, "p95_APE": 0.807325, "RMSE_log": 0.397454},
        },
        {
            "artifact_id": "official_v0_1_cold_target_guard_search",
            "route": "cold",
            "artifact_role": "target_report_model",
            "display_name": "reference_prediction_with_search_and_guard",
            "internal_trace_id": "cold_prediction_v0.3 guard_search_gm",
            "artifact_path": "models/track6/cold_prediction_v0.3",
            "feature_schema_version": SNAPSHOT_VERSION,
            "metrics": {"fixed_test_n": 3099, "MdAPE": 0.409820, "MAPE": 0.849260, "p95_APE": 2.346465},
        },
    ]
    cur = conn.cursor()
    for row in rows:
        cur.execute(
            """
            INSERT INTO model_artifact_registry (
              artifact_id, service_version, route, artifact_role, display_name,
              internal_trace_id, artifact_path, artifact_hash,
              feature_schema_version, metrics_json, active_flag, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["artifact_id"],
                SERVICE_VERSION,
                row["route"],
                row["artifact_role"],
                row["display_name"],
                row["internal_trace_id"],
                row["artifact_path"],
                None,
                row["feature_schema_version"],
                json.dumps(row["metrics"], ensure_ascii=False, sort_keys=True),
                1,
                CREATED_AT,
            ),
        )


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    names = [
        "artist_registry",
        "artist_aliases",
        "artist_profile_snapshots",
        "artwork_price_observations",
        "artist_search_feature_snapshots",
        "artist_search_results",
        "similar_artwork_stats_cache",
        "similar_artist_cache",
        "model_artifact_registry",
    ]
    counts: dict[str, int] = {}
    for name in names:
        counts[name] = int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
    return counts


def write_summary(counts: dict[str, int], db_path: Path) -> None:
    summary = {
        "service_version": SERVICE_VERSION,
        "snapshot_version": SNAPSHOT_VERSION,
        "db_path": str(db_path.relative_to(REPO)),
        "created_at": CREATED_AT,
        "source_files": {
            "schema": str(SCHEMA_PATH.relative_to(REPO)),
            "train": str(TRAIN_PATH.relative_to(REPO)),
            "search_features": str(SEARCH_FEATURE_PATH.relative_to(REPO)),
            "search_results": str(SEARCH_RESULT_PATH.relative_to(REPO)),
        },
        "table_counts": counts,
        "notes": [
            "This DB is the official v0.1 local cache foundation.",
            "It does not train or replace the report-level models.",
            "Warm/Cold raw-input adapters will use this DB for artist matching, history lookup, search features, and explanation data.",
        ],
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 가격 예측 서비스 공식 테스트 v0.1 DB 생성 결과",
        "",
        f"- 생성일: {CREATED_AT}",
        f"- 공식 버전: `{SERVICE_VERSION}`",
        f"- DB 파일: `{summary['db_path']}`",
        f"- cache snapshot: `{SNAPSHOT_VERSION}`",
        "",
        "## 1. 생성 목적",
        "",
        "- 보고서 기준 Warm/Cold 모델을 raw 입력 서비스에 연결하기 전 필요한 조회 기반 생성",
        "- 작가 매칭, 가격 이력, 검색 피처, 유사작품 통계, 유사작가 후보, 모델 레지스트리 저장",
        "- 모델 학습 또는 모델 교체는 수행하지 않음",
        "",
        "## 2. 원천 파일",
        "",
    ]
    for label, path in summary["source_files"].items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(["", "## 3. 적재 결과", "", "| 테이블 | row 수 |", "|---|---:|"])
    for name, count in counts.items():
        lines.append(f"| `{name}` | {count:,} |")
    lines.extend(
        [
            "",
            "## 4. 다음 단계",
            "",
            "- `/api/v1/artists/resolve`에서 `artist_aliases`와 `artist_registry`를 사용해 작가 후보를 반환",
            "- `/api/v1/artworks/price-estimate`에서 `artwork_price_observations`, `similar_artwork_stats_cache`, `artist_search_feature_snapshots`를 조회",
            "- Warm/Cold 중간 피처 생성 adapter를 추가한 뒤 fixed-test parity와 동일 입력 반복 검증 수행",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(db_path: Path) -> dict[str, int]:
    train_rows = read_csv(TRAIN_PATH)
    search_rows = read_csv(SEARCH_FEATURE_PATH)
    search_result_rows = read_csv(SEARCH_RESULT_PATH)

    conn = connect_rebuilt(db_path)
    try:
        artists = build_artist_aggregates(train_rows)
        alias_to_artist = insert_artists(conn, artists)
        normalized_rows = insert_artworks(conn, train_rows)
        name_to_snapshot_id = insert_search_features(conn, search_rows, alias_to_artist)
        insert_search_results(conn, search_result_rows, name_to_snapshot_id)
        insert_similar_artwork_stats(conn, normalized_rows)
        insert_similar_artists(conn, artists)
        insert_model_registry(conn)
        conn.commit()
        counts = table_counts(conn)
    finally:
        conn.close()
    write_summary(counts, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    args = parser.parse_args()
    counts = build(args.db_path)
    print(json.dumps({"db_path": str(args.db_path), "table_counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
