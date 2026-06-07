#!/usr/bin/env python3
"""Evaluate risk-adjusted price range and confidence policies for v0.1.

This experiment keeps the point prediction unchanged. It learns range-width
multipliers on the warm validation split and evaluates them on the warm test
split, so the resulting policy is reproducible and not tuned on 0604 labels.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


def find_repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO = find_repo_root()
EXP_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PRED_PATH = (
    REPO
    / "models/track6/price_prediction_v0.1/evidence/experiments/"
    / "PP-V8_warm_deployment_simplification/outputs/predictions.csv"
)
VAL_FEATURE_PATH = (
    REPO / "models/track6/price_prediction_v0.1/data/training/track6_split/track6_val_warm.csv"
)
TEST_FEATURE_PATH = (
    REPO / "models/track6/price_prediction_v0.1/data/training/track6_split/track6_test_warm.csv"
)

BASE_CANDIDATE = "compact_blend_mape_guarded"
MULTIPLIER_GRID = [1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00]
TARGET_COVERAGE = 0.85


def fmt_float(value: float | int, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def md_table(df: pd.DataFrame, columns: list[str] | None = None) -> str:
    if df.empty:
        return "_데이터 없음_"
    view = df.copy() if columns is None else df[columns].copy()

    def clean(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(clean(col) for col in view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(clean(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def markdown_to_html(markdown: str) -> str:
    html_lines: list[str] = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if in_table and not (line.startswith("| ") and line.endswith(" |")):
            html_lines.append("</table>")
            in_table = False
        if not line:
            continue
        if line.startswith("| ") and line.endswith(" |"):
            cells = [escape(cell.strip()) for cell in line.strip("|").split("|")]
            if set(cells) == {"---"}:
                continue
            if not in_table:
                html_lines.append("<table>")
                html_lines.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr>")
                in_table = True
            else:
                html_lines.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            html_lines.append(f"<p>{escape(line)}</p>")
    if in_table:
        html_lines.append("</table>")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>OP-V01-CAL-04 위험도 기반 가격 범위/신뢰도 보정</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.55; color: #1f2933; }}
h1, h2, h3 {{ color: #101828; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 24px; font-size: 14px; }}
th, td {{ border: 1px solid #d8dee9; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f3f6fa; }}
</style>
</head>
<body>
{chr(10).join(html_lines)}
</body>
</html>
"""


def load_data() -> pd.DataFrame:
    pred = pd.read_csv(PRED_PATH)
    pred = pred[
        (pred["candidate"] == BASE_CANDIDATE)
        & (pred["split"].isin(["validation", "test"]))
    ].copy()
    pred["_track6_row_id"] = pred["_track6_row_id"].astype(int)
    frames = []
    for split, path in [("validation", VAL_FEATURE_PATH), ("test", TEST_FEATURE_PATH)]:
        df = pd.read_csv(path, low_memory=False)
        df["split"] = split
        frames.append(df)
    features = pd.concat(frames, ignore_index=True)
    keep_cols = [
        "split",
        "_track6_row_id",
        "artist_name_ko",
        "title_raw",
        "area_cm2",
        "medium_support_bucket",
        "artist_works_count_train",
        "is_high_price_candidate",
    ]
    df = pred.merge(features[[col for col in keep_cols if col in features.columns]], on=["split", "_track6_row_id"], how="left")
    return add_risk_groups(df)


