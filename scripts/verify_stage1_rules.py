"""Stage 1 규칙 검증 (코덱스 P1 + P2 항목).

검증 항목:
P1 (하나라도 위반 시 실패):
- 하드룰 재검증 (필터 위반 0건)
- 중복 검증 (canonical key 기준 0%)
- 작가 단위 분산 (price variance > 0, collapse 작가 0명)

P2 (권고):
- strata 분포 (cell n >= 5)
- 이상치 (작가 평균 대비 100x)
- 대표성 (모집단 vs sampled)

Stage 2 진입 조건:
- P1 전부 통과 + 규칙문서/제외로그 완료
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
STAGE1_PATH = DATA / "curated" / "stage1_200x20.parquet"
SOURCE_PATH = DATA / "primary_market_dataset.parquet"
REPORT_PATH = DATA / "curated" / "stage1_verification_report.json"

# 중복 판정 canonical key
DUP_KEY = ["artist_slug", "title", "year_made", "area_cm2", "medium_category"]

# 임계치
OUTLIER_PRICE_RATIO = 100.0  # 작가 평균 대비 배수
STRATA_MIN_CELL = 5  # 권고: cell 당 최소 n


def check_hard_rules(df: pd.DataFrame) -> dict:
    """P1: 하드룰 재검증."""
    violations: dict = {}

    # is_excluded_for_training == 0
    violations["excluded"] = int((df["is_excluded_for_training"] != 0).sum())

    # price_krw > 1
    violations["price_invalid"] = int((df["price_krw"] <= 1).sum())

    # 필수 변수 결측
    required = [
        "artist_slug",
        "area_cm2",
        "medium_category",
        "year_made",
        "gallery_tier",
        "price_krw",
    ]
    for col in required:
        violations[f"{col}_missing"] = int(df[col].isna().sum())

    # area_cm2 > 0
    violations["area_invalid"] = int((df["area_cm2"] <= 0).sum())

    # year_made 1900 ~ 2026
    violations["year_made_invalid"] = int(
        ((df["year_made"] < 1900) | (df["year_made"] > 2026)).sum()
    )

    # 작가당 작품 수 >= 10
    counts = df["artist_slug"].value_counts()
    violations["artist_works_below_10"] = int((counts < 10).sum())

    total = sum(violations.values())
    return {
        "violations": violations,
        "total": total,
        "pass": total == 0,
    }


def check_duplicates(df: pd.DataFrame) -> dict:
    """P1: 중복 검증 (canonical key 기준)."""
    dup_mask = df.duplicated(subset=DUP_KEY, keep=False)
    n_dup = int(dup_mask.sum())
    n_dup_keys = int(df[dup_mask].groupby(DUP_KEY).ngroups) if n_dup > 0 else 0

    return {
        "n_duplicate_records": n_dup,
        "n_duplicate_keys": n_dup_keys,
        "duplicate_rate_pct": round(n_dup / len(df) * 100, 2),
        "pass": n_dup == 0,
    }


def check_artist_variance(df: pd.DataFrame) -> dict:
    """P1: 작가 단위 가격 분산 검증."""
    artist_var = df.groupby("artist_slug")["price_krw"].var()
    collapse_artists = artist_var[(artist_var.isna()) | (artist_var == 0)]
    return {
        "n_artists_total": int(df["artist_slug"].nunique()),
        "n_collapse_artists": int(len(collapse_artists)),
        "collapse_artist_slugs": collapse_artists.index.tolist(),
        "pass": len(collapse_artists) == 0,
    }


def check_strata(df: pd.DataFrame) -> dict:
    """P2: strata 분포 점검."""
    medium_counts = df["medium_category"].value_counts().to_dict()
    tier_counts = (
        df["gallery_tier"].astype(str).value_counts().to_dict()
    )
    cross = (
        df.groupby(["medium_category", "gallery_tier"])
        .size()
        .reset_index(name="n")
    )

    small_cells = cross[cross["n"] < STRATA_MIN_CELL]

    return {
        "medium_dist": medium_counts,
        "tier_dist": tier_counts,
        "cross_cells": cross.to_dict(orient="records"),
        "n_small_cells": int(len(small_cells)),
        "small_cells": small_cells.to_dict(orient="records"),
        "pass": True,  # P2 는 fail 처리 X (권고만)
    }


def check_outliers(df: pd.DataFrame) -> dict:
    """P2: 가격 이상치 (작가 평균 100x 초과)."""
    artist_mean = df.groupby("artist_slug")["price_krw"].transform("mean")
    ratio = df["price_krw"] / artist_mean
    outliers = df[ratio > OUTLIER_PRICE_RATIO]

    return {
        "n_outliers": int(len(outliers)),
        "outlier_records": (
            outliers[["artist_slug", "title", "price_krw"]]
            .head(20)
            .to_dict(orient="records")
        ),
        "pass": True,  # P2 는 fail 처리 X
    }


def check_representativeness(df: pd.DataFrame) -> dict:
    """P2: 모집단 대비 대표성."""
    # 모집단 (필터 적용 후) 분포
    pop = pd.read_parquet(SOURCE_PATH)
    pop = pop[(pop["is_excluded_for_training"] == 0) & (pop["price_krw"] > 1)]
    pop = pop[
        pop["area_cm2"].notna()
        & pop["medium_category"].notna()
        & pop["year_made"].notna()
        & pop["gallery_tier"].notna()
    ]
    pop = pop[
        (pop["year_made"] >= 1900) & (pop["year_made"] <= 2026)
    ]

    pop_medium = pop["medium_category"].value_counts(normalize=True) * 100
    sample_medium = (
        df["medium_category"].value_counts(normalize=True) * 100
    )

    diffs = (sample_medium - pop_medium).abs().fillna(sample_medium)
    return {
        "population_medium_pct": pop_medium.round(2).to_dict(),
        "sample_medium_pct": sample_medium.round(2).to_dict(),
        "max_abs_pct_diff": float(diffs.max().round(2)),
        "pass": True,  # P2
    }


def check_source(df: pd.DataFrame) -> dict:
    """P2: source 다양성."""
    src = df["source"].value_counts().to_dict() if "source" in df.columns else {
        "artsy": len(df)
    }
    return {
        "source_dist": src,
        "single_source": len(src) == 1,
    }


def main() -> None:
    logger.info("=" * 60)
    logger.info("Stage 1 규칙 검증 (코덱스 P1 + P2)")
    logger.info("=" * 60)

    df = pd.read_parquet(STAGE1_PATH)
    logger.info(f"Loaded: {len(df)} records / {df['artist_slug'].nunique()} artists")

    # P1
    logger.info("")
    logger.info("--- P1 검증 ---")
    hard = check_hard_rules(df)
    logger.info(f"하드룰 재검증: {'PASS' if hard['pass'] else 'FAIL'} (위반 {hard['total']}건)")
    if not hard["pass"]:
        for k, v in hard["violations"].items():
            if v > 0:
                logger.info(f"  - {k}: {v}건")

    dup = check_duplicates(df)
    logger.info(f"중복 검증: {'PASS' if dup['pass'] else 'FAIL'} ({dup['duplicate_rate_pct']}%)")
    if not dup["pass"]:
        logger.info(f"  - 중복 records: {dup['n_duplicate_records']} / 키 그룹: {dup['n_duplicate_keys']}")

    var = check_artist_variance(df)
    logger.info(f"작가 분산 검증: {'PASS' if var['pass'] else 'FAIL'} (collapse 작가 {var['n_collapse_artists']}명)")
    if not var["pass"]:
        for slug in var["collapse_artist_slugs"]:
            logger.info(f"  - {slug}")

    p1_pass = hard["pass"] and dup["pass"] and var["pass"]

    # P2
    logger.info("")
    logger.info("--- P2 검증 (권고) ---")
    strata = check_strata(df)
    logger.info(f"strata: medium {len(strata['medium_dist'])} 종 / tier {len(strata['tier_dist'])} 종 / 작은 cell (<{STRATA_MIN_CELL}) {strata['n_small_cells']}개")

    outlier = check_outliers(df)
    logger.info(f"이상치 (작가 평균 {OUTLIER_PRICE_RATIO}x 초과): {outlier['n_outliers']}건")

    rep = check_representativeness(df)
    logger.info(f"매체 분포 모집단 대비 max diff: {rep['max_abs_pct_diff']}%p")

    source = check_source(df)
    logger.info(f"source 분포: {source['source_dist']}")

    # Final
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"P1 종합: {'PASS' if p1_pass else 'FAIL'}")
    logger.info(f"Stage 2 진입 가능: {'YES' if p1_pass else 'NO (P1 fix 필요)'}")
    logger.info("=" * 60)

    # Save report
    report = {
        "stage": "stage1",
        "n_records": len(df),
        "n_artists": int(df["artist_slug"].nunique()),
        "p1": {
            "hard_rules": hard,
            "duplicates": dup,
            "artist_variance": var,
            "all_pass": p1_pass,
        },
        "p2": {
            "strata": strata,
            "outliers": outlier,
            "representativeness": rep,
            "source": source,
        },
        "stage2_eligible": p1_pass,
    }

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Report saved: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
