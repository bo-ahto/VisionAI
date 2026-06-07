from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0605_artist_level_model_retrain_revalidation"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
SPLIT_ROOT = PROJECT_ROOT / "data/track6_split_with_year_type_edition_size_artist_name"
ARTIFACT_MANIFEST = PROJECT_ROOT / "data/track6/artifacts/track6_artifact_manifest.json"
SEARCH_FEATURE_PATH = PROJECT_ROOT / "data/track6/external_search/track6_artist_search_pilot_features.csv"
RAW_COLLECTED = PROJECT_ROOT / "data/track4_primary_market_raw_collected.csv"
GALLERY_CLEANED = PROJECT_ROOT / "data/track4_primary_market_cleaned_v2.csv"


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
    "artist_meta_nationality_ko",
]

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

EXTERNAL_NUMERIC = [
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
    "gallery_tier_raw_numeric",
    "gallery_tier_raw_available_flag",
    "gallery_tier_validated_score",
    "gallery_tier_validated_available_flag",
    "gallery_tier_any_available_flag",
    "gallery_city_count",
    "gallery_city_count_log",
    "exhibition_total_x_log_area",
    "exhibition_total_x_followers_log",
    "gallery_validated_x_followers_log",
    "gallery_tier_x_exhibition_total_log",
]

EXTERNAL_CATEGORICAL = [
    "gallery_tier_raw_bucket",
    "gallery_tier_validated",
    "gallery_ref_type",
    "gallery_audit_status",
    "gallery_feature_source",
    "exhibition_size_bucket",
    "gallery_exhibition_bucket",
]

BASE_NUMERIC = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
GENERATED = [
    "size_bucket",
    "shape_bucket",
    "medium_size_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]


@dataclass(frozen=True)
class CorrectionRule:
    name: str
    cols: tuple[str, ...]
    min_n: int
    shrinkage: float
    cap: float


WARM_RULES = [
    CorrectionRule("artist_history_band", ("artist_history_band",), min_n=20, shrinkage=0.65, cap=0.30),
    CorrectionRule("area_pred_price", ("area_band", "pred_price_band"), min_n=20, shrinkage=0.65, cap=0.30),
]

COLD_RULES = [
    CorrectionRule("qwidth_pred_price", ("uncertainty_band", "pred_price_band"), min_n=25, shrinkage=0.65, cap=0.30),
    CorrectionRule("source_area", ("track4_source", "area_band"), min_n=25, shrinkage=0.65, cap=0.30),
]


def stable_bucket(value: object, seed: int, modulo: int = 10_000) -> int:
    text = f"{value}::{seed}"
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16) % modulo


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = value.strip()
    if value.endswith("_A") or value.endswith("_B") or value.endswith("_C"):
        value = value[:-2].strip()
    return " ".join(value.split())


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def artifact_features() -> dict[str, list[str]]:
    manifest = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for item in manifest["artifacts"]:
        if item["key"] == "warm_price_model":
            out["warm"] = item["features"]
        if item["key"] == "cold_lightgbm_price_model":
            out["cold_lightgbm"] = item["features"]
    return out


def read_master() -> pd.DataFrame:
    files = [
        "track6_train.csv",
        "track6_val_warm.csv",
        "track6_test_warm.csv",
        "track6_val_cold.csv",
        "track6_test_cold.csv",
    ]
    frames = []
    for file_name in files:
        frame = pd.read_csv(SPLIT_ROOT / file_name, low_memory=False)
        frame["source_split"] = file_name.replace("track6_", "").replace(".csv", "")
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True, sort=False)
    df = df.drop_duplicates("_track6_row_id", keep="first")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    df = df[(df["price_krw"] > 0) & df["ln_price_krw"].notna()].copy()
    df["artist_key"] = df["artist_key"].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    df["artist_search_name"] = df["artist_name_ko"].map(clean_artist_name)
    return df.reset_index(drop=True)


def boolish(series: pd.Series | None, index: pd.Index) -> pd.Series:
    if series is None:
        return pd.Series(0.0, index=index)
    return series.astype("string").str.lower().isin(["true", "1", "yes", "y"]).astype(float)


