#!/usr/bin/env python3
"""Run PP-H27 bootstrap validation for PP-H23/H26 search candidates."""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_ID = "PP-H27"
EXP_SLUG = "PP-H27_search_candidate_stability_validation"
TITLE = "H23/H26 검색 보정 후보 안정성 검증"

PRED_PATH = BASE_EXP_DIR / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
BOOTSTRAP_ITERATIONS = 800
SEED = 20260603

CANDIDATES = {
    "h23_gallery_museum_median_cap0.1": {
        "pred_col": "h23_gallery_museum_median_cap0.1__pred_log",
        "family": "PP-H23",
        "description": "갤러리/미술관 소스군 보정 cap0.1",
    },
    "h23_gallery_museum_median_cap0.2": {
        "pred_col": "h23_gallery_museum_median_cap0.2__pred_log",
        "family": "PP-H23",
        "description": "갤러리/미술관 소스군 보정 cap0.2",
    },
    "h23_exhibition_median_cap0.1": {
        "pred_col": "h23_exhibition_median_cap0.1__pred_log",
        "family": "PP-H23",
        "description": "전시 문맥 소스군 보정 cap0.1",
    },
    "h23_exhibition_median_cap0.2": {
        "pred_col": "h23_exhibition_median_cap0.2__pred_log",
        "family": "PP-H23",
        "description": "전시 문맥 소스군 보정 cap0.2",
    },
    "h23_news_median_cap0.1": {
        "pred_col": "h23_news_median_cap0.1__pred_log",
        "family": "PP-H23",
        "description": "뉴스 소스군 보정 cap0.1",
    },
    "h23_news_median_cap0.2": {
        "pred_col": "h23_news_median_cap0.2__pred_log",
        "family": "PP-H23",
        "description": "뉴스 소스군 보정 cap0.2",
    },
    "h23_social_blog_median_cap0.1": {
        "pred_col": "h23_social_blog_median_cap0.1__pred_log",
        "family": "PP-H23",
        "description": "블로그/소셜 소스군 보정 cap0.1",
    },
    "h23_social_blog_median_cap0.2": {
        "pred_col": "h23_social_blog_median_cap0.2__pred_log",
        "family": "PP-H23",
        "description": "블로그/소셜 소스군 보정 cap0.2",
    },
    "h26_risk_qwidth_action_median_cap0.1": {
        "pred_col": "h26_risk_qwidth_action_median_cap0.1__pred_log",
        "family": "PP-H26",
        "description": "위험 action x q-width 보정 cap0.1",
    },
    "h26_risk_qwidth_action_median_cap0.2": {
        "pred_col": "h26_risk_qwidth_action_median_cap0.2__pred_log",
        "family": "PP-H26",
        "description": "위험 action x q-width 보정 cap0.2",
    },
    "h26_confidence_only_lower_q10_blend0.5": {
        "pred_col": "h26_confidence_only_lower_q10_blend0.5__pred_log",
        "family": "PP-H26",
        "description": "위험 action q10 방향 블렌딩 0.5",
    },
}


def metric_values(frame: pd.DataFrame, pred_col: str) -> dict[str, float]:
    if frame.empty:
        return {
            "n": 0,
            "MdAPE": math.nan,
            "MAPE": math.nan,
            "p95_APE": math.nan,
            "RMSE_log": math.nan,
            "Within_30": math.nan,
            "Within_50": math.nan,
        }
    actual_log = frame["actual_log"].astype(float).to_numpy()
    pred_log = frame[pred_col].astype(float).to_numpy()
    actual = frame["actual_price"].astype(float).to_numpy()
    pred = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def metric_delta(base_metrics: dict[str, float], candidate_metrics: dict[str, float]) -> dict[str, float]:
    return {
        "delta_MdAPE": base_metrics["MdAPE"] - candidate_metrics["MdAPE"],
        "delta_MAPE": base_metrics["MAPE"] - candidate_metrics["MAPE"],
        "delta_p95_APE": base_metrics["p95_APE"] - candidate_metrics["p95_APE"],
        "delta_RMSE_log": base_metrics["RMSE_log"] - candidate_metrics["RMSE_log"],
        "delta_Within_30": candidate_metrics["Within_30"] - base_metrics["Within_30"],
        "delta_Within_50": candidate_metrics["Within_50"] - base_metrics["Within_50"],
    }


