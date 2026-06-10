#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = ROOT / "experiments/track6/PP-WBASE1_warm_base_lock"
DATA_DIR = EXP_DIR / "data"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

FPOL3_OBJECTIVE = ROOT / "experiments/track6/PP-FPOL3_warm_policy_best_candidate_comparison/outputs/objective_best_summary.csv"
FPOL6_METRICS = ROOT / "experiments/track6/PP-FPOL6_directional_price_bin_guard/outputs/candidate_metrics.csv"
FPOL6_PREDS = ROOT / "experiments/track6/PP-FPOL6_directional_price_bin_guard/outputs/candidate_predictions.csv"
FPOL8_STABILITY = ROOT / "experiments/track6/PP-FPOL8_repeated_holdout_stability/outputs/final_stability_summary.csv"
FPOL9_12_RECS = ROOT / "experiments/track6/PP-FPOL9_12_remaining_method_batch/outputs/final_remaining_method_recommendations.csv"


RAW_BASE_ID = "WARM_BASE_RAW_V1"
RAW_BASE_NAME = "blend_svcnum_ppv8_wsvc_0.70 / base_pred_log"
MAPE_CHAMPION_ID = (
    "artist=huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p5"
    "__svc=PP-WHUBER7_pred_size_material_svc_artist_eps1.05_alpha0p01_dir_under_guard_cap0p08"
    "__totalcap=0.04__direction=under_guard__price=none"
)
BALANCED_CHAMPION_ID = (
    "artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08"
    "__totalcap=0.03__direction=none__price=mid_open_tail_guard"
)
P95_CHAMPION_ID = (
    "artist=none__svc=PP-WHUBER7_pred_size_svc_eps1.05_alpha0p001_dir_under_guard_cap0p08"
    "__totalcap=0.03__direction=under_guard__price=none"
)


