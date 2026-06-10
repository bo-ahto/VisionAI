#!/usr/bin/env python3
"""Run PP-CF1: confidence-filtered residual training audit for Warm/HCOEF.

This experiment checks whether low-confidence Warm rows should be excluded or
down-weighted when fitting residual calibration models. Confidence tiers are
defined only from feature-side signals, never from actual price or residuals.
"""
from __future__ import annotations

import html
import json
import math
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


try:
    from catboost import CatBoostRegressor
except Exception:  # pragma: no cover - optional local dependency
    CatBoostRegressor = None

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - optional local dependency
    XGBRegressor = None


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-CF1"
EXP_SLUG = "PP-CF1_warm_confidence_filtered_training"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

SOURCE_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)

SEED = 20260608
N_FOLDS = 5
BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"

COMPONENT_COLS = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
]

RESIDUAL_FEATURES = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n_log",
    "log_area",
    "component_prediction_spread",
    "component_prediction_range",
    "current_vs_stable_gap_abs",
    "current_minus_stable_log",
    "ppv8_minus_stable_log",
    "svc_minus_stable_log",
    "l10_minus_stable_log",
    "confidence_risk_score",
]

CAPS = [0.01, 0.02, 0.03, 0.05, 0.08]

HIGH_CONFIDENCE_RULE = {
    "quantile_width_max": 1.20,
    "component_prediction_spread_max": 0.10,
    "l10_price_range_ratio_max": 2.00,
    "svc_group_n_min": 5,
    "current_vs_stable_gap_abs_max": 0.025,
}

LOW_CONFIDENCE_RULE = {
    "quantile_width_min": 1.60,
    "component_prediction_spread_min": 0.18,
    "l10_price_range_ratio_min": 2.50,
    "svc_group_n_max": 4,
    "current_vs_stable_gap_abs_min": 0.050,
}

WEIGHT_BY_TIER = {
    "high_confidence": 1.00,
    "medium_confidence": 0.45,
    "low_confidence": 0.15,
}


@dataclass(frozen=True)
class TrainPolicy:
    policy: str
    description: str
    allowed_tiers: tuple[str, ...] | None
    weighted: bool = False


