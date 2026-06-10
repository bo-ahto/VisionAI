#!/usr/bin/env python3
"""Run PP-HCOEF17: guarded PP-V8 movement on top of Warm HCOEF stable.

PP-HCOEF16 showed that PP-V8/service component is strong on the 0604 stress
set but weak on fixed validation/test when used directly. This experiment keeps
the current HCOEF stable candidate as the base prediction and only moves toward
PP-V8 in high-confidence or high-agreement regions.

No threshold or weight is learned from test or 0604. Candidate policies are
predefined and selected on validation only; fixed test and 0604 are confirmation
sets.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF17"
EXP_SLUG = "PP-HCOEF17_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

HCOEF16_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF16_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
OPERATIONAL_0604 = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "operational"
    / "outputs"
    / "0604_evaluation"
    / "operational_predictions_with_actual.csv"
)

BASELINE = "hcoef_stable"
REFERENCE = "current_70_30"
PPV8 = "ppv8_service_proxy"
SVC = "svc_numeric_seed_mean"

SEED = 20260608
N_BOOTSTRAP = 300


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((actual_log - pred_log) ** 2))),
        "Within_30": float(np.nanmean(ape <= 0.30)),
        "Within_50": float(np.nanmean(ape <= 0.50)),
        "over_2x_n": int(np.nansum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual_price * 0.5)),
    }


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        pred_log,
    )


def metric_row(
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    stable_metric: dict[str, float],
    scope: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "scope": scope,
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": n,
        **m,
        "delta_MdAPE_vs_stable": m["MdAPE"] - stable_metric["MdAPE"],
        "delta_MAPE_vs_stable": m["MAPE"] - stable_metric["MAPE"],
        "delta_p95_APE_vs_stable": m["p95_APE"] - stable_metric["p95_APE"],
        "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_metric["RMSE_log"],
        "improve_count_vs_stable": int(m["MdAPE"] < stable_metric["MdAPE"])
        + int(m["MAPE"] < stable_metric["MAPE"])
        + int(m["p95_APE"] < stable_metric["p95_APE"]),
    }
    if extra:
        row.update(extra)
    return row


def load_frames() -> dict[str, pd.DataFrame]:
    preds = pd.read_csv(HCOEF16_PREDICTIONS, low_memory=False)
    base = preds[
        preds["candidate"].eq(BASELINE)
        & preds["split"].isin(["validation", "test", "0604_ex50"])
    ].copy()
    keep = [
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        BASELINE,
        REFERENCE,
        PPV8,
        SVC,
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    base = base[keep].drop_duplicates(["split", "_track6_row_id"]).copy()

    if OPERATIONAL_0604.exists():
        operational = pd.read_csv(OPERATIONAL_0604, low_memory=False)
        op_cols = [
            "_track6_row_id",
            "title",
            "artist_name",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "width_cm",
            "height_cm",
            "area_cm2",
            "log_area",
            "l10_quantile_width",
            "l10_price_range_ratio",
            "service_confidence_tier",
            "service_primary_candidate",
            "service_primary_pred_log",
            "pp_v8_compact_blend_mape_guarded_pred_log",
        ]
        op_cols = [c for c in op_cols if c in operational.columns]
        op = operational[op_cols].drop_duplicates("_track6_row_id")
        base = base.merge(op, on="_track6_row_id", how="left")

    base = add_features(base)
    return {
        split: frame.reset_index(drop=True)
        for split, frame in base.groupby("split", sort=False)
    }


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in [BASELINE, REFERENCE, PPV8, SVC]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in ["svc_group_level", "svc_coverage_tier"]:
        out[col] = out[col].fillna("__MISSING__").astype(str)
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    coverage_map = {
        "high_n": 2.0,
        "medium_n": 1.0,
        "low_n": 0.0,
        "__MISSING__": 0.0,
        "nan": 0.0,
    }
    out["coverage_numeric"] = out["svc_coverage_tier"].map(coverage_map).fillna(0.0)
    out["ppv8_minus_stable"] = out[PPV8] - out[BASELINE]
    out["abs_ppv8_stable_gap"] = out["ppv8_minus_stable"].abs()
    out["ppv8_minus_current"] = out[PPV8] - out[REFERENCE]
    out["abs_ppv8_current_gap"] = out["ppv8_minus_current"].abs()
    pred_cols = [BASELINE, REFERENCE, PPV8, SVC]
    out["pred_spread"] = out[pred_cols].max(axis=1) - out[pred_cols].min(axis=1)
    out["ppv8_direction"] = np.where(out["ppv8_minus_stable"] >= 0, "ppv8_higher", "ppv8_lower")
    out["svc_group_n_band"] = pd.cut(
        out["svc_group_n"],
        bins=[-0.1, 4, 9, 19, 49, np.inf],
        labels=["n_0_4", "n_5_9", "n_10_19", "n_20_49", "n_50_plus"],
    ).astype(str)
    out["gap_band"] = pd.cut(
        out["abs_ppv8_stable_gap"],
        bins=[-0.001, 0.03, 0.05, 0.10, 0.20, np.inf],
        labels=["gap_000_003", "gap_003_005", "gap_005_010", "gap_010_020", "gap_020_plus"],
    ).astype(str)
    if "l10_price_range_ratio" in out.columns:
        out["l10_price_range_ratio"] = pd.to_numeric(out["l10_price_range_ratio"], errors="coerce")
        out["l10_range_ratio_band"] = pd.cut(
            out["l10_price_range_ratio"],
            bins=[-0.001, 0.25, 0.50, 0.75, 1.0, np.inf],
            labels=["range_000_025", "range_025_050", "range_050_075", "range_075_100", "range_100_plus"],
        ).astype(str)
    else:
        out["l10_range_ratio_band"] = "__MISSING__"
    return out


def slug(value: float) -> str:
    return str(value).replace(".", "p")


def build_policy_configs() -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    configs.extend(
        [
            {"candidate": BASELINE, "method": "baseline", "source_col": BASELINE, "description": "HCOEF 안정 후보"},
            {"candidate": REFERENCE, "method": "baseline", "source_col": REFERENCE, "description": "기존 70:30 기준"},
            {"candidate": PPV8, "method": "component", "source_col": PPV8, "description": "PP-V8/service proxy"},
            {"candidate": SVC, "method": "component", "source_col": SVC, "description": "유사 작품 기반 가격 피처"},
        ]
    )
    for gap in [0.03, 0.05, 0.10, 0.15, 0.20]:
        for cap in [0.02, 0.03, 0.05]:
            for weight in [0.10, 0.25, 0.50]:
                configs.append(
                    {
                        "candidate": f"hcoef17_guard_agree_gap{slug(gap)}_cap{slug(cap)}_w{slug(weight)}",
                        "method": "guarded_move",
                        "policy_type": "agreement_only",
                        "gap": gap,
                        "cap": cap,
                        "weight": weight,
                        "coverage_min": 0.0,
                        "n_min": 0.0,
                        "description": f"PP-V8과 HCOEF 안정 후보 차이가 {gap} 이하일 때만 cap {cap}, weight {weight}로 이동.",
                    }
                )
    for coverage_min in [1.0, 2.0]:
        for n_min in [10.0, 20.0]:
            for gap in [0.05, 0.10, 0.15]:
                for cap in [0.03, 0.05]:
                    for weight in [0.10, 0.25]:
                        configs.append(
                            {
                                "candidate": (
                                    f"hcoef17_guard_cov{int(coverage_min)}_n{int(n_min)}_"
                                    f"gap{slug(gap)}_cap{slug(cap)}_w{slug(weight)}"
                                ),
                                "method": "guarded_move",
                                "policy_type": "coverage_agreement",
                                "gap": gap,
                                "cap": cap,
                                "weight": weight,
                                "coverage_min": coverage_min,
                                "n_min": n_min,
                                "description": (
                                    f"coverage>={coverage_min}, 표본수>={n_min}, PP-V8 gap<={gap}일 때만 "
                                    f"cap {cap}, weight {weight}로 이동."
                                ),
                            }
                        )
    configs.extend(
        [
            {
                "candidate": "hcoef17_adaptive_tiered_conservative",
                "method": "guarded_move",
                "policy_type": "adaptive",
                "description": "high coverage gap<=0.10은 0.25, medium coverage gap<=0.05는 0.10만 이동.",
            },
            {
                "candidate": "hcoef17_adaptive_tiered_mape_guard",
                "method": "guarded_move",
                "policy_type": "adaptive_mape",
                "description": "high coverage gap<=0.15는 0.25, medium coverage gap<=0.10은 0.10만 이동.",
            },
            {
                "candidate": "hcoef17_adaptive_tiny_agreement_only",
                "method": "guarded_move",
                "policy_type": "adaptive_tiny",
                "description": "gap<=0.03일 때만 cap 0.02, weight 0.50으로 아주 좁게 이동.",
            },
        ]
    )
    return configs


def predict_policy(frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if config["method"] in ["baseline", "component"]:
        pred = frame[config["source_col"]].to_numpy(dtype=float)
        mask = np.ones(len(frame), dtype=bool)
        move = pred - frame[BASELINE].to_numpy(dtype=float)
        return pred, mask, move

    stable = frame[BASELINE].to_numpy(dtype=float)
    ppv8_delta = frame["ppv8_minus_stable"].to_numpy(dtype=float)
    abs_gap = frame["abs_ppv8_stable_gap"].to_numpy(dtype=float)
    coverage = frame["coverage_numeric"].to_numpy(dtype=float)
    group_n = frame["svc_group_n"].to_numpy(dtype=float)

    policy_type = config["policy_type"]
    if policy_type in ["agreement_only", "coverage_agreement"]:
        mask = abs_gap <= float(config["gap"])
        if policy_type == "coverage_agreement":
            mask &= coverage >= float(config["coverage_min"])
            mask &= group_n >= float(config["n_min"])
        move = np.clip(ppv8_delta, -float(config["cap"]), float(config["cap"])) * float(config["weight"])
    elif policy_type == "adaptive":
        high = (coverage >= 2.0) & (group_n >= 20) & (abs_gap <= 0.10)
        medium = (coverage >= 1.0) & (group_n >= 10) & (abs_gap <= 0.05)
        weights = np.where(high, 0.25, np.where(medium, 0.10, 0.0))
        mask = weights > 0
        move = np.clip(ppv8_delta, -0.03, 0.03) * weights
    elif policy_type == "adaptive_mape":
        high = (coverage >= 2.0) & (group_n >= 20) & (abs_gap <= 0.15)
        medium = (coverage >= 1.0) & (group_n >= 10) & (abs_gap <= 0.10)
        weights = np.where(high, 0.25, np.where(medium, 0.10, 0.0))
        mask = weights > 0
        move = np.clip(ppv8_delta, -0.05, 0.05) * weights
    elif policy_type == "adaptive_tiny":
        mask = abs_gap <= 0.03
        move = np.clip(ppv8_delta, -0.02, 0.02) * 0.50
    else:
        raise ValueError(f"Unknown policy type: {policy_type}")

    pred = stable + np.where(mask, move, 0.0)
    return pred, mask, move


def prediction_frame(frame: pd.DataFrame, config: dict[str, Any], pred: np.ndarray, mask: np.ndarray, move: np.ndarray) -> pd.DataFrame:
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": config["candidate"],
            "method": config["method"],
            "split": frame["split"].to_numpy(),
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred,
            "pred_price": pred_price,
            "hcoef_stable": frame[BASELINE].to_numpy(dtype=float),
            "current_70_30": frame[REFERENCE].to_numpy(dtype=float),
            "ppv8_service_proxy": frame[PPV8].to_numpy(dtype=float),
            "svc_numeric_seed_mean": frame[SVC].to_numpy(dtype=float),
            "policy_applied": mask.astype(int),
            "policy_move_log": np.where(mask, move, 0.0),
            "abs_ppv8_stable_gap": frame["abs_ppv8_stable_gap"].to_numpy(dtype=float),
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
            "svc_group_n_band": frame["svc_group_n_band"].astype(str).to_numpy(),
            "gap_band": frame["gap_band"].astype(str).to_numpy(),
            "ppv8_direction": frame["ppv8_direction"].astype(str).to_numpy(),
            "l10_range_ratio_band": frame["l10_range_ratio_band"].astype(str).to_numpy(),
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def fixed_confirmation(frames: dict[str, pd.DataFrame], configs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    residual_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    for split, frame in frames.items():
        stable_metric = metric(frame, frame[BASELINE].to_numpy(dtype=float))
        for config in configs:
            pred, mask, move = predict_policy(frame, config)
            m = metric(frame, pred)
            metric_rows.append(
                metric_row(
                    split,
                    config["candidate"],
                    config["method"],
                    len(frame),
                    m,
                    stable_metric,
                    "fixed_confirmation",
                    {
                        "policy_apply_rate": float(mask.mean()),
                        "mean_policy_move_log": float(np.nanmean(np.where(mask, move, 0.0))),
                        "mean_abs_policy_move_log": float(np.nanmean(np.abs(np.where(mask, move, 0.0)))),
                    },
                )
            )
            pred_rows.append(prediction_frame(frame, config, pred, mask, move))
            residual_rows.append(residual_row(frame, config, pred, mask, move))
            policy_rows.append(policy_row(config))
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.DataFrame(residual_rows), pd.DataFrame(policy_rows).drop_duplicates("candidate")


def residual_row(frame: pd.DataFrame, config: dict[str, Any], pred: np.ndarray, mask: np.ndarray, move: np.ndarray) -> dict[str, Any]:
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    residual = frame["actual_log"].to_numpy(dtype=float) - pred
    ape = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    return {
        "split": str(frame["split"].iloc[0]),
        "candidate": config["candidate"],
        "method": config["method"],
        "n": len(frame),
        "policy_apply_rate": float(mask.mean()),
        "median_policy_move_log": float(np.nanmedian(np.where(mask, move, 0.0))),
        "mean_abs_policy_move_log": float(np.nanmean(np.abs(np.where(mask, move, 0.0)))),
        "median_residual_log": float(np.nanmedian(residual)),
        "mean_residual_log": float(np.nanmean(residual)),
        "residual_std": float(np.nanstd(residual)),
        "ape_median": float(np.nanmedian(ape)),
        "ape_mean": float(np.nanmean(ape)),
        "ape_p95": float(np.nanquantile(ape, 0.95)),
        "over_2x_n": int(np.nansum(pred_price >= actual * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual * 0.5)),
    }


def policy_row(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate": config["candidate"],
        "method": config["method"],
        "policy_type": config.get("policy_type", config["method"]),
        "gap": config.get("gap", np.nan),
        "cap": config.get("cap", np.nan),
        "weight": config.get("weight", np.nan),
        "coverage_min": config.get("coverage_min", np.nan),
        "n_min": config.get("n_min", np.nan),
        "source_col": config.get("source_col", ""),
        "description": config.get("description", ""),
    }


def coefficient_proxy(policy_map: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in policy_map.iterrows():
        candidate = row["candidate"]
        method = row["method"]
        if method in ["baseline", "component"]:
            rows.append(
                {
                    "candidate": candidate,
                    "feature": row.get("source_col", ""),
                    "coefficient_or_policy_role": "source prediction",
                    "direction": "해당 예측값을 그대로 사용",
                    "value": 1.0,
                    "description": row["description"],
                }
            )
            continue
        rows.extend(
            [
                {
                    "candidate": candidate,
                    "feature": "ppv8_minus_stable",
                    "coefficient_or_policy_role": "bounded movement",
                    "direction": "PP-V8이 더 높으면 가격을 올리고, 낮으면 가격을 낮춤",
                    "value": row.get("weight", np.nan),
                    "description": "clip된 PP-V8-HCOEF 차이에 적용되는 이동 비율",
                },
                {
                    "candidate": candidate,
                    "feature": "abs_ppv8_stable_gap",
                    "coefficient_or_policy_role": "gate",
                    "direction": "차이가 작을수록 PP-V8 반영 허용",
                    "value": row.get("gap", np.nan),
                    "description": "예측값 차이가 큰 구간에서는 HCOEF 안정 후보 유지",
                },
                {
                    "candidate": candidate,
                    "feature": "svc_coverage_tier / svc_group_n",
                    "coefficient_or_policy_role": "confidence gate",
                    "direction": "비교군 신뢰도가 높을수록 PP-V8 반영 허용",
                    "value": row.get("coverage_min", np.nan),
                    "description": "유사 작품 기반 가격 피처가 충분한 구간인지 확인",
                },
            ]
        )
    return pd.DataFrame(rows)


def bootstrap_summary(frames: dict[str, pd.DataFrame], configs: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(SEED)
    for split in ["validation", "test"]:
        frame = frames[split]
        pred_map = {config["candidate"]: predict_policy(frame, config)[0] for config in configs}
        stable_pred = pred_map[BASELINE]
        actual_price = frame["actual_price"].to_numpy(dtype=float)
        actual_log = frame["actual_log"].to_numpy(dtype=float)
        artists = frame["artist_key"].astype(str).to_numpy()
        unique_artists = np.unique(artists)
        for scheme in ["row_bootstrap", "artist_bootstrap"]:
            per_candidate = {config["candidate"]: [] for config in configs}
            for _ in range(N_BOOTSTRAP):
                if scheme == "row_bootstrap":
                    idx = rng.integers(0, len(frame), len(frame))
                else:
                    sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                    idx = np.concatenate([np.flatnonzero(artists == artist) for artist in sampled_artists])
                    if len(idx) == 0:
                        continue
                stable_m = metric_from_arrays(actual_price[idx], actual_log[idx], stable_pred[idx])
                for config in configs:
                    pred = pred_map[config["candidate"]]
                    m = metric_from_arrays(actual_price[idx], actual_log[idx], pred[idx])
                    per_candidate[config["candidate"]].append(
                        (
                            m["MdAPE"] - stable_m["MdAPE"],
                            m["MAPE"] - stable_m["MAPE"],
                            m["p95_APE"] - stable_m["p95_APE"],
                            m["RMSE_log"] - stable_m["RMSE_log"],
                        )
                    )
            for config in configs:
                arr = np.asarray(per_candidate[config["candidate"]], dtype=float)
                if arr.size == 0:
                    continue
                rows.append(
                    {
                        "split": split,
                        "validation_scheme": scheme,
                        "candidate": config["candidate"],
                        "method": config["method"],
                        "n_bootstrap": len(arr),
                        "mean_delta_MdAPE_vs_stable": float(arr[:, 0].mean()),
                        "mean_delta_MAPE_vs_stable": float(arr[:, 1].mean()),
                        "mean_delta_p95_APE_vs_stable": float(arr[:, 2].mean()),
                        "mean_delta_RMSE_log_vs_stable": float(arr[:, 3].mean()),
                        "MdAPE_improve_prob": float((arr[:, 0] < 0).mean()),
                        "MAPE_improve_prob": float((arr[:, 1] < 0).mean()),
                        "p95_improve_prob": float((arr[:, 2] < 0).mean()),
                        "all3_improve_prob": float(((arr[:, 0] < 0) & (arr[:, 1] < 0) & (arr[:, 2] < 0)).mean()),
                        "any2_improve_prob": float(
                            ((arr[:, 0] < 0).astype(int) + (arr[:, 1] < 0).astype(int) + (arr[:, 2] < 0).astype(int) >= 2).mean()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def candidate_selection(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    b_val = bootstrap_df[bootstrap_df["split"].eq("validation")].pivot_table(
        index="candidate",
        columns="validation_scheme",
        values=["all3_improve_prob", "any2_improve_prob"],
        aggfunc="first",
    )
    b_val.columns = [f"validation_{scheme}_{metric}" for metric, scheme in b_val.columns]
    b_val = b_val.reset_index()
    out = val[
        [
            "candidate",
            "method",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "policy_apply_rate",
        ]
    ].rename(
        columns={
            "MdAPE": "validation_MdAPE",
            "MAPE": "validation_MAPE",
            "p95_APE": "validation_p95_APE",
            "RMSE_log": "validation_RMSE_log",
        }
    )
    test_small = test[
        [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
        ]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "RMSE_log": "test_RMSE_log",
            "delta_MdAPE_vs_stable": "test_delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable": "test_delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable": "test_delta_p95_APE_vs_stable",
        }
    )
    out = out.merge(test_small, on="candidate", how="left").merge(b_val, on="candidate", how="left")
    out["validation_pass_2of3"] = (
        (out["delta_MdAPE_vs_stable"] < 0).astype(int)
        + (out["delta_MAPE_vs_stable"] < 0).astype(int)
        + (out["delta_p95_APE_vs_stable"] < 0).astype(int)
        >= 2
    )
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= 0.8064
    out["fixed_test_2of3"] = (
        (out["test_delta_MdAPE_vs_stable"] <= 0).astype(int)
        + (out["test_delta_MAPE_vs_stable"] <= 0).astype(int)
        + (out["test_delta_p95_APE_vs_stable"] <= 0).astype(int)
        >= 2
    )
    row_all3 = out.get("validation_row_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    artist_all3 = out.get("validation_artist_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    out["bootstrap_gate"] = (row_all3 >= 0.90) & (artist_all3 >= 0.90)
    conditions = [
        out["bootstrap_gate"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"],
        out["validation_pass_2of3"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"],
        out["validation_pass_2of3"],
    ]
    choices = ["운영 후보 검토", "fixed test 확인 후보", "validation 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    return out.sort_values(
        ["decision", "validation_MdAPE", "validation_MAPE", "validation_p95_APE"],
        ascending=[True, True, True, True],
    )


def service_gap_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = frames.get("0604_ex50")
    if frame is None:
        return pd.DataFrame()
    stable_pred = frame[BASELINE].to_numpy(dtype=float)
    ppv8_pred = frame[PPV8].to_numpy(dtype=float)
    actual = frame["actual_price"].to_numpy(dtype=float)
    stable_price = np.clip(np.exp(stable_pred), 1_000.0, None)
    ppv8_price = np.clip(np.exp(ppv8_pred), 1_000.0, None)
    stable_ape = np.abs(stable_price - actual) / np.clip(actual, 1.0, None)
    ppv8_ape = np.abs(ppv8_price - actual) / np.clip(actual, 1.0, None)
    cols = [
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_price",
        BASELINE,
        PPV8,
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "svc_group_n_band",
        "gap_band",
        "ppv8_direction",
        "l10_range_ratio_band",
    ]
    optional = ["title", "artist_name", "medium_support_bucket", "width_cm", "height_cm", "area_cm2", "l10_price_range_ratio", "service_confidence_tier"]
    cols += [c for c in optional if c in frame.columns]
    out = frame[cols].copy()
    out["hcoef_stable_ape"] = stable_ape
    out["ppv8_service_proxy_ape"] = ppv8_ape
    out["ppv8_minus_hcoef_ape_delta"] = ppv8_ape - stable_ape
    out["winner"] = np.where(ppv8_ape < stable_ape, "ppv8_better", "hcoef_better_or_tie")
    out["stable_pred_price"] = stable_price
    out["ppv8_pred_price"] = ppv8_price
    return out.sort_values("ppv8_minus_hcoef_ape_delta")


def segment_summary(predictions: pd.DataFrame, selected_candidates: list[str]) -> pd.DataFrame:
    focus = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    segment_cols = ["svc_coverage_tier", "svc_group_level", "svc_group_n_band", "gap_band", "ppv8_direction", "l10_range_ratio_band"]
    rows: list[dict[str, Any]] = []
    for segment_col in segment_cols:
        for (split, candidate, value), group in focus.groupby(["split", "candidate", segment_col], dropna=False):
            if len(group) < 5:
                continue
            rows.append(
                {
                    "split": split,
                    "candidate": candidate,
                    "segment_col": segment_col,
                    "segment_value": value,
                    "n": len(group),
                    "MdAPE": float(group["ape"].median()),
                    "MAPE": float(group["ape"].mean()),
                    "p95_APE": float(group["ape"].quantile(0.95)),
                    "median_residual_log": float(group["residual_log"].median()),
                    "policy_apply_rate": float(group["policy_applied"].mean()),
                }
            )
    return pd.DataFrame(rows).sort_values(["split", "segment_col", "MAPE"], ascending=[True, True, False])


def markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    show = df.head(max_rows).copy()
    cols = list(show.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(markdown_cell(row[col]) for col in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(df)} rows shown._")
    return "\n".join(lines)


def md_to_html(markdown: str) -> str:
    lines: list[str] = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("| ") and line.endswith(" |"):
            cells = [html.escape(c.strip()) for c in line.strip("|").split("|")]
            if not in_table:
                lines.append("<table>")
                in_table = True
                lines.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            elif set(cells[0]) <= {"-"}:
                continue
            else:
                lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            lines.append("</table>")
            in_table = False
        if line.startswith("# "):
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            lines.append(f"<p>{html.escape(line)}</p>")
        elif not line:
            lines.append("")
        else:
            lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        lines.append("</table>")
    style = """
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 28px; color: #1f2933; }
    h1, h2, h3 { color: #17202a; }
    table { border-collapse: collapse; width: 100%; margin: 14px 0 24px; font-size: 13px; }
    th, td { border: 1px solid #d7dee8; padding: 7px 9px; text-align: left; vertical-align: top; }
    th { background: #eef3f8; }
    p { line-height: 1.55; }
    </style>
    """
    return "<!doctype html><html><head><meta charset='utf-8'>" + style + "</head><body>" + "\n".join(lines) + "</body></html>"


def render_report(metrics_df: pd.DataFrame, selection: pd.DataFrame, bootstrap_df: pd.DataFrame, policy_map: pd.DataFrame, gap_audit: pd.DataFrame, segment_df: pd.DataFrame) -> str:
    validation_top = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    stress_top = metrics_df[metrics_df["split"].eq("0604_ex50")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    selected_top = selection.sort_values(["decision", "validation_MdAPE", "test_MdAPE"]).head(20)
    boot_focus = bootstrap_df[
        bootstrap_df["candidate"].isin(selected_top["candidate"].tolist() + [BASELINE, PPV8, REFERENCE])
    ].copy()
    if not gap_audit.empty:
        ppv8_better = float((gap_audit["winner"] == "ppv8_better").mean())
        gap_summary = gap_audit.groupby(["svc_coverage_tier", "gap_band", "winner"], dropna=False).size().reset_index(name="n")
    else:
        ppv8_better = np.nan
        gap_summary = pd.DataFrame()
    lines = [
        "# PP-HCOEF17 Warm guarded PP-V8 movement",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: HCOEF 안정 후보를 기본으로 유지하면서 PP-V8/service component를 신뢰 가능한 구간에만 제한 반영할 수 있는지 검증",
        "- 기준 후보: `hcoef2_size_reliability_cap005_s050`",
        "- 선택 기준: validation 우선, fixed test와 0604는 확인용",
        "- 금지 기준: test/0604 residual을 보고 threshold, weight, cap을 만들지 않음",
        "",
        "## 1. 실행 결론",
        "",
        "- PP-V8 전체 반영은 HCOEF16에서 fixed test/artist OOF 기준 미통과였음.",
        "- HCOEF17은 PP-V8과 HCOEF 안정 후보의 예측 차이가 작거나 비교군 신뢰도가 높은 구간에서만 제한 이동하는 후보를 비교함.",
        "- 새 후보는 validation에서 먼저 판단하고, fixed test p95 guard와 bootstrap으로 재검증함.",
        f"- 0604에서 PP-V8이 HCOEF 안정 후보보다 APE가 낮은 비율: `{ppv8_better:.4f}`",
        "",
        "## 2. validation 상위 후보",
        "",
        markdown_table(validation_top[["candidate", "method", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "policy_apply_rate"]].round(4), 25),
        "",
        "## 3. fixed test 상위 후보",
        "",
        markdown_table(test_top[["candidate", "method", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "policy_apply_rate"]].round(4), 25),
        "",
        "## 4. 0604 stress test 상위 후보",
        "",
        markdown_table(stress_top[["candidate", "method", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "policy_apply_rate"]].round(4), 25),
        "",
        "## 5. 후보 선택표",
        "",
        markdown_table(selected_top.round(4), 25),
        "",
        "## 6. bootstrap 요약",
        "",
        markdown_table(boot_focus.sort_values(["split", "validation_scheme", "all3_improve_prob"], ascending=[True, True, False]).round(4), 40),
        "",
        "## 7. 0604 PP-V8/HCOEF 승패 구간",
        "",
        markdown_table(gap_summary.sort_values(["svc_coverage_tier", "gap_band", "winner"]).head(40), 40),
        "",
        "## 8. 구간별 오차 요약",
        "",
        markdown_table(segment_df.head(40).round(4), 40),
        "",
        "## 9. 정책/계수 해석",
        "",
        markdown_table(policy_map.head(40).round(4), 40),
        "",
        "## 10. 해석",
        "",
        "- `ppv8_minus_stable`는 PP-V8 예측값과 HCOEF 안정 후보의 로그 가격 차이임.",
        "- 정책 후보는 이 차이를 그대로 쓰지 않고 `cap`으로 자른 뒤 `weight`만큼만 반영함.",
        "- `abs_ppv8_stable_gap`은 두 모델이 얼마나 다르게 보는지를 의미함. 차이가 큰 구간에서는 PP-V8을 신뢰하지 않고 HCOEF 안정 후보를 유지함.",
        "- `svc_coverage_tier`와 `svc_group_n`은 유사 작품 기반 가격 피처의 신뢰도를 나타냄. 표본이 많고 coverage가 높을 때만 PP-V8 이동을 허용하는 후보를 별도 비교함.",
        "- 이 실험에서 운영 후보가 나오지 않으면, PP-V8은 점 예측 교체보다 신뢰도/가격 범위/risk guard에 쓰는 것이 더 타당함.",
        "",
        "## 11. 산출물",
        "",
        "- `outputs/metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/feature_coefficients.csv`",
        "- `outputs/policy_map.csv`",
        "- `outputs/residual_analysis.csv`",
        "- `outputs/bootstrap_or_repeated_split_summary.csv`",
        "- `outputs/service_feature_gap_audit.csv`",
        "- `outputs/error_segment_summary.csv`",
        "- `outputs/selected_candidates.csv`",
    ]
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    frames = load_frames()
    configs = build_policy_configs()
    metrics_df, predictions, residuals, policy_map = fixed_confirmation(frames, configs)
    bootstrap_df = bootstrap_summary(frames, configs)
    selection = candidate_selection(metrics_df, bootstrap_df)
    feature_coefficients = coefficient_proxy(policy_map)
    gap_audit = service_gap_audit(frames)
    selected_candidates = selection.head(8)["candidate"].tolist()
    segment_candidates = list(dict.fromkeys([BASELINE, PPV8, REFERENCE, *selected_candidates]))
    segment_df = segment_summary(predictions, segment_candidates)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    feature_coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    policy_map.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    gap_audit.to_csv(EXP_DIR / "outputs" / "service_feature_gap_audit.csv", index=False)
    segment_df.to_csv(EXP_DIR / "outputs" / "error_segment_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Guarded PP-V8 movement over Warm HCOEF stable candidate",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "ppv8_component": PPV8,
        "n_bootstrap": N_BOOTSTRAP,
        "inputs": {
            "hcoef16_predictions": str(HCOEF16_PREDICTIONS.relative_to(REPO)),
            "operational_0604": str(OPERATIONAL_0604.relative_to(REPO)),
        },
        "candidate_count": len(configs),
        "candidates": configs,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_report(metrics_df, selection, bootstrap_df, policy_map, gap_audit, segment_df)
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(report), encoding="utf-8")

    doc_summary = DOC_ROOT / "pp_hcoef17_warm_huber_price_basis_coefficient_refinement_summary.md"
    doc_summary.write_text(report, encoding="utf-8")
    doc_summary.with_suffix(".html").write_text(md_to_html(report), encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(
        metrics_df[metrics_df["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])[["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "policy_apply_rate"]]
        .head(15)
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
