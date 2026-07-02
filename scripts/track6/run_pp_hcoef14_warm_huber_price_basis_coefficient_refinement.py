#!/usr/bin/env python3
"""Run PP-HCOEF14: risk-segment shrinkage/routing OOF for Warm Huber.

HCOEF13 identified the remaining risk segments for the stable Warm Huber
candidate. This experiment turns those findings into small, interpretable
candidate policies and validates them with row/artist OOF before looking at
fixed test:

- route selected risk segments back toward the v0.1 70:30 reference,
- shrink the Huber residual correction only in low-confidence segments,
- apply tiny segment-median residual corrections only within HCOEF13 risk masks.

Fixed test and 0604 are confirmation only. Candidate selection is driven by
validation OOF.
"""
from __future__ import annotations

import html
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402
import run_pp_hcoef13_warm_huber_price_basis_coefficient_refinement as hcoef13  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF14"
EXP_SLUG = "PP-HCOEF14_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef5.REFERENCE
STABLE = hcoef5.STABLE
FEATURES = hcoef13.FEATURES
N_FOLDS = 5
N_REPEATS = 20
SEED = 20260608


@dataclass(frozen=True)
class CandidateConfig:
    candidate: str
    method: str
    risk_mask: str
    route_weight: float = 0.0
    keep_weight: float = 1.0
    keys: tuple[str, ...] = ()
    min_n: int = 20
    cap: float = 0.02
    strength: float = 0.25
    purpose: str = ""


