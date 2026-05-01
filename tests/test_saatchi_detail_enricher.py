"""Unit tests for saatchi_detail_enricher (v3.4-2 step 2).

Pure parser 함수 (`parse_saatchi_detail_html`) 의 분기 검증:
- primary HTML regex 매칭
- JSON fallback (camelCase / snake_case)
- unresolved (모든 매칭 실패)
- access denied → blocked
- short response 경고
- isSoldOut / isReserved / availability 추출
- price_zero_flag systematic branch (코덱스 P0)
- content_hash 안정성
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from saatchi_detail_enricher import parse_saatchi_detail_html  # noqa: E402


def _make_html(
    *,
    year_html: str | None = "2022",
    year_json_camel: str | None = None,
    year_json_snake: str | None = None,
    is_sold_out: str | None = "false",
    is_reserved: str | None = "false",
    availability: str | None = "http://schema.org/InStock",
    extra: str = "",
) -> str:
    """다양한 분기 fixture 생성."""
    parts = [
        "<html>",
        "<body>",
        '<div class="page">' * 400,  # padding to ensure raw_size > 5kb
    ]
    if year_html:
        parts.append(f'<h5>Year Created:</h5></div><div class="x"><p>{year_html}</p></div>')
    if year_json_camel:
        parts.append(f'"yearCreated":"{year_json_camel}"')
    if year_json_snake:
        parts.append(f'"year_created":"{year_json_snake}"')
    if is_sold_out is not None:
        parts.append(f'"isSoldOut":{is_sold_out}')
    if is_reserved is not None:
        parts.append(f'"isReserved":{is_reserved}')
    if availability:
        parts.append(f'"availability":"{availability}"')
    parts.append(extra)
    parts.append("</body></html>")
    return "".join(parts)


# --- year_created branch coverage ---


def test_primary_html_regex_match():
    html = _make_html(year_html="2022")
    r = parse_saatchi_detail_html(html, url="u")
    assert r.year_created == 2022
    assert r.extraction_source == "html_year_created"
    assert r.fetch_status == "ok"
    assert r.parse_warnings == []


def test_json_camel_fallback_when_html_missing():
    html = _make_html(year_html=None, year_json_camel="2018")
    r = parse_saatchi_detail_html(html)
    assert r.year_created == 2018
    assert r.extraction_source == "json_yearCreated"


def test_json_snake_fallback_when_html_and_camel_missing():
    html = _make_html(year_html=None, year_json_camel=None, year_json_snake="2009")
    r = parse_saatchi_detail_html(html)
    assert r.year_created == 2009
    assert r.extraction_source == "json_year_created"


def test_html_takes_priority_over_json_fallbacks():
    """primary html 이 있으면 JSON 우선순위 X (코덱스 P1: extraction_source 정확성)."""
    html = _make_html(year_html="2024", year_json_camel="2010", year_json_snake="2005")
    r = parse_saatchi_detail_html(html)
    assert r.year_created == 2024
    assert r.extraction_source == "html_year_created"


def test_unresolved_when_no_year_match():
    html = _make_html(year_html=None, year_json_camel=None, year_json_snake=None)
    r = parse_saatchi_detail_html(html)
    assert r.year_created is None
    assert r.extraction_source == "unresolved"
    assert "year_created_unresolved" in r.parse_warnings


# --- fetch_status branch coverage ---


def test_access_denied_returns_blocked():
    html = "<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY>..."
    r = parse_saatchi_detail_html(html)
    assert r.fetch_status == "blocked"
    assert r.year_created is None
    assert r.extraction_source == "unresolved"
    assert r.content_hash is None
    assert "access_denied" in r.parse_warnings


def test_short_response_warning():
    html = "tiny page"
    r = parse_saatchi_detail_html(html)
    assert r.fetch_status == "short_response"
    assert "short_response_under_5kb" in r.parse_warnings


# --- isSoldOut / isReserved / availability ---


def test_sold_out_true_extraction():
    html = _make_html(is_sold_out="true", is_reserved="false")
    r = parse_saatchi_detail_html(html)
    assert r.is_sold_out is True
    assert r.is_reserved is False


def test_availability_extraction():
    html = _make_html(availability="http://schema.org/OutOfStock")
    r = parse_saatchi_detail_html(html)
    assert r.availability == "http://schema.org/OutOfStock"


def test_availability_signal_missing_warning():
    html = _make_html(is_sold_out=None, availability=None)
    r = parse_saatchi_detail_html(html)
    assert r.is_sold_out is None
    assert r.availability is None
    assert "availability_signal_missing" in r.parse_warnings


# --- price_zero_flag (코덱스 P0 systematic branch) ---


def test_price_zero_flag_set_when_price_is_zero():
    html = _make_html()
    r = parse_saatchi_detail_html(html, price_krw=0)
    assert r.price_zero_flag is True


def test_price_zero_flag_false_for_normal_price():
    html = _make_html()
    r = parse_saatchi_detail_html(html, price_krw=1_000_000)
    assert r.price_zero_flag is False


def test_price_zero_flag_false_when_price_none():
    html = _make_html()
    r = parse_saatchi_detail_html(html, price_krw=None)
    assert r.price_zero_flag is False


def test_price_zero_with_missing_sold_out_emits_warning():
    """코덱스 P0: price=0 & isSoldOut missing 조합 별도 추적."""
    html = _make_html(is_sold_out=None)
    r = parse_saatchi_detail_html(html, price_krw=0)
    assert r.price_zero_flag is True
    assert "price_zero_isSoldOut_missing" in r.parse_warnings


def test_price_zero_with_sold_out_present_no_warning():
    """price=0 라도 isSoldOut 노출되면 warning X."""
    html = _make_html(is_sold_out="false")
    r = parse_saatchi_detail_html(html, price_krw=0)
    assert r.price_zero_flag is True
    assert "price_zero_isSoldOut_missing" not in r.parse_warnings


# --- content_hash drift detection ---


def test_content_hash_deterministic_for_same_html():
    html = _make_html()
    r1 = parse_saatchi_detail_html(html)
    r2 = parse_saatchi_detail_html(html)
    assert r1.content_hash == r2.content_hash
    assert len(r1.content_hash) == 16


def test_content_hash_changes_for_different_html():
    r1 = parse_saatchi_detail_html(_make_html(year_html="2020"))
    r2 = parse_saatchi_detail_html(_make_html(year_html="2021"))
    assert r1.content_hash != r2.content_hash


# --- to_dict serialization ---


def test_to_dict_returns_jsonable_fields():
    html = _make_html(year_html="2022")
    r = parse_saatchi_detail_html(html, url="https://example.com/x")
    d = r.to_dict()
    assert d["url"] == "https://example.com/x"
    assert d["year_created"] == 2022
    assert d["extraction_source"] == "html_year_created"
    assert isinstance(d["parse_warnings"], list)
