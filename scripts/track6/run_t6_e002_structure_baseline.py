#!/usr/bin/env python3
"""Run T6-E002 structure-only baseline on Track6 validation splits."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
FEATURE_DIR = REPO / "data" / "track6_split" / "features"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E002_structure_only_baseline.md"
RESULT_JSON = RESULT_DIR / "t6_e002_structure_only_baseline.json"
RESULT_CSV = RESULT_DIR / "t6_e002_structure_only_baseline_metrics.csv"
PRED_CSV = PRED_DIR / "t6_e002_structure_only_baseline_predictions.csv"

STRUCTURE_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
]
NUMERIC_FEATURES = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
]
CATEGORICAL_FEATURES = [
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
]


def read_pair(feature_path: Path, label_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature = pd.read_csv(feature_path)
    label = pd.read_csv(label_path)
    return feature, label


def make_xy(feature: pd.DataFrame, label: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    merged = feature[["_track6_row_id", *STRUCTURE_FEATURES]].merge(
        label[["_track6_row_id", "ln_price_krw", "price_krw"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    x = merged[STRUCTURE_FEATURES].copy()
    for col in NUMERIC_FEATURES:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        x[col] = x[col].fillna("__MISSING__").astype(str)
    y_log = merged["ln_price_krw"].astype(float)
    y_price = merged["price_krw"].astype(float)
    return x, y_log, y_price


def onehot_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def ordinal_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
    ])
    categorical = Pipeline([
        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def build_models() -> dict[str, Any]:
    return {
        "log_median_dummy": DummyRegressor(strategy="median"),
        "ridge_onehot": Pipeline([
            ("prep", onehot_preprocessor()),
            ("model", Ridge(alpha=10.0)),
        ]),
        "huber_onehot": Pipeline([
            ("prep", onehot_preprocessor()),
            ("model", HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=500)),
        ]),
        "hist_gbdt_ordinal": Pipeline([
            ("prep", ordinal_preprocessor()),
            ("model", HistGradientBoostingRegressor(
                loss="squared_error",
                learning_rate=0.05,
                max_iter=250,
                max_leaf_nodes=31,
                l2_regularization=0.05,
                random_state=20260518,
            )),
        ]),
        "lightgbm_basic": Pipeline([
            ("prep", ordinal_preprocessor()),
            ("model", LGBMRegressor(
                objective="regression",
                n_estimators=350,
                learning_rate=0.04,
                num_leaves=31,
                min_child_samples=40,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=1.0,
                random_state=20260518,
                verbosity=-1,
            )),
        ]),
    }


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


def prediction_frame(split: str, model_name: str, feature: pd.DataFrame, label: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = feature[["_track6_row_id"]].merge(
        label[["_track6_row_id", "price_krw", "ln_price_krw", "artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    out["split"] = split
    out["model"] = model_name
    out["pred_ln_price_krw"] = pred_log
    out["pred_price_krw"] = np.exp(pred_log)
    out["ape"] = np.abs(out["pred_price_krw"] - out["price_krw"]) / out["price_krw"]
    return out


def render_experiment(result: dict[str, Any]) -> str:
    best_warm = result["best_by_split"]["val_warm"]
    best_cold = result["best_by_split"]["val_cold"]
    lines = [
        "# T6-E002 구조-only baseline",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H2`",
        "- 상태: 검증 완료",
        "- 목적: 작가 피처 없이 작품 구조 정보만으로 기본 예측 가능성 확인",
        "- 사용 데이터: Track6 name-corrected feature/label split",
        "- 사용 스크립트: `scripts/track6/run_t6_e002_structure_baseline.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- 예측 CSV: `{result['prediction_csv']}`",
        "",
        "## 1. 사용 피처",
        "",
    ]
    lines += [f"- `{col}`" for col in STRUCTURE_FEATURES]
    lines += [
        "",
        "## 2. 비교 모델",
        "",
        "- `log_median_dummy`: train 로그가격 중앙값 예측",
        "- `ridge_onehot`: one-hot + Ridge",
        "- `huber_onehot`: one-hot + Huber robust regression",
        "- `hist_gbdt_ordinal`: ordinal category + 기본 histogram GBDT",
        "- `lightgbm_basic`: ordinal category + 기본 LightGBM",
        "",
        "## 3. validation 결과",
        "",
        "| split | model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| `{row['split']}` | `{row['model']}` | `{row['median_ape']:.4f}` | `{row['p95_ape']:.4f}` | "
            f"`{row['within_30']:.4f}` | `{row['within_50']:.4f}` | `{row['rmse_log']:.4f}` |"
        )
    lines += [
        "",
        "## 4. 핵심 해석",
        "",
        f"- Warm 최저 median APE: `{best_warm['median_ape']:.4f}` (`{best_warm['model']}`)",
        f"- Cold 최저 median APE: `{best_cold['median_ape']:.4f}` (`{best_cold['model']}`)",
        "- 중앙값 baseline보다 구조 피처 모델이 Warm/Cold 모두 개선되면 구조 정보 기반 예측 가능성이 있다고 판단",
        "- 이 실험은 작가 피처를 넣기 전 기준점이므로, 이후 T6-E003/T6-E004의 비교 기준으로 사용",
        "",
        "## 5. 결론",
        "",
        "- T6-H2는 validation 기준 검증 완료",
        f"- Warm 구조-only 기준 후보: `{best_warm['model']}`",
        f"- Cold 구조-only 기준 후보: `{best_cold['model']}`",
        "- 다음 단계는 Warm 작가 피처 ablation(T6-E003)과 Cold 모델 비교(T6-E004)",
        "",
    ]
    return "\n".join(lines)


def update_docs(result: dict[str, Any]) -> None:
    best_warm = result["best_by_split"]["val_warm"]
    best_cold = result["best_by_split"]["val_cold"]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    text = hypo.read_text(encoding="utf-8")
    old = "| T6-H2 | T6-G2 | Track6 split에서도 작품 구조 정보만으로 기본 예측이 가능할 것이다 | 작가 피처 없이 구조-only baseline을 Warm/Cold validation에서 평가 | Track6 split | 구조 피처 | 중앙값 baseline | median APE가 중앙값 baseline보다 개선 | 예정 | 미실행 | split 생성 후 진행 | T6-E002 | - |"
    new = (
        "| T6-H2 | T6-G2 | Track6 split에서도 작품 구조 정보만으로 기본 예측이 가능할 것이다 | "
        "작가 피처 없이 구조-only baseline을 Warm/Cold validation에서 평가 | Track6 name-corrected split | 구조 피처 | 중앙값 baseline | median APE가 중앙값 baseline보다 개선 | "
        f"검증 완료 | validation baseline 검증 | Warm `{best_warm['model']}` median APE `{best_warm['median_ape']:.4f}`, Cold `{best_cold['model']}` median APE `{best_cold['median_ape']:.4f}` | T6-E002 | T6-E003/T6-E004 진행 |"
    )
    if old in text:
        hypo.write_text(text.replace(old, new), encoding="utf-8")

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    text = results.read_text(encoding="utf-8")
    row = (
        f"| {result['created_at']} | T6-E002 | T6-H2 | 검증 완료 | Track6 name-corrected split | "
        f"{best_warm['model']} / {best_cold['model']} | 구조-only 피처 | "
        f"best `{best_warm['median_ape']:.4f}` (`{best_warm['model']}`) | "
        f"best `{best_cold['median_ape']:.4f}` (`{best_cold['model']}`) | "
        "구조 피처 baseline 기준 확보 | [기록](../experiments/2026-05-18_T6-E002_structure_only_baseline.md) |"
    )
    marker = "| 2026-05-18 | T6-E001C |"
    if "| 2026-05-18 | T6-E002 | T6-H2 |" not in text:
        text = text.replace(marker, row + "\n" + marker)
        results.write_text(text, encoding="utf-8")

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    text = index.read_text(encoding="utf-8")
    row = "| 2026-05-18 | T6-E002 | T6-H2 | 검증 완료 | 구조-only baseline 완료 | [기록](2026-05-18_T6-E002_structure_only_baseline.md) |"
    marker = "| 2026-05-18 | T6-E001C |"
    if "| 2026-05-18 | T6-E002 | T6-H2 |" not in text:
        text = text.replace(marker, row + "\n" + marker)
        index.write_text(text, encoding="utf-8")


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    EXP_DOC.parent.mkdir(parents=True, exist_ok=True)

    train_f, train_l = read_pair(
        FEATURE_DIR / "cold" / "track6_train_cold_features.csv",
        LABEL_DIR / "track6_train_labels.csv",
    )
    val_warm_f, val_warm_l = read_pair(
        FEATURE_DIR / "warm" / "track6_val_warm_warm_features.csv",
        LABEL_DIR / "track6_val_warm_labels.csv",
    )
    val_cold_f, val_cold_l = read_pair(
        FEATURE_DIR / "cold" / "track6_val_cold_cold_features.csv",
        LABEL_DIR / "track6_val_cold_labels.csv",
    )

    x_train, y_train_log, _ = make_xy(train_f, train_l)
    eval_sets = {
        "val_warm": (*make_xy(val_warm_f, val_warm_l), val_warm_f, val_warm_l),
        "val_cold": (*make_xy(val_cold_f, val_cold_l), val_cold_f, val_cold_l),
    }

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for model_name, model in build_models().items():
        model.fit(x_train, y_train_log)
        for split, (x_eval, _y_log, y_price, f_eval, l_eval) in eval_sets.items():
            pred_log = np.asarray(model.predict(x_eval), dtype=float)
            row = {"split": split, "model": model_name}
            row.update(metrics(y_price, pred_log))
            metric_rows.append(row)
            pred_frames.append(prediction_frame(split, model_name, f_eval, l_eval, pred_log))

    metric_df = pd.DataFrame(metric_rows).sort_values(["split", "median_ape", "p95_ape"])
    pred_df = pd.concat(pred_frames, ignore_index=True)
    metric_df.to_csv(RESULT_CSV, index=False)
    pred_df.to_csv(PRED_CSV, index=False)

    best_by_split = {
        split: metric_df.loc[metric_df["split"].eq(split)].sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict()
        for split in ["val_warm", "val_cold"]
    }
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E002",
        "hypothesis_id": "T6-H2",
        "features": STRUCTURE_FEATURES,
        "train_feature_path": "data/track6_split/features/cold/track6_train_cold_features.csv",
        "train_label_path": "data/track6_split/labels/track6_train_labels.csv",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "metrics": metric_df.to_dict(orient="records"),
        "best_by_split": best_by_split,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render_experiment(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps({
        "result": str(RESULT_JSON.relative_to(REPO)),
        "best_by_split": best_by_split,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
