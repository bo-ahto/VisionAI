#!/usr/bin/env python3
"""Run Track6 PP-X gallery tier and exhibition feature revalidation.

The earlier exhibition experiments used an expanded split. This script keeps
the current Track6 split fixed and joins exhibition/gallery fields only as
additional features, then compares them against the latest PP-W Cold candidates.
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
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, load_scope, metrics  # noqa: E402
from run_pp_w_experiments import (  # noqa: E402
    BASE_NUMERIC,
    META_ALL,
    META_NUMERIC,
    add_artist_meta,
    base_feature_sets,
    unique,
)


EXPERIMENTS = {
    "PP-X1": {"slug": "PP-X1_gallery_exhibition_feature_coverage", "title": "갤러리/전시 활동 피처 커버리지 재검증"},
    "PP-X2": {"slug": "PP-X2_cold_catboost_exhibition_gallery_revalidation", "title": "Cold CatBoost 전시/갤러리 피처 재검증"},
    "PP-X3": {"slug": "PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation", "title": "Cold LightGBM Quantile 전시/갤러리 피처 재검증"},
    "PP-X4": {"slug": "PP-X4_cold_lightgbm_external_huber_residual", "title": "Cold LightGBM 전시/갤러리 + Huber 잔차 보정"},
    "PP-X5": {"slug": "PP-X5_external_feature_policy_comparison", "title": "전시/갤러리 피처 목적별 정책 비교"},
}

SPLIT_ROOT = REPO / "data" / "track6_split"
RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"
CLEANED_V2 = REPO / "data" / "track4_primary_market_cleaned_v2.csv"

EXHIBITION_NUMERIC = [
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
    "artist_exhibition_total_count",
    "artist_exhibition_available_count",
    "artist_exhibition_solo_count_missing",
    "artist_exhibition_group_count_missing",
    "artist_exhibition_fair_count_missing",
    "artist_exhibition_solo_count_log",
    "artist_exhibition_group_count_log",
    "artist_exhibition_fair_count_log",
    "artist_exhibition_total_count_log",
]

GALLERY_NUMERIC = [
    "gallery_tier_raw_numeric",
    "gallery_tier_raw_available_flag",
    "gallery_tier_validated_score",
    "gallery_tier_validated_available_flag",
    "gallery_tier_any_available_flag",
    "gallery_city_count",
    "gallery_city_count_log",
]

GALLERY_CATEGORICAL = [
    "gallery_tier_raw_bucket",
    "gallery_tier_validated",
    "gallery_ref_type",
    "gallery_audit_status",
    "gallery_feature_source",
]

EXTERNAL_INTERACTIONS_NUMERIC = [
    "exhibition_total_x_log_area",
    "exhibition_total_x_followers_log",
    "gallery_validated_x_followers_log",
    "gallery_tier_x_exhibition_total_log",
]

EXTERNAL_INTERACTIONS_CATEGORICAL = [
    "exhibition_size_bucket",
    "gallery_exhibition_bucket",
]

EXTERNAL_NUMERIC = EXHIBITION_NUMERIC + GALLERY_NUMERIC + EXTERNAL_INTERACTIONS_NUMERIC
EXTERNAL_CATEGORICAL = GALLERY_CATEGORICAL + EXTERNAL_INTERACTIONS_CATEGORICAL
EXTERNAL_ALL = EXTERNAL_NUMERIC + EXTERNAL_CATEGORICAL
EXTERNAL_JOIN_COLUMNS = EXHIBITION_NUMERIC + GALLERY_NUMERIC + GALLERY_CATEGORICAL


def split_file(split: str) -> Path:
    return SPLIT_ROOT / f"track6_{split}.csv"


def tier_to_score(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text in {"tier a", "a", "1"}:
        return 3.0
    if text in {"tier b", "b", "2"}:
        return 2.0
    if text in {"tier c", "c", "3"}:
        return 1.0
    return np.nan


def clean_count(series: pd.Series) -> pd.Series:
    value = pd.to_numeric(series, errors="coerce")
    return value.mask((value < 0) | (value > 200))


def load_raw_external_map() -> pd.DataFrame:
    raw_cols = [
        "track4_source",
        "track4_source_row_index",
        "saatchi__solo_count",
        "saatchi__group_count",
        "saatchi__fair_count",
        "saatchi__gallery_tier",
        "saatchi__gallery_city_count",
        "gallery_primary__gallery_tier",
    ]
    raw = pd.read_csv(RAW_COLLECTED, usecols=lambda c: c in set(raw_cols), low_memory=False)
    raw["track4_source_row_index"] = pd.to_numeric(raw["track4_source_row_index"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    raw["track4_source_row_index"] = raw["track4_source_row_index"].astype(int)
    raw = raw.drop_duplicates(["track4_source", "track4_source_row_index"], keep="first")
    raw = raw.rename(columns={
        "saatchi__solo_count": "artist_exhibition_solo_count",
        "saatchi__group_count": "artist_exhibition_group_count",
        "saatchi__fair_count": "artist_exhibition_fair_count",
        "saatchi__gallery_city_count": "gallery_city_count",
    })
    for col in [
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
    ]:
        raw[col] = clean_count(raw[col])
    raw["gallery_tier_raw_numeric"] = pd.to_numeric(raw.get("saatchi__gallery_tier"), errors="coerce")
    raw["gallery_tier_raw_numeric"] = raw["gallery_tier_raw_numeric"].where(
        raw["gallery_tier_raw_numeric"].notna(),
        pd.to_numeric(raw.get("gallery_primary__gallery_tier"), errors="coerce"),
    )
    raw["gallery_city_count"] = pd.to_numeric(raw.get("gallery_city_count"), errors="coerce")
    return raw[[
        "track4_source",
        "track4_source_row_index",
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
        "gallery_tier_raw_numeric",
        "gallery_city_count",
    ]]


def load_validated_gallery_map() -> pd.DataFrame:
    cols = [
        "track4_source",
        "track4_source_row_index",
        "gallery_tier_validated",
        "gallery_ref_type",
        "gallery_audit_status",
    ]
    gallery = pd.read_csv(CLEANED_V2, usecols=lambda c: c in set(cols), low_memory=False)
    gallery["track4_source_row_index"] = pd.to_numeric(gallery["track4_source_row_index"], errors="coerce").astype("Int64")
    gallery = gallery.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    gallery["track4_source_row_index"] = gallery["track4_source_row_index"].astype(int)
    gallery = gallery.drop_duplicates(["track4_source", "track4_source_row_index"], keep="first")
    return gallery


def source_membership() -> pd.DataFrame:
    frames = []
    for split in ["train", "val_cold", "test_cold"]:
        df = pd.read_csv(
            split_file(split),
            usecols=["_track6_row_id", "track4_source", "track4_source_row_index"],
            low_memory=False,
        )
        df["split_source"] = split
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["track4_source_row_index"] = pd.to_numeric(out["track4_source_row_index"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["track4_source", "track4_source_row_index"]).copy()
    out["track4_source_row_index"] = out["track4_source_row_index"].astype(int)
    return out.drop_duplicates("_track6_row_id", keep="first")


def build_external_row_map() -> pd.DataFrame:
    source = source_membership()
    raw = load_raw_external_map()
    validated = load_validated_gallery_map()
    out = source.merge(raw, on=["track4_source", "track4_source_row_index"], how="left")
    out = out.merge(validated, on=["track4_source", "track4_source_row_index"], how="left")
    out = engineer_external_features(out)
    return out[["_track6_row_id", *EXTERNAL_JOIN_COLUMNS]]


def engineer_external_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    count_cols = [
        "artist_exhibition_solo_count",
        "artist_exhibition_group_count",
        "artist_exhibition_fair_count",
    ]
    for col in count_cols:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
        out[f"{col}_missing"] = out[col].isna().astype(float)
        out[f"{col}_log"] = np.log1p(out[col].clip(lower=0).fillna(0.0))
    out["artist_exhibition_total_count"] = out[count_cols].sum(axis=1, min_count=1)
    out["artist_exhibition_total_count_log"] = np.log1p(out["artist_exhibition_total_count"].clip(lower=0).fillna(0.0))
    out["artist_exhibition_available_count"] = 3.0 - out[[f"{col}_missing" for col in count_cols]].sum(axis=1)

    out["gallery_tier_raw_numeric"] = pd.to_numeric(out.get("gallery_tier_raw_numeric"), errors="coerce")
    out["gallery_tier_raw_available_flag"] = out["gallery_tier_raw_numeric"].notna().astype(float)
    out["gallery_tier_raw_bucket"] = out["gallery_tier_raw_numeric"].astype("Int64").astype("string").fillna("__MISSING__")
    out["gallery_tier_validated"] = out.get("gallery_tier_validated", pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    out["gallery_tier_validated_score"] = out["gallery_tier_validated"].map(tier_to_score).astype(float)
    out["gallery_tier_validated_available_flag"] = out["gallery_tier_validated_score"].notna().astype(float)
    out["gallery_tier_any_available_flag"] = ((out["gallery_tier_raw_available_flag"] > 0) | (out["gallery_tier_validated_available_flag"] > 0)).astype(float)
    out["gallery_city_count"] = pd.to_numeric(out.get("gallery_city_count"), errors="coerce")
    out["gallery_city_count_log"] = np.log1p(out["gallery_city_count"].clip(lower=0).fillna(0.0))
    for col in ["gallery_ref_type", "gallery_audit_status"]:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    out["gallery_feature_source"] = np.select(
        [
            out["gallery_tier_validated_available_flag"].eq(1),
            out["gallery_tier_raw_available_flag"].eq(1),
        ],
        ["validated", "raw"],
        default="missing",
    )
    return out


def add_external_features(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    ext = build_external_row_map()
    out_frames = []
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


def engineer_external_interactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    total_log = pd.to_numeric(out["artist_exhibition_total_count_log"], errors="coerce").fillna(0.0)
    log_area = pd.to_numeric(out["log_area"], errors="coerce").fillna(0.0)
    followers_log = pd.to_numeric(out.get("artist_meta_followers_log"), errors="coerce").fillna(0.0)
    tier_score = pd.to_numeric(out["gallery_tier_validated_score"], errors="coerce").fillna(0.0)
    out["exhibition_total_x_log_area"] = total_log * log_area
    out["exhibition_total_x_followers_log"] = total_log * followers_log
    out["gallery_validated_x_followers_log"] = tier_score * followers_log
    out["gallery_tier_x_exhibition_total_log"] = tier_score * total_log
    size = out.get("size_bucket", pd.Series("__MISSING__", index=out.index)).astype("string").fillna("__MISSING__")
    exhibition_bucket = pd.cut(
        pd.to_numeric(out["artist_exhibition_total_count"], errors="coerce"),
        bins=[-np.inf, 0, 3, 8, np.inf],
        labels=["none", "low", "mid", "high"],
    ).astype("string").fillna("__MISSING__")
    out["exhibition_size_bucket"] = size.astype(str) + "__" + exhibition_bucket.astype(str)
    out["gallery_exhibition_bucket"] = out["gallery_feature_source"].astype(str) + "__" + exhibition_bucket.astype(str)
    return out


def load_cold_with_meta_external(features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    external = set(EXTERNAL_ALL)
    base_required = [c for c in features if c not in set(META_ALL) and c not in external]
    train, val, test = load_scope("cold", base_required)
    train, val, test = add_artist_meta([train, val, test])
    train, val, test = add_external_features([train, val, test])
    return train, val, test


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_source = set(BASE_NUMERIC + META_NUMERIC + EXTERNAL_NUMERIC)
    numeric = [col for col in features if col in numeric_source]
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


def fit_direct(model_name: str, loss_or_objective: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
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
    model = lgbm_model(features, objective=loss_or_objective)
    model.fit(train[features], y)
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "ln_price_krw", "price_krw"]]


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(metric_frame(frame), pred_log)


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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def feature_candidates() -> dict[str, tuple[str, list[str], str]]:
    fs = base_feature_sets()
    cat_base = unique(fs["generated_all"] + META_ALL)
    lgb_base = unique(fs["cold_lgb"] + META_ALL)
    exhibition = EXHIBITION_NUMERIC
    gallery = GALLERY_NUMERIC + GALLERY_CATEGORICAL
    interactions = EXTERNAL_INTERACTIONS_NUMERIC + EXTERNAL_INTERACTIONS_CATEGORICAL
    return {
        "baseline_catboost_ppw2_generated_all_meta_all": (
            "PP-W2 CatBoost 최신 기준",
            cat_base,
            "전시/갤러리 피처를 넣지 않은 최신 CatBoost 기준선",
        ),
        "catboost_exhibition": (
            "CatBoost + 전시 활동 피처",
            unique(cat_base + exhibition),
            "대칭 트리에서 작품 조건, 작가 메타, 전시 횟수 조합이 유효한지 확인",
        ),
        "catboost_gallery": (
            "CatBoost + 갤러리 티어 피처",
            unique(cat_base + gallery),
            "갤러리 티어/검증 여부가 가격 구간을 나눌 수 있는지 확인",
        ),
        "catboost_exhibition_gallery": (
            "CatBoost + 전시 활동 + 갤러리 티어",
            unique(cat_base + exhibition + gallery),
            "작가 활동 이력과 갤러리 신뢰도를 함께 넣었을 때 개선되는지 확인",
        ),
        "catboost_exhibition_gallery_interaction": (
            "CatBoost + 전시/갤러리 상호작용",
            unique(cat_base + exhibition + gallery + interactions),
            "전시 활동 효과가 작품 크기/작가 인지도/갤러리 tier에 따라 달라지는지 확인",
        ),
        "baseline_lightgbm_quantile_ppw4_meta_all": (
            "PP-W4 LightGBM Quantile 최신 기준",
            lgb_base,
            "전시/갤러리 피처를 넣지 않은 최신 LightGBM Quantile 기준선",
        ),
        "lightgbm_quantile_exhibition": (
            "LightGBM Quantile + 전시 활동 피처",
            unique(lgb_base + exhibition),
            "전시 활동이 중앙값 예측과 p95 안정화에 도움이 되는지 확인",
        ),
        "lightgbm_quantile_gallery": (
            "LightGBM Quantile + 갤러리 티어 피처",
            unique(lgb_base + gallery),
            "갤러리 tier/가용 여부가 중앙값 예측을 안정화하는지 확인",
        ),
        "lightgbm_quantile_exhibition_gallery": (
            "LightGBM Quantile + 전시 활동 + 갤러리 티어",
            unique(lgb_base + exhibition + gallery),
            "전시 활동과 갤러리 신뢰도 묶음이 평균/큰 오차를 줄이는지 확인",
        ),
        "lightgbm_quantile_exhibition_gallery_interaction": (
            "LightGBM Quantile + 전시/갤러리 상호작용",
            unique(lgb_base + exhibition + gallery + interactions),
            "전시/갤러리 정보가 위험 구간 분리에 도움 되는지 확인",
        ),
    }


def run_x1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = unique(base_feature_sets()["generated_all"] + META_ALL + EXTERNAL_ALL)
    train, val, test = load_cold_with_meta_external(features)
    rows: list[dict[str, Any]] = []
    for split, frame in [("train", train), ("validation", val), ("test", test)]:
        rows.append({
            "experiment_id": "PP-X1",
            "candidate": "external_feature_coverage",
            "scope": "cold",
            "split": split,
            "policy": "coverage_only",
            "n_rows": len(frame),
            "solo_coverage": float(frame["artist_exhibition_solo_count"].notna().mean()),
            "group_coverage": float(frame["artist_exhibition_group_count"].notna().mean()),
            "fair_coverage": float(frame["artist_exhibition_fair_count"].notna().mean()),
            "gallery_raw_coverage": float(frame["gallery_tier_raw_available_flag"].mean()),
            "gallery_validated_coverage": float(frame["gallery_tier_validated_available_flag"].mean()),
            "gallery_any_coverage": float(frame["gallery_tier_any_available_flag"].mean()),
        })
    maps = [{
        "experiment_id": "PP-X1",
        "source_raw": str(RAW_COLLECTED.relative_to(REPO)),
        "source_validated": str(CLEANED_V2.relative_to(REPO)),
        "join_key": "_track6_row_id -> track4_source + track4_source_row_index",
        "note": "Current Track6 split membership is fixed; only external columns are joined.",
    }]
    return rows, [], maps


def run_direct_models() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidates = feature_candidates()
    all_features = unique([feature for _name, (_strategy, features, _hypothesis) in candidates.items() for feature in features])
    train, val, test = load_cold_with_meta_external(all_features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for candidate, (strategy, features, hypothesis) in candidates.items():
        if candidate.startswith("catboost") or candidate.startswith("baseline_catboost"):
            exp_id = "PP-X2"
            model_name = "catboost"
            loss = "RMSE"
            policy = "cold_catboost_exhibition_gallery_revalidation"
        else:
            exp_id = "PP-X3"
            model_name = "lightgbm"
            loss = "quantile"
            policy = "cold_lightgbm_quantile_exhibition_gallery_revalidation"
        pred = fit_direct(model_name, loss, train, val, test, features)
        maps.append({
            "experiment_id": exp_id,
            "candidate": candidate,
            "model": model_name,
            "loss_or_objective": loss,
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(rows, exp_id, candidate, split, frame, pred[split], policy, {
                "model": model_name,
                "loss_or_objective": loss,
                "feature_strategy": strategy,
                "n_features": len(features),
            })
            preds.append(prediction_frame(exp_id, candidate, split, frame, pred[split], policy, {
                "model": model_name,
                "loss_or_objective": loss,
                "feature_strategy": strategy,
                "n_features": len(features),
            }))
    return rows, preds, maps


def residual_features(frame: pd.DataFrame, base_pred: np.ndarray, features: list[str]) -> pd.DataFrame:
    numeric, categorical = split_types(features)
    out = pd.DataFrame(index=frame.index)
    out["base_pred_log"] = base_pred
    for col in numeric:
        out[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in categorical:
        codes, _ = pd.factorize(frame[col].astype("string").fillna("__MISSING__"), sort=True)
        out[f"{col}_code"] = codes.astype(float)
    return out


def run_x4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidates = feature_candidates()
    base_name = "lightgbm_quantile_exhibition_gallery_interaction"
    strategy, features, hypothesis = candidates[base_name]
    train, val, test = load_cold_with_meta_external(features)
    base_pred = fit_direct("lightgbm", "quantile", train, val, test, features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, "PP-X4", f"base_{base_name}", split, frame, base_pred[split], "external_lightgbm_quantile_base", {
            "stage1_model": "lightgbm",
            "feature_strategy": strategy,
            "n_features": len(features),
        })
        preds.append(prediction_frame("PP-X4", f"base_{base_name}", split, frame, base_pred[split], "external_lightgbm_quantile_base", {
            "stage1_model": "lightgbm",
            "feature_strategy": strategy,
            "n_features": len(features),
        }))
    x_val = residual_features(val, base_pred["validation"], features)
    x_test = residual_features(test, base_pred["test"], features)
    y_resid = val["ln_price_krw"].to_numpy(dtype=float) - base_pred["validation"]
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000)),
    ])
    model.fit(x_val, y_resid)
    val_resid = np.asarray(model.predict(x_val), dtype=float)
    test_resid = np.asarray(model.predict(x_test), dtype=float)
    for cap in [0.15, 0.25, 0.35, 0.50]:
        for strength in [0.50, 0.75, 1.00]:
            cand = f"{base_name}_huber_residual_cap{cap:g}_s{strength:g}"
            maps.append({
                "experiment_id": "PP-X4",
                "base_candidate": base_name,
                "residual_model": "HuberRegressor",
                "cap": cap,
                "strength": strength,
                "hypothesis": "전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정",
            })
            for split, frame, pred, resid in [
                ("validation", val, base_pred["validation"], val_resid),
                ("test", test, base_pred["test"], test_resid),
            ]:
                final = pred + np.clip(resid, -cap, cap) * strength
                add_metric(rows, "PP-X4", cand, split, frame, final, "external_lightgbm_quantile_huber_residual", {
                    "stage1_model": "lightgbm",
                    "residual_model": "HuberRegressor",
                    "cap": cap,
                    "strength": strength,
                })
                preds.append(prediction_frame("PP-X4", cand, split, frame, final, "external_lightgbm_quantile_huber_residual", {
                    "stage1_model": "lightgbm",
                    "residual_model": "HuberRegressor",
                    "cap": cap,
                    "strength": strength,
                }))
    return rows, preds, maps


def source_prediction(folder: str, candidate: str, split: str) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq("cold") & df["split"].astype(str).eq(split)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {folder} {candidate} {split}")
    return out


def best_candidate(folder: str, objective: str) -> str:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "metrics.csv")
    val = df[df["split"].astype(str).eq("validation")].copy()
    return str(val.sort_values([objective, "MdAPE", "MAPE", "p95_APE"]).iloc[0]["candidate"])


def run_x5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    sources = [
        ("w2_mdape", "PP-W2_cold_catboost_artist_meta_feature_expansion", "generated_all_meta_all"),
        ("w4_p95", "PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "base_lightgbm_quantile_meta_all"),
        ("x2_mdape", "PP-X2_cold_catboost_exhibition_gallery_revalidation", best_candidate("PP-X2_cold_catboost_exhibition_gallery_revalidation", "MdAPE")),
        ("x3_mape", "PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation", best_candidate("PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation", "MAPE")),
        ("x3_p95", "PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation", best_candidate("PP-X3_cold_lightgbm_quantile_exhibition_gallery_revalidation", "p95_APE")),
        ("x4_mape", "PP-X4_cold_lightgbm_external_huber_residual", best_candidate("PP-X4_cold_lightgbm_external_huber_residual", "MAPE")),
        ("x4_p95", "PP-X4_cold_lightgbm_external_huber_residual", best_candidate("PP-X4_cold_lightgbm_external_huber_residual", "p95_APE")),
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for label, folder, candidate in sources:
        maps.append({"experiment_id": "PP-X5", "label": label, "folder": folder, "candidate": candidate})
        for split in ["validation", "test"]:
            src = source_prediction(folder, candidate, split)
            pred_log = src["pred_log"].to_numpy(dtype=float)
            metric_input = src[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})
            rows.append({
                "experiment_id": "PP-X5",
                "candidate": f"component_{label}",
                "scope": "cold",
                "split": split,
                "policy": "external_feature_policy_comparison",
                "selected_source": label,
                **metrics(metric_input, pred_log),
            })
            out = src.copy()
            out["experiment_id"] = "PP-X5"
            out["candidate"] = f"component_{label}"
            out["policy"] = "external_feature_policy_comparison"
            out["selected_source"] = label
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
        "- 목적: 갤러리 티어와 개인전/전시 활동 피처를 현재 최신 Cold 후보 구조에서 재검증한다.",
        "- 기준: 기존 Track6 split은 바꾸지 않고 `_track6_row_id` 기준으로 외부 피처만 추가한다.",
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
    else:
        lines += ["## 커버리지", "", markdown_table(metrics_df)]
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
        "source_raw": str(RAW_COLLECTED.relative_to(REPO)),
        "source_validated_gallery": str(CLEANED_V2.relative_to(REPO)),
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
    summary_frames: list[pd.DataFrame] = []
    rows, preds, maps = run_x1()
    summary_frames.append(write_exp("PP-X1", rows, preds, maps))

    direct_rows, direct_preds, direct_maps = run_direct_models()
    for exp_id in ["PP-X2", "PP-X3"]:
        rows = [row for row in direct_rows if row["experiment_id"] == exp_id]
        preds = [pred for pred in direct_preds if not pred.empty and str(pred["experiment_id"].iloc[0]) == exp_id]
        maps = [row for row in direct_maps if row["experiment_id"] == exp_id]
        summary_frames.append(write_exp(exp_id, rows, preds, maps))

    rows, preds, maps = run_x4()
    summary_frames.append(write_exp("PP-X4", rows, preds, maps))

    rows, preds, maps = run_x5()
    summary_frames.append(write_exp("PP-X5", rows, preds, maps))

    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(BASE_EXP_DIR / "PP-X_gallery_exhibition_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-X_gallery_exhibition_summary_metrics.csv",
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
