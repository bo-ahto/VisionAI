"""Track 3 PR26 (F6) — Frozen Cold Benchmark 구축.

실험 목적 (Codex 1순위 인프라 권고):
  Mini hold-out cold 평가의 seed별 variance (std 0.23 noisy)를 제거.
  Frozen benchmark 1회 고정 → 향후 실험 false positive 감소.

설계:
  - release_split train (1,966 작가)에서 cold artist 100명 통째 hold-out
  - Stratification 4축 (Codex 권고):
    1. works_count regime: low(≤2) / mid(3-10) / high(>10) — 50/30/20 비율
    2. price tertile (작가 median price): low/mid/high — 각 strata 안에서 균등
    3. medium dominant: 결과 분포가 train 전체와 ±10% 이내인지 검증
    4. is_3d_share (작가 평균 has_depth): 결과 분포 통제 검증
  - 단일 SEED=42 (seed-free 효과)
  - 분포 검증 미통과 시 SEED 변경 후 재시도 (최대 10회)

산출물:
  data/track3_splits/frozen_mini_cold_artists.json - cold benchmark 작가 list + 통계
  data/track3_splits/frozen_mini_cold.csv - cold benchmark 작품 (cold_mini)
  data/track3_splits/frozen_mini_train.csv - mini_train (나머지 작가)
  data/track3_pr26_baseline_cache.json - V0 baseline 예측 (ape_array 포함, paired 비교용)
  scripts/track3/_frozen_loader.py - 향후 실험에서 import해서 사용할 loader
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
FROZEN_DIR = REPO / "data" / "track3_splits"
BASELINE_OUT = REPO / "data" / "track3_pr26_baseline_cache.json"
LOADER_OUT = REPO / "scripts" / "track3" / "_frozen_loader.py"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"
N_COLD = 100
DIST_TOLERANCE = 0.10  # medium / 3D 분포 차이 허용 (절대값)

# V0 baseline features (현 운영 v1.2)
COLD_FEATS = ["medium_category", "support_category", "orientation",
               "depth_cm", "width_cm", "height_cm", "log_area", "estimated_ho",
               "medium_ho_bucket", "aspect_ratio", "artist_works_log"]
COLD_CAT = ["medium_category", "support_category", "orientation", "medium_ho_bucket"]
WARM_FEATS = COLD_FEATS + [ARTIST_COL]
WARM_CAT = COLD_CAT + [ARTIST_COL]

LGB_PARAMS = {
    "objective": "regression", "metric": "rmse",
    "learning_rate": 0.04, "num_leaves": 198, "min_data_in_leaf": 75,
    "feature_fraction": 0.987, "bagging_fraction": 0.978, "bagging_freq": 5,
    "reg_alpha": 0.36, "reg_lambda": 4.75, "verbose": -1,
    "deterministic": True, "num_threads": 1,
    "seed": 42, "bagging_seed": 42, "feature_fraction_seed": 42,
    "data_random_seed": 42, "drop_seed": 42, "objective_seed": 42,
}


def artist_stats(train_df):
    """작가별 통계: count, median price, is_3d_share, dominant medium."""
    stats = train_df.groupby(ARTIST_COL).agg(
        count=(ARTIST_COL, "size"),
        median_price=(PRICE_COL, "median"),
        is_3d_share=("depth_cm", lambda x: (x > 0).mean()),
    ).reset_index()
    # dominant medium
    dom_medium = (train_df.groupby([ARTIST_COL, "medium_category"]).size()
                  .reset_index(name="n").sort_values(["artist_name_ko", "n"], ascending=[True, False]))
    dom_medium = dom_medium.drop_duplicates(ARTIST_COL).rename(columns={"medium_category": "dom_medium"})
    stats = stats.merge(dom_medium[[ARTIST_COL, "dom_medium"]], on=ARTIST_COL)
    return stats


def stratified_sample(stats, train_df, seed):
    """works_count × price_tertile 9 strata quota sampling."""
    rng = np.random.default_rng(seed)
    # count regime
    stats["count_regime"] = pd.cut(stats["count"], bins=[-1, 2, 10, 10_000],
                                     labels=["low", "mid", "high"])
    # price tertile (전체 기준)
    stats["price_tertile"] = pd.qcut(stats["median_price"], q=3, labels=["low", "mid", "high"])

    # 50/30/20 비율 (low/mid/high count) × 33/33/33 (price)
    count_quota = {"low": 50, "mid": 30, "high": 20}
    cold_artists = []
    for regime, n in count_quota.items():
        sub = stats[stats["count_regime"] == regime]
        # price tertile 균등 (n/3 each)
        per_tertile = n // 3
        remainder = n - per_tertile * 3
        for i, tertile in enumerate(["low", "mid", "high"]):
            target_n = per_tertile + (1 if i < remainder else 0)
            cand = sub[sub["price_tertile"] == tertile]
            if len(cand) < target_n:
                logger.warning(f"  ({regime}, {tertile}) strata 부족: {len(cand)} < {target_n}, 모두 선택")
                target_n = len(cand)
            picks = rng.choice(cand[ARTIST_COL].values, size=target_n, replace=False)
            cold_artists.extend(picks.tolist())
    return cold_artists


def check_distribution(train_df, cold_artists, mini_train_df):
    """Cold benchmark 분포가 train과 유사한지 검증.
    Returns (passed: bool, deviations: dict)."""
    cold_df = train_df[train_df[ARTIST_COL].isin(cold_artists)]
    deviations = {}
    # Medium 분포
    train_med = train_df["medium_category"].value_counts(normalize=True)
    cold_med = cold_df["medium_category"].value_counts(normalize=True)
    med_dev = {m: abs(cold_med.get(m, 0) - train_med.get(m, 0))
               for m in train_med.index}
    deviations["medium"] = med_dev
    # 3D share
    train_3d = (train_df["depth_cm"] > 0).mean()
    cold_3d = (cold_df["depth_cm"] > 0).mean()
    deviations["is_3d_share"] = abs(cold_3d - train_3d)
    # Price log-scale ratio
    train_log_p = np.log1p(train_df[PRICE_COL]).mean()
    cold_log_p = np.log1p(cold_df[PRICE_COL]).mean()
    deviations["mean_log_price"] = abs(cold_log_p - train_log_p)

    # 판정: medium 최대 편차 + 3D 편차 < tolerance
    max_med_dev = max(med_dev.values()) if med_dev else 0
    passed = (max_med_dev <= DIST_TOLERANCE and
              deviations["is_3d_share"] <= DIST_TOLERANCE and
              deviations["mean_log_price"] <= 0.5)
    return passed, deviations


def make_features(df, train_counts):
    df = df.copy()
    df["ho_bucket"] = pd.cut(df["estimated_ho"], bins=[-0.1, 5, 20, 50, 200],
                              labels=["0-5", "5-20", "20-50", "50+"]).astype(str)
    df["medium_ho_bucket"] = df["medium_category"].astype(str) + "_" + df["ho_bucket"]
    df["aspect_ratio"] = np.log(df["width_cm"] / df["height_cm"].replace(0, 1))
    df["artist_works_log"] = np.log1p(df[ARTIST_COL].map(train_counts).fillna(0))
    return df


def build_lad(features, cat_cols):
    cat = [c for c in features if c in cat_cols]
    num = [c for c in features if c not in cat_cols]
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", max_categories=100), cat),
        ("num", StandardScaler(), num),
    ])
    return Pipeline([("prep", pre),
                     ("est", QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0))])


def to_cat(df, features, cat_cols):
    df = df[features].copy()
    for c in cat_cols:
        if c in df.columns: df[c] = df[c].astype("category")
    return df


def train_lgb(df_train):
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(df_train))
    cut = int(len(df_train) * 0.1)
    X_tr = to_cat(df_train.iloc[perm[cut:]], WARM_FEATS, WARM_CAT)
    X_va = to_cat(df_train.iloc[perm[:cut]], WARM_FEATS, WARM_CAT)
    y_tr = df_train.iloc[perm[cut:]][TARGET].values
    y_va = df_train.iloc[perm[:cut]][TARGET].values
    tr_set = lgb.Dataset(X_tr, y_tr, categorical_feature=WARM_CAT)
    val_set = lgb.Dataset(X_va, y_va, categorical_feature=WARM_CAT, reference=tr_set)
    return lgb.train(LGB_PARAMS, tr_set, num_boost_round=2000, valid_sets=[val_set],
                     callbacks=[lgb.early_stopping(30, verbose=False)])


def compute_baseline_metrics(y_true_ln, y_pred_ln):
    y_true = np.exp(y_true_ln); y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    return {
        "n": int(len(y_true)),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "within_30pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred/y_true - 1) < 0.50)),
        "p95_ape": float(np.percentile(ape, 95)),
        "p99_ape": float(np.percentile(ape, 99)),
        "max_ape": float(np.max(ape)),
        "ape_array": ape.tolist(),
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR26 (F6) — Frozen Cold Benchmark 구축")
    logger.info("=" * 70)

    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT / "track3_train.csv")
    logger.info(f"train: {len(train):,} rows / {train[ARTIST_COL].nunique():,} artists")

    stats = artist_stats(train)
    logger.info(f"\n작가 통계: count_regime 분포 = "
                f"low(≤2): {(stats['count']<=2).sum()}, "
                f"mid(3-10): {((stats['count']>=3)&(stats['count']<=10)).sum()}, "
                f"high(>10): {(stats['count']>10).sum()}")

    # Stratified sampling — 분포 검증 미통과 시 seed 변경
    for try_seed in [42, 1, 2, 3, 7, 11, 17, 23, 31, 47]:
        logger.info(f"\n시도 seed={try_seed}")
        cold_artists = stratified_sample(stats, train, try_seed)
        cold_df = train[train[ARTIST_COL].isin(cold_artists)]
        mini_train_df = train[~train[ARTIST_COL].isin(cold_artists)]
        passed, dev = check_distribution(train, cold_artists, mini_train_df)
        logger.info(f"  cold_artists={len(cold_artists)}, cold_rows={len(cold_df)}, "
                    f"mini_train_rows={len(mini_train_df)}")
        max_med_dev = max(dev["medium"].values()) if dev["medium"] else 0
        logger.info(f"  분포 편차: 3D={dev['is_3d_share']:.4f}, "
                    f"max_medium={max_med_dev:.4f}, log_price={dev['mean_log_price']:.4f}")
        if passed:
            logger.info(f"  ✅ 분포 검증 통과 (seed={try_seed})")
            FROZEN_SEED = try_seed
            break
    else:
        raise RuntimeError("10 seeds 시도 후도 분포 검증 미통과")

    # Save frozen split
    frozen_meta = {
        "frozen_seed": FROZEN_SEED,
        "n_cold_artists": len(cold_artists),
        "n_cold_rows": int(len(cold_df)),
        "n_mini_train_artists": int(mini_train_df[ARTIST_COL].nunique()),
        "n_mini_train_rows": int(len(mini_train_df)),
        "distribution_check": {
            "is_3d_share_deviation": dev["is_3d_share"],
            "max_medium_deviation": max(dev["medium"].values()) if dev["medium"] else 0,
            "mean_log_price_deviation": dev["mean_log_price"],
            "tolerance": DIST_TOLERANCE,
            "passed": True,
        },
        "stratification": "works_count × price_tertile (50/30/20 × 33/33/34)",
        "cold_artists": cold_artists,
        "created": "PR26 (F6) frozen cold benchmark",
        "usage": "load via scripts/track3/_frozen_loader.py",
    }
    (FROZEN_DIR / "frozen_mini_cold_artists.json").write_text(
        json.dumps(frozen_meta, indent=2, ensure_ascii=False))
    cold_df.to_csv(FROZEN_DIR / "frozen_mini_cold.csv", index=False, encoding="utf-8-sig")
    mini_train_df.to_csv(FROZEN_DIR / "frozen_mini_train.csv", index=False, encoding="utf-8-sig")
    logger.info(f"\n✅ Frozen split 저장: {FROZEN_DIR}")

    # ── V0 baseline 학습 + 예측 (paired baseline 캐싱) ──
    logger.info("\n[V0 baseline] Cold LAD + Warm LGB 학습...")
    counts = mini_train_df[ARTIST_COL].value_counts().to_dict()
    tr = make_features(mini_train_df, counts)
    cm = make_features(cold_df, counts)

    # Cold LAD
    lad = build_lad(COLD_FEATS, COLD_CAT)
    lad.fit(tr[COLD_FEATS], tr[TARGET].values)
    cold_pred = lad.predict(cm[COLD_FEATS])
    cold_baseline = compute_baseline_metrics(cold_df[TARGET].values, cold_pred)

    # Warm LGB는 frozen cold benchmark에 사용 안 함 (cold artist는 unseen이라 Warm 무의미).
    # 다만 향후 paired 비교용 reference로 cold만 캐싱.
    logger.info(f"  Cold V0 baseline: med_APE={cold_baseline['median_ape']:.4f}, "
                f"W30={cold_baseline['within_30pct']:.4f}")

    # Save baseline cache
    baseline_cache = {
        "frozen_seed": FROZEN_SEED,
        "frozen_metadata": "data/track3_splits/frozen_mini_cold_artists.json",
        "v0_features_used": {"cold": COLD_FEATS, "categorical": COLD_CAT},
        "cold_baseline": cold_baseline,
    }
    BASELINE_OUT.write_text(json.dumps(baseline_cache, indent=2, ensure_ascii=False))
    logger.info(f"✅ V0 baseline cache: {BASELINE_OUT}")

    # ── Frozen loader (향후 실험용) ──
    loader_code = f'''"""Frozen Cold Benchmark loader (F6 PR26 산출물).

