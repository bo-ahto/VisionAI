"""Track 3 PR9 — Quantile objective + Sample reweighting.

Codex 권장: heteroscedastic 처리 (고가 구간 오차 큼 → quantile loss)
            sample reweighting (가격대 균형, source 균형)

설계:
- Baseline = PR7 ALL Cold (LAD 0.391) / Warm Tuned LGB (0.104)
- Variant A: LightGBM Quantile objective (q=0.5) Cold — LAD를 nonlinear로
- Variant B: Sample weight Cold (price-band reverse-frequency)
- Variant C: Source-balanced weight (PR5 발견 활용)
- Variant D: Combined (Quantile LGB + price-band weight)

PR7 ALL features 그대로 사용.
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
OUT_PATH = REPO / "data" / "track3_pr9_quantile_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
SOURCE_COL = "source_platform"
BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]
NEW_CAT = ["source_platform", "medium_ho_bucket"]
NEW_NUM = ["artist_works_log", "aspect_ratio"]
ALL_FEATURES = BASE_FEATURES + NEW_CAT + NEW_NUM
ALL_CAT = BASE_CAT + NEW_CAT
WARM_FEATURES = ALL_FEATURES + [ARTIST_COL]
WARM_CAT = ALL_CAT + [ARTIST_COL]
SEED = 42

PRICE_BANDS = {"B1": (0, 1_000_000), "B2": (1_000_000, 3_000_000),
               "B3": (3_000_000, 10_000_000), "B4": (10_000_000, float("inf"))}


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def price_band_breakdown(y_true_ln, y_pred_ln, prices):
    result = {}
    for band, (lo, hi) in PRICE_BANDS.items():
        mask = (prices > lo) & (prices <= hi)
        if mask.sum() > 0:
            result[band] = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
    return result


def make_features(df, train_artist_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_artist_counts).fillna(0))
    return df


def build_lad(features, cat_cols):
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


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat, seed, objective="regression",
              alpha=0.5, sample_weight=None):
    params = {"objective": objective, "learning_rate": 0.04, "num_leaves": 127,
              "min_data_in_leaf": 50, "feature_fraction": 0.9, "bagging_fraction": 0.9,
              "bagging_freq": 5, "verbose": -1, "seed": seed}
    if objective == "regression":
        params["metric"] = "rmse"
    elif objective == "quantile":
        params["alpha"] = alpha
        params["metric"] = "quantile"
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat, weight=sample_weight)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def price_band_weights(prices):
    """역빈도 weight — B4 (>10M) 같이 적은 구간에 더 큰 가중치."""
    bands = np.digitize(prices, bins=[1_000_000, 3_000_000, 10_000_000])
    # band 0=B1, 1=B2, 2=B3, 3=B4
    counts = np.bincount(bands, minlength=4)
    inv_freq = len(prices) / (4 * counts.clip(min=1))
    inv_freq = np.clip(inv_freq, 0.5, 3.0)  # cap [0.5, 3.0]
    return inv_freq[bands]


def source_balanced_weights(sources):
    """역빈도 weight by source."""
    counts = pd.Series(sources).value_counts()
    total = len(sources)
    inv_freq = {src: min(3.0, total / (3 * n)) for src, n in counts.items()}
    return np.array([inv_freq[s] for s in sources])


# ─── Cold evaluation ───

def eval_cold_lad(dev_df, cold_folds):
    """PR7 ALL Cold LAD (baseline)."""
    fold_results = []
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        counts = tr_df[ARTIST_COL].value_counts().to_dict()
        tr_feat = make_features(tr_df, counts)
        te_feat = make_features(te_df, counts)
        model = build_lad(ALL_FEATURES, ALL_CAT)
        model.fit(tr_feat[ALL_FEATURES], tr_feat[TARGET].values)
        pred = model.predict(te_feat[ALL_FEATURES])
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold["fold"]
        m["price_band"] = price_band_breakdown(te_feat[TARGET].values, pred,
                                                te_feat[PRICE_COL].values)
        fold_results.append(m)
    return aggregate(fold_results, "Cold_LAD_baseline")


def eval_cold_lgb_quantile(dev_df, cold_folds, alpha=0.5, weight_fn=None, name="Cold_LGB_quantile"):
    """LightGBM quantile objective + optional sample weight."""
    fold_results = []
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        counts = tr_df[ARTIST_COL].value_counts().to_dict()
        tr_feat = make_features(tr_df, counts)
        te_feat = make_features(te_df, counts)

        rng = np.random.default_rng(SEED + fold["fold"])
        perm = rng.permutation(len(tr_feat))
        cut = int(len(tr_feat) * 0.1)
        va_idx = perm[:cut]; in_tr = perm[cut:]
        tr_in = tr_feat.iloc[in_tr]
        va_in = tr_feat.iloc[va_idx]

        X_tr = to_cat(tr_in, ALL_FEATURES, ALL_CAT)
        X_va = to_cat(va_in, ALL_FEATURES, ALL_CAT)
        X_te = to_cat(te_feat, ALL_FEATURES, ALL_CAT)
        y_tr = tr_in[TARGET].values
        y_va = va_in[TARGET].values

        weights = weight_fn(tr_in) if weight_fn else None

        model = train_lgb(X_tr, y_tr, X_va, y_va, ALL_CAT, SEED,
                          objective="quantile", alpha=alpha, sample_weight=weights)
        pred = model.predict(X_te)
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold["fold"]
        m["price_band"] = price_band_breakdown(te_feat[TARGET].values, pred,
                                                te_feat[PRICE_COL].values)
        fold_results.append(m)
    return aggregate(fold_results, name)


def aggregate(fold_results, name):
    return {
        "model": name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "price_band_median": {
            band: {
                k: float(np.median([f["price_band"].get(band, {}).get(k, np.nan)
                                     for f in fold_results
                                     if band in f.get("price_band", {})]))
                for k in ["median_ape", "mape", "within_30pct"]
            }
            for band in PRICE_BANDS
        },
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR9 — Quantile objective + Sample reweighting")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    results = {}

    # Baseline: PR7 ALL Cold LAD
    logger.info("\n--- Baseline: Cold LAD PR7 ALL ---")
    results["A_baseline_lad"] = eval_cold_lad(dev_df, cold_meta["folds"])
    logger.info(f"  med_APE={results['A_baseline_lad']['median']['median_ape']:.3f}")

    # Variant 1: LightGBM Quantile q=0.5 (no weight)
    logger.info("\n--- Variant 1: LGB Quantile q=0.5 ---")
    results["B_lgb_quantile"] = eval_cold_lgb_quantile(dev_df, cold_meta["folds"],
                                                        alpha=0.5, weight_fn=None,
                                                        name="LGB_quantile")
    logger.info(f"  med_APE={results['B_lgb_quantile']['median']['median_ape']:.3f}")

    # Variant 2: LGB Quantile + price-band reweight
    logger.info("\n--- Variant 2: LGB Quantile + price-band reweight ---")
    def price_weight_fn(df_in):
        return price_band_weights(df_in[PRICE_COL].values)
    results["C_lgb_q_priceweight"] = eval_cold_lgb_quantile(dev_df, cold_meta["folds"],
                                                              alpha=0.5, weight_fn=price_weight_fn,
                                                              name="LGB_q_priceweight")
    logger.info(f"  med_APE={results['C_lgb_q_priceweight']['median']['median_ape']:.3f}")

    # Variant 3: LGB Quantile + source reweight
    logger.info("\n--- Variant 3: LGB Quantile + source reweight ---")
    def source_weight_fn(df_in):
        return source_balanced_weights(df_in[SOURCE_COL].values)
    results["D_lgb_q_sourceweight"] = eval_cold_lgb_quantile(dev_df, cold_meta["folds"],
                                                               alpha=0.5, weight_fn=source_weight_fn,
                                                               name="LGB_q_sourceweight")
    logger.info(f"  med_APE={results['D_lgb_q_sourceweight']['median']['median_ape']:.3f}")

    # Variant 4: LGB Quantile + 결합 weight (price × source)
    logger.info("\n--- Variant 4: LGB Quantile + price × source weight ---")
    def combined_weight_fn(df_in):
        return price_band_weights(df_in[PRICE_COL].values) * \
               source_balanced_weights(df_in[SOURCE_COL].values)
    results["E_lgb_q_combined"] = eval_cold_lgb_quantile(dev_df, cold_meta["folds"],
                                                           alpha=0.5, weight_fn=combined_weight_fn,
                                                           name="LGB_q_combined")
    logger.info(f"  med_APE={results['E_lgb_q_combined']['median']['median_ape']:.3f}")

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 PR9 — Quantile + Reweight 결과 (Cold, 5-fold GroupKFold OOF)")
    print("=" * 80)
    print()
    print(f"{'Variant':<22} {'med_APE':>9} {'MAPE':>8} {'W30':>7} {'B4 med_APE':>11}")
    print("-" * 80)
    base_med = results["A_baseline_lad"]["median"]["median_ape"]
    for name, res in results.items():
        m = res["median"]
        b4 = res["price_band_median"].get("B4", {}).get("median_ape", float("nan"))
        delta = m["median_ape"] - base_med
        mark = "★" if delta < -0.001 else ("⚠️" if delta > 0.001 else "")
        print(f"{name:<22} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
              f"{m['within_30pct']:>7.3f} {b4:>11.3f}  {delta:+.3f} {mark}")

    print()
    print("Price-band 별 med_APE (best vs baseline):")
    best = min(results, key=lambda k: results[k]["median"]["median_ape"])
    print(f"  best variant = {best}")
    print(f"  {'band':<5} {'baseline':>10} {'best':>10}")
    for band in ["B1", "B2", "B3", "B4"]:
        b_val = results["A_baseline_lad"]["price_band_median"].get(band, {}).get("median_ape", 0)
        n_val = results[best]["price_band_median"].get(band, {}).get("median_ape", 0)
        print(f"  {band:<5} {b_val:>10.3f} {n_val:>10.3f}")

    print()
    print("📝 해석:")
    if results[best]["median"]["median_ape"] < base_med - 0.005:
        print(f"  ✅ '{best}' baseline 대비 -{base_med - results[best]['median']['median_ape']:.3f} 개선")
    else:
        print(f"  ⚠️ 모든 variant baseline (0.391) 대비 개선 미미 또는 악화")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
