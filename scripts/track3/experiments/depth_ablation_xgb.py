"""Depth feature ablation 실험 — XGBoost regressor (v3: Warm + Cold 양쪽).

목적: `has_depth` + `depth_cm` 피처가 가격 예측에 미치는 영향 측정.

v3 변경 (외부 검수자 leakage 지적 반영):
- categorical dtype을 split 이후에 fit (train만 보고)
- GroupShuffleSplit 추가 → 진짜 cold-start (unseen artist) 평가
- Warm-start와 Cold-start 결과 모두 보고

재현 방법:
    cd depth_ablation_share
    python3 -m pip install pandas numpy scikit-learn "xgboost>=2.0"
    python3 depth_ablation_xgb.py

데이터:
    track3_unified_v1_train.csv (같은 폴더, 40,137 rows, is_outlier=0만)

비교 변형:
    A. With depth     — has_depth + depth_cm 포함 (8 features)
    B. Without depth  — has_depth + depth_cm 제외 (6 features)

평가 시나리오 (둘 다 측정):
    1. WARM (random split)   — 같은 작가 작품이 train/test 양쪽 가능 (학습된 작가 평가)
    2. COLD (GroupShuffleSplit) — 작가 단위 분리 (진짜 신규 작가 평가)

평가 metric:
    - median APE   median(|y - ŷ| / y) — 중앙값 비율 오차 (outlier robust, primary)
    - MAPE         mean(|y - ŷ| / y)
    - RMSE (log)
    - Within-30%   |ŷ/y - 1| < 0.3 비율 (실용 정확도)
    - Within-50%   |ŷ/y - 1| < 0.5 비율

Output:
    - 콘솔 결과 표 (Warm + Cold 둘 다)
    - depth_ablation_results.json (재현용, env 메타 포함)

주의:
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
from sklearn.model_selection import train_test_split, GroupShuffleSplit
import xgboost as xgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── 설정 ───
# 같은 폴더에서 직접 읽기 (외부 공유 패키지 기준).
# 원본 repo 구조(VisionAI/scripts/track3/experiments/)는 SCRIPT_DIR로 자동 처리.
SCRIPT_DIR = Path(__file__).resolve().parent
_local_csv = SCRIPT_DIR / "track3_unified_v1_train.csv"
_repo_csv = SCRIPT_DIR.parent.parent.parent / "data" / "track3_unified_v1_train.csv"
DATA_PATH = _local_csv if _local_csv.exists() else _repo_csv
OUT_PATH = SCRIPT_DIR / "depth_ablation_results.json"

# Feature 설정
COMMON_FEATURES = [
    "artist_name_ko",
    "medium_category",
    "support_category",
    "log_area",
    "estimated_ho",
    "orientation",
]
DEPTH_FEATURES = ["has_depth", "depth_cm"]
TARGET = "ln_price_krw_unified"
ARTIST_COL = "artist_name_ko"

CATEGORICAL_COLS = ["artist_name_ko", "medium_category", "support_category", "orientation"]

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
    "enable_categorical": True,
    "early_stopping_rounds": 30,
}

SEEDS = [42, 123, 456, 789, 1024]
TEST_SIZE = 0.2


def load_data() -> pd.DataFrame:
    """데이터 로드만 (categorical fit 안 함 — split 이후로 이동)."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"데이터 로드: {len(df):,} 작품 / {len(df.columns)} 컬럼")
    return df


def fit_categorical(train_df, test_df, features):
    """Categorical dtype을 train만 보고 fit, test는 train 카테고리로 매핑.

    이전 v2는 load_data()에서 전체 df에 astype('category') 적용 →
    test row까지 카테고리 set 결정 (약한 leakage). v3는 split 이후 fit.
    """
    train_df = train_df[features].copy()
    test_df = test_df[features].copy()
    for col in features:
        if col in CATEGORICAL_COLS:
            train_cats = pd.Categorical(train_df[col]).categories
            dtype = pd.CategoricalDtype(categories=train_cats)
            train_df[col] = train_df[col].astype(dtype)
            test_df[col] = test_df[col].astype(dtype)  # train에 없는 카테고리는 NaN
    return train_df, test_df


