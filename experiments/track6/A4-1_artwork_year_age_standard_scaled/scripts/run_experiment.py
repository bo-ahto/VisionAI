#!/usr/bin/env python3
"""Run A4-1 with the dedicated numeric StandardScaler runner."""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
CONFIG = REPO / "experiments" / "track6" / "A4-1_artwork_year_age_standard_scaled" / "experiment_config.json"
sys.path.insert(0, str(REPO))

from scripts.track6.a4_1_standard_scaled_variable_experiment_runner import run_from_config  # noqa: E402


def main() -> None:
    results = run_from_config(CONFIG)
    print(results[["variable_block", "scope", "model_code", "model_name", "R2", "MdAPE", "p95_APE"]].to_string(index=False))


if __name__ == "__main__":
    main()
