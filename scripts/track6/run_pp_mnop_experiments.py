#!/usr/bin/env python3
"""Run Track6 PP-M/N/O/P follow-up postprocessing experiments."""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    REPO,
    SEED,
    SPLIT_ROOT,
    artifact_features,
    cat_indices,
    cat_ready,
    fit_predict,
    load_scope,
    metrics,
    normalize,
    split_types,
)


EXPERIMENTS = {
    "PP-M1": {"slug": "PP-M1_warm_artist_median_huber_residual", "title": "Warm 작가 중앙값 기준선 + Huber 잔차 모델"},
    "PP-M2": {"slug": "PP-M2_warm_artist_prior_huber", "title": "Warm target-encoded artist prior + Huber"},
    "PP-M3": {"slug": "PP-M3_warm_artist_median_catboost_residual", "title": "Warm 작가 기준선 + CatBoost residual"},
    "PP-N1": {"slug": "PP-N1_cold_quantile_lightgbm_conformal_range", "title": "Cold Quantile LightGBM 범위 보수화"},
    "PP-N2": {"slug": "PP-N2_cold_catboost_quantile_range", "title": "Cold CatBoost Quantile 손실 비교"},
    "PP-N3": {"slug": "PP-N3_cold_conformal_baseline_range", "title": "Cold Conformal prediction 보정"},
    "PP-O1": {"slug": "PP-O1_warm_explainable_nonlinear_hgb", "title": "Warm 설명 가능한 비선형 모델"},
    "PP-O2": {"slug": "PP-O2_cold_explainable_nonlinear_hgb", "title": "Cold 설명 가능한 비선형 모델"},
    "PP-P1": {"slug": "PP-P1_warm_cold_final_policy_routing", "title": "Warm/Cold 최종 후보 라우팅 통합"},
    "PP-P2": {"slug": "PP-P2_quantile_width_model_routing", "title": "Quantile width 기반 모델 선택 라우팅"},
    "PP-P3": {"slug": "PP-P3_service_display_policy_validation", "title": "서비스 표시 정책 통합 검증"},
}


