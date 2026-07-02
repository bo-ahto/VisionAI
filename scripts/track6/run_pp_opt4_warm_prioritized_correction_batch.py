#!/usr/bin/env python3
"""Run prioritized Warm correction policy batch experiments.

The batch reuses frozen validation OOF and fixed test predictions from recent
Track6 experiments. It does not tune on test. Test metrics are diagnostic.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_DIR = REPO / "experiments" / "track6" / "PP-OPT4_warm_prioritized_correction_batch"
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
EPS = 1e-12


@dataclass(frozen=True)
class CatBoostPolicy:
    model_policy: str
    tier_profile: str
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


def metrics_for(group: pd.DataFrame, pred_col: str = "pred_log") -> dict[str, float]:
    actual_price = pd.to_numeric(group["actual_price"], errors="coerce").to_numpy(dtype=float)
    pred_log = pd.to_numeric(group[pred_col], errors="coerce").to_numpy(dtype=float)
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
    pred_log = pred_log[valid]
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual_price) / np.maximum(actual_price, EPS)
    actual_log = pd.to_numeric(group.loc[valid, "actual_log"], errors="coerce").to_numpy(dtype=float)
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
    for (candidate, eval_split, family), group in predictions.groupby(
        ["candidate", "eval_split", "family"], dropna=False
    ):
        row = {
            "candidate": candidate,
            "eval_split": eval_split,
            "family": family,
        }
        row.update(metrics_for(group))
        row["mean_abs_correction_log"] = float(
            pd.to_numeric(group["correction_log"], errors="coerce").abs().mean()
        )
        row["p95_abs_correction_log"] = float(
            pd.to_numeric(group["correction_log"], errors="coerce").abs().quantile(0.95)
        )
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
        + 0.50 * np.maximum(metrics["delta_p95_APE"].fillna(9), 0)
        + 0.25 * np.maximum(metrics["delta_MdAPE"].fillna(9), 0)
    )
    metrics["balanced_score"] = (
        metrics["delta_MAPE"].fillna(9)
        + metrics["delta_p95_APE"].fillna(9) * 0.20
        + metrics["delta_MdAPE"].fillna(9) * 0.20
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
        "svc_coverage_tier",
        "svc_group_level",
        "qwidth_band",
        "stable_pred_price_band",
        "medium_support_bucket",
        "log_area",
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

    cf1_cols = [
        "split",
        "candidate",
        "_track6_row_id",
        "confidence_tier",
        "component_prediction_spread",
        "component_prediction_range",
        "current_vs_stable_gap_abs",
        "confidence_risk_score",
    ]
    cf1 = pd.read_csv(CF1, usecols=cf1_cols)
    cf1 = cf1[cf1["candidate"] == BASE_CANDIDATE].copy()
    cf1 = cf1.drop(columns=["candidate"]).drop_duplicates(["split", "_track6_row_id"])
    base = base.merge(cf1, on=["split", "_track6_row_id"], how="left")
    base["confidence_tier"] = base["confidence_tier"].fillna("medium_confidence")
    return base


def source_predictions(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, col in [
        (BASE_CANDIDATE, "hcoef_stable"),
        (REFERENCE_CANDIDATE, "current_70_30"),
        ("svc_numeric_seed_mean", "svc_numeric_seed_mean"),
        ("ppv8_service_proxy", "ppv8_service_proxy"),
        ("l10_seq_full_generated_bucket", "l10_seq_pred_log"),
    ]:
        tmp = base.copy()
        tmp["candidate"] = candidate
        tmp["family"] = "source"
        tmp["pred_log"] = pd.to_numeric(tmp[col], errors="coerce")
        tmp["correction_log"] = tmp["pred_log"] - pd.to_numeric(tmp["hcoef_stable"], errors="coerce")
        rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


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
    elif profile == "high_only":
        mapping = {"high_confidence": 1.0, "medium_confidence": 0.0, "low_confidence": 0.0}
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
    if profile == "qcap_conservative":
        return np.minimum(cap, np.where(q <= 1.2, 0.03, np.where(q <= 1.6, 0.02, 0.005)))
    if profile == "qcap_balanced":
        return np.minimum(cap, np.where(q <= 1.2, 0.04, np.where(q <= 1.6, 0.03, 0.01)))
    raise ValueError(profile)


def catboost_policy_predictions(base: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(CF3_RAW)
    raw = raw.rename(columns={"split": "eval_split"})
    raw["split"] = raw["eval_split"].map({"validation_oof": "validation", "test": "test"})
    join_cols = ["split", "eval_split", "_track6_row_id"]
    frame = raw.merge(
        base.drop(columns=["artist_key", "artist_name_ko", "actual_log", "actual_price"], errors="ignore"),
        on=join_cols,
        how="left",
        suffixes=("", "_base"),
    )
    # Restore stable base and labels from raw/base merge preference.
    base_labels = base[
        [
            "split",
            "eval_split",
            "_track6_row_id",
            "artist_key",
            "artist_name_ko",
            "actual_log",
            "actual_price",
            "hcoef_stable",
            "current_70_30",
        ]
    ]
    frame = frame.drop(
        columns=[
            c
            for c in [
                "artist_key",
                "artist_name_ko",
                "actual_log",
                "actual_price",
                "hcoef_stable",
                "current_70_30",
            ]
            if c in frame.columns
        ]
    )
    frame = frame.merge(base_labels, on=join_cols, how="left")

    rows = []
    policies = [
        CatBoostPolicy(model_policy, tier, qcap, cap, strength)
        for model_policy in ["all_rows", "confidence_weighted", "high_mid_only"]
        for tier in [
            "same",
            "confidence_weighted_apply",
            "low_guarded",
            "high_only",
        ]
        for qcap in ["fixed", "qcap_conservative", "qcap_balanced"]
        for cap in [0.015, 0.02, 0.03, 0.05]
        for strength in [0.75, 1.00, 1.15]
    ]
    q_profiles = ["same", "qwidth_conservative", "qwidth_balanced"]

    for policy in policies:
        subset = frame[frame["model_policy"] == policy.model_policy].copy()
        if subset.empty:
            continue
        for q_profile in q_profiles:
            tier_mult = tier_multiplier(subset["confidence_tier"], policy.tier_profile)
            q_mult = qwidth_multiplier(subset["quantile_width"], q_profile)
            cap_arr = dynamic_cap(subset["quantile_width"], policy.cap, policy.cap_profile)
            raw_corr = pd.to_numeric(subset["raw_catboost_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
            correction = np.clip(raw_corr * policy.strength * tier_mult * q_mult, -cap_arr, cap_arr)
            tmp = subset.copy()
            tmp["correction_log"] = correction
            tmp["pred_log"] = pd.to_numeric(tmp["hcoef_stable"], errors="coerce") + correction
            tmp["candidate"] = (
                "catboost_resid__"
                f"model={policy.model_policy}__tier={policy.tier_profile}__qmult={q_profile}"
                f"__cap={fmt_float(policy.cap)}__capprof={policy.cap_profile}__s={fmt_float(policy.strength)}"
            )
            tmp["family"] = "catboost_residual_policy"
            rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


def fmt_float(value: float) -> str:
    return str(value).replace(".", "p")


def artist_predictions(base: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(AMW10)
    df["eval_split"] = df["split"].map(to_eval_split)
    keep_feature_sets = {
        "birth_generation",
        "birth_generation_followers",
        "birth_generation_for_sale",
        "birth_generation_total_works",
        "birth_generation_gallery",
        "birth_generation_exhibition",
    }
    df = df[df["feature_set"].isin(keep_feature_sets)].copy()
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
    df["candidate"] = "artist_meta__" + df["candidate"].astype(str)
    df["family"] = "artist_meta_residual"
    # AMW10 was trained on current_70_30 base; keep its own pred_log as source.
    return prediction_columns(df)


def dynamic_blend_predictions(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    svc = pd.to_numeric(base["svc_numeric_seed_mean"], errors="coerce")
    ppv8 = pd.to_numeric(base["ppv8_service_proxy"], errors="coerce")
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5)
    svc_n = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0)
    gap = (ppv8 - svc).abs()

    weight_defs: dict[str, np.ndarray] = {}
    for w in [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]:
        weight_defs[f"global_svc_w{fmt_float(w)}"] = np.full(len(base), w)
    weight_defs["qwidth_defensive"] = np.where(qwidth <= 1.2, 0.70, np.where(qwidth <= 1.6, 0.75, 0.85))
    weight_defs["qwidth_ppv8_when_confident"] = np.where(qwidth <= 1.2, 0.62, np.where(qwidth <= 1.6, 0.72, 0.84))
    weight_defs["svc_n_reliability"] = np.where(svc_n >= 12, 0.82, np.where(svc_n >= 5, 0.72, 0.62))
    weight_defs["gap_guard"] = np.where(gap <= 0.05, 0.62, np.where(gap <= 0.12, 0.72, 0.86))
    weight_defs["qwidth_gap_guard"] = np.where(
        (qwidth <= 1.2) & (gap <= 0.08),
        0.62,
        np.where((qwidth <= 1.6) & (gap <= 0.12), 0.72, 0.86),
    )

    for name, w in weight_defs.items():
        tmp = base.copy()
        tmp["pred_log"] = w * svc + (1.0 - w) * ppv8
        tmp["correction_log"] = tmp["pred_log"] - pd.to_numeric(tmp["hcoef_stable"], errors="coerce")
        tmp["candidate"] = f"dynamic_blend__{name}"
        tmp["family"] = "dynamic_svc_ppv8_blend"
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
        "residual_adjustment_log",
    ]
    df = pd.read_csv(CF1, usecols=usecols)
    df = df[(df["model_family"] == "xgboost") & (df["eval_split"].isin(["validation_oof", "test"]))].copy()
    df = df.merge(
        base,
        on=["split", "eval_split", "_track6_row_id"],
        how="left",
        suffixes=("_xgb", ""),
    )
    rows = []
    selected = df["candidate"].drop_duplicates().tolist()
    # Keep all global XGBoost predictions plus medium/low routing diagnostics.
    for candidate in selected:
        sub = df[df["candidate"] == candidate].copy()
        for route in ["all", "medium_only", "low_only", "medium_low"]:
            tmp = sub.copy()
            xgb_pred_col = "pred_log_xgb" if "pred_log_xgb" in tmp.columns else "pred_log"
            xgb_pred = pd.to_numeric(tmp[xgb_pred_col], errors="coerce")
            base_pred = pd.to_numeric(tmp["hcoef_stable"], errors="coerce")
            tier = tmp["confidence_tier"].astype(str)
            if route == "all":
                use = np.ones(len(tmp), dtype=bool)
            elif route == "medium_only":
                use = tier.eq("medium_confidence").to_numpy()
            elif route == "low_only":
                use = tier.eq("low_confidence").to_numpy()
            else:
                use = tier.isin(["medium_confidence", "low_confidence"]).to_numpy()
            tmp["pred_log"] = np.where(use, xgb_pred, base_pred)
            tmp["correction_log"] = tmp["pred_log"] - base_pred
            tmp["candidate"] = f"xgboost_route__{candidate}__route={route}"
            tmp["family"] = "xgboost_residual_route"
            rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True)


def select_top_candidates(metrics: pd.DataFrame, family: str, limit: int = 12) -> list[str]:
    val = metrics[
        (metrics["eval_split"] == "validation_oof")
        & (metrics["family"] == family)
        & (metrics["candidate"] != BASE_CANDIDATE)
    ].copy()
    if val.empty:
        return []
    base_p95 = float(
        metrics[
            (metrics["eval_split"] == "validation_oof") & (metrics["candidate"] == BASE_CANDIDATE)
        ]["p95_APE"].iloc[0]
    )
    guarded = val[val["p95_APE"] <= base_p95 + 0.005].sort_values(["guarded_score", "MAPE"])
    if len(guarded) < limit:
        guarded = pd.concat([guarded, val.sort_values(["guarded_score", "MAPE"])], ignore_index=True)
    return guarded["candidate"].drop_duplicates().head(limit).tolist()


def combined_catboost_artist_predictions(
    base: pd.DataFrame, catboost_preds: pd.DataFrame, artist_preds: pd.DataFrame, metrics: pd.DataFrame
) -> pd.DataFrame:
    cat_candidates = select_top_candidates(metrics, "catboost_residual_policy", limit=6)
    artist_candidates = select_top_candidates(metrics, "artist_meta_residual", limit=6)
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
    cat = catboost_preds[catboost_preds["candidate"].isin(cat_candidates)][
        key_cols + ["candidate", "correction_log"]
    ].rename(columns={"candidate": "catboost_candidate", "correction_log": "catboost_correction_log"})
    artist = artist_preds[artist_preds["candidate"].isin(artist_candidates)][
        key_cols + ["candidate", "correction_log"]
    ].rename(columns={"candidate": "artist_candidate", "correction_log": "artist_correction_log"})

    rows = []
    total_caps = [0.03, 0.04]
    cat_weights = [0.80, 1.00]
    artist_weights = [0.50, 1.00]
    for cat_name in cat_candidates:
        cat_sub = cat[cat["catboost_candidate"] == cat_name]
        for artist_name in artist_candidates:
            merged = cat_sub.merge(
                artist[artist["artist_candidate"] == artist_name],
                on=key_cols,
                how="inner",
            ).merge(base_key, on=key_cols, how="left")
            if merged.empty:
                continue
            cat_corr = pd.to_numeric(merged["catboost_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
            artist_corr = pd.to_numeric(merged["artist_correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
            for total_cap in total_caps:
                for cw in cat_weights:
                    for aw in artist_weights:
                        correction = np.clip(cw * cat_corr + aw * artist_corr, -total_cap, total_cap)
                        tmp = merged.copy()
                        tmp["correction_log"] = correction
                        tmp["pred_log"] = pd.to_numeric(tmp["hcoef_stable"], errors="coerce") + correction
                        tmp["candidate"] = (
                            "combo_cat_artist__"
                            f"cat={short_name(cat_name)}__artist={short_name(artist_name)}"
                            f"__cw={fmt_float(cw)}__aw={fmt_float(aw)}__totalcap={fmt_float(total_cap)}"
                        )
                        tmp["family"] = "catboost_artist_combo"
                        rows.append(prediction_columns(tmp))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def short_name(name: str) -> str:
    cleaned = (
        name.replace("catboost_resid__", "cb_")
        .replace("artist_meta__", "am_")
        .replace("huber_", "h_")
        .replace("ridge_", "r_")
        .replace("confidence_weighted", "cw")
        .replace("confidence", "conf")
        .replace("medium", "mid")
        .replace("generation", "gen")
        .replace("birth", "birth")
        .replace("gatenone", "gn")
        .replace("alpha0p01", "a01")
        .replace("alpha0p1", "a1")
        .replace("cap0p03", "c03")
        .replace("cap0p05", "c05")
        .replace("s0p5", "s05")
        .replace("s0p75", "s075")
    )
    return cleaned[:90]


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


def render_report(metrics: pd.DataFrame, predictions: pd.DataFrame, selected: pd.DataFrame) -> str:
    base_cols = [
        "candidate",
        "family",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "guarded_score",
        "improves_all3_vs_base",
    ]
    val = metrics[metrics["eval_split"] == "validation_oof"].sort_values(["guarded_score", "MAPE"])
    test = metrics[metrics["eval_split"] == "test"].sort_values(["MAPE", "p95_APE"])
    all3_val = val[val["improves_all3_vs_base"]]
    all3_test = test[test["improves_all3_vs_base"]]

    family_summary = (
        metrics[metrics["candidate"] != BASE_CANDIDATE]
        .groupby(["family", "eval_split"])
        .agg(
            candidates=("candidate", "nunique"),
            best_MAPE=("MAPE", "min"),
            best_MdAPE=("MdAPE", "min"),
            best_p95_APE=("p95_APE", "min"),
            all3_improved=("improves_all3_vs_base", "sum"),
        )
        .reset_index()
        .sort_values(["eval_split", "best_MAPE"])
    )

    return f"""# PP-OPT4 Warm 우선순위 보정 배치 실험

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 기준가: `{BASE_CANDIDATE}` from PP-HCOEF20
- 검증: validation OOF에서 후보 선택, fixed test는 진단용
- 목적: 최근 논의한 개선 후보를 빠뜨리지 않고 같은 기준으로 비교한다.

