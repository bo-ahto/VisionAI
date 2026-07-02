#!/usr/bin/env python3
"""Run PP-HCOEF20: low-dimensional Huber coefficient search and range policy.

This experiment continues the Warm Huber HCOEF line after PP-HCOEF19 confirmed
that research components and operational v0.1 components are aligned on the
0604 stress set. HCOEF20 deliberately separates two tasks:

1. point-prediction candidates: learn small OOF residual corrections over the
   current HCOEF stable candidate using only operationally available component,
   reliability, and gap features.
2. service policy candidates: use quantile width as a price range/confidence
   signal rather than a direct point-prediction movement rule.

Candidate selection is validation/OOF first. Fixed test and 0604 are only
confirmation/stress checks; no threshold or coefficient is selected from
test/0604 residuals.
"""
from __future__ import annotations

import html
import json
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
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF20"
EXP_SLUG = "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

HCOEF18_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF18_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
PP_L10_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-L10_warm_l8_feature_variant_sequential"
    / "outputs"
    / "predictions.csv"
)
OPERATIONAL_0604 = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "operational"
    / "outputs"
    / "0604_evaluation"
    / "operational_predictions_with_actual.csv"
)

BASELINE = "hcoef_stable"
REFERENCE = "current_70_30"
PPV8 = "ppv8_service_proxy"
SVC = "svc_numeric_seed_mean"
L10_COL = "l10_seq_pred_log"
L10_CANDIDATE = "l8_seq__full_plus_generated_buckets"

SEED = 20260608
N_FOLDS = 5
N_BOOTSTRAP = 300
STABLE_TEST_P95 = 0.8064
STABLE_0604_P95 = 0.9835


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


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    return np.exp(np.clip(np.asarray(values, dtype=float), np.log(1_000.0), np.log(1_000_000_000_000.0)))


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_price = safe_exp(pred_log)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((actual_log - pred_log) ** 2))),
        "Within_30": float(np.nanmean(ape <= 0.30)),
        "Within_50": float(np.nanmean(ape <= 0.50)),
        "over_2x_n": int(np.nansum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual_price * 0.5)),
    }


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        pred_log,
    )


def metric_row(
    scope: str,
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    stable_metric: dict[str, float],
    reference_metric: dict[str, float],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "scope": scope,
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": n,
        **m,
        "delta_MdAPE_vs_stable": m["MdAPE"] - stable_metric["MdAPE"],
        "delta_MAPE_vs_stable": m["MAPE"] - stable_metric["MAPE"],
        "delta_p95_APE_vs_stable": m["p95_APE"] - stable_metric["p95_APE"],
        "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_metric["RMSE_log"],
        "delta_MdAPE_vs_current70_30": m["MdAPE"] - reference_metric["MdAPE"],
        "delta_MAPE_vs_current70_30": m["MAPE"] - reference_metric["MAPE"],
        "delta_p95_APE_vs_current70_30": m["p95_APE"] - reference_metric["p95_APE"],
        "improve_count_vs_stable": int(m["MdAPE"] < stable_metric["MdAPE"])
        + int(m["MAPE"] < stable_metric["MAPE"])
        + int(m["p95_APE"] < stable_metric["p95_APE"]),
        "improve_count_vs_current70_30": int(m["MdAPE"] < reference_metric["MdAPE"])
        + int(m["MAPE"] < reference_metric["MAPE"])
        + int(m["p95_APE"] < reference_metric["p95_APE"]),
    }
    if extra:
        row.update(extra)
    return row


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def load_l10_quantiles() -> pd.DataFrame:
    l10 = pd.read_csv(PP_L10_PREDICTIONS, low_memory=False)
    q = l10[l10["candidate"].eq(L10_CANDIDATE)].copy()
    keep = ["split", "_track6_row_id", "pred_log", "q10_log", "q50_log", "q90_log", "quantile_width"]
    q = q[keep].rename(
        columns={
            "pred_log": "l10_seq_pred_log_l10",
            "quantile_width": "quantile_width_l10",
        }
    )
    q["l10_price_range_ratio_l10"] = (
        np.exp(q["q90_log"]) - np.exp(q["q10_log"])
    ) / np.clip(np.exp(q["q50_log"]), 1_000.0, None)
    return q.drop_duplicates(["split", "_track6_row_id"])


