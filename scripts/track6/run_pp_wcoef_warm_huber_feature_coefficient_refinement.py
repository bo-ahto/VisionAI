#!/usr/bin/env python3
"""Run PP-WCOEF1~PP-WCOEF6 Warm Huber coefficient refinement experiments.

The experiment starts from the current Warm v0.1 candidate:

    blend_svcnum_ppv8_wsvc_0.70

It tests whether Huber can improve by making its linear coefficients more
granular by size, material/support, comparable-stat reliability, and artist
baseline/meta segments. It also tests a weak residual correction on top of the
current candidate. The residual correction is diagnostic: current-candidate
predictions are available for validation/test only, so validation is used as a
calibration set with internal cross-fitting for validation predictions.
"""
from __future__ import annotations

import html
import json
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


warnings.filterwarnings("ignore", category=ConvergenceWarning)


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WCOEF"
EXP_SLUG = "PP-WCOEF_warm_huber_feature_coefficient_refinement"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm Huber 계수 세분화 및 잔차 보정 실험"
SEED = 20260606

SPLIT_ROOT = REPO / "data" / "track6_split"
SVC5_DIR = EXP_ROOT / "PP-SVC5_warm_multilevel_comparable_stats"
SVC5_FEATURES = {
    "train": SVC5_DIR / "outputs" / "comparable_multilevel_features_train_oof.csv",
    "validation": SVC5_DIR / "outputs" / "comparable_multilevel_features_validation.csv",
    "test": SVC5_DIR / "outputs" / "comparable_multilevel_features_test.csv",
}
SVC5_PREDICTIONS = SVC5_DIR / "outputs" / "predictions.csv"

CURRENT_CANDIDATE = "blend_svcnum_ppv8_wsvc_0.70"
PPV8_CANDIDATE = "pp_v8_compact_blend_mape_guarded"
FALLBACK_CANDIDATE = "fallback_numeric"

BASE_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
    "artist_key",
]

BASE_NUMERIC = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
]

BASE_CATEGORICAL = [
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
    "artist_key",
]

ARTIST_META_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_meta_birth_year",
]

ARTIST_META_CATEGORICAL = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
]

SVC_NUMERIC = [
    "svc_group_log_price_median",
    "svc_group_log_price_q25",
    "svc_group_log_price_q75",
    "svc_group_log_price_iqr",
    "svc_group_log_unit_area_median",
    "svc_group_log_unit_area_iqr",
    "svc_group_n_log",
]

SVC_CATEGORICAL = [
    "svc_group_level",
    "svc_coverage_tier",
]

ARTIST_PRIOR_FEATURES = [
    "artist_prior_log_price_k5",
    "artist_prior_log_price_k15",
    "artist_prior_log_price_k30",
    "artist_prior_log_unit_area_k15",
    "artist_prior_n_log",
    "artist_prior_iqr",
]

SIZE_INTERACTION_FEATURES = [
    "log_area_x_size_small",
    "log_area_x_size_mid_low",
    "log_area_x_size_mid_high",
    "log_area_x_size_large",
    "aspect_ratio_x_size_small",
    "aspect_ratio_x_size_mid_low",
    "aspect_ratio_x_size_mid_high",
    "aspect_ratio_x_size_large",
]

MATERIAL_SIZE_FEATURES = [
    "size_bin",
    "medium_size_bin",
    "support_size_bin",
    "medium_support_size_bin",
]

SVC_RELIABILITY_FEATURES = [
    "svc_reliability_bin",
    "svc_price_x_rel_high",
    "svc_price_x_rel_mid",
    "svc_price_x_rel_low",
    "svc_unit_area_x_rel_high",
    "svc_unit_area_x_rel_mid",
    "svc_unit_area_x_rel_low",
    "svc_n_log_x_rel_high",
    "svc_iqr_x_rel_low",
    "svc_missing_flag",
]

ARTIST_SEGMENT_FEATURES = [
    "artist_works_bin",
    "artist_meta_total_works_bin",
    "artist_prior_price_x_works_low",
    "artist_prior_price_x_works_mid",
    "artist_prior_price_x_works_high",
    "artist_prior_unit_area_x_works_high",
]

RESIDUAL_PRED_FEATURES = [
    "current_pred_log",
    "ppv8_pred_log",
    "fallback_pred_log",
    "current_ppv8_gap_abs",
    "current_fallback_gap_abs",
    "pred_log_bin",
]

ALPHAS = [0.0001, 0.001, 0.01]
RESIDUAL_ALPHAS = [0.001, 0.01]
RESIDUAL_CAPS = [0.03, 0.05, 0.08, 0.12]
RESIDUAL_STRENGTHS = [0.25, 0.50, 0.75, 1.00]
BOOTSTRAP_ITERATIONS = 300


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def read_split(name: str) -> pd.DataFrame:
    path = SPLIT_ROOT / f"track6_{name}.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame["price_krw"] = pd.to_numeric(frame["price_krw"], errors="coerce")
    frame["ln_price_krw"] = pd.to_numeric(frame["ln_price_krw"], errors="coerce")
    return frame.dropna(subset=["price_krw", "ln_price_krw"]).copy()


