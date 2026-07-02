#!/usr/bin/env python3
"""
Art1 원화 카테고리 수집 스크립트.

전제:
- 사이트 사용 허가를 받은 상태에서 실행한다.
- 수집 대상은 원화 카테고리(medium=0)이다.

수집 대상:
- 목록 1페이지: https://www.art1.com/marketPlace/market_list.php?medium=0
- 추가 목록: /marketPlace/__artworks_list.php?page=N&medium=0
- 상세: /marketPlace/__detail_view.php?goods={goods_id}

수집 항목:
- 목록: goods_id, 작품명, 작가명, 크기, 가격, 판매완료 여부, 이미지, 목록 class
- 상세: 제작연도, 장르, 재료, 액자, 크기, 배송, 판매가격, 작품설명, 작가소개

운영:
- HTML 원본은 raw_html/에 캐시한다.
- 재실행 시 캐시를 사용하므로 중간에 멈춰도 이어서 진행할 수 있다.
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


BASE_URL = "https://www.art1.com"
LIST_URL = f"{BASE_URL}/marketPlace/market_list.php?medium=0"
AJAX_LIST_URL = f"{BASE_URL}/marketPlace/__artworks_list.php"
DETAIL_URL = f"{BASE_URL}/marketPlace/__detail_view.php?goods={{goods_id}}"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Art1Collector/1.0"

PACKAGE_DIR = Path(__file__).resolve().parents[1]
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


def clean_detail_value(value: Any) -> str:
    """상세 표 안에 같이 붙는 UI 링크 문구를 제거한다."""
    text = clean_text(value)
    for suffix in ("작가 작품 모아보기", "회화작품 모아보기", "작품 모아보기"):
        text = text.replace(suffix, "")
    return clean_text(text)


def absolute_url(url: str) -> str:
    if not url:
        return ""
    return urllib.parse.urljoin(BASE_URL, url)


def fetch_url(url: str, cache_path: Path, cfg: FetchConfig, referer: str = LIST_URL) -> str:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not cfg.refresh:
        return cache_path.read_text(encoding="utf-8", errors="replace")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": referer,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    cache_path.write_text(html, encoding="utf-8")
    if cfg.delay_sec > 0:
        time.sleep(cfg.delay_sec)
    return html


def parse_price_krw(text: str) -> int | None:
    text = clean_text(text)
    if not text or "판매완료" in text or "문의" in text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else None


def parse_size(size_text: str) -> tuple[float | None, float | None, float | None, str]:
    text = clean_text(size_text)
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.split("(")[0])]
    while len(nums) < 3:
        nums.append(None)
    ho = ""
    m = re.search(r"\(([^)]*호[^)]*)\)", text)
    if m:
        ho = clean_text(m.group(1))
    return nums[0], nums[1], nums[2], ho


def parse_total_page(html: str) -> int:
    m = re.search(r"totalPage\s*=\s*(\d+)", html)
    return int(m.group(1)) if m else 1


def parse_card_sections(html: str, page: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for sec in soup.select("section.newsBox"):
        if "bt_vewmore" in (sec.get("class") or []):
            continue
        goods_id = clean_text(sec.get("id", "")).replace("isto", "")
        if not goods_id:
            onclick = sec.select_one(".Boximg")
            raw = onclick.get("onclick", "") if onclick else ""
            m = re.search(r"goods\s*=\s*'(\d+)'", raw)
            goods_id = m.group(1) if m else ""
        if not goods_id:
            continue
        title = clean_text(sec.select_one("h1").get_text(" ", strip=True) if sec.select_one("h1") else "")
        artist = clean_text(sec.select_one(".name").get_text(" ", strip=True) if sec.select_one(".name") else "")
        size_text = clean_text(sec.select_one(".info").get_text(" ", strip=True) if sec.select_one(".info") else "")
        price_text = clean_text(sec.select_one(".price").get_text(" ", strip=True) if sec.select_one(".price") else "")
        img = sec.select_one(".Boximg img")
        img_src = absolute_url(img.get("src", "") if img else "")
        is_sold = "판매완료" in price_text or bool(sec.select_one(".sale"))
        width_cm, height_cm, depth_cm, ho_size = parse_size(size_text)
        rows.append(
            {
                "source": "art1",
                "category": "fine_art",
                "medium_filter": "0",
                "list_page": page,
                "goods_id": goods_id,
                "title_list": title,
                "artist_list": artist,
                "size_text_list": size_text,
                "width_cm_list": width_cm,
                "height_cm_list": height_cm,
                "depth_cm_list": depth_cm,
                "ho_size_list": ho_size,
                "price_text_list": price_text,
                "price_krw_list": parse_price_krw(price_text),
                "is_sold_list": is_sold,
                "image_url_list": img_src,
                "list_classes": " ".join(sec.get("class") or []),
                "detail_url": DETAIL_URL.format(goods_id=goods_id),
            }
        )
    return rows


def detail_table_values(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}
    table = soup.select_one("article.workInfo table")
    if not table:
        table = soup.find("table")
    if not table:
        return values
    for tr in table.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        key = clean_text(th.get_text(" ", strip=True))
        val = clean_text(td.get_text(" ", strip=True))
        if "|" in key:
            key = clean_text(key.split("|", 1)[0])
        # tooltip text can be attached to the th. Keep only the label before obvious help marks.
        key = re.sub(r"\s+!.*$", "", key).strip()
        if key:
            values[key] = val
    return values


def parse_detail_page(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(soup.select_one(".titleArea h1").get_text(" ", strip=True) if soup.select_one(".titleArea h1") else "")
    main_img = soup.select_one(".imgArea img")
    image_url = absolute_url(main_img.get("src", "") if main_img else "")
    table = detail_table_values(soup)

    price_text = clean_text(soup.select_one(".buyArea .price .txt").get_text(" ", strip=True) if soup.select_one(".buyArea .price .txt") else "")
    if not price_text:
        price_text = table.get("판매가격", "")
    size_text = table.get("크기", "")
    width_cm, height_cm, depth_cm, ho_size = parse_size(size_text)

    # 작품설명과 작가소개 영역은 스킨 구조가 바뀔 수 있어 대표 class와 텍스트 헤더 양쪽으로 시도한다.
    artwork_desc = ""
    artist_profile = ""
    for art in soup.select("article"):
        txt = clean_text(art.get_text(" ", strip=True))
        if not artwork_desc and ("작품설명" in txt or "작품 설명" in txt):
            artwork_desc = txt
        if not artist_profile and ("작가소개" in txt or "작가 소개" in txt):
            artist_profile = txt
    if not artwork_desc:
        cand = soup.select_one(".curators_view, #curators_view")
        artwork_desc = clean_text(cand.get_text(" ", strip=True) if cand else "")
    if not artist_profile:
        cand = soup.select_one(".artist_profile, #artist_profile")
        artist_profile = clean_text(cand.get_text(" ", strip=True) if cand else "")

    return {
        "title_detail": title,
        "artist_detail": clean_detail_value(table.get("작가명", "")),
        "year_detail": table.get("제작연도", ""),
        "genre_detail": clean_detail_value(table.get("장르", "")),
        "medium_detail": table.get("재료", ""),
        "frame_detail": table.get("액자", ""),
        "size_text_detail": size_text,
        "width_cm_detail": width_cm,
        "height_cm_detail": height_cm,
        "depth_cm_detail": depth_cm,
        "ho_size_detail": ho_size,
        "shipping_cost_detail": table.get("배송비", ""),
        "shipping_method_detail": table.get("배송방법", ""),
        "price_text_detail": price_text,
        "price_krw_detail": parse_price_krw(price_text),
        "image_url_detail": image_url,
        "artwork_description": artwork_desc,
        "artist_profile": artist_profile,
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


def collect_list(cfg: FetchConfig, max_pages: int | None) -> tuple[list[dict[str, Any]], int]:
    first_html = fetch_url(LIST_URL, LIST_HTML_DIR / "page_001.html", cfg, referer=LIST_URL)
    total_page = parse_total_page(first_html)
    if max_pages is not None:
        total_page = min(total_page, max_pages)

    all_rows = parse_card_sections(first_html, 1)
    print(f"list page 1/{total_page}: {len(all_rows)} rows")
    for page in range(2, total_page + 1):
        params = {
            "page": str(page),
            "medium": "0",
            "sort": "",
            "place": "",
            "ambience": "",
            "price1": "0",
            "price2": "0",
            "depth_size": "0",
            "width_size": "0",
            "shape": "",
            "color": "",
            "delivery": "",
            "soldout": "",
            "hashtag": "",
            "subject": "",
            "size": "",
        }
        url = AJAX_LIST_URL + "?" + urllib.parse.urlencode(params)
        html = fetch_url(url, LIST_HTML_DIR / f"page_{page:03d}.html", cfg, referer=LIST_URL)
        rows = parse_card_sections(html, page)
        all_rows.extend(rows)
        print(f"list page {page}/{total_page}: {len(rows)} rows")
    # de-dupe by goods_id
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in all_rows:
        gid = str(row.get("goods_id") or "")
        if gid and gid not in seen:
            seen.add(gid)
            deduped.append(row)
    return deduped, total_page


def collect_detail(list_rows: list[dict[str, Any]], cfg: FetchConfig) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(list_rows, start=1):
        gid = str(row["goods_id"])
        try:
            html = fetch_url(DETAIL_URL.format(goods_id=gid), DETAIL_HTML_DIR / f"goods_{gid}.html", cfg, referer=LIST_URL)
            detail = parse_detail_page(html)
            out.append({**row, **detail, "detail_fetch_status": "ok"})
        except Exception as exc:
            out.append({**row, "detail_fetch_status": f"error: {type(exc).__name__}: {exc}"})
        if idx % 25 == 0 or idx == len(list_rows):
            print(f"detail {idx}/{len(list_rows)}")
            write_csv(OUTPUT_DIR / "art1_fine_art_detail_partial.csv", out)
    return out


def enrich(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        out["title_final"] = clean_text(row.get("title_detail")) or clean_text(row.get("title_list"))
        out["artist_final"] = clean_text(row.get("artist_detail")) or clean_text(row.get("artist_list"))
        out["price_krw_final"] = row.get("price_krw_detail") or row.get("price_krw_list")
        out["has_positive_price"] = bool(out["price_krw_final"])
        out["width_cm_final"] = row.get("width_cm_detail") or row.get("width_cm_list")
        out["height_cm_final"] = row.get("height_cm_detail") or row.get("height_cm_list")
        out["depth_cm_final"] = row.get("depth_cm_detail") or row.get("depth_cm_list")
        if out["width_cm_final"] and out["height_cm_final"]:
            out["area_cm2"] = float(out["width_cm_final"]) * float(out["height_cm_final"])
        else:
            out["area_cm2"] = None
        out["image_url_final"] = clean_text(row.get("image_url_detail")) or clean_text(row.get("image_url_list"))
        enriched.append(out)
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=None, help="테스트용 최대 목록 페이지 수")
    parser.add_argument("--list-only", action="store_true", help="목록만 수집")
    parser.add_argument("--delay-sec", type=float, default=1.0, help="HTTP 요청 간격")
    parser.add_argument("--refresh", action="store_true", help="캐시 무시 후 재수집")
    args = parser.parse_args()

    cfg = FetchConfig(delay_sec=args.delay_sec, refresh=args.refresh)
    list_rows, total_page = collect_list(cfg, args.max_pages)
    write_csv(OUTPUT_DIR / "art1_fine_art_list.csv", list_rows)
    if args.list_only:
        summary = {"mode": "list_only", "total_page": total_page, "list_rows": len(list_rows)}
        (OUTPUT_DIR / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    detail_rows = collect_detail(list_rows, cfg)
    write_csv(OUTPUT_DIR / "art1_fine_art_detail.csv", detail_rows)
    enriched = enrich(detail_rows)
    write_csv(OUTPUT_DIR / "art1_fine_art_detail_normalized.csv", enriched)
    summary = {
        "mode": "detail",
        "total_page": total_page,
        "list_rows": len(list_rows),
        "detail_rows": len(detail_rows),
        "detail_ok_rows": sum(1 for r in detail_rows if r.get("detail_fetch_status") == "ok"),
        "detail_error_rows": sum(1 for r in detail_rows if r.get("detail_fetch_status") != "ok"),
        "positive_price_rows": sum(1 for r in enriched if r.get("has_positive_price")),
        "sold_rows_list": sum(1 for r in enriched if r.get("is_sold_list")),
        "delay_sec": args.delay_sec,
    }
    (OUTPUT_DIR / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
