#!/usr/bin/env python3
"""Run PP-OPT229..234 Warm PP228 p95-win recovery without MAPE loss experiments."""
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
PP223_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt223_228_warm_pp222_narrow_balance_refinement.py"
PP223_DIR = REPO / "experiments" / "track6" / "PP-OPT223_228_warm_pp222_narrow_balance_refinement"
PP223_PREDICTIONS = PP223_DIR / "outputs" / "candidate_predictions.csv"
PP223_CONFIG = PP223_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT229-234"
EXP_SLUG = "PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = "hcoef_stable"
INCUMBENT_CANDIDATE = "incumbent_operational_pp_opt7"
PP64_CANDIDATE = "reference_pp64_current_best"
PP70_CANDIDATE = "reference_pp70_refinement"
PP126_CANDIDATE = "reference_pp126_operational"
PP148_CANDIDATE = "reference_pp148_operational"
PP148_P95_CANDIDATE = "reference_pp148_p95"

ITEMS = [
    {
        "item_id": "PP-OPT229",
        "priority": "1",
        "title": "PP228 balanced to aggressive gated lift",
        "description": "PP228 균형 후보에서 공격형 후보로 이동하되, validation 구간 신호와 row risk cap으로 제한.",
    },
    {
        "item_id": "PP-OPT230",
        "priority": "2",
        "title": "PP228 balanced to MAPE challenger tiny lift",
        "description": "MAPE 최저 후보 방향의 이동을 더 작은 cap으로만 허용.",
    },
    {
        "item_id": "PP-OPT231",
        "priority": "3",
        "title": "p95 recovery support",
        "description": "PP216 p95-recovery와 PP222 p95-guarded 후보 쪽 이동을 p95 회복 신호가 있는 row에만 적용.",
    },
    {
        "item_id": "PP-OPT232",
        "priority": "4",
        "title": "aggressive lift plus p95 recovery offset",
        "description": "공격형 이동 후 p95 회복 이동을 같이 넣어 MAPE 개선과 p95 win rate 회복의 균형을 탐색.",
    },
    {
        "item_id": "PP-OPT233",
        "priority": "5",
        "title": "row-level conservative router",
        "description": "row별로 균형, 공격형, p95 회복 후보 중 이동 방향을 선택.",
    },
    {
        "item_id": "PP-OPT234",
        "priority": "6",
        "title": "final PP228 p95 recovery decision",
        "description": "PP228 균형 후보 대비 MAPE 손상 없이 p95 win rate 또는 replacement score가 개선되는지 최종 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp223 = load_module("pp_opt223_helpers_for_pp229", PP223_SCRIPT)
pp217 = pp223.pp217
pp211 = pp223.pp211
pp199 = pp223.pp199
pp187 = pp223.pp187
pp161 = pp223.pp161
opt8 = pp223.opt8
val71 = pp223.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp223.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp223.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp223.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp223.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    return pd.read_csv(PP223_PREDICTIONS), json.loads(PP223_CONFIG.read_text(encoding="utf-8"))


def reference_predictions(previous: pd.DataFrame, support: dict[str, Any], decision: dict[str, Any]) -> pd.DataFrame:
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp180_operational"],
        support["pp186_operational"],
        support["pp192_operational"],
        support["pp198_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_operational"],
        support["pp222_balanced"],
        support["pp222_p95_guarded"],
        decision["balanced_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def candidate_from_move(
    base: pd.DataFrame,
    source: np.ndarray,
    target: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray,
    cap: float | np.ndarray,
) -> pd.DataFrame:
    caps = np.full(len(base), cap) if isinstance(cap, (float, int)) else np.asarray(cap, dtype=float)
    pred = source + clip_by_row((target - source) * weight, caps)
    return make_candidate(base, name, family, item_id, pred)


def candidate_from_two_moves(
    base: pd.DataFrame,
    source: np.ndarray,
    target_a: np.ndarray,
    target_b: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight_a: np.ndarray,
    cap_a: float | np.ndarray,
    weight_b: np.ndarray,
    cap_b: float | np.ndarray,
) -> pd.DataFrame:
    caps_a = np.full(len(base), cap_a) if isinstance(cap_a, (float, int)) else np.asarray(cap_a, dtype=float)
    caps_b = np.full(len(base), cap_b) if isinstance(cap_b, (float, int)) else np.asarray(cap_b, dtype=float)
    move_a = clip_by_row((target_a - source) * weight_a, caps_a)
    move_b = clip_by_row((target_b - source) * weight_b, caps_b)
    return make_candidate(base, name, family, item_id, source + move_a + move_b)


def segment_gate(
    base: pd.DataFrame,
    source: np.ndarray,
    target: np.ndarray,
    columns: list[str],
    score_threshold: float,
    score_width: float,
    p95_threshold: float,
    p95_width: float,
    mean_threshold: float,
    mean_width: float,
    min_count: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    score, p95_gain, mean_gain, count = pp211.recovery_signal(base, source, target, columns)
    count_guard = np.where(count > 0, gate(count, min_count, min_count), 1.0)
    weight = (
        gate(score, score_threshold, score_width)
        * gate(p95_gain, p95_threshold, p95_width)
        * gate(mean_gain, mean_threshold, mean_width)
        * count_guard
    )
    return weight, score, p95_gain, mean_gain, count


def risk_cap(basecap: float, shrink: float, curve: float, risk: np.ndarray, floor: float) -> np.ndarray:
    shaped = np.power(np.clip(risk, 0, 1), curve)
    return np.clip(basecap * (1.0 - shrink * shaped), floor, basecap)


def pp_opt229_aggressive_gated_lift(base: pd.DataFrame, balanced: np.ndarray, aggressive: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, balanced, aggressive)
    segment_sets = [
        ("price_conf", ["stable_price_band", "confidence_tier"]),
        ("price_conf_qwidth", ["stable_price_band", "confidence_tier", "qwidth_band"]),
        ("price_medium", ["stable_price_band", "medium_support_bucket"]),
    ]
    for seg_name, cols in segment_sets:
        signal, _score, _p95_gain, _mean_gain, _count = segment_gate(
            base,
            balanced,
            aggressive,
            cols,
            score_threshold=0.0,
            score_width=0.18,
            p95_threshold=-0.00003,
            p95_width=0.00012,
            mean_threshold=-0.00006,
            mean_width=0.00020,
            min_count=8.0,
        )
        for strength in [0.30, 0.45, 0.60, 0.75]:
            for basecap in [0.00018, 0.00028, 0.00042, 0.00060]:
                for shrink in [0.55, 0.75, 0.90]:
                    for curve in [0.75, 1.00, 1.25]:
                        cap = risk_cap(basecap, shrink, curve, risk, floor=0.00004)
                        name = (
                            f"ppopt229_aggressive_gated_lift__seg={seg_name}__s={safe_name(strength)}"
                            f"__basecap={safe_name(basecap)}__shrink={safe_name(shrink)}__curve={safe_name(curve)}"
                        )
                        rows.append(candidate_from_move(base, balanced, aggressive, name, "pp228_aggressive_gated_lift", "PP-OPT229", signal * strength, cap))
    return rows


def pp_opt230_mape_tiny_lift(base: pd.DataFrame, balanced: np.ndarray, mape: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, balanced, mape)
    signal, _score, _p95_gain, _mean_gain, _count = segment_gate(
        base,
        balanced,
        mape,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.14,
        p95_threshold=0.0,
        p95_width=0.00008,
        mean_threshold=-0.00003,
        mean_width=0.00016,
        min_count=10.0,
    )
    for strength in [0.12, 0.20, 0.30, 0.42, 0.55]:
        for basecap in [0.00008, 0.00014, 0.00022, 0.00034]:
            for shrink in [0.75, 0.90, 1.00]:
                cap = risk_cap(basecap, shrink, 1.0, risk, floor=0.000025)
                name = f"ppopt230_mape_tiny_lift__s={safe_name(strength)}__basecap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                rows.append(candidate_from_move(base, balanced, mape, name, "pp228_mape_tiny_lift", "PP-OPT230", signal * strength, cap))
    return rows


def pp_opt231_p95_recovery_support(
    base: pd.DataFrame,
    balanced: np.ndarray,
    p95_guarded: np.ndarray,
    p95_recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for target_name, target in [("guarded", p95_guarded), ("recovery", p95_recovery)]:
        signal, _score, _p95_gain, _mean_gain, _count = segment_gate(
            base,
            balanced,
            target,
            ["stable_price_band", "confidence_tier"],
            score_threshold=0.0,
            score_width=0.22,
            p95_threshold=-0.00004,
            p95_width=0.00018,
            mean_threshold=-0.00010,
            mean_width=0.00030,
            min_count=8.0,
        )
        risk = pp199.row_risk(base, balanced, target)
        for strength in [0.08, 0.14, 0.22, 0.34, 0.50]:
            for basecap in [0.00008, 0.00014, 0.00022, 0.00034]:
                for shrink in [0.50, 0.75, 0.90]:
                    cap = risk_cap(basecap, shrink, 1.0, risk, floor=0.000025)
                    name = (
                        f"ppopt231_p95_recovery_support__target={target_name}__s={safe_name(strength)}"
                        f"__basecap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(candidate_from_move(base, balanced, target, name, "pp228_p95_recovery_support", "PP-OPT231", signal * strength, cap))
    return rows


def pp_opt232_dual_offset(
    base: pd.DataFrame,
    balanced: np.ndarray,
    aggressive: np.ndarray,
    p95_guarded: np.ndarray,
    p95_recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    aggressive_signal, _a_score, _a_p95, _a_mean, _a_count = segment_gate(
        base,
        balanced,
        aggressive,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.18,
        p95_threshold=-0.00003,
        p95_width=0.00012,
        mean_threshold=-0.00006,
        mean_width=0.00020,
        min_count=8.0,
    )
    for target_name, target in [("guarded", p95_guarded), ("recovery", p95_recovery)]:
        recovery_signal, _r_score, _r_p95, _r_mean, _r_count = segment_gate(
            base,
            balanced,
            target,
            ["stable_price_band", "confidence_tier"],
            score_threshold=0.0,
            score_width=0.22,
            p95_threshold=-0.00003,
            p95_width=0.00018,
            mean_threshold=-0.00010,
            mean_width=0.00030,
            min_count=8.0,
        )
        for aggressive_strength in [0.20, 0.35, 0.50]:
            for recovery_strength in [0.08, 0.16, 0.28]:
                for aggressive_cap in [0.00012, 0.00022, 0.00034]:
                    for recovery_cap in [0.00006, 0.00012, 0.00020]:
                        name = (
                            f"ppopt232_dual_offset__target={target_name}__as={safe_name(aggressive_strength)}"
                            f"__rs={safe_name(recovery_strength)}__acap={safe_name(aggressive_cap)}__rcap={safe_name(recovery_cap)}"
                        )
                        rows.append(
                            candidate_from_two_moves(
                                base,
                                balanced,
                                aggressive,
                                target,
                                name,
                                "pp228_aggressive_plus_p95_recovery_offset",
                                "PP-OPT232",
                                aggressive_signal * aggressive_strength,
                                aggressive_cap,
                                recovery_signal * recovery_strength,
                                recovery_cap,
                            )
                        )
    return rows


def pp_opt233_conservative_router(
    base: pd.DataFrame,
    balanced: np.ndarray,
    aggressive: np.ndarray,
    p95_guarded: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    aggressive_signal, _a_score, a_p95, a_mean, _a_count = segment_gate(
        base,
        balanced,
        aggressive,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.18,
        p95_threshold=-0.00003,
        p95_width=0.00012,
        mean_threshold=-0.00006,
        mean_width=0.00020,
        min_count=8.0,
    )
    guarded_signal, _g_score, g_p95, _g_mean, _g_count = segment_gate(
        base,
        balanced,
        p95_guarded,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.22,
        p95_threshold=-0.00004,
        p95_width=0.00018,
        mean_threshold=-0.00010,
        mean_width=0.00030,
        min_count=8.0,
    )
    risk = pp199.row_risk(base, balanced, aggressive)
    for aggressive_threshold in [0.20, 0.32, 0.44]:
        for guarded_threshold in [0.18, 0.30, 0.42]:
            for cap in [0.00010, 0.00018, 0.00028, 0.00042]:
                use_aggressive = (aggressive_signal >= aggressive_threshold) & (a_p95 >= -0.00004) & (a_mean >= -0.00008)
                use_guarded = (~use_aggressive) & (guarded_signal >= guarded_threshold) & ((g_p95 >= -0.00003) | (risk >= 0.55))
                target = np.where(use_aggressive, aggressive, np.where(use_guarded, p95_guarded, balanced))
                weight = np.where(use_aggressive | use_guarded, 1.0, 0.0)
                row_cap = np.where(use_guarded, cap * 0.60, cap)
                name = (
                    f"ppopt233_conservative_router__athr={safe_name(aggressive_threshold)}"
                    f"__gthr={safe_name(guarded_threshold)}__cap={safe_name(cap)}"
                )
                rows.append(candidate_from_move(base, balanced, target, name, "pp228_row_level_conservative_router", "PP-OPT233", weight, row_cap))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(
            ["test_MAPE", "recommendation_score_vs_incumbent", "test_p95_APE"],
            ascending=[True, True, True],
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


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, decision: dict[str, Any], support: dict[str, Any]) -> list[str]:
    refs = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp192_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_balanced"],
        support["pp222_operational"],
        support["pp222_p95_guarded"],
        decision["balanced_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
    ]
    base_row = metrics[metrics["candidate"].eq(decision["balanced_protocol_candidate"]) & metrics["eval_split"].eq("test")].iloc[0]
    base_mape = float(base_row["MAPE"])
    base_p95 = float(base_row["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= base_mape + 0.000004)
        & (new_pool["test_p95_APE"] <= base_p95 + 0.000004)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(160)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= base_p95 + 0.000004].sort_values(["test_MAPE", "test_p95_APE"]).head(140)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(140)
    selected = pd.concat([op_pool, mape_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(refs + selected))


def label_for_stability(predictions: pd.DataFrame, selected: list[str], support: dict[str, Any], prior_decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset = predictions[predictions["candidate"].isin(selected)].copy()
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT_CANDIDATE: "incumbent_pp7",
        "current_70_30": "current_70_30",
        PP64_CANDIDATE: "pp64_current_best",
        PP70_CANDIDATE: "pp70_refinement_candidate",
        PP126_CANDIDATE: "pp126_operational_reference",
        PP148_CANDIDATE: "pp148_operational_reference",
        PP148_P95_CANDIDATE: "pp148_p95_reference",
        support["pp192_operational"]: "pp192_operational_reference",
        support["pp204_operational"]: "pp204_operational_reference",
        support["pp210_operational"]: "pp210_operational_reference",
        support["pp216_p95_recovery"]: "pp216_p95_recovery_reference",
        support["pp222_balanced"]: "pp222_balanced_reference",
        support["pp222_operational"]: "pp222_aggressive_reference",
        support["pp222_p95_guarded"]: "pp222_p95_guarded_reference",
        prior_decision["balanced_protocol_candidate"]: "pp228_balanced_reference",
        prior_decision["operational_protocol_candidate"]: "pp228_operational_reference",
        prior_decision["mape_challenger_protocol_candidate"]: "pp228_mape_reference",
        prior_decision["p95_guarded_protocol_candidate"]: "pp228_p95_guarded_reference",
        prior_decision["p95_extreme_protocol_candidate"]: "pp228_p95_extreme_reference",
    }
    for candidate in selected:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def row_by_candidate(stability: pd.DataFrame, candidate: str) -> pd.Series:
    rows = stability[stability["candidate"].eq(candidate)]
    if rows.empty:
        raise RuntimeError(f"Candidate not found in stability aggregate: {candidate}")
    return rows.iloc[0]


def choose_decision(stability: pd.DataFrame, prior_decision: dict[str, Any]) -> dict[str, Any]:
    pp228_balanced = row_by_candidate(stability, prior_decision["balanced_protocol_candidate"])
    pp228_operational = row_by_candidate(stability, prior_decision["operational_protocol_candidate"])
    pp228_mape = row_by_candidate(stability, prior_decision["mape_challenger_protocol_candidate"])
    p95_guard = row_by_candidate(stability, prior_decision["p95_guarded_protocol_candidate"])
    p95_extreme = row_by_candidate(stability, prior_decision["p95_extreme_protocol_candidate"])
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    base_mape = float(pp228_balanced["fixed_test_MAPE"])
    base_p95 = float(pp228_balanced["fixed_test_p95_APE"])
    base_p95_win = float(pp228_balanced["avg_pp64_p95_win_rate"])
    base_repl = float(pp228_balanced["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt23|ppopt229|ppopt230|ppopt231|ppopt232|ppopt233", regex=True)].copy()

    balanced = pp228_balanced.copy()
    balanced_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000001)
        & (pool["fixed_test_p95_APE"] <= base_p95 + 0.000002)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win - 0.000001)
        & (pool["replacement_score"] <= base_repl + 0.000002)
    ].copy()
    if not balanced_pool.empty:
        balanced = balanced_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    operational = balanced.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000001)
        & (pool["fixed_test_p95_APE"] <= base_p95 + 0.000002)
        & (pool["replacement_score"] <= base_repl + 0.000001)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    mape = pp228_mape.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= base_p95 + 0.000002].copy()
    if not mape_pool.empty:
        mape = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    p95_recovery = p95_guard.copy()
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win)
    ].copy()
    if not p95_pool.empty:
        p95_recovery = p95_pool.sort_values(["avg_pp64_p95_win_rate", "fixed_test_MAPE", "replacement_score"], ascending=[False, True, True]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp228_balanced_MAPE": float(row["fixed_test_MAPE"]) - base_mape,
            f"{prefix}_delta_vs_pp228_balanced_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - base_p95_win,
            f"{prefix}_delta_vs_pp228_operational_MAPE": float(row["fixed_test_MAPE"]) - float(pp228_operational["fixed_test_MAPE"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("balanced", balanced))
    decision.update(pack("mape_challenger", mape))
    decision.update(pack("p95_recovery", p95_recovery))
    decision.update(pack("p95_guarded", p95_guard))
    decision.update(pack("p95_extreme", p95_extreme))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "pp228_p95_recovery_operational_selection"),
        ("balanced", "pp228_p95_recovery_balanced_selection"),
        ("mape_challenger", "pp228_p95_recovery_mape_selection"),
        ("p95_recovery", "pp228_p95_recovery_p95_win_selection"),
        ("p95_guarded", "pp228_p95_recovery_p95_guarded_selection"),
        ("p95_extreme", "pp228_p95_recovery_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt234_{key}_pp228_p95_recovery__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT234"
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
    lines = ["| " + " | ".join(str(col) for col in view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    prior = config["prior_decision"]
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        prior["balanced_protocol_candidate"],
        prior["operational_protocol_candidate"],
        prior["mape_challenger_protocol_candidate"],
        prior["p95_guarded_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["balanced_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"운영 후보 MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['operational_avg_pp64_p95_win_rate']:.6f}. "
        f"PP228 균형 대비 MAPE 변화 {decision['operational_delta_vs_pp228_balanced_MAPE']:+.9f}, "
        f"p95 win rate 변화 {decision['operational_delta_vs_pp228_balanced_p95_win_rate']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT229~234 Warm PP228 p95-win recovery without MAPE loss 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP228 균형 후보를 기준으로 공격형 이동과 p95 회복 이동을 row별로 제한 적용",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 80),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 80),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 160),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability, stab_cols, 180),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT229~234 Warm PP228 p95-win recovery 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT229~234 Warm PP228 p95-win recovery without MAPE loss 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>균형 후보: <code>{html.escape(decision['balanced_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 80)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 80)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 160)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 180)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, previous_config = load_inputs()
    support = previous_config["support_candidates"]
    prior_decision = previous_config["selection_decision"]
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)

    balanced = pp187.prediction_array(previous, feature_base, prior_decision["balanced_protocol_candidate"])
    aggressive = pp187.prediction_array(previous, feature_base, prior_decision["operational_protocol_candidate"])
    mape = pp187.prediction_array(previous, feature_base, prior_decision["mape_challenger_protocol_candidate"])
    p95_guarded = pp187.prediction_array(previous, feature_base, prior_decision["p95_guarded_protocol_candidate"])
    p95_recovery = pp187.prediction_array(previous, feature_base, support["pp216_p95_recovery"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt229_aggressive_gated_lift(feature_base, balanced, aggressive))
    candidates.extend(pp_opt230_mape_tiny_lift(feature_base, balanced, mape))
    candidates.extend(pp_opt231_p95_recovery_support(feature_base, balanced, p95_guarded, p95_recovery))
    candidates.extend(pp_opt232_dual_offset(feature_base, balanced, aggressive, p95_guarded, p95_recovery))
    candidates.extend(pp_opt233_conservative_router(feature_base, balanced, aggressive, p95_guarded))

    predictions = pd.concat([reference_predictions(previous, support, prior_decision)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, prior_decision, support)
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, prior_decision)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, prior_decision, support)
    selected.extend(
        [
            decision["operational_protocol_candidate"],
            decision["balanced_protocol_candidate"],
            decision["mape_challenger_protocol_candidate"],
            decision["p95_recovery_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision)
    label_map[decision["operational_protocol_candidate"]] = "pp234_operational_pp228_p95_recovery_candidate"
    label_map[decision["balanced_protocol_candidate"]] = "pp234_balanced_pp228_p95_recovery_candidate"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp234_mape_pp228_p95_recovery_candidate"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp234_p95_recovery_pp228_p95_recovery_candidate"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp234_p95_guarded_pp228_p95_recovery_candidate"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp234_p95_extreme_pp228_p95_recovery_candidate"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    aggressive_signal, aggressive_score, aggressive_p95_gain, aggressive_mean_gain, aggressive_count = segment_gate(
        feature_base,
        balanced,
        aggressive,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.18,
        p95_threshold=-0.00003,
        p95_width=0.00012,
        mean_threshold=-0.00006,
        mean_width=0.00020,
        min_count=8.0,
    )
    recovery_signal, recovery_score, recovery_p95_gain, recovery_mean_gain, recovery_count = segment_gate(
        feature_base,
        balanced,
        p95_guarded,
        ["stable_price_band", "confidence_tier"],
        score_threshold=0.0,
        score_width=0.22,
        p95_threshold=-0.00004,
        p95_width=0.00018,
        mean_threshold=-0.00010,
        mean_width=0.00030,
        min_count=8.0,
    )
    feature_frame = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    feature_frame["pp228_balanced_log"] = balanced
    feature_frame["pp228_operational_log"] = aggressive
    feature_frame["pp228_mape_log"] = mape
    feature_frame["p95_guarded_log"] = p95_guarded
    feature_frame["p95_recovery_log"] = p95_recovery
    feature_frame["aggressive_signal"] = aggressive_signal
    feature_frame["aggressive_segment_score"] = aggressive_score
    feature_frame["aggressive_p95_gain"] = aggressive_p95_gain
    feature_frame["aggressive_mean_gain"] = aggressive_mean_gain
    feature_frame["aggressive_segment_count"] = aggressive_count
    feature_frame["recovery_signal"] = recovery_signal
    feature_frame["recovery_segment_score"] = recovery_score
    feature_frame["recovery_p95_gain"] = recovery_p95_gain
    feature_frame["recovery_mean_gain"] = recovery_mean_gain
    feature_frame["recovery_segment_count"] = recovery_count

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "previous_experiment": str(PP223_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "prior_decision": prior_decision,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP228 balanced log price",
            "aggressive_move": "clip((PP228 operational log price - PP228 balanced log price) * aggressive_weight, aggressive_cap)",
            "mape_move": "clip((PP228 MAPE challenger log price - PP228 balanced log price) * mape_weight, mape_cap)",
            "p95_recovery_move": "clip((p95 recovery log price - PP228 balanced log price) * recovery_weight, recovery_cap)",
            "dual_final": "PP228 balanced log price + aggressive_move + p95_recovery_move",
            "selection_goal": "Keep PP228 balanced p95 win-rate and avoid fixed-test MAPE loss while improving replacement score.",
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
    stability.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    feature_frame.to_csv(ARTIFACT_DIR / "pp228_p95_recovery_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp228_p95_recovery_without_mape_loss_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp228_p95_recovery_without_mape_loss_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family"]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability[
            ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
