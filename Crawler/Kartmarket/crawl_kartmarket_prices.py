"""K-ARTMARKET 경매 가격 크롤러.

KADA에서 수집한 작가 목록 기반으로 K-ARTMARKET의 경매 낙찰 데이터를 수집한다.
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://k-artmarket.kr/member/work/WorkList.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
}
# Crawler/Kartmarket/ → 저장소 루트는 3단계 위 (parent×3)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DELAY = 2.0


def search_artist(name_kor: str, page: int = 1) -> str:
    """작가명으로 K-ARTMARKET 검색."""
    data = urllib.parse.urlencode({
        "searchKeyword": name_kor,
        "searchCondition": "1",
        "pageNo": str(page),
    }).encode("utf-8")
    req = urllib.request.Request(BASE_URL, data=data, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_works(html: str, target_artist: str) -> list[dict]:
    """검색 결과 HTML에서 작품 정보 추출."""
    items = re.findall(r"<li\b[^>]*>(.*?)</li>", html, re.DOTALL)
    works = []

    for item in items:
        text = re.sub(r"<[^>]+>", "\n", item)
        lines = [l.strip() for l in text.split("\n") if l.strip() and l.strip() != "&nbsp;"]

        if len(lines) < 8:
            continue

        # KRW 가격이 있는 항목만
        krw_idx = None
        for i, line in enumerate(lines):
            if line == "KRW":
                krw_idx = i
                break

        if krw_idx is None:
            continue

        # 구조: [작가, 작품명, 재료, 크기cm, cm, 크기inch, inch, KRW, 가격, 경매명, 경매사, 날짜, ...]
        artist_name = lines[0] if lines else ""

        # 타겟 작가 필터
        if target_artist and target_artist not in artist_name:
            continue

        try:
            work = {
                "artist": artist_name,
                "title": lines[1] if len(lines) > 1 else "",
                "material": lines[2] if len(lines) > 2 else "",
                "size_raw": "",
                "price_krw": 0,
                "auction_name": "",
                "auction_house": "",
                "auction_date": "",
            }

            # 크기 추출 (cm 기준)
            for i, line in enumerate(lines):
                if "☓" in line and "cm" not in line.lower():
                    work["size_raw"] = line + " cm"
                    break
                if re.match(r"\d+[\.\d]*☓\d+[\.\d]*", line):
                    work["size_raw"] = line + " cm"
                    break

            # 가격
            if krw_idx + 1 < len(lines):
                price_str = lines[krw_idx + 1].replace(",", "")
                if price_str.isdigit():
                    work["price_krw"] = int(price_str)

            # 경매 정보 (가격 다음)
            post_price = lines[krw_idx + 2 :]
            if len(post_price) >= 1:
                work["auction_name"] = post_price[0]
            if len(post_price) >= 2:
                work["auction_house"] = post_price[1]
            if len(post_price) >= 3:
                # 날짜 패턴
                for pp in post_price[2:]:
                    if re.match(r"\d{4}-\d{2}-\d{2}", pp):
                        work["auction_date"] = pp
                        break

            if work["price_krw"] > 0:
                works.append(work)

        except (IndexError, ValueError):
            continue

    return works


def get_total_count(html: str) -> int:
    """검색 결과 총 건수."""
    m = re.search(r"총\s*<strong>(\d[\d,]*)</strong>\s*건", html)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def main() -> None:
    """KADA 작가 목록 기반 경매 데이터 수집."""
    # KADA 작가 목록 로드
    profiles_path = DATA_DIR / "kada_artist_profiles_unique.csv"
    if not profiles_path.exists():
        logger.error("KADA 프로필 파일 없음: %s", profiles_path)
        return

    import pandas as pd

    artists_df = pd.read_csv(profiles_path)
    # 한글 이름 추출 — name_kor가 "중견작가"인 경우 대체 시도
    artist_names = []
    for _, row in artists_df.iterrows():
        name_kor = str(row.get("name_kor", ""))
        name_eng = str(row.get("name_eng", ""))
        if name_kor and name_kor not in ("중견작가", "신진작가", "원로", "nan", ""):
            artist_names.append({"kor": name_kor, "eng": name_eng})
        else:
            # 영문 이름의 성(last name)을 한글로 변환 시도 — 여기서는 영문 그대로 검색
            artist_names.append({"kor": name_eng, "eng": name_eng})

    logger.info("검색 대상 작가: %d명", len(artist_names))

    all_works: list[dict] = []
    artists_with_data = 0

    for i, artist in enumerate(artist_names):
        name = artist["kor"]
        name_eng = artist["eng"]

        try:
            html = search_artist(name, page=1)
            total = get_total_count(html)
            works = parse_works(html, "")  # 필터 없이 전부 수집 (검색 자체가 필터)

            # 추가 페이지
            if total > 10:
                pages = min((total // 10) + 1, 10)  # 최대 10페이지
                for p in range(2, pages + 1):
                    time.sleep(DELAY)
                    html_p = search_artist(name, page=p)
                    works.extend(parse_works(html_p, ""))

            if works:
                artists_with_data += 1
                for w in works:
                    w["search_query"] = name
                    w["artist_eng"] = name_eng
                all_works.extend(works)

            logger.info(
                "[%d/%d] %s (%s): %d건 (총 %d건)",
                i + 1, len(artist_names), name, name_eng, len(works), total,
            )

        except Exception as e:
            logger.warning("[%d/%d] %s: ERROR %s", i + 1, len(artist_names), name, e)

        time.sleep(DELAY)

    # 저장
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    json_path = DATA_DIR / "kartmarket_auction_prices.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    logger.info("JSON saved: %s (%d works)", json_path, len(all_works))

    csv_path = DATA_DIR / "kartmarket_auction_prices.csv"
    if all_works:
        fieldnames = [
            "search_query", "artist_eng", "artist", "title", "material",
            "size_raw", "price_krw", "auction_name", "auction_house", "auction_date",
        ]
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for w in all_works:
                writer.writerow({k: w.get(k, "") for k in fieldnames})
        logger.info("CSV saved: %s", csv_path)

    # 요약
    print(f"\n{'='*70}")
    print(f"K-ARTMARKET 경매 데이터 수집 완료")
    print(f"{'='*70}")
    print(f"  검색 작가: {len(artist_names)}명")
    print(f"  데이터 확보: {artists_with_data}명")
    print(f"  총 작품: {len(all_works)}건")
    if all_works:
        prices = [w["price_krw"] for w in all_works if w["price_krw"] > 0]
        if prices:
            print(f"  가격 범위: {min(prices):,}~{max(prices):,}원")
            import statistics
            print(f"  가격 중앙: {statistics.median(prices):,.0f}원")
        houses = set(w["auction_house"] for w in all_works if w["auction_house"])
        print(f"  경매사: {houses}")


if __name__ == "__main__":
    main()
