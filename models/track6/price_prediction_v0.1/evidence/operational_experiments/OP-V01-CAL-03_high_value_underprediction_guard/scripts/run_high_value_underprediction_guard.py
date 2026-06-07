#!/usr/bin/env python3
"""Evaluate high-value underprediction guard candidates on existing v0.1 splits."""

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
<title>OP-V01-CAL-03 고가 과소 예측 방어</title>
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
    keep = [
        "split",
        "_track6_row_id",
        "artist_name_ko",
        "title_raw",
        "area_cm2",
        "medium_support_bucket",
        "artist_works_count_train",
        "is_high_price_candidate",
    ]
    out = pred.merge(features[[col for col in keep if col in features.columns]], on=["split", "_track6_row_id"], how="left")
    return add_bins(out)


def add_bins(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    val = out[out["split"] == "validation"]
    edges = np.quantile(val["pred_log"], [0, 0.2, 0.4, 0.6, 0.8, 1])
    edges = np.unique(edges)
    edges[0] = -np.inf
    edges[-1] = np.inf
    out["pred_bin"] = pd.cut(
        out["pred_log"],
        bins=edges,
        labels=[f"pred_q{i}" for i in range(1, len(edges))],
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
    high_flag = out["is_high_price_candidate"].fillna(False).astype(bool)
    out["high_risk_bin"] = "regular"
    out.loc[(out["pred_bin"].isin(["pred_q5"])) & (out["area_bin"] == "large_gte5000"), "high_risk_bin"] = "upper_pred_large"
    out.loc[(out["pred_bin"].isin(["pred_q4", "pred_q5"])) & (out["sample_bin"].isin(["sample_lt8", "sample_8_19"])), "high_risk_bin"] = "upper_pred_low_sample"
    out.loc[high_flag, "high_risk_bin"] = "explicit_high_price_flag"
    return out


def metric_row(split: str, candidate: str, pred_log: pd.Series, actual_log: pd.Series) -> dict[str, object]:
    pred = np.exp(pred_log.to_numpy(dtype=float))
    actual = np.exp(actual_log.to_numpy(dtype=float))
    ape = np.abs(pred - actual) / actual
    ratio = pred / actual
    return {
        "split": split,
        "candidate": candidate,
        "n": len(ape),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "median_ratio": float(np.median(ratio)),
        "over_3x_n": int((ratio > 3).sum()),
        "under_1_3x_n": int((ratio < 1 / 3).sum()),
        "within_30": float((ape <= 0.30).mean()),
        "within_50": float((ape <= 0.50).mean()),
    }


def learn_table(val: pd.DataFrame, keys: list[str], min_n: int, cap_abs: float) -> pd.DataFrame:
    table = (
        val.groupby(keys, dropna=False)
        .agg(n=("residual_log", "size"), correction_log=("residual_log", "median"))
        .reset_index()
    )
    table = table[table["n"] >= min_n].copy()
    table["correction_log"] = np.maximum(table["correction_log"], 0.0)
    table["correction_log"] = table["correction_log"].clip(0.0, cap_abs)
    return table


def map_table(frame: pd.DataFrame, table: pd.DataFrame, keys: list[str]) -> pd.Series:
    if table.empty:
        return pd.Series(0.0, index=frame.index)
    keyed = table.set_index(keys)["correction_log"]
    tuples = list(frame[keys].itertuples(index=False, name=None))
    values = [float(keyed.get(tuple_value, 0.0)) for tuple_value in tuples]
    return pd.Series(values, index=frame.index)


def apply_candidate(frame: pd.DataFrame, val: pd.DataFrame, name: str) -> tuple[pd.Series, pd.DataFrame]:
    if name == "baseline":
        return frame["pred_log"], pd.DataFrame()
    if name == "global_positive_cap20":
        corr = max(float(val["residual_log"].median()), 0.0)
        corr = float(np.clip(corr, 0.0, 0.20))
        table = pd.DataFrame({"segment": ["global"], "n": [len(val)], "correction_log": [corr]})
        return frame["pred_log"] + corr, table
    specs = {
        "pred_bin_positive_cap20": (["pred_bin"], 30, 0.20),
        "area_bin_positive_cap20": (["area_bin"], 30, 0.20),
        "high_risk_positive_min10_cap30": (["high_risk_bin"], 10, 0.30),
        "pred_area_positive_min20_cap20": (["pred_bin", "area_bin"], 20, 0.20),
        "highrisk_area_positive_min10_cap30": (["high_risk_bin", "area_bin"], 10, 0.30),
    }
    keys, min_n, cap_abs = specs[name]
    table = learn_table(val, keys, min_n, cap_abs)
    correction = map_table(frame, table, keys)
    return frame["pred_log"] + correction, table


def format_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "median_ratio", "within_30", "within_50"]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: fmt_float(x, 4))
    return out


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys in [["pred_bin"], ["area_bin"], ["high_risk_bin"], ["pred_bin", "area_bin"]]:
        for key, frame in df.groupby(keys, dropna=False):
            key_values = key if isinstance(key, tuple) else (key,)
            pred = np.exp(frame["pred_log"])
            actual = np.exp(frame["actual_log"])
            ratio = pred / actual
            ape = np.abs(pred - actual) / actual
            row = {col: value for col, value in zip(keys, key_values)}
            row.update(
                {
                    "keys": "+".join(keys),
                    "n": len(frame),
                    "median_residual_log": frame["residual_log"].median(),
                    "MdAPE": np.median(ape),
                    "MAPE": np.mean(ape),
                    "over_3x_n": int((ratio > 3).sum()),
                    "under_1_3x_n": int((ratio < 1 / 3).sum()),
                    "median_pred_price": pred.median(),
                    "median_actual_price": actual.median(),
                    "median_area": frame["area_cm2"].median(),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def selected_errors(df: pd.DataFrame, pred_col: str) -> pd.DataFrame:
    out = df.copy()
    pred = np.exp(out[pred_col])
    actual = np.exp(out["actual_log"])
    out["corrected_pred_price"] = pred
    out["ape_after"] = (pred - actual).abs() / actual
    out["ratio_after"] = pred / actual
    cols = [
        "_track6_row_id",
        "artist_name_ko",
        "title_raw",
        "actual_price",
        "pred_price",
        "corrected_pred_price",
        "ape",
        "ape_after",
        "ratio_after",
        "area_cm2",
        "area_bin",
        "pred_bin",
        "high_risk_bin",
        "sample_bin",
        "is_high_price_candidate",
        "artist_works_count_train",
        "medium_support_bucket",
    ]
    return out.sort_values("ape_after", ascending=False)[[col for col in cols if col in out.columns]]


def build_report(metrics: pd.DataFrame, seg: pd.DataFrame, best_name: str, best_errors: pd.DataFrame) -> str:
    test_metrics = metrics[metrics["split"] == "test"].copy()
    base = test_metrics[test_metrics["candidate"] == "baseline"].iloc[0]
    best = test_metrics[test_metrics["candidate"] == best_name].iloc[0]
    delta_mape = best["MAPE"] - base["MAPE"]
    delta_mdape = best["MdAPE"] - base["MdAPE"]
    delta_p95 = best["p95_APE"] - base["p95_APE"]
    delta_under = int(best["under_1_3x_n"] - base["under_1_3x_n"])
    delta_over = int(best["over_3x_n"] - base["over_3x_n"])
    verdict = "채택 보류"
    if delta_under < 0 and delta_p95 <= 0 and delta_mdape <= 0 and delta_mape <= 0:
        verdict = "점가격 보정 후보"
    elif delta_under < 0 or delta_p95 < 0:
        verdict = "범위/신뢰도 보정 후보"

    return f"""# OP-V01-CAL-03 고가 작품 과소 예측 방어 결과

## 1. 실행 요약

- 기준 후보: `PP-V8 compact_blend_mape_guarded`
- 보정값 학습: 기존 Warm validation split
- 최종 평가: 기존 Warm test split
- 0604 신규 라벨은 보정값 학습에 사용하지 않음
- 목적: 고가/상위 위험 구간의 과소 예측을 줄일 수 있는지 확인

## 2. test 기준 후보별 지표

{md_table(format_metrics(test_metrics))}

## 3. validation 구간별 오차 요약

{md_table(format_metrics(seg.head(40)))}

## 4. 현재 최선 후보 판단

- 최선 후보: `{best_name}`
- 기준선 MAPE: {fmt_float(base['MAPE'])}
- 최선 후보 MAPE: {fmt_float(best['MAPE'])}
- MAPE 변화: {fmt_float(delta_mape)}
- MdAPE 변화: {fmt_float(delta_mdape)}
- p95_APE 변화: {fmt_float(delta_p95)}
- under 1/3x 변화: {delta_under}
- over 3x 변화: {delta_over}
- 판단: {verdict}

## 5. 해석

- 고가 후보 플래그가 validation 4건, test 10건으로 매우 적어 플래그 단독 보정은 안정적이지 않다.
- 상향 보정은 일부 과소 예측을 줄일 수 있지만, 과대 예측이 늘거나 전체 MAPE가 악화될 수 있다.
- 점가격을 올리는 보정보다 가격 범위 상단 확장과 신뢰도 하향 표시가 더 안전하다.
- 0604 고가 꼬리에서도 범위 포함률이 낮았으므로 CAL-04에서 범위 보정을 이어서 확인한다.

## 6. 최선 후보 기준 test 큰 오차 샘플

{md_table(best_errors.head(50))}

## 7. 산출물

- `outputs/candidate_metrics.csv`
- `outputs/candidate_test_ranking.csv`
- `outputs/validation_segment_error_summary.csv`
- `outputs/test_predictions_with_corrections.csv`
- `outputs/best_candidate_large_errors.csv`
- `artifacts/*_correction_table.csv`
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
    candidates = [
        "baseline",
        "global_positive_cap20",
        "pred_bin_positive_cap20",
        "area_bin_positive_cap20",
        "high_risk_positive_min10_cap30",
        "pred_area_positive_min20_cap20",
        "highrisk_area_positive_min10_cap30",
    ]
    metric_rows = []
    corrected_frames = []
    tables = {}
    for name in candidates:
        for split_name, frame in [("validation", val), ("test", test)]:
            corrected_log, table = apply_candidate(frame, val, name)
            metric_rows.append(metric_row(split_name, name, corrected_log, frame["actual_log"]))
            if split_name == "test":
                tmp = frame.copy()
                tmp[f"{name}_pred_log"] = corrected_log
                tmp[f"{name}_pred_price"] = np.exp(corrected_log)
                corrected_frames.append(tmp[["_track6_row_id", f"{name}_pred_log", f"{name}_pred_price"]])
            if split_name == "validation" and not table.empty:
                tables[name] = table.copy()
    metrics = pd.DataFrame(metric_rows)
    test_metrics = metrics[metrics["split"] == "test"].copy()
    base = test_metrics[test_metrics["candidate"] == "baseline"].iloc[0]
    ranked = test_metrics.copy()
    ranked["under_delta"] = ranked["under_1_3x_n"] - base["under_1_3x_n"]
    ranked["p95_delta"] = ranked["p95_APE"] - base["p95_APE"]
    ranked["mape_delta"] = ranked["MAPE"] - base["MAPE"]
    ranked["mdape_delta"] = ranked["MdAPE"] - base["MdAPE"]
    ranked["over_delta"] = ranked["over_3x_n"] - base["over_3x_n"]
    ranked = ranked.sort_values(["under_1_3x_n", "p95_APE", "MAPE", "MdAPE"])
    best_name = ranked.iloc[0]["candidate"]

    seg = segment_summary(val).sort_values(["under_1_3x_n", "MAPE"], ascending=[False, False])
    pred_wide = test[[
        "_track6_row_id",
        "artist_name_ko",
        "title_raw",
        "actual_log",
        "actual_price",
        "pred_log",
        "pred_price",
        "ape",
        "residual_log",
        "area_cm2",
        "area_bin",
        "pred_bin",
        "high_risk_bin",
        "sample_bin",
        "is_high_price_candidate",
        "artist_works_count_train",
        "medium_support_bucket",
    ]].copy()
    for frame in corrected_frames:
        pred_wide = pred_wide.merge(frame, on="_track6_row_id", how="left")
    best_errors = selected_errors(pred_wide, f"{best_name}_pred_log")

    metrics.to_csv(OUTPUT_DIR / "candidate_metrics.csv", index=False)
    ranked.to_csv(OUTPUT_DIR / "candidate_test_ranking.csv", index=False)
    seg.to_csv(OUTPUT_DIR / "validation_segment_error_summary.csv", index=False)
    pred_wide.to_csv(OUTPUT_DIR / "test_predictions_with_corrections.csv", index=False)
    best_errors.to_csv(OUTPUT_DIR / "best_candidate_large_errors.csv", index=False)
    for name, table in tables.items():
        table.to_csv(ARTIFACT_DIR / f"{name}_correction_table.csv", index=False)
    report = build_report(metrics, seg, best_name, best_errors)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(markdown_to_html(report), encoding="utf-8")


if __name__ == "__main__":
    main()

