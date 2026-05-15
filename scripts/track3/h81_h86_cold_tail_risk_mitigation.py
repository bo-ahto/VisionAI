"""Track 3 H81-H86 Cold tail-risk mitigation.

Tests whether post-processing policies can reduce Cold p95/tail error.
Policy selection uses an internal Cold calibration split only; release Cold
test is used for final verification.
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
    add_features,
    add_history,
    build_artist_history,
    build_lad,
    metric,
)
from h70_h72_operational_revalidation import split_cold_calibration


OUT_PATH = REPO / "data" / "track3_h81_h86_cold_tail_risk_mitigation_results.json"
DATE = "2026-05-15"


def prepare(train_raw: pd.DataFrame, *frames: pd.DataFrame) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    hist, global_values = build_artist_history(train_raw)
    train = add_history(add_features(train_raw), hist, global_values)
    prepared = [add_history(add_features(frame), hist, global_values) for frame in frames]
    return train, prepared


def cold_h32_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    base = build_lad(COLD_BASE_FEATURES)
    base.fit(train[COLD_BASE_FEATURES], train[TARGET].values)
    base_pred = base.predict(test[COLD_BASE_FEATURES])

    model_3d = build_lad(COLD_3D_FEATURES)
    model_3d.fit(train[COLD_3D_FEATURES], train[TARGET].values)
    pred_3d = model_3d.predict(test[COLD_3D_FEATURES])

    mask_3d = test["is_3d_work"].eq(1).to_numpy()
    pred = base_pred.copy()
    pred[mask_3d] = pred_3d[mask_3d]
    return pred


def ape_values(y_true_ln: np.ndarray, y_pred_ln: np.ndarray) -> np.ndarray:
    return np.abs(np.exp(y_pred_ln) - np.exp(y_true_ln)) / np.exp(y_true_ln)


def tail_metric(df: pd.DataFrame, pred: np.ndarray) -> dict:
    row = metric(df[TARGET].values, pred)
    ape = ape_values(df[TARGET].values, pred)
    abs_log = np.abs(pred - df[TARGET].values)
    row["p80_ape"] = float(np.quantile(ape, 0.80))
    row["p99_ape"] = float(np.quantile(ape, 0.99))
    row["q80_price_multiplier"] = float(np.exp(np.quantile(abs_log, 0.80)))
    row["q90_price_multiplier"] = float(np.exp(np.quantile(abs_log, 0.90)))
    return row


def high_risk_masks(df: pd.DataFrame, thresholds: dict[str, float], pred: np.ndarray) -> dict[str, np.ndarray]:
    large_size = (
        df["is_large_ho"].eq(1)
        | df["is_extra_large_ho"].eq(1)
        | df["is_very_large_area"].eq(1)
        | df["log_area"].ge(thresholds["log_area_q90"])
    ).to_numpy()
    extreme_outlier = (
        df["ho_area_gap_abs"].ge(thresholds["ho_area_gap_q90"])
        | df["log_area"].ge(thresholds["log_area_q90"])
    ).to_numpy()
    pred_extreme = (pred <= thresholds["pred_ln_q20"]) | (pred >= thresholds["pred_ln_q80"])
    combined_score = (
        df["is_large_ho"].eq(1).astype(int).to_numpy()
        + df["is_extra_large_ho"].eq(1).astype(int).to_numpy()
        + df["is_very_large_area"].eq(1).astype(int).to_numpy()
        + df["log_area"].ge(thresholds["log_area_q90"]).astype(int).to_numpy()
        + df["ho_area_gap_abs"].ge(thresholds["ho_area_gap_q80"]).astype(int).to_numpy()
        + pred_extreme.astype(int)
    )
    return {
        "large_size": large_size,
        "extreme_outlier": extreme_outlier,
        "pred_extreme": pred_extreme,
        "combined_score_2plus": combined_score >= 2,
    }


def make_thresholds(train: pd.DataFrame, cal_pred: np.ndarray) -> dict[str, float]:
    return {
        "log_area_q90": float(train["log_area"].quantile(0.90)),
        "ho_area_gap_q80": float(train["ho_area_gap_abs"].quantile(0.80)),
        "ho_area_gap_q90": float(train["ho_area_gap_abs"].quantile(0.90)),
        "pred_ln_q20": float(np.quantile(cal_pred, 0.20)),
        "pred_ln_q80": float(np.quantile(cal_pred, 0.80)),
        "target_ln_q01": float(train[TARGET].quantile(0.01)),
        "target_ln_q05": float(train[TARGET].quantile(0.05)),
        "target_ln_q95": float(train[TARGET].quantile(0.95)),
        "target_ln_q99": float(train[TARGET].quantile(0.99)),
        "global_target_median": float(train[TARGET].median()),
    }


def group_medians(train: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {
        "medium_ho_bucket": train.groupby("medium_ho_bucket")[TARGET].median().to_dict(),
        "ho_bucket_refined": train.groupby("ho_bucket_refined")[TARGET].median().to_dict(),
        "medium_category": train.groupby("medium_category")[TARGET].median().to_dict(),
    }


def group_target(df: pd.DataFrame, group_values: dict[str, float], col: str, fallback: float) -> np.ndarray:
    return df[col].map(group_values).fillna(fallback).to_numpy()


def apply_policy(df: pd.DataFrame, pred: np.ndarray, policy: dict, thresholds: dict[str, float], medians: dict[str, dict[str, float]]) -> np.ndarray:
    out = pred.copy()
    kind = policy["kind"]
    if kind == "clip_train_target":
        out = np.clip(out, thresholds[policy["lo"]], thresholds[policy["hi"]])
    elif kind == "shrink_global":
        mask = high_risk_masks(df, thresholds, pred)[policy["mask"]]
        out[mask] = (1.0 - policy["weight"]) * out[mask] + policy["weight"] * thresholds["global_target_median"]
    elif kind == "shrink_group":
        mask = high_risk_masks(df, thresholds, pred)[policy["mask"]]
        target = group_target(df, medians[policy["group_col"]], policy["group_col"], thresholds["global_target_median"])
        out[mask] = (1.0 - policy["weight"]) * out[mask] + policy["weight"] * target[mask]
    elif kind == "cap_high_risk_to_target_q":
        mask = high_risk_masks(df, thresholds, pred)[policy["mask"]]
        out[mask] = np.clip(out[mask], thresholds[policy["lo"]], thresholds[policy["hi"]])
    else:
        raise ValueError(f"unknown policy: {kind}")
    return out


def candidate_policies() -> list[dict]:
    policies: list[dict] = [
        {"name": "clip_target_q01_q99", "hypothesis": "H81", "kind": "clip_train_target", "lo": "target_ln_q01", "hi": "target_ln_q99"},
        {"name": "clip_target_q05_q95", "hypothesis": "H81", "kind": "clip_train_target", "lo": "target_ln_q05", "hi": "target_ln_q95"},
    ]
    for mask in ["large_size", "extreme_outlier", "pred_extreme", "combined_score_2plus"]:
        for weight in [0.10, 0.20, 0.30, 0.40]:
            policies.append({"name": f"global_shrink_{mask}_w{weight:.2f}", "hypothesis": "H82", "kind": "shrink_global", "mask": mask, "weight": weight})
        for group_col in ["medium_ho_bucket", "ho_bucket_refined", "medium_category"]:
            for weight in [0.10, 0.20, 0.30]:
                policies.append({"name": f"group_shrink_{mask}_{group_col}_w{weight:.2f}", "hypothesis": "H83", "kind": "shrink_group", "mask": mask, "group_col": group_col, "weight": weight})
        policies.append({"name": f"cap_{mask}_q01_q99", "hypothesis": "H84", "kind": "cap_high_risk_to_target_q", "mask": mask, "lo": "target_ln_q01", "hi": "target_ln_q99"})
        policies.append({"name": f"cap_{mask}_q05_q95", "hypothesis": "H84", "kind": "cap_high_risk_to_target_q", "mask": mask, "lo": "target_ln_q05", "hi": "target_ln_q95"})
    return policies


def select_policies(cal: pd.DataFrame, cal_pred: np.ndarray, thresholds: dict[str, float], medians: dict[str, dict[str, float]]) -> list[dict]:
    base = tail_metric(cal, cal_pred)
    rows = []
    for policy in candidate_policies():
        pred = apply_policy(cal, cal_pred, policy, thresholds, medians)
        row = tail_metric(cal, pred)
        rows.append(
            {
                "policy": policy,
                "cal_metric": row,
                "delta_p95": row["p95_ape"] - base["p95_ape"],
                "delta_median": row["median_ape"] - base["median_ape"],
                "delta_q80_x": row["q80_price_multiplier"] - base["q80_price_multiplier"],
            }
        )
    eligible = [
        row
        for row in rows
        if row["delta_p95"] < -0.02
        and row["delta_median"] <= 0.03
        and row["cal_metric"]["within_30pct"] >= base["within_30pct"] - 0.03
    ]
    if not eligible:
        eligible = [row for row in rows if row["delta_p95"] < 0 and row["delta_median"] <= 0.05]
    return sorted(eligible, key=lambda row: (row["cal_metric"]["p95_ape"], row["cal_metric"]["median_ape"]))[:10]


def run() -> dict:
    train_raw = pd.read_csv(SPLIT / "track3_train.csv")
    cold_raw = pd.read_csv(SPLIT / "track3_test_cold.csv")

    core_raw, cal_raw = split_cold_calibration(train_raw)
    core, [cal] = prepare(core_raw, cal_raw)
    cal_pred = cold_h32_predict(core, cal)
    thresholds = make_thresholds(core, cal_pred)
    medians = group_medians(core)
    selected = select_policies(cal, cal_pred, thresholds, medians)

    full_train, [cold] = prepare(train_raw, cold_raw)
    cold_pred = cold_h32_predict(full_train, cold)
    full_thresholds = make_thresholds(full_train, cal_pred)
    full_medians = group_medians(full_train)
    test_base = tail_metric(cold, cold_pred)

    test_results = []
    for selected_row in selected:
        policy = selected_row["policy"]
        pred = apply_policy(cold, cold_pred, policy, full_thresholds, full_medians)
        row = tail_metric(cold, pred)
        test_results.append(
            {
                "policy": policy,
                "cal_metric": selected_row["cal_metric"],
                "test_metric": row,
                "test_delta": {
                    "median_ape": row["median_ape"] - test_base["median_ape"],
                    "p90_ape": row["p90_ape"] - test_base["p90_ape"],
                    "p95_ape": row["p95_ape"] - test_base["p95_ape"],
                    "p99_ape": row["p99_ape"] - test_base["p99_ape"],
                    "q80_price_multiplier": row["q80_price_multiplier"] - test_base["q80_price_multiplier"],
                    "within_30pct": row["within_30pct"] - test_base["within_30pct"],
                },
            }
        )

    return {
        "experiment_id": "H81_H86_cold_tail_risk_mitigation",
        "date": DATE,
        "data": {
            "train_rows": int(len(train_raw)),
            "cold_rows": int(len(cold_raw)),
            "internal_cold_calibration_rows": int(len(cal)),
            "internal_cold_calibration_artists": int(cal[ARTIST_COL].nunique()),
        },
        "model_policy": "H32 Cold conditional fallback",
        "selection_rule": "Choose policies on internal calibration only: reduce p95 APE, keep median APE increase <= 0.03 and within-30% drop <= 0.03 where possible.",
        "baseline_test_metric": test_base,
        "selected_policies_test_results": test_results,
        "judgement": {
            "h81": "Prediction clipping is useful only if it reduces p95 without damaging median/within-30%.",
            "h82": "Global shrinkage is useful only if high-risk tail improves on release test after calibration selection.",
            "h83": "Group shrinkage is useful only if train-derived group medians reduce tail without overfitting.",
            "h84": "High-risk caps are useful only if they reduce p95 and q80 width together.",
            "h85": "If no selected policy improves test tail materially, Cold tail risk should be handled by warnings rather than post-processing.",
            "h86": "Adopt a policy only if it improves p95 by at least 0.05 without increasing median APE by more than 0.02.",
        },
    }


def main() -> None:
    result = run()
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    base = result["baseline_test_metric"]
    print("H81-H86 Cold tail-risk mitigation")
    print(f"saved: {OUT_PATH}")
    print("baseline:", {
        "median": round(base["median_ape"], 4),
        "p95": round(base["p95_ape"], 4),
        "p99": round(base["p99_ape"], 4),
        "q80_x": round(base["q80_price_multiplier"], 3),
    })
    print("selected policies:")
    for row in result["selected_policies_test_results"][:8]:
        m = row["test_metric"]
        d = row["test_delta"]
        print(
            row["policy"]["name"],
            "median=", round(m["median_ape"], 4),
            "p95=", round(m["p95_ape"], 4),
            "p99=", round(m["p99_ape"], 4),
            "q80_x=", round(m["q80_price_multiplier"], 3),
            "delta_p95=", round(d["p95_ape"], 4),
            "delta_median=", round(d["median_ape"], 4),
        )


if __name__ == "__main__":
    main()
