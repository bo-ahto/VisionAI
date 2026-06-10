#!/usr/bin/env python3
"""Run PP-HCOEF16: OOF validation of PP-V8/service component as Huber inputs.

PP-HCOEF15 showed that the operational PP-V8/service-primary component is
strong on the 0604 latest-label stress set. This script does not select a new
candidate from 0604. Instead, it tests whether PP-V8-style predictions help as
low-dimensional Huber residual features under validation OOF and artist OOF.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import warnings


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF16"
EXP_SLUG = "PP-HCOEF16_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

SVC3_PREDICTIONS = REPO / "experiments" / "track6" / "PP-SVC3_warm_svc_blend_routing" / "outputs" / "predictions.csv"
V8_PREDICTIONS = REPO / "experiments" / "track6" / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv"
HCOEF3_PREDICTIONS = REPO / "experiments" / "track6" / "PP-HCOEF3_warm_huber_residual_repeated_validation" / "outputs" / "candidate_predictions.csv"
HCOEF15_PREDICTIONS = REPO / "experiments" / "track6" / "PP-HCOEF15_warm_huber_price_basis_coefficient_refinement" / "outputs" / "candidate_predictions.csv"
OPERATIONAL_0604 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

REFERENCE = "current_70_30"
STABLE = "hcoef2_size_reliability_cap005_s050"
BASELINE = "hcoef_stable"
PPV8 = "ppv8_service_proxy"

SEED = 20260608
N_REPEATS = 20
N_FOLDS = 5

DIRECT_CANDIDATES = [
    {
        "candidate": "hcoef16_ppv8_proxy_direct",
        "kind": "direct",
        "weight_ppv8": 1.0,
        "description": "PP-V8/service component 단독. 0604에서는 강하지만 fixed test/OOF 대조군으로만 사용.",
    },
    {
        "candidate": "hcoef16_stable_ppv8_blend_w010",
        "kind": "direct",
        "weight_ppv8": 0.10,
        "description": "HCOEF 안정 후보 90% + PP-V8 10% 제한 결합.",
    },
    {
        "candidate": "hcoef16_stable_ppv8_blend_w025",
        "kind": "direct",
        "weight_ppv8": 0.25,
        "description": "HCOEF 안정 후보 75% + PP-V8 25% 제한 결합.",
    },
    {
        "candidate": "hcoef16_stable_ppv8_blend_w050",
        "kind": "direct",
        "weight_ppv8": 0.50,
        "description": "HCOEF 안정 후보 50% + PP-V8 50% 공격형 결합.",
    },
]

FEATURE_SETS: dict[str, list[str]] = {
    "ppv8_pred_stack": [
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
    ],
    "ppv8_gap_reliability": [
        "stable_ppv8_gap",
        "current_ppv8_gap",
        "svc_ppv8_gap",
        "pred_spread",
        "svc_group_n_log",
        "coverage_numeric",
    ],
    "ppv8_core_reliability": [
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "stable_ppv8_gap",
        "current_ppv8_gap",
        "svc_group_n_log",
        "coverage_numeric",
    ],
}

RESIDUAL_CONFIGS: list[dict[str, Any]] = []
for feature_key in ["ppv8_pred_stack", "ppv8_gap_reliability", "ppv8_core_reliability"]:
    for alpha in [0.001, 0.01]:
        for cap in [0.02, 0.03, 0.05]:
            for strength in [0.25, 0.50]:
                RESIDUAL_CONFIGS.append(
                    {
                        "candidate": f"hcoef16_resid_{feature_key}_alpha{str(alpha).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}_s{str(strength).replace('.', 'p')}",
                        "kind": "residual_huber",
                        "feature_key": feature_key,
                        "alpha": alpha,
                        "cap": cap,
                        "strength": strength,
                        "description": f"{feature_key} 피처 기반 Huber residual 보정, cap {cap}, strength {strength}.",
                    }
                )

CANDIDATES = [*DIRECT_CANDIDATES, *RESIDUAL_CONFIGS]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
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
        np.asarray(pred_log, dtype=float),
    )


def load_validation_test_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    svc = pd.read_csv(SVC3_PREDICTIONS, low_memory=False)
    svc = svc[svc["split"].isin(["validation", "test"])].copy()
    meta_cols = [
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    meta = svc[meta_cols].drop_duplicates(["split", "_track6_row_id"])
    svc_wide = (
        svc.pivot_table(
            index=["split", "_track6_row_id"],
            columns="candidate",
            values="pred_log",
            aggfunc="last",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    svc_wide = svc_wide.rename(
        columns={
            "svc_numeric_seed_mean": "svc_numeric_seed_mean",
            "pp_v8_compact_blend_mape_guarded": PPV8,
            "blend_svcnum_ppv8_wsvc_0.70": "svc70_ppv8_30",
        }
    )

    hcoef = pd.read_csv(HCOEF3_PREDICTIONS, low_memory=False)
    hcoef = hcoef[hcoef["split"].isin(["validation", "test"]) & hcoef["candidate"].isin([REFERENCE, STABLE])].copy()
    h_wide = (
        hcoef.pivot_table(
            index=["split", "_track6_row_id"],
            columns="candidate",
            values="pred_log",
            aggfunc="last",
        )
        .reset_index()
        .rename_axis(None, axis=1)
        .rename(columns={REFERENCE: "current_70_30", STABLE: "hcoef_stable"})
    )
    out = meta.merge(svc_wide, on=["split", "_track6_row_id"], how="inner").merge(
        h_wide, on=["split", "_track6_row_id"], how="inner"
    )
    out = add_features(out)
    validation = out[out["split"].eq("validation")].reset_index(drop=True)
    test = out[out["split"].eq("test")].reset_index(drop=True)

    v8 = pd.read_csv(V8_PREDICTIONS, low_memory=False)
    v8_compact = v8[v8["candidate"].eq("compact_blend_mape_guarded")][["split", "_track6_row_id", "pred_log"]].rename(
        columns={"pred_log": "pp_v8_from_ppv8_file"}
    )
    audit = out[["split", "_track6_row_id", PPV8]].merge(v8_compact, on=["split", "_track6_row_id"], how="inner")
    audit["abs_diff"] = (audit[PPV8] - audit["pp_v8_from_ppv8_file"]).abs()
    return validation, test, audit


def load_0604_frame() -> pd.DataFrame:
    preds = pd.read_csv(HCOEF15_PREDICTIONS, low_memory=False)
    base = (
        preds[[
            "_track6_row_id",
            "artist_key",
            "artist_name_ko",
            "actual_price_krw",
            "actual_log_krw",
            "svc_group_level",
            "svc_coverage_tier",
            "svc_group_n",
            "l10_price_range_ratio",
            "title",
        ]]
        .drop_duplicates("_track6_row_id")
        .rename(
            columns={
                "actual_price_krw": "actual_price",
                "actual_log_krw": "actual_log",
            }
        )
    )
    wide = (
        preds.pivot_table(
            index="_track6_row_id",
            columns="candidate",
            values="pred_log_krw",
            aggfunc="last",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    wide = wide.rename(
        columns={
            "current_70_30": "current_70_30",
            STABLE: "hcoef_stable",
            "service_primary_ppv8_operational": PPV8,
            "svc_numeric_seed_mean": "svc_numeric_seed_mean",
        }
    )
    if PPV8 not in wide.columns and "pp_v8_compact_blend_mape_guarded_operational" in wide.columns:
        wide[PPV8] = wide["pp_v8_compact_blend_mape_guarded_operational"]
    out = base.merge(wide, on="_track6_row_id", how="inner")

    operational = pd.read_csv(OPERATIONAL_0604, low_memory=False)
    if "pp_v8_compact_blend_mape_guarded_pred_log" in operational.columns:
        audit = operational[["_track6_row_id", "pp_v8_compact_blend_mape_guarded_pred_log"]].copy()
        out = out.merge(audit, on="_track6_row_id", how="left")
        out["ppv8_service_abs_diff"] = (out[PPV8] - out["pp_v8_compact_blend_mape_guarded_pred_log"]).abs()
    else:
        out["ppv8_service_abs_diff"] = np.nan
    out["split"] = "0604_ex50"
    return add_features(out)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in ["svc_group_level", "svc_coverage_tier"]:
        if col not in out.columns:
            out[col] = "__MISSING__"
        out[col] = out[col].fillna("__MISSING__").astype(str)
    out["svc_group_n"] = pd.to_numeric(out.get("svc_group_n", np.nan), errors="coerce").fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    coverage_map = {
        "high_n": 2.0,
        "medium_n": 1.0,
        "low_n": 0.0,
        "__MISSING__": 0.0,
        "nan": 0.0,
    }
    out["coverage_numeric"] = out["svc_coverage_tier"].map(coverage_map).fillna(0.0)
    required = ["current_70_30", "hcoef_stable", PPV8, "svc_numeric_seed_mean"]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise ValueError(f"Missing required prediction columns: {missing}")
    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["stable_ppv8_gap"] = out["hcoef_stable"] - out[PPV8]
    out["current_ppv8_gap"] = out["current_70_30"] - out[PPV8]
    out["svc_ppv8_gap"] = out["svc_numeric_seed_mean"] - out[PPV8]
    pred_cols = ["current_70_30", "hcoef_stable", PPV8, "svc_numeric_seed_mean"]
    out["pred_spread"] = out[pred_cols].max(axis=1) - out[pred_cols].min(axis=1)
    return out


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(n))
    folds = np.array_split(order, N_FOLDS)
    all_idx = np.arange(n)
    return [(np.setdiff1d(all_idx, hold, assume_unique=False), hold) for hold in folds]


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    artists = frame["artist_key"].astype(str).to_numpy()
    unique = rng.permutation(np.unique(artists))
    fold_of = {artist: idx % N_FOLDS for idx, artist in enumerate(unique)}
    all_idx = np.arange(len(frame))
    out = []
    for fold_id in range(N_FOLDS):
        hold = np.flatnonzero([fold_of[artist] == fold_id for artist in artists])
        train = np.setdiff1d(all_idx, hold, assume_unique=False)
        out.append((train, hold))
    return out


def direct_prediction(frame: pd.DataFrame, config: dict[str, Any]) -> np.ndarray:
    weight = float(config["weight_ppv8"])
    if weight >= 1.0:
        return frame[PPV8].to_numpy(dtype=float)
    return (1.0 - weight) * frame[BASELINE].to_numpy(dtype=float) + weight * frame[PPV8].to_numpy(dtype=float)


def fit_residual_model(train: pd.DataFrame, config: dict[str, Any]):
    features = FEATURE_SETS[config["feature_key"]]
    target = train["actual_log"].to_numpy(dtype=float) - train[BASELINE].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model = make_pipeline(
            StandardScaler(),
            HuberRegressor(alpha=float(config["alpha"]), epsilon=1.35, max_iter=1000),
        )
        model.fit(train[features], target)
    return model


def residual_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, Any]:
    features = FEATURE_SETS[config["feature_key"]]
    model = fit_residual_model(train, config)
    raw = np.asarray(model.predict(eval_frame[features]), dtype=float)
    correction = np.clip(raw, -float(config["cap"]), float(config["cap"])) * float(config["strength"])
    pred = eval_frame[BASELINE].to_numpy(dtype=float) + correction
    return pred, model


def predict_candidate(train: pd.DataFrame, eval_frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, Any | None]:
    if config["kind"] == "direct":
        return direct_prediction(eval_frame, config), None
    return residual_prediction(train, eval_frame, config)


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray, method: str) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": frame["actual_price"].to_numpy(dtype=float),
            "pred_log": np.asarray(pred_log, dtype=float),
            "pred_price": np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None),
            "hcoef_stable": frame[BASELINE].to_numpy(dtype=float),
            "current_70_30": frame["current_70_30"].to_numpy(dtype=float),
            "ppv8_service_proxy": frame[PPV8].to_numpy(dtype=float),
            "svc_numeric_seed_mean": frame["svc_numeric_seed_mean"].to_numpy(dtype=float),
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    residual_rows: list[dict[str, Any]] = []
    baselines = [
        ("current_70_30", "baseline_reference", "current_70_30"),
        ("hcoef_stable", "baseline_stable", BASELINE),
        ("ppv8_service_proxy", "component", PPV8),
        ("svc_numeric_seed_mean", "component", "svc_numeric_seed_mean"),
    ]
    for split, frame in frames.items():
        stable_metric = metric(frame, frame[BASELINE].to_numpy(dtype=float))
        for candidate, method, col in baselines:
            pred = frame[col].to_numpy(dtype=float)
            m = metric(frame, pred)
            metric_rows.append(metric_row(split, candidate, method, len(frame), m, stable_metric, "fixed_confirmation"))
            pred_rows.append(prediction_frame(frame, candidate, split, pred, method))
            residual_rows.append(residual_row(frame, candidate, split, pred, method))
    for config in CANDIDATES:
        for split, frame in frames.items():
            pred, model = predict_candidate(validation, frame, config)
            stable_metric = metric(frame, frame[BASELINE].to_numpy(dtype=float))
            m = metric(frame, pred)
            metric_rows.append(metric_row(split, config["candidate"], config["kind"], len(frame), m, stable_metric, "fixed_confirmation"))
            pred_rows.append(prediction_frame(frame, config["candidate"], split, pred, config["kind"]))
            residual_rows.append(residual_row(frame, config["candidate"], split, pred, config["kind"]))
            if split == "test" and model is not None:
                coef_rows.append(coefficient_frame(model, config))
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True), pd.DataFrame(residual_rows)


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    stable_metric = metric(validation, validation[BASELINE].to_numpy(dtype=float))
    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            folds = row_folds(len(validation), SEED + repeat) if scheme == "row_oof" else artist_folds(validation, SEED + repeat)
            for config in CANDIDATES:
                oof = np.full(len(validation), np.nan, dtype=float)
                for train_idx, hold_idx in folds:
                    train = validation.iloc[train_idx].copy()
                    hold = validation.iloc[hold_idx].copy()
                    if config["kind"] == "direct":
                        pred = direct_prediction(hold, config)
                    else:
                        pred, _ = residual_prediction(train, hold, config)
                    oof[hold_idx] = pred
                m = metric(validation, oof)
                rows.append(
                    metric_row(
                        f"validation_{scheme}",
                        config["candidate"],
                        config["kind"],
                        len(validation),
                        m,
                        stable_metric,
                        "repeated_oof",
                        {"repeat": repeat, "validation_scheme": scheme},
                    )
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, config["candidate"], f"validation_{scheme}_repeat0", oof, config["kind"]))
    rows.append(
        metric_row(
            "validation_reference",
            "hcoef_stable",
            "baseline_stable",
            len(validation),
            stable_metric,
            stable_metric,
            "repeated_oof",
            {"repeat": -1, "validation_scheme": "reference"},
        )
    )
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True)


def metric_row(
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    stable_metric: dict[str, float],
    scope: str,
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
        "improve_count_vs_stable": int(m["MdAPE"] < stable_metric["MdAPE"])
        + int(m["MAPE"] < stable_metric["MAPE"])
        + int(m["p95_APE"] < stable_metric["p95_APE"]),
    }
    if extra:
        row.update(extra)
    return row


def summarize_repeated(metrics_df: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics_df[metrics_df["scope"].eq("repeated_oof") & metrics_df["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows = []
    for (scheme, candidate), group in repeated.groupby(["validation_scheme", "candidate"], dropna=False):
        rows.append(
            {
                "summary_type": "repeated_oof",
                "validation_scheme": scheme,
                "candidate": candidate,
                "n_repeats": int(group["repeat"].nunique()),
                "mean_MdAPE": float(group["MdAPE"].mean()),
                "mean_MAPE": float(group["MAPE"].mean()),
                "mean_p95_APE": float(group["p95_APE"].mean()),
                "mean_RMSE_log": float(group["RMSE_log"].mean()),
                "mean_delta_MdAPE_vs_stable": float(group["delta_MdAPE_vs_stable"].mean()),
                "mean_delta_MAPE_vs_stable": float(group["delta_MAPE_vs_stable"].mean()),
                "mean_delta_p95_APE_vs_stable": float(group["delta_p95_APE_vs_stable"].mean()),
                "MdAPE_improve_prob": float((group["delta_MdAPE_vs_stable"] < 0).mean()),
                "MAPE_improve_prob": float((group["delta_MAPE_vs_stable"] < 0).mean()),
                "p95_improve_prob": float((group["delta_p95_APE_vs_stable"] < 0).mean()),
                "all3_improve_prob": float(
                    (
                        (group["delta_MdAPE_vs_stable"] < 0)
                        & (group["delta_MAPE_vs_stable"] < 0)
                        & (group["delta_p95_APE_vs_stable"] < 0)
                    ).mean()
                ),
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    pivot = summary.pivot_table(
        index="candidate",
        columns="validation_scheme",
        values="all3_improve_prob",
        aggfunc="first",
    ).reset_index()
    pivot = pivot.rename(columns={"row_oof": "row_all3_improve_prob", "artist_oof": "artist_all3_improve_prob"})
    return summary.merge(pivot, on="candidate", how="left")


def residual_row(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray, method: str) -> dict[str, Any]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    residual = frame["actual_log"].to_numpy(dtype=float) - pred_log
    ape = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    return {
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": len(frame),
        "median_residual_log": float(np.nanmedian(residual)),
        "mean_residual_log": float(np.nanmean(residual)),
        "residual_std": float(np.nanstd(residual)),
        "ape_median": float(np.nanmedian(ape)),
        "ape_mean": float(np.nanmean(ape)),
        "ape_p95": float(np.nanquantile(ape, 0.95)),
        "over_2x_n": int(np.nansum(pred_price >= actual * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual * 0.5)),
    }


def coefficient_frame(model: Any, config: dict[str, Any]) -> pd.DataFrame:
    features = FEATURE_SETS[config["feature_key"]]
    huber = model.named_steps["huberregressor"]
    rows = []
    for feature, coefficient in zip(features, huber.coef_, strict=True):
        rows.append(
            {
                "candidate": config["candidate"],
                "feature_set": config["feature_key"],
                "feature": feature,
                "coefficient_on_scaled_feature": float(coefficient),
                "abs_coefficient": float(abs(coefficient)),
                "direction": "가격 보정값을 올리는 방향" if coefficient > 0 else "가격 보정값을 낮추는 방향",
                "alpha": config["alpha"],
                "cap": config["cap"],
                "strength": config["strength"],
            }
        )
    return pd.DataFrame(rows).sort_values("abs_coefficient", ascending=False)


def candidate_selection(summary: pd.DataFrame, fixed_metrics: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    combo = summary.drop_duplicates("candidate")[
        [
            "candidate",
            "row_all3_improve_prob",
            "artist_all3_improve_prob",
        ]
    ].copy()
    test = fixed_metrics[fixed_metrics["split"].eq("test")][
        [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
        ]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "RMSE_log": "test_RMSE_log",
        }
    )
    out = combo.merge(test, on="candidate", how="left")
    out["passes_repeat_gate"] = (out["row_all3_improve_prob"] >= 0.90) & (out["artist_all3_improve_prob"] >= 0.90)
    out["passes_fixed_p95_guard"] = out["test_p95_APE"] <= 0.8064
    out["passes_fixed_all3"] = (
        (out["delta_MdAPE_vs_stable"] <= 0)
        & (out["delta_MAPE_vs_stable"] <= 0)
        & (out["delta_p95_APE_vs_stable"] <= 0)
    )
    conditions = [
        out["passes_repeat_gate"] & out["passes_fixed_p95_guard"] & out["passes_fixed_all3"],
        out["passes_repeat_gate"],
        out["passes_fixed_all3"],
    ]
    choices = ["운영 후보 검토", "반복 검증 후보", "fixed test 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    return out.sort_values(
        ["passes_repeat_gate", "passes_fixed_all3", "test_MdAPE", "test_MAPE"],
        ascending=[False, False, True, True],
    )


def markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(df: pd.DataFrame, max_rows: int = 25) -> str:
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
        elif line.startswith("```"):
            continue
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
    </style>
    """
    return "<!doctype html><html><head><meta charset='utf-8'>" + style + "</head><body>" + "\n".join(lines) + "</body></html>"


