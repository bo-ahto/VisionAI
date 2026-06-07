#!/usr/bin/env python3
"""Run T6-E007 final test confirmation for selected Track6 candidates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from run_t6_e005_feature_combo_ablation import (
    ARTIST_FEATURES,
    FEATURE_SETS,
    REPO,
    add_generated_features,
    cat_ready,
    cat_feature_indices,
    cold_catboost_model,
    cold_lightgbm_model,
    merge_xy,
    metrics,
    prediction_frame,
    read_pair,
    warm_model,
)


WARM_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E007_test_confirmation.md"
RESULT_JSON = RESULT_DIR / "t6_e007_test_confirmation.json"
RESULT_CSV = RESULT_DIR / "t6_e007_test_confirmation_metrics.csv"
PRED_CSV = PRED_DIR / "t6_e007_test_confirmation_predictions.csv"
SELECTION_JSON = RESULT_DIR / "t6_e006_validation_candidate_selection.json"

DEFAULT_SELECTED = {
    "warm": {
        "split": "test_warm",
        "model": "huber_warm_artist",
        "feature_set": "base_medium_size",
        "columns": FEATURE_SETS["base_medium_size"] + ARTIST_FEATURES,
        "validation_median_ape": np.nan,
        "validation_p95_ape": np.nan,
    },
    "cold_median": {
        "split": "test_cold",
        "model": "catboost_cold",
        "feature_set": "base",
        "columns": FEATURE_SETS["base"],
        "validation_median_ape": np.nan,
        "validation_p95_ape": np.nan,
    },
    "cold_tail": {
        "split": "test_cold",
        "model": "lightgbm_cold",
        "feature_set": "base_size_shape",
        "columns": FEATURE_SETS["base_size_shape"],
        "validation_median_ape": np.nan,
        "validation_p95_ape": np.nan,
    },
}


def selected_candidates() -> dict[str, dict[str, Any]]:
    selected = DEFAULT_SELECTED.copy()
    if not SELECTION_JSON.exists():
        return selected
    payload = json.loads(SELECTION_JSON.read_text(encoding="utf-8"))
    selected = {}
    for key, spec in payload["selected"].items():
        feature_set = spec["feature_set"]
        columns = FEATURE_SETS[feature_set] + ARTIST_FEATURES if key == "warm" else FEATURE_SETS[feature_set]
        selected[key] = {
            "split": "test_warm" if key == "warm" else "test_cold",
            "model": spec["model"],
            "feature_set": feature_set,
            "columns": columns,
            "validation_median_ape": float(spec["median_ape"]),
            "validation_p95_ape": float(spec["p95_ape"]),
        }
    return selected


def run_warm(
    selected: dict[str, dict[str, Any]],
    train_f: pd.DataFrame,
    train_l: pd.DataFrame,
    test_f: pd.DataFrame,
    test_l: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    spec = selected["warm"]
    columns = spec["columns"]
    x_train, y_train, _price_train, _merged_train = merge_xy(train_f, train_l, columns)
    x_test, _y_test, y_price, merged_test = merge_xy(test_f, test_l, columns)
    model = warm_model(columns)
    model.fit(x_train, y_train)
    pred_log = np.asarray(model.predict(x_test), dtype=float)
    row = {key: value for key, value in spec.items() if key != "columns"}
    row.update(metrics(y_price, pred_log))
    row["median_delta_vs_validation"] = row["median_ape"] - spec["validation_median_ape"]
    row["p95_delta_vs_validation"] = row["p95_ape"] - spec["validation_p95_ape"]
    pred = prediction_frame("test_warm", f"{spec['model']}__{spec['feature_set']}", merged_test, pred_log)
    return row, pred


def fit_predict_cold(model_name: str, columns: list[str], x_train: pd.DataFrame, y_train: pd.Series, x_test: pd.DataFrame) -> np.ndarray:
    if model_name == "catboost_cold":
        model = cold_catboost_model()
        x_train_cat = cat_ready(x_train, columns)
        x_test_cat = cat_ready(x_test, columns)
        model.fit(x_train_cat, y_train, cat_features=cat_feature_indices(columns))
        return np.asarray(model.predict(x_test_cat), dtype=float)
    if model_name == "lightgbm_cold":
        model = cold_lightgbm_model(columns)
        model.fit(x_train, y_train)
        return np.asarray(model.predict(x_test), dtype=float)
    raise ValueError(f"unsupported cold model: {model_name}")


def run_cold(
    selected: dict[str, dict[str, Any]],
    train_f: pd.DataFrame,
    train_l: pd.DataFrame,
    test_f: pd.DataFrame,
    test_l: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    seen: set[str] = set()
    for key in [k for k in selected if k.startswith("cold_")]:
        spec = selected[key]
        spec_id = f"{spec['model']}__{spec['feature_set']}"
        if spec_id in seen:
            continue
        seen.add(spec_id)
        columns = spec["columns"]
        x_train, y_train, _price_train, _merged_train = merge_xy(train_f, train_l, columns)
        x_test, _y_test, y_price, merged_test = merge_xy(test_f, test_l, columns)
        pred_log = fit_predict_cold(spec["model"], columns, x_train, y_train, x_test)
        row = {field: value for field, value in spec.items() if field != "columns"}
        row.update(metrics(y_price, pred_log))
        row["median_delta_vs_validation"] = row["median_ape"] - spec["validation_median_ape"]
        row["p95_delta_vs_validation"] = row["p95_ape"] - spec["validation_p95_ape"]
        rows.append(row)
        preds.append(prediction_frame("test_cold", f"{spec['model']}__{spec['feature_set']}", merged_test, pred_log))
    return rows, preds


def verdict(row: dict[str, Any]) -> str:
    median_delta = row["median_delta_vs_validation"]
    p95_delta = row["p95_delta_vs_validation"]
    if median_delta <= 0.05 and p95_delta <= 0.20:
        return "유지"
    if median_delta <= 0.10:
        return "주의 유지"
    return "보류"


def render(result: dict[str, Any]) -> str:
    lines = [
        "# T6-E007 test 최종 확인",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H6`",
        "- 상태: 검증 완료",
        "- 목적: validation에서 고정한 후보가 test에서도 같은 방향으로 유지되는지 확인",
        "- 사용 스크립트: `scripts/track6/run_t6_e007_test_confirmation.py`",
        f"- 결과 JSON: `{result['result_json']}`",
        f"- 예측 CSV: `{result['prediction_csv']}`",
        "",
        "## 1. test 적용 원칙",
        "",
        "- validation 결과를 보고 후보를 바꾸지 않음",
        "- T6-E006에서 고정한 후보만 test에 적용",
        "- 학습은 `track6_train_*_features.csv`와 `track6_train_labels.csv` 기준으로만 진행",
        "- test 정답 가격은 예측 후 평가 단계에서만 결합",
        "",
        "## 2. test 결과",
        "",
        "| 구분 | 모델 | 피처셋 | val median | test median | val p95 | test p95 | 판단 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in result["metrics"]:
        lines.append(
            f"| `{row['split']}` | `{row['model']}` | `{row['feature_set']}` | "
            f"`{row['validation_median_ape']:.4f}` | `{row['median_ape']:.4f}` | "
            f"`{row['validation_p95_ape']:.4f}` | `{row['p95_ape']:.4f}` | {verdict(row)} |"
        )
    lines += [
        "",
        "## 3. 해석",
        "",
        "- Warm 후보는 test에서 validation 대비 성능 변화를 확인해 최종 Warm 후보 유지 여부를 판단",
        "- Cold 대표 오차 후보와 큰 오차 후보는 목적이 다르므로 둘 중 하나만 절대 우위로 보지 않음",
        "- test에서 median은 좋지만 p95가 나쁘면 단일 가격 예측은 가능하더라도 신뢰도/가격 범위 정책이 필요",
        "",
        "## 4. 결론",
        "",
    ]
    for row in result["metrics"]:
        lines.append(f"- `{row['split']}` / `{row['model']}` / `{row['feature_set']}`: {verdict(row)}")
    lines += [
        "- 다음 단계는 신뢰도/가격 범위 정책 검증(T6-E008)",
        "",
    ]
    return "\n".join(lines)


def replace_row(path: Path, prefix: str, row: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = row
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    marker = "| 2026-05-18 | T6-E006 |"
    path.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def update_docs(result: dict[str, Any]) -> None:
    warm = next(row for row in result["metrics"] if row["split"] == "test_warm")
    cold_rows = [row for row in result["metrics"] if row["split"] == "test_cold"]
    cold_best = sorted(cold_rows, key=lambda row: (row["median_ape"], row["p95_ape"]))[0]
    cold_tail = sorted(cold_rows, key=lambda row: (row["p95_ape"], row["median_ape"]))[0]

    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    row = (
        "| T6-H6 | T6-G6 | 최종 후보는 validation뿐 아니라 test에서도 같은 방향의 성능을 보여야 한다 | "
        "validation에서 고른 후보만 test에 적용 | Track6 name-corrected split | 최종 후보 피처 | validation 성능 | test 성능 급락 없음 | "
        f"검증 완료 | test holdout 확인 | Warm test `{warm['median_ape']:.4f}` ({verdict(warm)}), "
        f"Cold best test `{cold_best['median_ape']:.4f}` ({verdict(cold_best)}), Cold tail p95 `{cold_tail['p95_ape']:.4f}` ({verdict(cold_tail)}) | T6-E006, T6-E007 | T6-E008 신뢰도 정책 진행 |"
    )
    replace_row(hypo, "| T6-H6 |", row)

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    row = (
        f"| {result['created_at']} | T6-E007 | T6-H6 | 검증 완료 | Track6 name-corrected split | "
        "Huber / CatBoost / LightGBM | T6-E006 선정 후보 | "
        f"test `{warm['median_ape']:.4f}` (`{warm['feature_set']}`) | "
        f"median test `{cold_best['median_ape']:.4f}`, p95 test `{cold_tail['p95_ape']:.4f}` | "
        "test holdout 확인 완료 | [기록](../experiments/2026-05-18_T6-E007_test_confirmation.md) |"
    )
    replace_row(results, "| 2026-05-18 | T6-E007 |", row)

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    row = "| 2026-05-18 | T6-E007 | T6-H6 | 검증 완료 | test 최종 확인 완료 | [기록](2026-05-18_T6-E007_test_confirmation.md) |"
    replace_row(index, "| 2026-05-18 | T6-E007 |", row)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)

    warm_train_f, warm_train_l = read_pair(WARM_FEATURE_DIR / "track6_train_warm_features.csv", LABEL_DIR / "track6_train_labels.csv")
    warm_test_f, warm_test_l = read_pair(WARM_FEATURE_DIR / "track6_test_warm_warm_features.csv", LABEL_DIR / "track6_test_warm_labels.csv")
    cold_train_f, cold_train_l = read_pair(COLD_FEATURE_DIR / "track6_train_cold_features.csv", LABEL_DIR / "track6_train_labels.csv")
    cold_test_f, cold_test_l = read_pair(COLD_FEATURE_DIR / "track6_test_cold_cold_features.csv", LABEL_DIR / "track6_test_cold_labels.csv")

    warm_train_f, warm_test_f = add_generated_features(warm_train_f, warm_test_f)
    cold_train_f, cold_test_f = add_generated_features(cold_train_f, cold_test_f)

    selected = selected_candidates()
    warm_row, warm_pred = run_warm(selected, warm_train_f, warm_train_l, warm_test_f, warm_test_l)
    cold_rows, cold_preds = run_cold(selected, cold_train_f, cold_train_l, cold_test_f, cold_test_l)
    rows = [warm_row, *cold_rows]
    preds = [warm_pred, *cold_preds]

    metric_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True)
    metric_df.to_csv(RESULT_CSV, index=False)
    pred_df.to_csv(PRED_CSV, index=False)

    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E007",
        "hypothesis_id": "T6-H6",
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "selected": {key: {k: v for k, v in spec.items() if k != "columns"} for key, spec in selected.items()},
        "metrics": metric_df.to_dict(orient="records"),
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps(result["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
