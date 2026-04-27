"""Saatchi Art 데이터 클린징 + 피처 엔지니어링.

Saatchi Art 수집 데이터를 기존 Artsy 학습 파이프라인과 동일한 스키마로 변환.
학습은 하지 않고, 기존 모델로 예측할 수 있는 형태로 준비.
"""
from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine.preprocessing.primary_medium_parser import parse_saatchi_medium

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ─── 호수 변환 테이블 (F형 기준, 기존 파이프라인과 동일) ───

HO_TABLE_F = {
    0: 180, 1: 364, 2: 520, 3: 727, 4: 1084,
    5: 1167, 6: 1338, 8: 1818, 10: 2412,
    12: 2757, 15: 3478, 20: 4304, 25: 5323,
    30: 5858, 40: 7320, 50: 9128, 60: 12636,
    80: 16918, 100: 21245, 120: 25740, 150: 33894,
    200: 43980, 300: 67060, 500: 121898,
}

USD_TO_KRW = 1380


def area_to_ho(area_cm2: float) -> int:
    best_ho = 0
    best_diff = float("inf")
    for ho, ref_area in HO_TABLE_F.items():
        diff = abs(area_cm2 - ref_area)
        if diff < best_diff:
            best_diff = diff
            best_ho = ho
    return best_ho


def aspect_to_canvas_type(aspect_ratio: float) -> str:
    if abs(aspect_ratio - 1.0) < 0.1:
        return "S"
    elif aspect_ratio < 1.25:
        return "F"
    elif aspect_ratio < 1.45:
        return "P"
    else:
        return "M"


# ─── 매체/지지체 분류 (기존 파이프라인과 동일) ───

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


def classify_support(text: str) -> str:
    m = text.lower()
    for label, keywords in SUPPORT_RULES:
        if any(kw in m for kw in keywords):
            return label
    return "other"


def classify_medium(text: str) -> str:
    m = text.lower()
    for label, keywords in MEDIUM_RULES:
        if any(kw in m for kw in keywords):
            return label
    return "other"


# ─── NLP: Bio에서 생년 추출 ───

def extract_birth_year(bio: str) -> float | None:
    """Bio 텍스트에서 생년 추출. 없으면 None."""
    if not bio:
        return None
    patterns = [
        r"(?:born|b\.)\s+(?:in\s+)?(?:on\s+)?(?:\w+\s+\d{1,2},?\s+)?(19\d{2}|20[01]\d)",
        r"(?:Born|born)\s+(?:in\s+)?(19\d{2}|20[01]\d)",
        r"\(b\.\s*(19\d{2}|20[01]\d)\)",
        r"(\d{4})년\s*생",
        r"(\d{4})년\s*출생",
    ]
    for pat in patterns:
        m = re.search(pat, bio)
        if m:
            year = int(m.group(1))
            if 1920 <= year <= 2005:
                return float(year)
    return None


# ─── NLP: 전시 텍스트에서 횟수 추출 ───

def extract_exhibition_counts(exhibitions: str, bio: str = "") -> dict:
    """exhibitions + bio 텍스트에서 전시 횟수 추정."""
    combined = f"{exhibitions or ''}\n{bio or ''}"
    if not combined.strip():
        return {"solo_count": 0, "group_count": 0, "fair_count": 0}

    solo = 0
    group = 0
    fair = 0

    # 개인전 / solo
    solo_pats = [
        r"(\d+)\s*(?:solo|individual|one.?person)\s*(?:exhibition|show)",
        r"solo\s*(?:exhibition|show)s?\s*[:]\s*(\d+)",
        r"개인전\s*[:]\s*(\d+)",
        r"(\d+)\s*개인전",
    ]
    for pat in solo_pats:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            solo = max(solo, int(m.group(1)))

    # 단체전 / group
    group_pats = [
        r"(\d+)\s*(?:group|collective|joint)\s*(?:exhibition|show)",
        r"group\s*(?:exhibition|show)s?\s*[:]\s*(\d+)",
        r"단체전\s*[:]\s*(\d+)",
        r"(\d+)\s*단체전",
    ]
    for pat in group_pats:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            group = max(group, int(m.group(1)))

    # 아트페어
    fair_pats = [
        r"(\d+)\s*(?:art\s*fair|fair)",
        r"아트페어\s*[:]\s*(\d+)",
        r"(\d+)\s*아트페어",
    ]
    for pat in fair_pats:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            fair = max(fair, int(m.group(1)))

    # 횟수가 없으면 줄 수로 추정 (exhibitions 텍스트에서)
    if not solo and not group and exhibitions:
        lines = [l.strip() for l in exhibitions.split("\n") if l.strip()]
        solo_lines = [l for l in lines if re.search(r"solo|individual|one.?person|개인", l, re.I)]
        group_lines = [l for l in lines if re.search(r"group|collective|단체", l, re.I)]
        fair_lines = [l for l in lines if re.search(r"fair|아트페어", l, re.I)]
        solo = len(solo_lines)
        group = len(group_lines)
        fair = len(fair_lines)

    return {"solo_count": solo, "group_count": group, "fair_count": fair}


