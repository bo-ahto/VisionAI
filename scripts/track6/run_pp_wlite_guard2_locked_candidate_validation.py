#!/usr/bin/env python3
"""PP-WLITE-GUARD2: locked Warm-lite guard candidate validation.

PP-WLITE-GUARD1 screened many Warm-style guard policies. This script locks the
most deployable cross-source candidate and validates it without further tuning.

Locked candidate:
- baseline: all6_current
- risk: component_spread = max(c0..c5) - min(c0..c5)
- trigger: component_spread >= 0.005 and c2_single <= all6_current
- prediction: 0.50 * all6_current + 0.50 * c2_single

The policy is evaluated on:
- PP-WCUT5 real low-history leave-one-out predictions
- PP-WCUT6 frozen Warm-lite v0.1 k-truncation predictions

This is still an offline validation over existing component predictions. A
production adoption would need the same formula added to the Warm-lite runtime
and parity-tested against these outputs.
"""
from __future__ import annotations

import importlib.util
import json
import sys
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
EXP = REPO / "experiments" / "track6" / "PP-WLITE-GUARD2_locked_candidate_validation"
N_BOOT = 600
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


def add_candidates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    comps = out[[f"c{i}" for i in range(6)]].to_numpy(dtype=float)
    sorted_comps = np.sort(comps, axis=1)
    out["all6_current"] = comps.mean(axis=1)
    out["c2_single"] = comps[:, 2]
    out["full4_only"] = comps[:, :4].mean(axis=1)
    out["component_spread"] = sorted_comps[:, -1] - sorted_comps[:, 0]
    out["guard_trigger"] = (out["component_spread"] >= 0.005) & (out["c2_single"] <= out["all6_current"])
    out["guard_c2_blend_spread005"] = np.where(
        out["guard_trigger"],
        0.50 * out["all6_current"] + 0.50 * out["c2_single"],
        out["all6_current"],
    )
    return out


def metrics(actual_price: pd.Series | np.ndarray, pred_log: pd.Series | np.ndarray) -> dict[str, float]:
    return {metric: float(value) for metric, value in cb1.mt(np.asarray(actual_price, dtype=float), np.asarray(pred_log, dtype=float)).items()}


