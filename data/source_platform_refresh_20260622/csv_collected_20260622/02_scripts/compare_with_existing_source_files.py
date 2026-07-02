#!/usr/bin/env python3
"""
기존 실험 source_files 원본과 새 표준 통합 CSV를 비교한다.

비교 기준:
- 기존 원본 폴더:
  docs/track6/dataset_handover_20260619/reproduction_package/source_files
- 새 통합 CSV:
  data/source_platform_refresh_20260622/csv_collected_20260622/03_outputs/standardized_artworks_merged_deduped.csv

출력:
- 03_outputs/existing_source_vs_new_standardized_comparison_summary.json
- 03_outputs/existing_source_records_not_in_new_standardized.csv
- 03_outputs/existing_source_records_matched_new_standardized.csv

주의:
- 이 스크립트는 비교만 한다.
- 새 통합 CSV나 기존 source_files를 수정하지 않는다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = BASE_DIR.parent
PROJECT_ROOT = BASE_DIR.parents[3]
DEFAULT_SOURCE_DIR = (
    PROJECT_ROOT
    / "docs/track6/dataset_handover_20260619/reproduction_package/source_files"
)
DEFAULT_OUTPUT_DIR = PACKAGE_DIR / "03_outputs"
DEFAULT_NEW_CSV = DEFAULT_OUTPUT_DIR / "standardized_artworks_merged_deduped.csv"


def clean_text(value: Any) -> str:
    """비교용 문자열을 정규화한다."""
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    if text in {"nan", "none", "null", "<na>"}:
        return ""
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"www\.", "", text)
    text = re.sub(r"\?.*$", "", text)
    text = re.sub(r"/+$", "", text)
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_id(value: Any) -> str:
    """ID 비교용 문자열을 정규화한다."""
    text = clean_text(value)
    if text.endswith(" 0"):
        text = text[:-2]
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def clean_url(value: Any) -> str:
    """URL 비교용 문자열을 정규화한다."""
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    if text in {"", "nan", "none", "null", "<na>"}:
        return ""
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"www\.", "", text)
    text = re.sub(r"\?.*$", "", text)
    return re.sub(r"/+$", "", text)


def num_bucket(value: Any, step: float = 1.0) -> str:
    """숫자를 비교용 버킷 문자열로 만든다."""
    num = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(num):
        return ""
    return str(round(float(num) / step) * step).rstrip("0").rstrip(".")


def make_semantic_key(row: pd.Series, artist: str, title: str, width: str, height: str) -> str:
    """ID/URL이 없거나 불안정할 때 쓰는 보조 비교 키를 만든다."""
    return "|".join(
        [
            clean_text(row.get(artist)),
            clean_text(row.get(title)),
            num_bucket(row.get(width), 1.0),
            num_bucket(row.get(height), 1.0),
        ]
    )


def normalize_new(path: Path) -> pd.DataFrame:
    """새 표준 통합 CSV를 비교 가능한 키 형태로 정리한다."""
    raw = pd.read_csv(path, low_memory=False)
    out = pd.DataFrame(
        {
            "new_row_index": raw.index,
            "source_family": raw["source_family"].map(clean_text),
            "source_artwork_id_key": raw["source_artwork_id"].map(clean_id),
            "artwork_url_key": raw["artwork_url"].map(clean_url),
            "image_url_key": raw["image_url"].map(clean_url),
            "semantic_key": raw.apply(
                lambda row: make_semantic_key(
                    row, "artist_name", "artwork_title", "width_cm", "height_cm"
                ),
                axis=1,
            ),
            "source_variant": raw["source_variant"],
            "source_artwork_id": raw["source_artwork_id"],
            "artwork_url": raw["artwork_url"],
            "artist_name": raw["artist_name"],
            "artwork_title": raw["artwork_title"],
            "price_krw": raw["price_krw"],
        }
    )
    return out


def normalize_artsy(path: Path) -> pd.DataFrame:
    """기존 Artsy 원본을 비교 가능한 형태로 정리한다."""
    raw = pd.read_csv(path, low_memory=False)
    return pd.DataFrame(
        {
            "existing_source_file": path.name,
            "existing_source_family": "artsy",
            "existing_row_index": raw.index,
            "source_artwork_id": raw["artwork_id"],
            "source_artwork_id_key": raw["artwork_id"].map(clean_id),
            "artwork_url": raw["artwork_url"],
            "artwork_url_key": raw["artwork_url"].map(clean_url),
            "image_url": raw["image_url"],
            "image_url_key": raw["image_url"].map(clean_url),
            "semantic_key": raw.apply(
                lambda row: make_semantic_key(
                    row, "artist_name", "title", "width_cm", "height_cm"
                ),
                axis=1,
            ),
            "artist_name": raw["artist_name"],
            "artwork_title": raw["title"],
            "price_krw": raw["price_krw"],
        }
    )


def normalize_saatchi(path: Path) -> pd.DataFrame:
    """기존 Saatchi 원본을 비교 가능한 형태로 정리한다."""
    raw = pd.read_csv(path, low_memory=False)
    return pd.DataFrame(
        {
            "existing_source_file": path.name,
            "existing_source_family": "saatchi",
            "existing_row_index": raw.index,
            "source_artwork_id": raw["artwork_id"],
            "source_artwork_id_key": raw["artwork_id"].map(clean_id),
            "artwork_url": raw["artwork_url"],
            "artwork_url_key": raw["artwork_url"].map(clean_url),
            "image_url": raw["image_url"],
            "image_url_key": raw["image_url"].map(clean_url),
            "semantic_key": raw.apply(
                lambda row: make_semantic_key(
                    row, "artist_name", "title", "area_cm2", "aspect_ratio"
                ),
                axis=1,
            ),
            "artist_name": raw["artist_name"],
            "artwork_title": raw["title"],
            "price_krw": raw["price_krw"],
        }
    )


def normalize_artue(path: Path) -> pd.DataFrame:
    """기존 Artue 원본을 비교 가능한 형태로 정리한다."""
    raw = pd.read_csv(path, low_memory=False)
    return pd.DataFrame(
        {
            "existing_source_file": path.name,
            "existing_source_family": "artue",
            "existing_row_index": raw.index,
            "source_artwork_id": raw["Handle"],
            "source_artwork_id_key": raw["Handle"].map(clean_id),
            "artwork_url": raw["URL"],
            "artwork_url_key": raw["URL"].map(clean_url),
            "image_url": "",
            "image_url_key": "",
            "semantic_key": raw.apply(
                lambda row: make_semantic_key(
                    row, "Artist", "Title", "Width (cm)", "Height (cm)"
                ),
                axis=1,
            ),
            "artist_name": raw["Artist"],
            "artwork_title": raw["Title"],
            "price_krw": raw["Price (KRW)"],
        }
    )


def normalize_gallery_primary(path: Path) -> pd.DataFrame:
    """기존 1차 시장 전달본을 별도 원천으로 정리한다."""
    raw = pd.read_csv(path, low_memory=False)
    return pd.DataFrame(
        {
            "existing_source_file": path.name,
            "existing_source_family": "gallery_primary",
            "existing_row_index": raw.index,
            "source_artwork_id": raw["idx"],
            "source_artwork_id_key": raw["idx"].map(clean_id),
            "artwork_url": "",
            "artwork_url_key": "",
            "image_url": raw.get("img_src", ""),
            "image_url_key": raw.get("img_src", pd.Series([""] * len(raw))).map(clean_url),
            "semantic_key": raw.apply(
                lambda row: make_semantic_key(row, "name_eng", "title", "width", "height"),
                axis=1,
            ),
            "artist_name": raw["name_eng"],
            "artwork_title": raw["title"],
            "price_krw": raw["price"],
        }
    )


def load_existing(source_dir: Path) -> pd.DataFrame:
    """source_files 원본 4개를 비교용 한 테이블로 합친다."""
    frames = [
        normalize_artsy(source_dir / "artsy_kr_artworks.csv"),
        normalize_saatchi(source_dir / "saatchi_cleaned.csv"),
        normalize_artue(next(source_dir.glob("artue_*.csv"))),
        normalize_gallery_primary(source_dir / "1차 시장 데이터 - 전달본_260504.csv"),
    ]
    return pd.concat(frames, ignore_index=True)


def match_existing_to_new(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """기존 원본 행이 새 통합 CSV에 있는지 ID/URL/이미지/보조키 순서로 찾는다."""
    new_by_id = {
        (row.source_family, row.source_artwork_id_key): row
        for row in new.itertuples()
        if row.source_artwork_id_key
    }
    new_by_url = {
        (row.source_family, row.artwork_url_key): row
        for row in new.itertuples()
        if row.artwork_url_key
    }
    new_by_image = {
        (row.source_family, row.image_url_key): row
        for row in new.itertuples()
        if row.image_url_key
    }
    new_by_semantic = {
        (row.source_family, row.semantic_key): row
        for row in new.itertuples()
        if row.semantic_key and row.semantic_key.count("|") == 3
    }

    records: list[dict[str, Any]] = []
    for row in existing.itertuples(index=False):
        family = row.existing_source_family
        matched = None
        method = ""
        if family != "gallery_primary":
            for method_name, lookup, key in [
                ("source_artwork_id", new_by_id, row.source_artwork_id_key),
                ("artwork_url", new_by_url, row.artwork_url_key),
                ("image_url", new_by_image, row.image_url_key),
                ("semantic_key", new_by_semantic, row.semantic_key),
            ]:
                if key and (family, key) in lookup:
                    matched = lookup[(family, key)]
                    method = method_name
                    break

        item = row._asdict()
        item["is_in_new_standardized"] = matched is not None
        item["match_method"] = method
        item["new_row_index"] = getattr(matched, "new_row_index", "")
        item["new_source_variant"] = getattr(matched, "source_variant", "")
        item["new_source_artwork_id"] = getattr(matched, "source_artwork_id", "")
        item["new_artwork_url"] = getattr(matched, "artwork_url", "")
        records.append(item)
    return pd.DataFrame(records)


def main() -> None:
    """비교를 실행하고 결과 파일을 저장한다."""
    source_dir = DEFAULT_SOURCE_DIR
    new_csv = DEFAULT_NEW_CSV
    new = normalize_new(new_csv)
    existing = load_existing(source_dir)
    compared = match_existing_to_new(existing, new)

    matched = compared[compared["is_in_new_standardized"]].copy()
    missing = compared[~compared["is_in_new_standardized"]].copy()

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matched_csv = DEFAULT_OUTPUT_DIR / "existing_source_records_matched_new_standardized.csv"
    missing_csv = DEFAULT_OUTPUT_DIR / "existing_source_records_not_in_new_standardized.csv"
    summary_json = DEFAULT_OUTPUT_DIR / "existing_source_vs_new_standardized_comparison_summary.json"
    matched.to_csv(matched_csv, index=False, encoding="utf-8-sig")
    missing.to_csv(missing_csv, index=False, encoding="utf-8-sig")

    summary = {
        "existing_source_dir": str(source_dir),
        "new_standardized_csv": str(new_csv),
        "existing_rows_total": len(compared),
        "new_rows_total": len(new),
        "matched_rows": int(compared["is_in_new_standardized"].sum()),
        "missing_rows": int((~compared["is_in_new_standardized"]).sum()),
        "by_existing_source": compared.groupby("existing_source_family")[
            "is_in_new_standardized"
        ].agg(["count", "sum"]).rename(columns={"count": "existing_rows", "sum": "matched_rows"}).to_dict("index"),
        "missing_by_existing_source": missing["existing_source_family"].value_counts().to_dict(),
        "matched_by_method": matched["match_method"].value_counts().to_dict(),
        "outputs": {
            "matched_csv": str(matched_csv),
            "missing_csv": str(missing_csv),
            "summary_json": str(summary_json),
        },
        "note": "gallery_primary 원천은 새 Artsy/Saatchi/Artue 통합 CSV에 대응 원천이 없으므로 전부 missing으로 잡힌다.",
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
