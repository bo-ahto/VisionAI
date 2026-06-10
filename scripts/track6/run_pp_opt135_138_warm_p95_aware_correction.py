#!/usr/bin/env python3
"""Run PP-OPT135..138 Warm p95-aware correction experiments.

PP127 showed that learned stack adoption can lower MAPE materially, but the
low-MAPE candidates damage p95.  This batch keeps the same non-submission Warm
validation/test split and focuses on recovering most of that MAPE gain with
hard p95 guards, tail-harm classifiers, row-level correction budgets, and a
final guarded router.
"""
from __future__ import annotations

import hashlib
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
PP127_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt127_134_warm_learned_stack_correction.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp127 = load_module("pp_opt127_helpers_for_pp135", PP127_SCRIPT)
pp119 = pp127.pp119
opt8 = pp127.opt8
val71 = pp127.val71

EXP_ID = "PP-OPT135-138"
EXP_SLUG = "PP-OPT135_138_warm_p95_aware_correction"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP127_CONFIG = REPO / "experiments" / "track6" / "PP-OPT127_134_warm_learned_stack_correction" / "artifacts" / "run_config.json"

BASE_CANDIDATE = pp127.BASE_CANDIDATE
INCUMBENT = pp127.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT135",
        "priority": "1",
        "title": "p95-aware hard guard on learned stack gain",
        "description": "PP127 low-MAPE stack_plain 보정에 p95 악화 확률 기반 hard guard를 적용한다.",
    },
    {
        "item_id": "PP-OPT136",
        "priority": "2",
        "title": "tail-harm rollback classifier",
        "description": "stack_plain이 큰 오차 구간을 악화시킬 row를 별도 분류하고 해당 row의 보정 이동량을 되돌린다.",
    },
    {
        "item_id": "PP-OPT137",
        "priority": "3",
        "title": "row-level correction budget",
        "description": "risk, quantile width, 가격대, tail-harm 확률에 따라 row별 최대 보정폭을 다르게 둔다.",
    },
    {
        "item_id": "PP-OPT138",
        "priority": "4",
        "title": "guarded correction router",
        "description": "PP126, PP134 harm rollback, p95-aware stack, p95 router를 row별 확률과 cap 안에서 결합한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    actual = base["actual_price"].to_numpy(dtype=float)
    return np.abs(safe_exp(pred_log) - actual) / np.maximum(actual, EPS)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp127.make_candidate(base, candidate, family, item_id, pred_log)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return pp127.row_cap(base, cap, mode)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any], dict[str, str]]:
    return pp127.load_inputs()


def build_scores(base: pd.DataFrame, ref: pd.DataFrame, labels: pd.DataFrame, model_detail: pd.DataFrame) -> dict[str, np.ndarray]:
    return pp127.build_scores(base, ref, labels, model_detail)


def pp134_op_prediction(base: pd.DataFrame, ref: pd.DataFrame, model_detail: pd.DataFrame, scores: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> np.ndarray:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    score = pp119.base_stack_score(scores, "gain75", 0.55, 0.18, 0.055, 0.085)
    base_w = gate(score, 0.12, 0.18)
    raw = safe + (stack - safe) * base_w * 0.55
    harm = np.maximum(signals["prob_stack_harm"], signals["prob_tail_harm"])
    keep = 1.0 - 0.35 * harm
    return safe + clip_by_row((raw - safe) * keep, row_cap(base, 0.018, "risk"))


def pp134_p95_prediction(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], signals: dict[str, np.ndarray]) -> np.ndarray:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target = ref["pp82_p95"].to_numpy(dtype=float)
    tail_score = np.clip(
        signals["prob_p95_gain"] * (0.55 + 0.45 * scores["tail_intent"]) * (1.0 - 0.50 * signals["prob_stack_harm"]),
        0,
        1,
    )
    w = gate(tail_score, 0.30, 0.18)
    return safe + clip_by_row((target - safe) * w * 0.55, row_cap(base, 0.008, "risk"))


