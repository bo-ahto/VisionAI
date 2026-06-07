from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0605_existing_split_error_cause_customization"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

WARM_CANDIDATE = "compact_blend_mape_guarded"
COLD_CANDIDATE = "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25"

WARM_PRED_PATH = (
    PROJECT_ROOT
    / "models/track6/price_prediction_v0.1/evidence/experiments/PP-V8_warm_deployment_simplification/outputs/predictions.csv"
)
WARM_SVC_PATH = (
    PROJECT_ROOT
    / "models/track6/price_prediction_v0.1/evidence/experiments/PP-SVC3_warm_svc_blend_routing/outputs/predictions.csv"
)
COLD_PRED_PATH = (
    PROJECT_ROOT
    / "models/track6/price_prediction_v0.1/evidence/experiments/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv"
)
SPLIT_ROOT = PROJECT_ROOT / "data/track6_split_with_year_type_edition_size_artist_name"


def read_split(route: str, split: str) -> pd.DataFrame:
    if split == "validation":
        split_name = "val"
    else:
        split_name = split
    path = SPLIT_ROOT / f"track6_{split_name}_{route}.csv"
    return pd.read_csv(path)


def safe_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def metrics(frame: pd.DataFrame, pred_col: str = "pred_price") -> dict[str, float | int]:
    actual = safe_num(frame["actual_price"])
    pred = safe_num(frame[pred_col])
    valid = frame[(actual > 0) & (pred > 0)].copy()
    if valid.empty:
        return {
            "n": 0,
            "MdAPE": math.nan,
            "MAPE": math.nan,
            "p95_APE": math.nan,
            "RMSE_log": math.nan,
            "over_3x_n": 0,
            "under_1_3x_n": 0,
        }
    actual = safe_num(valid["actual_price"])
    pred = safe_num(valid[pred_col])
    ape = (pred - actual).abs() / actual
    ratio = pred / actual
    return {
        "n": int(len(valid)),
        "MdAPE": float(ape.median()),
        "MAPE": float(ape.mean()),
        "p95_APE": float(ape.quantile(0.95)),
        "RMSE_log": float(np.sqrt(np.mean((np.log(pred) - np.log(actual)) ** 2))),
        "median_ratio": float(ratio.median()),
        "over_3x_n": int((ratio >= 3.0).sum()),
        "under_1_3x_n": int((ratio <= (1.0 / 3.0)).sum()),
    }


def band_price(price: float | int | None) -> str:
    if pd.isna(price):
        return "price_missing"
    price = float(price)
    if price < 500_000:
        return "under_0_5m"
    if price < 1_000_000:
        return "0_5m_1m"
    if price < 3_000_000:
        return "1m_3m"
    if price < 10_000_000:
        return "3m_10m"
    if price < 30_000_000:
        return "10m_30m"
    if price < 100_000_000:
        return "30m_100m"
    return "100m_plus"


def band_area(area: float | int | None) -> str:
    if pd.isna(area):
        return "area_missing"
    area = float(area)
    if area <= 0:
        return "area_missing"
    if area < 100:
        return "tiny"
    if area < 1_000:
        return "small"
    if area < 5_000:
        return "medium"
    if area < 20_000:
        return "large"
    if area < 80_000:
        return "very_large"
    return "extreme_large"


def band_count(value: float | int | None, prefix: str) -> str:
    if pd.isna(value):
        return f"{prefix}_missing"
    value = float(value)
    if value <= 5:
        return f"{prefix}_le_5"
    if value <= 10:
        return f"{prefix}_6_10"
    if value <= 30:
        return f"{prefix}_11_30"
    if value <= 100:
        return f"{prefix}_31_100"
    if value <= 1_000:
        return f"{prefix}_101_1000"
    return f"{prefix}_1000_plus"


def band_qwidth(value: float | int | None) -> str:
    if pd.isna(value):
        return "qwidth_missing"
    value = float(value)
    if value <= 1.5:
        return "qwidth_low"
    if value <= 2.5:
        return "qwidth_mid"
    if value <= 4:
        return "qwidth_high"
    return "qwidth_extreme"


