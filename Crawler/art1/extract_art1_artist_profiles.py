#!/usr/bin/env python3
"""
Art1 작가 프로필 추출 스크립트.

입력:
- raw_html/detail/goods_*.html (같은 폴더의 collect_art1_fine_art.py 실행 산출물)

추출 대상:
- 작품 상세 AJAX HTML 안의 article.artistInfo / #viewPage3 / .profile 영역
- 작가별 작품 모아보기 링크: /marketPlace/artist.php?idx={artist_idx}

수집 원칙:
- Art1은 작가 페이지보다 작품 상세 안의 작가 프로필 영역이 더 풍부하다.
- 기존 Art1 작품 수집 raw HTML을 재사용해 작가 프로필을 분리한다.
- artist_idx는 Art1 내부 식별자이므로 운영 공통 artist_key로 바로 쓰지 않는다.
- 같은 작가가 여러 작품에 반복되면 가장 긴 프로필을 대표 row로 선택한다.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DETAIL_DIR = PACKAGE_DIR / "raw_html" / "detail"
OUTPUT_DIR = PACKAGE_DIR / "outputs"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).replace("\xa0", " ").split())
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def extract_goods_id(path: Path) -> str:
    m = re.search(r"goods_(\d+)\.html$", path.name)
    return m.group(1) if m else path.stem


def split_ko_en_name(value: str) -> tuple[str, str]:
    value = clean_text(value)
    for suffix in ("작가 작품 모아보기", "+ 작가 작품 모아보기", "작품 모아보기"):
        value = clean_text(value.replace(suffix, ""))
    if "|" in value:
        left, right = value.split("|", 1)
        return clean_text(left), clean_text(right)
    parts = value.split()
    if len(parts) >= 2 and re.search(r"[A-Za-z]", value):
        ko = clean_text(" ".join(p for p in parts if not re.search(r"[A-Za-z]", p)))
        en = clean_text(" ".join(p for p in parts if re.search(r"[A-Za-z]", p)))
        return ko or value, en
    return value, ""


def detail_table_values(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}
    table = soup.select_one("article.workInfo table") or soup.find("table")
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
        key = re.sub(r"\s+!.*$", "", key).strip()
        if key:
            values[key] = val
    return values


def extract_artist_idx_and_url(soup: BeautifulSoup) -> tuple[str, str]:
    for a in soup.find_all("a"):
        href = clean_text(a.get("href", ""))
        if "/marketPlace/artist.php" not in href:
            continue
        m = re.search(r"idx=(\d+)", href)
        if m:
            return m.group(1), "https://www.art1.com" + href
    return "", ""


def profile_node(soup: BeautifulSoup):
    for selector in ["article.artistInfo .profile", "#viewPage3 .profile", "article.artistInfo", "#viewPage3"]:
        node = soup.select_one(selector)
        if node and clean_text(node.get_text(" ", strip=True)):
            return node
    return None


def extract_paragraph_sections(node) -> dict[str, str]:
    sections: dict[str, str] = {}
    if not node:
        return sections

    # Art1 프로필은 div.paragraph 안의 h2 제목으로 이력 섹션이 나뉜다.
    for para in node.select(".paragraph"):
        heading_el = para.find(["h2", "h3", "strong"])
        heading = clean_text(heading_el.get_text(" ", strip=True) if heading_el else "")
        if not heading:
            continue
        texts: list[str] = []
        for li in para.find_all("li"):
            texts.append(clean_text(li.get_text(" ", strip=True)))
        if not texts:
            raw = clean_text(para.get_text(" ", strip=True))
            raw = clean_text(raw.replace(heading, "", 1))
            if raw:
                texts.append(raw)
        sections[heading] = " | ".join(t for t in texts if t)

    # statement는 paragraph가 아닌 상단 텍스트에 들어가는 경우가 있어 별도 추출한다.
    raw = clean_text(node.get_text(" ", strip=True))
    m = re.search(r"_ Artist Statement\s+(.+?)(?:\s+_ Education|\s+_ Selected Solo Exhibition|\s+_ Selected Group Exhibition|\s+_ Awards|\s+_ Project|$)", raw)
    if m:
        sections["_ Artist Statement"] = clean_text(m.group(1))
    return sections


def parse_profile(path: Path) -> dict[str, Any]:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    goods_id = extract_goods_id(path)
    table = detail_table_values(soup)
    artist_raw = clean_text(table.get("작가명", ""))
    artist_ko, artist_en = split_ko_en_name(artist_raw)
    artist_idx, artist_source_url = extract_artist_idx_and_url(soup)
    node = profile_node(soup)
    profile_text = clean_text(node.get_text(" ", strip=True) if node else "")
    sections = extract_paragraph_sections(node)

    return {
        "source": "art1",
        "goods_id": goods_id,
        "artist_idx": artist_idx,
        "artist_source_url": artist_source_url,
        "artist_name_raw": artist_raw,
        "artist_name_ko": artist_ko,
        "artist_name_en": artist_en,
        "artist_profile_text": profile_text,
        "artist_statement": sections.get("_ Artist Statement", ""),
        "education_text": sections.get("_ Education", ""),
        "selected_solo_exhibition_text": sections.get("_ Selected Solo Exhibition", ""),
        "selected_group_exhibition_text": sections.get("_ Selected Group Exhibition", ""),
        "awards_text": sections.get("_ Awards", ""),
        "project_text": sections.get("_ Project", ""),
        "collections_text": sections.get("_Collections", "") or sections.get("_ Collections", ""),
        "section_titles_json": json.dumps(list(sections), ensure_ascii=False),
        "profile_source_file": str(path),
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


def dedupe_artists(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("artist_idx") or row.get("artist_name_raw") or row.get("artist_name_ko")
        if not key:
            continue
        current = grouped.get(str(key))
        if current is None or len(str(row.get("artist_profile_text", ""))) > len(str(current.get("artist_profile_text", ""))):
            grouped[str(key)] = row
    return list(grouped.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-detail-dir", default=str(DEFAULT_RAW_DETAIL_DIR), help="Art1 goods_*.html 위치")
    args = parser.parse_args()

    raw_dir = Path(args.raw_detail_dir)
    paths = sorted(raw_dir.glob("goods_*.html"))
    if not paths:
        raise FileNotFoundError(f"No goods_*.html files found in {raw_dir}")

    rows = [parse_profile(path) for path in paths]
    artist_rows = dedupe_artists(rows)

    write_csv(OUTPUT_DIR / "art1_artwork_artist_profiles.csv", rows)
    write_csv(OUTPUT_DIR / "art1_artists_deduped.csv", artist_rows)

    summary = {
        "source": "art1",
        "input_raw_detail_dir": str(raw_dir),
        "artwork_profile_rows": len(rows),
        "artist_rows_deduped": len(artist_rows),
        "with_artist_idx": sum(1 for r in rows if r.get("artist_idx")),
        "with_profile_text": sum(1 for r in rows if r.get("artist_profile_text")),
        "with_statement": sum(1 for r in rows if r.get("artist_statement")),
        "with_education": sum(1 for r in rows if r.get("education_text")),
        "with_solo_exhibition": sum(1 for r in rows if r.get("selected_solo_exhibition_text")),
        "with_group_exhibition": sum(1 for r in rows if r.get("selected_group_exhibition_text")),
        "with_awards": sum(1 for r in rows if r.get("awards_text")),
        "with_project": sum(1 for r in rows if r.get("project_text")),
        "with_collections": sum(1 for r in rows if r.get("collections_text")),
    }
    (OUTPUT_DIR / "art1_artists_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
