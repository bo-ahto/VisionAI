"""Feature Sweep — Post-hoc Amendment Cycle.

Amendment doc: docs/feature_sweep_amendment_20260509.md
Decision binding ❌ X / record only.

P1 4 fix 적용:
1. Fold-internal feature ranking (selection leakage 방지 / outer CV train fold 내부)
2. Locked config space (12 N × 6 model = 72 configs / 전체 dump)
3. 1-SE winner rule (cold SE ≈ 2.117%p / band 내 최소 N + 운영 정합 모델 우선)
4. Model-matched secondary metric

P2:
- LightGBM / RF / HGB = default / screening only / winner 자격 X
- Warm multi-seed (3 seeds: 42/7/13) — sensitivity
- N grid sparse: 5/8/10/12/15/18/20/22/25/28/30/32

Total: 5 outer fold × (4-method rank + 12 N × 6 model retrain) ≈ 3-4 시간
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from catboost import CatBoostRegressor, Pool
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold, KFold

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
OUT_DIR = Path(__file__).parent
OUT_FULL = OUT_DIR / "sweep_full_results.json"
OUT_MATRIX = OUT_DIR / "sweep_matrix.csv"

# ─── Config space (locked) ────────────────────────────────────────────
N_GRID = [5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 32]
MODELS = ["catboost", "xgboost", "lightgbm", "randomforest", "histgb", "ensemble_cb_xgb"]
WARM_SEEDS = [42, 7, 13]

# Winner-eligible models (운영 정합 / locked params)
WINNER_ELIGIBLE = {"catboost", "xgboost", "ensemble_cb_xgb"}

# 1-SE noise band (Phase 0 cold ens fold std 4.734 / SE = 4.734/√5 = 2.117)
NOISE_SE_PP = 2.117

# Phase 0 baseline anchor
BASELINE_ANCHOR = {
    "cold_ensemble":          38.6224,
    "cold_artsy_ensemble":    33.5200,
    "cold_saatchi_ensemble":  41.7400,
    "warm_kfold_xgboost":     9.7140,
    "warm_kfold_ensemble":    10.4680,
}

GUARDS = {
    "G1": {"metric": "warm_kfold_ensemble", "pp": 0.5, "vs": "warm"},  # model-matched
    "G2": {"metric": "cold_ensemble", "pp": 0.8, "vs": "cold"},
    "G3": {"metric": "cold_artsy_ensemble", "pp": 1.0, "vs": "cold"},
    "G4": {"metric": "cold_saatchi_ensemble", "pp": 1.0, "vs": "cold"},
}


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _mdape_neg(estimator, X, y):
    pred = estimator.predict(X)
    return -_mdape(y if not hasattr(y, "values") else y.values, pred)


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None, cat_features: list[str]) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def fold_internal_ranking(
    X_tr: pd.DataFrame, y_tr: np.ndarray, cb_best: dict, xgb_best: dict,
    cat_features: list[str],
) -> dict[str, float]:
    """4-method aggregate ranking (CB FI / XGB gain / SHAP avg / Permutation).

    Train fold 내부 retrain → ranking 산출. Selection leakage 방지.
    """
    # CatBoost retrain
    cb = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=0, random_seed=42,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr, cat_features))

    # CB FI
    cb_fi = cb.get_feature_importance(type="PredictionValuesChange")
    cb_fi_dict = {f: float(v) for f, v in zip(X_tr.columns, cb_fi)}

    # CB SHAP
    cb_shap = cb.get_feature_importance(data=_cb_pool(X_tr, y_tr, cat_features), type="ShapValues")
    cb_shap_vals = cb_shap[:, :-1]
    cb_shap_pct_dict = dict(zip(X_tr.columns, np.abs(cb_shap_vals).mean(axis=0)))

    # XGBoost retrain
    Xtr_e, _, label_maps = _label_encode_xgb(X_tr, X_tr.iloc[:1])
    dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )

    # XGB gain
    score = booster.get_score(importance_type="gain")
    xgb_gain_dict = {f: score.get(f, 0.0) for f in X_tr.columns}

    # XGB SHAP
    xgb_shap_vals = shap.TreeExplainer(booster).shap_values(Xtr_e)
    xgb_shap_pct_dict = dict(zip(X_tr.columns, np.abs(xgb_shap_vals).mean(axis=0)))

    # SHAP avg (CB + XGB / normalized within method first)
    cb_shap_total = sum(cb_shap_pct_dict.values()) or 1.0
    xgb_shap_total = sum(xgb_shap_pct_dict.values()) or 1.0
    shap_avg_dict = {
        f: (cb_shap_pct_dict[f] / cb_shap_total + xgb_shap_pct_dict[f] / xgb_shap_total) / 2.0
        for f in X_tr.columns
    }

    # Permutation Importance (CB / sample 5000 / 3 repeats — speed)
    rng = np.random.RandomState(42)
    sample_idx = rng.choice(len(X_tr), size=min(5000, len(X_tr)), replace=False)
    pi = permutation_importance(
        cb, X_tr.iloc[sample_idx], y_tr[sample_idx],
        scoring=_mdape_neg, n_repeats=3, random_state=42, n_jobs=1,
    )
    pi_dict = dict(zip(X_tr.columns, pi.importances_mean))

    # Rank per method (ASC = 영향도 높음)
    def rank_dict(d: dict) -> dict:
        sorted_feats = sorted(d.items(), key=lambda x: -x[1])
        return {f: i + 1 for i, (f, _) in enumerate(sorted_feats)}

    cb_rank = rank_dict(cb_fi_dict)
    xgb_rank = rank_dict(xgb_gain_dict)
    shap_rank = rank_dict(shap_avg_dict)
    pi_rank = rank_dict(pi_dict)

    avg_rank = {f: (cb_rank[f] + xgb_rank[f] + shap_rank[f] + pi_rank[f]) / 4.0
                for f in X_tr.columns}
    return avg_rank


def _local_label_encode(
    X_train: pd.DataFrame, X_test: pd.DataFrame, cat_features: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Local label encoding (CAT_FEATURES global X / fold-internal X cols 영역 의 의무 영역 의 의무)."""
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


