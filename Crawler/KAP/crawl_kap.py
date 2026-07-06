"""KAP(Korean Artist Project) Career 크롤러.

영문+한국어 양쪽에서 작가 프로필(학력/전시/수상/소장처)을 수집한다.
모든 레코드에 출처(source, source_url) 포함.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Crawler/KAP/ → 저장소 루트는 3단계 위 (parent×3)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DELAY = 1.5
ENG_BASE = "http://www.koreanartistproject.com/eng_artist.art"
KOR_BASE = "http://www.koreanartistproject.com/kor_artist.art"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_basic_info(html: str, lang: str) -> dict:
    """기본 정보(이름, 생년, 장르) 추출 — HTML에서 직접."""
    info: dict = {}
    text = re.sub(r"<[^>]+>", "\n", html)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 작가명 — "View" 마커 이후. 이름과 미술관이 같은 줄 또는 다음 줄에 있을 수 있음.
    view_kw = "View" if lang == "eng" else "상세보기"
    found_view = False
    for idx, line in enumerate(lines):
        if view_kw in line:
            found_view = True
            continue
        if found_view:
            key = "name_eng" if lang == "eng" else "name_kor"
            if lang == "eng":
                # 같은 줄: "Un Kang, Savina Museum"
                m = re.match(r"^([A-Za-z][\w\s\-\.\']+)\s*,\s*(.+)", line)
                if m:
                    info[key] = m.group(1).strip()
                    info["recommended_museum"] = m.group(2).strip()
                    break
                # 쉼표로 끝남: "Un Kang," → 다음 줄이 미술관
                m2 = re.match(r"^([A-Za-z][\w\s\-\.\']+),?\s*$", line)
                if m2 and idx + 1 < len(lines):
                    info[key] = m2.group(1).strip().rstrip(",")
                    info["recommended_museum"] = lines[idx + 1].strip()
                    break
            else:
                m = re.match(r"^([\uac00-\ud7af]{2,10})\s*,?\s*(.*)", line)
                if m:
                    info[key] = m.group(1).strip()
                    museum = m.group(2).strip() if m.group(2) else ""
                    if not museum and idx + 1 < len(lines):
                        museum = lines[idx + 1].strip()
                    info["recommended_museum"] = museum
                    break

    # 생년
    birth_kw = "Birth" if lang == "eng" else "출생"
    for i, line in enumerate(lines):
        if line == birth_kw and i + 1 < len(lines):
            bm = re.match(r"(\d{4})(?:\s*,\s*(.+))?", lines[i + 1])
            if bm:
                info["birth_year"] = int(bm.group(1))
                info["birth_place"] = bm.group(2).strip() if bm.group(2) else ""
            break

    # 장르
    genre_kw = "Genre" if lang == "eng" else "장르"
    for i, line in enumerate(lines):
        if line == genre_kw and i + 1 < len(lines):
            info["genre"] = lines[i + 1]
            break

    return info


def parse_cv_tables(html: str) -> dict:
    """HTML 테이블에서 Education, Solo, Group, Award, Collection 추출.

    KAP 구조: 첫 3개 테이블은 로그인/회원가입 폼이고,
    table[3]=학력, [4]=개인전, [5]=그룹전, [6]=수상, [7]=소장처.
    '정보테이블' class가 포함된 테이블만 CV 데이터.
    """
    tables = re.findall(r"<table\b[^>]*>(.*?)</table>", html, re.DOTALL)

    # '정보테이블' caption이 있는 테이블만 필터
    cv_tables: list[str] = []
    for table in tables:
        if "정보테이블" in table:
            cv_tables.append(table)

    sections: list[list[dict]] = []
    for table in cv_tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL)
        entries: list[dict] = []
        for row in rows:
            # 연도는 <th scope="row"> 또는 <td>에 있을 수 있음
            th_cells = re.findall(r"<th[^>]*>(.*?)</th>", row, re.DOTALL)
            td_cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)

            year_text = ""
            if th_cells:
                year_text = re.sub(r"<[^>]+>", "", th_cells[0]).strip()
            desc_parts = [re.sub(r"<[^>]+>", " ", c).strip() for c in td_cells]
            desc_text = re.sub(r"\s+", " ", " ".join(desc_parts)).strip()

            year_m = re.match(r"(\d{4})", year_text)
            if year_m and desc_text:
                entries.append({"year": int(year_m.group(1)), "description": desc_text, "source": "KAP"})
            elif desc_text and len(desc_text) > 3:
                # 소장처 등 연도 없는 항목
                entries.append({"institution": desc_text, "source": "KAP"})
        if entries:
            sections.append(entries)

    # 섹션 매핑: education, solo, group, award, collection
    result: dict = {
        "education": [],
        "solo_exhibitions": [],
        "group_exhibitions": [],
        "awards": [],
        "collections_raw": [],
    }
    labels = ["education", "solo_exhibitions", "group_exhibitions", "awards", "collections_raw"]
    for i, sec in enumerate(sections):
        if i < len(labels):
            result[labels[i]] = sec

    return result


def parse_collections(html: str) -> list[str]:
    """소장처 목록 추출 — 테이블 이후 텍스트 영역."""
    text = re.sub(r"<[^>]+>", "\n", html)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    collections: list[str] = []
    # "more" 또는 "Privacy" 앞의 기관명 목록
    collecting = False
    for line in reversed(lines):
        if line in ("more", "Privacy Policy l User Agreement l About KAP", ""):
            continue
        if re.match(r"^\d{4}$", line):
            break  # 연도 = 전시 영역 시작
        if ":" in line and len(line) < 10:
            continue
        if len(line) > 5:
            collections.insert(0, line)
            collecting = True
        if collecting and not line:
            break

    # 전시/수상 항목과 구분 — 기관명 특징 필터
    filtered = []
    for c in collections:
        if re.match(r"^\d{4}\t", c):
            continue
        filtered.append(c)

    return filtered


def crawl_artist(auth_id: int) -> dict | None:
    """한 작가의 영문+한글 Career 데이터 수집."""
    eng_url = f"{ENG_BASE}?method=artistView&auth_reg_no={auth_id}&flag=artist&flag2=career"
    kor_url = f"{KOR_BASE}?method=artistView&auth_reg_no={auth_id}&flag=artist&flag2=career"

    # 영문 페이지
    eng_html = fetch(eng_url)
    if "Artists > View" not in eng_html and "참여작가 > 상세보기" not in eng_html:
        return None
    if len(eng_html) < 500:
        return None

    eng_info = parse_basic_info(eng_html, "eng")

    if not eng_info.get("name_eng"):
        return None

    # 한국어 페이지 — 한글 이름 수집
    time.sleep(0.5)
    try:
        kor_html = fetch(kor_url)
        kor_info = parse_basic_info(kor_html, "kor")
    except Exception:
        kor_info = {}

    # CV 테이블 파싱 (영문 기준)
    cv = parse_cv_tables(eng_html)

    # 소장처 — CV 테이블 또는 텍스트에서
    collections_from_table = [
        c.get("institution", c.get("description", ""))
        for c in cv.get("collections_raw", [])
    ]
    collections_from_text = parse_collections(eng_html)
    collections = collections_from_table if collections_from_table else collections_from_text

    profile = {
        "source": "KAP",
        "source_url": eng_url,
        "source_url_kor": kor_url,
        "kap_id": auth_id,
        "name_eng": eng_info.get("name_eng", ""),
        "name_kor": kor_info.get("name_kor", ""),
        "birth_year": eng_info.get("birth_year"),
        "birth_place": eng_info.get("birth_place", ""),
        "genre": eng_info.get("genre", ""),
        "recommended_museum": eng_info.get("recommended_museum", ""),
        "homepage": eng_info.get("homepage", ""),
        "education": cv["education"],
        "education_count": len(cv["education"]),
        "solo_exhibitions": cv["solo_exhibitions"],
        "solo_exhibition_count": len(cv["solo_exhibitions"]),
        "group_exhibitions": cv["group_exhibitions"],
        "group_exhibition_count": len(cv["group_exhibitions"]),
        "awards": cv["awards"],
        "award_count": len(cv["awards"]),
        "collections": collections,
        "collection_count": len(collections),
    }

    return profile


def main() -> None:
    logger.info("=== KAP Career 크롤링 시작 ===")

    all_profiles: list[dict] = []
    empty_streak = 0

    for auth_id in range(1, 300):
        try:
            profile = crawl_artist(auth_id)
            if profile:
                empty_streak = 0
                all_profiles.append(profile)
                logger.info(
                    "[%3d] %s (%s) b.%s | 학력 %d | 개인전 %d | 그룹전 %d | 수상 %d | 소장 %d",
                    auth_id,
                    profile["name_eng"],
                    profile["name_kor"],
                    profile.get("birth_year", "?"),
                    profile["education_count"],
                    profile["solo_exhibition_count"],
                    profile["group_exhibition_count"],
                    profile["award_count"],
                    profile["collection_count"],
                )
            else:
                empty_streak += 1
                if empty_streak > 30:
                    logger.info("연속 %d개 빈 페이지 — 종료", empty_streak)
                    break
        except Exception as e:
            empty_streak += 1
            if empty_streak > 30:
                break

        time.sleep(DELAY)

    # 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    json_path = DATA_DIR / "kap_artist_profiles.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, ensure_ascii=False, indent=2)

    csv_path = DATA_DIR / "kap_artist_profiles.csv"
    fields = [
        "kap_id", "source", "source_url", "name_eng", "name_kor",
        "birth_year", "birth_place", "genre",
        "education_count", "solo_exhibition_count", "group_exhibition_count",
        "award_count", "collection_count",
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_profiles)

    logger.info("JSON: %s (%d profiles)", json_path, len(all_profiles))
    logger.info("CSV: %s", csv_path)

    # 요약
    print(f"\n{'='*70}")
    print(f"KAP 크롤링 완료")
    print(f"{'='*70}")
    print(f"  총 작가: {len(all_profiles)}명")
    print(f"  한글 이름: {sum(1 for p in all_profiles if p.get('name_kor'))}명")
    print(f"  생년: {sum(1 for p in all_profiles if p.get('birth_year'))}명")
    print(f"  학력: {sum(1 for p in all_profiles if p['education_count'] > 0)}명")
    print(f"  개인전: {sum(1 for p in all_profiles if p['solo_exhibition_count'] > 0)}명")
    print(f"  그룹전: {sum(1 for p in all_profiles if p['group_exhibition_count'] > 0)}명")
    print(f"  수상: {sum(1 for p in all_profiles if p['award_count'] > 0)}명")
    print(f"  소장처: {sum(1 for p in all_profiles if p['collection_count'] > 0)}명")


if __name__ == "__main__":
    main()
