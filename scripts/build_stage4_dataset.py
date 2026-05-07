"""Stage 4 curated 데이터셋 빌드 (v3 — Artsy 전체 활용).

사전등록 (`docs/stage4_확장검증계획_20260507.md` §6.0):
- Source: Artsy raw 30,046 only (Saatchi 제외)
- Cleansing rule: Stage 3 동일
- 3-way split: Train ≤2023 / Val 2024 / Test 2025
- Warm threshold: train ≥10 작품
- Test-eligible: warm + test n≥3

산출물:
- data/curated/stage4_full.parquet (전체 cleansed)
- data/curated/stage4_warm_test_eligible.parquet (primary 평가용)
- experiments/structural_v1/results/stage4_dataset_freeze.json (freeze artifact + hash)
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "artsy_kr_artworks.csv"
ARTISTS = ROOT / "data" / "artsy_kr_artists_full.csv"
OUT_DIR = ROOT / "data" / "curated"
RESULTS = ROOT / "experiments" / "structural_v1" / "results"

WARM_THRESHOLD = 10


def parse_year(date_str):
    if pd.isna(date_str):
        return None
    m = re.search(r"\b(19|20)\d{2}\b", str(date_str))
    return int(m.group()) if m else None


def file_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main():
    print("=" * 80)
    print("Stage 4 Curated Dataset Build (v3 — Artsy only)")
    print("=" * 80)

    # 1. Load + cleansing
    df = pd.read_csv(SRC)
    print(f"\n[1/5] Source: {SRC.relative_to(ROOT)} — {len(df):,} 작품 (raw)")

    df["year_made"] = df["date"].apply(parse_year)
    clean = df[
        df["price_krw"].notna() & (df["price_krw"] > 1) &
        df["width_cm"].notna() & df["height_cm"].notna() &
        (df["width_cm"] > 0) & (df["height_cm"] > 0) &
        df["artist_birth_year"].notna() &
        df["year_made"].notna() &
        (df["year_made"] >= 1900) & (df["year_made"] <= 2026)
    ].copy().reset_index(drop=True)
    print(f"      → cleansing 통과: {len(clean):,} 작품 / {clean['artist_slug'].nunique()} 작가")

    # 2. Feature 산출 (F4 + log_area)
    clean["area_cm2"] = clean["width_cm"] * clean["height_cm"]
    clean["log_area"] = np.log(clean["area_cm2"].clip(lower=1))
    clean["birth_year_centered"] = clean["artist_birth_year"] - clean["artist_birth_year"].mean()
    clean["log_artist_total_works"] = np.log1p(clean["artist_total_works"])
    clean["log_price"] = np.log(clean["price_krw"].clip(lower=1))

    # 3. Split tags
    # 사전등록 §6.0: Train ≤2023 / Val == 2024 / Test == 2025 (2026+ 제외)
    def assign_split(y):
        if y <= 2023:
            return "train"
        if y == 2024:
            return "val"
        if y == 2025:
            return "test"
        return "future_excluded"

    clean["split"] = clean["year_made"].apply(assign_split)
    n_excluded = (clean["split"] == "future_excluded").sum()
    if n_excluded:
        print(f"      → 2026+ 작품 {n_excluded:,} 건 사전등록 split 정의 외 — future_excluded")
    clean = clean[clean["split"] != "future_excluded"].copy().reset_index(drop=True)
    print(f"\n[2/5] 3-way split tag 부여:")
    for s, n in clean["split"].value_counts().items():
        print(f"      {s:>5}: {n:>5,} 작품 / {clean[clean['split']==s]['artist_slug'].nunique()} 작가")

    # 4. Warm artist 정의 (train ≥10)
    train_counts = clean[clean["split"] == "train"].groupby("artist_slug").size()
    warm_artists = set(train_counts[train_counts >= WARM_THRESHOLD].index)
    clean["is_warm_artist"] = clean["artist_slug"].isin(warm_artists)
    print(f"\n[3/5] Warm artist (train ≥{WARM_THRESHOLD}): {len(warm_artists):,} 명")

    # Test-eligible (warm + test n≥3)
    test_warm = clean[(clean["split"] == "test") & clean["is_warm_artist"]]
    test_counts = test_warm.groupby("artist_slug").size()
    test_eligible_artists = set(test_counts[test_counts >= 3].index)
    clean["is_test_eligible"] = clean["artist_slug"].isin(test_eligible_artists)
    print(f"      Test-eligible warm artists (test n≥3): {len(test_eligible_artists):,} 명")

    # Depth bin
    def depth_bin(slug):
        n = train_counts.get(slug, 0)
        if n < 10:
            return "cold"
        if n <= 14:
            return "10-14"
        if n <= 24:
            return "15-24"
        return "25+"

    clean["depth_bin"] = clean["artist_slug"].apply(depth_bin)

    # 5. 산출물 저장
    full_path = OUT_DIR / "stage4_full.parquet"
    eligible_path = OUT_DIR / "stage4_warm_test_eligible.parquet"

    clean.to_parquet(full_path, index=False)
    eligible_df = clean[clean["is_test_eligible"]].copy()
    eligible_df.to_parquet(eligible_path, index=False)
    print(f"\n[4/5] 산출물:")
    print(f"      {full_path.relative_to(ROOT)}: {len(clean):,} 작품")
    print(f"      {eligible_path.relative_to(ROOT)}: {len(eligible_df):,} 작품 (test-eligible warm 작가의 전체 split)")

    # 6. Freeze artifact (사전등록 §6.0)
    freeze = {
        "version": "stage4_v3_20260507",
        "model_hash": "track2_v1_20260507",
        "feature_pipeline_version": "f4_spline_v1_20260506",
        "source": {
            "raw_artworks_path": str(SRC.relative_to(ROOT)),
            "raw_artworks_sha256_16": file_sha256(SRC),
            "raw_artworks_n_rows": int(len(df)),
        },
        "cleansing_rules": {
            "price_krw_gt_1": True,
            "width_cm_gt_0": True,
            "height_cm_gt_0": True,
            "artist_birth_year_non_null": True,
            "year_made_range_1900_2026": True,
        },
        "cleansing_pass": {
            "n_artworks": int(len(clean)),
            "n_artists": int(clean["artist_slug"].nunique()),
        },
        "split": {
            "train": {"year_max": 2023, "n": int((clean["split"] == "train").sum())},
            "val": {"year_eq": 2024, "n": int((clean["split"] == "val").sum())},
            "test": {"year_eq": 2025, "n": int((clean["split"] == "test").sum())},
        },
        "warm_threshold": WARM_THRESHOLD,
        "warm_artists_n": int(len(warm_artists)),
        "test_eligible_artists_n": int(len(test_eligible_artists)),
        "test_eligible_n_threshold": 3,
        "depth_bin_counts": {
            bin_label: int((clean["depth_bin"] == bin_label).sum())
            for bin_label in ["cold", "10-14", "15-24", "25+"]
        },
        "test_eligible_depth_distribution": {
            bin_label: int(((clean["depth_bin"] == bin_label) & clean["is_test_eligible"]).sum())
            for bin_label in ["10-14", "15-24", "25+"]
        },
        "outputs": {
            "stage4_full_parquet": {
                "path": str(full_path.relative_to(ROOT)),
                "sha256_16": file_sha256(full_path),
                "n_rows": int(len(clean)),
            },
            "stage4_warm_test_eligible_parquet": {
                "path": str(eligible_path.relative_to(ROOT)),
                "sha256_16": file_sha256(eligible_path),
                "n_rows": int(len(eligible_df)),
            },
        },
    }

    freeze_path = RESULTS / "stage4_dataset_freeze.json"
    with freeze_path.open("w", encoding="utf-8") as f:
        json.dump(freeze, f, indent=2, ensure_ascii=False)
    print(f"\n[5/5] Freeze artifact: {freeze_path.relative_to(ROOT)}")
    print(f"      Train data hash (stage4_full.parquet SHA-16): {freeze['outputs']['stage4_full_parquet']['sha256_16']}")

    print("\n" + "=" * 80)
    print("Build PASS")
    print(f"  Funnel 일치 확인 (`stage4_funnel.json` 대비, 사전등록 split 정의 적용 후):")
    print(f"    cleansing pass total (2026+ 제외 후): 8,891 - 396 = 8,495 → 실제 {len(clean):,} {'✓' if len(clean) == 8495 else '✗'}")
    print(f"    warm artists (train ≥10): 120 → 실제 {len(warm_artists)} {'✓' if len(warm_artists) == 120 else '✗'}")
    print(f"    test-eligible warm: 40 → 실제 {len(test_eligible_artists)} {'✓' if len(test_eligible_artists) == 40 else '✗'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
