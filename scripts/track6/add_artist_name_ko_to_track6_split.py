#!/usr/bin/env python3
"""Add artist_name_ko to a Track6 split without mutating the original split."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size"
TARGET_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"

FULL_SPLIT_FILES = [
    SOURCE_ROOT / "track6_train.csv",
    SOURCE_ROOT / "track6_test_warm.csv",
    SOURCE_ROOT / "track6_test_cold.csv",
]

FEATURE_FILES = [
    TARGET_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
    TARGET_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv",
    TARGET_ROOT / "features" / "cold" / "track6_test_cold_cold_features.csv",
]


def build_artist_name_map() -> pd.DataFrame:
    frames = []
    for path in FULL_SPLIT_FILES:
        df = pd.read_csv(path, usecols=["_track6_row_id", "artist_name_ko"], low_memory=False)
        frames.append(df)
    mapping = pd.concat(frames, ignore_index=True).drop_duplicates("_track6_row_id")
    mapping["artist_name_ko"] = mapping["artist_name_ko"].astype("string").fillna("__missing__")
    return mapping


def enrich_feature_file(path: Path, mapping: pd.DataFrame) -> dict[str, int | str]:
    df = pd.read_csv(path, low_memory=False)
    if "artist_name_ko" in df.columns:
        df = df.drop(columns=["artist_name_ko"])
    before_cols = len(df.columns)
    out = df.merge(mapping, on="_track6_row_id", how="left")
    out["artist_name_ko"] = out["artist_name_ko"].astype("string").fillna("__missing__")
    out.to_csv(path, index=False)
    return {
        "path": str(path.relative_to(REPO)),
        "rows": int(len(out)),
        "columns_before": int(before_cols),
        "columns_after": int(len(out.columns)),
        "artist_name_ko_missing_or_unmatched": int(out["artist_name_ko"].eq("__missing__").sum()),
        "artist_name_ko_unique": int(out["artist_name_ko"].nunique(dropna=True)),
    }


def main() -> None:
    if TARGET_ROOT.exists():
        shutil.rmtree(TARGET_ROOT)
    shutil.copytree(SOURCE_ROOT, TARGET_ROOT)

    mapping = build_artist_name_map()
    summaries = [enrich_feature_file(path, mapping) for path in FEATURE_FILES]

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_root": str(SOURCE_ROOT.relative_to(REPO)),
        "target_root": str(TARGET_ROOT.relative_to(REPO)),
        "join_key": "_track6_row_id",
        "added_column": "artist_name_ko",
        "policy": "original split is copied first; feature files are enriched by row id from the full split CSV files",
        "files": summaries,
    }
    quality_dir = REPO / "data" / "track6" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "track6_artist_name_split_enrichment_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
