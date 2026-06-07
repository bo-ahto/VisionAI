#!/usr/bin/env python3
"""Split 0604 operational evaluation metrics by label-quality groups.

This experiment does not change v0.1 predictions. It separates evaluation
groups so that very low or extreme labels do not hide the actual correction
problem we need to solve next.
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
INPUT = (
    REPO
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/"
    / "operational_predictions_with_actual.csv"
)

PRICE_COL = "service_primary_pred_price_krw"
ACTUAL_COL = "actual_price_krw"
ACTUAL_USD_COL = "actual_price_usd_equiv"
RANGE_LOW_COL = "service_range_low_price_krw"
RANGE_HIGH_COL = "service_range_high_price_krw"

CANDIDATES = [
    ("service_primary", "service_primary_pred_price_krw"),
    ("v01_operational", "v01_operational_pred_price_krw"),
    ("pp_v8_compact_blend_mape_guarded", "pp_v8_compact_blend_mape_guarded_pred_price_krw"),
    ("svc_numeric_seed_mean", "svc_numeric_seed_mean_pred_price_krw"),
    ("pp_v2_defensive", "pp_v2_defensive_pred_price_krw"),
    ("l10_generated_bucket_seq", "l10_generated_bucket_seq_pred_price_krw"),
]


def fmt_float(value: float | int, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def fmt_int(value: float | int) -> str:
    if pd.isna(value):
        return ""
    return f"{int(round(float(value))):,}"


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
    """Small markdown renderer for headings, bullets, fenced text, and tables."""
    html_lines: list[str] = []
    in_ul = False
    in_pre = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_pre:
                html_lines.append("</code></pre>")
                in_pre = False
            else:
                html_lines.append("<pre><code>")
                in_pre = True
            continue
        if in_pre:
            html_lines.append(escape(line))
            continue
        if line.startswith("| ") and line.endswith(" |"):
            cells = [escape(cell.strip()) for cell in line.strip("|").split("|")]
            if set(cells) == {"---"}:
                continue
            tag = "th" if not html_lines or not html_lines[-1].endswith("</tr></table>") else "td"
            if tag == "th":
                html_lines.append("<table><tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr></table>")
            else:
                html_lines[-1] = html_lines[-1].replace("</table>", "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr></table>")
            continue
        if in_ul and not line.startswith("- "):
            html_lines.append("</ul>")
            in_ul = False
        if not line:
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
        else:
            html_lines.append(f"<p>{escape(line)}</p>")
    if in_ul:
        html_lines.append("</ul>")
    body = "\n".join(html_lines)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>OP-V01-CAL-01 라벨 검수 평가 분리</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.55; color: #1f2933; }}
h1, h2, h3 {{ color: #101828; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 24px; font-size: 14px; }}
th, td {{ border: 1px solid #d8dee9; padding: 8px 10px; text-align: left; vertical-align: top; }}
th {{ background: #f3f6fa; }}
code, pre {{ background: #f6f8fa; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT, low_memory=False)
    numeric_cols = [
        ACTUAL_COL,
        ACTUAL_USD_COL,
        "actual_price_native",
        PRICE_COL,
        RANGE_LOW_COL,
        RANGE_HIGH_COL,
        "svc_group_n",
        "area_cm2",
        "l10_price_range_ratio",
        "l10_quantile_width",
    ]
    for _, pred_col in CANDIDATES:
        numeric_cols.append(pred_col)
    for col in sorted(set(numeric_cols)):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df[ACTUAL_COL].notna() & (df[ACTUAL_COL] > 0)].copy()
    return df


def add_qc_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["flag_actual_under_50_usd"] = out[ACTUAL_USD_COL] < 50
    out["flag_actual_over_100k_usd"] = out[ACTUAL_USD_COL] >= 100_000
    out["flag_actual_over_1m_usd"] = out[ACTUAL_USD_COL] >= 1_000_000
    out["flag_non_usd_currency"] = out["actual_currency"].fillna("") != "USD"
    out["flag_small_native_price"] = (
        out["actual_currency"].isin(["USD", "EUR"])
        & out["actual_price_native"].notna()
        & (out["actual_price_native"] < 50)
    )
    out["label_qc_bucket"] = "core_50_to_100k_usd"
    out.loc[out["flag_actual_under_50_usd"], "label_qc_bucket"] = "review_under_50_usd"
    out.loc[
        out["flag_actual_over_100k_usd"] & ~out["flag_actual_over_1m_usd"],
        "label_qc_bucket",
    ] = "review_over_100k_usd"
    out.loc[out["flag_actual_over_1m_usd"], "label_qc_bucket"] = "review_over_1m_usd"
    out["actual_usd_band"] = pd.cut(
        out[ACTUAL_USD_COL],
        bins=[-np.inf, 50, 500, 2_000, 10_000, 100_000, 1_000_000, np.inf],
        labels=[
            "<50",
            "50-500",
            "500-2k",
            "2k-10k",
            "10k-100k",
            "100k-1m",
            "1m+",
        ],
        right=False,
    ).astype(str)
    return out


def metric_row(label: str, df: pd.DataFrame, candidate: str, pred_col: str) -> dict[str, object]:
    valid = df[[ACTUAL_COL, pred_col]].dropna().copy()
    valid = valid[(valid[ACTUAL_COL] > 0) & (valid[pred_col] > 0)]
    if valid.empty:
        return {
            "group": label,
            "candidate": candidate,
            "n": 0,
            "MdAPE": np.nan,
            "MAPE": np.nan,
            "p95_APE": np.nan,
            "RMSE_log": np.nan,
            "median_ratio": np.nan,
            "over_3x_n": 0,
            "under_1_3x_n": 0,
            "within_5pct_n": 0,
            "range_coverage": np.nan,
        }
    actual = valid[ACTUAL_COL].to_numpy(dtype=float)
    pred = valid[pred_col].to_numpy(dtype=float)
    ape = np.abs(pred - actual) / actual
    ratio = pred / actual
    pred_log = np.log(np.clip(pred, 1_000.0, None))
    actual_log = np.log(np.clip(actual, 1_000.0, None))
    range_coverage = np.nan
    if {RANGE_LOW_COL, RANGE_HIGH_COL}.issubset(df.columns) and pred_col == PRICE_COL:
        range_df = df.loc[valid.index, [ACTUAL_COL, RANGE_LOW_COL, RANGE_HIGH_COL]].dropna()
        if not range_df.empty:
            range_coverage = (
                (range_df[ACTUAL_COL] >= range_df[RANGE_LOW_COL])
                & (range_df[ACTUAL_COL] <= range_df[RANGE_HIGH_COL])
            ).mean()
    return {
        "group": label,
        "candidate": candidate,
        "n": len(valid),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "median_ratio": float(np.median(ratio)),
        "over_3x_n": int((ratio > 3).sum()),
        "under_1_3x_n": int((ratio < 1 / 3).sum()),
        "within_5pct_n": int((ape <= 0.05).sum()),
        "range_coverage": float(range_coverage) if not pd.isna(range_coverage) else np.nan,
    }


def build_group_metrics(df: pd.DataFrame) -> pd.DataFrame:
    groups: list[tuple[str, pd.DataFrame]] = [
        ("all_numeric_labels", df),
        ("actual_50_plus_usd", df[df[ACTUAL_USD_COL] >= 50]),
        (
            "core_50_to_100k_usd",
            df[(df[ACTUAL_USD_COL] >= 50) & (df[ACTUAL_USD_COL] < 100_000)],
        ),
        ("review_under_50_usd", df[df["flag_actual_under_50_usd"]]),
        ("review_over_100k_usd", df[df["flag_actual_over_100k_usd"]]),
        ("review_over_1m_usd", df[df["flag_actual_over_1m_usd"]]),
        ("usd_currency", df[df["actual_currency"] == "USD"]),
        ("non_usd_currency", df[df["flag_non_usd_currency"]]),
    ]
    rows = []
    for group, frame in groups:
        for candidate, pred_col in CANDIDATES:
            if pred_col in frame.columns:
                rows.append(metric_row(group, frame, candidate, pred_col))
    return pd.DataFrame(rows)


def build_price_band_metrics(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for band, frame in df.groupby("actual_usd_band", observed=False):
        rows.append(metric_row(str(band), frame, "service_primary", PRICE_COL))
    return pd.DataFrame(rows)


def build_qc_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for bucket, frame in df.groupby("label_qc_bucket"):
        rows.append(
            {
                "label_qc_bucket": bucket,
                "n": len(frame),
                "actual_usd_median": frame[ACTUAL_USD_COL].median(),
                "pred_usd_median": (frame[PRICE_COL] / 1380.0).median(),
                "ape_median": (np.abs(frame[PRICE_COL] - frame[ACTUAL_COL]) / frame[ACTUAL_COL]).median(),
                "ape_mean": (np.abs(frame[PRICE_COL] - frame[ACTUAL_COL]) / frame[ACTUAL_COL]).mean(),
                "svc_group_n_median": frame["svc_group_n"].median(),
                "price_range_ratio_median": frame["l10_price_range_ratio"].median(),
            }
        )
    return pd.DataFrame(rows)


def selected_cases(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "_v01_row_id",
        "_track6_row_id",
        "artist_name",
        "title",
        "actual_currency",
        "actual_price_native",
        ACTUAL_COL,
        ACTUAL_USD_COL,
        PRICE_COL,
        "service_primary_ape",
        "service_primary_ratio",
        "label_qc_bucket",
        "warm_cold_route",
        "service_primary_candidate",
        "svc_group_level",
        "svc_group_n",
        "medium_support_bucket",
        "area_cm2",
        "l10_price_range_ratio",
        "service_confidence_tier",
    ]
    existing = [col for col in cols if col in df.columns]
    return df[existing].copy()


def format_metric_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "median_ratio", "range_coverage"]:
        if col in out.columns:
            out[col] = out[col].map(lambda x: fmt_float(x, 4))
    return out


def build_report(
    df: pd.DataFrame,
    service_metrics: pd.DataFrame,
    band_metrics: pd.DataFrame,
    qc_summary: pd.DataFrame,
    review_low: pd.DataFrame,
    high_tail: pd.DataFrame,
    severe: pd.DataFrame,
) -> str:
    all_metrics = service_metrics[service_metrics["group"] == "all_numeric_labels"].iloc[0]
    no_low_metrics = service_metrics[service_metrics["group"] == "actual_50_plus_usd"].iloc[0]
    core_metrics = service_metrics[service_metrics["group"] == "core_50_to_100k_usd"].iloc[0]
    low_metrics = service_metrics[service_metrics["group"] == "review_under_50_usd"].iloc[0]
    high_metrics = service_metrics[service_metrics["group"] == "review_over_100k_usd"].iloc[0]

    report = f"""# OP-V01-CAL-01 라벨 검수 기준 평가 분리 결과

