#!/usr/bin/env python3
"""PP-CDATA1: Cold 학습곡선 — "어떤 데이터가 늘어야 Cold가 좋아지나" 근거 실험.

Cold는 "처음 보는 작가" 예측이다. 같은 cold 작가에 가격 데이터를 더 주면 그 작가는
Warm이 되어버리므로, Cold 개선의 질문은 *학습에 등장하는 작가(breadth)를 늘리면
처음 보는 cold 작가 일반화가 좋아지는가, 포화하는가*이다.

설계 (Warm CF12의 Cold판):
- cold test(3,099행/200작가)는 고정. train과 작가 완전 분리(누수 0 확인됨).
- train 작가를 25/50/75/100%로 늘리며(seed 3) LightGBM Quantile(v0.2 운영 동일 파라미터,
  검색 없는 12 피처)을 재학습.
- 각 비율에서 고정 cold test의 q50 대표 예측 MdAPE/MAPE/p95 측정.
- 학습 작가수/행수도 함께 기록.

검색 피처는 제외(ROI 0 확인됨 + 재학습 불가한 frozen snapshot). 순수 "데이터 양↔일반화" 곡선.
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
OUT = Path(__file__).resolve().parents[1] / "artifacts"

FEATURES = [
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
CATS = ["medium_category", "support_category", "size_bucket", "support_size_bucket"]
LGB_PARAMS = dict(
    objective="quantile",
    alpha=0.5,
    n_estimators=430,
    num_leaves=31,
    learning_rate=0.035,
    min_child_samples=35,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_alpha=0.0,
    reg_lambda=1.2,
    max_depth=-1,
    subsample_freq=1,
    n_jobs=-1,
    verbose=-1,
)
FRACTIONS = [0.25, 0.50, 0.75, 1.00]
SEEDS = [20260617, 20260618, 20260619]


def prep(df):
    x = df[FEATURES].copy()
    for c in CATS:
        x[c] = x[c].astype("category")
    for c in [f for f in FEATURES if f not in CATS]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x


def metrics(actual_log, pred_log):
    actual = np.exp(np.asarray(actual_log, dtype=float))
    pred = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(
            np.sqrt(np.mean((np.log(actual) - np.asarray(pred_log, dtype=float)) ** 2))
        ),
    }


def main():
    df = pd.read_csv(STORE, low_memory=False)
    df["ln_price"] = np.log(pd.to_numeric(df["price_krw"], errors="coerce"))
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()
    test_x, test_y = prep(test), test["ln_price"].to_numpy(float)
    train_artists = train["artist_key"].dropna().unique()

    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        order = rng.permutation(train_artists)
        for frac in FRACTIONS:
            k = max(1, int(round(len(order) * frac)))
            picked = set(order[:k])
            sub = train[train["artist_key"].isin(picked)]
            model = LGBMRegressor(**{**LGB_PARAMS, "random_state": seed})
            model.fit(prep(sub), sub["ln_price"].to_numpy(float), categorical_feature=CATS)
            m = metrics(test_y, model.predict(test_x))
            rows.append(
                {
                    "seed": seed,
                    "train_fraction": frac,
                    "train_rows": len(sub),
                    "train_artists": len(picked),
                    "median_history_n": float(sub["artist_key"].value_counts().median()),
                    **m,
                }
            )
            print(json.dumps(rows[-1], ensure_ascii=False))

    detail = pd.DataFrame(rows)
    summary = (
        detail.groupby("train_fraction")
        .agg(
            train_rows=("train_rows", "mean"),
            train_artists=("train_artists", "mean"),
            MdAPE=("MdAPE", "mean"),
            MAPE=("MAPE", "mean"),
            p95_APE=("p95_APE", "mean"),
            RMSE_log=("RMSE_log", "mean"),
        )
        .reset_index()
    )

    OUT.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUT / "learning_curve_detail.csv", index=False)
    summary.to_csv(OUT / "learning_curve_summary.csv", index=False)
    print("\n=== SUMMARY (seed 평균) ===")
    print(summary.to_string(index=False))
    delta = (
        summary.iloc[-1][["MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
        - summary.iloc[0][["MdAPE", "MAPE", "p95_APE", "RMSE_log"]]
    )
    print("\n25%→100% 변화:", {k: round(float(v), 4) for k, v in delta.items()})


if __name__ == "__main__":
    main()