def render_report(
    fixed_metrics: pd.DataFrame,
    summary: pd.DataFrame,
    selection: pd.DataFrame,
    residuals: pd.DataFrame,
    coeffs: pd.DataFrame,
    audit: pd.DataFrame,
) -> str:
    fixed_top = fixed_metrics[fixed_metrics["split"].isin(["validation", "test", "0604_ex50"])].copy()
    fixed_focus = fixed_top[fixed_top["candidate"].isin(["current_70_30", "hcoef_stable", "ppv8_service_proxy", "hcoef16_stable_ppv8_blend_w010", "hcoef16_stable_ppv8_blend_w025"])]
    test_sorted = fixed_metrics[fixed_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    repeat_focus = summary.sort_values(["row_all3_improve_prob", "artist_all3_improve_prob", "mean_delta_MdAPE_vs_stable"], ascending=[False, False, True])
    audit_rate = float((audit["abs_diff"] <= 1e-10).mean()) if not audit.empty else np.nan
    audit_max = float(audit["abs_diff"].max()) if not audit.empty else np.nan
    lines = [
        "# PP-HCOEF16 Warm PP-V8/service component OOF 재검증",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: HCOEF15에서 0604 성능이 좋았던 PP-V8/service component를 validation OOF 기준 Huber 입력 피처로 재검증",
        "- 기준 후보: `hcoef2_size_reliability_cap005_s050`",
        "- 0604 라벨은 stress test로만 사용하고 후보 선택에는 사용하지 않음",
        "- PP-V8 component는 validation/test에서 `PP-SVC3`와 `PP-V8` 산출물이 동일함을 감사함",
        f"  - validation/test PP-V8 proxy 일치율: `{audit_rate:.4f}`",
        f"  - validation/test PP-V8 proxy 최대 차이: `{audit_max:.6f}`",
        "",
        "## 1. 실행 결론",
        "",
        "- PP-V8/service component 단독은 0604에서는 강하지만 validation/test에서는 HCOEF 안정 후보보다 약함.",
        "- HCOEF 안정 후보에 PP-V8을 작은 비율로 섞거나 Huber residual 피처로 넣는 후보를 반복 OOF로 검증함.",
        "- 채택 여부는 0604가 아니라 row OOF, artist OOF, fixed test p95 guard로 판단함.",
        "",
        "## 2. fixed validation/test/0604 주요 후보",
        "",
        markdown_table(fixed_focus[["split", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]].round(4), max_rows=40),
        "",
        "## 3. fixed test 상위 후보",
        "",
        markdown_table(test_sorted[["candidate", "method", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]].round(4), max_rows=25),
        "",
        "## 4. 반복 OOF 요약",
        "",
        markdown_table(repeat_focus[["candidate", "validation_scheme", "n_repeats", "mean_MdAPE", "mean_MAPE", "mean_p95_APE", "mean_delta_MdAPE_vs_stable", "mean_delta_MAPE_vs_stable", "mean_delta_p95_APE_vs_stable", "all3_improve_prob", "row_all3_improve_prob", "artist_all3_improve_prob"]].round(4), max_rows=35),
        "",
        "## 5. 후보 선택 판단",
        "",
        markdown_table(selection.round(4), max_rows=30),
        "",
        "## 6. 잔차 요약",
        "",
        markdown_table(residuals[residuals["split"].isin(["test", "0604_ex50"])].sort_values(["split", "ape_median"])[["split", "candidate", "method", "n", "median_residual_log", "ape_median", "ape_mean", "ape_p95", "over_2x_n", "under_half_n"]].round(4), max_rows=30),
        "",
        "## 7. 계수 해석",
        "",
        markdown_table(coeffs.head(40).round(5), max_rows=40),
        "",
        "## 8. 해석",
        "",
        "- PP-V8/service component는 0604 최신 라벨에서 HCOEF 안정 후보보다 낮은 MdAPE/MAPE/p95를 보였음.",
        "- 그러나 validation/test의 기존 고정 split에서는 PP-V8 단독이 HCOEF 안정 후보보다 약함.",
        "- 따라서 PP-V8을 전체 대체 모델로 쓰는 것보다, gap/coverage를 이용한 제한적 Huber 입력으로 검증하는 접근이 맞음.",
        "- row OOF와 artist OOF gate를 통과하지 못한 후보는 0604 성능이 좋아도 운영 후보로 채택하지 않음.",
        "- PP-V8 관련 계수는 service component를 얼마나 신뢰할지보다, stable 후보와 PP-V8의 차이가 남은 residual을 설명하는지를 확인하는 용도로 해석해야 함.",
        "",
        "## 9. 산출물",
        "",
        "- `outputs/metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/feature_coefficients.csv`",
        "- `outputs/residual_analysis.csv`",
        "- `outputs/bootstrap_or_repeated_split_summary.csv`",
        "- `outputs/selected_candidates.csv`",
        "- `outputs/input_component_audit.csv`",
    ]
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    validation, test, component_audit = load_validation_test_frames()
    frame_0604 = load_0604_frame()
    frames = {"validation": validation, "test": test, "0604_ex50": frame_0604}

    fixed_metrics, fixed_predictions, coeffs, residuals = fixed_confirmation(frames)
    oof_metrics, oof_predictions = repeated_oof(validation)
    all_metrics = pd.concat([fixed_metrics, oof_metrics], ignore_index=True, sort=False)
    summary = summarize_repeated(all_metrics)
    selection = candidate_selection(summary, fixed_metrics)
    predictions = pd.concat([fixed_predictions, oof_predictions], ignore_index=True, sort=False)

    (EXP_DIR / "outputs" / "metrics.csv").parent.mkdir(parents=True, exist_ok=True)
    fixed_metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    summary.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    component_audit.to_csv(EXP_DIR / "outputs" / "input_component_audit.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "OOF validation of PP-V8/service component as Huber residual input; 0604 stress only",
        "reference": REFERENCE,
        "stable": STABLE,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "inputs": {
            "svc3_predictions": str(SVC3_PREDICTIONS.relative_to(REPO)),
            "v8_predictions": str(V8_PREDICTIONS.relative_to(REPO)),
            "hcoef3_predictions": str(HCOEF3_PREDICTIONS.relative_to(REPO)),
            "hcoef15_predictions": str(HCOEF15_PREDICTIONS.relative_to(REPO)),
            "operational_0604": str(OPERATIONAL_0604.relative_to(REPO)),
        },
        "feature_sets": FEATURE_SETS,
        "candidate_count": len(CANDIDATES),
        "candidates": CANDIDATES,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_report(fixed_metrics, summary, selection, residuals, coeffs, component_audit)
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(report), encoding="utf-8")
    doc_summary = DOC_ROOT / "pp_hcoef16_warm_huber_price_basis_coefficient_refinement_summary.md"
    doc_summary.write_text(report, encoding="utf-8")
    doc_summary.with_suffix(".html").write_text(md_to_html(report), encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])[["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
        .head(15)
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()

