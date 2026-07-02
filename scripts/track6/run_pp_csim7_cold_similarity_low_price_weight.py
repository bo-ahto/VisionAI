#!/usr/bin/env python3
"""PP-CSIM7: low-price weighted training for Cold artwork_similarity_k160.

Router-free model-training follow-up to PP-CSIM6.  Output caps did not reduce
APE > 5, so this experiment changes training itself:

- keep artwork_similarity_k160 features
- increase training weight for lower actual-price bands
- optionally use lower quantile alpha to reduce over-prediction

The goal is to reduce low-price over-prediction and APE > 5 without losing the
overall gains from k160.
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
from run_pp_cmeta4_user_input_meta_only import candidate_defs, load_user_meta_frames  # noqa: E402
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


EXP_ID = "PP-CSIM7"
SLUG = "PP-CSIM7_cold_similarity_low_price_weight"
TITLE = "Cold 유사작품 k160 저가구간 가중 학습 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim7_cold_similarity_low_price_weight_summary.md"

TOP_K = 160

WEIGHT_VARIANTS = [
    ("k160_alpha50_unweighted", 0.50, 1.0, 1.0, "기준: q50, 가중치 없음"),
    ("k160_alpha45_unweighted", 0.45, 1.0, 1.0, "q45, 가중치 없음"),
    ("k160_alpha40_unweighted", 0.40, 1.0, 1.0, "q40, 가중치 없음"),
    ("k160_low_w2_alpha50", 0.50, 2.0, 1.25, "저가 2.0배 / 1m~3m 1.25배 / q50"),
    ("k160_low_w3_alpha50", 0.50, 3.0, 1.50, "저가 3.0배 / 1m~3m 1.5배 / q50"),
    ("k160_low_w2_alpha45", 0.45, 2.0, 1.25, "저가 2.0배 / 1m~3m 1.25배 / q45"),
    ("k160_low_w3_alpha45", 0.45, 3.0, 1.50, "저가 3.0배 / 1m~3m 1.5배 / q45"),
    ("k160_low_w2_alpha40", 0.40, 2.0, 1.25, "저가 2.0배 / 1m~3m 1.25배 / q40"),
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def price_weights(frame: pd.DataFrame, low_weight: float, mid_weight: float) -> np.ndarray:
    price = pd.to_numeric(frame["price_krw"], errors="coerce").to_numpy(dtype=float)
    weights = np.ones(len(frame), dtype=float)
    weights[price < 1_000_000] = low_weight
    weights[(price >= 1_000_000) & (price < 3_000_000)] = mid_weight
    return weights


def fit_weighted_quantile(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    *,
    alpha: float,
    low_weight: float,
    mid_weight: float,
) -> dict[str, np.ndarray]:
    train_n, val_n, test_n = normalize_for_model(train, val, test, features)
    y = train_n["ln_price_krw"].to_numpy(dtype=float)
    model = lgbm_quantile_model(train_n, features, alpha=alpha)
    sample_weight = price_weights(train_n, low_weight, mid_weight)
    model.fit(train_n[features], y, model__sample_weight=sample_weight)
    return {
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
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


def prediction_frame(candidate: str, split: str, frame: pd.DataFrame, pred: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


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


def main() -> None:
    ensure_dirs()
    fs = base_feature_sets()
    cmeta = {name: (strategy, features, hypothesis) for name, strategy, features, hypothesis in candidate_defs()}
    artwork_features = unique(fs["cold_lgb"])
    core_features = cmeta["user_meta_core_bucket"][1]
    required = unique(artwork_features + core_features + ARTWORK_SIM_FEATURES + ARTIST_SIM_FEATURES)
    train, val, test = load_user_meta_frames(required)

    assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=EXP_ID)
    for name, features in [("artwork_only", artwork_features), ("user_meta_core_bucket", core_features)]:
        assert_strict_cold_features(features, context=f"{EXP_ID}:{name}")

    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=f"artwork_sim_k{TOP_K}", top_k=TOP_K
    )
    features = unique(core_features + art_ref_features)

    # Baseline user_meta_core_bucket is trained with the same local helper for
    # direct comparability, but without similarity features.
    user_pred = fit_weighted_quantile(train, val, test, core_features, alpha=0.50, low_weight=1.0, mid_weight=1.0)

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, frame in [("validation", val), ("test", test)]:
        pred = user_pred[split]
        metric_rows.append(metric_row("user_meta_core_bucket", split, frame, pred, "기존 사용자 메타 core bucket"))
        pred_frames.append(prediction_frame("user_meta_core_bucket", split, frame, pred, "기존 사용자 메타 core bucket"))

    for name, alpha, low_weight, mid_weight, policy in WEIGHT_VARIANTS:
        preds = fit_weighted_quantile(
            train_art,
            val_art,
            test_art,
            features,
            alpha=alpha,
            low_weight=low_weight,
            mid_weight=mid_weight,
        )
        for split, frame in [("validation", val_art), ("test", test_art)]:
            pred = preds[split]
            extra = {"alpha": alpha, "low_weight": low_weight, "mid_weight": mid_weight}
            metric_rows.append(metric_row(name, split, frame, pred, policy, extra))
            pred_frames.append(prediction_frame(name, split, frame, pred, policy, extra))

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
        "training_weighting": True,
        "top_k": TOP_K,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    segment_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "alpha", "low_weight", "mid_weight", "policy",
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
        "- 목적: 출력 cap 대신 학습 단계에서 저가 구간 가중치와 낮은 quantile을 적용해 극단 과대평가를 줄일 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 라우터는 사용하지 않았다.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 기준",
        md_table(tail_metrics, metric_cols),
        "",
        "## 3. 가격대별 진단",
        md_table(segment_df.sort_values(["segment", "APE_gt_5", "p95_APE"]).head(60), seg_cols),
        "",
        "## 4. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- 저가 가중치와 낮은 quantile이 APE > 5를 줄이는 대신 MdAPE/MAPE를 얼마나 희생하는지 함께 봐야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 결과: MdAPE 기준</h2>{html_table(test_metrics, metric_cols)}
<h2>Test 결과: APE &gt; 5 기준</h2>{html_table(tail_metrics, metric_cols)}
<h2>가격대별 진단</h2>{html_table(segment_df.sort_values(['segment', 'APE_gt_5', 'p95_APE']).head(60), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
