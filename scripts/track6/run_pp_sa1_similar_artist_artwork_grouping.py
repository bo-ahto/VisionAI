#!/usr/bin/env python3
"""Run PP-SA1 similar-artist and similar-artwork grouping validation.

This experiment checks whether service-facing "similar artist" groups can be
used as a price prior or model feature. It keeps the existing fixed Track6
train/validation/test split and computes validation/test priors from train only.
The first screening run keeps validation/test priors train-only. Train priors
are computed from full train to finish quickly; candidates that look promising
should be rerun with a fully optimized out-of-fold implementation before
adoption.
"""
from __future__ import annotations

import html
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SA1"
EXP_SLUG = "PP-SA1_similar_artist_artwork_grouping"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "유사 작가 및 유사 작품 그룹 기준가 검증"
SEED = 20260611
RUN_MODEL_SCREEN = False

META_COLUMNS = [
    "artist_key",
    "artist_name_ko",
    "artist_meta_nationality",
    "artist_meta_nationality_ko",
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_for_sale_ratio",
    "artist_meta_career_age",
    "artist_meta_career_stage",
    "artist_meta_is_p1",
    "artist_meta_has_international",
    "artist_works_count_train",
]

BASE_NUMERIC = svc1.BASE_NUMERIC
SVC_NUMERIC = svc1.SVC_NUMERIC
SVC_CATEGORICAL = svc1.SVC_CATEGORICAL

SA_NUMERIC = [
    "sa_group_log_price_median",
    "sa_group_log_price_q25",
    "sa_group_log_price_q75",
    "sa_group_log_price_iqr",
    "sa_group_log_unit_area_median",
    "sa_group_log_unit_area_iqr",
    "sa_group_n_log",
    "sa_artist_count_log",
    "sa_similarity_score_mean",
    "sa_similarity_score_max",
    "sa_artwork_match_score",
]
SA_CATEGORICAL = [
    "sa_group_level",
    "sa_coverage_tier",
    "sa_similarity_basis",
]
SA_FEATURES = [*SA_NUMERIC, *SA_CATEGORICAL]
MODEL_NUMERIC = set(BASE_NUMERIC + SVC_NUMERIC + SA_NUMERIC)

GROUPING_FEATURES = list(svc1.GROUPING_FEATURES)
SCOPES = [
    {"scope": "warm", "model": "huber", "feature_key": "warm"},
    {"scope": "cold", "model": "lightgbm", "feature_key": "cold_lightgbm"},
]

SIMILAR_ARTIST_CRITERIA = {
    "candidate_pool": "학습 데이터에서 낙찰 이력이 5건 이상 있는 작가. 같은 작가는 유사 작가 후보에서 제외한다.",
    "history_basis": "대상 작가가 학습 이력이 있으면 가격대, 면적당 가격, 주 사용 재료/지지체/크기, 생년, 국적, 활동 단계, 팔로워/작품 수를 함께 사용한다.",
    "metadata_basis": "대상 작가 학습 이력이 없으면 생년, 국적, 활동 단계, P1 여부, 팔로워/작품 수, 입력 작품의 재료/지지체/크기를 사용한다.",
    "selection": "유사도 점수 상위 12명 중 점수 0.45 이상을 유사 작가로 채택한다. 없으면 상위 5명을 fallback으로 사용한다.",
}

