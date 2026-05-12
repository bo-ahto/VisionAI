"""Track 3 PR16b — 동명이인 수작업 구분용 CV URL 추가.

source별 작가 URL 매핑:
  Artsy: artsy_kr_artists_with_links.csv 의 url_cv / url_overview 직접 사용
         (slug == artist_entity_id_raw)
  Saatchi: saatchi_kr_artists.json 의 username 기반
           https://www.saatchiart.com/{username}
           username 없는 경우: account/artist/{artist_id} 패턴 fallback
  Artue: 작가별 첫 작품 URL 참조 (artue.io는 작가 단독 profile URL 없음)

출력:
  data/track3_unified_v2_with_urls.csv (URL 컬럼 추가)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
SRC_PARQUET = DATA / "track3_unified_v2.parquet"
OUT_CSV = DATA / "track3_unified_v2_with_urls.csv"


def build_artsy_url_map() -> dict:
    """slug → (profile_url, cv_url)."""
    df = pd.read_csv(DATA / "artsy_kr_artists_with_links.csv")
    return {
        row["slug"]: (row.get("url_overview"), row.get("url_cv"))
        for _, row in df.iterrows() if pd.notna(row.get("slug"))
    }


def build_saatchi_url_map() -> dict:
    """artist_id (str) → profile_url."""
    with open(DATA / "saatchi_kr_artists.json") as f:
        artists = json.load(f)
    m = {}
    for a in artists:
        aid = str(a["artist_id"])
        username = (a.get("username") or "").strip()
        if username:
            m[aid] = f"https://www.saatchiart.com/{username}"
        else:
            # fallback: numeric id 기반 (실제 작동 보장은 못 함)
            m[aid] = f"https://www.saatchiart.com/account/artist/{aid}"
    return m


def build_artue_url_map() -> dict:
    """작가 이름 → 첫 작품 URL (artue는 별도 작가 profile URL 없음)."""
    df = pd.read_csv(DATA / "artue_테스트_가격포함.csv")
    m = {}
    for _, row in df.iterrows():
        artist = str(row["Artist"]).strip()
        url = row.get("URL")
        if artist and pd.notna(url) and artist not in m:
            m[artist] = url
    return m


def main():
    logger.info("Loading unified v2 + source URL mappings")
    df = pd.read_parquet(SRC_PARQUET)
    artsy_map = build_artsy_url_map()
    saatchi_map = build_saatchi_url_map()
    artue_map = build_artue_url_map()

    logger.info(f"  Artsy mapping: {len(artsy_map):,} slugs")
    logger.info(f"  Saatchi mapping: {len(saatchi_map):,} ids")
    logger.info(f"  Artue mapping: {len(artue_map):,} artists")

    def resolve(row):
        src = row["source_platform"]
        eid = row["artist_entity_id_raw"]
        if src == "artsy":
            r = artsy_map.get(eid)
            if r:
                return pd.Series({"profile_url": r[0], "cv_url": r[1]})
        elif src == "saatchi":
            url = saatchi_map.get(str(eid))
            if url:
                return pd.Series({"profile_url": url, "cv_url": url})
        elif src == "artue":
            # Artue: 작가 이름으로 매핑
            url = artue_map.get(str(row["artist_name_raw"]).strip())
            if url:
                return pd.Series({"profile_url": url, "cv_url": url})
        return pd.Series({"profile_url": None, "cv_url": None})

    urls = df.apply(resolve, axis=1)
    df["profile_url"] = urls["profile_url"]
    df["cv_url"] = urls["cv_url"]

    # 매핑 비율 통계
    coverage = df.groupby("source_platform").agg(
        total=("source_platform", "size"),
        with_url=("profile_url", lambda s: s.notna().sum()),
    )
    coverage["coverage_pct"] = (100 * coverage["with_url"] / coverage["total"]).round(1)
    logger.info(f"\nURL coverage by source:\n{coverage}")

    # 동명이인 구분 편의를 위해 컬럼 재정렬: 핵심 식별 정보를 앞에 배치
    PRIORITY = [
        "artist_name_ko_orig",   # 원본 한글명
        "artist_name_ko",        # 분리 ID
        "artist_entity_suffix",  # A/B/C...
        "is_homonym",            # 동명이인 여부
        "source_platform",       # 출처
        "artist_entity_id_raw",  # source의 entity ID (slug/numeric)
        "artist_name_raw",       # 원본 영문/원어 이름
        "profile_url",           # 작가 profile URL
        "cv_url",                # 작가 CV URL
        "price_krw_unified",     # 가격 (수작업 비교용)
        "medium_category",
        "support_category",
        "width_cm", "height_cm", "depth_cm",
    ]
    ordered = PRIORITY + [c for c in df.columns if c not in PRIORITY]
    df = df[ordered]

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"\n✅ Saved: {OUT_CSV}")
    logger.info(f"   {len(df):,} rows × {len(df.columns)} cols")

    # 동명이인 작품만 sample 출력
    print()
    print("=" * 80)
    print("동명이인 작품 sample (수작업 검수용)")
    print("=" * 80)
    sample = df[df["is_homonym"]].head(15)[
        ["artist_name_ko_orig", "artist_name_ko", "source_platform",
         "artist_name_raw", "profile_url", "price_krw_unified"]]
    print(sample.to_string())


if __name__ == "__main__":
    main()
