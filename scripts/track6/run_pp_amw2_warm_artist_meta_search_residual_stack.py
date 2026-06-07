#!/usr/bin/env python3
"""Run PP-AMW2 Warm artist-meta + search residual stacking.

This experiment keeps the current strong Warm prediction fixed and combines
two already-fitted validation-only residual corrections:

1. PP-AMW1: artist metadata segment residual correction.
2. PP-H29: external search feature segment residual correction.

The goal is to check whether artist metadata and search context explain
different parts of the remaining Warm error. Test labels are not used to
create either correction value or to choose the correction weights.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-AMW2"
EXP_SLUG = "PP-AMW2_warm_artist_meta_search_residual_stack"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

AMW1_DIR = REPO / "experiments" / "track6" / "PP-AMW1_warm_artist_meta_residual_calibration"
H29_DIR = REPO / "experiments" / "track6" / "PP-H29_warm_search_feature_calibration"

AMW1_PRED_PATH = AMW1_DIR / "outputs" / "predictions.csv"
AMW1_METRIC_PATH = AMW1_DIR / "outputs" / "metrics.csv"
H29_PRED_PATH = H29_DIR / "outputs" / "candidate_predictions.csv"
H29_METRIC_PATH = H29_DIR / "outputs" / "metrics.csv"

BASELINE_CANDIDATE = "baseline_ppv8_compact_blend_mape_guarded"
H29_COMPACT_MARKER = "h29_v8_compact_mape_"

WEIGHT_GRID = [
    (1.0, 1.0),
    (1.0, 0.75),
    (1.0, 0.50),
    (0.75, 1.0),
    (0.50, 1.0),
    (0.50, 0.50),
]
TOTAL_CORRECTION_CAPS = [0.03, 0.05, 0.08, 0.10]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def metric_row(base: pd.DataFrame, pred_log: np.ndarray, candidate: str, split: str, policy: str) -> dict[str, Any]:
    actual_log = base["actual_log"].to_numpy(dtype=float)
    actual_price = np.exp(actual_log)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual_price) / np.maximum(actual_price, 1e-9)
    ratio = pred_price / np.maximum(actual_price, 1e-9)
    return {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        "n": int(len(base)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(pred_log - actual_log)))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "over_3x_n": int(np.sum(ratio > 3.0)),
        "under_1_3x_n": int(np.sum(ratio < (1.0 / 3.0))),
        "median_ratio": float(np.median(ratio)),
    }


def load_base_predictions() -> pd.DataFrame:
    pred = pd.read_csv(AMW1_PRED_PATH, low_memory=False)
    base = pred[pred["candidate"].eq(BASELINE_CANDIDATE)].copy()
    if base.empty:
        raise RuntimeError(f"Missing baseline candidate in {AMW1_PRED_PATH}: {BASELINE_CANDIDATE}")
    keep_cols = ["split", "_track6_row_id", "actual_log", "pred_log", "actual_price", "pred_price"]
    base = base[keep_cols].drop_duplicates(["split", "_track6_row_id"], keep="first")
    base = base[base["split"].isin(["validation", "test"])].copy()
    base = base.sort_values(["split", "_track6_row_id"]).reset_index(drop=True)
    return base


def select_amw_candidates(limit: int = 20) -> list[str]:
    metrics = pd.read_csv(AMW1_METRIC_PATH, low_memory=False)
    val = metrics[
        metrics["split"].eq("validation")
        & ~metrics["candidate"].eq(BASELINE_CANDIDATE)
    ].copy()
    baseline = metrics[
        metrics["split"].eq("validation")
        & metrics["candidate"].eq(BASELINE_CANDIDATE)
    ].iloc[0]
    guarded = val[
        (val["MdAPE"] <= baseline["MdAPE"] + 0.003)
        & (val["p95_APE"] <= baseline["p95_APE"] + 0.005)
    ].copy()
    if guarded.empty:
        guarded = val
    return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "RMSE_log"]).head(limit)["candidate"].tolist()


def select_h29_candidates(limit: int = 24) -> list[str]:
    metrics = pd.read_csv(H29_METRIC_PATH, low_memory=False)
    val = metrics[
        metrics["split"].eq("validation")
        & metrics["candidate"].astype(str).str.contains(H29_COMPACT_MARKER, regex=False)
        & metrics["policy"].eq("validation_segment_median_residual_correction")
    ].copy()
    baseline = metrics[
        metrics["split"].eq("validation")
        & metrics["candidate"].eq("baseline__v8_compact_mape")
    ].iloc[0]
    guarded = val[
        (val["MdAPE"] <= baseline["MdAPE"] + 0.003)
        & (val["p95_APE"] <= baseline["p95_APE"] + 0.010)
    ].copy()
    if guarded.empty:
        guarded = val
    return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "RMSE_log"]).head(limit)["candidate"].tolist()


def correction_series(path: Path, candidate: str, base_index: pd.MultiIndex) -> pd.Series:
    pred = pd.read_csv(path, low_memory=False)
    part = pred[pred["candidate"].eq(candidate)].copy()
    if part.empty:
        raise RuntimeError(f"Missing correction candidate: {candidate}")
    part["correction_log"] = pd.to_numeric(part["corrected_pred_log"], errors="coerce") - pd.to_numeric(part["pred_log"], errors="coerce")
    series = part.set_index(["split", "_track6_row_id"])["correction_log"]
    return series.reindex(base_index).fillna(0.0).astype(float)


def load_corrections(base: pd.DataFrame, amw_candidates: list[str], h29_candidates: list[str]) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    base_index = pd.MultiIndex.from_frame(base[["split", "_track6_row_id"]])
    amw = {candidate: correction_series(AMW1_PRED_PATH, candidate, base_index) for candidate in amw_candidates}
    h29 = {candidate: correction_series(H29_PRED_PATH, candidate, base_index) for candidate in h29_candidates}
    return amw, h29


def short_id(prefix: str, order: int) -> str:
    return f"{prefix}{order:02d}"


def run_grid(base: pd.DataFrame, amw: dict[str, pd.Series], h29: dict[str, pd.Series]) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics_rows: list[dict[str, Any]] = []
    combo_rows: list[dict[str, Any]] = []
    base_index = pd.MultiIndex.from_frame(base[["split", "_track6_row_id"]])
    base_pred = base["pred_log"].to_numpy(dtype=float)
    split_masks = {split: base["split"].eq(split).to_numpy() for split in ["validation", "test"]}

    for split, mask in split_masks.items():
        metrics_rows.append(metric_row(base.loc[mask], base_pred[mask], "baseline_ppv8_compact_blend_mape_guarded", split, "baseline"))

    amw_ids = {candidate: short_id("amw", i + 1) for i, candidate in enumerate(amw)}
    h29_ids = {candidate: short_id("h29", i + 1) for i, candidate in enumerate(h29)}
    amw_values = {candidate: series.reindex(base_index).to_numpy(dtype=float) for candidate, series in amw.items()}
    h29_values = {candidate: series.reindex(base_index).to_numpy(dtype=float) for candidate, series in h29.items()}

    for amw_candidate, amw_corr in amw_values.items():
        for h29_candidate, h29_corr in h29_values.items():
            for amw_weight, h29_weight in WEIGHT_GRID:
                raw_corr = (amw_corr * amw_weight) + (h29_corr * h29_weight)
                for cap in TOTAL_CORRECTION_CAPS:
                    total_corr = np.clip(raw_corr, -cap, cap)
                    candidate = (
                        f"stack_{amw_ids[amw_candidate]}_{h29_ids[h29_candidate]}"
                        f"_wa{amw_weight:g}_wh{h29_weight:g}_cap{str(cap).replace('.', 'p')}"
                    )
                    combo_rows.append({
                        "candidate": candidate,
                        "artist_meta_candidate": amw_candidate,
                        "search_candidate": h29_candidate,
                        "artist_meta_weight": amw_weight,
                        "search_weight": h29_weight,
                        "total_correction_cap": cap,
                        "mean_abs_artist_meta_correction": float(np.mean(np.abs(amw_corr))),
                        "mean_abs_search_correction": float(np.mean(np.abs(h29_corr))),
                        "mean_abs_combined_correction": float(np.mean(np.abs(total_corr))),
                        "max_abs_combined_correction": float(np.max(np.abs(total_corr))),
                    })
                    pred_log = base_pred + total_corr
                    for split, mask in split_masks.items():
                        metrics_rows.append(metric_row(
                            base.loc[mask],
                            pred_log[mask],
                            candidate,
                            split,
                            "artist_meta_search_residual_stack",
                        ))
    return pd.DataFrame(metrics_rows), pd.DataFrame(combo_rows)


def add_baseline_deltas(metrics: pd.DataFrame) -> pd.DataFrame:
    out = metrics.copy()
    baseline = out[out["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")].set_index("split")
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_vs_baseline_{col}"] = out.apply(lambda row: row[col] - baseline.loc[row["split"], col], axis=1)
    return out


def select_validation_candidates(metrics: pd.DataFrame, limit: int = 30) -> pd.DataFrame:
    validation = metrics[
        metrics["split"].eq("validation")
        & ~metrics["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")
    ].copy()
    baseline = metrics[
        metrics["split"].eq("validation")
        & metrics["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")
    ].iloc[0]
    guarded = validation[
        (validation["MdAPE"] <= baseline["MdAPE"] + 0.003)
        & (validation["p95_APE"] <= baseline["p95_APE"] + 0.005)
        & (validation["MAPE"] <= baseline["MAPE"])
    ].copy()
    if guarded.empty:
        guarded = validation
    return guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "RMSE_log"]).head(limit)


def select_conservative_balanced_candidates(metrics: pd.DataFrame, combo_map: pd.DataFrame, limit: int = 30) -> pd.DataFrame:
    """Select small-correction candidates that improve all core validation metrics."""
    validation = metrics[
        metrics["split"].eq("validation")
        & ~metrics["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")
    ].copy()
    balanced = validation[
        (validation["delta_vs_baseline_MdAPE"] < 0)
        & (validation["delta_vs_baseline_MAPE"] < 0)
        & (validation["delta_vs_baseline_p95_APE"] < 0)
    ].copy()
    if balanced.empty:
        return validation.sort_values(["MAPE", "MdAPE", "p95_APE", "RMSE_log"]).head(limit)
    balanced = balanced.merge(
        combo_map[["candidate", "mean_abs_combined_correction", "max_abs_combined_correction"]],
        on="candidate",
        how="left",
    )
    return balanced.sort_values([
        "mean_abs_combined_correction",
        "MAPE",
        "MdAPE",
        "p95_APE",
        "RMSE_log",
    ]).head(limit)


def build_prediction_export(base: pd.DataFrame, combo_map: pd.DataFrame, candidate_ids: list[str], amw: dict[str, pd.Series], h29: dict[str, pd.Series]) -> pd.DataFrame:
    base_index = pd.MultiIndex.from_frame(base[["split", "_track6_row_id"]])
    base_pred = base["pred_log"].to_numpy(dtype=float)
    parts = []
    combo_lookup = combo_map.set_index("candidate")
    for candidate in candidate_ids:
        if candidate == "baseline_ppv8_compact_blend_mape_guarded":
            pred_log = base_pred.copy()
            artist_corr = np.zeros(len(base))
            search_corr = np.zeros(len(base))
            total_corr = np.zeros(len(base))
        else:
            row = combo_lookup.loc[candidate]
            artist_corr = amw[row["artist_meta_candidate"]].reindex(base_index).to_numpy(dtype=float) * float(row["artist_meta_weight"])
            search_corr = h29[row["search_candidate"]].reindex(base_index).to_numpy(dtype=float) * float(row["search_weight"])
            total_corr = np.clip(artist_corr + search_corr, -float(row["total_correction_cap"]), float(row["total_correction_cap"]))
            pred_log = base_pred + total_corr
        part = base.copy()
        part["candidate"] = candidate
        part["artist_meta_correction"] = artist_corr
        part["search_correction"] = search_corr
        part["total_correction"] = total_corr
        part["corrected_pred_log"] = pred_log
        part["corrected_pred_price"] = np.exp(pred_log)
        part["corrected_ape"] = np.abs(part["corrected_pred_price"] - np.exp(part["actual_log"])) / np.maximum(np.exp(part["actual_log"]), 1e-9)
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_결과 없음_"
    view = df.head(max_rows).copy() if max_rows else df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.6f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(view.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def render_html(title: str, summary: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 28px}th,td{border:1px solid #d8dee9;padding:7px 8px;text-align:right}"
        "th:first-child,td:first-child{text-align:left}th{background:#eef2f7}.note{white-space:pre-wrap;background:#f8fafc;border-left:4px solid #2563eb;padding:12px 14px}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='note'>{html.escape(summary)}</div>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=True, float_format=lambda value: f"{value:.6f}"))
    body.append("</body></html>")
    return "\n".join(body)


def main() -> None:
    ensure_dirs()
    base = load_base_predictions()
    amw_candidates = select_amw_candidates()
    h29_candidates = select_h29_candidates()
    amw_corrections, h29_corrections = load_corrections(base, amw_candidates, h29_candidates)

    metrics, combo_map = run_grid(base, amw_corrections, h29_corrections)
    metrics = add_baseline_deltas(metrics)
    validation_selected = select_validation_candidates(metrics)
    conservative_selected = select_conservative_balanced_candidates(metrics, combo_map)
    selected_ids = validation_selected["candidate"].tolist()
    conservative_ids = conservative_selected["candidate"].tolist()
    selected_metrics = metrics[metrics["candidate"].isin(selected_ids + ["baseline_ppv8_compact_blend_mape_guarded"])].copy()
    conservative_metrics = metrics[metrics["candidate"].isin(conservative_ids + ["baseline_ppv8_compact_blend_mape_guarded"])].copy()
    selected_test = selected_metrics[selected_metrics["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()
    conservative_test = conservative_metrics[conservative_metrics["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).copy()
    test_top = metrics[metrics["split"].eq("test")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(30).copy()
    test_all_metric_improved = metrics[
        metrics["split"].eq("test")
        & (metrics["delta_vs_baseline_MdAPE"] < 0)
        & (metrics["delta_vs_baseline_MAPE"] < 0)
        & (metrics["delta_vs_baseline_p95_APE"] < 0)
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(30).copy()
    validation_top = metrics[metrics["split"].eq("validation")].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(30).copy()

    export_ids = ["baseline_ppv8_compact_blend_mape_guarded"]
    export_ids += validation_selected.head(5)["candidate"].tolist()
    export_ids += conservative_selected.head(5)["candidate"].tolist()
    export_ids += test_top.head(5)["candidate"].tolist()
    export_ids = list(dict.fromkeys(export_ids))
    predictions = build_prediction_export(base, combo_map, export_ids, amw_corrections, h29_corrections)

    metrics.to_csv(OUT_DIR / "metrics.csv", index=False)
    combo_map.to_csv(OUT_DIR / "candidate_map.csv", index=False)
    selected_metrics.to_csv(OUT_DIR / "selected_candidate_metrics.csv", index=False)
    conservative_metrics.to_csv(OUT_DIR / "conservative_balanced_candidate_metrics.csv", index=False)
    validation_top.to_csv(OUT_DIR / "validation_top_candidates.csv", index=False)
    test_top.to_csv(OUT_DIR / "test_top_candidates.csv", index=False)
    test_all_metric_improved.to_csv(OUT_DIR / "test_all_metric_improved_candidates.csv", index=False)
    predictions.to_csv(OUT_DIR / "prediction_samples.csv", index=False)

    baseline_test = metrics[
        metrics["split"].eq("test")
        & metrics["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")
    ].iloc[0]
    best_val_selected_test = selected_test.iloc[0]
    best_conservative_test = conservative_test.iloc[0]
    best_test = test_top.iloc[0]
    best_all_metric_test = test_all_metric_improved.iloc[0] if not test_all_metric_improved.empty else best_test
    best_validation = validation_top[~validation_top["candidate"].eq("baseline_ppv8_compact_blend_mape_guarded")].iloc[0]

    summary = "\n".join([
        "- 기준 후보: PP-V8 compact_blend_mape_guarded",
        "- 결합 방식: PP-AMW1 작가 메타 보정값 + PP-H29 검색 피처 보정값을 가중 결합",
        "- 보정값 생성: 두 보정 모두 validation 잔차에서 생성된 기존 후보만 사용",
        "- 가중치 선택: validation 성능 기준으로 후보를 고르고 test에는 같은 설정을 적용",
        "- 운영 코드 변경: 없음",
        "",
        "핵심 결과:",
        f"- 기준 test MdAPE {baseline_test['MdAPE']:.4f}, MAPE {baseline_test['MAPE']:.4f}, p95_APE {baseline_test['p95_APE']:.4f}",
        f"- validation 1순위 후보: {best_validation['candidate']} / validation MdAPE {best_validation['MdAPE']:.4f}, MAPE {best_validation['MAPE']:.4f}, p95_APE {best_validation['p95_APE']:.4f}",
        f"- validation 선택 후보 중 test 최선: {best_val_selected_test['candidate']} / test MdAPE {best_val_selected_test['MdAPE']:.4f}, MAPE {best_val_selected_test['MAPE']:.4f}, p95_APE {best_val_selected_test['p95_APE']:.4f}",
        f"- 보수 선택 후보 중 test 최선: {best_conservative_test['candidate']} / test MdAPE {best_conservative_test['MdAPE']:.4f}, MAPE {best_conservative_test['MAPE']:.4f}, p95_APE {best_conservative_test['p95_APE']:.4f}",
        f"- 전체 grid 중 test MAPE 최선: {best_test['candidate']} / test MdAPE {best_test['MdAPE']:.4f}, MAPE {best_test['MAPE']:.4f}, p95_APE {best_test['p95_APE']:.4f}",
        f"- test에서 MdAPE/MAPE/p95가 모두 개선된 후보 중 MAPE 최선: {best_all_metric_test['candidate']} / test MdAPE {best_all_metric_test['MdAPE']:.4f}, MAPE {best_all_metric_test['MAPE']:.4f}, p95_APE {best_all_metric_test['p95_APE']:.4f}",
        "",
        "판단 기준:",
        "- validation 선택 후보가 test에서도 기준 대비 MdAPE/MAPE/p95를 함께 낮추면 후속 반복 검증 대상으로 둔다.",
        "- 보수 선택 후보는 validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보를 우선한다.",
        "- test에서만 좋아지는 후보는 탐색 결과로만 보고 바로 채택하지 않는다.",
    ])

    report = f"""# PP-AMW2 Warm 작가 메타 + 검색 피처 잔차 결합 보정 결과

