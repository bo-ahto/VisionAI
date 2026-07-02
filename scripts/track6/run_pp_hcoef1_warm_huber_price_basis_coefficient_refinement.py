#!/usr/bin/env python3
"""Run PP-HCOEF1 Warm Huber price-basis coefficient refinement.

This experiment keeps the current Warm candidate fixed as the reference, then
tests whether a small set of interpretable price-basis signals can improve it:

1. Current 70:30 Warm candidate.
2. Existing compact defensive Warm candidate.
3. Existing comparable-stat Huber candidate.
4. Shrunk comparable prior and a Huber refit using that prior.

Candidate selection is based on validation cross-fit / deterministic validation
metrics. Fixed test and the 0604 labelled file are confirmation checks.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svcshrink1_warm_comparable_prior_shrinkage as shrink1  # noqa: E402
import run_pp_svcshrink2_warm_huber_shrunk_comparable_refit as shrink2  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF1"
EXP_SLUG = "PP-HCOEF1_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

TRAIN = REPO / "data" / "track6_split" / "track6_train.csv"
VAL = REPO / "data" / "track6_split" / "track6_val_warm.csv"
TEST = REPO / "data" / "track6_split" / "track6_test_warm.csv"
OPS = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "operational"
    / "outputs"
    / "0604_evaluation"
    / "operational_predictions_with_actual.csv"
)
SVC5_PRED = REPO / "experiments" / "track6" / "PP-SVC5_warm_multilevel_comparable_stats" / "outputs" / "predictions.csv"
SVC5_FEATURES = {
    "validation": REPO
    / "experiments"
    / "track6"
    / "PP-SVC5_warm_multilevel_comparable_stats"
    / "outputs"
    / "comparable_multilevel_features_validation.csv",
    "test": REPO
    / "experiments"
    / "track6"
    / "PP-SVC5_warm_multilevel_comparable_stats"
    / "outputs"
    / "comparable_multilevel_features_test.csv",
}

REFERENCE = "current_70_30"
SEED = 20260607
N_FOLDS = 5
SHRINK_K = 5.0

SOURCE_CANDIDATES = {
    "blend_svcnum_ppv8_wsvc_0.70": "current_70_30",
    "pp_v8_compact_blend_mape_guarded": "ppv8_defensive",
    "fallback_numeric": "svc_fallback",
    "baseline_huber": "baseline_huber",
}

META_FEATURE_SETS = {
    "basis3": ["ppv8_defensive", "svc_fallback", "shrunk_huber_refit"],
    "basis5": ["current_70_30", "ppv8_defensive", "svc_fallback", "shrunk_huber_refit", "shrunk_svc_prior"],
    "basis_reliability": [
        "current_70_30",
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "raw_svc_prior",
        "log_area",
        "svc_group_n_log",
        "current_ppv8_gap",
        "current_shrunk_huber_gap",
        "raw_shrunk_prior_gap",
    ],
}

RESIDUAL_FEATURE_SETS = {
    "resid_basis_gap": [
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "current_ppv8_gap",
        "current_shrunk_huber_gap",
        "raw_shrunk_prior_gap",
        "svc_group_n_log",
    ],
    "resid_basis_size_reliability": [
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "log_area",
        "svc_group_n_log",
        "svc_prior_iqr",
        "current_ppv8_gap",
        "current_shrunk_huber_gap",
        "raw_shrunk_prior_gap",
    ],
}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    resid = actual_log - np.asarray(pred_log, dtype=float)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean(resid**2))),
    }


def norm_str(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def load_source_frame(split: str) -> pd.DataFrame:
    path = VAL if split == "validation" else TEST
    base = pd.read_csv(path, low_memory=False)
    base = base[
        [
            "_track6_row_id",
            "price_krw",
            "ln_price_krw",
            "artist_key",
            "artist_name_ko",
            "log_area",
            "area_cm2",
            "medium_category",
            "support_category",
            "medium_support_bucket",
        ]
    ].copy()
    base["actual_price"] = pd.to_numeric(base["price_krw"], errors="coerce")
    base["actual_log"] = pd.to_numeric(base["ln_price_krw"], errors="coerce")
    return base


def pivot_svc5_predictions() -> dict[str, pd.DataFrame]:
    pred = pd.read_csv(SVC5_PRED, low_memory=False)
    pred = pred[pred["candidate"].isin(SOURCE_CANDIDATES)].copy()
    out: dict[str, pd.DataFrame] = {}
    for split in ["validation", "test"]:
        part = pred[pred["split"].eq(split)].copy()
        wide = part.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last")
        wide = wide.rename(columns=SOURCE_CANDIDATES).reset_index()
        out[split] = wide
    return out


def train_shrunk_huber_refit() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], np.ndarray]:
    train_df = pd.read_csv(TRAIN, low_memory=False)
    train_keys, size_edges = shrink1.prep(train_df, None)
    y_train = pd.to_numeric(train_df["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    groups, global_median = shrink1.train_groups(train_keys, y_train)
    _, oof_shrunk = shrink2.oof_comparable(train_keys, y_train)

    train_base = shrink2.base_frame(train_df)
    train_base["cmp_median"] = oof_shrunk

    eval_x: dict[str, pd.DataFrame] = {}
    raw_prior: dict[str, np.ndarray] = {}
    shrunk_prior: dict[str, np.ndarray] = {}

    for split, path in [("validation", VAL), ("test", TEST)]:
        df = pd.read_csv(path, low_memory=False)
        keys, _ = shrink1.prep(df, size_edges)
        raw_prior[split] = shrink1.raw_prior(keys, groups, global_median)
        shrunk_prior[split] = shrink1.shrunk_prior(keys, groups, global_median, SHRINK_K)
        frame = shrink2.base_frame(df)
        frame["cmp_median"] = shrunk_prior[split]
        eval_x[split] = frame

    ops = pd.read_csv(OPS, low_memory=False)
    ops = ops[ops["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(ops.get("actual_price_usd_equiv"), errors="coerce")
    ops = ops[~(usd < 50.0)].copy()
    ops_keys, _ = shrink1.prep(ops, size_edges)
    raw_prior["0604_ex50"] = shrink1.raw_prior(ops_keys, groups, global_median)
    shrunk_prior["0604_ex50"] = shrink1.shrunk_prior(ops_keys, groups, global_median, SHRINK_K)
    ops_x = shrink2.base_frame(ops)
    ops_x["cmp_median"] = shrunk_prior["0604_ex50"]
    eval_x["0604_ex50"] = ops_x

    pred = shrink2.fit_predict(
        train_base,
        y_train,
        eval_x,
        shrink2.NUMERIC_BASE + ["cmp_median"],
    )
    return pred, raw_prior, shrunk_prior, size_edges


def build_validation_test_frames(shrunk_pred: dict[str, np.ndarray], raw_prior: dict[str, np.ndarray], shrunk_prior: dict[str, np.ndarray]) -> dict[str, pd.DataFrame]:
    source_pred = pivot_svc5_predictions()
    frames: dict[str, pd.DataFrame] = {}
    for split in ["validation", "test"]:
        frame = load_source_frame(split)
        frame = frame.merge(source_pred[split], on="_track6_row_id", how="left")
        features = pd.read_csv(SVC5_FEATURES[split], low_memory=False)
        frame = frame.merge(
            features[
                [
                    "_track6_row_id",
                    "svc_group_level",
                    "svc_coverage_tier",
                    "svc_group_n",
                    "svc_group_n_log",
                    "svc_group_log_price_iqr",
                ]
            ],
            on="_track6_row_id",
            how="left",
        )
        frame["shrunk_huber_refit"] = shrunk_pred[split]
        frame["raw_svc_prior"] = raw_prior[split]
        frame["shrunk_svc_prior"] = shrunk_prior[split]
        frames[split] = add_derived_features(frame, split)
    return frames


def build_0604_frame(shrunk_pred: dict[str, np.ndarray], raw_prior: dict[str, np.ndarray], shrunk_prior: dict[str, np.ndarray]) -> pd.DataFrame:
    ops = pd.read_csv(OPS, low_memory=False)
    ops = ops[ops["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(ops.get("actual_price_usd_equiv"), errors="coerce")
    ops = ops[~(usd < 50.0)].copy().reset_index(drop=True)
    frame = pd.DataFrame()
    frame["_track6_row_id"] = ops["_track6_row_id"]
    frame["actual_price"] = pd.to_numeric(ops["actual_price_krw"], errors="coerce")
    frame["actual_log"] = np.log(np.clip(frame["actual_price"].to_numpy(dtype=float), 1.0, None))
    frame["artist_key"] = norm_str(ops["artist_key"])
    frame["artist_name_ko"] = norm_str(ops.get("artist_name", pd.Series([""] * len(ops))))
    frame["log_area"] = pd.to_numeric(ops["log_area"], errors="coerce")
    frame["area_cm2"] = pd.to_numeric(ops["area_cm2"], errors="coerce")
    frame["medium_category"] = norm_str(ops["medium_category"])
    frame["support_category"] = norm_str(ops["support_category"])
    frame["medium_support_bucket"] = norm_str(ops["medium_support_bucket"])
    frame["current_70_30"] = pd.to_numeric(ops["v01_operational_pred_log"], errors="coerce")
    frame["ppv8_defensive"] = pd.to_numeric(ops["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce")
    frame["svc_fallback"] = pd.to_numeric(ops["svc_numeric_seed_mean_pred_log"], errors="coerce")
    frame["baseline_huber"] = pd.to_numeric(ops["pp_v2_defensive_pred_log"], errors="coerce")
    frame["shrunk_huber_refit"] = shrunk_pred["0604_ex50"]
    frame["raw_svc_prior"] = raw_prior["0604_ex50"]
    frame["shrunk_svc_prior"] = shrunk_prior["0604_ex50"]
    frame["svc_group_level"] = norm_str(ops["svc_group_level"])
    frame["svc_coverage_tier"] = norm_str(ops["svc_coverage_tier"])
    frame["svc_group_n"] = pd.to_numeric(ops["svc_group_n"], errors="coerce")
    frame["svc_group_n_log"] = np.log1p(frame["svc_group_n"].fillna(0.0))
    frame["svc_group_log_price_iqr"] = pd.to_numeric(ops.get("svc_group_log_price_iqr"), errors="coerce")
    return add_derived_features(frame, "0604_ex50")


def add_derived_features(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    out = frame.copy()
    out["split"] = split
    for col in [
        "current_70_30",
        "ppv8_defensive",
        "svc_fallback",
        "baseline_huber",
        "shrunk_huber_refit",
        "raw_svc_prior",
        "shrunk_svc_prior",
        "log_area",
        "svc_group_n_log",
        "svc_group_log_price_iqr",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["svc_prior_iqr"] = out["svc_group_log_price_iqr"].fillna(out["svc_group_log_price_iqr"].median())
    out["current_ppv8_gap"] = out["current_70_30"] - out["ppv8_defensive"]
    out["current_shrunk_huber_gap"] = out["current_70_30"] - out["shrunk_huber_refit"]
    out["raw_shrunk_prior_gap"] = out["raw_svc_prior"] - out["shrunk_svc_prior"]
    out["svc_n_low_flag"] = (pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0) < 10).astype(float)
    out["svc_n_high_flag"] = (pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0) >= 30).astype(float)
    return out


def linear_pipeline(kind: str, alpha: float) -> Pipeline:
    if kind == "huber":
        model = HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=5000)
    elif kind == "ridge":
        model = Ridge(alpha=alpha)
    else:
        raise ValueError(f"Unknown model kind: {kind}")
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", model),
        ]
    )


def crossfit_predict(frame: pd.DataFrame, features: list[str], target: np.ndarray, kind: str, alpha: float) -> np.ndarray:
    pred = np.full(len(frame), np.nan, dtype=float)
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for train_idx, hold_idx in kf.split(np.arange(len(frame))):
        model = linear_pipeline(kind, alpha)
        model.fit(frame.iloc[train_idx][features], target[train_idx])
        pred[hold_idx] = np.asarray(model.predict(frame.iloc[hold_idx][features]), dtype=float)
    return pred


def fit_full_predict(
    validation: pd.DataFrame,
    eval_frame: pd.DataFrame,
    features: list[str],
    target: np.ndarray,
    kind: str,
    alpha: float,
) -> tuple[np.ndarray, Pipeline]:
    model = linear_pipeline(kind, alpha)
    model.fit(validation[features], target)
    pred = np.asarray(model.predict(eval_frame[features]), dtype=float)
    return pred, model


def clip_to_component_range(frame: pd.DataFrame, pred: np.ndarray, margin: float) -> np.ndarray:
    cols = ["current_70_30", "ppv8_defensive", "svc_fallback", "shrunk_huber_refit", "shrunk_svc_prior"]
    lo = frame[cols].min(axis=1).to_numpy(dtype=float) - margin
    hi = frame[cols].max(axis=1).to_numpy(dtype=float) + margin
    return np.clip(np.asarray(pred, dtype=float), lo, hi)


def coefficient_frame(model: Pipeline, candidate: str, features: list[str], model_type: str, target: str) -> pd.DataFrame:
    reg = model.named_steps["model"]
    coef = getattr(reg, "coef_", np.full(len(features), np.nan))
    intercept = float(getattr(reg, "intercept_", np.nan))
    rows = [
        {
            "candidate": candidate,
            "model_type": model_type,
            "target": target,
            "feature": feature,
            "coefficient_on_scaled_feature": float(coef[idx]),
            "abs_coefficient": float(abs(coef[idx])),
            "intercept": intercept,
        }
        for idx, feature in enumerate(features)
    ]
    return pd.DataFrame(rows).sort_values("abs_coefficient", ascending=False)


def add_prediction(
    pred_rows: list[pd.DataFrame],
    candidate: str,
    method: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    selected_on_validation: bool,
) -> None:
    pred_price = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1_000.0, None)
    ape = np.abs(pred_price - frame["actual_price"].to_numpy(dtype=float)) / np.clip(
        frame["actual_price"].to_numpy(dtype=float), 1.0, None
    )
    pred_rows.append(
        pd.DataFrame(
            {
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "method": method,
                "split": frame["split"].to_numpy(),
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame["artist_key"].astype(str).to_numpy(),
                "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
                "actual_log": frame["actual_log"].to_numpy(dtype=float),
                "actual_price": frame["actual_price"].to_numpy(dtype=float),
                "pred_log": np.asarray(pred_log, dtype=float),
                "pred_price": pred_price,
                "residual_log": frame["actual_log"].to_numpy(dtype=float) - np.asarray(pred_log, dtype=float),
                "ape": ape,
                "selected_on_validation": selected_on_validation,
            }
        )
    )


def evaluate_prediction(candidate: str, method: str, frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    return {
        "candidate": candidate,
        "method": method,
        "split": str(frame["split"].iloc[0]),
        "n": int(len(frame)),
        **metric_from_arrays(
            frame["actual_price"].to_numpy(dtype=float),
            frame["actual_log"].to_numpy(dtype=float),
            np.asarray(pred_log, dtype=float),
        ),
    }


def reference_metrics(metrics: pd.DataFrame, split: str) -> pd.Series:
    row = metrics[(metrics["split"].eq(split)) & (metrics["candidate"].eq(REFERENCE))]
    if row.empty:
        raise RuntimeError(f"Missing reference metrics for {split}")
    return row.iloc[0]


def rank_validation(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    ref = reference_metrics(metrics, "validation")
    val["score"] = (
        0.40 * val["MdAPE"] / ref["MdAPE"]
        + 0.35 * val["MAPE"] / ref["MAPE"]
        + 0.25 * val["p95_APE"] / ref["p95_APE"]
    )
    val["beats_ref_metric_count"] = (
        (val["MdAPE"] < ref["MdAPE"]).astype(int)
        + (val["MAPE"] < ref["MAPE"]).astype(int)
        + (val["p95_APE"] < ref["p95_APE"]).astype(int)
    )
    return val.sort_values(["score", "MdAPE", "MAPE", "p95_APE"])


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = rank_validation(metrics)
    ref = reference_metrics(metrics, "validation")
    rows: list[dict[str, Any]] = []
    objectives = {
        "balanced_score": val,
        "mdape_primary": val[val["MAPE"].le(ref["MAPE"] * 1.03) & val["p95_APE"].le(ref["p95_APE"] * 1.05)].sort_values("MdAPE"),
        "mape_guarded": val[val["MdAPE"].le(ref["MdAPE"] * 1.08) & val["p95_APE"].le(ref["p95_APE"] * 1.05)].sort_values("MAPE"),
        "p95_guarded": val[val["MdAPE"].le(ref["MdAPE"] * 1.08) & val["MAPE"].le(ref["MAPE"] * 1.05)].sort_values("p95_APE"),
    }
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    ops = metrics[metrics["split"].eq("0604_ex50")].set_index("candidate")
    for objective, ranked in objectives.items():
        if ranked.empty:
            continue
        selected = ranked.iloc[0]
        row: dict[str, Any] = {
            "selection_objective": objective,
            "selected_candidate": selected["candidate"],
            "method": selected["method"],
            "val_MdAPE": selected["MdAPE"],
            "val_MAPE": selected["MAPE"],
            "val_p95_APE": selected["p95_APE"],
            "val_score": selected["score"],
        }
        if selected["candidate"] in test.index:
            t = test.loc[selected["candidate"]]
            row.update({"test_MdAPE": t["MdAPE"], "test_MAPE": t["MAPE"], "test_p95_APE": t["p95_APE"]})
        if selected["candidate"] in ops.index:
            o = ops.loc[selected["candidate"]]
            row.update({"ops0604_MdAPE": o["MdAPE"], "ops0604_MAPE": o["MAPE"], "ops0604_p95_APE": o["p95_APE"]})
        rows.append(row)
    return pd.DataFrame(rows).drop_duplicates("selected_candidate")


def bootstrap_summary(predictions: pd.DataFrame, selected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    test = predictions[predictions["split"].eq("test")].copy()
    metrics = (
        test.groupby("candidate", as_index=False)
        .agg(MdAPE=("ape", "median"), MAPE=("ape", "mean"))
        .sort_values(["MdAPE", "MAPE"])
    )
    candidate_pool = [REFERENCE]
    candidate_pool.extend(selected["selected_candidate"].dropna().astype(str).tolist())
    candidate_pool.extend(metrics.head(8)["candidate"].astype(str).tolist())
    candidate_pool = list(dict.fromkeys(candidate_pool))

    wide = test[test["candidate"].isin(candidate_pool)].pivot_table(
        index=["_track6_row_id", "artist_key", "actual_price", "actual_log"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    )
    candidate_pool = [c for c in candidate_pool if c in wide.columns and wide[c].notna().all()]
    if REFERENCE not in candidate_pool:
        raise RuntimeError("Reference candidate missing in bootstrap pool")

    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(SEED)
    artists = wide.reset_index()["artist_key"].astype(str).to_numpy()
    unique_artists = np.unique(artists)
    actual_price = wide.reset_index()["actual_price"].to_numpy(dtype=float)
    actual_log = wide.reset_index()["actual_log"].to_numpy(dtype=float)

    for sample_type in ["row_bootstrap", "artist_bootstrap"]:
        for sample_idx in range(300):
            if sample_type == "row_bootstrap":
                indices = rng.integers(0, len(wide), size=len(wide))
            else:
                sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                parts = [np.flatnonzero(artists == artist) for artist in sampled_artists]
                indices = np.concatenate(parts)
            ref_metric = metric_from_arrays(actual_price[indices], actual_log[indices], wide[REFERENCE].to_numpy(dtype=float)[indices])
            for candidate in candidate_pool:
                cand_metric = metric_from_arrays(actual_price[indices], actual_log[indices], wide[candidate].to_numpy(dtype=float)[indices])
                rows.append(
                    {
                        "sample_type": sample_type,
                        "sample_idx": sample_idx,
                        "candidate": candidate,
                        "delta_MdAPE": cand_metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE": cand_metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE": cand_metric["p95_APE"] - ref_metric["p95_APE"],
                    }
                )
    samples = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"], observed=False):
        summary_rows.append(
            {
                "sample_type": sample_type,
                "candidate": candidate,
                "mean_delta_MdAPE": float(group["delta_MdAPE"].mean()),
                "mean_delta_MAPE": float(group["delta_MAPE"].mean()),
                "mean_delta_p95_APE": float(group["delta_p95_APE"].mean()),
                "MdAPE_improve_prob": float((group["delta_MdAPE"] < 0).mean()),
                "MAPE_improve_prob": float((group["delta_MAPE"] < 0).mean()),
                "p95_improve_prob": float((group["delta_p95_APE"] < 0).mean()),
            }
        )
    return pd.DataFrame(summary_rows).sort_values(["sample_type", "mean_delta_MdAPE"]), samples


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    selected = predictions[predictions["split"].isin(["test", "0604_ex50"])].copy()
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in selected.groupby(["split", "candidate"], observed=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "candidate"])


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(v: Any) -> str:
        if isinstance(v, (float, np.floating)):
            return f"{float(v):.4f}"
        return str(v)

    cols = [str(c) for c in data.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2,h3{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    bootstrap: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
) -> None:
    test = metrics[metrics["split"].eq("test")].copy()
    ref_test = reference_metrics(metrics, "test")
    top_test = test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    val_top = rank_validation(metrics).head(12)

    better = test[
        ((test["MdAPE"] < ref_test["MdAPE"]).astype(int) + (test["MAPE"] < ref_test["MAPE"]).astype(int) + (test["p95_APE"] < ref_test["p95_APE"]).astype(int))
        >= 2
    ].sort_values(["MdAPE", "MAPE", "p95_APE"])

    decision = "반복 검증 후보 없음"
    if not selected.empty:
        selected_names = set(selected["selected_candidate"].astype(str))
        selected_test = test[test["candidate"].isin(selected_names)].copy()
        if not selected_test.empty:
            selected_test["improved_metric_count"] = (
                (selected_test["MdAPE"] < ref_test["MdAPE"]).astype(int)
                + (selected_test["MAPE"] < ref_test["MAPE"]).astype(int)
                + (selected_test["p95_APE"] < ref_test["p95_APE"]).astype(int)
            )
            best_selected = selected_test.sort_values(["improved_metric_count", "MdAPE"], ascending=[False, True]).iloc[0]
            if best_selected["improved_metric_count"] >= 2:
                decision = (
                    f"반복 검증 후보: `{best_selected['candidate']}`. "
                    f"test MdAPE/MAPE/p95 {best_selected['MdAPE']:.4f}/{best_selected['MAPE']:.4f}/{best_selected['p95_APE']:.4f}."
                )
            else:
                decision = "validation 선택 후보가 fixed test에서 2개 이상 지표 개선 조건을 만족하지 못해 기본 후보 유지"

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 기준가/계수 고도화 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: Warm Huber에서 기준가 생성 방식과 피처별 계수 조정으로 기존 70:30 후보를 넘을 수 있는지 확인.",
            "- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.",
            "- 선택 원칙: validation 내부 교차검증 또는 validation 지표로 후보를 고르고, fixed test와 0604는 확인용으로 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}",
            f"- 현재 기준 test: MdAPE `{ref_test['MdAPE']:.4f}`, MAPE `{ref_test['MAPE']:.4f}`, p95 `{ref_test['p95_APE']:.4f}`, RMSE_log `{ref_test['RMSE_log']:.4f}`.",
            "- test만 좋은 후보는 채택하지 않고 bootstrap 및 추가 split 재검증 대상으로만 분리.",
            "",
            "## 2. Validation 상위 후보",
            "",
            markdown_table(val_top[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "score", "beats_ref_metric_count"]].round(4)),
            "",
            "## 3. Validation 선택 후보의 test/0604 확인",
            "",
            markdown_table(selected.round(4)),
            "",
            "## 4. Fixed test 상위 후보",
            "",
            markdown_table(top_test[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4)),
            "",
            "## 5. 기준 후보 대비 2개 이상 지표 개선 후보",
            "",
            markdown_table(better[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4), max_rows=20),
            "",
            "## 6. Bootstrap 안정성 요약",
            "",
            markdown_table(bootstrap.round(4), max_rows=24),
            "",
            "## 7. 주요 Huber/Ridge 계수",
            "",
            "- 계수는 표준화된 피처 기준이다. 절대 가격 단위의 직접 계수는 아니며, 방향성과 상대적 영향 확인용이다.",
            markdown_table(coefficients.head(40).round(5)),
            "",
            "## 8. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=40),
            "",
            "## 9. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/bootstrap_samples.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef1_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef1_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    shrunk_pred, raw_prior, shrunk_prior, _ = train_shrunk_huber_refit()
    frames = build_validation_test_frames(shrunk_pred, raw_prior, shrunk_prior)
    frames["0604_ex50"] = build_0604_frame(shrunk_pred, raw_prior, shrunk_prior)

    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []

    # Direct component baselines.
    baseline_cols = [
        "current_70_30",
        "ppv8_defensive",
        "svc_fallback",
        "baseline_huber",
        "shrunk_huber_refit",
        "raw_svc_prior",
        "shrunk_svc_prior",
    ]
    for candidate in baseline_cols:
        for split, frame in frames.items():
            pred = frame[candidate].to_numpy(dtype=float)
            metrics_rows.append(evaluate_prediction(candidate, "basis_component", frame, pred))
            add_prediction(pred_rows, candidate, "basis_component", frame, pred, selected_on_validation=False)

    # Deterministic weight grids. These do not fit on test.
    for w_current in np.round(np.arange(0.0, 1.01, 0.05), 2):
        candidate = f"blend_current_shrunk_huber_wcurrent_{w_current:.2f}"
        for split, frame in frames.items():
            pred = w_current * frame["current_70_30"].to_numpy(dtype=float) + (1.0 - w_current) * frame["shrunk_huber_refit"].to_numpy(dtype=float)
            metrics_rows.append(evaluate_prediction(candidate, "current_shrunk_huber_weight_grid", frame, pred))
            add_prediction(pred_rows, candidate, "current_shrunk_huber_weight_grid", frame, pred, selected_on_validation=False)

    for w_ppv8 in np.round(np.arange(0.0, 1.01, 0.10), 2):
        for w_svc in np.round(np.arange(0.0, 1.0 - w_ppv8 + 0.001, 0.10), 2):
            w_shr = round(1.0 - w_ppv8 - w_svc, 2)
            if w_shr < -1e-9:
                continue
            candidate = f"blend_ppv8_svc_shrunk_{w_ppv8:.1f}_{w_svc:.1f}_{w_shr:.1f}"
            for split, frame in frames.items():
                pred = (
                    w_ppv8 * frame["ppv8_defensive"].to_numpy(dtype=float)
                    + w_svc * frame["svc_fallback"].to_numpy(dtype=float)
                    + w_shr * frame["shrunk_huber_refit"].to_numpy(dtype=float)
                )
                metrics_rows.append(evaluate_prediction(candidate, "basis_weight_simplex_grid", frame, pred))
                add_prediction(pred_rows, candidate, "basis_weight_simplex_grid", frame, pred, selected_on_validation=False)

    # Cross-fit validation meta models; full validation fit for test and 0604.
    for feature_set_name, features in META_FEATURE_SETS.items():
        for kind, alphas in [("huber", [0.0001, 0.001, 0.01]), ("ridge", [0.1, 1.0, 10.0])]:
            for alpha in alphas:
                base_candidate = f"meta_{kind}_{feature_set_name}_alpha{alpha:g}"
                val_frame = frames["validation"]
                target = val_frame["actual_log"].to_numpy(dtype=float)
                val_pred = crossfit_predict(val_frame, features, target, kind, alpha)
                test_pred, model = fit_full_predict(val_frame, frames["test"], features, target, kind, alpha)
                ops_pred, _ = fit_full_predict(val_frame, frames["0604_ex50"], features, target, kind, alpha)
                split_preds = {"validation": val_pred, "test": test_pred, "0604_ex50": ops_pred}
                for margin in [None, 0.30]:
                    candidate = base_candidate if margin is None else f"{base_candidate}_clip0p30"
                    for split, frame in frames.items():
                        pred = split_preds[split]
                        if margin is not None:
                            pred = clip_to_component_range(frame, pred, margin)
                        metrics_rows.append(evaluate_prediction(candidate, f"meta_{kind}_crossfit_validation", frame, pred))
                        add_prediction(pred_rows, candidate, f"meta_{kind}_crossfit_validation", frame, pred, selected_on_validation=True)
                coef_rows.append(coefficient_frame(model, base_candidate, features, kind, "actual_log"))

    # Residual Huber correction over the current 70:30 candidate.
    for feature_set_name, features in RESIDUAL_FEATURE_SETS.items():
        for alpha in [0.0001, 0.001, 0.01]:
            val_frame = frames["validation"]
            residual_target = val_frame["actual_log"].to_numpy(dtype=float) - val_frame[REFERENCE].to_numpy(dtype=float)
            val_raw_corr = crossfit_predict(val_frame, features, residual_target, "huber", alpha)
            test_raw_corr, model = fit_full_predict(val_frame, frames["test"], features, residual_target, "huber", alpha)
            ops_raw_corr, _ = fit_full_predict(val_frame, frames["0604_ex50"], features, residual_target, "huber", alpha)
            raw_by_split = {"validation": val_raw_corr, "test": test_raw_corr, "0604_ex50": ops_raw_corr}
            coef_rows.append(coefficient_frame(model, f"residual_huber_{feature_set_name}_alpha{alpha:g}", features, "huber", "current_residual_log"))
            for cap in [0.03, 0.05, 0.08, 0.12]:
                for strength in [0.25, 0.50, 0.75, 1.00]:
                    candidate = f"residual_huber_{feature_set_name}_alpha{alpha:g}_cap{cap:.2f}_s{strength:.2f}"
                    for split, frame in frames.items():
                        correction = np.clip(raw_by_split[split], -cap, cap) * strength
                        pred = frame[REFERENCE].to_numpy(dtype=float) + correction
                        metrics_rows.append(evaluate_prediction(candidate, "current_residual_huber_correction", frame, pred))
                        add_prediction(pred_rows, candidate, "current_residual_huber_correction", frame, pred, selected_on_validation=True)

    metrics = pd.DataFrame(metrics_rows)
    predictions = pd.concat(pred_rows, ignore_index=True)
    coefficients = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    selected = select_validation_candidates(metrics)
    bootstrap, bootstrap_samples = bootstrap_summary(predictions, selected)
    residuals = residual_analysis(predictions[predictions["candidate"].isin(set(selected["selected_candidate"].astype(str)) | {REFERENCE})])

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coefficients.to_csv(out / "feature_coefficients.csv", index=False)
    selected.to_csv(out / "selected_validation_candidates.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    bootstrap.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    bootstrap_samples.to_csv(out / "bootstrap_samples.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "source_candidates": SOURCE_CANDIDATES,
        "meta_feature_sets": META_FEATURE_SETS,
        "residual_feature_sets": RESIDUAL_FEATURE_SETS,
        "selection_policy": "validation score: 0.40 MdAPE + 0.35 MAPE + 0.25 p95, fixed test confirmation",
        "shrink_k": SHRINK_K,
        "folds": N_FOLDS,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, selected, bootstrap, coefficients, residuals)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- validation selected candidates ---")
    print(selected.round(4).to_string(index=False))
    print("--- fixed test top 10 ---")
    print(
        metrics[metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(10)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
