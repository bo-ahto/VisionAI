#!/usr/bin/env python3
"""Analyze labeled 2026-06-04 Warm prediction rows for price spikes.

This script reads the labeled service-style prediction CSV and creates a
focused error analysis for Warm-only rows.  The goal is not to train a new
model here; it is to identify which kinds of rows produce unstable prices and
which correction policy should be tested next.
"""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "models" / "track6" / "price_prediction_v0.1" / "data" / "predictions_all_price_0604.csv"
EXP_DIR = REPO / "experiments" / "track6" / "OP-0604_warm_price_spike_error_analysis"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

# These rates match the conversion columns already present in the prediction CSV.
EXCHANGE_RATES_TO_KRW = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "KRW": 1.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}

PREDICTION_CANDIDATES = {
    "svc_group_median": "svc_group_median_pred_price_krw",
    "legacy_warm_huber": "legacy_warm_huber_pred_price_krw",
}


def parse_price(message: object) -> tuple[float, str | None, float]:
    """Parse numeric sale price from Artsy-style sale message text.

    Non-numeric states such as "Sold", "Price on request", and missing values
    return NaN because they cannot be used as ground-truth price labels.
    """
    if pd.isna(message):
        return np.nan, None, np.nan

    text = str(message).strip()
    currency: str | None = None
    raw = text

    if text.startswith("US$"):
        currency = "USD"
        raw = text.replace("US$", "", 1)
    elif text.startswith("KRW") or text.startswith("₩"):
        currency = "KRW"
        raw = text.replace("KRW", "", 1).replace("₩", "", 1)
    elif text.startswith("€"):
        currency = "EUR"
        raw = text.replace("€", "", 1)
    elif text.startswith("£"):
        currency = "GBP"
        raw = text.replace("£", "", 1)
    elif text.startswith("HK$"):
        currency = "HKD"
        raw = text.replace("HK$", "", 1)
    elif text.startswith("¥"):
        currency = "JPY"
        raw = text.replace("¥", "", 1)

    if currency is None:
        return np.nan, None, np.nan

    match = re.search(r"[-+]?[0-9][0-9,]*(?:\.[0-9]+)?", raw)
    if not match:
        return np.nan, currency, np.nan

    native = float(match.group(0).replace(",", ""))
    return native, currency, native * EXCHANGE_RATES_TO_KRW[currency]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace({0: np.nan})


def add_actual_and_error_columns(df: pd.DataFrame) -> pd.DataFrame:
    parsed = df["sale_message"].apply(parse_price)
    df[["actual_price_native", "actual_currency", "actual_price_krw"]] = pd.DataFrame(parsed.tolist(), index=df.index)
    df["actual_price_usd_equiv"] = df["actual_price_krw"] / EXCHANGE_RATES_TO_KRW["USD"]
    df["has_numeric_actual"] = df["actual_price_krw"].notna()

    df["actual_label_quality"] = np.select(
        [
            ~df["has_numeric_actual"],
            df["actual_price_usd_equiv"] < 50,
            df["actual_price_usd_equiv"] >= 100_000,
        ],
        [
            "not_numeric_actual",
            "review_very_low_price_under_50_usd",
            "review_high_tail_over_100k_usd",
        ],
        default="numeric_actual",
    )

    actual_bins = [-np.inf, 50, 100, 500, 1_000, 5_000, 20_000, 100_000, np.inf]
    actual_labels = [
        "<50usd_review",
        "50_100usd",
        "100_500usd",
        "500_1k_usd",
        "1k_5k_usd",
        "5k_20k_usd",
        "20k_100k_usd",
        "100k_plus_usd",
    ]
    df["actual_price_band"] = pd.cut(df["actual_price_usd_equiv"], actual_bins, labels=actual_labels)

    area_bins = [-np.inf, 500, 1_500, 5_000, 15_000, 50_000, np.inf]
    area_labels = ["area_missing_or_tiny", "small", "medium", "large", "very_large", "extreme_large"]
    df["area_band"] = pd.cut(df["area_cm2"], area_bins, labels=area_labels)
    df["area_band"] = df["area_band"].cat.add_categories(["missing"]).fillna("missing")

    group_n_bins = [-np.inf, 5, 10, 30, 100, 1_000, np.inf]
    group_n_labels = ["n_le_5", "n_6_10", "n_11_30", "n_31_100", "n_101_1000", "n_1000_plus"]
    df["svc_group_n_band"] = pd.cut(df["svc_group_n"], group_n_bins, labels=group_n_labels)

    for name, col in PREDICTION_CANDIDATES.items():
        df[f"{name}_ratio"] = safe_divide(df[col], df["actual_price_krw"])
        df[f"{name}_ape"] = (df[col] - df["actual_price_krw"]).abs() / df["actual_price_krw"]
        df[f"{name}_log_error"] = np.log(df[col].clip(lower=1)) - np.log(df["actual_price_krw"].clip(lower=1))
        df[f"{name}_spike_type"] = np.select(
            [
                df[f"{name}_ratio"] >= 3,
                df[f"{name}_ratio"] <= 1 / 3,
            ],
            ["over_prediction_3x_plus", "under_prediction_one_third_or_less"],
            default="within_3x",
        )

    return df


