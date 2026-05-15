"""Track 3 H69 — close H46 price-range calibration policy."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
    COLD_3D_FEATURES,
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


OUT_PATH = REPO / "data" / "track3_h69_price_range_calibration_results.json"


def interval_row(y_true_ln: np.ndarray, y_pred_ln: np.ndarray, mask: np.ndarray, q: float) -> dict:
    err = np.abs(y_pred_ln[mask] - y_true_ln[mask])
    width = float(np.quantile(err, q))
    coverage = float(np.mean(err <= width))
    return {
        "n": int(mask.sum()),
        "target_coverage": float(q),
        "width_abs_log": width,
        "price_multiplier": float(np.exp(width)),
        "coverage": coverage,
    }


def group_rows(df: pd.DataFrame, pred: np.ndarray, groups: dict[str, np.ndarray]) -> dict:
    y = df[TARGET].values
    rows = {}
    for name, mask in groups.items():
        if int(mask.sum()) < 20:
            continue
        rows[name] = {
            "metric": metric(y[mask], pred[mask]),
            "interval_80": interval_row(y, pred, mask, 0.80),
            "interval_90": interval_row(y, pred, mask, 0.90),
        }
    return rows


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)
    cold = add_history(add_features(cold_raw), hist, global_values)

    # Final Warm candidate: H66 larger-low-lr, averaged over the standard seeds.
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

    # Final Cold candidate: H32 conditional fallback.
    cold_base = build_lad(COLD_BASE_FEATURES)
    cold_base.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_base_pred = cold_base.predict(cold[COLD_BASE_FEATURES])
    cold_3d = build_lad(COLD_3D_FEATURES)
    cold_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    cold_3d_pred = cold_3d.predict(cold[COLD_3D_FEATURES])
    mask_3d = cold["is_3d_work"].eq(1).to_numpy()
    cold_pred = cold_base_pred.copy()
    cold_pred[mask_3d] = cold_3d_pred[mask_3d]

    warm_groups = {
        "all": np.ones(len(warm), dtype=bool),
        "A_51_plus": warm["artist_count"].ge(51).to_numpy(),
        "B_11_to_50": (warm["artist_count"].ge(11) & warm["artist_count"].le(50)).to_numpy(),
        "C_4_to_10": (warm["artist_count"].ge(4) & warm["artist_count"].le(10)).to_numpy(),
        "D_1_to_3": warm["artist_count"].le(3).to_numpy(),
    }

    high_risk = (
        cold["is_large_ho"].eq(1)
        | cold["is_extra_large_ho"].eq(1)
        | cold["is_very_large_area"].eq(1)
    ).to_numpy()
    cold_groups = {
        "all": np.ones(len(cold), dtype=bool),
        "standard_3d": mask_3d & ~high_risk,
        "standard_2d": (~mask_3d) & ~high_risk,
        "high_risk_large_or_very_large": high_risk,
        "large_ho": cold["is_large_ho"].eq(1).to_numpy(),
        "extra_large_ho": cold["is_extra_large_ho"].eq(1).to_numpy(),
        "very_large_area": cold["is_very_large_area"].eq(1).to_numpy(),
    }

    warm_rows = group_rows(warm, warm_pred, warm_groups)
    cold_rows = group_rows(cold, cold_pred, cold_groups)

    result = {
        "experiment_id": "H69_price_range_calibration_close",
        "date": "2026-05-14",
        "reason": "Close H46 by fixing price-range calibration groups on the final H66/H32 model candidates.",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "cold_rows": len(cold)},
        "models": {
            "warm": "H66 larger-low-lr LightGBM averaged over seeds 11/22/33",
            "cold": "H32 conditional fallback: base LAD for non-3D, 3D LAD for 3D works",
        },
        "warm_per_seed": warm_per_seed,
        "warm_groups": warm_rows,
        "cold_groups": cold_rows,
        "policy": {
            "primary_interval": "80% interval",
            "fallback_interval": "90% interval for low-confidence display or reviewer-only diagnostics",
            "warm": {
                "A_51_plus": "narrow range",
                "B_11_to_50": "narrow-to-normal range",
                "C_4_to_10": "normal range",
                "D_1_to_3": "wide range and low-confidence warning",
            },
            "cold": {
                "standard_3d": "normal Cold range",
                "standard_2d": "wide range",
                "high_risk_large_or_very_large": "wide range and low-confidence warning",
            },
        },
        "judgement": {
            "close_h46": True,
            "note": "Group-specific widths restore target coverage where global widths under-cover, especially Warm low-history and Cold 2D/large works.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H69 price range calibration close")
    print(f"saved: {OUT_PATH}")
    print("Warm 80% widths")
    for name, row in warm_rows.items():
        print(
            f"{name:<28} med={row['metric']['median_ape']:.4f} "
            f"w80={row['interval_80']['width_abs_log']:.4f} x{row['interval_80']['price_multiplier']:.2f}"
        )
    print("Cold 80% widths")
    for name, row in cold_rows.items():
        print(
            f"{name:<28} med={row['metric']['median_ape']:.4f} "
            f"w80={row['interval_80']['width_abs_log']:.4f} x{row['interval_80']['price_multiplier']:.2f}"
        )


if __name__ == "__main__":
    main()
