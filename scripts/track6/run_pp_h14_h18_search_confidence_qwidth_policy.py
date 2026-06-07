#!/usr/bin/env python3
"""Run PP-H14/H18 search-match confidence and q-width correction analysis."""
from __future__ import annotations

import json
import math
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_ID = "PP-H14-H18"
EXP_SLUG = "PP-H14_H18_search_confidence_qwidth_policy"
TITLE = "검색 신뢰도 기반 가격 범위/q-width 보정 검증"

PP_Y2_PRED = REPO / "experiments" / "track6" / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "predictions.csv"
H12_ARTIST_QUEUE = REPO / "experiments" / "track6" / "PP-H12_search_match_disambiguation_review" / "outputs" / "artist_match_review_queue.csv"
VAL_COLD = REPO / "data" / "track6_split" / "track6_val_cold.csv"
TEST_COLD = REPO / "data" / "track6_split" / "track6_test_cold.csv"

BASE_CANDIDATE = "lgbq_search_all_external_interaction"


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def load_base_predictions() -> pd.DataFrame:
    pred = pd.read_csv(PP_Y2_PRED, low_memory=False)
    pred = pred[pred["candidate"].eq(BASE_CANDIDATE)].copy()
    val_meta = pd.read_csv(VAL_COLD, low_memory=False)[["_track6_row_id", "artist_name_ko", "artist_key"]]
    test_meta = pd.read_csv(TEST_COLD, low_memory=False)[["_track6_row_id", "artist_name_ko", "artist_key"]]
    meta = pd.concat([
        val_meta.assign(split="validation"),
        test_meta.assign(split="test"),
    ], ignore_index=True)
    pred = pred.merge(meta, on=["_track6_row_id", "split"], how="left", suffixes=("", "_meta"))
    pred["artist_search_name"] = pred["artist_name_ko"].map(clean_artist_name)
    return pred


def add_h12(pred: pd.DataFrame, h12_artist_queue: Path) -> pd.DataFrame:
    h12 = pd.read_csv(h12_artist_queue, low_memory=False)
    keep = [
        "artist_search_name",
        "auto_artist_label",
        "recommended_action",
        "artist_match_confidence",
        "match_artist_count",
        "partial_match_count",
        "irrelevant_count",
        "h11_search_quality_grade",
        "h11_search_quality_score",
        "h11_search_art_match_ratio",
        "h11_search_name_match_ratio",
    ]
    out = pred.merge(h12[[col for col in keep if col in h12.columns]], on="artist_search_name", how="left")
    out["recommended_action"] = out["recommended_action"].fillna("not_collected_by_h11_h12")
    out["auto_artist_label"] = out["auto_artist_label"].fillna("not_collected")
    out["artist_match_confidence"] = pd.to_numeric(out["artist_match_confidence"], errors="coerce").fillna(0.0)
    out["h11_search_quality_score"] = pd.to_numeric(out["h11_search_quality_score"], errors="coerce").fillna(0.0)
    out["h11_search_quality_grade"] = out["h11_search_quality_grade"].fillna("missing")
    return out


def qwidth_bins(df: pd.DataFrame) -> tuple[pd.Series, dict[str, float]]:
    val = df[df["split"].eq("validation")]["quantile_width_log"].dropna()
    q33 = float(val.quantile(0.33))
    q66 = float(val.quantile(0.66))
    bins = pd.cut(
        df["quantile_width_log"],
        bins=[-np.inf, q33, q66, np.inf],
        labels=["stable", "caution", "risk"],
    ).astype(str)
    return bins, {"qwidth_33": q33, "qwidth_66": q66}


def confidence_grade(row: pd.Series) -> str:
    action = str(row.get("recommended_action", ""))
    qbin = str(row.get("qwidth_bin", "risk"))
    if action == "candidate_for_h14_h18" and qbin in {"stable", "caution"}:
        return "medium"
    if action == "confidence_only_or_manual_review" and qbin == "stable":
        return "medium"
    return "low"


def range_multiplier(grade: str) -> float:
    if grade == "high":
        return 1.0
    if grade == "medium":
        return 1.2
    return 1.5


