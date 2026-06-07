#!/usr/bin/env python3
"""Build the latest Track6 final control/integration audit.

PP-I1~I5 were created before the latest Warm/Cold follow-up candidates.
This script does not retrain models. It re-indexes the newest validation/test
metrics and produces a policy-level final integration table so that deployment
candidate selection is not based on stale PP-I5 results.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-I6"
EXP_NAME = "PP-I6_latest_final_control_integration"
EXP_DIR = EXP_ROOT / EXP_NAME

METRIC_COLS = ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]
KEY_COLS = ["scope", "source_group", "experiment_id", "candidate", "policy", "slice"]


SOURCES: list[dict[str, Any]] = [
    {
        "source_group": "warm_latest_blend",
        "path": EXP_ROOT / "PP-V6_V8_warm_gap_summary_metrics.csv",
        "scope": None,
        "evidence_level": "validation_and_test",
        "selection_role": "latest_warm_core_candidates",
        "comment": "PP-L10 신규 후보를 기존 Warm 조합에 반영한 최신 fine blend/compact blend 후보",
    },
    {
        "source_group": "warm_mape_custom_correction",
        "path": EXP_ROOT / "PP-WMAPE_warm_mape_optimization" / "outputs" / "metrics.csv",
        "scope": "warm",
        "evidence_level": "validation_and_test",
        "selection_role": "latest_warm_mape_p95_candidates",
        "comment": "Warm MAPE 감소 목적의 구간별 validation 보정 후보",
    },
    {
        "source_group": "cold_qwidth_stability",
        "path": EXP_ROOT / "PP-Y21_cold_y18_split_seed_stability" / "outputs" / "metrics.csv",
        "scope": "cold",
        "evidence_level": "validation_test_eval_pool",
        "selection_role": "latest_cold_qwidth_candidates",
        "comment": "Cold q-width 기반 보정 후보의 validation/test/반복 holdout 안정성 검증",
    },
    {
        "source_group": "cold_search_correction",
        "path": EXP_ROOT / "PP-H27_search_candidate_stability_validation" / "outputs" / "metrics.csv",
        "scope": "cold",
        "evidence_level": "validation_and_test_by_slice",
        "selection_role": "latest_cold_external_search_candidates",
        "comment": "검색 소스군 기반 보정 후보. 최종 점 예측보다는 신뢰도/리뷰 정책과 함께 판단",
        "filter": {"slice": "overall"},
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def read_source(src: dict[str, Any]) -> pd.DataFrame:
    path = Path(src["path"])
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    for key, value in src.get("filter", {}).items():
        if key in df.columns:
            df = df[df[key].astype(str).eq(str(value))].copy()
    if df.empty:
        return df
    if "scope" not in df.columns:
        df["scope"] = src.get("scope", "unknown")
    elif src.get("scope") is not None:
        df["scope"] = df["scope"].fillna(src["scope"])
    if "policy" not in df.columns:
        df["policy"] = "not_recorded"
    if "slice" not in df.columns:
        df["slice"] = "overall"
    if "notes" not in df.columns:
        df["notes"] = ""
    if "n" not in df.columns and "row_n" in df.columns:
        df["n"] = df["row_n"]
    if "n" not in df.columns:
        df["n"] = np.nan
    df["source_group"] = src["source_group"]
    df["source_file"] = str(path.relative_to(REPO))
    df["evidence_level"] = src["evidence_level"]
    df["selection_role"] = src["selection_role"]
    df["source_comment"] = src["comment"]
    keep = [
        "source_group",
        "experiment_id",
        "candidate",
        "scope",
        "split",
        "policy",
        "slice",
        "n",
        *METRIC_COLS,
        "notes",
        "source_file",
        "evidence_level",
        "selection_role",
        "source_comment",
    ]
    for col in keep:
        if col not in df.columns:
            df[col] = np.nan
    return df[keep].copy()


def load_candidate_metrics() -> pd.DataFrame:
    frames = [read_source(src) for src in SOURCES]
    frames = [df for df in frames if not df.empty]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    for col in METRIC_COLS + ["n"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["split"] = out["split"].astype(str)
    out["scope"] = out["scope"].astype(str)
    out["candidate"] = out["candidate"].astype(str)
    out["policy"] = out["policy"].astype(str)
    out["slice"] = out["slice"].astype(str)
    return out


def pick_row(df: pd.DataFrame, objective: str) -> pd.Series | None:
    if df.empty:
        return None
    usable = df.dropna(subset=["MdAPE", "MAPE", "p95_APE"]).copy()
    if usable.empty:
        return None
    best_mdape = usable["MdAPE"].min()
    if objective == "mdape_primary":
        ordered = usable.sort_values(["MdAPE", "MAPE", "p95_APE", "RMSE_log"], na_position="last")
    elif objective == "mape_guarded":
        guarded = usable[usable["MdAPE"].le(best_mdape * 1.05)].copy()
        ordered = guarded.sort_values(["MAPE", "MdAPE", "p95_APE", "RMSE_log"], na_position="last")
    elif objective == "p95_guarded":
        guarded = usable[usable["MdAPE"].le(best_mdape * 1.08)].copy()
        ordered = guarded.sort_values(["p95_APE", "MdAPE", "MAPE", "RMSE_log"], na_position="last")
    elif objective == "balanced_rank":
        ranked = usable.copy()
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            ranked[f"{metric}_rank"] = ranked[metric].rank(method="min", ascending=True)
        ranked["rank_sum"] = ranked[[f"{m}_rank" for m in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]]].sum(axis=1)
        ordered = ranked.sort_values(["rank_sum", "MdAPE", "MAPE", "p95_APE"], na_position="last")
    else:
        raise ValueError(f"unknown objective: {objective}")
    if ordered.empty:
        return None
    return ordered.iloc[0]


def matching_test_row(metrics_df: pd.DataFrame, row: pd.Series) -> pd.Series | None:
    mask = metrics_df["split"].eq("test")
    for col in KEY_COLS:
        mask &= metrics_df[col].astype(str).eq(str(row[col]))
    test_rows = metrics_df[mask].copy()
    if test_rows.empty:
        return None
    return test_rows.iloc[0]


def build_policy_candidates(metrics_df: pd.DataFrame) -> pd.DataFrame:
    objectives = [
        ("mdape_primary", "중앙 오차 최소 후보"),
        ("mape_guarded", "평균 오차 최소 후보"),
        ("p95_guarded", "큰 오차 방어 후보"),
        ("balanced_rank", "균형 후보"),
    ]
    rows: list[dict[str, Any]] = []
    val_df = metrics_df[metrics_df["split"].eq("validation")].copy()
    for scope in ["warm", "cold"]:
        scope_val = val_df[val_df["scope"].eq(scope)].copy()
        for objective, objective_ko in objectives:
            picked = pick_row(scope_val, objective)
            if picked is None:
                continue
            test = matching_test_row(metrics_df, picked)
            base = {
                "scope": scope,
                "objective": objective,
                "objective_ko": objective_ko,
                "selection_basis": "validation",
                "source_group": picked["source_group"],
                "experiment_id": picked["experiment_id"],
                "candidate": picked["candidate"],
                "policy": picked["policy"],
                "slice": picked["slice"],
                "source_file": picked["source_file"],
                "selection_role": picked["selection_role"],
                "source_comment": picked["source_comment"],
            }
            for prefix, selected in [("validation", picked), ("test", test)]:
                if selected is None:
                    for col in ["n", *METRIC_COLS]:
                        base[f"{prefix}_{col}"] = np.nan
                else:
                    for col in ["n", *METRIC_COLS]:
                        base[f"{prefix}_{col}"] = selected[col]
            rows.append(base)
    return pd.DataFrame(rows)


def best_by_experiment(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    val_df = metrics_df[metrics_df["split"].eq("validation")].copy()
    for keys, group in val_df.groupby(["scope", "source_group"], dropna=False):
        best = group.sort_values(["MdAPE", "MAPE", "p95_APE"], na_position="last").head(3).copy()
        best.insert(0, "rank_in_source", range(1, len(best) + 1))
        rows.append(best)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def find_metric(metrics_df: pd.DataFrame, source_group: str, split: str, contains: str | None = None) -> dict[str, float] | None:
    df = metrics_df[metrics_df["source_group"].eq(source_group) & metrics_df["split"].eq(split)].copy()
    if contains:
        df = df[df["candidate"].astype(str).str.contains(contains, regex=False, na=False)].copy()
    if df.empty:
        return None
    row = df.sort_values(["MdAPE", "MAPE", "p95_APE"], na_position="last").iloc[0]
    return {col: float(row[col]) for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"] if pd.notna(row[col])}


def lookup_metric_row(metrics_df: pd.DataFrame, source_group: str, candidate: str, split: str) -> pd.Series | None:
    df = metrics_df[
        metrics_df["source_group"].eq(source_group)
        & metrics_df["candidate"].astype(str).eq(candidate)
        & metrics_df["split"].astype(str).eq(split)
    ].copy()
    if df.empty:
        return None
    if "slice" in df.columns:
        overall = df[df["slice"].astype(str).eq("overall")]
        if not overall.empty:
            df = overall
    return df.iloc[0]


def recommendation_row(
    metrics_df: pd.DataFrame,
    scope: str,
    use_case: str,
    source_group: str,
    candidate: str,
    decision: str,
    reason: str,
    next_action: str,
) -> dict[str, Any]:
    val = lookup_metric_row(metrics_df, source_group, candidate, "validation")
    test = lookup_metric_row(metrics_df, source_group, candidate, "test")
    row: dict[str, Any] = {
        "scope": scope,
        "use_case": use_case,
        "source_group": source_group,
        "candidate": candidate,
        "decision": decision,
        "reason": reason,
        "next_action": next_action,
    }
    for prefix, selected in [("validation", val), ("test", test)]:
        for col in ["n", *METRIC_COLS]:
            row[f"{prefix}_{col}"] = selected[col] if selected is not None and col in selected.index else np.nan
    if pd.notna(row.get("validation_MdAPE")) and pd.notna(row.get("test_MdAPE")):
        row["test_minus_validation_MdAPE"] = row["test_MdAPE"] - row["validation_MdAPE"]
    else:
        row["test_minus_validation_MdAPE"] = np.nan
    return row


def build_recommendations(metrics_df: pd.DataFrame) -> pd.DataFrame:
    rows = [
        recommendation_row(
            metrics_df,
            "warm",
            "대표 점 예측",
            "warm_latest_blend",
            "fine_blend_mape_guarded",
            "서비스 대표 후보 유지/우선",
            "validation/test 차이가 작고, PP-V6 실행 요약에서 MdAPE/MAPE/p95가 기존 대표 대비 균형 있게 개선됐다.",
            "최종 artifact 전 좁은 설정 재실행 또는 동일 split 재생성으로 고정한다.",
        ),
        recommendation_row(
            metrics_df,
            "warm",
            "배포 단순화/평균오차 방어",
            "warm_latest_blend",
            "compact_blend_mape_guarded",
            "서비스 보조 후보",
            "대표 후보보다 구조가 단순하고 MAPE/p95가 낮아 API 방어값 또는 단순 배포 후보로 적합하다.",
            "대표가와 별도로 range/confidence 정책에서 활용한다.",
        ),
        recommendation_row(
            metrics_df,
            "warm",
            "CatBoost residual 추가 보정",
            "warm_mape_custom_correction",
            "wmape_catboost_residual_v8_compact_blend_mape_guarded",
            "추가 split 검증 후 채택 검토",
            "validation 수치는 가장 강하지만 validation-test 차이가 커서 residual 모델 과적합 가능성을 확인해야 한다.",
            "동일 구조를 다른 seed/artist holdout으로 반복한 뒤 대표 후보 교체 여부를 판단한다.",
        ),
        recommendation_row(
            metrics_df,
            "cold",
            "대표 개선 후보",
            "cold_qwidth_stability",
            "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25",
            "서비스 개선 후보 유지",
            "validation 최저 후보는 아니지만 test MdAPE/MAPE/p95 균형과 PP-Y21 반복 holdout 안정성이 가장 납득 가능하다.",
            "Cold 기본 후보와 함께 confidence/range 제한 적용으로 운영한다.",
        ),
        recommendation_row(
            metrics_df,
            "cold",
            "큰 오차 방어 후보",
            "cold_qwidth_stability",
            "stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35",
            "p95 방어 전용",
            "p95는 낮지만 test MdAPE/MAPE가 대표 후보보다 약해 전체 점 예측 후보로는 부적합하다.",
            "위험 구간 range 확대 또는 fallback 정책에만 사용한다.",
        ),
        recommendation_row(
            metrics_df,
            "cold",
            "검색 보정 후보",
            "cold_search_correction",
            "h23_gallery_museum_median_cap0.2",
            "제한 적용",
            "검색 보정은 test MAPE/p95 개선 신호가 있으나 provider agreement가 낮아 직접 점 예측보다 신뢰도/검수 플래그가 안전하다.",
            "검색 provider 표준화와 manual review 기준이 붙은 뒤 제한적으로 적용한다.",
        ),
    ]
    return pd.DataFrame(rows)


def build_axis_audit(metrics_df: pd.DataFrame, policy_df: pd.DataFrame, recommendation_df: pd.DataFrame) -> pd.DataFrame:
    pp_i = EXP_ROOT / "PP-I_summary_metrics.csv"
    pp_j = EXP_ROOT / "PP-J_summary_metrics.csv"
    pp_s = EXP_ROOT / "PP-S_summary_metrics.csv"
    pp_t = EXP_ROOT / "PP-T_summary_metrics.csv"
    h22 = EXP_ROOT / "PP-H22_provider_agreement_stability" / "outputs" / "provider_agreement_by_artist.csv"
    rows = [
        {
            "axis": "모델 설정값 조정",
            "existing_experiments": "PP-I1 Warm Huber epsilon/alpha, PP-I2 Cold CatBoost depth/lr/l2, PP-S3 Cold LightGBM objective, PP-T4 Warm objective policy",
            "status": "실행됨",
            "audit_result": "기본 설정을 대체할 만큼 일관된 개선은 제한적이었다. 최신 성능 개선은 설정값보다 후보 조합과 구간 보정에서 발생했다.",
            "gap": "최신 후보 자체를 다시 전부 grid search한 실험은 아니다.",
            "action": "PP-I6에서는 설정 재학습이 아니라 최신 후보 정책 선택을 우선 보완한다. 최종 artifact 확정 직전에는 채택 후보 1개에 대해서만 좁은 범위 재튜닝을 권장한다.",
            "evidence_file": str(pp_i.relative_to(REPO)) if pp_i.exists() else "",
        },
        {
            "axis": "모델별 커스텀 보정",
            "existing_experiments": "PP-J1~J6, PP-WMAPE, PP-Y21, PP-H27/H22",
            "status": "실행됨",
            "audit_result": "Huber는 큰 오차/기여도 구간, CatBoost는 leaf/segment, LightGBM/Quantile은 q-width/tail 구간 중심으로 보정했다.",
            "gap": "PP-J는 오래된 기준 후보에서 시작했기 때문에, 최신 후보 기준 최종 선택표와 연결이 약했다.",
            "action": "PP-I6에서 최신 Warm WMAPE, Cold Y21/H27 후보를 같은 validation 선택 기준으로 연결한다.",
            "evidence_file": str(pp_j.relative_to(REPO)) if pp_j.exists() else "",
        },
        {
            "axis": "최종 통합",
            "existing_experiments": "PP-I5 final integrated candidate validation",
            "status": "부분 실행",
            "audit_result": "PP-I5는 실행됐지만 PP-V6/V8/WMAPE, PP-Y21/H27/H22 등 최신 후보가 반영되지 않았다.",
            "gap": "최신 Warm/Cold 후보 기준으로 최종 후보를 다시 선택하는 통합 표가 없었다.",
            "action": "PP-I6에서 최신 후보를 정규화하고 validation 기준 objective별 후보를 다시 선정한다.",
            "evidence_file": str((EXP_ROOT / "PP-I5_final_integrated_candidate_validation" / "reports" / "result_report.md").relative_to(REPO)),
        },
        {
            "axis": "외부 검색 보정 운영성",
            "existing_experiments": "PP-H22 provider agreement, PP-H27 search candidate stability",
            "status": "실행됨",
            "audit_result": "검색 보정은 일부 test 지표를 개선하지만 provider agreement가 낮아 점 예측 직접 피처로 과신하기 어렵다.",
            "gap": "정기 수집 표준화와 manual review 기준이 없으면 운영 리스크가 있다.",
            "action": "점 예측 후보에는 보조적으로만 반영하고, API에서는 신뢰도 하향/검수 플래그로 우선 사용한다.",
            "evidence_file": str(h22.relative_to(REPO)) if h22.exists() else "",
        },
    ]
    if not recommendation_df.empty:
        warm = recommendation_df[recommendation_df["scope"].eq("warm") & recommendation_df["use_case"].eq("대표 점 예측")]
        cold = recommendation_df[recommendation_df["scope"].eq("cold") & recommendation_df["use_case"].eq("대표 개선 후보")]
        if not warm.empty:
            rows.append({
                "axis": "PP-I6 Warm 최신 통합 결과",
                "existing_experiments": str(warm.iloc[0]["candidate"]),
                "status": "신규 실행",
                "audit_result": f"대표 점 예측 후보는 validation MdAPE {warm.iloc[0]['validation_MdAPE']:.4f}, test MdAPE {warm.iloc[0]['test_MdAPE']:.4f} 수준이다.",
                "gap": "WMAPE CatBoost residual 보정은 validation 수치가 강하지만 추가 split 검증 전 대표 후보 교체는 위험하다.",
                "action": "대표가/평균오차/큰오차 방어 목적별 후보를 API 정책에서 분리하고, residual 후보는 반복 검증 후 채택한다.",
                "evidence_file": str((EXP_DIR / "outputs" / "final_policy_candidates.csv").relative_to(REPO)),
            })
        if not cold.empty:
            rows.append({
                "axis": "PP-I6 Cold 최신 통합 결과",
                "existing_experiments": str(cold.iloc[0]["candidate"]),
                "status": "신규 실행",
                "audit_result": f"대표 개선 후보는 validation MdAPE {cold.iloc[0]['validation_MdAPE']:.4f}, test MdAPE {cold.iloc[0]['test_MdAPE']:.4f} 수준이다.",
                "gap": "Cold는 artist 구성 변동성이 커서 최종 서비스에는 보수적 기준선과 개선 후보를 함께 둔다.",
                "action": "Cold 개선 후보는 confidence/range 정책과 함께 제한 적용한다.",
                "evidence_file": str((EXP_DIR / "outputs" / "final_policy_candidates.csv").relative_to(REPO)),
            })
    return pd.DataFrame(rows)


def format_metric(value: Any) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.4f}"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    if df.empty:
        return ["데이터 없음"]
    labels = columns
    lines = [
        "| " + " | ".join(labels) + " |",
        "| " + " | ".join(["---"] * len(labels)) + " |",
    ]
    for _, row in df[columns].iterrows():
        values: list[str] = []
        for col in columns:
            value = row[col]
            if col.endswith(("MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50")) or col.startswith(("validation_", "test_")):
                values.append(format_metric(value))
            else:
                values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_markdown(
    metrics_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    best_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
) -> str:
    title = "PP-I6 최신 최종 통합/설정/커스텀 보정 감사"
    lines = [
        f"# {title}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 기존 `PP-I1~PP-I5`에서 다룬 설정값 조정, 커스텀 보정, 최종 통합이 최신 Warm/Cold 후보까지 반영됐는지 확인한다.",
        "- 기준: 후보 선택은 validation 지표로만 수행하고, test 지표는 선택 후 확인용으로 기록한다.",
        "- 성격: 이미 생성된 후보 예측/지표를 통합 감사하는 실험이며, 신규 모델 재학습 실험은 아니다.",
        "",
        "## 1. 결론",
        "",
        "- 설정값 조정 실험은 이미 진행됐다. 다만 최신 성능 개선의 주 원인은 설정값 자체가 아니라 모델 조합, 구간 보정, q-width 기반 보정이었다.",
        "- 모델별 커스텀 보정도 진행됐다. Huber는 큰 오차/기여도 구간, CatBoost는 leaf/segment, LightGBM/Quantile은 q-width/tail 구간을 사용했다.",
        "- 기존 최종 통합 실험 `PP-I5`는 실행됐지만 최신 후보를 포함하지 못했다. 따라서 최종 통합 판단은 `PP-I6` 기준으로 갱신해야 한다.",
        "- 단, validation 최저 후보가 항상 서비스 대표 후보는 아니다. validation-test 차이, 반복 holdout 안정성, 운영 설명 가능성을 같이 보고 추천 후보를 별도로 분리했다.",
        "",
        "## 2. 축별 감사 결과",
        "",
        *markdown_table(audit_df, ["axis", "status", "audit_result", "gap", "action"]),
        "",
        "## 3. 서비스 추천 후보",
        "",
        *markdown_table(recommendation_df, [
            "scope",
            "use_case",
            "candidate",
            "decision",
            "validation_MdAPE",
            "validation_MAPE",
            "validation_p95_APE",
            "test_MdAPE",
            "test_MAPE",
            "test_p95_APE",
            "test_minus_validation_MdAPE",
            "reason",
        ]),
        "",
        "## 4. 최신 후보 objective별 validation 선택 결과",
        "",
        *markdown_table(policy_df, [
            "scope",
            "objective_ko",
            "source_group",
            "candidate",
            "validation_MdAPE",
            "validation_MAPE",
            "validation_p95_APE",
            "test_MdAPE",
            "test_MAPE",
            "test_p95_APE",
        ]),
        "",
        "## 5. 소스별 validation 상위 후보",
        "",
        *markdown_table(best_df, [
            "rank_in_source",
            "scope",
            "source_group",
            "candidate",
            "policy",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
        ]),
        "",
        "## 6. 실행 판단",
        "",
        "- Warm은 `PP-V6/V8/WMAPE` 계열을 최신 후보군으로 보고, 목적별로 대표가/평균오차/큰오차 방어 후보를 분리한다.",
        "- Warm 대표 후보는 일단 `PP-V6 fine_blend_mape_guarded`를 유지하고, `PP-WMAPE` CatBoost residual 보정은 추가 split 검증 후 교체 여부를 본다.",
        "- Cold 대표 개선 후보는 `PP-Y21 qwidth_bin_oof_min30_cap0.25`로 두고, `pred_x_qwidth`는 큰 오차 방어 전용으로만 본다.",
        "- `PP-H27` 검색 보정은 provider agreement 리스크 때문에 점 예측 직접 반영보다 신뢰도 하향/검수 플래그와 함께 제한적으로 쓴다.",
        "- 최종 서비스 적용 전에는 추천 후보만 대상으로 좁은 범위 설정값 재튜닝과 동일 split 재실행을 추가하면 충분하다.",
        "",
        "## 7. 산출물",
        "",
        f"- 정규화 후보 지표: `{(EXP_DIR / 'outputs' / 'normalized_candidate_metrics.csv').relative_to(REPO)}`",
        f"- 최종 정책 후보표: `{(EXP_DIR / 'outputs' / 'final_policy_candidates.csv').relative_to(REPO)}`",
        f"- 서비스 추천 후보표: `{(EXP_DIR / 'outputs' / 'service_recommendation_candidates.csv').relative_to(REPO)}`",
        f"- 축별 감사표: `{(EXP_DIR / 'outputs' / 'experiment_axis_audit.csv').relative_to(REPO)}`",
    ]
    return "\n".join(lines) + "\n"


def render_html(
    md: str,
    metrics_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    recommendation_df: pd.DataFrame,
) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(EXP_ID)} latest final integration</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif; margin: 28px; color: #1f2933; line-height: 1.55; }}
    h1, h2 {{ color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 14px 0 28px; }}
    th, td {{ border: 1px solid #d8dee4; padding: 7px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
    .note {{ background: #f8fafc; border-left: 4px solid #2563eb; padding: 10px 12px; margin-bottom: 18px; }}
  </style>
</head>
<body>
  <h1>{html.escape(EXP_ID)} 최신 최종 통합/설정/커스텀 보정 감사</h1>
  <div class="note">후보 선택은 validation 기준이며, test는 선택 후 확인용입니다.</div>
  <h2>서비스 추천 후보</h2>
  {recommendation_df.to_html(index=False, escape=True)}
  <h2>최종 정책 후보</h2>
  {policy_df.to_html(index=False, escape=True)}
  <h2>축별 감사</h2>
  {audit_df.to_html(index=False, escape=True)}
  <h2>전체 정규화 후보 지표</h2>
  {metrics_df.to_html(index=False, escape=True)}
  <h2>Markdown 원문</h2>
  <pre>{html.escape(md)}</pre>
</body>
</html>
"""