def build_point_metrics(pred: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, group in pred.groupby("split", dropna=False):
        rows.append({
            "experiment_id": EXP_ID,
            "family": "baseline",
            "candidate": "pp_y2_base",
            "split": split,
            "slice": "overall",
            "description": "PP-Y2 기준 예측",
            **metric_values(group, "pred_log"),
        })
        for candidate, cfg in CANDIDATES.items():
            rows.append({
                "experiment_id": EXP_ID,
                "family": cfg["family"],
                "candidate": candidate,
                "split": split,
                "slice": "overall",
                "description": cfg["description"],
                **metric_values(group, cfg["pred_col"]),
            })
        for action, seg in group.groupby("recommended_action", dropna=False):
            rows.append({
                "experiment_id": EXP_ID,
                "family": "baseline",
                "candidate": "pp_y2_base",
                "split": split,
                "slice": f"h12_action={action}",
                "description": "PP-Y2 기준 예측",
                **metric_values(seg, "pred_log"),
            })
            for candidate, cfg in CANDIDATES.items():
                rows.append({
                    "experiment_id": EXP_ID,
                    "family": cfg["family"],
                    "candidate": candidate,
                    "split": split,
                    "slice": f"h12_action={action}",
                    "description": cfg["description"],
                    **metric_values(seg, cfg["pred_col"]),
                })
    return pd.DataFrame(rows)


def row_bootstrap(test: pd.DataFrame, rng: np.random.Generator, slice_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    n = len(test)
    if n == 0:
        return pd.DataFrame()
    for iteration in range(BOOTSTRAP_ITERATIONS):
        sample = test.iloc[rng.integers(0, n, size=n)]
        base_metrics = metric_values(sample, "pred_log")
        for candidate, cfg in CANDIDATES.items():
            candidate_metrics = metric_values(sample, cfg["pred_col"])
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": "row",
                "slice": slice_name,
                "iteration": iteration,
                "family": cfg["family"],
                "candidate": candidate,
                **metric_delta(base_metrics, candidate_metrics),
            })
    return pd.DataFrame(rows)


def artist_bootstrap(test: pd.DataFrame, rng: np.random.Generator, slice_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if test.empty:
        return pd.DataFrame()
    artist_col = "artist_key" if "artist_key" in test.columns else "artist_search_name"
    artists = test[artist_col].fillna("__MISSING_ARTIST__").astype(str)
    groups = {
        artist: group.copy()
        for artist, group in test.assign(_bootstrap_artist=artists).groupby("_bootstrap_artist", dropna=False)
    }
    artist_keys = np.array(list(groups.keys()), dtype=object)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        sampled = rng.choice(artist_keys, size=len(artist_keys), replace=True)
        sample = pd.concat([groups[artist] for artist in sampled], ignore_index=True)
        base_metrics = metric_values(sample, "pred_log")
        for candidate, cfg in CANDIDATES.items():
            candidate_metrics = metric_values(sample, cfg["pred_col"])
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": "artist",
                "slice": slice_name,
                "iteration": iteration,
                "family": cfg["family"],
                "candidate": candidate,
                **metric_delta(base_metrics, candidate_metrics),
            })
    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "delta_RMSE_log",
        "delta_Within_30",
        "delta_Within_50",
    ]
    rows: list[dict[str, Any]] = []
    for (bootstrap_type, slice_name, family, candidate), group in bootstrap.groupby(
        ["bootstrap_type", "slice", "family", "candidate"],
        dropna=False,
    ):
        for metric in metric_cols:
            values = group[metric].astype(float).dropna().to_numpy()
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": bootstrap_type,
                "slice": slice_name,
                "family": family,
                "candidate": candidate,
                "metric": metric,
                "median_delta": float(np.median(values)),
                "ci_low_2_5": float(np.quantile(values, 0.025)),
                "ci_high_97_5": float(np.quantile(values, 0.975)),
                "prob_improvement_gt_0": float(np.mean(values > 0)),
                "n_bootstrap": int(len(values)),
            })
    return pd.DataFrame(rows)


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(df: pd.DataFrame, max_rows: int = 80) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def render_report(metrics: pd.DataFrame, summary: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    test_overall = metrics[metrics["split"].eq("test") & metrics["slice"].eq("overall")].sort_values(
        ["MdAPE", "MAPE"],
        na_position="last",
    )
    risk = metrics[metrics["split"].eq("test") & metrics["slice"].eq("h12_action=confidence_only_or_manual_review")].sort_values(
        ["p95_APE", "MAPE"],
        na_position="last",
    )
    focus = summary[
        summary["metric"].isin(["delta_MdAPE", "delta_MAPE", "delta_p95_APE", "delta_RMSE_log"])
    ].sort_values(["slice", "candidate", "bootstrap_type", "metric"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- PP-H23 전시 문맥 보정과 PP-H26 위험 구간 fallback 후보가 test 단일 결과에서만 좋아진 것인지 확인한다.",
        "- row bootstrap은 작품 단위 안정성을 확인한다.",
        "- artist bootstrap은 특정 작가 구성에 의존하는지 확인한다.",
        "- delta는 `기준 모델 점수 - 후보 점수`다. 오차 지표에서는 양수일수록 후보가 좋다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"})),
        "",
        "## Test 전체 점수",
        "",
        markdown_table(test_overall),
        "",
        "## 위험 구간 점수",
        "",
        markdown_table(risk),
        "",
        "## Bootstrap 안정성 요약",
        "",
        markdown_table(focus, max_rows=160),
        "",
        "## 해석 기준",
        "",
        "- 전체 slice에서 안정적이면 운영 후보로 볼 수 있다.",
        "- 위험 구간 slice에서만 안정적이면 전체 모델 보정이 아니라 위험 구간 전용 정책으로 남긴다.",
        "- artist bootstrap 개선 확률이 낮으면 특정 작가 구성에 민감하므로 수동 검수 후 재실행해야 한다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{EXP_ID}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>{EXP_ID} {TITLE}</h1>