def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "mape": float(np.mean(ape)),
        "median_ape": float(np.median(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.50)),
    }


def split_warm(df, features, seed):
    """Random 80/20 split — 같은 작가가 train/test 양쪽 가능 (warm-start)."""
    X = df[features + [ARTIST_COL]] if ARTIST_COL not in features else df[features]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=seed
    )
    return X_train, X_test, y_train, y_test


def split_cold(df, features, seed):
    """GroupShuffleSplit by artist — 작가 단위 분리 (cold-start)."""
    X = df[features]
    y = df[TARGET]
    groups = df[ARTIST_COL]
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=seed)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    return X.iloc[train_idx], X.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]


def run_one_seed(df, features, seed, scenario):
    """단일 seed × scenario (warm or cold) 학습 + 평가."""
    if scenario == "warm":
        X_train, X_test, y_train, y_test = split_warm(df, features, seed)
    else:
        X_train, X_test, y_train, y_test = split_cold(df, features, seed)

    # Split 후 categorical fit (train만 보고)
    X_train_cat, X_test_cat = fit_categorical(X_train, X_test, features)

    # Inner val for early stopping (train 안에서)
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train_cat, y_train, test_size=0.1, random_state=seed
    )

    model = xgb.XGBRegressor(random_state=seed, **XGB_PARAMS)
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)

    y_pred = model.predict(X_test_cat)
    metrics = compute_metrics(y_test.values, y_pred)
    metrics["n_train"] = int(len(X_train))
    metrics["n_test"] = int(len(X_test))
    metrics["best_iter"] = int(model.best_iteration)

    # Cold scenario: test 작가 unseen 비율 (반드시 100%여야 정상)
    if scenario == "cold":
        test_artists = set(X_test[ARTIST_COL])
        train_artists = set(X_train[ARTIST_COL])
        unseen = len(test_artists - train_artists)
        metrics["unseen_artists_pct"] = float(unseen / len(test_artists))
    return metrics


