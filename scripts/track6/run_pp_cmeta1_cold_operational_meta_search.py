#!/usr/bin/env python3
"""PP-CMETA1: Cold operational artist-meta/search feature validation.

This experiment matches the intended Cold design:
- no same-artist price history features
- no artist_key category memorization
- no per-artist search_delta lookup
- train on artwork + artist meta/search/exhibition features available for
  historical artists, then evaluate on unseen Cold artists.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO  # noqa: E402
from run_pp_w_experiments import META_ALL, base_feature_sets, unique  # noqa: E402
from run_pp_y_cold_combination_experiments import (  # noqa: E402
    direct_bundle_experiment,
    external_core_features,
    external_interaction_features,
    load_cold_full,
    load_search_df,
    search_all_features,
    search_context_features,
)


EXP_ID = "PP-CMETA1"
SLUG = "PP-CMETA1_cold_operational_meta_search_validation"
TITLE = "Cold 운영형 작가 메타/인터넷 검색 피처 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"


def candidates() -> list[tuple[str, str, list[str], str]]:
    fs = base_feature_sets()
    artwork = fs["cold_lgb"]
    return [
        (
            "artwork_only_lgbq",
            "작품 정보만 사용",
            unique(artwork),
            "작가 외부 정보가 전혀 없을 때의 운영 최저 기준",
        ),
        (
            "artwork_artist_meta_lgbq",
            "작품 정보 + 비가격성 작가 메타",
            unique(artwork + META_ALL),
            "학습 작가의 메타 패턴을 배워 신규 작가 메타와 작품 정보로 예측",
        ),
        (
            "artwork_artist_meta_search_context_lgbq",
            "작품 정보 + 작가 메타 + 검색 문맥",
            unique(artwork + META_ALL + search_context_features()),
            "인터넷 검색에서 얻은 미술/전시/갤러리 문맥이 Cold 예측을 보완하는지 확인",
        ),
        (
            "artwork_artist_meta_external_core_lgbq",
            "작품 정보 + 작가 메타 + 전시/갤러리 구조화 피처",
            unique(artwork + META_ALL + external_core_features()),
            "검색 결과를 구조화한 전시/갤러리 피처가 예측력을 갖는지 확인",
        ),
        (
            "artwork_artist_meta_search_external_lgbq",
            "작품 정보 + 작가 메타 + 검색 + 전시/갤러리",
            unique(artwork + META_ALL + search_all_features() + external_interaction_features()),
            "운영 수집 가능한 외부 정보를 모두 사용한 Cold 후보",
        ),
    ]


def coverage_summary(all_features: list[str], search_df: pd.DataFrame) -> pd.DataFrame:
    train, val, test = load_cold_full(all_features, search_df)
    rows: list[dict[str, Any]] = []
    checks = [
        ("artist_meta_birth_year", "작가 생년"),
        ("artist_meta_followers", "작가 팔로워"),
        ("artist_meta_total_works", "작가 전체 작품 수"),
        ("search_success_flag", "검색 성공"),
        ("search_quality_score", "검색 품질 점수"),
        ("artist_exhibition_total_count", "전시 총수"),
        ("gallery_tier_any_available_flag", "갤러리 tier 가용"),
    ]
    for split, frame in [("train", train), ("validation", val), ("test", test)]:
        for col, label in checks:
            if col not in frame.columns:
                continue
            series = frame[col]
            if col.endswith("_flag"):
                covered = pd.to_numeric(series, errors="coerce").fillna(0.0) > 0
            else:
                covered = series.notna()
            rows.append({
                "split": split,
                "feature": col,
                "label": label,
                "n": int(len(frame)),
                "covered_rows": int(covered.sum()),
                "coverage_rate": float(covered.mean()) if len(frame) else 0.0,
            })
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                vals.append(f"{value:.6f}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    head = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    body = []
    for _, row in df[cols].iterrows():
        cells = []
        for col in cols:
            value = row[col]
            text = f"{value:.6f}" if isinstance(value, float) else str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def main() -> None:
    for path in [OUT, REPORTS, ARTIFACTS]:
        path.mkdir(parents=True, exist_ok=True)

    search_df = load_search_df()
    cands = candidates()
    metric_rows, prediction_frames, feature_map = direct_bundle_experiment(
        EXP_ID,
        cands,
        "lightgbm",
        "cold_operational_meta_search_no_artist_lookup",
        search_df,
    )

    metrics = pd.DataFrame(metric_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    feature_map_df = pd.DataFrame(feature_map)
    all_features = unique([feature for _, _, features, _ in cands for feature in features])
    coverage = coverage_summary(all_features, search_df)

    metrics.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "predictions.csv", index=False)
    feature_map_df.to_csv(OUT / "feature_map.csv", index=False)
    coverage.to_csv(OUT / "feature_coverage.csv", index=False)

    test = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)
    val = metrics[metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).reset_index(drop=True)

    summary = {
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "design": {
            "uses_same_artist_price_history": False,
            "uses_artist_key_as_model_feature": False,
            "uses_per_artist_lookup_postprocess": False,
            "uses_artist_meta": True,
            "uses_cached_internet_search_features": True,
            "live_search_in_this_run": False,
        },
        "best_test_candidate": test.iloc[0].to_dict() if not test.empty else {},
        "source_note": "검색 피처는 기존 동결 검색 cache를 사용했다. 운영 적용 시 동일 schema로 신규 작가 검색 수집 후 입력한다.",
    }
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = ["candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "n_features", "feature_strategy"]
    coverage_cols = ["split", "feature", "covered_rows", "n", "coverage_rate"]
    map_cols = ["candidate", "n_features", "feature_strategy", "hypothesis"]

    report_md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 같은 작가 가격 이력 없이, 작품 정보와 운영 수집 가능한 작가 메타/인터넷 검색 피처만으로 Cold 가격을 예측할 수 있는지 확인한다.",
        "- 제외: `artist_key` 모델 피처, 같은 작가 가격 통계, 작가별 search_delta lookup 후처리.",
        "- 검색 피처: 이번 실행에서는 기존 동결 검색 cache를 사용했다. 운영에서는 같은 schema로 신규 작가를 검색 수집해 넣는 방식으로 연결한다.",
        "",
        "## Test 결과",
        md_table(test[metric_cols], metric_cols),
        "",
        "## Validation 결과",
        md_table(val[metric_cols], metric_cols),
        "",
        "## 외부 피처 커버리지",
        md_table(coverage[coverage_cols], coverage_cols),
        "",
        "## 후보별 피처 설계",
        md_table(feature_map_df[map_cols], map_cols),
        "",
        "## 해석",
        "- 이 실험은 사용자가 기대한 운영형 Cold 구조를 lookup 없이 분리 검증한다.",
        "- `artwork_only_lgbq` 대비 작가 메타/검색/전시 피처 후보의 개선 여부가 핵심 판단 기준이다.",
        "- 실제 운영 승격 전에는 신규 작가 live search 수집 -> feature 생성 -> same schema inference -> fallback 정책 검증이 필요하다.",
    ])
    (REPORTS / "result_report.md").write_text(report_md, encoding="utf-8")

    report_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; }}
    table {{ border-collapse: collapse; margin: 16px 0; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
    code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
    .note {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 12px 16px; margin: 18px 0; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE)}</h1>
  <div class="note">
    같은 작가 가격 이력, <code>artist_key</code> 모델 피처, 작가별 lookup 후처리를 제외하고
    작품 정보와 운영 수집 가능한 작가 메타/검색 피처만 검증했다.
  </div>
  <h2>Test 결과</h2>
  {html_table(test, metric_cols)}
  <h2>Validation 결과</h2>
  {html_table(val, metric_cols)}
  <h2>외부 피처 커버리지</h2>
  {html_table(coverage, coverage_cols)}
  <h2>후보별 피처 설계</h2>
  {html_table(feature_map_df, map_cols)}
</body>
</html>
"""
    (REPORTS / "result_report.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
