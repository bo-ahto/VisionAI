#!/usr/bin/env python3
"""Analyze Track 5 Cold risk slices from final candidate predictions."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track5_split"
RESULT_DIR = REPO / "data" / "track5" / "results"
PRED_PATH = REPO / "data" / "track5" / "predictions" / "t5_e010_final_candidate_test_predictions.csv"
RESULT_PATH = RESULT_DIR / "t5_e012_cold_risk_slice_analysis_metrics.json"


def summarize(df: pd.DataFrame) -> dict[str, Any]:
    ape = df["ape"].to_numpy(dtype=float)
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def add_risk_flags(df: pd.DataFrame, train: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    large_cut = float(train["log_area"].quantile(0.75))
    out["is_large_work"] = (out["log_area"] >= large_cut).astype(int)
    out["is_very_large_work"] = (pd.to_numeric(out["area_cm2"], errors="coerce") >= 10000).fillna(False).astype(int)
    out["is_3d"] = (pd.to_numeric(out["has_depth"], errors="coerce").fillna(0) > 0).astype(int)
    out["medium_unknown"] = out["medium_category"].fillna("unknown").astype(str).str.lower().isin(["unknown", "other"]).astype(int)
    out["support_unknown"] = out["support_category"].fillna("unknown").astype(str).str.lower().isin(["unknown", "other"]).astype(int)
    out["risk_score"] = (
        out["is_large_work"]
        + out["is_very_large_work"]
        + out["is_3d"]
        + out["medium_unknown"]
        + out["support_unknown"]
    )
    out["risk_group"] = np.where(out["risk_score"] >= 2, "high_risk", np.where(out["risk_score"] == 1, "mid_risk", "low_risk"))
    return out


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(SPLIT_DIR / "track5_train.csv", low_memory=False)
    cold = pd.read_csv(SPLIT_DIR / "track5_test_cold.csv", low_memory=False)
    pred = pd.read_csv(PRED_PATH)
    pred = pred[(pred["task"] == "cold") & (pred["candidate"] == "cold_full_size_quantile")].copy()
    cold = cold.reset_index(drop=True)
    pred = pred.reset_index(drop=True)
    merged = pd.concat(
        [
            cold[
                [
                    "artist_key",
                    "medium_category",
                    "support_category",
                    "log_area",
                    "area_cm2",
                    "has_depth",
                ]
            ],
            pred[["actual_price_krw", "pred_price_krw", "ape"]],
        ],
        axis=1,
    )
    merged = add_risk_flags(merged, train)
    output: dict[str, Any] = {
        "experiment_id": "T5-E012",
        "hypothesis_id": "T5-H15",
        "date": date.today().isoformat(),
        "overall": summarize(merged),
        "risk_groups": {name: summarize(group) for name, group in merged.groupby("risk_group")},
        "flags": {},
    }
    for flag in ["is_large_work", "is_very_large_work", "is_3d", "medium_unknown", "support_unknown"]:
        output["flags"][flag] = {
            "flag_0": summarize(merged[merged[flag] == 0]),
            "flag_1": summarize(merged[merged[flag] == 1]),
        }
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
