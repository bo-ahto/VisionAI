#!/usr/bin/env python3
"""Freeze the final Warm operational candidate from PP-OPT6.

This script creates a compact, reproducible final-model package:
metrics, predictions, model logic, configuration, and a standalone report.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_DIR = REPO / "experiments" / "track6" / "PP-OPT7_warm_final_operational_freeze"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

OPT5_AGG = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT5_warm_focused_repeated_validation"
    / "outputs"
    / "aggregate_candidate_stability.csv"
)
OPT6_METRICS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT6_warm_p95_guard_refinement"
    / "outputs"
    / "full_guard_metrics.csv"
)
OPT6_AGG = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT6_warm_p95_guard_refinement"
    / "outputs"
    / "aggregate_guard_stability.csv"
)
OPT6_PREDS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT6_warm_p95_guard_refinement"
    / "outputs"
    / "selected_guard_predictions.csv"
)

BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"
FINAL_MODEL_ID = "warm_catboost_artist_qcap_risk_strict_v1"
FINAL_CANDIDATE = (
    "p95guard__seed=combo_cat=cb_tier=same__qmult=same__cap=0p02__caprof=qcap_balanced__s=1p0__"
    "artist=am_h_birth_gen_gn_a01_c03_s075__guard=risk_strict_cap0p020"
)
FINAL_SEED_CANDIDATE = (
    "combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__"
    "artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025"
)


def ensure_dirs() -> None:
    for path in (OUT_DIR, REPORT_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.6f}")
    headers = list(view.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def html_from_markdown(markdown: str) -> str:
    escaped = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-OPT7 Warm final operational freeze</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; line-height: 1.55; }}
    pre {{ white-space: pre-wrap; background: #f7f8fa; border: 1px solid #d8dee4; border-radius: 8px; padding: 18px; }}
  </style>
</head>
<body><pre>{escaped}</pre></body>
</html>
"""


def load_final_predictions() -> pd.DataFrame:
    keep = {BASE_CANDIDATE, REFERENCE_CANDIDATE, FINAL_CANDIDATE}
    df = pd.read_csv(OPT6_PREDS)
    out = df[df["candidate"].isin(keep)].copy()
    if out[out["candidate"] == FINAL_CANDIDATE].empty:
        raise ValueError("Final candidate predictions were not found in PP-OPT6 selected predictions")
    out["model_id"] = out["candidate"].map(
        {
            BASE_CANDIDATE: "baseline_hcoef_stable",
            REFERENCE_CANDIDATE: "reference_current_70_30",
            FINAL_CANDIDATE: FINAL_MODEL_ID,
        }
    )
    return out.sort_values(["model_id", "eval_split", "_track6_row_id"])


def load_metrics() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metrics = pd.read_csv(OPT6_METRICS)
    agg = pd.read_csv(OPT6_AGG)
    opt5 = pd.read_csv(OPT5_AGG)
    keep = {BASE_CANDIDATE, REFERENCE_CANDIDATE, FINAL_CANDIDATE}
    metric_cols = [
        "candidate",
        "family",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "Within_30",
        "Within_50",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "strict_all3_vs_base",
        "guarded_test_pass",
        "guarded_score",
    ]
    selected_metrics = metrics[metrics["candidate"].isin(keep)][metric_cols].copy()
    selected_metrics["model_id"] = selected_metrics["candidate"].map(
        {
            BASE_CANDIDATE: "baseline_hcoef_stable",
            REFERENCE_CANDIDATE: "reference_current_70_30",
            FINAL_CANDIDATE: FINAL_MODEL_ID,
        }
    )

    agg_cols = [
        "candidate",
        "family",
        "mean_delta_MdAPE",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "worst_scenario_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "mean_strict_all3_rate",
        "validation_delta_MAPE",
        "validation_delta_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_p95_validation_pass",
        "test_guarded_pass",
        "test_strict_all3",
        "operational_pass",
        "recommendation_score",
    ]
    selected_agg = agg[agg["candidate"] == FINAL_CANDIDATE][agg_cols].copy()
    selected_agg["model_id"] = FINAL_MODEL_ID

    seed_cols = [
        "candidate",
        "family",
        "mean_delta_MdAPE",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "mean_MAPE_improve_rate",
        "mean_p95_not_worse_rate",
        "mean_all3_improve_rate",
        "full_validation_delta_MAPE",
        "full_validation_delta_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "stable_validation_pass",
        "test_diagnostic_pass",
    ]
    seed_metrics = opt5[opt5["candidate"] == FINAL_SEED_CANDIDATE][seed_cols].copy()
    seed_metrics["model_id"] = "unguarded_seed_before_risk_strict_guard"
    return selected_metrics, selected_agg, seed_metrics


