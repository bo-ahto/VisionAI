"""Stage 4 funnel 재집계 (코덱스 권고 #2).

Artsy raw 30,046 → cleansing → 3-way time-split (Train≤2023 / Val 2024 / Test 2025)
→ warm artist (train ≥10) / test 평가 가능 (test n≥3) / depth bin 분포 산출.

본 스크립트로 산출된 실제 분포가 Stage 4 plan §2.1 새 목표의 근거.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "artsy_kr_artworks.csv"
OUT = ROOT / "experiments" / "structural_v1" / "results" / "stage4_funnel.json"
WARM_THRESHOLD = 10


def parse_year(date_str):
    """Artsy 'date' 컬럼에서 4자리 연도 추출."""
    if pd.isna(date_str):
        return None
    m = re.search(r"\b(19|20)\d{2}\b", str(date_str))
    return int(m.group()) if m else None


def main():
    df = pd.read_csv(SRC)
    print(f"Artsy raw: {len(df):,} 작품")

    # 기본 cleansing (Stage 3 룰)
    df["year_made"] = df["date"].apply(parse_year)
    clean = df[
        df["price_krw"].notna() & (df["price_krw"] > 1) &
        df["width_cm"].notna() & df["height_cm"].notna() &
        (df["width_cm"] > 0) & (df["height_cm"] > 0) &
        df["artist_birth_year"].notna() &
        df["year_made"].notna() &
        (df["year_made"] >= 1900) & (df["year_made"] <= 2026)
    ].copy()
    print(f"  → cleansing 통과 (price+size+birth+year_made 1900-2026): {len(clean):,}")

    counts_all = clean.groupby("artist_slug").size()
    print(f"  Unique artists: {len(counts_all):,}")
    print()

    # 3-way split
    train = clean[clean["year_made"] <= 2023]
    val = clean[clean["year_made"] == 2024]
    test = clean[clean["year_made"] == 2025]

    print(f"[3-way split]")
    print(f"  Train (year ≤ 2023): {len(train):,} 작품, {train['artist_slug'].nunique()} 작가")
    print(f"  Val   (year = 2024): {len(val):,} 작품, {val['artist_slug'].nunique()} 작가")
    print(f"  Test  (year = 2025): {len(test):,} 작품, {test['artist_slug'].nunique()} 작가")
    print()

    # Train 기준 warm artist 정의 (train ≥10)
    train_counts = train.groupby("artist_slug").size()
    warm_artists = set(train_counts[train_counts >= WARM_THRESHOLD].index)
    print(f"[Warm artist (train ≥{WARM_THRESHOLD})]: {len(warm_artists):,} 명")
    print(f"  Train 작품 (warm 만): {train_counts[train_counts >= WARM_THRESHOLD].sum():,}")
    print()

    # Test 평가 가능 = warm artist 중 test 에서 n ≥ 3 작품 보유
    test_counts = test[test["artist_slug"].isin(warm_artists)].groupby("artist_slug").size()
    test_eligible = test_counts[test_counts >= 3]
    print(f"[Test 평가 가능 (warm artist 중 test n≥3)]")
    print(f"  Test-eligible warm artists: {len(test_eligible):,} 명")
    print(f"  Test 작품 (test-eligible 만): {test_eligible.sum():,}")
    print(f"  Test 작품 (warm artist 전체, n≥1): {test[test['artist_slug'].isin(warm_artists)].shape[0]:,}")
    print()

    # Depth bin 분포 (train counts 기준, warm artists 만)
    print(f"[Warm artist depth bin (train 작품 수 기준)]")
    bins_def = [(10, 14), (15, 24), (25, 999)]
    bin_summary = []
    for lo, hi in bins_def:
        bin_artists = [a for a in warm_artists if lo <= train_counts[a] <= hi]
        bin_test = test[test["artist_slug"].isin(bin_artists)]
        bin_test_eligible = [a for a in bin_artists if a in test_eligible.index]
        bin_summary.append({
            "depth_bin": f"{lo}-{hi if hi < 999 else '+'}",
            "n_artists": len(bin_artists),
            "n_test_eligible_artists": len(bin_test_eligible),
            "n_test_rows_total": len(bin_test),
            "n_test_rows_eligible": int(bin_test[bin_test["artist_slug"].isin(bin_test_eligible)].shape[0]),
        })
        print(f"  {lo:>2}-{hi if hi<999 else '+':>3}: {len(bin_artists):>3} 작가 (test-eligible {len(bin_test_eligible):>3}), "
              f"test rows {len(bin_test):>4} (eligible {bin_summary[-1]['n_test_rows_eligible']:>3})")
    print()

    # Val 도 동일 분석
    val_counts = val[val["artist_slug"].isin(warm_artists)].groupby("artist_slug").size()
    val_eligible = val_counts[val_counts >= 3]
    print(f"[Val (year=2024) — warm artist 중 n≥3]")
    print(f"  Val-eligible warm artists: {len(val_eligible):,} 명")
    print(f"  Val 작품 (val-eligible 만): {val_eligible.sum():,}")
    print()

    # Cluster bootstrap 가용 평가
    n_clusters_estimated = len(test_eligible)
    print(f"[Cluster bootstrap 가용성]")
    print(f"  Test-eligible warm artists = cluster bootstrap 표본 단위 = {n_clusters_estimated} clusters")
    print(f"  (Stage 3 P3 기준 13 clusters 였음 → {n_clusters_estimated/13:.1f}× 확장)")
    print()

    # 비교
    print(f"[Stage 3 vs Stage 4 (정정 후) 비교]")
    print(f"  {'항목':<40} {'Stage 3':>12} {'Stage 4 (가용)':>16} {'배수':>8}")
    print(f"  {'전체 작가 (train)':<40} {'~100':>12} {len(warm_artists):>16,} {len(warm_artists)/100:>7.1f}×")
    print(f"  {'Warm test rows':<40} {'44':>12} {bin_summary[0]['n_test_rows_total']+bin_summary[1]['n_test_rows_total']+bin_summary[2]['n_test_rows_total']:>16,} —")
    print(f"  {'Test-eligible warm artists':<40} {'13':>12} {n_clusters_estimated:>16,} {n_clusters_estimated/13:>7.1f}×")

    summary = {
        "source": "Artsy raw 30,046 → cleansing 통과",
        "cleansing_pass_total": int(len(clean)),
        "unique_artists_total": int(len(counts_all)),
        "split": {
            "train_year_le_2023": {"n_rows": int(len(train)), "n_artists": int(train["artist_slug"].nunique())},
            "val_year_eq_2024": {"n_rows": int(len(val)), "n_artists": int(val["artist_slug"].nunique())},
            "test_year_eq_2025": {"n_rows": int(len(test)), "n_artists": int(test["artist_slug"].nunique())},
        },
        "warm_artist_train_ge_10": {
            "n_artists": int(len(warm_artists)),
            "n_train_rows": int(train_counts[train_counts >= WARM_THRESHOLD].sum()),
        },
        "test_eligible_warm_n_ge_3": {
            "n_artists": int(len(test_eligible)),
            "n_test_rows": int(test_eligible.sum()),
            "n_test_rows_warm_total": int(test[test["artist_slug"].isin(warm_artists)].shape[0]),
        },
        "val_eligible_warm_n_ge_3": {
            "n_artists": int(len(val_eligible)),
            "n_val_rows": int(val_eligible.sum()),
        },
        "depth_bins": bin_summary,
        "cluster_bootstrap_available_clusters": int(n_clusters_estimated),
        "stage3_baseline": {"n_clusters": 13, "n_test_rows": 44},
        "expansion_multiplier": float(n_clusters_estimated / 13),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
