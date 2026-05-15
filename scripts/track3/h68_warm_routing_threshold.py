"""Track 3 H68 — Warm/Cold routing threshold by artist training count."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
    COLD_BASE_FEATURES,
    REPO,
    SEEDS,
    SPLIT,
    TARGET,
    WARM_H31_CAT,
    WARM_H31_FEATURES,
    add_features,
    add_history,
    build_artist_history,
    build_lad,
    metric,
    to_cat,
)
from h61_h65_model_improvement_followups import train_lgb_fixed
from h66_warm_lgbm_retune_multiseed import PARAMS as H66_PARAMS


OUT_PATH = REPO / "data" / "track3_h68_warm_routing_threshold_results.json"
THRESHOLDS = [1, 2, 3, 5, 10, 20, 50]


def ape_values(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> np.ndarray:
    y_true = np.exp(y_true_ln)
    y_pred = np.exp(y_pred_ln)
    return np.abs(y_pred - y_true) / y_true


def threshold_policy_metric(warm: pd.DataFrame, warm_pred: np.ndarray, fallback_pred: np.ndarray, threshold: int) -> dict:
    use_warm = warm["artist_count"].ge(threshold).to_numpy()
    pred = fallback_pred.copy()
    pred[use_warm] = warm_pred[use_warm]
    out = metric(warm[TARGET].values, pred)
    out["threshold"] = int(threshold)
    out["warm_model_rows"] = int(use_warm.sum())
    out["fallback_rows"] = int((~use_warm).sum())
    out["warm_model_ratio"] = float(use_warm.mean())
    return out


def slice_metrics_by_count(warm: pd.DataFrame, pred_map: dict[str, np.ndarray]) -> dict:
    bins = {
        "count_1": warm["artist_count"].eq(1).to_numpy(),
        "count_2_4": (warm["artist_count"].ge(2) & warm["artist_count"].le(4)).to_numpy(),
        "count_5_9": (warm["artist_count"].ge(5) & warm["artist_count"].le(9)).to_numpy(),
        "count_10_19": (warm["artist_count"].ge(10) & warm["artist_count"].le(19)).to_numpy(),
        "count_20_plus": warm["artist_count"].ge(20).to_numpy(),
    }
    result = {}
    for pred_name, pred in pred_map.items():
        result[pred_name] = {}
        for bin_name, mask in bins.items():
            if int(mask.sum()) < 10:
                continue
            row = metric(warm.loc[mask, TARGET].values, pred[mask])
            row["artist_count_min"] = float(warm.loc[mask, "artist_count"].min())
            row["artist_count_max"] = float(warm.loc[mask, "artist_count"].max())
            result[pred_name][bin_name] = row
    return result


def paired_wins(warm: pd.DataFrame, warm_pred: np.ndarray, fallback_pred: np.ndarray) -> dict:
    warm_ape = ape_values(warm[TARGET].values, warm_pred)
    fallback_ape = ape_values(warm[TARGET].values, fallback_pred)
    result = {}
    for max_count in [1, 2, 3, 5, 10]:
        mask = warm["artist_count"].le(max_count).to_numpy()
        if int(mask.sum()) < 10:
            continue
        result[f"artist_count_le_{max_count}"] = {
            "n": int(mask.sum()),
            "warm_median_ape": float(np.median(warm_ape[mask])),
            "fallback_median_ape": float(np.median(fallback_ape[mask])),
            "fallback_win_rate": float(np.mean(fallback_ape[mask] < warm_ape[mask])),
            "fallback_better_10pp": int(np.sum((warm_ape[mask] - fallback_ape[mask]) >= 0.10)),
            "fallback_worse_10pp": int(np.sum((fallback_ape[mask] - warm_ape[mask]) >= 0.10)),
        }
    return result


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)

    warm_preds = []
    warm_per_seed = []
    for seed in SEEDS:
        model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, H66_PARAMS["larger_low_lr"], seed=seed)
        pred = model.predict(to_cat(warm, WARM_H31_FEATURES, WARM_H31_CAT))
        warm_preds.append(pred)
        row = metric(warm[TARGET].values, pred)
        row["seed"] = seed
        row["best_iteration"] = int(model.best_iteration)
        warm_per_seed.append(row)
    warm_pred = np.mean(warm_preds, axis=0)

    cold_fallback_model = build_lad(COLD_BASE_FEATURES)
    cold_fallback_model.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_fallback_pred = cold_fallback_model.predict(warm[COLD_BASE_FEATURES])

    policies = {
        f"warm_if_count_ge_{threshold}": threshold_policy_metric(warm, warm_pred, cold_fallback_pred, threshold)
        for threshold in THRESHOLDS
    }
    always_warm = metric(warm[TARGET].values, warm_pred)
    always_warm["warm_model_rows"] = int(len(warm))
    always_warm["fallback_rows"] = 0
    always_warm["warm_model_ratio"] = 1.0
    always_cold_fallback = metric(warm[TARGET].values, cold_fallback_pred)
    always_cold_fallback["warm_model_rows"] = 0
    always_cold_fallback["fallback_rows"] = int(len(warm))
    always_cold_fallback["warm_model_ratio"] = 0.0

    result = {
        "experiment_id": "H68_warm_routing_threshold",
        "date": "2026-05-14",
        "reason": "Test whether Warm model routing should require more than one training artwork per artist.",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "train_artists": int(train["artist_name_ko"].nunique())},
        "models": {
            "warm": "H66 larger-low-lr LightGBM, averaged over seeds 11/22/33",
            "fallback": "Cold base Quantile/LAD model using COLD_BASE_FEATURES, applied to Warm low-count artists",
        },
        "warm_per_seed": warm_per_seed,
        "references": {
            "always_warm": always_warm,
            "always_cold_fallback_on_warm": always_cold_fallback,
        },
        "threshold_policies": policies,
        "slice_metrics": slice_metrics_by_count(
            warm,
            {"warm_h66": warm_pred, "cold_fallback": cold_fallback_pred},
        ),
        "paired_low_count_comparison": paired_wins(warm, warm_pred, cold_fallback_pred),
    }

    best = min(policies, key=lambda key: policies[key]["median_ape"])
    base = always_warm["median_ape"]
    result["judgement"] = {
        "best_threshold_policy": best,
        "best_threshold_median_ape": policies[best]["median_ape"],
        "always_warm_median_ape": base,
        "delta_best_vs_always_warm": policies[best]["median_ape"] - base,
        "adopt_threshold_routing": bool(policies[best]["median_ape"] <= base - 0.003),
        "note": "If threshold routing does not improve median APE meaningfully, keep artist_count>=1 as Warm and expose low-count confidence warnings instead.",
    }

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H68 Warm routing threshold")
    print(f"saved: {OUT_PATH}")
    print(f"always_warm={base:.4f}")
    print(f"always_cold_fallback_on_warm={always_cold_fallback['median_ape']:.4f}")
    for name, row in policies.items():
        print(
            f"{name:<24} median={row['median_ape']:.4f} "
            f"p95={row['p95_ape']:.4f} warm_rows={row['warm_model_rows']} fallback_rows={row['fallback_rows']}"
        )
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
