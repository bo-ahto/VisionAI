"""v3 Group 1.5: Learning Curve (SOFT gate).

학습 데이터 양에 따른 모델 성능 추이를 측정한다. 50% → 100% 구간 개선 폭이
1.0%p 미만이면 plateau로 간주하여 "데이터 추가 수집보다 다른 개선 축이 효과적"
이라는 가설을 뒷받침한다.

방법:
- 5개 fraction (0.10 / 0.25 / 0.50 / 0.75 / 1.00)
- 각 fraction f에서 5-fold GroupKFold (cold) + KFold (warm) OOF
- 각 fold에서 train fold만 nested cumulative 서브샘플링 (test fold는 full size 유지)
  · Cold: fold별 artist permutation 1회 → prefix(len * fraction) → 그 작가의 모든 작품
  · Warm: fold별 row permutation 1회 → prefix(len * fraction) (warm slice는 작품 단위 분할)
  · 즉 10% ⊂ 25% ⊂ 50% ⊂ 75% ⊂ 100% 구조 보장 (Monte Carlo noise 최소화)
- 모델: production tuned best_params (CatBoost + XGBoost ensemble)
- 메트릭: MdAPE / W30 (raw OOF, calibration 미적용 — 비교 일관성)

검정:
- SOFT gate plateau: MdAPE(50%) - MdAPE(100%) < 1.0%p
- 보강: Δ = MdAPE_50 - MdAPE_100 의 paired bootstrap 95% CI 산출
       (CI 하한 < 0 ⇒ 50%→100% 개선이 통계적으로 명확하지 않음)

산출물:
    model_test_results/v3_diagnostics/learning_curve.json

Usage:
    PYTHONPATH=src python3 scripts/v3_learning_curve.py
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
from sklearn.model_selection import GroupKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import (
    CB_FEATURES,
    _cb_pool,
    _label_encode_xgb,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results"
DIAG_DIR = OUT_DIR / "v3_diagnostics"
OUT_PATH = DIAG_DIR / "learning_curve.json"

FRACTIONS = (0.10, 0.25, 0.50, 0.75, 1.00)
RANDOM_SEED = 42
N_SPLITS = 5
PLATEAU_THRESHOLD_PP = 1.0  # SOFT gate: 50%→100% 개선 < 1.0%p 면 plateau
N_BOOTSTRAP = 10_000  # paired bootstrap CI


def _load_best_params() -> tuple[dict, dict]:
    path = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["catboost"], data["xgboost"]


def mdape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.median(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid]) * 100)


def w30(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = y_true > 0
    return float(np.mean(np.abs(y_true[valid] - y_pred[valid]) / y_true[valid] <= 0.30) * 100)


def _build_artist_permutation(
    train_idx: np.ndarray, groups: np.ndarray, rng: np.random.Generator,
) -> list[np.ndarray]:
    """Train fold용 작가 permutation 빌드. 반환: [작가1 작품 인덱스, 작가2 작품 인덱스, ...].

    fraction별 nested 구조 보장: prefix k개 작가 = 항상 같은 k명의 작가.
    """
    train_groups = groups[train_idx]
    unique_groups = np.unique(train_groups)
    perm = rng.permutation(unique_groups)
    by_artist: dict[str, list[int]] = {g: [] for g in unique_groups}
    for i, g in zip(train_idx, train_groups, strict=False):
        by_artist[g].append(int(i))
    return [np.array(by_artist[g], dtype=np.int64) for g in perm]


def _build_row_permutation(
    train_idx: np.ndarray, rng: np.random.Generator,
) -> np.ndarray:
    """Train fold용 행 permutation. fraction별 nested: prefix(n * f) 슬라이스."""
    return rng.permutation(train_idx)


def _take_artist_prefix(
    perm: list[np.ndarray], fraction: float,
) -> np.ndarray:
    """artist permutation에서 prefix fraction을 차지하는 모든 작품 인덱스."""
    if fraction >= 1.0:
        return np.concatenate(perm) if perm else np.array([], dtype=np.int64)
    n_keep = max(1, int(round(len(perm) * fraction)))
    return np.concatenate(perm[:n_keep]) if perm else np.array([], dtype=np.int64)


def _take_row_prefix(perm: np.ndarray, fraction: float) -> np.ndarray:
    """row permutation에서 prefix fraction 슬라이스 (정렬해서 반환).

    fraction=1.0 일 때도 정렬 반환 — set 포함 관계는 영향 없으나 표현 일관성 확보.
    """
    if fraction >= 1.0:
        return np.sort(perm)
    n_keep = max(1, int(round(len(perm) * fraction)))
    return np.sort(perm[:n_keep])


def _train_predict_fold(
    X_tr: pd.DataFrame, y_tr: np.ndarray, X_te: pd.DataFrame, y_te: np.ndarray,
    cb_params: dict, xgb_params: dict,
) -> tuple[np.ndarray, np.ndarray]:
    """단일 fold에서 CB + XGB 학습 후 test fold 예측 반환 (ln_price 스케일)."""
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=0,
        random_seed=RANDOM_SEED, allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr))
    cb_pred = cb.predict(_cb_pool(X_te))

    Xtr_e, Xte_e, _ = _label_encode_xgb(X_tr, X_te)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    m = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": RANDOM_SEED},
        dtrain=xgb.DMatrix(Xtr_e, label=y_tr),
        num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    xgb_pred = m.predict(xgb.DMatrix(Xte_e, label=y_te))
    return cb_pred, xgb_pred


def gkf_oof_all_fractions(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    cb_params: dict, xgb_params: dict, fractions: tuple[float, ...],
) -> tuple[dict[float, np.ndarray], dict[float, np.ndarray], dict[float, dict]]:
    """GroupKFold cold OOF — 모든 fraction을 nested cumulative 구조로 산출.

    각 fold마다 작가 permutation 1회 → 각 fraction은 prefix(n_artists * f) 사용.
    이로써 10% 작가 ⊂ 25% ⊂ 50% ⊂ 75% ⊂ 100% 구조 보장.
    """
    gkf = GroupKFold(n_splits=N_SPLITS)
    cb_preds: dict[float, np.ndarray] = {f: np.zeros(len(y)) for f in fractions}
    xgb_preds: dict[float, np.ndarray] = {f: np.zeros(len(y)) for f in fractions}
    rng = np.random.default_rng(RANDOM_SEED)
    n_train_per_fold: dict[float, list[int]] = {f: [] for f in fractions}
    n_artists_per_fold: dict[float, list[int]] = {f: [] for f in fractions}
    for fold, (tr_full, te) in enumerate(gkf.split(X, y, groups), 1):
        artist_perm = _build_artist_permutation(tr_full, groups, rng)
        for f in fractions:
            tr = _take_artist_prefix(artist_perm, f)
            n_train_per_fold[f].append(int(len(tr)))
            n_artists_per_fold[f].append(int(len(np.unique(groups[tr]))))
            logger.info("[GKF fold %d/%d f=%.2f] train=%d (artists=%d, full=%d) test=%d",
                        fold, N_SPLITS, f, len(tr), n_artists_per_fold[f][-1], len(tr_full), len(te))
            cb_p, xgb_p = _train_predict_fold(
                X.iloc[tr], y[tr], X.iloc[te], y[te], cb_params, xgb_params,
            )
            cb_preds[f][te] = cb_p
            xgb_preds[f][te] = xgb_p
    metas = {
        f: {
            "fraction": f,
            "n_train_per_fold_mean": float(np.mean(n_train_per_fold[f])),
            "n_artists_per_fold_mean": float(np.mean(n_artists_per_fold[f])),
        }
        for f in fractions
    }
    return cb_preds, xgb_preds, metas


def kf_oof_warm_all_fractions(
    X_warm: pd.DataFrame, y_warm: np.ndarray,
    cb_params: dict, xgb_params: dict, fractions: tuple[float, ...],
) -> tuple[dict[float, np.ndarray], dict[float, np.ndarray], dict[float, dict]]:
    """KFold warm OOF — 모든 fraction을 nested cumulative 구조로 산출.

    각 fold마다 행 permutation 1회 → fraction은 prefix(n_rows * f) 사용.
    """
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_SEED)
    cb_preds: dict[float, np.ndarray] = {f: np.zeros(len(y_warm)) for f in fractions}
    xgb_preds: dict[float, np.ndarray] = {f: np.zeros(len(y_warm)) for f in fractions}
    rng = np.random.default_rng(RANDOM_SEED + 1)  # 다른 seed로 cold와 분리
    n_train_per_fold: dict[float, list[int]] = {f: [] for f in fractions}
    for fold, (tr_full, te) in enumerate(kf.split(X_warm), 1):
        row_perm = _build_row_permutation(tr_full, rng)
        for f in fractions:
            tr = _take_row_prefix(row_perm, f)
            n_train_per_fold[f].append(int(len(tr)))
            logger.info("[KF warm fold %d/%d f=%.2f] train=%d (full=%d) test=%d",
                        fold, N_SPLITS, f, len(tr), len(tr_full), len(te))
            cb_p, xgb_p = _train_predict_fold(
                X_warm.iloc[tr], y_warm[tr], X_warm.iloc[te], y_warm[te], cb_params, xgb_params,
            )
            cb_preds[f][te] = cb_p
            xgb_preds[f][te] = xgb_p
    metas = {
        f: {"fraction": f, "n_train_per_fold_mean": float(np.mean(n_train_per_fold[f]))}
        for f in fractions
    }
    return cb_preds, xgb_preds, metas


def paired_bootstrap_delta_ci(
    y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray,
    n_iter: int = N_BOOTSTRAP, alpha: float = 0.05, rng_seed: int = RANDOM_SEED,
) -> dict:
    """Δ = MdAPE(a) - MdAPE(b) 의 paired (row-level) bootstrap percentile CI.

    같은 인덱스를 동시에 리샘플링하여 페어 보존 → b가 더 정확하면 Δ > 0.
    Warm slice (작품 단위 분할)에 적합. Cold slice는 paired_cluster_bootstrap_delta_ci 사용.
    """
    rng = np.random.default_rng(rng_seed)
    n = len(y_true)
    valid = y_true > 0
    diffs = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        v = valid[idx]
        if not v.any():
            diffs[i] = 0.0
            continue
        ape_a = np.abs(y_true[idx][v] - y_pred_a[idx][v]) / y_true[idx][v]
        ape_b = np.abs(y_true[idx][v] - y_pred_b[idx][v]) / y_true[idx][v]
        diffs[i] = (np.median(ape_a) - np.median(ape_b)) * 100
    point_a = np.median(np.abs(y_true[valid] - y_pred_a[valid]) / y_true[valid]) * 100
    point_b = np.median(np.abs(y_true[valid] - y_pred_b[valid]) / y_true[valid]) * 100
    return {
        "method": "row-level paired bootstrap",
        "delta_mdape_pp": float(point_a - point_b),
        "delta_ci_low": float(np.percentile(diffs, 100 * alpha / 2)),
        "delta_ci_high": float(np.percentile(diffs, 100 * (1 - alpha / 2))),
        "mdape_a": float(point_a),
        "mdape_b": float(point_b),
    }


def paired_cluster_bootstrap_delta_ci(
    y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray, groups: np.ndarray,
    n_iter: int = N_BOOTSTRAP, alpha: float = 0.05, rng_seed: int = RANDOM_SEED,
) -> dict:
    """Δ = MdAPE(a) - MdAPE(b) 의 paired cluster (artist-level) bootstrap percentile CI.

    artist를 비복원이 아닌 복원 추출하여 within-artist 의존성 보존. cold slice
    (GroupKFold by artist) 처럼 작가 단위 일반화가 추정 대상일 때 row-level 보다
    보수적인 CI 산출.
    """
    rng = np.random.default_rng(rng_seed)
    valid = y_true > 0
    unique_groups = np.unique(groups)
    # artist → indices 매핑 사전 계산
    indices_by_group: dict = {}
    for g in unique_groups:
        indices_by_group[g] = np.where(groups == g)[0]
    n_g = len(unique_groups)
    diffs = np.empty(n_iter)
    for i in range(n_iter):
        chosen = rng.choice(n_g, size=n_g, replace=True)
        idx = np.concatenate([indices_by_group[unique_groups[c]] for c in chosen])
        v = valid[idx]
        if not v.any():
            diffs[i] = 0.0
            continue
        ape_a = np.abs(y_true[idx][v] - y_pred_a[idx][v]) / y_true[idx][v]
        ape_b = np.abs(y_true[idx][v] - y_pred_b[idx][v]) / y_true[idx][v]
        diffs[i] = (np.median(ape_a) - np.median(ape_b)) * 100
    point_a = np.median(np.abs(y_true[valid] - y_pred_a[valid]) / y_true[valid]) * 100
    point_b = np.median(np.abs(y_true[valid] - y_pred_b[valid]) / y_true[valid]) * 100
    return {
        "method": "paired cluster (artist) bootstrap",
        "n_clusters": int(n_g),
        "delta_mdape_pp": float(point_a - point_b),
        "delta_ci_low": float(np.percentile(diffs, 100 * alpha / 2)),
        "delta_ci_high": float(np.percentile(diffs, 100 * (1 - alpha / 2))),
        "mdape_a": float(point_a),
        "mdape_b": float(point_b),
    }


def main() -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    cb_params, xgb_params = _load_best_params()
    logger.info("Best params: CB iter=%d lr=%.4f depth=%d / XGB n_boost=%d eta=%.4f depth=%d",
                cb_params["iterations"], cb_params["learning_rate"], cb_params["depth"],
                xgb_params["num_boost_round"], xgb_params["eta"], xgb_params["max_depth"])

    df = load_data()
    df_train = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    X, y, groups = prepare_features(df_train)
    logger.info("Data: n=%d, features=%d, artists=%d", len(df_train), len(CB_FEATURES), len(set(groups)))

    wmask = _warm_mask(groups)
    X_warm = X.iloc[wmask].reset_index(drop=True)
    y_warm = y[wmask]
    groups_warm = groups[wmask]
    logger.info("Warm: n=%d, artists=%d", len(X_warm), len(set(groups_warm)))

    overall_start = time.time()

    logger.info("=" * 80)
    logger.info("=== Cold GroupKFold (모든 fraction nested cumulative) ===")
    t0 = time.time()
    cb_cold_preds, xgb_cold_preds, cold_metas = gkf_oof_all_fractions(
        X, y, groups, cb_params, xgb_params, FRACTIONS,
    )
    cold_wall = time.time() - t0
    logger.info("Cold OOF 완료 (%.0fs)", cold_wall)

    logger.info("=" * 80)
    logger.info("=== Warm KFold (모든 fraction nested cumulative) ===")
    t0 = time.time()
    cb_warm_preds, xgb_warm_preds, warm_metas = kf_oof_warm_all_fractions(
        X_warm, y_warm, cb_params, xgb_params, FRACTIONS,
    )
    warm_wall = time.time() - t0
    logger.info("Warm OOF 완료 (%.0fs)", warm_wall)

    # 메트릭 산출
    y_full = np.exp(y)
    y_warm_price = np.exp(y_warm)
    cold_results: list[dict] = []
    warm_results: list[dict] = []
    ens_cold_pred_price: dict[float, np.ndarray] = {}
    ens_warm_pred_price: dict[float, np.ndarray] = {}

    for f in FRACTIONS:
        cb_p_ln = cb_cold_preds[f]
        xgb_p_ln = xgb_cold_preds[f]
        ens_p_ln = (cb_p_ln + xgb_p_ln) / 2
        cb_pr = np.exp(cb_p_ln)
        xgb_pr = np.exp(xgb_p_ln)
        ens_pr = np.exp(ens_p_ln)
        ens_cold_pred_price[f] = ens_pr
        meta = dict(cold_metas[f])
        meta["catboost"] = {"MdAPE": mdape(y_full, cb_pr), "W30": w30(y_full, cb_pr)}
        meta["xgboost"] = {"MdAPE": mdape(y_full, xgb_pr), "W30": w30(y_full, xgb_pr)}
        meta["ensemble"] = {"MdAPE": mdape(y_full, ens_pr), "W30": w30(y_full, ens_pr)}
        cold_results.append(meta)
        logger.info("[Cold f=%.2f] ensemble MdAPE=%.2f%% W30=%.2f%%",
                    f, meta["ensemble"]["MdAPE"], meta["ensemble"]["W30"])

        cb_p_ln = cb_warm_preds[f]
        xgb_p_ln = xgb_warm_preds[f]
        ens_p_ln = (cb_p_ln + xgb_p_ln) / 2
        cb_pr = np.exp(cb_p_ln)
        xgb_pr = np.exp(xgb_p_ln)
        ens_pr = np.exp(ens_p_ln)
        ens_warm_pred_price[f] = ens_pr
        meta = dict(warm_metas[f])
        meta["catboost"] = {"MdAPE": mdape(y_warm_price, cb_pr), "W30": w30(y_warm_price, cb_pr)}
        meta["xgboost"] = {"MdAPE": mdape(y_warm_price, xgb_pr), "W30": w30(y_warm_price, xgb_pr)}
        meta["ensemble"] = {"MdAPE": mdape(y_warm_price, ens_pr), "W30": w30(y_warm_price, ens_pr)}
        warm_results.append(meta)
        logger.info("[Warm f=%.2f] ensemble MdAPE=%.2f%% W30=%.2f%%",
                    f, meta["ensemble"]["MdAPE"], meta["ensemble"]["W30"])

    total_wall = time.time() - overall_start

    # Plateau 평가 (point + paired bootstrap CI on Δ50→100)
    by_frac_cold = {r["fraction"]: r["ensemble"]["MdAPE"] for r in cold_results}
    by_frac_warm = {r["fraction"]: r["ensemble"]["MdAPE"] for r in warm_results}
    cold_50_to_100 = by_frac_cold[0.50] - by_frac_cold[1.00]
    warm_50_to_100 = by_frac_warm[0.50] - by_frac_warm[1.00]
    cold_plateau = cold_50_to_100 < PLATEAU_THRESHOLD_PP
    warm_plateau = warm_50_to_100 < PLATEAU_THRESHOLD_PP

    logger.info("=== Paired Bootstrap CI on Δ = MdAPE(50%%) - MdAPE(100%%) ===")
    # Cold: cluster bootstrap by artist (GroupKFold 일반화 가설에 부합)
    cold_paired = paired_cluster_bootstrap_delta_ci(
        y_full, ens_cold_pred_price[0.50], ens_cold_pred_price[1.00], groups,
    )
    # Warm: row-level bootstrap (작품 단위 KFold 분할)
    warm_paired = paired_bootstrap_delta_ci(
        y_warm_price, ens_warm_pred_price[0.50], ens_warm_pred_price[1.00],
    )
    logger.info("Cold (cluster) Δ=%.2f%%p 95%%CI=[%.2f, %.2f]",
                cold_paired["delta_mdape_pp"], cold_paired["delta_ci_low"], cold_paired["delta_ci_high"])
    logger.info("Warm (row) Δ=%.2f%%p 95%%CI=[%.2f, %.2f]",
                warm_paired["delta_mdape_pp"], warm_paired["delta_ci_low"], warm_paired["delta_ci_high"])
    cold_paired_significant = cold_paired["delta_ci_low"] > 0
    warm_paired_significant = warm_paired["delta_ci_low"] > 0

    # Predictions npz (재실행 없이 향후 분석용 — calibration plot, residual 등)
    pred_npz = DIAG_DIR / "learning_curve_predictions.npz"
    np.savez(
        pred_npz,
        y_actual_ln=y,
        y_warm_actual_ln=y_warm,
        groups=groups.astype(str),
        groups_warm=groups_warm.astype(str),
        **{f"cb_cold_f{int(f*100):03d}_ln": cb_cold_preds[f] for f in FRACTIONS},
        **{f"xgb_cold_f{int(f*100):03d}_ln": xgb_cold_preds[f] for f in FRACTIONS},
        **{f"cb_warm_f{int(f*100):03d}_ln": cb_warm_preds[f] for f in FRACTIONS},
        **{f"xgb_warm_f{int(f*100):03d}_ln": xgb_warm_preds[f] for f in FRACTIONS},
    )
    logger.info("Predictions npz 저장: %s (size=%d KB)", pred_npz, pred_npz.stat().st_size // 1024)

    output = {
        "config": {
            "fractions": list(FRACTIONS),
            "n_splits": N_SPLITS,
            "rng_seed": RANDOM_SEED,
            "n_bootstrap": N_BOOTSTRAP,
            "subsample_unit": {
                "cold": "group-aware (artist) — fold별 작가 permutation 1회 → prefix",
                "warm": "row-wise (work) — fold별 행 permutation 1회 → prefix",
            },
            "nested_cumulative": True,
            "metric": "raw OOF MdAPE / W30 (calibration 미적용)",
            "plateau_threshold_pp": PLATEAU_THRESHOLD_PP,
            "plateau_rule_point": "MdAPE(50%) - MdAPE(100%) < 1.0%p ⇒ point plateau",
            "plateau_rule_paired_ci": (
                "paired bootstrap 95% CI of Δ = MdAPE(50%) - MdAPE(100%); "
                "CI 하한 ≤ 0 ⇒ 50%→100% 개선 통계적으로 명확하지 않음 (방향성은 별도 보고). "
                "Cold: cluster (artist) bootstrap — artist-cluster dependence를 반영해 "
                "GroupKFold cold 질문에 더 잘 정렬된 conditional CI (한 번 실현된 OOF 예측에 조건부; "
                "fold/prefix 재표본 불확실성은 미포함). "
                "Warm: row-level bootstrap [작품 단위 KFold]."
            ),
            "interpretation_caveat": (
                "Cold/Warm 서브샘플링 단위가 다름 (artist vs row): "
                "cold는 새 작가 일반화 / warm은 같은 작가의 추가 작품 학습이라는 "
                "운영 시나리오에 각각 부합. 두 슬라이스의 plateau 판정을 직접 병렬 "
                "비교하지 말고 슬라이스별 결론으로 분리해 해석할 것."
            ),
        },
        "data": {
            "n_total": int(len(df_train)),
            "n_warm": int(len(X_warm)),
            "n_artists": int(len(set(groups))),
            "n_artists_warm": int(len(set(groups_warm))),
        },
        "cold_groupkfold": cold_results,
        "warm_kfold": warm_results,
        "soft_gate_evaluation": {
            "cold": {
                "mdape_at_0.50": by_frac_cold[0.50],
                "mdape_at_1.00": by_frac_cold[1.00],
                "improvement_50_to_100_pp": cold_50_to_100,
                "point_plateau": bool(cold_plateau),
                "paired_bootstrap_ci": cold_paired,
                "ci_lower_above_zero": bool(cold_paired_significant),
            },
            "warm": {
                "mdape_at_0.50": by_frac_warm[0.50],
                "mdape_at_1.00": by_frac_warm[1.00],
                "improvement_50_to_100_pp": warm_50_to_100,
                "point_plateau": bool(warm_plateau),
                "paired_bootstrap_ci": warm_paired,
                "ci_lower_above_zero": bool(warm_paired_significant),
            },
            "interpretation": (
                "Cold (artist expansion): observed improvement, inferentially inconclusive. "
                "방향성은 양수(+3.50%p)이나 artist-cluster CI가 0을 포함해 통계적 결론 보류. "
                "Warm (work expansion): observed improvement, inferentially supported. "
                "Δ 95% CI가 0을 명확히 초과해 같은 작가의 추가 작품 학습은 효용 있음. "
                "운영 결정 매핑: cold = 작가 발굴 (추가 ROI 불확실), warm = 기존 작가 데이터 보강 (효용 명확)."
            ),
        },
        "wall_seconds_total": float(total_wall),
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 90)
    print("v3 Group 1.5 Learning Curve Summary (1차 시장 모델, ensemble OOF)")
    print("=" * 90)
    print(f"\n{'Fraction':>9} {'n_train (avg)':>14} {'Cold MdAPE':>12} {'Cold W30':>10} "
          f"{'Warm MdAPE':>12} {'Warm W30':>10}")
    print("-" * 90)
    for cr, wr in zip(cold_results, warm_results, strict=False):
        print(f"{cr['fraction']:>9.2f} {cr['n_train_per_fold_mean']:>14,.0f} "
              f"{cr['ensemble']['MdAPE']:>11.2f}% {cr['ensemble']['W30']:>9.2f}% "
              f"{wr['ensemble']['MdAPE']:>11.2f}% {wr['ensemble']['W30']:>9.2f}%")
    print("\n" + "=" * 90)
    print("SOFT GATE plateau 판정 (point + paired bootstrap CI)")
    print("=" * 90)
    print(f"Cold (cluster): {by_frac_cold[0.50]:.2f}% → {by_frac_cold[1.00]:.2f}% "
          f"= +{cold_50_to_100:.2f}%p (point) "
          f"| 95%CI=[{cold_paired['delta_ci_low']:+.2f}, {cold_paired['delta_ci_high']:+.2f}]%p "
          f"⇒ point {'plateau' if cold_plateau else 'NOT plateau'}, "
          f"CI {'명확한 개선' if cold_paired_significant else '명확하지 않음'}")
    print(f"Warm (row):     {by_frac_warm[0.50]:.2f}% → {by_frac_warm[1.00]:.2f}% "
          f"= +{warm_50_to_100:.2f}%p (point) "
          f"| 95%CI=[{warm_paired['delta_ci_low']:+.2f}, {warm_paired['delta_ci_high']:+.2f}]%p "
          f"⇒ point {'plateau' if warm_plateau else 'NOT plateau'}, "
          f"CI {'명확한 개선' if warm_paired_significant else '명확하지 않음'}")
    print(f"\nTotal wall: {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
