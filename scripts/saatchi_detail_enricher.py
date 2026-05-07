"""Saatchi Art detail page enricher (v3.4-2 step 2).

배경 (코덱스 v3.4-2 step 2 설계):
- v3.4-2 step 1 검증: 26 stratified sample 모두 Year Created 100% 검출, anti-bot 0%.
- 본 모듈: detail page HTML 에서 year_created / isSoldOut / isReserved / availability
  추출 + drift 감지용 extraction_source 라벨 + price_zero_flag systematic branch 추적.

설계:
- pure parser (`parse_saatchi_detail_html`) — 순수 함수, 단위 테스트 가능
- fetch + parse wrapper (`fetch_and_parse_saatchi_detail`) — network + 변환
- 분리 로깅: fetch_status (ok/blocked/timeout/5xx/network_error) + parse_warnings list
- raw HTML 의 sha256 prefix (16자) 보존 — drift 추적

Usage:
    from scripts.saatchi_detail_enricher import (
        fetch_and_parse_saatchi_detail,
        parse_saatchi_detail_html,
        EnrichmentResult,
    )

    result = fetch_and_parse_saatchi_detail(
        "https://www.saatchiart.com/art/Painting-X/.../view",
        price_krw=1_000_000,
    )
    print(result.year_created, result.extraction_source)

Notes:
- 이 모듈은 production code 아님 (data enrichment / research). pure 함수 위주로
  단위 테스트만 강제. fetch wrapper 는 network 의존이라 smoke verification 만.
"""

from __future__ import annotations

import hashlib
import logging
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

# 코덱스 v3.4-2 step 1 검증: primary regex 26/26 일치
YEAR_HTML_PATTERN = re.compile(
    r"<h5>Year Created:</h5></div><div[^>]*><p>(\d{4})</p>",
    re.IGNORECASE,
)
# JSON fallback (drift 대응용)
YEAR_JSON_CAMEL_PATTERN = re.compile(r'"yearCreated"\s*:\s*"?(\d{4})"?')
YEAR_JSON_SNAKE_PATTERN = re.compile(r'"year_created"\s*:\s*"?(\d{4})"?')

IS_SOLD_OUT_PATTERN = re.compile(r'"isSoldOut"\s*:\s*(true|false)')
IS_RESERVED_PATTERN = re.compile(r'"isReserved"\s*:\s*(true|false)')
AVAILABILITY_PATTERN = re.compile(r'"availability"\s*:\s*"([^"]+)"')

# Saatchi access denied page (UA 차단 감지)
ACCESS_DENIED_MARKER = "<TITLE>Access Denied</TITLE>"

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_0) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)
DEFAULT_TIMEOUT = 20

ExtractionSource = Literal[
    "html_year_created",
    "json_yearCreated",
    "json_year_created",
    "unresolved",
]
FetchStatus = Literal["ok", "blocked", "timeout", "5xx", "network_error", "short_response"]


@dataclass
class EnrichmentResult:
    """Enrichment 결과 + diagnostics."""

    url: str
    fetch_status: FetchStatus
    raw_size: int
    content_hash: str | None
    year_created: int | None
    extraction_source: ExtractionSource
    is_sold_out: bool | None
    is_reserved: bool | None
    availability: str | None
    price_zero_flag: bool
    parse_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _content_hash(html: str) -> str:
    """drift 감지용 sha256 prefix (16자)."""
    return hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()[:16]


def _parse_year(html: str) -> tuple[int | None, ExtractionSource]:
    """Year Created 추출 — primary HTML → JSON camelCase → JSON snake_case."""
    m = YEAR_HTML_PATTERN.search(html)
    if m:
        return int(m.group(1)), "html_year_created"
    m = YEAR_JSON_CAMEL_PATTERN.search(html)
    if m:
        return int(m.group(1)), "json_yearCreated"
    m = YEAR_JSON_SNAKE_PATTERN.search(html)
    if m:
        return int(m.group(1)), "json_year_created"
    return None, "unresolved"


def _parse_bool_field(html: str, pattern: re.Pattern) -> bool | None:
    m = pattern.search(html)
    if not m:
        return None
    return m.group(1) == "true"


