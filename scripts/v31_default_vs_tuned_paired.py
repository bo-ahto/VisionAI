"""v3.1-2: Optuna tuning effect 정식 paired Wilcoxon (1.2 scope-reduced).

배경:
- v3.0 Group 1.2 v1 vs v2 paired test 는 v1 OOF raw 부재로 proxy 비교만 수행 (v1
  점추정이 v2 95% CI 내부 ⇒ 차이 통계적으로 명확하지 않음).
- v1 historical 전체 재현 (29,361 rows + 37 features + default hp) 은 학습 데이터/
  feature schema 차이로 paired 비교 불가능 (rows 매칭 안 됨). v3.2 로 미룸.
- 본 작업은 scope-reduced: v3-filtered (28,376 rows + 32 features) 위에서
  default hp vs Optuna tuned hp 만 비교하여 Optuna 효과를 정식 검정.

방법:
1. Default hp 학습 (catboost iter=1000 lr=0.05 depth=6 / xgb similar) → GroupKFold
   OOF (cold) + KFold OOF (warm) 산출
2. Tuned hp OOF 는 기존 oof_predictions.npz 사용 (production)
3. 동일 row order 위에서 per-row absolute percentage error 산출
   - cold: |y_actual - y_pred| / y_actual (cell calibration 미적용 raw)
   - warm: 동일
4. Paired Wilcoxon signed-rank test (양측 / 단측 default<tuned)
5. Cohen's d_z (paired effect size)
6. Bootstrap 10000 paired CI on Δ = MdAPE_default - MdAPE_tuned

산출물:
    model_test_results/v3_diagnostics/default_vs_tuned_paired.json

Usage:
    PYTHONPATH=src python3 scripts/v31_default_vs_tuned_paired.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from scipy import stats
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import (
    CAT_FEATURES,
    _cb_pool,
    _warm_mask,
    load_data,
    prepare_features,
)

from visionai.price_engine._eval_helpers import label_encode_xgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
OUT_JSON = DIAG_DIR / "default_vs_tuned_paired.json"

RANDOM_SEED = 42
N_BOOTSTRAP = 10_000

# Default hp = train_primary_market_v3_filtered.py:166-180 의 cv_groupkfold 기본값
DEFAULT_CB_PARAMS = {
    "iterations": 1000,
    "learning_rate": 0.05,
    "depth": 6,
}
DEFAULT_XGB_PARAMS = {
    "eta": 0.05,
    "max_depth": 6,
    "num_boost_round": 1000,
}


def _train_cb_xgb_oof_groupkfold(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Default hp 로 GroupKFold OOF 산출."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[GKF default %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **DEFAULT_CB_PARAMS,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))

        Xtr_e, Xte_e, _ = label_encode_xgb(
            X.iloc[tr],
            X.iloc[te],
            categorical_features=CAT_FEATURES,
        )
        xgb_p = {k: v for k, v in DEFAULT_XGB_PARAMS.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y[tr]),
            num_boost_round=DEFAULT_XGB_PARAMS["num_boost_round"],
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y[te]))
    return cb_preds, xgb_preds


def _train_cb_xgb_oof_kfold_warm(
    X_warm: pd.DataFrame,
    y_warm: np.ndarray,
    n_splits: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Default hp 로 warm slice KFold OOF 산출."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    cb_preds = np.zeros(len(y_warm))
    xgb_preds = np.zeros(len(y_warm))
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[KF warm default %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **DEFAULT_CB_PARAMS,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X_warm.iloc[tr], y_warm[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X_warm.iloc[te]))

        Xtr_e, Xte_e, _ = label_encode_xgb(
            X_warm.iloc[tr],
            X_warm.iloc[te],
            categorical_features=CAT_FEATURES,
        )
        xgb_p = {k: v for k, v in DEFAULT_XGB_PARAMS.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y_warm[tr]),
            num_boost_round=DEFAULT_XGB_PARAMS["num_boost_round"],
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y_warm[te]))
    return cb_preds, xgb_preds


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def paired_test(
    y_true: np.ndarray,
    pred_default: np.ndarray,
    pred_tuned: np.ndarray,
    label: str,
    groups: np.ndarray | None = None,
) -> dict:
    """per-row absolute percentage error 위에서 paired Wilcoxon + Cohen's d_z + paired bootstrap CI."""
    valid = (y_true > 0) & (pred_default > 0) & (pred_tuned > 0)
    if not valid.any():
        return {"label": label, "skipped": True}
    yt = y_true[valid]
    pd_default = pred_default[valid]
    pd_tuned = pred_tuned[valid]
    ape_default = np.abs(yt - pd_default) / yt
    ape_tuned = np.abs(yt - pd_tuned) / yt
    diff = ape_default - ape_tuned  # 양수면 tuned 가 개선

    # Wilcoxon signed-rank
    try:
        wstat, p_two = stats.wilcoxon(diff, alternative="two-sided")
        _, p_one = stats.wilcoxon(diff, alternative="greater")  # H1: default > tuned
    except ValueError as e:
        wstat, p_two, p_one = float("nan"), float("nan"), float("nan")
        logger.warning("wilcoxon fail (%s): %s", label, e)

    # Cohen's d_z (paired)
    d_z = float(np.mean(diff) / np.std(diff, ddof=1)) if np.std(diff, ddof=1) > 0 else 0.0

    # Paired bootstrap CI on Δ MdAPE = MdAPE_default - MdAPE_tuned
    rng = np.random.default_rng(RANDOM_SEED)
    n = len(yt)
    if groups is not None:
        # cluster bootstrap by artist
        valid_groups = groups[valid]
        unique_groups = np.unique(valid_groups)
        idx_by_group = {g: np.where(valid_groups == g)[0] for g in unique_groups}
        n_g = len(unique_groups)
        diffs_md = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            chosen = rng.choice(n_g, size=n_g, replace=True)
            idx = np.concatenate([idx_by_group[unique_groups[c]] for c in chosen])
            diffs_md[i] = (np.median(ape_default[idx]) - np.median(ape_tuned[idx])) * 100
        method = "paired cluster (artist) bootstrap"
    else:
        # row-level bootstrap (warm slice 작품 단위 KFold)
        diffs_md = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            idx = rng.integers(0, n, size=n)
            diffs_md[i] = (np.median(ape_default[idx]) - np.median(ape_tuned[idx])) * 100
        method = "row-level paired bootstrap"

    return {
        "label": label,
        "n": int(n),
        "mdape_default": float(np.median(ape_default) * 100),
        "mdape_tuned": float(np.median(ape_tuned) * 100),
        "delta_mdape_pp": float(np.median(ape_default) * 100 - np.median(ape_tuned) * 100),
        "wilcoxon": {
            "statistic": float(wstat) if not np.isnan(wstat) else None,
            "p_two_sided": float(p_two) if not np.isnan(p_two) else None,
            "p_one_sided_default_gt_tuned": float(p_one) if not np.isnan(p_one) else None,
        },
        "cohens_d_z": d_z,
        "paired_bootstrap_ci": {
            "method": method,
            "delta_mdape_pp": float(np.median(diffs_md)),
            "ci_low": float(np.percentile(diffs_md, 2.5)),
            "ci_high": float(np.percentile(diffs_md, 97.5)),
        },
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_gkf_tuned_ln = oof["cb_preds_gkf_ln"]
    xgb_gkf_tuned_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_kf_tuned_ln = oof["cb_preds_kf_ln"]
    xgb_kf_tuned_ln = oof["xgb_preds_kf_ln"]
    warm_mask_full = oof["warm_mask"].astype(bool)

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y, groups = prepare_features(df)
    np.testing.assert_allclose(y, y_actual_ln, rtol=1e-10)

    # Default hp 학습
    overall_start = time.time()
    logger.info("=== Default hp GroupKFold OOF (cold) ===")
    cb_gkf_default_ln, xgb_gkf_default_ln = _train_cb_xgb_oof_groupkfold(X, y, groups)
    logger.info("=== Default hp KFold OOF (warm) ===")
    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm_check = y[wmask]
    np.testing.assert_allclose(y_warm_check, y_warm_ln, rtol=1e-10)
    cb_kf_default_ln, xgb_kf_default_ln = _train_cb_xgb_oof_kfold_warm(X_warm, y_warm_check)
    train_wall = time.time() - overall_start

    # 가격 공간으로 변환 + ensemble
    y_full_price = np.exp(y)
    y_warm_price = np.exp(y_warm_ln)

    cb_cold_default = np.exp(cb_gkf_default_ln)
    xgb_cold_default = np.exp(xgb_gkf_default_ln)
    ens_cold_default = np.exp((cb_gkf_default_ln + xgb_gkf_default_ln) / 2)

    cb_cold_tuned = np.exp(cb_gkf_tuned_ln)
    xgb_cold_tuned = np.exp(xgb_gkf_tuned_ln)
    ens_cold_tuned = np.exp((cb_gkf_tuned_ln + xgb_gkf_tuned_ln) / 2)

    cb_warm_default = np.exp(cb_kf_default_ln)
    xgb_warm_default = np.exp(xgb_kf_default_ln)
    ens_warm_default = np.exp((cb_kf_default_ln + xgb_kf_default_ln) / 2)

    cb_warm_tuned = np.exp(cb_kf_tuned_ln)
    xgb_warm_tuned = np.exp(xgb_kf_tuned_ln)
    ens_warm_tuned = np.exp((cb_kf_tuned_ln + xgb_kf_tuned_ln) / 2)

    # paired tests
    # cold: artist-cluster bootstrap (within-artist 의존성 보존)
    # warm: row-level + artist-cluster 둘 다 (warm slice 도 동일 artist 복수 작품 포함이라
    #       cluster bootstrap 이 운영 일반화 결론에 더 정합 — codex v3.1-2 P1)
    groups_warm = groups[wmask]
    cold_results = [
        paired_test(y_full_price, cb_cold_default, cb_cold_tuned, "cold_catboost", groups),
        paired_test(y_full_price, xgb_cold_default, xgb_cold_tuned, "cold_xgboost", groups),
        paired_test(y_full_price, ens_cold_default, ens_cold_tuned, "cold_ensemble", groups),
    ]
    # warm: row-level (KFold 작품 분할 정합) + cluster (artist 일반화 보조 검정)
    warm_results_row = [
        paired_test(y_warm_price, cb_warm_default, cb_warm_tuned, "warm_catboost_row"),
        paired_test(y_warm_price, xgb_warm_default, xgb_warm_tuned, "warm_xgboost_row"),
        paired_test(y_warm_price, ens_warm_default, ens_warm_tuned, "warm_ensemble_row"),
    ]
    warm_results_cluster = [
        paired_test(
            y_warm_price, cb_warm_default, cb_warm_tuned, "warm_catboost_cluster", groups_warm
        ),
        paired_test(
            y_warm_price, xgb_warm_default, xgb_warm_tuned, "warm_xgboost_cluster", groups_warm
        ),
        paired_test(
            y_warm_price, ens_warm_default, ens_warm_tuned, "warm_ensemble_cluster", groups_warm
        ),
    ]
    warm_results = warm_results_row + warm_results_cluster

    # Tuned point estimates 메모용
    summary = {
        "config": {
            "scope": (
                "v3-filtered (28,376 rows / 32 features) 위에서 default hp vs Optuna tuned hp 의 "
                "paired Wilcoxon. v1 historical 전체 재현 (29,361 rows / 37 features / default hp) "
                "은 row schema 차이로 paired 불가능 → v3.2 로 미룸. 본 작업은 Optuna 효과만 분리."
            ),
            "default_hp": {
                "catboost": DEFAULT_CB_PARAMS,
                "xgboost": DEFAULT_XGB_PARAMS,
            },
            "tuned_hp_source": "model_test_results/integrated_v3_filtered_tuned_best_params.json",
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RANDOM_SEED,
            "interpretation": (
                "Δ MdAPE = MdAPE_default - MdAPE_tuned (양수 = tuned 가 개선). "
                "Wilcoxon p-value 가 α=0.05 미만이면 효과 통계적으로 유의. "
                "Cohen's d_z 절대값 0.2 small / 0.5 medium / 0.8 large. "
                "Paired bootstrap CI 하한 > 0 ⇒ 통계적으로 명확한 개선. "
                "Warm 결과는 row-level (작품 단위 KFold 분할 정합) + cluster (artist 일반화 보조) "
                "둘 다 보고 — cluster CI 가 0 포함하면 artist 단위 일반화 증거 보류."
            ),
        },
        "cold_groupkfold": cold_results,
        "warm_kfold": warm_results,
        "wall_seconds_total": float(train_wall),
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 110)
    print("v3.1-2 default vs tuned paired Wilcoxon (Optuna 효과)")
    print("=" * 110)
    print(
        f"\n{'Slice':<25} {'n':>6} {'MdAPE def':>10} {'MdAPE tuned':>12} {'Δ %p':>8} "
        f"{'Wilcoxon p':>11} {'d_z':>7} {'95% CI Δ (cluster/row)':>26}"
    )
    print("-" * 110)
    for r in cold_results + warm_results:
        if r.get("skipped"):
            continue
        wp = r["wilcoxon"]["p_two_sided"]
        ci = r["paired_bootstrap_ci"]
        print(
            f"{r['label']:<25} {r['n']:>6} {r['mdape_default']:>9.2f}% {r['mdape_tuned']:>11.2f}% "
            f"{r['delta_mdape_pp']:>+7.2f}%p "
            f"{wp:>10.4f} {r['cohens_d_z']:>+7.3f} "
            f"[{ci['ci_low']:>+5.2f}, {ci['ci_high']:>+5.2f}]"
        )

    print(f"\nTotal wall: {train_wall:.0f}s ({train_wall / 60:.1f} min)")
    print(f"저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
