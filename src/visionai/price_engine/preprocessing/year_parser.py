"""제작연도 파싱 모듈.

제작연도 문자열에서 4자리 연도를 추출하고 결측 플래그를 생성한다.

기획서 참조: 3.2.3
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class YearResult:
    """제작연도 파싱 결과."""

    year_created: int | None
    is_year_missing: bool


_PAT_YEAR = re.compile(r"(?:^|[^0-9])(\d{4})(?:[^0-9]|$)")


def parse_year(raw: str | float | None) -> YearResult:
    """제작연도 문자열에서 4자리 연도를 추출한다.

    Args:
        raw: 제작연도 원본. 예: "1937", "ca.1970", "2023년", NaN

    Returns:
        YearResult with year_created and is_year_missing.
    """
    if raw is None:
        return YearResult(year_created=None, is_year_missing=True)

    text = str(raw).strip()
    if text == "" or text.lower() == "nan":
        return YearResult(year_created=None, is_year_missing=True)

    m = _PAT_YEAR.search(text)
    if m:
        year = int(m.group(1))
        if 1000 <= year <= 2030:
            return YearResult(year_created=year, is_year_missing=False)

    return YearResult(year_created=None, is_year_missing=True)
