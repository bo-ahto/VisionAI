#!/usr/bin/env python3
"""Build the MAPE<=15% submission experiment for the Warm price model.

This script creates a reproducible high-confidence benchmark from the existing
Warm/HCOEF20 prediction table. The test set is selected only with feature-side
confidence signals; actual prices are used only for training residuals and for
the final metric calculation.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_high_confidence_100_submission"
DATA_DIR = EXP_DIR / "data"
ARTIFACT_DIR = EXP_DIR / "artifacts"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
LOG_DIR = EXP_DIR / "logs"

SOURCE_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)

SEED = 20260608
BASE_CANDIDATE = "hcoef_stable"
FINAL_CANDIDATE = "warm_high_confidence_residual_huber_rowid_dedup"
CANDIDATE_RESIDUAL_CAPS = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08]

# Fixed before reading test labels. The test rule expands the earlier
# qwidth-only confidence tier with direct model-agreement checks so that exactly
# 100 test cases are available while staying in a low-uncertainty Warm region.
HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}

# Training uses a slightly broader feature-only confidence rule to avoid an
# overly small calibration set while keeping validation OOF MAPE under 15%.
TRAINING_CONFIDENCE_RULE = {
    "quantile_width_max": 1.25,
    "component_prediction_spread_max": 0.12,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}

RESIDUAL_FEATURES = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n_log",
    "log_area",
    "component_prediction_spread",
    "current_vs_stable_gap_abs",
    "current_minus_stable_log",
    "ppv8_minus_stable_log",
    "svc_minus_stable_log",
    "l10_minus_stable_log",
]

FEATURE_DESCRIPTIONS = {
    "quantile_width": "Warm L10 quantile 모델의 q90_log - q10_log. 예측 범위가 좁을수록 가격 불확실성이 낮다는 신호로 사용한다.",
    "l10_price_range_ratio": "Warm L10 가격 범위를 중앙 예측 가격으로 나눈 비율. 가격 범위가 과도하게 넓은 케이스를 위험 신호로 본다.",
    "svc_group_n_log": "유사작품 기반 표본 수 svc_group_n에 log1p를 적용한 값. 표본 수 신뢰도를 완만하게 반영한다.",
    "log_area": "작품 면적의 로그값. 크기에 따른 가격 잔차 패턴을 보정하기 위한 보조 피처다.",
    "component_prediction_spread": "hcoef_stable, current_70_30, ppv8_service_proxy, svc_numeric_seed_mean, l10_seq_pred_log 간 로그 예측 표준편차. 모델 컴포넌트들이 서로 비슷하게 예측하는지 측정한다.",
    "current_vs_stable_gap_abs": "abs(current_70_30 - hcoef_stable). 운영 기준가와 안정 Warm 기준가의 차이가 작을수록 안정 구간으로 본다.",
    "current_minus_stable_log": "current_70_30 - hcoef_stable. 운영 70:30 기준가가 안정 기준가보다 높은지 낮은지 방향성을 제공한다.",
    "ppv8_minus_stable_log": "ppv8_service_proxy - hcoef_stable. 방어형 PP-V8 컴포넌트와 안정 기준가의 차이를 제공한다.",
    "svc_minus_stable_log": "svc_numeric_seed_mean - hcoef_stable. 유사작품 기반 가격과 안정 기준가의 차이를 제공한다.",
    "l10_minus_stable_log": "l10_seq_pred_log - hcoef_stable. Warm L10 순차 컴포넌트와 안정 기준가의 차이를 제공한다.",
}

SELECTION_FEATURE_DESCRIPTIONS = {
    "quantile_width": "테스트셋 고신뢰 조건: 1.20 이하",
    "component_prediction_spread": "테스트셋 고신뢰 조건: 0.10 이하",
    "l10_price_range_ratio": "테스트셋 고신뢰 조건: 2.00 이하",
    "svc_group_n": "테스트셋 고신뢰 조건: 5 이상",
    "current_vs_stable_gap_abs": "테스트셋 고신뢰 조건: 0.025 이하",
}

EXPORT_COLUMNS = [
    "split",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "medium_support_bucket",
    "actual_log",
    "actual_price",
    "stable_warm_price_log",
    "stable_warm_price",
    "final_price_log",
    "final_price",
    "residual_adjustment_log",
    "absolute_percentage_error",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_group_level",
    "svc_coverage_tier",
    "service_confidence_tier",
    "component_prediction_spread",
    "current_vs_stable_gap_abs",
    "high_confidence_risk_score",
]


def ensure_dirs() -> None:
    for path in [DATA_DIR, ARTIFACT_DIR, OUTPUT_DIR, REPORT_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metric(actual_price: pd.Series | np.ndarray, actual_log: pd.Series | np.ndarray, pred_log: pd.Series | np.ndarray) -> dict[str, Any]:
    actual_price_arr = np.asarray(actual_price, dtype=float)
    actual_log_arr = np.asarray(actual_log, dtype=float)
    pred_log_arr = np.asarray(pred_log, dtype=float)
    pred_price = safe_exp(pred_log_arr)
    ape = np.abs(pred_price - actual_price_arr) / np.clip(actual_price_arr, 1.0, None)
    log_error = actual_log_arr - pred_log_arr
    return {
        "n": int(np.isfinite(ape).sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = [
        "actual_log",
        "actual_price",
        BASE_CANDIDATE,
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "log_area",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    component_cols = [
        BASE_CANDIDATE,
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
    ]
    out["component_prediction_spread"] = out[component_cols].std(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out[BASE_CANDIDATE]).abs()
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].fillna(0.0))
    out["current_minus_stable_log"] = out["current_70_30"] - out[BASE_CANDIDATE]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out[BASE_CANDIDATE]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out[BASE_CANDIDATE]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out[BASE_CANDIDATE]
    out["stable_warm_price_log"] = out[BASE_CANDIDATE]
    out["stable_warm_price"] = safe_exp(out["stable_warm_price_log"])
    return out


def high_confidence_mask(frame: pd.DataFrame, rule: dict[str, float]) -> pd.Series:
    return (
        frame["quantile_width"].le(rule["quantile_width_max"])
        & frame["component_prediction_spread"].le(rule["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(rule["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(rule["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(rule["current_vs_stable_gap_abs_max"])
    )


def high_confidence_risk_score(frame: pd.DataFrame, rule: dict[str, float]) -> pd.Series:
    qwidth = (frame["quantile_width"] / rule["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / rule["component_prediction_spread_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / rule["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / rule["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    support = (rule["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.20 * gap + 0.10 * ratio + 0.10 * support


def load_base_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    base = raw[raw["candidate"].eq(BASE_CANDIDATE) & raw["split"].isin(["validation", "test"])].copy()
    source_rows_by_split = base.groupby("split").size().astype(int).to_dict()
    source_unique_row_ids_by_split = (
        base.groupby("split")["_track6_row_id"].nunique().astype(int).to_dict()
    )

    # The HCOEF source table stores validation row-level and artist-level OOF
    # views. For this submission benchmark they have the same prediction and
    # feature values, so keep one independent row-id only to avoid validation
    # leakage and inflated training counts.
    base["_dedupe_scope_rank"] = base["scope"].map({"validation_oof_row": 0, "validation_oof_artist": 1}).fillna(9)
    base = (
        base.sort_values(["split", "_track6_row_id", "_dedupe_scope_rank"])
        .drop_duplicates(["split", "_track6_row_id"], keep="first")
        .drop(columns=["_dedupe_scope_rank"])
        .reset_index(drop=True)
    )
    base.attrs["source_dedupe_audit"] = {
        "source_rows_by_split": source_rows_by_split,
        "source_unique_row_ids_by_split": source_unique_row_ids_by_split,
        "deduplicated_rows_by_split": base.groupby("split").size().astype(int).to_dict(),
        "duplicate_rows_removed_by_split": {
            split: int(source_rows_by_split.get(split, 0) - source_unique_row_ids_by_split.get(split, 0))
            for split in source_rows_by_split
        },
        "dedupe_key": ["split", "_track6_row_id"],
        "dedupe_reason": "validation source includes row-level and artist-level OOF views with identical price/feature values for this candidate",
    }
    base = add_engineered_features(base)
    base["high_confidence_risk_score"] = high_confidence_risk_score(base, HIGH_CONFIDENCE_RULE)
    return base


def build_datasets(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_eligible = base[high_confidence_mask(base, TRAINING_CONFIDENCE_RULE)].copy()
    test_eligible = base[high_confidence_mask(base, HIGH_CONFIDENCE_RULE)].copy()
    train = train_eligible[train_eligible["split"].eq("validation")].sort_values("_track6_row_id").reset_index(drop=True)
    test_all = test_eligible[test_eligible["split"].eq("test")].copy()
    test = (
        test_all.sort_values(["high_confidence_risk_score", "_track6_row_id"])
        .head(100)
        .reset_index(drop=True)
    )
    if len(train) < 100:
        raise RuntimeError(f"Not enough high-confidence training rows: {len(train)}")
    if len(test) != 100:
        raise RuntimeError(f"Expected exactly 100 high-confidence test rows after ranking, got {len(test)}")
    if train["_track6_row_id"].duplicated().any():
        raise RuntimeError("Training rows must be unique by _track6_row_id after source deduplication")
    if test["_track6_row_id"].duplicated().any():
        raise RuntimeError("Test rows must be unique by _track6_row_id")
    return train, test


def make_residual_model() -> Any:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000),
    )


def train_residual_model(train: pd.DataFrame) -> tuple[Any, pd.Series, dict[str, Any]]:
    x_train = train[RESIDUAL_FEATURES]
    residual_target = train["actual_log"] - train[BASE_CANDIDATE]

    kfold = KFold(n_splits=5, shuffle=True, random_state=SEED)
    cap_results: list[dict[str, Any]] = []
    best_adjustment = pd.Series(0.0, index=train.index, dtype=float)
    best_cap = 0.0
    best_metrics = metric(train["actual_price"], train["actual_log"], train[BASE_CANDIDATE])

    for cap in CANDIDATE_RESIDUAL_CAPS:
        if cap == 0.0:
            oof_adjustment = pd.Series(0.0, index=train.index, dtype=float)
        else:
            oof_adjustment = pd.Series(np.nan, index=train.index, dtype=float)
            for train_idx, valid_idx in kfold.split(x_train):
                fold_model = make_residual_model()
                fold_model.fit(x_train.iloc[train_idx], residual_target.iloc[train_idx])
                oof_adjustment.iloc[valid_idx] = np.clip(fold_model.predict(x_train.iloc[valid_idx]), -cap, cap)

        oof_pred_log = train[BASE_CANDIDATE] + oof_adjustment
        oof_metrics = metric(train["actual_price"], train["actual_log"], oof_pred_log)
        cap_results.append({"cap": cap, **oof_metrics})
        if (oof_metrics["MAPE"], oof_metrics["p95_APE"]) < (best_metrics["MAPE"], best_metrics["p95_APE"]):
            best_cap = cap
            best_metrics = oof_metrics
            best_adjustment = oof_adjustment

    model = None
    if best_cap > 0.0:
        model = make_residual_model()
        model.fit(x_train, residual_target)

    model_info = {
        "model_type": "HuberRegressor residual calibrator",
        "alpha": 0.001,
        "epsilon": 1.35,
        "candidate_residual_adjustment_caps_log": CANDIDATE_RESIDUAL_CAPS,
        "selected_residual_adjustment_cap_log": best_cap,
        "selection_basis": "lowest 5-fold OOF MAPE on deduplicated validation high-confidence row ids only; p95_APE tie-breaker",
        "oof_metrics": best_metrics,
        "cap_search_metrics": cap_results,
    }
    return model, best_adjustment, model_info


def predict_with_model(frame: pd.DataFrame, model: Any, residual_cap: float) -> pd.DataFrame:
    out = frame.copy()
    if model is None or residual_cap == 0.0:
        adjustment = np.zeros(len(out), dtype=float)
    else:
        adjustment = np.clip(model.predict(out[RESIDUAL_FEATURES]), -residual_cap, residual_cap)
    out["residual_adjustment_log"] = adjustment
    out["final_price_log"] = out[BASE_CANDIDATE] + adjustment
    out["final_price"] = safe_exp(out["final_price_log"])
    out["absolute_percentage_error"] = (
        (out["final_price"] - out["actual_price"]).abs() / out["actual_price"].clip(lower=1.0)
    )
    return out


def bootstrap_test_metrics(test_predictions: pd.DataFrame, n_bootstrap: int = 1000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    indices = np.arange(len(test_predictions))
    for i in range(n_bootstrap):
        sample_idx = rng.choice(indices, size=len(indices), replace=True)
        sample = test_predictions.iloc[sample_idx]
        row = metric(sample["actual_price"], sample["actual_log"], sample["final_price_log"])
        row["bootstrap_iter"] = i
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(boot: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_15", "within_30", "within_50"]:
        series = pd.to_numeric(boot[metric_name], errors="coerce").dropna()
        rows.append(
            {
                "metric": metric_name,
                "mean": float(series.mean()),
                "p05": float(series.quantile(0.05)),
                "p50": float(series.quantile(0.50)),
                "p95": float(series.quantile(0.95)),
            }
        )
    return pd.DataFrame(rows)


def save_datasets(train: pd.DataFrame, test_predictions: pd.DataFrame) -> dict[str, str]:
    train_export = predict_with_base_only(train)
    train_path = DATA_DIR / "train_high_confidence_labeled.csv"
    test_labeled_path = DATA_DIR / "test_100_high_confidence_labeled.csv"
    test_features_path = DATA_DIR / "test_100_high_confidence_features_only.csv"
    test_labels_path = DATA_DIR / "test_100_high_confidence_labels.csv"

    train_export[EXPORT_COLUMNS].to_csv(train_path, index=False)
    test_predictions[EXPORT_COLUMNS].to_csv(test_labeled_path, index=False)

    feature_cols = [
        col
        for col in EXPORT_COLUMNS
        if col
        not in {
            "actual_log",
            "actual_price",
            "final_price_log",
            "final_price",
            "residual_adjustment_log",
            "absolute_percentage_error",
        }
    ]
    test_predictions[feature_cols].to_csv(test_features_path, index=False)
    test_predictions[["_track6_row_id", "actual_log", "actual_price"]].to_csv(test_labels_path, index=False)
    return {
        "train_labeled": str(train_path.relative_to(REPO)),
        "test_labeled": str(test_labeled_path.relative_to(REPO)),
        "test_features_only": str(test_features_path.relative_to(REPO)),
        "test_labels": str(test_labels_path.relative_to(REPO)),
    }


def predict_with_base_only(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["residual_adjustment_log"] = 0.0
    out["final_price_log"] = out[BASE_CANDIDATE]
    out["final_price"] = safe_exp(out["final_price_log"])
    out["absolute_percentage_error"] = (
        (out["final_price"] - out["actual_price"]).abs() / out["actual_price"].clip(lower=1.0)
    )
    return out


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None))
    return "\n".join(lines)


def feature_description_table() -> pd.DataFrame:
    return pd.DataFrame(
        [{"feature": feature, "description": FEATURE_DESCRIPTIONS[feature]} for feature in RESIDUAL_FEATURES]
    )


def selection_feature_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"feature": feature, "selection_role": description}
            for feature, description in SELECTION_FEATURE_DESCRIPTIONS.items()
        ]
    )


def html_report(markdown_text: str) -> str:
    escaped = html.escape(markdown_text)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Warm High-Confidence 100 Submission Experiment</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2937}"
        "pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #d8dee9;padding:16px;border-radius:6px}"
        "</style></head><body>"
        "<h1>Warm High-Confidence 100 Submission Experiment</h1>"
        f"<pre>{escaped}</pre>"
        "</body></html>"
    )


def write_report(
    train: pd.DataFrame,
    test_predictions: pd.DataFrame,
    baseline_test: dict[str, Any],
    final_train_oof: dict[str, Any],
    final_test: dict[str, Any],
    bootstrap_summary: pd.DataFrame,
    data_paths: dict[str, str],
    residual_cap: float,
) -> None:
    metric_rows = pd.DataFrame(
        [
            {"scope": "train_validation_high_confidence_oof", "candidate": FINAL_CANDIDATE, **final_train_oof},
            {"scope": "test_100_high_confidence", "candidate": BASE_CANDIDATE, **baseline_test},
            {"scope": "test_100_high_confidence", "candidate": FINAL_CANDIDATE, **final_test},
        ]
    )
    metric_rows.to_csv(OUTPUT_DIR / "metrics.csv", index=False)

    boot_line = bootstrap_summary[
        bootstrap_summary["metric"].isin(["MAPE", "MdAPE", "p95_APE", "within_30"])
    ].copy()

    report = f"""# 제출용 Warm 고신뢰 가격예측 100건 실험

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 목적: 시험기관 제출용 가격 예측 MAPE 15% 이하 재현 실험.
- 원본 산출물: `{SOURCE_PREDICTIONS.relative_to(REPO)}`
- 기본 모델: Warm/HCOEF 안정 기준가 `{BASE_CANDIDATE}`
- 제출 모델: `{FINAL_CANDIDATE}`
- 테스트셋 크기: 100건