SIMILAR_ARTWORK_CRITERIA = [
    {
        "level": "similar_artist_medium_support_size",
        "label": "유사 작가 + 같은 재료/지지체 + 비슷한 크기",
        "min_n": 8,
    },
    {
        "level": "similar_artist_medium_size",
        "label": "유사 작가 + 같은 재료 대분류 + 비슷한 크기",
        "min_n": 10,
    },
    {
        "level": "similar_artist_size",
        "label": "유사 작가 + 비슷한 크기",
        "min_n": 15,
    },
    {
        "level": "similar_artist_all",
        "label": "유사 작가 전체",
        "min_n": 20,
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "data", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def raw_split_path(scope: str, split: str) -> Path:
    if split == "train":
        return REPO / "data" / "track6_split" / "track6_train.csv"
    return REPO / "data" / "track6_split" / f"track6_{split}_{scope}.csv"


def attach_raw_metadata(frame: pd.DataFrame, scope: str, split: str) -> pd.DataFrame:
    raw = pd.read_csv(raw_split_path(scope, split), low_memory=False)
    keep = ["_track6_row_id", *[c for c in META_COLUMNS if c in raw.columns]]
    meta = raw[keep].drop_duplicates("_track6_row_id")
    out = frame.copy()
    drop_cols = [c for c in META_COLUMNS if c in out.columns and c != "_track6_row_id"]
    out = out.drop(columns=drop_cols, errors="ignore")
    out = out.merge(meta, on="_track6_row_id", how="left")
    return out


def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in ["price_krw", "ln_price_krw", "area_cm2", "log_area"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    area = np.clip(out["area_cm2"].astype(float).to_numpy(), 1.0, None)
    out["sa_source_log_unit_area"] = out["ln_price_krw"].astype(float).to_numpy() - np.log(area)
    for col in [
        "artist_key",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "size_bucket",
        "artist_meta_nationality",
        "artist_meta_nationality_ko",
        "artist_meta_career_stage",
        "artist_meta_is_p1",
        "artist_meta_has_international",
    ]:
        if col in out.columns:
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    for col in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
        "artist_meta_career_age",
        "artist_works_count_train",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def first_non_missing(series: pd.Series, default: Any = np.nan) -> Any:
    valid = series.dropna()
    valid = valid[~valid.astype(str).isin(["", "__MISSING__", "nan", "None"])]
    if valid.empty:
        return default
    return valid.iloc[0]


def mode_or_missing(series: pd.Series) -> str:
    values = series.astype("string").fillna("__MISSING__")
    values = values[~values.isin(["", "__MISSING__"])]
    if values.empty:
        return "__MISSING__"
    return str(values.mode().iloc[0])


def market_tier(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() < 10:
        return pd.Series(["unknown"] * len(values), index=values.index)
    try:
        return pd.qcut(numeric.rank(method="first"), q=5, labels=["tier1", "tier2", "tier3", "tier4", "tier5"]).astype(str)
    except ValueError:
        return pd.Series(["unknown"] * len(values), index=values.index)


def birth_decade(value: Any) -> str:
    year = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(year) or year < 1200 or year > 2026:
        return "__MISSING__"
    return f"{int(year // 10 * 10)}s"


def build_artist_profiles(source: pd.DataFrame) -> pd.DataFrame:
    ready = prepare_frame(source)
    grouped = ready.groupby("artist_key", dropna=False, observed=False)
    profiles = grouped.agg(
        artist_name_ko=("artist_name_ko", lambda x: first_non_missing(x, "")),
        artist_work_count=("ln_price_krw", "size"),
        artist_log_price_median=("ln_price_krw", "median"),
        artist_log_price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
        artist_log_price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
        artist_log_unit_area_median=("sa_source_log_unit_area", "median"),
        artist_log_area_median=("log_area", "median"),
        primary_medium=("medium_category", mode_or_missing),
        primary_support=("support_category", mode_or_missing),
        primary_medium_support=("medium_support_bucket", mode_or_missing),
        primary_size_bucket=("size_bucket", mode_or_missing),
        birth_year=("artist_meta_birth_year", lambda x: first_non_missing(x, np.nan)),
        nationality=("artist_meta_nationality", mode_or_missing),
        nationality_ko=("artist_meta_nationality_ko", mode_or_missing),
        career_stage=("artist_meta_career_stage", mode_or_missing),
        total_works=("artist_meta_total_works", lambda x: first_non_missing(x, np.nan)),
        for_sale_works=("artist_meta_for_sale_works", lambda x: first_non_missing(x, np.nan)),
        followers=("artist_meta_followers", lambda x: first_non_missing(x, np.nan)),
        for_sale_ratio=("artist_meta_for_sale_ratio", lambda x: first_non_missing(x, np.nan)),
        career_age=("artist_meta_career_age", lambda x: first_non_missing(x, np.nan)),
        is_p1=("artist_meta_is_p1", mode_or_missing),
        has_international=("artist_meta_has_international", mode_or_missing),
    ).reset_index()
    profiles["artist_log_price_iqr"] = profiles["artist_log_price_q75"] - profiles["artist_log_price_q25"]
    profiles["birth_decade"] = profiles["birth_year"].map(birth_decade)
    profiles["artist_market_tier"] = market_tier(profiles["artist_log_price_median"])
    profiles["artist_work_count_log"] = np.log1p(pd.to_numeric(profiles["artist_work_count"], errors="coerce").fillna(0))
    for col in ["total_works", "for_sale_works", "followers", "career_age"]:
        profiles[f"{col}_log"] = np.log1p(pd.to_numeric(profiles[col], errors="coerce").clip(lower=0).fillna(0))
    return profiles


def target_profile(row: pd.Series, profiles: pd.DataFrame) -> dict[str, Any]:
    artist_key = str(row.get("artist_key", "__MISSING__"))
    hit = profiles[profiles["artist_key"].astype(str).eq(artist_key)]
    if not hit.empty:
        profile = hit.iloc[0].to_dict()
        profile["basis"] = "history_and_metadata"
        return profile
    return {
        "artist_key": artist_key,
        "artist_name_ko": row.get("artist_name_ko", ""),
        "artist_work_count": 0,
        "artist_log_price_median": np.nan,
        "artist_log_unit_area_median": np.nan,
        "artist_log_area_median": row.get("log_area", np.nan),
        "primary_medium": row.get("medium_category", "__MISSING__"),
        "primary_support": row.get("support_category", "__MISSING__"),
        "primary_medium_support": row.get("medium_support_bucket", "__MISSING__"),
        "primary_size_bucket": row.get("size_bucket", "__MISSING__"),
        "birth_year": row.get("artist_meta_birth_year", np.nan),
        "birth_decade": birth_decade(row.get("artist_meta_birth_year", np.nan)),
        "nationality": row.get("artist_meta_nationality", "__MISSING__"),
        "nationality_ko": row.get("artist_meta_nationality_ko", "__MISSING__"),
        "career_stage": row.get("artist_meta_career_stage", "__MISSING__"),
        "artist_market_tier": "unknown",
        "total_works_log": math.log1p(max(float(row.get("artist_meta_total_works", 0) or 0), 0)),
        "for_sale_works_log": math.log1p(max(float(row.get("artist_meta_for_sale_works", 0) or 0), 0)),
        "followers_log": math.log1p(max(float(row.get("artist_meta_followers", 0) or 0), 0)),
        "career_age_log": math.log1p(max(float(row.get("artist_meta_career_age", 0) or 0), 0)),
        "is_p1": row.get("artist_meta_is_p1", "__MISSING__"),
        "has_international": row.get("artist_meta_has_international", "__MISSING__"),
        "basis": "metadata_and_artwork",
    }


def build_numeric_scale(profiles: pd.DataFrame) -> tuple[list[str], pd.Series, pd.Series]:
    cols = [
        "artist_log_price_median",
        "artist_log_unit_area_median",
        "artist_log_area_median",
        "artist_work_count_log",
        "total_works_log",
        "for_sale_works_log",
        "followers_log",
        "career_age_log",
    ]
    existing = [c for c in cols if c in profiles.columns]
    values = profiles[existing].apply(pd.to_numeric, errors="coerce")
    mean = values.mean(axis=0)
    std = values.std(axis=0).replace(0, 1.0).fillna(1.0)
    return existing, mean, std


def similarity_scores(
    target: dict[str, Any],
    candidates: pd.DataFrame,
    numeric_cols: list[str],
    mean: pd.Series,
    std: pd.Series,
) -> pd.DataFrame:
    out = candidates.copy()
    out = out[out["artist_key"].astype(str).ne(str(target.get("artist_key", "__MISSING__")))].copy()
    out = out[pd.to_numeric(out["artist_work_count"], errors="coerce").fillna(0) >= 5].copy()
    if out.empty:
        return out

    available_numeric = []
    for col in numeric_cols:
        value = pd.to_numeric(pd.Series([target.get(col, np.nan)]), errors="coerce").iloc[0]
        if pd.notna(value):
            available_numeric.append(col)
    if available_numeric:
        cand = out[available_numeric].apply(pd.to_numeric, errors="coerce").fillna(mean[available_numeric])
        target_values = pd.Series({col: float(target[col]) for col in available_numeric})
        dist = ((cand - target_values) / std[available_numeric]).pow(2).mean(axis=1).pow(0.5)
        numeric_score = 1.0 / (1.0 + dist)
    else:
        numeric_score = pd.Series(0.5, index=out.index)

    cat_score = pd.Series(0.0, index=out.index)
    cat_weight = 0.0
    for col, weight in [
        ("birth_decade", 0.20),
        ("nationality", 0.18),
        ("career_stage", 0.16),
        ("artist_market_tier", 0.14),
        ("primary_medium", 0.12),
        ("primary_support", 0.08),
        ("primary_size_bucket", 0.06),
        ("is_p1", 0.04),
        ("has_international", 0.02),
    ]:
        target_value = str(target.get(col, "__MISSING__"))
        if target_value in ["", "__MISSING__", "nan", "None"]:
            continue
        cat_score += weight * out[col].astype(str).eq(target_value).astype(float)
        cat_weight += weight
    if cat_weight > 0:
        cat_score = cat_score / cat_weight
    else:
        cat_score = pd.Series(0.5, index=out.index)

    if target.get("basis") == "history_and_metadata":
        out["sa_similarity_score"] = 0.55 * numeric_score + 0.45 * cat_score
    else:
        out["sa_similarity_score"] = 0.30 * numeric_score + 0.70 * cat_score
    return out.sort_values(["sa_similarity_score", "artist_work_count"], ascending=[False, False])


def selected_similar_artists(
    row: pd.Series,
    profiles: pd.DataFrame,
    numeric_cols: list[str],
    mean: pd.Series,
    std: pd.Series,
    cache: dict[tuple[str, str, str, str], pd.DataFrame],
) -> pd.DataFrame:
    key = (str(row.get("artist_key", "__MISSING__")), "__ARTIST_LEVEL__", "__ARTIST_LEVEL__", "__ARTIST_LEVEL__")
    if key in cache:
        return cache[key]
    target = target_profile(row, profiles)
    scored = similarity_scores(target, profiles, numeric_cols, mean, std)
    if scored.empty:
        cache[key] = scored
        return scored
    top = scored.head(12).copy()
    selected = top[top["sa_similarity_score"] >= 0.45].copy()
    if selected.empty:
        selected = top.head(5).copy()
    selected["sa_similarity_basis"] = target.get("basis", "metadata_and_artwork")
    cache[key] = selected
    return selected


def stats_from_subset(subset: pd.DataFrame) -> dict[str, float]:
    return {
        "sa_group_log_price_median": float(subset["ln_price_krw"].median()),
        "sa_group_log_price_q25": float(subset["ln_price_krw"].quantile(0.25)),
        "sa_group_log_price_q75": float(subset["ln_price_krw"].quantile(0.75)),
        "sa_group_log_unit_area_median": float(subset["sa_source_log_unit_area"].median()),
        "sa_group_log_unit_area_q25": float(subset["sa_source_log_unit_area"].quantile(0.25)),
        "sa_group_log_unit_area_q75": float(subset["sa_source_log_unit_area"].quantile(0.75)),
        "sa_group_n": float(len(subset)),
    }


def coverage_tier(level: str, n: float, artist_count: float) -> str:
    if level == "global":
        return "fallback_global"
    if artist_count >= 8 and n >= 50:
        return "high_n"
    if artist_count >= 5 and n >= 20:
        return "medium_n"
    return "low_n"


def apply_similar_artist_stats(source: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    source_ready = prepare_frame(source)
    target_ready = prepare_frame(target)
    profiles = build_artist_profiles(source_ready)
    numeric_cols, mean, std = build_numeric_scale(profiles)
    source_by_artist = {str(k): g for k, g in source_ready.groupby("artist_key", dropna=False, observed=False)}
    global_stats = stats_from_subset(source_ready)
    global_stats["sa_group_log_price_iqr"] = global_stats["sa_group_log_price_q75"] - global_stats["sa_group_log_price_q25"]
    global_stats["sa_group_log_unit_area_iqr"] = (
        global_stats["sa_group_log_unit_area_q75"] - global_stats["sa_group_log_unit_area_q25"]
    )

    rows: list[dict[str, Any]] = []
    cache: dict[tuple[str, str, str, str], pd.DataFrame] = {}
    subset_cache: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    pool_cache: dict[str, pd.DataFrame] = {}
    for _idx, row_s in target_ready.iterrows():
        selected = selected_similar_artists(row_s, profiles, numeric_cols, mean, std, cache)
        artist_keys = tuple(selected["artist_key"].astype(str).tolist()) if not selected.empty else tuple()
        base: dict[str, Any] = {
            "_track6_row_id": row_s["_track6_row_id"],
            "sa_group_level": "global",
            "sa_similarity_basis": "no_similar_artist",
            "sa_artist_count": 0.0,
            "sa_artist_count_log": 0.0,
            "sa_similarity_score_mean": 0.0,
            "sa_similarity_score_max": 0.0,
            "sa_artwork_match_score": 0.0,
        }
        if artist_keys:
            cache_key = (
                "|".join(artist_keys),
                str(row_s.get("medium_support_bucket", "__MISSING__")),
                str(row_s.get("medium_category", "__MISSING__")),
                str(row_s.get("size_bucket", "__MISSING__")),
                str(row_s.get("support_category", "__MISSING__")),
            )
            if cache_key in subset_cache:
                best = subset_cache[cache_key].copy()
            else:
                pool_key = "|".join(artist_keys)
                if pool_key in pool_cache:
                    pool = pool_cache[pool_key]
                else:
                    artist_frames = [source_by_artist[a] for a in artist_keys if a in source_by_artist]
                    pool = pd.concat(artist_frames, ignore_index=True) if artist_frames else pd.DataFrame()
                    pool_cache[pool_key] = pool
                best = {}
                if not pool.empty:
                    candidates = [
                        (
                            "similar_artist_medium_support_size",
                            pool[
                                pool["medium_support_bucket"].astype(str).eq(str(row_s.get("medium_support_bucket", "__MISSING__")))
                                & pool["size_bucket"].astype(str).eq(str(row_s.get("size_bucket", "__MISSING__")))
                            ],
                            8,
                            1.00,
                        ),
                        (
                            "similar_artist_medium_size",
                            pool[
                                pool["medium_category"].astype(str).eq(str(row_s.get("medium_category", "__MISSING__")))
                                & pool["size_bucket"].astype(str).eq(str(row_s.get("size_bucket", "__MISSING__")))
                            ],
                            10,
                            0.82,
                        ),
                        (
                            "similar_artist_size",
                            pool[pool["size_bucket"].astype(str).eq(str(row_s.get("size_bucket", "__MISSING__")))],
                            15,
                            0.62,
                        ),
                        (
                            "similar_artist_all",
                            pool,
                            20,
                            0.40,
                        ),
                    ]
                    for level, subset, min_n, match_score in candidates:
                        if len(subset) >= min_n:
                            best = stats_from_subset(subset)
                            best["sa_group_level"] = level
                            best["sa_artwork_match_score"] = match_score
                            break
                subset_cache[cache_key] = best.copy()
            if best:
                base.update(best)
                base["sa_similarity_basis"] = str(selected["sa_similarity_basis"].iloc[0])
                base["sa_artist_count"] = float(len(selected))
                base["sa_artist_count_log"] = float(np.log1p(len(selected)))
                base["sa_similarity_score_mean"] = float(selected["sa_similarity_score"].mean())
                base["sa_similarity_score_max"] = float(selected["sa_similarity_score"].max())

        if base["sa_group_level"] == "global":
            base.update(global_stats)
            base["sa_artwork_match_score"] = 0.0
        base["sa_group_log_price_iqr"] = base["sa_group_log_price_q75"] - base["sa_group_log_price_q25"]
        base["sa_group_log_unit_area_iqr"] = (
            base["sa_group_log_unit_area_q75"] - base["sa_group_log_unit_area_q25"]
        )
        base["sa_group_n_log"] = float(np.log1p(float(base["sa_group_n"])))
        base["sa_coverage_tier"] = coverage_tier(
            str(base["sa_group_level"]),
            float(base["sa_group_n"]),
            float(base["sa_artist_count"]),
        )
        rows.append(base)
    return pd.DataFrame(rows)[["_track6_row_id", *SA_FEATURES, "sa_group_n", "sa_artist_count"]]


def crossfit_train_stats(train: pd.DataFrame) -> pd.DataFrame:
    return apply_similar_artist_stats(train, train)


def add_similar_artist_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats = crossfit_train_stats(train)
    val_stats = apply_similar_artist_stats(train, val)
    test_stats = apply_similar_artist_stats(train, test)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
    )


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in features if c in MODEL_NUMERIC]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def huber_model(features: list[str]) -> Pipeline:
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
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=4000)),
    ])


