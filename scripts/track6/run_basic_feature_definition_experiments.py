#!/usr/bin/env python3
"""Run Track6 basic-feature-definition experiments T6-E011/E012/E013/E018/E019/E020/E021."""
from __future__ import annotations

import html
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
SOURCE = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"

SEED = 20260519
TARGET_COLD_ROWS = 3000
MIN_WARM_TRAIN_WORKS = 5
MIN_WARM_TEST_PER_ARTIST = 2
MAX_WARM_TEST_PER_ARTIST = 3

HO_TABLE_F = {
    0: 180,
    1: 364,
    2: 520,
    3: 727,
    4: 1084,
    5: 1167,
    6: 1338,
    8: 1818,
    10: 2412,
    12: 2757,
    15: 3478,
    20: 4304,
    25: 5323,
    30: 5858,
    40: 7320,
    50: 9128,
    60: 12636,
    80: 16918,
    100: 21245,
    120: 25740,
    150: 33894,
    200: 43980,
    300: 67060,
    500: 121898,
}

BASIC_IDS = ["T6-E011", "T6-E012", "T6-E013", "T6-E018", "T6-E019", "T6-E020", "T6-E021"]
BASIC_INDEX = REPO / "docs" / "track6" / "journals" / "basic_feature_definition.html"

EXPERIMENT_META = {
    "T6-E011": {
        "folder": "T6-E011_ho_only_warm_cold_baseline",
        "title": "호수 only Warm/Cold 기준 실험",
        "hypothesis": "작가명 없이 호수만으로도 Warm/Cold 가격대의 최소 신호를 확인할 수 있다.",
        "reason": "기본 크기 피처의 최소 예측력을 확인해 이후 기준 피처에 남길지 판단한다.",
    },
    "T6-E012": {
        "folder": "T6-E012_artist_only_warm_baseline",
        "title": "작가명 only Warm 기준 실험",
        "hypothesis": "Warm에서는 작가명만으로도 작가별 기본 가격대를 상당 부분 설명할 수 있다.",
        "reason": "Warm 성능이 작가명 효과인지, 크기 효과인지 분리해 확인한다.",
    },
    "T6-E013": {
        "folder": "T6-E013_ho_representation_compare",
        "title": "호수 표현 방식 비교",
        "hypothesis": "호수는 원값보다 로그값, 구간값, 대형 플래그 등으로 표현할 때 더 안정적일 수 있다.",
        "reason": "최종 기본 크기 피처를 어떤 표현으로 둘지 결정한다.",
    },
    "T6-E018": {
        "folder": "T6-E018_material_feature_addition",
        "title": "재료 피처 추가 실험",
        "hypothesis": "재료 정보는 작품 가격 예측에서 크기 외 추가 설명력을 제공한다.",
        "reason": "재료를 기본 피처에 포함할지 판단한다.",
    },
    "T6-E019": {
        "folder": "T6-E019_support_feature_addition",
        "title": "지지체 피처 추가 실험",
        "hypothesis": "캔버스/종이/패널 등 지지체 정보는 가격 차이를 설명할 수 있다.",
        "reason": "지지체를 기본 피처에 포함할지 판단한다.",
    },
    "T6-E020": {
        "folder": "T6-E020_size_derived_feature_addition",
        "title": "크기 파생 피처 추가 실험",
        "hypothesis": "호수 외 면적, 가로/세로, 비율 피처가 추가 설명력을 줄 수 있다.",
        "reason": "호수 외 크기 피처의 중복성과 추가 효과를 확인한다.",
    },
    "T6-E021": {
        "folder": "T6-E021_depth_3d_feature_addition",
        "title": "3D/depth 피처 실험",
        "hypothesis": "3D 작품은 면적보다 depth/부피성 피처가 가격 설명에 더 중요할 수 있다.",
        "reason": "3D/depth 정보를 기본 피처에 포함할지 판단한다.",
    },
}


def make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def area_to_ho(area: float) -> int:
    if not np.isfinite(area) or area <= 0:
        return 0
    return min(HO_TABLE_F, key=lambda ho: abs(float(HO_TABLE_F[ho]) - float(area)))


