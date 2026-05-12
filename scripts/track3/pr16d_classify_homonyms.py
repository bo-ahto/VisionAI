"""Track 3 PR16d — 동명이인 분리 entity 자동 분류 + 수동 검수 리스트 추출.

규칙 (사용자 정의):
  1. 같은 한글명 안에서 profile_url이 동일 → 같은 사람 (자동 merge 대상)
  2. 같은 한글명 + 모두 같은 platform → platform이 자체적으로 잘 구분한 것 (OK 그대로)
  3. 같은 한글명 + 여러 platform → 수동 검수 필요 (같은 사람일 수도, 다른 사람일 수도)

출력:
  data/homonym_review/auto_merge.csv      — URL 동일 묶음 (있으면)
  data/homonym_review/single_platform.csv — 한 플랫폼 내 분리 (OK)
  data/homonym_review/manual_review.csv   — 수동 검수 필요 (multi-platform)
  data/homonym_review/summary.md          — 요약
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
SRC_CSV = DATA / "track3_homonym_review.csv"
OUT_DIR = DATA / "homonym_review"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(SRC_CSV)
    logger.info(f"동명이인 entity rows: {len(df)}")

    auto_merge_rows = []
    single_platform_rows = []
    manual_review_rows = []

    for orig_name, group in df.groupby("artist_name_ko_orig"):
        platforms = group["source_platform"].unique()
        urls = group["profile_url"].dropna().unique()

        # 분류 1: URL 중복 → 자동 merge
        # 같은 한글명 내에서 profile_url이 동일한 entity 묶음이 있으면 그것들을 같은 사람으로 표시
        url_dup = group.groupby("profile_url").filter(lambda x: len(x) > 1)
        if len(url_dup) > 0:
            for url, sub in url_dup.groupby("profile_url"):
                auto_merge_rows.append({
                    "artist_name_ko_orig": orig_name,
                    "shared_profile_url": url,
                    "merged_ids": " + ".join(sub["artist_name_ko"]),
                    "platforms": ", ".join(sub["source_platform"]),
                    "total_works": int(sub["n_works"].sum()),
                    "n_entities": len(sub),
                })

        # 분류 2: 한 platform 내 분리 (모두 같은 source) → OK
        if len(platforms) == 1:
            single_platform_rows.append({
                "artist_name_ko_orig": orig_name,
                "platform": platforms[0],
                "n_split_entities": len(group),
                "split_ids": " | ".join(group.sort_values("n_works", ascending=False)["artist_name_ko"]),
                "total_works": int(group["n_works"].sum()),
                "median_price_range":
                    f"{group['median_krw'].min():,.0f} ~ {group['median_krw'].max():,.0f}",
            })
        else:
            # 분류 3: 여러 platform에 걸침 → 수동 검수 대상
            # 각 entity row를 그대로 보여줌
            for _, r in group.sort_values("n_works", ascending=False).iterrows():
                manual_review_rows.append({
                    "artist_name_ko_orig": orig_name,
                    "artist_name_ko": r["artist_name_ko"],
                    "platform": r["source_platform"],
                    "entity_id_raw": r["artist_entity_id_raw"],
                    "raw_name": r["artist_name_raw"],
                    "n_works": int(r["n_works"]),
                    "median_krw": r["median_krw"],
                    "min_krw": r["min_krw"],
                    "max_krw": r["max_krw"],
                    "profile_url": r["profile_url"],
                    "cv_url": r["cv_url"],
                    "sample_artwork_url_1": r["sample_artwork_url_1"],
                    "sample_artwork_url_2": r["sample_artwork_url_2"],
                    "sample_artwork_url_3": r["sample_artwork_url_3"],
                    "sample_image_url_1": r["sample_image_url_1"],
                    "sample_image_url_2": r["sample_image_url_2"],
                    "sample_image_url_3": r["sample_image_url_3"],
                })

    # 저장
    auto_merge_df = pd.DataFrame(auto_merge_rows)
    single_df = pd.DataFrame(single_platform_rows).sort_values("n_split_entities", ascending=False)
    manual_df = pd.DataFrame(manual_review_rows)

    auto_merge_df.to_csv(OUT_DIR / "auto_merge.csv", index=False, encoding="utf-8-sig")
    single_df.to_csv(OUT_DIR / "single_platform.csv", index=False, encoding="utf-8-sig")
    manual_df.to_csv(OUT_DIR / "manual_review.csv", index=False, encoding="utf-8-sig")

    # 요약
    n_orig = df["artist_name_ko_orig"].nunique()
    n_single = len(single_df)
    n_multi = manual_df["artist_name_ko_orig"].nunique() if len(manual_df) else 0
    n_auto = len(auto_merge_df)

    summary = f"""# 동명이인 분리 entity 자동 분류 결과