향후 Track 3 실험에서 사용 — 단일 import로 frozen cold + mini_train + V0 baseline 로드.

Usage:
    from scripts.track3._frozen_loader import load_frozen_benchmark

    mini_train, cold_mini, baseline = load_frozen_benchmark()
    # mini_train: pd.DataFrame, 학습용
    # cold_mini: pd.DataFrame, frozen cold test
    # baseline['ape_array']: V0 baseline 예측 APE (paired 비교용)
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT_DIR = REPO / "data" / "track3_splits"
BASELINE_PATH = REPO / "data" / "track3_pr26_baseline_cache.json"


def load_frozen_benchmark():
    """Returns (mini_train, cold_mini, baseline_dict)."""
    mini_train = pd.read_csv(SPLIT_DIR / "frozen_mini_train.csv")
    cold_mini = pd.read_csv(SPLIT_DIR / "frozen_mini_cold.csv")
    baseline = json.loads(BASELINE_PATH.read_text())
    return mini_train, cold_mini, baseline


if __name__ == "__main__":
    mt, cm, bl = load_frozen_benchmark()
    print(f"mini_train: {{len(mt):,}} rows / {{mt['artist_name_ko'].nunique():,}} artists")
    print(f"cold_mini : {{len(cm):,}} rows / {{cm['artist_name_ko'].nunique():,}} artists")
    print(f"V0 cold baseline med_APE: {{bl['cold_baseline']['median_ape']:.4f}}")
