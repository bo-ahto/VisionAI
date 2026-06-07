#!/usr/bin/env python3
"""Add reusable Track6 size/ho features to the latest enriched split.

This script keeps the existing split unchanged and creates a new split copy:
`data/track6_split_with_year_type_edition_size`.

The ho conversion uses the same F-size area table that was used in the A1
sample experiment, but moves the calculation into the dataset pipeline so later
experiments can use the same feature consistently.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SOURCE_DATA = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition.csv"
OUT_DATA = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition_size.csv"
SPLIT_DIR = REPO / "data" / "track6_split_with_year_type_edition"
OUT_SPLIT_DIR = REPO / "data" / "track6_split_with_year_type_edition_size"
QUALITY_DIR = REPO / "data" / "track6" / "quality"

SIZE_COLS = ["estimated_ho", "ln_estimated_ho"]

# F-type canvas area table used in the prior A1 ho/size experiment.
HO_TABLE_F = {
    0: 180,
    1: 364,
    2: 520,
    3: 727,
    4: 1084,
    5: 1167,
    6: 1338,
    8: 1818,
    10: 2412,
    12: 2757,
    15: 3478,
    20: 4304,
    25: 5323,
    30: 5858,
    40: 7320,
    50: 9128,
    60: 12636,
    80: 16918,
    100: 21245,
    120: 25740,
    150: 33894,
    200: 43980,
    300: 67060,
    500: 121898,
}


def area_to_ho(area: object) -> float:
    value = pd.to_numeric(area, errors="coerce")
    if not np.isfinite(value) or value <= 0:
        return np.nan
    return float(min(HO_TABLE_F, key=lambda ho: abs(float(HO_TABLE_F[ho]) - float(value))))


def add_size_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.drop(columns=[c for c in SIZE_COLS if c in df.columns], errors="ignore").copy()
    out["area_cm2"] = pd.to_numeric(out["area_cm2"], errors="coerce")
    out["estimated_ho"] = out["area_cm2"].apply(area_to_ho)
    out["ln_estimated_ho"] = np.log(out["estimated_ho"].clip(lower=0.01))
    return out


def summarize(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "estimated_ho_missing": int(df["estimated_ho"].isna().sum()),
        "ln_estimated_ho_missing": int(df["ln_estimated_ho"].isna().sum()),
        "estimated_ho_counts_top10": df["estimated_ho"].value_counts(dropna=False).head(10).to_dict(),
    }


def write_split_copy(summary: dict) -> None:
    if OUT_SPLIT_DIR.exists():
        shutil.rmtree(OUT_SPLIT_DIR)
    shutil.copytree(SPLIT_DIR, OUT_SPLIT_DIR)

    csv_files = [
        *OUT_SPLIT_DIR.glob("*.csv"),
        *OUT_SPLIT_DIR.glob("features/warm/*.csv"),
        *OUT_SPLIT_DIR.glob("features/cold/*.csv"),
    ]
    for path in sorted(csv_files):
        df = pd.read_csv(path, low_memory=False)
        if "area_cm2" not in df.columns:
            continue
        out = add_size_cols(df)
        out.to_csv(path, index=False)
        summary["files"][str(path.relative_to(REPO))] = summarize(out)


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_data": str(SOURCE_DATA.relative_to(REPO)),
        "output_data": str(OUT_DATA.relative_to(REPO)),
        "source_split": str(SPLIT_DIR.relative_to(REPO)),
        "output_split": str(OUT_SPLIT_DIR.relative_to(REPO)),
        "ho_table": "F-size area nearest match",
        "files": {},
    }

    full = pd.read_csv(SOURCE_DATA, low_memory=False)
    full_out = add_size_cols(full)
    full_out.to_csv(OUT_DATA, index=False)
    summary["files"][str(OUT_DATA.relative_to(REPO))] = summarize(full_out)

    write_split_copy(summary)

    out_summary = QUALITY_DIR / "track6_size_ho_enrichment_summary.json"
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
