#!/usr/bin/env python3
"""Run PP-WMIN8: validation-only routing between WMIN4 and WMIN7 p95 candidates.

WMIN7 found that higher SVC weights can reduce fixed-test p95 but often trade
off fixed-test MAPE.  PP-WMIN8 therefore does not replace the whole model.
It routes only selected validation-defined risk rows from the WMIN4 selected
candidate to WMIN7 alternatives, then confirms on fixed test.

Selection uses validation only.  Fixed test is confirmation.  0604 is not used.
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wmin4_warm_min1_operational_decision as wmin4  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN8"
EXP_SLUG = "PP-WMIN8_warm_min1_weight_router"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin8_warm_min1_weight_router_summary.md"

WMIN7_PREDS = REPO / "experiments" / "track6" / "PP-WMIN7_warm_min1_weight_retuning" / "outputs" / "candidate_predictions.csv"
PP258_REFERENCE = "current_pp258_operational_reference"
WMIN4_SELECTED = "min1_huber_refit_partial"
ALT_CANDIDATES = [
    "min1_w750_huber_refit_partial",
    "min1_w775_huber_refit_partial",
    "min1_w800_huber_refit_partial",
    "min1_w850_huber_refit_partial",
    "min1_w625_huber_refit_partial",
    "min1_w650_huber_refit_partial",
    "min1_w675_huber_refit_partial",
]
RISK_QUANTILES = [0.50, 0.60, 0.70, 0.80, 0.90]
QWIDTH_THRESHOLDS = [0.80, 1.00, 1.20, 1.40, 1.60]
SPREAD_THRESHOLDS = [0.06, 0.10, 0.14, 0.18]
GAP_THRESHOLDS = [0.015, 0.030, 0.050]
ALT_GAP_THRESHOLDS = [0.005, 0.010, 0.020]
MIN_ROUTE_SHARE = 0.02
MAX_ROUTE_SHARE = 0.80


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fmt(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in view.columns) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def table_html(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "<p><em>결과 없음</em></p>"
    view = frame[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(fmt(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def load_predictions() -> pd.DataFrame:
    df = pd.read_csv(WMIN7_PREDS, low_memory=False)
    needed = {PP258_REFERENCE, WMIN4_SELECTED, *ALT_CANDIDATES}
    missing = needed - set(df["candidate_label"].dropna().astype(str))
    if missing:
        raise RuntimeError(f"Missing WMIN7 predictions: {sorted(missing)}")
    return df[df["candidate_label"].isin(needed)].copy()


def split_meta_wide(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"].eq(eval_split)].copy()
    meta_cols = [
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    meta = (
        subset[subset["candidate_label"].eq(PP258_REFERENCE)][meta_cols]
        .drop_duplicates("_track6_row_id")
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )
    wide = subset.pivot_table(index="_track6_row_id", columns="candidate_label", values="pred_log", aggfunc="first")
    wide = wide.reindex(meta["_track6_row_id"]).reset_index(drop=True)
    return meta, wide


def metric_arrays(meta: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = meta["actual_price"].to_numpy(dtype=float)
    actual_log = meta["actual_log"].to_numpy(dtype=float)
    pred = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred)
    pred_price = np.clip(np.exp(pred[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred[valid] - actual_log[valid]) ** 2))),
    }


def gate_inputs(meta: pd.DataFrame, wide: pd.DataFrame, alt: str) -> pd.DataFrame:
    out = pd.DataFrame(index=meta.index)
    out["risk_score"] = wmin4.risk_score(meta)
    out["quantile_width"] = pd.to_numeric(meta["quantile_width"], errors="coerce").fillna(1.50)
    out["component_prediction_spread"] = pd.to_numeric(meta["component_prediction_spread"], errors="coerce").fillna(0.10)
    out["current_vs_stable_gap_abs"] = pd.to_numeric(meta["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03)
    out["low_confidence"] = meta["confidence_tier"].fillna("").astype(str).eq("low_confidence")
    out["very_high_price"] = meta["stable_price_band"].fillna("").astype(str).eq("very_high_price")
    out["high_plus_price"] = meta["stable_price_band"].fillna("").astype(str).isin(["high_price", "very_high_price"])
    out["alt_gap_abs"] = np.abs(wide[alt].to_numpy(dtype=float) - wide[WMIN4_SELECTED].to_numpy(dtype=float))
    out["alt_lower"] = wide[alt].to_numpy(dtype=float) < wide[WMIN4_SELECTED].to_numpy(dtype=float)
    out["alt_higher"] = wide[alt].to_numpy(dtype=float) > wide[WMIN4_SELECTED].to_numpy(dtype=float)
    return out


def make_gate_specs(validation_meta: pd.DataFrame, validation_wide: pd.DataFrame, alt: str) -> list[dict[str, Any]]:
    data = gate_inputs(validation_meta, validation_wide, alt)
    specs: list[dict[str, Any]] = []
    for q in RISK_QUANTILES:
        threshold = float(np.nanquantile(data["risk_score"], q))
        specs.append({"name": f"risk_q{int(q * 100)}", "kind": "risk_ge", "threshold": threshold})
        for gap in ALT_GAP_THRESHOLDS:
            specs.append({"name": f"risk_q{int(q * 100)}_altgap_ge{int(gap*1000):03d}", "kind": "risk_ge_altgap_ge", "threshold": threshold, "gap": gap})
            specs.append({"name": f"risk_q{int(q * 100)}_altlower_gap{int(gap*1000):03d}", "kind": "risk_ge_altlower_gap", "threshold": threshold, "gap": gap})
            specs.append({"name": f"risk_q{int(q * 100)}_althigher_gap{int(gap*1000):03d}", "kind": "risk_ge_althigher_gap", "threshold": threshold, "gap": gap})
    for threshold in QWIDTH_THRESHOLDS:
        specs.append({"name": f"qwidth_ge{int(threshold*100):03d}", "kind": "qwidth_ge", "threshold": threshold})
    for threshold in SPREAD_THRESHOLDS:
        specs.append({"name": f"spread_ge{int(threshold*1000):03d}", "kind": "spread_ge", "threshold": threshold})
    for threshold in GAP_THRESHOLDS:
        specs.append({"name": f"gap_ge{int(threshold*1000):03d}", "kind": "gap_ge", "threshold": threshold})
    specs.extend(
        [
            {"name": "low_confidence", "kind": "low_confidence"},
            {"name": "very_high_price", "kind": "very_high_price"},
            {"name": "high_plus_price", "kind": "high_plus_price"},
        ]
    )
    return specs


def apply_gate(meta: pd.DataFrame, wide: pd.DataFrame, alt: str, spec: dict[str, Any]) -> np.ndarray:
    data = gate_inputs(meta, wide, alt)
    kind = spec["kind"]
    if kind == "risk_ge":
        mask = data["risk_score"].to_numpy(dtype=float) >= float(spec["threshold"])
    elif kind == "risk_ge_altgap_ge":
        mask = (data["risk_score"].to_numpy(dtype=float) >= float(spec["threshold"])) & (data["alt_gap_abs"].to_numpy(dtype=float) >= float(spec["gap"]))
    elif kind == "risk_ge_altlower_gap":
        mask = (
            (data["risk_score"].to_numpy(dtype=float) >= float(spec["threshold"]))
            & data["alt_lower"].to_numpy(dtype=bool)
            & (data["alt_gap_abs"].to_numpy(dtype=float) >= float(spec["gap"]))
        )
    elif kind == "risk_ge_althigher_gap":
        mask = (
            (data["risk_score"].to_numpy(dtype=float) >= float(spec["threshold"]))
            & data["alt_higher"].to_numpy(dtype=bool)
            & (data["alt_gap_abs"].to_numpy(dtype=float) >= float(spec["gap"]))
        )
    elif kind == "qwidth_ge":
        mask = data["quantile_width"].to_numpy(dtype=float) >= float(spec["threshold"])
    elif kind == "spread_ge":
        mask = data["component_prediction_spread"].to_numpy(dtype=float) >= float(spec["threshold"])
    elif kind == "gap_ge":
        mask = data["current_vs_stable_gap_abs"].to_numpy(dtype=float) >= float(spec["threshold"])
    elif kind in {"low_confidence", "very_high_price", "high_plus_price"}:
        mask = data[kind].to_numpy(dtype=bool)
    else:
        raise ValueError(f"Unknown gate kind: {kind}")
    return np.asarray(mask, dtype=bool)


def route_predictions(meta: pd.DataFrame, wide: pd.DataFrame, alt: str, mask: np.ndarray) -> np.ndarray:
    base = wide[WMIN4_SELECTED].to_numpy(dtype=float)
    alt_pred = wide[alt].to_numpy(dtype=float)
    return np.where(mask, alt_pred, base)


def candidate_frame(meta: pd.DataFrame, pred_log: np.ndarray, candidate_label: str, split: str, alt: str, gate_name: str, route_share: float) -> pd.DataFrame:
    out = meta.copy()
    out["candidate"] = candidate_label
    out["candidate_label"] = candidate_label
    out["family"] = "wmin8_min1_weight_router"
    out["item_id"] = EXP_ID
    out["eval_split"] = split
    out["pred_log"] = pred_log
    out["source_experiment"] = EXP_ID
    out["method"] = "validation_defined_candidate_router"
    out["scope"] = "fixed_confirmation"
    out["split"] = "validation" if split == "validation_oof" else "test"
    out["alt_candidate"] = alt
    out["gate_name"] = gate_name
    out["route_share"] = route_share
    return out


def build_routed_candidates(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    val_meta, val_wide = split_meta_wide(predictions, "validation_oof")
    test_meta, test_wide = split_meta_wide(predictions, "test")
    val_base_metric = metric_arrays(val_meta, val_wide[WMIN4_SELECTED].to_numpy(dtype=float))
    rows: list[pd.DataFrame] = []
    audits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for alt in ALT_CANDIDATES:
        for spec in make_gate_specs(val_meta, val_wide, alt):
            val_mask = apply_gate(val_meta, val_wide, alt, spec)
            val_share = float(val_mask.mean())
            if val_share < MIN_ROUTE_SHARE or val_share > MAX_ROUTE_SHARE:
                continue
            val_pred = route_predictions(val_meta, val_wide, alt, val_mask)
            val_metric = metric_arrays(val_meta, val_pred)
            # Keep only candidates that improve at least one validation objective and
            # do not blow up the others too much.  This pruning is validation-only.
            if (
                val_metric["MAPE"] > val_base_metric["MAPE"] + 0.003
                or val_metric["p95_APE"] > val_base_metric["p95_APE"] + 0.015
            ):
                continue
            test_mask = apply_gate(test_meta, test_wide, alt, spec)
            test_share = float(test_mask.mean())
            label_alt = alt.replace("min1_", "").replace("_huber_refit_partial", "")
            label = f"min1_route_{label_alt}_{spec['name']}"
            if label in seen:
                continue
            seen.add(label)
            test_pred = route_predictions(test_meta, test_wide, alt, test_mask)
            rows.append(candidate_frame(val_meta, val_pred, label, "validation_oof", alt, spec["name"], val_share))
            rows.append(candidate_frame(test_meta, test_pred, label, "test", alt, spec["name"], test_share))
            audits.append(
                {
                    "candidate_label": label,
                    "alt_candidate": alt,
                    "gate_name": spec["name"],
                    "gate_kind": spec["kind"],
                    "threshold": spec.get("threshold", np.nan),
                    "gap": spec.get("gap", np.nan),
                    "validation_route_share": val_share,
                    "test_route_share": test_share,
                    **{f"validation_{key}": value for key, value in val_metric.items()},
                }
            )
    if not rows:
        raise RuntimeError("No routed candidates survived validation pruning")
    return pd.concat(rows, ignore_index=True), pd.DataFrame(audits)


def comparison_vs_wmin4(fixed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    new_rows = fixed[fixed["candidate_label"].str.startswith("min1_route_", na=False)].copy()
    for split, group in new_rows.groupby("eval_split", dropna=False):
        base = fixed[(fixed["eval_split"].eq(split)) & (fixed["candidate_label"].eq(WMIN4_SELECTED))]
        if base.empty:
            continue
        base_row = base.iloc[0]
        for _, row in group.iterrows():
            rows.append(
                {
                    "candidate_label": row["candidate_label"],
                    "eval_split": split,
                    "delta_MdAPE_vs_wmin4_selected": float(row["MdAPE"] - base_row["MdAPE"]),
                    "delta_MAPE_vs_wmin4_selected": float(row["MAPE"] - base_row["MAPE"]),
                    "delta_p95_APE_vs_wmin4_selected": float(row["p95_APE"] - base_row["p95_APE"]),
                    "delta_RMSE_log_vs_wmin4_selected": float(row["RMSE_log"] - base_row["RMSE_log"]),
                }
            )
    return pd.DataFrame(rows)


def render_report(
    aggregate: pd.DataFrame,
    fixed: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    gate_audit: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    agg_cols = [
        "candidate_label",
        "passes_validation_gate",
        "passes_fixed_confirmation",
        "fixed_validation_MdAPE",
        "fixed_validation_MAPE",
        "fixed_validation_p95_APE",
        "validation_avg_MAPE_win_rate",
        "validation_avg_p95_win_rate",
        "validation_replacement_score",
        "fixed_test_MdAPE",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_MAPE_vs_current_pp258",
        "fixed_test_delta_p95_vs_current_pp258",
    ]
    fixed_cols = [
        "candidate_label",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_vs_current_pp258_MAPE",
        "delta_vs_current_pp258_p95_APE",
    ]
    comp_cols = [
        "candidate_label",
        "eval_split",
        "delta_MdAPE_vs_wmin4_selected",
        "delta_MAPE_vs_wmin4_selected",
        "delta_p95_APE_vs_wmin4_selected",
        "delta_RMSE_log_vs_wmin4_selected",
    ]
    audit_cols = [
        "candidate_label",
        "alt_candidate",
        "gate_name",
        "validation_route_share",
        "test_route_share",
        "validation_MdAPE",
        "validation_MAPE",
        "validation_p95_APE",
    ]
    selected = decision["selected_candidate_label"]
    status_line = (
        f"{decision['decision_status']}: `{selected}` 선택. "
        f"validation {decision['selected_fixed_validation_MdAPE']:.6f}/"
        f"{decision['selected_fixed_validation_MAPE']:.6f}/"
        f"{decision['selected_fixed_validation_p95_APE']:.6f}, "
        f"fixed test {decision['selected_fixed_test_MdAPE']:.6f}/"
        f"{decision['selected_fixed_test_MAPE']:.6f}/"
        f"{decision['selected_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-WMIN8 Warm min1 weight router 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 선택 기준: validation-only gate 생성 + WMIN4 validation replacement score",
            "- fixed test: 최종 확인용으로만 기록",
            "- 0604: 사용하지 않음",
            f"- 결론: {status_line}",
            f"- 판단 근거: {decision['reason']}",
            "",
            "## 1. 후보별 교체 판단",
            markdown_table(aggregate, agg_cols, 120),
            "",
            "## 2. WMIN4 선택 후보 대비 변화량",
            markdown_table(comparison.sort_values(["eval_split", "delta_MAPE_vs_wmin4_selected"]), comp_cols, 120),
            "",
            "## 3. fixed validation/test 지표",
            markdown_table(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 160),
            "",
            "## 4. Gate Audit",
            markdown_table(gate_audit.sort_values(["validation_MAPE", "validation_p95_APE"]), audit_cols, 80),
            "",
            "## 5. 선택 후보 반복 validation 시나리오",
            markdown_table(
                repeated_summary[repeated_summary["candidate_label"].eq(selected)].round(6),
                [
                    "candidate_label",
                    "scenario",
                    "mean_MdAPE",
                    "mean_MAPE",
                    "mean_p95_APE",
                    "current_pp258_MAPE_win_rate",
                    "current_pp258_p95_win_rate",
                    "current_pp258_all3_win_rate",
                ],
                60,
            ),
            "",
            "## 6. 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-WMIN8 Warm min1 weight router 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1320px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 10px; font-size:30px; }} h2 {{ margin:36px 0 12px; padding-top:18px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:22px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-WMIN8 Warm min1 weight router 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(status_line)}<br>{html.escape(decision['reason'])}</div>
<h2>1. 후보별 교체 판단</h2>{table_html(aggregate, agg_cols, 120)}
<h2>2. WMIN4 선택 후보 대비 변화량</h2>{table_html(comparison.sort_values(["eval_split", "delta_MAPE_vs_wmin4_selected"]), comp_cols, 120)}
<h2>3. fixed validation/test 지표</h2>{table_html(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 160)}
<h2>4. Gate Audit</h2>{table_html(gate_audit.sort_values(["validation_MAPE", "validation_p95_APE"]), audit_cols, 80)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md + "\n", html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()
    source_predictions = load_predictions()
    routed_predictions, gate_audit = build_routed_candidates(source_predictions)
    baselines = source_predictions[source_predictions["candidate_label"].isin([PP258_REFERENCE, WMIN4_SELECTED])].copy()
    decision_predictions = pd.concat([baselines, routed_predictions], ignore_index=True, sort=False)
    decision_predictions = decision_predictions.drop_duplicates(["candidate_label", "eval_split", "_track6_row_id"], keep="first")

    fixed = wmin4.fixed_metrics(decision_predictions)
    repeated_detail, repeated_summary = wmin4.repeated_validation_metrics(decision_predictions)
    aggregate = wmin4.aggregate_decision(fixed, repeated_summary)
    decision = wmin4.choose_decision(aggregate)
    comparison = comparison_vs_wmin4(fixed)
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selection_policy": "validation-only route gate generation; fixed test confirmation; 0604 not used",
        "reference_candidate_label": PP258_REFERENCE,
        "base_candidate_label": WMIN4_SELECTED,
        "alt_candidates": ALT_CANDIDATES,
        "risk_quantiles": RISK_QUANTILES,
        "qwidth_thresholds": QWIDTH_THRESHOLDS,
        "spread_thresholds": SPREAD_THRESHOLDS,
        "gap_thresholds": GAP_THRESHOLDS,
        "alt_gap_thresholds": ALT_GAP_THRESHOLDS,
        "route_share_bounds": [MIN_ROUTE_SHARE, MAX_ROUTE_SHARE],
        "decision": decision,
    }
    decision_predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    fixed.to_csv(OUT_DIR / "fixed_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "operational_decision_aggregate.csv", index=False)
    comparison.to_csv(OUT_DIR / "comparison_vs_wmin4_selected.csv", index=False)
    gate_audit.to_csv(OUT_DIR / "gate_audit.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(aggregate, fixed, repeated_summary, comparison, gate_audit, decision, config)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_SUMMARY.write_text(md, encoding="utf-8")
    (EXP_DIR / "logs").mkdir(exist_ok=True)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "completed",
                "decision": decision,
                "candidate_count": int(routed_predictions["candidate_label"].nunique()),
                "seconds": round(time.time() - start, 2),
                "experiment_dir": str(EXP_DIR.relative_to(REPO)),
                "report": str((REPORT_DIR / "result_report.md").relative_to(REPO)),
                "summary_doc": str(DOC_SUMMARY.relative_to(REPO)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
