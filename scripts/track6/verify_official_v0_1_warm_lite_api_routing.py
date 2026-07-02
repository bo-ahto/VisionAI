"""Verify official v0.1 API routing for cold, warm-lite, and warm cases."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


DEFAULT_BASE_URL = "http://127.0.0.1:8031"


CASES = [
    {
        "case": "unknown_artist_cold",
        "expected_route": "cold",
        "artist": {"name_en": "unknown local api test artist"},
    },
    {
        "case": "one_price_history_warm_lite",
        "expected_route": "warm_lite",
        "artist": {"selected_artist_key": "mu ri"},
    },
    {
        "case": "four_price_history_warm_lite",
        "expected_route": "warm_lite",
        "artist": {"selected_artist_key": "sunny jung"},
    },
    {
        "case": "five_plus_price_history_warm",
        "expected_route": "warm",
        "artist": {"selected_artist_key": "marina lyu"},
    },
]


def build_payload(artist: dict[str, Any]) -> dict[str, Any]:
    return {
        "artwork": {
            "title": "local official v0.1 routing check",
            "artist": artist,
            "year": 2020,
            "category": "Painting",
            "dimensions": {"width_cm": 72.7, "height_cm": 60.6, "depth_cm": 0},
            "medium": {"medium_category": "painting", "support_category": "canvas"},
        },
        "options": {
            "include_comparable_samples": True,
            "max_comparable_samples": 5,
            "include_calculation_steps": True,
            "include_debug_fields": True,
        },
    }


def compact_result(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    prediction = response.get("prediction", {})
    routing = response.get("routing", {})
    summary = response.get("calculation_summary", {})
    return {
        "case": case["case"],
        "expected_route": case["expected_route"],
        "actual_route": response.get("route"),
        "display_route": response.get("display_route"),
        "route_ok": response.get("route") == case["expected_route"],
        "price_krw": prediction.get("price_krw"),
        "range_krw": prediction.get("range_krw"),
        "confidence": prediction.get("confidence", {}).get("level"),
        "same_artist_training_price_count": routing.get("same_artist_training_price_count"),
        "adapter_execution_level": summary.get("adapter_execution_level"),
        "warnings": [item.get("code") for item in response.get("warnings", [])],
    }


def call_estimate(base_url: str, case: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{base_url}/api/v1/artworks/price-estimate",
        json=build_payload(case["artist"]),
        timeout=30,
    )
    response.raise_for_status()
    return compact_result(case, response.json())


def deterministic_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    price_range = row.get("range_krw") or {}
    return (
        row.get("actual_route"),
        row.get("display_route"),
        row.get("price_krw"),
        price_range.get("low"),
        price_range.get("mid"),
        price_range.get("high"),
        row.get("confidence"),
        row.get("same_artist_training_price_count"),
        row.get("adapter_execution_level"),
        tuple(row.get("warnings") or []),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    rows = []
    for case in CASES:
        repeats = [call_estimate(args.base_url, case) for _ in range(args.repeat)]
        first = repeats[0]
        first["repeat_count"] = args.repeat
        first["deterministic_repeat_ok"] = len({deterministic_signature(row) for row in repeats}) == 1
        rows.append(first)

    print(json.dumps(rows, ensure_ascii=False, indent=2))
    if not all(row["route_ok"] and row["deterministic_repeat_ok"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
