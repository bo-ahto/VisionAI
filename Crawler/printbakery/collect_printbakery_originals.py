#!/usr/bin/env python3
"""
Print Bakery 오리지널 평면 카테고리 수집 스크립트.

수집 대상:
- https://printbakery.com/product/list.html?cate_no=367

수집 방식:
- 목록 페이지에서 product_no, 작가명, 작품명, 표시 가격, 이미지, 상세 URL을 수집한다.
- 상세 페이지에서 artwork, artist, price, maker, size, method, material, edition,
  code, 상품간략설명, og 이미지, meta description을 추가 수집한다.
- HTML 원본을 raw_html/ 아래에 캐시하므로 중간에 중단되어도 재실행하면 이어서 진행된다.

주의:
- robots.txt에서 /product/list.html, /product/detail.html은 금지 경로가 아니다.
- 기본 요청 간격은 1초다. --delay-sec로 조정할 수 있다.
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
LIST_URL = f"{BASE_URL}/product/list.html?cate_no=367&page={{page}}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) PrintBakeryCollector/1.0"

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


def fetch_url(url: str, cache_path: Path, cfg: FetchConfig) -> str:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not cfg.refresh:
        return cache_path.read_text(encoding="utf-8", errors="replace")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    cache_path.write_text(html, encoding="utf-8")
    if cfg.delay_sec > 0:
        time.sleep(cfg.delay_sec)
    return html


def parse_price_krw(text: str) -> int | None:
    text = clean_text(text)
    if not text:
        return None
    if "문의" in text or "별도" in text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def parse_size_cm(size: str) -> tuple[float | None, float | None, float | None]:
    nums = re.findall(r"\d+(?:\.\d+)?", clean_text(size))
    vals = [float(n) for n in nums[:3]]
    while len(vals) < 3:
        vals.append(None)
    return vals[0], vals[1], vals[2]


def parse_detail_design(soup: BeautifulSoup) -> dict[str, str]:
    """
    Cafe24 상품 상세의 숨김 상세 스펙 영역을 key/value로 읽는다.

    예:
    artwork DRAWN
    artist 정영서 Jung Young Seo
    price 850,000원
    maker 정영서
    size 40.9x24.2cm
    method oil on canvas
    material 2025
    edition Original
    code P0000ZOJ
    """
    out: dict[str, str] = {}
    area = soup.select_one(".xans-product-detaildesign")
    if not area:
        return out

    rows = area.select("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = clean_text(cells[0].get_text(" ", strip=True)).lower()
            val = clean_text(cells[1].get_text(" ", strip=True))
            if key:
                out[key] = val

    # 일부 Cafe24 스킨은 li/span 구조로 나온다.
    if not out:
        text = area.get_text(" ", strip=True)
        keys = ["artwork", "artist", "price", "maker", "size", "method", "material", "edition", "code", "상품간략설명"]
        pattern = "|".join(re.escape(k) for k in keys)
        matches = list(re.finditer(rf"({pattern})\s+", text, flags=re.I))
        for i, match in enumerate(matches):
            key = match.group(1).lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            out[key] = clean_text(text[start:end])
    return out


def parse_list_page(html: str, page: int) -> tuple[list[dict[str, Any]], int | None]:
    soup = BeautifulSoup(html, "html.parser")
    total_count = None
    for s in soup.stripped_strings:
        m = re.search(r"총\s*([\d,]+)\s*개", s)
        if m:
            total_count = int(m.group(1).replace(",", ""))
            break

    rows: list[dict[str, Any]] = []
    for item in soup.select("li.product-item[data-product-no]"):
        product_no = clean_text(item.get("data-product-no"))
        link = item.select_one('a[href*="/product/detail.html"]')
        img = item.select_one("img")
        artist = clean_text(item.select_one("p.artist").get_text(" ", strip=True) if item.select_one("p.artist") else "")
        title = clean_text(item.select_one("p.name").get_text(" ", strip=True) if item.select_one("p.name") else "")
        price_text = clean_text(item.select_one(".price-info .price.list").get_text(" ", strip=True) if item.select_one(".price-info .price.list") else "")
        if not price_text:
            price_text = clean_text(item.select_one(".price-info").get_text(" ", strip=True) if item.select_one(".price-info") else "")

        rows.append(
            {
                "source": "printbakery",
                "cate_no": "367",
                "list_page": page,
                "product_no": product_no,
                "artist_list": artist,
                "title_list": title,
                "price_text_list": price_text,
                "price_krw_list": parse_price_krw(price_text),
                "detail_url": absolute_url(link.get("href", "") if link else ""),
                "image_url_list": absolute_url(img.get("src", "") if img else ""),
                "image_alt_list": clean_text(img.get("alt", "") if img else ""),
            }
        )
    return rows, total_count


def parse_detail_page(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    design = parse_detail_design(soup)

    meta_description = ""
    meta_keywords = ""
    og_title = ""
    og_description = ""
    og_image = ""
    og_price = ""
    for meta in soup.find_all("meta"):
        name = meta.get("name", "")
        prop = meta.get("property", "")
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
        elif prop == "product:price:amount":
            og_price = content

    artist_visible = clean_text(soup.select_one(".artist-info").get_text(" ", strip=True) if soup.select_one(".artist-info") else "")
    title_visible = clean_text(soup.select_one(".info-area p.name").get_text(" ", strip=True) if soup.select_one(".info-area p.name") else "")
    desc_visible = clean_text(soup.select_one(".artwork-area .desc").get_text(" ", strip=True) if soup.select_one(".artwork-area .desc") else "")

    size = design.get("size", "")
    width_cm, height_cm, depth_cm = parse_size_cm(size)
    price_detail = design.get("price", "") or og_price

    return {
        "artist_detail": design.get("artist", "") or artist_visible,
        "title_detail": design.get("artwork", "") or title_visible or og_title,
        "price_text_detail": price_detail,
        "price_krw_detail": parse_price_krw(price_detail) or parse_price_krw(og_price),
        "maker": design.get("maker", ""),
        "size_raw": size,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "depth_cm": depth_cm,
        "method": design.get("method", ""),
        "material": design.get("material", ""),
        "edition": design.get("edition", ""),
        "code": design.get("code", ""),
        "short_description": design.get("상품간략설명", "") or desc_visible,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def collect_list_pages(cfg: FetchConfig, max_pages: int | None) -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    total_count = None
    page = 1
    while True:
        if max_pages is not None and page > max_pages:
            break
        html = fetch_url(LIST_URL.format(page=page), LIST_HTML_DIR / f"page_{page:03d}.html", cfg)
        rows, page_total = parse_list_page(html, page)
        if page_total:
            total_count = page_total
        if not rows:
            break
        all_rows.extend(rows)
        print(f"list page {page}: {len(rows)} rows")
        if total_count and len(all_rows) >= total_count:
            break
        page += 1
    return all_rows


def collect_detail_pages(list_rows: list[dict[str, Any]], cfg: FetchConfig) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    unique_rows: list[dict[str, Any]] = []
    for row in list_rows:
        product_no = str(row.get("product_no") or "")
        if not product_no or product_no in seen:
            continue
        seen.add(product_no)
        unique_rows.append(row)

    for idx, row in enumerate(unique_rows, start=1):
        product_no = str(row["product_no"])
        url = str(row["detail_url"])
        try:
            html = fetch_url(url, DETAIL_HTML_DIR / f"product_{product_no}.html", cfg)
            detail = parse_detail_page(html)
            output_rows.append({**row, **detail, "detail_fetch_status": "ok"})
        except Exception as exc:  # 네트워크/파싱 실패 행도 남겨 재시도 가능하게 한다.
            output_rows.append({**row, "detail_fetch_status": f"error: {type(exc).__name__}: {exc}"})
        if idx % 25 == 0 or idx == len(unique_rows):
            print(f"detail {idx}/{len(unique_rows)}")
            write_csv(OUTPUT_DIR / "printbakery_originals_detail_partial.csv", output_rows)
    return output_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=None, help="테스트용 최대 목록 페이지 수")
    parser.add_argument("--list-only", action="store_true", help="목록 페이지만 수집")
    parser.add_argument("--delay-sec", type=float, default=1.0, help="HTTP 요청 간격")
    parser.add_argument("--refresh", action="store_true", help="캐시 HTML 무시 후 재수집")
    args = parser.parse_args()

    cfg = FetchConfig(delay_sec=args.delay_sec, refresh=args.refresh)
    rows = collect_list_pages(cfg, args.max_pages)
    rows = sorted(rows, key=lambda r: int(r["product_no"]) if str(r["product_no"]).isdigit() else 0, reverse=True)
    write_csv(OUTPUT_DIR / "printbakery_originals_list.csv", rows)
    print(f"list total rows: {len(rows)}")

    if args.list_only:
        summary = {"list_rows": len(rows), "detail_rows": 0, "mode": "list_only"}
        (OUTPUT_DIR / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    detail_rows = collect_detail_pages(rows, cfg)
    write_csv(OUTPUT_DIR / "printbakery_originals_detail.csv", detail_rows)
    summary = {
        "list_rows": len(rows),
        "detail_rows": len(detail_rows),
        "detail_ok_rows": sum(1 for r in detail_rows if r.get("detail_fetch_status") == "ok"),
        "detail_error_rows": sum(1 for r in detail_rows if r.get("detail_fetch_status") != "ok"),
        "delay_sec": args.delay_sec,
        "category_url": LIST_URL.format(page=1),
    }
    (OUTPUT_DIR / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
