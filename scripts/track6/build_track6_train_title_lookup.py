#!/usr/bin/env python3
"""Build a complete Track6 train title lookup table.

The model feature and label files intentionally omit artwork titles. This
export joins those files back to the full train split by `_track6_row_id` so
training rows can be audited with artwork names.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track6_split"
T0_PATH = REPO / "data" / "dataset_tiers_cleansed_20260508" / "T0_operational_28376_cleansed.csv"
OUT_CSV = SPLIT_DIR / "track6_train_title_lookup_complete.csv"
OUT_SUMMARY = SPLIT_DIR / "track6_train_title_lookup_complete_summary.json"


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_url(value: object) -> str:
    return clean_text(value).rstrip("/")


def url_slug(value: object) -> str:
    url = clean_text(value)
    if not url:
        return ""
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    slug = ""
    if "artwork" in parts:
        idx = parts.index("artwork")
        if idx + 1 < len(parts):
            slug = parts[idx + 1]
    elif "art" in parts:
        idx = parts.index("art")
        if idx + 1 < len(parts):
            slug = parts[idx + 1]
    elif parts:
        slug = parts[-1]
    return unquote(slug).strip()


def first_non_empty(row: pd.Series, columns: list[str]) -> tuple[str, str]:
    for col in columns:
        value = clean_text(row.get(col, ""))
        if value:
            return value, col
    return "", ""


def main() -> None:
    train = pd.read_csv(SPLIT_DIR / "track6_train.csv", dtype=str, low_memory=False)
    labels = pd.read_csv(SPLIT_DIR / "labels" / "track6_train_labels.csv", dtype=str, low_memory=False)
    warm = pd.read_csv(
        SPLIT_DIR / "features" / "warm" / "track6_train_warm_features.csv",
        dtype=str,
        low_memory=False,
    )
    cold = pd.read_csv(
        SPLIT_DIR / "features" / "cold" / "track6_train_cold_features.csv",
        dtype=str,
        low_memory=False,
    )
    t0 = pd.read_csv(T0_PATH, dtype=str, low_memory=False)

    out = train.copy()
    out["title_raw_clean"] = out["title_raw"].map(clean_text)
    out["_artwork_url_norm"] = out["artwork_url"].map(normalize_url)
    out["title_url_slug"] = out["artwork_url"].map(url_slug)

    t0_lookup = t0.copy()
    t0_lookup["title"] = t0_lookup["title"].map(clean_text)
    t0_lookup["_artwork_url_norm"] = t0_lookup["artwork_url"].map(normalize_url)

    by_id = (
        t0_lookup[["artwork_id", "title", "source"]]
        .dropna(subset=["artwork_id"])
        .drop_duplicates("artwork_id")
        .rename(
            columns={
                "artwork_id": "source_artwork_id",
                "title": "title_t0_by_artwork_id",
                "source": "t0_source_by_artwork_id",
            }
        )
    )
    by_url = (
        t0_lookup[["_artwork_url_norm", "title", "source"]]
        .dropna(subset=["_artwork_url_norm"])
        .drop_duplicates("_artwork_url_norm")
        .rename(
            columns={
                "title": "title_t0_by_artwork_url",
                "source": "t0_source_by_artwork_url",
            }
        )
    )

    out = out.merge(by_id, on="source_artwork_id", how="left")
    out = out.merge(by_url, on="_artwork_url_norm", how="left")

    title_values: list[str] = []
    title_sources: list[str] = []
    for _, row in out.iterrows():
        value, source = first_non_empty(
            row,
            [
                "title_raw_clean",
                "title_t0_by_artwork_id",
                "title_t0_by_artwork_url",
                "title_url_slug",
                "source_artwork_id",
            ],
        )
        title_values.append(value)
        title_sources.append(source)
    out["title_resolved"] = title_values
    out["title_resolved_source"] = title_sources

    source_labels = {
        "title_raw_clean": "track6_split.title_raw",
        "title_t0_by_artwork_id": "T0.title matched by source_artwork_id",
        "title_t0_by_artwork_url": "T0.title matched by artwork_url",
        "title_url_slug": "artwork_url slug fallback",
        "source_artwork_id": "source_artwork_id fallback",
    }
    out["title_resolved_source_desc"] = out["title_resolved_source"].map(source_labels).fillna("")

    row_ids = out["_track6_row_id"].map(clean_text)
    label_match = row_ids.isin(set(labels["_track6_row_id"].map(clean_text)))
    warm_feature_match = row_ids.isin(set(warm["_track6_row_id"].map(clean_text)))
    cold_feature_match = row_ids.isin(set(cold["_track6_row_id"].map(clean_text)))
    all_matched = label_match & warm_feature_match & cold_feature_match

    ordered_cols = [
        "_track6_row_id",
        "track4_source",
        "track4_source_row_index",
        "source_artwork_id",
        "artwork_url",
        "image_url",
        "artist_key",
        "artist_name_ko",
        "artist_name_ko_orig",
        "artist_name_standardized",
        "title_resolved",
        "title_resolved_source_desc",
        "title_raw",
        "title_t0_by_artwork_id",
        "title_t0_by_artwork_url",
        "title_url_slug",
        "price_krw",
        "ln_price_krw",
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "collected_material_raw",
        "nant_support",
        "nant_tool",
        "artist_works_count_train",
        "artist_meta_source",
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
    ]
    remaining_cols = [col for col in out.columns if col not in ordered_cols and not col.startswith("_artwork_url_norm")]
    out = out[ordered_cols + remaining_cols]
    out["_track6_row_id_num"] = pd.to_numeric(out["_track6_row_id"], errors="coerce")
    out = out.sort_values("_track6_row_id_num").drop(columns=["_track6_row_id_num"])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_csv": str(OUT_CSV.relative_to(REPO)),
        "rows": int(len(out)),
        "unique_track6_row_id": int(out["_track6_row_id"].nunique()),
        "duplicate_track6_row_id": int(out["_track6_row_id"].duplicated().sum()),
        "label_matched_rows": int(label_match.sum()),
        "warm_feature_matched_rows": int(warm_feature_match.sum()),
        "cold_feature_matched_rows": int(cold_feature_match.sum()),
        "all_feature_label_matched_rows": int(all_matched.sum()),
        "missing_feature_or_label_match_rows": int((~all_matched).sum()),
        "blank_title_raw_rows": int(out["title_raw_clean"].map(clean_text).eq("").sum()),
        "blank_title_resolved_rows": int(out["title_resolved"].map(clean_text).eq("").sum()),
        "title_resolved_source_counts": out["title_resolved_source_desc"].value_counts(dropna=False).to_dict(),
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
