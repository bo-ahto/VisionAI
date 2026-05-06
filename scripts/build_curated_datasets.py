"""Stage 1-3 curated dataset builder.

데이터 클렌징 단계 계획 (docs/데이터클렌징_단계계획_20260506.md) 에 따라
Stage 1 (200/20), Stage 2 (500/50), Stage 3 (1000/100) 데이터셋을 구축한다.

Filter:
- is_excluded_for_training == 0
- price_krw > 1
- 필수 변수 결측 없음 (artist_slug / area_cm2 / medium_category / year_made / gallery_tier)
- 작가당 작품 수 >= 10

Stratification:
- 작가 단위 stratified sampling
- 1순위: medium_category (작가 대표 매체)
- 2순위: gallery_tier (2 / 3 / 4)
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
OUTPUT_DIR = DATA / "curated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FIELDS = [
    "artist_slug",
    "area_cm2",
    "medium_category",
    "year_made",
    "gallery_tier",
    "price_krw",
]

MIN_WORKS_PER_ARTIST = 10
SLOPE_CHECK_MIN_WORKS = 15

STAGES = {
    "stage1": {"records": 200, "artists": 20, "works_per_artist": 10},
    "stage2": {"records": 500, "artists": 50, "works_per_artist": 10},
    # Stage 3: 작가당 최대 15작품 → random slope 점검 sub-sample 확보
    "stage3": {"records": 1000, "artists": 100, "works_per_artist": 15},
}

SEED = 42
rng = np.random.default_rng(SEED)

CURRENT_YEAR = 2026
YEAR_MADE_MIN = 1900


def load_eligible() -> pd.DataFrame:
    """필터 적용 후 eligible records 반환."""
    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    artsy["source"] = "artsy"

    df = artsy.copy()

    # 1. is_excluded_for_training == 0
    df = df[df["is_excluded_for_training"] == 0]
    logger.info(f"After exclusion filter: {len(df)} records")

    # 2. price_krw > 1
    df = df[df["price_krw"] > 1]
    logger.info(f"After price filter: {len(df)} records")

    # 3. 필수 변수 결측 없음
    for col in REQUIRED_FIELDS:
        before = len(df)
        df = df[df[col].notna()]
        after = len(df)
        if before != after:
            logger.info(f"  {col} 결측 제거: -{before - after}")

    logger.info(f"After required-field filter: {len(df)} records")

    # 4. area_cm2 > 0
    df = df[df["area_cm2"] > 0]
    logger.info(f"After area>0 filter: {len(df)} records")

    # 5. year_made 합리적 범위 (1900 ~ current_year)
    before = len(df)
    df = df[
        (df["year_made"] >= YEAR_MADE_MIN)
        & (df["year_made"] <= CURRENT_YEAR)
    ]
    logger.info(
        f"After year_made range filter ({YEAR_MADE_MIN}~{CURRENT_YEAR}): "
        f"{len(df)} records (-{before - len(df)})"
    )

    return df


def filter_eligible_artists(df: pd.DataFrame) -> pd.DataFrame:
    """작가당 작품 수 >= MIN_WORKS_PER_ARTIST 필터."""
    counts = df["artist_slug"].value_counts()
    eligible = counts[counts >= MIN_WORKS_PER_ARTIST].index
    df = df[df["artist_slug"].isin(eligible)].copy()
    logger.info(
        f"Eligible artists (>=10 works): {len(eligible)} / "
        f"records: {len(df)}"
    )
    return df


def get_artist_primary_medium(df: pd.DataFrame) -> pd.DataFrame:
    """각 작가의 대표 매체 (가장 많은 작품의 medium_category)."""
    primary = (
        df.groupby("artist_slug")["medium_category"]
        .agg(lambda s: s.mode().iloc[0])
        .reset_index()
        .rename(columns={"medium_category": "primary_medium"})
    )
    return primary


def stratified_artist_sample(
    df: pd.DataFrame, n_artists: int, seed: int
) -> list[str]:
    """매체 + 갤러리 tier 기반 stratified 작가 샘플링."""
    rng_local = np.random.default_rng(seed)
    artist_summary = (
        df.groupby("artist_slug")
        .agg(
            primary_medium=("medium_category", lambda s: s.mode().iloc[0]),
            primary_tier=("gallery_tier", lambda s: s.mode().iloc[0]),
            work_count=("artwork_id", "count"),
        )
        .reset_index()
    )

    # 매체 비율: oil / acrylic / others 단순화
    def medium_group(m: str) -> str:
        if m == "oil":
            return "oil"
        if m == "acrylic":
            return "acrylic"
        return "others"

    artist_summary["medium_group"] = artist_summary["primary_medium"].apply(
        medium_group
    )

    # 모집단 비율
    pop_dist = artist_summary["medium_group"].value_counts(normalize=True)
    logger.info(f"Population medium dist: {dict(pop_dist.round(3))}")

    # 비례 할당
    quotas: dict[str, int] = {}
    remaining = n_artists
    for grp in ["oil", "acrylic", "others"]:
        q = int(round(n_artists * pop_dist.get(grp, 0)))
        quotas[grp] = q
        remaining -= q
    # 잔여는 가장 많은 group 에 할당
    if remaining != 0:
        biggest = pop_dist.idxmax()
        quotas[biggest] += remaining

    logger.info(f"Quotas (artists per medium group): {quotas}")

    selected_artists: list[str] = []
    for grp, q in quotas.items():
        pool = artist_summary[artist_summary["medium_group"] == grp]
        if len(pool) < q:
            logger.warning(
                f"  {grp}: pool {len(pool)} < quota {q} → 전체 사용"
            )
            picked = pool["artist_slug"].tolist()
        else:
            picked = rng_local.choice(
                pool["artist_slug"].values, size=q, replace=False
            ).tolist()
        selected_artists.extend(picked)

    return selected_artists


def build_stage(
    df: pd.DataFrame,
    target_records: int,
    target_artists: int,
    works_per_artist: int,
    seed: int,
) -> pd.DataFrame:
    """Stage 데이터셋 구축.

    Args:
        df: eligible records
        target_records: 목표 record 수
        target_artists: 목표 작가 수
        works_per_artist: 작가당 최대 작품 수
        seed: 재현성용 seed

    Returns:
        curated DataFrame (target_records 근사)
    """
    artists = stratified_artist_sample(df, target_artists, seed)
    sub = df[df["artist_slug"].isin(artists)].copy()

    # 각 작가별로 max works_per_artist 작품 샘플링
    sampled_chunks: list[pd.DataFrame] = []
    for artist in artists:
        artist_works = sub[sub["artist_slug"] == artist]
        n_take = min(works_per_artist, len(artist_works))
        if len(artist_works) > n_take:
            sampled = artist_works.sample(n=n_take, random_state=seed)
        else:
            sampled = artist_works
        sampled_chunks.append(sampled)

    curated = pd.concat(sampled_chunks, ignore_index=True)
    logger.info(
        f"  → {len(curated)} records / "
        f"{curated['artist_slug'].nunique()} artists"
    )
    return curated


def report_summary(df: pd.DataFrame, name: str) -> dict:
    """단계별 요약 리포트."""
    summary = {
        "name": name,
        "n_records": len(df),
        "n_artists": int(df["artist_slug"].nunique()),
        "works_per_artist_min": int(
            df["artist_slug"].value_counts().min()
        ),
        "works_per_artist_max": int(
            df["artist_slug"].value_counts().max()
        ),
        "works_per_artist_mean": float(
            df["artist_slug"].value_counts().mean().round(2)
        ),
        "medium_dist": df["medium_category"].value_counts().to_dict(),
        "gallery_tier_dist": (
            df["gallery_tier"].astype(str).value_counts().to_dict()
        ),
        "price_krw_median": float(df["price_krw"].median()),
        "price_krw_mean": float(df["price_krw"].mean()),
        "year_made_min": int(df["year_made"].min()),
        "year_made_max": int(df["year_made"].max()),
        "artists_with_15plus_works": int(
            (df["artist_slug"].value_counts() >= SLOPE_CHECK_MIN_WORKS).sum()
        ),
    }
    return summary


def main() -> None:
    logger.info("=" * 60)
    logger.info("Stage 1-3 curated dataset builder")
    logger.info("=" * 60)

    # 1. Load + filter
    df = load_eligible()

    # 2. Eligible artists
    df = filter_eligible_artists(df)

    # 3. Build each stage
    summaries: dict = {}
    for stage_name, params in STAGES.items():
        logger.info("")
        logger.info(f"=== Building {stage_name} ===")
        curated = build_stage(
            df,
            target_records=params["records"],
            target_artists=params["artists"],
            works_per_artist=params["works_per_artist"],
            seed=SEED,
        )

        # Save (parquet + csv)
        base_name = (
            f"{stage_name}_{params['records']}x{params['artists']}"
        )
        parquet_path = OUTPUT_DIR / f"{base_name}.parquet"
        csv_path = OUTPUT_DIR / f"{base_name}.csv"
        curated.to_parquet(parquet_path, index=False)
        curated.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"  Saved: {parquet_path.relative_to(ROOT)}")
        logger.info(f"  Saved: {csv_path.relative_to(ROOT)}")

        # Summary
        summaries[stage_name] = report_summary(curated, stage_name)

    # 4. Save summary
    summary_path = OUTPUT_DIR / "stage_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    logger.info("")
    logger.info(f"Summary saved: {summary_path.relative_to(ROOT)}")

    # 5. Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    for name, s in summaries.items():
        logger.info(
            f"{name}: {s['n_records']} records / {s['n_artists']} artists / "
            f"avg {s['works_per_artist_mean']} works/artist / "
            f"{s['artists_with_15plus_works']} artists with >=15 works"
        )


if __name__ == "__main__":
    main()
