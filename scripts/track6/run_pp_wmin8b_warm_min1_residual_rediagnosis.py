#!/usr/bin/env python3
"""Run PP-WMIN8B: residual re-diagnosis and segment correction after WMIN8.

The original WMIN objective reserved PP-WMIN8 for a HCOEF23-style residual
diagnosis and correction-stack rebuild.  The earlier PP-WMIN8 run selected a
useful weight router.  This follow-up keeps that router intact and audits the
remaining residuals on top of it.

Selection rule:
- segment maps and thresholds are derived from validation OOF only.
- fixed test is confirmation only.
- 0604 is not used.
- validation corrections are artist-excluded OOF medians, so a row does not use
  residuals from the same artist when deriving its validation correction.
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
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor
from sklearn.preprocessing import StandardScaler
import warnings


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wmin4_warm_min1_operational_decision as wmin4  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN8B"
EXP_SLUG = "PP-WMIN8B_warm_min1_residual_rediagnosis"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin8b_warm_min1_residual_rediagnosis_summary.md"

SOURCE_PREDS = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router" / "outputs" / "candidate_predictions.csv"
SOURCE_GATE = REPO / "experiments" / "track6" / "PP-WMIN8_warm_min1_weight_router" / "outputs" / "gate_audit.csv"
WMIN7_PREDS = REPO / "experiments" / "track6" / "PP-WMIN7_warm_min1_weight_retuning" / "outputs" / "candidate_predictions.csv"

PP258_REFERENCE = "current_pp258_operational_reference"
WMIN4_SELECTED = "min1_huber_refit_partial"
WMIN8_SELECTED = "min1_route_w850_risk_q50_altlower_gap005"
WMIN8_ALT = "min1_w850_huber_refit_partial"

MIN_SEGMENT_ROWS = [20, 35, 50]
CAPS = [0.0025, 0.005, 0.01, 0.02]
STRENGTHS = [0.20, 0.35, 0.50]
RISK_QS = [None, 0.50, 0.60, 0.70]
SEGMENT_SETS = {
    "confidence": ["confidence_tier"],
    "svc_level": ["svc_group_level"],
    "svc_n_band": ["svc_group_n_band"],
    "qwidth_band": ["qwidth_band"],
    "spread_band": ["spread_band"],
    "price_band": ["stable_price_band"],
    "route_flag": ["wmin8_route_flag"],
    "price_qwidth": ["stable_price_band", "qwidth_band"],
    "svc_conf": ["svc_group_level", "confidence_tier"],
}
NUMERIC_FEATURES = [
    "quantile_width",
    "component_prediction_spread",
    "current_vs_stable_gap_abs",
    "svc_group_n",
    "risk_score",
    "wmin8_alt_gap_abs",
]
CATEGORICAL_FEATURES = [
    "confidence_tier",
    "stable_price_band",
    "svc_group_level",
    "svc_coverage_tier",
    "svc_group_n_band",
    "qwidth_band",
    "spread_band",
    "gap_band",
    "wmin8_route_flag",
]


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def fmt(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(c) for c in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in view.columns) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def table_html(frame: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if frame.empty:
        return "<p><em>결과 없음</em></p>"
    view = frame[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(fmt(row[c]))}</td>" for c in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def band_by_validation_quantiles(all_values: pd.Series, validation_values: pd.Series, prefix: str) -> pd.Series:
    values = pd.to_numeric(validation_values, errors="coerce").dropna()
    if values.nunique() < 4:
        return pd.Series([f"{prefix}_unknown"] * len(all_values), index=all_values.index)
    qs = np.unique(np.nanquantile(values, [0.0, 0.25, 0.50, 0.75, 1.0]))
    if len(qs) < 4:
        return pd.Series([f"{prefix}_unknown"] * len(all_values), index=all_values.index)
    labels = [f"{prefix}_q{i + 1}" for i in range(len(qs) - 1)]
    return pd.cut(
        pd.to_numeric(all_values, errors="coerce"),
        bins=qs,
        labels=labels,
        include_lowest=True,
        duplicates="drop",
    ).astype("object").fillna(f"{prefix}_unknown")


def load_source_predictions() -> pd.DataFrame:
    df = pd.read_csv(SOURCE_PREDS, low_memory=False)
    if WMIN8_ALT not in set(df["candidate_label"].dropna().astype(str)):
        wmin7 = pd.read_csv(WMIN7_PREDS, low_memory=False)
        alt_rows = wmin7[wmin7["candidate_label"].eq(WMIN8_ALT)].copy()
        if alt_rows.empty:
            raise RuntimeError(f"missing WMIN7 alt candidate: {WMIN8_ALT}")
        df = pd.concat([df, alt_rows], ignore_index=True, sort=False)
    needed = {PP258_REFERENCE, WMIN4_SELECTED, WMIN8_SELECTED, WMIN8_ALT}
    missing = needed - set(df["candidate_label"].dropna().astype(str))
    if missing:
        raise RuntimeError(f"missing source candidates: {sorted(missing)}")
    df = df[df["candidate_label"].isin(needed)].copy()

    wide = df.pivot_table(
        index=["eval_split", "_track6_row_id"],
        columns="candidate_label",
        values="pred_log",
        aggfunc="first",
    ).reset_index()
    wide["wmin8_alt_gap_abs"] = (wide[WMIN8_ALT] - wide[WMIN4_SELECTED]).abs()
    wide["wmin8_route_flag"] = np.where(
        (wide[WMIN8_SELECTED] - wide[WMIN8_ALT]).abs() <= (wide[WMIN8_SELECTED] - wide[WMIN4_SELECTED]).abs(),
        "routed_to_alt",
        "kept_base",
    )
    df = df.merge(
        wide[["eval_split", "_track6_row_id", "wmin8_alt_gap_abs", "wmin8_route_flag"]],
        on=["eval_split", "_track6_row_id"],
        how="left",
    )
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["quantile_width", "component_prediction_spread", "current_vs_stable_gap_abs", "svc_group_n", "actual_log", "actual_price", "pred_log"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    reference = out[out["candidate_label"].eq(PP258_REFERENCE)].copy()
    validation_ref = reference[reference["eval_split"].eq("validation_oof")]
    out["risk_score"] = wmin4.risk_score(out)
    out["qwidth_band"] = band_by_validation_quantiles(out["quantile_width"], validation_ref["quantile_width"], "qwidth")
    out["spread_band"] = band_by_validation_quantiles(out["component_prediction_spread"], validation_ref["component_prediction_spread"], "spread")
    out["gap_band"] = band_by_validation_quantiles(out["current_vs_stable_gap_abs"], validation_ref["current_vs_stable_gap_abs"], "gap")
    out["svc_group_n_band"] = pd.cut(
        pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0),
        bins=[-np.inf, 1, 2, 4, 9, 19, np.inf],
        labels=["n0_1", "n2", "n3_4", "n5_9", "n10_19", "n20_plus"],
    ).astype("object").fillna("n_missing")
    for col in CATEGORICAL_FEATURES:
        out[col] = out[col].astype("object").where(out[col].notna(), "missing")
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(np.exp(np.clip(out["pred_log"], -50, 50)) - out["actual_price"]) / np.maximum(out["actual_price"], 1.0)
    out["over_50pct_error"] = out["ape"] > 0.50
    out["over_100pct_error"] = out["ape"] > 1.00
    return out


def selected_base_frame(df: pd.DataFrame, label: str = WMIN8_SELECTED) -> pd.DataFrame:
    base = df[df["candidate_label"].eq(label)].copy()
    return base.sort_values(["eval_split", "_track6_row_id"]).reset_index(drop=True)


def segment_key(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    return frame[cols].astype(str).agg("|".join, axis=1)


def residual_map(validation: pd.DataFrame, cols: list[str], min_rows: int) -> tuple[dict[str, float], float, dict[str, int]]:
    work = validation.copy()
    work["_segment_key"] = segment_key(work, cols)
    stats = work.groupby("_segment_key")["residual_log"].agg(["size", "median"]).reset_index()
    mapping = {
        str(row["_segment_key"]): float(row["median"])
        for _, row in stats.iterrows()
        if int(row["size"]) >= min_rows and np.isfinite(float(row["median"]))
    }
    counts = {str(row["_segment_key"]): int(row["size"]) for _, row in stats.iterrows()}
    global_median = float(np.nanmedian(work["residual_log"]))
    if not np.isfinite(global_median):
        global_median = 0.0
    return mapping, global_median, counts


def validation_oof_segment_correction(validation: pd.DataFrame, cols: list[str], min_rows: int) -> np.ndarray:
    keys = segment_key(validation, cols).to_numpy()
    artists = validation["artist_key"].fillna("__missing_artist__").astype(str).to_numpy()
    residuals = validation["residual_log"].to_numpy(dtype=float)
    corrections = np.zeros(len(validation), dtype=float)
    for i, key in enumerate(keys):
        mask_artist_excluded = artists != artists[i]
        seg_mask = (keys == key) & mask_artist_excluded & np.isfinite(residuals)
        if int(seg_mask.sum()) >= min_rows:
            corr = float(np.nanmedian(residuals[seg_mask]))
        else:
            fallback_mask = mask_artist_excluded & np.isfinite(residuals)
            corr = float(np.nanmedian(residuals[fallback_mask])) if fallback_mask.any() else 0.0
        corrections[i] = corr if np.isfinite(corr) else 0.0
    return corrections


def apply_segment_candidate(
    base: pd.DataFrame,
    validation: pd.DataFrame,
    segment_name: str,
    cols: list[str],
    min_rows: int,
    cap: float,
    strength: float,
    risk_q: float | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    label_parts = [
        "min1_wmin8b",
        f"seg_{segment_name}",
        f"min{min_rows}",
        f"cap{str(cap).replace('.', 'p')}",
        f"s{str(strength).replace('.', 'p')}",
    ]
    if risk_q is not None:
        label_parts.append(f"riskq{int(risk_q * 100)}")
    candidate_label = "_".join(label_parts)

    val = base[base["eval_split"].eq("validation_oof")].copy()
    test = base[base["eval_split"].eq("test")].copy()
    val_corr_raw = validation_oof_segment_correction(val, cols, min_rows)
    mapping, global_median, counts = residual_map(validation, cols, min_rows)

    def _correct(frame: pd.DataFrame, raw: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        if raw is None:
            keys = segment_key(frame, cols)
            raw_corr = keys.map(mapping).fillna(global_median).to_numpy(dtype=float)
        else:
            raw_corr = raw
        if risk_q is None:
            mask = np.ones(len(frame), dtype=bool)
        else:
            threshold = float(np.nanquantile(validation["risk_score"], risk_q))
            mask = frame["risk_score"].to_numpy(dtype=float) >= threshold
        applied = np.where(mask, np.clip(strength * raw_corr, -cap, cap), 0.0)
        return frame["pred_log"].to_numpy(dtype=float) + applied, applied

    val_pred, val_applied = _correct(val, val_corr_raw)
    test_pred, test_applied = _correct(test)
    out = pd.concat([
        make_candidate_rows(val, candidate_label, val_pred, val_applied, segment_name, min_rows, cap, strength, risk_q),
        make_candidate_rows(test, candidate_label, test_pred, test_applied, segment_name, min_rows, cap, strength, risk_q),
    ], ignore_index=True)
    info = {
        "candidate_label": candidate_label,
        "segment_name": segment_name,
        "segment_cols": ",".join(cols),
        "min_rows": min_rows,
        "cap": cap,
        "strength": strength,
        "risk_q": risk_q,
        "usable_segment_count": len(mapping),
        "global_median_residual": global_median,
        "validation_mean_abs_applied": float(np.mean(np.abs(val_applied))),
        "test_mean_abs_applied": float(np.mean(np.abs(test_applied))),
        "max_segment_count": max(counts.values()) if counts else 0,
    }
    return out, info


def make_candidate_rows(
    frame: pd.DataFrame,
    candidate_label: str,
    pred_log: np.ndarray,
    applied: np.ndarray,
    segment_name: str,
    min_rows: int,
    cap: float,
    strength: float,
    risk_q: float | None,
) -> pd.DataFrame:
    out = frame.copy()
    out["candidate_label"] = candidate_label
    out["candidate"] = candidate_label
    out["family"] = "wmin8b_residual_rediagnosis"
    out["item_id"] = EXP_ID
    out["source_experiment"] = EXP_ID
    out["method"] = "artist_excluded_validation_segment_residual_correction"
    out["pred_log"] = pred_log
    out["pred_price"] = np.exp(np.clip(pred_log, -50, 50))
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.maximum(out["actual_price"], 1.0)
    out["segment_name"] = segment_name
    out["segment_min_rows"] = min_rows
    out["correction_cap"] = cap
    out["correction_strength"] = strength
    out["risk_q"] = "" if risk_q is None else risk_q
    out["applied_correction_log"] = applied
    return out


def build_candidates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    baselines = df[df["candidate_label"].isin([PP258_REFERENCE, WMIN4_SELECTED, WMIN8_SELECTED, WMIN8_ALT])].copy()
    base = selected_base_frame(df, WMIN8_SELECTED)
    validation = base[base["eval_split"].eq("validation_oof")].copy()
    rows: list[pd.DataFrame] = [baselines]
    infos: list[dict[str, Any]] = []
    for segment_name, cols in SEGMENT_SETS.items():
        for min_rows in MIN_SEGMENT_ROWS:
            for cap in CAPS:
                for strength in STRENGTHS:
                    for risk_q in RISK_QS:
                        cand, info = apply_segment_candidate(base, validation, segment_name, cols, min_rows, cap, strength, risk_q)
                        rows.append(cand)
                        infos.append(info)
    return pd.concat(rows, ignore_index=True), pd.DataFrame(infos)


def segment_residual_analysis(base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, split_df in base.groupby("eval_split", dropna=False):
        overall_m = wmin4.metrics_from_arrays(
            split_df["actual_log"].to_numpy(dtype=float),
            split_df["actual_price"].to_numpy(dtype=float),
            split_df["pred_log"].to_numpy(dtype=float),
        )
        for segment_name, cols in SEGMENT_SETS.items():
            work = split_df.copy()
            work["_segment_key"] = segment_key(work, cols)
            for key, group in work.groupby("_segment_key", dropna=False):
                if len(group) < 12:
                    continue
                m = wmin4.metrics_from_arrays(
                    group["actual_log"].to_numpy(dtype=float),
                    group["actual_price"].to_numpy(dtype=float),
                    group["pred_log"].to_numpy(dtype=float),
                )
                rows.append({
                    "eval_split": split,
                    "segment_name": segment_name,
                    "segment_cols": ",".join(cols),
                    "segment_value": key,
                    "n": len(group),
                    **m,
                    "delta_MAPE_vs_overall": m["MAPE"] - overall_m["MAPE"],
                    "delta_p95_vs_overall": m["p95_APE"] - overall_m["p95_APE"],
                    "median_residual_log": float(np.nanmedian(group["residual_log"])),
                    "over_50pct_error_rate": float(np.nanmean(group["ape"] > 0.50)),
                    "risk_rank_score": float(max(m["MAPE"] - overall_m["MAPE"], 0) + 0.5 * max(m["p95_APE"] - overall_m["p95_APE"], 0)),
                })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["eval_split", "risk_rank_score"], ascending=[True, False]).reset_index(drop=True)


def coefficient_audit(base: pd.DataFrame) -> pd.DataFrame:
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
    rows: list[dict[str, Any]] = []
    val = base[base["eval_split"].eq("validation_oof")].copy()
    val = val.dropna(subset=["actual_log", "pred_log", "residual_log"])
    if len(val) < 50:
        return pd.DataFrame()
    numeric = val[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.fillna(numeric.median(numeric_only=True)).fillna(0.0)
    cats = pd.get_dummies(val[CATEGORICAL_FEATURES].fillna("missing").astype(str), drop_first=True)
    design = pd.concat([numeric, cats], axis=1)
    design = design.loc[:, design.nunique(dropna=False) > 1]
    x = StandardScaler().fit_transform(design)
    targets = {
        "signed_residual_log": val["residual_log"].to_numpy(dtype=float),
        "abs_residual_log": val["residual_log"].abs().to_numpy(dtype=float),
    }
    for target_name, y in targets.items():
        model = HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=5000)
        model.fit(x, y)
        for feature, coef in zip(design.columns, model.coef_, strict=False):
            rows.append({
                "target": target_name,
                "feature": feature,
                "standardized_coefficient": float(coef),
                "abs_standardized_coefficient": float(abs(coef)),
                "direction": (
                    "실제>예측 방향" if target_name == "signed_residual_log" and coef > 0
                    else "예측>실제 방향" if target_name == "signed_residual_log"
                    else "오차위험 증가" if coef > 0
                    else "오차위험 감소"
                ),
            })
    out = pd.DataFrame(rows)
    return out.sort_values(["target", "abs_standardized_coefficient"], ascending=[True, False]).reset_index(drop=True)


def compare_vs_wmin8(fixed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation_oof", "test"]:
        base = fixed[(fixed["eval_split"].eq(split)) & (fixed["candidate_label"].eq(WMIN8_SELECTED))]
        if base.empty:
            continue
        b = base.iloc[0]
        for _, row in fixed[fixed["eval_split"].eq(split)].iterrows():
            rows.append({
                "candidate_label": row["candidate_label"],
                "eval_split": split,
                "delta_MdAPE_vs_wmin8_selected": row["MdAPE"] - b["MdAPE"],
                "delta_MAPE_vs_wmin8_selected": row["MAPE"] - b["MAPE"],
                "delta_p95_APE_vs_wmin8_selected": row["p95_APE"] - b["p95_APE"],
                "delta_RMSE_log_vs_wmin8_selected": row["RMSE_log"] - b["RMSE_log"],
            })
    return pd.DataFrame(rows)


def choose_decision(aggregate: pd.DataFrame, comp: pd.DataFrame) -> dict[str, Any]:
    candidate_pool = aggregate[aggregate["candidate_label"].str.startswith("min1_wmin8b_", na=False)].copy()
    if candidate_pool.empty:
        return {"decision_status": "hold", "selected_candidate_label": WMIN8_SELECTED, "reason": "생성된 보정 후보 없음"}
    gated = candidate_pool[candidate_pool["passes_validation_gate"]].copy()
    if gated.empty:
        selected = candidate_pool.sort_values(["validation_replacement_score", "fixed_validation_MAPE"]).iloc[0]
        return {
            "decision_status": "hold",
            "selected_candidate_label": WMIN8_SELECTED,
            "best_screened_candidate": selected["candidate_label"],
            "reason": "validation gate를 통과한 잔차 보정 후보가 없어 WMIN8 선택 후보 유지",
        }
    selected = gated.sort_values(
        ["validation_replacement_score", "fixed_validation_MAPE", "validation_avg_p95_win_rate"],
        ascending=[True, True, False],
    ).iloc[0]
    test_delta = comp[(comp["candidate_label"].eq(selected["candidate_label"])) & (comp["eval_split"].eq("test"))]
    improves_wmin8 = False
    if not test_delta.empty:
        d = test_delta.iloc[0]
        improves_wmin8 = (
            d["delta_MAPE_vs_wmin8_selected"] <= 0
            and d["delta_p95_APE_vs_wmin8_selected"] <= 0
            and d["delta_MdAPE_vs_wmin8_selected"] <= 0
        )
    status = "adopt_candidate" if bool(selected["passes_fixed_confirmation"]) and improves_wmin8 else "validation_pass_fixed_hold"
    reason = (
        "validation gate와 fixed test에서 PP258 및 WMIN8 대비 all-metric 개선"
        if status == "adopt_candidate"
        else "validation gate는 통과했지만 fixed test에서 WMIN8 대비 일부 지표 trade-off가 있어 보류"
    )
    return {
        "decision_status": status,
        "selected_candidate_label": selected["candidate_label"] if status == "adopt_candidate" else WMIN8_SELECTED,
        "best_screened_candidate": selected["candidate_label"],
        "reason": reason,
        "selected_fixed_validation_MdAPE": float(selected["fixed_validation_MdAPE"]),
        "selected_fixed_validation_MAPE": float(selected["fixed_validation_MAPE"]),
        "selected_fixed_validation_p95_APE": float(selected["fixed_validation_p95_APE"]),
        "selected_fixed_test_MdAPE": float(selected["fixed_test_MdAPE"]),
        "selected_fixed_test_MAPE": float(selected["fixed_test_MAPE"]),
        "selected_fixed_test_p95_APE": float(selected["fixed_test_p95_APE"]),
        "selected_validation_MAPE_win_rate": float(selected["validation_avg_MAPE_win_rate"]),
        "selected_validation_p95_win_rate": float(selected["validation_avg_p95_win_rate"]),
        "selected_validation_replacement_score": float(selected["validation_replacement_score"]),
    }


def render_reports(
    fixed: pd.DataFrame,
    aggregate: pd.DataFrame,
    decision: dict[str, Any],
    comp: pd.DataFrame,
    residual_segments: pd.DataFrame,
    coefficients: pd.DataFrame,
    correction_info: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[str, str]:
    agg_cols = [
        "candidate_label",
        "passes_validation_gate",
        "passes_fixed_confirmation",
        "fixed_validation_MdAPE",
        "fixed_validation_MAPE",
        "fixed_validation_p95_APE",
        "validation_avg_MAPE_win_rate",
        "validation_avg_p95_win_rate",
        "validation_replacement_score",
        "fixed_test_MdAPE",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
    ]
    fixed_cols = ["candidate_label", "eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    comp_cols = ["candidate_label", "eval_split", "delta_MdAPE_vs_wmin8_selected", "delta_MAPE_vs_wmin8_selected", "delta_p95_APE_vs_wmin8_selected"]
    seg_cols = ["eval_split", "segment_name", "segment_value", "n", "MAPE", "p95_APE", "delta_MAPE_vs_overall", "delta_p95_vs_overall", "median_residual_log", "over_50pct_error_rate"]
    coef_cols = ["target", "feature", "standardized_coefficient", "direction"]
    info_cols = ["candidate_label", "segment_name", "min_rows", "cap", "strength", "risk_q", "usable_segment_count", "validation_mean_abs_applied", "test_mean_abs_applied"]

    md = "\n".join([
        "# PP-WMIN8B Warm min1 잔차 재진단 및 보정 스택 재구축",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건",
        "- 선택 기준: validation OOF에서 생성한 segment 보정 후보 + WMIN4 decision layer",
        "- fixed test: 확인용",
        "- 0604: 사용하지 않음",
        f"- 결론: {decision['decision_status']} / `{decision['selected_candidate_label']}`",
        f"- 판단 근거: {decision['reason']}",
        "",
        "## 1. 후보별 교체 판단",
        markdown_table(aggregate, agg_cols, 80),
        "",
        "## 2. WMIN8 선택 후보 대비 변화량",
        markdown_table(comp.sort_values(["eval_split", "delta_MAPE_vs_wmin8_selected"]), comp_cols, 120),
        "",
        "## 3. fixed validation/test 지표",
        markdown_table(fixed, fixed_cols, 100),
        "",
        "## 4. 잔차 위험 구간",
        markdown_table(residual_segments, seg_cols, 80),
        "",
        "## 5. Huber 계수 감사",
        markdown_table(coefficients, coef_cols, 50),
        "",
        "## 6. 보정 후보 설정",
        markdown_table(correction_info.sort_values(["validation_mean_abs_applied", "test_mean_abs_applied"], ascending=[False, False]), info_cols, 80),
        "",
        "## 7. 실행 설정",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
    ])
    html_report = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-WMIN8B Warm min1 residual re-diagnosis</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin: 12px 0 28px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    h1 {{ font-size: 26px; }} h2 {{ margin-top: 28px; border-top: 1px solid #d1d5db; padding-top: 16px; }}
  </style>
</head>
<body>
<h1>PP-WMIN8B Warm min1 잔차 재진단 및 보정 스택 재구축</h1>
<p>결론: {html.escape(str(decision['decision_status']))} / <code>{html.escape(str(decision['selected_candidate_label']))}</code></p>
<p>{html.escape(str(decision['reason']))}</p>
<h2>1. 후보별 교체 판단</h2>{table_html(aggregate, agg_cols, 80)}
<h2>2. WMIN8 선택 후보 대비 변화량</h2>{table_html(comp.sort_values(['eval_split', 'delta_MAPE_vs_wmin8_selected']), comp_cols, 120)}
<h2>3. fixed validation/test 지표</h2>{table_html(fixed, fixed_cols, 100)}
<h2>4. 잔차 위험 구간</h2>{table_html(residual_segments, seg_cols, 80)}
<h2>5. Huber 계수 감사</h2>{table_html(coefficients, coef_cols, 50)}
<h2>6. 보정 후보 설정</h2>{table_html(correction_info.sort_values(['validation_mean_abs_applied', 'test_mean_abs_applied'], ascending=[False, False]), info_cols, 80)}
</body>
</html>"""
    return md, html_report