def classify_likely_cause(row: pd.Series) -> str:
    """Assign a practical first-pass cause bucket for the svc_group_median error."""
    if not row["has_numeric_actual"]:
        return "정답 가격 없음"
    if row["actual_price_usd_equiv"] < 50:
        return "정답 가격 표기 점검 필요: 50달러 이하 극저가"
    if pd.isna(row.get("width_cm")) or pd.isna(row.get("height_cm")) or pd.isna(row.get("area_cm2")):
        return "크기 결측으로 fallback 의존"
    if row.get("svc_group_level") == "global":
        return "유사 작품 묶음 실패로 global fallback 사용"
    if row.get("svc_group_n", 0) < 10:
        return "유사 작품 표본 수 부족"
    if row.get("actual_price_usd_equiv", 0) >= 100_000 and row.get("svc_group_median_ratio", 1) <= 1 / 3:
        return "고가 작품 상방 꼬리 미반영"
    if row.get("area_cm2", 0) >= 50_000 and row.get("svc_group_median_ratio", 1) <= 1 / 3:
        return "대형 작품 상방 효과 부족"
    if row.get("area_cm2", np.inf) <= 500 and row.get("svc_group_median_ratio", 1) >= 3:
        return "소형/저가 작품에 작가 기준값 과대 적용"
    if row.get("svc_group_median_ratio", 1) >= 3:
        return "저가 구간 과대 예측"
    if row.get("svc_group_median_ratio", 1) <= 1 / 3:
        return "고가 구간 과소 예측"
    return "정상 범위 또는 세부 잔차"


def metric_row(frame: pd.DataFrame, label: str, candidate: str) -> dict[str, object]:
    ape = frame[f"{candidate}_ape"].dropna()
    ratio = frame[f"{candidate}_ratio"].dropna()
    return {
        "scope": label,
        "candidate": candidate,
        "n": int(len(ape)),
        "MdAPE": float(ape.median()) if len(ape) else np.nan,
        "MAPE": float(ape.mean()) if len(ape) else np.nan,
        "p95_APE": float(ape.quantile(0.95)) if len(ape) else np.nan,
        "median_ratio": float(ratio.median()) if len(ratio) else np.nan,
        "over_3x_n": int((ratio >= 3).sum()),
        "under_1_3x_n": int((ratio <= 1 / 3).sum()),
    }


def summarize_group(frame: pd.DataFrame, by: str, candidate: str = "svc_group_median") -> pd.DataFrame:
    rows = []
    for value, group in frame.groupby(by, dropna=False, observed=False):
        ape = group[f"{candidate}_ape"].dropna()
        ratio = group[f"{candidate}_ratio"].dropna()
        if len(ape) == 0:
            continue
        rows.append(
            {
                "segment_type": by,
                "segment": str(value),
                "n": int(len(group)),
                "MdAPE": float(ape.median()),
                "MAPE": float(ape.mean()),
                "p95_APE": float(ape.quantile(0.95)),
                "median_ratio": float(ratio.median()),
                "over_3x_n": int((ratio >= 3).sum()),
                "under_1_3x_n": int((ratio <= 1 / 3).sum()),
                "actual_median_krw": float(group["actual_price_krw"].median()),
                "pred_median_krw": float(group[PREDICTION_CANDIDATES[candidate]].median()),
            }
        )
    return pd.DataFrame(rows)


