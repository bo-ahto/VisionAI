#!/usr/bin/env python3
"""Compare v0.1 70:30 re-predictions with labeled 0604 prices."""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "experiments" / "track6").exists() and (current / "data").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
EXP_DIR = REPO / "experiments" / "track6" / "OP-0605_v01_70_30_reprediction"
DEFAULT_PREDICTION_FILE = EXP_DIR / "outputs" / "predictions" / "predictions_all.csv"
DEFAULT_LABEL_FILE = REPO / "data" / "test_new_artworks_test_0604.csv"
DEFAULT_OUTPUT_DIR = EXP_DIR / "outputs" / "comparison"
REPORT_DIR = EXP_DIR / "reports"

FX_KRW_PER_UNIT = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "KRW": 1.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}

CANDIDATES = {
    "svc_group_median": "svc_group_median_pred_price_krw",
    "legacy_warm_huber": "legacy_warm_huber_pred_price_krw",
    "legacy_log_blend_svc0p7_huber0p3": "legacy_log_blend_svc0p7_huber0p3_pred_price_krw",
    "svc_numeric_seed_mean": "svc_numeric_seed_mean_pred_price_krw",
    "pp_v8_distilled_component": "pp_v8_distilled_pred_price_krw",
    "v01_70_30_repred": "v01_70_30_repred_price_krw",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare prediction candidates with numeric sale labels.")
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTION_FILE, help="02 스크립트 예측 파일")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABEL_FILE, help="가격 라벨이 있는 원본 CSV")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="비교 결과 출력 폴더")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def parse_price(message: object) -> tuple[float, str | None, float]:
    if pd.isna(message):
        return np.nan, None, np.nan
    text = str(message).strip()
    currency: str | None = None
    raw = text
    if text.startswith("US$"):
        currency = "USD"
        raw = text.replace("US$", "", 1)
    elif text.startswith("KRW") or text.startswith("₩"):
        currency = "KRW"
        raw = text.replace("KRW", "", 1).replace("₩", "", 1)
    elif text.startswith("€"):
        currency = "EUR"
        raw = text.replace("€", "", 1)
    elif text.startswith("£"):
        currency = "GBP"
        raw = text.replace("£", "", 1)
    elif text.startswith("HK$"):
        currency = "HKD"
        raw = text.replace("HK$", "", 1)
    elif text.startswith("¥"):
        currency = "JPY"
        raw = text.replace("¥", "", 1)
    if currency is None:
        return np.nan, None, np.nan
    match = re.search(r"[-+]?[0-9][0-9,]*(?:\.[0-9]+)?", raw)
    if not match:
        return np.nan, currency, np.nan
    native = float(match.group(0).replace(",", ""))
    return native, currency, native * FX_KRW_PER_UNIT[currency]


def add_actual_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    parsed = out["sale_message"].apply(parse_price)
    out[["actual_price_native", "actual_currency", "actual_price_krw"]] = pd.DataFrame(parsed.tolist(), index=out.index)
    out["actual_price_usd_equiv"] = out["actual_price_krw"] / FX_KRW_PER_UNIT["USD"]
    out["actual_label_quality"] = np.select(
        [
            out["actual_price_krw"].isna(),
            out["actual_price_usd_equiv"] < 50,
            out["actual_price_usd_equiv"] >= 100_000,
        ],
        [
            "not_numeric_actual",
            "review_very_low_price_under_50_usd",
            "review_high_tail_over_100k_usd",
        ],
        default="numeric_actual",
    )
    bins = [-np.inf, 50, 100, 500, 1_000, 5_000, 20_000, 100_000, np.inf]
    labels = ["<50usd_review", "50_100usd", "100_500usd", "500_1k_usd", "1k_5k_usd", "5k_20k_usd", "20k_100k_usd", "100k_plus_usd"]
    out["actual_price_band"] = pd.cut(out["actual_price_usd_equiv"], bins, labels=labels)
    return out


def add_error_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    actual = pd.to_numeric(out["actual_price_krw"], errors="coerce")
    for name, col in CANDIDATES.items():
        if col not in out.columns:
            continue
        pred = pd.to_numeric(out[col], errors="coerce")
        out[f"{name}_ape"] = (pred - actual).abs() / actual
        out[f"{name}_ratio"] = pred / actual
        out[f"{name}_log_error"] = np.log(pred.clip(lower=1)) - np.log(actual.clip(lower=1))
    return out


