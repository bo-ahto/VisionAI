"""Track 3 PR15 — Depth feature 영향 측정 (release_split 기반).

사용자 요청: 깊이 feature를 (1) 유무만 / (2) cm만 / (3) 둘 다 / (baseline) 둘 다 제외 비교.

Variants:
  D_none:     깊이 정보 제외 (baseline)
  A_has:      has_depth만 (binary)
  B_cm:       depth_cm만 (실수)
  C_both:     has_depth + depth_cm

Eval:
  release_split train / test_warm / test_cold 사용
  Cold LAD (test_cold) + Warm Tuned LGB (test_warm)

Breakdown:
  - test_warm overall
  - test_cold overall
  - has_depth=1 vs has_depth=0
  - medium_category별
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
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_pr15_depth_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
SEED = 42

BASE_NO_DEPTH = ["medium_category", "support_category",
                 "log_area", "estimated_ho", "orientation",
                 "medium_ho_bucket", "artist_works_log", "aspect_ratio"]
BASE_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]

VARIANTS = {
    "D_none":    [],
    "A_has":     ["has_depth"],
    "B_cm":      ["depth_cm"],
    "C_both":    ["has_depth", "depth_cm"],
}


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def build_cold_lad(features, cat_cols):
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
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


def train_warm_lgb(df_train, features, cat_cols, train_counts):
    df_feat = make_features(df_train, train_counts)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(df_feat))
    cut = int(len(df_feat) * 0.1)
    va_idx = perm[:cut]; tr_idx = perm[cut:]
    X_tr = to_cat(df_feat.iloc[tr_idx], features, cat_cols)
    X_va = to_cat(df_feat.iloc[va_idx], features, cat_cols)
    y_tr = df_feat.iloc[tr_idx][TARGET].values
    y_va = df_feat.iloc[va_idx][TARGET].values
    params = {"objective": "regression", "metric": "rmse",
              "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
              "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
              "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1, "seed": SEED}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_cols)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=cat_cols, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"n": int(len(y_true)),
            "median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30))}


def run_variant(name, depth_feats, train_df, test_warm_df, test_cold_df, train_counts):
    """한 variant 학습 + 평가."""
    cold_feats = BASE_NO_DEPTH + depth_feats
    warm_feats = cold_feats + [ARTIST_COL]
    warm_cat = BASE_CAT + [ARTIST_COL]

    logger.info(f"\n[{name}] features = BASE + {depth_feats}")

    tr_feat = make_features(train_df, train_counts)
    cold_model = build_cold_lad(cold_feats, BASE_CAT)
    cold_model.fit(tr_feat[cold_feats], tr_feat[TARGET].values)

    warm_model = train_warm_lgb(train_df, warm_feats, warm_cat, train_counts)

    # test_cold (Cold LAD)
    cold_feat = make_features(test_cold_df, train_counts)
    cold_pred = cold_model.predict(cold_feat[cold_feats])

    # test_warm (Warm LGB)
    warm_feat = make_features(test_warm_df, train_counts)
    X_warm = to_cat(warm_feat, warm_feats, warm_cat)
    warm_pred = warm_model.predict(X_warm)

    result = {
        "variant": name,
        "depth_feats": depth_feats,
        "cold_features_count": len(cold_feats),
        "warm_features_count": len(warm_feats),
        "test_cold": compute_metrics(test_cold_df[TARGET].values, cold_pred),
        "test_warm": compute_metrics(test_warm_df[TARGET].values, warm_pred),
    }

    # has_depth=1 vs has_depth=0 분해
    for label, mask in [
        ("test_cold_3d (has_depth=1)", test_cold_df["has_depth"] == 1),
        ("test_cold_2d (has_depth=0)", test_cold_df["has_depth"] == 0),
    ]:
        if mask.sum() > 0:
            result[label] = compute_metrics(
                test_cold_df.loc[mask, TARGET].values, cold_pred[mask.values])
    for label, mask in [
        ("test_warm_3d (has_depth=1)", test_warm_df["has_depth"] == 1),
        ("test_warm_2d (has_depth=0)", test_warm_df["has_depth"] == 0),
    ]:
        if mask.sum() > 0:
            result[label] = compute_metrics(
                test_warm_df.loc[mask, TARGET].values, warm_pred[mask.values])

    # medium별 breakdown (test_cold)
    medium_brk = {}
    for med in test_cold_df["medium_category"].unique():
        mask = (test_cold_df["medium_category"] == med).values
        if mask.sum() >= 20:
            medium_brk[str(med)] = compute_metrics(
                test_cold_df[TARGET].values[mask], cold_pred[mask])
    result["test_cold_by_medium"] = medium_brk

    return result, cold_pred, warm_pred


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR15 — Depth feature ablation (release_split)")
    logger.info("=" * 70)

    train_df = pd.read_csv(SPLIT / "track3_train.csv")
    test_warm_df = pd.read_csv(SPLIT / "track3_test_warm.csv")
    test_cold_df = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train_df):,} / test_warm {len(test_warm_df):,} / test_cold {len(test_cold_df):,}")

    # has_depth=1 비중
    for name, d in [("train", train_df), ("test_warm", test_warm_df), ("test_cold", test_cold_df)]:
        pct = 100 * (d["has_depth"] == 1).mean()
        logger.info(f"  {name}: has_depth=1 비중 {pct:.1f}%")

    # train 작가 작품수 (train만 보고)
    train_counts = train_df[ARTIST_COL].value_counts().to_dict()

    # 4 variants 실행
    results = {}
    cold_preds = {}
    warm_preds = {}
    for name, depth_feats in VARIANTS.items():
        r, cp, wp = run_variant(name, depth_feats, train_df, test_warm_df, test_cold_df, train_counts)
        results[name] = r
        cold_preds[name] = cp
        warm_preds[name] = wp

    # 출력
    print()
    print("=" * 90)
    print("📊 PR15 — Depth feature ablation (release_split, Cold LAD + Warm Tuned LGB)")
    print("=" * 90)

    print()
    print(f"{'Variant':<12} {'Cold med_APE':>13} {'Cold W30':>10} {'Warm med_APE':>13} {'Warm W30':>10}")
    print("-" * 70)
    for name in VARIANTS:
        r = results[name]
        c = r["test_cold"]; w = r["test_warm"]
        print(f"{name:<12} {c['median_ape']:>13.4f} {c['within_30pct']:>10.4f} "
              f"{w['median_ape']:>13.4f} {w['within_30pct']:>10.4f}")

    # Cold delta from D_none baseline
    print()
    print("=" * 90)
    print("Δ vs D_none (깊이 무관 baseline)")
    print("=" * 90)
    base_c = results["D_none"]["test_cold"]["median_ape"]
    base_w = results["D_none"]["test_warm"]["median_ape"]
    print(f"{'Variant':<12} {'ΔCold':>10} {'ΔWarm':>10}")
    for name in ["A_has", "B_cm", "C_both"]:
        dc = results[name]["test_cold"]["median_ape"] - base_c
        dw = results[name]["test_warm"]["median_ape"] - base_w
        print(f"{name:<12} {dc:>+10.4f} {dw:>+10.4f}")

    # 3D (has_depth=1) only
    print()
    print("=" * 90)
    print("3D 작품(has_depth=1)만 — depth feature가 가장 영향 있어야 할 subset")
    print("=" * 90)
    print(f"{'Variant':<12} {'Cold3D med_APE':>15} {'Cold2D med_APE':>15} {'Warm3D med_APE':>15} {'Warm2D med_APE':>15}")
    for name in VARIANTS:
        r = results[name]
        c3 = r.get("test_cold_3d (has_depth=1)", {}).get("median_ape", float('nan'))
        c2 = r.get("test_cold_2d (has_depth=0)", {}).get("median_ape", float('nan'))
        w3 = r.get("test_warm_3d (has_depth=1)", {}).get("median_ape", float('nan'))
        w2 = r.get("test_warm_2d (has_depth=0)", {}).get("median_ape", float('nan'))
        print(f"{name:<12} {c3:>15.4f} {c2:>15.4f} {w3:>15.4f} {w2:>15.4f}")

    # medium별 cold breakdown
    print()
    print("=" * 90)
    print("test_cold per-medium (med_APE) — variant 차이")
    print("=" * 90)
    media_set = set()
    for name in VARIANTS:
        media_set.update(results[name]["test_cold_by_medium"].keys())
    media_sorted = sorted(media_set)
    header = f"{'Medium':<12}" + "".join([f"{name:>10}" for name in VARIANTS])
    print(header)
    for med in media_sorted:
        row = f"{med:<12}"
        for name in VARIANTS:
            v = results[name]["test_cold_by_medium"].get(med, {}).get("median_ape")
            row += f"{v:>10.4f}" if v is not None else f"{'':>10}"
        print(row)

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
