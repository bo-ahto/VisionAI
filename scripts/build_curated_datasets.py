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
    # 작가 메타 — 작가 단위 누락 시 표본 편향 위험 (코덱스 P1)
    "artist_birth_year",
    "career_age",
    # 작품 메타 — 결측 없는 데이터로 통일
    "image_url",
]

# 추가 필수 (텍스트 + 빈 문자열 처리 필요)
REQUIRED_TEXT_FIELDS = [
    "medium_l1",
    "support_l1",
    "support_leaf",
]

# JSON 배열 컬럼 — '[]' 빈 배열 제외
REQUIRED_JSON_ARRAY_FIELDS = [
    "mediums_json",
    "supports_json",
]

# 분석에 사용 안 함 + 거의 모두 결측 → 출력에서 drop
DROP_COLUMNS = [
    "exclude_reason",  # 100% 결측 (정상 데이터 by design)
    "value_grade_note",  # 98.5% 결측
]

# CSV 출력용 한글 병기 컬럼명 매핑 (영문 → "한글 (영문)")
KR_COLUMN_LABELS = {
    "artwork_id": "작품ID",
    "artist_slug": "작가slug",
    "artist_name": "작가명",
    "title": "작품명",
    "price_krw": "가격_KRW",
    "price_raw": "원가격",
    "dimensions_cm": "크기_cm",
    "medium": "재료_원문",
    "image_url": "이미지URL",
    "artwork_url": "작품URL",
    "ho": "호수",
    "ho_power": "호수_가중",
    "ln_ho": "log_호수",
    "area_cm2": "면적_cm2",
    "aspect_ratio": "종횡비",
    "is_small": "소형작품여부",
    "support_type": "지지체타입",
    "medium_category": "재료_분류",
    "year_made": "제작연도",
    "work_age": "작품경과년수",
    "has_depth": "입체여부",
    "artist_birth_year": "작가_출생년",
    "career_age": "활동연차",  # 작가 첫 작품 기준 N년차 (재계산 값)
    "career_stage": "활동등급",  # 합성 score (followers/works/exhibitions 종합)
    "ln_followers": "log_팔로워수",
    "artist_total_works": "작가_총작품수",
    "for_sale_ratio": "판매가능비율",
    "request_ratio": "문의비율",
    "solo_count": "개인전수",
    "group_count": "단체전수",
    "fair_count": "아트페어수",
    "artist_is_p1": "주력작가여부",
    "gallery_name": "갤러리명",
    "gallery_tier": "갤러리등급",
    "gallery_city_count": "갤러리_도시수",
    "has_seoul": "서울갤러리여부",
    "has_international": "해외갤러리여부",
    "price_currency": "가격통화",
    "is_krw": "KRW통화여부",
    "freshness_discount": "신작_할인",
    "medium_l1": "재료_대분류",
    "medium_leaf": "재료_세분류",
    "support_l1": "지지체_대분류",
    "support_leaf": "지지체_세분류",
    "mediums_json": "재료_JSON",
    "supports_json": "지지체_JSON",
    "has_multimedia": "복합매체여부",
    "ln_price": "log_가격",
}


def make_kr_columns(df: pd.DataFrame) -> pd.DataFrame:
    """CSV 출력용 — '한글 (영문)' 헤더로 변환."""
    new_cols = {}
    for col in df.columns:
        kr = KR_COLUMN_LABELS.get(col)
        if kr:
            new_cols[col] = f"{kr} ({col})"
        else:
            new_cols[col] = col
    return df.rename(columns=new_cols)

# 중복 판정 canonical key
DUP_KEY = ["artist_slug", "title", "year_made", "area_cm2", "medium_category"]

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

# 작가 활동 연령 합리성 (작품 제작 시 최소 15세)
MIN_CREATION_AGE = 15

