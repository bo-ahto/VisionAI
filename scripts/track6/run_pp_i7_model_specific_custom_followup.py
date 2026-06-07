#!/usr/bin/env python3
"""Run PP-I7 model-specific custom correction follow-up checks.

The goal is not to add another broad model search. PP-I7 takes the latest
Warm/Cold candidates and checks whether their model-specific correction logic
is stable enough to become a service policy.
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
EXP_ID = "PP-I7"
EXP_SLUG = "PP-I7_model_specific_custom_followup"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "모델 구조별 커스텀 보정 후속 검증"
SEED = 20260603
BOOTSTRAP_ITERATIONS = 500

WARM_BASE_LABEL = "warm_v6_fine_blend_mape_guarded"
WARM_CANDIDATES = [
    {
        "label": "warm_v6_fine_blend_mape_guarded",
        "source": "PP-V6",
        "path": EXP_ROOT / "PP-V6_warm_l10_refreshed_fine_blend" / "outputs" / "predictions.csv",
        "candidate": "fine_blend_mape_guarded",
        "policy": "current_representative",
        "use_case": "대표 점 예측",
    },
    {
        "label": "warm_v8_compact_blend_mape_guarded",
        "source": "PP-V8",
        "path": EXP_ROOT / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv",
        "candidate": "compact_blend_mape_guarded",
        "policy": "deployment_simplification",
        "use_case": "배포 단순화/평균오차 방어",
    },
    {
        "label": "warm_wmape_catboost_residual_v8",
        "source": "PP-WMAPE",
        "path": EXP_ROOT / "PP-WMAPE_warm_mape_optimization" / "outputs" / "candidate_predictions.csv",
        "candidate": "wmape_catboost_residual_v8_compact_blend_mape_guarded",
        "policy": "catboost_residual_after_warm_blend",
        "use_case": "CatBoost residual 보정",
    },
    {
        "label": "warm_wmape_catboost_residual_h29",
        "source": "PP-WMAPE",
        "path": EXP_ROOT / "PP-WMAPE_warm_mape_optimization" / "outputs" / "candidate_predictions.csv",
        "candidate": "wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05",
        "policy": "search_calibrated_catboost_residual",
        "use_case": "검색 보정 + CatBoost residual",
    },
]

COLD_BASE_LABEL = "cold_pp_y2_base"
COLD_SOURCE_PATH = EXP_ROOT / "PP-H20_H26_search_feature_expansion" / "outputs" / "candidate_predictions.csv"
COLD_AGREEMENT_PATH = EXP_ROOT / "PP-H22_provider_agreement_stability" / "outputs" / "provider_agreement_by_artist.csv"
COLD_SOURCE_CANDIDATES = {
    "gallery_museum_cap0.2": "h23_gallery_museum_median_cap0.2__pred_log",
    "news_cap0.2": "h23_news_median_cap0.2__pred_log",
    "exhibition_cap0.2": "h23_exhibition_median_cap0.2__pred_log",
    "risk_qwidth_action_cap0.2": "h26_risk_qwidth_action_median_cap0.2__pred_log",
}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    if frame.empty:
        return {
            "n": 0,
            "RMSE_log": np.nan,
            "MdAPE": np.nan,
            "MAPE": np.nan,
            "p95_APE": np.nan,
            "Within_30": np.nan,
            "Within_50": np.nan,
        }
    actual_log = frame["actual_log"].astype(float).to_numpy()
    actual_price = frame["actual_price"].astype(float).to_numpy()
    pred = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((actual_log - pred) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def load_split_meta(scope: str) -> pd.DataFrame:
    frames = []
    for split in ["validation", "test"]:
        name = "val" if split == "validation" else "test"
        path = REPO / "data" / "track6_split" / f"track6_{name}_{scope}.csv"
        frame = pd.read_csv(path, low_memory=False)
        keep = [col for col in ["_track6_row_id", "artist_key", "artist_name_ko"] if col in frame.columns]
        part = frame[keep].drop_duplicates("_track6_row_id").copy()
        part["split"] = split
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def load_warm_predictions() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    meta = load_split_meta("warm")
    for cfg in WARM_CANDIDATES:
        path = Path(cfg["path"])
        if not path.exists():
            continue
        df = pd.read_csv(path, low_memory=False)
        if "scope" in df.columns:
            df = df[df["scope"].astype(str).eq("warm")].copy()
        df = df[
            df["split"].astype(str).isin(["validation", "test"])
            & df["candidate"].astype(str).eq(str(cfg["candidate"]))
        ].copy()
        if df.empty:
            continue
        keep = ["split", "_track6_row_id", "actual_log", "pred_log", "actual_price"]
        part = df[keep].drop_duplicates(["split", "_track6_row_id"]).copy()
        part["candidate_label"] = cfg["label"]
        part["source_experiment"] = cfg["source"]
        part["source_candidate"] = cfg["candidate"]
        part["policy"] = cfg["policy"]
        part["use_case"] = cfg["use_case"]
        part = part.merge(meta, on=["split", "_track6_row_id"], how="left")
        frames.append(part)
    if not frames:
        raise RuntimeError("No warm candidate predictions found.")
    return pd.concat(frames, ignore_index=True)


def long_metrics(long_df: pd.DataFrame, scope: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, split), group in long_df.groupby(["candidate_label", "split"], dropna=False):
        first = group.iloc[0]
        rows.append({
            "experiment_id": EXP_ID,
            "scope": scope,
            "candidate": candidate,
            "split": split,
            "source_experiment": first.get("source_experiment", ""),
            "source_candidate": first.get("source_candidate", ""),
            "policy": first.get("policy", ""),
            "use_case": first.get("use_case", ""),
            **metric_values(group, group["pred_log"]),
        })
    return pd.DataFrame(rows)


def pivot_predictions(long_df: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["split", "_track6_row_id", "actual_log", "actual_price", "artist_key", "artist_name_ko"]
    base = long_df[key_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    wide = long_df.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate_label",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    return base.merge(wide, on=["split", "_track6_row_id"], how="inner")


def bootstrap_compare(
    wide: pd.DataFrame,
    candidate_labels: list[str],
    baseline_label: str,
    scope: str,
    split: str = "test",
) -> pd.DataFrame:
    test = wide[wide["split"].astype(str).eq(split)].dropna(subset=[baseline_label]).copy()
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, Any]] = []
    if test.empty:
        return pd.DataFrame()
    row_indices = np.arange(len(test))
    artist_keys = test["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    unique_artists = np.unique(artist_keys)
    artist_to_indices = {artist: np.flatnonzero(artist_keys == artist) for artist in unique_artists}

    for iteration in range(BOOTSTRAP_ITERATIONS):
        row_sample = rng.choice(row_indices, size=len(row_indices), replace=True)
        artist_sample_keys = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        artist_sample = np.concatenate([artist_to_indices[artist] for artist in artist_sample_keys])
        for mode, indices in [("row_bootstrap", row_sample), ("artist_bootstrap", artist_sample)]:
            sample = test.iloc[indices].copy()
            base_metrics = metric_values(sample, sample[baseline_label])
            for candidate in candidate_labels:
                if candidate == baseline_label or candidate not in sample.columns:
                    continue
                usable = sample.dropna(subset=[candidate])
                if usable.empty:
                    continue
                base_on_usable = metric_values(usable, usable[baseline_label])
                cand_metrics = metric_values(usable, usable[candidate])
                row = {
                    "experiment_id": EXP_ID,
                    "scope": scope,
                    "candidate": candidate,
                    "baseline": baseline_label,
                    "split": split,
                    "bootstrap_mode": mode,
                    "iteration": iteration,
                    "n": cand_metrics["n"],
                }
                for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                    row[f"baseline_{metric}"] = base_on_usable[metric]
                    row[f"candidate_{metric}"] = cand_metrics[metric]
                    row[f"delta_{metric}"] = base_on_usable[metric] - cand_metrics[metric]
                rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    if bootstrap.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (scope, candidate, mode), group in bootstrap.groupby(["scope", "candidate", "bootstrap_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "scope": scope,
            "candidate": candidate,
            "bootstrap_mode": mode,
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"delta_{metric}"].astype(float).dropna().to_numpy()
            row[f"delta_{metric}_median"] = float(np.median(values))
            row[f"delta_{metric}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"delta_{metric}_ci_high"] = float(np.quantile(values, 0.975))
            row[f"delta_{metric}_prob_improve"] = float(np.mean(values > 0))
        rows.append(row)
    return pd.DataFrame(rows)


def cold_conditions(df: pd.DataFrame) -> dict[str, pd.Series]:
    action_candidate = df["recommended_action"].astype(str).eq("candidate_for_h14_h18")
    qwidth_risk = df["qwidth_bin"].astype(str).eq("risk")
    qwidth_caution_risk = df["qwidth_bin"].astype(str).isin(["caution", "risk"])
    return {
        "full": pd.Series(True, index=df.index),
        "action_candidate_only": action_candidate,
        "qwidth_risk_only": qwidth_risk,
        "qwidth_caution_risk_only": qwidth_caution_risk,
        "action_and_caution_risk": action_candidate & qwidth_caution_risk,
    }


def load_cold_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not COLD_SOURCE_PATH.exists():
        raise RuntimeError(f"Missing cold source: {COLD_SOURCE_PATH}")
    pred = pd.read_csv(COLD_SOURCE_PATH, low_memory=False)
    meta = load_split_meta("cold")
    pred = pred.merge(meta, on=["split", "_track6_row_id"], how="left", suffixes=("", "_split"))
    if "artist_key_split" in pred.columns:
        pred["artist_key"] = pred["artist_key"].fillna(pred["artist_key_split"])
    agreement_cols: list[str] = []
    if COLD_AGREEMENT_PATH.exists():
        agreement = pd.read_csv(COLD_AGREEMENT_PATH, low_memory=False)
        agreement_cols = [
            col for col in [
                "artist_search_name",
                "provider_agreement_score",
                "provider_agreement_grade",
                "provider_disagreement_risk_flag",
            ]
            if col in agreement.columns
        ]
        pred = pred.merge(agreement[agreement_cols].drop_duplicates("artist_search_name"), on="artist_search_name", how="left")

    frames = []
    base = pred[[
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "artist_key",
        "artist_name_ko",
        "artist_search_name",
        "recommended_action",
        "qwidth_bin",
        *[col for col in agreement_cols if col != "artist_search_name"],
    ]].copy()
    base["candidate_label"] = COLD_BASE_LABEL
    base["source_experiment"] = "PP-H20_H26"
    base["source_candidate"] = "pp_y2_base"
    base["policy"] = "baseline"
    base["use_case"] = "Cold 기준선"
    base["pred_log"] = pred["pred_log"].astype(float)
    frames.append(base)

    conditions = cold_conditions(pred)
    for source_name, pred_col in COLD_SOURCE_CANDIDATES.items():
        if pred_col not in pred.columns:
            continue
        for condition_name, condition_mask in conditions.items():
            part = base.copy()
            part["candidate_label"] = f"cold_search_{source_name}_{condition_name}"
            part["source_candidate"] = source_name
            part["policy"] = f"search_restricted_{condition_name}"
            part["use_case"] = "검색/위험 구간 제한 보정"
            part["pred_log"] = np.where(condition_mask, pred[pred_col].astype(float), pred["pred_log"].astype(float))
            part["applied_rate"] = float(np.mean(condition_mask))
            frames.append(part)
    long_df = pd.concat(frames, ignore_index=True)
    condition_map = pd.DataFrame([
        {
            "condition": name,
            "description": {
                "full": "전체 샘플에 보정 적용",
                "action_candidate_only": "검색 action이 candidate_for_h14_h18인 샘플에만 보정 적용",
                "qwidth_risk_only": "qwidth_bin이 risk인 샘플에만 보정 적용",
                "qwidth_caution_risk_only": "qwidth_bin이 caution 또는 risk인 샘플에만 보정 적용",
                "action_and_caution_risk": "검색 action 후보이면서 caution/risk인 샘플에만 보정 적용",
            }[name],
            "validation_applied_rate": float(conditions[name][pred["split"].astype(str).eq("validation")].mean()),
            "test_applied_rate": float(conditions[name][pred["split"].astype(str).eq("test")].mean()),
        }
        for name in conditions
    ])
    return long_df, condition_map


def select_validation_candidates(metrics_df: pd.DataFrame, scope: str, baseline_label: str) -> pd.DataFrame:
    scope_metrics = metrics_df[metrics_df["scope"].eq(scope)].copy()
    val = scope_metrics[scope_metrics["split"].eq("validation")].copy()
    test = scope_metrics[scope_metrics["split"].eq("test")].copy()
    baseline_val = val[val["candidate"].eq(baseline_label)]
    baseline_test = test[test["candidate"].eq(baseline_label)]
    if baseline_val.empty:
        return pd.DataFrame()
    base_mdape = float(baseline_val.iloc[0]["MdAPE"])
    objectives = []
    for name, filtered, sort_cols in [
        ("mdape_primary", val, ["MdAPE", "MAPE", "p95_APE"]),
        ("mape_guarded", val[val["MdAPE"].le(base_mdape * 1.05)], ["MAPE", "MdAPE", "p95_APE"]),
        ("p95_guarded", val[val["MdAPE"].le(base_mdape * 1.08)], ["p95_APE", "MdAPE", "MAPE"]),
    ]:
        filtered = filtered[~filtered["candidate"].eq(baseline_label)].copy()
        if filtered.empty:
            continue
        picked = filtered.sort_values(sort_cols).iloc[0].to_dict()
        picked["objective"] = name
        match = test[test["candidate"].eq(picked["candidate"])]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            picked[f"test_{metric}"] = float(match.iloc[0][metric]) if not match.empty else np.nan
            picked[f"baseline_validation_{metric}"] = float(baseline_val.iloc[0][metric])
            picked[f"baseline_test_{metric}"] = float(baseline_test.iloc[0][metric]) if not baseline_test.empty else np.nan
        objectives.append(picked)
    return pd.DataFrame(objectives)


def add_recommendations(metrics_df: pd.DataFrame, bootstrap_summary: pd.DataFrame, baseline_label: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, group in metrics_df.groupby("scope", dropna=False):
        base_test = group[(group["candidate"].eq(baseline_label)) & (group["split"].eq("test"))]
        if base_test.empty:
            continue
        base = base_test.iloc[0]
        test = group[group["split"].eq("test") & ~group["candidate"].eq(baseline_label)].copy()
        for row in test.itertuples(index=False):
            mdape_delta = float(base.MdAPE - row.MdAPE)
            mape_delta = float(base.MAPE - row.MAPE)
            p95_delta = float(base.p95_APE - row.p95_APE)
            artist = bootstrap_summary[
                (bootstrap_summary["scope"].eq(scope))
                & (bootstrap_summary["candidate"].eq(row.candidate))
                & (bootstrap_summary["bootstrap_mode"].eq("artist_bootstrap"))
            ]
            mdape_prob = float(artist.iloc[0]["delta_MdAPE_prob_improve"]) if not artist.empty else np.nan
            mape_prob = float(artist.iloc[0]["delta_MAPE_prob_improve"]) if not artist.empty else np.nan
            p95_prob = float(artist.iloc[0]["delta_p95_APE_prob_improve"]) if not artist.empty else np.nan
            if mdape_delta >= 0 and mape_delta >= 0 and p95_delta >= 0:
                decision = "대표 교체 후보"
            elif mdape_delta >= -0.01 and (mape_delta > 0 or p95_delta > 0):
                decision = "목적별 방어 후보"
            elif mdape_delta >= -0.02 and mape_delta > 0 and p95_delta > 0:
                decision = "추가 검증 후보"
            else:
                decision = "보류"
            rows.append({
                "scope": scope,
                "candidate": row.candidate,
                "split": "test",
                "decision": decision,
                "test_MdAPE": row.MdAPE,
                "test_MAPE": row.MAPE,
                "test_p95_APE": row.p95_APE,
                "delta_MdAPE_vs_baseline": mdape_delta,
                "delta_MAPE_vs_baseline": mape_delta,
                "delta_p95_APE_vs_baseline": p95_delta,
                "artist_bootstrap_MdAPE_prob": mdape_prob,
                "artist_bootstrap_MAPE_prob": mape_prob,
                "artist_bootstrap_p95_prob": p95_prob,
            })
    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "_No rows._"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        if pd.api.types.is_float_dtype(safe[col]):
            safe[col] = safe[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.6f}")
        else:
            safe[col] = safe[col].map(lambda value: "" if pd.isna(value) else str(value).replace("\n", " "))
    lines = [
        "| " + " | ".join(safe.columns) + " |",
        "| " + " | ".join(["---"] * len(safe.columns)) + " |",
    ]
    for values in safe.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines)


def render_report(
    warm_metrics: pd.DataFrame,
    warm_bootstrap: pd.DataFrame,
    warm_recommendations: pd.DataFrame,
    cold_metrics: pd.DataFrame,
    cold_selection: pd.DataFrame,
    cold_bootstrap: pd.DataFrame,
    cold_recommendations: pd.DataFrame,
    condition_map: pd.DataFrame,
) -> str:
    warm_view = warm_metrics[warm_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    warm_boot_view = warm_bootstrap[warm_bootstrap["bootstrap_mode"].eq("artist_bootstrap")].sort_values(
        ["delta_MAPE_prob_improve", "delta_p95_APE_prob_improve", "delta_MdAPE_prob_improve"],
        ascending=False,
    )
    cold_view = cold_metrics[cold_metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(20)
    cold_boot_view = cold_bootstrap[cold_bootstrap["bootstrap_mode"].eq("artist_bootstrap")].sort_values(
        ["delta_MAPE_prob_improve", "delta_p95_APE_prob_improve", "delta_MdAPE_prob_improve"],
        ascending=False,
    ).head(30)
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 모델 구조별 약점을 반영한 최신 보정 후보가 서비스 후보로 안정적인지 확인한다.",
        "- 원칙: validation에서 정책 후보를 고르고, test와 bootstrap은 선택 후 안정성 확인으로 사용한다.",
        "",
        "## 1. 실행 계획 요약",
        "",
        "- Warm: `PP-V6` 대표 후보를 기준으로 `PP-V8` 단순화 후보와 `PP-WMAPE` CatBoost residual 후보를 비교한다.",
        "- Cold: `PP-H23/H26` 검색 보정을 전체 적용하지 않고 `recommended_action`, `qwidth_bin` 조건으로 제한 적용해 비교한다.",
        "- 서비스 비교군 통계 피처는 누수 방지 설계가 필요하므로 이번 실행에서는 계획으로 분리하고, `PP-SVC1`로 후속 실행한다.",
        "",
        "## 2. Warm test 결과",
        "",
        markdown_table(warm_view[["candidate", "source_experiment", "use_case", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]], max_rows=20),
        "",
        "## 3. Warm artist bootstrap 안정성",
        "",
        markdown_table(warm_boot_view[[
            "candidate",
            "delta_MdAPE_median",
            "delta_MdAPE_prob_improve",
            "delta_MAPE_median",
            "delta_MAPE_prob_improve",
            "delta_p95_APE_median",
            "delta_p95_APE_prob_improve",
        ]], max_rows=20),
        "",
        "## 4. Warm 추천 판단",
        "",
        markdown_table(warm_recommendations.sort_values(["decision", "delta_MAPE_vs_baseline"], ascending=[True, False]), max_rows=20),
        "",
        "## 5. Cold 제한 조건",
        "",
        markdown_table(condition_map, max_rows=20),
        "",
        "## 6. Cold validation 선택 후보",
        "",
        markdown_table(cold_selection[[
            "objective",
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "test_MdAPE",
            "test_MAPE",
            "test_p95_APE",
        ]], max_rows=20),
        "",
        "## 7. Cold test 상위 결과",
        "",
        markdown_table(cold_view[["candidate", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]], max_rows=20),
        "",
        "## 8. Cold artist bootstrap 안정성",
        "",
        markdown_table(cold_boot_view[[
            "candidate",
            "delta_MdAPE_median",
            "delta_MdAPE_prob_improve",
            "delta_MAPE_median",
            "delta_MAPE_prob_improve",
            "delta_p95_APE_median",
            "delta_p95_APE_prob_improve",
        ]], max_rows=30),
        "",
        "## 9. Cold 추천 판단",
        "",
        markdown_table(cold_recommendations.sort_values(["decision", "delta_MAPE_vs_baseline"], ascending=[True, False]).head(30), max_rows=30),
        "",
        "## 10. 다음 실행",
        "",
        "- Warm `PP-WMAPE` residual 후보가 MdAPE를 악화시키고 MAPE/p95만 개선한다면 대표 후보가 아니라 방어 후보로 둔다.",
        "- Cold 검색 보정은 전체 적용보다 제한 적용이 안전한지 보고, 신뢰도/API 정책으로 연결한다.",
        "- 다음 신규 학습 축은 `PP-SVC1` 서비스 비교군 통계 피처다. train 기준 비교군 통계를 만들고 Warm/Cold 모델 입력과 API 표시값을 동시에 검증한다.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(
    warm_metrics: pd.DataFrame,
    warm_bootstrap_raw: pd.DataFrame,
    warm_bootstrap: pd.DataFrame,
    warm_recommendations: pd.DataFrame,
    cold_metrics: pd.DataFrame,
    cold_selection: pd.DataFrame,
    cold_bootstrap_raw: pd.DataFrame,
    cold_bootstrap: pd.DataFrame,
    cold_recommendations: pd.DataFrame,
    condition_map: pd.DataFrame,
) -> None:
    ensure_dirs()
    outputs = {
        "warm_metrics.csv": warm_metrics,
        "warm_bootstrap_samples.csv": warm_bootstrap_raw,
        "warm_bootstrap_summary.csv": warm_bootstrap,
        "warm_recommendations.csv": warm_recommendations,
        "cold_metrics.csv": cold_metrics,
        "cold_validation_selection.csv": cold_selection,
        "cold_bootstrap_samples.csv": cold_bootstrap_raw,
        "cold_bootstrap_summary.csv": cold_bootstrap,
        "cold_recommendations.csv": cold_recommendations,
        "cold_condition_map.csv": condition_map,
    }
    for filename, df in outputs.items():
        df.to_csv(EXP_DIR / "outputs" / filename, index=False)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "warm_baseline": WARM_BASE_LABEL,
        "cold_baseline": COLD_BASE_LABEL,
        "warm_candidates": WARM_CANDIDATES,
        "cold_source_path": str(COLD_SOURCE_PATH.relative_to(REPO)),
        "cold_source_candidates": COLD_SOURCE_CANDIDATES,
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (EXP_DIR / "data" / "source_files.json").write_text(json.dumps({
        "warm": [str(Path(cfg["path"]).relative_to(REPO)) for cfg in WARM_CANDIDATES],
        "cold": str(COLD_SOURCE_PATH.relative_to(REPO)),
        "agreement": str(COLD_AGREEMENT_PATH.relative_to(REPO)),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "model_manifest.json").write_text(json.dumps({
        "target": "ln_price_krw",
        "mode": "model_specific_custom_correction_followup",
        "note": "No new fitted model artifact. This experiment validates correction policies from existing predictions.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_report(
        warm_metrics,
        warm_bootstrap,
        warm_recommendations,
        cold_metrics,
        cold_selection,
        cold_bootstrap,
        cold_recommendations,
        condition_map,
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d8dee4;padding:7px;vertical-align:top}}th{{background:#eef2f7}}pre{{white-space:pre-wrap}}</style>
</head><body><pre>{html.escape(md)}</pre></body></html>"""
    for path in [
        EXP_DIR / "README.md",
        EXP_DIR / "reports" / "result_report.md",
        DOC_ROOT / "pp_i7_model_specific_custom_followup_summary.md",
    ]:
        path.write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")


