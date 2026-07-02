#!/usr/bin/env python3
"""PP-ROUTE-CF7: Warm-lite unified tail-guard follow-up.

Goal:
- CF5/CF6 showed unified Warm-lite improves central/mean error, but CF5 still
  loses to operational Warm WMIN8 on p95/RMSE.
- This experiment tunes only on Warm validation rows, then evaluates on the
  fixed Warm test rows.

Candidate families:
1. Residual strength/cap grid.
2. Uncertainty/disagreement conditional residual dampening.
3. Validation-fitted Huber calibration layer over the unified Warm-lite axes.
"""
from __future__ import annotations

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
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=ConvergenceWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF7_warm_lite_tail_guard"
WARM_OPERATIONAL = (
    REPO
    / "models"
    / "track6"
    / "warm_wmin8_operational_candidate"
    / "artifacts"
    / "wmin8_selected_candidate_predictions.csv"
)

SEEDS = [20260612, 20260613, 20260614]
WARM_CANDIDATE = "min1_route_w850_risk_q50_altlower_gap005"


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


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


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    warm_base = artifact_features()["warm"]
    needed = unique(
        warm_base
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + [
            "medium_support_bucket",
            "ln_price_krw",
            "price_krw",
            "_track6_row_id",
            "artist_key",
        ]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, val, test = load_scope("warm", needed)
    keep = unique([c for c in needed if c in train.columns] + ["ln_price_krw", "price_krw"])
    train = train[keep].reset_index(drop=True)
    val = val[keep].reset_index(drop=True)
    test = test[keep].reset_index(drop=True)

    counts = train.groupby(train["artist_key"].astype(str)).size()
    for frame in [val, test]:
        frame["full_train_artist_history_n"] = frame["artist_key"].astype(str).map(counts).fillna(0).astype(int)

    audit = {
        "train_rows": int(len(train)),
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "train_artists": int(train["artist_key"].astype(str).nunique()),
        "validation_min_history": int(val["full_train_artist_history_n"].min()),
        "validation_max_history": int(val["full_train_artist_history_n"].max()),
        "test_min_history": int(test["full_train_artist_history_n"].min()),
        "test_max_history": int(test["full_train_artist_history_n"].max()),
    }
    return train, val.sort_values("_track6_row_id").reset_index(drop=True), test.sort_values("_track6_row_id").reset_index(drop=True), audit


def train_unified_stack(train: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, dict[str, object]]:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        train_s = cgrp.train_with_internal_stats(train)
    finally:
        cgrp.LADDER = base_ladder

    train_s = q3.add_price_proxy(train_s)
    q_oof = q3.oof_quantiles(train_s, seed=seed)
    q_models = q3.fit_quantile_models(train_s, seed=seed)
    residual_models = q3.fit_residual_models(train_s, q_oof)
    return train_s, {"q_models": q_models, "residual_models": residual_models}


def predict_split(train: pd.DataFrame, frame: pd.DataFrame, stack: dict[str, object], seed: int, split: str) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        frame_s = cgrp.assign_group_stats(train, frame)
    finally:
        cgrp.LADDER = base_ladder

    frame_s = q3.add_price_proxy(frame_s)
    qpred = q3.apply_stack(frame_s, stack)

    out = frame[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw", "full_train_artist_history_n"]].copy()
    out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
    out["split"] = split
    out["trunc_seed"] = seed
    out["q10_log"] = qpred["lgbq_full_q10"].to_numpy(dtype=float)
    out["q50_full_log"] = qpred["lgbq_full_q50"].to_numpy(dtype=float)
    out["q90_log"] = qpred["lgbq_full_q90"].to_numpy(dtype=float)
    out["q50_lean_log"] = qpred["lgbq_lean_q50"].to_numpy(dtype=float)
    out["qavg_log"] = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float)
    out["quantile_uncertainty_width_log"] = qpred["lgbq_width"].to_numpy(dtype=float)
    out["full_lean_gap_abs_log"] = np.abs(out["q50_full_log"] - out["q50_lean_log"])
    out["catboost_residual_log"] = qpred["cb_residual"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = qpred["lgb_residual"].to_numpy(dtype=float)
    out["current_residual_correction_log"] = np.clip(0.50 * out["lgb_huber_residual_log"], -0.10, 0.10)
    out["current_pred_log"] = out["qavg_log"] + out["current_residual_correction_log"]

    for col in [
        "grp_log_price_median",
        "grp_log_price_q25",
        "grp_log_price_q75",
        "grp_log_price_iqr",
        "grp_unit_area_median",
        "grp_unit_area_iqr",
        "grp_n_log",
        "grp_match_level",
        "grp_price_proxy",
        "log_area",
        "area_cm2",
        "aspect_ratio",
        "has_depth",
        "is_3d_candidate",
    ]:
        if col in frame_s.columns:
            out[col] = frame_s[col].to_numpy()
    return out.sort_values(["split", "trunc_seed", "_track6_row_id"]).reset_index(drop=True)


def seed_mean_features(preds: pd.DataFrame) -> pd.DataFrame:
    agg: dict[str, tuple[str, str]] = {
        "artist_key": ("artist_key", "first"),
        "actual_price": ("actual_price", "first"),
        "actual_log": ("actual_log", "first"),
        "full_train_artist_history_n": ("full_train_artist_history_n", "first"),
        "seed_n": ("trunc_seed", "nunique"),
    }
    for col in [
        "q10_log",
        "q50_full_log",
        "q90_log",
        "q50_lean_log",
        "qavg_log",
        "quantile_uncertainty_width_log",
        "full_lean_gap_abs_log",
        "catboost_residual_log",
        "lgb_huber_residual_log",
        "current_residual_correction_log",
        "current_pred_log",
        "grp_log_price_median",
        "grp_log_price_q25",
        "grp_log_price_q75",
        "grp_log_price_iqr",
        "grp_unit_area_median",
        "grp_unit_area_iqr",
        "grp_n_log",
        "grp_match_level",
        "grp_price_proxy",
        "log_area",
        "area_cm2",
        "aspect_ratio",
    ]:
        if col in preds.columns:
            agg[col] = (col, "mean")
    return (
        preds.groupby(["split", "_track6_row_id"], as_index=False)
        .agg(**agg)
        .sort_values(["split", "_track6_row_id"])
        .reset_index(drop=True)
    )


def candidate_grid(val_seed_mean: pd.DataFrame) -> list[dict[str, Any]]:
    width_q = {
        q: float(np.nanquantile(val_seed_mean["quantile_uncertainty_width_log"], q))
        for q in [0.50, 0.67, 0.75, 0.80, 0.90]
    }
    gap_q = {q: float(np.nanquantile(val_seed_mean["full_lean_gap_abs_log"], q)) for q in [0.67, 0.75, 0.80, 0.90]}
    corr_abs = np.abs(val_seed_mean["current_residual_correction_log"].to_numpy(dtype=float))
    corr_q = {q: float(np.nanquantile(corr_abs, q)) for q in [0.67, 0.75, 0.80, 0.90]}

    specs: list[dict[str, Any]] = [
        {"name": "current_s05_cap010", "family": "baseline", "strength": 0.50, "cap_pos": 0.10, "cap_neg": 0.10},
        {"name": "qavg_no_residual", "family": "residual_grid", "strength": 0.00, "cap_pos": 0.00, "cap_neg": 0.00},
    ]

    for strength in [0.25, 0.50, 0.75, 1.00]:
        for cap in [0.03, 0.05, 0.075, 0.10, 0.15]:
            specs.append(
                {
                    "name": f"lgbres_s{strength:.2f}_cap{cap:.3f}".replace(".", "p"),
                    "family": "residual_grid",
                    "strength": strength,
                    "cap_pos": cap,
                    "cap_neg": cap,
                }
            )

    for cap_neg in [0.05, 0.075, 0.10, 0.15]:
        for cap_pos in [0.03, 0.05, 0.075, 0.10]:
            specs.append(
                {
                    "name": f"asym_s05_neg{cap_neg:.3f}_pos{cap_pos:.3f}".replace(".", "p"),
                    "family": "asymmetric_cap",
                    "strength": 0.50,
                    "cap_pos": cap_pos,
                    "cap_neg": cap_neg,
                }
            )

    for q, threshold in width_q.items():
        for factor in [0.00, 0.25, 0.50]:
            specs.append(
                {
                    "name": f"width_q{int(q * 100)}_corr_factor{factor:.2f}".replace(".", "p"),
                    "family": "width_guard",
                    "strength": 0.50,
                    "cap_pos": 0.10,
                    "cap_neg": 0.10,
                    "width_threshold": threshold,
                    "high_factor": factor,
                }
            )

    for q, threshold in gap_q.items():
        for factor in [0.00, 0.25, 0.50]:
            specs.append(
                {
                    "name": f"gap_q{int(q * 100)}_corr_factor{factor:.2f}".replace(".", "p"),
                    "family": "full_lean_gap_guard",
                    "strength": 0.50,
                    "cap_pos": 0.10,
                    "cap_neg": 0.10,
                    "gap_threshold": threshold,
                    "high_factor": factor,
                }
            )

    for q, threshold in corr_q.items():
        for factor in [0.00, 0.25, 0.50]:
            specs.append(
                {
                    "name": f"corrabs_q{int(q * 100)}_corr_factor{factor:.2f}".replace(".", "p"),
                    "family": "correction_size_guard",
                    "strength": 0.50,
                    "cap_pos": 0.10,
                    "cap_neg": 0.10,
                    "corr_abs_threshold": threshold,
                    "high_factor": factor,
                }
            )

    for q, threshold in width_q.items():
        for hist_n in [5, 10, 20]:
            for factor in [0.00, 0.25, 0.50]:
                specs.append(
                    {
                        "name": f"lowhist{hist_n}_width_q{int(q * 100)}_factor{factor:.2f}".replace(".", "p"),
                        "family": "low_history_width_guard",
                        "strength": 0.50,
                        "cap_pos": 0.10,
                        "cap_neg": 0.10,
                        "width_threshold": threshold,
                        "history_max": hist_n,
                        "high_factor": factor,
                    }
                )
    return specs


def apply_rule_candidate(frame: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    qavg = frame["qavg_log"].to_numpy(dtype=float)
    residual = frame["lgb_huber_residual_log"].to_numpy(dtype=float)
    corr = np.asarray(spec["strength"], dtype=float) * residual
    corr = np.minimum(np.maximum(corr, -float(spec["cap_neg"])), float(spec["cap_pos"]))

    factor = np.ones(len(frame), dtype=float)
    family = spec["family"]
    if family == "width_guard":
        mask = frame["quantile_uncertainty_width_log"].to_numpy(dtype=float) >= float(spec["width_threshold"])
        factor[mask] = float(spec["high_factor"])
    elif family == "full_lean_gap_guard":
        mask = frame["full_lean_gap_abs_log"].to_numpy(dtype=float) >= float(spec["gap_threshold"])
        factor[mask] = float(spec["high_factor"])
    elif family == "correction_size_guard":
        mask = np.abs(frame["current_residual_correction_log"].to_numpy(dtype=float)) >= float(spec["corr_abs_threshold"])
        factor[mask] = float(spec["high_factor"])
    elif family == "low_history_width_guard":
        width_mask = frame["quantile_uncertainty_width_log"].to_numpy(dtype=float) >= float(spec["width_threshold"])
        hist_mask = frame["full_train_artist_history_n"].to_numpy(dtype=float) <= float(spec["history_max"])
        factor[width_mask & hist_mask] = float(spec["high_factor"])

    return qavg + corr * factor


META_FEATURES = [
    "q10_log",
    "q50_full_log",
    "q90_log",
    "q50_lean_log",
    "qavg_log",
    "current_pred_log",
    "quantile_uncertainty_width_log",
    "full_lean_gap_abs_log",
    "lgb_huber_residual_log",
    "current_residual_correction_log",
    "full_train_artist_history_n",
    "grp_log_price_median",
    "grp_log_price_iqr",
    "grp_unit_area_iqr",
    "grp_n_log",
    "grp_match_level",
    "grp_price_proxy",
    "log_area",
    "area_cm2",
    "aspect_ratio",
]


def meta_pipeline(kind: str) -> Pipeline:
    model: Any
    if kind == "ridge":
        model = Ridge(alpha=1.0)
    else:
        model = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=4000)
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        (
                            "num",
                            Pipeline(
                                [
                                    ("impute", SimpleImputer(strategy="median")),
                                    ("scale", StandardScaler()),
                                ]
                            ),
                            META_FEATURES,
                        )
                    ],
                    remainder="drop",
                ),
            ),
            ("model", model),
        ]
    )


