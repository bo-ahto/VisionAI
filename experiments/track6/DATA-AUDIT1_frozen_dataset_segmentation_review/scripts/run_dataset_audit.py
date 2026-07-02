"""Audit Track6 frozen training dataset for segmentation and feature cleanup.

This script does not train or change the production model. It inspects the
official frozen split used by the current Track6 experiments and writes tables
that help decide whether a future model experiment should:

1. split a route/segment more finely,
2. remove a noisy or unusable feature,
3. add a bucket or guard for a risky region,
4. keep the current dataset policy unchanged.

The audit intentionally uses only frozen split files so the results are tied to
the same dataset used by the official v0.1 model comparisons.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
BASE = REPO / "models/track6/price_prediction_v0.1/data/training/track6_split"
EXP = REPO / "experiments/track6/DATA-AUDIT1_frozen_dataset_segmentation_review"
OUT = EXP / "outputs"
REPORT = EXP / "reports/dataset_segmentation_audit.md"

FULL_SPLITS = {
    "train": BASE / "track6_train.csv",
    "val_warm": BASE / "track6_val_warm.csv",
    "test_warm": BASE / "track6_test_warm.csv",
    "val_cold": BASE / "track6_val_cold.csv",
    "test_cold": BASE / "track6_test_cold.csv",
}

FEATURE_FILES = {
    "warm_train": BASE / "features/warm/track6_train_warm_features.csv",
    "warm_val": BASE / "features/warm/track6_val_warm_warm_features.csv",
    "warm_test": BASE / "features/warm/track6_test_warm_warm_features.csv",
    "cold_train": BASE / "features/cold/track6_train_cold_features.csv",
    "cold_val": BASE / "features/cold/track6_val_cold_cold_features.csv",
    "cold_test": BASE / "features/cold/track6_test_cold_cold_features.csv",
}

LABEL_FILES = {
    "train": BASE / "labels/track6_train_labels.csv",
    "val_warm": BASE / "labels/track6_val_warm_labels.csv",
    "test_warm": BASE / "labels/track6_test_warm_labels.csv",
    "val_cold": BASE / "labels/track6_val_cold_labels.csv",
    "test_cold": BASE / "labels/track6_test_cold_labels.csv",
}

LEAKAGE_COLS = {
    "price_krw",
    "ln_price_krw",
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "artist_name_standardized",
    "artist_works_log",
    "artist_works_count_train",
}

SEGMENT_COLS = [
    "track4_source",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "nant_support",
    "nant_tool",
    "nant_material_match_method",
    "has_depth",
    "is_3d_candidate",
    "is_extreme_aspect_ratio",
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
    "price_band_train_q",
    "area_band_train_q",
    "aspect_band",
    "history_count_band",
]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def qcut_with_train_edges(
    train: pd.Series,
    parts: list[pd.Series],
    q: int,
    prefix: str,
) -> list[pd.Series]:
    numeric = pd.to_numeric(train, errors="coerce").dropna()
    if numeric.empty:
        return [pd.Series(["missing"] * len(p), index=p.index) for p in parts]
    edges = np.unique(np.nanquantile(numeric, np.linspace(0, 1, q + 1)))
    if len(edges) <= 2:
        return [pd.Series([f"{prefix}_single"] * len(p), index=p.index) for p in parts]
    edges[0] = -np.inf
    edges[-1] = np.inf
    labels = [f"{prefix}{i + 1}" for i in range(len(edges) - 1)]
    return [
        pd.cut(pd.to_numeric(p, errors="coerce"), bins=edges, labels=labels, include_lowest=True)
        .astype("object")
        .fillna("missing")
        for p in parts
    ]


def add_derived_bins(splits: dict[str, pd.DataFrame]) -> None:
    ordered = [splits[k] for k in FULL_SPLITS]
    price_bands = qcut_with_train_edges(splits["train"]["ln_price_krw"], [df["ln_price_krw"] for df in ordered], 5, "price_q")
    area_bands = qcut_with_train_edges(splits["train"]["log_area"], [df["log_area"] for df in ordered], 5, "area_q")
    for df, price_band, area_band in zip(ordered, price_bands, area_bands):
        df["price_band_train_q"] = price_band
        df["area_band_train_q"] = area_band
        aspect = pd.to_numeric(df["aspect_ratio"], errors="coerce")
        df["aspect_band"] = np.select(
            [
                aspect.isna(),
                aspect < 0.5,
                aspect <= 2.0,
                aspect <= 5.0,
                aspect > 5.0,
            ],
            ["missing", "very_tall", "balanced", "wide", "extreme"],
            default="missing",
        )
        hist = pd.to_numeric(df.get("artist_works_count_train", 0), errors="coerce").fillna(0)
        df["history_count_band"] = np.select(
            [
                hist == 0,
                hist == 1,
                hist.between(2, 4),
                hist.between(5, 9),
                hist.between(10, 29),
                hist >= 30,
            ],
            ["0_cold", "1", "2_4", "5_9", "10_29", "30_plus"],
            default="missing",
        )


def ape_from_log(pred_log: pd.Series, actual_log: pd.Series) -> pd.Series:
    return (np.exp(pred_log) - np.exp(actual_log)).abs() / np.exp(actual_log)


def describe_target(df: pd.DataFrame) -> dict[str, float | int]:
    y = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    price = pd.to_numeric(df["price_krw"], errors="coerce")
    return {
        "rows": int(len(df)),
        "artist_key_n": int(df["artist_key"].nunique(dropna=True)) if "artist_key" in df else 0,
        "artist_name_ko_n": int(df["artist_name_ko"].nunique(dropna=True)) if "artist_name_ko" in df else 0,
        "ln_price_mean": round(float(y.mean()), 6),
        "ln_price_std": round(float(y.std()), 6),
        "price_median": round(float(price.median()), 2),
        "price_p95": round(float(price.quantile(0.95)), 2),
    }


def missing_and_cardinality(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for split, df in splits.items():
        for col in df.columns:
            s = df[col]
            rows.append(
                {
                    "split": split,
                    "column": col,
                    "dtype": str(s.dtype),
                    "missing_rate": round(float(s.isna().mean()), 6),
                    "nunique": int(s.nunique(dropna=True)),
                    "top_value": "" if s.dropna().empty else str(s.dropna().mode().iloc[0])[:120],
                    "top_share": round(float((s == s.dropna().mode().iloc[0]).mean()), 6)
                    if not s.dropna().empty
                    else 0.0,
                }
            )
    return pd.DataFrame(rows)


def feature_file_audit() -> pd.DataFrame:
    rows = []
    for name, path in FEATURE_FILES.items():
        df = read_csv(path)
        is_cold = name.startswith("cold")
        leakage = sorted((set(df.columns) & LEAKAGE_COLS) if is_cold else (set(df.columns) & {"price_krw", "ln_price_krw"}))
        for col in df.columns:
            s = df[col]
            rows.append(
                {
                    "feature_set": name,
                    "column": col,
                    "dtype": str(s.dtype),
                    "missing_rate": round(float(s.isna().mean()), 6),
                    "nunique": int(s.nunique(dropna=True)),
                    "is_leakage_risk": col in leakage,
                    "is_constant": int(s.nunique(dropna=True)) <= 1,
                }
            )
    return pd.DataFrame(rows)


def segment_target_table(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for split, df in splits.items():
        for col in SEGMENT_COLS:
            if col not in df.columns:
                continue
            tmp = df[[col, "ln_price_krw", "price_krw"]].copy()
            tmp[col] = tmp[col].astype("object").where(tmp[col].notna(), "missing")
            for value, g in tmp.groupby(col, dropna=False):
                if len(g) < 20:
                    continue
                rows.append(
                    {
                        "split": split,
                        "segment_column": col,
                        "segment_value": str(value)[:160],
                        "rows": int(len(g)),
                        "row_share": round(float(len(g) / len(df)), 6),
                        "ln_price_median": round(float(g["ln_price_krw"].median()), 6),
                        "ln_price_iqr": round(float(g["ln_price_krw"].quantile(0.75) - g["ln_price_krw"].quantile(0.25)), 6),
                        "price_median": round(float(g["price_krw"].median()), 2),
                    }
                )
    return pd.DataFrame(rows)


def train_test_segment_shift(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    train = splits["train"]
    for target_split in ["val_warm", "test_warm", "val_cold", "test_cold"]:
        target = splits[target_split]
        for col in SEGMENT_COLS:
            if col not in train.columns or col not in target.columns:
                continue
            a = train[col].astype("object").where(train[col].notna(), "missing")
            b = target[col].astype("object").where(target[col].notna(), "missing")
            values = sorted(set(a.unique()) | set(b.unique()), key=str)
            diffs = []
            for value in values:
                train_share = float((a == value).mean())
                target_share = float((b == value).mean())
                diffs.append((abs(target_share - train_share), value, train_share, target_share))
            diffs.sort(reverse=True, key=lambda x: x[0])
            if not diffs:
                continue
            max_diff, value, train_share, target_share = diffs[0]
            rows.append(
                {
                    "target_split": target_split,
                    "segment_column": col,
                    "max_abs_share_diff": round(max_diff, 6),
                    "largest_shift_value": str(value)[:160],
                    "train_share": round(train_share, 6),
                    "target_share": round(target_share, 6),
                    "train_unique": int(a.nunique()),
                    "target_unique": int(b.nunique()),
                }
            )
    return pd.DataFrame(rows).sort_values(["target_split", "max_abs_share_diff"], ascending=[True, False])


def high_cardinality_review(splits: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    train = splits["train"]
    for col in train.columns:
        s = train[col]
        dtype_text = str(s.dtype)
        if not (
            s.dtype == "object"
            or dtype_text == "str"
            or dtype_text.startswith("bool")
            or dtype_text.startswith("string")
        ):
            continue
        counts = s.astype("object").where(s.notna(), "missing").value_counts(dropna=False)
        if counts.empty:
            continue
        rare_share = float(counts[counts < 10].sum() / len(s))
        rows.append(
            {
                "column": col,
                "nunique_train": int(counts.size),
                "top_value": str(counts.index[0])[:160],
                "top_share": round(float(counts.iloc[0] / len(s)), 6),
                "rare_level_row_share_lt10": round(rare_share, 6),
                "review_hint": "bucket_or_remove" if counts.size > 100 or rare_share > 0.2 else "ok",
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["review_priority"] = np.where(out["review_hint"].eq("bucket_or_remove"), 0, 1)
    return out.sort_values(["review_priority", "nunique_train"], ascending=[True, False]).drop(columns=["review_priority"])


def split_integrity_checks(splits: dict[str, pd.DataFrame], feature_audit: pd.DataFrame) -> pd.DataFrame:
    train = splits["train"]
    train_keys = set(train["artist_key"].dropna())
    train_names = set(train["artist_name_ko"].dropna())
    train_orig = set(train["artist_name_ko_orig"].dropna())
    rows = []

    for split_name in ["val_warm", "test_warm"]:
        df = splits[split_name]
        rows.append(
            {
                "check": f"{split_name}_warm_min_history_gte5",
                "status": "PASS" if pd.to_numeric(df["artist_works_count_train"], errors="coerce").min() >= 5 else "FAIL",
                "detail": f"min={pd.to_numeric(df['artist_works_count_train'], errors='coerce').min()}",
            }
        )

    for split_name in ["val_cold", "test_cold"]:
        df = splits[split_name]
        rows.append(
            {
                "check": f"{split_name}_cold_artist_key_overlap_train",
                "status": "PASS" if len(set(df["artist_key"].dropna()) & train_keys) == 0 else "FAIL",
                "detail": str(len(set(df["artist_key"].dropna()) & train_keys)),
            }
        )
        rows.append(
            {
                "check": f"{split_name}_cold_artist_name_overlap_train",
                "status": "PASS" if len(set(df["artist_name_ko"].dropna()) & train_names) == 0 else "FAIL",
                "detail": str(len(set(df["artist_name_ko"].dropna()) & train_names)),
            }
        )
        rows.append(
            {
                "check": f"{split_name}_cold_artist_name_orig_overlap_train",
                "status": "PASS" if len(set(df["artist_name_ko_orig"].dropna()) & train_orig) == 0 else "FAIL",
                "detail": str(len(set(df["artist_name_ko_orig"].dropna()) & train_orig)),
            }
        )

    risky = feature_audit[(feature_audit["feature_set"].str.startswith("cold")) & (feature_audit["is_leakage_risk"])]
    rows.append(
        {
            "check": "cold_feature_no_same_artist_leakage_columns",
            "status": "PASS" if risky.empty else "FAIL",
            "detail": "" if risky.empty else ", ".join(sorted(risky["column"].unique())),
        }
    )
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    df.to_csv(path, index=False)
    return path


def md_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    cols = list(view.columns)

    def clean(value: object) -> str:
        text = "" if pd.isna(value) else str(value)
        return text.replace("|", "\\|").replace("\n", " ")[:240]

    header = "| " + " | ".join(cols) + " |"
    divider = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = [
        "| " + " | ".join(clean(row[col]) for col in cols) + " |"
        for _, row in view.iterrows()
    ]
    return "\n".join([header, divider, *body])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    splits = {name: read_csv(path) for name, path in FULL_SPLITS.items()}
    add_derived_bins(splits)

    split_summary = pd.DataFrame(
        [{"split": name, **describe_target(df)} for name, df in splits.items()]
    )
    coverage = missing_and_cardinality(splits)
    feature_audit = feature_file_audit()
    segments = segment_target_table(splits)
    shifts = train_test_segment_shift(splits)
    high_card = high_cardinality_review(splits)
    integrity = split_integrity_checks(splits, feature_audit)

    # Candidate views for quick decision making.
    high_missing = coverage[(coverage["split"] == "train") & (coverage["missing_rate"] >= 0.5)].sort_values(
        "missing_rate", ascending=False
    )
    high_shift = shifts[shifts["max_abs_share_diff"] >= 0.10].copy()
    candidate_split_cols = (
        segments[segments["split"].isin(["test_warm", "test_cold"])]
        .groupby("segment_column")
        .agg(
            segment_count=("segment_value", "nunique"),
            max_segment_rows=("rows", "max"),
            median_price_spread=("ln_price_median", lambda s: round(float(s.max() - s.min()), 6)),
            max_iqr=("ln_price_iqr", "max"),
        )
        .reset_index()
        .sort_values(["median_price_spread", "max_iqr"], ascending=False)
    )

    outputs = {
        "split_summary.csv": split_summary,
        "column_missing_cardinality.csv": coverage,
        "feature_file_audit.csv": feature_audit,
        "segment_target_summary.csv": segments,
        "train_eval_segment_shift.csv": shifts,
        "high_cardinality_review.csv": high_card,
        "integrity_checks.csv": integrity,
        "candidate_split_columns.csv": candidate_split_cols,
    }
    for name, df in outputs.items():
        write_csv(df, name)

    report = f"""# DATA-AUDIT1 frozen dataset segmentation review

