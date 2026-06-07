#!/usr/bin/env python3
"""Track6 T6-E017: compare candidate models with fixed basic features."""
from __future__ import annotations

import json
import math
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LinearRegression, QuantileRegressor, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from scripts.track6.run_basic_feature_definition_experiments import prepare_frame, split_frame  # noqa: E402


EXP_ID = "T6-E017"
EXP_DIR = REPO / "experiments" / "track6" / "T6-E017_baseline_model_freeze"
SEED = 20260519

WARM_BASIC_CAT = ["artist_name_ko", "medium_category", "support_category"]
WARM_BASIC_NUM = ["ln_estimated_ho"]
WARM_MIN_CAT = ["artist_name_ko"]
WARM_MIN_NUM = ["ln_estimated_ho"]

COLD_BASIC_CAT = ["medium_category", "support_category"]
COLD_BASIC_NUM = ["ln_estimated_ho"]
COLD_MIN_CAT: list[str] = []
COLD_MIN_NUM = ["ln_estimated_ho"]

TARGET = "ln_price_krw"


def make_onehot() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def make_linear_preprocessor(cat_features: list[str], num_features: list[str]) -> ColumnTransformer:
    transformers = []
    if cat_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                        ("onehot", make_onehot()),
                    ]
                ),
                cat_features,
            )
        )
    if num_features:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                num_features,
            )
        )
    return ColumnTransformer(transformers)


def make_tree_preprocessor(cat_features: list[str], num_features: list[str]) -> ColumnTransformer:
    transformers = []
    if cat_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                        (
                            "ordinal",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                                encoded_missing_value=-1,
                            ),
                        ),
                    ]
                ),
                cat_features,
            )
        )
    if num_features:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                num_features,
            )
        )
    return ColumnTransformer(transformers)


