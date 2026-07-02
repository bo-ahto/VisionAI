#!/usr/bin/env python3
"""Run PP-HCOEF22: purpose-aware routing and confidence policy validation.

HCOEF20 and HCOEF21 produced several candidates that slightly improve MAPE or
validation p95, but none safely replaced the current HCOEF stable point
prediction. HCOEF22 therefore tests a narrower operational question:

- Can validation/OOF-only segment routing use those candidates in the segments
  where they are consistently useful?
- Can the same validation-derived signals define a practical price
  range/confidence policy without moving the point prediction?

No split, segment, weight, or routing rule is selected from fixed test or 0604
residuals. Fixed test and 0604 remain confirmation/stress checks only.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef20_warm_huber_price_basis_coefficient_refinement as h20


EXP_ID = "PP-HCOEF22"
EXP_SLUG = "PP-HCOEF22_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

H20_DIR = REPO / "experiments" / "track6" / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
H21_DIR = REPO / "experiments" / "track6" / "PP-HCOEF21_warm_huber_price_basis_coefficient_refinement"

BASELINE = h20.BASELINE
REFERENCE = h20.REFERENCE
PPV8 = h20.PPV8
SVC = h20.SVC
SEED = 20260608
N_BOOTSTRAP = 300

STABLE_TEST_P95 = h20.STABLE_TEST_P95
STABLE_0604_P95 = h20.STABLE_0604_P95

META_COLS = [
    "scope",
    "split",
    "candidate",
    "method",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "actual_log",
    "actual_price",
    "pred_log",
    "pred_price",
    "policy_move_log",
    BASELINE,
    REFERENCE,
    PPV8,
    SVC,
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_coverage_tier",
    "svc_group_level",
    "service_confidence_tier",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "medium_support_bucket",
    "log_area",
    "residual_log",
    "ape",
]


@dataclass(frozen=True)
class CandidateConfig:
    candidate: str
    method: str
    purpose: str = ""


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def fmt_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, empty: str = "| 없음 |\n| --- |") -> str:
    if df.empty:
        return empty
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt_cell(v) for v in row) + " |")
    return "\n".join(lines)


def load_selected(path: Path, source: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["source_experiment"] = source
    return df


def candidate_pool() -> pd.DataFrame:
    """Select a validation-driven candidate pool from HCOEF20/HCOEF21 results."""
    h20_sel = load_selected(H20_DIR / "outputs" / "selected_candidates.csv", "PP-HCOEF20")
    h21_sel = load_selected(H21_DIR / "outputs" / "selected_candidates.csv", "PP-HCOEF21")
    all_sel = pd.concat([h20_sel, h21_sel], ignore_index=True)

    base_names = {BASELINE, REFERENCE, PPV8, SVC}
    keep = all_sel["candidate"].isin(base_names)

    # Candidate pool is chosen from validation/OOF behavior, not fixed test or 0604.
    row_2of3 = pd.to_numeric(all_sel["row_oof_improve_count_vs_stable"], errors="coerce").fillna(0) >= 2
    artist_2of3 = pd.to_numeric(all_sel["artist_oof_improve_count_vs_stable"], errors="coerce").fillna(0) >= 2
    row_mape = pd.to_numeric(all_sel["row_oof_delta_MAPE_vs_stable"], errors="coerce").fillna(0) < -0.00025
    artist_mape = pd.to_numeric(all_sel["artist_oof_delta_MAPE_vs_stable"], errors="coerce").fillna(0) < -0.00025
    row_p95 = pd.to_numeric(all_sel["row_oof_delta_p95_APE_vs_stable"], errors="coerce").fillna(0) < -0.002
    artist_p95 = pd.to_numeric(all_sel["artist_oof_delta_p95_APE_vs_stable"], errors="coerce").fillna(0) < -0.002
    keep |= row_2of3 & artist_2of3
    keep |= row_mape & artist_mape
    keep |= row_p95 & artist_p95

    # Keep a small ranked slice so the routing search remains interpretable.
    pool = all_sel[keep].copy()
    pool["rank_score"] = (
        pd.to_numeric(pool["row_oof_MAPE"], errors="coerce").fillna(999)
        + pd.to_numeric(pool["artist_oof_MAPE"], errors="coerce").fillna(999)
        + 0.25 * pd.to_numeric(pool["row_oof_p95_APE"], errors="coerce").fillna(999)
        + 0.25 * pd.to_numeric(pool["artist_oof_p95_APE"], errors="coerce").fillna(999)
    )
    pool = pool.sort_values(["candidate", "rank_score", "source_experiment"]).drop_duplicates("candidate", keep="first")
    pool = pool.sort_values("rank_score").head(36)

    # Ensure baseline and minimum reference always exist.
    source_priority = {"PP-HCOEF21": 0, "PP-HCOEF20": 1}
    all_sel["source_rank"] = all_sel["source_experiment"].map(source_priority).fillna(9)
    required = (
        all_sel[all_sel["candidate"].isin(base_names)]
        .sort_values(["source_rank", "candidate"])
        .drop_duplicates("candidate")
    )
    pool = pd.concat([required, pool], ignore_index=True).drop_duplicates("candidate", keep="first")

    pool["source_rank"] = pool["source_experiment"].map(source_priority).fillna(9)
    pool = pool.sort_values(["source_rank", "rank_score", "candidate"]).drop_duplicates("candidate", keep="first")
    return pool.reset_index(drop=True)


def read_predictions_for_pool(pool: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source, root in [("PP-HCOEF20", H20_DIR), ("PP-HCOEF21", H21_DIR)]:
        names = set(pool.loc[pool["source_experiment"].eq(source), "candidate"])
        # Baselines are present in both files; keep them from HCOEF21 when possible.
        if source == "PP-HCOEF20":
            names -= {BASELINE, REFERENCE, PPV8, SVC}
        if source == "PP-HCOEF21":
            names |= {BASELINE, REFERENCE, PPV8, SVC}
        if not names:
            continue
        path = root / "outputs" / "candidate_predictions.csv"
        header = pd.read_csv(path, nrows=0)
        usecols = [col for col in META_COLS if col in header.columns]
        df = pd.read_csv(path, usecols=usecols, low_memory=False)
        df = df[df["candidate"].isin(names)].copy()
        df["source_experiment"] = source
        frames.append(df)
    if not frames:
        raise RuntimeError("No candidate predictions loaded.")
    out = pd.concat(frames, ignore_index=True)
    return out.drop_duplicates(["scope", "split", "_track6_row_id", "candidate"], keep="last")


def metric_for_group(group: pd.DataFrame) -> dict[str, float]:
    return h20.metric_from_arrays(
        group["actual_price"].to_numpy(dtype=float),
        group["actual_log"].to_numpy(dtype=float),
        group["pred_log"].to_numpy(dtype=float),
    )


def segment_metrics(predictions: pd.DataFrame, segment_cols: list[tuple[str, ...]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    focus = predictions[predictions["scope"].isin(["validation_oof_row", "validation_oof_artist"])].copy()
    for cols in segment_cols:
        seg_name = "+".join(cols)
        focus["__segment_value"] = focus[list(cols)].astype(str).agg(" | ".join, axis=1)
        for keys, group in focus.groupby(["scope", "candidate", "__segment_value"], dropna=False):
            scope, candidate, value = keys
            if len(group) < 15:
                continue
            m = metric_for_group(group)
            rows.append(
                {
                    "scope": scope,
                    "candidate": candidate,
                    "segment_col": seg_name,
                    "segment_value": value,
                    "n": len(group),
                    **m,
                }
            )
    seg = pd.DataFrame(rows)
    if seg.empty:
        return seg

    base = seg[seg["candidate"].eq(BASELINE)].copy()
    base = base[
        [
            "scope",
            "segment_col",
            "segment_value",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
        ]
    ].rename(
        columns={
            "MdAPE": "stable_MdAPE",
            "MAPE": "stable_MAPE",
            "p95_APE": "stable_p95_APE",
            "RMSE_log": "stable_RMSE_log",
        }
    )
    seg = seg.merge(base, on=["scope", "segment_col", "segment_value"], how="left")
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        seg[f"delta_{metric}_vs_stable"] = seg[metric] - seg[f"stable_{metric}"]
    return seg


def choose_segment_candidate(row: pd.Series, family: str) -> bool:
    if row["candidate"] == BASELINE:
        return False
    d_md = float(row["mean_delta_MdAPE"])
    d_ma = float(row["mean_delta_MAPE"])
    d_p95 = float(row["mean_delta_p95_APE"])
    if family == "mape_guard":
        return d_ma < -0.0004 and d_md <= 0.004 and d_p95 <= 0.008
    if family == "p95_guard":
        return d_p95 < -0.004 and d_md <= 0.006 and d_ma <= 0.004
    if family == "any2_guard":
        improves = int(d_md < -0.0002) + int(d_ma < -0.0002) + int(d_p95 < -0.001)
        return improves >= 2 and d_p95 <= 0.006
    raise ValueError(f"Unknown family: {family}")


def build_policy_map(seg: pd.DataFrame) -> pd.DataFrame:
    """Build routing rules from validation row+artist OOF segment performance only."""
    columns = [
        "policy_family",
        "segment_col",
        "segment_value",
        "chosen_candidate",
        "purpose",
        "n_row",
        "n_artist",
        "mean_delta_MdAPE",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "score",
    ]
    row = seg[seg["scope"].eq("validation_oof_row")].copy()
    artist = seg[seg["scope"].eq("validation_oof_artist")].copy()
    merge_cols = ["candidate", "segment_col", "segment_value"]
    both = row.merge(
        artist,
        on=merge_cols,
        suffixes=("_row", "_artist"),
        how="inner",
    )
    both = both[(both["n_row"] >= 20) & (both["n_artist"] >= 20)].copy()
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        both[f"mean_delta_{metric}"] = (
            both[f"delta_{metric}_vs_stable_row"] + both[f"delta_{metric}_vs_stable_artist"]
        ) / 2.0

    policies: list[dict[str, Any]] = []
    families = {
        "mape_guard": {
            "purpose": "MAPE 특화 후보를 p95 악화가 작은 구간에만 사용",
            "score": lambda x: x["mean_delta_MAPE"] + 0.30 * max(x["mean_delta_p95_APE"], 0.0) + 0.20 * max(x["mean_delta_MdAPE"], 0.0),
        },
        "p95_guard": {
            "purpose": "큰 오차 감소 후보를 MdAPE/MAPE 악화가 작은 구간에만 사용",
            "score": lambda x: x["mean_delta_p95_APE"] + 0.25 * max(x["mean_delta_MAPE"], 0.0) + 0.25 * max(x["mean_delta_MdAPE"], 0.0),
        },
        "any2_guard": {
            "purpose": "MdAPE/MAPE/p95 중 2개 이상 개선되는 구간에서만 대체 후보 사용",
            "score": lambda x: x["mean_delta_MdAPE"] + x["mean_delta_MAPE"] + 0.50 * x["mean_delta_p95_APE"],
        },
    }
    for family, spec in families.items():
        eligible = both[both.apply(lambda x: choose_segment_candidate(x, family), axis=1)].copy()
        if eligible.empty:
            continue
        eligible["score"] = eligible.apply(spec["score"], axis=1)
        for (seg_col, seg_val), group in eligible.groupby(["segment_col", "segment_value"], dropna=False):
            best = group.sort_values(["score", "mean_delta_MAPE", "mean_delta_p95_APE"]).iloc[0]
            policies.append(
                {
                    "policy_family": family,
                    "segment_col": seg_col,
                    "segment_value": seg_val,
                    "chosen_candidate": best["candidate"],
                    "purpose": spec["purpose"],
                    "n_row": int(best["n_row"]),
                    "n_artist": int(best["n_artist"]),
                    "mean_delta_MdAPE": float(best["mean_delta_MdAPE"]),
                    "mean_delta_MAPE": float(best["mean_delta_MAPE"]),
                    "mean_delta_p95_APE": float(best["mean_delta_p95_APE"]),
                    "score": float(best["score"]),
                }
            )
    return pd.DataFrame(policies, columns=columns)


def apply_policy_for_scope(source: pd.DataFrame, family_rules: pd.DataFrame, candidate_name: str) -> pd.DataFrame:
    """Apply one policy family to one scope/split prediction table."""
    stable = source[source["candidate"].eq(BASELINE)].copy()
    if stable.empty:
        raise RuntimeError(f"{BASELINE} prediction is missing.")
    stable = stable.drop_duplicates("_track6_row_id").set_index("_track6_row_id")

    pred_log = stable["pred_log"].copy()
    method_by_row = pd.Series("stable_default", index=stable.index, dtype=object)
    chosen_by_row = pd.Series(BASELINE, index=stable.index, dtype=object)

    for rule in family_rules.itertuples(index=False):
        cols = str(rule.segment_col).split("+")
        expected = str(rule.segment_value)
        segment_values = stable[cols].astype(str).agg(" | ".join, axis=1)
        mask = segment_values.eq(expected)
        if not mask.any():
            continue
        cand = source[source["candidate"].eq(rule.chosen_candidate)].drop_duplicates("_track6_row_id").set_index("_track6_row_id")
        common = stable.index[mask].intersection(cand.index)
        if common.empty:
            continue
        pred_log.loc[common] = cand.loc[common, "pred_log"].astype(float)
        method_by_row.loc[common] = f"{rule.policy_family}:{rule.segment_col}"
        chosen_by_row.loc[common] = rule.chosen_candidate

    out = stable.reset_index().copy()
    out["candidate"] = candidate_name
    out["method"] = "validation_segment_routing"
    out["pred_log"] = pred_log.reindex(stable.index).to_numpy(dtype=float)
    out["pred_price"] = h20.safe_exp(out["pred_log"].to_numpy(dtype=float))
    out["policy_move_log"] = out["pred_log"] - out[BASELINE].astype(float)
    out["routing_method"] = method_by_row.reindex(stable.index).to_numpy()
    out["routed_candidate"] = chosen_by_row.reindex(stable.index).to_numpy()
    out["residual_log"] = out["actual_log"].astype(float) - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"].astype(float)) / np.clip(out["actual_price"].astype(float), 1.0, None)
    out["experiment_id"] = EXP_ID
    return out


def build_policy_predictions(predictions: pd.DataFrame, policy_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for family, rules in policy_df.groupby("policy_family", dropna=False):
        for (scope, split), source in predictions.groupby(["scope", "split"], dropna=False):
            candidate_name = f"hcoef22_route_{family}"
            out = apply_policy_for_scope(source, rules, candidate_name)
            out["scope"] = scope
            out["split"] = split
            frames.append(out)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def add_range_confidence_policy(predictions: pd.DataFrame) -> pd.DataFrame:
    """Create validation-derived price range/confidence tiers for stable point prediction."""
    stable = predictions[predictions["candidate"].eq(BASELINE)].copy()
    validation = stable[stable["scope"].eq("validation_oof_row")].copy()
    q33 = float(pd.to_numeric(validation["quantile_width"], errors="coerce").quantile(0.33))
    q66 = float(pd.to_numeric(validation["quantile_width"], errors="coerce").quantile(0.66))
    q85 = float(pd.to_numeric(validation["quantile_width"], errors="coerce").quantile(0.85))

    qwidth = pd.to_numeric(stable["quantile_width"], errors="coerce")
    n = pd.to_numeric(stable["svc_group_n"], errors="coerce").fillna(0)
    conditions = [
        (qwidth <= q33) & (n >= 20),
        (qwidth <= q66) & (n >= 10),
        (qwidth <= q85) & (n >= 5),
    ]
    stable["hcoef22_confidence_tier"] = np.select(conditions, ["high", "medium", "watch"], default="low")
    stable["hcoef22_range_multiplier_low"] = np.exp(-0.50 * qwidth.clip(lower=0.25, upper=2.5))
    stable["hcoef22_range_multiplier_high"] = np.exp(0.50 * qwidth.clip(lower=0.25, upper=2.5))

    rows: list[dict[str, Any]] = []
    for (scope, split, tier), group in stable.groupby(["scope", "split", "hcoef22_confidence_tier"], dropna=False):
        if len(group) < 5:
            continue
        actual = group["actual_log"].to_numpy(dtype=float)
        pred = group["pred_log"].to_numpy(dtype=float)
        qwidth_g = pd.to_numeric(group["quantile_width"], errors="coerce").to_numpy(dtype=float)
        within = (actual >= pred - 0.5 * qwidth_g) & (actual <= pred + 0.5 * qwidth_g)
        rows.append(
            {
                "scope": scope,
                "split": split,
                "hcoef22_confidence_tier": tier,
                "n": len(group),
                "range_coverage_qwidth": float(np.nanmean(within)),
                "median_quantile_width": float(np.nanmedian(qwidth_g)),
                "median_low_multiplier": float(group["hcoef22_range_multiplier_low"].median()),
                "median_high_multiplier": float(group["hcoef22_range_multiplier_high"].median()),
                "stable_MdAPE": float(group["ape"].median()),
                "stable_MAPE": float(group["ape"].mean()),
                "stable_p95_APE": float(group["ape"].quantile(0.95)),
                "over_50pct_error_rate": float((group["ape"] > 0.50).mean()),
                "policy_rule": (
                    f"high: qwidth<=validation q33({q33:.4f}) and n>=20; "
                    f"medium: qwidth<=q66({q66:.4f}) and n>=10; "
                    f"watch: qwidth<=q85({q85:.4f}) and n>=5; else low"
                ),
            }
        )
    return pd.DataFrame(rows)


def evaluate_predictions(predictions: pd.DataFrame, configs: list[CandidateConfig]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scope, split), group in predictions.groupby(["scope", "split"], dropna=False):
        stable = group[group["candidate"].eq(BASELINE)].drop_duplicates("_track6_row_id")
        current = group[group["candidate"].eq(REFERENCE)].drop_duplicates("_track6_row_id")
        stable_metric = metric_for_group(stable)
        reference_metric = metric_for_group(current) if not current.empty else stable_metric
        for config in configs:
            cand = group[group["candidate"].eq(config.candidate)].drop_duplicates("_track6_row_id")
            if cand.empty:
                continue
            m = metric_for_group(cand)
            rows.append(
                h20.metric_row(
                    scope=scope,
                    split=split,
                    candidate=config.candidate,
                    method=config.method,
                    n=len(cand),
                    m=m,
                    stable_metric=stable_metric,
                    reference_metric=reference_metric,
                    extra={
                        "mean_policy_move_log": float(cand["policy_move_log"].mean()),
                        "mean_abs_policy_move_log": float(cand["policy_move_log"].abs().mean()),
                        "routed_share": float((cand.get("routed_candidate", BASELINE) != BASELINE).mean())
                        if "routed_candidate" in cand.columns
                        else 0.0,
                    },
                )
            )
    return pd.DataFrame(rows)


def selection_table(metrics: pd.DataFrame, bootstrap: pd.DataFrame) -> pd.DataFrame:
    selected = h20.selection_table(metrics, bootstrap)
    route_mask = selected["candidate"].str.startswith("hcoef22_route_")
    selected.loc[route_mask & selected["decision"].eq("보류"), "decision"] = "구간 라우팅 후보"
    selected.loc[route_mask & (selected["test_improve_count_vs_stable"] >= 2) & selected["fixed_test_p95_guard"], "decision"] = "구간 라우팅 개선 후보"
    selected.loc[route_mask & selected["candidate"].str.contains("mape_guard") & selected["test_MAPE"].lt(selected.loc[selected["candidate"].eq(BASELINE), "test_MAPE"].min()), "decision"] = "MAPE 특화 라우팅 후보"
    return selected


def residual_analysis(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    focus_candidates = list(dict.fromkeys([BASELINE, REFERENCE, *selected]))
    focus = predictions[predictions["candidate"].isin(focus_candidates)].copy()
    rows: list[dict[str, Any]] = []
    for col in ["svc_coverage_tier", "svc_group_n_band", "qwidth_band", "gap_band", "pred_spread_band", "medium_support_bucket"]:
        for (scope, split, candidate, value), group in focus.groupby(["scope", "split", "candidate", col], dropna=False):
            if len(group) < 5:
                continue
            rows.append(
                {
                    "scope": scope,
                    "split": split,
                    "candidate": candidate,
                    "segment_col": col,
                    "segment_value": value,
                    "n": len(group),
                    "MdAPE": float(group["ape"].median()),
                    "MAPE": float(group["ape"].mean()),
                    "p95_APE": float(group["ape"].quantile(0.95)),
                    "median_residual_log": float(group["residual_log"].median()),
                    "mean_residual_log": float(group["residual_log"].mean()),
                    "mean_abs_move_log": float(group["policy_move_log"].abs().mean()),
                }
            )
    return pd.DataFrame(rows).sort_values(["scope", "split", "segment_col", "MAPE"], ascending=[True, True, True, False])


def coefficient_or_policy_table(policy_df: pd.DataFrame, pool: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in policy_df.itertuples(index=False):
        rows.append(
            {
                "candidate": f"hcoef22_route_{row.policy_family}",
                "method": "validation_segment_routing",
                "feature": row.segment_col,
                "standardized_coefficient": np.nan,
                "raw_role": "routing_rule",
                "direction": "choose segment candidate",
                "interpretation": (
                    f"validation row/artist OOF에서 {row.segment_value} 구간의 "
                    f"{row.chosen_candidate} 후보가 stable보다 목적 지표를 개선해 해당 구간에만 적용."
                ),
                "chosen_candidate": row.chosen_candidate,
                "segment_value": row.segment_value,
                "mean_delta_MdAPE": row.mean_delta_MdAPE,
                "mean_delta_MAPE": row.mean_delta_MAPE,
                "mean_delta_p95_APE": row.mean_delta_p95_APE,
            }
        )
    for row in pool.itertuples(index=False):
        rows.append(
            {
                "candidate": row.candidate,
                "method": getattr(row, "method", "source"),
                "feature": "source_candidate",
                "standardized_coefficient": 1.0 if row.candidate in {BASELINE, REFERENCE, PPV8, SVC} else np.nan,
                "raw_role": "candidate_pool",
                "direction": "source prediction",
                "interpretation": f"{row.source_experiment}의 validation/OOF 기준 후보 풀에 포함.",
                "chosen_candidate": row.candidate,
                "segment_value": "",
                "mean_delta_MdAPE": np.nan,
                "mean_delta_MAPE": np.nan,
                "mean_delta_p95_APE": np.nan,
            }
        )
    return pd.DataFrame(rows)


def write_report(
    pool: pd.DataFrame,
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    policy_df: pd.DataFrame,
    range_df: pd.DataFrame,
    bootstrap: pd.DataFrame,
) -> None:
    top_selection = selected.head(18)[
        [
            "candidate",
            "decision",
            "row_oof_MdAPE",
            "row_oof_MAPE",
            "row_oof_p95_APE",
            "artist_oof_MdAPE",
            "artist_oof_MAPE",
            "artist_oof_p95_APE",
            "test_MdAPE",
            "test_MAPE",
            "test_p95_APE",
            "stress0604_MdAPE",
            "stress0604_MAPE",
            "stress0604_p95_APE",
        ]
    ]
    route_metrics = metrics[metrics["candidate"].str.startswith("hcoef22_route_") | metrics["candidate"].isin([BASELINE, REFERENCE])]
    route_metrics = route_metrics[route_metrics["scope"].isin(["validation_oof_row", "validation_oof_artist", "fixed_confirmation", "0604_stress"])]

    md = f"""# PP-HCOEF22 Warm Huber 목적별 라우팅/신뢰도 정책 검증

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 목적: HCOEF20~21의 MAPE/p95 후보를 validation OOF 기준 구간 라우팅으로 제한 적용할 수 있는지 검증.
- 현재 기준 후보: `{BASELINE}` = `hcoef2_size_reliability_cap005_s050`.
- 최소 비교 기준: `{REFERENCE}` = SVC 70% + PP-V8 30%.
- fixed test와 0604 residual은 정책 선택에 사용하지 않음.

