"""Track 3 — Phase 2 Cold 비선형 모델.

Plan v2.1 §4.2 Cold 모델: LightGBM / XGBoost / CatBoost (artist 미사용).

학습 모델:
  - LightGBM default
  - XGBoost default
  - CatBoost default
  (Phase 2 단계: default → Best model만 Phase 5에서 Optuna 적용)

Evaluation: GroupKFold(5) OOF + Source-stratified + Price-band stratified.
Phase 4.5 trigger 체크 (B4 median APE / >100M median APE).
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
OUT_PATH = REPO / "data" / "track3_phase2_cold_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
PRICE_COL = "price_krw_unified"
COLD_FEATURES = [
    "medium_category", "support_category", "has_depth",
    "log_area", "estimated_ho", "orientation",
]
CATEGORICAL_COLS = ["medium_category", "support_category", "orientation"]
SEED = 42

# Price-band 경계 (KRW, business-defined fixed bands — Plan v2.1)
PRICE_BANDS = {"B1": (0, 1_000_000), "B2": (1_000_000, 3_000_000),
               "B3": (3_000_000, 10_000_000), "B4": (10_000_000, float("inf"))}


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
        "n": int(len(y_true)),
    }


def price_band_breakdown(y_true_ln, y_pred_ln, prices):
    """Price-band별 median APE 분해."""
    result = {}
    for band, (lo, hi) in PRICE_BANDS.items():
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() == 0:
            continue
        result[band] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    # >100M trigger 체크용
    mask_100m = prices > 100_000_000
    if mask_100m.sum() > 0:
        result[">100M"] = compute_metrics(y_true_ln[mask_100m], y_pred_ln[mask_100m])
    return result


def source_breakdown(y_true_ln, y_pred_ln, sources):
    result = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() == 0:
            continue
        result[src] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    return result


def to_categorical(df, features):
    df = df[features].copy()
    for col in features:
        if col in CATEGORICAL_COLS:
            df[col] = df[col].astype("category")
    return df


def train_lgb(X_train, y_train, X_val, y_val, cat_features):
    train_set = lgb.Dataset(X_train, y_train, categorical_feature=cat_features)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_features, reference=train_set)
    params = {
        "objective": "regression", "metric": "rmse", "learning_rate": 0.05,
        "num_leaves": 63, "min_data_in_leaf": 20,
        "feature_fraction": 0.9, "bagging_fraction": 0.9, "bagging_freq": 5,
        "verbose": -1, "seed": SEED,
    }
    return lgb.train(params, train_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def train_xgb(X_train, y_train, X_val, y_val):
    model = xgb.XGBRegressor(
        objective="reg:squarederror", n_estimators=2000, learning_rate=0.05,
        max_depth=8, min_child_weight=5, subsample=0.9, colsample_bytree=0.9,
        reg_alpha=0.1, reg_lambda=1.0, tree_method="hist", enable_categorical=True,
        early_stopping_rounds=30, random_state=SEED,
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model


def train_cb(X_train, y_train, X_val, y_val, cat_features):
    model = CatBoostRegressor(
        iterations=2000, learning_rate=0.05, depth=8,
        l2_leaf_reg=3.0, random_seed=SEED, verbose=False,
        cat_features=cat_features, early_stopping_rounds=30,
    )
    model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
    return model


def run_tree_cold(model_name, dev_df, cold_folds):
    """단일 tree model 5-fold GroupKFold OOF."""
    fold_results = []
    oof_pred = np.full(len(dev_df), np.nan)

    for fold in cold_folds:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]
        # 추가 val split (10% of train)
        rng = np.random.default_rng(SEED + fold["fold"])
        perm = rng.permutation(len(train_idx))
        val_n = int(len(train_idx) * 0.1)
        val_idx = np.array(train_idx)[perm[:val_n]]
        tr_idx = np.array(train_idx)[perm[val_n:]]

        X_train = to_categorical(dev_df.iloc[tr_idx], COLD_FEATURES)
        X_val = to_categorical(dev_df.iloc[val_idx], COLD_FEATURES)
        X_test = to_categorical(dev_df.iloc[test_idx], COLD_FEATURES)
        y_train = dev_df.iloc[tr_idx][TARGET].values
        y_val = dev_df.iloc[val_idx][TARGET].values
        y_test = dev_df.iloc[test_idx][TARGET].values

        cat_feat = [c for c in COLD_FEATURES if c in CATEGORICAL_COLS]

        if model_name == "LightGBM":
            model = train_lgb(X_train, y_train, X_val, y_val, cat_feat)
            y_pred = model.predict(X_test)
        elif model_name == "XGBoost":
            model = train_xgb(X_train, y_train, X_val, y_val)
            y_pred = model.predict(X_test)
        elif model_name == "CatBoost":
            model = train_cb(X_train, y_train, X_val, y_val, cat_feat)
            y_pred = model.predict(X_test)
        else:
            raise ValueError(model_name)

        oof_pred[test_idx] = y_pred
        m = compute_metrics(y_test, y_pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)

    agg = {
        "model": model_name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "source_breakdown": source_breakdown(
            dev_df[TARGET].values, oof_pred, dev_df[SOURCE_COL].values
        ),
        "price_band_breakdown": price_band_breakdown(
            dev_df[TARGET].values, oof_pred, dev_df[PRICE_COL].values
        ),
    }
    return agg


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Phase 2 — Cold 비선형 모델 (GroupKFold 5-fold OOF)")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    results = {}
    for name in ["LightGBM", "XGBoost", "CatBoost"]:
        logger.info(f"\n--- {name} ---")
        try:
            res = run_tree_cold(name, dev_df, cold_meta["folds"])
            results[name] = res
            m = res["median"]
            logger.info(
                f"  med_APE={m['median_ape']:.3f} MAPE={m['mape']:.3f} "
                f"RMSE_log={m['rmse_log']:.3f} W30={m['within_30pct']:.3f}"
            )
        except Exception as e:
            logger.error(f"  {name} 실패: {e}")
            results[name] = {"error": str(e)}

    print()
    print("=" * 90)
    print("📊 Phase 2 Cold 비선형 모델 결과 (5-fold GroupKFold OOF, fold-median)")
    print("=" * 90)
    print(f"{'Model':<14} {'med_APE':>9} {'MAPE':>8} {'RMSE_log':>9} {'W30':>7} {'W50':>7}")
    print("-" * 70)
    for name, res in results.items():
        if "error" in res:
            print(f"{name:<14} ERROR: {res['error']}")
            continue
        m = res["median"]
        print(f"{name:<14} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
              f"{m['rmse_log']:>9.3f} {m['within_30pct']:>7.3f} {m['within_50pct']:>7.3f}")

    valid = {k: v for k, v in results.items() if "error" not in v}
    if valid:
        best = min(valid, key=lambda k: valid[k]["median"]["median_ape"])
        print()
        print(f"📊 Best ({best}) — Source / Price-band breakdown")
        print("=" * 90)
        sb = valid[best]["source_breakdown"]
        print(f"Source:    {'src':<8} {'n':>7} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
        for src, m in sb.items():
            print(f"           {src:<8} {m['n']:>7,} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['within_30pct']:>7.3f}")
        print()
        pb = valid[best]["price_band_breakdown"]
        print(f"Price band:{'band':<8} {'n':>7} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
        for band, m in pb.items():
            print(f"           {band:<8} {m['n']:>7,} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['within_30pct']:>7.3f}")

        # Phase 4.5 trigger 체크
        print()
        print("🚨 Phase 4.5 Trigger 체크:")
        b4_mape = pb.get("B4", {}).get("median_ape", None)
        m100_mape = pb.get(">100M", {}).get("median_ape", None)
        trigger_b4 = b4_mape is not None and b4_mape > 0.50
        trigger_100m = m100_mape is not None and m100_mape > 0.70
        print(f"  B4 (>10M) median_APE = {b4_mape:.3f}  {'⚠️ TRIGGER' if trigger_b4 else '✓ OK'} (threshold 0.50)")
        if m100_mape is not None:
            print(f"  >100M median_APE      = {m100_mape:.3f}  {'⚠️ TRIGGER' if trigger_100m else '✓ OK'} (threshold 0.70)")
        if trigger_b4 or trigger_100m:
            print("  → Phase 4.5 (2-stage 거장 모델) 즉시 실행 필요")

    # Phase 1 비교
    print()
    print("📝 Phase 1 (선형) vs Phase 2 (비선형) Cold 비교:")
    print(f"  - Phase 1 Best (Quantile_q05): med_APE 0.429")
    if valid:
        m = valid[best]["median"]
        print(f"  - Phase 2 Best ({best}): med_APE {m['median_ape']:.3f}")
        delta = 0.429 - m["median_ape"]
        print(f"    → 비선형 향상: ↓{delta:.3f}")
    print()

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
