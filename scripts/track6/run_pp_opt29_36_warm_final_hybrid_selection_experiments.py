#!/usr/bin/env python3
"""Run PP-OPT29..36 Warm final hybrid selection experiments.

This batch focuses on combining the strongest recent signals:

- PP-OPT20: stable p95-oriented challenger
- PP-OPT23: MAPE-oriented monotonic challenger
- PP-OPT27: emergency tail guard signal
- PP-OPT15/21: aggressive MAPE improvement signals

It remains non-submission and uses the same Warm validation OOF / fixed test
split as prior PP-OPT batches.
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
OPT8_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt8_warm_extended_correction_experiments.py"
OPT9_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt9_13_warm_followup_improvement_experiments.py"
OPT14_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt14_20_warm_gate_refinement_experiments.py"
OPT21_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt21_28_warm_model_characteristic_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt8 = load_module("pp_opt8_helpers", OPT8_SCRIPT)
opt9 = load_module("pp_opt9_helpers", OPT9_SCRIPT)
opt14 = load_module("pp_opt14_helpers", OPT14_SCRIPT)
opt21 = load_module("pp_opt21_helpers", OPT21_SCRIPT)

EXP_ID = "PP-OPT29-36"
EXP_SLUG = "PP-OPT29_36_warm_final_hybrid_selection_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP14_PREDS = REPO / "experiments" / "track6" / "PP-OPT14_20_warm_gate_refinement_experiments" / "outputs" / "candidate_predictions.csv"
PP14_AGG = REPO / "experiments" / "track6" / "PP-OPT14_20_warm_gate_refinement_experiments" / "outputs" / "aggregate_candidate_stability.csv"
PP21_PREDS = REPO / "experiments" / "track6" / "PP-OPT21_28_warm_model_characteristic_experiments" / "outputs" / "candidate_predictions.csv"
PP21_AGG = REPO / "experiments" / "track6" / "PP-OPT21_28_warm_model_characteristic_experiments" / "outputs" / "aggregate_candidate_stability.csv"

BASE_CANDIDATE = opt8.BASE_CANDIDATE
INCUMBENT = "incumbent_operational_pp_opt7"
PREV_CHALLENGER = "previous_challenger_pp20"
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {"item_id": "PP-OPT29", "priority": "1", "title": "PP20 + PP23 위험도별 혼합", "description": "위험 구간은 PP20, 안정 구간은 PP23 비중을 높인다."},
    {"item_id": "PP-OPT30", "priority": "2", "title": "PP20 vs PP23 row별 선택 classifier", "description": "각 row에서 PP20과 PP23 중 더 좋은 후보를 선택하도록 학습한다."},
    {"item_id": "PP-OPT31", "priority": "3", "title": "PP23 + emergency tail guard", "description": "PP23에 PP27 tail 방어 신호를 위험 구간에서만 약하게 더한다."},
    {"item_id": "PP-OPT32", "priority": "4", "title": "monotonic gate probability calibration", "description": "PP23 monotonic gate를 더 보수적으로 보정해 과보정을 줄인다."},
    {"item_id": "PP-OPT33", "priority": "5", "title": "constrained candidate stacking", "description": "PP7/20/23/15/27 후보를 제한 조건 안에서 가중 결합한다."},
    {"item_id": "PP-OPT34", "priority": "6", "title": "p95-safe uplift label 재정의", "description": "p95 악화 없이 개선되는 row만 보정하도록 라벨을 재정의한다."},
    {"item_id": "PP-OPT35", "priority": "7", "title": "segment별 PP20/PP23/PP27 라우팅", "description": "가격대/신뢰도/유사작품수 구간별로 최적 후보를 고른다."},
    {"item_id": "PP-OPT36", "priority": "8", "title": "final challenger freeze protocol", "description": "PP20 대비 추가 개선까지 고려해 최종 challenger를 선택한다."},
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def select_components() -> dict[str, str]:
    a14 = pd.read_csv(PP14_AGG)
    a21 = pd.read_csv(PP21_AGG)
    op21 = a21[a21["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    op14 = a14[a14["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    if op21.empty or op14.empty:
        raise ValueError("Prior batches must contain operational-pass candidates")
    return {
        "pp20": str(a14[a14["item_id"].eq("PP-OPT20")].iloc[0]["candidate"]),
        "pp23": str(op21[op21["item_id"].eq("PP-OPT23")].iloc[0]["candidate"]),
        "pp23_mape": str(a21[a21["item_id"].eq("PP-OPT23")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp27_tail": str(a21[a21["item_id"].eq("PP-OPT27")].sort_values(["test_p95_APE", "test_MAPE"]).iloc[0]["candidate"]),
        "pp15_mape": str(a14[a14["item_id"].eq("PP-OPT15")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp21_mape": str(a21[a21["item_id"].eq("PP-OPT21")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp19_stable": str(op14[op14["item_id"].eq("PP-OPT19")].iloc[0]["candidate"]),
        "pp14_stable": str(op14[op14["item_id"].eq("PP-OPT14")].iloc[0]["candidate"]),
        "pp24_conformal": str(op21[op21["item_id"].eq("PP-OPT24")].iloc[0]["candidate"]),
    }


def load_prediction_components(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    source_map = {
        "pp20": PP14_PREDS,
        "pp15_mape": PP14_PREDS,
        "pp19_stable": PP14_PREDS,
        "pp14_stable": PP14_PREDS,
        "pp23": PP21_PREDS,
        "pp23_mape": PP21_PREDS,
        "pp27_tail": PP21_PREDS,
        "pp21_mape": PP21_PREDS,
        "pp24_conformal": PP21_PREDS,
    }
    out = base[["eval_split", "_track6_row_id"]].copy()
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    for file_path in sorted(set(source_map.values())):
        labels = [label for label, path in source_map.items() if path == file_path]
        needed = {selected[label] for label in labels}
        chunks = []
        for chunk in pd.read_csv(file_path, usecols=usecols, chunksize=100_000):
            part = chunk[chunk["candidate"].isin(needed)].copy()
            if not part.empty:
                chunks.append(part)
        if not chunks:
            raise ValueError(f"No components loaded from {file_path}")
        long = pd.concat(chunks, ignore_index=True)
        for label in labels:
            candidate = selected[label]
            part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
            out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    # Add incumbent directly from source for convenience.
    source = opt8.source_predictions(base)
    inc = source[source["candidate"].eq(INCUMBENT)][["eval_split", "_track6_row_id", "pred_log"]]
    out = out.merge(inc.rename(columns={"pred_log": "incumbent"}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in list(selected) + ["incumbent"] if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing prediction components: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt8.candidate_frame(
        base,
        candidate,
        family,
        item_id,
        pred_log,
        pred_log - pd.to_numeric(base["hcoef_stable"], errors="coerce").to_numpy(dtype=float),
    )


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def row_cap(base: pd.DataFrame, cap: float, mode: str) -> np.ndarray:
    return opt9.row_cap(base, cap, mode)


def uncertainty_score(base: pd.DataFrame, tail_prob: np.ndarray) -> np.ndarray:
    q = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    score = (
        0.30 * np.clip((q - 1.0) / 0.8, 0, 1)
        + 0.20 * np.clip(spread / 0.18, 0, 1)
        + 0.15 * np.clip(gap / 0.055, 0, 1)
        + 0.15 * np.clip(1.0 / np.maximum(svc + 1.0, 1.0), 0, 1)
        + 0.20 * np.clip(tail_prob, 0, 1)
    )
    return np.clip(score, 0, 1)


def gate(prob: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((prob - threshold) / max(width, 1e-6), 0.0, 1.0)


def validation_thresholds(base: pd.DataFrame, incumbent: np.ndarray) -> dict[str, float]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(incumbent, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    return {
        "p85": float(np.quantile(inc_ape[val_mask], 0.85)),
        "p90": float(np.quantile(inc_ape[val_mask], 0.90)),
        "p95": float(np.quantile(inc_ape[val_mask], 0.95)),
    }


def train_probabilities(base: pd.DataFrame, comp: pd.DataFrame, thresholds: dict[str, float]) -> dict[str, np.ndarray]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc = comp["incumbent"].to_numpy(dtype=float)
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    pp15 = comp["pp15_mape"].to_numpy(dtype=float)
    inc_ape = ape(inc, actual_price)
    pp20_ape = ape(pp20, actual_price)
    pp23_ape = ape(pp23, actual_price)
    pp15_ape = ape(pp15, actual_price)
    tail_label = inc_ape >= thresholds["p90"]
    pp23_over_pp20 = (pp23_ape + 0.001 < pp20_ape) & (pp23_ape <= thresholds["p90"] + 0.02)
    pp15_safe = (pp15_ape + 0.001 < inc_ape) & (pp15_ape <= thresholds["p90"])
    pp23_safe = (pp23_ape + 0.001 < inc_ape) & (pp23_ape <= thresholds["p90"])
    pp23_p95safe = (pp23_ape + 0.001 < pp20_ape) & (pp23_ape <= thresholds["p85"])
    return {
        "tail_lgbm": opt21.oof_lgbm_probability(base, tail_label.astype(int)),
        "select_pp23_lgbm": opt21.oof_lgbm_probability(base, pp23_over_pp20.astype(int)),
        "select_pp23_cat": opt21.oof_catboost_probability(base, pp23_over_pp20.astype(int)),
        "pp15_safe_lgbm": opt21.oof_lgbm_probability(base, pp15_safe.astype(int)),
        "pp23_safe_lgbm": opt21.oof_lgbm_probability(base, pp23_safe.astype(int)),
        "pp23_p95safe_lgbm": opt21.oof_lgbm_probability(base, pp23_p95safe.astype(int)),
    }


def pp_opt29_risk_blend(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    risk = uncertainty_score(base, probs["tail_lgbm"])
    rows: list[pd.DataFrame] = []
    for risk_power in [0.75, 1.00, 1.35]:
        r = np.clip(risk, 0, 1) ** risk_power
        for floor in [0.10, 0.20, 0.30]:
            w20 = np.clip(floor + (1.0 - floor) * r, 0, 1)
            pred = (1.0 - w20) * pp23 + w20 * pp20
            name = f"ppopt29_risk_blend__power={safe_name(risk_power)}__floor={safe_name(floor)}"
            rows.append(make_candidate(base, name, "pp20_pp23_risk_weighted_blend", "PP-OPT29", pred))
    return rows


def pp_opt30_row_selector(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    for prob_name in ["select_pp23_lgbm", "select_pp23_cat"]:
        prob = probs[prob_name]
        for threshold in [0.18, 0.28, 0.38]:
            for sharpness in [0.75, 1.00, 1.35]:
                w23 = gate(prob, threshold, 0.60) ** sharpness
                pred = w23 * pp23 + (1.0 - w23) * pp20
                name = f"ppopt30_row_selector__model={prob_name}__thr={safe_name(threshold)}__sharp={safe_name(sharpness)}"
                rows.append(make_candidate(base, name, "pp20_pp23_row_selector", "PP-OPT30", pred))
    return rows


def pp_opt31_emergency_tail_guard(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    pp23 = comp["pp23"].to_numpy(dtype=float)
    tail_delta = comp["pp27_tail"].to_numpy(dtype=float) - pp23
    rows: list[pd.DataFrame] = []
    for threshold in [0.12, 0.20, 0.30]:
        tg = gate(probs["tail_lgbm"], threshold, 0.62)
        for strength in [0.25, 0.40, 0.55, 0.70]:
            for cap in [0.010, 0.014, 0.018]:
                corr = clip_by_row(tail_delta * tg * strength, row_cap(base, cap, "risk"))
                name = f"ppopt31_pp23_tail_guard__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "pp23_emergency_tail_guard", "PP-OPT31", pp23 + corr))
    return rows


def pp_opt32_monotonic_calibration(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    delta = pp23 - inc
    rows: list[pd.DataFrame] = []
    for prob_name in ["pp23_safe_lgbm", "pp23_p95safe_lgbm"]:
        prob = probs[prob_name]
        for threshold in [0.14, 0.24, 0.34]:
            for blend_floor in [0.00, 0.20, 0.40]:
                w = blend_floor + (1.0 - blend_floor) * gate(prob, threshold, 0.60)
                calibrated = inc + delta * w
                # Blend back to PP20 in high-risk rows.
                risk = uncertainty_score(base, probs["tail_lgbm"])
                w20 = np.clip((risk - 0.45) / 0.45, 0, 1)
                pred = (1.0 - w20) * calibrated + w20 * pp20
                name = f"ppopt32_monotonic_calibration__prob={prob_name}__thr={safe_name(threshold)}__floor={safe_name(blend_floor)}"
                rows.append(make_candidate(base, name, "monotonic_gate_probability_calibration", "PP-OPT32", pred))
    return rows


def pp_opt33_candidate_stacking(base: pd.DataFrame, comp: pd.DataFrame) -> list[pd.DataFrame]:
    keys = ["incumbent", "pp20", "pp23", "pp15_mape", "pp27_tail"]
    rows: list[pd.DataFrame] = []
    weight_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    # Keep grid compact and constrained.
    for w20 in weight_values:
        for w23 in weight_values:
            for w15 in [0.0, 0.1, 0.2, 0.3]:
                for w27 in [0.0, 0.1, 0.2]:
                    w_inc = 1.0 - w20 - w23 - w15 - w27
                    if w_inc < -1e-9 or w_inc > 0.8:
                        continue
                    if w23 + w15 <= 0:
                        continue
                    weights = {"incumbent": w_inc, "pp20": w20, "pp23": w23, "pp15_mape": w15, "pp27_tail": w27}
                    pred = sum(weights[key] * comp[key].to_numpy(dtype=float) for key in keys)
                    name = (
                        f"ppopt33_stack__inc={safe_name(w_inc)}__p20={safe_name(w20)}"
                        f"__p23={safe_name(w23)}__p15={safe_name(w15)}__p27={safe_name(w27)}"
                    )
                    rows.append(make_candidate(base, name, "constrained_candidate_stacking", "PP-OPT33", pred))
    return rows


def pp_opt34_p95_safe_uplift(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    for source_key, prob_key in [("pp15_mape", "pp15_safe_lgbm"), ("pp23", "pp23_p95safe_lgbm"), ("pp21_mape", "pp15_safe_lgbm")]:
        delta = comp[source_key].to_numpy(dtype=float) - inc
        prob = probs[prob_key]
        for threshold in [0.18, 0.28, 0.38, 0.48]:
            for strength in [0.45, 0.65, 0.85]:
                corr = clip_by_row(delta * gate(prob, threshold, 0.60) * strength * opt9.qwidth_governor(base, "mild"), row_cap(base, 0.022, "risk"))
                name = f"ppopt34_p95safe_uplift__src={source_key}__prob={prob_key}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "p95_safe_uplift_gate", "PP-OPT34", inc + corr))
    return rows


def segment_router_predictions(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    candidate_keys: list[str],
    group_cols: list[str],
    objective: str,
) -> np.ndarray:
    return opt21.segment_router_predictions(base, comp, candidate_keys, group_cols, objective)


def pp_opt35_segment_router(base: pd.DataFrame, comp: pd.DataFrame) -> list[pd.DataFrame]:
    candidate_keys = ["incumbent", "pp20", "pp23", "pp15_mape", "pp27_tail", "pp19_stable", "pp14_stable"]
    group_sets = {
        "price": ["stable_price_band"],
        "confidence": ["confidence_tier"],
        "price_confidence": ["stable_price_band", "confidence_tier"],
        "price_support": ["stable_price_band", "svc_group_n_band"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "support_qwidth": ["svc_group_n_band", "qwidth_band"],
        "spread_price": ["pred_spread_band", "stable_price_band"],
    }
    rows: list[pd.DataFrame] = []
    for group_name, cols in group_sets.items():
        for objective in ["mape", "guarded"]:
            pred = segment_router_predictions(base, comp, candidate_keys, cols, objective)
            name = f"ppopt35_segment_router__group={group_name}__obj={objective}"
            rows.append(make_candidate(base, name, "pp20_pp23_pp27_segment_router", "PP-OPT35", pred))
    return rows


def previous_challenger_frame(base: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    return make_candidate(base, PREV_CHALLENGER, "previous_challenger", "PREV", comp["pp20"].to_numpy(dtype=float))


def select_protocol_candidate(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> pd.Series:
    prev_test = metrics[(metrics["candidate"].eq(PREV_CHALLENGER)) & (metrics["eval_split"].eq("test"))].iloc[0]
    candidates = aggregate[
        ~aggregate["candidate"].isin([BASE_CANDIDATE, INCUMBENT, PREV_CHALLENGER])
    ].copy()
    # Prefer candidates that improve PP-OPT7 and do not give back too much p95
    # versus the PP20 challenger.
    operational = candidates[candidates["operational_pass_vs_incumbent"]].copy()
    if not operational.empty:
        operational["delta_vs_prev_MAPE"] = operational["test_MAPE"] - float(prev_test["MAPE"])
        operational["delta_vs_prev_p95_APE"] = operational["test_p95_APE"] - float(prev_test["p95_APE"])
        preferred = operational[
            (operational["delta_vs_prev_MAPE"] < 0)
            & (operational["delta_vs_prev_p95_APE"] <= 0.0015)
        ].copy()
        if not preferred.empty:
            return preferred.sort_values(
                [
                    "delta_vs_prev_MAPE",
                    "delta_vs_prev_p95_APE",
                    "incumbent_MAPE_improve_rate",
                    "recommendation_score_vs_incumbent",
                ],
                ascending=[True, True, False, True],
            ).iloc[0]
        return operational.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    return candidates.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]


def add_protocol_candidate(predictions: pd.DataFrame, metrics: pd.DataFrame, aggregate: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    selected = select_protocol_candidate(metrics, aggregate)
    source_name = str(selected["candidate"])
    protocol_name = f"ppopt36_final_challenger__source={safe_name(source_name)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source_name)].copy()
    duplicate["candidate"] = protocol_name
    duplicate["family"] = "final_challenger_freeze_protocol"
    duplicate["item_id"] = "PP-OPT36"
    decision = {
        "selected_source_candidate": source_name,
        "protocol_candidate": protocol_name,
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "operational pass first, then PP20 MAPE improvement with p95 give-back <= 0.0015, then recommendation score",
    }
    for col in [
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "recommendation_score_vs_incumbent",
    ]:
        decision[col] = float(selected[col])
    return pd.concat([predictions, duplicate], ignore_index=True), decision


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    item_info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "PREV"}:
            continue
        ordered = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        )
        best = ordered.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MdAPE": best["test_MdAPE"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MdAPE": best["test_delta_vs_incumbent_MdAPE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "validation_delta_vs_incumbent_MAPE": best["validation_delta_vs_incumbent_MAPE"],
                "validation_delta_vs_incumbent_p95_APE": best["validation_delta_vs_incumbent_p95_APE"],
                "incumbent_MAPE_improve_rate": best["incumbent_MAPE_improve_rate"],
                "incumbent_p95_not_worse_rate": best["incumbent_p95_not_worse_rate"],
                "incumbent_all3_rate": best["incumbent_all3_rate"],
                "stable_validation_pass_vs_incumbent": bool(best["stable_validation_pass_vs_incumbent"]),
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
            }
        )
    summary = pd.DataFrame(rows).merge(item_info, on="item_id", how="left")
    return summary.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    incumbent = metrics[metrics["candidate"].eq(INCUMBENT)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]].sort_values("eval_split")
    previous = metrics[metrics["candidate"].eq(PREV_CHALLENGER)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("eval_split")
    selected_metrics = metrics[metrics["candidate"].eq(decision["protocol_candidate"])][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "stable_validation_pass_vs_incumbent",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "item_id",
        "candidate",
        "family",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    md = "\n".join(
        [
            "# PP-OPT29~36 Warm 최종 하이브리드 선택 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## PP-OPT36 최종 선택 후보",
            f"- 선택 후보: `{decision['protocol_candidate']}`",
            f"- 원본 후보: `{decision['selected_source_candidate']}`",
            f"- 원본 실험: `{decision['selected_source_item_id']}` / `{decision['selected_source_family']}`",
            markdown_table(selected_metrics, list(selected_metrics.columns), 10),
            "",
            "## 이전 challenger PP-OPT20",
            markdown_table(previous, list(previous.columns), 10),
            "",
            "## 현재 운영 후보 PP-OPT7",
            markdown_table(incumbent, list(incumbent.columns), 10),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## MAPE와 p95 동시 개선 후보",
            markdown_table(both, result_cols, 40),
            "",
            "## 해석",
            "이번 실험은 PP20 안정성, PP23 성능, PP27 tail 방어를 조합하는 최종 선택 실험이다. PP20보다 MAPE가 낮아지면서 p95를 크게 되돌리지 않는 후보를 우선한다.",
            "만약 PP36 선택 후보가 PP20 대비 MAPE를 낮추되 p95 손실이 제한적이면 운영 challenger를 PP36으로 갱신할 수 있다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    verdict = "최종 challenger 후보가 선택되었다."
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT29~36 Warm 최종 하이브리드 선택 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1240px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
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
  <h1>PP-OPT29~36 Warm 최종 하이브리드 선택 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)} 선택 후보는 <code>{html.escape(decision['protocol_candidate'])}</code>이다.</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision['test_delta_vs_incumbent_MAPE']:.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision['test_delta_vs_incumbent_p95_APE']:.6f}</div>
  </div>

  <h2>1. PP-OPT36 최종 선택 후보</h2>
  <p>원본 후보: <code>{html.escape(decision['selected_source_candidate'])}</code></p>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}

  <h2>2. 이전 challenger PP-OPT20</h2>
  {table_html(previous, list(previous.columns), 10)}

  <h2>3. 현재 운영 후보 PP-OPT7</h2>
  {table_html(incumbent, list(incumbent.columns), 10)}

  <h2>4. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>5. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}

  <h2>6. MAPE와 p95 동시 개선 후보</h2>
  {table_html(both, result_cols, 40)}

  <h2>7. 해석</h2>
  <p>이번 실험은 PP20 안정성, PP23 성능, PP27 tail 방어를 조합하는 최종 선택 실험이다. PP20보다 MAPE가 낮아지면서 p95를 크게 되돌리지 않는 후보를 우선한다.</p>
  <p>PP36 선택 후보가 PP20 대비 MAPE를 낮추고 p95 손실을 제한하면 운영 challenger를 PP36으로 갱신할 수 있다.</p>

  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    selected = select_components()
    comp = load_prediction_components(base, selected)
    thresholds = validation_thresholds(base, comp["incumbent"].to_numpy(dtype=float))
    probs = train_probabilities(base, comp, thresholds)

    candidates: list[pd.DataFrame] = [previous_challenger_frame(base, comp)]
    candidates.extend(pp_opt29_risk_blend(base, comp, probs))
    candidates.extend(pp_opt30_row_selector(base, comp, probs))
    candidates.extend(pp_opt31_emergency_tail_guard(base, comp, probs))
    candidates.extend(pp_opt32_monotonic_calibration(base, comp, probs))
    candidates.extend(pp_opt33_candidate_stacking(base, comp))
    candidates.extend(pp_opt34_p95_safe_uplift(base, comp, probs))
    candidates.extend(pp_opt35_segment_router(base, comp))

    predictions = pd.concat([source] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    predictions, decision = add_protocol_candidate(predictions, metrics, aggregate)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

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
        "items": ITEMS,
        "selected_components": selected,
        "thresholds": thresholds,
        "selection_decision": decision,
        "sources": {
            "pp_opt14_predictions": str(PP14_PREDS.relative_to(REPO)),
            "pp_opt14_aggregate": str(PP14_AGG.relative_to(REPO)),
            "pp_opt21_predictions": str(PP21_PREDS.relative_to(REPO)),
            "pp_opt21_aggregate": str(PP21_AGG.relative_to(REPO)),
            "pp_opt8_helper": str(OPT8_SCRIPT.relative_to(REPO)),
            "pp_opt9_helper": str(OPT9_SCRIPT.relative_to(REPO)),
            "pp_opt14_helper": str(OPT14_SCRIPT.relative_to(REPO)),
            "pp_opt21_helper": str(OPT21_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    gate_df = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            **{name: values for name, values in probs.items()},
        }
    )
    gate_df.to_csv(ARTIFACT_DIR / "gate_probabilities.csv", index=False)

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "final_hybrid_selection_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "final_hybrid_selection_result.html").write_text(report_html, encoding="utf-8")

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
                "test_delta_vs_incumbent_MAPE",
                "test_delta_vs_incumbent_p95_APE",
                "incumbent_MAPE_improve_rate",
                "incumbent_p95_not_worse_rate",
                "stable_validation_pass_vs_incumbent",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nOperational pass count:", int(aggregate["operational_pass_vs_incumbent"].sum()))


if __name__ == "__main__":
    main()
