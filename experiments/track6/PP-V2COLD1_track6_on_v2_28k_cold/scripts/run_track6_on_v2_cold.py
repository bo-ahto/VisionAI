#!/usr/bin/env python3
"""PP-V2COLD1: Track6 Cold(v0.3) 모델을 v2 리포트의 28,376건 cold 테스트셋에 실행.

배경: v2 리포트 §8.2 Cold slice = integrated_v3 GroupKFold OOF 28,376건(Saatchi 21,087 +
Artsy 7,289), CatBoost MdAPE 39.4%(보고값, source_calibration.json). 같은 28,376행
정답가격(OOF y_ln_price)에 Track6 cold를 돌려 같은 셋에서 비교한다.

데이터 조인:
  - OOF parquet(28,376) = 행 식별 + 정답(y_ln_price) + CatBoost 예측(cb_pred_ln_price, 이 파일은 41.3%)
  - Saatchi 피처: artist_slug+ln_price 100% 매칭(area_cm2/medium/support/birth/solo·group·fair)
  - Artsy 피처: artist_slug+ln_price 99.6% 매칭(width/height/medium/birth, 전시 없음)

CatBoost 비교 기준 2개: 보고서 최종 39.4%, 이 OOF parquet(audit4 버전) 41.3%.
검색 피처는 결측(이 작가들은 Track6 검색 lookup 미커버) — golden set과 동일 한계.
"""

from __future__ import annotations

