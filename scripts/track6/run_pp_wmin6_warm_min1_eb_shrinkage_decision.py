#!/usr/bin/env python3
"""Run PP-WMIN6: EB-shrunk min1 SVC + Warm decision validation.

PP-WMIN5 confirmed that the WMIN4 selected min1 candidate is safe on the 0604
stress set.  PP-WMIN6 returns to the normal Warm validation/fixed-test protocol
and checks whether empirical-Bayes shrinkage of the min1 comparable median can
improve the selected WMIN4 path.

Selection uses validation only through the existing WMIN4 decision layer.
Fixed test is recorded as confirmation.  The 0604 stress set is not used here.
"""
from __future__ import annotations

import html
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
import run_pp_svcshrink1_warm_comparable_prior_shrinkage as shrink1  # noqa: E402
import run_pp_wmin2_warm_artist_min1_svc_numeric as wmin2  # noqa: E402
import run_pp_wmin3_warm_min1_hcoef_refit as wmin3  # noqa: E402
import run_pp_wmin4_warm_min1_operational_decision as wmin4  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN6"
EXP_SLUG = "PP-WMIN6_warm_min1_eb_shrinkage_decision"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"
DOC_SUMMARY = REPO / "docs" / "track6" / "experiments" / "pp_wmin6_warm_min1_eb_shrinkage_decision_summary.md"

K_GRID = [2, 5, 10, 20, 50]
SEEDS = wmin2.SEEDS
MEDIAN_COL = "svc_group_log_price_median"
WMIN4_SELECTED = "min1_huber_refit_partial"
PP258_REFERENCE = "current_pp258_operational_reference"
PPV8 = wmin2.PPV8


def ensure_dirs() -> None:
    for path in [EXP_DIR, OUT_DIR, REPORT_DIR, ARTIFACT_DIR, DOC_SUMMARY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.exp(np.asarray(values, dtype=float)), 1_000.0, None)


def format_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, cols: list[str] | None = None, max_rows: int = 80) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame.copy() if cols is None else frame[cols].copy()
    view = view.head(max_rows)
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_value(row[col]) for col in view.columns) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def table_html(frame: pd.DataFrame, cols: list[str] | None = None, max_rows: int = 80) -> str:
    if frame.empty:
        return "<p><em>결과 없음</em></p>"
    view = frame.copy() if cols is None else frame[cols].copy()
    view = view.head(max_rows)
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_value(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred)
    ape = np.abs(safe_exp(pred[valid]) - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred[valid] - actual_log[valid]) ** 2))),
    }


def prep_shrink_keys(frame: pd.DataFrame, size_edges: np.ndarray) -> pd.DataFrame:
    keys, _ = shrink1.prep(frame, size_edges)
    return keys