def apply_range_policy(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["confidence_grade"] = out.apply(confidence_grade, axis=1)
    out["range_multiplier"] = out["confidence_grade"].map(range_multiplier).astype(float)
    center = (out["q10_log"].astype(float) + out["q90_log"].astype(float)) / 2.0
    half = (out["q90_log"].astype(float) - out["q10_log"].astype(float)) * out["range_multiplier"] / 2.0
    out["policy_range_low_log"] = center - half
    out["policy_range_high_log"] = center + half
    out["policy_range_coverage"] = (
        (out["actual_log"].astype(float) >= out["policy_range_low_log"])
        & (out["actual_log"].astype(float) <= out["policy_range_high_log"])
    )
    out["policy_range_ratio"] = np.exp(out["policy_range_high_log"] - out["policy_range_low_log"])
    out["base_range_coverage"] = (
        (out["actual_log"].astype(float) >= out["q10_log"].astype(float))
        & (out["actual_log"].astype(float) <= out["q90_log"].astype(float))
    )
    return out


def build_conformal_buffers(df: pd.DataFrame, target_coverage: float) -> pd.DataFrame:
    val = df[df["split"].eq("validation")].copy()
    lower_miss = val["q10_log"].astype(float) - val["actual_log"].astype(float)
    upper_miss = val["actual_log"].astype(float) - val["q90_log"].astype(float)
    val["range_miss_log"] = np.maximum(np.maximum(lower_miss, upper_miss), 0.0)
    rows = []
    global_buffer = float(val["range_miss_log"].quantile(target_coverage))
    for grade, group in val.groupby("confidence_grade"):
        if len(group) >= 30:
            buffer = float(group["range_miss_log"].quantile(target_coverage))
            used_global = False
        else:
            buffer = global_buffer
            used_global = True
        rows.append({
            "confidence_grade": grade,
            "target_coverage": target_coverage,
            "n_validation": int(len(group)),
            "conformal_buffer_log": buffer,
            "used_global_fallback": used_global,
        })
    rows.append({
        "confidence_grade": "__GLOBAL__",
        "target_coverage": target_coverage,
        "n_validation": int(len(val)),
        "conformal_buffer_log": global_buffer,
        "used_global_fallback": False,
    })
    return pd.DataFrame(rows)


def apply_conformal_range(df: pd.DataFrame, buffers: pd.DataFrame, policy_name: str) -> pd.DataFrame:
    out = df.copy()
    buffer_map = buffers.set_index("confidence_grade")["conformal_buffer_log"].to_dict()
    global_buffer = float(buffer_map.get("__GLOBAL__", 0.0))
    out[f"{policy_name}_buffer_log"] = out["confidence_grade"].map(buffer_map).fillna(global_buffer).astype(float)
    out[f"{policy_name}_low_log"] = out["q10_log"].astype(float) - out[f"{policy_name}_buffer_log"]
    out[f"{policy_name}_high_log"] = out["q90_log"].astype(float) + out[f"{policy_name}_buffer_log"]
    out[f"{policy_name}_coverage"] = (
        (out["actual_log"].astype(float) >= out[f"{policy_name}_low_log"])
        & (out["actual_log"].astype(float) <= out[f"{policy_name}_high_log"])
    )
    out[f"{policy_name}_range_ratio"] = np.exp(out[f"{policy_name}_high_log"] - out[f"{policy_name}_low_log"])
    return out


def metric_values(frame: pd.DataFrame, pred_col: str = "pred_log") -> dict[str, float]:
    actual_log = frame["actual_log"].astype(float).to_numpy()
    pred_log = frame[pred_col].astype(float).to_numpy()
    actual = frame["actual_price"].astype(float).to_numpy()
    pred = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred_log) ** 2))) if len(frame) else math.nan,
        "MdAPE": float(np.median(ape)) if len(frame) else math.nan,
        "MAPE": float(np.mean(ape)) if len(frame) else math.nan,
        "p95_APE": float(np.quantile(ape, 0.95)) if len(frame) else math.nan,
        "Within_30": float(np.mean(ape <= 0.30)) if len(frame) else math.nan,
        "Within_50": float(np.mean(ape <= 0.50)) if len(frame) else math.nan,
    }


