#!/usr/bin/env python3
"""Run PP-HCOEF7: direct unit-area basis features in Warm Huber residual model.

HCOEF6 showed that hard routing protects p95_APE but removes most of the gain.
This experiment keeps the stable HCOEF3 residual-correction structure and lets
Huber learn small coefficients for unit-area basis and basis reliability
features directly.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_hcoef4_warm_basis_generation_refinement as hcoef4  # noqa: E402
import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF7"
EXP_SLUG = "PP-HCOEF7_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = "current_70_30"
STABLE = "hcoef2_size_reliability_cap005_s050"
N_FOLDS = 5
N_REPEATS = 12
SEED = 20260610

BASE_RESIDUAL_FEATURES = hcoef1.RESIDUAL_FEATURE_SETS["resid_basis_size_reliability"]

FEATURE_SETS = {
    "unit_area_reliability": BASE_RESIDUAL_FEATURES
    + [
        "basis_relaxed_unit_area_log",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_unit_gap",
        "basis_shrunk_weight",
    ],
    "unit_area_level_flags": BASE_RESIDUAL_FEATURES
    + [
        "basis_relaxed_unit_area_log",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_unit_gap",
        "basis_abs_gap",
        "basis_shrunk_weight",
        "basis_level_artist_family",
        "basis_level_detail",
        "basis_level_market",
    ],
    "shrunk_basis_gap": BASE_RESIDUAL_FEATURES
    + [
        "basis_shrunk_price_log",
        "basis_shrunk_vs_current_gap",
        "basis_relaxed_unit_area_log",
        "basis_unit_gap",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_shrunk_weight",
    ],
    "risk_flags": BASE_RESIDUAL_FEATURES
    + [
        "basis_relaxed_unit_area_log",
        "basis_unit_gap",
        "basis_abs_gap",
        "basis_low_iqr_flag",
        "basis_high_n_flag",
        "basis_artist_family_flag",
        "basis_shrunk_weight",
    ],
}

ALPHAS = [0.01, 0.001]
CAPS = [0.03, 0.05]
STRENGTHS = [0.25, 0.50, 0.75]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    base = hcoef4.build_eval_frames()
    basis = hcoef4.build_basis_features("loose")
    frames = hcoef4.merge_policy_frames(base, basis, "loose")
    return {split: add_hcoef7_features(frame) for split, frame in frames.items()}


def add_hcoef7_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    numeric_cols = [
        "basis_relaxed_unit_area_log",
        "basis_relaxed_price_log",
        "basis_shrunk_price_log",
        "basis_shrunk_vs_current_gap",
        "basis_relaxed_vs_current_gap",
        "basis_relaxed_n_log",
        "basis_relaxed_iqr",
        "basis_shrunk_weight",
        REFERENCE,
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
    level = out["basis_relaxed_level"].astype(str)
    out["basis_unit_gap"] = out["basis_relaxed_unit_area_log"] - out[REFERENCE]
    out["basis_abs_gap"] = out["basis_relaxed_vs_current_gap"].abs()
    out["basis_level_artist_family"] = level.isin(["artist_medium_support_size", "artist_size", "artist"]).astype(float)
    out["basis_level_detail"] = level.isin(["artist_medium_support_size", "artist_size"]).astype(float)
    out["basis_level_market"] = level.isin(["medium_support_size", "medium_category_support_size", "medium_size"]).astype(float)
    out["basis_low_iqr_flag"] = out["basis_relaxed_iqr"].le(0.8).astype(float)
    out["basis_high_n_flag"] = out["basis_relaxed_n_log"].ge(np.log1p(10.0)).astype(float)
    out["basis_artist_family_flag"] = out["basis_level_artist_family"]
    return out


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef1.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def stable_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> tuple[np.ndarray, Any]:
    return hcoef5.hcoef2_prediction(train, eval_frame)


def residual_model_prediction(
    train: pd.DataFrame,
    eval_frame: pd.DataFrame,
    features: list[str],
    alpha: float,
    cap: float,
    strength: float,
) -> tuple[np.ndarray, Any]:
    target = train["actual_log"].to_numpy(dtype=float) - train[REFERENCE].to_numpy(dtype=float)
    model = hcoef1.linear_pipeline("huber", alpha)
    model.fit(train[features], target)
    raw = np.asarray(model.predict(eval_frame[features]), dtype=float)
    pred = eval_frame[REFERENCE].to_numpy(dtype=float) + np.clip(raw, -cap, cap) * strength
    return pred, model


def candidate_name(feature_key: str, alpha: float, cap: float, strength: float) -> str:
    return f"hcoef7_{feature_key}_alpha{alpha:g}_cap{cap:.2f}_s{strength:.2f}"


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.row_folds(n, seed)


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.artist_folds(frame, seed)


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            oof: dict[str, np.ndarray] = {}

            for train_idx, hold_idx in folds:
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                stable_pred, _ = stable_prediction(train, hold)
                if STABLE not in oof:
                    oof[STABLE] = np.full(len(validation), np.nan, dtype=float)
                oof[STABLE][hold_idx] = stable_pred

                for feature_key, features in FEATURE_SETS.items():
                    for alpha in ALPHAS:
                        target = train["actual_log"].to_numpy(dtype=float) - train[REFERENCE].to_numpy(dtype=float)
                        model = hcoef1.linear_pipeline("huber", alpha)
                        model.fit(train[features], target)
                        raw = np.asarray(model.predict(hold[features]), dtype=float)
                        for cap in CAPS:
                            for strength in STRENGTHS:
                                name = candidate_name(feature_key, alpha, cap, strength)
                                pred = hold[REFERENCE].to_numpy(dtype=float) + np.clip(raw, -cap, cap) * strength
                                if name not in oof:
                                    oof[name] = np.full(len(validation), np.nan, dtype=float)
                                oof[name][hold_idx] = pred

            ref_metric = metric_from_frame(validation, oof[STABLE])
            for candidate, pred in oof.items():
                metric = metric_from_frame(validation, pred)
                metric_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": candidate,
                        "n": len(validation),
                        **metric,
                        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE_vs_hcoef2": metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - ref_metric["p95_APE"],
                        "improve_count_vs_hcoef2": int(metric["MdAPE"] < ref_metric["MdAPE"])
                        + int(metric["MAPE"] < ref_metric["MAPE"])
                        + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                    }
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, candidate, f"validation_{scheme}_repeat0", pred, "repeated_oof"))
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []

    stable_by_split: dict[str, np.ndarray] = {}
    stable_model = None
    for split in ["validation", "test", "0604_ex50"]:
        pred, model = stable_prediction(validation, frames[split])
        stable_by_split[split] = pred
        stable_model = model
        metric_rows.append(metric_row(split, STABLE, "hcoef2_stable", frames[split], pred, pred))
        pred_rows.append(prediction_frame(frames[split], STABLE, split, pred, "hcoef2_stable"))

    if stable_model is not None:
        coef_rows.append(
            hcoef4.coef_frame(stable_model, STABLE, BASE_RESIDUAL_FEATURES, "huber_residual", "residual_log")
        )

    for feature_key, features in FEATURE_SETS.items():
        for alpha in ALPHAS:
            for cap in CAPS:
                for strength in STRENGTHS:
                    name = candidate_name(feature_key, alpha, cap, strength)
                    fitted_model = None
                    for split in ["validation", "test", "0604_ex50"]:
                        pred, model = residual_model_prediction(validation, frames[split], features, alpha, cap, strength)
                        fitted_model = model
                        metric_rows.append(metric_row(split, name, "unit_area_basis_residual_huber", frames[split], pred, stable_by_split[split]))
                        pred_rows.append(prediction_frame(frames[split], name, split, pred, "unit_area_basis_residual_huber"))
                    if fitted_model is not None:
                        coef_rows.append(hcoef4.coef_frame(fitted_model, name, features, "huber_residual", "residual_log"))

    predictions = pd.concat(pred_rows, ignore_index=True)
    residuals = residual_analysis(predictions)
    return pd.DataFrame(metric_rows), predictions, pd.concat(coef_rows, ignore_index=True), residuals


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred: np.ndarray, method: str) -> pd.DataFrame:
    pred = np.asarray(pred, dtype=float)
    price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred,
            "pred_price": price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred,
            "ape": np.abs(price - actual) / np.clip(actual, 1.0, None),
        }
    )


def metric_row(split: str, candidate: str, method: str, frame: pd.DataFrame, pred: np.ndarray, stable_pred: np.ndarray) -> dict[str, Any]:
    metric = metric_from_frame(frame, pred)
    stable = metric_from_frame(frame, stable_pred)
    return {
        "validation_scheme": "fixed_confirmation",
        "repeat": -1,
        "candidate": candidate,
        "method": method,
        "split": split,
        "n": len(frame),
        **metric,
        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - stable["MdAPE"],
        "delta_MAPE_vs_hcoef2": metric["MAPE"] - stable["MAPE"],
        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - stable["p95_APE"],
        "improve_count_vs_hcoef2": int(metric["MdAPE"] < stable["MdAPE"])
        + int(metric["MAPE"] < stable["MAPE"])
        + int(metric["p95_APE"] < stable["p95_APE"]),
    }


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    repeat_metrics = metrics[metrics["repeat"].ge(0)].copy()
    for (scheme, candidate), group in repeat_metrics.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "mean_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].mean()),
                "mean_delta_MAPE_vs_hcoef2": float(group["delta_MAPE_vs_hcoef2"].mean()),
                "mean_delta_p95_APE_vs_hcoef2": float(group["delta_p95_APE_vs_hcoef2"].mean()),
                "std_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].std()),
                "MdAPE_improve_prob_vs_hcoef2": float((group["delta_MdAPE_vs_hcoef2"] < 0).mean()),
                "MAPE_improve_prob_vs_hcoef2": float((group["delta_MAPE_vs_hcoef2"] < 0).mean()),
                "p95_improve_prob_vs_hcoef2": float((group["delta_p95_APE_vs_hcoef2"] < 0).mean()),
                "all3_improve_prob_vs_hcoef2": float((group["improve_count_vs_hcoef2"] == 3).mean()),
                "mean_improve_count_vs_hcoef2": float(group["improve_count_vs_hcoef2"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["all3_improve_prob_vs_hcoef2", "mean_delta_MdAPE_vs_hcoef2", "mean_delta_MAPE_vs_hcoef2"],
        ascending=[False, True, True],
    )


def select_candidates(summary: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    row = summary[summary["validation_scheme"].eq("row_oof")].set_index("candidate")
    artist = summary[summary["validation_scheme"].eq("artist_oof")].set_index("candidate")
    test = fixed[fixed["split"].eq("test")].set_index("candidate")
    ops = fixed[fixed["split"].eq("0604_ex50")].set_index("candidate")
    candidates = sorted(set(row.index) & set(artist.index) & set(test.index))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate": candidate,
                "row_all3_prob": row.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "artist_all3_prob": artist.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "row_delta_MdAPE": row.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "row_delta_MAPE": row.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "row_delta_p95_APE": row.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "artist_delta_MdAPE": artist.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "artist_delta_MAPE": artist.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "artist_delta_p95_APE": artist.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "test_delta_MdAPE": test.loc[candidate, "delta_MdAPE_vs_hcoef2"],
                "test_delta_MAPE": test.loc[candidate, "delta_MAPE_vs_hcoef2"],
                "test_delta_p95_APE": test.loc[candidate, "delta_p95_APE_vs_hcoef2"],
                "ops0604_delta_MdAPE": ops.loc[candidate, "delta_MdAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_MAPE": ops.loc[candidate, "delta_MAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_p95_APE": ops.loc[candidate, "delta_p95_APE_vs_hcoef2"] if candidate in ops.index else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["passes_repeat_gate"] = (
        out["row_all3_prob"].ge(0.90)
        & out["artist_all3_prob"].ge(0.90)
        & out["row_delta_MdAPE"].lt(0)
        & out["row_delta_MAPE"].le(0)
        & out["row_delta_p95_APE"].le(0)
        & out["artist_delta_MdAPE"].lt(0)
        & out["artist_delta_MAPE"].le(0)
        & out["artist_delta_p95_APE"].le(0)
    )
    out["passes_fixed_guard"] = out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].le(0) & out["test_delta_p95_APE"].le(0)
    out["purpose"] = np.select(
        [
            out["passes_repeat_gate"] & out["passes_fixed_guard"],
            out["row_delta_MAPE"].lt(0) & out["artist_delta_MAPE"].lt(0),
            out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].lt(0),
        ],
        ["operational_candidate", "repeat_mape_candidate", "fixed_confirmation_candidate"],
        default="hold_or_reject",
    )
    return out.sort_values(
        ["passes_repeat_gate", "passes_fixed_guard", "row_delta_MdAPE", "artist_delta_MdAPE", "test_delta_MdAPE"],
        ascending=[False, False, True, True, True],
    )


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": int(len(group)),
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "candidate"])


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    lines = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(summary: pd.DataFrame, fixed: pd.DataFrame, selection: pd.DataFrame, coeffs: pd.DataFrame, residuals: pd.DataFrame) -> None:
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    decision = "새 운영 기본 후보 채택 없음"
    if not selection.empty:
        first = selection.iloc[0]
        if bool(first["passes_repeat_gate"]) and bool(first["passes_fixed_guard"]):
            decision = f"운영 후보 가능: `{first['candidate']}`"
        elif bool(first["passes_repeat_gate"]):
            decision = f"반복 OOF 후보이나 fixed guard 보류: `{first['candidate']}`"

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 면적단가 기준가 직접 잔차 피처 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF4에서 강한 계수로 확인된 면적단가 기준가와 기준가 신뢰도 피처를 HCOEF3 잔차 보정에 직접 추가.",
            f"- 기준 후보: `{STABLE}`.",
            "- 방식: `current_70_30` 잔차를 Huber로 학습하고, 보정값은 cap/strength로 제한.",
            "- 후보 선택: 반복 OOF 우선, fixed test는 최종 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}.",
            "- 이 실험은 routing 조건을 사람이 직접 고정하는 대신 Huber 계수가 basis 신뢰도를 직접 조정하도록 한 점이 HCOEF6와 다름.",
            "",
            "## 2. 후보 선택표",
            "",
            markdown_table(selection.round(4), max_rows=24),
            "",
            "## 3. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4), max_rows=32),
            "",
            "## 4. Fixed test 상위 후보",
            "",
            markdown_table(
                fixed_test[
                    [
                        "candidate",
                        "method",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_hcoef2",
                        "delta_MAPE_vs_hcoef2",
                        "delta_p95_APE_vs_hcoef2",
                    ]
                ].round(4),
                max_rows=24,
            ),
            "",
            "## 5. 주요 계수",
            "",
            "- 계수는 표준화된 피처 기준이다.",
            markdown_table(coeffs.head(80).round(5)),
            "",
            "## 6. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=50),
            "",
            "## 7. 다음 보정 방향",
            "",
            "- 반복 OOF와 fixed guard를 동시에 통과한 후보가 있으면 HCOEF8에서 반복 횟수를 늘려 재검증.",
            "- 통과 후보가 없으면 segmented Huber 계수 또는 작가 메타 residual 피처와 결합하는 방향으로 이동.",
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/repeated_validation_metrics.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef7_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef7_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"])
    repeated_summary = summarize_repeated(repeated_metrics)
    fixed_metrics, fixed_predictions, coeffs, residuals = fixed_confirmation(frames)
    selection = select_candidates(repeated_summary, fixed_metrics)

    out = EXP_DIR / "outputs"
    fixed_metrics.to_csv(out / "metrics.csv", index=False)
    repeated_metrics.to_csv(out / "repeated_validation_metrics.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    pd.concat([repeated_predictions, fixed_predictions], ignore_index=True).to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": STABLE,
        "feature_sets": FEATURE_SETS,
        "alphas": ALPHAS,
        "caps": CAPS,
        "strengths": STRENGTHS,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "selection_policy": "row/artist repeated OOF first; fixed test p95 must not worsen for operational candidate",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(repeated_summary, fixed_metrics, selection, coeffs, residuals)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected top ---")
    print(selection.head(12).round(4).to_string(index=False))
    print("--- fixed test top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(12)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_vs_hcoef2", "delta_MAPE_vs_hcoef2", "delta_p95_APE_vs_hcoef2"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