## 1. 실험 설계

- 후보 풀은 HCOEF20~21의 validation/OOF 개선 신호가 있는 후보만 사용.
- 구간 선택은 validation row OOF와 artist OOF가 동시에 개선되는 경우에만 허용.
- 라우팅 축:
  - `qwidth_band`
  - `svc_coverage_tier`
  - `svc_group_n_band`
  - `gap_band`
  - `pred_spread_band`
  - `qwidth_band + svc_coverage_tier`
  - `gap_band + qwidth_band`
- 후보 유형:
  - `mape_guard`: MAPE 개선을 우선하되 MdAPE/p95 악화가 작은 구간에만 적용.
  - `p95_guard`: 큰 오차 방어를 우선하되 MdAPE/MAPE 악화가 작은 구간에만 적용.
  - `any2_guard`: MdAPE/MAPE/p95 중 2개 이상 개선되는 구간에만 적용.

## 2. 후보 풀 요약

{md_table(pool[['candidate','source_experiment','decision','row_oof_MdAPE','row_oof_MAPE','row_oof_p95_APE','artist_oof_MdAPE','artist_oof_MAPE','artist_oof_p95_APE']].head(24))}

## 3. 라우팅 후보 선택표

{md_table(policy_df[['policy_family','segment_col','segment_value','chosen_candidate','n_row','n_artist','mean_delta_MdAPE','mean_delta_MAPE','mean_delta_p95_APE']].head(40), empty='| 없음 |\\n| --- |')}

