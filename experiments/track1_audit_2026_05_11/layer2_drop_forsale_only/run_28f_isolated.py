"""Layer 2.B isolated cycle — for_sale_ratio 단독 제거 (PR-29F → 28f).

Pre-context:
- Layer 2.A (27f, for_sale_ratio + ln_followers 함께 제거): FAIL_BEYOND_NOISE
  - cold Δ +2.49pp vs 29f / warm xgb +0.61pp / warm ens +0.74pp
  - ln_followers warm signal 명확 — 분리 측정 필요
- Codex R2: REJECT 27f, 28f 단독 제거 cycle 권고

Drops: for_sale_ratio only (CB_FEATURES_BASE_29 - 1 = 28 features)
Expected: warm 영향 거의 0, cold 미미한 변화 (within noise)
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
    CB_FEATURES_BASE_29,
    CAT_FEATURES_29,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "layer2_28f_results.json"

DROP_FEATURES = ["for_sale_ratio"]
NEW_FEATURES = [f for f in CB_FEATURES_BASE_29 if f not in DROP_FEATURES]
NEW_CAT_FEATURES = [c for c in CAT_FEATURES_29 if c in NEW_FEATURES]

BASELINE_ANCHORS = {
    "29f": {
        "cold_ensemble":          39.2960,
        "cold_artsy_ensemble":    34.2823,
        "cold_saatchi_ensemble":  42.5389,
        "warm_kfold_xgboost":      9.7831,
        "warm_kfold_ensemble":    10.4828,
    },
    "32f": {
        "cold_ensemble":          38.6224,
        "cold_artsy_ensemble":    33.5200,
        "cold_saatchi_ensemble":  41.7400,
        "warm_kfold_xgboost":      9.7140,
        "warm_kfold_ensemble":    10.4680,
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
    logger.info("Layer 2.B isolated — for_sale_ratio 단독 제거 (29 → 28)")
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

    X = X_full[NEW_FEATURES].copy()
    assert len(X.columns) == 28, f"Expected 28 features, got {len(X.columns)}"
    assert "for_sale_ratio" not in X.columns
    assert "ln_followers" in X.columns
    assert "source" not in X.columns

    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source_arr, cb_best, xgb_best, label="GroupKFold")

    logger.info("\n--- Warm slice ---")
    warm_mask_arr = _warm_mask(groups)
    X_warm = X[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]
    g_warm = groups[warm_mask_arr]
    logger.info(f"  warm n={len(X_warm)} / artists={len(set(g_warm))}")

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

    deltas_29f, deltas_32f = {}, {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        m = round(v["mean"], 4)
        for baseline_label, baseline_dict, deltas_target in (
            ("29f", BASELINE_ANCHORS["29f"], deltas_29f),
            ("32f", BASELINE_ANCHORS["32f"], deltas_32f),
        ):
            base = baseline_dict.get(k)
            if base is None:
                continue
            deltas_target[k] = {
                "isolated_mean": m,
                "baseline_mean": base,
                "delta": round(m - base, 4),
                "baseline": baseline_label,
            }

    cold_std = summary["cold_ensemble"]["std"] or 0
    warm_xgb_std = summary["warm_kfold_xgboost"]["std"] or 0
    delta_cold_29f = deltas_29f.get("cold_ensemble", {}).get("delta", 0)
    delta_warm_xgb_29f = deltas_29f.get("warm_kfold_xgboost", {}).get("delta", 0)
    delta_warm_ens_29f = deltas_29f.get("warm_kfold_ensemble", {}).get("delta", 0)

    cold_in_noise = abs(delta_cold_29f) < 0.5 * cold_std
    # warm noise: use warm_xgb std (smaller), 2*std threshold for strict warm
    warm_in_noise = abs(delta_warm_xgb_29f) < 2 * warm_xgb_std

    out = {
        "cycle": "Layer 2.B isolated — for_sale_ratio 단독 제거",
        "n_features_before": 29,
        "n_features_after": 28,
        "features_dropped": DROP_FEATURES,
        "rationale": "for_sale_ratio: PSI=8.95, saatchi 100% 1.0 constant, serving 4 위치 1.0 하드코딩 (train-only signal)",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold": warm_kfold,
        "summary_std": summary,
        "deltas_vs_29f_baseline": deltas_29f,
        "deltas_vs_32f_baseline": deltas_32f,
        "delta_cold_ensemble_pp_vs_29f": delta_cold_29f,
        "delta_warm_xgb_pp_vs_29f": delta_warm_xgb_29f,
        "delta_warm_ens_pp_vs_29f": delta_warm_ens_29f,
        "cold_ensemble_std_pp": round(cold_std, 4),
        "warm_xgb_std_pp": round(warm_xgb_std, 4),
        "cold_within_noise_vs_29f": cold_in_noise,
        "warm_within_noise_vs_29f": warm_in_noise,
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
    print(f"Layer 2.B RESULTS (29 → 28 / DROP {DROP_FEATURES})")
    print("=" * 70)
    print(f"\nΔ vs 29f baseline:")
    print(f"{'metric':28s} {'28f':>10s} {'29f':>10s} {'Δ vs 29f':>10s}")
    for k, d in deltas_29f.items():
        print(f"{k:28s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+10.3f}")
    print()
    print(f"=== Noise check ===")
    print(f"  Δ Cold ensemble vs 29f = {delta_cold_29f:+.3f}pp (cold std={cold_std:.3f}, 0.5*std={0.5*cold_std:.3f})")
    print(f"  Δ Warm xgb vs 29f      = {delta_warm_xgb_29f:+.3f}pp (warm xgb std={warm_xgb_std:.3f}, 2*std={2*warm_xgb_std:.3f})")
    print(f"  Δ Warm ens vs 29f      = {delta_warm_ens_29f:+.3f}pp")
    print(f"  Cold within noise      = {cold_in_noise}")
    print(f"  Warm within noise      = {warm_in_noise}")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