def add_risk_groups(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    val = out[out["split"] == "validation"]
    pred_edges = np.quantile(val["pred_log"], [0, 0.2, 0.4, 0.6, 0.8, 1])
    pred_edges = np.unique(pred_edges)
    pred_edges[0] = -np.inf
    pred_edges[-1] = np.inf
    out["pred_bin"] = pd.cut(
        out["pred_log"],
        bins=pred_edges,
        labels=[f"pred_q{i}" for i in range(1, len(pred_edges))],
        include_lowest=True,
    ).astype(str)
    area = pd.to_numeric(out["area_cm2"], errors="coerce")
    out["area_bin"] = "area_missing"
    out.loc[area < 500, "area_bin"] = "tiny_lt500"
    out.loc[(area >= 500) & (area < 1_500), "area_bin"] = "small_500_1500"
    out.loc[(area >= 1_500) & (area < 5_000), "area_bin"] = "mid_1500_5000"
    out.loc[area >= 5_000, "area_bin"] = "large_gte5000"
    works = pd.to_numeric(out["artist_works_count_train"], errors="coerce")
    out["sample_bin"] = "sample_missing"
    out.loc[works < 8, "sample_bin"] = "sample_lt8"
    out.loc[(works >= 8) & (works < 20), "sample_bin"] = "sample_8_19"
    out.loc[(works >= 20) & (works < 100), "sample_bin"] = "sample_20_99"
    out.loc[works >= 100, "sample_bin"] = "sample_100_plus"

    width_q75 = float(val["routing_width"].quantile(0.75))
    width_q90 = float(val["routing_width"].quantile(0.90))
    high_flag = out["is_high_price_candidate"].fillna(False).astype(bool)
    out["risk_group"] = "regular"
    out.loc[
        out["area_bin"].isin(["tiny_lt500", "small_500_1500"]) & out["pred_bin"].isin(["pred_q1", "pred_q2"]),
        "risk_group",
    ] = "small_low_price_risk"
    out.loc[out["sample_bin"].isin(["sample_lt8", "sample_missing"]), "risk_group"] = "low_sample"
    out.loc[out["routing_width"] >= width_q75, "risk_group"] = "wide_uncertainty"
    out.loc[
        out["pred_bin"].isin(["pred_q4", "pred_q5"]) & (
            out["area_bin"].eq("large_gte5000") | out["sample_bin"].isin(["sample_lt8", "sample_8_19"])
        ),
        "risk_group",
    ] = "high_value_range_risk"
    out.loc[out["routing_width"] >= width_q90, "risk_group"] = "wide_uncertainty"
    out.loc[high_flag, "risk_group"] = "explicit_high_price_flag"
    return out


def interval_for(frame: pd.DataFrame, multiplier: pd.Series | float) -> pd.DataFrame:
    width = frame["routing_width"].astype(float) * multiplier
    out = frame.copy()
    out["range_multiplier"] = multiplier
    out["range_width_log"] = width
    out["range_low_log"] = out["pred_log"] - width / 2.0
    out["range_high_log"] = out["pred_log"] + width / 2.0
    out["range_low_price"] = np.exp(out["range_low_log"])
    out["range_high_price"] = np.exp(out["range_high_log"])
    out["range_ratio"] = np.exp(width)
    out["range_contains_actual"] = (
        (out["actual_log"] >= out["range_low_log"]) & (out["actual_log"] <= out["range_high_log"])
    )
    out["range_miss_low"] = out["actual_log"] < out["range_low_log"]
    out["range_miss_high"] = out["actual_log"] > out["range_high_log"]
    return out


def confidence_tier(frame: pd.DataFrame) -> pd.Series:
    n = pd.to_numeric(frame["artist_works_count_train"], errors="coerce").fillna(0)
    ratio = pd.to_numeric(frame["range_ratio"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    confidence = pd.Series("low", index=frame.index, dtype=object)
    confidence[(n >= 10) & (ratio <= 8.0)] = "medium"
    confidence[(n >= 30) & (ratio <= 4.0)] = "high"
    confidence[frame["risk_group"].isin(["wide_uncertainty", "high_value_range_risk", "explicit_high_price_flag"])] = "low"
    return confidence


def range_metrics(split: str, policy: str, frame: pd.DataFrame) -> dict[str, object]:
    high_actual_cut = frame["actual_price"].quantile(0.95)
    high_actual = frame[frame["actual_price"] >= high_actual_cut]
    severe = frame[frame["ape"] >= 1.0]
    return {
        "split": split,
        "policy": policy,
        "n": len(frame),
        "coverage": float(frame["range_contains_actual"].mean()),
        "miss_low_n": int(frame["range_miss_low"].sum()),
        "miss_high_n": int(frame["range_miss_high"].sum()),
        "median_range_ratio": float(frame["range_ratio"].median()),
        "p90_range_ratio": float(frame["range_ratio"].quantile(0.90)),
        "p95_range_ratio": float(frame["range_ratio"].quantile(0.95)),
        "mean_width_log": float(frame["range_width_log"].mean()),
        "high_actual_coverage": float(high_actual["range_contains_actual"].mean()) if len(high_actual) else np.nan,
        "severe_error_coverage": float(severe["range_contains_actual"].mean()) if len(severe) else np.nan,
        "high_conf_n": int((frame["confidence_tier"] == "high").sum()),
        "medium_conf_n": int((frame["confidence_tier"] == "medium").sum()),
        "low_conf_n": int((frame["confidence_tier"] == "low").sum()),
    }


def choose_multipliers(val: pd.DataFrame, target: float = TARGET_COVERAGE) -> pd.DataFrame:
    rows = []
    for group, frame in val.groupby("risk_group"):
        selected = MULTIPLIER_GRID[-1]
        selected_coverage = 0.0
        for multiplier in MULTIPLIER_GRID:
            covered = interval_for(frame, multiplier)["range_contains_actual"].mean()
            selected_coverage = float(covered)
            if covered >= target:
                selected = multiplier
                break
        rows.append(
            {
                "risk_group": group,
                "n": len(frame),
                "target_coverage": target,
                "selected_multiplier": selected,
                "validation_coverage_at_selected": selected_coverage,
                "baseline_coverage": float(interval_for(frame, 1.0)["range_contains_actual"].mean()),
            }
        )
    return pd.DataFrame(rows)


def apply_policy(frame: pd.DataFrame, policy: str, table: pd.DataFrame | None = None) -> pd.DataFrame:
    if policy == "baseline_centered_width":
        out = interval_for(frame, 1.0)
    elif policy == "fixed_125_width":
        out = interval_for(frame, 1.25)
    elif policy == "fixed_150_width":
        out = interval_for(frame, 1.50)
    elif policy == "risk_target_85_width":
        assert table is not None
        mapping = table.set_index("risk_group")["selected_multiplier"].to_dict()
        multiplier = frame["risk_group"].map(mapping).fillna(1.0).astype(float)
        out = interval_for(frame, multiplier)
    elif policy == "risk_min_high_tail_width":
        assert table is not None
        mapping = table.set_index("risk_group")["selected_multiplier"].to_dict()
        multiplier = frame["risk_group"].map(mapping).fillna(1.0).astype(float)
        multiplier = multiplier.where(
            ~frame["risk_group"].isin(["high_value_range_risk", "explicit_high_price_flag"]),
            np.maximum(multiplier, 2.0),
        )
        out = interval_for(frame, multiplier.astype(float))
    else:
        raise ValueError(f"unknown policy: {policy}")
    out["confidence_tier"] = confidence_tier(out)
    return out


def format_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "coverage",
        "median_range_ratio",
        "p90_range_ratio",
        "p95_range_ratio",
        "mean_width_log",
        "high_actual_coverage",
        "severe_error_coverage",
        "validation_coverage_at_selected",
        "baseline_coverage",
        "target_coverage",
        "selected_multiplier",
    ]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: fmt_float(x, 4))
    return out


def risk_group_metrics(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    rows = []
    for group, group_df in frame.groupby("risk_group"):
        row = range_metrics("test", policy, group_df)
        row["risk_group"] = group
        rows.append(row)
    return pd.DataFrame(rows)


def build_report(metrics: pd.DataFrame, table: pd.DataFrame, risk_metrics: pd.DataFrame, best_policy: str, best_frame: pd.DataFrame) -> str:
    test_metrics = metrics[metrics["split"] == "test"].copy()
    baseline = test_metrics[test_metrics["policy"] == "baseline_centered_width"].iloc[0]
    best = test_metrics[test_metrics["policy"] == best_policy].iloc[0]
    coverage_delta = best["coverage"] - baseline["coverage"]
    width_delta = best["median_range_ratio"] - baseline["median_range_ratio"]
    verdict = "채택 보류"
    if coverage_delta > 0 and best["coverage"] >= 0.95 and best["p90_range_ratio"] <= baseline["p90_range_ratio"] * 2.0:
        verdict = "범위/신뢰도 보정 후보"
    if coverage_delta <= 0:
        verdict = "채택 보류"

    large_misses = best_frame[~best_frame["range_contains_actual"]].copy()
    large_misses["range_miss_direction"] = np.where(large_misses["range_miss_high"], "상한 초과", "하한 미만")
    large_misses = large_misses.sort_values("ape", ascending=False)
    cols = [
        "_track6_row_id",
        "artist_name_ko",
        "title_raw",
        "actual_price",
        "pred_price",
        "range_low_price",
        "range_high_price",
        "ape",
        "range_miss_direction",
        "risk_group",
        "confidence_tier",
        "range_ratio",
        "routing_width",
        "artist_works_count_train",
        "area_cm2",
        "medium_support_bucket",
    ]
    miss_table = large_misses[[col for col in cols if col in large_misses.columns]].head(50)

    return f"""# OP-V01-CAL-04 위험도 기반 가격 범위/신뢰도 보정 결과

## 1. 실행 요약

- 기준 후보: `PP-V8 compact_blend_mape_guarded`
- 점가격: 변경 없음
- 기준 범위: `pred_log ± routing_width / 2`
- 보정값 학습: 기존 Warm validation split
- 최종 평가: 기존 Warm test split
- 0604 신규 라벨은 범위 배율 학습에 사용하지 않음

## 2. test 기준 범위 정책별 지표

{md_table(format_metrics(test_metrics))}

## 3. validation에서 선택된 위험 그룹별 범위 배율

{md_table(format_metrics(table))}

## 4. 최선 정책의 위험 그룹별 test 지표

{md_table(format_metrics(risk_metrics))}

## 5. 현재 최선 후보 판단

- 최선 정책: `{best_policy}`
- 기준 범위 포함률: {fmt_float(baseline['coverage'])}
- 최선 범위 포함률: {fmt_float(best['coverage'])}
- 범위 포함률 변화: {fmt_float(coverage_delta)}
- 기준 median range ratio: {fmt_float(baseline['median_range_ratio'])}
- 최선 median range ratio: {fmt_float(best['median_range_ratio'])}
- median range ratio 변화: {fmt_float(width_delta)}
- 판단: {verdict}

## 6. 해석

- CAL-02와 CAL-03에서 점가격 보정은 안정적으로 채택하기 어려웠다.
- CAL-04는 점가격을 유지하고, 위험 그룹의 가격 범위와 신뢰도만 조정한다.
- 범위 포함률이 개선되더라도 범위가 지나치게 넓어지면 서비스 설명력이 떨어진다.
- 따라서 최종 채택은 범위 포함률 개선과 범위 폭 증가를 함께 봐야 한다.
- 이 정책은 v0.1 운영 기본값에 바로 반영하지 않는다.
- 별도 후보 출력 필드로 API/프론트 테스트를 진행한 뒤 반영 여부를 결정한다.

## 7. 최선 정책 기준 범위 밖 큰 오차 샘플

{md_table(miss_table)}

## 8. 산출물

- `outputs/range_policy_metrics.csv`
- `outputs/risk_group_multiplier_table.csv`
- `outputs/best_policy_test_predictions.csv`
- `outputs/best_policy_risk_group_metrics.csv`
- `outputs/best_policy_range_misses.csv`
- `artifacts/risk_group_multiplier_table.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    val = df[df["split"] == "validation"].copy()
    test = df[df["split"] == "test"].copy()
    table = choose_multipliers(val)
    policies = [
        "baseline_centered_width",
        "fixed_125_width",
        "fixed_150_width",
        "risk_target_85_width",
        "risk_min_high_tail_width",
    ]
    metric_rows = []
    policy_frames: dict[str, pd.DataFrame] = {}
    for policy in policies:
        for split, frame in [("validation", val), ("test", test)]:
            adjusted = apply_policy(frame, policy, table)
            metric_rows.append(range_metrics(split, policy, adjusted))
            if split == "test":
                policy_frames[policy] = adjusted
    metrics = pd.DataFrame(metric_rows)
    test_metrics = metrics[metrics["split"] == "test"].copy()
    baseline = test_metrics[test_metrics["policy"] == "baseline_centered_width"].iloc[0]
    ranked = test_metrics.copy()
    ranked["coverage_delta"] = ranked["coverage"] - baseline["coverage"]
    ranked["width_penalty"] = ranked["p90_range_ratio"] / baseline["p90_range_ratio"]
    ranked = ranked.sort_values(["coverage", "width_penalty"], ascending=[False, True])
    eligible = ranked[
        (ranked["coverage"] >= 0.95)
        & (ranked["width_penalty"] <= 2.0)
        & (ranked["coverage_delta"] > 0)
    ].copy()
    if not eligible.empty:
        best_policy = str(eligible.sort_values(["coverage", "width_penalty"], ascending=[False, True]).iloc[0]["policy"])
    else:
        best_policy = str(ranked.iloc[0]["policy"])
    best_frame = policy_frames[best_policy].copy()
    risk_metrics = risk_group_metrics(best_frame, best_policy)
    miss = best_frame[~best_frame["range_contains_actual"]].copy()
    miss["range_miss_direction"] = np.where(miss["range_miss_high"], "high", "low")

    metrics.to_csv(OUTPUT_DIR / "range_policy_metrics.csv", index=False)
    ranked.to_csv(OUTPUT_DIR / "range_policy_test_ranking.csv", index=False)
    table.to_csv(OUTPUT_DIR / "risk_group_multiplier_table.csv", index=False)
    table.to_csv(ARTIFACT_DIR / "risk_group_multiplier_table.csv", index=False)
    best_frame.to_csv(OUTPUT_DIR / "best_policy_test_predictions.csv", index=False)
    risk_metrics.to_csv(OUTPUT_DIR / "best_policy_risk_group_metrics.csv", index=False)
    miss.to_csv(OUTPUT_DIR / "best_policy_range_misses.csv", index=False)

    report = build_report(metrics, table, risk_metrics, best_policy, best_frame)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(markdown_to_html(report), encoding="utf-8")


if __name__ == "__main__":
    main()