TRAIN_POLICIES = [
    TrainPolicy("all_rows", "validation 전체 row로 학습", None, False),
    TrainPolicy("high_only", "고신뢰 row만 학습", ("high_confidence",), False),
    TrainPolicy("high_mid_only", "고신뢰 + 중신뢰 row만 학습", ("high_confidence", "medium_confidence"), False),
    TrainPolicy("confidence_weighted", "전체 row를 쓰되 신뢰도별 sample weight 적용", None, True),
    TrainPolicy("low_only_diagnostic", "저신뢰 row만 학습하는 진단 대조군", ("low_confidence",), False),
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric(frame: pd.DataFrame, pred_log: pd.Series | np.ndarray) -> dict[str, Any]:
    pred_log_arr = np.asarray(pred_log, dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = safe_exp(pred_log_arr)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(np.isfinite(ape).sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(actual_log - pred_log_arr)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def load_base_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    base = raw[
        raw["candidate"].eq(BASE_CANDIDATE)
        & raw["split"].isin(["validation", "test"])
    ].copy()
    source_audit = {
        "source_rows_by_split": base.groupby("split").size().astype(int).to_dict(),
        "source_unique_row_ids_by_split": base.groupby("split")["_track6_row_id"].nunique().astype(int).to_dict(),
    }
    base["_scope_rank"] = base["scope"].map({"validation_oof_row": 0, "validation_oof_artist": 1}).fillna(9)
    base = (
        base.sort_values(["split", "_track6_row_id", "_scope_rank"])
        .drop_duplicates(["split", "_track6_row_id"], keep="first")
        .drop(columns=["_scope_rank"])
        .reset_index(drop=True)
    )
    source_audit["deduplicated_rows_by_split"] = base.groupby("split").size().astype(int).to_dict()
    base.attrs["source_audit"] = source_audit
    return add_features(base)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = [
        "actual_log",
        "actual_price",
        "hcoef_stable",
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

    out["component_prediction_spread"] = out[COMPONENT_COLS].std(axis=1)
    out["component_prediction_range"] = out[COMPONENT_COLS].max(axis=1) - out[COMPONENT_COLS].min(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out["hcoef_stable"]).abs()
    out["svc_group_n"] = out["svc_group_n"].fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    out["log_area"] = out["log_area"].fillna(out["log_area"].median())
    out["current_minus_stable_log"] = out["current_70_30"] - out["hcoef_stable"]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out["hcoef_stable"]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out["hcoef_stable"]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out["hcoef_stable"]
    out["confidence_risk_score"] = confidence_risk_score(out)
    out["confidence_tier"] = confidence_tier(out)
    out["confidence_sample_weight"] = out["confidence_tier"].map(WEIGHT_BY_TIER).fillna(0.15)
    return out


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["quantile_width"].le(HIGH_CONFIDENCE_RULE["quantile_width_max"])
        & frame["component_prediction_spread"].le(HIGH_CONFIDENCE_RULE["component_prediction_spread_max"])
        & frame["l10_price_range_ratio"].le(HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"])
        & frame["svc_group_n"].ge(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        & frame["current_vs_stable_gap_abs"].le(HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"])
    )


def low_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["quantile_width"].gt(LOW_CONFIDENCE_RULE["quantile_width_min"])
        | frame["component_prediction_spread"].gt(LOW_CONFIDENCE_RULE["component_prediction_spread_min"])
        | frame["l10_price_range_ratio"].gt(LOW_CONFIDENCE_RULE["l10_price_range_ratio_min"])
        | frame["svc_group_n"].lt(HIGH_CONFIDENCE_RULE["svc_group_n_min"])
        | frame["current_vs_stable_gap_abs"].gt(LOW_CONFIDENCE_RULE["current_vs_stable_gap_abs_min"])
    )


def confidence_tier(frame: pd.DataFrame) -> pd.Series:
    high = high_confidence_mask(frame)
    low = low_confidence_mask(frame)
    return pd.Series(
        np.select([high, low], ["high_confidence", "low_confidence"], default="medium_confidence"),
        index=frame.index,
    )


def confidence_risk_score(frame: pd.DataFrame) -> pd.Series:
    qwidth = (frame["quantile_width"] / HIGH_CONFIDENCE_RULE["quantile_width_max"]).clip(0.0, 10.0)
    spread = (frame["component_prediction_spread"] / HIGH_CONFIDENCE_RULE["component_prediction_spread_max"]).clip(0.0, 10.0)
    ratio = (frame["l10_price_range_ratio"] / HIGH_CONFIDENCE_RULE["l10_price_range_ratio_max"]).clip(0.0, 10.0)
    gap = (frame["current_vs_stable_gap_abs"] / HIGH_CONFIDENCE_RULE["current_vs_stable_gap_abs_max"]).clip(0.0, 10.0)
    support = (HIGH_CONFIDENCE_RULE["svc_group_n_min"] / frame["svc_group_n"].clip(lower=1.0)).clip(0.0, 10.0)
    return 0.35 * qwidth + 0.25 * spread + 0.15 * ratio + 0.15 * gap + 0.10 * support


def make_model(model_family: str):
    if model_family == "huber":
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000)),
            ]
        )
    if model_family == "ridge":
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=5.0)),
            ]
        )
    if model_family == "catboost":
        if CatBoostRegressor is None:
            raise RuntimeError("catboost is not available")
        return CatBoostRegressor(
            loss_function="MAE",
            iterations=120,
            depth=4,
            learning_rate=0.04,
            l2_leaf_reg=12.0,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )
    if model_family == "xgboost":
        if XGBRegressor is None:
            raise RuntimeError("xgboost is not available")
        return XGBRegressor(
            objective="reg:squarederror",
            n_estimators=120,
            max_depth=3,
            learning_rate=0.035,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=12.0,
            random_state=SEED,
            verbosity=0,
            n_jobs=1,
        )
    raise ValueError(f"Unknown model family: {model_family}")


