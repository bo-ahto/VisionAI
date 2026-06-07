#!/usr/bin/env python3
"""Run remaining PP-Y Cold closure experiments.

These experiments close the remaining Cold feature/model-combination axes after
PP-Y1/Y2/Y3/Y6/Y7/Y8/Y10:

- PP-Y4: LightGBM feature-swap candidates with objective changes.
- PP-Y5/Y12/Y13/Y14: information, external, search, and price-bin routing.
- PP-Y11: validation meta stacking over strong PP-Y components.
- PP-Y15: segment residual calibration with minimum row and cap checks.
"""
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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import META_ALL, base_feature_sets, unique  # noqa: E402
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    add_bundle_predictions,
    direct_bundle_experiment,
    external_core_features,
    external_interaction_features,
    fit_predict,
    load_cold_full,
    load_search_df,
    metric_input,
    prediction_frame,
    search_all_features,
    search_context_features,
)


EXPERIMENTS = {
    "PP-Y4": {"slug": "PP-Y4_cold_lgb_feature_objective_closure", "title": "Cold LightGBM 피처 교환 + 목적함수 closure"},
    "PP-Y5": {"slug": "PP-Y5_cold_feature_quality_routing", "title": "Cold 피처 가용성/품질 기반 라우팅"},
    "PP-Y9": {"slug": "PP-Y9_cold_objective_custom_closure", "title": "Cold 목적함수 커스텀 closure"},
    "PP-Y11": {"slug": "PP-Y11_cold_validation_meta_stacking_closure", "title": "Cold validation meta stacking closure"},
    "PP-Y12": {"slug": "PP-Y12_cold_external_availability_routing", "title": "Cold 전시/갤러리 사용 여부 라우팅"},
    "PP-Y13": {"slug": "PP-Y13_cold_search_quality_fallback", "title": "Cold 검색 품질 기반 fallback"},
    "PP-Y14": {"slug": "PP-Y14_cold_pred_price_bin_model_selection", "title": "Cold 예측 가격대별 모델 선택"},
    "PP-Y15": {"slug": "PP-Y15_cold_segment_min_rows_cap_calibration", "title": "Cold segment 최소 표본 수/cap 보정"},
}

PRIOR_SUMMARY = BASE_EXP_DIR / "PP-Y_cold_combination_summary_metrics.csv"
CLOSURE_SUMMARY = BASE_EXP_DIR / "PP-Y_closure_summary_metrics.csv"


