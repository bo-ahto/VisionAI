#!/usr/bin/env python3
"""PP-CDATA1 (2부): 피처셋별 Cold 학습곡선 — "어떤 데이터가 늘어야 좋아지나" 규명.

두 피처셋의 학습곡선(학습 작가 25/50/75/100%, 고정 cold test)을 비교:
  - A_artwork : 작품 물리 피처 12개만 (v0.2 운영, 검색 없음)
  - B_artwork_meta : A + 작가 메타/전시/갤러리(비검색 46피처)

질문:
  1) B가 A보다 *수준*이 낮나(100%에서)? → 작가 정보가 cold 예측에 도움이 되나
  2) B가 데이터 증가에 따라 *스케일*하나? → 작가 메타를 더 수집하면 cold가 좋아지나
검색 피처는 두 셋 모두 제외(ROI 0 + frozen).
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[4]
STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
SCHEMA = (
    REPO
    / "models"
    / "track6"
    / "cold_v03_research_upstream_refreeze_candidate"
    / "artifacts"
    / "feature_schema.json"
)
OUT = Path(__file__).resolve().parents[1] / "artifacts"

ARTWORK = [
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
    "size_bucket",
    "support_size_bucket",
]
LGB = dict(
    objective="quantile",
    alpha=0.5,
    n_estimators=430,
    num_leaves=31,
    learning_rate=0.035,
    min_child_samples=35,
    subsample=0.9,
    subsample_freq=1,
    colsample_bytree=0.9,
    reg_alpha=0.0,
    reg_lambda=1.2,
    max_depth=-1,
    n_jobs=-1,
    verbose=-1,
)
FRACTIONS = [0.25, 0.50, 0.75, 1.00]
SEEDS = [20260617, 20260618, 20260619]


def prep(df, feats):
    x = df[feats].copy()
    cats = []
    for c in feats:
        if x[c].dtype == object or str(x[c].dtype) == "string":
            x[c] = x[c].astype("category")
            cats.append(c)
        else:
            x[c] = pd.to_numeric(x[c], errors="coerce")
    return x, cats


def metrics(actual_log, pred_log):
    actual = np.exp(np.asarray(actual_log, float))
    pred = np.clip(np.exp(np.asarray(pred_log, float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
    }


def curve(train, test, feats, label):
    test_x, _ = prep(test, feats)
    test_y = test["ln_price"].to_numpy(float)
    arts = train["artist_key"].dropna().unique()
    rows = []
    for seed in SEEDS:
        order = np.random.default_rng(seed).permutation(arts)
        for frac in FRACTIONS:
            k = max(1, int(round(len(order) * frac)))
            sub = train[train["artist_key"].isin(set(order[:k]))]
            x, cats = prep(sub, feats)
            model = LGBMRegressor(**{**LGB, "random_state": seed})
            model.fit(x, sub["ln_price"].to_numpy(float), categorical_feature=cats)
            rows.append(
                {
                    "feature_set": label,
                    "seed": seed,
                    "train_fraction": frac,
                    "train_artists": int(k),
                    **metrics(test_y, model.predict(test_x)),
                }
            )
    return rows


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln_price"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()

    feats_all = json.loads(SCHEMA.read_text())["pp_y2_feature_columns"]
    artist_feats = [
        f
        for f in feats_all
        if ("artist_meta" in f or "artist_exhibition" in f or "gallery" in f) and "search" not in f
    ]
    artist_feats = [f for f in artist_feats if f in df.columns]
    sets = {"A_artwork": ARTWORK, "B_artwork_meta": ARTWORK + artist_feats}

    rows = []
    for label, feats in sets.items():
        print(f"--- {label} ({len(feats)} feat) ---")
        rows += curve(train, test, feats, label)

    detail = pd.DataFrame(rows)
    summary = (
        detail.groupby(["feature_set", "train_fraction"])
        .agg(
            train_artists=("train_artists", "mean"),
            MdAPE=("MdAPE", "mean"),
            MAPE=("MAPE", "mean"),
            p95_APE=("p95_APE", "mean"),
        )
        .reset_index()
    )
    OUT.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUT / "featureset_curve_detail.csv", index=False)
    summary.to_csv(OUT / "featureset_curve_summary.csv", index=False)
    print("\n=== SUMMARY (seed 평균) ===")
    print(summary.to_string(index=False))
    for label in sets:
        s = summary[summary["feature_set"] == label].sort_values("train_fraction")
        d = s.iloc[-1][["MdAPE", "MAPE", "p95_APE"]] - s.iloc[0][["MdAPE", "MAPE", "p95_APE"]]
        print(f"{label} 25%→100%: " + ", ".join(f"{k} {float(v):+.4f}" for k, v in d.items()))


if __name__ == "__main__":
    main()