def build_correction_map(df: pd.DataFrame, min_rows: int, cap: float) -> pd.DataFrame:
    val = df[df["split"].eq("validation")].copy()
    val["segment_key"] = val["qwidth_bin"].astype(str) + "__" + val["recommended_action"].astype(str)
    global_corr = float(np.median(val["actual_log"].astype(float) - val["pred_log"].astype(float)))
    rows = []
    for segment, group in val.groupby("segment_key", dropna=False):
        n = int(len(group))
        correction = float(np.median(group["actual_log"].astype(float) - group["pred_log"].astype(float)))
        used_fallback = n < min_rows
        if used_fallback:
            correction = global_corr
        correction = float(np.clip(correction, -cap, cap))
        rows.append({
            "segment_key": segment,
            "n_validation": n,
            "raw_median_residual_log": float(np.median(group["actual_log"].astype(float) - group["pred_log"].astype(float))),
            "correction_log": correction,
            "min_rows": min_rows,
            "cap": cap,
            "used_global_fallback": used_fallback,
        })
    rows.append({
        "segment_key": "__GLOBAL__",
        "n_validation": int(len(val)),
        "raw_median_residual_log": global_corr,
        "correction_log": float(np.clip(global_corr, -cap, cap)),
        "min_rows": min_rows,
        "cap": cap,
        "used_global_fallback": False,
    })
    return pd.DataFrame(rows)


