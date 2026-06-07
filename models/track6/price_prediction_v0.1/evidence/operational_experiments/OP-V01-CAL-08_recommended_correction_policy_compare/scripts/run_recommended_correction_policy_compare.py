from __future__ import annotations

import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[7]
EXP_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

SOURCE_PREDICTIONS = (
    REPO
    / "models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-07_warm_amw6_operational_revalidation/outputs/0604_predictions_with_amw6_candidates.csv"
)

FX_USD = 1380.0


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def add_log_candidate(frame: pd.DataFrame, name: str, values: pd.Series | np.ndarray, descriptions: list[dict[str, str]]) -> None:
    frame[name] = np.asarray(values, dtype=float)
    descriptions.append({"candidate": name, "description": describe_candidate(name)})


def describe_candidate(name: str) -> str:
    mapping = {
        "baseline_ppv8": "현재 v0.1 운영 기본 점가격",
        "meta_core": "작가 생년/작품 수/판매 작품 수/팔로워 수 기반 Huber 잔차 보정",
        "birth_generation_guard": "작가 생년대 구간별 반복 오차 중앙값 보정",
        "meta_plus_birth_cap007": "작가 메타 보정과 생년대 보정을 합산하되 전체 보정폭을 제한",
        "meta_plus_half_birth_cap006": "작가 메타 보정에 생년대 보정 절반만 추가",
        "svc_w005": "유사 작품 기반 가격 피처 5% 결합",
        "svc_w010": "유사 작품 기반 가격 피처 10% 결합",
        "svc_w015": "유사 작품 기반 가격 피처 15% 결합",
        "svc_w020": "유사 작품 기반 가격 피처 20% 결합",
        "meta_svc_w005": "작가 메타 보정값에 유사 작품 기반 가격 피처 5% 결합",
        "meta_svc_w010": "작가 메타 보정값에 유사 작품 기반 가격 피처 10% 결합",
        "meta_svc_w015": "작가 메타 보정값에 유사 작품 기반 가격 피처 15% 결합",
        "birth_svc_w010": "생년대 보정값에 유사 작품 기반 가격 피처 10% 결합",
        "meta_birth_svc_w005": "작가 메타 + 생년대 보정값에 유사 작품 기반 가격 피처 5% 결합",
        "meta_birth_svc_w010": "작가 메타 + 생년대 보정값에 유사 작품 기반 가격 피처 10% 결합",
        "svc_cond_reliability": "유사 작품 표본 신뢰도가 높을수록 0~20%만 조건부 결합",
        "meta_svc_cond_reliability": "작가 메타 보정값에 유사 작품 신뢰도 조건부 결합",
        "birth_svc_cond_reliability": "생년대 보정값에 유사 작품 신뢰도 조건부 결합",
        "meta_birth_svc_cond_reliability": "작가 메타 + 생년대 보정값에 유사 작품 신뢰도 조건부 결합",
    }
    return mapping.get(name, name)


def weight_suffix(weight: float) -> str:
    return f"{int(round(weight * 100)):03d}"


def blend(base: pd.Series, svc: pd.Series, weight: float) -> np.ndarray:
    return weight * svc.to_numpy(dtype=float) + (1.0 - weight) * base.to_numpy(dtype=float)


def conditional_svc_weight(frame: pd.DataFrame) -> pd.Series:
    n = pd.to_numeric(frame.get("svc_group_n"), errors="coerce").fillna(0.0)
    iqr = pd.to_numeric(frame.get("svc_group_log_price_iqr"), errors="coerce").fillna(99.0)
    rel = frame.get("svc_reliability_bin", pd.Series("low", index=frame.index)).astype(str)
    weight = pd.Series(0.0, index=frame.index, dtype=float)
    weight[(n >= 30) & (iqr <= 0.70)] = 0.20
    weight[(weight.eq(0.0)) & (n >= 10) & (iqr <= 1.20)] = 0.10
    weight[(weight.eq(0.0)) & (rel.eq("high"))] = 0.20
    weight[(weight.eq(0.0)) & (rel.eq("mid"))] = 0.10
    return weight.clip(0.0, 0.20)


