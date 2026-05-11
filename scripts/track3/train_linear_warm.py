"""Track 3 — Phase 1 Warm 선형 모델.

Plan v2.1 §4.1 Warm 모델: Cold features + artist_name_ko target encoding.

학습 모델 (Cold와 동일하나 artist target encoding 추가):
  - OLS, Ridge, Lasso, Huber, Quantile (q=0.5)

Target encoding: cross-fit (out-of-fold encoding within train) — leakage 방지.
Evaluation: random 80/10/10 N=3 seeds (Phase 1은 빠른 진행, 최종 N=20은 Phase 5).
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
from sklearn.model_selection import KFold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
SPLITS_DIR = REPO / "data" / "track3_splits"
OUT_PATH = REPO / "data" / "track3_phase1_warm_results.json"

ARTIST_COL = "artist_name_ko"
TARGET = "ln_price_krw_unified"
SOURCE_COL = "source_platform"
COLD_FEATURES = [
    "medium_category", "support_category", "has_depth",
    "log_area", "estimated_ho", "orientation",
]
CATEGORICAL_COLS = ["medium_category", "support_category", "orientation"]
NUMERIC_COLS = ["has_depth", "log_area", "estimated_ho", "artist_te"]
TE_SMOOTHING = 20.0  # smoothed mean

N_SEEDS_PHASE1 = 3  # Phase 1 빠른 측정, 최종은 Phase 5에서 N=20


def smoothed_target_encode(
    train_df: pd.DataFrame, target_col: str, group_col: str, smoothing: float = TE_SMOOTHING
) -> tuple[dict, float]:
    """train_df 기준 smoothed target encoding map 생성.

    smoothed = (n * group_mean + smoothing * global_mean) / (n + smoothing)
    """
    global_mean = train_df[target_col].mean()
    stats = train_df.groupby(group_col)[target_col].agg(["mean", "count"])
    smoothed = (stats["count"] * stats["mean"] + smoothing * global_mean) / (
        stats["count"] + smoothing
    )
    return smoothed.to_dict(), float(global_mean)


def apply_target_encode(values: pd.Series, te_map: dict, global_mean: float) -> np.ndarray:
    """unseen group는 global_mean으로 fallback."""
    return values.map(te_map).fillna(global_mean).values


def cross_fit_artist_te(
    train_df: pd.DataFrame, n_inner_folds: int = 5, seed: int = 42
) -> np.ndarray:
    """train_df 내부에서 cross-fit OOF target encoding 생성 (leakage 방지)."""
    oof_te = np.full(len(train_df), np.nan)
    kf = KFold(n_splits=n_inner_folds, shuffle=True, random_state=seed)
    for inner_train_idx, inner_val_idx in kf.split(train_df):
        sub_train = train_df.iloc[inner_train_idx]
        te_map, gm = smoothed_target_encode(sub_train, TARGET, ARTIST_COL)
        oof_te[inner_val_idx] = apply_target_encode(
            train_df.iloc[inner_val_idx][ARTIST_COL], te_map, gm
        )
    return oof_te


def build_pipeline(estimator):
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_COLS),
        ("num", StandardScaler(), NUMERIC_COLS),
    ])
    return Pipeline([("prep", preprocess), ("est", estimator)])


def compute_metrics(y_true_ln, y_pred_ln):
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


def run_model_warm(name: str, estimator_factory, dev_df, warm_splits, n_seeds=N_SEEDS_PHASE1) -> dict:
    """Warm 모델 multi-seed 학습 + 평가 (target encoding cross-fit)."""
    seed_results = []
    for split in warm_splits[:n_seeds]:
        train_idx = split["train_indices"]
        test_idx = split["test_indices"]
        train_df = dev_df.iloc[train_idx].copy()
        test_df = dev_df.iloc[test_idx].copy()

        # Cross-fit TE on train
        train_df["artist_te"] = cross_fit_artist_te(train_df, seed=split["seed"])
        # Full-fit TE on entire train for test
        full_te_map, gm = smoothed_target_encode(train_df, TARGET, ARTIST_COL)
        test_df["artist_te"] = apply_target_encode(test_df[ARTIST_COL], full_te_map, gm)

        features = COLD_FEATURES + ["artist_te"]
        X_train = train_df[features]
        X_test = test_df[features]
        y_train = train_df[TARGET].values
        y_test = test_df[TARGET].values

        pipe = build_pipeline(estimator_factory())
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)

        m = compute_metrics(y_test, y_pred)
        m["seed"] = split["seed"]
        m["unseen_in_test"] = int((~test_df[ARTIST_COL].isin(train_df[ARTIST_COL])).sum())
        seed_results.append(m)

    agg = {
        "model": name,
        "n_seeds": len(seed_results),
        "per_seed": seed_results,
        "mean": {k: float(np.mean([s[k] for s in seed_results]))
                 for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
        "std": {k: float(np.std([s[k] for s in seed_results]))
                for k in ["median_ape", "mape", "rmse_log", "within_30pct", "within_50pct"]},
    }
    return agg


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 Phase 1 — Warm 선형 모델 (random 80/10/10 × N=3 seeds)")
    logger.info("=" * 70)

    outer_meta = json.loads((SPLITS_DIR / "outer_holdout_artists.json").read_text())
    warm_meta = json.loads((SPLITS_DIR / "warm_splits.json").read_text())
    df = pd.read_csv(DATA_PATH)
    dev_artists = set(outer_meta["dev_artists"])
    dev_df = df[df[ARTIST_COL].isin(dev_artists)].reset_index(drop=True)
    logger.info(f"Dev pool: {len(dev_df):,} rows / {dev_df[ARTIST_COL].nunique():,} 작가")

    models = {
        "OLS":           lambda: LinearRegression(),
        "Ridge":         lambda: RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0]),
        "Lasso":         lambda: LassoCV(alphas=[0.001, 0.01, 0.1, 1.0], max_iter=10000),
        "Huber":         lambda: HuberRegressor(max_iter=500),
        "Quantile_q05":  lambda: QuantileRegressor(quantile=0.5, solver="highs", alpha=0.0),
    }

    results = {}
    for name, factory in models.items():
        logger.info(f"\n--- {name} ---")
        try:
            res = run_model_warm(name, factory, dev_df, warm_meta["splits"])
            results[name] = res
            m = res["mean"]
            s = res["std"]
            logger.info(
                f"  med_APE={m['median_ape']:.3f}±{s['median_ape']:.3f} "
                f"MAPE={m['mape']:.3f}±{s['mape']:.3f} "
                f"RMSE_log={m['rmse_log']:.3f}±{s['rmse_log']:.3f} "
                f"W30={m['within_30pct']:.3f}"
            )
        except Exception as e:
            logger.error(f"  {name} 실패: {e}")
            results[name] = {"error": str(e)}

    # 결과 출력
    print()
    print("=" * 90)
    print(f"📊 Phase 1 Warm 선형 모델 결과 (random 80/10/10 × N={N_SEEDS_PHASE1} seeds, mean±std)")
    print("=" * 90)
    print(f"{'Model':<18} {'med_APE':>14} {'MAPE':>13} {'RMSE_log':>14} {'W30':>13}")
    print("-" * 90)
    for name, res in results.items():
        if "error" in res:
            print(f"{name:<18} ERROR: {res['error']}")
            continue
        m, s = res["mean"], res["std"]
        print(f"{name:<18} {m['median_ape']:.3f}±{s['median_ape']:.3f}   "
              f"{m['mape']:.3f}±{s['mape']:.3f}   "
              f"{m['rmse_log']:.3f}±{s['rmse_log']:.3f}   "
              f"{m['within_30pct']:.3f}±{s['within_30pct']:.3f}")

    print()
    print("📝 비교:")
    print(f"  - Warm median baseline (Phase 0): med_APE 0.739")
    valid = {k: v for k, v in results.items() if "error" not in v}
    if valid:
        best = min(valid, key=lambda k: valid[k]["mean"]["median_ape"])
        print(f"  - Best Warm 선형 ({best}): med_APE {valid[best]['mean']['median_ape']:.3f}")
        print(f"  - Cold best (Phase 1) 대비 Warm 우세 폭이 artist 정보 가치")
    print()

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