def engineer_meta(df: pd.DataFrame) -> pd.DataFrame:
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
    out["artist_meta_is_p1_flag"] = boolish(out.get("artist_meta_is_p1"), out.index)
    out["artist_meta_has_international_flag"] = boolish(out.get("artist_meta_has_international"), out.index)
    out["is_high_price_candidate_flag"] = boolish(out.get("is_high_price_candidate"), out.index)
    for col in META_CATEGORICAL:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def add_search_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if SEARCH_FEATURE_PATH.exists():
        search = pd.read_csv(SEARCH_FEATURE_PATH, low_memory=False).drop_duplicates("artist_search_name", keep="last")
        out = out.merge(search, on="artist_search_name", how="left")
    for col in SEARCH_NUMERIC:
        if col not in out.columns:
            out[col] = 0.0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in SEARCH_CATEGORICAL:
        if col not in out.columns:
            out[col] = "missing"
        out[col] = out[col].astype("string").fillna("missing").replace({"": "missing"})
    out["search_quality_x_log_area"] = out["search_quality_score"] * pd.to_numeric(out["log_area"], errors="coerce").fillna(0.0)
    out["search_art_match_x_followers_log"] = out["search_art_match_ratio"] * pd.to_numeric(out["artist_meta_followers_log"], errors="coerce").fillna(0.0)
    stage = pd.to_numeric(out["artist_meta_career_stage"], errors="coerce").fillna(0.0)
    out["search_exhibition_x_career_stage"] = out["search_exhibition_ratio"] * stage
    out["search_size_quality_bucket"] = out["size_bucket"].astype(str) + "__" + out["search_quality_grade"].astype(str)
    return out


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
    values = pd.to_numeric(series, errors="coerce")
    return values.mask((values < 0) | (values > 200))


def build_external_map() -> pd.DataFrame:
    source_cols = ["track4_source", "track4_source_row_index"]
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
    raw = pd.read_csv(RAW_COLLECTED, usecols=lambda col: col in raw_cols, low_memory=False)
    raw["track4_source_row_index"] = pd.to_numeric(raw["track4_source_row_index"], errors="coerce")
    raw = raw.dropna(subset=source_cols).copy()
    raw["track4_source_row_index"] = raw["track4_source_row_index"].astype(int)
    raw = raw.drop_duplicates(source_cols, keep="first")
    raw = raw.rename(
        columns={
            "saatchi__solo_count": "artist_exhibition_solo_count",
            "saatchi__group_count": "artist_exhibition_group_count",
            "saatchi__fair_count": "artist_exhibition_fair_count",
            "saatchi__gallery_city_count": "gallery_city_count",
        }
    )
    for col in ["artist_exhibition_solo_count", "artist_exhibition_group_count", "artist_exhibition_fair_count"]:
        raw[col] = clean_count(raw[col])
    raw["gallery_tier_raw_numeric"] = pd.to_numeric(raw.get("saatchi__gallery_tier"), errors="coerce")
    raw["gallery_tier_raw_numeric"] = raw["gallery_tier_raw_numeric"].where(
        raw["gallery_tier_raw_numeric"].notna(),
        pd.to_numeric(raw.get("gallery_primary__gallery_tier"), errors="coerce"),
    )
    raw["gallery_city_count"] = pd.to_numeric(raw.get("gallery_city_count"), errors="coerce")

    gallery_cols = ["track4_source", "track4_source_row_index", "gallery_tier_validated", "gallery_ref_type", "gallery_audit_status"]
    gallery = pd.read_csv(GALLERY_CLEANED, usecols=lambda col: col in gallery_cols, low_memory=False)
    gallery["track4_source_row_index"] = pd.to_numeric(gallery["track4_source_row_index"], errors="coerce")
    gallery = gallery.dropna(subset=source_cols).copy()
    gallery["track4_source_row_index"] = gallery["track4_source_row_index"].astype(int)
    gallery = gallery.drop_duplicates(source_cols, keep="first")
    return raw.merge(gallery, on=source_cols, how="left")


