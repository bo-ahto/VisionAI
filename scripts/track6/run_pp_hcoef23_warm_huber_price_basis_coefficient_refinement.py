#!/usr/bin/env python3
"""Run PP-HCOEF23: residual driver audit for the current Warm Huber candidate.

This experiment does not tune a new point prediction from fixed test or 0604
residuals. It audits where the current Warm Huber stable candidate still fails,
using validation/OOF first, so the next basis-price and coefficient experiments
can be designed from operationally available signals.
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef20_warm_huber_price_basis_coefficient_refinement as h20


EXP_ID = "PP-HCOEF23"
EXP_SLUG = "PP-HCOEF23_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

H22_DIR = REPO / "experiments" / "track6" / "PP-HCOEF22_warm_huber_price_basis_coefficient_refinement"
H22_PREDICTIONS = H22_DIR / "outputs" / "candidate_predictions.csv"

BASELINE = h20.BASELINE
REFERENCE = h20.REFERENCE
PPV8 = h20.PPV8
SVC = h20.SVC
SEED = 20260608
N_BOOTSTRAP = 300
MIN_SEGMENT_N = 15

FOCUS_CANDIDATES = [
    BASELINE,
    REFERENCE,
    "hcoef22_route_mape_guard",
    "hcoef22_route_p95_guard",
    "hcoef22_route_any2_guard",
]

SEGMENT_COLS = [
    "svc_coverage_tier",
    "svc_group_level",
    "svc_group_n_band",
    "qwidth_band",
    "gap_band",
    "pred_spread_band",
    "service_confidence_tier",
    "stable_pred_price_band",
    "log_area_band",
    "medium_support_bucket_grouped",
]

NUMERIC_FEATURES = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "log_area",
    "stable_current_gap_abs",
    "stable_ppv8_gap_abs",
    "stable_svc_gap_abs",
    "ppv8_svc_gap_abs",
]

CATEGORICAL_FEATURES = [
    "svc_coverage_tier",
    "svc_group_level",
    "svc_group_n_band",
    "qwidth_band",
    "gap_band",
    "pred_spread_band",
    "service_confidence_tier",
    "log_area_band",
    "medium_support_bucket_grouped",
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def fmt_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, max_rows: int | None = None, empty: str = "| 없음 |\n| --- |") -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return empty
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt_cell(v) for v in row) + " |")
    return "\n".join(lines)


def load_predictions() -> pd.DataFrame:
    df = pd.read_csv(H22_PREDICTIONS, low_memory=False)
    df = df[df["candidate"].isin(FOCUS_CANDIDATES)].copy()
    if df.empty:
        raise RuntimeError(f"No focus candidates found in {H22_PREDICTIONS}")
    return add_derived_features(df)


def add_quantile_band(frame: pd.DataFrame, col: str, label_prefix: str, out_col: str) -> pd.Series:
    validation = frame[(frame["scope"].eq("validation_oof_row")) & (frame["candidate"].eq(BASELINE))]
    values = pd.to_numeric(validation[col], errors="coerce").dropna()
    if values.nunique() < 4:
        return pd.Series([f"{label_prefix}_unknown"] * len(frame), index=frame.index)
    qs = np.nanquantile(values, [0.0, 0.25, 0.50, 0.75, 1.0])
    qs = np.unique(qs)
    if len(qs) < 4:
        return pd.Series([f"{label_prefix}_unknown"] * len(frame), index=frame.index)
    labels = [f"{label_prefix}_q{i+1}" for i in range(len(qs) - 1)]
    return pd.cut(
        pd.to_numeric(frame[col], errors="coerce"),
        bins=qs,
        labels=labels,
        include_lowest=True,
        duplicates="drop",
    ).astype("object").fillna(f"{label_prefix}_unknown")


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [BASELINE, REFERENCE, PPV8, SVC, "pred_log", "actual_log", "actual_price"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["stable_current_gap_abs"] = (out[BASELINE] - out[REFERENCE]).abs()
    out["stable_ppv8_gap_abs"] = (out[BASELINE] - out[PPV8]).abs()
    out["stable_svc_gap_abs"] = (out[BASELINE] - out[SVC]).abs()
    out["ppv8_svc_gap_abs"] = (out[PPV8] - out[SVC]).abs()
    out["abs_residual_log"] = pd.to_numeric(out["residual_log"], errors="coerce").abs()
    out["abs_residual_log_band"] = pd.cut(
        out["abs_residual_log"],
        bins=[-np.inf, np.log(1.3), np.log(1.5), np.log(2.0), np.inf],
        labels=["within_30pct_log", "30_50pct_log", "50_100pct_log", "over_100pct_log"],
    ).astype("object")
    out["error_direction"] = np.select(
        [
            pd.to_numeric(out["residual_log"], errors="coerce") > np.log(1.10),
            pd.to_numeric(out["residual_log"], errors="coerce") < -np.log(1.10),
        ],
        ["under_predicted", "over_predicted"],
        default="near_balanced",
    )
    out["over_50pct_error"] = pd.to_numeric(out["ape"], errors="coerce") > 0.50
    out["over_100pct_error"] = pd.to_numeric(out["ape"], errors="coerce") > 1.00
    out["log_area_band"] = add_quantile_band(out, "log_area", "area", "log_area_band")

    stable_validation = out[(out["scope"].eq("validation_oof_row")) & (out["candidate"].eq(BASELINE))]
    top_medium = stable_validation["medium_support_bucket"].value_counts(dropna=False).head(12).index
    out["medium_support_bucket_grouped"] = out["medium_support_bucket"].where(
        out["medium_support_bucket"].isin(top_medium),
        "other_bucket",
    )
    for col in SEGMENT_COLS + CATEGORICAL_FEATURES:
        if col in out.columns:
            out[col] = out[col].astype("object").where(out[col].notna(), "missing")
    return out


def metric(frame: pd.DataFrame, pred_log: np.ndarray | None = None) -> dict[str, float]:
    pred = frame["pred_log"].to_numpy(dtype=float) if pred_log is None else np.asarray(pred_log, dtype=float)
    return h20.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        pred,
    )


def metrics_table(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouped = predictions.groupby(["scope", "split", "candidate", "method"], dropna=False)
    for (scope, split, candidate, method), group in grouped:
        m = metric(group)
        rows.append(
            {
                "scope": scope,
                "split": split,
                "candidate": candidate,
                "method": method,
                "n": len(group),
                **m,
            }
        )
    out = pd.DataFrame(rows)
    baseline = out[out["candidate"].eq(BASELINE)][
        ["scope", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "stable_MdAPE",
            "MAPE": "stable_MAPE",
            "p95_APE": "stable_p95_APE",
            "RMSE_log": "stable_RMSE_log",
        }
    )
    reference = out[out["candidate"].eq(REFERENCE)][
        ["scope", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "current70_30_MdAPE",
            "MAPE": "current70_30_MAPE",
            "p95_APE": "current70_30_p95_APE",
            "RMSE_log": "current70_30_RMSE_log",
        }
    )
    out = out.merge(baseline, on="scope", how="left").merge(reference, on="scope", how="left")
    for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_{metric_name}_vs_stable"] = out[metric_name] - out[f"stable_{metric_name}"]
        out[f"delta_{metric_name}_vs_current70_30"] = out[metric_name] - out[f"current70_30_{metric_name}"]
    return out.sort_values(["scope", "MdAPE", "MAPE", "candidate"]).reset_index(drop=True)


def segment_residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    focus = predictions[predictions["candidate"].isin([BASELINE, REFERENCE])].copy()
    overall = metrics_table(focus)
    overall_key = overall.set_index(["scope", "candidate"])

    for segment_col in SEGMENT_COLS:
        if segment_col not in focus.columns:
            continue
        for (scope, split, candidate, segment_value), group in focus.groupby(
            ["scope", "split", "candidate", segment_col], dropna=False
        ):
            if len(group) < MIN_SEGMENT_N:
                continue
            m = metric(group)
            base_row = overall_key.loc[(scope, candidate)]
            rows.append(
                {
                    "scope": scope,
                    "split": split,
                    "candidate": candidate,
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "n": len(group),
                    **m,
                    "delta_MdAPE_vs_candidate_overall": m["MdAPE"] - float(base_row["MdAPE"]),
                    "delta_MAPE_vs_candidate_overall": m["MAPE"] - float(base_row["MAPE"]),
                    "delta_p95_APE_vs_candidate_overall": m["p95_APE"] - float(base_row["p95_APE"]),
                    "median_residual_log": float(np.nanmedian(group["residual_log"])),
                    "mean_residual_log": float(np.nanmean(group["residual_log"])),
                    "median_abs_residual_log": float(np.nanmedian(group["abs_residual_log"])),
                    "over_50pct_error_rate": float(np.nanmean(group["over_50pct_error"])),
                    "over_100pct_error_rate": float(np.nanmean(group["over_100pct_error"])),
                    "under_pred_rate": float(np.nanmean(group["residual_log"] > np.log(1.10))),
                    "over_pred_rate": float(np.nanmean(group["residual_log"] < -np.log(1.10))),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["risk_rank_score"] = (
        out["delta_MAPE_vs_candidate_overall"].clip(lower=0)
        + 0.50 * out["delta_p95_APE_vs_candidate_overall"].clip(lower=0)
        + 0.25 * out["over_50pct_error_rate"]
    )
    return out.sort_values(["candidate", "scope", "risk_rank_score"], ascending=[True, True, False])


def validation_risk_segments(segment_df: pd.DataFrame) -> pd.DataFrame:
    stable = segment_df[
        segment_df["candidate"].eq(BASELINE)
        & segment_df["scope"].isin(["validation_oof_row", "validation_oof_artist"])
    ].copy()
    if stable.empty:
        return pd.DataFrame()

    value_cols = [
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_candidate_overall",
        "delta_MAPE_vs_candidate_overall",
        "delta_p95_APE_vs_candidate_overall",
        "median_residual_log",
        "over_50pct_error_rate",
        "over_100pct_error_rate",
        "under_pred_rate",
        "over_pred_rate",
        "risk_rank_score",
    ]
    pivot = stable.pivot_table(
        index=["segment_col", "segment_value"],
        columns="scope",
        values=value_cols,
        aggfunc="first",
    )
    pivot.columns = [f"{metric}_{scope.replace('validation_oof_', '')}" for metric, scope in pivot.columns]
    pivot = pivot.reset_index()
    pivot = pivot[
        (pivot.get("n_row", 0) >= MIN_SEGMENT_N)
        & (pivot.get("n_artist", 0) >= MIN_SEGMENT_N)
    ].copy()
    if pivot.empty:
        return pivot

    pivot["validation_mean_delta_MAPE"] = pivot[["delta_MAPE_vs_candidate_overall_row", "delta_MAPE_vs_candidate_overall_artist"]].mean(axis=1)
    pivot["validation_mean_delta_p95"] = pivot[["delta_p95_APE_vs_candidate_overall_row", "delta_p95_APE_vs_candidate_overall_artist"]].mean(axis=1)
    pivot["validation_mean_over50"] = pivot[["over_50pct_error_rate_row", "over_50pct_error_rate_artist"]].mean(axis=1)
    pivot["validation_mean_risk_rank"] = pivot[["risk_rank_score_row", "risk_rank_score_artist"]].mean(axis=1)
    pivot["bias_direction"] = np.select(
        [
            pivot[["median_residual_log_row", "median_residual_log_artist"]].mean(axis=1) > np.log(1.05),
            pivot[["median_residual_log_row", "median_residual_log_artist"]].mean(axis=1) < -np.log(1.05),
        ],
        ["주로 낮게 예측", "주로 높게 예측"],
        default="방향성 약함",
    )
    pivot["risk_reason"] = np.select(
        [
            pivot["validation_mean_delta_p95"] > 0.15,
            pivot["validation_mean_delta_MAPE"] > 0.08,
            pivot["validation_mean_over50"] > 0.20,
        ],
        ["p95 큰 오차 위험", "평균 오차 위험", "50% 초과 오차 빈도"],
        default="상대 위험",
    )
    pivot = pivot.sort_values("validation_mean_risk_rank", ascending=False)
    return pivot.reset_index(drop=True)


def append_confirmation_to_risk_segments(risk: pd.DataFrame, segment_df: pd.DataFrame) -> pd.DataFrame:
    if risk.empty:
        return risk
    stable = segment_df[segment_df["candidate"].eq(BASELINE)].copy()
    confirmations = []
    for _, row in risk.iterrows():
        for scope in ["fixed_confirmation", "0604_stress"]:
            match = stable[
                stable["scope"].eq(scope)
                & stable["segment_col"].eq(row["segment_col"])
                & stable["segment_value"].eq(row["segment_value"])
            ]
            if match.empty:
                continue
            first = match.iloc[0]
            confirmations.append(
                {
                    "segment_col": row["segment_col"],
                    "segment_value": row["segment_value"],
                    "scope": scope,
                    "confirm_n": first["n"],
                    "confirm_MdAPE": first["MdAPE"],
                    "confirm_MAPE": first["MAPE"],
                    "confirm_p95_APE": first["p95_APE"],
                    "confirm_delta_MAPE": first["delta_MAPE_vs_candidate_overall"],
                    "confirm_delta_p95": first["delta_p95_APE_vs_candidate_overall"],
                    "confirm_over50": first["over_50pct_error_rate"],
                }
            )
    confirm = pd.DataFrame(confirmations)
    if confirm.empty:
        return risk
    fixed = confirm[confirm["scope"].eq("fixed_confirmation")].drop(columns="scope")
    stress = confirm[confirm["scope"].eq("0604_stress")].drop(columns="scope")
    fixed = fixed.add_prefix("fixed_").rename(
        columns={"fixed_segment_col": "segment_col", "fixed_segment_value": "segment_value"}
    )
    stress = stress.add_prefix("stress0604_").rename(
        columns={"stress0604_segment_col": "segment_col", "stress0604_segment_value": "segment_value"}
    )
    return risk.merge(fixed, on=["segment_col", "segment_value"], how="left").merge(
        stress, on=["segment_col", "segment_value"], how="left"
    )


def coefficient_audit(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    focus_scopes = ["validation_oof_row", "validation_oof_artist"]
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
    for scope in focus_scopes:
        frame = predictions[(predictions["scope"].eq(scope)) & (predictions["candidate"].eq(BASELINE))].copy()
        frame = frame.dropna(subset=["actual_log", "pred_log", "residual_log"])
        if len(frame) < 50:
            continue

        numeric = frame[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
        numeric = numeric.fillna(numeric.median(numeric_only=True))
        categorical = pd.get_dummies(frame[CATEGORICAL_FEATURES].fillna("missing").astype(str), drop_first=True)
        design = pd.concat([numeric, categorical], axis=1)
        design = design.loc[:, design.nunique(dropna=False) > 1]
        scaler = StandardScaler()
        x = scaler.fit_transform(design)

        targets = {
            "signed_residual_log": frame["residual_log"].to_numpy(dtype=float),
            "abs_residual_log": frame["abs_residual_log"].to_numpy(dtype=float),
        }
        for target_name, y in targets.items():
            model = HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=5000)
            model.fit(x, y)
            for feature, coef in zip(design.columns, model.coef_, strict=False):
                if target_name == "signed_residual_log":
                    direction = "낮게 예측되는 방향" if coef > 0 else "높게 예측되는 방향"
                    meaning = "양수 계수는 실제 가격이 예측보다 높은 경향, 음수 계수는 예측이 실제보다 높은 경향을 의미"
                else:
                    direction = "오차 위험 증가" if coef > 0 else "오차 위험 감소"
                    meaning = "양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미"
                rows.append(
                    {
                        "scope": scope,
                        "target": target_name,
                        "feature": feature,
                        "standardized_coefficient": float(coef),
                        "abs_standardized_coefficient": float(abs(coef)),
                        "direction": direction,
                        "interpretation": meaning,
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["target", "scope", "abs_standardized_coefficient"], ascending=[True, True, False])


def bootstrap_candidate_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    available = [c for c in FOCUS_CANDIDATES if c in set(predictions["candidate"])]
    for scope, scope_df in predictions.groupby("scope", dropna=False):
        pivot = scope_df.pivot_table(
            index=["_track6_row_id", "actual_price", "actual_log"],
            columns="candidate",
            values="pred_log",
            aggfunc="first",
        ).reset_index()
        if BASELINE not in pivot.columns:
            continue
        for candidate in available:
            if candidate == BASELINE or candidate not in pivot.columns:
                continue
            common = pivot[pivot[[BASELINE, candidate, "actual_price", "actual_log"]].notna().all(axis=1)]
            if len(common) < 30:
                continue
            actual_price = common["actual_price"].to_numpy(dtype=float)
            actual_log = common["actual_log"].to_numpy(dtype=float)
            stable_pred = common[BASELINE].to_numpy(dtype=float)
            cand_pred = common[candidate].to_numpy(dtype=float)
            deltas = []
            for _ in range(N_BOOTSTRAP):
                idx = rng.integers(0, len(common), len(common))
                stable_m = h20.metric_from_arrays(actual_price[idx], actual_log[idx], stable_pred[idx])
                cand_m = h20.metric_from_arrays(actual_price[idx], actual_log[idx], cand_pred[idx])
                deltas.append(
                    {
                        "delta_MdAPE": cand_m["MdAPE"] - stable_m["MdAPE"],
                        "delta_MAPE": cand_m["MAPE"] - stable_m["MAPE"],
                        "delta_p95_APE": cand_m["p95_APE"] - stable_m["p95_APE"],
                        "delta_RMSE_log": cand_m["RMSE_log"] - stable_m["RMSE_log"],
                    }
                )
            delta_df = pd.DataFrame(deltas)
            rows.append(
                {
                    "scope": scope,
                    "candidate": candidate,
                    "n": len(common),
                    "p_improve_MdAPE": float(np.mean(delta_df["delta_MdAPE"] < 0)),
                    "p_improve_MAPE": float(np.mean(delta_df["delta_MAPE"] < 0)),
                    "p_improve_p95_APE": float(np.mean(delta_df["delta_p95_APE"] < 0)),
                    "p_improve_all3": float(
                        np.mean(
                            (delta_df["delta_MdAPE"] < 0)
                            & (delta_df["delta_MAPE"] < 0)
                            & (delta_df["delta_p95_APE"] < 0)
                        )
                    ),
                    "mean_delta_MdAPE_vs_stable": float(delta_df["delta_MdAPE"].mean()),
                    "mean_delta_MAPE_vs_stable": float(delta_df["delta_MAPE"].mean()),
                    "mean_delta_p95_APE_vs_stable": float(delta_df["delta_p95_APE"].mean()),
                    "mean_delta_RMSE_log_vs_stable": float(delta_df["delta_RMSE_log"].mean()),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["scope", "p_improve_all3", "p_improve_MAPE"], ascending=[True, False, False])


def config_payload(predictions: pd.DataFrame) -> dict[str, Any]:
    return {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Current Warm Huber stable residual driver audit before new basis/coefficient tuning.",
        "input_predictions": str(H22_PREDICTIONS.relative_to(REPO)),
        "baseline_candidate": BASELINE,
        "minimum_reference": REFERENCE,
        "focus_candidates": [c for c in FOCUS_CANDIDATES if c in set(predictions["candidate"])],
        "segment_columns": SEGMENT_COLS,
        "numeric_features_for_coefficient_audit": NUMERIC_FEATURES,
        "categorical_features_for_coefficient_audit": CATEGORICAL_FEATURES,
        "selection_policy": "No threshold, coefficient, or correction is selected from fixed test or 0604 residuals.",
        "bootstrap_iterations": N_BOOTSTRAP,
        "min_segment_n": MIN_SEGMENT_N,
    }


def render_report(
    metrics: pd.DataFrame,
    risk_segments: pd.DataFrame,
    coefficients: pd.DataFrame,
    bootstrap: pd.DataFrame,
    residuals: pd.DataFrame,
) -> str:
    overall_cols = [
        "scope",
        "candidate",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE_vs_stable",
        "delta_MAPE_vs_stable",
        "delta_p95_APE_vs_stable",
    ]
    overall_view = metrics[metrics["candidate"].isin(FOCUS_CANDIDATES)][overall_cols].copy()

    risk_cols = [
        "segment_col",
        "segment_value",
        "n_row",
        "n_artist",
        "validation_mean_delta_MAPE",
        "validation_mean_delta_p95",
        "validation_mean_over50",
        "bias_direction",
        "risk_reason",
        "fixed_confirm_delta_MAPE",
        "fixed_confirm_delta_p95",
        "stress0604_confirm_delta_MAPE",
        "stress0604_confirm_delta_p95",
    ]
    risk_view = risk_segments[[col for col in risk_cols if col in risk_segments.columns]].head(20)

    coef_view = coefficients[
        coefficients["target"].isin(["signed_residual_log", "abs_residual_log"])
    ].head(30)

    boot_view = bootstrap.head(30)

    stable_risk = risk_segments.head(5)
    if stable_risk.empty:
        top_risk_text = "- validation 기준으로 반복 확인된 위험 구간이 충분히 크지 않음."
    else:
        bullets = []
        for _, row in stable_risk.iterrows():
            bullets.append(
                f"- `{row['segment_col']} = {row['segment_value']}`: "
                f"validation 평균 MAPE 악화 `{row['validation_mean_delta_MAPE']:.4f}`, "
                f"p95 악화 `{row['validation_mean_delta_p95']:.4f}`, "
                f"방향 `{row['bias_direction']}`."
            )
        top_risk_text = "\n".join(bullets)

    return f"""# PP-HCOEF23 Warm Huber 남은 오차 원인 분석

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 목적: 현재 Warm 1순위 후보 `hcoef_stable`이 남기는 오차를 validation/OOF 기준으로 분해.
- 최소 비교 기준: `current_70_30`.
- 이 실험은 새 보정값을 test/0604에서 고르지 않음.

