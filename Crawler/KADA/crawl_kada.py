"""KADA 작가 프로필 크롤러.

K-ARTMARKET 작가 디지털 아카이브에서 작가 프로필 데이터를 수집한다.
수집 항목: 이름, 생년, 학력, 전시 이력, 소장처, 분야.
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

BASE_URL = "https://k-artmarket.kr/kada/katEn/contents/KATEN0101.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
# Crawler/KADA/ → 저장소 루트는 3단계 위 (parent×3)
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DELAY = 1.5  # 요청 간 대기 (초)


def fetch(url: str) -> str:
    """URL에서 HTML을 가져온다."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect_artist_ids() -> list[str]:
    """전 페이지에서 작가 dataId를 수집한다."""
    all_ids: list[str] = []
    for page in range(1, 20):  # safety limit
        url = f"{BASE_URL}?page={page}"
        html = fetch(url)
        ids = list(dict.fromkeys(re.findall(r"dataId=([A-Z0-9]+)", html)))
        if not ids:
            break
        all_ids.extend(ids)
        logger.info("Page %d: %d artists", page, len(ids))
        time.sleep(DELAY)
    logger.info("Total artist IDs: %d", len(all_ids))
    return all_ids


def parse_profile(html: str) -> dict:
    """상세 페이지 HTML에서 작가 프로필을 추출한다."""
    profile: dict = {}

    # 작가명 — <h2> 태그에서 이름 + 생년 추출
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)
    for h in h2:
        text = re.sub(r"<[^>]+>", "", h).strip()
        if text and text != "Artists" and len(text) > 1:
            # "Donghyun Son1980" 패턴
            m = re.match(r"(.+?)(\d{4})$", text)
            if m:
                profile["name_eng"] = m.group(1).strip()
                profile["birth_year"] = int(m.group(2))
            else:
                profile["name_eng"] = text
            break

    # 한글 이름 — listName class 또는 autho_info 영역
    kor_matches = re.findall(r"[\uac00-\ud7af]{2,10}", html[:5000])
    # 작가 이름은 보통 2~5자 한글
    for km in kor_matches:
        if 2 <= len(km) <= 5 and km not in ("신진", "중견", "원로", "작가", "전시", "서울", "한국"):
            profile["name_kor"] = km
            break

    # 분야
    field_m = re.search(
        r"(Painting|Sculpture|Media|Installation|Photography|Mixed Media|Drawing|Print|Craft)",
        html, re.IGNORECASE,
    )
    if field_m:
        profile["field"] = field_m.group(0)

    # 학력 — Education 키워드 후 텍스트 추출
    edu_idx = html.find("ducation")
    education: list[str] = []
    if edu_idx > 0:
        edu_area = html[edu_idx : edu_idx + 2000]
        edu_text = re.sub(r"<[^>]+>", "\n", edu_area)
        for line in edu_text.split("\n"):
            line = line.strip()
            if any(
                kw in line.lower()
                for kw in [
                    "university", "college", "academy", "school",
                    "m.f.a", "b.f.a", "ph.d", "m.a.", "b.a.",
                    "대학", "석사", "학사", "박사",
                ]
            ):
                education.append(line[:150])
        # 연도-학력 패턴
        year_edu = re.findall(r"(\d{4})\s*:?\s*(.*?(?:University|College|Academy|School|대학)[^<\n]*)", edu_area)
        for year, desc in year_edu:
            entry = f"{year}: {re.sub(r'<[^>]+>', '', desc).strip()}"
            if entry not in education:
                education.append(entry[:150])
    profile["education"] = education

    # 전시 이력 — Solo Exhibition / Group Exhibition 섹션
    def count_exhibitions(keyword: str) -> int:
        pattern = rf"{keyword}\s*(?:Exhibition|Show)"
        idx = html.find(keyword)
        if idx < 0:
            return 0
        # 해당 섹션 이후 전시 항목 카운트 (연도 패턴)
        section = html[idx : idx + 10000]
        entries = re.findall(r"(?:~\s*)?(\d{4})\s*\n?\s*(.+?)(?:<|$)", section)
        return len(entries)

    # Solo Exhibition 섹션 찾기
    solo_idx = html.find("Solo Exhibition")
    group_idx = html.find("Group Exhibition")
    other_idx = html.find("Other activities")
    coll_idx = html.find("Collection")

    def extract_exhibition_list(start: int, end: int) -> list[dict]:
        if start < 0:
            return []
        section = html[start:end] if end > 0 else html[start : start + 10000]
        text = re.sub(r"<[^>]+>", "\n", section)
        entries = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        current_year = None
        for line in lines:
            year_m = re.match(r"^~?\s*(\d{4})$", line)
            if year_m:
                current_year = int(year_m.group(1))
            elif current_year and len(line) > 3 and line not in (
                "Solo Exhibition", "Group Exhibition", "Show More ∨", "Other activities", "Collection",
            ):
                entries.append({"year": current_year, "title": line[:200]})
        return entries

    solo_end = group_idx if group_idx > solo_idx else (other_idx if other_idx > 0 else coll_idx)
    group_end = other_idx if other_idx > group_idx else (coll_idx if coll_idx > 0 else -1)

    solo_list = extract_exhibition_list(solo_idx, solo_end)
    group_list = extract_exhibition_list(group_idx, group_end)

    profile["solo_exhibitions"] = solo_list
    profile["solo_exhibition_count"] = len(solo_list)
    profile["group_exhibitions"] = group_list
    profile["group_exhibition_count"] = len(group_list)

    # 소장처 — Collection 섹션
    collections: list[dict] = []
    if coll_idx > 0:
        coll_section = html[coll_idx : coll_idx + 3000]
        coll_text = re.sub(r"<[^>]+>", "\n", coll_section)
        coll_lines = [l.strip() for l in coll_text.split("\n") if l.strip()]
        current_year = None
        for line in coll_lines:
            if line in ("Collection", "Show More ∨"):
                continue
            year_m = re.match(r"^(\d{4})$", line)
            if year_m:
                current_year = int(year_m.group(1))
            elif current_year and len(line) > 3:
                collections.append({"year": current_year, "institution": line[:150]})
                current_year = None
    profile["collections"] = collections
    profile["collection_count"] = len(collections)

    return profile


