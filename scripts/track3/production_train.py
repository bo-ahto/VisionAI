"""Track 3 Production — 최종 모델 학습 + artifact 저장.

PR7 ALL features 기반 final 모델:
  Cold: LAD + (medium/support/has_depth/log_area/estimated_ho/orientation
              + source/medium_ho_bucket/artist_works_log/aspect_ratio)
  Warm: Tuned LGB + Cold features + artist_name_ko

Artifacts:
  data/production/track3_cold_lad.joblib
  data/production/track3_warm_lgb.joblib
  data/production/track3_metadata.json (학습 통계 + artist counts + 운영 정보)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
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
PROD_DIR = REPO / "data" / "production"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
BASE_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation"]
BASE_CAT = ["medium_category", "support_category", "orientation"]
ALL_FEATURES = BASE_FEATURES + ["source_platform", "medium_ho_bucket",
                                  "artist_works_log", "aspect_ratio"]
ALL_CAT = BASE_CAT + ["source_platform", "medium_ho_bucket"]
WARM_FEATURES = ALL_FEATURES + [ARTIST_COL]
WARM_CAT = ALL_CAT + [ARTIST_COL]
SEED = 42


def make_features(df, artist_counts):
    """PR7 feature engineering."""
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(artist_counts).fillna(0))
    return df


def build_lad():
    cat = [c for c in ALL_FEATURES if c in ALL_CAT]
    num = [c for c in ALL_FEATURES if c not in ALL_CAT]
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


def train_warm_lgb(df, artist_counts):
    """PR1 tuned params + PR7 features."""
    df_feat = make_features(df, artist_counts)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(df_feat))
    cut = int(len(df_feat) * 0.1)
    va_idx = perm[:cut]; tr_idx = perm[cut:]

    X_tr = to_cat(df_feat.iloc[tr_idx], WARM_FEATURES, WARM_CAT)
    X_va = to_cat(df_feat.iloc[va_idx], WARM_FEATURES, WARM_CAT)
    y_tr = df_feat.iloc[tr_idx][TARGET].values
    y_va = df_feat.iloc[va_idx][TARGET].values

    params = {"objective": "regression", "metric": "rmse",
              "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
              "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
              "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1, "seed": SEED}
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=WARM_CAT)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=WARM_CAT, reference=tr_set)
    return lgb.train(params, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def main():
    logger.info("=" * 70)
    logger.info("Track 3 Production — Final model training")
    logger.info("=" * 70)

    df = pd.read_csv(DATA_PATH)
    df = df[df["is_outlier"] == 0].reset_index(drop=True)
    logger.info(f"Training data: {len(df):,} rows / {df[ARTIST_COL].nunique():,} artists")

    PROD_DIR.mkdir(parents=True, exist_ok=True)

    # Artist counts (전체 train 기준)
    artist_counts = df[ARTIST_COL].value_counts().to_dict()

    # Cold LAD 학습
    logger.info("\n[Cold] LAD + ALL features 학습...")
    cold_df = make_features(df, artist_counts)
    cold_model = build_lad()
    cold_model.fit(cold_df[ALL_FEATURES], cold_df[TARGET].values)
    cold_path = PROD_DIR / "track3_cold_lad.joblib"
    joblib.dump(cold_model, cold_path)
    logger.info(f"  ✓ Saved: {cold_path}")

    # Warm LGB 학습
    logger.info("\n[Warm] Tuned LightGBM + ALL features 학습...")
    warm_model = train_warm_lgb(df, artist_counts)
    warm_path = PROD_DIR / "track3_warm_lgb.txt"
    warm_model.save_model(str(warm_path))
    logger.info(f"  ✓ Saved: {warm_path}")

    # Metadata
    metadata = {
        "version": "v1.0",
        "training_data": "track3_unified_v1_train.csv",
        "n_rows": int(len(df)),
        "n_artists": int(df[ARTIST_COL].nunique()),
        "target": TARGET,
        "models": {
            "cold": {
                "type": "LAD (Quantile q=0.5)",
                "features": ALL_FEATURES,
                "categorical": ALL_CAT,
                "artifact": "track3_cold_lad.joblib",
                "expected_med_ape": 0.391,
                "expected_w30": 0.373,
            },
            "warm": {
                "type": "LightGBM (Tuned)",
                "features": WARM_FEATURES,
                "categorical": WARM_CAT,
                "artifact": "track3_warm_lgb.txt",
                "expected_med_ape": 0.104,
                "expected_w30": 0.776,
                "hyperparams": {
                    "learning_rate": 0.04, "num_leaves": 198,
                    "min_data_in_leaf": 75, "feature_fraction": 0.987,
                    "bagging_fraction": 0.978, "reg_alpha": 0.36, "reg_lambda": 4.75,
                },
            },
        },
        "routing": {
            "rule": "train_count >= 1 → Warm; else → Cold",
            "rare_artist_blend": "1건 작가는 Warm 100% (PR2), 2건도 Warm 100%",
        },
        "high_price_caveat": {
            ">100M_cold": "예측 불가 (med_APE 0.98). 비공개 권장",
            ">100M_warm": "Warm 2-stage 별도 모델 (med_APE 0.04)",
        },
        "source_bias_caveat": {
            "artsy_markup": "+45.5% vs Saatchi (동일 특성). source feature로 흡수.",
            "operational_note": "source 정보 입력 필수",
        },
        "artist_counts_count": int(len(artist_counts)),
        "artist_counts_path": "track3_artist_counts.json",
        "feature_engineering": {
            "ho_bucket": "estimated_ho를 [0-5, 5-20, 20-50, 50+]로 분류",
            "medium_ho_bucket": "medium × ho_bucket interaction",
            "aspect_ratio": "log(width / height)",
            "artist_works_log": "log1p(train fold artist count)",
        },
        "limitations": [
            "listing-price prediction (시장가치 예측 아님)",
            "시간 split 없음 (temporal validation 불가)",
            ">100M Cold 사실상 예측 불가",
            "Source 정보 없으면 ±20-45% 오차 가능",
        ],
    }
    metadata_path = PROD_DIR / "track3_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    logger.info(f"  ✓ Saved: {metadata_path}")

    # Artist counts (for inference)
    counts_path = PROD_DIR / "track3_artist_counts.json"
    counts_path.write_text(json.dumps(artist_counts, indent=2, ensure_ascii=False))
    logger.info(f"  ✓ Saved: {counts_path}")

    print()
    print("=" * 70)
    print("✅ Production Models Saved")
    print("=" * 70)
    print(f"  Cold LAD:          {cold_path.name}")
    print(f"  Warm LGB:          {warm_path.name}")
    print(f"  Metadata:          {metadata_path.name}")
    print(f"  Artist counts:     {counts_path.name}")
    print()
    print(f"Expected performance:")
    print(f"  Cold (unseen):     med_APE 0.391, W30 0.37")
    print(f"  Warm (≥1건):       med_APE 0.104, W30 0.78")


if __name__ == "__main__":
    main()
