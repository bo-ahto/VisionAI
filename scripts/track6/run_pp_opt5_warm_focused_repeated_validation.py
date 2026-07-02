#!/usr/bin/env python3
"""Focused repeated validation for Warm correction candidates.

This experiment follows PP-OPT4. It keeps only the promising correction
families and evaluates them with repeated validation subsets before looking at
the fixed test split. Test metrics are diagnostic, not a selection target.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_DIR = REPO / "experiments" / "track6" / "PP-OPT5_warm_focused_repeated_validation"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

HCOEF20 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
CF1 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CF1_warm_confidence_filtered_training"
    / "outputs"
    / "candidate_predictions.csv"
)
CF3_RAW = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CF3_warm_catboost_correction_strength_tuning"
    / "outputs"
    / "raw_catboost_corrections.csv"
)
AMW10 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-AMW10_warm_birth_generation_activity_external_residual_correction"
    / "outputs"
    / "candidate_predictions.csv"
)

BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"
RANDOM_SEED = 20260608
REPEAT_COUNT = 80
SAMPLE_FRAC = 0.72
EPS = 1e-12


@dataclass(frozen=True)
class CatBoostSpec:
    model_policy: str
    tier_profile: str
    qwidth_profile: str
    cap_profile: str
    cap: float
    strength: float


def ensure_dirs() -> None:
    for path in (OUT_DIR, REPORT_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def to_eval_split(split: str) -> str:
    if split == "validation":
        return "validation_oof"
    return split


def fmt_float(value: float) -> str:
    return str(value).replace(".", "p")


def prediction_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
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
    for col in cols:
        if col not in df.columns:
            df[col] = np.nan
    out = df[cols].copy()
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
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual_price) / np.maximum(actual_price, EPS)
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


def metrics_for(group: pd.DataFrame) -> dict[str, float]:
    return metrics_for_arrays(
        pd.to_numeric(group["actual_price"], errors="coerce").to_numpy(dtype=float),
        pd.to_numeric(group["actual_log"], errors="coerce").to_numpy(dtype=float),
        pd.to_numeric(group["pred_log"], errors="coerce").to_numpy(dtype=float),
    )


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (candidate, eval_split, family), group in predictions.groupby(["candidate", "eval_split", "family"]):
        row = {"candidate": candidate, "eval_split": eval_split, "family": family}
        row.update(metrics_for(group))
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
    metrics["improves_all3_vs_base"] = (
        (metrics["delta_MdAPE"] < 0)
        & (metrics["delta_MAPE"] < 0)
        & (metrics["delta_p95_APE"] < 0)
    )
    metrics["guarded_score"] = (
        metrics["delta_MAPE"].fillna(9)
        + 0.60 * np.maximum(metrics["delta_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(metrics["delta_MdAPE"].fillna(9), 0)
    )
    return metrics.sort_values(["eval_split", "guarded_score", "MAPE"])


def load_base() -> pd.DataFrame:
    usecols = [
        "scope",
        "split",
        "candidate",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
    ]
    df = pd.read_csv(HCOEF20, usecols=usecols)
    keep = (
        (df["candidate"] == BASE_CANDIDATE)
        & (
            ((df["split"] == "validation") & (df["scope"] == "validation_oof_row"))
            | ((df["split"] == "test") & (df["scope"] == "fixed_confirmation"))
        )
    )
    base = df.loc[keep].copy()
    base["eval_split"] = base["split"].map(to_eval_split)
    base = base.drop(columns=["candidate", "scope"])

    cf_cols = [
        "split",
        "candidate",
        "_track6_row_id",
        "confidence_tier",
        "component_prediction_spread",
        "component_prediction_range",
        "current_vs_stable_gap_abs",
        "confidence_risk_score",
    ]
    cf = pd.read_csv(CF1, usecols=cf_cols)
    cf = cf[cf["candidate"] == BASE_CANDIDATE].copy()
    cf = cf.drop(columns=["candidate"]).drop_duplicates(["split", "_track6_row_id"])
    base = base.merge(cf, on=["split", "_track6_row_id"], how="left")
    base["confidence_tier"] = base["confidence_tier"].fillna("medium_confidence")
    return base


def source_predictions(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, col in [
        (BASE_CANDIDATE, "hcoef_stable"),
        (REFERENCE_CANDIDATE, "current_70_30"),
        ("svc_numeric_seed_mean", "svc_numeric_seed_mean"),
        ("ppv8_service_proxy", "ppv8_service_proxy"),
    ]:
        tmp = base.copy()
        tmp["candidate"] = candidate
        tmp["family"] = "source"
        tmp["pred_log"] = pd.to_numeric(tmp[col], errors="coerce")
        tmp["correction_log"] = tmp["pred_log"] - pd.to_numeric(tmp["hcoef_stable"], errors="coerce")
        rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


def tier_multiplier(tier: pd.Series, profile: str) -> np.ndarray:
    values = tier.fillna("medium_confidence").astype(str)
    if profile == "same":
        return np.ones(len(values))
    if profile == "confidence_weighted_apply":
        mapping = {"high_confidence": 1.0, "medium_confidence": 0.45, "low_confidence": 0.15}
    elif profile == "low_guarded":
        mapping = {"high_confidence": 1.0, "medium_confidence": 0.60, "low_confidence": 0.25}
    elif profile == "high_mid_guarded_low_off":
        mapping = {"high_confidence": 1.0, "medium_confidence": 0.50, "low_confidence": 0.0}
    else:
        raise ValueError(profile)
    return values.map(mapping).fillna(0.45).to_numpy(dtype=float)


def qwidth_multiplier(qwidth: pd.Series, profile: str) -> np.ndarray:
    q = pd.to_numeric(qwidth, errors="coerce").fillna(1.5).to_numpy(dtype=float)
    if profile == "same":
        return np.ones(len(q))
    if profile == "qwidth_conservative":
        return np.where(q <= 1.2, 1.0, np.where(q <= 1.6, 0.55, 0.15))
    if profile == "qwidth_balanced":
        return np.where(q <= 1.2, 1.0, np.where(q <= 1.6, 0.70, 0.25))
    raise ValueError(profile)


def dynamic_cap(qwidth: pd.Series, cap: float, profile: str) -> np.ndarray:
    q = pd.to_numeric(qwidth, errors="coerce").fillna(1.5).to_numpy(dtype=float)
    if profile == "fixed":
        return np.full(len(q), cap)
    if profile == "qcap_balanced":
        return np.minimum(cap, np.where(q <= 1.2, 0.04, np.where(q <= 1.6, 0.03, 0.01)))
    raise ValueError(profile)


def catboost_specs() -> list[CatBoostSpec]:
    specs: list[CatBoostSpec] = []
    for tier_profile in ["same", "low_guarded", "confidence_weighted_apply"]:
        for qwidth_profile in ["same", "qwidth_balanced", "qwidth_conservative"]:
            for cap_profile in ["fixed", "qcap_balanced"]:
                for cap in [0.02, 0.03, 0.05]:
                    for strength in [0.75, 1.00, 1.15]:
                        specs.append(
                            CatBoostSpec(
                                model_policy="confidence_weighted",
                                tier_profile=tier_profile,
                                qwidth_profile=qwidth_profile,
                                cap_profile=cap_profile,
                                cap=cap,
                                strength=strength,
                            )
                        )
    return specs


def catboost_predictions(base: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(CF3_RAW)
    raw = raw.rename(columns={"split": "eval_split"})
    raw["split"] = raw["eval_split"].map({"validation_oof": "validation", "test": "test"})
    frame = raw.merge(
        base,
        on=["split", "_track6_row_id"],
        how="left",
        suffixes=("", "_base"),
    )
    rows = []
    for spec in catboost_specs():
        subset = frame[frame["model_policy"] == spec.model_policy].copy()
        if subset.empty:
            continue
        tier_mult = tier_multiplier(subset["confidence_tier"], spec.tier_profile)
        q_mult = qwidth_multiplier(subset["quantile_width"], spec.qwidth_profile)
        cap_arr = dynamic_cap(subset["quantile_width"], spec.cap, spec.cap_profile)
        raw_corr = pd.to_numeric(subset["raw_catboost_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
        correction = np.clip(raw_corr * spec.strength * tier_mult * q_mult, -cap_arr, cap_arr)
        tmp = subset.copy()
        tmp["correction_log"] = correction
        tmp["pred_log"] = pd.to_numeric(tmp["hcoef_stable"], errors="coerce") + correction
        tmp["candidate"] = (
            "catboost_focus__"
            f"tier={spec.tier_profile}__qmult={spec.qwidth_profile}"
            f"__cap={fmt_float(spec.cap)}__capprof={spec.cap_profile}__s={fmt_float(spec.strength)}"
        )
        tmp["family"] = "catboost_focus"
        rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


def xgboost_route_predictions(base: pd.DataFrame) -> pd.DataFrame:
    usecols = [
        "split",
        "eval_split",
        "_track6_row_id",
        "candidate",
        "model_family",
        "train_policy",
        "residual_cap_log",
        "pred_log",
    ]
    df = pd.read_csv(CF1, usecols=usecols)
    df = df[(df["model_family"] == "xgboost") & (df["eval_split"].isin(["validation_oof", "test"]))].copy()
    keep_candidates = {
        "xgboost_low_only_diagnostic_cap0p02",
        "xgboost_low_only_diagnostic_cap0p03",
        "xgboost_low_only_diagnostic_cap0p05",
        "xgboost_low_only_diagnostic_cap0p08",
        "xgboost_all_rows_cap0p03",
        "xgboost_all_rows_cap0p05",
        "xgboost_all_rows_cap0p08",
        "xgboost_confidence_weighted_cap0p03",
        "xgboost_confidence_weighted_cap0p05",
    }
    df = df[df["candidate"].isin(keep_candidates)].copy()
    frame = df.merge(base, on=["split", "eval_split", "_track6_row_id"], how="left", suffixes=("_xgb", ""))
    rows = []
    for candidate in sorted(frame["candidate"].dropna().unique()):
        sub = frame[frame["candidate"] == candidate].copy()
        for route in ["all", "medium_only", "low_only", "medium_low"]:
            tier = sub["confidence_tier"].astype(str)
            if route == "all":
                use = np.ones(len(sub), dtype=bool)
            elif route == "medium_only":
                use = tier.eq("medium_confidence").to_numpy()
            elif route == "low_only":
                use = tier.eq("low_confidence").to_numpy()
            else:
                use = tier.isin(["medium_confidence", "low_confidence"]).to_numpy()
            base_pred = pd.to_numeric(sub["hcoef_stable"], errors="coerce")
            xgb_pred_col = "pred_log_xgb" if "pred_log_xgb" in sub.columns else "pred_log"
            xgb_pred = pd.to_numeric(sub[xgb_pred_col], errors="coerce")
            tmp = sub.copy()
            tmp["pred_log"] = np.where(use, xgb_pred, base_pred)
            tmp["correction_log"] = tmp["pred_log"] - base_pred
            tmp["candidate"] = f"xgboost_focus__{candidate}__route={route}"
            tmp["family"] = "xgboost_focus"
            rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


def artist_predictions(base: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(AMW10)
    df["eval_split"] = df["split"].map(to_eval_split)
    keep_feature_sets = {
        "birth_generation",
        "birth_generation_for_sale",
        "birth_generation_total_works",
        "birth_generation_gallery",
    }
    keep = (
        df["feature_set"].isin(keep_feature_sets)
        & df["candidate"].astype(str).str.startswith("huber_")
        & df["candidate"].astype(str).str.contains("gatenone")
        & df["candidate"].astype(str).str.contains("s0p75")
    )
    df = df.loc[keep].copy()
    df = df.merge(
        base[
            [
                "split",
                "eval_split",
                "_track6_row_id",
                "confidence_tier",
                "hcoef_stable",
                "current_70_30",
                "quantile_width",
                "l10_price_range_ratio",
                "svc_group_n",
                "component_prediction_spread",
                "current_vs_stable_gap_abs",
            ]
        ],
        on=["split", "eval_split", "_track6_row_id"],
        how="left",
    )
    df["candidate"] = "artist_focus__" + df["candidate"].astype(str)
    df["family"] = "artist_focus"
    return prediction_columns(df)


def short_name(name: str) -> str:
    cleaned = (
        name.replace("catboost_focus__", "cb_")
        .replace("artist_focus__", "am_")
        .replace("huber_", "h_")
        .replace("birth_generation", "birth_gen")
        .replace("gatenone", "gn")
        .replace("alpha0p01", "a01")
        .replace("cap0p03", "c03")
        .replace("cap0p05", "c05")
        .replace("s0p75", "s075")
        .replace("confidence_weighted", "cw")
        .replace("qwidth", "qw")
    )
    return cleaned[:86]


def combined_catboost_artist_predictions(
    base: pd.DataFrame,
    catboost: pd.DataFrame,
    artist: pd.DataFrame,
    first_metrics: pd.DataFrame,
) -> pd.DataFrame:
    cat_pool = first_metrics[
        (first_metrics["eval_split"] == "validation_oof")
        & (first_metrics["family"] == "catboost_focus")
        & (first_metrics["delta_MAPE"] < 0)
    ].copy()
    artist_pool = first_metrics[
        (first_metrics["eval_split"] == "validation_oof")
        & (first_metrics["family"] == "artist_focus")
        & (first_metrics["delta_p95_APE"] <= 0.01)
    ].copy()
    cat_candidates = cat_pool.sort_values(["guarded_score", "MAPE"])["candidate"].head(8).tolist()
    artist_candidates = artist_pool.sort_values(["guarded_score", "MAPE"])["candidate"].head(8).tolist()
    if not cat_candidates or not artist_candidates:
        return pd.DataFrame()

    key_cols = ["split", "eval_split", "_track6_row_id"]
    base_key = base[
        key_cols
        + [
            "artist_key",
            "artist_name_ko",
            "confidence_tier",
            "actual_log",
            "actual_price",
            "hcoef_stable",
            "current_70_30",
            "quantile_width",
            "l10_price_range_ratio",
            "svc_group_n",
            "component_prediction_spread",
            "current_vs_stable_gap_abs",
        ]
    ]
    cat = catboost[catboost["candidate"].isin(cat_candidates)][
        key_cols + ["candidate", "correction_log"]
    ].rename(columns={"candidate": "catboost_candidate", "correction_log": "catboost_correction_log"})
    art = artist[artist["candidate"].isin(artist_candidates)][
        key_cols + ["candidate", "correction_log"]
    ].rename(columns={"candidate": "artist_candidate", "correction_log": "artist_correction_log"})

    rows = []
    for cat_name in cat_candidates:
        cat_sub = cat[cat["catboost_candidate"] == cat_name]
        for artist_name in artist_candidates:
            merged = cat_sub.merge(art[art["artist_candidate"] == artist_name], on=key_cols, how="inner")
            merged = merged.merge(base_key, on=key_cols, how="left")
            if merged.empty:
                continue
            cat_corr = pd.to_numeric(merged["catboost_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
            artist_corr = pd.to_numeric(merged["artist_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
            for total_cap in [0.025, 0.03, 0.04]:
                for cat_weight in [0.80, 1.00]:
                    for artist_weight in [0.50, 0.75, 1.00]:
                        correction = np.clip(
                            cat_weight * cat_corr + artist_weight * artist_corr,
                            -total_cap,
                            total_cap,
                        )
                        tmp = merged.copy()
                        tmp["correction_log"] = correction
                        tmp["pred_log"] = pd.to_numeric(tmp["hcoef_stable"], errors="coerce") + correction
                        tmp["candidate"] = (
                            "combo_focus__"
                            f"cat={short_name(cat_name)}__artist={short_name(artist_name)}"
                            f"__cw={fmt_float(cat_weight)}__aw={fmt_float(artist_weight)}"
                            f"__totalcap={fmt_float(total_cap)}"
                        )
                        tmp["family"] = "catboost_artist_focus"
                        rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_prediction_matrix(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"] == eval_split].copy()
    meta_cols = [
        "_track6_row_id",
        "artist_key",
        "confidence_tier",
        "actual_log",
        "actual_price",
    ]
    meta = (
        subset[subset["candidate"] == BASE_CANDIDATE][meta_cols]
        .drop_duplicates("_track6_row_id")
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )
    wide = subset.pivot_table(
        index="_track6_row_id",
        columns="candidate",
        values="pred_log",
        aggfunc="first",
    )
    wide = wide.reindex(meta["_track6_row_id"]).reset_index(drop=True)
    return meta, wide


def metric_matrix(meta: pd.DataFrame, wide: pd.DataFrame, row_positions: np.ndarray) -> pd.DataFrame:
    actual_price = pd.to_numeric(meta.iloc[row_positions]["actual_price"], errors="coerce").to_numpy(dtype=float)
    actual_log = pd.to_numeric(meta.iloc[row_positions]["actual_log"], errors="coerce").to_numpy(dtype=float)
    pred = wide.iloc[row_positions].to_numpy(dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0)
    if not valid.any():
        raise ValueError("No valid rows for metric matrix")
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred = pred[valid]
    ape = np.abs(np.exp(pred) - actual_price[:, None]) / np.maximum(actual_price[:, None], EPS)
    rmse_mask = np.isfinite(actual_log)
    rmse = np.full(pred.shape[1], np.nan)
    if rmse_mask.any():
        rmse = np.sqrt(np.nanmean((pred[rmse_mask] - actual_log[rmse_mask, None]) ** 2, axis=0))
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
    all_positions = np.arange(len(meta))
    samples: list[tuple[str, int, np.ndarray]] = []

    tiers = meta["confidence_tier"].fillna("medium_confidence").astype(str)
    for repeat in range(REPEAT_COUNT):
        selected: list[int] = []
        for tier in sorted(tiers.unique()):
            idx = np.flatnonzero(tiers.to_numpy() == tier)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            selected.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("confidence_stratified_rows", repeat, np.array(sorted(selected), dtype=int)))

    artists = meta["artist_key"].fillna("__missing_artist__").astype(str)
    unique_artists = np.array(sorted(artists.unique()))
    for repeat in range(REPEAT_COUNT):
        artist_n = max(1, int(round(len(unique_artists) * SAMPLE_FRAC)))
        chosen_artists = set(rng.choice(unique_artists, size=artist_n, replace=False).tolist())
        selected = np.flatnonzero(artists.isin(chosen_artists).to_numpy())
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
    detail["improves_all3_vs_base"] = (
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
            median_delta_MAPE=("delta_MAPE", "median"),
            p90_delta_p95_APE=("delta_p95_APE", lambda s: float(np.quantile(s, 0.90))),
            improve_MdAPE_rate=("delta_MdAPE", lambda s: float(np.mean(s < 0))),
            improve_MAPE_rate=("delta_MAPE", lambda s: float(np.mean(s < 0))),
            p95_not_worse_rate=("delta_p95_APE", lambda s: float(np.mean(s <= 0))),
            all3_improve_rate=("improves_all3_vs_base", "mean"),
        )
        .reset_index()
    )
    summary["stability_score"] = (
        summary["mean_delta_MAPE"].fillna(9)
        + 0.40 * np.maximum(summary["mean_delta_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(summary["p90_delta_p95_APE"].fillna(9), 0)
        - 0.004 * summary["all3_improve_rate"].fillna(0)
    )
    return detail, summary.sort_values(["stability_score", "mean_delta_MAPE"])


def aggregate_candidate_stability(
    repeated_summary: pd.DataFrame,
    full_metrics: pd.DataFrame,
) -> pd.DataFrame:
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
            mean_all3_improve_rate=("all3_improve_rate", "mean"),
            mean_stability_score=("stability_score", "mean"),
        )
        .reset_index()
    )
    val = full_metrics[full_metrics["eval_split"] == "validation_oof"][
        [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "guarded_score",
            "improves_all3_vs_base",
        ]
    ].rename(
        columns={
            "MdAPE": "full_validation_MdAPE",
            "MAPE": "full_validation_MAPE",
            "p95_APE": "full_validation_p95_APE",
            "delta_MdAPE": "full_validation_delta_MdAPE",
            "delta_MAPE": "full_validation_delta_MAPE",
            "delta_p95_APE": "full_validation_delta_p95_APE",
            "guarded_score": "full_validation_guarded_score",
            "improves_all3_vs_base": "full_validation_all3",
        }
    )
    test = full_metrics[full_metrics["eval_split"] == "test"][
        [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "guarded_score",
            "improves_all3_vs_base",
        ]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "delta_MdAPE": "test_delta_MdAPE",
            "delta_MAPE": "test_delta_MAPE",
            "delta_p95_APE": "test_delta_p95_APE",
            "guarded_score": "test_guarded_score",
            "improves_all3_vs_base": "test_all3",
        }
    )
    aggregate = aggregate.merge(val, on="candidate", how="left").merge(test, on="candidate", how="left")
    aggregate["stable_validation_pass"] = (
        (aggregate["mean_MAPE_improve_rate"] >= 0.65)
        & (aggregate["mean_p95_not_worse_rate"] >= 0.55)
        & (aggregate["full_validation_delta_MAPE"] < 0)
        & (aggregate["full_validation_delta_p95_APE"] <= 0.005)
    )
    aggregate["test_diagnostic_pass"] = (
        (aggregate["test_delta_MAPE"] < 0)
        & (aggregate["test_delta_MdAPE"] < 0)
        & (aggregate["test_delta_p95_APE"] <= 0.005)
    )
    aggregate["recommendation_score"] = (
        aggregate["mean_stability_score"].fillna(9)
        + 0.40 * np.maximum(aggregate["test_delta_p95_APE"].fillna(9), 0)
        + 0.20 * np.maximum(aggregate["test_delta_MdAPE"].fillna(9), 0)
    )
    return aggregate.sort_values(["stable_validation_pass", "recommendation_score", "test_guarded_score"], ascending=[False, True, True])


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


def render_report(
    full_metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    aggregate: pd.DataFrame,
) -> str:
    base = full_metrics[full_metrics["candidate"] == BASE_CANDIDATE][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].sort_values("eval_split")

    family_summary = (
        aggregate.groupby("family")
        .agg(
            candidates=("candidate", "nunique"),
            stable_validation_pass=("stable_validation_pass", "sum"),
            test_diagnostic_pass=("test_diagnostic_pass", "sum"),
            best_test_MAPE=("test_MAPE", "min"),
            best_test_p95_APE=("test_p95_APE", "min"),
            mean_all3_rate=("mean_all3_improve_rate", "max"),
        )
        .reset_index()
        .sort_values(["stable_validation_pass", "best_test_MAPE"], ascending=[False, True])
    )

    ranking_cols = [
        "candidate",
        "family",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "mean_all3_improve_rate",
        "full_validation_delta_MAPE",
        "full_validation_delta_p95_APE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_validation_pass",
        "test_diagnostic_pass",
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
        "all3_improve_rate",
        "stability_score",
    ]
    test_cols = [
        "candidate",
        "family",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_validation_pass",
        "test_diagnostic_pass",
    ]
    test_all3 = aggregate[aggregate["test_diagnostic_pass"]].sort_values(["test_guarded_score", "test_MAPE"])

    return f"""# PP-OPT5 Warm 집중 반복 검증

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 기준 후보: `{BASE_CANDIDATE}`
- 반복 검증: validation OOF 내부에서 `{REPEAT_COUNT}`회씩 3가지 샘플링
- 샘플링 방식: confidence stratified rows, artist group holdout, row bootstrap
- 목적: PP-OPT4에서 가능성이 보인 후보가 반복 샘플에서도 안정적인지 확인한다.

