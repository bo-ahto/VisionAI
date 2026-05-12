"""Track 3 PR16f — Production v1.2 모델을 release_split v3 test로 평가 + metadata 갱신.

평가:
  Cold LAD on test_cold (3,561 rows / 200 unseen 작가)
  Warm Tuned LGB on test_warm (1,717 rows / 1,717 학습된 작가)

metric:
  median APE / MAPE / RMSE(log) / Within-30% / Within-50%
  + Cold per-source / per-medium breakdown
  + Warm per-source

저장:
  data/production/track3_metadata.json — expected_med_ape / expected_w30 / eval_full 갱신
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
PROD = REPO / "data" / "production"
UNIFIED_V3 = REPO / "data" / "track3_unified_v3.parquet"  # source 정보 lookup용

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"

ALL_FEATURES = ["medium_category", "support_category", "depth_cm",
                "log_area", "estimated_ho", "orientation",
                "medium_ho_bucket", "artist_works_log", "aspect_ratio"]
ALL_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
WARM_FEATURES = ALL_FEATURES + [ARTIST_COL]
WARM_CAT = ALL_CAT + [ARTIST_COL]


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def compute_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean((y_pred_ln - y_true_ln)**2))),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR16f — Production v1.2 평가 (release_split v3 test)")
    logger.info("=" * 70)

    # 데이터 로드
    train = pd.read_csv(SPLIT / "track3_train.csv")
    test_warm = pd.read_csv(SPLIT / "track3_test_warm.csv")
    test_cold = pd.read_csv(SPLIT / "track3_test_cold.csv")
    logger.info(f"train {len(train):,} / test_warm {len(test_warm):,} / test_cold {len(test_cold):,}")

    # source 정보 lookup (test는 학습 셋이 아니라 metric breakdown 용도)
    unified = pd.read_parquet(UNIFIED_V3)
    src_map = unified.set_index(["artist_name_ko", "ln_price_krw_unified",
                                  "width_cm", "height_cm"])[SOURCE_COL].to_dict()
    def lookup_source(df):
        keys = list(zip(df[ARTIST_COL], df[TARGET], df["width_cm"], df["height_cm"]))
        return pd.Series([src_map.get(k) for k in keys])
    test_warm["_source"] = lookup_source(test_warm).values
    test_cold["_source"] = lookup_source(test_cold).values
    logger.info(f"source lookup coverage — warm {test_warm['_source'].notna().mean():.1%}, "
                f"cold {test_cold['_source'].notna().mean():.1%}")

    # 모델 로드
    cold_model = joblib.load(PROD / "track3_cold_lad.joblib")
    warm_model = lgb.Booster(model_file=str(PROD / "track3_warm_lgb.txt"))

    train_counts = train[ARTIST_COL].value_counts().to_dict()

    # ─── Cold 평가 ───
    cold_feat = make_features(test_cold, train_counts)
    cold_pred = cold_model.predict(cold_feat[ALL_FEATURES])
    cold_overall = compute_metrics(test_cold[TARGET].values, cold_pred)
    logger.info(f"\n[Cold] {cold_overall}")

    # per-source / per-medium breakdown
    cold_by_source = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = test_cold["_source"].values == src
        if mask.sum() > 0:
            cold_by_source[src] = compute_metrics(
                test_cold[TARGET].values[mask], cold_pred[mask])
    cold_by_medium = {}
    for med in test_cold["medium_category"].unique():
        mask = (test_cold["medium_category"] == med).values
        if mask.sum() >= 20:
            cold_by_medium[str(med)] = compute_metrics(
                test_cold[TARGET].values[mask], cold_pred[mask])

    # ─── Warm 평가 ───
    warm_feat = make_features(test_warm, train_counts)
    X_warm = to_cat(warm_feat, WARM_FEATURES, WARM_CAT)
    warm_pred = warm_model.predict(X_warm)
    warm_overall = compute_metrics(test_warm[TARGET].values, warm_pred)
    logger.info(f"\n[Warm] {warm_overall}")

    warm_by_source = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = test_warm["_source"].values == src
        if mask.sum() > 0:
            warm_by_source[src] = compute_metrics(
                test_warm[TARGET].values[mask], warm_pred[mask])

    # ─── 출력 ───
    print()
    print("=" * 80)
    print("📊 Production v1.2 — release_split v3 evaluation")
    print("=" * 80)
    print()
    print(f"{'Model':<8} {'n':>6} {'med_APE':>9} {'MAPE':>9} {'RMSE_log':>9} {'W30':>7} {'W50':>7}")
    print("-" * 60)
    for name, m in [("Cold", cold_overall), ("Warm", warm_overall)]:
        print(f"{name:<8} {m['n']:>6,} {m['median_ape']:>9.4f} {m['mape']:>9.4f} "
              f"{m['rmse_log']:>9.4f} {m['within_30pct']:>7.4f} {m['within_50pct']:>7.4f}")

    print()
    print("[Cold per-source]")
    for src, m in cold_by_source.items():
        print(f"  {src:<8} n={m['n']:>4,} med_APE={m['median_ape']:.4f} W30={m['within_30pct']:.4f}")

    print()
    print("[Warm per-source]")
    for src, m in warm_by_source.items():
        print(f"  {src:<8} n={m['n']:>4,} med_APE={m['median_ape']:.4f} W30={m['within_30pct']:.4f}")

    print()
    print("[Cold per-medium] (n≥20만 출력)")
    for med, m in sorted(cold_by_medium.items(), key=lambda x: -x[1]["n"]):
        print(f"  {med:<12} n={m['n']:>4,} med_APE={m['median_ape']:.4f} W30={m['within_30pct']:.4f}")

    # ─── Metadata 갱신 ───
    meta_path = PROD / "track3_metadata.json"
    meta = json.loads(meta_path.read_text())
    meta["models"]["cold"]["expected_med_ape"] = round(cold_overall["median_ape"], 4)
    meta["models"]["cold"]["expected_w30"] = round(cold_overall["within_30pct"], 4)
    meta["models"]["cold"]["eval_full"] = cold_overall
    meta["models"]["cold"]["eval_by_source"] = cold_by_source
    meta["models"]["cold"]["eval_by_medium"] = cold_by_medium
    meta["models"]["warm"]["expected_med_ape"] = round(warm_overall["median_ape"], 4)
    meta["models"]["warm"]["expected_w30"] = round(warm_overall["within_30pct"], 4)
    meta["models"]["warm"]["eval_full"] = warm_overall
    meta["models"]["warm"]["eval_by_source"] = warm_by_source
    meta["eval_protocol"] = "release_split v3 test sets (test_cold 3,561 + test_warm 1,717)"
    meta["eval_date"] = "2026-05-12"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Metadata updated: {meta_path}")


if __name__ == "__main__":
    main()
