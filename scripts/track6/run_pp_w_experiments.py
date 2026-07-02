#!/usr/bin/env python3
"""Run Track6 PP-W cold artist-meta and model-ordering experiments."""
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
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    GENERATED,
    REPO,
    SEED,
    artifact_features,
    load_scope,
    metrics,
)


EXPERIMENTS = {
    "PP-W1": {"slug": "PP-W1_cold_lightgbm_artist_meta_feature_expansion", "title": "Cold LightGBM 작가 메타 피처 확장"},
    "PP-W2": {"slug": "PP-W2_cold_catboost_artist_meta_feature_expansion", "title": "Cold CatBoost 작가 메타 피처 확장"},
    "PP-W3": {"slug": "PP-W3_cold_catboost_quantile_artist_meta_huber_residual", "title": "Cold CatBoost Quantile + 작가 메타 + Huber residual"},
    "PP-W4": {"slug": "PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "title": "Cold LightGBM Quantile + 작가 메타 + CatBoost residual"},
    "PP-W5": {"slug": "PP-W5_cold_artist_meta_objective_policy_refresh", "title": "Cold 작가 메타 후보 목적별 정책 갱신"},
}

FEATURE_CANDIDATES = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"

BASE_NUMERIC = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
]

META_RAW = [
    "artist_meta_source",
    "artist_meta_nationality",
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
    "is_high_price_candidate",
]

META_NUMERIC = [
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_stage",
    "artist_meta_total_works_log",
    "artist_meta_for_sale_works_log",
    "artist_meta_followers_log",
    "artist_meta_birth_year_missing",
    "artist_meta_total_works_missing",
    "artist_meta_for_sale_works_missing",
    "artist_meta_followers_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_is_p1_flag",
    "artist_meta_has_international_flag",
    "is_high_price_candidate_flag",
]

META_CATEGORICAL = [
    "artist_meta_source",
    "artist_meta_nationality",
]

META_ALL = META_NUMERIC + META_CATEGORICAL


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def base_feature_sets() -> dict[str, list[str]]:
    features = artifact_features()
    cold_lgb = features["cold_lightgbm"]
    cold_cb = features["cold_catboost"]
    raw = [
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
    ]
    medium_size = unique(raw + ["size_bucket", "medium_size_bucket", "medium_shape_bucket"])
    support_shape = unique(raw + ["size_bucket", "shape_bucket", "support_size_bucket", "medium_shape_bucket"])
    generated_all = unique(raw + GENERATED)
    return {
        "cold_lgb": cold_lgb,
        "cold_cb": cold_cb,
        "raw": raw,
        "medium_size": medium_size,
        "support_shape": support_shape,
        "generated_all": generated_all,
    }


def pp_w1_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    return [
        ("baseline_support_size", "LightGBM 기존 support-size 기준", fs["cold_lgb"], "기존 Cold LightGBM 기준 피처셋"),
        ("support_size_meta_numeric", "support-size + 작가 메타 숫자", unique(fs["cold_lgb"] + META_NUMERIC), "작가 활동량/인지도 숫자 피처가 Cold 기준선을 보완하는지 확인"),
        ("support_size_meta_all", "support-size + 작가 메타 전체", unique(fs["cold_lgb"] + META_ALL), "작가 숫자 피처와 국적/소스 범주 피처를 함께 사용"),
        ("medium_size_meta_all", "medium-size + 작가 메타 전체", unique(fs["medium_size"] + META_ALL), "PP-U3에서 가능성이 있던 medium-size 조합에 작가 메타 추가"),
        ("support_shape_meta_all", "support-shape + 작가 메타 전체", unique(fs["support_shape"] + META_ALL), "support/shape bucket 조합에 작가 메타 추가"),
        ("generated_all_meta_all", "전체 생성 bucket + 작가 메타 전체", unique(fs["generated_all"] + META_ALL), "작품 조건 bucket과 작가 메타를 최대 투입"),
    ]


