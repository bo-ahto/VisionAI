#!/usr/bin/env python3
"""Run PP-HCOEF4: Warm Huber basis-generation refinement.

This experiment explicitly compares comparable-price bases before trying to
replace the current Warm candidate. Candidate choice is validation-only; fixed
test and the labelled 0604 file are confirmation checks.
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

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
from run_pp_svc1_comparable_stats_feature_validation import GROUP_DEFS  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF4"
EXP_SLUG = "PP-HCOEF4_warm_basis_generation_refinement"
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

REFERENCE = "current_70_30"
CURRENT_IMPROVED = "hcoef2_size_reliability_cap005_s050"
SEED = 20260608
N_FOLDS = 5

POLICIES = {
    "loose": {
        "artist_medium_support_size": 3,
        "artist_size": 3,
        "artist": 3,
        "medium_support_size": 20,
        "medium_category_support_size": 20,
        "medium_size": 30,
    },
    "default": {
        "artist_medium_support_size": 5,
        "artist_size": 5,
        "artist": 5,
        "medium_support_size": 30,
        "medium_category_support_size": 30,
        "medium_size": 50,
    },
    "strict": {
        "artist_medium_support_size": 10,
        "artist_size": 10,
        "artist": 10,
        "medium_support_size": 50,
        "medium_category_support_size": 50,
        "medium_size": 80,
    },
}

BASIS_FEATURE_SETS = {
    "basis_core": [
        REFERENCE,
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "basis_relaxed_price_log",
        "basis_relaxed_unit_area_log",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_relaxed_missing",
        "log_area",
    ],
    "basis_gap_reliability": [
        REFERENCE,
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "basis_relaxed_price_log",
        "basis_relaxed_unit_area_log",
        "basis_relaxed_vs_current_gap",
        "basis_relaxed_vs_svc_gap",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "svc_group_n_log",
        "svc_prior_iqr",
        "log_area",
    ],
    "basis_level_signals": [
        REFERENCE,
        "ppv8_defensive",
        "svc_fallback",
        "shrunk_huber_refit",
        "shrunk_svc_prior",
        "basis_artist_price_log",
        "basis_artist_size_price_log",
        "basis_artist_medium_support_size_price_log",
        "basis_relaxed_price_log",
        "basis_relaxed_n_log",
        "basis_artist_n_log",
        "basis_artist_size_n_log",
        "basis_artist_medium_support_size_n_log",
        "log_area",
    ],
}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def norm_str(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def size_edges_from_train(train: pd.DataFrame) -> np.ndarray:
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    edges = np.quantile(values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    edges[0] = -np.inf
    edges[-1] = np.inf
    return np.unique(edges)


def add_size_bucket(frame: pd.DataFrame, edges: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    labels = [f"q{i + 1}" for i in range(len(edges) - 1)]
    log_area = pd.to_numeric(out["log_area"], errors="coerce")
    out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
    out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
    return out


def load_feature_frame(path: Path, split: str, edges: np.ndarray) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    raw = add_size_bucket(raw, edges)
    out = raw[
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
            "size_bucket",
        ]
    ].copy()
    out["split"] = split
    out["actual_price"] = pd.to_numeric(out["price_krw"], errors="coerce")
    out["actual_log"] = pd.to_numeric(out["ln_price_krw"], errors="coerce")
    out["artist_key"] = norm_str(out["artist_key"])
    out["artist_name_ko"] = norm_str(out["artist_name_ko"])
    for col in ["medium_category", "support_category", "medium_support_bucket", "size_bucket"]:
        out[col] = norm_str(out[col])
    out["area_cm2"] = pd.to_numeric(out["area_cm2"], errors="coerce")
    out["log_area"] = pd.to_numeric(out["log_area"], errors="coerce")
    return out


def load_ops_frame(edges: np.ndarray) -> pd.DataFrame:
    raw = pd.read_csv(OPS, low_memory=False)
    raw = raw[raw["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(raw.get("actual_price_usd_equiv"), errors="coerce")
    raw = raw[~(usd < 50.0)].copy().reset_index(drop=True)
    raw["price_krw"] = pd.to_numeric(raw["actual_price_krw"], errors="coerce")
    raw["ln_price_krw"] = np.log(np.clip(raw["price_krw"].to_numpy(dtype=float), 1.0, None))
    raw["artist_name_ko"] = raw.get("artist_name", pd.Series([""] * len(raw), index=raw.index))
    raw = add_size_bucket(raw, edges)
    cols = [
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
        "size_bucket",
    ]
    out = raw[cols].copy()
    out["split"] = "0604_ex50"
    out["actual_price"] = pd.to_numeric(out["price_krw"], errors="coerce")
    out["actual_log"] = pd.to_numeric(out["ln_price_krw"], errors="coerce")
    out["artist_key"] = norm_str(out["artist_key"])
    out["artist_name_ko"] = norm_str(out["artist_name_ko"])
    for col in ["medium_category", "support_category", "medium_support_bucket", "size_bucket"]:
        out[col] = norm_str(out[col])
    out["area_cm2"] = pd.to_numeric(out["area_cm2"], errors="coerce")
    out["log_area"] = pd.to_numeric(out["log_area"], errors="coerce")
    out["_ops_current_70_30"] = pd.to_numeric(raw["v01_operational_pred_log"], errors="coerce")
    out["_ops_ppv8_defensive"] = pd.to_numeric(raw["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce")
    out["_ops_svc_fallback"] = pd.to_numeric(raw["svc_numeric_seed_mean_pred_log"], errors="coerce")
    out["_ops_baseline_huber"] = pd.to_numeric(raw["pp_v2_defensive_pred_log"], errors="coerce")
    out["_ops_svc_group_n_log"] = np.log1p(pd.to_numeric(raw.get("svc_group_n"), errors="coerce").fillna(0.0))
    return out


def source_ready(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["ln_price_krw"] = pd.to_numeric(out["ln_price_krw"], errors="coerce")
    out["area_cm2"] = pd.to_numeric(out["area_cm2"], errors="coerce")
    out["source_log_unit_area"] = out["ln_price_krw"] - np.log(np.clip(out["area_cm2"], 1.0, None))
    return out


def aggregate_basis(source: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if keys:
        grouped = source.groupby(keys, dropna=False, observed=False)
        return grouped.agg(
            price_median=("ln_price_krw", "median"),
            price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
            price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
            unit_area_median=("source_log_unit_area", "median"),
            n=("ln_price_krw", "size"),
        ).reset_index()
    return pd.DataFrame(
        [
            {
                "price_median": float(source["ln_price_krw"].median()),
                "price_q25": float(source["ln_price_krw"].quantile(0.25)),
                "price_q75": float(source["ln_price_krw"].quantile(0.75)),
                "unit_area_median": float(source["source_log_unit_area"].median()),
                "n": int(len(source)),
            }
        ]
    )


def merge_basis(source: pd.DataFrame, target: pd.DataFrame, level: str, keys: list[str], min_n: int) -> pd.DataFrame:
    stats = aggregate_basis(source, keys)
    if keys:
        merged = target[keys].merge(stats, on=keys, how="left")
    else:
        merged = pd.concat([target.reset_index(drop=True), pd.DataFrame([stats.iloc[0].to_dict()] * len(target))], axis=1)
    n = pd.to_numeric(merged["n"], errors="coerce")
    eligible = n.fillna(0).ge(min_n)
    out = pd.DataFrame({"_track6_row_id": target["_track6_row_id"].to_numpy()})
    price = pd.to_numeric(merged["price_median"], errors="coerce")
    unit = pd.to_numeric(merged["unit_area_median"], errors="coerce") + target["log_area"].to_numpy(dtype=float)
    iqr = pd.to_numeric(merged["price_q75"], errors="coerce") - pd.to_numeric(merged["price_q25"], errors="coerce")
    prefix = f"basis_{level}"
    out[f"{prefix}_price_log"] = np.where(eligible, price, np.nan)
    out[f"{prefix}_unit_area_log"] = np.where(eligible, unit, np.nan)
    out[f"{prefix}_n"] = np.where(eligible, n, 0.0)
    out[f"{prefix}_n_log"] = np.log1p(out[f"{prefix}_n"].astype(float))
    out[f"{prefix}_iqr"] = np.where(eligible, iqr, np.nan)
    out[f"{prefix}_covered"] = eligible.astype(float)
    return out


def basis_for_target(train: pd.DataFrame, target: pd.DataFrame, policy: str) -> pd.DataFrame:
    source = source_ready(train)
    parts: list[pd.DataFrame] = []
    for group_def in GROUP_DEFS:
        level = str(group_def["level"])
        min_n = int(POLICIES[policy][level])
        parts.append(merge_basis(source, target, level, list(group_def["keys"]), min_n))
    parts.append(merge_basis(source, target, "global", [], 1))
    out = target[["_track6_row_id"]].copy()
    for part in parts:
        out = out.merge(part, on="_track6_row_id", how="left")
    return out


def crossfit_basis(train: pd.DataFrame, policy: str) -> pd.DataFrame:
    pred_parts: list[pd.DataFrame] = []
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for source_idx, hold_idx in kf.split(train):
        pred_parts.append(basis_for_target(train.iloc[source_idx].copy(), train.iloc[hold_idx].copy(), policy))
    return pd.concat(pred_parts, ignore_index=True)


def relaxed_basis(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    out = frame.copy()
    levels = [
        "artist_medium_support_size",
        "artist_size",
        "artist",
        "medium_support_size",
        "medium_category_support_size",
        "medium_size",
        "global",
    ]
    price_cols = [f"basis_{level}_price_log" for level in levels]
    unit_cols = [f"basis_{level}_unit_area_log" for level in levels]
    n_cols = [f"basis_{level}_n" for level in levels]
    iqr_cols = [f"basis_{level}_iqr" for level in levels]

    price_stack = out[price_cols].to_numpy(dtype=float)
    unit_stack = out[unit_cols].to_numpy(dtype=float)
    n_stack = out[n_cols].to_numpy(dtype=float)
    iqr_stack = out[iqr_cols].to_numpy(dtype=float)
    first_idx = np.argmax(np.isfinite(price_stack), axis=1)
    row_idx = np.arange(len(out))
    out["basis_relaxed_price_log"] = price_stack[row_idx, first_idx]
    out["basis_relaxed_unit_area_log"] = unit_stack[row_idx, first_idx]
    out["basis_relaxed_n"] = n_stack[row_idx, first_idx]
    out["basis_relaxed_n_log"] = np.log1p(np.nan_to_num(out["basis_relaxed_n"].to_numpy(dtype=float), nan=0.0))
    out["basis_relaxed_iqr"] = iqr_stack[row_idx, first_idx]
    out["basis_relaxed_level"] = np.asarray(levels, dtype=object)[first_idx]
    out["basis_relaxed_missing"] = (~np.isfinite(out["basis_relaxed_price_log"].to_numpy(dtype=float))).astype(float)

    # Reliability shrink: small comparable groups move toward the artist/global fallback.
    artist = out["basis_artist_price_log"].fillna(out["basis_global_price_log"])
    base = out["basis_relaxed_price_log"].fillna(out["basis_global_price_log"])
    n = pd.to_numeric(out["basis_relaxed_n"], errors="coerce").fillna(0.0)
    weight = np.clip(n / (n + 8.0), 0.0, 1.0)
    out["basis_shrunk_price_log"] = weight * base + (1.0 - weight) * artist
    out["basis_shrunk_weight"] = weight
    return out


def build_basis_features(policy: str) -> dict[str, pd.DataFrame]:
    train_raw = pd.read_csv(TRAIN, low_memory=False)
    edges = size_edges_from_train(train_raw)
    train = load_feature_frame(TRAIN, "train", edges)
    val = load_feature_frame(VAL, "validation", edges)
    test = load_feature_frame(TEST, "test", edges)
    ops = load_ops_frame(edges)
    out = {
        "train_oof": relaxed_basis(train.merge(crossfit_basis(train, policy), on="_track6_row_id", how="left"), policy),
        "validation": relaxed_basis(val.merge(basis_for_target(train, val, policy), on="_track6_row_id", how="left"), policy),
        "test": relaxed_basis(test.merge(basis_for_target(train, test, policy), on="_track6_row_id", how="left"), policy),
        "0604_ex50": relaxed_basis(ops.merge(basis_for_target(train, ops, policy), on="_track6_row_id", how="left"), policy),
    }
    return out


def build_eval_frames() -> dict[str, pd.DataFrame]:
    shrunk_pred, raw_prior, shrunk_prior, _ = hcoef1.train_shrunk_huber_refit()
    frames = hcoef1.build_validation_test_frames(shrunk_pred, raw_prior, shrunk_prior)
    frames["0604_ex50"] = hcoef1.build_0604_frame(shrunk_pred, raw_prior, shrunk_prior)
    for col in ["_ops_current_70_30", "_ops_ppv8_defensive", "_ops_svc_fallback", "_ops_baseline_huber", "_ops_svc_group_n_log"]:
        if col in frames["0604_ex50"].columns:
            frames["0604_ex50"] = frames["0604_ex50"].drop(columns=[col])
    return frames


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def evaluate(candidate: str, method: str, frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    return {
        "candidate": candidate,
        "method": method,
        "split": str(frame["split"].iloc[0]),
        "n": int(len(frame)),
        **metric_from_frame(frame, pred_log),
    }


def add_prediction(rows: list[pd.DataFrame], candidate: str, method: str, frame: pd.DataFrame, pred_log: np.ndarray) -> None:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    rows.append(
        pd.DataFrame(
            {
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "method": method,
                "split": frame["split"].to_numpy(),
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame["artist_key"].astype(str).to_numpy(),
                "actual_log": frame["actual_log"].to_numpy(dtype=float),
                "actual_price": actual,
                "pred_log": pred_log,
                "pred_price": pred_price,
                "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
                "ape": np.abs(pred_price - actual) / np.clip(actual, 1.0, None),
            }
        )
    )


def linear_pipeline(kind: str, alpha: float) -> Pipeline:
    model = HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=5000) if kind == "huber" else Ridge(alpha=alpha)
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


def fit_predict(train_frame: pd.DataFrame, eval_frame: pd.DataFrame, features: list[str], target: np.ndarray, kind: str, alpha: float) -> tuple[np.ndarray, Pipeline]:
    model = linear_pipeline(kind, alpha)
    model.fit(train_frame[features], target)
    return np.asarray(model.predict(eval_frame[features]), dtype=float), model


def coef_frame(model: Pipeline, candidate: str, features: list[str], kind: str, target: str) -> pd.DataFrame:
    reg = model.named_steps["model"]
    coef = getattr(reg, "coef_", np.full(len(features), np.nan))
    return pd.DataFrame(
        [
            {
                "candidate": candidate,
                "model_type": kind,
                "target": target,
                "feature": feature,
                "coefficient_on_scaled_feature": float(coef[idx]),
                "abs_coefficient": float(abs(coef[idx])),
                "intercept": float(getattr(reg, "intercept_", np.nan)),
            }
            for idx, feature in enumerate(features)
        ]
    ).sort_values(["candidate", "abs_coefficient"], ascending=[True, False])


def add_derived_basis(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = [
        "basis_relaxed_price_log",
        "basis_relaxed_unit_area_log",
        "basis_shrunk_price_log",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_artist_price_log",
        "basis_artist_size_price_log",
        "basis_artist_medium_support_size_price_log",
        "basis_artist_n_log",
        "basis_artist_size_n_log",
        "basis_artist_medium_support_size_n_log",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
    out["basis_relaxed_vs_current_gap"] = out["basis_relaxed_price_log"] - out[REFERENCE]
    out["basis_relaxed_vs_svc_gap"] = out["basis_relaxed_price_log"] - out["svc_fallback"]
    out["basis_shrunk_vs_current_gap"] = out["basis_shrunk_price_log"] - out[REFERENCE]
    return out


def merge_policy_frames(base_frames: dict[str, pd.DataFrame], policy_features: dict[str, pd.DataFrame], policy: str) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for split in ["validation", "test", "0604_ex50"]:
        basis_cols = [c for c in policy_features[split].columns if c.startswith("basis_") or c == "_track6_row_id"]
        frame = base_frames[split].merge(policy_features[split][basis_cols], on="_track6_row_id", how="left")
        frame["basis_policy"] = policy
        frames[split] = add_derived_basis(frame)
    return frames


def coverage_rows(policy_features: dict[str, pd.DataFrame], policy: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split in ["validation", "test", "0604_ex50"]:
        frame = policy_features[split]
        for level in ["artist_medium_support_size", "artist_size", "artist", "medium_support_size", "medium_category_support_size", "medium_size"]:
            covered = pd.to_numeric(frame[f"basis_{level}_covered"], errors="coerce").fillna(0.0).to_numpy() > 0
            n = pd.to_numeric(frame[f"basis_{level}_n"], errors="coerce").fillna(0.0)
            rows.append(
                {
                    "policy": policy,
                    "split": split,
                    "level": level,
                    "rows": int(len(frame)),
                    "covered_rows": int(covered.sum()),
                    "covered_share": float(covered.mean()),
                    "median_n_when_covered": float(n[covered].median()) if covered.any() else 0.0,
                }
            )
    return pd.DataFrame(rows)


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    ref = val[val["candidate"].eq(REFERENCE)].iloc[0]
    val["score"] = 0.40 * val["MdAPE"] / ref["MdAPE"] + 0.35 * val["MAPE"] / ref["MAPE"] + 0.25 * val["p95_APE"] / ref["p95_APE"]
    val["beats_ref_metric_count"] = (
        (val["MdAPE"] < ref["MdAPE"]).astype(int)
        + (val["MAPE"] < ref["MAPE"]).astype(int)
        + (val["p95_APE"] < ref["p95_APE"]).astype(int)
    )
    objectives = {
        "balanced_score": val.sort_values(["score", "MdAPE", "MAPE"]),
        "mdape_guarded": val[val["MAPE"].le(ref["MAPE"] * 1.03) & val["p95_APE"].le(ref["p95_APE"] * 1.05)].sort_values("MdAPE"),
        "mape_guarded": val[val["MdAPE"].le(ref["MdAPE"] * 1.05) & val["p95_APE"].le(ref["p95_APE"] * 1.05)].sort_values("MAPE"),
        "p95_guarded": val[val["MdAPE"].le(ref["MdAPE"] * 1.05) & val["MAPE"].le(ref["MAPE"] * 1.05)].sort_values("p95_APE"),
    }
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    ops = metrics[metrics["split"].eq("0604_ex50")].set_index("candidate")
    rows: list[dict[str, Any]] = []
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


def residual_analysis(predictions: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    names = set(selected["selected_candidate"].dropna().astype(str)) | {REFERENCE, CURRENT_IMPROVED}
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions[predictions["candidate"].isin(names)].groupby(["split", "candidate"], observed=False):
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

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    lines = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
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
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
    coverage: pd.DataFrame,
) -> None:
    val = metrics[metrics["split"].eq("validation")].copy()
    test = metrics[metrics["split"].eq("test")].copy()
    ref_test = test[test["candidate"].eq(REFERENCE)].iloc[0]
    improved_test = test[
        ((test["MdAPE"] < ref_test["MdAPE"]).astype(int) + (test["MAPE"] < ref_test["MAPE"]).astype(int) + (test["p95_APE"] < ref_test["p95_APE"]).astype(int))
        >= 2
    ].sort_values(["MdAPE", "MAPE", "p95_APE"])

    decision = "반복 검증 후보 없음"
    if not selected.empty:
        names = set(selected["selected_candidate"].astype(str))
        selected_test = test[test["candidate"].isin(names)].copy()
        if not selected_test.empty:
            selected_test["improved_metric_count"] = (
                (selected_test["MdAPE"] < ref_test["MdAPE"]).astype(int)
                + (selected_test["MAPE"] < ref_test["MAPE"]).astype(int)
                + (selected_test["p95_APE"] < ref_test["p95_APE"]).astype(int)
            )
            best = selected_test.sort_values(["improved_metric_count", "MdAPE"], ascending=[False, True]).iloc[0]
            if int(best["improved_metric_count"]) >= 2:
                decision = (
                    f"반복 검증 후보: `{best['candidate']}`. "
                    f"fixed test MdAPE/MAPE/p95 `{best['MdAPE']:.4f}/{best['MAPE']:.4f}/{best['p95_APE']:.4f}`."
                )
            else:
                decision = "validation 선택 후보가 fixed test에서 기준 후보를 충분히 넘지 못해 보류."

    md = "\n".join(
        [
            f"# {EXP_ID} Warm 기준가 생성 방식 고도화 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 유사 작품 기준가를 작가/크기/재료 조합과 표본 수 신뢰도로 완화해 Huber 계수 조정에 넣었을 때 현재 Warm 후보를 넘는지 확인.",
            "- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.",
            "- 현재 개선 후보 대조: `hcoef2_size_reliability_cap005_s050`.",
            "- 선택 원칙: validation에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}",
            f"- 기준 fixed test: MdAPE `{ref_test['MdAPE']:.4f}`, MAPE `{ref_test['MAPE']:.4f}`, p95 `{ref_test['p95_APE']:.4f}`, RMSE_log `{ref_test['RMSE_log']:.4f}`.",
            "- fixed test만 좋은 후보는 채택하지 않고 HCOEF5 반복 검증 후보로만 분리.",
            "",
            "## 2. Validation 상위 후보",
            "",
            markdown_table(val.sort_values(["MdAPE", "MAPE", "p95_APE"])[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4), max_rows=16),
            "",
            "## 3. Validation 선택 후보의 test/0604 확인",
            "",
            markdown_table(selected.round(4)),
            "",
            "## 4. Fixed test 상위 후보",
            "",
            markdown_table(test.sort_values(["MdAPE", "MAPE", "p95_APE"])[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4), max_rows=16),
            "",
            "## 5. 기준 대비 2개 이상 지표 개선 후보",
            "",
            markdown_table(improved_test[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4), max_rows=24),
            "",
            "## 6. 주요 계수",
            "",
            "- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.",
            markdown_table(coefficients.head(60).round(5)),
            "",
            "## 7. 기준가 coverage",
            "",
            markdown_table(coverage.round(4), max_rows=36),
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
            "- `outputs/coverage_summary.csv`",
            "- `outputs/selected_validation_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef4_warm_basis_generation_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef4_warm_basis_generation_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    base_frames = build_eval_frames()
    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    coverage_frames: list[pd.DataFrame] = []

    # Existing references.
    for split, frame in base_frames.items():
        pred = frame[REFERENCE].to_numpy(dtype=float)
        metrics_rows.append(evaluate(REFERENCE, "reference", frame, pred))
        add_prediction(pred_rows, REFERENCE, "reference", frame, pred)

    improved_cfg = {
        "feature_key": "resid_basis_size_reliability",
        "alpha": 0.01,
        "cap": 0.05,
        "strength": 0.50,
    }
    validation = base_frames["validation"]
    residual_target = validation["actual_log"].to_numpy(dtype=float) - validation[REFERENCE].to_numpy(dtype=float)
    features = hcoef1.RESIDUAL_FEATURE_SETS[improved_cfg["feature_key"]]
    hcoef2_model = hcoef1.linear_pipeline("huber", float(improved_cfg["alpha"]))
    hcoef2_model.fit(validation[features], residual_target)
    for split, frame in base_frames.items():
        raw = np.asarray(hcoef2_model.predict(frame[features]), dtype=float)
        pred = frame[REFERENCE].to_numpy(dtype=float) + np.clip(raw, -improved_cfg["cap"], improved_cfg["cap"]) * improved_cfg["strength"]
        metrics_rows.append(evaluate(CURRENT_IMPROVED, "current_residual_huber_correction", frame, pred))
        add_prediction(pred_rows, CURRENT_IMPROVED, "current_residual_huber_correction", frame, pred)

    for policy in POLICIES:
        policy_features = build_basis_features(policy)
        coverage_frames.append(coverage_rows(policy_features, policy))
        frames = merge_policy_frames(base_frames, policy_features, policy)

        # Direct basis components and fixed blends.
        direct_cols = {
            f"{policy}_relaxed_price_basis": "basis_relaxed_price_log",
            f"{policy}_relaxed_unit_area_basis": "basis_relaxed_unit_area_log",
            f"{policy}_shrunk_price_basis": "basis_shrunk_price_log",
        }
        for candidate, col in direct_cols.items():
            for split, frame in frames.items():
                pred = frame[col].to_numpy(dtype=float)
                metrics_rows.append(evaluate(candidate, "basis_component", frame, pred))
                add_prediction(pred_rows, candidate, "basis_component", frame, pred)

        for w in [0.20, 0.35, 0.50, 0.65, 0.80]:
            candidate = f"{policy}_dynamic_svc_basis_wbasis_{w:.2f}"
            for split, frame in frames.items():
                n = pd.to_numeric(frame["basis_relaxed_n"], errors="coerce").fillna(0.0)
                reliability = np.clip(n / (n + 8.0), 0.0, 1.0)
                eff_w = w * reliability
                pred = eff_w * frame["basis_relaxed_price_log"].to_numpy(dtype=float) + (1.0 - eff_w) * frame[REFERENCE].to_numpy(dtype=float)
                metrics_rows.append(evaluate(candidate, "reliability_weighted_basis_blend", frame, pred))
                add_prediction(pred_rows, candidate, "reliability_weighted_basis_blend", frame, pred)

        for feature_key, feature_list in BASIS_FEATURE_SETS.items():
            for kind, alphas in [("huber", [0.001, 0.01, 0.1]), ("ridge", [0.1, 1.0, 10.0])]:
                for alpha in alphas:
                    candidate = f"{policy}_{kind}_{feature_key}_alpha{alpha:g}"
                    val_frame = frames["validation"]
                    target = val_frame["actual_log"].to_numpy(dtype=float)
                    val_pred = crossfit_predict(val_frame, feature_list, target, kind, alpha)
                    test_pred, model = fit_predict(val_frame, frames["test"], feature_list, target, kind, alpha)
                    ops_pred, _ = fit_predict(val_frame, frames["0604_ex50"], feature_list, target, kind, alpha)
                    for split, frame, pred in [
                        ("validation", val_frame, val_pred),
                        ("test", frames["test"], test_pred),
                        ("0604_ex50", frames["0604_ex50"], ops_pred),
                    ]:
                        metrics_rows.append(evaluate(candidate, f"{kind}_basis_meta_validation", frame, pred))
                        add_prediction(pred_rows, candidate, f"{kind}_basis_meta_validation", frame, pred)
                    coef_rows.append(coef_frame(model, candidate, feature_list, kind, "actual_log"))

    metrics = pd.DataFrame(metrics_rows)
    predictions = pd.concat(pred_rows, ignore_index=True)
    coefficients = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    selected = select_validation_candidates(metrics)
    residuals = residual_analysis(predictions, selected)
    coverage = pd.concat(coverage_frames, ignore_index=True)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coefficients.to_csv(out / "feature_coefficients.csv", index=False)
    selected.to_csv(out / "selected_validation_candidates.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    coverage.to_csv(out / "coverage_summary.csv", index=False)
    # This is a candidate-search experiment. Repeated split validation is done
    # in the follow-up, so leave an explicit placeholder for artifact parity.
    pd.DataFrame(
        [
            {
                "note": "PP-HCOEF4 is validation-selected candidate search. Repeat OOF validation is required in PP-HCOEF5 for any promoted candidate.",
            }
        ]
    ).to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "current_improved_candidate": CURRENT_IMPROVED,
        "basis_policies": POLICIES,
        "basis_feature_sets": BASIS_FEATURE_SETS,
        "selection_policy": "validation-only ranking; fixed test and 0604 confirmation",
        "folds": N_FOLDS,
        "seed": SEED,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics, selected, coefficients, residuals, coverage)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected validation candidates ---")
    print(selected.round(4).to_string(index=False))
    print("--- fixed test top 12 ---")
    print(
        metrics[metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(12)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
