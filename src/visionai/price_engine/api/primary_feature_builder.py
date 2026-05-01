"""Phase 1 피처 빌더 — 37개 피처 생성."""

from __future__ import annotations

import math

# ─── 호수 변환 테이블 (F형 기준) ───
HO_TABLE_F = {
    0: 180,
    1: 364,
    2: 520,
    3: 727,
    4: 1084,
    5: 1167,
    6: 1338,
    8: 1818,
    10: 2412,
    12: 2757,
    15: 3478,
    20: 4304,
    25: 5323,
    30: 5858,
    40: 7320,
    50: 9128,
    60: 12636,
    80: 16918,
    100: 21245,
    120: 25740,
    150: 33894,
    200: 43980,
    300: 67060,
    500: 121898,
}

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

SUPPORT_FACTORS = {
    "canvas": 1.0,
    "linen": 1.1,
    "paper": 0.8,
    "panel": 0.9,
    "silk": 1.0,
    "metal": 0.9,
    "other": 0.85,
}


# ─── career_stage v2 (multi-factor 연속 점수, 0~8) ─────────────────────
def career_stage_v2_score(
    artist_birth_year: float | int | None,
    solo_count: float | int | None,
    group_count: float | int | None,
    fair_count: float | int | None,
    ln_followers: float | None,
    current_year: int = 2026,
) -> float:
    """기존 4단계 분류 대체 — 연령/활동량/시장존재감 통합 점수.

    배경 (Codex review, 2026-04-27): 기존 career_stage가 Artsy에서 Stage 3=0건,
    Stage 4=0.2%로 사실상 binary. v2는 0~8 연속 점수로 모델이 임계값을 학습.

    Codex 후속 P1 (2026-04-27): 초안에 포함됐던 career_age 항은 제거.
    학습 데이터(prepare_primary_market_dataset.py: artist shows에서 도출)와
    서빙 프로필(artist_matcher.py:83 — 항상 0 고정, DB 스키마에도 컬럼 없음)
    간 학습/서빙 드리프트 발생 → career_duration 항 (0~2) 제외하고 0~8 스케일.

    구성 요소 (각 cap):
    - age_score (0~3):     (age - 30) / 12, cap [0, 3]
    - activity_score (0~3): log1p(solo + 0.7*fair + 0.3*group), cap 3
    - market_presence (0~2): ln_followers / 6, cap 2
    """
    score = 0.0
    if artist_birth_year is not None and not _is_nan(artist_birth_year) and artist_birth_year > 0:
        age = current_year - float(artist_birth_year)
        score += min(max((age - 30) / 12, 0), 3)
    solo = float(solo_count or 0)
    group = float(group_count or 0)
    fair = float(fair_count or 0)
    activity = solo + 0.7 * fair + 0.3 * group
    score += min(math.log1p(activity), 3)
    if ln_followers is not None and not _is_nan(ln_followers):
        score += min(float(ln_followers) / 6, 2)
    return float(score)


def _is_nan(v) -> bool:
    try:
        return v != v  # NaN != NaN
    except Exception:
        return False


def area_to_ho(area_cm2: float) -> int:
    best_ho, best_diff = 0, float("inf")
    for ho, ref in HO_TABLE_F.items():
        diff = abs(area_cm2 - ref)
        if diff < best_diff:
            best_diff, best_ho = diff, ho
    return best_ho


