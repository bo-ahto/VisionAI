#!/usr/bin/env python3
"""Create Track 6 strict train/validation/test splits.

Track 6 prioritizes reliable evaluation sets:
- cold validation/test are selected first by Korean artist-name groups
- cold artists and names do not overlap train
- warm validation/test keep enough train rows for the same artist
- evaluation set sizes are checked before model experiments start
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
OUT_DIR = REPO / "data" / "track6_split"
TRACK6_DATA = REPO / "data" / "track6"
OUT_JSON = OUT_DIR / "track6_split_summary.json"
OUT_MEMBERSHIP = OUT_DIR / "track6_split_membership.csv"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "split_report.md"
OUT_CLEANING_REVIEW = REPO / "docs" / "track6" / "dataset" / "cleaning_review.md"
OUT_EXPERIMENT = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E001_strict_split_generation.md"

RANDOM_SEED = 20260518
TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"

MIN_VAL_WARM_ROWS = 200
MIN_VAL_WARM_ARTISTS = 80
MIN_TEST_WARM_ROWS = 500
MIN_TEST_WARM_ARTISTS = 200
MIN_VAL_COLD_ROWS = 1000
MIN_VAL_COLD_ARTISTS = 80
MIN_TEST_COLD_ROWS = 2500
MIN_TEST_COLD_ARTISTS = 200

WARM_MIN_TRAIN_PER_ARTIST = 5
WARM_MIN_HOLDOUT_PER_ARTIST = 2
WARM_MAX_HOLDOUT_PER_ARTIST = 3
WARM_ARTIST_BUFFER = 10

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


def norm_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return " ".join(text.strip().split()).lower()


def duplicate_key(df: pd.DataFrame) -> pd.Series:
    available = [c for c in DUPLICATE_KEY_COLS if c in df.columns]
    return df[available].fillna("").astype(str).agg("|".join, axis=1)


def load_candidates() -> pd.DataFrame:
    df = pd.read_csv(INPUT, low_memory=False)
    work = df.loc[df["is_training_candidate"].astype(str).str.lower().eq("true")].copy()
    work = work.loc[work["artist_key"].fillna("").astype(str).ne("")]
    work = work.loc[work["artist_name_ko"].fillna("").astype(str).ne("")]
    work = work.dropna(subset=[TARGET_LOG, TARGET_PRICE, "width_cm", "height_cm", "area_cm2", "log_area"])
    work["_track6_row_id"] = work.index.astype(int)
    work["_artist_name_ko_norm"] = work["artist_name_ko"].map(norm_name)
    if "artist_name_ko_orig" in work.columns:
        work["_artist_name_ko_orig_norm"] = work["artist_name_ko_orig"].map(norm_name)
    else:
        work["_artist_name_ko_orig_norm"] = work["_artist_name_ko_norm"]
    return work


def cleaning_review(df_all: pd.DataFrame, work: pd.DataFrame) -> dict[str, Any]:
    orig = work["artist_name_ko_orig"] if "artist_name_ko_orig" in work.columns else work["artist_name_ko"]
    homonym_by_orig = work.groupby(orig.fillna("").astype(str))["artist_key"].nunique()
    entity_suffix_nonempty = (
        work.get("artist_entity_suffix", pd.Series([""] * len(work), index=work.index))
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )
    return {
        "input_rows": int(len(df_all)),
        "training_candidate_rows_before_track6_filter": int(
            df_all["is_training_candidate"].astype(str).str.lower().eq("true").sum()
        ),
        "track6_candidate_rows": int(len(work)),
        "artist_key_count": int(work["artist_key"].nunique()),
        "artist_name_ko_missing_rows": int(work["artist_name_ko"].isna().sum()),
        "artist_name_ko_orig_missing_rows": int(work["artist_name_ko_orig"].isna().sum())
        if "artist_name_ko_orig" in work.columns
        else None,
        "homonym_original_name_count": int((homonym_by_orig > 1).sum()),
        "is_homonym_rows": int(
            work.get("is_homonym", pd.Series([False] * len(work), index=work.index)).astype(str).str.lower().eq("true").sum()
        ),
        "artist_entity_suffix_rows": int(entity_suffix_nonempty.sum()),
        "medium_unknown_rows": int(work["medium_category"].fillna("").astype(str).str.lower().isin(["unknown", ""]).sum()),
        "support_unknown_rows": int(work["support_category"].fillna("").astype(str).str.lower().isin(["unknown", ""]).sum()),
        "source_rows": work["track4_source"].value_counts(dropna=False).to_dict() if "track4_source" in work.columns else {},
    }


def select_name_groups(
    df: pd.DataFrame,
    excluded_names: set[str],
    min_rows: int,
    min_artists: int,
    rng: np.random.Generator,
) -> set[str]:
    candidates = df.loc[~df["_artist_name_ko_orig_norm"].isin(excluded_names)]
    grouped = (
        candidates.groupby("_artist_name_ko_orig_norm")
        .agg(rows=("artist_key", "size"), artists=("artist_key", "nunique"))
        .reset_index()
    )
    grouped = grouped.loc[grouped["_artist_name_ko_orig_norm"].ne("")]
    grouped["_rand"] = rng.random(len(grouped))
    grouped = grouped.sort_values(["_rand"]).reset_index(drop=True)
    selected: set[str] = set()
    rows = 0
    artists = 0
    for _, item in grouped.iterrows():
        selected.add(str(item["_artist_name_ko_orig_norm"]))
        rows += int(item["rows"])
        artists += int(item["artists"])
        if rows >= min_rows and artists >= min_artists:
            break
    return selected


def holdout_warm(
    df: pd.DataFrame,
    min_rows: int,
    min_artists: int,
    used_artists: set[str],
    rng: np.random.Generator,
) -> pd.Index:
    counts = df["artist_key"].value_counts()
    eligible = counts[counts >= WARM_MIN_TRAIN_PER_ARTIST + WARM_MIN_HOLDOUT_PER_ARTIST].index.to_numpy()
    eligible = np.array([a for a in eligible if a not in used_artists])
    rng.shuffle(eligible)
    holdout: list[int] = []
    artist_count = 0
    for artist in eligible:
        group = df.loc[df["artist_key"] == artist]
        max_holdout = min(WARM_MAX_HOLDOUT_PER_ARTIST, len(group) - WARM_MIN_TRAIN_PER_ARTIST)
        if max_holdout < WARM_MIN_HOLDOUT_PER_ARTIST:
            continue
        n = max_holdout
        sampled = group.sample(n=n, random_state=int(rng.integers(0, 2**31 - 1))).index.tolist()
        holdout.extend(sampled)
        used_artists.add(str(artist))
        artist_count += 1
        if len(holdout) >= min_rows and artist_count >= min_artists:
            break
    return pd.Index(holdout)


def remove_train_eval_duplicates(splits: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    eval_names = ["val_warm", "test_warm", "val_cold", "test_cold"]
    eval_key_set = set(pd.concat([duplicate_key(splits[name]) for name in eval_names]).dropna().astype(str))
    eval_key_set.discard("")
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


def create_splits(work: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    rng = np.random.default_rng(RANDOM_SEED)
    cold_test_names = select_name_groups(work, set(), MIN_TEST_COLD_ROWS, MIN_TEST_COLD_ARTISTS, rng)
    cold_val_names = select_name_groups(work, cold_test_names, MIN_VAL_COLD_ROWS, MIN_VAL_COLD_ARTISTS, rng)
    cold_names = cold_test_names | cold_val_names

    cold_test = work.loc[work["_artist_name_ko_orig_norm"].isin(cold_test_names)].copy()
    cold_val = work.loc[work["_artist_name_ko_orig_norm"].isin(cold_val_names)].copy()
    train_pool = work.loc[~work["_artist_name_ko_orig_norm"].isin(cold_names)].copy()

    used_warm_artists: set[str] = set()
    warm_test_idx = holdout_warm(
        train_pool,
        MIN_TEST_WARM_ROWS,
        MIN_TEST_WARM_ARTISTS + WARM_ARTIST_BUFFER,
        used_warm_artists,
        rng,
    )
    warm_pool_after_test = train_pool.drop(index=warm_test_idx)
    warm_val_idx = holdout_warm(
        warm_pool_after_test,
        MIN_VAL_WARM_ROWS,
        MIN_VAL_WARM_ARTISTS + WARM_ARTIST_BUFFER,
        used_warm_artists,
        rng,
    )
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
    for name, frame in splits.items():
        drop_cols = [c for c in frame.columns if c.startswith("_artist_name_")]
        splits[name] = frame.drop(columns=drop_cols)
    return splits, {
        "cold_test_name_groups": sorted(cold_test_names),
        "cold_val_name_groups": sorted(cold_val_names),
        "duplicate_handling": duplicate_summary,
    }


def one_work_artist_count(frame: pd.DataFrame) -> int:
    counts = frame["artist_key"].value_counts()
    return int((counts == 1).sum())


def split_summary(splits: dict[str, pd.DataFrame], clean: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    train = splits["train"]
    train_keys = set(train["artist_key"].astype(str))
    train_name_ko = set(train["artist_name_ko"].dropna().astype(str))
    train_name_orig = set(train["artist_name_ko_orig"].dropna().astype(str))
    summary: dict[str, Any] = {
        "created_at": date.today().isoformat(),
        "input": str(INPUT.relative_to(REPO)),
        "random_seed": RANDOM_SEED,
        "policy": {
            "min_val_warm_rows": MIN_VAL_WARM_ROWS,
            "min_val_warm_artists": MIN_VAL_WARM_ARTISTS,
            "min_test_warm_rows": MIN_TEST_WARM_ROWS,
            "min_test_warm_artists": MIN_TEST_WARM_ARTISTS,
            "min_val_cold_rows": MIN_VAL_COLD_ROWS,
            "min_val_cold_artists": MIN_VAL_COLD_ARTISTS,
            "min_test_cold_rows": MIN_TEST_COLD_ROWS,
            "min_test_cold_artists": MIN_TEST_COLD_ARTISTS,
            "warm_min_train_per_artist": WARM_MIN_TRAIN_PER_ARTIST,
            "warm_holdout_per_artist": [WARM_MIN_HOLDOUT_PER_ARTIST, WARM_MAX_HOLDOUT_PER_ARTIST],
            "warm_artist_buffer": WARM_ARTIST_BUFFER,
        },
        "cleaning_review": clean,
        "files": {},
        "checks": {},
        "duplicate_handling": meta["duplicate_handling"],
    }
    for name, frame in splits.items():
        artist_counts = frame["artist_key"].value_counts()
        summary["files"][name] = {
            "path": str((OUT_DIR / f"track6_{name}.csv").relative_to(REPO)),
            "rows": int(len(frame)),
            "artists": int(frame["artist_key"].nunique()),
            "artist_name_ko": int(frame["artist_name_ko"].nunique()),
            "price_median": float(frame[TARGET_PRICE].median()) if len(frame) else None,
            "price_p90": float(frame[TARGET_PRICE].quantile(0.90)) if len(frame) else None,
            "artist_rows_min": int(artist_counts.min()) if len(artist_counts) else 0,
            "artist_rows_median": float(artist_counts.median()) if len(artist_counts) else None,
            "artist_rows_p90": float(artist_counts.quantile(0.90)) if len(artist_counts) else None,
            "one_work_artists": one_work_artist_count(frame),
            "medium_unknown_rate": float(frame["medium_category"].fillna("").astype(str).str.lower().isin(["unknown", ""]).mean()),
            "support_unknown_rate": float(frame["support_category"].fillna("").astype(str).str.lower().isin(["unknown", ""]).mean()),
        }

    for name in ["val_warm", "test_warm"]:
        frame = splits[name]
        summary["checks"][f"{name}_artists_all_in_train"] = bool(set(frame["artist_key"].astype(str)).issubset(train_keys))
        summary["checks"][f"{name}_min_train_count"] = int(frame["artist_works_count_train"].min()) if len(frame) else 0
        summary["checks"][f"{name}_meets_min_rows"] = bool(len(frame) >= summary["policy"][f"min_{name}_rows"])
        summary["checks"][f"{name}_meets_min_artists"] = bool(
            frame["artist_key"].nunique() >= summary["policy"][f"min_{name}_artists"]
        )
    for name in ["val_cold", "test_cold"]:
        frame = splits[name]
        summary["checks"][f"{name}_overlap_train_artist_key"] = int(len(train_keys & set(frame["artist_key"].astype(str))))
        summary["checks"][f"{name}_overlap_train_artist_name_ko"] = int(len(train_name_ko & set(frame["artist_name_ko"].dropna().astype(str))))
        summary["checks"][f"{name}_overlap_train_artist_name_ko_orig"] = int(
            len(train_name_orig & set(frame["artist_name_ko_orig"].dropna().astype(str)))
        )
        summary["checks"][f"{name}_artist_works_log_nonzero"] = int((frame["artist_works_log"] > 0).sum())
        summary["checks"][f"{name}_meets_min_rows"] = bool(len(frame) >= summary["policy"][f"min_{name}_rows"])
        summary["checks"][f"{name}_meets_min_artists"] = bool(
            frame["artist_key"].nunique() >= summary["policy"][f"min_{name}_artists"]
        )
    eval_keys = set(pd.concat([duplicate_key(splits[n]) for n in ["val_warm", "test_warm", "val_cold", "test_cold"]]))
    summary["checks"]["train_eval_duplicate_key_overlap"] = int(duplicate_key(train).isin(eval_keys).sum())
    hard_checks = [
        summary["checks"]["val_cold_overlaps_train_artist_key"] if "val_cold_overlaps_train_artist_key" in summary["checks"] else 0,
    ]
    summary["status"] = "pass" if all(
        [
            summary["checks"]["val_warm_artists_all_in_train"],
            summary["checks"]["test_warm_artists_all_in_train"],
            summary["checks"]["val_warm_min_train_count"] >= WARM_MIN_TRAIN_PER_ARTIST,
            summary["checks"]["test_warm_min_train_count"] >= WARM_MIN_TRAIN_PER_ARTIST,
            summary["checks"]["val_cold_overlap_train_artist_key"] == 0,
            summary["checks"]["test_cold_overlap_train_artist_key"] == 0,
            summary["checks"]["val_cold_overlap_train_artist_name_ko"] == 0,
            summary["checks"]["test_cold_overlap_train_artist_name_ko"] == 0,
            summary["checks"]["val_cold_overlap_train_artist_name_ko_orig"] == 0,
            summary["checks"]["test_cold_overlap_train_artist_name_ko_orig"] == 0,
            summary["checks"]["val_cold_artist_works_log_nonzero"] == 0,
            summary["checks"]["test_cold_artist_works_log_nonzero"] == 0,
            summary["checks"]["train_eval_duplicate_key_overlap"] == 0,
            summary["checks"]["val_warm_meets_min_rows"],
            summary["checks"]["val_warm_meets_min_artists"],
            summary["checks"]["test_warm_meets_min_rows"],
            summary["checks"]["test_warm_meets_min_artists"],
            summary["checks"]["val_cold_meets_min_rows"],
            summary["checks"]["val_cold_meets_min_artists"],
            summary["checks"]["test_cold_meets_min_rows"],
            summary["checks"]["test_cold_meets_min_artists"],
        ]
    ) else "review_required"
    return summary


def write_outputs(splits: dict[str, pd.DataFrame], summary: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRACK6_DATA.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        frame.to_csv(OUT_DIR / f"track6_{name}.csv", index=False)
    membership_rows = []
    for name, frame in splits.items():
        for row_id, artist_key in frame[["_track6_row_id", "artist_key"]].itertuples(index=False):
            membership_rows.append({"split": name, "track6_row_id": int(row_id), "artist_key": artist_key})
    pd.DataFrame(membership_rows).to_csv(OUT_MEMBERSHIP, index=False)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_CLEANING_REVIEW.write_text(render_cleaning_review(summary), encoding="utf-8")
    OUT_REPORT.write_text(render_split_report(summary), encoding="utf-8")
    OUT_EXPERIMENT.write_text(render_experiment(summary), encoding="utf-8")


def render_cleaning_review(summary: dict[str, Any]) -> str:
    c = summary["cleaning_review"]
    source_lines = "\n".join(f"| `{k}` | `{v:,}` |" for k, v in c["source_rows"].items())
    return f"""# Track 6 클렌징 검토 요약

