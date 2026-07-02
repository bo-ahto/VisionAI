#!/usr/bin/env python3
"""PP-COLD-QF1: Warm-lite style follow-up candidates for Cold.

This experiment checks whether the ideas that helped the new Warm-lite path
transfer to Cold:

1. full/lean LightGBM Quantile predictions,
2. clipped residual correction trained from OOF residuals,
3. disagreement/qwidth based tail guard,
4. conditional correction of the current Cold v0.3 research chain.

The fixed test set is only used for final reporting. Thresholds and candidate
ranking are based on validation.
"""
from __future__ import annotations

import html
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402

_cgrp_spec = importlib.util.spec_from_file_location(
    "cgrp", SCRIPT_DIR / "run_pp_cgrp1_cold_group_price_stats_base.py"
)
cgrp = importlib.util.module_from_spec(_cgrp_spec)
assert _cgrp_spec.loader is not None
_cgrp_spec.loader.exec_module(cgrp)


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-COLD-QF1"
EXP_SLUG = "PP-COLD-QF1_warm_lite_style_cold_followup"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
BASE_ROWS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CBASE1_cold_base_lock"
    / "outputs"
    / "fixed_cold_base_rows.csv"
)

SEED = 20260616
SEEDS = [20260616, 20260617, 20260618]
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}
N_ESTIMATORS = 650

CATEGORICAL = {
    "medium_category",
    "support_category",
    "size_bucket",
    "support_size_bucket",
    "medium_support_bucket",
    "shape_bucket",
    "medium_shape_bucket",
}
NUMERIC = {
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "grp_log_price_median",
    "grp_log_price_q25",
    "grp_log_price_q75",
    "grp_log_price_iqr",
    "grp_unit_area_median",
    "grp_unit_area_iqr",
    "grp_n_log",
    "grp_match_level",
    "grp_price_proxy",
    "full_q50",
    "lean_q50",
    "full_lean_avg",
    "full_qwidth",
    "full_lean_gap_abs",
    "full_lean_gap_signed",
}


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_row(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(ape)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred) ** 2))),
        "within_30": float(np.mean(ape <= 0.30)),
        "over_50pct_error_rate": float(np.mean(ape > 0.50)),
    }


def md_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda v: "" if pd.isna(v) else f"{float(v):.6f}")
        else:
            data[col] = data[col].map(lambda v: "" if pd.isna(v) else str(v))
    header = [str(c) for c in data.columns]
    rows = [list(map(str, row)) for row in data.itertuples(index=False)]
    return "\n".join(
        ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
        + ["| " + " | ".join(row) + " |" for row in rows]
    )


def write_simple_html(markdown: str, path: Path) -> None:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for raw in markdown.splitlines():
        if raw.startswith("| "):
            table.append(raw)
            continue
        flush_table()
        line = html.escape(raw)
        if raw.startswith("# "):
            body.append(f"<h1>{html.escape(raw[2:])}</h1>")
        elif raw.startswith("## "):
            body.append(f"<h2>{html.escape(raw[3:])}</h2>")
        elif raw.startswith("### "):
            body.append(f"<h3>{html.escape(raw[4:])}</h3>")
        elif raw.startswith("- "):
            body.append(f"<p>{line}</p>")
        elif raw.strip() == "":
            body.append("")
        else:
            body.append(f"<p>{line}</p>")
    flush_table()
    path.write_text(
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<title>PP-COLD-QF1 Warm-lite style Cold follow-up</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "max-width:1180px;margin:36px auto;line-height:1.6;color:#111827}"
        "table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px}"
        "th,td{border:1px solid #d1d5db;padding:6px 8px;text-align:left}"
        "th{background:#f3f4f6}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}"
        "</style></head><body>"
        + "\n".join(body)
        + "</body></html>",
        encoding="utf-8",
    )


def split_feature_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [f for f in features if f in NUMERIC]
    categorical = [f for f in features if f not in numeric]
    return numeric, categorical


def quantile_pipeline(features: list[str], alpha: float, seed: int) -> Pipeline:
    numeric, categorical = split_feature_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline(
        [
            ("prep", ColumnTransformer(transformers)),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=N_ESTIMATORS,
                    learning_rate=0.035,
                    num_leaves=31,
                    min_child_samples=35,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    reg_lambda=1.2,
                    random_state=seed,
                    verbosity=-1,
                ),
            ),
        ]
    )


