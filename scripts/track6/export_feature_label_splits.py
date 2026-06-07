#!/usr/bin/env python3
"""Export Track6 split files into separate feature and label files.

The goal is to reduce price leakage:
- feature files must not contain target/price/sale/currency columns
- label files contain prices and slice metadata for evaluation only
- model prediction scripts should read feature files; evaluation scripts read labels
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SPLIT_DIR = REPO / "data" / "track6_split"
FEATURE_DIR = SPLIT_DIR / "features"
LABEL_DIR = SPLIT_DIR / "labels"
WARM_FEATURE_DIR = FEATURE_DIR / "warm"
COLD_FEATURE_DIR = FEATURE_DIR / "cold"
OUT_MANIFEST = REPO / "data" / "track6" / "manifests" / "track6_feature_label_manifest.json"
OUT_REPORT = REPO / "docs" / "track6" / "dataset" / "feature_label_pipeline_report.md"

SPLITS = ["train", "val_warm", "test_warm", "val_cold", "test_cold"]
TASK_SPLITS = {
    "warm": ["train", "val_warm", "test_warm"],
    "cold": ["train", "val_cold", "test_cold"],
}
TARGET_COLUMNS = ["price_krw", "ln_price_krw"]
LABEL_META_COLUMNS = [
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "artist_name_ko_orig",
    "medium_category",
    "support_category",
    "has_depth",
    "is_3d_candidate",
    "is_high_price_candidate",
    "is_extreme_aspect_ratio",
]
TRACKING_ONLY_COLUMNS = [
    "track4_source",
    "track4_source_row_index",
    "source_artwork_id",
    "artwork_url",
    "image_url",
    "cleaning_exclude_reasons",
]
MODEL_EXCLUDE_COLUMNS = [
    "artist_name_ko",
    "artist_name_ko_orig",
    "artist_name_standardized",
    "is_homonym",
    "artist_entity_suffix",
    "title_raw",
]
MODEL_EXCLUDE_PREFIXES = [
    "artist_meta_",
    "nant_",
]
MODEL_EXCLUDE_EXTRA_COLUMNS = [
    "collected_material_raw",
]
COLD_FORBIDDEN_COLUMNS = [
    "artist_key",
    "artist_works_log",
    "artist_works_count_train",
]
PRICE_LEAK_ALLOWLIST = {"estimated_ho"}
PRICE_LEAK_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"price",
        r"krw",
        r"\busd\b",
        r"currency",
        r"amount",
        r"sold",
        r"sale",
        r"for_sale",
        r"cost",
        r"fee",
    ]
]


def is_price_like(column: str) -> bool:
    if column in PRICE_LEAK_ALLOWLIST:
        return False
    return any(pattern.search(column) for pattern in PRICE_LEAK_PATTERNS)


def base_removed_columns(df: pd.DataFrame) -> list[str]:
    return sorted(
        {
            col
            for col in df.columns
            if col in TARGET_COLUMNS
            or col in TRACKING_ONLY_COLUMNS
            or col in MODEL_EXCLUDE_COLUMNS
            or col in MODEL_EXCLUDE_EXTRA_COLUMNS
            or any(col.startswith(prefix) for prefix in MODEL_EXCLUDE_PREFIXES)
            or is_price_like(col)
        }
    )


def split_features_labels(df: pd.DataFrame, task: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    label_cols = [col for col in LABEL_META_COLUMNS + TARGET_COLUMNS if col in df.columns]
    label_cols = list(dict.fromkeys(label_cols))
    removed_cols = set(base_removed_columns(df))
    if task == "cold":
        removed_cols.update(col for col in COLD_FORBIDDEN_COLUMNS if col in df.columns)
    removed_cols = sorted(removed_cols)
    feature = df.drop(columns=removed_cols, errors="ignore").copy()
    label = df[label_cols].copy()
    return feature, label, removed_cols


def validate_feature_file(feature: pd.DataFrame, task: str) -> list[str]:
    leaks = [col for col in feature.columns if is_price_like(col) or col in TARGET_COLUMNS]
    leaks += [col for col in TRACKING_ONLY_COLUMNS if col in feature.columns]
    leaks += [col for col in MODEL_EXCLUDE_COLUMNS if col in feature.columns]
    leaks += [col for col in MODEL_EXCLUDE_EXTRA_COLUMNS if col in feature.columns]
    leaks += [
        col
        for col in feature.columns
        if any(col.startswith(prefix) for prefix in MODEL_EXCLUDE_PREFIXES)
    ]
    if task == "cold":
        leaks += [col for col in COLD_FORBIDDEN_COLUMNS if col in feature.columns]
    return sorted(set(leaks))


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Track 6 feature/label 분리 파이프라인 보고서",
        "",
        f"- 생성일: `{manifest['created_at']}`",
        f"- 상태: `{manifest['status']}`",
        "- 목적: 모델 입력 파일에서 가격/정답/출처성 컬럼을 물리적으로 분리해 누수 가능성을 줄임",
        "",
        "## 1. 사용 원칙",
        "",
        "- 학습/예측 코드는 `features` 파일만 읽음",
        "- 평가 코드는 `labels` 파일을 별도로 읽어 예측값과 결합함",
        "- validation labels는 모델/피처 선택에만 사용함",
        "- test labels는 최종 후보 확정 후 최종 평가에만 사용함",
        "",
        "## 2. 제거 기준",
        "",
        "- feature 파일에서 제거하는 컬럼",
        "  - `price`, `krw`, `usd`, `currency`, `amount`, `sold`, `sale`, `cost`, `fee` 패턴 포함 컬럼",
        "  - `track4_source`, `source_artwork_id`, URL, image URL 등 출처/추적 컬럼",
        "  - target 컬럼 `price_krw`, `ln_price_krw`",
        "- 예외",
        "  - `estimated_ho`는 가격이 아니라 작품 크기 호수 추정값이므로 제거하지 않음",
        "",
        "## 3. 산출물",
        "",
        "| task | split | feature rows | feature cols | label rows | label cols | 제거 컬럼 | 누수 의심 컬럼 |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for task, task_items in manifest["tasks"].items():
        for name, item in task_items.items():
            removed = ", ".join(f"`{col}`" for col in item["removed_columns"]) or "-"
            leaks = ", ".join(f"`{col}`" for col in item["feature_leak_columns"]) or "-"
            lines.append(
                f"| `{task}` | `{name}` | `{item['feature_rows']:,}` | `{item['feature_columns']}` | "
                f"`{item['label_rows']:,}` | `{item['label_columns']}` | {removed} | {leaks} |"
            )
    lines += [
        "",
        "## 4. 해석",
        "",
        "- feature 파일의 누수 의심 컬럼이 0개이면 모델 실험은 feature 파일 기준으로 진행 가능",
        "- Warm 모델은 `features/warm` 파일만 읽음",
        "- Cold 모델은 작가 식별/작가 이력 컬럼이 제거된 `features/cold` 파일만 읽음",
        "- full split 파일은 감사/재생성용으로 보존하되 모델 코드에서 직접 읽지 않음",
        "- labels 파일은 평가 스크립트에서만 사용함",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    for stale in FEATURE_DIR.glob("track6_*_features.csv"):
        stale.unlink()
    WARM_FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    COLD_FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    for stale in WARM_FEATURE_DIR.glob("track6_*_features.csv"):
        stale.unlink()
    for stale in COLD_FEATURE_DIR.glob("track6_*_features.csv"):
        stale.unlink()
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "created_at": date.today().isoformat(),
        "status": "pass",
        "warm_feature_dir": str(WARM_FEATURE_DIR.relative_to(REPO)),
        "cold_feature_dir": str(COLD_FEATURE_DIR.relative_to(REPO)),
        "label_dir": str(LABEL_DIR.relative_to(REPO)),
        "target_columns": TARGET_COLUMNS,
        "tracking_only_columns": TRACKING_ONLY_COLUMNS,
        "model_exclude_columns": MODEL_EXCLUDE_COLUMNS,
        "cold_forbidden_columns": COLD_FORBIDDEN_COLUMNS,
        "price_leak_allowlist": sorted(PRICE_LEAK_ALLOWLIST),
        "tasks": {"warm": {}, "cold": {}},
    }

    loaded: dict[str, pd.DataFrame] = {}
    for split in SPLITS:
        full_path = SPLIT_DIR / f"track6_{split}.csv"
        df = pd.read_csv(full_path, low_memory=False)
        loaded[split] = df
        label_cols = [col for col in LABEL_META_COLUMNS + TARGET_COLUMNS if col in df.columns]
        label = df[list(dict.fromkeys(label_cols))].copy()
        label_path = LABEL_DIR / f"track6_{split}_labels.csv"
        label.to_csv(label_path, index=False)

    for task, out_dir in [("warm", WARM_FEATURE_DIR), ("cold", COLD_FEATURE_DIR)]:
        for split in TASK_SPLITS[task]:
            df = loaded[split]
            full_path = SPLIT_DIR / f"track6_{split}.csv"
            label_path = LABEL_DIR / f"track6_{split}_labels.csv"
            label_cols = [col for col in LABEL_META_COLUMNS + TARGET_COLUMNS if col in df.columns]
            feature, _, removed_cols = split_features_labels(df, task)
            leaks = validate_feature_file(feature, task)
            feature_path = out_dir / f"track6_{split}_{task}_features.csv"
            feature.to_csv(feature_path, index=False)
            if leaks:
                manifest["status"] = "fail"
            manifest["tasks"][task][split] = {
                "full_path": str(full_path.relative_to(REPO)),
                "feature_path": str(feature_path.relative_to(REPO)),
                "label_path": str(label_path.relative_to(REPO)),
                "feature_rows": int(len(feature)),
                "feature_columns": int(len(feature.columns)),
                "label_rows": int(len(df)),
                "label_columns": int(len(list(dict.fromkeys(label_cols)))),
                "removed_columns": removed_cols,
                "feature_leak_columns": leaks,
            }

    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_REPORT.write_text(render_report(manifest), encoding="utf-8")
    print(OUT_MANIFEST)
    print(OUT_REPORT)
    print(json.dumps({"status": manifest["status"], "tasks": manifest["tasks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
