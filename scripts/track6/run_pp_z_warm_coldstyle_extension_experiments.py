#!/usr/bin/env python3
"""Run PP-Z Warm cold-style feature/model extension experiments.

PP-W/X/Y expanded Cold with artist metadata, exhibition/gallery, search
features, LightGBM Quantile, and CatBoost. PP-Z applies the same axes to Warm
while keeping the current Track6 Warm split fixed.
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
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    BASE_NUMERIC,
    GENERATED,
    REPO,
    SEED,
    artifact_features,
    load_scope,
    metrics,
)
from run_pp_h_search_pilot_experiments import (  # noqa: E402
    SEARCH_CATEGORICAL,
    SEARCH_CONTEXT_FEATURES,
    SEARCH_FEATURE_PATH,
    SEARCH_NUMERIC,
    add_search_features,
)
from run_pp_w_experiments import (  # noqa: E402
    META_ALL,
    META_CATEGORICAL,
    META_NUMERIC,
    add_artist_meta,
)
from run_pp_x_gallery_exhibition_revalidation import (  # noqa: E402
    EXTERNAL_ALL,
    EXTERNAL_CATEGORICAL,
    EXTERNAL_INTERACTIONS_CATEGORICAL,
    EXTERNAL_INTERACTIONS_NUMERIC,
    EXTERNAL_JOIN_COLUMNS,
    EXTERNAL_NUMERIC,
    SPLIT_ROOT,
    engineer_external_features,
    engineer_external_interactions,
    load_raw_external_map,
    load_validated_gallery_map,
)


EXPERIMENTS = {
    "PP-Z1": {
        "slug": "PP-Z1_warm_huber_coldstyle_feature_expansion",
        "title": "Warm Huber Cold형 확장 피처 재학습",
    },
    "PP-Z2": {
        "slug": "PP-Z2_warm_lightgbm_quantile_coldstyle_feature_expansion",
        "title": "Warm LightGBM Quantile Cold형 확장 피처 재학습",
    },
    "PP-Z3": {
        "slug": "PP-Z3_warm_catboost_coldstyle_feature_expansion",
        "title": "Warm CatBoost Cold형 확장 피처 재학습",
    },
    "PP-Z4": {
        "slug": "PP-Z4_warm_lgbq_qwidth_segment_calibration",
        "title": "Warm LightGBM Quantile q-width 구간 보정",
    },
}

SUMMARY_PATH = BASE_EXP_DIR / "PP-Z_warm_coldstyle_extension_summary_metrics.csv"

EXTRA_WARM_NUMERIC = [
    "artist_works_log",
    "artist_works_count_train",
]
NUMERIC_FEATURES = set(
    BASE_NUMERIC
    + EXTRA_WARM_NUMERIC
    + META_NUMERIC
    + EXTERNAL_NUMERIC
    + SEARCH_NUMERIC
)
SEARCH_ALL = SEARCH_NUMERIC + SEARCH_CATEGORICAL
EXTERNAL_CORE = [c for c in EXTERNAL_ALL if c not in set(EXTERNAL_INTERACTIONS_NUMERIC + EXTERNAL_INTERACTIONS_CATEGORICAL)]
SEARCH_INTERACTIONS = [
    "search_quality_x_log_area",
    "search_art_match_x_followers_log",
    "search_exhibition_x_career_stage",
    "search_size_quality_bucket",
]
ADDED_FEATURES = set(META_ALL + EXTERNAL_ALL + SEARCH_ALL + SEARCH_INTERACTIONS)


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def split_file(split: str) -> Path:
    return SPLIT_ROOT / f"track6_{split}.csv"


def warm_external_row_map() -> pd.DataFrame:
    frames = []
    for split in ["train", "val_warm", "test_warm"]:
        df = pd.read_csv(
            split_file(split),
            usecols=["_track6_row_id", "track4_source", "track4_source_row_index"],
            low_memory=False,
        )
        df["split_source"] = split
        frames.append(df)
    source = pd.concat(frames, ignore_index=True)
    source["track4_source_row_index"] = pd.to_numeric(source["track4_source_row_index"], errors="coerce").astype("Int64")
    source = source.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    source["track4_source_row_index"] = source["track4_source_row_index"].astype(int)
    source = source.drop_duplicates("_track6_row_id", keep="first")
    out = source.merge(load_raw_external_map(), on=["track4_source", "track4_source_row_index"], how="left")
    out = out.merge(load_validated_gallery_map(), on=["track4_source", "track4_source_row_index"], how="left")
    out = engineer_external_features(out)
    return out[["_track6_row_id", *EXTERNAL_JOIN_COLUMNS]]


def add_warm_external_features(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    ext = warm_external_row_map()
    out_frames: list[pd.DataFrame] = []
    for frame in frames:
        out = frame.merge(ext, on="_track6_row_id", how="left")
        for col in EXTERNAL_NUMERIC:
            if col not in out.columns:
                out[col] = np.nan
            out[col] = pd.to_numeric(out[col], errors="coerce")
        for col in EXTERNAL_CATEGORICAL:
            if col not in out.columns:
                out[col] = "__MISSING__"
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
        out = engineer_external_interactions(out)
        out_frames.append(out)
    return out_frames


def load_search_features() -> pd.DataFrame:
    if not SEARCH_FEATURE_PATH.exists():
        return pd.DataFrame(columns=["artist_search_name", *SEARCH_ALL])
    return pd.read_csv(SEARCH_FEATURE_PATH, low_memory=False)


def load_warm_full(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_required = [feature for feature in features if feature not in ADDED_FEATURES]
    train, val, test = load_scope("warm", base_required)
    train, val, test = add_artist_meta([train, val, test])
    train, val, test = add_warm_external_features([train, val, test])
    train, val, test = add_search_features([train, val, test], load_search_features())
    return train, val, test


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [col for col in features if col in NUMERIC_FEATURES]
    categorical = [col for col in features if col not in numeric]
    return numeric, categorical


def normalize_frame(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
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


def huber_model(features: list[str]) -> Pipeline:
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


def lgbm_quantile_model(features: list[str], alpha: float) -> Pipeline:
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
            n_estimators=450,
            learning_rate=0.035,
            num_leaves=31,
            min_child_samples=35,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.2,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def catboost_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function="RMSE",
        iterations=550,
        learning_rate=0.035,
        depth=6,
        l2_leaf_reg=8.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "ln_price_krw", "price_krw"]]


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(metric_frame(frame), pred_log)


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        **metric_values(frame, pred_log),
    }
    if "search_collected_flag" in frame.columns:
        covered_mask = frame["search_collected_flag"].to_numpy(dtype=float) > 0
        row["search_coverage_rate"] = float(frame["search_collected_flag"].mean())
        row["search_covered_n"] = int(covered_mask.sum())
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def feature_candidates() -> dict[str, tuple[str, list[str], str]]:
    features = artifact_features()
    warm_base = features["warm"]
    warm_base_with_artist_volume = unique(warm_base + ["artist_works_log", "artist_works_count_train"])
    external_interactions = EXTERNAL_INTERACTIONS_NUMERIC + EXTERNAL_INTERACTIONS_CATEGORICAL
    return {
        "baseline_warm_base_existing_combo": (
            "Warm final artifact 기준 피처셋",
            warm_base,
            "현재 Warm Huber와 동일한 기준선",
        ),
        "warm_base_artist_volume": (
            "Warm 기준 + 작가 학습량",
            warm_base_with_artist_volume,
            "작가 이력이 있는 Warm에서 작가별 표본 수가 안정성 신호가 되는지 확인",
        ),
        "warm_base_artist_meta_all": (
            "Warm 기준 + 작가 메타 전체",
            unique(warm_base_with_artist_volume + META_ALL),
            "Cold PP-W에서 검증한 작가 활동/인지도/국적 피처가 Warm에도 추가 설명력을 주는지 확인",
        ),
        "warm_base_exhibition_gallery": (
            "Warm 기준 + 전시/갤러리",
            unique(warm_base_with_artist_volume + EXTERNAL_CORE),
            "작가 이력이 있어도 전시 활동과 갤러리 tier가 가격 기준선을 보완하는지 확인",
        ),
        "warm_base_external_interaction": (
            "Warm 기준 + 전시/갤러리 상호작용",
            unique(warm_base_with_artist_volume + META_ALL + EXTERNAL_CORE + external_interactions),
            "전시/갤러리 효과가 크기, 팔로워, 작가 경력과 결합될 때 개선되는지 확인",
        ),
        "warm_base_search_context": (
            "Warm 기준 + 검색 핵심 문맥",
            unique(warm_base_with_artist_volume + META_ALL + SEARCH_CONTEXT_FEATURES),
            "검색 품질/전시 문맥이 이미 학습 이력이 있는 작가에서도 추가 신호인지 확인",
        ),
        "warm_base_search_all": (
            "Warm 기준 + 검색 전체",
            unique(warm_base_with_artist_volume + META_ALL + SEARCH_ALL),
            "검색 노출량, 문맥, 동명이인 위험 전체를 Warm에 넣었을 때 과적합 없이 개선되는지 확인",
        ),
        "warm_base_meta_external_search_all": (
            "Warm 기준 + 작가 메타 + 전시/갤러리 + 검색 전체",
            unique(warm_base_with_artist_volume + META_ALL + EXTERNAL_ALL + SEARCH_ALL),
            "Cold식 확장 피처 전체를 Warm에 이식했을 때 모델별로 감당 가능한지 확인",
        ),
    }


def fit_huber(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    train = normalize_frame(train, features)
    val = normalize_frame(val, features)
    test = normalize_frame(test, features)
    model = huber_model(features)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def fit_lgbm_quantile(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, dict[str, np.ndarray]]:
    train = normalize_frame(train, features)
    val = normalize_frame(val, features)
    test = normalize_frame(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, dict[str, np.ndarray]] = {"validation": {}, "test": {}}
    for name, alpha in [("q10", 0.10), ("q50", 0.50), ("q90", 0.90)]:
        model = lgbm_quantile_model(features, alpha)
        model.fit(train[features], y)
        out["validation"][name] = np.asarray(model.predict(val[features]), dtype=float)
        out["test"][name] = np.asarray(model.predict(test[features]), dtype=float)
    for split in ["validation", "test"]:
        q10 = np.minimum(out[split]["q10"], out[split]["q90"])
        q90 = np.maximum(out[split]["q10"], out[split]["q90"])
        out[split]["q10"] = q10
        out[split]["q90"] = q90
        out[split]["qwidth"] = q90 - q10
    return out


def fit_catboost(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    train = normalize_frame(train, features)
    val = normalize_frame(val, features)
    test = normalize_frame(test, features)
    model = catboost_model()
    model.fit(cat_ready(train, features), train["ln_price_krw"].to_numpy(dtype=float), cat_features=cat_indices(features))
    return {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def run_direct_models() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]], dict[str, Any]]:
    candidates = feature_candidates()
    all_features = unique([feature for _name, (_strategy, features, _hypothesis) in candidates.items() for feature in features])
    train, val, test = load_warm_full(all_features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    lgbq_predictions: dict[str, Any] = {"validation_frame": val, "test_frame": test, "items": {}}

    for candidate, (strategy, features, hypothesis) in candidates.items():
        direct_specs = [
            ("PP-Z1", "huber", "Huber", "warm_huber_coldstyle_feature_expansion"),
            ("PP-Z2", "lightgbm_quantile", "LightGBM Quantile", "warm_lightgbm_quantile_coldstyle_feature_expansion"),
            ("PP-Z3", "catboost", "CatBoost RMSE", "warm_catboost_coldstyle_feature_expansion"),
        ]
        for exp_id, model_key, model_label, policy in direct_specs:
            start = time.time()
            if model_key == "huber":
                pred = fit_huber(train, val, test, features)
                split_preds = {
                    "validation": {"pred_log": pred["validation"]},
                    "test": {"pred_log": pred["test"]},
                }
            elif model_key == "lightgbm_quantile":
                quant = fit_lgbm_quantile(train, val, test, features)
                split_preds = {
                    "validation": {
                        "pred_log": quant["validation"]["q50"],
                        "q10_log": quant["validation"]["q10"],
                        "q90_log": quant["validation"]["q90"],
                        "qwidth_log": quant["validation"]["qwidth"],
                    },
                    "test": {
                        "pred_log": quant["test"]["q50"],
                        "q10_log": quant["test"]["q10"],
                        "q90_log": quant["test"]["q90"],
                        "qwidth_log": quant["test"]["qwidth"],
                    },
                }
                lgbq_predictions["items"][candidate] = {
                    "strategy": strategy,
                    "features": features,
                    "hypothesis": hypothesis,
                    "validation_pred": quant["validation"],
                    "test_pred": quant["test"],
                }
            else:
                pred = fit_catboost(train, val, test, features)
                split_preds = {
                    "validation": {"pred_log": pred["validation"]},
                    "test": {"pred_log": pred["test"]},
                }

            maps.append({
                "experiment_id": exp_id,
                "candidate": candidate,
                "model": model_label,
                "feature_strategy": strategy,
                "hypothesis": hypothesis,
                "n_features": len(features),
                "features": ", ".join(features),
                "runtime_sec": round(time.time() - start, 3),
            })
            for split, frame in [("validation", val), ("test", test)]:
                values = split_preds[split]
                add_metric(rows, exp_id, candidate, split, frame, values["pred_log"], policy, {
                    "model": model_label,
                    "feature_strategy": strategy,
                    "n_features": len(features),
                })
                extra = {
                    "model": model_label,
                    "feature_strategy": strategy,
                    "n_features": len(features),
                }
                for key in ["q10_log", "q90_log", "qwidth_log"]:
                    if key in values:
                        extra[key] = values[key]
                preds.append(prediction_frame(exp_id, candidate, split, frame, values["pred_log"], policy, extra))
    return rows, preds, maps, lgbq_predictions


def fit_edges(values: np.ndarray, q: int = 3) -> np.ndarray | None:
    clean = pd.Series(values).replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
    if clean.size == 0:
        return None
    quantiles = np.linspace(0.0, 1.0, q + 1)
    edges = np.unique(np.nanquantile(clean, quantiles))
    if len(edges) < 2:
        return None
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def apply_edges(values: np.ndarray, edges: np.ndarray | None, prefix: str) -> pd.Series:
    if edges is None:
        return pd.Series([f"{prefix}_all"] * len(values), dtype="string")
    labels = [f"{prefix}_{idx + 1}" for idx in range(len(edges) - 1)]
    return pd.cut(values, bins=edges, labels=labels, include_lowest=True).astype("string").fillna(f"{prefix}_missing")


def segment_frame(frame: pd.DataFrame, pred_log: np.ndarray, qwidth: np.ndarray, pred_edges: np.ndarray | None, qwidth_edges: np.ndarray | None) -> pd.DataFrame:
    out = pd.DataFrame({
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "qwidth_log": qwidth,
        "size_bucket": frame.get("size_bucket", pd.Series("__MISSING__", index=frame.index)).astype(str).to_numpy(),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["pred_bin"] = apply_edges(pred_log, pred_edges, "pred")
    out["qwidth_bin"] = apply_edges(qwidth, qwidth_edges, "qwidth")
    out["pred_x_qwidth"] = out["pred_bin"].astype(str) + "__" + out["qwidth_bin"].astype(str)
    out["size_x_qwidth"] = out["size_bucket"].astype(str) + "__" + out["qwidth_bin"].astype(str)
    return out


def build_correction_map(seg: pd.DataFrame, segment_col: str, min_rows: int, cap: float) -> tuple[dict[str, float], float, pd.DataFrame]:
    grouped = seg.groupby(segment_col, dropna=False)["residual_log"].agg(["count", "median"]).reset_index()
    usable = grouped[grouped["count"].ge(min_rows)].copy()
    usable["correction"] = usable["median"].clip(lower=-cap, upper=cap)
    correction_map = dict(zip(usable[segment_col].astype(str), usable["correction"].astype(float), strict=False))
    fallback = float(np.clip(seg["residual_log"].median(), -cap, cap))
    usable["segment_col"] = segment_col
    usable["min_rows"] = min_rows
    usable["cap"] = cap
    usable["fallback_correction"] = fallback
    return correction_map, fallback, usable


def apply_correction(seg: pd.DataFrame, segment_col: str, correction_map: dict[str, float], fallback: float) -> np.ndarray:
    correction = seg[segment_col].astype(str).map(correction_map).fillna(fallback).to_numpy(dtype=float)
    return seg["pred_log"].to_numpy(dtype=float) + correction


def run_qwidth_calibration(lgbq_predictions: dict[str, Any]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = lgbq_predictions["validation_frame"]
    test = lgbq_predictions["test_frame"]
    items = lgbq_predictions["items"]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    if not items:
        return rows, preds, maps

    candidate_scores = []
    for candidate, item in items.items():
        pred = item["validation_pred"]["q50"]
        candidate_scores.append((metric_values(val, pred)["MdAPE"], candidate))
    _score, base_candidate = sorted(candidate_scores)[0]
    item = items[base_candidate]
    val_pred = item["validation_pred"]["q50"]
    test_pred = item["test_pred"]["q50"]
    val_qwidth = item["validation_pred"]["qwidth"]
    test_qwidth = item["test_pred"]["qwidth"]
    pred_edges = fit_edges(val_pred, q=3)
    qwidth_edges = fit_edges(val_qwidth, q=3)
    val_seg = segment_frame(val, val_pred, val_qwidth, pred_edges, qwidth_edges)
    test_seg = segment_frame(test, test_pred, test_qwidth, pred_edges, qwidth_edges)

    for split, frame, pred_log in [("validation", val, val_pred), ("test", test, test_pred)]:
        add_metric(rows, "PP-Z4", f"base_{base_candidate}", split, frame, pred_log, "warm_lgbq_qwidth_segment_base", {
            "base_candidate": base_candidate,
            "model": "LightGBM Quantile",
            "segment_col": "none",
            "min_rows": 0,
            "cap": 0.0,
        })
        preds.append(prediction_frame("PP-Z4", f"base_{base_candidate}", split, frame, pred_log, "warm_lgbq_qwidth_segment_base", {
            "base_candidate": base_candidate,
            "model": "LightGBM Quantile",
            "segment_col": "none",
            "min_rows": 0,
            "cap": 0.0,
        }))

    for segment_col in ["qwidth_bin", "pred_bin", "pred_x_qwidth", "size_x_qwidth"]:
        for min_rows in [30, 50, 80]:
            for cap in [0.05, 0.10, 0.15, 0.25]:
                correction_map, fallback, map_df = build_correction_map(val_seg, segment_col, min_rows, cap)
                candidate = f"{base_candidate}__{segment_col}_min{min_rows}_cap{cap:g}"
                corrected_val = apply_correction(val_seg, segment_col, correction_map, fallback)
                corrected_test = apply_correction(test_seg, segment_col, correction_map, fallback)
                maps.append({
                    "experiment_id": "PP-Z4",
                    "candidate": candidate,
                    "base_candidate": base_candidate,
                    "segment_col": segment_col,
                    "min_rows": min_rows,
                    "cap": cap,
                    "fallback_correction": fallback,
                    "n_segments": int(len(map_df)),
                    "correction_detail": map_df.to_json(orient="records", force_ascii=False),
                })
                for split, frame, pred_log in [("validation", val, corrected_val), ("test", test, corrected_test)]:
                    add_metric(rows, "PP-Z4", candidate, split, frame, pred_log, "warm_lgbq_qwidth_segment_calibration", {
                        "base_candidate": base_candidate,
                        "model": "LightGBM Quantile",
                        "segment_col": segment_col,
                        "min_rows": min_rows,
                        "cap": cap,
                    })
                    preds.append(prediction_frame("PP-Z4", candidate, split, frame, pred_log, "warm_lgbq_qwidth_segment_calibration", {
                        "base_candidate": base_candidate,
                        "model": "LightGBM Quantile",
                        "segment_col": segment_col,
                        "min_rows": min_rows,
                        "cap": cap,
                    }))
    return rows, preds, maps


def render_report(exp_id: str, info: dict[str, str], metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    best_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(10)
    best_val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(10)
    best_val_text = best_val.to_csv(index=False)
    best_test_text = best_test.to_csv(index=False)
    md = f"""# {exp_id} {info['title']}