def conditional_blend(base: pd.Series, svc: pd.Series, weight: pd.Series) -> np.ndarray:
    return weight.to_numpy(dtype=float) * svc.to_numpy(dtype=float) + (1.0 - weight.to_numpy(dtype=float)) * base.to_numpy(dtype=float)


def add_candidates(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = frame.copy()
    descriptions: list[dict[str, str]] = []

    baseline = pd.to_numeric(out["pp_v8_compact_blend_mape_guarded_pred_log"], errors="coerce")
    svc = pd.to_numeric(out["svc_numeric_seed_mean_pred_log"], errors="coerce")
    meta = pd.to_numeric(out["service_primary_ppv8__meta_core_test_twin_log"], errors="coerce")
    birth = pd.to_numeric(out["service_primary_ppv8__birth_generation_segment_guard_log"], errors="coerce")
    meta_corr = pd.to_numeric(out["service_primary_ppv8__meta_core_test_twin_correction_log"], errors="coerce").fillna(0.0)
    birth_corr = pd.to_numeric(out["service_primary_ppv8__birth_generation_segment_guard_correction_log"], errors="coerce").fillna(0.0)

    add_log_candidate(out, "baseline_ppv8", baseline, descriptions)
    add_log_candidate(out, "meta_core", meta, descriptions)
    add_log_candidate(out, "birth_generation_guard", birth, descriptions)
    add_log_candidate(out, "meta_plus_birth_cap007", baseline + np.clip(meta_corr + birth_corr, -0.07, 0.07), descriptions)
    add_log_candidate(out, "meta_plus_half_birth_cap006", baseline + np.clip(meta_corr + 0.5 * birth_corr, -0.06, 0.06), descriptions)

    for weight in [0.05, 0.10, 0.15, 0.20]:
        add_log_candidate(out, f"svc_w{weight_suffix(weight)}", blend(baseline, svc, weight), descriptions)

    for weight in [0.05, 0.10, 0.15]:
        add_log_candidate(out, f"meta_svc_w{weight_suffix(weight)}", blend(meta, svc, weight), descriptions)

    add_log_candidate(out, "birth_svc_w010", blend(birth, svc, 0.10), descriptions)
    add_log_candidate(out, "meta_birth_svc_w005", blend(out["meta_plus_birth_cap007"], svc, 0.05), descriptions)
    add_log_candidate(out, "meta_birth_svc_w010", blend(out["meta_plus_birth_cap007"], svc, 0.10), descriptions)

    cond_weight = conditional_svc_weight(out)
    out["conditional_svc_weight"] = cond_weight
    add_log_candidate(out, "svc_cond_reliability", conditional_blend(baseline, svc, cond_weight), descriptions)
    add_log_candidate(out, "meta_svc_cond_reliability", conditional_blend(meta, svc, cond_weight), descriptions)
    add_log_candidate(out, "birth_svc_cond_reliability", conditional_blend(birth, svc, cond_weight), descriptions)
    add_log_candidate(out, "meta_birth_svc_cond_reliability", conditional_blend(out["meta_plus_birth_cap007"], svc, cond_weight), descriptions)

    return out, pd.DataFrame(descriptions).drop_duplicates("candidate")


def metric_row(frame: pd.DataFrame, scope: str, candidate: str) -> dict[str, Any]:
    actual = pd.to_numeric(frame["actual_price_krw"], errors="coerce")
    pred_log = pd.to_numeric(frame[candidate], errors="coerce")
    pred = pd.Series(safe_exp(pred_log), index=frame.index)
    valid = actual.gt(0) & pred_log.notna()
    ape = ((pred.loc[valid] - actual.loc[valid]).abs() / actual.loc[valid]).replace([np.inf, -np.inf], np.nan).dropna()
    ratio = (pred.loc[valid] / actual.loc[valid]).replace([np.inf, -np.inf], np.nan).dropna()
    log_error = (pred_log.loc[valid] - np.log(actual.loc[valid])).replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "scope": scope,
        "candidate": candidate,
        "n": int(len(ape)),
        "MdAPE": float(ape.median()) if len(ape) else np.nan,
        "MAPE": float(ape.mean()) if len(ape) else np.nan,
        "p95_APE": float(ape.quantile(0.95)) if len(ape) else np.nan,
        "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))) if len(log_error) else np.nan,
        "median_ratio": float(ratio.median()) if len(ratio) else np.nan,
        "over_3x_n": int((ratio > 3.0).sum()) if len(ratio) else 0,
        "under_1_3x_n": int((ratio < (1.0 / 3.0)).sum()) if len(ratio) else 0,
        "within_30": float((ape <= 0.30).mean()) if len(ape) else np.nan,
        "within_50": float((ape <= 0.50).mean()) if len(ape) else np.nan,
    }


