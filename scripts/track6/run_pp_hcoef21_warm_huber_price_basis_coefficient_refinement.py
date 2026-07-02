#!/usr/bin/env python3
"""Run PP-HCOEF21: reliability-adaptive Warm basis and Huber coefficient checks.

This experiment follows PP-HCOEF20. HCOEF20 showed that another broad
component stack does not safely replace the current HCOEF stable candidate.
HCOEF21 therefore tests a narrower question:

- Can the fixed 70:30 comparable-price basis be replaced by a reliability
  adaptive basis?
- If so, can a small Huber residual correction improve it without increasing
  large-error risk?

Candidate selection remains validation/OOF first. Fixed test and 0604 are
confirmation/stress checks only; no weight, boundary, or correction is selected
from test/0604 residuals.
"""
from __future__ import annotations

import json
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef20_warm_huber_price_basis_coefficient_refinement as h20

EXP_ID = "PP-HCOEF21"
EXP_SLUG = "PP-HCOEF21_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASELINE = h20.BASELINE
REFERENCE = h20.REFERENCE
PPV8 = h20.PPV8
SVC = h20.SVC
L10_COL = h20.L10_COL

SEED = 20260608
N_BOOTSTRAP = h20.N_BOOTSTRAP
STABLE_TEST_P95 = h20.STABLE_TEST_P95
STABLE_0604_P95 = h20.STABLE_0604_P95


