"""KADA 작가 프로필 + K-ARTMARKET 경매 가격 + Artsy/KAP CV 통합.

3개 소스를 한글 이름 기준으로 매칭해 통합 데이터셋을 생성한다.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    # 1. KADA 한글+영문 이름 (96명)
    kada_names = load_json(DATA_DIR / "kada_artists_korean.json")
    logger.info("KADA 작가: %d명", len(kada_names))

    # 2. K-ARTMARKET 경매 가격 (22명)
    kartmarket = load_json(DATA_DIR / "kada_kartmarket_prices.json")
    price_by_kor = {a["name_kor"]: a for a in kartmarket}
    logger.info("K-ARTMARKET 가격: %d명", len(kartmarket))

    # 3. Artsy CV (13명)
    artsy_cv = load_json(DATA_DIR / "kada_artsy_cv.json")
    artsy_by_kor = {a["name_kor"]: a for a in artsy_cv}
    logger.info("Artsy CV: %d명", len(artsy_cv))

    # 4. KAP Career (111명) — 한글 이름으로 매칭
    kap_path = DATA_DIR / "kap_artist_profiles.json"
    kap_by_kor: dict = {}
    if kap_path.exists():
        kap_profiles = load_json(kap_path)
        for p in kap_profiles:
            kor = p.get("name_kor", "")
            if kor and len(kor) >= 2:
                kap_by_kor[kor] = p
        logger.info("KAP 프로필: %d명 (한글 이름 있는)", len(kap_by_kor))

    # 통합
    integrated: list[dict] = []
    for artist in kada_names:
        name_kor = artist["name_kor"]
        name_eng = artist["name_eng"]

        record: dict = {
            "name_kor": name_kor,
            "name_eng": name_eng,
            "sources": ["KADA"],
        }

        # K-ARTMARKET 가격
        price_data = price_by_kor.get(name_kor)
        if price_data:
            works = price_data.get("works", price_data.get("works_sample", []))
            prices = [w["price_krw"] for w in works if isinstance(w.get("price_krw"), int) and w["price_krw"] > 0]
            record["has_auction_price"] = True
            record["auction_count"] = price_data.get("total", len(works))
            record["price_min"] = min(prices) if prices else 0
            record["price_max"] = max(prices) if prices else 0
            record["price_median"] = sorted(prices)[len(prices) // 2] if prices else 0
            record["sources"].append("K-ARTMARKET")
        else:
            record["has_auction_price"] = False
            record["auction_count"] = 0

        # Artsy CV
        artsy = artsy_by_kor.get(name_kor)
        if artsy:
            record["artsy_slug"] = artsy["slug"]
            record["artsy_solo_shows"] = artsy.get("solo_shows", 0)
            record["artsy_group_shows"] = artsy.get("group_shows", 0)
            record["artsy_fair_booths"] = artsy.get("fair_booths", 0)
            record["sources"].append("Artsy")

        # KAP Career
        kap = kap_by_kor.get(name_kor)
        if kap:
            record["kap_education_count"] = kap.get("education_count", len(kap.get("education", [])))
            record["kap_solo_count"] = kap.get("solo_exhibition_count", 0)
            record["kap_group_count"] = kap.get("group_exhibition_count", 0)
            record["kap_award_count"] = kap.get("award_count", 0)
            record["kap_collection_count"] = kap.get("collection_count", 0)
            record["sources"].append("KAP")

        record["source_count"] = len(record["sources"])
        integrated.append(record)

    # 정렬: 가격 있는 작가 우선, 소스 많은 순
    integrated.sort(key=lambda x: (-int(x["has_auction_price"]), -x["source_count"], -x["auction_count"]))

    # 저장
    out_path = DATA_DIR / "kada_integrated_dataset.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(integrated, f, ensure_ascii=False, indent=2)
    logger.info("통합 데이터셋: %s (%d artists)", out_path, len(integrated))

    # 요약
    has_price = [a for a in integrated if a["has_auction_price"]]
    has_artsy = [a for a in integrated if "Artsy" in a["sources"]]
    has_kap = [a for a in integrated if "KAP" in a["sources"]]
    has_both = [a for a in integrated if a["has_auction_price"] and a["source_count"] >= 3]

    print(f"\n{'='*70}")
    print("KADA 작가 통합 데이터셋")
    print(f"{'='*70}")
    print(f"  총 KADA 작가: {len(integrated)}명")
    print(f"  경매 가격 보유: {len(has_price)}명")
    print(f"  Artsy CV 보유: {len(has_artsy)}명")
    print(f"  KAP Career 보유: {len(has_kap)}명")
    print(f"  가격 + 프로필(3소스+): {len(has_both)}명")
    print()

    if has_price:
        all_prices = []
        for a in has_price:
            if a["price_median"] > 0:
                all_prices.append(a["price_median"])
        if all_prices:
            print(f"  경매 가격 중앙값 범위: {min(all_prices):,}~{max(all_prices):,}원")

    print(f"\n  상위 작가 (가격+프로필):")
    for a in has_both[:10]:
        srcs = ", ".join(a["sources"])
        print(f"    {a['name_kor']} ({a['name_eng']}) — {a['auction_count']}건 | "
              f"중앙 {a['price_median']:,}원 | 소스: {srcs}")


if __name__ == "__main__":
    main()
