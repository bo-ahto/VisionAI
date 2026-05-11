"""Track 3 PR3 — Conformal prediction (신뢰구간).

목적: 점추정 외 calibrated 80/90% 신뢰구간 제공.

방법: Split conformal prediction
  1. Train: 60% (모델 학습)
  2. Calib: 20% (calibration set으로 nonconformity score 분포)
  3. Test: 20% (calibrated 구간 평가)
  4. Quantile q=0.9, 0.95로 conformity threshold 결정

Cold (LAD) + Warm (LightGBM) 둘 다.
Coverage 분해: source × price-band 12 셀 (Plan v2.1 §4.6).
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
OUT_PATH = REPO / "data" / "track3_pr3_conformal_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
SOURCE_COL = "source_platform"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_LIN = ["medium_category", "support_category", "orientation"]
CAT_COLS_TREE = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42

PRICE_BANDS = {"B1": (0, 1_000_000), "B2": (1_000_000, 3_000_000),
               "B3": (3_000_000, 10_000_000), "B4": (10_000_000, float("inf"))}
COVERAGE_TARGETS = [0.80, 0.90]


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


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat):
    params = {"objective": "regression", "metric": "rmse",
              "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
              "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
              "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1, "seed": SEED}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def conformal_intervals(y_pred, calib_residuals, target_coverage):
    """Split conformal: calib_residuals의 quantile로 interval 반환."""
    # residual = |y_true - y_pred| (log space)
    q = np.quantile(calib_residuals, target_coverage)
    return y_pred - q, y_pred + q  # log space intervals


def coverage_metrics(y_true, y_pred, lo, hi, prices, sources):
    """전체 + source × price-band coverage 계산."""
    covered = (y_true >= lo) & (y_true <= hi)
    width = np.exp(hi) - np.exp(lo)  # 원본 KRW 폭
    width_relative = width / np.exp(y_pred)  # 예측값 대비 폭

    result = {
        "overall": {
            "n": int(len(y_true)),
            "coverage": float(covered.mean()),
            "median_width_pct": float(np.median(width_relative) * 100),  # 예측값 대비 %
        },
        "by_source": {},
        "by_price_band": {},
        "by_source_x_band": {},
    }

    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() > 0:
            result["by_source"][src] = {
                "n": int(mask.sum()),
                "coverage": float(covered[mask].mean()),
            }

    for band, (lo_p, hi_p) in PRICE_BANDS.items():
        mask = (prices > lo_p) & (prices <= hi_p)
        if mask.sum() > 0:
            result["by_price_band"][band] = {
                "n": int(mask.sum()),
                "coverage": float(covered[mask].mean()),
            }

    for src in ["artsy", "saatchi", "artue"]:
        for band, (lo_p, hi_p) in PRICE_BANDS.items():
            mask = (sources == src) & (prices > lo_p) & (prices <= hi_p)
            if mask.sum() > 5:
                result["by_source_x_band"][f"{src}_{band}"] = {
                    "n": int(mask.sum()),
                    "coverage": float(covered[mask].mean()),
                }

    return result


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR3 — Conformal prediction (신뢰구간)")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    # 3-way split: 60 / 20 calib / 20 test
    split = warm_meta["splits"][0]
    # warm split은 80/10/10 → train_idx를 60/20 분할 (cal_idx)
    full_train_idx = np.array(split["train_indices"] + split["val_indices"])
    test_idx = split["test_indices"]
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(full_train_idx))
    cut = int(len(full_train_idx) * 0.75)  # 75/25 split (전체 90%→ 67.5/22.5 ≈ 60/20)
    tr_idx_final = full_train_idx[perm[:cut]]
    cal_idx = full_train_idx[perm[cut:]]
    logger.info(f"Train: {len(tr_idx_final):,} / Calib: {len(cal_idx):,} / Test: {len(test_idx):,}")

    tr_df = dev_df.iloc[tr_idx_final]
    cal_df = dev_df.iloc[cal_idx]
    te_df = dev_df.iloc[test_idx]

    results = {}

    # ─── Warm LGB Conformal ───
    logger.info("\n--- Warm LightGBM Conformal ---")
    # Inner val for early stopping
    n_tr = len(tr_df)
    perm_in = rng.permutation(n_tr)
    cut_in = int(n_tr * 0.1)
    va_in = perm_in[:cut_in]
    tr_in = perm_in[cut_in:]

    X_tr_w = to_cat(tr_df.iloc[tr_in], WARM_FEATURES, CAT_COLS_TREE)
    X_va_w = to_cat(tr_df.iloc[va_in], WARM_FEATURES, CAT_COLS_TREE)
    X_cal_w = to_cat(cal_df, WARM_FEATURES, CAT_COLS_TREE)
    X_te_w = to_cat(te_df, WARM_FEATURES, CAT_COLS_TREE)

    warm_model = train_lgb(X_tr_w, tr_df.iloc[tr_in][TARGET].values,
                           X_va_w, tr_df.iloc[va_in][TARGET].values, CAT_COLS_TREE)
    pred_cal = warm_model.predict(X_cal_w)
    pred_te = warm_model.predict(X_te_w)

    # Nonconformity = absolute log residual
    calib_residuals = np.abs(cal_df[TARGET].values - pred_cal)

    for tc in COVERAGE_TARGETS:
        lo, hi = conformal_intervals(pred_te, calib_residuals, tc)
        cov = coverage_metrics(te_df[TARGET].values, pred_te, lo, hi,
                                te_df[PRICE_COL].values, te_df[SOURCE_COL].values)
        results[f"warm_lgb_{int(tc*100)}pct"] = cov
        logger.info(f"  Warm @{int(tc*100)}%: coverage={cov['overall']['coverage']:.3f}, "
                    f"median width={cov['overall']['median_width_pct']:.1f}% of pred")

    # ─── Cold LAD Conformal ───
    logger.info("\n--- Cold LAD Conformal ---")
    cold_model = build_lad_pipeline(COLD_FEATURES)
    cold_model.fit(tr_df[COLD_FEATURES], tr_df[TARGET].values)
    pred_cal_c = cold_model.predict(cal_df[COLD_FEATURES])
    pred_te_c = cold_model.predict(te_df[COLD_FEATURES])
    calib_residuals_c = np.abs(cal_df[TARGET].values - pred_cal_c)

    for tc in COVERAGE_TARGETS:
        lo, hi = conformal_intervals(pred_te_c, calib_residuals_c, tc)
        cov = coverage_metrics(te_df[TARGET].values, pred_te_c, lo, hi,
                                te_df[PRICE_COL].values, te_df[SOURCE_COL].values)
        results[f"cold_lad_{int(tc*100)}pct"] = cov
        logger.info(f"  Cold @{int(tc*100)}%: coverage={cov['overall']['coverage']:.3f}, "
                    f"median width={cov['overall']['median_width_pct']:.1f}% of pred")

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 PR3 — Conformal Prediction (80% / 90% coverage)")
    print("=" * 80)
    print()
    for key, cov in results.items():
        print(f"\n[{key}]")
        o = cov["overall"]
        print(f"  Overall: coverage={o['coverage']:.3f} (목표 {key.split('_')[-1]}), "
              f"median width = ±{o['median_width_pct']/2:.1f}% of predicted price")
        print(f"  Source breakdown:")
        for src, m in cov["by_source"].items():
            print(f"    {src:<8} n={m['n']:>5,}  coverage={m['coverage']:.3f}")
        print(f"  Price-band breakdown:")
        for band, m in cov["by_price_band"].items():
            print(f"    {band:<6} n={m['n']:>5,}  coverage={m['coverage']:.3f}")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