def estimate_career_stage(birth_year: float | None, solo_count: int, career_age: float | None) -> int:
    """경력 단계 추정 (1=신진, 2=신진후기, 3=중견, 4=원로)."""
    age = 2026 - birth_year if birth_year else None
    if age and age >= 60 and solo_count >= 5:
        return 4
    if career_age and career_age >= 15 and solo_count >= 3:
        return 3
    if career_age and career_age >= 5:
        return 2
    if solo_count >= 10:
        return 3
    if solo_count >= 3:
        return 2
    return 1


# ─── 메인 ───

def main() -> None:
    logger.info("=== Saatchi Art 데이터 클린징 ===")

    # 1. 로드
    with open(DATA_DIR / "saatchi_kr_artworks.json", encoding="utf-8") as f:
        works = json.load(f)
    logger.info("원본: %d건", len(works))

    with open(DATA_DIR / "saatchi_kr_artists.json", encoding="utf-8") as f:
        profiles_list = json.load(f)
    profiles = {p["artist_id"]: p for p in profiles_list}
    logger.info("프로필: %d명", len(profiles))

    df = pd.DataFrame(works)

    # 2. 기본 필터
    n0 = len(df)
    df = df[df["price_usd"] > 0]
    logger.info("가격 필터 (>0): %d건 (제거 %d)", len(df), n0 - len(df))

    n1 = len(df)
    df = df[df["category"] == "painting"]
    logger.info("카테고리 필터 (painting): %d건 (제거 %d)", len(df), n1 - len(df))

    n2 = len(df)
    df = df[(df["width_cm"] > 1) & (df["height_cm"] > 1)]
    logger.info("크기 필터 (>1cm): %d건 (제거 %d)", len(df), n2 - len(df))

    n3 = len(df)
    df = df[(df["width_cm"] <= 500) & (df["height_cm"] <= 500)]
    logger.info("크기 이상치 (<=500cm): %d건 (제거 %d)", len(df), n3 - len(df))

    # 가격 KRW 변환
    df["price_krw"] = (df["price_usd"] * USD_TO_KRW).astype(int)

    n4 = len(df)
    df = df[(df["price_krw"] >= 100_000) & (df["price_krw"] <= 5_000_000_000)]
    logger.info("가격 범위 (10만~50억원): %d건 (제거 %d)", len(df), n4 - len(df))

    logger.info("--- 클린징 완료: %d건 ---", len(df))

    # 3. 프로필 조인
    df["_profile"] = df["artist_id"].apply(lambda aid: profiles.get(aid, {}))
    df["bio"] = df["_profile"].apply(lambda p: p.get("bio", ""))
    df["education"] = df["_profile"].apply(lambda p: p.get("education", ""))
    df["exhibitions_text"] = df["_profile"].apply(lambda p: p.get("exhibitions", ""))
    df["events"] = df["_profile"].apply(lambda p: p.get("events", ""))
    df["followers"] = df["_profile"].apply(lambda p: p.get("followers", 0))
    df["total_artworks_profile"] = df["_profile"].apply(lambda p: p.get("total_artworks", 0))
    df["badges"] = df["_profile"].apply(lambda p: p.get("badges", []))
    df.drop(columns=["_profile"], inplace=True)

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
    logger.info("호수: min=%d, max=%d, median=%d", df["ho"].min(), df["ho"].max(), df["ho"].median())

    # 4.2 지지체/매체 분류
    # support_type/medium_category는 v3 모델 호환을 위해 구 classify_* 유지
    df["medium_text"] = df["materials"].fillna("") + " " + df["mediums"].fillna("")
    df["support_type"] = df["medium_text"].apply(classify_support)
    df["medium_category"] = df["mediums"].fillna("").apply(classify_medium)
    # 신규 metadata 컬럼은 새 파서로
    parsed_saatchi = df.apply(
        lambda r: parse_saatchi_medium(r.get("materials"), r.get("mediums"), r.get("category")),
        axis=1,
    )
    df["medium_l1"] = parsed_saatchi.apply(lambda p: p.medium_l1)
    df["medium_leaf"] = parsed_saatchi.apply(lambda p: p.medium_leaf)
    df["support_l1"] = parsed_saatchi.apply(lambda p: p.support_l1)
    df["support_leaf"] = parsed_saatchi.apply(lambda p: p.support_leaf)
    df["mediums_json"] = parsed_saatchi.apply(lambda p: json.dumps(p.mediums, ensure_ascii=False))
    df["supports_json"] = parsed_saatchi.apply(lambda p: json.dumps(p.supports, ensure_ascii=False))
    df["has_multimedia"] = parsed_saatchi.apply(lambda p: int(p.has_multimedia))
    df["has_special_finish"] = parsed_saatchi.apply(lambda p: int(p.has_special_finish))
    df["is_excluded_for_training"] = parsed_saatchi.apply(lambda p: int(p.is_excluded_for_training))
    df["exclude_reason"] = parsed_saatchi.apply(lambda p: p.exclude_reason or "")
    df["value_grade_note"] = parsed_saatchi.apply(lambda p: p.value_grade_note or "")
    logger.info("지지체: %s", dict(df["support_type"].value_counts().head(6)))
    logger.info("매체: %s", dict(df["medium_category"].value_counts().head(6)))
    n_excl = int(df["is_excluded_for_training"].sum())
    logger.info("학습 제외 후보: %d (사유: %s)", n_excl, dict(df.loc[df["is_excluded_for_training"] == 1, "exclude_reason"].value_counts().head(6)))

    # 학습 제외 필터 — 후속 통계/aggregation 전에 적용 (Codex review #2)
    if n_excl > 0:
        n_before = len(df)
        df = df[df["is_excluded_for_training"] == 0].copy()
        logger.info("학습 제외 필터 적용: %d → %d (%d건 제거)", n_before, len(df), n_before - len(df))

    # 4.3 작품 속성
    df["is_unique"] = 1  # Saatchi는 원작 직거래
    df["is_edition"] = 0
    df["attribution_class"] = "Unique"
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["year_made"] = np.nan  # Saatchi에 제작연도 없음
    df["work_age"] = np.nan

    # 4.4 작가 피처 — 생년 (bio에서 추출)
    df["artist_birth_year"] = df["bio"].apply(extract_birth_year)
    birth_count = df["artist_birth_year"].notna().sum()
    logger.info("생년 추출: %d건 (%.1f%%)", birth_count, birth_count / len(df) * 100)

    # 작가별 생년 전파 (같은 작가의 다른 작품에서 추출된 생년 사용)
    artist_births = df.dropna(subset=["artist_birth_year"]).groupby("artist_id")["artist_birth_year"].first().to_dict()
    df["artist_birth_year"] = df.apply(
        lambda r: r["artist_birth_year"] if pd.notna(r["artist_birth_year"]) else artist_births.get(r["artist_id"]),
        axis=1,
    )
    birth_after = df["artist_birth_year"].notna().sum()
    logger.info("생년 전파 후: %d건 (%.1f%%)", birth_after, birth_after / len(df) * 100)

    # 팔로워
    df["ln_followers"] = df["followers"].fillna(0).apply(lambda f: math.log(f + 1))

    # 전시 횟수 (NLP)
    exh_counts = df.apply(
        lambda r: extract_exhibition_counts(r.get("exhibitions_text", ""), r.get("bio", "")),
        axis=1,
    )
    exh_df = pd.DataFrame(exh_counts.tolist())
    df["solo_count"] = exh_df["solo_count"].values
    df["group_count"] = exh_df["group_count"].values
    df["fair_count"] = exh_df["fair_count"].values
    has_exh = ((df["solo_count"] > 0) | (df["group_count"] > 0) | (df["fair_count"] > 0)).sum()
    logger.info("전시 추출: %d건 (%.1f%%)", has_exh, has_exh / len(df) * 100)

    # career_age (전시 횟수 기반 추정, 정확한 첫 전시 연도 없음)
    df["career_age"] = np.nan

    # career_stage
    df["career_stage"] = df.apply(
        lambda r: estimate_career_stage(
            r.get("artist_birth_year"),
            r.get("solo_count", 0),
            r.get("career_age"),
        ),
        axis=1,
    )
    logger.info("경력 단계: %s", dict(df["career_stage"].value_counts().sort_index()))

    # 작가 통계
    df["artist_total_works"] = df["total_artworks_profile"].fillna(0).astype(int)
    df["for_sale_ratio"] = 1.0  # Saatchi는 모두 판매 중
    df["request_ratio"] = 0.0  # price on request 없음
    df["artist_is_p1"] = False

    # vintage / freshness (work_age 없으므로 0)
    df["vintage_premium"] = 0.0
    df["freshness_discount"] = 0.0

    # 4.5 갤러리 피처
    df["gallery_name"] = "Saatchi Art"
    df["gallery_type"] = "Online Gallery"
    df["gallery_tier"] = 3  # Saatchi Art = mid-tier 온라인 갤러리
    df["gallery_city_count"] = 1
    df["has_seoul"] = 0
    df["has_international"] = 1  # 국제 플랫폼

    # 4.6 통화
    df["price_currency"] = "USD"
    df["is_krw"] = 0

    # 4.7 타겟
    df["ln_price"] = df["price_krw"].apply(math.log)

    # 4.8 메타 (기존 스키마와 호환)
    df["artist_name"] = df.apply(
        lambda r: f"{r.get('artist_first_name', '')} {r.get('artist_last_name', '')}".strip(),
        axis=1,
    )
    df["artist_slug"] = df["artist_id"].astype(str)  # Saatchi는 slug 대신 ID 사용
    df["price_raw"] = df["price_usd"].apply(lambda p: f"${p:,.0f}")
    df["dimensions_cm"] = df.apply(
        lambda r: f"{r['width_cm']} × {r['height_cm']}" + (f" × {r['depth_cm']}" if r.get("depth_cm") else "") + " cm",
        axis=1,
    )
    df["medium"] = df["mediums"].fillna("")
    df["source"] = "saatchi"

    # 5. 피처 선택 (기존 46컬럼 + source)
    feature_cols = [
        "ho", "ho_power", "ln_ho", "area_cm2", "aspect_ratio", "is_small",
        "support_type", "medium_category", "attribution_class", "is_unique", "is_edition",
        "year_made", "work_age", "has_depth",
        "artist_birth_year", "career_age", "career_stage",
        "ln_followers", "artist_total_works", "for_sale_ratio", "request_ratio",
        "solo_count", "group_count", "fair_count",
        "artist_is_p1",
        "gallery_name", "gallery_type", "gallery_tier", "gallery_city_count",
        "has_seoul", "has_international",
        "price_currency", "is_krw",
        "vintage_premium", "freshness_discount",
    ]

    meta_cols = [
        "artwork_id", "artist_slug", "artist_name", "title", "price_krw", "price_raw",
        "dimensions_cm", "medium", "image_url", "artwork_url",
    ]

    # 신규 parser metadata (PR1 통합) — additive, 모델 입력 X
    parser_meta_cols = [
        "medium_l1", "medium_leaf", "support_l1", "support_leaf",
        "mediums_json", "supports_json",
        "has_multimedia", "has_special_finish",
        "exclude_reason", "value_grade_note",
    ]

    # 학습 제외 필터는 4.2 medium 파싱 직후 이미 적용됨
    out = df[meta_cols + feature_cols + parser_meta_cols + ["ln_price", "source"]].copy()

    # 6. 저장
    out_path = DATA_DIR / "saatchi_cleaned.parquet"
    out.to_parquet(out_path, index=False)
    logger.info("저장: %s (%d건, %d컬럼)", out_path, len(out), len(out.columns))

    csv_path = DATA_DIR / "saatchi_cleaned.csv"
    out.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info("CSV: %s", csv_path)

    # 7. 통계 리포트
    print(f"\n{'='*70}")
    print("Saatchi Art 데이터 클린징 결과")
    print(f"{'='*70}")

    print(f"\n  [필터링]")
    print(f"  원본: 30,607건")
    print(f"  클린 후: {len(out):,}건")
    print(f"  작가: {out['artist_slug'].nunique():,}명")

    print(f"\n  [가격 분포 (KRW)]")
    prices = out["price_krw"]
    print(f"  최소: {prices.min():,.0f}원")
    print(f"  최대: {prices.max():,.0f}원")
    print(f"  중앙: {prices.median():,.0f}원")
    print(f"  평균: {prices.mean():,.0f}원")

    print(f"\n  [가격대별]")
    bins = [0, 1_000_000, 3_000_000, 5_000_000, 10_000_000, 30_000_000, float("inf")]
    labels = ["~100만", "100~300만", "300~500만", "500~1천만", "1천~3천만", "3천만+"]
    price_bins = pd.cut(prices, bins=bins, labels=labels)
    for label in labels:
        cnt = (price_bins == label).sum()
        print(f"  {label}: {cnt:,}건 ({cnt/len(out)*100:.1f}%)")

    print(f"\n  [호수 분포]")
    print(f"  최소: {out['ho'].min()}호")
    print(f"  최대: {out['ho'].max()}호")
    print(f"  중앙: {out['ho'].median():.0f}호")

    print(f"\n  [매체]")
    for mc, cnt in out["medium_category"].value_counts().head(8).items():
        print(f"  {mc}: {cnt:,}건 ({cnt/len(out)*100:.1f}%)")

    print(f"\n  [지지체]")
    for st, cnt in out["support_type"].value_counts().head(6).items():
        print(f"  {st}: {cnt:,}건 ({cnt/len(out)*100:.1f}%)")

    print(f"\n  [피처 완전도]")
    for col in ["artist_birth_year", "career_age", "year_made", "solo_count"]:
        if col in out.columns:
            if col in ["solo_count"]:
                filled = (out[col] > 0).sum()
            else:
                filled = out[col].notna().sum()
            print(f"  {col}: {filled:,}/{len(out):,} ({filled/len(out)*100:.1f}%)")

    print(f"\n  [경력 단계]")
    for stage, cnt in out["career_stage"].value_counts().sort_index().items():
        labels_map = {1: "신진", 2: "신진후기", 3: "중견", 4: "원로"}
        print(f"  Stage {stage} ({labels_map.get(stage, '?')}): {cnt:,}건")

    print(f"\n  [기존 데이터 비교]")
    try:
        existing = pd.read_parquet(DATA_DIR / "primary_market_dataset.parquet")
        print(f"  기존 (Artsy+Artue): {len(existing):,}건, {existing['artist_slug'].nunique():,}명")
        print(f"  기존 가격 중앙: {existing['price_krw'].median():,.0f}원")
        print(f"  Saatchi: {len(out):,}건, {out['artist_slug'].nunique():,}명")
        print(f"  Saatchi 가격 중앙: {prices.median():,.0f}원")
    except Exception:
        print(f"  기존 데이터 없음")

    print(f"\n  [저장]")
    print(f"  data/saatchi_cleaned.parquet")
    print(f"  data/saatchi_cleaned.csv")


if __name__ == "__main__":
    main()
