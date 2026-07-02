#!/usr/bin/env python3
"""
Saatchi / Artsy 원본 CSV 표준화 및 병합 스크립트.

필요한 입력 파일:
  - 01_source/saatchi_kr_artworks.csv
  - 01_source/artsy_kr_artworks.csv

실행 방법:
  1. 이 파일이 있는 폴더로 이동
  2. python3 standardize_and_merge_saatchi_artsy.py

출력 파일:
  - 02_output/saatchi_standardized.csv
  - 02_output/artsy_standardized.csv
  - 02_output/saatchi_artsy_standardized_merged.csv
  - 02_output/standardization_summary.json

처리 범위:
  - 두 원본 CSV를 읽는다.
  - 플랫폼별 컬럼명을 공통 컬럼명으로 맞춘다.
  - 숫자 컬럼은 숫자형으로 정리한다.
  - Saatchi의 분리된 작가명은 표시용 artist_name으로 합친다.
  - Artsy의 date에서 4자리 연도만 artwork_year로 추출한다.
  - 두 표준화 결과를 하나의 CSV로 병합한다.

주의:
  - 가격을 새로 계산하거나 예측값을 만들지 않는다.
  - 작가별 통계, 작품별 통계, 모델 피처를 새로 생성하지 않는다.
  - DB나 외부 CSV lookup을 사용하지 않고, 같은 폴더 안의 01_source 파일만 사용한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "01_source"
OUTPUT_DIR = BASE_DIR / "02_output"

SAATCHI_SOURCE = SOURCE_DIR / "saatchi_kr_artworks.csv"
ARTSY_SOURCE = SOURCE_DIR / "artsy_kr_artworks.csv"


# 두 플랫폼을 합친 뒤 공통으로 볼 컬럼 목록이다.
# 원본에 없는 컬럼은 빈 값으로 채운다.
STANDARD_COLUMNS = [
    "source",
    "source_row_index",
    "source_artwork_id",
    "artwork_title",
    "artwork_year",
    "artwork_url",
    "image_url",
    "price_krw",
    "price_usd",
    "price_raw",
    "price_currency",
    "price_amount",
    "width_cm",
    "height_cm",
    "depth_cm",
    "dimensions_raw",
    "medium_raw",
    "medium_category_raw",
    "medium_type_raw",
    "materials_raw",
    "support_or_category_raw",
    "subject_raw",
    "style_raw",
    "orientation_raw",
    "size_bin_raw",
    "attribution_class",
    "availability",
    "is_auction",
    "artist_id_or_slug",
    "artist_name",
    "artist_first_name",
    "artist_last_name",
    "artist_nationality",
    "artist_birth_year",
    "artist_total_works",
    "artist_for_sale",
    "artist_followers",
    "artist_is_p1",
    "artist_gender",
    "artist_city",
    "artist_country",
    "gallery_name",
    "gallery_type",
    "gallery_cities",
]


def clean_text(value: object) -> str:
    """NaN과 공백을 정리해서 문자열로 반환한다."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return re.sub(r"\s+", " ", text)


def clean_number(value: object) -> float | pd.NA:
    """통화 기호, 콤마 등이 섞인 값을 숫자로 변환한다."""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-", "-."}:
        return pd.NA
    try:
        return float(text)
    except ValueError:
        return pd.NA


def extract_year(value: object) -> str:
    """date 컬럼에서 4자리 연도만 추출한다. 없으면 빈 값으로 둔다."""
    text = clean_text(value)
    match = re.search(r"(18|19|20)\d{2}", text)
    return match.group(0) if match else ""


def join_artist_name(first_name: object, last_name: object) -> str:
    """Saatchi처럼 first/last가 나뉜 작가명을 하나의 표시명으로 합친다."""
    parts = [clean_text(first_name), clean_text(last_name)]
    return " ".join(part for part in parts if part)


def empty_frame(index: Iterable[int]) -> pd.DataFrame:
    """표준 컬럼을 가진 빈 프레임을 만든 뒤 index 길이에 맞춰 확장한다."""
    return pd.DataFrame(index=index, columns=STANDARD_COLUMNS)


