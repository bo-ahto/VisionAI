"""비미술 항목 클렌징 모듈.

K-Auction 데이터에서 미술 작품이 아닌 항목(주류, 명품, 보석, 이벤트/상품권,
도자공예, 목공예)을 식별한다. classify_non_art()로 플래그를 생성하고,
cleanse_dataframe()으로 제거 또는 플래그 추가가 가능하다.

현재 파이프라인에서는 제거 방식 사용 (비미술 항목 ~2.9% 제거).
분류 기준: 재료 유무 × 제목 키워드 조합.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CleansingResult:
    """비미술 분류 결과."""

    is_non_art: bool
    category: str  # art / event / alcohol / luxury / jewelry / craft_ceramic / craft_wood
    confidence: float  # 0.0 ~ 1.0


# ─── 제목 기반 패턴 (재료 없음 전제) ───

_PAT_EVENT = re.compile(
    r"항공권|숙박권|식사권|이용권|상품권|바우처|voucher|멘토링.*식사|골프용품|"
    r"와의\s*(저녁)?식사|광고\s*바우처|렌탈권|수제화.*상품권|임플란트",
    re.IGNORECASE,
)

_PAT_ALCOHOL = re.compile(
    r"위스키\s*(테이스팅|클래스)|테이스팅\s*클래스|소믈리에.*클래스|와인\s*클래스",
    re.IGNORECASE,
)

_PAT_LUXURY = re.compile(
    r"Birkin|Rolex|루이비통.*핸드백",
    re.IGNORECASE,
)

_PAT_LUXURY_BAG = re.compile(r"가방$")

_PAT_JEWELRY_TITLE = re.compile(
    r"다이아몬드|사파이어|루비|에메랄드|탄자나이트",
    re.IGNORECASE,
)

# ─── 재료 기반 패턴 ───

_PAT_JEWELRY_MAT = re.compile(
    r"18K|14K|플래티넘|백금.*다이아|골드.*다이아|다이아.*골드",
    re.IGNORECASE,
)

_PAT_CRAFT_CERAMIC = re.compile(
    r"^도자기|^자기$|^도자$|분청|나전|칠기|옹기",
)

_WOOD_NAMES = (
    r"소나무|오동나무|참나무|느티나무|괴목|먹감나무|은행나무|"
    r"참죽나무|벚나무|흑단|화류목|박달나무|배나무|감나무"
)
_PAT_CRAFT_WOOD = re.compile(
    rf"^({_WOOD_NAMES})(\s*,\s*({_WOOD_NAMES}))*$",
)


def classify_non_art(title: str | None, material: str | None) -> CleansingResult:
    """제목과 재료로 비미술 항목을 분류한다.

    Args:
        title: 작품 제목.
        material: 재료 문자열.

    Returns:
        CleansingResult with category and confidence.
    """
    t = str(title or "").strip()
    m = str(material or "").strip()
    # pandas NaN → str(nan) = "nan" 처리
    if m.lower() == "nan":
        m = ""
    no_material = m == ""

    # 1. 이벤트/상품권: 재료 없음 + 이벤트 키워드
    if no_material and _PAT_EVENT.search(t):
        return CleansingResult(is_non_art=True, category="event", confidence=1.0)

    # 2. 주류/테이스팅: 재료 없음 + 주류 키워드
    if no_material and _PAT_ALCOHOL.search(t):
        return CleansingResult(is_non_art=True, category="alcohol", confidence=1.0)

    # 3. 명품: Birkin/Rolex (재료 무관) 또는 재료 없음 + "가방"
    if _PAT_LUXURY.search(t):
        return CleansingResult(is_non_art=True, category="luxury", confidence=1.0)
    if no_material and _PAT_LUXURY_BAG.search(t):
        return CleansingResult(is_non_art=True, category="luxury", confidence=1.0)

    # 4. 보석: 재료에 금/다이아 또는 재료 없음 + 보석 키워드
    if _PAT_JEWELRY_MAT.search(m):
        return CleansingResult(is_non_art=True, category="jewelry", confidence=0.95)
    if no_material and _PAT_JEWELRY_TITLE.search(t):
        return CleansingResult(is_non_art=True, category="jewelry", confidence=0.95)

    # 5. 도자/공예: 재료가 도자기 계열
    if m and _PAT_CRAFT_CERAMIC.search(m):
        return CleansingResult(is_non_art=True, category="craft_ceramic", confidence=0.9)

    # 6. 목공예: 재료가 순수 목재명만
    if m and _PAT_CRAFT_WOOD.match(m):
        return CleansingResult(is_non_art=True, category="craft_wood", confidence=0.85)

    # 미술 작품
    return CleansingResult(is_non_art=False, category="art", confidence=0.0)


def cleanse_dataframe(
    df: pd.DataFrame,
    title_col: str = "제목",
    material_col: str = "재료",
    min_confidence: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """DataFrame에서 비미술 항목을 제거한다.

    Args:
        df: 원본 DataFrame.
        title_col: 제목 컬럼명.
        material_col: 재료 컬럼명.
        min_confidence: 이 값 이상의 confidence를 가진 비미술 항목만 제거.

    Returns:
        (클렌징된 DataFrame, 제거된 DataFrame)
    """
    results = df.apply(
        lambda row: classify_non_art(
            str(row.get(title_col, "")),
            str(row.get(material_col, "")),
        ),
        axis=1,
    )

    is_non_art = pd.Series(
        [r.is_non_art and r.confidence >= min_confidence for r in results],
        index=df.index,
    )

    removed = df[is_non_art].copy()
    removed["_non_art_category"] = [
        r.category for r in results[is_non_art.values]
    ]
    removed["_non_art_confidence"] = [
        r.confidence for r in results[is_non_art.values]
    ]

    cleaned = df[~is_non_art].copy()

    # 카테고리별 로그
    if len(removed) > 0:
        cats = removed["_non_art_category"].value_counts()
        cat_str = ", ".join(f"{k}={v}" for k, v in cats.items())
        logger.info(
            "Data cleansing: removed %d non-art items (%.1f%%): %s",
            len(removed),
            len(removed) / len(df) * 100,
            cat_str,
        )
    else:
        logger.info("Data cleansing: no non-art items found")

    return cleaned, removed
