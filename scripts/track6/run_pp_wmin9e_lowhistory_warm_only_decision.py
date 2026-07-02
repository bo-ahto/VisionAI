#!/usr/bin/env python3
"""PP-WMIN9E: low-history Warm-only decision table.

This is a presentation-facing consolidation experiment. It answers whether the
1~4 history band can be served by one Warm-like path instead of Warm-lite.

The valid same-row evidence for low-history Warm is PP-WMIN9C:
WMIN8 svc-core(min1 svc_numeric Huber, 70% axis) on the same PP-WCUT4 LOO rows.
Full WMIN8 is a 5+ route and needs PPV8/router upstream features; applying the
frozen full artifact to train-held low-history rows would leak labels unless the
upstream Warm stack is retrained per hold-out. This report therefore separates:

- decision evidence we can use now: Warm-lite vs WMIN8 svc-core proxy by k
- blocked evidence: full WMIN8 1~4 direct test without upstream retraining
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WMIN9E_lowhistory_warm_only_decision"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin9e_lowhistory_warm_only_decision_summary.md"
WMIN9C = REPO / "experiments" / "track6" / "PP-WMIN9C_warm_lite_vs_wmin8_lowhistory"
WMIN9B = REPO / "experiments" / "track6" / "PP-WMIN9B_warm_lite_boundary_comparison"


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    DOC_SUMMARY.parent.mkdir(parents=True, exist_ok=True)


def fmt(value: Any) -> str:
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    if pd.isna(value):
        return ""
    return str(value)


def table_md(frame: pd.DataFrame, cols: list[str]) -> str:
    if frame.empty:
        return "_No rows_"
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in frame[cols].iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def metric_winner(wl: float, wp: float, lower_is_better: bool = True) -> str:
    if not np.isfinite(wl) or not np.isfinite(wp):
        return "insufficient"
    eps = 1e-12
    if abs(wl - wp) <= eps:
        return "tie"
    if lower_is_better:
        return "warm_lite" if wl < wp else "warm_proxy"
    return "warm_lite" if wl > wp else "warm_proxy"


def row_interpretation(row: pd.Series) -> str:
    wins = {
        "MdAPE": row["winner_MdAPE"],
        "MAPE": row["winner_MAPE"],
        "p95_APE": row["winner_p95_APE"],
    }
    wl_count = sum(v == "warm_lite" for v in wins.values())
    wp_count = sum(v == "warm_proxy" for v in wins.values())
    if wl_count == 3:
        return "Warm-lite wins all primary metrics"
    if wp_count == 3:
        return "Warm proxy wins all primary metrics"
    return (
        "Mixed: "
        f"Warm-lite wins {', '.join(k for k, v in wins.items() if v == 'warm_lite')}; "
        f"Warm proxy wins {', '.join(k for k, v in wins.items() if v == 'warm_proxy')}"
    )


def main() -> None:
    ensure_dirs()
    comp = pd.read_csv(WMIN9C / "outputs" / "comparison.csv")
    cold = pd.read_csv(WMIN9B / "outputs" / "low_history_per_k.csv")

    warm_lite = comp[comp["candidate"].eq("warm_lite")].copy()
    warm_proxy = comp[comp["candidate"].eq("wmin8_svc_core")].copy()
    paired = warm_lite.merge(
        warm_proxy,
        on="k",
        suffixes=("_warm_lite", "_warm_proxy"),
        validate="one_to_one",
    )
    paired["n"] = paired["n_warm_lite"].astype(int)
    paired = paired[
        [
            "k",
            "n",
            "MdAPE_warm_lite",
            "MAPE_warm_lite",
            "p95_APE_warm_lite",
            "MdAPE_warm_proxy",
            "MAPE_warm_proxy",
            "p95_APE_warm_proxy",
        ]
    ].copy()
    paired_k = paired[~paired["k"].astype(str).eq("all")].copy()
    paired_overall = paired[paired["k"].astype(str).eq("all")].copy()
    paired_k["k"] = paired_k["k"].astype(int)
    paired_k = paired_k.merge(
        cold.rename(columns={"history_k": "k"}),
        on="k",
        how="left",
        validate="one_to_one",
        suffixes=("", "_cold_source"),
    )
    paired = pd.concat([paired_k, paired_overall], ignore_index=True, sort=False)
    for metric in ["MdAPE", "MAPE", "p95_APE"]:
        paired[f"delta_{metric}_warm_lite_minus_warm_proxy"] = (
            paired[f"{metric}_warm_lite"] - paired[f"{metric}_warm_proxy"]
        )
        paired[f"winner_{metric}"] = [
            metric_winner(wl, wp)
            for wl, wp in zip(paired[f"{metric}_warm_lite"], paired[f"{metric}_warm_proxy"])
        ]
    paired["interpretation"] = paired.apply(row_interpretation, axis=1)

    overall = paired[paired["k"].astype(str).eq("all")].copy()
    per_k = paired[~paired["k"].astype(str).eq("all")].copy()
    per_k["k"] = per_k["k"].astype(int)
    per_k = per_k.sort_values("k")

    decision = {
        "experiment_id": "PP-WMIN9E",
        "question": "Can the 1~4 history band use Warm-only instead of Warm-lite?",
        "usable_evidence": "PP-WMIN9C same-row Warm-lite vs WMIN8 svc-core proxy by k, plus PP-WMIN9B Warm-lite vs Cold by k.",
        "full_wmin8_direct_test_status": "blocked_without_upstream_retraining",
        "full_wmin8_blocker": (
            "The 1~4 LOO rows are held out from training rows. Calling the frozen full WMIN8 artifact "
            "would reuse PPV8/upstream models trained with those rows, so the result would be label-leaky. "
            "A clean full-WMIN8 low-history test requires retraining the PPV8/upstream Warm stack per hold-out."
        ),
        "warm_only_1to4_supported_by_current_valid_evidence": False,
        "reason": (
            "Overall 1~4 Warm-lite beats WMIN8 svc-core proxy on MdAPE/MAPE/p95. "
            "By k, Warm-lite wins all metrics for k=2 and k=3; k=1 and k=4 are mixed, "
            "but Warm-lite wins representative error and the overall 1~4 decision."
        ),
    }

    per_k.to_csv(EXP / "outputs" / "per_k_warm_lite_vs_warm_proxy.csv", index=False)
    overall.to_csv(EXP / "outputs" / "overall_warm_lite_vs_warm_proxy.csv", index=False)
    pd.DataFrame([decision]).to_csv(EXP / "outputs" / "warm_only_decision.csv", index=False)
    (EXP / "artifacts" / "run_config.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = "\n".join(
        [
            "# PP-WMIN9E Low-History Warm-Only Decision",
            "",
            "## 1. Decision",
            "",
            f"- Warm-only 1~4 supported: `{decision['warm_only_1to4_supported_by_current_valid_evidence']}`",
            f"- Reason: {decision['reason']}",
            "",
            "## 2. Per-k same-row comparison",
            "",
            table_md(
                per_k,
                [
                    "k",
                    "n",
                    "MdAPE_warm_lite",
                    "MAPE_warm_lite",
                    "p95_APE_warm_lite",
                    "MdAPE_warm_proxy",
                    "MAPE_warm_proxy",
                    "p95_APE_warm_proxy",
                    "interpretation",
                ],
            ),
            "",
            "## 3. Overall 1~4 comparison",
            "",
            table_md(
                overall,
                [
                    "k",
                    "n",
                    "MdAPE_warm_lite",
                    "MAPE_warm_lite",
                    "p95_APE_warm_lite",
                    "MdAPE_warm_proxy",
                    "MAPE_warm_proxy",
                    "p95_APE_warm_proxy",
                    "interpretation",
                ],
            ),
            "",
            "## 4. Full WMIN8 direct-test status",
            "",
            f"- Status: `{decision['full_wmin8_direct_test_status']}`",
            f"- Blocker: {decision['full_wmin8_blocker']}",
            "",
        ]
    )
    (EXP / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    DOC_SUMMARY.write_text(report, encoding="utf-8")

    print(report)


if __name__ == "__main__":
    main()
