"""Track 3 H48-H52 and H57-H60 pending follow-up experiments."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
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
from h61_h65_model_improvement_followups import build_linear, train_lgb_fixed
from h66_warm_lgbm_retune_multiseed import PARAMS as H66_PARAMS


OUT_PATH = REPO / "data" / "track3_h48_h60_pending_followups_results.json"
ARTIST_COL = "artist_name_ko"
SEED = 11


def simple_interval_coverage(y_true_ln: np.ndarray, y_pred_ln: np.ndarray, width: float) -> dict:
    covered = np.abs(y_pred_ln - y_true_ln) <= width
    return {"n": int(len(y_true_ln)), "width_abs_log": float(width), "coverage": float(np.mean(covered))}


def slice_metric(df: pd.DataFrame, pred: np.ndarray, mask: np.ndarray, min_n: int = 20) -> dict | None:
    if int(mask.sum()) < min_n:
        return None
    return metric(df.loc[mask, TARGET].values, pred[mask])


def add_extended_artist_history(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby(ARTIST_COL)[TARGET]
    stats = grouped.agg(["min", "max", "median"]).rename(
        columns={"min": "artist_ln_price_min", "max": "artist_ln_price_max", "median": "artist_ln_price_median_ext"}
    )
    stats["artist_ln_price_p25"] = grouped.quantile(0.25)
    stats["artist_ln_price_p75"] = grouped.quantile(0.75)
    stats["artist_ln_price_p90"] = grouped.quantile(0.90)
    global_p90 = float(train[TARGET].quantile(0.90))
    high_share = train.assign(_is_high=train[TARGET].ge(global_p90).astype(float)).groupby(ARTIST_COL)["_is_high"].mean()
    stats["artist_high_price_share"] = high_share
    stats["artist_price_range"] = stats["artist_ln_price_max"] - stats["artist_ln_price_min"]
    joined = out[[ARTIST_COL]].join(stats, on=ARTIST_COL)
    defaults = {
        "artist_ln_price_min": float(train[TARGET].min()),
        "artist_ln_price_max": float(train[TARGET].max()),
        "artist_ln_price_median_ext": float(train[TARGET].median()),
        "artist_ln_price_p25": float(train[TARGET].quantile(0.25)),
        "artist_ln_price_p75": float(train[TARGET].quantile(0.75)),
        "artist_ln_price_p90": float(train[TARGET].quantile(0.90)),
        "artist_high_price_share": 0.0,
        "artist_price_range": float(train[TARGET].max() - train[TARGET].min()),
    }
    for col, default in defaults.items():
        out[col] = joined[col].fillna(default)
    return out


def add_interactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["artist_median_x_log_area"] = out["artist_ln_price_median"].fillna(0) * out["log_area"].fillna(0)
    out["artist_median_x_log_ho"] = out["artist_ln_price_median"].fillna(0) * out["log_ho"].fillna(0)
    out["artist_works_x_log_area"] = out["artist_works_log"].fillna(0) * out["log_area"].fillna(0)
    out["artist_works_x_large_ho"] = out["artist_works_log"].fillna(0) * out["is_large_ho"].fillna(0)
    return out


def add_combo_features(train: pd.DataFrame, df: pd.DataFrame, min_count: int = 100) -> pd.DataFrame:
    out = df.copy()
    combo = out["medium_category"].fillna("unknown").astype(str) + "__" + out["support_category"].fillna("unknown").astype(str)
    train_combo = train["medium_category"].fillna("unknown").astype(str) + "__" + train["support_category"].fillna("unknown").astype(str)
    valid = set(train_combo.value_counts()[lambda s: s >= min_count].index)
    out["medium_support_combo_clean"] = combo.where(combo.isin(valid), "other_combo")
    return out


def main() -> None:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    warm = add_history(add_features(warm_raw), hist, global_values)
    cold = add_history(add_features(cold_raw), hist, global_values)

    # Current Warm candidate: H66 larger-low-lr.
    warm_model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, H66_PARAMS["larger_low_lr"], seed=SEED)
    warm_pred = warm_model.predict(to_cat(warm, WARM_H31_FEATURES, WARM_H31_CAT))

    # Current Cold candidate: H32 conditional fallback.
    cold_base = build_lad(COLD_BASE_FEATURES)
    cold_base.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    cold_base_pred = cold_base.predict(cold[COLD_BASE_FEATURES])
    cold_3d = build_lad(COLD_3D_FEATURES)
    cold_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    cold_3d_pred = cold_3d.predict(cold[COLD_3D_FEATURES])
    mask_3d = cold["is_3d_work"].eq(1).to_numpy()
    cold_h32_pred = cold_base_pred.copy()
    cold_h32_pred[mask_3d] = cold_3d_pred[mask_3d]

    # H48: narrower Cold high-risk definitions.
    cold_abs_log_err = np.abs(cold_h32_pred - cold[TARGET].values)
    high_risk_masks = {
        "3d_only": cold["is_3d_work"].eq(1).to_numpy(),
        "large_ho_only": cold["is_large_ho"].eq(1).to_numpy(),
        "extra_large_ho_only": cold["is_extra_large_ho"].eq(1).to_numpy(),
        "very_large_area_only": cold["is_very_large_area"].eq(1).to_numpy(),
        "3d_and_large_ho": (cold["is_3d_work"].eq(1) & cold["is_large_ho"].eq(1)).to_numpy(),
        "3d_and_very_large_area": (cold["is_3d_work"].eq(1) & cold["is_very_large_area"].eq(1)).to_numpy(),
    }
    h48 = {}
    for name, mask in high_risk_masks.items():
        if int(mask.sum()) < 20:
            continue
        low_mask = ~mask
        width_low = float(np.quantile(cold_abs_log_err[low_mask], 0.80))
        width_high = float(np.quantile(cold_abs_log_err[mask], 0.80))
        h48[name] = {
            "high_risk": slice_metric(cold, cold_h32_pred, mask),
            "low_risk": slice_metric(cold, cold_h32_pred, low_mask),
            "coverage_with_low_width": simple_interval_coverage(cold.loc[mask, TARGET].values, cold_h32_pred[mask], width_low),
            "coverage_with_high_width": simple_interval_coverage(cold.loc[mask, TARGET].values, cold_h32_pred[mask], width_high),
            "low_width": width_low,
            "high_width": width_high,
        }

    # H49: H45 mid-volume exception with tail metrics.
    cold_3d_df = cold.loc[mask_3d]
    q33, q66 = cold_3d_df["volume_log"].quantile([0.33, 0.66]).to_list()
    mask_3d_mid = (cold["is_3d_work"].eq(1) & cold["volume_log"].gt(q33) & cold["volume_log"].le(q66)).to_numpy()
    cold_mid_exception_pred = cold_h32_pred.copy()
    cold_mid_exception_pred[mask_3d_mid] = cold_base_pred[mask_3d_mid]
    h49 = {
        "h32_all": metric(cold[TARGET].values, cold_h32_pred),
        "mid_exception_all": metric(cold[TARGET].values, cold_mid_exception_pred),
        "h32_mid_3d": slice_metric(cold, cold_h32_pred, mask_3d_mid),
        "mid_exception_mid_3d": slice_metric(cold, cold_mid_exception_pred, mask_3d_mid),
    }

    # H50/H51: Warm confidence grades based on p90 and grade-specific intervals.
    grade_masks = {
        "A_51_plus": warm["artist_count"].ge(51).to_numpy(),
        "B_11_to_50": (warm["artist_count"].ge(11) & warm["artist_count"].le(50)).to_numpy(),
        "C_4_to_10": (warm["artist_count"].ge(4) & warm["artist_count"].le(10)).to_numpy(),
        "D_1_to_3": warm["artist_count"].le(3).to_numpy(),
    }
    warm_abs_log_err = np.abs(warm_pred - warm[TARGET].values)
    global_warm_width80 = float(np.quantile(warm_abs_log_err, 0.80))
    h50 = {}
    h51 = {}
    for grade, mask in grade_masks.items():
        h50[grade] = slice_metric(warm, warm_pred, mask, min_n=10)
        width80 = float(np.quantile(warm_abs_log_err[mask], 0.80))
        width90 = float(np.quantile(warm_abs_log_err[mask], 0.90))
        h51[grade] = {
            "global_width80_coverage": simple_interval_coverage(warm.loc[mask, TARGET].values, warm_pred[mask], global_warm_width80),
            "grade_width80_coverage": simple_interval_coverage(warm.loc[mask, TARGET].values, warm_pred[mask], width80),
            "grade_width90_coverage": simple_interval_coverage(warm.loc[mask, TARGET].values, warm_pred[mask], width90),
        }

    # H52: Cold intervals by condition.
    cold_slices = {
        "all": np.ones(len(cold), dtype=bool),
        "2d": ~mask_3d,
        "3d": mask_3d,
        "large_ho": cold["is_large_ho"].eq(1).to_numpy(),
        "extra_large_ho": cold["is_extra_large_ho"].eq(1).to_numpy(),
        "very_large_area": cold["is_very_large_area"].eq(1).to_numpy(),
    }
    global_cold_width80 = float(np.quantile(cold_abs_log_err, 0.80))
    h52 = {}
    for name, mask in cold_slices.items():
        width80 = float(np.quantile(cold_abs_log_err[mask], 0.80))
        width90 = float(np.quantile(cold_abs_log_err[mask], 0.90))
        h52[name] = {
            "metric": slice_metric(cold, cold_h32_pred, mask),
            "global_width80_coverage": simple_interval_coverage(cold.loc[mask, TARGET].values, cold_h32_pred[mask], global_cold_width80),
            "slice_width80_coverage": simple_interval_coverage(cold.loc[mask, TARGET].values, cold_h32_pred[mask], width80),
            "slice_width90_coverage": simple_interval_coverage(cold.loc[mask, TARGET].values, cold_h32_pred[mask], width90),
        }

    # H57/H58: Warm model feature extensions, single-seed screen.
    train_ext = add_interactions(add_extended_artist_history(train, train))
    warm_ext = add_interactions(add_extended_artist_history(train, warm))
    h57_features = [
        "artist_ln_price_min",
        "artist_ln_price_max",
        "artist_ln_price_p25",
        "artist_ln_price_p75",
        "artist_ln_price_p90",
        "artist_high_price_share",
        "artist_price_range",
    ]
    h58_features = [
        "artist_median_x_log_area",
        "artist_median_x_log_ho",
        "artist_works_x_log_area",
        "artist_works_x_large_ho",
    ]
    warm_variants = {
        "h66_base": (WARM_H31_FEATURES, WARM_H31_CAT, train, warm),
        "h57_extended_history": (WARM_H31_FEATURES + h57_features, WARM_H31_CAT, train_ext, warm_ext),
        "h58_interactions": (WARM_H31_FEATURES + h58_features, WARM_H31_CAT, train_ext, warm_ext),
        "h57_h58_combined": (WARM_H31_FEATURES + h57_features + h58_features, WARM_H31_CAT, train_ext, warm_ext),
    }
    h57_h58 = {}
    for name, (features, cats, tr, te) in warm_variants.items():
        model = train_lgb_fixed(tr, features, cats, H66_PARAMS["larger_low_lr"], seed=SEED)
        pred = model.predict(to_cat(te, features, cats))
        h57_h58[name] = {"features": features, "metric": metric(te[TARGET].values, pred), "best_iteration": int(model.best_iteration)}

    # H59: material-level scale correction on Cold H32 predictions.
    global_medium_median = train[TARGET].median()
    medium_median = train.groupby("medium_category")[TARGET].median()
    medium_shift = cold["medium_category"].map(medium_median).fillna(global_medium_median).to_numpy() - float(global_medium_median)
    h59 = {}
    for weight in [0.05, 0.10, 0.20]:
        pred = cold_h32_pred + weight * medium_shift
        h59[f"medium_shift_{weight:g}"] = metric(cold[TARGET].values, pred)
    h59["h32_base"] = metric(cold[TARGET].values, cold_h32_pred)

    # H60: cleaned medium/support combo for Cold base model.
    train_combo = add_combo_features(train, train)
    cold_combo = add_combo_features(train, cold)
    combo_features = COLD_BASE_FEATURES + ["medium_support_combo_clean"]
    combo_model = build_linear(combo_features, "quantile", alpha=0.0)
    combo_model.fit(train_combo[combo_features], train_combo[TARGET].values)
    combo_base_pred = combo_model.predict(cold_combo[combo_features])
    combo_h32_pred = combo_base_pred.copy()
    combo_h32_pred[mask_3d] = cold_3d_pred[mask_3d]
    h60 = {
        "h32_base": metric(cold[TARGET].values, cold_h32_pred),
        "combo_base_only": metric(cold[TARGET].values, combo_base_pred),
        "combo_base_plus_3d_fallback": metric(cold[TARGET].values, combo_h32_pred),
    }

    result = {
        "experiment_id": "H48_H60_pending_followups",
        "date": "2026-05-14",
        "data": {"train_rows": len(train), "warm_rows": len(warm), "cold_rows": len(cold)},
        "references": {
            "warm_h66_seed11": metric(warm[TARGET].values, warm_pred),
            "cold_h32": metric(cold[TARGET].values, cold_h32_pred),
        },
        "h48_cold_high_risk_redefinition": h48,
        "h49_cold_mid_volume_tail_check": h49,
        "h50_warm_confidence_p90_grades": h50,
        "h51_warm_grade_intervals": h51,
        "h52_cold_slice_intervals": h52,
        "h57_h58_warm_feature_extensions": h57_h58,
        "h59_cold_material_scale_correction": h59,
        "h60_cold_clean_combo": h60,
        "judgement": {
            "h48": "Prefer definitions where high-risk median/tail error is worse than low-risk and a separate width is justified.",
            "h49": "Adopt mid-volume exception only if median improvement does not create unacceptable p90/p95 deterioration.",
            "h50_h51": "Warm confidence grades should be based on both median APE and p90/p95 or grade interval width.",
            "h52": "Cold intervals should be split only if slice-specific widths are meaningfully different.",
            "h57_h58": "Adopt only if single-seed gains are large enough to justify multi-seed confirmation.",
            "h59_h60": "Adopt only if Cold H32 improves without worsening tail metrics materially.",
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("H48-H60 pending followups")
    print(f"saved: {OUT_PATH}")
    print("H57/H58 warm:", {k: round(v["metric"]["median_ape"], 4) for k, v in h57_h58.items()})
    print("H59 cold:", {k: round(v["median_ape"], 4) for k, v in h59.items()})
    print("H60 cold:", {k: round(v["median_ape"], 4) for k, v in h60.items()})
    print("H49 all:", round(h49["h32_all"]["median_ape"], 4), "->", round(h49["mid_exception_all"]["median_ape"], 4))


if __name__ == "__main__":
    main()