def band_meta_score(value: float | int | None) -> str:
    if pd.isna(value):
        return "meta_missing"
    value = float(value)
    if value < 0.25:
        return "meta_low"
    if value < 0.5:
        return "meta_mid"
    if value < 0.75:
        return "meta_good"
    return "meta_high"


def classify_error(row: pd.Series) -> str:
    route = row.get("route")
    ratio = row.get("pred_actual_ratio")
    if pd.isna(ratio):
        return "오차 계산 불가"
    ratio = float(ratio)
    actual = row.get("actual_price")
    area = row.get("area_cm2")
    qwidth = row.get("price_range_ratio")
    group_n = row.get("svc_group_n")
    artist_n = row.get("artist_works_count_train")
    medium_bucket = str(row.get("medium_support_bucket") or "")

    if ratio >= 3.0:
        if pd.notna(actual) and float(actual) < 1_000_000:
            return "저가 작품 과대 예측"
        if pd.notna(area) and float(area) < 500:
            return "소형 작품 과대 예측"
        if pd.notna(group_n) and float(group_n) <= 10:
            return "유사 표본 부족 과대 예측"
        if pd.notna(artist_n) and float(artist_n) <= 10:
            return "작가 이력 부족 과대 예측"
        return "과대 예측 잔차"

    if ratio <= (1.0 / 3.0):
        if pd.notna(actual) and float(actual) >= 30_000_000:
            return "고가 작품 상방 꼬리 과소 예측"
        if pd.notna(area) and float(area) >= 20_000:
            return "대형 작품 과소 예측"
        if pd.notna(qwidth) and float(qwidth) >= 4:
            return "불확실성 큰 구간 과소 예측"
        return "과소 예측 잔차"

    if pd.notna(qwidth) and float(qwidth) >= 4:
        return "예측 범위가 넓은 불확실 구간"
    if pd.notna(group_n) and float(group_n) <= 5:
        return "유사 표본 수 부족"
    if route == "warm" and pd.notna(artist_n) and float(artist_n) <= 5:
        return "작가 이력 수 부족"
    if route == "cold" and row.get("meta_completeness_band") in {"meta_missing", "meta_low"} and row.get("ape", 0) >= 0.5:
        return "작가 메타 부족 구간"
    if medium_bucket in {"other__other", "unknown__unknown", "other"}:
        return "재료/지지체 정보 약함"
    return "정상 범위 또는 세부 잔차"


