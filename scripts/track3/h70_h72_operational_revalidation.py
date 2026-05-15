"""Track 3 H70-H72 operational revalidation.

Revalidates audit risks found on 2026-05-15:
- H70: price-range calibration using internal calibration splits, not test residuals.
- H71: Cold 3D mid-volume exception using train-derived thresholds, not cold-test quantiles.
- H72: H60 medium/support combo cleanup with a min_count grid.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
    ARTIST_COL,
    COLD_3D_FEATURES,
    COLD_BASE_FEATURES,
    REPO,
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
from h48_h60_pending_followups import add_combo_features
from h61_h65_model_improvement_followups import build_linear, train_lgb_fixed
from h66_warm_lgbm_retune_multiseed import PARAMS as H66_PARAMS


OUT_PATH = REPO / "data" / "track3_h70_h72_operational_revalidation_results.json"
SEED = 20260515
WARM_SEEDS = [11, 22, 33]


def split_warm_calibration(train_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hold out one row from artists with at least 2 train rows."""
    rng = np.random.default_rng(SEED)
    cal_indices: list[int] = []
    for _, group in train_raw.groupby(ARTIST_COL):
        if len(group) >= 2:
            cal_indices.append(int(rng.choice(group.index.to_numpy())))
    cal_idx = pd.Index(cal_indices)
    core = train_raw.drop(index=cal_idx).reset_index(drop=True)
    cal = train_raw.loc[cal_idx].reset_index(drop=True)
    return core, cal