- 생성일: `{summary['created_at']}`
- 입력: `{summary['input']}`
- 목적: Track6 split 전 학습 후보와 작가명/동명이인 상태 확인

## 1. 후보 데이터

- 전체 입력 rows: `{c['input_rows']:,}`
- Track4 학습 후보 rows: `{c['training_candidate_rows_before_track6_filter']:,}`
- Track6 후보 rows: `{c['track6_candidate_rows']:,}`
- 작가 key 수: `{c['artist_key_count']:,}`
- 한글 작가명 결측 rows: `{c['artist_name_ko_missing_rows']:,}`
- 원본 한글명 결측 rows: `{c['artist_name_ko_orig_missing_rows']:,}`

## 2. 작가명/동명이인

- 원본 한글명 기준 여러 artist_key가 있는 이름 수: `{c['homonym_original_name_count']:,}`
- `is_homonym=True` rows: `{c['is_homonym_rows']:,}`
- `artist_entity_suffix` 사용 rows: `{c['artist_entity_suffix_rows']:,}`
- 해석: 동명이인 후보는 split 검증에서 이름 기준 중복 제거 대상으로 함께 관리함

## 3. 재료/지지체

- `medium_category` unknown rows: `{c['medium_unknown_rows']:,}`
- `support_category` unknown rows: `{c['support_unknown_rows']:,}`
- 해석: unknown은 즉시 제외하지 않고 후속 Cold/Warm 위험 구간으로 관리함

