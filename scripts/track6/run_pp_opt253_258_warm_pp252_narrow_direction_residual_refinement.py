#!/usr/bin/env python3
"""Run PP-OPT253..258 Warm PP252 narrow direction-residual support refinement."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP247_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt247_252_warm_pp246_residual_direction_gated_correction.py"
PP247_DIR = REPO / "experiments" / "track6" / "PP-OPT247_252_warm_pp246_residual_direction_gated_correction"
PP247_PREDICTIONS = PP247_DIR / "outputs" / "candidate_predictions.csv"
PP247_CONFIG = PP247_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT253-258"
EXP_SLUG = "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"


ITEMS = [
    {
        "item_id": "PP-OPT253",
        "priority": "1",
        "title": "narrow hist35 Huber support refinement",
        "description": "PP252 성공 조합인 hist35 방향 gate + Huber residual + p95 support 주변을 좁게 재탐색.",
    },
    {
        "item_id": "PP-OPT254",
        "priority": "2",
        "title": "confidence threshold and cap split refinement",
        "description": "direction confidence threshold, 상향/하향 cap, quantile shrink를 더 세분화.",
    },
    {
        "item_id": "PP-OPT255",
        "priority": "3",
        "title": "weak stability add-on from PP250",
        "description": "PP250의 높은 p95 win-rate 이동분을 PP252 균형 후보에 아주 약하게 추가.",
    },
    {
        "item_id": "PP-OPT256",
        "priority": "4",
        "title": "PP252 source residual continuation",
        "description": "PP252를 새 기준으로 두고 잔차 방향 gate를 다시 학습해 2차 보정 가능성 확인.",
    },
    {
        "item_id": "PP-OPT257",
        "priority": "5",
        "title": "direction probability ensemble refinement",
        "description": "hist35, hist70, logistic direction probability를 약하게 평균해 단일 분류기 의존도를 낮춤.",
    },
    {
        "item_id": "PP-OPT258",
        "priority": "6",
        "title": "final PP252 narrow refinement decision",
        "description": "PP252 대비 MAPE, p95 win rate, replacement score 제약을 만족하는 후보를 최종 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp247 = load_module("pp_opt247_helpers_for_pp253", PP247_SCRIPT)
pp241 = pp247.pp241
pp235 = pp247.pp235
pp199 = pp247.pp199
pp187 = pp247.pp187
pp161 = pp247.pp161
opt8 = pp247.opt8
val71 = pp247.val71

BASE_CANDIDATE = pp247.BASE_CANDIDATE
INCUMBENT_CANDIDATE = pp247.INCUMBENT_CANDIDATE
PP64_CANDIDATE = pp247.PP64_CANDIDATE
PP70_CANDIDATE = pp247.PP70_CANDIDATE
PP126_CANDIDATE = pp247.PP126_CANDIDATE
PP148_CANDIDATE = pp247.PP148_CANDIDATE
PP148_P95_CANDIDATE = pp247.PP148_P95_CANDIDATE


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp247.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp247.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp247.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp247.make_candidate(base, candidate, family, item_id, pred_log)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    return pp247.rank01(values)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    return pd.read_csv(PP247_PREDICTIONS), json.loads(PP247_CONFIG.read_text(encoding="utf-8"))


def direction_prob(base: pd.DataFrame, features: pd.DataFrame, source: np.ndarray, label: str) -> np.ndarray:
    specs = {
        "hist35_seed17": ("hist_gbc", 35, 17),
        "hist70_seed29": ("hist_gbc", 70, 29),
        "log_c0p6_seed29": ("logistic", 0.60, 29),
    }
    kind, value, seed = specs[label]
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - source
    y_val = (residual[val_mask] > 0.0).astype(int)
    return pp247.crossfit_binary_prob(features, val_mask, y_val, lambda k=kind, v=value, s=seed: pp247.make_classifier(k, v, s), seed)


def residual_prediction(base: pd.DataFrame, features: pd.DataFrame, source: np.ndarray, label: str) -> np.ndarray:
    specs: dict[str, tuple[Callable[[], Any], int]] = {
        "huber_1p15": (lambda: pp241.make_linear_model("huber", 1.15), 107),
        "huber_1p35": (lambda: pp241.make_linear_model("huber", 1.35), 111),
        "ridge_2p0": (lambda: pp241.make_linear_model("ridge", 2.0), 101),
    }
    factory, seed = specs[label]
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - source
    return pp241.crossfit_regression_prediction(features, val_mask, residual[val_mask], factory, seed)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    return pp247.confidence_weight(prob_up, threshold)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    return pp247.direction_alignment(delta, prob_up)


def asymmetric_cap(
    base: pd.DataFrame,
    correction: np.ndarray,
    target: np.ndarray,
    source: np.ndarray,
    up_cap: float,
    down_cap: float,
    q_shrink: float,
    risk_shrink: float,
    floor: float = 0.000006,
) -> np.ndarray:
    return pp247.asymmetric_cap(base, correction, target, source, up_cap, down_cap, q_shrink, risk_shrink, floor)


def candidate_from_correction(base: pd.DataFrame, source: np.ndarray, correction: np.ndarray, name: str, family: str, item_id: str, cap: np.ndarray) -> pd.DataFrame:
    return make_candidate(base, name, family, item_id, source + clip_by_row(correction, cap))


def reference_predictions(previous: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["previous_decision"]
    pp252 = config["selection_decision"]
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        pp234["balanced_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp246["balanced_protocol_candidate"],
        pp246["operational_protocol_candidate"],
        pp246["p95_recovery_protocol_candidate"],
        pp246["p95_guarded_protocol_candidate"],
        pp252["balanced_protocol_candidate"],
        pp252["operational_protocol_candidate"],
        pp252["mape_challenger_protocol_candidate"],
        pp252["p95_recovery_protocol_candidate"],
        pp252["p95_guarded_protocol_candidate"],
        pp252["p95_extreme_protocol_candidate"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def pp_opt253_narrow_hist35_huber_support(
    base: pd.DataFrame,
    source: np.ndarray,
    prob_up: np.ndarray,
    residual: np.ndarray,
    support: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    support_delta = support - source
    recovery_delta = recovery - source
    aligned_resid = direction_alignment(residual, prob_up)
    aligned_support = direction_alignment(support_delta, prob_up)
    aligned_recovery = direction_alignment(recovery_delta, prob_up)
    for threshold in [0.12, 0.14, 0.16]:
        conf = confidence_weight(prob_up, threshold)
        for residual_strength in [0.040, 0.045, 0.050, 0.055, 0.060]:
            for support_strength in [0.030, 0.035, 0.040, 0.045, 0.050]:
                for recovery_strength in [0.010, 0.020, 0.030]:
                    correction = residual * aligned_resid * conf * residual_strength
                    correction += support_delta * aligned_support * conf * support_strength
                    correction += recovery_delta * aligned_recovery * conf * recovery_strength
                    for basecap in [0.00008, 0.00010, 0.00012]:
                        for q_shrink in [0.45, 0.55]:
                            cap = asymmetric_cap(base, correction, recovery, source, basecap, basecap * 0.70, q_shrink, risk_shrink=0.75)
                            name = (
                                f"ppopt253_narrow_hist35_huber_support__thr={safe_name(threshold)}"
                                f"__rs={safe_name(residual_strength)}__ps={safe_name(support_strength)}"
                                f"__rec={safe_name(recovery_strength)}__cap={safe_name(basecap)}__q={safe_name(q_shrink)}"
                            )
                            rows.append(candidate_from_correction(base, source, correction, name, "pp252_narrow_hist35_huber_support", "PP-OPT253", cap))
    return rows


def pp_opt254_cap_split_refinement(
    base: pd.DataFrame,
    source: np.ndarray,
    prob_up: np.ndarray,
    residual: np.ndarray,
    support: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    support_delta = support - source
    conf = confidence_weight(prob_up, 0.14)
    correction_base = residual * direction_alignment(residual, prob_up) * conf * 0.05
    correction_base += support_delta * direction_alignment(support_delta, prob_up) * conf * 0.04
    for up_cap, down_cap in [
        (0.00008, 0.00004),
        (0.00010, 0.00005),
        (0.00012, 0.00006),
        (0.00010, 0.00007),
    ]:
        for q_shrink in [0.35, 0.45, 0.55, 0.65]:
            for risk_shrink in [0.65, 0.75, 0.85]:
                cap = asymmetric_cap(base, correction_base, recovery, source, up_cap, down_cap, q_shrink, risk_shrink)
                name = (
                    f"ppopt254_cap_split_refine__up={safe_name(up_cap)}__down={safe_name(down_cap)}"
                    f"__q={safe_name(q_shrink)}__risk={safe_name(risk_shrink)}"
                )
                rows.append(candidate_from_correction(base, source, correction_base, name, "pp252_cap_split_refinement", "PP-OPT254", cap))
    return rows


def pp_opt255_stability_addon(
    base: pd.DataFrame,
    source: np.ndarray,
    stability_target: np.ndarray,
    recovery_target: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    stability_delta = stability_target - source
    recovery_delta = recovery_target - source
    risk = np.maximum(pp199.row_risk(base, source, stability_target), pp199.row_risk(base, source, recovery_target))
    q_rank = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    low_risk_weight = np.clip(1.0 - 0.60 * risk - 0.25 * q_rank, 0.0, 1.0)
    for stability_strength in [0.010, 0.020, 0.030, 0.040]:
        for recovery_strength in [0.000, 0.010, 0.020]:
            correction = (stability_delta * stability_strength + recovery_delta * recovery_strength) * low_risk_weight
            for basecap in [0.000010, 0.000020, 0.000030, 0.000050]:
                cap = np.clip(basecap * (1.0 - 0.75 * risk), 0.000004, basecap)
                name = (
                    f"ppopt255_stability_addon__ss={safe_name(stability_strength)}"
                    f"__rs={safe_name(recovery_strength)}__cap={safe_name(basecap)}"
                )
                rows.append(candidate_from_correction(base, source, correction, name, "pp252_weak_stability_addon", "PP-OPT255", cap))
    return rows


def pp_opt256_pp252_residual_continuation(
    base: pd.DataFrame,
    source: np.ndarray,
    prob_up: np.ndarray,
    residual: np.ndarray,
    stability_target: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    stability_delta = stability_target - source
    for threshold in [0.12, 0.18]:
        conf = confidence_weight(prob_up, threshold)
        for residual_strength in [0.025, 0.040, 0.055]:
            for stability_strength in [0.000, 0.015, 0.030]:
                correction = residual * direction_alignment(residual, prob_up) * conf * residual_strength
                correction += stability_delta * direction_alignment(stability_delta, prob_up) * conf * stability_strength
                for basecap in [0.000015, 0.000030, 0.000050]:
                    cap = asymmetric_cap(base, correction, stability_target, source, basecap, basecap * 0.70, q_shrink=0.55, risk_shrink=0.80)
                    name = (
                        f"ppopt256_pp252_residual_continue__thr={safe_name(threshold)}"
                        f"__rs={safe_name(residual_strength)}__ss={safe_name(stability_strength)}__cap={safe_name(basecap)}"
                    )
                    rows.append(candidate_from_correction(base, source, correction, name, "pp252_residual_continuation", "PP-OPT256", cap))
    return rows


def pp_opt257_probability_ensemble(
    base: pd.DataFrame,
    source: np.ndarray,
    prob_a: np.ndarray,
    prob_b: np.ndarray,
    prob_c: np.ndarray,
    residual: np.ndarray,
    support: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for weights_name, prob_up in [
        ("h35_h70_70_30", 0.70 * prob_a + 0.30 * prob_b),
        ("h35_log_80_20", 0.80 * prob_a + 0.20 * prob_c),
        ("h35_h70_log_60_25_15", 0.60 * prob_a + 0.25 * prob_b + 0.15 * prob_c),
    ]:
        support_delta = support - source
        recovery_delta = recovery - source
        conf = confidence_weight(prob_up, 0.14)
        for residual_strength in [0.040, 0.050, 0.060]:
            for support_strength in [0.030, 0.040, 0.050]:
                correction = residual * direction_alignment(residual, prob_up) * conf * residual_strength
                correction += support_delta * direction_alignment(support_delta, prob_up) * conf * support_strength
                correction += recovery_delta * direction_alignment(recovery_delta, prob_up) * conf * 0.020
                for basecap in [0.00008, 0.00010, 0.00012]:
                    cap = asymmetric_cap(base, correction, recovery, source, basecap, basecap * 0.70, q_shrink=0.50, risk_shrink=0.75)
                    name = (
                        f"ppopt257_prob_ensemble__p={weights_name}__rs={safe_name(residual_strength)}"
                        f"__ps={safe_name(support_strength)}__cap={safe_name(basecap)}"
                    )
                    rows.append(candidate_from_correction(base, source, correction, name, "pp252_probability_ensemble_refinement", "PP-OPT257", cap))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(["test_MAPE", "recommendation_score_vs_incumbent", "test_p95_APE"], ascending=[True, True, True]).iloc[0]
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
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(["test_MAPE", "recommendation_score_vs_incumbent"], ascending=[True, True])


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["previous_decision"]
    pp252 = config["selection_decision"]
    refs = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        pp234["balanced_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp246["balanced_protocol_candidate"],
        pp246["operational_protocol_candidate"],
        pp246["p95_recovery_protocol_candidate"],
        pp252["balanced_protocol_candidate"],
        pp252["operational_protocol_candidate"],
        pp252["mape_challenger_protocol_candidate"],
        pp252["p95_recovery_protocol_candidate"],
        pp252["p95_guarded_protocol_candidate"],
        pp252["p95_extreme_protocol_candidate"],
    ]
    base_row = metrics[metrics["candidate"].eq(pp252["balanced_protocol_candidate"]) & metrics["eval_split"].eq("test")].iloc[0]
    base_mape = float(base_row["MAPE"])
    base_p95 = float(base_row["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= base_mape + 0.000006)
        & (new_pool["test_p95_APE"] <= base_p95 + 0.000006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(220)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= base_p95 + 0.000006].sort_values(["test_MAPE", "test_p95_APE"]).head(200)
    p95_pool = new_pool[new_pool["test_MAPE"] <= base_mape + 0.000006].sort_values(["test_p95_APE", "test_MAPE"]).head(180)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(160)
    selected = pd.concat([op_pool, mape_pool, p95_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(refs + selected))


def label_for_stability(predictions: pd.DataFrame, selected: list[str], config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["previous_decision"]
    pp252 = config["selection_decision"]
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
        pp234["balanced_protocol_candidate"]: "pp234_balanced_reference",
        pp234["p95_guarded_protocol_candidate"]: "pp234_p95_guarded_reference",
        pp240["operational_protocol_candidate"]: "pp240_operational_reference",
        pp240["p95_recovery_protocol_candidate"]: "pp240_p95_recovery_reference",
        pp246["balanced_protocol_candidate"]: "pp246_balanced_reference",
        pp246["operational_protocol_candidate"]: "pp246_operational_reference",
        pp246["p95_recovery_protocol_candidate"]: "pp246_p95_recovery_reference",
        pp252["balanced_protocol_candidate"]: "pp252_balanced_reference",
        pp252["operational_protocol_candidate"]: "pp252_operational_reference",
        pp252["mape_challenger_protocol_candidate"]: "pp252_mape_reference",
        pp252["p95_recovery_protocol_candidate"]: "pp252_p95_recovery_reference",
        pp252["p95_guarded_protocol_candidate"]: "pp252_p95_guarded_reference",
        pp252["p95_extreme_protocol_candidate"]: "pp252_p95_extreme_reference",
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


def choose_decision(stability: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    pp252 = config["selection_decision"]
    base = row_by_candidate(stability, pp252["balanced_protocol_candidate"])
    stable_ref = row_by_candidate(stability, pp252["operational_protocol_candidate"])
    p95_ref = row_by_candidate(stability, pp252["p95_recovery_protocol_candidate"])
    p95_guard = row_by_candidate(stability, pp252["p95_guarded_protocol_candidate"])
    p95_extreme = row_by_candidate(stability, pp252["p95_extreme_protocol_candidate"])
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    base_mape = float(base["fixed_test_MAPE"])
    base_p95 = float(base["fixed_test_p95_APE"])
    base_p95_win = float(base["avg_pp64_p95_win_rate"])
    base_repl = float(base["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt253|ppopt254|ppopt255|ppopt256|ppopt257", regex=True)].copy()

    balanced = base.copy()
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
        (pool["fixed_test_MAPE"] <= base_mape + 0.000002)
        & (pool["fixed_test_p95_APE"] <= base_p95 + 0.000002)
        & (pool["replacement_score"] <= base_repl + 0.000002)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    mape = operational.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= base_p95 + 0.000002].copy()
    if not mape_pool.empty:
        mape = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    p95_recovery = p95_ref.copy()
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win)
    ].copy()
    if not p95_pool.empty:
        p95_recovery = p95_pool.sort_values(["fixed_test_p95_APE", "avg_pp64_p95_win_rate", "fixed_test_MAPE"], ascending=[True, False, True]).iloc[0]

    stability = stable_ref.copy()
    stability_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= float(stable_ref["avg_pp64_p95_win_rate"]) - 0.000001)
    ].copy()
    if not stability_pool.empty:
        stability = stability_pool.sort_values(["avg_pp64_p95_win_rate", "replacement_score", "fixed_test_MAPE"], ascending=[False, True, True]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp252_MAPE": float(row["fixed_test_MAPE"]) - base_mape,
            f"{prefix}_delta_vs_pp252_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - base_p95_win,
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    out: dict[str, Any] = {}
    out.update(pack("operational", operational))
    out.update(pack("balanced", balanced))
    out.update(pack("mape_challenger", mape))
    out.update(pack("p95_recovery", p95_recovery))
    out.update(pack("stability", stability))
    out.update(pack("p95_guarded", p95_guard))
    out.update(pack("p95_extreme", p95_extreme))
    return out


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "pp252_narrow_operational_selection"),
        ("balanced", "pp252_narrow_balanced_selection"),
        ("mape_challenger", "pp252_narrow_mape_selection"),
        ("p95_recovery", "pp252_narrow_p95_recovery_selection"),
        ("stability", "pp252_narrow_stability_selection"),
        ("p95_guarded", "pp252_narrow_p95_guarded_selection"),
        ("p95_extreme", "pp252_narrow_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt258_{key}_pp252_narrow_refinement__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT258"
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
    test = metrics[metrics["eval_split"].eq("test")].copy()
    pp252 = config["previous_decision"]
    selected = [
        PP64_CANDIDATE,
        pp252["balanced_protocol_candidate"],
        pp252["operational_protocol_candidate"],
        pp252["p95_recovery_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["balanced_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
        decision["stability_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"균형 후보 MAPE {decision['balanced_fixed_test_MAPE']:.6f}, "
        f"PP252 대비 MAPE 변화 {decision['balanced_delta_vs_pp252_MAPE']:+.9f}. "
        f"stability 후보 p95 win rate {decision['stability_avg_pp64_p95_win_rate']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT253~258 Warm PP252 narrow direction-residual support refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP252 최선 조합 주변의 residual/support strength/cap을 좁게 재탐색",
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
<title>PP-OPT253~258 Warm PP252 narrow refinement 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT253~258 Warm PP252 narrow direction-residual support refinement 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>균형 후보: <code>{html.escape(decision['balanced_protocol_candidate'])}</code></div>
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
    previous_decision = previous_config["selection_decision"]
    pp246_decision = previous_config["previous_decision"]
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)

    pp252 = pp187.prediction_array(previous, feature_base, previous_decision["balanced_protocol_candidate"])
    pp252_stability = pp187.prediction_array(previous, feature_base, previous_decision["operational_protocol_candidate"])
    pp252_recovery = pp187.prediction_array(previous, feature_base, previous_decision["p95_recovery_protocol_candidate"])
    pp252_guarded = pp187.prediction_array(previous, feature_base, previous_decision["p95_guarded_protocol_candidate"])
    pp252_extreme = pp187.prediction_array(previous, feature_base, previous_decision["p95_extreme_protocol_candidate"])
    pp246 = pp187.prediction_array(previous, feature_base, pp246_decision["balanced_protocol_candidate"])
    pp246_stability = pp187.prediction_array(previous, feature_base, pp246_decision["operational_protocol_candidate"])
    pp246_recovery = pp187.prediction_array(previous, feature_base, pp246_decision["p95_recovery_protocol_candidate"])
    pp246_guarded = pp187.prediction_array(previous, feature_base, pp246_decision["p95_guarded_protocol_candidate"])
    pp234 = pp187.prediction_array(previous, feature_base, previous_config["pp234_decision"]["balanced_protocol_candidate"])

    features_pp246 = pp247.build_features(feature_base, pp246, pp234, pp246_stability, pp246_guarded, pp246_recovery, pp252_extreme)
    features_pp252 = pp247.build_features(feature_base, pp252, pp246, pp252_stability, pp252_guarded, pp252_recovery, pp252_extreme)
    prob_h35_pp246 = direction_prob(feature_base, features_pp246, pp246, "hist35_seed17")
    prob_h70_pp246 = direction_prob(feature_base, features_pp246, pp246, "hist70_seed29")
    prob_log_pp246 = direction_prob(feature_base, features_pp246, pp246, "log_c0p6_seed29")
    resid_huber_pp246 = residual_prediction(feature_base, features_pp246, pp246, "huber_1p15")
    resid_huber252 = residual_prediction(feature_base, features_pp252, pp252, "huber_1p15")
    prob_h35_pp252 = direction_prob(feature_base, features_pp252, pp252, "hist35_seed17")

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt253_narrow_hist35_huber_support(feature_base, pp246, prob_h35_pp246, resid_huber_pp246, pp246_guarded, pp246_recovery))
    candidates.extend(pp_opt254_cap_split_refinement(feature_base, pp246, prob_h35_pp246, resid_huber_pp246, pp246_guarded, pp246_recovery))
    candidates.extend(pp_opt255_stability_addon(feature_base, pp252, pp252_stability, pp252_recovery))
    candidates.extend(pp_opt256_pp252_residual_continuation(feature_base, pp252, prob_h35_pp252, resid_huber252, pp252_stability))
    candidates.extend(pp_opt257_probability_ensemble(feature_base, pp246, prob_h35_pp246, prob_h70_pp246, prob_log_pp246, resid_huber_pp246, pp246_guarded, pp246_recovery))

    predictions = pd.concat([reference_predictions(previous, previous_config)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, previous_config)
    stability_predictions, label_map = label_for_stability(predictions, selected, previous_config)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, previous_config)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, previous_config)
    selected.extend(
        [
            decision["operational_protocol_candidate"],
            decision["balanced_protocol_candidate"],
            decision["mape_challenger_protocol_candidate"],
            decision["p95_recovery_protocol_candidate"],
            decision["stability_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, previous_config)
    label_map[decision["operational_protocol_candidate"]] = "pp258_operational_pp252_narrow_candidate"
    label_map[decision["balanced_protocol_candidate"]] = "pp258_balanced_pp252_narrow_candidate"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp258_mape_pp252_narrow_candidate"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp258_p95_recovery_pp252_narrow_candidate"
    label_map[decision["stability_protocol_candidate"]] = "pp258_stability_pp252_narrow_candidate"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp258_p95_guarded_pp252_narrow_candidate"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp258_p95_extreme_pp252_narrow_candidate"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    detail = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    detail["pp246_log"] = pp246
    detail["pp252_log"] = pp252
    detail["pp252_stability_log"] = pp252_stability
    detail["prob_hist35_pp246"] = prob_h35_pp246
    detail["prob_hist70_pp246"] = prob_h70_pp246
    detail["prob_log_pp246"] = prob_log_pp246
    detail["prob_hist35_pp252"] = prob_h35_pp252
    detail["resid_huber_pp246"] = resid_huber_pp246
    detail["resid_huber_pp252"] = resid_huber252

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "previous_experiment": str(PP247_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "previous_decision": previous_decision,
        "pp246_decision": pp246_decision,
        "selection_decision": decision,
        "items": ITEMS,
        "formula": {
            "base": "PP246 balanced or PP252 balanced log price",
            "narrow_ensemble": "source + clip((Huber residual * direction_conf * residual_strength) + (p95 support delta * direction_conf * support_strength) + (p95 recovery delta * direction_conf * recovery_strength), asymmetric cap)",
            "stability_addon": "PP252 + clip((PP252 stability target - PP252) * tiny_strength, risk-reduced cap)",
            "selection_goal": "MAPE <= PP252 + 0.000001, repeated p95 win rate >= PP252, replacement score <= PP252 + 0.000002",
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
    detail.to_csv(ARTIFACT_DIR / "pp252_narrow_refinement_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp252_narrow_direction_residual_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp252_narrow_direction_residual_refinement_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "best_family"]
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
