#!/usr/bin/env python3
"""Create Track6 PP-G/PP-H conditional external-data experiment artifacts."""
from __future__ import annotations

import html
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BASE_EXP_DIR = REPO / "experiments" / "track6"
SPLIT_ROOT = REPO / "data" / "track6_split"
SEED = 20260602

EXPERIMENTS = {
    "PP-G1": {"slug": "PP-G1_exhibition_external_data_check", "title": "전시 이력 신규/보강 데이터 검증", "group": "G"},
    "PP-G2": {"slug": "PP-G2_award_institution_external_data_check", "title": "수상/기관 이력 신규 데이터 검증", "group": "G"},
    "PP-G3": {"slug": "PP-G3_gallery_affiliation_external_data_check", "title": "갤러리 소속 정보 검증", "group": "G"},
    "PP-G4": {"slug": "PP-G4_external_artist_db_bundle_check", "title": "외부 DB 전체 묶음 검증", "group": "G"},
    "PP-G5": {"slug": "PP-G5_external_db_postprocessing_combo_check", "title": "외부 DB + 후보정 결합 검증", "group": "G"},
    "PP-H1": {"slug": "PP-H1_naver_search_metric_check", "title": "네이버 검색 결과 수 검증", "group": "H"},
    "PP-H2": {"slug": "PP-H2_google_search_metric_check", "title": "구글 검색 결과 수 검증", "group": "H"},
    "PP-H3": {"slug": "PP-H3_google_trends_metric_check", "title": "Google Trends 관심도 검증", "group": "H"},
    "PP-H4": {"slug": "PP-H4_social_metric_check", "title": "SNS/소셜 신규 지표 검증", "group": "H"},
    "PP-H5": {"slug": "PP-H5_search_quality_flag_check", "title": "검색 품질 표시 변수 검증", "group": "H"},
    "PP-H6": {"slug": "PP-H6_search_social_bundle_check", "title": "검색/소셜 전체 묶음 검증", "group": "H"},
}

REQUIREMENTS = {
    "PP-G1": ["solo_exhibition_count", "group_exhibition_count", "artfair_count", "exhibition_quality_tier"],
    "PP-G2": ["award_count", "institution_exhibition_count", "institution_tier"],
    "PP-G3": ["gallery_affiliated", "exclusive_gallery", "gallery_tier", "gallery_match_confidence"],
    "PP-G4": ["solo_exhibition_count", "award_count", "institution_tier", "gallery_tier"],
    "PP-G5": ["external_artist_db_bundle_pred_log", "postprocessing_candidate_pred_log"],
    "PP-H1": ["naver_blog_count", "naver_news_count", "naver_web_count", "naver_search_success", "homonym_risk"],
    "PP-H2": ["google_result_count", "google_search_success", "google_recollect_variance"],
    "PP-H3": ["google_trends_score", "google_trends_available"],
    "PP-H4": ["instagram_mention_count", "web_social_mention_count", "social_match_success"],
    "PP-H5": ["search_match_score", "homonym_risk", "search_quality_grade"],
    "PP-H6": ["naver_blog_count", "google_result_count", "google_trends_score", "instagram_mention_count", "search_quality_grade"],
}

EXISTING_META_FILE = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"


def available_columns() -> dict[str, list[str]]:
    paths = {
        "warm_features": SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
        "cold_features": SPLIT_ROOT / "features" / "cold" / "track6_train_cold_features.csv",
        "train_labels": SPLIT_ROOT / "labels" / "track6_train_labels.csv",
        "artist_meta_candidates": EXISTING_META_FILE,
    }
    out: dict[str, list[str]] = {}
    for key, path in paths.items():
        if path.exists():
            out[key] = pd.read_csv(path, nrows=5, low_memory=False).columns.tolist()
        else:
            out[key] = []
    return out


def meta_coverage() -> pd.DataFrame:
    if not EXISTING_META_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(EXISTING_META_FILE, low_memory=False)
    meta_cols = [c for c in df.columns if c.startswith("artist_meta_")]
    rows = []
    for col in meta_cols:
        s = df[col]
        rows.append({
            "column": col,
            "n_rows": int(len(df)),
            "non_null": int(s.notna().sum()),
            "coverage": float(s.notna().mean()),
            "n_unique": int(s.nunique(dropna=True)),
        })
    return pd.DataFrame(rows)


