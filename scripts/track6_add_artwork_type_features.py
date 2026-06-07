#!/usr/bin/env python3
"""Create a Track6 feature-candidate dataset with artwork type features.

The script does not use data source as a model feature. Source-specific raw
columns are used only to restore an operational artwork type value such as
painting, print, sculpture, photography, drawing, mixed_media, or unknown.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
TRACK6_IN = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year.csv"
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
SAATCHI_CSV = REPO / "data" / "saatchi_kr_artworks.csv"
ARTSY_CSV = REPO / "data" / "artsy_kr_artworks.csv"
TRACK6_OUT = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected_with_year_type.csv"
SUMMARY_OUT = REPO / "data" / "track6" / "quality" / "track6_artwork_type_enrichment_summary.json"

KEYS = ["track4_source", "track4_source_row_index"]


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_type(value: Any) -> str:
    text = clean_text(value).lower()
    if not text or text in {"nan", "none", "<na>", "-", "__missing__"}:
        return "unknown"

    # Ordered from more specific to broad because some terms overlap.
    if any(k in text for k in ["printmaking", "prints", "print", "poster", "pigmentprint", "판화", "프린트"]):
        return "print"
    if any(k in text for k in ["sculpture", "sculpt", "ceramic", "porcelain", "조각", "입체", "도자"]):
        return "sculpture"
    if any(k in text for k in ["photography", "photo", "사진"]):
        return "photography"
    if any(k in text for k in ["drawing", "work on paper", "collage", "드로잉", "콜라주"]):
        return "drawing"
    if any(k in text for k in ["painting", "회화", "유화", "아크릴", "acrylic", "oil on", "oil paint"]):
        return "painting"
    if any(k in text for k in ["mixed media", "mixed-media", "mixed", "혼합", "복합"]):
        return "mixed_media"
    if any(k in text for k in ["installation", "설치"]):
        return "installation"
    if any(k in text for k in ["digital", "nft", "video", "film", "animation", "디지털", "영상"]):
        return "digital_video"
    if any(k in text for k in ["textile", "fabric", "섬유"]):
        return "textile"
    if any(k in text for k in ["design", "decorative", "architecture", "book"]):
        return "design_other"
    return "other"


def saatchi_type_from_url(url: Any) -> str:
    text = clean_text(url)
    match = re.search(r"/art/([^-/]+)-", text)
    if not match:
        return "unknown"
    return normalize_type(match.group(1))


def major3(value: str) -> str:
    if value in {"painting", "print", "sculpture"}:
        return value
    return "other_unknown"


def infer_type_from_material_support(row: Any) -> str:
    """Infer artwork type only when direct source type is unavailable."""
    texts = [
        clean_text(getattr(row, "medium_category", "")),
        clean_text(getattr(row, "support_category", "")),
        clean_text(getattr(row, "medium_support_bucket", "")),
        clean_text(getattr(row, "nant_tool", "")),
        clean_text(getattr(row, "nant_material_idx", "")),
        clean_text(getattr(row, "nant_support", "")),
        clean_text(getattr(row, "title_raw", "")),
    ]
    text = " ".join(t for t in texts if t).lower()
    if not text:
        return "unknown"

    if any(k in text for k in ["print", "판화", "인쇄", "실크스크린"]):
        return "print"
    if any(k in text for k in ["sculpture_material", "sculpture", "조각", "도자", "ceramic", "porcelain"]):
        return "sculpture"
    if any(k in text for k in ["photo", "photography", "사진"]):
        return "photography"
    if any(k in text for k in ["digital", "디지털"]):
        return "digital_video"
    if any(k in text for k in ["collage", "drawing", "charcoal", "pencil", "드로잉", "연필", "차콜", "콜라주"]):
        return "drawing"
    if any(
        k in text
        for k in [
            "oil",
            "acrylic",
            "gouache",
            "pastel",
            "ink",
            "watercolor",
            "painting_material",
            "유화",
            "아크릴",
            "수채",
            "채색",
            "수묵",
            "옻칠",
        ]
    ):
        return "painting"
    if any(k in text for k in ["mixed_media", "mixed", "혼합재료", "혼합"]):
        return "mixed_media"
    if any(k in text for k in ["textile", "섬유"]):
        return "textile"
    return "unknown"


def main() -> None:
    track6 = pd.read_csv(TRACK6_IN, low_memory=False)
    raw = pd.read_csv(RAW_COLLECTED, low_memory=False)

    df = track6.copy()
    df["track4_source_row_index"] = pd.to_numeric(df["track4_source_row_index"], errors="coerce").astype("Int64")
    raw["track4_source_row_index"] = pd.to_numeric(raw["track4_source_row_index"], errors="coerce").astype("Int64")

    raw_cols = [
        "track4_source",
        "track4_source_row_index",
        "artsy__category",
        "artsy__medium_type",
        "artue__Medium (EN)",
        "artue__Medium (KO)",
        "gallery_primary__exhibition_type",
    ]
    raw_lookup = raw[[c for c in raw_cols if c in raw.columns]].copy()
    df = df.merge(raw_lookup, on=KEYS, how="left")

    saatchi_lookup = pd.DataFrame(columns=["artwork_url", "saatchi_category"])
    if SAATCHI_CSV.exists():
        saatchi = pd.read_csv(SAATCHI_CSV, usecols=["artwork_url", "category"], low_memory=False)
        saatchi_lookup = saatchi.rename(columns={"category": "saatchi_category"}).drop_duplicates("artwork_url")
        df = df.merge(saatchi_lookup, on="artwork_url", how="left")
    else:
        df["saatchi_category"] = pd.NA

    artsy_lookup = pd.DataFrame(columns=["artwork_url", "artsy_category_direct", "artsy_medium_type_direct"])
    if ARTSY_CSV.exists():
        artsy = pd.read_csv(ARTSY_CSV, usecols=["artwork_url", "category", "medium_type"], low_memory=False)
        artsy_lookup = artsy.rename(
            columns={"category": "artsy_category_direct", "medium_type": "artsy_medium_type_direct"}
        ).drop_duplicates("artwork_url")
        df = df.merge(artsy_lookup, on="artwork_url", how="left")
    else:
        df["artsy_category_direct"] = pd.NA
        df["artsy_medium_type_direct"] = pd.NA

    artwork_type_raw = []
    artwork_type_source = []
    artwork_type_method = []

    for row in df.itertuples(index=False):
        src = clean_text(getattr(row, "track4_source", ""))
        raw_value = ""
        source_col = "__missing__"
        method = "__missing__"

        if src == "saatchi":
            raw_value = clean_text(getattr(row, "saatchi_category", ""))
            if raw_value:
                source_col = "saatchi_kr_artworks.category"
                method = "artwork_url_exact_match"
            else:
                raw_value = clean_text(getattr(row, "artwork_url", ""))
                source_col = "artwork_url"
                method = "saatchi_url_category_prefix"
        elif src == "artsy":
            raw_value = clean_text(getattr(row, "artsy_category_direct", "")) or clean_text(
                getattr(row, "artsy__category", "")
            )
            if raw_value:
                source_col = "artsy.category"
                method = "artwork_url_or_raw_row_match"
            else:
                raw_value = clean_text(getattr(row, "artsy_medium_type_direct", "")) or clean_text(
                    getattr(row, "artsy__medium_type", "")
                )
                source_col = "artsy.medium_type"
                method = "artwork_url_or_raw_row_match"
        elif src == "artue":
            raw_value = clean_text(getattr(row, "artue__Medium (EN)", "")) or clean_text(
                getattr(row, "artue__Medium (KO)", "")
            )
            source_col = "artue.medium_text"
            method = "medium_text_keyword_inference"
        else:
            raw_value = clean_text(getattr(row, "medium_category", ""))
            source_col = "medium_category"
            method = "fallback_medium_category_keyword_inference"

        if src == "saatchi" and source_col == "artwork_url":
            normalized = saatchi_type_from_url(raw_value)
        else:
            normalized = normalize_type(raw_value)

        artwork_type_raw.append(raw_value if raw_value else "__missing__")
        artwork_type_source.append(source_col)
        artwork_type_method.append(method)

    df["artwork_type_raw"] = artwork_type_raw
    df["artwork_type_source"] = artwork_type_source
    df["artwork_type_match_method"] = artwork_type_method

    normalized = []
    for raw_value, source_col in zip(df["artwork_type_raw"], df["artwork_type_source"], strict=True):
        if source_col == "artwork_url":
            normalized.append(saatchi_type_from_url(raw_value))
        else:
            normalized.append(normalize_type(raw_value))
    df["artwork_type"] = normalized
    df["artwork_type_major3"] = df["artwork_type"].map(major3)
    df["artwork_type_missing"] = df["artwork_type"].eq("unknown").astype(int)

    inferred = []
    final_type = []
    confidence = []
    for row in df.itertuples(index=False):
        direct_type = clean_text(getattr(row, "artwork_type", "unknown")) or "unknown"
        inferred_type = infer_type_from_material_support(row)
        inferred.append(inferred_type)
        if direct_type != "unknown":
            final_type.append(direct_type)
            confidence.append("direct")
        elif inferred_type != "unknown":
            final_type.append(inferred_type)
            confidence.append("inferred")
        else:
            final_type.append("unknown")
            confidence.append("unknown")

    df["artwork_type_inferred"] = inferred
    df["artwork_type_final"] = final_type
    df["artwork_type_final_major3"] = df["artwork_type_final"].map(major3)
    df["artwork_type_confidence"] = confidence

    helper_cols = [
        "artsy__category",
        "artsy__medium_type",
        "artue__Medium (EN)",
        "artue__Medium (KO)",
        "gallery_primary__exhibition_type",
        "saatchi_category",
        "artsy_category_direct",
        "artsy_medium_type_direct",
    ]
    df = df.drop(columns=[c for c in helper_cols if c in df.columns])

    TRACK6_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRACK6_OUT, index=False)

    by_source = {}
    for src, sub in df.groupby("track4_source", dropna=False):
        by_source[str(src)] = {
            "rows": int(len(sub)),
            "artwork_type_counts": sub["artwork_type"].value_counts(dropna=False).to_dict(),
            "major3_counts": sub["artwork_type_major3"].value_counts(dropna=False).to_dict(),
            "missing_rate": float(sub["artwork_type"].eq("unknown").mean()),
        }

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(TRACK6_IN.relative_to(REPO)),
        "output_file": str(TRACK6_OUT.relative_to(REPO)),
        "rows": int(len(df)),
        "artwork_type_counts": df["artwork_type"].value_counts(dropna=False).to_dict(),
        "artwork_type_major3_counts": df["artwork_type_major3"].value_counts(dropna=False).to_dict(),
        "artwork_type_inferred_counts": df["artwork_type_inferred"].value_counts(dropna=False).to_dict(),
        "artwork_type_final_counts": df["artwork_type_final"].value_counts(dropna=False).to_dict(),
        "artwork_type_final_major3_counts": df["artwork_type_final_major3"].value_counts(dropna=False).to_dict(),
        "artwork_type_confidence_counts": df["artwork_type_confidence"].value_counts(dropna=False).to_dict(),
        "unknown_rows": int(df["artwork_type"].eq("unknown").sum()),
        "unknown_rate": float(df["artwork_type"].eq("unknown").mean()),
        "final_unknown_rows": int(df["artwork_type_final"].eq("unknown").sum()),
        "final_unknown_rate": float(df["artwork_type_final"].eq("unknown").mean()),
        "by_track4_source": by_source,
        "model_feature_policy": (
            "Use artwork_type or artwork_type_major3 as operational input features. "
            "Do not use artwork_type_source, artwork_type_raw, or match method as model features."
        ),
        "new_columns": [
            "artwork_type",
            "artwork_type_major3",
            "artwork_type_inferred",
            "artwork_type_final",
            "artwork_type_final_major3",
            "artwork_type_confidence",
            "artwork_type_raw",
            "artwork_type_source",
            "artwork_type_match_method",
            "artwork_type_missing",
        ],
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