def add_external_features(df: pd.DataFrame) -> pd.DataFrame:
    ext = build_external_map()
    out = df.copy()
    out["track4_source_row_index"] = pd.to_numeric(out["track4_source_row_index"], errors="coerce")
    out = out.merge(ext, on=["track4_source", "track4_source_row_index"], how="left", suffixes=("", "_ext"))
    count_cols = ["artist_exhibition_solo_count", "artist_exhibition_group_count", "artist_exhibition_fair_count"]
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
        [out["gallery_tier_validated_available_flag"].eq(1), out["gallery_tier_raw_available_flag"].eq(1)],
        ["validated", "raw"],
        default="missing",
    )
    total_log = pd.to_numeric(out["artist_exhibition_total_count_log"], errors="coerce").fillna(0.0)
    log_area = pd.to_numeric(out["log_area"], errors="coerce").fillna(0.0)
    followers_log = pd.to_numeric(out["artist_meta_followers_log"], errors="coerce").fillna(0.0)
    tier_score = pd.to_numeric(out["gallery_tier_validated_score"], errors="coerce").fillna(0.0)
    out["exhibition_total_x_log_area"] = total_log * log_area
    out["exhibition_total_x_followers_log"] = total_log * followers_log
    out["gallery_validated_x_followers_log"] = tier_score * followers_log
    out["gallery_tier_x_exhibition_total_log"] = tier_score * total_log
    out["exhibition_size_bucket"] = out["size_bucket"].astype(str) + "__" + pd.cut(
        total_log, bins=[-np.inf, 0.0, 1.5, 3.0, np.inf], labels=["none", "low", "mid", "high"]
    ).astype(str)
    out["gallery_exhibition_bucket"] = out["gallery_feature_source"].astype(str) + "__" + out["exhibition_size_bucket"].astype(str)
    for col in EXTERNAL_NUMERIC:
        out[col] = pd.to_numeric(out.get(col), errors="coerce").fillna(0.0)
    for col in EXTERNAL_CATEGORICAL:
        out[col] = out.get(col, pd.Series(index=out.index, dtype=object)).astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def add_generated(train: pd.DataFrame, frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    edges = np.quantile(values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)
    if len(edges) < 2:
        edges = np.array([-np.inf, np.inf])
    large_cut = float(np.nanquantile(pd.to_numeric(train["area_cm2"], errors="coerce"), 0.80))

    def transform(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        log_area = pd.to_numeric(out["log_area"], errors="coerce")
        aspect = pd.to_numeric(out["aspect_ratio"], errors="coerce")
        area = pd.to_numeric(out["area_cm2"], errors="coerce")
        is_3d = out["is_3d_candidate"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])
        labels = [f"q{i + 1}" for i in range(len(edges) - 1)]
        out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
        out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
        out["shape_bucket"] = np.select(
            [aspect.isna(), aspect < 0.65, aspect <= 1.55, aspect <= 2.5, aspect > 2.5],
            ["__MISSING__", "tall", "balanced", "wide", "extreme_wide"],
            default="__MISSING__",
        )
        out["medium_size_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["support_size_bucket"] = out["support_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["medium_shape_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["shape_bucket"].astype(str)
        out["is_large_2d"] = ((area >= large_cut) & ~is_3d).astype(str)
        out["is_large_3d"] = ((area >= large_cut) & is_3d).astype(str)
        return out

    return [transform(frame) for frame in frames]


def prepare_features(train: pd.DataFrame, frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    generated = add_generated(train, frames)
    return [add_search_features(add_external_features(engineer_meta(frame))) for frame in generated]


def artist_level_split(master: pd.DataFrame, seed: int) -> dict[str, pd.DataFrame]:
    artists = pd.Series(master["artist_key"].dropna().unique()).sort_values().to_numpy()
    buckets = pd.Series(artists).map(lambda artist: stable_bucket(artist, seed, 10_000)).to_numpy()
    cold_cal_artists = set(artists[buckets < 700])
    cold_test_artists = set(artists[(buckets >= 700) & (buckets < 1_400)])
    warm_pool = master[~master["artist_key"].isin(cold_cal_artists | cold_test_artists)].copy()
    cold_cal = master[master["artist_key"].isin(cold_cal_artists)].copy()
    cold_test = master[master["artist_key"].isin(cold_test_artists)].copy()

    train_parts = []
    warm_cal_parts = []
    warm_test_parts = []
    for _, group in warm_pool.groupby("artist_key", observed=False):
        group = group.sort_values("_track6_row_id").copy()
        if len(group) < 8:
            train_parts.append(group)
            continue
        bucket = group["_track6_row_id"].map(lambda row_id: stable_bucket(row_id, seed, 10_000))
        warm_cal = group[bucket < 1_000]
        warm_test = group[(bucket >= 1_000) & (bucket < 2_000)]
        train = group[~group.index.isin(warm_cal.index.union(warm_test.index))]
        if len(warm_cal) == 0 or len(warm_test) == 0 or len(train) < 3:
            train_parts.append(group)
            continue
        train_parts.append(train)
        warm_cal_parts.append(warm_cal)
        warm_test_parts.append(warm_test)
    train = pd.concat(train_parts, ignore_index=True)
    warm_cal = pd.concat(warm_cal_parts, ignore_index=True) if warm_cal_parts else pd.DataFrame(columns=master.columns)
    warm_test = pd.concat(warm_test_parts, ignore_index=True) if warm_test_parts else pd.DataFrame(columns=master.columns)
    return {
        "train": train,
        "warm_calibration": warm_cal,
        "warm_test": warm_test,
        "cold_calibration": cold_cal,
        "cold_test": cold_test,
    }


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_source = set(BASE_NUMERIC + META_NUMERIC + SEARCH_NUMERIC + EXTERNAL_NUMERIC)
    numeric = [col for col in features if col in numeric_source]
    categorical = [col for col in features if col not in numeric]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
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
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000))])


def lgbm_quantile_model(features: list[str], alpha: float, seed: int) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline(
        [
            ("prep", ColumnTransformer(transformers)),
            (
                "model",
                LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    n_estimators=300,
                    learning_rate=0.04,
                    num_leaves=31,
                    min_child_samples=35,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    reg_lambda=1.2,
                    random_state=seed,
                    verbosity=-1,
                ),
            ),
        ]
    )


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float | int]:
    actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
    actual_price = frame["price_krw"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    ratio = pred_price / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "over_3x_n": int((ratio >= 3.0).sum()),
        "under_1_3x_n": int((ratio <= (1.0 / 3.0)).sum()),
    }


