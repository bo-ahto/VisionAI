#!/usr/bin/env python3
"""Run T6-E004 Cold model comparison on Track6 validation split."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from xgboost import XGBRegressor


REPO = Path(__file__).resolve().parents[2]
FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E004_cold_model_compare.md"
RESULT_JSON = RESULT_DIR / "t6_e004_cold_model_compare.json"
RESULT_CSV = RESULT_DIR / "t6_e004_cold_model_compare_metrics.csv"
PRED_CSV = PRED_DIR / "t6_e004_cold_model_compare_predictions.csv"

FEATURES = [
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
NUMERIC = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
CATEGORICAL = ["has_depth", "is_3d_candidate", "medium_category", "support_category", "medium_support_bucket", "is_extreme_aspect_ratio"]


def read_pair(feature_path: Path, label_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.read_csv(feature_path), pd.read_csv(label_path)


def make_xy(feature: pd.DataFrame, label: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    merged = feature[["_track6_row_id", *FEATURES]].merge(
        label[["_track6_row_id", "ln_price_krw", "price_krw"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    x = merged[FEATURES].copy()
    for col in NUMERIC:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    for col in CATEGORICAL:
        x[col] = x[col].fillna("__MISSING__").astype(str)
    return x, merged["ln_price_krw"].astype(float), merged["price_krw"].astype(float)


def onehot_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
        ("cat", Pipeline([("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=10))]), CATEGORICAL),
    ])


def ordinal_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), NUMERIC),
        ("cat", Pipeline([("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))]), CATEGORICAL),
    ])


def cat_ready(x: pd.DataFrame) -> pd.DataFrame:
    out = x.copy()
    for col in NUMERIC:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in CATEGORICAL:
        out[col] = out[col].fillna("__MISSING__").astype(str)
    return out


def build_models() -> dict[str, Any]:
    return {
        "ridge_onehot": Pipeline([("prep", onehot_preprocessor()), ("model", Ridge(alpha=10.0))]),
        "huber_onehot": Pipeline([("prep", onehot_preprocessor()), ("model", HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=700))]),
        "hist_quantile_ordinal": Pipeline([
            ("prep", ordinal_preprocessor()),
            ("model", HistGradientBoostingRegressor(
                loss="quantile",
                quantile=0.5,
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
        "xgboost_basic": Pipeline([
            ("prep", ordinal_preprocessor()),
            ("model", XGBRegressor(
                objective="reg:squarederror",
                n_estimators=350,
                learning_rate=0.04,
                max_depth=5,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=1.0,
                random_state=20260518,
                n_jobs=2,
            )),
        ]),
    }


def build_catboost() -> CatBoostRegressor:
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


def prediction_frame(model_name: str, feature: pd.DataFrame, label: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = feature[["_track6_row_id"]].merge(
        label[["_track6_row_id", "price_krw", "ln_price_krw", "artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    out["split"] = "val_cold"
    out["model"] = model_name
    out["pred_ln_price_krw"] = pred_log
    out["pred_price_krw"] = np.exp(pred_log)
    out["ape"] = np.abs(out["pred_price_krw"] - out["price_krw"]) / out["price_krw"]
    return out


def render_experiment(result: dict[str, Any]) -> str:
    best = result["best_median"]
    best_p95 = result["best_p95"]
    lines = [
        "# T6-E004 Cold 모델 비교",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H4`",
        "- 상태: 검증 완료",
        "- 목적: Cold에서 robust 계열과 트리 계열 중 어떤 방식이 안정적인지 확인",
        "- 사용 데이터: Track6 name-corrected Cold feature/label split",
        "- 사용 스크립트: `scripts/track6/run_t6_e004_cold_model_compare.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- 예측 CSV: `{result['prediction_csv']}`",
        "",
        "## 1. 사용 피처",
        "",
    ]
    lines += [f"- `{col}`" for col in FEATURES]
    lines += [
        "",
        "## 2. validation 결과",
        "",
        "| model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| `{row['model']}` | `{row['median_ape']:.4f}` | `{row['p95_ape']:.4f}` | "
            f"`{row['within_30']:.4f}` | `{row['within_50']:.4f}` | `{row['rmse_log']:.4f}` |"
        )
    lines += [
        "",
        "## 3. 핵심 해석",
        "",
        f"- median APE 최저: `{best['median_ape']:.4f}` (`{best['model']}`)",
        f"- p95 APE 최저: `{best_p95['p95_ape']:.4f}` (`{best_p95['model']}`)",
        "- median 기준과 p95 기준이 다르면 대표 오차와 큰 오차 위험을 분리해서 판단",
        "- Cold는 작가 피처를 쓰지 않으므로 구조 피처 기반 일반화 성능이 핵심",
        "",
        "## 4. 결론",
        "",
        "- T6-H4는 validation 기준 검증 완료",
        f"- Cold 대표 오차 기준 후보는 `{best['model']}`",
        f"- Cold 큰 오차 위험 보조 기준 후보는 `{best_p95['model']}`",
        "- 다음 단계는 피처 조합 실험(T6-E005)",
        "",
    ]
    return "\n".join(lines)


def update_docs(result: dict[str, Any]) -> None:
    best = result["best_median"]
    best_p95 = result["best_p95"]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    text = hypo.read_text(encoding="utf-8")
    old = "| T6-H4 | T6-G4 | Cold에서는 robust 선형 계열이 복잡한 트리 모델보다 안정적일 것이다 | Quantile, Huber, Ridge, LightGBM, XGBoost, CatBoost 비교 | Track6 split | Cold 구조 피처 | 구조-only baseline | Cold median/p95 개선 | 예정 | 미실행 | split 생성 후 진행 | T6-E004 | - |"
    new = (
        "| T6-H4 | T6-G4 | Cold에서는 robust 선형 계열이 복잡한 트리 모델보다 안정적일 것이다 | "
        "Huber, Ridge, quantile tree, LightGBM, XGBoost, CatBoost 비교 | Track6 name-corrected split | Cold 구조 피처 | 구조-only baseline | Cold median/p95 개선 | "
        f"검증 완료 | Cold validation 모델 비교 | median best `{best['model']}` `{best['median_ape']:.4f}`, p95 best `{best_p95['model']}` `{best_p95['p95_ape']:.4f}` | T6-E004 | T6-E005 진행 |"
    )
    if old in text:
        hypo.write_text(text.replace(old, new), encoding="utf-8")

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    text = results.read_text(encoding="utf-8")
    row = (
        f"| {result['created_at']} | T6-E004 | T6-H4 | 검증 완료 | Track6 name-corrected split | "
        f"{best['model']} / {best_p95['model']} | Cold 구조 피처 | - | "
        f"median best `{best['median_ape']:.4f}` (`{best['model']}`), p95 best `{best_p95['p95_ape']:.4f}` (`{best_p95['model']}`) | "
        "Cold 모델 후보 기준 확보 | [기록](../experiments/2026-05-18_T6-E004_cold_model_compare.md) |"
    )
    marker = "| 2026-05-18 | T6-E003 |"
    if "| 2026-05-18 | T6-E004 | T6-H4 |" not in text:
        results.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    text = index.read_text(encoding="utf-8")
    row = "| 2026-05-18 | T6-E004 | T6-H4 | 검증 완료 | Cold 모델 비교 완료 | [기록](2026-05-18_T6-E004_cold_model_compare.md) |"
    marker = "| 2026-05-18 | T6-E003 |"
    if "| 2026-05-18 | T6-E004 | T6-H4 |" not in text:
        index.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    train_f, train_l = read_pair(FEATURE_DIR / "track6_train_cold_features.csv", LABEL_DIR / "track6_train_labels.csv")
    val_f, val_l = read_pair(FEATURE_DIR / "track6_val_cold_cold_features.csv", LABEL_DIR / "track6_val_cold_labels.csv")
    x_train, y_train, _ = make_xy(train_f, train_l)
    x_val, _y_val_log, y_val_price = make_xy(val_f, val_l)

    rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for model_name, model in build_models().items():
        model.fit(x_train, y_train)
        pred_log = np.asarray(model.predict(x_val), dtype=float)
        row = {"model": model_name}
        row.update(metrics(y_val_price, pred_log))
        rows.append(row)
        pred_frames.append(prediction_frame(model_name, val_f, val_l, pred_log))

    cat = build_catboost()
    x_train_cat = cat_ready(x_train)
    x_val_cat = cat_ready(x_val)
    cat.fit(x_train_cat, y_train, cat_features=[x_train_cat.columns.get_loc(c) for c in CATEGORICAL])
    pred_log = np.asarray(cat.predict(x_val_cat), dtype=float)
    row = {"model": "catboost_basic"}
    row.update(metrics(y_val_price, pred_log))
    rows.append(row)
    pred_frames.append(prediction_frame("catboost_basic", val_f, val_l, pred_log))

    metric_df = pd.DataFrame(rows).sort_values(["median_ape", "p95_ape"])
    pred_df = pd.concat(pred_frames, ignore_index=True)
    metric_df.to_csv(RESULT_CSV, index=False)
    pred_df.to_csv(PRED_CSV, index=False)

    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E004",
        "hypothesis_id": "T6-H4",
        "features": FEATURES,
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "metrics": metric_df.to_dict(orient="records"),
        "best_median": metric_df.sort_values(["median_ape", "p95_ape"]).iloc[0].to_dict(),
        "best_p95": metric_df.sort_values(["p95_ape", "median_ape"]).iloc[0].to_dict(),
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render_experiment(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps({"result": str(RESULT_JSON.relative_to(REPO)), "best_median": result["best_median"], "best_p95": result["best_p95"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
