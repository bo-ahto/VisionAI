#!/usr/bin/env python3
"""Run PP-HCOEF2: conservative selection audit for PP-HCOEF1 candidates.

PP-HCOEF1 generated many coefficient/refinement candidates. This follow-up does
not re-fit models. It applies a stricter, pre-declared operating filter to the
PP-HCOEF1 outputs:

- residual Huber correction only;
- validation improves MdAPE, MAPE, and p95 versus current_70_30;
- correction cap is small enough for operational safety;
- fixed test and 0604 are used only as confirmation.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF2"
EXP_SLUG = "PP-HCOEF2_warm_huber_conservative_residual_selection"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
SOURCE_DIR = REPO / "experiments" / "track6" / "PP-HCOEF1_warm_huber_price_basis_coefficient_refinement"
REFERENCE = "current_70_30"


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def parse_candidate(candidate: str) -> dict[str, float | str | None]:
    out: dict[str, float | str | None] = {"alpha": None, "cap": None, "strength": None, "feature_set": None}
    alpha = re.search(r"_alpha([0-9.]+)_", candidate)
    cap = re.search(r"_cap([0-9.]+)_", candidate)
    strength = re.search(r"_s([0-9.]+)$", candidate)
    feature_set = re.search(r"residual_huber_(.+?)_alpha", candidate)
    if alpha:
        out["alpha"] = float(alpha.group(1))
    if cap:
        out["cap"] = float(cap.group(1))
    if strength:
        out["strength"] = float(strength.group(1))
    if feature_set:
        out["feature_set"] = feature_set.group(1)
    return out


def metric_delta(metrics: pd.DataFrame) -> pd.DataFrame:
    ref = metrics[metrics["candidate"].eq(REFERENCE)].set_index("split")
    rows: list[dict[str, Any]] = []
    for _, row in metrics.iterrows():
        if row["candidate"] == REFERENCE:
            continue
        split = row["split"]
        if split not in ref.index:
            continue
        base = ref.loc[split]
        parsed = parse_candidate(str(row["candidate"]))
        rows.append(
            {
                **row.to_dict(),
                **parsed,
                "delta_MdAPE": row["MdAPE"] - base["MdAPE"],
                "delta_MAPE": row["MAPE"] - base["MAPE"],
                "delta_p95_APE": row["p95_APE"] - base["p95_APE"],
                "improve_count": int(row["MdAPE"] < base["MdAPE"])
                + int(row["MAPE"] < base["MAPE"])
                + int(row["p95_APE"] < base["p95_APE"]),
            }
        )
    return pd.DataFrame(rows)


def select_candidates(delta: pd.DataFrame) -> pd.DataFrame:
    val = delta[delta["split"].eq("validation")].copy()
    val = val[val["method"].eq("current_residual_huber_correction")].copy()
    val = val[val["improve_count"].eq(3)].copy()
    val = val[pd.to_numeric(val["cap"], errors="coerce").le(0.05)].copy()
    val = val[pd.to_numeric(val["strength"], errors="coerce").le(0.75)].copy()
    val["selection_score"] = (
        0.40 * val["MdAPE"]
        + 0.35 * val["MAPE"]
        + 0.25 * val["p95_APE"]
        + 0.05 * pd.to_numeric(val["cap"], errors="coerce")
    )
    return val.sort_values(["selection_score", "p95_APE", "MdAPE"]).head(10)


def bootstrap_for_candidates(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    test = predictions[predictions["split"].eq("test")].copy()
    pool = [REFERENCE, *selected]
    wide = test[test["candidate"].isin(pool)].pivot_table(
        index=["_track6_row_id", "artist_key", "actual_price", "actual_log"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    )
    pool = [c for c in pool if c in wide.columns and wide[c].notna().all()]
    actual_price = wide.reset_index()["actual_price"].to_numpy(dtype=float)
    actual_log = wide.reset_index()["actual_log"].to_numpy(dtype=float)
    artists = wide.reset_index()["artist_key"].astype(str).to_numpy()
    unique_artists = np.unique(artists)
    rng = np.random.default_rng(20260607)
    rows: list[dict[str, Any]] = []
    for sample_type in ["row_bootstrap", "artist_bootstrap"]:
        for sample_idx in range(500):
            if sample_type == "row_bootstrap":
                idx = rng.integers(0, len(wide), size=len(wide))
            else:
                sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                idx = np.concatenate([np.flatnonzero(artists == a) for a in sampled_artists])
            ref_metrics = metrics_from_arrays(actual_price[idx], actual_log[idx], wide[REFERENCE].to_numpy(dtype=float)[idx])
            for candidate in pool:
                cand_metrics = metrics_from_arrays(actual_price[idx], actual_log[idx], wide[candidate].to_numpy(dtype=float)[idx])
                rows.append(
                    {
                        "sample_type": sample_type,
                        "candidate": candidate,
                        "delta_MdAPE": cand_metrics["MdAPE"] - ref_metrics["MdAPE"],
                        "delta_MAPE": cand_metrics["MAPE"] - ref_metrics["MAPE"],
                        "delta_p95_APE": cand_metrics["p95_APE"] - ref_metrics["p95_APE"],
                    }
                )
    samples = pd.DataFrame(rows)
    summary = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"], observed=False):
        summary.append(
            {
                "sample_type": sample_type,
                "candidate": candidate,
                "mean_delta_MdAPE": float(group["delta_MdAPE"].mean()),
                "mean_delta_MAPE": float(group["delta_MAPE"].mean()),
                "mean_delta_p95_APE": float(group["delta_p95_APE"].mean()),
                "MdAPE_improve_prob": float((group["delta_MdAPE"] < 0).mean()),
                "MAPE_improve_prob": float((group["delta_MAPE"] < 0).mean()),
                "p95_improve_prob": float((group["delta_p95_APE"] < 0).mean()),
            }
        )
    return pd.DataFrame(summary).sort_values(["sample_type", "mean_delta_MdAPE"])


def metrics_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    resid = actual_log - pred_log
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean(resid**2))),
    }


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(v: Any) -> str:
        if isinstance(v, (float, np.floating)):
            return f"{float(v):.4f}"
        return str(v)

    cols = [str(c) for c in data.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = "body{font-family:-apple-system,Segoe UI,sans-serif;margin:32px;color:#1f2937}table{border-collapse:collapse;width:100%;margin:12px 0}th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}th{background:#f3f4f6}"
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def main() -> None:
    ensure_dirs()
    metrics = pd.read_csv(SOURCE_DIR / "outputs" / "metrics.csv")
    predictions = pd.read_csv(SOURCE_DIR / "outputs" / "candidate_predictions.csv")
    delta = metric_delta(metrics)
    selected = select_candidates(delta)
    selected_names = selected["candidate"].astype(str).tolist()
    confirm = delta[delta["candidate"].isin(selected_names) & delta["split"].isin(["validation", "test", "0604_ex50"])].copy()
    confirm = confirm.sort_values(["candidate", "split"])
    bootstrap = bootstrap_for_candidates(predictions, selected_names[:5])

    out = EXP_DIR / "outputs"
    selected.to_csv(out / "selected_conservative_candidates.csv", index=False)
    confirm.to_csv(out / "selected_candidate_confirm_metrics.csv", index=False)
    bootstrap.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)

    best = selected.iloc[0] if not selected.empty else None
    if best is None:
        decision = "보수적 선택 기준을 만족하는 후보 없음. PP-HCOEF1 기본 판단 유지."
    else:
        decision = (
            f"반복 재검증 후보: `{best['candidate']}`. validation에서 3개 지표를 모두 개선하고 "
            f"cap={best['cap']}, strength={best['strength']}로 보정 폭이 작다."
        )

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 보수적 잔차 보정 선택 검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- source: PP-HCOEF1 outputs.",
            "- 목적: test만 좋은 후보를 배제하고, validation에서 명확히 개선된 작은 보정 후보만 분리.",
            "- 선택 기준: Huber 잔차 보정 후보, validation 3개 지표 모두 개선, cap <= 0.05, strength <= 0.75.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}",
            "- 이 후보는 즉시 v0.1 반영이 아니라 반복 split/OOF 재검증 후보로 둔다.",
            "",
            "## 2. 선택 후보",
            "",
            markdown_table(
                selected[
                    [
                        "candidate",
                        "feature_set",
                        "alpha",
                        "cap",
                        "strength",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "delta_MdAPE",
                        "delta_MAPE",
                        "delta_p95_APE",
                        "selection_score",
                    ]
                ].round(4)
            ),
            "",
            "## 3. 선택 후보 validation/test/0604 확인",
            "",
            markdown_table(
                confirm[
                    [
                        "split",
                        "candidate",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE",
                        "delta_MAPE",
                        "delta_p95_APE",
                        "improve_count",
                    ]
                ].round(4),
                max_rows=30,
            ),
            "",
            "## 4. Bootstrap 안정성",
            "",
            markdown_table(bootstrap.round(4), max_rows=20),
            "",
            "## 5. 산출물",
            "",
            "- `outputs/selected_conservative_candidates.csv`",
            "- `outputs/selected_candidate_confirm_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef2_warm_huber_conservative_residual_selection_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef2_warm_huber_conservative_residual_selection_summary.html").write_text(md_to_html(md), encoding="utf-8")

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "source_experiment": str(SOURCE_DIR.relative_to(REPO)),
        "selection_rule": "method=current_residual_huber_correction, validation improve_count=3, cap<=0.05, strength<=0.75",
        "selected": selected_names,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print(selected[["candidate", "feature_set", "alpha", "cap", "strength", "MdAPE", "MAPE", "p95_APE"]].round(4).to_string(index=False))
    print("--- confirmation ---")
    print(confirm[["split", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "improve_count"]].round(4).head(18).to_string(index=False))


if __name__ == "__main__":
    main()
