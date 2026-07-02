#!/usr/bin/env python3
"""PP-CSIM11: Cold expanded gallery-tier mapping validation.

Validate whether expanded gallery-tier mapping can improve strict Cold.
The mapping combines frozen validated Track4 gallery tiers, source raw gallery
tiers, and exact matches to the curated gallery tier dictionary.
"""
from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cold_experiment_harness import assert_no_artist_lookup_postprocess, assert_strict_cold_features, strict_cold_run_summary  # noqa: E402
from run_pp_cmeta4_user_input_meta_only import (  # noqa: E402
    META_BUCKET_FEATURES,
    USER_META_CORE,
    candidate_defs,
    load_user_meta_frames,
)
from run_pp_csim1_cold_similarity_reference import (  # noqa: E402
    ARTIST_SIM_FEATURES,
    ARTWORK_SIM_FEATURES,
    compute_reference_stats,
    html_table,
    json_clean,
    lgbm_quantile_model,
    md_table,
    normalize_for_model,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM11"
SLUG = "PP-CSIM11_cold_gallery_tier_expanded_mapping_validation"
TITLE = "Cold 확장 갤러리 티어 매핑 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim11_cold_gallery_tier_expanded_mapping_validation_summary.md"
GALLERY_AUDIT = REPO / "data" / "track4_gallery_metadata_audit.csv"
GALLERY_DICTIONARY = REPO / "data" / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
TRACK4_RAW_COLLECTED = REPO / "data" / "track4_primary_market_raw_collected.csv"

TOP_K = 160
ALPHA = 0.45

ENTERABLE_META = [
    "artist_meta_birth_year",
    "artist_meta_career_stage",
    "artist_meta_birth_year_missing",
    "artist_meta_career_stage_missing",
    "artist_meta_nationality",
]

ENTERABLE_BUCKETS = [
    "artist_birth_period_bucket",
    "artist_career_stage_bucket",
    "medium_birth_period_bucket",
    "career_size_bucket",
]

OPTIONAL_FOLLOWERS = [
    "artist_meta_followers",
    "artist_meta_followers_log",
    "artist_meta_followers_missing",
    "artist_followers_bucket",
]

OPTIONAL_TOTAL_WORKS = [
    "artist_meta_total_works",
    "artist_meta_total_works_log",
    "artist_meta_total_works_missing",
    "artist_inventory_bucket",
]

OPTIONAL_FLAGS = [
    "artist_meta_is_p1_flag",
    "artist_meta_has_international_flag",
]

OPTIONAL_COMPLETENESS = [
    "artist_meta_completeness_bucket",
    "support_meta_completeness_bucket",
]

GALLERY_TIER_FEATURES = [
    "user_gallery_tier_score",
    "user_gallery_tier_available_flag",
    "user_gallery_tier_missing_flag",
    "user_gallery_tier_bucket",
]

GALLERY_CONTEXT_FEATURES = GALLERY_TIER_FEATURES + [
    "user_gallery_ref_type",
    "user_gallery_audit_status",
    "user_gallery_category",
    "user_gallery_mapping_source",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fit_quantile(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float = ALPHA,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], y)
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, features: list[str]) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
        "n_features": len(features),
        "features": ",".join(features),
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


def segment_summary(predictions: pd.DataFrame, candidate: str, split: str) -> pd.DataFrame:
    df = predictions[predictions["candidate"].eq(candidate) & predictions["split"].eq(split)].copy()
    if df.empty:
        return pd.DataFrame()
    df["actual_price_band"] = pd.cut(
        pd.to_numeric(df["actual_price"], errors="coerce"),
        bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
        include_lowest=True,
    ).astype("string")
    rows = []
    for segment, group in df.groupby("actual_price_band", dropna=False, observed=False):
        pred = group["pred_log"].to_numpy(dtype=float)
        md = metrics(
            group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
            ),
            pred,
        )
        rows.append({
            "candidate": candidate,
            "split": split,
            "segment": str(segment),
            "n": int(len(group)),
            **md,
            **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
        })
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_empty_"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            value = row[col]
            vals.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def remove_features(features: list[str], remove: list[str]) -> list[str]:
    remove_set = set(remove)
    return [feature for feature in features if feature not in remove_set]


