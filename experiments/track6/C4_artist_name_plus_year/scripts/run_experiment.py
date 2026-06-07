#!/usr/bin/env python3
"""Run Track6 C4 artist_name_ko plus artwork year experiment."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from scripts.track6.fixed_variable_experiment_runner import run_from_config  # noqa: E402


if __name__ == "__main__":
    config = REPO / "experiments" / "track6" / "C4_artist_name_plus_year" / "experiment_config.json"
    results = run_from_config(config)
    print(results[["variable_block", "scope", "model_code", "model_name", "R2", "RMSE_log", "MdAPE", "p95_APE"]].to_string(index=False))