def fit_meta_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    val_pred_parts = []
    test_pred_parts = []
    y = val["actual_log"].to_numpy(dtype=float)
    for kind in ["huber", "ridge"]:
        oof = np.full(len(val), np.nan, dtype=float)
        kf = KFold(n_splits=5, shuffle=True, random_state=20260612)
        for tr_idx, va_idx in kf.split(val):
            pipe = meta_pipeline(kind)
            pipe.fit(val.iloc[tr_idx][META_FEATURES], y[tr_idx])
            oof[va_idx] = pipe.predict(val.iloc[va_idx][META_FEATURES])

        final_pipe = meta_pipeline(kind)
        final_pipe.fit(val[META_FEATURES], y)
        test_pred = final_pipe.predict(test[META_FEATURES])

        name = f"validation_oof_{kind}_meta_calibrator"
        val_part = val[["_track6_row_id", "actual_price", "actual_log"]].copy()
        val_part["candidate"] = name
        val_part["pred_log"] = oof
        val_pred_parts.append(val_part)

        test_part = test[["_track6_row_id", "actual_price", "actual_log"]].copy()
        test_part["candidate"] = name
        test_part["pred_log"] = test_pred
        test_pred_parts.append(test_part)

        row = {"candidate": name, "family": "meta_calibrator", "selection_source": "validation_oof"}
        row.update(metrics(val["actual_price"].to_numpy(), y, oof))
        rows.append(row)

    return pd.DataFrame(rows), pd.concat(val_pred_parts, ignore_index=True), pd.concat(test_pred_parts, ignore_index=True)