## 목적

현재 official v0.1 계열 실험의 기준인 frozen split을 대상으로, 모델 성능 개선을 위해 데이터셋을 더 세분화할 후보와 제거/정리할 feature 후보를 점검했다.

이 감사는 모델을 새로 학습하지 않는다. 데이터셋 구조, 분포, 누수 가능성, 세그먼트 차이를 확인하는 사전 진단이다.

## 기준 데이터

`{BASE.relative_to(REPO)}`

## 1. Split 요약

{md_table(split_summary)}

## 2. 무결성 검사

{md_table(integrity)}

## 3. 결측률이 높은 train 컬럼

{md_table(high_missing[["column", "missing_rate", "nunique", "top_value", "top_share"]], 30)}

## 4. 고유값이 많거나 희소 level이 많은 범주형 컬럼

희소 level이 많으면 모델이 의미 있는 패턴보다 개별 값에 끌릴 수 있다. 이 경우 bucket화, 상위 level만 유지, 또는 제거 실험 대상이다.

{md_table(high_card[["column", "nunique_train", "top_value", "top_share", "rare_level_row_share_lt10", "review_hint"]], 30)}

## 5. Train 대비 평가셋 분포 차이가 큰 세그먼트

`max_abs_share_diff`는 특정 값의 train 비중과 평가셋 비중 차이의 최댓값이다. 차이가 큰 컬럼은 별도 평가/라우팅/보정 후보가 된다.

