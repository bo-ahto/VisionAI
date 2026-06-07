#!/usr/bin/env python3
"""Run PP-AMW5 Warm artist meta/external coefficient correction experiment.

Hypothesis:
    The current strongest Warm candidate already captures most artist/size
    signal. However, remaining residuals may still depend on artist metadata
    such as birth year, work volume, for-sale count, exhibition count, and
    gallery tier. This experiment keeps the current Warm candidate fixed and
    learns only a small residual correction from those signals.

Important leakage rule:
    The correction is fitted on validation data only. Validation metrics use
    artist-group cross fitting, so a validation row is not corrected by a
    model fitted on itself. Test metrics are produced by fitting the correction
    on the full validation set and applying it once to the fixed test set.
"""
from __future__ import annotations

import html
import json
import os
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
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


os.environ.setdefault("MPLCONFIGDIR", "/private/tmp")
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values.*")

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_z_warm_coldstyle_extension_experiments as ppz  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-AMW5"
EXP_SLUG = "PP-AMW5_warm_artist_meta_external_coefficient_correction"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 작가 메타/전시·갤러리 계수형 잔차 보정"
SEED = 20260607
CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE

ARTIST_META_NUMERIC = [
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_works_log",
    "artist_works_count_train",
    "artist_meta_total_works_log",
    "artist_meta_for_sale_works_log",
    "artist_meta_followers_log",
    "artist_meta_available_count",
    "artist_meta_completeness_score",
]

ARTIST_META_CATEGORICAL = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
    "artist_birth_generation_bin",
    "artist_meta_total_works_bin",
    "artist_meta_for_sale_works_bin",
    "artist_meta_followers_bin",
]

EXTERNAL_NUMERIC = [
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
    "artist_exhibition_total_count",
    "artist_exhibition_available_count",
    "artist_exhibition_solo_count_log",
    "artist_exhibition_group_count_log",
    "artist_exhibition_fair_count_log",
    "artist_exhibition_total_count_log",
    "gallery_tier_raw_numeric",
    "gallery_tier_raw_available_flag",
    "gallery_tier_validated_score",
    "gallery_tier_validated_available_flag",
    "gallery_tier_any_available_flag",
    "gallery_city_count",
    "gallery_city_count_log",
    "exhibition_total_x_log_area",
    "exhibition_total_x_followers_log",
    "gallery_raw_tier_x_followers_log",
    "gallery_validated_x_followers_log",
    "gallery_tier_x_exhibition_total_log",
]

EXTERNAL_CATEGORICAL = [
    "gallery_tier_raw_bucket",
    "gallery_tier_validated",
    "gallery_ref_type",
    "gallery_audit_status",
    "gallery_feature_source",
    "exhibition_total_bin",
    "gallery_exhibition_bucket",
    "exhibition_size_bucket",
]

RESIDUAL_CONTEXT = [
    "current_pred_log",
    "ppv8_pred_log",
    "fallback_pred_log",
    "current_ppv8_gap_abs",
    "current_fallback_gap_abs",
    "pred_log_bin",
]

BASE_CONTEXT = [
    "log_area",
    "aspect_ratio",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "size_bin",
    "svc_group_log_price_median",
    "svc_group_log_price_iqr",
    "svc_group_n_log",
    "svc_reliability_bin",
]

NUMERIC_FEATURES = set(
    ARTIST_META_NUMERIC
    + EXTERNAL_NUMERIC
    + ["current_pred_log", "ppv8_pred_log", "fallback_pred_log", "current_ppv8_gap_abs", "current_fallback_gap_abs"]
    + ["log_area", "aspect_ratio", "svc_group_log_price_median", "svc_group_log_price_iqr", "svc_group_n_log"]
)

