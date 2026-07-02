#!/usr/bin/env python3
"""PP-WLITE-GUARD1: Warm-inspired risk guard for Warm-lite.

Warm WMIN8 improved by keeping a primary price candidate and switching to a
more conservative alternative only when row risk is high. This experiment tests
the same idea for Warm-lite without retraining:

- baseline: current Warm-lite all6 Huber average
- risk: disagreement among c0..c5 component predictions
- alternatives: full4, lean2, single components, median/trimmed/lower means
- policies: switch/blend/clipped-downward correction when risk is high and the
  alternative is lower than the baseline by a small gap

The experiment evaluates each policy on both:
- PP-WCUT5: real low-history leave-one-out component predictions
- PP-WCUT6: frozen Warm-lite v0.1 component predictions under k truncation

This is a guard-policy screening experiment. It does not change the frozen
Warm-lite artifact by itself.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

_cb1_spec = importlib.util.spec_from_file_location(
    "cb1", SCRIPT_DIR / "run_pp_cboost1_cold_base_training_axis.py"
)
cb1 = importlib.util.module_from_spec(_cb1_spec)
_cb1_spec.loader.exec_module(cb1)


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-GUARD1_warm_lite_risk_guard"
N_BOOT = 400

SOURCES = {
    "PP-WCUT5_real_low_history": REPO
    / "experiments"
    / "track6"
    / "PP-WCUT5_warm_lite_huber_component_ablation"
    / "outputs"
    / "predictions_all_seeds.csv",
    "PP-WCUT6_frozen_truncation": REPO
    / "experiments"
    / "track6"
    / "PP-WCUT6_warm_lite_candidate_followup_validation"
    / "outputs"
    / "predictions_all_conditions.csv",
}

BASELINE = "all6_current"
PRIMARY_METRICS = ["MdAPE", "MAPE", "p95_APE"]


@dataclass(frozen=True)
class Policy:
    name: str
    alt: str
    risk_metric: str
    threshold_kind: str
    threshold_value: float
    gap: float
    mode: str
    strength: float


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)


def load_source(name: str, path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    out = pd.DataFrame(
        {
            "dataset": name,
            "seed": df["seed"].astype(int),
            "artist_key": df["artist_key"].astype(str),
            "actual_price": df["actual_price"].astype(float),
        }
    )
    if "history_k" in df.columns:
        out["k"] = df["history_k"].astype(int)
    else:
        out["k"] = df["k"].astype(int)
    for i in range(6):
        direct = f"c{i}"
        pred = f"c{i}_pred_log"
        if direct in df.columns:
            out[f"c{i}"] = df[direct].astype(float)
        elif pred in df.columns:
            out[f"c{i}"] = df[pred].astype(float)
        else:
            raise RuntimeError(f"{path} is missing component c{i}")
    out["row_id"] = np.arange(len(out))
    return out


def add_base_predictions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    comps = out[[f"c{i}" for i in range(6)]].to_numpy(dtype=float)
    sorted_comps = np.sort(comps, axis=1)
    out["all6_current"] = comps.mean(axis=1)
    out["full4_only"] = comps[:, :4].mean(axis=1)
    out["lean2_only"] = comps[:, 4:].mean(axis=1)
    for i in range(6):
        out[f"c{i}_single"] = comps[:, i]
    out["median6"] = np.median(comps, axis=1)
    out["trimmed_mean4"] = sorted_comps[:, 1:5].mean(axis=1)
    out["lower3_mean"] = sorted_comps[:, :3].mean(axis=1)
    out["lower2_mean"] = sorted_comps[:, :2].mean(axis=1)
    out["min_component"] = sorted_comps[:, 0]
    out["component_spread"] = sorted_comps[:, -1] - sorted_comps[:, 0]
    out["component_std"] = comps.std(axis=1)
    out["full_lean_gap_abs"] = (out["full4_only"] - out["lean2_only"]).abs()
    out["lean_minus_full"] = out["lean2_only"] - out["full4_only"]
    return out


def metric_record(dataset: str, candidate: str, frame: pd.DataFrame, pred_col: str) -> dict[str, object]:
    mt = cb1.mt(frame["actual_price"].to_numpy(dtype=float), frame[pred_col].to_numpy(dtype=float))
    return {
        "dataset": dataset,
        "candidate": candidate,
        "n": int(len(frame)),
        **{metric: round(float(mt[metric]), 6) for metric in PRIMARY_METRICS},
    }


def apply_policy(df: pd.DataFrame, policy: Policy) -> np.ndarray:
    base = df[BASELINE].to_numpy(dtype=float)
    alt = df[policy.alt].to_numpy(dtype=float)
    risk = df[policy.risk_metric].to_numpy(dtype=float)
    if policy.threshold_kind == "quantile":
        threshold = float(np.quantile(risk, policy.threshold_value))
    elif policy.threshold_kind == "fixed":
        threshold = policy.threshold_value
    else:
        raise ValueError(policy.threshold_kind)

    use_alt = (risk >= threshold) & (alt <= base - policy.gap)
    if policy.mode == "switch":
        pred = np.where(use_alt, alt, base)
    elif policy.mode == "blend":
        pred = np.where(use_alt, (1.0 - policy.strength) * base + policy.strength * alt, base)
    elif policy.mode == "clip_down":
        delta = np.clip(alt - base, -policy.strength, 0.0)
        pred = np.where(use_alt, base + delta, base)
    else:
        raise ValueError(policy.mode)
    return pred


def policy_grid() -> list[Policy]:
    alts = [
        "full4_only",
        "lean2_only",
        "c0_single",
        "c2_single",
        "c4_single",
        "c5_single",
        "median6",
        "trimmed_mean4",
        "lower3_mean",
        "lower2_mean",
        "min_component",
    ]
    risks = ["component_spread", "component_std", "full_lean_gap_abs"]
    thresholds: list[tuple[str, float]] = [
        ("quantile", 0.50),
        ("quantile", 0.65),
        ("quantile", 0.75),
        ("quantile", 0.85),
        ("fixed", 0.005),
        ("fixed", 0.010),
        ("fixed", 0.020),
        ("fixed", 0.050),
    ]
    gaps = [0.0, 0.0025, 0.005, 0.010, 0.020]
    modes: list[tuple[str, float]] = [
        ("switch", 1.0),
        ("blend", 0.25),
        ("blend", 0.50),
        ("clip_down", 0.020),
        ("clip_down", 0.050),
        ("clip_down", 0.100),
    ]
    policies = []
    for alt in alts:
        for risk in risks:
            for threshold_kind, threshold_value in thresholds:
                for gap in gaps:
                    for mode, strength in modes:
                        policies.append(
                            Policy(
                                name=(
                                    f"guard_alt={alt}__risk={risk}__thr={threshold_kind}{threshold_value}"
                                    f"__gap={gap}__mode={mode}{strength}"
                                ),
                                alt=alt,
                                risk_metric=risk,
                                threshold_kind=threshold_kind,
                                threshold_value=threshold_value,
                                gap=gap,
                                mode=mode,
                                strength=strength,
                            )
                        )
    return policies


def evaluate_base_candidates(df: pd.DataFrame) -> pd.DataFrame:
    candidates = [
        BASELINE,
        "full4_only",
        "lean2_only",
        "c0_single",
        "c1_single",
        "c2_single",
        "c3_single",
        "c4_single",
        "c5_single",
        "median6",
        "trimmed_mean4",
        "lower3_mean",
        "lower2_mean",
        "min_component",
    ]
    rows = []
    for dataset, group in df.groupby("dataset", sort=True):
        base = metric_record(dataset, BASELINE, group, BASELINE)
        for candidate in candidates:
            row = metric_record(dataset, candidate, group, candidate)
            for metric in PRIMARY_METRICS:
                row[f"delta_{metric}_minus_all6"] = row[metric] - base[metric]
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["dataset", "MAPE", "p95_APE", "MdAPE"])


def evaluate_policies(df: pd.DataFrame, policies: list[Policy]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_frames = []
    baseline_rows = {
        dataset: metric_record(dataset, BASELINE, group, BASELINE)
        for dataset, group in df.groupby("dataset", sort=True)
    }
    for idx, policy in enumerate(policies):
        policy_col = f"policy_{idx}"
        policy_preds = []
        for dataset, group in df.groupby("dataset", sort=True):
            pred = apply_policy(group, policy)
            temp = group[["dataset", "seed", "k", "artist_key", "row_id", "actual_price", BASELINE]].copy()
            temp[policy_col] = pred
            mt = cb1.mt(temp["actual_price"].to_numpy(dtype=float), pred)
            base = baseline_rows[dataset]
            row = {
                "policy_id": idx,
                "policy_name": policy.name,
                "dataset": dataset,
                "n": int(len(temp)),
                "alt": policy.alt,
                "risk_metric": policy.risk_metric,
                "threshold_kind": policy.threshold_kind,
                "threshold_value": policy.threshold_value,
                "gap": policy.gap,
                "mode": policy.mode,
                "strength": policy.strength,
                "changed_rate": float(np.mean(np.abs(pred - temp[BASELINE].to_numpy(dtype=float)) > 1e-12)),
                **{metric: round(float(mt[metric]), 6) for metric in PRIMARY_METRICS},
            }
            for metric in PRIMARY_METRICS:
                row[f"delta_{metric}_minus_all6"] = row[metric] - base[metric]
            rows.append(row)
            temp = temp.rename(columns={policy_col: "policy_pred_log"})
            temp["policy_id"] = idx
            policy_preds.append(temp)
        if idx % 500 == 0:
            print(f"[policy] evaluated {idx}/{len(policies)}", flush=True)
        if idx < 0:
            pred_frames.extend(policy_preds)
    return pd.DataFrame(rows), pd.DataFrame(pred_frames)


def score_policy_table(metrics: pd.DataFrame) -> pd.DataFrame:
    pivot = metrics.pivot_table(
        index=[
            "policy_id",
            "policy_name",
            "alt",
            "risk_metric",
            "threshold_kind",
            "threshold_value",
            "gap",
            "mode",
            "strength",
        ],
        columns="dataset",
        values=[
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_MdAPE_minus_all6",
            "delta_MAPE_minus_all6",
            "delta_p95_APE_minus_all6",
            "changed_rate",
        ],
        aggfunc="first",
    )
    pivot.columns = [f"{value}__{dataset}" for value, dataset in pivot.columns]
    scored = pivot.reset_index()
    delta_cols = [c for c in scored.columns if c.startswith("delta_")]
    for metric in PRIMARY_METRICS:
        cols = [c for c in scored.columns if c.startswith(f"delta_{metric}_minus_all6__")]
        scored[f"max_delta_{metric}"] = scored[cols].max(axis=1)
        scored[f"mean_delta_{metric}"] = scored[cols].mean(axis=1)
    scored["guard_score"] = (
        2.0 * scored["mean_delta_p95_APE"]
        + scored["mean_delta_MAPE"]
        + scored["mean_delta_MdAPE"]
        + 10.0 * scored["max_delta_MdAPE"].clip(lower=0)
        + 5.0 * scored["max_delta_MAPE"].clip(lower=0)
    )
    scored["strict_improves_both"] = (
        (scored["max_delta_MdAPE"] <= 0.0)
        & (scored["max_delta_MAPE"] <= 0.0)
        & (scored["max_delta_p95_APE"] <= 0.0)
    )
    scored["p95_improves_without_large_regression"] = (
        (scored["max_delta_p95_APE"] < -0.002)
        & (scored["max_delta_MdAPE"] <= 0.001)
        & (scored["max_delta_MAPE"] <= 0.001)
    )
    return scored.sort_values(["strict_improves_both", "p95_improves_without_large_regression", "guard_score"], ascending=[False, False, True])


def cross_source_selection(metrics: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Select policies on one source and report their metrics on the other source."""
    rows = []
    datasets = sorted(metrics["dataset"].unique())
    for train_dataset in datasets:
        test_candidates = [dataset for dataset in datasets if dataset != train_dataset]
        if len(test_candidates) != 1:
            continue
        test_dataset = test_candidates[0]
        train = metrics[metrics["dataset"].eq(train_dataset)].copy()
        train["score"] = (
            2.0 * train["delta_p95_APE_minus_all6"]
            + train["delta_MAPE_minus_all6"]
            + train["delta_MdAPE_minus_all6"]
            + 10.0 * train["delta_MdAPE_minus_all6"].clip(lower=0)
            + 5.0 * train["delta_MAPE_minus_all6"].clip(lower=0)
        )
        train["strict_improves"] = (
            (train["delta_MdAPE_minus_all6"] <= 0.0)
            & (train["delta_MAPE_minus_all6"] <= 0.0)
            & (train["delta_p95_APE_minus_all6"] <= 0.0)
        )
        train = train.sort_values(["strict_improves", "score"], ascending=[False, True])
        for rank, (_, train_row) in enumerate(train.head(top_n).iterrows(), start=1):
            policy_id = int(train_row["policy_id"])
            test_row = metrics[
                metrics["policy_id"].eq(policy_id) & metrics["dataset"].eq(test_dataset)
            ].iloc[0]
            rows.append(
                {
                    "train_dataset": train_dataset,
                    "test_dataset": test_dataset,
                    "rank_on_train": rank,
                    "policy_id": policy_id,
                    "policy_name": train_row["policy_name"],
                    "train_strict_improves": bool(train_row["strict_improves"]),
                    "train_delta_MdAPE": train_row["delta_MdAPE_minus_all6"],
                    "train_delta_MAPE": train_row["delta_MAPE_minus_all6"],
                    "train_delta_p95_APE": train_row["delta_p95_APE_minus_all6"],
                    "test_delta_MdAPE": test_row["delta_MdAPE_minus_all6"],
                    "test_delta_MAPE": test_row["delta_MAPE_minus_all6"],
                    "test_delta_p95_APE": test_row["delta_p95_APE_minus_all6"],
                    "test_strict_improves": bool(
                        (test_row["delta_MdAPE_minus_all6"] <= 0.0)
                        and (test_row["delta_MAPE_minus_all6"] <= 0.0)
                        and (test_row["delta_p95_APE_minus_all6"] <= 0.0)
                    ),
                }
            )
    return pd.DataFrame(rows)


