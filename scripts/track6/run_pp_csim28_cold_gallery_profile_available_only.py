#!/usr/bin/env python3
"""PP-CSIM28: profile-available-only Cold gallery/exhibition validation.

CSIM27은 전체 Cold cohort에서 갤러리/전시 문맥의 효과를 봤다.
이번 실험은 운영 입력에 갤러리 또는 전시 정보가 있는 경우만 따로 본다.

조건:
  - train / validation / test 모두 갤러리 또는 전시 정보가 있는 행만 사용
  - artist_key, 동일 작가 가격 이력, artist_key lookup 후처리 금지
  - search_* / 외부 live 검색 피처 금지
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

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_csim1_cold_similarity_reference import compute_reference_stats, html_table, json_clean, md_table  # noqa: E402
from run_pp_csim27_cold_gallery_profile_grouping import (  # noqa: E402
    ALPHA,
    ARTWORK_FEATURES,
    ARTWORK_SIM_FEATURES,
    CORE_ARTIST_META,
    FEATURE_STORE,
    GENERATED_PROFILE_BUCKETS,
    PROFILE_FEATURES,
    PROFILE_SIM_FEATURES,
    TOP_K,
    add_profile_buckets,
    coverage_summary,
    fit_predict,
    metric_row,
    prediction_frame,
    segment_summary,
)
from run_pre_pp_experiments import BASE_EXP_DIR, REPO  # noqa: E402
from run_pp_w_experiments import unique  # noqa: E402


EXP_ID = "PP-CSIM28"
SLUG = "PP-CSIM28_cold_gallery_profile_available_only"
TITLE = "Cold 갤러리/전시 정보 보유 입력 전용 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim28_cold_gallery_profile_available_only_summary.md"


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def profile_available_mask(frame: pd.DataFrame) -> pd.Series:
    gallery = pd.to_numeric(frame.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0) > 0
    exhibition = pd.to_numeric(frame.get("artist_exhibition_available_count", 0.0), errors="coerce").fillna(0.0) > 0
    return gallery | exhibition


def load_profile_available_frames(required_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(FEATURE_STORE, low_memory=False)
    frame = add_profile_buckets(frame)
    required = unique(["_track6_row_id", "price_krw", "ln_price_krw", "split_name"] + required_features)
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing feature-store columns: {missing}")
    frame = frame[required].copy()

    before_after = []
    out_frames = []
    for split in ["train", "validation", "test"]:
        part = frame[frame["split_name"].eq(split)].copy()
        before = len(part)
        part = part[profile_available_mask(part)].copy()
        after = len(part)
        before_after.append({"split": split, "before_n": before, "after_n": after, "kept_rate": after / before if before else 0.0})
        out_frames.append(part.drop(columns=["split_name"]).reset_index(drop=True))
    return out_frames[0], out_frames[1], out_frames[2], pd.DataFrame(before_after)


def write_reports(metrics_df: pd.DataFrame, filter_df: pd.DataFrame, coverage_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "n_model_features", "n_similarity_features", "policy",
    ]
    filter_cols = ["split", "before_n", "after_n", "kept_rate"]
    cov_cols = ["split", "n", "gallery_any_n", "gallery_any_rate", "gallery_validated_n", "gallery_validated_rate", "exhibition_available_n", "exhibition_available_rate"]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]

    test_sorted = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5"])
    val_sorted = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5"])

    feature_lines = []
    for cand in candidates:
        feature_lines.extend([
            f"### {cand['name']}",
            f"- 정책: {cand['policy']}",
            f"- 모델 입력 피처 수: {len(cand['model_features'])}",
            f"- 유사 이웃 선택 피처 수: {len(cand['sim_features'])}",
            "",
        ])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 갤러리 또는 전시 정보가 실제로 있는 입력만 대상으로 학습/검증/테스트했을 때 해당 문맥 피처가 도움이 되는지 확인한다.",
        "- 엄격 조건: `artist_key`, 동일 작가 가격 이력, artist_key lookup, `search_*`, 외부 live 검색 미사용.",
        "- 필터 조건: `gallery_tier_any_available_flag > 0 OR artist_exhibition_available_count > 0`.",
        "",
        "## 1. 필터 후 평가 행 수",
        md_table(filter_df, filter_cols),
        "",
        "## 2. Test 결과",
        md_table(test_sorted, metric_cols),
        "",
        "## 3. Validation 결과",
        md_table(val_sorted, metric_cols),
        "",
        "## 4. 필터 후 갤러리/전시 커버리지",
        md_table(coverage_df, cov_cols),
        "",
        "## 5. 가격대별 Test 진단",
        md_table(seg_df[seg_df["split"].eq("test")].sort_values(["candidate", "segment"]), seg_cols),
        "",
        "## 6. 후보 정의",
        *feature_lines,
        "## 7. 해석 기준",
        "",
        "- 이 결과는 전체 Cold가 아니라 갤러리/전시 정보가 있는 입력에 한정된 성능이다.",
        "- 운영에서 사용자가 갤러리/전시 정보를 안정적으로 입력하거나 DB에서 검증해 붙일 수 있을 때만 적용 가능하다.",
        "- 전체 Cold 기본 모델과 직접 비교하지 말고, 동일한 profile-available cohort 안에서 후보끼리 비교해야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>필터 조건: gallery_tier_any_available_flag &gt; 0 OR artist_exhibition_available_count &gt; 0</p>
<h2>필터 후 평가 행 수</h2>{html_table(filter_df, filter_cols)}
<h2>Test 결과</h2>{html_table(test_sorted, metric_cols)}
<h2>Validation 결과</h2>{html_table(val_sorted, metric_cols)}
<h2>커버리지</h2>{html_table(coverage_df, cov_cols)}
<h2>가격대별 Test 진단</h2>{html_table(seg_df[seg_df['split'].eq('test')].sort_values(['candidate', 'segment']), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    base_model_features = unique(ARTWORK_FEATURES + CORE_ARTIST_META)
    profile_model_features = unique(base_model_features + PROFILE_FEATURES + GENERATED_PROFILE_BUCKETS)
    base_sim_features = unique(ARTWORK_SIM_FEATURES)
    profile_sim_features = unique(PROFILE_SIM_FEATURES)
    required = unique(profile_model_features + profile_sim_features)

    for label, features in [
        ("base_model", base_model_features),
        ("profile_model", profile_model_features),
        ("base_sim", base_sim_features),
        ("profile_sim", profile_sim_features),
    ]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{label}")
        bad = [feature for feature in features if feature.startswith("search_") or feature == "artist_key"]
        if bad:
            raise ValueError(f"{label} contains forbidden features: {bad}")

    train, val, test, filter_df = load_profile_available_frames(required)
    if min(len(train), len(val), len(test)) <= TOP_K:
        raise RuntimeError("Profile-available split is too small for configured top_k")

    candidates = [
        {
            "name": "base_profile_available_artwork_similarity_k80",
            "model_features": base_model_features,
            "sim_features": base_sim_features,
            "policy": "정보 보유 행만 사용하되 모델 구조는 기본 작품/작가 메타 + 작품 유사 이웃",
        },
        {
            "name": "direct_gallery_profile_available_k80",
            "model_features": profile_model_features,
            "sim_features": base_sim_features,
            "policy": "정보 보유 행에서 갤러리/전시 문맥을 모델 입력에 직접 추가",
        },
        {
            "name": "similarity_gallery_profile_available_k80",
            "model_features": base_model_features,
            "sim_features": profile_sim_features,
            "policy": "정보 보유 행에서 갤러리/전시 문맥은 유사 이웃 선택에만 사용",
        },
        {
            "name": "direct_and_similarity_gallery_profile_available_k80",
            "model_features": profile_model_features,
            "sim_features": profile_sim_features,
            "policy": "정보 보유 행에서 갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용",
        },
    ]

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for cand in candidates:
        train_ref, val_ref, test_ref, ref_features = compute_reference_stats(
            train,
            val,
            test,
            cand["sim_features"],
            prefix=f"{cand['name']}_ref_k{TOP_K}",
            top_k=TOP_K,
        )
        model_features = unique(cand["model_features"] + ref_features)
        preds = fit_predict(train_ref, val_ref, test_ref, model_features)
        for split, frame in [("validation", val_ref), ("test", test_ref)]:
            pred = preds[split]
            metric_rows.append(metric_row(cand["name"], split, frame, pred, cand["policy"], model_features, cand["sim_features"]))
            pred_frames.append(prediction_frame(cand["name"], split, frame, pred, cand["policy"]))
        cand["model_features"] = model_features

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    coverage_df = coverage_summary(train, val, test)
    seg_df = segment_summary(predictions_df)
    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "feature_store": str(FEATURE_STORE.relative_to(REPO)),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_artist_identity_feature": False,
        "uses_same_artist_price_history": False,
        "uses_gallery_profile_features": True,
        "profile_available_filter": "gallery_tier_any_available_flag > 0 OR artist_exhibition_available_count > 0",
        "top_k": TOP_K,
        "alpha": ALPHA,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    filter_df.to_csv(OUT / "profile_available_filter_counts.csv", index=False)
    coverage_df.to_csv(OUT / "gallery_profile_coverage.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, filter_df, coverage_df, seg_df, summary, candidates)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