ALPHAS = [0.001, 0.01]
EPSILONS = [1.20, 1.35]
CAPS = [0.03, 0.05, 0.08]
STRENGTHS = [0.25, 0.50]
SEGMENT_CAPS = [0.03, 0.05]
SEGMENT_STRENGTHS = [0.50, 1.00]
MIN_SEGMENT_N = [20, 40]
SHRINK_K = 30.0


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def clean_label(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def qcut_labels(values: pd.Series, labels: list[str]) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    non_null = numeric.dropna()
    if non_null.nunique() < 3:
        return pd.Series(np.where(numeric.notna(), labels[0], "__MISSING__"), index=values.index).astype("string")
    try:
        cut = pd.qcut(numeric, q=min(len(labels), non_null.nunique()), labels=labels[: min(len(labels), non_null.nunique())], duplicates="drop")
        return cut.astype("string").fillna("__MISSING__")
    except ValueError:
        return pd.Series(np.where(numeric.notna(), labels[0], "__MISSING__"), index=values.index).astype("string")


def birth_generation(values: pd.Series) -> pd.Series:
    year = pd.to_numeric(values, errors="coerce")
    bins = [-np.inf, 1949, 1969, 1979, 1989, np.inf]
    labels = ["pre_1950", "1950_1969", "1970_1979", "1980_1989", "post_1990"]
    return pd.cut(year, bins=bins, labels=labels, include_lowest=True).astype("string").fillna("__MISSING__")


def exhibition_bin(values: pd.Series) -> pd.Series:
    count = pd.to_numeric(values, errors="coerce")
    bins = [-np.inf, 0, 3, 8, np.inf]
    labels = ["none", "low", "mid", "high"]
    return pd.cut(count, bins=bins, labels=labels, include_lowest=True).astype("string").fillna("__MISSING__")


def add_external_features(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ext = ppz.warm_external_row_map()
    out_frames: list[pd.DataFrame] = []
    for frame in [val, test]:
        out = frame.merge(ext, on="_track6_row_id", how="left")
        out_frames.append(out)
    return out_frames[0], out_frames[1]


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()

    for col in ["artist_meta_total_works", "artist_meta_for_sale_works", "artist_meta_followers"]:
        out[f"{col}_log"] = np.log1p(pd.to_numeric(out.get(col), errors="coerce").clip(lower=0).fillna(0.0))

    meta_cols = [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
    ]
    out["artist_meta_available_count"] = sum(pd.to_numeric(out.get(c), errors="coerce").notna().astype(float) for c in meta_cols)
    out["artist_meta_completeness_score"] = out["artist_meta_available_count"] / float(len(meta_cols))

    out["artist_birth_generation_bin"] = birth_generation(out.get("artist_meta_birth_year", pd.Series(np.nan, index=out.index)))
    out["artist_meta_total_works_bin"] = qcut_labels(out.get("artist_meta_total_works", pd.Series(np.nan, index=out.index)), ["low", "mid", "high"])
    out["artist_meta_for_sale_works_bin"] = qcut_labels(out.get("artist_meta_for_sale_works", pd.Series(np.nan, index=out.index)), ["low", "mid", "high"])
    out["artist_meta_followers_bin"] = qcut_labels(out.get("artist_meta_followers", pd.Series(np.nan, index=out.index)), ["low", "mid", "high"])

    out["artist_exhibition_total_count"] = pd.to_numeric(out.get("artist_exhibition_total_count"), errors="coerce")
    out["artist_exhibition_total_count_log"] = np.log1p(out["artist_exhibition_total_count"].clip(lower=0).fillna(0.0))
    out["exhibition_total_bin"] = exhibition_bin(out["artist_exhibition_total_count"])

    followers_log = pd.to_numeric(out.get("artist_meta_followers_log"), errors="coerce").fillna(0.0)
    total_log = pd.to_numeric(out.get("artist_exhibition_total_count_log"), errors="coerce").fillna(0.0)
    log_area = pd.to_numeric(out.get("log_area"), errors="coerce").fillna(0.0)
    gallery_raw = pd.to_numeric(out.get("gallery_tier_raw_numeric"), errors="coerce").fillna(0.0)
    gallery_validated = pd.to_numeric(out.get("gallery_tier_validated_score"), errors="coerce").fillna(0.0)
    out["exhibition_total_x_log_area"] = total_log * log_area
    out["exhibition_total_x_followers_log"] = total_log * followers_log
    out["gallery_raw_tier_x_followers_log"] = gallery_raw * followers_log
    out["gallery_validated_x_followers_log"] = gallery_validated * followers_log
    out["gallery_tier_x_exhibition_total_log"] = gallery_raw * total_log

    size = clean_label(out.get("size_bin", pd.Series("__MISSING__", index=out.index)))
    out["exhibition_size_bucket"] = size.astype(str) + "__" + out["exhibition_total_bin"].astype(str)
    out["gallery_exhibition_bucket"] = clean_label(out.get("gallery_feature_source", pd.Series("__MISSING__", index=out.index))).astype(str) + "__" + out["exhibition_total_bin"].astype(str)
    out["birth_x_gallery_bucket"] = out["artist_birth_generation_bin"].astype(str) + "__" + clean_label(out.get("gallery_tier_raw_bucket", pd.Series("__MISSING__", index=out.index))).astype(str)
    out["works_x_exhibition_bucket"] = out["artist_meta_total_works_bin"].astype(str) + "__" + out["exhibition_total_bin"].astype(str)

    for col in ARTIST_META_CATEGORICAL + EXTERNAL_CATEGORICAL + ["birth_x_gallery_bucket", "works_x_exhibition_bucket", "pred_log_bin", "svc_reliability_bin", "medium_category", "support_category", "medium_support_bucket", "size_bin"]:
        if col not in out.columns:
            out[col] = "__MISSING__"
        out[col] = clean_label(out[col])

    return out


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    train, val, test = wcoef.load_frames()
    del train
    val, test, _ref = wcoef.add_reference_prediction_features(val, test)
    val, test = add_external_features(val, test)
    return engineer_features(val), engineer_features(test)


def feature_exists(frame: pd.DataFrame, features: list[str]) -> list[str]:
    return [feature for feature in dict.fromkeys(features) if feature in frame.columns]


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [feature for feature in features if feature in NUMERIC_FEATURES]
    categorical = [feature for feature in features if feature not in numeric]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = clean_label(out[col])
    return out


def residual_model(features: list[str], alpha: float, epsilon: float) -> Pipeline:
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
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=8, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=8)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=5000)),
    ])