def evaluate_top_bootstrap(df: pd.DataFrame, scored: pd.DataFrame, policies: list[Policy], top_n: int = 12) -> pd.DataFrame:
    top_ids = [int(x) for x in scored.head(top_n)["policy_id"].tolist()]
    rng = np.random.default_rng(20260615)
    rows = []
    for policy_id in top_ids:
        policy = policies[policy_id]
        for dataset, group in df.groupby("dataset", sort=True):
            pred = apply_policy(group, policy)
            base = group[BASELINE].to_numpy(dtype=float)
            price = group["actual_price"].to_numpy(dtype=float)
            groups = pd.Series(np.arange(len(group))).groupby(group["artist_key"].to_numpy()).apply(list)
            wins = {metric: 0 for metric in PRIMARY_METRICS}
            losses = {metric: 0 for metric in PRIMARY_METRICS}
            for _ in range(N_BOOT):
                sampled = rng.choice(len(groups), size=len(groups), replace=True)
                idx = np.concatenate([groups.iloc[i] for i in sampled])
                pm = cb1.mt(price[idx], pred[idx])
                bm = cb1.mt(price[idx], base[idx])
                for metric in PRIMARY_METRICS:
                    wins[metric] += pm[metric] < bm[metric]
                    losses[metric] += pm[metric] > bm[metric]
            row = {
                "policy_id": policy_id,
                "policy_name": policy.name,
                "dataset": dataset,
                "n_boot": N_BOOT,
            }
            for metric in PRIMARY_METRICS:
                row[f"p_policy_better_all6_{metric}"] = wins[metric] / N_BOOT
                row[f"p_policy_worse_all6_{metric}"] = losses[metric] / N_BOOT
            rows.append(row)
    return pd.DataFrame(rows)


