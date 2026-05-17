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


def duplicate_key(df: pd.DataFrame) -> pd.Series:
    available = [c for c in DUPLICATE_KEY_COLS if c in df.columns]
    return df[available].fillna("").astype(str).agg("|".join, axis=1)


def remove_train_eval_duplicates(splits: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict]:
    eval_names = ["val_warm", "val_cold", "test_warm", "test_cold"]
    eval_keys = pd.concat([duplicate_key(splits[name]) for name in eval_names], ignore_index=True)
    eval_key_set = set(eval_keys[eval_keys.ne("")])
    train = splits["train"].copy()
    remove_mask = duplicate_key(train).isin(eval_key_set)
    removed = train.loc[remove_mask].copy()
    out = {k: v.copy() for k, v in splits.items()}
    out["train"] = train.loc[~remove_mask].copy()
    train_artists_after_removal = set(out["train"]["artist_key"])
    warm_removed: dict[str, int] = {}
    for name in ["val_warm", "test_warm"]:
        warm_mask = out[name]["artist_key"].isin(train_artists_after_removal)
        warm_removed[name] = int((~warm_mask).sum())
        out[name] = out[name].loc[warm_mask].copy()
    return out, {
        "duplicate_key_columns": DUPLICATE_KEY_COLS,
        "removed_train_rows": int(remove_mask.sum()),
        "removed_train_artists": int(removed["artist_key"].nunique()) if len(removed) else 0,
        "removed_warm_eval_rows_after_train_duplicate_removal": warm_removed,
    }


