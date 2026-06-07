#!/usr/bin/env python3
"""Validate residual calibration for Track6 selected Warm/Cold candidates."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from run_t6_e005_feature_combo_ablation import REPO, add_generated_features


WARM_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
RESULT_DIR = REPO / "data" / "track6" / "results"
PRED_DIR = REPO / "data" / "track6" / "predictions"
DOC_DIR = REPO / "docs" / "track6" / "experiments"

VAL_PRED_CSV = PRED_DIR / "t6_e005_feature_combo_ablation_predictions.csv"
TEST_PRED_CSV = PRED_DIR / "t6_e007_test_confirmation_predictions.csv"
SELECTION_JSON = RESULT_DIR / "t6_e006_validation_candidate_selection.json"
RESULT_JSON = RESULT_DIR / "t6_pp_residual_calibration.json"
RESULT_CSV = RESULT_DIR / "t6_pp_residual_calibration_metrics.csv"
RULE_CSV = RESULT_DIR / "t6_pp_residual_calibration_rules.csv"
PRED_CSV = PRED_DIR / "t6_pp_residual_calibration_predictions.csv"
EXP_DOC = DOC_DIR / "2026-05-29_T6-PP_residual_calibration.md"

MIN_GROUP_N = 50


def selected_prediction_names() -> dict[str, str]:
    payload = json.loads(SELECTION_JSON.read_text(encoding="utf-8"))
    selected = payload["selected"]
    names: dict[str, str] = {}
    seen: set[str] = set()
    for key, spec in selected.items():
        model_name = f"{spec['model']}__{spec['feature_set']}"
        if model_name in seen:
            continue
        seen.add(model_name)
        names[key] = model_name
    return names


def load_features(split: str) -> pd.DataFrame:
    if split == "val_warm":
        train = pd.read_csv(WARM_FEATURE_DIR / "track6_train_warm_features.csv")
        target = pd.read_csv(WARM_FEATURE_DIR / "track6_val_warm_warm_features.csv")
    elif split == "test_warm":
        train = pd.read_csv(WARM_FEATURE_DIR / "track6_train_warm_features.csv")
        target = pd.read_csv(WARM_FEATURE_DIR / "track6_test_warm_warm_features.csv")
    elif split == "val_cold":
        train = pd.read_csv(COLD_FEATURE_DIR / "track6_train_cold_features.csv")
        target = pd.read_csv(COLD_FEATURE_DIR / "track6_val_cold_cold_features.csv")
    elif split == "test_cold":
        train = pd.read_csv(COLD_FEATURE_DIR / "track6_train_cold_features.csv")
        target = pd.read_csv(COLD_FEATURE_DIR / "track6_test_cold_cold_features.csv")
    else:
        raise ValueError(f"unknown split: {split}")
    _train, target = add_generated_features(train, target)
    target["split"] = split
    return target


def enrich(pred: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for split in sorted(pred["split"].unique()):
        features = load_features(split)
        keep = [
            "_track6_row_id",
            "split",
            "size_bucket",
            "shape_bucket",
            "medium_category",
            "support_category",
            "medium_support_bucket",
            "artist_works_count_train",
            "artist_meta_total_works",
            "artist_meta_for_sale_works",
            "artist_meta_followers",
        ]
        keep = [col for col in keep if col in features.columns]
        part = pred.loc[pred["split"].eq(split)].merge(
            features[keep],
            on=["_track6_row_id", "split"],
            how="left",
            validate="many_to_one",
        )
        frames.append(part)
    out = pd.concat(frames, ignore_index=True)
    out["pred_log"] = np.log(out["pred_price_krw"].clip(lower=1_000.0))
    out["actual_log"] = np.log(out["price_krw"].clip(lower=1_000.0))
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def metric_row(scope: str, model: str, method: str, frame: pd.DataFrame, pred_log_col: str) -> dict[str, Any]:
    pred_price = np.exp(frame[pred_log_col].to_numpy(dtype=float))
    actual = frame["price_krw"].to_numpy(dtype=float)
    ape = np.abs(pred_price - actual) / actual
    return {
        "scope": scope,
        "model": model,
        "method": method,
        "n": int(len(frame)),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "RMSE_log": float(np.sqrt(np.mean((frame[pred_log_col].to_numpy(dtype=float) - frame["actual_log"].to_numpy(dtype=float)) ** 2))),
    }


def assign_pred_bin(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[float]]:
    edges = np.quantile(val["pred_log"], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)
    labels = [f"pred_q{i + 1}" for i in range(len(edges) - 1)]
    val = val.copy()
    test = test.copy()
    val["pred_bin"] = pd.cut(val["pred_log"], edges, labels=labels, include_lowest=True).astype(str)
    test["pred_bin"] = pd.cut(test["pred_log"], edges, labels=labels, include_lowest=True).astype(str)
    return val, test, [float(x) for x in edges]


def rule_table(val: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rules = (
        val.groupby(group_col, dropna=False)["residual_log"]
        .agg(["count", "median"])
        .reset_index()
        .rename(columns={group_col: "group_value", "count": "n", "median": "correction_log"})
    )
    rules["group_col"] = group_col
    rules.loc[rules["n"] < MIN_GROUP_N, "correction_log"] = 0.0
    return rules[["group_col", "group_value", "n", "correction_log"]]


def apply_rules(test: pd.DataFrame, rules: pd.DataFrame, group_col: str, output_col: str) -> pd.DataFrame:
    merged = test.merge(
        rules.loc[rules["group_col"].eq(group_col), ["group_value", "correction_log"]],
        left_on=group_col,
        right_on="group_value",
        how="left",
    )
    test = test.copy()
    test[output_col] = test["pred_log"] + merged["correction_log"].fillna(0.0).to_numpy(dtype=float)
    return test


def evaluate_candidate(scope: str, model_name: str, val: pd.DataFrame, test: pd.DataFrame) -> tuple[list[dict[str, Any]], list[pd.DataFrame], pd.DataFrame]:
    val, test, pred_bin_edges = assign_pred_bin(val, test)
    group_cols = ["pred_bin", "size_bucket", "medium_category", "support_category"]
    group_cols = [col for col in group_cols if col in val.columns and col in test.columns]

    rows = [metric_row(scope, model_name, "baseline", test, "pred_log")]
    rules = []
    pred_outputs = []

    overall_correction = float(val["residual_log"].median())
    overall = test.copy()
    overall["corrected_pred_log"] = overall["pred_log"] + overall_correction
    rows.append(metric_row(scope, model_name, "overall_median_residual", overall, "corrected_pred_log"))
    pred_outputs.append(overall.assign(calibration_method="overall_median_residual"))
    rules.append(pd.DataFrame([{
        "scope": scope,
        "model": model_name,
        "method": "overall_median_residual",
        "group_col": "__all__",
        "group_value": "__all__",
        "n": int(len(val)),
        "correction_log": overall_correction,
        "pred_bin_edges": json.dumps(pred_bin_edges),
    }]))

    for group_col in group_cols:
        group_rules = rule_table(val, group_col)
        corrected = apply_rules(test, group_rules, group_col, "corrected_pred_log")
        method = f"{group_col}_median_residual"
        rows.append(metric_row(scope, model_name, method, corrected, "corrected_pred_log"))
        pred_outputs.append(corrected.assign(calibration_method=method))
        group_rules = group_rules.assign(
            scope=scope,
            model=model_name,
            method=method,
            pred_bin_edges=json.dumps(pred_bin_edges),
        )
        rules.append(group_rules)

    return rows, pred_outputs, pd.concat(rules, ignore_index=True, sort=False)


def render(result: dict[str, Any]) -> str:
    lines = [
        "# T6-PP residual calibration",
        "",
        f"- 날짜: `{result['created_at']}`",
        "- 목적: Warm Huber / Cold CatBoost+LightGBM 후보의 validation residual 보정 효과 검증",
        "- 원칙: validation 예측에서만 보정값을 만들고 test에는 고정 적용",
        f"- 결과 CSV: `{result['result_csv']}`",
        f"- 보정 규칙 CSV: `{result['rule_csv']}`",
        "",
        "## Best Test Result",
        "",
        "| scope | model | best method | baseline MdAPE | best MdAPE | baseline p95 | best p95 | decision |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in result["summary"]:
        lines.append(
            f"| `{row['scope']}` | `{row['model']}` | `{row['best_method']}` | "
            f"`{row['baseline_MdAPE']:.4f}` | `{row['best_MdAPE']:.4f}` | "
            f"`{row['baseline_p95_APE']:.4f}` | `{row['best_p95_APE']:.4f}` | {row['decision']} |"
        )
    lines += [
        "",
        "## Decision Rule",
        "",
        "- 채택: MdAPE가 개선되고 p95_APE가 악화되지 않는 경우",
        "- 보류: MdAPE만 좋아지고 p95_APE가 악화되는 경우",
        "- 중단: baseline보다 MdAPE가 나빠지는 경우",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    names = selected_prediction_names()
    val_pred = enrich(pd.read_csv(VAL_PRED_CSV))
    test_pred = enrich(pd.read_csv(TEST_PRED_CSV))

    rows: list[dict[str, Any]] = []
    pred_outputs: list[pd.DataFrame] = []
    rules: list[pd.DataFrame] = []
    for scope, selected_model in names.items():
        val_split = "val_warm" if scope == "warm" else "val_cold"
        test_split = "test_warm" if scope == "warm" else "test_cold"
        val = val_pred.loc[val_pred["split"].eq(val_split) & val_pred["model"].eq(selected_model)].copy()
        test = test_pred.loc[test_pred["split"].eq(test_split) & test_pred["model"].eq(selected_model)].copy()
        if val.empty or test.empty:
            continue
        model_rows, model_preds, model_rules = evaluate_candidate(scope, selected_model, val, test)
        rows.extend(model_rows)
        pred_outputs.extend(model_preds)
        rules.append(model_rules)

    metrics = pd.DataFrame(rows)
    rules_df = pd.concat(rules, ignore_index=True, sort=False) if rules else pd.DataFrame()
    preds = pd.concat(pred_outputs, ignore_index=True, sort=False) if pred_outputs else pd.DataFrame()
    if not preds.empty:
        preds["corrected_pred_price_krw"] = np.exp(preds["corrected_pred_log"])
        preds["corrected_ape"] = (preds["corrected_pred_price_krw"] - preds["price_krw"]).abs() / preds["price_krw"]

    summary = []
    for (scope, model), part in metrics.groupby(["scope", "model"], dropna=False):
        baseline = part.loc[part["method"].eq("baseline")].iloc[0]
        eligible = part.loc[part["method"].ne("baseline") & (part["p95_APE"] <= baseline["p95_APE"])]
        if eligible.empty:
            best = part.loc[part["method"].eq("baseline")].iloc[0]
            decision = "보류"
        else:
            best = eligible.sort_values(["MdAPE", "p95_APE"]).iloc[0]
            decision = "채택" if best["MdAPE"] < baseline["MdAPE"] else "보류"
        summary.append({
            "scope": scope,
            "model": model,
            "best_method": str(best["method"]),
            "baseline_MdAPE": float(baseline["MdAPE"]),
            "best_MdAPE": float(best["MdAPE"]),
            "baseline_p95_APE": float(baseline["p95_APE"]),
            "best_p95_APE": float(best["p95_APE"]),
            "decision": decision,
        })

    metrics.to_csv(RESULT_CSV, index=False)
    rules_df.to_csv(RULE_CSV, index=False)
    preds.to_csv(PRED_CSV, index=False)
    result = {
        "created_at": date.today().isoformat(),
        "experiment_id": "T6-PP-residual-calibration",
        "result_csv": str(RESULT_CSV.relative_to(REPO)),
        "rule_csv": str(RULE_CSV.relative_to(REPO)),
        "prediction_csv": str(PRED_CSV.relative_to(REPO)),
        "summary": summary,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    EXP_DOC.write_text(render(result), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