def main() -> None:
    """메인 크롤링 파이프라인."""
    logger.info("=== KADA 작가 프로필 크롤링 시작 ===")

    # 1. 작가 ID 수집
    artist_ids = collect_artist_ids()

    # 2. 상세 페이지 크롤링
    profiles: list[dict] = []
    for i, data_id in enumerate(artist_ids):
        url = f"{BASE_URL}?schM=view&dataId={data_id}"
        try:
            html = fetch(url)
            profile = parse_profile(html)
            profile["data_id"] = data_id
            profiles.append(profile)

            name = profile.get("name_eng", "?")
            name_kr = profile.get("name_kor", "?")
            birth = profile.get("birth_year", "?")
            solo = profile.get("solo_exhibition_count", 0)
            group = profile.get("group_exhibition_count", 0)
            coll = profile.get("collection_count", 0)
            edu = len(profile.get("education", []))

            logger.info(
                "[%d/%d] %s (%s) b.%s | 학력 %d | 개인전 %d | 그룹전 %d | 소장 %d",
                i + 1, len(artist_ids), name, name_kr, birth, edu, solo, group, coll,
            )

        except Exception as e:
            logger.warning("[%d/%d] %s: ERROR %s", i + 1, len(artist_ids), data_id, e)
            profiles.append({"data_id": data_id, "error": str(e)})

        time.sleep(DELAY)

    # 3. 저장
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON 저장
    json_path = OUTPUT_DIR / "kada_artist_profiles.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    logger.info("JSON saved: %s (%d profiles)", json_path, len(profiles))

    # CSV 저장 (요약)
    csv_path = OUTPUT_DIR / "kada_artist_profiles.csv"
    fieldnames = [
        "data_id", "name_eng", "name_kor", "birth_year", "field",
        "education_count", "solo_exhibition_count", "group_exhibition_count",
        "collection_count",
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in profiles:
            if "error" in p:
                continue
            writer.writerow({
                "data_id": p.get("data_id", ""),
                "name_eng": p.get("name_eng", ""),
                "name_kor": p.get("name_kor", ""),
                "birth_year": p.get("birth_year", ""),
                "field": p.get("field", ""),
                "education_count": len(p.get("education", [])),
                "solo_exhibition_count": p.get("solo_exhibition_count", 0),
                "group_exhibition_count": p.get("group_exhibition_count", 0),
                "collection_count": p.get("collection_count", 0),
            })
    logger.info("CSV saved: %s", csv_path)

    # 4. 요약
    valid = [p for p in profiles if "error" not in p]
    print(f"\n{'='*70}")
    print(f"KADA 크롤링 완료")
    print(f"{'='*70}")
    print(f"  총 작가: {len(artist_ids)}명")
    print(f"  수집 성공: {len(valid)}명")
    print(f"  생년 확보: {sum(1 for p in valid if p.get('birth_year'))}명")
    print(f"  학력 확보: {sum(1 for p in valid if p.get('education'))}명")
    print(f"  개인전 확보: {sum(1 for p in valid if p.get('solo_exhibition_count', 0) > 0)}명")
    print(f"  소장처 확보: {sum(1 for p in valid if p.get('collection_count', 0) > 0)}명")
    print(f"  저장: {json_path} / {csv_path}")


if __name__ == "__main__":
    main()