def finalize_standard_frame(df: pd.DataFrame) -> pd.DataFrame:
    """표준 컬럼 순서를 고정하고 숫자 컬럼 타입을 정리한다."""
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    out = df[STANDARD_COLUMNS].copy()

    numeric_columns = [
        "price_krw",
        "price_usd",
        "price_amount",
        "width_cm",
        "height_cm",
        "depth_cm",
        "artist_birth_year",
        "artist_total_works",
        "artist_for_sale",
        "artist_followers",
    ]
    for col in numeric_columns:
        out[col] = out[col].map(clean_number)

    # 텍스트 컬럼은 불필요한 공백과 NaN 문자열을 제거한다.
    for col in out.columns:
        if col not in numeric_columns:
            out[col] = out[col].map(clean_text)

    return out


def standardize_saatchi(path: Path) -> pd.DataFrame:
    """Saatchi 원본 컬럼을 표준 컬럼으로 매핑한다."""
    raw = pd.read_csv(path)
    out = empty_frame(raw.index)

    out["source"] = "saatchi"
    out["source_row_index"] = raw.index
    out["source_artwork_id"] = raw.get("artwork_id", "")
    out["artwork_title"] = raw.get("title", "")
    out["artwork_url"] = raw.get("artwork_url", "")
    out["image_url"] = raw.get("image_url", "")

    out["price_krw"] = raw.get("price_krw", "")
    out["price_usd"] = raw.get("price_usd", "")
    out["price_raw"] = raw.get("price_usd", "")
    out["price_currency"] = raw.get("price_usd", "").map(
        lambda value: "USD" if clean_text(value) else ""
    )
    out["price_amount"] = raw.get("price_usd", "")

    out["width_cm"] = raw.get("width_cm", "")
    out["height_cm"] = raw.get("height_cm", "")
    out["depth_cm"] = raw.get("depth_cm", "")

    out["medium_raw"] = raw.get("mediums", "")
    out["medium_category_raw"] = raw.get("category", "")
    out["medium_type_raw"] = raw.get("mediums", "")
    out["materials_raw"] = raw.get("materials", "")
    out["support_or_category_raw"] = raw.get("category", "")
    out["subject_raw"] = raw.get("subject", "")
    out["style_raw"] = raw.get("styles", "")
    out["orientation_raw"] = raw.get("orientation", "")
    out["size_bin_raw"] = raw.get("size_bin", "")

    out["artist_id_or_slug"] = raw.get("artist_id", "")
    out["artist_first_name"] = raw.get("artist_first_name", "")
    out["artist_last_name"] = raw.get("artist_last_name", "")
    out["artist_name"] = [
        join_artist_name(first, last)
        for first, last in zip(out["artist_first_name"], out["artist_last_name"])
    ]
    out["artist_gender"] = raw.get("artist_gender", "")
    out["artist_city"] = raw.get("artist_city", "")
    out["artist_country"] = raw.get("country", "")

    return finalize_standard_frame(out)


