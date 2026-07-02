#!/usr/bin/env python3
"""PP-ROUTE-CF3: condition-retrained Warm vs Warm-lite k=1..6.

This experiment answers a stricter routing-boundary question than CF2:

- For the same Warm fixed-test artworks, expose exactly k same-artist training
  rows for k=1..6.
- Retrain the Warm-lite Quantile + residual stack for every seed/k condition.
- Retrain the regeneratable Warm stack axes for every seed/k condition:
  comparable-stat Huber axis, generated-bucket sequential axis, validation
  Huber refit, and validation-derived risk router.

It still does not claim to be an exact historical WMIN8 artifact rebuild,
because the old PPV8/V2 upstream stack is not reconstructed. The point is to
avoid frozen-model leakage and compare the two model families after condition
specific training.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning


warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=ConvergenceWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_l10_warm_l8_feature_variant_experiments as l10  # noqa: E402
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF3_retrained_warm_vs_warm_lite_k1_to_k6"

DEFAULT_SEEDS = [20260612, 20260613, 20260614]
DEFAULT_KS = [1, 2, 3, 4, 5, 6]
WARM_ROUTE_GAP = 0.005
WARM_REFIT_ALPHA = 0.01
WARM_REFIT_CAP = 0.05
WARM_REFIT_STRENGTH = 0.50
L10_CANDIDATE = "full_plus_generated_buckets"
L10_SEQ_LABEL = f"l8_seq__{L10_CANDIDATE}"
WARM_LITE_CANDIDATE = "qavg_lgbres_s05_cap010"


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def fmt(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return ""
        if abs(float(value) - round(float(value))) < 1e-9 and abs(float(value)) >= 1:
            return str(int(round(float(value))))
        return f"{float(value):.6f}"
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    pred_price = np.clip(np.exp(pred_log[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log[valid] - actual_log[valid]) ** 2))),
    }


def add_ape(frame: pd.DataFrame, pred_col: str, out_col: str) -> pd.DataFrame:
    out = frame.copy()
    pred_price = np.clip(np.exp(pd.to_numeric(out[pred_col], errors="coerce")), 1_000.0, None)
    actual = pd.to_numeric(out["actual_price"], errors="coerce")
    out[out_col] = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    return out


def patch_svc_min1() -> None:
    for group_def in svc1.GROUP_DEFS:
        if "artist_key" in group_def["keys"]:
            group_def["min_n"] = 1


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def load_frames(ks: list[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    warm_base = artifact_features()["warm"]
    # l10.feature_candidates() returns tuple(name, strategy, features, hypothesis).
    l10_features = {
        name: features
        for name, _strategy, features, _hypothesis in l10.feature_candidates()
    }[L10_CANDIDATE]
    needed = unique(
        warm_base
        + l10_features
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, val, test = load_scope("warm", needed)
    train = train[unique([c for c in needed if c in train.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)
    val = val[unique([c for c in needed if c in val.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)
    test = test[unique([c for c in needed if c in test.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)

    counts = train.groupby(train["artist_key"].astype(str)).size()
    test["full_train_artist_history_n"] = test["artist_key"].astype(str).map(counts).fillna(0).astype(int)
    eligible = test["full_train_artist_history_n"] >= max(ks)
    test_eval = test.loc[eligible].sort_values("_track6_row_id").reset_index(drop=True)
    audit = {
        "warm_fixed_test_rows_total": int(len(test)),
        "exact_k1_to_k6_eligible_rows": int(len(test_eval)),
        "excluded_rows_with_less_than_max_k_history": int((~eligible).sum()),
        "min_full_train_artist_history_n": int(test_eval["full_train_artist_history_n"].min()),
        "max_full_train_artist_history_n": int(test_eval["full_train_artist_history_n"].max()),
        "validation_rows_for_refit_and_router": int(len(val)),
    }
    return train, val, test_eval, audit, l10_features


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for artist, idx in train.groupby(train["artist_key"].astype(str), sort=False).indices.items():
        idx_arr = np.asarray(idx, dtype=int)
        if artist in target_artists and len(idx_arr) > k:
            keep.append(np.asarray(rng.choice(idx_arr, size=k, replace=False), dtype=int))
        else:
            keep.append(idx_arr)
    return train.iloc[np.concatenate(keep)].sort_values("_track6_row_id").reset_index(drop=True)


def run_warm_lite_retrained(train_k: pd.DataFrame, test: pd.DataFrame, seed: int, k: int) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        train_s = cgrp.train_with_internal_stats(train_k)
        test_s = cgrp.assign_group_stats(train_k, test)
    finally:
        cgrp.LADDER = base_ladder

    stack = q3.train_stack(train_s)
    qpred = q3.apply_stack(test_s, stack)
    pred_log = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + np.clip(
        0.50 * qpred["lgb_residual"].to_numpy(dtype=float),
        -0.10,
        0.10,
    )
    out = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
    out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
    out["candidate"] = "Warm-lite retrained"
    out["trunc_seed"] = seed
    out["k"] = k
    out["pred_log"] = pred_log
    out["q50_full_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
    out["q50_lean_log"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
    out["quantile_uncertainty_width_log"] = qpred["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = qpred["lgb_residual"].to_numpy(dtype=float)
    out["applied_residual_correction_log"] = np.clip(0.50 * qpred["lgb_residual"].to_numpy(dtype=float), -0.10, 0.10)
    return out.sort_values("_track6_row_id").reset_index(drop=True)


def extract_l10_seq(preds: list[pd.DataFrame], split: str, expected: pd.DataFrame) -> pd.DataFrame:
    seq = pd.concat(preds, ignore_index=True)
    seq = seq[seq["candidate"].eq(L10_SEQ_LABEL) & seq["split"].eq(split)].copy()
    if seq["_track6_row_id"].nunique() != len(expected):
        raise RuntimeError(f"L10 {split} row mismatch: got {seq['_track6_row_id'].nunique()} expected {len(expected)}")
    cols = ["_track6_row_id", "pred_log", "quantile_width"]
    return (
        expected[["_track6_row_id"]]
        .merge(seq[cols], on="_track6_row_id", how="left", validate="one_to_one")
        .rename(columns={"pred_log": "l10_seq_pred_log", "quantile_width": "l10_quantile_width"})
    )


def refit_features(frame: pd.DataFrame, current: np.ndarray, svc_pred: np.ndarray, l10_pred: np.ndarray, l10_width: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    out["current_70_30"] = np.asarray(current, dtype=float)
    out["svc_fallback"] = np.asarray(svc_pred, dtype=float)
    out["l10_seq"] = np.asarray(l10_pred, dtype=float)
    out["log_area"] = pd.to_numeric(frame["log_area"], errors="coerce").to_numpy(dtype=float)
    out["svc_group_n_log"] = np.log1p(pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0.0).to_numpy(dtype=float))
    iqr = pd.to_numeric(frame["svc_group_log_price_iqr"], errors="coerce")
    out["svc_prior_iqr"] = iqr.fillna(iqr.median()).to_numpy(dtype=float)
    out["current_l10_gap"] = out["current_70_30"] - out["l10_seq"]
    out["current_svc_gap"] = out["current_70_30"] - out["svc_fallback"]
    out["svc_l10_gap"] = out["svc_fallback"] - out["l10_seq"]
    out["l10_quantile_width"] = np.asarray(l10_width, dtype=float)
    return out


def fit_refit_model(val_features: pd.DataFrame, val_actual_log: np.ndarray, val_current: np.ndarray) -> Any:
    target = np.asarray(val_actual_log, dtype=float) - np.asarray(val_current, dtype=float)
    model = hcoef1.linear_pipeline("huber", WARM_REFIT_ALPHA)
    model.fit(val_features, target)
    return model


def apply_refit_model(model: Any, features: pd.DataFrame, current: np.ndarray) -> np.ndarray:
    raw = np.asarray(model.predict(features), dtype=float)
    correction = np.clip(raw, -WARM_REFIT_CAP, WARM_REFIT_CAP) * WARM_REFIT_STRENGTH
    return np.asarray(current, dtype=float) + correction


def warm_risk_score(
    l10_width: np.ndarray,
    component_spread: np.ndarray,
    gap_abs: np.ndarray,
    history_k: np.ndarray,
    base_pred: np.ndarray,
    price_cut: float,
) -> np.ndarray:
    qwidth_score = np.clip((np.asarray(l10_width, dtype=float) - 1.20) / 1.20, 0.0, 1.0)
    spread_score = np.clip(np.asarray(component_spread, dtype=float) / 0.18, 0.0, 1.0)
    gap_score = np.clip(np.asarray(gap_abs, dtype=float) / 0.06, 0.0, 1.0)
    low_conf_score = np.where(np.asarray(history_k, dtype=float) <= 1, 1.0, 0.35)
    price_band_score = np.where(np.asarray(base_pred, dtype=float) >= price_cut, 1.0, 0.0)
    return np.clip(
        0.38 * qwidth_score
        + 0.22 * spread_score
        + 0.14 * gap_score
        + 0.16 * low_conf_score
        + 0.10 * price_band_score,
        0.0,
        1.0,
    )


def run_warm_retrained(
    train_k: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    l10_features: list[str],
    seed: int,
    k: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    patch_svc_min1()
    svc_features = svc1.candidate_features(artifact_features()["warm"])["svc_numeric"]

    train_stats = svc1.crossfit_train_stats(train_k)
    train_full = train_k.merge(train_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    val_stats = svc1.apply_comparable_stats(train_k, val)
    test_stats = svc1.apply_comparable_stats(train_k, test)
    val_full = val.merge(val_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))
    test_full = test.merge(test_stats, on="_track6_row_id", how="left", suffixes=("", "_svc"))

    svc_pred = svc1.fit_predict("huber", train_full, val_full, test_full, svc_features)
    val_svc = np.asarray(svc_pred["validation"], dtype=float)
    test_svc = np.asarray(svc_pred["test"], dtype=float)

    _rows, l10_preds, _feature_info = l10.run_candidate(
        name=L10_CANDIDATE,
        strategy="기준 피처셋+생성 bucket",
        features=l10_features,
        hypothesis="PP-ROUTE-CF3 condition-specific retraining",
        base_train=train_k,
        base_val=val,
        base_test=test,
    )
    val_l10 = extract_l10_seq(l10_preds, "validation", val)
    test_l10 = extract_l10_seq(l10_preds, "test", test)
    val_l10_pred = val_l10["l10_seq_pred_log"].to_numpy(dtype=float)
    test_l10_pred = test_l10["l10_seq_pred_log"].to_numpy(dtype=float)
    val_l10_width = val_l10["l10_quantile_width"].to_numpy(dtype=float)
    test_l10_width = test_l10["l10_quantile_width"].to_numpy(dtype=float)

    val_base_current = 0.70 * val_svc + 0.30 * val_l10_pred
    val_alt_current = 0.85 * val_svc + 0.15 * val_l10_pred
    test_base_current = 0.70 * test_svc + 0.30 * test_l10_pred
    test_alt_current = 0.85 * test_svc + 0.15 * test_l10_pred

    val_base_features = refit_features(val_full, val_base_current, val_svc, val_l10_pred, val_l10_width)
    val_alt_features = refit_features(val_full, val_alt_current, val_svc, val_l10_pred, val_l10_width)
    test_base_features = refit_features(test_full, test_base_current, test_svc, test_l10_pred, test_l10_width)
    test_alt_features = refit_features(test_full, test_alt_current, test_svc, test_l10_pred, test_l10_width)

    base_refit = fit_refit_model(val_base_features, val["ln_price_krw"].to_numpy(dtype=float), val_base_current)
    alt_refit = fit_refit_model(val_alt_features, val["ln_price_krw"].to_numpy(dtype=float), val_alt_current)
    val_base_pred = apply_refit_model(base_refit, val_base_features, val_base_current)
    val_alt_pred = apply_refit_model(alt_refit, val_alt_features, val_alt_current)
    test_base_pred = apply_refit_model(base_refit, test_base_features, test_base_current)
    test_alt_pred = apply_refit_model(alt_refit, test_alt_features, test_alt_current)

    val_history = val["artist_key"].astype(str).map(train_k.groupby(train_k["artist_key"].astype(str)).size()).fillna(0).to_numpy(dtype=float)
    test_history = test["artist_key"].astype(str).map(train_k.groupby(train_k["artist_key"].astype(str)).size()).fillna(0).to_numpy(dtype=float)
    val_price_cut = float(np.nanquantile(val_base_pred, 0.90))
    val_risk = warm_risk_score(
        val_l10_width,
        np.abs(val_svc - val_l10_pred),
        np.abs(val_base_current - val_l10_pred),
        val_history,
        val_base_pred,
        val_price_cut,
    )
    threshold = float(np.nanquantile(val_risk, 0.50))
    test_risk = warm_risk_score(
        test_l10_width,
        np.abs(test_svc - test_l10_pred),
        np.abs(test_base_current - test_l10_pred),
        test_history,
        test_base_pred,
        val_price_cut,
    )
    route_to_alt = (test_risk >= threshold) & (test_alt_pred < test_base_pred) & ((test_base_pred - test_alt_pred) >= WARM_ROUTE_GAP)
    routed = np.where(route_to_alt, test_alt_pred, test_base_pred)

    out = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
    out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
    out["candidate"] = "Warm retrained clean stack"
    out["trunc_seed"] = seed
    out["k"] = k
    out["pred_log"] = routed
    out["svc_core_pred_log"] = test_svc
    out["l10_seq_pred_log"] = test_l10_pred
    out["base_w700_refit_pred_log"] = test_base_pred
    out["alternative_w850_refit_pred_log"] = test_alt_pred
    out["route_to_alternative"] = route_to_alt
    out["risk_score"] = test_risk
    out["route_threshold"] = threshold
    out["l10_quantile_width"] = test_l10_width
    out["artist_history_n"] = test_history

    audit = out[
        [
            "trunc_seed",
            "k",
            "_track6_row_id",
            "artist_key",
            "svc_core_pred_log",
            "l10_seq_pred_log",
            "base_w700_refit_pred_log",
            "alternative_w850_refit_pred_log",
            "route_to_alternative",
            "risk_score",
            "route_threshold",
            "artist_history_n",
        ]
    ].copy()
    return out.sort_values("_track6_row_id").reset_index(drop=True), audit.sort_values("_track6_row_id").reset_index(drop=True)


def repeated_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, seed, k), group in predictions.groupby(["candidate", "trunc_seed", "k"], sort=True):
        row = {"candidate": candidate, "trunc_seed": int(seed), "k": int(k)}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "candidate", "trunc_seed"]).reset_index(drop=True)


def seed_mean_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    return (
        predictions.groupby(["candidate", "k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "candidate", "_track6_row_id"])
        .reset_index(drop=True)
    )


def same_n_metrics(seed_mean: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} retrained seed-mean"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def paired_by_k(seed_mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    warm = seed_mean[seed_mean["candidate"].eq("Warm retrained clean stack")].rename(columns={"pred_log": "warm_pred_log"})
    lite = seed_mean[seed_mean["candidate"].eq("Warm-lite retrained")].rename(columns={"pred_log": "warm_lite_pred_log"})
    wide = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "k", "warm_pred_log"]].merge(
        lite[["_track6_row_id", "k", "warm_lite_pred_log"]],
        on=["_track6_row_id", "k"],
        how="inner",
        validate="one_to_one",
    )
    wide = add_ape(wide, "warm_pred_log", "warm_ape")
    wide = add_ape(wide, "warm_lite_pred_log", "warm_lite_ape")
    rows = []
    for k, group in wide.groupby("k", sort=True):
        warm_ape = group["warm_ape"].to_numpy(dtype=float)
        lite_ape = group["warm_lite_ape"].to_numpy(dtype=float)
        rows.append(
            {
                "k": int(k),
                "n": int(len(group)),
                "warm_better_share": float(np.mean(warm_ape < lite_ape)),
                "warm_lite_better_share": float(np.mean(lite_ape < warm_ape)),
                "tie_share": float(np.mean(np.isclose(warm_ape, lite_ape))),
                "median_ape_delta_warm_minus_warm_lite": float(np.nanmedian(warm_ape - lite_ape)),
                "mean_ape_delta_warm_minus_warm_lite": float(np.nanmean(warm_ape - lite_ape)),
            }
        )
    return pd.DataFrame(rows), wide


def write_report(
    metrics_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
    paired_df: pd.DataFrame,
    warm_audit: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    best_by_metric = {
        metric: str(metrics_df.sort_values(metric).iloc[0]["candidate"]) + " " + str(metrics_df.sort_values(metric).iloc[0]["condition"])
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    }
    route_summary = (
        warm_audit.groupby(["trunc_seed", "k"], as_index=False)
        .agg(
            route_to_alt_share=("route_to_alternative", "mean"),
            median_risk_score=("risk_score", "median"),
            route_threshold=("route_threshold", "first"),
        )
        .sort_values(["k", "trunc_seed"])
    )
    lines = [
        "# PP-ROUTE-CF3 Retrained Warm vs Warm-lite k=1~6",
        "",
        "## 1. 목적",
        "",
        "Warm fixed-test 중 k=1~6을 모두 만들 수 있는 동일 작품에서, Warm과 Warm-lite를 각 k 조건별로 다시 학습해 비교한다.",
        "",
        "## 2. CF2와 다른 점",
        "",
        "- CF2는 동결 Warm-lite 번들과 WMIN8-shell을 강제 적용했다.",
        "- CF3는 각 seed/k 조건마다 Warm-lite Quantile/잔차 모델을 다시 학습한다.",
        "- CF3는 각 seed/k 조건마다 Warm의 비교군 Huber 축, 버킷 순차 보정 축, validation Huber refit, validation risk router를 다시 학습한다.",
        "- 단, 과거 WMIN8의 모든 PPV8/V2 상류 실험 산출물을 그대로 재현한 것은 아니므로 후보명은 `Warm retrained clean stack`으로 분리한다.",
        "",
        "## 3. Same-n seed-mean metrics",
        "",
        md_table(metrics_df, ["candidate", "condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 4. 관찰 요약",
        "",
        f"- Best by MdAPE: `{best_by_metric['MdAPE']}`.",
        f"- Best by MAPE: `{best_by_metric['MAPE']}`.",
        f"- Best by p95 APE: `{best_by_metric['p95_APE']}`.",
        f"- Best by RMSE log: `{best_by_metric['RMSE_log']}`.",
        "",
        "## 5. Paired row-level comparison",
        "",
        md_table(paired_df, ["k", "n", "warm_better_share", "warm_lite_better_share", "median_ape_delta_warm_minus_warm_lite", "mean_ape_delta_warm_minus_warm_lite"], 20),
        "",
        "## 6. Repeated seed metrics",
        "",
        md_table(repeated_df, ["candidate", "trunc_seed", "k", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 80),
        "",
        "## 7. Warm retrained route audit",
        "",
        md_table(route_summary, ["trunc_seed", "k", "route_to_alt_share", "median_risk_score", "route_threshold"], 40),
        "",
        "## 8. 해석 주의",
        "",
        "- 이 결과는 학습까지 다시 한 route-boundary 실험이다.",
        "- 실제 운영 Warm WMIN8 artifact와 이름을 혼용하지 않는다. CF3 Warm은 재현 가능한 clean stack이고, 운영 WMIN8 전체 상류 산출물의 완전 재생성은 아니다.",
        "- Warm-lite k=5~6은 모델을 다시 학습했더라도 공식 라우팅 범위 밖의 정책 스트레스 비교다.",
        "",
        "## 9. Config",
        "",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="*", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--ks", nargs="*", type=int, default=DEFAULT_KS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seeds = list(args.seeds)
    ks = list(args.ks)
    start = time.time()
    ensure_dirs()

    train, val, test, eligibility_audit, l10_features = load_frames(ks)
    target_artists = set(test["artist_key"].astype(str)) | set(val["artist_key"].astype(str))

    pred_parts: list[pd.DataFrame] = []
    warm_audit_parts: list[pd.DataFrame] = []
    for seed in seeds:
        for k in ks:
            condition_start = time.time()
            train_k = truncate_train(train, target_artists, seed, k)
            warm_lite = run_warm_lite_retrained(train_k, test, seed, k)
            warm, warm_audit = run_warm_retrained(train_k, val, test, l10_features, seed, k)
            pred_parts.extend([warm_lite, warm])
            warm_audit_parts.append(warm_audit)
            print(
                json.dumps(
                    {
                        "done": "condition",
                        "seed": seed,
                        "k": k,
                        "rows": len(test),
                        "seconds": round(time.time() - condition_start, 2),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    predictions = pd.concat(pred_parts, ignore_index=True)
    warm_audit = pd.concat(warm_audit_parts, ignore_index=True)
    repeated_df = repeated_metrics(predictions)
    seed_mean = seed_mean_predictions(predictions)
    if not seed_mean["seed_n"].eq(len(seeds)).all():
        raise RuntimeError("Seed mean table has missing seeds")
    metrics_df = same_n_metrics(seed_mean)
    paired_df, paired_rows = paired_by_k(seed_mean)

    predictions.to_csv(EXP / "outputs" / "predictions_all_conditions.csv", index=False)
    warm_audit.to_csv(EXP / "outputs" / "warm_retrained_route_audit.csv", index=False)
    repeated_df.to_csv(EXP / "outputs" / "repeated_condition_metrics.csv", index=False)
    seed_mean.to_csv(EXP / "outputs" / "seed_mean_predictions_by_k.csv", index=False)
    metrics_df.to_csv(EXP / "outputs" / "same_n_metrics_by_k.csv", index=False)
    paired_df.to_csv(EXP / "outputs" / "paired_warm_vs_warm_lite_by_k.csv", index=False)
    paired_rows.to_csv(EXP / "outputs" / "paired_row_level_ape_by_k.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF3",
        "experiment_slug": EXP.name,
        "seeds": seeds,
        "k_values": ks,
        "base_eval_set": "Warm fixed-test rows with at least max(k) same-artist train-history rows",
        "eligibility_audit": eligibility_audit,
        "warm_lite_training": {
            "group_stats": "k-truncated train, 5-fold internal stats for train rows, full train_k stats for test rows",
            "quantile_models": "LightGBM Quantile q10/q50/q90 full + q50 lean retrained per seed/k",
            "residual_model": "LightGBM objective=huber residual retrained per seed/k from OOF Quantile residual",
            "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)",
        },
        "warm_training": {
            "svc_axis": "comparable-stat Huber retrained per seed/k with artist min_n=1",
            "sequential_axis": "CatBoost Quantile -> Huber -> CatBoost residual generated-bucket stack retrained per seed/k",
            "refit": "Huber residual refit trained on warm validation per seed/k",
            "router": "risk threshold q50 learned from warm validation per seed/k, gap=0.005",
            "candidate": "validation-routed 0.70/0.30 base vs 0.85/0.15 alternative",
        },
        "limitations": [
            "This is a condition-retrained clean stack comparison, not an exact historical WMIN8/PPV8 full artifact rebuild.",
            "Warm-lite k=5~6 remains outside the official Warm-lite route and is included as a stress comparison.",
            "The same-n main table excludes rows that cannot support all k values.",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, repeated_df, paired_df, warm_audit, config)

    print("[same-n metrics]")
    print(metrics_df.to_string(index=False))
    print("\n[paired by k]")
    print(paired_df.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