## 1. 실행한 우선순위

1. CatBoost residual 보정값에 p95 guard와 작은 cap 적용
2. 신뢰도 구간별 보정 라우팅
3. quantile width 기반 동적 cap/strength
4. 작가 생년/세대 중심 메타 보정
5. CatBoost 작품/신뢰도 보정 + 작가 메타 보정 합산
6. SVC 기준가와 PPV8 보조 후보의 동적 blend weight 재탐색
7. XGBoost residual을 중신뢰/저신뢰 구간에서 비교

## 2. 후보군별 요약

{markdown_table(family_summary, 80)}

## 3. Validation OOF 기준 상위 후보

{markdown_table(val[base_cols], 30)}

## 4. Validation에서 세 지표 모두 개선된 후보

{markdown_table(all3_val[base_cols], 30)}

## 5. Test 진단 상위 후보

{markdown_table(test[base_cols], 30)}

## 6. Test에서 세 지표 모두 개선된 후보

{markdown_table(all3_test[base_cols], 30)}

## 7. Validation 선택 후보의 test 대응

{markdown_table(selected, 30)}

## 8. 해석

- CatBoost/XGBoost처럼 유연한 잔차 모델은 MAPE를 낮출 수 있지만, cap과 저신뢰 구간 제어가 없으면 p95가 흔들린다.
- 작가 메타는 생년/세대 계열의 작은 보정으로 둘 때 p95 방어 신호가 가장 안정적이다.
- SVC/PPV8 동적 blend는 기준가 구조를 바꾸는 후보이므로, validation 선택과 test 진단이 일치할 때만 후속 반복 검증으로 승격한다.
- 이번 배치는 기존 OOF 산출물을 재조합한 1차 screening이다. 최종 반영 전에는 선택 후보만 별도 재학습/repeated holdout으로 확인해야 한다.