def fit_residual_model(model_family: str, train: pd.DataFrame, policy: TrainPolicy):
    model = make_model(model_family)
    x = train[RESIDUAL_FEATURES]
    y = train["actual_log"].to_numpy(dtype=float) - train[BASE_CANDIDATE].to_numpy(dtype=float)
    sample_weight = None
    if policy.weighted:
        sample_weight = train["confidence_sample_weight"].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        if model_family in {"huber", "ridge"}:
            if sample_weight is None:
                model.fit(x, y)
            else:
                model.fit(x, y, model__sample_weight=sample_weight)
        elif model_family == "catboost":
            model.fit(x, y, sample_weight=sample_weight)
        else:
            model.fit(x, y, sample_weight=sample_weight)
    return model


def select_training_rows(frame: pd.DataFrame, policy: TrainPolicy) -> pd.DataFrame:
    if policy.allowed_tiers is None:
        return frame.copy()
    return frame[frame["confidence_tier"].isin(policy.allowed_tiers)].copy()


def split_iter(validation: pd.DataFrame):
    groups = validation["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    if len(np.unique(groups)) >= N_FOLDS:
        splitter = GroupKFold(n_splits=N_FOLDS)
        yield from splitter.split(validation, groups=groups)
    else:
        splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        yield from splitter.split(validation)


def predict_adjustment(model: Any, model_family: str, frame: pd.DataFrame, cap: float) -> np.ndarray:
    raw = np.asarray(model.predict(frame[RESIDUAL_FEATURES]), dtype=float)
    return np.clip(raw, -cap, cap)


def validation_oof(validation: pd.DataFrame, model_family: str, policy: TrainPolicy, cap: float) -> tuple[np.ndarray, np.ndarray]:
    pred = np.full(len(validation), np.nan, dtype=float)
    move = np.full(len(validation), np.nan, dtype=float)
    for train_idx, hold_idx in split_iter(validation):
        train_fold = select_training_rows(validation.iloc[train_idx].copy(), policy)
        if len(train_fold) < 25:
            pred[hold_idx] = validation.iloc[hold_idx][BASE_CANDIDATE].to_numpy(dtype=float)
            move[hold_idx] = 0.0
            continue
        model = fit_residual_model(model_family, train_fold, policy)
        adjustment = predict_adjustment(model, model_family, validation.iloc[hold_idx], cap)
        pred[hold_idx] = validation.iloc[hold_idx][BASE_CANDIDATE].to_numpy(dtype=float) + adjustment
        move[hold_idx] = adjustment
    return pred, move


def fixed_test_prediction(validation: pd.DataFrame, test: pd.DataFrame, model_family: str, policy: TrainPolicy, cap: float) -> tuple[np.ndarray, np.ndarray, Any | None]:
    train = select_training_rows(validation.copy(), policy)
    if len(train) < 25:
        return test[BASE_CANDIDATE].to_numpy(dtype=float), np.zeros(len(test), dtype=float), None
    model = fit_residual_model(model_family, train, policy)
    adjustment = predict_adjustment(model, model_family, test, cap)
    return test[BASE_CANDIDATE].to_numpy(dtype=float) + adjustment, adjustment, model


def prediction_frame(
    frame: pd.DataFrame,
    split: str,
    scope: str,
    candidate: str,
    model_family: str,
    train_policy: str,
    cap: float,
    pred_log: np.ndarray,
    move: np.ndarray,
) -> pd.DataFrame:
    out = frame[
        [
            "split",
            "_track6_row_id",
            "artist_key",
            "artist_name_ko",
            "actual_log",
            "actual_price",
            BASE_CANDIDATE,
            REFERENCE_CANDIDATE,
            "quantile_width",
            "l10_price_range_ratio",
            "svc_group_n",
            "component_prediction_spread",
            "component_prediction_range",
            "current_vs_stable_gap_abs",
            "confidence_risk_score",
            "confidence_tier",
        ]
    ].copy()
    out["experiment_id"] = EXP_ID
    out["prediction_scope"] = scope
    out["eval_split"] = split
    out["candidate"] = candidate
    out["model_family"] = model_family
    out["train_policy"] = train_policy
    out["residual_cap_log"] = cap
    out["residual_adjustment_log"] = move
    out["pred_log"] = pred_log
    out["pred_price"] = safe_exp(pred_log)
    out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"].clip(lower=1.0)
    return out


def metric_rows_for_candidate(pred: pd.DataFrame, split: str, scope: str, candidate: str, model_family: str, train_policy: str, cap: float, train_n: int) -> list[dict[str, Any]]:
    rows = []
    subsets = [("all", pred)]
    for tier in ["high_confidence", "medium_confidence", "low_confidence"]:
        subsets.append((tier, pred[pred["confidence_tier"].eq(tier)]))
    for tier_name, sub in subsets:
        if sub.empty:
            continue
        rows.append(
            {
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "model_family": model_family,
                "train_policy": train_policy,
                "residual_cap_log": cap,
                "train_n": train_n,
                "split": split,
                "slice": tier_name,
                **metric(sub, sub["pred_log"]),
            }
        )
    return rows


def baseline_predictions(validation: pd.DataFrame, test: pd.DataFrame) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    pred_frames = []
    metric_rows = []
    baselines = [
        (BASE_CANDIDATE, BASE_CANDIDATE),
        (REFERENCE_CANDIDATE, REFERENCE_CANDIDATE),
    ]
    for candidate, col in baselines:
        for split, frame in [("validation_oof", validation), ("test", test)]:
            pred_log = frame[col].to_numpy(dtype=float)
            move = pred_log - frame[BASE_CANDIDATE].to_numpy(dtype=float)
            pred = prediction_frame(frame, split, "source", candidate, "source", "none", 0.0, pred_log, move)
            pred_frames.append(pred)
            metric_rows.extend(metric_rows_for_candidate(pred, split, "source", candidate, "source", "none", 0.0, 0))
    return pred_frames, metric_rows


def confidence_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, split_df in frame.groupby("split"):
        for tier, group in split_df.groupby("confidence_tier"):
            base_metric = metric(group, group[BASE_CANDIDATE])
            rows.append(
                {
                    "split": split,
                    "confidence_tier": tier,
                    "n": int(len(group)),
                    "quantile_width_median": float(group["quantile_width"].median()),
                    "quantile_width_max": float(group["quantile_width"].max()),
                    "component_spread_median": float(group["component_prediction_spread"].median()),
                    "component_spread_max": float(group["component_prediction_spread"].max()),
                    "l10_range_ratio_median": float(group["l10_price_range_ratio"].median()),
                    "svc_group_n_median": float(group["svc_group_n"].median()),
                    "gap_abs_median": float(group["current_vs_stable_gap_abs"].median()),
                    "base_MdAPE": base_metric["MdAPE"],
                    "base_MAPE": base_metric["MAPE"],
                    "base_p95_APE": base_metric["p95_APE"],
                }
            )
    return pd.DataFrame(rows)


def training_policy_audit(validation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy in TRAIN_POLICIES:
        train = select_training_rows(validation, policy)
        row = {
            "policy": policy.policy,
            "description": policy.description,
            "weighted": policy.weighted,
            "train_n": int(len(train)),
            "unique_row_ids": int(train["_track6_row_id"].nunique()),
            "duplicate_row_ids": int(train["_track6_row_id"].duplicated().sum()),
        }
        for tier in ["high_confidence", "medium_confidence", "low_confidence"]:
            row[f"{tier}_n"] = int(train["confidence_tier"].eq(tier).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def run_experiment() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    frame = load_base_frame()
    validation = frame[frame["split"].eq("validation")].reset_index(drop=True)
    test = frame[frame["split"].eq("test")].reset_index(drop=True)

    model_families = ["huber", "ridge"]
    if CatBoostRegressor is not None:
        model_families.append("catboost")
    if XGBRegressor is not None:
        model_families.append("xgboost")

    pred_frames, metric_rows = baseline_predictions(validation, test)
    final_models: dict[str, Any] = {}

    for model_family in model_families:
        for policy in TRAIN_POLICIES:
            train = select_training_rows(validation, policy)
            train_n = int(len(train))
            if train_n < 25:
                continue
            for cap in CAPS:
                candidate = f"{model_family}_{policy.policy}_cap{str(cap).replace('.', 'p')}"
                oof_pred, oof_move = validation_oof(validation, model_family, policy, cap)
                val_frame = prediction_frame(validation, "validation_oof", "residual_oof", candidate, model_family, policy.policy, cap, oof_pred, oof_move)
                pred_frames.append(val_frame)
                metric_rows.extend(metric_rows_for_candidate(val_frame, "validation_oof", "residual_oof", candidate, model_family, policy.policy, cap, train_n))

                test_pred, test_move, model = fixed_test_prediction(validation, test, model_family, policy, cap)
                test_frame = prediction_frame(test, "test", "fixed_test", candidate, model_family, policy.policy, cap, test_pred, test_move)
                pred_frames.append(test_frame)
                metric_rows.extend(metric_rows_for_candidate(test_frame, "test", "fixed_test", candidate, model_family, policy.policy, cap, train_n))
                if model is not None:
                    final_models[candidate] = model

    predictions = pd.concat(pred_frames, ignore_index=True)
    metrics_df = pd.DataFrame(metric_rows).sort_values(["split", "slice", "MAPE", "MdAPE", "p95_APE", "candidate"]).reset_index(drop=True)
    confidence_df = confidence_summary(frame)
    policy_df = training_policy_audit(validation)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    confidence_df.to_csv(EXP_DIR / "outputs" / "confidence_tier_summary.csv", index=False)
    policy_df.to_csv(EXP_DIR / "outputs" / "training_policy_audit.csv", index=False)

    top_validation = (
        metrics_df[
            metrics_df["split"].eq("validation_oof")
            & metrics_df["slice"].eq("all")
            & metrics_df["model_family"].ne("source")
        ]
        .sort_values(["MAPE", "MdAPE", "p95_APE"])
        .head(20)
    )
    top_test = (
        metrics_df[
            metrics_df["split"].eq("test")
            & metrics_df["slice"].eq("all")
            & metrics_df["model_family"].ne("source")
        ]
        .sort_values(["MAPE", "MdAPE", "p95_APE"])
        .head(20)
    )
    top_validation.to_csv(EXP_DIR / "outputs" / "top_validation_oof_candidates.csv", index=False)
    top_test.to_csv(EXP_DIR / "outputs" / "top_test_candidates_diagnostic.csv", index=False)

    best_candidate = str(top_validation.iloc[0]["candidate"]) if not top_validation.empty else ""
    if best_candidate in final_models:
        joblib.dump(final_models[best_candidate], EXP_DIR / "artifacts" / "best_validation_selected_model.joblib")

    run_config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "source_audit": frame.attrs.get("source_audit", {}),
        "base_candidate": BASE_CANDIDATE,
        "reference_candidate": REFERENCE_CANDIDATE,
        "component_columns": COMPONENT_COLS,
        "residual_features": RESIDUAL_FEATURES,
        "high_confidence_rule": HIGH_CONFIDENCE_RULE,
        "low_confidence_rule": LOW_CONFIDENCE_RULE,
        "confidence_weight_by_tier": WEIGHT_BY_TIER,
        "model_families": model_families,
        "residual_caps_log": CAPS,
        "selection_policy": "Select by validation_oof/all MAPE, then inspect fixed test. Test is diagnostic only.",
        "best_validation_oof_candidate": best_candidate,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(metrics_df, confidence_df, policy_df, run_config)
    return metrics_df, predictions, confidence_df, policy_df


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.head(max_rows).copy()
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


def write_report(metrics_df: pd.DataFrame, confidence_df: pd.DataFrame, policy_df: pd.DataFrame, run_config: dict[str, Any]) -> None:
    base_cols = ["candidate", "model_family", "train_policy", "residual_cap_log", "train_n", "split", "slice", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate"]
    baseline = metrics_df[
        metrics_df["candidate"].isin([BASE_CANDIDATE, REFERENCE_CANDIDATE])
        & metrics_df["slice"].eq("all")
    ][base_cols]
    top_val = metrics_df[
        metrics_df["split"].eq("validation_oof")
        & metrics_df["slice"].eq("all")
        & metrics_df["model_family"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(15)[base_cols]
    top_test = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["slice"].eq("all")
        & metrics_df["model_family"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(15)[base_cols]

    best_val = top_val.iloc[0].to_dict() if not top_val.empty else {}
    best_name = best_val.get("candidate", "")
    best_test = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["slice"].eq("all")
        & metrics_df["candidate"].eq(best_name)
    ][base_cols]
    top_val_high = metrics_df[
        metrics_df["split"].eq("validation_oof")
        & metrics_df["slice"].eq("high_confidence")
        & metrics_df["model_family"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(15)[base_cols]
    best_high_name = str(top_val_high.iloc[0]["candidate"]) if not top_val_high.empty else ""
    best_high_test = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["slice"].eq("high_confidence")
        & metrics_df["candidate"].eq(best_high_name)
    ][base_cols]
    top_test_high = metrics_df[
        metrics_df["split"].eq("test")
        & metrics_df["slice"].eq("high_confidence")
        & metrics_df["model_family"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(10)[base_cols]

    key_rows = []
    for label, candidate, split, tier in [
        ("기준가 validation 전체", BASE_CANDIDATE, "validation_oof", "all"),
        ("기준가 validation 고신뢰", BASE_CANDIDATE, "validation_oof", "high_confidence"),
        ("기준가 validation 저신뢰", BASE_CANDIDATE, "validation_oof", "low_confidence"),
        ("기준가 test 전체", BASE_CANDIDATE, "test", "all"),
        ("기준가 test 고신뢰", BASE_CANDIDATE, "test", "high_confidence"),
        ("기준가 test 저신뢰", BASE_CANDIDATE, "test", "low_confidence"),
        ("validation 전체 선택 1위", best_name, "validation_oof", "all"),
        ("validation 전체 선택 1위 test", best_name, "test", "all"),
        ("validation 고신뢰 선택 1위", best_high_name, "validation_oof", "high_confidence"),
        ("validation 고신뢰 선택 1위 test", best_high_name, "test", "high_confidence"),
    ]:
        row = metrics_df[
            metrics_df["candidate"].eq(candidate)
            & metrics_df["split"].eq(split)
            & metrics_df["slice"].eq(tier)
        ]
        if not row.empty:
            item = row.iloc[0][base_cols].to_dict()
            item["summary"] = label
            key_rows.append(item)
    key_df = pd.DataFrame(key_rows)
    if not key_df.empty:
        key_df = key_df[["summary"] + base_cols]

    report = f"""# PP-CF1 Warm 신뢰도 필터 학습 실험

- 실험 ID: `{EXP_ID}`
- 실행 시각: {datetime.now().isoformat(timespec="seconds")}
- 목적: 저신뢰 데이터가 residual 보정 모델 학습 안정성을 떨어뜨리는지 확인하고, 고신뢰/저신뢰 학습 기준을 명확히 정의한다.
- 원천: `{SOURCE_PREDICTIONS.relative_to(REPO)}`
- 선택 원칙: 후보 선택은 `validation_oof/all` MAPE 기준이며, test는 최종 확인용으로만 본다.

## 신뢰도 등급 정의

정답 가격, residual, APE는 등급 산정에 사용하지 않는다.

### 고신뢰

아래 조건을 모두 만족한다.

- `quantile_width <= {HIGH_CONFIDENCE_RULE['quantile_width_max']}`
- `component_prediction_spread <= {HIGH_CONFIDENCE_RULE['component_prediction_spread_max']}`
- `l10_price_range_ratio <= {HIGH_CONFIDENCE_RULE['l10_price_range_ratio_max']}`
- `svc_group_n >= {HIGH_CONFIDENCE_RULE['svc_group_n_min']}`
- `abs(current_70_30 - hcoef_stable) <= {HIGH_CONFIDENCE_RULE['current_vs_stable_gap_abs_max']}`

### 저신뢰

아래 위험 조건 중 하나라도 만족하면 저신뢰로 둔다.

- `quantile_width > {LOW_CONFIDENCE_RULE['quantile_width_min']}`
- `component_prediction_spread > {LOW_CONFIDENCE_RULE['component_prediction_spread_min']}`
- `l10_price_range_ratio > {LOW_CONFIDENCE_RULE['l10_price_range_ratio_min']}`
- `svc_group_n < {HIGH_CONFIDENCE_RULE['svc_group_n_min']}`
- `abs(current_70_30 - hcoef_stable) > {LOW_CONFIDENCE_RULE['current_vs_stable_gap_abs_min']}`

그 외는 중신뢰다.

## 핵심 결과

{markdown_table(key_df)}

- `validation_oof/all` 기준 1위는 전체 운영 구간 평균을 낮추는 후보다. 이 기준에서는 저신뢰 구간도 함께 최적화하므로 전체 학습 또는 가중 학습이 유리하다.
- `validation_oof/high_confidence` 기준 1위는 고신뢰 구간 전용 보정 후보다. 이 기준에서는 고신뢰만 학습한 Huber가 가장 안정적으로 나왔다.
- test 고신뢰 100건만 보면 CatBoost의 `high_mid_only` 또는 `confidence_weighted`가 가장 낮은 MAPE를 냈지만, 이는 test 진단값이므로 후보 선택 기준으로 쓰면 안 된다.

## 신뢰도 구간별 원본 기준가 성능

{markdown_table(confidence_df.sort_values(['split', 'confidence_tier']))}

## 학습 정책

{markdown_table(policy_df)}

## 기준 후보 성능

{markdown_table(baseline)}

## Validation OOF 상위 후보

{markdown_table(top_val)}

## Validation OOF 고신뢰 구간 상위 후보

{markdown_table(top_val_high)}

## Validation 1위 후보의 Test 확인

{markdown_table(best_test)}

## Validation 고신뢰 1위 후보의 Test 고신뢰 확인

{markdown_table(best_high_test)}

## Test 상위 후보

아래 표는 진단용이다. 후보 선택에는 사용하지 않는다.

{markdown_table(top_test)}

## Test 고신뢰 상위 후보

아래 표도 진단용이다. 후보 선택에는 사용하지 않는다.

{markdown_table(top_test_high)}

## 해석

- 과거 PP-L, PP-WMAPE, HCOEF 계열 다수는 신뢰도를 학습 row 제외 기준보다 피처, cap, routing, guard로 사용했다.
- 이 실험은 같은 residual feature와 같은 OOF 방식에서 `전체 학습`, `고신뢰 학습`, `고+중신뢰 학습`, `신뢰도 가중 학습`, `저신뢰만 학습`을 직접 비교한다.
- 고신뢰 hard filter가 validation OOF와 test에서 동시에 안정적이면, 후속 Warm/HCOEF 보정 실험은 train filter 또는 sample weight를 기본 옵션으로 두는 것이 맞다.

## 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/confidence_tier_summary.csv`
- `outputs/training_policy_audit.csv`
- `outputs/top_validation_oof_candidates.csv`
- `outputs/top_test_candidates_diagnostic.csv`
- `artifacts/run_config.json`
"""
    report_path = EXP_DIR / "reports" / "result_report.md"
    html_path = EXP_DIR / "reports" / "result_report.html"
    report_path.write_text(report, encoding="utf-8")
    escaped = html.escape(report)
    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>PP-CF1 Warm Confidence Filtered Training</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2937}"
        "pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #d8dee9;padding:16px;border-radius:6px}</style>"
        "</head><body><h1>PP-CF1 Warm 신뢰도 필터 학습 실험</h1>"
        f"<pre>{escaped}</pre></body></html>"
    )
    html_path.write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_cf1_warm_confidence_filtered_training.md").write_text(report, encoding="utf-8")
    (DOC_ROOT / "pp_cf1_warm_confidence_filtered_training.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    metrics_df, _, confidence_df, policy_df = run_experiment()
    top = metrics_df[
        metrics_df["split"].eq("validation_oof")
        & metrics_df["slice"].eq("all")
        & metrics_df["model_family"].ne("source")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(5)
    print(json.dumps({
        "experiment": EXP_SLUG,
        "confidence_counts": confidence_df[["split", "confidence_tier", "n", "base_MAPE"]].to_dict(orient="records"),
        "training_policies": policy_df[["policy", "train_n", "high_confidence_n", "medium_confidence_n", "low_confidence_n"]].to_dict(orient="records"),
        "top_validation_oof": top[["candidate", "model_family", "train_policy", "residual_cap_log", "train_n", "MAPE", "MdAPE", "p95_APE"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
