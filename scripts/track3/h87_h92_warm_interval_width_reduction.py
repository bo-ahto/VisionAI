"""Track 3 H87-H92 Warm interval-width reduction.

Tests whether Warm price-range width can be reduced with operationally
definable calibration groups or tail shrink policies.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from h34_h43_followup_validation import (
    ARTIST_COL,
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
from h61_h65_model_improvement_followups import train_lgb_fixed
from h66_warm_lgbm_retune_multiseed import PARAMS as H66_PARAMS
from h70_h72_operational_revalidation import split_warm_calibration


OUT_PATH = REPO / "data" / "track3_h87_h92_warm_interval_width_reduction_results.json"
DATE = "2026-05-15"


def prepare(train_raw: pd.DataFrame, *frames: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    prepared = [add_history(add_features(frame), hist, global_values) for frame in frames]
    return train, prepared


def warm_predict(train: pd.DataFrame, test: pd.DataFrame, seeds: list[int]) -> np.ndarray:
    preds = []
    for seed in seeds:
        model = train_lgb_fixed(train, WARM_H31_FEATURES, WARM_H31_CAT, H66_PARAMS["larger_low_lr"], seed=seed)
        preds.append(model.predict(to_cat(test, WARM_H31_FEATURES, WARM_H31_CAT)))
    return np.mean(preds, axis=0)


def abs_log_error(df: pd.DataFrame, pred: np.ndarray) -> np.ndarray:
    return np.abs(pred - df[TARGET].values)


def price_multiplier(width_abs_log: float) -> float:
    return float(np.exp(width_abs_log))


def tail_metric(df: pd.DataFrame, pred: np.ndarray) -> dict:
    row = metric(df[TARGET].values, pred)
    abs_log = abs_log_error(df, pred)
    row["q80_price_multiplier"] = price_multiplier(float(np.quantile(abs_log, 0.80)))
    row["q90_price_multiplier"] = price_multiplier(float(np.quantile(abs_log, 0.90)))
    row["p80_abs_log_error"] = float(np.quantile(abs_log, 0.80))
    return row


def count_grade(df: pd.DataFrame) -> pd.Series:
    return pd.cut(
        df["artist_count"],
        bins=[-0.1, 3, 10, 50, 100000],
        labels=["D_1_to_3", "C_4_to_10", "B_11_to_50", "A_51_plus"],
    ).astype(str)


def thresholds(train: pd.DataFrame, pred_cal: np.ndarray) -> dict[str, float]:
    return {
        "log_area_q90": float(train["log_area"].quantile(0.90)),
        "estimated_ho_q90": float(train["estimated_ho"].quantile(0.90)),
        "pred_ln_q20": float(np.quantile(pred_cal, 0.20)),
        "pred_ln_q80": float(np.quantile(pred_cal, 0.80)),
        "global_target_median": float(train[TARGET].median()),
    }


def warm_groups(df: pd.DataFrame, pred: np.ndarray, t: dict[str, float]) -> dict[str, np.ndarray]:
    grade = count_grade(df)
    large = (
        df["is_large_ho"].eq(1)
        | df["is_extra_large_ho"].eq(1)
        | df["is_very_large_area"].eq(1)
        | df["log_area"].ge(t["log_area_q90"])
        | df["estimated_ho"].ge(t["estimated_ho_q90"])
    ).to_numpy()
    pred_mid = (pred > t["pred_ln_q20"]) & (pred < t["pred_ln_q80"])
    low_risk = grade.isin(["A_51_plus", "B_11_to_50"]).to_numpy() & (~large) & pred_mid
    high_risk = grade.eq("D_1_to_3").to_numpy() | large | (~pred_mid)
    return {
        "all": np.ones(len(df), dtype=bool),
        "A_51_plus": grade.eq("A_51_plus").to_numpy(),
        "B_11_to_50": grade.eq("B_11_to_50").to_numpy(),
        "C_4_to_10": grade.eq("C_4_to_10").to_numpy(),
        "D_1_to_3": grade.eq("D_1_to_3").to_numpy(),
        "not_large": ~large,
        "large_or_extreme": large,
        "pred_mid_60": pred_mid,
        "pred_low_or_high": ~pred_mid,
        "combined_low_risk": low_risk,
        "combined_high_risk": high_risk,
    }


def width_from_calibration(df: pd.DataFrame, pred: np.ndarray, groups: dict[str, np.ndarray], q: float = 0.80) -> dict[str, dict]:
    err = abs_log_error(df, pred)
    out = {}
    for name, mask in groups.items():
        if int(mask.sum()) < 20:
            continue
        width = float(np.quantile(err[mask], q))
        out[name] = {
            "n": int(mask.sum()),
            "width_abs_log": width,
            "price_multiplier": price_multiplier(width),
        }
    return out


def apply_widths(df: pd.DataFrame, pred: np.ndarray, groups: dict[str, np.ndarray], widths: dict[str, dict]) -> dict[str, dict]:
    err = abs_log_error(df, pred)
    out = {}
    for name, mask in groups.items():
        if name not in widths or int(mask.sum()) < 20:
            continue
        width = widths[name]["width_abs_log"]
        row = tail_metric(df.loc[mask], pred[mask])
        out[name] = {
            "n": int(mask.sum()),
            "share": float(mask.sum() / len(df)),
            "metric": row,
            "cal_width_abs_log": width,
            "cal_price_multiplier": widths[name]["price_multiplier"],
            "test_coverage_with_cal_width": float(np.mean(err[mask] <= width)),
        }
    return out


def group_medians(train: pd.DataFrame) -> dict[str, dict[str, float]]:
    train = train.copy()
    train["artist_grade"] = count_grade(train)
    return {
        "artist_grade": train.groupby("artist_grade")[TARGET].median().to_dict(),
        "medium_category": train.groupby("medium_category")[TARGET].median().to_dict(),
    }


def group_target(df: pd.DataFrame, medians: dict[str, dict[str, float]], group_col: str, fallback: float) -> np.ndarray:
    if group_col == "artist_grade":
        keys = count_grade(df)
    else:
        keys = df[group_col]
    return keys.map(medians[group_col]).fillna(fallback).to_numpy()


def shrink_policy(df: pd.DataFrame, pred: np.ndarray, mask: np.ndarray, target: np.ndarray, weight: float) -> np.ndarray:
    out = pred.copy()
    out[mask] = (1.0 - weight) * out[mask] + weight * target[mask]
    return out


def select_shrink(cal: pd.DataFrame, cal_pred: np.ndarray, t: dict[str, float], medians: dict[str, dict[str, float]]) -> list[dict]:
    groups = warm_groups(cal, cal_pred, t)
    masks = {
        "D_1_to_3": groups["D_1_to_3"],
        "combined_high_risk": groups["combined_high_risk"],
        "large_or_extreme": groups["large_or_extreme"],
    }
    base = tail_metric(cal, cal_pred)
    rows = []
    for mask_name, mask in masks.items():
        if int(mask.sum()) < 20:
            continue
        for group_col in ["artist_grade", "medium_category"]:
            target = group_target(cal, medians, group_col, t["global_target_median"])
            for weight in [0.10, 0.20, 0.30, 0.40]:
                pred = shrink_policy(cal, cal_pred, mask, target, weight)
                row = tail_metric(cal, pred)
                rows.append(
                    {
                        "policy": {
                            "name": f"shrink_{mask_name}_{group_col}_w{weight:.2f}",
                            "mask": mask_name,
                            "group_col": group_col,
                            "weight": weight,
                        },
                        "cal_metric": row,
                        "delta_p80_x": row["q80_price_multiplier"] - base["q80_price_multiplier"],
                        "delta_median": row["median_ape"] - base["median_ape"],
                        "delta_p95": row["p95_ape"] - base["p95_ape"],
                    }
                )
    eligible = [
        row
        for row in rows
        if row["delta_p80_x"] < 0
        and row["delta_median"] <= 0.015
        and row["delta_p95"] <= 0.03
    ]
    if not eligible:
        eligible = [row for row in rows if row["delta_p80_x"] < 0 and row["delta_median"] <= 0.03]
    return sorted(eligible, key=lambda row: (row["cal_metric"]["q80_price_multiplier"], row["cal_metric"]["median_ape"]))[:10]


def apply_selected_policy(df: pd.DataFrame, pred: np.ndarray, policy: dict, t: dict[str, float], medians: dict[str, dict[str, float]]) -> np.ndarray:
    groups = warm_groups(df, pred, t)
    mask = groups[policy["mask"]]
    target = group_target(df, medians, policy["group_col"], t["global_target_median"])
    return shrink_policy(df, pred, mask, target, policy["weight"])


def run() -> dict:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    warm_raw = pd.read_csv(SPLIT / "track3_test_warm.csv")

    core_raw, cal_raw = split_warm_calibration(train_raw)
    core, [cal] = prepare(core_raw, cal_raw)
    cal_pred = warm_predict(core, cal, seeds=[11])
    t_cal = thresholds(core, cal_pred)
    med_cal = group_medians(core)

    cal_groups = warm_groups(cal, cal_pred, t_cal)
    cal_widths = width_from_calibration(cal, cal_pred, cal_groups, q=0.80)
    selected = select_shrink(cal, cal_pred, t_cal, med_cal)

    full_train, [warm] = prepare(train_raw, warm_raw)
    warm_pred = warm_predict(full_train, warm, seeds=SEEDS)
    t_test = thresholds(full_train, cal_pred)
    med_test = group_medians(full_train)
    test_groups = warm_groups(warm, warm_pred, t_test)
    group_width_results = apply_widths(warm, warm_pred, test_groups, cal_widths)
    base_metric = tail_metric(warm, warm_pred)

    shrink_results = []
    for item in selected:
        policy = item["policy"]
        pred = apply_selected_policy(warm, warm_pred, policy, t_test, med_test)
        row = tail_metric(warm, pred)
        shrink_results.append(
            {
                "policy": policy,
                "cal_metric": item["cal_metric"],
                "test_metric": row,
                "test_delta": {
                    "median_ape": row["median_ape"] - base_metric["median_ape"],
                    "p95_ape": row["p95_ape"] - base_metric["p95_ape"],
                    "q80_price_multiplier": row["q80_price_multiplier"] - base_metric["q80_price_multiplier"],
                    "within_30pct": row["within_30pct"] - base_metric["within_30pct"],
                },
            }
        )

    return {
        "experiment_id": "H87_H92_warm_interval_width_reduction",
        "date": DATE,
        "data": {
            "train_rows": int(len(train_raw)),
            "warm_rows": int(len(warm_raw)),
            "internal_warm_calibration_rows": int(len(cal)),
        },
        "model_policy": "H66 Warm larger-low-lr LightGBM, 3-seed average on release test",
        "baseline_test_metric": base_metric,
        "group_interval_results": group_width_results,
        "selected_shrink_test_results": shrink_results,
        "judgement": {
            "h87": "Artist-history grades are useful only if high-history groups keep coverage with narrower widths.",
            "h88": "Low-risk Warm subset is useful if q80 multiplier is materially lower than all Warm and keeps coverage >=0.75.",
            "h89": "High-risk Warm warnings remain necessary if D/large/extreme groups need wide intervals.",
            "h90": "Shrink policy is useful only if q80 multiplier decreases without hurting median APE materially.",
            "h91": "If group-specific intervals reduce low-risk width but not all-Warm width, use display policy rather than model replacement.",
            "h92": "Adopt only after separate holdout/CV because release test has already been used repeatedly.",
        },
    }


def main() -> None:
    result = run()
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    base = result["baseline_test_metric"]
    print("H87-H92 Warm interval width reduction")
    print(f"saved: {OUT_PATH}")
    print("baseline:", {
        "median": round(base["median_ape"], 4),
        "p95": round(base["p95_ape"], 4),
        "q80_x": round(base["q80_price_multiplier"], 3),
        "q90_x": round(base["q90_price_multiplier"], 3),
    })
    print("group intervals:")
    for name, row in result["group_interval_results"].items():
        print(
            name,
            "n=", row["n"],
            "share=", round(row["share"], 3),
            "cal_x=", round(row["cal_price_multiplier"], 3),
            "cov=", round(row["test_coverage_with_cal_width"], 3),
            "med=", round(row["metric"]["median_ape"], 4),
        )
    print("shrink candidates:")
    for row in result["selected_shrink_test_results"][:5]:
        m = row["test_metric"]
        d = row["test_delta"]
        print(
            row["policy"]["name"],
            "median=", round(m["median_ape"], 4),
            "p95=", round(m["p95_ape"], 4),
            "q80_x=", round(m["q80_price_multiplier"], 3),
            "delta_q80_x=", round(d["q80_price_multiplier"], 4),
            "delta_median=", round(d["median_ape"], 4),
        )


if __name__ == "__main__":
    main()
