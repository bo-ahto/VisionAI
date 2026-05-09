"""Feature Sweep — Simplified (post-hoc amendment / killed-restart).

Original full sweep (12 N × 6 model × 3 seeds) 영역 의 의무 영역 의 의무 thermal
throttling 영역 의 의무 영역 의 의무 매우 슬로우 영역 의 의무 영역 의 의무 (warm
fold 1=8분 → fold 3=112분 / 24+ 시간 추정) → killed.

Simplified config:
- N grid: 5, 10, 15, 20, 25, 30, 32 (7)
- Models: CatBoost / XGBoost / Ensemble (3 winner-eligible only)
- Warm seeds: 42 only (multi-seed 영역 의 의무 영역 의 의무 영역 의 의무 잃음)
- Total: 7 × 3 = 21 configs / 105 cold fits + 105 warm fits
- 추정 시간: ~30분-1시간

P1 4 fix 유지:
1. Fold-internal 4-method ranking
2. Locked config space (21 configs)
3. 1-SE winner rule (cold SE 2.117%p / band 내 최소 N + 운영 정합 모델)
4. Model-matched secondary
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
OUT_FULL = OUT_DIR / "sweep_simplified_results.json"
OUT_MATRIX = OUT_DIR / "sweep_simplified_matrix.csv"

# ─── Simplified config (locked) ──────────────────────────────────────
N_GRID = [5, 10, 15, 20, 25, 30, 32]
MODELS = ["catboost", "xgboost", "ensemble_cb_xgb"]
WARM_SEEDS = [42]

WINNER_ELIGIBLE = {"catboost", "xgboost", "ensemble_cb_xgb"}

NOISE_SE_PP = 2.117  # Phase 0 cold ens std 4.734 / √5

BASELINE_ANCHOR = {
    "cold_ensemble":          38.6224,
    "cold_artsy_ensemble":    33.5200,
    "cold_saatchi_ensemble":  41.7400,
    "warm_kfold_xgboost":     9.7140,
    "warm_kfold_ensemble":    10.4680,
}

GUARDS = {
    "G1": {"metric": "warm_kfold_ensemble", "pp": 0.5, "vs": "warm"},
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


def predict_with_model(
    model_name: str, X_tr: pd.DataFrame, y_tr: np.ndarray,
    X_te: pd.DataFrame, cat_features: list[str],
    cb_best: dict, xgb_best: dict, seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
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
    logger.info("Feature Sweep (SIMPLIFIED) — Post-hoc amendment / killed-restart")
    logger.info("=" * 70)
    logger.info(f"N grid: {N_GRID}")
    logger.info(f"Models: {MODELS}")
    logger.info(f"Warm seeds: {WARM_SEEDS}")
    logger.info(f"Total configs: {len(N_GRID)} × {len(MODELS)} = {len(N_GRID) * len(MODELS)}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    X_full, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()

    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X_full, y, groups))

    # Step 1: Fold-internal ranking
    logger.info("\n--- Step 1: Fold-internal 4-method ranking (5 outer folds) ---")
    fold_rankings: list[dict[str, float]] = []
    for fold, (tr, te) in enumerate(cold_splits, 1):
        t1 = time.time()
        ranking = fold_internal_ranking(X_full.iloc[tr], y[tr], cb_best, xgb_best, CAT_FEATURES)
        fold_rankings.append(ranking)
        logger.info(f"  fold {fold}/5 ranking ({time.time()-t1:.1f}s)")

    fold_top_n: list[dict[int, list[str]]] = []
    for fold_rank in fold_rankings:
        sorted_feats = sorted(fold_rank.items(), key=lambda x: x[1])
        top_n_dict = {n: [f for f, _ in sorted_feats[:n]] for n in N_GRID}
        fold_top_n.append(top_n_dict)

    # Step 2: Cold sweep
    logger.info("\n--- Step 2: Cold sweep (7 N × 3 model × 5 fold = 105 fits) ---")
    cold_results: dict = {}
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
                fm = {
                    "fold": fold, "n_train": int(len(tr)), "n_test": int(len(te)),
                    "ensemble": _summary_fold(y_te_price, pred_price),
                    "elapsed_sec": round(time.time() - t1, 1),
                }
                for src_name in sorted(set(src_te)):
                    mask = src_te == src_name
                    if mask.sum() == 0:
                        continue
                    fm[f"{src_name}_ensemble"] = _summary_fold(y_te_price[mask], pred_price[mask])
                cold_results[(N, model_name)]["folds"].append(fm)
            logger.info(f"    N={N:>2}: 3 models done ({sum(cold_results[(N, m)]['folds'][-1]['elapsed_sec'] for m in MODELS):.1f}s)")

    # Step 3: Warm sweep (single seed)
    logger.info("\n--- Step 3: Warm sweep (7 N × 3 model × 1 seed × 5 fold = 105 fits) ---")
    warm_mask = _warm_mask(groups)
    X_warm = X_full[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]

    cold_avg_ranking = {f: np.mean([fr[f] for fr in fold_rankings]) for f in X_full.columns}
    sorted_avg = sorted(cold_avg_ranking.items(), key=lambda x: x[1])
    warm_top_n = {n: [f for f, _ in sorted_avg[:n]] for n in N_GRID}

    warm_results: dict = {}
    for N in N_GRID:
        for model_name in MODELS:
            warm_results[(N, model_name, 42)] = {"folds": []}

    seed = 42
    kf = KFold(n_splits=5, shuffle=True, random_state=seed)
    warm_splits = list(kf.split(X_warm, y_warm))
    for fold, (tr, te) in enumerate(warm_splits, 1):
        logger.info(f"\n  Warm fold {fold}/5 (seed {seed})")
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
                fm = {
                    "seed": seed, "fold": fold,
                    "ensemble": _summary_fold(y_te_price, pred_price),
                    "elapsed_sec": round(time.time() - t1, 1),
                }
                warm_results[(N, model_name, seed)]["folds"].append(fm)
            logger.info(f"    N={N:>2}: 3 models done ({sum(warm_results[(N, m, seed)]['folds'][-1]['elapsed_sec'] for m in MODELS):.1f}s)")

    # Aggregate
    summary_rows = []
    for N in N_GRID:
        for model_name in MODELS:
            cf = cold_results[(N, model_name)]["folds"]
            cold_ens_vals = [f["ensemble"]["MdAPE"] for f in cf]
            artsy = [f.get("artsy_ensemble", {}).get("MdAPE") for f in cf]
            artsy = [v for v in artsy if v is not None]
            saatchi = [f.get("saatchi_ensemble", {}).get("MdAPE") for f in cf]
            saatchi = [v for v in saatchi if v is not None]

            wf = warm_results[(N, model_name, 42)]["folds"]
            warm_ens_vals = [f["ensemble"]["MdAPE"] for f in wf]

            row = {
                "N": N,
                "model": model_name,
                "cold_ens_median": float(np.median(cold_ens_vals)),
                "cold_ens_mean": float(np.mean(cold_ens_vals)),
                "cold_ens_std": float(np.std(cold_ens_vals, ddof=0)),
                "cold_ens_min": float(np.min(cold_ens_vals)),
                "cold_ens_max": float(np.max(cold_ens_vals)),
                "cold_artsy_median": float(np.median(artsy)) if artsy else None,
                "cold_saatchi_median": float(np.median(saatchi)) if saatchi else None,
                "warm_ens_median": float(np.median(warm_ens_vals)),
                "warm_ens_std": float(np.std(warm_ens_vals, ddof=0)),
                "winner_eligible": model_name in WINNER_ELIGIBLE,
            }
            row["delta_cold_vs_baseline"] = round(row["cold_ens_median"] - BASELINE_ANCHOR["cold_ensemble"], 4)
            row["delta_warm_vs_baseline"] = round(row["warm_ens_median"] - BASELINE_ANCHOR["warm_kfold_ensemble"], 4)
            row["delta_artsy_vs_baseline"] = round(row["cold_artsy_median"] - BASELINE_ANCHOR["cold_artsy_ensemble"], 4) if row["cold_artsy_median"] else None
            row["delta_saatchi_vs_baseline"] = round(row["cold_saatchi_median"] - BASELINE_ANCHOR["cold_saatchi_ensemble"], 4) if row["cold_saatchi_median"] else None
            row["g1_pass"] = bool(row["delta_warm_vs_baseline"] <= 0.5)
            row["g2_pass"] = bool(row["delta_cold_vs_baseline"] <= 0.8)
            row["g3_pass"] = bool(row["delta_artsy_vs_baseline"] is not None and row["delta_artsy_vs_baseline"] <= 1.0)
            row["g4_pass"] = bool(row["delta_saatchi_vs_baseline"] is not None and row["delta_saatchi_vs_baseline"] <= 1.0)
            row["all_guards_pass"] = row["g1_pass"] and row["g2_pass"] and row["g3_pass"] and row["g4_pass"]
            summary_rows.append(row)

    # 1-SE winner
    eligible_passed = [r for r in summary_rows if r["winner_eligible"] and r["all_guards_pass"]]
    if not eligible_passed:
        winner = None
        winner_reason = "No winner-eligible config passed all guards."
        noise_band_set = []
    else:
        best_cold = min(r["cold_ens_median"] for r in eligible_passed)
        threshold = best_cold + NOISE_SE_PP
        noise_band_set = sorted(
            [r for r in eligible_passed if r["cold_ens_median"] <= threshold],
            key=lambda r: (r["N"], {"catboost": 0, "xgboost": 1, "ensemble_cb_xgb": 2}.get(r["model"], 99))
        )
        winner = noise_band_set[0]
        winner_reason = f"1-SE rule (band={NOISE_SE_PP}%p / best_cold={best_cold:.3f}) → smallest N + winner-eligible model priority"

    out = {
        "amendment_doc": "docs/feature_sweep_amendment_20260509.md",
        "decision_binding": False,
        "config_simplified": True,
        "n_grid": N_GRID,
        "models": MODELS,
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

    import csv
    with open(OUT_MATRIX, "w") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    logger.info(f"[OK] {OUT_MATRIX.name}")

    print("\n" + "=" * 100)
    print(f"Feature Sweep (SIMPLIFIED) — {len(summary_rows)} configs")
    print("=" * 100)
    print(f"\n{'N':>3} {'model':>17s} {'cold_med':>9s} {'cold_min':>9s} {'cold_max':>9s} {'warm_med':>9s} {'artsy':>7s} {'saatchi':>8s} {'guards':>7s} {'Δcold':>9s} {'Δwarm':>9s}")
    print("-" * 100)
    for r in summary_rows:
        guards = ''.join(['1' if r[f'g{i}_pass'] else '0' for i in range(1, 5)])
        print(f"{r['N']:>3} {r['model']:>17s} {r['cold_ens_median']:>9.3f} {r['cold_ens_min']:>9.3f} {r['cold_ens_max']:>9.3f} "
              f"{r['warm_ens_median']:>9.3f} {(r['cold_artsy_median'] or 0):>7.2f} "
              f"{(r['cold_saatchi_median'] or 0):>8.2f} {guards:>7s} "
              f"{r['delta_cold_vs_baseline']:>+9.3f} {r['delta_warm_vs_baseline']:>+9.3f}")

    print(f"\n=== 1-SE Noise Band Dominant Set ({len(noise_band_set)}) ===")
    for r in noise_band_set:
        print(f"  N={r['N']:>2} / {r['model']:<17s} / cold_med={r['cold_ens_median']:.3f}")

    print(f"\n=== WINNER ===")
    if winner:
        print(f"  N={winner['N']} / model={winner['model']}")
        print(f"  cold_ens_median: {winner['cold_ens_median']:.3f} (Δ {winner['delta_cold_vs_baseline']:+.3f} vs 38.622)")
        print(f"  warm_ens_median: {winner['warm_ens_median']:.3f} (Δ {winner['delta_warm_vs_baseline']:+.3f} vs 10.468)")
        print(f"  Reason: {winner_reason}")
    else:
        print(f"  None — {winner_reason}")


if __name__ == "__main__":
    main()