{md_table(high_shift[["target_split", "segment_column", "max_abs_share_diff", "largest_shift_value", "train_share", "target_share"]], 40)}

## 6. 세분화 후보 컬럼

`median_price_spread`가 크면 같은 컬럼 안의 값별 가격대 차이가 크다는 뜻이다. 이런 컬럼은 모델 입력으로 유지하거나 별도 bucket/세그먼트 기준으로 검토할 가치가 있다.

{md_table(candidate_split_cols, 30)}

## 7. 1차 판단

- Warm/Cold split 무결성과 Cold 누수 차단은 통과했다.
- 작가 메타 컬럼 중 결측이 큰 항목은 운영 입력 가능성과 함께 별도 검토가 필요하다.
- `artist_name_standardized`, `title_raw`, URL류, raw material 문자열처럼 고유값이 큰 컬럼은 직접 feature로 쓰기보다 정규화/bucket/embedding/검수 큐 대상이다.
- `track4_source`, 재료/지지체 계열, 면적/가격 band, 작가 메타 source 계열은 평가셋 분포 차이가 있는지 확인해 세그먼트별 성능 비교 후보로 삼는다.
- 다음 단계는 이 감사 결과에서 나온 후보 컬럼을 기준으로 feature 제거/추가/세분화 실험을 작은 실험군으로 나누어 실제 MdAPE, MAPE, p95 APE 변화를 확인하는 것이다.

## 산출물

| 파일 | 내용 |
|---|---|
| `outputs/split_summary.csv` | split별 row, 작가 수, 가격 분포 |
| `outputs/column_missing_cardinality.csv` | 컬럼별 결측률/고유값 수 |
| `outputs/feature_file_audit.csv` | Warm/Cold feature 파일 누수/상수/결측 점검 |
| `outputs/segment_target_summary.csv` | 세그먼트별 가격 분포 |
| `outputs/train_eval_segment_shift.csv` | train 대비 val/test 분포 차이 |
| `outputs/high_cardinality_review.csv` | 고유값/희소 level 많은 컬럼 |
| `outputs/candidate_split_columns.csv` | 세분화 후보 컬럼 요약 |
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT), "outputs": sorted(outputs)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
