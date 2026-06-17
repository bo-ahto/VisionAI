#!/usr/bin/env python3
"""HTTP API parity for official v0.1 Warm-lite Quantile residual bundle."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter  # noqa: E402
from visionai.price_engine.api.official_v0_1_schemas import PriceEstimateRequest  # noqa: E402


DEFAULT_BASE_URL = "http://127.0.0.1:8031"
OUT = REPO / "experiments" / "track6" / "PP-WLITE-Q5_quantile_residual_bundle_api_parity"


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)


def case_rows(max_cases: int) -> pd.DataFrame:
    import sqlite3

    db = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
    query = """
    SELECT r.artist_key, r.valid_price_count, o.title, o.width_cm, o.height_cm, o.depth_cm,
           o.medium_category, o.support_category
    FROM artist_registry r
    JOIN artwork_price_observations o ON o.artist_key = r.artist_key
    WHERE r.valid_price_count BETWEEN 1 AND 4
      AND o.price_krw IS NOT NULL
      AND o.width_cm IS NOT NULL
      AND o.height_cm IS NOT NULL
      AND o.medium_category IS NOT NULL
      AND o.support_category IS NOT NULL
    GROUP BY r.artist_key
    ORDER BY r.valid_price_count, r.artist_key
    LIMIT ?
    """
    with sqlite3.connect(db) as conn:
        return pd.read_sql_query(query, conn, params=(max_cases,))


def payload_from_row(row: pd.Series) -> dict[str, Any]:
    depth = row.get("depth_cm")
    try:
        depth = float(depth)
    except (TypeError, ValueError):
        depth = 0.0
    if not math.isfinite(depth) or depth < 0:
        depth = 0.0
    return {
        "artwork": {
            "title": str(row.get("title") or "warm-lite parity check"),
            "artist": {"selected_artist_key": str(row["artist_key"])},
            "year": 2020,
            "category": "Painting",
            "dimensions": {
                "width_cm": float(row["width_cm"]),
                "height_cm": float(row["height_cm"]),
                "depth_cm": depth,
            },
            "medium": {
                "medium_category": str(row["medium_category"]),
                "support_category": str(row["support_category"]),
            },
        },
        "options": {
            "include_comparable_samples": False,
            "max_comparable_samples": 0,
            "include_calculation_steps": True,
            "include_debug_fields": True,
        },
    }


def extract_api_log(response: dict[str, Any]) -> float | None:
    for step in response.get("calculation_summary", {}).get("steps", []):
        output = step.get("output") or {}
        adapter_output = output.get("adapter_output") or {}
        if "warm_lite_pred_log" in adapter_output:
            return float(adapter_output["warm_lite_pred_log"])
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--max-cases", type=int, default=24)
    parser.add_argument("--tolerance-log", type=float, default=1e-12)
    args = parser.parse_args()

    ensure_dirs()
    adapter = ReportModelProxyAdapter()
    rows = []
    for _, row in case_rows(args.max_cases).iterrows():
        payload = payload_from_row(row)
        request_model = PriceEstimateRequest.model_validate(payload)
        direct = adapter.predict_warm_lite(request_model, str(row["artist_key"]))
        response = requests.post(
            f"{args.base_url}/api/v1/artworks/price-estimate",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        api_log = extract_api_log(body)
        api_price = body.get("prediction", {}).get("price_krw")
        direct_log = direct.output.get("warm_lite_pred_log")
        rows.append(
            {
                "artist_key": row["artist_key"],
                "history_count": int(row["valid_price_count"]),
                "route": body.get("route"),
                "adapter_execution_level": body.get("calculation_summary", {}).get("adapter_execution_level"),
                "direct_price_krw": direct.price_krw,
                "api_price_krw": api_price,
                "direct_log": direct_log,
                "api_log": api_log,
                "abs_log_diff": (
                    abs(float(api_log) - float(direct_log))
                    if api_log is not None and direct_log is not None
                    else math.inf
                ),
                "price_match": int(api_price or -1) == int(direct.price_krw or -2),
                "route_ok": body.get("route") == "warm_lite",
                "adapter_ok": body.get("calculation_summary", {}).get("adapter_execution_level") == "report_model_adapter",
            }
        )

    out = pd.DataFrame(rows)
    passed = bool(
        len(out) > 0
        and out["route_ok"].all()
        and out["adapter_ok"].all()
        and out["price_match"].all()
        and np.isfinite(out["abs_log_diff"]).all()
        and float(out["abs_log_diff"].max()) <= args.tolerance_log
    )
    summary = {
        "experiment_id": "PP-WLITE-Q5",
        "check": "official_v0_1_http_api_parity",
        "base_url": args.base_url,
        "n_cases": int(len(out)),
        "max_abs_log_diff": float(out["abs_log_diff"].max()) if len(out) else None,
        "n_price_mismatch": int((~out["price_match"]).sum()) if len(out) else 0,
        "n_route_mismatch": int((~out["route_ok"]).sum()) if len(out) else 0,
        "n_adapter_mismatch": int((~out["adapter_ok"]).sum()) if len(out) else 0,
        "passed": passed,
    }
    out.to_csv(OUT / "outputs" / "official_v0_1_api_parity_rows.csv", index=False)
    (OUT / "artifacts" / "official_v0_1_api_parity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-WLITE-Q5 official v0.1 API parity",
            "",
            f"- Passed: `{passed}`",
            f"- Cases: `{summary['n_cases']}`",
            f"- Max abs log diff: `{summary['max_abs_log_diff']}`",
            f"- Price mismatches: `{summary['n_price_mismatch']}`",
            f"- Route mismatches: `{summary['n_route_mismatch']}`",
            f"- Adapter mismatches: `{summary['n_adapter_mismatch']}`",
            "",
        ]
    )
    (OUT / "reports" / "official_v0_1_api_parity_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