def huber_residual_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_feature_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        try:
            enc = OneHotEncoder(handle_unknown="ignore", min_frequency=15, sparse_output=True)
        except TypeError:
            enc = OneHotEncoder(handle_unknown="ignore", min_frequency=15)
        transformers.append(("cat", enc, categorical))
    return Pipeline(
        [
            ("prep", ColumnTransformer(transformers)),
            ("model", HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=4000)),
        ]
    )


def add_group_price_proxy(*frames: pd.DataFrame) -> list[pd.DataFrame]:
    out_frames = []
    for frame in frames:
        out = frame.copy()
        out["grp_price_proxy"] = out["grp_unit_area_median"].astype(float) + out["log_area"].astype(float).clip(lower=0)
        out_frames.append(out)
    return out_frames


def fit_quantile_mean(
    train: pd.DataFrame,
    evals: dict[str, pd.DataFrame],
    features: list[str],
    quantiles: dict[str, float],
    seeds: list[int],
) -> dict[str, dict[str, np.ndarray]]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    accum: dict[str, dict[str, np.ndarray]] = {
        name: {q: np.zeros(len(frame), dtype=float) for q in quantiles} for name, frame in evals.items()
    }
    for seed in seeds:
        for qname, alpha in quantiles.items():
            model = quantile_pipeline(features, alpha, seed).fit(train[features], y)
            for name, frame in evals.items():
                accum[name][qname] += np.asarray(model.predict(frame[features]), dtype=float) / len(seeds)
    return accum


def fit_q50(
    train: pd.DataFrame,
    evals: dict[str, pd.DataFrame],
    features: list[str],
    seed: int,
) -> dict[str, np.ndarray]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    model = quantile_pipeline(features, 0.50, seed).fit(train[features], y)
    return {name: np.asarray(model.predict(frame[features]), dtype=float) for name, frame in evals.items()}


def build_oof_avg(train: pd.DataFrame, full_features: list[str], lean_features: list[str]) -> pd.DataFrame:
    train = train.reset_index(drop=True)
    oof_full = np.zeros(len(train), dtype=float)
    oof_lean = np.zeros(len(train), dtype=float)
    for fold, (tr_idx, va_idx) in enumerate(KFold(n_splits=5, shuffle=True, random_state=SEED).split(train), start=1):
        tr = train.iloc[tr_idx].reset_index(drop=True)
        va = train.iloc[va_idx].reset_index(drop=True)
        pred = fit_q50(tr, {"va": va}, full_features, SEED + fold)
        oof_full[va_idx] = pred["va"]
        pred = fit_q50(tr, {"va": va}, lean_features, SEED + 100 + fold)
        oof_lean[va_idx] = pred["va"]
    out = train.copy()
    out["full_q50"] = oof_full
    out["lean_q50"] = oof_lean
    out["full_lean_avg"] = 0.5 * oof_full + 0.5 * oof_lean
    # OOF residual training only has q50 models. Use full/lean disagreement as
    # the training-time uncertainty proxy instead of an all-NaN qwidth column.
    out["full_qwidth"] = np.abs(oof_full - oof_lean)
    out["full_lean_gap_abs"] = np.abs(oof_full - oof_lean)
    out["full_lean_gap_signed"] = oof_full - oof_lean
    out["residual_oof"] = out["ln_price_krw"].to_numpy(dtype=float) - out["full_lean_avg"].to_numpy(dtype=float)
    return out


def add_prediction_features(frame: pd.DataFrame, preds: dict[str, np.ndarray]) -> pd.DataFrame:
    out = frame.copy()
    out["full_q50"] = preds["full_q50"]
    out["lean_q50"] = preds["lean_q50"]
    out["full_lean_avg"] = 0.5 * preds["full_q50"] + 0.5 * preds["lean_q50"]
    out["full_qwidth"] = preds["full_q90"] - preds["full_q10"]
    out["full_lean_gap_abs"] = np.abs(preds["full_q50"] - preds["lean_q50"])
    out["full_lean_gap_signed"] = preds["full_q50"] - preds["lean_q50"]
    return out


