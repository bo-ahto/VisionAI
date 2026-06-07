#!/usr/bin/env python3
"""Create a Track6 feature-candidate dataset with artwork year features.

The script does not overwrite the existing Track6 dataset. It restores artwork
year from source-specific raw columns and Saatchi detail-page enrichment, then
writes a new feature-candidate CSV plus an audit summary.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TRACK6_IN = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
SAATCHI_YEAR_JSONL = REPO / "data" / "saatchi_year_enrichment_artifact_20260501" / "raw.jsonl"
TRACK6_OUT = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year.csv"
SUMMARY_OUT = REPO / "data" / "track6" / "quality" / "track6_artwork_year_enrichment_summary.json"

CURRENT_YEAR = 2026
MIN_YEAR = 1800
MAX_YEAR = CURRENT_YEAR


def parse_year(value: Any) -> float:
    """Parse one plausible artwork year from a raw value.

    Returns np.nan for missing, ranges, impossible years, or ambiguous text.
    """
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    match = re.search(r"(18\d{2}|19\d{2}|20\d{2})", text)
    if not match:
        return np.nan
    year = int(match.group(1))
    if year < MIN_YEAR or year > MAX_YEAR:
        return np.nan
    return float(year)


def load_saatchi_year_map(path: Path) -> tuple[dict[str, int], dict[str, Any]]:
    by_url: dict[str, int] = {}
    rows = 0
    ok_rows = 0
    parsed_rows = 0
    extraction_sources: dict[str, int] = {}
    warning_rows = 0

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            rec = json.loads(line)
            status = rec.get("fetch_status")
            if status == "ok":
                ok_rows += 1
            source = rec.get("extraction_source") or "__missing__"
            extraction_sources[source] = extraction_sources.get(source, 0) + 1
            if rec.get("parse_warnings"):
                warning_rows += 1

            url = rec.get("url")
            year = parse_year(rec.get("year_created"))
            if url and status == "ok" and pd.notna(year):
                parsed_rows += 1
                by_url[url] = int(year)

    summary = {
        "artifact_path": str(path.relative_to(REPO)),
        "artifact_rows": rows,
        "fetch_status_ok_rows": ok_rows,
        "valid_year_rows": parsed_rows,
        "unique_url_with_valid_year": len(by_url),
        "extraction_sources": extraction_sources,
        "parse_warning_rows": warning_rows,
        "trust_note": (
            "Saatchi artwork year is not from the original CSV. It is detail-page "
            "HTML enrichment fetched on 2026-05-01 and used only when fetch_status=ok "
            "and year_created is valid."
        ),
    }
    return by_url, summary


def main() -> None:
    track6 = pd.read_csv(TRACK6_IN, low_memory=False)
    raw = pd.read_csv(RAW_COLLECTED, low_memory=False)
    saatchi_year_map, saatchi_summary = load_saatchi_year_map(SAATCHI_YEAR_JSONL)

    raw_lookup_cols = [
        "track4_source",
        "track4_source_row_index",
        "artsy__date",
        "artue__Year",
        "gallery_primary__연도",
        "gallery_primary__exhibition_date",
        "saatchi__artwork_url",
    ]
    raw_lookup = raw[raw_lookup_cols].copy()

    df = track6.copy()
    df["track4_source_row_index"] = pd.to_numeric(df["track4_source_row_index"], errors="coerce").astype("Int64")
    raw_lookup["track4_source_row_index"] = pd.to_numeric(
        raw_lookup["track4_source_row_index"], errors="coerce"
    ).astype("Int64")
    df = df.merge(raw_lookup, on=["track4_source", "track4_source_row_index"], how="left")

    source = df["track4_source"].astype("string")
    artwork_year = pd.Series(np.nan, index=df.index, dtype="float64")
    year_source = pd.Series("__missing__", index=df.index, dtype="string")
    match_method = pd.Series("__missing__", index=df.index, dtype="string")

    # Artsy: artwork date from original artsy artwork crawl.
    artsy_year = df["artsy__date"].map(parse_year)
    mask = source.eq("artsy") & artsy_year.notna()
    artwork_year.loc[mask] = artsy_year.loc[mask]
    year_source.loc[mask] = "artsy__date"
    match_method.loc[mask] = "raw_collected_by_track4_source_row_index"

    # Artue: year column from original Artue sheet/crawl.
    artue_year = df["artue__Year"].map(parse_year)
    mask = source.eq("artue") & artue_year.notna()
    artwork_year.loc[mask] = artue_year.loc[mask]
    year_source.loc[mask] = "artue__Year"
    match_method.loc[mask] = "raw_collected_by_track4_source_row_index"

    # Gallery primary: the available year is usually exhibition/listing year, so keep
    # provenance explicit rather than treating it as a confirmed creation year.
    gallery_year = df["gallery_primary__연도"].map(parse_year)
    mask = source.eq("gallery_primary") & gallery_year.notna()
    artwork_year.loc[mask] = gallery_year.loc[mask]
    year_source.loc[mask] = "gallery_primary__연도"
    match_method.loc[mask] = "raw_collected_listing_year_by_track4_source_row_index"

    # Saatchi: no year in the original CSV, so use detail-page enrichment.
    saatchi_url = df["artwork_url"].fillna(df["saatchi__artwork_url"]).astype("string")
    saatchi_year = saatchi_url.map(saatchi_year_map)
    mask = source.eq("saatchi") & saatchi_year.notna()
    artwork_year.loc[mask] = pd.to_numeric(saatchi_year.loc[mask], errors="coerce")
    year_source.loc[mask] = "saatchi_year_enrichment.year_created"
    match_method.loc[mask] = "detail_page_enrichment_by_artwork_url"

    df["artwork_year"] = artwork_year.astype("Int64")
    df["has_artwork_year"] = df["artwork_year"].notna().astype(int)
    df["artwork_age"] = np.where(df["artwork_year"].notna(), CURRENT_YEAR - df["artwork_year"].astype(float), np.nan)
    df["artwork_year_source"] = year_source
    df["artwork_year_match_method"] = match_method
    df["artwork_year_missing"] = df["artwork_year"].isna().astype(int)

    helper_cols = [
        "artsy__date",
        "artue__Year",
        "gallery_primary__연도",
        "gallery_primary__exhibition_date",
        "saatchi__artwork_url",
    ]
    df = df.drop(columns=[c for c in helper_cols if c in df.columns])

    TRACK6_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRACK6_OUT, index=False)

    by_source = {}
    for src, sub in df.groupby("track4_source", dropna=False):
        by_source[str(src)] = {
            "rows": int(len(sub)),
            "artwork_year_non_null": int(sub["artwork_year"].notna().sum()),
            "artwork_year_fill_rate": float(sub["artwork_year"].notna().mean()),
            "year_source_counts": sub["artwork_year_source"].value_counts(dropna=False).to_dict(),
        }

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(TRACK6_IN.relative_to(REPO)),
        "output_file": str(TRACK6_OUT.relative_to(REPO)),
        "raw_collected_file": str(RAW_COLLECTED.relative_to(REPO)),
        "rows": int(len(df)),
        "artwork_year_non_null": int(df["artwork_year"].notna().sum()),
        "artwork_year_fill_rate": float(df["artwork_year"].notna().mean()),
        "year_range": {
            "min": int(df["artwork_year"].min()) if df["artwork_year"].notna().any() else None,
            "max": int(df["artwork_year"].max()) if df["artwork_year"].notna().any() else None,
            "valid_range": [MIN_YEAR, MAX_YEAR],
        },
        "by_track4_source": by_source,
        "saatchi_enrichment": saatchi_summary,
        "new_columns": [
            "artwork_year",
            "has_artwork_year",
            "artwork_age",
            "artwork_year_source",
            "artwork_year_match_method",
            "artwork_year_missing",
        ],
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
