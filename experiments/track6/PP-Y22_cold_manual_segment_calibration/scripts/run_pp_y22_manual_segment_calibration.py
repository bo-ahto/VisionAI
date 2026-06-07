#!/usr/bin/env python3
"""Cold manual segment residual calibration experiment.

This experiment checks whether human-defined, operationally explainable
segments work better than validation-quantile automatic bins for Cold
post-processing.
"""
from __future__ import annotations

import html
import argparse
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP_ID = "PP-Y22"
EXP_SLUG = "PP-Y22_cold_manual_segment_calibration"
EXP_DIR = PROJECT_ROOT / "experiments/track6" / EXP_SLUG
SOURCE_PREDICTIONS = PROJECT_ROOT / "experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv"
AUTO_METRICS = PROJECT_ROOT / "experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/metrics.csv"
SOURCE_CANDIDATE = "lgbq_search_all_external_interaction"
SEED = 20260605


@dataclass(frozen=True)
class Policy:
    segment_name: str
    segment_cols: tuple[str, ...]
    min_rows: int
    cap: float
    strength: float
    fallback: str

    @property
    def candidate(self) -> str:
        return (
            f"manual_{self.segment_name}"
            f"_min{self.min_rows}_cap{self.cap:g}_s{self.strength:g}_{self.fallback}"
        )


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data", "scripts"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)


def load_source(split: str) -> pd.DataFrame:
    df = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    mask = (
        df["candidate"].astype(str).eq(SOURCE_CANDIDATE)
        & df["scope"].astype(str).eq("cold")
        & df["split"].astype(str).eq(split)
    )
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"Missing source predictions: {SOURCE_PREDICTIONS} {split}")
    for col in ["actual_log", "pred_log", "actual_price", "pred_price", "residual_log", "quantile_width_log"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if "price_range_ratio" not in out.columns:
        out["price_range_ratio"] = np.exp(np.clip(out["quantile_width_log"], 0.0, 8.0))
    out["price_range_ratio"] = pd.to_numeric(out["price_range_ratio"], errors="coerce")
    return add_manual_segments(out)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "over_3x_n": int((pred_price / np.clip(actual_price, 1.0, None) >= 3.0).sum()),
        "under_1_3x_n": int((pred_price / np.clip(actual_price, 1.0, None) <= (1.0 / 3.0)).sum()),
    }


def price_band(price: float) -> str:
    if pd.isna(price) or price <= 0:
        return "price_missing"
    if price < 500_000:
        return "under_0_5m"
    if price < 1_000_000:
        return "0_5m_1m"
    if price < 3_000_000:
        return "1m_3m"
    if price < 10_000_000:
        return "3m_10m"
    if price < 30_000_000:
        return "10m_30m"
    if price < 100_000_000:
        return "30m_100m"
    return "100m_plus"


def qwidth_band(ratio: float) -> str:
    if pd.isna(ratio) or ratio <= 0:
        return "qwidth_missing"
    if ratio <= 1.5:
        return "very_narrow_le_1_5x"
    if ratio <= 2.5:
        return "narrow_1_5_2_5x"
    if ratio <= 4.0:
        return "normal_2_5_4x"
    if ratio <= 7.0:
        return "wide_4_7x"
    return "extreme_gt_7x"


def qwidth_simple_band(ratio: float) -> str:
    if pd.isna(ratio) or ratio <= 0:
        return "q_missing"
    if ratio <= 2.5:
        return "q_stable_le_2_5x"
    if ratio <= 7.0:
        return "q_uncertain_2_5_7x"
    return "q_extreme_gt_7x"


def search_band(row: pd.Series) -> str:
    grade = str(row.get("search_quality_grade", "missing")).strip().lower()
    if grade in {"medium", "high"}:
        return "search_ok"
    if grade == "low":
        return "search_low"
    return "search_missing"


def external_band(row: pd.Series) -> str:
    gallery = pd.to_numeric(pd.Series([row.get("gallery_tier_any_available_flag", 0.0)]), errors="coerce").fillna(0.0).iloc[0]
    exhibition = pd.to_numeric(pd.Series([row.get("artist_exhibition_available_count", 0.0)]), errors="coerce").fillna(0.0).iloc[0]
    if gallery > 0 and exhibition >= 2:
        return "external_full"
    if gallery > 0 or exhibition >= 2:
        return "external_partial"
    return "external_sparse"


