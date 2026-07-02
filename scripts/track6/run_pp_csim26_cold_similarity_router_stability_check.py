#!/usr/bin/env python3
"""PP-CSIM26: stability check for CSIM25 Cold residual rule routers.

This follow-up focuses on the small set of plausible CSIM25 routers:
- k40 vs k80 similar artist-meta residual correction
- cap 0.18 vs 0.25
- negative correction thresholds 0.03 vs 0.05

It does not train a new model. It reconstructs routed predictions from CSIM24
outputs and compares candidates with paired bootstrap, split ranking and
segment diagnostics. The goal is to avoid selecting a rule only because it
looked best on one test table.
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

from cold_experiment_harness import strict_cold_run_summary  # noqa: E402
from run_pp_cmeta5_user_meta_robustness_validation import paired_bootstrap  # noqa: E402
from run_pp_csim1_cold_similarity_reference import html_table, json_clean, md_table  # noqa: E402
from run_pp_csim25_cold_similarity_residual_rule_router import (  # noqa: E402
    BASE_CANDIDATE,
    build_prediction_for_candidate,
    load_predictions,
)
from run_pp_csim5_cold_similarity_residual_clip import tail_counts  # noqa: E402
from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXP_ID = "PP-CSIM26"
SLUG = "PP-CSIM26_cold_similarity_router_stability_check"
TITLE = "Cold 유사 이웃 잔차 라우터 안정성 재검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim26_cold_similarity_router_stability_check_summary.md"

FOCUS_CANDIDATES = [
    "base",
    "resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03",
    "resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05",
    "resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03",
    "resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05",
    "resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03",
    "resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05",
    "resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03",
    "resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05",
]


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def metric_row(candidate: str, split: str, pred: pd.DataFrame) -> dict[str, Any]:
    frame = pred[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "split": split,
        "selected_rate": float(pred["selected"].mean()),
        **metrics(frame, pred["pred_log"].to_numpy(dtype=float)),
        **tail_counts(frame, pred["pred_log"].to_numpy(dtype=float)),
    }


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
                "selected_rate": float(group["selected"].mean()),
                **metrics(frame, pred),
                **tail_counts(frame, pred),
            })
    return pd.DataFrame(rows)


def rank_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in metrics_df.groupby("split", observed=False):
        work = group.copy()
        for metric in ["MdAPE", "MAPE", "p95_APE", "APE_gt_5"]:
            work[f"{metric}_rank"] = work[metric].rank(method="min", ascending=True)
        for _, row in work.iterrows():
            rows.append({
                "candidate": row["candidate"],
                "split": split,
                "rank_sum": float(row["MdAPE_rank"] + row["MAPE_rank"] + row["p95_APE_rank"] + row["APE_gt_5_rank"]),
                "MdAPE_rank": float(row["MdAPE_rank"]),
                "MAPE_rank": float(row["MAPE_rank"]),
                "p95_APE_rank": float(row["p95_APE_rank"]),
                "APE_gt_5_rank": float(row["APE_gt_5_rank"]),
            })
    return pd.DataFrame(rows)


def paired_bootstraps(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        base = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq("base"))].sort_values("_track6_row_id")
        frame = base[["_track6_row_id", "actual_log", "actual_price"]].rename(
            columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
        )
        for candidate in FOCUS_CANDIDATES:
            if candidate == "base":
                continue
            cand = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq(candidate))].sort_values("_track6_row_id")
            rows.append(paired_bootstrap(
                frame,
                cand["pred_log"].to_numpy(dtype=float),
                base["pred_log"].to_numpy(dtype=float),
                a_name=candidate,
                b_name="base",
            ) | {"split": split, "comparison": "candidate_vs_base"})

        for k40, k80 in [
            (
                "resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p03",
                "resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p03",
            ),
            (
                "resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p03",
                "resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p03",
            ),
            (
                "resid_artist_meta_k40_s1p0_cap0p18__route_neg_corr_ge_0p05",
                "resid_artist_meta_k80_s1p0_cap0p18__route_neg_corr_ge_0p05",
            ),
            (
                "resid_artist_meta_k40_s1p0_cap0p25__route_neg_corr_ge_0p05",
                "resid_artist_meta_k80_s1p0_cap0p25__route_neg_corr_ge_0p05",
            ),
        ]:
            pred_a = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq(k40))].sort_values("_track6_row_id")
            pred_b = predictions[(predictions["split"].eq(split)) & (predictions["candidate"].eq(k80))].sort_values("_track6_row_id")
            rows.append(paired_bootstrap(
                frame,
                pred_a["pred_log"].to_numpy(dtype=float),
                pred_b["pred_log"].to_numpy(dtype=float),
                a_name=k40,
                b_name=k80,
            ) | {"split": split, "comparison": "k40_vs_k80"})
    return pd.DataFrame(rows)


def write_reports(metrics_df: pd.DataFrame, rank_df: pd.DataFrame, boot_df: pd.DataFrame, seg_df: pd.DataFrame, summary: dict[str, Any]) -> None:
    metric_cols = ["candidate", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "APE_gt_2", "APE_gt_5", "APE_gt_10", "selected_rate"]
    rank_cols = ["candidate", "split", "rank_sum", "MdAPE_rank", "MAPE_rank", "p95_APE_rank", "APE_gt_5_rank"]
    boot_cols = [
        "comparison", "split", "candidate_a", "candidate_b", "n", "n_boot",
        "delta_MdAPE_a_minus_b_mean", "delta_MAPE_a_minus_b_mean", "delta_p95_APE_a_minus_b_mean",
        "p_delta_MdAPE_a_minus_b_lt_0", "p_delta_MAPE_a_minus_b_lt_0", "p_delta_p95_APE_a_minus_b_lt_0",
    ]
    seg_cols = ["candidate", "split", "segment", "n", "selected_rate", "MdAPE", "MAPE", "p95_APE", "APE_gt_2", "APE_gt_5", "APE_gt_10"]

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        "- 목적: CSIM25에서 남은 k40/k80 규칙 후보의 split 안정성과 bootstrap 우세 여부를 재검증한다.",
        "- 추가 학습 없음. CSIM24 예측값과 CSIM25 라우팅 규칙만 재사용한다.",
        "- 금지: 실제 가격을 라우터 입력으로 쓰지 않음, `artist_key`/동일 작가 가격 이력/검색 lookup 미사용.",
        "",
        "## 1. 후보별 성능",
        md_table(metrics_df.sort_values(["split", "MAPE", "p95_APE"]), metric_cols),
        "",
        "## 2. 지표별 순위",
        md_table(rank_df.sort_values(["split", "rank_sum"]), rank_cols),
        "",
        "## 3. Paired bootstrap",
        md_table(boot_df, boot_cols),
        "",
        "## 4. 가격대별 진단",
        md_table(seg_df.sort_values(["split", "candidate", "segment"]), seg_cols),
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;vertical-align:top}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>후보별 성능</h2>{html_table(metrics_df.sort_values(["split", "MAPE", "p95_APE"]), metric_cols)}
<h2>지표별 순위</h2>{html_table(rank_df.sort_values(["split", "rank_sum"]), rank_cols)}
<h2>Paired bootstrap</h2>{html_table(boot_df, boot_cols)}
<h2>가격대별 진단</h2>{html_table(seg_df.sort_values(["split", "candidate", "segment"]), seg_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    source = load_predictions()
    pred_frames = [
        build_prediction_for_candidate(source, split, candidate)
        for split in ["validation", "test"]
        for candidate in FOCUS_CANDIDATES
    ]
    predictions = pd.concat(pred_frames, ignore_index=True)
    metrics_df = pd.DataFrame([
        metric_row(candidate, split, group)
        for (candidate, split), group in predictions.groupby(["candidate", "split"], observed=False)
    ])
    rank_df = rank_summary(metrics_df)
    boot_df = paired_bootstraps(predictions)
    seg_df = segment_summary(predictions)

    summary = strict_cold_run_summary({
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-CSIM25",
        "strict_cold_compliant": True,
        "uses_search_features": False,
        "uses_external_live_search": False,
        "uses_artist_key_lookup_postprocess": False,
        "uses_rule_router": True,
        "router_uses_actual_price": False,
        "focus_candidates": FOCUS_CANDIDATES,
    })
    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "predictions.csv", index=False)
    rank_df.to_csv(OUT / "rank_summary.csv", index=False)
    boot_df.to_csv(OUT / "paired_bootstrap.csv", index=False)
    seg_df.to_csv(OUT / "segment_metrics.csv", index=False)
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(metrics_df, rank_df, boot_df, seg_df, summary)


if __name__ == "__main__":
    main()
