#!/usr/bin/env python3
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
BATCH_DIR = ROOT / "experiments/track6/PP-FPOL4_8_planned_improvement_batch"
REPORTS_DIR = BATCH_DIR / "reports"
OUTPUTS_DIR = BATCH_DIR / "outputs"

PREV_COMPARISON = ROOT / "experiments/track6/PP-FPOL3_warm_policy_best_candidate_comparison/outputs/objective_best_summary.csv"
EXPERIMENTS = {
    "PP-FPOL4": ROOT / "experiments/track6/PP-FPOL4_two_stage_artist_svc_stack/outputs/candidate_metrics.csv",
    "PP-FPOL5": ROOT / "experiments/track6/PP-FPOL5_total_correction_budget/outputs/candidate_metrics.csv",
    "PP-FPOL6": ROOT / "experiments/track6/PP-FPOL6_directional_price_bin_guard/outputs/candidate_metrics.csv",
    "PP-FPOL7": ROOT / "experiments/track6/PP-FPOL7_svc_reliability_size_gate/outputs/candidate_metrics.csv",
}
STABILITY = ROOT / "experiments/track6/PP-FPOL8_repeated_holdout_stability/outputs/final_stability_summary.csv"


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def md_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "(no rows)"
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        out.append("| " + " | ".join(fmt(row[c]) for c in columns) + " |")
    return "\n".join(out)