## 4. 후보 판단 요약

{md_table(top_selection)}

## 5. 가격 범위/신뢰도 정책

{md_table(range_df[['scope','split','hcoef22_confidence_tier','n','range_coverage_qwidth','median_quantile_width','stable_MdAPE','stable_MAPE','stable_p95_APE','over_50pct_error_rate']])}

## 6. Bootstrap / 반복 검증 요약

{md_table(bootstrap.sort_values(['any2_improve_prob','all3_improve_prob'], ascending=False).head(24)[['candidate','source_scope','validation_scheme','all3_improve_prob','any2_improve_prob','mean_delta_MdAPE_vs_stable','mean_delta_MAPE_vs_stable','mean_delta_p95_APE_vs_stable']] if not bootstrap.empty else pd.DataFrame(), empty='| 없음 |\\n| --- |')}

## 7. 해석

- HCOEF22는 새 계수를 test에 맞춘 실험이 아니라, validation에서 이미 확인된 후보를 특정 구간에만 제한 적용하는 실험임.
- 라우팅 후보가 `hcoef_stable` 대비 fixed test p95 `0.8064`를 넘기면 운영 기본 후보로 채택하지 않음.
- MAPE가 낮아져도 MdAPE 또는 p95가 악화되면 목적별 후보로만 유지함.
- quantile width와 표본 수는 점 예측 이동보다 가격 범위/신뢰도 표시 정책으로 쓰는 편이 더 안전한지 함께 확인함.

