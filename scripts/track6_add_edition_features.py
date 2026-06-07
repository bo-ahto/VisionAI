#!/usr/bin/env python3
"""Create a Track6 feature-candidate dataset with edition features.

The script restores edition information from source-specific raw columns.
Signed information is not promoted to a model feature because the current
collected data has no structured signed field and title-keyword hits are too
sparse for a controlled A7 experiment.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TRACK6_IN = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type.csv"
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
TRACK6_OUT = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type_edition.csv"
SUMMARY_OUT = REPO / "data" / "track6" / "quality" / "track6_edition_enrichment_summary.json"

KEYS = ["track4_source", "track4_source_row_index"]


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_edition_class(source: str, artsy_attr: Any, saatchi_attr: Any, saatchi_is_edition: Any) -> str:
    src = clean_text(source)
    if src == "artsy":
        text = clean_text(artsy_attr).lower()
        if text == "unique":
            return "unique"
        if text == "limited edition":
            return "limited_edition"
        if text == "open edition":
            return "open_edition"
        if text == "unknown edition":
            return "unknown_edition"
        return "unknown"
    if src == "saatchi":
        text = clean_text(saatchi_attr).lower()
        is_edition_text = clean_text(saatchi_is_edition).lower()
        if text == "unique" or is_edition_text in {"0", "0.0", "false"}:
            return "unique"
        if is_edition_text in {"1", "1.0", "true"}:
            return "limited_edition"
        return "unknown"
    return "unknown"


def main() -> None:
    track6 = pd.read_csv(TRACK6_IN, low_memory=False)
    raw = pd.read_csv(RAW_COLLECTED, low_memory=False)
    track6["track4_source_row_index"] = pd.to_numeric(
        track6["track4_source_row_index"], errors="coerce"
    ).astype("Int64")
    raw["track4_source_row_index"] = pd.to_numeric(raw["track4_source_row_index"], errors="coerce").astype("Int64")

    raw_cols = [
        "track4_source",
        "track4_source_row_index",
        "artsy__attribution_class",
        "artsy__availability",
        "saatchi__attribution_class",
        "saatchi__is_unique",
        "saatchi__is_edition",
    ]
    df = track6.merge(raw[raw_cols], on=KEYS, how="left")

    edition_class = []
    for row in df.itertuples(index=False):
        edition_class.append(
            normalize_edition_class(
                getattr(row, "track4_source", ""),
                getattr(row, "artsy__attribution_class", ""),
                getattr(row, "saatchi__attribution_class", ""),
                getattr(row, "saatchi__is_edition", ""),
            )
        )

    df["edition_class"] = edition_class
    df["is_edition"] = df["edition_class"].isin(["limited_edition", "open_edition", "unknown_edition"]).astype(int)
    df["is_limited_edition"] = df["edition_class"].eq("limited_edition").astype(int)
    df["is_open_edition"] = df["edition_class"].eq("open_edition").astype(int)
    df["is_unknown_edition"] = df["edition_class"].eq("unknown_edition").astype(int)
    df["is_unique_work"] = df["edition_class"].eq("unique").astype(int)
    df["edition_info_available"] = df["edition_class"].ne("unknown").astype(int)
    df["edition_source"] = df["track4_source"].map(
        {
            "artsy": "artsy__attribution_class",
            "saatchi": "saatchi__attribution_class/is_edition",
        }
    ).fillna("__missing__")

    helper_cols = [
        "artsy__attribution_class",
        "artsy__availability",
        "saatchi__attribution_class",
        "saatchi__is_unique",
        "saatchi__is_edition",
    ]
    df = df.drop(columns=[c for c in helper_cols if c in df.columns])

    TRACK6_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRACK6_OUT, index=False)

    by_source = {}
    for src, sub in df.groupby("track4_source", dropna=False):
        by_source[str(src)] = {
            "rows": int(len(sub)),
            "edition_class_counts": sub["edition_class"].value_counts(dropna=False).to_dict(),
            "is_edition_counts": sub["is_edition"].value_counts(dropna=False).to_dict(),
            "edition_info_available_rate": float(sub["edition_info_available"].mean()),
        }

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(TRACK6_IN.relative_to(REPO)),
        "output_file": str(TRACK6_OUT.relative_to(REPO)),
        "rows": int(len(df)),
        "edition_class_counts": df["edition_class"].value_counts(dropna=False).to_dict(),
        "is_edition_counts": df["is_edition"].value_counts(dropna=False).to_dict(),
        "edition_info_available_rate": float(df["edition_info_available"].mean()),
        "by_track4_source": by_source,
        "signed_note": (
            "Structured signed field is unavailable in Track6 raw sources. "
            "Title keyword hits are sparse, so signed is excluded from A7 model inputs."
        ),
        "model_feature_policy": (
            "Use edition_class or derived edition flags as operational input features. "
            "Do not use edition_source as a model feature."
        ),
        "new_columns": [
            "edition_class",
            "is_edition",
            "is_limited_edition",
            "is_open_edition",
            "is_unknown_edition",
            "is_unique_work",
            "edition_info_available",
            "edition_source",
        ],
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
