#!/usr/bin/env python3
"""Warm birth/generation + activity/external residual correction experiment.

This experiment follows PP-AMW8 but expands the tested signals around the
birth-year/generation axis:

- birth year + generation only
- birth year + generation + one activity signal
- birth year + generation + activity bundle
- birth year + generation + exhibition/gallery diagnostics

The base Warm prediction stays fixed. Validation uses artist-key grouped OOF
corrections; test applies a correction fitted only on the full validation set.
"""
from __future__ import annotations

import html
import importlib.util
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
AMW8_SCRIPT = REPO / "experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction/scripts/run_experiment.py"
spec = importlib.util.spec_from_file_location("amw8_module", AMW8_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import AMW8 script: {AMW8_SCRIPT}")
amw8 = importlib.util.module_from_spec(spec)
sys.modules["amw8_module"] = amw8
spec.loader.exec_module(amw8)


EXPERIMENT_ID = "PP-AMW10"
EXP_DIR = REPO / "experiments/track6/PP-AMW10_warm_birth_generation_activity_external_residual_correction"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
LOG_DIR = EXP_DIR / "logs"

BASE_CANDIDATE = amw8.BASE_CANDIDATE
SEED = 20260608

BIRTH_YEAR = "artist_meta_birth_year"
GENERATION = "artist_birth_generation_bin"
CAREER_STAGE = "artist_meta_career_stage"

TOTAL_WORKS = "artist_meta_total_works_log1p"
TOTAL_WORKS_MISSING = "artist_meta_total_works_missing"
FOR_SALE = "artist_meta_for_sale_works_log1p"
FOR_SALE_MISSING = "artist_meta_for_sale_works_missing"
FOLLOWERS = "artist_meta_followers_log1p"
FOLLOWERS_MISSING = "artist_meta_followers_missing"
MARKET_GAP = "artist_meta_market_depth_gap_log1p"
FOR_SALE_RATIO = "artist_meta_for_sale_ratio"

EXHIBITION_TOTAL = "artist_exhibition_total_count_log"
EXHIBITION_AVAILABLE = "artist_exhibition_available_count"
GALLERY_TIER = "gallery_tier_raw_numeric"
GALLERY_AVAILABLE = "gallery_tier_raw_available_flag"
GALLERY_SOURCE = "gallery_feature_source"
GALLERY_CITY = "gallery_city_count_log"

BASE_FEATURES = [BIRTH_YEAR, GENERATION]
ACTIVITY_FEATURES = [
    TOTAL_WORKS,
    TOTAL_WORKS_MISSING,
    FOR_SALE,
    FOR_SALE_MISSING,
    FOLLOWERS,
    FOLLOWERS_MISSING,
]
MARKET_FEATURES = [MARKET_GAP, FOR_SALE_RATIO]
EXTERNAL_FEATURES = [EXHIBITION_TOTAL, EXHIBITION_AVAILABLE, GALLERY_TIER, GALLERY_AVAILABLE, GALLERY_SOURCE, GALLERY_CITY]

FEATURE_SETS: dict[str, list[str]] = {
    "birth_generation": BASE_FEATURES,
    "birth_generation_total_works": BASE_FEATURES + [TOTAL_WORKS, TOTAL_WORKS_MISSING],
    "birth_generation_for_sale": BASE_FEATURES + [FOR_SALE, FOR_SALE_MISSING],
    "birth_generation_followers": BASE_FEATURES + [FOLLOWERS, FOLLOWERS_MISSING],
    "birth_generation_market_gap": BASE_FEATURES + MARKET_FEATURES,
    "birth_generation_activity_bundle": BASE_FEATURES + ACTIVITY_FEATURES + MARKET_FEATURES,
    "birth_generation_career_activity": BASE_FEATURES + [CAREER_STAGE] + ACTIVITY_FEATURES + MARKET_FEATURES,
    "birth_generation_exhibition": BASE_FEATURES + [EXHIBITION_TOTAL, EXHIBITION_AVAILABLE],
    "birth_generation_gallery": BASE_FEATURES + [GALLERY_TIER, GALLERY_AVAILABLE, GALLERY_SOURCE, GALLERY_CITY],
    "birth_generation_activity_external": BASE_FEATURES + ACTIVITY_FEATURES + MARKET_FEATURES + EXTERNAL_FEATURES,
}


def ensure_dirs() -> None:
    for directory in [OUT_DIR, REPORT_DIR, LOG_DIR, EXP_DIR / "scripts"]:
        directory.mkdir(parents=True, exist_ok=True)


def gate_mask(frame: pd.DataFrame, gate: str) -> np.ndarray:
    if gate == "none":
        return np.ones(len(frame), dtype=bool)
    if gate == "birth_available":
        return pd.to_numeric(frame[BIRTH_YEAR], errors="coerce").notna().to_numpy()
    if gate == "activity_available":
        cols = ["artist_meta_total_works", "artist_meta_for_sale_works", "artist_meta_followers"]
        return frame[cols].apply(lambda col: pd.to_numeric(col, errors="coerce").notna()).any(axis=1).to_numpy()
    if gate == "activity_complete":
        cols = ["artist_meta_total_works", "artist_meta_followers"]
        return frame[cols].apply(lambda col: pd.to_numeric(col, errors="coerce").notna()).all(axis=1).to_numpy()
    if gate == "external_available":
        cols = ["artist_exhibition_total_count", "gallery_tier_raw_numeric", "gallery_city_count"]
        return frame[cols].apply(lambda col: pd.to_numeric(col, errors="coerce").notna()).any(axis=1).to_numpy()
    raise ValueError(gate)


def gates_for_feature_set(set_name: str) -> list[str]:
    gates = ["none"]
    if "activity" in set_name or any(token in set_name for token in ["total_works", "for_sale", "followers", "market"]):
        gates.append("activity_available")
    if "external" in set_name or "gallery" in set_name or "exhibition" in set_name:
        gates.append("external_available")
    return gates


def candidate_grid() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model_specs = [
        ("huber", 0.01),
        ("ridge", 0.1),
    ]
    for set_name, features in FEATURE_SETS.items():
        for gate in gates_for_feature_set(set_name):
            for model_kind, alpha in model_specs:
                for cap in [0.03, 0.05]:
                    for strength in [0.50, 0.75]:
                        rows.append(
                            {
                                "candidate": (
                                    f"{model_kind}_{set_name}_gate{gate}_"
                                    f"alpha{str(alpha).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}_s{str(strength).replace('.', 'p')}"
                                ),
                                "family": f"{model_kind}_gated_residual",
                                "feature_set": set_name,
                                "features": features,
                                "gate": gate,
                                "model_kind": model_kind,
                                "alpha": alpha,
                                "epsilon": 1.35,
                                "cap": cap,
                                "strength": strength,
                            }
                        )
    return rows


def add_deltas(row: dict[str, Any], base: dict[str, float], prefix: str) -> None:
    for metric in ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]:
        row[f"{prefix}delta_{metric}"] = float(row[f"{prefix}{metric}"] - base[metric])