def evaluate_candidates(
    candidates: dict[str, dict[str, np.ndarray]],
    eval_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for split, frame in eval_frames.items():
        actual_price = frame["price_krw"].to_numpy(dtype=float)
        actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
        for cand, pred_by_split in candidates.items():
            if split not in pred_by_split:
                continue
            rows.append({"candidate": cand, "split": split, **metric_row(actual_price, actual_log, pred_by_split[split])})
    return pd.DataFrame(rows)


def make_current_base_candidates(base_rows: pd.DataFrame) -> dict[str, dict[str, np.ndarray]]:
    out: dict[str, dict[str, np.ndarray]] = {}
    columns = {
        "current_v03_research_guard_search": "research_base_pred_log",
        "current_v03_guard_only": "guard_pred_log",
        "current_y18_qwidth_base": "y18_qwidth_pred_log",
        "current_v02_defense": "v02_defense_pred_log",
    }
    for name, col in columns.items():
        out[name] = {}
        for split, part in base_rows.groupby("split"):
            out[name][split] = part[col].to_numpy(dtype=float)
    return out


def make_residual_candidates(
    val_pred_features: pd.DataFrame,
    test_pred_features: pd.DataFrame,
    residual_model: Pipeline,
    residual_features: list[str],
) -> dict[str, dict[str, np.ndarray]]:
    val_resid = residual_model.predict(val_pred_features[residual_features])
    test_resid = residual_model.predict(test_pred_features[residual_features])
    out: dict[str, dict[str, np.ndarray]] = {}
    for strength in [0.25, 0.50, 0.75, 1.00]:
        for cap in [0.025, 0.050, 0.075, 0.100, 0.150]:
            name = f"qf1_avg_plus_huber_residual_s{strength:g}_cap{cap:g}"
            out[name] = {
                "validation": val_pred_features["full_lean_avg"].to_numpy(dtype=float)
                + np.clip(strength * val_resid, -cap, cap),
                "test": test_pred_features["full_lean_avg"].to_numpy(dtype=float)
                + np.clip(strength * test_resid, -cap, cap),
            }
    return out


def make_qf1_guard_candidates(val: pd.DataFrame, test: pd.DataFrame) -> dict[str, dict[str, np.ndarray]]:
    q = {
        "width_q50": float(val["full_qwidth"].quantile(0.50)),
        "width_q67": float(val["full_qwidth"].quantile(0.67)),
        "width_q80": float(val["full_qwidth"].quantile(0.80)),
        "gap_q50": float(val["full_lean_gap_abs"].quantile(0.50)),
        "gap_q67": float(val["full_lean_gap_abs"].quantile(0.67)),
        "gap_q80": float(val["full_lean_gap_abs"].quantile(0.80)),
    }
    out: dict[str, dict[str, np.ndarray]] = {}
    for width_name in ["width_q50", "width_q67", "width_q80"]:
        for gap_name in ["gap_q50", "gap_q67", "gap_q80"]:
            for weight in [0.25, 0.50, 0.75]:
                name = f"qf1_avg_full_lean_lower_guard_{width_name}_{gap_name}_w{weight:g}"
                out[name] = {}
                for split, frame in [("validation", val), ("test", test)]:
                    avg = frame["full_lean_avg"].to_numpy(dtype=float)
                    lower = np.minimum(frame["full_q50"].to_numpy(dtype=float), frame["lean_q50"].to_numpy(dtype=float))
                    mask = (
                        (frame["full_qwidth"].to_numpy(dtype=float) >= q[width_name])
                        & (frame["full_lean_gap_abs"].to_numpy(dtype=float) >= q[gap_name])
                        & (lower < avg)
                    )
                    pred = avg.copy()
                    pred[mask] = (1.0 - weight) * avg[mask] + weight * lower[mask]
                    out[name][split] = pred
    return out


def make_v03_hybrid_candidates(
    val: pd.DataFrame,
    test: pd.DataFrame,
    base_rows: pd.DataFrame,
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, float]]:
    base_val = base_rows[base_rows["split"].eq("validation")].reset_index(drop=True)
    base_test = base_rows[base_rows["split"].eq("test")].reset_index(drop=True)
    if not np.array_equal(base_val["_track6_row_id"].to_numpy(), val["_track6_row_id"].to_numpy()):
        raise ValueError("validation row order mismatch")
    if not np.array_equal(base_test["_track6_row_id"].to_numpy(), test["_track6_row_id"].to_numpy()):
        raise ValueError("test row order mismatch")

    ref_q = {
        "qwidth_q50": float(base_val["quantile_width_log"].quantile(0.50)),
        "qwidth_q67": float(base_val["quantile_width_log"].quantile(0.67)),
        "qwidth_q80": float(base_val["quantile_width_log"].quantile(0.80)),
        "gap_to_qf1_q50": float(np.quantile(np.clip(base_val["research_base_pred_log"].to_numpy() - val["full_lean_avg"].to_numpy(), 0, None), 0.50)),
        "gap_to_qf1_q67": float(np.quantile(np.clip(base_val["research_base_pred_log"].to_numpy() - val["full_lean_avg"].to_numpy(), 0, None), 0.67)),
        "gap_to_qf1_q80": float(np.quantile(np.clip(base_val["research_base_pred_log"].to_numpy() - val["full_lean_avg"].to_numpy(), 0, None), 0.80)),
    }

    out: dict[str, dict[str, np.ndarray]] = {}
    for width_name in ["qwidth_q50", "qwidth_q67", "qwidth_q80"]:
        for gap_name in ["gap_to_qf1_q50", "gap_to_qf1_q67", "gap_to_qf1_q80"]:
            for weight in [0.20, 0.35, 0.50]:
                for cap in [0.025, 0.050, 0.075, 0.100]:
                    name = f"v03_down_to_qf1_if_risky_{width_name}_{gap_name}_w{weight:g}_cap{cap:g}"
                    out[name] = {}
                    for split, frame, brow in [
                        ("validation", val, base_val),
                        ("test", test, base_test),
                    ]:
                        base = brow["research_base_pred_log"].to_numpy(dtype=float)
                        target = frame["full_lean_avg"].to_numpy(dtype=float)
                        qwidth = brow["quantile_width_log"].to_numpy(dtype=float)
                        gap_down = base - target
                        mask = (
                            (qwidth >= ref_q[width_name])
                            & (gap_down >= ref_q[gap_name])
                            & (target < base)
                        )
                        move = np.clip(weight * (target - base), -cap, 0.0)
                        pred = base.copy()
                        pred[mask] = base[mask] + move[mask]
                        out[name][split] = pred
    return out, ref_q


