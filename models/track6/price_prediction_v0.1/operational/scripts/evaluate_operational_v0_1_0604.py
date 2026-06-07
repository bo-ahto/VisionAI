#!/usr/bin/env python3
"""Evaluate operational v0.1 predictions against the labeled 0604 CSV."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "models" / "track6").exists() and (current / "data").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
OP_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1" / "operational"
DEFAULT_PREDICTION = OP_ROOT / "outputs" / "0604_predictions" / "predictions_all.csv"
DEFAULT_LABEL = REPO / "data" / "test_new_artworks_test_0604.csv"
DEFAULT_OUTPUT_DIR = OP_ROOT / "outputs" / "0604_evaluation"
REPORT_DIR = OP_ROOT / "reports"

FX = {"USD": 1380.0, "EUR": 1530.0, "KRW": 1.0, "GBP": 1780.0, "HKD": 178.0, "JPY": 9.5}
CANDIDATES = {
    "svc_numeric_seed_mean": "svc_numeric_seed_mean_pred_price_krw",
    "pp_v2_defensive": "pp_v2_defensive_pred_price_krw",
    "l10_generated_bucket_seq": "l10_generated_bucket_seq_pred_price_krw",
    "pp_v8_compact_blend_mape_guarded": "pp_v8_compact_blend_mape_guarded_pred_price_krw",
    "v01_operational": "v01_operational_pred_price_krw",
    "service_primary": "service_primary_pred_price_krw",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate operational v0.1 on labeled 0604 data.")
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTION)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
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
    return native, currency, native * FX[currency]


def add_actual(frame: pd.DataFrame) -> pd.DataFrame:
    parsed = frame["sale_message"].apply(parse_price)
    frame[["actual_price_native", "actual_currency", "actual_price_krw"]] = pd.DataFrame(parsed.tolist(), index=frame.index)
    frame["actual_price_usd_equiv"] = frame["actual_price_krw"] / FX["USD"]
    return frame


def add_candidate_error_columns(frame: pd.DataFrame) -> pd.DataFrame:
    actual = pd.to_numeric(frame["actual_price_krw"], errors="coerce")
    for candidate, col in CANDIDATES.items():
        if col not in frame.columns:
            continue
        pred = pd.to_numeric(frame[col], errors="coerce")
        frame[f"{candidate}_ape"] = ((pred - actual).abs() / actual).replace([np.inf, -np.inf], np.nan)
        frame[f"{candidate}_ratio"] = (pred / actual).replace([np.inf, -np.inf], np.nan)
    return frame


def metric_row(frame: pd.DataFrame, scope: str, candidate: str, price_col: str) -> dict[str, Any]:
    actual = pd.to_numeric(frame["actual_price_krw"], errors="coerce")
    pred = pd.to_numeric(frame[price_col], errors="coerce")
    ape = ((pred - actual).abs() / actual).replace([np.inf, -np.inf], np.nan).dropna()
    log_error = (np.log(pred.clip(lower=1)) - np.log(actual.clip(lower=1))).replace([np.inf, -np.inf], np.nan).dropna()
    ratio = (pred / actual).replace([np.inf, -np.inf], np.nan).dropna()
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


def markdown_table(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(x))
    return "\n".join([
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
        *["| " + " | ".join(row) + " |" for row in view.itertuples(index=False, name=None)],
    ])


def main() -> None:
    args = parse_args()
    pred_path = resolve(args.predictions)
    label_path = resolve(args.labels)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    pred = pd.read_csv(pred_path, low_memory=False)
    labels = pd.read_csv(label_path, low_memory=False).reset_index().rename(columns={"index": "_v01_row_id"})
    labels["_v01_row_id"] = labels["_v01_row_id"].astype(int)
    merged = pred.merge(labels[["_v01_row_id", "sale_message"]], on="_v01_row_id", how="left")
    merged = add_actual(merged)
    merged = add_candidate_error_columns(merged)
    rows: list[dict[str, Any]] = []
    scopes = {
        "numeric_actual_all": merged[merged["actual_price_krw"].notna()].copy(),
        "numeric_actual_excluding_under_50_usd": merged[
            (merged["actual_price_krw"].notna()) & (merged["actual_price_usd_equiv"] >= 50)
        ].copy(),
    }
    for scope, frame in scopes.items():
        for candidate, col in CANDIDATES.items():
            if col in frame.columns:
                rows.append(metric_row(frame, scope, candidate, col))
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output_dir / "operational_candidate_metrics.csv", index=False)
    merged.to_csv(output_dir / "operational_predictions_with_actual.csv", index=False)
    service_error_cols = [
        "_v01_row_id",
        "artist_name",
        "title",
        "actual_currency",
        "actual_price_krw",
        "actual_price_usd_equiv",
        "service_primary_pred_price_krw",
        "service_range_low_price_krw",
        "service_range_high_price_krw",
        "service_confidence_tier",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "l10_price_range_ratio",
        "service_primary_ape",
        "service_primary_ratio",
        "v01_operational_ape",
        "pp_v8_compact_blend_mape_guarded_ape",
    ]
    service_error_cols = [col for col in service_error_cols if col in merged.columns]
    large_errors = merged[merged["actual_price_krw"].notna()].sort_values("service_primary_ape", ascending=False)
    large_errors[service_error_cols].head(100).to_csv(output_dir / "service_primary_largest_errors_top100.csv", index=False)
    large_errors_excluding_under_50 = merged[
        (merged["actual_price_krw"].notna()) & (merged["actual_price_usd_equiv"] >= 50)
    ].sort_values("service_primary_ape", ascending=False)
    large_errors_excluding_under_50[service_error_cols].head(100).to_csv(
        output_dir / "service_primary_largest_errors_excluding_under_50_top100.csv",
        index=False,
    )
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prediction_file": str(pred_path.relative_to(REPO)),
        "label_file": str(label_path.relative_to(REPO)),
        "total_rows": int(len(merged)),
        "numeric_actual_rows": int(merged["actual_price_krw"].notna().sum()),
        "very_low_price_rows": int(((merged["actual_price_krw"].notna()) & (merged["actual_price_usd_equiv"] < 50)).sum()),
        "metrics_file": str((output_dir / "operational_candidate_metrics.csv").relative_to(REPO)),
    }
    (output_dir / "evaluation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    primary_scope = metrics[
        (metrics["scope"].eq("numeric_actual_excluding_under_50_usd"))
        & (metrics["candidate"].eq("service_primary"))
    ]
    primary_mdape = primary_scope["MdAPE"].iloc[0] if not primary_scope.empty else np.nan
    primary_mape = primary_scope["MAPE"].iloc[0] if not primary_scope.empty else np.nan
    primary_p95 = primary_scope["p95_APE"].iloc[0] if not primary_scope.empty else np.nan
    report = f"""# operational v0.1 0604 평가