## 4. 출처별 후보 rows

| 출처 | rows |
|---|---:|
{source_lines}
"""


def render_split_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Track 6 split 생성 보고서",
        "",
        f"- 생성일: `{summary['created_at']}`",
        f"- 입력: `{summary['input']}`",
        f"- random seed: `{summary['random_seed']}`",
        f"- 상태: `{summary['status']}`",
        "- 방식: validation/test를 먼저 충분히 확보한 뒤 남은 데이터를 train으로 구성",
        "- Cold 기준: `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 모두 train 겹침 0",
        "- Warm 기준: 평가 작가가 train에 최소 5작품 이상 남음",
        "",
        "## 1. split 결과",
        "",
        "| split | rows | 작가 수 | 한글명 수 | 가격 중앙값 | 가격 p90 | 작가당 rows 중앙값 | 1작품 작가 수 | 파일 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, item in summary["files"].items():
        lines.append(
            f"| `{name}` | `{item['rows']:,}` | `{item['artists']:,}` | `{item['artist_name_ko']:,}` | "
            f"`{item['price_median']:,.0f}` | `{item['price_p90']:,.0f}` | `{item['artist_rows_median']:.1f}` | "
            f"`{item['one_work_artists']:,}` | `{item['path']}` |"
        )
    checks = summary["checks"]
    lines += [
        "",
        "## 2. 핵심 검증",
        "",
        f"- val_warm 작가 모두 train 존재: `{checks['val_warm_artists_all_in_train']}`",
        f"- test_warm 작가 모두 train 존재: `{checks['test_warm_artists_all_in_train']}`",
        f"- val_warm 최소 train 작품 수: `{checks['val_warm_min_train_count']}`",
        f"- test_warm 최소 train 작품 수: `{checks['test_warm_min_train_count']}`",
        f"- val_cold train artist_key 겹침: `{checks['val_cold_overlap_train_artist_key']}`",
        f"- test_cold train artist_key 겹침: `{checks['test_cold_overlap_train_artist_key']}`",
        f"- val_cold train artist_name_ko 겹침: `{checks['val_cold_overlap_train_artist_name_ko']}`",
        f"- test_cold train artist_name_ko 겹침: `{checks['test_cold_overlap_train_artist_name_ko']}`",
        f"- val_cold train artist_name_ko_orig 겹침: `{checks['val_cold_overlap_train_artist_name_ko_orig']}`",
        f"- test_cold train artist_name_ko_orig 겹침: `{checks['test_cold_overlap_train_artist_name_ko_orig']}`",
        f"- val_cold `artist_works_log > 0` rows: `{checks['val_cold_artist_works_log_nonzero']}`",
        f"- test_cold `artist_works_log > 0` rows: `{checks['test_cold_artist_works_log_nonzero']}`",
        f"- train/eval 동일 작품 후보 겹침: `{checks['train_eval_duplicate_key_overlap']}`",
        "",
        "## 3. 최소 평가셋 크기 통과 여부",
        "",
        f"- val_warm rows 기준 통과: `{checks['val_warm_meets_min_rows']}`",
        f"- val_warm 작가 수 기준 통과: `{checks['val_warm_meets_min_artists']}`",
        f"- test_warm rows 기준 통과: `{checks['test_warm_meets_min_rows']}`",
        f"- test_warm 작가 수 기준 통과: `{checks['test_warm_meets_min_artists']}`",
        f"- val_cold rows 기준 통과: `{checks['val_cold_meets_min_rows']}`",
        f"- val_cold 작가 수 기준 통과: `{checks['val_cold_meets_min_artists']}`",
        f"- test_cold rows 기준 통과: `{checks['test_cold_meets_min_rows']}`",
        f"- test_cold 작가 수 기준 통과: `{checks['test_cold_meets_min_artists']}`",
        "",
        "## 4. 해석",
        "",
        "- Track6는 Track5보다 Cold 이름 중복 기준을 강화함",
        "- Warm 평가는 train에 충분한 작품이 남는 작가 중심으로 구성함",
        "- split 상태가 `pass`이면 T6-E002 구조-only baseline으로 진행 가능",
    ]
    return "\n".join(lines)


def render_experiment(summary: dict[str, Any]) -> str:
    return f"""# T6-E001 strict split 생성 및 검증