def band_price(price: float) -> str:
    if pd.isna(price):
        return "price_missing"
    if price < 500_000:
        return "under_0_5m"
    if price < 1_000_000:
        return "0_5m_1m"
    if price < 3_000_000:
        return "1m_3m"
    if price < 10_000_000:
        return "3m_10m"
    if price < 30_000_000:
        return "10m_30m"
    if price < 100_000_000:
        return "30m_100m"
    return "100m_plus"


def band_area(area: float) -> str:
    if pd.isna(area) or area <= 0:
        return "area_missing"
    if area < 100:
        return "tiny"
    if area < 1_000:
        return "small"
    if area < 5_000:
        return "medium"
    if area < 20_000:
        return "large"
    if area < 80_000:
        return "very_large"
    return "extreme_large"


def band_count(value: float, prefix: str) -> str:
    if pd.isna(value):
        return f"{prefix}_missing"
    if value <= 5:
        return f"{prefix}_le_5"
    if value <= 10:
        return f"{prefix}_6_10"
    if value <= 30:
        return f"{prefix}_11_30"
    if value <= 100:
        return f"{prefix}_31_100"
    return f"{prefix}_100_plus"


def band_qwidth(value: float) -> str:
    if pd.isna(value):
        return "qwidth_missing"
    if value <= 1.5:
        return "qwidth_low"
    if value <= 2.5:
        return "qwidth_mid"
    if value <= 4.0:
        return "qwidth_high"
    return "qwidth_extreme"


def meta_band(frame: pd.DataFrame) -> pd.Series:
    cols = ["artist_meta_total_works", "artist_meta_followers", "artist_meta_birth_year", "artist_meta_nationality_ko"]
    score = pd.Series(0.0, index=frame.index)
    for col in cols:
        value = frame.get(col, pd.Series(index=frame.index, dtype=object))
        score += value.notna().astype(float)
    score = score / len(cols)
    return pd.cut(score, [-0.01, 0.25, 0.5, 0.75, 1.01], labels=["meta_low", "meta_mid", "meta_good", "meta_high"]).astype(str)


def enrich_for_correction(frame: pd.DataFrame, pred_log: np.ndarray, route: str, q10: np.ndarray | None = None, q90: np.ndarray | None = None) -> pd.DataFrame:
    out = frame.copy()
    out["route"] = route
    out["pred_log"] = pred_log
    out["pred_price"] = np.clip(np.exp(pred_log), 1_000.0, None)
    out["actual_price"] = out["price_krw"].astype(float)
    out["actual_log"] = out["ln_price_krw"].astype(float)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["area_band"] = pd.to_numeric(out["area_cm2"], errors="coerce").map(band_area)
    out["pred_price_band"] = out["pred_price"].map(band_price)
    out["artist_history_band"] = pd.to_numeric(out.get("artist_works_count_retrain", out.get("artist_works_count_train")), errors="coerce").map(lambda x: band_count(x, "artist_n"))
    if q10 is not None and q90 is not None:
        out["quantile_width_log"] = np.maximum(q90 - q10, 0.0)
        out["price_range_ratio"] = np.exp(np.clip(out["quantile_width_log"], 0.0, 8.0))
    else:
        out["quantile_width_log"] = 0.0
        out["price_range_ratio"] = 1.0
    out["uncertainty_band"] = out["price_range_ratio"].map(band_qwidth)
    out["meta_completeness_band"] = meta_band(out)
    return out


def operational_segment(row: pd.Series) -> str:
    route = row["route"]
    pred = float(row["pred_price"])
    area = float(row["area_cm2"]) if pd.notna(row["area_cm2"]) else np.nan
    qwidth = float(row.get("price_range_ratio", 1.0))
    meta = str(row.get("meta_completeness_band", ""))
    artist_n = pd.to_numeric(pd.Series([row.get("artist_works_count_retrain", row.get("artist_works_count_train"))]), errors="coerce").iloc[0]
    if route == "warm":
        if pd.notna(artist_n) and artist_n <= 10:
            return "warm_low_sample"
        if pred >= 30_000_000 or (pd.notna(area) and area >= 20_000):
            return "warm_upper_tail_or_large"
        return "warm_regular"
    if qwidth >= 6.0:
        return "cold_extreme_uncertainty"
    if pred < 1_000_000 and qwidth >= 4.0:
        return "cold_low_price_uncertain"
    if meta in {"meta_low", "meta_mid"}:
        return "cold_meta_sparse"
    if pred >= 30_000_000 or (pd.notna(area) and area >= 20_000):
        return "cold_upper_tail_or_large"
    return "cold_regular"