## 1. 기준 성능

{markdown_table(base, 10)}

## 2. 후보군별 요약

{markdown_table(family_summary, 20)}

## 3. 반복 검증 종합 순위

{markdown_table(aggregate[ranking_cols], 30)}

## 4. 시나리오별 안정성 상위 후보

{markdown_table(repeated_summary[scenario_cols].sort_values(['stability_score', 'mean_delta_MAPE']), 40)}

## 5. Test 진단 통과 후보

{markdown_table(test_all3[test_cols], 30)}

## 6. Test MAPE 상위 후보

{markdown_table(aggregate.sort_values(['test_MAPE', 'test_p95_APE'])[test_cols], 30)}

## 7. 해석

- 반복 검증에서 통과한 후보는 validation OOF의 여러 부분 샘플에서도 MAPE 개선이 재현된 후보로 본다.
- test_diagnostic_pass는 fixed test에서 MdAPE, MAPE가 개선되고 p95 악화가 0.005 이하인 후보를 뜻한다.
- CatBoost 계열은 MAPE 개선 폭이 크지만 p95가 흔들리는지 확인해야 한다.
- XGBoost medium-only 계열은 개선 폭은 작아도 p95 방어가 되는지 확인하는 후보로 둔다.
- 이 단계의 목적은 최종 모델 선택이 아니라, 다음 재학습/운영 후보를 줄이는 것이다.

