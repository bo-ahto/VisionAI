#!/usr/bin/env python3
"""Compare PP-FPOL2 with the strongest previous Warm correction candidates."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[4]
EXP_ID = "PP-FPOL3"
EXP_DIR = REPO / "experiments/track6/PP-FPOL3_warm_policy_best_candidate_comparison"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

BASELINE = {
    "source": "REFERENCE",
    "candidate": "blend_svcnum_ppv8_wsvc_0.70",
    "family": "reference",
    "feature_set": "base_warm_blend",
    "test_MdAPE": 0.140484,
    "test_MAPE": 0.274799,
    "test_p95_APE": 0.833074,
    "test_RMSE_log": 0.399609,
}

VALIDATION_BASELINE = {
    "validation_MdAPE": 0.130522,
    "validation_MAPE": 0.211028,
    "validation_p95_APE": 0.658041,
    "validation_RMSE_log": 0.329201,
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def add_deltas(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["test_delta_MdAPE"] = out["test_MdAPE"] - BASELINE["test_MdAPE"]
    out["test_delta_MAPE"] = out["test_MAPE"] - BASELINE["test_MAPE"]
    out["test_delta_p95_APE"] = out["test_p95_APE"] - BASELINE["test_p95_APE"]
    out["test_delta_RMSE_log"] = out["test_RMSE_log"] - BASELINE["test_RMSE_log"]
    out["test_balanced_delta"] = out["test_delta_MdAPE"] + out["test_delta_MAPE"] + 0.20 * out["test_delta_p95_APE"]
    out["test_improves_all_three"] = (
        (out["test_delta_MdAPE"] < 0) & (out["test_delta_MAPE"] < 0) & (out["test_delta_p95_APE"] < 0)
    )
    return out


def normalize_wide(path: str, source: str) -> pd.DataFrame:
    df = pd.read_csv(REPO / path)
    rows = []
    for _, row in df.iterrows():
        if str(row.get("family", "")).lower() == "reference":
            continue
        if "test_MdAPE" not in row or pd.isna(row.get("test_MdAPE")):
            continue
        rows.append(
            {
                "source": source,
                "candidate": row.get("candidate"),
                "family": row.get("family", ""),
                "feature_set": row.get("feature_set", row.get("features", "")),
                "policy": row.get("correction_policy", row.get("guard", "")),
                "test_MdAPE": row.get("test_MdAPE"),
                "test_MAPE": row.get("test_MAPE"),
                "test_p95_APE": row.get("test_p95_APE"),
                "test_RMSE_log": row.get("test_RMSE_log"),
                "validation_delta_MdAPE": row.get("validation_delta_MdAPE", pd.NA),
                "validation_delta_MAPE": row.get("validation_delta_MAPE", pd.NA),
                "validation_delta_p95_APE": row.get("validation_delta_p95_APE", pd.NA),
                "mean_abs_correction": row.get("test_mean_abs_correction", row.get("mean_abs_correction", pd.NA)),
            }
        )
    return pd.DataFrame(rows)


def normalize_long(path: str, source: str) -> pd.DataFrame:
    df = pd.read_csv(REPO / path)
    test = df[df["split"].eq("test")].copy()
    test = test[~test["family"].astype(str).str.lower().eq("reference")].copy()
    val = df[df["split"].eq("validation")].copy()
    val = val[["candidate", "MdAPE", "MAPE", "p95_APE"]].rename(
        columns={
            "MdAPE": "validation_MdAPE",
            "MAPE": "validation_MAPE",
            "p95_APE": "validation_p95_APE",
        }
    )
    merged = test.merge(val, on="candidate", how="left")
    rows = []
    for _, row in merged.iterrows():
        rows.append(
            {
                "source": source,
                "candidate": row.get("candidate"),
                "family": row.get("family", ""),
                "feature_set": row.get("feature_set", row.get("features", "")),
                "policy": row.get("correction_policy", row.get("method", "")),
                "test_MdAPE": row.get("MdAPE"),
                "test_MAPE": row.get("MAPE"),
                "test_p95_APE": row.get("p95_APE"),
                "test_RMSE_log": row.get("RMSE_log"),
                "validation_delta_MdAPE": row.get("validation_MdAPE") - VALIDATION_BASELINE["validation_MdAPE"]
                if pd.notna(row.get("validation_MdAPE"))
                else pd.NA,
                "validation_delta_MAPE": row.get("validation_MAPE") - VALIDATION_BASELINE["validation_MAPE"]
                if pd.notna(row.get("validation_MAPE"))
                else pd.NA,
                "validation_delta_p95_APE": row.get("validation_p95_APE") - VALIDATION_BASELINE["validation_p95_APE"]
                if pd.notna(row.get("validation_p95_APE"))
                else pd.NA,
                "mean_abs_correction": row.get("mean_abs_correction", pd.NA),
            }
        )
    return pd.DataFrame(rows)


def load_candidates() -> pd.DataFrame:
    frames = [
        pd.DataFrame([BASELINE]),
        normalize_wide(
            "experiments/track6/PP-FPOL2_warm_artist_artwork_policy_huber_residual/outputs/candidate_metrics.csv",
            "PP-FPOL2",
        ),
        normalize_wide(
            "experiments/track6/PP-AMW10_warm_birth_generation_activity_external_residual_correction/outputs/candidate_metrics.csv",
            "PP-AMW10",
        ),
        normalize_wide(
            "experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction/outputs/combo_candidate_metrics.csv",
            "PP-AMW8",
        ),
        normalize_long(
            "experiments/track6/PP-WHUBER7_warm_residual_huber_correction_methods/outputs/all_candidate_metrics.csv",
            "PP-WHUBER7",
        ),
        normalize_long(
            "experiments/track6/PP-WCOEF_warm_huber_feature_coefficient_refinement/outputs/all_candidate_metrics.csv",
            "PP-WCOEF",
        ),
    ]
    df = pd.concat(frames, ignore_index=True)
    for col in ["test_MdAPE", "test_MAPE", "test_p95_APE", "test_RMSE_log"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["test_MdAPE", "test_MAPE", "test_p95_APE", "test_RMSE_log"])
    return add_deltas(df)


def pick_summary(df: pd.DataFrame) -> pd.DataFrame:
    non_ref = df[~df["source"].eq("REFERENCE")].copy()
    rows = []
    picks = {
        "MdAPE 최저": non_ref.sort_values(["test_MdAPE", "test_MAPE"]).iloc[0],
        "MAPE 최저": non_ref.sort_values(["test_MAPE", "test_p95_APE"]).iloc[0],
        "p95 최저": non_ref.sort_values(["test_p95_APE", "test_MAPE"]).iloc[0],
        "세 지표 균형 최저": non_ref.sort_values(["test_balanced_delta", "test_MAPE"]).iloc[0],
        "세 지표 모두 개선 중 균형 최저": non_ref[non_ref["test_improves_all_three"]]
        .sort_values(["test_balanced_delta", "test_MAPE"])
        .iloc[0],
        "이번 정책 실험 최선": non_ref[non_ref["source"].eq("PP-FPOL2")]
        .sort_values(["test_balanced_delta", "test_MAPE"])
        .iloc[0],
    }
    for objective, row in picks.items():
        item = row.to_dict()
        item["objective"] = objective
        rows.append(item)
    return pd.DataFrame(rows)


def selected_rows(df: pd.DataFrame) -> pd.DataFrame:
    names = {
        "blend_svcnum_ppv8_wsvc_0.70",
        "huber_artist_core_hard_clip_small_global_eps1p05_cap0p03_s0p5",
        "huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5",
        "PP-WHUBER7_pred_size_material_svc_artist_eps1.35_alpha0p01_predbin_mid_open_tail_guard_cap0p08_s0p25",
        "PP-WHUBER7_pred_size_svc_eps1.05_alpha0p01_dir_under_guard_cap0p08",
        "PP-WHUBER7_pred_size_material_svc_artist_eps1.60_alpha0p001_predbin_mid_open_tail_guard_cap0p06_s0p35",
        "PP-WCOEF5_resid_pred_size_svc_alpha0p001_cap0p08_s0p25",
        "PP-WCOEF5_resid_pred_size_material_svc_artist_alpha0p01_cap0p08_s0p25",
    }
    rows = df[df["candidate"].isin(names)].copy()
    return rows.sort_values(["test_balanced_delta", "test_MAPE"])


def bootstrap_lookup() -> pd.DataFrame:
    frames = []
    sources = {
        "PP-FPOL2": "experiments/track6/PP-FPOL2_warm_artist_artwork_policy_huber_residual/outputs/bootstrap_summary.csv",
        "PP-AMW10": "experiments/track6/PP-AMW10_warm_birth_generation_activity_external_residual_correction/outputs/bootstrap_summary.csv",
        "PP-AMW8": "experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction/outputs/bootstrap_summary.csv",
        "PP-WHUBER7": "experiments/track6/PP-WHUBER7_warm_residual_huber_correction_methods/outputs/bootstrap_summary.csv",
        "PP-WCOEF": "experiments/track6/PP-WCOEF_warm_huber_feature_coefficient_refinement/outputs/bootstrap_summary.csv",
    }
    for source, path in sources.items():
        full = REPO / path
        if not full.exists():
            continue
        df = pd.read_csv(full)
        df["source"] = source
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def format_float(value: Any, digits: int = 4) -> str:
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        values = []
        for col in columns:
            value = row[col]
            values.append(format_float(value) if isinstance(value, (float, int)) or pd.api.types.is_number(value) else str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_report(df: pd.DataFrame, summary: pd.DataFrame, selected: pd.DataFrame, bootstrap: pd.DataFrame) -> None:
    cols = [
        "objective",
        "source",
        "candidate",
        "feature_set",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "test_balanced_delta",
    ]
    selected_cols = [
        "source",
        "candidate",
        "feature_set",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "test_balanced_delta",
    ]
    report = [
        "# PP-FPOL3 Warm 최상위 후보 비교",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 비교 대상: PP-FPOL2, PP-AMW10, PP-AMW8, PP-WHUBER7, PP-WCOEF",
        "- 기준 test: 607건 Warm 고정 test",
        "- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`",
        "",
        "## 1. 목적별 최상위 후보",
        "",
        markdown_table(summary, cols),
        "",
        "## 2. 주요 후보 직접 비교",
        "",
        markdown_table(selected, selected_cols),
        "",
        "## 3. 판단",
        "",
        "- MdAPE만 최우선이면 PP-WHUBER7의 `pred_size_material_svc_artist` 후보가 가장 낮다. 다만 일부 후보는 p95가 악화된다.",
        "- MAPE와 p95까지 같이 보면 PP-WHUBER7의 `pred_size_svc ... dir_under_guard_cap0p08` 후보가 가장 강하다.",
        "- PP-FPOL2 최선 후보는 기존 안정 후보인 작가 생년+세대 계열과 거의 같은 방향이며, 전체 최상위는 아니다.",
        "- 작품 피처 전체 통합 보정은 PP-WHUBER7의 SVC/가격대 guard 방식으로 쓸 때 더 강했고, PP-FPOL2처럼 일반 작가+작품 피처를 한 번에 넣으면 개선 폭이 줄었다.",
    ]
    (REPORT_DIR / "best_candidate_comparison.md").write_text("\n".join(report), encoding="utf-8")

    html_body = "<html><head><meta charset='utf-8'><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.45;margin:32px;}table{border-collapse:collapse;width:100%;font-size:12px;}th,td{border:1px solid #ddd;padding:5px;vertical-align:top;}th{background:#f4f6f8;}</style></head><body>"
    html_body += "<h1>PP-FPOL3 Warm 최상위 후보 비교</h1>"
    html_body += "<h2>목적별 최상위 후보</h2>" + summary.to_html(index=False, escape=True)
    html_body += "<h2>주요 후보 직접 비교</h2>" + selected.to_html(index=False, escape=True)
    if not bootstrap.empty:
        html_body += "<h2>Bootstrap</h2>" + bootstrap.to_html(index=False, escape=True)
    html_body += "</body></html>"
    (REPORT_DIR / "best_candidate_comparison.html").write_text(html_body, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    candidates = load_candidates()
    summary = pick_summary(candidates)
    selected = selected_rows(candidates)
    bootstrap = bootstrap_lookup()
    selected_names = set(summary["candidate"]) | set(selected["candidate"])
    bootstrap_selected = bootstrap[bootstrap["candidate"].isin(selected_names)].copy() if not bootstrap.empty else bootstrap

    candidates.to_csv(OUT_DIR / "normalized_candidate_comparison.csv", index=False)
    summary.to_csv(OUT_DIR / "objective_best_summary.csv", index=False)
    selected.to_csv(OUT_DIR / "selected_candidate_comparison.csv", index=False)
    bootstrap_selected.to_csv(OUT_DIR / "selected_bootstrap_summary.csv", index=False)
    manifest = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_rows": int(len(candidates)),
        "summary_rows": int(len(summary)),
        "selected_rows": int(len(selected)),
        "outputs": [
            "outputs/normalized_candidate_comparison.csv",
            "outputs/objective_best_summary.csv",
            "outputs/selected_candidate_comparison.csv",
            "outputs/selected_bootstrap_summary.csv",
            "reports/best_candidate_comparison.md",
            "reports/best_candidate_comparison.html",
        ],
    }
    (OUT_DIR / "comparison_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(candidates, summary, selected, bootstrap_selected)


if __name__ == "__main__":
    main()
