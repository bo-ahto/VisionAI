"""Track 3 PR16e — 수동 검수 결과 적용 + 데이터셋 재정비.

작업:
1. data/homonym_review/동명이인수작업 - manual_review.csv 의 메모를 파싱
2. unified v2 의 동명이인 분리를 메모대로 재정리
3. unified v3 parquet/csv 저장 (모든 정보 보존)
4. release_split CSV 3개 재생성 — 학습용 11개 컬럼만 (사용자 요청: 최소화)

메모 액션:
  o                          → 그대로 (별개 작가 확정)
  "X와 같은작가"               → X로 통합 (공백 변형 허용)
  "o_한글명 X로 변경"         → 한글명 자체 정정 + 동명이인 묶음 유지
  "X 인데 작가 이름 잘못 기입" → 한글명 완전 다른 사람 (별개 작가, is_homonym=False)
  "o_X 인데 작가 이름 잘못 기입" → 한글명 정정 + 각자 별개
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
SRC_PARQUET = DATA / "track3_unified_v2.parquet"
REVIEW_CSV = DATA / "homonym_review" / "동명이인수작업 - manual_review.csv"
OUT_PARQUET = DATA / "track3_unified_v3.parquet"
OUT_CSV_FULL = DATA / "track3_unified_v3.csv"
SPLIT_DIR = DATA / "release_split"

ARTIST_COL = "artist_name_ko"
SOURCE_COL = "source_platform"
ENTITY_COL = "artist_entity_id_raw"
TARGET = "ln_price_krw_unified"
SEED = 42

# 학습용 release_split CSV 컬럼 (최소화)
KEEP_COLS = [
    "artist_name_ko",          # 분리 ID (학습용 작가 식별자)
    "medium_category", "support_category",
    "depth_cm", "width_cm", "height_cm",
    "log_area", "estimated_ho", "orientation",
    "price_krw_unified",       # 원본 KRW (평가용)
    "ln_price_krw_unified",    # 학습 target
]

N_COLD_ARTISTS = 200
WARM_PER_ARTIST = 1


def parse_memo(memo: str) -> tuple[str | None, str | None, bool, str]:
    """메모 → (target_id, target_orig, is_homonym, action_type).
    target_id/orig이 None이면 그대로 유지."""
    if not isinstance(memo, str):
        return None, None, True, "KEEP"
    memo = memo.strip()
    if memo == "o" or memo == "":
        return None, None, True, "KEEP"

    # MERGE: "X_S와 같은작가" or "X_S 와 같은작가"
    m = re.match(r"^(\S+?)\s*와\s*같은작가", memo)
    if m:
        target = m.group(1).strip()
        target_orig = target.rsplit("_", 1)[0]
        return target, target_orig, True, "MERGE"

    # RENAME_KEEP: "o_한글명 X_S로 변경"
    m = re.search(r"한글명\s+(\S+?)_(\S+?)로\s*변경", memo)
    if m:
        new_orig = m.group(1).strip()
        new_suffix = m.group(2).strip()
        return f"{new_orig}_{new_suffix}", new_orig, True, "RENAME_KEEP"

    # DIFFERENT_ARTIST: "X 인데 작가 이름이 잘못 기입됨" (o_ prefix 없음)
    if not memo.startswith("o_"):
        m = re.match(r"^(\S+?)\s+인데\s+작가\s+이름이\s+잘못\s+기입됨", memo)
        if m:
            new_orig = m.group(1).strip()
            return new_orig, new_orig, False, "DIFFERENT"

    # RENAME_KEEP_INDIV: "o_X_S 인데 작가 이름 잘못 기입됨"
    m = re.search(r"o_(\S+?)_(\S+?)\s+인데", memo)
    if m:
        new_orig = m.group(1).strip()
        new_suffix = m.group(2).strip()
        return f"{new_orig}_{new_suffix}", new_orig, True, "RENAME_INDIV"

    logger.warning(f"미매칭 메모: {memo!r}")
    return None, None, True, "UNKNOWN"


def build_apply_map(review_df: pd.DataFrame) -> dict:
    """(artist_name_ko 분리 ID, source, entity_id) → (new_id, new_orig, is_homonym)."""
    m = {}
    for _, row in review_df.iterrows():
        key = (row["artist_name_ko"], row["platform"], str(row["entity_id_raw"]))
        target_id, target_orig, is_homo, action = parse_memo(row.get("동명이인 메모"))
        if target_id is None:
            # KEEP — 그대로
            target_id = row["artist_name_ko"]
            target_orig = row["artist_name_ko_orig"]
        m[key] = {
            "new_id": target_id,
            "new_orig": target_orig,
            "is_homonym": is_homo,
            "action": action,
        }
    return m


def apply_review(df: pd.DataFrame, apply_map: dict) -> pd.DataFrame:
    df = df.copy()

    def transform(row):
        key = (row[ARTIST_COL], row[SOURCE_COL], str(row[ENTITY_COL]))
        if key in apply_map:
            r = apply_map[key]
            return pd.Series({
                "new_artist_name_ko": r["new_id"],
                "new_orig": r["new_orig"],
                "new_is_homonym": r["is_homonym"],
            })
        # manual_review 대상 아님 → 그대로 (single_platform 또는 비동명이인)
        return pd.Series({
            "new_artist_name_ko": row[ARTIST_COL],
            "new_orig": row.get("artist_name_ko_orig", row[ARTIST_COL]),
            "new_is_homonym": row.get("is_homonym", False),
        })

    new = df.apply(transform, axis=1)
    df[ARTIST_COL] = new["new_artist_name_ko"]
    df["artist_name_ko_orig"] = new["new_orig"]
    df["is_homonym"] = new["new_is_homonym"]

    # artist_entity_suffix 재계산 (분리 ID에서 추출, 분리 안 된 작가는 "")
    def get_suffix(name_id, orig):
        if name_id != orig and name_id.startswith(orig + "_"):
            return name_id[len(orig) + 1:]
        return ""
    df["artist_entity_suffix"] = df.apply(
        lambda r: get_suffix(r[ARTIST_COL], r["artist_name_ko_orig"]), axis=1)

    return df


def regenerate_release_split(df: pd.DataFrame, out_dir: Path) -> dict:
    """release_split 재생성. 학습용 11개 컬럼만 유지."""
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
    cold_set = set(cold_artists)

    test_cold = df[df[ARTIST_COL].isin(cold_set)].copy()
    remaining = df[~df[ARTIST_COL].isin(cold_set)].copy()

    rem_counts = remaining.groupby(ARTIST_COL).size()
    multi_artists = rem_counts[rem_counts >= 2].index.tolist()
    warm_idx = []
    for artist in multi_artists:
        artist_rows = remaining[remaining[ARTIST_COL] == artist]
        sampled = rng.choice(artist_rows.index, size=WARM_PER_ARTIST, replace=False)
        warm_idx.extend(sampled.tolist())

    test_warm = remaining.loc[warm_idx].copy()
    train = remaining.drop(warm_idx).copy()

    # Sanity check
    assert set(train[ARTIST_COL]) & set(test_cold[ARTIST_COL]) == set()
    assert set(test_warm[ARTIST_COL]).issubset(set(train[ARTIST_COL]))

    # 학습용 컬럼만 유지
    for d_name, d in [("train", train), ("test_warm", test_warm), ("test_cold", test_cold)]:
        cols = [c for c in KEEP_COLS if c in d.columns]
        d_min = d[cols].copy()
        if d_name == "train":
            train = d_min
        elif d_name == "test_warm":
            test_warm = d_min
        else:
            test_cold = d_min

    out_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(out_dir / "track3_train.csv", index=False, encoding="utf-8-sig")
    test_warm.to_csv(out_dir / "track3_test_warm.csv", index=False, encoding="utf-8-sig")
    test_cold.to_csv(out_dir / "track3_test_cold.csv", index=False, encoding="utf-8-sig")

    meta = {
        "seed": SEED, "n_cold_artists": N_COLD_ARTISTS, "warm_per_artist": WARM_PER_ARTIST,
        "homonym_handling": "PR16e v3: manual review 적용 + 한글명 정정 (유수즈이→유수지, 이효윤→이효연, 이진우_B→이우진)",
        "keep_cols": KEEP_COLS,
        "n_cols": len(KEEP_COLS),
        "train": {"n_rows": int(len(train)), "n_artists": int(train[ARTIST_COL].nunique())},
        "test_warm": {"n_rows": int(len(test_warm)), "n_artists": int(test_warm[ARTIST_COL].nunique())},
        "test_cold": {"n_rows": int(len(test_cold)), "n_artists": int(test_cold[ARTIST_COL].nunique()),
                       "stratification": {"low": n_low, "mid": n_mid, "high": n_high}},
    }
    (out_dir / "split_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return {"train": train, "test_warm": test_warm, "test_cold": test_cold, "meta": meta}


def main():
    logger.info("=" * 70)
    logger.info("Track 3 PR16e — Manual review 적용 + 데이터셋 v3 재정비")
    logger.info("=" * 70)

    df = pd.read_parquet(SRC_PARQUET)
    review = pd.read_csv(REVIEW_CSV)
    logger.info(f"unified v2: {len(df):,} rows / {df[ARTIST_COL].nunique():,} 분리 ID")
    logger.info(f"manual_review: {len(review)} entity rows")

    # 메모 액션 분포
    actions = {"KEEP": 0, "MERGE": 0, "RENAME_KEEP": 0, "DIFFERENT": 0,
               "RENAME_INDIV": 0, "UNKNOWN": 0}
    for _, row in review.iterrows():
        _, _, _, action = parse_memo(row.get("동명이인 메모"))
        actions[action] += 1
    logger.info(f"Action 분포: {actions}")

    # 적용
    apply_map = build_apply_map(review)
    df_v3 = apply_review(df, apply_map)

    # 변경 사항 검증
    n_orig = df[ARTIST_COL].nunique()
    n_v3 = df_v3[ARTIST_COL].nunique()
    logger.info(f"\n작가 ID 수: {n_orig} → {n_v3} ({n_v3 - n_orig:+d})")

    # 한글명 정정 검증
    print()
    print("=" * 80)
    print("한글명 정정 결과")
    print("=" * 80)
    for orig in ["유수즈이", "이효윤"]:
        n_old = (df["artist_name_ko_orig"] == orig).sum()
        new_name = {"유수즈이": "유수지", "이효윤": "이효연"}[orig]
        n_new = (df_v3["artist_name_ko_orig"] == new_name).sum()
        print(f"  {orig}({n_old}건) → {new_name}({n_new}건)")
    # 이진우_B → 이우진 (부분 정정)
    n_yj_b = ((df["artist_name_ko_orig"] == "이진우") & (df["artist_name_ko"] == "이진우_B")).sum()
    n_uj = (df_v3["artist_name_ko_orig"] == "이우진").sum()
    print(f"  이진우_B({n_yj_b}건) → 이우진({n_uj}건)")

    # is_homonym 분포 변화
    logger.info(f"\nis_homonym 변화: {df['is_homonym'].sum():,} → {df_v3['is_homonym'].sum():,}")

    # 저장
    df_v3.to_parquet(OUT_PARQUET, index=False)
    df_v3.to_csv(OUT_CSV_FULL, index=False, encoding="utf-8-sig")
    logger.info(f"\n✅ Saved: {OUT_PARQUET}")
    logger.info(f"✅ Saved: {OUT_CSV_FULL}")

    # release_split 재생성
    logger.info("\n" + "=" * 70)
    logger.info("release_split 재생성 (학습용 11개 컬럼만)")
    logger.info("=" * 70)
    result = regenerate_release_split(df_v3, SPLIT_DIR)
    print()
    print("=" * 80)
    print("📦 release_split v3 (학습용 11개 컬럼)")
    print("=" * 80)
    for name in ["train", "test_warm", "test_cold"]:
        d = result[name]
        print(f"  {name:<12} {len(d):>6,} rows / {d[ARTIST_COL].nunique():>5} artists / {len(d.columns)} cols")
    print(f"  KEEP_COLS: {KEEP_COLS}")


if __name__ == "__main__":
    main()