def normalize_gallery_name(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value).strip().lower())
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b(gallery|galerie|galleria|art|contemporary|seoul)\b", " ", text)
    text = text.replace("갤러리", "").replace("화랑", "")
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def load_gallery_dictionary() -> pd.DataFrame:
    dictionary = pd.read_csv(GALLERY_DICTIONARY)
    dictionary = dictionary.dropna(subset=["명칭"]).copy()
    dictionary["gallery_norm"] = dictionary["명칭"].map(normalize_gallery_name)
    dictionary = dictionary[dictionary["gallery_norm"].ne("")]
    dictionary = dictionary.drop_duplicates("gallery_norm", keep="first")
    return dictionary.rename(columns={"티어": "dict_tier", "분류": "dict_category", "명칭": "dict_gallery_name"})


def load_gallery_audit_map() -> pd.DataFrame:
    # Track6 model frames keep only `_track6_row_id`, which is the global row
    # position in the Track4 cleaned table. `track4_source_row_index` is
    # source-local and is not unique across sources.
    audit = pd.read_csv(GALLERY_AUDIT, engine="python").reset_index(names="_track6_row_id")
    audit = audit[[
        "_track6_row_id",
        "track4_source",
        "track4_source_row_index",
        "gallery_name_raw",
        "gallery_key",
        "gallery_tier_validated",
        "gallery_ref_type",
        "gallery_audit_status",
    ]]
    raw_cols = [
        "track4_source",
        "track4_source_row_index",
        "saatchi__gallery_name",
        "saatchi__gallery_type",
        "saatchi__gallery_tier",
        "artsy__gallery_name",
        "artsy__gallery_type",
        "gallery_primary__gallery_tier",
        "gallery_primary__gallery_name(KR)",
        "gallery_primary__gallery_name(EN)",
        "gallery_primary__gallery_country",
    ]
    raw = pd.read_csv(TRACK4_RAW_COLLECTED, usecols=lambda col: col in raw_cols, low_memory=False)
    raw = raw.drop_duplicates(["track4_source", "track4_source_row_index"], keep="first")
    out = audit.merge(raw, on=["track4_source", "track4_source_row_index"], how="left")

    raw_name = out["gallery_name_raw"].copy()
    for col in [
        "saatchi__gallery_name",
        "artsy__gallery_name",
        "gallery_primary__gallery_name(KR)",
        "gallery_primary__gallery_name(EN)",
    ]:
        raw_name = raw_name.fillna(out[col])
    out["user_gallery_name_raw"] = raw_name
    out["gallery_norm"] = out["user_gallery_name_raw"].map(normalize_gallery_name)

    dictionary = load_gallery_dictionary()
    out = out.merge(dictionary[["gallery_norm", "dict_tier", "dict_category", "dict_gallery_name"]], on="gallery_norm", how="left")

    source_tier = pd.to_numeric(out["saatchi__gallery_tier"], errors="coerce")
    source_tier = source_tier.fillna(pd.to_numeric(out["gallery_primary__gallery_tier"], errors="coerce"))
    source_tier_label = np.where(source_tier.notna(), "raw_tier_" + source_tier.astype("Int64").astype(str), pd.NA)
    source_tier_score = np.where(source_tier.notna(), (6.0 - source_tier.clip(lower=1, upper=5)), np.nan)

    tier_score_map = {"Tier A": 5.0, "Tier B": 4.0, "Tier C": 3.0, "Tier D": 2.0, "Tier E": 1.0}
    validated_score = out["gallery_tier_validated"].map(tier_score_map)
    dict_score = out["dict_tier"].map(tier_score_map)

    out["user_gallery_tier_label"] = out["gallery_tier_validated"]
    out["user_gallery_tier_label"] = out["user_gallery_tier_label"].fillna(pd.Series(source_tier_label, index=out.index))
    out["user_gallery_tier_label"] = out["user_gallery_tier_label"].fillna(out["dict_tier"])
    out["user_gallery_tier_score_raw"] = validated_score.fillna(pd.Series(source_tier_score, index=out.index)).fillna(dict_score)
    out["user_gallery_mapping_source"] = np.select(
        [
            out["gallery_tier_validated"].notna(),
            source_tier.notna(),
            out["dict_tier"].notna(),
        ],
        ["validated_audit", "source_raw_tier", "dictionary_exact"],
        default="unmatched",
    )
    out["user_gallery_ref_type_expanded"] = out["gallery_ref_type"].fillna(out["dict_category"]).fillna(out["saatchi__gallery_type"]).fillna(out["artsy__gallery_type"])
    out["user_gallery_audit_status_expanded"] = np.where(out["user_gallery_mapping_source"].eq("unmatched"), "gallery_tier_unmatched", "ok")
    return out[[
        "_track6_row_id",
        "user_gallery_name_raw",
        "gallery_norm",
        "gallery_key",
        "user_gallery_tier_label",
        "user_gallery_tier_score_raw",
        "user_gallery_mapping_source",
        "user_gallery_ref_type_expanded",
        "user_gallery_audit_status_expanded",
    ]].rename(columns={
        "gallery_key": "user_gallery_key",
        "user_gallery_tier_label": "user_gallery_tier_validated",
        "user_gallery_ref_type_expanded": "user_gallery_ref_type",
        "user_gallery_audit_status_expanded": "user_gallery_audit_status",
    })