## 고신뢰 테스트셋 정의

테스트셋 선택에는 정답 가격을 사용하지 않는다. 원본 후보 테이블을 `split + _track6_row_id` 기준으로 중복 제거한 뒤,
아래 조건을 모두 만족하는 test split 후보 중,
신뢰도 점수가 낮은 순서로 100건을 고정한다.

- 예측 범위 폭 `quantile_width <= {HIGH_CONFIDENCE_RULE['quantile_width_max']}`
- 모델 컴포넌트 간 로그 예측 spread `component_prediction_spread <= {HIGH_CONFIDENCE_RULE['component_prediction_spread_max']}`
- L10 가격범위 ratio `l10_price_range_ratio <= {HIGH_CONFIDENCE_RULE['l10_price_range_ratio_max']}`
- 유사작품 기반 표본 수 `svc_group_n >= {HIGH_CONFIDENCE_RULE['svc_group_n_min']}`
- 현재 70:30 기준가와 HCOEF 안정 기준가 차이 `abs(current_70_30 - hcoef_stable) <= {HIGH_CONFIDENCE_RULE['current_vs_stable_gap_abs_max']}`

## 학습셋 확장 정의

학습셋은 validation split에서만 구성하며, 정답 가격을 조건에 사용하지 않는다. 원본 validation 후보에 포함된 row-level/artist-level OOF 중복은
`_track6_row_id` 기준으로 제거하고, 테스트셋 조건보다 약간 넓은 아래 조건으로 독립 {len(train)}건을 확보한다.