def main() -> None:
    warm_long = load_warm_predictions()
    warm_metrics = long_metrics(warm_long, "warm")
    warm_wide = pivot_predictions(warm_long)
    warm_labels = sorted(warm_long["candidate_label"].unique())
    warm_bootstrap_raw = bootstrap_compare(warm_wide, warm_labels, WARM_BASE_LABEL, "warm")
    warm_bootstrap = summarize_bootstrap(warm_bootstrap_raw)
    warm_recommendations = add_recommendations(warm_metrics, warm_bootstrap, WARM_BASE_LABEL)

    cold_long, condition_map = load_cold_predictions()
    cold_metrics = long_metrics(cold_long, "cold")
    cold_selection = select_validation_candidates(cold_metrics, "cold", COLD_BASE_LABEL)
    cold_wide = pivot_predictions(cold_long)
    selected_cold = set(cold_selection["candidate"].astype(str)) if not cold_selection.empty else set()
    top_cold = set(
        cold_metrics[cold_metrics["split"].eq("validation")]
        .sort_values(["MAPE", "MdAPE", "p95_APE"])
        .head(12)["candidate"]
        .astype(str)
    )
    cold_labels = sorted((selected_cold | top_cold) - {COLD_BASE_LABEL})
    cold_bootstrap_raw = bootstrap_compare(cold_wide, [COLD_BASE_LABEL, *cold_labels], COLD_BASE_LABEL, "cold")
    cold_bootstrap = summarize_bootstrap(cold_bootstrap_raw)
    cold_recommendations = add_recommendations(
        cold_metrics[cold_metrics["candidate"].isin([COLD_BASE_LABEL, *cold_labels])].copy(),
        cold_bootstrap,
        COLD_BASE_LABEL,
    )

    write_outputs(
        warm_metrics,
        warm_bootstrap_raw,
        warm_bootstrap,
        warm_recommendations,
        cold_metrics,
        cold_selection,
        cold_bootstrap_raw,
        cold_bootstrap,
        cold_recommendations,
        condition_map,
    )
    print(json.dumps({
        "status": "completed",
        "experiment": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "doc": str((DOC_ROOT / "pp_i7_model_specific_custom_followup_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
