"""Artsy 작가 정보 + URL 링크 데이터셋 생성.

기존 `data/artsy_kr_artists_full.csv` (1,925 작가, 14 컬럼) 기반.
Artsy URL pattern = `https://www.artsy.net/artist/{slug}/<section>`.

5 URL 컬럼 파생: cv / overview / works / shows / auction-results
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "artsy_kr_artists_full.csv"
OUT = ROOT / "data" / "artsy_kr_artists_with_links.csv"

ARTSY_BASE = "https://www.artsy.net/artist"
SECTIONS = {
    "url_overview": "",
    "url_cv": "/cv",
    "url_works": "/works-for-sale",
    "url_shows": "/shows",
    "url_auction_results": "/auction-results",
}


def main():
    df = pd.read_csv(SRC)
    print(f"입력: {SRC.relative_to(ROOT)} — {len(df):,} 작가 × {len(df.columns)} 컬럼")

    missing_slug = df["slug"].isna().sum()
    if missing_slug:
        print(f"⚠️  slug 결측 {missing_slug} 건 — 해당 row URL 컬럼 결측")

    for col, suffix in SECTIONS.items():
        df[col] = df["slug"].apply(
            lambda s: f"{ARTSY_BASE}/{s}{suffix}" if pd.notna(s) else None
        )

    df.to_csv(OUT, index=False)
    print(f"\n출력: {OUT.relative_to(ROOT)} — {len(df):,} 작가 × {len(df.columns)} 컬럼")
    print(f"  추가된 URL 컬럼: {list(SECTIONS.keys())}")
    print(f"\nsample (first 3 rows, slug + url_cv):")
    print(df[["slug", "name", "url_cv"]].head(3).to_string(index=False))


if __name__ == "__main__":
    main()