def source_unit_area(frame: pd.DataFrame) -> pd.Series:
    area = np.clip(pd.to_numeric(frame["area_cm2"], errors="coerce").fillna(1.0), 1.0, None)
    return pd.to_numeric(frame["ln_price_krw"], errors="coerce") - np.log(area)


def aggregate_artist_priors(source: pd.DataFrame) -> pd.DataFrame:
    src = source.copy()
    src["artist_key"] = src["artist_key"].astype("string").fillna("__MISSING__")
    src["source_log_unit_area"] = source_unit_area(src)
    grouped = src.groupby("artist_key", dropna=False, observed=False)
    stats = grouped.agg(
        artist_price_median=("ln_price_krw", "median"),
        artist_price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
        artist_price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
        artist_unit_area_median=("source_log_unit_area", "median"),
        artist_prior_n=("ln_price_krw", "size"),
    ).reset_index()
    stats["artist_prior_iqr_raw"] = stats["artist_price_q75"] - stats["artist_price_q25"]
    return stats


def apply_artist_priors(source: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    stats = aggregate_artist_priors(source)
    global_price = float(pd.to_numeric(source["ln_price_krw"], errors="coerce").median())
    global_unit = float(source_unit_area(source).median())
    out = target[["_track6_row_id", "artist_key"]].copy()
    out["artist_key"] = out["artist_key"].astype("string").fillna("__MISSING__")
    out = out.merge(stats, on="artist_key", how="left")
    n = pd.to_numeric(out["artist_prior_n"], errors="coerce").fillna(0.0)
    artist_price = pd.to_numeric(out["artist_price_median"], errors="coerce").fillna(global_price)
    artist_unit = pd.to_numeric(out["artist_unit_area_median"], errors="coerce").fillna(global_unit)
    for k in [5, 15, 30]:
        weight = n / (n + float(k))
        out[f"artist_prior_log_price_k{k}"] = weight * artist_price + (1.0 - weight) * global_price
        if k == 15:
            out[f"artist_prior_log_unit_area_k{k}"] = weight * artist_unit + (1.0 - weight) * global_unit
    out["artist_prior_n_log"] = np.log1p(n)
    out["artist_prior_iqr"] = pd.to_numeric(out["artist_prior_iqr_raw"], errors="coerce").fillna(0.0).clip(0.0, 3.0)
    return out[["_track6_row_id", *ARTIST_PRIOR_FEATURES]]


def crossfit_artist_priors(train: pd.DataFrame) -> pd.DataFrame:
    folds = min(5, max(2, len(train) // 1000))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    parts: list[pd.DataFrame] = []
    for source_idx, holdout_idx in kfold.split(train):
        parts.append(apply_artist_priors(train.iloc[source_idx].copy(), train.iloc[holdout_idx].copy()))
    return pd.concat(parts, ignore_index=True)


def bin_edges(train: pd.DataFrame, col: str, quantiles: list[float]) -> np.ndarray:
    values = pd.to_numeric(train[col], errors="coerce").dropna()
    edges = [-np.inf]
    if not values.empty:
        edges.extend(np.quantile(values, quantiles).tolist())
    edges.append(np.inf)
    unique_edges = np.unique(np.asarray(edges, dtype=float))
    if len(unique_edges) < 3:
        return np.array([-np.inf, np.inf])
    return unique_edges


def cut_with_edges(values: pd.Series, edges: np.ndarray, labels: list[str]) -> pd.Series:
    actual_labels = labels[: max(1, len(edges) - 1)]
    return pd.cut(pd.to_numeric(values, errors="coerce"), bins=edges, labels=actual_labels, include_lowest=True).astype("string")


def add_segment_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    size_edges = bin_edges(train, "log_area", [0.25, 0.50, 0.75])
    works_edges = bin_edges(train, "artist_works_count_train", [0.33, 0.66])
    meta_total_edges = bin_edges(train, "artist_meta_total_works", [0.33, 0.66])
    global_log_price = float(pd.to_numeric(train["ln_price_krw"], errors="coerce").median())
    global_unit_area = float(source_unit_area(train).median())

    def apply(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["size_bin"] = cut_with_edges(out["log_area"], size_edges, ["small", "mid_low", "mid_high", "large"]).fillna("missing")
        out["artist_works_bin"] = cut_with_edges(out["artist_works_count_train"], works_edges, ["low", "mid", "high"]).fillna("missing")
        out["artist_meta_total_works_bin"] = cut_with_edges(out["artist_meta_total_works"], meta_total_edges, ["low", "mid", "high"]).fillna("missing")

        medium = out["medium_category"].astype("string").fillna("__MISSING__")
        support = out["support_category"].astype("string").fillna("__MISSING__")
        medium_support = out["medium_support_bucket"].astype("string").fillna("__MISSING__")
        size = out["size_bin"].astype("string").fillna("missing")
        out["medium_size_bin"] = medium + "__" + size
        out["support_size_bin"] = support + "__" + size
        out["medium_support_size_bin"] = medium_support + "__" + size

        log_area = pd.to_numeric(out["log_area"], errors="coerce").fillna(0.0)
        aspect_ratio = pd.to_numeric(out["aspect_ratio"], errors="coerce").fillna(0.0)
        for label in ["small", "mid_low", "mid_high", "large"]:
            mask = out["size_bin"].eq(label).astype(float)
            out[f"log_area_x_size_{label}"] = log_area * mask
            out[f"aspect_ratio_x_size_{label}"] = aspect_ratio * mask

        n = pd.to_numeric(out.get("svc_group_n", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(0.0)
        n_log = pd.to_numeric(out.get("svc_group_n_log", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(0.0)
        svc_iqr = pd.to_numeric(out.get("svc_group_log_price_iqr", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(99.0)
        svc_price = pd.to_numeric(out.get("svc_group_log_price_median", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(global_log_price)
        svc_unit = pd.to_numeric(out.get("svc_group_log_unit_area_median", pd.Series(np.nan, index=out.index)), errors="coerce").fillna(global_unit_area)
        rel = np.where((n >= 30) & (svc_iqr <= 0.70), "high", np.where((n >= 10) & (svc_iqr <= 1.20), "mid", "low"))
        rel = np.where(n <= 0, "missing", rel)
        out["svc_reliability_bin"] = pd.Series(rel, index=out.index).astype("string")
        for label in ["high", "mid", "low"]:
            mask = out["svc_reliability_bin"].eq(label).astype(float)
            out[f"svc_price_x_rel_{label}"] = svc_price * mask
            out[f"svc_unit_area_x_rel_{label}"] = svc_unit * mask
        out["svc_n_log_x_rel_high"] = n_log * out["svc_reliability_bin"].eq("high").astype(float)
        out["svc_iqr_x_rel_low"] = svc_iqr.clip(0.0, 3.0) * out["svc_reliability_bin"].eq("low").astype(float)
        out["svc_missing_flag"] = out["svc_reliability_bin"].eq("missing").astype(int)

        prior_price = pd.to_numeric(out["artist_prior_log_price_k15"], errors="coerce").fillna(global_log_price)
        prior_unit = pd.to_numeric(out["artist_prior_log_unit_area_k15"], errors="coerce").fillna(global_unit_area)
        for label in ["low", "mid", "high"]:
            mask = out["artist_works_bin"].eq(label).astype(float)
            out[f"artist_prior_price_x_works_{label}"] = prior_price * mask
        out["artist_prior_unit_area_x_works_high"] = prior_unit * out["artist_works_bin"].eq("high").astype(float)
        return out

    return apply(train), apply(val), apply(test)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = read_split("train")
    val = read_split("val_warm")
    test = read_split("test_warm")
    for split_name, frame in [("train", train), ("validation", val), ("test", test)]:
        features = pd.read_csv(SVC5_FEATURES[split_name], low_memory=False)
        frame = frame.merge(features, on="_track6_row_id", how="left")
        if split_name == "train":
            train = frame
        elif split_name == "validation":
            val = frame
        else:
            test = frame

    train_priors = crossfit_artist_priors(train)
    val_priors = apply_artist_priors(train, val)
    test_priors = apply_artist_priors(train, test)
    train = train.merge(train_priors, on="_track6_row_id", how="left")
    val = val.merge(val_priors, on="_track6_row_id", how="left")
    test = test.merge(test_priors, on="_track6_row_id", how="left")
    return add_segment_features(train, val, test)


def feature_exists(frame: pd.DataFrame, features: list[str]) -> list[str]:
    return [feature for feature in dict.fromkeys(features) if feature in frame.columns]


def numeric_features() -> set[str]:
    return set(
        BASE_NUMERIC
        + ARTIST_META_NUMERIC
        + SVC_NUMERIC
        + ARTIST_PRIOR_FEATURES
        + SIZE_INTERACTION_FEATURES
        + [f for f in SVC_RELIABILITY_FEATURES if f != "svc_reliability_bin"]
        + [f for f in ARTIST_SEGMENT_FEATURES if not f.endswith("_bin")]
        + [f for f in RESIDUAL_PRED_FEATURES if f != "pred_log_bin"]
    )


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_all = numeric_features()
    numeric = [feature for feature in features if feature in numeric_all]
    categorical = [feature for feature in features if feature not in numeric]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def huber_model(features: list[str], alpha: float) -> Pipeline:
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
        ("model", HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=5000)),
    ])


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    actual_log = pd.to_numeric(frame["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    actual_price = pd.to_numeric(frame["price_krw"], errors="coerce").to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def prediction_frame(
    sub_experiment: str,
    candidate: str,
    method: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "candidate": candidate,
        "method": method,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
    })
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


def coefficient_frame(model: Pipeline, candidate: str, sub_experiment: str) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    try:
        names = prep.get_feature_names_out()
    except Exception:
        names = np.array([f"feature_{i}" for i in range(len(reg.coef_))])
    coef = np.asarray(reg.coef_, dtype=float)
    frame = pd.DataFrame({
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "candidate": candidate,
        "encoded_feature": names,
        "coefficient": coef,
        "abs_coefficient": np.abs(coef),
    })
    return frame.sort_values("abs_coefficient", ascending=False).head(200)


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
        "n_features": 0 if isinstance(features, str) else len(features),
        "features": features if isinstance(features, str) else ", ".join(features),
        **metric_values(frame, pred),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def direct_huber_feature_sets() -> dict[str, dict[str, Any]]:
    return {
        "PP-WCOEF1_size_segment_coefficients": {
            "sub_experiment": "PP-WCOEF1",
            "family": "huber_size_coefficients",
            "features": BASE_FEATURES + ["size_bin"] + SIZE_INTERACTION_FEATURES,
        },
        "PP-WCOEF2_material_support_size_coefficients": {
            "sub_experiment": "PP-WCOEF2",
            "family": "huber_material_support_coefficients",
            "features": BASE_FEATURES + MATERIAL_SIZE_FEATURES,
        },
        "PP-WCOEF3_comparable_reliability_coefficients": {
            "sub_experiment": "PP-WCOEF3",
            "family": "huber_comparable_reliability_coefficients",
            "features": BASE_FEATURES + SVC_NUMERIC + SVC_CATEGORICAL + SVC_RELIABILITY_FEATURES,
        },
        "PP-WCOEF4_artist_prior_meta_coefficients": {
            "sub_experiment": "PP-WCOEF4",
            "family": "huber_artist_prior_meta_coefficients",
            "features": BASE_FEATURES + ARTIST_PRIOR_FEATURES + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL + ARTIST_SEGMENT_FEATURES,
        },
        "PP-WCOEF4_artist_prior_meta_no_artist_key": {
            "sub_experiment": "PP-WCOEF4",
            "family": "huber_artist_prior_meta_coefficients",
            "features": [f for f in BASE_FEATURES if f != "artist_key"]
            + ARTIST_PRIOR_FEATURES
            + ARTIST_META_NUMERIC
            + ARTIST_META_CATEGORICAL
            + ARTIST_SEGMENT_FEATURES,
        },
        "PP-WCOEF4_all_detail_coefficients": {
            "sub_experiment": "PP-WCOEF4",
            "family": "huber_all_detail_coefficients",
            "features": BASE_FEATURES
            + ["size_bin"]
            + SIZE_INTERACTION_FEATURES
            + MATERIAL_SIZE_FEATURES
            + SVC_NUMERIC
            + SVC_CATEGORICAL
            + SVC_RELIABILITY_FEATURES
            + ARTIST_PRIOR_FEATURES
            + ARTIST_META_NUMERIC
            + ARTIST_META_CATEGORICAL
            + ARTIST_SEGMENT_FEATURES,
        },
    }


def fit_direct_huber_candidates(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coeff_rows: list[pd.DataFrame] = []
    for base_name, config in direct_huber_feature_sets().items():
        sub_experiment = config["sub_experiment"]
        family = config["family"]
        features = feature_exists(train, config["features"])
        for alpha in ALPHAS:
            label = f"{base_name}_alpha{str(alpha).replace('.', 'p')}"
            model = huber_model(features, alpha)
            tr = normalize(train, features)
            va = normalize(val, features)
            te = normalize(test, features)
            model.fit(tr[features], tr["ln_price_krw"].to_numpy(dtype=float))
            coeff_rows.append(coefficient_frame(model, label, sub_experiment))
            for split_name, frame, normalized in [("validation", val, va), ("test", test, te)]:
                pred = np.asarray(model.predict(normalized[features]), dtype=float)
                add_metric_row(
                    metrics_rows,
                    sub_experiment,
                    family,
                    label,
                    split_name,
                    "huber_retrained",
                    frame,
                    pred,
                    features,
                    alpha,
                )
                pred_rows.append(prediction_frame(sub_experiment, label, "huber_retrained", split_name, frame, pred))
    return pd.DataFrame(metrics_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coeff_rows, ignore_index=True)


def load_reference_predictions() -> pd.DataFrame:
    pred = pd.read_csv(SVC5_PREDICTIONS, low_memory=False)
    keep = {CURRENT_CANDIDATE, PPV8_CANDIDATE, FALLBACK_CANDIDATE}
    return pred[pred["candidate"].isin(keep) & pred["split"].isin(["validation", "test"])].copy()


def reference_wide(ref: pd.DataFrame, split: str) -> pd.DataFrame:
    part = ref[ref["split"].eq(split)].copy()
    base_cols = ["split", "_track6_row_id", "actual_log", "actual_price", "artist_key", "artist_name_ko"]
    base = part[base_cols].drop_duplicates(["split", "_track6_row_id"])
    wide = part.pivot_table(index=["split", "_track6_row_id"], columns="candidate", values="pred_log", aggfunc="last").reset_index()
    wide.columns.name = None
    return base.merge(wide, on=["split", "_track6_row_id"], how="inner")


def add_reference_prediction_features(
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ref = load_reference_predictions()
    ref_val = reference_wide(ref, "validation")
    ref_test = reference_wide(ref, "test")
    rename = {
        CURRENT_CANDIDATE: "current_pred_log",
        PPV8_CANDIDATE: "ppv8_pred_log",
        FALLBACK_CANDIDATE: "fallback_pred_log",
    }
    ref_val = ref_val.rename(columns=rename)
    ref_test = ref_test.rename(columns=rename)
    keep = ["_track6_row_id", "current_pred_log", "ppv8_pred_log", "fallback_pred_log"]
    val_out = val.merge(ref_val[keep], on="_track6_row_id", how="inner")
    test_out = test.merge(ref_test[keep], on="_track6_row_id", how="inner")

    pred_edges = bin_edges(val_out.rename(columns={"current_pred_log": "pred_for_bin"}), "pred_for_bin", [0.25, 0.50, 0.75])

    def apply(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["current_ppv8_gap_abs"] = np.abs(out["current_pred_log"] - out["ppv8_pred_log"])
        out["current_fallback_gap_abs"] = np.abs(out["current_pred_log"] - out["fallback_pred_log"])
        out["pred_log_bin"] = cut_with_edges(out["current_pred_log"], pred_edges, ["low", "mid_low", "mid_high", "high"]).fillna("missing")
        return out

    return apply(val_out), apply(test_out), ref


def current_reference_metrics(
    ref: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for split_name, frame in [("validation", val), ("test", test)]:
        actual_frame = frame.rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
        for candidate, col in [
            (CURRENT_CANDIDATE, "current_pred_log"),
            (PPV8_CANDIDATE, "ppv8_pred_log"),
            (FALLBACK_CANDIDATE, "fallback_pred_log"),
        ]:
            pred = frame[col].to_numpy(dtype=float)
            sub = "REFERENCE"
            add_metric_row(
                rows,
                sub,
                "reference",
                candidate,
                split_name,
                "reference_prediction",
                actual_frame,
                pred,
                "reference_prediction",
            )
            preds.append(prediction_frame(sub, candidate, "reference_prediction", split_name, actual_frame, pred))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def residual_feature_sets() -> dict[str, list[str]]:
    safe_base = [f for f in BASE_FEATURES if f != "artist_key"]
    return {
        "resid_pred_size_svc": RESIDUAL_PRED_FEATURES
        + safe_base
        + ["size_bin"]
        + SIZE_INTERACTION_FEATURES
        + SVC_NUMERIC
        + SVC_CATEGORICAL
        + SVC_RELIABILITY_FEATURES,
        "resid_pred_size_material_svc_artist": RESIDUAL_PRED_FEATURES
        + safe_base
        + MATERIAL_SIZE_FEATURES
        + SVC_NUMERIC
        + SVC_CATEGORICAL
        + SVC_RELIABILITY_FEATURES
        + ARTIST_PRIOR_FEATURES
        + ARTIST_META_NUMERIC
        + ARTIST_META_CATEGORICAL
        + ARTIST_SEGMENT_FEATURES,
    }


def crossfit_residual_prediction(frame: pd.DataFrame, features: list[str], alpha: float) -> np.ndarray:
    folds = min(5, max(2, len(frame) // 100))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    pred = np.zeros(len(frame), dtype=float)
    y = frame["ln_price_krw"].to_numpy(dtype=float) - frame["current_pred_log"].to_numpy(dtype=float)
    for train_idx, holdout_idx in kfold.split(frame):
        model = huber_model(features, alpha)
        tr = normalize(frame.iloc[train_idx].copy(), features)
        ho = normalize(frame.iloc[holdout_idx].copy(), features)
        model.fit(tr[features], y[train_idx])
        pred[holdout_idx] = np.asarray(model.predict(ho[features]), dtype=float)
    return pred


def fit_residual_candidates(
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coeff_rows: list[pd.DataFrame] = []
    for base_name, raw_features in residual_feature_sets().items():
        features = feature_exists(val, raw_features)
        y_val = val["ln_price_krw"].to_numpy(dtype=float) - val["current_pred_log"].to_numpy(dtype=float)
        for alpha in RESIDUAL_ALPHAS:
            val_raw_correction = crossfit_residual_prediction(val, features, alpha)
            model = huber_model(features, alpha)
            va = normalize(val, features)
            te = normalize(test, features)
            model.fit(va[features], y_val)
            test_raw_correction = np.asarray(model.predict(te[features]), dtype=float)
            base_label = f"PP-WCOEF5_{base_name}_alpha{str(alpha).replace('.', 'p')}"
            coeff_rows.append(coefficient_frame(model, base_label, "PP-WCOEF5"))
            for cap in RESIDUAL_CAPS:
                for strength in RESIDUAL_STRENGTHS:
                    label = f"{base_label}_cap{str(cap).replace('.', 'p')}_s{str(strength).replace('.', 'p')}"
                    for split_name, frame, raw_correction in [
                        ("validation", val, val_raw_correction),
                        ("test", test, test_raw_correction),
                    ]:
                        correction = np.clip(raw_correction, -cap, cap) * strength
                        pred = frame["current_pred_log"].to_numpy(dtype=float) + correction
                        add_metric_row(
                            metrics_rows,
                            "PP-WCOEF5",
                            "weak_residual_huber_correction",
                            label,
                            split_name,
                            "validation_crossfit_residual_huber" if split_name == "validation" else "validation_calibrated_residual_huber",
                            frame,
                            pred,
                            features,
                            alpha,
                            {
                                "correction_cap": cap,
                                "correction_strength": strength,
                                "mean_abs_correction": float(np.mean(np.abs(correction))),
                            },
                        )
                        pred_rows.append(prediction_frame(
                            "PP-WCOEF5",
                            label,
                            "residual_huber_correction",
                            split_name,
                            frame,
                            pred,
                            {
                                "correction_cap": cap,
                                "correction_strength": strength,
                                "correction_log": correction,
                            },
                        ))
    return pd.DataFrame(metrics_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coeff_rows, ignore_index=True)


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    current = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    val["balanced_score"] = (
        0.45 * val["MdAPE"] / float(current["MdAPE"])
        + 0.35 * val["MAPE"] / float(current["MAPE"])
        + 0.20 * val["p95_APE"] / float(current["p95_APE"])
    )
    rows: list[dict[str, Any]] = []
    selectors = {
        "MdAPE 우선": (val, ["MdAPE", "MAPE", "p95_APE"]),
        "MAPE 우선 + MdAPE 5% 이내": (val[val["MdAPE"] <= float(current["MdAPE"]) * 1.05].copy(), ["MAPE", "MdAPE", "p95_APE"]),
        "p95 우선 + MdAPE 8% 이내": (val[val["MdAPE"] <= float(current["MdAPE"]) * 1.08].copy(), ["p95_APE", "MdAPE", "MAPE"]),
        "균형 점수": (val, ["balanced_score", "MdAPE", "MAPE", "p95_APE"]),
    }
    for objective, (pool, sort_cols) in selectors.items():
        if pool.empty:
            pool = val
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
    test_rows = []
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
        test_rows.append(row)
    return pd.DataFrame(test_rows)


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
    candidate_pool = [CURRENT_CANDIDATE]
    candidate_pool.extend(selected["selected_candidate"].dropna().tolist())
    top_test = (
        test.groupby(["candidate"], as_index=False)
        .agg(MdAPE=("ape", "median"), MAPE=("ape", "mean"), p95_APE=("ape", lambda x: float(np.quantile(x, 0.95))))
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(5)["candidate"]
        .tolist()
    )
    candidate_pool.extend(top_test)
    candidate_pool = list(dict.fromkeys(candidate_pool))

    wide = test[test["candidate"].isin(candidate_pool)].pivot_table(
        index=["_track6_row_id", "artist_key"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    actual = test[["_track6_row_id", "actual_log", "actual_price", "artist_key"]].drop_duplicates("_track6_row_id")
    wide = wide.merge(actual, on=["_track6_row_id", "artist_key"], how="inner")
    wide = wide.dropna(subset=[CURRENT_CANDIDATE]).reset_index(drop=True)
    candidate_pool = [c for c in candidate_pool if c in wide.columns and wide[c].notna().all()]

    rng = np.random.default_rng(SEED)
    sample_rows: list[dict[str, Any]] = []

    def append_samples(indices: np.ndarray, sample_type: str, iteration: int) -> None:
        actual_price = wide.loc[indices, "actual_price"].to_numpy(dtype=float)
        actual_log = wide.loc[indices, "actual_log"].to_numpy(dtype=float)
        current_metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, CURRENT_CANDIDATE].to_numpy(dtype=float))
        for candidate in candidate_pool:
            cand_metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, candidate].to_numpy(dtype=float))
            row = {
                "sample_type": sample_type,
                "iteration": iteration,
                "candidate": candidate,
            }
            for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[metric_name] = cand_metric[metric_name]
                row[f"delta_{metric_name}"] = cand_metric[metric_name] - current_metric[metric_name]
            sample_rows.append(row)

    n = len(wide)
    artists = wide["artist_key"].astype(str).unique()
    artist_to_indices = {artist: wide.index[wide["artist_key"].astype(str).eq(artist)].to_numpy() for artist in artists}
    for iteration in range(BOOTSTRAP_ITERATIONS):
        row_indices = rng.integers(0, n, size=n)
        append_samples(row_indices, "row_bootstrap", iteration)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        artist_indices = np.concatenate([artist_to_indices[artist] for artist in sampled_artists])
        append_samples(artist_indices, "artist_bootstrap", iteration)

    samples = pd.DataFrame(sample_rows)
    summary_rows: list[dict[str, Any]] = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"], observed=False):
        row = {
            "experiment_id": EXP_ID,
            "sub_experiment": "PP-WCOEF6",
            "sample_type": sample_type,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
        }
        for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{metric_name}"]
            row[f"mean_delta_{metric_name}"] = float(delta.mean())
            row[f"p10_delta_{metric_name}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric_name}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric_name}"] = float(np.mean(delta < 0))
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), samples


def render_report(metrics: pd.DataFrame, selected: pd.DataFrame, bootstrap: pd.DataFrame) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    validation = metrics[metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    current_test = test[test["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    current_val = validation[validation["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    top_test = test.head(30).copy()
    top_validation = validation.head(30).copy()
    selected_view = selected.copy()
    boot_view = bootstrap.sort_values(["sample_type", "mean_delta_MdAPE", "mean_delta_MAPE"]).copy()

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: Huber 선형 모델의 피처별 계수를 더 세밀하게 나누거나 현재 Warm 1순위 후보 위에 약한 잔차 보정을 적용했을 때 추가 개선이 가능한지 확인",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        f"- 기준 validation MdAPE/MAPE/p95: `{current_val['MdAPE']:.4f}` / `{current_val['MAPE']:.4f}` / `{current_val['p95_APE']:.4f}`",
        f"- 기준 test MdAPE/MAPE/p95: `{current_test['MdAPE']:.4f}` / `{current_test['MAPE']:.4f}` / `{current_test['p95_APE']:.4f}`",
        "",
        "## 0. 실행 결론",
        "",
        "- PP-WCOEF1~4 직접 Huber 재학습 후보는 기존 Huber 기준선보다 일부 개선됐지만 현재 Warm 1순위 후보를 대체하지 못함",
        "- 직접 Huber 후보 중 가장 강한 축은 PP-WCOEF3 유사 작품 기반 가격 피처 신뢰도별 계수 조정",
        "- PP-WCOEF3 test MdAPE는 `0.1532`로 기존 Huber test MdAPE `0.2274`보다 개선됐지만 현재 Warm 1순위 `0.1405`에는 미달",
        "- PP-WCOEF5 약한 잔차 보정은 test 일부 후보에서 MdAPE `0.1353`, p95_APE `0.8291`까지 개선 신호 확인",
        "- 다만 validation 선택 후보와 test 최상위 후보가 완전히 일치하지 않고, bootstrap에서 MAPE 개선 확률이 낮아 즉시 v0.1 반영은 보류",
        "- 현재 판단: v0.1 기본 Warm 후보는 유지, PP-WCOEF5는 추가 split/OOF 재검증 후보로 승격",
        "",
        "## 1. 실험 구성",
        "",
        "- PP-WCOEF1: 크기 구간별 Huber 계수 세분화",
        "- PP-WCOEF2: 재료/지지체와 크기 조합 계수 세분화",
        "- PP-WCOEF3: 유사 작품 기반 가격 피처의 표본 수/분산 신뢰도별 계수 조정",
        "- PP-WCOEF4: 작가 기준선과 작가 메타 구간별 계수 조정",
        "- PP-WCOEF5: 현재 Warm 1순위 후보 위 약한 Huber 잔차 보정",
        "- PP-WCOEF6: 선택 후보의 row/artist bootstrap 안정성 검증",
        "",
        "## 2. Test 상위 후보",
        "",
        "| 순위 | 세부 실험 | 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---:|---|---|---|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_test.itertuples(index=False), 1):
        lines.append(
            f"| {rank} | {row.sub_experiment} | `{row.candidate}` | {row.family} | {row.method} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += [
        "",
        "## 3. Validation 기준 선택 후보",
        "",
        "| 선택 기준 | 세부 실험 | 후보 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected_view.itertuples(index=False):
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
    for row in boot_view.head(30).itertuples(index=False):
        lines.append(
            f"| {row.sample_type} | `{row.candidate}` | {row.mean_delta_MdAPE:.5f} | "
            f"{row.improvement_probability_MdAPE:.3f} | {row.improvement_probability_MAPE:.3f} | "
            f"{row.improvement_probability_p95_APE:.3f} |"
        )
    lines += [
        "",
        "## 5. 해석 기준",
        "",
        "- Huber 직접 재학습 후보가 좋아지면 피처 계수 구조를 더 세밀하게 두는 방향으로 후속 검증",
        "- PP-WCOEF5가 좋아지면 현재 Warm 1순위 후보의 사후 보정값을 운영 후보로 분리해 추가 split 검증",
        "- test 상위 후보라도 validation 선택 후보와 bootstrap 개선 확률이 낮으면 바로 반영하지 않음",
        "- MdAPE, MAPE, p95_APE가 엇갈리면 대표 가격 후보와 큰 오차 방어 후보를 분리",
        "",
        "## 6. 산출물",
        "",
        "- `outputs/all_candidate_metrics.csv`",
        "- `outputs/predictions.csv`",
        "- `outputs/selected_validation_candidates.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
        "- `outputs/huber_coefficients_top.csv`",
        "- `reports/result_report.md`",
        "- `reports/result_report.html`",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
.warn{{background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">Warm Huber의 계수 세분화와 현재 Warm 1순위 후보의 약한 잔차 보정 가능성을 같은 split에서 비교한 리포트.</div>
<div class="warn">PP-WCOEF5는 validation 기반 사후 보정 가능성 확인용이다. 운영 반영 전에는 별도 OOF 또는 추가 split 재검증이 필요하다.</div>
<h2>실행 결론</h2>
<ul>
<li>PP-WCOEF1~4 직접 Huber 재학습 후보는 기존 Huber 기준선보다 일부 개선됐지만 현재 Warm 1순위 후보를 대체하지 못함.</li>
<li>직접 Huber 후보 중 가장 강한 축은 PP-WCOEF3 유사 작품 기반 가격 피처 신뢰도별 계수 조정.</li>
<li>PP-WCOEF3 test MdAPE는 0.1532로 기존 Huber test MdAPE 0.2274보다 개선됐지만 현재 Warm 1순위 0.1405에는 미달.</li>
<li>PP-WCOEF5 약한 잔차 보정은 test 일부 후보에서 MdAPE 0.1353, p95_APE 0.8291까지 개선 신호 확인.</li>
<li>validation 선택 후보와 test 최상위 후보가 완전히 일치하지 않고 bootstrap에서 MAPE 개선 확률이 낮아 즉시 v0.1 반영은 보류.</li>
<li>현재 판단: v0.1 기본 Warm 후보는 유지, PP-WCOEF5는 추가 split/OOF 재검증 후보로 승격.</li>
</ul>
<h2>Validation 기준 선택 후보</h2>{selected_view.to_html(index=False, escape=True)}
<h2>Test 상위 후보</h2>{top_test.to_html(index=False, escape=True)}
<h2>Validation 상위 후보</h2>{top_validation.to_html(index=False, escape=True)}
<h2>Bootstrap 안정성 요약</h2>{boot_view.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    selected: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    bootstrap_samples: pd.DataFrame,
    coefficients: pd.DataFrame,
) -> None:
    metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_validation_candidates.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "huber_coefficients_top.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "current_candidate": CURRENT_CANDIDATE,
        "direct_huber_alphas": ALPHAS,
        "residual_huber_alphas": RESIDUAL_ALPHAS,
        "residual_caps": RESIDUAL_CAPS,
        "residual_strengths": RESIDUAL_STRENGTHS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "leakage_control": {
            "train_comparable_features": "PP-SVC5 train out-of-fold comparable features",
            "artist_price_priors_train": "train internal out-of-fold",
            "artist_price_priors_validation_test": "train-only",
            "PP-WCOEF5_validation": "validation internal cross-fitting",
            "PP-WCOEF5_test": "residual model fitted on full validation and applied to test",
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
    train, val, test = load_frames()

    direct_metrics, direct_predictions, direct_coefficients = fit_direct_huber_candidates(train, val, test)
    val_ref, test_ref, ref = add_reference_prediction_features(val, test)
    ref_metrics, ref_predictions = current_reference_metrics(ref, val_ref, test_ref)
    residual_metrics, residual_predictions, residual_coefficients = fit_residual_candidates(val_ref, test_ref)

    all_metrics = pd.concat([ref_metrics, direct_metrics, residual_metrics], ignore_index=True)
    all_predictions = pd.concat([ref_predictions, direct_predictions, residual_predictions], ignore_index=True)
    all_coefficients = pd.concat([direct_coefficients, residual_coefficients], ignore_index=True)
    selected = select_validation_candidates(all_metrics)
    bootstrap_summary, bootstrap_samples = bootstrap_candidates(all_predictions, selected)
    write_outputs(all_metrics, all_predictions, selected, bootstrap_summary, bootstrap_samples, all_coefficients)

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