def balanced_delta(row: dict[str, Any], prefix: str) -> float:
    return float(row[f"{prefix}delta_MdAPE"] + row[f"{prefix}delta_MAPE"] + 0.20 * row[f"{prefix}delta_p95_APE"])


def candidate_metric_row(
    cand: dict[str, Any],
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
    base_val: dict[str, float],
    base_test: dict[str, float],
) -> dict[str, Any]:
    val_metrics = amw8.corrected_metrics(val, val_corr)
    test_metrics = amw8.corrected_metrics(test, test_corr)
    row: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": cand["candidate"],
        "family": cand["family"],
        "feature_set": cand["feature_set"],
        "features": ",".join(cand["features"]),
        "gate": cand["gate"],
        "model_kind": cand["model_kind"],
        "alpha": cand["alpha"],
        "cap": cand["cap"],
        "strength": cand["strength"],
        "validation_gate_rate": float(gate_mask(val, cand["gate"]).mean()),
        "test_gate_rate": float(gate_mask(test, cand["gate"]).mean()),
        "validation_mean_abs_correction": float(np.mean(np.abs(val_corr))),
        "test_mean_abs_correction": float(np.mean(np.abs(test_corr))),
        "validation_nonzero_rate": float(np.mean(np.abs(val_corr) > 1e-12)),
        "test_nonzero_rate": float(np.mean(np.abs(test_corr) > 1e-12)),
        **{f"validation_{key}": value for key, value in val_metrics.items()},
        **{f"test_{key}": value for key, value in test_metrics.items()},
    }
    add_deltas(row, base_val, "validation_")
    add_deltas(row, base_test, "test_")
    row["validation_balanced_delta"] = balanced_delta(row, "validation_")
    row["test_balanced_delta"] = balanced_delta(row, "test_")
    return row