CANDIDATES: list[CandidateConfig] = [
    CandidateConfig("hcoef14_route_ppv8_pos_ref_w025", "route_reference", "ppv8_pos", route_weight=0.25, purpose="ppv8 gap 양수 구간을 70:30 기준으로 일부 되돌림"),
    CandidateConfig("hcoef14_route_ppv8_pos_ref_w050", "route_reference", "ppv8_pos", route_weight=0.50, purpose="ppv8 gap 양수 구간을 70:30 기준으로 절반 되돌림"),
    CandidateConfig("hcoef14_route_basis_disagree_ref_w025", "route_reference", "basis_disagreement", route_weight=0.25, purpose="기준가와 현재 후보 불일치 구간 보수 routing"),
    CandidateConfig("hcoef14_route_basis_disagree_ref_w050", "route_reference", "basis_disagreement", route_weight=0.50, purpose="기준가와 현재 후보 불일치 구간 강한 보수 routing"),
    CandidateConfig("hcoef14_route_artist_overall_ref_w025", "route_reference", "artist_overall", route_weight=0.25, purpose="작가 전체 fallback 구간 일부 보수 routing"),
    CandidateConfig("hcoef14_route_artist_overall_ref_w050", "route_reference", "artist_overall", route_weight=0.50, purpose="작가 전체 fallback 구간 절반 보수 routing"),
    CandidateConfig("hcoef14_route_core_gap_ref_w025", "route_reference", "core_gap_risk", route_weight=0.25, purpose="후보 gap 위험 구간 보수 routing"),
    CandidateConfig("hcoef14_route_core_gap_ref_w050", "route_reference", "core_gap_risk", route_weight=0.50, purpose="후보 gap 위험 구간 강한 보수 routing"),
    CandidateConfig("hcoef14_shrink_n1019_keep050", "shrink_hcoef", "n_10_19", keep_weight=0.50, purpose="표본 수 10~19 구간 Huber 잔차 보정 절반 축소"),
    CandidateConfig("hcoef14_shrink_n1019_keep075", "shrink_hcoef", "n_10_19", keep_weight=0.75, purpose="표본 수 10~19 구간 Huber 잔차 보정 약한 축소"),
    CandidateConfig("hcoef14_shrink_iqr_mid_high_keep050", "shrink_hcoef", "iqr_mid_high", keep_weight=0.50, purpose="IQR 중간/높음 구간 Huber 잔차 보정 절반 축소"),
    CandidateConfig("hcoef14_shrink_iqr_mid_high_keep075", "shrink_hcoef", "iqr_mid_high", keep_weight=0.75, purpose="IQR 중간/높음 구간 Huber 잔차 보정 약한 축소"),
    CandidateConfig("hcoef14_shrink_core_risk_keep050", "shrink_hcoef", "core_risk", keep_weight=0.50, purpose="HCOEF13 핵심 위험 구간 Huber 잔차 보정 절반 축소"),
    CandidateConfig("hcoef14_shrink_core_risk_keep075", "shrink_hcoef", "core_risk", keep_weight=0.75, purpose="HCOEF13 핵심 위험 구간 Huber 잔차 보정 약한 축소"),
    CandidateConfig("hcoef14_seg_n1019_cap002_s025", "segment_residual", "n_10_19", keys=("basis_n_bucket",), min_n=20, cap=0.02, strength=0.25, purpose="표본 수 10~19 구간 segment median residual 보정"),
    CandidateConfig("hcoef14_seg_n1019_cap002_s050", "segment_residual", "n_10_19", keys=("basis_n_bucket",), min_n=20, cap=0.02, strength=0.50, purpose="표본 수 10~19 구간 segment median residual 보정 강화"),
    CandidateConfig("hcoef14_seg_iqr_cap002_s025", "segment_residual", "iqr_mid_high", keys=("basis_iqr_bucket",), min_n=20, cap=0.02, strength=0.25, purpose="IQR 위험 구간 segment median residual 보정"),
    CandidateConfig("hcoef14_seg_gap_cap002_s025", "segment_residual", "core_gap_risk", keys=("ppv8_gap_sign", "basis_gap_sign"), min_n=15, cap=0.02, strength=0.25, purpose="후보 gap 구간 segment median residual 보정"),
    CandidateConfig("hcoef14_seg_pred_basis_cap002_s025", "segment_residual", "n_10_19", keys=("pred_bin", "basis_n_bucket"), min_n=12, cap=0.02, strength=0.25, purpose="예측 가격대 x 표본 수 구간 residual 보정"),
    CandidateConfig("hcoef14_seg_size_basis_cap002_s025", "segment_residual", "n_10_19", keys=("size_bin", "basis_n_bucket"), min_n=12, cap=0.02, strength=0.25, purpose="크기 x 표본 수 구간 residual 보정"),
    CandidateConfig("hcoef14_seg_core_risk_cap002_s025", "segment_residual", "core_risk", keys=("risk_cause",), min_n=20, cap=0.02, strength=0.25, purpose="HCOEF13 핵심 위험 cause별 residual 보정"),
    CandidateConfig("hcoef14_seg_core_risk_cap003_s025", "segment_residual", "core_risk", keys=("risk_cause",), min_n=20, cap=0.03, strength=0.25, purpose="HCOEF13 핵심 위험 cause별 residual 보정 cap 확대"),
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef5.metric_from_frame(frame, np.asarray(pred_log, dtype=float))


def stable_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    return hcoef5.hcoef2_prediction(train, eval_frame)


def add_segments(train: pd.DataFrame, eval_frame: pd.DataFrame, train_stable: np.ndarray, eval_stable: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    edges = hcoef13.actual_bin_edges(train)
    train_enriched = hcoef13.enrich_split(train, train, train_stable, train_stable, edges)
    eval_enriched = hcoef13.enrich_split(train, eval_frame, train_stable, eval_stable, edges)
    return train_enriched, eval_enriched


def risk_mask(frame: pd.DataFrame, mask_name: str) -> np.ndarray:
    if mask_name == "ppv8_pos":
        mask = frame["ppv8_gap_sign"].eq("ppv8_pos")
    elif mask_name == "basis_disagreement":
        mask = frame["risk_cause"].eq("basis_current_disagreement")
    elif mask_name == "artist_overall":
        mask = frame["basis_level_simple"].eq("artist_overall")
    elif mask_name == "n_10_19":
        mask = frame["basis_n_bucket"].eq("n_10_19")
    elif mask_name == "iqr_mid_high":
        mask = frame["basis_iqr_bucket"].isin(["iqr_mid", "iqr_high"])
    elif mask_name == "core_gap_risk":
        mask = frame["ppv8_gap_sign"].eq("ppv8_pos") | frame["risk_cause"].eq("basis_current_disagreement")
    elif mask_name == "core_risk":
        mask = (
            frame["basis_n_bucket"].eq("n_10_19")
            | frame["basis_iqr_bucket"].isin(["iqr_mid", "iqr_high"])
            | frame["ppv8_gap_sign"].eq("ppv8_pos")
            | frame["risk_cause"].eq("basis_current_disagreement")
            | frame["basis_level_simple"].eq("artist_overall")
        )
    else:
        raise ValueError(f"Unknown risk mask: {mask_name}")
    return mask.fillna(False).to_numpy(dtype=bool)


def group_labels(frame: pd.DataFrame, keys: tuple[str, ...]) -> pd.Series:
    if len(keys) == 1:
        return frame[keys[0]].astype(str)
    return frame[list(keys)].astype(str).agg(" + ".join, axis=1)


def fit_segment_map(
    train: pd.DataFrame,
    train_stable: np.ndarray,
    config: CandidateConfig,
) -> dict[str, dict[str, Any]]:
    mask = risk_mask(train, config.risk_mask)
    if not mask.any():
        return {}
    residual = train["actual_log"].to_numpy(dtype=float) - np.asarray(train_stable, dtype=float)
    labels = group_labels(train, config.keys)
    work = pd.DataFrame({"label": labels, "residual": residual, "mask": mask})
    out: dict[str, dict[str, Any]] = {}
    for label, group in work[work["mask"]].groupby("label", observed=False):
        if len(group) < config.min_n:
            continue
        raw = float(np.median(group["residual"].to_numpy(dtype=float)))
        correction = float(np.clip(raw, -config.cap, config.cap) * config.strength)
        out[str(label)] = {
            "raw_median_residual_log": raw,
            "correction_log": correction,
            "n": int(len(group)),
        }
    return out


def apply_candidate(
    config: CandidateConfig,
    train: pd.DataFrame,
    eval_frame: pd.DataFrame,
    train_stable: np.ndarray,
    eval_reference: np.ndarray,
    eval_stable: np.ndarray,
) -> tuple[np.ndarray, pd.DataFrame]:
    pred = np.asarray(eval_stable, dtype=float).copy()
    mask = risk_mask(eval_frame, config.risk_mask)
    rows: list[dict[str, Any]] = []

    if config.method == "route_reference":
        pred[mask] = eval_stable[mask] + config.route_weight * (eval_reference[mask] - eval_stable[mask])
        rows.append(
            {
                "candidate": config.candidate,
                "method": config.method,
                "risk_mask": config.risk_mask,
                "segment_label": config.risk_mask,
                "matched_n": int(mask.sum()),
                "correction_log": np.nan,
                "route_weight": config.route_weight,
                "keep_weight": np.nan,
            }
        )
    elif config.method == "shrink_hcoef":
        pred[mask] = eval_reference[mask] + config.keep_weight * (eval_stable[mask] - eval_reference[mask])
        rows.append(
            {
                "candidate": config.candidate,
                "method": config.method,
                "risk_mask": config.risk_mask,
                "segment_label": config.risk_mask,
                "matched_n": int(mask.sum()),
                "correction_log": np.nan,
                "route_weight": np.nan,
                "keep_weight": config.keep_weight,
            }
        )
    elif config.method == "segment_residual":
        segment_map = fit_segment_map(train, train_stable, config)
        labels = group_labels(eval_frame, config.keys)
        applied = np.zeros(len(eval_frame), dtype=bool)
        for label, info in segment_map.items():
            label_mask = (labels.astype(str).to_numpy() == label) & mask
            if not label_mask.any():
                continue
            pred[label_mask] = pred[label_mask] + float(info["correction_log"])
            applied |= label_mask
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "risk_mask": config.risk_mask,
                    "segment_label": label,
                    "matched_n": int(label_mask.sum()),
                    "train_segment_n": int(info["n"]),
                    "raw_median_residual_log": float(info["raw_median_residual_log"]),
                    "correction_log": float(info["correction_log"]),
                    "cap": config.cap,
                    "strength": config.strength,
                    "min_n": config.min_n,
                }
            )
        if not rows:
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "risk_mask": config.risk_mask,
                    "segment_label": "__NO_MATCH__",
                    "matched_n": 0,
                    "correction_log": 0.0,
                    "cap": config.cap,
                    "strength": config.strength,
                    "min_n": config.min_n,
                }
            )
    else:
        raise ValueError(f"Unknown method: {config.method}")

    return pred, pd.DataFrame(rows)


