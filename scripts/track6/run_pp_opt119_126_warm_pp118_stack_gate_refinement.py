#!/usr/bin/env python3
"""Run PP-OPT119..126 Warm PP118 stack-gate refinement experiments.

PP118 found a materially better operating candidate by taking a confidence
weighted Huber stack only where the gain/harm/risk gate allowed it.  This batch
keeps that same learned Huber-stack prediction and refines the adoption gate,
movement cap, risk rollback, and p95-purpose routing without retraining the
expensive base stackers.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP96_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt96_102_warm_tail_label_refinement_experiments.py"
PP111_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt111_118_warm_next_dimension_experiments.py"
PP71_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt71_75_warm_pp70_stability_validation.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp96 = load_module("pp_opt96_helpers_for_pp119", PP96_SCRIPT)
pp111 = load_module("pp_opt111_helpers_for_pp119", PP111_SCRIPT)
val71 = load_module("pp_opt71_helpers_for_pp119", PP71_SCRIPT)
opt8 = pp96.opt8
opt9 = pp96.opt9
opt29 = pp96.opt29

EXP_ID = "PP-OPT119-126"
EXP_SLUG = "PP-OPT119_126_warm_pp118_stack_gate_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP111_DIR = REPO / "experiments" / "track6" / "PP-OPT111_118_warm_next_dimension_experiments"
PP111_PREDS = PP111_DIR / "outputs" / "candidate_predictions.csv"
PP111_CONFIG = PP111_DIR / "artifacts" / "run_config.json"
PP111_MODEL_DETAIL = PP111_DIR / "artifacts" / "next_dimension_model_prediction_detail.csv"
PP96_LABELS = REPO / "experiments" / "track6" / "PP-OPT96_102_warm_tail_label_refinement_experiments" / "artifacts" / "tail_label_probability_detail.csv"

BASE_CANDIDATE = pp96.BASE_CANDIDATE
INCUMBENT = pp96.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT119",
        "priority": "1",
        "title": "fine stack adoption gate",
        "description": "PP118의 Huber stack 채택 gate 주변에서 threshold, width, strength를 세분화한다.",
    },
    {
        "item_id": "PP-OPT120",
        "priority": "2",
        "title": "p95 guarded stack gate",
        "description": "risk, harm, stack gap이 큰 row에서는 Huber stack 이동량을 줄여 p95 악화를 방어한다.",
    },
    {
        "item_id": "PP-OPT121",
        "priority": "3",
        "title": "adaptive movement cap",
        "description": "Huber stack으로 이동하는 로그 이동량에 risk별 cap을 적용한다.",
    },
    {
        "item_id": "PP-OPT122",
        "priority": "4",
        "title": "segment strength schedule",
        "description": "신뢰도, 가격대, risk에 따라 stack 채택 강도를 다르게 적용한다.",
    },
    {
        "item_id": "PP-OPT123",
        "priority": "5",
        "title": "risk rollback from aggressive stack",
        "description": "MAPE가 강한 stack 후보를 쓰되 high-risk row는 PP118 또는 PP81로 되돌린다.",
    },
    {
        "item_id": "PP-OPT124",
        "priority": "6",
        "title": "p95 purpose limited router",
        "description": "XGBoost p95 성향 후보와 p95 meta-router를 MAPE guard 안에서만 제한 채택한다.",
    },
    {
        "item_id": "PP-OPT125",
        "priority": "7",
        "title": "stability selected stack challenger",
        "description": "고정 test와 반복 안정성 점수로 후보를 선별한다.",
    },
    {
        "item_id": "PP-OPT126",
        "priority": "8",
        "title": "final stack-gate decision",
        "description": "선택 후보를 운영형/p95형으로 복제하고 PP118, PP81/PP95와 비교한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return opt9.row_cap(base, cap, mode)


def qwidth_governor(base: pd.DataFrame, mode: str = "strict") -> np.ndarray:
    return opt9.qwidth_governor(base, mode)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source, ref, labels, selected_refs, _ = pp111.load_inputs()
    cfg111 = load_json(PP111_CONFIG)
    pp118 = pp96.load_predictions_from_file(
        base,
        PP111_PREDS,
        {
            "pp118_op": cfg111["selection_decision"]["operational_protocol_candidate"],
            "pp118_p95": cfg111["selection_decision"]["p95_protocol_candidate"],
            "pp111_p95_source": cfg111["selection_decision"]["p95_candidate"],
        },
    )
    ref = pd.concat([ref, pp118], axis=1)
    selected_refs = dict(selected_refs)
    selected_refs.update(
        {
            "pp118_op": cfg111["selection_decision"]["operational_protocol_candidate"],
            "pp118_p95": cfg111["selection_decision"]["p95_protocol_candidate"],
            "pp111_p95_source": cfg111["selection_decision"]["p95_candidate"],
        }
    )
    model_detail = base[["eval_split", "_track6_row_id"]].merge(
        pd.read_csv(PP111_MODEL_DETAIL), on=["eval_split", "_track6_row_id"], how="left"
    )
    if model_detail.filter(regex=r"^(stack|direct|residual)_").isna().any(axis=None):
        raise ValueError("Missing PP111 model prediction detail after merge")
    labels = base[["eval_split", "_track6_row_id"]].merge(pd.read_csv(PP96_LABELS), on=["eval_split", "_track6_row_id"], how="left")
    return base, source, ref, labels, model_detail, selected_refs, cfg111


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp110_operational", "pp110_op"),
        ("reference_pp118_operational", "pp118_op"),
        ("reference_pp118_p95", "pp118_p95"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


def build_scores(base: pd.DataFrame, ref: pd.DataFrame, labels: pd.DataFrame, model_detail: pd.DataFrame) -> dict[str, np.ndarray]:
    risk = val71.risk_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gain_any = labels["prob_best_gain_any"].to_numpy(dtype=float)
    gain75 = labels["prob_best_gain_tail75"].to_numpy(dtype=float)
    gain80 = labels["prob_best_gain_tail80"].to_numpy(dtype=float)
    gain85 = labels["prob_best_gain_tail85"].to_numpy(dtype=float)
    harm = np.clip(
        0.50 * labels["prob_best_harm"].to_numpy(dtype=float)
        + 0.18 * labels["prob_pp20_harm"].to_numpy(dtype=float)
        + 0.16 * labels["prob_pp48_harm"].to_numpy(dtype=float)
        + 0.16 * labels["prob_p95_weighted_harm"].to_numpy(dtype=float),
        0,
        1,
    )
    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    pp118 = ref["pp118_op"].to_numpy(dtype=float)
    pp81 = ref["pp81"].to_numpy(dtype=float)
    stack_gap = np.abs(stack - pp118)
    p95_risk = np.clip(
        0.36 * risk
        + 0.22 * gate(qwidth, 1.18, 0.92)
        + 0.15 * gate(spread, 0.12, 0.18)
        + 0.17 * harm
        + 0.10 * gate(stack_gap, 0.050, 0.100),
        0,
        1,
    )
    tail_intent = np.clip(0.52 * gain80 + 0.22 * gain85 + 0.16 * gate(qwidth, 1.20, 0.90) + 0.10 * risk, 0, 1)
    return {
        "risk": risk,
        "qwidth": qwidth,
        "spread": spread,
        "gain_any": gain_any,
        "gain75": gain75,
        "gain80": gain80,
        "gain85": gain85,
        "harm": harm,
        "stack": stack,
        "stack_gap": stack_gap,
        "p95_risk": p95_risk,
        "tail_intent": tail_intent,
        "pp118_delta_abs": np.abs(pp118 - pp81),
    }


def base_stack_score(scores: dict[str, np.ndarray], gain_key: str, hpen: float, rpen: float, gap_thr: float, gap_width: float) -> np.ndarray:
    gain = scores[gain_key]
    improvement = np.clip(gain - hpen * scores["harm"] - rpen * scores["risk"], 0, 1)
    gap_guard = 1.0 - gate(scores["stack_gap"], gap_thr, gap_width)
    return np.clip(improvement * gap_guard, 0, 1)


def pp_opt119_fine_gate(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    target = scores["stack"]
    policies = [
        ("balanced", "gain75", 0.70, 0.18, 0.055, 0.085),
        ("less_harm", "gain75", 0.55, 0.18, 0.055, 0.085),
        ("more_harm", "gain75", 0.85, 0.18, 0.055, 0.085),
        ("risk_light", "gain_any", 0.70, 0.10, 0.060, 0.090),
        ("risk_strict", "gain75", 0.70, 0.26, 0.050, 0.075),
        ("gap_wide", "gain75", 0.70, 0.18, 0.070, 0.110),
    ]
    for safe_key in ["pp81", "pp118_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for policy_name, gain_key, hpen, rpen, gap_thr, gap_width in policies:
            score = base_stack_score(scores, gain_key, hpen, rpen, gap_thr, gap_width)
            for threshold in [0.06, 0.08, 0.10, 0.12, 0.14, 0.16]:
                for width in [0.16, 0.20, 0.24, 0.30]:
                    w = gate(score, threshold, width)
                    for strength in [0.55, 0.65, 0.75, 0.85, 0.95]:
                        pred = safe + (target - safe) * w * strength
                        name = (
                            f"ppopt119_fine_gate__safe={safe_key}__policy={policy_name}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "fine_stack_adoption_gate", "PP-OPT119", pred))
    return rows


def pp_opt120_p95_guard(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    target = scores["stack"]
    p95_guard = np.maximum(scores["p95_risk"], gate(scores["stack_gap"], 0.06, 0.12))
    for safe_key in ["pp81", "pp118_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        score = base_stack_score(scores, "gain75", 0.70, 0.18, 0.055, 0.085)
        for threshold in [0.06, 0.10, 0.12, 0.16]:
            for guard_strength in [0.25, 0.40, 0.55, 0.70]:
                guarded = gate(score, threshold, 0.22) * np.clip(1.0 - guard_strength * p95_guard, 0, 1)
                for strength in [0.65, 0.80, 0.95, 1.10]:
                    pred = safe + (target - safe) * guarded * strength
                    name = (
                        f"ppopt120_p95_guard__safe={safe_key}__thr={safe_name(threshold)}"
                        f"__guard={safe_name(guard_strength)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "p95_guarded_stack_gate", "PP-OPT120", pred))
    return rows


def pp_opt121_adaptive_cap(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    target = scores["stack"]
    score = base_stack_score(scores, "gain75", 0.70, 0.18, 0.055, 0.085)
    for safe_key in ["pp81", "pp118_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        raw_delta = target - safe
        for threshold in [0.06, 0.10, 0.14]:
            w = gate(score, threshold, 0.22)
            for base_cap in [0.012, 0.018, 0.026, 0.038, 0.055]:
                for risk_shrink in [0.20, 0.35, 0.50, 0.70]:
                    cap = np.maximum(0.006, base_cap * (1.0 - risk_shrink * scores["p95_risk"]))
                    for strength in [0.55, 0.75, 0.95]:
                        pred = safe + np.clip(raw_delta * w * strength, -cap, cap)
                        name = (
                            f"ppopt121_adaptive_cap__safe={safe_key}__thr={safe_name(threshold)}"
                            f"__cap={safe_name(base_cap)}__rshrink={safe_name(risk_shrink)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "adaptive_stack_movement_cap", "PP-OPT121", pred))
    return rows


def segment_multiplier(base: pd.DataFrame, scores: dict[str, np.ndarray], policy: str) -> np.ndarray:
    conf = base["confidence_tier"].astype(str)
    price = base["stable_price_band"].astype(str)
    risk = scores["risk"]
    if policy == "confidence_push":
        mult = np.where(conf.eq("high_confidence"), 1.10, np.where(conf.eq("low_confidence"), 0.55, 0.82))
    elif policy == "risk_push":
        mult = np.where(risk < 0.35, 1.15, np.where(risk > 0.68, 0.42, 0.76))
    elif policy == "price_guard":
        mult = np.where(price.eq("very_high_price"), 0.45, np.where(price.eq("high_price"), 0.70, 1.00))
    elif policy == "balanced_guard":
        mult = np.where((risk < 0.40) & ~price.eq("very_high_price"), 1.05, np.where(risk > 0.65, 0.45, 0.75))
    else:
        mult = np.ones(len(base), dtype=float)
    return np.asarray(mult, dtype=float)


def pp_opt122_segment_strength(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    target = scores["stack"]
    score = base_stack_score(scores, "gain75", 0.70, 0.18, 0.055, 0.085)
    for safe_key in ["pp81", "pp118_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for policy in ["confidence_push", "risk_push", "price_guard", "balanced_guard"]:
            mult = segment_multiplier(base, scores, policy)
            for threshold in [0.06, 0.10, 0.12, 0.16]:
                w = gate(score, threshold, 0.22) * mult
                for strength in [0.55, 0.70, 0.85, 1.00]:
                    pred = safe + (target - safe) * w * strength
                    name = (
                        f"ppopt122_segment_strength__safe={safe_key}__policy={policy}"
                        f"__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "segment_strength_schedule", "PP-OPT122", pred))
    return rows


def pp_opt123_aggressive_rollback(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], model_detail: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    aggressive_targets = {
        "huber_weighted": model_detail["stack_huber_weighted"].to_numpy(dtype=float),
        "huber_plain": model_detail["stack_huber_plain"].to_numpy(dtype=float),
    }
    rollback_score = np.maximum(scores["p95_risk"], gate(scores["stack_gap"], 0.05, 0.10))
    for target_key, target in aggressive_targets.items():
        for safe_key in ["pp81", "pp118_op"]:
            safe = ref[safe_key].to_numpy(dtype=float)
            for cap in [0.018, 0.026, 0.038, 0.055]:
                moved = safe + np.clip(target - safe, -row_cap(base, cap, "risk"), row_cap(base, cap, "risk"))
                for rollback_strength in [0.25, 0.45, 0.65, 0.85]:
                    for keep_floor in [0.00, 0.15, 0.30]:
                        keep = np.maximum(keep_floor, 1.0 - rollback_strength * rollback_score)
                        pred = safe + (moved - safe) * keep
                        name = (
                            f"ppopt123_aggressive_rollback__target={target_key}__safe={safe_key}"
                            f"__cap={safe_name(cap)}__rollback={safe_name(rollback_strength)}__floor={safe_name(keep_floor)}"
                        )
                        rows.append(make_candidate(base, name, "risk_rollback_from_aggressive_stack", "PP-OPT123", pred))
    return rows


def pp_opt124_p95_limited(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], model_detail: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp118_op"].to_numpy(dtype=float)
    targets = {
        "xgb_direct": model_detail["direct_xgb_weighted"].to_numpy(dtype=float),
        "pp118_p95": ref["pp118_p95"].to_numpy(dtype=float),
        "pp82_p95": ref["pp82_p95"].to_numpy(dtype=float),
    }
    mape_guard = np.clip(1.0 - gate(scores["gain75"] - 0.65 * scores["harm"], 0.02, 0.22), 0, 1)
    tail_score = np.clip(scores["tail_intent"] * (1.0 - 0.45 * scores["harm"]), 0, 1)
    for target_key, target in targets.items():
        for threshold in [0.08, 0.14, 0.22, 0.32]:
            w = gate(tail_score, threshold, 0.26)
            for mape_penalty in [0.20, 0.35, 0.50]:
                guarded = w * np.clip(1.0 - mape_penalty * mape_guard, 0, 1)
                for strength in [0.10, 0.18, 0.28, 0.40]:
                    pred = safe + (target - safe) * guarded * strength
                    name = (
                        f"ppopt124_p95_limited__target={target_key}__thr={safe_name(threshold)}"
                        f"__mpen={safe_name(mape_penalty)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "p95_purpose_limited_router", "PP-OPT124", pred))
    return rows


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
                "incumbent_MAPE_improve_rate": best["incumbent_MAPE_improve_rate"],
                "incumbent_p95_not_worse_rate": best["incumbent_p95_not_worse_rate"],
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


def select_candidates_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> list[str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    pp64_mape = float(test[test["candidate"].eq("reference_pp64_current_best")]["MAPE"].iloc[0])
    pp64_p95 = float(test[test["candidate"].eq("reference_pp64_current_best")]["p95_APE"].iloc[0])
    new_pool = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].copy()
    new_pool["delta_vs_pp64_MAPE"] = new_pool["test_MAPE"] - pp64_mape
    new_pool["delta_vs_pp64_p95_APE"] = new_pool["test_p95_APE"] - pp64_p95
    balanced = new_pool[
        (new_pool["delta_vs_pp64_MAPE"] <= 0.00005)
        & (new_pool["delta_vs_pp64_p95_APE"] <= 0.00006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(24)
    best_mape = new_pool.sort_values(["test_MAPE", "test_p95_APE"]).head(24)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(24)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(24)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    references = [
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp110_operational",
        "reference_pp118_operational",
        "reference_pp118_p95",
        "reference_pp82_operational",
        "reference_pp82_p95",
        INCUMBENT,
        BASE_CANDIDATE,
    ]
    return references + [candidate for candidate in selected if candidate not in references]


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT: "incumbent_pp7",
        "reference_pp64_current_best": "pp64_current_best",
        "reference_pp70_refinement": "pp70_refinement_candidate",
        "reference_pp81_best": "pp81_stable_reference",
        "reference_pp95_operational": "pp95_operational_reference",
        "reference_pp110_operational": "pp110_operational_reference",
        "reference_pp118_operational": "pp118_operational_reference",
        "reference_pp118_p95": "pp118_p95_reference",
        "reference_pp82_operational": "pp82_operational_reference",
        "reference_pp82_p95": "pp82_p95_reference",
    }
    subset = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    for candidate in selected_candidates:
        if candidate not in label_map:
            label_map[candidate] = f"candidate_{safe_name(candidate)[:120]}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def attach_candidate_names(stability_aggregate: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    if "candidate" in stability_aggregate.columns:
        return stability_aggregate
    lookup = fixed[["candidate_label", "candidate"]].drop_duplicates("candidate_label")
    return stability_aggregate.merge(lookup, on="candidate_label", how="left")


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp110_operational_reference",
        "pp118_operational_reference",
        "pp118_p95_reference",
        "pp82_operational_reference",
        "pp82_p95_reference",
        "incumbent_pp7",
        "hcoef_stable_source",
    }
    pool = stability_aggregate[~stability_aggregate["candidate_label"].isin(refs)].copy()
    if pool.empty:
        raise ValueError("No new stability candidates available")
    pool["fixed_test_delta_vs_pp64_MAPE"] = pool["fixed_test_MAPE"] - float(pp64["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp64_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp64["fixed_test_p95_APE"])
    op_pool = pool[
        (pool["fixed_test_delta_vs_pp64_MAPE"] <= -0.00020)
        & (pool["fixed_test_delta_vs_pp64_p95_APE"] <= 0.00005)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.82)
    ].copy()
    if op_pool.empty:
        op_pool = pool.sort_values(["replacement_score", "fixed_test_MAPE"]).head(24).copy()
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00020)
        & (pool["fixed_test_p95_APE"] < float(pp64["fixed_test_p95_APE"]) - 0.00008)
    ].copy()
    if p95_pool.empty:
        p95_pool = pool[pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00035].copy()
    if p95_pool.empty:
        p95_pool = pool.copy()
    p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]
    return {
        "operational_label": str(operational["candidate_label"]),
        "operational_candidate": str(operational["candidate"]),
        "operational_fixed_test_MAPE": float(operational["fixed_test_MAPE"]),
        "operational_fixed_test_p95_APE": float(operational["fixed_test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["fixed_test_delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["fixed_test_delta_vs_pp64_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "stack_gate_refined_operational_selection"), ("p95", "stack_gate_refined_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt126_{key}_stack_gate_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT126"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


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


def render_reports(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    item_summary: pd.DataFrame,
    stability_aggregate: pd.DataFrame,
    stability_summary: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected_names = [
        "reference_pp64_current_best",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp118_operational",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected_names)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
    top_p95 = aggregate[
        (aggregate["item_id"].str.startswith("PP-OPT", na=False))
        & (aggregate["test_delta_vs_incumbent_MAPE"] < 0)
    ].sort_values(["test_p95_APE", "test_MAPE"])
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "p95_test_MAPE",
        "p95_test_p95_APE",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "candidate",
        "item_id",
        "family",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "recommendation_score_vs_incumbent",
    ]
    stab_cols = [
        "candidate_label",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_vs_pp64_MAPE",
        "fixed_test_delta_vs_pp64_p95_APE",
        "avg_delta_vs_pp64_MAPE",
        "avg_delta_vs_pp64_p95_APE",
        "avg_pp64_MAPE_win_rate",
        "avg_pp64_p95_win_rate",
        "replacement_score",
    ]
    scenario_cols = [
        "candidate_label",
        "eval_split",
        "scenario",
        "mean_delta_vs_pp64_MAPE",
        "mean_delta_vs_pp64_p95_APE",
        "pp64_MAPE_win_rate",
        "pp64_p95_win_rate",
        "pp64_all3_win_rate",
    ]
    focus_labels = [
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp118_operational_reference",
        "pp126_operational_stack_gate_challenger",
        "pp126_p95_stack_gate_challenger",
    ]
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(focus_labels)]
    verdict = (
        f"운영 후보 {decision['operational_label']} fixed test MAPE "
        f"{decision['operational_fixed_test_MAPE']:.6f}, p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP64 대비 MAPE {decision['operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp64_p95_APE']:+.6f}."
    )
    interpretation = (
        "PP118 이후의 개선은 Huber stack 자체가 아니라 stack 채택 gate의 세부 조건에서 나온다. "
        "p95를 크게 훼손하는 공격적 stack은 운영 후보에서 제외하고, 반복 안정성이 높은 gate 후보만 승격한다."
    )
    md = "\n".join(
        [
            "# PP-OPT119~126 Warm PP118 stack-gate refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP118 Huber stack 채택 gate를 p95 guard와 함께 세분화",
            f"- 결론: {verdict}",
            f"- 해석: {interpretation}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 30),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 60),
            "",
            "## p95 후보 상위",
            markdown_table(top_p95, result_cols, 40),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 80),
            "",
            "## 선택 후보 시나리오별 안정성",
            markdown_table(scenario_focus, scenario_cols, 80),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT119~126 Warm PP118 stack-gate refinement 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1280px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .warn {{ border-left: 4px solid #b45309; background: #fff7ed; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT119~126 Warm PP118 stack-gate refinement 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="warn">{html.escape(interpretation)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>안정성 검증 후보</strong>{stability_aggregate['candidate_label'].nunique()}개</div>
    <div class="panel"><strong>운영형 PP64 대비 MAPE</strong>{decision['operational_delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{decision['operational_delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 주요 후보 test 비교</h2>
  {table_html(selected_test, list(selected_test.columns), 30)}
  <h2>2. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 30)}
  <h2>3. 탐색 후보 상위</h2>
  {table_html(top_new, result_cols, 60)}
  <h2>4. p95 후보 상위</h2>
  {table_html(top_p95, result_cols, 40)}
  <h2>5. 선택 후보 반복 안정성</h2>
  {table_html(stability_aggregate, stab_cols, 80)}
  <h2>6. 선택 후보 시나리오별 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 80)}
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, labels, model_detail, selected_refs, parent_config = load_inputs()
    scores = build_scores(base, ref, labels, model_detail)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt119_fine_gate(base, ref, scores))
    candidates.extend(pp_opt120_p95_guard(base, ref, scores))
    candidates.extend(pp_opt121_adaptive_cap(base, ref, scores))
    candidates.extend(pp_opt122_segment_strength(base, ref, scores))
    candidates.extend(pp_opt123_aggressive_rollback(base, ref, scores, model_detail))
    candidates.extend(pp_opt124_p95_limited(base, ref, scores, model_detail))

    predictions = pd.concat([source] + reference_candidates(base, ref) + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected_for_stability = select_candidates_for_stability(metrics, aggregate)
    stability_predictions, label_map = label_for_stability(predictions, selected_for_stability)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = select_protocol_candidates(stability_aggregate)
    predictions, decision = add_protocol_rows(predictions, decision)

    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected_for_stability = select_candidates_for_stability(metrics, aggregate)
    selected_for_stability.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected_for_stability = list(dict.fromkeys(selected_for_stability))
    stability_predictions, label_map = label_for_stability(predictions, selected_for_stability)
    label_map[decision["operational_protocol_candidate"]] = "pp126_operational_stack_gate_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp126_p95_stack_gate_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "selected_references": selected_refs,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp111_config": str(PP111_CONFIG.relative_to(REPO)),
            "pp111_predictions": str(PP111_PREDS.relative_to(REPO)),
            "pp111_model_detail": str(PP111_MODEL_DETAIL.relative_to(REPO)),
            "pp96_label_probabilities": str(PP96_LABELS.relative_to(REPO)),
            "pp96_helper": str(PP96_SCRIPT.relative_to(REPO)),
            "pp111_helper": str(PP111_SCRIPT.relative_to(REPO)),
            "pp71_validation_helper": str(PP71_SCRIPT.relative_to(REPO)),
        },
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
    score_detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in scores.items():
        score_detail[key] = value
    score_detail.to_csv(ARTIFACT_DIR / "stack_gate_score_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "stack_gate_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "stack_gate_refinement_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            [
                "priority",
                "title",
                "tested_candidates",
                "test_MAPE",
                "test_p95_APE",
                "p95_test_MAPE",
                "p95_test_p95_APE",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability_aggregate[
            [
                "candidate_label",
                "fixed_test_MAPE",
                "fixed_test_p95_APE",
                "fixed_test_delta_vs_pp64_MAPE",
                "fixed_test_delta_vs_pp64_p95_APE",
                "avg_delta_vs_pp64_MAPE",
                "avg_delta_vs_pp64_p95_APE",
                "avg_pp64_MAPE_win_rate",
                "avg_pp64_p95_win_rate",
                "replacement_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