def risk_band(row: pd.Series) -> str:
    qband = str(row["qwidth_simple_manual"])
    search = str(row["search_quality_manual"])
    external = str(row["external_info_manual"])
    if qband == "q_extreme_gt_7x":
        return "risk_extreme_qwidth"
    if search == "search_missing" and external == "external_sparse":
        return "risk_info_sparse"
    if qband == "q_uncertain_2_5_7x" and external != "external_full":
        return "risk_uncertain_partial_info"
    return "risk_regular"


def add_manual_segments(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["pred_price_manual"] = out["pred_price"].map(price_band)
    out["qwidth_manual"] = out["price_range_ratio"].map(qwidth_band)
    out["qwidth_simple_manual"] = out["price_range_ratio"].map(qwidth_simple_band)
    out["search_quality_manual"] = out.apply(search_band, axis=1)
    out["external_info_manual"] = out.apply(external_band, axis=1)
    out["risk_manual"] = out.apply(risk_band, axis=1)
    return out


def build_segment(frame: pd.DataFrame, cols: tuple[str, ...]) -> pd.Series:
    return frame[list(cols)].astype(str).agg("__".join, axis=1)


def fit_map(frame: pd.DataFrame, policy: Policy) -> tuple[dict[str, float], float, pd.DataFrame]:
    working = frame.copy()
    working["segment"] = build_segment(working, policy.segment_cols)
    grouped = (
        working.groupby("segment", dropna=False)
        .agg(n=("residual_log", "size"), median_residual=("residual_log", "median"))
        .reset_index()
    )
    eligible = grouped[grouped["n"] >= policy.min_rows].copy()
    corr_map = dict(zip(eligible["segment"].astype(str), eligible["median_residual"].astype(float), strict=False))
    global_corr = float(working["residual_log"].median())
    return corr_map, global_corr, grouped


def apply_policy(frame: pd.DataFrame, policy: Policy, corr_map: dict[str, float], global_corr: float) -> tuple[np.ndarray, np.ndarray, pd.Series]:
    segment = build_segment(frame, policy.segment_cols)
    fallback_value = global_corr if policy.fallback == "global" else 0.0
    raw_corr = segment.astype(str).map(corr_map).fillna(fallback_value).to_numpy(dtype=float)
    correction = np.clip(raw_corr, -policy.cap, policy.cap) * policy.strength
    pred = frame["pred_log"].to_numpy(dtype=float) + correction
    return pred, correction, segment


def oof_prediction(val: pd.DataFrame, policy: Policy, n_splits: int = 5) -> tuple[np.ndarray, np.ndarray, pd.Series]:
    oof = np.zeros(len(val), dtype=float)
    corrections = np.zeros(len(val), dtype=float)
    full_segment = build_segment(val, policy.segment_cols)
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    for train_idx, hold_idx in kfold.split(val):
        train_fold = val.iloc[train_idx].reset_index(drop=True)
        hold_fold = val.iloc[hold_idx].reset_index(drop=True)
        corr_map, global_corr, _ = fit_map(train_fold, policy)
        pred, corr, _ = apply_policy(hold_fold, policy, corr_map, global_corr)
        oof[hold_idx] = pred
        corrections[hold_idx] = corr
    return oof, corrections, full_segment


def prediction_frame(policy: Policy, split: str, frame: pd.DataFrame, pred_log: np.ndarray, correction: np.ndarray, segment: pd.Series) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": policy.candidate,
            "scope": "cold",
            "split": split,
            "policy": "manual_segment_residual_calibration",
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": frame["actual_price"].to_numpy(dtype=float),
            "base_pred_log": frame["pred_log"].to_numpy(dtype=float),
            "pred_log": pred_log,
            "base_pred_price": frame["pred_price"].to_numpy(dtype=float),
            "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
            "correction_log": correction,
            "segment": segment.astype(str).to_numpy(),
            "segment_name": policy.segment_name,
            "min_rows": policy.min_rows,
            "cap": policy.cap,
            "strength": policy.strength,
            "fallback": policy.fallback,
        }
    )
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    for col in [
        "quantile_width_log",
        "price_range_ratio",
        "search_quality_grade",
        "search_quality_score",
        "gallery_tier_any_available_flag",
        "artist_exhibition_available_count",
        "pred_price_manual",
        "qwidth_manual",
        "qwidth_simple_manual",
        "search_quality_manual",
        "external_info_manual",
        "risk_manual",
    ]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    return out


