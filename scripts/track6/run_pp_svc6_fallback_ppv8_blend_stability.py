#!/usr/bin/env python3
"""Run PP-SVC6 fallback comparable + PP-V8 blend stability validation."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC6"
EXP_SLUG = "PP-SVC6_warm_fallback_ppv8_blend_stability"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm fallback 비교군 + PP-V8 결합 비율 안정성 검증"
SOURCE_PREDICTIONS = EXP_ROOT / "PP-SVC5_warm_multilevel_comparable_stats" / "outputs" / "predictions.csv"
SEED = 20260604
ITERATIONS = 200
SELECTION_FRACTION = 0.70
WEIGHTS = np.round(np.arange(0.40, 0.9001, 0.025), 3)

BASE_CANDIDATES = [
    "fallback_numeric",
    "pp_v8_compact_blend_mape_guarded",
    "blend_svcnum_ppv8_wsvc_0.70",
]
REFERENCE_CANDIDATES = [
    "blend_svcnum_ppv8_wsvc_0.70",
    "pp_v8_compact_blend_mape_guarded",
    "fallback_numeric",
]
OBJECTIVES = [
    "mape_guarded_ppv8",
    "mape_guarded_reference",
    "balanced_reference",
    "mdape_primary",
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_wide_predictions() -> pd.DataFrame:
    long = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    long = long[long["split"].isin(["validation", "test"])].copy()
    keep_candidates = set(BASE_CANDIDATES)
    long = long[long["candidate"].isin(keep_candidates)].copy()
    base_cols = [
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    base = long[base_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    wide = long.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    out = base.merge(wide, on=["split", "_track6_row_id"], how="inner")
    out["artist_key"] = out["artist_key"].fillna("__MISSING__").astype(str)
    out["artist_name_ko"] = out["artist_name_ko"].fillna("").astype(str)
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__").astype(str)
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__").astype(str)
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce")
    missing = [candidate for candidate in BASE_CANDIDATES if candidate not in out.columns]
    if missing:
        raise ValueError(f"Missing candidate predictions: {missing}")
    return out


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def label_for_weight(weight: float) -> str:
    return f"blend_fallback_numeric_ppv8_wfallback_{weight:.3f}"


def make_candidates(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, str, float]]:
    out: dict[str, tuple[np.ndarray, str, float]] = {}
    for candidate in BASE_CANDIDATES:
        out[candidate] = (frame[candidate].to_numpy(dtype=float), "reference", np.nan)
    fallback = frame["fallback_numeric"].to_numpy(dtype=float)
    ppv8 = frame["pp_v8_compact_blend_mape_guarded"].to_numpy(dtype=float)
    for weight in WEIGHTS:
        out[label_for_weight(float(weight))] = (
            float(weight) * fallback + (1.0 - float(weight)) * ppv8,
            "fallback_ppv8_weighted_blend",
            float(weight),
        )
    return out


def score_candidate(metrics: dict[str, float], references: dict[str, dict[str, float]], objective: str) -> float:
    ppv8 = references["pp_v8_compact_blend_mape_guarded"]
    reference = references["blend_svcnum_ppv8_wsvc_0.70"]
    if objective == "mdape_primary":
        return metrics["MdAPE"]
    if objective == "mape_guarded_ppv8":
        guard_penalty = max(0.0, metrics["MdAPE"] - ppv8["MdAPE"]) * 10.0
        return metrics["MAPE"] + guard_penalty
    if objective == "mape_guarded_reference":
        guard_penalty = max(0.0, metrics["MdAPE"] - reference["MdAPE"]) * 10.0
        return metrics["MAPE"] + guard_penalty
    if objective == "balanced_reference":
        return (
            0.40 * metrics["MdAPE"] / reference["MdAPE"]
            + 0.40 * metrics["MAPE"] / reference["MAPE"]
            + 0.20 * metrics["p95_APE"] / reference["p95_APE"]
        )
    raise ValueError(f"Unknown objective: {objective}")


def evaluate_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = make_candidates(frame)
    reference_metrics = {
        candidate: metric_values(frame, candidates[candidate][0])
        for candidate in REFERENCE_CANDIDATES
    }
    rows: list[dict[str, Any]] = []
    for candidate, (pred, method, weight) in candidates.items():
        metrics = metric_values(frame, pred)
        row = {
            "candidate": candidate,
            "method": method,
            "weight_fallback": weight,
            **metrics,
        }
        for objective in OBJECTIVES:
            row[f"score_{objective}"] = score_candidate(metrics, reference_metrics, objective)
        rows.append(row)
    return pd.DataFrame(rows)


def select_candidate(selection: pd.DataFrame, objective: str) -> pd.Series:
    metrics = evaluate_candidates(selection)
    blend_metrics = metrics[metrics["method"].eq("fallback_ppv8_weighted_blend")].copy()
    if objective == "mape_guarded_ppv8":
        ppv8_mdape = float(metrics.loc[metrics["candidate"].eq("pp_v8_compact_blend_mape_guarded"), "MdAPE"].iloc[0])
        guarded = blend_metrics[blend_metrics["MdAPE"] <= ppv8_mdape + 1e-12].copy()
        if not guarded.empty:
            return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "weight_fallback"]).iloc[0]
    if objective == "mape_guarded_reference":
        ref_mdape = float(metrics.loc[metrics["candidate"].eq("blend_svcnum_ppv8_wsvc_0.70"), "MdAPE"].iloc[0])
        guarded = blend_metrics[blend_metrics["MdAPE"] <= ref_mdape + 1e-12].copy()
        if not guarded.empty:
            return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "weight_fallback"]).iloc[0]
    score_col = f"score_{objective}"
    return blend_metrics.sort_values([score_col, "MdAPE", "MAPE", "p95_APE", "weight_fallback"]).iloc[0]


def split_validation(val: pd.DataFrame, mode: str, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    if mode == "row_holdout":
        indices = val.index.to_numpy()
        n_select = max(1, int(round(len(indices) * SELECTION_FRACTION)))
        selected = rng.choice(indices, size=n_select, replace=False)
        selection_mask = val.index.isin(selected)
    elif mode == "artist_holdout":
        artists = val["artist_key"].fillna("__MISSING__").astype(str).unique()
        n_select = max(1, int(round(len(artists) * SELECTION_FRACTION)))
        selected_artists = set(rng.choice(artists, size=n_select, replace=False).tolist())
        selection_mask = val["artist_key"].fillna("__MISSING__").astype(str).isin(selected_artists)
    else:
        raise ValueError(f"Unknown holdout mode: {mode}")
    selection = val.loc[selection_mask].copy()
    holdout = val.loc[~selection_mask].copy()
    if selection.empty or holdout.empty:
        raise ValueError(f"Invalid split for mode={mode}: selection={len(selection)}, holdout={len(holdout)}")
    return selection, holdout


def candidate_prediction(frame: pd.DataFrame, candidate: str) -> tuple[np.ndarray, str, float]:
    candidates = make_candidates(frame)
    if candidate not in candidates:
        raise KeyError(candidate)
    return candidates[candidate]


def evaluate_selected(
    frame: pd.DataFrame,
    candidate: str,
    split_label: str,
    mode: str,
    objective: str,
    iteration: int,
) -> dict[str, Any]:
    pred, method, weight = candidate_prediction(frame, candidate)
    metrics = metric_values(frame, pred)
    row: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "iteration": iteration,
        "holdout_mode": mode,
        "objective": objective,
        "eval_split": split_label,
        "selected_candidate": candidate,
        "selected_method": method,
        "selected_weight_fallback": weight,
        **metrics,
    }
    for reference in REFERENCE_CANDIDATES:
        ref_pred, _ref_method, _ref_weight = candidate_prediction(frame, reference)
        ref_metrics = metric_values(frame, ref_pred)
        ref_label = {
            "blend_svcnum_ppv8_wsvc_0.70": "pp_svc3",
            "pp_v8_compact_blend_mape_guarded": "pp_v8",
            "fallback_numeric": "fallback",
        }[reference]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            row[f"{ref_label}_{metric}"] = ref_metrics[metric]
            row[f"delta_vs_{ref_label}_{metric}"] = ref_metrics[metric] - metrics[metric]
    return row


def run_iterations(wide: pd.DataFrame) -> pd.DataFrame:
    val = wide[wide["split"].eq("validation")].copy()
    test = wide[wide["split"].eq("test")].copy()
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    for iteration in range(ITERATIONS):
        for mode in ["row_holdout", "artist_holdout"]:
            selection, holdout = split_validation(val, mode, rng)
            for objective in OBJECTIVES:
                selected = select_candidate(selection, objective)
                candidate = str(selected["candidate"])
                for split_label, frame in [("selection", selection), ("holdout", holdout), ("test", test)]:
                    row = evaluate_selected(frame, candidate, split_label, mode, objective, iteration)
                    row["selection_MdAPE"] = float(selected["MdAPE"])
                    row["selection_MAPE"] = float(selected["MAPE"])
                    row["selection_p95_APE"] = float(selected["p95_APE"])
                    row["selection_score"] = float(selected[f"score_{objective}"])
                    rows.append(row)
    return pd.DataFrame(rows)


def build_selection_frequency(iteration_results: pd.DataFrame) -> pd.DataFrame:
    selected = iteration_results[iteration_results["eval_split"].eq("selection")].copy()
    total = (
        selected.groupby(["holdout_mode", "objective"], dropna=False)["iteration"]
        .nunique()
        .rename("iterations")
        .reset_index()
    )
    freq = (
        selected.groupby(
            ["holdout_mode", "objective", "selected_candidate", "selected_method", "selected_weight_fallback"],
            dropna=False,
        )["iteration"]
        .nunique()
        .rename("selected_count")
        .reset_index()
        .merge(total, on=["holdout_mode", "objective"], how="left")
    )
    freq["selected_share"] = freq["selected_count"] / freq["iterations"]
    return freq.sort_values(["holdout_mode", "objective", "selected_count"], ascending=[True, True, False])


def build_summary_metrics(iteration_results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    metric_names = ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    delta_names = [
        "delta_vs_pp_svc3_MdAPE",
        "delta_vs_pp_svc3_MAPE",
        "delta_vs_pp_svc3_p95_APE",
        "delta_vs_pp_v8_MdAPE",
        "delta_vs_pp_v8_MAPE",
        "delta_vs_pp_v8_p95_APE",
        "delta_vs_fallback_MdAPE",
        "delta_vs_fallback_MAPE",
        "delta_vs_fallback_p95_APE",
    ]
    for keys, group in iteration_results.groupby(["holdout_mode", "objective", "eval_split"], dropna=False):
        row: dict[str, Any] = {
            "holdout_mode": keys[0],
            "objective": keys[1],
            "eval_split": keys[2],
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
            "selected_weight_mean": float(group["selected_weight_fallback"].mean()),
            "selected_weight_median": float(group["selected_weight_fallback"].median()),
            "selected_weight_std": float(group["selected_weight_fallback"].std(ddof=1)),
        }
        for metric in metric_names:
            values = group[metric].astype(float).to_numpy()
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            row[f"{metric}_median"] = float(np.median(values))
        for metric in delta_names:
            values = group[metric].astype(float).to_numpy()
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_median"] = float(np.median(values))
            row[f"{metric}_prob_improve"] = float(np.mean(values > 0))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["holdout_mode", "objective", "eval_split"])


def fixed_candidate_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    fixed = [
        "blend_svcnum_ppv8_wsvc_0.70",
        "pp_v8_compact_blend_mape_guarded",
        "fallback_numeric",
        label_for_weight(0.50),
        label_for_weight(0.55),
        label_for_weight(0.575),
        label_for_weight(0.60),
        label_for_weight(0.625),
        label_for_weight(0.65),
        label_for_weight(0.70),
        label_for_weight(0.75),
    ]
    rows: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        frame = wide[wide["split"].eq(split)].copy()
        for candidate in fixed:
            pred, method, weight = candidate_prediction(frame, candidate)
            row = {
                "candidate": candidate,
                "method": method,
                "weight_fallback": weight,
                "split": split,
                **metric_values(frame, pred),
            }
            ref_pred, _method, _weight = candidate_prediction(frame, "blend_svcnum_ppv8_wsvc_0.70")
            ref_metrics = metric_values(frame, ref_pred)
            for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[f"delta_vs_pp_svc3_{metric}"] = ref_metrics[metric] - row[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def prediction_frame(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    fixed = [
        "blend_svcnum_ppv8_wsvc_0.70",
        "pp_v8_compact_blend_mape_guarded",
        "fallback_numeric",
        label_for_weight(0.55),
        label_for_weight(0.575),
        label_for_weight(0.60),
        label_for_weight(0.625),
        label_for_weight(0.75),
    ]
    for split, frame in wide.groupby("split", dropna=False):
        for candidate in fixed:
            pred, method, weight = candidate_prediction(frame, candidate)
            out = frame[
                [
                    "split",
                    "_track6_row_id",
                    "actual_log",
                    "actual_price",
                    "artist_key",
                    "artist_name_ko",
                    "svc_group_level",
                    "svc_coverage_tier",
                    "svc_group_n",
                ]
            ].copy()
            out["experiment_id"] = EXP_ID
            out["candidate"] = candidate
            out["method"] = method
            out["weight_fallback"] = weight
            out["pred_log"] = pred
            out["pred_price"] = np.clip(np.exp(pred), 1_000.0, None)
            out["residual_log"] = out["actual_log"] - out["pred_log"]
            out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
            rows.append(out)
    return pd.concat(rows, ignore_index=True)


def render_report(
    selection_frequency: pd.DataFrame,
    summary_metrics: pd.DataFrame,
    fixed_metrics: pd.DataFrame,
) -> tuple[str, str]:
    top_freq = (
        selection_frequency.groupby(["holdout_mode", "objective"], group_keys=False)
        .head(8)
        .reset_index(drop=True)
    )
    holdout_summary = summary_metrics[summary_metrics["eval_split"].eq("holdout")].copy()
    test_summary = summary_metrics[summary_metrics["eval_split"].eq("test")].copy()
    fixed_test = fixed_metrics[fixed_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: `fallback_numeric + PP-V8` 결합 비율을 반복 holdout으로 재검증",
        "- 입력: PP-SVC5 validation/test 예측값",
        "- 선택 데이터: validation selection subset",
        "- 확인 데이터: validation holdout subset과 test",
        f"- 반복 횟수: row/artist holdout 각 `{ITERATIONS}`회",
        f"- weight 후보: `{WEIGHTS[0]:.3f}`부터 `{WEIGHTS[-1]:.3f}`까지 `0.025` 간격",
        "",
        "## 1. 고정 후보 test 성능",
        "",
        "| 후보 | weight | MdAPE | MAPE | p95_APE | PP-SVC3 대비 MdAPE 변화 | PP-SVC3 대비 MAPE 변화 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in fixed_test.itertuples():
        weight = "" if pd.isna(row.weight_fallback) else f"{row.weight_fallback:.3f}"
        lines.append(
            f"| `{row.candidate}` | {weight} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | "
            f"{row.delta_vs_pp_svc3_MdAPE:.4f} | {row.delta_vs_pp_svc3_MAPE:.4f} |"
        )
    lines += [
        "",
        "## 2. 반복 선택 빈도",
        "",
        "| holdout 방식 | 선택 기준 | 후보 | weight | 선택 횟수 | 선택 비율 |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in top_freq.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | `{row.selected_candidate}` | "
            f"{row.selected_weight_fallback:.3f} | {int(row.selected_count)} | {row.selected_share:.3f} |"
        )
    lines += [
        "",
        "## 3. 내부 holdout 요약",
        "",
        "| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-SVC3 MAPE 개선확률 | PP-SVC3 p95 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in holdout_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.selected_weight_median:.3f} | "
            f"{row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | {row.p95_APE_mean:.4f} | "
            f"{row.delta_vs_pp_svc3_MAPE_prob_improve:.3f} | {row.delta_vs_pp_svc3_p95_APE_prob_improve:.3f} |"
        )
    lines += [
        "",
        "## 4. 선택 후 test 요약",
        "",
        "| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-SVC3 MdAPE 개선확률 | PP-SVC3 MAPE 개선확률 | PP-SVC3 p95 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.selected_weight_median:.3f} | "
            f"{row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | {row.p95_APE_mean:.4f} | "
            f"{row.delta_vs_pp_svc3_MdAPE_prob_improve:.3f} | {row.delta_vs_pp_svc3_MAPE_prob_improve:.3f} | "
            f"{row.delta_vs_pp_svc3_p95_APE_prob_improve:.3f} |"
        )
    lines += [
        "",
        "## 5. 해석",
        "",
        "- test 고정 후보만 보면 `w=0.55~0.60` 구간이 기존 PP-SVC3보다 MdAPE/MAPE를 소폭 개선",
        "- 반복 holdout에서 같은 구간이 안정적으로 선택되면 Warm 서비스 후보 갱신 가능",
        "- 반복 holdout에서 `w=0.70~0.75`가 더 자주 선택되면 기존 PP-SVC3 계열 유지가 타당",
        "- row holdout과 artist holdout 선택 weight가 다르면 작가 단위 일반화 관점에서 보수적으로 판단",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}} th{{background:#eef2f7}} code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Fixed Metrics</h2>{fixed_metrics.to_html(index=False, escape=True)}
<h2>Selection Frequency</h2>{selection_frequency.to_html(index=False, escape=True)}
<h2>Summary Metrics</h2>{summary_metrics.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    iteration_results: pd.DataFrame,
    selection_frequency: pd.DataFrame,
    summary_metrics: pd.DataFrame,
    fixed_metrics: pd.DataFrame,
    predictions: pd.DataFrame,
) -> None:
    iteration_results.to_csv(EXP_DIR / "outputs" / "iteration_results.csv", index=False)
    selection_frequency.to_csv(EXP_DIR / "outputs" / "selection_frequency.csv", index=False)
    summary_metrics.to_csv(EXP_DIR / "outputs" / "summary_metrics.csv", index=False)
    fixed_metrics.to_csv(EXP_DIR / "outputs" / "fixed_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "base_candidates": BASE_CANDIDATES,
        "reference_candidates": REFERENCE_CANDIDATES,
        "objectives": OBJECTIVES,
        "weights": [float(weight) for weight in WEIGHTS],
        "iterations": ITERATIONS,
        "selection_fraction": SELECTION_FRACTION,
        "selection_rule": "selection_subset_only",
        "evaluation_rule": "holdout_and_test_after_selection",
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(selection_frequency, summary_metrics, fixed_metrics)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc6_fallback_ppv8_blend_stability_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    wide = load_wide_predictions()
    iteration_results = run_iterations(wide)
    selection_frequency = build_selection_frequency(iteration_results)
    summary_metrics = build_summary_metrics(iteration_results)
    fixed_metrics = fixed_candidate_metrics(wide)
    predictions = prediction_frame(wide)
    write_outputs(iteration_results, selection_frequency, summary_metrics, fixed_metrics, predictions)
    print(json.dumps({
        "status": "completed",
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc6_fallback_ppv8_blend_stability_summary.md").relative_to(REPO)),
        "top_selection": selection_frequency.head(12).to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
