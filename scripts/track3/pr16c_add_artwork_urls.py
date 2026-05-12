"""Track 3 PR16c — 작품 URL + 이미지 URL 추가 (수작업 검수 보강).

배경: Saatchi profile URL이 깨져 있는 경우가 있어 작품 페이지/이미지로 검증 필요.

source별 작품 URL 매핑:
  Artsy: artsy_kr_artworks.csv (artwork_id → artwork_url, image_url)
  Saatchi: saatchi_kr_artworks.csv (artwork_id → artwork_url, image_url)
  Artue: artue_테스트_가격포함.csv (Handle → URL). 이미지 없음.

출력 (덮어쓰기):
  data/track3_unified_v2_with_urls.csv     (전체 41,365 rows + artwork_url + image_url)
  data/track3_homonym_review.csv           (동명이인 검수용, 분리 entity 단위 + sample 작품)
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
SRC_CSV = DATA / "track3_unified_v2_with_urls.csv"      # 직전 단계 결과 (profile/cv URL 포함)
OUT_FULL_CSV = DATA / "track3_unified_v2_with_urls.csv"  # 덮어쓰기
OUT_REVIEW_CSV = DATA / "track3_homonym_review.csv"      # 동명이인 요약 (작품 sample 포함)


def build_artsy_artwork_map() -> dict:
    """artwork_id → (artwork_url, image_url)."""
    df = pd.read_csv(DATA / "artsy_kr_artworks.csv")
    return {
        str(row["artwork_id"]): (row.get("artwork_url"), row.get("image_url"))
        for _, row in df.iterrows() if pd.notna(row.get("artwork_id"))
    }


def build_saatchi_artwork_map() -> dict:
    """artwork_id → (artwork_url, image_url)."""
    df = pd.read_csv(DATA / "saatchi_kr_artworks.csv")
    return {
        str(row["artwork_id"]): (row.get("artwork_url"), row.get("image_url"))
        for _, row in df.iterrows() if pd.notna(row.get("artwork_id"))
    }


def build_artue_artwork_map() -> dict:
    """Handle → URL (Artue는 이미지 없음)."""
    df = pd.read_csv(DATA / "artue_테스트_가격포함.csv")
    return {
        str(row["Handle"]).strip(): (row.get("URL"), None)
        for _, row in df.iterrows() if pd.notna(row.get("Handle"))
    }


def main():
    logger.info("Loading unified v2 + artwork URL maps")
    df = pd.read_csv(SRC_CSV)
    artsy_aw = build_artsy_artwork_map()
    saatchi_aw = build_saatchi_artwork_map()
    artue_aw = build_artue_artwork_map()
    logger.info(f"  Artsy artworks: {len(artsy_aw):,}")
    logger.info(f"  Saatchi artworks: {len(saatchi_aw):,}")
    logger.info(f"  Artue artworks: {len(artue_aw):,}")

    def resolve_artwork(row):
        src = row["source_platform"]
        lid = str(row["source_listing_id"]).strip()
        if src == "artsy":
            r = artsy_aw.get(lid)
        elif src == "saatchi":
            r = saatchi_aw.get(lid)
        elif src == "artue":
            r = artue_aw.get(lid)
        else:
            r = None
        if r:
            return pd.Series({"artwork_url": r[0], "image_url": r[1]})
        return pd.Series({"artwork_url": None, "image_url": None})

    aw = df.apply(resolve_artwork, axis=1)
    df["artwork_url"] = aw["artwork_url"]
    df["image_url"] = aw["image_url"]

    # Coverage 확인
    coverage = df.groupby("source_platform").agg(
        total=("source_platform", "size"),
        with_aw=("artwork_url", lambda s: s.notna().sum()),
        with_img=("image_url", lambda s: s.notna().sum()),
    )
    coverage["aw_pct"] = (100 * coverage["with_aw"] / coverage["total"]).round(1)
    coverage["img_pct"] = (100 * coverage["with_img"] / coverage["total"]).round(1)
    logger.info(f"\nArtwork URL coverage:\n{coverage}")

    # 컬럼 재정렬: 검수에 필요한 정보 앞으로
    PRIORITY = [
        "artist_name_ko_orig", "artist_name_ko", "artist_entity_suffix", "is_homonym",
        "source_platform", "artist_entity_id_raw", "artist_name_raw",
        "profile_url", "cv_url",
        "artwork_url", "image_url",
        "price_krw_unified",
        "medium_category", "support_category",
        "width_cm", "height_cm", "depth_cm",
    ]
    ordered = PRIORITY + [c for c in df.columns if c not in PRIORITY]
    df = df[ordered]
    df.to_csv(OUT_FULL_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"\n✅ Saved: {OUT_FULL_CSV} ({len(df):,} × {len(df.columns)} cols)")

    # ── 동명이인 검수용 요약 (분리 entity 단위, 작품 sample 3개 포함) ──
    homo = df[df["is_homonym"] == True].copy()

    summary_rows = []
    grp_keys = ["artist_name_ko_orig", "artist_name_ko", "artist_entity_suffix",
                "source_platform", "artist_entity_id_raw", "artist_name_raw"]
    for keys, g in homo.groupby(grp_keys):
        g_sorted = g.sort_values("price_krw_unified")
        sample_aw = g_sorted["artwork_url"].dropna().head(3).tolist()
        sample_img = g_sorted["image_url"].dropna().head(3).tolist()
        sample_aw += [""] * (3 - len(sample_aw))
        sample_img += [""] * (3 - len(sample_img))
        summary_rows.append({
            **dict(zip(grp_keys, keys)),
            "n_works": len(g),
            "median_krw": g["price_krw_unified"].median(),
            "min_krw": g["price_krw_unified"].min(),
            "max_krw": g["price_krw_unified"].max(),
            "profile_url": g["profile_url"].iloc[0],
            "cv_url": g["cv_url"].iloc[0],
            "sample_artwork_url_1": sample_aw[0],
            "sample_artwork_url_2": sample_aw[1],
            "sample_artwork_url_3": sample_aw[2],
            "sample_image_url_1": sample_img[0],
            "sample_image_url_2": sample_img[1],
            "sample_image_url_3": sample_img[2],
        })
    summary = pd.DataFrame(summary_rows).sort_values(
        ["artist_name_ko_orig", "n_works"], ascending=[True, False]
    ).reset_index(drop=True)
    summary.to_csv(OUT_REVIEW_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"✅ Saved: {OUT_REVIEW_CSV} ({len(summary)} 분리 entity rows)")

    print()
    print("=" * 80)
    print("동명이인 검수 sample (구자현, 김유리)")
    print("=" * 80)
    s = summary[summary["artist_name_ko_orig"].isin(["구자현", "김유리"])][
        ["artist_name_ko", "source_platform", "n_works", "median_krw",
         "profile_url", "sample_artwork_url_1"]
    ]
    print(s.to_string())


if __name__ == "__main__":
    main()
