#!/usr/bin/env python3
"""Run T6-E005 operational feature-combination ablation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
WARM_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E005_feature_combo_ablation.md"
RESULT_JSON = RESULT_DIR / "t6_e005_feature_combo_ablation.json"
RESULT_CSV = RESULT_DIR / "t6_e005_feature_combo_ablation_metrics.csv"
PRED_CSV = PRED_DIR / "t6_e005_feature_combo_ablation_predictions.csv"

BASE_NUMERIC = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
BASE_CATEGORICAL = ["has_depth", "is_3d_candidate", "medium_category", "support_category"]
EXISTING_COMBO = ["medium_support_bucket", "is_extreme_aspect_ratio"]
GENERATED_COMBO = [
    "size_bucket",
    "shape_bucket",
    "medium_size_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]
ARTIST_FEATURES = ["artist_key"]

FEATURE_SETS = {
    "base": BASE_NUMERIC + BASE_CATEGORICAL,
    "base_existing_combo": BASE_NUMERIC + BASE_CATEGORICAL + EXISTING_COMBO,
    "base_size_shape": BASE_NUMERIC + BASE_CATEGORICAL + ["size_bucket", "shape_bucket"],
    "base_medium_size": BASE_NUMERIC + BASE_CATEGORICAL + ["size_bucket", "medium_size_bucket"],
    "base_support_size": BASE_NUMERIC + BASE_CATEGORICAL + ["size_bucket", "support_size_bucket"],
    "base_medium_shape": BASE_NUMERIC + BASE_CATEGORICAL + ["shape_bucket", "medium_shape_bucket"],
    "base_large_flags": BASE_NUMERIC + BASE_CATEGORICAL + ["size_bucket", "is_large_2d", "is_large_3d"],
    "all_operational_combos": BASE_NUMERIC + BASE_CATEGORICAL + EXISTING_COMBO + GENERATED_COMBO,
}


def read_pair(feature_path: Path, label_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.read_csv(feature_path), pd.read_csv(label_path)


def size_edges(train: pd.DataFrame) -> np.ndarray:
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    quantiles = np.quantile(values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    quantiles[0] = -np.inf
    quantiles[-1] = np.inf
    return np.unique(quantiles)


def add_generated_features(train: pd.DataFrame, val: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    edges = size_edges(train)
    train_area = pd.to_numeric(train["area_cm2"], errors="coerce")
    large_cut = float(np.nanquantile(train_area, 0.80))

    def transform(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        log_area = pd.to_numeric(out["log_area"], errors="coerce")
        aspect = pd.to_numeric(out["aspect_ratio"], errors="coerce")
        area = pd.to_numeric(out["area_cm2"], errors="coerce")
        is_3d = out["is_3d_candidate"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])

        labels = [f"q{i + 1}" for i in range(len(edges) - 1)]
        out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
        out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"

        out["shape_bucket"] = np.select(
            [
                aspect.isna(),
                aspect < 0.65,
                aspect <= 1.55,
                aspect <= 2.5,
                aspect > 2.5,
            ],
            ["__MISSING__", "tall", "balanced", "wide", "extreme_wide"],
            default="__MISSING__",
        )
        out["medium_size_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["support_size_bucket"] = out["support_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["medium_shape_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["shape_bucket"].astype(str)
        out["is_large_2d"] = ((area >= large_cut) & ~is_3d).astype(str)
        out["is_large_3d"] = ((area >= large_cut) & is_3d).astype(str)
        return out

    return transform(train), transform(val)


def merge_xy(feature: pd.DataFrame, label: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    label_cols = ["_track6_row_id", "ln_price_krw", "price_krw"]
    for meta_col in ["artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]:
        if meta_col not in feature.columns:
            label_cols.append(meta_col)
    merged = feature[["_track6_row_id", *columns]].merge(
        label[label_cols],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    x = merged[columns].copy()
    for col in columns:
        if col in BASE_NUMERIC or col == "artist_works_count_train" or col == "artist_works_log":
            x[col] = pd.to_numeric(x[col], errors="coerce")
        else:
            x[col] = x[col].fillna("__MISSING__").astype(str)
    return x, merged["ln_price_krw"].astype(float), merged["price_krw"].astype(float), merged


def split_feature_types(columns: list[str]) -> tuple[list[str], list[str]]:
    numeric = [col for col in columns if col in BASE_NUMERIC]
    categorical = [col for col in columns if col not in numeric]
    return numeric, categorical


def ordinal_preprocessor(columns: list[str]) -> ColumnTransformer:
    numeric, categorical = split_feature_types(columns)
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric),
        ("cat", Pipeline([("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))]), categorical),
    ])


def onehot_preprocessor(columns: list[str]) -> ColumnTransformer:
    numeric, categorical = split_feature_types(columns)
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=10))]), categorical),
    ])


def warm_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=20260518,
        verbose=False,
        allow_writing_files=False,
    )


def cold_median_model(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("prep", ordinal_preprocessor(columns)),
        ("model", HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.5,
            learning_rate=0.05,
            max_iter=250,
            max_leaf_nodes=31,
            l2_regularization=0.05,
            random_state=20260518,
        )),
    ])


def cold_tail_model(columns: list[str]) -> Pipeline:
    return Pipeline([
        ("prep", onehot_preprocessor(columns)),
        ("model", HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000)),
    ])


def cat_feature_indices(columns: list[str]) -> list[int]:
    numeric, _categorical = split_feature_types(columns)
    return [idx for idx, col in enumerate(columns) if col not in numeric]


def metrics(y_true_price: pd.Series, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.exp(pred_log)
    y = y_true_price.to_numpy(dtype=float)
    ape = np.abs(pred_price - y) / y
    log_true = np.log(y)
    return {
        "median_ape": float(np.median(ape)),
        "mape": float(np.mean(ape)),
        "p90_ape": float(np.quantile(ape, 0.90)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "rmse_log": float(np.sqrt(np.mean((pred_log - log_true) ** 2))),
    }


def prediction_frame(split: str, model_name: str, merged: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    meta_cols = [col for col in ["artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"] if col in merged.columns]
    out = merged[["_track6_row_id", "price_krw", "ln_price_krw", *meta_cols]].copy()
    out["split"] = split
    out["model"] = model_name
    out["pred_ln_price_krw"] = pred_log
    out["pred_price_krw"] = np.exp(pred_log)
    out["ape"] = np.abs(out["pred_price_krw"] - out["price_krw"]) / out["price_krw"]
    return out


def run_warm(train_f: pd.DataFrame, train_l: pd.DataFrame, val_f: pd.DataFrame, val_l: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for feature_set, columns in FEATURE_SETS.items():
        warm_columns = columns + ARTIST_FEATURES
        x_train, y_train, _price_train, _merged_train = merge_xy(train_f, train_l, warm_columns)
        x_val, _y_val, y_price, merged_val = merge_xy(val_f, val_l, warm_columns)
        model = warm_model()
        model.fit(x_train, y_train, cat_features=cat_feature_indices(warm_columns))
        pred_log = np.asarray(model.predict(x_val), dtype=float)
        row = {
            "split": "val_warm",
            "model": "catboost_warm_artist",
            "feature_set": feature_set,
            "features": warm_columns,
        }
        row.update(metrics(y_price, pred_log))
        rows.append(row)
        preds.append(prediction_frame("val_warm", f"catboost_warm_artist__{feature_set}", merged_val, pred_log))
    return rows, preds


def run_cold(train_f: pd.DataFrame, train_l: pd.DataFrame, val_f: pd.DataFrame, val_l: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for feature_set, columns in FEATURE_SETS.items():
        x_train, y_train, _price_train, _merged_train = merge_xy(train_f, train_l, columns)
        x_val, _y_val, y_price, merged_val = merge_xy(val_f, val_l, columns)
        for model_name, build in [
            ("hist_quantile_cold", cold_median_model),
            ("huber_cold", cold_tail_model),
        ]:
            model = build(columns)
            model.fit(x_train, y_train)
            pred_log = np.asarray(model.predict(x_val), dtype=float)
            row = {"split": "val_cold", "model": model_name, "feature_set": feature_set, "features": columns}
            row.update(metrics(y_price, pred_log))
            rows.append(row)
            preds.append(prediction_frame("val_cold", f"{model_name}__{feature_set}", merged_val, pred_log))
    return rows, preds


def render_experiment(result: dict[str, Any]) -> str:
    warm_best = result["warm_best"]
    cold_best = result["cold_best"]
    cold_tail_best = result["cold_tail_best"]
    lines = [
        "# T6-E005 피처 조합 ablation",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H5`",
        "- 상태: 검증 완료",
        "- 목적: 운영에서 만들 수 있는 크기/재료/지지체 조합 피처가 Warm/Cold 성능을 개선하는지 확인",
        "- 사용 데이터: Track6 name-corrected feature/label split",
        "- 사용 스크립트: `scripts/track6/run_t6_e005_feature_combo_ablation.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- 예측 CSV: `{result['prediction_csv']}`",
        "",
        "## 1. 실험 방법",
        "",
        "- Warm: T6-E003에서 검증된 `CatBoost + artist_key` 구조를 고정하고 피처 조합만 변경",
        "- Cold: T6-E004에서 확인한 `hist_quantile`과 `huber`를 사용해 대표 오차와 큰 오차를 같이 확인",
        "- size bucket은 train 기준 `log_area` 분위수로 만들고 validation에는 같은 기준을 적용",
        "- 정답 가격은 feature 생성에 사용하지 않고 평가 단계에서만 label 파일을 결합",
        "",
        "## 2. validation 결과",
        "",
        "| split | model | feature set | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| `{row['split']}` | `{row['model']}` | `{row['feature_set']}` | `{row['median_ape']:.4f}` | "
            f"`{row['p95_ape']:.4f}` | `{row['within_30']:.4f}` | `{row['within_50']:.4f}` | `{row['rmse_log']:.4f}` |"
        )
    lines += [
        "",
        "## 3. 핵심 해석",
        "",
        f"- Warm 최저 median APE: `{warm_best['median_ape']:.4f}` (`{warm_best['feature_set']}`)",
        f"- Cold 최저 median APE: `{cold_best['median_ape']:.4f}` (`{cold_best['model']}`, `{cold_best['feature_set']}`)",
        f"- Cold 최저 p95 APE: `{cold_tail_best['p95_ape']:.4f}` (`{cold_tail_best['model']}`, `{cold_tail_best['feature_set']}`)",
        "- Warm과 Cold에서 같은 조합 피처가 항상 같은 방향으로 작동하지 않으므로 모델별 피처셋 분리 관리가 필요",
        "",
        "## 4. 결론",
        "",
        "- T6-H5는 validation 기준 검증 완료",
        "- 피처 조합은 후보 선정에 포함하되, Warm/Cold 최종 피처셋은 별도로 고정해야 함",
        "- 다음 단계는 validation 기준 최종 후보 선정(T6-E006)",
        "",
    ]
    return "\n".join(lines)


def replace_table_row(path: Path, prefix: str, row: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = row
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    marker = "| 2026-05-18 | T6-E004 |"
    path.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def update_docs(result: dict[str, Any]) -> None:
    warm_best = result["warm_best"]
    cold_best = result["cold_best"]
    cold_tail_best = result["cold_tail_best"]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    row = (
        "| T6-H5 | T6-G5 | 크기/재료/지지체 조합 피처는 일부 구간 성능을 개선할 수 있다 | "
        "기본 피처에 운영 가능 조합 피처를 하나씩 추가하고 Warm/Cold validation 성능 비교 | Track6 name-corrected split | "
        "size_bucket, shape_bucket, medium_size_bucket, support_size_bucket | 기본 피처셋 | median 또는 p95 개선 | "
        f"검증 완료 | Warm/Cold validation feature ablation | Warm best `{warm_best['median_ape']:.4f}` (`{warm_best['feature_set']}`), "
        f"Cold median best `{cold_best['median_ape']:.4f}` (`{cold_best['feature_set']}`), Cold p95 best `{cold_tail_best['p95_ape']:.4f}` (`{cold_tail_best['feature_set']}`) | T6-E005 | T6-E006 진행 |"
    )
    replace_table_row(hypo, "| T6-H5 |", row)

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    row = (
        f"| {result['created_at']} | T6-E005 | T6-H5 | 검증 완료 | Track6 name-corrected split | "
        "CatBoost / HistQuantile / Huber | 운영 가능 조합 피처 | "
        f"best `{warm_best['median_ape']:.4f}` (`{warm_best['feature_set']}`) | "
        f"median best `{cold_best['median_ape']:.4f}` (`{cold_best['feature_set']}`), p95 best `{cold_tail_best['p95_ape']:.4f}` (`{cold_tail_best['feature_set']}`) | "
        "Warm/Cold별 후보 피처셋 분리 필요 | [기록](../experiments/2026-05-18_T6-E005_feature_combo_ablation.md) |"
    )
    replace_table_row(results, "| 2026-05-18 | T6-E005 |", row)

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    row = "| 2026-05-18 | T6-E005 | T6-H5 | 검증 완료 | 피처 조합 ablation 완료 | [기록](2026-05-18_T6-E005_feature_combo_ablation.md) |"
    replace_table_row(index, "| 2026-05-18 | T6-E005 |", row)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    warm_train_f, warm_train_l = read_pair(WARM_FEATURE_DIR / "track6_train_warm_features.csv", LABEL_DIR / "track6_train_labels.csv")
    warm_val_f, warm_val_l = read_pair(WARM_FEATURE_DIR / "track6_val_warm_warm_features.csv", LABEL_DIR / "track6_val_warm_labels.csv")
    cold_train_f, cold_train_l = read_pair(COLD_FEATURE_DIR / "track6_train_cold_features.csv", LABEL_DIR / "track6_train_labels.csv")
    cold_val_f, cold_val_l = read_pair(COLD_FEATURE_DIR / "track6_val_cold_cold_features.csv", LABEL_DIR / "track6_val_cold_labels.csv")

    warm_train_f, warm_val_f = add_generated_features(warm_train_f, warm_val_f)
    cold_train_f, cold_val_f = add_generated_features(cold_train_f, cold_val_f)

    warm_rows, warm_preds = run_warm(warm_train_f, warm_train_l, warm_val_f, warm_val_l)
    cold_rows, cold_preds = run_cold(cold_train_f, cold_train_l, cold_val_f, cold_val_l)

    metric_df = pd.DataFrame(warm_rows + cold_rows).sort_values(["split", "median_ape", "p95_ape", "model"])
    pred_df = pd.concat(warm_preds + cold_preds, ignore_index=True)
    metric_df.to_csv(RESULT_CSV, index=False)
    pred_df.to_csv(PRED_CSV, index=False)

    warm_best = metric_df.loc[metric_df["split"].eq("val_warm")].sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict()
    cold_best = metric_df.loc[metric_df["split"].eq("val_cold")].sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict()
    cold_tail_best = metric_df.loc[metric_df["split"].eq("val_cold")].sort_values(["p95_ape", "median_ape"]).iloc[0].to_dict()

    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E005",
        "hypothesis_id": "T6-H5",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "metrics": metric_df.to_dict(orient="records"),
        "warm_best": warm_best,
        "cold_best": cold_best,
        "cold_tail_best": cold_tail_best,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render_experiment(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps({
        "result": str(RESULT_JSON.relative_to(REPO)),
        "warm_best": warm_best,
        "cold_best": cold_best,
        "cold_tail_best": cold_tail_best,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