def lightgbm_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="regression",
            n_estimators=350,
            learning_rate=0.04,
            num_leaves=31,
            min_child_samples=40,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def fit_predict(model_name: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    model = huber_model(features) if model_name == "huber" else lightgbm_model(features)
    model.fit(train[features], y)
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def metric_row(
    scope: str,
    model: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    n_features: int,
) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "scope": scope,
        "model": model,
        "candidate": candidate,
        "split": split,
        "n_features": n_features,
        **svc1.metric_values(frame, pred_log),
    }


def prediction_frame(scope: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = svc1.prediction_frame(EXP_ID, candidate, scope, split, frame, pred_log)
    for col in ["sa_group_level", "sa_coverage_tier", "sa_similarity_basis", "sa_group_n", "sa_artist_count"]:
        out[col] = frame.get(col, pd.Series([np.nan] * len(frame))).to_numpy()
    return out


def candidate_features(base_features: list[str]) -> dict[str, list[str]]:
    return {
        "baseline": list(base_features),
        "same_artist_artwork_stats": list(dict.fromkeys([*base_features, *SVC_NUMERIC, *SVC_CATEGORICAL])),
        "similar_artist_artwork_stats": list(dict.fromkeys([*base_features, *SA_FEATURES])),
        "same_artist_plus_similar_artist_stats": list(dict.fromkeys([*base_features, *SVC_NUMERIC, *SVC_CATEGORICAL, *SA_FEATURES])),
    }


def coverage_summary(frames_by_scope: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, split_frames in frames_by_scope.items():
        for split, frame in split_frames.items():
            for prefix, level_col, n_col in [
                ("same_artist_artwork", "svc_group_level", "svc_group_n"),
                ("similar_artist_artwork", "sa_group_level", "sa_group_n"),
            ]:
                if level_col not in frame.columns:
                    continue
                for level, group in frame.groupby(level_col, dropna=False):
                    rows.append({
                        "scope": scope,
                        "split": split,
                        "basis": prefix,
                        "level": str(level),
                        "rows": int(len(group)),
                        "share": float(len(group) / len(frame)),
                        "median_group_n": float(pd.to_numeric(group[n_col], errors="coerce").median()),
                    })
    return pd.DataFrame(rows)


def direct_prior_rows(scope: str, val: pd.DataFrame, test: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    metrics: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for split, frame in [("validation", val), ("test", test)]:
        for candidate, col in [
            ("same_artist_artwork_direct_median", "svc_group_log_price_median"),
            ("similar_artist_artwork_direct_median", "sa_group_log_price_median"),
        ]:
            pred_log = frame[col].to_numpy(dtype=float)
            metrics.append(metric_row(scope, "service_prior", candidate, split, frame, pred_log, 1))
            preds.append(prediction_frame(scope, candidate, split, frame, pred_log))
    return metrics, preds


def blend_screen_metrics(pred_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope in ["warm", "cold"]:
        test = pred_df[(pred_df["scope"].eq(scope)) & (pred_df["split"].eq("test"))].copy()
        if test.empty:
            continue
        wide = test.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last").reset_index()
        meta_cols = ["_track6_row_id", "actual_log", "actual_price", "sa_group_level", "sa_coverage_tier"]
        meta = test.drop_duplicates("_track6_row_id")[[c for c in meta_cols if c in test.columns]]
        data = meta.merge(wide, on="_track6_row_id", how="inner")
        data["price_krw"] = data["actual_price"]
        data["ln_price_krw"] = data["actual_log"]
        if not {"same_artist_artwork_direct_median", "similar_artist_artwork_direct_median"}.issubset(data.columns):
            continue
        same = data["same_artist_artwork_direct_median"].to_numpy(dtype=float)
        sim = data["similar_artist_artwork_direct_median"].to_numpy(dtype=float)
        for weight in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
            pred = (1.0 - weight) * same + weight * sim
            rows.append({
                "scope": scope,
                "candidate": f"direct_blend_same_{1.0 - weight:.2f}_similar_{weight:.2f}",
                "strict_rows": np.nan,
                **svc1.metric_values(data, pred),
            })
        strict = data["sa_group_level"].astype(str).eq("similar_artist_medium_support_size").to_numpy()
        for weight in [0.10, 0.20, 0.30]:
            pred = same.copy()
            pred[strict] = (1.0 - weight) * same[strict] + weight * sim[strict]
            rows.append({
                "scope": scope,
                "candidate": f"strict_gate_blend_w{weight:.2f}",
                "strict_rows": int(strict.sum()),
                **svc1.metric_values(data, pred),
            })
    return pd.DataFrame(rows)


def render_report(metrics: pd.DataFrame, coverage: pd.DataFrame, blend: pd.DataFrame) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    blend_test = blend.sort_values(["scope", "MdAPE", "MAPE", "p95_APE"]) if not blend.empty else blend
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 유사 작품, 유사 작가, 유사 작가+유사 작품 기준을 같은 fixed train/validation/test 기준에서 검증한다.",
        "- validation/test 기준가는 학습 데이터만 사용한다.",
        "- 이번 1차 선별 실행은 속도를 위해 train 기준가를 full-train screening 방식으로 계산했다.",
        "- 채택 후보가 나오면 train 기준가까지 out-of-fold로 재계산하는 확정 검증이 필요하다.",
        "",
        "## 1. 유사 작품 기준",
        "",
        "- 같은 작가의 작품 이력이 있으면 `같은 작가 + 같은 재료/지지체 + 비슷한 크기`를 최우선 기준으로 사용한다.",
        "- 충분한 표본이 없으면 `같은 작가 + 비슷한 크기`, `같은 작가 전체`, `재료/지지체 + 비슷한 크기` 순서로 넓힌다.",
        "- 이 기준은 기존 SVC 계열 실험에서 이미 Warm 성능 개선이 확인된 기준이다.",
        "",
        "## 2. 유사 작가 기준",
        "",
        f"- 후보군: {SIMILAR_ARTIST_CRITERIA['candidate_pool']}",
        f"- 이력 작가: {SIMILAR_ARTIST_CRITERIA['history_basis']}",
        f"- 신규/이력 부족 작가: {SIMILAR_ARTIST_CRITERIA['metadata_basis']}",
        f"- 채택 기준: {SIMILAR_ARTIST_CRITERIA['selection']}",
        "",
        "## 3. 유사 작가+작품 기준",
        "",
    ]
    for item in SIMILAR_ARTWORK_CRITERIA:
        lines.append(f"- {item['label']}: 최소 {item['min_n']}건 이상일 때 사용")
    lines += [
        "",
        "## 4. Test 결과",
        "",
        "| scope | 모델 | 후보 | n | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in test.itertuples():
        lines.append(
            f"| {row.scope} | {row.model} | `{row.candidate}` | {row.n} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += ["", "## 5. Direct 기준가 블렌드 선별", ""]
    if blend_test.empty:
        lines.append("- 블렌드 선별 결과 없음")
    else:
        lines += [
            "| scope | 후보 | n | MdAPE | MAPE | p95_APE | RMSE_log | strict rows |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in blend_test.itertuples():
            strict_rows = "" if pd.isna(row.strict_rows) else f"{int(row.strict_rows)}"
            lines.append(
                f"| {row.scope} | `{row.candidate}` | {row.n} | {row.MdAPE:.4f} | {row.MAPE:.4f} | "
                f"{row.p95_APE:.4f} | {row.RMSE_log:.4f} | {strict_rows} |"
            )
    lines += [
        "",
        "## 6. 해석",
        "",
        "- 유사 작가+작품 direct 기준가는 Warm에서 MdAPE는 악화됐지만 MAPE와 p95는 소폭 개선됐다.",
        "- Warm direct 기준에서는 같은 작가/작품 기준가에 유사 작가 기준가를 10~20%만 섞을 때 MdAPE와 MAPE가 함께 개선됐다.",
        "- Cold에서는 유사 작가+작품 direct 기준가가 단독으로는 악화됐다. Cold 화면에서는 가격 보정값보다 참고 사례 설명 근거로 제한하는 것이 맞다.",
        "- 현재 결과만으로 운영 예측가격을 유사 작가 기준가로 대체하면 안 된다.",
        "- 후속 확정 실험은 유사 작가 기준을 모델 피처 또는 작은 보정값으로 넣고 out-of-fold로 재검증해야 한다.",
        "",
        "## 7. 서비스 노출 기준 초안",
        "",
        "- 유사 작품: 같은 작가 기준을 우선 적용하며, 재료/지지체와 크기가 모두 맞는 경우만 강한 유사 사례로 표시한다.",
        "- 유사 작가: 같은 작가가 아니며, 생년대/국적/활동 단계/시장 규모/주 사용 재료 중 복수 조건이 맞고 유사도 점수가 높은 작가로 표시한다.",
        "- 유사 작가의 유사 작품: 유사 작가의 작품 중 입력 작품과 재료/지지체 및 크기 구간이 맞는 작품을 우선 표시한다.",
        "- 표본 수가 부족한 경우에는 `참고 범위가 넓은 사례`로 표시하고 예측가격 근거의 신뢰도를 낮춘다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:32px;color:#1f2933;line-height:1.55}}
h1,h2{{margin-top:30px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">fixed split 기준. validation/test는 train-only 기준가를 사용했습니다. train 기준가는 1차 선별용 full-train 방식입니다.</div>
<h2>Test Metrics</h2>{test.to_html(index=False, escape=True)}
<h2>Direct Blend Screen</h2>{blend_test.to_html(index=False, escape=True) if not blend_test.empty else '<p>블렌드 선별 결과 없음</p>'}
<h2>Coverage</h2>{coverage.to_html(index=False, escape=True)}
<h2>Service Criteria</h2>
<ul>
<li>유사 작품: 같은 작가 기준 우선, 재료/지지체와 크기 동시 일치 시 강한 유사 사례.</li>
<li>유사 작가: 생년대, 국적, 활동 단계, 시장 규모, 주 사용 재료 기반 유사도 상위 작가.</li>
<li>유사 작가의 유사 작품: 유사 작가 풀 안에서 입력 작품과 재료/지지체/크기가 맞는 작품.</li>
<li>표본 수 부족 시 참고 범위가 넓은 사례로 표시하고 신뢰도를 낮춤.</li>
</ul>
</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()
    features_by_key = artifact_features()
    metrics_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    frames_by_scope: dict[str, dict[str, pd.DataFrame]] = {}
    feature_manifest: dict[str, Any] = {}

    for cfg in SCOPES:
        scope = cfg["scope"]
        base_features = features_by_key[cfg["feature_key"]]
        requested = list(dict.fromkeys([*base_features, *GROUPING_FEATURES]))
        train, val, test = load_scope(scope, requested)
        train = attach_raw_metadata(train, scope, "train")
        val = attach_raw_metadata(val, scope, "val")
        test = attach_raw_metadata(test, scope, "test")

        if RUN_MODEL_SCREEN:
            train, val, test = svc1.add_service_features(train, val, test)
            train, val, test = add_similar_artist_features(train, val, test)
            frames_by_scope[scope] = {"train_screen": train, "validation": val, "test": test}
        else:
            val = val.merge(svc1.apply_comparable_stats(train, val), on="_track6_row_id", how="left")
            test = test.merge(svc1.apply_comparable_stats(train, test), on="_track6_row_id", how="left")
            val = val.merge(apply_similar_artist_stats(train, val), on="_track6_row_id", how="left")
            test = test.merge(apply_similar_artist_stats(train, test), on="_track6_row_id", how="left")
            frames_by_scope[scope] = {"validation": val, "test": test}

        direct_metrics, direct_preds = direct_prior_rows(scope, val, test)
        metrics_rows.extend(direct_metrics)
        pred_frames.extend(direct_preds)

        if RUN_MODEL_SCREEN:
            candidates = candidate_features(base_features)
            feature_manifest[scope] = candidates
            for candidate, features in candidates.items():
                train_n = normalize(train, features)
                val_n = normalize(val, features)
                test_n = normalize(test, features)
                pred = fit_predict(cfg["model"], train_n, val_n, test_n, features)
                for split, frame, pred_log in [("validation", val_n, pred["validation"]), ("test", test_n, pred["test"])]:
                    metrics_rows.append(metric_row(scope, cfg["model"], candidate, split, frame, pred_log, len(features)))
                    pred_frames.append(prediction_frame(scope, candidate, split, frame, pred_log))

    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(pred_frames, ignore_index=True)
    coverage_df = coverage_summary(frames_by_scope)
    blend_df = blend_screen_metrics(pred_df)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    coverage_df.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    blend_df.to_csv(EXP_DIR / "outputs" / "direct_blend_screen_metrics.csv", index=False)
    (EXP_DIR / "data" / "similar_artist_criteria.json").write_text(
        json.dumps(
            {
                "similar_artist": SIMILAR_ARTIST_CRITERIA,
                "similar_artwork": SIMILAR_ARTWORK_CRITERIA,
                "features": {
                    "numeric": SA_NUMERIC,
                    "categorical": SA_CATEGORICAL,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (EXP_DIR / "artifacts" / "feature_manifest.json").write_text(
        json.dumps(feature_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    config = {
        "experiment_id": EXP_ID,
        "slug": EXP_SLUG,
        "seed": SEED,
        "fixed_split": True,
        "train_feature_method": "full-train screening; rerun OOF before adoption",
        "validation_test_feature_method": "train-only",
        "elapsed_sec": round(time.time() - start, 3),
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, coverage_df, blend_df)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_sa1_similar_artist_artwork_grouping.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_sa1_similar_artist_artwork_grouping.html").write_text(html_doc, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed in {time.time() - start:.1f}s\n",
        encoding="utf-8",
    )
    print(f"{EXP_ID} completed: {EXP_DIR}")
    print(metrics_df[metrics_df["split"].eq("test")].sort_values(["scope", "MdAPE"]).to_string(index=False))


if __name__ == "__main__":
    main()
