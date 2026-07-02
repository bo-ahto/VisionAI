"""Build Track 4 primary-market cleaned v1 dataset.

Input:
- data/track4_primary_market_raw_unified.csv

Output:
- data/track4_primary_market_cleaned_v1.csv
- data/track4_primary_market_cleaned_v1_summary.json

Policy:
- Keep rows but add cleaning flags and is_training_candidate.
- Do not use source/gallery as production model features yet.
- Validate gallery_name/gallery_tier as metadata only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
RAW_PATH = DATA / "track4_primary_market_raw_unified.csv"
TIER_PATH = DATA / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
OUT_CSV = DATA / "track4_primary_market_cleaned_v1.csv"
OUT_SUMMARY = DATA / "track4_primary_market_cleaned_v1_summary.json"


def norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\(\)\[\]{}·.,&'\"]", "", text)
    return text


def canonical_gallery_name(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = re.sub(r"\s+", " ", str(value).strip())
    return text or None


def load_gallery_tier_reference() -> dict[str, dict[str, str]]:
    if not TIER_PATH.exists():
        return {}
    ref = pd.read_csv(TIER_PATH)
    mapping: dict[str, dict[str, str]] = {}
    for _, row in ref.iterrows():
        name = str(row["명칭"]).strip()
        if not name:
            continue
        payload = {"tier": str(row["티어"]).strip(), "category": str(row["분류"]).strip(), "matched_name": name}
        mapping[norm_text(name)] = payload
        # Common English aliases visible in the raw primary-market data.
        aliases = {
            "타데우스 로팍": ["타데우스 로팍", "thaddaeus ropac", "thaddaeus ropac seoul"],
            "이화익갤러리": ["leehwaik gallery", "lee hwaik gallery"],
            "아트소향": ["art sohyang"],
            "갤러리 플래닛": ["gallery planet"],
            "초이앤초이 갤러리": ["choi&choi", "choi choi", "choi and choi"],
            "김리아갤러리": ["kimreeaa gallery", "kimreeaa"],
            "BHAK(비에이치에이케이)": ["bhak"],
        }.get(name, [])
        for alias in aliases:
            mapping[norm_text(alias)] = payload
    manual_aliases = {
        "타데우스 로팍": {"tier": "Tier A", "category": "갤러리", "matched_name": "타데우스 로팍 서울"},
        "thaddaeus ropac": {"tier": "Tier A", "category": "갤러리", "matched_name": "타데우스 로팍 서울"},
        "리만머핀 갤러리": {"tier": "Tier A", "category": "갤러리", "matched_name": "리만머핀 서울"},
        "lehmann maupin": {"tier": "Tier A", "category": "갤러리", "matched_name": "리만머핀 서울"},
        "갤러리기체": {"tier": "Tier C", "category": "하이-엔드 라이징/이머징", "matched_name": "갤러리 기체"},
        "야리라거 갤러리": {"tier": "Tier C", "category": "하이-엔드 라이징/이머징", "matched_name": "야리 라거"},
        "yari lager gallery": {"tier": "Tier C", "category": "하이-엔드 라이징/이머징", "matched_name": "야리 라거"},
    }
    for alias, payload in manual_aliases.items():
        mapping[norm_text(alias)] = payload
    return mapping


def validate_gallery(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    tier_ref = load_gallery_tier_reference()
    df["gallery_name_clean"] = df["gallery_name"].map(canonical_gallery_name)
    df["gallery_tier_raw"] = df["gallery_tier"]
    df["gallery_tier_is_actual_tier"] = df["gallery_tier"].astype(str).str.match(r"^Tier [A-E]$", na=False)
    df["gallery_tier_validated"] = None
    df["gallery_tier_match_source"] = "unmatched"

    for idx, name in df["gallery_name_clean"].items():
        key = norm_text(name)
        if key in tier_ref:
            df.at[idx, "gallery_tier_validated"] = tier_ref[key]["tier"]
            df.at[idx, "gallery_tier_match_source"] = "tier_reference"

    # Raw source-specific values are not actual tiers.
    df.loc[df["source"].eq("saatchi"), "gallery_tier_match_source"] = df.loc[
        df["source"].eq("saatchi"), "gallery_tier_match_source"
    ].where(df["gallery_tier_validated"].notna(), "platform_default")
    df.loc[df["source"].eq("artsy") & df["gallery_tier_validated"].isna(), "gallery_tier_match_source"] = "raw_gallery_type_only"
    df.loc[df["gallery_name_clean"].isna(), "gallery_tier_match_source"] = "missing_gallery_name"
    return df


def add_exclusion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    reasons: list[list[str]] = [[] for _ in range(len(df))]

    def mark(mask: pd.Series, reason: str) -> None:
        for pos in np.flatnonzero(mask.to_numpy()):
            reasons[pos].append(reason)

    price = pd.to_numeric(df["price_krw"], errors="coerce")
    width = pd.to_numeric(df["width_cm"], errors="coerce")
    height = pd.to_numeric(df["height_cm"], errors="coerce")
    depth = pd.to_numeric(df["depth_cm"], errors="coerce")
    aspect = pd.to_numeric(df["aspect_ratio"], errors="coerce")
    year = pd.to_numeric(df["year_made"], errors="coerce")

    mark(df["artist_name_raw"].isna() | df["artist_name_raw"].astype(str).str.strip().eq(""), "missing_artist")
    mark(df["title"].isna() | df["title"].astype(str).str.strip().eq(""), "missing_title")
    mark(price.isna() | (price <= 0), "missing_or_non_positive_price")
    mark(price < 10_000, "price_under_10000")
    mark(price > 1_000_000_000, "price_over_1b")
    mark(width.isna() | height.isna(), "missing_width_height")
    mark((width <= 0) | (height <= 0), "non_positive_width_height")
    mark((width > 1000) | (height > 1000), "width_height_over_1000cm")
    mark(aspect.notna() & ((aspect < 0.05) | (aspect > 20)), "extreme_aspect_ratio")
    mark(depth.notna() & (depth < 0), "negative_depth")
    mark(depth.notna() & (depth > 300), "depth_over_300cm")
    mark(year.notna() & ((year < 1000) | (year > 2026)), "invalid_year_made")
    if "is_excluded_for_training" in df.columns:
        mark(pd.to_numeric(df["is_excluded_for_training"], errors="coerce").fillna(0).eq(1), "source_excluded_for_training")

    df["cleaning_exclude_reasons"] = [";".join(items) for items in reasons]
    df["is_training_candidate"] = df["cleaning_exclude_reasons"].eq("").astype(int)

    # Invalid years are not useful but do not need to poison the whole row if
    # future models simply ignore year. Keep both raw and cleaned year.
    df["year_made_clean"] = year.where(year.between(1000, 2026))
    return df


def add_dedupe_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    key = [
        df["source"].fillna("").astype(str).str.lower().str.strip(),
        df["artist_name_raw"].fillna("").astype(str).str.lower().str.strip(),
        df["title"].fillna("").astype(str).str.lower().str.strip(),
        df["price_krw"].round(0).astype("Int64").astype(str),
        df["width_cm"].round(1).astype(str),
        df["height_cm"].round(1).astype(str),
    ]
    composite = key[0]
    for part in key[1:]:
        composite = composite + "|" + part
    df["semantic_duplicate_key"] = composite
    df["is_semantic_duplicate"] = df.duplicated("semantic_duplicate_key", keep=False).astype(int)
    df["is_semantic_duplicate_keep"] = (~df.duplicated("semantic_duplicate_key", keep="first")).astype(int)
    df.loc[(df["is_semantic_duplicate"] == 1) & (df["is_semantic_duplicate_keep"] == 0), "is_training_candidate"] = 0
    df.loc[(df["is_semantic_duplicate"] == 1) & (df["is_semantic_duplicate_keep"] == 0), "cleaning_exclude_reasons"] = (
        df.loc[(df["is_semantic_duplicate"] == 1) & (df["is_semantic_duplicate_keep"] == 0), "cleaning_exclude_reasons"]
        .replace("", np.nan)
        .fillna("semantic_duplicate_drop")
        .astype(str)
        .where(
            df.loc[(df["is_semantic_duplicate"] == 1) & (df["is_semantic_duplicate_keep"] == 0), "cleaning_exclude_reasons"].eq(""),
            df.loc[(df["is_semantic_duplicate"] == 1) & (df["is_semantic_duplicate_keep"] == 0), "cleaning_exclude_reasons"] + ";semantic_duplicate_drop",
        )
    )
    return df


def build_summary(df: pd.DataFrame) -> dict:
    candidate = df[df["is_training_candidate"] == 1]
    reason_counts: dict[str, int] = {}
    for value in df["cleaning_exclude_reasons"].dropna():
        if not value:
            continue
        for reason in str(value).split(";"):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    gallery_match_counts = {
        str(k): int(v) for k, v in df["gallery_tier_match_source"].value_counts(dropna=False).items()
    }
    gallery_tier_counts = {
        str(k): int(v) for k, v in df["gallery_tier_validated"].fillna("unmatched").value_counts().items()
    }
    return {
        "created_at": "2026-05-15",
        "input": str(RAW_PATH.relative_to(REPO)),
        "output": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(df)),
        "n_training_candidates": int(len(candidate)),
        "n_excluded": int(len(df) - len(candidate)),
        "source_counts": {str(k): int(v) for k, v in df["source"].value_counts().items()},
        "training_candidate_source_counts": {str(k): int(v) for k, v in candidate["source"].value_counts().items()},
        "exclude_reason_counts": reason_counts,
        "gallery_validation": {
            "gallery_name_missing": int(df["gallery_name_clean"].isna().sum()),
            "raw_gallery_tier_values": {str(k): int(v) for k, v in df["gallery_tier_raw"].fillna("missing").value_counts().items()},
            "gallery_tier_match_source_counts": gallery_match_counts,
            "gallery_tier_validated_counts": gallery_tier_counts,
            "note": "gallery_tier_raw from Saatchi/Artsy is not an actual A-E tier. Use gallery_tier_validated only for audit, not as a production feature yet.",
        },
        "price_summary_training_candidates": {
            "median": float(candidate["price_krw"].median()) if len(candidate) else None,
            "q25": float(candidate["price_krw"].quantile(0.25)) if len(candidate) else None,
            "q75": float(candidate["price_krw"].quantile(0.75)) if len(candidate) else None,
            "max": float(candidate["price_krw"].max()) if len(candidate) else None,
        },
    }


def main() -> None:
    df = pd.read_csv(RAW_PATH, low_memory=False)
    df = validate_gallery(df)
    df = add_exclusion(df)
    df = add_dedupe_flags(df)
    summary = build_summary(df)

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Track 4 primary-market cleaned v1")
    print(f"input: {RAW_PATH.relative_to(REPO)}")
    print(f"output: {OUT_CSV.relative_to(REPO)}")
    print(f"rows: {summary['n_rows']:,}")
    print(f"training candidates: {summary['n_training_candidates']:,}")
    print(f"excluded: {summary['n_excluded']:,}")
    print(f"exclude reasons: {summary['exclude_reason_counts']}")
    print(f"gallery match: {summary['gallery_validation']['gallery_tier_match_source_counts']}")


if __name__ == "__main__":
    main()