def pp_w2_candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    return [
        ("baseline_medium_shape", "CatBoost 기존 medium-shape 기준", fs["cold_cb"], "기존 Cold CatBoost 기준 피처셋"),
        ("medium_shape_meta_numeric", "medium-shape + 작가 메타 숫자", unique(fs["cold_cb"] + META_NUMERIC), "대칭 트리에서 작가 숫자 피처와 medium-shape 조합 확인"),
        ("medium_shape_meta_all", "medium-shape + 작가 메타 전체", unique(fs["cold_cb"] + META_ALL), "CatBoost의 범주형 처리 장점을 국적/소스 피처까지 확장"),
        ("medium_size_meta_all", "medium-size + 작가 메타 전체", unique(fs["medium_size"] + META_ALL), "CatBoost에서 재료+크기+작가 메타 조건 조합 확인"),
        ("support_shape_meta_all", "support-shape + 작가 메타 전체", unique(fs["support_shape"] + META_ALL), "support/shape bucket과 작가 메타 조건 조합 확인"),
        ("generated_all_meta_all", "전체 생성 bucket + 작가 메타 전체", unique(fs["generated_all"] + META_ALL), "CatBoost가 많은 범주 조합 중 유효 split만 찾는지 확인"),
    ]


def load_meta_map() -> pd.DataFrame:
    meta = pd.read_csv(
        FEATURE_CANDIDATES,
        low_memory=False,
        usecols=["track4_source_row_index", *META_RAW],
    ).rename(columns={"track4_source_row_index": "_track6_row_id"})
    meta["_track6_row_id"] = pd.to_numeric(meta["_track6_row_id"], errors="coerce")
    meta = meta.dropna(subset=["_track6_row_id"]).copy()
    meta["_track6_row_id"] = meta["_track6_row_id"].astype(int)
    meta = meta.drop_duplicates("_track6_row_id", keep="first")
    return meta


def add_artist_meta(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    meta = load_meta_map()
    out_frames = []
    for frame in frames:
        out = frame.merge(meta, on="_track6_row_id", how="left")
        out = engineer_artist_meta(out)
        out_frames.append(out)
    return out_frames


def engineer_artist_meta(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_meta_career_stage",
    ]:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
    for col in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_career_stage",
    ]:
        out[f"{col}_missing"] = out[col].isna().astype(float)
    out["artist_meta_total_works_log"] = np.log1p(out["artist_meta_total_works"].clip(lower=0))
    out["artist_meta_for_sale_works_log"] = np.log1p(out["artist_meta_for_sale_works"].clip(lower=0))
    out["artist_meta_followers_log"] = np.log1p(out["artist_meta_followers"].clip(lower=0))
    out["artist_meta_is_p1_flag"] = boolish(out.get("artist_meta_is_p1"))
    out["artist_meta_has_international_flag"] = boolish(out.get("artist_meta_has_international"))
    out["is_high_price_candidate_flag"] = boolish(out.get("is_high_price_candidate"))
    for col in META_CATEGORICAL:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def boolish(values: pd.Series | None) -> pd.Series:
    if values is None:
        return pd.Series(0.0, index=pd.RangeIndex(0))
    return values.astype("string").str.lower().isin(["true", "1", "yes", "y"]).astype(float)


