"""Build a source-preserving Track 4 primary-market raw collected dataset.

This is intentionally different from `track4_primary_market_raw_unified.csv`.

Goal:
- Preserve the original collected columns from each source.
- Do not standardize, infer, derive, or clean values.
- Keep missing columns blank for sources that do not have them.
- Add only minimal audit metadata (`track4_source`, `track4_source_file`,
  `track4_source_row_index`).

Use this file as the first inspection layer before any cleaning rules.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
OUT_CSV = DATA / "track4_primary_market_raw_collected.csv"
OUT_SUMMARY = DATA / "track4_primary_market_raw_collected_summary.json"

SOURCES = [
    ("saatchi", DATA / "saatchi_cleaned.csv"),
    ("artsy", DATA / "artsy_kr_artworks.csv"),
    ("artue", DATA / "artue_테스트_가격포함.csv"),
    ("gallery_primary", DATA / "1차 시장 데이터 - 전달본_260504.csv"),
]


def namespaced_columns(source: str, columns: list[str]) -> list[str]:
    return [f"{source}__{col}" for col in columns]


def load_source(source: str, path: Path) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_csv(path, dtype="string", keep_default_na=False)
    original_columns = list(df.columns)
    df = df.copy()
    df.columns = namespaced_columns(source, original_columns)
    df.insert(0, "track4_source_row_index", range(len(df)))
    df.insert(0, "track4_source_file", str(path.relative_to(REPO)))
    df.insert(0, "track4_source", source)
    return df, original_columns


def main() -> None:
    frames: list[pd.DataFrame] = []
    source_columns: dict[str, list[str]] = {}
    source_rows: dict[str, int] = {}

    for source, path in SOURCES:
        frame, original_columns = load_source(source, path)
        frames.append(frame)
        source_columns[source] = original_columns
        source_rows[source] = int(len(frame))

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = combined.fillna("")
    combined.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "created_at": "2026-05-15",
        "purpose": "source-preserving raw collected union before standardization/cleaning",
        "output": str(OUT_CSV.relative_to(REPO)),
        "n_rows": int(len(combined)),
        "n_columns": int(combined.shape[1]),
        "source_rows": source_rows,
        "source_columns": source_columns,
        "metadata_columns_added": [
            "track4_source",
            "track4_source_file",
            "track4_source_row_index",
        ],
        "rules": [
            "No standardization",
            "No inferred medium/support categories",
            "No derived area/log/aspect/ln_price",
            "No price parsing or filtering",
            "Source-specific original columns are namespaced as <source>__<original_column>",
            "Columns not present in a source are left blank after union",
        ],
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Track 4 primary-market raw collected dataset")
    print(f"output: {OUT_CSV.relative_to(REPO)}")
    print(f"rows: {summary['n_rows']:,}")
    print(f"columns: {summary['n_columns']:,}")
    print(f"source rows: {source_rows}")


if __name__ == "__main__":
    main()