def select_by_validation(metrics: pd.DataFrame, baseline: str, family_filter: str) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    base = val[val["candidate"].eq(baseline)].iloc[0]
    val = val[val["candidate"].str.startswith(family_filter)].copy()
    for k in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        val[f"delta_{k}"] = val[k] - float(base[k])
    val["score"] = val["delta_MAPE"] + 0.35 * val["delta_p95_APE"] + 0.20 * np.maximum(val["delta_MdAPE"], 0)
    return val.sort_values(["score", "delta_MdAPE"]).reset_index(drop=True)


def main() -> None:
    ensure_dirs()

    base_features = artifact_features()["cold_lightgbm"]
    extra = ["medium_support_bucket"]
    train, val, test = load_scope("cold", list(dict.fromkeys(base_features + extra)))
    need = list(
        dict.fromkeys(
            base_features
            + extra
            + [
                "ln_price_krw",
                "price_krw",
                "log_area",
                "artist_key",
                "_track6_row_id",
                "medium_category",
                "support_category",
                "size_bucket",
            ]
        )
    )
    train = train[need].reset_index(drop=True)
    val = val[need].reset_index(drop=True)
    test = test[need].reset_index(drop=True)

    train_s = cgrp.train_with_internal_stats(train)
    val_s = cgrp.assign_group_stats(train, val)
    test_s = cgrp.assign_group_stats(train, test)
    train_s, val_s, test_s = add_group_price_proxy(train_s, val_s, test_s)

    full_features = list(dict.fromkeys(base_features + extra + cgrp.GRP_FULL + ["grp_price_proxy"]))
    lean_features = list(
        dict.fromkeys(
            [
                "log_area",
                "aspect_ratio",
                "has_depth",
                "is_3d_candidate",
                "medium_category",
                "support_category",
                "size_bucket",
            ]
            + cgrp.GRP_LEAN
            + ["grp_price_proxy"]
        )
    )

    full_preds = fit_quantile_mean(
        train_s,
        {"validation": val_s, "test": test_s},
        full_features,
        QUANTILES,
        SEEDS,
    )
    lean_q50 = fit_quantile_mean(
        train_s,
        {"validation": val_s, "test": test_s},
        lean_features,
        {"q50": 0.50},
        SEEDS,
    )

    val_pf = add_prediction_features(
        val_s,
        {
            "full_q10": full_preds["validation"]["q10"],
            "full_q50": full_preds["validation"]["q50"],
            "full_q90": full_preds["validation"]["q90"],
            "lean_q50": lean_q50["validation"]["q50"],
        },
    )
    test_pf = add_prediction_features(
        test_s,
        {
            "full_q10": full_preds["test"]["q10"],
            "full_q50": full_preds["test"]["q50"],
            "full_q90": full_preds["test"]["q90"],
            "lean_q50": lean_q50["test"]["q50"],
        },
    )

    candidates: dict[str, dict[str, np.ndarray]] = {
        "qf1_full_q50": {
            "validation": val_pf["full_q50"].to_numpy(dtype=float),
            "test": test_pf["full_q50"].to_numpy(dtype=float),
        },
        "qf1_lean_q50": {
            "validation": val_pf["lean_q50"].to_numpy(dtype=float),
            "test": test_pf["lean_q50"].to_numpy(dtype=float),
        },
        "qf1_full_lean_avg": {
            "validation": val_pf["full_lean_avg"].to_numpy(dtype=float),
            "test": test_pf["full_lean_avg"].to_numpy(dtype=float),
        },
    }
    candidates.update(make_qf1_guard_candidates(val_pf, test_pf))

    train_oof = build_oof_avg(train_s, full_features, lean_features)
    residual_features = list(
        dict.fromkeys(
            full_features
            + [
                "full_q50",
                "lean_q50",
                "full_lean_avg",
                "full_qwidth",
                "full_lean_gap_abs",
                "full_lean_gap_signed",
            ]
        )
    )
    residual_model = huber_residual_model(residual_features).fit(
        train_oof[residual_features],
        train_oof["residual_oof"].to_numpy(dtype=float),
    )
    candidates.update(make_residual_candidates(val_pf, test_pf, residual_model, residual_features))

    base_rows = pd.read_csv(BASE_ROWS)
    base_rows = base_rows.sort_values(["split", "_track6_row_id"]).reset_index(drop=True)
    val_pf = val_pf.sort_values("_track6_row_id").reset_index(drop=True)
    test_pf = test_pf.sort_values("_track6_row_id").reset_index(drop=True)
    current = make_current_base_candidates(base_rows)
    candidates.update(current)
    hybrid, hybrid_thresholds = make_v03_hybrid_candidates(val_pf, test_pf, base_rows)
    candidates.update(hybrid)

    eval_frames = {"validation": val_pf, "test": test_pf}
    metrics = evaluate_candidates(candidates, eval_frames)
    metrics.to_csv(EXP_DIR / "outputs" / "candidate_metrics.csv", index=False)

    qf1_rank = select_by_validation(metrics, "qf1_full_lean_avg", "qf1_")
    hybrid_rank = select_by_validation(metrics, "current_v03_research_guard_search", "v03_down_to_qf1")
    qf1_rank.to_csv(EXP_DIR / "outputs" / "qf1_validation_rank.csv", index=False)
    hybrid_rank.to_csv(EXP_DIR / "outputs" / "v03_hybrid_validation_rank.csv", index=False)

    top_names = (
        [
            "current_v03_research_guard_search",
            "current_v03_guard_only",
            "current_y18_qwidth_base",
            "current_v02_defense",
            "qf1_full_q50",
            "qf1_lean_q50",
            "qf1_full_lean_avg",
        ]
        + qf1_rank["candidate"].head(5).astype(str).tolist()
        + hybrid_rank["candidate"].head(8).astype(str).tolist()
    )
    top_names = list(dict.fromkeys(top_names))
    top_metrics = metrics[metrics["candidate"].isin(top_names)].copy()
    top_metrics["candidate"] = pd.Categorical(top_metrics["candidate"], categories=top_names, ordered=True)
    top_metrics = top_metrics.sort_values(["candidate", "split"]).reset_index(drop=True)
    top_metrics.to_csv(EXP_DIR / "outputs" / "selected_candidate_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "purpose": "Warm-lite style full/lean Quantile, clipped residual, and disagreement guard tests for Cold",
        "full_features": full_features,
        "lean_features": lean_features,
        "seeds": SEEDS,
        "quantiles": QUANTILES,
        "residual": {
            "target": "OOF actual_log - full_lean_avg",
            "model": "HuberRegressor",
            "features": residual_features,
        },
        "v03_hybrid_thresholds": hybrid_thresholds,
        "selection": "validation ranking only; fixed test reported for selected candidates",
        "prohibitions": ["0604 사용 금지", "test로 후보 선택 금지"],
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def split_table(names: list[str]) -> pd.DataFrame:
        show = metrics[metrics["candidate"].isin(names)].copy()
        return show[["candidate", "split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate"]]

    qf1_show = qf1_rank.head(12)[
        ["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "score"]
    ]
    hybrid_show = hybrid_rank.head(12)[
        ["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "score"]
    ]
    selected_test = top_metrics[top_metrics["split"].eq("test")][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate"]
    ].copy()

    base_test = metrics[
        metrics["split"].eq("test") & metrics["candidate"].eq("current_v03_research_guard_search")
    ].iloc[0]
    selected_test["delta_MAPE_vs_v03"] = selected_test["MAPE"] - float(base_test["MAPE"])
    selected_test["delta_p95_vs_v03"] = selected_test["p95_APE"] - float(base_test["p95_APE"])
    selected_test["delta_MdAPE_vs_v03"] = selected_test["MdAPE"] - float(base_test["MdAPE"])

    report = "\n".join(
        [
            "# PP-COLD-QF1 Warm-lite style Cold follow-up",
            "",
            "## 목적",
            "- 새 Warm-lite에서 효과가 있었던 `full/lean Quantile`, `clip 잔차 보정`, `불일치 기반 tail guard`를 Cold에 맞게 검증했다.",
            "- Cold는 같은 작가 가격 이력이 없으므로 작가 이력 대신 작품 피처와 작가 미사용 비교군 그룹 통계를 사용했다.",
            "- 기준선은 두 개다: raw-input 후보끼리는 `qf1_full_lean_avg`, 최종 Cold 교체/추가 후보는 `current_v03_research_guard_search`다.",
            "- threshold와 후보 순위는 validation에서만 정하고 fixed test는 확인용으로만 보고했다.",
            "",
            "## 실험 설계",
            "- full Quantile: 기존 Cold LightGBM 12피처 + medium_support_bucket + 작가 미사용 그룹 통계 full + grp_price_proxy.",
            "- lean Quantile: log_area/aspect/depth/medium/support/size + 그룹 통계 lean + grp_price_proxy.",
            "- residual: train 5-fold OOF `actual_log - full_lean_avg`를 HuberRegressor로 학습하고, 적용 시 clip cap을 둔다.",
            "- qf1 guard: full/lean 예측 차이와 full Quantile qwidth가 큰 행에서 lower(q50_full, q50_lean) 방향으로 이동한다.",
            "- v0.3 hybrid: 현행 v0.3 예측이 qf1 평균보다 높고 qwidth/gap이 큰 행만 qf1 쪽으로 작게 내린다.",
            "",
            "## 주요 기준선과 선택 후보 test 결과",
            md_table(selected_test),
            "",
            "## qf1 내부 validation 상위 후보",
            md_table(qf1_show),
            "",
            "## v0.3 hybrid validation 상위 후보",
            md_table(hybrid_show),
            "",
            "## 판단 기준",
            "- `qf1_*`가 v0.3보다 좋으면 Cold 자체를 Warm-lite 스타일로 단순화할 가능성이 있다.",
            "- `qf1_*`는 v0.3보다 약하지만 `v03_down_to_qf1_*`가 test MAPE/p95를 낮추면 방어층 추가 가능성이 있다.",
            "- v0.3 기준 test에서 MdAPE/MAPE/p95가 모두 악화되면 현행 Cold 체인을 유지해야 한다.",
            "",
            "## 산출물",
            f"- 실험 폴더: `{EXP_DIR.relative_to(REPO)}`",
            "- `outputs/candidate_metrics.csv`: 전체 후보 validation/test 지표.",
            "- `outputs/qf1_validation_rank.csv`: qf1 내부 후보 validation 순위.",
            "- `outputs/v03_hybrid_validation_rank.csv`: v0.3 조건부 보정 후보 validation 순위.",
            "- `outputs/selected_candidate_metrics.csv`: 기준선과 상위 후보 비교표.",
            "- `artifacts/run_config.json`: 피처, threshold, residual 학습 설정.",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    write_simple_html(report, EXP_DIR / "reports" / "result_report.html")
    (DOC_ROOT / "pp_cold_qf1_warm_lite_style_cold_followup_summary.md").write_text(report, encoding="utf-8")

    print(selected_test.round(6).to_string(index=False))
    print()
    print("[PP-COLD-QF1] wrote", EXP_DIR)


if __name__ == "__main__":
    main()
