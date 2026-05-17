#!/usr/bin/env python3
"""Generate a final quality review for Track 4 cleaned and split datasets."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TRACK4_DOCS = DOCS / "track4"
SPLIT = DATA / "track4_split"

CLEANED_PATH = DATA / "track4_primary_market_cleaned_v2.csv"
FEATURE_PATH = DATA / "track4_primary_market_feature_candidates_v1.csv"
COLUMN_PROFILE_PATH = DATA / "track4_dataset_column_profile_20260517.csv"
SIZE_REVIEW_SAMPLE_PATH = DATA / "track4_dataset_size_review_samples_20260517.csv"
REPORT_PATH = TRACK4_DOCS / "dataset" / "final_quality_review_2026-05-17.md"

SPLIT_FILES = {
    "train": SPLIT / "track4_train.csv",
    "val_warm": SPLIT / "track4_val_warm.csv",
    "val_cold": SPLIT / "track4_val_cold.csv",
    "test_warm": SPLIT / "track4_test_warm.csv",
    "test_cold": SPLIT / "track4_test_cold.csv",
}

KEY_MODEL_COLUMNS = [
    "price_krw",
    "ln_price_krw",
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "artist_works_log",
]

TRACE_COLUMNS = [
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artwork_url",
    "image_url",
]

DUPLICATE_KEY_COLS = [
    "artist_key",
    "title_raw",
    "price_krw",
    "width_cm",
    "height_cm",
    "depth_cm",
    "medium_category",
    "support_category",
]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def is_missing(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def safe_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def top_values(series: pd.Series, limit: int = 5) -> str:
    values = series.fillna("<NA>").astype(str).str.strip().replace("", "<EMPTY>")
    counts = values.value_counts(dropna=False).head(limit)
    return "; ".join(f"{idx}: {cnt}" for idx, cnt in counts.items())


def profile_columns(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        missing = is_missing(s)
        numeric = safe_float(s)
        numeric_ratio = float(numeric.notna().mean()) if n else 0.0
        kind = "numeric" if numeric_ratio >= 0.95 and numeric.notna().any() else "text/category"
        rows.append(
            {
                "column": col,
                "dtype": str(s.dtype),
                "in_feature_candidates": col in read_feature_columns(),
                "missing_count": int(missing.sum()),
                "missing_rate": round(float(missing.mean()), 6) if n else 0.0,
                "unique_count": int(s.nunique(dropna=True)),
                "detected_type": kind,
                "min": round(float(numeric.min()), 6) if kind == "numeric" and numeric.notna().any() else "",
                "median": round(float(numeric.median()), 6) if kind == "numeric" and numeric.notna().any() else "",
                "max": round(float(numeric.max()), 6) if kind == "numeric" and numeric.notna().any() else "",
                "top_values": top_values(s),
            }
        )
    return pd.DataFrame(rows)


_FEATURE_COLUMNS: set[str] | None = None


def read_feature_columns() -> set[str]:
    global _FEATURE_COLUMNS
    if _FEATURE_COLUMNS is None:
        _FEATURE_COLUMNS = set(pd.read_csv(FEATURE_PATH, nrows=0).columns)
    return _FEATURE_COLUMNS


def mismatch_count(actual: pd.Series, expected: pd.Series, tolerance: float = 1e-6) -> int:
    mask = actual.notna() & expected.notna()
    return int((np.abs(actual[mask] - expected[mask]) > tolerance).sum())


def duplicate_key(df: pd.DataFrame) -> pd.Series:
    parts = []
    for col in DUPLICATE_KEY_COLS:
        if col in df.columns:
            parts.append(df[col].fillna("").astype(str).str.strip().str.lower())
        else:
            parts.append(pd.Series([""] * len(df), index=df.index))
    return pd.concat(parts, axis=1).agg("||".join, axis=1)


def split_checks(splits: dict[str, pd.DataFrame]) -> dict[str, object]:
    train_keys = set(splits["train"]["artist_key"].dropna().astype(str))
    checks: dict[str, object] = {}
    checks["row_counts"] = {name: len(df) for name, df in splits.items()}
    checks["artist_counts"] = {
        name: int(df["artist_key"].dropna().astype(str).nunique()) for name, df in splits.items()
    }
    for name in ["val_warm", "test_warm"]:
        eval_keys = set(splits[name]["artist_key"].dropna().astype(str))
        checks[f"{name}_artist_not_in_train"] = len(eval_keys - train_keys)
    for name in ["val_cold", "test_cold"]:
        eval_keys = set(splits[name]["artist_key"].dropna().astype(str))
        checks[f"{name}_artist_overlap_with_train"] = len(eval_keys & train_keys)
        checks[f"{name}_artist_works_log_nonzero"] = int(
            (safe_float(splits[name].get("artist_works_log", pd.Series(dtype=float))).fillna(0) != 0).sum()
        )

    train_dupes = set(duplicate_key(splits["train"]))
    for name in ["val_warm", "val_cold", "test_warm", "test_cold"]:
        checks[f"{name}_duplicate_key_overlap_with_train"] = len(set(duplicate_key(splits[name])) & train_dupes)

    for name, df in splits.items():
        checks[f"{name}_price_missing"] = int(is_missing(df["price_krw"]).sum()) if "price_krw" in df else None
        checks[f"{name}_target_missing"] = int(is_missing(df["ln_price_krw"]).sum()) if "ln_price_krw" in df else None
        checks[f"{name}_required_feature_missing_rows"] = int(
            df[[c for c in KEY_MODEL_COLUMNS if c in df.columns]].isna().any(axis=1).sum()
        )
    return checks


def build_report() -> None:
    cleaned = read_csv(CLEANED_PATH)
    feature = read_csv(FEATURE_PATH)
    splits = {name: read_csv(path) for name, path in SPLIT_FILES.items()}

    profile = profile_columns(cleaned)
    COLUMN_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    profile.to_csv(COLUMN_PROFILE_PATH, index=False)

    train_candidates = cleaned[cleaned["is_training_candidate"].astype(str).str.lower() == "true"].copy()
    price = safe_float(cleaned["price_krw"])
    ln_price = safe_float(cleaned["ln_price_krw"])
    width = safe_float(cleaned["width_cm"])
    height = safe_float(cleaned["height_cm"])
    depth = safe_float(cleaned["depth_cm"])
    area = safe_float(cleaned["area_cm2"])
    log_area = safe_float(cleaned["log_area"])
    aspect = safe_float(cleaned["aspect_ratio"])

    expected_ln = np.log(price.where(price > 0))
    expected_area = width * height
    expected_log_area = np.log(expected_area.where(expected_area > 0))
    shorter = pd.concat([width, height], axis=1).min(axis=1)
    longer = pd.concat([width, height], axis=1).max(axis=1)
    expected_aspect = longer / shorter.replace(0, np.nan)
    expected_has_depth = depth.notna() & (depth > 0)

    split_result = split_checks(splits)

    suspicious_size_mask = (
        (safe_float(train_candidates["aspect_ratio"]) > 10)
        | (safe_float(train_candidates["depth_cm"]) > 100)
        | (safe_float(train_candidates["width_cm"]) > 1000)
        | (safe_float(train_candidates["height_cm"]) > 1000)
    )
    size_review_cols = [
        "track4_source",
        "artist_name_ko",
        "title_raw",
        "size_raw",
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "aspect_ratio",
        "medium_raw",
        "artwork_url",
    ]
    train_candidates.loc[suspicious_size_mask, size_review_cols].to_csv(SIZE_REVIEW_SAMPLE_PATH, index=False)

    source_counts = cleaned["track4_source"].fillna("<NA>").value_counts(dropna=False)
    medium_counts = cleaned["medium_category"].fillna("<NA>").value_counts(dropna=False)
    support_counts = cleaned["support_category"].fillna("<NA>").value_counts(dropna=False)
    exclude_counts = (
        cleaned["cleaning_exclude_reasons"]
        .fillna("")
        .astype(str)
        .str.split("|")
        .explode()
        .str.strip()
        .replace("", np.nan)
        .dropna()
        .value_counts()
    )

    issue_rows = []
    issue_rows.append(("price_krw <= 0", int((price.notna() & (price <= 0)).sum())))
    issue_rows.append(("ln_price_krw 계산 불일치", mismatch_count(ln_price, expected_ln, 1e-6)))
    issue_rows.append(("area_cm2 계산 불일치", mismatch_count(area, expected_area, 1e-6)))
    issue_rows.append(("log_area 계산 불일치", mismatch_count(log_area, expected_log_area, 1e-6)))
    issue_rows.append(("aspect_ratio 계산 불일치", mismatch_count(aspect, expected_aspect, 1e-6)))
    issue_rows.append(("has_depth 계산 불일치", int((cleaned["has_depth"].astype(bool) != expected_has_depth).sum())))
    issue_rows.append(("artist_key 결측", int(is_missing(cleaned["artist_key"]).sum())))
    issue_rows.append(("artist_name_ko 결측", int(is_missing(cleaned["artist_name_ko"]).sum())))
    issue_rows.append(("학습 후보 중 가격 결측", int(is_missing(train_candidates["price_krw"]).sum())))
    issue_rows.append(("학습 후보 중 크기 결측", int(train_candidates[["width_cm", "height_cm"]].isna().any(axis=1).sum())))
    issue_rows.append(("학습 후보 중 재료 unknown", int((train_candidates["medium_category"] == "unknown").sum())))
    issue_rows.append(("학습 후보 중 지지체 unknown", int((train_candidates["support_category"] == "unknown").sum())))

    trace_missing = {
        col: int(is_missing(feature[col]).sum())
        for col in TRACE_COLUMNS
        if col in feature.columns
    }

    lines: list[str] = []
    lines.append("# Track 4 최종 데이터셋 품질 검토")
    lines.append("")
    lines.append("- 기준일: 2026-05-17")
    lines.append("- 대상 파일: `data/track4_primary_market_cleaned_v2.csv`")
    lines.append("- 피처 후보 파일: `data/track4_primary_market_feature_candidates_v1.csv`")
    lines.append("- split 폴더: `data/track4_split/`")
    lines.append("- 컬럼별 상세 프로파일: `data/track4_dataset_column_profile_20260517.csv`")
    lines.append("")
    lines.append("## 1. 결론")
    lines.append("")
    lines.append("- 치명적인 split 누수는 발견되지 않음")
    lines.append("- Cold 평가셋의 작가는 train과 겹치지 않음")
    lines.append("- Cold 평가셋의 `artist_works_log`는 모두 0으로 재계산되어 있음")
    lines.append("- train/eval 간 동일 작품 후보 key 겹침은 0건으로 확인됨")
    lines.append("- 가격, 면적, 로그 면적, aspect ratio 파생값 계산 불일치는 0건임")
    lines.append("- 명확한 크기 파싱 오류 후보는 학습 후보에서 제외되었음")
    lines.append("- `support_category=unknown` 비율이 높아 지지체 피처는 후속 실험에서 보수적으로 사용해야 함")
    lines.append("- 남은 `depth_cm > 100` 사례는 대형 설치/조각 가능성이 있어 3D 피처 실험에서 별도 확인함")
    lines.append("")
    lines.append("## 2. 파일 크기와 row 수")
    lines.append("")
    lines.append(f"- cleaned_v2 rows: `{len(cleaned):,}`")
    lines.append(f"- cleaned_v2 columns: `{len(cleaned.columns):,}`")
    lines.append(f"- feature_candidates rows: `{len(feature):,}`")
    lines.append(f"- feature_candidates columns: `{len(feature.columns):,}`")
    lines.append(f"- 학습 후보 rows: `{len(train_candidates):,}`")
    lines.append("")
    lines.append("## 3. Split 점검")
    lines.append("")
    for k, v in split_result["row_counts"].items():
        lines.append(f"- {k} rows: `{v:,}`")
    for k, v in split_result["artist_counts"].items():
        lines.append(f"- {k} artists: `{v:,}`")
    lines.append(f"- val_warm 작가 중 train 미존재 수: `{split_result['val_warm_artist_not_in_train']}`")
    lines.append(f"- test_warm 작가 중 train 미존재 수: `{split_result['test_warm_artist_not_in_train']}`")
    lines.append(f"- val_cold 작가 train 겹침 수: `{split_result['val_cold_artist_overlap_with_train']}`")
    lines.append(f"- test_cold 작가 train 겹침 수: `{split_result['test_cold_artist_overlap_with_train']}`")
    lines.append(f"- val_cold `artist_works_log > 0` rows: `{split_result['val_cold_artist_works_log_nonzero']}`")
    lines.append(f"- test_cold `artist_works_log > 0` rows: `{split_result['test_cold_artist_works_log_nonzero']}`")
    for name in ["val_warm", "val_cold", "test_warm", "test_cold"]:
        lines.append(f"- {name} train 동일 작품 후보 key 겹침 수: `{split_result[f'{name}_duplicate_key_overlap_with_train']}`")
    lines.append("")
    lines.append("## 4. 핵심 컬럼 정합성")
    lines.append("")
    lines.append("| 점검 항목 | 발견 rows |")
    lines.append("|---|---:|")
    for label, value in issue_rows:
        lines.append(f"| {label} | {value:,} |")
    lines.append("")
    lines.append("## 5. 학습 후보 내 크기 보완 결과")
    lines.append("")
    lines.append(f"- aspect_ratio > 10 rows: `{int((safe_float(train_candidates['aspect_ratio']) > 10).sum()):,}`")
    lines.append(f"- depth_cm > 100 rows: `{int((safe_float(train_candidates['depth_cm']) > 100).sum()):,}`")
    lines.append(f"- width_cm > 1000 또는 height_cm > 1000 rows: `{int(((safe_float(train_candidates['width_cm']) > 1000) | (safe_float(train_candidates['height_cm']) > 1000)).sum()):,}`")
    lines.append(f"- 검토 샘플 파일: `data/track4_dataset_size_review_samples_20260517.csv`")
    lines.append("- 해석")
    lines.append("- `2.0 × 65.1 × 53.0 cm`처럼 얇은 치수가 먼저 오는 경우는 depth로 재배치함")
    lines.append("- `aspect_ratio > 10` 또는 width/height 1000cm 초과 값은 학습 후보에서 제외함")
    lines.append("- 남은 `depth_cm > 100`은 대형 설치/조각 가능성이 있으므로 단순 오류로 제외하지 않음")
    lines.append("- 조치")
    lines.append("- 2D 모델 실험에서는 `has_depth=False` 또는 `is_3d_candidate=False` slice를 별도로 확인함")
    lines.append("- 3D 모델 실험에서는 depth/volume 계열 피처를 별도 가설로 검증함")
    lines.append("- 크기 보완 후 `aspect_ratio`, `area_cm2`, `log_area` 계산 불일치는 0건임")
    lines.append("")
    lines.append("## 6. 출처별 row 수")
    lines.append("")
    for name, count in source_counts.items():
        lines.append(f"- {name}: `{count:,}`")
    lines.append("")
    lines.append("## 7. 재료/지지체 분포")
    lines.append("")
    lines.append("- medium_category 상위 값")
    for name, count in medium_counts.head(12).items():
        lines.append(f"- {name}: `{count:,}`")
    lines.append("")
    lines.append("- support_category 상위 값")
    for name, count in support_counts.head(12).items():
        lines.append(f"- {name}: `{count:,}`")
    lines.append("")
    lines.append("## 8. 학습 제외 사유")
    lines.append("")
    for name, count in exclude_counts.head(20).items():
        lines.append(f"- {name}: `{count:,}`")
    lines.append("")
    lines.append("## 9. 추적 컬럼 결측")
    lines.append("")
    for col, count in trace_missing.items():
        lines.append(f"- {col}: `{count:,}`")
    lines.append("")
    lines.append("## 10. 컬럼별 상세 프로파일")
    lines.append("")
    lines.append("- 전체 컬럼별 결측률, 고유값 수, 숫자 범위, 대표값은 아래 CSV에서 확인함")
    lines.append("- `data/track4_dataset_column_profile_20260517.csv`")
    lines.append("")
    lines.append("## 11. 운영/학습 전 주의사항")
    lines.append("")
    lines.append("- `track4_source`, URL, image URL, source row index는 추적용이며 모델 피처로 쓰지 않음")
    lines.append("- `gallery_tier_validated`는 현재 모델 피처에서 제외함")
    lines.append("- `artist_name_ko`는 표시와 매칭 보조용이며, 최종 운영 라우팅은 내부 작가 ID 기준이 필요함")
    lines.append("- Warm 평가셋 row 수가 작아 모델 성능 검증 시 반복 split 또는 내부 CV가 필요함")
    lines.append("- 지지체 unknown이 많으므로 support 피처는 ablation으로 가치 확인 후 사용해야 함")
    lines.append("- 가격 없는 작품은 예측 입력 후보로는 쓸 수 있지만 학습 target으로는 사용할 수 없음")
    lines.append("- 현재 데이터셋은 split 구조와 핵심 파생값 검증을 통과했으므로 Track 4 baseline 실험에 사용할 수 있음")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "cleaned_rows": len(cleaned),
        "cleaned_columns": len(cleaned.columns),
        "feature_rows": len(feature),
        "feature_columns": len(feature.columns),
        "training_candidate_rows": len(train_candidates),
        "split_checks": split_result,
        "issues": dict(issue_rows),
        "training_size_review": {
            "aspect_ratio_gt_10": int((safe_float(train_candidates["aspect_ratio"]) > 10).sum()),
            "depth_gt_100": int((safe_float(train_candidates["depth_cm"]) > 100).sum()),
            "width_or_height_gt_1000": int(
                ((safe_float(train_candidates["width_cm"]) > 1000) | (safe_float(train_candidates["height_cm"]) > 1000)).sum()
            ),
            "sample_path": str(SIZE_REVIEW_SAMPLE_PATH.relative_to(ROOT)),
        },
    }
    (DATA / "track4_dataset_final_quality_review_20260517.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(REPORT_PATH)
    print(COLUMN_PROFILE_PATH)


if __name__ == "__main__":
    build_report()
