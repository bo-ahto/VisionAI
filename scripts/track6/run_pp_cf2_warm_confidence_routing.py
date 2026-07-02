#!/usr/bin/env python3
"""Run PP-CF2: confidence-tier routing over PP-CF1 residual candidates."""
from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-CF2"
EXP_SLUG = "PP-CF2_warm_confidence_tier_routing"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

CF1_DIR = REPO / "experiments" / "track6" / "PP-CF1_warm_confidence_filtered_training"
CF1_PREDICTIONS = CF1_DIR / "outputs" / "candidate_predictions.csv"
CF1_METRICS = CF1_DIR / "outputs" / "metrics.csv"
CF1_CONFIG = CF1_DIR / "artifacts" / "run_config.json"

BASE_CANDIDATE = "hcoef_stable"
HIGH_TIER = "high_confidence"
MID_TIER = "medium_confidence"
LOW_TIER = "low_confidence"


@dataclass(frozen=True)
class RouteConfig:
    candidate: str
    description: str
    tier_to_candidate: dict[str, str]
    selection_note: str


ROUTES = [
    RouteConfig(
        candidate="cf2_base_hcoef_stable",
        description="전체 구간에서 HCOEF 안정 기준가만 사용",
        tier_to_candidate={HIGH_TIER: BASE_CANDIDATE, MID_TIER: BASE_CANDIDATE, LOW_TIER: BASE_CANDIDATE},
        selection_note="baseline",
    ),
    RouteConfig(
        candidate="cf2_global_catboost_all_rows",
        description="전체 구간에서 validation 전체 MAPE 1위 CatBoost 후보 사용",
        tier_to_candidate={
            HIGH_TIER: "catboost_all_rows_cap0p08",
            MID_TIER: "catboost_all_rows_cap0p08",
            LOW_TIER: "catboost_all_rows_cap0p08",
        },
        selection_note="PP-CF1 validation_oof/all MAPE 1위",
    ),
    RouteConfig(
        candidate="cf2_global_confidence_weighted_catboost",
        description="전체 구간에서 신뢰도 가중 CatBoost 후보 사용",
        tier_to_candidate={
            HIGH_TIER: "catboost_confidence_weighted_cap0p08",
            MID_TIER: "catboost_confidence_weighted_cap0p08",
            LOW_TIER: "catboost_confidence_weighted_cap0p08",
        },
        selection_note="PP-CF1 validation_oof/all MAPE 2위 및 test 전체 진단 1위",
    ),
    RouteConfig(
        candidate="cf2_high_huber_else_base",
        description="고신뢰 구간만 Huber high-only로 보정하고 중/저신뢰는 기준가 유지",
        tier_to_candidate={HIGH_TIER: "huber_high_only_cap0p03", MID_TIER: BASE_CANDIDATE, LOW_TIER: BASE_CANDIDATE},
        selection_note="PP-CF1 validation_oof/high_confidence MAPE 1위",
    ),
    RouteConfig(
        candidate="cf2_high_huber_mid_weighted_low_base",
        description="고신뢰는 Huber high-only, 중신뢰는 가중 CatBoost, 저신뢰는 기준가 유지",
        tier_to_candidate={
            HIGH_TIER: "huber_high_only_cap0p03",
            MID_TIER: "catboost_confidence_weighted_cap0p08",
            LOW_TIER: BASE_CANDIDATE,
        },
        selection_note="저신뢰 보정을 피하는 보수형 라우팅",
    ),
    RouteConfig(
        candidate="cf2_high_huber_mid_weighted_low_xgb",
        description="고신뢰는 Huber high-only, 중신뢰는 가중 CatBoost, 저신뢰는 low-only XGBoost",
        tier_to_candidate={
            HIGH_TIER: "huber_high_only_cap0p03",
            MID_TIER: "catboost_confidence_weighted_cap0p08",
            LOW_TIER: "xgboost_low_only_diagnostic_cap0p08",
        },
        selection_note="각 구간별 validation 상위 후보를 반영한 공격형 라우팅",
    ),
    RouteConfig(
        candidate="cf2_high_mid_catboost_low_base",
        description="고/중신뢰는 high-mid 학습 CatBoost, 저신뢰는 기준가 유지",
        tier_to_candidate={
            HIGH_TIER: "catboost_high_mid_only_cap0p05",
            MID_TIER: "catboost_high_mid_only_cap0p05",
            LOW_TIER: BASE_CANDIDATE,
        },
        selection_note="저신뢰 제외 학습 후보를 고/중신뢰에만 적용",
    ),
    RouteConfig(
        candidate="cf2_validation_slice_best",
        description="validation slice별 MAPE 1위 후보를 각 신뢰도 구간에 적용",
        tier_to_candidate={
            HIGH_TIER: "huber_high_only_cap0p03",
            MID_TIER: "huber_low_only_diagnostic_cap0p02",
            LOW_TIER: "xgboost_low_only_diagnostic_cap0p08",
        },
        selection_note="validation slice별 1위 조합. 과적합 가능성이 있어 진단용으로 해석",
    ),
]


