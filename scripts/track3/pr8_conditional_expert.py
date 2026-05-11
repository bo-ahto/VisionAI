"""Track 3 PR8 — Cold Conditional Expert + Fallback.

Codex 권장: "Cold에서 언제 어떤 규칙을 켤지" 배우는 conditional expert.
            Hard 분리 위험 회피 → fallback 구조 필수.

설계:
- Baseline = PR7 ALL Cold (LAD 6 features + source + interaction + popularity + aspect, med_APE 0.391)
- Variant A: Source-conditional (Artsy/Saatchi/Artue 별 LAD + fallback global LAD)
- Variant B: Source × ho_bucket cell expert (12 cells + fallback)
- Variant C: Soft expert (예측 가격대로 expert weight, fallback global)

평가: 5-fold GroupKFold OOF.
Fallback: 셀 표본 < N_MIN → global LAD 사용.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_pr8_conditional_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
SOURCE_COL = "source_platform"
BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]
NEW_CAT = ["source_platform", "medium_ho_bucket"]  # interaction
NEW_NUM = ["artist_works_log", "aspect_ratio"]
SEED = 42
N_MIN_CELL = 200  # cell expert를 학습하려면 최소 표본 (아니면 fallback)


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
            "n": int(len(y_true))}


def make_features(df, train_artist_counts=None):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    if train_artist_counts is not None:
        df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_artist_counts).fillna(0))
    else:
        df["artist_works_log"] = 0.0
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


# ─── ALL features (PR7 best) ───
ALL_FEATURES = BASE_FEATURES + NEW_CAT + NEW_NUM
ALL_CAT = BASE_CAT + NEW_CAT


# ─── Variant A: Source-conditional ───

def predict_source_conditional(tr_df, te_df, fallback_n_min=N_MIN_CELL):
    """각 source 별 LAD + fallback global."""
    # Global fallback
    fallback = build_lad(ALL_FEATURES, ALL_CAT)
    fallback.fit(tr_df[ALL_FEATURES], tr_df[TARGET].values)

    # Source experts
    experts = {}
    for src in tr_df[SOURCE_COL].unique():
        sub = tr_df[tr_df[SOURCE_COL] == src]
        if len(sub) >= fallback_n_min:
            # source feature 제외 (이미 conditional)
            feats = [f for f in ALL_FEATURES if f != SOURCE_COL]
            cats = [c for c in ALL_CAT if c != SOURCE_COL]
            m = build_lad(feats, cats)
            m.fit(sub[feats], sub[TARGET].values)
            experts[src] = (m, feats)

    # Predict
    pred = np.zeros(len(te_df))
    fallback_count = 0
    for i, (_, row) in enumerate(te_df.iterrows()):
        src = row[SOURCE_COL]
        if src in experts:
            model, feats = experts[src]
            pred[i] = model.predict(row[feats].to_frame().T)[0]
        else:
            pred[i] = fallback.predict(row[ALL_FEATURES].to_frame().T)[0]
            fallback_count += 1
    return pred, fallback_count, len(experts)


# ─── Variant B: Source × ho_bucket cell expert ───

def predict_cell_expert(tr_df, te_df, fallback_n_min=N_MIN_CELL):
    """각 (source × ho_bucket) 셀 별 LAD + fallback global."""
    fallback = build_lad(ALL_FEATURES, ALL_CAT)
    fallback.fit(tr_df[ALL_FEATURES], tr_df[TARGET].values)

    # Cell experts
    experts = {}
    for (src, hb), sub in tr_df.groupby([SOURCE_COL, "ho_bucket"]):
        if len(sub) >= fallback_n_min:
            feats = [f for f in ALL_FEATURES if f not in [SOURCE_COL]]
            cats = [c for c in ALL_CAT if c != SOURCE_COL]
            m = build_lad(feats, cats)
            m.fit(sub[feats], sub[TARGET].values)
            experts[(src, hb)] = (m, feats)

    pred = np.zeros(len(te_df))
    fallback_count = 0
    for i, (_, row) in enumerate(te_df.iterrows()):
        key = (row[SOURCE_COL], row["ho_bucket"])
        if key in experts:
            model, feats = experts[key]
            pred[i] = model.predict(row[feats].to_frame().T)[0]
        else:
            pred[i] = fallback.predict(row[ALL_FEATURES].to_frame().T)[0]
            fallback_count += 1
    return pred, fallback_count, len(experts)


# ─── Variant C: Soft expert (예측 가격대 기반 weight) ───

def predict_soft_expert(tr_df, te_df, n_min=N_MIN_CELL):
    """1차 예측 → 가격대로 expert 선택 (soft weight)."""
    # 1차: global LAD
    global_model = build_lad(ALL_FEATURES, ALL_CAT)
    global_model.fit(tr_df[ALL_FEATURES], tr_df[TARGET].values)
    pred_global_te = global_model.predict(te_df[ALL_FEATURES])

    # Price-band별 expert (train 가격 기준)
    bands = {"low": (0, 1_000_000), "mid": (1_000_000, 10_000_000),
             "high": (10_000_000, float("inf"))}
    experts = {}
    for band, (lo, hi) in bands.items():
        mask = (tr_df[PRICE_COL] > lo) & (tr_df[PRICE_COL] <= hi)
        sub = tr_df[mask]
        if len(sub) >= n_min:
            m = build_lad(ALL_FEATURES, ALL_CAT)
            m.fit(sub[ALL_FEATURES], sub[TARGET].values)
            experts[band] = m

    # Test 예측: 1차 예측 가격대로 expert 선택
    pred = np.zeros(len(te_df))
    for i in range(len(te_df)):
        pred_price = np.exp(pred_global_te[i])
        if pred_price <= 1_000_000:
            band = "low"
        elif pred_price <= 10_000_000:
            band = "mid"
        else:
            band = "high"
        if band in experts:
            row = te_df.iloc[i:i+1]
            pred[i] = experts[band].predict(row[ALL_FEATURES])[0]
        else:
            pred[i] = pred_global_te[i]
    return pred, len(experts)


# ─── Evaluation ───

def evaluate_variant(name, predict_fn, dev_df, cold_folds):
    fold_results = []
    for fold in cold_folds:
        tr_df = dev_df.iloc[fold["train_indices"]]
        te_df = dev_df.iloc[fold["test_indices"]]
        artist_counts = tr_df[ARTIST_COL].value_counts().to_dict()
        tr_feat = make_features(tr_df, artist_counts)
        te_feat = make_features(te_df, artist_counts)
        result = predict_fn(tr_feat, te_feat)
        pred = result[0]
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold["fold"]
        if len(result) > 1:
            m["fallback_count"] = result[1]
        if len(result) > 2:
            m["n_experts"] = result[2]
        fold_results.append(m)
        info = f"med_APE={m['median_ape']:.3f}"
        if "n_experts" in m:
            info += f", n_experts={m['n_experts']}, fallback={m.get('fallback_count', 0)}/{m['n']}"
        logger.info(f"  {name} fold {fold['fold']}: {info}")

    return {
        "model": name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR8 — Cold Conditional Expert + Fallback")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    results = {}

    # Baseline = PR7 ALL Cold (재계산)
    def baseline_predict(tr_df, te_df):
        model = build_lad(ALL_FEATURES, ALL_CAT)
        model.fit(tr_df[ALL_FEATURES], tr_df[TARGET].values)
        return (model.predict(te_df[ALL_FEATURES]),)

    logger.info("\n--- Baseline (PR7 ALL — re-eval) ---")
    results["baseline_pr7_all"] = evaluate_variant("baseline_PR7_all", baseline_predict, dev_df, cold_meta["folds"])

    logger.info("\n--- Variant A: Source-conditional ---")
    results["source_conditional"] = evaluate_variant("source_conditional", predict_source_conditional, dev_df, cold_meta["folds"])

    logger.info("\n--- Variant B: Source × ho_bucket cell expert ---")
    results["source_x_ho_cell"] = evaluate_variant("source_x_ho_cell", predict_cell_expert, dev_df, cold_meta["folds"])

    logger.info("\n--- Variant C: Soft expert (price-band) ---")
    results["soft_price_band"] = evaluate_variant("soft_price_band", predict_soft_expert, dev_df, cold_meta["folds"])

    # 결과 출력
    print()
    print("=" * 80)
    print("📊 PR8 — Cold Conditional Expert + Fallback (5-fold GroupKFold OOF)")
    print("=" * 80)
    print(f"{'Variant':<25} {'med_APE':>9} {'MAPE':>8} {'W30':>7} {'vs base':>10}")
    print("-" * 80)
    base_med = results["baseline_pr7_all"]["median"]["median_ape"]
    for name, res in results.items():
        m = res["median"]
        delta = m["median_ape"] - base_med
        mark = "★" if name != "baseline_pr7_all" and delta < 0 else ""
        print(f"{name:<25} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
              f"{m['within_30pct']:>7.3f} {delta:>+10.3f} {mark}")

    print()
    print("📝 해석:")
    best = min([k for k in results], key=lambda k: results[k]["median"]["median_ape"])
    print(f"  Best variant: '{best}' (med_APE={results[best]['median']['median_ape']:.3f})")
    print(f"  vs PR7 baseline (0.391): {results[best]['median']['median_ape'] - 0.391:+.3f}")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