## 1. 실행 요약

- 입력 파일: `{INPUT.relative_to(REPO)}`
- 숫자 실제 가격 라벨 수: {len(df):,}건
- Warm/Cold 라우팅: 0604 라벨 보유 행은 모두 Warm으로 평가됨
- 기준 예측값: `service_primary_pred_price_krw`
- 기준 후보: `pp_v8_compact_blend_mape_guarded`
- 이 실험은 예측값을 바꾸지 않고, 평가 그룹만 분리함

## 2. 핵심 결과

| 구분 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
| --- | --- | --- | --- | --- | --- |
| 전체 숫자 라벨 | {fmt_float(all_metrics['MdAPE'])} | {fmt_float(all_metrics['MAPE'])} | {fmt_float(all_metrics['p95_APE'])} | {fmt_float(all_metrics['RMSE_log'])} | 50달러 미만 라벨 때문에 MAPE가 크게 왜곡됨 |
| 50달러 이상 | {fmt_float(no_low_metrics['MdAPE'])} | {fmt_float(no_low_metrics['MAPE'])} | {fmt_float(no_low_metrics['p95_APE'])} | {fmt_float(no_low_metrics['RMSE_log'])} | 저가 이상 라벨을 제외하면 평균 오차가 안정됨 |
| 50달러 이상 10만 달러 미만 | {fmt_float(core_metrics['MdAPE'])} | {fmt_float(core_metrics['MAPE'])} | {fmt_float(core_metrics['p95_APE'])} | {fmt_float(core_metrics['RMSE_log'])} | 일반 운영 평가의 핵심 구간 |
| 50달러 미만 검수 대상 | {fmt_float(low_metrics['MdAPE'])} | {fmt_float(low_metrics['MAPE'])} | {fmt_float(low_metrics['p95_APE'])} | {fmt_float(low_metrics['RMSE_log'])} | 가격 단위/라벨 확인이 먼저 필요 |
| 10만 달러 이상 고가 꼬리 | {fmt_float(high_metrics['MdAPE'])} | {fmt_float(high_metrics['MAPE'])} | {fmt_float(high_metrics['p95_APE'])} | {fmt_float(high_metrics['RMSE_log'])} | 고가 작품 과소 예측 방어 대상 |

