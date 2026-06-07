#!/usr/bin/env python3
"""Track6 T6-E010: Hedonic artist + ho / log-transform experiment.

The experiment creates its own train/test files from the Track6 cleaned
candidate table so the data used for this run is reproducible from one script.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments" / "track6" / "T6-E010_hedonic_artist_ho_log"
DATA_DIR = EXP_DIR / "data"
OUT_DIR = EXP_DIR / "outputs"
LOG_DIR = EXP_DIR / "logs"
SOURCE = REPO / "data" / "track6" / "track6_feature_candidates_name_corrected.csv"

SEED = 20260519
TARGET_COLD_ROWS = 3000
MIN_WARM_TRAIN_WORKS = 5
MIN_WARM_TEST_PER_ARTIST = 2
MAX_WARM_TEST_PER_ARTIST = 3

# F-type canvas area table used in existing preparation scripts.
HO_TABLE_F = {
    0: 180,
    1: 364,
    2: 520,
    3: 727,
    4: 1084,
    5: 1167,
    6: 1338,
    8: 1818,
    10: 2412,
    12: 2757,
    15: 3478,
    20: 4304,
    25: 5323,
    30: 5858,
    40: 7320,
    50: 9128,
    60: 12636,
    80: 16918,
    100: 21245,
    120: 25740,
    150: 33894,
    200: 43980,
    300: 67060,
    500: 121898,
}


def make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def area_to_ho(area: float) -> int:
    if not np.isfinite(area) or area <= 0:
        return 0
    return min(HO_TABLE_F, key=lambda ho: abs(float(HO_TABLE_F[ho]) - float(area)))


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def prepare_base_frame() -> pd.DataFrame:
    raw = pd.read_csv(SOURCE, low_memory=False)
    df = raw.copy()
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["area_cm2"] = pd.to_numeric(df["area_cm2"], errors="coerce")
    df["width_cm"] = pd.to_numeric(df["width_cm"], errors="coerce")
    df["height_cm"] = pd.to_numeric(df["height_cm"], errors="coerce")
    df["artist_name_ko"] = df["artist_name_ko"].fillna("").astype(str).str.strip()
    df["artist_key"] = df["artist_key"].fillna("").astype(str).str.strip()
    df["_experiment_row_id"] = (
        df["track4_source"].fillna("").astype(str)
        + ":"
        + df["track4_source_row_index"].fillna("").astype(str)
    )

    candidate_mask = to_bool(df["is_training_candidate"])
    required_mask = (
        candidate_mask
        & df["artist_key"].ne("")
        & df["artist_name_ko"].ne("")
        & df["price_krw"].gt(0)
        & df["area_cm2"].gt(0)
    )
    df = df.loc[required_mask].copy()
    df["estimated_ho"] = df["area_cm2"].apply(area_to_ho).astype(float)
    df = df[df["estimated_ho"].gt(0)].copy()
    df["ln_estimated_ho"] = np.log(df["estimated_ho"].clip(lower=0.01))
    df["ln_price_krw"] = np.log(df["price_krw"])
    df["ho_bucket"] = pd.cut(
        df["estimated_ho"],
        bins=[-0.01, 5, 20, 50, 100, np.inf],
        labels=["0-5", "5-20", "20-50", "50-100", "100+"],
    ).astype(str)
    df["price_bucket"] = pd.cut(
        df["price_krw"],
        bins=[0, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["under_1m", "1m_3m", "3m_10m", "10m_plus"],
    ).astype(str)
    return df.reset_index(drop=True)


def split_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    artist_counts = df.groupby("artist_key").size().sort_values(ascending=False)
    artist_keys = artist_counts.index.to_numpy()
    rng.shuffle(artist_keys)

    cold_artists: list[str] = []
    cold_rows = 0
    for artist in artist_keys:
        if cold_rows >= TARGET_COLD_ROWS:
            break
        count = int(artist_counts.loc[artist])
        cold_artists.append(str(artist))
        cold_rows += count
    cold_artist_set = set(cold_artists)
    cold_test = df[df["artist_key"].isin(cold_artist_set)].copy()
    warm_pool = df[~df["artist_key"].isin(cold_artist_set)].copy()

    warm_test_indices: list[int] = []
    for artist, group in warm_pool.groupby("artist_key", sort=False):
        n = len(group)
        if n <= MIN_WARM_TRAIN_WORKS:
            continue
        max_holdout = min(MAX_WARM_TEST_PER_ARTIST, n - MIN_WARM_TRAIN_WORKS)
        if max_holdout < MIN_WARM_TEST_PER_ARTIST:
            continue
        holdout_n = max(1, min(max_holdout, int(round(n * 0.2))))
        holdout_n = max(MIN_WARM_TEST_PER_ARTIST, holdout_n)
        holdout_n = min(holdout_n, max_holdout)
        picked = rng.choice(group.index.to_numpy(), size=holdout_n, replace=False)
        warm_test_indices.extend(int(i) for i in picked)

    warm_test = warm_pool.loc[warm_test_indices].copy()
    train = warm_pool.drop(index=warm_test_indices).copy()

    train_counts = train.groupby("artist_key").size()
    warm_test = warm_test[warm_test["artist_key"].map(train_counts).fillna(0).ge(MIN_WARM_TRAIN_WORKS)].copy()

    manifest = {
        "source": str(SOURCE.relative_to(REPO)),
        "seed": SEED,
        "target_cold_rows": TARGET_COLD_ROWS,
        "min_warm_train_works": MIN_WARM_TRAIN_WORKS,
        "min_warm_test_per_artist": MIN_WARM_TEST_PER_ARTIST,
        "rows": {
            "candidate_after_filter": int(len(df)),
            "train": int(len(train)),
            "warm_test": int(len(warm_test)),
            "cold_test": int(len(cold_test)),
        },
        "artists": {
            "train": int(train["artist_key"].nunique()),
            "warm_test": int(warm_test["artist_key"].nunique()),
            "cold_test": int(cold_test["artist_key"].nunique()),
        },
        "checks": {
            "cold_train_artist_overlap": int(len(set(train["artist_key"]).intersection(set(cold_test["artist_key"])))),
            "warm_test_min_train_works": int(warm_test["artist_key"].map(train_counts).min()) if len(warm_test) else 0,
            "warm_test_rows_per_artist_min": int(warm_test.groupby("artist_key").size().min()) if len(warm_test) else 0,
        },
        "ho_definition": "estimated_ho is nearest F-type ho from area_cm2 using HO_TABLE_F",
    }
    return train.reset_index(drop=True), warm_test.reset_index(drop=True), cold_test.reset_index(drop=True), manifest


def export_experiment_data(train: pd.DataFrame, warm_test: pd.DataFrame, cold_test: pd.DataFrame) -> dict[str, str]:
    def write_csv(name: str, frame: pd.DataFrame) -> str:
        path = DATA_DIR / name
        frame.to_csv(path, index=False)
        return str(path.relative_to(REPO))

    metadata_cols = [
        "_experiment_row_id",
        "artist_key",
        "artist_name_ko",
        "title_raw",
        "track4_source",
        "source_artwork_id",
        "area_cm2",
        "estimated_ho",
        "ln_estimated_ho",
        "ho_bucket",
        "price_bucket",
    ]
    labels = ["_experiment_row_id", "price_krw", "ln_price_krw"]
    files = {
        "warm_train_base_features": write_csv(
            "warm_train_base_features.csv",
            train[["_experiment_row_id", "artist_name_ko", "estimated_ho"]],
        ),
        "warm_train_base_labels": write_csv("warm_train_base_labels.csv", train[labels]),
        "warm_train_log_features": write_csv(
            "warm_train_log_features.csv",
            train[["_experiment_row_id", "artist_name_ko", "estimated_ho", "ln_estimated_ho"]],
        ),
        "warm_train_log_labels": write_csv("warm_train_log_labels.csv", train[labels]),
        "warm_test_base_features": write_csv(
            "warm_test_base_features.csv",
            warm_test[["_experiment_row_id", "artist_name_ko", "estimated_ho"]],
        ),
        "warm_test_log_features": write_csv(
            "warm_test_log_features.csv",
            warm_test[["_experiment_row_id", "artist_name_ko", "estimated_ho", "ln_estimated_ho"]],
        ),
        "warm_test_labels": write_csv("warm_test_labels.csv", warm_test[labels]),
        "warm_test_metadata": write_csv("warm_test_metadata.csv", warm_test[metadata_cols]),
        "cold_train_base_features": write_csv(
            "cold_train_base_features.csv",
            train[["_experiment_row_id", "estimated_ho"]],
        ),
        "cold_train_base_labels": write_csv("cold_train_base_labels.csv", train[labels]),
        "cold_train_log_features": write_csv(
            "cold_train_log_features.csv",
            train[["_experiment_row_id", "estimated_ho", "ln_estimated_ho"]],
        ),
        "cold_train_log_labels": write_csv("cold_train_log_labels.csv", train[labels]),
        "cold_test_base_features": write_csv(
            "cold_test_base_features.csv",
            cold_test[["_experiment_row_id", "estimated_ho"]],
        ),
        "cold_test_log_features": write_csv(
            "cold_test_log_features.csv",
            cold_test[["_experiment_row_id", "estimated_ho", "ln_estimated_ho"]],
        ),
        "cold_test_labels": write_csv("cold_test_labels.csv", cold_test[labels]),
        "cold_test_metadata": write_csv("cold_test_metadata.csv", cold_test[metadata_cols]),
    }
    return files


def build_model(cat_cols: list[str], num_cols: list[str]) -> Pipeline:
    transformers = []
    if cat_cols:
        transformers.append(("cat", make_encoder(), cat_cols))
    if num_cols:
        transformers.append(("num", StandardScaler(), num_cols))
    pre = ColumnTransformer(transformers=transformers, remainder="drop")
    return Pipeline([("preprocess", pre), ("model", Ridge(alpha=1.0))])


def metrics(actual: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    pred = np.clip(np.asarray(pred, dtype=float), 1_000.0, None)
    ape = np.abs(pred - actual) / actual
    return {
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "mape": float(np.mean(ape)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "rmse_log": float(math.sqrt(mean_squared_error(np.log(actual), np.log(pred)))),
    }


def predict_and_score(
    name: str,
    train_x: pd.DataFrame,
    train_y: pd.Series,
    test_x: pd.DataFrame,
    test_y: pd.Series,
    cat_cols: list[str],
    num_cols: list[str],
    target_mode: str,
    metadata: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:
    model = build_model(cat_cols=cat_cols, num_cols=num_cols)
    model.fit(train_x[cat_cols + num_cols], train_y)
    raw_pred = model.predict(test_x[cat_cols + num_cols])
    if target_mode == "log":
        pred = np.exp(raw_pred)
    else:
        pred = raw_pred
    pred = np.clip(pred, 1_000.0, None)
    out = metadata.copy()
    out["actual_price_krw"] = test_y.to_numpy(dtype=float)
    out["pred_price_krw"] = pred
    out["ape"] = np.abs(out["pred_price_krw"] - out["actual_price_krw"]) / out["actual_price_krw"]
    score = {"experiment_case": name, "n": int(len(out)), **metrics(test_y.to_numpy(dtype=float), pred)}
    return score, out


def slice_metrics(predictions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for case, pred in predictions.items():
        for slice_col in ["ho_bucket", "price_bucket"]:
            for value, group in pred.groupby(slice_col, dropna=False):
                if len(group) < 20:
                    continue
                rows.append(
                    {
                        "experiment_case": case,
                        "slice_type": slice_col,
                        "slice_value": str(value),
                        "n": int(len(group)),
                        "median_ape": float(group["ape"].median()),
                        "p95_ape": float(group["ape"].quantile(0.95)),
                        "within_30": float((group["ape"] <= 0.30).mean()),
                        "within_50": float((group["ape"] <= 0.50).mean()),
                    }
                )
    return pd.DataFrame(rows)


def write_summary(metrics_df: pd.DataFrame, manifest: dict, files: dict[str, str]) -> None:
    warm_rows = metrics_df[metrics_df["experiment_case"].str.contains("warm_test")]
    cold_rows = metrics_df[metrics_df["experiment_case"].str.contains("cold_test")]
    best_warm = warm_rows.sort_values("median_ape").iloc[0].to_dict()
    best_cold = cold_rows.sort_values("median_ape").iloc[0].to_dict()

    def markdown_table(frame: pd.DataFrame) -> str:
        view = frame.copy()
        for col in view.columns:
            if pd.api.types.is_float_dtype(view[col]):
                view[col] = view[col].map(lambda value: f"{value:.4f}")
            else:
                view[col] = view[col].astype(str)
        headers = list(view.columns)
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for _, row in view.iterrows():
            lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
        return "\n".join(lines)

    path = OUT_DIR / "summary.md"
    path.write_text(
        "\n".join(
            [
                "# T6-E010 결과 요약",
                "",
                "- 실험 목적: 작가명(한글)과 추정 호수만으로 가격 예측 신호가 있는지 확인",
                "- 비교 목적: 원 가격/원 호수 조합과 ln 변환 조합 중 어떤 방식이 나은지 확인",
                "- 모델: Ridge 기반 헤도닉 선형 회귀",
                "- 데이터 원본: `data/track6/track6_feature_candidates_name_corrected.csv`",
                "- 호수 생성: `area_cm2`를 기존 F형 호수 면적표와 비교해 가장 가까운 호수로 변환",
                "",
                "## 데이터 구성",
                "",
                f"- train: {manifest['rows']['train']:,}건 / {manifest['artists']['train']:,}명",
                f"- warm_test: {manifest['rows']['warm_test']:,}건 / {manifest['artists']['warm_test']:,}명",
                f"- cold_test: {manifest['rows']['cold_test']:,}건 / {manifest['artists']['cold_test']:,}명",
                f"- Cold/train 작가 겹침: {manifest['checks']['cold_train_artist_overlap']}",
                f"- Warm test 작가별 train 최소 작품 수: {manifest['checks']['warm_test_min_train_works']}",
                f"- Warm test 작가별 평가 최소 작품 수: {manifest['checks']['warm_test_rows_per_artist_min']}",
                "",
                "## 핵심 결과",
                "",
                f"- Warm 최고: `{best_warm['experiment_case']}` median APE `{best_warm['median_ape']:.4f}`",
                f"- Cold 최고: `{best_cold['experiment_case']}` median APE `{best_cold['median_ape']:.4f}`",
                "- 낮을수록 좋은 지표: median APE, p95 APE, MAPE, RMSE(log)",
                "- 높을수록 좋은 지표: Within-30, Within-50",
                "",
                "## 생성 파일",
                "",
                *[f"- `{value}`" for value in files.values()],
                "",
                "## 전체 지표",
                "",
                markdown_table(metrics_df),
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run.log"

    started_at = datetime.now().isoformat(timespec="seconds")
    df = prepare_base_frame()
    train, warm_test, cold_test, manifest = split_frame(df)
    files = export_experiment_data(train, warm_test, cold_test)

    warm_meta = warm_test[
        [
            "_experiment_row_id",
            "artist_key",
            "artist_name_ko",
            "title_raw",
            "track4_source",
            "estimated_ho",
            "ln_estimated_ho",
            "ho_bucket",
            "price_bucket",
        ]
    ].reset_index(drop=True)
    cold_meta = cold_test[
        [
            "_experiment_row_id",
            "artist_key",
            "artist_name_ko",
            "title_raw",
            "track4_source",
            "estimated_ho",
            "ln_estimated_ho",
            "ho_bucket",
            "price_bucket",
        ]
    ].reset_index(drop=True)

    cases = [
        (
            "warm_model_warm_test_base",
            train[["artist_name_ko", "estimated_ho"]],
            train["price_krw"],
            warm_test[["artist_name_ko", "estimated_ho"]],
            warm_test["price_krw"],
            ["artist_name_ko"],
            ["estimated_ho"],
            "raw",
            warm_meta,
        ),
        (
            "warm_model_warm_test_log",
            train[["artist_name_ko", "ln_estimated_ho"]],
            train["ln_price_krw"],
            warm_test[["artist_name_ko", "ln_estimated_ho"]],
            warm_test["price_krw"],
            ["artist_name_ko"],
            ["ln_estimated_ho"],
            "log",
            warm_meta,
        ),
        (
            "warm_model_cold_test_base",
            train[["artist_name_ko", "estimated_ho"]],
            train["price_krw"],
            cold_test[["artist_name_ko", "estimated_ho"]],
            cold_test["price_krw"],
            ["artist_name_ko"],
            ["estimated_ho"],
            "raw",
            cold_meta,
        ),
        (
            "warm_model_cold_test_log",
            train[["artist_name_ko", "ln_estimated_ho"]],
            train["ln_price_krw"],
            cold_test[["artist_name_ko", "ln_estimated_ho"]],
            cold_test["price_krw"],
            ["artist_name_ko"],
            ["ln_estimated_ho"],
            "log",
            cold_meta,
        ),
        (
            "cold_model_cold_test_base",
            train[["estimated_ho"]],
            train["price_krw"],
            cold_test[["estimated_ho"]],
            cold_test["price_krw"],
            [],
            ["estimated_ho"],
            "raw",
            cold_meta,
        ),
        (
            "cold_model_cold_test_log",
            train[["ln_estimated_ho"]],
            train["ln_price_krw"],
            cold_test[["ln_estimated_ho"]],
            cold_test["price_krw"],
            [],
            ["ln_estimated_ho"],
            "log",
            cold_meta,
        ),
        (
            "cold_model_warm_test_base",
            train[["estimated_ho"]],
            train["price_krw"],
            warm_test[["estimated_ho"]],
            warm_test["price_krw"],
            [],
            ["estimated_ho"],
            "raw",
            warm_meta,
        ),
        (
            "cold_model_warm_test_log",
            train[["ln_estimated_ho"]],
            train["ln_price_krw"],
            warm_test[["ln_estimated_ho"]],
            warm_test["price_krw"],
            [],
            ["ln_estimated_ho"],
            "log",
            warm_meta,
        ),
    ]

    rows = []
    predictions: dict[str, pd.DataFrame] = {}
    for case in cases:
        score, pred = predict_and_score(*case)
        rows.append(score)
        predictions[score["experiment_case"]] = pred
        pred.to_csv(OUT_DIR / f"predictions_{score['experiment_case']}.csv", index=False)

    metrics_df = pd.DataFrame(rows).sort_values(["experiment_case"]).reset_index(drop=True)
    metrics_df.to_csv(OUT_DIR / "metrics.csv", index=False)
    slices = slice_metrics(predictions)
    slices.to_csv(OUT_DIR / "slice_metrics.csv", index=False)

    finished_at = datetime.now().isoformat(timespec="seconds")
    manifest["started_at"] = started_at
    manifest["finished_at"] = finished_at
    manifest["generated_files"] = files
    (OUT_DIR / "experiment_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary(metrics_df, manifest, files)
    log_path.write_text(
        "\n".join(
            [
                f"started_at={started_at}",
                f"finished_at={finished_at}",
                f"source={SOURCE}",
                f"train_rows={manifest['rows']['train']}",
                f"warm_test_rows={manifest['rows']['warm_test']}",
                f"cold_test_rows={manifest['rows']['cold_test']}",
                "status=completed",
            ]
        ),
        encoding="utf-8",
    )

    print(metrics_df.to_string(index=False))
    print(f"\nsummary: {OUT_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
