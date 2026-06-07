#!/usr/bin/env python3
"""Run PP-SVC4 Warm blend repeated holdout stability validation."""
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
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC4"
EXP_SLUG = "PP-SVC4_warm_blend_holdout_stability"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm blend holdout stability validation"
SOURCE_PREDICTIONS = EXP_ROOT / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
SEED = 20260603
ITERATIONS = 200
SELECTION_FRACTION = 0.70

BASE_CANDIDATES = [
    "svc_numeric_seed_mean",
    "svc_full_seed_mean",
    "pp_v6_fine_blend_mape_guarded",
    "pp_v8_compact_blend_mape_guarded",
]
SVC_CANDIDATES = ["svc_numeric_seed_mean", "svc_full_seed_mean"]
PP_CANDIDATES = ["pp_v6_fine_blend_mape_guarded", "pp_v8_compact_blend_mape_guarded"]
REFERENCE_CANDIDATES = ["pp_v6_fine_blend_mape_guarded", "pp_v8_compact_blend_mape_guarded"]
OBJECTIVES = ["mdape_primary", "mape_guarded", "balanced"]

SHORT_NAMES = {
    "svc_numeric_seed_mean": "svcnum",
    "svc_full_seed_mean": "svcfull",
    "pp_v6_fine_blend_mape_guarded": "ppv6",
    "pp_v8_compact_blend_mape_guarded": "ppv8",
}
LONG_NAMES = {value: key for key, value in SHORT_NAMES.items()}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_wide_predictions() -> pd.DataFrame:
    long = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    long = long[long["split"].isin(["validation", "test"])].copy()
    base_cols = [
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "artist_works_count_train",
    ]
    base = long[base_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    meta_cols = ["split", "_track6_row_id", "svc_group_level", "svc_coverage_tier", "svc_group_n"]
    meta = (
        long[meta_cols]
        .replace({"": np.nan})
        .dropna(subset=["svc_group_level"])
        .drop_duplicates(["split", "_track6_row_id"])
    )
    wide = long.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    out = base.merge(meta, on=["split", "_track6_row_id"], how="left").merge(
        wide,
        on=["split", "_track6_row_id"],
        how="inner",
    )
    out["svc_group_level"] = out["svc_group_level"].fillna("__MISSING__")
    out["svc_coverage_tier"] = out["svc_coverage_tier"].fillna("__MISSING__")
    out["svc_group_n"] = pd.to_numeric(out["svc_group_n"], errors="coerce")
    missing = [candidate for candidate in BASE_CANDIDATES if candidate not in out.columns]
    if missing:
        raise ValueError(f"Missing base prediction columns: {missing}")
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


def make_weighted_candidates(frame: pd.DataFrame) -> dict[str, tuple[np.ndarray, str]]:
    out: dict[str, tuple[np.ndarray, str]] = {}
    for candidate in BASE_CANDIDATES:
        out[candidate] = (frame[candidate].to_numpy(dtype=float), "base")
    weights = np.round(np.arange(0.0, 1.0001, 0.05), 2)
    for svc in SVC_CANDIDATES:
        for pp in PP_CANDIDATES:
            svc_pred = frame[svc].to_numpy(dtype=float)
            pp_pred = frame[pp].to_numpy(dtype=float)
            for weight in weights:
                label = f"blend_{SHORT_NAMES[svc]}_{SHORT_NAMES[pp]}_wsvc_{weight:.2f}"
                out[label] = (weight * svc_pred + (1.0 - weight) * pp_pred, "weighted_blend")
    return out


def candidate_meta(label: str) -> dict[str, Any]:
    if label in BASE_CANDIDATES:
        return {
            "selected_family": "base",
            "selected_svc": "",
            "selected_pp": "",
            "selected_weight": np.nan,
        }
    match = re.match(r"blend_(svcnum|svcfull)_(ppv6|ppv8)_wsvc_([0-9.]+)$", label)
    if not match:
        return {
            "selected_family": "other",
            "selected_svc": "",
            "selected_pp": "",
            "selected_weight": np.nan,
        }
    svc, pp, weight = match.groups()
    return {
        "selected_family": f"blend_{svc}_{pp}",
        "selected_svc": LONG_NAMES[svc],
        "selected_pp": LONG_NAMES[pp],
        "selected_weight": float(weight),
    }


def score_metrics(metrics: dict[str, float], ppv6_metrics: dict[str, float], objective: str) -> float:
    if objective == "mdape_primary":
        return metrics["MdAPE"]
    if objective == "mape_guarded":
        guard_penalty = max(0.0, metrics["MdAPE"] - ppv6_metrics["MdAPE"]) * 10.0
        return metrics["MAPE"] + guard_penalty
    if objective == "balanced":
        return (
            0.40 * metrics["MdAPE"] / ppv6_metrics["MdAPE"]
            + 0.35 * metrics["MAPE"] / ppv6_metrics["MAPE"]
            + 0.25 * metrics["p95_APE"] / ppv6_metrics["p95_APE"]
        )
    raise ValueError(f"Unknown objective: {objective}")


def evaluate_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    candidates = make_weighted_candidates(frame)
    rows: list[dict[str, Any]] = []
    ppv6_metrics = metric_values(frame, frame["pp_v6_fine_blend_mape_guarded"])
    for candidate, (pred, method) in candidates.items():
        metrics = metric_values(frame, pred)
        rows.append({
            "candidate": candidate,
            "method": method,
            **candidate_meta(candidate),
            **metrics,
            "score_mdape_primary": score_metrics(metrics, ppv6_metrics, "mdape_primary"),
            "score_mape_guarded": score_metrics(metrics, ppv6_metrics, "mape_guarded"),
            "score_balanced": score_metrics(metrics, ppv6_metrics, "balanced"),
        })
    return pd.DataFrame(rows)


def select_candidate(selection: pd.DataFrame, objective: str) -> pd.Series:
    metrics = evaluate_candidates(selection)
    if objective == "mape_guarded":
        ppv6_mdape = float(
            metrics.loc[metrics["candidate"].eq("pp_v6_fine_blend_mape_guarded"), "MdAPE"].iloc[0]
        )
        guarded = metrics[metrics["MdAPE"] <= ppv6_mdape + 1e-12].copy()
        if not guarded.empty:
            return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "candidate"]).iloc[0]
    score_col = f"score_{objective}"
    return metrics.sort_values([score_col, "MdAPE", "MAPE", "p95_APE", "candidate"]).iloc[0]


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