<div class="note">delta는 기준 모델 점수에서 후보 점수를 뺀 값입니다. 오차 지표에서는 양수일수록 좋습니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>Test 전체 점수</h2>{test_overall.to_html(index=False, escape=True)}
<h2>위험 구간 점수</h2>{risk.to_html(index=False, escape=True)}
<h2>Bootstrap 안정성 요약</h2>{focus.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = datetime.now()
    pred = pd.read_csv(PRED_PATH, low_memory=False)
    missing_cols = [cfg["pred_col"] for cfg in CANDIDATES.values() if cfg["pred_col"] not in pred.columns]
    if missing_cols:
        raise ValueError(f"Missing candidate prediction columns: {missing_cols}")

    metrics = build_point_metrics(pred)
    test = pred[pred["split"].eq("test")].copy()
    risk_test = test[test["recommended_action"].eq("confidence_only_or_manual_review")].copy()

    rng = np.random.default_rng(SEED)
    bootstrap = pd.concat(
        [
            row_bootstrap(test, rng, "overall"),
            artist_bootstrap(test, rng, "overall"),
            row_bootstrap(risk_test, rng, "h12_action=confidence_only_or_manual_review"),
            artist_bootstrap(risk_test, rng, "h12_action=confidence_only_or_manual_review"),
        ],
        ignore_index=True,
    )
    bootstrap_summary = summarize_bootstrap(bootstrap)

    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    metrics.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    bootstrap.to_csv(exp_dir / "outputs" / "bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(exp_dir / "outputs" / "bootstrap_summary.csv", index=False)
    metrics.to_csv(BASE_EXP_DIR / "PP-H27_search_candidate_stability_summary_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "predictions": str(PRED_PATH.relative_to(REPO)),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "seed": SEED,
        "candidates": ", ".join(CANDIDATES.keys()),
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps({
        "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
        "bootstrap_samples": str((exp_dir / "outputs" / "bootstrap_samples.csv").relative_to(REPO)),
        "bootstrap_summary": str((exp_dir / "outputs" / "bootstrap_summary.csv").relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, bootstrap_summary, config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "summary": str((BASE_EXP_DIR / "PP-H27_search_candidate_stability_summary_metrics.csv").relative_to(REPO)),
        "bootstrap_summary": str((exp_dir / "outputs" / "bootstrap_summary.csv").relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
