#!/usr/bin/env python3
"""Build Track6 final candidate artifacts and manifest."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from run_t6_e005_feature_combo_ablation import (
    ARTIST_FEATURES,
    FEATURE_SETS,
    REPO,
    add_generated_features,
    cat_feature_indices,
    cold_median_model,
    cold_tail_model,
    merge_xy,
    read_pair,
    warm_model,
)


WARM_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
ARTIFACT_DIR = REPO / "data" / "track6" / "artifacts"
RESULT_DIR = REPO / "data" / "track6" / "results"
EXP_DOC = REPO / "docs" / "track6" / "experiments" / "2026-05-18_T6-E009_final_artifact_manifest.md"
RESULT_JSON = RESULT_DIR / "t6_e009_final_artifact_manifest.json"
MANIFEST_JSON = ARTIFACT_DIR / "track6_artifact_manifest.json"
WARM_MODEL = ARTIFACT_DIR / "track6_warm_catboost_base_medium_size.cbm"
COLD_MEDIAN_MODEL = ARTIFACT_DIR / "track6_cold_hist_quantile_base.joblib"
COLD_TAIL_MODEL = ARTIFACT_DIR / "track6_cold_huber_base_size_shape.joblib"


def combine_features(path_a: Path, path_b: Path) -> pd.DataFrame:
    return pd.concat([pd.read_csv(path_a), pd.read_csv(path_b)], ignore_index=True, sort=False)


def combine_labels(path_a: Path, path_b: Path) -> pd.DataFrame:
    return pd.concat([pd.read_csv(path_a), pd.read_csv(path_b)], ignore_index=True, sort=False)


def fit_warm(feature: pd.DataFrame, label: pd.DataFrame) -> dict[str, Any]:
    columns = FEATURE_SETS["base_medium_size"] + ARTIST_FEATURES
    x_train, y_train, _price, _merged = merge_xy(feature, label, columns)
    model = warm_model()
    model.fit(x_train, y_train, cat_features=cat_feature_indices(columns))
    model.save_model(WARM_MODEL)
    return {
        "artifact": str(WARM_MODEL.relative_to(REPO)),
        "model": "CatBoostRegressor",
        "feature_set": "base_medium_size",
        "features": columns,
        "training_rows": int(len(x_train)),
    }


def fit_cold_median(feature: pd.DataFrame, label: pd.DataFrame) -> dict[str, Any]:
    columns = FEATURE_SETS["base"]
    x_train, y_train, _price, _merged = merge_xy(feature, label, columns)
    model = cold_median_model(columns)
    model.fit(x_train, y_train)
    joblib.dump(model, COLD_MEDIAN_MODEL)
    return {
        "artifact": str(COLD_MEDIAN_MODEL.relative_to(REPO)),
        "model": "HistGradientBoostingRegressor(loss=quantile)",
        "feature_set": "base",
        "features": columns,
        "training_rows": int(len(x_train)),
    }


def fit_cold_tail(feature: pd.DataFrame, label: pd.DataFrame) -> dict[str, Any]:
    columns = FEATURE_SETS["base_size_shape"]
    x_train, y_train, _price, _merged = merge_xy(feature, label, columns)
    model = cold_tail_model(columns)
    model.fit(x_train, y_train)
    joblib.dump(model, COLD_TAIL_MODEL)
    return {
        "artifact": str(COLD_TAIL_MODEL.relative_to(REPO)),
        "model": "HuberRegressor",
        "feature_set": "base_size_shape",
        "features": columns,
        "training_rows": int(len(x_train)),
    }


def feature_generation_summary(feature: pd.DataFrame) -> dict[str, Any]:
    log_area = pd.to_numeric(feature["log_area"], errors="coerce").dropna()
    area = pd.to_numeric(feature["area_cm2"], errors="coerce").dropna()
    return {
        "size_bucket_source": "train+validation log_area quantiles",
        "log_area_quantiles": [float(x) for x in np.quantile(log_area, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])],
        "large_area_cutoff_q80": float(np.quantile(area, 0.80)),
        "generated_features": [
            "size_bucket",
            "shape_bucket",
            "medium_size_bucket",
            "support_size_bucket",
            "medium_shape_bucket",
            "is_large_2d",
            "is_large_3d",
        ],
    }


def render(result: dict[str, Any]) -> str:
    lines = [
        "# T6-E009 최종 artifact manifest",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 관련 가설: `T6-H8`",
        "- 상태: 검증 완료",
        "- 목적: Track6 최종 후보 모델, 피처, 재현 파일을 manifest로 고정",
        "- 사용 스크립트: `scripts/track6/run_t6_e009_build_final_artifacts.py`",
        f"- manifest: `{result['manifest_json']}`",
        "",
        "## 1. 생성 원칙",
        "",
        "- test 데이터는 artifact 학습에 사용하지 않음",
        "- artifact 학습에는 `train + validation`만 사용",
        "- Warm/Cold 모델은 분리 관리",
        "- Cold는 대표 오차용 후보와 큰 오차 관찰용 후보를 함께 남김",
        "- 운영 입력에서 만들 수 없는 피처는 사용하지 않음",
        "",
        "## 2. artifact 목록",
        "",
        "| 구분 | 모델 | 피처셋 | 학습 row | 파일 |",
        "|---|---|---|---:|---|",
    ]
    for item in result["artifacts"]:
        lines.append(
            f"| `{item['key']}` | `{item['model']}` | `{item['feature_set']}` | `{item['training_rows']}` | `{item['artifact']}` |"
        )
    lines += [
        "",
        "## 3. 운영 라우팅",
        "",
        "- 입력 작가가 학습 artist_key/한글명 기준으로 확인되면 Warm 후보 사용",
        "- 처음 보는 작가이면 Cold 후보 사용",
        "- Cold 3D, 극단 형태, 비균형 형태는 신뢰도 경고 후보로 표시",
        "- Warm 저이력 작가는 신뢰도 경고 후보로 표시",
        "",
        "## 4. 결론",
        "",
        "- T6-H8은 검증 완료",
        "- Track6 기준 최종 후보 artifact와 manifest를 생성함",
        "- 다음 작업은 서비스 입력 스키마와 추론 스크립트 연결",
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
    marker = "| 2026-05-18 | T6-E008 |"
    path.write_text(text.replace(marker, row + "\n" + marker), encoding="utf-8")


def update_docs(result: dict[str, Any]) -> None:
    hypo = REPO / "docs" / "track6" / "tables" / "hypothesis_table.md"
    row = (
        "| T6-H8 | T6-G8 | 최종 운영 후보는 성능, 운영 가능성, 설명 가능성, 재현 가능성을 모두 만족해야 한다 | "
        "최종 모델, 피처, 전처리, manifest 생성 | Track6 artifacts | artifact manifest | 파일 누락 없음 | manifest ready | "
        f"검증 완료 | artifact manifest 생성 | Warm/Cold artifact `{len(result['artifacts'])}`개 생성, manifest ready | T6-E009 | 서비스 추론 스크립트 연결 |"
    )
    replace_row(hypo, "| T6-H8 |", row)

    results = REPO / "docs" / "track6" / "tables" / "experiment_results_table.md"
    row = (
        f"| {result['created_at']} | T6-E009 | T6-H8 | 검증 완료 | Track6 train+validation | "
        "CatBoost / HistQuantile / Huber | 최종 후보 피처 | artifact 생성 | artifact 생성 | "
        "최종 후보 manifest ready | [기록](../experiments/2026-05-18_T6-E009_final_artifact_manifest.md) |"
    )
    replace_row(results, "| 2026-05-18 | T6-E009 |", row)

    index = REPO / "docs" / "track6" / "experiments" / "INDEX.md"
    row = "| 2026-05-18 | T6-E009 | T6-H8 | 검증 완료 | 최종 artifact manifest 생성 | [기록](2026-05-18_T6-E009_final_artifact_manifest.md) |"
    replace_row(index, "| 2026-05-18 | T6-E009 |", row)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    warm_feature = combine_features(
        WARM_FEATURE_DIR / "track6_train_warm_features.csv",
        WARM_FEATURE_DIR / "track6_val_warm_warm_features.csv",
    )
    warm_label = combine_labels(LABEL_DIR / "track6_train_labels.csv", LABEL_DIR / "track6_val_warm_labels.csv")
    cold_feature = combine_features(
        COLD_FEATURE_DIR / "track6_train_cold_features.csv",
        COLD_FEATURE_DIR / "track6_val_cold_cold_features.csv",
    )
    cold_label = combine_labels(LABEL_DIR / "track6_train_labels.csv", LABEL_DIR / "track6_val_cold_labels.csv")
    warm_feature, _warm_unused = add_generated_features(warm_feature, warm_feature)
    cold_feature, _cold_unused = add_generated_features(cold_feature, cold_feature)

    artifacts = [
        {"key": "warm_price_model", **fit_warm(warm_feature, warm_label)},
        {"key": "cold_median_price_model", **fit_cold_median(cold_feature, cold_label)},
        {"key": "cold_tail_reference_model", **fit_cold_tail(cold_feature, cold_label)},
    ]
    manifest = {
        "created_at": date.today().isoformat(),
        "track": "track6",
        "training_policy": "train + validation only, test excluded",
        "target": "ln_price_krw",
        "price_label": "price_krw",
        "routing_policy": {
            "warm": "artist exists in training artist identity table",
            "cold": "artist not found in training artist identity table",
        },
        "risk_policy_candidates": [
            "cold_3d",
            "cold_extreme_shape",
            "cold_unbalanced_shape",
            "warm_low_artist_history",
        ],
        "feature_generation": {
            "warm": feature_generation_summary(warm_feature),
            "cold": feature_generation_summary(cold_feature),
        },
        "artifacts": artifacts,
        "source_experiments": ["T6-E001", "T6-E002", "T6-E003", "T6-E004", "T6-E005", "T6-E006", "T6-E007", "T6-E008"],
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-E009",
        "hypothesis_id": "T6-H8",
        "manifest_json": str(MANIFEST_JSON.relative_to(REPO)),
        "result_json": str(RESULT_JSON.relative_to(REPO)),
        "artifacts": artifacts,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render(result), encoding="utf-8")
    update_docs(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
