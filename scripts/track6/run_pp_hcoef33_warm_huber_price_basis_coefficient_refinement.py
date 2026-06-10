#!/usr/bin/env python3
"""Run PP-HCOEF33: extended validation for HCOEF32 ultra-micro candidates.

PP-HCOEF32 found a tiny fixed-test p95 improvement candidate, but its repeated
all3 signal was weak. This script does not tune a new candidate. It narrows the
candidate set and performs stronger repeated row/artist validation to decide
whether the HCOEF32 candidate can be promoted beyond "fixed confirmation".

Selection principle:

* Validation/OOF and repeated split stability are the primary evidence.
* Fixed test and 0604 are confirmation checks only.
* 0604 labels or fixed residuals are never used to create a new rule.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24
from scripts.track6 import run_pp_hcoef28_warm_huber_price_basis_coefficient_refinement as h28


EXP_ID = "PP-HCOEF33"
EXP_SLUG = "PP-HCOEF33_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

H32_DIR = REPO / "experiments" / "track6" / "PP-HCOEF32_warm_huber_price_basis_coefficient_refinement"
H32_PREDICTIONS = H32_DIR / "outputs" / "candidate_predictions.csv"
H32_SELECTED = H32_DIR / "outputs" / "selected_candidates.csv"
H32_COEFFICIENTS = H32_DIR / "outputs" / "feature_coefficients.csv"

BASELINE = h28.BASELINE
REFERENCE = h28.REFERENCE

H32_CONFIRM = "hcoef32_s03_all3_dir_top2_w0p025_cap0p001"
H32_CONFIRM_CAP25 = "hcoef32_s03_all3_dir_top2_w0p025_cap0p0025"
H32_NEAR_MID = "hcoef32_s03_all3_dir_top2_w0p05_cap0p0025"
H32_MAPE_NEAR = "hcoef32_s03_mape_dir_top2_w0p05_cap0p0025"
H29_MAPE_RISK = "hcoef29_risk_guarded_component_s0p5_cap0p08"
H29_0604_RISK = "hcoef29_core_component_delta_s0p5_cap0p08"

FOCUS_CANDIDATES = [
    BASELINE,
    REFERENCE,
    H32_CONFIRM,
    H32_CONFIRM_CAP25,
    H32_NEAR_MID,
    H32_MAPE_NEAR,
    H29_MAPE_RISK,
    H29_0604_RISK,
]

N_REPEATS = 2000
SEED = 20260608
ROW_FRACTIONS = [0.80, 0.70]
ARTIST_FRACTIONS = [0.80, 0.70]

USECOLS = {
    "experiment_id",
    "scope",
    "split",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "actual_log",
    "actual_price",
    "candidate",
    "method",
    "source_candidate",
    "mask_name",
    "mask_applied",
    "strength",
    "cap",
    "pred_log",
    "pred_price",
    "policy_move_log",
    "ape",
    "move_weight",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "svc_group_level",
    "service_confidence_tier",
    "medium_support_bucket",
    "log_area",
    "quantile_width",
    "svc_group_n",
    "svc_group_n_log",
    "stable_ppv8_gap_abs",
}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_focus_predictions() -> pd.DataFrame:
    if not H32_PREDICTIONS.exists():
        raise FileNotFoundError(H32_PREDICTIONS)
    header_cols = pd.read_csv(H32_PREDICTIONS, nrows=0).columns.tolist()
    usecols = [col for col in header_cols if col in USECOLS]
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(H32_PREDICTIONS, usecols=usecols, chunksize=250_000, low_memory=False):
        focused = chunk[chunk["candidate"].isin(FOCUS_CANDIDATES)].copy()
        if not focused.empty:
            chunks.append(focused)
    if not chunks:
        raise RuntimeError("No focus candidate predictions were loaded from HCOEF32.")
    out = pd.concat(chunks, ignore_index=True, sort=False)
    out["source_experiment_id"] = out["experiment_id"]
    out["experiment_id"] = EXP_ID
    return out


def point_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    metrics = h28.point_metrics(predictions)
    order = {candidate: idx for idx, candidate in enumerate(FOCUS_CANDIDATES)}
    metrics["candidate_order"] = metrics["candidate"].map(order).fillna(99)
    return metrics.sort_values(["scope", "candidate_order", "candidate"]).drop(columns=["candidate_order"])


def repeated_validation(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    detail_rows: list[dict[str, Any]] = []
    scopes = ["validation_oof_row", "validation_oof_artist"]

    for scope in scopes:
        scoped = predictions[predictions["scope"].eq(scope)].copy()
        if scoped.empty:
            continue
        row_ids = scoped["_track6_row_id"].dropna().unique()
        artists = (
            scoped[["_track6_row_id", "artist_key"]]
            .drop_duplicates()["artist_key"]
            .fillna("unknown")
            .astype(str)
            .unique()
        )
        schemes: list[tuple[str, float, np.ndarray]] = []
        for fraction in ROW_FRACTIONS:
            schemes.append((f"row_subsample_{int(fraction * 100)}pct", fraction, row_ids))
        for fraction in ARTIST_FRACTIONS:
            schemes.append((f"artist_holdout_{int(fraction * 100)}pct", fraction, artists))

        for scheme, fraction, population in schemes:
            for repeat in range(N_REPEATS):
                n_take = max(1, int(len(population) * fraction))
                chosen = set(rng.choice(population, size=n_take, replace=False))
                if scheme.startswith("row_"):
                    subset = scoped[scoped["_track6_row_id"].isin(chosen)]
                else:
                    subset = scoped[scoped["artist_key"].fillna("unknown").astype(str).isin(chosen)]

                base_group = subset[subset["candidate"].eq(BASELINE)]
                base_metrics = h28.metric_from_arrays(
                    base_group["actual_price"].to_numpy(),
                    base_group["actual_log"].to_numpy(),
                    base_group["pred_log"].to_numpy(),
                )
                for candidate, group in subset.groupby("candidate", sort=False):
                    metrics = h28.metric_from_arrays(
                        group["actual_price"].to_numpy(),
                        group["actual_log"].to_numpy(),
                        group["pred_log"].to_numpy(),
                    )
                    row = {
                        "source_scope": scope,
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": candidate,
                        **metrics,
                    }
                    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                        row[f"delta_{metric}_vs_stable"] = metrics[metric] - base_metrics[metric]
                    row["MdAPE_improved"] = metrics["MdAPE"] < base_metrics["MdAPE"]
                    row["MAPE_improved"] = metrics["MAPE"] < base_metrics["MAPE"]
                    row["p95_improved"] = metrics["p95_APE"] < base_metrics["p95_APE"]
                    detail_rows.append(row)

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return detail, detail
    detail["all3_improved"] = detail["MdAPE_improved"] & detail["MAPE_improved"] & detail["p95_improved"]
    detail["any2_improved"] = detail[["MdAPE_improved", "MAPE_improved", "p95_improved"]].sum(axis=1) >= 2

    rows: list[dict[str, Any]] = []
    for (scope, scheme, candidate), group in detail.groupby(["source_scope", "validation_scheme", "candidate"], sort=False):
        row: dict[str, Any] = {
            "source_scope": scope,
            "validation_scheme": scheme,
            "candidate": candidate,
            "n_repeats": int(group["repeat"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{metric}_vs_stable"]
            row[f"mean_delta_{metric}_vs_stable"] = float(delta.mean())
            row[f"median_delta_{metric}_vs_stable"] = float(delta.median())
            row[f"q01_delta_{metric}_vs_stable"] = float(delta.quantile(0.01))
            row[f"q05_delta_{metric}_vs_stable"] = float(delta.quantile(0.05))
            row[f"q95_delta_{metric}_vs_stable"] = float(delta.quantile(0.95))
            row[f"q99_delta_{metric}_vs_stable"] = float(delta.quantile(0.99))
            row[f"worst_delta_{metric}_vs_stable"] = float(delta.max())
        for metric in ["MdAPE", "MAPE", "p95"]:
            row[f"{metric}_improve_prob"] = float(group[f"{metric}_improved"].mean())
        row["all3_improve_prob"] = float(group["all3_improved"].mean())
        row["any2_improve_prob"] = float(group["any2_improved"].mean())
        rows.append(row)

    summary = pd.DataFrame(rows)
    return detail, summary


def candidate_gate_summary(metrics: pd.DataFrame, repeated: pd.DataFrame) -> pd.DataFrame:
    def metric_slice(scope: str, prefix: str) -> pd.DataFrame:
        cols = [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "delta_RMSE_log_vs_stable",
            "improve_count_vs_stable",
            "mean_move_weight",
        ]
        present = [col for col in cols if col in metrics.columns]
        out = metrics[metrics["scope"].eq(scope)][present].copy()
        return out.rename(
            columns={
                "MdAPE": f"{prefix}_MdAPE",
                "MAPE": f"{prefix}_MAPE",
                "p95_APE": f"{prefix}_p95_APE",
                "RMSE_log": f"{prefix}_RMSE_log",
                "delta_MdAPE_vs_stable": f"{prefix}_delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable": f"{prefix}_delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable": f"{prefix}_delta_p95_APE_vs_stable",
                "delta_RMSE_log_vs_stable": f"{prefix}_delta_RMSE_log_vs_stable",
                "improve_count_vs_stable": f"{prefix}_improve_count_vs_stable",
                "mean_move_weight": f"{prefix}_mean_move_weight",
            }
        )

    out = metric_slice("validation_oof_row", "row_oof")
    for scope, prefix in [
        ("validation_oof_artist", "artist_oof"),
        ("fixed_confirmation", "test"),
        ("0604_stress", "stress0604"),
    ]:
        out = out.merge(metric_slice(scope, prefix), on="candidate", how="outer")

    if not repeated.empty:
        prob = repeated.pivot_table(
            index="candidate",
            values=[
                "all3_improve_prob",
                "any2_improve_prob",
                "MdAPE_improve_prob",
                "MAPE_improve_prob",
                "p95_improve_prob",
                "mean_delta_MdAPE_vs_stable",
                "mean_delta_MAPE_vs_stable",
                "mean_delta_p95_APE_vs_stable",
                "worst_delta_p95_APE_vs_stable",
            ],
            aggfunc=["min", "mean"],
        )
        prob.columns = [f"repeated_{stat}_{metric}" for stat, metric in prob.columns]
        out = out.merge(prob.reset_index(), on="candidate", how="left")

    stable = out[out["candidate"].eq(BASELINE)].iloc[0]
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= stable["test_p95_APE"]
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= stable["stress0604_p95_APE"]
    out["fixed_test_2of3"] = out["test_improve_count_vs_stable"].fillna(0) >= 2
    out["repeated_any2_gate_90"] = out["repeated_min_any2_improve_prob"].fillna(0.0) >= 0.90
    out["repeated_all3_gate_90"] = out["repeated_min_all3_improve_prob"].fillna(0.0) >= 0.90
    out["repeated_all3_gate_95"] = out["repeated_min_all3_improve_prob"].fillna(0.0) >= 0.95
    out["decision"] = np.select(
        [
            out["candidate"].eq(BASELINE),
            out["candidate"].eq(REFERENCE),
            out["repeated_all3_gate_95"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            out["repeated_all3_gate_90"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            out["repeated_any2_gate_90"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            (out["test_MAPE"] < stable["test_MAPE"]) & out["fixed_test_p95_guard"],
        ],
        [
            "현재 안정 후보",
            "서비스 v0.1 기준",
            "강한 검증 후보",
            "반복 all3 검증 후보",
            "반복 any2 검증 후보",
            "fixed/0604 확인 후보",
            "MAPE 목적 후보",
        ],
        default="보류",
    )
    order = {
        "현재 안정 후보": 0,
        "강한 검증 후보": 1,
        "반복 all3 검증 후보": 2,
        "반복 any2 검증 후보": 3,
        "fixed/0604 확인 후보": 4,
        "MAPE 목적 후보": 5,
        "서비스 v0.1 기준": 6,
        "보류": 7,
    }
    out["decision_order"] = out["decision"].map(order).fillna(99)
    return out.sort_values(["decision_order", "test_MdAPE", "test_MAPE", "test_p95_APE", "candidate"]).drop(columns=["decision_order"])


def segment_impact(predictions: pd.DataFrame) -> pd.DataFrame:
    segment_cols = [
        "qwidth_band",
        "svc_group_n_band",
        "gap_band",
        "pred_spread_band",
        "svc_group_level",
        "stable_pred_price_band",
    ]
    rows: list[dict[str, Any]] = []
    focus = [H32_CONFIRM, H32_NEAR_MID, H29_MAPE_RISK, H29_0604_RISK]
    subset = predictions[predictions["candidate"].isin([BASELINE, *focus])].copy()
    for (scope, split), scope_df in subset.groupby(["scope", "split"], sort=False):
        base = scope_df[scope_df["candidate"].eq(BASELINE)]
        for segment in segment_cols:
            if segment not in scope_df.columns:
                continue
            base_groups = {
                str(value): group
                for value, group in base.groupby(segment, dropna=False)
            }
            for candidate in focus:
                cand = scope_df[scope_df["candidate"].eq(candidate)]
                for value, group in cand.groupby(segment, dropna=False):
                    key = str(value)
                    base_group = base_groups.get(key)
                    if base_group is None or len(group) < 15:
                        continue
                    m = h28.metric_from_arrays(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy())
                    bm = h28.metric_from_arrays(base_group["actual_price"].to_numpy(), base_group["actual_log"].to_numpy(), base_group["pred_log"].to_numpy())
                    rows.append(
                        {
                            "scope": scope,
                            "split": split,
                            "candidate": candidate,
                            "segment": segment,
                            "segment_value": key,
                            "n": int(m["n"]),
                            "delta_MdAPE_vs_stable": m["MdAPE"] - bm["MdAPE"],
                            "delta_MAPE_vs_stable": m["MAPE"] - bm["MAPE"],
                            "delta_p95_APE_vs_stable": m["p95_APE"] - bm["p95_APE"],
                            "delta_RMSE_log_vs_stable": m["RMSE_log"] - bm["RMSE_log"],
                        }
                    )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_delta_sum"] = out[["delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]].abs().sum(axis=1)
    return out.sort_values(["scope", "candidate", "abs_delta_sum"], ascending=[True, True, False])


def residual_analysis(predictions: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    focus = list(dict.fromkeys([BASELINE, REFERENCE, *selected.head(8)["candidate"].tolist()]))
    return h28.residual_analysis(predictions[predictions["candidate"].isin(focus)].copy(), selected)


def coefficient_summary() -> pd.DataFrame:
    if not H32_COEFFICIENTS.exists():
        return pd.DataFrame()
    coeffs = pd.read_csv(H32_COEFFICIENTS)
    out = coeffs[coeffs["candidate"].isin(FOCUS_CANDIDATES)].copy()
    if out.empty:
        return out
    out["experiment_note"] = "PP-HCOEF33은 새 계수를 학습하지 않고 HCOEF32 후보를 확장 재검증"
    return out


def write_config() -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF32",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "focus_candidates": FOCUS_CANDIDATES,
        "n_repeats": N_REPEATS,
        "row_fractions": ROW_FRACTIONS,
        "artist_fractions": ARTIST_FRACTIONS,
        "selection_rule": "extended repeated row/artist validation first; fixed test and 0604 confirmation only",
        "no_new_candidate_generation": True,
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    repeated: pd.DataFrame,
    segment: pd.DataFrame,
    residuals: pd.DataFrame,
    coeffs: pd.DataFrame,
) -> str:
    selected_cols = [
        "candidate",
        "decision",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "repeated_min_any2_improve_prob",
        "repeated_min_all3_improve_prob",
        "repeated_mean_mean_delta_MdAPE_vs_stable",
        "repeated_mean_mean_delta_MAPE_vs_stable",
        "repeated_mean_mean_delta_p95_APE_vs_stable",
    ]
    selected_cols = [col for col in selected_cols if col in selected.columns]
    repeat_cols = [
        "source_scope",
        "validation_scheme",
        "candidate",
        "n_repeats",
        "all3_improve_prob",
        "any2_improve_prob",
        "MdAPE_improve_prob",
        "MAPE_improve_prob",
        "p95_improve_prob",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "worst_delta_p95_APE_vs_stable",
    ]
    metric_cols = ["scope", "split", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]
    metric_cols = [col for col in metric_cols if col in metrics.columns]

    top = selected[selected["candidate"].eq(H32_CONFIRM)]
    top_decision = top["decision"].iloc[0] if not top.empty else "확인 불가"
    top_any2 = top["repeated_min_any2_improve_prob"].iloc[0] if "repeated_min_any2_improve_prob" in top and not top.empty else np.nan
    top_all3 = top["repeated_min_all3_improve_prob"].iloc[0] if "repeated_min_all3_improve_prob" in top and not top.empty else np.nan

    md = "\n".join(
        [
            "# PP-HCOEF33 Warm Huber HCOEF32 extended validation",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF32의 tiny p95 개선 후보가 반복 split/artist-level split에서도 안정적인지 확장 검증.",
            "- 새 후보 생성 없음: HCOEF32 주요 후보만 좁혀서 재검증.",
            "- fixed test와 0604는 확인용이며, 후보 선택 기준으로 사용하지 않음.",
            "",
            "## 1. 실행 결론",
            "",
            f"- 핵심 확인 후보 `{H32_CONFIRM}` 판단: {top_decision}.",
            f"- 확장 반복 검증 min any2/all3: `{top_any2:.4f} / {top_all3:.4f}`.",
            "- 운영 후보 승격 기준은 repeated all3 `0.90` 이상, fixed/0604 p95 방어, fixed 2개 이상 개선.",
            "- 기준을 넘지 못하면 `hcoef_stable`을 현재 안정 후보로 유지하고 HCOEF32는 p95-first 확인 후보로만 관리.",
            "",
            "## 2. 검증 대상 후보",
            "",
            h24.md_table(pd.DataFrame({"candidate": FOCUS_CANDIDATES}), max_rows=20),
            "",
            "## 3. 후보별 판단 요약",
            "",
            h24.md_table(selected[selected_cols].round(6), max_rows=40),
            "",
            "## 4. Scope별 고정 지표",
            "",
            h24.md_table(metrics[metric_cols].round(6), max_rows=80),
            "",
            "## 5. 확장 반복 검증 요약",
            "",
            h24.md_table(
                repeated[repeat_cols].sort_values(["candidate", "source_scope", "validation_scheme"]).round(6),
                max_rows=120,
            ),
            "",
            "## 6. Segment별 영향",
            "",
            h24.md_table(
                segment.head(120).drop(columns=["abs_delta_sum"], errors="ignore").round(6),
                max_rows=120,
            ),
            "",
            "## 7. 계수/구간 해석",
            "",
            "- PP-HCOEF33은 새 계수를 학습하지 않음.",
            "- 아래 계수는 HCOEF32 후보가 사용한 방향 일치 segment 해석을 재첨부한 것.",
            "",
            h24.md_table(coeffs.round(6), max_rows=80),
            "",
            "## 8. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(6), max_rows=80),
            "",
            "## 9. 다음 방향",
            "",
            "- HCOEF32 확인 후보가 repeated all3 기준을 넘지 못하면 점 예측용 ultra-micro 이동은 운영 기본값으로 올리지 않음.",
            "- 다음 성능 개선은 fixed tiny improvement가 아니라 기준가 생성 방식 재탐색과 Huber 저차원 계수 재학습으로 이동.",
            "- 방향 일치 segment는 가격 범위, 신뢰도, 수동 검수 정책에서 재사용 가능.",
            "",
            "## 10. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/segment_impact.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    return md


def main() -> None:
    ensure_dirs()
    predictions = load_focus_predictions()
    metrics = point_metrics(predictions)
    detail, repeated = repeated_validation(predictions)
    selected = candidate_gate_summary(metrics, repeated)
    segment = segment_impact(predictions)
    residuals = residual_analysis(predictions, selected)
    coeffs = coefficient_summary()

    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "repeated_iteration_metrics.csv", index=False)
    repeated.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    segment.to_csv(EXP_DIR / "outputs" / "segment_impact.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    write_config()

    md = render_report(metrics, selected, repeated, segment, residuals, coeffs)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef33_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef33_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