def ensure_dirs() -> None:
    for path in [DATA_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def metrics(actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.exp(actual_log)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "n": int(len(ape)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        rows.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return "\n".join(rows)


def html_table(df: pd.DataFrame, cols: list[str]) -> str:
    rows = ["<table><thead><tr>"]
    rows.extend(f"<th>{html.escape(c)}</th>" for c in cols)
    rows.append("</tr></thead><tbody>")
    for _, row in df[cols].iterrows():
        rows.append("<tr>")
        rows.extend(f"<td>{html.escape(fmt(row[c]))}</td>" for c in cols)
        rows.append("</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def raw_base_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    preds = pd.read_csv(FPOL6_PREDS)
    base = preds.drop_duplicates(["split", "_track6_row_id"]).copy()
    base["fixed_base_id"] = RAW_BASE_ID
    base["fixed_base_name"] = RAW_BASE_NAME
    base["fixed_base_pred_log"] = base["base_pred_log"]
    base["fixed_base_pred_price"] = np.exp(base["fixed_base_pred_log"])
    base["fixed_base_residual_log"] = base["actual_log"] - base["fixed_base_pred_log"]
    base["fixed_base_ape"] = np.abs(base["fixed_base_pred_price"] - base["actual_price"]) / base["actual_price"]
    export_cols = [
        "split",
        "_track6_row_id",
        "fixed_base_id",
        "fixed_base_name",
        "artist_key",
        "artist_name_ko",
        "svc_reliability_bin",
        "pred_log_bin",
        "size_bin",
        "actual_log",
        "actual_price",
        "fixed_base_pred_log",
        "fixed_base_pred_price",
        "fixed_base_residual_log",
        "fixed_base_ape",
    ]
    base[export_cols].to_csv(DATA_DIR / "fixed_warm_base_validation_test_rows.csv", index=False)

    metric_rows = []
    for split, frame in base.groupby("split", sort=False):
        metric_rows.append(
            {
                "selection": f"{RAW_BASE_ID}_{split}",
                "role": "fixed_raw_base_for_future_modeling",
                "source": "REFERENCE",
                "candidate": RAW_BASE_NAME,
                "split": split,
                **metrics(frame["actual_log"].to_numpy(float), frame["fixed_base_pred_log"].to_numpy(float)),
                "delta_MdAPE": 0.0,
                "delta_MAPE": 0.0,
                "delta_p95_APE": 0.0,
                "balanced_delta": 0.0,
                "locked_for_future_modeling": True,
            }
        )
    return base, pd.DataFrame(metric_rows)


def fpol6_rows() -> pd.DataFrame:
    df = pd.read_csv(FPOL6_METRICS)
    test = df[df["split"].eq("test")].copy()
    selected = []
    for role, candidate in [
        ("current_mape_champion_for_comparison", MAPE_CHAMPION_ID),
        ("current_balanced_champion_for_guardrail", BALANCED_CHAMPION_ID),
        ("current_p95_champion_for_guardrail", P95_CHAMPION_ID),
    ]:
        row = test[test["candidate"].eq(candidate)].head(1).copy()
        row["selection"] = role
        row["role"] = role
        row["source"] = "PP-FPOL6"
        row["locked_for_future_modeling"] = False
        selected.append(row)
    out = pd.concat(selected, ignore_index=True)
    return out[
        [
            "selection",
            "role",
            "source",
            "candidate",
            "split",
            "RMSE_log",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "Within_30",
            "Within_50",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "balanced_delta",
            "locked_for_future_modeling",
        ]
    ]


def fpol3_rows() -> pd.DataFrame:
    df = pd.read_csv(FPOL3_OBJECTIVE)
    out = df.rename(
        columns={
            "objective": "selection",
            "test_RMSE_log": "RMSE_log",
            "test_MdAPE": "MdAPE",
            "test_MAPE": "MAPE",
            "test_p95_APE": "p95_APE",
            "test_delta_MdAPE": "delta_MdAPE",
            "test_delta_MAPE": "delta_MAPE",
            "test_delta_p95_APE": "delta_p95_APE",
            "test_balanced_delta": "balanced_delta",
        }
    ).copy()
    out["role"] = "previous_warm_huber_reference"
    out["split"] = "test"
    out["Within_30"] = np.nan
    out["Within_50"] = np.nan
    out["locked_for_future_modeling"] = False
    return out[
        [
            "selection",
            "role",
            "source",
            "candidate",
            "split",
            "RMSE_log",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "Within_30",
            "Within_50",
            "delta_MdAPE",
            "delta_MAPE",
            "delta_p95_APE",
            "balanced_delta",
            "locked_for_future_modeling",
        ]
    ]


def fpol9_12_rows() -> pd.DataFrame:
    df = pd.read_csv(FPOL9_12_RECS)
    out = df.copy()
    out["role"] = "remaining_method_reference"
    out["split"] = "test"
    out["locked_for_future_modeling"] = False
    cols = [
        "selection",
        "role",
        "source",
        "candidate",
        "split",
        "RMSE_log",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "Within_30",
        "Within_50",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "balanced_delta",
        "locked_for_future_modeling",
    ]
    return out[cols]


def stability_reference() -> pd.DataFrame:
    df = pd.read_csv(FPOL8_STABILITY)
    grouped = (
        df.groupby("candidate", as_index=False)
        .agg(
            stability_score=("stability_score", "mean"),
            bootstrap_improve_MAPE=("improvement_probability_MAPE", "mean"),
            bootstrap_improve_p95_APE=("improvement_probability_p95_APE", "mean"),
            fold_improve_MAPE=("fold_improvement_probability_MAPE", "mean"),
            fold_improve_p95_APE=("fold_improvement_probability_p95_APE", "mean"),
        )
        .sort_values(["stability_score", "bootstrap_improve_MAPE"], ascending=[False, False])
    )
    grouped.to_csv(OUTPUT_DIR / "warm_stability_reference.csv", index=False)
    return grouped


def write_report(summary: pd.DataFrame, stability: pd.DataFrame) -> None:
    cols = [
        "selection",
        "role",
        "source",
        "candidate",
        "split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "balanced_delta",
        "locked_for_future_modeling",
    ]
    report_rows = summary.copy()
    if "n" not in report_rows.columns:
        report_rows["n"] = np.nan
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# Warm 기준 성능 정리 및 Base 고정

- 작성일: {generated}
- 목적: 이후 CatBoost/XGBoost/LightGBM 등 다른 residual 모델 실험에서 기준 base가 흔들리지 않도록 고정한다.

## 고정 결정

1. **모델링용 raw base는 `{RAW_BASE_ID}`로 고정한다.**
   - source column: `PP-FPOL6_directional_price_bin_guard/outputs/candidate_predictions.csv`의 `base_pred_log`
   - 의미: 기존 Warm 70:30 계열 기준 로그 가격, FPOL/WHUBER 보정이 들어가기 전 기준값
   - residual target: `actual_log - fixed_base_pred_log`
2. **현재 성능 비교 champion은 FPOL6 후보로 별도 고정한다.**
   - MAPE champion: `{MAPE_CHAMPION_ID}`
   - balanced/p95 guardrail: `{BALANCED_CHAMPION_ID}`
3. 다른 모델 실험은 `{RAW_BASE_ID}`의 residual을 학습하고, 결과를 아래 두 기준과 모두 비교한다.
   - raw base 대비 개선폭
   - FPOL6 champion 대비 개선/악화 여부

## Warm 성능 요약

{md_table(report_rows, cols)}

## 안정성 참고 Top 8

{md_table(stability.head(8), ['candidate', 'stability_score', 'bootstrap_improve_MAPE', 'bootstrap_improve_p95_APE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}

## 다음 모델 실험 규칙

- base prediction은 항상 `fixed_base_pred_log`를 사용한다.
- residual target은 `actual_log - fixed_base_pred_log`로 둔다.
- Huber 계수나 FPOL6 보정값을 새 모델의 입력 target으로 쓰지 않는다.
- CatBoost/XGBoost/LightGBM 후보는 validation split에서 학습/튜닝하고, test split 607건은 최종 비교에만 사용한다.
- 성능 표는 최소 `MdAPE`, `MAPE`, `p95_APE`, `RMSE_log`, `Within_30`, `Within_50`을 포함한다.
- 최종 후보는 MAPE 단독이 아니라 `MAPE`, `p95_APE`, `balanced_delta`, 반복 안정성 순서로 판단한다.

## 산출물

- `data/fixed_warm_base_validation_test_rows.csv`
- `outputs/warm_base_performance_summary.csv`
- `outputs/warm_stability_reference.csv`
- `artifacts/warm_base_lock_manifest.json`
"""
    (REPORT_DIR / "warm_base_lock.md").write_text(md, encoding="utf-8")

    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>Warm Base Lock</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:#172033}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:16px 0 28px}}
th,td{{border:1px solid #d4d9e2;padding:6px 8px;vertical-align:top}}
th{{background:#edf2f7}}td{{word-break:break-word}}
code{{background:#f3f5f7;padding:1px 4px;border-radius:4px}}
</style></head><body>
<h1>Warm 기준 성능 정리 및 Base 고정</h1>
<p>작성일: {html.escape(generated)}</p>
<h2>고정 결정</h2>
<ul>
<li>모델링용 raw base: <code>{html.escape(RAW_BASE_ID)}</code></li>
<li>residual target: <code>actual_log - fixed_base_pred_log</code></li>
<li>현재 비교 champion: <code>PP-FPOL6</code></li>
</ul>
<h2>Warm 성능 요약</h2>
{html_table(report_rows, cols)}
<h2>안정성 참고 Top 8</h2>
{html_table(stability.head(8), ['candidate', 'stability_score', 'bootstrap_improve_MAPE', 'bootstrap_improve_p95_APE', 'fold_improve_MAPE', 'fold_improve_p95_APE'])}
</body></html>
"""
    (REPORT_DIR / "warm_base_lock.html").write_text(html_doc, encoding="utf-8")


def write_manifest(summary: pd.DataFrame) -> None:
    manifest = {
        "experiment_id": "PP-WBASE1_warm_base_lock",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "fixed_raw_base": {
            "id": RAW_BASE_ID,
            "name": RAW_BASE_NAME,
            "source_file": str(FPOL6_PREDS.relative_to(ROOT)),
            "source_column": "base_pred_log",
            "residual_target": "actual_log - fixed_base_pred_log",
            "modeling_split_policy": {
                "train_or_calibration": "validation split, 519 rows",
                "fixed_test": "test split, 607 rows",
            },
        },
        "comparison_champions": {
            "mape_champion": MAPE_CHAMPION_ID,
            "balanced_champion": BALANCED_CHAMPION_ID,
            "p95_champion": P95_CHAMPION_ID,
        },
        "next_experiment_rule": [
            "Do not change fixed_base_pred_log between model families.",
            "Train new residual models on actual_log - fixed_base_pred_log.",
            "Report improvements against both raw base and PP-FPOL6 champions.",
        ],
        "summary_rows": json.loads(summary.to_json(orient="records", force_ascii=False)),
    }
    (ARTIFACT_DIR / "warm_base_lock_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    _, raw = raw_base_rows()
    summary = pd.concat([raw, fpol3_rows(), fpol6_rows(), fpol9_12_rows()], ignore_index=True, sort=False)
    summary.to_csv(OUTPUT_DIR / "warm_base_performance_summary.csv", index=False)
    stability = stability_reference()
    write_report(summary, stability)
    write_manifest(summary)


if __name__ == "__main__":
    main()
