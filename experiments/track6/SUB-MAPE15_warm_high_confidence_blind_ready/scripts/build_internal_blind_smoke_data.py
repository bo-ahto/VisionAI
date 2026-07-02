#!/usr/bin/env python3
"""Build an internal unlabeled candidate pool for blind protocol smoke tests."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[4]
SOURCE_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_high_confidence_blind_ready" / "data"

FEATURE_COLUMNS = [
    "split",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "medium_support_bucket",
    "svc_group_level",
    "svc_coverage_tier",
    "service_confidence_tier",
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "log_area",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    frame = raw[raw["candidate"].eq("hcoef_stable") & raw["split"].eq("test")].copy()
    frame[FEATURE_COLUMNS].to_csv(OUT_DIR / "internal_blind_smoke_candidate_pool_features.csv", index=False)
    frame[["_track6_row_id", "actual_log", "actual_price"]].to_csv(
        OUT_DIR / "internal_blind_smoke_candidate_pool_labels.csv", index=False
    )


if __name__ == "__main__":
    main()
