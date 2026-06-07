#!/usr/bin/env python3
"""Add standardized artist metadata columns to the latest Track6 feature split.

This script does not rebuild train/validation/test membership. It only joins
artist metadata already present in the full split CSVs into the separated
feature CSVs by `_track6_row_id`.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
OUT_SUMMARY = SPLIT_ROOT / "track6_artist_meta_feature_augmentation_summary.json"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "artist_meta_feature_augmentation_report.md"

SPLITS = ["train", "val_warm", "test_warm", "val_cold", "test_cold"]
FEATURE_FILES = [
    SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
    SPLIT_ROOT / "features" / "warm" / "track6_val_warm_warm_features.csv",
    SPLIT_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv",
    SPLIT_ROOT / "features" / "cold" / "track6_train_cold_features.csv",
    SPLIT_ROOT / "features" / "cold" / "track6_val_cold_cold_features.csv",
    SPLIT_ROOT / "features" / "cold" / "track6_test_cold_cold_features.csv",
]

RAW_META_COLUMNS = [
    "artist_works_log",
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_nationality",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_is_p1",
]

NUMERIC_META_COLUMNS = [
    "artist_works_log",
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_is_p1",
]

CATEGORICAL_META_COLUMNS = [
    "artist_meta_nationality",
]

EXHIBITION_COUNT_MAP = {
    "artist_exhibition_solo_count": "saatchi__solo_count",
    "artist_exhibition_group_count": "saatchi__group_count",
    "artist_exhibition_fair_count": "saatchi__fair_count",
}


def bool_to_numeric(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return 1.0
    if text in {"false", "0", "no", "n"}:
        return 0.0
    return np.nan


def normalize_meta(full: pd.DataFrame) -> pd.DataFrame:
    cols = ["_track6_row_id", *[c for c in RAW_META_COLUMNS if c in full.columns]]
    meta = full[cols].copy()
    for col in NUMERIC_META_COLUMNS:
        if col not in meta.columns:
            meta[col] = np.nan
        if col == "artist_meta_is_p1":
            meta[col] = meta[col].map(bool_to_numeric)
        else:
            meta[col] = pd.to_numeric(meta[col], errors="coerce")
        meta[f"{col}_is_missing"] = meta[col].isna().astype(int)

    for col in CATEGORICAL_META_COLUMNS:
        if col not in meta.columns:
            meta[col] = ""
        text = meta[col].astype("string").fillna("").str.strip()
        meta[col] = text.mask(text.eq(""), "__missing__")
        meta[f"{col}_is_missing"] = meta[col].eq("__missing__").astype(int)

    availability_cols = []
    for col in RAW_META_COLUMNS:
        missing_col = f"{col}_is_missing"
        if missing_col in meta.columns:
            availability_cols.append(missing_col)
    if availability_cols:
        meta["artist_meta_available_count"] = len(availability_cols) - meta[availability_cols].sum(axis=1)
        meta["artist_meta_completeness_score"] = meta["artist_meta_available_count"] / len(availability_cols)
    else:
        meta["artist_meta_available_count"] = 0
        meta["artist_meta_completeness_score"] = 0.0

    return meta.drop_duplicates("_track6_row_id")


def normalize_exhibition_counts(full: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(
        RAW_COLLECTED,
        usecols=lambda c: c in set(EXHIBITION_COUNT_MAP.values()),
        low_memory=False,
    )
    raw["_raw_row_index"] = raw.index.astype(int)
    count_cols = ["_raw_row_index", *EXHIBITION_COUNT_MAP.values()]
    raw = raw[count_cols].copy()

    base = full[["_track6_row_id", "track4_source_row_index"]].copy()
    base["track4_source_row_index"] = pd.to_numeric(base["track4_source_row_index"], errors="coerce").astype("Int64")
    out = base.merge(
        raw,
        left_on="track4_source_row_index",
        right_on="_raw_row_index",
        how="left",
        validate="many_to_one",
    )
    result = out[["_track6_row_id"]].copy()
    for std_col, raw_col in EXHIBITION_COUNT_MAP.items():
        value = pd.to_numeric(out[raw_col], errors="coerce")
        # Counts above 200 are almost certainly years accidentally parsed as counts.
        value = value.mask(value > 200)
        result[std_col] = value
        result[f"{std_col}_is_missing"] = result[std_col].isna().astype(int)
    count_columns = list(EXHIBITION_COUNT_MAP.keys())
    result["artist_exhibition_total_count"] = result[count_columns].sum(axis=1, min_count=1)
    result["artist_exhibition_available_count"] = len(count_columns) - result[
        [f"{c}_is_missing" for c in count_columns]
    ].sum(axis=1)
    return result.drop_duplicates("_track6_row_id")


def load_meta_by_row_id() -> pd.DataFrame:
    frames = []
    for split in SPLITS:
        path = SPLIT_ROOT / f"track6_{split}.csv"
        frames.append(pd.read_csv(path, low_memory=False))
    full = pd.concat(frames, ignore_index=True)
    meta = normalize_meta(full)
    exhibition = normalize_exhibition_counts(full)
    return meta.merge(exhibition, on="_track6_row_id", how="left", validate="one_to_one")


def augment_feature_file(path: Path, meta: pd.DataFrame) -> dict[str, Any]:
    features = pd.read_csv(path, low_memory=False)
    before_cols = list(features.columns)
    add_cols = [c for c in meta.columns if c != "_track6_row_id"]
    features = features.drop(columns=[c for c in add_cols if c in features.columns], errors="ignore")
    out = features.merge(meta, on="_track6_row_id", how="left", validate="many_to_one")
    out.to_csv(path, index=False)

    stats = {
        "path": str(path.relative_to(REPO)),
        "rows": int(len(out)),
        "columns_before": int(len(before_cols)),
        "columns_after": int(len(out.columns)),
        "added_columns": add_cols,
        "missing_join_rows": int(out["artist_meta_completeness_score"].isna().sum()),
        "non_null_rates": {},
    }
    for col in [
        *RAW_META_COLUMNS,
        *EXHIBITION_COUNT_MAP.keys(),
        "artist_exhibition_total_count",
        "artist_exhibition_available_count",
        "artist_meta_available_count",
        "artist_meta_completeness_score",
    ]:
        if col in out.columns:
            stats["non_null_rates"][col] = float(out[col].notna().mean())
    return stats


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Track6 작가 메타 feature 보강 보고서",
        "",
        f"- 생성일: `{summary['created_at']}`",
        f"- 대상 split: `{summary['split_root']}`",
        "- 목적: Group E 작가 변수 실험을 위해 기존 split 멤버십은 유지하고 feature 파일에 작가 메타를 추가",
        "- 원칙: 가격/라벨/출처 컬럼은 feature에 추가하지 않음",
        "",
        "## 1. 추가 컬럼",
        "",
    ]
    for col in summary["added_columns"]:
        lines.append(f"- `{col}`")
    lines += [
        "",
        "## 2. 파일별 보강 결과",
        "",
        "| 파일 | rows | columns before | columns after | join 누락 rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in summary["files"]:
        lines.append(
            f"| `{item['path']}` | `{item['rows']:,}` | `{item['columns_before']}` | "
            f"`{item['columns_after']}` | `{item['missing_join_rows']}` |"
        )
    lines += [
        "",
        "## 3. 해석",
        "",
        "- `artist_meta_*_is_missing`은 값이 비어 있는지 알려주는 결측 flag",
        "- `artist_meta_available_count`는 사용 가능한 작가 메타 개수",
        "- `artist_meta_completeness_score`는 사용 가능한 작가 메타 비율",
        "- `artist_meta_source`는 출처 편향 위험이 있어 feature 파일에는 추가하지 않음",
        "- `artist_meta_for_sale_ratio`, `artist_meta_has_international`, `artist_meta_career_age`는 값 품질 문제가 있어 이번 보강에서 제외",
        "- `artist_exhibition_*_count`는 원본 `saatchi__solo_count/group_count/fair_count`에서 가져온 값",
        "- 전시 횟수 컬럼의 `200` 초과 값은 연도가 잘못 들어간 것으로 보고 결측 처리",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    meta = load_meta_by_row_id()
    file_stats = [augment_feature_file(path, meta) for path in FEATURE_FILES]
    added_columns = [c for c in meta.columns if c != "_track6_row_id"]
    summary = {
        "created_at": date.today().isoformat(),
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "join_key": "_track6_row_id",
        "added_columns": added_columns,
        "excluded_columns": [
            "artist_meta_source",
            "artist_meta_for_sale_ratio",
            "artist_meta_has_international",
            "artist_meta_career_age",
        ],
        "files": file_stats,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(render_report(summary), encoding="utf-8")
    print(OUT_SUMMARY.relative_to(REPO))
    print(OUT_REPORT.relative_to(REPO))


if __name__ == "__main__":
    main()
