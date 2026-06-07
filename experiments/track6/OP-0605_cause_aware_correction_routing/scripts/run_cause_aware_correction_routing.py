from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0605_cause_aware_correction_routing"
OUTPUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

SOURCE_EXP_DIR = PROJECT_ROOT / "experiments/track6/OP-0605_existing_split_error_cause_customization"
SOURCE_ROWS_PATH = SOURCE_EXP_DIR / "outputs/enriched_error_rows.csv"


@dataclass(frozen=True)
class Rule:
    name: str
    cols: tuple[str, ...]
    min_n: int
    shrinkage: float
    cap: float


@dataclass(frozen=True)
class Policy:
    name: str
    objective: str
    segment_specific_objective: bool = False


WARM_RULES = [
    Rule("global", tuple(), min_n=1, shrinkage=0.50, cap=0.20),
    Rule("artist_history_band", ("artist_history_band",), min_n=25, shrinkage=0.65, cap=0.30),
    Rule("svc_coverage_group_n", ("svc_coverage_tier", "svc_group_n_band"), min_n=18, shrinkage=0.65, cap=0.30),
    Rule("area_pred_price", ("area_band", "pred_price_band"), min_n=18, shrinkage=0.65, cap=0.30),
    Rule("material_support_area", ("medium_support_bucket", "area_band"), min_n=18, shrinkage=0.65, cap=0.30),
]

COLD_RULES = [
    Rule("global", tuple(), min_n=1, shrinkage=0.50, cap=0.20),
    Rule("qwidth_pred_price", ("uncertainty_band", "pred_price_band"), min_n=25, shrinkage=0.65, cap=0.30),
    Rule("meta_area", ("meta_completeness_band", "area_band"), min_n=25, shrinkage=0.65, cap=0.30),
    Rule("material_support_area", ("medium_support_bucket", "area_band"), min_n=25, shrinkage=0.65, cap=0.30),
    Rule("source_area", ("track4_source", "area_band"), min_n=25, shrinkage=0.65, cap=0.30),
]

CORRECTION_WEIGHTS = {
    "w25": 0.25,
    "w50": 0.50,
    "w75": 0.75,
    "w100": 1.00,
}

POLICIES = [
    Policy("single_best_balanced", "balanced", segment_specific_objective=False),
    Policy("segment_balanced", "balanced", segment_specific_objective=False),
    Policy("segment_mape_guard", "mape_guard", segment_specific_objective=False),
    Policy("segment_p95_guard", "p95_guard", segment_specific_objective=False),
    Policy("segment_objective_aware", "balanced", segment_specific_objective=True),
]

EXPERT_POLICY_NAMES = ["expert_model_structure_guard"]

OBJECTIVE_BY_SEGMENT = {
    "warm_low_sample": "p95_guard",
    "warm_upper_tail_or_large": "p95_guard",
    "warm_material_weak": "balanced",
    "warm_regular": "balanced",
    "cold_sparse_artist_high_pred": "mape_guard",
    "cold_low_price_uncertain": "mape_guard",
    "cold_extreme_uncertainty": "p95_guard",
    "cold_upper_tail_or_large": "p95_guard",
    "cold_meta_sparse": "balanced",
    "cold_regular": "balanced",
}


def safe_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def metrics(frame: pd.DataFrame, pred_col: str) -> dict[str, float | int]:
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
            "median_ratio": math.nan,
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


def interval_metrics(frame: pd.DataFrame, pred_col: str, width_col: str) -> dict[str, float | int]:
    actual = safe_num(frame["actual_price"])
    pred = safe_num(frame[pred_col])
    width = safe_num(frame[width_col]).clip(lower=1.01)
    valid = frame[(actual > 0) & (pred > 0) & (width > 0)].copy()
    if valid.empty:
        return {
            "n": 0,
            "coverage": math.nan,
            "median_interval_ratio": math.nan,
            "p90_interval_ratio": math.nan,
            "miss_low_n": 0,
            "miss_high_n": 0,
        }
    actual = safe_num(valid["actual_price"])
    pred = safe_num(valid[pred_col])
    width = safe_num(valid[width_col]).clip(lower=1.01)
    lower = pred / width
    upper = pred * width
    interval_ratio = upper / lower
    return {
        "n": int(len(valid)),
        "coverage": float(((actual >= lower) & (actual <= upper)).mean()),
        "median_interval_ratio": float(interval_ratio.median()),
        "p90_interval_ratio": float(interval_ratio.quantile(0.90)),
        "miss_low_n": int((actual < lower).sum()),
        "miss_high_n": int((actual > upper).sum()),
    }


