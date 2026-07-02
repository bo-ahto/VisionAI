#!/usr/bin/env python3
"""Run PP-WMIN10: official API fixed-test parity for WMIN8 Warm route."""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN10"
EXP_SLUG = "PP-WMIN10_warm_wmin8_api_fixed_test_parity"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin10_warm_wmin8_api_fixed_test_parity_summary.md"

TEST_WARM = REPO / "data" / "track6_split" / "track6_test_warm.csv"
WMIN8_PREDICTIONS = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router" / "outputs" / "candidate_predictions.csv"
SELECTED_CANDIDATE = "min1_route_w850_risk_q50_altlower_gap005"
DEFAULT_BASE_URL = "http://127.0.0.1:8031"


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def safe_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def safe_int(value: object) -> int | None:
    number = safe_float(value)
    return int(round(number)) if number is not None else None


def safe_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and not math.isfinite(value):
        return default
    text = str(value).strip()
    return text if text else default


def krw_from_log(value: float | None) -> int | None:
    if value is None or not math.isfinite(value):
        return None
    return int(round(math.exp(value)))


def load_eval_rows(limit: int | None = None) -> pd.DataFrame:
    test = pd.read_csv(TEST_WARM, low_memory=False)
    pred_cols = [
        "candidate_label",
        "eval_split",
        "_track6_row_id",
        "pred_log",
        "actual_log",
        "actual_price",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
        "confidence_tier",
    ]
    pred = pd.read_csv(WMIN8_PREDICTIONS, usecols=pred_cols, low_memory=False)
    selected = pred[
        pred["candidate_label"].eq(SELECTED_CANDIDATE)
        & pred["eval_split"].eq("test")
    ].copy()
    selected = selected.rename(
        columns={
            "pred_log": "expected_wmin8_pred_log",
            "actual_log": "expected_actual_log",
            "actual_price": "expected_actual_price",
            "confidence_tier": "expected_confidence_tier",
        }
    )
    rows = test.merge(selected, on="_track6_row_id", how="inner")
    rows = rows.sort_values("_track6_row_id").reset_index(drop=True)
    if limit is not None:
        rows = rows.head(limit).copy()
    return rows


def build_payload(row: pd.Series) -> dict[str, Any]:
    return {
        "artwork": {
            "title": safe_str(row.get("title_raw"), "Untitled"),
            "artist": {
                "selected_artist_key": safe_str(row.get("artist_key")),
                "name_ko": safe_str(row.get("artist_name_ko"), None),
            },
            "year": safe_int(row.get("date")),
            "category": "Painting",
            "dimensions": {
                "width_cm": safe_float(row.get("width_cm")),
                "height_cm": safe_float(row.get("height_cm")),
                "depth_cm": safe_float(row.get("depth_cm")) if safe_float(row.get("depth_cm")) is not None else 0,
            },
            "medium": {
                "medium_category": safe_str(row.get("medium_category"), "unknown"),
                "support_category": safe_str(row.get("support_category"), "unknown"),
            },
            "artwork_url": safe_str(row.get("artwork_url"), None),
            "source_artwork_id": safe_str(row.get("source_artwork_id"), None),
            "external_artwork_id": safe_str(row.get("source_artwork_id"), None),
        },
        "options": {
            "include_comparable_samples": False,
            "max_comparable_samples": 0,
            "include_calculation_steps": True,
            "include_debug_fields": True,
        },
    }


def adapter_output(response: dict[str, Any]) -> dict[str, Any]:
    summary = response.get("calculation_summary") or {}
    for step in summary.get("steps") or []:
        output = step.get("output") or {}
        if output.get("adapter_output") is not None:
            return output.get("adapter_output") or {}
    return {}