def recompute_artist_counts_from_train(splits: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {k: v.copy() for k, v in splits.items()}
    train_counts = out["train"]["artist_key"].value_counts()
    for name, frame in out.items():
        counts = frame["artist_key"].map(train_counts).fillna(0).astype(int)
        frame["artist_works_count_train"] = counts
        frame["artist_works_log"] = np.log1p(counts)
        out[name] = frame
    return out


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

    splits = {
        "train": train,
        "val_warm": warm_val,
        "val_cold": cold_val,
        "test_warm": warm_test,
        "test_cold": cold_test,
    }
    splits, duplicate_summary = remove_train_eval_duplicates(splits)
    splits = recompute_artist_counts_from_train(splits)
    for frame in splits.values():
        frame.attrs["duplicate_summary"] = duplicate_summary
    return splits


def summarize(splits: dict[str, pd.DataFrame]) -> dict:
    summary = {
        "created_at": "2026-05-15",
        "input": str(INPUT.relative_to(REPO)),
        "random_seed": RANDOM_SEED,
        "files": {},
        "duplicate_handling": splits["train"].attrs.get("duplicate_summary", {}),
    }
    for name, frame in splits.items():
        path = OUT_DIR / f"track4_{name}.csv"
        homonym_rows = (
            int(frame["is_homonym"].astype(str).str.lower().eq("true").sum())
            if "is_homonym" in frame.columns
            else 0
        )
        summary["files"][name] = {
            "path": str(path.relative_to(REPO)),
            "rows": int(len(frame)),
            "artists": int(frame["artist_key"].nunique()),
            "artist_name_ko": int(frame["artist_name_ko"].nunique()) if "artist_name_ko" in frame.columns else None,
            "homonym_rows": homonym_rows,
            "artist_works_log_min": float(pd.to_numeric(frame["artist_works_log"], errors="coerce").min()),
            "artist_works_log_max": float(pd.to_numeric(frame["artist_works_log"], errors="coerce").max()),
        }
    train_artists = set(splits["train"]["artist_key"])
    train_names = set(splits["train"]["artist_name_ko"]) if "artist_name_ko" in splits["train"] else set()
    train_orig_names = set(splits["train"]["artist_name_ko_orig"]) if "artist_name_ko_orig" in splits["train"] else set()
    summary["checks"] = {
        "val_cold_overlap_train_artists": int(len(train_artists & set(splits["val_cold"]["artist_key"]))),
        "test_cold_overlap_train_artists": int(len(train_artists & set(splits["test_cold"]["artist_key"]))),
        "val_cold_overlap_train_artist_name_ko": int(len(train_names & set(splits["val_cold"]["artist_name_ko"]))) if train_names else None,
        "test_cold_overlap_train_artist_name_ko": int(len(train_names & set(splits["test_cold"]["artist_name_ko"]))) if train_names else None,
        "val_cold_overlap_train_artist_name_ko_orig": int(len(train_orig_names & set(splits["val_cold"]["artist_name_ko_orig"]))) if train_orig_names else None,
        "test_cold_overlap_train_artist_name_ko_orig": int(len(train_orig_names & set(splits["test_cold"]["artist_name_ko_orig"]))) if train_orig_names else None,
        "val_warm_artists_in_train": int(set(splits["val_warm"]["artist_key"]).issubset(train_artists)),
        "test_warm_artists_in_train": int(set(splits["test_warm"]["artist_key"]).issubset(train_artists)),
        "val_cold_artist_works_log_nonzero": int((pd.to_numeric(splits["val_cold"]["artist_works_log"], errors="coerce") > 0).sum()),
        "test_cold_artist_works_log_nonzero": int((pd.to_numeric(splits["test_cold"]["artist_works_log"], errors="coerce") > 0).sum()),
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
        "- `artist_name_ko`는 표시/리포트용 작가명으로 함께 보존",
        "- 동명이인은 `artist_name_ko_orig`, `is_homonym`, `artist_entity_suffix`로 함께 보존",
        "- `artist_works_log`는 split 이후 train에 남은 작품 수 기준으로 다시 계산",
        "- train/eval 간 동일 작품 후보는 train에서 제거",
        "- source는 split 기준이나 모델 피처로 사용하지 않음",
        "",
        "## 1. split 결과",
        "",
        "| split | rows | artist_key 수 | 한글명 수 | 동명이인 rows | artist_works_log 범위 | 파일 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, item in summary["files"].items():
        lines.append(
            f"| `{name}` | `{item['rows']:,}` | `{item['artists']:,}` | "
            f"`{item['artist_name_ko']:,}` | `{item['homonym_rows']:,}` | "
            f"`{item['artist_works_log_min']:.2f}~{item['artist_works_log_max']:.2f}` | `{item['path']}` |"
        )
    lines += [
        "",
        "## 2. 중복/누수 방지",
        "",
        f"- train에서 제거한 동일 작품 후보 rows: `{summary['duplicate_handling'].get('removed_train_rows', 0):,}`",
        f"- 제거된 rows의 작가 수: `{summary['duplicate_handling'].get('removed_train_artists', 0):,}`",
        "- 제거 기준: 같은 `artist_key`, 제목, 가격, 크기, 재료/지지체가 평가셋에도 있는 경우",
        "- 평가셋은 그대로 두고 train에서만 제거해 평가 성능 과대평가를 줄임",
        "",
        "## 3. 검증",
        "",
        f"- validation cold와 train 작가 겹침: `{summary['checks']['val_cold_overlap_train_artists']}`",
        f"- test cold와 train 작가 겹침: `{summary['checks']['test_cold_overlap_train_artists']}`",
        f"- validation warm 작가가 train에 모두 존재: `{bool(summary['checks']['val_warm_artists_in_train'])}`",
        f"- test warm 작가가 train에 모두 존재: `{bool(summary['checks']['test_warm_artists_in_train'])}`",
        f"- validation cold의 `artist_works_log > 0` rows: `{summary['checks']['val_cold_artist_works_log_nonzero']}`",
        f"- test cold의 `artist_works_log > 0` rows: `{summary['checks']['test_cold_artist_works_log_nonzero']}`",
        f"- validation cold와 train 한글 표시명 겹침: `{summary['checks']['val_cold_overlap_train_artist_name_ko']}`",
        f"- test cold와 train 한글 표시명 겹침: `{summary['checks']['test_cold_overlap_train_artist_name_ko']}`",
        f"- validation cold와 train 원본 한글명 겹침: `{summary['checks']['val_cold_overlap_train_artist_name_ko_orig']}`",
        f"- test cold와 train 원본 한글명 겹침: `{summary['checks']['test_cold_overlap_train_artist_name_ko_orig']}`",
        "",
        "## 4. 동명이인 해석",
        "",
        "- Warm/Cold의 실제 분리 기준은 `artist_key`임",
        "- `artist_key` 기준 train과 cold의 작가 겹침은 0건임",
        "- 원본 한글명은 같은데 `artist_key`가 다른 경우가 있어 `artist_name_ko_orig`는 cold와 train 사이에서 겹칠 수 있음",
        "- 이 경우는 이름이 같은 다른 작가 또는 표기 변형 후보이므로, 모델/평가 기준에서는 `artist_key`를 우선함",
        "- 동명이인으로 판정된 경우 `artist_name_ko`에 `_A`, `_B` suffix가 붙어 표시됨",
        "",
        "## 5. 남은 확인",
        "",
        "- Warm 평가셋은 작가당 1건 방식이라 rows가 작음",
        "- Warm 성능은 baseline 이후 반복 split 또는 내부 CV로 안정성을 확인해야 함",
        "- `support_category=unknown`이 많으므로 모델 실험에서 unknown 처리 효과를 별도로 확인해야 함",
        "",
        "## 6. 다음 단계",
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
