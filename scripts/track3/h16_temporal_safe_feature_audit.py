"""Track 3 H16 — temporal-safe feature feasibility audit."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h16_temporal_safe_feature_audit.json"

DATE_CANDIDATES = [
    "sale_date",
    "sold_date",
    "transaction_date",
    "auction_date",
    "created_at",
    "registered_at",
    "listed_at",
    "year",
    "creation_year",
]

REQUIRED_FOR_TEMPORAL_HISTORY = [
    "artist_name_ko",
    "ln_price_krw_unified",
    "price_krw_unified",
]


def audit_file(path: Path) -> dict:
    df = pd.read_csv(path, nrows=5)
    cols = list(df.columns)
    found_dates = [col for col in DATE_CANDIDATES if col in cols]
    missing_required = [col for col in REQUIRED_FOR_TEMPORAL_HISTORY if col not in cols]
    return {
        "columns": cols,
        "date_columns_found": found_dates,
        "missing_required_columns": missing_required,
        "can_order_artist_history_by_time": bool(found_dates and not missing_required),
    }


def main() -> None:
    files = ["track3_train.csv", "track3_test_warm.csv", "track3_test_cold.csv"]
    result = {
        "experiment_id": "H16_temporal_safe_feature_audit",
        "date_candidates": DATE_CANDIDATES,
        "required_columns": REQUIRED_FOR_TEMPORAL_HISTORY,
        "files": {file: audit_file(SPLIT / file) for file in files},
    }
    result["judgement"] = {
        "can_run_temporal_safe_revalidation": all(
            row["can_order_artist_history_by_time"] for row in result["files"].values()
        ),
        "reason": "release split has no transaction/listing date column for ordering artist history",
        "next_requirement": "add sale_date, transaction_date, auction_date, or another reliable prediction-time column",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print("H16 temporal-safe feature audit")
    print(f"saved: {OUT_PATH}")
    for file, row in result["files"].items():
        print(
            f"{file:<22} date_cols={row['date_columns_found']} "
            f"can_order={row['can_order_artist_history_by_time']}"
        )
    print(f"can_run={result['judgement']['can_run_temporal_safe_revalidation']}")


if __name__ == "__main__":
    main()
