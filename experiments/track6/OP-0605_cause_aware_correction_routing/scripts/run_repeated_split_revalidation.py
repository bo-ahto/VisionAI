from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0605_cause_aware_correction_routing"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
SOURCE_SCRIPT = EXP_DIR / "scripts/run_cause_aware_correction_routing.py"
SOURCE_ROWS_PATH = (
    PROJECT_ROOT
    / "experiments/track6/OP-0605_existing_split_error_cause_customization/outputs/enriched_error_rows.csv"
)


def load_source_module():
    spec = importlib.util.spec_from_file_location("cause_routing", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stable_bucket(value: object, seed: int, modulo: int = 10) -> int:
    text = f"{value}::{seed}"
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def assign_validation_role(frame: pd.DataFrame, mode: str, seed: int) -> pd.Series:
    role = pd.Series("test", index=frame.index, dtype=object)
    validation_mask = frame["split"].eq("validation")
    if mode == "row_repeated":
        bucket = frame.loc[validation_mask, "_track6_row_id"].apply(lambda value: stable_bucket(value, seed))
    elif mode == "artist_repeated":
        artist_value = frame.loc[validation_mask, "artist_key"].fillna(frame.loc[validation_mask, "artist_name_ko"])
        bucket = artist_value.apply(lambda value: stable_bucket(value, seed))
    else:
        raise ValueError(f"Unknown mode: {mode}")
    role.loc[validation_mask] = np.where(bucket < 6, "correction_calibration", "router_validation")
    return role


def summarize_metric_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metric_cols = ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "over_3x_n", "under_1_3x_n"]
    for (route, split_mode), group in frame.groupby(["route", "split_mode"], observed=False):
        for metric in metric_cols:
            values = pd.to_numeric(group[metric], errors="coerce")
            rows.append(
                {
                    "route": route,
                    "split_mode": split_mode,
                    "metric": metric,
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=0)),
                    "min": float(values.min()),
                    "median": float(values.median()),
                    "max": float(values.max()),
                }
            )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    view = frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    if view.empty:
        return "_결과 없음_"
    cols = list(view.columns)
    lines = [
        "| " + " | ".join(str(col) for col in cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in view.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append("" if pd.isna(value) else f"{value:.4f}")
            else:
                text = "" if pd.isna(value) else str(value)
                values.append(text.replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(run_metrics: pd.DataFrame, summary: pd.DataFrame, baseline: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    key_summary = summary[
        summary["metric"].isin(["MdAPE", "MAPE", "p95_APE", "RMSE_log"])
    ].sort_values(["route", "split_mode", "metric"])
    delta_summary = run_metrics.groupby(["route", "split_mode"], observed=False)[
        ["delta_MdAPE", "delta_MAPE", "delta_p95_APE", "delta_RMSE_log"]
    ].agg(["mean", "std", "min", "max"])
    delta_summary.columns = ["_".join(col).strip() for col in delta_summary.columns.to_flat_index()]
    delta_summary = delta_summary.reset_index()

    md = f"""# 원인별 보정/라우팅 반복 split 재검증 결과

## 1. 검증 범위

- 검증 대상: `expert_model_structure_guard`
- 검증 의미: 모델 재학습 검증이 아니라, validation에서 학습하는 보정값과 라우팅 정책의 안정성 검증
- 반복 방식
  - row repeated: validation 행을 여러 seed로 보정값 학습용/라우팅 확인용으로 재분할
  - artist repeated: validation 작가 단위로 보정값 학습용/라우팅 확인용으로 재분할
- 최종 평가는 기존 test split에서만 수행

## 2. 기준선

{md_table(baseline)}

## 3. 반복 split 지표 분포

{md_table(key_summary)}

## 4. 기준선 대비 변화량

{md_table(delta_summary)}

## 5. 해석

- Warm은 row 반복 split과 artist-level split에서 평균 개선 폭이 매우 작고 일부 seed에서는 기준선보다 나빠질 수 있음
- Warm 보정은 최종 점가격 교체 후보라기보다 가격 범위/신뢰도 조정 후보로 보는 편이 안전함
- Cold는 row 반복 split에서 MdAPE/MAPE/p95_APE 개선이 안정적으로 유지됨
- Cold는 artist-level split에서 p95_APE와 MAPE 평균은 개선되지만, MdAPE와 RMSE_log는 일부 seed에서 기준선보다 나빠질 수 있음
- Cold 보정은 가능성이 있으나, artist 단위 일반화까지 최종 채택하려면 모델 재학습을 포함한 artist-level 반복 검증이 추가로 필요함
- Cold는 일부 split에서 과소 예측 건수가 늘어날 수 있으므로 가격 범위/신뢰도 정책과 함께 봐야 함
- 이 검증은 보정/라우팅 안정성 검증이며, 모델 자체의 재학습 안정성은 별도 반복 재학습 실험이 필요함

## 6. 산출물

- `outputs/repeated_split_revalidation_metrics.csv`
- `outputs/repeated_split_revalidation_summary.csv`
- `reports/repeated_split_revalidation_report.md`
"""
    (REPORT_DIR / "repeated_split_revalidation_report.md").write_text(md, encoding="utf-8")

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>원인별 보정/라우팅 반복 split 재검증 결과</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1, h2 {{ color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; margin: 14px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
  </style>
</head>
<body>
  <h1>원인별 보정/라우팅 반복 split 재검증 결과</h1>
  <h2>기준선</h2>{baseline.to_html(index=False, escape=True)}
  <h2>반복 split 지표 분포</h2>{key_summary.to_html(index=False, escape=True)}
  <h2>기준선 대비 변화량</h2>{delta_summary.to_html(index=False, escape=True)}
</body>
</html>
"""
    (REPORT_DIR / "repeated_split_revalidation_report.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_source_module()
    rows = pd.read_csv(SOURCE_ROWS_PATH)
    rows["operational_segment"] = rows.apply(source.operational_segment, axis=1)

    all_metrics = []
    baseline_rows = []
    for route in ["warm", "cold"]:
        route_rows = rows[rows["route"].eq(route)].copy()
        test = route_rows[route_rows["split"].eq("test")].copy()
        baseline_rows.append({"route": route, "policy": "baseline", **source.metrics(test, "pred_price")})

    baseline = pd.DataFrame(baseline_rows)
    baseline_by_route = baseline.set_index("route")

    for split_mode in ["row_repeated", "artist_repeated"]:
        for seed in range(20):
            rows_with_role = rows.copy()
            rows_with_role["eval_split"] = assign_validation_role(rows_with_role, split_mode, seed)
            for route in ["warm", "cold"]:
                route_rows = rows_with_role[rows_with_role["route"].eq(route)].copy()
                calibration = route_rows[route_rows["eval_split"].eq("correction_calibration")]
                route_with_candidates, _ = source.add_candidate_predictions(route_rows, calibration, route)
                routed_pred, _ = source.apply_expert_policy(route_with_candidates, route)
                route_with_candidates["expert_model_structure_guard_pred_price"] = routed_pred
                test = route_with_candidates[route_with_candidates["split"].eq("test")]
                row = {
                    "route": route,
                    "split_mode": split_mode,
                    "seed": seed,
                    **source.metrics(test, "expert_model_structure_guard_pred_price"),
                }
                base = baseline_by_route.loc[route]
                row["delta_MdAPE"] = row["MdAPE"] - float(base["MdAPE"])
                row["delta_MAPE"] = row["MAPE"] - float(base["MAPE"])
                row["delta_p95_APE"] = row["p95_APE"] - float(base["p95_APE"])
                row["delta_RMSE_log"] = row["RMSE_log"] - float(base["RMSE_log"])
                all_metrics.append(row)

    run_metrics = pd.DataFrame(all_metrics)
    summary = summarize_metric_distribution(run_metrics)
    run_metrics.to_csv(OUTPUT_DIR / "repeated_split_revalidation_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "repeated_split_revalidation_summary.csv", index=False)
    baseline.to_csv(OUTPUT_DIR / "repeated_split_revalidation_baseline.csv", index=False)
    write_report(run_metrics, summary, baseline)

    output = {
        "runs": int(len(run_metrics)),
        "report_md": str((REPORT_DIR / "repeated_split_revalidation_report.md").relative_to(PROJECT_ROOT)),
        "report_html": str((REPORT_DIR / "repeated_split_revalidation_report.html").relative_to(PROJECT_ROOT)),
        "metrics": str((OUTPUT_DIR / "repeated_split_revalidation_metrics.csv").relative_to(PROJECT_ROOT)),
    }
    (OUTPUT_DIR / "repeated_split_revalidation_summary.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