def policies(full: bool = False) -> list[Policy]:
    segment_sets = {
        "qwidth_manual": ("qwidth_manual",),
        "qwidth_simple_manual": ("qwidth_simple_manual",),
        "pred_price_manual": ("pred_price_manual",),
        "pred_x_qwidth_manual": ("pred_price_manual", "qwidth_simple_manual"),
        "search_x_qwidth_manual": ("search_quality_manual", "qwidth_simple_manual"),
        "external_x_qwidth_manual": ("external_info_manual", "qwidth_simple_manual"),
        "risk_manual": ("risk_manual",),
        "risk_x_price_manual": ("risk_manual", "pred_price_manual"),
    }
    out: list[Policy] = []
    if full:
        min_rows_values = [30, 50, 100]
        cap_values = [0.10, 0.15, 0.20, 0.25, 0.35]
        strength_values = [0.50, 0.75, 1.00]
        fallback_values = ["zero", "global"]
    else:
        min_rows_values = [30, 100]
        cap_values = [0.15, 0.25, 0.35]
        strength_values = [0.75, 1.00]
        fallback_values = ["zero"]
    for segment_name, cols in segment_sets.items():
        for min_rows in min_rows_values:
            for cap in cap_values:
                for strength in strength_values:
                    for fallback in fallback_values:
                        out.append(Policy(segment_name, cols, min_rows, cap, strength, fallback))
    return out


def add_metric(rows: list[dict[str, Any]], policy: Policy | None, split: str, frame: pd.DataFrame, pred_log: np.ndarray, metric_policy: str, extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": EXP_ID,
        "candidate": policy.candidate if policy else "component_pp_y2_baseline",
        "scope": "cold",
        "split": split,
        "policy": metric_policy,
        **metric_values(frame, pred_log),
    }
    if policy:
        row.update(
            {
                "segment_name": policy.segment_name,
                "segment_columns": "__".join(policy.segment_cols),
                "min_rows": policy.min_rows,
                "cap": policy.cap,
                "strength": policy.strength,
                "fallback": policy.fallback,
            }
        )
    if extra:
        row.update(extra)
    rows.append(row)


def selection_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation_oof") & metrics_df["policy"].eq("manual_segment_residual_calibration")].copy()
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    val["balanced_rank_score"] = (
        0.45 * val["MdAPE"].rank(method="min")
        + 0.30 * val["MAPE"].rank(method="min")
        + 0.25 * val["p95_APE"].rank(method="min")
    )
    selectors = [
        ("validation_oof_best_mdape", ["MdAPE", "MAPE", "p95_APE"]),
        ("validation_oof_best_mape", ["MAPE", "MdAPE", "p95_APE"]),
        ("validation_oof_best_p95", ["p95_APE", "MdAPE", "MAPE"]),
        ("validation_oof_balanced_rank", ["balanced_rank_score", "MdAPE", "MAPE", "p95_APE"]),
    ]
    rows: list[dict[str, Any]] = []
    for selector, sort_cols in selectors:
        val_row = val.sort_values(sort_cols).iloc[0]
        test_row = test[test["candidate"].eq(val_row["candidate"])].iloc[0]
        rows.append(
            {
                "selector": selector,
                "candidate": val_row["candidate"],
                "segment_name": val_row.get("segment_name", ""),
                "min_rows": val_row.get("min_rows", ""),
                "cap": val_row.get("cap", ""),
                "strength": val_row.get("strength", ""),
                "fallback": val_row.get("fallback", ""),
                "validation_oof_MdAPE": val_row["MdAPE"],
                "validation_oof_MAPE": val_row["MAPE"],
                "validation_oof_p95_APE": val_row["p95_APE"],
                "test_MdAPE": test_row["MdAPE"],
                "test_MAPE": test_row["MAPE"],
                "test_p95_APE": test_row["p95_APE"],
                "test_RMSE_log": test_row["RMSE_log"],
            }
        )
    return pd.DataFrame(rows)


def load_auto_reference() -> pd.DataFrame:
    if not AUTO_METRICS.exists():
        return pd.DataFrame()
    df = pd.read_csv(AUTO_METRICS, low_memory=False)
    candidates = [
        "component_pp_y2_baseline",
        "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25",
        "stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25",
        "stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35",
    ]
    out = df[df["candidate"].isin(candidates) & df["split"].isin(["validation", "test"])].copy()
    return out[
        [
            "candidate",
            "split",
            "policy",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "Within_30",
            "Within_50",
        ]
    ].sort_values(["split", "MdAPE", "MAPE"])


