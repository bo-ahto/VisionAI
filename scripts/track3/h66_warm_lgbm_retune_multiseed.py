"""Track 3 H66 — multi-seed validation for H62 Warm LightGBM retuning."""
from __future__ import annotations

import json

from h61_h65_model_improvement_followups import train_lgb_fixed
from h34_h43_followup_validation import (
    REPO,
    SEEDS,
    SPLIT,
    TARGET,
    WARM_H31_CAT,
    WARM_H31_FEATURES,
    add_features,
    add_history,
    build_artist_history,
    metric,
    to_cat,
)

import numpy as np
import pandas as pd


OUT_PATH = REPO / "data" / "track3_h66_warm_lgbm_retune_multiseed_results.json"


PARAMS = {
    "h31_current_like": {
        "learning_rate": 0.04,
        "num_leaves": 198,
        "min_data_in_leaf": 75,
        "feature_fraction": 0.987,
        "bagging_fraction": 0.978,
        "bagging_freq": 5,
        "reg_alpha": 0.36,
        "reg_lambda": 4.75,
    },
    "larger_low_lr": {
        "learning_rate": 0.025,
        "num_leaves": 256,
        "min_data_in_leaf": 60,
        "feature_fraction": 0.95,
        "bagging_fraction": 0.95,
        "bagging_freq": 5,
        "reg_alpha": 0.2,
        "reg_lambda": 4.0,
    },
    "smaller_regularized": {
        "learning_rate": 0.035,
        "num_leaves": 96,
        "min_data_in_leaf": 120,
        "feature_fraction": 0.90,
        "bagging_fraction": 0.90,
        "bagging_freq": 5,
        "reg_alpha": 1.0,
        "reg_lambda": 8.0,
    },
}


def summarize(per_seed: list[dict]) -> dict:
    med = np.array([row["median_ape"] for row in per_seed], dtype=float)
    p95 = np.array([row["p95_ape"] for row in per_seed], dtype=float)
    return {
        "mean_median_ape": float(med.mean()),
        "std_median_ape": float(med.std()),
        "best_median_ape": float(med.min()),
        "worst_median_ape": float(med.max()),
        "mean_p95_ape": float(p95.mean()),
    }


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)

    result = {
        "experiment_id": "H66_warm_lgbm_retune_multiseed",
        "date": "2026-05-14",
        "reason": "Multi-seed validation of H62 Warm LightGBM retuning candidates.",
        "seeds": SEEDS,
        "data": {"train_rows": len(train), "warm_rows": len(warm)},
        "variants": {name: {"params": params, "per_seed": []} for name, params in PARAMS.items()},
    }

    for seed in SEEDS:
        for name, params in PARAMS.items():
            model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, params, seed=seed)
            pred = model.predict(to_cat(warm, WARM_H31_FEATURES, WARM_H31_CAT))
            row = metric(warm[TARGET].values, pred)
            row["seed"] = seed
            row["best_iteration"] = int(model.best_iteration)
            result["variants"][name]["per_seed"].append(row)

    for row in result["variants"].values():
        row["summary"] = summarize(row["per_seed"])

    best = min(result["variants"], key=lambda key: result["variants"][key]["summary"]["mean_median_ape"])
    base = result["variants"]["h31_current_like"]["summary"]["mean_median_ape"]
    result["judgement"] = {
        "best_variant": best,
        "best_mean_median_ape": result["variants"][best]["summary"]["mean_median_ape"],
        "h31_current_like_mean_median_ape": base,
        "delta_best_vs_current_like": result["variants"][best]["summary"]["mean_median_ape"] - base,
        "adopt_retuned_variant": bool(best != "h31_current_like" and result["variants"][best]["summary"]["mean_median_ape"] <= base - 0.003),
        "note": "Lower median APE is better. Adoption requires multi-seed improvement over the current-like H31 setting.",
    }

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H66 Warm LightGBM retune multi-seed")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        s = row["summary"]
        print(f"{name:<22} mean={s['mean_median_ape']:.4f} std={s['std_median_ape']:.4f} p95={s['mean_p95_ape']:.4f}")
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
