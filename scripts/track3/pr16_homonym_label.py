"""Track 3 PR16 — 동명이인 작가 분리 라벨링.

사용자 요청:
  원본 데이터의 source_platform + artist_entity_id_raw 기반으로 동명이인을 식별하고,
  한글명 뒤에 _A/_B/_C... suffix를 붙여 명확하게 구분. 동명이인 여부를 표시하는
  컬럼(is_homonym)도 추가.

설계:
  TRUE_homonym 식별 기준 (PR13와 동일):
    - 같은 artist_name_ko 안에 entity_id가 ≥2개
    - 그중 보조 entity 중 ≥3건인 것이 1개 이상
    - entity별 median price CV > 0.5 (가격대 다름)

  분리 라벨링:
    entity 작품수 내림차순으로 정렬
    가장 많은 entity = 한글명_A
    다음 = 한글명_B, _C, _D...

  새 컬럼:
    artist_name_ko_orig: 원본 한글명 (보존)
    artist_name_ko: 분리 ID로 갱신 (학습 / API 호환성을 위해)
    is_homonym: bool (TRUE_homonym 작가 작품이면 True)
    artist_entity_suffix: "A" / "B" / "C"... (분리 안 된 작가는 "")

출력:
  data/track3_unified_v2.parquet (라벨링된 unified)
  data/release_split/ (재생성된 train/test_warm/test_cold CSV)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
SRC_PARQUET = REPO / "data" / "track3_unified_v1.parquet"
OUT_PARQUET = REPO / "data" / "track3_unified_v2.parquet"
SPLIT_DIR = REPO / "data" / "release_split"

ARTIST_COL = "artist_name_ko"
SOURCE_COL = "source_platform"
ENTITY_COL = "artist_entity_id_raw"
PRICE_COL = "price_krw_unified"
TARGET = "ln_price_krw_unified"
SEED = 42

N_MIN_SECONDARY = 3   # 보조 entity ≥3건이면 분리 대상 (PR13 기준)
CV_THRESHOLD = 0.5    # entity별 median price CV > 0.5이면 가격대 다름

# release_split 재생성 설정 (split_for_release.py와 동일)
N_COLD_ARTISTS = 200
WARM_PER_ARTIST = 1
KEEP_COLS = [
    "artist_name_ko", "artist_name_ko_orig", "is_homonym", "artist_entity_suffix",
    "medium_category", "support_category",
    "has_depth", "depth_cm", "width_cm", "height_cm",
    "log_area", "estimated_ho", "orientation",
    "price_krw_unified", "ln_price_krw_unified",
]


def identify_and_label_homonyms(df: pd.DataFrame) -> tuple[pd.DataFrame, list, dict]:
    """TRUE_homonym 식별 + 분리 라벨링.

    Returns:
        labeled_df: artist_name_ko가 분리 ID로 갱신된 DataFrame
                   + artist_name_ko_orig (원본 보존)
                   + is_homonym (bool)
                   + artist_entity_suffix ("A"/"B"/.../"" 분리 안 된 경우)
        homonym_artists: TRUE_homonym 작가 한글명 list
        homonym_map: (한글명, entity_id) → (new_id, suffix) dict
    """
    homonym_artists = []
    homonym_map = {}

    for name, group in df.groupby(ARTIST_COL):
        entities = group.groupby(ENTITY_COL).agg(
            n=("artist_name_raw", "size"),
            median_price=(PRICE_COL, "median"),
        ).reset_index().sort_values("n", ascending=False)

        if len(entities) <= 1:
            continue

        secondary_multi = entities.iloc[1:][entities.iloc[1:]["n"] >= N_MIN_SECONDARY]
        prices = entities["median_price"].dropna()
        cv = float(prices.std() / max(prices.mean(), 1)) if len(prices) >= 2 else 0.0

        if len(secondary_multi) >= 1 and cv > CV_THRESHOLD:
            homonym_artists.append(name)
            for i, (_, row) in enumerate(entities.iterrows()):
                eid = row[ENTITY_COL]
                # A, B, C, D... (Z까지 26개, 그 이상은 AA, AB...)
                suffix = _idx_to_suffix(i)
                new_id = f"{name}_{suffix}"
                homonym_map[(name, eid)] = (new_id, suffix)

    # 라벨링 적용
    df = df.copy()
    df["artist_name_ko_orig"] = df[ARTIST_COL]  # 원본 보존

    def apply_label(row):
        key = (row[ARTIST_COL], row[ENTITY_COL])
        if key in homonym_map:
            return homonym_map[key]
        return (row[ARTIST_COL], "")

    labels = df.apply(apply_label, axis=1)
    df[ARTIST_COL] = labels.apply(lambda x: x[0])
    df["artist_entity_suffix"] = labels.apply(lambda x: x[1])
    df["is_homonym"] = df["artist_name_ko_orig"].isin(set(homonym_artists))

    return df, homonym_artists, homonym_map


def _idx_to_suffix(idx: int) -> str:
    """0 → A, 1 → B, ... 25 → Z, 26 → AA, 27 → AB ..."""
    chars = []
    n = idx
    while True:
        chars.append(chr(ord("A") + n % 26))
        n = n // 26 - 1
        if n < 0:
            break
    return "".join(reversed(chars))


def regenerate_release_split(df: pd.DataFrame) -> dict:
    """release_split 재생성 (split_for_release.py 동일 로직, 새 ID 기준).

    is_outlier=0 필터링 후 진행.
    """
    df = df[df["is_outlier"] == 0].reset_index(drop=True)
    rng = np.random.default_rng(SEED)

    # Cold test 작가 200명 stratified sampling
    artist_counts = df.groupby(ARTIST_COL).size().sort_values()
    all_artists = artist_counts.index.tolist()
    artists_low = [a for a in all_artists if artist_counts[a] <= 2]
    artists_mid = [a for a in all_artists if 3 <= artist_counts[a] <= 10]
    artists_high = [a for a in all_artists if artist_counts[a] > 10]

    n_low = int(N_COLD_ARTISTS * 0.5)
    n_mid = int(N_COLD_ARTISTS * 0.3)
    n_high = N_COLD_ARTISTS - n_low - n_mid

    cold_artists = (
        list(rng.choice(artists_low, size=min(n_low, len(artists_low)), replace=False)) +
        list(rng.choice(artists_mid, size=min(n_mid, len(artists_mid)), replace=False)) +
        list(rng.choice(artists_high, size=min(n_high, len(artists_high)), replace=False))
    )
    cold_artists_set = set(cold_artists)

    test_cold_df = df[df[ARTIST_COL].isin(cold_artists_set)].copy()
    remaining_df = df[~df[ARTIST_COL].isin(cold_artists_set)].copy()

    # Warm test: 작가 ≥2건 중 1건씩
    remaining_counts = remaining_df.groupby(ARTIST_COL).size()
    multi_artists = remaining_counts[remaining_counts >= 2].index.tolist()

    warm_test_indices = []
    for artist in multi_artists:
        artist_rows = remaining_df[remaining_df[ARTIST_COL] == artist]
        sampled_idx = rng.choice(artist_rows.index, size=WARM_PER_ARTIST, replace=False)
        warm_test_indices.extend(sampled_idx.tolist())

    test_warm_df = remaining_df.loc[warm_test_indices].copy()
    train_df = remaining_df.drop(warm_test_indices).copy()

    # 학습 외 메타 컬럼 제거 (KEEP_COLS만 유지)
    for d_name, d in [("train", train_df), ("test_warm", test_warm_df), ("test_cold", test_cold_df)]:
        cols_keep = [c for c in KEEP_COLS if c in d.columns]
        if d_name == "train":
            train_df = d[cols_keep].copy()
        elif d_name == "test_warm":
            test_warm_df = d[cols_keep].copy()
        else:
            test_cold_df = d[cols_keep].copy()

    # Sanity check
    assert set(train_df[ARTIST_COL]) & set(test_cold_df[ARTIST_COL]) == set(), \
        "train ∩ test_cold 작가 겹침 발견!"
    assert set(test_warm_df[ARTIST_COL]).issubset(set(train_df[ARTIST_COL])), \
        "test_warm 작가가 train에 없음!"

    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(SPLIT_DIR / "track3_train.csv", index=False, encoding="utf-8-sig")
    test_warm_df.to_csv(SPLIT_DIR / "track3_test_warm.csv", index=False, encoding="utf-8-sig")
    test_cold_df.to_csv(SPLIT_DIR / "track3_test_cold.csv", index=False, encoding="utf-8-sig")

    meta = {
        "seed": SEED, "n_cold_artists": N_COLD_ARTISTS, "warm_per_artist": WARM_PER_ARTIST,
        "homonym_handling": "PR16 v2: TRUE_homonym 38명 entity_id 기반 _A/_B/_C... 분리",
        "train": {"n_rows": int(len(train_df)),
                  "n_artists": int(train_df[ARTIST_COL].nunique())},
        "test_warm": {"n_rows": int(len(test_warm_df)),
                       "n_artists": int(test_warm_df[ARTIST_COL].nunique())},
        "test_cold": {"n_rows": int(len(test_cold_df)),
                       "n_artists": int(test_cold_df[ARTIST_COL].nunique()),
                       "stratification": {"low": n_low, "mid": n_mid, "high": n_high}},
    }
    (SPLIT_DIR / "split_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False))

    return {
        "train": train_df, "test_warm": test_warm_df, "test_cold": test_cold_df,
        "meta": meta,
    }


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR16 — 동명이인 분리 라벨링 (_A/_B/_C... suffix)")
    logger.info("=" * 70)

    df = pd.read_parquet(SRC_PARQUET)
    logger.info(f"원본: {len(df):,} 작품 / {df[ARTIST_COL].nunique():,} 작가")
    logger.info(f"Sources: {dict(df[SOURCE_COL].value_counts())}")

    # 1. 분리 라벨링
    df_labeled, homonym_artists, homonym_map = identify_and_label_homonyms(df)
    n_split_entities = len(homonym_map)
    n_new_artists = df_labeled[ARTIST_COL].nunique()
    logger.info(f"\nTRUE_homonym 식별: {len(homonym_artists)} 명")
    logger.info(f"분리된 entity 매핑: {n_split_entities} (모두 _A/_B/_C... 부여)")
    logger.info(f"작가 ID 수: {df[ARTIST_COL].nunique()} → {n_new_artists} "
                f"(+{n_new_artists - df[ARTIST_COL].nunique()})")
    logger.info(f"is_homonym=True 작품: {df_labeled['is_homonym'].sum():,} "
                f"({100*df_labeled['is_homonym'].mean():.2f}%)")

    # Sample 출력
    print()
    print("=" * 80)
    print(f"분리 라벨 sample (Top 8 TRUE_homonym 작가)")
    print("=" * 80)
    for name in homonym_artists[:8]:
        rows = df_labeled[df_labeled["artist_name_ko_orig"] == name]
        new_ids = rows.groupby(ARTIST_COL).agg(
            n=("artist_entity_suffix", "size"),
            source=(SOURCE_COL, lambda s: dict(s.value_counts())),
        ).reset_index().sort_values("n", ascending=False)
        print(f"\n'{name}' → {len(new_ids)} 개로 분리:")
        for _, r in new_ids.iterrows():
            srcs = ", ".join([f"{k}={v}" for k, v in r["source"].items()])
            print(f"  {r[ARTIST_COL]:<20s} {r['n']:>3}건 (sources: {srcs})")

    # 2. unified v2 parquet 저장
    df_labeled.to_parquet(OUT_PARQUET, index=False)
    logger.info(f"\n✅ Saved: {OUT_PARQUET}")

    # 3. release_split 재생성
    logger.info("\n" + "=" * 70)
    logger.info("release_split 재생성 (새 ID 기준)")
    logger.info("=" * 70)
    result = regenerate_release_split(df_labeled)
    print()
    print("=" * 80)
    print("📦 release_split 재생성 완료")
    print("=" * 80)
    for name in ["train", "test_warm", "test_cold"]:
        d = result[name]
        n_homo = int(d["is_homonym"].sum())
        print(f"  {name:<12} {len(d):>6,} rows / {d[ARTIST_COL].nunique():>5} artists "
              f"(homonym 작품 {n_homo})")
    logger.info("✅ release_split CSV 3개 재생성 완료")


if __name__ == "__main__":
    main()
