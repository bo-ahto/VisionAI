#!/usr/bin/env python3
"""Create repeated Warm recheck splits and revalidate the Track 4 Warm model."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "data" / "track4_primary_market_feature_candidates_v1.csv"
BASE_SPLIT_DIR = REPO / "data" / "track4_split"
OUT_SPLIT_DIR = REPO / "data" / "track4_warm_recheck_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
RESULT_PATH = RESULT_DIR / "t4_e053_warm_recheck_split_revalidation_metrics.json"

TARGET_LOG = "ln_price_krw"
TARGET_PRICE = "price_krw"
SEEDS = [20260518, 20260519, 20260520, 20260521, 20260522]
ELIGIBLE_MIN_WORKS = 5
EVAL_ARTIST_FRAC = 0.20
MAX_EVAL_PER_ARTIST = 3
MIN_TRAIN_PER_EVAL_ARTIST = 2

CATEGORICAL_FEATURES = ["artist_key", "medium_category", "support_category"]
NUMERIC_FEATURES = [
    "artist_works_log",
    "artist_works_count_train",
    "artist_train_median_log_price",
    "artist_train_mean_log_price",
    "artist_train_iqr_log_price",
    "log_area",
    "aspect_ratio",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_model(seed: int) -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC_FEATURES),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                        ("onehot", onehot_encoder()),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    model = RandomForestRegressor(
        n_estimators=260,
        min_samples_leaf=8,
        max_features=0.75,
        random_state=seed,
        n_jobs=-1,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def load_work() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    work = df.loc[df["is_training_candidate"].astype(str).str.lower().eq("true")].copy()
    work = work.loc[work["artist_key"].fillna("").astype(str).ne("")]
    work = work.dropna(subset=[TARGET_LOG, TARGET_PRICE])
    work["_track4_row_id"] = work.index.astype(int)
    return work.reset_index(drop=True)


def cold_eval_artists() -> set[str]:
    artists: set[str] = set()
    for filename in ["track4_val_cold.csv", "track4_test_cold.csv"]:
        path = BASE_SPLIT_DIR / filename
        if path.exists():
            frame = pd.read_csv(path, usecols=["artist_key"])
            artists.update(frame["artist_key"].dropna().astype(str).tolist())
    return artists


def holdout_indices(pool: pd.DataFrame, seed: int) -> pd.Index:
    rng = np.random.default_rng(seed)
    counts = pool["artist_key"].value_counts()
    eligible_artists = counts[counts >= ELIGIBLE_MIN_WORKS].index.to_numpy()
    eval_artist_count = max(1, int(round(len(eligible_artists) * EVAL_ARTIST_FRAC)))
    eval_artists = set(rng.choice(eligible_artists, size=eval_artist_count, replace=False).tolist())

    holdout: list[int] = []
    for _, group in pool.loc[pool["artist_key"].isin(eval_artists)].groupby("artist_key", sort=False):
        max_holdout = min(MAX_EVAL_PER_ARTIST, len(group) - MIN_TRAIN_PER_EVAL_ARTIST)
        if max_holdout <= 0:
            continue
        n_holdout = max(1, min(max_holdout, int(round(len(group) * 0.25))))
        sampled = group.sample(n=n_holdout, random_state=int(rng.integers(0, 2**31 - 1))).index.tolist()
        holdout.extend(sampled)
    return pd.Index(holdout)


def add_artist_train_stats(train: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    grouped = train.groupby("artist_key")[TARGET_LOG]
    stats = grouped.agg(["median", "mean", "count"]).rename(
        columns={
            "median": "artist_train_median_log_price",
            "mean": "artist_train_mean_log_price",
            "count": "artist_works_count_train",
        }
    )
    stats["artist_train_iqr_log_price"] = grouped.quantile(0.75) - grouped.quantile(0.25)
    out = out.merge(stats, left_on="artist_key", right_index=True, how="left")
    out["artist_works_count_train"] = out["artist_works_count_train"].fillna(0).astype(int)
    out["artist_works_log"] = np.log1p(out["artist_works_count_train"])
    out["artist_train_median_log_price"] = out["artist_train_median_log_price"].fillna(float(train[TARGET_LOG].median()))
    out["artist_train_mean_log_price"] = out["artist_train_mean_log_price"].fillna(float(train[TARGET_LOG].mean()))
    out["artist_train_iqr_log_price"] = out["artist_train_iqr_log_price"].fillna(0.0)
    return out


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, Any]:
    actual_price = df[TARGET_PRICE].to_numpy(dtype=float)
    pred_price = np.maximum(np.exp(pred_log), 1.0)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "rows": int(len(df)),
        "artists": int(df["artist_key"].nunique()),
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "rmse_log": float(np.sqrt(mean_squared_error(df[TARGET_LOG].to_numpy(dtype=float), pred_log))),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
    }


def summarize_seed_result(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names = ["median_ape", "mape", "rmse_log", "within_30", "within_50", "p90_ape", "p95_ape"]
    summary: dict[str, Any] = {
        "seeds": len(rows),
        "eval_rows_mean": float(np.mean([r["metrics"]["rows"] for r in rows])),
        "eval_artists_mean": float(np.mean([r["metrics"]["artists"] for r in rows])),
    }
    for name in metric_names:
        values = np.array([r["metrics"][name] for r in rows], dtype=float)
        summary[f"{name}_mean"] = float(values.mean())
        summary[f"{name}_std"] = float(values.std(ddof=0))
        summary[f"{name}_min"] = float(values.min())
        summary[f"{name}_max"] = float(values.max())
    return summary


def write_readme(summary: dict[str, Any]) -> None:
    lines = [
        "# Track 4 Warm 재검증 split",
        "",
        "- 목적: 기존 `track4_test_warm.csv`가 137건으로 작아 Warm 최종 성능 판단이 흔들릴 수 있는 문제를 보완",
        "- 원칙: 기존 Track 4 split은 보존하고, Warm 재검증용 split만 별도 생성",
        "- 기준: 기존 Cold validation/test 작가는 제외하고 Warm 후보 작가에서 반복 holdout 생성",
        "- 저장 방식: train CSV를 seed별로 복제하지 않고, 평가 holdout membership과 seed별 평가 CSV만 저장",
        "- 재현 명령: `python3 scripts/track4/run_t4_e053_warm_recheck_split_revalidation.py`",
        "",
        "## 결과 요약",
        "",
        f"- seed 수: `{summary['seeds']}`",
        f"- 평균 평가 rows: `{summary['eval_rows_mean']:.1f}`",
        f"- 평균 평가 작가 수: `{summary['eval_artists_mean']:.1f}`",
        f"- Warm median APE 평균: `{summary['median_ape_mean']:.4f}`",
        f"- Warm median APE 표준편차: `{summary['median_ape_std']:.4f}`",
        f"- Warm p95 APE 평균: `{summary['p95_ape_mean']:.4f}`",
        "",
        "## 생성 파일",
        "",
        "- `warm_recheck_split_membership.csv`: seed별 Warm 평가 holdout row membership",
        "- `warm_recheck_summary.json`: split 생성 설정과 결과 요약",
        "- `seed_*_warm_eval.csv`: seed별 Warm 평가 rows",
    ]
    (OUT_SPLIT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    work = load_work()
    cold_artists = cold_eval_artists()
    pool = work.loc[~work["artist_key"].isin(cold_artists)].copy().reset_index(drop=True)

    membership_rows: list[dict[str, Any]] = []
    seed_results: list[dict[str, Any]] = []
    for seed in SEEDS:
        eval_idx = holdout_indices(pool, seed)
        eval_mask = pool.index.isin(eval_idx)
        train_raw = pool.loc[~eval_mask].copy()
        eval_raw = pool.loc[eval_mask].copy()

        train = add_artist_train_stats(train_raw, train_raw)
        eval_df = add_artist_train_stats(train_raw, eval_raw)

        model = build_model(seed)
        model.fit(train[FEATURES], train[TARGET_LOG])
        pred = model.predict(eval_df[FEATURES])
        seed_metric = metrics(eval_df, pred)

        eval_out = eval_df.drop(columns=[c for c in eval_df.columns if c.startswith("artist_train_")], errors="ignore")
        eval_out.to_csv(OUT_SPLIT_DIR / f"seed_{seed}_warm_eval.csv", index=False)

        for row_id, artist_key in eval_raw[["_track4_row_id", "artist_key"]].itertuples(index=False):
            membership_rows.append(
                {
                    "seed": seed,
                    "split": "warm_eval",
                    "track4_row_id": int(row_id),
                    "artist_key": artist_key,
                }
            )

        seed_results.append(
            {
                "seed": seed,
                "train_rows": int(len(train_raw)),
                "train_artists": int(train_raw["artist_key"].nunique()),
                "eval_rows": int(len(eval_raw)),
                "eval_artists": int(eval_raw["artist_key"].nunique()),
                "metrics": seed_metric,
            }
        )

    membership = pd.DataFrame(membership_rows)
    membership.to_csv(OUT_SPLIT_DIR / "warm_recheck_split_membership.csv", index=False)

    summary = summarize_seed_result(seed_results)
    result = {
        "experiment_id": "T4-E053",
        "hypothesis_id": "T4-H40",
        "date": date.today().isoformat(),
        "purpose": "Revalidate Warm final RandomForest on repeated expanded Warm holdout splits.",
        "input": str(INPUT.relative_to(REPO)),
        "base_split_reference": str(BASE_SPLIT_DIR.relative_to(REPO)),
        "output_split_dir": str(OUT_SPLIT_DIR.relative_to(REPO)),
        "excluded_cold_eval_artists": int(len(cold_artists)),
        "settings": {
            "seeds": SEEDS,
            "eligible_min_works": ELIGIBLE_MIN_WORKS,
            "eval_artist_frac": EVAL_ARTIST_FRAC,
            "max_eval_per_artist": MAX_EVAL_PER_ARTIST,
            "min_train_per_eval_artist": MIN_TRAIN_PER_EVAL_ARTIST,
            "features": FEATURES,
            "model": "RandomForestRegressor",
        },
        "seed_results": seed_results,
        "summary": summary,
        "reference_single_test": {
            "experiment_id": "T4-E049",
            "test_warm_rows": 137,
            "median_ape": 0.1970,
            "p95_ape": 0.9219,
            "within_30": 0.6715,
            "within_50": 0.8613,
        },
        "conclusion": {
            "status": "completed",
            "decision": "Use repeated Warm recheck metrics together with the original fixed split before final Warm performance claims.",
        },
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_SPLIT_DIR / "warm_recheck_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_readme(summary)

    print(RESULT_PATH)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