def evaluate_rule_candidates(split_name: str, frame: pd.DataFrame, specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_parts = []
    for spec in specs:
        pred = apply_rule_candidate(frame, spec)
        row = {
            "split": split_name,
            "candidate": spec["name"],
            "family": spec["family"],
            "spec": json.dumps(spec, ensure_ascii=False, sort_keys=True),
        }
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), pred))
        rows.append(row)

        part = frame[["_track6_row_id", "actual_price", "actual_log"]].copy()
        part["split"] = split_name
        part["candidate"] = spec["name"]
        part["pred_log"] = pred
        pred_parts.append(part)
    return pd.DataFrame(rows), pd.concat(pred_parts, ignore_index=True)


def load_warm_operational(row_ids: set[int], eval_split: str) -> pd.DataFrame:
    raw = pd.read_csv(WARM_OPERATIONAL, low_memory=False)
    warm = raw[
        raw["eval_split"].eq(eval_split)
        & raw["candidate_label"].eq(WARM_CANDIDATE)
        & raw["_track6_row_id"].astype(int).isin(row_ids)
    ].copy()
    if warm["_track6_row_id"].nunique() != len(row_ids):
        raise RuntimeError(f"Warm operational {eval_split} row mismatch: got {warm['_track6_row_id'].nunique()} expected {len(row_ids)}")
    out = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "pred_log"]].copy()
    out["candidate"] = "Warm WMIN8 operational"
    return out.sort_values("_track6_row_id").reset_index(drop=True)


