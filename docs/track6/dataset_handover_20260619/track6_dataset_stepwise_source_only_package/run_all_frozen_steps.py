#!/usr/bin/env python3
"""Run all Track6 steps with frozen reference split."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STEPS = [
    "step_01_prepare_source_files.py",
    "step_02_track4_cleaning.py",
    "step_03_artist_name_correction.py",
    "step_04_artist_meta_enrichment.py",
    "step_05_nant_material_enrichment.py",
    "step_06b_create_frozen_split.py",
    "step_07_export_feature_label.py",
    "step_08b_copy_verify_frozen_output.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all Track6 steps with frozen reference split.")
    parser.add_argument("--dry-run", action="store_true", help="실행 순서만 출력한다.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for script in STEPS:
        print(f"\n== run {script}")
        if args.dry_run:
            continue
        completed = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=False)
        if completed.returncode != 0:
            return int(completed.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