def logic_steps() -> pd.DataFrame:
    rows = [
        {
            "step": 1,
            "name": "기준 로그가격 생성",
            "formula": "기준로그가격 = HCOEF_안정기준로그가격",
            "description": "Warm/HCOEF 계열에서 선택한 안정 기준가를 사용한다. 이 값은 최종 예측의 중심값이다.",
        },
        {
            "step": 2,
            "name": "CatBoost 잔차 보정 생성",
            "formula": "CatBoost보정 = clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한)",
            "description": "confidence_weighted CatBoost 잔차 모델을 사용한다. qcap_balanced cap 0.02이므로 quantile_width가 1.6 이하이면 상한 0.02, 1.6 초과이면 상한 0.01을 적용한다.",
        },
        {
            "step": 3,
            "name": "작가 생년/세대 보정 생성",
            "formula": "작가보정 = clip(Huber(작가생년/세대 잔차), -0.03, +0.03) * 0.75",
            "description": "작가 생년과 세대 구간 기반 Huber 보정이다. 게이트 없이 전체 구간에 적용하며 alpha 0.01, cap 0.03, strength 0.75 조건을 사용한다. 실제 적용은 Huber 잔차를 먼저 cap으로 제한한 뒤 strength를 곱한다.",
        },
        {
            "step": 4,
            "name": "1차 합산 보정",
            "formula": "1차보정 = clip(1.0 * CatBoost보정 + 0.5 * 작가보정, -0.025, +0.025)",
            "description": "작품/신뢰도 기반 CatBoost 보정을 주 보정으로 쓰고, 작가 메타 보정은 절반 가중치로 보조한다.",
        },
        {
            "step": 5,
            "name": "위험 구간 판정",
            "formula": "고위험 = low_confidence OR quantile_width >= 1.65 OR component_spread >= 0.13 OR stable_gap >= 0.05 OR svc_group_n < 4",
            "description": "저신뢰, 넓은 가격구간, 모델 간 큰 불일치, 작은 유사작품 표본 수를 고위험으로 본다.",
        },
        {
            "step": 6,
            "name": "중위험 구간 판정",
            "formula": "중위험 = medium_confidence OR quantile_width >= 1.28 OR component_spread >= 0.08 OR stable_gap >= 0.025 OR svc_group_n < 8",
            "description": "고위험이 아니지만 불확실성이 있는 구간을 중위험으로 본다. 고위험 조건이 먼저 적용된다.",
        },
        {
            "step": 7,
            "name": "risk_strict 보정 축소",
            "formula": "위험계수 = 0.15 if 고위험 else 0.55 if 중위험 else 0.90",
            "description": "p95 악화를 줄이기 위해 불확실성이 클수록 보정값을 강하게 줄인다.",
        },
        {
            "step": 8,
            "name": "최종 보정",
            "formula": "최종보정 = clip(1차보정 * 위험계수, -0.020, +0.020)",
            "description": "최종 로그 보정값은 절대값 0.02 이내로 제한한다.",
        },
        {
            "step": 9,
            "name": "최종 가격 산출",
            "formula": "최종로그가격 = 기준로그가격 + 최종보정; 최종KRW가격 = exp(최종로그가격)",
            "description": "로그공간에서 보정 후 원화 가격으로 변환한다.",
        },
    ]
    return pd.DataFrame(rows)