def run_variant(df, variant_name, features, scenario):
    logger.info(f"\n{'='*70}\n[{scenario.upper()}] 버전 {variant_name}: {len(features)} 피처")
    logger.info(f"  피처 목록: {features}")
    logger.info(f"{'='*70}")

    seed_results = []
    for seed in SEEDS:
        m = run_one_seed(df, features, seed, scenario)
        seed_results.append(m)
        extra = f" / unseen={m.get('unseen_artists_pct', 0)*100:.0f}%" if scenario == "cold" else ""
        logger.info(
            f"  seed={seed} | MAPE={m['mape']:.3f} | median_APE={m['median_ape']:.3f} | "
            f"RMSE_log={m['rmse_log']:.3f} | W30={m['within_30pct']:.3f}{extra}"
        )

    agg = {
        "variant": variant_name,
        "scenario": scenario,
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


def compare_variants(result_A, result_B):
    LOWER_IS_BETTER = {
        "mape": True, "median_ape": True, "rmse_log": True,
        "within_30pct": False, "within_50pct": False,
    }
    diffs = {}
    for k, lower_better in LOWER_IS_BETTER.items():
        paired = [a[k] - b[k] for a, b in zip(result_A["per_seed"], result_B["per_seed"])]
        if lower_better:
            n_better = sum(1 for d in paired if d < 0)
        else:
            n_better = sum(1 for d in paired if d > 0)
        diffs[k] = {
            "mean": float(np.mean(paired)),
            "std": float(np.std(paired)),
            "lower_is_better": lower_better,
            "better_seeds": int(n_better),
            "n_seeds": len(paired),
        }
    return diffs


def print_table(results_A, results_B, diffs, scenario_label, n_unique_artists):
    print()
    print("=" * 75)
    print(f"📊 [{scenario_label}] (A=깊이 포함 / B=깊이 제외, {len(SEEDS)}회 반복)")
    print(f"   데이터: 40,137 작품 / {n_unique_artists:,} 작가")
    print("=" * 75)
    print(f"{'지표':<14} {'A (평균±편차)':<19} {'B (평균±편차)':<19} {'차이':<13} {'A 우세'}")
    print("-" * 75)
    for k, label in [
        ("mape", "MAPE"),
        ("median_ape", "median APE"),
        ("rmse_log", "RMSE (log)"),
        ("within_30pct", "Within-30%"),
        ("within_50pct", "Within-50%"),
    ]:
        a_mean, a_std = results_A["mean"][k], results_A["std"][k]
        b_mean, b_std = results_B["mean"][k], results_B["std"][k]
        d = diffs[k]
        sign = "↓" if d["mean"] < 0 else "↑"
        a_better = (d["mean"] < 0) if d["lower_is_better"] else (d["mean"] > 0)
        mark = "✓" if a_better else "✗"
        print(
            f"{label:<14} {a_mean:.4f}±{a_std:.4f}   "
            f"{b_mean:.4f}±{b_std:.4f}   "
            f"{sign}{abs(d['mean']):.4f}      "
            f"{d['better_seeds']}/{d['n_seeds']} {mark}"
        )


def main():
    logger.info("=" * 70)
    logger.info("깊이 피처 영향 비교 실험 — XGBoost v3")
    logger.info(f"Warm-start (random split) + Cold-start (GroupShuffleSplit) 양쪽 측정")
    logger.info("=" * 70)

    df = load_data()
    n_unique = int(df[ARTIST_COL].nunique())
    logger.info(f"데이터: {len(df):,} 작품 / {n_unique:,} 작가")

    features_A = COMMON_FEATURES + DEPTH_FEATURES
    features_B = COMMON_FEATURES

    output = {
        "config": {
            "data": DATA_PATH.name,
            "xgb_params": XGB_PARAMS,
            "seeds": SEEDS,
            "test_size": TEST_SIZE,
        },
    }

    # ─── WARM scenario ───
    warm_A = run_variant(df, "A_깊이포함", features_A, "warm")
    warm_B = run_variant(df, "B_깊이제외", features_B, "warm")
    warm_diffs = compare_variants(warm_A, warm_B)
    print_table(warm_A, warm_B, warm_diffs,
                "WARM (random split — 학습된 작가 평가)", n_unique)
    output["warm"] = {"variant_A": warm_A, "variant_B": warm_B, "diff": warm_diffs}

    # ─── COLD scenario ───
    cold_A = run_variant(df, "A_깊이포함", features_A, "cold")
    cold_B = run_variant(df, "B_깊이제외", features_B, "cold")
    cold_diffs = compare_variants(cold_A, cold_B)
    print_table(cold_A, cold_B, cold_diffs,
                "COLD (GroupShuffleSplit by artist — 진짜 신규 작가 평가)", n_unique)
    output["cold"] = {"variant_A": cold_A, "variant_B": cold_B, "diff": cold_diffs}

    print()
    print("📝 해석 가이드:")
    print("  - WARM은 'mostly warm-start' (같은 작가가 train/test 양쪽 등장 가능)")
    print("    → 실 운영에서 학습된 작가의 신규 작품 예측 시나리오")
    print("  - COLD는 작가 단위 완전 분리 (test 작가 100% unseen)")
    print("    → 실 운영에서 신규 작가 작품 예측 시나리오")
    print("  - 두 결과는 다른 시나리오를 측정 — 단순 비교 X")
    print()

    import platform
    import sklearn
    output["env"] = {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
        "xgboost": xgb.__version__,
        "platform": platform.platform(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
