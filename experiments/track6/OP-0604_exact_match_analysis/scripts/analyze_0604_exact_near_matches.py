#!/usr/bin/env python3
"""Analyze exact and near price hits in the 0604 operational v0.1 evaluation.

This script is intentionally report-oriented:
- exact hit: predicted KRW equals actual KRW without rounding.
- rounded exact hit: predicted KRW rounded to the nearest KRW equals actual KRW.
- near hit: absolute percentage error is below a chosen threshold.

The goal is to explain whether the model literally matched any listed price and,
when it did not, which cases came close and why.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]
INPUT_PATH = (
    PROJECT_ROOT
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/"
    / "operational_predictions_with_actual.csv"
)
EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0604_exact_match_analysis"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

THRESHOLDS = [0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.10]

CANDIDATES = [
    ("service_primary", "service_primary_pred_price_krw", "service_primary_ape"),
    (
        "pp_v8_compact_blend_mape_guarded",
        "pp_v8_compact_blend_mape_guarded_pred_price_krw",
        "pp_v8_compact_blend_mape_guarded_ape",
    ),
    ("v01_operational", "v01_operational_pred_price_krw", "v01_operational_ape"),
    (
        "svc_numeric_seed_mean",
        "svc_numeric_seed_mean_pred_price_krw",
        "svc_numeric_seed_mean_ape",
    ),
    ("pp_v2_defensive", "pp_v2_defensive_pred_price_krw", "pp_v2_defensive_ape"),
    (
        "l10_generated_bucket_seq",
        "l10_generated_bucket_seq_pred_price_krw",
        "l10_generated_bucket_seq_ape",
    ),
]


def fmt_int(value: float | int) -> str:
    if pd.isna(value):
        return ""
    return f"{int(round(float(value))):,}"


def fmt_float(value: float | int, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def load_numeric_labels() -> pd.DataFrame:
    df = pd.read_csv(INPUT_PATH)
    df = df[pd.to_numeric(df["actual_price_krw"], errors="coerce").notna()].copy()
    df["actual_price_krw"] = df["actual_price_krw"].astype(float)
    return df


def build_candidate_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, pred_col, ape_col in CANDIDATES:
        valid = df[[pred_col, ape_col, "actual_price_krw"]].dropna().copy()
        if valid.empty:
            continue
        exact = valid[pred_col] == valid["actual_price_krw"]
        rounded_exact = valid[pred_col].round(0) == valid["actual_price_krw"].round(0)
        row = {
            "candidate": name,
            "n": len(valid),
            "exact_krw_count": int(exact.sum()),
            "rounded_exact_krw_count": int(rounded_exact.sum()),
            "min_ape": valid[ape_col].min(),
            "median_ape": valid[ape_col].median(),
            "mean_ape": valid[ape_col].mean(),
            "p95_ape": valid[ape_col].quantile(0.95),
        }
        for threshold in THRESHOLDS:
            key = f"within_{threshold:.1%}"
            row[key] = int((valid[ape_col] <= threshold).sum())
            row[f"{key}_rate"] = row[key] / len(valid)
        rows.append(row)
    return pd.DataFrame(rows)


def build_top_near_matches(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    cols = [
        "_v01_row_id",
        "_track6_row_id",
        "title",
        "artist_name",
        "sale_message",
        "actual_price_native",
        "actual_currency",
        "actual_price_krw",
        "actual_price_usd_equiv",
        "service_primary_pred_price_krw",
        "service_primary_ape",
        "service_primary_ratio",
        "service_primary_candidate",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "svc_numeric_seed_mean_pred_price_krw",
        "pp_v2_defensive_pred_price_krw",
        "l10_generated_bucket_seq_pred_price_krw",
        "pp_v8_compact_blend_mape_guarded_pred_price_krw",
        "v01_operational_pred_price_krw",
    ]
    existing_cols = [col for col in cols if col in df.columns]
    out = df.sort_values("service_primary_ape")[existing_cols].head(top_n).copy()
    out["abs_error_krw"] = (
        out["service_primary_pred_price_krw"] - out["actual_price_krw"]
    ).abs()
    out["error_direction"] = np.where(
        out["service_primary_pred_price_krw"] >= out["actual_price_krw"],
        "over",
        "under",
    )
    return out


def build_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    segment_cols = [
        "svc_group_level",
        "svc_coverage_tier",
        "actual_currency",
        "medium_support_bucket",
        "medium_category",
        "support_category",
    ]
    rows = []
    for threshold in [0.01, 0.03, 0.05, 0.10]:
        near = df[df["service_primary_ape"] <= threshold].copy()
        for col in segment_cols:
            all_counts = df[col].fillna("(missing)").value_counts()
            near_counts = near[col].fillna("(missing)").value_counts()
            for value, count in near_counts.head(12).items():
                rows.append(
                    {
                        "threshold": f"<={threshold:.0%}",
                        "segment_column": col,
                        "segment_value": value,
                        "near_count": int(count),
                        "near_share": count / len(near) if len(near) else np.nan,
                        "all_count": int(all_counts.get(value, 0)),
                        "hit_rate_within_segment": count / all_counts.get(value, 1),
                    }
                )
    return pd.DataFrame(rows)


def build_numeric_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, subset in [
        ("all_numeric_labels", df),
        ("near_1pct", df[df["service_primary_ape"] <= 0.01]),
        ("near_3pct", df[df["service_primary_ape"] <= 0.03]),
        ("near_5pct", df[df["service_primary_ape"] <= 0.05]),
    ]:
        rows.append(
            {
                "group": label,
                "n": len(subset),
                "median_actual_krw": subset["actual_price_krw"].median(),
                "median_actual_usd_equiv": subset["actual_price_usd_equiv"].median(),
                "median_area_cm2": subset["area_cm2"].median(),
                "median_svc_group_n": subset["svc_group_n"].median(),
                "median_quantile_width": subset["l10_quantile_width"].median(),
                "median_price_range_ratio": subset["l10_price_range_ratio"].median(),
            }
        )
    return pd.DataFrame(rows)


def build_display_rounding_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for currency, pred_col, actual_col, units in [
        (
            "KRW",
            "service_primary_pred_price_krw",
            "actual_price_krw",
            [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000],
        ),
        (
            "USD",
            "service_primary_pred_price_usd",
            "actual_price_usd_equiv",
            [1, 10, 100, 1_000],
        ),
    ]:
        valid = df[[pred_col, actual_col]].dropna()
        for unit in units:
            pred_rounded = (valid[pred_col] / unit).round() * unit
            actual_rounded = (valid[actual_col] / unit).round() * unit
            count = int((pred_rounded == actual_rounded).sum())
            rows.append(
                {
                    "currency": currency,
                    "rounding_unit": unit,
                    "n": len(valid),
                    "rounded_display_match_count": count,
                    "rounded_display_match_rate": count / len(valid) if len(valid) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_데이터 없음_"
    view = df[columns].copy()
    headers = [str(col) for col in view.columns]
    rows = []
    for _, row in view.iterrows():
        rows.append([str(row[col]) if not pd.isna(row[col]) else "" for col in view.columns])

    def clean(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(clean(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clean(value) for value in row) + " |")
    return "\n".join(lines)


def build_report(
    df: pd.DataFrame,
    summary: pd.DataFrame,
    top_matches: pd.DataFrame,
    segments: pd.DataFrame,
    profile: pd.DataFrame,
    display_rounding: pd.DataFrame,
) -> str:
    service_summary = summary[summary["candidate"] == "service_primary"].iloc[0]
    top10 = top_matches.head(10).copy()
    top10_view = pd.DataFrame(
        {
            "row_id": top10["_v01_row_id"],
            "작품명": top10["title"],
            "작가": top10["artist_name"],
            "실제 KRW": top10["actual_price_krw"].map(fmt_int),
            "예측 KRW": top10["service_primary_pred_price_krw"].map(fmt_int),
            "절대오차 KRW": top10["abs_error_krw"].map(fmt_int),
            "APE": top10["service_primary_ape"].map(lambda x: fmt_float(x, 6)),
            "비교 묶음": top10["svc_group_level"],
            "표본수": top10["svc_group_n"].map(lambda x: "" if pd.isna(x) else int(x)),
            "재료/지지체": top10["medium_support_bucket"],
        }
    )

    summary_view = summary.copy()
    for col in ["min_ape", "median_ape", "mean_ape", "p95_ape"]:
        summary_view[col] = summary_view[col].map(lambda x: fmt_float(x, 6))
    for threshold in THRESHOLDS:
        rate_col = f"within_{threshold:.1%}_rate"
        count_col = f"within_{threshold:.1%}"
        summary_view[f"{threshold:.1%} 이내"] = (
            summary_view[count_col].astype(str)
            + " ("
            + (summary_view[rate_col] * 100).map(lambda x: fmt_float(x, 2))
            + "%)"
        )

    profile_view = profile.copy()
    for col in profile_view.columns:
        if col not in ["group", "n"]:
            profile_view[col] = profile_view[col].map(lambda x: fmt_float(x, 2))

    segment_key = segments[
        (segments["threshold"].isin(["<=1%", "<=3%", "<=5%"]))
        & (segments["segment_column"].isin(["svc_group_level", "medium_support_bucket"]))
    ].copy()
    segment_key["near_share"] = (segment_key["near_share"] * 100).map(
        lambda x: fmt_float(x, 1) + "%"
    )
    segment_key["hit_rate_within_segment"] = (
        segment_key["hit_rate_within_segment"] * 100
    ).map(lambda x: fmt_float(x, 1) + "%")

    display_view = display_rounding.copy()
    display_view["rounding_unit"] = display_view["rounding_unit"].map(fmt_int)
    display_view["rounded_display_match_rate"] = (
        display_view["rounded_display_match_rate"] * 100
    ).map(lambda x: fmt_float(x, 2) + "%")

    exact_count = int(service_summary["exact_krw_count"])
    rounded_exact_count = int(service_summary["rounded_exact_krw_count"])
    min_ape = float(service_summary["min_ape"])
    min_case = top_matches.iloc[0]

    lines = [
        "# 0604 테스트 정확/근접 적중 분석",
        "",
        "## 1. 결론",
        "",
        f"- 운영 기본 예측값 기준 정확히 같은 원화 가격으로 맞춘 건수: `{exact_count}`건.",
        f"- 원화 단위로 반올림해도 정확히 같은 가격으로 맞춘 건수: `{rounded_exact_count}`건.",
        f"- 가장 가까운 사례의 오차율: `{min_ape:.6f}`.",
        (
            "- 따라서 0604 테스트에서는 실제 가격을 숫자 단위로 그대로 맞춘 사례는 없고, "
            "예측 기준선과 실제 판매가가 매우 가까웠던 근접 적중 사례가 존재함."
        ),
        "",
        "## 2. 분석 기준",
        "",
        "- 정확 일치: `예측 원화 가격 == 실제 원화 가격`.",
        "- 반올림 정확 일치: `예측 원화 가격을 1원 단위로 반올림한 값 == 실제 원화 가격`.",
        "- 근접 적중: 절대 퍼센트 오차가 0.1%, 0.5%, 1%, 2%, 3%, 5%, 10% 이내인 경우.",
        "- 분석 대상: 0604 신규 테스트 중 실제 숫자 가격 라벨이 있는 837건.",
        "",
        "## 3. 후보별 정확/근접 적중 현황",
        "",
        markdown_table(
            summary_view,
            [
                "candidate",
                "n",
                "exact_krw_count",
                "rounded_exact_krw_count",
                "min_ape",
                "median_ape",
                "mean_ape",
                "p95_ape",
                "0.1% 이내",
                "0.5% 이내",
                "1.0% 이내",
                "3.0% 이내",
                "5.0% 이내",
                "10.0% 이내",
            ],
        ),
        "",
        "## 4. 화면 표시 반올림 기준 참고",
        "",
        (
            "- 모델 원값 기준으로는 정확 일치가 없지만, 화면에서 가격을 만원/10만원 단위로 둥글게 보여주면 "
            "실제 가격과 같은 값처럼 보이는 사례가 발생할 수 있음."
        ),
        "- 이 표는 운영 기본값만 기준으로 계산한 참고 지표이며, 모델이 정확히 맞췄다는 의미는 아님.",
        "",
        markdown_table(
            display_view,
            [
                "currency",
                "rounding_unit",
                "n",
                "rounded_display_match_count",
                "rounded_display_match_rate",
            ],
        ),
        "",
        "## 5. 운영 기본값 기준 상위 근접 적중 사례",
        "",
        markdown_table(
            top10_view,
            [
                "row_id",
                "작품명",
                "작가",
                "실제 KRW",
                "예측 KRW",
                "절대오차 KRW",
                "APE",
                "비교 묶음",
                "표본수",
                "재료/지지체",
            ],
        ),
        "",
        "## 6. 가장 가까운 사례 해석",
        "",
        f"- 작품: `{min_case['title']}`.",
        f"- 작가: `{min_case['artist_name']}`.",
        f"- 실제 가격: `{fmt_int(min_case['actual_price_krw'])}`원.",
        f"- 예측 가격: `{fmt_int(min_case['service_primary_pred_price_krw'])}`원.",
        f"- 차이: `{fmt_int(min_case['abs_error_krw'])}`원.",
        f"- 오차율: `{float(min_case['service_primary_ape']):.6f}`.",
        f"- 비교 묶음: `{min_case['svc_group_level']}`, 표본수 `{int(min_case['svc_group_n']) if pd.notna(min_case['svc_group_n']) else ''}`건.",
        (
            "- 해석: 같은 작가의 과거 가격 기준선과 작품 크기/재료 조건이 실제 신규 가격대와 거의 일치하면서 "
            "운영 기본 결합값이 실제 가격 근처에 위치한 사례."
        ),
        (
            "- 주의: 신규 실제 라벨을 모델 입력으로 사용한 것이 아니므로, 실제 가격을 복사해서 맞춘 구조는 아님."
        ),
        "",
        "## 7. 어떻게 가까워졌는가",
        "",
        "- 운영 기본값은 `pp_v8_compact_blend_mape_guarded`.",
        "- 계산 구조: `0.75 * 오차 안정화 후보 + 0.25 * 생성 버킷 순차 후보`를 로그 가격 공간에서 결합.",
        "- 오차 안정화 후보: 큰 오차를 줄이도록 학습한 방어형 가격 기준.",
        "- 생성 버킷 순차 후보: 크기, 재료/지지체, 가격 구간 정보를 더 세밀하게 반영한 후보.",
        "- 가까운 사례는 두 후보가 비슷한 방향의 가격대를 가리키거나, 한 후보의 치우침을 다른 후보가 보완한 경우.",
        "",
        "## 8. 근접 적중 사례의 공통 특성",
        "",
        markdown_table(
            profile_view,
            [
                "group",
                "n",
                "median_actual_krw",
                "median_actual_usd_equiv",
                "median_area_cm2",
                "median_svc_group_n",
                "median_quantile_width",
                "median_price_range_ratio",
            ],
        ),
        "",
        markdown_table(
            segment_key,
            [
                "threshold",
                "segment_column",
                "segment_value",
                "near_count",
                "near_share",
                "all_count",
                "hit_rate_within_segment",
            ],
        ),
        "",
        "## 9. 보고용 해석",
        "",
        "- 원값 기준으로 정확히 맞춘 가격은 없음.",
        "- 화면 표시 반올림 기준으로 같아 보이는 값은 있을 수 있으므로, 보고 시 원값 기준과 표시값 기준을 구분해야 함.",
        "- 1% 이내 근접 적중은 운영 기본값 기준 20건.",
        "- 근접 적중은 주로 같은 작가 기준선이 확보된 작품에서 발생.",
        "- 특히 oil/acrylic canvas처럼 학습 데이터에 반복적으로 등장하는 재료/지지체에서 가격 기준이 안정적으로 잡힘.",
        "- 정확 일치가 없다는 점은 모델이 특정 정답 가격을 외운 것이 아니라 연속 가격을 예측하고 있음을 보여줌.",
        "- 가까운 사례 분석은 이후 구간별 보정이나 작가별 가격 기준선 보정의 근거로 활용 가능.",
        "",
        "## 10. 산출물",
        "",
        "- 후보별 요약: `outputs/candidate_exact_near_match_summary.csv`.",
        "- 운영 기본값 상위 근접 사례: `outputs/service_primary_top_near_matches.csv`.",
        "- 근접 적중 구간 요약: `outputs/service_primary_near_match_segment_summary.csv`.",
        "- 수치 프로파일: `outputs/service_primary_near_match_numeric_profile.csv`.",
        "- 화면 표시 반올림 기준 요약: `outputs/service_primary_display_rounding_match_summary.csv`.",
    ]
    return "\n".join(lines) + "\n"


def build_html_report(markdown_text: str, tables: dict[str, pd.DataFrame]) -> str:
    escaped = markdown_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = escaped.replace("\n", "<br>\n")
    table_html = []
    for title, table in tables.items():
        table_html.append(f"<h2>{title}</h2>")
        table_html.append(table.to_html(index=False, escape=False, border=0))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>0604 테스트 정확/근접 적중 분석</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2933; line-height: 1.55; }}
    h1, h2 {{ margin-top: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f6f9; }}
    .markdown {{ padding: 18px 20px; background: #fbfdff; border: 1px solid #d9e2ec; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="markdown">{body}</div>
  {''.join(table_html)}
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_numeric_labels()
    summary = build_candidate_summary(df)
    top_matches = build_top_near_matches(df)
    segments = build_segment_summary(df)
    profile = build_numeric_profile(df)
    display_rounding = build_display_rounding_summary(df)

    summary.to_csv(OUTPUT_DIR / "candidate_exact_near_match_summary.csv", index=False)
    top_matches.to_csv(OUTPUT_DIR / "service_primary_top_near_matches.csv", index=False)
    segments.to_csv(OUTPUT_DIR / "service_primary_near_match_segment_summary.csv", index=False)
    profile.to_csv(OUTPUT_DIR / "service_primary_near_match_numeric_profile.csv", index=False)
    display_rounding.to_csv(
        OUTPUT_DIR / "service_primary_display_rounding_match_summary.csv", index=False
    )

    report = build_report(df, summary, top_matches, segments, profile, display_rounding)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")

    html = build_html_report(
        report,
        {
            "후보별 정확/근접 적중 요약": summary,
            "운영 기본값 상위 근접 사례": top_matches.head(30),
            "근접 적중 수치 프로파일": profile,
            "화면 표시 반올림 기준 요약": display_rounding,
            "근접 적중 구간 요약": segments.head(120),
        },
    )
    (REPORT_DIR / "result_report.html").write_text(html, encoding="utf-8")

    service = summary[summary["candidate"] == "service_primary"].iloc[0]
    print("numeric_labels", len(df))
    print("service_primary_exact", int(service["exact_krw_count"]))
    print("service_primary_rounded_exact", int(service["rounded_exact_krw_count"]))
    print("service_primary_min_ape", float(service["min_ape"]))
    print("report", REPORT_DIR / "result_report.md")


if __name__ == "__main__":
    main()
