#!/usr/bin/env python3
"""Build Track6 split copies with year, type, and edition columns."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SPLIT_DIR = REPO / "data" / "track6_split_with_year_type"
OUT_DIR = REPO / "data" / "track6_split_with_year_type_edition"
EDITION_DATA = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition.csv"
EDITION_COLS = [
    "edition_class",
    "is_edition",
    "is_limited_edition",
    "is_open_edition",
    "is_unknown_edition",
    "is_unique_work",
    "edition_info_available",
    "edition_source",
]
KEYS = ["track4_source", "track4_source_row_index"]


def merge_edition_cols(df: pd.DataFrame, edition_lookup: pd.DataFrame) -> pd.DataFrame:
    out = df.drop(columns=[c for c in EDITION_COLS if c in df.columns], errors="ignore").copy()
    out["track4_source_row_index"] = pd.to_numeric(out["track4_source_row_index"], errors="coerce").astype("Int64")
    return out.merge(edition_lookup, on=KEYS, how="left")


def summarize(out: pd.DataFrame) -> dict:
    return {
        "rows": int(len(out)),
        "edition_class_counts": out["edition_class"].value_counts(dropna=False).to_dict(),
        "is_edition_counts": out["is_edition"].value_counts(dropna=False).to_dict(),
        "edition_info_available_rate": float(out["edition_info_available"].mean()),
    }


def main() -> None:
    edition_df = pd.read_csv(EDITION_DATA, low_memory=False)
    edition_df["track4_source_row_index"] = pd.to_numeric(
        edition_df["track4_source_row_index"], errors="coerce"
    ).astype("Int64")
    edition_lookup = edition_df[KEYS + EDITION_COLS].drop_duplicates(KEYS)

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
        out = merge_edition_cols(df, edition_lookup)
        out.to_csv(OUT_DIR / name, index=False)
        summary["files"][name] = summarize(out)

    shutil.copy2(SPLIT_DIR / "track6_split_membership.csv", OUT_DIR / "track6_split_membership.csv")
    shutil.copy2(SPLIT_DIR / "track6_split_summary.json", OUT_DIR / "track6_split_summary.json")
    if (SPLIT_DIR / "track6_split_with_year_type_summary.json").exists():
        shutil.copy2(
            SPLIT_DIR / "track6_split_with_year_type_summary.json",
            OUT_DIR / "track6_split_with_year_type_summary.json",
        )

    split_by_kind = {
        "track6_train_warm_features.csv": "track6_train.csv",
        "track6_train_cold_features.csv": "track6_train.csv",
        "track6_val_warm_warm_features.csv": "track6_val_warm.csv",
        "track6_test_warm_warm_features.csv": "track6_test_warm.csv",
        "track6_val_cold_cold_features.csv": "track6_val_cold.csv",
        "track6_test_cold_cold_features.csv": "track6_test_cold.csv",
    }
    feature_rels = [
        Path("features/warm/track6_train_warm_features.csv"),
        Path("features/cold/track6_train_cold_features.csv"),
        Path("features/warm/track6_val_warm_warm_features.csv"),
        Path("features/warm/track6_test_warm_warm_features.csv"),
        Path("features/cold/track6_val_cold_cold_features.csv"),
        Path("features/cold/track6_test_cold_cold_features.csv"),
    ]
    for rel in feature_rels:
        features = pd.read_csv(SPLIT_DIR / rel, low_memory=False)
        full_split = pd.read_csv(OUT_DIR / split_by_kind[rel.name], low_memory=False)
        join_cols = ["_track6_row_id", *EDITION_COLS]
        out = features.drop(columns=[c for c in EDITION_COLS if c in features.columns], errors="ignore")
        out = out.merge(full_split[join_cols], on="_track6_row_id", how="left")
        out_path = OUT_DIR / rel
        out.to_csv(out_path, index=False)
        summary["files"][str(rel)] = summarize(out)

    for label in (SPLIT_DIR / "labels").glob("*.csv"):
        shutil.copy2(label, OUT_DIR / "labels" / label.name)

    (OUT_DIR / "track6_split_with_year_type_edition_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