def load_gallery_dictionary_summary() -> dict[str, Any]:
    dictionary = pd.read_csv(GALLERY_DICTIONARY)
    return {
        "path": str(GALLERY_DICTIONARY.relative_to(REPO)),
        "n_entries": int(len(dictionary)),
        "tier_counts": {str(k): int(v) for k, v in dictionary["티어"].value_counts(dropna=False).to_dict().items()},
        "category_counts": {str(k): int(v) for k, v in dictionary["분류"].value_counts(dropna=False).to_dict().items()},
    }


def add_gallery_features(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    gallery = load_gallery_audit_map()
    out_frames: list[pd.DataFrame] = []
    for frame in frames:
        out = frame.merge(gallery, on="_track6_row_id", how="left")
        tier = out["user_gallery_tier_validated"].astype("string")
        out["user_gallery_tier_score"] = pd.to_numeric(out["user_gallery_tier_score_raw"], errors="coerce")
        out["user_gallery_tier_available_flag"] = out["user_gallery_tier_score"].notna().astype(float)
        out["user_gallery_tier_missing_flag"] = out["user_gallery_tier_score"].isna().astype(float)
        out["user_gallery_tier_score"] = out["user_gallery_tier_score"].fillna(0.0)
        out["user_gallery_tier_bucket"] = tier.fillna("user_gallery_tier_missing").replace({"": "user_gallery_tier_missing"})
        out["user_gallery_ref_type"] = out["user_gallery_ref_type"].astype("string").fillna("user_gallery_ref_missing").replace({"": "user_gallery_ref_missing"})
        out["user_gallery_audit_status"] = out["user_gallery_audit_status"].astype("string").fillna("user_gallery_audit_missing").replace({"": "user_gallery_audit_missing"})
        out["user_gallery_mapping_source"] = out["user_gallery_mapping_source"].astype("string").fillna("unmatched").replace({"": "unmatched"})
        out["user_gallery_category"] = np.where(
            out["user_gallery_tier_available_flag"].to_numpy(dtype=float) > 0,
            out["user_gallery_ref_type"].astype(str),
            "user_gallery_category_missing",
        )
        out_frames.append(out)
    return out_frames


def gallery_coverage(frames: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for split, frame in frames:
        rows.append({
            "split": split,
            "n": int(len(frame)),
            "gallery_tier_available_n": int(pd.to_numeric(frame["user_gallery_tier_available_flag"], errors="coerce").fillna(0).sum()),
            "gallery_tier_available_rate": float(pd.to_numeric(frame["user_gallery_tier_available_flag"], errors="coerce").fillna(0).mean()),
            "gallery_audit_ok_n": int(frame["user_gallery_audit_status"].astype(str).eq("ok").sum()),
            "mapping_sources": json.dumps(frame["user_gallery_mapping_source"].astype(str).value_counts().to_dict(), ensure_ascii=False),
        })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    full_core = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + full_core + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)
    train, val, test = add_gallery_features([train, val, test])

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(full_core, context=f"{EXP_ID}:full_core")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{TOP_K}", top_k=TOP_K
    )

    full_features = unique(full_core + art_ref_features)
    enterable_features = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS + art_ref_features)
    similarity_only = unique(artwork_features + art_ref_features)
    artwork_only = unique(artwork_features)
    enterable_gallery_tier = unique(enterable_features + GALLERY_TIER_FEATURES)
    enterable_gallery_context = unique(enterable_features + GALLERY_CONTEXT_FEATURES)
    similarity_gallery_context = unique(similarity_only + GALLERY_CONTEXT_FEATURES)
    artwork_gallery_context = unique(artwork_only + GALLERY_CONTEXT_FEATURES)

    candidates = [
        ("enterable_only", enterable_features, "운영 입력 가능성이 높은 작가 메타만 사용"),
        ("enterable_gallery_tier", enterable_gallery_tier, "enterable_only + 갤러리 티어 점수/가용 flag"),
        ("enterable_gallery_context", enterable_gallery_context, "enterable_only + 갤러리 티어/유형/감사 상태"),
        ("similarity_only", similarity_only, "작가 메타 없이 작품 피처 + 유사작품 k160 통계만 사용"),
        ("similarity_gallery_context", similarity_gallery_context, "similarity_only + 갤러리 티어/유형/감사 상태"),
        ("artwork_only", artwork_only, "작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용"),
        ("artwork_gallery_context", artwork_gallery_context, "artwork_only + 갤러리 티어/유형/감사 상태"),
        ("full_current_meta", full_features, "현재 k160 q45 전체 user_meta_core_bucket 피처 참고"),
    ]

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for name, features, policy in candidates:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")
        if any(feature.startswith("search_") for feature in features):
            raise ValueError(f"{name} includes forbidden search_* feature")
        preds = fit_quantile(train_art, val_art, test_art, features, alpha=ALPHA)
        for split, frame in [("validation", val_art), ("test", test_art)]:
            pred = preds[split]
            metric_rows.append(metric_row(name, split, frame, pred, policy, features))
            pred_frames.append(prediction_frame(name, split, frame, pred, policy))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    segment_df = pd.concat([
        segment_summary(predictions_df, candidate, "test")
        for candidate in metrics_df[metrics_df["split"].eq("test")]["candidate"].unique()
    ], ignore_index=True)
    coverage_df = gallery_coverage([("train", train_art), ("validation", val_art), ("test", test_art)])
    dictionary_summary = load_gallery_dictionary_summary()

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "gallery_tier_feature_validation": True,
        "gallery_audit_source": str(GALLERY_AUDIT.relative_to(REPO)),
        "gallery_dictionary": dictionary_summary,
        "top_k": TOP_K,
        "alpha": ALPHA,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    coverage_df.to_csv(OUT / "gallery_coverage.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "n_features", "policy",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5"]
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    tail_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "p95_APE", "MAPE"])
    best_mdape = test_metrics.iloc[0]["candidate"]
    best_tail = tail_metrics.iloc[0]["candidate"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: 보유 원천 데이터의 갤러리명/원천 tier/티어 리스트 exact match를 합쳐 갤러리 티어 coverage를 확장했을 때 Cold 성능이 개선되는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 구조: 유사작품 k160 + LightGBM Quantile q45 고정, 확장 갤러리 피처 추가 여부만 변경.",
        f"- 갤러리 사전: `{dictionary_summary['path']}` / {dictionary_summary['n_entries']}개 항목.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 기준",
        md_table(tail_metrics, metric_cols),
        "",
        "## 3. 갤러리 티어 커버리지",
        md_table(coverage_df, ["split", "n", "gallery_tier_available_n", "gallery_tier_available_rate", "gallery_audit_ok_n", "mapping_sources"]),
        "",
        "## 4. 가격대별 진단",
        md_table(segment_df.sort_values(["segment", "candidate"]), seg_cols),
        "",
        "## 5. 피처 세트 정의",
        "",
        f"- `enterable_only`: `{', '.join(enterable_features)}`",
        f"- `enterable_gallery_tier`: `{', '.join(enterable_gallery_tier)}`",
        f"- `enterable_gallery_context`: `{', '.join(enterable_gallery_context)}`",
        f"- `similarity_only`: `{', '.join(similarity_only)}`",
        f"- `similarity_gallery_context`: `{', '.join(similarity_gallery_context)}`",
        f"- `artwork_only`: `{', '.join(artwork_only)}`",
        f"- `artwork_gallery_context`: `{', '.join(artwork_gallery_context)}`",
        f"- `full_current_meta`: `{', '.join(full_features)}`",
        "",
        "## 6. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- raw source tier는 Saatchi/1차시장 원천 tier를 그대로 사용하므로, 운영 사전 기준으로 쓰려면 갤러리명 alias와 티어 정책 검수가 추가로 필요하다.",
        "- 이번 실험은 갤러리 티어 coverage를 늘렸을 때의 가능성 검증이며, 최종 채택 전에는 매핑 사전 버전 고정과 사람이 검수한 alias 확장이 필요하다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 결과: MdAPE 기준</h2>{html_table(test_metrics, metric_cols)}
<h2>Test 결과: APE &gt; 5 기준</h2>{html_table(tail_metrics, metric_cols)}
<h2>가격대별 진단</h2>{html_table(segment_df.sort_values(['segment', 'candidate']), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
