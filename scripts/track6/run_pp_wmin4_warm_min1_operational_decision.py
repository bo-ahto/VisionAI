#!/usr/bin/env python3
"""Run PP-WMIN4 Warm min1 operational decision validation.

This experiment compares the WMIN3 min1 SVC/HCOEF candidates against the
current PP258 operational candidate on the same Warm validation OOF and fixed
test rows. Candidate selection uses validation-only repeated stability and
replacement score; fixed test is recorded as final confirmation.
"""
from __future__ import annotations

import html
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]

PP258_DIR = REPO / "experiments" / "track6" / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
PP258_PREDS = PP258_DIR / "outputs" / "candidate_predictions.csv"
PP258_CONFIG = PP258_DIR / "artifacts" / "run_config.json"

WMIN3_DIR = REPO / "experiments" / "track6" / "PP-WMIN3_warm_min1_hcoef_refit"
WMIN3_PREDS = WMIN3_DIR / "outputs" / "candidate_predictions.csv"

EXP_ID = "PP-WMIN4"
EXP_SLUG = "PP-WMIN4_warm_min1_operational_decision"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin4_warm_min1_operational_decision_summary.md"

SEED = 20260612
REPEATS = 260
SAMPLE_FRAC = 0.72
EPS = 1e-12

WMIN3_LABELS = {
    "wmin2_svc_numeric_seed_mean_min1": "min1_svc_numeric_reference",
    "wmin3_min1_70_30_basis": "min1_70_30_basis",
    "wmin3_min1_hcoef_delta_transplant": "min1_huber_delta_transplant",
    "wmin3_min1_hcoef_refit_partial": "min1_huber_refit_partial",
    "wmin3_min1_hcoef_refit_svc_proxy": "min1_huber_refit_svc_proxy",
    "old_hcoef_stable_min5": "old_hcoef_stable_min5_reference",
    "old_current_70_30_min5": "old_current_70_30_min5_reference",
}


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(values, -50, 50))


def format_float(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    body = []
    for _, row in view.iterrows():
        body.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def metrics_from_arrays(actual_log: np.ndarray, actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    valid = np.isfinite(actual_log) & np.isfinite(actual_price) & np.isfinite(pred_log) & (actual_price > 0)
    if valid.sum() == 0:
        return {"n": 0, "MdAPE": np.nan, "MAPE": np.nan, "p95_APE": np.nan, "RMSE_log": np.nan}
    ape = np.abs(safe_exp(pred_log[valid]) - actual_price[valid]) / np.maximum(actual_price[valid], EPS)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log[valid] - actual_log[valid]) ** 2))),
    }