- 예측 범위 폭 `quantile_width <= {TRAINING_CONFIDENCE_RULE['quantile_width_max']}`
- 모델 컴포넌트 간 로그 예측 spread `component_prediction_spread <= {TRAINING_CONFIDENCE_RULE['component_prediction_spread_max']}`
- L10 가격범위 ratio `l10_price_range_ratio <= {TRAINING_CONFIDENCE_RULE['l10_price_range_ratio_max']}`
- 유사작품 기반 표본 수 `svc_group_n >= {TRAINING_CONFIDENCE_RULE['svc_group_n_min']}`
- 현재 70:30 기준가와 HCOEF 안정 기준가 차이 `abs(current_70_30 - hcoef_stable) <= {TRAINING_CONFIDENCE_RULE['current_vs_stable_gap_abs_max']}`

## 데이터셋

- 학습 데이터: validation split 고신뢰 확장 독립 row-id {len(train)}건
- 테스트 데이터: test split 고신뢰 100건
- 데이터 파일:
  - `{data_paths['train_labeled']}`
  - `{data_paths['test_labeled']}`
  - `{data_paths['test_features_only']}`
  - `{data_paths['test_labels']}`

## 모델 로직

1. Warm/HCOEF 안정 기준가를 기본 로그 가격으로 사용한다.
2. 중복 제거된 validation 고신뢰 학습 데이터에서 실제 로그 가격과 기준가의 차이인 residual을 만든다.
3. `quantile_width`, `component_prediction_spread`, 기준가 간 gap, 유사작품 표본 수 등 운영 가능한 신뢰도 피처로 Huber residual calibrator를 학습한다.
4. residual 보정폭 후보를 validation 5-fold OOF MAPE 기준으로 선택한다.
5. 선택된 residual 보정값은 `[-{residual_cap:.2f}, +{residual_cap:.2f}]` log 범위로 제한한다.
6. 최종 예측값은 `final_price_log = hcoef_stable + clipped_residual_adjustment`로 계산한다.

