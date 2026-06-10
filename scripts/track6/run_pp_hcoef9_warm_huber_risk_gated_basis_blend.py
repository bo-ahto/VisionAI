#!/usr/bin/env python3
"""Run PP-HCOEF9: risk-gated basis blend for Warm Huber.

HCOEF4 showed that a loose comparable-basis Huber model can improve MdAPE/MAPE
but may worsen p95_APE. HCOEF5 used a single global cap/strength for every row.
This experiment keeps the stable HCOEF3 candidate as the anchor and only moves
toward the loose basis model when the comparable-basis signal looks reliable.

The routing signals are prediction-time features only: comparable sample count,
comparable spread, and disagreement between the stable and loose-basis models.
Fixed test is confirmation only; repeated validation/OOF drives selection.
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

import run_pp_hcoef4_warm_basis_generation_refinement as hcoef4  # noqa: E402
import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF9"
EXP_SLUG = "PP-HCOEF9_warm_huber_risk_gated_basis_blend"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef5.REFERENCE
STABLE = hcoef5.STABLE
N_FOLDS = 5
N_REPEATS = 20
SEED = 20260612

BASIS_CONFIGS = [
    {
        "name": "loose_basis_core_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.1,
        "source": "HCOEF4 MdAPE/MAPE 개선 신호 후보",
    },
    {
        "name": "loose_basis_core_huber_alpha0p01",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.01,
        "source": "HCOEF4 neighbouring basis-core 후보",
    },
    {
        "name": "loose_basis_gap_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_gap_reliability",
        "kind": "huber",
        "alpha": 0.1,
        "source": "HCOEF4 gap/reliability 후보",
    },
]

RISK_POLICIES = [
    {
        "name": "low_strong_mid_light_high_stable",
        "low": {"min_n": 10, "max_iqr": 0.75, "max_basis_gap": 0.70, "max_model_gap": 0.55, "cap": 0.10, "strength": 0.75},
        "mid": {"min_n": 5, "max_iqr": 1.00, "max_basis_gap": 0.95, "max_model_gap": 0.75, "cap": 0.05, "strength": 0.35},
        "high": {"cap": 0.00, "strength": 0.00},
    },
    {
        "name": "low_medium_mid_tiny_high_stable",
        "low": {"min_n": 10, "max_iqr": 0.75, "max_basis_gap": 0.70, "max_model_gap": 0.55, "cap": 0.08, "strength": 0.50},
        "mid": {"min_n": 5, "max_iqr": 1.00, "max_basis_gap": 0.95, "max_model_gap": 0.75, "cap": 0.03, "strength": 0.20},
        "high": {"cap": 0.00, "strength": 0.00},
    },
    {
        "name": "low_only_basis_high_stable",
        "low": {"min_n": 10, "max_iqr": 0.70, "max_basis_gap": 0.65, "max_model_gap": 0.50, "cap": 0.10, "strength": 0.75},
        "mid": {"min_n": 999999, "max_iqr": 0.0, "max_basis_gap": 0.0, "max_model_gap": 0.0, "cap": 0.00, "strength": 0.00},
        "high": {"cap": 0.00, "strength": 0.00},
    },
    {
        "name": "broad_low_mid_guarded",
        "low": {"min_n": 8, "max_iqr": 0.85, "max_basis_gap": 0.80, "max_model_gap": 0.65, "cap": 0.08, "strength": 0.60},
        "mid": {"min_n": 4, "max_iqr": 1.10, "max_basis_gap": 1.05, "max_model_gap": 0.85, "cap": 0.04, "strength": 0.25},
        "high": {"cap": 0.01, "strength": 0.10},
    },
    {
        "name": "model_agreement_only",
        "low": {"min_n": 3, "max_iqr": 9.99, "max_basis_gap": 9.99, "max_model_gap": 0.30, "cap": 0.08, "strength": 0.75},
        "mid": {"min_n": 3, "max_iqr": 9.99, "max_basis_gap": 9.99, "max_model_gap": 0.50, "cap": 0.04, "strength": 0.35},
        "high": {"cap": 0.00, "strength": 0.00},
    },
    {
        "name": "sample_count_only",
        "low": {"min_n": 15, "max_iqr": 9.99, "max_basis_gap": 9.99, "max_model_gap": 9.99, "cap": 0.08, "strength": 0.50},
        "mid": {"min_n": 7, "max_iqr": 9.99, "max_basis_gap": 9.99, "max_model_gap": 9.99, "cap": 0.04, "strength": 0.25},
        "high": {"cap": 0.00, "strength": 0.00},
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    return hcoef5.build_frames()


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef5.metric_from_frame(frame, pred_log)


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.row_folds(n, seed)


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.artist_folds(frame, seed)


def risk_labels(frame: pd.DataFrame, diff: np.ndarray, policy: dict[str, Any]) -> np.ndarray:
    n_log = pd.to_numeric(frame.get("basis_relaxed_n_log"), errors="coerce").fillna(0.0)
    iqr = pd.to_numeric(frame.get("basis_relaxed_iqr"), errors="coerce").fillna(np.inf)
    basis_gap = pd.to_numeric(frame.get("basis_relaxed_vs_current_gap"), errors="coerce").abs().fillna(np.inf)
    model_gap = pd.Series(np.abs(np.asarray(diff, dtype=float)), index=frame.index)

    low_cfg = policy["low"]
    mid_cfg = policy["mid"]
    low = (
        n_log.ge(np.log1p(float(low_cfg["min_n"])))
        & iqr.le(float(low_cfg["max_iqr"]))
        & basis_gap.le(float(low_cfg["max_basis_gap"]))
        & model_gap.le(float(low_cfg["max_model_gap"]))
    )
    mid = (
        ~low
        & n_log.ge(np.log1p(float(mid_cfg["min_n"])))
        & iqr.le(float(mid_cfg["max_iqr"]))
        & basis_gap.le(float(mid_cfg["max_basis_gap"]))
        & model_gap.le(float(mid_cfg["max_model_gap"]))
    )
    labels = np.full(len(frame), "high", dtype=object)
    labels[mid.to_numpy(dtype=bool)] = "mid"
    labels[low.to_numpy(dtype=bool)] = "low"
    return labels


def risk_gated_prediction(frame: pd.DataFrame, stable_pred: np.ndarray, basis_pred: np.ndarray, policy: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    stable_pred = np.asarray(stable_pred, dtype=float)
    basis_pred = np.asarray(basis_pred, dtype=float)
    diff = basis_pred - stable_pred
    labels = risk_labels(frame, diff, policy)
    correction = np.zeros(len(frame), dtype=float)
    for segment in ["low", "mid", "high"]:
        params = policy[segment]
        cap = float(params["cap"])
        strength = float(params["strength"])
        mask = labels == segment
        if cap > 0.0 and strength > 0.0 and mask.any():
            correction[mask] = np.clip(diff[mask], -cap, cap) * strength
    return stable_pred + correction, labels


def candidate_name(basis_name: str, policy: dict[str, Any]) -> str:
    return f"hcoef9_{basis_name}_{policy['name']}"


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred: np.ndarray, method: str) -> pd.DataFrame:
    pred = np.asarray(pred, dtype=float)
    price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred,
            "pred_price": price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred,
            "ape": np.abs(price - actual) / np.clip(actual, 1.0, None),
        }
    )


def metric_row(split: str, candidate: str, method: str, frame: pd.DataFrame, pred: np.ndarray, stable_pred: np.ndarray) -> dict[str, Any]:
    metric = metric_from_frame(frame, pred)
    stable = metric_from_frame(frame, stable_pred)
    return {
        "validation_scheme": "fixed_confirmation",
        "repeat": -1,
        "candidate": candidate,
        "method": method,
        "split": split,
        "n": len(frame),
        **metric,
        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - stable["MdAPE"],
        "delta_MAPE_vs_hcoef2": metric["MAPE"] - stable["MAPE"],
        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - stable["p95_APE"],
        "improve_count_vs_hcoef2": int(metric["MdAPE"] < stable["MdAPE"])
        + int(metric["MAPE"] < stable["MAPE"])
        + int(metric["p95_APE"] < stable["p95_APE"]),
    }


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            oof: dict[str, np.ndarray] = {}

            for train_idx, hold_idx in folds:
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                stable_pred, _ = hcoef5.hcoef2_prediction(train, hold)
                if STABLE not in oof:
                    oof[STABLE] = np.full(len(validation), np.nan, dtype=float)
                oof[STABLE][hold_idx] = stable_pred

                for config in BASIS_CONFIGS:
                    basis_pred, _ = hcoef5.basis_prediction(train, hold, config)
                    basis_name = str(config["name"])
                    if basis_name not in oof:
                        oof[basis_name] = np.full(len(validation), np.nan, dtype=float)
                    oof[basis_name][hold_idx] = basis_pred

                    for policy in RISK_POLICIES:
                        name = candidate_name(basis_name, policy)
                        pred, _ = risk_gated_prediction(hold, stable_pred, basis_pred, policy)
                        if name not in oof:
                            oof[name] = np.full(len(validation), np.nan, dtype=float)
                        oof[name][hold_idx] = pred

            ref_metric = metric_from_frame(validation, oof[STABLE])
            for candidate, pred in oof.items():
                metric = metric_from_frame(validation, pred)
                metric_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": candidate,
                        "n": len(validation),
                        **metric,
                        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE_vs_hcoef2": metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - ref_metric["p95_APE"],
                        "improve_count_vs_hcoef2": int(metric["MdAPE"] < ref_metric["MdAPE"])
                        + int(metric["MAPE"] < ref_metric["MAPE"])
                        + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                    }
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, candidate, f"validation_{scheme}_repeat0", pred, "repeated_oof"))

    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    segment_rows: list[dict[str, Any]] = []

    stable_by_split: dict[str, np.ndarray] = {}
    stable_model = None
    for split in ["validation", "test", "0604_ex50"]:
        pred, model = hcoef5.hcoef2_prediction(validation, frames[split])
        stable_by_split[split] = pred
        stable_model = model
        metric_rows.append(metric_row(split, STABLE, "hcoef3_stable_anchor", frames[split], pred, pred))
        pred_rows.append(prediction_frame(frames[split], STABLE, split, pred, "hcoef3_stable_anchor"))

    if stable_model is not None:
        coef_rows.append(
            hcoef4.coef_frame(
                stable_model,
                STABLE,
                hcoef4.hcoef1.RESIDUAL_FEATURE_SETS["resid_basis_size_reliability"],
                "huber_residual",
                "residual_log",
            )
        )

    for config in BASIS_CONFIGS:
        basis_by_split: dict[str, np.ndarray] = {}
        fitted_model = None
        basis_name = str(config["name"])
        for split in ["validation", "test", "0604_ex50"]:
            pred, model = hcoef5.basis_prediction(validation, frames[split], config)
            basis_by_split[split] = pred
            fitted_model = model
            metric_rows.append(metric_row(split, basis_name, "loose_basis_huber_full", frames[split], pred, stable_by_split[split]))
            pred_rows.append(prediction_frame(frames[split], basis_name, split, pred, "loose_basis_huber_full"))
        if fitted_model is not None:
            coef_rows.append(
                hcoef4.coef_frame(
                    fitted_model,
                    basis_name,
                    hcoef4.BASIS_FEATURE_SETS[str(config["feature_key"])],
                    str(config["kind"]),
                    "actual_log",
                )
            )

        for policy in RISK_POLICIES:
            name = candidate_name(basis_name, policy)
            for split in ["validation", "test", "0604_ex50"]:
                pred, labels = risk_gated_prediction(frames[split], stable_by_split[split], basis_by_split[split], policy)
                metric_rows.append(metric_row(split, name, "risk_gated_basis_blend", frames[split], pred, stable_by_split[split]))
                pred_rows.append(prediction_frame(frames[split], name, split, pred, "risk_gated_basis_blend"))
                counts = pd.Series(labels).value_counts(normalize=False).to_dict()
                shares = pd.Series(labels).value_counts(normalize=True).to_dict()
                segment_rows.append(
                    {
                        "candidate": name,
                        "basis_candidate": basis_name,
                        "policy": policy["name"],
                        "split": split,
                        "low_n": int(counts.get("low", 0)),
                        "mid_n": int(counts.get("mid", 0)),
                        "high_n": int(counts.get("high", 0)),
                        "low_share": float(shares.get("low", 0.0)),
                        "mid_share": float(shares.get("mid", 0.0)),
                        "high_share": float(shares.get("high", 0.0)),
                    }
                )

    predictions = pd.concat(pred_rows, ignore_index=True)
    residuals = residual_analysis(predictions)
    return pd.DataFrame(metric_rows), predictions, pd.concat(coef_rows, ignore_index=True), residuals, pd.DataFrame(segment_rows)


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    repeat_metrics = metrics[metrics["repeat"].ge(0)].copy()
    for (scheme, candidate), group in repeat_metrics.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "mean_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].mean()),
                "mean_delta_MAPE_vs_hcoef2": float(group["delta_MAPE_vs_hcoef2"].mean()),
                "mean_delta_p95_APE_vs_hcoef2": float(group["delta_p95_APE_vs_hcoef2"].mean()),
                "std_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].std()),
                "MdAPE_improve_prob_vs_hcoef2": float((group["delta_MdAPE_vs_hcoef2"] < 0).mean()),
                "MAPE_improve_prob_vs_hcoef2": float((group["delta_MAPE_vs_hcoef2"] < 0).mean()),
                "p95_improve_prob_vs_hcoef2": float((group["delta_p95_APE_vs_hcoef2"] < 0).mean()),
                "all3_improve_prob_vs_hcoef2": float((group["improve_count_vs_hcoef2"] == 3).mean()),
                "mean_improve_count_vs_hcoef2": float(group["improve_count_vs_hcoef2"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["all3_improve_prob_vs_hcoef2", "mean_delta_MdAPE_vs_hcoef2", "mean_delta_MAPE_vs_hcoef2"],
        ascending=[False, True, True],
    )


def select_candidates(summary: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    row = summary[summary["validation_scheme"].eq("row_oof")].set_index("candidate")
    artist = summary[summary["validation_scheme"].eq("artist_oof")].set_index("candidate")
    test = fixed[fixed["split"].eq("test")].set_index("candidate")
    ops = fixed[fixed["split"].eq("0604_ex50")].set_index("candidate")
    candidates = sorted(set(row.index) & set(artist.index) & set(test.index))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate": candidate,
                "row_all3_prob": row.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "artist_all3_prob": artist.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "row_delta_MdAPE": row.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "row_delta_MAPE": row.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "row_delta_p95_APE": row.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "artist_delta_MdAPE": artist.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "artist_delta_MAPE": artist.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "artist_delta_p95_APE": artist.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "test_delta_MdAPE": test.loc[candidate, "delta_MdAPE_vs_hcoef2"],
                "test_delta_MAPE": test.loc[candidate, "delta_MAPE_vs_hcoef2"],
                "test_delta_p95_APE": test.loc[candidate, "delta_p95_APE_vs_hcoef2"],
                "ops0604_delta_MdAPE": ops.loc[candidate, "delta_MdAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_MAPE": ops.loc[candidate, "delta_MAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_p95_APE": ops.loc[candidate, "delta_p95_APE_vs_hcoef2"] if candidate in ops.index else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["passes_repeat_gate"] = (
        out["row_all3_prob"].ge(0.90)
        & out["artist_all3_prob"].ge(0.90)
        & out["row_delta_MdAPE"].lt(0)
        & out["row_delta_MAPE"].le(0)
        & out["row_delta_p95_APE"].le(0)
        & out["artist_delta_MdAPE"].lt(0)
        & out["artist_delta_MAPE"].le(0)
        & out["artist_delta_p95_APE"].le(0)
    )
    out["passes_fixed_guard"] = out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].le(0) & out["test_delta_p95_APE"].le(0)
    out["purpose"] = np.select(
        [
            out["passes_repeat_gate"] & out["passes_fixed_guard"],
            out["row_delta_MAPE"].lt(0) & out["artist_delta_MAPE"].lt(0) & out["test_delta_p95_APE"].le(0.01),
            out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].lt(0) & out["test_delta_p95_APE"].le(0.01),
        ],
        ["operational_candidate", "repeat_mape_candidate", "fixed_confirmation_candidate"],
        default="hold_or_reject",
    )
    return out.sort_values(
        ["passes_repeat_gate", "passes_fixed_guard", "row_delta_MdAPE", "artist_delta_MdAPE", "test_delta_MdAPE"],
        ascending=[False, False, True, True, True],
    )


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": int(len(group)),
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "candidate"])


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
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
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
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
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    summary: pd.DataFrame,
    fixed: pd.DataFrame,
    selection: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    segments: pd.DataFrame,
) -> None:
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    segment_summary = (
        segments.groupby("candidate", observed=False)
        .agg(
            low_share_mean=("low_share", "mean"),
            mid_share_mean=("mid_share", "mean"),
            high_share_mean=("high_share", "mean"),
        )
        .reset_index()
        .sort_values(["low_share_mean", "mid_share_mean"], ascending=[False, False])
    )
    decision = "새 운영 기본 후보 채택 없음"
    if not selection.empty:
        top = selection.iloc[0]
        if bool(top["passes_repeat_gate"]) and bool(top["passes_fixed_guard"]):
            decision = f"운영 후보 가능: `{top['candidate']}`"
        elif str(top["purpose"]) != "hold_or_reject":
            decision = f"목적별 보류 후보: `{top['candidate']}`"

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 위험도 기반 기준가 결합 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF4 loose 기준가 Huber의 MdAPE/MAPE 개선 신호를 HCOEF3 안정 후보 위에 제한적으로 반영.",
            "- 핵심 가설: 유사 작품 기준가의 표본 수가 충분하고 분산이 낮으며 HCOEF3과 HCOEF4 예측 차이가 과도하지 않을 때만 HCOEF4 쪽으로 이동하면 p95 악화 없이 중앙/평균 오차를 줄일 수 있다.",
            f"- 기준 후보: `{STABLE}`.",
            f"- 반복 설정: row OOF {N_REPEATS}회, artist OOF {N_REPEATS}회, 각 {N_FOLDS} folds.",
            "- 후보 선택: 반복 OOF 우선, fixed test/0604는 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}.",
            "- p95_APE를 함께 낮추지 못한 후보는 기본 후보로 채택하지 않는다.",
            "",
            "## 2. 후보 선택표",
            "",
            markdown_table(selection.round(4), max_rows=24),
            "",
            "## 3. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4), max_rows=36),
            "",
            "## 4. Fixed test 상위 후보",
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
                        "delta_MdAPE_vs_hcoef2",
                        "delta_MAPE_vs_hcoef2",
                        "delta_p95_APE_vs_hcoef2",
                    ]
                ].round(4),
                max_rows=28,
            ),
            "",
            "## 5. 위험도 구간 적용 비율",
            "",
            markdown_table(segment_summary.round(4), max_rows=24),
            "",
            "## 6. 주요 계수",
            "",
            "- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.",
            markdown_table(coeffs.sort_values("abs_coefficient", ascending=False).head(40).round(5)),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=36),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/risk_segment_summary.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef9_warm_huber_risk_gated_basis_blend_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef9_warm_huber_risk_gated_basis_blend_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"])
    fixed_metrics, fixed_predictions, coeffs, residuals, segments = fixed_confirmation(frames)
    summary = summarize_repeated(repeated_metrics)
    selection = select_candidates(summary, fixed_metrics)

    metrics = pd.concat([repeated_metrics, fixed_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([repeated_predictions, fixed_predictions], ignore_index=True, sort=False)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)
    segments.to_csv(out / "risk_segment_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": STABLE,
        "original_warm_reference": REFERENCE,
        "basis_configs": BASIS_CONFIGS,
        "risk_policies": RISK_POLICIES,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "selection_policy": "row/artist repeated OOF first; fixed test p95 must not worsen",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, fixed_metrics, selection, coeffs, residuals, segments)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected candidates ---")
    print(selection.round(4).head(20).to_string(index=False))
    print("--- fixed test top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])[
            [
                "candidate",
                "method",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_vs_hcoef2",
                "delta_MAPE_vs_hcoef2",
                "delta_p95_APE_vs_hcoef2",
            ]
        ]
        .round(4)
        .head(16)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
