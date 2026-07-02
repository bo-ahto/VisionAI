#!/usr/bin/env python3
"""Run PP-HCOEF27: repeated split validation for HCOEF26 gated candidates.

HCOEF26 found low-risk fallback candidates that improved fixed-test MdAPE/MAPE
while keeping fixed-test p95 at the current stable candidate level. HCOEF27 does
not create a new point prediction formula. It audits whether the HCOEF26 signal
survives repeated row subsampling and artist holdout on validation OOF outputs.

The large HCOEF26 prediction file is read in chunks and filtered to a small,
predefined candidate set so this experiment remains reproducible without
duplicating a 2GB artifact.
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
from scripts.track6 import run_pp_hcoef26_warm_huber_price_basis_coefficient_refinement as h26


EXP_ID = "PP-HCOEF27"
EXP_SLUG = "PP-HCOEF27_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
H26_DIR = REPO / "experiments" / "track6" / "PP-HCOEF26_warm_huber_price_basis_coefficient_refinement"

BASELINE = h26.BASELINE
REFERENCE = h26.REFERENCE
PPV8 = h26.PPV8
SVC = h26.SVC
L10_COL = h26.L10_COL
SEED = 20260608
N_REPEATS = 500
ROW_FRACTION = 0.80
ARTIST_FRACTION = 0.80


PREDICTION_USECOLS = [
    "experiment_id",
    "scope",
    "split",
    "candidate",
    "method",
    "source_candidate",
    "mask_name",
    "mask_applied",
    "strength",
    "cap",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "actual_log",
    "actual_price",
    "pred_log",
    "pred_price",
    "policy_move_log",
    BASELINE,
    REFERENCE,
    PPV8,
    SVC,
    L10_COL,
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_coverage_tier",
    "svc_group_level",
    "service_confidence_tier",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "medium_support_bucket",
    "log_area",
    "hcoef23_risk_score",
    "hcoef23_risk_factor",
    "residual_log",
    "ape",
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    return h24.h20.metric_from_arrays(actual_price, actual_log, pred_log)


def select_candidate_set(validation_limit: int = 16, report_limit: int = 12) -> tuple[list[str], pd.DataFrame]:
    """Select candidates from HCOEF26 using validation ranking plus report-top audit candidates."""
    metrics = pd.read_csv(H26_DIR / "outputs" / "metrics.csv")
    selected = pd.read_csv(H26_DIR / "outputs" / "selected_candidates.csv")
    row = metrics[metrics["scope"].eq("validation_oof_row")].copy()
    artist = metrics[metrics["scope"].eq("validation_oof_artist")].copy()
    merged = row.merge(
        artist[["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "improve_count_vs_stable"]],
        on="candidate",
        suffixes=("_row", "_artist"),
    )
    merged = merged[~merged["method"].eq("source")].copy()
    merged = merged[(merged["improve_count_vs_stable_row"] >= 2) & (merged["improve_count_vs_stable_artist"] >= 2)].copy()
    merged["validation_score"] = (
        merged["delta_MdAPE_vs_stable_row"]
        + merged["delta_MAPE_vs_stable_row"]
        + merged["delta_p95_APE_vs_stable_row"]
        + merged["delta_MdAPE_vs_stable_artist"]
        + merged["delta_MAPE_vs_stable_artist"]
        + merged["delta_p95_APE_vs_stable_artist"]
    )
    validation_top = merged.sort_values(
        ["validation_score", "MAPE_row", "MAPE_artist", "MdAPE_row", "MdAPE_artist", "candidate"]
    )["candidate"].head(validation_limit).tolist()

    report_top = selected[
        ~selected["decision"].isin(["현재 기준 후보", "최소 비교 기준", "component 대조군", "보류"])
    ]["candidate"].head(report_limit).tolist()

    candidates = list(dict.fromkeys([BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket", *validation_top, *report_top]))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate": candidate,
                "selection_basis": (
                    "baseline_or_component"
                    if candidate in {BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket"}
                    else "validation_top"
                    if candidate in validation_top
                    else "hcoef26_report_top_audit"
                ),
            }
        )
    return candidates, pd.DataFrame(rows)


def load_prediction_subset(candidates: list[str]) -> pd.DataFrame:
    path = H26_DIR / "outputs" / "candidate_predictions.csv"
    chunks: list[pd.DataFrame] = []
    keep = set(candidates)
    for chunk in pd.read_csv(path, usecols=lambda c: c in set(PREDICTION_USECOLS), chunksize=200_000):
        filtered = chunk[chunk["candidate"].isin(keep)].copy()
        if not filtered.empty:
            chunks.append(filtered)
    if not chunks:
        raise RuntimeError("No HCOEF26 predictions found for selected candidates")
    out = pd.concat(chunks, ignore_index=True)
    out["experiment_id"] = EXP_ID
    return out


def point_metrics(predictions: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, group in predictions.groupby("scope", sort=False):
        stable = group[group["candidate"].eq(BASELINE)].sort_values("_track6_row_id")
        reference = group[group["candidate"].eq(REFERENCE)].sort_values("_track6_row_id")
        stable_m = metric_from_arrays(
            stable["actual_price"].to_numpy(dtype=float),
            stable["actual_log"].to_numpy(dtype=float),
            stable["pred_log"].to_numpy(dtype=float),
        )
        ref_m = metric_from_arrays(
            reference["actual_price"].to_numpy(dtype=float),
            reference["actual_log"].to_numpy(dtype=float),
            reference["pred_log"].to_numpy(dtype=float),
        )
        split = str(stable["split"].iloc[0])
        for candidate in candidates:
            cdf = group[group["candidate"].eq(candidate)].sort_values("_track6_row_id")
            if cdf.empty:
                continue
            pred = cdf["pred_log"].to_numpy(dtype=float)
            actual_price = cdf["actual_price"].to_numpy(dtype=float)
            actual_log = cdf["actual_log"].to_numpy(dtype=float)
            move = cdf["policy_move_log"].to_numpy(dtype=float)
            m = metric_from_arrays(actual_price, actual_log, pred)
            rows.append(
                h24.metric_row(
                    scope,
                    split,
                    candidate,
                    str(cdf["method"].iloc[0]),
                    len(cdf),
                    m,
                    stable_m,
                    ref_m,
                    move,
                )
                | {
                    "source_candidate": str(cdf.get("source_candidate", pd.Series([""])).iloc[0]),
                    "mask_name": str(cdf.get("mask_name", pd.Series([""])).iloc[0]),
                    "mask_applied_share": float(pd.to_numeric(cdf.get("mask_applied", pd.Series([1.0] * len(cdf))), errors="coerce").fillna(1.0).mean()),
                }
            )
    return pd.DataFrame(rows)


def repeated_validation(predictions: pd.DataFrame, candidates: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for source_scope in ["validation_oof_row", "validation_oof_artist"]:
        focus = predictions[predictions["scope"].eq(source_scope)].copy()
        if focus.empty:
            continue
        pivot = focus.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
        meta = focus.drop_duplicates("_track6_row_id").set_index("_track6_row_id")
        common = pivot.index[pivot[BASELINE].notna()]
        pivot = pivot.loc[common, [c for c in candidates if c in pivot.columns]]
        meta = meta.loc[common]
        actual_price = meta["actual_price"].to_numpy(dtype=float)
        actual_log = meta["actual_log"].to_numpy(dtype=float)
        artists = meta["artist_key"].astype(str).to_numpy()
        unique_artists = np.unique(artists)
        n_rows = len(pivot)
        row_size = max(30, int(n_rows * ROW_FRACTION))
        artist_size = max(5, int(len(unique_artists) * ARTIST_FRACTION))
        candidate_preds = {candidate: pivot[candidate].to_numpy(dtype=float) for candidate in pivot.columns}

        for scheme in ["row_subsample_80pct", "artist_holdout_80pct"]:
            for repeat in range(N_REPEATS):
                if scheme == "row_subsample_80pct":
                    idx = rng.choice(n_rows, size=row_size, replace=False)
                else:
                    chosen_artists = rng.choice(unique_artists, size=artist_size, replace=False)
                    idx = np.flatnonzero(np.isin(artists, chosen_artists))
                    if len(idx) < 30:
                        continue
                stable_m = metric_from_arrays(actual_price[idx], actual_log[idx], candidate_preds[BASELINE][idx])
                for candidate in pivot.columns:
                    pred = candidate_preds[candidate][idx]
                    m = metric_from_arrays(actual_price[idx], actual_log[idx], pred)
                    detail_rows.append(
                        {
                            "source_scope": source_scope,
                            "validation_scheme": scheme,
                            "repeat": repeat,
                            "candidate": candidate,
                            "n": len(idx),
                            "MdAPE": m["MdAPE"],
                            "MAPE": m["MAPE"],
                            "p95_APE": m["p95_APE"],
                            "RMSE_log": m["RMSE_log"],
                            "delta_MdAPE_vs_stable": m["MdAPE"] - stable_m["MdAPE"],
                            "delta_MAPE_vs_stable": m["MAPE"] - stable_m["MAPE"],
                            "delta_p95_APE_vs_stable": m["p95_APE"] - stable_m["p95_APE"],
                            "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_m["RMSE_log"],
                            "improve_count_vs_stable": int(m["MdAPE"] < stable_m["MdAPE"])
                            + int(m["MAPE"] < stable_m["MAPE"])
                            + int(m["p95_APE"] < stable_m["p95_APE"]),
                        }
                    )
    detail = pd.DataFrame(detail_rows)
    for (source_scope, scheme, candidate), group in detail.groupby(["source_scope", "validation_scheme", "candidate"], sort=False):
        d_md = group["delta_MdAPE_vs_stable"].to_numpy(dtype=float)
        d_ma = group["delta_MAPE_vs_stable"].to_numpy(dtype=float)
        d_p95 = group["delta_p95_APE_vs_stable"].to_numpy(dtype=float)
        d_rmse = group["delta_RMSE_log_vs_stable"].to_numpy(dtype=float)
        summary_rows.append(
            {
                "source_scope": source_scope,
                "validation_scheme": scheme,
                "candidate": candidate,
                "n_repeats": len(group),
                "mean_delta_MdAPE_vs_stable": float(np.mean(d_md)),
                "mean_delta_MAPE_vs_stable": float(np.mean(d_ma)),
                "mean_delta_p95_APE_vs_stable": float(np.mean(d_p95)),
                "mean_delta_RMSE_log_vs_stable": float(np.mean(d_rmse)),
                "median_delta_MdAPE_vs_stable": float(np.median(d_md)),
                "median_delta_MAPE_vs_stable": float(np.median(d_ma)),
                "median_delta_p95_APE_vs_stable": float(np.median(d_p95)),
                "q05_delta_MdAPE_vs_stable": float(np.quantile(d_md, 0.05)),
                "q95_delta_MdAPE_vs_stable": float(np.quantile(d_md, 0.95)),
                "q05_delta_MAPE_vs_stable": float(np.quantile(d_ma, 0.05)),
                "q95_delta_MAPE_vs_stable": float(np.quantile(d_ma, 0.95)),
                "q05_delta_p95_APE_vs_stable": float(np.quantile(d_p95, 0.05)),
                "q95_delta_p95_APE_vs_stable": float(np.quantile(d_p95, 0.95)),
                "MdAPE_improve_prob": float((d_md < 0).mean()),
                "MAPE_improve_prob": float((d_ma < 0).mean()),
                "p95_improve_prob": float((d_p95 < 0).mean()),
                "all3_improve_prob": float(((d_md < 0) & (d_ma < 0) & (d_p95 < 0)).mean()),
                "any2_improve_prob": float((((d_md < 0).astype(int) + (d_ma < 0).astype(int) + (d_p95 < 0).astype(int)) >= 2).mean()),
            }
        )
    return detail, pd.DataFrame(summary_rows)


def selected_table(metrics: pd.DataFrame, repeated: pd.DataFrame, selection_basis: pd.DataFrame) -> pd.DataFrame:
    def metric_slice(scope: str, prefix: str) -> pd.DataFrame:
        cols = ["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "improve_count_vs_stable", "mask_applied_share"]
        return metrics[metrics["scope"].eq(scope)][cols].rename(
            columns={
                "MdAPE": f"{prefix}_MdAPE",
                "MAPE": f"{prefix}_MAPE",
                "p95_APE": f"{prefix}_p95_APE",
                "RMSE_log": f"{prefix}_RMSE_log",
                "delta_MdAPE_vs_stable": f"{prefix}_delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable": f"{prefix}_delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable": f"{prefix}_delta_p95_APE_vs_stable",
                "improve_count_vs_stable": f"{prefix}_improve_count_vs_stable",
                "mask_applied_share": f"{prefix}_mask_applied_share",
            }
        )

    out = metric_slice("validation_oof_row", "row_oof")
    for scope, prefix in [
        ("validation_oof_artist", "artist_oof"),
        ("fixed_confirmation", "test"),
        ("0604_stress", "stress0604"),
    ]:
        out = out.merge(metric_slice(scope, prefix), on="candidate", how="left")

    prob = repeated.pivot_table(
        index="candidate",
        values=["all3_improve_prob", "any2_improve_prob", "MdAPE_improve_prob", "MAPE_improve_prob", "p95_improve_prob"],
        aggfunc=["min", "mean"],
    )
    prob.columns = [f"repeated_{stat}_{metric}" for stat, metric in prob.columns]
    out = out.merge(prob.reset_index(), on="candidate", how="left")
    out = out.merge(selection_basis, on="candidate", how="left")

    stable_test_p95 = out.loc[out["candidate"].eq(BASELINE), "test_p95_APE"].min()
    stable_0604_p95 = out.loc[out["candidate"].eq(BASELINE), "stress0604_p95_APE"].min()
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= stable_test_p95
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= stable_0604_p95
    out["fixed_test_2of3"] = out["test_improve_count_vs_stable"] >= 2
    out["repeated_any2_gate"] = out["repeated_min_any2_improve_prob"].fillna(0.0) >= 0.90
    out["repeated_all3_gate"] = out["repeated_min_all3_improve_prob"].fillna(0.0) >= 0.90
    out["decision"] = np.select(
        [
            out["candidate"].eq(BASELINE),
            out["candidate"].eq(REFERENCE),
            out["candidate"].isin([PPV8, SVC, "l10_seq_full_generated_bucket"]),
            out["repeated_all3_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            out["repeated_any2_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            (out["test_improve_count_vs_stable"] >= 2) & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"],
        ],
        ["현재 기준 후보", "최소 비교 기준", "component 대조군", "반복 검증 통과 후보", "반복 any2 검증 후보", "fixed 확인 후보"],
        default="보류",
    )
    order = {"현재 기준 후보": 0, "반복 검증 통과 후보": 1, "반복 any2 검증 후보": 2, "fixed 확인 후보": 3, "최소 비교 기준": 4, "component 대조군": 5, "보류": 6}
    out["decision_order"] = out["decision"].map(order).fillna(9)
    return out.sort_values(["decision_order", "test_MdAPE", "test_MAPE", "test_p95_APE", "candidate"]).drop(columns=["decision_order"])


def feature_coefficients(predictions: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    focus = selected.head(25)["candidate"].tolist()
    rows: list[dict[str, Any]] = []
    for candidate in focus:
        cdf = predictions[predictions["candidate"].eq(candidate)]
        if cdf.empty:
            continue
        first = cdf.iloc[0]
        rows.append(
            {
                "candidate": candidate,
                "method": first.get("method", ""),
                "source_candidate": first.get("source_candidate", ""),
                "mask_name": first.get("mask_name", ""),
                "strength": first.get("strength", np.nan),
                "cap": first.get("cap", np.nan),
                "mean_mask_applied": float(pd.to_numeric(cdf.get("mask_applied", pd.Series([1.0] * len(cdf))), errors="coerce").fillna(1.0).mean()),
                "mean_abs_move_log": float(pd.to_numeric(cdf["policy_move_log"], errors="coerce").abs().mean()),
                "interpretation": "HCOEF26 후보 이동분을 해당 mask 구간에만 적용하고 나머지는 hcoef_stable로 fallback하는 정책.",
            }
        )
    return pd.DataFrame(rows)


def residual_analysis(predictions: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    focus = list(dict.fromkeys([BASELINE, REFERENCE, *selected.head(15)["candidate"].tolist()]))
    return h24.residual_analysis(predictions[predictions["candidate"].isin(focus)].copy(), focus)


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    residuals: pd.DataFrame,
    coeffs: pd.DataFrame,
    selection_basis: pd.DataFrame,
) -> None:
    base = selected[selected["candidate"].eq(BASELINE)].iloc[0]
    non_base = selected[~selected["decision"].isin(["현재 기준 후보", "최소 비교 기준", "component 대조군", "보류"])].copy()
    if non_base.empty:
        best_line = "반복 검증 기준을 통과한 새 후보 없음. `hcoef_stable` 유지."
    else:
        best = non_base.iloc[0]
        best_line = (
            f"상위 재검증 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test `{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`, "
            f"repeated min any2 `{best['repeated_min_any2_improve_prob']:.4f}`, min all3 `{best['repeated_min_all3_improve_prob']:.4f}`)."
        )

    selected_cols = [
        "candidate",
        "selection_basis",
        "decision",
        "row_oof_MdAPE",
        "row_oof_MAPE",
        "row_oof_p95_APE",
        "artist_oof_MdAPE",
        "artist_oof_MAPE",
        "artist_oof_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "repeated_min_any2_improve_prob",
        "repeated_min_all3_improve_prob",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
    ]
    metric_cols = ["scope", "candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "mask_applied_share"]
    repeat_cols = [
        "source_scope",
        "validation_scheme",
        "candidate",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "MdAPE_improve_prob",
        "MAPE_improve_prob",
        "p95_improve_prob",
        "any2_improve_prob",
        "all3_improve_prob",
    ]

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber HCOEF26 반복 split/artist holdout 재검증",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF26 low-risk fallback 후보가 validation 반복 표본에서도 안정적인지 확인.",
            "- 새 보정식 생성 여부: 없음. HCOEF26 후보 예측값을 재사용해 반복 검증만 수행.",
            "- 후보 선택 기준: validation OOF 상위 후보 + HCOEF26 보고서 상위 후보를 분리 기록.",
            "- fixed test와 0604는 후보 경계값 선택에 사용하지 않고 확인 지표로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 기준 후보 `hcoef_stable` fixed test: `{base['test_MdAPE']:.4f}/{base['test_MAPE']:.4f}/{base['test_p95_APE']:.4f}`.",
            "- HCOEF27에서 반복 all3 gate를 통과하지 못하면 HCOEF26은 운영 기본 후보가 아니라 MAPE/MdAPE 연구 후보로 유지.",
            "",
            "## 2. 후보 선택 근거",
            "",
            h24.md_table(selection_basis, max_rows=40),
            "",
            "## 3. 최종 선택표",
            "",
            h24.md_table(selected[selected_cols].round(4), max_rows=40),
            "",
            "## 4. Scope별 point metrics",
            "",
            h24.md_table(metrics[metric_cols].round(4), max_rows=80),
            "",
            "## 5. 반복 split/artist holdout 요약",
            "",
            h24.md_table(repeated_summary[repeat_cols].round(4).sort_values(["source_scope", "validation_scheme", "any2_improve_prob", "all3_improve_prob"], ascending=[True, True, False, False]), max_rows=120),
            "",
            "## 6. 정책/계수 해석",
            "",
            "- HCOEF27의 계수는 새로 학습된 Huber 계수가 아니라 HCOEF26 정책 가중치와 적용 mask를 의미함.",
            "- `mask_name`은 HCOEF25 후보 이동분을 적용할 수 있는 구간임.",
            "- mask를 만족하지 않는 행은 `hcoef_stable`로 fallback하므로 큰 오차 악화를 줄이는 구조임.",
            "",
            h24.md_table(coeffs.round(5), max_rows=60),
            "",
            "## 7. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=90),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef27_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef27_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(candidates: list[str]) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF26",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "candidate_count": len(candidates),
        "n_repeats": N_REPEATS,
        "row_fraction": ROW_FRACTION,
        "artist_fraction": ARTIST_FRACTION,
        "selection_rule": "validation OOF top candidates plus HCOEF26 report-top audit candidates; no new threshold from fixed test or 0604",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    candidates, basis = select_candidate_set()
    predictions = load_prediction_subset(candidates)
    metrics = point_metrics(predictions, candidates)
    detail, repeated = repeated_validation(predictions, candidates)
    selected = selected_table(metrics, repeated, basis)
    coeffs = feature_coefficients(predictions, selected)
    residuals = residual_analysis(predictions, selected)

    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coeffs.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "repeated_iteration_metrics.csv", index=False)
    repeated.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    basis.to_csv(EXP_DIR / "outputs" / "candidate_selection_basis.csv", index=False)
    write_config(candidates)
    write_report(metrics, selected, repeated, residuals, coeffs, basis)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
