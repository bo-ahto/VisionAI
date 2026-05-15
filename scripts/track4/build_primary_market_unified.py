"""Build Track 4 primary-market raw unified dataset.

This script intentionally starts before Track 4 splitting.
It collects fragmented primary-market source files into one common schema.
Prediction-only files are excluded because they do not provide ground-truth prices.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
OUT_CSV = DATA / "track4_primary_market_raw_unified.csv"
OUT_SUMMARY = DATA / "track4_primary_market_raw_unified_summary.json"


def clean_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return re.sub(r"\s+", " ", text)


def to_number(value: object) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        if np.isfinite(value):
            return float(value)
        return None
    text = str(value)
    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_price_krw(value: object) -> float | None:
    number = to_number(value)
    if number is None or number <= 0:
        return None
    return float(number)


def parse_dimensions(value: object) -> tuple[float | None, float | None, float | None]:
    text = clean_text(value)
    if not text:
        return None, None, None
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if len(nums) >= 3:
        return nums[0], nums[1], nums[2]
    if len(nums) >= 2:
        return nums[0], nums[1], None
    return None, None, None


def infer_medium_category(text: object, fallback: object = None) -> str:
    fallback_text = clean_text(fallback)
    if fallback_text:
        return fallback_text.lower()
    raw = (clean_text(text) or "").lower()
    if any(k in raw for k in ["oil", "유화"]):
        return "oil"
    if any(k in raw for k in ["acrylic", "아크릴"]):
        return "acrylic"
    if any(k in raw for k in ["watercolor", "수채"]):
        return "watercolor"
    if any(k in raw for k in ["pigment", "안료"]):
        return "pigment"
    if any(k in raw for k in ["print", "lithograph", "edition", "프린트", "판화"]):
        return "print"
    if any(k in raw for k in ["photo", "photograph", "사진"]):
        return "photo"
    if any(k in raw for k in ["bronze", "steel", "ceramic", "glass", "sculpture", "조각"]):
        return "sculpture"
    if any(k in raw for k in ["mixed", "혼합"]):
        return "mixed"
    return "other"


def infer_support_category(text: object, fallback: object = None) -> str:
    fallback_text = clean_text(fallback)
    if fallback_text:
        return fallback_text.lower()
    raw = (clean_text(text) or "").lower()
    if "canvas" in raw or "캔버스" in raw:
        return "canvas"
    if "paper" in raw or "종이" in raw:
        return "paper"
    if "linen" in raw:
        return "linen"
    if "panel" in raw or "패널" in raw:
        return "panel"
    if "wood" in raw or "나무" in raw:
        return "wood"
    if "metal" in raw or "steel" in raw or "aluminum" in raw:
        return "metal"
    return "unknown"


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["width_cm", "height_cm", "depth_cm", "price_krw", "estimated_ho"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["has_depth"] = (df["depth_cm"].fillna(0) > 0).astype(int)
    df["area_cm2"] = df["width_cm"] * df["height_cm"]
    df.loc[df["area_cm2"] <= 0, "area_cm2"] = np.nan
    df["log_area"] = np.log1p(df["area_cm2"])
    df["aspect_ratio"] = df["width_cm"] / df["height_cm"]
    df.loc[~np.isfinite(df["aspect_ratio"]), "aspect_ratio"] = np.nan
    df["ln_price"] = np.log(df["price_krw"])
    return df


def standard_columns(rows: list[dict]) -> pd.DataFrame:
    columns = [
        "source",
        "source_file",
        "source_artwork_id",
        "artist_name_raw",
        "artist_slug",
        "title",
        "year_made",
        "medium_raw",
        "medium_category",
        "support_category",
        "width_cm",
        "height_cm",
        "depth_cm",
        "has_depth",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "estimated_ho",
        "price_krw",
        "ln_price",
        "price_raw",
        "price_currency",
        "artwork_url",
        "image_url",
        "gallery_name",
        "gallery_tier",
        "is_excluded_for_training",
        "exclude_reason",
    ]
    df = pd.DataFrame(rows)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


def load_saatchi() -> pd.DataFrame:
    path = DATA / "saatchi_cleaned.csv"
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        width, height, depth = parse_dimensions(r.get("dimensions_cm"))
        rows.append(
            {
                "source": "saatchi",
                "source_file": str(path.relative_to(REPO)),
                "source_artwork_id": clean_text(r.get("artwork_id")),
                "artist_name_raw": clean_text(r.get("artist_name")),
                "artist_slug": clean_text(r.get("artist_slug")),
                "title": clean_text(r.get("title")),
                "year_made": to_number(r.get("year_made")),
                "medium_raw": clean_text(r.get("medium")),
                "medium_category": infer_medium_category(r.get("medium"), r.get("medium_category")),
                "support_category": infer_support_category(r.get("medium"), r.get("support_type")),
                "width_cm": width,
                "height_cm": height,
                "depth_cm": depth,
                "estimated_ho": to_number(r.get("ho")),
                "price_krw": parse_price_krw(r.get("price_krw")),
                "price_raw": clean_text(r.get("price_raw")),
                "price_currency": clean_text(r.get("price_currency")) or "USD",
                "artwork_url": clean_text(r.get("artwork_url")),
                "image_url": clean_text(r.get("image_url")),
                "gallery_name": clean_text(r.get("gallery_name")),
                "gallery_tier": clean_text(r.get("gallery_tier")),
                "is_excluded_for_training": int(to_number(r.get("is_excluded_for_training")) or 0),
                "exclude_reason": clean_text(r.get("exclude_reason")),
            }
        )
    return add_derived(standard_columns(rows))


def load_artsy() -> pd.DataFrame:
    path = DATA / "artsy_kr_artworks.csv"
    df = pd.read_csv(path)
    if "is_auction" in df.columns:
        df = df[df["is_auction"].astype(str).str.lower() != "true"].copy()
    rows = []
    for _, r in df.iterrows():
        width = to_number(r.get("width_cm"))
        height = to_number(r.get("height_cm"))
        depth = to_number(r.get("depth_cm"))
        if width is None or height is None:
            width, height, parsed_depth = parse_dimensions(r.get("dimensions_cm"))
            depth = depth if depth is not None else parsed_depth
        rows.append(
            {
                "source": "artsy",
                "source_file": str(path.relative_to(REPO)),
                "source_artwork_id": clean_text(r.get("artwork_id")),
                "artist_name_raw": clean_text(r.get("artist_name")),
                "artist_slug": clean_text(r.get("artist_slug")),
                "title": clean_text(r.get("title")),
                "year_made": to_number(r.get("date")),
                "medium_raw": clean_text(r.get("medium")),
                "medium_category": infer_medium_category(r.get("medium"), r.get("medium_type")),
                "support_category": infer_support_category(r.get("medium")),
                "width_cm": width,
                "height_cm": height,
                "depth_cm": depth,
                "estimated_ho": None,
                "price_krw": parse_price_krw(r.get("price_krw")),
                "price_raw": clean_text(r.get("price_raw")),
                "price_currency": clean_text(r.get("price_currency")),
                "artwork_url": clean_text(r.get("artwork_url")),
                "image_url": clean_text(r.get("image_url")),
                "gallery_name": clean_text(r.get("gallery_name")),
                "gallery_tier": clean_text(r.get("gallery_type")),
                "is_excluded_for_training": 0,
                "exclude_reason": None,
            }
        )
    return add_derived(standard_columns(rows))


def load_artue() -> pd.DataFrame:
    path = DATA / "artue_테스트_가격포함.csv"
    df = pd.read_csv(path)
    rows = []
    for idx, r in df.iterrows():
        medium = clean_text(r.get("Medium (EN)")) or clean_text(r.get("Medium (KO)"))
        rows.append(
            {
                "source": "artue",
                "source_file": str(path.relative_to(REPO)),
                "source_artwork_id": clean_text(r.get("Handle")) or f"artue_{idx}",
                "artist_name_raw": clean_text(r.get("Artist")),
                "artist_slug": clean_text(r.get("Handle")),
                "title": clean_text(r.get("Title")),
                "year_made": to_number(r.get("Year")),
                "medium_raw": medium,
                "medium_category": infer_medium_category(medium),
                "support_category": infer_support_category(medium),
                "width_cm": to_number(r.get("Width (cm)")),
                "height_cm": to_number(r.get("Height (cm)")),
                "depth_cm": to_number(r.get("Depth (cm)")),
                "estimated_ho": None,
                "price_krw": parse_price_krw(r.get("Price (KRW)")),
                "price_raw": clean_text(r.get("Price (KRW)")),
                "price_currency": "KRW",
                "artwork_url": clean_text(r.get("URL")),
                "image_url": None,
                "gallery_name": None,
                "gallery_tier": None,
                "is_excluded_for_training": 0,
                "exclude_reason": None,
            }
        )
    return add_derived(standard_columns(rows))


def load_gallery_primary() -> pd.DataFrame:
    path = DATA / "1차 시장 데이터 - 전달본_260504.csv"
    df = pd.read_csv(path)
    rows = []
    for idx, r in df.iterrows():
        rows.append(
            {
                "source": "gallery_primary",
                "source_file": str(path.relative_to(REPO)),
                "source_artwork_id": clean_text(r.get("idx")) or f"gallery_primary_{idx}",
                "artist_name_raw": clean_text(r.get("name_kor")) or clean_text(r.get("name_eng")),
                "artist_slug": clean_text(r.get("name_eng")),
                "title": clean_text(r.get("title")),
                "year_made": to_number(r.get("연도")),
                "medium_raw": clean_text(r.get("materials")),
                "medium_category": infer_medium_category(r.get("materials")),
                "support_category": infer_support_category(r.get("materials")),
                "width_cm": to_number(r.get("width")),
                "height_cm": to_number(r.get("height")),
                "depth_cm": None,
                "estimated_ho": None,
                "price_krw": parse_price_krw(r.get("price")),
                "price_raw": clean_text(r.get("price")),
                "price_currency": "KRW",
                "artwork_url": None,
                "image_url": clean_text(r.get("img_src")),
                "gallery_name": clean_text(r.get("gallery_name(KR)")) or clean_text(r.get("gallery_name(EN)")),
                "gallery_tier": clean_text(r.get("gallery_tier")),
                "is_excluded_for_training": 0,
                "exclude_reason": None,
            }
        )
    return add_derived(standard_columns(rows))


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["artist_name_raw", "title", "medium_raw"]:
        df[f"_{col}_key"] = df[col].fillna("").astype(str).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    df["_price_key"] = df["price_krw"].round(0)
    df["_size_key"] = (
        df["width_cm"].round(1).astype(str)
        + "x"
        + df["height_cm"].round(1).astype(str)
        + "x"
        + df["depth_cm"].fillna(0).round(1).astype(str)
    )
    before = len(df)
    df = df.drop_duplicates(
        subset=["source", "source_artwork_id"],
        keep="first",
    )
    df = df.drop_duplicates(
        subset=["source", "_artist_name_raw_key", "_title_key", "_price_key", "_size_key"],
        keep="first",
    )
    removed = before - len(df)
    df = df.drop(columns=[c for c in df.columns if c.startswith("_")])
    df.attrs["dedupe_removed"] = removed
    return df


def build_summary(df: pd.DataFrame, source_counts_raw: dict[str, int], dedupe_removed: int) -> dict:
    usable = df[
        df["price_krw"].notna()
        & (df["price_krw"] > 0)
        & df["artist_name_raw"].notna()
        & df["title"].notna()
        & df["width_cm"].notna()
        & df["height_cm"].notna()
    ]
    return {
        "created_at": "2026-05-15",
        "output": str(OUT_CSV.relative_to(REPO)),
        "raw_source_rows": source_counts_raw,
        "dedupe_removed_rows": int(dedupe_removed),
        "n_rows": int(len(df)),
        "n_usable_basic_rows": int(len(usable)),
        "n_sources": int(df["source"].nunique()),
        "n_artists_raw": int(df["artist_name_raw"].nunique()),
        "source_counts": {str(k): int(v) for k, v in df["source"].value_counts().items()},
        "usable_source_counts": {str(k): int(v) for k, v in usable["source"].value_counts().items()},
        "missing_rate": {
            col: float(df[col].isna().mean())
            for col in [
                "artist_name_raw",
                "title",
                "price_krw",
                "width_cm",
                "height_cm",
                "medium_category",
                "support_category",
                "artwork_url",
            ]
        },
        "price_summary": {
            "median": float(usable["price_krw"].median()) if len(usable) else None,
            "q25": float(usable["price_krw"].quantile(0.25)) if len(usable) else None,
            "q75": float(usable["price_krw"].quantile(0.75)) if len(usable) else None,
            "max": float(usable["price_krw"].max()) if len(usable) else None,
        },
        "notes": [
            "Prediction-only files were excluded from the training-target union.",
            "This is a raw unified dataset; artist normalization and final training exclusions are next steps.",
            "source is kept for audit and bias analysis, not as a production input feature.",
        ],
    }


def main() -> None:
    loaders = [load_saatchi, load_artsy, load_artue, load_gallery_primary]
    frames = []
    raw_counts = {}
    for loader in loaders:
        frame = loader()
        source = str(frame["source"].iloc[0]) if len(frame) else loader.__name__
        raw_counts[source] = int(len(frame))
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["price_krw"].notna() & (combined["price_krw"] > 0)].copy()
    combined = dedupe(combined)
    dedupe_removed = combined.attrs.get("dedupe_removed", 0)

    combined.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    summary = build_summary(combined, raw_counts, dedupe_removed)
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Track 4 primary-market unified dataset")
    print(f"saved: {OUT_CSV.relative_to(REPO)}")
    print(f"rows: {summary['n_rows']:,}")
    print(f"usable basic rows: {summary['n_usable_basic_rows']:,}")
    print(f"sources: {summary['source_counts']}")
    print(f"usable sources: {summary['usable_source_counts']}")
    print(f"price median: {summary['price_summary']['median']:,.0f}")


if __name__ == "__main__":
    main()

