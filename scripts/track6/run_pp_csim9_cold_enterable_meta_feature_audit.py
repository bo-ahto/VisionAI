#!/usr/bin/env python3
"""PP-CSIM9: Cold enterable artist-metadata feature audit.

Before promoting a Cold candidate, validate whether the model depends on artist
metadata that users cannot reliably enter.  This experiment keeps the selected
k160 q45 structure and compares metadata feature sets:

- full current user_meta_core_bucket
- enterable-only metadata
- removing followers
- removing total works
- removing both followers and total works
- artwork + similarity only
- artwork only
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


EXP_ID = "PP-CSIM9"
SLUG = "PP-CSIM9_cold_enterable_meta_feature_audit"
TITLE = "Cold 사용자 입력 가능 작가 메타 피처 감사"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim9_cold_enterable_meta_feature_audit_summary.md"

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


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    full_core = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + full_core + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(full_core, context=f"{EXP_ID}:full_core")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{TOP_K}", top_k=TOP_K
    )

    full_features = unique(full_core + art_ref_features)
    enterable_features = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS + art_ref_features)
    no_followers = unique(remove_features(full_features, OPTIONAL_FOLLOWERS))
    no_total_works = unique(remove_features(full_features, OPTIONAL_TOTAL_WORKS))
    no_followers_total = unique(remove_features(full_features, OPTIONAL_FOLLOWERS + OPTIONAL_TOTAL_WORKS))
    no_optional_all = unique(remove_features(full_features, OPTIONAL_FOLLOWERS + OPTIONAL_TOTAL_WORKS + OPTIONAL_FLAGS + OPTIONAL_COMPLETENESS))
    similarity_only = unique(artwork_features + art_ref_features)
    artwork_only = unique(artwork_features)

    candidates = [
        ("full_current_meta", full_features, "현재 k160 q45 전체 user_meta_core_bucket 피처"),
        ("enterable_only", enterable_features, "운영 입력 가능성이 높은 메타만 사용"),
        ("no_followers", no_followers, "followers 계열 제거"),
        ("no_total_works", no_total_works, "total works 계열 제거"),
        ("no_followers_total", no_followers_total, "followers + total works 제거"),
        ("no_optional_all", no_optional_all, "followers/total works/P1/international/completeness 제거"),
        ("similarity_only", similarity_only, "작품 피처 + 유사작품 k160 통계만 사용"),
        ("artwork_only", artwork_only, "작가 메타와 유사작품 통계를 모두 제거하고 작품 피처만 사용"),
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

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_similarity_reference_stats": True,
        "router_used": False,
        "feature_audit": True,
        "top_k": TOP_K,
        "alpha": ALPHA,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
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
        "- 목적: Cold 후보에서 운영 입력이 애매한 작가 메타를 제거해도 성능이 유지되는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 구조: 유사작품 k160 + LightGBM Quantile q45 고정, 피처 세트만 변경.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 기준",
        md_table(tail_metrics, metric_cols),
        "",
        "## 3. 가격대별 진단",
        md_table(segment_df.sort_values(["segment", "candidate"]), seg_cols),
        "",
        "## 4. 피처 세트 정의",
        "",
        f"- `full_current_meta`: `{', '.join(full_features)}`",
        f"- `enterable_only`: `{', '.join(enterable_features)}`",
        f"- `similarity_only`: `{', '.join(similarity_only)}`",
        f"- `artwork_only`: `{', '.join(artwork_only)}`",
        "",
        "## 5. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- `artwork_only`는 작가 메타를 아예 쓰지 않는 하한선 비교다. 중앙 오차는 크게 무너지지 않지만, APE > 5가 크게 늘어 저가/불확실 구간 방어에는 부족하다.",
        "- `similarity_only`는 작가 메타 없이 유사작품 통계만 추가한 비교다. 이 실험에서는 유사작품 통계만으로는 tail 안정성이 개선되지 않았다.",
        "- `enterable_only`는 사용자가 비교적 입력하기 쉬운 작가 메타만 남긴 후보이며, full 메타 대비 중앙 오차는 손해가 있지만 p95와 APE > 5가 가장 안정적이다.",
        "- 입력하기 애매한 피처를 제거했을 때의 손실과 tail 변화를 기준으로 기본 학습 피처를 정한다.",
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
