"""Confirmatory Cycle — Top 15 + XGBoost vs 32 + Ensemble (decision-binding ✓).

prereg = docs/confirmatory_prereg_20260509.md
Decision binding ✅ YES (운영 채택 결정 영역).

P0/P1 fix 적용 (코덱스 round 1 + 2):
1. Locked Holdout 20% 분리 (artist GroupShuffleSplit / random_state=20260509)
2. Top 15 ranking = 80% 내부 fold-internal 재산출 (selection leakage 방지)
3. Sweep ranking = reference only (binding X)
4. Binding = Top15+XGB vs 32+Ensemble (1 binary decision)
5. Diagnostic = 32+XGBoost (non-binding / record only)
6. CV-Holdout gap fail-safe (overfit detection)
7. Multi-seed warm (3 seeds: 42/7/13 / median primary)

Protocol:
Step 1. Holdout split (locked / 80/20 artist GroupShuffleSplit)
Step 2. 80% subset 내부 fold-internal 4-method ranking (5 fold)
Step 3. Top 15 features (80% ranking 영역 의 의무 영역 의 의무 alphabetical tie-break)
Step 4. 80% CV evaluation (cold GKF + warm KF 3-seed + warm GKF guard) — 3 configs
Step 5. 80% retrain + Holdout test (3 configs)
Step 6. Decision criterion + verdict
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _label_encode_xgb,
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "confirmatory_results.json"

# ─── Locked config ────────────────────────────────────────────────────
HOLDOUT_RANDOM_STATE = 20260509
HOLDOUT_FRACTION = 0.20
WARM_SEEDS = [42, 7, 13]
NOISE_SE_PP = 2.117  # Phase 0 cold ens fold std × 1
WARM_GAP_PP = 0.5

# Decision criteria (locked)
GUARD_LOCKED = {
    "G1_warm": 0.5,    # Δ warm ≤ +0.5
    "G2_cold": 0.8,    # Δ cold ≤ +0.8
    "G3_artsy": 1.0,   # Δ artsy cold ≤ +1.0
    "G4_saatchi": 1.0, # Δ saatchi cold ≤ +1.0
}


def _summary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {"n": len(y_true), "MdAPE": float(_mdape(y_true, y_pred))}


def _mdape_neg(estimator, X, y):
    pred = estimator.predict(X)
    return -_mdape(y if not hasattr(y, "values") else y.values, pred)


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None, cat_features: list[str]) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _local_label_encode(
    X_train: pd.DataFrame, X_test: pd.DataFrame, cat_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    Xtr_e = X_train.copy()
    Xte_e = X_test.copy()
    for col in cat_features:
        if col not in Xtr_e.columns:
            continue
        train_vals = Xtr_e[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)
        Xtr_e[col] = Xtr_e[col].map(mapping).astype(float)
        Xte_e[col] = Xte_e[col].map(mapping).fillna(unseen_idx).astype(float)
    return Xtr_e, Xte_e


def fold_internal_ranking(
    X_tr: pd.DataFrame, y_tr: np.ndarray, cb_best: dict, xgb_best: dict,
    cat_features: list[str],
) -> dict[str, float]:
    """4-method aggregate rank (1=highest impact / fold-internal / leakage X)."""
    cb = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=0, random_seed=42,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr, cat_features))

    cb_fi = cb.get_feature_importance(type="PredictionValuesChange")
    cb_fi_dict = {f: float(v) for f, v in zip(X_tr.columns, cb_fi)}

    cb_shap = cb.get_feature_importance(data=_cb_pool(X_tr, y_tr, cat_features), type="ShapValues")
    cb_shap_pct_dict = dict(zip(X_tr.columns, np.abs(cb_shap[:, :-1]).mean(axis=0)))

    Xtr_e, _ = _local_label_encode(X_tr, X_tr.iloc[:1], cat_features)
    dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )
    score = booster.get_score(importance_type="gain")
    xgb_gain_dict = {f: score.get(f, 0.0) for f in X_tr.columns}

    xgb_shap_vals = shap.TreeExplainer(booster).shap_values(Xtr_e)
    xgb_shap_pct_dict = dict(zip(X_tr.columns, np.abs(xgb_shap_vals).mean(axis=0)))

    cb_total = sum(cb_shap_pct_dict.values()) or 1.0
    xgb_total = sum(xgb_shap_pct_dict.values()) or 1.0
    shap_avg_dict = {
        f: (cb_shap_pct_dict[f] / cb_total + xgb_shap_pct_dict[f] / xgb_total) / 2.0
        for f in X_tr.columns
    }

    rng = np.random.RandomState(42)
    sample_idx = rng.choice(len(X_tr), size=min(5000, len(X_tr)), replace=False)
    pi = permutation_importance(
        cb, X_tr.iloc[sample_idx], y_tr[sample_idx],
        scoring=_mdape_neg, n_repeats=3, random_state=42, n_jobs=1,
    )
    pi_dict = dict(zip(X_tr.columns, pi.importances_mean))

    def rank_dict(d: dict) -> dict:
        sorted_feats = sorted(d.items(), key=lambda x: -x[1])
        return {f: i + 1 for i, (f, _) in enumerate(sorted_feats)}

    return {f: (rank_dict(cb_fi_dict)[f] + rank_dict(xgb_gain_dict)[f]
                + rank_dict(shap_avg_dict)[f] + rank_dict(pi_dict)[f]) / 4.0
            for f in X_tr.columns}


def predict_xgb(
    X_tr: pd.DataFrame, y_tr: np.ndarray, X_te: pd.DataFrame,
    cat_features: list[str], xgb_best: dict, seed: int = 42,
) -> np.ndarray:
    Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
    dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
    dtest = xgb.DMatrix(Xte_e)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    m = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": seed},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )
    return m.predict(dtest)


def predict_cb(
    X_tr: pd.DataFrame, y_tr: np.ndarray, X_te: pd.DataFrame,
    cat_features: list[str], cb_best: dict, seed: int = 42,
) -> np.ndarray:
    cb = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=0, random_seed=seed,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr, cat_features))
    return cb.predict(_cb_pool(X_te, None, cat_features))


def predict_ensemble(
    X_tr: pd.DataFrame, y_tr: np.ndarray, X_te: pd.DataFrame,
    cat_features: list[str], cb_best: dict, xgb_best: dict, seed: int = 42,
) -> np.ndarray:
    cb_pred = predict_cb(X_tr, y_tr, X_te, cat_features, cb_best, seed)
    xgb_pred = predict_xgb(X_tr, y_tr, X_te, cat_features, xgb_best, seed)
    return (cb_pred + xgb_pred) / 2.0


def cv_evaluate_cold(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, source: np.ndarray,
    cat_features: list[str], predict_fn, *, label: str,
) -> dict:
    """cold GroupKFold-5 evaluation."""
    gkf = GroupKFold(n_splits=5)
    fold_metrics = []
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        t0 = time.time()
        pred_log = predict_fn(X.iloc[tr], y[tr], X.iloc[te], cat_features)
        y_te_price = np.exp(y[te])
        pred_price = np.exp(pred_log)
        src_te = source[te]

        f = {"fold": fold, "all": _summary(y_te_price, pred_price), "elapsed_sec": round(time.time()-t0, 1)}
        for src in sorted(set(src_te)):
            mask = src_te == src
            f[src] = _summary(y_te_price[mask], pred_price[mask])
        fold_metrics.append(f)
        logger.info(f"    {label} cold fold {fold}/5: all={f['all']['MdAPE']:.2f} ({f['elapsed_sec']}s)")
    return {"folds": fold_metrics}


def cv_evaluate_warm(
    X_warm: pd.DataFrame, y_warm: np.ndarray,
    cat_features: list[str], predict_fn, *, label: str,
    seeds: list[int] = WARM_SEEDS,
) -> dict:
    """warm KFold-5 multi-seed median."""
    seed_results = {}
    for seed in seeds:
        kf = KFold(n_splits=5, shuffle=True, random_state=seed)
        fold_metrics = []
        for fold, (tr, te) in enumerate(kf.split(X_warm, y_warm), 1):
            t0 = time.time()
            pred_log = predict_fn(X_warm.iloc[tr], y_warm[tr], X_warm.iloc[te], cat_features, seed=seed)
            y_te_price = np.exp(y_warm[te])
            pred_price = np.exp(pred_log)
            f = {"fold": fold, "MdAPE": float(_mdape(y_te_price, pred_price)), "elapsed_sec": round(time.time()-t0, 1)}
            fold_metrics.append(f)
        seed_results[seed] = fold_metrics
        seed_median = float(np.median([f["MdAPE"] for f in fold_metrics]))
        logger.info(f"    {label} warm seed={seed} median={seed_median:.3f}")
    return seed_results


def warm_groupkfold_guard(
    X_warm: pd.DataFrame, y_warm: np.ndarray, g_warm: np.ndarray,
    cat_features: list[str], predict_fn, *, label: str,
) -> dict:
    gkf = GroupKFold(n_splits=5)
    fold_metrics = []
    for fold, (tr, te) in enumerate(gkf.split(X_warm, y_warm, g_warm), 1):
        pred_log = predict_fn(X_warm.iloc[tr], y_warm[tr], X_warm.iloc[te], cat_features)
        y_te_price = np.exp(y_warm[te])
        pred_price = np.exp(pred_log)
        fold_metrics.append({"fold": fold, "MdAPE": float(_mdape(y_te_price, pred_price))})
    return {"folds": fold_metrics, "median": float(np.median([f["MdAPE"] for f in fold_metrics]))}


def evaluate_config(
    config_name: str,
    X_train_full: pd.DataFrame, y_train_full: np.ndarray, groups_train: np.ndarray,
    X_holdout: pd.DataFrame, y_holdout: np.ndarray, groups_holdout: np.ndarray,
    source_train: np.ndarray, source_holdout: np.ndarray,
    features: list[str], cat_features: list[str],
    cb_best: dict, xgb_best: dict, *,
    use_ensemble: bool = False, use_xgb: bool = False, use_cb: bool = False,
) -> dict:
    """Evaluate single config: 80% CV (cold + warm 3-seed + warm guard) + Holdout test."""
    t0 = time.time()
    logger.info(f"\n=== Config: {config_name} ===")
    logger.info(f"  features: {len(features)} cols ({features})")

    X_tr = X_train_full[features].copy()
    X_ho = X_holdout[features].copy()

    # warm slice within 80%
    warm_mask_tr = _warm_mask(groups_train)
    X_warm_tr = X_tr[warm_mask_tr].reset_index(drop=True)
    y_warm_tr = y_train_full[warm_mask_tr]
    g_warm_tr = groups_train[warm_mask_tr]

    # predict functions
    if use_cb:
        cold_fn = lambda Xtr, ytr, Xte, cat: predict_cb(Xtr, ytr, Xte, cat, cb_best, seed=42)
        warm_fn = lambda Xtr, ytr, Xte, cat, seed=42: predict_cb(Xtr, ytr, Xte, cat, cb_best, seed=seed)
    elif use_xgb:
        cold_fn = lambda Xtr, ytr, Xte, cat: predict_xgb(Xtr, ytr, Xte, cat, xgb_best, seed=42)
        warm_fn = lambda Xtr, ytr, Xte, cat, seed=42: predict_xgb(Xtr, ytr, Xte, cat, xgb_best, seed=seed)
    elif use_ensemble:
        cold_fn = lambda Xtr, ytr, Xte, cat: predict_ensemble(Xtr, ytr, Xte, cat, cb_best, xgb_best, seed=42)
        warm_fn = lambda Xtr, ytr, Xte, cat, seed=42: predict_ensemble(Xtr, ytr, Xte, cat, cb_best, xgb_best, seed=seed)
    else:
        raise ValueError("must specify model")

    # 80% CV cold
    logger.info(f"  80% CV cold (GroupKFold-5)")
    cv_cold = cv_evaluate_cold(X_tr, y_train_full, groups_train, source_train, cat_features, cold_fn, label=config_name)

    # 80% warm CV (multi-seed)
    logger.info(f"  80% CV warm (KFold-5 × 3 seeds)")
    cv_warm = cv_evaluate_warm(X_warm_tr, y_warm_tr, cat_features, warm_fn, label=config_name)

    # 80% warm guard (GroupKFold-5)
    logger.info(f"  80% warm GroupKFold-5 guard")
    cv_warm_guard = warm_groupkfold_guard(X_warm_tr, y_warm_tr, g_warm_tr, cat_features,
                                           lambda Xtr, ytr, Xte, cat: warm_fn(Xtr, ytr, Xte, cat, seed=42),
                                           label=config_name)

    # Holdout test (80% retrain + Holdout predict)
    logger.info(f"  Holdout test (80% retrain + Holdout predict)")
    pred_log = cold_fn(X_tr, y_train_full, X_ho, cat_features)
    y_ho_price = np.exp(y_holdout)
    pred_price = np.exp(pred_log)
    holdout_all = _summary(y_ho_price, pred_price)
    holdout_per_source = {}
    for src in sorted(set(source_holdout)):
        mask = source_holdout == src
        holdout_per_source[src] = _summary(y_ho_price[mask], pred_price[mask])
    # warm slice within Holdout
    holdout_warm_mask = _warm_mask(groups_holdout)
    holdout_warm = _summary(y_ho_price[holdout_warm_mask], pred_price[holdout_warm_mask]) if holdout_warm_mask.sum() > 0 else None

    # Aggregate metrics
    cold_all_vals = [f["all"]["MdAPE"] for f in cv_cold["folds"]]
    cold_artsy_vals = [f.get("artsy", {}).get("MdAPE") for f in cv_cold["folds"] if f.get("artsy")]
    cold_saatchi_vals = [f.get("saatchi", {}).get("MdAPE") for f in cv_cold["folds"] if f.get("saatchi")]
    warm_seed_medians = []
    for seed, folds in cv_warm.items():
        warm_seed_medians.append(float(np.median([f["MdAPE"] for f in folds])))

    out = {
        "config_name": config_name,
        "n_features": len(features),
        "features": features,
        "cv_80": {
            "cold_all_median": float(np.median(cold_all_vals)),
            "cold_artsy_median": float(np.median(cold_artsy_vals)) if cold_artsy_vals else None,
            "cold_saatchi_median": float(np.median(cold_saatchi_vals)) if cold_saatchi_vals else None,
            "warm_seed_medians": warm_seed_medians,
            "warm_3seed_median": float(np.median(warm_seed_medians)),
            "warm_groupkfold_median": cv_warm_guard["median"],
            "cold_folds_detail": cv_cold["folds"],
            "warm_seed_folds": {str(s): folds for s, folds in cv_warm.items()},
            "warm_groupkfold_folds": cv_warm_guard["folds"],
        },
        "holdout": {
            "n": int(len(X_ho)),
            "all": holdout_all,
            "warm": holdout_warm,
            "per_source": holdout_per_source,
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }
    logger.info(f"  CV cold median: {out['cv_80']['cold_all_median']:.3f}")
    logger.info(f"  CV warm 3-seed median: {out['cv_80']['warm_3seed_median']:.3f}")
    logger.info(f"  Holdout cold: {out['holdout']['all']['MdAPE']:.3f}")
    if holdout_warm:
        logger.info(f"  Holdout warm: {holdout_warm['MdAPE']:.3f}")
    return out


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Confirmatory Cycle — Top 15 + XGBoost (decision-binding ✓)")
    logger.info("=" * 70)

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    X_full, y, groups = prepare_features(df)
    source_full = df["source"].astype(str).to_numpy()

    # ─── Step 1: Locked Holdout split (artist GroupShuffleSplit) ──────
    logger.info(f"\n--- Step 1: Locked Holdout split (random_state={HOLDOUT_RANDOM_STATE}) ---")
    gss = GroupShuffleSplit(n_splits=1, test_size=HOLDOUT_FRACTION, random_state=HOLDOUT_RANDOM_STATE)
    train_idx, holdout_idx = next(gss.split(X_full, y, groups))
    X_train = X_full.iloc[train_idx].reset_index(drop=True)
    y_train = y[train_idx]
    groups_train = groups[train_idx]
    source_train = source_full[train_idx]
    X_holdout = X_full.iloc[holdout_idx].reset_index(drop=True)
    y_holdout = y[holdout_idx]
    groups_holdout = groups[holdout_idx]
    source_holdout = source_full[holdout_idx]
    logger.info(f"  Train (80%): {len(X_train)} rows / {len(set(groups_train))} artists")
    logger.info(f"  Holdout (20%): {len(X_holdout)} rows / {len(set(groups_holdout))} artists")
    assert len(set(groups_train) & set(groups_holdout)) == 0, "artist overlap!"

    # ─── Step 2: 80% 내부 fold-internal 4-method ranking (5 fold) ─────
    logger.info(f"\n--- Step 2: 80% 내부 fold-internal 4-method ranking (selection leakage 방지) ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits_train = list(gkf.split(X_train, y_train, groups_train))
    fold_rankings = []
    for fold, (tr, te) in enumerate(cold_splits_train, 1):
        t1 = time.time()
        ranking = fold_internal_ranking(X_train.iloc[tr], y_train[tr], cb_best, xgb_best, CAT_FEATURES)
        fold_rankings.append(ranking)
        logger.info(f"  fold {fold}/5 ranking done ({time.time()-t1:.1f}s)")

    avg_ranking = {f: np.mean([fr[f] for fr in fold_rankings]) for f in X_train.columns}

    # ─── Step 3: Top 15 (alphabetical tie-break) ─────────────────────
    sorted_feats = sorted(avg_ranking.items(), key=lambda x: (x[1], x[0]))  # rank ASC, name ASC tie-break
    top15 = [f for f, _ in sorted_feats[:15]]
    cat_features_top15 = [c for c in CAT_FEATURES if c in top15]
    logger.info(f"\n--- Step 3: Top 15 (80% / alphabetical tie-break) ---")
    for i, (f, r) in enumerate(sorted_feats[:15], 1):
        logger.info(f"  {i:>2}. {f:30s} avg_rank={r:.2f}")

    # ─── Step 4-5: 3 configs evaluation (80% CV + Holdout test) ──────
    configs = []

    # Config 1: Top 15 + XGBoost (BINDING test)
    configs.append(evaluate_config(
        "Top15_XGBoost (BINDING)",
        X_train, y_train, groups_train, X_holdout, y_holdout, groups_holdout,
        source_train, source_holdout, top15, cat_features_top15,
        cb_best, xgb_best, use_xgb=True,
    ))

    # Config 2: 32 + Ensemble (BINDING comparator / 운영 정합)
    cat_features_32 = [c for c in CAT_FEATURES if c in CB_FEATURES]
    configs.append(evaluate_config(
        "32_Ensemble (BINDING comparator)",
        X_train, y_train, groups_train, X_holdout, y_holdout, groups_holdout,
        source_train, source_holdout, list(CB_FEATURES), cat_features_32,
        cb_best, xgb_best, use_ensemble=True,
    ))

    # Config 3: 32 + XGBoost (DIAGNOSTIC / non-binding)
    configs.append(evaluate_config(
        "32_XGBoost (DIAGNOSTIC)",
        X_train, y_train, groups_train, X_holdout, y_holdout, groups_holdout,
        source_train, source_holdout, list(CB_FEATURES), cat_features_32,
        cb_best, xgb_best, use_xgb=True,
    ))

    # ─── Step 6: Decision criterion (BINDING comparison) ─────────────
    test_cfg = configs[0]   # Top15+XGBoost
    base_cfg = configs[1]   # 32+Ensemble

    test_holdout_cold = test_cfg["holdout"]["all"]["MdAPE"]
    base_holdout_cold = base_cfg["holdout"]["all"]["MdAPE"]
    test_holdout_warm = test_cfg["holdout"]["warm"]["MdAPE"] if test_cfg["holdout"]["warm"] else None
    base_holdout_warm = base_cfg["holdout"]["warm"]["MdAPE"] if base_cfg["holdout"]["warm"] else None
    test_holdout_artsy = test_cfg["holdout"]["per_source"].get("artsy", {}).get("MdAPE")
    base_holdout_artsy = base_cfg["holdout"]["per_source"].get("artsy", {}).get("MdAPE")
    test_holdout_saatchi = test_cfg["holdout"]["per_source"].get("saatchi", {}).get("MdAPE")
    base_holdout_saatchi = base_cfg["holdout"]["per_source"].get("saatchi", {}).get("MdAPE")

    deltas = {
        "G2_cold": test_holdout_cold - base_holdout_cold,
        "G1_warm": (test_holdout_warm - base_holdout_warm) if test_holdout_warm and base_holdout_warm else None,
        "G3_artsy": (test_holdout_artsy - base_holdout_artsy) if test_holdout_artsy and base_holdout_artsy else None,
        "G4_saatchi": (test_holdout_saatchi - base_holdout_saatchi) if test_holdout_saatchi and base_holdout_saatchi else None,
    }
    guard_pass = {
        "G1": (deltas["G1_warm"] is not None and deltas["G1_warm"] <= GUARD_LOCKED["G1_warm"]),
        "G2": deltas["G2_cold"] <= GUARD_LOCKED["G2_cold"],
        "G3": (deltas["G3_artsy"] is not None and deltas["G3_artsy"] <= GUARD_LOCKED["G3_artsy"]),
        "G4": (deltas["G4_saatchi"] is not None and deltas["G4_saatchi"] <= GUARD_LOCKED["G4_saatchi"]),
    }

    # CV-Holdout gap fail-safe
    cv_cold_test = test_cfg["cv_80"]["cold_all_median"]
    cv_warm_test = test_cfg["cv_80"]["warm_3seed_median"]
    gap_cold = test_holdout_cold - cv_cold_test
    gap_warm = test_holdout_warm - cv_warm_test if test_holdout_warm else None
    gap_pass = {
        "cold_gap": gap_cold <= NOISE_SE_PP,
        "warm_gap": (gap_warm is not None and gap_warm <= WARM_GAP_PP),
    }

    all_guards_pass = all(guard_pass.values())
    all_gaps_pass = all(gap_pass.values())
    verdict = "CHAMPION" if (all_guards_pass and all_gaps_pass) else "FAIL"

    out = {
        "prereg": "docs/confirmatory_prereg_20260509.md",
        "decision_binding": True,
        "holdout_random_state": HOLDOUT_RANDOM_STATE,
        "holdout_fraction": HOLDOUT_FRACTION,
        "warm_seeds": WARM_SEEDS,
        "n_train": int(len(X_train)),
        "n_holdout": int(len(X_holdout)),
        "n_artists_train": int(len(set(groups_train))),
        "n_artists_holdout": int(len(set(groups_holdout))),
        "top15_features": top15,
        "fold_rankings_avg_80pct": avg_ranking,
        "configs": configs,
        "binding_comparison": {
            "test_config": "Top15_XGBoost",
            "comparator": "32_Ensemble",
            "test_holdout_cold": test_holdout_cold,
            "base_holdout_cold": base_holdout_cold,
            "test_holdout_warm": test_holdout_warm,
            "base_holdout_warm": base_holdout_warm,
            "test_holdout_artsy": test_holdout_artsy,
            "base_holdout_artsy": base_holdout_artsy,
            "test_holdout_saatchi": test_holdout_saatchi,
            "base_holdout_saatchi": base_holdout_saatchi,
            "deltas": deltas,
            "guard_locked": GUARD_LOCKED,
            "guard_pass": guard_pass,
            "all_guards_pass": all_guards_pass,
            "cv_holdout_gap_cold": gap_cold,
            "cv_holdout_gap_warm": gap_warm,
            "noise_band_cold_pp": NOISE_SE_PP,
            "noise_band_warm_pp": WARM_GAP_PP,
            "gap_pass": gap_pass,
            "all_gaps_pass": all_gaps_pass,
            "verdict": verdict,
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    # Print summary
    print("\n" + "=" * 80)
    print("Confirmatory Cycle Results")
    print("=" * 80)
    print(f"\nHoldout (locked): {len(X_holdout)} rows / {len(set(groups_holdout))} artists")
    print(f"Top 15 features: {top15}")
    print()
    for cfg in configs:
        print(f"\n{cfg['config_name']} (n={cfg['n_features']}):")
        print(f"  CV cold median: {cfg['cv_80']['cold_all_median']:.3f}")
        print(f"  CV warm 3-seed median: {cfg['cv_80']['warm_3seed_median']:.3f}")
        print(f"  CV warm guard (GKF) median: {cfg['cv_80']['warm_groupkfold_median']:.3f}")
        print(f"  Holdout cold: {cfg['holdout']['all']['MdAPE']:.3f}")
        if cfg['holdout']['warm']:
            print(f"  Holdout warm: {cfg['holdout']['warm']['MdAPE']:.3f}")
        for src, m in cfg['holdout']['per_source'].items():
            print(f"  Holdout {src}: {m['MdAPE']:.3f}")

    print(f"\n=== Binding Comparison: Top15+XGBoost vs 32+Ensemble ===")
    print(f"  Δ cold      = {deltas['G2_cold']:+.3f}  (threshold ≤+{GUARD_LOCKED['G2_cold']}) {'✓' if guard_pass['G2'] else '✗'}")
    print(f"  Δ warm      = {deltas['G1_warm']:+.3f}  (threshold ≤+{GUARD_LOCKED['G1_warm']}) {'✓' if guard_pass['G1'] else '✗'}")
    if deltas['G3_artsy'] is not None:
        print(f"  Δ Artsy     = {deltas['G3_artsy']:+.3f}  (threshold ≤+{GUARD_LOCKED['G3_artsy']}) {'✓' if guard_pass['G3'] else '✗'}")
    if deltas['G4_saatchi'] is not None:
        print(f"  Δ Saatchi   = {deltas['G4_saatchi']:+.3f}  (threshold ≤+{GUARD_LOCKED['G4_saatchi']}) {'✓' if guard_pass['G4'] else '✗'}")

    print(f"\n=== CV-Holdout Gap (overfit fail-safe) ===")
    print(f"  cold gap = {gap_cold:+.3f} (threshold ≤+{NOISE_SE_PP}) {'✓' if gap_pass['cold_gap'] else '✗'}")
    if gap_warm is not None:
        print(f"  warm gap = {gap_warm:+.3f} (threshold ≤+{WARM_GAP_PP}) {'✓' if gap_pass['warm_gap'] else '✗'}")

    print(f"\n=== VERDICT: {verdict} ===")
    if verdict == "CHAMPION":
        print("  → 운영 채택 가능 (decision-binding)")
    else:
        failures = []
        for k, v in guard_pass.items():
            if not v:
                failures.append(f"{k} guard FAIL (Δ={deltas.get(f'{k}_cold', deltas.get(f'{k}_warm', deltas.get(f'{k}_artsy', deltas.get(f'{k}_saatchi'))))})")
        for k, v in gap_pass.items():
            if not v:
                failures.append(f"{k} gap FAIL")
        print(f"  Failures: {failures}")
        print("  → 운영 변경 X (decision-binding)")


if __name__ == "__main__":
    main()
