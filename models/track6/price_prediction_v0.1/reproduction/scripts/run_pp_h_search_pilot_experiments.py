#!/usr/bin/env python3
"""Run Track6 PP-H external web-search feature pilot experiments.

This is a bounded pilot. It collects public search-result snippets for a
configured artist set, converts the snippets into reproducible search-quality
features, and tests whether those features improve the current Cold candidates.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from duckduckgo_search import DDGS
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import (  # noqa: E402
    BASE_NUMERIC,
    META_ALL,
    META_CATEGORICAL,
    META_NUMERIC,
    base_feature_sets,
    load_cold_with_meta,
    unique,
)


EXPERIMENTS = {
    "PP-H7": {
        "slug": "PP-H7_external_search_feature_pilot_collection",
        "title": "외부 검색 피처 파일럿 수집",
    },
    "PP-H8": {
        "slug": "PP-H8_cold_catboost_search_feature_augmentation",
        "title": "Cold CatBoost 검색 피처 추가 검증",
    },
    "PP-H9": {
        "slug": "PP-H9_cold_lightgbm_quantile_search_feature_augmentation",
        "title": "Cold LightGBM Quantile 검색 피처 추가 검증",
    },
    "PP-H10": {
        "slug": "PP-H10_cold_search_feature_residual_correction",
        "title": "Cold 검색 피처 기반 잔차 보정 검증",
    },
}

SEARCH_DIR = REPO / "data" / "track6" / "external_search"
SEARCH_FEATURE_PATH = SEARCH_DIR / "track6_artist_search_pilot_features.csv"
SEARCH_RAW_PATH = SEARCH_DIR / "track6_artist_search_pilot_raw.jsonl"

SEARCH_NUMERIC = [
    "search_result_count",
    "search_source_count",
    "search_art_context_count",
    "search_exhibition_context_count",
    "search_gallery_context_count",
    "search_award_institution_context_count",
    "search_social_context_count",
    "search_market_context_count",
    "search_homonym_context_count",
    "search_art_match_ratio",
    "search_exhibition_ratio",
    "search_source_ratio",
    "search_quality_score",
    "search_result_count_log",
    "search_art_context_count_log",
    "search_exhibition_context_count_log",
    "search_source_count_log",
    "search_collected_flag",
    "search_success_flag",
    "search_quality_x_log_area",
    "search_art_match_x_followers_log",
    "search_exhibition_x_career_stage",
]

SEARCH_CATEGORICAL = [
    "search_quality_grade",
    "search_size_quality_bucket",
    "search_homonym_risk_grade",
]

SEARCH_CONTEXT_FEATURES = [
    "search_source_count",
    "search_art_context_count",
    "search_exhibition_context_count",
    "search_gallery_context_count",
    "search_award_institution_context_count",
    "search_art_match_ratio",
    "search_quality_score",
    "search_collected_flag",
    "search_success_flag",
    "search_quality_grade",
]

ART_KEYWORDS = [
    "작가",
    "미술",
    "화가",
    "아티스트",
    "art",
    "artist",
    "painting",
    "contemporary",
    "갤러리",
    "gallery",
    "museum",
    "전시",
]
EXHIBITION_KEYWORDS = ["전시", "개인전", "단체전", "아트페어", "비엔날레", "exhibition", "solo", "fair", "biennale"]
GALLERY_KEYWORDS = ["갤러리", "화랑", "gallery", "museum", "미술관", "art center", "kunsthalle"]
AWARD_KEYWORDS = ["수상", "award", "prize", "residency", "레지던시", "기관", "재단", "foundation"]
SOCIAL_KEYWORDS = ["instagram", "인스타", "blog", "블로그", "facebook", "youtube", "뉴스", "news"]
MARKET_KEYWORDS = ["auction", "옥션", "경매", "price", "판매", "작품가격", "작품 가격"]
HOMONYM_KEYWORDS = ["배우", "가수", "축구", "야구", "정치", "기업인", "교수", "아나운서", "model", "singer", "actor"]


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def search_query(name: str) -> str:
    if re.search(r"[가-힣]", name):
        return f"{name} 작가 미술 전시"
    return f"{name} artist art exhibition"


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def domain_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "__UNKNOWN__"


def result_text(result: dict[str, Any]) -> str:
    return " ".join(str(result.get(key, "")) for key in ["title", "body", "href"])


def grade_quality(result_count: int, art_count: int, homonym_count: int, source_count: int) -> str:
    if result_count <= 0:
        return "missing"
    if art_count >= 4 and homonym_count == 0 and source_count >= 3:
        return "high"
    if art_count >= 2 and homonym_count <= 1:
        return "medium"
    return "low"


def row_from_results(name: str, query: str, results: list[dict[str, Any]], error: str = "") -> dict[str, Any]:
    texts = [result_text(result) for result in results]
    domains = sorted({domain_of(str(result.get("href", ""))) for result in results})
    result_count = len(results)
    art_count = sum(contains_any(text, ART_KEYWORDS) for text in texts)
    exhibition_count = sum(contains_any(text, EXHIBITION_KEYWORDS) for text in texts)
    gallery_count = sum(contains_any(text, GALLERY_KEYWORDS) for text in texts)
    award_count = sum(contains_any(text, AWARD_KEYWORDS) for text in texts)
    social_count = sum(contains_any(text, SOCIAL_KEYWORDS) for text in texts)
    market_count = sum(contains_any(text, MARKET_KEYWORDS) for text in texts)
    homonym_count = sum(contains_any(text, HOMONYM_KEYWORDS) for text in texts)
    denom = max(result_count, 1)
    source_count = len([domain for domain in domains if domain != "__UNKNOWN__"])
    quality_score = (art_count / denom) + 0.25 * min(source_count / 5.0, 1.0) - 0.40 * min(homonym_count / denom, 1.0)
    quality_score = float(np.clip(quality_score, 0.0, 1.25))
    return {
        "artist_search_name": name,
        "search_query": query,
        "search_result_count": float(result_count),
        "search_source_count": float(source_count),
        "search_art_context_count": float(art_count),
        "search_exhibition_context_count": float(exhibition_count),
        "search_gallery_context_count": float(gallery_count),
        "search_award_institution_context_count": float(award_count),
        "search_social_context_count": float(social_count),
        "search_market_context_count": float(market_count),
        "search_homonym_context_count": float(homonym_count),
        "search_art_match_ratio": float(art_count / denom),
        "search_exhibition_ratio": float(exhibition_count / denom),
        "search_source_ratio": float(source_count / denom),
        "search_quality_score": quality_score,
        "search_quality_grade": grade_quality(result_count, art_count, homonym_count, source_count),
        "search_homonym_risk_grade": "risk" if homonym_count >= 2 else ("watch" if homonym_count == 1 else "clear"),
        "search_collected_flag": 1.0,
        "search_success_flag": 1.0 if result_count > 0 and not error else 0.0,
        "search_error": error,
        "search_source_domains": ",".join(domains),
        "collected_at": datetime.now().isoformat(timespec="seconds"),
    }


def select_artist_names(limit_artists: int, selection_policy: str) -> list[str]:
    fs = base_feature_sets()
    base_features = unique(fs["generated_all"] + META_ALL)
    train, val, test = load_cold_with_meta(base_features)
    frames = {"train": train, "validation": val, "test": test}
    for frame in frames.values():
        frame["artist_search_name"] = frame["artist_name_ko"].map(clean_artist_name)
    if selection_policy == "train_frequency":
        counts = frames["train"]["artist_search_name"].value_counts()
    else:
        counts = pd.concat([frame["artist_search_name"] for frame in frames.values()], ignore_index=True).value_counts()
    names = [name for name in counts.index.tolist() if name]
    return names[:limit_artists]


def load_cached_features() -> pd.DataFrame:
    if SEARCH_FEATURE_PATH.exists():
        return pd.read_csv(SEARCH_FEATURE_PATH, low_memory=False)
    return pd.DataFrame()


def collect_search_features(limit_artists: int, max_results: int, selection_policy: str, refresh: bool) -> pd.DataFrame:
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    selected_names = select_artist_names(limit_artists, selection_policy)
    cached = load_cached_features()
    if cached.empty or refresh:
        existing_names: set[str] = set()
        rows: list[dict[str, Any]] = []
    else:
        existing_names = set(cached["artist_search_name"].astype(str))
        rows = cached.to_dict(orient="records")

    raw_handle = SEARCH_RAW_PATH.open("a", encoding="utf-8")
    try:
        with DDGS() as ddgs:
            for idx, name in enumerate(selected_names, start=1):
                if name in existing_names:
                    continue
                query = search_query(name)
                error = ""
                results: list[dict[str, Any]] = []
                try:
                    results = list(ddgs.text(query, max_results=max_results))
                except Exception as exc:  # pragma: no cover - external network behavior
                    error = f"{type(exc).__name__}: {exc}"
                raw_handle.write(json.dumps({
                    "artist_search_name": name,
                    "query": query,
                    "max_results": max_results,
                    "results": results,
                    "error": error,
                    "collected_at": datetime.now().isoformat(timespec="seconds"),
                }, ensure_ascii=False) + "\n")
                raw_handle.flush()
                rows.append(row_from_results(name, query, results, error))
                if idx % 25 == 0:
                    print(json.dumps({"collected": idx, "limit": len(selected_names), "latest": name}, ensure_ascii=False))
                time.sleep(0.12)
    finally:
        raw_handle.close()
    out = pd.DataFrame(rows).drop_duplicates("artist_search_name", keep="last")
    add_search_transforms(out)
    out.to_csv(SEARCH_FEATURE_PATH, index=False)
    return out


def add_search_transforms(df: pd.DataFrame) -> pd.DataFrame:
    for col in [
        "search_result_count",
        "search_art_context_count",
        "search_exhibition_context_count",
        "search_source_count",
    ]:
        df[f"{col}_log"] = np.log1p(pd.to_numeric(df[col], errors="coerce").fillna(0.0))
    return df


def add_search_features(frames: list[pd.DataFrame], search_df: pd.DataFrame) -> list[pd.DataFrame]:
    search = search_df.copy()
    add_search_transforms(search)
    keep_cols = ["artist_search_name", *SEARCH_NUMERIC, *SEARCH_CATEGORICAL]
    search = search[[col for col in keep_cols if col in search.columns]].drop_duplicates("artist_search_name")
    out_frames: list[pd.DataFrame] = []
    for frame in frames:
        out = frame.copy()
        out["artist_search_name"] = out["artist_name_ko"].map(clean_artist_name)
        out = out.merge(search, on="artist_search_name", how="left")
        for col in SEARCH_NUMERIC:
            if col not in out.columns:
                out[col] = np.nan
        for col in SEARCH_CATEGORICAL:
            if col not in out.columns:
                out[col] = pd.NA
        out["search_collected_flag"] = pd.to_numeric(out["search_collected_flag"], errors="coerce").fillna(0.0)
        out["search_success_flag"] = pd.to_numeric(out["search_success_flag"], errors="coerce").fillna(0.0)
        for col in [c for c in SEARCH_NUMERIC if c not in {"search_collected_flag", "search_success_flag"}]:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        for col in SEARCH_CATEGORICAL:
            out[col] = out[col].astype("string").fillna("missing").replace({"": "missing"})
        out["search_quality_x_log_area"] = out["search_quality_score"] * pd.to_numeric(out["log_area"], errors="coerce").fillna(0.0)
        followers = pd.to_numeric(out.get("artist_meta_followers_log"), errors="coerce").fillna(0.0)
        out["search_art_match_x_followers_log"] = out["search_art_match_ratio"] * followers
        career_stage = pd.to_numeric(out.get("artist_meta_career_stage"), errors="coerce").fillna(0.0)
        out["search_exhibition_x_career_stage"] = out["search_exhibition_ratio"] * career_stage
        out["search_size_quality_bucket"] = out["size_bucket"].astype(str) + "__" + out["search_quality_grade"].astype(str)
        out_frames.append(out)
    return out_frames


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_source = set(BASE_NUMERIC + META_NUMERIC + SEARCH_NUMERIC)
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
    base = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_values(frame, pred_log),
    }
    covered_mask = frame["search_collected_flag"].to_numpy(dtype=float) > 0
    if covered_mask.any():
        covered_frame = frame.loc[covered_mask].copy()
        covered_pred = pred_log[covered_mask]
        for key, value in metric_values(covered_frame, covered_pred).items():
            base[f"covered_{key}"] = value
        base["covered_n"] = int(covered_mask.sum())
    else:
        base["covered_n"] = 0
    base["coverage_rate"] = float(frame["search_collected_flag"].mean())
    if extra:
        base.update(extra)
    rows.append(base)


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
        "search_collected_flag": frame["search_collected_flag"].to_numpy(dtype=float),
        "search_quality_grade": frame["search_quality_grade"].astype(str).to_numpy(),
        "search_quality_score": frame["search_quality_score"].to_numpy(dtype=float),
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
    return {
        "baseline_catboost_ppw2_like": (
            "PP-W2와 같은 CatBoost 작품조건+작가메타 기준",
            cat_base,
            "검색 피처를 넣지 않은 동일 스크립트 기준선",
        ),
        "catboost_search_context": (
            "CatBoost + 검색 문맥 핵심 피처",
            unique(cat_base + SEARCH_CONTEXT_FEATURES),
            "대칭 트리에서 작품조건, 작가메타, 검색 품질 조합이 가격 구간을 더 잘 나누는지 확인",
        ),
        "catboost_search_all": (
            "CatBoost + 검색 전체 피처",
            unique(cat_base + SEARCH_NUMERIC + SEARCH_CATEGORICAL),
            "검색 노출량, 전시/기관/갤러리 문맥, 동명이인 위험까지 모두 반영",
        ),
        "catboost_search_interaction": (
            "CatBoost + 검색 상호작용 피처",
            unique(cat_base + SEARCH_CONTEXT_FEATURES + [
                "search_quality_x_log_area",
                "search_art_match_x_followers_log",
                "search_exhibition_x_career_stage",
                "search_size_quality_bucket",
            ]),
            "검색 인지도 효과가 작품 크기, 작가 팔로워, 경력 단계에 따라 달라지는지 확인",
        ),
        "baseline_lightgbm_quantile_ppw4_like": (
            "PP-W4와 같은 LightGBM 중앙값 기준",
            lgb_base,
            "검색 피처를 넣지 않은 LightGBM Quantile 기준선",
        ),
        "lightgbm_quantile_search_context": (
            "LightGBM Quantile + 검색 문맥 핵심 피처",
            unique(lgb_base + SEARCH_CONTEXT_FEATURES),
            "중앙값 예측을 기준으로 검색 품질이 안정적인 구간을 만드는지 확인",
        ),
        "lightgbm_quantile_search_all": (
            "LightGBM Quantile + 검색 전체 피처",
            unique(lgb_base + SEARCH_NUMERIC + SEARCH_CATEGORICAL),
            "검색 피처 전체가 중앙값 예측과 MAPE/p95 안정화에 도움이 되는지 확인",
        ),
    }


def load_frames_with_search(search_df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    non_search = [feature for feature in features if feature not in set(SEARCH_NUMERIC + SEARCH_CATEGORICAL)]
    train, val, test = load_cold_with_meta(non_search)
    return tuple(add_search_features([train, val, test], search_df))  # type: ignore[return-value]


def run_h7(search_df: pd.DataFrame, selection_policy: str, limit_artists: int, max_results: int) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = unique(base_feature_sets()["generated_all"] + META_ALL + SEARCH_NUMERIC + SEARCH_CATEGORICAL)
    train, val, test = load_frames_with_search(search_df, features)
    frames = {"train": train, "validation": val, "test": test}
    rows = []
    for split, frame in frames.items():
        rows.append({
            "experiment_id": "PP-H7",
            "candidate": "external_search_collection",
            "scope": "cold",
            "split": split,
            "policy": "search_feature_collection_only",
            "n_rows": int(len(frame)),
            "unique_artists": int(frame["artist_search_name"].nunique()),
            "covered_n": int(frame["search_collected_flag"].sum()),
            "coverage_rate": float(frame["search_collected_flag"].mean()),
            "search_quality_mean": float(frame["search_quality_score"].mean()),
            "search_high_rate": float(frame["search_quality_grade"].eq("high").mean()),
            "search_medium_rate": float(frame["search_quality_grade"].eq("medium").mean()),
            "search_low_rate": float(frame["search_quality_grade"].eq("low").mean()),
        })
    map_rows = [{
        "experiment_id": "PP-H7",
        "selection_policy": selection_policy,
        "limit_artists": limit_artists,
        "max_results_per_artist": max_results,
        "feature_path": str(SEARCH_FEATURE_PATH.relative_to(REPO)),
        "raw_path": str(SEARCH_RAW_PATH.relative_to(REPO)),
        "note": "DuckDuckGo public search snippets are converted into capped count/context features; this is not total web result count.",
    }]
    return rows, [], map_rows


def run_direct_models(search_df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidates = feature_candidates()
    all_features = unique([feature for _name, (_strategy, features, _hypothesis) in candidates.items() for feature in features])
    train, val, test = load_frames_with_search(search_df, all_features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for candidate, (strategy, features, hypothesis) in candidates.items():
        if candidate.startswith("catboost") or candidate == "baseline_catboost_ppw2_like":
            exp_id = "PP-H8"
            model_name = "catboost"
            loss = "RMSE"
            policy = "cold_catboost_search_feature_augmentation"
        else:
            exp_id = "PP-H9"
            model_name = "lightgbm"
            loss = "quantile"
            policy = "cold_lightgbm_quantile_search_feature_augmentation"
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


def run_residual(search_df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    candidates = feature_candidates()
    base_name = "catboost_search_interaction"
    strategy, features, hypothesis = candidates[base_name]
    train, val, test = load_frames_with_search(search_df, features)
    base_pred = fit_direct("catboost", "RMSE", train, val, test, features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, "PP-H10", f"base_{base_name}", split, frame, base_pred[split], "search_feature_base_catboost", {
            "stage1_model": "catboost",
            "feature_strategy": strategy,
            "n_features": len(features),
        })
        preds.append(prediction_frame("PP-H10", f"base_{base_name}", split, frame, base_pred[split], "search_feature_base_catboost", {
            "stage1_model": "catboost",
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
    for cap in [0.15, 0.25, 0.35]:
        for strength in [0.50, 0.75, 1.00]:
            cand = f"{base_name}_huber_residual_cap{cap:g}_s{strength:g}"
            maps.append({
                "experiment_id": "PP-H10",
                "base_candidate": base_name,
                "residual_model": "HuberRegressor",
                "cap": cap,
                "strength": strength,
                "hypothesis": "검색 품질로 생기는 과대/과소 예측 구간을 검증 잔차 기반으로 완만하게 보정",
            })
            for split, frame, pred, resid in [
                ("validation", val, base_pred["validation"], val_resid),
                ("test", test, base_pred["test"], test_resid),
            ]:
                final = pred + np.clip(resid, -cap, cap) * strength
                add_metric(rows, "PP-H10", cand, split, frame, final, "search_feature_huber_residual_correction", {
                    "stage1_model": "catboost",
                    "residual_model": "HuberRegressor",
                    "cap": cap,
                    "strength": strength,
                })
                preds.append(prediction_frame("PP-H10", cand, split, frame, final, "search_feature_huber_residual_correction", {
                    "stage1_model": "catboost",
                    "residual_model": "HuberRegressor",
                    "cap": cap,
                    "strength": strength,
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
        "- 목적: 외부 검색 기반 작가 인지도/문맥 피처가 Cold 가격 예측을 개선하는지 확인한다.",
        "- 기준: 기존 데이터 split은 유지하고, 검색 결과는 작가명 기준으로만 수집한다.",
        "- 주의: 이번 파일럿의 `search_result_count`는 검색엔진 전체 결과 수가 아니라 요청당 반환된 상위 결과 수와 그 문맥 분석값이다.",
        "",
    ]
    if not metrics_df.empty and "MdAPE" in metrics_df.columns:
        test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
        lines += [
            "## Test 결과 상위",
            "",
            "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 검색 커버리지 | 검색 커버 행 MdAPE |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in test.head(20).itertuples():
            covered_mdape = getattr(row, "covered_MdAPE", np.nan)
            coverage_rate = getattr(row, "coverage_rate", np.nan)
            lines.append(f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {coverage_rate:.3f} | {covered_mdape:.4f} |")
    else:
        lines += ["## 수집 커버리지", "", markdown_table(metrics_df)]
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-artists", type=int, default=120)
    parser.add_argument("--max-results", type=int, default=6)
    parser.add_argument("--selection-policy", choices=["all_frequency", "train_frequency"], default="all_frequency")
    parser.add_argument("--refresh-search", action="store_true")
    parser.add_argument("--skip-collect", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = time.time()
    if args.skip_collect and SEARCH_FEATURE_PATH.exists():
        search_df = pd.read_csv(SEARCH_FEATURE_PATH, low_memory=False)
        add_search_transforms(search_df)
    else:
        search_df = collect_search_features(args.limit_artists, args.max_results, args.selection_policy, args.refresh_search)

    summary_frames: list[pd.DataFrame] = []
    h7_rows, h7_preds, h7_maps = run_h7(search_df, args.selection_policy, args.limit_artists, args.max_results)
    summary_frames.append(write_exp("PP-H7", h7_rows, h7_preds, h7_maps))

    direct_rows, direct_preds, direct_maps = run_direct_models(search_df)
    for exp_id in ["PP-H8", "PP-H9"]:
        rows = [row for row in direct_rows if row["experiment_id"] == exp_id]
        preds = [pred for pred in direct_preds if not pred.empty and str(pred["experiment_id"].iloc[0]) == exp_id]
        maps = [row for row in direct_maps if row["experiment_id"] == exp_id]
        summary_frames.append(write_exp(exp_id, rows, preds, maps))

    h10_rows, h10_preds, h10_maps = run_residual(search_df)
    summary_frames.append(write_exp("PP-H10", h10_rows, h10_preds, h10_maps))

    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(BASE_EXP_DIR / "PP-H_search_pilot_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-H_search_pilot_summary_metrics.csv",
        "search_features": str(SEARCH_FEATURE_PATH.relative_to(REPO)),
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
