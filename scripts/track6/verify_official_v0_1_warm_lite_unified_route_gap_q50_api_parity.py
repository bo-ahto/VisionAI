#!/usr/bin/env python3
"""HTTP API parity for the default unified Warm-lite route_gap_q50 policy."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "track6"))

import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402
from visionai.price_engine.api.official_v0_1_report_adapters import ReportModelProxyAdapter  # noqa: E402
from visionai.price_engine.api.official_v0_1_schemas import PriceEstimateRequest  # noqa: E402


DEFAULT_BASE_URL = "http://127.0.0.1:8031"
OUT = REPO / "experiments" / "track6" / "PP-ROUTE-CF11_unified_route_gap_q50_api_parity"
CF9 = REPO / "experiments" / "track6" / "PP-ROUTE-CF9_conditional_cf7_router"
POLICY_ENV = "PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY"
POLICY_VALUE = "warm_lite_unified_route_gap_q50"


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)


def source_rows(split: str, max_cases: int | None) -> pd.DataFrame:
    needed = unique(
        artifact_features()["warm"]
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    _train, val, test = load_scope("warm", needed)
    parts = []
    if split in {"validation", "both"}:
        v = val.copy()
        v["split"] = "validation"
        parts.append(v)
    if split in {"test", "both"}:
        t = test.copy()
        t["split"] = "test"
        parts.append(t)
    out = pd.concat(parts, ignore_index=True).sort_values(["split", "_track6_row_id"]).reset_index(drop=True)
    if max_cases is not None and max_cases > 0:
        out = out.head(max_cases).copy()
    return out


def reference_predictions() -> pd.DataFrame:
    val = pd.read_csv(CF9 / "outputs" / "validation_router_candidate_predictions.csv", low_memory=False)
    test = pd.read_csv(CF9 / "outputs" / "test_router_candidate_predictions.csv", low_memory=False)
    ref = pd.concat([val, test], ignore_index=True)
    ref = ref[ref["candidate"].eq("route_gap_q50")].copy()
    return ref[["_track6_row_id", "split", "pred_log", "route_to_cf7"]].rename(
        columns={"pred_log": "cf9_reference_log", "route_to_cf7": "cf9_route_to_cf7"}
    )


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
            "title": f"route_gap_q50 parity row {int(row['_track6_row_id'])}",
            "source_artwork_id": str(int(row["_track6_row_id"])),
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


def extract_adapter_output(response: dict[str, Any]) -> dict[str, Any]:
    for step in response.get("calculation_summary", {}).get("steps", []):
        output = step.get("output") or {}
        adapter_output = output.get("adapter_output") or {}
        if "warm_lite_unified_route_gap_q50_pred_log" in adapter_output:
            return adapter_output
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--split", choices=["validation", "test", "both"], default="test")
    parser.add_argument("--max-cases", type=int, default=0, help="0 means all selected split rows")
    parser.add_argument("--tolerance-log", type=float, default=1e-10)
    args = parser.parse_args()

    ensure_dirs()
    env_value = os.getenv(POLICY_ENV)
    if env_value not in {None, "", POLICY_VALUE}:
        print(
            json.dumps(
                {
                    "warning": "server may not be running with the unified policy",
                    "expected_default_or_env": f"default unified or {POLICY_ENV}={POLICY_VALUE}",
                    "actual_env": env_value,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

    selected = source_rows(args.split, None if args.max_cases == 0 else args.max_cases)
    selected = selected.merge(reference_predictions(), on=["_track6_row_id", "split"], how="left", validate="one_to_one")
    adapter = ReportModelProxyAdapter()

    rows = []
    for _, row in selected.iterrows():
        payload = payload_from_row(row)
        request_model = PriceEstimateRequest.model_validate(payload)
        direct = adapter.predict_warm_lite_unified_route_gap_q50(request_model, str(row["artist_key"]))
        response = requests.post(
            f"{args.base_url}/api/v1/artworks/price-estimate",
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        body = response.json()
        adapter_output = extract_adapter_output(body)
        direct_log = float(direct.output["warm_lite_unified_route_gap_q50_pred_log"])
        api_log = adapter_output.get("warm_lite_unified_route_gap_q50_pred_log")
        cf9_log = row.get("cf9_reference_log")
        rows.append(
            {
                "split": row["split"],
                "_track6_row_id": int(row["_track6_row_id"]),
                "artist_key": row["artist_key"],
                "history_count": direct.output.get("artist_history_n"),
                "route": body.get("route"),
                "adapter_execution_level": body.get("calculation_summary", {}).get("adapter_execution_level"),
                "direct_log": direct_log,
                "api_log": float(api_log) if api_log is not None else np.nan,
                "cf9_reference_log": float(cf9_log) if pd.notna(cf9_log) else np.nan,
                "abs_api_direct_log_diff": (
                    abs(float(api_log) - direct_log) if api_log is not None else math.inf
                ),
                "abs_direct_cf9_log_diff": (
                    abs(direct_log - float(cf9_log)) if pd.notna(cf9_log) else math.inf
                ),
                "api_route_to_cf7": adapter_output.get("route_to_cf7"),
                "cf9_route_to_cf7": bool(row["cf9_route_to_cf7"]) if pd.notna(row.get("cf9_route_to_cf7")) else None,
                "route_ok": body.get("route") == "warm_lite",
                "adapter_ok": body.get("calculation_summary", {}).get("adapter_execution_level") == "report_model_adapter",
                "unified_output_ok": api_log is not None,
            }
        )

    out = pd.DataFrame(rows)
    out["cf9_route_match"] = out["api_route_to_cf7"].astype("boolean") == out["cf9_route_to_cf7"].astype("boolean")
    passed = bool(
        len(out) > 0
        and out["route_ok"].all()
        and out["adapter_ok"].all()
        and out["unified_output_ok"].all()
        and out["cf9_route_match"].fillna(False).all()
        and np.isfinite(out["abs_api_direct_log_diff"]).all()
        and np.isfinite(out["abs_direct_cf9_log_diff"]).all()
        and float(out["abs_api_direct_log_diff"].max()) <= args.tolerance_log
        and float(out["abs_direct_cf9_log_diff"].max()) <= args.tolerance_log
    )
    by_split = []
    for split, group in out.groupby("split", sort=True):
        by_split.append(
            {
                "split": split,
                "n": int(len(group)),
                "max_abs_api_direct_log_diff": float(group["abs_api_direct_log_diff"].max()),
                "max_abs_direct_cf9_log_diff": float(group["abs_direct_cf9_log_diff"].max()),
                "n_route_mismatch": int((~group["route_ok"]).sum()),
                "n_adapter_mismatch": int((~group["adapter_ok"]).sum()),
                "n_cf9_route_mismatch": int((~group["cf9_route_match"].fillna(False)).sum()),
            }
        )
    summary = {
        "experiment_id": "PP-ROUTE-CF11",
        "check": "official_v0_1_default_unified_route_gap_q50_http_api_parity",
        "base_url": args.base_url,
        "server_policy": f"default unified or {POLICY_ENV}={POLICY_VALUE}",
        "actual_env": env_value,
        "split": args.split,
        "n_cases": int(len(out)),
        "max_abs_api_direct_log_diff": float(out["abs_api_direct_log_diff"].max()) if len(out) else None,
        "max_abs_direct_cf9_log_diff": float(out["abs_direct_cf9_log_diff"].max()) if len(out) else None,
        "n_route_mismatch": int((~out["route_ok"]).sum()) if len(out) else 0,
        "n_adapter_mismatch": int((~out["adapter_ok"]).sum()) if len(out) else 0,
        "n_unified_output_missing": int((~out["unified_output_ok"]).sum()) if len(out) else 0,
        "n_cf9_route_mismatch": int((~out["cf9_route_match"].fillna(False)).sum()) if len(out) else 0,
        "passed": passed,
        "by_split": by_split,
    }
    out.to_csv(OUT / "outputs" / "official_v0_1_unified_route_gap_q50_api_parity_rows.csv", index=False)
    (OUT / "artifacts" / "official_v0_1_unified_route_gap_q50_api_parity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = "\n".join(
        [
            "# PP-ROUTE-CF11 official v0.1 default unified route_gap_q50 API parity",
            "",
            "```json",
            json.dumps(summary, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    (OUT / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
