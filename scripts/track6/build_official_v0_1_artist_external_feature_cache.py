#!/usr/bin/env python3
"""Build artist-level exhibition/gallery feature cache for official v0.1.

The Cold report model was trained with row-level exhibition/gallery features.
The service receives raw user input, so it needs an artist-level feature cache
that can be joined by artist_key or normalized artist name.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".cache" / "matplotlib"))

from run_pp_x_gallery_exhibition_revalidation import (  # noqa: E402
    EXTERNAL_JOIN_COLUMNS,
    build_external_row_map,
)


DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
OUT_DIR = REPO / "data" / "track6" / "service_v0_1"
OUT_CSV = OUT_DIR / "official_v0_1_artist_external_feature_cache.csv"
OUT_JSON = OUT_DIR / "official_v0_1_artist_external_feature_cache_summary.json"


COUNT_COLS = [
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
]


def normalize_name(value: object) -> str:
    import re

    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)


def median_or_nan(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return float("nan")
    return float(numeric.median())


def mode_or_missing(values: pd.Series) -> str:
    series = values.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    series = series[series.ne("__MISSING__")]
    if series.empty:
        return "__MISSING__"
    return str(series.mode(dropna=True).iloc[0])


def tier_to_score(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    text = str(value).strip().lower()
    if text in {"tier a", "a", "1"}:
        return 3.0
    if text in {"tier b", "b", "2"}:
        return 2.0
    if text in {"tier c", "c", "3"}:
        return 1.0
    return float("nan")


def load_artist_map() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
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
    return obs.merge(artists, on="artist_key", how="left")


def aggregate_artist(group: pd.DataFrame) -> dict[str, Any]:
    row: dict[str, Any] = {
        "artist_key": str(group["artist_key"].iloc[0]),
        "external_feature_row_count": int(len(group)),
    }
    for col in ["name_ko", "name_en", "birth_year", "nationality"]:
        if col in group.columns:
            row[col] = mode_or_missing(group[col]) if col != "birth_year" else median_or_nan(group[col])

    for col in COUNT_COLS:
        row[col] = median_or_nan(group[col]) if col in group.columns else float("nan")
        row[f"{col}_missing"] = 1.0 if pd.isna(row[col]) else 0.0
        row[f"{col}_log"] = float(np.log1p(max(row[col], 0.0))) if not pd.isna(row[col]) else 0.0

    counts = [row[col] for col in COUNT_COLS if not pd.isna(row[col])]
    row["artist_exhibition_total_count"] = float(sum(counts)) if counts else float("nan")
    row["artist_exhibition_total_count_log"] = (
        float(np.log1p(max(row["artist_exhibition_total_count"], 0.0)))
        if not pd.isna(row["artist_exhibition_total_count"])
        else 0.0
    )
    row["artist_exhibition_available_count"] = float(len(counts))

    row["gallery_tier_raw_numeric"] = median_or_nan(group.get("gallery_tier_raw_numeric", pd.Series(dtype=float)))
    row["gallery_tier_raw_available_flag"] = 0.0 if pd.isna(row["gallery_tier_raw_numeric"]) else 1.0
    row["gallery_tier_raw_bucket"] = (
        str(int(round(row["gallery_tier_raw_numeric"])))
        if not pd.isna(row["gallery_tier_raw_numeric"])
        else "__MISSING__"
    )
    row["gallery_tier_validated"] = mode_or_missing(group.get("gallery_tier_validated", pd.Series(dtype=object)))
    row["gallery_tier_validated_score"] = median_or_nan(
        group.get("gallery_tier_validated_score", pd.Series(dtype=float))
        if "gallery_tier_validated_score" in group
        else group.get("gallery_tier_validated", pd.Series(dtype=object)).map(tier_to_score)
    )
    row["gallery_tier_validated_available_flag"] = 0.0 if pd.isna(row["gallery_tier_validated_score"]) else 1.0
    row["gallery_tier_any_available_flag"] = float(
        row["gallery_tier_raw_available_flag"] > 0 or row["gallery_tier_validated_available_flag"] > 0
    )
    row["gallery_city_count"] = median_or_nan(group.get("gallery_city_count", pd.Series(dtype=float)))
    row["gallery_city_count_log"] = (
        float(np.log1p(max(row["gallery_city_count"], 0.0))) if not pd.isna(row["gallery_city_count"]) else 0.0
    )
    for col in ["gallery_ref_type", "gallery_audit_status"]:
        row[col] = mode_or_missing(group.get(col, pd.Series(dtype=object)))
    if row["gallery_tier_validated_available_flag"] > 0:
        row["gallery_feature_source"] = "validated"
    elif row["gallery_tier_raw_available_flag"] > 0:
        row["gallery_feature_source"] = "raw"
    else:
        row["gallery_feature_source"] = "missing"

    row["artist_name_ko_normalized"] = normalize_name(row.get("name_ko"))
    row["artist_name_en_normalized"] = normalize_name(row.get("name_en"))
    row["feature_cache_version"] = "official_v0_1_artist_external_feature_cache"
    row["created_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    return row


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    external = build_external_row_map()
    artist_map = load_artist_map()
    merged = external.merge(artist_map, left_on="_track6_row_id", right_on="track6_row_id", how="inner")
    if merged.empty:
        raise RuntimeError("No row-level external features matched official v0.1 DB observations.")

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
    out.to_csv(OUT_CSV, index=False)
    summary = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_rows": int(len(external)),
        "matched_rows": int(len(merged)),
        "artist_count": int(out["artist_key"].nunique()),
        "output_csv": str(OUT_CSV.relative_to(REPO)),
        "available_gallery_artist_count": int((out["gallery_tier_any_available_flag"].fillna(0) > 0).sum()),
        "available_exhibition_artist_count": int((out["artist_exhibition_available_count"].fillna(0) > 0).sum()),
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
