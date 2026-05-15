"""Track 3 H15 — missing pattern feature audit.

Checks whether current release split has missingness variance for H15.
If there is no missingness, missing-pattern features cannot be evaluated.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parent.parent.parent
SPLIT = REPO / "data" / "release_split"
OUT_PATH = REPO / "data" / "track3_h15_missing_pattern_audit.json"

CORE_COLS = [
    "artist_name_ko",
    "medium_category",
    "support_category",
    "depth_cm",
    "width_cm",
    "height_cm",
    "log_area",
    "estimated_ho",
    "orientation",
]


def audit_file(path: Path) -> dict:
    df = pd.read_csv(path)
    missing = df[CORE_COLS].isna()
    blank = df[CORE_COLS].astype(str).apply(lambda s: s.str.strip().eq(""))
    missing_or_blank = missing | blank
    row_missing_count = missing_or_blank.sum(axis=1)
    return {
        "rows": int(len(df)),
        "column_missing_or_blank": {col: int(missing_or_blank[col].sum()) for col in CORE_COLS},
        "rows_with_any_missing": int((row_missing_count > 0).sum()),
        "missing_count_distribution": {str(k): int(v) for k, v in row_missing_count.value_counts().sort_index().items()},
        "has_missing_signal": bool((row_missing_count > 0).any()),
    }


def main() -> None:
    files = ["track3_train.csv", "track3_test_warm.csv", "track3_test_cold.csv"]
    result = {
        "experiment_id": "H15_missing_pattern_audit",
        "core_columns": CORE_COLS,
        "files": {file: audit_file(SPLIT / file) for file in files},
    }
    result["judgement"] = {
        "can_run_missing_pattern_feature_experiment": any(
            row["has_missing_signal"] for row in result["files"].values()
        ),
        "reason": "current release split has no missing/blank values in core columns",
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print("H15 missing pattern audit")
    print(f"saved: {OUT_PATH}")
    for file, row in result["files"].items():
        print(
            f"{file:<22} rows={row['rows']} "
            f"rows_with_missing={row['rows_with_any_missing']} "
            f"has_signal={row['has_missing_signal']}"
        )
    print(f"can_run={result['judgement']['can_run_missing_pattern_feature_experiment']}")


if __name__ == "__main__":
    main()
