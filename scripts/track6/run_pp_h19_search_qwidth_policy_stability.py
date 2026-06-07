#!/usr/bin/env python3
"""Run PP-H19 stability checks for H12B/H18 search q-width correction policies."""
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
EXP_ID = "PP-H19"
EXP_SLUG = "PP-H19_search_qwidth_policy_stability"
TITLE = "검색 신뢰도 x 예측 불확실성 보정 안정성 검증"

H14_H18_H12B_DIR = BASE_EXP_DIR / "PP-H14_H18_search_confidence_qwidth_policy_h12b"
BASE_PRED_PATH = H14_H18_H12B_DIR / "outputs" / "h14_confidence_range_predictions.csv"
CORRECTION_MAP_PATH = H14_H18_H12B_DIR / "outputs" / "correction_maps.csv"

BOOTSTRAP_ITERATIONS = 600
SEED = 20260603
PRIMARY_CANDIDATES = [
    "h18_qwidth_x_h12_median_min30_cap0.1",
    "h18_qwidth_x_h12_median_min30_cap0.2",
    "h18_qwidth_x_h12_median_min80_cap0.1",
    "h18_qwidth_x_h12_median_min80_cap0.2",
]


def metric_values(frame: pd.DataFrame, pred_col: str) -> dict[str, float]:
    actual_log = frame["actual_log"].astype(float).to_numpy()
    pred_log = frame[pred_col].astype(float).to_numpy()
    actual = frame["actual_price"].astype(float).to_numpy()
    pred = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    if len(frame) == 0:
        return {
            "n": 0,
            "MdAPE": math.nan,
            "MAPE": math.nan,
            "p95_APE": math.nan,
            "RMSE_log": math.nan,
            "Within_30": math.nan,
            "Within_50": math.nan,
        }
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def apply_candidate(base: pd.DataFrame, correction_maps: pd.DataFrame, candidate: str) -> pd.DataFrame:
    cmap = correction_maps[correction_maps["candidate"].eq(candidate)].copy()
    if cmap.empty:
        raise ValueError(f"correction map not found for candidate={candidate}")

    out = base.copy()
    out["segment_key"] = out["qwidth_bin"].astype(str) + "__" + out["recommended_action"].astype(str)
    correction_by_segment = cmap.set_index("segment_key")["correction_log"].to_dict()
    global_correction = float(correction_by_segment.get("__GLOBAL__", 0.0))
    out[f"{candidate}__correction_log"] = (
        out["segment_key"].map(correction_by_segment).fillna(global_correction).astype(float)
    )
    out[f"{candidate}__pred_log"] = out["pred_log"].astype(float) + out[f"{candidate}__correction_log"]
    return out


def build_predictions(base: pd.DataFrame, correction_maps: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    out = base.copy()
    for candidate in candidates:
        corrected = apply_candidate(base, correction_maps, candidate)
        out[f"{candidate}__correction_log"] = corrected[f"{candidate}__correction_log"]
        out[f"{candidate}__pred_log"] = corrected[f"{candidate}__pred_log"]
    return out


def build_point_metrics(pred: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, group in pred.groupby("split", dropna=False):
        rows.append({
            "experiment_id": EXP_ID,
            "split": split,
            "slice": "overall",
            "candidate": "pp_y2_base",
            **metric_values(group, "pred_log"),
        })
        for candidate in candidates:
            rows.append({
                "experiment_id": EXP_ID,
                "split": split,
                "slice": "overall",
                "candidate": candidate,
                **metric_values(group, f"{candidate}__pred_log"),
            })

        for action, seg in group.groupby("recommended_action", dropna=False):
            rows.append({
                "experiment_id": EXP_ID,
                "split": split,
                "slice": f"h12_action={action}",
                "candidate": "pp_y2_base",
                **metric_values(seg, "pred_log"),
            })
            for candidate in candidates:
                rows.append({
                    "experiment_id": EXP_ID,
                    "split": split,
                    "slice": f"h12_action={action}",
                    "candidate": candidate,
                    **metric_values(seg, f"{candidate}__pred_log"),
                })
    return pd.DataFrame(rows)


def metric_delta(base_metrics: dict[str, float], candidate_metrics: dict[str, float]) -> dict[str, float]:
    return {
        "delta_MdAPE": base_metrics["MdAPE"] - candidate_metrics["MdAPE"],
        "delta_MAPE": base_metrics["MAPE"] - candidate_metrics["MAPE"],
        "delta_p95_APE": base_metrics["p95_APE"] - candidate_metrics["p95_APE"],
        "delta_RMSE_log": base_metrics["RMSE_log"] - candidate_metrics["RMSE_log"],
        "delta_Within_30": candidate_metrics["Within_30"] - base_metrics["Within_30"],
        "delta_Within_50": candidate_metrics["Within_50"] - base_metrics["Within_50"],
    }


def row_bootstrap(test: pd.DataFrame, candidates: list[str], rng: np.random.Generator) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    n = len(test)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        idx = rng.integers(0, n, size=n)
        sample = test.iloc[idx]
        base_metrics = metric_values(sample, "pred_log")
        for candidate in candidates:
            cand_metrics = metric_values(sample, f"{candidate}__pred_log")
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": "row",
                "iteration": iteration,
                "candidate": candidate,
                **metric_delta(base_metrics, cand_metrics),
            })
    return pd.DataFrame(rows)