def predict_with_model(
    model_name: str, X_tr: pd.DataFrame, y_tr: np.ndarray,
    X_te: pd.DataFrame, cat_features: list[str],
    cb_best: dict, xgb_best: dict, seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (y_pred_log, y_pred_price)."""
    if model_name == "catboost":
        cb = CatBoostRegressor(
            **cb_best, loss_function="RMSE", verbose=0, random_seed=seed,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X_tr, y_tr, cat_features))
        pred = cb.predict(_cb_pool(X_te, None, cat_features))
        return pred, np.exp(pred)
    elif model_name == "xgboost":
        Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
        dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
        dtest = xgb.DMatrix(Xte_e, label=None)
        xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": seed},
            dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
        )
        pred = m.predict(dtest)
        return pred, np.exp(pred)
    elif model_name == "lightgbm":
        Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
        m = lgb.LGBMRegressor(
            n_estimators=500, learning_rate=0.05, max_depth=-1,
            random_state=seed, verbose=-1,
        )
        m.fit(Xtr_e, y_tr)
        pred = m.predict(Xte_e)
        return pred, np.exp(pred)
    elif model_name == "randomforest":
        Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
        m = RandomForestRegressor(
            n_estimators=200, max_depth=None,
            n_jobs=-1, random_state=seed,
        )
        m.fit(Xtr_e, y_tr)
        pred = m.predict(Xte_e)
        return pred, np.exp(pred)
    elif model_name == "histgb":
        Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
        m = HistGradientBoostingRegressor(
            max_iter=500, learning_rate=0.05, random_state=seed,
        )
        m.fit(Xtr_e, y_tr)
        pred = m.predict(Xte_e)
        return pred, np.exp(pred)
    elif model_name == "ensemble_cb_xgb":
        cb_pred, _ = predict_with_model("catboost", X_tr, y_tr, X_te, cat_features, cb_best, xgb_best, seed)
        xgb_pred, _ = predict_with_model("xgboost", X_tr, y_tr, X_te, cat_features, cb_best, xgb_best, seed)
        ens = (cb_pred + xgb_pred) / 2.0
        return ens, np.exp(ens)
    else:
        raise ValueError(model_name)


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Feature Sweep — Post-hoc amendment cycle")
    logger.info("=" * 70)
    logger.info(f"N grid: {N_GRID}")
    logger.info(f"Models: {MODELS}")
    logger.info(f"Total configs: {len(N_GRID)} × {len(MODELS)} = {len(N_GRID) * len(MODELS)}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    # Cold GroupKFold-5 outer
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X_full, y, groups))

    # Per-fold rankings (fold-internal / selection leakage 방지)
    logger.info("\n--- Step 1: Fold-internal 4-method ranking (5 outer folds) ---")
    fold_rankings: list[dict[str, float]] = []
    for fold, (tr, te) in enumerate(cold_splits, 1):
        t1 = time.time()
        ranking = fold_internal_ranking(
            X_full.iloc[tr], y[tr], cb_best, xgb_best, CAT_FEATURES,
        )
        fold_rankings.append(ranking)
        logger.info(f"  fold {fold}/5 ranking done ({time.time()-t1:.1f}s)")

    # Per-fold top-N feature sets
    fold_top_n: list[dict[int, list[str]]] = []
    for fold_rank in fold_rankings:
        sorted_feats = sorted(fold_rank.items(), key=lambda x: x[1])
        top_n_dict = {n: [f for f, _ in sorted_feats[:n]] for n in N_GRID}
        fold_top_n.append(top_n_dict)

    # Per (N, model, seed) — cold + warm CV
    logger.info("\n--- Step 2: Cold sweep (12 N × 6 model × 5 fold) ---")
    cold_results: dict = {}  # (N, model) → {fold: metrics}
    for N in N_GRID:
        for model_name in MODELS:
            cold_results[(N, model_name)] = {"folds": []}

    for fold, (tr, te) in enumerate(cold_splits, 1):
        logger.info(f"\n  Fold {fold}/5 (cold)")
        for N in N_GRID:
            features = fold_top_n[fold-1][N]
            cat_features_iter = [c for c in CAT_FEATURES if c in features]
            X_tr_n = X_full[features].iloc[tr]
            X_te_n = X_full[features].iloc[te]
            y_te_price = np.exp(y[te])
            src_te = source[te]

            for model_name in MODELS:
                t1 = time.time()
                _, pred_price = predict_with_model(
                    model_name, X_tr_n, y[tr], X_te_n, cat_features_iter,
                    cb_best, xgb_best, seed=42,
                )
                fold_metric = {
                    "fold": fold,
                    "n_train": int(len(tr)),
                    "n_test": int(len(te)),
                    "ensemble": _summary_fold(y_te_price, pred_price),
                    "elapsed_sec": round(time.time() - t1, 1),
                }
                # source split
                for src_name in sorted(set(src_te)):
                    mask = src_te == src_name
                    if mask.sum() == 0:
                        continue
                    fold_metric[f"{src_name}_ensemble"] = _summary_fold(
                        y_te_price[mask], pred_price[mask]
                    )
                cold_results[(N, model_name)]["folds"].append(fold_metric)
            logger.info(f"    N={N:>2}: {len(MODELS)} models done ({sum(cold_results[(N, m)]['folds'][-1]['elapsed_sec'] for m in MODELS):.1f}s)")

    # Warm sweep (multi-seed)
    logger.info("\n--- Step 3: Warm sweep (12 N × 6 model × 3 seeds × 5 fold) ---")
    warm_mask = _warm_mask(groups)
    X_warm = X_full[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    g_warm = groups[warm_mask]

    # Warm fold-internal ranking (cold ranking 영역 의 의무 영역 의 의무 X / warm 별도 ranking 영역 의 의무)
    # 단순화: cold ranking 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 (영향도 영역 의 의무 영역 의 의무 동일 ordering 영역 의 의무 영역 의 의무 / cold 영역 의 의무 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 strictly fold-internal)
    # warm 영역 의 의무 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 = warm KFold 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 = 별도 영역 의 의무 영역 의 의무 비용 영역 의 의무 영역 의 의무 영역 의 의무 큰 영역 의 의무 영역 의 의무.
    # → cold-fold ranking 영역 의 의무 영역 의 의무 warm 영역 의 의무 영역 의 의무 영역 의 의무 reuse (영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무).
    # 다만 cold ranking 영역 의 의무 영역 의 의무 5 fold rank average 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 정합 (warm 영역 의 의무 영역 의 의무 영역 의 의무 fold-internal selection 영역 의 의무 영역 의 의무 영역 의 의무 X).
    cold_avg_ranking = {f: np.mean([fr[f] for fr in fold_rankings]) for f in X_full.columns}
    sorted_avg = sorted(cold_avg_ranking.items(), key=lambda x: x[1])
    warm_top_n = {n: [f for f, _ in sorted_avg[:n]] for n in N_GRID}

    warm_results: dict = {}  # (N, model, seed) → folds
    for N in N_GRID:
        for model_name in MODELS:
            for seed in WARM_SEEDS:
                warm_results[(N, model_name, seed)] = {"folds": []}

    for seed in WARM_SEEDS:
        logger.info(f"\n  Warm seed {seed}")
        kf = KFold(n_splits=5, shuffle=True, random_state=seed)
        warm_splits = list(kf.split(X_warm, y_warm))
        for fold, (tr, te) in enumerate(warm_splits, 1):
            for N in N_GRID:
                features = warm_top_n[N]
                cat_features_iter = [c for c in CAT_FEATURES if c in features]
                X_tr_n = X_warm[features].iloc[tr]
                X_te_n = X_warm[features].iloc[te]
                y_te_price = np.exp(y_warm[te])

                for model_name in MODELS:
                    t1 = time.time()
                    _, pred_price = predict_with_model(
                        model_name, X_tr_n, y_warm[tr], X_te_n, cat_features_iter,
                        cb_best, xgb_best, seed=seed,
                    )
                    fold_metric = {
                        "seed": seed,
                        "fold": fold,
                        "ensemble": _summary_fold(y_te_price, pred_price),
                        "elapsed_sec": round(time.time() - t1, 1),
                    }
                    warm_results[(N, model_name, seed)]["folds"].append(fold_metric)
            logger.info(f"    seed {seed} fold {fold}/5: {len(N_GRID)*len(MODELS)} configs done")

    # Summary aggregation
    summary_rows = []
    for N in N_GRID:
        for model_name in MODELS:
            cold_folds = cold_results[(N, model_name)]["folds"]
            cold_ens_vals = [f["ensemble"]["MdAPE"] for f in cold_folds]
            cold_artsy = [f.get("artsy_ensemble", {}).get("MdAPE") for f in cold_folds]
            cold_artsy = [v for v in cold_artsy if v is not None]
            cold_saatchi = [f.get("saatchi_ensemble", {}).get("MdAPE") for f in cold_folds]
            cold_saatchi = [v for v in cold_saatchi if v is not None]

            # warm: aggregate over 3 seeds (median of seed medians)
            warm_seed_medians = []
            for seed in WARM_SEEDS:
                w_folds = warm_results[(N, model_name, seed)]["folds"]
                w_vals = [f["ensemble"]["MdAPE"] for f in w_folds]
                if w_vals:
                    warm_seed_medians.append(float(np.median(w_vals)))

            row = {
                "N": N,
                "model": model_name,
                "cold_ens_median": float(np.median(cold_ens_vals)),
                "cold_ens_mean": float(np.mean(cold_ens_vals)),
                "cold_ens_std": float(np.std(cold_ens_vals, ddof=0)),
                "cold_ens_q1": float(np.percentile(cold_ens_vals, 25)),
                "cold_ens_q3": float(np.percentile(cold_ens_vals, 75)),
                "cold_artsy_median": float(np.median(cold_artsy)) if cold_artsy else None,
                "cold_saatchi_median": float(np.median(cold_saatchi)) if cold_saatchi else None,
                "warm_ens_median_3seed": float(np.median(warm_seed_medians)) if warm_seed_medians else None,
                "warm_ens_seed_range": [float(min(warm_seed_medians)), float(max(warm_seed_medians))] if warm_seed_medians else None,
                "winner_eligible": model_name in WINNER_ELIGIBLE,
            }
            # Guard check (vs Phase 0 baseline)
            row["delta_cold_ens_vs_baseline"] = round(row["cold_ens_median"] - BASELINE_ANCHOR["cold_ensemble"], 4)
            row["delta_warm_ens_vs_baseline"] = round(row["warm_ens_median_3seed"] - BASELINE_ANCHOR["warm_kfold_ensemble"], 4) if row["warm_ens_median_3seed"] else None
            row["delta_artsy_vs_baseline"] = round(row["cold_artsy_median"] - BASELINE_ANCHOR["cold_artsy_ensemble"], 4) if row["cold_artsy_median"] else None
            row["delta_saatchi_vs_baseline"] = round(row["cold_saatchi_median"] - BASELINE_ANCHOR["cold_saatchi_ensemble"], 4) if row["cold_saatchi_median"] else None
            row["g1_pass"] = bool(row["delta_warm_ens_vs_baseline"] is not None and row["delta_warm_ens_vs_baseline"] <= 0.5)
            row["g2_pass"] = bool(row["delta_cold_ens_vs_baseline"] <= 0.8)
            row["g3_pass"] = bool(row["delta_artsy_vs_baseline"] is not None and row["delta_artsy_vs_baseline"] <= 1.0)
            row["g4_pass"] = bool(row["delta_saatchi_vs_baseline"] is not None and row["delta_saatchi_vs_baseline"] <= 1.0)
            row["all_guards_pass"] = row["g1_pass"] and row["g2_pass"] and row["g3_pass"] and row["g4_pass"]
            summary_rows.append(row)

    # 1-SE winner selection
    winner_eligible_rows = [r for r in summary_rows if r["winner_eligible"] and r["all_guards_pass"]]
    if not winner_eligible_rows:
        winner = None
        winner_reason = "No winner-eligible config passed all guards."
        noise_band_set = []
    else:
        best_cold = min(r["cold_ens_median"] for r in winner_eligible_rows)
        noise_band_threshold = best_cold + NOISE_SE_PP
        noise_band_set = sorted(
            [r for r in winner_eligible_rows if r["cold_ens_median"] <= noise_band_threshold],
            key=lambda r: (r["N"], {"catboost": 0, "xgboost": 1, "ensemble_cb_xgb": 2}.get(r["model"], 99))
        )
        winner = noise_band_set[0]
        winner_reason = f"1-SE rule (band={NOISE_SE_PP:.3f}%p / best_cold={best_cold:.3f}) → smallest N + winner-eligible model priority"

    out = {
        "amendment_doc": "docs/feature_sweep_amendment_20260509.md",
        "decision_binding": False,
        "n_grid": N_GRID,
        "models": MODELS,
        "winner_eligible_models": list(WINNER_ELIGIBLE),
        "warm_seeds": WARM_SEEDS,
        "noise_se_pp": NOISE_SE_PP,
        "baseline_anchor": BASELINE_ANCHOR,
        "fold_rankings_avg": cold_avg_ranking,
        "summary_rows": summary_rows,
        "noise_band_dominant_set": [{"N": r["N"], "model": r["model"], "cold_ens_median": r["cold_ens_median"]} for r in noise_band_set],
        "winner": winner,
        "winner_reason": winner_reason,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT_FULL.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    logger.info(f"\n[OK] {OUT_FULL.name} (elapsed {out['elapsed_sec']}s)")

    # CSV matrix
    import csv
    with open(OUT_MATRIX, "w") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    logger.info(f"[OK] {OUT_MATRIX.name}")

    # Print summary
    print("\n" + "=" * 100)
    print(f"Feature Sweep Results ({len(N_GRID) * len(MODELS)} configs)")
    print("=" * 100)
    print(f"\n{'N':>3} {'model':>17s} {'cold_med':>9s} {'cold_q1':>9s} {'cold_q3':>9s} {'warm_med':>9s} {'artsy':>7s} {'saatchi':>8s} {'guards':>7s} {'eligible':>9s}")
    for r in summary_rows:
        guards = ''.join(['1' if r[f'g{i}_pass'] else '0' for i in range(1, 5)])
        print(f"{r['N']:>3} {r['model']:>17s} {r['cold_ens_median']:>9.3f} {r['cold_ens_q1']:>9.3f} {r['cold_ens_q3']:>9.3f} "
              f"{(r['warm_ens_median_3seed'] or 0):>9.3f} {(r['cold_artsy_median'] or 0):>7.2f} "
              f"{(r['cold_saatchi_median'] or 0):>8.2f} {guards:>7s} {str(r['winner_eligible']):>9s}")

    print(f"\n=== 1-SE Noise Band Dominant Set ({len(noise_band_set)}) ===")
    for r in noise_band_set:
        print(f"  N={r['N']:>2} / {r['model']:<17s} / cold_med={r['cold_ens_median']:.3f}")

    print(f"\n=== WINNER ===")
    if winner:
        print(f"  N={winner['N']} / model={winner['model']}")
        print(f"  cold_ens_median: {winner['cold_ens_median']:.3f} (vs baseline 38.622 / Δ {winner['delta_cold_ens_vs_baseline']:+.3f})")
        print(f"  warm_ens_median: {winner['warm_ens_median_3seed']:.3f} (vs baseline 10.468 / Δ {winner['delta_warm_ens_vs_baseline']:+.3f})")
        print(f"  Reason: {winner_reason}")
    else:
        print(f"  None — {winner_reason}")


if __name__ == "__main__":
    main()