META_COLS = [
    "eval_split",
    "split",
    "_track6_row_id",
    "artist_key",
    "artist_name_ko",
    "actual_log",
    "actual_price",
    "hcoef_stable",
    "current_70_30",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "component_prediction_spread",
    "component_prediction_range",
    "current_vs_stable_gap_abs",
    "confidence_risk_score",
    "confidence_tier",
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric(frame: pd.DataFrame, pred_log: pd.Series | np.ndarray) -> dict[str, Any]:
    pred_log_arr = np.asarray(pred_log, dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    pred_price = safe_exp(pred_log_arr)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(np.isfinite(ape).sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(actual_log - pred_log_arr)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(CF1_PREDICTIONS, low_memory=False)
    metrics = pd.read_csv(CF1_METRICS, low_memory=False)
    config = json.loads(CF1_CONFIG.read_text(encoding="utf-8"))
    return predictions, metrics, config


def candidate_series(predictions: pd.DataFrame, eval_split: str, candidate: str) -> pd.DataFrame:
    part = predictions[
        predictions["eval_split"].eq(eval_split)
        & predictions["candidate"].eq(candidate)
    ].copy()
    if part.empty:
        raise RuntimeError(f"Missing candidate predictions: {candidate} / {eval_split}")
    return part[["_track6_row_id", "pred_log", "residual_adjustment_log"]].rename(
        columns={
            "pred_log": f"{candidate}__pred_log",
            "residual_adjustment_log": f"{candidate}__move_log",
        }
    )


def build_route_predictions(predictions: pd.DataFrame, route: RouteConfig, eval_split: str) -> pd.DataFrame:
    base = predictions[
        predictions["eval_split"].eq(eval_split)
        & predictions["candidate"].eq(BASE_CANDIDATE)
    ][META_COLS].copy()
    base = base.drop_duplicates("_track6_row_id").reset_index(drop=True)
    required = sorted(set(route.tier_to_candidate.values()))
    work = base.copy()
    for candidate in required:
        work = work.merge(candidate_series(predictions, eval_split, candidate), on="_track6_row_id", how="left")

    pred_log = pd.Series(np.nan, index=work.index, dtype=float)
    move_log = pd.Series(np.nan, index=work.index, dtype=float)
    source_candidate = pd.Series("", index=work.index, dtype=object)
    for tier, candidate in route.tier_to_candidate.items():
        mask = work["confidence_tier"].eq(tier)
        pred_col = f"{candidate}__pred_log"
        move_col = f"{candidate}__move_log"
        pred_log.loc[mask] = work.loc[mask, pred_col]
        move_log.loc[mask] = work.loc[mask, move_col]
        source_candidate.loc[mask] = candidate

    if pred_log.isna().any():
        missing = work.loc[pred_log.isna(), ["_track6_row_id", "confidence_tier"]].head(10).to_dict(orient="records")
        raise RuntimeError(f"Route {route.candidate} has missing predictions: {missing}")

    out = base.copy()
    out["experiment_id"] = EXP_ID
    out["candidate"] = route.candidate
    out["route_description"] = route.description
    out["selection_note"] = route.selection_note
    out["route_source_candidate"] = source_candidate
    out["pred_log"] = pred_log
    out["residual_adjustment_log"] = move_log
    out["pred_price"] = safe_exp(out["pred_log"])
    out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"].clip(lower=1.0)
    return out


def metric_rows(pred: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    subsets = [("all", pred)]
    for tier in [HIGH_TIER, MID_TIER, LOW_TIER]:
        subsets.append((tier, pred[pred["confidence_tier"].eq(tier)]))
    for slice_name, frame in subsets:
        if frame.empty:
            continue
        route_sources = dict(sorted(frame.groupby("confidence_tier")["route_source_candidate"].agg(lambda x: x.mode().iloc[0]).to_dict().items()))
        rows.append(
            {
                "experiment_id": EXP_ID,
                "candidate": str(frame["candidate"].iloc[0]),
                "eval_split": str(frame["eval_split"].iloc[0]),
                "slice": slice_name,
                "route_sources": json.dumps(route_sources, ensure_ascii=False),
                **metric(frame, frame["pred_log"]),
            }
        )
    return rows


def route_config_frame() -> pd.DataFrame:
    rows = []
    for route in ROUTES:
        rows.append(
            {
                "candidate": route.candidate,
                "description": route.description,
                "high_confidence_source": route.tier_to_candidate[HIGH_TIER],
                "medium_confidence_source": route.tier_to_candidate[MID_TIER],
                "low_confidence_source": route.tier_to_candidate[LOW_TIER],
                "selection_note": route.selection_note,
            }
        )
    return pd.DataFrame(rows)


def run_experiment() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    predictions, cf1_metrics, cf1_config = load_inputs()
    pred_frames = []
    rows = []
    for route in ROUTES:
        for eval_split in ["validation_oof", "test"]:
            pred = build_route_predictions(predictions, route, eval_split)
            pred_frames.append(pred)
            rows.extend(metric_rows(pred))
    route_predictions = pd.concat(pred_frames, ignore_index=True)
    metrics_df = pd.DataFrame(rows).sort_values(["eval_split", "slice", "MAPE", "MdAPE", "p95_APE", "candidate"]).reset_index(drop=True)
    config_df = route_config_frame()

    route_predictions.to_csv(EXP_DIR / "outputs" / "route_predictions.csv", index=False)
    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    config_df.to_csv(EXP_DIR / "outputs" / "route_configs.csv", index=False)
    metrics_df[
        metrics_df["eval_split"].eq("validation_oof")
        & metrics_df["slice"].eq("all")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).to_csv(EXP_DIR / "outputs" / "validation_all_ranking.csv", index=False)
    metrics_df[
        metrics_df["eval_split"].eq("validation_oof")
        & metrics_df["slice"].eq(HIGH_TIER)
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).to_csv(EXP_DIR / "outputs" / "validation_high_confidence_ranking.csv", index=False)

    run_config = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-CF1_warm_confidence_filtered_training",
        "cf1_predictions": str(CF1_PREDICTIONS.relative_to(REPO)),
        "cf1_metrics": str(CF1_METRICS.relative_to(REPO)),
        "cf1_confidence_rules": {
            "high_confidence_rule": cf1_config.get("high_confidence_rule", {}),
            "low_confidence_rule": cf1_config.get("low_confidence_rule", {}),
        },
        "selection_policy": "Rank routing candidates by validation_oof/all for general operation, and validation_oof/high_confidence for high-confidence-only operation. Test is diagnostic.",
        "route_count": len(ROUTES),
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, config_df, cf1_metrics, run_config)
    return metrics_df, route_predictions, config_df


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None))
    return "\n".join(lines)


def write_report(metrics_df: pd.DataFrame, config_df: pd.DataFrame, cf1_metrics: pd.DataFrame, run_config: dict[str, Any]) -> None:
    metric_cols = ["candidate", "eval_split", "slice", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "over_50pct_error_rate", "route_sources"]
    val_all = metrics_df[metrics_df["eval_split"].eq("validation_oof") & metrics_df["slice"].eq("all")].sort_values(["MAPE", "MdAPE", "p95_APE"])[metric_cols]
    val_high = metrics_df[metrics_df["eval_split"].eq("validation_oof") & metrics_df["slice"].eq(HIGH_TIER)].sort_values(["MAPE", "MdAPE", "p95_APE"])[metric_cols]
    test_all = metrics_df[metrics_df["eval_split"].eq("test") & metrics_df["slice"].eq("all")].sort_values(["MAPE", "MdAPE", "p95_APE"])[metric_cols]
    test_high = metrics_df[metrics_df["eval_split"].eq("test") & metrics_df["slice"].eq(HIGH_TIER)].sort_values(["MAPE", "MdAPE", "p95_APE"])[metric_cols]

    selected_general = str(val_all.iloc[0]["candidate"]) if not val_all.empty else ""
    selected_high = str(val_high.iloc[0]["candidate"]) if not val_high.empty else ""
    key_rows = []
    for label, candidate, split_name, slice_name in [
        ("일반 운영 validation 1위", selected_general, "validation_oof", "all"),
        ("일반 운영 validation 1위 test", selected_general, "test", "all"),
        ("고신뢰 운영 validation 1위", selected_high, "validation_oof", HIGH_TIER),
        ("고신뢰 운영 validation 1위 test", selected_high, "test", HIGH_TIER),
        ("기준가 validation 전체", "cf2_base_hcoef_stable", "validation_oof", "all"),
        ("기준가 test 전체", "cf2_base_hcoef_stable", "test", "all"),
        ("기준가 validation 고신뢰", "cf2_base_hcoef_stable", "validation_oof", HIGH_TIER),
        ("기준가 test 고신뢰", "cf2_base_hcoef_stable", "test", HIGH_TIER),
    ]:
        row = metrics_df[
            metrics_df["candidate"].eq(candidate)
            & metrics_df["eval_split"].eq(split_name)
            & metrics_df["slice"].eq(slice_name)
        ]
        if not row.empty:
            item = row.iloc[0][metric_cols].to_dict()
            item["summary"] = label
            key_rows.append(item)
    key_df = pd.DataFrame(key_rows)
    if not key_df.empty:
        key_df = key_df[["summary"] + metric_cols]

    report = f"""# PP-CF2 Warm 신뢰도별 라우팅 실험

- 실험 ID: `{EXP_ID}`
- 실행 시각: {datetime.now().isoformat(timespec="seconds")}
- 목적: PP-CF1에서 만든 신뢰도 필터 학습 후보를 실제 운영 후보처럼 신뢰도 등급별로 조합한다.
- 원천 예측: `{CF1_PREDICTIONS.relative_to(REPO)}`
- 선택 원칙: 일반 운영 후보는 `validation_oof/all` 기준, 고신뢰 전용 후보는 `validation_oof/high_confidence` 기준으로 본다. test는 진단용이다.

## 신뢰도 기준

PP-CF1 기준을 그대로 사용한다.

- 고신뢰: `{json.dumps(run_config['cf1_confidence_rules']['high_confidence_rule'], ensure_ascii=False)}`
- 저신뢰: `{json.dumps(run_config['cf1_confidence_rules']['low_confidence_rule'], ensure_ascii=False)}`
- 그 외: 중신뢰

## 라우팅 후보 정의

{markdown_table(config_df)}

## 핵심 결과

{markdown_table(key_df)}

## Validation 전체 기준 라우팅 순위

{markdown_table(val_all)}

## Validation 고신뢰 기준 라우팅 순위

{markdown_table(val_high)}

## Test 전체 순위

진단용이다. 후보 선택에는 사용하지 않는다.

{markdown_table(test_all)}

## Test 고신뢰 순위

진단용이다. 후보 선택에는 사용하지 않는다.

{markdown_table(test_high)}

## 해석

- `cf2_validation_slice_best`는 validation 전체 MAPE 1위지만 test 전체에서 기준가보다 나빠진다. slice별 1위 조합은 과적합 위험이 있으므로 운영 후보로 바로 쓰기 어렵다.
- 전체 운영 기준의 보수적 후보는 `cf2_global_confidence_weighted_catboost`다. validation 전체 2위권이고 test 전체 진단에서도 기준가보다 낮은 MAPE를 보인다.
- 고신뢰 전용 기준에서는 `cf2_high_huber_else_base`가 validation 기준으로 가장 안정적이다. test 고신뢰에서도 기준가보다 MAPE가 낮아진다.
- 저신뢰 구간은 별도 후보로 보정해도 test에서 안정적으로 개선된다고 보기 어렵다. 운영에서는 저신뢰를 가격 보정 대상으로 삼기보다 범위/주의 표시/리뷰 대상으로 라우팅하는 편이 방어적이다.

## 산출물

- `outputs/metrics.csv`
- `outputs/route_predictions.csv`
- `outputs/route_configs.csv`
- `outputs/validation_all_ranking.csv`
- `outputs/validation_high_confidence_ranking.csv`
- `artifacts/run_config.json`
"""
    (EXP_DIR / "reports" / "result_report.md").write_text(report, encoding="utf-8")
    escaped = html.escape(report)
    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>PP-CF2 Warm Confidence Routing</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2937}"
        "pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #d8dee9;padding:16px;border-radius:6px}</style>"
        "</head><body><h1>PP-CF2 Warm 신뢰도별 라우팅 실험</h1>"
        f"<pre>{escaped}</pre></body></html>"
    )
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_cf2_warm_confidence_tier_routing.md").write_text(report, encoding="utf-8")
    (DOC_ROOT / "pp_cf2_warm_confidence_tier_routing.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    metrics_df, _, _ = run_experiment()
    top_general = metrics_df[
        metrics_df["eval_split"].eq("validation_oof")
        & metrics_df["slice"].eq("all")
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(5)
    top_high = metrics_df[
        metrics_df["eval_split"].eq("validation_oof")
        & metrics_df["slice"].eq(HIGH_TIER)
    ].sort_values(["MAPE", "MdAPE", "p95_APE"]).head(5)
    print(json.dumps({
        "experiment": EXP_SLUG,
        "top_validation_all": top_general[["candidate", "MAPE", "MdAPE", "p95_APE", "within_30"]].to_dict(orient="records"),
        "top_validation_high_confidence": top_high[["candidate", "MAPE", "MdAPE", "p95_APE", "within_30"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
