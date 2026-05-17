#!/usr/bin/env python3
"""Validate Track 4 model feature sets against forbidden feature manifest."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO / "configs" / "track4" / "feature_manifest.json"
SPLIT_DIR = REPO / "data" / "track4_split"
RESULT_DIR = REPO / "data" / "track4" / "results"
RESULT_PATH = RESULT_DIR / "t4_e034_feature_manifest_check.json"
REQUIRED_SPLITS = [
    "track4_train.csv",
    "track4_val_warm.csv",
    "track4_val_cold.csv",
    "track4_test_warm.csv",
    "track4_test_cold.csv",
]


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def split_columns() -> dict[str, list[str]]:
    columns: dict[str, list[str]] = {}
    for file_name in REQUIRED_SPLITS:
        path = SPLIT_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(path)
        columns[file_name] = list(pd.read_csv(path, nrows=0).columns)
    return columns


def reasons_for_feature(feature: str, manifest: dict[str, Any], allow_conditional: bool = False) -> list[str]:
    if allow_conditional and feature in set(manifest.get("conditional_allow_exact", [])):
        return []
    reasons: list[str] = []
    forbidden_exact = set(manifest.get("forbidden_exact", []))
    if feature in forbidden_exact:
        reasons.append("forbidden_exact")
    lower = feature.lower()
    for pattern in manifest.get("forbidden_patterns", []):
        if pattern.lower() in lower:
            reasons.append(f"forbidden_pattern:{pattern}")
    return reasons


def validate_feature_set(
    name: str,
    features: list[str],
    manifest: dict[str, Any],
    available_columns: set[str],
    allow_conditional: bool = False,
) -> dict[str, Any]:
    missing = sorted(feature for feature in features if feature not in available_columns)
    violations = {
        feature: reasons_for_feature(feature, manifest, allow_conditional=allow_conditional)
        for feature in features
        if reasons_for_feature(feature, manifest, allow_conditional=allow_conditional)
    }
    return {
        "feature_set": name,
        "features": features,
        "conditional_allow_enabled": allow_conditional,
        "missing_columns": missing,
        "violations": violations,
        "passed": not missing and not violations,
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    columns_by_split = split_columns()
    common_columns = set.intersection(*(set(cols) for cols in columns_by_split.values()))
    generated_columns = set(manifest.get("generated_operational_columns", []))
    available_model_columns = common_columns | generated_columns

    model_checks = [
        validate_feature_set(name, features, manifest, available_model_columns, allow_conditional=True)
        for name, features in manifest.get("model_feature_sets", {}).items()
    ]
    negative_checks = [
        validate_feature_set(name, features, manifest, available_model_columns, allow_conditional=False)
        for name, features in manifest.get("negative_control_feature_sets", {}).items()
    ]
    target_presence = {
        split_name: sorted(set(manifest.get("target_columns", [])) & set(cols))
        for split_name, cols in columns_by_split.items()
    }
    trace_presence = {
        split_name: sorted(set(manifest.get("trace_only_columns", [])) & set(cols))
        for split_name, cols in columns_by_split.items()
    }
    result = {
        "experiment_id": "T4-E034",
        "hypothesis_id": "T4-H25",
        "date": date.today().isoformat(),
        "manifest": str(MANIFEST_PATH.relative_to(REPO)),
        "split_files": REQUIRED_SPLITS,
        "generated_operational_columns": sorted(generated_columns),
        "conditional_allow_exact": sorted(manifest.get("conditional_allow_exact", [])),
        "model_feature_checks": model_checks,
        "negative_control_checks": negative_checks,
        "target_columns_present_for_training_label": target_presence,
        "trace_columns_present_for_audit_only": trace_presence,
        "all_model_feature_sets_passed": all(check["passed"] for check in model_checks),
        "negative_controls_detected": all(not check["passed"] and check["violations"] for check in negative_checks),
    }
    result["passed"] = result["all_model_feature_sets_passed"] and result["negative_controls_detected"]
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(RESULT_PATH)
    print(json.dumps({"passed": result["passed"], "model_checks": len(model_checks), "negative_controls": len(negative_checks)}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