def metrics_for(frame: pd.DataFrame, scope: str, candidate: str) -> dict[str, Any]:
    ape = pd.to_numeric(frame[f"{candidate}_ape"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    ratio = pd.to_numeric(frame[f"{candidate}_ratio"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    log_error = pd.to_numeric(frame[f"{candidate}_log_error"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "scope": scope,
        "candidate": candidate,
        "n": int(len(ape)),
        "MdAPE": float(ape.median()) if len(ape) else np.nan,
        "MAPE": float(ape.mean()) if len(ape) else np.nan,
        "p95_APE": float(ape.quantile(0.95)) if len(ape) else np.nan,
        "RMSE_log": float(np.sqrt(np.mean(log_error.to_numpy() ** 2))) if len(log_error) else np.nan,
        "median_ratio": float(ratio.median()) if len(ratio) else np.nan,
        "over_3x_n": int((ratio >= 3).sum()) if len(ratio) else 0,
        "under_1_3x_n": int((ratio <= 1 / 3).sum()) if len(ratio) else 0,
    }


def build_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = {
        "numeric_actual_all": frame[frame["actual_price_krw"].notna()].copy(),
        "numeric_actual_excluding_under_50_usd": frame[(frame["actual_price_krw"].notna()) & (frame["actual_price_usd_equiv"] >= 50)].copy(),
    }
    for scope, part in scopes.items():
        for candidate in CANDIDATES:
            if f"{candidate}_ape" in part.columns:
                rows.append(metrics_for(part, scope, candidate))
    return pd.DataFrame(rows)


def build_segment_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    usable = frame[(frame["actual_price_krw"].notna()) & (frame["actual_price_usd_equiv"] >= 50)].copy()
    for segment_col in ["actual_price_band", "svc_group_level", "svc_coverage_tier"]:
        if segment_col not in usable.columns:
            continue
        for segment, group in usable.groupby(segment_col, dropna=False, observed=False):
            if len(group) < 5:
                continue
            for candidate in ["svc_group_median", "legacy_log_blend_svc0p7_huber0p3", "v01_70_30_repred"]:
                if f"{candidate}_ape" not in group.columns:
                    continue
                row = metrics_for(group, f"{segment_col}={segment}", candidate)
                row["segment_column"] = segment_col
                row["segment_value"] = str(segment)
                rows.append(row)
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "- 데이터 없음"
    view = df.head(max_rows).copy() if max_rows else df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(x))
    header = "| " + " | ".join(view.columns) + " |"
    sep = "| " + " | ".join("---" for _ in view.columns) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in view.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *rows])


def write_report(output_dir: Path, metrics: pd.DataFrame, segment_metrics: pd.DataFrame, merged: pd.DataFrame, summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    all_scope = metrics[metrics["scope"].eq("numeric_actual_all")].sort_values(["MdAPE", "MAPE"])
    filtered_scope = metrics[metrics["scope"].eq("numeric_actual_excluding_under_50_usd")].sort_values(["MdAPE", "MAPE"])
    top_errors = merged[merged["actual_price_krw"].notna()].copy()
    if "v01_70_30_repred_ape" in top_errors.columns:
        top_errors = top_errors.sort_values("v01_70_30_repred_ape", ascending=False)
    cols = [
        "_v01_row_id",
        "title",
        "artist_name",
        "sale_message",
        "actual_price_krw",
        "v01_70_30_repred_price_krw",
        "v01_70_30_repred_ape",
        "svc_group_level",
        "svc_group_n",
    ]
    top_errors = top_errors[[col for col in cols if col in top_errors.columns]].head(30)
    md = f"""# v0.1 70:30 재예측 비교 결과

- 작성일: {summary['created_at']}
- 예측 파일: `{summary['prediction_file']}`
- 라벨 파일: `{summary['label_file']}`
- 전체 행: {summary['total_rows']:,}
- 숫자 가격 라벨: {summary['numeric_actual_rows']:,}
- 50달러 미만 검수 필요 라벨: {summary['very_low_price_rows']:,}
- PP-V8 component 재현 방식: {summary['ppv8_component_method']}
- PP-V8 component fidelity: test RMSE_log `{summary['ppv8_fidelity_RMSE_log']}`, MdAE_log `{summary['ppv8_fidelity_MdAE_log']}`

## 1. 실행 해석

- `v01_70_30_repred`: v0.1 정책 식 `70% svc_numeric_seed_mean + 30% PP-V8 component`를 적용한 재예측 후보
- `PP-V8 component`: 원천 후보 전체 artifact가 없어 기존 PP-V8 예측을 CatBoost로 모사한 distillation component
- 따라서 이번 결과는 최종 식을 신규 파일에 적용한 재실행이지만, PP-V8 축은 source-decomposed exact가 아닌 재현용 component임
- 완전한 source-decomposed exact 비교를 위해서는 PP-V8 원천 후보별 신규 데이터 추론 artifact가 추가로 필요함

## 2. 전체 숫자 라벨 기준

{markdown_table(all_scope)}

## 3. 50달러 미만 검수 필요 라벨 제외 기준

{markdown_table(filtered_scope)}

## 4. 주요 segment 비교

{markdown_table(segment_metrics.sort_values(['segment_column', 'segment_value', 'MdAPE']).head(80))}

## 5. v0.1 70:30 재예측 큰 오차 상위

{markdown_table(top_errors)}
"""
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    style = "body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#17202a;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}th,td{border:1px solid #d8dee4;padding:7px;text-align:left}th{background:#eef2f7}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>v0.1 70:30 재예측 비교</title><style>{style}</style></head>
<body><h1>v0.1 70:30 재예측 비교 결과</h1>
<p>PP-V8 component: {html.escape(summary['ppv8_component_method'])}, fidelity RMSE_log {html.escape(str(summary['ppv8_fidelity_RMSE_log']))}, MdAE_log {html.escape(str(summary['ppv8_fidelity_MdAE_log']))}</p>
<h2>전체 숫자 라벨 기준</h2>{all_scope.to_html(index=False, escape=True)}
<h2>50달러 미만 제외 기준</h2>{filtered_scope.to_html(index=False, escape=True)}
<h2>Segment 비교</h2>{segment_metrics.to_html(index=False, escape=True)}
<h2>큰 오차 상위</h2>{top_errors.to_html(index=False, escape=True)}
<p>{html.escape(summary['reproduction_note'])}</p></body></html>"""
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    args = parse_args()
    prediction_file = resolve(args.predictions)
    label_file = resolve(args.labels)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not prediction_file.exists():
        raise FileNotFoundError(f"prediction file not found: {prediction_file}")
    if not label_file.exists():
        raise FileNotFoundError(f"label file not found: {label_file}")

    pred = pd.read_csv(prediction_file, low_memory=False)
    labels = pd.read_csv(label_file, low_memory=False).reset_index().rename(columns={"index": "_v01_row_id"})
    labels["_v01_row_id"] = labels["_v01_row_id"].astype(int)
    keep = ["_v01_row_id", "sale_message", "availability", "is_for_sale", "is_sold", "price_currency"]
    keep = [col for col in keep if col in labels.columns]
    merged = pred.merge(labels[keep], on="_v01_row_id", how="left")
    merged = add_actual_columns(merged)
    merged = add_error_columns(merged)
    metrics = build_metrics(merged)
    segment_metrics = build_segment_metrics(merged)
    prediction_summary_path = prediction_file.parent / "prediction_summary.json"
    prediction_summary = {}
    if prediction_summary_path.exists():
        prediction_summary = json.loads(prediction_summary_path.read_text(encoding="utf-8"))
    ppv8_info = prediction_summary.get("pp_v8_component_info", {})
    ppv8_fidelity = ppv8_info.get("fidelity_test_from_validation_only", {})

    merged.to_csv(output_dir / "predictions_with_actual_and_errors.csv", index=False)
    metrics.to_csv(output_dir / "candidate_metrics.csv", index=False)
    segment_metrics.to_csv(output_dir / "segment_metrics.csv", index=False)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prediction_file": str(prediction_file.relative_to(REPO)),
        "label_file": str(label_file.relative_to(REPO)),
        "output_dir": str(output_dir.relative_to(REPO)),
        "total_rows": int(len(merged)),
        "numeric_actual_rows": int(merged["actual_price_krw"].notna().sum()),
        "very_low_price_rows": int(((merged["actual_price_krw"].notna()) & (merged["actual_price_usd_equiv"] < 50)).sum()),
        "reproduction_note": "v0.1 70:30 정책 식은 적용했지만 PP-V8 30% component는 기존 PP-V8 예측을 모사한 distillation component이다.",
        "ppv8_component_method": str(ppv8_info.get("interpretation", "unknown")),
        "ppv8_fidelity_RMSE_log": None if "RMSE_log" not in ppv8_fidelity else round(float(ppv8_fidelity["RMSE_log"]), 4),
        "ppv8_fidelity_MdAE_log": None if "MdAE_log" not in ppv8_fidelity else round(float(ppv8_fidelity["MdAE_log"]), 4),
        "outputs": {
            "predictions_with_actual_and_errors": str((output_dir / "predictions_with_actual_and_errors.csv").relative_to(REPO)),
            "candidate_metrics": str((output_dir / "candidate_metrics.csv").relative_to(REPO)),
            "segment_metrics": str((output_dir / "segment_metrics.csv").relative_to(REPO)),
            "report_md": str((REPORT_DIR / "result_report.md").relative_to(REPO)),
            "report_html": str((REPORT_DIR / "result_report.html").relative_to(REPO)),
        },
    }
    (output_dir / "comparison_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(output_dir, metrics, segment_metrics, merged, summary)
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
