#!/usr/bin/env python3
"""Run PP-H20~H26 search feature expansion checks.

This script separates API-dependent experiments from experiments that can be
run with the current PP-H11/H12B/H14/H18 artifacts.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
EXP_SLUG = "PP-H20_H26_search_feature_expansion"
TITLE = "검색 피처 보완 실험"

BASE_PRED_PATH = (
    BASE_EXP_DIR
    / "PP-H14_H18_search_confidence_qwidth_policy_h12b"
    / "outputs"
    / "h14_confidence_range_predictions.csv"
)
STANDARDIZED_SEARCH_PATH = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_standardized_latest.csv"
)
SNAPSHOT_PATH = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_snapshot_latest.csv"
)

SOURCE_GROUPS = ["gallery_museum", "art_general", "exhibition", "market", "news", "social_blog", "other"]
CAPS = [0.10, 0.20]
MIN_ROWS = 30


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


def build_api_preflight() -> pd.DataFrame:
    collected_providers: set[str] = set()
    successful_providers: set[str] = set()
    if STANDARDIZED_SEARCH_PATH.exists():
        try:
            standard = pd.read_csv(STANDARDIZED_SEARCH_PATH, usecols=["provider", "has_result"], low_memory=False)
            collected_providers = set(standard["provider"].dropna().astype(str).unique())
            successful = standard[standard["has_result"].fillna(False).astype(bool)]
            successful_providers = set(successful["provider"].dropna().astype(str).unique())
        except Exception:
            collected_providers = set()
            successful_providers = set()
    has_naver_official = {"naver_api_blog", "naver_api_news", "naver_api_webkr"}.issubset(collected_providers)
    has_google = any(provider.startswith("google") for provider in successful_providers)
    has_python_search = any(provider.startswith("python_") or provider == "duckduckgo_html" for provider in successful_providers)
    has_secondary_provider = has_google or has_python_search
    secondary_provider_label = "Python 검색 라이브러리" if has_python_search else "Google"
    checks = [
        {
            "experiment_id": "PP-H20",
            "candidate": "naver_official_api_multi_source",
            "status": "completed_latest_snapshot" if has_naver_official else "ready" if (
                os.getenv("NAVER_CLIENT_ID") or os.getenv("NAVER_SEARCH_CLIENT_ID")
            ) and (
                os.getenv("NAVER_CLIENT_SECRET") or os.getenv("NAVER_SEARCH_CLIENT_SECRET")
            ) else "blocked_missing_credentials",
            "required": "NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 또는 NAVER_SEARCH_CLIENT_ID/NAVER_SEARCH_CLIENT_SECRET",
            "next_action": "완료된 최신 snapshot 사용" if has_naver_official else "Naver 공식 검색 API 키 주입 후 blog/news/webkr provider 재수집",
        },
        {
            "experiment_id": "PP-H21",
            "candidate": "secondary_global_search_collection",
            "status": "completed_python_latest_snapshot" if has_python_search else "completed_google_latest_snapshot" if has_google else "ready" if os.getenv("GOOGLE_API_KEY") and (
                os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
            ) else "ready_python_provider",
            "required": "python_ddg/python_ddg_art_domains 또는 GOOGLE_API_KEY + GOOGLE_CSE_ID",
            "next_action": "완료된 Python 검색 snapshot 사용" if has_python_search else "완료된 Google snapshot 사용" if has_google else "Python 검색 라이브러리 provider 우선 수집",
        },
        {
            "experiment_id": "PP-H22",
            "candidate": "provider_agreement_stability",
            "status": "ready" if has_naver_official and has_secondary_provider else "ready_collect_python_provider" if has_naver_official else "blocked_single_provider",
            "required": "최소 2개 provider의 동일 작가/동일 템플릿 수집 결과",
            "next_action": f"Naver x {secondary_provider_label} agreement score 계산" if has_naver_official and has_secondary_provider else "Python 검색 provider 수집 후 Naver x Python agreement score 계산",
        },
    ]
    return pd.DataFrame(checks)


def build_source_features() -> pd.DataFrame:
    standard = pd.read_csv(STANDARDIZED_SEARCH_PATH, low_memory=False)
    standard = standard[standard["has_result"].fillna(False).astype(bool)].copy()
    source_counts = (
        standard.groupby(["artist_search_name", "source_group"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for group in SOURCE_GROUPS:
        if group not in source_counts.columns:
            source_counts[group] = 0
    source_counts["source_total_count"] = source_counts[SOURCE_GROUPS].sum(axis=1)
    for group in SOURCE_GROUPS:
        source_counts[f"source_group_{group}_count"] = source_counts[group].astype(float)
        source_counts[f"source_group_{group}_ratio"] = (
            source_counts[group].astype(float) / source_counts["source_total_count"].replace(0, np.nan)
        ).fillna(0.0)
    source_counts = source_counts.drop(columns=[group for group in SOURCE_GROUPS if group in source_counts.columns])

    flag_cols = [
        "is_art_context",
        "is_exhibition_context",
        "is_gallery_context",
        "is_market_context",
        "is_social_context",
        "is_homonym_context",
        "is_trusted_domain",
        "is_recent_context",
        "artist_name_in_result",
    ]
    flag_agg = standard.groupby("artist_search_name", dropna=False)[flag_cols].sum().reset_index()
    for col in flag_cols:
        flag_agg[f"{col}_ratio"] = (
            pd.to_numeric(flag_agg[col], errors="coerce").fillna(0.0)
            / source_counts.set_index("artist_search_name").loc[flag_agg["artist_search_name"], "source_total_count"].to_numpy()
        )
        flag_agg[f"{col}_ratio"] = flag_agg[f"{col}_ratio"].replace([np.inf, -np.inf], 0.0).fillna(0.0)

    snapshot = pd.read_csv(SNAPSHOT_PATH, low_memory=False)
    keep = [
        "artist_search_name",
        "search_recent_result_count",
        "search_recent_result_ratio",
        "search_quality_score",
        "search_quality_grade",
        "search_name_match_ratio",
        "search_homonym_risk_ratio",
        "provider_coverage_count",
    ]
    out = source_counts.merge(flag_agg, on="artist_search_name", how="left")
    out = out.merge(snapshot[[col for col in keep if col in snapshot.columns]], on="artist_search_name", how="left")
    numeric_cols = [col for col in out.columns if col != "artist_search_name" and out[col].dtype.kind in "biufc"]
    out[numeric_cols] = out[numeric_cols].fillna(0.0)
    return out


def attach_search_features(base: pd.DataFrame, source_features: pd.DataFrame) -> pd.DataFrame:
    out = base.merge(source_features, on="artist_search_name", how="left")
    for canonical, preferred, fallback in [
        ("search_quality_score", "search_quality_score_y", "search_quality_score_x"),
        ("search_quality_grade", "search_quality_grade_y", "search_quality_grade_x"),
        ("search_name_match_ratio", "search_name_match_ratio", "h11_search_name_match_ratio"),
    ]:
        if preferred in out.columns:
            out[canonical] = out[preferred]
        elif fallback in out.columns:
            out[canonical] = out[fallback]
    for col in source_features.columns:
        if col != "artist_search_name" and col in out.columns and out[col].dtype.kind in "biufc":
            out[col] = out[col].fillna(0.0)
    for col in ["search_quality_score", "search_name_match_ratio", "search_homonym_risk_ratio", "provider_coverage_count"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    return out


def segment_series(frame: pd.DataFrame, feature: str) -> pd.Series:
    values = pd.to_numeric(frame[feature], errors="coerce").fillna(0.0)
    val_values = values[frame["split"].eq("validation")]
    positive = val_values[val_values > 0]
    if positive.empty:
        return pd.Series("missing", index=frame.index)
    threshold = float(positive.median())
    labels = np.where(values <= 0, "none", np.where(values <= threshold, "low", "high"))
    return pd.Series(labels, index=frame.index)


def build_correction_map(
    frame: pd.DataFrame,
    segment_col: str,
    cap: float,
    experiment_id: str,
    candidate: str,
) -> pd.DataFrame:
    val = frame[frame["split"].eq("validation")].copy()
    global_corr = float(np.median(val["actual_log"].astype(float) - val["pred_log"].astype(float)))
    rows = []
    for segment, group in val.groupby(segment_col, dropna=False):
        n = int(len(group))
        raw = float(np.median(group["actual_log"].astype(float) - group["pred_log"].astype(float)))
        used_global = n < MIN_ROWS
        corr = global_corr if used_global else raw
        corr = float(np.clip(corr, -cap, cap))
        rows.append({
            "experiment_id": experiment_id,
            "candidate": candidate,
            "segment_col": segment_col,
            "segment_value": segment,
            "n_validation": n,
            "raw_median_residual_log": raw,
            "correction_log": corr,
            "cap": cap,
            "min_rows": MIN_ROWS,
            "used_global_fallback": used_global,
        })
    rows.append({
        "experiment_id": experiment_id,
        "candidate": candidate,
        "segment_col": segment_col,
        "segment_value": "__GLOBAL__",
        "n_validation": int(len(val)),
        "raw_median_residual_log": global_corr,
        "correction_log": float(np.clip(global_corr, -cap, cap)),
        "cap": cap,
        "min_rows": MIN_ROWS,
        "used_global_fallback": False,
    })
    return pd.DataFrame(rows)


def apply_correction(frame: pd.DataFrame, cmap: pd.DataFrame, segment_col: str, pred_col: str) -> pd.Series:
    corrections = cmap.set_index("segment_value")["correction_log"].to_dict()
    global_corr = float(corrections.get("__GLOBAL__", 0.0))
    return frame["pred_log"].astype(float) + frame[segment_col].map(corrections).fillna(global_corr).astype(float)


def evaluate_candidate(
    frame: pd.DataFrame,
    pred_col: str,
    experiment_id: str,
    candidate: str,
    policy: str,
    feature: str = "",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, group in frame.groupby("split", dropna=False):
        rows.append({
            "experiment_id": experiment_id,
            "candidate": candidate,
            "split": split,
            "slice": "overall",
            "policy": policy,
            "feature": feature,
            **metric_values(group, pred_col),
        })
        if "recommended_action" in group.columns:
            for action, seg in group.groupby("recommended_action", dropna=False):
                rows.append({
                    "experiment_id": experiment_id,
                    "candidate": candidate,
                    "split": split,
                    "slice": f"h12_action={action}",
                    "policy": policy,
                    "feature": feature,
                    **metric_values(seg, pred_col),
                })
    return rows


def run_h23_source_group_calibration(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    maps: list[pd.DataFrame] = []
    pred_cols = pd.DataFrame(index=frame.index)
    rows.extend(evaluate_candidate(frame, "pred_log", "PP-H23", "pp_y2_base", "base", ""))
    features = [f"source_group_{group}_ratio" for group in SOURCE_GROUPS if f"source_group_{group}_ratio" in frame.columns]
    for feature in features:
        segment_col = f"h23_segment__{feature}"
        work = frame.copy()
        work[segment_col] = segment_series(work, feature)
        for cap in CAPS:
            candidate = f"h23_{feature.replace('source_group_', '').replace('_ratio', '')}_median_cap{cap:g}"
            cmap = build_correction_map(work, segment_col, cap, "PP-H23", candidate)
            pred_col = f"{candidate}__pred_log"
            work[pred_col] = apply_correction(work, cmap, segment_col, pred_col)
            pred_cols[pred_col] = work[pred_col]
            rows.extend(evaluate_candidate(work, pred_col, "PP-H23", candidate, "source_group_segment_median", feature))
            maps.append(cmap)
    return rows, maps, pred_cols


def run_h24_recency_calibration(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    maps: list[pd.DataFrame] = []
    pred_cols = pd.DataFrame(index=frame.index)
    rows.extend(evaluate_candidate(frame, "pred_log", "PP-H24", "pp_y2_base", "base", ""))
    features = [col for col in ["search_recent_result_count", "search_recent_result_ratio", "is_recent_context_ratio"] if col in frame.columns]
    for feature in features:
        segment_col = f"h24_segment__{feature}"
        work = frame.copy()
        work[segment_col] = segment_series(work, feature)
        for cap in CAPS:
            candidate = f"h24_{feature}_median_cap{cap:g}"
            cmap = build_correction_map(work, segment_col, cap, "PP-H24", candidate)
            pred_col = f"{candidate}__pred_log"
            work[pred_col] = apply_correction(work, cmap, segment_col, pred_col)
            pred_cols[pred_col] = work[pred_col]
            rows.extend(evaluate_candidate(work, pred_col, "PP-H24", candidate, "recency_segment_median", feature))
            maps.append(cmap)
    return rows, maps, pred_cols


def run_h26_risk_fallback(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    maps: list[pd.DataFrame] = []
    pred_cols = pd.DataFrame(index=frame.index)
    rows.extend(evaluate_candidate(frame, "pred_log", "PP-H26", "pp_y2_base", "base", ""))

    risk_action = "confidence_only_or_manual_review"
    work = frame.copy()
    work["h26_action_segment"] = np.where(work["recommended_action"].eq(risk_action), risk_action, "other")
    work["h26_qwidth_action_segment"] = np.where(
        work["recommended_action"].eq(risk_action),
        work["qwidth_bin"].astype(str) + "__" + risk_action,
        "other",
    )
    for segment_col, policy_name in [
        ("h26_action_segment", "risk_action_median"),
        ("h26_qwidth_action_segment", "risk_qwidth_action_median"),
    ]:
        for cap in CAPS:
            candidate = f"h26_{policy_name}_cap{cap:g}"
            cmap = build_correction_map(work, segment_col, cap, "PP-H26", candidate)
            pred_col = f"{candidate}__pred_log"
            work[pred_col] = apply_correction(work, cmap, segment_col, pred_col)
            pred_cols[pred_col] = work[pred_col]
            rows.extend(evaluate_candidate(work, pred_col, "PP-H26", candidate, policy_name, segment_col))
            maps.append(cmap)

    for blend_target, target_col in [("lower_q10", "q10_log"), ("upper_q90", "q90_log")]:
        for weight in [0.25, 0.50]:
            candidate = f"h26_confidence_only_{blend_target}_blend{weight:g}"
            pred_col = f"{candidate}__pred_log"
            work[pred_col] = work["pred_log"].astype(float)
            mask = work["recommended_action"].eq(risk_action)
            work.loc[mask, pred_col] = (
                (1.0 - weight) * work.loc[mask, "pred_log"].astype(float)
                + weight * work.loc[mask, target_col].astype(float)
            )
            pred_cols[pred_col] = work[pred_col]
            rows.extend(evaluate_candidate(work, pred_col, "PP-H26", candidate, "risk_quantile_blend", target_col))
    return rows, maps, pred_cols


def build_h25_manual_review_priority(frame: pd.DataFrame) -> pd.DataFrame:
    val = frame[frame["split"].eq("validation")].copy()
    val["base_ape"] = np.abs(np.exp(val["pred_log"].astype(float)) - val["actual_price"].astype(float)) / np.clip(
        val["actual_price"].astype(float),
        1.0,
        None,
    )
    group = val.groupby("artist_search_name", dropna=False).agg(
        validation_rows=("base_ape", "size"),
        validation_mdape=("base_ape", "median"),
        validation_mape=("base_ape", "mean"),
        validation_p95_ape=("base_ape", lambda s: float(np.quantile(s, 0.95))),
        recommended_action=("recommended_action", lambda s: s.mode().iloc[0] if not s.mode().empty else ""),
        qwidth_bin=("qwidth_bin", lambda s: s.mode().iloc[0] if not s.mode().empty else ""),
        search_quality_score=("search_quality_score", "max"),
        search_name_match_ratio=("search_name_match_ratio", "max"),
        search_homonym_risk_ratio=("search_homonym_risk_ratio", "max"),
        source_total_count=("source_total_count", "max"),
        source_group_gallery_museum_ratio=("source_group_gallery_museum_ratio", "max"),
        source_group_market_ratio=("source_group_market_ratio", "max"),
        source_group_news_ratio=("source_group_news_ratio", "max"),
    ).reset_index()
    action_weight = group["recommended_action"].map({
        "confidence_only_or_manual_review": 3.0,
        "candidate_for_h14_h18": 2.0,
        "do_not_use_for_point_prediction": 1.5,
        "not_collected_by_h11_h12": 1.0,
    }).fillna(1.0)
    group["manual_review_priority_score"] = (
        0.40 * group["validation_p95_ape"].rank(pct=True)
        + 0.25 * group["validation_mdape"].rank(pct=True)
        + 0.20 * action_weight / 3.0
        + 0.10 * (1.0 - group["search_name_match_ratio"].clip(0.0, 1.0))
        + 0.05 * group["search_homonym_risk_ratio"].clip(0.0, 1.0)
    )
    group["review_reason"] = np.select(
        [
            group["recommended_action"].eq("confidence_only_or_manual_review"),
            group["validation_p95_ape"].ge(group["validation_p95_ape"].quantile(0.80)),
            group["search_name_match_ratio"].lt(0.30),
        ],
        [
            "검색 결과는 있으나 작가 일치 자동판정이 애매함",
            "validation 큰 오차가 커서 보정 영향이 큼",
            "작가명 매칭률이 낮아 동명이인/무관 결과 검수 필요",
        ],
        default="검색 피처 검수 후보",
    )
    return group.sort_values("manual_review_priority_score", ascending=False)


def render_report(metrics: pd.DataFrame, preflight: pd.DataFrame, review_priority: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test") & metrics["slice"].eq("overall")].copy()
    test = test.sort_values(["experiment_id", "MdAPE", "MAPE"], na_position="last")
    risk = metrics[metrics["split"].eq("test") & metrics["slice"].eq("h12_action=confidence_only_or_manual_review")].copy()
    risk = risk.sort_values(["experiment_id", "p95_APE", "MAPE"], na_position="last")
    top_review = review_priority.head(30).copy()
    lines = [
        f"# PP-H20~H26 {TITLE}",
        "",
        "## 목적",
        "",
        "- 공식 API가 필요한 검색 피처 실험과 현재 데이터로 가능한 검색 보정 실험을 분리한다.",
        "- H11의 `naver_html` 수집 결과를 사용해 소스군별/최근성/위험 구간 보정 가능성을 추가 확인한다.",
        "",
        "## 실행 설정",
        "",
        markdown_table(pd.DataFrame([config]).T.reset_index().rename(columns={"index": "항목", 0: "값"})),
        "",
        "## API Preflight",
        "",
        markdown_table(preflight),
        "",
        "## Test 전체 결과",
        "",
        markdown_table(test, max_rows=80),
        "",
        "## 위험 구간 결과",
        "",
        markdown_table(risk, max_rows=80),
        "",
        "## 수동 검수 우선순위 상위",
        "",
        markdown_table(top_review, max_rows=30),
        "",
        "## 해석",
        "",
        "- PP-H20~H22는 현재 공식 API 키 또는 2개 이상 provider 결과가 없어 blocked 상태다.",
        "- PP-H23/H24는 H11 HTML 폴백 데이터의 소스군/최근성 신호를 validation residual 보정에 사용한 제한 실험이다.",
        "- PP-H26은 H12B에서 가장 위험한 `confidence_only_or_manual_review` 구간을 별도로 방어할 수 있는지 확인한다.",
        "- 이 결과는 공식 Naver/Google 수집 후 재실행해야 최종 결론으로 사용할 수 있다.",
        "",
    ]
    md = "\n".join(lines)
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>PP-H20~H26</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}.note{{background:#f8fafc;border-left:4px solid #667085;padding:10px 12px}}</style></head>
<body><h1>PP-H20~H26 {TITLE}</h1>
<div class="note">공식 API 키가 필요한 실험은 preflight로 상태를 남기고, 현재 H11/H12B/H14 산출물로 가능한 실험을 실행했습니다.</div>
<h2>실행 설정</h2>{pd.DataFrame([config]).T.reset_index().rename(columns={'index':'항목',0:'값'}).to_html(index=False, escape=True)}
<h2>API Preflight</h2>{preflight.to_html(index=False, escape=True)}
<h2>Test 전체 결과</h2>{test.to_html(index=False, escape=True)}
<h2>위험 구간 결과</h2>{risk.to_html(index=False, escape=True)}
<h2>수동 검수 우선순위 상위</h2>{top_review.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = datetime.now()
    preflight = build_api_preflight()
    base = pd.read_csv(BASE_PRED_PATH, low_memory=False)
    source_features = build_source_features()
    frame = attach_search_features(base, source_features)

    metric_rows: list[dict[str, Any]] = []
    correction_maps: list[pd.DataFrame] = []
    prediction_cols = pd.DataFrame(index=frame.index)
    for fn in [run_h23_source_group_calibration, run_h24_recency_calibration, run_h26_risk_fallback]:
        rows, maps, preds = fn(frame)
        metric_rows.extend(rows)
        correction_maps.extend(maps)
        prediction_cols = pd.concat([prediction_cols, preds], axis=1)

    review_priority = build_h25_manual_review_priority(frame)
    h25_metrics = pd.DataFrame([
        {
            "experiment_id": "PP-H25",
            "candidate": "manual_review_priority_generation",
            "split": "validation",
            "slice": "artist",
            "policy": "manual_review_queue",
            "feature": "h12b_label_x_validation_error_x_search_source",
            "n": int(len(review_priority)),
            "MdAPE": math.nan,
            "MAPE": math.nan,
            "p95_APE": math.nan,
            "RMSE_log": math.nan,
            "Within_30": math.nan,
            "Within_50": math.nan,
        }
    ])
    metrics = pd.concat([pd.DataFrame(metric_rows), h25_metrics], ignore_index=True)

    exp_dir = BASE_EXP_DIR / EXP_SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    pred_out = pd.concat([
        frame[[
            "split",
            "_track6_row_id",
            "artist_search_name",
            "artist_key",
            "recommended_action",
            "qwidth_bin",
            "actual_log",
            "pred_log",
            "actual_price",
            "pred_price",
        ]],
        prediction_cols,
    ], axis=1)
    cmap_out = pd.concat(correction_maps, ignore_index=True) if correction_maps else pd.DataFrame()

    metrics.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    preflight.to_csv(exp_dir / "outputs" / "api_preflight.csv", index=False)
    source_features.to_csv(exp_dir / "outputs" / "source_group_features.csv", index=False)
    pred_out.to_csv(exp_dir / "outputs" / "candidate_predictions.csv", index=False)
    cmap_out.to_csv(exp_dir / "outputs" / "correction_maps.csv", index=False)
    review_priority.to_csv(exp_dir / "outputs" / "h25_manual_review_priority.csv", index=False)
    metrics.to_csv(BASE_EXP_DIR / "PP-H20_H26_search_feature_expansion_summary_metrics.csv", index=False)

    config = {
        "title": TITLE,
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "base_predictions": str(BASE_PRED_PATH.relative_to(REPO)),
        "standardized_search": str(STANDARDIZED_SEARCH_PATH.relative_to(REPO)),
        "snapshot": str(SNAPSHOT_PATH.relative_to(REPO)),
        "min_rows": MIN_ROWS,
        "caps": ", ".join(str(cap) for cap in CAPS),
        "note": "PP-H20~H22 require official API/provider data. PP-H23~H26 run on current H11 naver_html artifacts.",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "output_paths.json").write_text(json.dumps({
        "metrics": str((exp_dir / "outputs" / "metrics.csv").relative_to(REPO)),
        "api_preflight": str((exp_dir / "outputs" / "api_preflight.csv").relative_to(REPO)),
        "source_group_features": str((exp_dir / "outputs" / "source_group_features.csv").relative_to(REPO)),
        "candidate_predictions": str((exp_dir / "outputs" / "candidate_predictions.csv").relative_to(REPO)),
        "correction_maps": str((exp_dir / "outputs" / "correction_maps.csv").relative_to(REPO)),
        "h25_manual_review_priority": str((exp_dir / "outputs" / "h25_manual_review_priority.csv").relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, preflight, review_priority, config)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} PP-H20~H26 completed\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "completed",
        "experiment": "PP-H20~H26",
        "summary": str((BASE_EXP_DIR / "PP-H20_H26_search_feature_expansion_summary_metrics.csv").relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
        "api_preflight": str((exp_dir / "outputs" / "api_preflight.csv").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
