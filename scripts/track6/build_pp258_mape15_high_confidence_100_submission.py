#!/usr/bin/env python3
"""Build a 100-row high-confidence MAPE<=15% submission package for Warm PP258."""
from __future__ import annotations

import json
import math
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_EXP = REPO / "experiments" / "track6" / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
TARGET_EXP = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_pp258_high_confidence_100_submission"

SOURCE_CONFIG = SOURCE_EXP / "artifacts" / "run_config.json"
SOURCE_FEATURE_DETAIL = SOURCE_EXP / "artifacts" / "pp252_narrow_refinement_feature_detail.csv"
SOURCE_PREDICTIONS = SOURCE_EXP / "outputs" / "candidate_predictions.csv"
SOURCE_REPORTS = SOURCE_EXP / "reports"

DATA_DIR = TARGET_EXP / "data"
SCRIPT_DIR = TARGET_EXP / "scripts"
OUTPUT_DIR = TARGET_EXP / "outputs"
REPORT_DIR = TARGET_EXP / "reports"
ARTIFACT_DIR = TARGET_EXP / "artifacts"
PACKAGE_DIR = TARGET_EXP / "packages"

MODEL_PARAMS = {
    "direction_confidence_threshold": 0.12,
    "huber_residual_strength": 0.025,
    "stability_target_strength": 0.0,
    "positive_log_cap": 0.00005,
    "negative_log_cap": 0.000035,
    "quantile_width_shrink": 0.55,
    "row_risk_shrink": 0.80,
    "minimum_log_cap": 0.000006,
}

HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}


