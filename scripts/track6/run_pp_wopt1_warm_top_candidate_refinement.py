#!/usr/bin/env python3
"""Run PP-WOPT1 Warm top-candidate refinement experiments.

This experiment starts from the current strong Warm candidate:

    blend_svcnum_ppv8_wsvc_0.70

It tests three refinement axes under the same fixed train/validation/test
split:

1. Huber with artist metadata and leakage-controlled artist price priors.
2. Huber with shrunken comparable-stat features instead of raw multilevel
   comparable columns.
3. Fixed and conditional blending between comparable-stat candidates and the
   PP-V8 error-stabilizing candidate.

The script intentionally keeps all derived train target statistics out-of-fold
for train rows and train-only for validation/test rows.
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
EXP_ID = "PP-WOPT1"
EXP_SLUG = "PP-WOPT1_warm_top_candidate_refinement"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm current top-candidate refinement"
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

SVC_SHRINK_FEATURES = [
    "svc_shrunk_log_price_k5",
    "svc_shrunk_log_price_k15",
    "svc_shrunk_log_price_k30",
    "svc_shrunk_log_unit_area_price_k15",
    "svc_reliability_k15",
    "svc_price_iqr_clipped",
]

ALPHAS = [0.0001, 0.001, 0.01]
FIXED_BLEND_WEIGHTS = np.round(np.arange(0.40, 0.9001, 0.025), 3)


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def read_split(name: str) -> pd.DataFrame:
    path = SPLIT_ROOT / f"track6_{name}.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame["price_krw"] = pd.to_numeric(frame["price_krw"], errors="coerce")
    frame["ln_price_krw"] = pd.to_numeric(frame["ln_price_krw"], errors="coerce")
    return frame.dropna(subset=["price_krw", "ln_price_krw"]).copy()


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
    return train, val, test


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


def add_artist_priors(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_priors = crossfit_artist_priors(train)
    val_priors = apply_artist_priors(train, val)
    test_priors = apply_artist_priors(train, test)
    return (
        train.merge(train_priors, on="_track6_row_id", how="left"),
        val.merge(val_priors, on="_track6_row_id", how="left"),
        test.merge(test_priors, on="_track6_row_id", how="left"),
    )


def add_svc_shrink_features(frame: pd.DataFrame, global_log_price: float, global_log_unit_area: float) -> pd.DataFrame:
    out = frame.copy()
    n = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
    svc_price = pd.to_numeric(out["svc_group_log_price_median"], errors="coerce").fillna(global_log_price)
    svc_iqr = pd.to_numeric(out["svc_group_log_price_iqr"], errors="coerce").fillna(3.0).clip(0.0, 3.0)
    unit_area = pd.to_numeric(out["svc_group_log_unit_area_median"], errors="coerce").fillna(global_log_unit_area)
    area = np.clip(pd.to_numeric(out["area_cm2"], errors="coerce").fillna(1.0), 1.0, None)
    unit_price_pred = unit_area + np.log(area)
    for k in [5, 15, 30]:
        n_weight = n / (n + float(k))
        iqr_weight = np.exp(-0.5 * svc_iqr)
        weight = (n_weight * iqr_weight).clip(0.0, 1.0)
        out[f"svc_shrunk_log_price_k{k}"] = weight * svc_price + (1.0 - weight) * global_log_price
        if k == 15:
            out[f"svc_shrunk_log_unit_area_price_k{k}"] = weight * unit_price_pred + (1.0 - weight) * global_log_price
            out[f"svc_reliability_k{k}"] = weight
    out["svc_price_iqr_clipped"] = svc_iqr
    return out


def add_shrink_features(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    global_log_price = float(pd.to_numeric(train["ln_price_krw"], errors="coerce").median())
    global_log_unit_area = float(source_unit_area(train).median())
    return (
        add_svc_shrink_features(train, global_log_price, global_log_unit_area),
        add_svc_shrink_features(val, global_log_price, global_log_unit_area),
        add_svc_shrink_features(test, global_log_price, global_log_unit_area),
    )


def feature_exists(frame: pd.DataFrame, features: list[str]) -> list[str]:
    return [feature for feature in features if feature in frame.columns]


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_all = set(BASE_NUMERIC + ARTIST_META_NUMERIC + SVC_NUMERIC + ARTIST_PRIOR_FEATURES + SVC_SHRINK_FEATURES)
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
        transformers.append(("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric))
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


def candidate_label(base: str, alpha: float) -> str:
    return f"{base}_alpha{str(alpha).replace('.', 'p')}"


def coefficient_frame(model: Pipeline, candidate: str) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    try:
        names = prep.get_feature_names_out()
    except Exception:
        names = np.array([f"feature_{i}" for i in range(len(reg.coef_))])
    coef = np.asarray(reg.coef_, dtype=float)
    frame = pd.DataFrame({
        "candidate": candidate,
        "encoded_feature": names,
        "coefficient": coef,
        "abs_coefficient": np.abs(coef),
    })
    return frame.sort_values("abs_coefficient", ascending=False).head(200)


def fit_huber_candidates(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_sets = {
        "huber_base_artifact": BASE_FEATURES,
        "huber_artist_meta_basic": BASE_FEATURES + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL,
        "huber_artist_prior": BASE_FEATURES + ARTIST_PRIOR_FEATURES,
        "huber_artist_meta_prior": BASE_FEATURES + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL + ARTIST_PRIOR_FEATURES,
        "huber_svc_shrink": BASE_FEATURES + SVC_SHRINK_FEATURES,
        "huber_artist_meta_prior_svc_shrink": (
            BASE_FEATURES + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL + ARTIST_PRIOR_FEATURES + SVC_SHRINK_FEATURES
        ),
        "huber_artist_meta_prior_svc_fallback": (
            BASE_FEATURES + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL + ARTIST_PRIOR_FEATURES + SVC_NUMERIC + SVC_CATEGORICAL
        ),
        "huber_no_artistkey_meta_prior_svc_shrink": (
            [f for f in BASE_FEATURES if f != "artist_key"]
            + ARTIST_META_NUMERIC
            + ARTIST_META_CATEGORICAL
            + ARTIST_PRIOR_FEATURES
            + SVC_SHRINK_FEATURES
        ),
    }
    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coeff_rows: list[pd.DataFrame] = []
    for base_name, raw_features in feature_sets.items():
        features = feature_exists(train, list(dict.fromkeys(raw_features)))
        for alpha in ALPHAS:
            label = candidate_label(base_name, alpha)
            model = huber_model(features, alpha)
            tr = normalize(train, features)
            va = normalize(val, features)
            te = normalize(test, features)
            model.fit(tr[features], pd.to_numeric(tr["ln_price_krw"], errors="coerce").to_numpy(dtype=float))
            coeff_rows.append(coefficient_frame(model, label))
            for split_name, frame, normalized in [("validation", val, va), ("test", test, te)]:
                pred = np.asarray(model.predict(normalized[features]), dtype=float)
                metrics_rows.append({
                    "experiment_id": EXP_ID,
                    "family": "huber_feature_model",
                    "candidate": label,
                    "split": split_name,
                    "method": "huber_retrained",
                    "alpha": alpha,
                    "n_features": len(features),
                    "features": ", ".join(features),
                    **metric_values(frame, pred),
                })
                pred_rows.append(make_prediction_frame(label, "huber_retrained", split_name, frame, pred))
    return pd.DataFrame(metrics_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coeff_rows, ignore_index=True)


def make_prediction_frame(candidate: str, method: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "method": method,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_group_level": frame.get("svc_group_level", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_coverage_tier": frame.get("svc_coverage_tier", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_group_n": pd.to_numeric(frame.get("svc_group_n", pd.Series([np.nan] * len(frame))), errors="coerce").to_numpy(),
    })
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def load_reference_predictions() -> pd.DataFrame:
    pred = pd.read_csv(SVC5_PREDICTIONS, low_memory=False)
    keep = {CURRENT_CANDIDATE, PPV8_CANDIDATE, FALLBACK_CANDIDATE}
    pred = pred[pred["candidate"].isin(keep) & pred["split"].isin(["validation", "test"])].copy()
    return pred


def reference_wide(ref: pd.DataFrame, split: str) -> pd.DataFrame:
    frame = ref[ref["split"].eq(split)].copy()
    base_cols = [
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
    base = frame[base_cols].drop_duplicates(["split", "_track6_row_id"])
    wide = frame.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    return base.merge(wide, on=["split", "_track6_row_id"], how="inner")


def blend_predictions(frame: pd.DataFrame, left: str, right: str, weight: float) -> np.ndarray:
    return weight * frame[left].to_numpy(dtype=float) + (1.0 - weight) * frame[right].to_numpy(dtype=float)


def dynamic_weight(frame: pd.DataFrame, high_weight: float, mid_weight: float, low_weight: float, min_n: int, max_iqr: float, disagree_cut: float) -> np.ndarray:
    n = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    iqr_proxy = np.abs(
        frame[FALLBACK_CANDIDATE].to_numpy(dtype=float) - frame[PPV8_CANDIDATE].to_numpy(dtype=float)
    )
    strong = (n >= min_n) & (iqr_proxy <= max_iqr)
    weak = (n < min_n) | (iqr_proxy > disagree_cut)
    weights = np.full(len(frame), mid_weight, dtype=float)
    weights[strong] = high_weight
    weights[weak] = low_weight
    return weights


def evaluate_blend_candidates(
    ref: pd.DataFrame,
    huber_preds: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    val = reference_wide(ref, "validation")
    test = reference_wide(ref, "test")

    # Add best Huber candidates to the wide reference frame so they can also be
    # tested as an alternative left-side component.
    huber_metric = (
        huber_preds[huber_preds["split"].eq("validation")]
        .groupby("candidate", as_index=False)
        .agg(MdAPE=("ape", "median"), MAPE=("ape", "mean"))
        .sort_values(["MAPE", "MdAPE"])
    )
    left_candidates = [FALLBACK_CANDIDATE]
    left_candidates.extend(huber_metric.head(4)["candidate"].tolist())
    for candidate in left_candidates:
        if candidate == FALLBACK_CANDIDATE:
            continue
        for split_name, frame in [("validation", val), ("test", test)]:
            part = huber_preds[(huber_preds["split"].eq(split_name)) & (huber_preds["candidate"].eq(candidate))]
            pred_map = part.set_index("_track6_row_id")["pred_log"]
            frame[candidate] = frame["_track6_row_id"].map(pred_map).to_numpy(dtype=float)

    metrics_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    for split_name, frame in [("validation", val), ("test", test)]:
        actual_frame = pd.DataFrame({
            "_track6_row_id": frame["_track6_row_id"],
            "ln_price_krw": frame["actual_log"],
            "price_krw": frame["actual_price"],
            "artist_key": frame["artist_key"],
            "artist_name_ko": frame["artist_name_ko"],
            "svc_group_level": frame["svc_group_level"],
            "svc_coverage_tier": frame["svc_coverage_tier"],
            "svc_group_n": frame["svc_group_n"],
        })
        for candidate in [CURRENT_CANDIDATE, PPV8_CANDIDATE, FALLBACK_CANDIDATE]:
            pred = frame[candidate].to_numpy(dtype=float)
            metrics_rows.append({
                "experiment_id": EXP_ID,
                "family": "reference",
                "candidate": candidate,
                "split": split_name,
                "method": "reference",
                "alpha": np.nan,
                "n_features": 0,
                "features": "reference_prediction",
                **metric_values(actual_frame, pred),
            })
            pred_rows.append(make_prediction_frame(candidate, "reference", split_name, actual_frame, pred))

        for left in left_candidates:
            for weight in FIXED_BLEND_WEIGHTS:
                label = f"blend_{left}_ppv8_wleft_{weight:.3f}"
                pred = blend_predictions(frame, left, PPV8_CANDIDATE, float(weight))
                metrics_rows.append({
                    "experiment_id": EXP_ID,
                    "family": "fixed_blend",
                    "candidate": label,
                    "split": split_name,
                    "method": "fixed_weight_blend",
                    "alpha": np.nan,
                    "n_features": 0,
                    "features": f"{weight:.3f} * {left} + {1.0 - float(weight):.3f} * {PPV8_CANDIDATE}",
                    **metric_values(actual_frame, pred),
                })
                if weight in [0.5, 0.575, 0.6, 0.7, 0.75]:
                    pred_rows.append(make_prediction_frame(label, "fixed_weight_blend", split_name, actual_frame, pred))

        for min_n in [5, 15, 30, 50]:
            for max_iqr in [0.35, 0.50, 0.70]:
                for disagree_cut in [0.50, 0.75, 1.00]:
                    for high_weight, mid_weight, low_weight in [(0.75, 0.60, 0.45), (0.70, 0.575, 0.45), (0.65, 0.55, 0.40)]:
                        weights = dynamic_weight(frame, high_weight, mid_weight, low_weight, min_n, max_iqr, disagree_cut)
                        pred = weights * frame[FALLBACK_CANDIDATE].to_numpy(dtype=float) + (
                            1.0 - weights
                        ) * frame[PPV8_CANDIDATE].to_numpy(dtype=float)
                        label = (
                            f"dyn_fallback_ppv8_n{min_n}_iqr{max_iqr:.2f}_d{disagree_cut:.2f}"
                            f"_w{high_weight:.2f}_{mid_weight:.3f}_{low_weight:.2f}"
                        )
                        metrics_rows.append({
                            "experiment_id": EXP_ID,
                            "family": "conditional_blend",
                            "candidate": label,
                            "split": split_name,
                            "method": "conditional_weight_blend",
                            "alpha": np.nan,
                            "n_features": 0,
                            "features": (
                                f"fallback/ppv8 dynamic weights by svc_group_n, "
                                f"fallback-ppv8 disagreement; mean_weight={float(np.mean(weights)):.4f}"
                            ),
                            **metric_values(actual_frame, pred),
                        })
    metrics = pd.DataFrame(metrics_rows)
    predictions = pd.concat(pred_rows, ignore_index=True)

    selected = select_validation_candidates(metrics)
    return metrics, predictions, selected


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    current = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    rows: list[dict[str, Any]] = []
    objectives = {
        "mdape_primary": ["MdAPE", "MAPE", "p95_APE"],
        "mape_current_mdape_guard": ["MAPE", "MdAPE", "p95_APE"],
        "balanced_current": ["balanced_score", "MdAPE", "MAPE", "p95_APE"],
    }
    val["balanced_score"] = (
        0.40 * val["MdAPE"] / float(current["MdAPE"])
        + 0.40 * val["MAPE"] / float(current["MAPE"])
        + 0.20 * val["p95_APE"] / float(current["p95_APE"])
    )
    for objective, sort_cols in objectives.items():
        pool = val.copy()
        if objective == "mape_current_mdape_guard":
            pool = pool[pool["MdAPE"] <= float(current["MdAPE"]) + 1e-12].copy()
            if pool.empty:
                pool = val.copy()
        selected = pool.sort_values(sort_cols).iloc[0]
        rows.append({
            "objective": objective,
            "selected_candidate": selected["candidate"],
            "selected_family": selected["family"],
            "selected_method": selected["method"],
            "validation_MdAPE": float(selected["MdAPE"]),
            "validation_MAPE": float(selected["MAPE"]),
            "validation_p95_APE": float(selected["p95_APE"]),
        })
    return pd.DataFrame(rows)


def attach_test_metrics(selected: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    rows: list[dict[str, Any]] = []
    for row in selected.to_dict("records"):
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
        rows.append(row)
    return pd.DataFrame(rows)


def render_report(all_metrics: pd.DataFrame, selected: pd.DataFrame) -> tuple[str, str]:
    test = all_metrics[all_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    val = all_metrics[all_metrics["split"].eq("validation")].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()
    current_test = test[test["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 현재 Warm 1순위 후보 이후 개선 여지를 같은 기준으로 검증",
        "- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`",
        f"- 기준 test MdAPE: `{current_test['MdAPE']:.4f}`",
        f"- 기준 test MAPE: `{current_test['MAPE']:.4f}`",
        f"- 기준 test p95_APE: `{current_test['p95_APE']:.4f}`",
        "",
        "## 1. 실험 축",
        "",
        "- Huber + 작가 메타/작가 가격 기준선",
        "- Huber + 신뢰도 보정 유사 작품 기반 가격 피처",
        "- 유사 작품 기반 가격 피처와 PP-V8 오차 안정화 후보의 고정 비율 재탐색",
        "- 표본 수와 후보 간 차이에 따른 조건별 결합 비율",
        "",
        "## 2. Test 상위 후보",
        "",
        "| 순위 | 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---:|---|---|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(test.head(25).itertuples(), 1):
        lines.append(
            f"| {rank} | `{row.candidate}` | {row.family} | {row.method} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += [
        "",
        "## 3. Validation 선택 후보와 Test 확인",
        "",
        "| 선택 기준 | 선택 후보 | 계열 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected.itertuples():
        lines.append(
            f"| {row.objective} | `{row.selected_candidate}` | {row.selected_family} | "
            f"{row.validation_MdAPE:.4f} | {row.validation_MAPE:.4f} | {row.validation_p95_APE:.4f} | "
            f"{row.test_MdAPE:.4f} | {row.test_MAPE:.4f} | {row.test_p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 4. Validation MAPE 상위 후보",
        "",
        "| 후보 | 계열 | 방식 | MdAPE | MAPE | p95_APE |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in val.head(20).itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.family} | {row.method} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 5. 해석",
        "",
        "- test 상위 후보만으로 바로 채택하지 않음",
        "- validation에서 선택된 후보가 test에서도 기준 후보를 함께 개선하는지 우선 확인",
        "- Huber 작가 메타 후보가 개선되면 모델 내부 피처 고도화 방향으로 승격",
        "- 고정 또는 조건별 결합 후보가 개선되면 PP-SVC6처럼 반복 holdout 검증으로 승격",
        "- MdAPE, MAPE, p95가 서로 엇갈리면 단일 점 예측 후보가 아니라 큰 오차 방어 보조 후보로 분리",
        "",
        "## 6. 산출물",
        "",
        "- `outputs/all_candidate_metrics.csv`",
        "- `outputs/huber_candidate_predictions.csv`",
        "- `outputs/blend_candidate_predictions.csv`",
        "- `outputs/selected_validation_candidates.csv`",
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
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">Warm 현 1순위 이후 개선 후보를 Huber 피처, 고정 결합, 조건별 결합으로 나눠 비교한 리포트.</div>
<h2>Selected Candidates</h2>{selected.to_html(index=False, escape=True)}
<h2>Test Metrics Top</h2>{test.head(60).to_html(index=False, escape=True)}
<h2>Validation Metrics Top</h2>{val.head(60).to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    all_metrics: pd.DataFrame,
    huber_predictions: pd.DataFrame,
    blend_predictions_df: pd.DataFrame,
    selected: pd.DataFrame,
    coefficients: pd.DataFrame,
) -> None:
    all_metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    huber_predictions.to_csv(EXP_DIR / "outputs" / "huber_candidate_predictions.csv", index=False)
    blend_predictions_df.to_csv(EXP_DIR / "outputs" / "blend_candidate_predictions.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_validation_candidates.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "huber_coefficients_top.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "current_candidate": CURRENT_CANDIDATE,
        "ppv8_candidate": PPV8_CANDIDATE,
        "fallback_candidate": FALLBACK_CANDIDATE,
        "alphas": ALPHAS,
        "fixed_blend_weights": FIXED_BLEND_WEIGHTS.tolist(),
        "leakage_control": {
            "artist_price_priors_train": "5-fold out-of-fold",
            "artist_price_priors_validation_test": "train-only",
            "comparable_features": "reused from PP-SVC5; train features are out-of-fold",
            "blend_selection": "validation only",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(all_metrics, selected)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    train, val, test = load_frames()
    train, val, test = add_artist_priors(train, val, test)
    train, val, test = add_shrink_features(train, val, test)

    huber_metrics, huber_predictions, coefficients = fit_huber_candidates(train, val, test)
    ref = load_reference_predictions()
    blend_metrics, blend_predictions_df, selected = evaluate_blend_candidates(ref, huber_predictions)
    all_metrics = pd.concat([huber_metrics, blend_metrics], ignore_index=True)
    selected = attach_test_metrics(selected, all_metrics)
    write_outputs(all_metrics, huber_predictions, blend_predictions_df, selected, coefficients)

    test = all_metrics[all_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(8)
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "top_test_candidates": test[["candidate", "family", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict("records"),
        "selected_validation_candidates": selected.to_dict("records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
