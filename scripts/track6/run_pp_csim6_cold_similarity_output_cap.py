#!/usr/bin/env python3
"""PP-CSIM6: Cold artwork_similarity_k160 output cap validation.

Router-free post-prediction stabilization.  The selected k160 direct model is
kept as the base model, but its log prediction is capped by the similar-artwork
reference distribution:

    capped_log = min(pred_log, ref_q75_log + margin)

The goal is to reduce extreme over-prediction and APE > 5 while preserving the
MdAPE/MAPE gains from PP-CSIM3.
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
    fit_quantile_bundle,
    html_table,
    json_clean,
    md_table,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, unique  # noqa: E402


EXP_ID = "PP-CSIM6"
SLUG = "PP-CSIM6_cold_similarity_output_cap"
TITLE = "Cold 유사작품 k160 출력 상한 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim6_cold_similarity_output_cap_summary.md"

TOP_K = 160
CAP_GRID = [
    ("cap_q75_p020", "q75", 0.20),
    ("cap_q75_p040", "q75", 0.40),
    ("cap_q75_p060", "q75", 0.60),
    ("cap_q75_p080", "q75", 0.80),
    ("cap_q75_p100", "q75", 1.00),
    ("cap_median_p080", "median", 0.80),
    ("cap_median_p100", "median", 1.00),
    ("cap_median_p120", "median", 1.20),
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


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


def cap_prediction(pred: np.ndarray, ref: np.ndarray, margin: float) -> tuple[np.ndarray, np.ndarray]:
    cap = ref + margin
    capped = np.minimum(pred, cap)
    return capped, pred > cap


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
            "cap_applied_rate": float(pd.to_numeric(group.get("cap_applied", 0), errors="coerce").fillna(0).mean()),
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

    prefix = f"artwork_sim_k{TOP_K}"
    q75_col = f"{prefix}_ref_log_price_q75"
    median_col = f"{prefix}_ref_log_price_median"
    train_art, val_art, test_art, art_ref_features = compute_reference_stats(
        train, val, test, ARTWORK_SIM_FEATURES, prefix=prefix, top_k=TOP_K
    )
    direct_features = unique(core_features + art_ref_features)
    direct_bundle = fit_quantile_bundle(train_art, val_art, test_art, direct_features)
    user_bundle = fit_quantile_bundle(train, val, test, core_features)

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split, frame, frame_art in [("validation", val, val_art), ("test", test, test_art)]:
        user_pred = user_bundle["q50"][split]
        metric_rows.append(metric_row("user_meta_core_bucket", split, frame, user_pred, "기존 사용자 메타 core bucket"))
        pred_frames.append(prediction_frame("user_meta_core_bucket", split, frame, user_pred, "기존 사용자 메타 core bucket", {"cap_applied": 0.0}))

        direct_pred = direct_bundle["q50"][split]
        metric_rows.append(metric_row("artwork_similarity_k160_direct", split, frame_art, direct_pred, "유사작품 k160 직접 q50 예측"))
        pred_frames.append(prediction_frame("artwork_similarity_k160_direct", split, frame_art, direct_pred, "유사작품 k160 직접 q50 예측", {"cap_applied": 0.0}))

        refs = {
            "q75": pd.to_numeric(frame_art[q75_col], errors="coerce").to_numpy(dtype=float),
            "median": pd.to_numeric(frame_art[median_col], errors="coerce").to_numpy(dtype=float),
        }
        for name, ref_name, margin in CAP_GRID:
            capped, applied = cap_prediction(direct_pred, refs[ref_name], margin)
            policy = f"유사작품 k160 직접 q50 예측을 ref_{ref_name}+{margin:.2f} log로 상한"
            candidate = f"artwork_similarity_k160_{name}"
            extra = {
                "cap_ref": ref_name,
                "cap_margin": margin,
                "cap_applied_count": int(applied.sum()),
                "cap_applied_rate": float(applied.mean()),
            }
            metric_rows.append(metric_row(candidate, split, frame_art, capped, policy, extra))
            pred_frames.append(prediction_frame(candidate, split, frame_art, capped, policy, {
                "cap_applied": applied.astype(float),
                "cap_ref": ref_name,
                "cap_margin": margin,
            }))

    metrics_df = pd.DataFrame(metric_rows)
    predictions_df = pd.concat(pred_frames, ignore_index=True)
    seg_df = pd.concat([
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
        "post_prediction_cap": True,
        "top_k": TOP_K,
    })

    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions_df.to_csv(OUT / "predictions.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    metric_cols = [
        "candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log",
        "Within_30", "Within_50", "APE_gt_1", "APE_gt_2", "APE_gt_5", "APE_gt_10",
        "cap_applied_count", "cap_applied_rate", "policy",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "cap_applied_rate"]
    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    tail_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values(["APE_gt_5", "p95_APE", "MAPE"])
    best_mdape = test_metrics.iloc[0]["candidate"]
    best_tail = tail_metrics.iloc[0]["candidate"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: `artwork_similarity_k160` 직접 예측의 과대평가 tail을 유사작품 비교군 상위 가격 기준으로 제한할 수 있는지 검증한다.",
        "- 조건: `artist_key`, 같은 작가 가격 이력, `artist_key` lookup 후처리, `search_*`, 외부 live 검색 미사용.",
        "- 라우터는 사용하지 않았고, 같은 후보 예측값에 deterministic output cap만 적용했다.",
        "",
        "## 1. Test 결과: MdAPE 기준",
        md_table(test_metrics, metric_cols),
        "",
        "## 2. Test 결과: APE > 5 기준",
        md_table(tail_metrics, metric_cols),
        "",
        "## 3. 가격대별 진단",
        md_table(seg_df.sort_values(["segment", "APE_gt_5", "p95_APE"]).head(60), seg_cols),
        "",
        "## 4. 결론",
        "",
        f"- MdAPE 기준 최상위 후보는 `{best_mdape}`이다.",
        f"- APE > 5 안정성 기준 최상위 후보는 `{best_tail}`이다.",
        "- output cap이 극단 오차를 줄이더라도 MdAPE/MAPE 손실이 크면 운영 후보로 보기 어렵다.",
        "- 라우터가 아니라 출력 안정화 실험이므로, 결과는 후보 예측값 후처리의 효과로 해석한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>Test 결과: MdAPE 기준</h2>{html_table(test_metrics, metric_cols)}
<h2>Test 결과: APE &gt; 5 기준</h2>{html_table(tail_metrics, metric_cols)}
<h2>가격대별 진단</h2>{html_table(seg_df.sort_values(['segment', 'APE_gt_5', 'p95_APE']).head(60), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
