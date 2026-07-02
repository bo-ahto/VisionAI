#!/usr/bin/env python3
"""Run PP-HCOEF15: latest-label stress test for Warm Huber candidates.

This experiment does not create a new correction from the 0604 labels. The 0604
labels are treated as external stress-test data only. It compares:

- the research HCOEF stable candidate,
- the v0.1 70:30 reference candidate,
- the operational service-primary candidate and its components.

The goal is to understand whether the current HCOEF winner remains robust on
new operational-style labels, and whether the operational component that looks
strong on 0604 should become an input for a future OOF-validated HCOEF
experiment.
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
EXP_ID = "PP-HCOEF15"
EXP_SLUG = "PP-HCOEF15_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

HCOEF14_PREDICTIONS = REPO / "experiments" / "track6" / "PP-HCOEF14_warm_huber_price_basis_coefficient_refinement" / "outputs" / "candidate_predictions.csv"
HCOEF14_METRICS = REPO / "experiments" / "track6" / "PP-HCOEF14_warm_huber_price_basis_coefficient_refinement" / "outputs" / "metrics.csv"
HCOEF14_COEFFICIENTS = REPO / "experiments" / "track6" / "PP-HCOEF14_warm_huber_price_basis_coefficient_refinement" / "outputs" / "feature_coefficients.csv"
OPERATIONAL_0604 = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational" / "outputs" / "0604_evaluation" / "operational_predictions_with_actual.csv"

REFERENCE = "current_70_30"
STABLE = "hcoef2_size_reliability_cap005_s050"
SEED = 20260608
N_BOOTSTRAP = 1000

RESEARCH_CANDIDATES = [
    REFERENCE,
    STABLE,
    "hcoef14_shrink_iqr_mid_high_keep050",
    "hcoef14_seg_iqr_cap002_s025",
]

OPERATIONAL_CANDIDATES = [
    {
        "candidate": "service_primary_ppv8_operational",
        "method": "operational_service_primary",
        "pred_log_col": "service_primary_pred_log",
        "pred_price_col": "service_primary_pred_price_krw",
        "description": "운영 v0.1 서비스 기본 출력. 현재 파일에서는 pp_v8_compact_blend_mape_guarded와 동일.",
    },
    {
        "candidate": "pp_v8_compact_blend_mape_guarded_operational",
        "method": "operational_component",
        "pred_log_col": "pp_v8_compact_blend_mape_guarded_pred_log",
        "pred_price_col": "pp_v8_compact_blend_mape_guarded_pred_price_krw",
        "description": "운영 0604에서 가장 낮은 외부 MdAPE/MAPE/p95를 보인 PP-V8 계열 component.",
    },
    {
        "candidate": "v01_operational_70_30",
        "method": "operational_reference_70_30",
        "pred_log_col": "v01_operational_pred_log",
        "pred_price_col": "v01_operational_pred_price_krw",
        "description": "운영 feature pipeline에서 생성된 v0.1 70:30 후보.",
    },
    {
        "candidate": "svc_numeric_seed_mean",
        "method": "operational_component",
        "pred_log_col": "svc_numeric_seed_mean_pred_log",
        "pred_price_col": "svc_numeric_seed_mean_pred_price_krw",
        "description": "유사 작품 기반 가격 피처 단독 component.",
    },
    {
        "candidate": "pp_v2_defensive",
        "method": "operational_component",
        "pred_log_col": "pp_v2_defensive_pred_log",
        "pred_price_col": "pp_v2_defensive_pred_price_krw",
        "description": "운영 artifact에 포함된 방어형 Warm component.",
    },
    {
        "candidate": "l10_generated_bucket_seq",
        "method": "operational_component",
        "pred_log_col": "l10_generated_bucket_seq_pred_log",
        "pred_price_col": "l10_generated_bucket_seq_pred_price_krw",
        "description": "Quantile/Huber/CatBoost 순차 후보 계열 운영 component.",
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray, pred_price: np.ndarray | None = None) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    if pred_price is None:
        pred_price = np.exp(pred_log)
    pred_price = np.asarray(pred_price, dtype=float)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((actual_log - pred_log) ** 2))),
        "median_ratio": float(np.nanmedian(pred_price / np.clip(actual_price, 1.0, None))),
        "over_2x_n": int(np.nansum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual_price * 0.5)),
        "over_3x_n": int(np.nansum(pred_price >= actual_price * 3.0)),
        "under_1_3x_n": int(np.nansum(pred_price <= actual_price / 3.0)),
    }


def load_research_predictions() -> pd.DataFrame:
    source = pd.read_csv(HCOEF14_PREDICTIONS, low_memory=False)
    frame = source[source["split"].eq("0604_ex50") & source["candidate"].isin(RESEARCH_CANDIDATES)].copy()
    frame["candidate_source"] = "research_hcoef"
    frame["actual_price_krw"] = frame["actual_price"].astype(float)
    frame["actual_log_krw"] = frame["actual_log"].astype(float)
    frame["pred_price_krw"] = frame["pred_price"].astype(float)
    frame["pred_log_krw"] = frame["pred_log"].astype(float)
    return frame[
        [
            "candidate_source",
            "candidate",
            "method",
            "split",
            "_track6_row_id",
            "artist_key",
            "artist_name_ko",
            "actual_price_krw",
            "actual_log_krw",
            "pred_log_krw",
            "pred_price_krw",
            "residual_log",
            "ape",
            "risk_cause",
            "pred_bin",
            "size_bin",
            "basis_n_bucket",
            "basis_iqr_bucket",
            "basis_level_simple",
            "basis_gap_sign",
            "ppv8_gap_sign",
        ]
    ]


def load_operational_predictions(stress_ids: set[int]) -> pd.DataFrame:
    source = pd.read_csv(OPERATIONAL_0604, low_memory=False)
    source = source[source["_track6_row_id"].isin(stress_ids)].copy()
    rows: list[pd.DataFrame] = []
    for config in OPERATIONAL_CANDIDATES:
        pred_log = pd.to_numeric(source[config["pred_log_col"]], errors="coerce")
        pred_price = pd.to_numeric(source[config["pred_price_col"]], errors="coerce")
        actual_price = pd.to_numeric(source["actual_price_krw"], errors="coerce")
        valid = pred_log.notna() & pred_price.notna() & actual_price.gt(0)
        part = pd.DataFrame(
            {
                "candidate_source": "operational_v0.1",
                "candidate": config["candidate"],
                "method": config["method"],
                "split": "0604_ex50",
                "_track6_row_id": source.loc[valid, "_track6_row_id"].astype(int).to_numpy(),
                "artist_key": source.loc[valid, "artist_key"].astype(str).to_numpy(),
                "artist_name_ko": source.loc[valid, "artist_name"].astype(str).to_numpy(),
                "actual_price_krw": actual_price.loc[valid].to_numpy(dtype=float),
                "actual_log_krw": np.log(actual_price.loc[valid].to_numpy(dtype=float)),
                "pred_log_krw": pred_log.loc[valid].to_numpy(dtype=float),
                "pred_price_krw": pred_price.loc[valid].to_numpy(dtype=float),
                "residual_log": np.log(actual_price.loc[valid].to_numpy(dtype=float)) - pred_log.loc[valid].to_numpy(dtype=float),
                "ape": np.abs(pred_price.loc[valid].to_numpy(dtype=float) - actual_price.loc[valid].to_numpy(dtype=float)) / np.clip(actual_price.loc[valid].to_numpy(dtype=float), 1.0, None),
                "risk_cause": "",
                "pred_bin": "",
                "size_bin": source.loc[valid, "size_bucket"].astype(str).to_numpy() if "size_bucket" in source.columns else "",
                "basis_n_bucket": "",
                "basis_iqr_bucket": "",
                "basis_level_simple": source.loc[valid, "svc_group_level"].astype(str).to_numpy(),
                "basis_gap_sign": "",
                "ppv8_gap_sign": "",
                "svc_group_level": source.loc[valid, "svc_group_level"].astype(str).to_numpy(),
                "svc_coverage_tier": source.loc[valid, "svc_coverage_tier"].astype(str).to_numpy(),
                "svc_group_n": pd.to_numeric(source.loc[valid, "svc_group_n"], errors="coerce").to_numpy(dtype=float),
                "l10_price_range_ratio": pd.to_numeric(source.loc[valid, "l10_price_range_ratio"], errors="coerce").to_numpy(dtype=float),
                "service_confidence_tier": source.loc[valid, "service_confidence_tier"].astype(str).to_numpy(),
                "title": source.loc[valid, "title"].astype(str).to_numpy(),
                "artist_name": source.loc[valid, "artist_name"].astype(str).to_numpy(),
                "actual_currency": source.loc[valid, "actual_currency"].astype(str).to_numpy(),
                "actual_price_usd_equiv": pd.to_numeric(source.loc[valid, "actual_price_usd_equiv"], errors="coerce").to_numpy(dtype=float),
            }
        )
        rows.append(part)
    return pd.concat(rows, ignore_index=True, sort=False)


def attach_operational_context(predictions: pd.DataFrame) -> pd.DataFrame:
    op = pd.read_csv(OPERATIONAL_0604, low_memory=False)
    context_cols = [
        "_track6_row_id",
        "title",
        "artist_name",
        "actual_currency",
        "actual_price_usd_equiv",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "l10_price_range_ratio",
        "service_confidence_tier",
    ]
    existing = [col for col in context_cols if col in op.columns]
    context = op[existing].drop_duplicates("_track6_row_id")
    out = predictions.merge(context, on="_track6_row_id", how="left", suffixes=("", "_op"))
    for col in ["svc_group_level", "svc_coverage_tier", "service_confidence_tier"]:
        alt = f"{col}_op"
        if alt in out.columns:
            out[col] = out[col].where(out[col].notna() & out[col].astype(str).ne(""), out[alt])
            out = out.drop(columns=[alt])
    for col in ["svc_group_n", "l10_price_range_ratio", "title", "artist_name", "actual_currency", "actual_price_usd_equiv"]:
        alt = f"{col}_op"
        if alt in out.columns:
            out[col] = out[col].where(out[col].notna(), out[alt])
            out = out.drop(columns=[alt])
    return out


def actual_price_band(usd: pd.Series) -> pd.Series:
    bins = [-np.inf, 100, 500, 1_000, 5_000, 20_000, 100_000, np.inf]
    labels = ["under_100usd", "100_500usd", "500_1k_usd", "1k_5k_usd", "5k_20k_usd", "20k_100k_usd", "100k_plus_usd"]
    return pd.cut(pd.to_numeric(usd, errors="coerce"), bins=bins, labels=labels).astype(str)


def qcut_label(series: pd.Series, labels: list[str]) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    try:
        return pd.qcut(values, q=len(labels), labels=labels, duplicates="drop").astype(str)
    except ValueError:
        return pd.Series(["unknown"] * len(series), index=series.index)


def build_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    research = load_research_predictions()
    stress_ids = set(research["_track6_row_id"].astype(int).unique())
    operational = load_operational_predictions(stress_ids)
    combined = pd.concat([research, operational], ignore_index=True, sort=False)
    combined = attach_operational_context(combined)
    combined["actual_price_band"] = actual_price_band(combined["actual_price_usd_equiv"])
    combined["svc_group_n_band"] = qcut_label(combined["svc_group_n"], ["n_q1", "n_q2", "n_q3", "n_q4"])
    combined["l10_range_ratio_band"] = qcut_label(combined["l10_price_range_ratio"], ["range_low", "range_mid", "range_high"])
    combined["prediction_ratio"] = combined["pred_price_krw"] / np.clip(combined["actual_price_krw"], 1.0, None)
    combined["residual_log"] = combined["actual_log_krw"] - combined["pred_log_krw"]
    combined["ape"] = np.abs(combined["pred_price_krw"] - combined["actual_price_krw"]) / np.clip(combined["actual_price_krw"], 1.0, None)

    h_actual = research[research["candidate"].eq(STABLE)][["_track6_row_id", "actual_price_krw"]].rename(columns={"actual_price_krw": "hcoef_actual_price_krw"})
    op_actual = pd.read_csv(OPERATIONAL_0604, usecols=["_track6_row_id", "actual_price_krw"], low_memory=False)
    audit = h_actual.merge(op_actual, on="_track6_row_id", how="left")
    audit["actual_price_abs_diff"] = (audit["hcoef_actual_price_krw"] - audit["actual_price_krw"]).abs()
    audit["actual_price_match"] = audit["actual_price_abs_diff"].le(1e-6)
    return combined, audit


def candidate_metric_rows(predictions: pd.DataFrame, scope: str, segment_column: str = "", segment_value: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    stable = predictions[predictions["candidate"].eq(STABLE)]
    reference = predictions[predictions["candidate"].eq(REFERENCE)]
    stable_metric = metric(stable["actual_price_krw"].to_numpy(), stable["actual_log_krw"].to_numpy(), stable["pred_log_krw"].to_numpy(), stable["pred_price_krw"].to_numpy()) if not stable.empty else {}
    reference_metric = metric(reference["actual_price_krw"].to_numpy(), reference["actual_log_krw"].to_numpy(), reference["pred_log_krw"].to_numpy(), reference["pred_price_krw"].to_numpy()) if not reference.empty else {}
    for candidate, group in predictions.groupby("candidate", observed=False):
        m = metric(
            group["actual_price_krw"].to_numpy(dtype=float),
            group["actual_log_krw"].to_numpy(dtype=float),
            group["pred_log_krw"].to_numpy(dtype=float),
            group["pred_price_krw"].to_numpy(dtype=float),
        )
        row = {
            "scope": scope,
            "split": "0604_ex50",
            "candidate": candidate,
            "candidate_source": str(group["candidate_source"].iloc[0]),
            "method": str(group["method"].iloc[0]),
            "n": int(len(group)),
            "segment_column": segment_column,
            "segment_value": segment_value,
            **m,
        }
        if stable_metric:
            row.update({
                "delta_MdAPE_vs_stable": m["MdAPE"] - stable_metric["MdAPE"],
                "delta_MAPE_vs_stable": m["MAPE"] - stable_metric["MAPE"],
                "delta_p95_APE_vs_stable": m["p95_APE"] - stable_metric["p95_APE"],
                "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_metric["RMSE_log"],
            })
        if reference_metric:
            row.update({
                "delta_MdAPE_vs_reference": m["MdAPE"] - reference_metric["MdAPE"],
                "delta_MAPE_vs_reference": m["MAPE"] - reference_metric["MAPE"],
                "delta_p95_APE_vs_reference": m["p95_APE"] - reference_metric["p95_APE"],
                "delta_RMSE_log_vs_reference": m["RMSE_log"] - reference_metric["RMSE_log"],
            })
        rows.append(row)
    return rows


def build_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = candidate_metric_rows(predictions, "overall")
    segment_columns = [
        "actual_price_band",
        "svc_coverage_tier",
        "svc_group_level",
        "service_confidence_tier",
        "l10_range_ratio_band",
    ]
    for column in segment_columns:
        if column not in predictions.columns:
            continue
        for value, group in predictions.groupby(column, dropna=False, observed=False):
            if len(group["_track6_row_id"].unique()) < 20:
                continue
            rows.extend(candidate_metric_rows(group, f"{column}={value}", column, str(value)))
    return pd.DataFrame(rows)


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in predictions.groupby("candidate", observed=False):
        residual = group["residual_log"].to_numpy(dtype=float)
        ape = group["ape"].to_numpy(dtype=float)
        rows.append(
            {
                "split": "0604_ex50",
                "candidate": candidate,
                "candidate_source": str(group["candidate_source"].iloc[0]),
                "n": int(len(group)),
                "median_residual_log": float(np.nanmedian(residual)),
                "mean_residual_log": float(np.nanmean(residual)),
                "residual_std": float(np.nanstd(residual)),
                "ape_median": float(np.nanmedian(ape)),
                "ape_mean": float(np.nanmean(ape)),
                "ape_p95": float(np.nanquantile(ape, 0.95)),
                "ape_gt_50pct_n": int(np.nansum(ape > 0.5)),
                "ape_gt_100pct_n": int(np.nansum(ape > 1.0)),
                "over_2x_n": int(np.nansum(group["pred_price_krw"].to_numpy(dtype=float) >= group["actual_price_krw"].to_numpy(dtype=float) * 2.0)),
                "under_half_n": int(np.nansum(group["pred_price_krw"].to_numpy(dtype=float) <= group["actual_price_krw"].to_numpy(dtype=float) * 0.5)),
            }
        )
    return pd.DataFrame(rows)


def pivot_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    value_cols = ["pred_price_krw", "pred_log_krw", "ape", "prediction_ratio"]
    index_cols = [
        "_track6_row_id",
        "title",
        "artist_name",
        "artist_key",
        "actual_price_krw",
        "actual_log_krw",
        "actual_currency",
        "actual_price_usd_equiv",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "l10_price_range_ratio",
        "actual_price_band",
        "service_confidence_tier",
    ]
    base = predictions[index_cols].drop_duplicates("_track6_row_id")
    wide = base.copy()
    for candidate, group in predictions.groupby("candidate", observed=False):
        one = group[["_track6_row_id", *value_cols]].copy()
        one = one.rename(columns={col: f"{candidate}_{col}" for col in value_cols})
        wide = wide.merge(one, on="_track6_row_id", how="left")
    return wide


def bootstrap_summary(wide: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    actual_price = wide["actual_price_krw"].to_numpy(dtype=float)
    actual_log = wide["actual_log_krw"].to_numpy(dtype=float)
    row_indices = np.arange(len(wide))
    artists = wide["artist_key"].astype(str).to_numpy()
    unique_artists = np.unique(artists)
    artist_to_idx = {artist: np.flatnonzero(artists == artist) for artist in unique_artists}

    baseline_metrics = {}
    for baseline in [STABLE, REFERENCE]:
        if f"{baseline}_pred_log_krw" not in wide.columns:
            continue
        baseline_metrics[baseline] = metric(
            actual_price,
            actual_log,
            wide[f"{baseline}_pred_log_krw"].to_numpy(dtype=float),
            wide[f"{baseline}_pred_price_krw"].to_numpy(dtype=float),
        )

    for scheme in ["row_bootstrap", "artist_bootstrap"]:
        for candidate in candidates:
            if f"{candidate}_pred_log_krw" not in wide.columns:
                continue
            candidate_pred_log = wide[f"{candidate}_pred_log_krw"].to_numpy(dtype=float)
            candidate_pred_price = wide[f"{candidate}_pred_price_krw"].to_numpy(dtype=float)
            for baseline, base_metric in baseline_metrics.items():
                if candidate == baseline:
                    continue
                baseline_pred_log = wide[f"{baseline}_pred_log_krw"].to_numpy(dtype=float)
                baseline_pred_price = wide[f"{baseline}_pred_price_krw"].to_numpy(dtype=float)
                deltas: list[dict[str, float]] = []
                for _ in range(N_BOOTSTRAP):
                    if scheme == "row_bootstrap":
                        idx = rng.choice(row_indices, size=len(row_indices), replace=True)
                    else:
                        sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                        idx = np.concatenate([artist_to_idx[artist] for artist in sampled_artists])
                    cm = metric(actual_price[idx], actual_log[idx], candidate_pred_log[idx], candidate_pred_price[idx])
                    bm = metric(actual_price[idx], actual_log[idx], baseline_pred_log[idx], baseline_pred_price[idx])
                    deltas.append({
                        "MdAPE": cm["MdAPE"] - bm["MdAPE"],
                        "MAPE": cm["MAPE"] - bm["MAPE"],
                        "p95_APE": cm["p95_APE"] - bm["p95_APE"],
                        "RMSE_log": cm["RMSE_log"] - bm["RMSE_log"],
                    })
                delta = pd.DataFrame(deltas)
                point = metric(actual_price, actual_log, candidate_pred_log, candidate_pred_price)
                rows.append(
                    {
                        "summary_type": scheme,
                        "split": "0604_ex50",
                        "candidate": candidate,
                        "baseline": baseline,
                        "n_bootstrap": N_BOOTSTRAP,
                        "point_delta_MdAPE": point["MdAPE"] - base_metric["MdAPE"],
                        "point_delta_MAPE": point["MAPE"] - base_metric["MAPE"],
                        "point_delta_p95_APE": point["p95_APE"] - base_metric["p95_APE"],
                        "point_delta_RMSE_log": point["RMSE_log"] - base_metric["RMSE_log"],
                        "MdAPE_improve_prob": float((delta["MdAPE"] < 0).mean()),
                        "MAPE_improve_prob": float((delta["MAPE"] < 0).mean()),
                        "p95_improve_prob": float((delta["p95_APE"] < 0).mean()),
                        "all3_improve_prob": float(((delta[["MdAPE", "MAPE", "p95_APE"]] < 0).all(axis=1)).mean()),
                        "delta_MdAPE_ci_low": float(delta["MdAPE"].quantile(0.025)),
                        "delta_MdAPE_ci_high": float(delta["MdAPE"].quantile(0.975)),
                        "delta_MAPE_ci_low": float(delta["MAPE"].quantile(0.025)),
                        "delta_MAPE_ci_high": float(delta["MAPE"].quantile(0.975)),
                        "delta_p95_APE_ci_low": float(delta["p95_APE"].quantile(0.025)),
                        "delta_p95_APE_ci_high": float(delta["p95_APE"].quantile(0.975)),
                    }
                )
    return pd.DataFrame(rows)


def feature_coefficients() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    if HCOEF14_COEFFICIENTS.exists():
        coeff = pd.read_csv(HCOEF14_COEFFICIENTS)
        coeff = coeff[coeff["candidate"].eq(STABLE)].copy()
        coeff["source"] = "HCOEF14 stable coefficient carry-forward"
        rows.append(coeff)
    policy_rows = []
    for config in OPERATIONAL_CANDIDATES:
        policy_rows.append(
            {
                "candidate": config["candidate"],
                "method": config["method"],
                "feature": config["pred_log_col"],
                "coefficient_on_scaled_feature": np.nan,
                "abs_coefficient": np.nan,
                "direction": config["description"],
                "source": "0604 stress-test operational component; not a fitted Huber coefficient",
            }
        )
    rows.append(pd.DataFrame(policy_rows))
    return pd.concat(rows, ignore_index=True, sort=False)


def gap_analysis(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = wide.copy()
    if f"service_primary_ppv8_operational_ape" in out.columns and f"{STABLE}_ape" in out.columns:
        out["service_minus_stable_ape"] = out["service_primary_ppv8_operational_ape"] - out[f"{STABLE}_ape"]
        out["service_improves_stable"] = out["service_minus_stable_ape"] < 0
    if f"service_primary_ppv8_operational_pred_log_krw" in out.columns and f"{STABLE}_pred_log_krw" in out.columns:
        out["service_minus_stable_pred_log"] = out["service_primary_ppv8_operational_pred_log_krw"] - out[f"{STABLE}_pred_log_krw"]
    summary_rows = []
    for col in ["svc_coverage_tier", "svc_group_level", "actual_price_band", "service_confidence_tier"]:
        if col not in out.columns:
            continue
        for value, group in out.groupby(col, dropna=False, observed=False):
            if len(group) < 20 or "service_minus_stable_ape" not in group:
                continue
            summary_rows.append(
                {
                    "segment_column": col,
                    "segment_value": value,
                    "n": int(len(group)),
                    "service_improve_rate_vs_stable": float(group["service_improves_stable"].mean()),
                    "median_service_minus_stable_ape": float(group["service_minus_stable_ape"].median()),
                    "mean_service_minus_stable_ape": float(group["service_minus_stable_ape"].mean()),
                    "median_service_minus_stable_pred_log": float(group["service_minus_stable_pred_log"].median()) if "service_minus_stable_pred_log" in group else np.nan,
                }
            )
    top_cols = [
        "_track6_row_id",
        "title",
        "artist_name",
        "actual_price_krw",
        "actual_price_usd_equiv",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "actual_price_band",
        f"{STABLE}_pred_price_krw",
        f"{STABLE}_ape",
        "service_primary_ppv8_operational_pred_price_krw",
        "service_primary_ppv8_operational_ape",
        "service_minus_stable_ape",
    ]
    top_cols = [col for col in top_cols if col in out.columns]
    top = out.sort_values("service_minus_stable_ape", ascending=True)[top_cols].head(100)
    return pd.DataFrame(summary_rows), top


def markdown_cell(value: Any) -> str:
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return ""
        return f"{float(value):.4f}"
    if pd.isna(value):
        return ""
    return str(value).replace("|", "/")


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()
    cols = list(data.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in data.iterrows():
        lines.append("| " + " | ".join(markdown_cell(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def md_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    in_table = False
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("| ") and line.endswith(" |"):
            cells = [html.escape(cell.strip()) for cell in line.strip("|").split("|")]
            if not in_table:
                body.append("<table>")
                in_table = True
            if set(cells[0]) <= {"-"}:
                continue
            tag = "th" if all(set(cell) <= {"-"} for cell in cells) else "td"
            if body[-1] == "<table>":
                tag = "th"
            body.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in cells) + "</tr>")
        else:
            if in_table:
                body.append("</table>")
                in_table = False
            if line.startswith("# "):
                body.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "):
                body.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("### "):
                body.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line:
                body.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body.append("</table>")
    return (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<title>PP-HCOEF15</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6}h1,h2,h3{margin-top:24px}p{line-height:1.55}</style>"
        "</head><body>" + "\n".join(body) + "</body></html>"
    )


def render_report(
    metrics_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    actual_audit_df: pd.DataFrame,
    gap_segment_df: pd.DataFrame,
    top_service_improvements: pd.DataFrame,
) -> str:
    overall = metrics_df[metrics_df["scope"].eq("overall")].copy()
    overall = overall.sort_values(["MdAPE", "MAPE", "p95_APE"])
    focus = overall[
        [
            "candidate",
            "candidate_source",
            "n",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
        ]
    ].round(4)
    boot_focus = bootstrap_df[
        bootstrap_df["baseline"].eq(STABLE)
        & bootstrap_df["candidate"].isin(["service_primary_ppv8_operational", "v01_operational_70_30", REFERENCE])
    ].copy()
    boot_focus = boot_focus[
        [
            "summary_type",
            "candidate",
            "baseline",
            "point_delta_MdAPE",
            "point_delta_MAPE",
            "point_delta_p95_APE",
            "MdAPE_improve_prob",
            "MAPE_improve_prob",
            "p95_improve_prob",
            "all3_improve_prob",
        ]
    ].round(4)
    residual_focus = residual_df.sort_values(["ape_median", "ape_mean"])[
        [
            "candidate",
            "n",
            "median_residual_log",
            "mean_residual_log",
            "residual_std",
            "ape_median",
            "ape_mean",
            "ape_p95",
            "over_2x_n",
            "under_half_n",
        ]
    ].round(4)
    service_segments = gap_segment_df.sort_values("median_service_minus_stable_ape").head(20).round(4)
    actual_match_rate = float(actual_audit_df["actual_price_match"].mean()) if not actual_audit_df.empty else 0.0
    actual_max_diff = float(actual_audit_df["actual_price_abs_diff"].max()) if not actual_audit_df.empty else np.nan

    lines = [
        "# PP-HCOEF15 Warm 최신 라벨 stress test",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 0604 최신 라벨을 외부 stress test로 사용해 HCOEF 안정 후보와 운영 후보의 차이를 비교",
        f"- 기준 후보: `{STABLE}`",
        f"- 비교 기준: `{REFERENCE}`",
        "- 후보 선택/보정값 산출에는 0604 라벨을 사용하지 않음",
        "- 0604는 외부 확인용이며 fixed test/OOF 결론을 대체하지 않음",
        "",
        "## 1. 실행 결론",
        "",
        "- HCOEF 안정 후보는 0604에서 `current_70_30`보다 MdAPE/MAPE/p95가 모두 소폭 개선됨.",
        "- 운영 service primary는 0604에서 HCOEF 안정 후보보다 MdAPE/MAPE/p95가 모두 낮음.",
        "- 다만 service primary는 HCOEF 계열 OOF/fixed test 후보 선택 절차로 검증된 새 Huber 후보가 아니므로 바로 Warm 개선 후보로 승격하지 않음.",
        "- 다음 실험은 service primary 또는 PP-V8 운영 component를 Huber 계수/위험도 피처로 넣고 OOF 기준으로 재검증하는 방향이 적절함.",
        "- 0604 actual price join 검증은 아래와 같음.",
        f"  - actual price 일치율: `{actual_match_rate:.4f}`",
        f"  - actual price 최대 차이: `{actual_max_diff:.4f}`",
        "",
        "## 2. 전체 0604 외부 라벨 성능",
        "",
        markdown_table(focus, max_rows=30),
        "",
        "## 3. HCOEF 안정 후보 대비 bootstrap",
        "",
        markdown_table(boot_focus, max_rows=30),
        "",
        "## 4. 잔차 요약",
        "",
        markdown_table(residual_focus, max_rows=30),
        "",
        "## 5. service primary가 HCOEF 안정 후보보다 좋아진 구간",
        "",
        markdown_table(service_segments, max_rows=20),
        "",
        "## 6. service primary 개선 상위 작품",
        "",
        markdown_table(top_service_improvements.round(4), max_rows=30),
        "",
        "## 7. 해석",
        "",
        "- HCOEF 안정 후보는 기존 70:30 기준 위에 작은 Huber 잔차 보정만 더한 후보라 fixed test와 OOF 근거가 가장 강함.",
        "- 0604에서는 PP-V8 운영 component가 더 강하게 나타남.",
        "- 이 결과는 PP-V8 계열이 신규 운영성 데이터에서 유효한 신호를 갖고 있음을 시사하지만, 0604 라벨로 새 가중치나 보정값을 만들면 과적합 위험이 있음.",
        "- 따라서 다음 후보는 `service_primary_pred_log`, `pp_v8_compact_blend_mape_guarded_pred_log`, `HCOEF stable pred_log`, `svc coverage`, `quantile width`를 저차원 Huber/meta guard 피처로 넣고 validation OOF에서 검증해야 함.",
        "- service primary가 낮은 가격대와 일부 low_n 구간에서 더 나은지, 또는 특정 고가 구간에서만 우연히 좋은지는 segment별 OOF 실험에서 다시 확인해야 함.",
        "",
        "## 8. 산출물",
        "",
        "- `outputs/metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/feature_coefficients.csv`",
        "- `outputs/residual_analysis.csv`",
        "- `outputs/bootstrap_or_repeated_split_summary.csv`",
        "- `outputs/segment_metric_summary.csv`",
        "- `outputs/service_vs_hcoef_gap_analysis.csv`",
        "- `outputs/service_improvement_top100.csv`",
        "- `outputs/actual_price_join_audit.csv`",
    ]
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    predictions, actual_audit = build_predictions()
    wide = pivot_predictions(predictions)
    metrics_df = build_metrics(predictions)
    residual_df = residual_analysis(predictions)
    candidates = sorted(predictions["candidate"].unique())
    bootstrap_df = bootstrap_summary(wide, candidates)
    coeff_df = feature_coefficients()
    gap_segment_df, top_service_improvements = gap_analysis(wide)

    overall_metrics = metrics_df[metrics_df["scope"].eq("overall")].copy()
    segment_metrics = metrics_df[~metrics_df["scope"].eq("overall")].copy()

    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    overall_metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    segment_metrics.to_csv(EXP_DIR / "outputs" / "segment_metric_summary.csv", index=False)
    residual_df.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    coeff_df.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    gap_segment_df.to_csv(EXP_DIR / "outputs" / "service_vs_hcoef_gap_analysis.csv", index=False)
    top_service_improvements.to_csv(EXP_DIR / "outputs" / "service_improvement_top100.csv", index=False)
    actual_audit.to_csv(EXP_DIR / "outputs" / "actual_price_join_audit.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "0604 latest label stress test only; no candidate selection from 0604 labels",
        "reference": REFERENCE,
        "stable": STABLE,
        "n_bootstrap": N_BOOTSTRAP,
        "inputs": {
            "hcoef14_predictions": str(HCOEF14_PREDICTIONS.relative_to(REPO)),
            "operational_0604": str(OPERATIONAL_0604.relative_to(REPO)),
        },
        "operational_candidates": OPERATIONAL_CANDIDATES,
        "research_candidates": RESEARCH_CANDIDATES,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report = render_report(metrics_df, residual_df, bootstrap_df, actual_audit, gap_segment_df, top_service_improvements)
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(report), encoding="utf-8")

    doc_summary = DOC_ROOT / "pp_hcoef15_warm_huber_price_basis_coefficient_refinement_summary.md"
    doc_summary.write_text(report, encoding="utf-8")
    doc_summary.with_suffix(".html").write_text(md_to_html(report), encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(overall_metrics.sort_values(["MdAPE", "MAPE", "p95_APE"])[["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