- 작성일: {summary['created_at']}
- 전체 행: {summary['total_rows']:,}
- 숫자 가격 라벨: {summary['numeric_actual_rows']:,}
- 50달러 미만 검수 필요 라벨: {summary['very_low_price_rows']:,}

## 서비스 적용 판단

- 서비스 주 후보: `service_primary`
- 현재 구현: `pp_v8_compact_blend_mape_guarded`
- 이유: 0604 신규 Warm 라벨에서 70:30 결합보다 MdAPE, MAPE, p95_APE가 모두 낮음
- 50달러 미만 검수 라벨 제외 기준: MdAPE `{primary_mdape:.4f}`, MAPE `{primary_mape:.4f}`, p95_APE `{primary_p95:.4f}`
- 70:30 결합 후보는 보고서 기준 후보로 유지하되, 실제 서비스 출력 기본값은 `service_primary_pred_price_krw`를 사용

## 후보 성능

{markdown_table(metrics.sort_values(['scope', 'MdAPE', 'MAPE']))}

## 추가 산출물

- 후보별 행 단위 오차: `outputs/0604_evaluation/operational_predictions_with_actual.csv`
- 서비스 주 후보 큰 오차 상위 100건: `outputs/0604_evaluation/service_primary_largest_errors_top100.csv`
- 50달러 미만 검수 라벨 제외 큰 오차 상위 100건: `outputs/0604_evaluation/service_primary_largest_errors_excluding_under_50_top100.csv`
"""
    (REPORT_DIR / "operational_0604_evaluation.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
