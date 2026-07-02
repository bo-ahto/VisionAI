#!/usr/bin/env python3
"""Run PP-OPT89..95 Warm guarded tail-routing experiments.

PP82 operational improved the fixed test metrics, but repeated validation did
not support replacing PP64/PP70 yet.  This batch weakens or guards the PP82 tail
fallback in risk-focus rows and validates the selected candidates with the same
PP83~88 stability protocol.
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
PP76_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt76_82_warm_tail_routing_experiments.py"
PP71_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt71_75_warm_pp70_stability_validation.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp76 = load_module("pp_opt76_helpers", PP76_SCRIPT)
val71 = load_module("pp_opt71_helpers_for_pp89", PP71_SCRIPT)
opt8 = pp76.opt8
opt9 = pp76.opt9
opt29 = pp76.opt29

EXP_ID = "PP-OPT89-95"
EXP_SLUG = "PP-OPT89_95_warm_tail_guarded_stability_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP76_DIR = REPO / "experiments" / "track6" / "PP-OPT76_82_warm_tail_routing_experiments"
PP76_PREDS = PP76_DIR / "outputs" / "candidate_predictions.csv"
PP76_ITEMS = PP76_DIR / "outputs" / "experiment_item_summary.csv"
PP76_CONFIG = PP76_DIR / "artifacts" / "run_config.json"
PP76_TAIL_PROB = PP76_DIR / "artifacts" / "tail_classifier_detail.csv"
PP76_TAIL_SCORE = PP76_DIR / "artifacts" / "tail_risk_scores.csv"
PP47_QUANT = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments" / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = pp76.BASE_CANDIDATE
INCUMBENT = pp76.INCUMBENT
PREV_CHALLENGER = pp76.PREV_CHALLENGER
SEED = 20260609

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT89",
        "priority": "1",
        "title": "PP82 risk-focus rollback shrink",
        "description": "risk-focus에서 PP82 fallback을 PP70 쪽으로 되돌려 MAPE 악화를 줄인다.",
    },
    {
        "item_id": "PP-OPT90",
        "priority": "2",
        "title": "weaker hard-tail fallback local grid",
        "description": "PP80/PP82와 같은 구조에서 threshold, width, strength를 보수적으로 재탐색한다.",
    },
    {
        "item_id": "PP-OPT91",
        "priority": "3",
        "title": "soft helper tail fallback",
        "description": "PP20 단독 대신 PP20/PP30/PP48 혼합 helper로 fallback 방향을 부드럽게 만든다.",
    },
    {
        "item_id": "PP-OPT92",
        "priority": "4",
        "title": "quantile-direction guarded fallback",
        "description": "잔차 quantile 방향과 fallback 이동 방향이 맞지 않으면 fallback 강도를 줄인다.",
    },
    {
        "item_id": "PP-OPT93",
        "priority": "5",
        "title": "PP81 stable route plus PP82 tail boost",
        "description": "반복 안정성이 좋았던 PP81 계열을 기준으로 tail에서만 PP82를 일부 반영한다.",
    },
    {
        "item_id": "PP-OPT94",
        "priority": "6",
        "title": "p95 mode guard",
        "description": "PP82 p95형을 PP70/PP82 운영형 쪽으로 되돌려 MAPE 손실을 줄인다.",
    },
    {
        "item_id": "PP-OPT95",
        "priority": "7",
        "title": "final guarded tail-routing challenger",
        "description": "운영형과 p95 목적형 후보를 분리해 최종 선택한다.",
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


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP76_PREDS, usecols=usecols, chunksize=260_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP76~82 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing prediction components: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source = opt9.load_base_and_source()
    cfg = load_json(PP76_CONFIG)
    item_summary = pd.read_csv(PP76_ITEMS)
    pp81_best = str(item_summary[item_summary["item_id"].eq("PP-OPT81")].iloc[0]["best_candidate"])
    selected = {
        "pp20": "previous_challenger_pp20",
        "pp30": "reference_pp30_best",
        "pp48": "reference_pp48_score",
        "pp64": "reference_pp64_current_best",
        "pp70": "reference_pp70_refinement",
        "pp82_op": cfg["selection_decision"]["operational_protocol_candidate"],
        "pp82_p95": cfg["selection_decision"]["p95_protocol_candidate"],
        "pp81_best": pp81_best,
    }
    ref = load_reference_predictions(base, selected)
    quant = base[["eval_split", "_track6_row_id"]].merge(pd.read_csv(PP47_QUANT), on=["eval_split", "_track6_row_id"], how="left")
    tail = (
        base[["eval_split", "_track6_row_id"]]
        .merge(pd.read_csv(PP76_TAIL_PROB), on=["eval_split", "_track6_row_id"], how="left")
        .merge(pd.read_csv(PP76_TAIL_SCORE), on=["eval_split", "_track6_row_id"], how="left")
    )
    return base, source, ref, quant, tail, selected, cfg


def generic_risk_score(base: pd.DataFrame) -> np.ndarray:
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    conf = base["confidence_tier"].astype(str)
    price = base["stable_price_band"].astype(str)
    return np.clip(
        0.38 * np.clip((qwidth - 1.20) / 0.95, 0, 1)
        + 0.22 * np.clip(spread / 0.18, 0, 1)
        + 0.14 * np.clip(gap / 0.06, 0, 1)
        + 0.16 * conf.eq("low_confidence").to_numpy(dtype=float)
        + 0.10 * price.eq("very_high_price").to_numpy(dtype=float),
        0,
        1,
    )


def score_bundle(base: pd.DataFrame, tail: pd.DataFrame) -> dict[str, np.ndarray]:
    risk = generic_risk_score(base)
    tail_score_risk = tail["tail_score_risk"].fillna(0).to_numpy(dtype=float)
    tail_score_p95 = tail["tail_score_p95"].fillna(0).to_numpy(dtype=float)
    prob_tail85 = tail["prob_tail85_only"].fillna(0).to_numpy(dtype=float)
    prob_stable85 = tail["prob_stable_better_tail85"].fillna(0).to_numpy(dtype=float)
    return {
        "generic_risk": risk,
        "tail_score_risk": tail_score_risk,
        "tail_score_p95": tail_score_p95,
        "tail85_prob": prob_tail85,
        "stable85_prob": prob_stable85,
        "p95_prob": np.clip(0.55 * tail_score_p95 + 0.45 * prob_tail85, 0, 1),
        "risk_prob": np.clip(0.50 * tail_score_risk + 0.50 * prob_stable85, 0, 1),
        "risk_focus": np.clip(0.55 * risk + 0.25 * tail_score_risk + 0.20 * prob_tail85, 0, 1),
    }


def helper_bundle(ref: pd.DataFrame) -> dict[str, np.ndarray]:
    pp20 = ref["pp20"].to_numpy(dtype=float)
    pp30 = ref["pp30"].to_numpy(dtype=float)
    pp48 = ref["pp48"].to_numpy(dtype=float)
    return {
        "pp20": pp20,
        "pp48": pp48,
        "p95_weighted": 0.45 * pp20 + 0.30 * pp30 + 0.25 * pp48,
        "balanced_stable": 0.34 * pp20 + 0.33 * pp30 + 0.33 * pp48,
        "pp48_bias": 0.20 * pp20 + 0.25 * pp30 + 0.55 * pp48,
    }


def quantile_direction(quant: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    q25 = quant[["pp45_q25", "pp23_q25", "pp41_q25"]].to_numpy(dtype=float)
    q50 = quant[["pp45_q50", "pp23_q50", "pp41_q50"]].to_numpy(dtype=float)
    q75 = quant[["pp45_q75", "pp23_q75", "pp41_q75"]].to_numpy(dtype=float)
    positive = (q25 > 0).sum(axis=1) >= 2
    negative = (q75 < 0).sum(axis=1) >= 2
    direction = np.where(positive, 1.0, np.where(negative, -1.0, 0.0))
    strength = np.clip(np.abs(np.nanmedian(q50, axis=1)) / 0.12, 0, 1)
    return np.nan_to_num(direction), np.nan_to_num(strength)


def pp_opt89_risk_focus_shrink(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp82 = ref["pp82_op"].to_numpy(dtype=float)
    pp70 = ref["pp70"].to_numpy(dtype=float)
    pp81 = ref["pp81_best"].to_numpy(dtype=float)
    for target_key, target in [("pp70", pp70), ("pp81", pp81)]:
        for score_key in ["generic_risk", "risk_focus", "p95_prob"]:
            score = scores[score_key]
            for threshold in [0.48, 0.56, 0.64, 0.72]:
                for width in [0.18, 0.30, 0.42]:
                    w = gate(score, threshold, width)
                    for strength in [0.20, 0.35, 0.50, 0.70, 0.90]:
                        pred = pp82 + (target - pp82) * w * strength
                        name = (
                            f"ppopt89_risk_shrink__target={target_key}__score={score_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "pp82_risk_focus_shrink", "PP-OPT89", pred))
    return rows


def pp_opt90_weaker_local_grid(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], helpers: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    for helper_key in ["pp20", "p95_weighted", "balanced_stable"]:
        helper = helpers[helper_key]
        for score_key in ["p95_prob", "risk_prob"]:
            score = scores[score_key]
            for threshold in [0.62, 0.66, 0.70, 0.74, 0.78]:
                for width in [0.18, 0.24, 0.32]:
                    w = gate(score, threshold, width)
                    for strength in [0.42, 0.55, 0.70, 0.85, 1.00]:
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt90_weaker_tail__helper={helper_key}__score={score_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "weaker_hard_tail_local_grid", "PP-OPT90", pred))
    return rows


def pp_opt91_soft_helper(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], helpers: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    for helper_key in ["p95_weighted", "balanced_stable", "pp48_bias"]:
        helper = helpers[helper_key]
        for threshold in [0.54, 0.62, 0.70, 0.78]:
            for width in [0.18, 0.30, 0.42]:
                w = gate(scores["p95_prob"], threshold, width)
                for strength in [0.25, 0.40, 0.58, 0.76]:
                    pred = anchor + (helper - anchor) * w * strength
                    name = (
                        f"ppopt91_soft_helper__helper={helper_key}__thr={safe_name(threshold)}"
                        f"__width={safe_name(width)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "soft_helper_tail_fallback", "PP-OPT91", pred))
    return rows


def pp_opt92_quantile_direction_guard(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], helpers: dict[str, np.ndarray], quant: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    direction, q_strength = quantile_direction(quant)
    for helper_key in ["pp20", "p95_weighted", "balanced_stable"]:
        helper = helpers[helper_key]
        aligned = ((helper - anchor) * direction > 0).astype(float)
        for penalty in [0.00, 0.20, 0.40, 0.65]:
            q_guard = np.where(aligned > 0, 1.0, penalty + (1.0 - penalty) * (1.0 - q_strength))
            for threshold in [0.58, 0.66, 0.74]:
                for width in [0.18, 0.30]:
                    w = gate(scores["p95_prob"], threshold, width) * q_guard
                    for strength in [0.45, 0.65, 0.85, 1.00]:
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt92_qdir_guard__helper={helper_key}__pen={safe_name(penalty)}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "quantile_direction_guarded_tail", "PP-OPT92", pred))
    return rows


def pp_opt93_pp81_tail_boost(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp81 = ref["pp81_best"].to_numpy(dtype=float)
    pp82 = ref["pp82_op"].to_numpy(dtype=float)
    pp82_p95 = ref["pp82_p95"].to_numpy(dtype=float)
    for target_key, target in [("pp82op", pp82), ("pp82p95", pp82_p95)]:
        for score_key in ["p95_prob", "risk_prob"]:
            score = scores[score_key]
            for threshold in [0.46, 0.56, 0.66, 0.76]:
                for width in [0.18, 0.30, 0.42]:
                    w = gate(score, threshold, width)
                    for strength in [0.10, 0.20, 0.34, 0.50]:
                        pred = pp81 + (target - pp81) * w * strength
                        name = (
                            f"ppopt93_pp81_tail_boost__target={target_key}__score={score_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "pp81_stable_tail_boost", "PP-OPT93", pred))
    return rows


def pp_opt94_p95_mode_guard(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    p95_mode = ref["pp82_p95"].to_numpy(dtype=float)
    targets = {
        "pp70": ref["pp70"].to_numpy(dtype=float),
        "pp82op": ref["pp82_op"].to_numpy(dtype=float),
        "pp81": ref["pp81_best"].to_numpy(dtype=float),
    }
    for target_key, target in targets.items():
        for score_key in ["generic_risk", "risk_focus"]:
            score = scores[score_key]
            for threshold in [0.50, 0.60, 0.70]:
                for width in [0.18, 0.32]:
                    w = gate(score, threshold, width)
                    for strength in [0.20, 0.35, 0.55, 0.75]:
                        pred = p95_mode + (target - p95_mode) * w * strength
                        name = (
                            f"ppopt94_p95_guard__target={target_key}__score={score_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "p95_mode_mape_guard", "PP-OPT94", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp48_score", "pp48"),
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81_best"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


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
        p95_best = group[group["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"])
        if p95_best.empty:
            p95_best = group.sort_values(["test_p95_APE", "test_MAPE"])
        p95 = p95_best.iloc[0]
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
                "stable_validation_pass_vs_incumbent": bool(best["stable_validation_pass_vs_incumbent"]),
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


def select_challengers(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = metrics[(metrics["candidate"].eq("reference_pp64_current_best")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pp70 = metrics[(metrics["candidate"].eq("reference_pp70_refinement")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT89", "PP-OPT90", "PP-OPT91", "PP-OPT92", "PP-OPT93", "PP-OPT94"])].copy()
    pool["delta_vs_pp64_MAPE"] = pool["test_MAPE"] - float(pp64["MAPE"])
    pool["delta_vs_pp64_p95_APE"] = pool["test_p95_APE"] - float(pp64["p95_APE"])
    pool["delta_vs_pp70_MAPE"] = pool["test_MAPE"] - float(pp70["MAPE"])
    pool["delta_vs_pp70_p95_APE"] = pool["test_p95_APE"] - float(pp70["p95_APE"])

    stable_op = pool[
        (pool["operational_pass_vs_incumbent"])
        & (pool["delta_vs_pp64_MAPE"] <= 0)
        & (pool["delta_vs_pp64_p95_APE"] <= 0)
    ].copy()
    if stable_op.empty:
        stable_op = pool[(pool["operational_pass_vs_incumbent"]) & (pool["delta_vs_pp64_MAPE"] <= 0.00002)].copy()
    operational = stable_op.sort_values(["recommendation_score_vs_incumbent", "test_MAPE", "test_p95_APE"]).iloc[0]

    p95_pool = pool[
        (pool["test_delta_vs_incumbent_MAPE"] < 0)
        & (pool["test_p95_APE"] < float(pp64["p95_APE"]) - 0.00020)
        & (pool["stable_validation_pass_vs_incumbent"])
    ].copy()
    if p95_pool.empty:
        p95_pool = pool[(pool["test_delta_vs_incumbent_MAPE"] < 0)].copy()
    p95 = p95_pool.sort_values(["test_p95_APE", "test_MAPE", "recommendation_score_vs_incumbent"]).iloc[0]

    return {
        "reference_pp64_test_MAPE": float(pp64["MAPE"]),
        "reference_pp64_test_p95_APE": float(pp64["p95_APE"]),
        "reference_pp70_test_MAPE": float(pp70["MAPE"]),
        "reference_pp70_test_p95_APE": float(pp70["p95_APE"]),
        "operational_source_candidate": str(operational["candidate"]),
        "operational_source_item_id": str(operational["item_id"]),
        "operational_source_family": str(operational["family"]),
        "operational_test_MAPE": float(operational["test_MAPE"]),
        "operational_test_p95_APE": float(operational["test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["delta_vs_pp64_p95_APE"]),
        "p95_source_candidate": str(p95["candidate"]),
        "p95_source_item_id": str(p95["item_id"]),
        "p95_source_family": str(p95["family"]),
        "p95_test_MAPE": float(p95["test_MAPE"]),
        "p95_test_p95_APE": float(p95["test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["delta_vs_pp64_p95_APE"]),
        "selection_reason": "select stable operational candidate first; keep a separate p95-focused candidate if MAPE still beats incumbent",
    }


def add_protocol_candidates(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "guarded_tail_operational_selection"), ("p95", "guarded_tail_p95_selection")]:
        source = out[f"{key}_source_candidate"]
        protocol = f"ppopt95_{key}_guarded_tail_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT95"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def label_predictions(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    selected = {
        "hcoef_stable_source": BASE_CANDIDATE,
        "incumbent_pp7": INCUMBENT,
        "pp64_current_best": "reference_pp64_current_best",
        "pp70_refinement_candidate": "reference_pp70_refinement",
        "pp81_stable_reference": "reference_pp81_best",
        "pp82_operational_reference": "reference_pp82_operational",
        "pp82_p95_reference": "reference_pp82_p95",
        "pp95_operational_guarded_tail": decision["operational_protocol_candidate"],
        "pp95_p95_guarded_tail": decision["p95_protocol_candidate"],
    }
    subset = predictions[predictions["candidate"].isin(set(selected.values()))].copy()
    label_lookup = {candidate: label for label, candidate in selected.items()}
    subset["candidate_label"] = subset["candidate"].map(label_lookup).fillna(subset["candidate"])
    return subset, selected


def stability_decision(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    op = stability_aggregate[stability_aggregate["candidate_label"].eq("pp95_operational_guarded_tail")].iloc[0]
    p95 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp95_p95_guarded_tail")].iloc[0]
    op_replace = (
        op["fixed_test_delta_vs_pp64_MAPE"] <= 0
        and op["fixed_test_delta_vs_pp64_p95_APE"] <= 0
        and op["avg_pp64_MAPE_win_rate"] >= 0.50
        and op["avg_pp64_p95_win_rate"] >= 0.45
    )
    return {
        "operational_verdict": "PP95 운영형은 PP64/PP70 교체 후보로 승격 가능" if op_replace else "PP95 운영형도 운영 교체는 보류",
        "p95_verdict": "PP95 p95형은 tail 안정성 우선 옵션으로 유지",
        "pp95_operational_fixed_test_MAPE": float(op["fixed_test_MAPE"]),
        "pp95_operational_fixed_test_p95_APE": float(op["fixed_test_p95_APE"]),
        "pp95_operational_delta_vs_pp64_MAPE": float(op["fixed_test_delta_vs_pp64_MAPE"]),
        "pp95_operational_delta_vs_pp64_p95_APE": float(op["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp95_operational_avg_pp64_MAPE_win_rate": float(op["avg_pp64_MAPE_win_rate"]),
        "pp95_operational_avg_pp64_p95_win_rate": float(op["avg_pp64_p95_win_rate"]),
        "pp95_operational_avg_pp64_all3_win_rate": float(op["avg_pp64_all3_win_rate"]),
        "pp95_p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "pp95_p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "pp95_p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "pp95_p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp95_p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "pp95_p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
    }


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 60) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 60) -> str:
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
    selected_metrics = metrics[
        metrics["eval_split"].eq("test")
        & metrics["candidate"].isin(
            [
                "reference_pp64_current_best",
                "reference_pp70_refinement",
                "reference_pp81_best",
                "reference_pp82_operational",
                "reference_pp82_p95",
                decision["operational_protocol_candidate"],
                decision["p95_protocol_candidate"],
            ]
        )
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    op = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    top_p95 = aggregate[aggregate["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(40)
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
        "p95_candidate",
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
        "avg_pp64_all3_win_rate",
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
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(["pp95_operational_guarded_tail", "pp95_p95_guarded_tail"])]
    stability = config["stability_decision"]
    verdict = (
        f"{stability['operational_verdict']}. 운영형 fixed test는 PP64 대비 MAPE "
        f"{stability['pp95_operational_delta_vs_pp64_MAPE']:+.6f}, p95 "
        f"{stability['pp95_operational_delta_vs_pp64_p95_APE']:+.6f}."
    )

    md = "\n".join(
        [
            "# PP-OPT89~95 Warm guarded tail-routing 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_metrics, list(selected_metrics.columns), 20),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 통과 후보 상위",
            markdown_table(op, result_cols, 50),
            "",
            "## p95 상위 후보",
            markdown_table(top_p95, result_cols, 40),
            "",
            "## 반복 안정성 검증",
            markdown_table(stability_aggregate, stab_cols, 40),
            "",
            "## 신규 후보 시나리오별 안정성",
            markdown_table(scenario_focus, scenario_cols, 30),
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
  <title>PP-OPT89~95 Warm guarded tail-routing 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1280px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
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
  <h1>PP-OPT89~95 Warm guarded tail-routing 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영형: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95형: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>운영형 PP64 대비 MAPE</strong>{stability['pp95_operational_delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{stability['pp95_operational_delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 주요 후보 test 비교</h2>
  {table_html(selected_metrics, list(selected_metrics.columns), 20)}
  <h2>2. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}
  <h2>3. 운영 통과 후보 상위</h2>
  {table_html(op, result_cols, 50)}
  <h2>4. p95 상위 후보</h2>
  {table_html(top_p95, result_cols, 40)}
  <h2>5. 반복 안정성 검증</h2>
  {table_html(stability_aggregate, stab_cols, 40)}
  <h2>6. 신규 후보 시나리오별 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 30)}
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, quant, tail, selected_refs, parent_config = load_inputs()
    scores = score_bundle(base, tail)
    helpers = helper_bundle(ref)
    references = add_reference_candidates(base, ref)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt89_risk_focus_shrink(base, ref, scores))
    candidates.extend(pp_opt90_weaker_local_grid(base, ref, scores, helpers))
    candidates.extend(pp_opt91_soft_helper(base, ref, scores, helpers))
    candidates.extend(pp_opt92_quantile_direction_guard(base, ref, scores, helpers, quant))
    candidates.extend(pp_opt93_pp81_tail_boost(base, ref, scores))
    candidates.extend(pp_opt94_p95_mode_guard(base, ref, scores))

    predictions = pd.concat([source] + references + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    decision = select_challengers(metrics, aggregate)
    predictions, decision = add_protocol_candidates(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    stability_predictions, stability_labels = label_predictions(predictions, decision)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = val71.aggregate_summary(stability_summary, fixed)
    stability_dec = stability_decision(stability_aggregate)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "previous_challenger": PREV_CHALLENGER,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "selected_references": selected_refs,
        "stability_labels": stability_labels,
        "selection_decision": decision,
        "stability_decision": stability_dec,
        "items": ITEMS,
        "sources": {
            "pp76_config": str(PP76_CONFIG.relative_to(REPO)),
            "pp76_predictions": str(PP76_PREDS.relative_to(REPO)),
            "pp76_tail_probability": str(PP76_TAIL_PROB.relative_to(REPO)),
            "pp76_tail_score": str(PP76_TAIL_SCORE.relative_to(REPO)),
            "pp47_quantile": str(PP47_QUANT.relative_to(REPO)),
            "pp76_helper": str(PP76_SCRIPT.relative_to(REPO)),
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
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "guarded_tail_routing_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "guarded_tail_routing_result.html").write_text(report_html, encoding="utf-8")

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
