#!/usr/bin/env python3
"""Create Track 5 train/validation/test splits with stronger Warm evaluation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
OUT_DIR = REPO / "data" / "track5_split"
OUT_REPORT = REPO / "docs" / "track5" / "dataset" / "split_report.md"
OUT_JSON = OUT_DIR / "track5_split_summary.json"
OUT_MEMBERSHIP = OUT_DIR / "track5_split_membership.csv"

RANDOM_SEED = 20260518
TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

COLD_TEST_ARTIST_FRAC = 0.10
COLD_VAL_ARTIST_FRAC = 0.05
WARM_TEST_ARTIST_FRAC = 0.20
WARM_VAL_ARTIST_FRAC = 0.10
WARM_ELIGIBLE_MIN_WORKS = 5
WARM_MAX_HOLDOUT_PER_ARTIST = 3
WARM_MIN_TRAIN_PER_ARTIST = 2

DUPLICATE_KEY_COLS = [
    "artist_key",
    "title_raw",
    "price_krw",
    "width_cm",
    "height_cm",
    "depth_cm",
    "medium_category",
    "support_category",
]


def sample_artists(artists: np.ndarray, frac: float, rng: np.random.Generator) -> set[str]:
    n = max(1, int(round(len(artists) * frac)))
    n = min(n, len(artists))
    if n <= 0:
        return set()
    return set(rng.choice(artists, size=n, replace=False).tolist())


def duplicate_key(df: pd.DataFrame) -> pd.Series:
    available = [c for c in DUPLICATE_KEY_COLS if c in df.columns]
    return df[available].fillna("").astype(str).agg("|".join, axis=1)


def load_training_candidates() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    work = df.loc[df["is_training_candidate"].astype(str).str.lower().eq("true")].copy()
    work = work.loc[work["artist_key"].fillna("").astype(str).ne("")]
    work = work.dropna(subset=[TARGET_LOG, TARGET_PRICE])
    work["_track5_row_id"] = work.index.astype(int)
    return work


def holdout_warm_rows(df: pd.DataFrame, artists: set[str], rng: np.random.Generator) -> pd.Index:
    holdout: list[int] = []
    candidates = df.loc[df["artist_key"].isin(artists)]
    for _, group in candidates.groupby("artist_key", sort=False):
        max_holdout = min(WARM_MAX_HOLDOUT_PER_ARTIST, len(group) - WARM_MIN_TRAIN_PER_ARTIST)
        if max_holdout <= 0:
            continue
        n_holdout = max(1, min(max_holdout, int(round(len(group) * 0.25))))
        sampled = group.sample(n=n_holdout, random_state=int(rng.integers(0, 2**31 - 1))).index.tolist()
        holdout.extend(sampled)
    return pd.Index(holdout)


def remove_train_eval_duplicates(splits: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    eval_names = ["val_warm", "test_warm", "val_cold", "test_cold"]
    eval_keys = pd.concat([duplicate_key(splits[name]) for name in eval_names], ignore_index=True)
    eval_key_set = set(eval_keys[eval_keys.ne("")])
    train = splits["train"].copy()
    remove_mask = duplicate_key(train).isin(eval_key_set)
    removed = train.loc[remove_mask].copy()

    out = {k: v.copy() for k, v in splits.items()}
    out["train"] = train.loc[~remove_mask].copy()
    warm_removed: dict[str, int] = {}
    train_counts = out["train"]["artist_key"].value_counts()
    for name in ["val_warm", "test_warm"]:
        final_counts = out[name]["artist_key"].map(train_counts).fillna(0).astype(int)
        keep = final_counts >= WARM_MIN_TRAIN_PER_ARTIST
        warm_removed[name] = int((~keep).sum())
        out[name] = out[name].loc[keep].copy()

    return out, {
        "duplicate_key_columns": DUPLICATE_KEY_COLS,
        "removed_train_rows": int(remove_mask.sum()),
        "removed_train_artists": int(removed["artist_key"].nunique()) if len(removed) else 0,
        "removed_warm_eval_rows_after_duplicate_removal": warm_removed,
    }


def recompute_artist_counts(splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {k: v.copy() for k, v in splits.items()}
    train_counts = out["train"]["artist_key"].value_counts()
    for name, frame in out.items():
        counts = frame["artist_key"].map(train_counts).fillna(0).astype(int)
        frame["artist_works_count_train"] = counts
        frame["artist_works_log"] = np.log1p(counts)
        out[name] = frame
    return out


def create_splits(df: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    rng = np.random.default_rng(RANDOM_SEED)
    artist_counts = df["artist_key"].value_counts()
    artists = artist_counts.index.to_numpy()

    cold_test_artists = sample_artists(artists, COLD_TEST_ARTIST_FRAC, rng)
    cold_pool = np.array([a for a in artists if a not in cold_test_artists])
    cold_val_artists = sample_artists(cold_pool, COLD_VAL_ARTIST_FRAC, rng)
    cold_artists = cold_test_artists | cold_val_artists

    train_pool = df.loc[~df["artist_key"].isin(cold_artists)].copy()
    cold_test = df.loc[df["artist_key"].isin(cold_test_artists)].copy()
    cold_val = df.loc[df["artist_key"].isin(cold_val_artists)].copy()

    warm_eligible = train_pool["artist_key"].value_counts()
    warm_eligible = warm_eligible[warm_eligible >= WARM_ELIGIBLE_MIN_WORKS].index.to_numpy()
    warm_test_artists = sample_artists(warm_eligible, WARM_TEST_ARTIST_FRAC, rng)
    warm_remaining = np.array([a for a in warm_eligible if a not in warm_test_artists])
    warm_val_artists = sample_artists(warm_remaining, WARM_VAL_ARTIST_FRAC, rng)

    warm_test_idx = holdout_warm_rows(train_pool, warm_test_artists, rng)
    warm_val_idx = holdout_warm_rows(train_pool.drop(index=warm_test_idx), warm_val_artists, rng)
    holdout_idx = set(warm_test_idx) | set(warm_val_idx)

    splits = {
        "train": train_pool.loc[~train_pool.index.isin(holdout_idx)].copy(),
        "val_warm": train_pool.loc[warm_val_idx].copy(),
        "test_warm": train_pool.loc[warm_test_idx].copy(),
        "val_cold": cold_val.copy(),
        "test_cold": cold_test.copy(),
    }
    splits, duplicate_summary = remove_train_eval_duplicates(splits)
    splits = recompute_artist_counts(splits)
    return splits, {
        "cold_test_artists": sorted(cold_test_artists),
        "cold_val_artists": sorted(cold_val_artists),
        "warm_test_artists": sorted(warm_test_artists),
        "warm_val_artists": sorted(warm_val_artists),
        "duplicate_handling": duplicate_summary,
    }


def split_summary(splits: dict[str, pd.DataFrame], meta: dict[str, Any]) -> dict[str, Any]:
    train_artists = set(splits["train"]["artist_key"])
    summary: dict[str, Any] = {
        "created_at": date.today().isoformat(),
        "input": str(INPUT.relative_to(REPO)),
        "random_seed": RANDOM_SEED,
        "policy": {
            "cold_test_artist_frac": COLD_TEST_ARTIST_FRAC,
            "cold_val_artist_frac": COLD_VAL_ARTIST_FRAC,
            "warm_test_artist_frac": WARM_TEST_ARTIST_FRAC,
            "warm_val_artist_frac": WARM_VAL_ARTIST_FRAC,
            "warm_eligible_min_works": WARM_ELIGIBLE_MIN_WORKS,
            "warm_max_holdout_per_artist": WARM_MAX_HOLDOUT_PER_ARTIST,
            "warm_min_train_per_artist": WARM_MIN_TRAIN_PER_ARTIST,
        },
        "files": {},
        "checks": {},
        "duplicate_handling": meta["duplicate_handling"],
    }
    for name, frame in splits.items():
        artist_counts = frame["artist_key"].value_counts()
        path = OUT_DIR / f"track5_{name}.csv"
        summary["files"][name] = {
            "path": str(path.relative_to(REPO)),
            "rows": int(len(frame)),
            "artists": int(frame["artist_key"].nunique()),
            "artist_name_ko": int(frame["artist_name_ko"].nunique()) if "artist_name_ko" in frame.columns else None,
            "price_median": float(frame[TARGET_PRICE].median()) if len(frame) else None,
            "price_p90": float(frame[TARGET_PRICE].quantile(0.90)) if len(frame) else None,
            "artist_rows_median": float(artist_counts.median()) if len(artist_counts) else None,
            "artist_rows_p90": float(artist_counts.quantile(0.90)) if len(artist_counts) else None,
        }

    for name in ["val_cold", "test_cold"]:
        summary["checks"][f"{name}_overlap_train_artist_key"] = int(len(train_artists & set(splits[name]["artist_key"])))
        summary["checks"][f"{name}_artist_works_log_nonzero"] = int(
            (pd.to_numeric(splits[name]["artist_works_log"], errors="coerce") > 0).sum()
        )
    for name in ["val_warm", "test_warm"]:
        summary["checks"][f"{name}_artists_all_in_train"] = bool(set(splits[name]["artist_key"]).issubset(train_artists))
        summary["checks"][f"{name}_min_train_count"] = int(splits[name]["artist_works_count_train"].min()) if len(splits[name]) else 0

    train_names = set(splits["train"].get("artist_name_ko_orig", pd.Series(dtype=str)).dropna().astype(str))
    for name in ["val_cold", "test_cold"]:
        eval_names = set(splits[name].get("artist_name_ko_orig", pd.Series(dtype=str)).dropna().astype(str))
        summary["checks"][f"{name}_overlap_train_artist_name_ko_orig"] = int(len(train_names & eval_names))
    return summary


def write_splits(splits: dict[str, pd.DataFrame], summary: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        frame.to_csv(OUT_DIR / f"track5_{name}.csv", index=False)
    membership_rows = []
    for name, frame in splits.items():
        for row_id, artist_key in frame[["_track5_row_id", "artist_key"]].itertuples(index=False):
            membership_rows.append({"split": name, "track5_row_id": int(row_id), "artist_key": artist_key})
    pd.DataFrame(membership_rows).to_csv(OUT_MEMBERSHIP, index=False)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 5 split 생성 보고서",
        "",
        "- 목적: Track 4에서 확인된 Warm test 표본 부족 문제를 해결한 새 실험용 split 생성",
        f"- 생성일: `{summary['created_at']}`",
        f"- 입력: `{summary['input']}`",
        f"- random seed: `{summary['random_seed']}`",
        "- 기준: `artist_key` 기준 Warm / Cold 분리",
        "- 운영 설명: 학습 DB에 작가가 있으면 Warm, 없으면 Cold",
        "",
        "## 1. split 정책",
        "",
        f"- Cold test 작가 비율: `{summary['policy']['cold_test_artist_frac']}`",
        f"- Cold validation 작가 비율: `{summary['policy']['cold_val_artist_frac']}`",
        f"- Warm test 후보 작가 비율: `{summary['policy']['warm_test_artist_frac']}`",
        f"- Warm validation 후보 작가 비율: `{summary['policy']['warm_val_artist_frac']}`",
        f"- Warm 평가 후보 최소 작품 수: `{summary['policy']['warm_eligible_min_works']}`",
        f"- Warm 평가 작가별 최대 holdout 작품 수: `{summary['policy']['warm_max_holdout_per_artist']}`",
        f"- Warm 평가 작가별 train에 남기는 최소 작품 수: `{summary['policy']['warm_min_train_per_artist']}`",
        "",
        "## 2. split 결과",
        "",
        "| split | rows | artist_key 수 | 한글명 수 | 가격 중앙값 | 가격 p90 | 작가당 rows 중앙값 | 파일 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, item in summary["files"].items():
        lines.append(
            f"| `{name}` | `{item['rows']:,}` | `{item['artists']:,}` | `{item['artist_name_ko']:,}` | "
            f"`{item['price_median']:,.0f}` | `{item['price_p90']:,.0f}` | `{item['artist_rows_median']:.1f}` | `{item['path']}` |"
        )
    lines += [
        "",
        "## 3. 누수/분리 검증",
        "",
        f"- val_cold와 train 작가 겹침: `{summary['checks']['val_cold_overlap_train_artist_key']}`",
        f"- test_cold와 train 작가 겹침: `{summary['checks']['test_cold_overlap_train_artist_key']}`",
        f"- val_cold의 `artist_works_log > 0` rows: `{summary['checks']['val_cold_artist_works_log_nonzero']}`",
        f"- test_cold의 `artist_works_log > 0` rows: `{summary['checks']['test_cold_artist_works_log_nonzero']}`",
        f"- val_warm 작가가 train에 모두 존재: `{summary['checks']['val_warm_artists_all_in_train']}`",
        f"- test_warm 작가가 train에 모두 존재: `{summary['checks']['test_warm_artists_all_in_train']}`",
        f"- val_warm 평가 rows의 최소 train 작품 수: `{summary['checks']['val_warm_min_train_count']}`",
        f"- test_warm 평가 rows의 최소 train 작품 수: `{summary['checks']['test_warm_min_train_count']}`",
        "",
        "## 4. 동일 작품 후보 처리",
        "",
        f"- train에서 제거한 동일 작품 후보 rows: `{summary['duplicate_handling']['removed_train_rows']:,}`",
        f"- 제거된 rows의 작가 수: `{summary['duplicate_handling']['removed_train_artists']:,}`",
        "- 같은 작가, 제목, 가격, 크기, 재료/지지체가 평가셋에 있으면 train에서 제거",
        "- 평가셋은 그대로 두고 train만 제거해 평가 성능 과대평가를 줄임",
        "",
        "## 5. 해석",
        "",
        "- Track5는 Track4 split을 덮어쓰지 않는 새 기준 split임",
        "- Warm test는 기존 Track4의 137건보다 크게 늘어 최종 성능 판단에 더 적합함",
        "- Cold는 작가 기준으로 train과 완전히 분리되어 신규 작가 상황을 평가함",
        "- 이 split을 기준으로 Track5 모델 실험을 새로 시작해야 함",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    work = load_training_candidates()
    splits, meta = create_splits(work)
    summary = split_summary(splits, meta)
    write_splits(splits, summary)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(render_report(summary), encoding="utf-8")
    print(OUT_JSON)
    print(OUT_REPORT)
    print(json.dumps(summary["files"], ensure_ascii=False))
    print(json.dumps(summary["checks"], ensure_ascii=False))


if __name__ == "__main__":
    main()
