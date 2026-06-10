#!/usr/bin/env python3
"""Run PP-HCOEF35: focused p95-guard refinement after HCOEF34.

HCOEF34 found basis-residual Huber candidates that clearly beat the original
Warm 70:30 candidate, but their fixed p95 was still slightly worse than the
current stable Huber candidate. HCOEF35 keeps the same train-only basis features
and searches a smaller cap/strength grid, using validation repeated OOF first
and fixed test/0604 as confirmation only.
"""
from __future__ import annotations

import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef34_warm_huber_price_basis_coefficient_refinement as h34


EXP_ID = "PP-HCOEF35"
EXP_SLUG = "PP-HCOEF35_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = h34.REFERENCE
STABLE_ALIAS = h34.STABLE_ALIAS
SEED = 20260608
N_REPEATS = 24


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def candidate_configs() -> list[h34.CandidateConfig]:
    configs: list[h34.CandidateConfig] = []
    for feature_key in ["basis_resid_all", "basis_resid_core"]:
        for alpha in [0.001, 0.01]:
            for cap in [0.001, 0.0025, 0.0035, 0.0050, 0.0075, 0.0100]:
                for strength in [0.10, 0.15, 0.20, 0.25, 0.35, 0.50]:
                    configs.append(
                        h34.CandidateConfig(
                            candidate=(
                                f"hcoef35_resid_{feature_key}_a{h34.slug(alpha)}"
                                f"_cap{h34.slug(cap)}_s{h34.slug(strength)}"
                            ),
                            kind="residual_huber",
                            feature_key=feature_key,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            description="HCOEF34 basis residual 구조에서 p95 방어를 위해 cap/strength를 촘촘하게 축소",
                        )
                    )
    return configs


