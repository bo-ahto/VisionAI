"""Source-Conditional Cycle — Separate Models (decision-binding).

prereg = docs/source_conditional_prereg_20260509.md
Decision binding ✅ YES.

Method (locked):
- Fresh Holdout (random_state=20260510 / artist GroupShuffleSplit / 80/20)
- Separate test: Artsy-only Ensemble + Saatchi-only Ensemble (32f / 운영 best_params)
- Comparator: Unified 32 + Ensemble (운영 정합 / 같은 fresh split)
- Decision: Saatchi Δ ≤ -0.5%p (개선 의무) AND overall Δ ≤ +0.8 AND Artsy Δ ≤ +1.0
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
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _mdape,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "source_conditional_results.json"

HOLDOUT_RANDOM_STATE = 20260510  # FRESH (Confirmatory 20260509 재사용 X)
HOLDOUT_FRACTION = 0.20

PRIMARY_THRESHOLD = 0.8     # overall cold Δ ≤ +0.8
ARTSY_THRESHOLD = 1.0       # Artsy cold Δ ≤ +1.0
SAATCHI_THRESHOLD = -0.5    # Saatchi Δ ≤ -0.5 (개선 의무)


def _summary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {"n": len(y_true), "MdAPE": float(_mdape(y_true, y_pred))}


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


def predict_ensemble(
    X_tr: pd.DataFrame, y_tr: np.ndarray, X_te: pd.DataFrame,
    cat_features: list[str], cb_best: dict, xgb_best: dict, seed: int = 42,
) -> np.ndarray:
    cb = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=0, random_seed=seed,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X_tr, y_tr, cat_features))
    cb_pred = cb.predict(_cb_pool(X_te, None, cat_features))

    Xtr_e, Xte_e = _local_label_encode(X_tr, X_te, cat_features)
    dtrain = xgb.DMatrix(Xtr_e, label=y_tr)
    dtest = xgb.DMatrix(Xte_e)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    m = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": seed},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )
    xgb_pred = m.predict(dtest)
    return (cb_pred + xgb_pred) / 2.0


def cv_cold_eval(
    X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
    cat_features: list[str], cb_best: dict, xgb_best: dict, *, label: str,
) -> dict:
    """source 별 (subset) GroupKFold-5 cold MdAPE."""
    gkf = GroupKFold(n_splits=5)
    fold_metrics = []
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        t0 = time.time()
        pred_log = predict_ensemble(X.iloc[tr], y[tr], X.iloc[te], cat_features, cb_best, xgb_best)
        f = {
            "fold": fold,
            "MdAPE": float(_mdape(np.exp(y[te]), np.exp(pred_log))),
            "elapsed_sec": round(time.time() - t0, 1),
        }
        fold_metrics.append(f)
        logger.info(f"  {label} cold fold {fold}/5: {f['MdAPE']:.3f} ({f['elapsed_sec']}s)")
    return {"folds": fold_metrics, "median": float(np.median([f["MdAPE"] for f in fold_metrics]))}


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Source-Conditional Cycle — Separate Models (decision-binding ✓)")
    logger.info("=" * 70)

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    X_full, y, groups = prepare_features(df)
    source_full = df["source"].astype(str).to_numpy()

    # ─── Step 1: Fresh Holdout split ──────────────────────────────────
    logger.info(f"\n--- Step 1: Fresh Holdout split (random_state={HOLDOUT_RANDOM_STATE}) ---")
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

    # source 별 split
    artsy_train_mask = source_train == "artsy"
    saatchi_train_mask = source_train == "saatchi"
    artsy_holdout_mask = source_holdout == "artsy"
    saatchi_holdout_mask = source_holdout == "saatchi"

    logger.info(f"  Train Artsy: {artsy_train_mask.sum()} / Saatchi: {saatchi_train_mask.sum()}")
    logger.info(f"  Holdout Artsy: {artsy_holdout_mask.sum()} / Saatchi: {saatchi_holdout_mask.sum()}")

    # 32 features 사용
    features = list(CB_FEATURES)
    cat_features_iter = [c for c in CAT_FEATURES if c in features]

    X_train_f = X_train[features].copy()
    X_holdout_f = X_holdout[features].copy()

    # ─── Step 2: 80% CV cold per source (sanity / non-binding) ────────
    logger.info(f"\n--- Step 2: 80% CV cold (source 별 / sanity) ---")

    # Artsy-only CV (within 80% Artsy)
    X_artsy_tr = X_train_f[artsy_train_mask].reset_index(drop=True)
    y_artsy_tr = y_train[artsy_train_mask]
    g_artsy_tr = groups_train[artsy_train_mask]
    cv_artsy = cv_cold_eval(X_artsy_tr, y_artsy_tr, g_artsy_tr, cat_features_iter,
                             cb_best, xgb_best, label="Artsy-only")

    # Saatchi-only CV (within 80% Saatchi)
    X_saatchi_tr = X_train_f[saatchi_train_mask].reset_index(drop=True)
    y_saatchi_tr = y_train[saatchi_train_mask]
    g_saatchi_tr = groups_train[saatchi_train_mask]
    cv_saatchi = cv_cold_eval(X_saatchi_tr, y_saatchi_tr, g_saatchi_tr, cat_features_iter,
                               cb_best, xgb_best, label="Saatchi-only")

    # ─── Step 3: Holdout test (3 configs / final / 1회) ───────────────
    logger.info(f"\n--- Step 3: Holdout test (3 configs) ---")

    # Config A: Artsy-only (80% Artsy retrain → Holdout Artsy predict)
    logger.info(f"  A. Artsy-only model")
    t1 = time.time()
    pred_artsy_log = predict_ensemble(
        X_artsy_tr, y_artsy_tr, X_holdout_f[artsy_holdout_mask].reset_index(drop=True),
        cat_features_iter, cb_best, xgb_best,
    )
    artsy_only_holdout = _summary(np.exp(y_holdout[artsy_holdout_mask]), np.exp(pred_artsy_log))
    logger.info(f"     Artsy-only Holdout (Artsy slice): {artsy_only_holdout['MdAPE']:.3f} ({time.time()-t1:.1f}s)")

    # Config B: Saatchi-only (80% Saatchi retrain → Holdout Saatchi predict)
    logger.info(f"  B. Saatchi-only model")
    t1 = time.time()
    pred_saatchi_log = predict_ensemble(
        X_saatchi_tr, y_saatchi_tr, X_holdout_f[saatchi_holdout_mask].reset_index(drop=True),
        cat_features_iter, cb_best, xgb_best,
    )
    saatchi_only_holdout = _summary(np.exp(y_holdout[saatchi_holdout_mask]), np.exp(pred_saatchi_log))
    logger.info(f"     Saatchi-only Holdout (Saatchi slice): {saatchi_only_holdout['MdAPE']:.3f} ({time.time()-t1:.1f}s)")

    # Combined separate routed (overall = Artsy-only Artsy + Saatchi-only Saatchi)
    y_holdout_artsy = y_holdout[artsy_holdout_mask]
    y_holdout_saatchi = y_holdout[saatchi_holdout_mask]
    y_combined = np.concatenate([np.exp(y_holdout_artsy), np.exp(y_holdout_saatchi)])
    pred_combined = np.concatenate([np.exp(pred_artsy_log), np.exp(pred_saatchi_log)])
    separate_routed_overall = _summary(y_combined, pred_combined)
    logger.info(f"     Separate routed (overall): {separate_routed_overall['MdAPE']:.3f}")

    # Config C: Unified 32 + Ensemble (BINDING comparator / 80% all retrain)
    logger.info(f"  C. Unified 32+Ensemble (BINDING comparator)")
    t1 = time.time()
    pred_unified_log = predict_ensemble(
        X_train_f, y_train, X_holdout_f, cat_features_iter, cb_best, xgb_best,
    )
    unified_overall = _summary(np.exp(y_holdout), np.exp(pred_unified_log))
    unified_artsy = _summary(np.exp(y_holdout[artsy_holdout_mask]),
                              np.exp(pred_unified_log[artsy_holdout_mask]))
    unified_saatchi = _summary(np.exp(y_holdout[saatchi_holdout_mask]),
                                np.exp(pred_unified_log[saatchi_holdout_mask]))
    logger.info(f"     Unified Holdout overall: {unified_overall['MdAPE']:.3f}")
    logger.info(f"     Unified Holdout Artsy:   {unified_artsy['MdAPE']:.3f}")
    logger.info(f"     Unified Holdout Saatchi: {unified_saatchi['MdAPE']:.3f}")
    logger.info(f"     ({time.time()-t1:.1f}s)")

    # ─── Step 4: Decision (BINDING) ───────────────────────────────────
    delta_overall = separate_routed_overall["MdAPE"] - unified_overall["MdAPE"]
    delta_artsy = artsy_only_holdout["MdAPE"] - unified_artsy["MdAPE"]
    delta_saatchi = saatchi_only_holdout["MdAPE"] - unified_saatchi["MdAPE"]

    pass_primary = delta_overall <= PRIMARY_THRESHOLD
    pass_artsy = delta_artsy <= ARTSY_THRESHOLD
    pass_saatchi = delta_saatchi <= SAATCHI_THRESHOLD

    all_pass = pass_primary and pass_artsy and pass_saatchi
    verdict = "CHAMPION" if all_pass else "FAIL"

    out = {
        "prereg": "docs/source_conditional_prereg_20260509.md",
        "decision_binding": True,
        "holdout_random_state": HOLDOUT_RANDOM_STATE,
        "n_train": int(len(X_train)),
        "n_holdout": int(len(X_holdout)),
        "n_artists_train": int(len(set(groups_train))),
        "n_artists_holdout": int(len(set(groups_holdout))),
        "train_artsy_n": int(artsy_train_mask.sum()),
        "train_saatchi_n": int(saatchi_train_mask.sum()),
        "holdout_artsy_n": int(artsy_holdout_mask.sum()),
        "holdout_saatchi_n": int(saatchi_holdout_mask.sum()),
        "cv_80": {
            "artsy_only_cold_median": cv_artsy["median"],
            "saatchi_only_cold_median": cv_saatchi["median"],
            "artsy_folds": cv_artsy["folds"],
            "saatchi_folds": cv_saatchi["folds"],
        },
        "holdout": {
            "separate_routed_overall": separate_routed_overall,
            "artsy_only_artsy_slice": artsy_only_holdout,
            "saatchi_only_saatchi_slice": saatchi_only_holdout,
            "unified_overall": unified_overall,
            "unified_artsy_slice": unified_artsy,
            "unified_saatchi_slice": unified_saatchi,
        },
        "binding_comparison": {
            "delta_overall": delta_overall,
            "delta_artsy": delta_artsy,
            "delta_saatchi": delta_saatchi,
            "primary_threshold": PRIMARY_THRESHOLD,
            "artsy_threshold": ARTSY_THRESHOLD,
            "saatchi_threshold": SAATCHI_THRESHOLD,
            "pass_primary": pass_primary,
            "pass_artsy": pass_artsy,
            "pass_saatchi": pass_saatchi,
            "all_pass": all_pass,
            "verdict": verdict,
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    # Print summary
    print("\n" + "=" * 80)
    print("Source-Conditional Cycle Results")
    print("=" * 80)
    print(f"\nFresh Holdout (random_state={HOLDOUT_RANDOM_STATE}):")
    print(f"  Train (80%): {len(X_train)} rows / {len(set(groups_train))} artists")
    print(f"  Holdout (20%): {len(X_holdout)} rows / {len(set(groups_holdout))} artists")
    print(f"  Holdout Artsy: {artsy_holdout_mask.sum()} / Saatchi: {saatchi_holdout_mask.sum()}")

    print(f"\n=== Holdout MdAPE (cold) ===")
    print(f"{'config':30s} {'overall':>10s} {'Artsy':>10s} {'Saatchi':>10s}")
    print(f"{'Separate routed (TEST)':30s} {separate_routed_overall['MdAPE']:>10.3f} "
          f"{artsy_only_holdout['MdAPE']:>10.3f} {saatchi_only_holdout['MdAPE']:>10.3f}")
    print(f"{'Unified 32+Ens (BASELINE)':30s} {unified_overall['MdAPE']:>10.3f} "
          f"{unified_artsy['MdAPE']:>10.3f} {unified_saatchi['MdAPE']:>10.3f}")

    print(f"\n=== Δ Separate − Unified ===")
    print(f"  Δ overall = {delta_overall:+.3f} (threshold ≤+{PRIMARY_THRESHOLD}) {'✓' if pass_primary else '✗'}")
    print(f"  Δ Artsy   = {delta_artsy:+.3f} (threshold ≤+{ARTSY_THRESHOLD}) {'✓' if pass_artsy else '✗'}")
    print(f"  Δ Saatchi = {delta_saatchi:+.3f} (threshold ≤{SAATCHI_THRESHOLD} 개선 의무) {'✓' if pass_saatchi else '✗'}")

    print(f"\n=== VERDICT: {verdict} ===")
    if verdict == "CHAMPION":
        print("  → Source-conditional 운영 적용 가능 (decision-binding)")
    else:
        print("  → 운영 unified 32+Ensemble 유지 (decision-binding)")


if __name__ == "__main__":
    main()
