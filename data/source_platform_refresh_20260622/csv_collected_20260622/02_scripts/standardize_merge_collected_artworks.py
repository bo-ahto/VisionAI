#!/usr/bin/env python3
"""
1차 정리용 수집 CSV 표준화 및 작품 단위 통합 스크립트.

1차 정리의 범위:
- 기존 실험 원본 데이터와 추가 수집 데이터를 한 데이터셋으로 합친다.
- 플랫폼별 컬럼명을 공통 컬럼명으로 맞춘다.
- 같은 작품으로 판단되는 중복 행을 제거한다.
- 가격 숫자가 전혀 없는 작품을 제거한다.
- `1원`, `999,999,999원`처럼 placeholder 가능성이 높은 가격을 제거한다.
- 입체 작품과 명백한 크기 오류 후보를 제거한다.
- 외화 가격은 원천에 있는 값을 보존한다. 이 단계에서 환율 변환은 하지 않는다.

필요한 입력 파일:
- 패키지 루트의 01_source_raw 아래에 있는 CSV 파일들
- 작품 CSV:
  - 01_source_raw/ahto_viewer_exports/ahto_export_artsy_artworks.csv
  - 01_source_raw/ahto_viewer_exports/ahto_export_saatchi_artworks.csv
  - 01_source_raw/source_platform_latest/source_platform_artsy_kr_artworks.csv
  - 01_source_raw/source_platform_latest/source_platform_saatchi_kr_artworks_split_13102.csv
  - 01_source_raw/artue_exports/artue_artworks.csv
  - 01_source_raw/legacy_experiment_sources/legacy_artsy_kr_artworks.csv
  - 01_source_raw/legacy_experiment_sources/legacy_saatchi_cleaned.csv
  - 01_source_raw/legacy_experiment_sources/legacy_artue_price_included.csv
  - 01_source_raw/legacy_experiment_sources/legacy_gallery_primary_260504.csv
- 작가 CSV는 있으면 보강용으로 사용하고, 없어도 작품 통합은 실행된다.
  - 01_source_raw/ahto_viewer_exports/ahto_export_saatchi_artists.csv
  - 01_source_raw/source_platform_latest/source_platform_artsy_kr_artists_full.csv
  - 01_source_raw/artue_exports/artue_artists.csv

실행 방법:
- 패키지 루트에서 실행:
  python3 02_scripts/standardize_merge_collected_artworks.py
- 다른 폴더에서 실행:
  python3 /path/to/02_scripts/standardize_merge_collected_artworks.py

출력 파일:
- 03_outputs/standardized_artworks_merged_deduped.csv
- 03_outputs/standardization_merge_summary.json
- 03_outputs/standardized_artworks_outlier_audit.csv
- 03_outputs/standardized_artworks_outlier_audit_summary.json
- 03_outputs/standardized_artworks_removed_by_filter.csv

처리 원칙:
- 작품 1건을 최종 CSV 1행으로 만든다.
- 플랫폼별 컬럼명을 공통 컬럼명으로 맞춘다.
- 가격, 크기, 작가 메타 등은 가능한 범위에서 표준 컬럼에 매핑한다.
- 작가 CSV는 작품 행에 부족한 작가 메타를 채우는 용도로만 사용한다.
- 중복 제거는 source_family + source_artwork_id를 1순위로 사용한다.
- 같은 작품이 여러 수집본에 있으면 최신/상세 수집본을 우선 남긴다.
- 가격 정보가 전혀 없는 작품은 최종 CSV에서 제외한다.
- `1원`, `999,999,999원`처럼 placeholder 가능성이 높은 가격은 최종 CSV에서 제외한다.
- 입체 작품은 최종 CSV에서 제외한다.
- 명백한 크기 오류 후보는 최종 CSV에서 제외한다.
- 이상치 후보는 자동 삭제하지 않고 별도 감사 파일로 남긴다.
- 가격을 새로 계산하거나 모델 피처를 새로 만들지는 않는다.
- 외화 가격을 원화로 환산하지 않는다.
- `price_amount`는 `price_currency`에 적힌 통화 기준의 원 가격 금액이다.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent
DEFAULT_SOURCE_DIR = PACKAGE_DIR / "01_source_raw"
DEFAULT_OUTPUT_DIR = PACKAGE_DIR / "03_outputs"


STANDARD_COLUMNS = [
    "source_family",
    "source_file",
    "source_variant",
    "source_row_index",
    "source_artwork_id",
    "artwork_title",
    "artwork_year",
    "artwork_url",
    "image_url",
    "price_krw",
    "price_usd",
    "price_eur",
    "price_raw",
    "price_currency",
    "price_amount",
    "width_cm",
    "height_cm",
    "depth_cm",
    "dimensions_raw",
    "medium_raw",
    "medium_ko",
    "medium_category_raw",
    "medium_type_raw",
    "materials_raw",
    "subject_raw",
    "style_raw",
    "orientation_raw",
    "size_bin_raw",
    "attribution_class",
    "availability",
    "status",
    "is_auction",
    "is_framed",
    "color",
    "artist_id_or_slug",
    "artist_name",
    "artist_first_name",
    "artist_last_name",
    "artist_nationality",
    "artist_nationality_ko",
    "artist_birth_year",
    "artist_gender",
    "artist_location_city",
    "artist_location_country",
    "artist_hometown",
    "artist_total_works",
    "artist_for_sale",
    "artist_followers",
    "artist_is_p1",
    "artist_solo_count",
    "artist_group_count",
    "artist_fair_count",
    "artist_total_shows",
    "artist_bio",
    "artist_education",
    "artist_exhibitions",
    "artist_instagram_url",
    "artist_website_url",
    "gallery_name",
    "gallery_type",
    "gallery_cities",
    "dedupe_key",
    "dedupe_rank",
]

INTERNAL_COLUMNS = ["dedupe_key", "dedupe_rank"]
STAGE1_OUTPUT_EXCLUDED_COLUMNS = INTERNAL_COLUMNS

NUMERIC_COLUMNS = [
    "source_row_index",
    "artwork_year",
    "price_krw",
    "price_usd",
    "price_eur",
    "price_amount",
    "width_cm",
    "height_cm",
    "depth_cm",
    "artist_birth_year",
    "artist_total_works",
    "artist_for_sale",
    "artist_followers",
    "artist_solo_count",
    "artist_group_count",
    "artist_fair_count",
    "artist_total_shows",
    "dedupe_rank",
]

# 같은 작품이 여러 CSV에 들어있을 때 어떤 행을 남길지 정하는 우선순위다.
# 숫자가 낮을수록 먼저 남는다.
SOURCE_PRIORITY = {
    "source_platform_saatchi_split": 10,
    "ahto_saatchi": 30,
    "source_platform_artsy": 10,
    "ahto_artsy": 20,
    "artue": 10,
    "legacy_artsy": 50,
    "legacy_saatchi": 50,
    "legacy_artue": 50,
    "legacy_gallery_primary": 60,
}


def clean_text(value: Any) -> str:
    """빈 값과 공백을 정리해서 안정적인 문자열로 만든다."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return re.sub(r"\s+", " ", text)


