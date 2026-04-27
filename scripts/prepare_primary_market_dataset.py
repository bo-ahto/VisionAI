"""1차 시장 가격 예측 학습 데이터셋 준비.

Artsy 수집 데이터 → 클린징 → 피처 엔지니어링 → 학습용 데이터셋 생성.
실험계획서 섹션 2, 5 기반.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from visionai.price_engine.preprocessing.primary_medium_parser import parse_artsy_medium

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ─── 호수 변환 테이블 (F형 기준) ──────────────────────────────────

HO_TABLE_F = {
    0: 180, 1: 364, 2: 520, 3: 727, 4: 1084,
    5: 1167, 6: 1338, 8: 1818, 10: 2412,
    12: 2757, 15: 3478, 20: 4304, 25: 5323,
    30: 5858, 40: 7320, 50: 9128, 60: 12636,
    80: 16918, 100: 21245, 120: 25740, 150: 33894,
    200: 43980, 300: 67060, 500: 121898,
}


def aspect_to_canvas_type(aspect_ratio: float) -> str:
    """종횡비로 F/P/M/S 타입 추정."""
    if abs(aspect_ratio - 1.0) < 0.1:
        return "S"
    elif aspect_ratio < 1.25:
        return "F"
    elif aspect_ratio < 1.45:
        return "P"
    else:
        return "M"


def area_to_ho(area_cm2: float) -> int:
    """면적(cm²)을 가장 가까운 호수로 변환 (F형 기준)."""
    best_ho = 0
    best_diff = float("inf")
    for ho, ref_area in HO_TABLE_F.items():
        diff = abs(area_cm2 - ref_area)
        if diff < best_diff:
            best_diff = diff
            best_ho = ho
    return best_ho


# ─── 매체/지지체 분류 ──────────────────────────────────────────────

SUPPORT_RULES = [
    ("canvas", ["canvas"]),
    ("linen", ["linen"]),
    ("paper", ["paper", "korean paper", "jangji", "hanji", "washi"]),
    ("panel", ["panel", "wood", "board", "mdf"]),
    ("silk", ["silk"]),
    ("metal", ["aluminum", "aluminium", "stainless", "copper", "brass"]),
]

MEDIUM_RULES = [
    ("oil", ["oil"]),
    ("acrylic", ["acrylic"]),
    ("ink", ["ink", "sumi"]),
    ("watercolor", ["watercolor", "gouache", "aquarelle"]),
    ("pigment", ["pigment", "color on"]),
    ("mixed", ["mixed media", "mixed technique"]),
    ("pastel", ["pastel"]),
    ("pencil", ["pencil", "graphite", "charcoal"]),
]


def classify_support(medium: str) -> str:
    """medium 문자열에서 지지체 분류."""
    m = medium.lower()
    for label, keywords in SUPPORT_RULES:
        if any(kw in m for kw in keywords):
            return label
    return "other"


def classify_medium(medium: str) -> str:
    """medium 문자열에서 매체 분류."""
    m = medium.lower()
    for label, keywords in MEDIUM_RULES:
        if any(kw in m for kw in keywords):
            return label
    return "other"


# ─── 갤러리 티어 추정 ──────────────────────────────────────────────

def compute_gallery_stats(df: pd.DataFrame) -> dict[str, dict]:
    """갤러리별 통계 계산."""
    stats: dict[str, dict] = {}
    for gal, group in df.groupby("gallery_name"):
        city_count = len(str(group.iloc[0].get("gallery_cities", "")).split(","))
        stats[gal] = {
            "count": len(group),
            "avg_price": group["price_krw"].mean(),
            "city_count": city_count,
        }
    return stats


def estimate_gallery_tier(
    gallery_name: str,
    gallery_cities: str,
    gallery_stats: dict,
    artist_fair_counts: dict,
) -> int:
    """갤러리 티어 추정 (1=메가, 5=신생)."""
    stat = gallery_stats.get(gallery_name, {})
    city_count = len(str(gallery_cities).split(",")) if gallery_cities else 0
    avg_price = stat.get("avg_price", 0)
    score = 0

    if city_count >= 4:
        score += 3
    elif city_count >= 2:
        score += 2

    if avg_price >= 50_000_000:
        score += 3
    elif avg_price >= 10_000_000:
        score += 2
    elif avg_price >= 3_000_000:
        score += 1

    work_count = stat.get("count", 0)
    if work_count >= 50:
        score += 2
    elif work_count >= 20:
        score += 1

    if score >= 7:
        return 1
    elif score >= 5:
        return 2
    elif score >= 3:
        return 3
    elif score >= 1:
        return 4
    else:
        return 5


# ─── 메인 파이프라인 ──────────────────────────────────────────────

def main() -> None:
    logger.info("=== 1차 시장 학습 데이터셋 준비 ===")

    # 1. 로드
    with open(DATA_DIR / "artsy_kr_artworks.json", encoding="utf-8") as f:
        works = json.load(f)
    logger.info("원본: %d건", len(works))

    # 작가 shows 데이터
    shows_path = DATA_DIR / "artsy_kr_artist_shows.json"
    shows_data: dict = {}
    if shows_path.exists():
        with open(shows_path, encoding="utf-8") as f:
            shows_data = json.load(f)
    logger.info("작가 shows: %d명", len(shows_data))

    # 2. 기본 필터: Painting + 가격 공개
    df = pd.DataFrame(works)
    df = df[df["category"] == "Painting"]
    df = df[df["price_krw"].notna() & (df["price_krw"] > 0)]
    logger.info("Painting + 가격공개: %d건", len(df))

    # 3. 클린징
    n_before = len(df)

    # 3.1 가격 이상치
    df = df[df["price_krw"] >= 100_000]  # 10만원 미만
    df = df[df["price_krw"] <= 5_000_000_000]  # 50억원 초과
    logger.info("가격 필터 (10만~50억): %d건 (제거 %d)", len(df), n_before - len(df))

    # 3.2 크기 필터
    n_before = len(df)
    df = df[df["width_cm"].notna() & (df["width_cm"] > 1)]
    df = df[df["height_cm"].notna() & (df["height_cm"] > 1)]
    logger.info("크기 필터: %d건 (제거 %d)", len(df), n_before - len(df))

    # 3.3 birth_year 필터 (없으면 제거하지 않고 NaN 유지)
    logger.info("birth_year 유효: %d건", df["artist_birth_year"].notna().sum())

    # 4. 피처 엔지니어링
    logger.info("--- 피처 엔지니어링 ---")

    # 4.1 크기 → 호수
    df["area_cm2"] = df["width_cm"] * df["height_cm"]
    df["aspect_ratio"] = df.apply(
        lambda r: max(r["width_cm"], r["height_cm"]) / max(min(r["width_cm"], r["height_cm"]), 0.1),
        axis=1,
    )
    df["canvas_type"] = df["aspect_ratio"].apply(aspect_to_canvas_type)
    df["ho"] = df["area_cm2"].apply(area_to_ho)
    df["ln_ho"] = df["ho"].apply(lambda h: math.log(h + 1))
    df["ho_power"] = df["ho"].apply(lambda h: h ** 0.74 if h > 0 else 0)
    df["is_small"] = (df["ho"] <= 3).astype(int)
    logger.info("호수 변환 완료 (min=%d, max=%d, median=%d)", df["ho"].min(), df["ho"].max(), df["ho"].median())

    # 4.2 지지체/매체 분류 — 새 시트 기반 파서 (PR1 통합)
    parsed_artsy = df.apply(
        lambda r: parse_artsy_medium(r.get("medium"), r.get("category")),
        axis=1,
    )
    df["support_type"] = parsed_artsy.apply(lambda p: p.support_type)
    df["medium_category"] = parsed_artsy.apply(lambda p: p.medium_category)
    # 신규 leaf/list 컬럼 (downstream에서 점진적 활용)
    df["medium_l1"] = parsed_artsy.apply(lambda p: p.medium_l1)
    df["medium_leaf"] = parsed_artsy.apply(lambda p: p.medium_leaf)
    df["support_l1"] = parsed_artsy.apply(lambda p: p.support_l1)
    df["support_leaf"] = parsed_artsy.apply(lambda p: p.support_leaf)
    df["mediums_json"] = parsed_artsy.apply(lambda p: json.dumps(p.mediums, ensure_ascii=False))
    df["supports_json"] = parsed_artsy.apply(lambda p: json.dumps(p.supports, ensure_ascii=False))
    df["has_multimedia"] = parsed_artsy.apply(lambda p: int(p.has_multimedia))
    df["has_special_finish"] = parsed_artsy.apply(lambda p: int(p.has_special_finish))
    df["is_excluded_for_training"] = parsed_artsy.apply(lambda p: int(p.is_excluded_for_training))
    df["exclude_reason"] = parsed_artsy.apply(lambda p: p.exclude_reason or "")
    df["value_grade_note"] = parsed_artsy.apply(lambda p: p.value_grade_note or "")
    logger.info("지지체: %s", dict(df["support_type"].value_counts().head(6)))
    logger.info("매체: %s", dict(df["medium_category"].value_counts().head(6)))
    n_excl = int(df["is_excluded_for_training"].sum())
    logger.info("학습 제외 후보: %d (사유: %s)", n_excl, dict(df.loc[df["is_excluded_for_training"] == 1, "exclude_reason"].value_counts().head(6)))

    # 4.3 제작연도 → work_age
    df["year_made"] = df["date"].apply(lambda d: int(re.match(r"(\d{4})", str(d)).group(1)) if re.match(r"(\d{4})", str(d)) else None)
    df["work_age"] = df["year_made"].apply(lambda y: 2026 - y if y else None)

    # 4.4 에디션
    df["is_unique"] = (df["attribution_class"] == "Unique").astype(int)
    df["is_edition"] = (df["attribution_class"] == "Limited edition").astype(int)

    # 4.5 3D
    df["has_depth"] = df["depth_cm"].notna().astype(int)

    # 4.6 작가 피처
    df["ln_followers"] = df["artist_followers"].fillna(0).apply(lambda f: math.log(f + 1))
    df["for_sale_ratio"] = df.apply(
        lambda r: r["artist_for_sale"] / max(r["artist_total_works"], 1),
        axis=1,
    )

    # request_ratio: 작가별 "Price on request" 비율
    all_df = pd.DataFrame(works)
    artist_request = all_df.groupby("artist_slug").apply(
        lambda g: g["price_raw"].str.contains("request", case=False, na=False).mean()
    ).to_dict()
    df["request_ratio"] = df["artist_slug"].map(artist_request).fillna(0)

    # shows 데이터 매칭
    def get_show_feat(slug: str, key: str, default: int = 0) -> int:
        sd = shows_data.get(slug, {})
        return sd.get(key, default)

    df["solo_count"] = df["artist_slug"].apply(lambda s: get_show_feat(s, "solo_count"))
    df["group_count"] = df["artist_slug"].apply(lambda s: get_show_feat(s, "group_count"))
    df["fair_count"] = df["artist_slug"].apply(lambda s: get_show_feat(s, "fair_count"))

    # career_age: 첫 전시 연도 기반
    def get_career_age(slug: str) -> float | None:
        sd = shows_data.get(slug, {})
        show_list = sd.get("shows", [])
        years = []
        for s in show_list:
            d = s.get("start_at", "") or s.get("d", "")
            m = re.match(r"(\d{4})", d)
            if m:
                years.append(int(m.group(1)))
        if years:
            return 2026 - min(years)
        return None

    df["career_age"] = df["artist_slug"].apply(get_career_age)

    # career_stage (1~4)
    def estimate_career_stage(row: pd.Series) -> int:
        birth = row.get("artist_birth_year")
        solo = row.get("solo_count", 0)
        career_age = row.get("career_age")
        if birth:
            age = 2026 - birth
        else:
            age = None

        if age and age >= 60 and solo >= 5:
            return 4  # 원로
        if career_age and career_age >= 15 and solo >= 3:
            return 3  # 중견
        if career_age and career_age >= 5:
            return 2  # 신진 후기
        return 1  # 신진

    df["career_stage"] = df.apply(estimate_career_stage, axis=1)

    # vintage_premium / freshness_discount
    df["vintage_premium"] = df.apply(
        lambda r: r["work_age"] if r.get("work_age") and r["career_stage"] >= 3 else 0,
        axis=1,
    )
    df["freshness_discount"] = df.apply(
        lambda r: r["work_age"] if r.get("work_age") and r["career_stage"] < 3 else 0,
        axis=1,
    )

    # 4.7 갤러리 피처
    gallery_stats = compute_gallery_stats(df)
    df["gallery_city_count"] = df["gallery_cities"].fillna("").apply(
        lambda c: len([x for x in c.split(",") if x.strip()])
    )
    df["has_seoul"] = df["gallery_cities"].fillna("").str.contains("Seoul", case=False).astype(int)
    df["has_international"] = (df["gallery_city_count"] >= 2).astype(int)
    df["gallery_tier"] = df.apply(
        lambda r: estimate_gallery_tier(r["gallery_name"], r.get("gallery_cities", ""), gallery_stats, {}),
        axis=1,
    )

    # 4.8 통화
    df["is_krw"] = (df["price_currency"] == "KRW").astype(int)

    # 4.9 로그 가격 (타겟)
    df["ln_price"] = df["price_krw"].apply(math.log)

    # 5. 최종 피처 선택
    feature_cols = [
        # 크기
        "ho", "ho_power", "ln_ho", "area_cm2", "aspect_ratio", "is_small",
        # 작품
        "support_type", "medium_category", "attribution_class", "is_unique", "is_edition",
        "year_made", "work_age", "has_depth",
        # 작가
        "artist_birth_year", "career_age", "career_stage",
        "ln_followers", "artist_total_works", "for_sale_ratio", "request_ratio",
        "solo_count", "group_count", "fair_count",
        "artist_is_p1",
        # 갤러리
        "gallery_name", "gallery_type", "gallery_tier", "gallery_city_count",
        "has_seoul", "has_international",
        # 컨텍스트
        "price_currency", "is_krw",
        "vintage_premium", "freshness_discount",
    ]

    meta_cols = [
        "artwork_id", "artist_slug", "artist_name", "title", "price_krw", "price_raw",
        "dimensions_cm", "medium", "image_url", "artwork_url",
    ]

    # 6. 저장
    out = df[meta_cols + feature_cols + ["ln_price"]].copy()
    out_path = DATA_DIR / "primary_market_dataset.parquet"
    out.to_parquet(out_path, index=False)
    logger.info("Parquet 저장: %s (%d건, %d컬럼)", out_path, len(out), len(out.columns))

    csv_path = DATA_DIR / "primary_market_dataset.csv"
    out.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info("CSV 저장: %s", csv_path)

    # 7. 요약
    print(f"\n{'='*70}")
    print("1차 시장 학습 데이터셋 준비 완료")
    print(f"{'='*70}")
    print(f"  총 건수: {len(out):,}")
    print(f"  작가 수: {out['artist_slug'].nunique():,}")
    print(f"  갤러리 수: {out['gallery_name'].nunique():,}")
    print()
    print(f"  [타겟]")
    print(f"  price_krw 중앙값: {out['price_krw'].median():,.0f}원")
    print(f"  price_krw 평균: {out['price_krw'].mean():,.0f}원")
    print()
    print(f"  [피처 요약]")
    print(f"  호수 중앙: {out['ho'].median():.0f}")
    print(f"  지지체: {dict(out['support_type'].value_counts().head(5))}")
    print(f"  매체: {dict(out['medium_category'].value_counts().head(5))}")
    print(f"  career_stage: {dict(out['career_stage'].value_counts().sort_index())}")
    print(f"  gallery_tier: {dict(out['gallery_tier'].value_counts().sort_index())}")
    print(f"  유니크: {out['is_unique'].sum():,} / 에디션: {out['is_edition'].sum():,}")
    print(f"  KRW 작품: {out['is_krw'].sum():,}")
    print()
    print(f"  [피처 완성도]")
    for col in feature_cols:
        non_null = out[col].notna().sum()
        pct = non_null * 100 // len(out)
        if pct < 100:
            print(f"    {col}: {pct}% ({non_null:,}/{len(out):,})")


if __name__ == "__main__":
    main()
