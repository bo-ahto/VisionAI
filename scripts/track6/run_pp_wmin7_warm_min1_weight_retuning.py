#!/usr/bin/env python3
"""Run PP-WMIN7: retune the min1 SVC / PPV8 blend weight.

The current WMIN4 path uses:

    min1_70_30_basis = 0.70 * min1_svc + 0.30 * PPV8

PP-WMIN7 keeps the selected min1 SVC and PPV8 components fixed, changes only the
blend weight, then applies the same WMIN3 partial Huber residual refit and the
same WMIN4 operational decision layer.

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

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_wmin3_warm_min1_hcoef_refit as wmin3  # noqa: E402
import run_pp_wmin4_warm_min1_operational_decision as wmin4  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN7"
EXP_SLUG = "PP-WMIN7_warm_min1_weight_retuning"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin7_warm_min1_weight_retuning_summary.md"

SVC_WEIGHTS = [0.50, 0.55, 0.60, 0.625, 0.65, 0.675, 0.70, 0.725, 0.75, 0.775, 0.80, 0.85, 0.90]
WMIN4_SELECTED = "min1_huber_refit_partial"
PP258_REFERENCE = "current_pp258_operational_reference"


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.exp(np.asarray(values, dtype=float)), 1_000.0, None)


def label_for_weight(weight: float, suffix: str) -> str:
    return f"min1_w{int(round(weight * 1000)):03d}_{suffix}"


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


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred_log: np.ndarray, method: str, weight: float) -> pd.DataFrame:
    pred_price = safe_exp(pred_log)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "candidate": candidate,
            "family": "wmin7_min1_weight_retuning",
            "item_id": EXP_ID,
            "eval_split": "validation_oof" if split == "validation" else "test",
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame.get("artist_name_ko", pd.Series("", index=frame.index)).astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "candidate_label": candidate,
            "source_experiment": EXP_ID,
            "method": method,
            "scope": "fixed_confirmation",
            "split": split,
            "svc_weight": weight,
            "ppv8_weight": 1.0 - weight,
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_n": pd.to_numeric(frame["svc_group_n"], errors="coerce").to_numpy(dtype=float),
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def frames_for_weight(base_frames: dict[str, pd.DataFrame], weight: float) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for split, frame in base_frames.items():
        changed = frame.copy()
        changed["current_70_30"] = (
            float(weight) * changed[wmin3.NEW_SVC].to_numpy(dtype=float)
            + (1.0 - float(weight)) * changed["ppv8_defensive"].to_numpy(dtype=float)
        )
        changed[wmin3.NEW_BASIS] = changed["current_70_30"]
        changed["svc_fallback"] = changed[wmin3.NEW_SVC]
        out[split] = hcoef1.add_derived_features(changed, split).reset_index(drop=True)
    return out


def build_weight_candidates() -> tuple[pd.DataFrame, pd.DataFrame]:
    base_frames = wmin3.make_variant_frames("partial")
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    for weight in SVC_WEIGHTS:
        frames = frames_for_weight(base_frames, weight)
        validation = frames["validation"].reset_index(drop=True)
        model = None
        basis_label = label_for_weight(weight, "70_30_basis")
        refit_label = label_for_weight(weight, "huber_refit_partial")
        for split in ["validation", "test"]:
            frame = frames[split].reset_index(drop=True)
            basis_pred = frame["current_70_30"].to_numpy(dtype=float)
            pred_rows.append(prediction_frame(frame, basis_label, split, basis_pred, "weight_retuned_basis", weight))
            if model is None:
                refit_pred, model = wmin3.fit_refit_candidate(validation, frame)
            else:
                refit_pred, _ = wmin3.fit_refit_candidate(validation, frame)
            pred_rows.append(prediction_frame(frame, refit_label, split, refit_pred, "partial_huber_refit_on_weight_retuned_basis", weight))
            if split == "test":
                coef = wmin3.hcoef3.coefficient_frame(model, wmin3.STABLE_CONFIG)
                coef["experiment_id"] = EXP_ID
                coef["candidate_label"] = refit_label
                coef["svc_weight"] = weight
                coef["ppv8_weight"] = 1.0 - weight
                coef_rows.append(coef)
    return pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def load_decision_baselines() -> pd.DataFrame:
    existing = pd.read_csv(wmin4.OUT_DIR / "candidate_predictions.csv", low_memory=False)
    keep = existing[existing["candidate_label"].isin([PP258_REFERENCE, WMIN4_SELECTED])].copy()
    if keep["candidate_label"].nunique() != 2:
        raise RuntimeError("Missing PP258 or WMIN4 selected baseline predictions")
    return keep


def attach_reference_meta(predictions: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    meta_cols = [
        "eval_split",
        "_track6_row_id",
        "confidence_tier",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    meta = reference[reference["candidate_label"].eq(PP258_REFERENCE)][meta_cols].drop_duplicates(["eval_split", "_track6_row_id"])
    out = predictions.drop(columns=[col for col in meta_cols[2:] if col in predictions.columns], errors="ignore")
    return out.merge(meta, on=["eval_split", "_track6_row_id"], how="left")


def comparison_vs_wmin4(fixed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    new_rows = fixed[fixed["candidate_label"].str.startswith("min1_w", na=False)].copy()
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
            "# PP-WMIN7 Warm min1 weight retuning 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 선택 기준: WMIN4와 동일하게 validation 반복 안정성 + validation replacement score",
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
            "## 4. 선택 후보 반복 validation 시나리오",
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
            "## 5. 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-WMIN7 Warm min1 weight retuning 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1320px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 10px; font-size:30px; }} h2 {{ margin:36px 0 12px; padding-top:18px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:22px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-WMIN7 Warm min1 weight retuning 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(status_line)}<br>{html.escape(decision['reason'])}</div>
<h2>1. 후보별 교체 판단</h2>{table_html(aggregate, agg_cols, 120)}
<h2>2. WMIN4 선택 후보 대비 변화량</h2>{table_html(comparison.sort_values(["eval_split", "delta_MAPE_vs_wmin4_selected"]), comp_cols, 120)}
<h2>3. fixed validation/test 지표</h2>{table_html(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 160)}
<h2>4. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md + "\n", html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()
    raw_predictions, coefficients = build_weight_candidates()
    baselines = load_decision_baselines()
    new_predictions = attach_reference_meta(raw_predictions, baselines)
    decision_predictions = pd.concat([baselines, new_predictions], ignore_index=True, sort=False)
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
        "selection_policy": "validation repeated stability and validation replacement score only; fixed test is confirmation; 0604 is not used",
        "reference_candidate_label": PP258_REFERENCE,
        "wmin4_selected_candidate_label": WMIN4_SELECTED,
        "svc_weights": SVC_WEIGHTS,
        "basis_formula": "weight * min1_svc_numeric_seed_mean + (1-weight) * pp_v8_compact_blend_mape_guarded",
        "huber_refit": {
            "mode": "WMIN3 partial",
            "current_70_30": "weight-retuned basis",
            "svc_fallback": "WMIN2 min1 SVC seed mean",
            "stable_config": wmin3.STABLE_CONFIG,
        },
        "decision": decision,
    }
    raw_predictions.to_csv(OUT_DIR / "wmin7_raw_candidate_predictions.csv", index=False)
    decision_predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    fixed.to_csv(OUT_DIR / "fixed_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "operational_decision_aggregate.csv", index=False)
    comparison.to_csv(OUT_DIR / "comparison_vs_wmin4_selected.csv", index=False)
    coefficients.to_csv(OUT_DIR / "huber_refit_coefficients.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(aggregate, fixed, repeated_summary, comparison, decision, config)
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
