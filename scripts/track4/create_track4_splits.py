"""Create Track 4 train/validation/test splits with Warm/Cold evaluation sets."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
OUT_DIR = REPO / "data" / "track4_split"
OUT_MD = REPO / "docs" / "track4_split_report.md"
OUT_JSON = OUT_DIR / "track4_split_summary.json"
RANDOM_SEED = 20260515


def sample_artists(artists: np.ndarray, n: int, rng: np.random.Generator) -> set[str]:
    if n <= 0:
        return set()
    n = min(n, len(artists))
    return set(rng.choice(artists, size=n, replace=False).tolist())


def pick_one_per_artist(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for _, group in df.groupby("artist_key", sort=False):
        rows.append(group.sample(n=1, random_state=int(rng.integers(0, 2**31 - 1))).index[0])
    return df.loc[rows].copy()


def create_splits(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(RANDOM_SEED)
    work = df.loc[df["is_training_candidate"].astype(str).str.lower().eq("true")].copy()
    work = work.loc[work["artist_key"].fillna("").astype(str).ne("")]
    artist_counts = work["artist_key"].value_counts()
    artists = artist_counts.index.to_numpy()

    n_cold_test = max(1, int(round(len(artists) * 0.10)))
    n_cold_val = max(1, int(round(len(artists) * 0.05)))
    cold_test_artists = sample_artists(artists, n_cold_test, rng)
    remaining_artists = np.array([a for a in artists if a not in cold_test_artists])
    cold_val_artists = sample_artists(remaining_artists, n_cold_val, rng)

    cold_test = work.loc[work["artist_key"].isin(cold_test_artists)].copy()
    cold_val = work.loc[work["artist_key"].isin(cold_val_artists)].copy()
    train_pool = work.loc[~work["artist_key"].isin(cold_test_artists | cold_val_artists)].copy()

    warm_eligible = train_pool["artist_key"].value_counts()
    warm_eligible = warm_eligible[warm_eligible >= 3].index.to_numpy()
    warm_test_artists = sample_artists(warm_eligible, max(1, int(round(len(warm_eligible) * 0.10))), rng)
    warm_remaining = np.array([a for a in warm_eligible if a not in warm_test_artists])
    warm_val_artists = sample_artists(warm_remaining, max(1, int(round(len(warm_eligible) * 0.05))), rng)

    warm_test = pick_one_per_artist(train_pool.loc[train_pool["artist_key"].isin(warm_test_artists)], rng)
    warm_val = pick_one_per_artist(train_pool.loc[train_pool["artist_key"].isin(warm_val_artists)], rng)
    holdout_idx = set(warm_test.index) | set(warm_val.index)
    train = train_pool.loc[~train_pool.index.isin(holdout_idx)].copy()

    return {
        "train": train,
        "val_warm": warm_val,
        "val_cold": cold_val,
        "test_warm": warm_test,
        "test_cold": cold_test,
    }


def summarize(splits: dict[str, pd.DataFrame]) -> dict:
    summary = {
        "created_at": "2026-05-15",
        "input": str(INPUT.relative_to(REPO)),
        "random_seed": RANDOM_SEED,
        "files": {},
    }
    for name, frame in splits.items():
        path = OUT_DIR / f"track4_{name}.csv"
        summary["files"][name] = {
            "path": str(path.relative_to(REPO)),
            "rows": int(len(frame)),
            "artists": int(frame["artist_key"].nunique()),
        }
    train_artists = set(splits["train"]["artist_key"])
    summary["checks"] = {
        "val_cold_overlap_train_artists": int(len(train_artists & set(splits["val_cold"]["artist_key"]))),
        "test_cold_overlap_train_artists": int(len(train_artists & set(splits["test_cold"]["artist_key"]))),
        "val_warm_artists_in_train": int(set(splits["val_warm"]["artist_key"]).issubset(train_artists)),
        "test_warm_artists_in_train": int(set(splits["test_warm"]["artist_key"]).issubset(train_artists)),
    }
    return summary


def render_md(summary: dict) -> str:
    lines = [
        "# Track 4 split 생성 보고서",
        "",
        "- 목적: Track 4 모델 실험용 train / validation / test split 생성",
        f"- 입력: `{summary['input']}`",
        f"- random seed: `{summary['random_seed']}`",
        "- 기준: `artist_key` 기준 Cold 작가 분리",
        "- source는 split 기준이나 모델 피처로 사용하지 않음",
        "",
        "## 1. split 결과",
        "",
        "| split | rows | artists | 파일 |",
        "|---|---:|---:|---|",
    ]
    for name, item in summary["files"].items():
        lines.append(f"| `{name}` | `{item['rows']:,}` | `{item['artists']:,}` | `{item['path']}` |")
    lines += [
        "",
        "## 2. 검증",
        "",
        f"- validation cold와 train 작가 겹침: `{summary['checks']['val_cold_overlap_train_artists']}`",
        f"- test cold와 train 작가 겹침: `{summary['checks']['test_cold_overlap_train_artists']}`",
        f"- validation warm 작가가 train에 모두 존재: `{bool(summary['checks']['val_warm_artists_in_train'])}`",
        f"- test warm 작가가 train에 모두 존재: `{bool(summary['checks']['test_warm_artists_in_train'])}`",
        "",
        "## 3. 다음 단계",
        "",
        "- 이 split을 기준으로 Track 4 baseline 모델 실험 진행",
        "- Warm / Cold 성능은 반드시 분리 기록",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT, dtype="string", keep_default_na=False)
    splits = create_splits(df)
    for name, frame in splits.items():
        frame.to_csv(OUT_DIR / f"track4_{name}.csv", index=False, encoding="utf-8-sig")
    summary = summarize(splits)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_md(summary), encoding="utf-8")
    print("Track 4 splits")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