- 날짜: {summary['created_at']}
- 관련 가설: T6-H1
- 상태: {'검증 완료' if summary['status'] == 'pass' else '검토 필요'}
- 사용 데이터: `data/track4_primary_market_feature_candidates_v1.csv`
- 사용 스크립트: `scripts/track6/create_track6_splits.py`
- 결과: `docs/track6/dataset/split_report.md`

## 실험 목적

- Track5에서 남은 Cold 이름 중복, Warm 저이력, 1작가 1작품 평가 문제를 split 단계에서 보완
- validation/test를 먼저 충분히 확보하고 남은 데이터를 train으로 구성

## 핵심 결과

- train rows: `{summary['files']['train']['rows']:,}`
- val_warm rows/artists: `{summary['files']['val_warm']['rows']:,}` / `{summary['files']['val_warm']['artists']:,}`
- test_warm rows/artists: `{summary['files']['test_warm']['rows']:,}` / `{summary['files']['test_warm']['artists']:,}`
- val_cold rows/artists: `{summary['files']['val_cold']['rows']:,}` / `{summary['files']['val_cold']['artists']:,}`
- test_cold rows/artists: `{summary['files']['test_cold']['rows']:,}` / `{summary['files']['test_cold']['artists']:,}`
- Cold train 이름 중복: val `{summary['checks']['val_cold_overlap_train_artist_name_ko_orig']}`, test `{summary['checks']['test_cold_overlap_train_artist_name_ko_orig']}`
- Warm 최소 train 작품 수: val `{summary['checks']['val_warm_min_train_count']}`, test `{summary['checks']['test_warm_min_train_count']}`

