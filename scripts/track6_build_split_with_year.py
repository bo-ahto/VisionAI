#!/usr/bin/env python3
"""Build Track6 split copies with artwork year columns.

This script mirrors `data/track6_split` into `data/track6_split_with_year`
without modifying the existing split. Year features are merged from
`track6_feature_candidates_name_corrected_with_year.csv` by
`track4_source + track4_source_row_index`.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SPLIT_DIR = REPO / "data" / "track6_split"
OUT_DIR = REPO / "data" / "track6_split_with_year"
YEAR_DATA = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year.csv"
YEAR_COLS = [
    "artwork_year",
    "has_artwork_year",
    "artwork_age",
    "artwork_year_source",
    "artwork_year_match_method",
    "artwork_year_missing",
]
KEYS = ["track4_source", "track4_source_row_index"]


def merge_year_cols(df: pd.DataFrame, year_lookup: pd.DataFrame) -> pd.DataFrame:
    out = df.drop(columns=[c for c in YEAR_COLS if c in df.columns], errors="ignore").copy()
    out["track4_source_row_index"] = pd.to_numeric(out["track4_source_row_index"], errors="coerce").astype("Int64")
    return out.merge(year_lookup, on=KEYS, how="left")


def main() -> None:
    year_df = pd.read_csv(YEAR_DATA, low_memory=False)
    year_df["track4_source_row_index"] = pd.to_numeric(
        year_df["track4_source_row_index"], errors="coerce"
    ).astype("Int64")
    year_lookup = year_df[KEYS + YEAR_COLS].drop_duplicates(KEYS)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "features" / "warm").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "features" / "cold").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "labels").mkdir(parents=True, exist_ok=True)

    split_files = [
        "track6_train.csv",
        "track6_val_warm.csv",
        "track6_test_warm.csv",
        "track6_val_cold.csv",
        "track6_test_cold.csv",
    ]
    summary = {"created_at": datetime.now().isoformat(timespec="seconds"), "files": {}}

    for name in split_files:
        df = pd.read_csv(SPLIT_DIR / name, low_memory=False)
        out = merge_year_cols(df, year_lookup)
        out.to_csv(OUT_DIR / name, index=False)
        summary["files"][name] = {
            "rows": int(len(out)),
            "artwork_year_non_null": int(out["artwork_year"].notna().sum()),
            "artwork_year_fill_rate": float(out["artwork_year"].notna().mean()),
        }

    shutil.copy2(SPLIT_DIR / "track6_split_membership.csv", OUT_DIR / "track6_split_membership.csv")
    summary["files"]["track6_split_membership.csv"] = {
        "rows": int(len(pd.read_csv(OUT_DIR / "track6_split_membership.csv", low_memory=False))),
        "note": "copied unchanged; membership file has no source-row columns",
    }

    # Feature files need source keys from the full split files to merge year columns.
    split_by_kind = {
        "track6_train_warm_features.csv": "track6_train.csv",
        "track6_train_cold_features.csv": "track6_train.csv",
        "track6_val_warm_warm_features.csv": "track6_val_warm.csv",
        "track6_test_warm_warm_features.csv": "track6_test_warm.csv",
        "track6_val_cold_cold_features.csv": "track6_val_cold.csv",
        "track6_test_cold_cold_features.csv": "track6_test_cold.csv",
    }
    for rel in [
        Path("features/warm/track6_train_warm_features.csv"),
        Path("features/cold/track6_train_cold_features.csv"),
        Path("features/warm/track6_val_warm_warm_features.csv"),
        Path("features/warm/track6_test_warm_warm_features.csv"),
        Path("features/cold/track6_val_cold_cold_features.csv"),
        Path("features/cold/track6_test_cold_cold_features.csv"),
    ]:
        features = pd.read_csv(SPLIT_DIR / rel, low_memory=False)
        full_split = pd.read_csv(OUT_DIR / split_by_kind[rel.name], low_memory=False)
        join_cols = ["_track6_row_id", *YEAR_COLS]
        out = features.drop(columns=[c for c in YEAR_COLS if c in features.columns], errors="ignore")
        out = out.merge(full_split[join_cols], on="_track6_row_id", how="left")
        out_path = OUT_DIR / rel
        out.to_csv(out_path, index=False)
        summary["files"][str(rel)] = {
            "rows": int(len(out)),
            "artwork_year_non_null": int(out["artwork_year"].notna().sum()),
            "artwork_year_fill_rate": float(out["artwork_year"].notna().mean()),
        }

    for label in (SPLIT_DIR / "labels").glob("*.csv"):
        shutil.copy2(label, OUT_DIR / "labels" / label.name)
    shutil.copy2(SPLIT_DIR / "track6_split_summary.json", OUT_DIR / "track6_split_summary.json")
    (OUT_DIR / "track6_split_with_year_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