def grouped_folds(frame: pd.DataFrame) -> list[tuple[np.ndarray, np.ndarray]]:
    groups = clean_label(frame.get("artist_key", pd.Series("__MISSING__", index=frame.index))).to_numpy()
    if pd.Series(groups).nunique() >= 5:
        return list(GroupKFold(n_splits=5).split(frame, groups=groups))
    return list(KFold(n_splits=5, shuffle=True, random_state=SEED).split(frame))


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return wcoef.metric_values(frame, pred_log)


def prediction_frame(candidate: str, method: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, correction: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "method": method,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "baseline_pred_log": frame["current_pred_log"].to_numpy(dtype=float),
        "correction_log": correction,
        "pred_log": pred_log,
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
    })
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["baseline_pred_price"] = np.clip(np.exp(out["baseline_pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    out["baseline_ape"] = np.abs(out["baseline_pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def coefficient_frame(model: Pipeline, candidate: str, feature_group: str) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    try:
        names = prep.get_feature_names_out()
    except Exception:
        names = np.array([f"feature_{i}" for i in range(len(reg.coef_))])
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "feature_group": feature_group,
        "encoded_feature": names,
        "coefficient": np.asarray(reg.coef_, dtype=float),
    })
    out["abs_coefficient"] = out["coefficient"].abs()
    return out.sort_values("abs_coefficient", ascending=False).head(120)


def feature_sets() -> dict[str, list[str]]:
    return {
        "artist_meta_core": RESIDUAL_CONTEXT + BASE_CONTEXT + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL,
        "external_gallery_exhibition": RESIDUAL_CONTEXT + BASE_CONTEXT + EXTERNAL_NUMERIC + EXTERNAL_CATEGORICAL,
        "artist_meta_external": RESIDUAL_CONTEXT + BASE_CONTEXT + ARTIST_META_NUMERIC + ARTIST_META_CATEGORICAL + EXTERNAL_NUMERIC + EXTERNAL_CATEGORICAL,
        "artist_meta_external_interactions": RESIDUAL_CONTEXT
        + BASE_CONTEXT
        + ARTIST_META_NUMERIC
        + ARTIST_META_CATEGORICAL
        + EXTERNAL_NUMERIC
        + EXTERNAL_CATEGORICAL
        + ["birth_x_gallery_bucket", "works_x_exhibition_bucket"],
    }


def add_metric_row(
    rows: list[dict[str, Any]],
    candidate: str,
    family: str,
    feature_group: str,
    method: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray,
    features: list[str] | str,
    extra: dict[str, Any] | None = None,
) -> None:
    baseline = metric(frame, frame["current_pred_log"].to_numpy(dtype=float))
    current = metric(frame, pred_log)
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "family": family,
        "feature_group": feature_group,
        "method": method,
        "split": split,
        "n_features": 0 if isinstance(features, str) else len(features),
        "features": features if isinstance(features, str) else ", ".join(features),
        "mean_abs_correction": float(np.mean(np.abs(correction))),
        "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
        **current,
    }
    for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]:
        row[f"delta_{key}"] = current[key] - baseline[key]
    if extra:
        row.update(extra)
    rows.append(row)