def learn_rule(calibration: pd.DataFrame, rule: CorrectionRule) -> dict[tuple[str, ...], float]:
    mapping: dict[tuple[str, ...], float] = {}
    for key, group in calibration.groupby(list(rule.cols), dropna=False, observed=False):
        if len(group) < rule.min_n:
            continue
        if not isinstance(key, tuple):
            key = (key,)
        correction = float(np.nanmedian(group["residual_log"])) * rule.shrinkage
        mapping[tuple(str(item) for item in key)] = max(-rule.cap, min(rule.cap, correction))
    return mapping


def apply_rule(frame: pd.DataFrame, rule: CorrectionRule, mapping: dict[tuple[str, ...], float]) -> pd.Series:
    values = []
    for _, row in frame.iterrows():
        key = tuple(str(row.get(col)) for col in rule.cols)
        values.append(mapping.get(key, 0.0))
    return pd.Series(values, index=frame.index)


def apply_expert_correction(calibration: pd.DataFrame, test: pd.DataFrame, route: str) -> tuple[np.ndarray, pd.DataFrame]:
    out = test.copy()
    rules = WARM_RULES if route == "warm" else COLD_RULES
    for rule in rules:
        correction = apply_rule(out, rule, learn_rule(calibration, rule))
        out[f"{rule.name}_w75"] = np.exp(np.log(out["pred_price"]) + correction * 0.75)
        out[f"{rule.name}_w100"] = np.exp(np.log(out["pred_price"]) + correction)
    out["operational_segment"] = out.apply(operational_segment, axis=1)
    selected_cols = []
    for _, row in out.iterrows():
        segment = row["operational_segment"]
        if route == "warm":
            if segment == "warm_low_sample":
                selected_cols.append("area_pred_price_w75")
            elif segment == "warm_regular":
                selected_cols.append("artist_history_band_w100")
            else:
                selected_cols.append("pred_price")
        else:
            if segment == "cold_extreme_uncertainty":
                selected_cols.append("qwidth_pred_price_w100")
            elif segment == "cold_low_price_uncertain":
                selected_cols.append("source_area_w100")
            elif segment == "cold_meta_sparse":
                selected_cols.append("qwidth_pred_price_w75")
            else:
                selected_cols.append("pred_price")
    corrected_price = np.asarray([row[col] for row, col in zip(out.to_dict(orient="records"), selected_cols, strict=False)], dtype=float)
    corrected_log = np.log(np.clip(corrected_price, 1_000.0, None))
    out["expert_selected_col"] = selected_cols
    out["expert_pred_log"] = corrected_log
    out["expert_pred_price"] = corrected_price
    return corrected_log, out