def shrunk_medians_by_k(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
    size_edges: np.ndarray,
    k_grid: list[int],
) -> dict[int, dict[str, np.ndarray]]:
    y_train = pd.to_numeric(train["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
    train_out = {int(k): np.full(len(train), np.nan, dtype=float) for k in k_grid}
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    for source_idx, holdout_idx in kfold.split(train):
        source_keys = prep_shrink_keys(train.iloc[source_idx], size_edges)
        holdout_keys = prep_shrink_keys(train.iloc[holdout_idx], size_edges)
        groups, global_median = shrink1.train_groups(source_keys, y_train[source_idx])
        for k in k_grid:
            train_out[int(k)][holdout_idx] = shrink1.shrunk_prior(holdout_keys, groups, global_median, float(k))

    full_groups, full_global = shrink1.train_groups(prep_shrink_keys(train, size_edges), y_train)
    val_keys = prep_shrink_keys(val, size_edges)
    test_keys = prep_shrink_keys(test, size_edges)
    return {
        int(k): {
            "train": train_out[int(k)],
            "validation": shrink1.shrunk_prior(val_keys, full_groups, full_global, float(k)),
            "test": shrink1.shrunk_prior(test_keys, full_groups, full_global, float(k)),
        }
        for k in k_grid
    }


def swap_median(frame: pd.DataFrame, values: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    out[MEDIAN_COL] = np.asarray(values, dtype=float)
    return out


def prediction_rows(
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    seed: int | None,
    k: int,
    source: str,
) -> pd.DataFrame:
    out = svc1.prediction_frame(EXP_ID, candidate, "warm", split, frame, pred_log)
    out["seed"] = seed
    out["shrinkage_k"] = k
    out["base_candidate"] = candidate
    out["source"] = source
    return out


def build_shrunk_svc_predictions() -> tuple[pd.DataFrame, dict[int, dict[str, pd.DataFrame]], pd.DataFrame]:
    base_features = artifact_features()["warm"]
    requested = list(
        dict.fromkeys([*base_features, *svc1.GROUPING_FEATURES, "area_cm2", "artist_key", "medium_category", "support_category"])
    )
    train_base, val_base, test_base = load_scope("warm", requested)
    size_edges = shrink1.prep(train_base, None)[1]
    group_defs = wmin2.group_defs_for_artist_min(wmin2.ARTIST_MIN_N_CANDIDATE)
    svc_features = list(dict.fromkeys([*base_features, *svc1.SVC_NUMERIC]))

    predictions: list[pd.DataFrame] = []
    seed0_meta: dict[int, dict[str, pd.DataFrame]] = {int(k): {} for k in K_GRID}
    coverage_rows: list[pd.DataFrame] = []
    for seed in SEEDS:
        train_raw, val_raw, test_raw, audit = wmin2.add_service_features_seed(train_base, val_base, test_base, seed, group_defs)
        audit = audit.copy()
        audit["shrinkage_seed"] = seed
        coverage_rows.append(audit)
        medians = shrunk_medians_by_k(train_base, val_base, test_base, seed, size_edges, K_GRID)
        for k in K_GRID:
            train_s = swap_median(train_raw, medians[int(k)]["train"])
            val_s = swap_median(val_raw, medians[int(k)]["validation"])
            test_s = swap_median(test_raw, medians[int(k)]["test"])
            if seed == SEEDS[0]:
                seed0_meta[int(k)]["validation"] = val_s.copy()
                seed0_meta[int(k)]["test"] = test_s.copy()

            train_n = svc1.normalize(train_s, svc_features)
            val_n = svc1.normalize(val_s, svc_features)
            test_n = svc1.normalize(test_s, svc_features)
            model = svc1.huber_model(svc_features)
            y_train = pd.to_numeric(train_n["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
            model.fit(train_n[svc_features], y_train)
            for split, frame_n, pred in [
                ("validation", val_n, np.asarray(model.predict(val_n[svc_features]), dtype=float)),
                ("test", test_n, np.asarray(model.predict(test_n[svc_features]), dtype=float)),
            ]:
                predictions.append(
                    prediction_rows(
                        f"wmin6_eb_svc_seed_{seed}_k{k}",
                        split,
                        frame_n,
                        pred,
                        seed,
                        int(k),
                        "min1_svc_numeric_with_eb_shrunk_median",
                    )
                )
    return pd.concat(predictions, ignore_index=True), seed0_meta, pd.concat(coverage_rows, ignore_index=True)


def seed_mean_by_k(seed_predictions: pd.DataFrame, seed0_meta: dict[int, dict[str, pd.DataFrame]]) -> tuple[pd.DataFrame, dict[int, dict[str, pd.DataFrame]]]:
    mean_rows: list[pd.DataFrame] = []
    mean_frames: dict[int, dict[str, pd.DataFrame]] = {int(k): {} for k in K_GRID}
    for k in K_GRID:
        part = seed_predictions[seed_predictions["shrinkage_k"].eq(int(k))].copy()
        for split, group in part.groupby("split", dropna=False):
            pivot = group.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last")
            mean_pred = pivot.mean(axis=1).rename("pred_log").reset_index()
            frame = seed0_meta[int(k)][str(split)].merge(mean_pred, on="_track6_row_id", how="inner")
            candidate = f"min1_eb_svc_numeric_reference_k{k}"
            mean_frames[int(k)][str(split)] = frame.copy()
            mean_rows.append(
                prediction_rows(candidate, str(split), frame, frame["pred_log"].to_numpy(dtype=float), None, int(k), "seed_mean")
            )
    return pd.concat(mean_rows, ignore_index=True), mean_frames


def ppv8_reference() -> pd.DataFrame:
    ref = wmin2.load_current_reference_predictions()
    return ref[ref["candidate"].eq(PPV8)][["split", "_track6_row_id", "pred_log"]].rename(columns={"pred_log": "ppv8_pred_log"})


def add_basis_predictions(mean_frames: dict[int, dict[str, pd.DataFrame]]) -> tuple[pd.DataFrame, dict[int, dict[str, pd.DataFrame]]]:
    ppv8 = ppv8_reference()
    rows: list[pd.DataFrame] = []
    basis_frames: dict[int, dict[str, pd.DataFrame]] = {int(k): {} for k in K_GRID}
    for k in K_GRID:
        for split, frame in mean_frames[int(k)].items():
            merged = frame.merge(ppv8[ppv8["split"].eq(split)], on=["_track6_row_id"], how="inner")
            merged["basis_pred_log"] = 0.70 * merged["pred_log"].to_numpy(dtype=float) + 0.30 * merged["ppv8_pred_log"].to_numpy(dtype=float)
            candidate = f"min1_eb_70_30_basis_k{k}"
            rows.append(
                prediction_rows(candidate, split, merged, merged["basis_pred_log"].to_numpy(dtype=float), None, int(k), "0.70_eb_svc_plus_0.30_ppv8")
            )
            basis_frames[int(k)][split] = merged.copy()
    return pd.concat(rows, ignore_index=True), basis_frames


def hcoef_frames_for_k(k: int, basis_frames: dict[int, dict[str, pd.DataFrame]], base_partial_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for split, base in base_partial_frames.items():
        src = basis_frames[int(k)][split][
            [
                "_track6_row_id",
                "pred_log",
                "basis_pred_log",
                "svc_group_level",
                "svc_coverage_tier",
                "svc_group_n",
                "svc_group_log_price_iqr",
            ]
        ].rename(columns={"pred_log": "eb_svc_pred_log"})
        merged = base.merge(src, on="_track6_row_id", how="inner", suffixes=("", "_eb"))
        if len(merged) != len(base):
            raise RuntimeError(f"WMIN6 HCOEF merge row mismatch for k={k}, split={split}: {len(merged)} != {len(base)}")
        merged["current_70_30"] = pd.to_numeric(merged["basis_pred_log"], errors="coerce")
        merged["svc_fallback"] = pd.to_numeric(merged["eb_svc_pred_log"], errors="coerce")
        merged[wmin3.NEW_SVC] = merged["svc_fallback"]
        merged[wmin3.NEW_BASIS] = merged["current_70_30"]
        for col in ["svc_group_level", "svc_coverage_tier"]:
            eb_col = f"{col}_eb"
            if eb_col in merged.columns:
                merged[col] = merged[eb_col].astype(str)
        for col in ["svc_group_n", "svc_group_log_price_iqr"]:
            eb_col = f"{col}_eb"
            if eb_col in merged.columns:
                merged[col] = pd.to_numeric(merged[eb_col], errors="coerce")
        merged["svc_group_n_log"] = np.log1p(pd.to_numeric(merged["svc_group_n"], errors="coerce").fillna(0.0))
        refreshed = hcoef1.add_derived_features(merged, split)
        out[split] = refreshed.reset_index(drop=True)
    return out


def add_hcoef_predictions(basis_frames: dict[int, dict[str, pd.DataFrame]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_partial_frames = wmin3.make_variant_frames("partial")
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    for k in K_GRID:
        frames = hcoef_frames_for_k(int(k), basis_frames, base_partial_frames)
        validation = frames["validation"].reset_index(drop=True)
        candidate = f"min1_eb_huber_refit_partial_k{k}"
        for split in ["validation", "test"]:
            frame = frames[split].reset_index(drop=True)
            pred, model = wmin3.fit_refit_candidate(validation, frame)
            pred_rows.append(
                prediction_rows(candidate, split, frame, pred, None, int(k), "partial_huber_refit_on_eb_70_30_basis")
            )
            if split == "test":
                coef = wmin3.hcoef3.coefficient_frame(model, wmin3.STABLE_CONFIG)
                coef["experiment_id"] = EXP_ID
                coef["candidate_label"] = candidate
                coef["shrinkage_k"] = int(k)
                coef_rows.append(coef)
    return pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def to_decision_predictions(source: pd.DataFrame, candidate_label_map: dict[str, str] | None = None) -> pd.DataFrame:
    out = source.copy()
    if candidate_label_map is None:
        out["candidate_label"] = out["candidate"]
    else:
        out["candidate_label"] = out["candidate"].map(candidate_label_map).fillna(out["candidate"])
    out["eval_split"] = np.where(out["split"].eq("validation"), "validation_oof", "test")
    out["family"] = "wmin6_min1_eb_shrinkage"
    out["item_id"] = EXP_ID
    out["source_experiment"] = EXP_ID
    if "quantile_width" not in out.columns:
        out["quantile_width"] = np.nan
    if "component_prediction_spread" not in out.columns:
        out["component_prediction_spread"] = np.nan
    if "current_vs_stable_gap_abs" not in out.columns:
        out["current_vs_stable_gap_abs"] = np.nan
    if "stable_price_band" not in out.columns:
        out["stable_price_band"] = np.nan
    return out


def attach_reference_meta(predictions: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    meta_cols = [
        "eval_split",
        "_track6_row_id",
        "confidence_tier",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    meta = (
        reference[reference["candidate_label"].eq(PP258_REFERENCE)][meta_cols]
        .drop_duplicates(["eval_split", "_track6_row_id"])
        .copy()
    )
    out = predictions.drop(columns=[col for col in meta_cols[2:] if col in predictions.columns], errors="ignore")
    return out.merge(meta, on=["eval_split", "_track6_row_id"], how="left")


def load_decision_baselines() -> pd.DataFrame:
    existing = pd.read_csv(wmin4.OUT_DIR / "candidate_predictions.csv", low_memory=False)
    keep = existing[existing["candidate_label"].isin([PP258_REFERENCE, WMIN4_SELECTED])].copy()
    if keep["candidate_label"].nunique() != 2:
        raise RuntimeError("Missing PP258 or WMIN4 selected baseline predictions")
    return keep


def comparison_vs_wmin4(fixed: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    wmin6 = fixed[fixed["candidate_label"].str.startswith("min1_eb_", na=False)].copy()
    for split, split_group in wmin6.groupby("eval_split", dropna=False):
        base = fixed[(fixed["eval_split"].eq(split)) & (fixed["candidate_label"].eq(WMIN4_SELECTED))]
        if base.empty:
            continue
        base_row = base.iloc[0]
        for _, row in split_group.iterrows():
            rows.append(
                {
                    "candidate_label": row["candidate_label"],
                    "eval_split": split,
                    "delta_MdAPE_vs_wmin4_selected": float(row["MdAPE"] - base_row["MdAPE"]),
                    "delta_MAPE_vs_wmin4_selected": float(row["MAPE"] - base_row["MAPE"]),
                    "delta_p95_APE_vs_wmin4_selected": float(row["p95_APE"] - base_row["p95_APE"]),
                    "delta_RMSE_log_vs_wmin4_selected": float(row["RMSE_log"] - base_row["RMSE_log"]),
                }
            )
    return pd.DataFrame(rows)


def render_report(
    aggregate: pd.DataFrame,
    fixed: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    svc_metrics: pd.DataFrame,
    decision: dict[str, Any],
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
        "fixed_test_delta_MAPE_vs_current_pp258",
        "fixed_test_delta_p95_vs_current_pp258",
    ]
    fixed_cols = [
        "candidate_label",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_vs_current_pp258_MAPE",
        "delta_vs_current_pp258_p95_APE",
    ]
    comp_cols = [
        "candidate_label",
        "eval_split",
        "delta_MdAPE_vs_wmin4_selected",
        "delta_MAPE_vs_wmin4_selected",
        "delta_p95_APE_vs_wmin4_selected",
        "delta_RMSE_log_vs_wmin4_selected",
    ]
    selected = decision["selected_candidate_label"]
    selected_row = aggregate[aggregate["candidate_label"].eq(selected)].iloc[0]
    status_line = (
        f"{decision['decision_status']}: `{selected}` 선택. "
        f"validation {decision['selected_fixed_validation_MdAPE']:.6f}/"
        f"{decision['selected_fixed_validation_MAPE']:.6f}/"
        f"{decision['selected_fixed_validation_p95_APE']:.6f}, "
        f"fixed test {decision['selected_fixed_test_MdAPE']:.6f}/"
        f"{decision['selected_fixed_test_MAPE']:.6f}/"
        f"{decision['selected_fixed_test_p95_APE']:.6f}."
    )
    selected_vs_wmin4 = comparison[comparison["candidate_label"].eq(selected)].copy()
    md = "\n".join(
        [
            "# PP-WMIN6 Warm min1 EB shrinkage decision 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 선택 기준: WMIN4와 동일하게 validation 반복 안정성 + validation replacement score",
            "- fixed test: 최종 확인용으로만 기록",
            "- 0604: 사용하지 않음. WMIN5에서 stress 통과 후 본 실험은 기존 비교 기준으로만 수행",
            f"- 결론: {status_line}",
            f"- 판단 근거: {decision['reason']}",
            f"- 선택 후보 fixed confirmation 통과: `{bool(selected_row['passes_fixed_confirmation'])}`",
            "",
            "## 1. 후보별 교체 판단",
            markdown_table(aggregate, agg_cols, 120),
            "",
            "## 2. WMIN4 선택 후보 대비 변화량",
            markdown_table(comparison.sort_values(["eval_split", "delta_MAPE_vs_wmin4_selected"]), comp_cols, 120),
            "",
            "## 3. fixed validation/test 지표",
            markdown_table(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 160),
            "",
            "## 4. EB SVC와 70:30 기준가 자체 지표",
            markdown_table(svc_metrics.sort_values(["eval_split", "candidate_label"]), fixed_cols, 120),
            "",
            "## 5. 선택 후보 반복 validation 시나리오",
            markdown_table(
                repeated_summary[repeated_summary["candidate_label"].eq(selected)].round(6),
                [
                    "candidate_label",
                    "scenario",
                    "mean_MdAPE",
                    "mean_MAPE",
                    "mean_p95_APE",
                    "current_pp258_MAPE_win_rate",
                    "current_pp258_p95_win_rate",
                    "current_pp258_all3_win_rate",
                ],
                60,
            ),
            "",
            "## 6. 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-WMIN6 Warm min1 EB shrinkage decision 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1320px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 10px; font-size:30px; }} h2 {{ margin:36px 0 12px; padding-top:18px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:22px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-WMIN6 Warm min1 EB shrinkage decision 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(status_line)}<br>{html.escape(decision['reason'])}</div>
<h2>1. 후보별 교체 판단</h2>{table_html(aggregate, agg_cols, 120)}
<h2>2. WMIN4 선택 후보 대비 변화량</h2>{table_html(comparison.sort_values(["eval_split", "delta_MAPE_vs_wmin4_selected"]), comp_cols, 120)}
<h2>3. fixed validation/test 지표</h2>{table_html(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 160)}
<h2>4. EB SVC와 70:30 기준가 자체 지표</h2>{table_html(svc_metrics.sort_values(["eval_split", "candidate_label"]), fixed_cols, 120)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md + "\n", html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()

    seed_predictions, seed0_meta, leakage_audit = build_shrunk_svc_predictions()
    mean_svc_predictions, mean_frames = seed_mean_by_k(seed_predictions, seed0_meta)
    basis_predictions, basis_frames = add_basis_predictions(mean_frames)
    hcoef_predictions, hcoef_coefficients = add_hcoef_predictions(basis_frames)

    raw_new_predictions = pd.concat([mean_svc_predictions, basis_predictions, hcoef_predictions], ignore_index=True, sort=False)
    decision_baselines = load_decision_baselines()
    new_decision_predictions = attach_reference_meta(to_decision_predictions(raw_new_predictions), decision_baselines)
    decision_predictions = pd.concat([decision_baselines, new_decision_predictions], ignore_index=True, sort=False)
    decision_predictions = decision_predictions.drop_duplicates(["candidate_label", "eval_split", "_track6_row_id"], keep="first")

    fixed = wmin4.fixed_metrics(decision_predictions)
    repeated_detail, repeated_summary = wmin4.repeated_validation_metrics(decision_predictions)
    aggregate = wmin4.aggregate_decision(fixed, repeated_summary)
    decision = wmin4.choose_decision(aggregate)
    comparison = comparison_vs_wmin4(fixed)
    svc_metrics = fixed[fixed["candidate_label"].str.contains("_svc_numeric_reference_|_70_30_basis_", regex=True, na=False)].copy()

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selection_policy": "validation repeated stability and validation replacement score only; fixed test is confirmation; 0604 is not used",
        "reference_candidate_label": PP258_REFERENCE,
        "wmin4_selected_candidate_label": WMIN4_SELECTED,
        "k_grid": K_GRID,
        "seeds": SEEDS,
        "median_replacement": "replace only svc_group_log_price_median with hierarchical empirical-Bayes shrunk median",
        "eb_formula": "shrunk = n/(n+k)*group_median + k/(n+k)*parent_estimate, applied from global -> artist -> artist+size -> artist+medium/support+size",
        "basis_formula": "min1_eb_70_30_basis = 0.70 * min1_eb_svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded",
        "huber_refit": {
            "mode": "WMIN3 partial",
            "current_70_30": "EB 70:30 basis",
            "svc_fallback": "EB SVC seed mean",
            "stable_config": wmin3.STABLE_CONFIG,
        },
        "decision": decision,
    }

    raw_new_predictions.to_csv(OUT_DIR / "wmin6_raw_candidate_predictions.csv", index=False)
    decision_predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    fixed.to_csv(OUT_DIR / "fixed_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "operational_decision_aggregate.csv", index=False)
    comparison.to_csv(OUT_DIR / "comparison_vs_wmin4_selected.csv", index=False)
    svc_metrics.to_csv(OUT_DIR / "svc_and_basis_fixed_metrics.csv", index=False)
    hcoef_coefficients.to_csv(OUT_DIR / "huber_refit_coefficients.csv", index=False)
    leakage_audit.to_csv(OUT_DIR / "leakage_audit.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(aggregate, fixed, repeated_summary, comparison, svc_metrics, decision, config)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_SUMMARY.write_text(md, encoding="utf-8")
    (EXP_DIR / "logs").mkdir(exist_ok=True)
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "completed",
                "decision": decision,
                "seconds": round(time.time() - start, 2),
                "experiment_dir": str(EXP_DIR.relative_to(REPO)),
                "report": str((REPORT_DIR / "result_report.md").relative_to(REPO)),
                "summary_doc": str(DOC_SUMMARY.relative_to(REPO)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
