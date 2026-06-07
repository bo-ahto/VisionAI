#!/usr/bin/env python3
"""Create slice-level diagnostics for E5-1 controlled nationality experiment."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments" / "track6" / "E5-1_controlled_nationality_effect"
OUT_DIR = EXP_DIR / "outputs"


def load_frame(split_name: str) -> pd.DataFrame:
    features = pd.read_csv(EXP_DIR / "data" / f"{split_name}_features.csv", low_memory=False)
    labels = pd.read_csv(EXP_DIR / "data" / f"{split_name}_labels.csv", low_memory=False)
    return features.merge(labels, on="_track6_row_id", how="inner")


def ho_bucket(value: object) -> str:
    ho = pd.to_numeric(value, errors="coerce")
    if pd.isna(ho):
        return "missing_ho"
    if ho <= 5:
        return "ho_000_005"
    if ho <= 10:
        return "ho_006_010"
    if ho <= 30:
        return "ho_011_030"
    if ho <= 50:
        return "ho_031_050"
    if ho <= 100:
        return "ho_051_100"
    return "ho_101_plus"


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__missing__").replace({"": "__missing__"})


def add_control_key(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["ho_control_bucket_manual"] = frame["estimated_ho"].map(ho_bucket)
    for col in ["nant_material_idx", "nant_tool", "nant_support", "artist_meta_nationality"]:
        frame[col] = normalize_text(frame[col])
    frame["control_key"] = (
        frame["ho_control_bucket_manual"].astype(str)
        + " | material="
        + frame["nant_material_idx"].astype(str)
        + " | tool="
        + frame["nant_tool"].astype(str)
        + " | support="
        + frame["nant_support"].astype(str)
    )
    return frame


def summarize_conditions(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    frame = add_control_key(frame)
    grouped = (
        frame.groupby("control_key", dropna=False)
        .agg(
            n=("price_krw", "size"),
            nationality_nunique=("artist_meta_nationality", "nunique"),
            median_price=("price_krw", "median"),
            p25_price=("price_krw", lambda x: float(np.quantile(x, 0.25))),
            p75_price=("price_krw", lambda x: float(np.quantile(x, 0.75))),
        )
        .reset_index()
    )
    grouped["scope"] = scope
    grouped["is_comparable_condition"] = (grouped["n"] >= 20) & (grouped["nationality_nunique"] >= 2)
    return grouped.sort_values(["is_comparable_condition", "n"], ascending=[False, False])


def summarize_nationality_within_conditions(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    frame = add_control_key(frame)
    comparable_keys = (
        frame.groupby("control_key")["artist_meta_nationality"]
        .nunique()
        .loc[lambda s: s >= 2]
        .index
    )
    frame = frame[frame["control_key"].isin(comparable_keys)].copy()
    grouped = (
        frame.groupby(["control_key", "artist_meta_nationality"], dropna=False)
        .agg(
            n=("price_krw", "size"),
            median_price=("price_krw", "median"),
            median_ln_price=("ln_price_krw", "median"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["n"] >= 5].copy()
    grouped["scope"] = scope
    return grouped.sort_values(["control_key", "n"], ascending=[True, False])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    warm = load_frame("test_warm")
    cold = load_frame("test_cold")
    condition_summary = pd.concat(
        [summarize_conditions(warm, "Warm"), summarize_conditions(cold, "Cold")],
        ignore_index=True,
    )
    nationality_summary = pd.concat(
        [
            summarize_nationality_within_conditions(warm, "Warm"),
            summarize_nationality_within_conditions(cold, "Cold"),
        ],
        ignore_index=True,
    )
    condition_summary.to_csv(OUT_DIR / "controlled_condition_summary.csv", index=False)
    nationality_summary.to_csv(OUT_DIR / "controlled_nationality_within_condition_summary.csv", index=False)

    summary = {
        "warm_comparable_condition_count": int(
            condition_summary.query("scope == 'Warm' and is_comparable_condition").shape[0]
        ),
        "cold_comparable_condition_count": int(
            condition_summary.query("scope == 'Cold' and is_comparable_condition").shape[0]
        ),
        "warm_nationality_condition_rows": int(nationality_summary.query("scope == 'Warm'").shape[0]),
        "cold_nationality_condition_rows": int(nationality_summary.query("scope == 'Cold'").shape[0]),
        "rule": "조건 묶음은 호수 구간 + 난트 재료 + 난트 도구 + 난트 지지체로 구성했다. 조건 묶음 내 국적이 2개 이상이고 표본이 20개 이상이면 비교 가능 후보로 표시했다.",
    }
    (OUT_DIR / "controlled_slice_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
