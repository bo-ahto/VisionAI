#!/usr/bin/env python3
"""Run PP-OPT139..142 Warm direct meta-stack experiments."""
from __future__ import annotations

import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP135_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt135_138_warm_p95_aware_correction.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp135 = load_module("pp_opt135_helpers_for_pp139", PP135_SCRIPT)
pp127 = pp135.pp127
opt8 = pp135.opt8
val71 = pp135.val71

EXP_ID = "PP-OPT139-142"
EXP_SLUG = "PP-OPT139_142_warm_direct_meta_stack"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = pp135.BASE_CANDIDATE
INCUMBENT = pp135.INCUMBENT
SEED = 20260609

ITEMS = [
    {
        "item_id": "PP-OPT139",
        "priority": "1",
        "title": "direct LightGBM meta-stack basis",
        "description": "기존 Warm 후보, direct model, stack model 예측값을 입력으로 validation OOF에서 로그가격을 직접 예측한다.",
    },
    {
        "item_id": "PP-OPT140",
        "priority": "2",
        "title": "quantile meta basis with uncertainty cap",
        "description": "q25/q50/q75 meta 예측의 폭을 불확실성으로 보고 폭이 큰 row의 이동량을 줄인다.",
    },
    {
        "item_id": "PP-OPT141",
        "priority": "3",
        "title": "two-head direct meta with tail guard",
        "description": "direct meta 예측과 p95/tail-harm 확률을 함께 사용해 큰 이동은 위험 구간에서 축소한다.",
    },
    {
        "item_id": "PP-OPT142",
        "priority": "4",
        "title": "final direct meta-stack decision",
        "description": "PP126/PP134와 direct meta 후보를 같은 fixed/repeated 기준으로 비교하고 최종 판단한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp135.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp135.gate(value, threshold, width)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp135.make_candidate(base, candidate, family, item_id, pred_log)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp135.clip_by_row(values, caps)


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return pp135.row_cap(base, cap, mode)


def build_meta_predictions(base: pd.DataFrame, feature_matrix: pd.DataFrame) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    target = base["actual_log"].to_numpy(dtype=float)
    preds = {
        "lgb_l1": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="regression_l1", seed_offset=700),
        "lgb_l2": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="regression", seed_offset=740),
        "lgb_huber": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="huber", seed_offset=780),
        "lgb_q25": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="quantile", alpha=0.25, seed_offset=820),
        "lgb_q50": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="quantile", alpha=0.50, seed_offset=860),
        "lgb_q75": pp127.oof_lgbm_regression(base, feature_matrix, target, objective="quantile", alpha=0.75, seed_offset=900),
    }
    detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in preds.items():
        detail[key] = value
    detail["meta_quantile_width"] = np.abs(preds["lgb_q75"] - preds["lgb_q25"])
    return preds, detail


