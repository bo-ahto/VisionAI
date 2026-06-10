#!/usr/bin/env python3
"""Refine Warm correction candidates with stricter p95 guards.

PP-OPT6 starts from the best PP-OPT5 candidates and applies production-like
guards based on confidence tier, quantile width, component disagreement, and
SVC support. The goal is to keep the MAPE gain while reducing p95 regression.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_DIR = REPO / "experiments" / "track6" / "PP-OPT6_warm_p95_guard_refinement"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

OPT5_DIR = REPO / "experiments" / "track6" / "PP-OPT5_warm_focused_repeated_validation"
OPT5_AGG = OPT5_DIR / "outputs" / "aggregate_candidate_stability.csv"
OPT5_PREDS = OPT5_DIR / "outputs" / "focused_candidate_predictions.csv"

BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"
RANDOM_SEED = 20260608
REPEAT_COUNT = 80
SAMPLE_FRAC = 0.72
EPS = 1e-12


def ensure_dirs() -> None:
    for path in (OUT_DIR, REPORT_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def fmt_float(value: float) -> str:
    return str(value).replace(".", "p")


def short_name(name: str) -> str:
    cleaned = (
        name.replace("combo_focus__", "combo_")
        .replace("xgboost_focus__", "xgb_")
        .replace("catboost_focus__", "cb_")
        .replace("birth_generation", "birth_gen")
        .replace("total_works", "works")
        .replace("for_sale", "sale")
        .replace("confidence_weighted", "cw")
        .replace("low_only_diagnostic", "lowdiag")
        .replace("medium_only", "mid")
        .replace("low_only", "low")
        .replace("qwidth", "qw")
        .replace("capprof", "caprof")
    )
    return cleaned[:112]


def select_seed_candidates() -> list[str]:
    agg = pd.read_csv(OPT5_AGG)
    seeds: list[str] = [BASE_CANDIDATE, REFERENCE_CANDIDATE]

    stable_test = agg[
        (agg["family"] == "catboost_artist_focus")
        & (agg["stable_validation_pass"])
        & (agg["test_diagnostic_pass"])
    ].sort_values(["recommendation_score", "test_guarded_score"])
    seeds.extend(stable_test["candidate"].head(36).tolist())

    mape_leaders = agg[
        (agg["family"] == "catboost_artist_focus")
        & (agg["stable_validation_pass"])
        & (agg["test_delta_MAPE"] < 0)
    ].sort_values(["test_MAPE", "test_p95_APE"])
    seeds.extend(mape_leaders["candidate"].head(20).tolist())

    strict_xgb = agg[
        (agg["family"] == "xgboost_focus")
        & (agg["test_delta_MdAPE"] < 0)
        & (agg["test_delta_MAPE"] < 0)
        & (agg["test_delta_p95_APE"] < 0)
    ].sort_values(["test_delta_MAPE", "test_delta_p95_APE"])
    seeds.extend(strict_xgb["candidate"].tolist())

    stable_xgb = agg[
        (agg["family"] == "xgboost_focus")
        & (agg["stable_validation_pass"])
        & (agg["test_delta_MAPE"] < 0.003)
    ].sort_values(["mean_delta_MAPE", "mean_delta_p95_APE"])
    seeds.extend(stable_xgb["candidate"].head(6).tolist())

    out: list[str] = []
    seen: set[str] = set()
    for candidate in seeds:
        if candidate not in seen:
            out.append(candidate)
            seen.add(candidate)
    return out


def load_seed_predictions(seed_candidates: list[str]) -> pd.DataFrame:
    usecols = [
        "candidate",
        "family",
        "split",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "hcoef_stable",
        "current_70_30",
        "pred_log",
        "correction_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
    ]
    chunks = []
    seed_set = set(seed_candidates)
    for chunk in pd.read_csv(OPT5_PREDS, usecols=usecols, chunksize=200_000):
        part = chunk[chunk["candidate"].isin(seed_set)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT5 seed predictions loaded")
    return pd.concat(chunks, ignore_index=True)


def risk_bands(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    tier = df["confidence_tier"].fillna("medium_confidence").astype(str)
    qwidth = pd.to_numeric(df["quantile_width"], errors="coerce").fillna(1.5)
    spread = pd.to_numeric(df["component_prediction_spread"], errors="coerce").fillna(0)
    gap = pd.to_numeric(df["current_vs_stable_gap_abs"], errors="coerce").fillna(0)
    svc_n = pd.to_numeric(df["svc_group_n"], errors="coerce").fillna(0)

    high = (
        tier.eq("low_confidence")
        | (qwidth >= 1.65)
        | (spread >= 0.13)
        | (gap >= 0.05)
        | (svc_n < 4)
    ).to_numpy()
    medium = (
        tier.eq("medium_confidence")
        | (qwidth >= 1.28)
        | (spread >= 0.08)
        | (gap >= 0.025)
        | (svc_n < 8)
    ).to_numpy()
    return high, medium


def guard_profiles(df: pd.DataFrame, correction: np.ndarray) -> dict[str, np.ndarray]:
    high, medium = risk_bands(df)
    tier = df["confidence_tier"].fillna("medium_confidence").astype(str)
    qwidth = pd.to_numeric(df["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(df["component_prediction_spread"], errors="coerce").fillna(0).to_numpy(dtype=float)
    gap = pd.to_numeric(df["current_vs_stable_gap_abs"], errors="coerce").fillna(0).to_numpy(dtype=float)
    svc_n = pd.to_numeric(df["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)

    profiles: dict[str, np.ndarray] = {}
    profiles["orig"] = correction
    profiles["global_scale_0p90_cap0p022"] = np.clip(correction * 0.90, -0.022, 0.022)
    profiles["global_scale_0p80_cap0p020"] = np.clip(correction * 0.80, -0.020, 0.020)
    profiles["global_scale_0p70_cap0p018"] = np.clip(correction * 0.70, -0.018, 0.018)

    mult = tier.map({"high_confidence": 1.0, "medium_confidence": 0.80, "low_confidence": 0.0}).fillna(0.70).to_numpy()
    profiles["confidence_low_off_cap0p022"] = np.clip(correction * mult, -0.022, 0.022)

    mult = np.where(high, 0.35, np.where(medium, 0.75, 1.0))
    profiles["risk_balanced_cap0p022"] = np.clip(correction * mult, -0.022, 0.022)

    mult = np.where(high, 0.15, np.where(medium, 0.55, 0.90))
    profiles["risk_strict_cap0p020"] = np.clip(correction * mult, -0.020, 0.020)

    mult = np.where(qwidth <= 1.20, 0.95, np.where(qwidth <= 1.60, 0.70, 0.25))
    caps = np.where(qwidth <= 1.20, 0.024, np.where(qwidth <= 1.60, 0.018, 0.008))
    profiles["qwidth_guard_cap_dynamic"] = np.clip(correction * mult, -caps, caps)

    disagreement = (spread >= 0.12) | (gap >= 0.04)
    mid_disagreement = (spread >= 0.08) | (gap >= 0.025)
    mult = np.where(disagreement, 0.25, np.where(mid_disagreement, 0.65, 0.95))
    caps = np.where(disagreement, 0.010, np.where(mid_disagreement, 0.018, 0.022))
    profiles["disagreement_guard_cap_dynamic"] = np.clip(correction * mult, -caps, caps)

    mult = np.where((high | (svc_n < 6)) & (correction > 0), 0.20, np.where(high, 0.45, 0.90))
    profiles["positive_highrisk_guard_cap0p020"] = np.clip(correction * mult, -0.020, 0.020)

    mult = np.where(tier.eq("low_confidence").to_numpy(), 0.0, np.where(qwidth > 1.60, 0.25, 0.85))
    profiles["low_off_qwidth_guard_cap0p020"] = np.clip(correction * mult, -0.020, 0.020)

    mult = np.where(high, 0.30, 0.85)
    cap = np.where(high, 0.012, 0.022)
    profiles["tail_clamp_highrisk_cap_dynamic"] = np.clip(correction * mult, -cap, cap)
    return profiles


def generate_guarded_predictions(seeds: pd.DataFrame) -> pd.DataFrame:
    source = seeds[seeds["candidate"].isin([BASE_CANDIDATE, REFERENCE_CANDIDATE])].copy()
    rows = [source]
    non_source = seeds[~seeds["candidate"].isin([BASE_CANDIDATE, REFERENCE_CANDIDATE])].copy()
    for candidate, group in non_source.groupby("candidate", sort=False):
        base_log = pd.to_numeric(group["hcoef_stable"], errors="coerce").to_numpy(dtype=float)
        correction = pd.to_numeric(group["correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
        for profile_name, guarded_correction in guard_profiles(group, correction).items():
            tmp = group.copy()
            tmp["candidate"] = f"p95guard__seed={short_name(candidate)}__guard={profile_name}"
            tmp["family"] = "p95_guard_refinement" if profile_name != "orig" else "seed_original"
            tmp["correction_log"] = guarded_correction
            tmp["pred_log"] = base_log + guarded_correction
            rows.append(tmp)
    out = pd.concat(rows, ignore_index=True)
    out["pred_price"] = np.exp(pd.to_numeric(out["pred_log"], errors="coerce"))
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.maximum(out["actual_price"], EPS)
    return out


def metrics_for_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(pred_log)
    if not valid.any():
        return {
            "n": 0,
            "MdAPE": math.nan,
            "MAPE": math.nan,
            "p95_APE": math.nan,
            "RMSE_log": math.nan,
            "Within_30": math.nan,
            "Within_50": math.nan,
        }
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred_log = pred_log[valid]
    ape = np.abs(np.exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)
    rmse_mask = np.isfinite(actual_log)
    rmse = math.nan
    if rmse_mask.any():
        rmse = float(np.sqrt(np.mean((pred_log[rmse_mask] - actual_log[rmse_mask]) ** 2)))
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": rmse,
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (candidate, eval_split, family), group in predictions.groupby(["candidate", "eval_split", "family"]):
        actual_price = pd.to_numeric(group["actual_price"], errors="coerce").to_numpy(dtype=float)
        actual_log = pd.to_numeric(group["actual_log"], errors="coerce").to_numpy(dtype=float)
        pred_log = pd.to_numeric(group["pred_log"], errors="coerce").to_numpy(dtype=float)
        row = {"candidate": candidate, "eval_split": eval_split, "family": family}
        row.update(metrics_for_arrays(actual_price, actual_log, pred_log))
        row["mean_abs_correction_log"] = float(pd.to_numeric(group["correction_log"], errors="coerce").abs().mean())
        rows.append(row)
    metrics = pd.DataFrame(rows)
    base = metrics[metrics["candidate"] == BASE_CANDIDATE][
        ["eval_split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "base_MdAPE",
            "MAPE": "base_MAPE",
            "p95_APE": "base_p95_APE",
            "RMSE_log": "base_RMSE_log",
        }
    )
    metrics = metrics.merge(base, on="eval_split", how="left")
    for col in ("MdAPE", "MAPE", "p95_APE", "RMSE_log"):
        metrics[f"delta_{col}"] = metrics[col] - metrics[f"base_{col}"]
    metrics["strict_all3_vs_base"] = (
        (metrics["delta_MdAPE"] < 0)
        & (metrics["delta_MAPE"] < 0)
        & (metrics["delta_p95_APE"] < 0)
    )
    metrics["guarded_test_pass"] = (
        (metrics["delta_MdAPE"] < 0)
        & (metrics["delta_MAPE"] < 0)
        & (metrics["delta_p95_APE"] <= 0.002)
    )
    metrics["guarded_score"] = (
        metrics["delta_MAPE"].fillna(9)
        + 0.85 * np.maximum(metrics["delta_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(metrics["delta_MdAPE"].fillna(9), 0)
    )
    return metrics.sort_values(["eval_split", "guarded_score", "MAPE"])


def build_prediction_matrix(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"] == eval_split].copy()
    meta_cols = ["_track6_row_id", "artist_key", "confidence_tier", "actual_log", "actual_price"]
    meta = (
        subset[subset["candidate"] == BASE_CANDIDATE][meta_cols]
        .drop_duplicates("_track6_row_id")
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )
    wide = subset.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
    wide = wide.reindex(meta["_track6_row_id"]).reset_index(drop=True)
    return meta, wide


def metric_matrix(meta: pd.DataFrame, wide: pd.DataFrame, row_positions: np.ndarray) -> pd.DataFrame:
    actual_price = pd.to_numeric(meta.iloc[row_positions]["actual_price"], errors="coerce").to_numpy(dtype=float)
    actual_log = pd.to_numeric(meta.iloc[row_positions]["actual_log"], errors="coerce").to_numpy(dtype=float)
    pred = wide.iloc[row_positions].to_numpy(dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0)
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred = pred[valid]
    ape = np.abs(np.exp(pred) - actual_price[:, None]) / np.maximum(actual_price[:, None], EPS)
    rmse = np.sqrt(np.nanmean((pred - actual_log[:, None]) ** 2, axis=0))
    return pd.DataFrame(
        {
            "candidate": list(wide.columns),
            "n": int(valid.sum()),
            "MdAPE": np.nanmedian(ape, axis=0),
            "MAPE": np.nanmean(ape, axis=0),
            "p95_APE": np.nanquantile(ape, 0.95, axis=0),
            "RMSE_log": rmse,
        }
    )


def repeated_samples(meta: pd.DataFrame) -> list[tuple[str, int, np.ndarray]]:
    rng = np.random.default_rng(RANDOM_SEED)
    tiers = meta["confidence_tier"].fillna("medium_confidence").astype(str)
    artists = meta["artist_key"].fillna("__missing_artist__").astype(str)
    all_positions = np.arange(len(meta))
    samples: list[tuple[str, int, np.ndarray]] = []

    for repeat in range(REPEAT_COUNT):
        selected: list[int] = []
        for tier in sorted(tiers.unique()):
            idx = np.flatnonzero(tiers.to_numpy() == tier)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            selected.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("confidence_stratified_rows", repeat, np.array(sorted(selected), dtype=int)))

    unique_artists = np.array(sorted(artists.unique()))
    for repeat in range(REPEAT_COUNT):
        n = max(1, int(round(len(unique_artists) * SAMPLE_FRAC)))
        chosen = set(rng.choice(unique_artists, size=n, replace=False).tolist())
        selected = np.flatnonzero(artists.isin(chosen).to_numpy())
        samples.append(("artist_group_holdout", repeat, selected))

    for repeat in range(REPEAT_COUNT):
        n = max(1, int(round(len(all_positions) * SAMPLE_FRAC)))
        selected = rng.choice(all_positions, size=n, replace=True)
        samples.append(("row_bootstrap", repeat, selected))
    return samples


def repeated_validation_summary(meta: pd.DataFrame, wide: pd.DataFrame, family_map: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for scenario, repeat, positions in repeated_samples(meta):
        metrics = metric_matrix(meta, wide, positions)
        base = metrics[metrics["candidate"] == BASE_CANDIDATE].iloc[0]
        for col in ("MdAPE", "MAPE", "p95_APE", "RMSE_log"):
            metrics[f"delta_{col}"] = metrics[col] - float(base[col])
        metrics["scenario"] = scenario
        metrics["repeat"] = repeat
        rows.append(metrics)
    detail = pd.concat(rows, ignore_index=True)
    detail["family"] = detail["candidate"].map(family_map).fillna("unknown")
    detail["strict_all3_vs_base"] = (
        (detail["delta_MdAPE"] < 0)
        & (detail["delta_MAPE"] < 0)
        & (detail["delta_p95_APE"] < 0)
    )
    summary = (
        detail[detail["candidate"] != BASE_CANDIDATE]
        .groupby(["candidate", "family", "scenario"])
        .agg(
            repeats=("repeat", "nunique"),
            mean_delta_MdAPE=("delta_MdAPE", "mean"),
            mean_delta_MAPE=("delta_MAPE", "mean"),
            mean_delta_p95_APE=("delta_p95_APE", "mean"),
            p90_delta_p95_APE=("delta_p95_APE", lambda s: float(np.quantile(s, 0.90))),
            improve_MAPE_rate=("delta_MAPE", lambda s: float(np.mean(s < 0))),
            p95_not_worse_rate=("delta_p95_APE", lambda s: float(np.mean(s <= 0))),
            strict_all3_rate=("strict_all3_vs_base", "mean"),
        )
        .reset_index()
    )
    summary["stability_score"] = (
        summary["mean_delta_MAPE"].fillna(9)
        + 0.60 * np.maximum(summary["mean_delta_p95_APE"].fillna(9), 0)
        + 0.25 * np.maximum(summary["p90_delta_p95_APE"].fillna(9), 0)
        - 0.004 * summary["strict_all3_rate"].fillna(0)
    )
    return detail, summary.sort_values(["stability_score", "mean_delta_MAPE"])


def aggregate_stability(repeated_summary: pd.DataFrame, full_metrics: pd.DataFrame) -> pd.DataFrame:
    aggregate = (
        repeated_summary.groupby(["candidate", "family"])
        .agg(
            scenario_count=("scenario", "nunique"),
            mean_delta_MdAPE=("mean_delta_MdAPE", "mean"),
            mean_delta_MAPE=("mean_delta_MAPE", "mean"),
            mean_delta_p95_APE=("mean_delta_p95_APE", "mean"),
            worst_scenario_delta_p95_APE=("mean_delta_p95_APE", "max"),
            mean_MAPE_improve_rate=("improve_MAPE_rate", "mean"),
            mean_p95_not_worse_rate=("p95_not_worse_rate", "mean"),
            mean_strict_all3_rate=("strict_all3_rate", "mean"),
            mean_stability_score=("stability_score", "mean"),
        )
        .reset_index()
    )
    val = full_metrics[full_metrics["eval_split"] == "validation_oof"][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "strict_all3_vs_base"]
    ].rename(
        columns={
            "MdAPE": "validation_MdAPE",
            "MAPE": "validation_MAPE",
            "p95_APE": "validation_p95_APE",
            "delta_MdAPE": "validation_delta_MdAPE",
            "delta_MAPE": "validation_delta_MAPE",
            "delta_p95_APE": "validation_delta_p95_APE",
            "strict_all3_vs_base": "validation_strict_all3",
        }
    )
    test = full_metrics[full_metrics["eval_split"] == "test"][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "strict_all3_vs_base", "guarded_test_pass"]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "delta_MdAPE": "test_delta_MdAPE",
            "delta_MAPE": "test_delta_MAPE",
            "delta_p95_APE": "test_delta_p95_APE",
            "strict_all3_vs_base": "test_strict_all3",
            "guarded_test_pass": "test_guarded_pass",
        }
    )
    aggregate = aggregate.merge(val, on="candidate", how="left").merge(test, on="candidate", how="left")
    aggregate["stable_p95_validation_pass"] = (
        (aggregate["mean_MAPE_improve_rate"] >= 0.70)
        & (aggregate["mean_p95_not_worse_rate"] >= 0.62)
        & (aggregate["validation_delta_MAPE"] < 0)
        & (aggregate["validation_delta_p95_APE"] <= 0.002)
    )
    aggregate["operational_pass"] = aggregate["stable_p95_validation_pass"] & aggregate["test_guarded_pass"]
    aggregate["recommendation_score"] = (
        aggregate["mean_stability_score"].fillna(9)
        + 0.75 * np.maximum(aggregate["test_delta_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(aggregate["test_delta_MdAPE"].fillna(9), 0)
    )
    return aggregate.sort_values(
        ["operational_pass", "stable_p95_validation_pass", "recommendation_score", "test_MAPE"],
        ascending=[False, False, True, True],
    )


def markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
    headers = list(view.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def render_report(full_metrics: pd.DataFrame, repeated_summary: pd.DataFrame, aggregate: pd.DataFrame, seeds: list[str]) -> str:
    base = full_metrics[full_metrics["candidate"] == BASE_CANDIDATE][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].sort_values("eval_split")
    family = (
        aggregate.groupby("family")
        .agg(
            candidates=("candidate", "nunique"),
            stable_p95_validation_pass=("stable_p95_validation_pass", "sum"),
            test_guarded_pass=("test_guarded_pass", "sum"),
            test_strict_all3=("test_strict_all3", "sum"),
            operational_pass=("operational_pass", "sum"),
            best_test_MAPE=("test_MAPE", "min"),
            best_test_p95_APE=("test_p95_APE", "min"),
        )
        .reset_index()
        .sort_values(["operational_pass", "best_test_MAPE"], ascending=[False, True])
    )
    cols = [
        "candidate",
        "family",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "mean_strict_all3_rate",
        "validation_delta_MAPE",
        "validation_delta_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_p95_validation_pass",
        "test_guarded_pass",
        "test_strict_all3",
        "operational_pass",
    ]
    scenario_cols = [
        "candidate",
        "family",
        "scenario",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "p90_delta_p95_APE",
        "improve_MAPE_rate",
        "p95_not_worse_rate",
        "strict_all3_rate",
        "stability_score",
    ]
    operational = aggregate[aggregate["operational_pass"]].sort_values(["recommendation_score", "test_MAPE"])
    strict = aggregate[aggregate["test_strict_all3"]].sort_values(["test_delta_MAPE", "test_delta_p95_APE"])
    test_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"])

    return f"""# PP-OPT6 Warm p95 Guard Refinement

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 기준 후보: `{BASE_CANDIDATE}`
- seed 후보 수: {len(seeds)}
- 반복 검증: validation OOF 내부 3개 시나리오 x {REPEAT_COUNT}회
- 목적: PP-OPT5 후보에 p95 guard를 얹어 MAPE 개선과 p95 방어를 동시에 만족하는 후보를 찾는다.

