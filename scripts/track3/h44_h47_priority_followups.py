"""Track 3 H44-H47 priority follow-up experiments."""
from __future__ import annotations

import json
from pathlib import Path

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
    ape_values,
    average_predictions,
    build_artist_history,
    build_lad,
    metric,
)


OUT_PATH = REPO / "data" / "track3_h44_h47_priority_followups_results.json"


def slice_metric(df: pd.DataFrame, pred: np.ndarray, mask: np.ndarray, min_n: int = 10) -> dict | None:
    if int(mask.sum()) < min_n:
        return None
    return metric(df.loc[mask, TARGET].values, pred[mask])


def simple_interval_coverage(y_true_ln: np.ndarray, y_pred_ln: np.ndarray, width: float) -> dict:
    covered = np.abs(y_pred_ln - y_true_ln) <= width
    return {
        "n": int(len(y_true_ln)),
        "width_abs_log": float(width),
        "coverage": float(np.mean(covered)),
    }


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)
    cold = add_history(add_features(cold_raw), hist, global_values)

    warm_pred, warm_per_seed = average_predictions(train, warm, WARM_H31_FEATURES, WARM_H31_CAT, SEEDS)

    cold_base_model = build_lad(COLD_BASE_FEATURES)
    cold_base_model.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_base_pred = cold_base_model.predict(cold[COLD_BASE_FEATURES])

    cold_3d_model = build_lad(COLD_3D_FEATURES)
    cold_3d_model.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    cold_3d_pred = cold_3d_model.predict(cold[COLD_3D_FEATURES])

    mask_3d = cold["is_3d_work"].astype(bool).to_numpy()
    cold_h32_pred = cold_base_pred.copy()
    cold_h32_pred[mask_3d] = cold_3d_pred[mask_3d]

    # H44: low-history Warm fallback.
    # Compare H31 Warm with a structure-only LightGBM fallback that does not use artist identity/history.
    structure_features = [f for f in WARM_H31_FEATURES if not f.startswith("artist_") and f != "artist_name_ko"]
    structure_cat = [c for c in WARM_H31_CAT if c in structure_features]
    warm_structure_pred, _ = average_predictions(train, warm, structure_features, structure_cat, [11])
    low_history_masks = {
        "artist_count_1": warm["artist_count"].eq(1).to_numpy(),
        "artist_count_1_to_3": warm["artist_count"].le(3).to_numpy(),
        "artist_count_4_plus": warm["artist_count"].ge(4).to_numpy(),
    }
    h44 = {
        "h31_warm": {name: slice_metric(warm, warm_pred, mask) for name, mask in low_history_masks.items()},
        "structure_only_fallback": {name: slice_metric(warm, warm_structure_pred, mask) for name, mask in low_history_masks.items()},
    }
    h44["delta_structure_minus_h31"] = {
        name: h44["structure_only_fallback"][name]["median_ape"] - h44["h31_warm"][name]["median_ape"]
        for name in low_history_masks
        if h44["h31_warm"][name] and h44["structure_only_fallback"][name]
    }

    # H45: Cold 3D mid-volume exception.
    cold_3d = cold.loc[mask_3d]
    q33, q66 = cold_3d["volume_log"].quantile([0.33, 0.66]).to_list()
    mask_3d_low = (cold["is_3d_work"].eq(1) & cold["volume_log"].le(q33)).to_numpy()
    mask_3d_mid = (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(q33) & cold["volume_log"].le(q66)).to_numpy()
    mask_3d_high = (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(q66)).to_numpy()
    cold_no_mid_fallback_pred = cold_h32_pred.copy()
    cold_no_mid_fallback_pred[mask_3d_mid] = cold_base_pred[mask_3d_mid]
    h45_masks = {"3d_low": mask_3d_low, "3d_mid": mask_3d_mid, "3d_high": mask_3d_high, "all_cold": np.ones(len(cold), dtype=bool)}
    h45 = {
        "h32_fallback": {name: slice_metric(cold, cold_h32_pred, mask) for name, mask in h45_masks.items()},
        "mid_volume_base_exception": {name: slice_metric(cold, cold_no_mid_fallback_pred, mask) for name, mask in h45_masks.items()},
    }
    h45["delta_exception_minus_h32"] = {
        name: h45["mid_volume_base_exception"][name]["median_ape"] - h45["h32_fallback"][name]["median_ape"]
        for name in h45_masks
        if h45["h32_fallback"][name] and h45["mid_volume_base_exception"][name]
    }

    # H46: wider ranges for high-risk works.
    warm_ape = ape_values(warm[TARGET].values, warm_pred)
    cold_ape = ape_values(cold[TARGET].values, cold_h32_pred)
    warm_high_risk = (warm["artist_count"].le(3) | warm["is_3d_work"].eq(1) | warm["is_extra_large_ho"].eq(1)).to_numpy()
    cold_high_risk = (cold["is_3d_work"].eq(1) | cold["is_large_ho"].eq(1) | cold["is_very_large_area"].eq(1)).to_numpy()
    warm_low_risk = ~warm_high_risk
    cold_low_risk = ~cold_high_risk
    warm_width_low = float(np.quantile(np.abs(warm_pred[warm_low_risk] - warm.loc[warm_low_risk, TARGET].values), 0.80))
    warm_width_high = float(np.quantile(np.abs(warm_pred[warm_high_risk] - warm.loc[warm_high_risk, TARGET].values), 0.80))
    cold_width_low = float(np.quantile(np.abs(cold_h32_pred[cold_low_risk] - cold.loc[cold_low_risk, TARGET].values), 0.80))
    cold_width_high = float(np.quantile(np.abs(cold_h32_pred[cold_high_risk] - cold.loc[cold_high_risk, TARGET].values), 0.80))
    h46 = {
        "warm": {
            "high_risk_n": int(warm_high_risk.sum()),
            "low_risk_n": int(warm_low_risk.sum()),
            "same_low_risk_width_on_high_risk": simple_interval_coverage(warm.loc[warm_high_risk, TARGET].values, warm_pred[warm_high_risk], warm_width_low),
            "separate_high_risk_width": simple_interval_coverage(warm.loc[warm_high_risk, TARGET].values, warm_pred[warm_high_risk], warm_width_high),
            "low_risk_width": warm_width_low,
            "high_risk_width": warm_width_high,
            "high_risk_median_ape": float(np.median(warm_ape[warm_high_risk])),
            "low_risk_median_ape": float(np.median(warm_ape[warm_low_risk])),
        },
        "cold": {
            "high_risk_n": int(cold_high_risk.sum()),
            "low_risk_n": int(cold_low_risk.sum()),
            "same_low_risk_width_on_high_risk": simple_interval_coverage(cold.loc[cold_high_risk, TARGET].values, cold_h32_pred[cold_high_risk], cold_width_low),
            "separate_high_risk_width": simple_interval_coverage(cold.loc[cold_high_risk, TARGET].values, cold_h32_pred[cold_high_risk], cold_width_high),
            "low_risk_width": cold_width_low,
            "high_risk_width": cold_width_high,
            "high_risk_median_ape": float(np.median(cold_ape[cold_high_risk])),
            "low_risk_median_ape": float(np.median(cold_ape[cold_low_risk])),
        },
    }

    # H47: confidence grade from artist_works_log.
    h47_bins = {
        "A_high_history_51_plus": warm["artist_count"].ge(51).to_numpy(),
        "B_mid_history_11_to_50": (warm["artist_count"].ge(11) & warm["artist_count"].le(50)).to_numpy(),
        "C_low_history_4_to_10": (warm["artist_count"].ge(4) & warm["artist_count"].le(10)).to_numpy(),
        "D_very_low_history_1_to_3": warm["artist_count"].le(3).to_numpy(),
    }
    h47 = {
        grade: {
            **slice_metric(warm, warm_pred, mask),
            "artist_count_min": int(warm.loc[mask, "artist_count"].min()),
            "artist_count_max": int(warm.loc[mask, "artist_count"].max()),
        }
        for grade, mask in h47_bins.items()
        if slice_metric(warm, warm_pred, mask)
    }

    result = {
        "experiment_id": "H44_H47_priority_followups",
        "date": "2026-05-14",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "cold_rows": len(cold)},
        "h44_warm_low_history_fallback": h44,
        "h45_cold_3d_mid_volume_exception": h45,
        "h46_high_risk_interval_width": h46,
        "h47_artist_history_confidence_grade": h47,
        "judgement": {
            "h44": "Use H31 for low-history Warm unless structure-only fallback clearly improves low-history slices.",
            "h45": "Adopt mid-volume exception only if all Cold and 3D-mid both improve.",
            "h46": "High-risk works need wider intervals if separate high-risk width improves coverage materially.",
            "h47": "Artist-count based confidence grading is usable if error increases monotonically as history decreases.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H44-H47 priority followups")
    print(f"saved: {OUT_PATH}")
    print("H44 deltas:", {k: round(v, 4) for k, v in h44["delta_structure_minus_h31"].items()})
    print("H45 deltas:", {k: round(v, 4) for k, v in h45["delta_exception_minus_h32"].items()})
    print("H46 warm coverage:", h46["warm"]["same_low_risk_width_on_high_risk"]["coverage"], "->", h46["warm"]["separate_high_risk_width"]["coverage"])
    print("H46 cold coverage:", h46["cold"]["same_low_risk_width_on_high_risk"]["coverage"], "->", h46["cold"]["separate_high_risk_width"]["coverage"])
    print("H47 medians:", {k: round(v["median_ape"], 4) for k, v in h47.items()})


if __name__ == "__main__":
    main()