## 8. 산출물

- `outputs/full_candidate_metrics.csv`
- `outputs/repeated_validation_detail.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/aggregate_candidate_stability.csv`
- `outputs/focused_candidate_predictions.csv`
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
  <title>PP-OPT5 Warm focused repeated validation</title>
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
    base = load_base()

    source = source_predictions(base)
    catboost = catboost_predictions(base)
    artist = artist_predictions(base)
    xgboost = xgboost_route_predictions(base)
    first_stage = pd.concat([source, catboost, artist, xgboost], ignore_index=True)
    first_metrics = summarize_predictions(first_stage)
    combo = combined_catboost_artist_predictions(base, catboost, artist, first_metrics)
    predictions = pd.concat([first_stage, combo], ignore_index=True) if not combo.empty else first_stage
    full_metrics = summarize_predictions(predictions)

    family_map = predictions[["candidate", "family"]].drop_duplicates().set_index("candidate")["family"]
    val_meta, val_wide = build_prediction_matrix(predictions, "validation_oof")
    repeated_detail, repeated_summary = repeated_validation_summary(val_meta, val_wide, family_map)
    aggregate = aggregate_candidate_stability(repeated_summary, full_metrics)

    predictions.to_csv(OUT_DIR / "focused_candidate_predictions.csv", index=False)
    full_metrics.to_csv(OUT_DIR / "full_candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)

    report = render_report(full_metrics, repeated_summary, aggregate)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_from_markdown(report), encoding="utf-8")

    config = {
        "experiment_id": "PP-OPT5",
        "base_candidate": BASE_CANDIDATE,
        "random_seed": RANDOM_SEED,
        "repeat_count_per_scenario": REPEAT_COUNT,
        "sample_frac": SAMPLE_FRAC,
        "sources": {
            "hcoef20": str(HCOEF20.relative_to(REPO)),
            "cf1": str(CF1.relative_to(REPO)),
            "cf3_raw": str(CF3_RAW.relative_to(REPO)),
            "amw10": str(AMW10.relative_to(REPO)),
        },
        "candidate_count": int(full_metrics["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "validation_rows": int(len(val_meta)),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nTop aggregate candidates:")
    cols = [
        "candidate",
        "family",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_validation_pass",
        "test_diagnostic_pass",
    ]
    print(aggregate[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