def pp_opt139_direct_meta_basis(base: pd.DataFrame, ref: pd.DataFrame, meta: dict[str, np.ndarray], scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    for target_key in ["lgb_l1", "lgb_l2", "lgb_huber", "lgb_q50"]:
        target = meta[target_key]
        delta = target - safe
        for strength in [0.10, 0.18, 0.28, 0.40, 0.55]:
            for cap in [0.010, 0.016, 0.026, 0.040]:
                cap_arr = np.maximum(0.004, cap * (1.0 - 0.55 * scores["p95_risk"]))
                pred = safe + clip_by_row(delta * strength, cap_arr)
                name = f"ppopt139_direct_meta__target={target_key}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "direct_lgbm_meta_stack_basis", "PP-OPT139", pred))
    return rows


def pp_opt140_quantile_basis(base: pd.DataFrame, ref: pd.DataFrame, meta: dict[str, np.ndarray], scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    q50 = meta["lgb_q50"]
    width = np.abs(meta["lgb_q75"] - meta["lgb_q25"])
    width_risk = gate(width, 0.045, 0.090)
    for width_penalty in [0.45, 0.65, 0.85]:
        keep = np.clip(1.0 - width_penalty * width_risk - 0.35 * scores["p95_risk"], 0, 1)
        for strength in [0.16, 0.24, 0.34, 0.46]:
            for cap in [0.010, 0.016, 0.024, 0.034]:
                cap_arr = np.maximum(0.0035, cap * (1.0 - 0.55 * width_risk) * (1.0 - 0.35 * scores["p95_risk"]))
                pred = safe + clip_by_row((q50 - safe) * keep * strength, cap_arr)
                name = f"ppopt140_quantile_meta__wpen={safe_name(width_penalty)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "quantile_meta_basis_uncertainty_cap", "PP-OPT140", pred))
    return rows


def pp_opt141_two_head_tail_guard(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    tail_harm = np.maximum(signals["prob_plain_tail_harm"], signals["prob_plain_p95_harm"])
    for target_key in ["lgb_l1", "lgb_huber", "lgb_q50"]:
        target = meta[target_key]
        risk = np.clip(0.45 * scores["p95_risk"] + 0.35 * tail_harm + 0.20 * gate(np.abs(target - safe), 0.030, 0.070), 0, 1)
        for risk_threshold in [0.45, 0.55, 0.65]:
            hard_keep = np.where(risk >= risk_threshold, 0.0, 1.0)
            soft_keep = np.clip(1.0 - 0.65 * risk, 0, 1)
            keep = np.minimum(hard_keep, soft_keep)
            for strength in [0.16, 0.26, 0.38, 0.50]:
                for cap in [0.010, 0.016, 0.024]:
                    cap_arr = np.maximum(0.0035, cap * (1.0 - 0.60 * risk))
                    pred = safe + clip_by_row((target - safe) * keep * strength, cap_arr)
                    name = (
                        f"ppopt141_two_head_meta__target={target_key}__rthr={safe_name(risk_threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "two_head_direct_meta_tail_guard", "PP-OPT141", pred))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        ).iloc[0]
        p95_pool = group[group["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"])
        if p95_pool.empty:
            p95_pool = group.sort_values(["test_p95_APE", "test_MAPE"])
        p95 = p95_pool.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
                "p95_candidate": p95["candidate"],
                "p95_test_MAPE": p95["test_MAPE"],
                "p95_test_p95_APE": p95["test_p95_APE"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "direct_meta_stack_operational_selection"), ("p95", "direct_meta_stack_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt142_{key}_direct_meta_stack_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT142"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability_aggregate: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        "reference_pp64_current_best",
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp134_operational_recomputed",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"운영 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP126 대비 MAPE {decision['operational_delta_vs_pp126_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp126_p95_APE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT139~142 Warm direct meta-stack 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: 사후 보정이 아니라 direct meta-stack/quantile meta 기준가로 큰 개선 가능성 확인",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 30),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 60),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 80),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT139~142 Warm direct meta-stack 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT139~142 Warm direct meta-stack 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 30)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 30)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 60)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 80)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, labels, model_detail, selected_refs, parent_config, selected_pp119 = pp135.load_inputs()
    scores = pp135.build_scores(base, ref, labels, model_detail)
    feature_matrix = pp127.build_feature_matrix(base, ref, labels, model_detail, scores)
    prior_signals, prior_signal_detail = pp127.build_learned_signals(base, ref, model_detail, feature_matrix)
    signals, signal_detail = pp135.build_p95_aware_signals(base, ref, model_detail, feature_matrix, prior_signals)
    ref, ref_notes = pp135.add_reference_predictions(base, ref, model_detail, scores, signals)
    meta, meta_detail = build_meta_predictions(base, feature_matrix)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt139_direct_meta_basis(base, ref, meta, scores))
    candidates.extend(pp_opt140_quantile_basis(base, ref, meta, scores))
    candidates.extend(pp_opt141_two_head_tail_guard(base, ref, meta, scores, signals))
    predictions = pd.concat([source] + pp135.reference_candidates(base, ref) + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = pp135.select_candidates_for_stability(metrics, aggregate)
    stability_predictions, label_map = pp135.label_for_stability(predictions, selected)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = pp135.select_protocol_candidates(stability_aggregate)
    predictions, decision = add_protocol_rows(predictions, decision)

    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = pp135.select_candidates_for_stability(metrics, aggregate)
    selected.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = pp135.label_for_stability(predictions, selected)
    label_map[decision["operational_protocol_candidate"]] = "pp142_operational_direct_meta_stack_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp142_p95_direct_meta_stack_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "selected_references": selected_refs,
        "selected_pp119_sources": selected_pp119,
        "recomputed_reference_notes": ref_notes,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {"pp135_helper": str(PP135_SCRIPT.relative_to(REPO))},
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    fixed.to_csv(OUT_DIR / "selected_fixed_candidate_metrics.csv", index=False)
    stability_detail.to_csv(OUT_DIR / "selected_stability_repeated_detail.csv", index=False)
    stability_summary.to_csv(OUT_DIR / "selected_stability_repeated_summary.csv", index=False)
    stability_aggregate.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    prior_signal_detail.to_csv(ARTIFACT_DIR / "prior_learned_signal_detail.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "p95_aware_signal_detail.csv", index=False)
    meta_detail.to_csv(ARTIFACT_DIR / "direct_meta_prediction_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "direct_meta_stack_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "direct_meta_stack_result.html").write_text(report_html, encoding="utf-8")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(item_summary[["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family"]].to_string(index=False))
    print("\nSelected stability:")
    print(stability_aggregate[["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
