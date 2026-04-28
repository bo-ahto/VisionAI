"""1차 시장(A 모델) v3-filtered 하이퍼파라미터 튜닝.

배경:
- 본 PR(`feature/primary-train-tuning`) 직전 PR #13 (`v3-filtered`) 머지로
  재학습 파이프라인은 확보됐으나 default hyperparameter로 v3 baseline 대비
  성능 약간 하락 (GroupKFold MdAPE 38.7→40.8, KFold 13.8→15.7).
- 본 스크립트는 Optuna로 CatBoost+XGBoost hyperparameter 튜닝 후 v3 동등 이상
  성능을 회복하는 것이 목표.

산출물:
- model_test_results/integrated_v3_filtered_tuned_catboost.cbm
- model_test_results/integrated_v3_filtered_tuned_xgboost.json
- model_test_results/integrated_v3_filtered_tuned_xgboost_label_maps.json
- model_test_results/integrated_v3_filtered_tuned_metrics.json
- model_test_results/integrated_v3_filtered_tuned_best_params.json

Usage:
    PYTHONPATH=src python3 scripts/tune_primary_market_v3_filtered.py
    PYTHONPATH=src python3 scripts/tune_primary_market_v3_filtered.py --trials 50
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold, KFold

# 같은 디렉토리의 train 스크립트에서 helper 임포트
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_primary_market_v3_filtered import (
    CB_FEATURES, CAT_FEATURES, _cb_pool, _label_encode_xgb,
    _mdape, _summary, load_data, prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "model_test_results"


# ─── Optuna objectives ──────────────────────────────────────────────
def _cb_groupkfold_mdape(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, params: dict, n_splits: int = 3,
) -> float:
    """CatBoost GroupKFold MdAPE (price 기준, %).

    Codex 4차 P1: Optuna objective도 leakage 제거 — eval_set/early_stopping 사용 시
    test labels가 iteration 선택에 leak. tuned 'iterations' suggested 그대로 사용.
    """
    gkf = GroupKFold(n_splits=n_splits)
    preds = np.zeros(len(y))
    for tr, te in gkf.split(X, y, groups):
        cb = CatBoostRegressor(
            **params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        preds[te] = cb.predict(_cb_pool(X.iloc[te]))
    y_price = np.exp(y)
    pred_price = np.exp(preds)
    return _mdape(y_price, pred_price)


# XGBoost 튜닝/평가는 warm slice만 (PrimaryPredictor 라우팅: training_count>=5)
WARM_MIN_COUNT = 5


def _warm_mask(groups: np.ndarray) -> np.ndarray:
    """artist별 작품 수 >= WARM_MIN_COUNT 인 행만 True."""
    counts = pd.Series(groups).value_counts()
    warm_set = set(counts[counts >= WARM_MIN_COUNT].index)
    return np.array([g in warm_set for g in groups])


def _xgb_kfold_mdape(
    X: pd.DataFrame, y: np.ndarray, params: dict, n_splits: int = 3,
) -> float:
    """XGBoost KFold MdAPE.

    Codex review: warm slice(training_count>=5)에서만 평가해야 production 라우팅과 일치.
    호출부에서 X, y는 이미 warm-filter 통과된 슬라이스로 받는다.
    """
    # Codex 4차 P1: Optuna XGBoost objective도 leakage 제거
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    preds = np.zeros(len(y))
    n_rounds = params.pop("num_boost_round", 1000)
    for tr, te in kf.split(X):
        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        m = xgb.train(
            params={**params, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=n_rounds,
        )  # no evals/early_stopping
        preds[te] = m.predict(dtest)
    y_price = np.exp(y)
    pred_price = np.exp(preds)
    return _mdape(y_price, pred_price)


def _objective_cb(trial, X, y, groups) -> float:
    params = {
        "iterations": trial.suggest_int("iterations", 1000, 3000, step=500),
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.1, log=True),
        "depth": trial.suggest_int("depth", 4, 8),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0, log=True),
        "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
    }
    return _cb_groupkfold_mdape(X, y, groups, params)


def _objective_xgb(trial, X, y) -> float:
    """XGBoost는 warm artists 대상 → KFold MdAPE 최소화."""
    params = {
        "num_boost_round": trial.suggest_int("num_boost_round", 1000, 3000, step=500),
        "eta": trial.suggest_float("eta", 0.02, 0.1, log=True),
        "max_depth": trial.suggest_int("max_depth", 4, 8),
        "gamma": trial.suggest_float("gamma", 0.0, 5.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 5.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 5.0),
        "subsample": trial.suggest_float("subsample", 0.7, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
    }
    return _xgb_kfold_mdape(X, y, params)


# ─── 최종 학습 + 메트릭 (5-fold, train_primary_market_v3_filtered와 같은 형식) ───
def _final_cv_groupkfold_5(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cb_params: dict, xgb_params: dict,
) -> dict:
    """확정된 best params로 5-fold GroupKFold (train 스크립트와 동일 메트릭).

    Codex P1 (2026-04-28): early stopping leakage 제거 — eval_set 사용 시 test labels가
    iteration 선택에 leak. tuned 'iterations' 그대로 사용 (production tune 검증 완료).
    """
    gkf = GroupKFold(n_splits=5)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))  # no eval_set — leakage 방지
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
        )  # no evals/early_stopping — leakage 방지
        xgb_preds[te] = m.predict(dtest)

    y_price = np.exp(y)
    cb_pred = np.exp(cb_preds)
    xgb_pred = np.exp(xgb_preds)
    ens = np.exp((cb_preds + xgb_preds) / 2)
    n = len(y)
    out = {
        "baseline": _summary(y_price, np.full_like(y_price, np.median(y_price)), n),
        "catboost_v3_filtered_tuned": _summary(y_price, cb_pred, n),
        "xgboost_v3_filtered_tuned": _summary(y_price, xgb_pred, n),
        "ensemble": _summary(y_price, ens, n),
    }
    for src in sorted(set(source)):
        m_ = source == src
        if m_.sum() == 0:
            continue
        out[src] = {
            "baseline": _summary(y_price[m_], np.full_like(y_price[m_], np.median(y_price[m_])), int(m_.sum())),
            "catboost_v3_filtered_tuned": _summary(y_price[m_], cb_pred[m_], int(m_.sum())),
            "xgboost_v3_filtered_tuned": _summary(y_price[m_], xgb_pred[m_], int(m_.sum())),
            "ensemble": _summary(y_price[m_], ens[m_], int(m_.sum())),
        }
    return out


def _final_cv_kfold_5(
    X: pd.DataFrame, y: np.ndarray, cb_params: dict, xgb_params: dict,
    groups: np.ndarray | None = None, source: np.ndarray | None = None,
) -> dict:
    """5-fold KFold + warm slice (artist_count>=5) + by-source 분리 메트릭.

    서빙 라우팅과 정렬: warm은 XGBoost on artist_count>=5.
    """
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cb_preds = np.zeros(len(y))
    xgb_preds = np.zeros(len(y))
    for tr, te in kf.split(X):
        # Codex P1: leakage 방지 — eval_set / early_stopping 제거
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_preds[te] = cb.predict(_cb_pool(X.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_preds[te] = m.predict(dtest)
    y_price = np.exp(y)
    cb_pred = np.exp(cb_preds)
    xgb_pred = np.exp(xgb_preds)
    ens = np.exp((cb_preds + xgb_preds) / 2)
    n = len(y)
    out = {
        "catboost_v3_filtered_tuned": _summary(y_price, cb_pred, n),
        "xgboost_v3_filtered_tuned": _summary(y_price, xgb_pred, n),
        "ensemble": _summary(y_price, ens, n),
    }
    if source is not None:
        for src in sorted(set(source)):
            m_ = source == src
            if m_.sum() == 0:
                continue
            out[src] = {
                "catboost_v3_filtered_tuned": _summary(y_price[m_], cb_pred[m_], int(m_.sum())),
                "xgboost_v3_filtered_tuned": _summary(y_price[m_], xgb_pred[m_], int(m_.sum())),
                "ensemble": _summary(y_price[m_], ens[m_], int(m_.sum())),
            }
    if groups is not None:
        wmask = _warm_mask(groups)
        n_warm = int(wmask.sum())
        if n_warm > 0:
            out["warm_slice"] = {
                "n": n_warm,
                "n_artists": int(pd.Series(groups[wmask]).nunique()),
                "catboost_v3_filtered_tuned": _summary(y_price[wmask], cb_pred[wmask], n_warm),
                "xgboost_v3_filtered_tuned": _summary(y_price[wmask], xgb_pred[wmask], n_warm),
                "ensemble": _summary(y_price[wmask], ens[wmask], n_warm),
            }
            if source is not None:
                for src in sorted(set(source)):
                    smask = wmask & (source == src)
                    if smask.sum() == 0:
                        continue
                    out["warm_slice"][src] = {
                        "catboost_v3_filtered_tuned": _summary(y_price[smask], cb_pred[smask], int(smask.sum())),
                        "xgboost_v3_filtered_tuned": _summary(y_price[smask], xgb_pred[smask], int(smask.sum())),
                        "ensemble": _summary(y_price[smask], ens[smask], int(smask.sum())),
                    }
    return out


def _train_final(X: pd.DataFrame, y: np.ndarray, cb_params: dict, xgb_params: dict):
    cb = CatBoostRegressor(
        **cb_params, loss_function="RMSE", verbose=100, random_seed=42,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X, y))

    Xe, _, label_maps = _label_encode_xgb(X, X.iloc[:1])
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
    xgbm = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
    )
    return cb, xgbm, label_maps


# ─── main ────────────────────────────────────────────────────────────
def main(n_trials: int) -> None:
    logger.info("=" * 60)
    logger.info("v3-filtered hyperparameter tuning (Optuna, %d trials per model)", n_trials)
    logger.info("=" * 60)

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    logger.info("Data: %d rows, %d artists, %d features", len(df), len(set(groups)), len(CB_FEATURES))

    # CatBoost 튜닝
    logger.info("--- CatBoost study ---")
    cb_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    cb_study.optimize(lambda t: _objective_cb(t, X, y, groups), n_trials=n_trials, show_progress_bar=False)
    cb_best = dict(cb_study.best_params)
    logger.info("CatBoost best MdAPE: %.2f%%", cb_study.best_value)
    logger.info("CatBoost best params: %s", cb_best)

    # XGBoost 튜닝 (warm 슬라이스: artist 작품 수 >= 5, primary_predictor 라우팅 일치)
    warm_mask = _warm_mask(groups)
    X_warm = X.iloc[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    n_warm = int(warm_mask.sum())
    n_warm_artists = int(pd.Series(groups[warm_mask]).nunique())
    logger.info("--- XGBoost study (KFold, warm slice: %d works, %d artists) ---",
                n_warm, n_warm_artists)
    xgb_study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    xgb_study.optimize(lambda t: _objective_xgb(t, X_warm, y_warm),
                       n_trials=n_trials, show_progress_bar=False)
    xgb_best = dict(xgb_study.best_params)
    logger.info("XGBoost best MdAPE (warm KFold): %.2f%%", xgb_study.best_value)
    logger.info("XGBoost best params: %s", xgb_best)

    # 최종 5-fold CV 메트릭
    # CatBoost는 cold(GroupKFold) 전체에서 평가, XGBoost는 warm(KFold) slice에서 평가
    logger.info("--- Final 5-fold CV with best params ---")
    gkf_metrics = _final_cv_groupkfold_5(X, y, groups, source, cb_best, xgb_best)
    # KFold는 warm slice로 평가 (라우팅 일치) + by-source 분리
    warm_groups = groups[warm_mask]
    warm_source = source[warm_mask]
    kf_metrics = _final_cv_kfold_5(X_warm, y_warm, cb_best, xgb_best,
                                    groups=warm_groups, source=warm_source)
    kf_metrics["_note"] = (
        f"Evaluated on warm slice only ({n_warm} works, {n_warm_artists} artists, "
        f"artist 작품수>={WARM_MIN_COUNT})"
    )

    # 전체 데이터로 최종 학습 — CatBoost는 전체, XGBoost는 warm slice (라우팅 일치)
    logger.info("--- Final training on full data ---")
    cb_final = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=100, random_seed=42, allow_writing_files=False,
    )
    cb_final.fit(_cb_pool(X, y))

    Xe_warm, _, label_maps = _label_encode_xgb(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    xgb_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )

    # 저장
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cb_final.save_model(str(OUT_DIR / "integrated_v3_filtered_tuned_catboost.cbm"))
    xgb_final.save_model(str(OUT_DIR / "integrated_v3_filtered_tuned_xgboost.json"))
    with (OUT_DIR / "integrated_v3_filtered_tuned_xgboost_label_maps.json").open("w") as f:
        json.dump(label_maps, f, ensure_ascii=False, indent=2)
    with (OUT_DIR / "integrated_v3_filtered_tuned_best_params.json").open("w") as f:
        json.dump({"catboost": cb_best, "xgboost": xgb_best}, f, ensure_ascii=False, indent=2)
    # Codex 5차 P1: 학습 시 warm artist slug list 저장 → 서빙 라우팅이 동일 기준 사용
    # (DB의 raw training_count가 학습 데이터 필터 후 count와 안 맞아 32명 미스라우팅 가능)
    warm_artists_set = sorted(set(groups[warm_mask].tolist()))
    with (OUT_DIR / "integrated_v3_filtered_tuned_warm_artists.json").open("w") as f:
        json.dump({
            "warm_artist_slugs": warm_artists_set,
            "n_artists": len(warm_artists_set),
            "n_warm_works": int(warm_mask.sum()),
            "min_count": int(WARM_MIN_COUNT),
            "note": "학습 시 artist_count>=5 (filtered) 작가 목록. 서빙 라우팅 시 lookup",
        }, f, ensure_ascii=False, indent=2)
    logger.info("Warm artist list saved: %d artists, %d works", len(warm_artists_set), int(warm_mask.sum()))
    metrics_doc = {
        "model": "integrated_v3_filtered_tuned",
        "data": f"{len(df)} = filtered from 29361 (excluded 985), tuning n_trials={n_trials}",
        "features": len(CB_FEATURES),
        "artists": int(len(set(groups))),
        "best_params": {"catboost": cb_best, "xgboost": xgb_best},
        "tuning_best_mdape": {
            "catboost_3fold": round(cb_study.best_value, 2),
            "xgboost_3fold": round(xgb_study.best_value, 2),
        },
        "groupkfold": gkf_metrics,
        "kfold": kf_metrics,
        "label_maps": label_maps,
    }
    with (OUT_DIR / "integrated_v3_filtered_tuned_metrics.json").open("w") as f:
        json.dump(metrics_doc, f, ensure_ascii=False, indent=2)

    logger.info("=" * 60)
    logger.info("Tuning complete")
    logger.info("=" * 60)
    logger.info("v3 baseline:           GroupKFold MdAPE 38.7%%, KFold 13.8%%")
    logger.info("v3-filtered (default): GroupKFold MdAPE 40.8%%, KFold 15.7%%")
    logger.info("v3-filtered (tuned):   GroupKFold MdAPE %.1f%%, KFold %.1f%%",
                gkf_metrics["ensemble"]["MdAPE"], kf_metrics["ensemble"]["MdAPE"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=30, help="Optuna trials per model (default 30)")
    args = p.parse_args()
    main(args.trials)