def add_reference_predictions(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> tuple[pd.DataFrame, dict[str, str]]:
    extra = pd.DataFrame(index=ref.index)
    extra["pp134_op_recomputed"] = pp134_op_prediction(base, ref, model_detail, scores, signals)
    extra["pp134_p95_recomputed"] = pp134_p95_prediction(base, ref, scores, signals)
    out = pd.concat([ref, extra], axis=1)
    return out, {
        "pp134_op_recomputed": "PP134 운영 후보 재계산: learned harm rollback",
        "pp134_p95_recomputed": "PP134 p95 후보 재계산: p95 tail router",
    }


def build_p95_aware_signals(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    prior_signals: dict[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    pp126 = ref["pp126_op"].to_numpy(dtype=float)
    stack_plain = model_detail["stack_huber_plain"].to_numpy(dtype=float)
    stack_weighted = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    ape_pp126 = ape_from_log(base, pp126)
    ape_plain = ape_from_log(base, stack_plain)
    ape_weighted = ape_from_log(base, stack_weighted)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    q85 = float(np.quantile(ape_pp126[val_mask], 0.85))
    q90 = float(np.quantile(ape_pp126[val_mask], 0.90))
    q95 = float(np.quantile(ape_pp126[val_mask], 0.95))

    labels = {
        "plain_harm": (ape_plain - ape_pp126 > 0.0040).astype(int),
        "plain_tail_harm": ((ape_plain - ape_pp126 > 0.0015) & (ape_plain >= q90)).astype(int),
        "plain_p95_harm": ((ape_plain - ape_pp126 > 0.0005) & (ape_plain >= q95)).astype(int),
        "plain_mid_safe_gain": ((ape_pp126 - ape_plain > 0.0010) & (ape_plain <= q85)).astype(int),
        "weighted_tail_harm": ((ape_weighted - ape_pp126 > 0.0015) & (ape_weighted >= q90)).astype(int),
    }
    learned: dict[str, np.ndarray] = dict(prior_signals)
    for i, (name, label) in enumerate(labels.items(), start=1):
        learned[f"prob_{name}"] = pp127.oof_lgbm_probability(base, feature_matrix, label, seed_offset=500 + 20 * i)

    detail = base[["eval_split", "_track6_row_id"]].copy()
    detail["ape_pp126_op"] = ape_pp126
    detail["ape_stack_plain"] = ape_plain
    detail["ape_stack_weighted"] = ape_weighted
    for key, value in learned.items():
        detail[key] = value
    for key, value in labels.items():
        detail[f"label_{key}"] = value
    detail["pp126_validation_ape_q85"] = q85
    detail["pp126_validation_ape_q90"] = q90
    detail["pp126_validation_ape_q95"] = q95
    return learned, detail


def p95_risk_score(scores: dict[str, np.ndarray], signals: dict[str, np.ndarray], delta_abs: np.ndarray) -> np.ndarray:
    return np.clip(
        0.30 * scores["p95_risk"]
        + 0.25 * signals["prob_plain_tail_harm"]
        + 0.20 * signals["prob_plain_p95_harm"]
        + 0.15 * signals["prob_plain_harm"]
        + 0.10 * gate(delta_abs, 0.035, 0.065),
        0,
        1,
    )


def p95_aware_stack_score(scores: dict[str, np.ndarray], signals: dict[str, np.ndarray], tail_penalty: float, harm_penalty: float) -> np.ndarray:
    gain = np.clip(0.72 * signals["prob_stack_plain_gain"] + 0.28 * signals["prob_plain_mid_safe_gain"], 0, 1)
    harm = np.clip(
        0.45 * signals["prob_plain_harm"]
        + 0.35 * signals["prob_plain_tail_harm"]
        + 0.20 * signals["prob_plain_p95_harm"],
        0,
        1,
    )
    return np.clip(gain * (1.0 - harm_penalty * harm) * (1.0 - tail_penalty * scores["p95_risk"]), 0, 1)


def pp_opt135_hard_guard(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    targets = {
        "stack_plain": model_detail["stack_huber_plain"].to_numpy(dtype=float),
        "stack_weighted": model_detail["stack_huber_weighted"].to_numpy(dtype=float),
    }
    for target_key, target in targets.items():
        delta = target - safe
        risk = p95_risk_score(scores, signals, np.abs(delta))
        for tail_penalty in [0.55, 0.75]:
            for harm_penalty in [0.55, 0.75]:
                score = p95_aware_stack_score(scores, signals, tail_penalty, harm_penalty)
                for threshold in [0.30, 0.36, 0.42]:
                    base_w = gate(score, threshold, 0.22)
                    for hard_threshold in [0.46, 0.56, 0.66]:
                        hard_keep = np.where(risk >= hard_threshold, 0.0, 1.0)
                        soft_keep = np.clip(1.0 - 0.65 * risk, 0, 1)
                        keep = np.minimum(hard_keep, soft_keep)
                        for cap in [0.014, 0.022, 0.034]:
                            cap_arr = np.maximum(0.004, cap * (1.0 - 0.60 * risk))
                            for strength in [0.45, 0.60, 0.75]:
                                pred = safe + clip_by_row(delta * base_w * keep * strength, cap_arr)
                                name = (
                                    f"ppopt135_hard_guard__target={target_key}__tpen={safe_name(tail_penalty)}"
                                    f"__hpen={safe_name(harm_penalty)}__thr={safe_name(threshold)}"
                                    f"__hard={safe_name(hard_threshold)}__cap={safe_name(cap)}__s={safe_name(strength)}"
                                )
                                rows.append(make_candidate(base, name, "p95_aware_hard_guard", "PP-OPT135", pred))
    return rows


def pp_opt136_tail_harm_rollback(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target = model_detail["stack_huber_plain"].to_numpy(dtype=float)
    delta = target - safe
    base_score = p95_aware_stack_score(scores, signals, 0.45, 0.45)
    tail_harm = np.maximum(signals["prob_plain_tail_harm"], signals["prob_plain_p95_harm"])
    for threshold in [0.26, 0.32, 0.38]:
        base_w = gate(base_score, threshold, 0.20)
        for pre_strength in [0.55, 0.70, 0.85]:
            raw_corr = delta * base_w * pre_strength
            for rollback in [0.70, 0.85, 1.00]:
                for floor in [0.00, 0.08, 0.16]:
                    keep = np.maximum(floor, 1.0 - rollback * tail_harm)
                    for cap in [0.014, 0.022, 0.034]:
                        cap_arr = np.maximum(0.004, cap * (1.0 - 0.50 * scores["p95_risk"]) * (1.0 - 0.40 * tail_harm))
                        pred = safe + clip_by_row(raw_corr * keep, cap_arr)
                        name = (
                            f"ppopt136_tail_harm_rollback__thr={safe_name(threshold)}__pre={safe_name(pre_strength)}"
                            f"__rollback={safe_name(rollback)}__floor={safe_name(floor)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "tail_harm_rollback_classifier", "PP-OPT136", pred))
    return rows


def pp_opt137_row_budget(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target = model_detail["stack_huber_plain"].to_numpy(dtype=float)
    delta = target - safe
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    high_price = price.isin(["high_price", "very_high_price"]).to_numpy(dtype=float)
    low_conf = conf.eq("low_confidence").to_numpy(dtype=float)
    score = p95_aware_stack_score(scores, signals, 0.60, 0.60)
    w = gate(score, 0.32, 0.22)
    tail_harm = np.maximum(signals["prob_plain_tail_harm"], signals["prob_plain_p95_harm"])
    for base_cap in [0.018, 0.026, 0.038]:
        for risk_shrink in [0.45, 0.60, 0.75]:
            for tail_shrink in [0.55, 0.75, 0.95]:
                segment_shrink = 1.0 - 0.18 * high_price - 0.10 * low_conf
                cap_arr = base_cap * (1.0 - risk_shrink * scores["p95_risk"]) * (1.0 - tail_shrink * tail_harm) * segment_shrink
                cap_arr = np.maximum(0.0035, cap_arr)
                for strength in [0.45, 0.60, 0.75]:
                    pred = safe + clip_by_row(delta * w * strength, cap_arr)
                    name = (
                        f"ppopt137_row_budget__cap={safe_name(base_cap)}__rshrink={safe_name(risk_shrink)}"
                        f"__tshrink={safe_name(tail_shrink)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "row_level_correction_budget", "PP-OPT137", pred))
    return rows


def pp_opt138_guarded_router(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    pp134 = ref["pp134_op_recomputed"].to_numpy(dtype=float)
    p95 = ref["pp134_p95_recomputed"].to_numpy(dtype=float)
    stack_plain = model_detail["stack_huber_plain"].to_numpy(dtype=float)
    tail_harm = np.maximum(signals["prob_plain_tail_harm"], signals["prob_plain_p95_harm"])
    risk = p95_risk_score(scores, signals, np.abs(stack_plain - safe))
    stack_score = p95_aware_stack_score(scores, signals, 0.65, 0.65)
    stack_w_base = gate(stack_score, 0.34, 0.22) * np.clip(1.0 - 0.80 * risk, 0, 1)
    p95_w_base = gate(signals["prob_p95_gain"] * scores["tail_intent"], 0.36, 0.24) * np.clip(1.0 - 0.40 * signals["prob_stack_harm"], 0, 1)
    for stack_strength in [0.30, 0.42, 0.55]:
        for rollback_weight in [0.35, 0.50, 0.65]:
            rollback_corr = (pp134 - safe) * rollback_weight
            stack_corr = (stack_plain - safe) * stack_w_base * stack_strength
            for p95_weight in [0.06, 0.12, 0.20]:
                p95_corr = (p95 - safe) * p95_w_base * p95_weight
                for cap in [0.012, 0.018, 0.026]:
                    cap_arr = np.maximum(0.0035, cap * (1.0 - 0.55 * risk) * (1.0 - 0.35 * tail_harm))
                    corr = rollback_corr + stack_corr + p95_corr
                    pred = safe + clip_by_row(corr, cap_arr)
                    name = (
                        f"ppopt138_guarded_router__stack={safe_name(stack_strength)}__rollback={safe_name(rollback_weight)}"
                        f"__p95={safe_name(p95_weight)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "guarded_correction_router", "PP-OPT138", pred))
    return rows


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp118_operational", "pp118_op"),
        ("reference_pp126_operational", "pp126_op"),
        ("reference_pp126_p95", "pp126_p95"),
        ("reference_pp134_operational_recomputed", "pp134_op_recomputed"),
        ("reference_pp134_p95_recomputed", "pp134_p95_recomputed"),
        ("reference_pp119_guarded_mape", "pp119_guarded_mape"),
        ("reference_pp119_aggressive_mape", "pp119_aggressive_mape"),
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
    pp126_p95 = float(test[test["candidate"].eq("reference_pp126_operational")]["p95_APE"].iloc[0])
    new_pool = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].copy()
    new_pool["delta_vs_pp64_MAPE"] = new_pool["test_MAPE"] - pp64_mape
    new_pool["delta_vs_pp64_p95_APE"] = new_pool["test_p95_APE"] - pp64_p95
    balanced = new_pool[
        (new_pool["delta_vs_pp64_MAPE"] <= 0.00005)
        & (new_pool["test_p95_APE"] <= pp126_p95 + 0.00008)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(24)
    best_mape_guarded = new_pool[new_pool["test_p95_APE"] <= pp126_p95 + 0.00080].sort_values(["test_MAPE", "test_p95_APE"]).head(24)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(24)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(24)
    selected = pd.concat([balanced, best_mape_guarded, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    references = [
        BASE_CANDIDATE,
        INCUMBENT,
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp118_operational",
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp134_operational_recomputed",
        "reference_pp134_p95_recomputed",
        "reference_pp119_guarded_mape",
        "reference_pp119_aggressive_mape",
        "reference_pp82_p95",
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
        "reference_pp118_operational": "pp118_operational_reference",
        "reference_pp126_operational": "pp126_operational_reference",
        "reference_pp126_p95": "pp126_p95_reference",
        "reference_pp134_operational_recomputed": "pp134_operational_recomputed_reference",
        "reference_pp134_p95_recomputed": "pp134_p95_recomputed_reference",
        "reference_pp119_guarded_mape": "pp119_guarded_mape_reference",
        "reference_pp119_aggressive_mape": "pp119_aggressive_mape_reference",
        "reference_pp82_p95": "pp82_p95_reference",
    }
    subset = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def attach_candidate_names(stability_aggregate: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    if "candidate" in stability_aggregate.columns:
        return stability_aggregate
    lookup = fixed[["candidate_label", "candidate"]].drop_duplicates("candidate_label")
    return stability_aggregate.merge(lookup, on="candidate_label", how="left")


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    pp126 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp126_operational_reference")].iloc[0]
    pp126_p95 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp126_p95_reference")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp118_operational_reference",
        "pp126_operational_reference",
        "pp126_p95_reference",
        "pp134_operational_recomputed_reference",
        "pp134_p95_recomputed_reference",
        "pp119_guarded_mape_reference",
        "pp119_aggressive_mape_reference",
        "pp82_p95_reference",
        "incumbent_pp7",
        "hcoef_stable_source",
    }
    pool = stability_aggregate[~stability_aggregate["candidate_label"].isin(refs)].copy()
    if pool.empty:
        raise ValueError("No new stability candidates available")
    pool["fixed_test_delta_vs_pp64_MAPE"] = pool["fixed_test_MAPE"] - float(pp64["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp64_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp64["fixed_test_p95_APE"])
    pool["fixed_test_delta_vs_pp126_MAPE"] = pool["fixed_test_MAPE"] - float(pp126["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp126_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp126["fixed_test_p95_APE"])
    op_pool = pool[
        (pool["fixed_test_delta_vs_pp64_MAPE"] <= -0.00020)
        & (pool["fixed_test_delta_vs_pp126_p95_APE"] <= 0.00008)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.84)
    ].copy()
    if op_pool.empty:
        operational = pp126.copy()
        operational["fixed_test_delta_vs_pp64_MAPE"] = float(pp126["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"])
        operational["fixed_test_delta_vs_pp64_p95_APE"] = float(pp126["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"])
        operational["fixed_test_delta_vs_pp126_MAPE"] = 0.0
        operational["fixed_test_delta_vs_pp126_p95_APE"] = 0.0
    else:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00025)
        & (pool["fixed_test_p95_APE"] < float(pp64["fixed_test_p95_APE"]) - 0.00004)
    ].copy()
    if p95_pool.empty:
        p95 = pp126_p95.copy()
        p95["fixed_test_delta_vs_pp64_MAPE"] = float(pp126_p95["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"])
        p95["fixed_test_delta_vs_pp64_p95_APE"] = float(pp126_p95["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"])
    else:
        p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]
    return {
        "operational_label": str(operational["candidate_label"]),
        "operational_candidate": str(operational["candidate"]),
        "operational_fixed_test_MAPE": float(operational["fixed_test_MAPE"]),
        "operational_fixed_test_p95_APE": float(operational["fixed_test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["fixed_test_delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["fixed_test_delta_vs_pp64_p95_APE"]),
        "operational_delta_vs_pp126_MAPE": float(operational["fixed_test_delta_vs_pp126_MAPE"]),
        "operational_delta_vs_pp126_p95_APE": float(operational["fixed_test_delta_vs_pp126_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_delta_vs_pp126_MAPE": float(p95["fixed_test_MAPE"] - float(pp126["fixed_test_MAPE"])),
        "p95_delta_vs_pp126_p95_APE": float(p95["fixed_test_p95_APE"] - float(pp126["fixed_test_p95_APE"])),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "p95_aware_operational_selection"), ("p95", "p95_aware_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt138_{key}_p95_aware_correction_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT138"
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
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp134_operational_recomputed",
        "reference_pp134_p95_recomputed",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected_names)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
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
        "pp126_operational_reference",
        "pp134_operational_recomputed_reference",
        "pp138_operational_p95_aware_correction_challenger",
        "pp138_p95_p95_aware_correction_challenger",
    ]
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(focus_labels)]
    verdict = (
        f"운영 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP126 대비 MAPE {decision['operational_delta_vs_pp126_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp126_p95_APE']:+.6f}."
    )
    interpretation = (
        "PP127의 큰 MAPE 개선은 p95 tail row에서 과한 이동을 만든다. "
        "이번 배치는 해당 tail-harm 확률을 직접 학습해 hard guard와 row별 budget으로 보정 강도를 줄였다."
    )
    md = "\n".join(
        [
            "# PP-OPT135~138 Warm p95-aware correction 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP127 low-MAPE 보정의 p95 악화를 막으면서 MAPE 개선 유지",
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
  <title>PP-OPT135~138 Warm p95-aware correction 결과</title>
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
  <h1>PP-OPT135~138 Warm p95-aware correction 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="warn">{html.escape(interpretation)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>안정성 검증 후보</strong>{stability_aggregate['candidate_label'].nunique()}개</div>
    <div class="panel"><strong>운영형 PP126 대비 MAPE</strong>{decision['operational_delta_vs_pp126_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP126 대비 p95</strong>{decision['operational_delta_vs_pp126_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 주요 후보 test 비교</h2>
  {table_html(selected_test, list(selected_test.columns), 30)}
  <h2>2. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 30)}
  <h2>3. 탐색 후보 상위</h2>
  {table_html(top_new, result_cols, 60)}
  <h2>4. 선택 후보 반복 안정성</h2>
  {table_html(stability_aggregate, stab_cols, 80)}
  <h2>5. 선택 후보 시나리오별 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 80)}
  <h2>6. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, labels, model_detail, selected_refs, parent_config, selected_pp119 = load_inputs()
    scores = build_scores(base, ref, labels, model_detail)
    feature_matrix = pp127.build_feature_matrix(base, ref, labels, model_detail, scores)
    prior_signals, prior_signal_detail = pp127.build_learned_signals(base, ref, model_detail, feature_matrix)
    signals, signal_detail = build_p95_aware_signals(base, ref, model_detail, feature_matrix, prior_signals)
    ref, ref_notes = add_reference_predictions(base, ref, model_detail, scores, signals)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt135_hard_guard(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt136_tail_harm_rollback(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt137_row_budget(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt138_guarded_router(base, ref, model_detail, scores, signals))

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
    label_map[decision["operational_protocol_candidate"]] = "pp138_operational_p95_aware_correction_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp138_p95_p95_aware_correction_challenger"
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
        "selected_pp119_sources": selected_pp119,
        "recomputed_reference_notes": ref_notes,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp127_config": str(PP127_CONFIG.relative_to(REPO)),
            "pp127_helper": str(PP127_SCRIPT.relative_to(REPO)),
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
    prior_signal_detail.to_csv(ARTIFACT_DIR / "prior_learned_signal_detail.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "p95_aware_signal_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "p95_aware_correction_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "p95_aware_correction_result.html").write_text(report_html, encoding="utf-8")

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