def fit_warm(train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    train = normalize(train, features)
    cal = normalize(cal, features)
    test = normalize(test, features)
    model = huber_model(features)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    return np.asarray(model.predict(cal[features]), dtype=float), np.asarray(model.predict(test[features]), dtype=float)


def fit_cold_quantile(train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame, features: list[str], seed: int) -> dict[str, dict[str, np.ndarray]]:
    train = normalize(train, features)
    cal = normalize(cal, features)
    test = normalize(test, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, dict[str, np.ndarray]] = {}
    for label, alpha in [("q10", 0.1), ("q50", 0.5), ("q90", 0.9)]:
        model = lgbm_quantile_model(features, alpha, seed)
        model.fit(train[features], y)
        out[label] = {
            "calibration": np.asarray(model.predict(cal[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    return out


def prediction_rows(seed: int, route: str, split: str, frame: pd.DataFrame, baseline_log: np.ndarray, expert_log: np.ndarray | None = None) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "seed": seed,
            "route": route,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "title_raw": frame["title_raw"].astype(str).to_numpy(),
            "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
            "actual_price": frame["price_krw"].to_numpy(dtype=float),
            "baseline_pred_log": baseline_log,
            "baseline_pred_price": np.clip(np.exp(baseline_log), 1_000.0, None),
        }
    )
    if expert_log is not None:
        out["expert_pred_log"] = expert_log
        out["expert_pred_price"] = np.clip(np.exp(expert_log), 1_000.0, None)
    return out


def run_seed(master: pd.DataFrame, seed: int, warm_features: list[str], cold_features: list[str]) -> tuple[list[dict[str, Any]], pd.DataFrame, dict[str, int]]:
    split = artist_level_split(master, seed)
    train_raw = split["train"].copy()
    train_counts = train_raw["artist_key"].value_counts()
    for key in split:
        split[key] = split[key].copy()
        split[key]["artist_works_count_retrain"] = split[key]["artist_key"].map(train_counts).fillna(0).astype(float)
    prepared = dict(zip(split.keys(), prepare_features(train_raw, [split[key] for key in split.keys()]), strict=False))
    train = prepared["train"]
    metrics_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []

    warm_cal = prepared["warm_calibration"]
    warm_test = prepared["warm_test"]
    if len(warm_cal) >= 50 and len(warm_test) >= 50:
        warm_cal_pred, warm_test_pred = fit_warm(train, warm_cal, warm_test, warm_features)
        warm_cal_e = enrich_for_correction(warm_cal, warm_cal_pred, "warm")
        warm_test_e = enrich_for_correction(warm_test, warm_test_pred, "warm")
        warm_expert_log, warm_test_corr = apply_expert_correction(warm_cal_e, warm_test_e, "warm")
        metrics_rows.append({"seed": seed, "route": "warm", "policy": "baseline_retrained_huber", **metric_values(warm_test, warm_test_pred)})
        metrics_rows.append({"seed": seed, "route": "warm", "policy": "expert_cause_aware_correction", **metric_values(warm_test, warm_expert_log)})
        pred_frames.append(prediction_rows(seed, "warm", "test", warm_test, warm_test_pred, warm_expert_log))

    cold_cal = prepared["cold_calibration"]
    cold_test = prepared["cold_test"]
    if len(cold_cal) >= 100 and len(cold_test) >= 100:
        bundle = fit_cold_quantile(train, cold_cal, cold_test, cold_features, seed)
        cold_cal_pred = bundle["q50"]["calibration"]
        cold_test_pred = bundle["q50"]["test"]
        cold_cal_e = enrich_for_correction(cold_cal, cold_cal_pred, "cold", bundle["q10"]["calibration"], bundle["q90"]["calibration"])
        cold_test_e = enrich_for_correction(cold_test, cold_test_pred, "cold", bundle["q10"]["test"], bundle["q90"]["test"])
        cold_expert_log, cold_test_corr = apply_expert_correction(cold_cal_e, cold_test_e, "cold")
        metrics_rows.append({"seed": seed, "route": "cold", "policy": "baseline_retrained_lgbm_quantile", **metric_values(cold_test, cold_test_pred)})
        metrics_rows.append({"seed": seed, "route": "cold", "policy": "expert_cause_aware_correction", **metric_values(cold_test, cold_expert_log)})
        pred_frames.append(prediction_rows(seed, "cold", "test", cold_test, cold_test_pred, cold_expert_log))

    sizes = {key: int(len(value)) for key, value in split.items()}
    pred_df = pd.concat(pred_frames, ignore_index=True, sort=False) if pred_frames else pd.DataFrame()
    return metrics_rows, pred_df, sizes


def summarize(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (route, policy), group in metrics_df.groupby(["route", "policy"], observed=False):
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "over_3x_n", "under_1_3x_n"]:
            values = pd.to_numeric(group[metric], errors="coerce")
            rows.append(
                {
                    "route": route,
                    "policy": policy,
                    "metric": metric,
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=0)),
                    "min": float(values.min()),
                    "median": float(values.median()),
                    "max": float(values.max()),
                }
            )
    return pd.DataFrame(rows)


def compare_baseline_expert(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (seed, route), group in metrics_df.groupby(["seed", "route"], observed=False):
        if len(group) < 2:
            continue
        baseline = group[group["policy"].str.startswith("baseline")].iloc[0]
        expert = group[group["policy"].eq("expert_cause_aware_correction")].iloc[0]
        row = {"seed": seed, "route": route}
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "over_3x_n", "under_1_3x_n"]:
            row[f"baseline_{metric}"] = baseline[metric]
            row[f"expert_{metric}"] = expert[metric]
            row[f"delta_{metric}"] = expert[metric] - baseline[metric]
        rows.append(row)
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    view = frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    if view.empty:
        return "_결과 없음_"
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in view.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append("" if pd.isna(value) else f"{value:.4f}")
            else:
                values.append("" if pd.isna(value) else str(value).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(metrics_df: pd.DataFrame, summary_df: pd.DataFrame, comparison_df: pd.DataFrame, split_sizes: pd.DataFrame, config: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    delta_summary = (
        comparison_df.groupby("route", observed=False)[
            ["delta_MdAPE", "delta_MAPE", "delta_p95_APE", "delta_RMSE_log", "delta_over_3x_n", "delta_under_1_3x_n"]
        ]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
    )
    delta_summary.columns = ["_".join([str(x) for x in col if x]) for col in delta_summary.columns.to_flat_index()]
    warm_base = summary_df[(summary_df["route"].eq("warm")) & (summary_df["policy"].eq("baseline_retrained_huber"))].set_index("metric")["mean"]
    warm_expert = summary_df[(summary_df["route"].eq("warm")) & (summary_df["policy"].eq("expert_cause_aware_correction"))].set_index("metric")["mean"]
    cold_base = summary_df[(summary_df["route"].eq("cold")) & (summary_df["policy"].eq("baseline_retrained_lgbm_quantile"))].set_index("metric")["mean"]
    cold_expert = summary_df[(summary_df["route"].eq("cold")) & (summary_df["policy"].eq("expert_cause_aware_correction"))].set_index("metric")["mean"]
    md = f"""# Artist-Level 모델 재학습 포함 재검증 결과

## 1. 목적

- 기존 보정/라우팅 정책이 고정 split에서만 좋아진 것인지 확인
- seed마다 작가 단위로 새 cold holdout을 만들고 모델을 다시 학습
- Warm은 같은 작가가 train에 남아 있는 행 단위 holdout으로 재학습 검증
- Cold는 작가를 통째로 train에서 제외한 calibration/test로 재학습 검증

## 2. 검증 설정

```json
{json.dumps(config, ensure_ascii=False, indent=2)}
```

## 3. 정책별 반복 지표

{md_table(summary_df)}

## 4. 기준선 대비 보정 정책 변화량

{md_table(delta_summary)}

## 5. seed별 변화량

{md_table(comparison_df)}

## 6. split 크기

{md_table(split_sizes)}

## 7. 해석 기준

- `delta_*`가 음수이면 보정 정책이 기준선보다 개선
- Cold에서 `under_1_3x_n` 증가가 반복되면 과소 예측 리스크가 커진 것으로 해석
- 이 실험은 모델을 다시 학습하는 artist-level 검증이므로, 이전 보정값 재분할 검증보다 최종 채택 판단에 더 가깝다

## 8. 실행 결론

- Warm 재학습 기준선은 평균 MdAPE `{warm_base.get("MdAPE", np.nan):.4f}`, MAPE `{warm_base.get("MAPE", np.nan):.4f}`, p95_APE `{warm_base.get("p95_APE", np.nan):.4f}`였다.
- Warm 원인별 보정 적용 후 평균 MdAPE `{warm_expert.get("MdAPE", np.nan):.4f}`, MAPE `{warm_expert.get("MAPE", np.nan):.4f}`, p95_APE `{warm_expert.get("p95_APE", np.nan):.4f}`로 기준선보다 좋아지지 않았다.
- Cold 재학습 기준선은 평균 MdAPE `{cold_base.get("MdAPE", np.nan):.4f}`, MAPE `{cold_base.get("MAPE", np.nan):.4f}`, p95_APE `{cold_base.get("p95_APE", np.nan):.4f}`였다.
- Cold 원인별 보정 적용 후 평균 MdAPE `{cold_expert.get("MdAPE", np.nan):.4f}`, MAPE `{cold_expert.get("MAPE", np.nan):.4f}`, p95_APE `{cold_expert.get("p95_APE", np.nan):.4f}`로 p95는 소폭 좋아졌지만 MdAPE/MAPE가 나빠졌다.
- 따라서 이번 원인별 보정/라우팅 후보는 v0.1 기본 정책으로 바로 채택하지 않는다.
- 기존 v0.1 Warm 1순위인 `PP-SVC3 70:30 결합`은 bootstrap 검증에서 개선 신호가 강하지만, 이번 스크립트의 재학습 검증 대상은 아니다.
- 기존 v0.1 Cold 기준인 `PP-Y18 LightGBM Quantile + qwidth 보정`은 `PP-Y21`에서 예측값 재사용 기준 반복 holdout 검증을 통과했지만, 모델 재학습 포함 검증은 별도 보강 대상이다.
- 이번 결과는 “추가 보정 정책을 붙이면 무조건 좋아진다”가 아니라, 모델을 다시 학습하면 보정 효과가 줄거나 방향이 바뀔 수 있음을 보여준다.
"""
    (REPORT_DIR / "artist_level_model_retrain_revalidation_report.md").write_text(md, encoding="utf-8")
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Artist-Level 모델 재학습 포함 재검증</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 28px}}th,td{{border:1px solid #d7dee8;padding:7px 8px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}pre{{background:#f6f8fa;padding:12px;overflow:auto}}</style></head>
<body><h1>Artist-Level 모델 재학습 포함 재검증 결과</h1>
<h2>정책별 반복 지표</h2>{summary_df.to_html(index=False, escape=True)}
<h2>기준선 대비 변화량</h2>{delta_summary.to_html(index=False, escape=True)}
<h2>seed별 변화량</h2>{comparison_df.to_html(index=False, escape=True)}
<h2>split 크기</h2>{split_sizes.to_html(index=False, escape=True)}
<h2>실행 결론</h2>
<ul>
<li>Warm 재학습 기준선은 평균 MdAPE {warm_base.get("MdAPE", np.nan):.4f}, MAPE {warm_base.get("MAPE", np.nan):.4f}, p95_APE {warm_base.get("p95_APE", np.nan):.4f}였다.</li>
<li>Warm 원인별 보정 적용 후 평균 MdAPE {warm_expert.get("MdAPE", np.nan):.4f}, MAPE {warm_expert.get("MAPE", np.nan):.4f}, p95_APE {warm_expert.get("p95_APE", np.nan):.4f}로 기준선보다 좋아지지 않았다.</li>
<li>Cold 재학습 기준선은 평균 MdAPE {cold_base.get("MdAPE", np.nan):.4f}, MAPE {cold_base.get("MAPE", np.nan):.4f}, p95_APE {cold_base.get("p95_APE", np.nan):.4f}였다.</li>
<li>Cold 원인별 보정 적용 후 평균 MdAPE {cold_expert.get("MdAPE", np.nan):.4f}, MAPE {cold_expert.get("MAPE", np.nan):.4f}, p95_APE {cold_expert.get("p95_APE", np.nan):.4f}로 p95는 소폭 좋아졌지만 MdAPE/MAPE가 나빠졌다.</li>
<li>따라서 이번 원인별 보정/라우팅 후보는 v0.1 기본 정책으로 바로 채택하지 않는다.</li>
<li>기존 v0.1 Warm 1순위인 PP-SVC3 70:30 결합은 bootstrap 검증에서 개선 신호가 강하지만, 이번 스크립트의 재학습 검증 대상은 아니다.</li>
<li>기존 v0.1 Cold 기준인 PP-Y18 LightGBM Quantile + qwidth 보정은 PP-Y21에서 예측값 재사용 기준 반복 holdout 검증을 통과했지만, 모델 재학습 포함 검증은 별도 보강 대상이다.</li>
<li>이번 결과는 “추가 보정 정책을 붙이면 무조건 좋아진다”가 아니라, 모델을 다시 학습하면 보정 효과가 줄거나 방향이 바뀔 수 있음을 보여준다.</li>
</ul>
</body></html>"""
    (REPORT_DIR / "artist_level_model_retrain_revalidation_report.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--start-seed", type=int, default=20260605)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    master = read_master()
    features = artifact_features()
    warm_features = features["warm"]
    cold_features = unique(
        features["cold_lightgbm"]
        + META_NUMERIC
        + META_CATEGORICAL
        + SEARCH_NUMERIC
        + SEARCH_CATEGORICAL
        + EXTERNAL_NUMERIC
        + EXTERNAL_CATEGORICAL
    )
    metrics_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    split_size_rows: list[dict[str, Any]] = []
    seeds = [args.start_seed + idx for idx in range(args.seeds)]
    for seed in seeds:
        rows, preds, sizes = run_seed(master, seed, warm_features, cold_features)
        metrics_rows.extend(rows)
        if not preds.empty:
            pred_frames.append(preds)
        split_size_rows.append({"seed": seed, **sizes})
        print(json.dumps({"seed": seed, "metrics_rows": len(rows), "sizes": sizes}, ensure_ascii=False))

    metrics_df = pd.DataFrame(metrics_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True, sort=False) if pred_frames else pd.DataFrame()
    split_sizes = pd.DataFrame(split_size_rows)
    summary_df = summarize(metrics_df)
    comparison_df = compare_baseline_expert(metrics_df)
    metrics_df.to_csv(OUTPUT_DIR / "artist_level_retrain_metrics.csv", index=False)
    predictions_df.to_csv(OUTPUT_DIR / "artist_level_retrain_predictions.csv", index=False)
    summary_df.to_csv(OUTPUT_DIR / "artist_level_retrain_summary.csv", index=False)
    comparison_df.to_csv(OUTPUT_DIR / "artist_level_retrain_comparison.csv", index=False)
    split_sizes.to_csv(OUTPUT_DIR / "artist_level_retrain_split_sizes.csv", index=False)
    config = {
        "seeds": seeds,
        "master_rows": int(len(master)),
        "warm_features": warm_features,
        "cold_feature_count": len(cold_features),
        "cold_feature_note": "LightGBM base + artist meta + search cache + exhibition/gallery cache",
        "split_policy": {
            "cold_calibration_artist_bucket": "0-699 / 10000",
            "cold_test_artist_bucket": "700-1399 / 10000",
            "warm_calibration_row_bucket": "0-999 / 10000 within remaining train artists with >=8 rows",
            "warm_test_row_bucket": "1000-1999 / 10000 within remaining train artists with >=8 rows",
        },
    }
    (OUTPUT_DIR / "artist_level_retrain_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, summary_df, comparison_df, split_sizes, config)
    print(
        json.dumps(
            {
                "status": "completed",
                "metrics": str((OUTPUT_DIR / "artist_level_retrain_metrics.csv").relative_to(PROJECT_ROOT)),
                "report": str((REPORT_DIR / "artist_level_model_retrain_revalidation_report.md").relative_to(PROJECT_ROOT)),
                "html": str((REPORT_DIR / "artist_level_model_retrain_revalidation_report.html").relative_to(PROJECT_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