def load_operational_0604_quantiles() -> pd.DataFrame:
    if not OPERATIONAL_0604.exists():
        return pd.DataFrame()
    op = pd.read_csv(OPERATIONAL_0604, low_memory=False)
    op = op[
        (pd.to_numeric(op["actual_price_krw"], errors="coerce").notna())
        & (pd.to_numeric(op["actual_price_usd_equiv"], errors="coerce") >= 50.0)
        & (op["warm_cold_route"].astype(str).eq("warm"))
    ].copy()
    keep_map = {
        "_track6_row_id": "_track6_row_id",
        "l10_q10_pred_log": "q10_log_operational",
        "l10_q50_pred_log": "q50_log_operational",
        "l10_q90_pred_log": "q90_log_operational",
        "l10_quantile_width": "quantile_width_operational",
        "l10_price_range_ratio": "l10_price_range_ratio_operational",
        "l10_generated_bucket_seq_pred_log": "l10_seq_pred_log_operational",
        "service_confidence_tier": "service_confidence_tier_operational",
        "actual_price_krw": "actual_price_operational",
    }
    cols = [col for col in keep_map if col in op.columns]
    out = op[cols].rename(columns={col: keep_map[col] for col in cols}).drop_duplicates("_track6_row_id")
    out["split"] = "0604_ex50"
    return out