def call_api(session: requests.Session, base_url: str, row: pd.Series, timeout: float) -> dict[str, Any]:
    response = session.post(
        f"{base_url.rstrip('/')}/api/v1/artworks/price-estimate",
        json=build_payload(row),
        timeout=timeout,
    )
    payload: dict[str, Any]
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_text": response.text[:1000]}
    if response.status_code >= 400:
        return {
            "http_status": response.status_code,
            "api_status": payload.get("status"),
            "error_code": (payload.get("error") or {}).get("code"),
            "error_message": (payload.get("error") or {}).get("message"),
        }
    out = adapter_output(payload)
    prediction = payload.get("prediction") or {}
    routing = payload.get("routing") or {}
    summary = payload.get("calculation_summary") or {}
    route_gate = out.get("route_gate") or {}
    return {
        "http_status": response.status_code,
        "api_status": payload.get("status"),
        "route": payload.get("route"),
        "display_route": payload.get("display_route"),
        "adapter_execution_level": summary.get("adapter_execution_level"),
        "warning_codes": ",".join(str(item.get("code")) for item in payload.get("warnings", [])),
        "api_price_krw": prediction.get("price_krw"),
        "api_range_low_krw": (prediction.get("range_krw") or {}).get("low"),
        "api_range_high_krw": (prediction.get("range_krw") or {}).get("high"),
        "api_final_log_price": out.get("final_log_price"),
        "api_base_log_price": out.get("base_log_price"),
        "api_alternative_log_price": out.get("alternative_log_price"),
        "api_selected_runtime_role": out.get("selected_runtime_role"),
        "api_use_alternative": route_gate.get("use_alternative"),
        "api_risk_score": route_gate.get("risk_score"),
        "api_component_prediction_spread": route_gate.get("component_prediction_spread"),
        "api_current_vs_stable_gap_abs": route_gate.get("current_vs_stable_gap_abs"),
        "api_stable_price_band": route_gate.get("stable_price_band"),
        "same_artist_training_price_count": routing.get("same_artist_training_price_count"),
        "error_code": None,
        "error_message": None,
    }


def existing_completed(path: Path) -> set[int]:
    if not path.exists():
        return set()
    try:
        df = pd.read_csv(path, usecols=["_track6_row_id"])
    except Exception:
        return set()
    return set(pd.to_numeric(df["_track6_row_id"], errors="coerce").dropna().astype(int))


def append_row(path: Path, row: dict[str, Any]) -> None:
    frame = pd.DataFrame([row])
    frame.to_csv(path, mode="a", index=False, header=not path.exists())