@dataclass(frozen=True)
class CandidateConfig:
    candidate: str
    method: str
    features: tuple[str, ...] = ()
    alpha: float | None = None
    cap: float | None = None
    strength: float | None = None
    source_col: str | None = None
    purpose: str = ""


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def add_adaptive_basis_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create pre-declared adaptive basis features from validation-safe signals."""
    out = frame.copy()
    thresholds = dict(out.attrs.get("thresholds", {}))
    q33 = thresholds.get("qwidth_q33", float(out.loc[out["split"].eq("validation"), "quantile_width"].quantile(0.33)))
    q80 = thresholds.get("qwidth_q80", float(out.loc[out["split"].eq("validation"), "quantile_width"].quantile(0.80)))

    n = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
    n_score = (np.log1p(n.clip(lower=0.0)) - np.log1p(5.0)) / (np.log1p(50.0) - np.log1p(5.0))
    n_score = n_score.clip(0.0, 1.0)

    coverage_score = out["svc_coverage_tier"].map(
        {"high_n": 1.0, "medium_n": 0.65, "low_n": 0.25, "fallback_global": 0.05, "__MISSING__": 0.05}
    ).fillna(0.05)

    qwidth = pd.to_numeric(out["quantile_width"], errors="coerce")
    qwidth_score = 1.0 - ((qwidth - q33) / max(q80 - q33, 1e-6))
    qwidth_score = qwidth_score.clip(0.0, 1.0).fillna(0.3)

    out["basis_reliability_score"] = (0.45 * n_score + 0.35 * coverage_score + 0.20 * qwidth_score).clip(0.0, 1.0)
    out["basis_low_reliability"] = (out["basis_reliability_score"] < 0.35).astype(float)
    out["basis_high_reliability"] = (out["basis_reliability_score"] >= 0.70).astype(float)
    out["basis_qwidth_extreme"] = (qwidth > q80).astype(float).fillna(0.0)
    out["basis_large_component_gap"] = (out["abs_ppv8_stable_gap"] > 0.20).astype(float)

    rel = out["basis_reliability_score"]
    extreme = out["basis_qwidth_extreme"]
    large_gap = out["basis_large_component_gap"]
    high = out["basis_high_reliability"]

    out["svc_weight_conservative"] = (0.55 + 0.30 * rel - 0.10 * extreme + 0.05 * high).clip(0.45, 0.85)
    out["svc_weight_balanced"] = (0.50 + 0.35 * rel - 0.15 * extreme + 0.05 * high).clip(0.35, 0.85)
    out["svc_weight_ppv8_guard"] = (0.30 + 0.55 * rel - 0.25 * large_gap - 0.15 * extreme).clip(0.25, 0.85)

    out["adaptive_basis_conservative"] = out["svc_weight_conservative"] * out[SVC] + (1.0 - out["svc_weight_conservative"]) * out[PPV8]
    out["adaptive_basis_balanced"] = out["svc_weight_balanced"] * out[SVC] + (1.0 - out["svc_weight_balanced"]) * out[PPV8]
    out["adaptive_basis_ppv8_guard"] = out["svc_weight_ppv8_guard"] * out[SVC] + (1.0 - out["svc_weight_ppv8_guard"]) * out[PPV8]

    stable_delta = out[BASELINE] - out[REFERENCE]
    out["adaptive_conservative_plus_stable_delta"] = out["adaptive_basis_conservative"] + stable_delta
    out["adaptive_balanced_plus_stable_delta"] = out["adaptive_basis_balanced"] + stable_delta
    out["adaptive_guard_plus_stable_delta"] = out["adaptive_basis_ppv8_guard"] + stable_delta

    out["stable_toward_conservative_cap003_s025"] = out[BASELINE] + np.clip(
        out["adaptive_basis_conservative"] - out[REFERENCE], -0.03, 0.03
    ) * 0.25
    out["stable_toward_balanced_cap003_s025"] = out[BASELINE] + np.clip(
        out["adaptive_basis_balanced"] - out[REFERENCE], -0.03, 0.03
    ) * 0.25
    out["stable_toward_guard_cap005_s025"] = out[BASELINE] + np.clip(
        out["adaptive_basis_ppv8_guard"] - out[REFERENCE], -0.05, 0.05
    ) * 0.25

    for col in [
        "adaptive_basis_conservative",
        "adaptive_basis_balanced",
        "adaptive_basis_ppv8_guard",
        "adaptive_conservative_plus_stable_delta",
        "adaptive_balanced_plus_stable_delta",
        "adaptive_guard_plus_stable_delta",
    ]:
        out[f"{col}_minus_stable"] = out[col] - out[BASELINE]
        out[f"{col}_minus_current"] = out[col] - out[REFERENCE]

    out["svc_minus_stable_x_reliable"] = out["svc_minus_stable"] * out["basis_reliability_score"]
    out["ppv8_minus_stable_x_lowrel"] = out["ppv8_minus_stable"] * out["basis_low_reliability"]
    out["current_minus_stable_x_qextreme"] = out["current_minus_stable"] * out["basis_qwidth_extreme"]
    out["adaptive_conservative_gap_x_reliability"] = (
        out["adaptive_basis_conservative_minus_stable"] * out["basis_reliability_score"]
    )
    return out


def load_base_frame() -> pd.DataFrame:
    base = h20.load_base_frame()
    out = add_adaptive_basis_features(base)
    out.attrs["thresholds"] = dict(base.attrs.get("thresholds", {}))
    return out


def build_candidate_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = [
        CandidateConfig(BASELINE, "source", source_col=BASELINE, purpose="현재 HCOEF 안정 후보"),
        CandidateConfig(REFERENCE, "source", source_col=REFERENCE, purpose="고정 70:30 기준 후보"),
        CandidateConfig(PPV8, "source", source_col=PPV8, purpose="오차 안정화 component"),
        CandidateConfig(SVC, "source", source_col=SVC, purpose="유사 작품 기반 가격 피처"),
        CandidateConfig("l10_seq_full_generated_bucket", "source", source_col=L10_COL, purpose="PP-L10 순차 component"),
    ]
    formula_sources = {
        "hcoef21_adaptive_basis_conservative": "adaptive_basis_conservative",
        "hcoef21_adaptive_basis_balanced": "adaptive_basis_balanced",
        "hcoef21_adaptive_basis_ppv8_guard": "adaptive_basis_ppv8_guard",
        "hcoef21_adaptive_conservative_plus_stable_delta": "adaptive_conservative_plus_stable_delta",
        "hcoef21_adaptive_balanced_plus_stable_delta": "adaptive_balanced_plus_stable_delta",
        "hcoef21_adaptive_guard_plus_stable_delta": "adaptive_guard_plus_stable_delta",
        "hcoef21_stable_toward_conservative_cap003_s025": "stable_toward_conservative_cap003_s025",
        "hcoef21_stable_toward_balanced_cap003_s025": "stable_toward_balanced_cap003_s025",
        "hcoef21_stable_toward_guard_cap005_s025": "stable_toward_guard_cap005_s025",
    }
    for candidate, source_col in formula_sources.items():
        configs.append(
            CandidateConfig(
                candidate=candidate,
                method="source",
                source_col=source_col,
                purpose="유사 표본 수, coverage, quantile 폭으로 SVC:PP-V8 비율을 조정한 기준가 후보",
            )
        )

    feature_sets = {
        "adaptive_reliability": (
            "adaptive_basis_conservative_minus_stable",
            "adaptive_basis_balanced_minus_stable",
            "adaptive_basis_ppv8_guard_minus_stable",
            "basis_reliability_score",
            "basis_low_reliability",
            "basis_high_reliability",
            "basis_qwidth_extreme",
            "svc_group_n_log",
            "coverage_numeric",
            "quantile_width",
            "pred_spread",
        ),
        "adaptive_interactions": (
            "adaptive_basis_conservative_minus_stable",
            "adaptive_basis_ppv8_guard_minus_stable",
            "svc_minus_stable_x_reliable",
            "ppv8_minus_stable_x_lowrel",
            "current_minus_stable_x_qextreme",
            "adaptive_conservative_gap_x_reliability",
            "basis_reliability_score",
            "basis_low_reliability",
            "basis_qwidth_extreme",
            "pred_spread",
            "log_area_filled",
        ),
    }
    for fs_name, features in feature_sets.items():
        for alpha in [0.001, 0.01]:
            for cap in [0.02, 0.03, 0.05]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=f"hcoef21_resid_huber_{fs_name}_a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}",
                            method="residual_huber",
                            features=features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="가변 기준가 신뢰도 피처로 HCOEF 안정 후보 residual을 작게 보정",
                        )
                    )
    for fs_name, features in {
        "adaptive_reliability": feature_sets["adaptive_reliability"],
        "adaptive_interactions": feature_sets["adaptive_interactions"],
    }.items():
        for alpha in [0.1, 1.0]:
            for cap in [0.02, 0.03]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=f"hcoef21_resid_ridge_{fs_name}_a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}",
                            method="residual_ridge",
                            features=features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="Huber residual과 비교하기 위한 Ridge residual 대조군",
                        )
                    )

    direct_features = (
        BASELINE,
        "adaptive_basis_conservative",
        "adaptive_basis_balanced",
        "adaptive_basis_ppv8_guard",
        REFERENCE,
        SVC,
        PPV8,
        "basis_reliability_score",
        "quantile_width",
        "svc_group_n_log",
        "pred_spread",
    )
    for method, alphas in [("direct_huber", [0.001, 0.01]), ("direct_ridge", [0.1, 1.0])]:
        for alpha in alphas:
            configs.append(
                CandidateConfig(
                    candidate=f"hcoef21_{method}_adaptive_basis_stack_a{slug_float(alpha)}",
                    method=method,
                    features=direct_features,
                    alpha=alpha,
                    purpose="가변 기준가와 기존 component를 저차원 선형 stack으로 직접 재학습",
                )
            )
    return configs


def estimator(config: CandidateConfig):
    if config.method in {"residual_huber", "direct_huber"}:
        model = HuberRegressor(epsilon=1.35, alpha=float(config.alpha or 0.001), max_iter=5000)
    elif config.method in {"residual_ridge", "direct_ridge"}:
        model = Ridge(alpha=float(config.alpha or 1.0))
    else:
        raise ValueError(f"Config {config.candidate} does not use an estimator.")
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), model)


def fit_model(train: pd.DataFrame, config: CandidateConfig):
    model = estimator(config)
    x = train[list(config.features)]
    if config.method.startswith("residual_"):
        y = train["actual_log"].to_numpy(dtype=float) - train[BASELINE].to_numpy(dtype=float)
    else:
        y = train["actual_log"].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x, y)
    return model


def predict_with_model(model: Any, frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, np.ndarray]:
    raw = model.predict(frame[list(config.features)])
    if config.method.startswith("residual_"):
        cap = float(config.cap or 0.0)
        strength = float(config.strength or 1.0)
        move = np.clip(raw, -cap, cap) * strength
        return frame[BASELINE].to_numpy(dtype=float) + move, move
    pred = np.asarray(raw, dtype=float)
    return pred, pred - frame[BASELINE].to_numpy(dtype=float)


def predict_source(frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, np.ndarray]:
    source = config.source_col or BASELINE
    pred = pd.to_numeric(frame[source], errors="coerce").to_numpy(dtype=float)
    pred = np.where(np.isfinite(pred), pred, frame[BASELINE].to_numpy(dtype=float))
    return pred, pred - frame[BASELINE].to_numpy(dtype=float)


def validation_oof_predictions(validation: pd.DataFrame, configs: list[CandidateConfig], scheme: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for config in configs:
        if config.method == "source":
            result[config.candidate] = predict_source(validation, config)
            continue
        pred = np.full(len(validation), np.nan, dtype=float)
        move = np.full(len(validation), np.nan, dtype=float)
        for train_idx, hold_idx in h20.split_iter(validation, scheme):
            train = validation.iloc[train_idx].copy()
            hold = validation.iloc[hold_idx].copy()
            model = fit_model(train, config)
            hold_pred, hold_move = predict_with_model(model, hold, config)
            pred[hold_idx] = hold_pred
            move[hold_idx] = hold_move
        result[config.candidate] = (pred, move)
    return result


def fixed_predictions(validation: pd.DataFrame, frame: pd.DataFrame, configs: list[CandidateConfig]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for config in configs:
        if config.method == "source":
            result[config.candidate] = predict_source(frame, config)
            continue
        model = fit_model(validation, config)
        result[config.candidate] = predict_with_model(model, frame, config)
    return result


def prediction_frame(scope: str, split: str, frame: pd.DataFrame, config: CandidateConfig, pred: np.ndarray, move: np.ndarray) -> pd.DataFrame:
    pred_price = h20.safe_exp(pred)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "scope": scope,
            "split": split,
            "candidate": config.candidate,
            "method": config.method,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].fillna("").astype(str).to_numpy(),
            "artist_name_ko": frame.get("artist_name_ko", pd.Series("", index=frame.index)).fillna("").astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred,
            "pred_price": pred_price,
            "policy_move_log": move,
            BASELINE: frame[BASELINE].to_numpy(dtype=float),
            REFERENCE: frame[REFERENCE].to_numpy(dtype=float),
            PPV8: frame[PPV8].to_numpy(dtype=float),
            SVC: frame[SVC].to_numpy(dtype=float),
            L10_COL: frame[L10_COL].to_numpy(dtype=float),
            "adaptive_basis_conservative": frame["adaptive_basis_conservative"].to_numpy(dtype=float),
            "adaptive_basis_balanced": frame["adaptive_basis_balanced"].to_numpy(dtype=float),
            "adaptive_basis_ppv8_guard": frame["adaptive_basis_ppv8_guard"].to_numpy(dtype=float),
            "basis_reliability_score": frame["basis_reliability_score"].to_numpy(dtype=float),
            "svc_weight_conservative": frame["svc_weight_conservative"].to_numpy(dtype=float),
            "svc_weight_balanced": frame["svc_weight_balanced"].to_numpy(dtype=float),
            "svc_weight_ppv8_guard": frame["svc_weight_ppv8_guard"].to_numpy(dtype=float),
            "quantile_width": frame["quantile_width"].to_numpy(dtype=float),
            "l10_price_range_ratio": frame["l10_price_range_ratio"].to_numpy(dtype=float),
            "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "service_confidence_tier": frame["service_confidence_tier"].astype(str).to_numpy(),
            "qwidth_band": frame["qwidth_band"].astype(str).to_numpy(),
            "svc_group_n_band": frame["svc_group_n_band"].astype(str).to_numpy(),
            "gap_band": frame["gap_band"].astype(str).to_numpy(),
            "pred_spread_band": frame["pred_spread_band"].astype(str).to_numpy(),
            "stable_pred_price_band": frame["stable_pred_price_band"].astype(str).to_numpy(),
            "medium_support_bucket": frame["medium_support_bucket"].astype(str).to_numpy(),
            "log_area": frame["log_area"].to_numpy(dtype=float),
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def evaluate_all(base: pd.DataFrame, configs: list[CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    validation = base[base["split"].eq("validation")].reset_index(drop=True)
    test = base[base["split"].eq("test")].reset_index(drop=True)
    stress = base[base["split"].eq("0604_ex50")].reset_index(drop=True)
    metric_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []

    for scheme in ["row", "artist"]:
        pred_map = validation_oof_predictions(validation, configs, scheme)
        stable_metric = h20.metric(validation, pred_map[BASELINE][0])
        reference_metric = h20.metric(validation, pred_map[REFERENCE][0])
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = h20.metric(validation, pred)
            metric_rows.append(
                h20.metric_row(
                    scope=f"validation_oof_{scheme}",
                    split="validation",
                    candidate=config.candidate,
                    method=config.method,
                    n=len(validation),
                    m=m,
                    stable_metric=stable_metric,
                    reference_metric=reference_metric,
                    extra={"mean_policy_move_log": float(np.nanmean(move)), "mean_abs_policy_move_log": float(np.nanmean(np.abs(move)))},
                )
            )
            prediction_rows.append(prediction_frame(f"validation_oof_{scheme}", "validation", validation, config, pred, move))

    for split, frame in [("test", test), ("0604_ex50", stress)]:
        pred_map = fixed_predictions(validation, frame, configs)
        stable_metric = h20.metric(frame, pred_map[BASELINE][0])
        reference_metric = h20.metric(frame, pred_map[REFERENCE][0])
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = h20.metric(frame, pred)
            metric_rows.append(
                h20.metric_row(
                    scope="fixed_confirmation" if split == "test" else "0604_stress",
                    split=split,
                    candidate=config.candidate,
                    method=config.method,
                    n=len(frame),
                    m=m,
                    stable_metric=stable_metric,
                    reference_metric=reference_metric,
                    extra={"mean_policy_move_log": float(np.nanmean(move)), "mean_abs_policy_move_log": float(np.nanmean(np.abs(move)))},
                )
            )
            prediction_rows.append(prediction_frame("fixed_confirmation" if split == "test" else "0604_stress", split, frame, config, pred, move))
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)


def bootstrap_summary(predictions: pd.DataFrame, configs: list[CandidateConfig]) -> pd.DataFrame:
    return h20.bootstrap_summary(predictions, configs)  # type: ignore[arg-type]


def selection_table(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    out = h20.selection_table(metrics_df, bootstrap_df)
    formula_mask = out["candidate"].str.startswith("hcoef21_adaptive") | out["candidate"].str.startswith("hcoef21_stable_toward")
    out.loc[formula_mask & out["decision"].eq("component 대조군"), "decision"] = "가변 기준가 후보"
    return out


def feature_interpretation(feature: str, coef: float, config: CandidateConfig) -> str:
    if feature.startswith("adaptive_basis_"):
        return "표본 수, coverage, quantile 폭으로 조정한 SVC:PP-V8 가변 기준가와 현재 안정 후보의 차이를 반영한다."
    if feature == "basis_reliability_score":
        return "유사 표본 수와 coverage가 높고 quantile 폭이 좁을수록 기준가 신뢰도가 높다는 신호다."
    if feature == "basis_low_reliability":
        return "유사 기준가를 강하게 믿기 어려운 구간인지 나타내는 이진 신호다."
    if feature == "basis_high_reliability":
        return "유사 기준가를 상대적으로 더 신뢰할 수 있는 구간인지 나타내는 이진 신호다."
    if feature == "basis_qwidth_extreme":
        return "예측 범위가 넓어 점 예측 이동을 조심해야 하는 구간인지 나타낸다."
    if feature == "svc_minus_stable_x_reliable":
        return "유사 기준가가 안정 후보와 다른 방향을 보일 때, 신뢰도가 높을수록 더 반영할지 확인한다."
    if feature == "ppv8_minus_stable_x_lowrel":
        return "유사 표본 신뢰도가 낮은 구간에서 오차 안정화 component 쪽으로 이동할지 확인한다."
    if feature == "current_minus_stable_x_qextreme":
        return "quantile 폭이 큰 구간에서 기존 70:30 후보와 안정 후보의 차이를 조심스럽게 반영한다."
    return h20.feature_interpretation(feature, coef, config)  # type: ignore[arg-type]


def coefficient_table(validation: pd.DataFrame, configs: list[CandidateConfig], selected: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    selected_set = set(selected) | {BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket"}
    for config in configs:
        if config.candidate not in selected_set:
            continue
        if config.method == "source":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": config.source_col,
                    "standardized_coefficient": 1.0,
                    "raw_role": "source_prediction",
                    "direction": "positive",
                    "interpretation": config.purpose,
                }
            )
            continue
        model = fit_model(validation, config)
        final = model.steps[-1][1]
        coefs = getattr(final, "coef_", np.zeros(len(config.features)))
        for feature, coef in zip(config.features, coefs):
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": feature,
                    "standardized_coefficient": float(coef),
                    "raw_role": "residual_log" if config.method.startswith("residual_") else "actual_log",
                    "direction": "raises prediction" if coef > 0 else "lowers prediction" if coef < 0 else "neutral",
                    "interpretation": feature_interpretation(feature, float(coef), config),
                }
            )
    return pd.DataFrame(rows)


def residual_analysis(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    focus_candidates = list(dict.fromkeys([BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket", *selected]))
    focus = predictions[predictions["candidate"].isin(focus_candidates)].copy()
    rows: list[dict[str, Any]] = []
    segment_cols = [
        "svc_coverage_tier",
        "svc_group_n_band",
        "qwidth_band",
        "gap_band",
        "pred_spread_band",
        "medium_support_bucket",
    ]
    for col in segment_cols:
        for (scope, split, candidate, value), group in focus.groupby(["scope", "split", "candidate", col], dropna=False):
            if len(group) < 5:
                continue
            rows.append(
                {
                    "scope": scope,
                    "split": split,
                    "candidate": candidate,
                    "segment_col": col,
                    "segment_value": value,
                    "n": len(group),
                    "MdAPE": float(group["ape"].median()),
                    "MAPE": float(group["ape"].mean()),
                    "p95_APE": float(group["ape"].quantile(0.95)),
                    "median_residual_log": float(group["residual_log"].median()),
                    "mean_residual_log": float(group["residual_log"].mean()),
                    "mean_abs_move_log": float(group["policy_move_log"].abs().mean()),
                }
            )
    return pd.DataFrame(rows).sort_values(["scope", "split", "segment_col", "MAPE"], ascending=[True, True, True, False])


def adaptive_weight_summary(base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, group in base.groupby("split"):
        for col in ["svc_coverage_tier", "svc_group_n_band", "qwidth_band"]:
            for value, seg in group.groupby(col, dropna=False):
                if len(seg) < 5:
                    continue
                rows.append(
                    {
                        "split": split,
                        "segment_col": col,
                        "segment_value": value,
                        "n": len(seg),
                        "mean_reliability_score": float(seg["basis_reliability_score"].mean()),
                        "mean_svc_weight_conservative": float(seg["svc_weight_conservative"].mean()),
                        "mean_svc_weight_balanced": float(seg["svc_weight_balanced"].mean()),
                        "mean_svc_weight_ppv8_guard": float(seg["svc_weight_ppv8_guard"].mean()),
                    }
                )
    return pd.DataFrame(rows)


def policy_map(configs: list[CandidateConfig], thresholds: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = [
        {
            "policy_item": "adaptive_basis",
            "candidate": "__global__",
            "method": "predeclared_reliability_weight",
            "details": "SVC:PP-V8 비율을 표본 수, coverage, quantile width로 조정한다. test/0604 residual은 사용하지 않는다.",
            "threshold_or_value": json.dumps(thresholds, ensure_ascii=False),
        }
    ]
    for config in configs:
        rows.append(
            {
                "policy_item": "candidate_config",
                "candidate": config.candidate,
                "method": config.method,
                "details": config.purpose,
                "threshold_or_value": json.dumps(
                    {
                        "features": list(config.features),
                        "alpha": config.alpha,
                        "cap": config.cap,
                        "strength": config.strength,
                        "source_col": config.source_col,
                    },
                    ensure_ascii=False,
                ),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    metrics_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    coeff_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    weight_df: pd.DataFrame,
) -> None:
    selected_show = selected_df.head(20)[
        [
            "candidate",
            "method",
            "decision",
            "row_oof_MdAPE",
            "row_oof_MAPE",
            "row_oof_p95_APE",
            "artist_oof_MdAPE",
            "artist_oof_MAPE",
            "artist_oof_p95_APE",
            "test_MdAPE",
            "test_MAPE",
            "test_p95_APE",
            "stress0604_MdAPE",
            "stress0604_MAPE",
            "stress0604_p95_APE",
        ]
    ]
    test_top = metrics_df[metrics_df["scope"].eq("fixed_confirmation")].sort_values(["MdAPE", "MAPE"]).head(20)
    row_top = metrics_df[metrics_df["scope"].eq("validation_oof_row")].sort_values(["MdAPE", "MAPE"]).head(20)
    boot_top = bootstrap_df.sort_values(["all3_improve_prob", "any2_improve_prob"], ascending=False).head(20)
    coeff_show = coeff_df.head(80)
    residual_show = residual_df.head(80)
    weight_show = weight_df.head(80)

    report = f"""# PP-HCOEF21 Warm Huber 가변 기준가/계수 검증

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 목적: 고정 70:30 기준가를 표본 수/coverage/quantile 폭 기반 가변 기준가로 바꿀 수 있는지 검증.
- 현재 기준 후보: `{BASELINE}` = `hcoef2_size_reliability_cap005_s050`.
- 최소 비교 기준: `{REFERENCE}` = SVC 70% + PP-V8 30%.
- 0604는 외부 stress test이며 후보 선택에는 사용하지 않음.