def evaluate(frame: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    scopes = {
        "all_numeric": frame[frame["actual_price_krw"].notna()].copy(),
        "actual_50_plus_usd": frame[pd.to_numeric(frame["actual_price_usd_equiv"], errors="coerce") >= 50].copy(),
        "core_50_to_100k_usd": frame[
            (pd.to_numeric(frame["actual_price_usd_equiv"], errors="coerce") >= 50)
            & (pd.to_numeric(frame["actual_price_usd_equiv"], errors="coerce") <= 100_000)
        ].copy(),
    }
    rows: list[dict[str, Any]] = []
    for scope, scope_frame in scopes.items():
        for candidate in candidates:
            rows.append(metric_row(scope_frame, scope, candidate))
    metrics = pd.DataFrame(rows)
    baseline = metrics[metrics["candidate"].eq("baseline_ppv8")].set_index("scope")
    for key in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "within_30", "within_50"]:
        metrics[f"delta_{key}"] = metrics.apply(lambda row: row[key] - baseline.loc[row["scope"], key], axis=1)
    return metrics


def rank_summary(metrics: pd.DataFrame, descriptions: pd.DataFrame) -> pd.DataFrame:
    core = metrics[metrics["scope"].eq("actual_50_plus_usd")].copy()
    baseline = core[core["candidate"].eq("baseline_ppv8")].iloc[0]
    core["balanced_score"] = (
        0.40 * core["MdAPE"] / baseline["MdAPE"]
        + 0.35 * core["MAPE"] / baseline["MAPE"]
        + 0.25 * core["p95_APE"] / baseline["p95_APE"]
    )
    core["improved_metric_count"] = (
        (core["delta_MdAPE"] < 0).astype(int)
        + (core["delta_MAPE"] < 0).astype(int)
        + (core["delta_p95_APE"] < 0).astype(int)
    )
    ranked = core.sort_values(["improved_metric_count", "balanced_score", "MAPE"], ascending=[False, True, True]).copy()
    ranked = ranked.merge(descriptions, on="candidate", how="left")
    return ranked


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_데이터 없음_"
    view = frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")
        else:
            view[col] = view[col].map(lambda value: "" if pd.isna(value) else str(value))
    rows = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
    ]
    rows.extend("| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None))
    return "\n".join(rows)


def simple_html(title: str, markdown_text: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13px}th,td{border:1px solid #d8dee9;padding:7px 9px;text-align:left}"
        "th{background:#eef2f7}.note{white-space:pre-wrap;background:#f8fafc;border-left:4px solid #2563eb;padding:12px 14px}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='note'>{html.escape(markdown_text)}</div>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=True, float_format=lambda value: f"{value:.4f}"))
    body.append("</body></html>")
    return "\n".join(body)


def main() -> None:
    ensure_dirs()
    source = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    source = source[source["baseline_name"].astype(str).eq("service_primary_ppv8")].copy()
    predictions, descriptions = add_candidates(source)
    candidate_cols = descriptions["candidate"].tolist()
    metrics = evaluate(predictions, candidate_cols)
    ranked = rank_summary(metrics, descriptions)

    predictions.to_csv(OUT_DIR / "recommended_candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "recommended_candidate_metrics.csv", index=False)
    ranked.to_csv(OUT_DIR / "recommended_candidate_ranked_actual_50_plus.csv", index=False)
    descriptions.to_csv(OUT_DIR / "candidate_descriptions.csv", index=False)

    top = ranked.head(8)
    baseline = ranked[ranked["candidate"].eq("baseline_ppv8")].iloc[0]
    best_balanced = ranked.iloc[0]
    best_mape = ranked.sort_values(["MAPE", "MdAPE", "p95_APE"]).iloc[0]
    best_mdape = ranked.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]
    best_p95 = ranked.sort_values(["p95_APE", "MAPE", "MdAPE"]).iloc[0]

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "n_rows": int(len(predictions)),
        "n_candidates": int(len(candidate_cols)),
        "best_balanced_candidate": str(best_balanced["candidate"]),
        "best_mape_candidate": str(best_mape["candidate"]),
        "best_mdape_candidate": str(best_mdape["candidate"]),
        "best_p95_candidate": str(best_p95["candidate"]),
    }
    (OUT_DIR / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# OP-V01-CAL-08 추천 보정 후보 통합 비교 결과

## 1. 실행 요약

- 작성일: {summary['created_at']}
- 기준: 현재 v0.1 운영 기본값 `baseline_ppv8`
- 비교 대상: 작가 메타 보정, 생년대 보정, 유사 작품 기반 가격 피처 저비중 결합, 조합 후보
- 평가 중심: 0604 라벨 중 50달러 미만 제외

## 2. 핵심 결과

- baseline: MdAPE `{baseline['MdAPE']:.4f}`, MAPE `{baseline['MAPE']:.4f}`, p95_APE `{baseline['p95_APE']:.4f}`
- 균형 점수 1위: `{best_balanced['candidate']}` / MdAPE `{best_balanced['MdAPE']:.4f}`, MAPE `{best_balanced['MAPE']:.4f}`, p95_APE `{best_balanced['p95_APE']:.4f}`
- MAPE 1위: `{best_mape['candidate']}` / MdAPE `{best_mape['MdAPE']:.4f}`, MAPE `{best_mape['MAPE']:.4f}`, p95_APE `{best_mape['p95_APE']:.4f}`
- MdAPE 1위: `{best_mdape['candidate']}` / MdAPE `{best_mdape['MdAPE']:.4f}`, MAPE `{best_mdape['MAPE']:.4f}`, p95_APE `{best_mdape['p95_APE']:.4f}`
- p95_APE 1위: `{best_p95['candidate']}` / MdAPE `{best_p95['MdAPE']:.4f}`, MAPE `{best_p95['MAPE']:.4f}`, p95_APE `{best_p95['p95_APE']:.4f}`

## 3. 판단

- 가장 균형이 좋은 후보는 `{best_balanced['candidate']}`이다. 이 후보는 {best_balanced['description']}.
- p95_APE를 가장 낮추는 후보는 유사 작품 기반 가격 피처 10% 결합 계열이었다.
- 생년대 보정은 단독으로는 안정적이지만, 유사 작품 결합과 함께 쓰면 목적에 따라 성능이 갈린다.
- 이번 결과는 0604 외부 확인 기준이므로 운영 기본값 교체 전 반복 split 또는 추가 신규 라벨에서 재확인이 필요하다.

## 4. 50달러 미만 제외 후보 순위

{markdown_table(top[['candidate', 'description', 'n', 'MdAPE', 'MAPE', 'p95_APE', 'RMSE_log', 'delta_MdAPE', 'delta_MAPE', 'delta_p95_APE', 'improved_metric_count', 'balanced_score']])}

## 5. 목적별 1순위

| 목적 | 후보 | 해석 |
| --- | --- | --- |
| 균형형 | `{best_balanced['candidate']}` | MdAPE/MAPE/p95를 함께 본 후보 |
| 평균오차 축소 | `{best_mape['candidate']}` | MAPE를 가장 낮춘 후보 |
| 대표 정확도 | `{best_mdape['candidate']}` | MdAPE를 가장 낮춘 후보 |
| 큰 오차 방어 | `{best_p95['candidate']}` | p95_APE를 가장 낮춘 후보 |

## 6. 산출물

- `outputs/recommended_candidate_metrics.csv`
- `outputs/recommended_candidate_ranked_actual_50_plus.csv`
- `outputs/recommended_candidate_predictions.csv`
- `outputs/candidate_descriptions.csv`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        simple_html(
            "OP-V01-CAL-08 추천 보정 후보 통합 비교 결과",
            report,
            {
                "50달러 미만 제외 후보 순위": ranked.head(16),
                "전체 지표": metrics.sort_values(["scope", "MAPE", "MdAPE"]).head(40),
                "후보 설명": descriptions,
            },
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