## 8. 판단

- 운영 기본 후보: `hcoef_stable` 유지 여부를 후보 선택표 기준으로 판단.
- MAPE 특화 후보: MAPE 개선이 있으나 p95 guard를 통과하지 못하면 별도 후보로만 유지.
- 신뢰도/범위 정책: point prediction과 분리해서 서비스 표시 정책으로 검토.

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/segment_policy_selection.csv`
- `outputs/policy_map.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/range_confidence_policy.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    report = EXP_DIR / "reports" / "result_report.md"
    report.write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h20.md_to_html(md), encoding="utf-8")

    summary = DOC_ROOT / "pp_hcoef22_warm_huber_price_basis_coefficient_refinement_summary.md"
    summary.write_text(md, encoding="utf-8")
    summary.with_suffix(".html").write_text(h20.md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    pool = candidate_pool()
    predictions = read_predictions_for_pool(pool)

    segment_cols = [
        ("qwidth_band",),
        ("svc_coverage_tier",),
        ("svc_group_n_band",),
        ("gap_band",),
        ("pred_spread_band",),
        ("qwidth_band", "svc_coverage_tier"),
        ("gap_band", "qwidth_band"),
    ]
    seg = segment_metrics(predictions, segment_cols)
    policy_df = build_policy_map(seg)
    policy_predictions = build_policy_predictions(predictions, policy_df)

    # Keep base/current plus pool candidates and policy candidates in one file.
    combined = pd.concat([predictions, policy_predictions], ignore_index=True, sort=False)

    configs = [
        CandidateConfig(candidate=row.candidate, method=getattr(row, "method", "source"), purpose="candidate_pool")
        for row in pool.itertuples(index=False)
    ]
    for family in sorted(policy_df["policy_family"].unique()) if not policy_df.empty else []:
        configs.append(CandidateConfig(candidate=f"hcoef22_route_{family}", method="validation_segment_routing", purpose="segment routing"))

    metrics = evaluate_predictions(combined, configs)
    bootstrap = h20.bootstrap_summary(combined, configs)  # type: ignore[arg-type]
    selected = selection_table(metrics, bootstrap)
    residual = residual_analysis(combined, selected.head(12)["candidate"].tolist())
    feature_or_policy = coefficient_or_policy_table(policy_df, pool)
    range_policy = add_range_confidence_policy(combined)

    pool.to_csv(EXP_DIR / "outputs" / "candidate_pool.csv", index=False)
    seg.to_csv(EXP_DIR / "outputs" / "segment_metrics.csv", index=False)
    policy_df.to_csv(EXP_DIR / "outputs" / "segment_policy_selection.csv", index=False)
    policy_df.to_csv(EXP_DIR / "outputs" / "policy_map.csv", index=False)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    combined.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    feature_or_policy.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residual.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    range_policy.to_csv(EXP_DIR / "outputs" / "range_confidence_policy.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiments": ["PP-HCOEF20", "PP-HCOEF21"],
        "baseline": BASELINE,
        "minimum_reference": REFERENCE,
        "selection_scope": "validation row/artist OOF only",
        "fixed_test_usage": "confirmation only",
        "stress0604_usage": "external stress only",
        "segment_cols": ["+".join(cols) for cols in segment_cols],
        "candidate_pool_size": int(len(pool)),
        "policy_rule_count": int(len(policy_df)),
        "n_bootstrap": N_BOOTSTRAP,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(pool, metrics, selected, policy_df, range_policy, bootstrap)
    print(f"[{EXP_ID}] complete")
    print(f"outputs: {EXP_DIR}")
    print(selected.head(10)[["candidate", "decision", "test_MdAPE", "test_MAPE", "test_p95_APE", "stress0604_MdAPE", "stress0604_MAPE", "stress0604_p95_APE"]].to_string(index=False))


if __name__ == "__main__":
    main()