## 1. 실험 설계

- `current_70_30`이 실제로 `0.7 * svc_numeric_seed_mean + 0.3 * ppv8_service_proxy`인 것을 확인한 뒤 진행.
- 가변 기준가:
  - SVC 신뢰도가 높으면 SVC 비중을 높임.
  - 표본 수/coverage가 낮거나 quantile 폭이 크면 PP-V8 쪽으로 일부 이동.
  - 기존 HCOEF 안정 보정량(`hcoef_stable - current_70_30`)을 더하는 후보와, 안정 후보에서 작은 cap만큼 이동하는 후보를 분리.
- Huber residual:
  - `residual_log = actual_log - hcoef_stable`를 OOF로 학습.
  - cap과 strength로 이동폭을 제한.
  - fixed test/0604 residual은 보정값 생성에 사용하지 않음.

## 2. 후보 선택표

{h20.markdown_table(selected_show, max_rows=25)}

## 3. Fixed Test 상위 후보

{h20.markdown_table(test_top[['candidate', 'method', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE_vs_stable', 'delta_MAPE_vs_stable', 'delta_p95_APE_vs_stable', 'improve_count_vs_stable']], max_rows=20)}

## 4. Validation Row OOF 상위 후보

{h20.markdown_table(row_top[['candidate', 'method', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE_vs_stable', 'delta_MAPE_vs_stable', 'delta_p95_APE_vs_stable', 'improve_count_vs_stable']], max_rows=20)}

## 5. Bootstrap / Repeated Split 요약

{h20.markdown_table(boot_top, max_rows=20)}

## 6. 가변 기준가 비율 요약

{h20.markdown_table(weight_show, max_rows=80)}

## 7. 계수 해석

{h20.markdown_table(coeff_show, max_rows=80)}

## 8. 잔차 구간 분석

{h20.markdown_table(residual_show, max_rows=80)}

## 9. 판단

- 운영 기본 후보는 현재 기준 후보보다 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 함.
- 가변 기준가 후보는 설명 가능성이 높지만, 큰 오차 p95가 안정 후보보다 커지면 운영 기본 후보로 채택하지 않음.
- Huber residual 후보는 MAPE 또는 p95 목적별 후보로는 남길 수 있지만, bootstrap gate를 통과하지 못하면 기본 후보로 승격하지 않음.
"""
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h20.md_to_html(report), encoding="utf-8")


def write_doc_summary(selected_df: pd.DataFrame) -> None:
    top = selected_df.head(8)[
        ["candidate", "decision", "test_MdAPE", "test_MAPE", "test_p95_APE", "stress0604_MdAPE", "stress0604_MAPE", "stress0604_p95_APE"]
    ]
    doc = f"""# PP-HCOEF21 Warm Huber 가변 기준가/계수 검증 요약

- 실험 폴더: `experiments/track6/{EXP_SLUG}`
- 실행 스크립트: `scripts/track6/run_pp_hcoef21_warm_huber_price_basis_coefficient_refinement.py`
- 목적: 단일 70:30 기준가를 표본 수/coverage/quantile 폭 기반 가변 기준가로 바꾸고, Huber residual로 작게 보정 가능한지 검증.

## 핵심 결과

{h20.markdown_table(top, max_rows=8)}

## 해석

- 가변 기준가는 Huber가 설명할 수 있는 기준가/신뢰도 피처를 명확히 만들기 위한 실험임.
- 운영 후보 판단은 fixed test 단독이 아니라 validation OOF, artist OOF, bootstrap을 우선함.
- 0604는 외부 stress test로만 사용함.
"""
    md = DOC_ROOT / "pp_hcoef21_warm_huber_price_basis_coefficient_refinement_summary.md"
    html = DOC_ROOT / "pp_hcoef21_warm_huber_price_basis_coefficient_refinement_summary.html"
    md.write_text(doc, encoding="utf-8")
    html.write_text(h20.md_to_html(doc), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    base = load_base_frame()
    configs = build_candidate_configs()

    config_payload = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": BASELINE,
        "reference": REFERENCE,
        "selection_policy": "validation/OOF first; fixed test and 0604 confirmation only",
        "thresholds_from_validation": base.attrs.get("thresholds", {}),
        "candidate_count": len(configs),
        "candidates": [config.__dict__ for config in configs],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    metrics_df, predictions_df = evaluate_all(base, configs)
    bootstrap_df = bootstrap_summary(predictions_df, configs)
    selected_df = selection_table(metrics_df, bootstrap_df)
    selected_names = selected_df[selected_df["decision"].ne("보류")]["candidate"].head(12).tolist()
    coeff_df = coefficient_table(base[base["split"].eq("validation")].copy(), configs, selected_names)
    residual_df = residual_analysis(predictions_df, selected_names)
    weight_df = adaptive_weight_summary(base)
    policy_df = policy_map(configs, base.attrs.get("thresholds", {}))

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions_df.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    selected_df.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    coeff_df.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residual_df.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    weight_df.to_csv(EXP_DIR / "outputs" / "adaptive_weight_summary.csv", index=False)
    policy_df.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)

    write_report(metrics_df, selected_df, coeff_df, residual_df, bootstrap_df, weight_df)
    write_doc_summary(selected_df)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(selected_df.head(10)[["candidate", "decision", "test_MdAPE", "test_MAPE", "test_p95_APE", "stress0604_MdAPE", "stress0604_MAPE", "stress0604_p95_APE"]].to_string(index=False))


if __name__ == "__main__":
    main()
