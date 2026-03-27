"""재료 문자열 파싱 모듈.

2,154개 고유 재료 문자열을 10종 매체 + 7종 지지체로 정규화한다.

기획서 참조: 3.2.2
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MediumResult:
    """재료 파싱 결과."""

    medium_category: str
    support_category: str


# 매체 분류 규칙 (우선순위 순)
_MEDIUM_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"유채|오일|oil", re.IGNORECASE), "유화"),
    (re.compile(r"수묵|먹|ink", re.IGNORECASE), "수묵"),
    (re.compile(r"사진|c-print|digital|피그먼트|젤라틴", re.IGNORECASE), "사진/디지털"),
    (re.compile(r"석판화|실크스크린|print|판화|리소|에칭|목판|동판|오프셋", re.IGNORECASE), "판화"),
    (re.compile(r"아크릴|acrylic", re.IGNORECASE), "아크릴"),
    (re.compile(r"혼합|미디어|mixed", re.IGNORECASE), "혼합재료"),
    (re.compile(r"채색|담채", re.IGNORECASE), "채색"),
    (re.compile(r"bronze|도자|ceramic|테라코타|stainless|조각|스테인", re.IGNORECASE), "조각/공예"),
]

# 지지체 분류 규칙
_SUPPORT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"캔버스|canvas", re.IGNORECASE), "캔버스"),
    (re.compile(r"종이|paper|지(?!름)", re.IGNORECASE), "종이"),
    (re.compile(r"비단|silk|견", re.IGNORECASE), "비단"),
    (re.compile(r"목재|wood|나무|목판", re.IGNORECASE), "목재"),
    (re.compile(r"패널|panel|보드", re.IGNORECASE), "패널"),
]


def parse_medium(raw: str | None) -> MediumResult:
    """재료 문자열을 매체/지지체로 분류한다.

    Args:
        raw: 원본 재료 문자열. 예: "캔버스에 유채", "Bronze, Aluminium"

    Returns:
        MediumResult with medium_category and support_category.
    """
    if not raw or not isinstance(raw, str) or raw.strip() == "":
        return MediumResult(medium_category="unknown", support_category="unknown")

    text = raw.strip()

    # 매체 분류
    medium = "기타"
    for pattern, category in _MEDIUM_RULES:
        if pattern.search(text):
            medium = category
            break

    # 지지체 분류
    support = "기타"
    for pattern, category in _SUPPORT_RULES:
        if pattern.search(text):
            support = category
            break

    return MediumResult(medium_category=medium, support_category=support)