def main() -> None:
    ensure_dirs()
    metrics_df = load_candidate_metrics()
    if metrics_df.empty:
        raise SystemExit("No source metrics found.")
    policy_df = build_policy_candidates(metrics_df)
    recommendation_df = build_recommendations(metrics_df)
    best_df = best_by_experiment(metrics_df)
    audit_df = build_axis_audit(metrics_df, policy_df, recommendation_df)

    metrics_df.to_csv(EXP_DIR / "outputs" / "normalized_candidate_metrics.csv", index=False)
    policy_df.to_csv(EXP_DIR / "outputs" / "final_policy_candidates.csv", index=False)
    recommendation_df.to_csv(EXP_DIR / "outputs" / "service_recommendation_candidates.csv", index=False)
    best_df.to_csv(EXP_DIR / "outputs" / "validation_top_candidates_by_source.csv", index=False)
    audit_df.to_csv(EXP_DIR / "outputs" / "experiment_axis_audit.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_name": EXP_NAME,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "selection_rule": "select by validation; test is confirmation only",
        "sources": [
            {**src, "path": str(Path(src["path"]).relative_to(REPO))}
            for src in SOURCES
        ],
        "metrics": METRIC_COLS,
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "model_manifest.json").write_text(json.dumps({
        "target": "ln_price_krw",
        "mode": "latest_policy_integration_audit",
        "note": "This experiment does not create a new fitted model artifact.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "data" / "source_files.json").write_text(json.dumps(config["sources"], ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_markdown(metrics_df, policy_df, best_df, audit_df, recommendation_df)
    html_doc = render_html(md, metrics_df, policy_df, audit_df, recommendation_df)
    for path in [
        EXP_DIR / "README.md",
        EXP_DIR / "reports" / "result_report.md",
        DOC_ROOT / "pp_i6_latest_final_control_integration_summary.md",
    ]:
        path.write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "completed",
        "experiment": str(EXP_DIR.relative_to(REPO)),
        "policy_candidates": str((EXP_DIR / "outputs" / "final_policy_candidates.csv").relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "doc": str((DOC_ROOT / "pp_i6_latest_final_control_integration_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