import json
import sys
import types
import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")  # LGBM feature-name 경고 억제(예측은 피처명 정렬 검증됨)

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "src"
for p in (SRC, REPO / "scripts" / "track6"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

if "pydantic" not in sys.modules:
    _pyd = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    _pyd.BaseModel = _BaseModel
    _pyd.Field = lambda default=None, **kw: default
    sys.modules["pydantic"] = _pyd
for _n, _a in [
    ("requests", {}),
    ("bs4", {"BeautifulSoup": object}),
    ("ddgs", {"DDGS": object}),
    ("duckduckgo_search", {"DDGS": object}),
]:
    if _n not in sys.modules:
        _m = types.ModuleType(_n)
        for _k, _v in _a.items():
            setattr(_m, _k, _v)
        sys.modules[_n] = _m

from visionai.price_engine.api.official_v0_1_report_adapters import (  # noqa: E402
    ReportModelProxyAdapter,
    _normalize_model_input_frame,
)

OOF = REPO / "model_test_results" / "audit4_drift_fix_v1_oof_groupkfold.parquet"
SAATCHI = REPO / "data" / "saatchi_cleaned.parquet"
ARTSY = REPO / "data" / "artsy_kr_artworks.csv"
OUT = Path(__file__).resolve().parents[1] / "artifacts"
REF_YEAR = 2026.0
REPORTED_CATBOOST_MDAPE = 0.3938  # v2 source_calibration.json cold_overall.baseline_mdape


def load_rows():
    oof = pd.read_parquet(OOF)
    oof["lnp"] = oof["y_ln_price"].round(3)

    s = pd.read_parquet(SAATCHI)
    s["lnp"] = s["ln_price"].round(3)
    scols = [
        "artist_slug",
        "lnp",
        "area_cm2",
        "medium_category",
        "support_type",
        "has_depth",
        "artist_birth_year",
        "solo_count",
        "group_count",
        "fair_count",
    ]
    s = s[scols].drop_duplicates(["artist_slug", "lnp"])

    a = pd.read_csv(ARTSY, low_memory=False)
    a["ln_price"] = np.log(pd.to_numeric(a["price_krw"], errors="coerce"))
    a["lnp"] = a["ln_price"].round(3)
    acols = [
        "artist_slug",
        "lnp",
        "width_cm",
        "height_cm",
        "depth_cm",
        "medium",
        "artist_birth_year",
    ]
    a = a[acols].drop_duplicates(["artist_slug", "lnp"])

    sa = oof[oof["source"] == "saatchi"].merge(s, on=["artist_slug", "lnp"], how="left")
    ar = oof[oof["source"] == "artsy"].merge(a, on=["artist_slug", "lnp"], how="left")
    return oof, sa, ar


def _req(width, height, depth, medium_cat, support_cat):
    return SimpleNamespace(
        artwork=SimpleNamespace(
            dimensions=SimpleNamespace(width_cm=width, height_cm=height, depth_cm=depth),
            medium=SimpleNamespace(medium_category=medium_cat, support_category=support_cat),
            category="painting",
        )
    )


def build_frame(
    adapter, feats, *, width, height, depth, medium, support, birth, solo, group, fair, mode
):
    base = adapter._build_cold_feature_frame(_req(width, height, depth, medium, support))
    f = base.copy()
    inject = mode == "matched"
    has_birth = pd.notna(birth)

    f["artist_meta_birth_year"] = float(birth) if (inject and has_birth) else np.nan
    f["artist_meta_career_stage"] = (REF_YEAR - float(birth)) if (inject and has_birth) else np.nan
    for c in [
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_for_sale_ratio",
    ]:
        f[c] = np.nan
    f["artist_meta_nationality"] = "KR" if inject else "__MISSING__"
    f["artist_meta_nationality_ko"] = "KR" if inject else "__MISSING__"
    f["artist_meta_source"] = "v2_cold" if inject else "__MISSING__"
    f["artist_meta_is_p1_flag"] = 0.0
    f["artist_meta_has_international_flag"] = 0.0
    f["is_high_price_candidate_flag"] = 0.0
    for c in [
        "artist_meta_birth_year",
        "artist_meta_total_works",
        "artist_meta_for_sale_works",
        "artist_meta_followers",
        "artist_meta_career_stage",
    ]:
        f[f"{c}_missing"] = float(pd.to_numeric(f[c], errors="coerce").isna().iloc[0])
    f["artist_meta_total_works_log"] = 0.0
    f["artist_meta_for_sale_works_log"] = 0.0
    f["artist_meta_followers_log"] = 0.0

    have_exh = inject and pd.notna(solo)
    if have_exh:
        solo, group, fair = float(solo), float(group or 0), float(fair or 0)
        total = solo + group + fair
        f["artist_exhibition_solo_count"] = solo
        f["artist_exhibition_group_count"] = group
        f["artist_exhibition_fair_count"] = fair
        f["artist_exhibition_total_count"] = total
        f["artist_exhibition_available_count"] = 1.0
        for c, v in [("solo", solo), ("group", group), ("fair", fair)]:
            f[f"artist_exhibition_{c}_count_missing"] = 0.0
            f[f"artist_exhibition_{c}_count_log"] = float(np.log1p(v))
        f["artist_exhibition_total_count_log"] = float(np.log1p(total))
    else:
        for c in ["solo", "group", "fair"]:
            f[f"artist_exhibition_{c}_count"] = np.nan
            f[f"artist_exhibition_{c}_count_missing"] = 1.0
            f[f"artist_exhibition_{c}_count_log"] = 0.0
        f["artist_exhibition_total_count"] = np.nan
        f["artist_exhibition_available_count"] = 0.0
        f["artist_exhibition_total_count_log"] = 0.0

    f["gallery_tier_raw_numeric"] = np.nan
    f["gallery_tier_validated_score"] = np.nan
    f["gallery_city_count"] = np.nan
    f["gallery_tier_raw_available_flag"] = 0.0
    f["gallery_tier_validated_available_flag"] = 0.0
    f["gallery_tier_any_available_flag"] = 0.0
    f["gallery_city_count_log"] = 0.0
    for c in [
        "gallery_tier_raw_bucket",
        "gallery_tier_validated",
        "gallery_ref_type",
        "gallery_audit_status",
    ]:
        f[c] = "__MISSING__"
    f["gallery_feature_source"] = "missing"

    for c in [
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
        "search_result_count_log",
        "search_art_context_count_log",
        "search_exhibition_context_count_log",
        "search_source_count_log",
        "search_quality_x_log_area",
        "search_art_match_x_followers_log",
        "search_exhibition_x_career_stage",
    ]:
        f[c] = 0.0
    f["search_quality_grade"] = "missing"
    f["search_homonym_risk_grade"] = "missing"
    f["search_size_quality_bucket"] = f["size_bucket"].astype(str) + "__missing"

    adapter._apply_external_feature_interactions(f)
    return _normalize_model_input_frame(f.reindex(columns=feats))


def predict(adapter, frame, artist_key):
    q10 = float(np.asarray(adapter.cold_y2_models["q10"].predict(frame))[0])
    q50 = float(np.asarray(adapter.cold_y2_models["q50"].predict(frame))[0])
    q90 = float(np.asarray(adapter.cold_y2_models["q90"].predict(frame))[0])
    q40 = float(np.asarray(adapter.cold_qr1_q40_model.predict(frame))[0])
    qwidth = max(q90 - q10, 0.0)
    rep = adapter._apply_cold_y16_segment_correction(q50, qwidth)
    v = pd.DataFrame(
        [
            {
                "y18_qwidth_pred_log": rep,
                "lgb_q40_pred_log": q40,
                "quantile_width_log": qwidth,
                "artist_key": artist_key,
            }
        ]
    )
    out = adapter.cold_v03.apply(
        v, params=adapter.cold_v03_params, lookup=adapter.cold_v03_lookup
    ).iloc[0]
    return float(out["cold_defense_pred_price_krw"])


def mdape(actual_ln, pred_krw):
    actual = np.exp(np.asarray(actual_ln, dtype=float))
    pred = np.asarray(pred_krw, dtype=float)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {
        "n": len(ape),
        "MdAPE": round(float(np.median(ape)), 4),
        "MAPE": round(float(np.mean(ape)), 4),
        "W30": round(float(np.mean(ape <= 0.30)), 4),
        "median_ratio": round(float(np.median(pred / np.clip(actual, 1.0, None))), 4),
    }


def main():
    oof, sa, ar = load_rows()
    adapter = ReportModelProxyAdapter()
    feats = adapter.cold_refreeze_schema["pp_y2_feature_columns"]

    results = {}
    for mode in ["serving", "matched"]:
        preds, actuals, cb = [], [], []
        for _, r in sa.iterrows():
            area = float(r["area_cm2"]) if pd.notna(r["area_cm2"]) else 0.0
            side = float(np.sqrt(area)) if area > 0 else 0.0
            depth = 1.0 if bool(r.get("has_depth")) else 0.0
            fr = build_frame(
                adapter,
                feats,
                width=side,
                height=side,
                depth=depth,
                medium=r.get("medium_category"),
                support=r.get("support_type"),
                birth=r.get("artist_birth_year"),
                solo=r.get("solo_count"),
                group=r.get("group_count"),
                fair=r.get("fair_count"),
                mode=mode,
            )
            preds.append(predict(adapter, fr, str(r["artist_slug"]).replace("-", " ")))
            actuals.append(r["y_ln_price"])
            cb.append(r["cb_pred_ln_price"])
        for _, r in ar.iterrows():
            w = float(r["width_cm"]) if pd.notna(r["width_cm"]) else 0.0
            h = float(r["height_cm"]) if pd.notna(r["height_cm"]) else 0.0
            d = float(r["depth_cm"]) if pd.notna(r["depth_cm"]) else 0.0
            fr = build_frame(
                adapter,
                feats,
                width=w,
                height=h,
                depth=d,
                medium=r.get("medium"),
                support="unknown",
                birth=r.get("artist_birth_year"),
                solo=np.nan,
                group=np.nan,
                fair=np.nan,
                mode=mode,
            )
            preds.append(predict(adapter, fr, str(r["artist_slug"]).replace("-", " ")))
            actuals.append(r["y_ln_price"])
            cb.append(r["cb_pred_ln_price"])
        results[f"track6_{mode}"] = mdape(actuals, preds)

    cb_pred_krw = np.exp(np.asarray(actuals, dtype=float) * 0 + np.asarray(cb, dtype=float))
    results["catboost_audit4_parquet"] = mdape(actuals, cb_pred_krw)
    results["catboost_reported_v2"] = {
        "MdAPE": REPORTED_CATBOOST_MDAPE,
        "n": len(actuals),
        "note": "v2 source_calibration.json cold_overall.baseline_mdape (최종 모델)",
    }
    results["coverage"] = {
        "saatchi_rows": len(sa),
        "artsy_rows": len(ar),
        "total": int(len(sa) + len(ar)),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "v2_28k_comparison.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
