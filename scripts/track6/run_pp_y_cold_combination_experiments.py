#!/usr/bin/env python3
"""Run Track6 PP-Y Cold feature/model combination expansion experiments."""
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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_h_search_pilot_experiments import (  # noqa: E402
    SEARCH_CATEGORICAL,
    SEARCH_CONTEXT_FEATURES,
    SEARCH_FEATURE_PATH,
    SEARCH_NUMERIC,
    add_search_features,
)
from run_pp_w_experiments import (  # noqa: E402
    BASE_NUMERIC,
    META_ALL,
    META_NUMERIC,
    base_feature_sets,
    load_cold_with_meta,
    unique,
)
from run_pp_x_gallery_exhibition_revalidation import (  # noqa: E402
    EXHIBITION_NUMERIC,
    EXTERNAL_CATEGORICAL,
    EXTERNAL_INTERACTIONS_CATEGORICAL,
    EXTERNAL_INTERACTIONS_NUMERIC,
    EXTERNAL_NUMERIC,
    GALLERY_CATEGORICAL,
    GALLERY_NUMERIC,
    add_external_features,
)


EXPERIMENTS = {
    "PP-Y1": {"slug": "PP-Y1_cold_lgbq_external_objective_refit", "title": "Cold LightGBM Quantile 전시/갤러리 목적별 재학습"},
    "PP-Y2": {"slug": "PP-Y2_cold_lgbq_search_external_combo", "title": "Cold LightGBM Quantile 검색 + 전시/갤러리 결합"},
    "PP-Y3": {"slug": "PP-Y3_cold_catboost_quantile_gallery_refit", "title": "Cold CatBoost Quantile 갤러리 단독 재검증"},
    "PP-Y6": {"slug": "PP-Y6_cold_lgbq_first_catboost_residual", "title": "Cold LightGBM Quantile 선행 + CatBoost residual"},
    "PP-Y7": {"slug": "PP-Y7_cold_catboost_quantile_first_lgb_residual", "title": "Cold CatBoost Quantile 선행 + LightGBM residual"},
    "PP-Y8": {"slug": "PP-Y8_cold_catboost_quantile_huber_quality_cap", "title": "Cold CatBoost Quantile + Huber residual + 품질 cap"},
    "PP-Y10": {"slug": "PP-Y10_cold_uncertainty_width_routing", "title": "Cold 불확실성 폭 기반 모델 선택"},
}

SUMMARY_PATH = BASE_EXP_DIR / "PP-Y_cold_combination_summary_metrics.csv"

ADDED_NUMERIC = [
    "base_pred_log",
    "quantile_width_log",
    "price_range_ratio",
]


def load_search_df() -> pd.DataFrame:
    if not SEARCH_FEATURE_PATH.exists():
        raise FileNotFoundError(f"missing search feature cache: {SEARCH_FEATURE_PATH}")
    return pd.read_csv(SEARCH_FEATURE_PATH, low_memory=False)


def external_core_features() -> list[str]:
    return unique(EXHIBITION_NUMERIC + GALLERY_NUMERIC + GALLERY_CATEGORICAL)


def external_interaction_features() -> list[str]:
    return unique(EXHIBITION_NUMERIC + GALLERY_NUMERIC + GALLERY_CATEGORICAL + EXTERNAL_INTERACTIONS_NUMERIC + EXTERNAL_INTERACTIONS_CATEGORICAL)


def search_context_features() -> list[str]:
    return unique(SEARCH_CONTEXT_FEATURES + [
        "search_result_count_log",
        "search_art_context_count_log",
        "search_exhibition_context_count_log",
        "search_source_count_log",
        "search_quality_x_log_area",
        "search_art_match_x_followers_log",
        "search_exhibition_x_career_stage",
        "search_size_quality_bucket",
    ])


def search_all_features() -> list[str]:
    return unique(SEARCH_NUMERIC + SEARCH_CATEGORICAL)


def all_added_features() -> set[str]:
    return set(EXTERNAL_NUMERIC + EXTERNAL_CATEGORICAL + SEARCH_NUMERIC + SEARCH_CATEGORICAL)


