#!/usr/bin/env python3
"""Run PP-WOPT2 conditional blend stability validation.

PP-WOPT1 found conditional fallback_numeric + PP-V8 candidates that looked
strong on the fixed test split. This script checks whether such conditional
rules can be selected from validation subsets and still hold on validation
holdout/test.
"""
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
EXP_ID = "PP-WOPT2"
EXP_SLUG = "PP-WOPT2_warm_conditional_blend_stability"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm conditional fallback + PP-V8 blend stability"
SEED = 20260606
ITERATIONS = 200
SELECTION_FRACTION = 0.70

SVC5_PREDICTIONS = EXP_ROOT / "PP-SVC5_warm_multilevel_comparable_stats" / "outputs" / "predictions.csv"
CURRENT_CANDIDATE = "blend_svcnum_ppv8_wsvc_0.70"
PPV8_CANDIDATE = "pp_v8_compact_blend_mape_guarded"
FALLBACK_CANDIDATE = "fallback_numeric"

FIXED_WEIGHTS = np.round(np.arange(0.50, 0.7501, 0.025), 3)


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_wide_predictions() -> pd.DataFrame:
    pred = pd.read_csv(SVC5_PREDICTIONS, low_memory=False)
    pred = pred[
        pred["split"].isin(["validation", "test"])
        & pred["candidate"].isin([CURRENT_CANDIDATE, PPV8_CANDIDATE, FALLBACK_CANDIDATE])
    ].copy()
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
    base = pred[base_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    wide = pred.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    out = base.merge(wide, on=["split", "_track6_row_id"], how="inner")
    out["artist_key"] = out["artist_key"].fillna("__MISSING__").astype(str)
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__").astype(str)
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__").astype(str)
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0.0)
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


def fixed_label(weight: float) -> str:
    return f"fixed_fallback_ppv8_wfallback_{weight:.3f}"


def dynamic_label(min_n: int, max_gap: float, hard_gap: float, high: float, mid: float, low: float) -> str:
    return f"dyn_fallback_ppv8_n{min_n}_gap{max_gap:.2f}_hard{hard_gap:.2f}_w{high:.2f}_{mid:.3f}_{low:.2f}"


def dynamic_weights(frame: pd.DataFrame, min_n: int, max_gap: float, hard_gap: float, high: float, mid: float, low: float) -> np.ndarray:
    n = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    gap = np.abs(frame[FALLBACK_CANDIDATE].to_numpy(dtype=float) - frame[PPV8_CANDIDATE].to_numpy(dtype=float))
    strong = (n >= min_n) & (gap <= max_gap)
    weak = (n < min_n) | (gap > hard_gap)
    weights = np.full(len(frame), mid, dtype=float)
    weights[strong] = high
    weights[weak] = low
    return weights


def build_candidates(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, str, float]]:
    candidates: dict[str, tuple[np.ndarray, str, float]] = {
        CURRENT_CANDIDATE: (frame[CURRENT_CANDIDATE].to_numpy(dtype=float), "reference", np.nan),
        PPV8_CANDIDATE: (frame[PPV8_CANDIDATE].to_numpy(dtype=float), "reference", np.nan),
        FALLBACK_CANDIDATE: (frame[FALLBACK_CANDIDATE].to_numpy(dtype=float), "reference", np.nan),
    }
    fallback = frame[FALLBACK_CANDIDATE].to_numpy(dtype=float)
    ppv8 = frame[PPV8_CANDIDATE].to_numpy(dtype=float)
    for weight in FIXED_WEIGHTS:
        candidates[fixed_label(float(weight))] = (
            float(weight) * fallback + (1.0 - float(weight)) * ppv8,
            "fixed_weight_blend",
            float(weight),
        )
    for min_n in [5, 15, 30, 50]:
        for max_gap in [0.35, 0.50, 0.70]:
            for hard_gap in [0.50, 0.75, 1.00]:
                for high, mid, low in [(0.75, 0.60, 0.45), (0.70, 0.575, 0.45), (0.65, 0.55, 0.40)]:
                    weights = dynamic_weights(frame, min_n, max_gap, hard_gap, high, mid, low)
                    label = dynamic_label(min_n, max_gap, hard_gap, high, mid, low)
                    candidates[label] = (
                        weights * fallback + (1.0 - weights) * ppv8,
                        "conditional_weight_blend",
                        float(np.mean(weights)),
                    )
    return candidates


