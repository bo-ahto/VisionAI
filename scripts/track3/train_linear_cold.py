"""Track 3 — Phase 1 Cold 선형 모델.

Plan v2.1 §4.1 Cold 모델: artist_name_ko 미사용. 6 features.

학습 모델:
  - OLS              (LinearRegression)
  - Ridge            (RidgeCV로 alpha 자동)
  - Lasso            (LassoCV로 alpha 자동)
  - Huber            (long-tail outlier robust)
  - LAD (q=0.5)      (least absolute deviation)
  - Quantile q=0.1, 0.5, 0.9  (신뢰구간 baseline)

Evaluation: GroupKFold(5) OOF + Source-stratified.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import (
    LinearRegression, RidgeCV, LassoCV, HuberRegressor, QuantileRegressor
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_phase1_cold_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
COLD_FEATURES = [
    "medium_category", "support_category", "has_depth",
    "log_area", "estimated_ho", "orientation",
]
CATEGORICAL_COLS = ["medium_category", "support_category", "orientation"]
NUMERIC_COLS = ["has_depth", "log_area", "estimated_ho"]


def build_pipeline(estimator):
    """OneHot + Scale (numeric) + estimator."""
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_COLS),
        ("num", StandardScaler(), NUMERIC_COLS),
    ])
    return Pipeline([("prep", preprocess), ("est", estimator)])


def compute_metrics(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> dict:
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    ape = np.abs(y_pred - y_true) / y_true
    log_resid = y_pred_ln - y_true_ln
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(np.mean(log_resid ** 2))),
        "within_30pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.30)),
        "within_50pct": float(np.mean(np.abs(y_pred / y_true - 1) < 0.50)),
    }


def source_breakdown(y_true_ln, y_pred_ln, sources):
    """Source 별 metric 분해."""
    result = {}
    for src in ["artsy", "saatchi", "artue"]:
        mask = sources == src
        if mask.sum() == 0:
            continue
        m = compute_metrics(y_true_ln[mask], y_pred_ln[mask])
        m["n"] = int(mask.sum())
        result[src] = m
    return result


def run_model_cold(name: str, estimator_factory, dev_df, cold_folds) -> dict:
    """단일 모델을 5-fold GroupKFold OOF로 학습 + 평가."""
    fold_results = []
    oof_pred = np.full(len(dev_df), np.nan)
    sources_arr = dev_df[SOURCE_COL].values

    for fold in cold_folds:
        train_idx = fold["train_indices"]
        test_idx = fold["test_indices"]
        X_train = dev_df.iloc[train_idx][COLD_FEATURES]
        X_test = dev_df.iloc[test_idx][COLD_FEATURES]
        y_train = dev_df.iloc[train_idx][TARGET].values
        y_test = dev_df.iloc[test_idx][TARGET].values

        pipe = build_pipeline(estimator_factory())
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        oof_pred[test_idx] = y_pred

        m = compute_metrics(y_test, y_pred)
        m["fold"] = fold["fold"]
        fold_results.append(m)

    # Aggregate (fold-median)
    agg = {
        "model": name,
        "n_folds": len(fold_results),
        "per_fold": fold_results,
        "median": {k: float(np.median([f[k] for f in fold_results]))
                   for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "source_breakdown": source_breakdown(
            dev_df[TARGET].values, oof_pred, sources_arr
        ),
    }
    return agg


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 Phase 1 — Cold 선형 모델 (GroupKFold 5-fold OOF)")
    logger.info("=" * 70)

    # Load
    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    cold_meta = json.loads((SPLITS_DIR / "cold_folds.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    # 모델 정의
    models = {
        "OLS":           lambda: LinearRegression(),
        "Ridge":         lambda: RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0]),
        "Lasso":         lambda: LassoCV(alphas=[0.001, 0.01, 0.1, 1.0], max_iter=10000),
        "Huber":         lambda: HuberRegressor(max_iter=500),
        "Quantile_q05":  lambda: QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0),
        "Quantile_q01":  lambda: QuantileRegressor(quantile=0.1, solver="highs", alpha=0.0),
        "Quantile_q09":  lambda: QuantileRegressor(quantile=0.9, solver="highs", alpha=0.0),
    }

    results = {}
    for name, factory in models.items():
        logger.info(f"\n--- {name} ---")
        try:
            res = run_model_cold(name, factory, dev_df, cold_meta["folds"])
            results[name] = res
            m = res["median"]
            logger.info(
                f"  med_APE={m['median_ape']:.3f} MAPE={m['mape']:.3f} "
                f"RMSE_log={m['rmse_log']:.3f} W30={m['within_30pct']:.3f}"
            )
        except Exception as e:
            logger.error(f"  {name} 실패: {e}")
            results[name] = {"error": str(e)}

    # 결과 출력
    print()
    print("=" * 90)
    print("📊 Phase 1 Cold 선형 모델 결과 (5-fold GroupKFold OOF, fold-median)")
    print("=" * 90)
    print(f"{'Model':<18} {'med_APE':>9} {'MAPE':>8} {'RMSE_log':>9} {'W30':>7} {'W50':>7}")
    print("-" * 90)
    for name, res in results.items():
        if "error" in res:
            print(f"{name:<18} ERROR: {res['error']}")
            continue
        m = res["median"]
        print(f"{name:<18} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
              f"{m['rmse_log']:>9.3f} {m['within_30pct']:>7.3f} {m['within_50pct']:>7.3f}")

    # Source breakdown — best 모델 기준
    valid = {k: v for k, v in results.items() if "error" not in v}
    if valid:
        best = min(valid, key=lambda k: valid[k]["median"]["median_ape"])
        print()
        print(f"📊 Best model ({best}) — Source별 분해")
        print("=" * 90)
        sb = valid[best]["source_breakdown"]
        print(f"{'Source':<10} {'n':>7} {'med_APE':>9} {'MAPE':>8} {'RMSE_log':>9} {'W30':>7}")
        print("-" * 60)
        for src, m in sb.items():
            print(f"{src:<10} {m['n']:>7,} {m['median_ape']:>9.3f} {m['mape']:>8.3f} "
                  f"{m['rmse_log']:>9.3f} {m['within_30pct']:>7.3f}")

    # Phase 0 비교
    print()
    print("📝 Phase 0 baseline 대비:")
    print(f"  - Median baseline: med_APE 0.754 (cold)")
    print(f"  - LightGBM both:   med_APE 0.472 (cold, Phase 0 ablation)")
    if valid:
        m = valid[best]["median"]
        print(f"  - Best 선형 ({best}): med_APE {m['median_ape']:.3f} (Phase 1)")
        delta_baseline = 0.754 - m["median_ape"]
        delta_lgb = m["median_ape"] - 0.472
        print(f"    → baseline 대비 ↓{delta_baseline:.3f} / LGB 대비 {'↑' if delta_lgb > 0 else '↓'}{abs(delta_lgb):.3f}")
    print()

    # Save
    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