def candidate_predictions(
    candidate: str,
    family: str,
    feature_set: str,
    gate: str,
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
) -> pd.DataFrame:
    frames = []
    for split, frame, correction in [("validation", val, val_corr), ("test", test, test_corr)]:
        pred_log = frame["pred_log"].to_numpy(dtype=float) + correction
        actual_log = frame["actual_log"].to_numpy(dtype=float)
        out = pd.DataFrame(
            {
                "experiment_id": EXPERIMENT_ID,
                "candidate": candidate,
                "family": family,
                "feature_set": feature_set,
                "gate": gate,
                "split": split,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame["artist_key"].to_numpy(),
                "artist_name_ko": frame["artist_name_ko"].to_numpy(),
                "actual_log": actual_log,
                "base_pred_log": frame["pred_log"].to_numpy(dtype=float),
                "correction_log": correction,
                "pred_log": pred_log,
                "actual_price": np.exp(actual_log),
                "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
            }
        )
        out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def run_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_val = amw8.base_metrics(val)
    base_test = amw8.base_metrics(test)
    metric_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    coef_rows: list[dict[str, Any]] = []

    for cand in candidate_grid():
        val_corr = amw8.oof_linear(
            val,
            cand["features"],
            cand["model_kind"],
            cand["alpha"],
            cand["epsilon"],
            cand["cap"],
            cand["strength"],
        )
        test_corr, info = amw8.fit_apply_linear(
            val,
            test,
            cand["features"],
            cand["model_kind"],
            cand["alpha"],
            cand["epsilon"],
            cand["cap"],
            cand["strength"],
        )
        val_corr = val_corr * gate_mask(val, cand["gate"]).astype(float)
        test_corr = test_corr * gate_mask(test, cand["gate"]).astype(float)

        metric_rows.append(candidate_metric_row(cand, val, test, val_corr, test_corr, base_val, base_test))
        prediction_frames.append(
            candidate_predictions(cand["candidate"], cand["family"], cand["feature_set"], cand["gate"], val, test, val_corr, test_corr)
        )
        for coef in sorted(info["coef_rows"], key=lambda r: abs(r["coefficient"]), reverse=True)[:20]:
            coef_rows.append(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "candidate": cand["candidate"],
                    "family": cand["family"],
                    "feature_set": cand["feature_set"],
                    "gate": cand["gate"],
                    **coef,
                }
            )

    metrics = pd.DataFrame(metric_rows).sort_values(["validation_balanced_delta", "validation_delta_MAPE"])
    predictions = pd.concat(prediction_frames, ignore_index=True)
    coefficients = pd.DataFrame(coef_rows)
    return metrics, predictions, coefficients


def fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return ""
        return f"{float(value):.{digits}f}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, columns].head(max_rows)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def feature_set_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature_set, group in metrics.groupby("feature_set"):
        best_test = group.sort_values(["test_balanced_delta", "test_delta_MAPE"]).iloc[0]
        best_val = group.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]).iloc[0]
        rows.append(
            {
                "feature_set": feature_set,
                "best_test_candidate": best_test["candidate"],
                "best_test_delta_MdAPE": best_test["test_delta_MdAPE"],
                "best_test_delta_MAPE": best_test["test_delta_MAPE"],
                "best_test_delta_p95_APE": best_test["test_delta_p95_APE"],
                "best_validation_candidate": best_val["candidate"],
                "best_validation_delta_MdAPE": best_val["validation_delta_MdAPE"],
                "best_validation_delta_MAPE": best_val["validation_delta_MAPE"],
                "best_validation_delta_p95_APE": best_val["validation_delta_p95_APE"],
            }
        )
    return pd.DataFrame(rows).sort_values(["best_test_delta_MAPE", "best_test_delta_MdAPE"])