## 목적
- Cold에서 사용한 작가 메타, 전시/갤러리, 검색 피처와 트리/분위수 모델 축을 Warm에 적용해 개선 여지가 있는지 확인한다.
- Track6 Warm split은 고정하고, 보정값과 후보 선택은 validation 기준으로만 판단한다.

## Validation Top 10
```csv
{best_val_text}```

## Test Top 10
```csv
{best_test_text}```

## 산출물
- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/policy_map.csv`
"""
    style = "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:28px;color:#17202a}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #d8dee9;padding:7px;text-align:left}th{background:#eef2f7}h1,h2{margin-top:22px}"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title><style>{style}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1>
<h2>Validation Top 10</h2>{best_val.to_html(index=False, escape=True)}
<h2>Test Top 10</h2>{best_test.to_html(index=False, escape=True)}
<h2>Policy / Feature Map</h2>{map_df.head(200).to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], preds: list[pd.DataFrame], maps: list[dict[str, Any]]) -> pd.DataFrame:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame([row for row in rows if row["experiment_id"] == exp_id])
    pred_parts = [frame for frame in preds if not frame.empty and frame["experiment_id"].eq(exp_id).any()]
    pred_df = pd.concat(pred_parts, ignore_index=True) if pred_parts else pd.DataFrame()
    if not pred_df.empty:
        pred_df = pred_df[pred_df["experiment_id"].eq(exp_id)].copy()
    map_df = pd.DataFrame([row for row in maps if row["experiment_id"] == exp_id])
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "policy_map.csv", index=False)
    if not pred_df.empty:
        pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
        pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "scope": "warm",
        "summary_path": str(SUMMARY_PATH.relative_to(REPO)),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, info, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")
    return metrics_df


def main() -> None:
    start = time.time()
    rows, preds, maps, lgbq_predictions = run_direct_models()
    q_rows, q_preds, q_maps = run_qwidth_calibration(lgbq_predictions)
    rows.extend(q_rows)
    preds.extend(q_preds)
    maps.extend(q_maps)
    summary_frames = []
    for exp_id in EXPERIMENTS:
        summary_frames.append(write_exp(exp_id, rows, preds, maps))
    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(SUMMARY_PATH, index=False)
    print(json.dumps({
        "status": "ok",
        "summary": str(SUMMARY_PATH.relative_to(REPO)),
        "experiments": list(EXPERIMENTS),
        "rows": int(len(summary)),
        "runtime_sec": round(time.time() - start, 3),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