def evaluate_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = build_candidates(frame)
    current_metrics = metric_values(frame, candidates[CURRENT_CANDIDATE][0])
    rows: list[dict[str, Any]] = []
    for candidate, (pred, method, weight) in candidates.items():
        metrics = metric_values(frame, pred)
        row = {
            "candidate": candidate,
            "method": method,
            "weight_or_mean_weight": weight,
            **metrics,
        }
        row["balanced_score"] = (
            0.40 * row["MdAPE"] / current_metrics["MdAPE"]
            + 0.40 * row["MAPE"] / current_metrics["MAPE"]
            + 0.20 * row["p95_APE"] / current_metrics["p95_APE"]
        )
        rows.append(row)
    return pd.DataFrame(rows)


def split_validation(val: pd.DataFrame, mode: str, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    if mode == "row_holdout":
        indices = val.index.to_numpy()
        n_select = max(1, int(round(len(indices) * SELECTION_FRACTION)))
        selected = rng.choice(indices, size=n_select, replace=False)
        mask = val.index.isin(selected)
    elif mode == "artist_holdout":
        artists = val["artist_key"].astype(str).unique()
        n_select = max(1, int(round(len(artists) * SELECTION_FRACTION)))
        selected = set(rng.choice(artists, size=n_select, replace=False).tolist())
        mask = val["artist_key"].astype(str).isin(selected)
    else:
        raise ValueError(mode)
    selection = val.loc[mask].copy()
    holdout = val.loc[~mask].copy()
    if selection.empty or holdout.empty:
        raise ValueError(f"Invalid split: {mode}")
    return selection, holdout


def select_candidate(selection: pd.DataFrame, objective: str) -> pd.Series:
    metrics = evaluate_candidates(selection)
    pool = metrics[metrics["method"].isin(["conditional_weight_blend", "fixed_weight_blend"])].copy()
    current = metrics[metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    if objective == "mape_current_mdape_guard":
        guarded = pool[pool["MdAPE"] <= float(current["MdAPE"]) + 1e-12].copy()
        if not guarded.empty:
            return guarded.sort_values(["MAPE", "MdAPE", "p95_APE"]).iloc[0]
        return pool.sort_values(["balanced_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
    if objective == "p95_current_mdape_guard":
        guarded = pool[pool["MdAPE"] <= float(current["MdAPE"]) + 1e-12].copy()
        if not guarded.empty:
            return guarded.sort_values(["p95_APE", "MdAPE", "MAPE"]).iloc[0]
        return pool.sort_values(["balanced_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
    if objective == "all_metric_guarded":
        guarded = pool[
            (pool["MdAPE"] <= float(current["MdAPE"]) + 1e-12)
            & (pool["MAPE"] <= float(current["MAPE"]) + 1e-12)
            & (pool["p95_APE"] <= float(current["p95_APE"]) + 1e-12)
        ].copy()
        if not guarded.empty:
            return guarded.sort_values(["balanced_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
        return pool.sort_values(["balanced_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
    if objective == "balanced_current":
        return pool.sort_values(["balanced_score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
    raise ValueError(objective)


def candidate_prediction(frame: pd.DataFrame, candidate: str) -> tuple[np.ndarray, str, float]:
    candidates = build_candidates(frame)
    if candidate not in candidates:
        raise KeyError(candidate)
    return candidates[candidate]


def evaluate_selected(frame: pd.DataFrame, candidate: str, split_label: str, mode: str, objective: str, iteration: int) -> dict[str, Any]:
    pred, method, weight = candidate_prediction(frame, candidate)
    metrics = metric_values(frame, pred)
    current_pred, _method, _weight = candidate_prediction(frame, CURRENT_CANDIDATE)
    current_metrics = metric_values(frame, current_pred)
    row: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "iteration": iteration,
        "holdout_mode": mode,
        "objective": objective,
        "eval_split": split_label,
        "selected_candidate": candidate,
        "selected_method": method,
        "selected_weight_or_mean_weight": weight,
        **metrics,
    }
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        row[f"current_{metric}"] = current_metrics[metric]
        row[f"delta_vs_current_{metric}"] = current_metrics[metric] - metrics[metric]
    return row


def fixed_candidate_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split_name, frame in wide.groupby("split", dropna=False):
        metrics = evaluate_candidates(frame)
        metrics["split"] = split_name
        current = metrics[metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            metrics[f"delta_vs_current_{metric}"] = float(current[metric]) - metrics[metric]
        rows.append(metrics)
    return pd.concat(rows, ignore_index=True)


def run_iterations(wide: pd.DataFrame) -> pd.DataFrame:
    val = wide[wide["split"].eq("validation")].copy()
    test = wide[wide["split"].eq("test")].copy()
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    objectives = ["mape_current_mdape_guard", "p95_current_mdape_guard", "all_metric_guarded", "balanced_current"]
    for iteration in range(ITERATIONS):
        for mode in ["row_holdout", "artist_holdout"]:
            selection, holdout = split_validation(val, mode, rng)
            for objective in objectives:
                selected = select_candidate(selection, objective)
                candidate = str(selected["candidate"])
                for split_label, frame in [("selection", selection), ("holdout", holdout), ("test", test)]:
                    row = evaluate_selected(frame, candidate, split_label, mode, objective, iteration)
                    row["selection_MdAPE"] = float(selected["MdAPE"])
                    row["selection_MAPE"] = float(selected["MAPE"])
                    row["selection_p95_APE"] = float(selected["p95_APE"])
                    rows.append(row)
    return pd.DataFrame(rows)


def build_summary(iteration_results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in iteration_results.groupby(["holdout_mode", "objective", "eval_split"], dropna=False):
        row: dict[str, Any] = {
            "holdout_mode": keys[0],
            "objective": keys[1],
            "eval_split": keys[2],
            "iterations": int(group["iteration"].nunique()),
            "selected_weight_median": float(group["selected_weight_or_mean_weight"].median()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            row[f"{metric}_mean"] = float(group[metric].mean())
            row[f"{metric}_median"] = float(group[metric].median())
            delta = group[f"delta_vs_current_{metric}"].astype(float)
            row[f"{metric}_improve_mean"] = float(delta.mean())
            row[f"{metric}_improve_prob"] = float((delta > 0).mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["holdout_mode", "objective", "eval_split"])


def build_selection_frequency(iteration_results: pd.DataFrame) -> pd.DataFrame:
    selected = iteration_results[iteration_results["eval_split"].eq("selection")].copy()
    total = selected.groupby(["holdout_mode", "objective"])["iteration"].nunique().rename("iterations").reset_index()
    freq = (
        selected.groupby(["holdout_mode", "objective", "selected_candidate", "selected_method"], dropna=False)["iteration"]
        .nunique()
        .rename("selected_count")
        .reset_index()
        .merge(total, on=["holdout_mode", "objective"], how="left")
    )
    freq["selected_share"] = freq["selected_count"] / freq["iterations"]
    return freq.sort_values(["holdout_mode", "objective", "selected_count"], ascending=[True, True, False])


def render_report(fixed_metrics: pd.DataFrame, summary: pd.DataFrame, frequency: pd.DataFrame) -> tuple[str, str]:
    fixed_test = fixed_metrics[fixed_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test_summary = summary[summary["eval_split"].eq("test")].copy()
    holdout_summary = summary[summary["eval_split"].eq("holdout")].copy()
    top_frequency = frequency.groupby(["holdout_mode", "objective"], group_keys=False).head(5)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: PP-WOPT1의 조건별 결합 후보가 validation 선택에도 안정적인지 확인",
        f"- 반복 횟수: row/artist holdout 각 `{ITERATIONS}`회",
        "- 선택 데이터: validation 일부",
        "- 검증 데이터: 남은 validation holdout과 고정 test",
        "",
        "## 1. 고정 test 상위 후보",
        "",
        "| 후보 | 방식 | MdAPE | MAPE | p95_APE | 기준 대비 MdAPE | 기준 대비 MAPE | 기준 대비 p95 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in fixed_test.head(25).itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.method} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | "
            f"{row.delta_vs_current_MdAPE:.4f} | {row.delta_vs_current_MAPE:.4f} | {row.delta_vs_current_p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 2. 선택 후 test 요약",
        "",
        "| holdout 방식 | 선택 기준 | weight 중앙값 | MdAPE 평균 | MAPE 평균 | p95 평균 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.selected_weight_median:.3f} | "
            f"{row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | {row.p95_APE_mean:.4f} | "
            f"{row.MdAPE_improve_prob:.3f} | {row.MAPE_improve_prob:.3f} | {row.p95_APE_improve_prob:.3f} |"
        )
    lines += [
        "",
        "## 3. 내부 holdout 요약",
        "",
        "| holdout 방식 | 선택 기준 | MdAPE 평균 | MAPE 평균 | p95 평균 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in holdout_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | {row.p95_APE_mean:.4f} | "
            f"{row.MdAPE_improve_prob:.3f} | {row.MAPE_improve_prob:.3f} | {row.p95_APE_improve_prob:.3f} |"
        )
    lines += [
        "",
        "## 4. 선택 빈도 상위",
        "",
        "| holdout 방식 | 선택 기준 | 후보 | 방식 | 선택 횟수 | 선택 비율 |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in top_frequency.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | `{row.selected_candidate}` | {row.selected_method} | "
            f"{int(row.selected_count)} | {row.selected_share:.3f} |"
        )
    lines += [
        "",
        "## 5. 해석",
        "",
        "- 고정 test에서 좋아 보이는 후보가 반복 선택 후 test 평균에서도 유지되는지 확인",
        "- holdout/test 개선확률이 낮으면 test 단일 split 우연 가능성이 큼",
        "- 조건별 결합 후보가 안정적이면 PP-SVC3 이후 후보로 승격",
        "- 안정적이지 않으면 현재 Warm 1순위 유지",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<h2>Fixed Metrics</h2>{fixed_test.head(80).to_html(index=False, escape=True)}
<h2>Summary</h2>{summary.to_html(index=False, escape=True)}
<h2>Selection Frequency</h2>{top_frequency.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(fixed_metrics: pd.DataFrame, iteration_results: pd.DataFrame, summary: pd.DataFrame, frequency: pd.DataFrame) -> None:
    fixed_metrics.to_csv(EXP_DIR / "outputs" / "fixed_candidate_metrics.csv", index=False)
    iteration_results.to_csv(EXP_DIR / "outputs" / "iteration_results.csv", index=False)
    summary.to_csv(EXP_DIR / "outputs" / "summary_metrics.csv", index=False)
    frequency.to_csv(EXP_DIR / "outputs" / "selection_frequency.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "seed": SEED,
        "iterations": ITERATIONS,
        "selection_fraction": SELECTION_FRACTION,
        "current_candidate": CURRENT_CANDIDATE,
        "candidate_source": str(SVC5_PREDICTIONS.relative_to(REPO)),
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(fixed_metrics, summary, frequency)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    wide = load_wide_predictions()
    fixed_metrics = fixed_candidate_metrics(wide)
    iteration_results = run_iterations(wide)
    summary = build_summary(iteration_results)
    frequency = build_selection_frequency(iteration_results)
    write_outputs(fixed_metrics, iteration_results, summary, frequency)
    test_top = fixed_metrics[fixed_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(8)
    test_summary = summary[summary["eval_split"].eq("test")]
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "top_fixed_test_candidates": test_top[[
            "candidate",
            "method",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_vs_current_MdAPE",
            "delta_vs_current_MAPE",
            "delta_vs_current_p95_APE",
        ]].to_dict("records"),
        "test_summary": test_summary[[
            "holdout_mode",
            "objective",
            "selected_weight_median",
            "MdAPE_mean",
            "MAPE_mean",
            "p95_APE_mean",
            "MdAPE_improve_prob",
            "MAPE_improve_prob",
            "p95_APE_improve_prob",
        ]].to_dict("records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
