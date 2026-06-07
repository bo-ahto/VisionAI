#!/usr/bin/env python3
"""Add material columns to Track6 split feature files.

Purpose:
- Keep train/warm/cold split membership unchanged.
- Promote material columns that already exist in `data/track6_split/track6_*.csv`
  into the corresponding feature files.
- Avoid attaching NANT material columns from the full cleaned dataset inside
  each experiment.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SPLIT_DIR = REPO / "data" / "track6_split"

MATERIAL_COLUMNS = [
    "collected_material_raw",
    "nant_support",
    "nant_tool",
    "nant_material_note",
    "nant_material_match_method",
    "nant_material_idx",
]

JOBS = [
    ("track6_train.csv", "features/warm/track6_train_warm_features.csv"),
    ("track6_train.csv", "features/cold/track6_train_cold_features.csv"),
    ("track6_val_warm.csv", "features/warm/track6_val_warm_warm_features.csv"),
    ("track6_test_warm.csv", "features/warm/track6_test_warm_warm_features.csv"),
    ("track6_val_cold.csv", "features/cold/track6_val_cold_cold_features.csv"),
    ("track6_test_cold.csv", "features/cold/track6_test_cold_cold_features.csv"),
]


def load_material_source(path: Path) -> pd.DataFrame:
    usecols = ["_track6_row_id", *MATERIAL_COLUMNS]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    if df["_track6_row_id"].duplicated().any():
        raise ValueError(f"duplicate _track6_row_id in {path}")
    return df


def update_feature_file(split_csv: str, feature_csv: str) -> dict[str, object]:
    split_path = SPLIT_DIR / split_csv
    feature_path = SPLIT_DIR / feature_csv
    features = pd.read_csv(feature_path, low_memory=False)
    material = load_material_source(split_path)
    before_cols = list(features.columns)

    missing_keys = set(features["_track6_row_id"]) - set(material["_track6_row_id"])
    if missing_keys:
        raise ValueError(f"{feature_csv}: {len(missing_keys)} feature rows missing from {split_csv}")

    keep = [c for c in features.columns if c not in MATERIAL_COLUMNS]
    merged = features[keep].merge(material, on="_track6_row_id", how="left", validate="one_to_one")

    if len(merged) != len(features):
        raise ValueError(f"{feature_csv}: row count changed after material merge")
    if not merged["_track6_row_id"].equals(features["_track6_row_id"]):
        raise ValueError(f"{feature_csv}: row order changed after material merge")

    merged.to_csv(feature_path, index=False)
    added = [c for c in MATERIAL_COLUMNS if c not in before_cols]
    refreshed = [c for c in MATERIAL_COLUMNS if c in before_cols]
    return {
        "feature_file": feature_csv,
        "rows": len(merged),
        "added_columns": added,
        "refreshed_columns": refreshed,
    }


def main() -> None:
    results = [update_feature_file(split_csv, feature_csv) for split_csv, feature_csv in JOBS]
    for result in results:
        print(
            f"{result['feature_file']}: rows={result['rows']} "
            f"added={result['added_columns']} refreshed={result['refreshed_columns']}"
        )


if __name__ == "__main__":
    main()