## 3. 라벨 검수 그룹 분포

{md_table(qc_summary)}

## 4. 실제 가격 구간별 지표

{md_table(format_metric_frame(band_metrics))}

## 5. 후보별 그룹 지표

{md_table(format_metric_frame(service_metrics))}

## 6. 50달러 미만 검수 대상

{md_table(review_low.head(30))}

## 7. 10만 달러 이상 고가 꼬리 대상

{md_table(high_tail.head(30))}

## 8. 후속 보정 타겟

{md_table(severe.head(50))}

## 9. 판단

- 0604 전체 MAPE는 모델 성능만의 문제가 아니라, 매우 낮은 실제 가격 라벨의 영향이 크다.
- 50달러 미만 라벨은 가격 단위, 수집 라벨, 판매 메시지 해석을 먼저 검수해야 한다.
- 일반 운영 구간은 50달러 이상 10만 달러 미만으로 분리해서 보는 것이 더 현실적이다.
- 고가 작품은 점가격을 바로 올리기보다 가격 범위 상단, 신뢰도, 고가 가능성 플래그부터 보정하는 편이 안전하다.
- 다음 실험은 저가/소형 과대 예측 방어와 고가 과소 예측 방어를 분리해서 진행한다.

## 10. 산출물

- `outputs/label_qc_flags.csv`
- `outputs/metrics_by_candidate_group.csv`
- `outputs/metrics_by_group_service_primary.csv`
- `outputs/metrics_by_actual_usd_band.csv`
- `outputs/label_qc_summary.csv`
- `outputs/review_under_50_usd.csv`
- `outputs/review_over_100k_usd.csv`
- `outputs/next_correction_targets.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    return report


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = add_qc_flags(load_data())
    metrics = build_group_metrics(df)
    service_metrics = metrics[metrics["candidate"] == "service_primary"].copy()
    band_metrics = build_price_band_metrics(df)
    qc_summary = build_qc_summary(df)

    review_low = selected_cases(df[df["flag_actual_under_50_usd"]].sort_values("service_primary_ape", ascending=False))
    high_tail = selected_cases(df[df["flag_actual_over_100k_usd"]].sort_values(ACTUAL_USD_COL, ascending=False))
    base_50_plus = df[df[ACTUAL_USD_COL] >= 50].copy()
    severe_mask = (base_50_plus["service_primary_ratio"] > 3) | (base_50_plus["service_primary_ratio"] < 1 / 3)
    severe = selected_cases(base_50_plus[severe_mask].sort_values("service_primary_ape", ascending=False))

    label_cols = [
        "_v01_row_id",
        "_track6_row_id",
        "artist_name",
        "title",
        "actual_currency",
        "actual_price_native",
        ACTUAL_COL,
        ACTUAL_USD_COL,
        PRICE_COL,
        "service_primary_ape",
        "service_primary_ratio",
        "label_qc_bucket",
        "actual_usd_band",
        "flag_actual_under_50_usd",
        "flag_actual_over_100k_usd",
        "flag_actual_over_1m_usd",
        "flag_non_usd_currency",
        "flag_small_native_price",
    ]
    df[[col for col in label_cols if col in df.columns]].to_csv(
        OUTPUT_DIR / "label_qc_flags.csv", index=False
    )
    metrics.to_csv(OUTPUT_DIR / "metrics_by_candidate_group.csv", index=False)
    service_metrics.to_csv(OUTPUT_DIR / "metrics_by_group_service_primary.csv", index=False)
    band_metrics.to_csv(OUTPUT_DIR / "metrics_by_actual_usd_band.csv", index=False)
    qc_summary.to_csv(OUTPUT_DIR / "label_qc_summary.csv", index=False)
    review_low.to_csv(OUTPUT_DIR / "review_under_50_usd.csv", index=False)
    high_tail.to_csv(OUTPUT_DIR / "review_over_100k_usd.csv", index=False)
    severe.to_csv(OUTPUT_DIR / "next_correction_targets.csv", index=False)

    report = build_report(
        df=df,
        service_metrics=service_metrics,
        band_metrics=band_metrics,
        qc_summary=qc_summary,
        review_low=review_low,
        high_tail=high_tail,
        severe=severe,
    )
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(markdown_to_html(report), encoding="utf-8")


if __name__ == "__main__":
    main()

