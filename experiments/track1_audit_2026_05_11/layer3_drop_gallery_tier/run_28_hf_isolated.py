"""Layer 3.A isolated cycle — gallery_tier 단독 제거 (29f_hf → 28_hf).

Pre-context:
- PR-FOLLOWERS-FALLBACK (직전 commit): 28f + has_followers = 29f_hf (PASS_NEUTRAL)
- Layer 3 audit (Codex R1 GO):
  - gallery_tier: Artsy 4 unique (2/3/4/5), Saatchi 100% constant=3
  - Serving: matched=3 / unmatched=4 (artist_matcher.py:102 + primary_feature_builder.py:218)
  - for_sale_ratio와 동일 패턴 — serve-time identifiability zero
  - PSI=1.60 SIGNIFICANT

Drops: gallery_tier (CB_FEATURES_BASE_29_HF - 1 = 28 features)
Cat features 변동 없음 (5개).
Codex R1 권고: 29f_hf base → 28_hf cycle (운영 후보 baseline)
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
    CB_FEATURES_BASE_29_HF,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "layer3_28_hf_results.json"

DROP_FEATURES = ["gallery_tier"]
NEW_FEATURES = [f for f in CB_FEATURES_BASE_29_HF if f not in DROP_FEATURES]
NEW_CAT_FEATURES = CAT_FEATURES_29

BASELINE_ANCHORS = {
    # PR-FOLLOWERS-FALLBACK Step A result (29f_hf)
    "29f_hf": {
        "cold_ensemble":          39.5151,
        "cold_artsy_ensemble":    35.4307,
        "cold_saatchi_ensemble":  42.0056,
        "warm_kfold_xgboost":      9.8076,
        "warm_kfold_ensemble":    10.5664,
    },
    # PR-28F result
    "28f": {
        "cold_ensemble":          38.9356,
        "cold_artsy_ensemble":    34.4108,
        "cold_saatchi_ensemble":  41.5995,
        "warm_kfold_xgboost":      9.8794,
        "warm_kfold_ensemble":    10.6196,
    },
}


def _summary_fold(y_true_price: np.ndarray, y_pred_price: np.ndarray) -> dict:
    return {"n": len(y_true_price), "MdAPE": float(_mdape(y_true_price, y_pred_price))}


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in NEW_CAT_FEATURES if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb(
    X_train: pd.DataFrame, X_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps: dict[str, dict[str, int]] = {}
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


def _cv_run(
    X: pd.DataFrame, y: np.ndarray, splits: list, source: np.ndarray | None,
    cb_params: dict, xgb_params: dict, *, label: str,
) -> dict:
    fold_results: list[dict] = []
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


def compute_std(folds: list[dict], path: list[str]) -> dict:
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


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Layer 3.A isolated — gallery_tier 단독 제거 (29f_hf → 28_hf)")
    logger.info("=" * 70)
    logger.info(f"DROP: {DROP_FEATURES}")
    logger.info(f"Features: {len(NEW_FEATURES)} = 29 - 1")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source_arr = df["source"].astype(str).to_numpy()

    # 28f base + has_followers inline (PR-FOLLOWERS-FALLBACK pattern), 그 후 gallery_tier 제거
    X_base = X_full[CB_FEATURES_BASE_28].copy()
    X_base["has_followers"] = (X_base["ln_followers"] > 0).astype(int)
    X = X_base[NEW_FEATURES].copy()  # has_followers 포함, gallery_tier 제외

    assert len(X.columns) == 28
    assert "gallery_tier" not in X.columns
    assert "has_followers" in X.columns

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

    deltas_29hf, deltas_28 = {}, {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        m = round(v["mean"], 4)
        for label, baseline_dict, target in (
            ("29f_hf", BASELINE_ANCHORS["29f_hf"], deltas_29hf),
            ("28f", BASELINE_ANCHORS["28f"], deltas_28),
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
    d_cold = deltas_29hf.get("cold_ensemble", {}).get("delta", 0)
    d_warm_xgb = deltas_29hf.get("warm_kfold_xgboost", {}).get("delta", 0)
    d_warm_ens = deltas_29hf.get("warm_kfold_ensemble", {}).get("delta", 0)

    cold_in_noise = abs(d_cold) < 0.5 * cold_std
    warm_in_noise = abs(d_warm_xgb) < 2 * warm_xgb_std

    out = {
        "cycle": "Layer 3.A isolated — gallery_tier 단독 제거",
        "n_features_before": 29,
        "n_features_after": 28,
        "features_dropped": DROP_FEATURES,
        "rationale": "gallery_tier: Saatchi 100% constant=3, serving matched=3/unmatched=4 → serve-time identifiability zero (for_sale_ratio 패턴)",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold": warm_kfold,
        "summary_std": summary,
        "deltas_vs_29f_hf_baseline": deltas_29hf,
        "deltas_vs_28f_baseline": deltas_28,
        "delta_cold_ensemble_pp_vs_29f_hf": d_cold,
        "delta_warm_xgb_pp_vs_29f_hf": d_warm_xgb,
        "delta_warm_ens_pp_vs_29f_hf": d_warm_ens,
        "cold_ensemble_std_pp": round(cold_std, 4),
        "warm_xgb_std_pp": round(warm_xgb_std, 4),
        "cold_within_noise_vs_29f_hf": cold_in_noise,
        "warm_within_noise_vs_29f_hf": warm_in_noise,
        "verdict": (
            "PASS_WITHIN_NOISE" if (cold_in_noise and warm_in_noise)
            else "PARTIAL_PASS" if cold_in_noise
            else "FAIL_BEYOND_NOISE"
        ),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 70)
    print(f"Layer 3.A RESULTS (29f_hf → 28_hf / DROP gallery_tier)")
    print("=" * 70)
    print(f"\nΔ vs 29f_hf baseline (PR-FOLLOWERS-FALLBACK):")
    print(f"{'metric':28s} {'28_hf':>10s} {'29f_hf':>10s} {'Δ vs 29f_hf':>13s}")
    for k, d in deltas_29hf.items():
        print(f"{k:28s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+13.3f}")
    print()
    print(f"=== Noise check vs 29f_hf ===")
    print(f"  Δ Cold ensemble = {d_cold:+.3f}pp (cold std={cold_std:.3f}, 0.5*std={0.5*cold_std:.3f})")
    print(f"  Δ Warm xgb      = {d_warm_xgb:+.3f}pp (warm xgb std={warm_xgb_std:.3f}, 2*std={2*warm_xgb_std:.3f})")
    print(f"  Δ Warm ens      = {d_warm_ens:+.3f}pp")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