def render_report(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    seed_metrics: pd.DataFrame,
    steps: pd.DataFrame,
    prediction_summary: pd.DataFrame,
) -> str:
    metric_view = metrics[
        [
            "model_id",
            "eval_split",
            "n",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "guarded_test_pass",
        ]
    ].sort_values(["eval_split", "model_id"])
    aggregate_view = aggregate[
        [
            "model_id",
            "mean_delta_MAPE",
            "mean_delta_p95_APE",
            "mean_MAPE_improve_rate",
            "mean_p95_not_worse_rate",
            "mean_strict_all3_rate",
            "test_delta_MdAPE",
            "test_delta_MAPE",
            "test_delta_p95_APE",
            "operational_pass",
        ]
    ]
    seed_view = seed_metrics[
        [
            "model_id",
            "mean_delta_MAPE",
            "mean_delta_p95_APE",
            "mean_MAPE_improve_rate",
            "mean_p95_not_worse_rate",
            "mean_all3_improve_rate",
            "test_delta_MdAPE",
            "test_delta_MAPE",
            "test_delta_p95_APE",
        ]
    ]
    prediction_view = prediction_summary[
        [
            "model_id",
            "eval_split",
            "rows",
            "mean_pred_price",
            "median_pred_price",
            "mean_abs_correction_log",
            "p95_abs_correction_log",
        ]
    ]
    return f"""# PP-OPT7 Warm 최종 운영 후보 고정

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 최종 모델 ID: `{FINAL_MODEL_ID}`
- 기준 후보: `{BASE_CANDIDATE}`
- 최종 후보: `{FINAL_CANDIDATE}`
- 원 seed 후보: `{FINAL_SEED_CANDIDATE}`

## 1. 선정 이유

- PP-OPT6 운영 조건을 통과했다.
- fixed test에서 MdAPE와 MAPE가 개선됐다.
- fixed test p95 악화가 0.002 이하로 제한됐다.
- 반복 validation에서 MAPE 개선률이 100%였고 p95 비악화율이 65% 수준이었다.
- OPT5 seed 대비 p95 악화 폭을 줄이면서 실사용 가능한 성능 개선을 유지했다.

## 2. 최종 성능

{markdown_table(metric_view, 20)}

## 3. 반복 검증 안정성

{markdown_table(aggregate_view, 10)}

## 4. Guard 적용 전 seed 성능

{markdown_table(seed_view, 10)}

## 5. 예측값 요약

{markdown_table(prediction_view, 20)}

## 6. 최종 예측 로직

{markdown_table(steps, 20)}

## 7. 핵심 수식

```text
CatBoost보정 = clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한)

작가보정 = clip(Huber(작가생년/세대 잔차), -0.03, +0.03) * 0.75

1차보정 = clip(1.0 * CatBoost보정 + 0.5 * 작가보정, -0.025, +0.025)

고위험 = low_confidence
      OR quantile_width >= 1.65
      OR component_prediction_spread >= 0.13
      OR current_vs_stable_gap_abs >= 0.05
      OR svc_group_n < 4

중위험 = medium_confidence
      OR quantile_width >= 1.28
      OR component_prediction_spread >= 0.08
      OR current_vs_stable_gap_abs >= 0.025
      OR svc_group_n < 8

위험계수 = 0.15 if 고위험 else 0.55 if 중위험 else 0.90

최종보정 = clip(1차보정 * 위험계수, -0.020, +0.020)

최종로그가격 = 기준로그가격 + 최종보정

최종KRW가격 = exp(최종로그가격)
```

## 8. 재현 실행

```bash
python3 scripts/track6/run_pp_opt7_warm_final_operational_freeze.py
```

## 9. 산출물

- `outputs/final_candidate_predictions.csv`
- `outputs/final_candidate_metrics.csv`
- `outputs/final_candidate_stability.csv`
- `outputs/final_logic_steps.csv`
- `outputs/final_prediction_summary.csv`
- `reports/final_model_report.md`
- `reports/final_model_report.html`
- `artifacts/final_model_config.json`
"""