def compare_directly_available_candidates(labeled: pd.DataFrame, usable: pd.DataFrame) -> pd.DataFrame:
    """Compare prediction columns that are directly available in the input CSV.

    The exact PP-SVC3 v0.1 70:30 policy is not directly runnable in this file,
    so this table is a diagnostic check for likely correction directions only.
    """
    rows: list[dict[str, object]] = []

    def add(scope: str, frame: pd.DataFrame, name: str, pred: pd.Series) -> None:
        ape = (pred - frame["actual_price_krw"]).abs() / frame["actual_price_krw"]
        ratio = pred / frame["actual_price_krw"]
        rows.append(
            {
                "scope": scope,
                "candidate": name,
                "n": int(len(frame)),
                "MdAPE": float(ape.median()),
                "MAPE": float(ape.mean()),
                "p95_APE": float(ape.quantile(0.95)),
                "median_ratio": float(ratio.median()),
                "over_3x_n": int((ratio >= 3).sum()),
                "under_1_3x_n": int((ratio <= 1 / 3).sum()),
            }
        )

    for scope, frame in [("numeric_actual_all", labeled), ("excluding_under_50_usd", usable)]:
        available = {
            "svc_q25": frame["svc_group_q25_price_krw"],
            "svc_median": frame["svc_group_median_pred_price_krw"],
            "svc_q75": frame["svc_group_q75_price_krw"],
            "legacy_warm_huber": frame["legacy_warm_huber_pred_price_krw"],
        }
        for name, pred in available.items():
            add(scope, frame, name, pred)

        svc_log = np.log(frame["svc_group_median_pred_price_krw"].clip(lower=1))
        huber_log = np.log(frame["legacy_warm_huber_pred_price_krw"].clip(lower=1))
        for weight in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            pred = np.exp(weight * svc_log + (1.0 - weight) * huber_log)
            add(scope, frame, f"log_blend_svc{weight:.1f}_huber{1.0 - weight:.1f}", pred)

    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, max_rows: int = 20) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:,.4f}")
    view = view.fillna("")
    headers = [str(col) for col in view.columns]
    rows = [[str(value).replace("\n", " ") for value in row] for row in view.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_html_report(markdown: str) -> str:
    # Lightweight markdown-to-readable-HTML for this report's limited syntax.
    lines = []
    in_table = False
    in_list = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("|"):
            if in_list:
                lines.append("</ul>")
                in_list = False
            if not in_table:
                lines.append("<pre>")
                in_table = True
            lines.append(html.escape(line))
        else:
            if in_table:
                lines.append("</pre>")
                in_table = False
            if in_list:
                lines.append("</ul>")
                in_list = False
            if line:
                lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        lines.append("</pre>")
    if in_list:
        lines.append("</ul>")
    body = "\n".join(lines)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>0604 Warm 가격 튐 구간 분석</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.62;color:#1f2933;max-width:1180px;margin:32px auto;padding:0 24px}}
h1{{font-size:30px}} h2{{border-top:1px solid #d8dee4;padding-top:22px;margin-top:36px}} h3{{margin-top:26px}}
pre{{white-space:pre-wrap;background:#f8fafc;border:1px solid #d8dee4;border-radius:8px;padding:14px;overflow:auto}}
li{{margin:5px 0}}
</style></head><body>{body}</body></html>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT)
    df = add_actual_and_error_columns(df)
    df["svc_error_cause"] = df.apply(classify_likely_cause, axis=1)

    labeled = df[df["has_numeric_actual"]].copy()
    usable = labeled[labeled["actual_price_usd_equiv"] >= 50].copy()

    metrics = pd.DataFrame(
        [
            metric_row(labeled, "numeric_actual_all", "svc_group_median"),
            metric_row(labeled, "numeric_actual_all", "legacy_warm_huber"),
            metric_row(usable, "numeric_actual_excluding_under_50_usd", "svc_group_median"),
            metric_row(usable, "numeric_actual_excluding_under_50_usd", "legacy_warm_huber"),
        ]
    )

    segment_frames = []
    for group_col in [
        "actual_label_quality",
        "actual_price_band",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n_band",
        "area_band",
        "medium_support_bucket",
        "svc_error_cause",
    ]:
        segment_frames.append(summarize_group(labeled, group_col, "svc_group_median"))
    segment_summary = pd.concat(segment_frames, ignore_index=True)
    candidate_comparison = compare_directly_available_candidates(labeled, usable)

    artist_rows = []
    for artist, group in labeled.groupby("artist_key", dropna=False):
        ape = group["svc_group_median_ape"].dropna()
        ratio = group["svc_group_median_ratio"].dropna()
        if len(ape) == 0:
            continue
        worst = group.sort_values("svc_group_median_ape", ascending=False).iloc[0]
        artist_rows.append(
            {
                "artist_key": artist,
                "artist_name": group["artist_name"].iloc[0],
                "n": int(len(group)),
                "MdAPE": float(ape.median()),
                "MAPE": float(ape.mean()),
                "p95_APE": float(ape.quantile(0.95)),
                "median_ratio": float(ratio.median()),
                "over_3x_n": int((ratio >= 3).sum()),
                "under_1_3x_n": int((ratio <= 1 / 3).sum()),
                "worst_title": worst["title"],
                "worst_sale_message": worst["sale_message"],
                "worst_ratio": float(worst["svc_group_median_ratio"]),
                "worst_cause": worst["svc_error_cause"],
            }
        )
    artist_summary = pd.DataFrame(artist_rows).sort_values(["MAPE", "n"], ascending=[False, False])

    top_cols = [
        "_v01_row_id",
        "_track6_row_id",
        "title",
        "artist_name",
        "sale_message",
        "actual_price_krw",
        "svc_group_median_pred_price_krw",
        "svc_group_median_ratio",
        "svc_group_median_ape",
        "legacy_warm_huber_pred_price_krw",
        "legacy_warm_huber_ratio",
        "legacy_warm_huber_ape",
        "svc_error_cause",
        "actual_label_quality",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "width_cm",
        "height_cm",
        "area_cm2",
        "medium_category",
        "support_category",
        "medium_support_bucket",
    ]
    spike_cases = labeled.sort_values("svc_group_median_ape", ascending=False)[top_cols].head(250)
    over_cases = labeled[labeled["svc_group_median_ratio"] >= 3].sort_values("svc_group_median_ratio", ascending=False)[top_cols].head(150)
    under_cases = labeled[labeled["svc_group_median_ratio"] <= 1 / 3].sort_values("svc_group_median_ratio", ascending=True)[top_cols].head(150)

    df.to_csv(OUT_DIR / "predictions_with_parsed_actual_and_errors.csv", index=False)
    metrics.to_csv(OUT_DIR / "overall_metrics.csv", index=False)
    segment_summary.to_csv(OUT_DIR / "segment_error_summary.csv", index=False)
    candidate_comparison.to_csv(OUT_DIR / "direct_candidate_comparison.csv", index=False)
    artist_summary.to_csv(OUT_DIR / "artist_error_summary.csv", index=False)
    spike_cases.to_csv(OUT_DIR / "top_price_spike_cases.csv", index=False)
    over_cases.to_csv(OUT_DIR / "top_over_prediction_cases.csv", index=False)
    under_cases.to_csv(OUT_DIR / "top_under_prediction_cases.csv", index=False)

    currency_counts = labeled["actual_currency"].value_counts(dropna=False).reset_index()
    currency_counts.columns = ["currency", "n"]
    quality_counts = df["actual_label_quality"].value_counts(dropna=False).reset_index()
    quality_counts.columns = ["actual_label_quality", "n"]
    cause_counts = labeled["svc_error_cause"].value_counts(dropna=False).reset_index()
    cause_counts.columns = ["svc_error_cause", "n"]

    main_findings = [
        "전체 6,873건은 모두 Warm route로 분류됨",
        "숫자 가격으로 파싱 가능한 정답은 837건이며, 나머지는 Sold, Price on request, 결측 등으로 정량 평가에서 제외",
        "예측 파일의 외화 환산은 1 USD = 1,380 KRW 기준과 일치",
        "현재 파일에는 정확한 PP-SVC3 70:30 v0.1 주 후보가 아니라 유사 작품 기반 가격 피처와 legacy Warm Huber baseline이 포함됨",
        "큰 오차의 상당수는 US$1, US$10, US$20 같은 극저가 라벨에서 발생하므로 보정 학습 전에 라벨 품질 필터가 필요",
        "유사 작품 기반 가격 피처는 중앙 구간에서는 Huber보다 안정적이지만, 고가 작품 상방 꼬리와 극저가/소형 작품 하방 꼬리에서 튀는 구간이 생김",
    ]

    report = f"""# 0604 Warm 가격 튐 구간 분석

## 1. 분석 대상

- 입력 파일: `{INPUT.relative_to(REPO)}`
- 전체 행 수: `{len(df):,}`
- Warm route 행 수: `{int((df['warm_cold_route'] == 'warm').sum()):,}`
- 숫자 정답 가격 행 수: `{len(labeled):,}`
- 숫자 정답 가격 제외 행 수: `{int((~df['has_numeric_actual']).sum()):,}`
- 환산 기준: `1 USD = 1,380 KRW`, `1 EUR = 1,530 KRW`

## 2. 주의할 점

- 이 파일은 Warm 데이터만 포함
- `sale_message`가 `Sold`, `Price on request`, 결측인 행은 실제 가격을 알 수 없어 오차 계산에서 제외
- `svc_group_median_pred_price_krw`: 유사 작품 기반 가격 피처의 중앙값 예측
- `legacy_warm_huber_pred_price_krw`: 기존 Warm Huber baseline 예측
- 정확한 v0.1 70:30 결합 후보는 이 파일에서 직접 계산된 컬럼이 아니므로 별도 artifact화가 필요

## 3. 핵심 요약
"""
    report += "\n".join(f"- {item}" for item in main_findings)
    report += "\n\n## 4. 전체 성능\n\n"
    report += markdown_table(metrics)
    report += "\n\n## 5. 정답 가격 상태\n\n"
    report += "### 통화별 숫자 라벨\n\n"
    report += markdown_table(currency_counts)
    report += "\n\n### 라벨 품질 플래그\n\n"
    report += markdown_table(quality_counts)
    report += "\n\n## 6. 가격 튐 원인 후보\n\n"
    report += markdown_table(cause_counts)
    report += "\n\n## 7. 주요 segment별 오차\n\n"
    important_segments = segment_summary[
        segment_summary["segment_type"].isin(
            ["actual_price_band", "svc_group_level", "svc_coverage_tier", "svc_group_n_band", "area_band", "svc_error_cause"]
        )
    ].sort_values(["segment_type", "MAPE"], ascending=[True, False])
    report += markdown_table(important_segments, max_rows=80)
    report += "\n\n## 8. 큰 오차 사례 상위\n\n"
    report += markdown_table(spike_cases[[
        "_v01_row_id", "title", "artist_name", "sale_message", "svc_group_median_ratio",
        "svc_group_median_ape", "svc_error_cause", "svc_group_level", "svc_group_n", "area_cm2"
    ]], max_rows=40)
    report += "\n\n## 9. 직접 계산 가능한 후보 비교\n\n"
    report += "- 이 비교는 최종 v0.1 주 후보가 아니라 현재 파일에 들어 있는 컬럼만 사용한 사전 점검\n"
    report += "- `excluding_under_50_usd`는 `US$1`, `US$10`처럼 검수 필요한 극저가 라벨을 제외한 기준\n\n"
    best_mdape = candidate_comparison.sort_values(["scope", "MdAPE", "MAPE", "p95_APE"]).groupby("scope", as_index=False).head(5)
    report += markdown_table(best_mdape, max_rows=20)
    report += "\n\n해석:\n\n"
    report += "- 극저가 라벨을 제외하면 `svc_median` 단독보다 `svc_median`과 `legacy Huber`를 로그 공간에서 섞는 방식이 MdAPE를 낮출 가능성이 있음\n"
    report += "- MAPE 기준으로는 Huber 비중을 더 높인 로그 결합이나 `svc_q25`가 유리하지만, `svc_q25`는 과소 예측 수가 크게 늘어 단독 적용은 위험\n"
    report += "- 따라서 다음 보정 실험은 전체 일괄 결합보다 `svc_group_level`, `svc_group_n`, `area_band`, `pred_log bin`별로 결합 가중치를 다르게 주는 방식이 적합\n"
    report += "\n\n## 10. 보정 방향\n\n"
    report += """- 1차 보정 전 라벨 필터: `actual_price_usd_equiv < 50` 라벨은 실제 가격인지 검수 후 보정 학습에서 제외
- 유사 작품 표본 수 기반 보정: `svc_group_n < 10`, `low_n`, `global fallback`은 예측 신뢰도를 낮게 표시하고 보정 강도를 별도로 둠
- 소형/저가 과대 예측 방지: 작은 면적, 낮은 예측가, 낮은 표본 수 구간은 `q25` 또는 낮은 분위값 쪽으로 shrink하는 실험 필요
- 고가 작품 과소 예측 방지: 실제 고가 tail에서 Huber가 더 가까운 사례가 있어, 대형/고가 신호가 있는 경우 `max(svc, huber)` 또는 Huber 가중치 상향 실험 필요
- segment residual 보정: 실제 가격이 아니라 예측 시점에 사용 가능한 `pred_log bin`, `svc_group_level`, `svc_group_n_band`, `area_band`, `medium_support_bucket` 기준으로 median residual 보정값을 학습
- 서비스 표시 보정: 크기 결측, global fallback, low_n은 단일 가격보다 범위와 낮은 신뢰도를 함께 표시
"""

    report += "\n## 11. 생성 파일\n\n"
    for file in sorted(OUT_DIR.glob("*.csv")):
        report += f"- `{file.relative_to(REPO)}`\n"

    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(render_html_report(report), encoding="utf-8")
    print(REPORT_DIR / "result_report.md")


if __name__ == "__main__":
    main()