## 1. 실험 설계

- 입력: HCOEF22의 후보 예측 산출물.
- 기준 후보: `hcoef_stable`.
- 비교 후보: `current_70_30`, HCOEF22 목적별 라우팅 후보.
- 분석 축:
  - 유사 표본 수와 coverage.
  - quantile width.
  - 후보 간 예측 gap.
  - 작품 크기.
  - 재료/지지체 bucket.
  - service confidence tier.
- validation row OOF와 artist OOF에서 위험 구간을 먼저 찾고, fixed test/0604는 확인용으로만 사용.

## 2. 전체 성능 재확인

{md_table(overall_view, max_rows=40)}

## 3. validation 기준 위험 구간

{top_risk_text}

{md_table(risk_view, max_rows=20)}

## 4. 잔차 계수 감사

- `signed_residual_log`: 양수면 실제 가격이 예측보다 높아 낮게 예측되는 방향.
- `abs_residual_log`: 양수면 남은 오차 크기가 커지는 위험 방향.
- 아래 계수는 validation/OOF에서만 학습한 해석용 계수이며, 가격 예측 후보로 직접 채택하지 않음.

{md_table(coef_view[['scope','target','feature','standardized_coefficient','direction','interpretation']], max_rows=30)}

## 5. 후보별 bootstrap 확인