def main() -> None:
    ensure_dirs()
    predictions = load_final_predictions()
    metrics, aggregate, seed_metrics = load_metrics()
    steps = logic_steps()

    prediction_summary = (
        predictions.groupby(["model_id", "eval_split"])
        .agg(
            rows=("_track6_row_id", "count"),
            mean_pred_price=("pred_price", "mean"),
            median_pred_price=("pred_price", "median"),
            mean_abs_correction_log=("correction_log", lambda s: float(pd.to_numeric(s, errors="coerce").abs().mean())),
            p95_abs_correction_log=("correction_log", lambda s: float(pd.to_numeric(s, errors="coerce").abs().quantile(0.95))),
        )
        .reset_index()
    )

    predictions.to_csv(OUT_DIR / "final_candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "final_candidate_metrics.csv", index=False)
    aggregate.to_csv(OUT_DIR / "final_candidate_stability.csv", index=False)
    seed_metrics.to_csv(OUT_DIR / "final_seed_before_guard_metrics.csv", index=False)
    steps.to_csv(OUT_DIR / "final_logic_steps.csv", index=False)
    prediction_summary.to_csv(OUT_DIR / "final_prediction_summary.csv", index=False)

    report = render_report(metrics, aggregate, seed_metrics, steps, prediction_summary)
    (REPORT_DIR / "final_model_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "final_model_report.html").write_text(html_from_markdown(report), encoding="utf-8")

    config = {
        "experiment_id": "PP-OPT7",
        "final_model_id": FINAL_MODEL_ID,
        "base_candidate": BASE_CANDIDATE,
        "reference_candidate": REFERENCE_CANDIDATE,
        "final_candidate": FINAL_CANDIDATE,
        "final_seed_candidate_before_guard": FINAL_SEED_CANDIDATE,
        "formula": {
            "catboost_correction": "clip(raw_catboost_residual, -dynamic_qcap, +dynamic_qcap)",
            "artist_correction": "clip(huber_birth_generation_residual, -0.03, +0.03) * 0.75",
            "pre_guard_correction": "clip(1.0 * catboost_correction + 0.5 * artist_correction, -0.025, +0.025)",
            "risk_multiplier": "0.15 if high_risk else 0.55 if medium_risk else 0.90",
            "final_correction": "clip(pre_guard_correction * risk_multiplier, -0.020, +0.020)",
            "final_log_price": "base_log_price + final_correction",
            "final_krw_price": "exp(final_log_price)",
        },
        "risk_thresholds": {
            "high_risk": {
                "confidence_tier": "low_confidence",
                "quantile_width_gte": 1.65,
                "component_prediction_spread_gte": 0.13,
                "current_vs_stable_gap_abs_gte": 0.05,
                "svc_group_n_lt": 4,
            },
            "medium_risk": {
                "confidence_tier": "medium_confidence",
                "quantile_width_gte": 1.28,
                "component_prediction_spread_gte": 0.08,
                "current_vs_stable_gap_abs_gte": 0.025,
                "svc_group_n_lt": 8,
            },
        },
        "sources": {
            "opt5_aggregate": str(OPT5_AGG.relative_to(REPO)),
            "opt6_metrics": str(OPT6_METRICS.relative_to(REPO)),
            "opt6_aggregate": str(OPT6_AGG.relative_to(REPO)),
            "opt6_predictions": str(OPT6_PREDS.relative_to(REPO)),
        },
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (ARTIFACT_DIR / "final_model_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nFinal metrics:")
    print(
        metrics[
            ["model_id", "eval_split", "n", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
