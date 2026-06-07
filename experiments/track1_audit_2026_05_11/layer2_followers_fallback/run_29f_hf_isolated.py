"""PR-FOLLOWERS-FALLBACK Step A isolated cycle — has_followers flag 추가 (28f → 29f_hf).

Pre-context:
- PR-28F (직전 commit): for_sale_ratio 제거 (29→28) — PASS_WITHIN_NOISE
- User 요구 + Codex R1 (A) GO: has_followers flag 도입 (has_birth_year 패턴 정합)
- 핵심: training data ln_followers=0 (8.6%, 진짜 0 followers) vs serving unmatched fallback (0) collapse

Inline 생성: has_followers = (ln_followers > 0).astype(int)
신규 features: 28 + has_followers = 29 (cat_features 변동 없음)

Expected (Codex Q4):
- cold 쪽에 더 큰 효과 가능 (unmatched 시 grade 정확도)
- warm은 "작은 변화" (existing ln_followers 그대로)
- best_params 재사용 (retune은 PASS 후 검토)
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
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS = REPO / "model_test_results"
OUT = Path(__file__).parent / "layer2_29f_hf_results.json"

# 28f base + has_followers (29 features, cat 변동 없음)
NEW_FEATURES = list(CB_FEATURES_BASE_28) + ["has_followers"]
NEW_CAT_FEATURES = CAT_FEATURES_29

BASELINE_ANCHORS = {
    # PR-28F result (Layer 2.B)
    "28f": {
        "cold_ensemble":          38.9356,
        "cold_artsy_ensemble":    34.4108,
        "cold_saatchi_ensemble":  41.5995,
        "warm_kfold_xgboost":      9.8794,
        "warm_kfold_ensemble":    10.6196,
    },
    # PR-29F result (Layer 1+)
    "29f": {
        "cold_ensemble":          39.2960,
        "cold_artsy_ensemble":    34.2823,
        "cold_saatchi_ensemble":  42.5389,
        "warm_kfold_xgboost":      9.7831,
        "warm_kfold_ensemble":    10.4828,
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
    logger.info("PR-FOLLOWERS-FALLBACK Step A — has_followers 추가 (28 → 29_hf)")
    logger.info("=" * 70)
    logger.info(f"ADD: has_followers (inline = (ln_followers > 0).astype(int))")
    logger.info(f"Features: 28 + 1 = {len(NEW_FEATURES)}")

    best_params = json.loads((ARTIFACTS / "integrated_v3_filtered_tuned_best_params.json").read_text())
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df)
    source_arr = df["source"].astype(str).to_numpy()

    # Inline has_followers (Codex Q2 권고)
    X_base = X_full[CB_FEATURES_BASE_28].copy()
    X_base["has_followers"] = (X_base["ln_followers"] > 0).astype(int)
    X = X_base[NEW_FEATURES].copy()

    assert len(X.columns) == 29
    assert "has_followers" in X.columns
    n_has = int(X["has_followers"].sum())
    logger.info(f"  has_followers=1: {n_has}/{len(X)} ({100*n_has/len(X):.1f}%)")
    logger.info(f"  has_followers=0: {len(X)-n_has}/{len(X)} ({100*(len(X)-n_has)/len(X):.1f}%)")

    logger.info("\n--- Cold GroupKFold-5 ---")
    gkf = GroupKFold(n_splits=5)
    cold_splits = list(gkf.split(X, y, groups))
    cold = _cv_run(X, y, cold_splits, source_arr, cb_best, xgb_best, label="GroupKFold")

    logger.info("\n--- Warm slice ---")
    warm_mask_arr = _warm_mask(groups)
    X_warm = X[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]
    logger.info(f"  warm n={len(X_warm)}")

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

    deltas_28f, deltas_29f = {}, {}
    for k, v in summary.items():
        if v["mean"] is None:
            continue
        m = round(v["mean"], 4)
        for label, baseline_dict, target in (
            ("28f", BASELINE_ANCHORS["28f"], deltas_28f),
            ("29f", BASELINE_ANCHORS["29f"], deltas_29f),
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
    d_cold_28f = deltas_28f.get("cold_ensemble", {}).get("delta", 0)
    d_warm_xgb_28f = deltas_28f.get("warm_kfold_xgboost", {}).get("delta", 0)
    d_warm_ens_28f = deltas_28f.get("warm_kfold_ensemble", {}).get("delta", 0)

    cold_better = d_cold_28f < 0
    warm_acceptable = abs(d_warm_xgb_28f) < 2 * warm_xgb_std

    out = {
        "cycle": "PR-FOLLOWERS-FALLBACK Step A — has_followers 추가",
        "n_features_before": 28,
        "n_features_after": 29,
        "features_added": ["has_followers"],
        "rationale": "0 = real zero vs 0 = unknown fallback 충돌 해소 (Codex R1 design A)",
        "best_params": best_params,
        "cold_groupkfold": cold,
        "warm_kfold": warm_kfold,
        "summary_std": summary,
        "deltas_vs_28f_baseline": deltas_28f,
        "deltas_vs_29f_baseline": deltas_29f,
        "delta_cold_ensemble_pp_vs_28f": d_cold_28f,
        "delta_warm_xgb_pp_vs_28f": d_warm_xgb_28f,
        "delta_warm_ens_pp_vs_28f": d_warm_ens_28f,
        "cold_ensemble_std_pp": round(cold_std, 4),
        "warm_xgb_std_pp": round(warm_xgb_std, 4),
        "cold_improvement_vs_28f": cold_better,
        "warm_acceptable_vs_28f": warm_acceptable,
        "verdict": (
            "PASS_IMPROVED" if (cold_better and warm_acceptable)
            else "PASS_NEUTRAL" if (abs(d_cold_28f) < 0.5 * cold_std and warm_acceptable)
            else "FAIL"
        ),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {OUT.name} (elapsed {out['elapsed_sec']}s)")

    print("\n" + "=" * 70)
    print(f"PR-FOLLOWERS-FALLBACK Step A RESULTS (28 → 29_hf / ADD has_followers)")
    print("=" * 70)
    print(f"\nΔ vs 28f baseline (PR-28F result):")
    print(f"{'metric':28s} {'29_hf':>10s} {'28f':>10s} {'Δ vs 28f':>10s}")
    for k, d in deltas_28f.items():
        print(f"{k:28s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+10.3f}")
    print(f"\nΔ vs 29f baseline (PR-29F result, dead 2 + source only):")
    print(f"{'metric':28s} {'29_hf':>10s} {'29f':>10s} {'Δ vs 29f':>10s}")
    for k, d in deltas_29f.items():
        print(f"{k:28s} {d['isolated_mean']:>10.3f} {d['baseline_mean']:>10.3f} {d['delta']:>+10.3f}")
    print()
    print(f"=== Noise check vs 28f ===")
    print(f"  Δ Cold ensemble = {d_cold_28f:+.3f}pp (cold std={cold_std:.3f}, 0.5*std={0.5*cold_std:.3f})")
    print(f"  Δ Warm xgb      = {d_warm_xgb_28f:+.3f}pp (warm xgb std={warm_xgb_std:.3f}, 2*std={2*warm_xgb_std:.3f})")
    print(f"  Δ Warm ens      = {d_warm_ens_28f:+.3f}pp")
    print(f"\n=== VERDICT: {out['verdict']} ===")


if __name__ == "__main__":
    main()