def parse_saatchi_detail_html(
    html: str,
    *,
    url: str = "",
    price_krw: float | int | None = None,
) -> EnrichmentResult:
    """Pure parser — HTML 문자열 → EnrichmentResult.

    Args:
        html: Saatchi detail page raw HTML
        url: 원본 URL (출력 trace 용)
        price_krw: 작품 가격 (price=0 systematic branch 추적용 — 코덱스 P0)

    Returns:
        EnrichmentResult with diagnostics (fetch_status 는 'ok' 또는 'short_response' /
        'blocked' — caller 가 fetch 단계에서 status 결정).
    """
    warnings: list[str] = []
    raw_size = len(html)

    # blocked 감지 (UA 차단)
    if ACCESS_DENIED_MARKER in html:
        return EnrichmentResult(
            url=url,
            fetch_status="blocked",
            raw_size=raw_size,
            content_hash=None,
            year_created=None,
            extraction_source="unresolved",
            is_sold_out=None,
            is_reserved=None,
            availability=None,
            price_zero_flag=bool(price_krw is not None and price_krw == 0),
            parse_warnings=["access_denied"],
        )

    # 짧은 응답 (anti-bot soft block / partial render)
    if raw_size < 5000:
        warnings.append("short_response_under_5kb")

    year, ext_src = _parse_year(html)
    if year is None:
        warnings.append("year_created_unresolved")

    is_sold_out = _parse_bool_field(html, IS_SOLD_OUT_PATTERN)
    is_reserved = _parse_bool_field(html, IS_RESERVED_PATTERN)
    avail_match = AVAILABILITY_PATTERN.search(html)
    availability = avail_match.group(1) if avail_match else None

    if is_sold_out is None and availability is None:
        warnings.append("availability_signal_missing")

    price_zero_flag = bool(price_krw is not None and price_krw == 0)
    if price_zero_flag and is_sold_out is None:
        warnings.append("price_zero_isSoldOut_missing")

    fetch_status: FetchStatus = "short_response" if raw_size < 5000 else "ok"

    return EnrichmentResult(
        url=url,
        fetch_status=fetch_status,
        raw_size=raw_size,
        content_hash=_content_hash(html),
        year_created=year,
        extraction_source=ext_src,
        is_sold_out=is_sold_out,
        is_reserved=is_reserved,
        availability=availability,
        price_zero_flag=price_zero_flag,
        parse_warnings=warnings,
    )


def fetch_saatchi_html(
    url: str,
    *,
    user_agent: str = DEFAULT_UA,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str, FetchStatus]:
    """URL 에서 raw HTML fetch + status 판정.

    Returns:
        (html, fetch_status) — html 은 fetch 실패 시 빈 문자열.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html_bytes = resp.read()
            html = html_bytes.decode("utf-8", errors="replace")
            return html, "ok"
    except urllib.error.HTTPError as e:
        if 500 <= e.code < 600:
            return "", "5xx"
        if e.code in (401, 403, 429):
            return "", "blocked"
        return "", "network_error"
    except TimeoutError:
        return "", "timeout"
    except urllib.error.URLError as e:
        # URLError reason 이 timeout 이면 timeout 으로 분류, 그 외는 network_error
        # (DNS/connection refused 등 — 코덱스 P1 분리 권고)
        reason = getattr(e, "reason", None)
        if isinstance(reason, TimeoutError) or (
            reason is not None and "timed out" in str(reason).lower()
        ):
            return "", "timeout"
        return "", "network_error"
    except Exception as e:
        logger.warning("fetch failed for %s: %s", url, e)
        return "", "network_error"


def fetch_and_parse_saatchi_detail(
    url: str,
    *,
    price_krw: float | int | None = None,
    user_agent: str = DEFAULT_UA,
    timeout: float = DEFAULT_TIMEOUT,
) -> EnrichmentResult:
    """Fetch + parse wrapper. fetch 실패 시 빈 result 반환."""
    html, status = fetch_saatchi_html(url, user_agent=user_agent, timeout=timeout)
    if status != "ok":
        return EnrichmentResult(
            url=url,
            fetch_status=status,
            raw_size=len(html),
            content_hash=None,
            year_created=None,
            extraction_source="unresolved",
            is_sold_out=None,
            is_reserved=None,
            availability=None,
            price_zero_flag=bool(price_krw is not None and price_krw == 0),
            parse_warnings=[f"fetch_{status}"],
        )
    return parse_saatchi_detail_html(html, url=url, price_krw=price_krw)
