"""Track 3 — 영구 데이터 분리 (release용).

Codex 권장 (Hybrid 분리):
- train: 학습용
- test_warm: 학습 작가별 1건 빼두기 (작가 ≥2건만) — 학습된 작가 신규 작품 평가
- test_cold: 완전 unseen 작가 (~200명) — 진짜 신규 작가 평가

Leakage 방지:
- split 먼저, 모든 transform (categorical fit, scaler, aggregate) 은 train만 보고
- artist_works_log 등 train-derived feature는 split 후 재계산
- 분리 결과는 영구 (3 CSV 파일로 저장)

설계:
- cold 작가 200명 선정 → 그 작가들의 모든 작품 = test_cold
- 남은 작가 중 작품 ≥2건인 작가에서 1건씩 빼서 test_warm
- 나머지 = train

균형:
- Cold 작가 선정: source × ho_bucket 층화 sampling 시도 (분포 보존)
- Warm 빼는 작품: random 선정
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
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
OUT_DIR = REPO / "data" / "release_split"

ARTIST_COL = "artist_name_ko"
SOURCE_COL = "source_platform"
TARGET = "ln_price_krw_unified"
PRICE_COL = "price_krw_unified"

SEED = 42
N_COLD_ARTISTS = 200  # ~200 작가를 cold test로
WARM_PER_ARTIST = 1  # 작가별 1건 warm test로


def main():
    logger.info("=" * 70)
    logger.info("Track 3 — Release Split (Codex 권장 Hybrid)")
    logger.info("=" * 70)

    df = pd.read_csv(DATA_PATH)
    df = df[df["is_outlier"] == 0].reset_index(drop=True)
    logger.info(f"전체 (is_outlier=0): {len(df):,} 작품 / {df[ARTIST_COL].nunique():,} 작가")

    rng = np.random.default_rng(SEED)

    # ─── Step 1: Cold test 작가 선정 (200명) ───
    artist_counts = df.groupby(ARTIST_COL).size().sort_values()
    all_artists = artist_counts.index.tolist()

    # 작가별 작품수 분포 균형 (singleton/소수/다수 모두 cold에 포함)
    # → 단순 random sampling이지만 작품수 stratified
    artists_low = [a for a in all_artists if artist_counts[a] <= 2]      # ≤2건
    artists_mid = [a for a in all_artists if 3 <= artist_counts[a] <= 10]  # 3-10건
    artists_high = [a for a in all_artists if artist_counts[a] > 10]      # >10건

    # 비율: cold test에 low 50% / mid 30% / high 20%
    n_low = int(N_COLD_ARTISTS * 0.5)   # 100명
    n_mid = int(N_COLD_ARTISTS * 0.3)   # 60명
    n_high = N_COLD_ARTISTS - n_low - n_mid  # 40명

    cold_artists = (
        list(rng.choice(artists_low, size=min(n_low, len(artists_low)), replace=False)) +
        list(rng.choice(artists_mid, size=min(n_mid, len(artists_mid)), replace=False)) +
        list(rng.choice(artists_high, size=min(n_high, len(artists_high)), replace=False))
    )
    cold_artists_set = set(cold_artists)
    logger.info(f"Cold test 작가: {len(cold_artists)} (low {len(artists_low)} / "
                f"mid {len(artists_mid)} / high {len(artists_high)} 중)")

    # Cold test = 이 작가들의 모든 작품
    test_cold_df = df[df[ARTIST_COL].isin(cold_artists_set)].copy()
    remaining_df = df[~df[ARTIST_COL].isin(cold_artists_set)].copy()
    logger.info(f"  test_cold: {len(test_cold_df):,} 작품 / {test_cold_df[ARTIST_COL].nunique()} 작가")
    logger.info(f"  remaining: {len(remaining_df):,} 작품 / {remaining_df[ARTIST_COL].nunique()} 작가")

    # ─── Step 2: Warm test 작품 선정 (작가별 1건, 작가 ≥2건만) ───
    # remaining의 ≥2건 작가들에서 작가별 random 1개씩 빼기
    remaining_counts = remaining_df.groupby(ARTIST_COL).size()
    multi_artists = remaining_counts[remaining_counts >= 2].index.tolist()
    logger.info(f"Warm 후보 작가 (≥2건): {len(multi_artists):,}")

    warm_test_indices = []
    for artist in multi_artists:
        artist_rows = remaining_df[remaining_df[ARTIST_COL] == artist]
        # random 1건 선택
        sampled_idx = rng.choice(artist_rows.index, size=WARM_PER_ARTIST, replace=False)
        warm_test_indices.extend(sampled_idx.tolist())

    test_warm_df = remaining_df.loc[warm_test_indices].copy()
    train_df = remaining_df.drop(warm_test_indices).copy()
    logger.info(f"  test_warm: {len(test_warm_df):,} 작품 / {test_warm_df[ARTIST_COL].nunique()} 작가")
    logger.info(f"  train: {len(train_df):,} 작품 / {train_df[ARTIST_COL].nunique()} 작가")

    # ─── Sanity check: 작가 overlap ───
    train_artists = set(train_df[ARTIST_COL])
    warm_artists = set(test_warm_df[ARTIST_COL])
    cold_artists_check = set(test_cold_df[ARTIST_COL])

    assert len(train_artists & cold_artists_check) == 0, "train과 test_cold 작가 겹침 발견!"
    assert warm_artists.issubset(train_artists), "test_warm 작가가 train에 모두 있어야 함!"
    logger.info("\n✅ Sanity check 통과:")
    logger.info(f"   train ∩ test_cold artists = 0 (완전 분리)")
    logger.info(f"   test_warm artists ⊂ train artists (모두 학습됨)")

    # ─── 분포 점검 ───
    print()
    print("=" * 80)
    print("📊 분리 결과")
    print("=" * 80)
    for name, d in [("train", train_df), ("test_warm", test_warm_df), ("test_cold", test_cold_df)]:
        print(f"\n[{name}] {len(d):,} 작품 / {d[ARTIST_COL].nunique():,} 작가")
        print(f"  Source: {dict(d[SOURCE_COL].value_counts())}")
        print(f"  Price median: {d[PRICE_COL].median():,.0f}원")
        print(f"  Price Q25/Q75: {d[PRICE_COL].quantile(0.25):,.0f} / {d[PRICE_COL].quantile(0.75):,.0f}")

    # ─── source_platform 컬럼 제거 (사용자 요청: 모델이 source 정보 참고하면 안 됨) ───
    COL_DROP = "source_platform"
    for d_name, d in [("train", train_df), ("test_warm", test_warm_df), ("test_cold", test_cold_df)]:
        if COL_DROP in d.columns:
            d.drop(columns=[COL_DROP], inplace=True)
    logger.info(f"\n⚠️  source_platform 컬럼 제거 (CSV에서 영구 삭제)")

    # ─── Save ───
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(OUT_DIR / "track3_train.csv", index=False, encoding="utf-8-sig")
    test_warm_df.to_csv(OUT_DIR / "track3_test_warm.csv", index=False, encoding="utf-8-sig")
    test_cold_df.to_csv(OUT_DIR / "track3_test_cold.csv", index=False, encoding="utf-8-sig")

    meta = {
        "seed": SEED,
        "n_cold_artists": N_COLD_ARTISTS,
        "warm_per_artist": WARM_PER_ARTIST,
        "train": {"n_rows": int(len(train_df)), "n_artists": int(train_df[ARTIST_COL].nunique())},
        "test_warm": {
            "n_rows": int(len(test_warm_df)),
            "n_artists": int(test_warm_df[ARTIST_COL].nunique()),
            "description": "학습된 작가별 1건 — warm-start eval",
        },
        "test_cold": {
            "n_rows": int(len(test_cold_df)),
            "n_artists": int(test_cold_df[ARTIST_COL].nunique()),
            "description": "완전 unseen 작가 — cold-start eval",
            "stratification": {"low (≤2건)": n_low, "mid (3-10건)": n_mid, "high (>10건)": n_high},
        },
        "leakage_prevention": [
            "train과 test_cold 작가 100% 분리 (overlap 0)",
            "test_warm 작가는 train에 ≥1건 남아 있음 (warm 평가 가능)",
            "사용 시 categorical fit/scaler 등은 train만 보고 fit, test에 apply",
            "artist_works_log 등 aggregate feature는 split 후 train만으로 재계산",
        ],
    }
    (OUT_DIR / "split_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False)
    )

    print()
    print("=" * 80)
    print(f"✅ Saved to: {OUT_DIR}")
    print("=" * 80)
    print(f"  track3_train.csv      {len(train_df):,} rows  ({100*len(train_df)/len(df):.1f}%)")
    print(f"  track3_test_warm.csv  {len(test_warm_df):,} rows  ({100*len(test_warm_df)/len(df):.1f}%)")
    print(f"  track3_test_cold.csv  {len(test_cold_df):,} rows  ({100*len(test_cold_df)/len(df):.1f}%)")
    print(f"  split_metadata.json")
    print()
    print(f"Test 총량: {len(test_warm_df) + len(test_cold_df):,} rows "
          f"({100*(len(test_warm_df) + len(test_cold_df))/len(df):.1f}%)")


if __name__ == "__main__":
    main()
