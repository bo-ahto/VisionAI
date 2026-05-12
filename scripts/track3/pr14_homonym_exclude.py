"""Track 3 PR14 — TRUE_homonym 38명 작품 제외 cycle (V4-A).

목적: 동명이인 작가 데이터를 학습에서 빼면 다른 작가의 cold-start 예측이 개선되는지 직접 측정.

비교 (paired — 동일 평가 대상):
  V1_full:   전체 학습 + 전체 평가 (기존 baseline)
  V1_subset: 전체 학습 + 38명 제외 평가 (paired 비교 reference)
  V4-A:      38명 제외 학습 + 38명 제외 평가 (cleaner training)

핵심 비교: V1_subset vs V4-A (학습 데이터 구성만 다름, 평가는 동일).

기대:
  V4-A가 V1_subset보다 좋아지면 → 동명이인이 다른 작가 학습 방해 입증 → 운영 채택
  V4-A ≈ V1_subset이면 → 38명 영향 없음 → V1 유지 (작가 보존)
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
from sklearn.model_selection import GroupKFold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1.parquet"
OUT_PATH = REPO / "data" / "track3_pr14_exclude_results.json"

PRICE_COL = "price_krw_unified"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"

BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]
CAT_ALL = BASE_CAT + ["medium_ho_bucket"]
SEED = 42
N_MIN_SECONDARY = 3


def identify_true_homonyms(df):
    """TRUE_homonym 작가 식별 (PR13와 동일 기준)."""
    homonym_artists = []
    for name, group in df.groupby("artist_name_ko"):
        entities = group.groupby("artist_entity_id_raw").agg(
            n=("artist_name_raw", "size"),
            median_price=(PRICE_COL, "median"),
        ).reset_index().sort_values("n", ascending=False)
        if len(entities) <= 1:
            continue
        secondary_multi = entities.iloc[1:][entities.iloc[1:]["n"] >= N_MIN_SECONDARY]
        prices = entities["median_price"].dropna()
        cv = float(prices.std() / max(prices.mean(), 1)) if len(prices) >= 2 else 0.0
        if len(secondary_multi) >= 1 and cv > 0.5:
            homonym_artists.append(name)
    return homonym_artists


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df["artist_name_ko"].map(train_counts).fillna(0))
    return df


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {"median_ape": float(np.median(ape)),
            "mape": float(np.mean(ape)),
            "rmse_log": float(np.sqrt(np.mean(log_resid**2))),
            "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
            "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50))}


def evaluate_paired(df_train_pool, df_eval_pool, name):
    """5-fold GroupKFold OOF — train_pool에서 학습, eval_pool에서 평가.

    fold split은 df_eval_pool 기준 (평가 대상 작가들의 GroupKFold).
    각 fold마다 eval test 작가들을 train_pool에서도 제외해 leakage 차단.
    """
    features = BASE_FEATURES + ["medium_ho_bucket", "artist_works_log", "aspect_ratio"]
    cat_cols = CAT_ALL

    gkf = GroupKFold(n_splits=5)
    fold_results = []
    oof_pred = np.full(len(df_eval_pool), np.nan)
    eval_indices = df_eval_pool.reset_index(drop=True).index.values

    for fold_idx, (_, test_idx) in enumerate(gkf.split(
            df_eval_pool, groups=df_eval_pool["artist_name_ko"])):
        te_df = df_eval_pool.iloc[test_idx]
        te_artists = set(te_df["artist_name_ko"])

        # train_pool에서 test 작가 제외 (leakage 차단)
        tr_df = df_train_pool[~df_train_pool["artist_name_ko"].isin(te_artists)]

        train_counts = tr_df["artist_name_ko"].value_counts().to_dict()
        tr_feat = make_features(tr_df, train_counts)
        te_feat = make_features(te_df, train_counts)

        cat = [c for c in features if c in cat_cols]
        num = [c for c in features if c not in cat_cols]
        preprocess = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
            ("num", StandardScaler(), num),
        ])
        model = Pipeline([("prep", preprocess),
                          ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])
        model.fit(tr_feat[features], tr_feat[TARGET].values)
        pred = model.predict(te_feat[features])

        oof_pred[test_idx] = pred
        m = compute_metrics(te_feat[TARGET].values, pred)
        m["fold"] = fold_idx
        m["n_train_rows"] = int(len(tr_df))
        m["n_train_artists"] = int(tr_df["artist_name_ko"].nunique())
        m["n_test_rows"] = int(len(te_df))
        m["n_test_artists"] = int(te_df["artist_name_ko"].nunique())
        fold_results.append(m)
        logger.info(f"  {name} fold {fold_idx}: med_APE={m['median_ape']:.4f} "
                    f"(train {m['n_train_rows']:,}rows/{m['n_train_artists']} artists, "
                    f"test {m['n_test_rows']:,}/{m['n_test_artists']})")

    sources = df_eval_pool[SOURCE_COL].values
    y_true = df_eval_pool[TARGET].values
    source_breakdown = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() > 0:
            source_breakdown[src] = compute_metrics(y_true[mask], oof_pred[mask])

    return {
        "name": name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "source_breakdown": source_breakdown,
        "oof_pred": oof_pred.tolist(),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR14 — V4-A: TRUE_homonym 38명 제외 cycle")
    logger.info("=" * 70)

    df = pd.read_parquet(DATA_PATH)
    df = df[df["is_outlier"] == 0].reset_index(drop=True)
    logger.info(f"전체: {len(df):,} 작품 / {df['artist_name_ko'].nunique():,} 작가")

    # TRUE_homonym 식별
    homonym_artists = identify_true_homonyms(df)
    homonym_set = set(homonym_artists)
    df_homonym = df[df["artist_name_ko"].isin(homonym_set)]
    df_clean = df[~df["artist_name_ko"].isin(homonym_set)].reset_index(drop=True)
    logger.info(f"\nTRUE_homonym: {len(homonym_artists)} 명 / {len(df_homonym):,} 작품 "
                f"({100*len(df_homonym)/len(df):.2f}%)")
    logger.info(f"제외 후: {len(df_clean):,} 작품 / {df_clean['artist_name_ko'].nunique():,} 작가")

    # ── Eval 1: V1_full (기존 baseline 재현) ──
    logger.info("\n" + "=" * 70)
    logger.info("V1_full: 전체 학습 + 전체 평가 (PR13 V1 baseline 재현)")
    logger.info("=" * 70)
    res_v1_full = evaluate_paired(df, df, "V1_full")

    # ── Eval 2: V1_subset (paired reference — 같은 평가셋으로 비교 가능) ──
    logger.info("\n" + "=" * 70)
    logger.info("V1_subset: 전체 학습 + 38명 제외 평가 (paired reference)")
    logger.info("=" * 70)
    res_v1_sub = evaluate_paired(df, df_clean, "V1_subset")

    # ── Eval 3: V4-A (38명 제외 학습 + 동일 평가) ──
    logger.info("\n" + "=" * 70)
    logger.info("V4-A: 38명 제외 학습 + 38명 제외 평가 (cleaner training)")
    logger.info("=" * 70)
    res_v4a = evaluate_paired(df_clean, df_clean, "V4_A_exclude")

    # ── Paired comparison (V1_subset vs V4-A: 같은 평가셋) ──
    pred_v1 = np.array(res_v1_sub["oof_pred"])
    pred_v4 = np.array(res_v4a["oof_pred"])
    y_true = df_clean[TARGET].values
    valid = ~(np.isnan(pred_v1) | np.isnan(pred_v4))
    ape_v1 = np.abs(np.exp(pred_v1[valid]) - np.exp(y_true[valid])) / np.exp(y_true[valid])
    ape_v4 = np.abs(np.exp(pred_v4[valid]) - np.exp(y_true[valid])) / np.exp(y_true[valid])
    win_rate_v4 = float((ape_v4 < ape_v1).mean())
    median_diff = float(np.median(ape_v4 - ape_v1))

    # 출력
    print()
    print("=" * 80)
    print("📊 PR14 — V4-A 결과 (TRUE_homonym 38명 제외, Cold LAD 5-fold OOF)")
    print("=" * 80)
    print()
    print(f"{'Variant':<35} {'med_APE':>9} {'MAPE':>8} {'W30':>7}")
    print("-" * 64)
    for label, r in [("V1_full (전체 학습+평가)", res_v1_full),
                     ("V1_subset (전체 학습, 제외 평가)", res_v1_sub),
                     ("V4-A (제외 학습+평가)", res_v4a)]:
        m = r["median"]
        print(f"{label:<35} {m['median_ape']:>9.4f} {m['mape']:>8.4f} {m['within_30pct']:>7.4f}")

    print()
    print("=" * 80)
    print("📊 Paired 비교 (V1_subset vs V4-A — 같은 평가셋)")
    print("=" * 80)
    delta_med = res_v4a["median"]["median_ape"] - res_v1_sub["median"]["median_ape"]
    print(f"  med_APE: V1_subset {res_v1_sub['median']['median_ape']:.4f} → "
          f"V4-A {res_v4a['median']['median_ape']:.4f}  ({delta_med:+.4f})")
    print(f"  작품 단위 win-rate (V4-A < V1_subset): {win_rate_v4:.4f}")
    print(f"  작품 단위 APE 차이 median: {median_diff:+.4f}")

    print()
    print("[Source breakdown — V1_subset vs V4-A]")
    print(f"  {'Source':<8} {'V1_sub':>8} {'V4-A':>8} {'Δ':>9}")
    for src in ["artsy", "saatchi", "artue"]:
        v1s = res_v1_sub["source_breakdown"].get(src, {})
        v4s = res_v4a["source_breakdown"].get(src, {})
        if v1s and v4s:
            d = v4s["median_ape"] - v1s["median_ape"]
            print(f"  {src:<8} {v1s['median_ape']:>8.4f} {v4s['median_ape']:>8.4f} {d:>+9.4f}")

    output = {
        "homonym_artists": homonym_artists,
        "n_homonym": len(homonym_artists),
        "n_works_excluded": int(len(df_homonym)),
        "pct_works_excluded": float(100*len(df_homonym)/len(df)),
        "V1_full": {k: v for k, v in res_v1_full.items() if k != "oof_pred"},
        "V1_subset": {k: v for k, v in res_v1_sub.items() if k != "oof_pred"},
        "V4_A": {k: v for k, v in res_v4a.items() if k != "oof_pred"},
        "paired": {
            "delta_median_ape": float(delta_med),
            "win_rate_v4a": win_rate_v4,
            "median_ape_diff": median_diff,
        },
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
