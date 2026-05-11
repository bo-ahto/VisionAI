"""Track 3 PR2 — Rare artist blend 비율 grid search.

목적: 운영 라우팅 3-way 중 "1-2건 작가 (rare)" 케이스의 blend 비율 결정.
     Warm features + strong smoothing vs Cold 비중 그리드.

설계:
- Dev pool에서 작가 작품수 1-2건인 작가들만 추출
- Cold LAD 예측 vs Warm LightGBM 예측을 가중평균
- 비율 grid: [0/100, 25/75, 50/50, 75/25, 100/0] (Cold/Warm)
- 1건 vs 2건 별도 평가

평가:
- median APE
- W30
- 작가별 별도 (1건 / 2건)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_pr2_blend_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_LIN = ["medium_category", "support_category", "orientation"]
CAT_COLS_TREE = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42

BLEND_GRID = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
            "n": int(len(y_true))}


def build_lad_pipeline(features):
    cat = [c for c in features if c in CAT_COLS_LIN]
    num = [c for c in features if c not in CAT_COLS_LIN]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat, seed):
    params = {"objective": "regression", "metric": "rmse",
              "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
              "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
              "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR2 — Rare artist blend 비율 grid search")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    # Use seed 42 warm split
    split = warm_meta["splits"][0]
    train_idx = split["train_indices"]
    val_idx = split["val_indices"]
    test_idx = split["test_indices"]
    tr_df = dev_df.iloc[train_idx]
    va_df = dev_df.iloc[val_idx]
    te_df = dev_df.iloc[test_idx].copy()

    # 1. Train Cold LAD on train_df
    logger.info("\n--- Cold LAD 학습 ---")
    cold_model = build_lad_pipeline(COLD_FEATURES)
    cold_model.fit(tr_df[COLD_FEATURES], tr_df[TARGET].values)
    pred_cold = cold_model.predict(te_df[COLD_FEATURES])

    # 2. Train Warm LightGBM (tuned PR1 params)
    logger.info("--- Warm LightGBM 학습 ---")
    X_tr_w = to_cat(tr_df, WARM_FEATURES, CAT_COLS_TREE)
    X_va_w = to_cat(va_df, WARM_FEATURES, CAT_COLS_TREE)
    X_te_w = to_cat(te_df, WARM_FEATURES, CAT_COLS_TREE)
    warm_model = train_lgb(X_tr_w, tr_df[TARGET].values,
                           X_va_w, va_df[TARGET].values, CAT_COLS_TREE, SEED)
    pred_warm = warm_model.predict(X_te_w)

    # 3. Rare artist mask 계산 (train fold 기준)
    artist_counts = tr_df[ARTIST_COL].value_counts().to_dict()
    te_df["train_count"] = te_df[ARTIST_COL].map(artist_counts).fillna(0).astype(int)
    te_df["pred_cold"] = pred_cold
    te_df["pred_warm"] = pred_warm

    # Group categories
    categories = {
        "all": te_df,
        "warm (≥3건)": te_df[te_df["train_count"] >= 3],
        "rare 1건": te_df[te_df["train_count"] == 1],
        "rare 2건": te_df[te_df["train_count"] == 2],
        "rare 1-2건 합": te_df[te_df["train_count"].isin([1, 2])],
        "unseen (0건)": te_df[te_df["train_count"] == 0],
    }
    logger.info("\n그룹별 분포:")
    for name, sub in categories.items():
        if len(sub) > 0:
            logger.info(f"  {name}: n={len(sub):,} / {sub[ARTIST_COL].nunique():,} 작가")

    # 4. Grid search on each category
    results = {}
    for cat_name, sub in categories.items():
        if len(sub) < 20:
            continue
        y_true = sub[TARGET].values
        grid_results = []
        for w_cold in BLEND_GRID:
            w_warm = 1 - w_cold
            pred_blend = w_cold * sub["pred_cold"].values + w_warm * sub["pred_warm"].values
            m = compute_metrics(y_true, pred_blend)
            m["w_cold"] = w_cold
            m["w_warm"] = w_warm
            grid_results.append(m)
        # Best blend
        best = min(grid_results, key=lambda x: x["median_ape"])
        results[cat_name] = {
            "n": int(len(sub)),
            "grid": grid_results,
            "best_w_cold": best["w_cold"],
            "best_med_ape": best["median_ape"],
        }

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 PR2 — Rare artist blend 비율 grid search")
    print("=" * 80)
    print()
    print(f"{'Category':<20} {'n':>7} {'Best w_cold':>12} {'Best med_APE':>14}")
    print("-" * 80)
    for cat_name, res in results.items():
        print(f"{cat_name:<20} {res['n']:>7,} {res['best_w_cold']:>12.2f} {res['best_med_ape']:>14.3f}")

    print()
    print("그룹별 grid 상세 (med_APE):")
    print("-" * 80)
    header = "Category"
    for w in BLEND_GRID:
        header += f"  w_cold={w:.1f}"
    print(header)
    for cat_name, res in results.items():
        row = f"{cat_name:<20}"
        for g in res["grid"]:
            mark = "★" if g["w_cold"] == res["best_w_cold"] else " "
            row += f"  {g['median_ape']:.3f}{mark}"
        print(row)

    # 운영 권장
    print()
    print("📝 운영 라우팅 권장:")
    if "rare 1건" in results:
        b = results["rare 1건"]["best_w_cold"]
        print(f"  1건 작가: w_cold={b:.2f} → cold {b:.0%} + warm {1-b:.0%}")
    if "rare 2건" in results:
        b = results["rare 2건"]["best_w_cold"]
        print(f"  2건 작가: w_cold={b:.2f} → cold {b:.0%} + warm {1-b:.0%}")
    if "warm (≥3건)" in results:
        b = results["warm (≥3건)"]["best_w_cold"]
        print(f"  ≥3건 작가: w_cold={b:.2f} (참고)")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