def load_base_frame() -> pd.DataFrame:
    preds = pd.read_csv(HCOEF18_PREDICTIONS, low_memory=False)
    base = preds[
        preds["candidate"].eq(BASELINE)
        & preds["split"].isin(["validation", "test", "0604_ex50"])
    ].copy()
    keep = [
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        BASELINE,
        REFERENCE,
        PPV8,
        SVC,
        L10_COL,
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "title",
        "medium_support_bucket",
        "width_cm",
        "height_cm",
        "area_cm2",
        "log_area",
        "service_confidence_tier",
    ]
    keep = [col for col in keep if col in base.columns]
    base = base[keep].drop_duplicates(["split", "_track6_row_id"]).copy()

    q = load_l10_quantiles()
    base = base.merge(q, on=["split", "_track6_row_id"], how="left")
    for col, fallback in [
        (L10_COL, "l10_seq_pred_log_l10"),
        ("quantile_width", "quantile_width_l10"),
        ("l10_price_range_ratio", "l10_price_range_ratio_l10"),
    ]:
        if col in base.columns and fallback in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(pd.to_numeric(base[fallback], errors="coerce"))

    op_q = load_operational_0604_quantiles()
    if not op_q.empty:
        base = base.merge(op_q, on=["split", "_track6_row_id"], how="left")
        mask = base["split"].eq("0604_ex50")
        for col, fallback in [
            (L10_COL, "l10_seq_pred_log_operational"),
            ("quantile_width", "quantile_width_operational"),
            ("l10_price_range_ratio", "l10_price_range_ratio_operational"),
            ("service_confidence_tier", "service_confidence_tier_operational"),
            ("q10_log", "q10_log_operational"),
            ("q50_log", "q50_log_operational"),
            ("q90_log", "q90_log_operational"),
        ]:
            if col in base.columns and fallback in base.columns:
                base.loc[mask, col] = base.loc[mask, col].fillna(base.loc[mask, fallback])
        if "actual_price_operational" in base.columns:
            actual_op = pd.to_numeric(base["actual_price_operational"], errors="coerce")
            base.loc[mask & actual_op.notna(), "actual_price"] = actual_op[mask & actual_op.notna()]
            base.loc[mask & actual_op.notna(), "actual_log"] = np.log(actual_op[mask & actual_op.notna()].clip(lower=1.0))

    return add_features(base)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = [
        "actual_log",
        "actual_price",
        BASELINE,
        REFERENCE,
        PPV8,
        SVC,
        L10_COL,
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "log_area",
        "area_cm2",
        "width_cm",
        "height_cm",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in ["svc_group_level", "svc_coverage_tier", "service_confidence_tier", "medium_support_bucket"]:
        if col in out.columns:
            out[col] = out[col].fillna("__MISSING__").astype(str)
        else:
            out[col] = "__MISSING__"

    out["svc_group_n"] = out["svc_group_n"].fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    coverage_map = {"high_n": 2.0, "medium_n": 1.0, "low_n": 0.0, "__MISSING__": 0.0, "nan": 0.0}
    out["coverage_numeric"] = out["svc_coverage_tier"].map(coverage_map).fillna(0.0)
    service_conf_map = {"high": 2.0, "medium": 1.0, "low": 0.0, "__MISSING__": 0.0}
    out["service_confidence_numeric"] = out["service_confidence_tier"].map(service_conf_map).fillna(0.0)

    out["current_minus_stable"] = out[REFERENCE] - out[BASELINE]
    out["ppv8_minus_stable"] = out[PPV8] - out[BASELINE]
    out["svc_minus_stable"] = out[SVC] - out[BASELINE]
    out["l10_minus_stable"] = out[L10_COL] - out[BASELINE]
    out["current_minus_ppv8"] = out[REFERENCE] - out[PPV8]
    out["svc_minus_ppv8"] = out[SVC] - out[PPV8]
    pred_cols = [BASELINE, REFERENCE, PPV8, SVC, L10_COL]
    out["pred_spread"] = out[pred_cols].max(axis=1) - out[pred_cols].min(axis=1)
    out["abs_ppv8_stable_gap"] = out["ppv8_minus_stable"].abs()
    out["log_area_filled"] = out["log_area"].fillna(out["log_area"].median())

    val = out[out["split"].eq("validation")]
    q33 = float(val["quantile_width"].quantile(0.33))
    q66 = float(val["quantile_width"].quantile(0.66))
    q80 = float(val["quantile_width"].quantile(0.80))
    spread66 = float(val["pred_spread"].quantile(0.66))
    spread80 = float(val["pred_spread"].quantile(0.80))
    out.attrs["thresholds"] = {
        "qwidth_q33": q33,
        "qwidth_q66": q66,
        "qwidth_q80": q80,
        "pred_spread_q66": spread66,
        "pred_spread_q80": spread80,
    }
    out["qwidth_band"] = pd.cut(
        out["quantile_width"],
        bins=[-np.inf, q33, q66, q80, np.inf],
        labels=["qwidth_low", "qwidth_mid", "qwidth_high", "qwidth_extreme"],
    ).astype(str)
    out["svc_group_n_band"] = pd.cut(
        out["svc_group_n"],
        bins=[-0.1, 4, 9, 19, 49, np.inf],
        labels=["n_0_4", "n_5_9", "n_10_19", "n_20_49", "n_50_plus"],
    ).astype(str)
    out["gap_band"] = pd.cut(
        out["abs_ppv8_stable_gap"],
        bins=[-0.001, 0.03, 0.05, 0.10, 0.20, np.inf],
        labels=["gap_000_003", "gap_003_005", "gap_005_010", "gap_010_020", "gap_020_plus"],
    ).astype(str)
    out["pred_spread_band"] = pd.cut(
        out["pred_spread"],
        bins=[-np.inf, spread66, spread80, np.inf],
        labels=["spread_low_mid", "spread_high", "spread_extreme"],
    ).astype(str)
    out["stable_pred_price"] = safe_exp(out[BASELINE])
    out["stable_pred_price_band"] = pd.qcut(
        out.loc[out["split"].eq("validation"), "stable_pred_price"],
        q=4,
        duplicates="drop",
    )
    # Re-apply validation price-band edges to all splits for diagnostics.
    bins = pd.qcut(out.loc[out["split"].eq("validation"), "stable_pred_price"], q=4, retbins=True, duplicates="drop")[1]
    bins[0] = -np.inf
    bins[-1] = np.inf
    out["stable_pred_price_band"] = pd.cut(out["stable_pred_price"], bins=bins, include_lowest=True).astype(str)
    return out.reset_index(drop=True)


def build_candidate_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = [
        CandidateConfig(BASELINE, "source", source_col=BASELINE, purpose="현재 HCOEF 안정 후보"),
        CandidateConfig(REFERENCE, "source", source_col=REFERENCE, purpose="서비스 v0.1 70:30 기준 후보"),
        CandidateConfig(PPV8, "source", source_col=PPV8, purpose="PP-V8/service component proxy"),
        CandidateConfig(SVC, "source", source_col=SVC, purpose="유사 작품 기반 가격 피처"),
        CandidateConfig("l10_seq_full_generated_bucket", "source", source_col=L10_COL, purpose="PP-L10 순차 component"),
    ]
    feature_sets = {
        "component_gaps": (
            "current_minus_stable",
            "ppv8_minus_stable",
            "svc_minus_stable",
            "l10_minus_stable",
            "pred_spread",
        ),
        "qwidth_reliability": (
            "quantile_width",
            "l10_price_range_ratio",
            "svc_group_n_log",
            "coverage_numeric",
            "pred_spread",
        ),
        "component_gaps_qwidth": (
            "current_minus_stable",
            "ppv8_minus_stable",
            "svc_minus_stable",
            "l10_minus_stable",
            "pred_spread",
            "quantile_width",
            "l10_price_range_ratio",
            "svc_group_n_log",
            "coverage_numeric",
            "log_area_filled",
        ),
    }
    for fs_name, features in feature_sets.items():
        for alpha in [0.001, 0.01]:
            for cap in [0.02, 0.03, 0.05]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=f"hcoef20_resid_huber_{fs_name}_a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}",
                            method="residual_huber",
                            features=features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="HCOEF 안정 후보 위에 작은 Huber 잔차 보정",
                        )
                    )
    for fs_name, features in {
        "component_gaps_qwidth": feature_sets["component_gaps_qwidth"],
        "qwidth_reliability": feature_sets["qwidth_reliability"],
    }.items():
        for alpha in [0.1, 1.0]:
            for cap in [0.02, 0.03]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=f"hcoef20_resid_ridge_{fs_name}_a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}",
                            method="residual_ridge",
                            features=features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="Huber보다 부드러운 Ridge 잔차 보정 대조군",
                        )
                    )
    direct_features = (
        BASELINE,
        REFERENCE,
        PPV8,
        SVC,
        L10_COL,
        "quantile_width",
        "svc_group_n_log",
        "coverage_numeric",
        "pred_spread",
    )
    for method, alphas in [("direct_huber", [0.001, 0.01]), ("direct_ridge", [0.1, 1.0])]:
        for alpha in alphas:
            configs.append(
                CandidateConfig(
                    candidate=f"hcoef20_{method}_component_stack_a{slug_float(alpha)}",
                    method=method,
                    features=direct_features,
                    alpha=alpha,
                    purpose="기준가/component 자체를 저차원 선형 stack으로 직접 재학습",
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
    return np.asarray(raw, dtype=float), np.asarray(raw, dtype=float) - frame[BASELINE].to_numpy(dtype=float)


def split_iter(frame: pd.DataFrame, scheme: str):
    if scheme == "row":
        splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        yield from splitter.split(frame)
        return
    groups = frame["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    n_groups = len(np.unique(groups))
    if n_groups < N_FOLDS:
        splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        yield from splitter.split(frame)
        return
    splitter = GroupKFold(n_splits=N_FOLDS)
    yield from splitter.split(frame, groups=groups)


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
        for train_idx, hold_idx in split_iter(validation, scheme):
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
    pred_price = safe_exp(pred)
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
        stable_metric = metric(validation, pred_map[BASELINE][0])
        reference_metric = metric(validation, pred_map[REFERENCE][0])
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = metric(validation, pred)
            metric_rows.append(
                metric_row(
                    scope=f"validation_oof_{scheme}",
                    split="validation",
                    candidate=config.candidate,
                    method=config.method,
                    n=len(validation),
                    m=m,
                    stable_metric=stable_metric,
                    reference_metric=reference_metric,
                    extra={
                        "mean_policy_move_log": float(np.nanmean(move)),
                        "mean_abs_policy_move_log": float(np.nanmean(np.abs(move))),
                    },
                )
            )
            prediction_rows.append(prediction_frame(f"validation_oof_{scheme}", "validation", validation, config, pred, move))

    for split, frame in [("test", test), ("0604_ex50", stress)]:
        pred_map = fixed_predictions(validation, frame, configs)
        stable_metric = metric(frame, pred_map[BASELINE][0])
        reference_metric = metric(frame, pred_map[REFERENCE][0])
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = metric(frame, pred)
            metric_rows.append(
                metric_row(
                    scope="fixed_confirmation" if split == "test" else "0604_stress",
                    split=split,
                    candidate=config.candidate,
                    method=config.method,
                    n=len(frame),
                    m=m,
                    stable_metric=stable_metric,
                    reference_metric=reference_metric,
                    extra={
                        "mean_policy_move_log": float(np.nanmean(move)),
                        "mean_abs_policy_move_log": float(np.nanmean(np.abs(move))),
                    },
                )
            )
            prediction_rows.append(
                prediction_frame("fixed_confirmation" if split == "test" else "0604_stress", split, frame, config, pred, move)
            )
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)


def bootstrap_summary(predictions: pd.DataFrame, configs: list[CandidateConfig]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(SEED)
    for scope in ["validation_oof_row", "validation_oof_artist"]:
        focus = predictions[predictions["scope"].eq(scope)].copy()
        if focus.empty:
            continue
        pivot = focus.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
        meta = focus.drop_duplicates("_track6_row_id").set_index("_track6_row_id")
        common = pivot.index[pivot[BASELINE].notna()]
        pivot = pivot.loc[common]
        meta = meta.loc[common]
        actual_price = meta["actual_price"].to_numpy(dtype=float)
        actual_log = meta["actual_log"].to_numpy(dtype=float)
        artists = meta["artist_key"].astype(str).to_numpy()
        unique_artists = np.unique(artists)
        for scheme in ["row_bootstrap", "artist_bootstrap"]:
            deltas: dict[str, list[tuple[float, float, float, float]]] = {config.candidate: [] for config in configs}
            stable_pred = pivot[BASELINE].to_numpy(dtype=float)
            for _ in range(N_BOOTSTRAP):
                if scheme == "row_bootstrap":
                    idx = rng.integers(0, len(pivot), len(pivot))
                else:
                    sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                    idx = np.concatenate([np.flatnonzero(artists == artist) for artist in sampled_artists])
                    if len(idx) == 0:
                        continue
                stable_m = metric_from_arrays(actual_price[idx], actual_log[idx], stable_pred[idx])
                for config in configs:
                    pred = pivot[config.candidate].to_numpy(dtype=float)
                    m = metric_from_arrays(actual_price[idx], actual_log[idx], pred[idx])
                    deltas[config.candidate].append(
                        (
                            m["MdAPE"] - stable_m["MdAPE"],
                            m["MAPE"] - stable_m["MAPE"],
                            m["p95_APE"] - stable_m["p95_APE"],
                            m["RMSE_log"] - stable_m["RMSE_log"],
                        )
                    )
            for config in configs:
                arr = np.asarray(deltas[config.candidate], dtype=float)
                if arr.size == 0:
                    continue
                rows.append(
                    {
                        "source_scope": scope,
                        "validation_scheme": scheme,
                        "candidate": config.candidate,
                        "method": config.method,
                        "n_bootstrap": len(arr),
                        "mean_delta_MdAPE_vs_stable": float(arr[:, 0].mean()),
                        "mean_delta_MAPE_vs_stable": float(arr[:, 1].mean()),
                        "mean_delta_p95_APE_vs_stable": float(arr[:, 2].mean()),
                        "mean_delta_RMSE_log_vs_stable": float(arr[:, 3].mean()),
                        "MdAPE_improve_prob": float((arr[:, 0] < 0).mean()),
                        "MAPE_improve_prob": float((arr[:, 1] < 0).mean()),
                        "p95_improve_prob": float((arr[:, 2] < 0).mean()),
                        "all3_improve_prob": float(((arr[:, 0] < 0) & (arr[:, 1] < 0) & (arr[:, 2] < 0)).mean()),
                        "any2_improve_prob": float(
                            (
                                (arr[:, 0] < 0).astype(int)
                                + (arr[:, 1] < 0).astype(int)
                                + (arr[:, 2] < 0).astype(int)
                                >= 2
                            ).mean()
                        ),
                    }
                )
    return pd.DataFrame(rows)


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
                    "interpretation": feature_interpretation(feature, coef, config),
                }
            )
    return pd.DataFrame(rows)


def feature_interpretation(feature: str, coef: float, config: CandidateConfig) -> str:
    if feature == "current_minus_stable":
        return "70:30 기준 후보가 HCOEF 안정 후보보다 높거나 낮은 방향을 잔차 보정에 반영한다."
    if feature == "ppv8_minus_stable":
        return "PP-V8 component와 HCOEF 안정 후보의 차이를 제한적으로 반영한다."
    if feature == "svc_minus_stable":
        return "유사 작품 기반 가격 피처와 안정 후보의 차이를 작게 반영한다."
    if feature == "l10_minus_stable":
        return "PP-L10 순차 component가 안정 후보와 다른 방향을 보조 신호로 쓴다."
    if feature == "quantile_width":
        return "예측 범위가 넓은 샘플에서 residual 보정 방향이 달라지는지 확인한다."
    if feature == "l10_price_range_ratio":
        return "가격 범위가 넓을수록 불확실성이 크다는 신호로 해석한다."
    if feature == "svc_group_n_log":
        return "유사 표본 수가 많을수록 기준가 신뢰도가 높다는 신호다."
    if feature == "coverage_numeric":
        return "유사 표본 수 coverage tier를 숫자로 바꾼 신뢰도 피처다."
    if feature == "pred_spread":
        return "component 간 예측값 차이가 큰 샘플의 위험도를 나타낸다."
    if feature in {BASELINE, REFERENCE, PPV8, SVC, L10_COL}:
        return "기준가 또는 component 자체의 저차원 선형 stack 계수다."
    return f"표준화 계수 {coef:.4f}로 잔차 또는 로그 가격을 보조한다."


def selection_table(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    def metric_slice(scope: str, prefix: str) -> pd.DataFrame:
        cols = [
            "candidate",
            "method",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "improve_count_vs_stable",
            "improve_count_vs_current70_30",
        ]
        return metrics_df[metrics_df["scope"].eq(scope)][cols].rename(
            columns={
                "MdAPE": f"{prefix}_MdAPE",
                "MAPE": f"{prefix}_MAPE",
                "p95_APE": f"{prefix}_p95_APE",
                "RMSE_log": f"{prefix}_RMSE_log",
                "delta_MdAPE_vs_stable": f"{prefix}_delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable": f"{prefix}_delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable": f"{prefix}_delta_p95_APE_vs_stable",
                "improve_count_vs_stable": f"{prefix}_improve_count_vs_stable",
                "improve_count_vs_current70_30": f"{prefix}_improve_count_vs_current70_30",
            }
        )

    out = metric_slice("validation_oof_row", "row_oof")
    for scope, prefix in [
        ("validation_oof_artist", "artist_oof"),
        ("fixed_confirmation", "test"),
        ("0604_stress", "stress0604"),
    ]:
        out = out.merge(metric_slice(scope, prefix).drop(columns=["method"], errors="ignore"), on="candidate", how="left")

    boot = bootstrap_df.pivot_table(
        index="candidate",
        columns=["source_scope", "validation_scheme"],
        values=["all3_improve_prob", "any2_improve_prob"],
        aggfunc="first",
    )
    if not boot.empty:
        boot.columns = [f"{scope}_{scheme}_{metric}" for metric, scope, scheme in boot.columns]
        out = out.merge(boot.reset_index(), on="candidate", how="left")

    row_all3 = out.get("validation_oof_row_row_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    artist_all3 = out.get("validation_oof_artist_artist_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    row_any2 = out.get("validation_oof_row_row_bootstrap_any2_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    artist_any2 = out.get("validation_oof_artist_artist_bootstrap_any2_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)

    out["bootstrap_all3_gate"] = (row_all3 >= 0.90) & (artist_all3 >= 0.90)
    out["bootstrap_any2_gate"] = (row_any2 >= 0.90) & (artist_any2 >= 0.90)
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= STABLE_TEST_P95
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= STABLE_0604_P95
    out["fixed_test_2of3"] = out["test_improve_count_vs_stable"] >= 2
    out["row_artist_2of3"] = (out["row_oof_improve_count_vs_stable"] >= 2) & (out["artist_oof_improve_count_vs_stable"] >= 2)

    conditions = [
        out["bootstrap_all3_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
        out["bootstrap_any2_gate"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"],
        out["test_MAPE"].lt(out["test_MAPE"].where(out["candidate"].eq(BASELINE)).min()) & out["fixed_test_p95_guard"],
        out["test_p95_APE"].lt(out["test_p95_APE"].where(out["candidate"].eq(BASELINE)).min()) & (out["test_MdAPE"] <= out["test_MdAPE"].where(out["candidate"].eq(BASELINE)).min() + 0.003),
        out["row_artist_2of3"],
    ]
    choices = ["운영 후보 검토", "반복 검증 통과 후보", "MAPE 특화 후보", "p95 방어 후보", "OOF 개선 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    out.loc[out["candidate"].eq(BASELINE), "decision"] = "현재 기준 후보"
    out.loc[out["candidate"].eq(REFERENCE), "decision"] = "최소 비교 기준"
    source_component = out["method"].eq("source") & ~out["candidate"].isin([BASELINE, REFERENCE])
    out.loc[source_component, "decision"] = "component 대조군"
    decision_order = {
        "현재 기준 후보": 0,
        "운영 후보 검토": 1,
        "반복 검증 통과 후보": 2,
        "MAPE 특화 후보": 3,
        "p95 방어 후보": 4,
        "OOF 개선 후보": 5,
        "최소 비교 기준": 6,
        "component 대조군": 7,
        "보류": 8,
    }
    out["decision_order"] = out["decision"].map(decision_order).fillna(9)
    return out.sort_values(["decision_order", "test_MdAPE", "test_MAPE", "test_p95_APE"]).drop(columns=["decision_order"])


def confidence_tier(frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.Series:
    q = pd.to_numeric(frame["quantile_width"], errors="coerce")
    n = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0.0)
    high = (q <= thresholds["qwidth_q33"]) & (n >= 20)
    medium = (q <= thresholds["qwidth_q66"]) & (n >= 10)
    return pd.Series(np.where(high, "high", np.where(medium, "medium", "low")), index=frame.index)


def range_confidence_policy(base: pd.DataFrame) -> pd.DataFrame:
    thresholds = base.attrs.get("thresholds", {})
    rows: list[dict[str, Any]] = []
    for split, frame in base.groupby("split", sort=False):
        frame = frame.copy()
        frame["range_confidence_tier"] = confidence_tier(frame, thresholds)
        for tier, group in frame.groupby("range_confidence_tier", dropna=False):
            if len(group) < 5:
                continue
            has_interval = group[["q10_log", "q90_log"]].notna().all(axis=1) if {"q10_log", "q90_log"}.issubset(group.columns) else pd.Series(False, index=group.index)
            interval_group = group[has_interval]
            stable_m = metric(group, group[BASELINE].to_numpy(dtype=float))
            coverage = np.nan
            median_range_ratio = float(group["l10_price_range_ratio"].median())
            if not interval_group.empty:
                coverage = float(
                    (
                        (interval_group["actual_log"] >= interval_group["q10_log"])
                        & (interval_group["actual_log"] <= interval_group["q90_log"])
                    ).mean()
                )
            rows.append(
                {
                    "split": split,
                    "range_confidence_tier": tier,
                    "n": len(group),
                    "q10_q90_coverage": coverage,
                    "median_quantile_width": float(group["quantile_width"].median()),
                    "median_price_range_ratio": median_range_ratio,
                    "stable_MdAPE": stable_m["MdAPE"],
                    "stable_MAPE": stable_m["MAPE"],
                    "stable_p95_APE": stable_m["p95_APE"],
                    "over_50pct_error_rate": float(
                        (
                            np.abs(safe_exp(group[BASELINE]) - group["actual_price"].to_numpy(dtype=float))
                            / np.clip(group["actual_price"].to_numpy(dtype=float), 1.0, None)
                            > 0.50
                        ).mean()
                    ),
                    "policy_rule": "high: qwidth<=validation q33 and svc_group_n>=20; medium: qwidth<=validation q66 and svc_group_n>=10; else low",
                }
            )
    return pd.DataFrame(rows)


def residual_analysis(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    focus_candidates = list(dict.fromkeys([BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket", *selected]))
    focus = predictions[predictions["candidate"].isin(focus_candidates)].copy()
    rows: list[dict[str, Any]] = []
    segment_cols = [
        "qwidth_band",
        "svc_group_n_band",
        "svc_coverage_tier",
        "svc_group_level",
        "gap_band",
        "pred_spread_band",
        "stable_pred_price_band",
        "medium_support_bucket",
    ]
    for col in segment_cols:
        if col not in focus.columns:
            continue
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


def policy_map(configs: list[CandidateConfig], thresholds: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = [
        {
            "policy_item": "candidate_selection",
            "candidate": "__global__",
            "method": "validation_first",
            "details": "Validation OOF/bootstrap에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.",
            "threshold_or_value": "",
        },
        {
            "policy_item": "range_confidence",
            "candidate": "__service_policy__",
            "method": "quantile_width_tier",
            "details": "Quantile width는 점 예측 이동보다 가격 범위/신뢰도 표시 정책으로 우선 사용.",
            "threshold_or_value": json.dumps(thresholds, ensure_ascii=False),
        },
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


def markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    show = df.head(max_rows).copy()
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(markdown_cell(row[col]) for col in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(df)} rows shown._")
    return "\n".join(lines)


def md_to_html(markdown: str) -> str:
    lines: list[str] = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("| ") and line.endswith(" |"):
            cells = [html.escape(c.strip()) for c in line.strip("|").split("|")]
            if not in_table:
                lines.append("<table>")
                in_table = True
                lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            elif set(cells[0]) <= {"-"}:
                continue
            else:
                lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            lines.append("</table>")
            in_table = False
        if line.startswith("# "):
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            lines.append(f"<p>{html.escape(line)}</p>")
        elif not line:
            lines.append("")
        else:
            lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        lines.append("</table>")
    style = """
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 28px; color: #1f2933; }
    h1, h2, h3 { color: #17202a; }
    table { border-collapse: collapse; width: 100%; margin: 14px 0 24px; font-size: 13px; }
    th, td { border: 1px solid #d7dee8; padding: 7px 9px; text-align: left; vertical-align: top; }
    th { background: #eef3f8; }
    p { line-height: 1.55; }
    code { background: #eef3f8; padding: 1px 3px; border-radius: 3px; }
    </style>
    """
    return "<!doctype html><html><head><meta charset='utf-8'>" + style + "</head><body>" + "\n".join(lines) + "</body></html>"


def render_report(
    metrics_df: pd.DataFrame,
    selection: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
    range_policy: pd.DataFrame,
    thresholds: dict[str, float],
) -> str:
    test_top = metrics_df[metrics_df["scope"].eq("fixed_confirmation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    row_top = metrics_df[metrics_df["scope"].eq("validation_oof_row")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    artist_top = metrics_df[metrics_df["scope"].eq("validation_oof_artist")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    stress_top = metrics_df[metrics_df["scope"].eq("0604_stress")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    selected_top = selection.head(30)
    selected_candidates = selected_top["candidate"].tolist()
    boot_focus = bootstrap_df[bootstrap_df["candidate"].isin(selected_candidates + [BASELINE, REFERENCE])].copy()
    coef_focus = coefficients[coefficients["candidate"].isin(selected_candidates[:8] + [BASELINE, REFERENCE])].copy()
    residual_focus = residuals[residuals["candidate"].isin(selected_candidates[:6] + [BASELINE, REFERENCE])].copy()
    return "\n".join(
        [
            "# PP-HCOEF20 Warm Huber 기준가/계수 재탐색",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF 안정 후보를 기본값으로 두고, 운영 component/신뢰도/gap 피처만 사용해 저차원 Huber 계수 보정 후보를 검증.",
            "- 기준 후보: `hcoef_stable` = `hcoef2_size_reliability_cap005_s050`.",
            "- 최소 비교 기준: `current_70_30`.",
            "- 0604는 외부 stress test이며 후보 선택에는 사용하지 않음.",
            "",
            "## 1. Validation에서 고정한 위험도 경계",
            "",
            markdown_table(pd.DataFrame([thresholds]).round(4), 5),
            "",
            "## 2. 실행 결론",
            "",
            "- 점 예측 후보는 validation row OOF, validation artist OOF, bootstrap을 우선해 판단.",
            "- fixed test와 0604가 좋아도 OOF/bootstrap이 약하면 운영 후보로 승격하지 않음.",
            "- quantile width는 점 예측을 직접 움직이기보다 가격 범위와 신뢰도 표시 정책으로 별도 분리.",
            "- Huber 계수는 기준가/component 간 gap, 표본 수 신뢰도, quantile width를 표준화한 뒤 residual_log를 작게 보정하는 방식으로 학습.",
            "",
            "## 3. 후보 선택표",
            "",
            markdown_table(
                selected_top[
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
                ].round(4),
                30,
            ),
            "",
            "## 4. Fixed Test 상위 후보",
            "",
            markdown_table(
                test_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "improve_count_vs_stable",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 5. Validation Row OOF 상위 후보",
            "",
            markdown_table(
                row_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "improve_count_vs_stable",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 6. Validation Artist OOF 상위 후보",
            "",
            markdown_table(
                artist_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "improve_count_vs_stable",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 7. 0604 Stress Test 상위 후보",
            "",
            markdown_table(
                stress_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "improve_count_vs_stable",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 8. Bootstrap 요약",
            "",
            markdown_table(
                boot_focus.sort_values(["source_scope", "validation_scheme", "all3_improve_prob"], ascending=[True, True, False]).round(4),
                60,
            ),
            "",
            "## 9. 가격 범위/신뢰도 정책",
            "",
            markdown_table(range_policy.round(4), 60),
            "",
            "## 10. 주요 계수 해석",
            "",
            markdown_table(coef_focus.sort_values(["candidate", "standardized_coefficient"], ascending=[True, False]).round(4), 80),
            "",
            "## 11. 구간별 잔차 요약",
            "",
            markdown_table(residual_focus.head(80).round(4), 80),
            "",
            "## 12. 판단",
            "",
            "- 운영 기본 후보가 되려면 HCOEF 안정 후보 대비 row OOF, artist OOF, fixed test에서 MdAPE/MAPE/p95가 모두 동등 또는 개선되어야 함.",
            "- MAPE 특화 후보와 p95 방어 후보는 운영 기본 후보와 분리해 목적별 후보로만 관리.",
            "- quantile width는 점 예측 이동 기준으로 바로 쓰지 않고, 가격 범위/신뢰도 표시 정책으로 따로 관리하는 것이 현재 실험 원칙에 맞음.",
            "",
            "## 13. 산출물",
            "",
            "- `artifacts/experiment_config.json`",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/range_confidence_policy.csv`",
            "- `outputs/selected_candidates.csv`",
        ]
    )


def main() -> None:
    ensure_dirs()
    base = load_base_frame()
    thresholds = base.attrs.get("thresholds", {})
    configs = build_candidate_configs()
    metrics_df, predictions = evaluate_all(base, configs)
    bootstrap_df = bootstrap_summary(predictions, configs)
    selection = selection_table(metrics_df, bootstrap_df)
    selected = selection.head(12)["candidate"].tolist()
    coefficients = coefficient_table(base[base["split"].eq("validation")].reset_index(drop=True), configs, selected)
    residuals = residual_analysis(predictions, selected)
    range_policy = range_confidence_policy(base)
    policies = policy_map(configs, thresholds)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    policies.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    range_policy.to_csv(EXP_DIR / "outputs" / "range_confidence_policy.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Warm Huber low-dimensional residual coefficient search and quantile range/confidence policy",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "candidate_count": len(configs),
        "n_folds": N_FOLDS,
        "n_bootstrap": N_BOOTSTRAP,
        "threshold_source": "validation split only",
        "thresholds": thresholds,
        "inputs": {
            "hcoef18_predictions": str(HCOEF18_PREDICTIONS.relative_to(REPO)),
            "pp_l10_predictions": str(PP_L10_PREDICTIONS.relative_to(REPO)),
            "operational_0604": str(OPERATIONAL_0604.relative_to(REPO)),
        },
        "candidate_configs": [config.__dict__ for config in configs],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_report(metrics_df, selection, bootstrap_df, coefficients, residuals, range_policy, thresholds)
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(report), encoding="utf-8")
    summary_path = DOC_ROOT / "pp_hcoef20_warm_huber_price_basis_coefficient_refinement_summary.md"
    summary_path.write_text(report, encoding="utf-8")
    summary_path.with_suffix(".html").write_text(md_to_html(report), encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(
        selection[
            [
                "candidate",
                "method",
                "decision",
                "test_MdAPE",
                "test_MAPE",
                "test_p95_APE",
                "stress0604_MdAPE",
                "stress0604_MAPE",
                "stress0604_p95_APE",
            ]
        ]
        .head(20)
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
