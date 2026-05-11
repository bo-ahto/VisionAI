"""Depth feature ablation 실험 — XGBoost regressor.

목적: `has_depth` + `depth_cm` 피처가 가격 예측에 미치는 영향 측정.
재현 방법:
    cd VisionAI && PYTHONPATH=src python3 scripts/track3/experiments/depth_ablation_xgb.py

데이터:
    data/track3_unified_v1_train.csv (40,137 rows, is_outlier=0만)

비교 변형:
    A. With depth     — has_depth + depth_cm 포함 (8 features)
    B. Without depth  — has_depth + depth_cm 제외 (6 features)

평가 metric:
    - MAPE          mean(|y - ŷ| / y) — 평균 비율 오차
    - median APE    median(|y - ŷ| / y) — 중앙값 비율 오차 (outlier robust)
    - RMSE (log)    log 공간 RMSE
    - Within-30%    |ŷ/y - 1| < 0.3 비율 (실용 정확도)
    - Within-50%    |ŷ/y - 1| < 0.5 비율

Split: random 80/20 (warm-start scenario, multi-seed N=5로 평균/std)

Output:
    - 콘솔 결과 표 + seed간 일관성 요약 (N=5 sign test)
    - data/depth_ablation_results.json (재현용)

주의:
    - random split이라 singleton 작가는 test에 unseen으로 섞일 수 있음 → "mostly warm-start"
    - 진짜 cold-start (unseen artist) 평가는 GroupShuffleSplit by artist_name_ko 별도 필요
    - has_depth와 depth_cm은 build 단계에서 depth_cm.fillna(0) + has_depth=(depth_cm>0) 강제 →
      사실상 thresholded copy 관계 (독립 기여 분리하려면 4-way ablation 필요)

Dependencies (pip):
    pandas, numpy, scikit-learn, xgboost (>=2.0)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import xgboost as xgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── 설정 ───
REPO = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
OUT_PATH = REPO / "data" / "depth_ablation_results.json"

# Feature 설정 (★ 학습 input)
COMMON_FEATURES = [
    "artist_name_ko",   # categorical (high cardinality)
    "medium_category",  # categorical (8)
    "support_category", # categorical (7)
    "log_area",         # continuous
    "estimated_ho",     # continuous (한국 호수)
    "orientation",      # categorical (4)
]
DEPTH_FEATURES = ["has_depth", "depth_cm"]  # 이 두 개가 실험 변수
TARGET = "ln_price_krw_unified"

CATEGORICAL_COLS = ["artist_name_ko", "medium_category", "support_category", "orientation"]

# XGBoost 하이퍼파라미터 (기본 — 실험 비교용)
XGB_PARAMS = {
    "objective": "reg:squarederror",
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 8,
    "min_child_weight": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "enable_categorical": True,  # XGBoost 2.0+ native categorical
    "early_stopping_rounds": 30,
}

SEEDS = [42, 123, 456, 789, 1024]  # multi-seed N=5
TEST_SIZE = 0.2


def load_data() -> pd.DataFrame:
    """학습 데이터 로드 + categorical dtype 변환."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    for col in CATEGORICAL_COLS:
        df[col] = df[col].astype("category")
    logger.info(f"Loaded: {len(df):,} rows / {len(df.columns)} cols")
    return df


def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    """log 공간 예측 → 원본 가격 복원 + metric 계산."""
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)

    ape = np.abs(y_pred - y_true) / y_true  # absolute percentage error
    log_resid = y_pred_ln - y_true_ln

    return {
        "mape": float(np.mean(ape)),
        "median_ape": float(np.median(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.50)),
    }


def run_one_seed(df: pd.DataFrame, features: list[str], seed: int) -> dict:
    """단일 seed로 train/test split + XGBoost 학습 + 평가."""
    X = df[features]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=seed
    )
    # validation set for early stopping (train 안에서 분리)
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=seed
    )

    model = xgb.XGBRegressor(random_state=seed, **XGB_PARAMS)
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)

    y_pred = model.predict(X_test)
    metrics = compute_metrics(y_test.values, y_pred)
    metrics["n_train"] = len(X_train)
    metrics["n_test"] = len(X_test)
    metrics["best_iter"] = int(model.best_iteration)
    return metrics


def run_variant(df: pd.DataFrame, variant_name: str, features: list[str]) -> dict:
    """variant를 N=5 seed로 학습 + 평균/std 집계."""
    logger.info(f"\n{'='*70}\nVariant {variant_name}: {len(features)} features")
    logger.info(f"  Features: {features}")
    logger.info(f"{'='*70}")

    seed_results = []
    for seed in SEEDS:
        m = run_one_seed(df, features, seed)
        seed_results.append(m)
        logger.info(
            f"  seed={seed} | MAPE={m['mape']:.3f} | median_APE={m['median_ape']:.3f} | "
            f"RMSE_log={m['rmse_log']:.3f} | W30={m['within_30pct']:.3f} | "
            f"W50={m['within_50pct']:.3f} | best_iter={m['best_iter']}"
        )

    agg = {
        "variant": variant_name,
        "n_features": len(features),
        "features": features,
        "seeds": SEEDS,
        "per_seed": seed_results,
        "mean": {
            k: float(np.mean([r[k] for r in seed_results]))
            for k in ["mape", "median_ape", "rmse_log", "within_30pct", "within_50pct"]
        },
        "std": {
            k: float(np.std([r[k] for r in seed_results]))
            for k in ["mape", "median_ape", "rmse_log", "within_30pct", "within_50pct"]
        },
    }
    return agg


