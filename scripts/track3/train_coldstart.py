"""Track 3 — Phase 4 Cold-start 특화 모델.

Plan v2.1 §4.4:
  - Work-level prototype: K-means → nearest cluster mean price
  - Segmented experts by medium × ho regime
  - KNN retrieval: K-nearest works weighted mean
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.neighbors import KNeighborsRegressor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_phase4_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
CAT_COLS = ["medium_category", "support_category", "orientation"]
NUM_COLS = ["has_depth", "log_area", "estimated_ho"]
SEED = 42


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def make_preprocess():
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CAT_COLS),
        ("num", StandardScaler(), NUM_COLS),
    ])


# ─── 1. Work-level Prototype (K-means) ───

def prototype_model(tr_df, te_df, k=16):
    """K-means on train features → test는 가장 가까운 cluster의 mean ln_price."""
    prep = make_preprocess()
    X_tr = prep.fit_transform(tr_df[COLD_FEATURES])
    X_te = prep.transform(te_df[COLD_FEATURES])
    km = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(X_tr)
    cluster_means = {}
    labels = km.predict(X_tr)
    for c in range(k):
        mask = labels == c
        cluster_means[c] = tr_df.iloc[mask][TARGET].mean() if mask.sum() > 0 else tr_df[TARGET].mean()
    test_labels = km.predict(X_te)
    return np.array([cluster_means[c] for c in test_labels])


# ─── 2. Segmented Experts (medium × ho bucket) ───

def ho_bucket(ho):
    if ho < 5: return "miniature"
    if ho < 20: return "small"
    if ho < 50: return "medium"
    if ho < 100: return "large"
    return "xlarge"


def segmented_experts(tr_df, te_df):
    """medium × ho_bucket 셀별 mean ln_price."""
    tr = tr_df.copy(); te = te_df.copy()
    tr["ho_bucket"] = tr["estimated_ho"].apply(ho_bucket)
    te["ho_bucket"] = te["estimated_ho"].apply(ho_bucket)
    cell_means = tr.groupby(["medium_category", "ho_bucket"])[TARGET].mean()
    global_mean = tr[TARGET].mean()
    medium_means = tr.groupby("medium_category")[TARGET].mean()
    bucket_means = tr.groupby("ho_bucket")[TARGET].mean()

    preds = []
    for _, row in te.iterrows():
        key = (row["medium_category"], row["ho_bucket"])
        if key in cell_means.index:
            preds.append(cell_means[key])
        elif row["medium_category"] in medium_means.index:
            preds.append(medium_means[row["medium_category"]])
        elif row["ho_bucket"] in bucket_means.index:
            preds.append(bucket_means[row["ho_bucket"]])
        else:
            preds.append(global_mean)
    return np.array(preds)


# ─── 3. KNN Retrieval ───

def knn_retrieval(tr_df, te_df, k=10):
    """K-nearest works weighted mean."""
    prep = make_preprocess()
    X_tr = prep.fit_transform(tr_df[COLD_FEATURES])
    X_te = prep.transform(te_df[COLD_FEATURES])
    knn = KNeighborsRegressor(n_neighbors=k, weights="distance", n_jobs=-1)
    knn.fit(X_tr, tr_df[TARGET].values)
    return knn.predict(X_te)


# ─── Main Cold OOF eval ───

def run_cold_method(method_fn, name, dev_df, cold_folds, **kwargs):
    fold_results = []
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        y_pred = method_fn(tr_df, te_df, **kwargs)
        y_true = te_df[TARGET].values
        m = compute_metrics(y_true, y_pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)
    return {"model": name, "n_folds": len(fold_results), "per_fold": fold_results,
            "median": {k: float(np.median([f[k] for f in fold_results]))
                       for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]}}


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Phase 4 — Cold-start 특화")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)

    results = {}
    for k_kmeans in [8, 16, 32]:
        logger.info(f"\n--- Prototype K={k_kmeans} ---")
        res = run_cold_method(prototype_model, f"Prototype_K{k_kmeans}", dev_df, cold_meta["folds"], k=k_kmeans)
        results[f"Prototype_K{k_kmeans}"] = res
        logger.info(f"  med_APE={res['median']['median_ape']:.3f}")

    logger.info("\n--- Segmented Experts (medium × ho_bucket) ---")
    res = run_cold_method(segmented_experts, "Segmented_Experts", dev_df, cold_meta["folds"])
    results["Segmented_Experts"] = res
    logger.info(f"  med_APE={res['median']['median_ape']:.3f}")

    for k_knn in [5, 10, 20]:
        logger.info(f"\n--- KNN k={k_knn} ---")
        res = run_cold_method(knn_retrieval, f"KNN_k{k_knn}", dev_df, cold_meta["folds"], k=k_knn)
        results[f"KNN_k{k_knn}"] = res
        logger.info(f"  med_APE={res['median']['median_ape']:.3f}")

    print()
    print("=" * 80)
    print("📊 Phase 4 Cold-start 특화 모델 결과")
    print("=" * 80)
    print(f"{'Model':<22} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
    print("-" * 50)
    for name, res in results.items():
        m = res["median"]
        print(f"{name:<22} {m['median_ape']:>9.3f} {m['mape']:>8.3f} {m['within_30pct']:>7.3f}")

    best = min(results, key=lambda k: results[k]["median"]["median_ape"])
    print()
    print(f"📝 비교: Phase 1 Cold Best (LAD) = 0.429")
    print(f"        Phase 4 Best ({best}) = {results[best]['median']['median_ape']:.3f}")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