def load_cold_full(features: list[str], search_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    added = all_added_features()
    base_required = [feature for feature in features if feature not in added and feature not in ADDED_NUMERIC]
    train, val, test = load_cold_with_meta(base_required)
    train, val, test = add_external_features([train, val, test])
    train, val, test = add_search_features([train, val, test], search_df)
    return train, val, test


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_source = set(BASE_NUMERIC + META_NUMERIC + EXTERNAL_NUMERIC + SEARCH_NUMERIC + ADDED_NUMERIC)
    numeric = [col for col in features if col in numeric_source]
    categorical = [col for col in features if col not in numeric]
    return numeric, categorical


def normalize_frame(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        if col not in out.columns:
            out[col] = "__MISSING__"
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def cat_ready(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame[features].copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in categorical:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out


def cat_indices(features: list[str]) -> list[int]:
    numeric, _ = split_types(features)
    return [idx for idx, col in enumerate(features) if col not in numeric]


def catboost_model(loss: str, *, iterations: int = 520, depth: int = 6) -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function=loss,
        iterations=iterations,
        learning_rate=0.035,
        depth=depth,
        l2_leaf_reg=8.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def lgbm_model(features: list[str], objective: str = "regression", *, alpha: float = 0.5, n_estimators: int = 430) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": n_estimators,
        "learning_rate": 0.035,
        "num_leaves": 31,
        "min_child_samples": 35,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.2,
        "random_state": SEED,
        "verbosity": -1,
    }
    if objective == "quantile":
        params["alpha"] = alpha
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", LGBMRegressor(**params))])


def huber_residual_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([
            ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000)),
    ])


def fit_predict(model_name: str, loss_or_objective: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], *, alpha: float = 0.5) -> dict[str, np.ndarray]:
    train = normalize_frame(train, features)
    val = normalize_frame(val, features)
    test = normalize_frame(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    if model_name == "catboost":
        model = catboost_model(loss_or_objective)
        model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
        return {
            "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
            "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
        }
    model = lgbm_model(features, objective=loss_or_objective, alpha=alpha)
    model.fit(train[features], y)
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def fit_quantile_bundle(model_name: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, dict[str, np.ndarray]]:
    if model_name == "lightgbm":
        return {
            "q10": fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.1),
            "q50": fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.5),
            "q90": fit_predict("lightgbm", "quantile", train, val, test, features, alpha=0.9),
        }
    return {
        "q10": fit_predict("catboost", "Quantile:alpha=0.1", train, val, test, features),
        "q50": fit_predict("catboost", "Quantile:alpha=0.5", train, val, test, features),
        "q90": fit_predict("catboost", "Quantile:alpha=0.9", train, val, test, features),
    }


def metric_input(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "ln_price_krw", "price_krw"]]


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(metric_input(frame), pred_log)