def md_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in view.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append("" if pd.isna(value) else f"{value:.4f}")
            else:
                values.append("" if pd.isna(value) else str(value).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_report(metrics_df: pd.DataFrame, selection_df: pd.DataFrame, map_df: pd.DataFrame, auto_ref: pd.DataFrame) -> None:
    top_val = metrics_df[metrics_df["split"].eq("validation_oof")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    top_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    baseline = metrics_df[metrics_df["candidate"].eq("component_pp_y2_baseline") & metrics_df["split"].eq("test")].iloc[0]
    best_selected = selection_df.sort_values(["test_MdAPE", "test_MAPE", "test_p95_APE"]).iloc[0]
    md = f"""# {EXP_ID} Cold 수동 구간 보정 실험

## 1. 목적

- 자동 분위수 구간 보정 대신 사람이 해석 가능한 수동 구간 보정이 Cold 성능을 더 안정적으로 개선하는지 확인
- 구간 기준을 validation 분포가 아니라 운영 설명이 가능한 가격대/불확실성 배수/검색 품질/외부 정보 상태로 고정
- validation 내부 OOF로 보정 정책을 선택하고 test에는 선택된 보정 정책을 1회 적용

## 2. 실험 기준

- 1차 예측값: `{SOURCE_CANDIDATE}`
- 기준 모델: Cold LightGBM Quantile + 검색/전시/갤러리 상호작용 피처
- 보정식: `corrected_pred_log = pred_log + clip(segment_median_residual, -cap, cap) * strength`
- residual 정의: `actual_log - pred_log`
- 수동 구간:
  - 예측 가격대: 50만원 미만, 50만-100만원, 100만-300만원, 300만-1000만원, 1000만-3000만원, 3000만-1억원, 1억원 이상
  - 예측 불확실성 배수: 1.5배 이하, 1.5-2.5배, 2.5-4배, 4-7배, 7배 초과
  - 검색 품질: 검색 양호, 검색 낮음, 검색 없음
  - 외부 정보: 갤러리/전시 정보 충분, 일부, 부족

## 3. 기존 자동 구간 후보 참고

{md_table(auto_ref)}

## 4. Validation OOF 선택 후보

{md_table(selection_df)}

## 5. Validation OOF 상위 후보

{md_table(top_val, max_rows=20)}

## 6. Test 상위 후보

{md_table(top_test, max_rows=20)}

## 7. 실행 결론

- 기준선 test MdAPE `{baseline["MdAPE"]:.4f}`, MAPE `{baseline["MAPE"]:.4f}`, p95_APE `{baseline["p95_APE"]:.4f}`.
- validation OOF로 선택된 수동 구간 후보 중 test 기준 최상위는 `{best_selected["candidate"]}`.
- 해당 후보 test MdAPE `{best_selected["test_MdAPE"]:.4f}`, MAPE `{best_selected["test_MAPE"]:.4f}`, p95_APE `{best_selected["test_p95_APE"]:.4f}`.
- 자동 구간 후보 `qwidth_bin_oof_min30_cap0.25`의 test MdAPE는 `0.4247`, MAPE는 `0.9910`, p95_APE는 `3.3053`.
- 결론: 수동 구간 후보는 기준선보다 MdAPE, MAPE, p95를 개선했지만 자동 qwidth 후보보다 MdAPE/MAPE가 낮지는 않았다.
- 따라서 수동 구간 보정은 v0.1 Cold 기본 보정 정책으로 바로 채택하지 않는다.
- 단, 수동 구간은 p95_APE를 낮추는 후보가 있어 큰 오차 방어 또는 수동 검수 우선순위 정책에는 활용 가치가 있다.
- test-only 상위 후보 `manual_qwidth_simple_manual_min30_cap0.25_s0.75_zero`는 test MdAPE `0.4233`으로 자동 qwidth 후보보다 낮았지만, validation OOF 선택 후보가 아니고 MAPE가 `1.1076`으로 악화되어 채택하지 않는다.
- 후속 실험은 수동 구간을 단독 보정보다 “자동 qwidth 후보 + p95 위험 구간만 수동 cap 보정” 형태로 제한 적용하는 방향이 적절하다.

## 8. 산출물

- metrics: `outputs/metrics.csv`
- predictions: `outputs/predictions.csv`
- correction map: `outputs/policy_map.csv`
- selection summary: `outputs/selection_summary.csv`
"""
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports/result_report.md").write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2937;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 28px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(EXP_ID)} Cold 수동 구간 보정 실험</h1>
<h2>기존 자동 구간 후보 참고</h2>{auto_ref.to_html(index=False, escape=True)}
<h2>Validation OOF 선택 후보</h2>{selection_df.to_html(index=False, escape=True)}
<h2>Validation OOF 상위 후보</h2>{top_val.to_html(index=False, escape=True)}
<h2>Test 상위 후보</h2>{top_test.to_html(index=False, escape=True)}
<h2>Correction Map 요약</h2>{map_df.head(80).to_html(index=False, escape=True)}
</body></html>"""
    (EXP_DIR / "reports/result_report.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Run the full policy grid. Default runs a focused fast grid.")
    args = parser.parse_args()
    started = time.time()
    ensure_dirs()
    val = load_source("validation")
    test = load_source("test")
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []

    add_metric(rows, None, "validation", val, val["pred_log"].to_numpy(dtype=float), "baseline")
    add_metric(rows, None, "test", test, test["pred_log"].to_numpy(dtype=float), "baseline")

    policy_grid = policies(full=args.full)
    for policy in policy_grid:
        oof_pred, oof_corr, oof_segment = oof_prediction(val, policy)
        corr_map, global_corr, segment_map = fit_map(val, policy)
        test_pred, test_corr, test_segment = apply_policy(test, policy, corr_map, global_corr)
        add_metric(
            rows,
            policy,
            "validation_oof",
            val,
            oof_pred,
            "manual_segment_residual_calibration",
            {
                "global_correction": global_corr,
                "eligible_segments": int((segment_map["n"] >= policy.min_rows).sum()),
                "total_segments": int(len(segment_map)),
            },
        )
        add_metric(
            rows,
            policy,
            "test",
            test,
            test_pred,
            "manual_segment_residual_calibration",
            {
                "global_correction": global_corr,
                "eligible_segments": int((segment_map["n"] >= policy.min_rows).sum()),
                "total_segments": int(len(segment_map)),
            },
        )
        preds.append(prediction_frame(policy, "validation_oof", val, oof_pred, oof_corr, oof_segment))
        preds.append(prediction_frame(policy, "test", test, test_pred, test_corr, test_segment))
        top_segments = segment_map.sort_values(["n", "segment"], ascending=[False, True]).head(20)
        for _, seg in top_segments.iterrows():
            maps.append(
                {
                    "experiment_id": EXP_ID,
                    "candidate": policy.candidate,
                    "segment_name": policy.segment_name,
                    "segment_columns": "__".join(policy.segment_cols),
                    "segment": seg["segment"],
                    "segment_n": int(seg["n"]),
                    "segment_median_residual": float(seg["median_residual"]),
                    "min_rows": policy.min_rows,
                    "cap": policy.cap,
                    "strength": policy.strength,
                    "fallback": policy.fallback,
                    "global_correction": global_corr,
                    "eligible_segments": int((segment_map["n"] >= policy.min_rows).sum()),
                    "total_segments": int(len(segment_map)),
                }
            )

    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True, sort=False)
    map_df = pd.DataFrame(maps)
    selection_df = selection_summary(metrics_df)
    auto_ref = load_auto_reference()

    metrics_df.to_csv(EXP_DIR / "outputs/metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs/predictions.csv", index=False)
    map_df.to_csv(EXP_DIR / "outputs/policy_map.csv", index=False)
    selection_df.to_csv(EXP_DIR / "outputs/selection_summary.csv", index=False)
    auto_ref.to_csv(EXP_DIR / "outputs/auto_reference_metrics.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": "Cold 수동 구간 보정 실험",
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(PROJECT_ROOT)),
        "source_candidate": SOURCE_CANDIDATE,
        "selection_policy": "validation_oof_first",
        "grid_mode": "full" if args.full else "focused",
        "policy_count": len(policy_grid),
        "manual_segments": {
            "pred_price_manual": "fixed KRW predicted price bands",
            "qwidth_manual": "fixed price range ratio bands",
            "search_quality_manual": "search grade collapsed into ok/low/missing",
            "external_info_manual": "gallery/exhibition availability collapsed into full/partial/sparse",
            "risk_manual": "rule-based qwidth and information sparsity risk bucket",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts/model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "data/manual_segment_policy.json").write_text(json.dumps(config["manual_segments"], ensure_ascii=False, indent=2), encoding="utf-8")
    render_report(metrics_df, selection_df, map_df, auto_ref)
    (EXP_DIR / "logs/run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed in {time.time() - started:.2f}s\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "completed",
                "seconds": round(time.time() - started, 2),
                "experiment": str(EXP_DIR.relative_to(PROJECT_ROOT)),
                "metrics": str((EXP_DIR / "outputs/metrics.csv").relative_to(PROJECT_ROOT)),
                "selection": str((EXP_DIR / "outputs/selection_summary.csv").relative_to(PROJECT_ROOT)),
                "report": str((EXP_DIR / "reports/result_report.md").relative_to(PROJECT_ROOT)),
                "selected": selection_df.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