def model_specs() -> list[dict]:
    specs = [
        {
            "model_name": "Linear Regression",
            "family": "linear",
            "estimator": LinearRegression(),
            "preprocess": "linear",
        },
        {
            "model_name": "Ridge",
            "family": "regularized_linear",
            "estimator": Ridge(alpha=1.0, random_state=SEED),
            "preprocess": "linear",
        },
        {
            "model_name": "Huber",
            "family": "linear_robust",
            "estimator": HuberRegressor(alpha=0.0001, epsilon=1.35, max_iter=300),
            "preprocess": "linear",
        },
        {
            "model_name": "Quantile / LAD",
            "family": "quantile_linear",
            "estimator": QuantileRegressor(quantile=0.5, alpha=0.001, solver="highs"),
            "preprocess": "linear",
        },
        {
            "model_name": "HistGradientBoosting",
            "family": "tree",
            "estimator": HistGradientBoostingRegressor(
                loss="squared_error",
                max_iter=250,
                learning_rate=0.05,
                l2_regularization=0.01,
                random_state=SEED,
            ),
            "preprocess": "tree",
        },
    ]
    try:
        from lightgbm import LGBMRegressor

        specs.append(
            {
                "model_name": "LightGBM",
                "family": "tree",
                "estimator": LGBMRegressor(
                    n_estimators=400,
                    learning_rate=0.04,
                    num_leaves=31,
                    min_child_samples=30,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    random_state=SEED,
                    verbose=-1,
                ),
                "preprocess": "tree",
            }
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        specs.append({"model_name": "LightGBM", "family": "tree", "skip_reason": repr(exc)})

    try:
        from xgboost import XGBRegressor

        specs.append(
            {
                "model_name": "XGBoost",
                "family": "tree",
                "estimator": XGBRegressor(
                    n_estimators=350,
                    learning_rate=0.04,
                    max_depth=5,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    objective="reg:squarederror",
                    random_state=SEED,
                    n_jobs=4,
                ),
                "preprocess": "tree",
            }
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        specs.append({"model_name": "XGBoost", "family": "tree", "skip_reason": repr(exc)})

    try:
        from catboost import CatBoostRegressor

        specs.append(
            {
                "model_name": "CatBoost",
                "family": "tree",
                "estimator": CatBoostRegressor(
                    iterations=350,
                    learning_rate=0.04,
                    depth=6,
                    loss_function="RMSE",
                    random_seed=SEED,
                    verbose=False,
                    allow_writing_files=False,
                ),
                "preprocess": "tree",
            }
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        specs.append({"model_name": "CatBoost", "family": "tree", "skip_reason": repr(exc)})
    return specs


def metrics_from_prediction(y_true_log: np.ndarray, y_pred_log: np.ndarray) -> dict[str, float]:
    y_true_price = np.exp(y_true_log)
    y_pred_price = np.exp(np.clip(y_pred_log, 0, 30))
    ape = np.abs(y_pred_price - y_true_price) / np.maximum(y_true_price, 1.0)
    return {
        "median_ape": float(np.median(ape)),
        "p95_ape": float(np.quantile(ape, 0.95)),
        "mape": float(np.mean(ape)),
        "within_30": float(np.mean(ape <= 0.30)),
        "within_50": float(np.mean(ape <= 0.50)),
        "rmse_log": float(math.sqrt(mean_squared_error(y_true_log, y_pred_log))),
    }


def fit_predict(
    spec: dict,
    train: pd.DataFrame,
    test: pd.DataFrame,
    cat_features: list[str],
    num_features: list[str],
) -> tuple[np.ndarray, float, str | None]:
    if "skip_reason" in spec:
        return np.array([]), 0.0, spec["skip_reason"]
    start = time.time()
    preprocessor = (
        make_linear_preprocessor(cat_features, num_features)
        if spec["preprocess"] == "linear"
        else make_tree_preprocessor(cat_features, num_features)
    )
    model = Pipeline([("prep", preprocessor), ("model", spec["estimator"])])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        model.fit(train[cat_features + num_features], train[TARGET])
    pred = model.predict(test[cat_features + num_features])
    return np.asarray(pred), time.time() - start, None


def save_dataset_files(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> None:
    data_dir = EXP_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    all_feature_cols = sorted(
        set(WARM_BASIC_CAT + WARM_BASIC_NUM + WARM_MIN_CAT + WARM_MIN_NUM + COLD_BASIC_CAT + COLD_BASIC_NUM)
    )
    id_cols = ["_experiment_row_id", "artist_key"]
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        frame[id_cols + all_feature_cols].to_csv(data_dir / f"{name}_features.csv", index=False)
        frame[id_cols + ["price_krw", "ln_price_krw"]].to_csv(data_dir / f"{name}_labels.csv", index=False)


def run_case(
    case_name: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    cat_features: list[str],
    num_features: list[str],
    split_name: str,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    pred_rows: list[dict] = []
    for spec in model_specs():
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {case_name} / {spec['model_name']}")
        pred, elapsed, skip_reason = fit_predict(spec, train, test, cat_features, num_features)
        row = {
            "experiment_id": EXP_ID,
            "case": case_name,
            "split": split_name,
            "model_name": spec["model_name"],
            "model_family": spec["family"],
            "cat_features": ", ".join(cat_features) if cat_features else "-",
            "num_features": ", ".join(num_features) if num_features else "-",
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "elapsed_sec": float(elapsed),
            "status": "skipped" if skip_reason else "ok",
            "skip_reason": skip_reason or "",
        }
        if skip_reason:
            row.update({k: np.nan for k in ["median_ape", "p95_ape", "mape", "within_30", "within_50", "rmse_log"]})
        else:
            row.update(metrics_from_prediction(test[TARGET].to_numpy(), pred))
            sample = pd.DataFrame(
                {
                    "experiment_case": case_name,
                    "split": split_name,
                    "model_name": spec["model_name"],
                    "_experiment_row_id": test["_experiment_row_id"].to_numpy(),
                    "artist_key": test["artist_key"].to_numpy(),
                    "actual_price": test["price_krw"].to_numpy(),
                    "pred_price": np.exp(np.clip(pred, 0, 30)),
                }
            )
            sample["ape"] = (sample["pred_price"] - sample["actual_price"]).abs() / sample["actual_price"].clip(lower=1.0)
            pred_rows.extend(sample.to_dict("records"))
        rows.append(row)
    return rows, pred_rows


def select_models(metrics: pd.DataFrame) -> dict:
    ok = metrics[metrics["status"].eq("ok")].copy()
    selected: dict[str, list[dict] | dict] = {}
    for split, label in [("warm_test", "warm"), ("cold_test", "cold")]:
        split_df = ok[ok["split"].eq(split)].sort_values(["median_ape", "p95_ape", "rmse_log"]).copy()
        selected[label] = split_df.head(3)[
            ["case", "model_name", "model_family", "median_ape", "p95_ape", "within_30", "within_50", "rmse_log"]
        ].to_dict("records")
    selected["by_case"] = {}
    for case_name in ["warm_min", "warm_basic", "cold_min", "cold_basic"]:
        case_df = ok[ok["case"].eq(case_name)].sort_values(["median_ape", "p95_ape", "rmse_log"]).copy()
        selected["by_case"][case_name] = case_df.head(3)[
            ["case", "model_name", "model_family", "median_ape", "p95_ape", "within_30", "within_50", "rmse_log"]
        ].to_dict("records")
    return selected


def make_slice_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    work = predictions.copy()
    work["price_bucket"] = pd.cut(
        work["actual_price"],
        bins=[0, 1_000_000, 3_000_000, 10_000_000, np.inf],
        labels=["under_1m", "1m_3m", "3m_10m", "10m_plus"],
    ).astype(str)
    rows = []
    for keys, group in work.groupby(["experiment_case", "split", "model_name", "price_bucket"], dropna=False):
        case, split, model_name, bucket = keys
        rows.append(
            {
                "experiment_case": case,
                "split": split,
                "model_name": model_name,
                "slice_type": "price_bucket",
                "slice_value": bucket,
                "n": int(len(group)),
                "median_ape": float(group["ape"].median()),
                "p95_ape": float(group["ape"].quantile(0.95)),
                "within_30": float((group["ape"] <= 0.30).mean()),
                "within_50": float((group["ape"] <= 0.50).mean()),
            }
        )
    return pd.DataFrame(rows)


def write_summary(metrics: pd.DataFrame, selected: dict, manifest: dict) -> None:
    display_cols = [
        "case",
        "split",
        "model_name",
        "status",
        "median_ape",
        "p95_ape",
        "within_30",
        "within_50",
        "rmse_log",
        "elapsed_sec",
    ]
    table_text = metrics.sort_values(["split", "median_ape"], na_position="last")[display_cols].to_csv(index=False)
    lines = [
        "# T6-E017 결과 요약",
        "",
        "- 실험 목적: 기본 피처셋을 고정한 상태에서 후보 모델 전체를 1차 비교",
        "- 실행 방식: Warm/Cold 모두 같은 후보 모델군을 기본 설정으로 1회 실행",
        "- 다음 단계: 같은 피처셋 안에서 상위 후보를 먼저 고른 뒤 Warm/Cold 최종 후보만 반복 실행, 튜닝, slice 안정성 검증",
        "",
        "## 데이터",
        "",
        f"- train: {manifest['rows']['train']:,}건 / {manifest['artists']['train']:,}명",
        f"- warm test: {manifest['rows']['warm_test']:,}건 / {manifest['artists']['warm_test']:,}명",
        f"- cold test: {manifest['rows']['cold_test']:,}건 / {manifest['artists']['cold_test']:,}명",
        f"- cold/train 작가 겹침: {manifest['checks']['cold_train_artist_overlap']}",
        "",
        "## 같은 피처셋 기준 모델 순위",
        "",
    ]
    case_labels = {
        "warm_min": "Warm 최소 피처",
        "warm_basic": "Warm 기본 피처",
        "cold_min": "Cold 최소 피처",
        "cold_basic": "Cold 기본 피처",
    }
    by_case = selected.get("by_case", {})
    for case_name, case_label in case_labels.items():
        lines.append(f"### {case_label}")
        for idx, row in enumerate(by_case.get(case_name, []), start=1):
            lines.append(
                f"- {idx}. {row['model_name']}: "
                f"median APE {row['median_ape']:.4f}, p95 {row['p95_ape']:.4f}, "
                f"Within-30 {row['within_30']:.4f}, Within-50 {row['within_50']:.4f}"
            )
        lines.append("")
    lines.append("## Warm/Cold 전체 후보 압축")
    lines.append("")
    for label in ["warm", "cold"]:
        lines.append(f"### {label.upper()} 상위 후보")
        for idx, row in enumerate(selected[label], start=1):
            lines.append(
                f"- {idx}. {row['model_name']} ({row['case']}): "
                f"median APE {row['median_ape']:.4f}, p95 {row['p95_ape']:.4f}, "
                f"Within-30 {row['within_30']:.4f}, Within-50 {row['within_50']:.4f}"
            )
        lines.append("")
    lines.extend(
        [
            "## 전체 지표",
            "",
            "```csv",
            table_text.strip(),
            "```",
            "",
        ]
    )
    (EXP_DIR / "outputs" / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    for sub in ["data", "outputs", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)

    log_path = EXP_DIR / "logs" / "run.log"
    log_path.write_text(f"started={datetime.now().isoformat()}\n", encoding="utf-8")

    df = prepare_frame()
    train, warm_test, cold_test, manifest = split_frame(df)
    manifest["experiment_id"] = EXP_ID
    manifest["created_at"] = datetime.now().isoformat()
    save_dataset_files(train, warm_test, cold_test)
    (EXP_DIR / "outputs" / "split_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    all_metrics: list[dict] = []
    all_predictions: list[dict] = []
    cases = [
        ("warm_min", warm_test, WARM_MIN_CAT, WARM_MIN_NUM, "warm_test"),
        ("warm_basic", warm_test, WARM_BASIC_CAT, WARM_BASIC_NUM, "warm_test"),
        ("cold_min", cold_test, COLD_MIN_CAT, COLD_MIN_NUM, "cold_test"),
        ("cold_basic", cold_test, COLD_BASIC_CAT, COLD_BASIC_NUM, "cold_test"),
    ]
    for case_name, test_df, cat_features, num_features, split_name in cases:
        rows, pred_rows = run_case(case_name, train, test_df, cat_features, num_features, split_name)
        all_metrics.extend(rows)
        all_predictions.extend(pred_rows)

    metrics = pd.DataFrame(all_metrics)
    predictions = pd.DataFrame(all_predictions)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    make_slice_metrics(predictions).to_csv(EXP_DIR / "outputs" / "slice_metrics.csv", index=False)

    selected = select_models(metrics)
    (EXP_DIR / "outputs" / "selected_models.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_summary(metrics, selected, manifest)
    log_path.write_text(log_path.read_text(encoding="utf-8") + f"finished={datetime.now().isoformat()}\n", encoding="utf-8")
    print(EXP_DIR / "outputs" / "metrics.csv")
    print(EXP_DIR / "outputs" / "selected_models.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