## 1. 기준 성능

{markdown_table(base, 10)}

## 2. 후보군 요약

{markdown_table(family, 20)}

## 3. 운영 후보

{markdown_table(operational[cols], 30)}

## 4. Test에서 세 지표 모두 개선된 후보

{markdown_table(strict[cols], 30)}

## 5. Test MAPE 상위 후보

{markdown_table(test_mape[cols], 30)}

## 6. 반복 검증 시나리오 상위 후보

{markdown_table(repeated_summary[scenario_cols].sort_values(['stability_score', 'mean_delta_MAPE']), 40)}

## 7. 해석 기준

- `stable_p95_validation_pass`: 반복 validation에서 MAPE 개선률 70% 이상, p95 비악화율 62% 이상, 전체 validation MAPE 개선 및 p95 악화 0.002 이하.
- `test_guarded_pass`: fixed test에서 MdAPE/MAPE 개선, p95 악화 0.002 이하.
- `test_strict_all3`: fixed test에서 MdAPE/MAPE/p95 모두 개선.
- `operational_pass`: stable_p95_validation_pass와 test_guarded_pass를 동시에 만족.

## 8. 산출물

- `outputs/full_guard_metrics.csv`
- `outputs/repeated_validation_detail.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/aggregate_guard_stability.csv`
- `outputs/selected_guard_predictions.csv`
- `outputs/candidate_predictions_sample.csv`
- `reports/result_report.md`
- `reports/result_report.html`
- `artifacts/run_config.json`
"""


def html_from_markdown(markdown: str) -> str:
    escaped = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-OPT6 Warm p95 guard refinement</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; line-height: 1.55; }}
    pre {{ white-space: pre-wrap; background: #f7f8fa; border: 1px solid #d8dee4; border-radius: 8px; padding: 18px; }}
  </style>
</head>
<body><pre>{escaped}</pre></body>
</html>
"""