def clean_number(value: Any) -> float | pd.NA:
    """통화 기호, 콤마, 문자열이 섞인 숫자 값을 float로 바꾼다."""
    if pd.isna(value):
        return pd.NA
    text = clean_text(value)
    if not text:
        return pd.NA
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-", "-."}:
        return pd.NA
    try:
        return float(text)
    except ValueError:
        return pd.NA


def extract_year(value: Any) -> float | pd.NA:
    """연도 문자열에서 4자리 연도만 추출한다."""
    text = clean_text(value)
    match = re.search(r"(18|19|20)\d{2}", text)
    if not match:
        return pd.NA
    return float(match.group(0))


def parse_dimensions_cm(value: Any) -> tuple[float | pd.NA, float | pd.NA, float | pd.NA]:
    """`15 × 20 × 1.7 cm` 같은 문자열에서 width/height/depth를 추출한다."""
    text = clean_text(value).lower()
    if not text:
        return (pd.NA, pd.NA, pd.NA)
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    values: list[float | pd.NA] = []
    for number in numbers[:3]:
        try:
            values.append(float(number))
        except ValueError:
            values.append(pd.NA)
    while len(values) < 3:
        values.append(pd.NA)
    return (values[0], values[1], values[2])


def pick_series(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    """컬럼이 있으면 해당 Series를, 없으면 빈 Series를 반환한다."""
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def first_non_empty(*values: Any) -> str:
    """여러 값 중 첫 번째 비어 있지 않은 값을 반환한다."""
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def combine_name(first_name: Any, last_name: Any) -> str:
    """first/last로 나뉜 작가명을 표시용 이름으로 합친다."""
    return " ".join(part for part in [clean_text(first_name), clean_text(last_name)] if part)


def new_standard_frame(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """표준 컬럼을 가진 빈 DataFrame을 만든다."""
    out = pd.DataFrame(index=raw.index, columns=STANDARD_COLUMNS)
    out["source_file"] = source_file
    out["source_variant"] = source_variant
    out["source_row_index"] = raw.index
    out["dedupe_rank"] = SOURCE_PRIORITY.get(source_variant, 999)
    return out


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼 순서와 타입을 마지막으로 정리한다."""
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    out = df[STANDARD_COLUMNS].copy()
    for col in NUMERIC_COLUMNS:
        out[col] = out[col].map(clean_number)

    for col in out.columns:
        if col not in NUMERIC_COLUMNS:
            out[col] = out[col].map(clean_text)

    return out


def drop_stage1_output_excluded_columns(df: pd.DataFrame) -> pd.DataFrame:
    """최종 공유/학습용 1차 정리 출력에서 제외할 컬럼을 제거한다."""
    return df.drop(columns=STAGE1_OUTPUT_EXCLUDED_COLUMNS, errors="ignore")


def build_dedupe_key(row: pd.Series) -> str:
    """중복 제거용 키를 만든다."""
    source_family = clean_text(row.get("source_family"))
    artwork_id = clean_text(row.get("source_artwork_id"))
    artwork_url = clean_text(row.get("artwork_url")).lower()

    # Artue는 현재 수집본과 과거 원본의 작품 ID 체계가 다를 수 있어 URL을 우선한다.
    if source_family == "artue" and artwork_url:
        return f"url::{source_family}::{artwork_url}"
    if source_family and artwork_id:
        return f"id::{source_family}::{artwork_id}"
    if source_family and artwork_url:
        return f"url::{source_family}::{artwork_url}"

    title = clean_text(row.get("artwork_title")).lower()
    artist = clean_text(row.get("artist_name")).lower()
    width = clean_text(row.get("width_cm"))
    height = clean_text(row.get("height_cm"))
    price = first_non_empty(row.get("price_krw"), row.get("price_usd"), row.get("price_raw"))
    return f"fallback::{source_family}::{artist}::{title}::{width}x{height}::{price}"


def has_any_price(df: pd.DataFrame) -> pd.Series:
    """양수 가격 숫자가 최소 하나 이상 있는지 판단한다."""
    numeric_price_cols = ["price_krw", "price_usd", "price_eur", "price_amount"]
    has_price = pd.Series(False, index=df.index)
    for col in numeric_price_cols:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        has = values.notna() & values.gt(0)
        has_price |= has

    if "price_raw" in df.columns:
        # `Sold`, `On hold`, `Price on request`, `0.0` 같은 문자열은 가격 숫자로 보지 않는다.
        cleaned = df["price_raw"].astype(str).str.strip().str.lower()
        raw_has_positive_digit = (
            df["price_raw"].notna()
            & cleaned.ne("")
            & ~cleaned.isin(["nan", "none", "null", "<na>"])
            & cleaned.str.contains(r"[1-9]", regex=True)
        )
        has_price |= raw_has_positive_digit
    return has_price


def is_placeholder_price(df: pd.DataFrame) -> pd.Series:
    """운영/학습에 쓰기 어려운 명백한 placeholder 가격을 찾는다."""
    price_krw = pd.to_numeric(df["price_krw"], errors="coerce")
    price_amount = pd.to_numeric(df["price_amount"], errors="coerce")
    currency = df["price_currency"].map(clean_text).str.upper()
    return price_krw.isin([1, 999_999_999]) | (
        currency.eq("KRW") & price_amount.isin([1, 999_999_999])
    )


def is_3d_artwork(df: pd.DataFrame) -> pd.Series:
    """입체/설치/공예 성격이 강한 작품을 찾는다."""
    category = df["medium_category_raw"].astype(str).str.strip().str.lower()
    medium_type = df["medium_type_raw"].astype(str).str.strip().str.lower()
    medium = df["medium_raw"].astype(str).str.strip().str.lower()
    text = category + " " + medium_type + " " + medium
    patterns = [
        "sculpture",
        "installation",
        "ceramic",
        "ceramics",
        "glass",
        "architecture",
        "video/film/animation",
        "video / installation",
        "design/decorative art",
        "furniture",
    ]
    mask = pd.Series(False, index=df.index)
    for pattern in patterns:
        mask |= text.str.contains(pattern, regex=False, na=False)
    return mask


def is_obvious_size_error(df: pd.DataFrame) -> pd.Series:
    """평면 작품 기준으로 명백히 비정상적인 cm 크기를 찾는다."""
    width = pd.to_numeric(df["width_cm"], errors="coerce")
    height = pd.to_numeric(df["height_cm"], errors="coerce")
    depth = pd.to_numeric(df["depth_cm"], errors="coerce")
    flat_width_height_error = width.gt(1000) | height.gt(1000)
    depth_error = depth.gt(500)
    return flat_width_height_error | depth_error


def build_outlier_audit(df: pd.DataFrame, output_dir: Path) -> dict[str, Any]:
    """가격/크기 이상치 후보를 플래그로 남긴다. 이 함수는 행을 삭제하지 않는다."""
    audit = df.copy()
    price_krw = pd.to_numeric(audit["price_krw"], errors="coerce")
    price_usd = pd.to_numeric(audit["price_usd"], errors="coerce")
    width = pd.to_numeric(audit["width_cm"], errors="coerce")
    height = pd.to_numeric(audit["height_cm"], errors="coerce")
    depth = pd.to_numeric(audit["depth_cm"], errors="coerce")
    area = width * height

    valid_price = price_krw[price_krw.gt(0)]
    valid_area = area[area.gt(0)]
    unit_price = price_krw / area
    valid_unit_price = unit_price[unit_price.gt(0) & unit_price.notna()]

    price_high_threshold = float(valid_price.quantile(0.999)) if not valid_price.empty else None
    price_low_threshold = float(valid_price.quantile(0.001)) if not valid_price.empty else None
    area_high_threshold = float(valid_area.quantile(0.999)) if not valid_area.empty else None
    unit_high_threshold = float(valid_unit_price.quantile(0.999)) if not valid_unit_price.empty else None
    unit_low_threshold = float(valid_unit_price.quantile(0.001)) if not valid_unit_price.empty else None

    flags = pd.DataFrame(index=audit.index)
    flags["flag_price_non_positive"] = (
        price_krw.notna() & price_krw.le(0)
    ) | (price_usd.notna() & price_usd.le(0))
    flags["flag_price_krw_extreme_high"] = (
        price_high_threshold is not None
    ) & price_krw.gt(price_high_threshold)
    flags["flag_price_krw_extreme_low"] = (
        price_low_threshold is not None
    ) & price_krw.gt(0) & price_krw.lt(price_low_threshold)
    flags["flag_price_placeholder_repeating_9"] = price_krw.isin(
        [999_999, 9_999_999, 99_999_999, 999_999_999]
    )
    flags["flag_size_non_positive"] = (
        width.notna() & width.le(0)
    ) | (height.notna() & height.le(0)) | (depth.notna() & depth.lt(0))
    flags["flag_size_cm_extreme"] = width.gt(1000) | height.gt(1000) | depth.gt(500)
    flags["flag_area_extreme_high"] = (
        area_high_threshold is not None
    ) & area.gt(area_high_threshold)
    flags["flag_unit_price_extreme_high"] = (
        unit_high_threshold is not None
    ) & unit_price.gt(unit_high_threshold)
    flags["flag_unit_price_extreme_low"] = (
        unit_low_threshold is not None
    ) & unit_price.gt(0) & unit_price.lt(unit_low_threshold)

    audit["area_cm2_calc"] = area
    audit["unit_price_krw_per_cm2_calc"] = unit_price
    audit["outlier_flag_count"] = flags.sum(axis=1)
    audit["outlier_flags"] = flags.apply(
        lambda row: ",".join(col for col, value in row.items() if bool(value)),
        axis=1,
    )

    flagged = drop_stage1_output_excluded_columns(audit[audit["outlier_flag_count"].gt(0)].copy())
    outlier_csv = output_dir / "standardized_artworks_outlier_audit.csv"
    outlier_summary_json = output_dir / "standardized_artworks_outlier_audit_summary.json"
    flagged.to_csv(outlier_csv, index=False, encoding="utf-8-sig")

    summary = {
        "output_csv": str(outlier_csv),
        "total_rows_checked": len(df),
        "flagged_rows": len(flagged),
        "flagged_ratio": len(flagged) / len(df) if len(df) else 0,
        "thresholds": {
            "price_krw_q001": price_low_threshold,
            "price_krw_q999": price_high_threshold,
            "area_cm2_q999": area_high_threshold,
            "unit_price_krw_per_cm2_q001": unit_low_threshold,
            "unit_price_krw_per_cm2_q999": unit_high_threshold,
            "size_cm_manual_extreme": {
                "width_cm_gt": 1000,
                "height_cm_gt": 1000,
                "depth_cm_gt": 500,
            },
        },
        "flag_counts": {col: int(flags[col].sum()) for col in flags.columns},
        "by_source_family": flagged["source_family"].value_counts().to_dict(),
        "by_source_variant": flagged["source_variant"].value_counts().to_dict(),
        "note": "이상치 후보만 표시한다. 최종 CSV에서 자동 삭제하지 않는다.",
    }
    outlier_summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def standardize_artsy(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """Artsy 작품 CSV를 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "artsy"
    out["source_artwork_id"] = pick_series(raw, "artwork_id")
    out["artwork_title"] = pick_series(raw, "title")
    out["artwork_year"] = pick_series(raw, "date").map(extract_year)
    out["artwork_url"] = pick_series(raw, "artwork_url")
    out["image_url"] = pick_series(raw, "image_url")
    # Artsy 수집본의 price_krw는 크롤러가 고정 환율로 만든 값일 수 있어
    # 1차 정리본에서는 비워둔다. 원 가격은 price_raw/currency/amount로 보존한다.
    out["price_krw"] = ""
    out["price_raw"] = pick_series(raw, "price_raw")
    out["price_currency"] = pick_series(raw, "price_currency")
    out["price_amount"] = pick_series(raw, "price_amount")
    out["width_cm"] = pick_series(raw, "width_cm")
    out["height_cm"] = pick_series(raw, "height_cm")
    out["depth_cm"] = pick_series(raw, "depth_cm")
    out["dimensions_raw"] = pick_series(raw, "dimensions_cm")
    out["medium_raw"] = pick_series(raw, "medium")
    out["medium_category_raw"] = pick_series(raw, "category")
    out["medium_type_raw"] = pick_series(raw, "medium_type")
    out["attribution_class"] = pick_series(raw, "attribution_class")
    out["availability"] = pick_series(raw, "availability")
    out["is_auction"] = pick_series(raw, "is_auction")
    out["artist_id_or_slug"] = pick_series(raw, "artist_slug")
    out["artist_name"] = pick_series(raw, "artist_name")
    out["artist_nationality"] = pick_series(raw, "artist_nationality")
    out["artist_birth_year"] = pick_series(raw, "artist_birth_year")
    out["artist_total_works"] = pick_series(raw, "artist_total_works")
    out["artist_for_sale"] = pick_series(raw, "artist_for_sale")
    out["artist_followers"] = pick_series(raw, "artist_followers")
    out["artist_is_p1"] = pick_series(raw, "artist_is_p1")
    out["gallery_name"] = pick_series(raw, "gallery_name")
    out["gallery_type"] = pick_series(raw, "gallery_type")
    out["gallery_cities"] = pick_series(raw, "gallery_cities")
    return finalize(out)


def standardize_saatchi(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """Saatchi 작품 CSV를 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "saatchi"
    out["source_artwork_id"] = pick_series(raw, "artwork_id")
    out["artwork_title"] = pick_series(raw, "title")
    out["artwork_url"] = pick_series(raw, "artwork_url")
    out["image_url"] = pick_series(raw, "image_url")
    # Saatchi 수집본의 price_krw는 price_usd에 고정 환율을 곱해 만든 값이므로
    # 1차 정리본에서는 비워둔다. 원 가격은 USD로 보존한다.
    out["price_krw"] = ""
    out["price_usd"] = pick_series(raw, "price_usd")
    out["price_raw"] = pick_series(raw, "price_usd")
    out["price_currency"] = pick_series(raw, "price_usd").map(lambda v: "USD" if clean_text(v) else "")
    out["price_amount"] = pick_series(raw, "price_usd")
    out["width_cm"] = pick_series(raw, "width_cm")
    out["height_cm"] = pick_series(raw, "height_cm")
    out["depth_cm"] = pick_series(raw, "depth_cm")
    out["medium_raw"] = pick_series(raw, "mediums")
    out["medium_category_raw"] = pick_series(raw, "category")
    out["materials_raw"] = pick_series(raw, "materials")
    out["subject_raw"] = pick_series(raw, "subject")
    out["style_raw"] = pick_series(raw, "styles")
    out["orientation_raw"] = pick_series(raw, "orientation")
    out["size_bin_raw"] = pick_series(raw, "size_bin")
    out["is_framed"] = pick_series(raw, "is_framed")
    out["color"] = pick_series(raw, "color")
    out["artist_id_or_slug"] = pick_series(raw, "artist_id")
    out["artist_first_name"] = pick_series(raw, "artist_first_name")
    out["artist_last_name"] = pick_series(raw, "artist_last_name")
    out["artist_name"] = [
        combine_name(first, last)
        for first, last in zip(out["artist_first_name"], out["artist_last_name"])
    ]
    out["artist_gender"] = pick_series(raw, "artist_gender")
    out["artist_location_city"] = pick_series(raw, "artist_city")
    out["artist_location_country"] = pick_series(raw, "country")
    return finalize(out)


def standardize_artue(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """Artue 작품 CSV를 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "artue"
    out["source_artwork_id"] = pick_series(raw, "id")
    out["artwork_title"] = pick_series(raw, "title")
    out["artwork_year"] = pick_series(raw, "year").combine_first(pick_series(raw, "create_date").map(extract_year))
    out["artwork_url"] = pick_series(raw, "url")
    out["image_url"] = pick_series(raw, "image_1")
    out["price_krw"] = pick_series(raw, "price_krw")
    out["price_usd"] = pick_series(raw, "price_usd")
    out["price_eur"] = pick_series(raw, "price_eur")
    out["price_currency"] = pick_series(raw, "default_currency")
    currency = out["price_currency"].map(clean_text).str.lower()
    price_amount = pd.Series([pd.NA] * len(raw), index=raw.index)
    price_amount[currency.eq("krw")] = pick_series(raw, "price_krw")[currency.eq("krw")]
    price_amount[currency.eq("usd")] = pick_series(raw, "price_usd")[currency.eq("usd")]
    price_amount[currency.eq("eur")] = pick_series(raw, "price_eur")[currency.eq("eur")]
    out["price_amount"] = price_amount
    out["price_raw"] = out["price_currency"].map(clean_text) + " " + out["price_amount"].map(clean_text)
    out["width_cm"] = pick_series(raw, "width_cm")
    out["height_cm"] = pick_series(raw, "height_cm")
    out["depth_cm"] = pick_series(raw, "depth_cm")
    out["dimensions_raw"] = pick_series(raw, "dimensions_all")
    out["medium_raw"] = pick_series(raw, "medium")
    out["medium_ko"] = pick_series(raw, "medium_ko")
    out["medium_category_raw"] = pick_series(raw, "medium_category")
    out["size_bin_raw"] = pick_series(raw, "size_label")
    out["attribution_class"] = pick_series(raw, "edition_type")
    out["availability"] = pick_series(raw, "view_status")
    out["status"] = pick_series(raw, "status")
    out["artist_id_or_slug"] = pick_series(raw, "artist_handle")
    out["artist_name"] = pick_series(raw, "artist_name")
    return finalize(out)


def standardize_legacy_saatchi(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """기존 실험 source_files의 saatchi_cleaned.csv를 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "saatchi"
    out["source_artwork_id"] = pick_series(raw, "artwork_id")
    out["artwork_title"] = pick_series(raw, "title")
    out["artwork_url"] = pick_series(raw, "artwork_url")
    out["image_url"] = pick_series(raw, "image_url")
    out["price_krw"] = ""
    out["price_raw"] = pick_series(raw, "price_raw")
    out["price_currency"] = pick_series(raw, "price_currency")
    out["price_amount"] = pick_series(raw, "price_raw")
    out["dimensions_raw"] = pick_series(raw, "dimensions_cm")
    parsed_dims = out["dimensions_raw"].map(parse_dimensions_cm)
    out["width_cm"] = [dims[0] for dims in parsed_dims]
    out["height_cm"] = [dims[1] for dims in parsed_dims]
    out["depth_cm"] = [dims[2] for dims in parsed_dims]
    out["medium_raw"] = pick_series(raw, "medium")
    out["medium_category_raw"] = pick_series(raw, "medium_category")
    out["materials_raw"] = pick_series(raw, "medium")
    out["support_or_category_raw"] = pick_series(raw, "support_type")
    out["attribution_class"] = pick_series(raw, "attribution_class")
    out["artist_id_or_slug"] = pick_series(raw, "artist_slug")
    out["artist_name"] = pick_series(raw, "artist_name")
    out["artist_birth_year"] = pick_series(raw, "artist_birth_year")
    out["artist_total_works"] = pick_series(raw, "artist_total_works")
    out["artist_followers"] = pick_series(raw, "ln_followers")
    out["artist_is_p1"] = pick_series(raw, "artist_is_p1")
    out["artist_solo_count"] = pick_series(raw, "solo_count")
    out["artist_group_count"] = pick_series(raw, "group_count")
    out["artist_fair_count"] = pick_series(raw, "fair_count")
    out["gallery_name"] = pick_series(raw, "gallery_name")
    out["gallery_type"] = pick_series(raw, "gallery_type")
    return finalize(out)


def standardize_legacy_artue(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """기존 실험 source_files의 Artue 가격 포함 CSV를 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "artue"
    out["source_artwork_id"] = pick_series(raw, "Handle")
    out["artwork_title"] = pick_series(raw, "Title")
    out["artwork_year"] = pick_series(raw, "Year")
    out["artwork_url"] = pick_series(raw, "URL")
    out["price_krw"] = pick_series(raw, "Price (KRW)")
    out["price_usd"] = pick_series(raw, "Price (USD)")
    out["price_currency"] = pick_series(raw, "Price (USD)").map(
        lambda value: "USD" if clean_text(value) else "KRW"
    )
    out["price_amount"] = pick_series(raw, "Price (USD)").combine_first(pick_series(raw, "Price (KRW)"))
    out["width_cm"] = pick_series(raw, "Width (cm)")
    out["height_cm"] = pick_series(raw, "Height (cm)")
    out["depth_cm"] = pick_series(raw, "Depth (cm)")
    out["medium_raw"] = pick_series(raw, "Medium (EN)")
    out["medium_ko"] = pick_series(raw, "Medium (KO)")
    out["medium_category_raw"] = pick_series(raw, "Medium (EN)")
    out["status"] = pick_series(raw, "Status")
    out["artist_id_or_slug"] = pick_series(raw, "Handle")
    out["artist_name"] = pick_series(raw, "Artist")
    out["artist_nationality"] = pick_series(raw, "Nationality")
    out["artist_nationality_ko"] = pick_series(raw, "Nationality KO")
    return finalize(out)


def standardize_legacy_gallery_primary(raw: pd.DataFrame, source_file: str, source_variant: str) -> pd.DataFrame:
    """기존 실험 source_files의 1차 시장 전달본을 표준 컬럼으로 바꾼다."""
    out = new_standard_frame(raw, source_file, source_variant)
    out["source_family"] = "gallery_primary"
    out["source_artwork_id"] = pick_series(raw, "idx")
    out["artwork_title"] = pick_series(raw, "title")
    out["artwork_year"] = pick_series(raw, "연도")
    out["image_url"] = pick_series(raw, "img_src")
    out["price_krw"] = ""
    out["price_raw"] = pick_series(raw, "price_raw")
    out["price_currency"] = pick_series(raw, "price").map(lambda value: "KRW" if clean_text(value) else "")
    out["price_amount"] = pick_series(raw, "price")
    out["width_cm"] = pick_series(raw, "width")
    out["height_cm"] = pick_series(raw, "height")
    out["dimensions_raw"] = pick_series(raw, "size_raw")
    out["medium_raw"] = pick_series(raw, "materials")
    out["medium_category_raw"] = pick_series(raw, "materials")
    out["artist_name"] = pick_series(raw, "name_eng")
    out["artist_nationality_ko"] = pick_series(raw, "국적")
    out["artist_birth_year"] = pick_series(raw, "birth_year")
    out["gallery_name"] = pick_series(raw, "gallery_name(EN)")
    out["gallery_cities"] = pick_series(raw, "gallery_city")
    return finalize(out)


def load_optional_csv(path: Path) -> pd.DataFrame:
    """선택 입력 CSV가 있으면 읽고, 없으면 빈 DataFrame을 반환한다."""
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def enrich_artsy_with_artist_csv(works: pd.DataFrame, artists: pd.DataFrame) -> pd.DataFrame:
    """Artsy 작가 CSV로 전시 수, 성별 등 부족한 작가 메타를 보강한다."""
    if artists.empty or "slug" not in artists.columns:
        return works
    meta = artists.copy()
    meta["_key"] = meta["slug"].map(clean_text)
    meta = meta.drop_duplicates("_key", keep="first").set_index("_key")
    mask = works["source_family"].eq("artsy")
    keys = works.loc[mask, "artist_id_or_slug"].map(clean_text)
    fill_map = {
        "artist_gender": "gender",
        "artist_solo_count": "solo_count",
        "artist_group_count": "group_count",
        "artist_fair_count": "fair_count",
        "artist_total_shows": "total_shows",
        "artist_nationality": "nationality",
        "artist_birth_year": "birth_year",
        "artist_total_works": "total_works",
        "artist_for_sale": "for_sale_works",
        "artist_followers": "followers",
        "artist_is_p1": "is_p1",
    }
    for out_col, meta_col in fill_map.items():
        if meta_col not in meta.columns:
            continue
        mapped = keys.map(meta[meta_col].to_dict())
        empty = works.loc[mask, out_col].map(clean_text).eq("")
        works.loc[mask & empty, out_col] = mapped.loc[empty]
    return works


def enrich_saatchi_with_artist_csv(works: pd.DataFrame, artists: pd.DataFrame) -> pd.DataFrame:
    """Saatchi 작가 CSV로 bio, 교육, 전시 등 부족한 작가 메타를 보강한다."""
    if artists.empty or "artist_id" not in artists.columns:
        return works
    meta = artists.copy()
    meta["_key"] = meta["artist_id"].map(clean_text)
    meta = meta.drop_duplicates("_key", keep="first").set_index("_key")
    mask = works["source_family"].eq("saatchi")
    keys = works.loc[mask, "artist_id_or_slug"].map(clean_text)
    fill_map = {
            "artist_location_country": "country",
        "artist_followers": "followers",
        "artist_total_works": "total_artworks",
        "artist_bio": "bio",
        "artist_education": "education",
        "artist_exhibitions": "exhibitions",
        "artist_instagram_url": "social_links.instagram",
        "artist_website_url": "social_links.artistHomepage",
    }
    for out_col, meta_col in fill_map.items():
        if meta_col not in meta.columns:
            continue
        mapped = keys.map(meta[meta_col].to_dict())
        empty = works.loc[mask, out_col].map(clean_text).eq("")
        works.loc[mask & empty, out_col] = mapped.loc[empty]
    return works


def enrich_artue_with_artist_csv(works: pd.DataFrame, artists: pd.DataFrame) -> pd.DataFrame:
    """Artue 작가 CSV로 국적, 작가 소개, 가격 범위 등 부족한 메타를 보강한다."""
    if artists.empty or "handle" not in artists.columns:
        return works
    meta = artists.copy()
    meta["_key"] = meta["handle"].map(clean_text)
    meta = meta.drop_duplicates("_key", keep="first").set_index("_key")
    mask = works["source_family"].eq("artue")
    keys = works.loc[mask, "artist_id_or_slug"].map(clean_text)
    fill_map = {
        "artist_nationality": "nationality",
        "artist_nationality_ko": "nationality_ko",
        "artist_hometown": "hometown",
        "artist_birth_year": "birth_year",
        "artist_bio": "bio",
        "artist_total_works": "work_count",
        "artist_for_sale": "available_count",
        "artist_instagram_url": "instagram_url",
        "artist_website_url": "website_url",
    }
    for out_col, meta_col in fill_map.items():
        if meta_col not in meta.columns:
            continue
        mapped = keys.map(meta[meta_col].to_dict())
        empty = works.loc[mask, out_col].map(clean_text).eq("")
        works.loc[mask & empty, out_col] = mapped.loc[empty]
    return works


def collect_standardized_frames(input_dir: Path, source_scope: str = "all") -> list[pd.DataFrame]:
    """입력 폴더에서 알려진 작품 CSV를 찾아 표준화한다."""
    specs = [
        ("ahto_viewer_exports/ahto_export_artsy_artworks.csv", "ahto_artsy", standardize_artsy),
        ("source_platform_latest/source_platform_artsy_kr_artworks.csv", "source_platform_artsy", standardize_artsy),
        ("ahto_viewer_exports/ahto_export_saatchi_artworks.csv", "ahto_saatchi", standardize_saatchi),
        ("source_platform_latest/source_platform_saatchi_kr_artworks_split_13102.csv", "source_platform_saatchi_split", standardize_saatchi),
        ("artue_exports/artue_artworks.csv", "artue", standardize_artue),
        ("legacy_experiment_sources/legacy_artsy_kr_artworks.csv", "legacy_artsy", standardize_artsy),
        ("legacy_experiment_sources/legacy_saatchi_cleaned.csv", "legacy_saatchi", standardize_legacy_saatchi),
        ("legacy_experiment_sources/legacy_artue_price_included.csv", "legacy_artue", standardize_legacy_artue),
        ("legacy_experiment_sources/legacy_gallery_primary_260504.csv", "legacy_gallery_primary", standardize_legacy_gallery_primary),
    ]

    if source_scope == "legacy":
        specs = [spec for spec in specs if spec[1].startswith("legacy_")]
    elif source_scope == "non_legacy":
        specs = [spec for spec in specs if not spec[1].startswith("legacy_")]
    elif source_scope != "all":
        raise ValueError(f"지원하지 않는 source_scope입니다: {source_scope}")

    frames: list[pd.DataFrame] = []
    for relative_path, variant, func in specs:
        path = input_dir / relative_path
        if not path.exists():
            continue
        raw = pd.read_csv(path)
        frame = func(raw, path.name, variant)
        frames.append(frame)
        print(f"loaded {relative_path}: raw={len(raw):,}, standardized={len(frame):,}")
    return frames


def merge_and_dedupe(input_dir: Path, output_dir: Path, source_scope: str = "all") -> dict[str, Any]:
    """표준화, 메타 보강, 중복 제거를 한 번에 실행한다."""
    frames = collect_standardized_frames(input_dir, source_scope=source_scope)
    if not frames:
        raise FileNotFoundError(f"작품 CSV를 찾지 못했습니다: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    removed_frames: list[pd.DataFrame] = []
    merged = pd.concat(frames, ignore_index=True)

    merged = enrich_artsy_with_artist_csv(
        merged,
        load_optional_csv(input_dir / "source_platform_latest/source_platform_artsy_kr_artists_full.csv"),
    )
    merged = enrich_saatchi_with_artist_csv(
        merged,
        load_optional_csv(input_dir / "ahto_viewer_exports/ahto_export_saatchi_artists.csv"),
    )
    merged = enrich_artue_with_artist_csv(
        merged,
        load_optional_csv(input_dir / "artue_exports/artue_artists.csv"),
    )

    merged = finalize(merged)
    merged["dedupe_key"] = merged.apply(build_dedupe_key, axis=1)

    before_dedupe = len(merged)
    by_source_before = merged["source_variant"].value_counts().to_dict()

    # 같은 dedupe_key 안에서는 우선순위가 높은 수집본을 먼저 남긴다.
    # 같은 우선순위라면 가격, 이미지, URL이 더 많이 채워진 행을 우선한다.
    completeness_cols = ["price_krw", "price_usd", "image_url", "artwork_url", "artist_name"]
    merged["_completeness"] = merged[completeness_cols].apply(
        lambda row: sum(1 for value in row if clean_text(value)),
        axis=1,
    )
    merged = merged.sort_values(
        ["dedupe_key", "dedupe_rank", "_completeness"],
        ascending=[True, True, False],
    )
    deduped = merged.drop_duplicates("dedupe_key", keep="first").drop(columns=["_completeness"])
    deduped = deduped.sort_values(["source_family", "artist_name", "artwork_title"]).reset_index(drop=True)

    deduped_before_price_filter = len(deduped)
    no_price_mask = ~has_any_price(deduped)
    no_price_rows = int(no_price_mask.sum())
    no_price_by_source_family = deduped.loc[no_price_mask, "source_family"].value_counts().to_dict()
    no_price_by_source_variant = deduped.loc[no_price_mask, "source_variant"].value_counts().to_dict()
    removed = deduped.loc[no_price_mask].copy()
    removed["removed_reason"] = "no_positive_price"
    removed_frames.append(removed)
    deduped = deduped.loc[~no_price_mask].reset_index(drop=True)

    placeholder_price_mask = is_placeholder_price(deduped)
    placeholder_price_rows = int(placeholder_price_mask.sum())
    placeholder_price_values = (
        pd.to_numeric(deduped.loc[placeholder_price_mask, "price_krw"], errors="coerce")
        .value_counts()
        .sort_index()
        .to_dict()
    )
    placeholder_price_by_source_family = deduped.loc[
        placeholder_price_mask, "source_family"
    ].value_counts().to_dict()
    placeholder_price_by_source_variant = deduped.loc[
        placeholder_price_mask, "source_variant"
    ].value_counts().to_dict()
    removed = deduped.loc[placeholder_price_mask].copy()
    removed["removed_reason"] = "placeholder_price_1_or_999999999"
    removed_frames.append(removed)
    deduped = deduped.loc[~placeholder_price_mask].reset_index(drop=True)

    three_d_mask = is_3d_artwork(deduped)
    three_d_rows = int(three_d_mask.sum())
    three_d_by_category = deduped.loc[
        three_d_mask, "medium_category_raw"
    ].astype(str).str.strip().str.lower().value_counts().to_dict()
    three_d_by_source_family = deduped.loc[
        three_d_mask, "source_family"
    ].value_counts().to_dict()
    three_d_by_source_variant = deduped.loc[
        three_d_mask, "source_variant"
    ].value_counts().to_dict()
    removed = deduped.loc[three_d_mask].copy()
    removed["removed_reason"] = "3d_artwork"
    removed_frames.append(removed)
    deduped = deduped.loc[~three_d_mask].reset_index(drop=True)

    obvious_size_error_mask = is_obvious_size_error(deduped)
    obvious_size_error_rows = int(obvious_size_error_mask.sum())
    obvious_size_error_by_category = deduped.loc[
        obvious_size_error_mask, "medium_category_raw"
    ].astype(str).str.strip().str.lower().value_counts().to_dict()
    obvious_size_error_by_source_family = deduped.loc[
        obvious_size_error_mask, "source_family"
    ].value_counts().to_dict()
    obvious_size_error_by_source_variant = deduped.loc[
        obvious_size_error_mask, "source_variant"
    ].value_counts().to_dict()
    removed = deduped.loc[obvious_size_error_mask].copy()
    removed["removed_reason"] = "obvious_size_error"
    removed_frames.append(removed)
    deduped = deduped.loc[~obvious_size_error_mask].reset_index(drop=True)

    output_csv = output_dir / "standardized_artworks_merged_deduped.csv"
    summary_json = output_dir / "standardization_merge_summary.json"
    removed_csv = output_dir / "standardized_artworks_removed_by_filter.csv"

    drop_stage1_output_excluded_columns(deduped).to_csv(output_csv, index=False, encoding="utf-8-sig")
    removed_all = pd.concat(removed_frames, ignore_index=True) if removed_frames else pd.DataFrame()
    drop_stage1_output_excluded_columns(removed_all).to_csv(removed_csv, index=False, encoding="utf-8-sig")
    outlier_summary = build_outlier_audit(deduped, output_dir)

    summary = {
        "stage": "stage1_source_merge_dedupe_2d_cleaning",
        "source_scope": source_scope,
        "stage_description": (
            "기존 원본 데이터와 추가 수집 데이터를 합친 뒤 중복, 가격 숫자 없음, "
            "placeholder 가격, 입체 작품, 명백한 크기 오류를 제거한 1차 정리 단계. "
            "환율 변환, 가격 보정, 모델 피처 생성은 수행하지 않는다."
        ),
        "input_dir": str(input_dir),
        "output_csv": str(output_csv),
        "removed_csv": str(removed_csv),
        "raw_standardized_rows_before_dedupe": before_dedupe,
        "deduped_rows_before_price_filter": deduped_before_price_filter,
        "final_rows_after_price_filter": len(deduped),
        "removed_duplicate_rows": before_dedupe - deduped_before_price_filter,
        "removed_no_price_rows": no_price_rows,
        "removed_no_price_by_source_family": no_price_by_source_family,
        "removed_no_price_by_source_variant": no_price_by_source_variant,
        "removed_placeholder_price_rows": placeholder_price_rows,
        "removed_placeholder_price_values": placeholder_price_values,
        "removed_placeholder_price_by_source_family": placeholder_price_by_source_family,
        "removed_placeholder_price_by_source_variant": placeholder_price_by_source_variant,
        "removed_3d_artwork_rows": three_d_rows,
        "removed_3d_artwork_by_category": three_d_by_category,
        "removed_3d_artwork_by_source_family": three_d_by_source_family,
        "removed_3d_artwork_by_source_variant": three_d_by_source_variant,
        "removed_obvious_size_error_rows": obvious_size_error_rows,
        "removed_obvious_size_error_by_category": obvious_size_error_by_category,
        "removed_obvious_size_error_by_source_family": obvious_size_error_by_source_family,
        "removed_obvious_size_error_by_source_variant": obvious_size_error_by_source_variant,
        "by_source_before_dedupe": by_source_before,
        "by_source_after_dedupe": deduped["source_variant"].value_counts().to_dict(),
        "by_source_family_after_dedupe": deduped["source_family"].value_counts().to_dict(),
        "dedupe_rule": "source_family + source_artwork_id 우선, 없으면 source_family + artwork_url, 둘 다 없으면 artist/title/size/price fallback",
        "source_priority": SOURCE_PRIORITY,
        "outlier_audit": outlier_summary,
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    """명령행 옵션을 해석한다."""
    parser = argparse.ArgumentParser(description="수집 CSV를 작품 단위 표준 CSV 하나로 통합합니다.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="원천 CSV 하위 폴더가 들어 있는 폴더. 기본값은 패키지 루트의 01_source_raw.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="결과 파일을 저장할 폴더. 기본값은 패키지 루트의 03_outputs.",
    )
    parser.add_argument(
        "--source-scope",
        choices=["all", "legacy", "non_legacy"],
        default="all",
        help="처리할 원천 범위. all=전체, legacy=기존 실험 원본만, non_legacy=신규/AHTO 수집본만.",
    )
    return parser.parse_args()


def main() -> None:
    """스크립트 진입점."""
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    summary = merge_and_dedupe(input_dir, output_dir, source_scope=args.source_scope)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
