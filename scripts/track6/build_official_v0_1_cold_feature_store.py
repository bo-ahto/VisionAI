#!/usr/bin/env python3
"""Build row-level Cold feature store for official v0.1.

This cache stores the same PP-Y2 search/external feature columns used by the
Cold fixed-test experiments. It is used for parity replay when an incoming
artwork can be matched to a known source row by artwork_url or source id.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

os.environ.setdefault("MPLCONFIGDIR", str(REPO / ".cache" / "matplotlib"))

import run_pp_y_cold_combination_experiments as ycombo  # noqa: E402


FEATURE_SCHEMA = REPO / "models" / "track6" / "cold_v03_research_upstream_refreeze_candidate" / "artifacts" / "feature_schema.json"
OUT_DIR = REPO / "data" / "track6" / "service_v0_1"
OUT_CSV = OUT_DIR / "official_v0_1_cold_feature_store.csv"
OUT_JSON = OUT_DIR / "official_v0_1_cold_feature_store_summary.json"
SPLIT_ROOT = REPO / "data" / "track6_split"


ID_COLUMNS = [
    "_track6_row_id",
    "split_name",
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artwork_url",
    "artist_key",
    "artist_name_ko",
    "artist_name_standardized",
    "title_raw",
    "price_krw",
    "ln_price_krw",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[()\\[\\]{}.,'\"`~!@#$%^&*_+=:;|/?<>-]", "", text)


def load_features() -> list[str]:
    payload = json.loads(FEATURE_SCHEMA.read_text(encoding="utf-8"))
    return list(payload["pp_y2_feature_columns"])


def load_exact_frames(features: list[str]) -> pd.DataFrame:
    search_df = ycombo.load_search_df()
    train, val, test = ycombo.load_cold_full(features, search_df)
    frames = []
    for split_name, frame in [("train", train), ("validation", val), ("test", test)]:
        part = ycombo.normalize_frame(frame, features).copy()
        part["split_name"] = split_name
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def load_split_identifiers() -> pd.DataFrame:
    frames = []
    for split_file, split_name in [
        ("track6_train.csv", "train"),
        ("track6_val_cold.csv", "validation"),
        ("track6_test_cold.csv", "test"),
    ]:
        path = SPLIT_ROOT / split_file
        part = pd.read_csv(path, low_memory=False)
        keep = [col for col in ID_COLUMNS if col in part.columns and col != "split_name"]
        part = part[keep].copy()
        part["split_name_source"] = split_name
        frames.append(part)
    out = pd.concat(frames, ignore_index=True)
    return out.drop_duplicates("_track6_row_id", keep="first")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    features = load_features()
    frame = load_exact_frames(features)
    identifiers = load_split_identifiers()
    frame = frame.merge(identifiers, on="_track6_row_id", how="left", suffixes=("", "_source"))
    for col in [c for c in ID_COLUMNS if c != "_track6_row_id"]:
        source_col = f"{col}_source"
        if source_col in frame.columns:
            if col in frame.columns:
                frame[col] = frame[col].where(frame[col].notna(), frame[source_col])
            else:
                frame[col] = frame[source_col]
    for col in ID_COLUMNS:
        if col not in frame.columns:
            frame[col] = pd.NA
    out = frame[[*ID_COLUMNS, *features]].copy()
    out["artist_key_normalized"] = out["artist_key"].map(normalize_text)
    out["artist_name_ko_normalized"] = out["artist_name_ko"].map(normalize_text)
    out["source_artwork_id_normalized"] = out["source_artwork_id"].map(normalize_text)
    out["artwork_url_normalized"] = out["artwork_url"].astype("string").fillna("").str.strip()
    out["feature_store_version"] = "official_v0_1_cold_feature_store"
    out["created_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    out = out.drop_duplicates("_track6_row_id", keep="first")
    out.to_csv(OUT_CSV, index=False)
    summary: dict[str, Any] = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "output_csv": str(OUT_CSV.relative_to(REPO)),
        "row_count": int(len(out)),
        "feature_count": int(len(features)),
        "artist_count": int(out["artist_key_normalized"].nunique()),
        "split_counts": {str(k): int(v) for k, v in out["split_name"].value_counts(dropna=False).to_dict().items()},
        "search_covered_rows": int(pd.to_numeric(out["search_collected_flag"], errors="coerce").fillna(0.0).gt(0).sum()),
        "search_coverage_rate": float(pd.to_numeric(out["search_collected_flag"], errors="coerce").fillna(0.0).gt(0).mean()),
        "external_gallery_rows": int(pd.to_numeric(out["gallery_tier_any_available_flag"], errors="coerce").fillna(0.0).gt(0).sum()),
        "external_exhibition_rows": int(pd.to_numeric(out["artist_exhibition_available_count"], errors="coerce").fillna(0.0).gt(0).sum()),
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