{md_table(boot_view, max_rows=30)}

## 6. 판단

- HCOEF23은 새 운영 기본 후보를 만들기 위한 실험이 아니라, 다음 기준가/계수 조정 실험의 원인 근거를 만드는 실험임.
- 현재 운영 기본 후보는 `hcoef_stable` 유지.
- 위험 구간이 validation row OOF와 artist OOF에서 동시에 반복되면 HCOEF24/HCOEF25에서만 보정 후보로 사용.
- fixed test 또는 0604에서만 보이는 위험은 보정 기준으로 사용하지 않고 운영 stress risk로만 기록.

## 7. 다음 실험 방향

- HCOEF24:
  - validation에서 확인된 위험 구간을 기준으로 기준가 생성 방식을 세분화.
  - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가와 fallback 순서를 비교.
- HCOEF25:
  - Huber 계수 조정형 잔차 보정.
  - 기준가 신뢰도, 후보 간 gap, quantile width, medium/support bucket을 저차원 피처로 사용.
  - cap/strength를 작게 제한하고 반복 OOF를 우선 적용.

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/risk_segments.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""


def main() -> None:
    ensure_dirs()
    predictions = load_predictions()
    metrics = metrics_table(predictions)
    residuals = segment_residual_analysis(predictions)
    risk = append_confirmation_to_risk_segments(validation_risk_segments(residuals), residuals)
    coefficients = coefficient_audit(predictions)
    bootstrap = bootstrap_candidate_comparison(predictions)
    report = render_report(metrics, risk, coefficients, bootstrap, residuals)

    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    risk.to_csv(EXP_DIR / "outputs" / "risk_segments.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    bootstrap.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config_payload(predictions), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h20.md_to_html(report), encoding="utf-8")

    doc_summary = DOC_ROOT / "pp_hcoef23_warm_huber_price_basis_coefficient_refinement_summary.md"
    doc_summary.write_text(report, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef23_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(
        h20.md_to_html(report),
        encoding="utf-8",
    )

    print(f"[{EXP_ID}] complete")
    print(f"outputs: {EXP_DIR}")
    print(metrics[metrics["candidate"].isin([BASELINE, REFERENCE])][["scope", "candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_string(index=False))
    if not risk.empty:
        print("top risk segments:")
        print(risk[["segment_col", "segment_value", "validation_mean_delta_MAPE", "validation_mean_delta_p95", "bias_direction"]].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