def standardize_artsy(path: Path) -> pd.DataFrame:
    """Artsy 원본 컬럼을 표준 컬럼으로 매핑한다."""
    raw = pd.read_csv(path)
    out = empty_frame(raw.index)

    out["source"] = "artsy"
    out["source_row_index"] = raw.index
    out["source_artwork_id"] = raw.get("artwork_id", "")
    out["artwork_title"] = raw.get("title", "")
    out["artwork_year"] = raw.get("date", "").map(extract_year)
    out["artwork_url"] = raw.get("artwork_url", "")
    out["image_url"] = raw.get("image_url", "")

    out["price_krw"] = raw.get("price_krw", "")
    out["price_raw"] = raw.get("price_raw", "")
    out["price_currency"] = raw.get("price_currency", "")
    out["price_amount"] = raw.get("price_amount", "")

    out["width_cm"] = raw.get("width_cm", "")
    out["height_cm"] = raw.get("height_cm", "")
    out["depth_cm"] = raw.get("depth_cm", "")
    out["dimensions_raw"] = raw.get("dimensions_cm", "")

    out["medium_raw"] = raw.get("medium", "")
    out["medium_category_raw"] = raw.get("category", "")
    out["medium_type_raw"] = raw.get("medium_type", "")
    out["support_or_category_raw"] = raw.get("category", "")
    out["attribution_class"] = raw.get("attribution_class", "")
    out["availability"] = raw.get("availability", "")
    out["is_auction"] = raw.get("is_auction", "")

    out["artist_id_or_slug"] = raw.get("artist_slug", "")
    out["artist_name"] = raw.get("artist_name", "")
    out["artist_nationality"] = raw.get("artist_nationality", "")
    out["artist_birth_year"] = raw.get("artist_birth_year", "")
    out["artist_total_works"] = raw.get("artist_total_works", "")
    out["artist_for_sale"] = raw.get("artist_for_sale", "")
    out["artist_followers"] = raw.get("artist_followers", "")
    out["artist_is_p1"] = raw.get("artist_is_p1", "")

    out["gallery_name"] = raw.get("gallery_name", "")
    out["gallery_type"] = raw.get("gallery_type", "")
    out["gallery_cities"] = raw.get("gallery_cities", "")

    return finalize_standard_frame(out)


def write_summary(saatchi: pd.DataFrame, artsy: pd.DataFrame, merged: pd.DataFrame) -> None:
    """입출력 행 수와 표준화 규칙 요약을 JSON으로 남긴다."""
    summary = {
        "source_files": {
            "saatchi": str(SAATCHI_SOURCE.relative_to(BASE_DIR)),
            "artsy": str(ARTSY_SOURCE.relative_to(BASE_DIR)),
        },
        "row_counts": {
            "saatchi_standardized": int(len(saatchi)),
            "artsy_standardized": int(len(artsy)),
            "merged": int(len(merged)),
        },
        "output_files": {
            "saatchi_standardized": "02_output/saatchi_standardized.csv",
            "artsy_standardized": "02_output/artsy_standardized.csv",
            "merged": "02_output/saatchi_artsy_standardized_merged.csv",
        },
        "standard_columns": STANDARD_COLUMNS,
        "notes": [
            "source와 source_artwork_id, source_row_index를 남겨 원본 추적이 가능하게 했다.",
            "Saatchi의 artist_first_name/artist_last_name은 artist_name으로 결합했다.",
            "Artsy의 date는 4자리 연도만 추출해 artwork_year로 저장했다.",
            "원본에 없는 컬럼은 빈 값으로 유지했다.",
            "가격/크기/작가 수치 컬럼은 숫자형으로 변환했다.",
        ],
    }
    with (OUTPUT_DIR / "standardization_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main() -> None:
    if not SAATCHI_SOURCE.exists():
        raise FileNotFoundError(f"Saatchi 원본 파일이 없습니다: {SAATCHI_SOURCE}")
    if not ARTSY_SOURCE.exists():
        raise FileNotFoundError(f"Artsy 원본 파일이 없습니다: {ARTSY_SOURCE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    saatchi = standardize_saatchi(SAATCHI_SOURCE)
    artsy = standardize_artsy(ARTSY_SOURCE)
    merged = pd.concat([saatchi, artsy], ignore_index=True)

    saatchi.to_csv(OUTPUT_DIR / "saatchi_standardized.csv", index=False)
    artsy.to_csv(OUTPUT_DIR / "artsy_standardized.csv", index=False)
    merged.to_csv(OUTPUT_DIR / "saatchi_artsy_standardized_merged.csv", index=False)
    write_summary(saatchi, artsy, merged)

    print("표준화/병합 완료")
    print(f"- Saatchi: {len(saatchi):,} rows")
    print(f"- Artsy: {len(artsy):,} rows")
    print(f"- Merged: {len(merged):,} rows")
    print(f"- Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