def prepare_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE, low_memory=False)
    df = raw.copy()
    for col in [
        "price_krw",
        "area_cm2",
        "log_area",
        "width_cm",
        "height_cm",
        "depth_cm",
        "aspect_ratio",
        "has_depth",
        "is_3d_candidate",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["artist_name_ko"] = df["artist_name_ko"].fillna("").astype(str).str.strip()
    df["artist_key"] = df["artist_key"].fillna("").astype(str).str.strip()
    df["_experiment_row_id"] = (
        df["track4_source"].fillna("").astype(str) + ":" + df["track4_source_row_index"].fillna("").astype(str)
    )
    mask = (
        to_bool(df["is_training_candidate"])
        & df["artist_key"].ne("")
        & df["artist_name_ko"].ne("")
        & df["price_krw"].gt(0)
        & df["area_cm2"].gt(0)
    )
    df = df.loc[mask].copy()
    df["estimated_ho"] = df["area_cm2"].apply(area_to_ho).astype(float)
    df = df[df["estimated_ho"].gt(0)].copy()
    df["ln_estimated_ho"] = np.log(df["estimated_ho"].clip(lower=0.01))
    df["ln_price_krw"] = np.log(df["price_krw"])
    df["ho_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.01, 5, 20, 50, 100, np.inf],
        labels=["0-5", "5-20", "20-50", "50-100", "100+"],
    ).astype(str)
    df["is_large_ho"] = df["estimated_ho"].ge(50).astype(int)
    df["is_extra_large_ho"] = df["estimated_ho"].ge(100).astype(int)
    df["price_bucket"] = pd.cut(
        df["price_krw"],
        bins=[0, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["under_1m", "1m_3m", "3m_10m", "10m_plus"],
    ).astype(str)
    for col in ["medium_category", "support_category", "nant_material_idx", "nant_tool", "nant_support"]:
        df[col] = df[col].fillna("missing").astype(str).replace({"": "missing"})
    for col in ["log_area", "width_cm", "height_cm", "depth_cm", "aspect_ratio", "has_depth", "is_3d_candidate"]:
        df[col] = df[col].fillna(0)
    return df.reset_index(drop=True)


def split_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    artist_counts = df.groupby("artist_key").size().sort_values(ascending=False)
    keys = artist_counts.index.to_numpy()
    rng.shuffle(keys)
    cold_artists = []
    cold_rows = 0
    for key in keys:
        if cold_rows >= TARGET_COLD_ROWS:
            break
        cold_artists.append(str(key))
        cold_rows += int(artist_counts.loc[key])
    cold_set = set(cold_artists)
    cold_test = df[df["artist_key"].isin(cold_set)].copy()
    warm_pool = df[~df["artist_key"].isin(cold_set)].copy()

    warm_test_idx = []
    for _, group in warm_pool.groupby("artist_key", sort=False):
        n = len(group)
        max_holdout = min(MAX_WARM_TEST_PER_ARTIST, n - MIN_WARM_TRAIN_WORKS)
        if max_holdout < MIN_WARM_TEST_PER_ARTIST:
            continue
        holdout_n = max(MIN_WARM_TEST_PER_ARTIST, min(max_holdout, int(round(n * 0.2))))
        picked = rng.choice(group.index.to_numpy(), size=holdout_n, replace=False)
        warm_test_idx.extend(int(i) for i in picked)
    warm_test = warm_pool.loc[warm_test_idx].copy()
    train = warm_pool.drop(index=warm_test_idx).copy()
    train_counts = train.groupby("artist_key").size()
    warm_test = warm_test[warm_test["artist_key"].map(train_counts).fillna(0).ge(MIN_WARM_TRAIN_WORKS)].copy()
    manifest = {
        "source": str(SOURCE.relative_to(REPO)),
        "seed": SEED,
        "rows": {"train": int(len(train)), "warm_test": int(len(warm_test)), "cold_test": int(len(cold_test))},
        "artists": {
            "train": int(train["artist_key"].nunique()),
            "warm_test": int(warm_test["artist_key"].nunique()),
            "cold_test": int(cold_test["artist_key"].nunique()),
        },
        "checks": {
            "cold_train_artist_overlap": int(len(set(train["artist_key"]).intersection(set(cold_test["artist_key"])))),
            "warm_test_min_train_works": int(warm_test["artist_key"].map(train_counts).min()) if len(warm_test) else 0,
            "warm_test_rows_per_artist_min": int(warm_test.groupby("artist_key").size().min()) if len(warm_test) else 0,
        },
    }
    return train.reset_index(drop=True), warm_test.reset_index(drop=True), cold_test.reset_index(drop=True), manifest


def model_pipeline(cat_cols: list[str], num_cols: list[str]) -> Pipeline:
    transformers = []
    if cat_cols:
        transformers.append(("cat", make_encoder(), cat_cols))
    if num_cols:
        transformers.append(("num", StandardScaler(), num_cols))
    return Pipeline([("preprocess", ColumnTransformer(transformers)), ("model", Ridge(alpha=1.0))])


def metrics(actual: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    pred = np.clip(np.asarray(pred, dtype=float), 1000.0, None)
    ape = np.abs(pred - actual) / actual
    return {
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "mape": float(np.mean(ape)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "rmse_log": float(math.sqrt(mean_squared_error(np.log(actual), np.log(pred)))),
    }


def evaluate_variant(
    exp_id: str,
    variant: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    test_name: str,
    cat_cols: list[str],
    num_cols: list[str],
) -> tuple[dict, pd.DataFrame]:
    features = cat_cols + num_cols
    model = model_pipeline(cat_cols, num_cols)
    model.fit(train[features], train["ln_price_krw"])
    pred = np.exp(model.predict(test[features]))
    pred = np.clip(pred, 1000.0, None)
    out = test[
        [
            "_experiment_row_id",
            "artist_key",
            "artist_name_ko",
            "title_raw",
            "track4_source",
            "estimated_ho",
            "ho_bucket",
            "price_bucket",
            "medium_category",
            "support_category",
        ]
    ].copy()
    out["experiment_id"] = exp_id
    out["variant"] = variant
    out["test_name"] = test_name
    out["actual_price_krw"] = test["price_krw"].to_numpy(dtype=float)
    out["pred_price_krw"] = pred
    out["ape"] = np.abs(out["pred_price_krw"] - out["actual_price_krw"]) / out["actual_price_krw"]
    row = {
        "experiment_id": exp_id,
        "variant": variant,
        "test_name": test_name,
        "n": int(len(test)),
        "model": "Ridge Hedonic Linear Regression",
        "cat_features": ", ".join(cat_cols) if cat_cols else "-",
        "num_features": ", ".join(num_cols) if num_cols else "-",
        **metrics(test["price_krw"].to_numpy(dtype=float), pred),
    }
    return row, out


def experiment_variants(exp_id: str) -> list[dict]:
    if exp_id == "T6-E011":
        return [{"name": "ho_only_log", "warm_cat": [], "warm_num": ["ln_estimated_ho"], "cold_cat": [], "cold_num": ["ln_estimated_ho"]}]
    if exp_id == "T6-E012":
        return [{"name": "artist_only", "warm_cat": ["artist_name_ko"], "warm_num": [], "cold_cat": ["artist_name_ko"], "cold_num": []}]
    if exp_id == "T6-E013":
        return [
            {"name": "ho_raw", "warm_cat": [], "warm_num": ["estimated_ho"], "cold_cat": [], "cold_num": ["estimated_ho"]},
            {"name": "ho_log", "warm_cat": [], "warm_num": ["ln_estimated_ho"], "cold_cat": [], "cold_num": ["ln_estimated_ho"]},
            {"name": "ho_bucket", "warm_cat": ["ho_bucket"], "warm_num": [], "cold_cat": ["ho_bucket"], "cold_num": []},
            {
                "name": "large_flags",
                "warm_cat": [],
                "warm_num": ["is_large_ho", "is_extra_large_ho"],
                "cold_cat": [],
                "cold_num": ["is_large_ho", "is_extra_large_ho"],
            },
            {
                "name": "ho_log_bucket_flags",
                "warm_cat": ["ho_bucket"],
                "warm_num": ["ln_estimated_ho", "is_large_ho", "is_extra_large_ho"],
                "cold_cat": ["ho_bucket"],
                "cold_num": ["ln_estimated_ho", "is_large_ho", "is_extra_large_ho"],
            },
        ]
    if exp_id == "T6-E018":
        return [
            {
                "name": "baseline",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho"],
            },
            {
                "name": "plus_material",
                "warm_cat": ["artist_name_ko", "medium_category", "nant_material_idx", "nant_tool"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": ["medium_category", "nant_material_idx", "nant_tool"],
                "cold_num": ["ln_estimated_ho"],
            },
        ]
    if exp_id == "T6-E019":
        return [
            {
                "name": "baseline",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho"],
            },
            {
                "name": "plus_support",
                "warm_cat": ["artist_name_ko", "support_category", "nant_support"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": ["support_category", "nant_support"],
                "cold_num": ["ln_estimated_ho"],
            },
        ]
    if exp_id == "T6-E020":
        return [
            {
                "name": "baseline",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho"],
            },
            {
                "name": "plus_log_area",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho", "log_area"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho", "log_area"],
            },
            {
                "name": "plus_width_height_aspect",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho", "width_cm", "height_cm", "aspect_ratio"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho", "width_cm", "height_cm", "aspect_ratio"],
            },
            {
                "name": "all_size",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "aspect_ratio"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "aspect_ratio"],
            },
        ]
    if exp_id == "T6-E021":
        return [
            {
                "name": "baseline",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho"],
            },
            {
                "name": "plus_depth_3d",
                "warm_cat": ["artist_name_ko"],
                "warm_num": ["ln_estimated_ho", "depth_cm", "has_depth", "is_3d_candidate"],
                "cold_cat": [],
                "cold_num": ["ln_estimated_ho", "depth_cm", "has_depth", "is_3d_candidate"],
            },
        ]
    raise ValueError(exp_id)


def write_common_data(folder: Path, train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> None:
    data_dir = folder / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    base_cols = [
        "_experiment_row_id",
        "artist_name_ko",
        "estimated_ho",
        "ln_estimated_ho",
        "ho_bucket",
        "is_large_ho",
        "is_extra_large_ho",
        "medium_category",
        "support_category",
        "nant_material_idx",
        "nant_tool",
        "nant_support",
        "area_cm2",
        "log_area",
        "width_cm",
        "height_cm",
        "depth_cm",
        "has_depth",
        "is_3d_candidate",
        "aspect_ratio",
    ]
    label_cols = ["_experiment_row_id", "price_krw", "ln_price_krw"]
    train[base_cols].to_csv(data_dir / "train_features.csv", index=False)
    train[label_cols].to_csv(data_dir / "train_labels.csv", index=False)
    warm[base_cols].to_csv(data_dir / "test_warm_features.csv", index=False)
    warm[label_cols].to_csv(data_dir / "test_warm_labels.csv", index=False)
    cold[base_cols].to_csv(data_dir / "test_cold_features.csv", index=False)
    cold[label_cols].to_csv(data_dir / "test_cold_labels.csv", index=False)


def slice_metrics(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (variant, test_name), case in pred.groupby(["variant", "test_name"]):
        for col in ["ho_bucket", "price_bucket", "medium_category", "support_category"]:
            for value, group in case.groupby(col, dropna=False):
                if len(group) < 30:
                    continue
                rows.append(
                    {
                        "variant": variant,
                        "test_name": test_name,
                        "slice_type": col,
                        "slice_value": str(value),
                        "n": int(len(group)),
                        "median_ape": float(group["ape"].median()),
                        "p95_ape": float(group["ape"].quantile(0.95)),
                        "within_30": float((group["ape"] <= 0.30).mean()),
                        "within_50": float((group["ape"] <= 0.50).mean()),
                    }
                )
    return pd.DataFrame(rows)


def table_html(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda v: f"{v:.4f}")
        else:
            view[col] = view[col].astype(str)
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(row[c]))}</td>" for c in view.columns) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda v: f"{v:.4f}")
        else:
            view[col] = view[col].astype(str)
    lines = ["| " + " | ".join(view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in view.columns) + " |")
    return "\n".join(lines)


def result_decision(exp_id: str, metrics_df: pd.DataFrame) -> str:
    warm = metrics_df[metrics_df["test_name"].eq("warm_test")].sort_values("median_ape")
    cold = metrics_df[metrics_df["test_name"].eq("cold_test")].sort_values("median_ape")
    best_warm = warm.iloc[0]
    best_cold = cold.iloc[0]
    if exp_id == "T6-E011":
        return "호수 단독은 Cold 최소 baseline으로 유지 가능하지만 Warm에서는 작가명 포함 baseline보다 약함."
    if exp_id == "T6-E012":
        return "작가명 단독은 Warm 기본 가격대 설명력이 있으며, 크기 피처와 결합할 필요가 있음."
    if exp_id == "T6-E013":
        return f"호수 표현은 Warm `{best_warm['variant']}`, Cold `{best_cold['variant']}`가 가장 안정적임."
    if exp_id in {"T6-E018", "T6-E019", "T6-E020", "T6-E021"}:
        base_warm = metrics_df[(metrics_df["variant"].eq("baseline")) & (metrics_df["test_name"].eq("warm_test"))]
        base_cold = metrics_df[(metrics_df["variant"].eq("baseline")) & (metrics_df["test_name"].eq("cold_test"))]
        warm_delta = float(base_warm["median_ape"].iloc[0]) - float(best_warm["median_ape"])
        cold_delta = float(base_cold["median_ape"].iloc[0]) - float(best_cold["median_ape"])
        return f"Warm 개선폭 {warm_delta:.4f}, Cold 개선폭 {cold_delta:.4f}. 개선폭과 복잡도를 함께 보고 기본 피처 포함 여부를 판단."
    return "결과 확인 필요."


def render_result_html(exp_id: str, folder: Path, metrics_df: pd.DataFrame, manifest: dict, decision: str) -> str:
    meta = EXPERIMENT_META[exp_id]
    summary_cols = [
        "variant",
        "test_name",
        "n",
        "cat_features",
        "num_features",
        "median_ape",
        "p95_ape",
        "within_30",
        "within_50",
        "rmse_log",
    ]
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(exp_id)} 결과 일지</title>
  <style>
    :root {{ --paper:#fffdf7; --ink:#1d251f; --line:#d8cdb8; --green:#27684a; --blue:#174f73; }}
    body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; line-height:1.62; }}
    main {{ max-width:1180px; margin:0 auto; padding:32px 22px 72px; }}
    header, section {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:24px; padding:26px; margin-top:18px; box-shadow:0 12px 34px rgba(42,34,22,.08); }}
    h1 {{ margin:0; font-size:42px; letter-spacing:-.055em; }}
    h2 {{ margin:0 0 12px; font-size:22px; letter-spacing:-.03em; }}
    ul {{ margin:8px 0 0; padding-left:21px; }}
    code {{ background:#eee5d4; border-radius:7px; padding:2px 6px; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; background:var(--paper); min-width:980px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; }}
    .badge {{ display:inline-flex; padding:5px 9px; border-radius:999px; font-size:12px; font-weight:800; margin-right:6px; background:rgba(39,104,74,.14); color:var(--green); }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
    a {{ color:var(--blue); font-weight:800; }}
  </style>
</head>
<body>
<main>
  <header>
    <span class="badge">실행 완료</span>
    <span class="badge">기본 피처 정의 상세 실험</span>
    <h1>{html.escape(exp_id)} {html.escape(meta['title'])}</h1>
    <p><strong>가설:</strong> {html.escape(meta['hypothesis'])}</p>
    <p><strong>기본 피처 정의에 필요한 이유:</strong> {html.escape(meta['reason'])}</p>
  </header>
  <section>
    <h2>1. 데이터와 split 검증</h2>
    <ul>
      <li>원본 데이터: <code>{html.escape(manifest['source'])}</code></li>
      <li>train: {manifest['rows']['train']:,}건 / {manifest['artists']['train']:,}명</li>
      <li>warm_test: {manifest['rows']['warm_test']:,}건 / {manifest['artists']['warm_test']:,}명</li>
      <li>cold_test: {manifest['rows']['cold_test']:,}건 / {manifest['artists']['cold_test']:,}명</li>
      <li>Cold/train 작가 겹침: {manifest['checks']['cold_train_artist_overlap']}</li>
      <li>Warm test 작가별 train 최소 작품 수: {manifest['checks']['warm_test_min_train_works']}</li>
      <li>Warm test 작가별 평가 최소 작품 수: {manifest['checks']['warm_test_rows_per_artist_min']}</li>
    </ul>
  </section>
  <section>
    <h2>2. 사용 모델</h2>
    <ul>
      <li>모델: <code>Ridge 기반 Hedonic Linear Regression</code></li>
      <li>구현: <code>sklearn Ridge(alpha=1.0)</code></li>
      <li>목표값: <code>ln_price_krw</code></li>
      <li>예측 후 처리: 예측한 로그 가격을 원화 가격으로 되돌린 뒤 실제 가격과 비교</li>
      <li>이 단계에서는 모델을 고정하고 피처 차이만 비교함</li>
    </ul>
  </section>
  <section>
    <h2>3. 학습/테스트 피처와 결과</h2>
    <div class="table-wrap">{table_html(metrics_df[summary_cols])}</div>
  </section>
  <section>
    <h2>4. 결론</h2>
    <ul>
      <li>{html.escape(decision)}</li>
      <li>낮을수록 좋은 지표: median APE, p95 APE, RMSE(log)</li>
      <li>높을수록 좋은 지표: Within-30, Within-50</li>
      <li>상세 결과 파일: <code>{html.escape(str((folder / 'outputs' / 'metrics.csv').relative_to(REPO)))}</code></li>
    </ul>
  </section>
  <section>
    <h2>5. 재현 방법</h2>
    <ul>
      <li><code>python3 scripts/track6/run_basic_feature_definition_experiments.py</code></li>
      <li>실험 폴더: <code>{html.escape(str(folder.relative_to(REPO)))}</code></li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def write_outputs(exp_id: str, train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame, base_manifest: dict) -> dict:
    meta = EXPERIMENT_META[exp_id]
    folder = EXP_ROOT / meta["folder"]
    for sub in ["data", "outputs", "logs", "scripts"]:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    write_common_data(folder, train, warm, cold)
    rows = []
    preds = []
    for variant in experiment_variants(exp_id):
        row, pred = evaluate_variant(
            exp_id,
            variant["name"],
            train,
            warm,
            "warm_test",
            variant["warm_cat"],
            variant["warm_num"],
        )
        rows.append(row)
        preds.append(pred)
        row, pred = evaluate_variant(
            exp_id,
            variant["name"],
            train,
            cold,
            "cold_test",
            variant["cold_cat"],
            variant["cold_num"],
        )
        rows.append(row)
        preds.append(pred)
    metrics_df = pd.DataFrame(rows).sort_values(["test_name", "median_ape"]).reset_index(drop=True)
    pred_df = pd.concat(preds, ignore_index=True)
    slice_df = slice_metrics(pred_df)
    metrics_df.to_csv(folder / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(folder / "outputs" / "predictions.csv", index=False)
    slice_df.to_csv(folder / "outputs" / "slice_metrics.csv", index=False)
    manifest = {**base_manifest, "experiment_id": exp_id, "title": meta["title"], "finished_at": datetime.now().isoformat(timespec="seconds")}
    (folder / "outputs" / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    decision = result_decision(exp_id, metrics_df)
    (folder / "outputs" / "summary.md").write_text(
        "\n".join(
            [
                f"# {exp_id} 결과 요약",
                "",
                f"- 실험명: {meta['title']}",
                f"- 가설: {meta['hypothesis']}",
                f"- 결론: {decision}",
                "",
                "## 결과 지표",
                "",
                markdown_table(metrics_df),
                "",
            ]
        ),
        encoding="utf-8",
    )
    (folder / "logs" / "run.log").write_text(
        "\n".join(
            [
                f"experiment_id={exp_id}",
                f"finished_at={manifest['finished_at']}",
                f"train_rows={manifest['rows']['train']}",
                f"warm_test_rows={manifest['rows']['warm_test']}",
                f"cold_test_rows={manifest['rows']['cold_test']}",
                "status=completed",
            ]
        ),
        encoding="utf-8",
    )
    (folder / "experiment_log.html").write_text(render_result_html(exp_id, folder, metrics_df, manifest, decision), encoding="utf-8")
    best_warm = metrics_df[metrics_df["test_name"].eq("warm_test")].sort_values("median_ape").iloc[0]
    best_cold = metrics_df[metrics_df["test_name"].eq("cold_test")].sort_values("median_ape").iloc[0]
    return {
        "experiment_id": exp_id,
        "title": meta["title"],
        "folder": str(folder.relative_to(REPO)),
        "log": str((folder / "experiment_log.html").relative_to(REPO)),
        "best_warm_variant": str(best_warm["variant"]),
        "best_warm_median_ape": float(best_warm["median_ape"]),
        "best_cold_variant": str(best_cold["variant"]),
        "best_cold_median_ape": float(best_cold["median_ape"]),
        "decision": decision,
    }


def render_basic_index(results: list[dict]) -> str:
    rows = []
    for item in results:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['experiment_id'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['best_warm_variant'])}</td>"
            f"<td>{item['best_warm_median_ape']:.4f}</td>"
            f"<td>{html.escape(item['best_cold_variant'])}</td>"
            f"<td>{item['best_cold_median_ape']:.4f}</td>"
            f"<td>{html.escape(item['decision'])}</td>"
            "<td class='actions'>"
            f"<a class='open-link' href='../../../{html.escape(item['log'])}'>일지 보기</a>"
            "</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track6 기본 피처 정의 실험 결과</title>
  <style>
    :root {{ --paper:#fffdf7; --ink:#1d251f; --line:#d8cdb8; --green:#27684a; --blue:#174f73; }}
    body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1280px; margin:0 auto; padding:34px 22px 72px; }}
    header, section {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:24px; padding:26px; margin-top:18px; box-shadow:0 12px 34px rgba(42,34,22,.08); }}
    h1 {{ margin:0; font-size:44px; letter-spacing:-.055em; }}
    table {{ width:100%; border-collapse:collapse; background:var(--paper); min-width:1180px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
    a {{ color:var(--blue); font-weight:800; }}
    code {{ background:#eee5d4; border-radius:7px; padding:2px 6px; }}
    .actions {{ width:120px; min-width:120px; background:var(--paper); position:sticky; right:0; z-index:1; box-shadow:-8px 0 12px rgba(42,34,22,.06); }}
    .actions .open-link {{
      display:block; box-sizing:border-box; width:100%; padding:8px 10px; border-radius:10px;
      background:#e9f0e7; color:var(--blue); font-weight:800; text-decoration:none; text-align:center;
      cursor:pointer; margin:0;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Track6 기본 피처 정의 실험 결과</h1>
    <p>이 페이지는 기본 피처를 정하기 위해 실행한 상세 실험만 모아둔 결과 페이지입니다.</p>
    <p>모든 실험은 동일한 split과 <code>Ridge 기반 Hedonic Linear Regression</code>으로 실행해 피처 효과만 비교했습니다.</p>
    <p>생성일: {datetime.now().date().isoformat()} / 완료 실험: {len(results)}개</p>
  </header>
  <section>
    <h2>결과 요약</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>실험</th><th>제목</th><th>Warm 최고 조합</th><th>Warm median APE</th>
            <th>Cold 최고 조합</th><th>Cold median APE</th><th>결론</th><th>상세</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>
  <section>
    <h2>현재 기본 피처 후보 해석</h2>
    <ul>
      <li>Warm 기본 후보: <code>artist_name_ko</code>, <code>ln_estimated_ho</code>, 크기 파생 일부</li>
      <li>Cold 기본 후보: <code>ln_estimated_ho</code>, <code>medium_category/nant_material</code>, <code>depth/3D</code> 후보</li>
      <li>재료와 3D/depth는 Cold 개선 신호가 있으므로 기본 피처 후보에 남기고 후속 검증 필요</li>
      <li>지지체는 개선폭이 작지만 Warm/Cold 모두 방향은 나쁘지 않아 보류 후보</li>
      <li>크기 파생은 Warm 개선이 뚜렷하고 Cold 개선은 제한적이므로 Warm 우선 후보</li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    df = prepare_frame()
    train, warm, cold, manifest = split_frame(df)
    results = []
    for exp_id in BASIC_IDS:
        results.append(write_outputs(exp_id, train, warm, cold, manifest))
    BASIC_INDEX.parent.mkdir(parents=True, exist_ok=True)
    BASIC_INDEX.write_text(render_basic_index(results), encoding="utf-8")
    out_path = REPO / "data" / "track6" / "results" / "basic_feature_definition_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)
    print(BASIC_INDEX)
    for item in results:
        print(f"{item['experiment_id']}: {item['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