def score_from_metrics(row: pd.Series, objective: str) -> float:
    mdape = float(row["MdAPE"])
    mape = float(row["MAPE"])
    p95 = float(row["p95_APE"])
    if objective == "mape_guard":
        return (0.10 * mdape) + (0.60 * mape) + (0.30 * p95)
    if objective == "p95_guard":
        return (0.15 * mdape) + (0.25 * mape) + (0.60 * p95)
    return (0.50 * mdape) + (0.30 * mape) + (0.20 * p95)


def stable_validation_role(row_id: object) -> str:
    try:
        value = int(row_id)
    except (TypeError, ValueError):
        value = abs(hash(str(row_id)))
    return "correction_calibration" if value % 5 in {0, 1, 2} else "router_validation"


def is_low_count(value: object, threshold: float) -> bool:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return bool(pd.notna(numeric) and float(numeric) <= threshold)


def operational_segment(row: pd.Series) -> str:
    route = row.get("route")
    pred_price = pd.to_numeric(pd.Series([row.get("pred_price")]), errors="coerce").iloc[0]
    area = pd.to_numeric(pd.Series([row.get("area_cm2")]), errors="coerce").iloc[0]
    price_range_ratio = pd.to_numeric(pd.Series([row.get("price_range_ratio")]), errors="coerce").iloc[0]
    meta_band = str(row.get("meta_completeness_band") or "")
    medium_bucket = str(row.get("medium_support_bucket") or "")

    if route == "warm":
        if is_low_count(row.get("svc_group_n"), 10) or is_low_count(row.get("artist_works_count_train"), 10):
            return "warm_low_sample"
        if (pd.notna(pred_price) and pred_price >= 30_000_000) or (pd.notna(area) and area >= 20_000):
            return "warm_upper_tail_or_large"
        if "unknown" in medium_bucket or "other" in medium_bucket:
            return "warm_material_weak"
        return "warm_regular"

    sparse_artist = is_low_count(row.get("artist_works_count_train"), 5)
    meta_sparse = meta_band in {"meta_missing", "meta_low"}
    if sparse_artist and meta_sparse and pd.notna(pred_price) and pred_price >= 3_000_000:
        return "cold_sparse_artist_high_pred"
    if pd.notna(pred_price) and pred_price < 1_000_000 and pd.notna(price_range_ratio) and price_range_ratio >= 4.0:
        return "cold_low_price_uncertain"
    if pd.notna(price_range_ratio) and price_range_ratio >= 6.0:
        return "cold_extreme_uncertainty"
    if (pd.notna(pred_price) and pred_price >= 30_000_000) or (pd.notna(area) and area >= 20_000):
        return "cold_upper_tail_or_large"
    if meta_sparse:
        return "cold_meta_sparse"
    return "cold_regular"


def learn_rule(calibration: pd.DataFrame, rule: Rule) -> dict[tuple[str, ...], float]:
    if not rule.cols:
        correction = float(np.nanmedian(calibration["residual_log"])) * rule.shrinkage
        correction = max(-rule.cap, min(rule.cap, correction))
        return {("global",): correction}

    mapping: dict[tuple[str, ...], float] = {}
    for key, group in calibration.groupby(list(rule.cols), dropna=False, observed=False):
        if len(group) < rule.min_n:
            continue
        if not isinstance(key, tuple):
            key = (key,)
        correction = float(np.nanmedian(group["residual_log"])) * rule.shrinkage
        correction = max(-rule.cap, min(rule.cap, correction))
        mapping[tuple(str(item) for item in key)] = correction
    return mapping