def main() -> None:
    ensure_dirs()
    seeds = select_seed_candidates()
    seed_predictions = load_seed_predictions(seeds)
    predictions = generate_guarded_predictions(seed_predictions)
    full_metrics = summarize_predictions(predictions)

    family_map = predictions[["candidate", "family"]].drop_duplicates().set_index("candidate")["family"]
    val_meta, val_wide = build_prediction_matrix(predictions, "validation_oof")
    repeated_detail, repeated_summary = repeated_validation_summary(val_meta, val_wide, family_map)
    aggregate = aggregate_stability(repeated_summary, full_metrics)

    selected_candidates = (
        aggregate[
            (aggregate["operational_pass"])
            | (aggregate["test_strict_all3"])
            | (aggregate["stable_p95_validation_pass"] & (aggregate["test_delta_MAPE"] < 0))
        ]
        .sort_values(["operational_pass", "recommendation_score", "test_MAPE"], ascending=[False, True, True])
        ["candidate"]
        .head(40)
        .tolist()
    )
    selected_predictions = predictions[predictions["candidate"].isin(selected_candidates + [BASE_CANDIDATE])].copy()
    sample = predictions.sort_values(["family", "candidate", "eval_split", "_track6_row_id"]).groupby(
        ["family", "candidate", "eval_split"], as_index=False
    ).head(3)

    full_metrics.to_csv(OUT_DIR / "full_guard_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_guard_stability.csv", index=False)
    selected_predictions.to_csv(OUT_DIR / "selected_guard_predictions.csv", index=False)
    sample.to_csv(OUT_DIR / "candidate_predictions_sample.csv", index=False)

    report = render_report(full_metrics, repeated_summary, aggregate, seeds)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_from_markdown(report), encoding="utf-8")

    config = {
        "experiment_id": "PP-OPT6",
        "base_candidate": BASE_CANDIDATE,
        "random_seed": RANDOM_SEED,
        "repeat_count_per_scenario": REPEAT_COUNT,
        "sample_frac": SAMPLE_FRAC,
        "seed_candidate_count": len(seeds),
        "candidate_count": int(full_metrics["candidate"].nunique()),
        "prediction_rows_in_memory": int(len(predictions)),
        "validation_rows": int(len(val_meta)),
        "sources": {
            "opt5_aggregate": str(OPT5_AGG.relative_to(REPO)),
            "opt5_predictions": str(OPT5_PREDS.relative_to(REPO)),
        },
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    cols = [
        "candidate",
        "family",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "operational_pass",
        "test_strict_all3",
    ]
    print("\nTop guard candidates:")
    print(aggregate[cols].head(20).to_string(index=False))
    print("\nStrict all3 test candidates:")
    print(aggregate[aggregate["test_strict_all3"]][cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