def summarize(rows: pd.DataFrame) -> pd.DataFrame:
    ok = rows[
        rows["http_status"].eq(200)
        & rows["route"].eq("warm")
        & rows["adapter_execution_level"].eq("report_model_adapter")
    ].copy()
    log_diff = pd.to_numeric(ok["log_diff"], errors="coerce").abs()
    price_diff_pct = pd.to_numeric(ok["price_diff_pct"], errors="coerce").abs()
    return pd.DataFrame(
        [
            {
                "n_total": int(len(rows)),
                "n_success": int(len(ok)),
                "n_error": int((rows["http_status"] != 200).sum()),
                "n_wrong_route": int((rows["route"] != "warm").sum()),
                "n_wrong_adapter": int((rows["adapter_execution_level"] != "report_model_adapter").sum()),
                "max_abs_log_diff": float(log_diff.max()) if len(log_diff) else np.nan,
                "mean_abs_log_diff": float(log_diff.mean()) if len(log_diff) else np.nan,
                "median_abs_log_diff": float(log_diff.median()) if len(log_diff) else np.nan,
                "p95_abs_log_diff": float(log_diff.quantile(0.95)) if len(log_diff) else np.nan,
                "max_abs_price_diff_pct": float(price_diff_pct.max()) if len(price_diff_pct) else np.nan,
                "mean_abs_price_diff_pct": float(price_diff_pct.mean()) if len(price_diff_pct) else np.nan,
                "n_log_diff_le_1e_10": int((log_diff <= 1e-10).sum()) if len(log_diff) else 0,
                "n_log_diff_le_1e_3": int((log_diff <= 1e-3).sum()) if len(log_diff) else 0,
                "n_log_diff_le_1e_2": int((log_diff <= 1e-2).sum()) if len(log_diff) else 0,
            }
        ]
    )


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_rows 없음_"
    text = frame.copy()
    for col in text.columns:
        text[col] = text[col].map(lambda value: "" if pd.isna(value) else str(value))
    headers = [str(col) for col in text.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in text.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in text.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(rows: pd.DataFrame, summary: pd.DataFrame, elapsed_sec: float) -> None:
    top = rows.copy()
    top["abs_log_diff"] = pd.to_numeric(top["log_diff"], errors="coerce").abs()
    top = top.sort_values("abs_log_diff", ascending=False).head(20)
    lines = [
        "# PP-WMIN10 Warm WMIN8 API Fixed-Test Parity",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 실행 시간: {elapsed_sec:.1f}s",
        f"- 비교 후보: `{SELECTED_CANDIDATE}`",
        "- 목적: WMIN8 fixed test 607건을 official v0.1 HTTP API로 재생해 endpoint 출력과 실험 산출물의 row-level parity를 확인한다.",
        "",
        "## 1. Summary",
        "",
        markdown_table(summary.round(12)),
        "",
        "## 2. Largest Absolute Log Differences",
        "",
    ]
    cols = [
        "_track6_row_id",
        "artist_key",
        "expected_wmin8_pred_log",
        "api_final_log_price",
        "log_diff",
        "expected_wmin8_price_krw",
        "api_price_krw",
        "price_diff_pct",
        "api_selected_runtime_role",
        "expected_stable_price_band",
        "api_stable_price_band",
    ]
    lines.append(markdown_table(top[cols]))
    lines.extend(
        [
            "",
            "## 3. Interpretation",
            "",
            "- `max_abs_log_diff`가 0에 가까우면 API endpoint가 WMIN8 실험 산출물과 동일한 계산 경로를 재현한다.",
            "- 차이가 크면 우선 `stable_price_band`, `component_prediction_spread`, `current_vs_stable_gap_abs` 및 라우팅 선택 차이를 확인한다.",
        ]
    )
    report = "\n".join(lines) + "\n"
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    DOC_SUMMARY.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    start = time.time()
    rows = load_eval_rows(limit=args.limit)
    output_path = OUT_DIR / "api_fixed_test_parity_rows.csv"
    if args.no_resume and output_path.exists():
        output_path.unlink()
    completed = existing_completed(output_path)

    session = requests.Session()
    for idx, row in rows.iterrows():
        row_id = int(row["_track6_row_id"])
        if row_id in completed:
            continue
        result = call_api(session, args.base_url, row, args.timeout)
        expected_log = safe_float(row["expected_wmin8_pred_log"])
        api_log = safe_float(result.get("api_final_log_price"))
        expected_price = krw_from_log(expected_log)
        api_price = safe_float(result.get("api_price_krw"))
        log_diff = api_log - expected_log if api_log is not None and expected_log is not None else np.nan
        price_diff_pct = (
            (api_price - expected_price) / max(float(expected_price), 1.0)
            if api_price is not None and expected_price is not None
            else np.nan
        )
        out = {
            "_track6_row_id": row_id,
            "row_number": int(idx),
            "artist_key": safe_str(row.get("artist_key")),
            "artist_name_ko": safe_str(row.get("artist_name_ko")),
            "title_raw": safe_str(row.get("title_raw")),
            "actual_price": safe_float(row.get("expected_actual_price")),
            "expected_wmin8_pred_log": expected_log,
            "expected_wmin8_price_krw": expected_price,
            "expected_quantile_width": safe_float(row.get("quantile_width")),
            "expected_component_prediction_spread": safe_float(row.get("component_prediction_spread")),
            "expected_current_vs_stable_gap_abs": safe_float(row.get("current_vs_stable_gap_abs")),
            "expected_stable_price_band": safe_str(row.get("stable_price_band")),
            "expected_confidence_tier": safe_str(row.get("expected_confidence_tier")),
            **result,
            "log_diff": log_diff,
            "price_diff_pct": price_diff_pct,
        }
        append_row(output_path, out)
        if (idx + 1) % 50 == 0:
            print(json.dumps({"processed": idx + 1, "row_id": row_id}, ensure_ascii=False))

    result_rows = pd.read_csv(output_path, low_memory=False)
    result_rows = result_rows.sort_values("_track6_row_id").reset_index(drop=True)
    result_rows.to_csv(output_path, index=False)
    summary = summarize(result_rows)
    summary.to_csv(OUT_DIR / "api_fixed_test_parity_summary.csv", index=False)
    run_config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "limit": args.limit,
        "selected_candidate": SELECTED_CANDIDATE,
        "source_test_warm": str(TEST_WARM.relative_to(REPO)),
        "source_wmin8_predictions": str(WMIN8_PREDICTIONS.relative_to(REPO)),
        "output_rows": str(output_path.relative_to(REPO)),
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(result_rows, summary, time.time() - start)
    print(json.dumps({"status": "completed", **summary.iloc[0].to_dict()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