SOURCE_SPECS = {
    "y1_external_interaction": ("PP-Y1_cold_lgbq_external_objective_refit", "lgbq_meta_external_interaction"),
    "y1_external_core": ("PP-Y1_cold_lgbq_external_objective_refit", "lgbq_meta_external_core"),
    "y2_search_external_interaction": ("PP-Y2_cold_lgbq_search_external_combo", "lgbq_search_all_external_interaction"),
    "y2_search_external_core": ("PP-Y2_cold_lgbq_search_external_combo", "lgbq_search_all_external_core"),
    "y6_lgbq_cat_resid": ("PP-Y6_cold_lgbq_first_catboost_residual", "lgbq_search_external_interaction_catboost_oof_cap0.15_s1"),
    "y10_mdape_route": ("PP-Y10_cold_uncertainty_width_routing", "route_lgbq_meta_external_interaction_to_h9_search_p95_qwidth_le_1.454"),
    "y10_p95_route": ("PP-Y10_cold_uncertainty_width_routing", "route_lgbq_search_all_external_interaction_to_w4_p95_qwidth_le_1.861"),
    "h9_search_p95": ("PP-H9_cold_lightgbm_quantile_search_feature_augmentation", "lightgbm_quantile_search_all"),
    "w4_p95": ("PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "base_lightgbm_quantile_meta_all"),
}


def source_prediction(label: str, split: str) -> pd.DataFrame:
    folder, candidate = SOURCE_SPECS[label]
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv", low_memory=False)
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq("cold") & df["split"].astype(str).eq(split)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {label}: {folder} {candidate} {split}")
    out["source_label"] = label
    return out


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    metric_frame = frame[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
    return metrics(metric_frame, pred_log)


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_from_frame(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def policy_prediction_frame(exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, selected_source: np.ndarray | str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["actual_log"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["actual_price"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "selected_source": selected_source if isinstance(selected_source, str) else selected_source,
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    for col in ["quantile_width_log", "price_range_ratio", "search_quality_score", "gallery_tier_any_available_flag", "artist_exhibition_available_count"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def merge_sources(labels: list[str], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label in labels:
        src = source_prediction(label, split)
        keep = ["_track6_row_id", "actual_log", "actual_price", "pred_log"]
        for col in ["quantile_width_log", "price_range_ratio", "search_quality_score", "search_quality_grade", "search_collected_flag", "gallery_tier_any_available_flag", "artist_exhibition_available_count"]:
            if col in src.columns:
                keep.append(col)
        part = src[keep].copy().rename(columns={"pred_log": f"{label}_pred"})
        part = part.rename(columns={col: f"{label}_{col}" for col in part.columns if col not in {"_track6_row_id", "actual_log", "actual_price", f"{label}_pred"}})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part.drop(columns=["actual_log", "actual_price"], errors="ignore"), on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty source merge")
    return merged


def y4_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    return [
        ("lgbq_medium_size_meta_external_core", "LightGBM medium-size + 작가메타 + 전시/갤러리", unique(fs["medium_size"] + META_ALL + external_core_features()), "PP-U3 medium-size 신호를 Quantile 구조에서 확인"),
        ("lgbq_support_shape_meta_external_core", "LightGBM support-shape + 작가메타 + 전시/갤러리", unique(fs["support_shape"] + META_ALL + external_core_features()), "support/shape 피처 교환 후보를 Quantile 구조에서 확인"),
        ("lgbq_generated_meta_search_external", "LightGBM generated + 작가메타 + 검색/전시/갤러리", unique(fs["generated_all"] + META_ALL + search_context_features() + external_core_features()), "생성 bucket 전체와 외부 피처 결합 확인"),
    ]


def run_y4(search_df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows, preds, maps = direct_bundle_experiment("PP-Y4", y4_candidates(), "lightgbm", "cold_lgb_feature_swap_quantile", search_df)
    # Add objective variants for the strongest broad candidate.
    fs = base_feature_sets()
    variants = [
        ("lgb_huber_generated_meta_search_external", "huber", unique(fs["generated_all"] + META_ALL + search_context_features() + external_core_features()), "LightGBM Huber objective on generated/search/external features"),
        ("lgb_mape_generated_meta_search_external", "mape", unique(fs["generated_all"] + META_ALL + search_context_features() + external_core_features()), "LightGBM MAPE objective on generated/search/external features"),
        ("lgb_l1_medium_size_meta_external", "regression_l1", unique(fs["medium_size"] + META_ALL + external_core_features()), "LightGBM L1 objective on medium-size/external features"),
    ]
    for name, objective, features, hypothesis in variants:
        train, val, test = load_cold_full(features, search_df)
        pred = fit_predict("lightgbm", objective, train, val, test, features)
        maps.append({
            "experiment_id": "PP-Y4",
            "candidate": name,
            "model": "lightgbm",
            "loss_or_objective": objective,
            "feature_strategy": hypothesis,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            metric_frame = frame[["_track6_row_id", "ln_price_krw", "price_krw"]].rename(columns={"ln_price_krw": "actual_log", "price_krw": "actual_price"})
            add_metric(rows, "PP-Y4", name, split, metric_frame, pred[split], "cold_lgb_feature_swap_objective", {
                "model": "lightgbm",
                "loss_or_objective": objective,
                "n_features": len(features),
            })
            preds.append(prediction_frame("PP-Y4", name, split, frame, pred[split], "cold_lgb_feature_swap_objective", {
                "model": "lightgbm",
                "loss_or_objective": objective,
                "n_features": len(features),
            }))
    return rows, preds, maps


def route_by_score(exp_id: str, stable_label: str, risk_label: str, score_col: str, thresholds: np.ndarray, direction: str, policy: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for threshold in thresholds:
        candidate = f"route_{stable_label}_to_{risk_label}_{score_col}_{direction}_{threshold:.3f}"
        maps.append({
            "experiment_id": exp_id,
            "candidate": candidate,
            "stable_source": stable_label,
            "risk_source": risk_label,
            "score_col": score_col,
            "threshold": float(threshold),
            "direction": direction,
        })
        for split in ["validation", "test"]:
            merged = merge_sources([stable_label, risk_label], split)
            score = pd.to_numeric(merged[score_col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
            use_stable = score >= threshold if direction == "gte" else score <= threshold
            final = np.where(use_stable, merged[f"{stable_label}_pred"].to_numpy(dtype=float), merged[f"{risk_label}_pred"].to_numpy(dtype=float))
            add_metric(rows, exp_id, candidate, split, merged, final, policy, {
                "stable_source": stable_label,
                "risk_source": risk_label,
                "threshold": float(threshold),
                "stable_rate": float(use_stable.mean()),
            })
            preds.append(policy_prediction_frame(exp_id, candidate, split, merged, final, policy, np.where(use_stable, stable_label, risk_label)))
    return rows, preds, maps


def run_y5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(["y2_search_external_interaction", "h9_search_p95"], "validation")
    score = (
        pd.to_numeric(val.get("y2_search_external_interaction_search_quality_score", 0.0), errors="coerce").fillna(0.0)
        + 0.35 * pd.to_numeric(val.get("y2_search_external_interaction_gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
        + 0.15 * pd.to_numeric(val.get("y2_search_external_interaction_artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0)
    )
    val["feature_quality_score"] = score
    thresholds = np.quantile(score, [0.33, 0.50, 0.66, 0.80])
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for risk_label in ["h9_search_p95", "w4_p95"]:
        for threshold in thresholds:
            candidate = f"route_y2_by_feature_quality_to_{risk_label}_{threshold:.3f}"
            maps.append({
                "experiment_id": "PP-Y5",
                "candidate": candidate,
                "stable_source": "y2_search_external_interaction",
                "risk_source": risk_label,
                "threshold": float(threshold),
                "score": "search_quality_score + 0.35*gallery_available + 0.15*exhibition_available_count",
            })
            for split in ["validation", "test"]:
                merged = merge_sources(["y2_search_external_interaction", risk_label], split)
                merged["feature_quality_score"] = (
                    pd.to_numeric(merged.get("y2_search_external_interaction_search_quality_score", 0.0), errors="coerce").fillna(0.0)
                    + 0.35 * pd.to_numeric(merged.get("y2_search_external_interaction_gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
                    + 0.15 * pd.to_numeric(merged.get("y2_search_external_interaction_artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0)
                )
                use_stable = merged["feature_quality_score"].to_numpy(dtype=float) >= float(threshold)
                final = np.where(use_stable, merged["y2_search_external_interaction_pred"].to_numpy(dtype=float), merged[f"{risk_label}_pred"].to_numpy(dtype=float))
                add_metric(rows, "PP-Y5", candidate, split, merged, final, "feature_quality_routing", {
                    "threshold": float(threshold),
                    "risk_source": risk_label,
                    "stable_rate": float(use_stable.mean()),
                })
                preds.append(policy_prediction_frame("PP-Y5", candidate, split, merged, final, "feature_quality_routing", np.where(use_stable, "y2_search_external_interaction", risk_label)))
    return rows, preds, maps


def run_y9(search_df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    fs = base_feature_sets()
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    candidates = [
        ("generated_search_external", unique(fs["generated_all"] + META_ALL + search_context_features() + external_core_features())),
        ("support_size_search_external", unique(fs["cold_lgb"] + META_ALL + search_context_features() + external_core_features())),
        ("medium_size_external", unique(fs["medium_size"] + META_ALL + external_core_features())),
    ]
    objectives = ["regression", "regression_l1", "huber", "mape", "quantile"]
    for feature_name, features in candidates:
        train, val, test = load_cold_full(features, search_df)
        for objective in objectives:
            name = f"lgb_{objective}_{feature_name}"
            pred = fit_predict("lightgbm", objective, train, val, test, features)
            maps.append({
                "experiment_id": "PP-Y9",
                "candidate": name,
                "model": "lightgbm",
                "loss_or_objective": objective,
                "feature_strategy": feature_name,
                "n_features": len(features),
                "features": ", ".join(features),
            })
            for split, frame in [("validation", val), ("test", test)]:
                metric_frame = frame[["_track6_row_id", "ln_price_krw", "price_krw"]].rename(columns={"ln_price_krw": "actual_log", "price_krw": "actual_price"})
                add_metric(rows, "PP-Y9", name, split, metric_frame, pred[split], "cold_objective_custom_closure", {
                    "model": "lightgbm",
                    "loss_or_objective": objective,
                    "feature_strategy": feature_name,
                    "n_features": len(features),
                })
                preds.append(prediction_frame("PP-Y9", name, split, frame, pred[split], "cold_objective_custom_closure", {
                    "model": "lightgbm",
                    "loss_or_objective": objective,
                    "feature_strategy": feature_name,
                    "n_features": len(features),
                }))
    return rows, preds, maps


def run_y11() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    labels = ["y1_external_interaction", "y2_search_external_interaction", "y6_lgbq_cat_resid", "y10_mdape_route", "y10_p95_route", "h9_search_p95", "w4_p95"]
    train_frame = merge_sources(labels, "validation")
    test_frame = merge_sources(labels, "test")
    pred_cols = [f"{label}_pred" for label in labels]
    for frame in [train_frame, test_frame]:
        frame["pred_mean"] = frame[pred_cols].mean(axis=1)
        frame["pred_std"] = frame[pred_cols].std(axis=1)
        frame["pred_min"] = frame[pred_cols].min(axis=1)
        frame["pred_max"] = frame[pred_cols].max(axis=1)
    features = pred_cols + ["pred_mean", "pred_std", "pred_min", "pred_max"]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    y = train_frame["actual_log"].to_numpy(dtype=float)
    models: list[tuple[str, Any]] = [
        ("ridge_10", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))])),
        ("huber", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))])),
    ]
    for name, model in models:
        model.fit(train_frame[features], y)
        for split, frame in [("validation", train_frame), ("test", test_frame)]:
            raw = np.asarray(model.predict(frame[features]), dtype=float)
            clipped = np.clip(raw, frame["pred_min"].to_numpy(dtype=float), frame["pred_max"].to_numpy(dtype=float))
            for suffix, pred in [("raw", raw), ("component_range_clipped", clipped)]:
                candidate = f"{name}_validation_meta_{suffix}"
                add_metric(rows, "PP-Y11", candidate, split, frame, pred, "validation_meta_stacking_closure", {
                    "meta_model": name,
                    "clipped": suffix == "component_range_clipped",
                })
                preds.append(policy_prediction_frame("PP-Y11", candidate, split, frame, pred, "validation_meta_stacking_closure", name))
        maps.append({
            "experiment_id": "PP-Y11",
            "meta_model": name,
            "source_labels": ", ".join(labels),
            "feature_columns": ", ".join(features),
            "note": "Validation-trained meta stacking closure; final OOF meta should be run separately before production selection.",
        })
    return rows, preds, maps


def run_y12() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    # Use external-rich model only when external information exists; otherwise p95 fallback.
    labels = ["y1_external_interaction", "h9_search_p95", "w4_p95"]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for risk_label in ["h9_search_p95", "w4_p95"]:
        for min_exh in [1, 2, 3]:
            candidate = f"external_available_minexh{min_exh}_else_{risk_label}"
            maps.append({"experiment_id": "PP-Y12", "candidate": candidate, "risk_source": risk_label, "min_exhibition_available": min_exh})
            for split in ["validation", "test"]:
                merged = merge_sources(["y1_external_interaction", risk_label], split)
                gallery = pd.to_numeric(merged.get("y1_external_interaction_gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0).to_numpy()
                exhibition = pd.to_numeric(merged.get("y1_external_interaction_artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0).to_numpy()
                use_external = (gallery > 0) | (exhibition >= min_exh)
                final = np.where(use_external, merged["y1_external_interaction_pred"].to_numpy(dtype=float), merged[f"{risk_label}_pred"].to_numpy(dtype=float))
                add_metric(rows, "PP-Y12", candidate, split, merged, final, "external_availability_routing", {"stable_rate": float(use_external.mean())})
                preds.append(policy_prediction_frame("PP-Y12", candidate, split, merged, final, "external_availability_routing", np.where(use_external, "y1_external_interaction", risk_label)))
    return rows, preds, maps


def run_y13() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(["y2_search_external_interaction", "w4_p95"], "validation")
    score_col = "y2_search_external_interaction_search_quality_score"
    thresholds = np.quantile(pd.to_numeric(val[score_col], errors="coerce").fillna(0.0), [0.25, 0.50, 0.75])
    return route_by_score("PP-Y13", "y2_search_external_interaction", "w4_p95", score_col, thresholds, "gte", "search_quality_fallback")


def run_y14() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    # Price bin routing uses predicted log price from the stable model only.
    labels = ["y2_search_external_interaction", "y10_mdape_route", "y10_p95_route"]
    val = merge_sources(labels, "validation")
    pred = val["y2_search_external_interaction_pred"].to_numpy(dtype=float)
    edges = np.quantile(pred, [0.33, 0.66])
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    policies = [
        ("low_y10p95_mid_y10mdape_high_y2", ["y10_p95_route", "y10_mdape_route", "y2_search_external_interaction"]),
        ("low_y2_mid_y10mdape_high_y10p95", ["y2_search_external_interaction", "y10_mdape_route", "y10_p95_route"]),
        ("low_y10mdape_mid_y2_high_y10p95", ["y10_mdape_route", "y2_search_external_interaction", "y10_p95_route"]),
    ]
    for candidate, order in policies:
        maps.append({"experiment_id": "PP-Y14", "candidate": candidate, "low_source": order[0], "mid_source": order[1], "high_source": order[2], "edge_low_mid": float(edges[0]), "edge_mid_high": float(edges[1])})
        for split in ["validation", "test"]:
            merged = merge_sources(labels, split)
            base_pred = merged["y2_search_external_interaction_pred"].to_numpy(dtype=float)
            low = base_pred <= edges[0]
            high = base_pred > edges[1]
            mid = ~(low | high)
            final = np.zeros(len(merged), dtype=float)
            selected = np.empty(len(merged), dtype=object)
            for mask, label in [(low, order[0]), (mid, order[1]), (high, order[2])]:
                final[mask] = merged.loc[mask, f"{label}_pred"].to_numpy(dtype=float)
                selected[mask] = label
            add_metric(rows, "PP-Y14", candidate, split, merged, final, "pred_price_bin_model_selection", {"edge_low_mid": float(edges[0]), "edge_mid_high": float(edges[1])})
            preds.append(policy_prediction_frame("PP-Y14", candidate, split, merged, final, "pred_price_bin_model_selection", selected))
    return rows, preds, maps


def run_y15() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    source_label = "y2_search_external_interaction"
    val = source_prediction(source_label, "validation")
    test = source_prediction(source_label, "test")
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for frame in [val, test]:
        frame["pred_bin"] = pd.qcut(frame["pred_log"], q=5, labels=[f"p{i}" for i in range(5)], duplicates="drop").astype(str)
        frame["qwidth_bin"] = pd.qcut(frame["quantile_width_log"], q=4, labels=[f"w{i}" for i in range(4)], duplicates="drop").astype(str)
        frame["external_info_bin"] = np.where(
            (pd.to_numeric(frame.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0) > 0)
            | (pd.to_numeric(frame.get("artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0) >= 2),
            "external_present",
            "external_sparse",
        )
    segment_sets = {
        "pred_bin": ["pred_bin"],
        "qwidth_bin": ["qwidth_bin"],
        "pred_x_qwidth": ["pred_bin", "qwidth_bin"],
        "external_x_qwidth": ["external_info_bin", "qwidth_bin"],
    }
    for segment_name, cols in segment_sets.items():
        val_seg = val.copy()
        test_seg = test.copy()
        val_seg["segment"] = val_seg[cols].astype(str).agg("__".join, axis=1)
        test_seg["segment"] = test_seg[cols].astype(str).agg("__".join, axis=1)
        corr = val_seg.groupby("segment").agg(n=("residual_log", "size"), median_residual=("residual_log", "median")).reset_index()
        global_corr = float(val_seg["residual_log"].median())
        for min_rows in [30, 50, 100, 150]:
            for cap in [0.10, 0.15, 0.25, 0.35]:
                candidate = f"{source_label}_{segment_name}_min{min_rows}_cap{cap:g}"
                maps.append({"experiment_id": "PP-Y15", "candidate": candidate, "source": source_label, "segment": segment_name, "min_rows": min_rows, "cap": cap})
                for split, frame in [("validation", val_seg), ("test", test_seg)]:
                    mapped = frame.merge(corr, on="segment", how="left")
                    residual = mapped["median_residual"].where(mapped["n"].fillna(0) >= min_rows, global_corr)
                    correction = np.clip(residual.to_numpy(dtype=float), -cap, cap)
                    final = mapped["pred_log"].to_numpy(dtype=float) + correction
                    metric_frame = mapped[["_track6_row_id", "actual_log", "actual_price"]]
                    add_metric(rows, "PP-Y15", candidate, split, metric_frame, final, "segment_min_rows_cap_calibration", {
                        "segment": segment_name,
                        "min_rows": min_rows,
                        "cap": cap,
                    })
                    preds.append(policy_prediction_frame("PP-Y15", candidate, split, mapped, final, "segment_min_rows_cap_calibration", source_label, {"segment": segment_name, "min_rows": min_rows, "cap": cap}))
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
        "- 목적: Cold 추가 실험 여지를 줄이기 위해 남은 피처/목적함수/라우팅/보정 축을 닫는다.",
        "- 기준: 기존 split과 기존 PP-Y 강한 후보를 유지하고 validation/test를 함께 기록한다.",
        "",
    ]
    test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines += [
        "## Test 결과 상위",
        "",
        "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in test.head(20).itertuples():
        lines.append(f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | `{row.policy}` |")
    lines += ["", "## 설정/피처 맵", "", markdown_table(map_df.head(120))]
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
    config = {"experiment_id": exp_id, "title": info["title"], "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"), "seed": SEED, "target": "ln_price_krw"}
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")
    metrics_df["folder"] = str(exp_dir.relative_to(REPO))
    return metrics_df


def update_unified_summary(closure: pd.DataFrame) -> None:
    if PRIOR_SUMMARY.exists():
        prior = pd.read_csv(PRIOR_SUMMARY, low_memory=False)
        combined = pd.concat([prior, closure], ignore_index=True, sort=False)
        combined = combined.drop_duplicates(["experiment_id", "candidate", "split", "policy"], keep="last")
        combined.to_csv(PRIOR_SUMMARY, index=False)
    closure.to_csv(CLOSURE_SUMMARY, index=False)


def main() -> None:
    start = time.time()
    search_df = load_search_df()
    summary_frames: list[pd.DataFrame] = []

    for exp_id, fn in [
        ("PP-Y4", lambda: run_y4(search_df)),
        ("PP-Y5", run_y5),
        ("PP-Y9", lambda: run_y9(search_df)),
        ("PP-Y11", run_y11),
        ("PP-Y12", run_y12),
        ("PP-Y13", run_y13),
        ("PP-Y14", run_y14),
        ("PP-Y15", run_y15),
    ]:
        rows, preds, maps = fn()
        summary_frames.append(write_exp(exp_id, rows, preds, maps))

    closure = pd.concat(summary_frames, ignore_index=True)
    update_unified_summary(closure)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "closure_summary": str(CLOSURE_SUMMARY.relative_to(REPO)),
        "unified_summary": str(PRIOR_SUMMARY.relative_to(REPO)),
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