def width_values(bundle: dict[str, dict[str, np.ndarray]], split: str) -> tuple[np.ndarray, np.ndarray]:
    q10 = bundle["q10"][split]
    q90 = bundle["q90"][split]
    width = np.maximum(q90 - q10, 0.0)
    ratio = np.exp(np.clip(width, 0.0, 8.0))
    return width, ratio


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_values(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    for col in ["search_quality_grade", "search_quality_score", "search_collected_flag", "gallery_tier_any_available_flag", "artist_exhibition_available_count"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def add_bundle_predictions(pred_df: pd.DataFrame, bundle: dict[str, dict[str, np.ndarray]], split: str) -> pd.DataFrame:
    out = pred_df.copy()
    q10 = bundle["q10"][split]
    q90 = bundle["q90"][split]
    width = np.maximum(q90 - q10, 0.0)
    out["q10_log"] = q10
    out["q90_log"] = q90
    out["quantile_width_log"] = width
    out["price_range_ratio"] = np.exp(np.clip(width, 0.0, 8.0))
    return out


def frame_with_base_features(frame: pd.DataFrame, pred_log: np.ndarray, features: list[str], width: np.ndarray | None = None) -> pd.DataFrame:
    out = frame.copy()
    out["base_pred_log"] = pred_log
    if width is None:
        out["quantile_width_log"] = 0.0
        out["price_range_ratio"] = 1.0
    else:
        out["quantile_width_log"] = width
        out["price_range_ratio"] = np.exp(np.clip(width, 0.0, 8.0))
    return out


def kfold_oof_base(model_name: str, loss_or_objective: str, train: pd.DataFrame, features: list[str], *, alpha: float = 0.5, n_splits: int = 3) -> np.ndarray:
    train = normalize_frame(train, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    oof = np.zeros(len(train), dtype=float)
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    for fit_idx, pred_idx in kfold.split(train):
        fit_frame = train.iloc[fit_idx].reset_index(drop=True)
        pred_frame = train.iloc[pred_idx].reset_index(drop=True)
        y_fit = y[fit_idx]
        if model_name == "catboost":
            model = catboost_model(loss_or_objective, iterations=360)
            model.fit(cat_ready(fit_frame, features), y_fit, cat_features=cat_indices(features))
            pred = np.asarray(model.predict(cat_ready(pred_frame, features)), dtype=float)
        else:
            model = lgbm_model(features, objective=loss_or_objective, alpha=alpha, n_estimators=320)
            model.fit(fit_frame[features], y_fit)
            pred = np.asarray(model.predict(pred_frame[features]), dtype=float)
        oof[pred_idx] = pred
    return oof


def direct_bundle_experiment(
    exp_id: str,
    candidates: list[tuple[str, str, list[str], str]],
    model_name: str,
    policy: str,
    search_df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    all_features = unique([feature for *_head, features, _hyp in candidates for feature in features])
    train, val, test = load_cold_full(all_features, search_df)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for candidate, strategy, features, hypothesis in candidates:
        bundle = fit_quantile_bundle(model_name, train, val, test, features)
        maps.append({
            "experiment_id": exp_id,
            "candidate": candidate,
            "model": model_name,
            "loss_or_objective": "quantile_q10_q50_q90",
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = bundle["q50"][split]
            width, ratio = width_values(bundle, split)
            add_metric(rows, exp_id, candidate, split, frame, pred, policy, {
                "model": model_name,
                "feature_strategy": strategy,
                "n_features": len(features),
                "quantile_width_median": float(np.median(width)),
                "price_range_ratio_median": float(np.median(ratio)),
            })
            pred_frame = prediction_frame(exp_id, candidate, split, frame, pred, policy, {
                "model": model_name,
                "feature_strategy": strategy,
                "n_features": len(features),
            })
            preds.append(add_bundle_predictions(pred_frame, bundle, split))
    return rows, preds, maps


def y1_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    base = unique(fs["cold_lgb"] + META_ALL)
    return [
        ("lgbq_meta_external_core", "LightGBM Quantile + 작가 메타 + 전시/갤러리 core", unique(base + external_core_features()), "PP-X3의 전시/갤러리 MdAPE 개선 신호를 q10/q50/q90 구조로 재검증"),
        ("lgbq_meta_external_interaction", "LightGBM Quantile + 작가 메타 + 전시/갤러리 상호작용", unique(base + external_interaction_features()), "전시/갤러리 효과가 작품 크기/인지도와 결합될 때의 중앙 예측과 범위 폭 확인"),
    ]


def y2_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    base = unique(fs["cold_lgb"] + META_ALL)
    return [
        ("lgbq_search_context_external_core", "LightGBM Quantile + 검색 문맥 + 전시/갤러리 core", unique(base + search_context_features() + external_core_features()), "검색의 p95 신호와 전시/갤러리의 MdAPE 신호 결합"),
        ("lgbq_search_all_external_core", "LightGBM Quantile + 검색 전체 + 전시/갤러리 core", unique(base + search_all_features() + external_core_features()), "검색 전체 피처와 전시/갤러리 피처를 모두 포함"),
        ("lgbq_search_all_external_interaction", "LightGBM Quantile + 검색 전체 + 전시/갤러리 상호작용", unique(base + search_all_features() + external_interaction_features()), "외부 피처 전체를 넣고 q-width로 위험 구간을 분리"),
    ]


def y3_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    base = unique(fs["generated_all"] + META_ALL)
    gallery = unique(GALLERY_NUMERIC + GALLERY_CATEGORICAL)
    return [
        ("catq_meta_baseline", "CatBoost Quantile + 작가 메타 기준", base, "PP-W2와 같은 CatBoost형 피처를 Quantile q50으로 재검증"),
        ("catq_meta_gallery", "CatBoost Quantile + 갤러리 단독", unique(base + gallery), "CatBoost에서 개선 신호가 있던 갤러리 피처만 추가"),
        ("catq_meta_gallery_search_quality", "CatBoost Quantile + 갤러리 + 검색 품질", unique(base + gallery + [
            "search_quality_score",
            "search_quality_grade",
            "search_collected_flag",
            "search_homonym_risk_grade",
            "search_quality_x_log_area",
        ]), "전시 피처는 제외하고 갤러리와 검색 품질 flag만 조합"),
    ]


def residual_exp(
    exp_id: str,
    base_candidate: tuple[str, str, list[str], str],
    base_model: str,
    residual_model: str,
    search_df: pd.DataFrame,
    *,
    policy: str,
    quality_cap: bool = False,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_cold_full(features, search_df)
    base_loss = "quantile" if base_model == "lightgbm" else "Quantile:alpha=0.5"
    alpha = 0.5
    oof_pred = kfold_oof_base(base_model, base_loss, train, features, alpha=alpha)
    full_bundle = fit_quantile_bundle(base_model, train, val, test, features)
    base_pred_val = full_bundle["q50"]["validation"]
    base_pred_test = full_bundle["q50"]["test"]
    val_width, _ = width_values(full_bundle, "validation")
    test_width, _ = width_values(full_bundle, "test")
    train_residual = train["ln_price_krw"].to_numpy(dtype=float) - oof_pred

    resid_features = unique(features + ADDED_NUMERIC)
    train_resid_frame = frame_with_base_features(train, oof_pred, resid_features)
    val_resid_frame = frame_with_base_features(val, base_pred_val, resid_features, val_width)
    test_resid_frame = frame_with_base_features(test, base_pred_test, resid_features, test_width)
    train_resid_frame = normalize_frame(train_resid_frame, resid_features)
    val_resid_frame = normalize_frame(val_resid_frame, resid_features)
    test_resid_frame = normalize_frame(test_resid_frame, resid_features)

    if residual_model == "catboost":
        model: Any = catboost_model("MAE", iterations=320, depth=4)
        model.fit(cat_ready(train_resid_frame, resid_features), train_residual, cat_features=cat_indices(resid_features))
        val_resid = np.asarray(model.predict(cat_ready(val_resid_frame, resid_features)), dtype=float)
        test_resid = np.asarray(model.predict(cat_ready(test_resid_frame, resid_features)), dtype=float)
    elif residual_model == "lightgbm":
        model = lgbm_model(resid_features, objective="regression_l1", n_estimators=320)
        model.fit(train_resid_frame[resid_features], train_residual)
        val_resid = np.asarray(model.predict(val_resid_frame[resid_features]), dtype=float)
        test_resid = np.asarray(model.predict(test_resid_frame[resid_features]), dtype=float)
    else:
        model = huber_residual_model(resid_features)
        model.fit(train_resid_frame[resid_features], train_residual)
        val_resid = np.asarray(model.predict(val_resid_frame[resid_features]), dtype=float)
        test_resid = np.asarray(model.predict(test_resid_frame[resid_features]), dtype=float)

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = [{
        "experiment_id": exp_id,
        "candidate": candidate,
        "base_model": base_model,
        "base_loss": base_loss,
        "residual_model": residual_model,
        "feature_strategy": strategy,
        "hypothesis": hypothesis,
        "n_features": len(features),
        "residual_train_source": "3-fold OOF base prediction on train",
        "features": ", ".join(features),
    }]

    for split, frame, base_pred, width in [("validation", val, base_pred_val, val_width), ("test", test, base_pred_test, test_width)]:
        add_metric(rows, exp_id, f"base_{candidate}", split, frame, base_pred, f"{policy}_base", {
            "base_model": base_model,
            "feature_strategy": strategy,
            "n_features": len(features),
            "quantile_width_median": float(np.median(width)),
        })
        pred_frame = prediction_frame(exp_id, f"base_{candidate}", split, frame, base_pred, f"{policy}_base", {
            "base_model": base_model,
            "feature_strategy": strategy,
            "n_features": len(features),
        })
        preds.append(pred_frame)

    for cap in [0.10, 0.15, 0.25, 0.35, 0.50]:
        for strength in [0.50, 0.75, 1.00]:
            cand_name = f"{candidate}_{residual_model}_oof_cap{cap:g}_s{strength:g}"
            for split, frame, base_pred, resid, width in [
                ("validation", val, base_pred_val, val_resid, val_width),
                ("test", test, base_pred_test, test_resid, test_width),
            ]:
                if quality_cap:
                    effective_cap = quality_adjusted_cap(frame, cap)
                    final = base_pred + np.clip(resid, -effective_cap, effective_cap) * strength
                else:
                    final = base_pred + np.clip(resid, -cap, cap) * strength
                add_metric(rows, exp_id, cand_name, split, frame, final, policy, {
                    "base_model": base_model,
                    "residual_model": residual_model,
                    "cap": cap,
                    "strength": strength,
                    "quality_cap": quality_cap,
                    "quantile_width_median": float(np.median(width)),
                })
                preds.append(prediction_frame(exp_id, cand_name, split, frame, final, policy, {
                    "base_model": base_model,
                    "residual_model": residual_model,
                    "cap": cap,
                    "strength": strength,
                    "quality_cap": quality_cap,
                }))
    return rows, preds, maps


def quality_adjusted_cap(frame: pd.DataFrame, cap: float) -> np.ndarray:
    quality = frame.get("search_quality_grade", pd.Series("missing", index=frame.index)).astype(str)
    search_low = quality.isin(["missing", "low"]).to_numpy()
    gallery_missing = pd.to_numeric(frame.get("gallery_tier_any_available_flag", pd.Series(0.0, index=frame.index)), errors="coerce").fillna(0.0).to_numpy() <= 0
    exhibition_sparse = pd.to_numeric(frame.get("artist_exhibition_available_count", pd.Series(0.0, index=frame.index)), errors="coerce").fillna(0.0).to_numpy() <= 1
    risk = search_low | (gallery_missing & exhibition_sparse)
    return np.where(risk, cap * 0.55, cap)


def source_prediction(folder: str, candidate: str, split: str) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv", low_memory=False)
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq("cold") & df["split"].astype(str).eq(split)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {folder} {candidate} {split}")
    return out


def y10_routing(current_preds: list[pd.DataFrame]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    pred_df = pd.concat(current_preds, ignore_index=True)
    stable_candidates = [
        "lgbq_search_all_external_interaction",
        "lgbq_search_all_external_core",
        "lgbq_meta_external_interaction",
        "lgbq_meta_external_core",
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    risk_sources = [
        ("h9_search_p95", "PP-H9_cold_lightgbm_quantile_search_feature_augmentation", "lightgbm_quantile_search_all"),
        ("w4_p95", "PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "base_lightgbm_quantile_meta_all"),
    ]
    for stable in stable_candidates:
        stable_frames = {
            split: pred_df[(pred_df["candidate"].eq(stable)) & (pred_df["split"].eq(split))].copy()
            for split in ["validation", "test"]
        }
        if any(frame.empty or "quantile_width_log" not in frame.columns for frame in stable_frames.values()):
            continue
        thresholds = np.quantile(stable_frames["validation"]["quantile_width_log"], [0.33, 0.50, 0.66, 0.80])
        for risk_label, folder, risk_candidate in risk_sources:
            for threshold in thresholds:
                candidate = f"route_{stable}_to_{risk_label}_qwidth_le_{threshold:.3f}"
                maps.append({
                    "experiment_id": "PP-Y10",
                    "candidate": candidate,
                    "stable_source": stable,
                    "risk_source": risk_label,
                    "threshold": float(threshold),
                    "rule": "use stable model when quantile_width_log <= threshold, otherwise risk model",
                })
                for split in ["validation", "test"]:
                    stable_frame = stable_frames[split]
                    risk = source_prediction(folder, risk_candidate, split)
                    merged = stable_frame[[
                        "_track6_row_id",
                        "actual_log",
                        "actual_price",
                        "pred_log",
                        "quantile_width_log",
                        "price_range_ratio",
                    ]].rename(columns={"pred_log": "stable_pred"}).merge(
                        risk[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "risk_pred"}),
                        on="_track6_row_id",
                        how="inner",
                    )
                    use_stable = merged["quantile_width_log"].to_numpy(dtype=float) <= float(threshold)
                    final = np.where(use_stable, merged["stable_pred"].to_numpy(dtype=float), merged["risk_pred"].to_numpy(dtype=float))
                    metric_frame = merged[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
                    rows.append({
                        "experiment_id": "PP-Y10",
                        "candidate": candidate,
                        "scope": "cold",
                        "split": split,
                        "policy": "uncertainty_width_routing",
                        "threshold": float(threshold),
                        "stable_source": stable,
                        "risk_source": risk_label,
                        "stable_rate": float(use_stable.mean()),
                        **metrics(metric_frame, final),
                    })
                    out = pd.DataFrame({
                        "experiment_id": "PP-Y10",
                        "candidate": candidate,
                        "scope": "cold",
                        "split": split,
                        "policy": "uncertainty_width_routing",
                        "_track6_row_id": merged["_track6_row_id"],
                        "actual_log": merged["actual_log"],
                        "pred_log": final,
                        "actual_price": merged["actual_price"],
                        "pred_price": np.clip(np.exp(final), 1_000.0, None),
                        "quantile_width_log": merged["quantile_width_log"],
                        "price_range_ratio": merged["price_range_ratio"],
                        "selected_source": np.where(use_stable, stable, risk_label),
                    })
                    out["residual_log"] = out["actual_log"] - out["pred_log"]
                    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
                    preds.append(out)
    return rows, preds, maps


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "- 없음"
    safe = df.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def render_report(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    info = EXPERIMENTS[exp_id]
    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "- 목적: Cold 가격 예측에서 피처 조합과 모델 순서 변경으로 추가 개선 가능성을 확인한다.",
        "- 기준: 기존 Track6 split을 고정하고 validation에서 후보를 비교한 뒤 test 결과를 함께 기록한다.",
        "",
    ]
    if not metrics_df.empty and "MdAPE" in metrics_df.columns:
        test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
        lines += [
            "## Test 결과 상위",
            "",
            "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for row in test.head(20).itertuples():
            lines.append(f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | `{row.policy}` |")
    lines += ["", "## 설정/피처 맵", "", markdown_table(map_df)]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], preds: list[pd.DataFrame], maps: list[dict[str, Any]]) -> pd.DataFrame:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()
    map_df = pd.DataFrame(maps)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "policy_map.csv", index=False)
    if not pred_df.empty:
        pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
        pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "target": "ln_price_krw",
        "search_feature_path": str(SEARCH_FEATURE_PATH.relative_to(REPO)),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")
    metrics_df["folder"] = str(exp_dir.relative_to(REPO))
    return metrics_df


def main() -> None:
    start = time.time()
    search_df = load_search_df()
    summary_frames: list[pd.DataFrame] = []
    current_pred_frames: list[pd.DataFrame] = []

    rows, preds, maps = direct_bundle_experiment("PP-Y1", y1_candidates(), "lightgbm", "cold_lgbq_external_objective_refit", search_df)
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y1", rows, preds, maps))

    rows, preds, maps = direct_bundle_experiment("PP-Y2", y2_candidates(), "lightgbm", "cold_lgbq_search_external_combo", search_df)
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y2", rows, preds, maps))

    rows, preds, maps = direct_bundle_experiment("PP-Y3", y3_candidates(), "catboost", "cold_catboost_quantile_gallery_refit", search_df)
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y3", rows, preds, maps))

    y6_base = ("lgbq_search_external_interaction", "LightGBM Quantile + 검색 전체 + 전시/갤러리 상호작용", unique(base_feature_sets()["cold_lgb"] + META_ALL + search_all_features() + external_interaction_features()), "LightGBM 중앙 예측 뒤 CatBoost residual로 범주형 잔차 조합 보정")
    rows, preds, maps = residual_exp("PP-Y6", y6_base, "lightgbm", "catboost", search_df, policy="cold_lgbq_first_catboost_residual")
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y6", rows, preds, maps))

    y7_base = ("catq_gallery_search_quality", "CatBoost Quantile + 갤러리 + 검색 품질", unique(base_feature_sets()["generated_all"] + META_ALL + GALLERY_NUMERIC + GALLERY_CATEGORICAL + ["search_quality_score", "search_quality_grade", "search_collected_flag", "search_homonym_risk_grade", "search_quality_x_log_area"]), "CatBoost 중앙 예측 뒤 LightGBM residual로 tail 구간 보정")
    rows, preds, maps = residual_exp("PP-Y7", y7_base, "catboost", "lightgbm", search_df, policy="cold_catboost_quantile_first_lgb_residual")
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y7", rows, preds, maps))

    rows, preds, maps = residual_exp("PP-Y8", y7_base, "catboost", "huber", search_df, policy="cold_catboost_quantile_huber_quality_cap", quality_cap=True)
    current_pred_frames.extend(preds)
    summary_frames.append(write_exp("PP-Y8", rows, preds, maps))

    rows, preds, maps = y10_routing(current_pred_frames)
    summary_frames.append(write_exp("PP-Y10", rows, preds, maps))

    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(SUMMARY_PATH, index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": str(SUMMARY_PATH.relative_to(REPO)),
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