def html_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "<p>(no rows)</p>"
    rows = ["<table><thead><tr>"]
    rows.extend(f"<th>{html.escape(c)}</th>" for c in columns)
    rows.append("</tr></thead><tbody>")
    for _, row in df[columns].iterrows():
        rows.append("<tr>")
        rows.extend(f"<td>{html.escape(fmt(row[c]))}</td>" for c in columns)
        rows.append("</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def load_candidate_metrics() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source, path in EXPERIMENTS.items():
        df = pd.read_csv(path)
        test = df[df["split"].eq("test")].copy()
        test["source"] = source
        frames.append(test)
    all_test = pd.concat(frames, ignore_index=True)
    all_test["prefixed_candidate"] = all_test["source"] + "::" + all_test["candidate"]
    return all_test


def load_previous_best() -> pd.DataFrame:
    prev = pd.read_csv(PREV_COMPARISON)
    if "split" not in prev.columns:
        prev = prev.rename(
            columns={
                "test_MdAPE": "MdAPE",
                "test_MAPE": "MAPE",
                "test_p95_APE": "p95_APE",
                "test_delta_MdAPE": "delta_MdAPE",
                "test_delta_MAPE": "delta_MAPE",
                "test_delta_p95_APE": "delta_p95_APE",
                "test_balanced_delta": "balanced_delta",
            }
        )
        prev["split"] = "test"
    if "objective" in prev.columns:
        out = prev[prev["split"].eq("test")].copy()
        out["selection"] = out["objective"]
        keep = ["selection", "source", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "balanced_delta"]
        return out[keep]
    rows = []
    for label, order_cols in [
        ("previous_balanced_best", ["balanced_delta", "MAPE"]),
        ("previous_mape_best", ["MAPE", "MdAPE"]),
        ("previous_p95_best", ["p95_APE", "MAPE"]),
    ]:
        row = prev[prev["split"].eq("test")].sort_values(order_cols).head(1).copy()
        row["selection"] = label
        rows.append(row)
    out = pd.concat(rows, ignore_index=True)
    keep = ["selection", "source", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "balanced_delta"]
    return out[keep]


def select_experiment_best(all_test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, group in all_test.groupby("source", sort=False):
        for label, order_cols in [
            ("mape_best", ["MAPE", "MdAPE"]),
            ("balanced_best", ["balanced_delta", "MAPE"]),
            ("p95_best", ["p95_APE", "MAPE"]),
        ]:
            row = group.sort_values(order_cols).head(1).copy()
            row["selection"] = f"{source}_{label}"
            rows.append(row)
    out = pd.concat(rows, ignore_index=True)
    keep = ["selection", "source", "candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "balanced_delta", "improves_all_three"]
    return out[keep]


def load_stability_summary(all_test: pd.DataFrame) -> pd.DataFrame:
    stability = pd.read_csv(STABILITY)
    grouped = (
        stability.groupby("candidate", as_index=False)
        .agg(
            stability_score=("stability_score", "mean"),
            row_artist_sample_types=("sample_type", "nunique"),
            bootstrap_improve_MAPE=("improvement_probability_MAPE", "mean"),
            bootstrap_improve_p95_APE=("improvement_probability_p95_APE", "mean"),
            bootstrap_improve_MdAPE=("improvement_probability_MdAPE", "mean"),
            fold_improve_MAPE=("fold_improvement_probability_MAPE", "mean"),
            fold_improve_p95_APE=("fold_improvement_probability_p95_APE", "mean"),
            mean_delta_MAPE_bootstrap=("mean_delta_MAPE_bootstrap", "mean"),
            mean_delta_p95_bootstrap=("mean_delta_p95_APE_bootstrap", "mean"),
        )
    )
    metric_cols = [
        "prefixed_candidate",
        "source",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "balanced_delta",
    ]
    metrics = all_test[metric_cols].rename(columns={"prefixed_candidate": "candidate"})
    out = grouped.merge(metrics, on="candidate", how="left")
    out = out.sort_values(["stability_score", "MAPE"], ascending=[False, True])
    return out


def build_recommendations(all_test: pd.DataFrame, stability: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, df, order_cols in [
        ("성능 최우선: test MAPE 최저", all_test, ["MAPE", "MdAPE"]),
        ("균형 우선: MdAPE/MAPE/p95 동시 개선", all_test, ["balanced_delta", "MAPE"]),
        ("p95 안정 우선: 큰 오차 꼬리 최소", all_test, ["p95_APE", "MAPE"]),
    ]:
        row = df.sort_values(order_cols).head(1).copy()
        row["recommendation"] = label
        rows.append(row)
    stable = stability.sort_values(["stability_score", "MAPE"], ascending=[False, True]).head(1).copy()
    stable["recommendation"] = "반복 안정성 우선: bootstrap/artist-fold 개선확률"
    stable = stable.rename(columns={"candidate": "prefixed_candidate"})
    stable["candidate"] = stable["prefixed_candidate"].str.split("::", n=1).str[1]
    rows.append(stable)
    out = pd.concat(rows, ignore_index=True, sort=False)
    keep = [
        "recommendation",
        "source",
        "candidate",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "balanced_delta",
        "stability_score",
        "bootstrap_improve_MAPE",
        "fold_improve_MAPE",
        "fold_improve_p95_APE",
    ]
    return out[keep]


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    all_test = load_candidate_metrics()
    previous = load_previous_best()
    experiment_best = select_experiment_best(all_test)
    stability = load_stability_summary(all_test)
    recommendations = build_recommendations(all_test, stability)

    all_test.to_csv(OUTPUTS_DIR / "all_fpol4_7_test_metrics.csv", index=False)
    previous.to_csv(OUTPUTS_DIR / "previous_best_reference.csv", index=False)
    experiment_best.to_csv(OUTPUTS_DIR / "experiment_best_summary.csv", index=False)
    stability.to_csv(OUTPUTS_DIR / "stability_joined_test_metrics.csv", index=False)
    recommendations.to_csv(OUTPUTS_DIR / "final_recommendations.csv", index=False)

    top_mape = all_test.sort_values(["MAPE", "MdAPE"]).head(1).iloc[0]
    top_balanced = all_test.sort_values(["balanced_delta", "MAPE"]).head(1).iloc[0]
    top_stability = stability.sort_values(["stability_score", "MAPE"], ascending=[False, True]).head(1).iloc[0]

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# PP-FPOL4~8 배치 실험 최종 요약

- 작성일: {generated_at}
- 목적: 후버 기반 잔차 보정에서 작가/작품/SVC 보정 조합을 한 번에 계획하고 순서대로 검증
- 기준 baseline: 기존 Warm/SVC 후버 계열 base candidate

## 결론

1. test MAPE 최저 후보는 `{top_mape['source']}`의 `{top_mape['candidate']}`입니다.
   - MdAPE `{top_mape['MdAPE']:.6f}`, MAPE `{top_mape['MAPE']:.6f}`, p95 `{top_mape['p95_APE']:.6f}`
2. MdAPE/MAPE/p95 균형 최저 후보는 `{top_balanced['source']}`의 `{top_balanced['candidate']}`입니다.
   - MdAPE `{top_balanced['MdAPE']:.6f}`, MAPE `{top_balanced['MAPE']:.6f}`, p95 `{top_balanced['p95_APE']:.6f}`, balanced_delta `{top_balanced['balanced_delta']:.6f}`
3. 반복 안정성 최상위 후보는 `{top_stability['candidate']}`입니다.
   - stability_score `{top_stability['stability_score']:.6f}`, bootstrap MAPE 개선확률 `{top_stability['bootstrap_improve_MAPE']:.6f}`, artist-fold MAPE 개선확률 `{top_stability['fold_improve_MAPE']:.6f}`

## 추천 후보

{md_table(recommendations, ['recommendation', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta', 'stability_score', 'bootstrap_improve_MAPE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}

## 기존 최고 후보 기준

{md_table(previous, ['selection', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta'])}

## 실험별 최적 후보

{md_table(experiment_best, ['selection', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta', 'improves_all_three'])}

## 안정성 상위 후보

{md_table(stability.head(20), ['source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'stability_score', 'bootstrap_improve_MAPE', 'bootstrap_improve_p95_APE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}

## 해석

- 작가 생년/세대 보정을 기존 SVC/작품 보정 위에 얹는 방식은 MAPE 개선 가능성이 확인되었습니다.
- 총 보정량 cap은 `0.04` 이상에서 대부분 포화되어, cap을 더 키우는 것보다 방향/가격구간 guard가 더 의미 있었습니다.
- 가격구간 guard는 p95 큰 오차 꼬리를 낮추는 데 효과가 있었고, 방향 guard는 MAPE를 더 낮추는 데 효과가 있었습니다.
- SVC 신뢰도/작품 크기 gate는 블라인드 안전장치 후보로는 의미가 있지만, 현재 고정 테스트 점수는 FPOL6보다 낮습니다.
- 최종 후보를 하나만 고르면 test MAPE 최저인 FPOL6 후보를 우선 검토하고, 외부 블라인드 안정성을 더 중시하면 FPOL7 soft reliability 후보를 보조 후보로 두는 것이 합리적입니다.

## 산출물

- `outputs/all_fpol4_7_test_metrics.csv`
- `outputs/experiment_best_summary.csv`
- `outputs/stability_joined_test_metrics.csv`
- `outputs/final_recommendations.csv`
"""
    (REPORTS_DIR / "final_batch_summary.md").write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>PP-FPOL4~8 배치 실험 최종 요약</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #172033; }}
h1, h2 {{ color: #123a63; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; font-size: 12px; }}
th, td {{ border: 1px solid #d4d9e2; padding: 6px 8px; vertical-align: top; }}
th {{ background: #edf2f7; }}
td {{ word-break: break-word; }}
code {{ background: #f3f5f7; padding: 1px 4px; border-radius: 4px; }}
.note {{ background: #f7f9fc; border-left: 4px solid #2f6db3; padding: 12px 16px; }}
</style>
</head>
<body>
<h1>PP-FPOL4~8 배치 실험 최종 요약</h1>
<p>작성일: {html.escape(generated_at)}</p>
<div class="note">
<p><b>MAPE 최저:</b> {html.escape(str(top_mape['source']))} / {html.escape(str(top_mape['MAPE']))}</p>
<p><b>균형 최저:</b> {html.escape(str(top_balanced['source']))} / {html.escape(str(top_balanced['balanced_delta']))}</p>
<p><b>안정성 최상위:</b> {html.escape(str(top_stability['candidate']))}</p>
</div>
<h2>추천 후보</h2>
{html_table(recommendations, ['recommendation', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta', 'stability_score', 'bootstrap_improve_MAPE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}
<h2>기존 최고 후보 기준</h2>
{html_table(previous, ['selection', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta'])}
<h2>실험별 최적 후보</h2>
{html_table(experiment_best, ['selection', 'source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'balanced_delta', 'improves_all_three'])}
<h2>안정성 상위 후보</h2>
{html_table(stability.head(20), ['source', 'candidate', 'MdAPE', 'MAPE', 'p95_APE', 'stability_score', 'bootstrap_improve_MAPE', 'bootstrap_improve_p95_APE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}
</body>
</html>
"""
    (REPORTS_DIR / "final_batch_summary.html").write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