## 1. 실행 요약

{summary}

## 2. 사용한 입력 후보

- 작가 메타 보정 후보 수: {len(amw_candidates)}
- 검색 피처 보정 후보 수: {len(h29_candidates)}
- 결합 후보 수: {len(combo_map)}

## 3. validation 상위 후보

{markdown_table(validation_top)}

## 4. validation 선택 후보의 validation/test 지표

{markdown_table(selected_metrics.sort_values(["candidate", "split"]))}

## 5. 보수 선택 후보의 validation/test 지표

{markdown_table(conservative_metrics.sort_values(["candidate", "split"]))}

## 6. test 기준 상위 후보

{markdown_table(test_top)}

## 7. test에서 세 지표가 모두 개선된 후보

{markdown_table(test_all_metric_improved)}

## 8. 후보 매핑 샘플

{markdown_table(combo_map.head(40))}

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_map.csv`
- `outputs/selected_candidate_metrics.csv`
- `outputs/conservative_balanced_candidate_metrics.csv`
- `outputs/validation_top_candidates.csv`
- `outputs/test_top_candidates.csv`
- `outputs/test_all_metric_improved_candidates.csv`
- `outputs/prediction_samples.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        render_html(
            "PP-AMW2 Warm 작가 메타 + 검색 피처 잔차 결합 보정 결과",
            summary,
            {
                "validation 상위 후보": validation_top,
                "validation 선택 후보의 validation/test 지표": selected_metrics.sort_values(["candidate", "split"]),
                "보수 선택 후보의 validation/test 지표": conservative_metrics.sort_values(["candidate", "split"]),
                "test 기준 상위 후보": test_top,
                "test에서 세 지표가 모두 개선된 후보": test_all_metric_improved,
                "후보 매핑 샘플": combo_map.head(40),
            },
        ),
        encoding="utf-8",
    )
    manifest = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": "PP-V8 compact_blend_mape_guarded",
        "artist_meta_source": str(AMW1_PRED_PATH.relative_to(REPO)),
        "search_source": str(H29_PRED_PATH.relative_to(REPO)),
        "method": "validation-selected weighted residual stacking",
        "amw_candidate_n": len(amw_candidates),
        "h29_candidate_n": len(h29_candidates),
        "combo_n": len(combo_map),
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "baseline_test": {
            "MdAPE": baseline_test["MdAPE"],
            "MAPE": baseline_test["MAPE"],
            "p95_APE": baseline_test["p95_APE"],
        },
        "best_validation_selected_test": {
            "candidate": best_val_selected_test["candidate"],
            "MdAPE": best_val_selected_test["MdAPE"],
            "MAPE": best_val_selected_test["MAPE"],
            "p95_APE": best_val_selected_test["p95_APE"],
        },
        "best_conservative_balanced_test": {
            "candidate": best_conservative_test["candidate"],
            "MdAPE": best_conservative_test["MdAPE"],
            "MAPE": best_conservative_test["MAPE"],
            "p95_APE": best_conservative_test["p95_APE"],
        },
        "best_test_exploratory": {
            "candidate": best_test["candidate"],
            "MdAPE": best_test["MdAPE"],
            "MAPE": best_test["MAPE"],
            "p95_APE": best_test["p95_APE"],
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
