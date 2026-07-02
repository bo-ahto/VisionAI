#!/usr/bin/env python3
"""PP-WLITE-GUARD3: refine Warm-lite guard trigger to reduce MdAPE regressions.

PP-WLITE-GUARD2 locked a simple guard that improved overall MAPE/p95 but still
caused small MdAPE regressions in some k/seed conditions. This experiment keeps
the Warm-inspired structure and searches narrower deployable triggers:

- baseline: all6_current
- candidate alternatives: c2/full4/median/trimmed/lower means
- trigger inputs: component spread, component std, full-vs-lean gap
- k restrictions: apply only to selected history-count bands
- action: blend, switch, or clipped downward move

The goal is not to overfit a new final model. It is to find whether a narrower
guard can preserve MAPE/p95 gains while reducing k-level MdAPE regressions.
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
EXP = REPO / "experiments" / "track6" / "PP-WLITE-GUARD3_refined_trigger_search"
N_BOOT = 500
PRIMARY_METRICS = ["MdAPE", "MAPE", "p95_APE"]

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


@dataclass(frozen=True)
class Policy:
    policy_id: int
    name: str
    alt: str
    risk_metric: str
    threshold: float
    gap: float
    mode: str
    strength: float
    allowed_ks: tuple[int, ...]


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
    out["k"] = df["history_k"].astype(int) if "history_k" in df.columns else df["k"].astype(int)
    for i in range(6):
        direct_col = f"c{i}"
        pred_col = f"c{i}_pred_log"
        if direct_col in df.columns:
            out[f"c{i}"] = df[direct_col].astype(float)
        elif pred_col in df.columns:
            out[f"c{i}"] = df[pred_col].astype(float)
        else:
            raise RuntimeError(f"{path} is missing component c{i}")
    out["row_id"] = np.arange(len(out))
    return out


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    comps = out[[f"c{i}" for i in range(6)]].to_numpy(dtype=float)
    sorted_comps = np.sort(comps, axis=1)
    out["all6_current"] = comps.mean(axis=1)
    out["c0_single"] = comps[:, 0]
    out["c2_single"] = comps[:, 2]
    out["c4_single"] = comps[:, 4]
    out["full4_only"] = comps[:, :4].mean(axis=1)
    out["lean2_only"] = comps[:, 4:].mean(axis=1)
    out["median6"] = np.median(comps, axis=1)
    out["trimmed_mean4"] = sorted_comps[:, 1:5].mean(axis=1)
    out["lower3_mean"] = sorted_comps[:, :3].mean(axis=1)
    out["lower2_mean"] = sorted_comps[:, :2].mean(axis=1)
    out["min_component"] = sorted_comps[:, 0]
    out["component_spread"] = sorted_comps[:, -1] - sorted_comps[:, 0]
    out["component_std"] = comps.std(axis=1)
    out["full_lean_gap_abs"] = (out["full4_only"] - out["lean2_only"]).abs()
    return out


def metrics(price: np.ndarray | pd.Series, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return {metric: float(value) for metric, value in cb1.mt(np.asarray(price, dtype=float), np.asarray(pred_log, dtype=float)).items()}


def policy_grid() -> list[Policy]:
    alts = ["c2_single", "full4_only", "median6", "trimmed_mean4", "lower3_mean", "lower2_mean"]
    risks = ["component_spread", "component_std", "full_lean_gap_abs"]
    thresholds = [0.005, 0.010, 0.020, 0.030, 0.050, 0.080]
    gaps = [0.0, 0.0025, 0.005, 0.010, 0.020]
    modes: list[tuple[str, float]] = [
        ("blend", 0.25),
        ("blend", 0.50),
        ("clip_down", 0.010),
        ("clip_down", 0.020),
        ("clip_down", 0.050),
        ("switch", 1.0),
    ]
    k_sets = [
        (1, 2, 3, 4),
        (1, 2, 4),
        (2, 3, 4),
        (2, 4),
        (1, 2),
        (3, 4),
        (1, 4),
        (2,),
        (3,),
        (4,),
        (1,),
    ]
    policies: list[Policy] = []
    pid = 0
    for alt in alts:
        for risk in risks:
            for threshold in thresholds:
                for gap in gaps:
                    for mode, strength in modes:
                        for allowed_ks in k_sets:
                            policies.append(
                                Policy(
                                    policy_id=pid,
                                    name=(
                                        f"alt={alt}__risk={risk}__thr={threshold}"
                                        f"__gap={gap}__mode={mode}{strength}"
                                        f"__k={'-'.join(map(str, allowed_ks))}"
                                    ),
                                    alt=alt,
                                    risk_metric=risk,
                                    threshold=threshold,
                                    gap=gap,
                                    mode=mode,
                                    strength=strength,
                                    allowed_ks=allowed_ks,
                                )
                            )
                            pid += 1
    return policies


def apply_policy(df: pd.DataFrame, policy: Policy) -> np.ndarray:
    base = df["all6_current"].to_numpy(dtype=float)
    alt = df[policy.alt].to_numpy(dtype=float)
    risk = df[policy.risk_metric].to_numpy(dtype=float)
    allowed = df["k"].isin(policy.allowed_ks).to_numpy()
    use_alt = allowed & (risk >= policy.threshold) & (alt <= base - policy.gap)
    if policy.mode == "blend":
        return np.where(use_alt, (1.0 - policy.strength) * base + policy.strength * alt, base)
    if policy.mode == "clip_down":
        delta = np.clip(alt - base, -policy.strength, 0.0)
        return np.where(use_alt, base + delta, base)
    if policy.mode == "switch":
        return np.where(use_alt, alt, base)
    raise ValueError(policy.mode)


def evaluate_policy_overall(df: pd.DataFrame, policy: Policy) -> list[dict[str, object]]:
    rows = []
    for dataset, group in df.groupby("dataset", sort=True):
        pred = apply_policy(group, policy)
        base_mt = metrics(group["actual_price"], group["all6_current"])
        mt = metrics(group["actual_price"], pred)
        row = {
            "policy_id": policy.policy_id,
            "policy_name": policy.name,
            "dataset": dataset,
            "n": int(len(group)),
            "alt": policy.alt,
            "risk_metric": policy.risk_metric,
            "threshold": policy.threshold,
            "gap": policy.gap,
            "mode": policy.mode,
            "strength": policy.strength,
            "allowed_ks": ",".join(map(str, policy.allowed_ks)),
            "changed_rate": float(np.mean(np.abs(pred - group["all6_current"].to_numpy(dtype=float)) > 1e-12)),
        }
        row.update({metric: round(mt[metric], 6) for metric in PRIMARY_METRICS})
        for metric in PRIMARY_METRICS:
            row[f"delta_{metric}_minus_all6"] = mt[metric] - base_mt[metric]
        rows.append(row)
    return rows


def evaluate_policy_by_k(df: pd.DataFrame, policy: Policy) -> list[dict[str, object]]:
    rows = []
    for (dataset, k), group in df.groupby(["dataset", "k"], sort=True):
        pred = apply_policy(group, policy)
        base_mt = metrics(group["actual_price"], group["all6_current"])
        mt = metrics(group["actual_price"], pred)
        row = {
            "policy_id": policy.policy_id,
            "policy_name": policy.name,
            "dataset": dataset,
            "k": int(k),
            "n": int(len(group)),
            "changed_rate": float(np.mean(np.abs(pred - group["all6_current"].to_numpy(dtype=float)) > 1e-12)),
        }
        row.update({metric: round(mt[metric], 6) for metric in PRIMARY_METRICS})
        for metric in PRIMARY_METRICS:
            row[f"delta_{metric}_minus_all6"] = mt[metric] - base_mt[metric]
        rows.append(row)
    return rows


def evaluate_all(df: pd.DataFrame, policies: list[Policy]) -> tuple[pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    by_k_rows = []
    for i, policy in enumerate(policies):
        overall_rows.extend(evaluate_policy_overall(df, policy))
        by_k_rows.extend(evaluate_policy_by_k(df, policy))
        if i % 1000 == 0:
            print(f"[policy] {i}/{len(policies)}", flush=True)
    return pd.DataFrame(overall_rows), pd.DataFrame(by_k_rows)


def score_policies(overall: pd.DataFrame, by_k: pd.DataFrame) -> pd.DataFrame:
    ov = overall.pivot_table(
        index=["policy_id", "policy_name", "alt", "risk_metric", "threshold", "gap", "mode", "strength", "allowed_ks"],
        columns="dataset",
        values=[*PRIMARY_METRICS, *[f"delta_{metric}_minus_all6" for metric in PRIMARY_METRICS], "changed_rate"],
        aggfunc="first",
    )
    ov.columns = [f"{value}__{dataset}" for value, dataset in ov.columns]
    scored = ov.reset_index()
    for metric in PRIMARY_METRICS:
        overall_delta_cols = [c for c in scored.columns if c.startswith(f"delta_{metric}_minus_all6__")]
        scored[f"max_overall_delta_{metric}"] = scored[overall_delta_cols].max(axis=1)
        scored[f"mean_overall_delta_{metric}"] = scored[overall_delta_cols].mean(axis=1)

    byk_summary = []
    for policy_id, group in by_k.groupby("policy_id", sort=False):
        row = {"policy_id": int(policy_id)}
        for metric in PRIMARY_METRICS:
            col = f"delta_{metric}_minus_all6"
            row[f"max_byk_delta_{metric}"] = float(group[col].max())
            row[f"mean_byk_delta_{metric}"] = float(group[col].mean())
            row[f"byk_worse_count_{metric}"] = int((group[col] > 0).sum())
        byk_summary.append(row)
    scored = scored.merge(pd.DataFrame(byk_summary), on="policy_id", how="left", validate="one_to_one")

    scored["overall_strict_improves"] = (
        (scored["max_overall_delta_MdAPE"] <= 0)
        & (scored["max_overall_delta_MAPE"] <= 0)
        & (scored["max_overall_delta_p95_APE"] <= 0)
    )
    scored["byk_guard_ok"] = (
        (scored["max_byk_delta_MdAPE"] <= 0.0005)
        & (scored["max_byk_delta_p95_APE"] <= 0.0005)
        & (scored["mean_byk_delta_MAPE"] < 0)
    )
    scored["refined_score"] = (
        2.5 * scored["mean_overall_delta_p95_APE"]
        + scored["mean_overall_delta_MAPE"]
        + scored["mean_overall_delta_MdAPE"]
        + 20.0 * scored["max_overall_delta_MdAPE"].clip(lower=0)
        + 10.0 * scored["max_byk_delta_MdAPE"].clip(lower=0)
        + 10.0 * scored["max_byk_delta_p95_APE"].clip(lower=0)
    )
    return scored.sort_values(
        ["overall_strict_improves", "byk_guard_ok", "refined_score"],
        ascending=[False, False, True],
    )


def bootstrap_top(df: pd.DataFrame, scored: pd.DataFrame, policies: list[Policy], top_n: int = 10) -> pd.DataFrame:
    policy_map = {policy.policy_id: policy for policy in policies}
    rng = np.random.default_rng(20260615)
    rows = []
    for policy_id in [int(v) for v in scored.head(top_n)["policy_id"].tolist()]:
        policy = policy_map[policy_id]
        for dataset, group in df.groupby("dataset", sort=True):
            pred = apply_policy(group, policy)
            base = group["all6_current"].to_numpy(dtype=float)
            price = group["actual_price"].to_numpy(dtype=float)
            clusters = pd.Series(np.arange(len(group))).groupby(group["artist_key"].to_numpy()).apply(list)
            wins = {metric: 0 for metric in PRIMARY_METRICS}
            losses = {metric: 0 for metric in PRIMARY_METRICS}
            ties = {metric: 0 for metric in PRIMARY_METRICS}
            for _ in range(N_BOOT):
                sampled = rng.choice(len(clusters), size=len(clusters), replace=True)
                idx = np.concatenate([clusters.iloc[i] for i in sampled])
                pm = metrics(price[idx], pred[idx])
                bm = metrics(price[idx], base[idx])
                for metric in PRIMARY_METRICS:
                    wins[metric] += pm[metric] < bm[metric]
                    losses[metric] += pm[metric] > bm[metric]
                    ties[metric] += pm[metric] == bm[metric]
            row = {"policy_id": policy_id, "policy_name": policy.name, "dataset": dataset, "n_boot": N_BOOT}
            for metric in PRIMARY_METRICS:
                row[f"p_policy_better_all6_{metric}"] = wins[metric] / N_BOOT
                row[f"p_policy_worse_all6_{metric}"] = losses[metric] / N_BOOT
                row[f"p_tie_{metric}"] = ties[metric] / N_BOOT
            rows.append(row)
    return pd.DataFrame(rows)


def table_md(frame: pd.DataFrame, cols: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[cols].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def write_report(scored: pd.DataFrame, overall: pd.DataFrame, by_k: pd.DataFrame, boot: pd.DataFrame, config: dict) -> None:
    top_ids = scored.head(8)["policy_id"].astype(int).tolist()
    top = scored[scored["policy_id"].isin(top_ids)].copy()
    top_overall = overall[overall["policy_id"].isin(top_ids)].copy()
    top_by_k = by_k[by_k["policy_id"].isin(top_ids)].copy()
    lines = [
        "# PP-WLITE-GUARD3 refined Warm-lite trigger search",
        "",
        "## Goal",
        "",
        "Search narrower Warm-lite guard triggers that reduce MdAPE/p95 regressions seen in PP-WLITE-GUARD2.",
        "",
        "## Top scored policies",
        "",
        top.to_string(index=False),
        "",
        "## Overall metrics for top policies",
        "",
        top_overall.to_string(index=False),
        "",
        "## k-level metrics for top policies",
        "",
        top_by_k.to_string(index=False),
        "",
        "## Bootstrap for top policies",
        "",
        boot.round(4).to_string(index=False),
        "",
        "## Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    data = add_features(pd.concat([load_source(name, path) for name, path in SOURCES.items()], ignore_index=True))
    policies = policy_grid()
    print(f"[start] evaluating {len(policies)} refined guard policies", flush=True)
    overall, by_k = evaluate_all(data, policies)
    scored = score_policies(overall, by_k)
    boot = bootstrap_top(data, scored, policies, top_n=10)

    data.to_csv(EXP / "outputs" / "normalized_component_predictions.csv", index=False)
    overall.to_csv(EXP / "outputs" / "refined_policy_metrics_overall.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "refined_policy_metrics_by_k.csv", index=False)
    scored.to_csv(EXP / "outputs" / "refined_policy_scores.csv", index=False)
    boot.to_csv(EXP / "outputs" / "top_policy_bootstrap.csv", index=False)

    config = {
        "experiment_id": "PP-WLITE-GUARD3",
        "sources": {name: str(path.relative_to(REPO)) for name, path in SOURCES.items()},
        "policy_count": len(policies),
        "n_boot": N_BOOT,
        "status": "refined trigger search; still offline and not adopted",
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(scored, overall, by_k, boot, config)

    print("[top scored policies]")
    print(scored.head(12).to_string(index=False), flush=True)
    print("[top overall]")
    print(overall[overall["policy_id"].isin(scored.head(3)["policy_id"])].to_string(index=False), flush=True)
    print("[bootstrap]")
    print(boot.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