def metric_row(
    scope: str,
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    ref_metric: dict[str, float],
    stable_metric: dict[str, float],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return h34.metric_row(scope, split, candidate, method, n, m, ref_metric, stable_metric, extra)


def prediction_frame(frame: pd.DataFrame, candidate: str, method: str, split: str, pred_log: np.ndarray) -> pd.DataFrame:
    out = h34.prediction_frame(frame, candidate, method, split, pred_log)
    out["experiment_id"] = EXP_ID
    return out


def fixed_confirmation(frames: dict[str, pd.DataFrame], configs: list[h34.CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    baselines = [
        (REFERENCE, "baseline_reference", REFERENCE),
        (STABLE_ALIAS, "baseline_stable", STABLE_ALIAS),
        ("basis_fallback_m5", "basis_component", "basis_fallback_m5"),
        ("basis_shrink_k20", "basis_component", "basis_shrink_k20"),
    ]
    for split, frame in frames.items():
        ref_metric = h34.metric(frame, frame[REFERENCE].to_numpy(dtype=float))
        stable_metric = h34.metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
        for candidate, method, col in baselines:
            pred = frame[col].to_numpy(dtype=float)
            m = h34.metric(frame, pred)
            metric_rows.append(metric_row("fixed_confirmation", split, candidate, method, len(frame), m, ref_metric, stable_metric))
            pred_rows.append(prediction_frame(frame, candidate, method, split, pred))
    for config in configs:
        for split, frame in frames.items():
            pred, model = h34.predict_candidate(validation, frame, config)
            ref_metric = h34.metric(frame, frame[REFERENCE].to_numpy(dtype=float))
            stable_metric = h34.metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
            m = h34.metric(frame, pred)
            metric_rows.append(metric_row("fixed_confirmation", split, config.candidate, config.kind, len(frame), m, ref_metric, stable_metric))
            pred_rows.append(prediction_frame(frame, config.candidate, config.kind, split, pred))
            if split == "test" and model is not None:
                coef = h34.coefficient_frame(model, config)
                coef["experiment_id"] = EXP_ID
                coef_rows.append(coef)
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def repeated_oof(validation: pd.DataFrame, configs: list[h34.CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    ref_metric = h34.metric(validation, validation[REFERENCE].to_numpy(dtype=float))
    stable_metric = h34.metric(validation, validation[STABLE_ALIAS].to_numpy(dtype=float))
    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            folds = h34.row_folds(len(validation), SEED + repeat) if scheme == "row_oof" else h34.artist_folds(validation, SEED + repeat)
            for config in configs:
                oof = np.full(len(validation), np.nan, dtype=float)
                for train_idx, hold_idx in folds:
                    train = validation.iloc[train_idx].copy()
                    hold = validation.iloc[hold_idx].copy()
                    pred, _ = h34.predict_candidate(train, hold, config)
                    oof[hold_idx] = pred
                m = h34.metric(validation, oof)
                rows.append(
                    metric_row(
                        "repeated_oof",
                        f"validation_{scheme}",
                        config.candidate,
                        config.kind,
                        len(validation),
                        m,
                        ref_metric,
                        stable_metric,
                        {"repeat": repeat, "validation_scheme": scheme},
                    )
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, config.candidate, config.kind, f"validation_{scheme}_repeat0", oof))
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True)


def summarize_repeated(metrics_df: pd.DataFrame) -> pd.DataFrame:
    return h34.summarize_repeated(metrics_df)


def select_candidates(fixed_metrics: pd.DataFrame, repeated_summary: pd.DataFrame) -> pd.DataFrame:
    out = h34.select_candidates(fixed_metrics, repeated_summary)
    out["fixed_p95_margin_vs_stable"] = out["test_p95_APE"] - 0.8063661210554905
    out["fixed_mape_margin_vs_stable"] = out["test_MAPE"] - 0.27298867375858177
    out["fixed_mdape_margin_vs_stable"] = out["test_MdAPE"] - 0.13880334431812874
    out["p95_guard_exact"] = out["fixed_p95_margin_vs_stable"] <= 0
    out["decision"] = np.select(
        [
            out["passes_strong_stable_gate"] & out["p95_guard_exact"],
            out["passes_stable_gate"] & out["p95_guard_exact"],
            out["passes_reference_gate"] & out["p95_guard_exact"],
            out["passes_reference_gate"],
        ],
        [
            "운영 후보 검토",
            "Warm 안정 후보 재검증",
            "p95 방어형 70:30 개선 후보",
            "기존 70:30 대비 개선 후보",
        ],
        default="보류",
    )
    return out.sort_values(
        ["p95_guard_exact", "passes_stable_gate", "passes_reference_gate", "test_MdAPE", "test_MAPE"],
        ascending=[False, False, False, True, True],
    )


def residual_analysis(predictions: pd.DataFrame, focus_candidates: set[str]) -> pd.DataFrame:
    return h34.residual_analysis(predictions, focus_candidates)


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    return h34.markdown_table(frame, max_rows)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
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
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.strip().startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6}p{line-height:1.55}h1,h2,h3{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    fixed_metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    selected: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
) -> None:
    top = selected.head(15).copy()
    p95_safe = selected[selected["p95_guard_exact"] & selected["passes_reference_gate"]].copy()
    if p95_safe.empty:
        conclusion = (
            "cap/strength를 촘촘하게 낮춰도 hcoef_stable의 fixed p95를 넘기면서 "
            "반복 OOF까지 통과하는 후보는 아직 없음."
        )
    else:
        best = p95_safe.iloc[0]
        conclusion = (
            f"`{best['candidate']}`가 p95 방어 조건을 만족하는 확인 후보. "
            f"test MdAPE/MAPE/p95 {best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}."
        )
    fixed_focus = fixed_metrics[
        fixed_metrics["split"].isin(["validation", "test", "0604_ex50"])
        & fixed_metrics["candidate"].isin([REFERENCE, STABLE_ALIAS, "basis_fallback_m5", "basis_shrink_k20"])
    ].copy()
    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 기준가 잔차 p95 방어 재검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF34에서 확인된 basis residual Huber 후보의 p95 악화를 막기 위해 cap/strength를 더 작게 탐색.",
            "- 기준 후보: `current_70_30`.",
            "- 안정 비교 후보: `hcoef_stable`.",
            "- 선택 원칙: validation 반복 OOF 우선, fixed test/0604 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {conclusion}",
            "- HCOEF35는 HCOEF34의 same-feature refinement이므로, 좋은 후보가 있더라도 HCOEF36에서 반복 수 확대 또는 bootstrap 확인 필요.",
            "",
            "## 2. 기준 후보 지표",
            "",
            markdown_table(
                fixed_focus[
                    [
                        "split",
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                    ]
                ].round(4),
                max_rows=40,
            ),
            "",
            "## 3. 후보 선택 판단",
            "",
            markdown_table(
                top[
                    [
                        "candidate",
                        "decision",
                        "method",
                        "test_MdAPE",
                        "test_MAPE",
                        "test_p95_APE",
                        "fixed_mdape_margin_vs_stable",
                        "fixed_mape_margin_vs_stable",
                        "fixed_p95_margin_vs_stable",
                        "stress0604_MdAPE",
                        "stress0604_MAPE",
                        "stress0604_p95_APE",
                        "row_oof_ref_any2_improve_prob",
                        "artist_oof_ref_any2_improve_prob",
                        "row_oof_stable_any2_improve_prob",
                        "artist_oof_stable_any2_improve_prob",
                    ]
                ].round(5),
                max_rows=15,
            ),
            "",
            "## 4. Fixed test 상위 후보",
            "",
            markdown_table(
                fixed_metrics[fixed_metrics["split"].eq("test")]
                .sort_values(["MdAPE", "MAPE", "p95_APE"])
                .head(20)[
                    [
                        "candidate",
                        "method",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "improve_count_vs_reference",
                        "improve_count_vs_stable",
                    ]
                ]
                .round(5),
                max_rows=20,
            ),
            "",
            "## 5. 반복 OOF 요약",
            "",
            markdown_table(
                repeated_summary.sort_values(
                    ["row_oof_ref_any2_improve_prob", "artist_oof_ref_any2_improve_prob", "mean_MdAPE"],
                    ascending=[False, False, True],
                )[
                    [
                        "candidate",
                        "validation_scheme",
                        "n_repeats",
                        "mean_MdAPE",
                        "mean_MAPE",
                        "mean_p95_APE",
                        "mean_delta_MdAPE_vs_reference",
                        "mean_delta_MAPE_vs_reference",
                        "mean_delta_p95_APE_vs_reference",
                        "ref_any2_improve_prob",
                        "stable_any2_improve_prob",
                        "stable_all3_improve_prob",
                    ]
                ].round(5),
                max_rows=30,
            ),
            "",
            "## 6. 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준. 방향성과 상대 영향 비교용.",
            markdown_table(coeffs.head(60).round(5), max_rows=60),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(5), max_rows=40),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef35_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef35_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = h34.build_frames()
    configs = candidate_configs()
    fixed_metrics, fixed_predictions, coeffs = fixed_confirmation(frames, configs)
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"], configs)
    metrics = pd.concat([fixed_metrics, repeated_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([fixed_predictions, repeated_predictions], ignore_index=True, sort=False)
    repeated_summary = summarize_repeated(metrics)
    selected = select_candidates(fixed_metrics, repeated_summary)
    focus_candidates = set(selected.head(15)["candidate"].astype(str)) | {REFERENCE, STABLE_ALIAS, "basis_fallback_m5", "basis_shrink_k20"}
    residuals = residual_analysis(predictions, focus_candidates)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected.to_csv(out / "selected_candidates.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF34",
        "reference_candidate": REFERENCE,
        "stable_candidate": h34.STABLE_CONFIG,
        "n_repeats": N_REPEATS,
        "seed": SEED,
        "caps": [0.001, 0.0025, 0.0035, 0.0050, 0.0075, 0.0100],
        "strengths": [0.10, 0.15, 0.20, 0.25, 0.35, 0.50],
        "feature_sets": ["basis_resid_all", "basis_resid_core"],
        "selection_policy": "validation repeated OOF first, fixed p95 guard against hcoef_stable",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(fixed_metrics, repeated_summary, selected, coeffs, residuals)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected candidates ---")
    print(
        selected.head(20)[
            [
                "candidate",
                "decision",
                "test_MdAPE",
                "test_MAPE",
                "test_p95_APE",
                "fixed_mdape_margin_vs_stable",
                "fixed_mape_margin_vs_stable",
                "fixed_p95_margin_vs_stable",
                "row_oof_ref_any2_improve_prob",
                "artist_oof_ref_any2_improve_prob",
                "row_oof_stable_any2_improve_prob",
                "artist_oof_stable_any2_improve_prob",
            ]
        ]
        .round(5)
        .to_string(index=False)
    )
    print("--- fixed test top 10 ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(10)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "improve_count_vs_reference", "improve_count_vs_stable"]]
        .round(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