def metric_row(
    scheme: str,
    repeat: int,
    candidate: str,
    frame: pd.DataFrame,
    pred: np.ndarray,
    stable_pred: np.ndarray,
    reference_pred: np.ndarray,
    split: str = "validation",
    method: str = "",
) -> dict[str, Any]:
    metric = metric_from_frame(frame, pred)
    stable_metric = metric_from_frame(frame, stable_pred)
    reference_metric = metric_from_frame(frame, reference_pred)
    return {
        "validation_scheme": scheme,
        "repeat": repeat,
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": len(frame),
        **metric,
        "delta_MdAPE_vs_stable": metric["MdAPE"] - stable_metric["MdAPE"],
        "delta_MAPE_vs_stable": metric["MAPE"] - stable_metric["MAPE"],
        "delta_p95_APE_vs_stable": metric["p95_APE"] - stable_metric["p95_APE"],
        "delta_RMSE_log_vs_stable": metric["RMSE_log"] - stable_metric["RMSE_log"],
        "delta_MdAPE_vs_reference": metric["MdAPE"] - reference_metric["MdAPE"],
        "delta_MAPE_vs_reference": metric["MAPE"] - reference_metric["MAPE"],
        "delta_p95_APE_vs_reference": metric["p95_APE"] - reference_metric["p95_APE"],
        "delta_RMSE_log_vs_reference": metric["RMSE_log"] - reference_metric["RMSE_log"],
        "improve_count_vs_stable": int(metric["MdAPE"] < stable_metric["MdAPE"])
        + int(metric["MAPE"] < stable_metric["MAPE"])
        + int(metric["p95_APE"] < stable_metric["p95_APE"]),
        "improve_count_vs_reference": int(metric["MdAPE"] < reference_metric["MdAPE"])
        + int(metric["MAPE"] < reference_metric["MAPE"])
        + int(metric["p95_APE"] < reference_metric["p95_APE"]),
    }


