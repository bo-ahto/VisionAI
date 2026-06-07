#!/usr/bin/env python3
"""Build a comprehensive 0604 operational v0.1 error report.

The report combines:
- exact and near-hit analysis,
- severe over/under prediction analysis,
- the impact of very low actual price labels,
- display-rounding caveats,
- follow-up correction ideas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[4]
INPUT = (
    REPO
    / "models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/"
    / "operational_predictions_with_actual.csv"
)
OUT = REPO / "experiments/track6/OP-0604_comprehensive_error_analysis"
OUTPUT_DIR = OUT / "outputs"
REPORT_DIR = OUT / "reports"

PRICE_COL = "service_primary_pred_price_krw"
APE_COL = "service_primary_ape"
RATIO_COL = "service_primary_ratio"


def fmt_int(value: float | int) -> str:
    if pd.isna(value):
        return ""
    return f"{int(round(float(value))):,}"


def fmt_float(value: float | int, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def md_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_데이터 없음_"
    view = df[columns].copy()
    headers = [str(col) for col in view.columns]

    def clean(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(clean(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(clean(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT, low_memory=False)
    df = df[pd.to_numeric(df["actual_price_krw"], errors="coerce").notna()].copy()
    numeric_cols = [
        "actual_price_krw",
        "actual_price_usd_equiv",
        PRICE_COL,
        APE_COL,
        RATIO_COL,
        "svc_group_n",
        "l10_price_range_ratio",
        "l10_quantile_width",
        "area_cm2",
        "width_cm",
        "height_cm",
        "depth_cm",
        "service_range_low_price_krw",
        "service_range_high_price_krw",
        "v01_operational_ape",
        "pp_v8_compact_blend_mape_guarded_ape",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["actual_under_50_usd"] = df["actual_price_usd_equiv"] < 50
    df["abs_error_krw"] = (df[PRICE_COL] - df["actual_price_krw"]).abs()
    df["error_direction"] = np.where(df[PRICE_COL] >= df["actual_price_krw"], "과대", "과소")
    return df


def metric_row(label: str, df: pd.DataFrame) -> dict[str, float | int | str]:
    pred_log = np.log(np.clip(df[PRICE_COL].to_numpy(dtype=float), 1_000.0, None))
    actual_log = np.log(np.clip(df["actual_price_krw"].to_numpy(dtype=float), 1_000.0, None))
    return {
        "구분": label,
        "n": len(df),
        "MdAPE": df[APE_COL].median(),
        "MAPE": df[APE_COL].mean(),
        "p95_APE": df[APE_COL].quantile(0.95),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))) if len(df) else np.nan,
        "median_ratio": df[RATIO_COL].median(),
        "over_3x_n": int((df[RATIO_COL] > 3).sum()),
        "under_1_3x_n": int((df[RATIO_COL] < 1 / 3).sum()),
        "APE_1plus_n": int((df[APE_COL] >= 1).sum()),
    }


def build_metric_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = df[~df["actual_under_50_usd"]].copy()
    low = df[df["actual_under_50_usd"]].copy()
    rows = [
        metric_row("전체 숫자 라벨", df),
        metric_row("50달러 미만 제외", base),
        metric_row("50달러 미만 검수 대상", low),
    ]
    out = pd.DataFrame(rows)
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "median_ratio"]:
        out[col] = out[col].map(lambda x: fmt_float(x, 4))
    return out


def build_exact_near_summary(df: pd.DataFrame) -> pd.DataFrame:
    thresholds = [0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.10]
    rows = []
    exact = df[PRICE_COL] == df["actual_price_krw"]
    rounded_exact = df[PRICE_COL].round(0) == df["actual_price_krw"].round(0)
    row = {
        "기준": "운영 기본값 원값",
        "n": len(df),
        "정확일치": int(exact.sum()),
        "1원반올림일치": int(rounded_exact.sum()),
        "최소_APE": df[APE_COL].min(),
    }
    for threshold in thresholds:
        count = int((df[APE_COL] <= threshold).sum())
        row[f"{threshold:.1%}_이내"] = f"{count} ({count / len(df) * 100:.2f}%)"
    rows.append(row)

    out = pd.DataFrame(rows)
    out["최소_APE"] = out["최소_APE"].map(lambda x: fmt_float(x, 6))
    return out


def build_display_rounding(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for currency, pred_col, actual_col, units in [
        ("KRW", PRICE_COL, "actual_price_krw", [1, 1_000, 10_000, 100_000, 1_000_000]),
        (
            "USD",
            "service_primary_pred_price_usd",
            "actual_price_usd_equiv",
            [1, 10, 100, 1_000],
        ),
    ]:
        valid = df[[pred_col, actual_col]].dropna()
        for unit in units:
            pred_round = (valid[pred_col] / unit).round() * unit
            actual_round = (valid[actual_col] / unit).round() * unit
            count = int((pred_round == actual_round).sum())
            rows.append(
                {
                    "통화": currency,
                    "반올림단위": fmt_int(unit),
                    "n": len(valid),
                    "표시값일치": count,
                    "표시값일치율": f"{count / len(valid) * 100:.2f}%",
                }
            )
    return pd.DataFrame(rows)


def selected_case_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "_v01_row_id",
        "artist_name",
        "title",
        "actual_currency",
        "actual_price_krw",
        "actual_price_usd_equiv",
        PRICE_COL,
        "abs_error_krw",
        APE_COL,
        RATIO_COL,
        "error_direction",
        "svc_group_level",
        "svc_coverage_tier",
        "service_confidence_tier",
        "svc_group_n",
        "medium_support_bucket",
        "width_cm",
        "height_cm",
        "area_cm2",
        "l10_price_range_ratio",
    ]
    out = df[[col for col in cols if col in df.columns]].copy()
    return out


def build_top_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = df[~df["actual_under_50_usd"]].copy()
    tables = {
        "near_top50": selected_case_columns(df.sort_values(APE_COL).head(50)),
        "low_actual_under_50": selected_case_columns(
            df[df["actual_under_50_usd"]].sort_values(APE_COL, ascending=False)
        ),
        "largest_errors_all_top100": selected_case_columns(
            df.sort_values(APE_COL, ascending=False).head(100)
        ),
        "largest_errors_excluding_under50_top100": selected_case_columns(
            base.sort_values(APE_COL, ascending=False).head(100)
        ),
        "over_3x_excluding_under50": selected_case_columns(
            base[base[RATIO_COL] > 3].sort_values(RATIO_COL, ascending=False)
        ),
        "under_1_3x_excluding_under50": selected_case_columns(
            base[base[RATIO_COL] < 1 / 3].sort_values(RATIO_COL).head(100)
        ),
        "high_actual_over_100k_usd": selected_case_columns(
            base[base["actual_price_usd_equiv"] >= 100_000].sort_values(
                "actual_price_usd_equiv", ascending=False
            )
        ),
    }
    return tables


def build_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = df[~df["actual_under_50_usd"]].copy()
    groups = {
        "전체_50달러이상": base,
        "근접_5pct": base[base[APE_COL] <= 0.05],
        "과대_3배초과": base[base[RATIO_COL] > 3],
        "과소_1_3미만": base[base[RATIO_COL] < 1 / 3],
        "APE_100pct이상": base[base[APE_COL] >= 1],
    }
    rows = []
    for label, frame in groups.items():
        row = {
            "구분": label,
            "n": len(frame),
            "median_actual_usd": frame["actual_price_usd_equiv"].median(),
            "median_pred_usd": (frame[PRICE_COL] / 1380.0).median(),
            "median_area_cm2": frame["area_cm2"].median(),
            "median_svc_group_n": frame["svc_group_n"].median(),
            "median_price_range_ratio": frame["l10_price_range_ratio"].median(),
            "top_group_level": frame["svc_group_level"].mode().iloc[0] if len(frame) else "",
            "top_medium_support": frame["medium_support_bucket"].mode().iloc[0] if len(frame) else "",
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    for col in [
        "median_actual_usd",
        "median_pred_usd",
        "median_area_cm2",
        "median_svc_group_n",
        "median_price_range_ratio",
    ]:
        out[col] = out[col].map(lambda x: fmt_float(x, 2))
    return out


def build_segment_counts(df: pd.DataFrame) -> pd.DataFrame:
    base = df[~df["actual_under_50_usd"]].copy()
    groups = {
        "근접_5pct": base[base[APE_COL] <= 0.05],
        "과대_3배초과": base[base[RATIO_COL] > 3],
        "과소_1_3미만": base[base[RATIO_COL] < 1 / 3],
        "APE_100pct이상": base[base[APE_COL] >= 1],
    }
    segment_cols = [
        "svc_group_level",
        "svc_coverage_tier",
        "service_confidence_tier",
        "medium_support_bucket",
        "actual_currency",
    ]
    rows = []
    for label, frame in groups.items():
        for col in segment_cols:
            counts = frame[col].fillna("(missing)").value_counts()
            for value, count in counts.head(8).items():
                rows.append(
                    {
                        "구분": label,
                        "세그먼트": col,
                        "값": value,
                        "건수": int(count),
                        "비중": f"{count / len(frame) * 100:.1f}%" if len(frame) else "",
                    }
                )
    return pd.DataFrame(rows)


def format_case_table(df: pd.DataFrame, n: int = 12) -> pd.DataFrame:
    view = df.head(n).copy()
    rename = {
        "_v01_row_id": "row_id",
        "artist_name": "작가",
        "title": "작품명",
        "actual_currency": "통화",
        "actual_price_krw": "실제_KRW",
        "actual_price_usd_equiv": "실제_USD환산",
        PRICE_COL: "예측_KRW",
        "abs_error_krw": "절대오차_KRW",
        APE_COL: "APE",
        RATIO_COL: "예측/실제",
        "error_direction": "방향",
        "svc_group_level": "비교묶음",
        "svc_group_n": "표본수",
        "medium_support_bucket": "재료/지지체",
        "l10_price_range_ratio": "가격범위비",
    }
    view = view.rename(columns=rename)
    for col in ["실제_KRW", "예측_KRW", "절대오차_KRW"]:
        if col in view:
            view[col] = view[col].map(fmt_int)
    for col in ["실제_USD환산", "APE", "예측/실제", "가격범위비"]:
        if col in view:
            view[col] = view[col].map(lambda x: fmt_float(x, 4))
    if "표본수" in view:
        view["표본수"] = view["표본수"].map(lambda x: "" if pd.isna(x) else fmt_int(x))
    keep = [
        "row_id",
        "작가",
        "작품명",
        "통화",
        "실제_KRW",
        "예측_KRW",
        "APE",
        "예측/실제",
        "방향",
        "비교묶음",
        "표본수",
        "재료/지지체",
    ]
    return view[[col for col in keep if col in view.columns]]


def build_report(
    metrics_df: pd.DataFrame,
    exact_df: pd.DataFrame,
    display_df: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    segment_profile: pd.DataFrame,
    segment_counts: pd.DataFrame,
) -> str:
    near = format_case_table(tables["near_top50"], 10)
    low_actual = format_case_table(tables["low_actual_under_50"], 8)
    over = format_case_table(tables["over_3x_excluding_under50"], 10)
    under = format_case_table(tables["under_1_3x_excluding_under50"], 15)
    high_actual = format_case_table(tables["high_actual_over_100k_usd"], 12)
    largest = format_case_table(tables["largest_errors_excluding_under50_top100"], 15)

    lines = [
        "# 0604 테스트 종합 오차 분석",
        "",
        "## 1. 핵심 결론",
        "",
        "- 0604 숫자 가격 라벨 837건 기준, 운영 기본값이 원화 가격을 정확히 맞춘 사례는 0건.",
        "- 1% 이내 근접 적중은 20건, 5% 이내 근접 적중은 98건.",
        "- 근접 적중은 주로 같은 작가 기준선이 잡힌 작품, 반복 재료/지지체, 가격 범위가 비교적 좁은 작품에서 발생.",
        "- 전체 MAPE 14.2852는 50달러 미만 검수 대상 8건의 영향이 매우 큼.",
        "- 50달러 미만을 제외하면 MAPE는 0.3359, p95_APE는 0.9273으로 내려감.",
        "- 50달러 이상에서도 큰 오차는 남아 있으며, 과대 예측은 저가 소품/소형작, 과소 예측은 고가 작품/특수 작가/큰 가격 범위에서 주로 발생.",
        "",
        "## 2. 전체 성능과 큰 오차 영향",
        "",
        md_table(metrics_df, list(metrics_df.columns)),
        "",
        "해석:",
        "",
        "- `전체 숫자 라벨`의 MAPE가 비정상적으로 큰 이유는 실제 가격이 1~30달러인 라벨이 포함되어 있기 때문.",
        "- MAPE는 실제 가격을 분모로 쓰므로 실제값이 매우 작으면 작은 금액 차이도 수백~수천 배 오차로 계산됨.",
        "- 따라서 운영 판단은 전체 수치와 함께 50달러 미만 검수 대상 제외 기준을 같이 봐야 함.",
        "",
        "## 3. 정확/근접 적중",
        "",
        md_table(exact_df, list(exact_df.columns)),
        "",
        "해석:",
        "",
        "- 정확 일치 0건은 모델이 정답 가격을 외우거나 복사한 구조가 아니라는 의미.",
        "- 근접 적중은 유사 작가/유사 조건의 가격 기준선과 실제 신규 판매가가 우연히 매우 가깝게 맞은 사례.",
        "- 서비스 화면에서 반올림 표시를 하면 같은 값처럼 보일 수 있으므로 원값 기준과 표시값 기준을 분리해 설명해야 함.",
        "",
        "### 3.1 화면 표시 반올림 기준",
        "",
        md_table(display_df, list(display_df.columns)),
        "",
        "### 3.2 근접 적중 상위 사례",
        "",
        md_table(near, list(near.columns)),
        "",
        "## 4. 50달러 미만 검수 대상",
        "",
        md_table(low_actual, list(low_actual.columns)),
        "",
        "해석:",
        "",
        "- 실제 가격이 1달러, 10달러, 20달러, 30달러로 들어온 라벨이 있음.",
        "- 해당 가격이 실제 판매가인지, placeholder/입력 오류/특수 상품 가격인지 검수 필요.",
        "- 모델은 일반 작품 가격 기준으로 예측하므로, 이런 초저가 라벨은 MAPE를 크게 왜곡함.",
        "- 운영 평가에서는 초저가 라벨을 별도 검수 태그로 분리하는 것이 필요.",
        "",
        "## 5. 50달러 이상 큰 오차 사례",
        "",
        "### 5.1 APE 기준 큰 오차 상위",
        "",
        md_table(largest, list(largest.columns)),
        "",
        "### 5.2 3배 초과 과대 예측",
        "",
        md_table(over, list(over.columns)),
        "",
        "해석:",
        "",
        "- 3배 초과 과대 예측은 50달러 이상 기준 4건.",
        "- 실제 가격 중앙값이 약 305달러로 낮은 편이며, 모델 예측은 작가/유사 조건 기준선을 따라 더 높은 가격대로 올라감.",
        "- 저가 소품, edition/오브젝트성 작품, 작은 크기 작품은 일반 회화 가격 기준선과 분리할 필요가 있음.",
        "",
        "### 5.3 3분의 1 미만 과소 예측",
        "",
        md_table(under, list(under.columns)),
        "",
        "해석:",
        "",
        "- 3분의 1 미만 과소 예측은 50달러 이상 기준 58건.",
        "- 실제 가격 중앙값이 16,500달러로 전체 중앙값보다 훨씬 높음.",
        "- 유명 작가, 고가 작품, 특수 작품군, 초대형 작품, 검색/작가 메타로 설명되지 않는 프리미엄에서 주로 발생.",
        "- 이 구간은 단순 중앙 예측보다 고가 위험 태그, 가격 범위 상단, 신뢰도 표시가 중요.",
        "",
        "### 5.4 초고가 라벨 검수 대상",
        "",
        md_table(high_actual, list(high_actual.columns)),
        "",
        "해석:",
        "",
        "- 10만 달러 이상 라벨은 8건, 100만 달러 이상 라벨은 2건.",
        "- 일부 라벨은 신규 운영 테스트 데이터의 가격 단위, 통화, 입력값 해석을 다시 확인해야 함.",
        "- 실제 초고가 작품이 맞다면 현재 v0.1 Warm 모델은 초고가 프리미엄을 충분히 반영하지 못함.",
        "- 따라서 초고가 라벨은 데이터 검수와 모델 보정을 동시에 봐야 하는 구간.",
        "",
        "## 6. 근접/큰 오차 세그먼트 비교",
        "",
        md_table(segment_profile, list(segment_profile.columns)),
        "",
        "세그먼트별 상위 분포:",
        "",
        md_table(segment_counts.head(80), list(segment_counts.columns)),
        "",
        "## 7. 원인 정리",
        "",
        "| 구분 | 주요 원인 | 해석 | 후속 보정 방향 |",
        "|---|---|---|---|",
        "| 근접 적중 | 작가 기준선과 작품 조건이 실제 가격대와 일치 | 같은 작가 과거 거래가 있는 Warm 구조가 잘 작동 | 해당 구조 유지, 안정 구간 신뢰도 상향 |",
        "| 초저가 라벨 | 실제 가격이 1~30달러 | MAPE를 과도하게 키움 | 라벨 검수, 초저가/비작품 상품 분리 |",
        "| 과대 예측 | 저가 소품/소형작을 일반 작품 기준선으로 예측 | 작가 기준선이 낮은 실제 판매가를 충분히 낮추지 못함 | 소품/edition/object 태그, 저가 구간 cap 보정 |",
        "| 과소 예측 | 고가 작품/유명 작가/특수 프리미엄 | 유사 조건 통계가 고가 프리미엄을 충분히 반영하지 못함 | 고가 위험 태그, q90/상단 범위 활용, 작가 프리미엄 보정 |",
        "| 초고가 라벨 | 10만 달러 이상 라벨 | 실제 초고가 작품인지, 통화/단위 입력 문제인지 확인 필요 | 초고가 검수 태그, 고가 작가 별도 보정 |",
        "| 불확실 구간 | 가격 범위비가 큼 | 모델 내부에서도 가격대 판단이 넓게 흔들림 | 신뢰도 하향, 범위 중심 표시, 수동 검수 후보 |",
        "",
        "## 8. 보고용 문장",
        "",
        "- 0604 신규 테스트에서는 가격을 정확히 맞춘 사례는 없으나, 1% 이내로 매우 근접한 사례는 20건 확인됨.",
        "- 잘 맞은 사례는 같은 작가의 과거 가격 기준선과 작품 조건이 실제 신규 가격과 일치한 경우가 많음.",
        "- 오차가 큰 사례는 초저가 라벨, 저가 소품 과대 예측, 고가 작품 과소 예측으로 나뉨.",
        "- 특히 50달러 미만 라벨 8건은 전체 MAPE를 크게 왜곡하므로 별도 검수 기준이 필요함.",
        "- 10만 달러 이상 초고가 라벨 8건은 데이터 검수와 고가 프리미엄 보정이 모두 필요한 구간임.",
        "- 서비스 적용 시 단일 가격만 표시하기보다 가격 범위, 신뢰도, 비교 표본 수, 검수 필요 여부를 함께 제공하는 것이 안전함.",
        "",
        "## 9. 산출물",
        "",
        "- `outputs/metric_summary.csv`",
        "- `outputs/exact_near_summary.csv`",
        "- `outputs/display_rounding_summary.csv`",
        "- `outputs/near_top50.csv`",
        "- `outputs/largest_errors_excluding_under50_top100.csv`",
        "- `outputs/over_3x_excluding_under50.csv`",
        "- `outputs/under_1_3x_excluding_under50.csv`",
        "- `outputs/high_actual_over_100k_usd.csv`",
        "- `reports/comprehensive_error_report.md`",
        "- `reports/comprehensive_error_report.html`",
    ]
    return "\n".join(lines) + "\n"


def html_report(md: str, tables: dict[str, pd.DataFrame]) -> str:
    body = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = body.replace("\n", "<br>\n")
    table_sections = []
    for title, table in tables.items():
        table_sections.append(f"<h2>{title}</h2>")
        table_sections.append(table.to_html(index=False, border=0, escape=True))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>0604 테스트 종합 오차 분석</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2933; line-height: 1.55; }}
    h1, h2, h3 {{ margin-top: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f6f9; }}
    .markdown {{ padding: 18px 20px; background: #fbfdff; border: 1px solid #d9e2ec; border-radius: 8px; }}
  </style>
</head>
<body>
  <div class="markdown">{body}</div>
  {''.join(table_sections)}
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    metrics_df = build_metric_summary(df)
    exact_df = build_exact_near_summary(df)
    display_df = build_display_rounding(df)
    tables = build_top_tables(df)
    segment_profile = build_segment_summary(df)
    segment_counts = build_segment_counts(df)

    metrics_df.to_csv(OUTPUT_DIR / "metric_summary.csv", index=False)
    exact_df.to_csv(OUTPUT_DIR / "exact_near_summary.csv", index=False)
    display_df.to_csv(OUTPUT_DIR / "display_rounding_summary.csv", index=False)
    segment_profile.to_csv(OUTPUT_DIR / "segment_profile_summary.csv", index=False)
    segment_counts.to_csv(OUTPUT_DIR / "segment_count_summary.csv", index=False)
    for name, table in tables.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)

    md = build_report(metrics_df, exact_df, display_df, tables, segment_profile, segment_counts)
    (REPORT_DIR / "comprehensive_error_report.md").write_text(md, encoding="utf-8")
    html = html_report(
        md,
        {
            "metric_summary": metrics_df,
            "exact_near_summary": exact_df,
            "near_top50": tables["near_top50"].head(30),
            "low_actual_under_50": tables["low_actual_under_50"],
            "largest_errors_excluding_under50_top100": tables[
                "largest_errors_excluding_under50_top100"
            ].head(30),
            "over_3x_excluding_under50": tables["over_3x_excluding_under50"],
            "under_1_3x_excluding_under50": tables["under_1_3x_excluding_under50"].head(30),
            "high_actual_over_100k_usd": tables["high_actual_over_100k_usd"],
            "segment_profile": segment_profile,
            "segment_counts": segment_counts.head(120),
        },
    )
    (REPORT_DIR / "comprehensive_error_report.html").write_text(html, encoding="utf-8")
    print("numeric_labels", len(df))
    print("report", REPORT_DIR / "comprehensive_error_report.md")
    print("html", REPORT_DIR / "comprehensive_error_report.html")


if __name__ == "__main__":
    main()