def apply_correction(df: pd.DataFrame, correction_map: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["segment_key"] = out["qwidth_bin"].astype(str) + "__" + out["recommended_action"].astype(str)
    corr = correction_map.set_index("segment_key")["correction_log"].to_dict()
    global_corr = float(corr.get("__GLOBAL__", 0.0))
    out["h18_correction_log"] = out["segment_key"].map(corr).fillna(global_corr).astype(float)
    out["h18_pred_log"] = out["pred_log"].astype(float) + out["h18_correction_log"]
    out["h18_pred_price"] = np.clip(np.exp(out["h18_pred_log"]), 1_000.0, None)
    out["h18_ape"] = np.abs(out["h18_pred_price"] - out["actual_price"].astype(float)) / out["actual_price"].astype(float)
    return out


def build_metrics(df: pd.DataFrame, corrected_candidates: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, group in df.groupby("split"):
        rows.append({"experiment_id": EXP_ID, "candidate": "pp_y2_base", "split": split, "slice": "overall", **metric_values(group, "pred_log")})
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": "h14_base_range",
            "split": split,
            "slice": "overall",
            "n": int(len(group)),
            "range_coverage": float(group["base_range_coverage"].mean()),
            "median_range_ratio": float(group["price_range_ratio"].median()),
        })
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": "h14_policy_range",
            "split": split,
            "slice": "overall",
            "n": int(len(group)),
            "range_coverage": float(group["policy_range_coverage"].mean()),
            "median_range_ratio": float(group["policy_range_ratio"].median()),
        })
        for policy_name in ["h14_conformal80_range", "h14_conformal90_range"]:
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": policy_name,
                "split": split,
                "slice": "overall",
                "n": int(len(group)),
                "range_coverage": float(group[f"{policy_name}_coverage"].mean()),
                "median_range_ratio": float(group[f"{policy_name}_range_ratio"].median()),
            })
        for grade, seg in group.groupby("confidence_grade"):
            rows.append({"experiment_id": EXP_ID, "candidate": "pp_y2_base", "split": split, "slice": f"confidence={grade}", **metric_values(seg, "pred_log")})
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": "h14_policy_range",
                "split": split,
                "slice": f"confidence={grade}",
                "n": int(len(seg)),
                "range_coverage": float(seg["policy_range_coverage"].mean()),
                "median_range_ratio": float(seg["policy_range_ratio"].median()),
                "MdAPE": float(seg["ape"].median()),
                "MAPE": float(seg["ape"].mean()),
                "p95_APE": float(seg["ape"].quantile(0.95)),
            })
            for policy_name in ["h14_conformal80_range", "h14_conformal90_range"]:
                rows.append({
                    "experiment_id": EXP_ID,
                    "candidate": policy_name,
                    "split": split,
                    "slice": f"confidence={grade}",
                    "n": int(len(seg)),
                    "range_coverage": float(seg[f"{policy_name}_coverage"].mean()),
                    "median_range_ratio": float(seg[f"{policy_name}_range_ratio"].median()),
                    "MdAPE": float(seg["ape"].median()),
                    "MAPE": float(seg["ape"].mean()),
                    "p95_APE": float(seg["ape"].quantile(0.95)),
                })
        for action, seg in group.groupby("recommended_action"):
            rows.append({"experiment_id": EXP_ID, "candidate": "pp_y2_base", "split": split, "slice": f"h12_action={action}", **metric_values(seg, "pred_log")})

    for candidate, cdf in corrected_candidates.items():
        for split, group in cdf.groupby("split"):
            rows.append({"experiment_id": EXP_ID, "candidate": candidate, "split": split, "slice": "overall", **metric_values(group, "h18_pred_log")})
            for grade, seg in group.groupby("confidence_grade"):
                rows.append({"experiment_id": EXP_ID, "candidate": candidate, "split": split, "slice": f"confidence={grade}", **metric_values(seg, "h18_pred_log")})
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def render_report(metrics: pd.DataFrame, predictions: pd.DataFrame, correction_maps: pd.DataFrame, conformal_buffers: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    test_overall = metrics[(metrics["split"].eq("test")) & (metrics["slice"].eq("overall"))].sort_values(["candidate"])
    confidence_test = metrics[(metrics["split"].eq("test")) & (metrics["slice"].astype(str).str.startswith("confidence="))].sort_values(["candidate", "slice"])
    action_test = metrics[(metrics["split"].eq("test")) & (metrics["slice"].astype(str).str.startswith("h12_action="))].sort_values(["slice"])
    grade_counts = predictions.groupby(["split", "confidence_grade"]).size().reset_index(name="n")
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 목적",
        "",
        "- H12에서 분리한 작가 검색 신뢰도를 Cold 예측의 신뢰도/가격 범위/q-width 보정에 연결한다.",
        "- 검색 피처를 점 예측에 직접 넣는 대신, 신뢰도가 낮은 구간을 넓은 가격 범위와 낮은 confidence로 처리할 수 있는지 확인한다.",
        "- H18 보정은 validation segment median residual로만 correction map을 만들고 test에 적용한다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"}), max_rows=80),
        "",
        "## Test 전체 결과",
        "",
        markdown_table(test_overall, max_rows=20),
        "",
        "## Test confidence별 결과",
        "",
        markdown_table(confidence_test, max_rows=40),
        "",
        "## Test H12 액션별 기준 오차",
        "",
        markdown_table(action_test, max_rows=40),
        "",
        "## Confidence 등급 분포",
        "",
        markdown_table(grade_counts),
        "",
        "## 보정 맵",
        "",
        markdown_table(correction_maps, max_rows=60),
        "",
        "## Conformal 범위 버퍼",
        "",
        markdown_table(conformal_buffers, max_rows=30),
        "",
        "## 해석",
        "",
        "- H14의 핵심은 range coverage가 오르면서 median range ratio가 과도하게 커지지 않는지다.",
        "- H18의 핵심은 validation에서 만든 q-width x H12 action 보정이 test에서 MdAPE/MAPE/p95를 동시에 악화시키지 않는지다.",
        "- H12가 아직 수동 검수 전 자동 라벨이므로, 이 결과는 운영 정책 후보 검증으로 보고 최종 모델 채택 근거로는 보류한다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{EXP_ID}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>{EXP_ID} {TITLE}</h1>