# Aspect ratio 극단 (자릿수 오타 의심) — 회화/드로잉 통상 1:5 이내
MAX_ASPECT_RATIO = 10.0


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

    # 3. 필수 변수 결측 없음 (NaN + 빈 문자열 모두 제외)
    for col in REQUIRED_FIELDS:
        before = len(df)
        notna_mask = df[col].notna()
        # 모든 컬럼에 대해 빈 문자열 체크 (dtype 무관)
        col_str = df[col].astype(str).str.strip()
        non_empty_mask = (col_str != "") & (col_str.str.lower() != "nan")
        df = df[notna_mask & non_empty_mask]
        after = len(df)
        if before != after:
            logger.info(f"  {col} 결측/빈문자 제거: -{before - after}")

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

    # 6. medium 텍스트 품질 검증
    #    - 숫자/연도만 들어간 medium 제외 (예: "2024", "201205")
    before = len(df)
    medium_str = df["medium"].astype(str).str.strip()
    is_numeric_only = medium_str.str.fullmatch(r"\d+(\.\d+)?", na=False)
    df = df[~is_numeric_only]
    logger.info(
        f"After medium-text quality filter (숫자만 medium 제외): "
        f"{len(df)} records (-{before - len(df)})"
    )

    # 6.1. 텍스트 필수 변수 결측/공백 제외 (medium_l1 / support_l1 / support_leaf)
    for col in REQUIRED_TEXT_FIELDS:
        before = len(df)
        col_str = df[col].astype(str).str.strip()
        df = df[df[col].notna() & (col_str != "")]
        logger.info(
            f"After {col} 결측/공백 제외: {len(df)} records (-{before - len(df)})"
        )

    # 6.2. JSON 배열 빈 배열 제외 (mediums_json / supports_json)
    for col in REQUIRED_JSON_ARRAY_FIELDS:
        before = len(df)
        col_str = df[col].astype(str).str.strip()
        df = df[(col_str != "") & (col_str != "[]")]
        logger.info(
            f"After {col} 빈 배열 제외: {len(df)} records (-{before - len(df)})"
        )

    # 6.5. title 앞뒤 공백 정리 (코덱스 P2)
    df["title"] = df["title"].astype(str).str.strip()

    # 6.6. title 데이터 품질 — 글자 없는 코드성 title 제외
    #      (alphabet/한글 문자 1개 이상 포함 필수)
    before = len(df)
    has_letters = df["title"].str.contains(
        r"[a-zA-Z가-힣]", regex=True, na=False
    )
    df = df[has_letters]
    logger.info(
        f"After title-quality filter (글자 없는 코드성 title 제외): "
        f"{len(df)} records (-{before - len(df)})"
    )

    # 6.7. medium 표기 정규화 (대소문자 → title case)
    #      "Oil on canvas" / "Oil on Canvas" 등 통일
    df["medium"] = (
        df["medium"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # 6.8. 작가 활동 연령 합리성 (year_made - birth_year >= 15)
    #      예: birth_year=2013, year_made=2022 → 9세 → 의심 row 제외
    before = len(df)
    creation_age = df["year_made"] - df["artist_birth_year"]
    df = df[creation_age >= MIN_CREATION_AGE]
    logger.info(
        f"After creation-age filter (>= {MIN_CREATION_AGE}세): "
        f"{len(df)} records (-{before - len(df)})"
    )

    # 6.85. career_age 재계산: 작가 첫 작품 연도 기반
    #       기존 career_age (작가별 고정값, 정의 불명확) → overwrite
    #       새 계산: year_made - 작가의 first year_made
    #       → within-artist 변동 가능 (활동 N년차 작품)
    first_year = df.groupby("artist_slug")["year_made"].transform("min")
    df["career_age"] = (df["year_made"] - first_year).astype("Int64")
    logger.info(
        "career_age 재계산 (작가 첫 작품 기준): "
        f"min={df['career_age'].min()}, max={df['career_age'].max()}, "
        f"mean={df['career_age'].mean():.2f}"
    )

    # 6.9. Aspect ratio 극단 제외 (자릿수 오타 의심)
    #      예: 112 × 1112 cm (1112은 112의 오타 의심)
    before = len(df)
    df = df[df["aspect_ratio"].between(1 / MAX_ASPECT_RATIO, MAX_ASPECT_RATIO)]
    logger.info(
        f"After aspect-ratio filter (1/{MAX_ASPECT_RATIO} ~ {MAX_ASPECT_RATIO}): "
        f"{len(df)} records (-{before - len(df)})"
    )

    # 7. 중복 제거 (canonical key 기준, 첫 번째 유지)
    before = len(df)
    df = df.drop_duplicates(subset=DUP_KEY, keep="first").reset_index(drop=True)
    logger.info(
        f"After dedup ({DUP_KEY}): {len(df)} records (-{before - len(df)})"
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

        # 결측만 있는 / 거의 결측 컬럼 drop
        drop_cols = [c for c in DROP_COLUMNS if c in curated.columns]
        if drop_cols:
            curated = curated.drop(columns=drop_cols)

        # 상수 컬럼 자동 drop (회귀 정보값 0 / 다중공선성 회피)
        # 예: vintage_premium=0 모두, source='artsy' 모두, gallery_type='Gallery' 모두
        constant_cols = [
            col
            for col in curated.columns
            if curated[col].nunique(dropna=False) == 1
        ]
        if constant_cols:
            curated = curated.drop(columns=constant_cols)
            logger.info(f"  Dropped constants: {constant_cols}")

        # Save
        # - parquet: 원본 영문 컬럼 (코드 호환성)
        # - csv: 한글 병기 헤더 (가독성)
        base_name = (
            f"{stage_name}_{params['records']}x{params['artists']}"
        )
        parquet_path = OUTPUT_DIR / f"{base_name}.parquet"
        csv_path = OUTPUT_DIR / f"{base_name}.csv"
        curated.to_parquet(parquet_path, index=False)
        curated_kr = make_kr_columns(curated)
        curated_kr.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"  Saved: {parquet_path.relative_to(ROOT)}")
        logger.info(f"  Saved: {csv_path.relative_to(ROOT)} (한글 병기 헤더)")

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
