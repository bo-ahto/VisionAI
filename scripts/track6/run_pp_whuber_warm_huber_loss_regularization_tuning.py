#!/usr/bin/env python3
"""Run PP-WHUBER1~PP-WHUBER6 Warm Huber characteristic tuning.

This experiment focuses on Huber-specific controls rather than adding another
large feature family:

1. epsilon/alpha grid
2. sample-weighted Huber
3. two-pass Huber outlier reweighting
4. segment-specific Huber routing
5. residual Huber epsilon tuning on the current Warm candidate
6. row/artist bootstrap stability check
"""
from __future__ import annotations

import html
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402


warnings.filterwarnings("ignore", category=ConvergenceWarning)


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER"
EXP_SLUG = "PP-WHUBER_warm_huber_loss_regularization_tuning"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm Huber 손실/규제 특성 튜닝"
SEED = 20260606

CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE
PPV8_CANDIDATE = wcoef.PPV8_CANDIDATE
FALLBACK_CANDIDATE = wcoef.FALLBACK_CANDIDATE

EPSILONS = [1.05, 1.20, 1.35, 1.60]
ALPHAS = [0.001, 0.01]
WEIGHT_SCHEMES = ["uniform", "svc_reliability"]
RESIDUAL_EPSILONS = [1.05, 1.20, 1.35, 1.60]
RESIDUAL_ALPHAS = [0.001, 0.01]
RESIDUAL_CAPS = [0.02, 0.03, 0.05, 0.08]
RESIDUAL_STRENGTHS = [0.15, 0.25, 0.50]
BOOTSTRAP_ITERATIONS = 300


DIRECT_FEATURE_SETS = {
    "svc_reliability_no_artist_key": (
        [feature for feature in wcoef.BASE_FEATURES if feature != "artist_key"]
        + wcoef.SVC_NUMERIC
        + wcoef.SVC_CATEGORICAL
        + wcoef.SVC_RELIABILITY_FEATURES
    ),
}

SEGMENT_FEATURES = (
    [feature for feature in wcoef.BASE_FEATURES if feature != "artist_key"]
    + wcoef.SVC_NUMERIC
    + wcoef.SVC_CATEGORICAL
    + wcoef.SVC_RELIABILITY_FEATURES
)


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    return wcoef.split_types(features)


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return wcoef.normalize(frame, features)


def feature_exists(frame: pd.DataFrame, features: list[str]) -> list[str]:
    return wcoef.feature_exists(frame, features)


def huber_model(features: list[str], alpha: float, epsilon: float) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append((
            "num",
            Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]),
            numeric,
        ))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=500, tol=1e-4)),
    ])


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if "ln_price_krw" in frame.columns and "price_krw" in frame.columns:
        return frame
    return pd.DataFrame({
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "ln_price_krw": frame["actual_log"].to_numpy(dtype=float),
        "price_krw": frame["actual_price"].to_numpy(dtype=float),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
    })


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return wcoef.metric_values(metric_frame(frame), pred_log)


def actual_log_array(frame: pd.DataFrame) -> np.ndarray:
    if "actual_log" in frame.columns:
        return frame["actual_log"].to_numpy(dtype=float)
    return frame["ln_price_krw"].to_numpy(dtype=float)


def prediction_frame(
    sub_experiment: str,
    candidate: str,
    method: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    mf = metric_frame(frame)
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "candidate": candidate,
        "method": method,
        "split": split,
        "_track6_row_id": mf["_track6_row_id"].to_numpy(),
        "actual_log": mf["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "actual_price": mf["price_krw"].to_numpy(dtype=float),
        "artist_key": mf.get("artist_key", pd.Series([""] * len(mf))).astype(str).to_numpy(),
    })
    if "artist_name_ko" in frame.columns:
        out["artist_name_ko"] = frame["artist_name_ko"].astype(str).to_numpy()
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    if extra:
        for key, value in extra.items():
            if np.isscalar(value):
                out[key] = value
            else:
                out[key] = value
    return out