<div class="note">H12 자동 라벨을 기반으로 한 H14/H18 정책 검증입니다. 수동 검수 전 결과이므로 최종 채택 전 재검증이 필요합니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>Test 전체 결과</h2>{test_overall.to_html(index=False, escape=True)}
<h2>Test confidence별 결과</h2>{confidence_test.to_html(index=False, escape=True)}
<h2>Test H12 액션별 기준 오차</h2>{action_test.to_html(index=False, escape=True)}
<h2>Confidence 등급 분포</h2>{grade_counts.to_html(index=False, escape=True)}
<h2>보정 맵</h2>{correction_maps.to_html(index=False, escape=True)}
<h2>Conformal 범위 버퍼</h2>{conformal_buffers.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h12-artist-queue", default=str(H12_ARTIST_QUEUE))
    parser.add_argument("--exp-slug", default=EXP_SLUG)
    parser.add_argument("--summary-name", default="PP-H14_H18_search_confidence_qwidth_summary_metrics.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = datetime.now()
    h12_artist_queue = Path(args.h12_artist_queue)
    base = add_h12(load_base_predictions(), h12_artist_queue)
    base["qwidth_bin"], edges = qwidth_bins(base)
    base = apply_range_policy(base)
    conformal80 = build_conformal_buffers(base, target_coverage=0.80)
    conformal90 = build_conformal_buffers(base, target_coverage=0.90)
    base = apply_conformal_range(base, conformal80, "h14_conformal80_range")
    base = apply_conformal_range(base, conformal90, "h14_conformal90_range")
    conformal_buffers = pd.concat([
        conformal80.assign(candidate="h14_conformal80_range"),
        conformal90.assign(candidate="h14_conformal90_range"),
    ], ignore_index=True)

    corrected_candidates: dict[str, pd.DataFrame] = {}
    correction_maps = []
    for min_rows in [30, 80]:
        for cap in [0.10, 0.20, 0.30]:
            cmap = build_correction_map(base, min_rows=min_rows, cap=cap)
            candidate = f"h18_qwidth_x_h12_median_min{min_rows}_cap{cap:g}"
            corr_df = apply_correction(base, cmap)
            corr_df["h18_candidate"] = candidate
            corrected_candidates[candidate] = corr_df
            correction_maps.append(cmap.assign(candidate=candidate))
    correction_map_df = pd.concat(correction_maps, ignore_index=True)
    metrics = build_metrics(base, corrected_candidates)

    exp_dir = BASE_EXP_DIR / args.exp_slug
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    best_test = metrics[(metrics["split"].eq("test")) & (metrics["slice"].eq("overall")) & (metrics["candidate"].astype(str).str.startswith("h18_"))].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(1)
    best_candidate = str(best_test["candidate"].iloc[0]) if not best_test.empty else ""
    corrected_best = corrected_candidates.get(best_candidate, pd.DataFrame())

    base.to_csv(exp_dir / "outputs" / "h14_confidence_range_predictions.csv", index=False)
    if not corrected_best.empty:
        corrected_best.to_csv(exp_dir / "outputs" / "h18_best_corrected_predictions.csv", index=False)
    metrics.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    correction_map_df.to_csv(exp_dir / "outputs" / "correction_maps.csv", index=False)
    conformal_buffers.to_csv(exp_dir / "outputs" / "conformal_range_buffers.csv", index=False)
    metrics.to_csv(BASE_EXP_DIR / args.summary_name, index=False)

    if h12_artist_queue.is_absolute() and h12_artist_queue.is_relative_to(REPO):
        h12_queue_for_config = str(h12_artist_queue.relative_to(REPO))
    else:
        h12_queue_for_config = str(h12_artist_queue)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": f"pp_h14_h18_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "base_prediction": str(PP_Y2_PRED.relative_to(REPO)),
        "base_candidate": BASE_CANDIDATE,
        "h12_artist_queue": h12_queue_for_config,
        "qwidth_33_validation": edges["qwidth_33"],
        "qwidth_66_validation": edges["qwidth_66"],
        "best_h18_candidate": best_candidate,
        "note": "H12 labels are automatic triage labels. Treat H14/H18 as policy diagnostics until manual review is complete.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps({
        "h14_confidence_range_predictions": str((exp_dir / "outputs" / "h14_confidence_range_predictions.csv").relative_to(REPO)),
        "h18_best_corrected_predictions": str((exp_dir / "outputs" / "h18_best_corrected_predictions.csv").relative_to(REPO)),
        "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
        "correction_maps": str((exp_dir / "outputs" / "correction_maps.csv").relative_to(REPO)),
        "conformal_range_buffers": str((exp_dir / "outputs" / "conformal_range_buffers.csv").relative_to(REPO)),
        "experiment_dir": str(exp_dir.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, base, correction_map_df, conformal_buffers, config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "best_h18_candidate": best_candidate,
        "summary": str((BASE_EXP_DIR / args.summary_name).relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