def run_huber_residual_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    coeffs: list[pd.DataFrame] = []
    y_val = val["ln_price_krw"].to_numpy(dtype=float) - val["current_pred_log"].to_numpy(dtype=float)
    folds = grouped_folds(val)

    for group_name, raw_features in feature_sets().items():
        features = feature_exists(val, raw_features)
        for alpha in ALPHAS:
            for epsilon in EPSILONS:
                oof_raw = np.zeros(len(val), dtype=float)
                for train_idx, holdout_idx in folds:
                    model = residual_model(features, alpha, epsilon)
                    tr = normalize(val.iloc[train_idx].copy(), features)
                    ho = normalize(val.iloc[holdout_idx].copy(), features)
                    model.fit(tr[features], y_val[train_idx])
                    oof_raw[holdout_idx] = np.asarray(model.predict(ho[features]), dtype=float)

                model = residual_model(features, alpha, epsilon)
                va = normalize(val, features)
                te = normalize(test, features)
                model.fit(va[features], y_val)
                test_raw = np.asarray(model.predict(te[features]), dtype=float)
                base_label = f"{EXP_ID}_huber_{group_name}_eps{epsilon:.2f}_alpha{alpha}".replace(".", "p")
                coeffs.append(coefficient_frame(model, base_label, group_name))

                for cap in CAPS:
                    for strength in STRENGTHS:
                        label = f"{base_label}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p")
                        for split_name, frame, raw in [("validation", val, oof_raw), ("test", test, test_raw)]:
                            correction = np.clip(raw, -cap, cap) * strength
                            pred_log = frame["current_pred_log"].to_numpy(dtype=float) + correction
                            add_metric_row(
                                rows,
                                label,
                                "huber_residual_coefficient_correction",
                                group_name,
                                "validation_artist_group_crossfit" if split_name == "validation" else "validation_fit_test_apply",
                                split_name,
                                frame,
                                pred_log,
                                correction,
                                features,
                                {
                                    "alpha": alpha,
                                    "epsilon": epsilon,
                                    "correction_cap": cap,
                                    "correction_strength": strength,
                                },
                            )
                            preds.append(prediction_frame(label, "huber_residual_correction", split_name, frame, pred_log, correction))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True), pd.concat(coeffs, ignore_index=True)


def segment_correction(train: pd.DataFrame, holdout: pd.DataFrame, segment: str, cap: float, strength: float, min_n: int) -> np.ndarray:
    residual = train["ln_price_krw"].to_numpy(dtype=float) - train["current_pred_log"].to_numpy(dtype=float)
    tmp = pd.DataFrame({"segment": clean_label(train[segment]), "residual": residual})
    global_median = float(np.median(residual))
    stats = tmp.groupby("segment", observed=False).agg(median=("residual", "median"), n=("residual", "size")).reset_index()
    stats["shrink"] = stats["n"] / (stats["n"] + SHRINK_K)
    stats["value"] = np.where(
        stats["n"] >= min_n,
        stats["median"] * stats["shrink"] + global_median * (1.0 - stats["shrink"]),
        global_median,
    )
    mapping = dict(zip(stats["segment"].astype(str), stats["value"].astype(float)))
    raw = clean_label(holdout[segment]).astype(str).map(mapping).fillna(global_median).to_numpy(dtype=float)
    return np.clip(raw, -cap, cap) * strength


