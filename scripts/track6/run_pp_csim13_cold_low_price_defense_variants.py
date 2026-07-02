#!/usr/bin/env python3
"""PP-CSIM13: Cold low-price defense variants.

Strict Cold follow-up for the current enterable_k160_q45 candidate.  The
experiment tests conservative low-price defenses that can be applied at
inference time without knowing actual price:

- lower quantile models q40/q35
- prediction/ref-price based q45 -> q40/q35 switching
- small downward adjustment for predicted low-price rows
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
from run_pp_cmeta4_user_input_meta_only import META_BUCKET_FEATURES, USER_META_CORE, load_user_meta_frames  # noqa: E402
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


EXP_ID = "PP-CSIM13"
SLUG = "PP-CSIM13_cold_low_price_defense_variants"
TITLE = "Cold 저가 구간 방어 변형 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim13_cold_low_price_defense_variants_summary.md"

TOP_K = 160

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


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fit_quantile(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def low_price_masks(frame: pd.DataFrame, pred_q45: np.ndarray) -> dict[str, np.ndarray]:
    ref_median = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_median"), errors="coerce").to_numpy(dtype=float)
    ref_iqr = pd.to_numeric(frame.get(f"artwork_sim_k{TOP_K}_ref_log_price_iqr"), errors="coerce").fillna(0.0).to_numpy(dtype=float)
    pred_price = np.exp(pred_q45)
    ref_price = np.exp(ref_median)
    return {
        "pred_lt_1m": pred_price < 1_000_000,
        "pred_lt_1p5m": pred_price < 1_500_000,
        "ref_lt_1p5m": np.isfinite(ref_price) & (ref_price < 1_500_000),
        "pred_ref_low": (pred_price < 1_500_000) & np.isfinite(ref_price) & (ref_price < 1_500_000),
        "pred_ref_low_stable": (pred_price < 1_500_000) & np.isfinite(ref_price) & (ref_price < 1_500_000) & (ref_iqr < 0.75),
    }


def metric_row(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred),
        **tail_counts(frame, pred),
    }
    if extra:
        row.update(extra)
    return row


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, mask_name: str = "") -> pd.DataFrame:
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
        "mask_name": mask_name,
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
        rows.append({
            "candidate": candidate,
            "split": split,
            "segment": str(segment),
            "n": int(len(group)),
            **metrics(
                group[["_track6_row_id", "actual_log", "actual_price"]].rename(
                    columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
                ),
                pred,
            ),
            **tail_counts(group.rename(columns={"actual_price": "price_krw"}), pred),
        })
    return pd.DataFrame(rows)


def add_candidate(
    rows: list[dict[str, Any]],
    pred_frames: list[pd.DataFrame],
    name: str,
    split: str,
    frame: pd.DataFrame,
    pred: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
    mask_name: str = "",
) -> None:
    rows.append(metric_row(name, split, frame, pred, policy, extra))
    pred_frames.append(prediction_frame(name, split, frame, pred, policy, mask_name))


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    artwork_features = unique(fs["cold_lgb"])
    enterable_base = unique(artwork_features + ENTERABLE_META + ENTERABLE_BUCKETS)
    required = unique(enterable_base + USER_META_CORE + META_BUCKET_FEATURES + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    assert_strict_cold_features(enterable_base, context=f"{EXP_ID}:enterable_base")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train,
        val,
        test,
        ARTWORK_SIM_FEATURES,
        prefix=f"artwork_sim_k{TOP_K}",
        top_k=TOP_K,
    )
    features = unique(enterable_base + art_ref_features)

    pred_by_alpha = {
        alpha: fit_quantile(train_art, val_art, test_art, features, alpha=alpha)
        for alpha in [0.45, 0.40, 0.35]
    }

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, frame in [("validation", val_art), ("test", test_art)]:
        q45 = pred_by_alpha[0.45][split]
        q40 = pred_by_alpha[0.40][split]
        q35 = pred_by_alpha[0.35][split]
        masks = low_price_masks(frame, q45)
        add_candidate(metric_rows, pred_frames, "enterable_k160_q45", split, frame, q45, "기준 enterable k160 q45", {"alpha": 0.45, "mask_rate": 0.0})
        add_candidate(metric_rows, pred_frames, "enterable_k160_q40", split, frame, q40, "전체 q40", {"alpha": 0.40, "mask_rate": 1.0})
        add_candidate(metric_rows, pred_frames, "enterable_k160_q35", split, frame, q35, "전체 q35", {"alpha": 0.35, "mask_rate": 1.0})

        candidates = [
            ("low_pred_q40", "pred_lt_1p5m", q40, "q45 예측가가 150만원 미만이면 q40 사용"),
            ("low_pred_ref_q40", "pred_ref_low", q40, "q45 예측가와 유사작품 기준가격이 모두 150만원 미만이면 q40 사용"),
            ("low_pred_ref_stable_q40", "pred_ref_low_stable", q40, "저가 예측 + 저가 기준가격 + 비교군 IQR < 0.75이면 q40 사용"),
            ("low_pred_ref_q35", "pred_ref_low", q35, "q45 예측가와 유사작품 기준가격이 모두 150만원 미만이면 q35 사용"),
        ]
        for name, mask_name, alt, policy in candidates:
            mask = masks[mask_name]
            pred = np.where(mask, alt, q45)
            add_candidate(
                metric_rows,
                pred_frames,
                name,
                split,
                frame,
                pred,
                policy,
                {"alpha": "q45_switch", "mask_name": mask_name, "mask_rate": float(np.mean(mask))},
                mask_name,
            )

        for delta in [0.03, 0.05, 0.08]:
            mask = masks["pred_ref_low_stable"]
            pred = np.where(mask, q45 - delta, q45)
            add_candidate(
                metric_rows,
                pred_frames,
                f"low_stable_down_{str(delta).replace('.', 'p')}",
                split,
                frame,
                pred,
                f"저가 안정 비교군이면 q45에서 {delta} log 하향",
                {"delta_log": delta, "mask_name": "pred_ref_low_stable", "mask_rate": float(np.mean(mask))},
                "pred_ref_low_stable",
            )

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
        "low_price_defense_variants": True,
        "top_k": TOP_K,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "mask_rate", "policy",
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
        "- 목적: 운영에서 알 수 있는 예측가/유사작품 기준가격 조건만으로 저가 구간 과대예측을 방어할 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
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
        "## 4. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- 저가 방어 후보는 actual price를 쓰지 않고, 사용 단계에서 알 수 있는 q45 예측값과 유사작품 기준가격만 사용한다.",
        "- 최종 채택은 전체 MdAPE 손실과 lt_1m APE > 5 감소가 동시에 확인될 때만 고려한다.",
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
