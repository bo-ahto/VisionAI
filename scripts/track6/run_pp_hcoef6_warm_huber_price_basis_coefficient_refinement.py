#!/usr/bin/env python3
"""Run PP-HCOEF6: conditional routing for Warm Huber basis candidates.

HCOEF4 showed that a finer comparable-price basis can improve MdAPE/MAPE, but
may worsen p95_APE when applied to every sample. HCOEF6 therefore tests a more
conservative rule: keep the stable HCOEF3 candidate by default and apply the
basis-Huber delta only where the basis looks reliable from train-derived
features such as sample count, price spread, basis level, and gap size.
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

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_hcoef4_warm_basis_generation_refinement as hcoef4  # noqa: E402
import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF6"
EXP_SLUG = "PP-HCOEF6_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = "current_70_30"
STABLE = "hcoef2_size_reliability_cap005_s050"
N_FOLDS = 5
N_REPEATS = 12
SEED = 20260609

BASIS_CONFIGS = [
    {
        "name": "loose_basis_core_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.1,
    },
    {
        "name": "loose_basis_core_huber_alpha0p01",
        "policy": "loose",
        "feature_key": "basis_core",
        "kind": "huber",
        "alpha": 0.01,
    },
    {
        "name": "loose_basis_gap_huber_alpha0p1",
        "policy": "loose",
        "feature_key": "basis_gap_reliability",
        "kind": "huber",
        "alpha": 0.1,
    },
]

ROUTING_RULES = [
    {
        "name": "artist_reliable_n5_iqr090_gap080_cap005_s050",
        "levels": ["artist_medium_support_size", "artist_size", "artist"],
        "min_n": 5,
        "max_iqr": 0.90,
        "max_abs_gap": 0.80,
        "min_weight": 0.35,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "name": "artist_strict_n10_iqr075_gap065_cap005_s075",
        "levels": ["artist_medium_support_size", "artist_size", "artist"],
        "min_n": 10,
        "max_iqr": 0.75,
        "max_abs_gap": 0.65,
        "min_weight": 0.55,
        "cap": 0.05,
        "strength": 0.75,
    },
    {
        "name": "detail_or_artist_n3_iqr080_gap060_cap003_s050",
        "levels": ["artist_medium_support_size", "artist_size", "artist"],
        "min_n": 3,
        "max_iqr": 0.80,
        "max_abs_gap": 0.60,
        "min_weight": 0.25,
        "cap": 0.03,
        "strength": 0.50,
    },
    {
        "name": "broad_reliable_n20_iqr080_gap080_cap005_s050",
        "levels": [
            "artist_medium_support_size",
            "artist_size",
            "artist",
            "medium_support_size",
            "medium_category_support_size",
            "medium_size",
        ],
        "min_n": 20,
        "max_iqr": 0.80,
        "max_abs_gap": 0.80,
        "min_weight": 0.70,
        "cap": 0.05,
        "strength": 0.50,
    },
    {
        "name": "broad_lowrisk_n30_iqr065_gap050_cap003_s075",
        "levels": [
            "artist_medium_support_size",
            "artist_size",
            "artist",
            "medium_support_size",
            "medium_category_support_size",
            "medium_size",
        ],
        "min_n": 30,
        "max_iqr": 0.65,
        "max_abs_gap": 0.50,
        "min_weight": 0.78,
        "cap": 0.03,
        "strength": 0.75,
    },
    {
        "name": "coverage_high_n8_iqr100_gap100_cap003_s025",
        "levels": [
            "artist_medium_support_size",
            "artist_size",
            "artist",
            "medium_support_size",
            "medium_category_support_size",
            "medium_size",
        ],
        "min_n": 8,
        "max_iqr": 1.00,
        "max_abs_gap": 1.00,
        "min_weight": 0.45,
        "cap": 0.03,
        "strength": 0.25,
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    base = hcoef4.build_eval_frames()
    basis = hcoef4.build_basis_features("loose")
    return hcoef4.merge_policy_frames(base, basis, "loose")


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def hcoef2_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    return hcoef5.hcoef2_prediction(train, eval_frame)


def basis_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, Any]:
    return hcoef5.basis_prediction(train, eval_frame, config)


def route_mask(frame: pd.DataFrame, rule: dict[str, Any]) -> np.ndarray:
    level = frame["basis_relaxed_level"].astype(str)
    n = pd.to_numeric(frame["basis_relaxed_n"], errors="coerce").fillna(0.0)
    iqr = pd.to_numeric(frame["basis_relaxed_iqr"], errors="coerce")
    gap = pd.to_numeric(frame["basis_relaxed_vs_current_gap"], errors="coerce")
    weight = pd.to_numeric(frame["basis_shrunk_weight"], errors="coerce").fillna(0.0)
    missing = pd.to_numeric(frame["basis_relaxed_missing"], errors="coerce").fillna(1.0)
    mask = (
        level.isin(rule["levels"])
        & n.ge(float(rule["min_n"]))
        & iqr.le(float(rule["max_iqr"]))
        & gap.abs().le(float(rule["max_abs_gap"]))
        & weight.ge(float(rule["min_weight"]))
        & missing.eq(0.0)
    )
    return mask.to_numpy(dtype=bool)


def routed_predictions(
    frame: pd.DataFrame,
    stable_pred: np.ndarray,
    basis_pred: np.ndarray,
    basis_name: str,
) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {
        STABLE: stable_pred,
        basis_name: basis_pred,
    }
    diff = basis_pred - stable_pred
    for rule in ROUTING_RULES:
        mask = route_mask(frame, rule)
        cap = float(rule["cap"])
        strength = float(rule["strength"])
        candidate = f"{basis_name}__route_{rule['name']}"
        pred = stable_pred.copy()
        pred[mask] = stable_pred[mask] + np.clip(diff[mask], -cap, cap) * strength
        out[candidate] = pred
    return out


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.row_folds(n, seed)


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.artist_folds(frame, seed)


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
            "basis_relaxed_level": frame["basis_relaxed_level"].astype(str).to_numpy(),
            "basis_relaxed_n": pd.to_numeric(frame["basis_relaxed_n"], errors="coerce").to_numpy(dtype=float),
            "basis_relaxed_iqr": pd.to_numeric(frame["basis_relaxed_iqr"], errors="coerce").to_numpy(dtype=float),
            "basis_shrunk_weight": pd.to_numeric(frame["basis_shrunk_weight"], errors="coerce").to_numpy(dtype=float),
            "basis_relaxed_vs_current_gap": pd.to_numeric(frame["basis_relaxed_vs_current_gap"], errors="coerce").to_numpy(dtype=float),
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
                stable_pred, _ = hcoef2_prediction(train, hold)
                for config in BASIS_CONFIGS:
                    basis_pred, _ = basis_prediction(train, hold, config)
                    for candidate, pred in routed_predictions(hold, stable_pred, basis_pred, str(config["name"])).items():
                        if candidate not in oof:
                            oof[candidate] = np.full(len(validation), np.nan, dtype=float)
                        oof[candidate][hold_idx] = pred
                if STABLE not in oof:
                    oof[STABLE] = np.full(len(validation), np.nan, dtype=float)
                oof[STABLE][hold_idx] = stable_pred

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
    route_rows: list[dict[str, Any]] = []

    stable_by_split: dict[str, np.ndarray] = {}
    stable_model = None
    for split in ["validation", "test", "0604_ex50"]:
        pred, model = hcoef2_prediction(validation, frames[split])
        stable_by_split[split] = pred
        stable_model = model
        metric_rows.append(metric_row(split, STABLE, "hcoef2_stable", frames[split], pred, pred))
        pred_rows.append(prediction_frame(frames[split], STABLE, split, pred, "hcoef2_stable"))

    if stable_model is not None:
        coef_rows.append(
            hcoef4.coef_frame(
                stable_model,
                STABLE,
                hcoef1.RESIDUAL_FEATURE_SETS["resid_basis_size_reliability"],
                "huber_residual",
                "residual_log",
            )
        )

    for config in BASIS_CONFIGS:
        fitted_model = None
        basis_by_split: dict[str, np.ndarray] = {}
        for split in ["validation", "test", "0604_ex50"]:
            pred, model = basis_prediction(validation, frames[split], config)
            basis_by_split[split] = pred
            fitted_model = model
            metric_rows.append(metric_row(split, str(config["name"]), "basis_huber_full", frames[split], pred, stable_by_split[split]))
            pred_rows.append(prediction_frame(frames[split], str(config["name"]), split, pred, "basis_huber_full"))

        if fitted_model is not None:
            coef_rows.append(
                hcoef4.coef_frame(
                    fitted_model,
                    str(config["name"]),
                    hcoef4.BASIS_FEATURE_SETS[str(config["feature_key"])],
                    str(config["kind"]),
                    "actual_log",
                )
            )

        for rule in ROUTING_RULES:
            candidate = f"{config['name']}__route_{rule['name']}"
            for split in ["validation", "test", "0604_ex50"]:
                mask = route_mask(frames[split], rule)
                diff = basis_by_split[split] - stable_by_split[split]
                pred = stable_by_split[split].copy()
                pred[mask] = stable_by_split[split][mask] + np.clip(diff[mask], -float(rule["cap"]), float(rule["cap"])) * float(rule["strength"])
                metric_rows.append(metric_row(split, candidate, "conditional_basis_on_hcoef2", frames[split], pred, stable_by_split[split]))
                pred_rows.append(prediction_frame(frames[split], candidate, split, pred, "conditional_basis_on_hcoef2"))
                route_rows.append(
                    {
                        "candidate": candidate,
                        "split": split,
                        "basis_candidate": str(config["name"]),
                        "route_rule": str(rule["name"]),
                        "routed_rows": int(mask.sum()),
                        "routed_share": float(mask.mean()),
                        "min_n": rule["min_n"],
                        "max_iqr": rule["max_iqr"],
                        "max_abs_gap": rule["max_abs_gap"],
                        "min_weight": rule["min_weight"],
                        "cap": rule["cap"],
                        "strength": rule["strength"],
                        "levels": ",".join(rule["levels"]),
                    }
                )

    predictions = pd.concat(pred_rows, ignore_index=True)
    residuals = residual_analysis(predictions)
    return pd.DataFrame(metric_rows), predictions, pd.concat(coef_rows, ignore_index=True), residuals, pd.DataFrame(route_rows)


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
            out["row_delta_MAPE"].lt(0) & out["artist_delta_MAPE"].lt(0),
            out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].lt(0),
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
    routes: pd.DataFrame,
) -> None:
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    decision = "새 운영 기본 후보 채택 없음"
    if not selection.empty:
        first = selection.iloc[0]
        if bool(first["passes_repeat_gate"]) and bool(first["passes_fixed_guard"]):
            decision = f"운영 후보 가능: `{first['candidate']}`"
        elif bool(first["passes_repeat_gate"]):
            decision = f"반복 OOF 후보이나 fixed guard 보류: `{first['candidate']}`"

    route_summary = routes.groupby(["candidate"], observed=False).agg(
        validation_routed_share=("routed_share", lambda x: float(x.iloc[0]) if len(x) else np.nan),
        mean_routed_share=("routed_share", "mean"),
        max_routed_share=("routed_share", "max"),
    ).reset_index()

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 조건부 기준가 routing 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF4 basis-Huber 후보의 MdAPE/MAPE 장점을 살리되, p95_APE 악화를 막기 위해 신뢰도가 높은 구간에만 제한 적용.",
            f"- 기준 후보: `{STABLE}`.",
            "- 방식: 기본 예측은 HCOEF3 안정 후보를 유지하고, 표본 수/IQR/gap/기준가 level/완화 weight 조건을 만족한 샘플에만 basis-Huber 차이를 cap/strength로 제한해 반영.",
            "- 후보 선택: 반복 OOF 우선, fixed test는 최종 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}.",
            "- 조건부 routing은 일부 MAPE/MdAPE 개선 신호를 만들었는지 확인하되, 운영 후보는 p95 guard와 반복 OOF를 동시에 통과해야 함.",
            "",
            "## 2. 후보 선택표",
            "",
            markdown_table(selection.round(4), max_rows=24),
            "",
            "## 3. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4), max_rows=32),
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
                max_rows=24,
            ),
            "",
            "## 5. Routing 적용 범위",
            "",
            markdown_table(route_summary.round(4), max_rows=24),
            "",
            "## 6. 주요 계수",
            "",
            "- HCOEF3 안정 후보와 basis-Huber 모델의 표준화 계수.",
            markdown_table(coeffs.head(60).round(5)),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=50),
            "",
            "## 8. 다음 보정 방향",
            "",
            "- 조건부 routing 후보가 p95 guard를 통과하지 못하면, basis-Huber를 전체 모델로 쓰기보다 원인 분석용 피처로 유지.",
            "- routing 조건이 너무 좁아 개선폭이 작으면, `basis_relaxed_unit_area_log`를 HCOEF3 residual 피처로 직접 넣는 저차원 Huber 실험으로 이동.",
            "- 특정 기준가 level에서만 좋아지는 경우, 크기/표본 수/재료 구간별 segmented Huber 계수 실험으로 이동.",
            "",
            "## 9. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/repeated_validation_metrics.csv`",
            "- `outputs/routing_rules.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef6_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef6_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"])
    repeated_summary = summarize_repeated(repeated_metrics)
    fixed_metrics, fixed_predictions, coeffs, residuals, routes = fixed_confirmation(frames)
    selection = select_candidates(repeated_summary, fixed_metrics)

    out = EXP_DIR / "outputs"
    fixed_metrics.to_csv(out / "metrics.csv", index=False)
    repeated_metrics.to_csv(out / "repeated_validation_metrics.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    pd.concat([repeated_predictions, fixed_predictions], ignore_index=True).to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    routes.to_csv(out / "routing_rules.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": STABLE,
        "basis_configs": BASIS_CONFIGS,
        "routing_rules": ROUTING_RULES,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "selection_policy": "row/artist repeated OOF first; fixed test p95 must not worsen for operational candidate",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(repeated_summary, fixed_metrics, selection, coeffs, residuals, routes)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected top ---")
    print(selection.head(12).round(4).to_string(index=False))
    print("--- fixed test top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(12)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_vs_hcoef2", "delta_MAPE_vs_hcoef2", "delta_p95_APE_vs_hcoef2"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
