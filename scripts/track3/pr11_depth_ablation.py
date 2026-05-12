"""Track 3 PR11 — 깊이 (has_depth + depth_cm) ablation.

사용자 질문: 깊이 feature가 가격 예측에 실제 영향 있는가?
            데이터 보니 78% 작품이 has_depth=1, median 2.5cm (캔버스 두께)
            → 설치미술 구분이 아니라 "stretched 캔버스 여부"

설계 (Cold LAD baseline 변형):
  V1: baseline (PR7 ALL with has_depth + depth_cm) — 현재
  V2: - has_depth만 (depth_cm 제거)
  V3: - depth_cm만 (has_depth 제거)
  V4: - 둘 다 제거 (no depth info)

추가:
  V5: 회화만 (canvas/paper/linen) baseline
  V6: 회화만 + 깊이 제거
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
OUT_PATH = REPO / "data" / "track3_pr11_depth_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SEED = 42


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)), "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def make_features(df, train_artist_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_artist_counts).fillna(0))
    return df


CAT_ALL = ["medium_category", "support_category", "orientation",
           "source_platform", "medium_ho_bucket"]


def get_features(include_has_depth=True, include_depth_cm=True):
    feats = ["medium_category", "support_category", "log_area", "estimated_ho",
             "orientation", "source_platform", "medium_ho_bucket",
             "artist_works_log", "aspect_ratio"]
    if include_has_depth:
        feats.append("has_depth")
    if include_depth_cm:
        feats.append("depth_cm")
    return feats


def build_lad(features):
    cat = [c for c in features if c in CAT_ALL]
    num = [c for c in features if c not in CAT_ALL]
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", preprocess),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def evaluate(name, dev_df, cold_folds, include_has_depth, include_depth_cm, filter_mask=None):
    features = get_features(include_has_depth, include_depth_cm)
    fold_results = []
    for fold in cold_folds:
        train_idx = fold["train_indices"]; test_idx = fold["test_indices"]
        tr_df = dev_df.iloc[train_idx]
        te_df = dev_df.iloc[test_idx]
        if filter_mask is not None:
            tr_df = tr_df[filter_mask.loc[tr_df.index]]
            te_df = te_df[filter_mask.loc[te_df.index]]
        if len(tr_df) < 100 or len(te_df) < 50:
            continue
        counts = tr_df[ARTIST_COL].value_counts().to_dict()
        tr_feat = make_features(tr_df, counts)
        te_feat = make_features(te_df, counts)
        model = build_lad(features)
        model.fit(tr_feat[features], tr_feat[TARGET].values)
        pred = model.predict(te_feat[features])
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold["fold"]
        m["n_test"] = len(te_feat)
        fold_results.append(m)

    return {
        "name": name,
        "features": features,
        "n_features": len(features),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR11 — 깊이 (has_depth + depth_cm) ablation")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)

    results = {}

    # 전체 데이터 — 깊이 4 variant
    logger.info("\n--- 전체 데이터 (Cold LAD) ---")
    results["V1_both_has_depth_and_depth_cm"] = evaluate(
        "V1 has_depth + depth_cm (현재)", dev_df, cold_meta["folds"], True, True)
    logger.info(f"  V1 (둘 다): med_APE={results['V1_both_has_depth_and_depth_cm']['median']['median_ape']:.4f}")

    results["V2_has_depth_only"] = evaluate(
        "V2 has_depth만", dev_df, cold_meta["folds"], True, False)
    logger.info(f"  V2 (has_depth만): med_APE={results['V2_has_depth_only']['median']['median_ape']:.4f}")

    results["V3_depth_cm_only"] = evaluate(
        "V3 depth_cm만", dev_df, cold_meta["folds"], False, True)
    logger.info(f"  V3 (depth_cm만): med_APE={results['V3_depth_cm_only']['median']['median_ape']:.4f}")

    results["V4_no_depth"] = evaluate(
        "V4 깊이 제거", dev_df, cold_meta["folds"], False, False)
    logger.info(f"  V4 (둘 다 제거): med_APE={results['V4_no_depth']['median']['median_ape']:.4f}")

    # 회화만 (canvas/paper/linen)
    logger.info("\n--- 회화만 (canvas/paper/linen) ---")
    painting_mask = dev_df["support_category"].isin(["canvas", "paper", "linen"])
    logger.info(f"  회화 작품: {painting_mask.sum():,} / 전체 {len(dev_df):,}")

    results["V5_painting_with_depth"] = evaluate(
        "V5 회화 + 깊이 (둘 다)", dev_df, cold_meta["folds"], True, True,
        filter_mask=painting_mask)
    logger.info(f"  V5 (회화 + 깊이): med_APE={results['V5_painting_with_depth']['median']['median_ape']:.4f}")

    results["V6_painting_no_depth"] = evaluate(
        "V6 회화 - 깊이", dev_df, cold_meta["folds"], False, False,
        filter_mask=painting_mask)
    logger.info(f"  V6 (회화 - 깊이): med_APE={results['V6_painting_no_depth']['median']['median_ape']:.4f}")

    print()
    print("=" * 80)
    print("📊 PR11 — 깊이 피처 영향 분리 ablation (Cold LAD 5-fold OOF)")
    print("=" * 80)
    print()
    print("[전체 데이터]")
    print(f"{'Variant':<35} {'med_APE':>9} {'W30':>7} {'vs V1':>10}")
    print("-" * 75)
    v1 = results["V1_both_has_depth_and_depth_cm"]["median"]["median_ape"]
    for key in ["V1_both_has_depth_and_depth_cm", "V2_has_depth_only",
                "V3_depth_cm_only", "V4_no_depth"]:
        r = results[key]
        m = r["median"]
        delta = m["median_ape"] - v1
        sign = "" if abs(delta) < 0.001 else ("✓" if delta < 0 else "↗")
        print(f"{r['name']:<35} {m['median_ape']:>9.4f} {m['within_30pct']:>7.4f} {delta:>+10.4f} {sign}")

    print()
    print("[회화만 (canvas/paper/linen)]")
    print(f"{'Variant':<35} {'med_APE':>9} {'W30':>7} {'vs V5':>10}")
    print("-" * 75)
    v5 = results["V5_painting_with_depth"]["median"]["median_ape"]
    for key in ["V5_painting_with_depth", "V6_painting_no_depth"]:
        r = results[key]
        m = r["median"]
        delta = m["median_ape"] - v5
        print(f"{r['name']:<35} {m['median_ape']:>9.4f} {m['within_30pct']:>7.4f} {delta:>+10.4f}")

    print()
    print("📝 결론:")
    v2_v1 = results["V2_has_depth_only"]["median"]["median_ape"] - v1
    v3_v1 = results["V3_depth_cm_only"]["median"]["median_ape"] - v1
    v4_v1 = results["V4_no_depth"]["median"]["median_ape"] - v1
    v6_v5 = results["V6_painting_no_depth"]["median"]["median_ape"] - v5
    print(f"  V2 (has_depth만): {v2_v1:+.4f} (depth_cm 제거 효과)")
    print(f"  V3 (depth_cm만): {v3_v1:+.4f} (has_depth 제거 효과)")
    print(f"  V4 (둘 다 제거): {v4_v1:+.4f} (둘 다 효과 합)")
    print(f"  회화: V6-V5 = {v6_v5:+.4f} (회화에서 깊이 효과)")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