def classify_support(text: str) -> str:
    t = text.lower()
    for label, keywords in SUPPORT_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def classify_medium(text: str) -> str:
    t = text.lower()
    for label, keywords in MEDIUM_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def build_features(
    width_cm: float,
    height_cm: float,
    medium: str,
    artist_profile: dict | None = None,
    target_market: str = "gallery",
    manual_overrides: dict | None = None,
    *,
    is_saatchi_warm: bool = False,
    year_made: int | None = None,
) -> dict:
    """37개 피처를 생성하여 dict로 반환.

    artist_profile: DB에서 가져온 작가 프로필 (매칭 성공 시).
    manual_overrides: 요청에서 직접 입력한 값 (birth_year, total_works 등).

    v3.6 Phase 1 PR4: V_year_saatchi_warm cohort gating + year 3종 피처.
    is_saatchi_warm: caller (server) 가 결정한 cohort gate 결과.
        True = saatchi & warm artist 조건 충족, False = 그 외 (artsy / saatchi cold /
        unmatched).
    year_made: 제작년도. caller 가 manual override 또는 cache/fetch 결과로 결정.

    Activation rule (v3.5 step 2 §2.3):
        is_saatchi_warm and year_made not None and 1800 <= year_made <= 2030 → 활성
        그 외 → 옵션 B disable (year_made=0.0, has_year_made=0, work_age=0.0)

    Output contract (v3.5 step 2 §4 옵션 B 단일 contract):
        모든 builder output 은 finite 0 또는 valid value. NaN 없음.
        학습 fillna(0) 후 model-input parity 보장.
    """
    p = artist_profile or {}
    m = manual_overrides or {}

    # 크기 피처
    area_cm2 = width_cm * height_cm
    aspect_ratio = max(width_cm, height_cm) / max(min(width_cm, height_cm), 0.1)
    ho = area_to_ho(area_cm2)

    # 매체/지지체 — 추론 경로는 v3 모델 호환을 위해 구 분류기 유지.
    # 새 parse_artsy_medium은 학습 데이터 prep에서만 사용 (Codex review #7).
    # 모델 재학습 PR에서 전환 예정.
    support_type = classify_support(medium)
    medium_category = classify_medium(medium)
    support_factor = SUPPORT_FACTORS.get(support_type, 0.85)

    # 작가 피처 (manual override > DB profile > 기본값)
    # None 체크 (0은 유효한 값이므로 `is not None` 사용)
    def _pick(manual_key: str, profile_key: str, default=0):
        mv = m.get(manual_key)
        if mv is not None:
            return mv
        pv = p.get(profile_key)
        if pv is not None:
            return pv
        return default

    birth_year = _pick("artist_birth_year", "birth_year", None) or p.get("birth_year_from_source")
    total_works = _pick("artist_total_works", "total_works", 0)
    followers = _pick("followers", "followers", 0)
    solo = _pick("solo_count", "solo_count", 0)
    group = _pick("group_count", "group_count", 0)
    fair = p.get("fair_count", 0) or 0
    # career_stage v2 (continuous 0~8) — 기존 int(1~4) 대체. career_age는 학습/서빙
    # 드리프트 회피 위해 v2 formula에서 제거 (Codex 재리뷰 P1, 2026-04-27).
    career_stage = career_stage_v2_score(
        artist_birth_year=birth_year,
        solo_count=solo,
        group_count=group,
        fair_count=fair,
        ln_followers=math.log(followers + 1) if followers else 0.0,
    )
    for_sale_ratio = p.get("for_sale_ratio", 1.0) or 1.0
    profile_completeness = p.get("profile_completeness", 0) or 0

    has_birth_year = 1 if birth_year else 0

    # 갤러리 피처 — gallery_name 제거 (Codex 14차 P1: train/serve 드리프트)
    gallery_type = p.get("gallery_type", "Unknown")
    gallery_tier = p.get("gallery_tier", 4)
    source = p.get("source", "manual")

    # v3.6 Phase 1 PR4: V_year_saatchi_warm gating + 옵션 B disable
    if is_saatchi_warm and year_made is not None and 1800 <= year_made <= 2030:
        feat_year_made = float(year_made)
        feat_has_year_made = 1
        feat_work_age = float(2026 - year_made)
    else:
        # 옵션 B: 비대상 → 0/0/0 (학습 fillna(0) 후 model-input parity)
        feat_year_made = 0.0
        feat_has_year_made = 0
        feat_work_age = 0.0

    features = {
        # 크기 (9)
        "ho": ho,
        "ho_power": ho**0.74 if ho > 0 else 0.0,
        "ln_ho": math.log(ho + 1),
        "area_cm2": area_cm2,
        "ln_area": math.log(max(area_cm2, 1)),
        "aspect_ratio": aspect_ratio,
        "is_small": 1 if ho <= 3 else 0,
        "support_factor": support_factor,
        "ho_x_support": ho * support_factor,
        # 작품 (3) — work_age 제거 (서빙=0 드리프트, Codex 4차 P1)
        "is_unique": 1,
        "is_edition": 0,
        "has_depth": 0,
        # 작가 (6) — career_age 제거 (서빙=0 드리프트, Codex 4차 P1)
        "artist_birth_year": float(birth_year) if birth_year else float("nan"),
        "has_birth_year": has_birth_year,
        "career_stage": career_stage,
        "ln_followers": math.log(followers + 1),
        "artist_total_works": total_works,
        "for_sale_ratio": for_sale_ratio,
        # 가격 레벨 (2)
        "ho_price_level": 0.0,
        "medium_price_level": 0.0,
        # 프로필 (1)
        "profile_completeness": profile_completeness,
        # 갤러리 (5) — vintage_premium/freshness_discount 제거 (서빙=0 드리프트)
        "gallery_tier": gallery_tier,
        "gallery_city_count": 1,
        "has_seoul": 0,
        "has_international": 0,
        "is_krw": 1 if target_market == "gallery" else 0,
        # categorical (6) — gallery_name 제거 (Codex 14차 P1)
        "support_type": support_type,
        "medium_category": medium_category,
        "attribution_class": "Unique",
        "gallery_type": gallery_type,
        "price_currency": "KRW" if target_market == "gallery" else "USD",
        "source": source,
        # v3.6 Phase 1 PR4: V_year_saatchi_warm enrichment (3) — 옵션 B disable
        "year_made": feat_year_made,
        "has_year_made": feat_has_year_made,
        "work_age": feat_work_age,
    }

    return features
