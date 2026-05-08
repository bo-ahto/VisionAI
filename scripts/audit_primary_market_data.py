"""1차 시장 dataset audit — 결측 / placeholder / anomaly 컬럼별 식별.

Output: model_test_results/primary_market_audit_20260508.json
        (보고서 작성 의 정량 입력)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import load_data  # type: ignore  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CURRENT_YEAR = 2026
OUT = REPO / "experiments" / "structural_v1" / "results" / "primary_market_audit_20260508.json"


def audit(df: pd.DataFrame) -> dict:
    n = len(df)
    audit_data: dict = {"n_total": n, "columns": {}}

    # 1. 결측 / placeholder 비율 (모든 컬럼)
    for c in df.columns:
        s = df[c]
        col_audit = {"dtype": str(s.dtype), "null_n": int(s.isna().sum())}
        if pd.api.types.is_numeric_dtype(s):
            col_audit["zero_n"] = int((s == 0).sum())
        else:
            placeholder_mask = s.astype(str).isin(
                ["", "nan", "None", "unknown", "Unknown", "null"]
            )
            col_audit["placeholder_n"] = int(placeholder_mask.sum())
        col_audit["unique_n"] = int(s.nunique(dropna=True))
        audit_data["columns"][c] = col_audit

    # 2. Anomaly 영역
    anomalies: dict = {}

    # price_krw
    p = df["price_krw"]
    anomalies["price_krw"] = {
        "null_n": int(p.isna().sum()),
        "zero_or_negative_n": int((p <= 0).sum()),
        "below_100k_krw_n": int((p < 100_000).sum()),
        "above_1B_krw_n": int((p > 1_000_000_000).sum()),
        "above_5B_krw_n": int((p > 5_000_000_000).sum()),
        "min": float(p.min()),
        "max": float(p.max()),
        "median": float(p.median()),
    }

    # area_cm2 / aspect_ratio / ho
    a = df["area_cm2"]
    ar = df["aspect_ratio"]
    ho = df["ho"]
    anomalies["dimensions"] = {
        "area_null_or_zero_n": int(((a.isna()) | (a <= 0)).sum()),
        "area_below_100cm2_n": int((a < 100).sum()),
        "area_above_50000cm2_n": int((a > 50_000).sum()),
        "area_above_100000cm2_n": int((a > 100_000).sum()),
        "area_max": float(a.max()),
        "aspect_invalid_n": int(((ar.isna()) | (ar <= 0)).sum()),
        "aspect_above_10_n": int((ar > 10).sum()),
        "ho_zero_n": int((ho == 0).sum()),
        "ho_above_200_n": int((ho > 200).sum()),
        "ho_max": int(ho.max()),
    }

    # year / age 정합성
    y = df["year_made"]
    b = df["artist_birth_year"]
    wa = df["work_age"]
    both = y.notna() & b.notna()
    diff = y - b
    anomalies["temporal"] = {
        "year_made_future_n": int((y > CURRENT_YEAR).sum()),
        "year_made_below_1900_n": int((y < 1900).sum()),
        "year_made_below_1950_n": int((y < 1950).sum()),
        "birth_year_future_n": int((b > CURRENT_YEAR).sum()),
        "birth_year_below_1900_n": int((b < 1900).sum()),
        "year_before_birth_n": int((both & (diff < 0)).sum()),
        "made_under_age_10_n": int((both & (diff < 10) & (diff >= 0)).sum()),
        "made_under_age_18_n": int((both & (diff < 18) & (diff >= 0)).sum()),
        "work_age_negative_n": int((wa < 0).sum()),
        "work_age_above_100_n": int((wa > 100).sum()),
    }

    # artist profile
    anomalies["artist_profile"] = {
        "total_works_zero_n": int((df["artist_total_works"] == 0).sum()),
        "for_sale_ratio_outside_01_n": int(
            ((df["for_sale_ratio"] > 1) | (df["for_sale_ratio"] < 0)).sum()
        ),
        "request_ratio_outside_01_n": int(
            ((df["request_ratio"] > 1) | (df["request_ratio"] < 0)).sum()
        ),
        "ln_followers_negative_n": int((df["ln_followers"] < 0).sum()),
    }

    # categorical placeholder
    cat_placeholder: dict = {}
    for col in ["support_type", "medium_category", "attribution_class", "gallery_type"]:
        s = df[col].astype(str)
        ph = s.isin(["unknown", "other", "Unknown", "Other", "", "nan", "None"])
        cat_placeholder[col] = {
            "placeholder_n": int(ph.sum()),
            "placeholder_pct": float(ph.mean() * 100),
        }
    anomalies["categorical_placeholder"] = cat_placeholder

    # gallery
    anomalies["gallery"] = {
        "gallery_name_empty_n": int(
            df["gallery_name"].astype(str).isin(["", "nan", "None"]).sum()
            + df["gallery_name"].isna().sum()
        ),
        "gallery_tier_zero_n": int((df["gallery_tier"] == 0).sum()),
        "gallery_tier_above_5_n": int((df["gallery_tier"] > 5).sum()),
        "gallery_city_count_zero_n": int((df["gallery_city_count"] == 0).sum()),
    }

    # unit price (KRW per cm²) — primary market sanity
    df_va = df[(df["area_cm2"] > 0) & (df["price_krw"] > 0)]
    unit = df_va["price_krw"] / df_va["area_cm2"]
    anomalies["unit_price"] = {
        "median_krw_per_cm2": float(unit.median()),
        "below_100_krw_per_cm2_n": int((unit < 100).sum()),
        "above_100k_krw_per_cm2_n": int((unit > 100_000).sum()),
        "above_1M_krw_per_cm2_n": int((unit > 1_000_000).sum()),
    }

    audit_data["anomalies"] = anomalies

    # 3. Source-stratified 결측
    by_source = {}
    for src in ["artsy", "saatchi"]:
        sub = df[df["source"] == src]
        by_source[src] = {
            "n": len(sub),
            "year_made_notna_n": int(sub["year_made"].notna().sum()),
            "year_made_notna_pct": float(sub["year_made"].notna().mean() * 100),
            "birth_year_notna_n": int(sub["artist_birth_year"].notna().sum()),
            "birth_year_notna_pct": float(sub["artist_birth_year"].notna().mean() * 100),
            "career_age_notna_n": int(sub["career_age"].notna().sum()),
            "career_age_notna_pct": float(sub["career_age"].notna().mean() * 100),
            "work_age_notna_n": int(sub["work_age"].notna().sum()),
            "work_age_notna_pct": float(sub["work_age"].notna().mean() * 100),
            "has_seoul_n": int((sub["has_seoul"] == 1).sum()),
            "is_krw_n": int((sub["is_krw"] == 1).sum()),
        }
    audit_data["by_source"] = by_source

    # 4. Cleansed dataset 후보 row counts
    candidates = {}

    def count(mask: np.ndarray, name: str) -> None:
        sub = df[mask]
        candidates[name] = {
            "n": len(sub),
            "n_artists": int(sub["artist_slug"].nunique()),
            "pct_of_total": float(len(sub) / n * 100),
        }

    count(np.ones(n, dtype=bool), "T0_operational_v3")
    count((df["source"] == "artsy").to_numpy(), "T1_artsy_only")
    count(
        ((df["source"] == "artsy") & df["year_made"].notna()).to_numpy(),
        "T2_artsy_year_notna",
    )
    count(
        (
            (df["source"] == "artsy")
            & df["year_made"].notna()
            & df["artist_birth_year"].notna()
        ).to_numpy(),
        "T3_artsy_year_birth_notna",
    )
    count(
        (
            (df["source"] == "artsy")
            & df["year_made"].notna()
            & df["artist_birth_year"].notna()
            & df["career_age"].notna()
            & df["work_age"].notna()
        ).to_numpy(),
        "T4_artsy_strict_4field",
    )
    count((df["is_krw"] == 1).to_numpy(), "T5_krw_only")

    # T6: T4 + anomaly free (가장 엄격)
    t4_mask = (
        (df["source"] == "artsy")
        & df["year_made"].notna()
        & df["artist_birth_year"].notna()
        & df["career_age"].notna()
        & df["work_age"].notna()
    )
    anomaly_free = (
        (df["price_krw"] > 100_000)
        & (df["price_krw"] < 1_000_000_000)
        & (df["area_cm2"] > 100)
        & (df["area_cm2"] < 50_000)
        & (df["aspect_ratio"] > 0)
        & (df["aspect_ratio"] <= 10)
        & (df["ho"] > 0)
        & (df["ho"] <= 200)
        & (df["year_made"] >= 1950)
        & (df["year_made"] <= CURRENT_YEAR)
        & (df["year_made"] - df["artist_birth_year"] >= 10)
        & (df["work_age"] >= 0)
        & (df["work_age"] <= 100)
        & (df["artist_total_works"] > 0)
        & (df["gallery_city_count"] > 0)
    )
    count((t4_mask & anomaly_free).to_numpy(), "T6_T4_plus_anomaly_free")
    audit_data["cleansed_candidates"] = candidates

    return audit_data


def main() -> None:
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].reset_index(drop=True)
    logger.info("After is_excluded_for_training==0: n=%d", len(df))

    result = audit(df)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", OUT)
    logger.info("=== Cleansed dataset 후보 ===")
    for k, v in result["cleansed_candidates"].items():
        logger.info("  %s: n=%d artists=%d (%.2f%%)", k, v["n"], v["n_artists"], v["pct_of_total"])


if __name__ == "__main__":
    main()