def write_report(base_val: dict[str, float], base_test: dict[str, float], metrics: pd.DataFrame, bootstrap: pd.DataFrame, summary: pd.DataFrame) -> None:
    cols = [
        "candidate",
        "feature_set",
        "gate",
        "family",
        "validation_delta_MdAPE",
        "validation_delta_MAPE",
        "validation_delta_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "test_mean_abs_correction",
    ]
    summary_cols = [
        "feature_set",
        "best_test_delta_MdAPE",
        "best_test_delta_MAPE",
        "best_test_delta_p95_APE",
        "best_test_candidate",
    ]
    boot_cols = [
        "sample_type",
        "candidate",
        "mean_delta_MdAPE",
        "improvement_probability_MdAPE",
        "mean_delta_MAPE",
        "improvement_probability_MAPE",
        "mean_delta_p95_APE",
        "improvement_probability_p95_APE",
    ]
    all3 = metrics[(metrics["test_delta_MdAPE"] < 0) & (metrics["test_delta_MAPE"] < 0) & (metrics["test_delta_p95_APE"] < 0)]
    lines = [
        "# PP-AMW10 Warm 생년/세대 + 활동/갤러리 잔차 보정",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{BASE_CANDIDATE}`",
        "- 목적: 생년+세대 조합을 중심으로 활동량, 판매 노출, 팔로워, 전시, 갤러리 신호를 추가했을 때 잔차 보정 개선이 유지되는지 확인",
        "- validation: 작가 키 기준 5-fold OOF",
        "- test: validation 전체 학습 후 고정 test 1회 적용",
        "- gate: 피처 결측/외부 피처 미보유 구간에 보정 적용을 제한하는 진단 옵션",
        "",
        "## 1. 기준 성능",
        "",
        "| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| validation | {fmt(base_val['RMSE_log'])} | {fmt(base_val['MdAPE'])} | {fmt(base_val['MAPE'])} | {fmt(base_val['p95_APE'])} | {fmt(base_val['Within_30'])} | {fmt(base_val['Within_50'])} |",
        f"| test | {fmt(base_test['RMSE_log'])} | {fmt(base_test['MdAPE'])} | {fmt(base_test['MAPE'])} | {fmt(base_test['p95_APE'])} | {fmt(base_test['Within_30'])} | {fmt(base_test['Within_50'])} |",
        "",
        "## 2. 피처 세트별 test 최선 요약",
        "",
        markdown_table(summary, summary_cols, max_rows=20),
        "",
        "## 3. test 3지표 모두 개선 후보",
        "",
        markdown_table(all3.sort_values(["test_delta_MAPE", "test_delta_p95_APE"]), cols, max_rows=30),
        "",
        "## 4. validation 기준 상위 후보",
        "",
        markdown_table(metrics.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]), cols, max_rows=20),
        "",
        "## 5. test 기준 상위 후보",
        "",
        markdown_table(metrics.sort_values(["test_balanced_delta", "test_delta_MAPE"]), cols, max_rows=20),
        "",
        "## 6. bootstrap 안정성",
        "",
        markdown_table(bootstrap.sort_values(["sample_type", "mean_delta_MAPE"]), boot_cols, max_rows=40),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/candidate_metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/feature_set_summary.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
        "- `outputs/coefficients_top.csv`",
        "- `outputs/experiment_manifest.json`",
    ]
    md = "\n".join(lines)
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    html_doc = (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<title>PP-AMW10 Warm birth generation activity external correction</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;line-height:1.55;color:#1f2933}"
        "pre{white-space:pre-wrap;background:#f6f8fa;padding:20px;border-radius:8px}</style></head>"
        f"<body><pre>{html.escape(md)}</pre></body></html>"
    )
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")


def run() -> None:
    ensure_dirs()
    val, test = amw8.amw7.prepare_frames()
    base_val = amw8.base_metrics(val)
    base_test = amw8.base_metrics(test)
    metrics, predictions, coefficients = run_candidates(val, test)
    summary = feature_set_summary(metrics)
    bootstrap_summary, bootstrap_samples = amw8.bootstrap_summary(metrics, predictions, test)

    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    coefficients.to_csv(OUT_DIR / "coefficients_top.csv", index=False)
    summary.to_csv(OUT_DIR / "feature_set_summary.csv", index=False)
    bootstrap_summary.to_csv(OUT_DIR / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(OUT_DIR / "bootstrap_samples.csv", index=False)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "title": "Warm birth/generation + activity/external residual correction",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": BASE_CANDIDATE,
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "feature_sets": FEATURE_SETS,
        "candidate_count": int(len(metrics)),
        "validation_method": "artist-key grouped 5-fold OOF",
        "test_method": "fit correction on full validation and apply once to fixed test",
        "outputs": [
            "outputs/candidate_metrics.csv",
            "outputs/candidate_predictions.csv",
            "outputs/feature_set_summary.csv",
            "outputs/bootstrap_summary.csv",
            "outputs/bootstrap_samples.csv",
            "outputs/coefficients_top.csv",
            "reports/result_report.md",
            "reports/result_report.html",
        ],
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(base_val, base_test, metrics, bootstrap_summary, summary)


if __name__ == "__main__":
    run()
