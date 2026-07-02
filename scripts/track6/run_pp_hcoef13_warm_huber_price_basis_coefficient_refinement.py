#!/usr/bin/env python3
"""Run PP-HCOEF13: residual risk diagnosis for the Warm Huber candidate.

HCOEF11/12 confirmed and packaged the stable residual Huber candidate
(`hcoef2_size_reliability_cap005_s050`). This experiment does not introduce a
new correction. It explains where the remaining errors come from so later
price-basis or coefficient-tuning experiments can be targeted without looking
at fixed test labels to choose rules.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef3_warm_huber_residual_repeated_validation as hcoef3  # noqa: E402
import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402
import run_pp_hcoef10_warm_huber_price_basis_coefficient_refinement as hcoef10  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF13"
EXP_SLUG = "PP-HCOEF13_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef5.REFERENCE
STABLE = hcoef5.STABLE
STABLE_CONFIG = next(item for item in hcoef3.CANDIDATES if item["candidate"] == STABLE)
FEATURES = hcoef5.hcoef1.RESIDUAL_FEATURE_SETS["resid_basis_size_reliability"]
SOURCE_HCOEF11 = REPO / "experiments" / "track6" / "PP-HCOEF11_warm_huber_price_basis_coefficient_refinement"


SEGMENT_KEYS = [
    ("risk_cause", ("risk_cause",), 20),
    ("pred_bin", ("pred_bin",), 20),
    ("size_bin", ("size_bin",), 20),
    ("basis_n_bucket", ("basis_n_bucket",), 15),
    ("basis_iqr_bucket", ("basis_iqr_bucket",), 15),
    ("basis_level_simple", ("basis_level_simple",), 15),
    ("basis_gap_sign", ("basis_gap_sign",), 15),
    ("ppv8_gap_sign", ("ppv8_gap_sign",), 15),
    ("medium_support_bucket", ("medium_support_bucket_clean",), 15),
    ("pred_x_basis_n", ("pred_bin", "basis_n_bucket"), 12),
    ("size_x_basis_n", ("size_bin", "basis_n_bucket"), 12),
    ("basis_level_x_gap", ("basis_level_simple", "basis_gap_sign"), 12),
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef5.metric_from_frame(frame, np.asarray(pred_log, dtype=float))


def metric_from_subset(frame: pd.DataFrame, pred_log: np.ndarray, idx: np.ndarray) -> dict[str, float]:
    return metric_from_frame(frame.iloc[idx], np.asarray(pred_log, dtype=float)[idx])


def stable_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    return hcoef5.hcoef2_prediction(train, eval_frame)


def actual_bin_edges(validation: pd.DataFrame) -> np.ndarray:
    values = validation["actual_log"].to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 4:
        return np.asarray([-np.inf, np.inf])
    edges = np.quantile(values, [0.0, 0.25, 0.50, 0.75, 1.0])
    edges[0] = -np.inf
    edges[-1] = np.inf
    return np.unique(edges)


def assign_actual_bin(frame: pd.DataFrame, edges: np.ndarray) -> np.ndarray:
    arr = frame["actual_log"].to_numpy(dtype=float)
    idx = np.searchsorted(edges, arr, side="right") - 1
    idx = np.clip(idx, 0, max(len(edges) - 2, 0))
    out = np.asarray([f"actual_diag_q{int(i) + 1}" for i in idx], dtype=object)
    out[~np.isfinite(arr)] = "actual_diag_missing"
    return out


def numeric_series(frame: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce")


def add_risk_diagnostics(frame: pd.DataFrame, actual_edges: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    basis_n = numeric_series(out, "basis_relaxed_n", 0.0).fillna(0.0)
    basis_iqr = numeric_series(out, "basis_relaxed_iqr", np.nan)
    basis_gap = numeric_series(out, "basis_relaxed_vs_current_gap", np.nan)
    svc_n = numeric_series(out, "svc_group_n", 0.0).fillna(0.0)
    svc_iqr = numeric_series(out, "svc_group_log_price_iqr", np.nan)
    area = numeric_series(out, "log_area", np.nan)
    pred_num = out["pred_bin"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    size_num = out["size_bin"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    medium_text = out["medium_support_bucket_clean"].astype(str)

    conditions = [
        basis_n < 5,
        basis_iqr > 1.00,
        basis_gap.abs() > 0.50,
        (pred_num >= 8) & (size_num >= 3),
        (pred_num <= 1) & (size_num <= 1),
        svc_n < 5,
        svc_iqr > 1.00,
        medium_text.str.contains("__MISSING__|other|unknown|nan", case=False, regex=True),
        area.isna(),
    ]
    choices = [
        "basis_low_sample",
        "basis_high_spread",
        "basis_current_disagreement",
        "high_price_large_size",
        "low_price_small_size",
        "svc_low_sample",
        "svc_high_spread",
        "medium_support_sparse_or_missing",
        "size_missing",
    ]
    out["risk_cause"] = np.select(conditions, choices, default="no_primary_risk").astype(object)
    out["actual_price_bin_diag_only"] = assign_actual_bin(out, actual_edges)
    out["basis_relaxed_n_num"] = basis_n.to_numpy(dtype=float)
    out["basis_relaxed_iqr_num"] = basis_iqr.to_numpy(dtype=float)
    out["basis_relaxed_vs_current_gap_num"] = basis_gap.to_numpy(dtype=float)
    out["svc_group_n_num"] = svc_n.to_numpy(dtype=float)
    out["svc_group_iqr_num"] = svc_iqr.to_numpy(dtype=float)
    return out


def enrich_split(
    validation: pd.DataFrame,
    frame: pd.DataFrame,
    validation_stable_pred: np.ndarray,
    frame_stable_pred: np.ndarray,
    actual_edges: np.ndarray,
) -> pd.DataFrame:
    _, enriched = hcoef10.add_segment_features(validation, frame, validation_stable_pred, frame_stable_pred)
    return add_risk_diagnostics(enriched.reset_index(drop=True), actual_edges)


def prediction_frame(
    frame: pd.DataFrame,
    candidate: str,
    split: str,
    pred_log: np.ndarray,
    method: str,
    reference_pred: np.ndarray,
    stable_pred: np.ndarray,
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
            "reference_pred_log": np.asarray(reference_pred, dtype=float),
            "stable_pred_log": np.asarray(stable_pred, dtype=float),
            "stable_minus_reference_log": np.asarray(stable_pred, dtype=float) - np.asarray(reference_pred, dtype=float),
        }
    )
    diag_cols = [
        "risk_cause",
        "pred_bin",
        "size_bin",
        "basis_n_bucket",
        "basis_iqr_bucket",
        "basis_level_simple",
        "basis_gap_sign",
        "ppv8_gap_sign",
        "medium_support_bucket_clean",
        "actual_price_bin_diag_only",
        "basis_relaxed_n_num",
        "basis_relaxed_iqr_num",
        "basis_relaxed_vs_current_gap_num",
        "basis_shrunk_weight",
        "svc_group_n_num",
        "svc_group_iqr_num",
        "svc_coverage_tier",
    ]
    for col in diag_cols:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    return out


def metric_rows(frames: dict[str, pd.DataFrame], stable_predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, frame in frames.items():
        ref_pred = frame[REFERENCE].to_numpy(dtype=float)
        ref_metric = metric_from_frame(frame, ref_pred)
        stable_pred = stable_predictions[split]
        stable_metric = metric_from_frame(frame, stable_pred)
        rows.append(
            {
                "validation_scheme": "fixed_diagnostic",
                "split": split,
                "candidate": REFERENCE,
                "method": "reference_70_30",
                "n": len(frame),
                **ref_metric,
                "delta_MdAPE_vs_reference": 0.0,
                "delta_MAPE_vs_reference": 0.0,
                "delta_p95_APE_vs_reference": 0.0,
                "delta_RMSE_log_vs_reference": 0.0,
                "improve_count_vs_reference": 0,
            }
        )
        rows.append(
            {
                "validation_scheme": "fixed_diagnostic",
                "split": split,
                "candidate": STABLE,
                "method": "stable_huber_residual",
                "n": len(frame),
                **stable_metric,
                "delta_MdAPE_vs_reference": stable_metric["MdAPE"] - ref_metric["MdAPE"],
                "delta_MAPE_vs_reference": stable_metric["MAPE"] - ref_metric["MAPE"],
                "delta_p95_APE_vs_reference": stable_metric["p95_APE"] - ref_metric["p95_APE"],
                "delta_RMSE_log_vs_reference": stable_metric["RMSE_log"] - ref_metric["RMSE_log"],
                "improve_count_vs_reference": int(stable_metric["MdAPE"] < ref_metric["MdAPE"])
                + int(stable_metric["MAPE"] < ref_metric["MAPE"])
                + int(stable_metric["p95_APE"] < ref_metric["p95_APE"]),
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


def feature_coefficients(model: Any) -> pd.DataFrame:
    reg = model.named_steps["model"]
    coefs = getattr(reg, "coef_", np.full(len(FEATURES), np.nan))
    roles = {
        "svc_fallback": "유사 작품 기반 가격 피처",
        "shrunk_svc_prior": "완화된 유사 작품 기준가",
        "current_shrunk_huber_gap": "현재 후보와 Huber 기준선 차이",
        "ppv8_defensive": "오차 안정화 후보",
        "shrunk_huber_refit": "Huber 기준 예측값",
        "raw_shrunk_prior_gap": "원 기준가와 완화 기준가 차이",
        "log_area": "작품 크기",
        "current_ppv8_gap": "현재 후보와 오차 안정화 후보 차이",
        "svc_group_n_log": "유사 표본 수 신뢰도",
        "svc_prior_iqr": "유사 표본 가격 분산",
    }
    rows: list[dict[str, Any]] = []
    for feature, coef in zip(FEATURES, coefs):
        direction = "가격 보정값을 올리는 방향" if coef > 0 else "가격 보정값을 낮추는 방향" if coef < 0 else "영향 거의 없음"
        rows.append(
            {
                "candidate": STABLE,
                "feature": feature,
                "feature_role": roles.get(feature, "잔차 보조 피처"),
                "coefficient_on_scaled_feature": float(coef),
                "abs_coefficient": float(abs(coef)),
                "direction": direction,
                "alpha": STABLE_CONFIG["alpha"],
                "cap": STABLE_CONFIG["cap"],
                "strength": STABLE_CONFIG["strength"],
            }
        )
    return pd.DataFrame(rows).sort_values("abs_coefficient", ascending=False)


def segment_value(frame: pd.DataFrame, keys: tuple[str, ...]) -> pd.Series:
    if len(keys) == 1:
        return frame[keys[0]].astype(str)
    return frame[list(keys)].astype(str).agg(" + ".join, axis=1)


def segment_summary_for_split(
    split: str,
    frame: pd.DataFrame,
    reference_pred: np.ndarray,
    stable_pred: np.ndarray,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    reference_metric = metric_from_frame(frame, reference_pred)
    stable_metric = metric_from_frame(frame, stable_pred)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    stable_price = np.clip(np.exp(stable_pred), 1_000.0, None)

    for segment_name, keys, min_n in SEGMENT_KEYS:
        labels = segment_value(frame, keys)
        tmp = pd.DataFrame({"segment_value": labels}).reset_index(names="row_pos")
        for value, group in tmp.groupby("segment_value", observed=False):
            idx = group["row_pos"].to_numpy(dtype=int)
            if len(idx) == 0:
                continue
            ref = metric_from_subset(frame, reference_pred, idx)
            stable = metric_from_subset(frame, stable_pred, idx)
            residual = frame["actual_log"].to_numpy(dtype=float)[idx] - stable_pred[idx]
            ape = np.abs(stable_price[idx] - actual_price[idx]) / np.clip(actual_price[idx], 1.0, None)
            rows.append(
                {
                    "split": split,
                    "segment_name": segment_name,
                    "segment_keys": "+".join(keys),
                    "segment_value": value,
                    "n": len(idx),
                    "min_n_for_action": min_n,
                    "enough_n": len(idx) >= min_n,
                    "stable_MdAPE": stable["MdAPE"],
                    "stable_MAPE": stable["MAPE"],
                    "stable_p95_APE": stable["p95_APE"],
                    "stable_RMSE_log": stable["RMSE_log"],
                    "reference_MdAPE": ref["MdAPE"],
                    "reference_MAPE": ref["MAPE"],
                    "reference_p95_APE": ref["p95_APE"],
                    "delta_MdAPE_vs_reference": stable["MdAPE"] - ref["MdAPE"],
                    "delta_MAPE_vs_reference": stable["MAPE"] - ref["MAPE"],
                    "delta_p95_APE_vs_reference": stable["p95_APE"] - ref["p95_APE"],
                    "segment_delta_MdAPE_vs_global_stable": stable["MdAPE"] - stable_metric["MdAPE"],
                    "segment_delta_MAPE_vs_global_stable": stable["MAPE"] - stable_metric["MAPE"],
                    "segment_delta_p95_vs_global_stable": stable["p95_APE"] - stable_metric["p95_APE"],
                    "median_residual_log": float(np.median(residual)),
                    "mean_residual_log": float(np.mean(residual)),
                    "suggested_raw_median_correction_log": float(np.median(residual)),
                    "ape_gt_50pct_rate": float((ape > 0.5).mean()),
                    "ape_gt_100pct_rate": float((ape > 1.0).mean()),
                    "over_2x_rate": float((stable_price[idx] >= actual_price[idx] * 2.0).mean()),
                    "under_half_rate": float((stable_price[idx] <= actual_price[idx] * 0.5).mean()),
                    "global_reference_MdAPE": reference_metric["MdAPE"],
                    "global_stable_MdAPE": stable_metric["MdAPE"],
                }
            )
    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary["high_residual_risk"] = (
            (summary["stable_p95_APE"] > summary["stable_p95_APE"].median())
            | (summary["stable_MAPE"] > summary["stable_MAPE"].median())
            | (summary["ape_gt_100pct_rate"] > 0.05)
        )
        summary["stable_worse_than_reference"] = (
            (summary["delta_MdAPE_vs_reference"] > 0)
            | (summary["delta_MAPE_vs_reference"] > 0)
            | (summary["delta_p95_APE_vs_reference"] > 0)
        )
    return summary


def next_experiment_candidates(segment_summary: pd.DataFrame) -> pd.DataFrame:
    if segment_summary.empty:
        return pd.DataFrame()
    validation = segment_summary[segment_summary["split"].eq("validation")].copy()
    validation = validation[validation["enough_n"]].copy()
    validation = validation[
        validation["high_residual_risk"]
        | validation["stable_worse_than_reference"]
        | (validation["median_residual_log"].abs() >= 0.03)
    ].copy()
    if validation.empty:
        return validation

    def recommendation(row: pd.Series) -> str:
        name = str(row["segment_name"])
        value = str(row["segment_value"])
        median_resid = float(row["median_residual_log"])
        if "low_sample" in value or name in {"basis_n_bucket", "pred_x_basis_n", "size_x_basis_n"}:
            return "기준가 표본 수 기반 shrinkage/fallback 재조정 실험"
        if "high_spread" in value or name == "basis_iqr_bucket":
            return "IQR 큰 구간의 기준가 영향도 축소 또는 p95 방어 cap 실험"
        if "disagreement" in value or "gap" in name:
            return "후보 간 예측 gap이 큰 구간의 routing 또는 보수형 fallback 실험"
        if name in {"pred_bin", "size_bin"}:
            return "예측 가격대/크기 구간별 Huber cap-strength 민감도 실험"
        if median_resid > 0:
            return "반복 과소예측 구간의 작은 상향 residual 보정 실험"
        return "반복 과대예측 구간의 작은 하향 residual 보정 실험"

    validation["priority_score"] = (
        validation["stable_MAPE"].fillna(0.0)
        + validation["stable_p95_APE"].fillna(0.0)
        + validation["median_residual_log"].abs().fillna(0.0)
        + validation["stable_worse_than_reference"].astype(float) * 0.25
    )
    validation["recommended_next_step"] = validation.apply(recommendation, axis=1)
    validation["guard_note"] = np.where(
        validation["stable_worse_than_reference"],
        "현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요",
        "현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능",
    )
    cols = [
        "segment_name",
        "segment_keys",
        "segment_value",
        "n",
        "stable_MdAPE",
        "stable_MAPE",
        "stable_p95_APE",
        "delta_MdAPE_vs_reference",
        "delta_MAPE_vs_reference",
        "delta_p95_APE_vs_reference",
        "median_residual_log",
        "ape_gt_100pct_rate",
        "priority_score",
        "recommended_next_step",
        "guard_note",
    ]
    return validation.sort_values("priority_score", ascending=False)[cols]


def largest_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    stable = predictions[predictions["candidate"].eq(STABLE)].copy()
    cols = [
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_price",
        "pred_price",
        "ape",
        "residual_log",
        "risk_cause",
        "pred_bin",
        "size_bin",
        "basis_n_bucket",
        "basis_iqr_bucket",
        "basis_level_simple",
        "basis_gap_sign",
        "medium_support_bucket_clean",
    ]
    return stable.sort_values(["split", "ape"], ascending=[True, False])[cols]


def carry_forward_summary(segment_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    source = SOURCE_HCOEF11 / "outputs" / "bootstrap_or_repeated_split_summary.csv"
    if source.exists():
        prev = pd.read_csv(source)
        prev.insert(0, "source_experiment", "PP-HCOEF11")
        prev.insert(1, "carried_forward_by", EXP_ID)
        rows.append(prev)
    risk = segment_summary[segment_summary["split"].eq("validation")].copy()
    if not risk.empty:
        risk = risk[risk["enough_n"]].copy()
        risk["summary_type"] = "diagnostic_segment_risk"
        risk["validation_scheme"] = "fixed_validation_diagnostic"
        risk["candidate"] = STABLE
        risk["metric"] = risk["segment_name"]
        keep = [
            "summary_type",
            "validation_scheme",
            "split",
            "candidate",
            "metric",
            "segment_value",
            "n",
            "stable_MdAPE",
            "stable_MAPE",
            "stable_p95_APE",
            "delta_MdAPE_vs_reference",
            "delta_MAPE_vs_reference",
            "delta_p95_APE_vs_reference",
            "median_residual_log",
            "high_residual_risk",
            "stable_worse_than_reference",
        ]
        rows.append(risk.sort_values("stable_p95_APE", ascending=False)[keep].head(80))
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True, sort=False)


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
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
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
    metrics: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    segment_summary: pd.DataFrame,
    next_candidates: pd.DataFrame,
    largest: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    fixed_view = metrics[metrics["split"].isin(["validation", "test", "0604_ex50"])].copy()
    stable_test = fixed_view[(fixed_view["split"].eq("test")) & (fixed_view["candidate"].eq(STABLE))].iloc[0]
    stable_0604 = fixed_view[(fixed_view["split"].eq("0604_ex50")) & (fixed_view["candidate"].eq(STABLE))].iloc[0]
    risk_top = next_candidates.head(12).copy()
    segment_top = (
        segment_summary[
            segment_summary["split"].eq("validation")
            & segment_summary["enough_n"]
            & (segment_summary["high_residual_risk"] | segment_summary["stable_worse_than_reference"])
        ]
        .sort_values(["stable_p95_APE", "stable_MAPE"], ascending=False)
        .head(24)
    )
    carried = summary[summary.get("summary_type", pd.Series(dtype=str)).eq("repeated_oof")].copy()

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 잔차 위험 원인 진단",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 현재 Warm 개선 후보가 아직 크게 틀리는 작품군을 기준가 신뢰도, 크기, 재료/지지체, 후보 간 gap 기준으로 정량화.",
            f"- 기준 후보: `{REFERENCE}` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.",
            f"- 진단 후보: `{STABLE}` = 기준 후보 위에 Huber 잔차 보정을 작게 더한 현재 Warm 개선 후보.",
            "- 주의: 이 실험은 새 보정 후보를 채택하지 않고 다음 계수 조정 실험의 원인 지도를 만든다.",
            "",
            "## 1. 실행 결론",
            "",
            "- 판단: 현재 Warm 개선 후보는 유지한다. HCOEF13은 후보 교체가 아니라 남은 오차 원인을 분리한 진단 실험이다.",
            f"- fixed test 성능: MdAPE `{stable_test['MdAPE']:.4f}`, MAPE `{stable_test['MAPE']:.4f}`, p95_APE `{stable_test['p95_APE']:.4f}`, RMSE_log `{stable_test['RMSE_log']:.4f}`.",
            f"- fixed test 개선폭: MdAPE `{stable_test['delta_MdAPE_vs_reference']:.4f}`, MAPE `{stable_test['delta_MAPE_vs_reference']:.4f}`, p95_APE `{stable_test['delta_p95_APE_vs_reference']:.4f}`.",
            f"- 0604 stress test 성능: MdAPE `{stable_0604['MdAPE']:.4f}`, MAPE `{stable_0604['MAPE']:.4f}`, p95_APE `{stable_0604['p95_APE']:.4f}`.",
            "- 다음 실험은 validation에서 확인된 위험 구간에 한정해 기준가 shrinkage, fallback, Huber cap/strength, routing을 비교하는 방식이 적절하다.",
            "",
            "## 2. Fixed validation/test/0604 성능",
            "",
            markdown_table(
                fixed_view[
                    [
                        "split",
                        "candidate",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "improve_count_vs_reference",
                    ]
                ].round(4)
            ),
            "",
            "## 3. HCOEF11 반복 검증 근거",
            "",
            "- HCOEF13은 반복 검증을 새로 돌리는 실험이 아니므로 HCOEF11의 row/artist OOF 근거를 carry-forward한다.",
            markdown_table(
                carried[
                    [
                        "validation_scheme",
                        "candidate",
                        "mean_delta_MdAPE_vs_reference",
                        "mean_delta_MAPE_vs_reference",
                        "mean_delta_p95_APE_vs_reference",
                        "MdAPE_improve_prob",
                        "MAPE_improve_prob",
                        "p95_improve_prob",
                        "all3_improve_prob",
                    ]
                ].round(4)
                if not carried.empty
                else carried
            ),
            "",
            "## 4. Validation 기준 위험 구간 상위",
            "",
            "- 아래 표는 test가 아니라 validation에서 본 위험 구간이다. 다음 보정 후보를 고를 때 우선 참고할 수 있다.",
            markdown_table(
                segment_top[
                    [
                        "segment_name",
                        "segment_value",
                        "n",
                        "stable_MdAPE",
                        "stable_MAPE",
                        "stable_p95_APE",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "median_residual_log",
                        "stable_worse_than_reference",
                    ]
                ].round(4),
                max_rows=24,
            ),
            "",
            "## 5. 다음 실험 후보",
            "",
            "- `median_residual_log`가 양수이면 과소예측 경향, 음수이면 과대예측 경향이다.",
            "- 이 표는 바로 적용할 보정식이 아니라 다음 HCOEF 실험의 후보 리스트다.",
            markdown_table(risk_top.round(4), max_rows=12),
            "",
            "## 6. Huber 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준이다. 실제 가격 단위 계수가 아니라 방향성과 상대 영향 비교용이다.",
            "- 현재 후보는 기준가를 크게 바꾸기보다, 유사 표본 수와 기준가 분산을 참고해 잔차 보정폭을 작게 제한한다.",
            markdown_table(coeffs.round(5)),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4)),
            "",
            "## 8. 큰 오차 작품 예시",
            "",
            "- 실제 가격 구간은 운영 시점에 알 수 없으므로 진단용으로만 사용한다.",
            markdown_table(largest.round(4), max_rows=30),
            "",
            "## 9. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/risk_segment_summary.csv`",
            "- `outputs/next_experiment_candidates.csv`",
            "- `outputs/largest_errors.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef13_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef13_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames_raw = hcoef5.build_frames()
    validation = frames_raw["validation"]
    validation_stable_pred, stable_model = stable_prediction(validation, validation)
    actual_edges = actual_bin_edges(validation)

    enriched_frames: dict[str, pd.DataFrame] = {}
    stable_predictions: dict[str, np.ndarray] = {}
    pred_rows: list[pd.DataFrame] = []
    segment_rows: list[pd.DataFrame] = []

    for split in ["validation", "test", "0604_ex50"]:
        frame = frames_raw[split]
        stable_pred, _ = stable_prediction(validation, frame)
        reference_pred = frame[REFERENCE].to_numpy(dtype=float)
        enriched = enrich_split(validation, frame, validation_stable_pred, stable_pred, actual_edges)
        enriched_frames[split] = enriched
        stable_predictions[split] = stable_pred

        pred_rows.append(
            prediction_frame(enriched, REFERENCE, split, reference_pred, "reference_70_30", reference_pred, stable_pred)
        )
        pred_rows.append(
            prediction_frame(enriched, STABLE, split, stable_pred, "stable_huber_residual", reference_pred, stable_pred)
        )
        segment_rows.append(segment_summary_for_split(split, enriched, reference_pred, stable_pred))

    metrics = metric_rows(enriched_frames, stable_predictions)
    predictions = pd.concat(pred_rows, ignore_index=True, sort=False)
    coeffs = feature_coefficients(stable_model)
    residuals = residual_analysis(predictions)
    segment_summary = pd.concat(segment_rows, ignore_index=True, sort=False)
    next_candidates = next_experiment_candidates(segment_summary)
    largest = largest_errors(predictions)
    summary = carry_forward_summary(segment_summary)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    segment_summary.to_csv(out / "risk_segment_summary.csv", index=False)
    next_candidates.to_csv(out / "next_experiment_candidates.csv", index=False)
    largest.to_csv(out / "largest_errors.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "stable_candidate": STABLE,
        "stable_config": STABLE_CONFIG,
        "feature_columns": FEATURES,
        "segment_keys": [
            {"segment_name": name, "keys": list(keys), "min_n": min_n} for name, keys, min_n in SEGMENT_KEYS
        ],
        "selection_policy": "Diagnostic only. Do not select a new candidate from fixed test; use validation risk segments to plan the next OOF experiment.",
        "source_validation_evidence": str((SOURCE_HCOEF11 / "outputs" / "bootstrap_or_repeated_split_summary.csv").relative_to(REPO)),
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, coeffs, residuals, segment_summary, next_candidates, largest, summary)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- fixed metrics ---")
    print(
        metrics[
            [
                "split",
                "candidate",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "RMSE_log",
                "delta_MdAPE_vs_reference",
                "delta_MAPE_vs_reference",
                "delta_p95_APE_vs_reference",
                "improve_count_vs_reference",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    print("--- next experiment candidates ---")
    print(next_candidates.round(4).head(15).to_string(index=False))


if __name__ == "__main__":
    main()
