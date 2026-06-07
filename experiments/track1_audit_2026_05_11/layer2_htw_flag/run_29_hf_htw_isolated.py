"""Layer 2 follow-up — has_total_works flag 추가 (28_hf → 29_hf_htw).

Pre-context:
- 28_hf base (PR-GALLERY-TIER, deploy candidate)
- artist_total_works keep 확정 (27_hf REJECTED, warm 9.3σ real signal)
- Codex 후속 권고: has_followers 패턴 정합 (missing detection)
- Distribution: Artsy 0.01% (1건) / Saatchi 1.98% (431건) has_total_works=0 — very sparse

Codex R1:
- cycle GO / deploy HOLD
- Inline: has_total_works = (artist_total_works > 0).astype(int)
- Naming: v3_filtered_tuned_29_hf_htw
- 예상: cold 소폭 +, warm 거의 0 또는 미세 -

Drops: 없음
Adds: has_total_works (CB_FEATURES_BASE_28_HF + 1 = 29 features)
Cat features 변동 없음 (5개).
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
from sklearn.model_selection import GroupKFold, KFold

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)
from visionai.price_engine.api.primary_predictor import (  # noqa: E402
    CAT_FEATURES_29,
    CB_FEATURES_BASE_28,
    CB_FEATURES_BASE_28_HF,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "layer2_29_hf_htw_results.json"

NEW_FEATURES = [*CB_FEATURES_BASE_28_HF, "has_total_works"]
NEW_CAT_FEATURES = CAT_FEATURES_29

BASELINE_ANCHORS = {
    "28_hf": {
        "cold_ensemble":          39.6473,
        "cold_artsy_ensemble":    36.0552,
        "cold_saatchi_ensemble":  42.3954,
        "warm_kfold_xgboost":      9.8497,
        "warm_kfold_ensemble":    10.5772,
    },
    "32f": {
        "cold_ensemble":          38.6224,
        "cold_artsy_ensemble":    33.5200,
        "cold_saatchi_ensemble":  41.7400,
        "warm_kfold_xgboost":      9.7140,
        "warm_kfold_ensemble":    10.4680,
    },
}


def _summary_fold(y_true_price, y_pred_price):
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _cb_pool(X, y=None):
    cat_idx = [X.columns.get_loc(c) for c in NEW_CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb(X_train, X_test):
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps = {}
    for col in NEW_CAT_FEATURES:
        if col not in X_train_e.columns:
            continue
        train_vals = X_train_e[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)
        label_maps[col] = mapping
        X_train_e[col] = X_train_e[col].map(mapping).astype(float)
        X_test_e[col] = X_test_e[col].map(mapping).fillna(unseen_idx).astype(float)
    return X_train_e, X_test_e, label_maps


def _cv_run(X, y, splits, source, cb_params, xgb_params, *, label):
    fold_results = []
    for fold, (tr, te) in enumerate(splits, 1):
        t0 = time.time()
        cb = CatBoostRegressor(
            **cb_params, loss_function="RMSE", verbose=0, random_seed=42,
            allow_writing_files=False,
        )
        cb.fit(_cb_pool(X.iloc[tr], y[tr]))
        cb_pred = cb.predict(_cb_pool(X.iloc[te]))

        Xtr_e, Xte_e, _ = _label_encode_xgb(X.iloc[tr], X.iloc[te])
        dtrain = xgb.DMatrix(Xtr_e, label=y[tr])
        dtest = xgb.DMatrix(Xte_e, label=y[te])
        xgb_p = {k: v for k, v in xgb_params.items() if k != "num_boost_round"}
        m = xgb.train(
            params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
            dtrain=dtrain, num_boost_round=xgb_params.get("num_boost_round", 1000),
        )
        xgb_pred = m.predict(dtest)

        y_te_price = np.exp(y[te])
        cb_price = np.exp(cb_pred)
        xgb_price = np.exp(xgb_pred)
        ens_price = np.exp((cb_pred + xgb_pred) / 2)

        f = {
            "fold": fold,
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "catboost": _summary_fold(y_te_price, cb_price),
            "xgboost": _summary_fold(y_te_price, xgb_price),
            "ensemble": _summary_fold(y_te_price, ens_price),
            "elapsed_sec": round(time.time() - t0, 1),
        }
        if source is not None:
            src_te = source[te]
            for src_name in sorted(set(src_te)):
                mask = src_te == src_name
                if mask.sum() == 0:
                    continue
                f[f"{src_name}_catboost"] = _summary_fold(y_te_price[mask], cb_price[mask])
                f[f"{src_name}_ensemble"] = _summary_fold(y_te_price[mask], ens_price[mask])
        fold_results.append(f)
        logger.info(f"  {label} fold {fold}/{len(splits)} done: cb={f['catboost']['MdAPE']:.2f} "
                    f"xgb={f['xgboost']['MdAPE']:.2f} ens={f['ensemble']['MdAPE']:.2f} "
                    f"({f['elapsed_sec']}s)")
    return {"folds": fold_results, "n_total": int(len(y))}


def compute_std(folds, path):
    vals = []
    for f in folds:
        cur = f
        for k in path:
            cur = cur.get(k, {})
        if isinstance(cur, dict) and "MdAPE" in cur:
            vals.append(cur["MdAPE"])
    if not vals:
        return {"std": None, "mean": None, "n_folds": 0, "values": []}
    arr = np.array(vals)
    return {
        "std": float(arr.std(ddof=0)),
        "mean": float(arr.mean()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "n_folds": len(vals),
        "values": [round(float(v), 3) for v in vals],
    }


def main():
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Layer 2 follow-up — has_total_works 추가 (28_hf → 29_hf_htw)")
    logger.info("=" * 70)
    logger.info(f"ADD: has_total_works (inline = (artist_total_works > 0).astype(int))")
    logger.info(f"Features: {len(NEW_FEATURES)} = 28 + 1")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source_arr = df["source"].astype(str).to_numpy()

    # 28_hf = 28f + has_followers - gallery_tier; here add has_total_works → 29
    X_base = X_full[CB_FEATURES_BASE_28].copy()
    X_base["has_followers"] = (X_base["ln_followers"] > 0).astype(int)
    X_28hf = X_base[CB_FEATURES_BASE_28_HF].copy()
    X_28hf["has_total_works"] = (X_28hf["artist_total_works"] > 0).astype(int)
    X = X_28hf[NEW_FEATURES].copy()

    assert len(X.columns) == 29
    assert "has_total_works" in X.columns
    assert "has_followers" in X.columns
    assert "gallery_tier" not in X.columns

    n_htw = int(X["has_total_works"].sum())
    logger.info(f"  has_total_works=1: {n_htw}/{len(X)} ({100*n_htw/len(X):.2f}%)")
    logger.info(f"  has_total_works=0: {len(X)-n_htw}/{len(X)} ({100*(len(X)-n_htw)/len(X):.2f}%)")

    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source_arr, cb_best, xgb_best, label="GroupKFold")

    logger.info("\n--- Warm slice ---")
    warm_mask_arr = _warm_mask(groups)
    X_warm = X[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]

    logger.info("\n--- Warm KFold-5 ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    warm_kfold_splits = list(kf.split(X_warm, y_warm))
    warm_kfold = _cv_run(X_warm, y_warm, warm_kfold_splits, None, cb_best, xgb_best, label="kfold")

    summary = {
        "cold_catboost":     compute_std(cold["folds"], ["catboost"]),
        "cold_xgboost":      compute_std(cold["folds"], ["xgboost"]),
        "cold_ensemble":     compute_std(cold["folds"], ["ensemble"]),
        "cold_artsy_ensemble":   compute_std(cold["folds"], ["artsy_ensemble"]),
        "cold_saatchi_ensemble": compute_std(cold["folds"], ["saatchi_ensemble"]),
        "warm_kfold_xgboost":  compute_std(warm_kfold["folds"], ["xgboost"]),
        "warm_kfold_ensemble": compute_std(warm_kfold["folds"], ["ensemble"]),
    }

    deltas_28hf, deltas_32 = {}, {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        m = round(v["mean"], 4)
        for label, baseline_dict, target in (
            ("28_hf", BASELINE_ANCHORS["28_hf"], deltas_28hf),
            ("32f", BASELINE_ANCHORS["32f"], deltas_32),
        ):
            base = baseline_dict.get(k)
            if base is None:
                continue
            target[k] = {
                "isolated_mean": m,
                "baseline_mean": base,
                "delta": round(m - base, 4),
                "baseline": label,
            }

    cold_std = summary["cold_ensemble"]["std"] or 0
    warm_xgb_std = summary["warm_kfold_xgboost"]["std"] or 0
    d_cold = deltas_28hf.get("cold_ensemble", {}).get("delta", 0)
    d_warm_xgb = deltas_28hf.get("warm_kfold_xgboost", {}).get("delta", 0)
    d_warm_ens = deltas_28hf.get("warm_kfold_ensemble", {}).get("delta", 0)

    cold_in_noise = abs(d_cold) < 0.5 * cold_std
    warm_in_noise = abs(d_warm_xgb) < 2 * warm_xgb_std

    out = {
        "cycle": "Layer 2 follow-up — has_total_works 추가 (28_hf → 29_hf_htw)",
        "n_features_before": 28,
        "n_features_after": 29,
        "features_added": ["has_total_works"],
        "rationale": "Codex Q4 권고 — has_followers 패턴 정합, missing detection. Distribution sparse: Artsy 0.01% / Saatchi 1.98% has_total_works=0.",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold": warm_kfold,
        "summary_std": summary,
        "deltas_vs_28_hf_baseline": deltas_28hf,
        "deltas_vs_32f_baseline": deltas_32,
        "delta_cold_ensemble_pp_vs_28_hf": d_cold,
        "delta_warm_xgb_pp_vs_28_hf": d_warm_xgb,
        "delta_warm_ens_pp_vs_28_hf": d_warm_ens,
        "cold_ensemble_std_pp": round(cold_std, 4),
        "warm_xgb_std_pp": round(warm_xgb_std, 4),
        "cold_within_noise_vs_28_hf": cold_in_noise,
        "warm_within_noise_vs_28_hf": warm_in_noise,
        "verdict": (
            "PASS_IMPROVED" if (d_cold < 0 and warm_in_noise)
            else "PASS_NEUTRAL" if (cold_in_noise and warm_in_noise)
            else "FAIL"
        ),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 70)
    print(f"Layer 2 follow-up RESULTS (28_hf → 29_hf_htw / ADD has_total_works)")
    print("=" * 70)
    print(f"\nΔ vs 28_hf baseline:")
    print(f"{'metric':28s} {'29_hf_htw':>10s} {'28_hf':>10s} {'Δ vs 28_hf':>12s}")
    for k, d in deltas_28hf.items():
        print(f"{k:28s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+12.3f}")
    print()
    print(f"=== Noise check vs 28_hf ===")
    print(f"  Δ Cold ensemble = {d_cold:+.3f}pp (cold std={cold_std:.3f}, 0.5*std={0.5*cold_std:.3f})")
    print(f"  Δ Warm xgb      = {d_warm_xgb:+.3f}pp (warm xgb std={warm_xgb_std:.3f}, 2*std={2*warm_xgb_std:.3f})")
    print(f"  Δ Warm ens      = {d_warm_ens:+.3f}pp")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
