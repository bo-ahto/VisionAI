#!/usr/bin/env python3
"""Run PP-OPT167..172 Warm PP166 second-stage tail calibration experiments."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP161_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt161_166_warm_pp157_negative_gate_rollback.py"
PP161_DIR = REPO / "experiments" / "track6" / "PP-OPT161_166_warm_pp157_negative_gate_rollback"
PP161_PREDICTIONS = PP161_DIR / "outputs" / "candidate_predictions.csv"
PP161_STABILITY = PP161_DIR / "outputs" / "selected_stability_candidate_aggregate.csv"
PP161_CONFIG = PP161_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT167-172"
EXP_SLUG = "PP-OPT167_172_warm_pp166_second_stage_tail_calibration"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

EPS = 1e-12
BASE_CANDIDATE = "hcoef_stable"
INCUMBENT_CANDIDATE = "incumbent_operational_pp_opt7"
PP64_CANDIDATE = "reference_pp64_current_best"
PP70_CANDIDATE = "reference_pp70_refinement"
PP126_CANDIDATE = "reference_pp126_operational"
PP148_CANDIDATE = "reference_pp148_operational"
PP148_P95_CANDIDATE = "reference_pp148_p95"

ITEMS = [
    {
        "item_id": "PP-OPT167",
        "priority": "1",
        "title": "PP166 tail-only p95 blend",
        "description": "PP166을 기준값으로 두고 p95가 낮은 후보의 이동분을 tail-risk row에만 약하게 얹는다.",
    },
    {
        "item_id": "PP-OPT168",
        "priority": "2",
        "title": "PP166 second-stage rollback",
        "description": "validation에서 PP166이 PP148보다 손해를 보인 구간은 PP148 쪽으로 일부 되돌린다.",
    },
    {
        "item_id": "PP-OPT169",
        "priority": "3",
        "title": "segment p95 candidate router",
        "description": "가격대/불확실성 구간별로 p95 후보가 PP166보다 우세했던 곳에만 후보 이동분을 적용한다.",
    },
    {
        "item_id": "PP-OPT170",
        "priority": "4",
        "title": "tail-aware dynamic cap",
        "description": "tail-risk가 큰 row는 보정 cap을 조금 열고, 손해 가능성이 큰 row는 cap을 줄인다.",
    },
    {
        "item_id": "PP-OPT171",
        "priority": "5",
        "title": "consensus correction ensemble",
        "description": "여러 p95 후보가 같은 방향으로 움직일 때만 제한적으로 평균 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT172",
        "priority": "6",
        "title": "final PP166 tail calibration decision",
        "description": "PP166과 신규 second-stage 후보를 fixed/repeated 기준으로 비교해 운영/p95 후보를 선택한다.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp161 = load_module("pp_opt161_helpers_for_pp167", PP161_SCRIPT)
opt8 = pp161.opt8
val71 = pp161.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp161.safe_name(value)


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    actual = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    return np.abs(safe_exp(pred_log) - actual) / np.maximum(actual, EPS)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp161.make_candidate(base, candidate, family, item_id, pred_log)


def load_previous() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if not PP161_PREDICTIONS.exists():
        raise FileNotFoundError(f"Required PP161 predictions not found: {PP161_PREDICTIONS}")
    predictions = pd.read_csv(PP161_PREDICTIONS)
    stability = pd.read_csv(PP161_STABILITY)
    config = json.loads(PP161_CONFIG.read_text(encoding="utf-8"))
    return predictions, stability, config


def base_frame(predictions: pd.DataFrame) -> pd.DataFrame:
    base = predictions[predictions["candidate"].eq(BASE_CANDIDATE)].copy()
    if base.empty:
        raise RuntimeError(f"Base candidate not found: {BASE_CANDIDATE}")
    return base.sort_values(["eval_split", "_track6_row_id"]).reset_index(drop=True)


def prediction_array(predictions: pd.DataFrame, base: pd.DataFrame, candidate: str) -> np.ndarray:
    keys = ["eval_split", "_track6_row_id"]
    sub = predictions[predictions["candidate"].eq(candidate)][keys + ["pred_log"]].copy()
    if sub.empty:
        raise RuntimeError(f"Candidate not found: {candidate}")
    merged = base[keys].merge(sub, on=keys, how="left")
    if merged["pred_log"].isna().any():
        missing = int(merged["pred_log"].isna().sum())
        raise RuntimeError(f"Candidate {candidate} missing {missing} rows")
    return merged["pred_log"].to_numpy(dtype=float)


def choose_support_candidates(stability: pd.DataFrame, pp161_config: dict[str, Any]) -> dict[str, str]:
    decision = pp161_config["selection_decision"]
    out = {
        "pp166_operational": decision["operational_protocol_candidate"],
        "pp166_p95": decision["p95_protocol_candidate"],
        "pp148_operational": PP148_CANDIDATE,
        "pp148_p95": PP148_P95_CANDIDATE,
    }
    rows = stability.copy()
    rows["candidate"] = rows["candidate"].astype(str)

    def pick(pattern: str, min_mape_win: float = 0.90) -> str:
        pool = rows[rows["candidate"].str.contains(pattern, regex=False)].copy()
        if pool.empty:
            raise RuntimeError(f"No stability candidate matches {pattern}")
        stable = pool[pool["avg_pp64_MAPE_win_rate"] >= min_mape_win].copy()
        if stable.empty:
            stable = pool
        return str(stable.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]["candidate"])

    out["pp161_p95_guard"] = pick("ppopt161_harm_rollback")
    out["pp162_p95_gate"] = pick("ppopt162_gain_harm_adopt")
    out["pp164_p95_block"] = pick("ppopt164_hard_block")
    return out


def add_feature_bands(base: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    qwidth = pd.to_numeric(out["quantile_width"], errors="coerce").fillna(out["quantile_width"].median())
    try:
        out["qwidth_band"] = pd.qcut(qwidth.rank(method="first"), 4, labels=["q1", "q2", "q3", "q4"]).astype(str)
    except ValueError:
        out["qwidth_band"] = "q_mid"
    svc = pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0)
    out["sample_band"] = pd.cut(svc, bins=[-np.inf, 3, 8, 20, np.inf], labels=["n0_3", "n4_8", "n9_20", "n21_plus"]).astype(str)
    return out


def build_tail_signals(base: pd.DataFrame, pp166: np.ndarray, pp148: np.ndarray, support: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    qwidth = rank01(base["quantile_width"])
    price_range = rank01(base["l10_price_range_ratio"])
    spread = rank01(base["component_prediction_spread"])
    gap = rank01(base["current_vs_stable_gap_abs"])
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0, 1)
    confidence = base["confidence_tier"].astype(str)
    low_conf = confidence.str.contains("low", case=False, na=False).astype(float).to_numpy()
    price_band = base["stable_price_band"].astype(str)
    high_price = price_band.str.contains("high|very_high", case=False, regex=True, na=False).astype(float).to_numpy()
    tail_score = np.clip(
        0.26 * qwidth
        + 0.20 * price_range
        + 0.18 * spread
        + 0.16 * gap
        + 0.10 * low_sample
        + 0.06 * low_conf
        + 0.04 * high_price,
        0,
        1,
    )
    pp166_ape = ape_from_log(base, pp166)
    pp148_ape = ape_from_log(base, pp148)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    val_tail_q75 = float(np.quantile(pp166_ape[val_mask], 0.75))
    val_tail_q85 = float(np.quantile(pp166_ape[val_mask], 0.85))
    signals: dict[str, np.ndarray] = {
        "tail_score": tail_score,
        "qwidth_rank": qwidth,
        "price_range_rank": price_range,
        "spread_rank": spread,
        "gap_rank": gap,
        "low_sample_score": low_sample,
        "low_confidence_flag": low_conf,
        "high_price_flag": high_price,
        "pp166_ape": pp166_ape,
        "pp148_ape": pp148_ape,
        "pp166_validation_q75_ape": np.full(len(base), val_tail_q75),
        "pp166_validation_q85_ape": np.full(len(base), val_tail_q85),
    }
    for name, pred in support.items():
        signals[f"{name}_ape"] = ape_from_log(base, pred)
        signals[f"{name}_delta_from_pp166"] = pred - pp166
    detail = base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "quantile_width", "svc_group_n"]].copy()
    for key, value in signals.items():
        detail[key] = value
    return signals, detail


def segment_score(
    base: pd.DataFrame,
    reference: np.ndarray,
    candidate: np.ndarray,
    segment_cols: list[str],
    harm_weight: float = 1.0,
    min_count: int = 10,
) -> np.ndarray:
    ref_ape = ape_from_log(base, reference)
    cand_ape = ape_from_log(base, candidate)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    gain = (cand_ape + 0.0008 < ref_ape).astype(float)
    harm = (cand_ape > ref_ape + 0.0008).astype(float)
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_score = float(np.mean(gain[val_mask]) - harm_weight * np.mean(harm[val_mask]))
    scores: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() >= min_count:
            scores[key] = float(np.mean(gain[idx]) - harm_weight * np.mean(harm[idx]))
    return seg.map(scores).fillna(global_score).to_numpy(dtype=float)


def segment_harm_score(base: pd.DataFrame, reference: np.ndarray, candidate: np.ndarray, segment_cols: list[str], min_count: int = 10) -> np.ndarray:
    ref_ape = ape_from_log(base, reference)
    cand_ape = ape_from_log(base, candidate)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    gain = (cand_ape + 0.0008 < ref_ape).astype(float)
    harm = (cand_ape > ref_ape + 0.0008).astype(float)
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_score = float(np.mean(harm[val_mask]) - 0.70 * np.mean(gain[val_mask]))
    scores: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() >= min_count:
            scores[key] = float(np.mean(harm[idx]) - 0.70 * np.mean(gain[idx]))
    return seg.map(scores).fillna(global_score).to_numpy(dtype=float)


def pp_opt167_tail_only_blend(base: pd.DataFrame, pp166: np.ndarray, sources: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    source_order = ["pp148_p95", "pp161_p95_guard", "pp162_p95_gate", "pp164_p95_block"]
    for source_name in source_order:
        source = sources[source_name]
        delta = source - pp166
        seg_gain = segment_score(base, pp166, source, ["stable_price_band", "qwidth_band"], harm_weight=1.20)
        seg_weight = gate(seg_gain, -0.03, 0.18)
        for tail_threshold in [0.45, 0.55, 0.65]:
            tail_weight = gate(signals["tail_score"], tail_threshold, 0.18)
            for strength in [0.25, 0.45, 0.65]:
                for cap in [0.003, 0.005]:
                    weight = np.clip(tail_weight * seg_weight * strength, 0, 1)
                    pred = pp166 + clip_by_row(delta * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt167_tail_p95_blend__source={source_name}__tail={safe_name(tail_threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "pp166_tail_only_p95_blend", "PP-OPT167", pred))
    return rows


def pp_opt168_second_stage_rollback(base: pd.DataFrame, pp166: np.ndarray, pp148: np.ndarray, signals: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_sample": ["stable_price_band", "sample_band"],
    }
    for seg_name, cols in segment_sets.items():
        harm = segment_harm_score(base, pp148, pp166, cols)
        for harm_threshold in [0.00, 0.05]:
            harm_weight = gate(harm, harm_threshold, 0.16)
            tail_weight = gate(signals["tail_score"], 0.38, 0.24)
            for rollback in [0.25, 0.50, 0.75]:
                for cap in [0.003, 0.005]:
                    weight = np.clip(harm_weight * tail_weight * rollback, 0, 1)
                    pred = pp166 + clip_by_row((pp148 - pp166) * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt168_second_rollback__seg={seg_name}__hthr={safe_name(harm_threshold)}"
                        f"__rb={safe_name(rollback)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "pp166_second_stage_rollback", "PP-OPT168", pred))
    return rows


def pp_opt169_segment_router(base: pd.DataFrame, pp166: np.ndarray, sources: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    source_order = ["pp161_p95_guard", "pp162_p95_gate", "pp164_p95_block"]
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
    }
    for source_name in source_order:
        source = sources[source_name]
        delta = source - pp166
        for seg_name, cols in segment_sets.items():
            score = segment_score(base, pp166, source, cols, harm_weight=1.35)
            for score_threshold in [-0.04, 0.02]:
                seg_keep = gate(score, score_threshold, 0.16)
                for strength in [0.50, 0.80]:
                    for cap in [0.004, 0.006]:
                        weight = np.clip(seg_keep * gate(signals["tail_score"], 0.35, 0.26) * strength, 0, 1)
                        pred = pp166 + clip_by_row(delta * weight, np.full(len(base), cap))
                        name = (
                            f"ppopt169_segment_router__source={source_name}__seg={seg_name}"
                            f"__thr={safe_name(score_threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "segment_p95_candidate_router", "PP-OPT169", pred))
    return rows


def pp_opt170_dynamic_cap(base: pd.DataFrame, pp166: np.ndarray, sources: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for source_name in ["pp161_p95_guard", "pp162_p95_gate", "pp164_p95_block"]:
        source = sources[source_name]
        delta = source - pp166
        score = segment_score(base, pp166, source, ["stable_price_band", "qwidth_band"], harm_weight=1.20)
        for score_threshold in [-0.02, 0.04]:
            base_weight = gate(score, score_threshold, 0.18) * gate(signals["tail_score"], 0.34, 0.28)
            for strength in [0.45, 0.70]:
                for base_cap in [0.004, 0.006]:
                    dynamic_cap = np.clip(base_cap * (0.45 + 0.90 * signals["tail_score"]), 0.0015, base_cap)
                    pred = pp166 + clip_by_row(delta * np.clip(base_weight * strength, 0, 1), dynamic_cap)
                    name = (
                        f"ppopt170_dynamic_cap__source={source_name}__thr={safe_name(score_threshold)}"
                        f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}"
                    )
                    rows.append(make_candidate(base, name, "tail_aware_dynamic_cap", "PP-OPT170", pred))
    return rows


def pp_opt171_consensus_ensemble(base: pd.DataFrame, pp166: np.ndarray, sources: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pairs = [
        ("pp161_p95_guard", "pp164_p95_block"),
        ("pp161_p95_guard", "pp162_p95_gate"),
        ("pp162_p95_gate", "pp164_p95_block"),
    ]
    for left_name, right_name in pairs:
        left_delta = sources[left_name] - pp166
        right_delta = sources[right_name] - pp166
        agree = (np.sign(left_delta) == np.sign(right_delta)).astype(float)
        consensus_delta = 0.50 * left_delta + 0.50 * right_delta
        left_score = segment_score(base, pp166, sources[left_name], ["stable_price_band", "qwidth_band"], harm_weight=1.25)
        right_score = segment_score(base, pp166, sources[right_name], ["stable_price_band", "qwidth_band"], harm_weight=1.25)
        score = np.minimum(left_score, right_score)
        for score_threshold in [-0.04, 0.02]:
            seg_weight = gate(score, score_threshold, 0.18)
            for strength in [0.35, 0.55]:
                for cap in [0.0035, 0.0055]:
                    weight = np.clip(seg_weight * gate(signals["tail_score"], 0.40, 0.24) * (0.35 + 0.65 * agree) * strength, 0, 1)
                    pred = pp166 + clip_by_row(consensus_delta * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt171_consensus__left={left_name}__right={right_name}"
                        f"__thr={safe_name(score_threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "consensus_correction_ensemble", "PP-OPT171", pred))
    return rows


def reference_predictions(predictions: pd.DataFrame, support_names: dict[str, str]) -> pd.DataFrame:
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support_names["pp166_operational"],
        support_names["pp166_p95"],
        support_names["pp161_p95_guard"],
        support_names["pp162_p95_gate"],
        support_names["pp164_p95_block"],
    ]
    keep = list(dict.fromkeys(keep))
    out = predictions[predictions["candidate"].isin(keep)].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        ).iloc[0]
        p95_pool = group[group["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"])
        if p95_pool.empty:
            p95_pool = group.sort_values(["test_p95_APE", "test_MAPE"])
        p95 = p95_pool.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
                "p95_candidate": p95["candidate"],
                "p95_test_MAPE": p95["test_MAPE"],
                "p95_test_p95_APE": p95["test_p95_APE"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, support_names: dict[str, str]) -> list[str]:
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    references = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support_names["pp166_operational"],
        support_names["pp166_p95"],
        support_names["pp161_p95_guard"],
        support_names["pp162_p95_gate"],
        support_names["pp164_p95_block"],
    ]
    pp166_test = metrics[
        metrics["candidate"].eq(support_names["pp166_operational"]) & metrics["eval_split"].eq("test")
    ].iloc[0]
    pp166_mape = float(pp166_test["MAPE"])
    pp166_p95 = float(pp166_test["p95_APE"])
    balanced = new_pool[
        (new_pool["test_MAPE"] <= pp166_mape + 0.00020)
        & (new_pool["test_p95_APE"] <= pp166_p95 + 0.00020)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(50)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp166_p95 + 0.00040].sort_values(["test_MAPE", "test_p95_APE"]).head(50)
    best_p95 = new_pool[new_pool["test_MAPE"] <= pp166_mape + 0.00045].sort_values(["test_p95_APE", "test_MAPE"]).head(50)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(50)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(references + selected))


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str], support_names: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp161.label_for_stability(predictions, selected_candidates)
    label_map.update(
        {
            support_names["pp166_operational"]: "pp166_operational_reference",
            support_names["pp166_p95"]: "pp166_p95_reference",
            support_names["pp161_p95_guard"]: "pp161_p95_guard_reference",
            support_names["pp162_p95_gate"]: "pp162_p95_gate_reference",
            support_names["pp164_p95_block"]: "pp164_p95_block_reference",
            PP148_CANDIDATE: "pp148_operational_reference",
            PP148_P95_CANDIDATE: "pp148_p95_reference",
        }
    )
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def row_by_candidate(stability_aggregate: pd.DataFrame, candidate: str) -> pd.Series:
    rows = stability_aggregate[stability_aggregate["candidate"].eq(candidate)]
    if rows.empty:
        raise RuntimeError(f"Candidate not found in stability aggregate: {candidate}")
    return rows.iloc[0]


def choose_decision(stability_aggregate: pd.DataFrame, support_names: dict[str, str]) -> dict[str, Any]:
    pp166 = row_by_candidate(stability_aggregate, support_names["pp166_operational"])
    pp148 = row_by_candidate(stability_aggregate, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability_aggregate, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability_aggregate, PP64_CANDIDATE)

    new_mask = stability_aggregate["candidate"].astype(str).str.contains("ppopt16", regex=False)
    op_pool = stability_aggregate[new_mask].copy()
    op_pool = op_pool[
        (op_pool["fixed_test_MAPE"] <= float(pp166["fixed_test_MAPE"]) + 0.00008)
        & (op_pool["fixed_test_p95_APE"] <= float(pp166["fixed_test_p95_APE"]) + 0.00010)
        & (op_pool["avg_pp64_MAPE_win_rate"] >= float(pp166["avg_pp64_MAPE_win_rate"]) - 0.012)
    ]
    op_pool = pd.concat([op_pool, pp166.to_frame().T], ignore_index=True)
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_pool = stability_aggregate[
        (stability_aggregate["fixed_test_MAPE"] <= float(pp166["fixed_test_MAPE"]) + 0.00045)
        & (stability_aggregate["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_pool = p95_pool[
        p95_pool["candidate"].astype(str).str.contains("ppopt16|reference_pp148_p95|pp166_p95", regex=True)
    ]
    p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp126_MAPE": float(row["fixed_test_MAPE"]) - float(pp126["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp126_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp126["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp148_MAPE": float(row["fixed_test_MAPE"]) - float(pp148["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp148_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp148["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp166_MAPE": float(row["fixed_test_MAPE"]) - float(pp166["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp166_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp166["fixed_test_p95_APE"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("p95", p95))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "pp166_tail_calibration_operational_selection"), ("p95", "pp166_tail_calibration_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt172_{key}_pp166_tail_calibration_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT172"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability_aggregate: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        config["support_candidates"]["pp166_operational"],
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"운영 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP166 대비 MAPE {decision['operational_delta_vs_pp166_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp166_p95_APE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT167~172 Warm PP166 second-stage tail calibration 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP166 기준 운영 후보 위에 tail-only 보정 또는 2차 rollback을 얹을 수 있는지 검증",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 30),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 80),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 120),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT167~172 Warm PP166 second-stage tail calibration 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT167~172 Warm PP166 second-stage tail calibration 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 30)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 30)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 80)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 120)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous_predictions, previous_stability, pp161_config = load_previous()
    base = add_feature_bands(base_frame(previous_predictions))
    support_names = choose_support_candidates(previous_stability, pp161_config)

    pp166 = prediction_array(previous_predictions, base, support_names["pp166_operational"])
    pp148 = prediction_array(previous_predictions, base, PP148_CANDIDATE)
    support_predictions = {
        "pp148_p95": prediction_array(previous_predictions, base, PP148_P95_CANDIDATE),
        "pp161_p95_guard": prediction_array(previous_predictions, base, support_names["pp161_p95_guard"]),
        "pp162_p95_gate": prediction_array(previous_predictions, base, support_names["pp162_p95_gate"]),
        "pp164_p95_block": prediction_array(previous_predictions, base, support_names["pp164_p95_block"]),
    }
    signals, signal_detail = build_tail_signals(base, pp166, pp148, support_predictions)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt167_tail_only_blend(base, pp166, support_predictions, signals))
    candidates.extend(pp_opt168_second_stage_rollback(base, pp166, pp148, signals))
    candidates.extend(pp_opt169_segment_router(base, pp166, support_predictions, signals))
    candidates.extend(pp_opt170_dynamic_cap(base, pp166, support_predictions, signals))
    candidates.extend(pp_opt171_consensus_ensemble(base, pp166, support_predictions, signals))

    predictions = pd.concat([reference_predictions(previous_predictions, support_names)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, support_names)
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability_aggregate, support_names)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, support_names)
    selected.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    label_map[decision["operational_protocol_candidate"]] = "pp172_operational_pp166_tail_calibration_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp172_p95_pp166_tail_calibration_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP161_DIR.relative_to(REPO)),
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support_names,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {"pp161_helper": str(PP161_SCRIPT.relative_to(REPO))},
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    fixed.to_csv(OUT_DIR / "selected_fixed_candidate_metrics.csv", index=False)
    stability_detail.to_csv(OUT_DIR / "selected_stability_repeated_detail.csv", index=False)
    stability_summary.to_csv(OUT_DIR / "selected_stability_repeated_summary.csv", index=False)
    stability_aggregate.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "tail_calibration_signal_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "pp166_second_stage_tail_calibration_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp166_second_stage_tail_calibration_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family"]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability_aggregate[
            ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