## 결론

- split 상태: `{summary['status']}`
- 상태가 `pass`이면 이 split을 Track6 기준 데이터셋으로 고정
- 이후 T6-E002부터 모든 모델 실험은 이 split 기준으로 실행
"""


def update_management_tables(summary: dict[str, Any]) -> None:
    status = "검증 완료" if summary["status"] == "pass" else "부분 검증"
    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    text = hypo.read_text(encoding="utf-8")
    old = (
        "| T6-H1 | T6-G1 | strict cold와 강화된 Warm 기준을 적용한 Track6 split이 최종 보고 기준으로 더 적합할 것이다 | "
        "Track3/4/5 방법을 반영해 클렌징 후보를 확정하고 validation/test 우선 split으로 한글명, 동명이인, Warm train 작품 수, Cold 이름 중복, 작가당 평가 작품 수를 검증 | "
        "Track4 feature candidates | split metadata | Track5 split | Cold 이름 중복 0, Warm train 최소 작품 수 기준 충족, 평가셋 최소 rows 충족, 1작가 1작품 비율 기록 | 예정 | 미실행 | split 생성 전 | T6-E001 | split 생성 스크립트 작성 |"
    )
    new = (
        "| T6-H1 | T6-G1 | strict cold와 강화된 Warm 기준을 적용한 Track6 split이 최종 보고 기준으로 더 적합할 것이다 | "
        "Track3/4/5 방법을 반영해 클렌징 후보를 확정하고 validation/test 우선 split으로 한글명, 동명이인, Warm train 작품 수, Cold 이름 중복, 작가당 평가 작품 수를 검증 | "
        f"Track6 split | split metadata | Track5 split | Cold 이름 중복 0, Warm train 최소 작품 수 기준 충족, 평가셋 최소 rows 충족, 1작가 1작품 비율 기록 | {status} | split 생성 검증 | "
        f"상태 `{summary['status']}`, test_warm `{summary['files']['test_warm']['rows']:,}`건, test_cold `{summary['files']['test_cold']['rows']:,}`건, Cold 이름 겹침 0 | T6-E001 | T6-E002 baseline 진행 |"
    )
    if old in text:
        hypo.write_text(text.replace(old, new), encoding="utf-8")

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    text = results.read_text(encoding="utf-8")
    old_row = (
        "| 2026-05-18 | T6-E001 | T6-H1 | 예정 | Track4 feature candidates | 모델 미사용 | split metadata | 예정 | 예정 | Track6 split 생성 전 | 예정 |"
    )
    new_row = (
        f"| {summary['created_at']} | T6-E001 | T6-H1 | {status} | Track4 feature candidates | 모델 미사용 | split metadata | "
        f"val `{summary['files']['val_warm']['rows']:,}`건 / test `{summary['files']['test_warm']['rows']:,}`건 | "
        f"val `{summary['files']['val_cold']['rows']:,}`건 / test `{summary['files']['test_cold']['rows']:,}`건, 이름 겹침 0 | "
        f"Track6 split 상태 `{summary['status']}` | [기록](../experiments/2026-05-18_T6-E001_strict_split_generation.md), [보고서](../dataset/split_report.md) |"
    )
    if old_row in text:
        results.write_text(text.replace(old_row, new_row), encoding="utf-8")

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    text = index.read_text(encoding="utf-8")
    old_idx = "| 2026-05-18 | T6-E001 | T6-H1 | 예정 | Track6 strict split 생성 및 검증 | 예정 |"
    new_idx = (
        f"| {summary['created_at']} | T6-E001 | T6-H1 | {status} | Track6 strict split 생성 및 검증, 상태 `{summary['status']}` | "
        "[기록](2026-05-18_T6-E001_strict_split_generation.md) |"
    )
    if old_idx in text:
        index.write_text(text.replace(old_idx, new_idx), encoding="utf-8")


def main() -> None:
    df_all = pd.read_csv(INPUT, low_memory=False)
    work = load_candidates()
    clean = cleaning_review(df_all, work)
    splits, meta = create_splits(work)
    summary = split_summary(splits, clean, meta)
    write_outputs(splits, summary)
    update_management_tables(summary)
    print(OUT_JSON)
    print(OUT_REPORT)
    print(json.dumps({"status": summary["status"], "files": summary["files"], "checks": summary["checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