def main() -> None:
    ensure_dirs()
    source = load_source_predictions()
    candidates, correction_info = build_candidates(source)
    fixed = wmin4.fixed_metrics(candidates)
    repeated_detail, repeated_summary = wmin4.repeated_validation_metrics(candidates)
    aggregate = wmin4.aggregate_decision(fixed, repeated_summary)
    comp = compare_vs_wmin8(fixed)
    decision = choose_decision(aggregate, comp)
    base = selected_base_frame(source, WMIN8_SELECTED)
    residual_segments = segment_residual_analysis(base)
    coefficients = coefficient_audit(base)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_predictions": str(SOURCE_PREDS.relative_to(REPO)),
        "source_gate_audit": str(SOURCE_GATE.relative_to(REPO)),
        "reference_candidate_label": PP258_REFERENCE,
        "wmin4_selected_candidate_label": WMIN4_SELECTED,
        "wmin8_selected_candidate_label": WMIN8_SELECTED,
        "candidate_count": int(candidates["candidate_label"].nunique()),
        "segment_sets": SEGMENT_SETS,
        "min_segment_rows": MIN_SEGMENT_ROWS,
        "caps": CAPS,
        "strengths": STRENGTHS,
        "risk_quantiles": RISK_QS,
        "selection_policy": "validation OOF segment corrections only; fixed test confirmation; 0604 not used",
        "decision": decision,
    }

    md, html_report = render_reports(fixed, aggregate, decision, comp, residual_segments, coefficients, correction_info, config)
    candidates.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    fixed.to_csv(OUT_DIR / "fixed_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "operational_decision_aggregate.csv", index=False)
    comp.to_csv(OUT_DIR / "comparison_vs_wmin8_selected.csv", index=False)
    residual_segments.to_csv(OUT_DIR / "residual_segment_analysis.csv", index=False)
    coefficients.to_csv(OUT_DIR / "feature_coefficient_audit.csv", index=False)
    correction_info.to_csv(OUT_DIR / "correction_candidate_config.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_report, encoding="utf-8")
    DOC_SUMMARY.write_text(md, encoding="utf-8")
    print(json.dumps({
        "experiment_id": EXP_ID,
        "decision": decision,
        "candidate_count": config["candidate_count"],
        "report": str((REPORT_DIR / "result_report.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
