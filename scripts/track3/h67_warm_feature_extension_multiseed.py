"""Track 3 H67 — multi-seed validation for H57/H58 Warm feature extensions."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

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
from h48_h60_pending_followups import add_extended_artist_history, add_interactions
from h61_h65_model_improvement_followups import train_lgb_fixed
from h66_warm_lgbm_retune_multiseed import PARAMS as H66_PARAMS


OUT_PATH = REPO / "data" / "track3_h67_warm_feature_extension_multiseed_results.json"

H57_FEATURES = [
    "artist_ln_price_min",
    "artist_ln_price_max",
    "artist_ln_price_p25",
    "artist_ln_price_p75",
    "artist_ln_price_p90",
    "artist_high_price_share",
    "artist_price_range",
]
H58_FEATURES = [
    "artist_median_x_log_area",
    "artist_median_x_log_ho",
    "artist_works_x_log_area",
    "artist_works_x_large_ho",
]


def summarize(rows: list[dict]) -> dict:
    med = np.array([row["median_ape"] for row in rows], dtype=float)
    p95 = np.array([row["p95_ape"] for row in rows], dtype=float)
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
    train_ext = add_interactions(add_extended_artist_history(train, train))
    warm_ext = add_interactions(add_extended_artist_history(train, warm))

    variants = {
        "h66_base": {
            "features": WARM_H31_FEATURES,
            "cat_cols": WARM_H31_CAT,
            "train": train,
            "warm": warm,
        },
        "h57_extended_history": {
            "features": WARM_H31_FEATURES + H57_FEATURES,
            "cat_cols": WARM_H31_CAT,
            "train": train_ext,
            "warm": warm_ext,
        },
        "h58_interactions": {
            "features": WARM_H31_FEATURES + H58_FEATURES,
            "cat_cols": WARM_H31_CAT,
            "train": train_ext,
            "warm": warm_ext,
        },
        "h57_h58_combined": {
            "features": WARM_H31_FEATURES + H57_FEATURES + H58_FEATURES,
            "cat_cols": WARM_H31_CAT,
            "train": train_ext,
            "warm": warm_ext,
        },
    }

    result = {
        "experiment_id": "H67_warm_feature_extension_multiseed",
        "date": "2026-05-14",
        "reason": "Multi-seed validation of H57/H58 Warm feature extension gains after the H66 retune.",
        "seeds": SEEDS,
        "data": {"train_rows": len(train), "warm_rows": len(warm)},
        "variants": {},
    }

    for name, cfg in variants.items():
        rows = []
        for seed in SEEDS:
            model = train_lgb_fixed(
                cfg["train"],
                cfg["features"],
                cfg["cat_cols"],
                H66_PARAMS["larger_low_lr"],
                seed=seed,
            )
            pred = model.predict(to_cat(cfg["warm"], cfg["features"], cfg["cat_cols"]))
            row = metric(cfg["warm"][TARGET].values, pred)
            row["seed"] = seed
            row["best_iteration"] = int(model.best_iteration)
            rows.append(row)
        result["variants"][name] = {
            "n_features": len(cfg["features"]),
            "added_features": [f for f in cfg["features"] if f not in WARM_H31_FEATURES],
            "per_seed": rows,
            "summary": summarize(rows),
        }

    base = result["variants"]["h66_base"]["summary"]["mean_median_ape"]
    for name, row in result["variants"].items():
        row["delta_vs_h66_base"] = row["summary"]["mean_median_ape"] - base

    best = min(result["variants"], key=lambda key: result["variants"][key]["summary"]["mean_median_ape"])
    result["judgement"] = {
        "best_variant": best,
        "best_mean_median_ape": result["variants"][best]["summary"]["mean_median_ape"],
        "h66_base_mean_median_ape": base,
        "delta_best_vs_h66_base": result["variants"][best]["summary"]["mean_median_ape"] - base,
        "adopt_feature_extension": bool(
            best != "h66_base"
            and result["variants"][best]["summary"]["mean_median_ape"] <= base - 0.003
            and result["variants"][best]["summary"]["mean_p95_ape"]
            <= result["variants"]["h66_base"]["summary"]["mean_p95_ape"] + 0.03
        ),
        "note": "Lower median APE is better. Adoption requires multi-seed improvement without material p95 deterioration.",
    }

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H67 Warm feature extension multi-seed")
    print(f"saved: {OUT_PATH}")
    for name, row in result["variants"].items():
        s = row["summary"]
        print(
            f"{name:<24} mean={s['mean_median_ape']:.4f} "
            f"std={s['std_median_ape']:.4f} p95={s['mean_p95_ape']:.4f} "
            f"delta={row['delta_vs_h66_base']:+.4f}"
        )
    print(json.dumps(result["judgement"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
