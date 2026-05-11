"""Track 3 — Phase 2 Warm 비선형 모델.

Plan v2.1 §4.2 Warm 모델: Cold features + artist_name_ko (native categorical).

학습 모델:
  - LightGBM (artist categorical native)
  - XGBoost (enable_categorical)
  - CatBoost (cat_features)

Evaluation: random 80/10/10 × N=3 seeds (Phase 2 빠른 측정).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_phase2_warm_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
WARM_FEATURES = [
    "artist_name_ko",
    "medium_category", "support_category", "has_depth",
    "log_area", "estimated_ho", "orientation",
]
CATEGORICAL_COLS = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42
N_SEEDS = 3


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.50)),
    }


def to_categorical(df, features):
    df = df[features].copy()
    for col in features:
        if col in CATEGORICAL_COLS:
            df[col] = df[col].astype("category")
    return df


def train_lgb(X_train, y_train, X_val, y_val, cat_features, seed):
    train_set = lgb.Dataset(X_train, y_train, categorical_feature=cat_features)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_features, reference=train_set)
    params = {
        "objective": "regression", "metric": "rmse", "learning_rate": 0.05,
        "num_leaves": 127, "min_data_in_leaf": 20,
        "feature_fraction": 0.9, "bagging_fraction": 0.9, "bagging_freq": 5,
        "verbose": -1, "seed": seed,
    }
    return lgb.train(params, train_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def train_xgb(X_train, y_train, X_val, y_val, seed):
    model = xgb.XGBRegressor(
        objective="reg:squarederror", n_estimators=2000, learning_rate=0.05,
        max_depth=8, min_child_weight=5, subsample=0.9, colsample_bytree=0.9,
        reg_alpha=0.1, reg_lambda=1.0, tree_method="hist", enable_categorical=True,
        early_stopping_rounds=30, random_state=seed,
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def train_cb(X_train, y_train, X_val, y_val, cat_features, seed):
    model = CatBoostRegressor(
        iterations=2000, learning_rate=0.05, depth=8,
        l2_leaf_reg=3.0, random_seed=seed, verbose=False,
        cat_features=cat_features, early_stopping_rounds=30,
    )
    model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
    return model


def run_tree_warm(model_name, dev_df, warm_splits, n_seeds=N_SEEDS):
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]
        val_idx = split["val_indices"]
        test_idx = split["test_indices"]

        X_train = to_categorical(dev_df.iloc[train_idx], WARM_FEATURES)
        X_val = to_categorical(dev_df.iloc[val_idx], WARM_FEATURES)
        X_test = to_categorical(dev_df.iloc[test_idx], WARM_FEATURES)
        y_train = dev_df.iloc[train_idx][TARGET].values
        y_val = dev_df.iloc[val_idx][TARGET].values
        y_test = dev_df.iloc[test_idx][TARGET].values

        cat_feat = [c for c in WARM_FEATURES if c in CATEGORICAL_COLS]

        if model_name == "LightGBM":
            model = train_lgb(X_train, y_train, X_val, y_val, cat_feat, split["seed"])
            y_pred = model.predict(X_test)
        elif model_name == "XGBoost":
            model = train_xgb(X_train, y_train, X_val, y_val, split["seed"])
            y_pred = model.predict(X_test)
        elif model_name == "CatBoost":
            model = train_cb(X_train, y_train, X_val, y_val, cat_feat, split["seed"])
            y_pred = model.predict(X_test)

        m = compute_metrics(y_test, y_pred)
        m["seed"] = split["seed"]
        seed_results.append(m)

    agg = {
        "model": model_name,
        "n_seeds": len(seed_results),
        "per_seed": seed_results,
        "mean": {k: float(np.mean([s[k] for s in seed_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "std": {k: float(np.std([s[k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }
    return agg


def main():
    logger.info("=" * 70)
    logger.info(f"Track 3 Phase 2 — Warm 비선형 (random 80/10/10 × N={N_SEEDS})")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    results = {}
    for name in ["LightGBM", "XGBoost", "CatBoost"]:
        logger.info(f"\n--- {name} ---")
        try:
            res = run_tree_warm(name, dev_df, warm_meta["splits"])
            results[name] = res
            m, s = res["mean"], res["std"]
            logger.info(
                f"  med_APE={m['median_ape']:.3f}±{s['median_ape']:.3f} "
                f"MAPE={m['mape']:.3f}±{s['mape']:.3f} "
                f"RMSE_log={m['rmse_log']:.3f}±{s['rmse_log']:.3f} "
                f"W30={m['within_30pct']:.3f}"
            )
        except Exception as e:
            logger.error(f"  {name} 실패: {e}")
            results[name] = {"error": str(e)}

    print()
    print("=" * 90)
    print(f"📊 Phase 2 Warm 비선형 모델 결과 (random 80/10/10 × N={N_SEEDS} seeds)")
    print("=" * 90)
    print(f"{'Model':<14} {'med_APE':>15} {'MAPE':>15} {'RMSE_log':>15} {'W30':>15}")
    print("-" * 90)
    for name, res in results.items():
        if "error" in res:
            print(f"{name:<14} ERROR: {res['error']}")
            continue
        m, s = res["mean"], res["std"]
        print(f"{name:<14} {m['median_ape']:.3f}±{s['median_ape']:.3f}    "
              f"{m['mape']:.3f}±{s['mape']:.3f}    "
              f"{m['rmse_log']:.3f}±{s['rmse_log']:.3f}    "
              f"{m['within_30pct']:.3f}±{s['within_30pct']:.3f}")

    print()
    print("📝 Phase 1 vs Phase 2 Warm 비교:")
    print(f"  - Phase 1 Best (Quantile_q05 선형): med_APE 0.314 ± 0.000")
    valid = {k: v for k, v in results.items() if "error" not in v}
    if valid:
        best = min(valid, key=lambda k: valid[k]["mean"]["median_ape"])
        m = valid[best]["mean"]
        print(f"  - Phase 2 Best ({best}): med_APE {m['median_ape']:.3f} ± {valid[best]['std']['median_ape']:.3f}")
        delta = 0.314 - m["median_ape"]
        print(f"    → 비선형 향상: ↓{delta:.3f}")
    print()

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