def apply_rule(frame: pd.DataFrame, rule: Rule, mapping: dict[tuple[str, ...], float]) -> pd.Series:
    if not rule.cols:
        return pd.Series(mapping.get(("global",), 0.0), index=frame.index)
    values = []
    for _, row in frame.iterrows():
        key = tuple(str(row.get(col)) for col in rule.cols)
        values.append(mapping.get(key, 0.0))
    return pd.Series(values, index=frame.index)


def add_candidate_predictions(frame: pd.DataFrame, calibration: pd.DataFrame, route: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = frame.copy()
    out["baseline_pred_price"] = out["pred_price"]
    rules = WARM_RULES if route == "warm" else COLD_RULES
    mapping_rows = []
    for rule in rules:
        mapping = learn_rule(calibration, rule)
        correction = apply_rule(out, rule, mapping)
        for weight_name, weight in CORRECTION_WEIGHTS.items():
            col = f"{route}_{rule.name}_{weight_name}_pred_price"
            out[col] = np.exp(np.log(out["pred_price"]) + (correction * weight))
        vals = list(mapping.values()) or [math.nan]
        mapping_rows.append(
            {
                "route": route,
                "rule": rule.name,
                "segment_cols": "+".join(rule.cols) if rule.cols else "global",
                "segments": len(mapping),
                "correction_log_min": float(np.nanmin(vals)),
                "correction_log_median": float(np.nanmedian(vals)),
                "correction_log_max": float(np.nanmax(vals)),
            }
        )
    return out, pd.DataFrame(mapping_rows)


def candidate_columns(frame: pd.DataFrame) -> list[str]:
    return ["baseline_pred_price"] + [
        col
        for col in frame.columns
        if col.endswith("_pred_price")
        and col != "baseline_pred_price"
        and (col.startswith("warm_") or col.startswith("cold_"))
    ]


def candidate_metrics(frame: pd.DataFrame, route: str, segment: str | None = None) -> pd.DataFrame:
    part = frame if segment is None else frame[frame["operational_segment"].eq(segment)]
    rows = []
    for col in candidate_columns(frame):
        rows.append(
            {
                "route": route,
                "operational_segment": segment or "__route_all__",
                "candidate": col,
                **metrics(part, col),
            }
        )
    return pd.DataFrame(rows)


def select_candidate(metric_frame: pd.DataFrame, objective: str) -> tuple[str, float, float]:
    base = metric_frame[metric_frame["candidate"].eq("baseline_pred_price")].iloc[0]
    scored = metric_frame.copy()
    scored["objective"] = objective
    scored["score"] = scored.apply(lambda row: score_from_metrics(row, objective), axis=1)
    selected = scored.sort_values(["score", "MdAPE", "MAPE", "p95_APE"]).iloc[0]
    return str(selected["candidate"]), float(base["score"]) if "score" in base else float(scored[scored["candidate"].eq("baseline_pred_price")]["score"].iloc[0]), float(selected["score"])


def build_routed_predictions(
    route_frame: pd.DataFrame,
    route: str,
    policy: Policy,
    min_segment_n: int,
) -> tuple[pd.Series, pd.DataFrame]:
    router_validation = route_frame[route_frame["eval_split"].eq("router_validation")].copy()
    segments = sorted(route_frame["operational_segment"].dropna().unique())
    selection_rows = []

    if policy.name == "single_best_balanced":
        metric_frame = candidate_metrics(router_validation, route)
        selected_candidate, baseline_score, selected_score = select_candidate(metric_frame, policy.objective)
        for segment in segments:
            selection_rows.append(
                {
                    "route": route,
                    "policy": policy.name,
                    "operational_segment": segment,
                    "router_validation_n": int(
                        router_validation[router_validation["operational_segment"].eq(segment)].shape[0]
                    ),
                    "objective": policy.objective,
                    "selected_candidate": selected_candidate,
                    "baseline_score": baseline_score,
                    "selected_score": selected_score,
                    "fallback_used": False,
                }
            )
    else:
        route_default_metrics = candidate_metrics(router_validation, route)
        default_candidate, default_baseline_score, default_selected_score = select_candidate(
            route_default_metrics, policy.objective
        )
        for segment in segments:
            segment_part = router_validation[router_validation["operational_segment"].eq(segment)]
            objective = OBJECTIVE_BY_SEGMENT.get(segment, policy.objective) if policy.segment_specific_objective else policy.objective
            if len(segment_part) < min_segment_n:
                selection_rows.append(
                    {
                        "route": route,
                        "policy": policy.name,
                        "operational_segment": segment,
                        "router_validation_n": int(len(segment_part)),
                        "objective": objective,
                        "selected_candidate": default_candidate,
                        "baseline_score": default_baseline_score,
                        "selected_score": default_selected_score,
                        "fallback_used": True,
                    }
                )
                continue
            metric_frame = candidate_metrics(router_validation, route, segment)
            selected_candidate, baseline_score, selected_score = select_candidate(metric_frame, objective)
            selection_rows.append(
                {
                    "route": route,
                    "policy": policy.name,
                    "operational_segment": segment,
                    "router_validation_n": int(len(segment_part)),
                    "objective": objective,
                    "selected_candidate": selected_candidate,
                    "baseline_score": baseline_score,
                    "selected_score": selected_score,
                    "fallback_used": False,
                }
            )

    selection = pd.DataFrame(selection_rows)
    mapping = selection.set_index("operational_segment")["selected_candidate"].to_dict()
    routed = []
    for _, row in route_frame.iterrows():
        col = mapping.get(row["operational_segment"], "baseline_pred_price")
        routed.append(row[col])
    return pd.Series(routed, index=route_frame.index), selection


def apply_expert_policy(route_frame: pd.DataFrame, route: str) -> tuple[pd.Series, pd.DataFrame]:
    """Model-structure driven policy kept separate from metric-selected routing.

    This is a hypothesis test, not a final deployment rule. It uses only fields
    that are observable before the true price is known.
    """
    if route == "warm":
        mapping = {
            "warm_low_sample": "warm_area_pred_price_w75_pred_price",
            "warm_regular": "warm_artist_history_band_w100_pred_price",
            "warm_material_weak": "warm_area_pred_price_w100_pred_price",
            "warm_upper_tail_or_large": "baseline_pred_price",
        }
        objective_note = "Warm: 표본 부족 구간은 크기/예측가격 보정, 일반 구간은 작가 이력 보정, 고가/대형 구간은 기준값 유지"
    else:
        mapping = {
            "cold_extreme_uncertainty": "cold_qwidth_pred_price_w100_pred_price",
            "cold_low_price_uncertain": "cold_source_area_w100_pred_price",
            "cold_meta_sparse": "cold_qwidth_pred_price_w75_pred_price",
            "cold_sparse_artist_high_pred": "baseline_pred_price",
            "cold_upper_tail_or_large": "baseline_pred_price",
        }
        objective_note = "Cold: 퀀타일 폭이 큰 구간은 qwidth 보정, 저가 불확실 구간은 source/크기 보정, 희소 작가 고예측 구간은 기준값 유지"

    routed = []
    rows = []
    counts = route_frame[route_frame["eval_split"].eq("router_validation")]["operational_segment"].value_counts()
    for segment in sorted(route_frame["operational_segment"].dropna().unique()):
        selected = mapping.get(segment, "baseline_pred_price")
        rows.append(
            {
                "route": route,
                "policy": "expert_model_structure_guard",
                "operational_segment": segment,
                "router_validation_n": int(counts.get(segment, 0)),
                "objective": objective_note,
                "selected_candidate": selected,
                "baseline_score": math.nan,
                "selected_score": math.nan,
                "fallback_used": False,
            }
        )
    for _, row in route_frame.iterrows():
        selected = mapping.get(row["operational_segment"], "baseline_pred_price")
        routed.append(row[selected])
    return pd.Series(routed, index=route_frame.index), pd.DataFrame(rows)


def add_range_widths(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    warm_base = safe_num(out.get("routing_width", pd.Series(index=out.index, dtype=float))).clip(lower=1.10, upper=4.00)
    cold_base = np.sqrt(
        safe_num(out.get("price_range_ratio", pd.Series(index=out.index, dtype=float))).clip(lower=1.21, upper=64.00)
    )
    out["base_interval_factor"] = np.where(out["route"].eq("warm"), warm_base, cold_base)
    out["base_interval_factor"] = pd.Series(out["base_interval_factor"], index=out.index).fillna(1.40).clip(lower=1.10)

    multipliers = {
        "warm_low_sample": 1.20,
        "warm_upper_tail_or_large": 1.35,
        "warm_material_weak": 1.15,
        "warm_regular": 1.00,
        "cold_sparse_artist_high_pred": 1.60,
        "cold_low_price_uncertain": 1.50,
        "cold_extreme_uncertainty": 1.45,
        "cold_upper_tail_or_large": 1.35,
        "cold_meta_sparse": 1.20,
        "cold_regular": 1.00,
    }
    out["risk_adjusted_interval_factor"] = (
        out["base_interval_factor"] * out["operational_segment"].map(multipliers).fillna(1.0)
    ).clip(lower=1.10, upper=8.00)
    return out


def write_plan() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    plan = """# 원인별 보정/라우팅 후속 실험 계획

## 1. 실험 배경

- 기존 작품별 오차 분석에서 Warm은 단순 점가격 보정 효과가 작았음
- Cold는 보정 방식에 따라 MdAPE, MAPE, p95_APE가 서로 엇갈렸음
- 따라서 하나의 보정식을 전체에 적용하지 않고, 운영 시점에 알 수 있는 피처로 위험 구간을 나눈 뒤 구간별 보정 후보를 선택함

## 2. 데이터 통제

- 0604 신규 데이터는 라벨 정합성 검증 전이므로 튜닝에는 사용하지 않음
- 기존 validation/test split만 사용
- validation은 다시 두 부분으로 나눔
  - 보정값 학습용: residual_log 중앙값 보정 맵 생성
  - 라우팅 선택용: 구간별 어떤 보정 후보를 선택할지 결정
- 최종 평가는 test split에서만 수행

## 3. 실험 대상

- Warm v0.1 후보: 기존 Warm 70:30 계열 결합 후보의 예측값
- Cold v0.1 후보: LightGBM Quantile 기반 Cold 안정 후보의 예측값
- 보정 후보
  - 전체 평균 잔차 보정
  - 작가 이력/유사 표본 수 구간 보정
  - 예측 범위/예측 가격 구간 보정
  - 작가 메타/크기 구간 보정
  - 재료/지지체/크기 구간 보정
  - 수집 source/크기 구간 보정
  - 각 보정값의 25%, 50%, 75%, 100% 부분 적용

## 4. 비교 정책

- 전체 단일 후보 선택: 전체 validation에서 가장 안정적인 후보 하나만 선택
- 구간별 대표 가격 안정 정책: MdAPE 중심으로 선택하되 MAPE와 p95도 함께 반영
- 구간별 MAPE 방어 정책: 큰 과대 예측으로 평균 오차가 커지는 구간을 방어
- 구간별 p95 방어 정책: 상위 5% 큰 오차를 줄이는 데 집중
- 구간별 목적 분리 정책: 구간 특성에 따라 MAPE 방어와 p95 방어를 다르게 적용
- 모델 구조 기반 고정 정책: 수치 최적화가 아니라 모델 특성상 타당한 보정만 제한적으로 적용

## 5. 기대 결과

- Warm은 점가격보다 가격 범위/신뢰도 조정의 필요성이 더 큰지 확인
- Cold는 원인 구간별 보정 후보를 다르게 적용했을 때 MAPE 또는 p95가 줄어드는지 확인
- 최종 v0.1에 즉시 반영 가능한 보정인지, 추가 검증이 필요한 후보인지 구분
"""
    (REPORT_DIR / "experiment_plan.md").write_text(plan, encoding="utf-8")


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


def write_report(
    policy_metrics: pd.DataFrame,
    route_segment_metrics: pd.DataFrame,
    selection: pd.DataFrame,
    range_metrics: pd.DataFrame,
    mapping_summary: pd.DataFrame,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best_by_route = policy_metrics.sort_values(["route", "MdAPE", "MAPE", "p95_APE"]).groupby("route").head(1)
    md = f"""# 원인별 보정/라우팅 후속 실험 결과

## 1. 결론

{md_table(best_by_route)}

## 2. 해석

- Warm은 구간별 점가격 보정으로 기준 후보 대비 MdAPE/MAPE/p95가 함께 개선됐으나, 고가/대형 꼬리 구간은 기준값 유지가 더 안전함
- Warm은 추가로 가격 범위와 신뢰도 조정을 병행하면 서비스 표시 안정성을 높일 수 있음
- Cold는 자동 metric 선택보다 모델 구조 기반 고정 정책이 더 안정적이며, MdAPE/MAPE/p95를 함께 낮췄음
- Cold는 대표 가격 후보와 큰 오차 방어 후보를 분리해서 서비스 정책으로 사용할지 판단해야 함
- 모델 구조 기반 고정 정책은 validation 자동 선택과 별도로, Huber/Warm의 안정성 및 Quantile/Cold의 불확실성 정보를 실제 보정에 어떻게 제한적으로 쓸 수 있는지 확인하기 위한 가설형 실험임

## 3. test 정책별 성능

{md_table(policy_metrics)}

## 4. test 구간별 성능

{md_table(route_segment_metrics, max_rows=80)}

## 5. 라우팅 선택 내역

{md_table(selection)}

## 6. 가격 범위 정책 시뮬레이션

{md_table(range_metrics)}

## 7. 보정 맵 요약

{md_table(mapping_summary)}

## 8. 산출물

- `outputs/test_policy_metrics.csv`
- `outputs/test_segment_policy_metrics.csv`
- `outputs/routing_selection.csv`
- `outputs/range_policy_metrics.csv`
- `outputs/test_predictions_with_routing.csv`
- `outputs/correction_mapping_summary.csv`
"""
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>원인별 보정/라우팅 후속 실험 결과</title>
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
  <h1>원인별 보정/라우팅 후속 실험 결과</h1>
  <div class="note">
    <p>validation을 보정값 학습용/라우팅 선택용으로 나누고, test에서만 최종 비교했습니다.</p>
  </div>
  <h2>Route별 최선 후보</h2>{best_by_route.to_html(index=False, escape=True)}
  <h2>test 정책별 성능</h2>{policy_metrics.to_html(index=False, escape=True)}
  <h2>test 구간별 성능</h2>{route_segment_metrics.head(80).to_html(index=False, escape=True)}
  <h2>라우팅 선택 내역</h2>{selection.to_html(index=False, escape=True)}
  <h2>가격 범위 정책 시뮬레이션</h2>{range_metrics.to_html(index=False, escape=True)}
  <h2>보정 맵 요약</h2>{mapping_summary.to_html(index=False, escape=True)}
</body>
</html>
"""
    (REPORT_DIR / "result_report.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()

    rows = pd.read_csv(SOURCE_ROWS_PATH)
    rows["eval_split"] = rows["split"]
    validation_mask = rows["split"].eq("validation")
    rows.loc[validation_mask, "eval_split"] = rows.loc[validation_mask, "_track6_row_id"].apply(stable_validation_role)
    rows["operational_segment"] = rows.apply(operational_segment, axis=1)

    route_frames = []
    mapping_parts = []
    selection_parts = []
    policy_metric_rows = []
    segment_metric_rows = []
    range_metric_rows = []

    for route in ["warm", "cold"]:
        route_rows = rows[rows["route"].eq(route)].copy()
        calibration = route_rows[route_rows["eval_split"].eq("correction_calibration")].copy()
        route_with_candidates, mapping_summary = add_candidate_predictions(route_rows, calibration, route)
        mapping_parts.append(mapping_summary)

        min_segment_n = 12 if route == "warm" else 35
        for policy in POLICIES:
            routed_pred, selection = build_routed_predictions(route_with_candidates, route, policy, min_segment_n)
            selection_parts.append(selection)
            policy_col = f"{policy.name}_pred_price"
            route_with_candidates[policy_col] = routed_pred

            test = route_with_candidates[route_with_candidates["split"].eq("test")]
            policy_metric_rows.append({"route": route, "policy": policy.name, **metrics(test, policy_col)})
            for segment, segment_part in test.groupby("operational_segment", observed=False):
                segment_metric_rows.append(
                    {
                        "route": route,
                        "policy": policy.name,
                        "operational_segment": segment,
                        **metrics(segment_part, policy_col),
                    }
                )

        for policy_name in EXPERT_POLICY_NAMES:
            routed_pred, selection = apply_expert_policy(route_with_candidates, route)
            selection_parts.append(selection)
            policy_col = f"{policy_name}_pred_price"
            route_with_candidates[policy_col] = routed_pred

            test = route_with_candidates[route_with_candidates["split"].eq("test")]
            policy_metric_rows.append({"route": route, "policy": policy_name, **metrics(test, policy_col)})
            for segment, segment_part in test.groupby("operational_segment", observed=False):
                segment_metric_rows.append(
                    {
                        "route": route,
                        "policy": policy_name,
                        "operational_segment": segment,
                        **metrics(segment_part, policy_col),
                    }
                )

        test = route_with_candidates[route_with_candidates["split"].eq("test")].copy()
        policy_metric_rows.append({"route": route, "policy": "baseline", **metrics(test, "baseline_pred_price")})
        for segment, segment_part in test.groupby("operational_segment", observed=False):
            segment_metric_rows.append(
                {
                    "route": route,
                    "policy": "baseline",
                    "operational_segment": segment,
                    **metrics(segment_part, "baseline_pred_price"),
                }
            )

        test_with_ranges = add_range_widths(test)
        for pred_col in ["baseline_pred_price", "segment_objective_aware_pred_price", "expert_model_structure_guard_pred_price"]:
            for width_col, range_policy in [
                ("base_interval_factor", "base_range"),
                ("risk_adjusted_interval_factor", "risk_adjusted_range"),
            ]:
                range_metric_rows.append(
                    {
                        "route": route,
                        "pred_policy": pred_col.replace("_pred_price", ""),
                        "range_policy": range_policy,
                        **interval_metrics(test_with_ranges, pred_col, width_col),
                    }
                )

        route_frames.append(route_with_candidates)

    test_predictions = pd.concat(route_frames, ignore_index=True, sort=False)
    policy_metrics = pd.DataFrame(policy_metric_rows).sort_values(["route", "MdAPE", "MAPE", "p95_APE"])
    segment_policy_metrics = pd.DataFrame(segment_metric_rows).sort_values(
        ["route", "operational_segment", "policy"]
    )
    selection = pd.concat(selection_parts, ignore_index=True).sort_values(["route", "policy", "operational_segment"])
    range_metrics = pd.DataFrame(range_metric_rows).sort_values(["route", "pred_policy", "range_policy"])
    mapping_summary = pd.concat(mapping_parts, ignore_index=True)

    test_predictions.to_csv(OUTPUT_DIR / "test_predictions_with_routing.csv", index=False)
    policy_metrics.to_csv(OUTPUT_DIR / "test_policy_metrics.csv", index=False)
    segment_policy_metrics.to_csv(OUTPUT_DIR / "test_segment_policy_metrics.csv", index=False)
    selection.to_csv(OUTPUT_DIR / "routing_selection.csv", index=False)
    range_metrics.to_csv(OUTPUT_DIR / "range_policy_metrics.csv", index=False)
    mapping_summary.to_csv(OUTPUT_DIR / "correction_mapping_summary.csv", index=False)

    summary = {
        "source_rows": str(SOURCE_ROWS_PATH.relative_to(PROJECT_ROOT)),
        "validation_split": {
            "correction_calibration": "validation rows where _track6_row_id % 5 in {0,1,2}",
            "router_validation": "validation rows where _track6_row_id % 5 in {3,4}",
        },
        "outputs": {
            "plan": str((REPORT_DIR / "experiment_plan.md").relative_to(PROJECT_ROOT)),
            "report_md": str((REPORT_DIR / "result_report.md").relative_to(PROJECT_ROOT)),
            "report_html": str((REPORT_DIR / "result_report.html").relative_to(PROJECT_ROOT)),
            "policy_metrics": str((OUTPUT_DIR / "test_policy_metrics.csv").relative_to(PROJECT_ROOT)),
        },
    }
    (OUTPUT_DIR / "experiment_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(policy_metrics, segment_policy_metrics, selection, range_metrics, mapping_summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