def load_cold_with_meta(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_required = [c for c in features if c not in META_ALL]
    train, val, test = load_scope("cold", base_required)
    return tuple(add_artist_meta([train, val, test]))  # type: ignore[return-value]


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in features if c in set(BASE_NUMERIC + META_NUMERIC)]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def normalize_frame(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def lgbm_model(features: list[str], objective: str = "regression") -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 450,
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
        params["alpha"] = 0.5
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", LGBMRegressor(**params))])


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


def catboost_model(loss: str) -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function=loss,
        iterations=550,
        learning_rate=0.035,
        depth=6,
        l2_leaf_reg=8.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def fit_direct(model_name: str, loss_or_objective: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    train = normalize_frame(train, features)
    val = normalize_frame(val, features)
    test = normalize_frame(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    if model_name == "lightgbm":
        model = lgbm_model(features, objective=loss_or_objective)
        model.fit(train[features], y)
        return {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    model = catboost_model(loss_or_objective)
    model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
    return {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "ln_price_krw", "price_krw"]]


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(metric_frame(frame), pred_log),
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def run_direct_exp(exp_id: str, model_name: str, candidates: list[tuple[str, str, list[str], str]], loss_or_objective: str, policy: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    all_features = unique([feature for *_head, features, _hyp in candidates for feature in features])
    train, val, test = load_cold_with_meta(all_features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for candidate, strategy, features, hypothesis in candidates:
        pred = fit_direct(model_name, loss_or_objective, train, val, test, features)
        maps.append({
            "experiment_id": exp_id,
            "candidate": candidate,
            "model": model_name,
            "loss_or_objective": loss_or_objective,
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(rows, exp_id, candidate, split, frame, pred[split], policy, {
                "model": model_name,
                "feature_strategy": strategy,
                "n_features": len(features),
            })
            preds.append(prediction_frame(exp_id, candidate, split, frame, pred[split], policy, {
                "model": model_name,
                "feature_strategy": strategy,
                "n_features": len(features),
            }))
    return rows, preds, maps


def run_w1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    return run_direct_exp("PP-W1", "lightgbm", pp_w1_candidates(), "regression", "cold_artist_meta_lightgbm")


def run_w2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    return run_direct_exp("PP-W2", "catboost", pp_w2_candidates(), "RMSE", "cold_artist_meta_catboost")


def run_sequence(exp_id: str, base_model: str, base_loss: str, base_candidate: tuple[str, str, list[str], str], residual_models: list[str]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidate, strategy, features, hypothesis = base_candidate
    train, val, test = load_cold_with_meta(features)
    base_pred = fit_direct(base_model, base_loss, train, val, test, features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, exp_id, f"base_{candidate}", split, frame, base_pred[split], "stage1_artist_meta_quantile_base", {
            "model": base_model,
            "feature_strategy": strategy,
            "n_features": len(features),
        })
        preds.append(prediction_frame(exp_id, f"base_{candidate}", split, frame, base_pred[split], "stage1_artist_meta_quantile_base", {
            "model": base_model,
            "feature_strategy": strategy,
            "n_features": len(features),
        }))

    x_val = sequence_meta_features(val, base_pred["validation"], features)
    x_test = sequence_meta_features(test, base_pred["test"], features)
    y_resid = val["ln_price_krw"].to_numpy(dtype=float) - base_pred["validation"]
    for residual_model in residual_models:
        model = build_residual_model(residual_model, x_val)
        model.fit(x_val, y_resid)
        val_resid = np.asarray(model.predict(x_val), dtype=float)
        test_resid = np.asarray(model.predict(x_test), dtype=float)
        for cap in [0.15, 0.25, 0.35, 0.50]:
            for strength in [0.50, 0.75, 1.00]:
                val_final = base_pred["validation"] + np.clip(val_resid, -cap, cap) * strength
                test_final = base_pred["test"] + np.clip(test_resid, -cap, cap) * strength
                cand_name = f"{candidate}_{residual_model}_cap{cap:g}_s{strength:g}"
                maps.append({
                    "experiment_id": exp_id,
                    "stage1_model": base_model,
                    "stage1_loss": base_loss,
                    "stage1_candidate": candidate,
                    "residual_model": residual_model,
                    "cap": cap,
                    "strength": strength,
                    "n_features": len(features),
                    "features": ", ".join(features),
                })
                for split, frame, pred in [("validation", val, val_final), ("test", test, test_final)]:
                    add_metric(rows, exp_id, cand_name, split, frame, pred, "artist_meta_quantile_then_residual", {
                        "stage1_model": base_model,
                        "residual_model": residual_model,
                        "cap": cap,
                        "strength": strength,
                    })
                    preds.append(prediction_frame(exp_id, cand_name, split, frame, pred, "artist_meta_quantile_then_residual", {
                        "stage1_model": base_model,
                        "residual_model": residual_model,
                        "cap": cap,
                        "strength": strength,
                    }))
    return rows, preds, maps


def sequence_meta_features(frame: pd.DataFrame, base_pred: np.ndarray, features: list[str]) -> pd.DataFrame:
    numeric, categorical = split_types(features)
    out = pd.DataFrame(index=frame.index)
    out["base_pred_log"] = base_pred
    for col in numeric:
        out[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in categorical:
        codes, _ = pd.factorize(frame[col].astype("string").fillna("__MISSING__"), sort=True)
        out[f"{col}_code"] = codes.astype(float)
    return out


def build_residual_model(name: str, x_val: pd.DataFrame) -> Any:
    if name == "huber":
        return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))])
    if name == "ridge_10":
        return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))])
    if name == "catboost_mae":
        return CatBoostRegressor(loss_function="MAE", iterations=300, learning_rate=0.04, depth=4, l2_leaf_reg=10.0, random_seed=SEED, verbose=False, allow_writing_files=False)
    if name == "catboost_quantile":
        return CatBoostRegressor(loss_function="Quantile:alpha=0.5", iterations=300, learning_rate=0.04, depth=4, l2_leaf_reg=10.0, random_seed=SEED, verbose=False, allow_writing_files=False)
    raise ValueError(name)


def run_w3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    base = ("catboost_quantile_meta_all", "CatBoost Quantile + medium-shape + 작가 메타 전체", unique(base_feature_sets()["cold_cb"] + META_ALL), "CatBoost Quantile이 작가 메타와 작품 조건을 함께 사용한 뒤 Huber/Ridge residual로 안정화")
    return run_sequence("PP-W3", "catboost", "Quantile:alpha=0.5", base, ["huber", "ridge_10"])


def run_w4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    base = ("lightgbm_quantile_meta_all", "LightGBM Quantile + support-size + 작가 메타 전체", unique(base_feature_sets()["cold_lgb"] + META_ALL), "LightGBM Quantile이 작가 메타 기반 중앙 예측을 만든 뒤 CatBoost residual로 조건 조합 보정")
    return run_sequence("PP-W4", "lightgbm", "quantile", base, ["huber", "catboost_mae", "catboost_quantile"])


def source_prediction(folder: str, candidate: str, split: str) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq("cold") & df["split"].astype(str).eq(split)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {folder} {candidate} {split}")
    return out


def merge_policy_sources(sources: list[tuple[str, str, str]], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate in sources:
        src = source_prediction(folder, candidate, split)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty policy source merge")
    return merged


def add_policy_metric(rows: list[dict[str, Any]], candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, selected_source: str) -> None:
    metric_input = frame[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
    rows.append({
        "experiment_id": "PP-W5",
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": "artist_meta_policy_refresh",
        "selected_source": selected_source,
        **metrics(metric_input, pred_log),
    })


def run_w5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    sources = [
        ("s1_mdape", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.2_s1"),
        ("s1_p95", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.5_s1"),
        ("q2_mape", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective"),
        ("w1_best_meta_lgb", "PP-W1_cold_lightgbm_artist_meta_feature_expansion", best_candidate("PP-W1_cold_lightgbm_artist_meta_feature_expansion", "MdAPE")),
        ("w2_best_meta_cb", "PP-W2_cold_catboost_artist_meta_feature_expansion", best_candidate("PP-W2_cold_catboost_artist_meta_feature_expansion", "MdAPE")),
        ("w3_best_seq", "PP-W3_cold_catboost_quantile_artist_meta_huber_residual", best_candidate("PP-W3_cold_catboost_quantile_artist_meta_huber_residual", "MdAPE")),
        ("w4_best_seq", "PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", best_candidate("PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "MdAPE")),
    ]
    val = merge_policy_sources(sources, "validation")
    test = merge_policy_sources(sources, "test")
    labels = [label for label, *_rest in sources]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    val_metrics = {label: policy_metric_values(val, val[label].to_numpy(dtype=float)) for label in labels}
    base_mdape = min(m["MdAPE"] for m in val_metrics.values())
    selectors = {
        "mdape_first": lambda label: val_metrics[label]["MdAPE"],
        "mape_guarded": lambda label: val_metrics[label]["MAPE"] if val_metrics[label]["MdAPE"] <= base_mdape * 1.08 else np.inf,
        "p95_guarded": lambda label: val_metrics[label]["p95_APE"] if val_metrics[label]["MdAPE"] <= base_mdape * 1.10 else np.inf,
    }
    for label in labels:
        for split, frame in [("validation", val), ("test", test)]:
            pred = frame[label].to_numpy(dtype=float)
            add_policy_metric(rows, f"component_{label}", split, frame, pred, label)
    for objective, scorer in selectors.items():
        selected = min(labels, key=scorer)
        maps.append({
            "experiment_id": "PP-W5",
            "objective": objective,
            "selected_label": selected,
            **{f"validation_{k}": v for k, v in val_metrics[selected].items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = frame[selected].to_numpy(dtype=float)
            add_policy_metric(rows, f"cold_artist_meta_policy_{objective}", split, frame, pred, selected)
            preds.append(pd.DataFrame({
                "experiment_id": "PP-W5",
                "candidate": f"cold_artist_meta_policy_{objective}",
                "scope": "cold",
                "split": split,
                "policy": "artist_meta_policy_refresh",
                "selected_source": selected,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "actual_log": frame["actual_log"].to_numpy(dtype=float),
                "pred_log": pred,
                "actual_price": frame["actual_price"].to_numpy(dtype=float),
                "pred_price": np.clip(np.exp(pred), 1_000.0, None),
            }))
    return rows, preds, maps


def best_candidate(folder: str, objective: str) -> str:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "metrics.csv")
    val = df[df["split"].astype(str).eq("validation")].copy()
    return str(val.sort_values([objective, "MdAPE", "MAPE", "p95_APE"]).iloc[0]["candidate"])


def policy_metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    metric_input = frame[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
    return metrics(metric_input, pred_log)


def render_report(exp_id: str, info: dict[str, Any], metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "- 목적: Cold 서비스 적용 가능성을 높이기 위해 작가 메타 피처와 모델 특성 기반 학습 순서를 추가 검증한다.",
        "- 선택 기준: validation에서 후보/보정 강도를 정하고 test에서 재현성을 본다.",
        "",
        "## Test 결과 상위",
        "",
        "| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in test.head(20).itertuples():
        lines.append(f"| `{row.candidate}` | `{row.policy}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += ["", "## 설정/정책 맵", ""]
    lines.append(markdown_table(map_df) if not map_df.empty else "- 별도 map 없음")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy / Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def markdown_table(df: pd.DataFrame) -> str:
    safe = df.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    rows = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *rows])


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


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
        "source_data": str(FEATURE_CANDIDATES.relative_to(REPO)),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, info, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")
    metrics_df["folder"] = str(exp_dir.relative_to(REPO))
    return metrics_df


def main() -> None:
    start = time.time()
    runners = {
        "PP-W1": run_w1,
        "PP-W2": run_w2,
        "PP-W3": run_w3,
        "PP-W4": run_w4,
        "PP-W5": run_w5,
    }
    summary_frames: list[pd.DataFrame] = []
    for exp_id in ["PP-W1", "PP-W2", "PP-W3", "PP-W4", "PP-W5"]:
        rows, preds, maps = runners[exp_id]()
        summary_frames.append(write_exp(exp_id, rows, preds, maps))
    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(BASE_EXP_DIR / "PP-W_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-W_summary_metrics.csv",
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
