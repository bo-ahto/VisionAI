#!/usr/bin/env python3
"""PP-GOLD1: Track6 Cold(v0.3) 모델을 4월 골든셋 150건에 돌려 CatBoost와 같은 셋에서 비교.

파트너 질문: "4월 골든셋 CatBoost ~39.5% vs 이번 Track6 ~41%"는 모델·테스트셋이
달라 직접 비교 불가였다. 같은 골든셋에 Track6 cold를 돌려 사과 대 사과 비교.

두 모드:
  - serving : 골든 작가가 Track6 DB/검색 스냅샷에 없으므로 메타 전부 결측(실서빙 현실)
  - matched : CatBoost가 쓴 정보(생년·전시 solo/group/fair)를 Track6 피처에 주입(공정 비교)

검색 피처는 두 모드 모두 결측(골든 작가는 검색 lookup 372명에 거의 없음 = 검색 보정 0).
실제 ReportModelProxyAdapter의 base/bucket 빌더와 y16·v0.3 후처리를 그대로 사용.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# .venv(실험용)에는 API 전용 pydantic이 없다. 스키마 검증은 쓰지 않고(덕타이핑
# request 사용) import만 통과시키면 되므로 최소 스텁 주입.
if "pydantic" not in sys.modules:
    _pyd = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    def _field(default=None, **kw):
        return default

    _pyd.BaseModel = _BaseModel
    _pyd.Field = _field
    sys.modules["pydantic"] = _pyd

# 검색 수집 전용 네트워크 모듈도 import 체인에 걸리므로 스텁(예측에는 미사용).
for _name, _attrs in [
    ("requests", {}),
    ("bs4", {"BeautifulSoup": object}),
    ("ddgs", {"DDGS": object}),
    ("duckduckgo_search", {"DDGS": object}),
]:
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        for _k, _v in _attrs.items():
            setattr(_m, _k, _v)
        sys.modules[_name] = _m
# scripts/track6도 import 경로에 필요
_scripts = REPO / "scripts" / "track6"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

from visionai.price_engine.api.official_v0_1_report_adapters import (  # noqa: E402
    ReportModelProxyAdapter,
    _normalize_model_input_frame,
)

GOLDEN_PRED = REPO / "data" / "golden_set_predictions.csv"
GOLDEN_CMP = REPO / "data" / "golden_set_comparison.csv"
OUT = Path(__file__).resolve().parents[1] / "artifacts"
REF_YEAR = 2026.0


def _req(width, height, medium_cat, support_cat, category="painting"):
    """_build_cold_feature_frame가 읽는 속성만 가진 덕타이핑 request."""
    return SimpleNamespace(
        artwork=SimpleNamespace(
            dimensions=SimpleNamespace(width_cm=width, height_cm=height, depth_cm=0.0),
            medium=SimpleNamespace(medium_category=medium_cat, support_category=support_cat),
            category=category,
        )
    )


def build_frame(adapter, row, features, mode):
    base = adapter._build_cold_feature_frame(
        _req(row["가로(cm)"], row["세로(cm)"], row["medium_category"], row["support_type"])
    )
    frame = base.copy()

    birth = row["birth_year_clean"]
    has_birth = pd.notna(birth)
    inject = mode == "matched"

    # --- 작가 메타 ---
    frame["artist_meta_birth_year"] = float(birth) if (inject and has_birth) else np.nan
    frame["artist_meta_career_stage"] = (
        (REF_YEAR - float(birth)) if (inject and has_birth) else np.nan
    )
    for col in [
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
    ]:
        frame[col] = np.nan
    frame["artist_meta_nationality"] = "KR" if inject else "__MISSING__"
    frame["artist_meta_nationality_ko"] = "KR" if inject else "__MISSING__"
    frame["artist_meta_source"] = "golden_set" if inject else "__MISSING__"
    frame["artist_meta_is_p1_flag"] = 0.0
    frame["artist_meta_has_international_flag"] = (
        float(row.get("has_intl", 0) or 0) if inject else 0.0
    )
    frame["is_high_price_candidate_flag"] = 0.0
    for col in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_career_stage",
    ]:
        frame[f"{col}_missing"] = float(pd.to_numeric(frame[col], errors="coerce").isna().iloc[0])
    frame["artist_meta_total_works_log"] = 0.0
    frame["artist_meta_for_sale_works_log"] = 0.0
    frame["artist_meta_followers_log"] = 0.0

    # --- 전시 (골든 solo/group/fair 주입; serving 모드는 결측) ---
    if inject:
        solo, group, fair = float(row["solo"]), float(row["group"]), float(row["fair"])
        total = solo + group + fair
        frame["artist_exhibition_solo_count"] = solo
        frame["artist_exhibition_group_count"] = group
        frame["artist_exhibition_fair_count"] = fair
        frame["artist_exhibition_total_count"] = total
        frame["artist_exhibition_available_count"] = 1.0
        for c, v in [("solo", solo), ("group", group), ("fair", fair)]:
            frame[f"artist_exhibition_{c}_count_missing"] = 0.0
            frame[f"artist_exhibition_{c}_count_log"] = float(np.log1p(v))
        frame["artist_exhibition_total_count_log"] = float(np.log1p(total))
    else:
        for c in ["solo", "group", "fair"]:
            frame[f"artist_exhibition_{c}_count"] = np.nan
            frame[f"artist_exhibition_{c}_count_missing"] = 1.0
            frame[f"artist_exhibition_{c}_count_log"] = 0.0
        frame["artist_exhibition_total_count"] = np.nan
        frame["artist_exhibition_available_count"] = 0.0
        frame["artist_exhibition_total_count_log"] = 0.0

    # --- 갤러리: 두 모드 모두 결측 (골든에 tier 없음) ---
    frame["gallery_tier_raw_numeric"] = np.nan
    frame["gallery_tier_validated_score"] = np.nan
    frame["gallery_city_count"] = np.nan
    frame["gallery_tier_raw_available_flag"] = 0.0
    frame["gallery_tier_validated_available_flag"] = 0.0
    frame["gallery_tier_any_available_flag"] = 0.0
    frame["gallery_city_count_log"] = 0.0
    for c in [
        "gallery_tier_raw_bucket",
        "gallery_tier_validated",
        "gallery_ref_type",
        "gallery_audit_status",
    ]:
        frame[c] = "__MISSING__"
    frame["gallery_feature_source"] = "missing"

    # --- 검색: 두 모드 모두 결측 (골든 작가 검색 lookup 미커버) ---
    search_zero = [
        "search_result_count",
        "search_source_count",
        "search_art_context_count",
        "search_exhibition_context_count",
        "search_gallery_context_count",
        "search_award_institution_context_count",
        "search_social_context_count",
        "search_market_context_count",
        "search_homonym_context_count",
        "search_art_match_ratio",
        "search_exhibition_ratio",
        "search_source_ratio",
        "search_quality_score",
        "search_collected_flag",
        "search_success_flag",
    ]
    for c in search_zero:
        frame[c] = 0.0
    frame["search_result_count_log"] = 0.0
    frame["search_art_context_count_log"] = 0.0
    frame["search_exhibition_context_count_log"] = 0.0
    frame["search_source_count_log"] = 0.0
    frame["search_quality_grade"] = "missing"
    frame["search_homonym_risk_grade"] = "missing"
    frame["search_size_quality_bucket"] = frame["size_bucket"].astype(str) + "__missing"
    frame["search_quality_x_log_area"] = 0.0
    frame["search_art_match_x_followers_log"] = 0.0
    frame["search_exhibition_x_career_stage"] = 0.0

    # --- 외부 상호작용 (어댑터 로직 그대로) ---
    adapter._apply_external_feature_interactions(frame)

    return _normalize_model_input_frame(frame.reindex(columns=features))


def predict(adapter, frame, artist_key):
    q10 = float(np.asarray(adapter.cold_y2_models["q10"].predict(frame), dtype=float)[0])
    q50 = float(np.asarray(adapter.cold_y2_models["q50"].predict(frame), dtype=float)[0])
    q90 = float(np.asarray(adapter.cold_y2_models["q90"].predict(frame), dtype=float)[0])
    q40 = float(np.asarray(adapter.cold_qr1_q40_model.predict(frame), dtype=float)[0])
    qwidth = max(q90 - q10, 0.0)
    rep_log = adapter._apply_cold_y16_segment_correction(q50, qwidth)
    v03_input = pd.DataFrame(
        [
            {
                "y18_qwidth_pred_log": rep_log,
                "lgb_q40_pred_log": q40,
                "quantile_width_log": qwidth,
                "artist_key": artist_key,
            }
        ]
    )
    out = adapter.cold_v03.apply(
        v03_input, params=adapter.cold_v03_params, lookup=adapter.cold_v03_lookup
    ).iloc[0]
    return float(out["cold_defense_pred_price_krw"])


def metrics(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": len(actual),
        "MdAPE": round(float(np.median(ape)), 4),
        "MAPE": round(float(np.mean(ape)), 4),
        "W30": round(float(np.mean(ape <= 0.30)), 4),
        "W50": round(float(np.mean(ape <= 0.50)), 4),
        "median_ratio": round(float(np.median(pred / np.clip(actual, 1.0, None))), 4),
    }


def main():
    pred_df = pd.read_csv(GOLDEN_PRED)
    cmp_df = pd.read_csv(GOLDEN_CMP)[["작가명", "작품명", "actual_krw"]]
    df = pred_df.merge(cmp_df, on=["작가명", "작품명"], how="inner")
    df = df[
        pd.notna(df["actual_krw"]) & pd.notna(df["가로(cm)"]) & pd.notna(df["세로(cm)"])
    ].reset_index(drop=True)

    adapter = ReportModelProxyAdapter()
    features = adapter.cold_refreeze_schema.get("pp_y2_feature_columns")

    results = {}
    rows_out = []
    for mode in ["serving", "matched"]:
        preds = []
        for _, row in df.iterrows():
            ak = str(row["작가명"]).strip().lower().replace("-", " ")
            frame = build_frame(adapter, row, features, mode)
            p = predict(adapter, frame, ak)
            preds.append(p)
            if mode == "matched":
                rows_out.append(
                    {
                        "작가명": row["작가명"],
                        "작품명": row["작품명"],
                        "actual_krw": float(row["actual_krw"]),
                        "track6_matched_krw": round(p),
                        "catboost_krw": round(float(row["predicted_krw"])),
                    }
                )
        results[f"track6_{mode}"] = metrics(df["actual_krw"], preds)

    # CatBoost 골든셋 원본 예측(predictions.csv predicted_krw) 동일 셋 재계산
    results["catboost_golden_recompute"] = metrics(df["actual_krw"], df["predicted_krw"])
    results["catboost_reported_mdape"] = 0.395  # golden_set_test_result.md 보고값

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "golden_comparison_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(rows_out).to_csv(OUT / "golden_per_artwork_matched.csv", index=False)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