def run_segment_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    segments = [
        "artist_birth_generation_bin",
        "artist_meta_total_works_bin",
        "artist_meta_for_sale_works_bin",
        "artist_meta_followers_bin",
        "exhibition_total_bin",
        "gallery_tier_raw_bucket",
        "gallery_feature_source",
        "birth_x_gallery_bucket",
        "works_x_exhibition_bucket",
    ]
    segments = feature_exists(val, segments)
    folds = grouped_folds(val)
    for segment in segments:
        for min_n in MIN_SEGMENT_N:
            for cap in SEGMENT_CAPS:
                for strength in SEGMENT_STRENGTHS:
                    label = f"{EXP_ID}_segment_{segment}_min{min_n}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p")
                    val_corr = np.zeros(len(val), dtype=float)
                    for train_idx, holdout_idx in folds:
                        val_corr[holdout_idx] = segment_correction(
                            val.iloc[train_idx].copy(),
                            val.iloc[holdout_idx].copy(),
                            segment,
                            cap,
                            strength,
                            min_n,
                        )
                    test_corr = segment_correction(val, test, segment, cap, strength, min_n)
                    for split_name, frame, correction in [("validation", val, val_corr), ("test", test, test_corr)]:
                        pred_log = frame["current_pred_log"].to_numpy(dtype=float) + correction
                        add_metric_row(
                            rows,
                            label,
                            "segment_median_residual_correction",
                            segment,
                            "validation_artist_group_crossfit" if split_name == "validation" else "validation_segment_map_test_apply",
                            split_name,
                            frame,
                            pred_log,
                            correction,
                            segment,
                            {
                                "segment": segment,
                                "min_segment_n": min_n,
                                "correction_cap": cap,
                                "correction_strength": strength,
                            },
                        )
                        preds.append(prediction_frame(label, "segment_residual_correction", split_name, frame, pred_log, correction))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def coverage_table(val: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
        "artist_exhibition_total_count",
        "gallery_tier_raw_numeric",
        "gallery_tier_validated_score",
        "gallery_city_count",
    ]
    rows = []
    for split, frame in [("validation", val), ("test", test)]:
        for col in cols:
            if col not in frame.columns:
                continue
            rows.append({
                "experiment_id": EXP_ID,
                "split": split,
                "feature": col,
                "coverage": float(frame[col].notna().mean()),
                "non_null_n": int(frame[col].notna().sum()),
                "n": int(len(frame)),
            })
    return pd.DataFrame(rows)


def selected_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    baseline = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    val["balanced_score"] = (
        0.45 * val["MdAPE"] / baseline["MdAPE"]
        + 0.35 * val["MAPE"] / baseline["MAPE"]
        + 0.20 * val["p95_APE"] / baseline["p95_APE"]
    )
    selectors = {
        "대표 정확도 우선": (val, ["MdAPE", "MAPE", "p95_APE"]),
        "평균 오차 우선": (val[val["MdAPE"] <= baseline["MdAPE"] * 1.05].copy(), ["MAPE", "MdAPE", "p95_APE"]),
        "큰 오차 방어 우선": (val[val["MdAPE"] <= baseline["MdAPE"] * 1.08].copy(), ["p95_APE", "MdAPE", "MAPE"]),
        "균형 점수": (val, ["balanced_score", "MdAPE", "MAPE", "p95_APE"]),
    }
    rows = []
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    for objective, (pool, sort_cols) in selectors.items():
        if pool.empty:
            pool = val
        picked = pool.sort_values(sort_cols).iloc[0]
        row = {
            "selection_objective": objective,
            "candidate": picked["candidate"],
            "family": picked["family"],
            "feature_group": picked["feature_group"],
            "validation_MdAPE": float(picked["MdAPE"]),
            "validation_MAPE": float(picked["MAPE"]),
            "validation_p95_APE": float(picked["p95_APE"]),
            "validation_delta_MdAPE": float(picked["delta_MdAPE"]),
            "validation_delta_MAPE": float(picked["delta_MAPE"]),
            "validation_delta_p95_APE": float(picked["delta_p95_APE"]),
        }
        if row["candidate"] in test.index:
            test_row = test.loc[row["candidate"]]
            if isinstance(test_row, pd.DataFrame):
                test_row = test_row.iloc[0]
            row.update({
                "test_MdAPE": float(test_row["MdAPE"]),
                "test_MAPE": float(test_row["MAPE"]),
                "test_p95_APE": float(test_row["p95_APE"]),
                "test_delta_MdAPE": float(test_row["delta_MdAPE"]),
                "test_delta_MAPE": float(test_row["delta_MAPE"]),
                "test_delta_p95_APE": float(test_row["delta_p95_APE"]),
            })
        rows.append(row)
    return pd.DataFrame(rows).drop_duplicates("candidate")