def prediction_frame(
    frame: pd.DataFrame,
    candidate: str,
    split: str,
    pred_log: np.ndarray,
    method: str,
) -> pd.DataFrame:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
            "ape": np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None),
        }
    )
    for col in ["risk_cause", "pred_bin", "size_bin", "basis_n_bucket", "basis_iqr_bucket", "basis_level_simple", "basis_gap_sign", "ppv8_gap_sign"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    return out


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    applied_rows: list[pd.DataFrame] = []

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = hcoef5.row_folds(len(validation), seed) if scheme == "row_oof" else hcoef5.artist_folds(validation, seed)
            stable_oof = np.full(len(validation), np.nan, dtype=float)
            candidate_oof = {config.candidate: np.full(len(validation), np.nan, dtype=float) for config in CANDIDATES}
            enriched_oof_parts: list[pd.DataFrame] = []

            for fold_id, (train_idx, hold_idx) in enumerate(folds):
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                train_stable, _ = stable_prediction(train, train)
                hold_stable, _ = stable_prediction(train, hold)
                train_enriched, hold_enriched = add_segments(train, hold, train_stable, hold_stable)
                reference_pred = hold_enriched[REFERENCE].to_numpy(dtype=float)
                stable_oof[hold_idx] = hold_stable

                hold_enriched = hold_enriched.copy()
                hold_enriched["_oof_row_pos"] = hold_idx
                enriched_oof_parts.append(hold_enriched)

                for config in CANDIDATES:
                    pred, applied = apply_candidate(config, train_enriched, hold_enriched, train_stable, reference_pred, hold_stable)
                    candidate_oof[config.candidate][hold_idx] = pred
                    if not applied.empty:
                        applied = applied.copy()
                        applied["validation_scheme"] = scheme
                        applied["repeat"] = repeat
                        applied["fold"] = fold_id
                        applied["split"] = "validation_oof"
                        applied_rows.append(applied)

            enriched_validation = pd.concat(enriched_oof_parts, ignore_index=True).sort_values("_oof_row_pos")
            reference_full = validation[REFERENCE].to_numpy(dtype=float)
            metric_rows.append(
                metric_row(
                    scheme,
                    repeat,
                    STABLE,
                    validation,
                    stable_oof,
                    stable_oof,
                    reference_full,
                    method="stable_oof_anchor",
                )
            )
            for config in CANDIDATES:
                pred = candidate_oof[config.candidate]
                metric_rows.append(
                    metric_row(
                        scheme,
                        repeat,
                        config.candidate,
                        validation,
                        pred,
                        stable_oof,
                        reference_full,
                        method=config.method,
                    )
                )
                if repeat == 0:
                    pred_rows.append(
                        prediction_frame(enriched_validation, config.candidate, f"validation_{scheme}_repeat0", pred, config.method)
                    )
            if repeat == 0:
                pred_rows.append(prediction_frame(enriched_validation, STABLE, f"validation_{scheme}_repeat0", stable_oof, "stable_oof_anchor"))

    return (
        pd.DataFrame(metric_rows),
        pd.concat(pred_rows, ignore_index=True, sort=False),
        pd.concat(applied_rows, ignore_index=True, sort=False) if applied_rows else pd.DataFrame(),
    )


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    validation_stable, stable_model = stable_prediction(validation, validation)
    train_enriched, _ = add_segments(validation, validation, validation_stable, validation_stable)
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    applied_rows: list[pd.DataFrame] = []
    segment_map_rows: list[pd.DataFrame] = []

    for split in ["validation", "test", "0604_ex50"]:
        frame = frames[split]
        stable_pred, _ = stable_prediction(validation, frame)
        _, enriched = add_segments(validation, frame, validation_stable, stable_pred)
        reference_pred = enriched[REFERENCE].to_numpy(dtype=float)

        metric_rows.append(
            metric_row("fixed_confirmation", -1, REFERENCE, enriched, reference_pred, stable_pred, reference_pred, split, "reference_70_30")
        )
        metric_rows.append(
            metric_row("fixed_confirmation", -1, STABLE, enriched, stable_pred, stable_pred, reference_pred, split, "stable_huber_residual")
        )
        pred_rows.append(prediction_frame(enriched, REFERENCE, split, reference_pred, "reference_70_30"))
        pred_rows.append(prediction_frame(enriched, STABLE, split, stable_pred, "stable_huber_residual"))

        for config in CANDIDATES:
            pred, applied = apply_candidate(config, train_enriched, enriched, validation_stable, reference_pred, stable_pred)
            metric_rows.append(metric_row("fixed_confirmation", -1, config.candidate, enriched, pred, stable_pred, reference_pred, split, config.method))
            pred_rows.append(prediction_frame(enriched, config.candidate, split, pred, config.method))
            if not applied.empty:
                applied = applied.copy()
                applied["validation_scheme"] = "fixed_confirmation"
                applied["repeat"] = -1
                applied["fold"] = -1
                applied["split"] = split
                applied_rows.append(applied)
                if config.method == "segment_residual" and split == "test":
                    segment_map_rows.append(applied.copy())

    coeffs = feature_coefficients(stable_model)
    return (
        pd.DataFrame(metric_rows),
        pd.concat(pred_rows, ignore_index=True, sort=False),
        coeffs,
        pd.concat(applied_rows, ignore_index=True, sort=False) if applied_rows else pd.DataFrame(),
        pd.concat(segment_map_rows, ignore_index=True, sort=False) if segment_map_rows else pd.DataFrame(),
    )


def feature_coefficients(model: Any) -> pd.DataFrame:
    reg = model.named_steps["model"]
    coefs = getattr(reg, "coef_", np.full(len(FEATURES), np.nan))
    rows: list[dict[str, Any]] = []
    for feature, coef in zip(FEATURES, coefs):
        rows.append(
            {
                "candidate": STABLE,
                "method": "stable_huber_residual",
                "feature": feature,
                "coefficient_on_scaled_feature": float(coef),
                "abs_coefficient": float(abs(coef)),
                "direction": "가격 보정값을 올리는 방향" if coef > 0 else "가격 보정값을 낮추는 방향" if coef < 0 else "영향 거의 없음",
            }
        )
    for config in CANDIDATES:
        rows.append(
            {
                "candidate": config.candidate,
                "method": config.method,
                "feature": config.risk_mask if not config.keys else "+".join(config.keys),
                "coefficient_on_scaled_feature": np.nan,
                "abs_coefficient": np.nan,
                "direction": config.purpose,
                "route_weight": config.route_weight,
                "keep_weight": config.keep_weight,
                "cap": config.cap,
                "strength": config.strength,
                "min_n": config.min_n,
            }
        )
    return pd.DataFrame(rows)


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        residual = group["residual_log"].to_numpy(dtype=float)
        ape = group["ape"].to_numpy(dtype=float)
        actual = group["actual_price"].to_numpy(dtype=float)
        pred = group["pred_price"].to_numpy(dtype=float)
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": len(group),
                "median_residual_log": float(np.median(residual)),
                "mean_residual_log": float(np.mean(residual)),
                "residual_std": float(np.std(residual)),
                "ape_median": float(np.median(ape)),
                "ape_mean": float(np.mean(ape)),
                "ape_p95": float(np.quantile(ape, 0.95)),
                "ape_gt_50pct_n": int((ape > 0.5).sum()),
                "ape_gt_100pct_n": int((ape > 1.0).sum()),
                "over_2x_n": int((pred >= actual * 2.0).sum()),
                "under_half_n": int((pred <= actual * 0.5).sum()),
            }
        )
    return pd.DataFrame(rows)


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics[metrics["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows: list[dict[str, Any]] = []
    for (scheme, candidate), group in repeated.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "summary_type": "repeated_oof",
                "validation_scheme": scheme,
                "split": "validation",
                "candidate": candidate,
                "method": str(group["method"].iloc[0]),
                "n_repeats": len(group),
                "mean_delta_MdAPE_vs_stable": float(group["delta_MdAPE_vs_stable"].mean()),
                "mean_delta_MAPE_vs_stable": float(group["delta_MAPE_vs_stable"].mean()),
                "mean_delta_p95_APE_vs_stable": float(group["delta_p95_APE_vs_stable"].mean()),
                "mean_delta_RMSE_log_vs_stable": float(group["delta_RMSE_log_vs_stable"].mean()),
                "MdAPE_improve_prob_vs_stable": float((group["delta_MdAPE_vs_stable"] < 0).mean()),
                "MAPE_improve_prob_vs_stable": float((group["delta_MAPE_vs_stable"] < 0).mean()),
                "p95_improve_prob_vs_stable": float((group["delta_p95_APE_vs_stable"] < 0).mean()),
                "all3_improve_prob_vs_stable": float((group["improve_count_vs_stable"] == 3).mean()),
                "mean_delta_MdAPE_vs_reference": float(group["delta_MdAPE_vs_reference"].mean()),
                "mean_delta_MAPE_vs_reference": float(group["delta_MAPE_vs_reference"].mean()),
                "mean_delta_p95_APE_vs_reference": float(group["delta_p95_APE_vs_reference"].mean()),
                "all3_improve_prob_vs_reference": float((group["improve_count_vs_reference"] == 3).mean()),
                "mean_improve_count_vs_stable": float(group["improve_count_vs_stable"].mean()),
            }
        )
    return pd.DataFrame(rows)