def by_k_for_top(df: pd.DataFrame, scored: pd.DataFrame, policies: list[Policy], top_n: int = 8) -> pd.DataFrame:
    rows = []
    top_ids = [int(x) for x in scored.head(top_n)["policy_id"].tolist()]
    for policy_id in top_ids:
        policy = policies[policy_id]
        for dataset, dataset_group in df.groupby("dataset", sort=True):
            for k, group in dataset_group.groupby("k", sort=True):
                pred = apply_policy(group, policy)
                mt = cb1.mt(group["actual_price"].to_numpy(dtype=float), pred)
                bm = cb1.mt(group["actual_price"].to_numpy(dtype=float), group[BASELINE].to_numpy(dtype=float))
                row = {
                    "policy_id": policy_id,
                    "policy_name": policy.name,
                    "dataset": dataset,
                    "k": int(k),
                    "n": int(len(group)),
                    **{metric: round(float(mt[metric]), 6) for metric in PRIMARY_METRICS},
                }
                for metric in PRIMARY_METRICS:
                    row[f"delta_{metric}_minus_all6"] = row[metric] - bm[metric]
                rows.append(row)
    return pd.DataFrame(rows)


def write_report(
    base_metrics: pd.DataFrame,
    policy_metrics: pd.DataFrame,
    scored: pd.DataFrame,
    cross_source: pd.DataFrame,
    boot: pd.DataFrame,
    by_k: pd.DataFrame,
    config: dict,
) -> None:
    top = scored.head(12).copy()
    focused_base = base_metrics[
        base_metrics["candidate"].isin([BASELINE, "median6", "trimmed_mean4", "lower3_mean", "full4_only", "c0_single", "c4_single", "c5_single"])
    ].copy()
    lines = [
        "# PP-WLITE-GUARD1 Warm-lite risk guard",
        "",
        "## Purpose",
        "",
        "Test Warm-style conditional conservative routing for Warm-lite using existing component predictions.",
        "",
        "## Base candidate metrics",
        "",
        focused_base.to_string(index=False),
        "",
        "## Top guard policies",
        "",
        top.to_string(index=False),
        "",
        "## Cross-source selection check",
        "",
        cross_source.to_string(index=False),
        "",
        "## Bootstrap for top policies",
        "",
        boot.round(4).to_string(index=False),
        "",
        "## Top policies by k",
        "",
        by_k.to_string(index=False),
        "",
        "## Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = [load_source(name, path) for name, path in SOURCES.items()]
    data = add_base_predictions(pd.concat(frames, ignore_index=True))
    data.to_csv(EXP / "outputs" / "normalized_component_predictions.csv", index=False)

    base_metrics = evaluate_base_candidates(data)
    policies = policy_grid()
    print(f"[start] evaluating {len(policies)} guard policies", flush=True)
    policy_metrics, _ = evaluate_policies(data, policies)
    scored = score_policy_table(policy_metrics)
    cross_source = cross_source_selection(policy_metrics, top_n=10)
    boot = evaluate_top_bootstrap(data, scored, policies, top_n=12)
    by_k = by_k_for_top(data, scored, policies, top_n=8)

    base_metrics.to_csv(EXP / "outputs" / "base_candidate_metrics.csv", index=False)
    policy_metrics.to_csv(EXP / "outputs" / "guard_policy_metrics_long.csv", index=False)
    scored.to_csv(EXP / "outputs" / "guard_policy_scores.csv", index=False)
    cross_source.to_csv(EXP / "outputs" / "cross_source_policy_selection.csv", index=False)
    boot.to_csv(EXP / "outputs" / "top_policy_bootstrap.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "top_policy_metrics_by_k.csv", index=False)

    config = {
        "experiment_id": "PP-WLITE-GUARD1",
        "sources": {k: str(v.relative_to(REPO)) for k, v in SOURCES.items()},
        "baseline": BASELINE,
        "policy_count": len(policies),
        "bootstrap_top_n": 12,
        "n_boot": N_BOOT,
        "selection_note": "Screening experiment; any candidate must be confirmed with OOF/refit validation before adoption.",
        "warm_inspired_pattern": "Use all6 as default and conditionally move to a conservative alternative only when component-disagreement risk is high.",
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(base_metrics, policy_metrics, scored, cross_source, boot, by_k, config)

    print("[base metrics]")
    print(base_metrics.groupby("dataset").head(8).to_string(index=False), flush=True)
    print("[top guard policies]")
    print(scored.head(12).to_string(index=False), flush=True)
    print("[cross-source selection]")
    print(cross_source.to_string(index=False), flush=True)
    print("[bootstrap]")
    print(boot.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