def markdown_table(frame: pd.DataFrame, floatfmt: str = ".4f") -> str:
    if frame.empty:
        return "_데이터 없음_"
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else format(float(value), floatfmt))
        else:
            out[col] = out[col].map(lambda value: "" if pd.isna(value) else str(value))
    headers = [str(col) for col in out.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in out.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def render_report(metrics: pd.DataFrame, selected: pd.DataFrame, coverage: pd.DataFrame) -> tuple[str, str]:
    val = metrics[metrics["split"].eq("validation")].copy()
    test = metrics[metrics["split"].eq("test")].copy()
    baseline_test = test[test["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    baseline_val = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    top_test = test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    top_val = val.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        "- 가설: Warm에서도 생년, 작가 활동량, 판매중 작품 수, 전시 횟수, 갤러리 tier가 남은 오차를 설명하면 현재 후보 위의 작은 보정으로 성능을 높일 수 있다.",
        "- 검증 방식: 현재 후보 예측값은 고정하고, validation 잔차를 작가 단위 교차검증으로 학습해 보정값을 만든다. test는 validation 전체로 만든 보정식을 한 번 적용한다.",
        f"- 기준 validation MdAPE/MAPE/p95: `{baseline_val['MdAPE']:.4f}` / `{baseline_val['MAPE']:.4f}` / `{baseline_val['p95_APE']:.4f}`",
        f"- 기준 test MdAPE/MAPE/p95: `{baseline_test['MdAPE']:.4f}` / `{baseline_test['MAPE']:.4f}` / `{baseline_test['p95_APE']:.4f}`",
        "",
        "## 1. 기존 실험 확인",
        "",
        "- PP-AMW1/PP-AMW4: 작가 생년/작품 수/판매중 작품 수/팔로워 기반 Warm 잔차 보정 실험은 이미 수행됨.",
        "- PP-WCOEF4: 작가 기준선과 작가 메타를 Huber 계수로 직접 넣는 재학습은 수행됐지만 현재 Warm 1순위 후보에는 미달.",
        "- PP-Z1: 전시/갤러리/검색 피처를 Warm Huber에 직접 넣어 재학습한 실험은 수행됐지만 현재 Warm 1순위 후보에는 미달.",
        "- 미검증 영역: 현재 Warm 1순위 후보 위에 작가 메타와 전시/갤러리 피처를 함께 사용한 계수형 잔차 보정.",
        "",
        "## 2. 피처 커버리지",
        "",
        markdown_table(coverage),
        "",
        "## 3. Validation 기준 선택 후보",
        "",
        markdown_table(selected),
        "",
        "## 4. Test 상위 후보",
        "",
        "| 순위 | 후보 | 방식 | 피처 그룹 | MdAPE | MAPE | p95_APE | d_MdAPE | d_MAPE | d_p95 | 평균 보정폭 |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_test.itertuples(index=False), 1):
        lines.append(
            f"| {rank} | `{row.candidate}` | {row.family} | {row.feature_group} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | "
            f"{row.delta_MdAPE:.4f} | {row.delta_MAPE:.4f} | {row.delta_p95_APE:.4f} | {row.mean_abs_correction:.4f} |"
        )
    lines += [
        "",
        "## 5. Validation 상위 후보",
        "",
        "| 순위 | 후보 | 방식 | 피처 그룹 | MdAPE | MAPE | p95_APE | d_MdAPE | d_MAPE | d_p95 |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_val.itertuples(index=False), 1):
        lines.append(
            f"| {rank} | `{row.candidate}` | {row.family} | {row.feature_group} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | "
            f"{row.delta_MdAPE:.4f} | {row.delta_MAPE:.4f} | {row.delta_p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 6. 해석",
        "",
        "- 개선이 있으면: 작가 메타/전시·갤러리 정보가 Warm의 남은 오차를 설명하는 보조 신호로 작동한 것.",
        "- 개선이 작으면: 현재 1순위 후보가 작가 기준선과 유사 작품 기반 가격 피처로 이미 대부분의 Warm 신호를 흡수한 것.",
        "- 갤러리 검증 tier는 test 커버리지가 0에 가까워 현재 운영 후보의 핵심 보정축으로 쓰기 어렵고, raw tier/전시 횟수는 커버리지가 있어 보조 검증 대상으로 볼 수 있다.",
        "- validation 선택 후보와 test 최상위 후보가 다르면 즉시 v0.1 기본값에 반영하지 않고 반복 split 검증 대상으로 둔다.",
        "",
        "## 7. 산출물",
        "",
        "- `outputs/all_candidate_metrics.csv`",
        "- `outputs/predictions.csv`",
        "- `outputs/huber_coefficients_top.csv`",
        "- `outputs/selected_candidates.csv`",
        "- `outputs/feature_coverage.csv`",
        "- `reports/result_report.md`",
        "- `reports/result_report.html`",
    ]
    markdown = "\n".join(lines) + "\n"
    body = "\n".join(
        f"<h1>{html.escape(line[2:])}</h1>" if line.startswith("# ")
        else f"<h2>{html.escape(line[3:])}</h2>" if line.startswith("## ")
        else f"<pre>{html.escape(line)}</pre>" if line.startswith("|") or line.startswith("- ")
        else "<br>" if not line
        else f"<p>{html.escape(line)}</p>"
        for line in lines
    )
    document = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(EXP_ID)} {html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.55; color: #1f2937; }}
    pre {{ white-space: pre-wrap; background: #f8fafc; padding: 8px 10px; border: 1px solid #e5e7eb; border-radius: 6px; }}
    h1, h2 {{ color: #111827; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    return markdown, document


def main() -> None:
    ensure_dirs()
    val, test = load_frames()

    baseline_rows: list[dict[str, Any]] = []
    for split_name, frame in [("validation", val), ("test", test)]:
        correction = np.zeros(len(frame), dtype=float)
        add_metric_row(
            baseline_rows,
            CURRENT_CANDIDATE,
            "reference",
            "reference",
            "reference_prediction",
            split_name,
            frame,
            frame["current_pred_log"].to_numpy(dtype=float),
            correction,
            "reference_prediction",
        )
    baseline = pd.DataFrame(baseline_rows)

    huber_metrics, huber_preds, coeffs = run_huber_residual_candidates(val, test)
    seg_metrics, seg_preds = run_segment_candidates(val, test)
    metrics = pd.concat([baseline, huber_metrics, seg_metrics], ignore_index=True)
    predictions = pd.concat([
        prediction_frame(CURRENT_CANDIDATE, "reference_prediction", "validation", val, val["current_pred_log"].to_numpy(dtype=float), np.zeros(len(val), dtype=float)),
        prediction_frame(CURRENT_CANDIDATE, "reference_prediction", "test", test, test["current_pred_log"].to_numpy(dtype=float), np.zeros(len(test), dtype=float)),
        huber_preds,
        seg_preds,
    ], ignore_index=True)
    coverage = coverage_table(val, test)
    selected = selected_candidates(metrics)

    metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "huber_coefficients_top.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    coverage.to_csv(EXP_DIR / "outputs" / "feature_coverage.csv", index=False)

    manifest = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": CURRENT_CANDIDATE,
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "outputs": [
            "outputs/all_candidate_metrics.csv",
            "outputs/predictions.csv",
            "outputs/huber_coefficients_top.csv",
            "outputs/selected_candidates.csv",
            "outputs/feature_coverage.csv",
        ],
        "existing_related_experiments": ["PP-AMW1", "PP-AMW4", "PP-WCOEF4", "PP-Z1"],
    }
    (EXP_DIR / "outputs" / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown, document = render_report(metrics, selected, coverage)
    (EXP_DIR / "reports" / "result_report.md").write_text(markdown, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(document, encoding="utf-8")
    (DOC_ROOT / "pp_amw5_warm_artist_meta_external_coefficient_correction_summary.md").write_text(markdown, encoding="utf-8")
    (DOC_ROOT / "pp_amw5_warm_artist_meta_external_coefficient_correction_summary.html").write_text(document, encoding="utf-8")

    test_top = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(8)
    print(test_top[["candidate", "family", "feature_group", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]].to_string(index=False))


if __name__ == "__main__":
    main()
