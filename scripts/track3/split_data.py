"""Track 3 — Phase 0 data split.

Plan v2.1 §3.1에 정의된 split 전략 구현:
1. Outer holdout: 작가 20% 격리 (최초 1회, Phase 5 최종 평가용)
2. Cold (PRIMARY): dev_pool 작가들로 GroupKFold(5)
3. Warm (SECONDARY): dev_pool 작품들로 random 80/10/10 × N=20 seed

Output:
    data/track3_splits/
      outer_holdout_artists.json    — 격리 작가 list + dev_pool 작가 list
      cold_folds.json               — fold 0~4 train/test artist+row indices
      warm_splits.json              — seed 0~19 train/val/test row indices

재현성:
    seed 고정 (42). N=20 seed for warm은 (42, 43, ..., 61)
    GroupKFold는 deterministic (sklearn 표준).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_PATH = REPO / "data" / "track3_unified_v1_train.csv"
OUT_DIR = REPO / "data" / "track3_splits"

# 설정
SEED = 42
OUTER_HOLDOUT_FRAC = 0.20  # 작가 단위 20% 격리
COLD_N_SPLITS = 5  # GroupKFold
WARM_N_SEEDS = 20
WARM_VAL_SIZE = 0.10
WARM_TEST_SIZE = 0.10
ARTIST_COL = "artist_name_ko"


def split_outer_holdout(
    df: pd.DataFrame, frac: float = OUTER_HOLDOUT_FRAC, seed: int = SEED
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """전체 작가 중 frac(20%)를 outer holdout으로 격리 (작가 단위)."""
    artists = df[ARTIST_COL].dropna().unique()
    rng = np.random.default_rng(seed)
    rng.shuffle(artists)
    n_holdout = int(len(artists) * frac)
    holdout_artists = set(artists[:n_holdout])
    dev_artists = set(artists[n_holdout:])

    df_holdout = df[df[ARTIST_COL].isin(holdout_artists)].copy()
    df_dev = df[df[ARTIST_COL].isin(dev_artists)].copy()

    meta = {
        "seed": seed,
        "frac": frac,
        "n_artists_total": len(artists),
        "n_artists_holdout": len(holdout_artists),
        "n_artists_dev": len(dev_artists),
        "n_rows_total": len(df),
        "n_rows_holdout": len(df_holdout),
        "n_rows_dev": len(df_dev),
        "holdout_artists": sorted(holdout_artists),
        "dev_artists": sorted(dev_artists),
    }
    logger.info(
        f"Outer holdout: artists {meta['n_artists_holdout']:,}/{meta['n_artists_total']:,} "
        f"({100*meta['n_artists_holdout']/meta['n_artists_total']:.1f}%) / "
        f"rows {meta['n_rows_holdout']:,}/{meta['n_rows_total']:,} "
        f"({100*meta['n_rows_holdout']/meta['n_rows_total']:.1f}%)"
    )
    return df_dev, df_holdout, meta


def cold_groupkfold(df_dev: pd.DataFrame, n_splits: int = COLD_N_SPLITS) -> list[dict]:
    """dev_pool에 GroupKFold(artist_name_ko) 적용 → 5 folds.

    각 fold는 fold 간 작가 겹침 0% 보장.
    """
    gkf = GroupKFold(n_splits=n_splits)
    groups = df_dev[ARTIST_COL].values
    folds = []
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(df_dev, groups=groups)):
        train_artists = set(df_dev.iloc[train_idx][ARTIST_COL].unique())
        test_artists = set(df_dev.iloc[test_idx][ARTIST_COL].unique())
        overlap = train_artists & test_artists
        assert not overlap, f"Fold {fold_idx} 작가 겹침: {overlap}"
        folds.append({
            "fold": fold_idx,
            "n_train_rows": len(train_idx),
            "n_test_rows": len(test_idx),
            "n_train_artists": len(train_artists),
            "n_test_artists": len(test_artists),
            "train_indices": train_idx.tolist(),
            "test_indices": test_idx.tolist(),
        })
        logger.info(
            f"  Cold fold {fold_idx}: train {len(train_idx):,} rows "
            f"({len(train_artists):,} artists) / test {len(test_idx):,} rows "
            f"({len(test_artists):,} artists)"
        )
    return folds


def warm_random_splits(df_dev: pd.DataFrame, n_seeds: int = WARM_N_SEEDS) -> list[dict]:
    """dev_pool 작품 단위 random 80/10/10 split × N seeds."""
    splits = []
    for i in range(n_seeds):
        seed = SEED + i
        idx = np.arange(len(df_dev))
        train_val_idx, test_idx = train_test_split(
            idx, test_size=WARM_TEST_SIZE, random_state=seed
        )
        # val_size를 전체 기준 10% → train_val 안에서 비율 환산
        val_frac = WARM_VAL_SIZE / (1 - WARM_TEST_SIZE)
        train_idx, val_idx = train_test_split(
            train_val_idx, test_size=val_frac, random_state=seed
        )
        splits.append({
            "seed": seed,
            "n_train_rows": len(train_idx),
            "n_val_rows": len(val_idx),
            "n_test_rows": len(test_idx),
            "train_indices": train_idx.tolist(),
            "val_indices": val_idx.tolist(),
            "test_indices": test_idx.tolist(),
        })
    logger.info(
        f"Warm random splits: N={n_seeds} seeds, "
        f"train ~{splits[0]['n_train_rows']:,} / val ~{splits[0]['n_val_rows']:,} / "
        f"test ~{splits[0]['n_test_rows']:,} rows"
    )
    return splits


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 Phase 0 — Data Split")
    logger.info("=" * 70)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded: {len(df):,} rows / {df[ARTIST_COL].nunique():,} unique artists")

    # 1. Outer holdout 격리
    logger.info("\n--- Step 1: Outer holdout 격리 (작가 20%) ---")
    df_dev, df_holdout, outer_meta = split_outer_holdout(df)

    # dev_pool에 0~N-1 reset_index for fold indices 일관성
    df_dev = df_dev.reset_index(drop=True)
    df_holdout = df_holdout.reset_index(drop=True)

    # 2. Cold GroupKFold (dev_pool 내부)
    logger.info("\n--- Step 2: Cold GroupKFold(5) on dev_pool ---")
    cold_folds = cold_groupkfold(df_dev)

    # 3. Warm random splits (dev_pool 내부)
    logger.info("\n--- Step 3: Warm random 80/10/10 × N=20 ---")
    warm_splits = warm_random_splits(df_dev)

    # Save outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Outer holdout meta (artists만 저장, df는 source CSV로 재구성)
    outer_path = OUT_DIR / "outer_holdout_artists.json"
    outer_path.write_text(json.dumps(outer_meta, indent=2, ensure_ascii=False))
    logger.info(f"\n✅ Saved: {outer_path}")

    # Cold folds (indices만, dev_pool reset_index 기준)
    cold_path = OUT_DIR / "cold_folds.json"
    cold_path.write_text(json.dumps({
        "n_splits": COLD_N_SPLITS,
        "group_col": ARTIST_COL,
        "dev_pool_n_rows": len(df_dev),
        "folds": cold_folds,
    }, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {cold_path}")

    # Warm splits (indices만)
    warm_path = OUT_DIR / "warm_splits.json"
    warm_path.write_text(json.dumps({
        "n_seeds": WARM_N_SEEDS,
        "val_size": WARM_VAL_SIZE,
        "test_size": WARM_TEST_SIZE,
        "dev_pool_n_rows": len(df_dev),
        "splits": warm_splits,
    }, indent=2, ensure_ascii=False))
    logger.info(f"✅ Saved: {warm_path}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Phase 0 Split — Summary")
    logger.info("=" * 70)
    logger.info(f"Outer holdout: {outer_meta['n_rows_holdout']:,} rows ({outer_meta['n_artists_holdout']:,} 작가)")
    logger.info(f"Dev pool:      {outer_meta['n_rows_dev']:,} rows ({outer_meta['n_artists_dev']:,} 작가)")
    logger.info(f"  Cold folds:   {COLD_N_SPLITS} folds, fold 간 작가 겹침 0% 검증")
    logger.info(f"  Warm splits:  N={WARM_N_SEEDS} seeds × 80/10/10")


if __name__ == "__main__":
    main()