def compare_variants(result_A: dict, result_B: dict) -> dict:
    """A (with depth) vs B (without depth) 비교 + paired diff.

    Metric 방향성 (lower_is_better):
      - mape / median_ape / rmse_log: 낮을수록 좋음 → A가 좋으면 diff<0
      - within_30pct / within_50pct: 높을수록 좋음 → A가 좋으면 diff>0
    `better_seeds` = A가 B보다 좋은 seed 수 (metric 방향성 반영).
    """
    LOWER_IS_BETTER = {
        "mape": True, "median_ape": True, "rmse_log": True,
        "within_30pct": False, "within_50pct": False,
    }
    diffs = {}
    for k, lower_better in LOWER_IS_BETTER.items():
        # seed-paired diff (A - B)
        paired = [a[k] - b[k] for a, b in zip(result_A["per_seed"], result_B["per_seed"])]
        # A가 더 좋은 seed 수 (metric 방향성 반영)
        if lower_better:
            n_better = sum(1 for d in paired if d < 0)
        else:
            n_better = sum(1 for d in paired if d > 0)
        diffs[k] = {
            "mean": float(np.mean(paired)),
            "std": float(np.std(paired)),
            "lower_is_better": lower_better,
            "better_seeds": int(n_better),  # A가 B보다 좋은 seed 수
            "n_seeds": len(paired),
        }
    return diffs


def main() -> None:
    logger.info("=" * 70)
    logger.info("Depth Feature Ablation — XGBoost (N=5 seeds, random 80/20)")
    logger.info("주의: random split이라 일부 singleton 작가는 test에 unseen으로 섞임 (mostly warm-start)")
    logger.info("=" * 70)

    df = load_data()
    n_unique_artists = int(df["artist_name_ko"].nunique())
    logger.info(f"Dataset: {len(df):,} rows / {n_unique_artists:,} unique artists")

    # Variant A: with depth (has_depth + depth_cm)
    features_A = COMMON_FEATURES + DEPTH_FEATURES
    result_A = run_variant(df, "A_with_depth", features_A)

    # Variant B: without depth
    features_B = COMMON_FEATURES
    result_B = run_variant(df, "B_no_depth", features_B)

    # 비교
    diffs = compare_variants(result_A, result_B)

    # 결과 출력
    print()
    print("=" * 70)
    print(f"📊 비교 결과 (A=with depth / B=no depth, N={len(SEEDS)} seeds, mostly warm-start)")
    print(f"   Dataset: {len(df):,} rows / {n_unique_artists:,} unique artists")
    print("=" * 70)
    print(f"{'Metric':<15} {'A (mean±std)':<22} {'B (mean±std)':<22} {'Δ (A-B)':<18} {'A better':<10}")
    print("-" * 90)
    for k, label in [
        ("mape", "MAPE"),
        ("median_ape", "median APE"),
        ("rmse_log", "RMSE (log)"),
        ("within_30pct", "Within-30%"),
        ("within_50pct", "Within-50%"),
    ]:
        a_mean, a_std = result_A["mean"][k], result_A["std"][k]
        b_mean, b_std = result_B["mean"][k], result_B["std"][k]
        d = diffs[k]
        # 방향성 반영 sign (A가 좋으면 ✓)
        a_is_better = (d["mean"] < 0) if d["lower_is_better"] else (d["mean"] > 0)
        sign = "↓" if d["mean"] < 0 else "↑"
        better_mark = "✓" if a_is_better else "✗"
        print(
            f"{label:<15} {a_mean:.4f}±{a_std:.4f}      "
            f"{b_mean:.4f}±{b_std:.4f}      "
            f"{sign}{abs(d['mean']):.4f}          "
            f"{d['better_seeds']}/{d['n_seeds']} {better_mark}"
        )

    print()
    print("📝 해석 가이드 (Codex R1 검수 반영):")
    print("  - MAPE/median APE/RMSE: 낮을수록 좋음")
    print("  - Within-30%/50%: 높을수록 좋음")
    print(f"  - A better N/{len(SEEDS)}: A가 B보다 좋은 seed 수 (metric 방향성 반영)")
    print(f"    {len(SEEDS)}/{len(SEEDS)} = 모든 seed에서 일관됨 (sign test p≈0.031, N=5)")
    print(f"  - N={len(SEEDS)}는 방향성 확인용. 통계적 유의성 강하게 주장하려면 N=20-30 권장")
    print(f"  - random split이라 일부 작가는 test에 unseen으로 섞임 (mostly warm-start)")
    print()

    # 결과 JSON 저장
    output = {
        "config": {
            "data": str(DATA_PATH.relative_to(REPO)),
            "xgb_params": XGB_PARAMS,
            "seeds": SEEDS,
            "test_size": TEST_SIZE,
            "common_features": COMMON_FEATURES,
            "depth_features": DEPTH_FEATURES,
        },
        "variant_A_with_depth": result_A,
        "variant_B_no_depth": result_B,
        "diff_A_minus_B": diffs,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