def prediction_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, notes: str = "", extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def warm_data(extra_features: list[str] | None = None) -> tuple[list[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    features = artifact_features()["warm"]
    if extra_features:
        features = list(dict.fromkeys(features + extra_features))
    train, val, test = load_scope("warm", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    return features, train, val, test


def cold_lgb_data() -> tuple[list[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    features = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    return features, train, val, test


def artist_prior(train: pd.DataFrame, frame: pd.DataFrame, smoothing: float = 5.0) -> np.ndarray:
    global_median = float(train["ln_price_krw"].median())
    stats = train.groupby("artist_key")["ln_price_krw"].agg(["median", "count"])
    smooth = (stats["median"] * stats["count"] + global_median * smoothing) / (stats["count"] + smoothing)
    return frame["artist_key"].map(smooth).fillna(global_median).to_numpy(dtype=float)


def non_artist_features(features: list[str]) -> list[str]:
    return [f for f in features if f not in {"artist_key", "artist_name_ko"}]


def huber_residual_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)),
    ])


def run_m1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features, train, val, test = warm_data()
    residual_features = non_artist_features(features)
    base = fit_predict("huber", train, val, test, features)
    train_prior = artist_prior(train, train, smoothing=5.0)
    model = huber_residual_model(residual_features)
    model.fit(train[residual_features], train["ln_price_krw"].to_numpy(dtype=float) - train_prior)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-M1", "scope": "warm", "artist_prior": "smoothed_train_artist_median", "smoothing": 5.0, "residual_model": "Huber"}]
    for split, frame in [("validation", val), ("test", test)]:
        prior = artist_prior(train, frame, smoothing=5.0)
        pred = prior + np.asarray(model.predict(frame[residual_features]), dtype=float)
        add_metric(rows, "PP-M1", "baseline_warm_huber", "warm", split, frame, base[split], "baseline")
        add_metric(rows, "PP-M1", "artist_median_plus_huber_residual", "warm", split, frame, pred, "artist_baseline_then_huber_residual")
        preds.append(prediction_frame("PP-M1", "baseline_warm_huber", "warm", split, frame, base[split], "baseline"))
        preds.append(prediction_frame("PP-M1", "artist_median_plus_huber_residual", "warm", split, frame, pred, "artist_baseline_then_huber_residual", {"artist_prior_log": prior}))
    return rows, preds, maps


def run_m2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features, train, val, test = warm_data()
    base = fit_predict("huber", train, val, test, features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for smoothing in [3.0, 8.0, 20.0]:
        train2 = train.copy()
        val2 = val.copy()
        test2 = test.copy()
        train2["artist_price_prior_log"] = artist_prior(train, train, smoothing=smoothing)
        val2["artist_price_prior_log"] = artist_prior(train, val, smoothing=smoothing)
        test2["artist_price_prior_log"] = artist_prior(train, test, smoothing=smoothing)
        model_features = list(dict.fromkeys(non_artist_features(features) + ["artist_price_prior_log"]))
        model = huber_residual_model(model_features)
        model.fit(train2[model_features], train2["ln_price_krw"].to_numpy(dtype=float))
        maps.append({"experiment_id": "PP-M2", "scope": "warm", "smoothing": smoothing, "model": "Huber with artist_price_prior_log"})
        for split, frame in [("validation", val2), ("test", test2)]:
            pred = np.asarray(model.predict(frame[model_features]), dtype=float)
            candidate = f"artist_prior_huber_smoothing_{smoothing:g}"
            add_metric(rows, "PP-M2", "baseline_warm_huber", "warm", split, frame, base[split], "baseline")
            add_metric(rows, "PP-M2", candidate, "warm", split, frame, pred, "artist_prior_feature_huber", extra={"smoothing": smoothing})
            preds.append(prediction_frame("PP-M2", candidate, "warm", split, frame, pred, "artist_prior_feature_huber", {"smoothing": smoothing}))
    return rows, preds, maps


def run_m3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features, train, val, test = warm_data()
    residual_features = non_artist_features(features)
    base = fit_predict("huber", train, val, test, features)
    train_prior = artist_prior(train, train, smoothing=5.0)
    target = train["ln_price_krw"].to_numpy(dtype=float) - train_prior
    model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=450,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=8.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(cat_ready(train, residual_features), target, cat_features=cat_indices(residual_features))
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-M3", "scope": "warm", "artist_prior": "smoothed_train_artist_median", "smoothing": 5.0, "residual_model": "CatBoost"}]
    for split, frame in [("validation", val), ("test", test)]:
        prior = artist_prior(train, frame, smoothing=5.0)
        pred = prior + np.asarray(model.predict(cat_ready(frame, residual_features)), dtype=float)
        add_metric(rows, "PP-M3", "baseline_warm_huber", "warm", split, frame, base[split], "baseline")
        add_metric(rows, "PP-M3", "artist_median_plus_catboost_residual", "warm", split, frame, pred, "artist_baseline_then_catboost_residual")
        preds.append(prediction_frame("PP-M3", "artist_median_plus_catboost_residual", "warm", split, frame, pred, "artist_baseline_then_catboost_residual", {"artist_prior_log": prior}))
    return rows, preds, maps


def quantile_lgbm(features: list[str], alpha: float) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=360,
            learning_rate=0.04,
            num_leaves=31,
            min_child_samples=35,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=2.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def coverage_stats(frame: pd.DataFrame, low_log: np.ndarray, high_log: np.ndarray) -> dict[str, float]:
    y = frame["ln_price_krw"].to_numpy(dtype=float)
    low = np.minimum(low_log, high_log)
    high = np.maximum(low_log, high_log)
    return {
        "range_coverage": float(np.mean((y >= low) & (y <= high))),
        "median_range_ratio": float(np.median(np.exp(high - low))),
    }


def run_n1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features, train, val, test = cold_lgb_data()
    base = fit_predict("lightgbm", train, val, test, features)
    models = {a: quantile_lgbm(features, a) for a in [0.10, 0.50, 0.90]}
    for model in models.values():
        model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    q_val = {a: np.asarray(m.predict(val[features]), dtype=float) for a, m in models.items()}
    q_test = {a: np.asarray(m.predict(test[features]), dtype=float) for a, m in models.items()}
    low_val = np.minimum(q_val[0.10], q_val[0.90])
    high_val = np.maximum(q_val[0.10], q_val[0.90])
    y_val = val["ln_price_krw"].to_numpy(dtype=float)
    scores = np.maximum.reduce([low_val - y_val, y_val - high_val, np.zeros_like(y_val)])
    qhat = float(np.quantile(scores, 0.80))
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-N1", "scope": "cold", "range_model": "LightGBM quantile q10/q50/q90", "conformal_qhat_log": qhat, "target_coverage": 0.80}]
    for split, frame, q in [("validation", val, q_val), ("test", test, q_test)]:
        low = np.minimum(q[0.10], q[0.90]) - qhat
        high = np.maximum(q[0.10], q[0.90]) + qhat
        extra = coverage_stats(frame, low, high)
        add_metric(rows, "PP-N1", "baseline_cold_lightgbm", "cold", split, frame, base[split], "baseline")
        add_metric(rows, "PP-N1", "quantile_lgbm_q50_conformal_range", "cold", split, frame, q[0.50], "quantile_q50_with_conformal_range", extra=extra)
        preds.append(prediction_frame("PP-N1", "quantile_lgbm_q50_conformal_range", "cold", split, frame, q[0.50], "quantile_q50_with_conformal_range", {"range_low_log": low, "range_high_log": high}))
    return rows, preds, maps


def run_n2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()["cold_catboost"]
    train, val, test = load_scope("cold", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    base = fit_predict("catboost", train, val, test, features)
    models: dict[float, CatBoostRegressor] = {}
    for alpha in [0.10, 0.50, 0.90]:
        model = CatBoostRegressor(
            loss_function=f"Quantile:alpha={alpha}",
            iterations=520,
            learning_rate=0.04,
            depth=6,
            l2_leaf_reg=8.0,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(cat_ready(train, features), train["ln_price_krw"].to_numpy(dtype=float), cat_features=cat_indices(features))
        models[alpha] = model
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-N2", "scope": "cold", "range_model": "CatBoost Quantile q10/q50/q90", "features": features}]
    for split, frame in [("validation", val), ("test", test)]:
        q = {alpha: np.asarray(model.predict(cat_ready(frame, features)), dtype=float) for alpha, model in models.items()}
        low = np.minimum(q[0.10], q[0.90])
        high = np.maximum(q[0.10], q[0.90])
        extra = coverage_stats(frame, low, high)
        add_metric(rows, "PP-N2", "baseline_cold_catboost", "cold", split, frame, base[split], "baseline")
        add_metric(rows, "PP-N2", "catboost_quantile_q50", "cold", split, frame, q[0.50], "catboost_quantile_q50", extra=extra)
        preds.append(prediction_frame("PP-N2", "baseline_cold_catboost", "cold", split, frame, base[split], "baseline"))
        preds.append(prediction_frame("PP-N2", "catboost_quantile_q50", "cold", split, frame, q[0.50], "catboost_quantile_q50", {
            "range_low_log": low,
            "range_high_log": high,
            "range_width_log": high - low,
        }))
    return rows, preds, maps


def run_n3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features, train, val, test = cold_lgb_data()
    base = fit_predict("lightgbm", train, val, test, features)
    abs_resid = np.abs(val["ln_price_krw"].to_numpy(dtype=float) - base["validation"])
    q80 = float(np.quantile(abs_resid, 0.80))
    q90 = float(np.quantile(abs_resid, 0.90))
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-N3", "scope": "cold", "base_model": "LightGBM", "q80_abs_residual_log": q80, "q90_abs_residual_log": q90}]
    for split, frame in [("validation", val), ("test", test)]:
        pred = base[split]
        for qname, width in [("range_80pct_conformal", q80), ("range_90pct_conformal", q90)]:
            low = pred - width
            high = pred + width
            extra = coverage_stats(frame, low, high)
            add_metric(rows, "PP-N3", qname, "cold", split, frame, pred, "baseline_point_with_conformal_range", extra=extra)
            preds.append(prediction_frame("PP-N3", qname, "cold", split, frame, pred, "baseline_point_with_conformal_range", {"range_low_log": low, "range_high_log": high}))
    return rows, preds, maps


def hgb_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HistGradientBoostingRegressor(
            loss="squared_error",
            learning_rate=0.035,
            max_iter=360,
            max_leaf_nodes=31,
            l2_regularization=0.05,
            random_state=SEED,
        )),
    ])


def run_o(exp_id: str, scope: str, baseline_model: str, feature_key: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()[feature_key]
    train, val, test = load_scope(scope, features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    base = fit_predict(baseline_model, train, val, test, features)
    model = hgb_model(features)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": exp_id, "scope": scope, "model": "HistGradientBoostingRegressor", "features": features, "purpose": "explainable_nonlinear_baseline_check"}]
    for split, frame in [("validation", val), ("test", test)]:
        pred = np.asarray(model.predict(frame[features]), dtype=float)
        add_metric(rows, exp_id, f"baseline_{baseline_model}", scope, split, frame, base[split], "baseline")
        add_metric(rows, exp_id, "hist_gradient_boosting", scope, split, frame, pred, "explainable_nonlinear_candidate")
        preds.append(prediction_frame(exp_id, "hist_gradient_boosting", scope, split, frame, pred, "explainable_nonlinear_candidate"))
    return rows, preds, maps


def source_prediction(folder: str, candidate: str, scope: str, split: str, model_source: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq(scope) & df["split"].astype(str).eq(split)
    if model_source and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(model_source)
    part = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if part.empty:
        raise ValueError(f"missing source prediction folder={folder} candidate={candidate} scope={scope} split={split}")
    return part


def metric_frame_from_source(src: pd.DataFrame) -> pd.DataFrame:
    return src[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def merge_source_predictions(sources: list[tuple[str, str, str, str | None]], scope: str, split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate, model_source in sources:
        src = source_prediction(folder, candidate, scope, split, model_source)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("no merged predictions")
    return merged


def choose_by_width(
    val: pd.DataFrame,
    test: pd.DataFrame,
    candidates: list[str],
    width_col: str,
) -> tuple[pd.Series, pd.Series, list[dict[str, Any]]]:
    q1, q2 = np.quantile(val[width_col].to_numpy(dtype=float), [0.33, 0.66])
    bins = [(-np.inf, q1, "stable"), (q1, q2, "caution"), (q2, np.inf, "risk")]
    selected: list[dict[str, Any]] = []
    val_pred = pd.Series(index=val.index, dtype=float)
    test_pred = pd.Series(index=test.index, dtype=float)
    for low, high, name in bins:
        mask_val = (val[width_col] > low) & (val[width_col] <= high)
        scores = {}
        frame = metric_frame_from_source(val.loc[mask_val].rename(columns={candidates[0]: "pred_log"}))
        for cand in candidates:
            if mask_val.sum() == 0:
                scores[cand] = np.inf
            else:
                scores[cand] = metrics(frame, val.loc[mask_val, cand].to_numpy(dtype=float))["MdAPE"]
        best = min(scores, key=scores.get)
        mask_test = (test[width_col] > low) & (test[width_col] <= high)
        val_pred.loc[mask_val] = val.loc[mask_val, best].to_numpy(dtype=float)
        test_pred.loc[mask_test] = test.loc[mask_test, best].to_numpy(dtype=float)
        selected.append({
            "segment": name,
            "width_low": float(low) if np.isfinite(low) else None,
            "width_high": float(high) if np.isfinite(high) else None,
            "selected_candidate": best,
            "validation_rows": int(mask_val.sum()),
            "test_rows": int(mask_test.sum()),
            **{f"val_mdape_{k}": float(v) for k, v in scores.items()},
        })
    val_pred = val_pred.fillna(val[candidates[0]])
    test_pred = test_pred.fillna(test[candidates[0]])
    return val_pred, test_pred, selected


def frame_from_pred_source(df: pd.DataFrame) -> pd.DataFrame:
    return df[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def run_p1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    sources = [
        ("warm", "PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75", "warm_pp_d4_integrated", None),
        ("cold", "PP-B4_oof_base_residual_source", "baseline", "cold_baseline_lightgbm", "cold_lightgbm"),
        ("cold", "PP-A7_hierarchical_segment_residual_calibration", "corrected_hierarchical", "cold_aux_a7_hierarchical", None),
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [{"experiment_id": "PP-P1", "policy": "api_candidate_policy", "warm_primary": "PP-D4", "cold_primary": "baseline_lightgbm", "cold_auxiliary": "PP-A7 risk/range"}]
    for scope, folder, candidate, label, model_source in sources:
        for split in ["validation", "test"]:
            src = source_prediction(folder, candidate, scope, split, model_source)
            frame = frame_from_pred_source(src)
            pred = src["pred_log"].to_numpy(dtype=float)
            add_metric(rows, "PP-P1", label, scope, split, frame, pred, "final_policy_component")
            extra = {"display_policy": "point_with_range" if scope == "warm" else "reference_price_with_wide_range"}
            preds.append(prediction_frame("PP-P1", label, scope, split, frame, pred, "final_policy_component", extra))
    return rows, preds, maps


def run_p2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    specs = {
        "warm": {
            "sources": [
                ("baseline_huber", "PP-B4_oof_base_residual_source", "baseline", "warm_huber"),
                ("pp_l8", "PP-L8_quantile_huber_catboost_sequential", "PP-L8_warm_quantile_features_huber_catboost_residual", None),
                ("pp_d4", "PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75", None),
            ],
            "width_source": ("PP-K1_quantile_price_range_auxiliary", "quantile_q50", None),
            "candidates": ["baseline_huber", "pp_l8", "pp_d4"],
        },
        "cold": {
            "sources": [
                ("baseline_lgb", "PP-B4_oof_base_residual_source", "baseline", "cold_lightgbm"),
                ("pp_n1_q50", "PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", None),
                ("pp_o2_hgb", "PP-O2_cold_explainable_nonlinear_hgb", "hist_gradient_boosting", None),
            ],
            "width_source": ("PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", None),
            "candidates": ["baseline_lgb", "pp_n1_q50", "pp_o2_hgb"],
        },
    }
    for scope, spec in specs.items():
        val = merge_source_predictions(spec["sources"], scope, "validation")
        test = merge_source_predictions(spec["sources"], scope, "test")
        width_folder, width_candidate, width_model_source = spec["width_source"]
        for split, merged in [("validation", val), ("test", test)]:
            width_src = source_prediction(width_folder, width_candidate, scope, split, width_model_source)
            width_cols = [c for c in ["range_width_log", "quantile_width"] if c in width_src.columns]
            if width_cols:
                w = width_src[["_track6_row_id", width_cols[0]]].rename(columns={width_cols[0]: "routing_width"})
            elif {"range_low_log", "range_high_log"}.issubset(width_src.columns):
                w = width_src[["_track6_row_id", "range_low_log", "range_high_log"]].copy()
                w["routing_width"] = w["range_high_log"] - w["range_low_log"]
                w = w[["_track6_row_id", "routing_width"]]
            else:
                raise ValueError(f"missing width columns in {width_folder}")
            merged_width = merged.merge(w, on="_track6_row_id", how="inner")
            if split == "validation":
                val = merged_width
            else:
                test = merged_width
        val_pred, test_pred, selected = choose_by_width(val, test, spec["candidates"], "routing_width")
        maps.extend([{"experiment_id": "PP-P2", "scope": scope, **item} for item in selected])
        for split, merged, pred in [("validation", val, val_pred.to_numpy(dtype=float)), ("test", test, test_pred.to_numpy(dtype=float))]:
            frame = frame_from_pred_source(merged)
            add_metric(rows, "PP-P2", "quantile_width_model_routing", scope, split, frame, pred, "width_segment_selected_model")
            for cand in spec["candidates"]:
                add_metric(rows, "PP-P2", f"baseline_component_{cand}", scope, split, frame, merged[cand].to_numpy(dtype=float), "routing_component")
            preds.append(prediction_frame("PP-P2", "quantile_width_model_routing", scope, split, frame, pred, "width_segment_selected_model", {"routing_width": merged["routing_width"].to_numpy(dtype=float)}))
    return rows, preds, maps


def run_p3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps = [
        {"experiment_id": "PP-P3", "scope": "warm", "display_policy": "point_with_range", "model_policy": "PP-D4"},
        {"experiment_id": "PP-P3", "scope": "cold", "display_policy": "reference_price_with_wide_range", "model_policy": "PP-P2/P-N range candidates"},
    ]
    sources = [
        ("warm", "PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "point_with_range"),
        ("cold", "PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "reference_price_with_wide_range"),
        ("cold", "PP-N3_cold_conformal_baseline_range", "range_90pct_conformal", "reference_price_90pct_conformal_range"),
    ]
    for scope, folder, candidate, display in sources:
        for split in ["validation", "test"]:
            src = source_prediction(folder, candidate, scope, split)
            frame = frame_from_pred_source(src)
            pred = src["pred_log"].to_numpy(dtype=float)
            extra = {}
            if {"range_low_log", "range_high_log"}.issubset(src.columns):
                extra.update(coverage_stats(frame, src["range_low_log"].to_numpy(dtype=float), src["range_high_log"].to_numpy(dtype=float)))
            add_metric(rows, "PP-P3", f"{candidate}_{display}", scope, split, frame, pred, display, extra=extra)
            preds.append(prediction_frame("PP-P3", f"{candidate}_{display}", scope, split, frame, pred, display))
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy() if "split" in metrics_df.columns else metrics_df.copy()
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.",
        "- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    sort_cols = [c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]
    for row in val.sort_values(sort_cols).itertuples():
        extra = []
        for key in ["range_coverage", "median_range_ratio", "smoothing"]:
            if hasattr(row, key):
                value = getattr(row, key)
                if pd.notna(value):
                    extra.append(f"{key}={value:.4f}" if isinstance(value, float) else f"{key}={value}")
        lines.append(
            f"| `{getattr(row, 'scope', '')}` | `{getattr(row, 'candidate', '')}` | `{getattr(row, 'policy', '')}` | "
            f"`{getattr(row, 'MdAPE', float('nan')):.4f}` | `{getattr(row, 'MAPE', float('nan')):.4f}` | "
            f"`{getattr(row, 'p95_APE', float('nan')):.4f}` | `{getattr(row, 'RMSE_log', float('nan')):.4f}` | {'; '.join(extra)} |"
        )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], pred_frames: list[pd.DataFrame], map_rows: list[dict[str, Any]]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(pred_frames, ignore_index=True)
    map_df = pd.DataFrame(map_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].astype(str).eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].astype(str).eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": EXPERIMENTS[exp_id]["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "validation selected, test confirmation"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps({"source": "track6_artifact_manifest plus generated policy features"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps({"target": "ln_price_krw", "experiment_id": exp_id}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(map_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {
        "PP-M1": run_m1,
        "PP-M2": run_m2,
        "PP-M3": run_m3,
        "PP-N1": run_n1,
        "PP-N2": run_n2,
        "PP-N3": run_n3,
        "PP-O1": lambda: run_o("PP-O1", "warm", "huber", "warm"),
        "PP-O2": lambda: run_o("PP-O2", "cold", "lightgbm", "cold_lightgbm"),
        "PP-P1": run_p1,
        "PP-P2": run_p2,
        "PP-P3": run_p3,
    }
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runners.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        val = df[df["split"].astype(str).eq("validation")].copy()
        if not val.empty:
            sort_cols = [c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]
            summary_rows.extend(val.sort_values(sort_cols).groupby("scope", as_index=False).head(1).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-MNOP_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-MNOP_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