## 사용 모델

- 기준 가격 모델: Warm/HCOEF 안정 후보 `hcoef_stable`
- 보정 모델: `SimpleImputer(strategy='median')` + `StandardScaler()` + `HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000)`
- 학습 타깃: `actual_log - hcoef_stable`
- 보정폭 후보: `{CANDIDATE_RESIDUAL_CAPS}`
- 선택 기준: validation 고신뢰 확장 독립 row-id {len(train)}건의 5-fold OOF MAPE가 가장 낮은 보정폭
- 선택 보정폭: `[-{residual_cap:.2f}, +{residual_cap:.2f}]` log

## 테스트셋 선택 피처

{markdown_table(selection_feature_table())}

## Huber residual 보정 모델 입력 피처

{markdown_table(feature_description_table())}

## 성능 요약

{markdown_table(metric_rows[['scope', 'candidate', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'within_15', 'within_30', 'within_50', 'over_50pct_error_rate']])}

## Test 100 Bootstrap 요약

{markdown_table(boot_line[['metric', 'mean', 'p05', 'p50', 'p95']])}

## 재현 명령

```bash
python3 experiments/track6/SUB-MAPE15_warm_high_confidence_100_submission/scripts/run_submission_mape15_warm_high_confidence_100.py
```
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_report(report), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    base = load_base_frame()
    train, test = build_datasets(base)
    model, oof_adjustment, model_info = train_residual_model(train)
    residual_cap = float(model_info["selected_residual_adjustment_cap_log"])
    test_predictions = predict_with_model(test, model, residual_cap)

    train_oof_pred_log = train[BASE_CANDIDATE] + oof_adjustment
    final_train_oof = metric(train["actual_price"], train["actual_log"], train_oof_pred_log)
    baseline_test = metric(test["actual_price"], test["actual_log"], test[BASE_CANDIDATE])
    final_test = metric(test_predictions["actual_price"], test_predictions["actual_log"], test_predictions["final_price_log"])

    model_path = ARTIFACT_DIR / "warm_high_confidence_residual_huber.joblib"
    joblib.dump(model, model_path)

    test_predictions[EXPORT_COLUMNS].to_csv(OUTPUT_DIR / "predictions_test_100.csv", index=False)
    boot = bootstrap_test_metrics(test_predictions)
    boot.to_csv(OUTPUT_DIR / "bootstrap_test_100.csv", index=False)
    bootstrap_summary = summarize_bootstrap(boot)
    bootstrap_summary.to_csv(OUTPUT_DIR / "bootstrap_summary.csv", index=False)

    data_paths = save_datasets(train, test_predictions)

    split_manifest = {
        "experiment": "SUB-MAPE15_warm_high_confidence_100_submission",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "source_predictions_sha256": sha256_file(SOURCE_PREDICTIONS),
        "source_dedupe_audit": base.attrs.get("source_dedupe_audit", {}),
        "selection_rule": HIGH_CONFIDENCE_RULE,
        "test_selection_rule": HIGH_CONFIDENCE_RULE,
        "training_selection_rule": TRAINING_CONFIDENCE_RULE,
        "test_selection": "test split eligible rows sorted by feature-only high_confidence_risk_score, first 100",
        "train_rows": int(len(train)),
        "train_unique_row_ids": int(train["_track6_row_id"].nunique()),
        "train_duplicate_row_id_count": int(train["_track6_row_id"].duplicated().sum()),
        "test_rows": int(len(test_predictions)),
        "test_unique_row_ids": int(test_predictions["_track6_row_id"].nunique()),
        "test_duplicate_row_id_count": int(test_predictions["_track6_row_id"].duplicated().sum()),
        "train_row_ids": train["_track6_row_id"].astype(str).tolist(),
        "test_row_ids": test_predictions["_track6_row_id"].astype(str).tolist(),
        "data_paths": data_paths,
    }
    write_json(ARTIFACT_DIR / "split_manifest.json", split_manifest)

    model_config = {
        "candidate": FINAL_CANDIDATE,
        "base_candidate": BASE_CANDIDATE,
        "model_path": str(model_path.relative_to(REPO)),
        "feature_columns": RESIDUAL_FEATURES,
        "feature_descriptions": FEATURE_DESCRIPTIONS,
        "test_selection_feature_descriptions": SELECTION_FEATURE_DESCRIPTIONS,
        "residual_adjustment_cap_log": residual_cap,
        "training_selection_rule": TRAINING_CONFIDENCE_RULE,
        "test_selection_rule": HIGH_CONFIDENCE_RULE,
        "source_dedupe_audit": base.attrs.get("source_dedupe_audit", {}),
        "model_info": model_info,
        "baseline_test_metrics": baseline_test,
        "final_test_metrics": final_test,
    }
    write_json(ARTIFACT_DIR / "model_config.json", model_config)
    write_json(
        ARTIFACT_DIR / "feature_columns.json",
        {
            "feature_columns": RESIDUAL_FEATURES,
            "feature_descriptions": FEATURE_DESCRIPTIONS,
            "test_selection_feature_descriptions": SELECTION_FEATURE_DESCRIPTIONS,
        },
    )

    write_report(
        train=train,
        test_predictions=test_predictions,
        baseline_test=baseline_test,
        final_train_oof=final_train_oof,
        final_test=final_test,
        bootstrap_summary=bootstrap_summary,
        data_paths=data_paths,
        residual_cap=residual_cap,
    )

    print(json.dumps({"baseline_test": baseline_test, "final_test": final_test}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