def select_candidates(summary: pd.DataFrame, fixed_metrics: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    pivot = summary.pivot_table(
        index=["candidate", "method"],
        columns="validation_scheme",
        values=[
            "mean_delta_MdAPE_vs_stable",
            "mean_delta_MAPE_vs_stable",
            "mean_delta_p95_APE_vs_stable",
            "all3_improve_prob_vs_stable",
            "all3_improve_prob_vs_reference",
        ],
        aggfunc="first",
    )
    pivot.columns = [f"{metric}_{scheme}" for metric, scheme in pivot.columns]
    selected = pivot.reset_index()
    fixed_test = fixed_metrics[fixed_metrics["split"].eq("test")][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "improve_count_vs_stable"]
    ].copy()
    fixed_test = fixed_test.add_prefix("test_").rename(columns={"test_candidate": "candidate"})
    selected = selected.merge(fixed_test, on="candidate", how="left")
    selected = selected[selected["candidate"].ne(STABLE)].copy()
    selected["passes_repeat_gate"] = (
        (selected.get("all3_improve_prob_vs_stable_row_oof", 0.0) >= 0.90)
        & (selected.get("all3_improve_prob_vs_stable_artist_oof", 0.0) >= 0.90)
    )
    selected["passes_fixed_guard"] = (
        (selected["test_delta_p95_APE_vs_stable"] <= 0.0)
        & (selected["test_improve_count_vs_stable"] >= 2)
    )
    selected["candidate_status"] = np.select(
        [
            selected["passes_repeat_gate"] & selected["passes_fixed_guard"],
            selected["passes_repeat_gate"],
            selected["test_improve_count_vs_stable"] >= 2,
        ],
        ["운영 후보 가능", "반복 검증 후보", "fixed 확인용 보류"],
        default="보류",
    )
    selected["rank_score"] = (
        selected.get("mean_delta_MdAPE_vs_stable_row_oof", 0.0).fillna(0.0)
        + selected.get("mean_delta_MAPE_vs_stable_row_oof", 0.0).fillna(0.0)
        + selected.get("mean_delta_p95_APE_vs_stable_row_oof", 0.0).fillna(0.0)
        + selected.get("mean_delta_MdAPE_vs_stable_artist_oof", 0.0).fillna(0.0)
        + selected.get("mean_delta_MAPE_vs_stable_artist_oof", 0.0).fillna(0.0)
        + selected.get("mean_delta_p95_APE_vs_stable_artist_oof", 0.0).fillna(0.0)
    )
    return selected.sort_values(["passes_repeat_gate", "passes_fixed_guard", "rank_score"], ascending=[False, False, True])