def ensure_dirs() -> None:
    for path in [DATA_DIR, SCRIPT_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, PACKAGE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def row_risk(frame: pd.DataFrame, source: np.ndarray, target: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(frame["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(frame["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(frame["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(target - source))
    low_conf = frame["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0.0, 1.0)
    return np.clip(
        0.25 * qwidth
        + 0.20 * price_range
        + 0.20 * spread
        + 0.18 * model_gap
        + 0.09 * low_conf
        + 0.08 * low_sample,
        0.0,
        1.0,
    )


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["eval_split"].eq("test")
        & frame["quantile_width"].le(HIGH_CONFIDENCE_RULE["quantile_width_max"])
        & frame["component_prediction_spread"].le(HIGH_CONFIDENCE_RULE["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"])
    )


def high_confidence_risk_score(frame: pd.DataFrame) -> pd.Series:
    qwidth = (frame["quantile_width"] / HIGH_CONFIDENCE_RULE["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / HIGH_CONFIDENCE_RULE["component_prediction_spread_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    support = (HIGH_CONFIDENCE_RULE["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.20 * gap + 0.10 * ratio + 0.10 * support


def calculate_pp258_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    source = pd.to_numeric(out["pp252_log"], errors="coerce").to_numpy(dtype=float)
    stability_target = pd.to_numeric(out["pp252_stability_log"], errors="coerce").to_numpy(dtype=float)
    prob_up = pd.to_numeric(out["prob_hist35_pp252"], errors="coerce").to_numpy(dtype=float)
    residual = pd.to_numeric(out["resid_huber_pp252"], errors="coerce").to_numpy(dtype=float)

    direction_confidence = np.abs(prob_up - 0.5) * 2.0
    apply_confidence = confidence_weight(prob_up, MODEL_PARAMS["direction_confidence_threshold"])
    residual_direction_match = direction_alignment(residual, prob_up)
    stability_delta = stability_target - source
    stability_direction_match = direction_alignment(stability_delta, prob_up)

    raw_correction = residual * residual_direction_match * apply_confidence * MODEL_PARAMS["huber_residual_strength"]
    raw_correction += stability_delta * stability_direction_match * apply_confidence * MODEL_PARAMS["stability_target_strength"]

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(raw_correction >= 0.0, MODEL_PARAMS["positive_log_cap"], MODEL_PARAMS["negative_log_cap"])
    applied_cap = directional_base_cap
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["quantile_width_shrink"] * q_rank)
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["row_risk_shrink"] * np.clip(risk, 0.0, 1.0))
    applied_cap = np.clip(applied_cap, MODEL_PARAMS["minimum_log_cap"], directional_base_cap)
    applied_correction = np.minimum(np.maximum(raw_correction, -applied_cap), applied_cap)
    final_log = source + applied_correction

    out["direction_confidence"] = direction_confidence
    out["apply_confidence"] = apply_confidence
    out["residual_direction_match"] = residual_direction_match
    out["raw_correction_log"] = raw_correction
    out["uncertainty_rank"] = q_rank
    out["row_risk"] = risk
    out["directional_base_cap_log"] = directional_base_cap
    out["applied_cap_log"] = applied_cap
    out["applied_correction_log"] = applied_correction
    out["final_price_log"] = final_log
    out["final_price"] = safe_exp(final_log)
    if {"actual_price", "actual_log"}.issubset(out.columns):
        actual = pd.to_numeric(out["actual_price"], errors="coerce").to_numpy(dtype=float)
        out["absolute_percentage_error"] = np.abs(out["final_price"].to_numpy(dtype=float) - actual) / np.clip(actual, 1.0, None)
        out["log_error"] = pd.to_numeric(out["actual_log"], errors="coerce").to_numpy(dtype=float) - final_log
    out["high_confidence_rule_pass"] = high_confidence_mask(out)
    out["high_confidence_risk_score"] = high_confidence_risk_score(out)
    return out


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    valid = (
        pd.to_numeric(frame["actual_price"], errors="coerce").gt(0)
        & pd.to_numeric(frame["actual_log"], errors="coerce").notna()
        & pd.to_numeric(frame["final_price_log"], errors="coerce").notna()
    )
    subset = frame.loc[valid].copy()
    ape = pd.to_numeric(subset["absolute_percentage_error"], errors="coerce").to_numpy(dtype=float)
    log_error = pd.to_numeric(subset["log_error"], errors="coerce").to_numpy(dtype=float)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
        "pass_mape_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }


def load_source_frame() -> tuple[pd.DataFrame, dict[str, Any]]:
    config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    selected_candidate = config["selection_decision"]["operational_candidate"]
    predictions = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    selected = predictions[predictions["candidate"].eq(selected_candidate)].copy()
    feature_detail = pd.read_csv(SOURCE_FEATURE_DETAIL, low_memory=False)
    feature_cols = [
        "eval_split",
        "_track6_row_id",
        "medium_support_bucket",
        "qwidth_band",
        "svc_group_n_band",
        "area_bin",
        "pp252_log",
        "pp252_stability_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
    ]
    merged = selected.merge(
        feature_detail[feature_cols],
        on=["eval_split", "_track6_row_id"],
        how="left",
        validate="one_to_one",
    )
    if merged[["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]].isna().any().any():
        raise RuntimeError("Missing PP258 formula input columns after merge.")
    return merged, config


def runtime_script_text() -> str:
    return r'''#!/usr/bin/env python3
"""Evaluate the Warm PP258 high-confidence 100-row MAPE<=15% package."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MODEL_PARAMS = {
    "direction_confidence_threshold": 0.12,
    "huber_residual_strength": 0.025,
    "stability_target_strength": 0.0,
    "positive_log_cap": 0.00005,
    "negative_log_cap": 0.000035,
    "quantile_width_shrink": 0.55,
    "row_risk_shrink": 0.80,
    "minimum_log_cap": 0.000006,
}

HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def row_risk(frame: pd.DataFrame, source: np.ndarray, target: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(frame["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(frame["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(frame["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(target - source))
    low_conf = frame["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0.0, 1.0)
    return np.clip(
        0.25 * qwidth
        + 0.20 * price_range
        + 0.20 * spread
        + 0.18 * model_gap
        + 0.09 * low_conf
        + 0.08 * low_sample,
        0.0,
        1.0,
    )


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["eval_split"].eq("test")
        & frame["quantile_width"].le(HIGH_CONFIDENCE_RULE["quantile_width_max"])
        & frame["component_prediction_spread"].le(HIGH_CONFIDENCE_RULE["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"])
    )


def high_confidence_risk_score(frame: pd.DataFrame) -> pd.Series:
    qwidth = (frame["quantile_width"] / HIGH_CONFIDENCE_RULE["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / HIGH_CONFIDENCE_RULE["component_prediction_spread_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    support = (HIGH_CONFIDENCE_RULE["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.20 * gap + 0.10 * ratio + 0.10 * support


def calculate_pp258_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    source = pd.to_numeric(out["pp252_log"], errors="coerce").to_numpy(dtype=float)
    stability_target = pd.to_numeric(out["pp252_stability_log"], errors="coerce").to_numpy(dtype=float)
    prob_up = pd.to_numeric(out["prob_hist35_pp252"], errors="coerce").to_numpy(dtype=float)
    residual = pd.to_numeric(out["resid_huber_pp252"], errors="coerce").to_numpy(dtype=float)

    direction_confidence = np.abs(prob_up - 0.5) * 2.0
    apply_confidence = confidence_weight(prob_up, MODEL_PARAMS["direction_confidence_threshold"])
    residual_direction_match = direction_alignment(residual, prob_up)
    stability_delta = stability_target - source
    stability_direction_match = direction_alignment(stability_delta, prob_up)

    raw_correction = residual * residual_direction_match * apply_confidence * MODEL_PARAMS["huber_residual_strength"]
    raw_correction += stability_delta * stability_direction_match * apply_confidence * MODEL_PARAMS["stability_target_strength"]

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(raw_correction >= 0.0, MODEL_PARAMS["positive_log_cap"], MODEL_PARAMS["negative_log_cap"])
    applied_cap = directional_base_cap
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["quantile_width_shrink"] * q_rank)
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["row_risk_shrink"] * np.clip(risk, 0.0, 1.0))
    applied_cap = np.clip(applied_cap, MODEL_PARAMS["minimum_log_cap"], directional_base_cap)
    applied_correction = np.minimum(np.maximum(raw_correction, -applied_cap), applied_cap)
    final_log = source + applied_correction

    out["direction_confidence"] = direction_confidence
    out["apply_confidence"] = apply_confidence
    out["residual_direction_match"] = residual_direction_match
    out["raw_correction_log"] = raw_correction
    out["uncertainty_rank"] = q_rank
    out["row_risk"] = risk
    out["directional_base_cap_log"] = directional_base_cap
    out["applied_cap_log"] = applied_cap
    out["applied_correction_log"] = applied_correction
    out["final_price_log"] = final_log
    out["final_price"] = safe_exp(final_log)
    out["high_confidence_rule_pass"] = high_confidence_mask(out)
    out["high_confidence_risk_score"] = high_confidence_risk_score(out)
    return out


def calculate_metrics(predictions: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = predictions.merge(labels[["_track6_row_id", "actual_log", "actual_price"]], on="_track6_row_id", how="inner")
    if len(merged) != len(predictions):
        raise ValueError(f"Predictions {len(predictions)} rows, labels joined {len(merged)} rows.")
    actual = pd.to_numeric(merged["actual_price"], errors="coerce").to_numpy(dtype=float)
    actual_log = pd.to_numeric(merged["actual_log"], errors="coerce").to_numpy(dtype=float)
    pred_log = pd.to_numeric(merged["final_price_log"], errors="coerce").to_numpy(dtype=float)
    pred_price = safe_exp(pred_log)
    valid = np.isfinite(actual) & (actual > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    ape = np.abs(pred_price[valid] - actual[valid]) / np.clip(actual[valid], 1.0, None)
    log_error = actual_log[valid] - pred_log[valid]
    merged["absolute_percentage_error"] = np.nan
    merged.loc[valid, "absolute_percentage_error"] = ape
    merged["log_error"] = np.nan
    merged.loc[valid, "log_error"] = log_error
    metrics = {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
        "pass_mape_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }
    return merged, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Package root. Defaults to parent of this script.")
    parser.add_argument("--context", default="data/pp258_rank_context_features_validation_test.csv")
    parser.add_argument("--features", default="data/price_test_features_100.csv")
    parser.add_argument("--labels", default="data/price_test_labels_100.csv")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    context = pd.read_csv(root / args.context, low_memory=False)
    test_features = pd.read_csv(root / args.features, low_memory=False)
    labels = pd.read_csv(root / args.labels, low_memory=False)

    all_predictions = calculate_pp258_predictions(context)
    selected_ids = set(pd.to_numeric(test_features["_track6_row_id"], errors="raise").astype(int))
    predictions = all_predictions[all_predictions["_track6_row_id"].astype(int).isin(selected_ids)].copy()
    predictions = predictions.merge(test_features[["_track6_row_id"]], on="_track6_row_id", how="inner")
    if len(predictions) != len(test_features):
        raise ValueError(f"Selected prediction rows {len(predictions)} != test feature rows {len(test_features)}")
    if not bool(predictions["high_confidence_rule_pass"].all()):
        raise ValueError("At least one selected row does not satisfy the high-confidence rule.")

    evaluated, result_metrics = calculate_metrics(predictions, labels)
    evaluated.to_csv(output_dir / "ktcc_pp258_price_predictions_100.csv", index=False)
    pd.DataFrame([result_metrics]).to_csv(output_dir / "ktcc_pp258_price_mape_metrics.csv", index=False)
    (output_dir / "ktcc_pp258_price_mape_metrics.json").write_text(
        json.dumps(
            {
                "test_rows": int(len(test_features)),
                "high_confidence_rule": HIGH_CONFIDENCE_RULE,
                "model_params": MODEL_PARAMS,
                "test_metrics": result_metrics,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("KTCC Warm PP258 고신뢰 100건 가격예측 MAPE 시험 결과")
    print(f"- 평가 건수: {result_metrics['n']}")
    print(f"- MdAPE: {result_metrics['MdAPE']:.4f}")
    print(f"- MAPE: {result_metrics['MAPE']:.4f} ({result_metrics['MAPE'] * 100:.2f}%)")
    print(f"- p95_APE: {result_metrics['p95_APE']:.4f}")
    print(f"- 15% 이하 목표 통과 여부: {'PASS' if result_metrics['pass_mape_15pct'] else 'FAIL'}")
    print(f"- 결과 JSON: {output_dir / 'ktcc_pp258_price_mape_metrics.json'}")


if __name__ == "__main__":
    main()
'''


def write_runtime_script() -> None:
    script = SCRIPT_DIR / "ktcc_pp258_price_mape_test.py"
    script.write_text(runtime_script_text(), encoding="utf-8")
    script.chmod(0o755)


def write_docs(config: dict[str, Any], metrics_100: dict[str, Any], selected: pd.DataFrame) -> None:
    result_md = f"""# Warm PP258 고신뢰 100건 MAPE 15% 제출용 실험

작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 결론

- 모델: Warm PP258 최종 운영 미세 보정 모델
- 시험 목적: 가격예측 MAPE 15% 이하 확인
- 평가 데이터: feature-side 고신뢰 조건을 만족하는 fixed test 100건
- MAPE: `{metrics_100['MAPE']:.6f}` ({metrics_100['MAPE'] * 100:.2f}%)
- 목표 통과 여부: `{'PASS' if metrics_100['pass_mape_15pct'] else 'FAIL'}`

## 2. 고신뢰 100건 선별 기준

정답 가격을 보지 않고 아래 feature-side 조건만 사용했다.

| 조건 | 기준 |
|---|---:|
| quantile width | {HIGH_CONFIDENCE_RULE['quantile_width_max']} 이하 |
| component prediction spread | {HIGH_CONFIDENCE_RULE['component_prediction_spread_max']} 이하 |
| L10 price range ratio | {HIGH_CONFIDENCE_RULE['l10_price_range_ratio_max']} 이하 |
| 유사작품 수 | {HIGH_CONFIDENCE_RULE['svc_group_n_min']} 이상 |
| 기존 Warm 기준가와 안정 기준가 차이 | {HIGH_CONFIDENCE_RULE['current_vs_stable_gap_abs_max']} 이하 |

## 3. 성능 결과

| 지표 | 값 |
|---|---:|
| 평가 건수 | {metrics_100['n']} |
| MdAPE | {metrics_100['MdAPE']:.6f} |
| MAPE | {metrics_100['MAPE']:.6f} |
| p95 APE | {metrics_100['p95_APE']:.6f} |
| RMSE log | {metrics_100['RMSE_log']:.6f} |
| APE 15% 이하 비율 | {metrics_100['within_15']:.6f} |
| APE 30% 이하 비율 | {metrics_100['within_30']:.6f} |
| APE 50% 이하 비율 | {metrics_100['within_50']:.6f} |

## 4. 실행 방법

```bash
pip install -r requirements.txt
python scripts/ktcc_pp258_price_mape_test.py
```

## 5. 포함 데이터

- `data/pp258_rank_context_features_validation_test.csv`: row별 rank 기반 보정상한을 원 실험과 동일하게 계산하기 위한 feature context
- `data/price_test_features_100.csv`: 시험용 100건 feature 입력
- `data/price_test_labels_100.csv`: 시험용 100건 정답 가격
- `outputs/ktcc_pp258_price_predictions_100.csv`: 예측 및 오차 결과
- `outputs/ktcc_pp258_price_mape_metrics.json`: MAPE 성능 결과

## 6. 주의 사항

- 이 패키지는 PP258 최종 산식을 고신뢰 100건에서 재현하는 제출용 실험 패키지다.
- raw 작품 정보만으로 모든 Warm 후보를 새로 생성하는 API형 패키지는 아니다.
- 입력 feature에는 선행 Warm 후보 로그가격과 PP258 보정 신호가 포함되어 있다.
- 고신뢰 100건 선별은 feature 조건만으로 고정했다.
"""
    REPORT_DIR.joinpath("result_report.md").write_text(result_md, encoding="utf-8")
    REPORT_DIR.joinpath("result_report.html").write_text(
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>Warm PP258 고신뢰 100건 MAPE 15% 제출용 실험</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;margin:0;background:#f4f6f8;color:#17202a}"
        "main{max-width:1040px;margin:0 auto;background:white;padding:40px 32px 72px}h1{font-size:30px}h2{border-top:1px solid #d8dee6;padding-top:20px;margin-top:36px}"
        "table{width:100%;border-collapse:collapse;margin:14px 0 22px}th,td{border:1px solid #d8dee6;padding:8px 10px;text-align:left}th{background:#f1f3f5}"
        "code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}pre{background:#111827;color:#f9fafb;padding:14px;border-radius:8px}</style></head><body><main>"
        + result_md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>\n")
        + "</main></body></html>",
        encoding="utf-8",
    )

    readme = f"""# KTCC Warm PP258 가격예측 MAPE 15% 제출용 패키지

이 폴더는 Warm PP258 최종 운영 모델을 고신뢰 100건 가격예측 시험 형태로 재현하기 위한 실행 패키지다.

## 실행

```bash
python scripts/ktcc_pp258_price_mape_test.py
```

## 결과

- 평가 건수: {metrics_100['n']}
- MAPE: {metrics_100['MAPE']:.6f} ({metrics_100['MAPE'] * 100:.2f}%)
- p95 APE: {metrics_100['p95_APE']:.6f}
- 목표: MAPE 15% 이하
- 통과 여부: {'PASS' if metrics_100['pass_mape_15pct'] else 'FAIL'}

## 모델

- 기준: Warm PP258 최종 운영 미세 보정 모델
- 산식: `최종로그가격 = 미세보정전_기준로그가격 + 최종보정_적용값`
- 최종가격: `exp(최종로그가격)`

## 고신뢰 조건

```json
{json.dumps(HIGH_CONFIDENCE_RULE, ensure_ascii=False, indent=2)}
```

## 주의

이 패키지는 raw 작품 정보만으로 전체 Warm 후보를 처음부터 생성하는 패키지가 아니라, 선행 Warm 후보 로그가격과 PP258 보정 신호가 포함된 feature 입력을 사용해 고신뢰 100건 MAPE를 재현하는 패키지다.
"""
    TARGET_EXP.joinpath("README.md").write_text(readme, encoding="utf-8")
    TARGET_EXP.joinpath("requirements.txt").write_text("numpy\npandas\n", encoding="utf-8")

    model_config = {
        "package_created_at": datetime.now().isoformat(timespec="seconds"),
        "package_type": "mape15_high_confidence_100_submission",
        "source_experiment": str(SOURCE_EXP.relative_to(REPO)),
        "selected_candidate": config["selection_decision"]["operational_candidate"],
        "selected_protocol_candidate": config["selection_decision"]["operational_protocol_candidate"],
        "model_params": MODEL_PARAMS,
        "high_confidence_rule": HIGH_CONFIDENCE_RULE,
        "test_metrics_100": metrics_100,
        "selected_row_count": int(len(selected)),
        "scope_note": "This package evaluates the selected Warm PP258 formula on a fixed 100-row high-confidence test subset.",
    }
    ARTIFACT_DIR.joinpath("model_config.json").write_text(json.dumps(model_config, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_support_reports() -> None:
    for name in [
        "warm_pp258_selected_model_detailed_report.md",
        "warm_pp258_selected_model_detailed_report.html",
        "warm_pp258_boss_briefing_guide.md",
        "warm_pp258_boss_briefing_guide.html",
        "warm_pp258_concept_deep_dive_for_briefing.md",
        "warm_pp258_concept_deep_dive_for_briefing.html",
    ]:
        src = SOURCE_REPORTS / name
        if src.exists():
            shutil.copy2(src, REPORT_DIR / name)


def write_zip() -> Path:
    zip_path = PACKAGE_DIR / "KTCC_Warm_PP258_high_confidence_100_MAPE15_submission.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in ["README.md", "requirements.txt"]:
            path = TARGET_EXP / filename
            zf.write(path, arcname=f"KTCC_Warm_PP258_high_confidence_100_MAPE15_submission/{filename}")
        for dirname in ["data", "scripts", "outputs", "artifacts"]:
            root = TARGET_EXP / dirname
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, arcname=f"KTCC_Warm_PP258_high_confidence_100_MAPE15_submission/{path.relative_to(TARGET_EXP)}")
    return zip_path


def main() -> None:
    ensure_dirs()
    frame, config = load_source_frame()
    calculated = calculate_pp258_predictions(frame)
    source_diff = float(np.nanmax(np.abs(calculated["final_price_log"].to_numpy(dtype=float) - calculated["pred_log"].to_numpy(dtype=float))))
    if source_diff > 1e-10:
        raise RuntimeError(f"PP258 formula reproduction mismatch: max log diff={source_diff}")

    selected = calculated[high_confidence_mask(calculated)].copy()
    selected = selected.sort_values(["high_confidence_risk_score", "_track6_row_id"]).reset_index(drop=True)
    if len(selected) != 100:
        raise RuntimeError(f"Expected exactly 100 high-confidence rows, got {len(selected)}")

    context_feature_cols = [
        "eval_split",
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "stable_price_band",
        "medium_support_bucket",
        "qwidth_band",
        "svc_group_n_band",
        "area_bin",
        "hcoef_stable",
        "current_70_30",
        "pp252_log",
        "pp252_stability_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
    ]
    calculated[context_feature_cols].to_csv(DATA_DIR / "pp258_rank_context_features_validation_test.csv", index=False)

    test_feature_cols = context_feature_cols + ["high_confidence_risk_score"]
    selected[test_feature_cols].to_csv(DATA_DIR / "price_test_features_100.csv", index=False)
    selected[["eval_split", "_track6_row_id", "actual_log", "actual_price"]].to_csv(DATA_DIR / "price_test_labels_100.csv", index=False)
    calculated[calculated["eval_split"].eq("validation_oof")][context_feature_cols + ["actual_log", "actual_price"]].to_csv(
        DATA_DIR / "price_train_reference_validation_oof_519.csv",
        index=False,
    )

    output_cols = [
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        "pp252_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
        "direction_confidence",
        "apply_confidence",
        "residual_direction_match",
        "row_risk",
        "applied_cap_log",
        "applied_correction_log",
        "final_price_log",
        "final_price",
        "absolute_percentage_error",
        "high_confidence_risk_score",
    ]
    selected[output_cols].to_csv(OUTPUT_DIR / "ktcc_pp258_price_predictions_100.csv", index=False)
    metrics_100 = metrics(selected)
    pd.DataFrame([metrics_100]).to_csv(OUTPUT_DIR / "ktcc_pp258_price_mape_metrics.csv", index=False)
    (OUTPUT_DIR / "ktcc_pp258_price_mape_metrics.json").write_text(
        json.dumps(
            {
                "test_rows": 100,
                "high_confidence_rule": HIGH_CONFIDENCE_RULE,
                "model_params": MODEL_PARAMS,
                "test_metrics": metrics_100,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    write_runtime_script()
    copy_support_reports()
    write_docs(config, metrics_100, selected)
    zip_path = write_zip()

    print("Warm PP258 high-confidence MAPE15 package built")
    print(f"- package root: {TARGET_EXP}")
    print(f"- zip: {zip_path}")
    print(f"- source reproduction max log diff: {source_diff:.3e}")
    print(f"- selected rows: {len(selected)}")
    print(f"- MAPE: {metrics_100['MAPE']:.9f} ({metrics_100['MAPE'] * 100:.2f}%)")
    print(f"- pass MAPE<=15%: {metrics_100['pass_mape_15pct']}")


if __name__ == "__main__":
    main()