def artist_bootstrap(test: pd.DataFrame, candidates: list[str], rng: np.random.Generator) -> pd.DataFrame:
    artist_col = "artist_key" if "artist_key" in test.columns else "artist_search_name"
    artist_values = test[artist_col].fillna("__MISSING_ARTIST__").astype(str)
    groups = {
        artist: group.copy()
        for artist, group in test.assign(_bootstrap_artist=artist_values).groupby("_bootstrap_artist", dropna=False)
    }
    artists = np.array(list(groups.keys()), dtype=object)
    rows: list[dict[str, Any]] = []
    for iteration in range(BOOTSTRAP_ITERATIONS):
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        sample = pd.concat([groups[artist] for artist in sampled_artists], ignore_index=True)
        base_metrics = metric_values(sample, "pred_log")
        for candidate in candidates:
            cand_metrics = metric_values(sample, f"{candidate}__pred_log")
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": "artist",
                "iteration": iteration,
                "candidate": candidate,
                **metric_delta(base_metrics, cand_metrics),
            })
    return pd.DataFrame(rows)


def summarize_bootstrap(boot: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "delta_RMSE_log",
        "delta_Within_30",
        "delta_Within_50",
    ]
    rows: list[dict[str, Any]] = []
    for (bootstrap_type, candidate), group in boot.groupby(["bootstrap_type", "candidate"], dropna=False):
        for metric in metric_cols:
            values = group[metric].astype(float).dropna().to_numpy()
            rows.append({
                "experiment_id": EXP_ID,
                "bootstrap_type": bootstrap_type,
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


def markdown_table(df: pd.DataFrame, max_rows: int = 60) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def render_report(
    metrics: pd.DataFrame,
    summary: pd.DataFrame,
    candidates: list[str],
    config: dict[str, Any],
) -> tuple[str, str]:
    test_overall = metrics[metrics["split"].eq("test") & metrics["slice"].eq("overall")].copy()
    bootstrap_focus = summary[summary["metric"].isin(["delta_MdAPE", "delta_MAPE", "delta_p95_APE", "delta_RMSE_log"])].copy()
    test_overall = test_overall.sort_values(["MdAPE", "MAPE"], na_position="last")
    bootstrap_focus = bootstrap_focus.sort_values(["candidate", "bootstrap_type", "metric"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- H12B 보수 라벨 기반 H18 보정 후보가 test 단일 결과에서만 좋아진 것인지, 표본을 다시 뽑아도 개선 방향이 유지되는지 확인한다.",
        "- row bootstrap은 개별 작품 단위의 흔들림을 본다.",
        "- artist bootstrap은 작가 단위로 다시 뽑았을 때 특정 작가 몇 명 때문에 좋아진 결과인지 확인한다.",
        "- delta 값은 `기준 모델 점수 - 후보 점수`다. MdAPE, MAPE, p95_APE, RMSE_log는 양수일수록 보정 후보가 더 좋다는 뜻이다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"}), max_rows=80),
        "",
        "## Test 전체 점수",
        "",
        markdown_table(test_overall),
        "",
        "## Bootstrap 안정성 요약",
        "",
        markdown_table(bootstrap_focus, max_rows=80),
        "",
        "## 후보 해석",
        "",
        "- `min80_cap0.2`: segment 표본 수 기준을 보수적으로 두고 보정 강도를 0.2 로그포인트까지 허용한 후보다. MdAPE 중심으로는 가장 좋지만, MAPE/RMSE에서는 덜 안정적일 수 있다.",
        "- `min30_cap0.2`: 더 세분화된 segment 보정을 허용한 후보다. MdAPE 개선 폭은 조금 작지만 MAPE/RMSE까지 함께 낮추는 균형 후보로 볼 수 있다.",
        "- bootstrap에서 artist 기준 개선 확률이 낮으면 특정 작가 구성에 민감하다는 뜻이므로 운영 적용 전 수동 검수 또는 보정 강도 축소가 필요하다.",
        "",
        "## 검증 후보",
        "",
        "\n".join(f"- `{candidate}`" for candidate in candidates),
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{EXP_ID}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>{EXP_ID} {TITLE}</h1>
<div class="note">delta는 기준 모델 점수에서 보정 후보 점수를 뺀 값입니다. 오차 지표에서는 양수일수록 보정 후보가 좋습니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>Test 전체 점수</h2>{test_overall.to_html(index=False, escape=True)}
<h2>Bootstrap 안정성 요약</h2>{bootstrap_focus.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = datetime.now()
    base = pd.read_csv(BASE_PRED_PATH, low_memory=False)
    correction_maps = pd.read_csv(CORRECTION_MAP_PATH, low_memory=False)
    available = set(correction_maps["candidate"].dropna().astype(str))
    candidates = [candidate for candidate in PRIMARY_CANDIDATES if candidate in available]
    if not candidates:
        raise ValueError("No configured candidates found in correction map.")

    pred = build_predictions(base, correction_maps, candidates)
    metrics = build_point_metrics(pred, candidates)
    test = pred[pred["split"].eq("test")].copy()
    if test.empty:
        raise ValueError("No test rows found.")

    rng = np.random.default_rng(SEED)
    row_boot = row_bootstrap(test, candidates, rng)
    artist_boot = artist_bootstrap(test, candidates, rng)
    bootstrap = pd.concat([row_boot, artist_boot], ignore_index=True)
    bootstrap_summary = summarize_bootstrap(bootstrap)

    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    metrics.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred.to_csv(exp_dir / "outputs" / "candidate_predictions.csv", index=False)
    bootstrap.to_csv(exp_dir / "outputs" / "bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(exp_dir / "outputs" / "bootstrap_summary.csv", index=False)
    metrics.to_csv(BASE_EXP_DIR / "PP-H19_search_qwidth_policy_stability_summary_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "base_predictions": str(BASE_PRED_PATH.relative_to(REPO)),
        "correction_maps": str(CORRECTION_MAP_PATH.relative_to(REPO)),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "seed": SEED,
        "candidates": ", ".join(candidates),
        "note": "H12B conservative automatic labels are used. This checks stability, not final production readiness.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps({
        "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
        "candidate_predictions": str((exp_dir / "outputs" / "candidate_predictions.csv").relative_to(REPO)),
        "bootstrap_samples": str((exp_dir / "outputs" / "bootstrap_samples.csv").relative_to(REPO)),
        "bootstrap_summary": str((exp_dir / "outputs" / "bootstrap_summary.csv").relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, bootstrap_summary, candidates, config)
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
        "summary": str((BASE_EXP_DIR / "PP-H19_search_qwidth_policy_stability_summary_metrics.csv").relative_to(REPO)),
        "bootstrap_summary": str((exp_dir / "outputs" / "bootstrap_summary.csv").relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
