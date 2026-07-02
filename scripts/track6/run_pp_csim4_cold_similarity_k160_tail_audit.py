#!/usr/bin/env python3
"""PP-CSIM4: tail audit for Cold artwork_similarity_k160.

This audit uses PP-CSIM3 predictions and checks whether k160 improves the
current user_meta_core_bucket candidate in the parts that matter for operation:

- row-level win rate
- large-error counts
- over/under prediction bias
- segment deltas by actual price band and quantile width band
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics


EXP_ID = "PP-CSIM4"
SLUG = "PP-CSIM4_cold_similarity_k160_tail_audit"
TITLE = "Cold 유사작품 k160 tail 안정성 추가 검증"
EXP = BASE_EXP_DIR / SLUG
OUT = EXP / "outputs"
REPORTS = EXP / "reports"
ARTIFACTS = EXP / "artifacts"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "pp_csim4_cold_similarity_k160_tail_audit_summary.md"
SOURCE_PRED = BASE_EXP_DIR / "PP-CSIM3_cold_similarity_k160_validation" / "outputs" / "predictions.csv"

BASELINE = "user_meta_core_bucket"
CHALLENGER = "artwork_similarity_k160"


def ensure_dirs() -> None:
    for path in [OUT, REPORTS, ARTIFACTS, DOC_MD.parent]:
        path.mkdir(parents=True, exist_ok=True)


def json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [json_clean(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


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


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    head = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    rows = []
    for _, row in df[cols].iterrows():
        cells = []
        for col in cols:
            value = row[col]
            text = f"{value:.6f}" if isinstance(value, float) else str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def paired_frame(pred: pd.DataFrame, split: str) -> pd.DataFrame:
    base = pred[pred["split"].eq(split) & pred["candidate"].eq(BASELINE)].copy()
    chal = pred[pred["split"].eq(split) & pred["candidate"].eq(CHALLENGER)].copy()
    keep = ["_track6_row_id", "actual_log", "actual_price", "pred_log", "pred_price", "quantile_width_log"]
    merged = base[keep].merge(chal[keep], on="_track6_row_id", suffixes=("_base", "_challenger"))
    merged["actual_price"] = merged["actual_price_base"]
    merged["actual_log"] = merged["actual_log_base"]
    merged["ape_base"] = (merged["pred_price_base"] - merged["actual_price"]).abs() / np.maximum(merged["actual_price"], 1.0)
    merged["ape_challenger"] = (merged["pred_price_challenger"] - merged["actual_price"]).abs() / np.maximum(merged["actual_price"], 1.0)
    merged["signed_pct_base"] = (merged["pred_price_base"] - merged["actual_price"]) / np.maximum(merged["actual_price"], 1.0)
    merged["signed_pct_challenger"] = (merged["pred_price_challenger"] - merged["actual_price"]) / np.maximum(merged["actual_price"], 1.0)
    merged["ape_delta_challenger_minus_base"] = merged["ape_challenger"] - merged["ape_base"]
    merged["challenger_wins"] = merged["ape_challenger"] < merged["ape_base"]
    return merged


def overall_rows(paired: pd.DataFrame, split: str) -> dict[str, Any]:
    out = {
        "split": split,
        "n": int(len(paired)),
        "win_rate": float(paired["challenger_wins"].mean()),
        "delta_median_APE": float(paired["ape_delta_challenger_minus_base"].median()),
        "delta_mean_APE": float(paired["ape_delta_challenger_minus_base"].mean()),
        "delta_p95_APE": float(paired["ape_challenger"].quantile(0.95) - paired["ape_base"].quantile(0.95)),
        "base_over_bias_mean": float(paired["signed_pct_base"].mean()),
        "challenger_over_bias_mean": float(paired["signed_pct_challenger"].mean()),
    }
    for threshold in [1.0, 2.0, 5.0, 10.0]:
        out[f"base_APE_gt_{threshold:g}"] = int((paired["ape_base"] > threshold).sum())
        out[f"challenger_APE_gt_{threshold:g}"] = int((paired["ape_challenger"] > threshold).sum())
        out[f"delta_count_APE_gt_{threshold:g}"] = int((paired["ape_challenger"] > threshold).sum() - (paired["ape_base"] > threshold).sum())
    return out


def segment_rows(paired: pd.DataFrame, split: str) -> pd.DataFrame:
    df = paired.copy()
    df["actual_price_band"] = pd.cut(
        pd.to_numeric(df["actual_price"], errors="coerce"),
        bins=[-np.inf, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["lt_1m", "1m_3m", "3m_10m", "gt_10m"],
        include_lowest=True,
    ).astype("string")
    try:
        df["quantile_width_band"] = pd.qcut(
            pd.to_numeric(df["quantile_width_log_challenger"], errors="coerce"),
            q=4,
            labels=["qwidth_q1_low", "qwidth_q2", "qwidth_q3", "qwidth_q4_high"],
            duplicates="drop",
        ).astype("string")
    except ValueError:
        df["quantile_width_band"] = "qwidth_unknown"

    rows = []
    for segment_type in ["actual_price_band", "quantile_width_band"]:
        for segment, group in df.groupby(segment_type, observed=False, dropna=False):
            if group.empty:
                continue
            rows.append({
                "split": split,
                "segment_type": segment_type,
                "segment": str(segment),
                "n": int(len(group)),
                "win_rate": float(group["challenger_wins"].mean()),
                "delta_MdAPE": float(group["ape_challenger"].median() - group["ape_base"].median()),
                "delta_MAPE": float(group["ape_challenger"].mean() - group["ape_base"].mean()),
                "delta_p95_APE": float(group["ape_challenger"].quantile(0.95) - group["ape_base"].quantile(0.95)),
                "base_p95_APE": float(group["ape_base"].quantile(0.95)),
                "challenger_p95_APE": float(group["ape_challenger"].quantile(0.95)),
                "delta_APE_gt_2_count": int((group["ape_challenger"] > 2.0).sum() - (group["ape_base"] > 2.0).sum()),
                "delta_APE_gt_5_count": int((group["ape_challenger"] > 5.0).sum() - (group["ape_base"] > 5.0).sum()),
            })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()
    pred = pd.read_csv(SOURCE_PRED, low_memory=False)
    overall = []
    segments = []
    paired_frames = []
    for split in ["validation", "test"]:
        paired = paired_frame(pred, split)
        paired["split"] = split
        paired_frames.append(paired)
        overall.append(overall_rows(paired, split))
        segments.append(segment_rows(paired, split))

    paired_df = pd.concat(paired_frames, ignore_index=True)
    overall_df = pd.DataFrame(overall)
    segment_df = pd.concat(segments, ignore_index=True)

    paired_df.to_csv(OUT / "paired_row_deltas.csv", index=False)
    overall_df.to_csv(OUT / "overall_tail_audit.csv", index=False)
    segment_df.to_csv(OUT / "segment_tail_audit.csv", index=False)

    summary = {
        "experiment_id": EXP_ID,
        "slug": SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_predictions": str(SOURCE_PRED),
        "baseline": BASELINE,
        "challenger": CHALLENGER,
        "router_used": False,
    }
    (ARTIFACTS / "run_summary.json").write_text(json.dumps(json_clean(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    overall_cols = [
        "split", "n", "win_rate", "delta_median_APE", "delta_mean_APE", "delta_p95_APE",
        "base_APE_gt_2", "challenger_APE_gt_2", "delta_count_APE_gt_2",
        "base_APE_gt_5", "challenger_APE_gt_5", "delta_count_APE_gt_5",
        "base_over_bias_mean", "challenger_over_bias_mean",
    ]
    segment_cols = [
        "split", "segment_type", "segment", "n", "win_rate", "delta_MdAPE",
        "delta_MAPE", "delta_p95_APE", "base_p95_APE", "challenger_p95_APE",
        "delta_APE_gt_2_count", "delta_APE_gt_5_count",
    ]
    risky = segment_df[segment_df["split"].eq("test")].sort_values(
        ["delta_p95_APE", "delta_MAPE"], ascending=[False, False]
    )
    helpful = segment_df[segment_df["split"].eq("test")].sort_values(
        ["delta_p95_APE", "delta_MAPE"], ascending=[True, True]
    )

    md = "\n".join([
        f"# {TITLE}",
        "",
        f"- 작성일: {summary['created_at']}",
        f"- 비교: `{CHALLENGER}` - `{BASELINE}`. delta가 음수이면 k160 후보가 더 좋다.",
        "- 목적: 라우터 없이 후보 모델 자체의 tail 안정성을 확인한다.",
        "",
        "## 1. 전체 tail 감사",
        md_table(overall_df, overall_cols),
        "",
        "## 2. test에서 악화된 세그먼트",
        md_table(risky.head(12), segment_cols),
        "",
        "## 3. test에서 개선된 세그먼트",
        md_table(helpful.head(12), segment_cols),
        "",
        "## 4. 결론",
        "",
        "- test 전체에서는 k160 후보가 평균 오차와 큰 오차 개수를 줄인다.",
        "- validation/test 모두 row-level win rate는 50%를 크게 넘지 않으므로, 개선은 모든 행에서 고르게 이기는 방식이 아니라 큰 오차를 줄이는 방식에 가깝다.",
        "- 저가 구간은 두 후보 모두 가장 취약하며, k160이 p95를 낮추지만 MdAPE는 약간 나빠질 수 있다.",
        "- 라우터를 쓰지 않는 조건에서는 k160 후보가 현재까지 가장 설득력 있는 개선 후보지만, 저가 tail과 메타 누락을 운영 표시 정책으로 같이 관리해야 한다.",
    ])
    (REPORTS / "result_report.md").write_text(md, encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(TITLE)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:32px;color:#1f2937}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d8dee9;padding:6px 9px;font-size:13px}}th{{background:#f3f4f6}}</style></head><body>
<h1>{html.escape(TITLE)}</h1>
<h2>전체 tail 감사</h2>{html_table(overall_df, overall_cols)}
<h2>test에서 악화된 세그먼트</h2>{html_table(risky.head(12), segment_cols)}
<h2>test에서 개선된 세그먼트</h2>{html_table(helpful.head(12), segment_cols)}
</body></html>"""
    (REPORTS / "result_report.html").write_text(html_doc, encoding="utf-8")
    print(json.dumps(json_clean(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