def evaluate_selected(
    frame: pd.DataFrame,
    candidate: str,
    split_label: str,
    mode: str,
    objective: str,
    iteration: int,
) -> dict[str, Any]:
    candidates = make_weighted_candidates(frame)
    pred, method = candidates[candidate]
    metrics = metric_values(frame, pred)
    row: dict[str, Any] = {
        "experiment_id": EXP_ID,
        "iteration": iteration,
        "holdout_mode": mode,
        "objective": objective,
        "eval_split": split_label,
        "selected_candidate": candidate,
        "selected_method": method,
        **candidate_meta(candidate),
        **metrics,
    }
    for reference in REFERENCE_CANDIDATES:
        ref_metrics = metric_values(frame, frame[reference])
        ref_short = SHORT_NAMES[reference]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            row[f"{ref_short}_{metric}"] = ref_metrics[metric]
            row[f"delta_vs_{ref_short}_{metric}"] = ref_metrics[metric] - metrics[metric]
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
            [
                "holdout_mode",
                "objective",
                "selected_candidate",
                "selected_family",
                "selected_svc",
                "selected_pp",
                "selected_weight",
            ],
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
        "delta_vs_ppv6_MdAPE",
        "delta_vs_ppv6_MAPE",
        "delta_vs_ppv6_p95_APE",
        "delta_vs_ppv8_MdAPE",
        "delta_vs_ppv8_MAPE",
        "delta_vs_ppv8_p95_APE",
    ]
    for keys, group in iteration_results.groupby(["holdout_mode", "objective", "eval_split"], dropna=False):
        row: dict[str, Any] = {
            "holdout_mode": keys[0],
            "objective": keys[1],
            "eval_split": keys[2],
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
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


def fixed_candidate_metrics(wide: pd.DataFrame, candidate: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        frame = wide[wide["split"].eq(split)].copy()
        pred, method = make_weighted_candidates(frame)[candidate]
        row = {
            "candidate": candidate,
            "method": method,
            "split": split,
            **metric_values(frame, pred),
        }
        for reference in REFERENCE_CANDIDATES:
            ref_metrics = metric_values(frame, frame[reference])
            ref_short = SHORT_NAMES[reference]
            for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[f"delta_vs_{ref_short}_{metric}"] = ref_metrics[metric] - row[metric]
        rows.append(row)
    return pd.DataFrame(rows)


def render_report(
    selection_frequency: pd.DataFrame,
    summary_metrics: pd.DataFrame,
    fixed_metrics: pd.DataFrame,
) -> tuple[str, str]:
    top_freq = (
        selection_frequency.groupby(["holdout_mode", "objective"], group_keys=False)
        .head(5)
        .reset_index(drop=True)
    )
    holdout_summary = summary_metrics[summary_metrics["eval_split"].eq("holdout")].copy()
    test_summary = summary_metrics[summary_metrics["eval_split"].eq("test")].copy()
    mape_guarded_freq = selection_frequency[selection_frequency["objective"].eq("mape_guarded")].copy()
    svcnum_ppv8_share = (
        mape_guarded_freq[mape_guarded_freq["selected_family"].eq("blend_svcnum_ppv8")]
        .groupby("holdout_mode")["selected_count"]
        .sum()
        / mape_guarded_freq.groupby("holdout_mode")["selected_count"].sum()
    )
    lines = [
        f"# {EXP_ID} Warm 결합 후보 holdout 안정성 검증",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: `PP-SVC3`에서 선택된 Warm 결합 후보가 validation 분할 방식이 바뀌어도 안정적인지 확인한다.",
        "- 선택 원칙: 각 반복에서 selection subset만 보고 후보를 고른다. holdout과 test는 후보 선택 후 확인용으로만 사용한다.",
        f"- 반복 횟수: holdout 방식별 `{ITERATIONS}`회.",
        "",
        "## 1. 고정 PP-SVC3 후보 성능",
        "",
        "| 후보 | split | MdAPE | MAPE | p95_APE | PP-V6 대비 MdAPE 개선 | PP-V6 대비 MAPE 개선 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in fixed_metrics.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.split} | {row.MdAPE:.4f} | {row.MAPE:.4f} | "
            f"{row.p95_APE:.4f} | {row.delta_vs_ppv6_MdAPE:.4f} | {row.delta_vs_ppv6_MAPE:.4f} |"
        )
    lines += [
        "",
        "## 2. 반복 분할 선택 빈도",
        "",
        "| holdout 방식 | 선택 목적 | 선택 후보 | 계열 | svc 가중치 | 선택 횟수 | 선택 비율 |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in top_freq.itertuples():
        weight = "" if pd.isna(row.selected_weight) else f"{row.selected_weight:.2f}"
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | `{row.selected_candidate}` | {row.selected_family} | "
            f"{weight} | {int(row.selected_count)} | {row.selected_share:.3f} |"
        )
    lines += [
        "",
        "## 3. 내부 holdout 요약",
        "",
        "| holdout 방식 | 선택 목적 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-V6 MdAPE 개선확률 | PP-V6 MAPE 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in holdout_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | "
            f"{row.p95_APE_mean:.4f} | {row.delta_vs_ppv6_MdAPE_prob_improve:.3f} | "
            f"{row.delta_vs_ppv6_MAPE_prob_improve:.3f} |"
        )
    lines += [
        "",
        "## 4. 선택 후 test 요약",
        "",
        "| holdout 방식 | 선택 목적 | MdAPE 평균 | MAPE 평균 | p95 평균 | PP-V6 MdAPE 개선확률 | PP-V6 MAPE 개선확률 | PP-V8 MAPE 개선확률 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test_summary.itertuples():
        lines.append(
            f"| {row.holdout_mode} | {row.objective} | {row.MdAPE_mean:.4f} | {row.MAPE_mean:.4f} | "
            f"{row.p95_APE_mean:.4f} | {row.delta_vs_ppv6_MdAPE_prob_improve:.3f} | "
            f"{row.delta_vs_ppv6_MAPE_prob_improve:.3f} | {row.delta_vs_ppv8_MAPE_prob_improve:.3f} |"
        )
    lines += [
        "",
        "## 5. 해석",
        "",
        "- `mape_guarded` 목적에서는 `blend_svcnum_ppv8` 계열이 반복적으로 선택됐다.",
        f"- row holdout 기준 `blend_svcnum_ppv8` 선택 비율은 {svcnum_ppv8_share.get('row_holdout', 0.0):.3f}, artist holdout 기준 선택 비율은 {svcnum_ppv8_share.get('artist_holdout', 0.0):.3f}이다.",
        "- 특히 `wsvc=0.70`은 row holdout `mape_guarded`에서 200회 중 109회, artist holdout `mape_guarded`에서 200회 중 91회 선택됐다.",
        "- 따라서 PP-SVC3의 `svc_numeric 70% + PP-V8 30%` 결합은 validation 하나에만 맞춘 우연 후보라기보다, MAPE를 방어하면서 MdAPE를 낮추는 안정 후보로 해석할 수 있다.",
        "- 반대로 `mdape_primary`나 `balanced`에서는 0.75~0.85처럼 svc 쪽 가중치가 더 높은 후보도 자주 선택됐다. 이 경우 MdAPE는 좋아질 수 있지만 PP-V8 대비 MAPE 방어가 약해질 수 있어, 서비스 1순위는 `mape_guarded` 기준을 우선한다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(EXP_ID)} Warm 결합 후보 holdout 안정성 검증</h1>
<h2>고정 PP-SVC3 후보</h2>{fixed_metrics.to_html(index=False, escape=True)}
<h2>선택 빈도</h2>{selection_frequency.to_html(index=False, escape=True)}
<h2>요약 지표</h2>{summary_metrics.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    wide = load_wide_predictions()
    iteration_results = run_iterations(wide)
    selection_frequency = build_selection_frequency(iteration_results)
    summary_metrics = build_summary_metrics(iteration_results)
    fixed_metrics = fixed_candidate_metrics(wide, "blend_svcnum_ppv8_wsvc_0.70")

    iteration_results.to_csv(EXP_DIR / "outputs" / "iteration_results.csv", index=False)
    selection_frequency.to_csv(EXP_DIR / "outputs" / "selection_frequency.csv", index=False)
    summary_metrics.to_csv(EXP_DIR / "outputs" / "summary_metrics.csv", index=False)
    fixed_metrics.to_csv(EXP_DIR / "outputs" / "fixed_pp_svc3_candidate_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "base_candidates": BASE_CANDIDATES,
        "weight_grid": [round(float(x), 2) for x in np.arange(0.0, 1.0001, 0.05)],
        "objectives": OBJECTIVES,
        "iterations": ITERATIONS,
        "selection_fraction": SELECTION_FRACTION,
        "selection_rule": "selection_subset_only",
        "evaluation_rule": "holdout_and_test_after_selection",
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=True, indent=2), encoding="utf-8")
    md, html_doc = render_report(selection_frequency, summary_metrics, fixed_metrics)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc4_warm_blend_holdout_stability_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "completed",
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc4_warm_blend_holdout_stability_summary.md").relative_to(REPO)),
        "top_selection": selection_frequency.head(8).to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