def split_cold_calibration(train_raw: pd.DataFrame, n_artists: int = 200) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hold out full artists from train to simulate an internal Cold calibration set."""
    rng = np.random.default_rng(SEED)
    artist_counts = train_raw[ARTIST_COL].value_counts()
    eligible = artist_counts[artist_counts >= 3].index.to_numpy()
    selected = rng.choice(eligible, size=min(n_artists, len(eligible)), replace=False)
    mask = train_raw[ARTIST_COL].isin(selected)
    core = train_raw.loc[~mask].reset_index(drop=True)
    cal = train_raw.loc[mask].reset_index(drop=True)
    return core, cal


def prepare(train_raw: pd.DataFrame, *frames: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    prepared = [add_history(add_features(frame), hist, global_values) for frame in frames]
    return train, prepared


def warm_predict(train: pd.DataFrame, test: pd.DataFrame, seeds: list[int] = WARM_SEEDS) -> np.ndarray:
    preds = []
    for seed in seeds:
        model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, H66_PARAMS["larger_low_lr"], seed=seed)
        preds.append(model.predict(to_cat(test, WARM_H31_FEATURES, WARM_H31_CAT)))
    return np.mean(preds, axis=0)


def cold_h32_predict(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = build_lad(COLD_BASE_FEATURES)
    base.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    base_pred = base.predict(test[COLD_BASE_FEATURES])

    model_3d = build_lad(COLD_3D_FEATURES)
    model_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    pred_3d = model_3d.predict(test[COLD_3D_FEATURES])

    mask_3d = test["is_3d_work"].eq(1).to_numpy()
    pred = base_pred.copy()
    pred[mask_3d] = pred_3d[mask_3d]
    return pred, base_pred, pred_3d


def width_from_calibration(df: pd.DataFrame, pred: np.ndarray, groups: dict[str, np.ndarray], q: float = 0.80) -> dict:
    err = np.abs(pred - df[TARGET].values)
    widths: dict[str, dict] = {}
    for name, mask in groups.items():
        n = int(mask.sum())
        if n < 20:
            continue
        width = float(np.quantile(err[mask], q))
        widths[name] = {"n": n, "width_abs_log": width, "price_multiplier": float(np.exp(width))}
    return widths


def apply_widths(df: pd.DataFrame, pred: np.ndarray, groups: dict[str, np.ndarray], widths: dict) -> dict:
    err = np.abs(pred - df[TARGET].values)
    out = {}
    for name, mask in groups.items():
        if name not in widths or int(mask.sum()) < 20:
            continue
        width = widths[name]["width_abs_log"]
        out[name] = {
            "n": int(mask.sum()),
            "metric": metric(df.loc[mask, TARGET].values, pred[mask]),
            "cal_width_abs_log": width,
            "cal_price_multiplier": widths[name]["price_multiplier"],
            "coverage": float(np.mean(err[mask] <= width)),
        }
    return out


def warm_groups(df: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "all": np.ones(len(df), dtype=bool),
        "A_51_plus": df["artist_count"].ge(51).to_numpy(),
        "B_11_to_50": (df["artist_count"].ge(11) & df["artist_count"].le(50)).to_numpy(),
        "C_4_to_10": (df["artist_count"].ge(4) & df["artist_count"].le(10)).to_numpy(),
        "D_1_to_3": df["artist_count"].le(3).to_numpy(),
    }


def cold_groups(df: pd.DataFrame) -> dict[str, np.ndarray]:
    mask_3d = df["is_3d_work"].eq(1).to_numpy()
    high_risk = (
        df["is_large_ho"].eq(1)
        | df["is_extra_large_ho"].eq(1)
        | df["is_very_large_area"].eq(1)
    ).to_numpy()
    return {
        "all": np.ones(len(df), dtype=bool),
        "standard_3d": mask_3d & ~high_risk,
        "standard_2d": (~mask_3d) & ~high_risk,
        "high_risk_large_or_very_large": high_risk,
        "large_ho": df["is_large_ho"].eq(1).to_numpy(),
        "extra_large_ho": df["is_extra_large_ho"].eq(1).to_numpy(),
        "very_large_area": df["is_very_large_area"].eq(1).to_numpy(),
    }


def revalidate_calibration(train_raw: pd.DataFrame, warm_raw: pd.DataFrame, cold_raw: pd.DataFrame) -> dict:
    warm_core_raw, warm_cal_raw = split_warm_calibration(train_raw)
    warm_core, [warm_cal] = prepare(warm_core_raw, warm_cal_raw)
    warm_cal_pred = warm_predict(warm_core, warm_cal, seeds=[11])
    warm_widths = width_from_calibration(warm_cal, warm_cal_pred, warm_groups(warm_cal), q=0.80)

    cold_core_raw, cold_cal_raw = split_cold_calibration(train_raw)
    cold_core, [cold_cal] = prepare(cold_core_raw, cold_cal_raw)
    cold_cal_pred, _, _ = cold_h32_predict(cold_core, cold_cal)
    cold_widths = width_from_calibration(cold_cal, cold_cal_pred, cold_groups(cold_cal), q=0.80)

    full_train, [warm, cold] = prepare(train_raw, warm_raw, cold_raw)
    warm_pred = warm_predict(full_train, warm)
    cold_pred, _, _ = cold_h32_predict(full_train, cold)

    return {
        "warm_calibration": {
            "core_rows": len(warm_core),
            "calibration_rows": len(warm_cal),
            "widths_from_internal_calibration": warm_widths,
            "test_coverage_with_calibration_widths": apply_widths(warm, warm_pred, warm_groups(warm), warm_widths),
        },
        "cold_calibration": {
            "core_rows": len(cold_core),
            "calibration_rows": len(cold_cal),
            "calibration_artists": int(cold_cal[ARTIST_COL].nunique()),
            "widths_from_internal_cold_artist_holdout": cold_widths,
            "test_coverage_with_calibration_widths": apply_widths(cold, cold_pred, cold_groups(cold), cold_widths),
        },
    }


def revalidate_mid_volume(train_raw: pd.DataFrame, cold_raw: pd.DataFrame) -> dict:
    train, [cold] = prepare(train_raw, cold_raw)
    h32_pred, base_pred, _ = cold_h32_predict(train, cold)

    train_3d = train.loc[train["is_3d_work"].eq(1)]
    q33, q66 = train_3d["volume_log"].quantile([0.33, 0.66]).to_list()
    mask_mid = (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(q33) & cold["volume_log"].le(q66)).to_numpy()
    pred_mid_exception = h32_pred.copy()
    pred_mid_exception[mask_mid] = base_pred[mask_mid]

    return {
        "threshold_source": "train_3d_volume_log_q33_q66",
        "q33": float(q33),
        "q66": float(q66),
        "mid_3d_n": int(mask_mid.sum()),
        "h32_all": metric(cold[TARGET].values, h32_pred),
        "train_threshold_mid_exception_all": metric(cold[TARGET].values, pred_mid_exception),
        "h32_mid_3d": metric(cold.loc[mask_mid, TARGET].values, h32_pred[mask_mid]) if int(mask_mid.sum()) else None,
        "train_threshold_mid_exception_mid_3d": metric(cold.loc[mask_mid, TARGET].values, pred_mid_exception[mask_mid]) if int(mask_mid.sum()) else None,
    }


def revalidate_combo_grid(train_raw: pd.DataFrame, cold_raw: pd.DataFrame) -> dict:
    train, [cold] = prepare(train_raw, cold_raw)
    h32_pred, _, cold_3d_pred = cold_h32_predict(train, cold)
    mask_3d = cold["is_3d_work"].eq(1).to_numpy()
    out = {"h32_base": metric(cold[TARGET].values, h32_pred), "grid": {}}
    for min_count in [20, 50, 100, 200, 500]:
        train_combo = add_combo_features(train, train, min_count=min_count)
        cold_combo = add_combo_features(train, cold, min_count=min_count)
        combo_features = COLD_BASE_FEATURES + ["medium_support_combo_clean"]
        model = build_linear(combo_features, "quantile", alpha=0.0)
        model.fit(train_combo[combo_features], train_combo[TARGET].values)
        combo_base_pred = model.predict(cold_combo[combo_features])
        combo_h32_pred = combo_base_pred.copy()
        combo_h32_pred[mask_3d] = cold_3d_pred[mask_3d]
        out["grid"][f"min_count_{min_count}"] = {
            "unique_train_combos": int(train_combo["medium_support_combo_clean"].nunique()),
            "combo_base_only": metric(cold[TARGET].values, combo_base_pred),
            "combo_base_plus_3d_fallback": metric(cold[TARGET].values, combo_h32_pred),
        }
    return out


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")

    h70 = revalidate_calibration(train_raw, warm_raw, cold_raw)
    h71 = revalidate_mid_volume(train_raw, cold_raw)
    h72 = revalidate_combo_grid(train_raw, cold_raw)

    result = {
        "experiment_id": "H70_H72_operational_revalidation",
        "date": "2026-05-15",
        "data": {
            "train_rows": int(len(train_raw)),
            "warm_rows": int(len(warm_raw)),
            "cold_rows": int(len(cold_raw)),
        },
        "h70_internal_calibration_split": h70,
        "h71_train_threshold_cold_3d_mid_volume": h71,
        "h72_h60_combo_min_count_grid": h72,
        "judgement": {
            "h70": "Adopt calibration only if internal-calibration widths reach acceptable test coverage without excessive width.",
            "h71": "Adopt mid-volume exception only if train-derived thresholds improve all-Cold and do not worsen p95 materially.",
            "h72": "Adopt combo cleanup only if at least one min_count improves H32 median APE without tail deterioration.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H70-H72 operational revalidation")
    print(f"saved: {OUT_PATH}")
    print("H70 warm coverage:", {k: round(v["coverage"], 3) for k, v in h70["warm_calibration"]["test_coverage_with_calibration_widths"].items()})
    print("H70 cold coverage:", {k: round(v["coverage"], 3) for k, v in h70["cold_calibration"]["test_coverage_with_calibration_widths"].items()})
    print(
        "H71 median:",
        round(h71["h32_all"]["median_ape"], 4),
        "->",
        round(h71["train_threshold_mid_exception_all"]["median_ape"], 4),
    )
    print(
        "H72 grid:",
        {
            k: round(v["combo_base_plus_3d_fallback"]["median_ape"], 4)
            for k, v in h72["grid"].items()
        },
    )


if __name__ == "__main__":
    main()
