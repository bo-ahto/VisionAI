"""제목 NLP 피처 추출.

작품 제목에서 주제, 시리즈, 키워드 등을 추출하여 피처로 활용.
이미지 없이 텍스트만으로 작품의 내용적 특성을 반영.

Phase 4 Tier 3 — 제목 NLP (KoBERT 대안: 규칙 기반 + TF-IDF).
"""
from __future__ import annotations

import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

# 주제 카테고리 키워드 매핑
# 주제 카테고리 키워드 — 2음절 이상만 사용하여 부분문자열 충돌 방지
_SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "landscape": ["풍경", "landscape", "mountain", "river", "계곡", "설경",
                   "해변", "호수", "lake", "forest", "산수", "山水"],
    "figure": ["인물", "여인", "소녀", "portrait", "figure", "woman", "nude",
               "미인도", "자화상", "self-portrait", "인체", "무희"],
    "flower": ["꽃", "flower", "rose", "장미", "매화", "목련", "연꽃", "lotus",
               "국화", "모란", "진달래", "난초", "orchid"],
    "animal": ["물고기", "horse", "bird", "고양이", "호랑이", "tiger", "사슴",
               "deer", "crane"],
    "abstract": ["추상", "abstract", "composition", "구성", "untitled", "무제",
                  "dialogue", "relatum", "ecriture", "from line", "from point"],
    "stilllife": ["정물", "still life", "과일", "fruit", "꽃병", "vase"],
    "calligraphy": ["서예", "calligraphy", "문자도"],
    "religious": ["불상", "佛像", "buddha", "보살", "관음", "십자가", "cross"],
}

# 시리즈 패턴 (정규식)
# 시리즈 패턴 — 실제 시리즈명만 (장르/화제어 제외)
_SERIES_PATTERNS: list[tuple[str, str]] = [
    (r"ecriture", "ecriture"),
    (r"from\s+(?:line|point|wind|port)", "from_series"),
    (r"dialogue", "dialogue"),
    (r"relatum", "relatum"),
    (r"correspond", "correspondence"),
    (r"\b[IVX]{2,}\b", "roman_numeral"),  # II, III, IV 등
    (r"\(\d+\)", "paren_number"),  # (3), (12) 등
    (r"edition\s+\d", "edition"),  # Edition 2 등
]


def extract_title_features(titles: pd.Series) -> pd.DataFrame:
    """제목 시리즈에서 NLP 피처 추출.

    Returns:
        DataFrame with columns:
        - title_length: 제목 글자 수
        - title_has_year: 제목에 연도 포함
        - title_has_number: 제목에 번호 포함 (시리즈)
        - title_is_untitled: 무제 여부
        - title_is_korean: 한글 제목
        - title_is_english: 영문 제목
        - title_has_hanja: 한자 포함
        - title_subject: 주제 카테고리 (가장 많이 매칭된 것)
        - title_is_series: 시리즈 작품 여부
    """
    n = len(titles)
    result = pd.DataFrame(index=titles.index)

    # 기본 텍스트 통계
    titles_str = titles.fillna("").astype(str)
    result["title_length"] = titles_str.str.len()
    result["title_has_year"] = titles_str.str.contains(
        r"\b(?:19|20)\d{2}\b", regex=True, na=False
    )
    result["title_has_number"] = titles_str.str.contains(
        r"(?:no\.?\s*\d|#\d|\d{2,}\-\d)", regex=True, case=False, na=False
    )
    result["title_is_untitled"] = titles_str.str.contains(
        r"무제|untitled", regex=True, case=False, na=False
    )

    # 언어 감지
    result["title_is_korean"] = titles_str.apply(
        lambda t: bool(re.search(r"[가-힣]", t))
    )
    result["title_is_english"] = titles_str.apply(
        lambda t: bool(re.search(r"[a-zA-Z]{3,}", t))
    )
    result["title_has_hanja"] = titles_str.apply(
        lambda t: bool(re.search(r"[\u4e00-\u9fff]", t))
    )

    # 주제 카테고리 — 키워드 매칭 수 기반 (0/1이 아닌 실제 count)
    subject_scores: dict[str, pd.Series] = {}
    for subject, keywords in _SUBJECT_KEYWORDS.items():
        count = pd.Series(0, index=titles.index)
        for kw in keywords:
            count += titles_str.str.contains(
                re.escape(kw), regex=True, case=False, na=False
            ).astype(int)
        subject_scores[subject] = count

    subject_df = pd.DataFrame(subject_scores, index=titles.index)
    result["title_subject"] = subject_df.idxmax(axis=1)
    result.loc[subject_df.sum(axis=1) == 0, "title_subject"] = "other"

    # 시리즈 감지
    is_series = pd.Series(False, index=titles.index)
    for pattern, _ in _SERIES_PATTERNS:
        is_series = is_series | titles_str.str.contains(
            pattern, regex=True, case=False, na=False
        )
    result["title_is_series"] = is_series | result["title_has_number"]

    logger.info(
        "Title NLP: %d titles, untitled=%.1f%%, korean=%.1f%%, series=%.1f%%",
        n,
        result["title_is_untitled"].mean() * 100,
        result["title_is_korean"].mean() * 100,
        result["title_is_series"].mean() * 100,
    )

    return result