def status_for(exp_id: str, cols_by_source: dict[str, list[str]]) -> tuple[str, str, list[str], list[str]]:
    required = REQUIREMENTS[exp_id]
    all_cols = sorted({c for cols in cols_by_source.values() for c in cols})
    present = [c for c in required if c in all_cols]
    missing = [c for c in required if c not in all_cols]
    if not missing:
        return "ready", "required columns are present in local split", present, missing
    if exp_id.startswith("PP-G") and EXISTING_META_FILE.exists():
        meta_cols = cols_by_source.get("artist_meta_candidates", [])
        existing_meta = [c for c in meta_cols if c.startswith("artist_meta_")]
        if existing_meta:
            return "blocked_existing_meta_only", "artist meta 후보 컬럼은 있으나 PP-G 요구사항은 신규/보강 외부 DB이므로 기존 컬럼 재사용으로 실행하지 않음", present, missing
    return "blocked_data_needed", "required 신규 외부/search/social columns are not available locally", present, missing


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    row = metrics_df.iloc[0]
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 신규 외부 데이터 또는 검색/소셜 지표가 후처리 이후 추가 개선에 필요한지 판단한다.",
        "- 실행 기준: 기존 컬럼 재사용이 아니라 신규/보강 데이터가 있을 때만 모델 성능 실험을 실행한다.",
        f"- 현재 상태: `{row.status}`",
        f"- 판단: {row.decision}",
        "",
        "## 필요한 컬럼",
        "",
    ]
    for col in json.loads(row.required_columns):
        lines.append(f"- `{col}`")
    lines += ["", "## 현재 누락 컬럼", ""]
    for col in json.loads(row.missing_columns):
        lines.append(f"- `{col}`")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Status</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Column Coverage</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No existing meta coverage.</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, cols_by_source: dict[str, list[str]], coverage_df: pd.DataFrame) -> dict[str, Any]:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    status, decision, present, missing = status_for(exp_id, cols_by_source)
    metrics_df = pd.DataFrame([{
        "experiment_id": exp_id,
        "group": info["group"],
        "title": info["title"],
        "status": status,
        "decision": decision,
        "required_columns": json.dumps(REQUIREMENTS[exp_id], ensure_ascii=False),
        "present_columns": json.dumps(present, ensure_ascii=False),
        "missing_columns": json.dumps(missing, ensure_ascii=False),
        "n_required": len(REQUIREMENTS[exp_id]),
        "n_present": len(present),
        "n_missing": len(missing),
        "can_train_model": status == "ready",
    }])
    pred_df = pd.DataFrame({
        "experiment_id": [exp_id],
        "scope": ["cold" if exp_id.startswith("PP-H") or exp_id in {"PP-G2", "PP-G3", "PP-G4", "PP-G5"} else "warm_or_cold"],
        "split": ["not_run"],
        "_track6_row_id": [-1],
        "actual_log": [np.nan],
        "pred_log": [np.nan],
        "actual_price": [np.nan],
        "pred_price": [np.nan],
        "status": [status],
    })
    map_df = coverage_df.copy()
    if map_df.empty:
        map_df = pd.DataFrame([{"experiment_id": exp_id, "note": "no existing artist meta coverage table"}])
    else:
        map_df.insert(0, "experiment_id", exp_id)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[["scope", "split", "_track6_row_id"]].to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[["scope", "split", "_track6_row_id"]].to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "policy": "conditional_external_data_check",
        "columns_by_source": cols_by_source,
    }
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "not_run unless new external/search data exists"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps({"required_columns": REQUIREMENTS[exp_id], "present_columns": present, "missing_columns": missing}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps({"mode": "conditional_check", "can_train_model": status == "ready", "target": "ln_price_krw"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(map_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} {status}\n", encoding="utf-8")
    out = metrics_df.iloc[0].to_dict()
    out["folder"] = str((exp_dir).relative_to(REPO))
    return out


def main() -> None:
    start = time.time()
    BASE_EXP_DIR.mkdir(parents=True, exist_ok=True)
    cols_by_source = available_columns()
    coverage_df = meta_coverage()
    rows = [write_exp(exp_id, cols_by_source, coverage_df) for exp_id in EXPERIMENTS]
    summary = pd.DataFrame(rows)
    summary.to_csv(BASE_EXP_DIR / "PP-G_H_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-G_H_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