def load_pp258_reference_predictions() -> tuple[pd.DataFrame, dict[str, Any]]:
    config = json.loads(PP258_CONFIG.read_text(encoding="utf-8"))
    decision = config["selection_decision"]
    candidate_labels = {
        decision["operational_protocol_candidate"]: "current_pp258_operational_reference",
        decision["balanced_protocol_candidate"]: "current_pp258_balanced_reference",
        decision["p95_recovery_protocol_candidate"]: "current_pp258_p95_recovery_reference",
        decision["stability_protocol_candidate"]: "current_pp258_stability_reference",
        "hcoef_stable": "pp258_source_hcoef_stable",
        "current_70_30": "pp258_source_current_70_30",
    }
    needed = set(candidate_labels)
    usecols = [
        "candidate",
        "family",
        "item_id",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "pred_log",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(PP258_PREDS, usecols=usecols, chunksize=240_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise RuntimeError("No PP258 reference predictions were loaded")
    out = pd.concat(chunks, ignore_index=True)
    out["candidate_label"] = out["candidate"].map(candidate_labels).fillna(out["candidate"])
    out["source_experiment"] = "PP258"
    return out, config


def load_wmin3_candidates(reference_meta: pd.DataFrame) -> pd.DataFrame:
    usecols = [
        "candidate",
        "method",
        "scope",
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        "pred_log",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    wmin = pd.read_csv(WMIN3_PREDS, usecols=usecols)
    wmin = wmin[wmin["scope"].eq("fixed_confirmation") & wmin["candidate"].isin(WMIN3_LABELS)].copy()
    wmin["eval_split"] = np.where(wmin["split"].eq("validation"), "validation_oof", "test")
    wmin["candidate_label"] = wmin["candidate"].map(WMIN3_LABELS)
    wmin["family"] = "wmin_min1_operational_candidate"
    wmin["item_id"] = EXP_ID
    wmin["source_experiment"] = "PP-WMIN3"

    meta_cols = [
        "eval_split",
        "_track6_row_id",
        "confidence_tier",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    meta = reference_meta[meta_cols].drop_duplicates(["eval_split", "_track6_row_id"])
    wmin = wmin.merge(meta, on=["eval_split", "_track6_row_id"], how="left")
    return wmin


def base_meta_and_wide(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"].eq(eval_split)].copy()
    meta_cols = [
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    reference = subset[subset["candidate_label"].eq("current_pp258_operational_reference")][meta_cols].copy()
    reference = reference.drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    wide = subset.pivot_table(index="_track6_row_id", columns="candidate_label", values="pred_log", aggfunc="first")
    wide = wide.reindex(reference["_track6_row_id"]).reset_index(drop=True)
    return reference, wide


def fixed_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for eval_split in ["validation_oof", "test"]:
        meta, wide = base_meta_and_wide(predictions, eval_split)
        actual_log = meta["actual_log"].to_numpy(dtype=float)
        actual_price = meta["actual_price"].to_numpy(dtype=float)
        ref = wide["current_pp258_operational_reference"].to_numpy(dtype=float)
        ref_m = metrics_from_arrays(actual_log, actual_price, ref)
        for label in wide.columns:
            pred = wide[label].to_numpy(dtype=float)
            m = metrics_from_arrays(actual_log, actual_price, pred)
            rows.append(
                {
                    "candidate_label": label,
                    "eval_split": eval_split,
                    **m,
                    "delta_vs_current_pp258_MdAPE": m["MdAPE"] - ref_m["MdAPE"],
                    "delta_vs_current_pp258_MAPE": m["MAPE"] - ref_m["MAPE"],
                    "delta_vs_current_pp258_p95_APE": m["p95_APE"] - ref_m["p95_APE"],
                    "delta_vs_current_pp258_RMSE_log": m["RMSE_log"] - ref_m["RMSE_log"],
                }
            )
    return pd.DataFrame(rows).sort_values(["eval_split", "MAPE", "p95_APE"])


def risk_score(meta: pd.DataFrame) -> np.ndarray:
    qwidth = pd.to_numeric(meta["quantile_width"], errors="coerce").fillna(1.50).to_numpy(dtype=float)
    spread = pd.to_numeric(meta["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(meta["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    confidence = meta["confidence_tier"].fillna("medium_confidence").astype(str)
    price = meta["stable_price_band"].fillna("unknown_price").astype(str)
    return np.clip(
        0.38 * np.clip((qwidth - 1.20) / 0.95, 0.0, 1.0)
        + 0.22 * np.clip(spread / 0.18, 0.0, 1.0)
        + 0.14 * np.clip(gap / 0.06, 0.0, 1.0)
        + 0.16 * confidence.eq("low_confidence").to_numpy(dtype=float)
        + 0.10 * price.eq("very_high_price").to_numpy(dtype=float),
        0.0,
        1.0,
    )


def sample_positions(meta: pd.DataFrame) -> list[tuple[str, int, np.ndarray]]:
    rng = np.random.default_rng(SEED)
    all_positions = np.arange(len(meta))
    samples: list[tuple[str, int, np.ndarray]] = [("full_validation", 0, all_positions)]

    confidence = meta["confidence_tier"].fillna("medium_confidence").astype(str).to_numpy()
    for repeat in range(REPEATS):
        chosen: list[int] = []
        for tier in sorted(set(confidence)):
            idx = np.flatnonzero(confidence == tier)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            chosen.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("confidence_stratified_rows", repeat, np.array(sorted(chosen), dtype=int)))

    price = meta["stable_price_band"].fillna("unknown_price").astype(str).to_numpy()
    for repeat in range(REPEATS):
        chosen = []
        for band in sorted(set(price)):
            idx = np.flatnonzero(price == band)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            chosen.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("price_band_stratified_rows", repeat, np.array(sorted(chosen), dtype=int)))

    artists = meta["artist_key"].fillna("__missing_artist__").astype(str)
    unique_artists = np.array(sorted(artists.unique()))
    for repeat in range(REPEATS):
        artist_n = max(1, int(round(len(unique_artists) * SAMPLE_FRAC)))
        chosen_artists = set(rng.choice(unique_artists, size=artist_n, replace=False).tolist())
        idx = np.flatnonzero(artists.isin(chosen_artists).to_numpy())
        samples.append(("artist_group_holdout", repeat, idx))

    for repeat in range(REPEATS):
        n = max(1, int(round(len(all_positions) * SAMPLE_FRAC)))
        samples.append(("row_bootstrap", repeat, rng.choice(all_positions, size=n, replace=True)))

    risk = risk_score(meta)
    risk_idx = np.flatnonzero(risk >= float(np.quantile(risk, 0.58)))
    if len(risk_idx) > 10:
        for repeat in range(REPEATS):
            n = max(8, int(round(len(risk_idx) * 0.78)))
            samples.append(("risk_focus_bootstrap", repeat, rng.choice(risk_idx, size=n, replace=True)))
    return samples


def metric_for_positions(meta: pd.DataFrame, wide: pd.DataFrame, positions: np.ndarray) -> pd.DataFrame:
    actual_log = meta.iloc[positions]["actual_log"].to_numpy(dtype=float)
    actual_price = meta.iloc[positions]["actual_price"].to_numpy(dtype=float)
    pred = wide.iloc[positions].to_numpy(dtype=float)
    valid = np.isfinite(actual_log) & np.isfinite(actual_price) & (actual_price > 0)
    pred = pred[valid]
    actual_log = actual_log[valid]
    actual_price = actual_price[valid]
    ape = np.abs(safe_exp(pred) - actual_price[:, None]) / np.maximum(actual_price[:, None], EPS)
    return pd.DataFrame(
        {
            "candidate_label": list(wide.columns),
            "n": int(valid.sum()),
            "MdAPE": np.nanmedian(ape, axis=0),
            "MAPE": np.nanmean(ape, axis=0),
            "p95_APE": np.nanquantile(ape, 0.95, axis=0),
            "RMSE_log": np.sqrt(np.nanmean((pred - actual_log[:, None]) ** 2, axis=0)),
        }
    )


def repeated_validation_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    meta, wide = base_meta_and_wide(predictions, "validation_oof")
    rows: list[pd.DataFrame] = []
    for scenario, repeat, positions in sample_positions(meta):
        metrics = metric_for_positions(meta, wide, positions)
        reference = metrics[metrics["candidate_label"].eq("current_pp258_operational_reference")].iloc[0]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            metrics[f"delta_vs_current_pp258_{metric}"] = metrics[metric] - float(reference[metric])
        metrics["wins_current_pp258_MdAPE"] = metrics["delta_vs_current_pp258_MdAPE"] < 0
        metrics["wins_current_pp258_MAPE"] = metrics["delta_vs_current_pp258_MAPE"] < 0
        metrics["wins_current_pp258_p95"] = metrics["delta_vs_current_pp258_p95_APE"] < 0
        metrics["wins_current_pp258_all3"] = (
            metrics["wins_current_pp258_MdAPE"] & metrics["wins_current_pp258_MAPE"] & metrics["wins_current_pp258_p95"]
        )
        metrics["scenario"] = scenario
        metrics["repeat"] = repeat
        rows.append(metrics)
    detail = pd.concat(rows, ignore_index=True)
    summary = (
        detail.groupby(["candidate_label", "scenario"])
        .agg(
            repeats=("repeat", "nunique"),
            mean_MdAPE=("MdAPE", "mean"),
            mean_MAPE=("MAPE", "mean"),
            mean_p95_APE=("p95_APE", "mean"),
            mean_delta_vs_current_pp258_MdAPE=("delta_vs_current_pp258_MdAPE", "mean"),
            mean_delta_vs_current_pp258_MAPE=("delta_vs_current_pp258_MAPE", "mean"),
            mean_delta_vs_current_pp258_p95_APE=("delta_vs_current_pp258_p95_APE", "mean"),
            current_pp258_MdAPE_win_rate=("wins_current_pp258_MdAPE", "mean"),
            current_pp258_MAPE_win_rate=("wins_current_pp258_MAPE", "mean"),
            current_pp258_p95_win_rate=("wins_current_pp258_p95", "mean"),
            current_pp258_all3_win_rate=("wins_current_pp258_all3", "mean"),
        )
        .reset_index()
    )
    summary["validation_stability_score"] = (
        summary["mean_delta_vs_current_pp258_MAPE"].fillna(9)
        + 0.70 * np.maximum(summary["mean_delta_vs_current_pp258_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(0.50 - summary["current_pp258_MAPE_win_rate"].fillna(0), 0)
        + 0.10 * np.maximum(0.50 - summary["current_pp258_p95_win_rate"].fillna(0), 0)
    )
    return detail, summary


def aggregate_decision(fixed: pd.DataFrame, repeated_summary: pd.DataFrame) -> pd.DataFrame:
    scenario_summary = (
        repeated_summary.groupby("candidate_label")
        .agg(
            scenario_count=("scenario", "nunique"),
            validation_avg_delta_MdAPE_vs_current_pp258=("mean_delta_vs_current_pp258_MdAPE", "mean"),
            validation_avg_delta_MAPE_vs_current_pp258=("mean_delta_vs_current_pp258_MAPE", "mean"),
            validation_avg_delta_p95_vs_current_pp258=("mean_delta_vs_current_pp258_p95_APE", "mean"),
            validation_avg_MdAPE_win_rate=("current_pp258_MdAPE_win_rate", "mean"),
            validation_avg_MAPE_win_rate=("current_pp258_MAPE_win_rate", "mean"),
            validation_avg_p95_win_rate=("current_pp258_p95_win_rate", "mean"),
            validation_avg_all3_win_rate=("current_pp258_all3_win_rate", "mean"),
            validation_avg_stability_score=("validation_stability_score", "mean"),
        )
        .reset_index()
    )
    validation = fixed[fixed["eval_split"].eq("validation_oof")][
        [
            "candidate_label",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_vs_current_pp258_MdAPE",
            "delta_vs_current_pp258_MAPE",
            "delta_vs_current_pp258_p95_APE",
        ]
    ].rename(
        columns={
            "MdAPE": "fixed_validation_MdAPE",
            "MAPE": "fixed_validation_MAPE",
            "p95_APE": "fixed_validation_p95_APE",
            "RMSE_log": "fixed_validation_RMSE_log",
            "delta_vs_current_pp258_MdAPE": "fixed_validation_delta_MdAPE_vs_current_pp258",
            "delta_vs_current_pp258_MAPE": "fixed_validation_delta_MAPE_vs_current_pp258",
            "delta_vs_current_pp258_p95_APE": "fixed_validation_delta_p95_vs_current_pp258",
        }
    )
    test = fixed[fixed["eval_split"].eq("test")][
        [
            "candidate_label",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_vs_current_pp258_MdAPE",
            "delta_vs_current_pp258_MAPE",
            "delta_vs_current_pp258_p95_APE",
        ]
    ].rename(
        columns={
            "MdAPE": "fixed_test_MdAPE",
            "MAPE": "fixed_test_MAPE",
            "p95_APE": "fixed_test_p95_APE",
            "RMSE_log": "fixed_test_RMSE_log",
            "delta_vs_current_pp258_MdAPE": "fixed_test_delta_MdAPE_vs_current_pp258",
            "delta_vs_current_pp258_MAPE": "fixed_test_delta_MAPE_vs_current_pp258",
            "delta_vs_current_pp258_p95_APE": "fixed_test_delta_p95_vs_current_pp258",
        }
    )
    out = scenario_summary.merge(validation, on="candidate_label", how="left").merge(test, on="candidate_label", how="left")
    out["validation_replacement_score"] = (
        out["fixed_validation_delta_MAPE_vs_current_pp258"].fillna(9)
        + 0.70 * np.maximum(out["fixed_validation_delta_p95_vs_current_pp258"].fillna(9), 0)
        + 0.50 * np.maximum(out["validation_avg_delta_MAPE_vs_current_pp258"].fillna(9), 0)
        + 0.35 * np.maximum(out["validation_avg_delta_p95_vs_current_pp258"].fillna(9), 0)
        + 0.04 * np.maximum(0.50 - out["validation_avg_MAPE_win_rate"].fillna(0), 0)
    )
    out["fixed_confirmation_score"] = (
        out["fixed_test_delta_MAPE_vs_current_pp258"].fillna(9)
        + 0.70 * np.maximum(out["fixed_test_delta_p95_vs_current_pp258"].fillna(9), 0)
    )
    out["is_reference_baseline"] = out["candidate_label"].eq("current_pp258_operational_reference")
    out.loc[out["is_reference_baseline"], ["validation_replacement_score", "fixed_confirmation_score"]] = 0.0
    out["passes_validation_gate"] = (
        (out["fixed_validation_delta_MAPE_vs_current_pp258"] <= 0)
        & (out["fixed_validation_delta_p95_vs_current_pp258"] <= 0)
        & (out["validation_avg_MAPE_win_rate"] >= 0.50)
        & (out["validation_avg_p95_win_rate"] >= 0.50)
    )
    out["passes_fixed_confirmation"] = (
        (out["fixed_test_delta_MAPE_vs_current_pp258"] <= 0)
        & (out["fixed_test_delta_p95_vs_current_pp258"] <= 0)
        & (out["fixed_test_delta_MdAPE_vs_current_pp258"] <= 0)
    )
    out.loc[out["is_reference_baseline"], ["passes_validation_gate", "passes_fixed_confirmation"]] = True
    return out.sort_values(["validation_replacement_score", "fixed_validation_MAPE", "fixed_validation_p95_APE"])


def choose_decision(aggregate: pd.DataFrame) -> dict[str, Any]:
    new_pool = aggregate[aggregate["candidate_label"].str.startswith("min1_", na=False)].copy()
    gated = new_pool[new_pool["passes_validation_gate"]].copy()
    if gated.empty:
        selected = new_pool.sort_values(["validation_replacement_score", "fixed_validation_MAPE"]).iloc[0]
        status = "hold"
        reason = "validation gate를 모두 통과한 min1 후보가 없어 운영 교체는 보류한다."
    else:
        selected = gated.sort_values(["validation_replacement_score", "fixed_validation_MAPE", "validation_avg_p95_win_rate"], ascending=[True, True, False]).iloc[0]
        if bool(selected["passes_fixed_confirmation"]):
            status = "adopt_candidate"
            reason = "validation gate를 통과했고 fixed test 확인에서도 기존 PP258 운영 후보보다 MdAPE/MAPE/p95가 모두 낮다."
        else:
            status = "validation_pass_fixed_hold"
            reason = "validation gate는 통과했지만 fixed test 확인에서 일부 지표가 기존 PP258보다 높아 운영 교체는 보류한다."
    return {
        "decision_status": status,
        "selected_candidate_label": selected["candidate_label"],
        "reason": reason,
        "selected_fixed_validation_MdAPE": float(selected["fixed_validation_MdAPE"]),
        "selected_fixed_validation_MAPE": float(selected["fixed_validation_MAPE"]),
        "selected_fixed_validation_p95_APE": float(selected["fixed_validation_p95_APE"]),
        "selected_fixed_test_MdAPE": float(selected["fixed_test_MdAPE"]),
        "selected_fixed_test_MAPE": float(selected["fixed_test_MAPE"]),
        "selected_fixed_test_p95_APE": float(selected["fixed_test_p95_APE"]),
        "selected_validation_MAPE_win_rate": float(selected["validation_avg_MAPE_win_rate"]),
        "selected_validation_p95_win_rate": float(selected["validation_avg_p95_win_rate"]),
        "selected_validation_replacement_score": float(selected["validation_replacement_score"]),
    }


def render_reports(
    fixed: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    aggregate: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    agg_cols = [
        "candidate_label",
        "passes_validation_gate",
        "passes_fixed_confirmation",
        "fixed_validation_MdAPE",
        "fixed_validation_MAPE",
        "fixed_validation_p95_APE",
        "validation_avg_MAPE_win_rate",
        "validation_avg_p95_win_rate",
        "validation_replacement_score",
        "fixed_test_MdAPE",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_MAPE_vs_current_pp258",
        "fixed_test_delta_p95_vs_current_pp258",
    ]
    fixed_cols = [
        "candidate_label",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_vs_current_pp258_MdAPE",
        "delta_vs_current_pp258_MAPE",
        "delta_vs_current_pp258_p95_APE",
    ]
    scenario_cols = [
        "candidate_label",
        "scenario",
        "repeats",
        "mean_MdAPE",
        "mean_MAPE",
        "mean_p95_APE",
        "mean_delta_vs_current_pp258_MAPE",
        "mean_delta_vs_current_pp258_p95_APE",
        "current_pp258_MAPE_win_rate",
        "current_pp258_p95_win_rate",
        "current_pp258_all3_win_rate",
    ]
    selected_scenarios = repeated_summary[repeated_summary["candidate_label"].eq(decision["selected_candidate_label"])].copy()
    verdict = (
        f"{decision['decision_status']}: {decision['selected_candidate_label']} 선택. "
        f"validation {decision['selected_fixed_validation_MdAPE']:.6f}/"
        f"{decision['selected_fixed_validation_MAPE']:.6f}/"
        f"{decision['selected_fixed_validation_p95_APE']:.6f}, "
        f"fixed test {decision['selected_fixed_test_MdAPE']:.6f}/"
        f"{decision['selected_fixed_test_MAPE']:.6f}/"
        f"{decision['selected_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-WMIN4 Warm min1 operational decision validation 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 선택 기준: validation OOF 반복 안정성 + validation replacement score",
            "- fixed test: 최종 확인용으로만 기록",
            f"- 결론: {verdict}",
            f"- 판단 근거: {decision['reason']}",
            "",
            "## 후보별 교체 판단",
            markdown_table(aggregate, agg_cols, 80),
            "",
            "## fixed validation/test 지표",
            markdown_table(fixed, fixed_cols, 120),
            "",
            "## 선택 후보 validation 반복 시나리오",
            markdown_table(selected_scenarios, scenario_cols, 40),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-WMIN4 Warm min1 operational decision validation 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1320px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 10px; font-size:30px; }} h2 {{ margin:36px 0 12px; padding-top:18px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:22px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-WMIN4 Warm min1 operational decision validation 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>{html.escape(decision['reason'])}</div>
<h2>1. 후보별 교체 판단</h2>{table_html(aggregate, agg_cols, 80)}
<h2>2. fixed validation/test 지표</h2>{table_html(fixed, fixed_cols, 120)}
<h2>3. 선택 후보 validation 반복 시나리오</h2>{table_html(selected_scenarios, scenario_cols, 40)}
<h2>4. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    pp258, pp258_config = load_pp258_reference_predictions()
    ref_meta = pp258[pp258["candidate_label"].eq("current_pp258_operational_reference")].copy()
    wmin3 = load_wmin3_candidates(ref_meta)
    predictions = pd.concat([pp258, wmin3], ignore_index=True, sort=False)
    predictions = predictions.drop_duplicates(["candidate_label", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)

    fixed = fixed_metrics(predictions)
    repeated_detail, repeated_summary = repeated_validation_metrics(predictions)
    aggregate = aggregate_decision(fixed, repeated_summary)
    decision = choose_decision(aggregate)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selection_policy": "validation OOF repeated stability and validation replacement score only; fixed test is final confirmation",
        "reference_candidate_label": "current_pp258_operational_reference",
        "reference_experiment": str(PP258_DIR.relative_to(REPO)),
        "wmin3_experiment": str(WMIN3_DIR.relative_to(REPO)),
        "validation_rows": int(predictions[predictions["eval_split"].eq("validation_oof")]["_track6_row_id"].nunique()),
        "test_rows": int(predictions[predictions["eval_split"].eq("test")]["_track6_row_id"].nunique()),
        "candidate_labels": sorted(predictions["candidate_label"].unique().tolist()),
        "repeats_per_scenario": REPEATS,
        "sample_frac": SAMPLE_FRAC,
        "pp258_selection_decision": pp258_config["selection_decision"],
        "decision": decision,
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    fixed.to_csv(OUT_DIR / "fixed_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "operational_decision_aggregate.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(fixed, repeated_summary, aggregate, decision, config)
    (REPORT_DIR / "wmin4_operational_decision_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "wmin4_operational_decision_result.html").write_text(report_html, encoding="utf-8")
    DOC_SUMMARY.write_text(report_md, encoding="utf-8")
    (EXP_DIR / "README.md").write_text(report_md, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nDecision aggregate:")
    print(
        aggregate[
            [
                "candidate_label",
                "passes_validation_gate",
                "passes_fixed_confirmation",
                "fixed_validation_MdAPE",
                "fixed_validation_MAPE",
                "fixed_validation_p95_APE",
                "validation_avg_MAPE_win_rate",
                "validation_avg_p95_win_rate",
                "validation_replacement_score",
                "fixed_test_MdAPE",
                "fixed_test_MAPE",
                "fixed_test_p95_APE",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
