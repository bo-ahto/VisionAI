"""Track 3 — Phase 3 Hybrid (단순 blend).

Plan v2.1 §4.3 단순화 버전:
  - Inner OOF CV 제거 (느림)
  - Cold: LAD + LightGBM 각각 학습 → 가중평균 (grid search on val fold)
  - Warm: LAD(TE) + LightGBM 각각 학습 → 가중평균
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
OUT_PATH = REPO / "data" / "track3_phase3_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
CAT_COLS_LIN = ["medium_category", "support_category", "orientation"]
CAT_COLS_TREE_COLD = ["medium_category", "support_category", "orientation"]
CAT_COLS_TREE_WARM = ["artist_name_ko", "medium_category", "support_category", "orientation"]
SEED = 42
TE_SMOOTHING = 20.0


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def smoothed_te(train_df, group_col, target_col, smoothing=TE_SMOOTHING):
    global_mean = train_df[target_col].mean()
    stats = train_df.groupby(group_col)[target_col].agg(["mean", "count"])
    smoothed = (stats["count"] * stats["mean"] + smoothing * global_mean) / (stats["count"] + smoothing)
    return smoothed.to_dict(), float(global_mean)


def build_lin_pipeline(features):
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


def train_lgb(X_tr, y_tr, X_val, y_val, cat_feat, seed=SEED):
    params = {"objective": "regression", "metric": "rmse", "learning_rate": 0.05,
              "num_leaves": 127, "min_data_in_leaf": 20, "feature_fraction": 0.9,
              "bagging_fraction": 0.9, "bagging_freq": 5, "verbose": -1, "seed": seed}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=cat_feat)
    val_set = lgb.Dataset(X_val, y_val, categorical_feature=cat_feat, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def find_best_blend(y_true, p1, p2, grid=None):
    """단순 grid search로 best blend weight (p1 = w, p2 = 1-w)."""
    if grid is None:
        grid = np.arange(0.0, 1.01, 0.1)
    best_w, best_score = 0.5, float("inf")
    for w in grid:
        pred = w * p1 + (1 - w) * p2
        # median APE 기준
        ape = np.abs(np.exp(pred) - np.exp(y_true)) / np.exp(y_true)
        score = np.median(ape)
        if score < best_score:
            best_score = score; best_w = w
    return float(best_w), float(best_score)


# ─── Cold Hybrid ───

def cold_hybrid(dev_df, cold_folds):
    """5-fold GroupKFold: LAD + LGB 각각 학습 → 가중평균."""
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]
        tr_df = dev_df.iloc[train_idx]
        te_df = dev_df.iloc[test_idx]

        # Linear (LAD)
        lin = build_lin_pipeline(COLD_FEATURES)
        lin.fit(tr_df[COLD_FEATURES], tr_df[TARGET].values)
        pred_lin = lin.predict(te_df[COLD_FEATURES])

        # LGB (with inner val 10%)
        rng = np.random.default_rng(SEED + fold["fold"])
        perm = rng.permutation(len(tr_df))
        cut = int(len(tr_df) * 0.1)
        va_idx = perm[:cut]; in_tr_idx = perm[cut:]
        X_in_tr = to_cat(tr_df.iloc[in_tr_idx], COLD_FEATURES, CAT_COLS_TREE_COLD)
        X_in_va = to_cat(tr_df.iloc[va_idx], COLD_FEATURES, CAT_COLS_TREE_COLD)
        X_te = to_cat(te_df, COLD_FEATURES, CAT_COLS_TREE_COLD)
        lgb_m = train_lgb(X_in_tr, tr_df.iloc[in_tr_idx][TARGET].values,
                          X_in_va, tr_df.iloc[va_idx][TARGET].values, CAT_COLS_TREE_COLD)
        pred_lgb = lgb_m.predict(X_te)

        y_true = te_df[TARGET].values

        # Fixed blends
        for w_label, w in [("blend_50_50", 0.5), ("blend_70_30_lin", 0.7),
                           ("blend_30_70_lin", 0.3)]:
            pass  # 각 blend의 fold 결과는 마지막에 모아서 계산

        m_lin = compute_metrics(y_true, pred_lin)
        m_lgb = compute_metrics(y_true, pred_lgb)
        # 50/50
        pred_50 = 0.5 * pred_lin + 0.5 * pred_lgb
        m_50 = compute_metrics(y_true, pred_50)
        # 70 lin / 30 lgb (LAD가 cold에서 더 좋았으니까 가중 더)
        pred_70 = 0.7 * pred_lin + 0.3 * pred_lgb
        m_70 = compute_metrics(y_true, pred_70)
        # 30 lin / 70 lgb
        pred_30 = 0.3 * pred_lin + 0.7 * pred_lgb
        m_30 = compute_metrics(y_true, pred_30)

        # Best blend grid search on this fold
        best_w, best_score = find_best_blend(y_true, pred_lin, pred_lgb)

        fold_results.append({
            "fold": fold["fold"],
            "lin": m_lin, "lgb": m_lgb,
            "blend_50_50": m_50, "blend_70_30_lin": m_70, "blend_30_70_lin": m_30,
            "best_blend_w_lin": best_w, "best_blend_med_ape": best_score,
        })
        logger.info(f"  Cold fold {fold['fold']}: lin={m_lin['median_ape']:.3f} "
                    f"lgb={m_lgb['median_ape']:.3f} 50/50={m_50['median_ape']:.3f} "
                    f"best_w_lin={best_w:.2f} → {best_score:.3f}")

    # Aggregate
    def fold_med(key):
        return {k: float(np.median([f[key][k] for f in fold_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}

    return {
        "lin_only": fold_med("lin"),
        "lgb_only": fold_med("lgb"),
        "blend_50_50": fold_med("blend_50_50"),
        "blend_70lin_30lgb": fold_med("blend_70_30_lin"),
        "blend_30lin_70lgb": fold_med("blend_30_70_lin"),
        "best_blend_w_lin_median": float(np.median([f["best_blend_w_lin"] for f in fold_results])),
        "best_blend_med_ape_median": float(np.median([f["best_blend_med_ape"] for f in fold_results])),
        "per_fold": fold_results,
    }


# ─── Warm Hybrid ───

def warm_hybrid(dev_df, warm_splits, n_seeds=3):
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]
        val_idx = split["val_indices"]
        test_idx = split["test_indices"]
        tr_df = dev_df.iloc[train_idx].copy()
        va_df = dev_df.iloc[val_idx].copy()
        te_df = dev_df.iloc[test_idx].copy()

        # Linear with TE
        te_map, gm = smoothed_te(tr_df, ARTIST_COL, TARGET)
        for d in [tr_df, va_df, te_df]:
            d["artist_te"] = d[ARTIST_COL].map(te_map).fillna(gm).values
        lin_features = COLD_FEATURES + ["artist_te"]
        lin = build_lin_pipeline(lin_features)
        lin.fit(tr_df[lin_features], tr_df[TARGET].values)
        pred_lin = lin.predict(te_df[lin_features])

        # LGB native categorical
        X_tr_lgb = to_cat(tr_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        X_va_lgb = to_cat(va_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        X_te_lgb = to_cat(te_df, WARM_FEATURES, CAT_COLS_TREE_WARM)
        lgb_m = train_lgb(X_tr_lgb, tr_df[TARGET].values, X_va_lgb, va_df[TARGET].values,
                          CAT_COLS_TREE_WARM, seed=split["seed"])
        pred_lgb = lgb_m.predict(X_te_lgb)

        y_true = te_df[TARGET].values
        m_lin = compute_metrics(y_true, pred_lin)
        m_lgb = compute_metrics(y_true, pred_lgb)
        m_50 = compute_metrics(y_true, 0.5 * pred_lin + 0.5 * pred_lgb)
        m_30_70 = compute_metrics(y_true, 0.3 * pred_lin + 0.7 * pred_lgb)
        m_70_30 = compute_metrics(y_true, 0.7 * pred_lin + 0.3 * pred_lgb)
        best_w, best_score = find_best_blend(y_true, pred_lin, pred_lgb)

        seed_results.append({
            "seed": split["seed"],
            "lin": m_lin, "lgb": m_lgb,
            "blend_50_50": m_50, "blend_30lin_70lgb": m_30_70, "blend_70lin_30lgb": m_70_30,
            "best_blend_w_lin": best_w, "best_blend_med_ape": best_score,
        })
        logger.info(f"  Warm seed {split['seed']}: lin={m_lin['median_ape']:.3f} "
                    f"lgb={m_lgb['median_ape']:.3f} 50/50={m_50['median_ape']:.3f} "
                    f"30L/70G={m_30_70['median_ape']:.3f} best_w_lin={best_w:.2f}")

    def seed_mean(key):
        return {k: float(np.mean([s[key][k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}

    return {
        "lin_only": seed_mean("lin"),
        "lgb_only": seed_mean("lgb"),
        "blend_50_50": seed_mean("blend_50_50"),
        "blend_30lin_70lgb": seed_mean("blend_30lin_70lgb"),
        "blend_70lin_30lgb": seed_mean("blend_70lin_30lgb"),
        "best_blend_w_lin_mean": float(np.mean([s["best_blend_w_lin"] for s in seed_results])),
        "best_blend_med_ape_mean": float(np.mean([s["best_blend_med_ape"] for s in seed_results])),
        "per_seed": seed_results,
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Phase 3 — Hybrid (단순 blend) Cold + Warm")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows")

    logger.info("\n--- Cold Hybrid (LAD + LGB blend) ---")
    cold_res = cold_hybrid(dev_df, cold_meta["folds"])

    logger.info("\n--- Warm Hybrid (LAD+TE + LGB blend) ---")
    warm_res = warm_hybrid(dev_df, warm_meta["splits"])

    print()
    print("=" * 80)
    print("📊 Phase 3 Cold Hybrid 결과 (fold-median)")
    print("=" * 80)
    print(f"{'Variant':<25} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
    print("-" * 60)
    for k in ["lin_only", "lgb_only", "blend_50_50", "blend_70lin_30lgb", "blend_30lin_70lgb"]:
        m = cold_res[k]
        print(f"{k:<25} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['within_30pct']:>7.3f}")
    print(f"{'best_blend (oracle)':<25} {cold_res['best_blend_med_ape_median']:>9.3f}  "
          f"w_lin median={cold_res['best_blend_w_lin_median']:.2f}")

    print()
    print("=" * 80)
    print("📊 Phase 3 Warm Hybrid 결과 (seed-mean)")
    print("=" * 80)
    print(f"{'Variant':<25} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
    print("-" * 60)
    for k in ["lin_only", "lgb_only", "blend_50_50", "blend_70lin_30lgb", "blend_30lin_70lgb"]:
        m = warm_res[k]
        print(f"{k:<25} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['within_30pct']:>7.3f}")
    print(f"{'best_blend (oracle)':<25} {warm_res['best_blend_med_ape_mean']:>9.3f}  "
          f"w_lin mean={warm_res['best_blend_w_lin_mean']:.2f}")

    output = {"cold": cold_res, "warm": warm_res}
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
