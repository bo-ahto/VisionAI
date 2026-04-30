"""v3.2-2: v1 historical 재현 + 정식 paired Wilcoxon (1.2 close).

배경:
- v3.0 1.2 v1 vs v2 paired test 는 v1 OOF 부재로 proxy 비교만 수행 (점추정 비교).
- v3.1-2 default vs tuned 는 scope-reduced (hp 효과만, features/data 동일).
- 본 작업은 v1 historical spec 을 재현하여 정식 1.2 검정 close.

v1 spec 정의:
- Features: CB_FEATURES (32) + 5 extra (career_age, work_age, vintage_premium,
  freshness_discount, gallery_name) = 37 (v2 가 제거한 train/serve drift features 재포함)
- Hyperparameters: default (catboost iter=1000 lr=0.05 depth=6 / xgb similar)
- 학습 데이터: v3-filtered 28,376 row (입체 985 제외) — paired 정합 위해
  v2 와 동일 row schema 사용. 정식 v1 spec (29,361 row) 은 row mismatch 로 paired
  비교 불가능해 본 작업에서 제외 (v3.3 backlog).

3-way 비교:
- v1 spec: CB_FEATURES + 5 extra + default hp
- v1.5 spec: CB_FEATURES only + default hp (= v3.1-2 default, 이미 산출)
- v2 spec: CB_FEATURES only + Optuna tuned (= production, 이미 산출)

차이 분해:
- v1 → v1.5: 5 features 제거 (train/serve drift fix) 효과
- v1.5 → v2: Optuna tuning 효과 (v3.1-2 결과)
- v1 → v2: 결합 효과 = 정식 1.2 답

Paired Wilcoxon + cluster ΔCI on per-row absolute percentage error.

산출물:
    model_test_results/v3_diagnostics/v1_historical_paired.json

Usage:
    PYTHONPATH=src python3 scripts/v32_v1_historical_paired.py
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
from catboost import CatBoostRegressor, Pool
from scipy import stats
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import CAT_FEATURES, CB_FEATURES, _warm_mask, load_data
from visionai.price_engine._eval_helpers import label_encode_xgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OOF_PATH = DIAG_DIR / "oof_predictions.npz"
DEFAULT_OOF_JSON = DIAG_DIR / "default_vs_tuned_paired.json"  # v3.1-2 산출물 참조
OUT_JSON = DIAG_DIR / "v1_historical_paired.json"

RANDOM_SEED = 42
N_BOOTSTRAP = 10_000

# v1 spec = v2 (32 features) + 5 extra (train/serve drift 이전)
V1_EXTRA_FEATURES = [
    "career_age",
    "work_age",
    "vintage_premium",
    "freshness_discount",
    "gallery_name",
]
V1_EXTRA_CATEGORICAL = ["gallery_name"]  # 5 중 categorical
V1_FEATURES = CB_FEATURES + V1_EXTRA_FEATURES  # 37
V1_CAT_FEATURES = CAT_FEATURES + V1_EXTRA_CATEGORICAL  # 7

# Default hp = v3.1-2 와 동일 (train_primary_market_v3_filtered.py:166-180 의 cv_groupkfold 기본값)
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


def prepare_features_v1(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """v1 features (37) 준비 — v2 와 동일 정규화 + 5 extra features 추가."""
    missing = [c for c in V1_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing V1 features in dataset: {missing}")

    X = df[V1_FEATURES].copy()
    for col in V1_CAT_FEATURES:
        X[col] = (
            X[col]
            .astype(str)
            .fillna("unknown")
            .replace({"nan": "unknown", "None": "unknown", "": "unknown"})
        )
    for col in V1_FEATURES:
        if col not in V1_CAT_FEATURES:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    y = df["ln_price"].to_numpy()
    groups = df["artist_slug"].astype(str).to_numpy()
    return X, y, groups


def _cb_pool_v1(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in V1_CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _train_v1_oof_groupkfold(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, n_splits: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """v1 spec (37 features + default hp) GroupKFold OOF."""
    gkf = GroupKFold(n_splits=n_splits)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        logger.info("[v1 GKF %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **DEFAULT_CB_PARAMS,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_v1(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool_v1(X.iloc[te]))

        Xtr_e, Xte_e, _ = label_encode_xgb(
            X.iloc[tr],
            X.iloc[te],
            categorical_features=V1_CAT_FEATURES,
        )
        xgb_p = {k: v for k, v in DEFAULT_XGB_PARAMS.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
            dtrain=xgb.DMatrix(Xtr_e, label=y[tr]),
            num_boost_round=DEFAULT_XGB_PARAMS["num_boost_round"],
        )
        xgb_preds[te] = m.predict(xgb.DMatrix(Xte_e, label=y[te]))
    return cb_preds, xgb_preds


def _train_v1_oof_kfold_warm(
    X_warm: pd.DataFrame, y_warm: np.ndarray, n_splits: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """v1 spec warm slice KFold OOF."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    cb_preds = np.zeros(len(y_warm))
    xgb_preds = np.zeros(len(y_warm))
    for fold, (tr, te) in enumerate(kf.split(X_warm), 1):
        logger.info("[v1 KF warm %d/%d] train=%d test=%d", fold, n_splits, len(tr), len(te))
        cb = CatBoostRegressor(
            **DEFAULT_CB_PARAMS,
            loss_function="RMSE",
            verbose=0,
            random_seed=RANDOM_SEED,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool_v1(X_warm.iloc[tr], y_warm[tr]))
        cb_preds[te] = cb.predict(_cb_pool_v1(X_warm.iloc[te]))

        Xtr_e, Xte_e, _ = label_encode_xgb(
            X_warm.iloc[tr],
            X_warm.iloc[te],
            categorical_features=V1_CAT_FEATURES,
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
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    label_a: str,
    label_b: str,
    groups: np.ndarray | None = None,
) -> dict:
    """per-row APE 위 paired Wilcoxon + Cohen's d_z + paired bootstrap CI on Δ MdAPE.

    Δ = MdAPE(a) - MdAPE(b). 양수면 b 가 더 정확.
    cluster bootstrap (groups 제공 시) 또는 row-level bootstrap.
    """
    valid = (y_true > 0) & (pred_a > 0) & (pred_b > 0)
    if not valid.any():
        return {"label": f"{label_a}_vs_{label_b}", "skipped": True}
    yt = y_true[valid]
    pa = pred_a[valid]
    pb = pred_b[valid]
    ape_a = np.abs(yt - pa) / yt
    ape_b = np.abs(yt - pb) / yt
    diff = ape_a - ape_b  # 양수면 b 가 개선

    try:
        wstat, p_two = stats.wilcoxon(diff, alternative="two-sided")
        _, p_one = stats.wilcoxon(diff, alternative="greater")
    except ValueError as e:
        wstat, p_two, p_one = float("nan"), float("nan"), float("nan")
        logger.warning("wilcoxon fail (%s vs %s): %s", label_a, label_b, e)

    d_z = float(np.mean(diff) / np.std(diff, ddof=1)) if np.std(diff, ddof=1) > 0 else 0.0

    rng = np.random.default_rng(RANDOM_SEED)
    n = len(yt)
    if groups is not None:
        valid_groups = groups[valid]
        unique_groups = np.unique(valid_groups)
        idx_by_group = {g: np.where(valid_groups == g)[0] for g in unique_groups}
        n_g = len(unique_groups)
        diffs_md = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            chosen = rng.choice(n_g, size=n_g, replace=True)
            idx = np.concatenate([idx_by_group[unique_groups[c]] for c in chosen])
            diffs_md[i] = (np.median(ape_a[idx]) - np.median(ape_b[idx])) * 100
        method = "paired cluster (artist) bootstrap"
    else:
        diffs_md = np.empty(N_BOOTSTRAP)
        for i in range(N_BOOTSTRAP):
            idx = rng.integers(0, n, size=n)
            diffs_md[i] = (np.median(ape_a[idx]) - np.median(ape_b[idx])) * 100
        method = "row-level paired bootstrap"

    return {
        "label": f"{label_a}_vs_{label_b}",
        "n": int(n),
        "mdape_a": float(np.median(ape_a) * 100),
        "mdape_b": float(np.median(ape_b) * 100),
        "delta_pp": float(np.median(ape_a) * 100 - np.median(ape_b) * 100),
        "wilcoxon": {
            "statistic": float(wstat) if not np.isnan(wstat) else None,
            "p_two_sided": float(p_two) if not np.isnan(p_two) else None,
            "p_one_sided_a_gt_b": float(p_one) if not np.isnan(p_one) else None,
        },
        "cohens_d_z": d_z,
        "paired_bootstrap_ci": {
            "method": method,
            "delta_pp": float(np.median(diffs_md)),
            "ci_low": float(np.percentile(diffs_md, 2.5)),
            "ci_high": float(np.percentile(diffs_md, 97.5)),
        },
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드 (v3-filtered 28,376 row)
    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X_v1, y, groups = prepare_features_v1(df)
    logger.info("v1 features: %d (CB_FEATURES 32 + 5 extra). Data: n=%d", X_v1.shape[1], len(df))

    # v2 (tuned) OOF — production
    oof = np.load(OOF_PATH, allow_pickle=True)
    y_actual_ln = oof["y_actual_ln"]
    cb_v2_gkf_ln = oof["cb_preds_gkf_ln"]
    xgb_v2_gkf_ln = oof["xgb_preds_gkf_ln"]
    y_warm_ln = oof["y_warm_actual_ln"]
    cb_v2_kf_ln = oof["cb_preds_kf_ln"]
    xgb_v2_kf_ln = oof["xgb_preds_kf_ln"]
    np.testing.assert_allclose(y, y_actual_ln, rtol=1e-10)

    # v1 학습 (37 features + default hp)
    overall_start = time.time()
    logger.info("=== v1 spec GroupKFold OOF (cold) ===")
    cb_v1_gkf_ln, xgb_v1_gkf_ln = _train_v1_oof_groupkfold(X_v1, y, groups)
    logger.info("=== v1 spec KFold OOF (warm) ===")
    wmask = _warm_mask(groups)
    X_v1_warm = X_v1.iloc[wmask].reset_index(drop=True)
    y_warm_check = y[wmask]
    np.testing.assert_allclose(y_warm_check, y_warm_ln, rtol=1e-10)
    cb_v1_kf_ln, xgb_v1_kf_ln = _train_v1_oof_kfold_warm(X_v1_warm, y_warm_check)
    train_wall = time.time() - overall_start
    logger.info("v1 학습 완료 (%.0fs)", train_wall)

    # 가격 변환 + ensemble
    y_full_price = np.exp(y)
    y_warm_price = np.exp(y_warm_ln)

    cb_v1_cold = np.exp(cb_v1_gkf_ln)
    xgb_v1_cold = np.exp(xgb_v1_gkf_ln)
    ens_v1_cold = np.exp((cb_v1_gkf_ln + xgb_v1_gkf_ln) / 2)

    cb_v2_cold = np.exp(cb_v2_gkf_ln)
    xgb_v2_cold = np.exp(xgb_v2_gkf_ln)
    ens_v2_cold = np.exp((cb_v2_gkf_ln + xgb_v2_gkf_ln) / 2)

    cb_v1_warm = np.exp(cb_v1_kf_ln)
    xgb_v1_warm = np.exp(xgb_v1_kf_ln)
    ens_v1_warm = np.exp((cb_v1_kf_ln + xgb_v1_kf_ln) / 2)

    cb_v2_warm = np.exp(cb_v2_kf_ln)
    xgb_v2_warm = np.exp(xgb_v2_kf_ln)
    ens_v2_warm = np.exp((cb_v2_kf_ln + xgb_v2_kf_ln) / 2)

    # paired tests: v1 vs v2 (정식 1.2)
    cold_results = [
        paired_test(y_full_price, cb_v1_cold, cb_v2_cold, "v1_cb", "v2_cb", groups),
        paired_test(y_full_price, xgb_v1_cold, xgb_v2_cold, "v1_xgb", "v2_xgb", groups),
        paired_test(y_full_price, ens_v1_cold, ens_v2_cold, "v1_ens", "v2_ens", groups),
    ]
    groups_warm = groups[wmask]
    warm_results_row = [
        paired_test(y_warm_price, cb_v1_warm, cb_v2_warm, "v1_cb", "v2_cb"),
        paired_test(y_warm_price, xgb_v1_warm, xgb_v2_warm, "v1_xgb", "v2_xgb"),
        paired_test(y_warm_price, ens_v1_warm, ens_v2_warm, "v1_ens", "v2_ens"),
    ]
    warm_results_cluster = [
        paired_test(y_warm_price, cb_v1_warm, cb_v2_warm, "v1_cb", "v2_cb_cluster", groups_warm),
        paired_test(
            y_warm_price, xgb_v1_warm, xgb_v2_warm, "v1_xgb", "v2_xgb_cluster", groups_warm
        ),
        paired_test(
            y_warm_price, ens_v1_warm, ens_v2_warm, "v1_ens", "v2_ens_cluster", groups_warm
        ),
    ]

    summary = {
        "config": {
            "scope": (
                "공통 28,376 row 위에서 reconstructed v1-like spec (CB_FEATURES + 5 extra "
                "train/serve-drift features + default hp) vs v2 (production tuned) paired close. "
                "이는 'exact historical v1 vs v2' 의 정식 종결이 아니라 'reconstructed v1-like vs v2 "
                "paired close' (codex v3.2-2 P1). v2 변경 중 (a) 5 features 제거 + (b) Optuna tuning "
                "의 결합 효과만 isolated. 입체 985 필터 효과 + 진정한 v1 spec (29,361 row) 은 row "
                "schema mismatch 로 paired 불가능 → v3.3 backlog (release-level v1→v2 총효과 + "
                "exact historical v1 reproduction)."
            ),
            "v1_features": V1_FEATURES,
            "v1_cat_features": V1_CAT_FEATURES,
            "v1_hp": {
                "catboost": DEFAULT_CB_PARAMS,
                "xgboost": DEFAULT_XGB_PARAMS,
            },
            "v2_hp_source": "model_test_results/integrated_v3_filtered_tuned_best_params.json",
            "n_bootstrap": N_BOOTSTRAP,
            "rng_seed": RANDOM_SEED,
            "scope_caveat": (
                "본 v1 재현은 'CB_FEATURES + 5 extra + default hp' = v2 가 도입한 변경 중 (a) "
                "5 features 제거 + (b) Optuna tuning 효과의 결합. (c) 입체 985 필터 효과는 "
                "isolated 안 됨 (v3.3 backlog: 29,361 vs 28,376 비교 — row mismatch 로 paired 불가)."
            ),
            "framing_guide": (
                "Cold 결과 (cluster CI 모두 0 포함): 'v2 가 방향성상 소폭 우세 (점추정 +0.05 ~ "
                "+0.76%p) 하나 cold 개선의 artist-cluster 일반화 증거는 부족 → 현 단계에선 구분 "
                "불가' 가 정확한 framing (codex v3.2-2 P2). 'noise 가능성' 까지 가능하나 단정 "
                "회피. Wilcoxon p<0.0001 은 표본 크기 효과 — cluster CI 가 의사결정 기준."
            ),
        },
        "cold_groupkfold_paired": cold_results,
        "warm_kfold_paired_row": warm_results_row,
        "warm_kfold_paired_cluster": warm_results_cluster,
        "wall_seconds_total": float(train_wall),
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("JSON 저장: %s", OUT_JSON)

    print("\n" + "=" * 110)
    print("v3.2-2 v1 historical paired Wilcoxon (정식 1.2 close)")
    print("=" * 110)
    print(
        f"\n{'Comparison':<35} {'n':>6} {'v1 MdAPE':>9} {'v2 MdAPE':>9} {'Δ %p':>8} "
        f"{'Wilcoxon p':>11} {'d_z':>7} {'95% CI Δ':>22}"
    )
    print("-" * 110)
    for r in cold_results + warm_results_row + warm_results_cluster:
        if r.get("skipped"):
            continue
        wp = r["wilcoxon"]["p_two_sided"]
        ci = r["paired_bootstrap_ci"]
        print(
            f"{r['label']:<35} {r['n']:>6} {r['mdape_a']:>8.2f}% {r['mdape_b']:>8.2f}% "
            f"{r['delta_pp']:>+7.2f}%p "
            f"{wp:>10.4f} {r['cohens_d_z']:>+7.3f} "
            f"[{ci['ci_low']:>+5.2f}, {ci['ci_high']:>+5.2f}]"
        )

    print(f"\nTotal wall: {train_wall:.0f}s ({train_wall / 60:.1f} min)")
    print(f"저장: {OUT_JSON}")


if __name__ == "__main__":
    main()
