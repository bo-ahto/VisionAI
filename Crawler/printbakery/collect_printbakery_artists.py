#!/usr/bin/env python3
"""
Print Bakery 아티스트 수집 스크립트.

수집 대상:
- 아티스트 목록: https://printbakery.com/api/artist-list.html?cate_no=515
- 아티스트 상세: https://printbakery.com/artist/detail.html?product_no={artist_product_no}

수집 원칙:
- 원본 HTML은 raw_html/에 저장한다.
- 이미 받은 HTML은 기본적으로 재사용한다.
- 원천 ID는 Print Bakery 내부 아티스트 상세 product_no로 저장한다.
- 원천 ID를 운영 공통 artist_key로 바로 쓰지 않는다.
- 상세 meta description, og description, JSON-LD brand name처럼 페이지에 있는 정보를 원문 그대로 보존한다.
- 생몰연도나 출생 지역처럼 문장 안에 섞인 값은 후보값으로만 추출한다.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


BASE_URL = "https://printbakery.com"
ARTIST_LIST_URL = f"{BASE_URL}/api/artist-list.html?cate_no=515"
ARTIST_DETAIL_URL = f"{BASE_URL}/artist/detail.html?product_no={{artist_product_no}}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) PrintBakeryArtistCollector/1.0"

PACKAGE_DIR = Path(__file__).resolve().parent
LIST_HTML_DIR = PACKAGE_DIR / "raw_html" / "list"
DETAIL_HTML_DIR = PACKAGE_DIR / "raw_html" / "detail"
OUTPUT_DIR = PACKAGE_DIR / "outputs"


@dataclass
class FetchConfig:
    delay_sec: float
    refresh: bool
    timeout: int = 30


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).replace("\xa0", " ").split())
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def absolute_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urllib.parse.urljoin(BASE_URL, url)


def fetch_url(url: str, cache_path: Path, cfg: FetchConfig, referer: str = BASE_URL) -> str:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not cfg.refresh:
        return cache_path.read_text(encoding="utf-8", errors="replace")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": referer,
        },
    )
    with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    cache_path.write_text(html, encoding="utf-8")
    if cfg.delay_sec > 0:
        time.sleep(cfg.delay_sec)
    return html


def parse_artist_list(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for li in soup.select("#artist-list li[data-product_no], li[data-product_no]"):
        artist_product_no = clean_text(li.get("data-product_no"))
        if not artist_product_no or artist_product_no in seen:
            continue
        seen.add(artist_product_no)

        han = clean_text(li.select_one(".han").get_text(" ", strip=True) if li.select_one(".han") else "")
        eng = clean_text(li.select_one(".eng").get_text(" ", strip=True) if li.select_one(".eng") else "")
        image = clean_text(li.select_one(".image").get_text(" ", strip=True) if li.select_one(".image") else "")
        link = clean_text(li.select_one(".link").get_text(" ", strip=True) if li.select_one(".link") else "")

        # 한글/영문 색인 구분은 프론트에서 쓰는 값이지만, 매칭/검수 보조값으로 보존한다.
        index_flags: list[str] = []
        if han:
            index_flags.append(han[0])
        if eng:
            index_flags.append(eng[0].upper())

        rows.append(
            {
                "source": "printbakery",
                "artist_product_no": artist_product_no,
                "artist_name_ko": han,
                "artist_name_en": eng,
                "artist_image": absolute_url(image),
                "artist_detail_url": absolute_url(link or f"/artist/detail.html?product_no={artist_product_no}"),
                "index_flag_candidate": ",".join(index_flags),
                "is_exclusive_candidate": "unknown",
            }
        )
    return rows


def parse_json_ld_brand(soup: BeautifulSoup) -> tuple[str, str]:
    brand_name = ""
    raw_json = ""
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = script.string or script.get_text("", strip=False)
        if not txt:
            continue
        raw_json = txt
        try:
            obj = json.loads(txt)
        except json.JSONDecodeError:
            continue
        brand = obj.get("brand") if isinstance(obj, dict) else None
        if isinstance(brand, dict):
            brand_name = clean_text(brand.get("name"))
            if brand_name:
                break
    return brand_name, raw_json


def parse_life_span(text: str) -> tuple[int | None, int | None, str]:
    text = clean_text(text)
    # 예: b.1931 - 2023, 예천...
    m = re.search(r"\bb\.\s*(\d{4})(?:\s*[-~]\s*(\d{4}))?", text, flags=re.I)
    if not m:
        return None, None, ""
    birth_year = int(m.group(1))
    death_year = int(m.group(2)) if m.group(2) else None
    after = clean_text(text[m.end() :].lstrip(" ,，"))
    place = ""
    if after:
        place = clean_text(re.split(r"[.。]|는|은", after, maxsplit=1)[0])
    return birth_year, death_year, place


def parse_artist_detail(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    meta_description = ""
    meta_keywords = ""
    og_title = ""
    og_description = ""
    og_image = ""
    for meta in soup.find_all("meta"):
        name = clean_text(meta.get("name", ""))
        prop = clean_text(meta.get("property", ""))
        content = clean_text(meta.get("content", ""))
        if name == "description":
            meta_description = content
        elif name == "keywords":
            meta_keywords = content
        elif prop == "og:title":
            og_title = content
        elif prop == "og:description":
            og_description = content
        elif prop == "og:image":
            og_image = absolute_url(content)

    title = clean_text(soup.find("title").get_text(" ", strip=True) if soup.find("title") else "")
    brand_name, json_ld_raw = parse_json_ld_brand(soup)
    birth_year, death_year, birth_place = parse_life_span(meta_description or og_description)

    # 상세 페이지 본문은 스킨 구조가 바뀔 수 있어 후보 텍스트로 넓게 보존한다.
    body_text = ""
    for selector in [".detail-container", ".artist-detail", ".xans-product-detail", "#contents"]:
        node = soup.select_one(selector)
        if node:
            body_text = clean_text(node.get_text(" ", strip=True))
            break

    return {
        "artist_page_title": title,
        "artist_meta_description": meta_description,
        "artist_meta_keywords": meta_keywords,
        "artist_og_title": og_title,
        "artist_og_description": og_description,
        "artist_og_image": og_image,
        "artist_brand_name": brand_name,
        "artist_json_ld_raw": json_ld_raw,
        "birth_year_candidate": birth_year,
        "death_year_candidate": death_year,
        "birth_place_candidate": birth_place,
        "artist_body_text_candidate": body_text,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="기존 캐시를 무시하고 다시 받는다.")
    parser.add_argument("--delay-sec", type=float, default=0.4, help="상세 요청 간 대기 시간.")
    parser.add_argument("--max-artists", type=int, default=None, help="테스트용 최대 작가 수.")
    args = parser.parse_args()

    cfg = FetchConfig(delay_sec=args.delay_sec, refresh=args.refresh)
    list_html = fetch_url(ARTIST_LIST_URL, LIST_HTML_DIR / "artist_list_cate_515.html", cfg, referer=f"{BASE_URL}/artist/list.html")
    list_rows = parse_artist_list(list_html)
    if args.max_artists:
        list_rows = list_rows[: args.max_artists]

    output_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(list_rows, start=1):
        artist_product_no = str(row["artist_product_no"])
        detail_url = ARTIST_DETAIL_URL.format(artist_product_no=artist_product_no)
        cache_path = DETAIL_HTML_DIR / f"artist_{artist_product_no}.html"
        try:
            html = fetch_url(detail_url, cache_path, cfg, referer=f"{BASE_URL}/artist/list.html")
            detail = parse_artist_detail(html)
            out = {
                **row,
                "artist_detail_url": detail_url,
                **detail,
                "detail_fetch_status": "ok",
            }
        except Exception as exc:  # noqa: BLE001 - 수집 실패 row도 결과에 남긴다.
            out = {
                **row,
                "artist_detail_url": detail_url,
                "detail_fetch_status": "failed",
                "detail_error": repr(exc),
            }
        output_rows.append(out)
        if idx % 50 == 0 or idx == len(list_rows):
            print(f"detail {idx}/{len(list_rows)}")

    write_csv(OUTPUT_DIR / "printbakery_artists_detail.csv", output_rows)
    summary = {
        "source": "printbakery",
        "list_url": ARTIST_LIST_URL,
        "rows": len(output_rows),
        "detail_ok": sum(1 for r in output_rows if r.get("detail_fetch_status") == "ok"),
        "with_ko_name": sum(1 for r in output_rows if r.get("artist_name_ko")),
        "with_en_name": sum(1 for r in output_rows if r.get("artist_name_en")),
        "with_meta_description": sum(1 for r in output_rows if r.get("artist_meta_description")),
        "with_birth_year_candidate": sum(1 for r in output_rows if r.get("birth_year_candidate")),
    }
    (OUTPUT_DIR / "printbakery_artists_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