## 전체 수치
- TRUE_homonym 작가 (한글명 기준): **{n_orig}명**
- 분리된 entity 총 수: **{len(df)}개** (38명 → 238 분리 entity)

## 분류

### 1️⃣ 자동 merge 가능 (profile_url 동일)
- 묶음 수: **{n_auto}개**
- 의미: 같은 한글명 안에서 URL이 동일한 entity → 같은 사람으로 자동 통합 가능
- 파일: `auto_merge.csv`

### 2️⃣ 한 플랫폼 내 분리 (정상 — 그대로 유지)
- 작가 수: **{n_single}명**
- 의미: source platform 자체가 이미 잘 구분한 것 (예: Saatchi에서 김유리 두 명을 다른 ID로)
- 파일: `single_platform.csv`

### 3️⃣ 수동 검수 필요 (여러 플랫폼 걸침)
- 작가 수: **{n_multi}명**
- entity 행 수: **{len(manual_df)}개**
- 의미: 다른 플랫폼에 같은 한글명이 있어 같은 사람/다른 사람인지 사람이 봐야 함
- 파일: `manual_review.csv` ← **이게 작업 대상**

## 검수 방법

각 작가별로 entity row 비교:
1. `profile_url` 클릭 → 작가 페이지 확인
2. URL 깨졌으면 `sample_artwork_url_1/2/3` 클릭 → 작품 페이지에서 작가 확인
3. `sample_image_url_*` 직접 → 작품 이미지 즉시 확인 (Artsy/Saatchi만)
4. 같은 사람이면 → 두 entity 묶음 (merge), 다른 사람이면 → 분리 유지
"""
    (OUT_DIR / "summary.md").write_text(summary)

    print()
    print("=" * 80)
    print("📊 동명이인 분류 결과")
    print("=" * 80)
    print(f"  자동 merge 가능 (URL 동일):  {n_auto:>3} 묶음")
    print(f"  한 플랫폼 내 분리 (OK):     {n_single:>3} 명")
    print(f"  수동 검수 필요 (multi):     {n_multi:>3} 명 / {len(manual_df)} entity rows")
    print()
    print(f"  → 파일: {OUT_DIR}/")
    print(f"      auto_merge.csv ({n_auto})")
    print(f"      single_platform.csv ({n_single})")
    print(f"      manual_review.csv ({len(manual_df)})  ← 작업 대상")
    print(f"      summary.md")

    # 수동 검수 대상 sample 출력
    if n_multi > 0:
        print()
        print("=" * 80)
        print(f"수동 검수 필요 작가 sample ({n_multi}명 중 상위 8명)")
        print("=" * 80)
        for name in manual_df["artist_name_ko_orig"].drop_duplicates().head(8):
            sub = manual_df[manual_df["artist_name_ko_orig"] == name]
            print(f"\n● {name}")
            for _, r in sub.iterrows():
                print(f"  {r['artist_name_ko']:<15s} {r['platform']:<8s} "
                      f"n={r['n_works']:>3} median={r['median_krw']:>14,.0f}원  "
                      f"{r['profile_url']}")


if __name__ == "__main__":
    main()
