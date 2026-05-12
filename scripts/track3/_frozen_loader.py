"""Frozen Cold Benchmark loader (F6 PR26 산출물).

향후 Track 3 실험에서 사용 — 단일 import로 frozen cold + mini_train + V0 baseline 로드.

Usage:
    from scripts.track3._frozen_loader import load_frozen_benchmark

    mini_train, cold_mini, baseline = load_frozen_benchmark()
    # mini_train: pd.DataFrame, 학습용
    # cold_mini: pd.DataFrame, frozen cold test
    # baseline['ape_array']: V0 baseline 예측 APE (paired 비교용)
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
SPLIT_DIR = REPO / "data" / "track3_splits"
BASELINE_PATH = REPO / "data" / "track3_pr26_baseline_cache.json"


def load_frozen_benchmark():
    """Returns (mini_train, cold_mini, baseline_dict)."""
    mini_train = pd.read_csv(SPLIT_DIR / "frozen_mini_train.csv")
    cold_mini = pd.read_csv(SPLIT_DIR / "frozen_mini_cold.csv")
    baseline = json.loads(BASELINE_PATH.read_text())
    return mini_train, cold_mini, baseline


if __name__ == "__main__":
    mt, cm, bl = load_frozen_benchmark()
    print(f"mini_train: {len(mt):,} rows / {mt['artist_name_ko'].nunique():,} artists")
    print(f"cold_mini : {len(cm):,} rows / {cm['artist_name_ko'].nunique():,} artists")
    print(f"V0 cold baseline med_APE: {bl['cold_baseline']['median_ape']:.4f}")