def metric_rows(df: pd.DataFrame, group_cols: list[str], candidates: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(group_cols, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_cols, keys))
        baseline = metrics(group["actual_price"], group["all6_current"])
        for candidate in candidates:
            mt = metrics(group["actual_price"], group[candidate])
            row = {**base, "candidate": candidate, "n": int(len(group))}
            row.update({metric: round(mt[metric], 6) for metric in PRIMARY_METRICS})
            row["changed_rate"] = float(np.mean(np.abs(group[candidate].to_numpy() - group["all6_current"].to_numpy()) > 1e-12))
            for metric in PRIMARY_METRICS:
                row[f"delta_{metric}_minus_all6"] = mt[metric] - baseline[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_overall(df: pd.DataFrame, candidate: str) -> pd.DataFrame:
    rng = np.random.default_rng(20260615)
    rows = []
    for dataset, group in df.groupby("dataset", sort=True):
        price = group["actual_price"].to_numpy(dtype=float)
        base = group["all6_current"].to_numpy(dtype=float)
        pred = group[candidate].to_numpy(dtype=float)
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
        row = {"dataset": dataset, "candidate": candidate, "n_boot": N_BOOT}
        for metric in PRIMARY_METRICS:
            row[f"p_candidate_better_all6_{metric}"] = wins[metric] / N_BOOT
            row[f"p_candidate_worse_all6_{metric}"] = losses[metric] / N_BOOT
            row[f"p_tie_{metric}"] = ties[metric] / N_BOOT
        rows.append(row)
    return pd.DataFrame(rows)


def condition_summary(by_seed_k: pd.DataFrame, candidate: str) -> pd.DataFrame:
    cand = by_seed_k[by_seed_k["candidate"].eq(candidate)].copy()
    rows = []
    for dataset, group in cand.groupby("dataset", sort=True):
        row = {"dataset": dataset, "candidate": candidate, "conditions": int(len(group))}
        for metric in PRIMARY_METRICS:
            delta_col = f"delta_{metric}_minus_all6"
            row[f"conditions_improved_{metric}"] = int((group[delta_col] < 0).sum())
            row[f"conditions_tied_{metric}"] = int((group[delta_col] == 0).sum())
            row[f"conditions_worse_{metric}"] = int((group[delta_col] > 0).sum())
            row[f"max_regression_{metric}"] = float(group[delta_col].max())
            row[f"mean_delta_{metric}"] = float(group[delta_col].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def table_md(frame: pd.DataFrame, cols: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    view = frame[cols].copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: f"{value:.6f}")
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def write_report(
    overall: pd.DataFrame,
    by_k: pd.DataFrame,
    by_seed_k: pd.DataFrame,
    boot: pd.DataFrame,
    cond: pd.DataFrame,
    config: dict,
) -> None:
    candidate = config["locked_candidate"]
    overall_focus = overall[overall["candidate"].isin(["all6_current", "c2_single", "full4_only", candidate])].copy()
    by_k_focus = by_k[by_k["candidate"].isin(["all6_current", candidate])].copy()
    lines = [
        "# PP-WLITE-GUARD2 locked Warm-lite guard validation",
        "",
        "## Locked Policy",
        "",
        "If `component_spread >= 0.005` and `c2_single <= all6_current`, use `0.50 * all6_current + 0.50 * c2_single`; otherwise keep `all6_current`.",
        "",
        "## Overall Metrics",
        "",
        table_md(
            overall_focus,
            [
                "dataset",
                "candidate",
                "n",
                "changed_rate",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ],
        ),
        "",
        "## Metrics By k",
        "",
        table_md(
            by_k_focus,
            [
                "dataset",
                "k",
                "candidate",
                "n",
                "changed_rate",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_minus_all6",
                "delta_MAPE_minus_all6",
                "delta_p95_APE_minus_all6",
            ],
        ),
        "",
        "## Condition Summary By seed/k",
        "",
        table_md(cond, cond.columns.tolist()),
        "",
        "## Artist-cluster Bootstrap",
        "",
        table_md(boot, boot.columns.tolist()),
        "",
        "## Config",
        "",
        json.dumps(config, ensure_ascii=False, indent=2),
        "",
        "## Full seed/k table",
        "",
        by_seed_k[by_seed_k["candidate"].eq(candidate)].to_string(index=False),
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = [load_source(name, path) for name, path in SOURCES.items()]
    data = add_candidates(pd.concat(frames, ignore_index=True))
    candidate = "guard_c2_blend_spread005"
    candidates = ["all6_current", "c2_single", "full4_only", candidate]

    overall = metric_rows(data, ["dataset"], candidates)
    by_k = metric_rows(data, ["dataset", "k"], candidates)
    by_seed_k = metric_rows(data, ["dataset", "seed", "k"], candidates)
    boot = bootstrap_overall(data, candidate)
    cond = condition_summary(by_seed_k, candidate)

    config = {
        "experiment_id": "PP-WLITE-GUARD2",
        "locked_candidate": candidate,
        "formula": "if component_spread >= 0.005 and c2_single <= all6_current then 0.5*all6_current + 0.5*c2_single else all6_current",
        "sources": {name: str(path.relative_to(REPO)) for name, path in SOURCES.items()},
        "n_boot": N_BOOT,
        "status": "offline locked-policy validation; not yet adopted into runtime artifact",
    }

    data.to_csv(EXP / "outputs" / "locked_candidate_predictions.csv", index=False)
    overall.to_csv(EXP / "outputs" / "locked_candidate_metrics_overall.csv", index=False)
    by_k.to_csv(EXP / "outputs" / "locked_candidate_metrics_by_k.csv", index=False)
    by_seed_k.to_csv(EXP / "outputs" / "locked_candidate_metrics_by_seed_k.csv", index=False)
    boot.to_csv(EXP / "outputs" / "locked_candidate_bootstrap.csv", index=False)
    cond.to_csv(EXP / "outputs" / "locked_candidate_condition_summary.csv", index=False)
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(overall, by_k, by_seed_k, boot, cond, config)

    print("[overall]")
    print(
        overall[overall["candidate"].isin(["all6_current", candidate])].to_string(index=False),
        flush=True,
    )
    print("[condition summary]")
    print(cond.to_string(index=False), flush=True)
    print("[bootstrap]")
    print(boot.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