## 9. 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_predictions_sample.csv`
- `outputs/validation_selected_test_counterparts.csv`
- `outputs/family_summary.csv`
- `reports/result_report.md`
- `reports/result_report.html`
- `artifacts/run_config.json`
"""


def html_from_markdown(markdown: str) -> str:
    escaped = (
        markdown.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-OPT4 Warm correction batch</title>
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
    catboost = catboost_policy_predictions(base)
    artist = artist_predictions(base)
    dynamic_blend = dynamic_blend_predictions(base)
    xgboost = xgboost_route_predictions(base)

    first_stage = pd.concat([source, catboost, artist, dynamic_blend, xgboost], ignore_index=True)
    first_metrics = summarize_predictions(first_stage)
    combo = combined_catboost_artist_predictions(base, catboost, artist, first_metrics)
    predictions = pd.concat([first_stage, combo], ignore_index=True) if not combo.empty else first_stage
    metrics = summarize_predictions(predictions)

    val_selected = (
        metrics[
            (metrics["eval_split"] == "validation_oof")
            & (metrics["candidate"] != BASE_CANDIDATE)
            & (
                (metrics["p95_APE"] <= metrics["base_p95_APE"] + 0.005)
                | (metrics["improves_all3_vs_base"])
            )
        ]
        .sort_values(["guarded_score", "MAPE"])
        .head(30)
    )
    selected = val_selected[
        ["candidate", "family", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]
    ].rename(
        columns={
            "MdAPE": "validation_MdAPE",
            "MAPE": "validation_MAPE",
            "p95_APE": "validation_p95_APE",
            "delta_MdAPE": "validation_delta_MdAPE",
            "delta_MAPE": "validation_delta_MAPE",
            "delta_p95_APE": "validation_delta_p95_APE",
        }
    )
    test_counter = metrics[metrics["eval_split"] == "test"][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "improves_all3_vs_base"]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "delta_MdAPE": "test_delta_MdAPE",
            "delta_MAPE": "test_delta_MAPE",
            "delta_p95_APE": "test_delta_p95_APE",
            "improves_all3_vs_base": "test_improves_all3_vs_base",
        }
    )
    selected = selected.merge(test_counter, on="candidate", how="left")

    family_summary = (
        metrics[metrics["candidate"] != BASE_CANDIDATE]
        .groupby(["family", "eval_split"])
        .agg(
            candidates=("candidate", "nunique"),
            best_MAPE=("MAPE", "min"),
            best_MdAPE=("MdAPE", "min"),
            best_p95_APE=("p95_APE", "min"),
            all3_improved=("improves_all3_vs_base", "sum"),
        )
        .reset_index()
    )

    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    selected.to_csv(OUT_DIR / "validation_selected_test_counterparts.csv", index=False)
    family_summary.to_csv(OUT_DIR / "family_summary.csv", index=False)
    sample = predictions.sort_values(["family", "candidate", "eval_split", "_track6_row_id"]).groupby(
        ["family", "candidate", "eval_split"], as_index=False
    ).head(5)
    sample.to_csv(OUT_DIR / "candidate_predictions_sample.csv", index=False)
    # The full prediction matrix is intentionally not written; the screening
    # grid is large, and metrics plus samples are sufficient for this stage.

    report = render_report(metrics, predictions, selected)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_from_markdown(report), encoding="utf-8")

    config = {
        "experiment_id": "PP-OPT4",
        "base_candidate": BASE_CANDIDATE,
        "sources": {
            "hcoef20": str(HCOEF20.relative_to(REPO)),
            "cf1": str(CF1.relative_to(REPO)),
            "cf3_raw": str(CF3_RAW.relative_to(REPO)),
            "amw10": str(AMW10.relative_to(REPO)),
        },
        "candidate_count": int(metrics["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nTop validation guarded candidates:")
    print(selected.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
