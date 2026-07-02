#!/usr/bin/env python3
"""PP-CSIM27: strict Cold gallery/profile grouping validation.

목적:
  Cold 예측에서 artist_key 가격 이력 lookup 없이, 작가 메타/갤러리/전시
  문맥을 더 세밀한 유사 그룹핑에 사용할 수 있는지 검증한다.

엄격 Cold 조건:
  - artist_key를 모델 피처로 사용하지 않는다.
  - 같은 작가 가격 이력을 직접 lookup하지 않는다.
  - artist_key 기반 보정 후처리를 사용하지 않는다.
  - search_* / 외부 live 검색 피처를 사용하지 않는다.

이번 실험의 비교 축:
  1. 기본 작품+작가 메타 + 유사작품 k80 기준
  2. 갤러리/전시 문맥을 모델 입력에 직접 추가
  3. 갤러리/전시 문맥을 유사 이웃 선택에만 추가
  4. 둘 다 추가
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

from cold_experiment_harness import (  # noqa: E402
    assert_no_artist_lookup_postprocess,
    assert_strict_cold_features,
    strict_cold_run_summary,
)
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import unique  # noqa: E402


EXP_ID = "PP-CSIM27"
SLUG = "PP-CSIM27_cold_gallery_profile_grouping"
TITLE = "Cold 갤러리/작가 프로필 유사 그룹핑 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim27_cold_gallery_profile_grouping_summary.md"

FEATURE_STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"
TOP_K = 80
ALPHA = 0.50

ARTWORK_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "size_bucket",
    "support_size_bucket",
]

CORE_ARTIST_META = [
    "artist_meta_birth_year",
    "artist_meta_total_works",
    "artist_meta_followers",
    "artist_meta_career_stage",
    "artist_meta_total_works_log",
    "artist_meta_followers_log",
    "artist_meta_birth_year_missing",
    "artist_meta_total_works_missing",
    "artist_meta_followers_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_is_p1_flag",
    "artist_meta_has_international_flag",
    "artist_meta_nationality",
]

PROFILE_FEATURES = [
    "artist_exhibition_solo_count_log",
    "artist_exhibition_group_count_log",
    "artist_exhibition_fair_count_log",
    "artist_exhibition_total_count_log",
    "artist_exhibition_available_count",
    "gallery_tier_raw_numeric",
    "gallery_tier_raw_available_flag",
    "gallery_tier_validated_score",
    "gallery_tier_validated_available_flag",
    "gallery_tier_any_available_flag",
    "gallery_city_count_log",
    "gallery_tier_raw_bucket",
    "gallery_tier_validated",
    "gallery_ref_type",
    "gallery_audit_status",
    "gallery_feature_source",
    "gallery_tier_x_exhibition_total_log",
    "exhibition_size_bucket",
    "gallery_exhibition_bucket",
]

GENERATED_PROFILE_BUCKETS = [
    "profile_exhibition_bucket",
    "profile_gallery_tier_bucket",
    "profile_gallery_source_bucket",
    "profile_gallery_exhibition_bucket",
    "profile_career_gallery_bucket",
    "profile_medium_gallery_bucket",
    "profile_size_exhibition_bucket",
]

ARTWORK_SIM_FEATURES = ARTWORK_FEATURES + [
    "medium_category",
    "support_category",
]

ARTIST_META_SIM_FEATURES = CORE_ARTIST_META + [
    "artist_birth_period_bucket",
    "artist_career_stage_bucket",
    "artist_inventory_bucket",
    "artist_followers_bucket",
]

PROFILE_SIM_FEATURES = ARTIST_META_SIM_FEATURES + PROFILE_FEATURES + GENERATED_PROFILE_BUCKETS


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def safe_str(frame: pd.DataFrame, col: str, default: str = "__MISSING__") -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="string")
    return frame[col].astype("string").fillna(default).replace({"": default})


def q_bucket(series: pd.Series, labels: list[str], missing: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    if valid.nunique() < 3:
        return pd.Series(missing, index=series.index, dtype="string")
    edges = np.unique(np.nanquantile(valid, np.linspace(0, 1, len(labels) + 1)))
    if len(edges) <= 2:
        return pd.Series(missing, index=series.index, dtype="string")
    bucket = pd.cut(numeric, bins=edges, labels=labels[: len(edges) - 1], include_lowest=True, duplicates="drop")
    return bucket.astype("string").fillna(missing)


def add_profile_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    birth = pd.to_numeric(out.get("artist_meta_birth_year"), errors="coerce")
    out["artist_birth_period_bucket"] = pd.cut(
        birth,
        bins=[-np.inf, 1900, 1949, 1979, np.inf],
        labels=["pre_1900", "1900_1949", "1950_1979", "1980_plus"],
        include_lowest=True,
    ).astype("string").fillna("birth_missing")
    career = pd.to_numeric(out.get("artist_meta_career_stage"), errors="coerce")
    out["artist_career_stage_bucket"] = pd.cut(
        career,
        bins=[-np.inf, 5, 15, 30, np.inf],
        labels=["career_new", "career_early", "career_mid", "career_long"],
        include_lowest=True,
    ).astype("string").fillna("career_missing")
    out["artist_inventory_bucket"] = q_bucket(out.get("artist_meta_total_works_log", pd.Series(index=out.index)), ["inv_low", "inv_mid", "inv_high", "inv_top"], "inv_missing")
    out["artist_followers_bucket"] = q_bucket(out.get("artist_meta_followers_log", pd.Series(index=out.index)), ["followers_low", "followers_mid", "followers_high", "followers_top"], "followers_missing")

    exhibition_total = pd.to_numeric(out.get("artist_exhibition_total_count", 0.0), errors="coerce").fillna(0.0)
    out["profile_exhibition_bucket"] = pd.cut(
        exhibition_total,
        bins=[-np.inf, 0, 2, 8, np.inf],
        labels=["exh_none", "exh_low", "exh_mid", "exh_high"],
        include_lowest=True,
    ).astype("string").fillna("exh_none")

    raw_tier = pd.to_numeric(out.get("gallery_tier_raw_numeric", np.nan), errors="coerce")
    validated = pd.to_numeric(out.get("gallery_tier_validated_score", np.nan), errors="coerce")
    any_gallery = pd.to_numeric(out.get("gallery_tier_any_available_flag", 0.0), errors="coerce").fillna(0.0)
    tier_score = validated.fillna(raw_tier)
    out["profile_gallery_tier_bucket"] = np.where(
        any_gallery <= 0,
        "gallery_missing",
        pd.cut(
            tier_score,
            bins=[-np.inf, 2, 4, np.inf],
            labels=["gallery_low", "gallery_mid", "gallery_high"],
            include_lowest=True,
        ).astype("string").fillna("gallery_unknown"),
    )
    out["profile_gallery_source_bucket"] = safe_str(out, "gallery_feature_source")
    out["profile_gallery_exhibition_bucket"] = out["profile_gallery_tier_bucket"].astype(str) + "__" + out["profile_exhibition_bucket"].astype(str)
    out["profile_career_gallery_bucket"] = out["artist_career_stage_bucket"].astype(str) + "__" + out["profile_gallery_tier_bucket"].astype(str)
    out["profile_medium_gallery_bucket"] = safe_str(out, "medium_category").astype(str) + "__" + out["profile_gallery_tier_bucket"].astype(str)
    out["profile_size_exhibition_bucket"] = safe_str(out, "size_bucket").astype(str) + "__" + out["profile_exhibition_bucket"].astype(str)
    return out


def load_frames(required_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(FEATURE_STORE, low_memory=False)
    frame = add_profile_buckets(frame)
    required = unique(["_track6_row_id", "price_krw", "ln_price_krw", "split_name"] + required_features)
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing feature-store columns: {missing}")
    frame = frame[required].copy()
    return (
        frame[frame["split_name"].eq("train")].drop(columns=["split_name"]).reset_index(drop=True),
        frame[frame["split_name"].eq("validation")].drop(columns=["split_name"]).reset_index(drop=True),
        frame[frame["split_name"].eq("test")].drop(columns=["split_name"]).reset_index(drop=True),
    )


def fit_predict(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    model = lgbm_quantile_model(train_n, features, alpha=ALPHA)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, features: list[str], sim_features: list[str]) -> dict[str, Any]:
    base = metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred)
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **base,
        **tail_counts(frame, pred),
        "n_model_features": len(features),
        "n_similarity_features": len(sim_features),
    }


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str) -> pd.DataFrame:
    return pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": pred,
        "pred_price": np.exp(pred),
        "policy": policy,
    })


def coverage_summary(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, frame in [("train", train), ("validation", val), ("test", test)]:
        rows.append({
            "split": split,
            "n": int(len(frame)),
            "gallery_any_n": int(pd.to_numeric(frame["gallery_tier_any_available_flag"], errors="coerce").fillna(0).sum()),
            "gallery_any_rate": float(pd.to_numeric(frame["gallery_tier_any_available_flag"], errors="coerce").fillna(0).mean()),
            "gallery_validated_n": int(pd.to_numeric(frame["gallery_tier_validated_available_flag"], errors="coerce").fillna(0).sum()),
            "gallery_validated_rate": float(pd.to_numeric(frame["gallery_tier_validated_available_flag"], errors="coerce").fillna(0).mean()),
            "exhibition_available_n": int(pd.to_numeric(frame["artist_exhibition_available_count"], errors="coerce").fillna(0).gt(0).sum()),
            "exhibition_available_rate": float(pd.to_numeric(frame["artist_exhibition_available_count"], errors="coerce").fillna(0).gt(0).mean()),
        })
    return pd.DataFrame(rows)


def segment_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, split), group_all in predictions.groupby(["candidate", "split"], observed=False):
        work = group_all.copy()
        work["actual_price_band"] = pd.cut(
            pd.to_numeric(work["actual_price"], errors="coerce"),
            bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
            labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
            include_lowest=True,
        ).astype("string")
        for segment, group in work.groupby("actual_price_band", observed=False):
            frame = group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
            )
            pred = group["pred_log"].to_numpy(dtype=float)
            rows.append({
                "candidate": candidate,
                "split": split,
                "segment": str(segment),
                "n": int(len(group)),
                **metrics(frame, pred),
                **tail_counts(frame, pred),
            })
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, coverage_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "APE_gt_2", "APE_gt_5", "APE_gt_10", "n_model_features", "n_similarity_features", "policy",
    ]
    cov_cols = ["split", "n", "gallery_any_n", "gallery_any_rate", "gallery_validated_n", "gallery_validated_rate", "exhibition_available_n", "exhibition_available_rate"]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]
    test_sorted = metrics_df[metrics_df["split"].eq("test")].sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5"])
    val_sorted = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "p95_APE", "MdAPE", "APE_gt_5"])

    feature_lines = []
    for cand in candidates:
        feature_lines.extend([
            f"### {cand['name']}",
            f"- 정책: {cand['policy']}",
            f"- 모델 입력 피처: `{', '.join(cand['model_features'])}`",
            f"- 유사 이웃 선택 피처: `{', '.join(cand['sim_features'])}`",
            "",
        ])

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: Cold에서 갤러리/전시/작가 프로필 문맥을 가격군 그룹핑에 사용할 수 있는지 검증한다.",
        "- 엄격 조건: `artist_key`, 동일 작가 가격 이력, artist_key lookup, `search_*`, 외부 live 검색 미사용.",
        "- 기준: LightGBM Quantile q50, 유사 이웃 기준가격 통계 k80.",
        "",
        "## 1. Test 결과",
        md_table(test_sorted, metric_cols),
        "",
        "## 2. Validation 결과",
        md_table(val_sorted, metric_cols),
        "",
        "## 3. 갤러리/전시 피처 커버리지",
        md_table(coverage_df, cov_cols),
        "",
        "## 4. 가격대별 Test 진단",
        md_table(seg_df[seg_df["split"].eq("test")].sort_values(["candidate", "segment"]), seg_cols),
        "",
        "## 5. 후보 정의",
        *feature_lines,
        "## 6. 해석",
        "",
        "- 갤러리/전시 문맥이 좋아 보이더라도 raw source tier 비중이 높으면 운영 채택 전에 입력 방식과 tier 사전 버전을 고정해야 한다.",
        "- `gallery_validated_rate`가 낮으면 검증된 갤러리 티어만으로는 효과를 기대하기 어렵고, 사용자 선택형 갤러리 입력 또는 운영 검수 사전이 필요하다.",
        "- 이번 실험에서 우세 후보는 Cold 운영 후보로 바로 승격하기보다, 동일 split 재현성과 APE > 5 tail risk를 함께 보고 후속 freezing 대상으로 삼는다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}code{{background:#eef2f7;padding:1px 4px;border-radius:4px}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<p>엄격 Cold 조건: artist_key, 동일 작가 가격 이력, artist_key lookup, search_* 및 외부 live 검색 미사용.</p>
<h2>Test 결과</h2>{html_table(test_sorted, metric_cols)}
<h2>Validation 결과</h2>{html_table(val_sorted, metric_cols)}
<h2>갤러리/전시 피처 커버리지</h2>{html_table(coverage_df, cov_cols)}
<h2>가격대별 Test 진단</h2>{html_table(seg_df[seg_df['split'].eq('test')].sort_values(['candidate', 'segment']), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)

    base_model_features = unique(ARTWORK_FEATURES + CORE_ARTIST_META)
    profile_model_features = unique(base_model_features + PROFILE_FEATURES + GENERATED_PROFILE_BUCKETS)
    base_sim_features = unique(ARTWORK_SIM_FEATURES)
    profile_sim_features = unique(ARTWORK_SIM_FEATURES + ARTIST_META_SIM_FEATURES + PROFILE_FEATURES + GENERATED_PROFILE_BUCKETS)
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

    train, val, test = load_frames(required)

    candidates = [
        {
            "name": "base_artwork_similarity_k80",
            "model_features": base_model_features,
            "sim_features": base_sim_features,
            "policy": "작품+기본 작가 메타, 유사 이웃은 작품 조건만 사용",
        },
        {
            "name": "direct_gallery_profile_k80",
            "model_features": profile_model_features,
            "sim_features": base_sim_features,
            "policy": "갤러리/전시 문맥을 모델 입력에 직접 추가",
        },
        {
            "name": "similarity_gallery_profile_k80",
            "model_features": base_model_features,
            "sim_features": profile_sim_features,
            "policy": "갤러리/전시 문맥은 유사 이웃 선택에만 사용",
        },
        {
            "name": "direct_and_similarity_gallery_profile_k80",
            "model_features": profile_model_features,
            "sim_features": profile_sim_features,
            "policy": "갤러리/전시 문맥을 모델 입력과 유사 이웃 선택에 모두 사용",
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
        "top_k": TOP_K,
        "alpha": ALPHA,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    coverage_df.to_csv(OUT / "gallery_profile_coverage.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, coverage_df, seg_df, summary, candidates)
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
