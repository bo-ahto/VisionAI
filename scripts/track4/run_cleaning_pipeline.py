"""Run the Track 4 cleaning pipeline end to end.

Use this after adding or replacing primary-market source CSVs. The pipeline
keeps the raw union, audit outputs, cleaned dataset, feature candidates, splits,
and final column-value audit in sync.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]

STEPS = [
    ("raw_collected", "scripts/track4/build_primary_market_raw_collected.py"),
    ("price_audit", "scripts/track4/audit_price_consistency.py"),
    ("size_audit", "scripts/track4/audit_size_consistency.py"),
    ("artist_audit", "scripts/track4/audit_artist_consistency.py"),
    ("medium_support_audit", "scripts/track4/audit_medium_support_consistency.py"),
    ("duplicate_audit", "scripts/track4/audit_duplicate_consistency.py"),
    ("gallery_audit", "scripts/track4/audit_gallery_metadata.py"),
    ("source_bias_audit", "scripts/track4/audit_source_bias.py"),
    ("cleaned_v2", "scripts/track4/build_primary_market_cleaned_v2.py"),
    ("split", "scripts/track4/create_track4_splits.py"),
    ("column_value_audit", "scripts/track4/audit_column_value_consistency.py"),
]

REQUIRED_OUTPUTS = [
    "data/track4_primary_market_raw_collected.csv",
    "data/track4_price_consistency_audit.csv",
    "data/track4_size_consistency_audit.csv",
    "data/track4_artist_consistency_audit.csv",
    "data/track4_medium_support_consistency_audit.csv",
    "data/track4_duplicate_consistency_audit.csv",
    "data/track4_gallery_metadata_audit.csv",
    "data/track4_primary_market_cleaned_v2.csv",
    "data/track4_primary_market_feature_candidates_v1.csv",
    "data/track4_split/track4_train.csv",
    "data/track4_split/track4_val_warm.csv",
    "data/track4_split/track4_val_cold.csv",
    "data/track4_split/track4_test_warm.csv",
    "data/track4_split/track4_test_cold.csv",
    "data/track4_column_value_consistency_audit.csv",
    "docs/track4/audits/column_value_consistency_audit.md",
    "docs/track4/dataset/primary_market_cleaned_v2_report.md",
    "docs/track4/dataset/split_report.md",
]


def run_step(name: str, script: str) -> None:
    print(f"\n== {name}: {script}")
    subprocess.run([sys.executable, script], cwd=REPO, check=True)


def check_outputs() -> None:
    missing = [path for path in REQUIRED_OUTPUTS if not (REPO / path).exists()]
    if missing:
        lines = "\n".join(f"- {path}" for path in missing)
        raise SystemExit(f"Missing expected outputs:\n{lines}")
    print("\n== output check: ok")


def main() -> None:
    for name, script in STEPS:
        run_step(name, script)
    check_outputs()


if __name__ == "__main__":
    main()