def applied_summary(applied: pd.DataFrame) -> pd.DataFrame:
    if applied.empty:
        return pd.DataFrame()
    group_cols = ["candidate", "method", "risk_mask", "split"]
    return (
        applied.groupby(group_cols, observed=False)
        .agg(
            applications=("matched_n", "sum"),
            map_rows=("segment_label", "count"),
            mean_correction_log=("correction_log", "mean"),
            max_abs_correction_log=("correction_log", lambda s: float(pd.to_numeric(s, errors="coerce").abs().max())),
        )
        .reset_index()
    )


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        if pd.isna(value):
            return ""
        return str(value)

    lines = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    summary: pd.DataFrame,
    fixed_metrics: pd.DataFrame,
    selection: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    applied: pd.DataFrame,
) -> None:
    fixed_test = fixed_metrics[fixed_metrics["split"].eq("test")].sort_values(["p95_APE", "MdAPE", "MAPE"]).copy()
    top_selection = selection.head(20).copy()
    best_status = "새 운영 후보 채택 없음"
    if not selection.empty and bool(selection.iloc[0]["passes_repeat_gate"]) and bool(selection.iloc[0]["passes_fixed_guard"]):
        best_status = f"운영 후보 가능: `{selection.iloc[0]['candidate']}`"
    elif not selection.empty and bool(selection.iloc[0]["passes_repeat_gate"]):
        best_status = f"반복 검증 후보: `{selection.iloc[0]['candidate']}`"

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 위험 구간 shrinkage/routing OOF 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF13에서 확인한 위험 구간에 한정해 보정 축소, 70:30 기준 routing, 작은 segment residual 보정을 검증.",
            f"- 기준 후보: `{STABLE}`.",
            f"- 비교 기준: `{REFERENCE}`.",
            f"- 반복 설정: row OOF {N_REPEATS}회, artist OOF {N_REPEATS}회, 각 {N_FOLDS} folds.",
            "- 후보 선택: 반복 OOF 우선. fixed test/0604는 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- 판단: {best_status}.",
            "- 현재 결과에서 반복 OOF gate와 fixed p95 guard를 동시에 통과하지 못하면 기본 후보로 채택하지 않는다.",
            "",
            "## 2. 후보 선택표",
            "",
            markdown_table(
                top_selection[
                    [
                        "candidate",
                        "method",
                        "candidate_status",
                        "passes_repeat_gate",
                        "passes_fixed_guard",
                        "all3_improve_prob_vs_stable_row_oof",
                        "all3_improve_prob_vs_stable_artist_oof",
                        "test_MdAPE",
                        "test_MAPE",
                        "test_p95_APE",
                        "test_delta_MdAPE_vs_stable",
                        "test_delta_MAPE_vs_stable",
                        "test_delta_p95_APE_vs_stable",
                    ]
                ].round(4)
                if not top_selection.empty
                else top_selection,
                max_rows=20,
            ),
            "",
            "## 3. 반복 OOF 요약",
            "",
            markdown_table(
                summary[
                    [
                        "validation_scheme",
                        "candidate",
                        "method",
                        "mean_delta_MdAPE_vs_stable",
                        "mean_delta_MAPE_vs_stable",
                        "mean_delta_p95_APE_vs_stable",
                        "MdAPE_improve_prob_vs_stable",
                        "MAPE_improve_prob_vs_stable",
                        "p95_improve_prob_vs_stable",
                        "all3_improve_prob_vs_stable",
                    ]
                ]
                .sort_values(["validation_scheme", "all3_improve_prob_vs_stable", "mean_delta_p95_APE_vs_stable"], ascending=[True, False, True])
                .round(4),
                max_rows=48,
            ),
            "",
            "## 4. Fixed test p95 상위 후보",
            "",
            markdown_table(
                fixed_test[
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
                        "improve_count_vs_stable",
                    ]
                ].round(4),
                max_rows=32,
            ),
            "",
            "## 5. 보정 적용 규모",
            "",
            markdown_table(applied_summary(applied).round(4), max_rows=40),
            "",
            "## 6. Huber 계수/정책 해석",
            "",
            "- 기존 Huber 잔차 보정 계수와 HCOEF14 정책 파라미터를 함께 기록한다.",
            "- route 후보는 위험 구간에서 현재 후보를 70:30 기준으로 일부 되돌리는 방식이다.",
            "- shrink 후보는 위험 구간에서 Huber 잔차 보정폭만 줄이는 방식이다.",
            "- segment residual 후보는 validation train fold에서 같은 위험 구간의 residual 중앙값만 아주 작게 반영한다.",
            markdown_table(coeffs.round(5), max_rows=42),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=42),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/segment_application_summary.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef14_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef14_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = hcoef5.build_frames()
    repeated_metrics, repeated_predictions, repeated_applied = repeated_oof(frames["validation"])
    fixed_metrics, fixed_predictions, coeffs, fixed_applied, segment_maps = fixed_confirmation(frames)
    metrics = pd.concat([repeated_metrics, fixed_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([repeated_predictions, fixed_predictions], ignore_index=True, sort=False)
    applied = pd.concat([repeated_applied, fixed_applied], ignore_index=True, sort=False)
    residuals = residual_analysis(predictions)
    summary = summarize_repeated(metrics)
    selection = select_candidates(summary, fixed_metrics)
    app_summary = applied_summary(applied)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)
    app_summary.to_csv(out / "segment_application_summary.csv", index=False)
    segment_maps.to_csv(out / "segment_correction_map.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "stable_candidate": STABLE,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "candidates": [config.__dict__ for config in CANDIDATES],
        "selection_policy": "OOF first. Fixed test and 0604 are confirmation only.",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, fixed_metrics, selection, coeffs, residuals, applied)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected candidates ---")
    print(selection.round(4).head(20).to_string(index=False))
    print("--- fixed test p95 top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["p95_APE", "MdAPE", "MAPE"])[
            [
                "candidate",
                "method",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable",
                "improve_count_vs_stable",
            ]
        ]
        .round(4)
        .head(24)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