def prepare_warm() -> pd.DataFrame:
    pred = pd.read_csv(WARM_PRED_PATH)
    pred = pred[pred["candidate"].eq(WARM_CANDIDATE)].copy()
    pred["route"] = "warm"
    pred["analysis_candidate"] = "Warm PP-V8 compact blend mape guarded"

    svc = pd.read_csv(WARM_SVC_PATH)
    svc = svc[svc["candidate"].eq("svc_numeric_seed_mean")].copy()
    svc_cols = [
        "_track6_row_id",
        "split",
        "artist_key",
        "artist_name_ko",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]
    svc = svc[[col for col in svc_cols if col in svc.columns]].drop_duplicates(["_track6_row_id", "split"])
    pred = pred.merge(svc, on=["_track6_row_id", "split"], how="left", suffixes=("", "_svc"))

    parts = []
    for split in ["validation", "test"]:
        base = read_split("warm", split)
        part = pred[pred["split"].eq(split)].merge(base, on="_track6_row_id", how="left", suffixes=("", "_base"))
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def prepare_cold() -> pd.DataFrame:
    all_pred = pd.read_csv(COLD_PRED_PATH)
    qwidth = all_pred[all_pred["candidate"].eq("component_pp_y2_baseline")][
        ["_track6_row_id", "split", "quantile_width_log", "price_range_ratio"]
    ].drop_duplicates(["_track6_row_id", "split"])
    pred = all_pred[all_pred["candidate"].eq(COLD_CANDIDATE)].copy()
    pred = pred.drop(columns=["quantile_width_log", "price_range_ratio"], errors="ignore")
    pred = pred.merge(qwidth, on=["_track6_row_id", "split"], how="left")
    pred["route"] = "cold"
    pred["analysis_candidate"] = "Cold LightGBM Quantile qwidth stable candidate"
    parts = []
    for split in ["validation", "test"]:
        base = read_split("cold", split)
        part = pred[pred["split"].eq(split)].merge(base, on="_track6_row_id", how="left", suffixes=("", "_base"))
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def enrich(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "actual_price" not in frame.columns:
        frame["actual_price"] = np.exp(frame["actual_log"])
    if "pred_price" not in frame.columns:
        frame["pred_price"] = np.exp(frame["pred_log"])
    frame["actual_price"] = safe_num(frame["actual_price"])
    frame["pred_price"] = safe_num(frame["pred_price"])
    frame["residual_log"] = np.log(frame["actual_price"]) - np.log(frame["pred_price"])
    frame["ape"] = (frame["pred_price"] - frame["actual_price"]).abs() / frame["actual_price"]
    frame["pred_actual_ratio"] = frame["pred_price"] / frame["actual_price"]
    frame["actual_price_band"] = frame["actual_price"].apply(band_price)
    frame["pred_price_band"] = frame["pred_price"].apply(band_price)
    frame["area_band"] = frame.get("area_cm2", pd.Series(index=frame.index, dtype=float)).apply(band_area)
    frame["artist_history_band"] = frame.get("artist_works_count_train", pd.Series(index=frame.index, dtype=float)).apply(
        lambda value: band_count(value, "artist_n")
    )
    frame["svc_group_n_band"] = frame.get("svc_group_n", pd.Series(index=frame.index, dtype=float)).apply(
        lambda value: band_count(value, "svc_n")
    )
    qwidth_source = frame.get("price_range_ratio", frame.get("routing_width", pd.Series(index=frame.index, dtype=float)))
    frame["uncertainty_band"] = qwidth_source.apply(band_qwidth)
    frame["meta_completeness_band"] = frame.get(
        "artist_meta_completeness_score", pd.Series(index=frame.index, dtype=float)
    ).apply(band_meta_score)
    frame["diagnostic_error_cause"] = frame.apply(classify_error, axis=1)
    return frame


def group_summary(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for key, group in frame.groupby(group_cols, dropna=False, observed=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = {col: value for col, value in zip(group_cols, key, strict=False)}
        row.update(metrics(group))
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["n", "MAPE"], ascending=[False, False])


@dataclass
class Rule:
    name: str
    cols: list[str]
    min_n: int = 30
    shrinkage: float = 0.65
    cap: float = 0.30


def learn_rule(validation: pd.DataFrame, rule: Rule) -> dict[tuple[str, ...], float]:
    mapping: dict[tuple[str, ...], float] = {}
    for key, group in validation.groupby(rule.cols, dropna=False, observed=False):
        if len(group) < rule.min_n:
            continue
        if not isinstance(key, tuple):
            key = (key,)
        correction = float(np.nanmedian(group["residual_log"])) * rule.shrinkage
        correction = max(-rule.cap, min(rule.cap, correction))
        mapping[tuple(str(item) for item in key)] = correction
    return mapping


def apply_rule(test: pd.DataFrame, rule: Rule, mapping: dict[tuple[str, ...], float]) -> pd.Series:
    values = []
    for _, row in test.iterrows():
        key = tuple(str(row.get(col)) for col in rule.cols)
        values.append(mapping.get(key, 0.0))
    return pd.Series(values, index=test.index)


def evaluate_route(route_frame: pd.DataFrame, route: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = route_frame[route_frame["split"].eq("validation")].copy()
    test = route_frame[route_frame["split"].eq("test")].copy()

    if route == "warm":
        rules = [
            Rule("global", [], min_n=1, shrinkage=0.5, cap=0.20),
            Rule("artist_history_band", ["artist_history_band"], min_n=40),
            Rule("svc_coverage_group_n", ["svc_coverage_tier", "svc_group_n_band"], min_n=25),
            Rule("area_pred_price", ["area_band", "pred_price_band"], min_n=25),
            Rule("material_support_area", ["medium_support_bucket", "area_band"], min_n=25),
        ]
    else:
        rules = [
            Rule("global", [], min_n=1, shrinkage=0.5, cap=0.20),
            Rule("qwidth_pred_price", ["uncertainty_band", "pred_price_band"], min_n=25),
            Rule("meta_area", ["meta_completeness_band", "area_band"], min_n=25),
            Rule("material_support_area", ["medium_support_bucket", "area_band"], min_n=25),
            Rule("source_area", ["track4_source", "area_band"], min_n=25),
        ]

    metric_rows = []
    metric_rows.append({"route": route, "candidate": "baseline", "rule": "none", **metrics(test)})
    mapping_rows = []
    test_out = test.copy()

    for rule in rules:
        if rule.name == "global":
            corr = float(np.nanmedian(validation["residual_log"])) * rule.shrinkage
            corr = max(-rule.cap, min(rule.cap, corr))
            pred_col = f"corrected_{rule.name}_pred_price"
            test_out[pred_col] = np.exp(np.log(test_out["pred_price"]) + corr)
            metric_rows.append({"route": route, "candidate": pred_col, "rule": rule.name, **metrics(test_out, pred_col)})
            mapping_rows.append(
                {
                    "route": route,
                    "rule": rule.name,
                    "segment_cols": "global",
                    "segments": 1,
                    "correction_log_min": corr,
                    "correction_log_median": corr,
                    "correction_log_max": corr,
                }
            )
            continue

        mapping = learn_rule(validation, rule)
        correction = apply_rule(test_out, rule, mapping)
        pred_col = f"corrected_{rule.name}_pred_price"
        test_out[pred_col] = np.exp(np.log(test_out["pred_price"]) + correction)
        metric_rows.append({"route": route, "candidate": pred_col, "rule": rule.name, **metrics(test_out, pred_col)})
        vals = list(mapping.values()) or [math.nan]
        mapping_rows.append(
            {
                "route": route,
                "rule": rule.name,
                "segment_cols": "+".join(rule.cols),
                "segments": len(mapping),
                "correction_log_min": float(np.nanmin(vals)),
                "correction_log_median": float(np.nanmedian(vals)),
                "correction_log_max": float(np.nanmax(vals)),
            }
        )

    return pd.DataFrame(metric_rows), pd.DataFrame(mapping_rows), test_out


def write_report(
    overall_metrics: pd.DataFrame,
    correction_metrics: pd.DataFrame,
    cause_summary: pd.DataFrame,
    segment_summary: pd.DataFrame,
    mapping_summary: pd.DataFrame,
    top_errors: pd.DataFrame,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    warm_best = correction_metrics[correction_metrics["route"].eq("warm")].sort_values(["MdAPE", "MAPE"]).iloc[0]
    cold_best = correction_metrics[correction_metrics["route"].eq("cold")].sort_values(["MdAPE", "MAPE"]).iloc[0]

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

    md = f"""# 기존 검증 데이터 기반 Warm/Cold 작품별 오차 원인 분석

## 1. 목적

- 0604 신규 데이터가 아니라 기존 validation/test split으로 분석
- Warm/Cold 최종 후보가 어떤 작품에서 크게 틀리는지 원인 분류
- validation에서 원인별 보정값을 만들고 test에서만 검증
- 정답 가격을 보고 붙이는 사후 원인 설명과, 운영에서 사전에 알 수 있는 피처 기반 보정을 분리

## 2. 기준 후보

- Warm 기준 후보: `{WARM_CANDIDATE}`
- Cold 기준 후보: `{COLD_CANDIDATE}`
- 조인 키: `_track6_row_id`
- 사용 데이터: `data/track6_split_with_year_type_edition_size_artist_name`

## 3. 결론

- Warm 최선 test 후보: `{warm_best["candidate"]}` / MdAPE `{warm_best["MdAPE"]:.4f}`, MAPE `{warm_best["MAPE"]:.4f}`, p95_APE `{warm_best["p95_APE"]:.4f}`
- Cold 최선 test 후보: `{cold_best["candidate"]}` / MdAPE `{cold_best["MdAPE"]:.4f}`, MAPE `{cold_best["MAPE"]:.4f}`, p95_APE `{cold_best["p95_APE"]:.4f}`
- 보정 후보는 실제 적용 전 반복 split 검증이 필요
- 이번 실험의 1차 목적은 “어떤 원인이 큰 오차를 만드는지”와 “원인 기반 보정 방향이 있는지”를 확인하는 것

## 4. 기준 성능

{md_table(overall_metrics)}

## 5. 원인별 오차 요약

{md_table(cause_summary)}

## 6. 관측 피처 구간별 취약 구간

{md_table(segment_summary, max_rows=40)}

## 7. validation 학습 -> test 적용 보정 후보

{md_table(correction_metrics)}

## 8. 보정 맵 요약

{md_table(mapping_summary)}

## 9. 큰 오차 상위 사례

{md_table(top_errors, max_rows=40)}

## 10. 해석

- Warm은 같은 작가 이력과 유사 작품 묶음 정보가 있어, 표본 수/작가 이력/크기 조합별 원인 분류가 가능
- Cold는 작가 가격 기준선이 없기 때문에, quantile width, 작가 메타 정보 완성도, 크기/재료 조합, source별 차이를 중심으로 원인을 봐야 함
- 전체 지표가 좋아도 특정 구간에서 p95_APE가 커지면 서비스 적용 시 가격 범위와 신뢰도 정책을 함께 조정해야 함
- validation에서 만든 구간 보정이 test에서 개선되지 않으면, 그 원인은 가격 보정보다는 신뢰도/범위 표시 정책으로 처리하는 편이 안전

## 11. 산출물

- `outputs/enriched_error_rows.csv`
- `outputs/overall_metrics.csv`
- `outputs/error_cause_summary.csv`
- `outputs/observable_segment_summary.csv`
- `outputs/correction_candidate_metrics.csv`
- `outputs/correction_mapping_summary.csv`
- `outputs/test_predictions_with_corrections.csv`
- `outputs/top_errors.csv`
"""
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>기존 검증 데이터 기반 Warm/Cold 작품별 오차 원인 분석</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1, h2 {{ color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; margin: 14px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dee8; padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .note {{ background: #f8fafc; border: 1px solid #d7dee8; padding: 12px; border-radius: 8px; margin-bottom: 18px; }}
  </style>
</head>
<body>
  <h1>기존 검증 데이터 기반 Warm/Cold 작품별 오차 원인 분석</h1>
  <div class="note">
    <p><strong>Warm 최선 test 후보:</strong> {warm_best["candidate"]} / MdAPE {warm_best["MdAPE"]:.4f}, MAPE {warm_best["MAPE"]:.4f}, p95_APE {warm_best["p95_APE"]:.4f}</p>
    <p><strong>Cold 최선 test 후보:</strong> {cold_best["candidate"]} / MdAPE {cold_best["MdAPE"]:.4f}, MAPE {cold_best["MAPE"]:.4f}, p95_APE {cold_best["p95_APE"]:.4f}</p>
  </div>
  <h2>기준 성능</h2>{overall_metrics.to_html(index=False, escape=True)}
  <h2>원인별 오차 요약</h2>{cause_summary.to_html(index=False, escape=True)}
  <h2>관측 피처 구간별 취약 구간</h2>{segment_summary.head(40).to_html(index=False, escape=True)}
  <h2>보정 후보 검증</h2>{correction_metrics.to_html(index=False, escape=True)}
  <h2>보정 맵 요약</h2>{mapping_summary.to_html(index=False, escape=True)}
  <h2>큰 오차 상위 사례</h2>{top_errors.head(60).to_html(index=False, escape=True)}
</body>
</html>
"""
    (REPORT_DIR / "result_report.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    warm = enrich(prepare_warm())
    cold = enrich(prepare_cold())
    all_rows = pd.concat([warm, cold], ignore_index=True, sort=False)

    overall = []
    for route, frame in [("warm", warm), ("cold", cold)]:
        for split, part in frame.groupby("split", observed=False):
            overall.append({"route": route, "split": split, "candidate": part["analysis_candidate"].iloc[0], **metrics(part)})
    overall_metrics = pd.DataFrame(overall)

    cause_summary = group_summary(all_rows[all_rows["split"].eq("test")], ["route", "diagnostic_error_cause"])
    segment_summary = group_summary(
        all_rows[all_rows["split"].eq("test")],
        ["route", "area_band", "pred_price_band", "medium_support_bucket", "uncertainty_band"],
    )

    correction_metric_parts = []
    mapping_parts = []
    test_parts = []
    for route, frame in [("warm", warm), ("cold", cold)]:
        metric_part, mapping_part, test_part = evaluate_route(frame, route)
        correction_metric_parts.append(metric_part)
        mapping_parts.append(mapping_part)
        test_parts.append(test_part)
    correction_metrics = pd.concat(correction_metric_parts, ignore_index=True)
    mapping_summary = pd.concat(mapping_parts, ignore_index=True)
    test_predictions = pd.concat(test_parts, ignore_index=True, sort=False)

    top_cols = [
        "route",
        "split",
        "_track6_row_id",
        "artist_name_ko",
        "artist_key",
        "title_raw",
        "actual_price",
        "pred_price",
        "ape",
        "pred_actual_ratio",
        "diagnostic_error_cause",
        "area_band",
        "pred_price_band",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "artist_history_band",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "price_range_ratio",
        "meta_completeness_band",
    ]
    top_cols = [col for col in top_cols if col in all_rows.columns]
    top_errors = all_rows[all_rows["split"].eq("test")].sort_values("ape", ascending=False)[top_cols].head(120)

    all_rows.to_csv(OUTPUT_DIR / "enriched_error_rows.csv", index=False)
    overall_metrics.to_csv(OUTPUT_DIR / "overall_metrics.csv", index=False)
    cause_summary.to_csv(OUTPUT_DIR / "error_cause_summary.csv", index=False)
    segment_summary.to_csv(OUTPUT_DIR / "observable_segment_summary.csv", index=False)
    correction_metrics.to_csv(OUTPUT_DIR / "correction_candidate_metrics.csv", index=False)
    mapping_summary.to_csv(OUTPUT_DIR / "correction_mapping_summary.csv", index=False)
    test_predictions.to_csv(OUTPUT_DIR / "test_predictions_with_corrections.csv", index=False)
    top_errors.to_csv(OUTPUT_DIR / "top_errors.csv", index=False)

    summary = {
        "created_from": "existing_track6_validation_test_split",
        "excluded": "0604_new_operational_data",
        "warm_candidate": WARM_CANDIDATE,
        "cold_candidate": COLD_CANDIDATE,
        "rows": {
            "warm": int(len(warm)),
            "cold": int(len(cold)),
            "test": int(len(all_rows[all_rows["split"].eq("test")])),
            "validation": int(len(all_rows[all_rows["split"].eq("validation")])),
        },
        "outputs": {
            "report_md": str((REPORT_DIR / "result_report.md").relative_to(PROJECT_ROOT)),
            "report_html": str((REPORT_DIR / "result_report.html").relative_to(PROJECT_ROOT)),
            "correction_metrics": str((OUTPUT_DIR / "correction_candidate_metrics.csv").relative_to(PROJECT_ROOT)),
        },
    }
    (OUTPUT_DIR / "experiment_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(
        overall_metrics=overall_metrics,
        correction_metrics=correction_metrics,
        cause_summary=cause_summary,
        segment_summary=segment_summary,
        mapping_summary=mapping_summary,
        top_errors=top_errors,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
