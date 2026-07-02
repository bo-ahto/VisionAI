#!/usr/bin/env python3
"""Run PP-HCOEF18: quantile-risk guarded refinement over Warm HCOEF stable.

This experiment keeps the current Warm HCOEF stable prediction as the default
point estimate and uses PP-L10 quantile width only as a pre-known risk signal.
No boundary is learned from test or 0604 residuals. Quantile-width thresholds
are computed from validation predictions, then applied unchanged to fixed test
and 0604 stress-test data.
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
EXP_ID = "PP-HCOEF18"
EXP_SLUG = "PP-HCOEF18_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

HCOEF17_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF17_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
PP_L10_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-L10_warm_l8_feature_variant_sequential"
    / "outputs"
    / "predictions.csv"
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
L10_CANDIDATE = "l8_seq__full_plus_generated_buckets"

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


def load_quantile_features() -> pd.DataFrame:
    l10 = pd.read_csv(PP_L10_PREDICTIONS, low_memory=False)
    q = l10[l10["candidate"].eq(L10_CANDIDATE)].copy()
    keep = [
        "split",
        "_track6_row_id",
        "pred_log",
        "q10_log",
        "q50_log",
        "q90_log",
        "quantile_width",
    ]
    q = q[keep].rename(columns={"pred_log": "l10_seq_pred_log"})
    q["l10_price_range_ratio"] = (
        np.exp(q["q90_log"]) - np.exp(q["q10_log"])
    ) / np.clip(np.exp(q["q50_log"]), 1_000.0, None)
    return q.drop_duplicates(["split", "_track6_row_id"])


def load_frames() -> tuple[dict[str, pd.DataFrame], dict[str, float]]:
    preds = pd.read_csv(HCOEF17_PREDICTIONS, low_memory=False)
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

    q = load_quantile_features()
    base = base.merge(q, on=["split", "_track6_row_id"], how="left")

    if OPERATIONAL_0604.exists():
        op = pd.read_csv(OPERATIONAL_0604, low_memory=False)
        op_keep = [
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
            "l10_generated_bucket_seq_pred_log",
            "service_confidence_tier",
        ]
        op_keep = [c for c in op_keep if c in op.columns]
        op = op[op_keep].drop_duplicates("_track6_row_id")
        base = base.merge(op, on="_track6_row_id", how="left", suffixes=("", "_0604"))
        mask_0604 = base["split"].eq("0604_ex50")
        if "l10_quantile_width" in base.columns:
            base.loc[mask_0604, "quantile_width"] = base.loc[mask_0604, "quantile_width"].fillna(
                base.loc[mask_0604, "l10_quantile_width"]
            )
        if "l10_price_range_ratio_0604" in base.columns:
            base.loc[mask_0604, "l10_price_range_ratio"] = base.loc[mask_0604, "l10_price_range_ratio"].fillna(
                base.loc[mask_0604, "l10_price_range_ratio_0604"]
            )
        if "l10_generated_bucket_seq_pred_log" in base.columns:
            base.loc[mask_0604, "l10_seq_pred_log"] = base.loc[mask_0604, "l10_seq_pred_log"].fillna(
                base.loc[mask_0604, "l10_generated_bucket_seq_pred_log"]
            )

    validation_q = base.loc[base["split"].eq("validation"), "quantile_width"].dropna()
    thresholds = {
        "qwidth_q33": float(validation_q.quantile(0.33)),
        "qwidth_q50": float(validation_q.quantile(0.50)),
        "qwidth_q66": float(validation_q.quantile(0.66)),
        "qwidth_q80": float(validation_q.quantile(0.80)),
    }
    validation_spread = (
        base.loc[base["split"].eq("validation"), [BASELINE, REFERENCE, PPV8, SVC]]
        .astype(float)
        .max(axis=1)
        - base.loc[base["split"].eq("validation"), [BASELINE, REFERENCE, PPV8, SVC]].astype(float).min(axis=1)
    )
    thresholds["pred_spread_q66"] = float(validation_spread.quantile(0.66))
    thresholds["pred_spread_q80"] = float(validation_spread.quantile(0.80))

    base = add_features(base, thresholds)
    return {
        split: frame.reset_index(drop=True)
        for split, frame in base.groupby("split", sort=False)
    }, thresholds


def add_features(frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    out = frame.copy()
    for col in [BASELINE, REFERENCE, PPV8, SVC, "l10_seq_pred_log", "quantile_width", "l10_price_range_ratio"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in ["svc_group_level", "svc_coverage_tier"]:
        out[col] = out[col].fillna("__MISSING__").astype(str)
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    coverage_map = {"high_n": 2.0, "medium_n": 1.0, "low_n": 0.0, "__MISSING__": 0.0, "nan": 0.0}
    out["coverage_numeric"] = out["svc_coverage_tier"].map(coverage_map).fillna(0.0)
    out["ppv8_minus_stable"] = out[PPV8] - out[BASELINE]
    out["current_minus_stable"] = out[REFERENCE] - out[BASELINE]
    out["l10_minus_stable"] = out["l10_seq_pred_log"] - out[BASELINE]
    out["abs_ppv8_stable_gap"] = out["ppv8_minus_stable"].abs()
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
    out["qwidth_band"] = pd.cut(
        out["quantile_width"],
        bins=[-np.inf, thresholds["qwidth_q33"], thresholds["qwidth_q66"], thresholds["qwidth_q80"], np.inf],
        labels=["qwidth_low", "qwidth_mid", "qwidth_high", "qwidth_extreme"],
    ).astype(str)
    out["pred_spread_band"] = pd.cut(
        out["pred_spread"],
        bins=[-np.inf, thresholds["pred_spread_q66"], thresholds["pred_spread_q80"], np.inf],
        labels=["spread_low_mid", "spread_high", "spread_extreme"],
    ).astype(str)
    return out


def slug(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def build_policy_configs(thresholds: dict[str, float]) -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = [
        {"candidate": BASELINE, "method": "baseline", "source_col": BASELINE, "description": "HCOEF 안정 후보"},
        {"candidate": REFERENCE, "method": "baseline", "source_col": REFERENCE, "description": "기존 70:30 기준"},
        {"candidate": PPV8, "method": "component", "source_col": PPV8, "description": "PP-V8/service proxy"},
        {"candidate": SVC, "method": "component", "source_col": SVC, "description": "유사 작품 기반 가격 피처"},
        {
            "candidate": "l10_seq_full_generated_bucket",
            "method": "component",
            "source_col": "l10_seq_pred_log",
            "description": "PP-L10 Quantile->Huber->CatBoost 순차 구조 예측값",
        },
    ]

    for q_name in ["qwidth_q66", "qwidth_q80"]:
        qv = thresholds[q_name]
        for cap in [0.02, 0.03, 0.05]:
            for weight in [0.25, 0.50, 0.75]:
                configs.append(
                    {
                        "candidate": f"hcoef18_qrisk_shrink_current_{q_name}_cap{slug(cap)}_w{slug(weight)}",
                        "method": "quantile_guard",
                        "policy_type": "high_qwidth_shrink_current",
                        "qwidth_threshold_name": q_name,
                        "qwidth_threshold": qv,
                        "cap": cap,
                        "weight": weight,
                        "description": (
                            f"quantile_width가 validation {q_name} 이상이면 HCOEF 보정폭을 current_70_30 방향으로 "
                            f"cap {cap}, weight {weight}만큼 축소."
                        ),
                    }
                )
                configs.append(
                    {
                        "candidate": f"hcoef18_qrisk_shrink_current_spread_{q_name}_cap{slug(cap)}_w{slug(weight)}",
                        "method": "quantile_guard",
                        "policy_type": "high_qwidth_or_spread_shrink_current",
                        "qwidth_threshold_name": q_name,
                        "qwidth_threshold": qv,
                        "spread_threshold": thresholds["pred_spread_q80"],
                        "cap": cap,
                        "weight": weight,
                        "description": (
                            f"quantile_width가 {q_name} 이상이거나 후보 간 spread가 높으면 HCOEF 보정폭을 "
                            f"current_70_30 방향으로 제한 축소."
                        ),
                    }
                )

    for q_name in ["qwidth_q33", "qwidth_q50"]:
        qv = thresholds[q_name]
        for gap in [0.05, 0.10, 0.15]:
            for cap in [0.02, 0.03, 0.05]:
                for weight in [0.10, 0.25, 0.50]:
                    configs.append(
                        {
                            "candidate": f"hcoef18_qrisk_lowq_ppv8_{q_name}_gap{slug(gap)}_cap{slug(cap)}_w{slug(weight)}",
                            "method": "quantile_guard",
                            "policy_type": "low_qwidth_ppv8_move",
                            "qwidth_threshold_name": q_name,
                            "qwidth_threshold": qv,
                            "gap": gap,
                            "cap": cap,
                            "weight": weight,
                            "description": (
                                f"quantile_width가 validation {q_name} 이하이고 PP-V8 gap이 {gap} 이하일 때만 "
                                f"PP-V8 방향으로 제한 이동."
                            ),
                        }
                    )

    for shrink_cap in [0.02, 0.03, 0.05]:
        for ppv8_cap in [0.02, 0.03]:
            configs.append(
                {
                    "candidate": f"hcoef18_qrisk_adaptive_shrink{slug(shrink_cap)}_ppv8{slug(ppv8_cap)}",
                    "method": "quantile_guard",
                    "policy_type": "adaptive_qrisk",
                    "qwidth_low": thresholds["qwidth_q33"],
                    "qwidth_high": thresholds["qwidth_q80"],
                    "spread_threshold": thresholds["pred_spread_q80"],
                    "shrink_cap": shrink_cap,
                    "ppv8_cap": ppv8_cap,
                    "description": (
                        "low quantile width와 작은 PP-V8 gap에서는 PP-V8 방향으로 소폭 이동하고, "
                        "high quantile width 또는 spread high 구간에서는 current_70_30 방향으로 보정폭 축소."
                    ),
                }
            )
    return configs


def predict_policy(frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if config["method"] in ["baseline", "component"]:
        pred = frame[config["source_col"]].to_numpy(dtype=float)
        mask = np.isfinite(pred)
        pred = np.where(mask, pred, frame[BASELINE].to_numpy(dtype=float))
        move = pred - frame[BASELINE].to_numpy(dtype=float)
        return pred, mask, move

    stable = frame[BASELINE].to_numpy(dtype=float)
    qwidth = frame["quantile_width"].to_numpy(dtype=float)
    pred_spread = frame["pred_spread"].to_numpy(dtype=float)
    ppv8_delta = frame["ppv8_minus_stable"].to_numpy(dtype=float)
    current_delta = frame["current_minus_stable"].to_numpy(dtype=float)
    abs_gap = frame["abs_ppv8_stable_gap"].to_numpy(dtype=float)
    policy_type = config["policy_type"]

    if policy_type == "high_qwidth_shrink_current":
        mask = qwidth >= float(config["qwidth_threshold"])
        move = np.clip(current_delta, -float(config["cap"]), float(config["cap"])) * float(config["weight"])
    elif policy_type == "high_qwidth_or_spread_shrink_current":
        mask = (qwidth >= float(config["qwidth_threshold"])) | (pred_spread >= float(config["spread_threshold"]))
        move = np.clip(current_delta, -float(config["cap"]), float(config["cap"])) * float(config["weight"])
    elif policy_type == "low_qwidth_ppv8_move":
        mask = (qwidth <= float(config["qwidth_threshold"])) & (abs_gap <= float(config["gap"]))
        move = np.clip(ppv8_delta, -float(config["cap"]), float(config["cap"])) * float(config["weight"])
    elif policy_type == "adaptive_qrisk":
        low = (qwidth <= float(config["qwidth_low"])) & (abs_gap <= 0.10)
        high = (qwidth >= float(config["qwidth_high"])) | (pred_spread >= float(config["spread_threshold"]))
        mask = low | high
        move_low = np.clip(ppv8_delta, -float(config["ppv8_cap"]), float(config["ppv8_cap"])) * 0.25
        move_high = np.clip(current_delta, -float(config["shrink_cap"]), float(config["shrink_cap"])) * 0.50
        move = np.where(high, move_high, np.where(low, move_low, 0.0))
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
            BASELINE: frame[BASELINE].to_numpy(dtype=float),
            REFERENCE: frame[REFERENCE].to_numpy(dtype=float),
            PPV8: frame[PPV8].to_numpy(dtype=float),
            SVC: frame[SVC].to_numpy(dtype=float),
            "l10_seq_pred_log": frame["l10_seq_pred_log"].to_numpy(dtype=float),
            "quantile_width": frame["quantile_width"].to_numpy(dtype=float),
            "l10_price_range_ratio": frame["l10_price_range_ratio"].to_numpy(dtype=float),
            "qwidth_band": frame["qwidth_band"].astype(str).to_numpy(),
            "pred_spread": frame["pred_spread"].to_numpy(dtype=float),
            "pred_spread_band": frame["pred_spread_band"].astype(str).to_numpy(),
            "policy_applied": mask.astype(int),
            "policy_move_log": np.where(mask, move, 0.0),
            "abs_ppv8_stable_gap": frame["abs_ppv8_stable_gap"].to_numpy(dtype=float),
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
            "svc_group_n_band": frame["svc_group_n_band"].astype(str).to_numpy(),
            "gap_band": frame["gap_band"].astype(str).to_numpy(),
            "ppv8_direction": frame["ppv8_direction"].astype(str).to_numpy(),
        }
    )
    optional = ["title", "medium_support_bucket", "width_cm", "height_cm", "area_cm2", "log_area", "service_confidence_tier"]
    for col in optional:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def policy_row(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate": config["candidate"],
        "method": config["method"],
        "policy_type": config.get("policy_type", config["method"]),
        "source_col": config.get("source_col", ""),
        "qwidth_threshold_name": config.get("qwidth_threshold_name", ""),
        "qwidth_threshold": config.get("qwidth_threshold", np.nan),
        "spread_threshold": config.get("spread_threshold", np.nan),
        "gap": config.get("gap", np.nan),
        "cap": config.get("cap", np.nan),
        "weight": config.get("weight", np.nan),
        "shrink_cap": config.get("shrink_cap", np.nan),
        "ppv8_cap": config.get("ppv8_cap", np.nan),
        "description": config.get("description", ""),
    }


def coefficient_proxy(policy_map: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
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
                    "feature": "quantile_width",
                    "coefficient_or_policy_role": "risk gate",
                    "direction": "폭이 낮으면 신뢰 구간, 높으면 위험 구간으로 해석",
                    "value": row.get("qwidth_threshold", np.nan),
                    "description": "validation quantile_width 분포에서만 만든 경계값",
                },
                {
                    "candidate": candidate,
                    "feature": "current_minus_stable",
                    "coefficient_or_policy_role": "shrink movement",
                    "direction": "위험 구간에서는 HCOEF 보정폭을 current_70_30 방향으로 줄임",
                    "value": row.get("cap", row.get("shrink_cap", np.nan)),
                    "description": "큰 오차 위험 구간에서 Huber 잔차 보정의 과한 움직임을 축소",
                },
                {
                    "candidate": candidate,
                    "feature": "ppv8_minus_stable",
                    "coefficient_or_policy_role": "bounded movement",
                    "direction": "low risk 구간에서는 PP-V8 방향으로 제한 이동",
                    "value": row.get("weight", np.nan),
                    "description": "PP-V8이 0604에서 강했던 신호를 validation risk gate로만 제한 사용",
                },
            ]
        )
    return pd.DataFrame(rows)


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
                            (
                                (arr[:, 0] < 0).astype(int)
                                + (arr[:, 1] < 0).astype(int)
                                + (arr[:, 2] < 0).astype(int)
                                >= 2
                            ).mean()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def candidate_selection(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    stress = metrics_df[metrics_df["split"].eq("0604_ex50")].copy()
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
    stress_small = stress[["candidate", "MdAPE", "MAPE", "p95_APE"]].rename(
        columns={"MdAPE": "stress0604_MdAPE", "MAPE": "stress0604_MAPE", "p95_APE": "stress0604_p95_APE"}
    )
    out = out.merge(test_small, on="candidate", how="left").merge(stress_small, on="candidate", how="left").merge(b_val, on="candidate", how="left")
    out["validation_pass_2of3"] = (
        (out["delta_MdAPE_vs_stable"] < 0).astype(int)
        + (out["delta_MAPE_vs_stable"] < 0).astype(int)
        + (out["delta_p95_APE_vs_stable"] < 0).astype(int)
        >= 2
    )
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= 0.8064
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= 0.9835
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
        out["bootstrap_gate"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"] & out["stress0604_p95_guard"],
        out["validation_pass_2of3"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"],
        out["validation_pass_2of3"],
    ]
    choices = ["운영 후보 검토", "fixed test 확인 후보", "validation 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    return out.sort_values(["decision", "validation_MdAPE", "validation_MAPE", "validation_p95_APE"])


def segment_summary(predictions: pd.DataFrame, selected_candidates: list[str]) -> pd.DataFrame:
    focus = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    segment_cols = ["qwidth_band", "pred_spread_band", "svc_coverage_tier", "svc_group_level", "svc_group_n_band", "gap_band", "ppv8_direction"]
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


def quantile_audit(frames: dict[str, pd.DataFrame], thresholds: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, frame in frames.items():
        for band, group in frame.groupby("qwidth_band", dropna=False):
            if len(group) < 5:
                continue
            for candidate, col in [(BASELINE, BASELINE), (REFERENCE, REFERENCE), (PPV8, PPV8), ("l10_seq_full_generated_bucket", "l10_seq_pred_log")]:
                pred = group[col].to_numpy(dtype=float)
                m = metric(group, pred)
                rows.append(
                    {
                        "split": split,
                        "qwidth_band": band,
                        "candidate": candidate,
                        "n": len(group),
                        "quantile_width_median": float(group["quantile_width"].median()),
                        **m,
                    }
                )
    audit = pd.DataFrame(rows)
    audit["threshold_q33"] = thresholds["qwidth_q33"]
    audit["threshold_q66"] = thresholds["qwidth_q66"]
    audit["threshold_q80"] = thresholds["qwidth_q80"]
    return audit


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


def render_report(
    metrics_df: pd.DataFrame,
    selection: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    policy_map: pd.DataFrame,
    quantile_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    thresholds: dict[str, float],
) -> str:
    validation_top = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    stress_top = metrics_df[metrics_df["split"].eq("0604_ex50")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    selected_top = selection.sort_values(["decision", "validation_MdAPE", "test_MdAPE"]).head(25)
    boot_focus = bootstrap_df[
        bootstrap_df["candidate"].isin(selected_top["candidate"].tolist() + [BASELINE, PPV8, REFERENCE, "l10_seq_full_generated_bucket"])
    ].copy()
    return "\n".join(
        [
            "# PP-HCOEF18 Warm quantile-risk guarded refinement",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF 안정 후보를 기본값으로 유지하면서 quantile width 위험도에 따라 보정폭 축소 또는 PP-V8 제한 이동이 가능한지 검증",
            "- 기준 후보: `hcoef2_size_reliability_cap005_s050`",
            "- 선택 기준: validation과 bootstrap 우선, fixed test와 0604는 확인용",
            "- 금지 기준: test/0604 residual을 보고 threshold, weight, cap을 만들지 않음",
            "",
            "## 1. validation에서 고정한 quantile width 경계",
            "",
            markdown_table(pd.DataFrame([thresholds]).round(4), 5),
            "",
            "## 2. 실행 결론",
            "",
            "- PP-L10 quantile width는 validation/test/0604에 공통으로 붙일 수 있었음.",
            "- 이 실험은 quantile width를 가격 예측값 자체로 쓰기보다 HCOEF 보정폭을 줄이는 risk gate로 사용함.",
            "- low quantile width 구간에서는 PP-V8 방향 제한 이동 후보를 비교함.",
            "- high quantile width 또는 모델 간 spread가 큰 구간에서는 HCOEF 잔차 보정폭을 `current_70_30` 방향으로 줄이는 후보를 비교함.",
            "- 후보 채택은 validation/OOF성 bootstrap gate와 fixed test p95 guard를 동시에 봄.",
            "",
            "## 3. validation 상위 후보",
            "",
            markdown_table(
                validation_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "policy_apply_rate",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 4. fixed test 상위 후보",
            "",
            markdown_table(
                test_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "policy_apply_rate",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 5. 0604 stress test 상위 후보",
            "",
            markdown_table(
                stress_top[
                    [
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                        "policy_apply_rate",
                    ]
                ].round(4),
                25,
            ),
            "",
            "## 6. 후보 선택표",
            "",
            markdown_table(selected_top.round(4), 25),
            "",
            "## 7. bootstrap 요약",
            "",
            markdown_table(boot_focus.sort_values(["split", "validation_scheme", "all3_improve_prob"], ascending=[True, True, False]).round(4), 45),
            "",
            "## 8. quantile width 구간별 후보 성능",
            "",
            markdown_table(quantile_df.sort_values(["split", "qwidth_band", "MdAPE"]).round(4), 60),
            "",
            "## 9. 구간별 오차 요약",
            "",
            markdown_table(segment_df.head(60).round(4), 60),
            "",
            "## 10. 정책/계수 해석",
            "",
            markdown_table(policy_map.head(60).round(4), 60),
            "",
            "## 11. 해석",
            "",
            "- `quantile_width`는 q90 로그 예측과 q10 로그 예측의 차이로, 값이 클수록 모델이 가격 범위를 넓게 본다는 뜻임.",
            "- Huber는 기본적으로 로그 가격을 선형 결합으로 예측하므로, HCOEF 보정폭이 위험 구간에서 과하게 작동하면 `current_70_30` 방향으로 줄이는 정책이 해석 가능함.",
            "- low quantile width는 quantile 모델이 상대적으로 좁은 가격 범위를 본 구간이므로, PP-V8 이동을 허용해도 되는지 확인하는 gate로 사용함.",
            "- high quantile width 또는 모델 간 spread가 큰 구간은 예측 불확실성이 큰 구간이므로, 점 예측을 공격적으로 움직이기보다 보정폭 축소 또는 신뢰도/범위 정책 후보로 보는 것이 맞음.",
            "",
            "## 12. 산출물",
            "",
            "- `artifacts/experiment_config.json`",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/policy_map.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/quantile_feature_audit.csv`",
            "- `outputs/error_segment_summary.csv`",
            "- `outputs/selected_candidates.csv`",
        ]
    )


def main() -> None:
    ensure_dirs()
    frames, thresholds = load_frames()
    configs = build_policy_configs(thresholds)
    metrics_df, predictions, residuals, policy_map = fixed_confirmation(frames, configs)
    bootstrap_df = bootstrap_summary(frames, configs)
    selection = candidate_selection(metrics_df, bootstrap_df)
    feature_coefficients = coefficient_proxy(policy_map)
    quantile_df = quantile_audit(frames, thresholds)
    selected_candidates = selection.head(8)["candidate"].tolist()
    segment_candidates = list(dict.fromkeys([BASELINE, PPV8, REFERENCE, "l10_seq_full_generated_bucket", *selected_candidates]))
    segment_df = segment_summary(predictions, segment_candidates)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    feature_coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    policy_map.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    quantile_df.to_csv(EXP_DIR / "outputs" / "quantile_feature_audit.csv", index=False)
    segment_df.to_csv(EXP_DIR / "outputs" / "error_segment_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Quantile-risk guarded refinement over Warm HCOEF stable candidate",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "ppv8_component": PPV8,
        "l10_candidate": L10_CANDIDATE,
        "n_bootstrap": N_BOOTSTRAP,
        "threshold_source": "validation quantile_width and validation prediction spread only",
        "thresholds": thresholds,
        "inputs": {
            "hcoef17_predictions": str(HCOEF17_PREDICTIONS.relative_to(REPO)),
            "pp_l10_predictions": str(PP_L10_PREDICTIONS.relative_to(REPO)),
            "operational_0604": str(OPERATIONAL_0604.relative_to(REPO)),
        },
        "candidate_count": len(configs),
        "candidates": configs,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_report(metrics_df, selection, bootstrap_df, policy_map, quantile_df, segment_df, thresholds)
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(report), encoding="utf-8")

    doc_summary = DOC_ROOT / "pp_hcoef18_warm_huber_price_basis_coefficient_refinement_summary.md"
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
