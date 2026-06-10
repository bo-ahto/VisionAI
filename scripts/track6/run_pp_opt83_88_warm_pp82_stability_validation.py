#!/usr/bin/env python3
"""Run PP-OPT83..88 Warm PP82 tail-routing stability validation.

This batch validates the PP82 operational and p95-focused tail-routing
candidates without creating new predictions.  It reuses the repeated
bootstrap/holdout protocol from PP-OPT71~75 and compares PP82 against PP64 and
PP70.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
OPT71_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt71_75_warm_pp70_stability_validation.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


val71 = load_module("pp_opt71_helpers", OPT71_SCRIPT)
BASE_CANDIDATE = val71.BASE_CANDIDATE
INCUMBENT = val71.INCUMBENT

EXP_ID = "PP-OPT83-88"
EXP_SLUG = "PP-OPT83_88_warm_pp82_stability_validation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP76_DIR = REPO / "experiments" / "track6" / "PP-OPT76_82_warm_tail_routing_experiments"
PP76_PREDS = PP76_DIR / "outputs" / "candidate_predictions.csv"
PP76_AGG = PP76_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP76_ITEMS = PP76_DIR / "outputs" / "experiment_item_summary.csv"
PP76_CONFIG = PP76_DIR / "artifacts" / "run_config.json"

SEED = 20260609

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT83",
        "priority": "1",
        "title": "fixed validation/test PP82 comparison",
        "description": "PP64, PP70, PP82 운영형, PP82 p95형을 fixed validation/test에서 비교한다.",
    },
    {
        "item_id": "PP-OPT84",
        "priority": "2",
        "title": "validation repeated stability",
        "description": "validation OOF에서 confidence, price, artist, risk 기반 반복 부분표본 승률을 계산한다.",
    },
    {
        "item_id": "PP-OPT85",
        "priority": "3",
        "title": "test bootstrap stress stability",
        "description": "fixed test를 bootstrap/stratified resample하여 후보 간 승률을 계산한다.",
    },
    {
        "item_id": "PP-OPT86",
        "priority": "4",
        "title": "PP82 operational replacement decision",
        "description": "PP82 운영형을 PP64/PP70의 운영 기준으로 교체할 수 있는지 판단한다.",
    },
    {
        "item_id": "PP-OPT87",
        "priority": "5",
        "title": "PP82 p95 mode decision",
        "description": "PP82 p95형을 운영 기본값이 아닌 tail 안정성 우선 모드로 둘지 판단한다.",
    },
    {
        "item_id": "PP-OPT88",
        "priority": "6",
        "title": "next experiment recommendation",
        "description": "PP82 검증 결과를 바탕으로 다음 실험 방향을 정리한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 70) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 70) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def select_candidates() -> tuple[dict[str, str], dict[str, Any]]:
    config = load_json(PP76_CONFIG)
    decision = config["selection_decision"]
    labels: dict[str, str] = {
        "hcoef_stable_source": BASE_CANDIDATE,
        "incumbent_pp7": INCUMBENT,
        "pp20_p95_reference": "previous_challenger_pp20",
        "pp30_p95_reference": "reference_pp30_best",
        "pp48_stability_reference": "reference_pp48_score",
        "pp52_quantile_reference": "reference_pp52_challenger",
        "pp58_mape_reference": "reference_pp58_challenger",
        "pp64_current_best": "reference_pp64_current_best",
        "pp70_refinement_candidate": "reference_pp70_refinement",
        "pp82_operational_tail_routing": decision["operational_protocol_candidate"],
        "pp82_p95_tail_routing": decision["p95_protocol_candidate"],
    }

    # Add raw item winners for context, excluding duplicates.
    agg = pd.read_csv(PP76_AGG)
    item_summary = pd.read_csv(PP76_ITEMS)
    for item_id in ["PP-OPT77", "PP-OPT78", "PP-OPT80", "PP-OPT81"]:
        row = item_summary[item_summary["item_id"].eq(item_id)]
        if not row.empty:
            labels[f"{item_id.lower().replace('-', '_')}_best"] = str(row.iloc[0]["best_candidate"])
            labels[f"{item_id.lower().replace('-', '_')}_p95_best"] = str(row.iloc[0]["p95_best_candidate"])
    top_mape = agg.sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]
    top_p95 = agg[agg["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).iloc[0]["candidate"]
    labels["top_mape_in_pp76_82"] = str(top_mape)
    labels["top_p95_with_mape_gain_in_pp76_82"] = str(top_p95)

    deduped: dict[str, str] = {}
    seen: set[str] = set()
    for label, candidate in labels.items():
        if candidate not in seen:
            deduped[label] = candidate
            seen.add(candidate)
    return deduped, config


def load_predictions(selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = [
        "candidate",
        "family",
        "item_id",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "pred_log",
        "correction_log",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    chunks = []
    for chunk in pd.read_csv(PP76_PREDS, usecols=usecols, chunksize=260_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No selected predictions loaded")
    predictions = pd.concat(chunks, ignore_index=True)
    label_lookup = {candidate: label for label, candidate in selected.items()}
    predictions["candidate_label"] = predictions["candidate"].map(label_lookup).fillna(predictions["candidate"])
    return predictions


def augment_aggregate(aggregate: pd.DataFrame) -> pd.DataFrame:
    out = aggregate.copy()
    refs = {
        "pp64": out[out["candidate_label"].eq("pp64_current_best")].iloc[0],
        "pp70": out[out["candidate_label"].eq("pp70_refinement_candidate")].iloc[0],
        "pp82_operational": out[out["candidate_label"].eq("pp82_operational_tail_routing")].iloc[0],
    }
    for ref_name, ref in refs.items():
        out[f"fixed_test_delta_vs_{ref_name}_MAPE"] = out["fixed_test_MAPE"] - float(ref["fixed_test_MAPE"])
        out[f"fixed_test_delta_vs_{ref_name}_p95_APE"] = out["fixed_test_p95_APE"] - float(ref["fixed_test_p95_APE"])
    return out


def make_decision(aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = aggregate[aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    pp70 = aggregate[aggregate["candidate_label"].eq("pp70_refinement_candidate")].iloc[0]
    op = aggregate[aggregate["candidate_label"].eq("pp82_operational_tail_routing")].iloc[0]
    p95 = aggregate[aggregate["candidate_label"].eq("pp82_p95_tail_routing")].iloc[0]

    op_replace = (
        op["fixed_test_delta_vs_pp64_MAPE"] <= 0
        and op["fixed_test_delta_vs_pp64_p95_APE"] <= 0
        and op["avg_pp64_MAPE_win_rate"] >= 0.50
        and op["avg_pp64_p95_win_rate"] >= 0.45
    )
    p95_mode_ok = (
        p95["fixed_test_delta_vs_pp64_p95_APE"] < -0.00030
        and p95["fixed_test_delta_vs_pp64_MAPE"] <= 0.00015
        and p95["avg_incumbent_MAPE_win_rate"] >= 0.95
    )
    verdict = (
        "PP82 운영형을 운영 1순위로 교체 가능"
        if op_replace
        else "PP64/PP70을 운영 기준으로 유지하고 PP82 운영형은 후보로 보류"
    )
    p95_verdict = (
        "PP82 p95형은 tail 안정성 우선 모드로 유지할 가치가 있음"
        if p95_mode_ok
        else "PP82 p95형은 p95 개선은 있으나 운영 옵션으로는 추가 검증 필요"
    )
    return {
        "operational_verdict": verdict,
        "p95_mode_verdict": p95_verdict,
        "pp82_operational_fixed_test_MAPE": float(op["fixed_test_MAPE"]),
        "pp82_operational_fixed_test_p95_APE": float(op["fixed_test_p95_APE"]),
        "pp82_operational_delta_vs_pp64_MAPE": float(op["fixed_test_delta_vs_pp64_MAPE"]),
        "pp82_operational_delta_vs_pp64_p95_APE": float(op["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp82_operational_delta_vs_pp70_MAPE": float(op["fixed_test_delta_vs_pp70_MAPE"]),
        "pp82_operational_delta_vs_pp70_p95_APE": float(op["fixed_test_delta_vs_pp70_p95_APE"]),
        "pp82_operational_avg_pp64_MAPE_win_rate": float(op["avg_pp64_MAPE_win_rate"]),
        "pp82_operational_avg_pp64_p95_win_rate": float(op["avg_pp64_p95_win_rate"]),
        "pp82_operational_avg_pp64_all3_win_rate": float(op["avg_pp64_all3_win_rate"]),
        "pp82_p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "pp82_p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "pp82_p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "pp82_p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp82_p95_avg_incumbent_MAPE_win_rate": float(p95["avg_incumbent_MAPE_win_rate"]),
        "pp82_p95_avg_incumbent_p95_win_rate": float(p95["avg_incumbent_p95_win_rate"]),
        "reference_pp64_MAPE": float(pp64["fixed_test_MAPE"]),
        "reference_pp64_p95_APE": float(pp64["fixed_test_p95_APE"]),
        "reference_pp70_MAPE": float(pp70["fixed_test_MAPE"]),
        "reference_pp70_p95_APE": float(pp70["fixed_test_p95_APE"]),
    }


def render_reports(
    fixed: pd.DataFrame,
    repeated_detail: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    aggregate: pd.DataFrame,
    selected: dict[str, str],
    parent_config: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    decision = config["decision"]
    selected_df = pd.DataFrame([{"label": label, "candidate": candidate} for label, candidate in selected.items()])
    agg_cols = [
        "candidate_label",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_vs_pp64_MAPE",
        "fixed_test_delta_vs_pp64_p95_APE",
        "fixed_test_delta_vs_pp70_MAPE",
        "fixed_test_delta_vs_pp70_p95_APE",
        "avg_delta_vs_pp64_MAPE",
        "avg_delta_vs_pp64_p95_APE",
        "avg_pp64_MAPE_win_rate",
        "avg_pp64_p95_win_rate",
        "avg_pp64_all3_win_rate",
        "avg_incumbent_MAPE_win_rate",
        "avg_incumbent_p95_win_rate",
        "replacement_score",
    ]
    fixed_cols = [
        "candidate_label",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_vs_incumbent_MAPE",
        "delta_vs_incumbent_p95_APE",
    ]
    scenario_cols = [
        "candidate_label",
        "eval_split",
        "scenario",
        "repeats",
        "mean_delta_vs_pp64_MAPE",
        "mean_delta_vs_pp64_p95_APE",
        "pp64_MAPE_win_rate",
        "pp64_p95_win_rate",
        "pp64_all3_win_rate",
        "mean_delta_vs_incumbent_MAPE",
        "mean_delta_vs_incumbent_p95_APE",
    ]
    scenario_focus = repeated_summary[
        repeated_summary["candidate_label"].isin(["pp82_operational_tail_routing", "pp82_p95_tail_routing"])
    ].sort_values(["candidate_label", "eval_split", "scenario"])
    callout = (
        f"{decision['operational_verdict']}. "
        f"PP82 운영형 vs PP64: MAPE {decision['pp82_operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['pp82_operational_delta_vs_pp64_p95_APE']:+.6f}. "
        f"{decision['p95_mode_verdict']}."
    )
    md = "\n".join(
        [
            "# PP-OPT83~88 Warm PP82 안정성 검증 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 검증 방식: 후보 추가 튜닝 없이 PP76~82 산출 후보를 반복 holdout/bootstrap으로 비교",
            f"- 결론: {callout}",
            "",
            "## 후보 라벨",
            markdown_table(selected_df, ["label", "candidate"], 50),
            "",
            "## 전체 후보 안정성 순위",
            markdown_table(aggregate, agg_cols, 50),
            "",
            "## fixed validation/test metric",
            markdown_table(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 70),
            "",
            "## PP82 시나리오별 PP64 대비 안정성",
            markdown_table(scenario_focus, scenario_cols, 40),
            "",
            "## 해석",
            "- PP82 운영형은 fixed test에서 PP64/PP70보다 MAPE와 p95가 모두 낮다.",
            "- 운영 교체 여부는 반복 검증에서 p95 승률이 충분히 따라오는지가 핵심이다.",
            "- PP82 p95형은 p95를 크게 낮추지만 MAPE가 PP64보다 높으므로 기본 운영값이 아니라 목적형 옵션으로 분리하는 것이 맞다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT83~88 Warm PP82 안정성 검증 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1280px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    li {{ margin: 6px 0; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT83~88 Warm PP82 안정성 검증 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(callout)}</div>
  <div class="grid">
    <div class="panel"><strong>비교 후보</strong>{len(selected)}개</div>
    <div class="panel"><strong>반복 검증 row</strong>{len(repeated_detail):,}개 metric</div>
    <div class="panel"><strong>PP82 운영형 MAPE</strong>{decision['pp82_operational_fixed_test_MAPE']:.6f}</div>
    <div class="panel"><strong>PP82 운영형 p95</strong>{decision['pp82_operational_fixed_test_p95_APE']:.6f}</div>
  </div>
  <h2>1. 후보 라벨</h2>
  {table_html(selected_df, ["label", "candidate"], 50)}
  <h2>2. 전체 후보 안정성 순위</h2>
  {table_html(aggregate, agg_cols, 50)}
  <h2>3. fixed validation/test metric</h2>
  {table_html(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 70)}
  <h2>4. PP82 시나리오별 PP64 대비 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 40)}
  <h2>5. 해석</h2>
  <ul>
    <li>PP82 운영형은 fixed test에서 PP64/PP70보다 MAPE와 p95가 모두 낮다.</li>
    <li>운영 교체 여부는 반복 검증에서 p95 승률이 충분히 따라오는지가 핵심이다.</li>
    <li>PP82 p95형은 p95를 크게 낮추지만 MAPE가 PP64보다 높으므로 기본 운영값이 아니라 목적형 옵션으로 분리하는 것이 맞다.</li>
  </ul>
  <h2>6. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    selected, parent_config = select_candidates()
    predictions = load_predictions(selected)
    fixed = val71.fixed_metrics(predictions)
    repeated_detail, repeated_summary = val71.repeated_metrics(predictions)
    aggregate = val71.aggregate_summary(repeated_summary, fixed)
    aggregate = augment_aggregate(aggregate)
    decision = make_decision(aggregate)
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "repeats_per_resample_scenario": val71.REPEATS,
        "sample_fraction": val71.SAMPLE_FRAC,
        "selected_candidates": selected,
        "candidate_count": len(selected),
        "validation_rows": int(predictions["eval_split"].eq("validation_oof").sum() / len(selected)),
        "test_rows": int(predictions["eval_split"].eq("test").sum() / len(selected)),
        "decision": decision,
        "items": ITEMS,
        "sources": {
            "pp76_config": str(PP76_CONFIG.relative_to(REPO)),
            "pp76_predictions": str(PP76_PREDS.relative_to(REPO)),
            "pp76_aggregate": str(PP76_AGG.relative_to(REPO)),
            "pp76_item_summary": str(PP76_ITEMS.relative_to(REPO)),
            "pp71_validation_helper": str(OPT71_SCRIPT.relative_to(REPO)),
        },
    }
    fixed.to_csv(OUT_DIR / "fixed_candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "stability_repeated_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "stability_repeated_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "stability_candidate_aggregate.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(fixed, repeated_detail, repeated_summary, aggregate, selected, parent_config, config)
    (REPORT_DIR / "pp82_stability_validation_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp82_stability_validation_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nAggregate:")
    print(
        aggregate[
            [
                "candidate_label",
                "fixed_test_MAPE",
                "fixed_test_p95_APE",
                "fixed_test_delta_vs_pp64_MAPE",
                "fixed_test_delta_vs_pp64_p95_APE",
                "fixed_test_delta_vs_pp70_MAPE",
                "fixed_test_delta_vs_pp70_p95_APE",
                "avg_delta_vs_pp64_MAPE",
                "avg_delta_vs_pp64_p95_APE",
                "avg_pp64_MAPE_win_rate",
                "avg_pp64_p95_win_rate",
                "avg_pp64_all3_win_rate",
                "replacement_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