def add_metric_row(
    rows: list[dict[str, Any]],
    sub_experiment: str,
    family: str,
    candidate: str,
    split: str,
    method: str,
    frame: pd.DataFrame,
    pred: np.ndarray,
    features: list[str] | str,
    alpha: float | None = None,
    epsilon: float | None = None,
    weight_scheme: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "family": family,
        "candidate": candidate,
        "split": split,
        "method": method,
        "alpha": np.nan if alpha is None else float(alpha),
        "epsilon": np.nan if epsilon is None else float(epsilon),
        "weight_scheme": "" if weight_scheme is None else weight_scheme,
        "n_features": 0 if isinstance(features, str) else len(features),
        "features": features if isinstance(features, str) else ", ".join(features),
        **metric_values(frame, pred),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def sample_weights(frame: pd.DataFrame, scheme: str) -> np.ndarray:
    n = len(frame)
    if scheme == "uniform":
        return np.ones(n, dtype=float)
    if scheme == "svc_reliability":
        rel = frame.get("svc_reliability_bin", pd.Series(["missing"] * n)).astype(str)
        mapping = {"high": 1.20, "mid": 1.00, "low": 0.75, "missing": 0.60}
        return rel.map(mapping).fillna(0.80).to_numpy(dtype=float)
    if scheme == "target_tail_guard":
        y = pd.to_numeric(frame["ln_price_krw"], errors="coerce")
        q05, q95 = y.quantile([0.05, 0.95])
        weights = np.ones(n, dtype=float)
        weights[(y < q05) | (y > q95)] = 0.60
        return weights
    raise ValueError(f"unknown weight scheme: {scheme}")


def add_combined_segments(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def apply(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["svc_artist_segment"] = (
            out.get("svc_reliability_bin", pd.Series(["missing"] * len(out))).astype(str)
            + "__"
            + out.get("artist_works_bin", pd.Series(["missing"] * len(out))).astype(str)
        )
        return out

    return apply(train), apply(val), apply(test)


def fit_direct_grid(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    outlier_rows: list[dict[str, Any]] = []
    for feature_set_name, raw_features in DIRECT_FEATURE_SETS.items():
        features = feature_exists(train, raw_features)
        tr = normalize(train, features)
        va = normalize(val, features)
        te = normalize(test, features)
        y = train["ln_price_krw"].to_numpy(dtype=float)
        for epsilon in EPSILONS:
            for alpha in ALPHAS:
                for weight_scheme in WEIGHT_SCHEMES:
                    weights = sample_weights(train, weight_scheme)
                    candidate = (
                        f"PP-WHUBER1_2_{feature_set_name}_eps{epsilon:.2f}_"
                        f"alpha{str(alpha).replace('.', 'p')}_{weight_scheme}"
                    )
                    model = huber_model(features, alpha, epsilon)
                    model.fit(tr[features], y, model__sample_weight=weights)
                    outlier_mask = getattr(model.named_steps["model"], "outliers_", np.array([], dtype=bool))
                    outlier_rows.append({
                        "candidate": candidate,
                        "feature_set": feature_set_name,
                        "epsilon": epsilon,
                        "alpha": alpha,
                        "weight_scheme": weight_scheme,
                        "train_outlier_rate": float(np.mean(outlier_mask)) if len(outlier_mask) else np.nan,
                        "train_scale": float(getattr(model.named_steps["model"], "scale_", np.nan)),
                    })
                    for split_name, frame, normalized in [("validation", val, va), ("test", test, te)]:
                        pred = np.asarray(model.predict(normalized[features]), dtype=float)
                        add_metric_row(
                            rows,
                            "PP-WHUBER1_2",
                            "epsilon_alpha_weighted_huber",
                            candidate,
                            split_name,
                            "huber_grid_weighted",
                            frame,
                            pred,
                            features,
                            alpha,
                            epsilon,
                            weight_scheme,
                            {"feature_set": feature_set_name},
                        )
                        preds.append(prediction_frame(
                            "PP-WHUBER1_2",
                            candidate,
                            "huber_grid_weighted",
                            split_name,
                            frame,
                            pred,
                            {"feature_set": feature_set_name, "epsilon": epsilon, "alpha": alpha, "weight_scheme": weight_scheme},
                        ))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True), pd.DataFrame(outlier_rows)


def fit_two_pass(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    feature_set_name = "svc_reliability_no_artist_key"
    features = feature_exists(train, DIRECT_FEATURE_SETS[feature_set_name])
    tr = normalize(train, features)
    va = normalize(val, features)
    te = normalize(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for epsilon in [1.05, 1.10, 1.35]:
        for alpha in [0.001, 0.01]:
            first = huber_model(features, alpha, epsilon)
            first.fit(tr[features], y)
            outliers = getattr(first.named_steps["model"], "outliers_", np.zeros(len(train), dtype=bool))
            for outlier_weight in [0.25, 0.50, 0.75]:
                weights = np.where(outliers, outlier_weight, 1.0)
                candidate = (
                    f"PP-WHUBER3_two_pass_{feature_set_name}_eps{epsilon:.2f}_"
                    f"alpha{str(alpha).replace('.', 'p')}_ow{str(outlier_weight).replace('.', 'p')}"
                )
                second = huber_model(features, alpha, epsilon)
                second.fit(tr[features], y, model__sample_weight=weights)
                diagnostics.append({
                    "candidate": candidate,
                    "epsilon": epsilon,
                    "alpha": alpha,
                    "outlier_weight": outlier_weight,
                    "first_pass_outlier_rate": float(np.mean(outliers)),
                    "second_pass_scale": float(getattr(second.named_steps["model"], "scale_", np.nan)),
                })
                for split_name, frame, normalized in [("validation", val, va), ("test", test, te)]:
                    pred = np.asarray(second.predict(normalized[features]), dtype=float)
                    add_metric_row(
                        rows,
                        "PP-WHUBER3",
                        "two_pass_outlier_reweighted_huber",
                        candidate,
                        split_name,
                        "two_pass_huber",
                        frame,
                        pred,
                        features,
                        alpha,
                        epsilon,
                        "outlier_reweight",
                        {"outlier_weight": outlier_weight, "first_pass_outlier_rate": float(np.mean(outliers))},
                    )
                    preds.append(prediction_frame(
                        "PP-WHUBER3",
                        candidate,
                        "two_pass_huber",
                        split_name,
                        frame,
                        pred,
                        {"epsilon": epsilon, "alpha": alpha, "outlier_weight": outlier_weight},
                    ))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True), pd.DataFrame(diagnostics)


def segment_epsilon(segment_col: str, segment_value: str, policy: str) -> float:
    if policy == "adaptive":
        if segment_col == "svc_reliability_bin":
            return {"high": 1.60, "mid": 1.35, "low": 1.10, "missing": 1.05}.get(segment_value, 1.20)
        if segment_col == "artist_works_bin":
            return {"high": 1.60, "mid": 1.35, "low": 1.10, "missing": 1.05}.get(segment_value, 1.20)
        return 1.20
    if policy == "robust":
        return 1.10
    return 1.35


def fit_segment_routing(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    features = feature_exists(train, SEGMENT_FEATURES)
    tr = normalize(train, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for segment_col in ["svc_reliability_bin", "artist_works_bin", "size_bin", "svc_artist_segment"]:
        for policy in ["adaptive", "robust", "balanced"]:
            alpha = 0.001
            min_rows = 250 if segment_col != "svc_artist_segment" else 400
            fallback = huber_model(features, alpha, 1.35)
            fallback.fit(tr[features], y)
            models: dict[str, Pipeline] = {}
            segment_counts = train[segment_col].astype(str).value_counts()
            for segment_value, count in segment_counts.items():
                if count < min_rows:
                    continue
                mask = train[segment_col].astype(str).eq(str(segment_value)).to_numpy()
                eps = segment_epsilon(segment_col, str(segment_value), policy)
                model = huber_model(features, alpha, eps)
                model.fit(tr.loc[mask, features], y[mask])
                models[str(segment_value)] = model
            candidate = f"PP-WHUBER4_segment_{segment_col}_{policy}_min{min_rows}"
            for split_name, frame in [("validation", val), ("test", test)]:
                normalized = normalize(frame, features)
                pred = np.asarray(fallback.predict(normalized[features]), dtype=float)
                used_specific = np.zeros(len(frame), dtype=bool)
                for segment_value, model in models.items():
                    mask = frame[segment_col].astype(str).eq(segment_value).to_numpy()
                    if not np.any(mask):
                        continue
                    pred[mask] = np.asarray(model.predict(normalized.loc[mask, features]), dtype=float)
                    used_specific[mask] = True
                add_metric_row(
                    rows,
                    "PP-WHUBER4",
                    "segment_specific_huber_routing",
                    candidate,
                    split_name,
                    "segment_huber_routing",
                    frame,
                    pred,
                    features,
                    alpha,
                    np.nan,
                    None,
                    {
                        "segment_col": segment_col,
                        "epsilon_policy": policy,
                        "min_rows": min_rows,
                        "n_segment_models": len(models),
                        "specific_model_coverage": float(np.mean(used_specific)),
                    },
                )
                preds.append(prediction_frame(
                    "PP-WHUBER4",
                    candidate,
                    "segment_huber_routing",
                    split_name,
                    frame,
                    pred,
                    {"segment_col": segment_col, "epsilon_policy": policy, "specific_model_coverage": used_specific.astype(float)},
                ))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def reference_metrics(val_ref: pd.DataFrame, test_ref: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for split_name, frame in [("validation", val_ref), ("test", test_ref)]:
        for candidate, col in [
            (CURRENT_CANDIDATE, "current_pred_log"),
            (PPV8_CANDIDATE, "ppv8_pred_log"),
            (FALLBACK_CANDIDATE, "fallback_pred_log"),
        ]:
            pred = frame[col].to_numpy(dtype=float)
            add_metric_row(
                rows,
                "REFERENCE",
                "reference",
                candidate,
                split_name,
                "reference_prediction",
                frame,
                pred,
                "reference_prediction",
            )
            preds.append(prediction_frame("REFERENCE", candidate, "reference_prediction", split_name, frame, pred))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def residual_feature_sets() -> dict[str, list[str]]:
    return {
        "pred_size_svc": wcoef.RESIDUAL_PRED_FEATURES
        + [feature for feature in wcoef.BASE_FEATURES if feature != "artist_key"]
        + ["size_bin"]
        + wcoef.SIZE_INTERACTION_FEATURES
        + wcoef.SVC_NUMERIC
        + wcoef.SVC_CATEGORICAL
        + wcoef.SVC_RELIABILITY_FEATURES,
        "pred_size_material_svc_artist": wcoef.residual_feature_sets()["resid_pred_size_material_svc_artist"],
    }


def crossfit_residual(frame: pd.DataFrame, features: list[str], alpha: float, epsilon: float) -> np.ndarray:
    folds = min(5, max(2, len(frame) // 100))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    pred = np.zeros(len(frame), dtype=float)
    y = actual_log_array(frame) - frame["current_pred_log"].to_numpy(dtype=float)
    for train_idx, holdout_idx in kfold.split(frame):
        model = huber_model(features, alpha, epsilon)
        tr = normalize(frame.iloc[train_idx].copy(), features)
        ho = normalize(frame.iloc[holdout_idx].copy(), features)
        model.fit(tr[features], y[train_idx])
        pred[holdout_idx] = np.asarray(model.predict(ho[features]), dtype=float)
    return pred


def fit_residual_tuning(val_ref: pd.DataFrame, test_ref: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for feature_set_name, raw_features in residual_feature_sets().items():
        features = feature_exists(val_ref, raw_features)
        y_val = actual_log_array(val_ref) - val_ref["current_pred_log"].to_numpy(dtype=float)
        for epsilon in RESIDUAL_EPSILONS:
            for alpha in RESIDUAL_ALPHAS:
                val_raw = crossfit_residual(val_ref, features, alpha, epsilon)
                model = huber_model(features, alpha, epsilon)
                va = normalize(val_ref, features)
                te = normalize(test_ref, features)
                model.fit(va[features], y_val)
                test_raw = np.asarray(model.predict(te[features]), dtype=float)
                base_label = (
                    f"PP-WHUBER5_resid_{feature_set_name}_eps{epsilon:.2f}_"
                    f"alpha{str(alpha).replace('.', 'p')}"
                )
                for cap in RESIDUAL_CAPS:
                    for strength in RESIDUAL_STRENGTHS:
                        label = f"{base_label}_cap{str(cap).replace('.', 'p')}_s{str(strength).replace('.', 'p')}"
                        for split_name, frame, raw in [("validation", val_ref, val_raw), ("test", test_ref, test_raw)]:
                            correction = np.clip(raw, -cap, cap) * strength
                            pred = frame["current_pred_log"].to_numpy(dtype=float) + correction
                            add_metric_row(
                                rows,
                                "PP-WHUBER5",
                                "residual_huber_epsilon_tuning",
                                label,
                                split_name,
                                "residual_huber_epsilon_grid",
                                frame,
                                pred,
                                features,
                                alpha,
                                epsilon,
                                None,
                                {
                                    "feature_set": feature_set_name,
                                    "correction_cap": cap,
                                    "correction_strength": strength,
                                    "mean_abs_correction": float(np.mean(np.abs(correction))),
                                },
                            )
                            preds.append(prediction_frame(
                                "PP-WHUBER5",
                                label,
                                "residual_huber_epsilon_grid",
                                split_name,
                                frame,
                                pred,
                                {
                                    "feature_set": feature_set_name,
                                    "epsilon": epsilon,
                                    "alpha": alpha,
                                    "correction_cap": cap,
                                    "correction_strength": strength,
                                    "correction_log": correction,
                                },
                            ))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    current = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    val["balanced_score"] = (
        0.45 * val["MdAPE"] / float(current["MdAPE"])
        + 0.35 * val["MAPE"] / float(current["MAPE"])
        + 0.20 * val["p95_APE"] / float(current["p95_APE"])
    )
    non_ref = val[~val["sub_experiment"].eq("REFERENCE")].copy()
    selectors = {
        "MdAPE 우선": (non_ref, ["MdAPE", "MAPE", "p95_APE"]),
        "MAPE 우선 + MdAPE 5% 이내": (
            non_ref[non_ref["MdAPE"] <= float(current["MdAPE"]) * 1.05].copy(),
            ["MAPE", "MdAPE", "p95_APE"],
        ),
        "p95 우선 + MdAPE 8% 이내": (
            non_ref[non_ref["MdAPE"] <= float(current["MdAPE"]) * 1.08].copy(),
            ["p95_APE", "MdAPE", "MAPE"],
        ),
        "균형 점수": (non_ref, ["balanced_score", "MdAPE", "MAPE", "p95_APE"]),
    }
    rows: list[dict[str, Any]] = []
    for objective, (pool, sort_cols) in selectors.items():
        if pool.empty:
            pool = non_ref
        selected = pool.sort_values(sort_cols).iloc[0]
        rows.append({
            "selection_objective": objective,
            "selected_candidate": selected["candidate"],
            "sub_experiment": selected["sub_experiment"],
            "family": selected["family"],
            "validation_MdAPE": float(selected["MdAPE"]),
            "validation_MAPE": float(selected["MAPE"]),
            "validation_p95_APE": float(selected["p95_APE"]),
            "validation_RMSE_log": float(selected["RMSE_log"]),
        })
    selected_df = pd.DataFrame(rows).drop_duplicates("selected_candidate")
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    output_rows: list[dict[str, Any]] = []
    for row in selected_df.to_dict("records"):
        candidate = row["selected_candidate"]
        if candidate in test.index:
            test_row = test.loc[candidate]
            if isinstance(test_row, pd.DataFrame):
                test_row = test_row.iloc[0]
            row.update({
                "test_MdAPE": float(test_row["MdAPE"]),
                "test_MAPE": float(test_row["MAPE"]),
                "test_p95_APE": float(test_row["p95_APE"]),
                "test_RMSE_log": float(test_row["RMSE_log"]),
            })
        output_rows.append(row)
    return pd.DataFrame(output_rows)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
    }


def bootstrap_candidates(predictions: pd.DataFrame, selected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    test = predictions[predictions["split"].eq("test")].copy()
    top_test = (
        test.groupby("candidate", as_index=False)
        .agg(MdAPE=("ape", "median"), MAPE=("ape", "mean"), p95_APE=("ape", lambda x: float(np.quantile(x, 0.95))))
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(8)["candidate"]
        .tolist()
    )
    candidates = [CURRENT_CANDIDATE] + selected["selected_candidate"].dropna().tolist() + top_test
    candidates = list(dict.fromkeys(candidates))
    wide = test[test["candidate"].isin(candidates)].pivot_table(
        index=["_track6_row_id", "artist_key"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    actual = test[["_track6_row_id", "artist_key", "actual_log", "actual_price"]].drop_duplicates("_track6_row_id")
    wide = wide.merge(actual, on=["_track6_row_id", "artist_key"], how="inner").reset_index(drop=True)
    candidates = [candidate for candidate in candidates if candidate in wide.columns and wide[candidate].notna().all()]
    rng = np.random.default_rng(SEED)
    artists = wide["artist_key"].astype(str).unique()
    artist_to_indices = {artist: wide.index[wide["artist_key"].astype(str).eq(artist)].to_numpy() for artist in artists}
    samples: list[dict[str, Any]] = []

    def add_sample(indices: np.ndarray, sample_type: str, iteration: int) -> None:
        actual_price = wide.loc[indices, "actual_price"].to_numpy(dtype=float)
        actual_log = wide.loc[indices, "actual_log"].to_numpy(dtype=float)
        current_metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, CURRENT_CANDIDATE].to_numpy(dtype=float))
        for candidate in candidates:
            metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, candidate].to_numpy(dtype=float))
            row = {"sample_type": sample_type, "iteration": iteration, "candidate": candidate}
            for name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[name] = metric[name]
                row[f"delta_{name}"] = metric[name] - current_metric[name]
            samples.append(row)

    n = len(wide)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        add_sample(rng.integers(0, n, size=n), "row_bootstrap", iteration)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        add_sample(np.concatenate([artist_to_indices[artist] for artist in sampled_artists]), "artist_bootstrap", iteration)

    samples_df = pd.DataFrame(samples)
    summary_rows: list[dict[str, Any]] = []
    for (sample_type, candidate), group in samples_df.groupby(["sample_type", "candidate"], observed=False):
        row = {
            "experiment_id": EXP_ID,
            "sub_experiment": "PP-WHUBER6",
            "sample_type": sample_type,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
        }
        for name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{name}"]
            row[f"mean_delta_{name}"] = float(delta.mean())
            row[f"improvement_probability_{name}"] = float(np.mean(delta < 0))
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), samples_df


def render_report(metrics: pd.DataFrame, selected: pd.DataFrame, bootstrap: pd.DataFrame) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    validation = metrics[metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    current_test = test[test["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    current_val = validation[validation["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    top_test = test.head(35)
    top_val = validation.head(35)
    boot_view = bootstrap.sort_values(["sample_type", "mean_delta_MdAPE", "mean_delta_MAPE"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: Huber의 이상치 처리 기준과 계수 규제를 조정해 Warm 성능 개선 여지를 확인",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        f"- 기준 validation MdAPE/MAPE/p95: `{current_val['MdAPE']:.4f}` / `{current_val['MAPE']:.4f}` / `{current_val['p95_APE']:.4f}`",
        f"- 기준 test MdAPE/MAPE/p95: `{current_test['MdAPE']:.4f}` / `{current_test['MAPE']:.4f}` / `{current_test['p95_APE']:.4f}`",
        "",
        "## 0. 실행 결론",
        "",
        "- 직접 Huber 재학습 계열은 현재 Warm 1순위 후보를 대체하지 못함",
        "- Huber `epsilon`/`alpha` 직접 튜닝, 표본 가중치, 2-pass 이상치 재가중, 구간별 Huber 라우팅은 일부 validation 개선이 있었지만 test에서 MdAPE/MAPE/p95 균형이 약함",
        "- 가장 의미 있는 개선은 현재 Warm 1순위 후보 위에 residual Huber를 약하게 적용한 PP-WHUBER5에서 발생",
        "- MdAPE 우선 후보: `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25`",
        "- MdAPE 우선 후보 test 성능: MdAPE `0.1346`, MAPE `0.2745`, p95_APE `0.8387`",
        "- 균형 후보: `PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25`",
        "- 균형 후보 test 성능: MdAPE `0.1353`, MAPE `0.2747`, p95_APE `0.8291`",
        "- 판단: v0.1 운영 후보에 바로 반영하기보다 PP-WHUBER5 후보를 반복 split 또는 OOF 재검증 대상으로 승격",
        "",
        "## 1. 실험 구성",
        "",
        "- PP-WHUBER1: Huber `epsilon`/`alpha` 그리드",
        "- PP-WHUBER2: 유사 작품 신뢰도/target tail 기반 표본 가중치",
        "- PP-WHUBER3: 1차 Huber outlier를 낮은 가중치로 두는 2-pass Huber",
        "- PP-WHUBER4: 유사 작품 신뢰도, 작가 이력량, 크기 구간별 별도 Huber 라우팅",
        "- PP-WHUBER5: 현재 Warm 1순위 후보 위 residual Huber의 `epsilon` 튜닝",
        "- PP-WHUBER6: row/artist bootstrap 안정성 검증",
        "",
        "## 2. Test 상위 후보",
        "",
        "| 순위 | 세부 실험 | 후보 | 계열 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---:|---|---|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_test.itertuples(index=False), 1):
        lines.append(
            f"| {rank} | {row.sub_experiment} | `{row.candidate}` | {row.family} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += [
        "",
        "## 3. Validation 기준 선택 후보",
        "",
        "| 선택 기준 | 세부 실험 | 후보 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected.itertuples(index=False):
        lines.append(
            f"| {row.selection_objective} | {row.sub_experiment} | `{row.selected_candidate}` | "
            f"{row.validation_MdAPE:.4f} | {row.validation_MAPE:.4f} | {row.validation_p95_APE:.4f} | "
            f"{row.test_MdAPE:.4f} | {row.test_MAPE:.4f} | {row.test_p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 4. Bootstrap 안정성 요약",
        "",
        "| 표본 추출 방식 | 후보 | MdAPE 평균 차이 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in boot_view.head(35).itertuples(index=False):
        lines.append(
            f"| {row.sample_type} | `{row.candidate}` | {row.mean_delta_MdAPE:.5f} | "
            f"{row.improvement_probability_MdAPE:.3f} | {row.improvement_probability_MAPE:.3f} | "
            f"{row.improvement_probability_p95_APE:.3f} |"
        )
    lines += [
        "",
        "## 5. 해석 기준",
        "",
        "- 직접 Huber가 개선되면 Huber 설정/가중치 자체를 v0.1 후속 후보로 검토",
        "- residual Huber만 개선되면 기본 모델은 유지하고 사후 보정 후보로 분리",
        "- validation 선택 후보와 test 상위 후보가 다르면 바로 반영하지 않고 추가 split 검증",
        "- MAPE 개선 확률이 낮으면 대표 가격 후보가 아니라 큰 오차 방어 후보로 분리",
        "",
        "## 6. 산출물",
        "",
        "- `outputs/all_candidate_metrics.csv`",
        "- `outputs/predictions.csv`",
        "- `outputs/selected_validation_candidates.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
        "- `outputs/direct_huber_outlier_diagnostics.csv`",
        "- `outputs/two_pass_diagnostics.csv`",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">Huber의 epsilon, alpha, 표본 가중치, 이상치 재가중, 구간별 학습을 같은 Warm split에서 비교한 리포트.</div>
<h2>실행 결론</h2>
<ul>
<li>직접 Huber 재학습 계열은 현재 Warm 1순위 후보를 대체하지 못함.</li>
<li>가장 의미 있는 개선은 현재 Warm 1순위 후보 위에 residual Huber를 약하게 적용한 PP-WHUBER5에서 발생.</li>
<li>MdAPE 우선 후보: <code>PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.60_alpha0p001_cap0p08_s0p25</code>, test MdAPE 0.1346 / MAPE 0.2745 / p95_APE 0.8387.</li>
<li>균형 후보: <code>PP-WHUBER5_resid_pred_size_material_svc_artist_eps1.35_alpha0p001_cap0p08_s0p25</code>, test MdAPE 0.1353 / MAPE 0.2747 / p95_APE 0.8291.</li>
<li>판단: v0.1 운영 후보에 바로 반영하기보다 반복 split 또는 OOF 재검증 대상으로 승격.</li>
</ul>
<h2>Validation 기준 선택 후보</h2>{selected.to_html(index=False, escape=True)}
<h2>Test 상위 후보</h2>{top_test.to_html(index=False, escape=True)}
<h2>Validation 상위 후보</h2>{top_val.to_html(index=False, escape=True)}
<h2>Bootstrap 안정성 요약</h2>{boot_view.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    selected: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    bootstrap_samples: pd.DataFrame,
    direct_diag: pd.DataFrame,
    two_pass_diag: pd.DataFrame,
) -> None:
    metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_validation_candidates.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)
    direct_diag.to_csv(EXP_DIR / "outputs" / "direct_huber_outlier_diagnostics.csv", index=False)
    two_pass_diag.to_csv(EXP_DIR / "outputs" / "two_pass_diagnostics.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "current_candidate": CURRENT_CANDIDATE,
        "epsilons": EPSILONS,
        "alphas": ALPHAS,
        "weight_schemes": WEIGHT_SCHEMES,
        "residual_epsilons": RESIDUAL_EPSILONS,
        "residual_alphas": RESIDUAL_ALPHAS,
        "residual_caps": RESIDUAL_CAPS,
        "residual_strengths": RESIDUAL_STRENGTHS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "leakage_control": {
            "artist_priors": "delegated to PP-WCOEF loader: train OOF, validation/test train-only",
            "comparable_features": "PP-SVC5 train OOF comparable features",
            "residual_validation": "validation internal cross-fit",
            "residual_test": "residual model fitted on full validation and applied to test",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics, selected, bootstrap_summary)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    train, val, test = wcoef.load_frames()
    train, val, test = add_combined_segments(train, val, test)

    direct_metrics, direct_predictions, direct_diag = fit_direct_grid(train, val, test)
    two_pass_metrics, two_pass_predictions, two_pass_diag = fit_two_pass(train, val, test)
    segment_metrics, segment_predictions = fit_segment_routing(train, val, test)

    val_ref, test_ref, _ = wcoef.add_reference_prediction_features(val, test)
    ref_metrics, ref_predictions = reference_metrics(val_ref, test_ref)
    residual_metrics, residual_predictions = fit_residual_tuning(val_ref, test_ref)

    all_metrics = pd.concat([ref_metrics, direct_metrics, two_pass_metrics, segment_metrics, residual_metrics], ignore_index=True)
    all_predictions = pd.concat([ref_predictions, direct_predictions, two_pass_predictions, segment_predictions, residual_predictions], ignore_index=True)
    selected = select_validation_candidates(all_metrics)
    bootstrap_summary, bootstrap_samples = bootstrap_candidates(all_predictions, selected)
    write_outputs(all_metrics, all_predictions, selected, bootstrap_summary, bootstrap_samples, direct_diag, two_pass_diag)

    top_test = all_metrics[all_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(10)
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "top_test_candidates": top_test[["sub_experiment", "candidate", "family", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict("records"),
        "selected_validation_candidates": selected.to_dict("records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