def baseline_rows(split: str, frame: pd.DataFrame, warm: pd.DataFrame | None) -> pd.DataFrame:
    rows = []
    for candidate, pred in [
        ("Warm-lite current s0.50 cap0.10", frame["current_pred_log"].to_numpy(dtype=float)),
        ("Warm-lite qavg no residual", frame["qavg_log"].to_numpy(dtype=float)),
    ]:
        row = {"split": split, "candidate": candidate, "family": "reference"}
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), pred))
        rows.append(row)
    if warm is not None:
        row = {"split": split, "candidate": "Warm WMIN8 operational", "family": "reference"}
        row.update(metrics(warm["actual_price"].to_numpy(), warm["actual_log"].to_numpy(), warm["pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows)


def select_candidates(validation_metrics: pd.DataFrame) -> pd.DataFrame:
    current = validation_metrics[validation_metrics["candidate"].eq("current_s05_cap010")].iloc[0]
    candidates = validation_metrics.copy()
    candidates["passes_balance_guard"] = (
        (candidates["MAPE"] <= float(current["MAPE"]) + 0.005)
        & (candidates["MdAPE"] <= float(current["MdAPE"]) + 0.005)
    )
    guarded = candidates[candidates["passes_balance_guard"]].copy()
    if guarded.empty:
        guarded = candidates.copy()
    best_p95 = guarded.sort_values(["p95_APE", "MAPE", "MdAPE"], ascending=True).head(1).copy()
    best_mape = candidates.sort_values(["MAPE", "p95_APE", "MdAPE"], ascending=True).head(1).copy()
    best_rmse = guarded.sort_values(["RMSE_log", "MAPE", "p95_APE"], ascending=True).head(1).copy()
    selected = pd.concat([best_p95, best_mape, best_rmse], ignore_index=True)
    selected["selection_reason"] = ["best_validation_p95_with_balance_guard", "best_validation_mape", "best_validation_rmse_with_balance_guard"][: len(selected)]
    return selected.drop_duplicates("candidate").reset_index(drop=True)


def select_meta_candidates(meta_metrics: pd.DataFrame, current_reference: pd.Series) -> pd.DataFrame:
    candidates = meta_metrics.copy()
    candidates["passes_balance_guard"] = (
        (candidates["MAPE"] <= float(current_reference["MAPE"]) + 0.005)
        & (candidates["MdAPE"] <= float(current_reference["MdAPE"]) + 0.005)
    )
    guarded = candidates[candidates["passes_balance_guard"]].copy()
    if guarded.empty:
        guarded = candidates.copy()
    selected = guarded.sort_values(["p95_APE", "MAPE", "MdAPE"], ascending=True).head(1).copy()
    selected["selection_reason"] = "best_validation_meta_p95_with_balance_guard"
    return selected.reset_index(drop=True)


def paired_vs_current(frame: pd.DataFrame, selected_preds: pd.DataFrame) -> pd.DataFrame:
    base = frame[["_track6_row_id", "actual_price", "actual_log", "current_pred_log"]].copy()
    base = add_ape(base, "current_pred_log", "current_ape")
    rows = []
    for candidate, part in selected_preds.groupby("candidate", sort=True):
        wide = base.merge(
            part[["_track6_row_id", "pred_log"]],
            on="_track6_row_id",
            how="inner",
            validate="one_to_one",
        )
        wide = add_ape(wide, "pred_log", "candidate_ape")
        rows.append(
            {
                "candidate": candidate,
                "n": int(len(wide)),
                "candidate_better_share": float(np.mean(wide["candidate_ape"] < wide["current_ape"])),
                "current_better_share": float(np.mean(wide["current_ape"] < wide["candidate_ape"])),
                "median_ape_delta_current_minus_candidate": float(np.nanmedian(wide["current_ape"] - wide["candidate_ape"])),
                "mean_ape_delta_current_minus_candidate": float(np.nanmean(wide["current_ape"] - wide["candidate_ape"])),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    validation_metrics: pd.DataFrame,
    test_metrics: pd.DataFrame,
    selected: pd.DataFrame,
    selected_test: pd.DataFrame,
    paired_test: pd.DataFrame,
    audit: dict[str, Any],
    config: dict[str, Any],
) -> None:
    top_val = validation_metrics.sort_values(["p95_APE", "MAPE", "MdAPE"]).head(20)
    top_test = test_metrics[test_metrics["candidate"].isin(selected["candidate"])].sort_values("candidate")
    reference_test = test_metrics[test_metrics["family"].eq("reference")].sort_values("candidate")
    lines = [
        "# PP-ROUTE-CF7 Warm-lite Tail Guard",
        "",
        "## 1. 목적",
        "",
        "CF5/CF6에서 확인된 Warm-lite unified의 남은 약점인 p95/RMSE tail 안정성을 개선한다.",
        "",
        "## 2. 설계",
        "",
        "- Warm train으로 unified Warm-lite stack을 seed 3개 재학습한다.",
        "- Warm validation에서 residual clip, 불확실성 조건부 감쇠, 검증셋 보정층 후보를 평가한다.",
        "- 후보 선택은 validation에서 수행하고, Warm fixed-test 607건은 최종 확인에만 사용한다.",
        "- 선택 기준은 p95 우선이며, validation MAPE와 MdAPE가 current 대비 +0.005를 넘게 악화되는 후보는 p95 선택에서 제외한다.",
        "",
        "## 3. 데이터 감사",
        "",
        "```json",
        json.dumps(audit, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 4. Validation Top Candidates by p95",
        "",
        md_table(top_val, ["candidate", "family", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 5. Selected Candidates",
        "",
        md_table(selected, ["candidate", "family", "selection_reason", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 10),
        "",
        "## 6. Test Reference Metrics",
        "",
        md_table(reference_test, ["candidate", "family", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 7. Selected Candidate Test Metrics",
        "",
        md_table(top_test, ["candidate", "family", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 8. Test Paired vs Current Warm-lite",
        "",
        md_table(paired_test, ["candidate", "n", "candidate_better_share", "current_better_share", "median_ape_delta_current_minus_candidate", "mean_ape_delta_current_minus_candidate"], 20),
        "",
        "## 9. 1차 판단",
        "",
    ]
    if not selected_test.empty:
        current_test = test_metrics[test_metrics["candidate"].eq("Warm-lite current s0.50 cap0.10")].iloc[0]
        best_test = selected_test.sort_values(["p95_APE", "MAPE", "MdAPE"]).iloc[0]
        lines.extend(
            [
                f"- Selected 중 test p95 최저 후보: `{best_test['candidate']}`.",
                f"- current 대비 test p95 delta: `{float(best_test['p95_APE'] - current_test['p95_APE']):.6f}`.",
                f"- current 대비 test MAPE delta: `{float(best_test['MAPE'] - current_test['MAPE']):.6f}`.",
                f"- current 대비 test RMSE_log delta: `{float(best_test['RMSE_log'] - current_test['RMSE_log']):.6f}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## 10. Config",
            "",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()
    train, val, test, audit = load_frames()

    seed_parts = []
    train_audit = []
    for seed in SEEDS:
        seed_start = time.time()
        train_s, stack = train_unified_stack(train, seed)
        train_audit.append(
            {
                "seed": seed,
                "train_rows": int(len(train_s)),
                "train_artists": int(train_s["artist_key"].astype(str).nunique()),
                "median_train_rows_per_artist": float(train_s.groupby(train_s["artist_key"].astype(str)).size().median()),
            }
        )
        seed_parts.append(predict_split(train, val, stack, seed, "validation"))
        seed_parts.append(predict_split(train, test, stack, seed, "test"))
        print(
            json.dumps(
                {
                    "done": "seed",
                    "seed": seed,
                    "validation_rows": len(val),
                    "test_rows": len(test),
                    "seconds": round(time.time() - seed_start, 2),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    seed_preds = pd.concat(seed_parts, ignore_index=True)
    mean_preds = seed_mean_features(seed_preds)
    val_mean = mean_preds[mean_preds["split"].eq("validation")].copy().reset_index(drop=True)
    test_mean = mean_preds[mean_preds["split"].eq("test")].copy().reset_index(drop=True)

    specs = candidate_grid(val_mean)
    val_rule_metrics, val_rule_preds = evaluate_rule_candidates("validation", val_mean, specs)
    test_rule_metrics, test_rule_preds = evaluate_rule_candidates("test", test_mean, specs)

    meta_val_metrics, meta_val_preds, meta_test_preds = fit_meta_candidates(val_mean, test_mean)
    meta_test_rows = []
    for candidate, part in meta_test_preds.groupby("candidate", sort=True):
        row = {"split": "test", "candidate": candidate, "family": "meta_calibrator", "selection_source": "validation_fit"}
        row.update(metrics(part["actual_price"].to_numpy(), part["actual_log"].to_numpy(), part["pred_log"].to_numpy()))
        meta_test_rows.append(row)
    meta_test_metrics = pd.DataFrame(meta_test_rows)

    warm_val = load_warm_operational(set(val["_track6_row_id"].astype(int)), "validation_oof")
    warm_test = load_warm_operational(set(test["_track6_row_id"].astype(int)), "test")
    val_reference = baseline_rows("validation", val_mean, warm_val)
    test_reference = baseline_rows("test", test_mean, warm_test)

    validation_metrics = pd.concat([val_reference, val_rule_metrics, meta_val_metrics], ignore_index=True, sort=False)
    test_metrics = pd.concat([test_reference, test_rule_metrics, meta_test_metrics], ignore_index=True, sort=False)

    selected = select_candidates(validation_metrics[validation_metrics["candidate"].isin(val_rule_metrics["candidate"])].copy())
    current_val_reference = val_reference[val_reference["candidate"].eq("Warm-lite current s0.50 cap0.10")].iloc[0]
    meta_selected = select_meta_candidates(meta_val_metrics, current_val_reference)
    selected = pd.concat([selected, meta_selected], ignore_index=True, sort=False).drop_duplicates("candidate").reset_index(drop=True)
    selected_test = test_metrics[test_metrics["candidate"].isin(selected["candidate"])].copy()

    selected_test_preds = pd.concat(
        [
            test_rule_preds[test_rule_preds["candidate"].isin(selected["candidate"])],
            meta_test_preds[meta_test_preds["candidate"].isin(selected["candidate"])],
        ],
        ignore_index=True,
        sort=False,
    )
    paired_test = paired_vs_current(test_mean, selected_test_preds)

    seed_preds.to_csv(EXP / "outputs" / "seed_level_predictions.csv", index=False)
    mean_preds.to_csv(EXP / "outputs" / "seed_mean_feature_predictions.csv", index=False)
    val_rule_metrics.to_csv(EXP / "outputs" / "validation_rule_candidate_metrics.csv", index=False)
    test_rule_metrics.to_csv(EXP / "outputs" / "test_rule_candidate_metrics.csv", index=False)
    meta_val_metrics.to_csv(EXP / "outputs" / "validation_meta_candidate_metrics.csv", index=False)
    meta_test_metrics.to_csv(EXP / "outputs" / "test_meta_candidate_metrics.csv", index=False)
    validation_metrics.to_csv(EXP / "outputs" / "validation_all_candidate_metrics.csv", index=False)
    test_metrics.to_csv(EXP / "outputs" / "test_all_candidate_metrics.csv", index=False)
    selected.to_csv(EXP / "outputs" / "selected_candidates_from_validation.csv", index=False)
    selected_test.to_csv(EXP / "outputs" / "selected_candidates_test_metrics.csv", index=False)
    paired_test.to_csv(EXP / "outputs" / "selected_candidates_test_paired_vs_current.csv", index=False)
    val_rule_preds.to_csv(EXP / "outputs" / "validation_rule_candidate_predictions.csv", index=False)
    test_rule_preds.to_csv(EXP / "outputs" / "test_rule_candidate_predictions.csv", index=False)
    meta_val_preds.to_csv(EXP / "outputs" / "validation_meta_candidate_predictions.csv", index=False)
    meta_test_preds.to_csv(EXP / "outputs" / "test_meta_candidate_predictions.csv", index=False)
    pd.DataFrame(train_audit).to_csv(EXP / "outputs" / "training_audit.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF7",
        "experiment_slug": EXP.name,
        "seeds": SEEDS,
        "base_eval_set": "Warm validation + Warm fixed-test",
        "selection_rule": "Choose on validation. p95 candidates must keep MAPE and MdAPE within +0.005 absolute of current_s05_cap010.",
        "candidate_families": [
            "residual_grid",
            "asymmetric_cap",
            "width_guard",
            "full_lean_gap_guard",
            "correction_size_guard",
            "low_history_width_guard",
            "meta_calibrator",
        ],
        "audit": audit,
        "training_audit": train_audit,
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(validation_metrics, test_metrics, selected, selected_test, paired_test, audit, config)

    print("[selected candidates from validation]")
    print(selected.to_string(index=False))
    print("\n[test selected metrics]")
    print(selected_test.sort_values(["p95_APE", "MAPE", "MdAPE"]).to_string(index=False))
    print("\n[test reference metrics]")
    print(test_reference.to_string(index=False))
    print("\n[test paired vs current]")
    print(paired_test.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