'''
    LOADER_OUT.write_text(loader_code)
    logger.info(f"✅ Frozen loader: {LOADER_OUT}")

    # ── 분포 비교 출력 ──
    print()
    print("=" * 80)
    print("📊 F6 — Frozen Cold Benchmark 구축 완료")
    print("=" * 80)
    print(f"\nFrozen split (SEED={FROZEN_SEED}):")
    print(f"  cold benchmark: {len(cold_df):,} rows / {len(cold_artists)} artists")
    print(f"  mini_train:     {len(mini_train_df):,} rows / {mini_train_df[ARTIST_COL].nunique():,} artists")
    print(f"\n분포 검증:")
    print(f"  3D share deviation: {dev['is_3d_share']:.4f} (tolerance {DIST_TOLERANCE})")
    print(f"  Max medium deviation: {max(dev['medium'].values()):.4f}")
    print(f"  Mean log-price deviation: {dev['mean_log_price']:.4f}")
    print(f"\nV0 baseline (Cold LAD):")
    print(f"  median_ape: {cold_baseline['median_ape']:.4f}")
    print(f"  within_30pct: {cold_baseline['within_30pct']:.4f}")
    print(f"  max_ape: {cold_baseline['max_ape']:.4f}")
    print(f"\n📌 향후 실험 사용: from scripts.track3._frozen_loader import load_frozen_benchmark")


if __name__ == "__main__":
    main()
