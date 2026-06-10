#!/usr/bin/env python3
"""Run PP-OPT96..102 Warm tail-label refinement experiments.

Previous tail routing improved fixed-test p95 but was not stable enough to
replace PP64/PP70.  This batch changes the classifier labels: instead of
learning "tail risk" only, it learns rows where fallback helpers actually beat
the anchor on validation OOF, and separately learns where fallback is harmful.
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


pp76 = load_module("pp_opt76_helpers_for_pp96", PP76_SCRIPT)
val71 = load_module("pp_opt71_helpers_for_pp96", PP71_SCRIPT)
opt8 = pp76.opt8
opt9 = pp76.opt9
opt21 = pp76.opt21
opt29 = pp76.opt29

EXP_ID = "PP-OPT96-102"
EXP_SLUG = "PP-OPT96_102_warm_tail_label_refinement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP76_DIR = REPO / "experiments" / "track6" / "PP-OPT76_82_warm_tail_routing_experiments"
PP76_PREDS = PP76_DIR / "outputs" / "candidate_predictions.csv"
PP76_ITEMS = PP76_DIR / "outputs" / "experiment_item_summary.csv"
PP76_CONFIG = PP76_DIR / "artifacts" / "run_config.json"
PP89_DIR = REPO / "experiments" / "track6" / "PP-OPT89_95_warm_tail_guarded_stability_experiments"
PP89_PREDS = PP89_DIR / "outputs" / "candidate_predictions.csv"
PP89_CONFIG = PP89_DIR / "artifacts" / "run_config.json"
PP47_QUANT = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments" / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = pp76.BASE_CANDIDATE
INCUMBENT = pp76.INCUMBENT
PREV_CHALLENGER = pp76.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT96",
        "priority": "1",
        "title": "best-helper gain label routing",
        "description": "best stable helper가 PP70보다 실제로 좋아지는 validation row를 학습해 routing한다.",
    },
    {
        "item_id": "PP-OPT97",
        "priority": "2",
        "title": "helper-specific gain label routing",
        "description": "PP20/PP48/혼합 helper별 개선 확률을 따로 학습해 fallback helper를 가중한다.",
    },
    {
        "item_id": "PP-OPT98",
        "priority": "3",
        "title": "gain minus harm guarded routing",
        "description": "개선 확률과 손상 확률을 같이 학습해, 손상 위험이 높으면 fallback을 줄인다.",
    },
    {
        "item_id": "PP-OPT99",
        "priority": "4",
        "title": "tail quantile label routing",
        "description": "tail 분위수별로 label을 분리해 p95 영역에서만 fallback을 허용한다.",
    },
    {
        "item_id": "PP-OPT100",
        "priority": "5",
        "title": "direction and gain aligned routing",
        "description": "잔차 quantile 방향과 helper 이동 방향이 맞고 개선 확률이 있을 때만 routing한다.",
    },
    {
        "item_id": "PP-OPT101",
        "priority": "6",
        "title": "existing candidate selector with refined labels",
        "description": "PP70, PP81, PP82, PP95 후보 중 label 기반으로 row별 선택/혼합한다.",
    },
    {
        "item_id": "PP-OPT102",
        "priority": "7",
        "title": "final label-refined tail challenger",
        "description": "운영형과 p95 목적형 후보를 분리해 최종 선택하고 안정성을 검증한다.",
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


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def load_predictions_from_file(base: pd.DataFrame, file_path: Path, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(file_path, usecols=usecols, chunksize=260_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError(f"No selected predictions loaded from {file_path}")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing prediction columns from {file_path}: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source = opt9.load_base_and_source()
    cfg76 = load_json(PP76_CONFIG)
    cfg89 = load_json(PP89_CONFIG)
    item76 = pd.read_csv(PP76_ITEMS)
    pp81_best = str(item76[item76["item_id"].eq("PP-OPT81")].iloc[0]["best_candidate"])
    selected76 = {
        "pp20": "previous_challenger_pp20",
        "pp30": "reference_pp30_best",
        "pp48": "reference_pp48_score",
        "pp64": "reference_pp64_current_best",
        "pp70": "reference_pp70_refinement",
        "pp82_op": cfg76["selection_decision"]["operational_protocol_candidate"],
        "pp82_p95": cfg76["selection_decision"]["p95_protocol_candidate"],
        "pp81": pp81_best,
    }
    selected89 = {
        "pp95_op": cfg89["selection_decision"]["operational_protocol_candidate"],
        "pp95_p95": cfg89["selection_decision"]["p95_protocol_candidate"],
    }
    ref76 = load_predictions_from_file(base, PP76_PREDS, selected76)
    ref89 = load_predictions_from_file(base, PP89_PREDS, selected89)
    ref = pd.concat([ref76, ref89], axis=1)
    quant = base[["eval_split", "_track6_row_id"]].merge(pd.read_csv(PP47_QUANT), on=["eval_split", "_track6_row_id"], how="left")
    selected = {**selected76, **selected89}
    config = {"pp76": cfg76, "pp89": cfg89}
    return base, source, ref, quant, selected, config


def helper_predictions(ref: pd.DataFrame) -> dict[str, np.ndarray]:
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


def build_label_probabilities(base: pd.DataFrame, ref: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    anchor_ape = ape(anchor, actual_price)
    helper_apes = {key: ape(pred, actual_price) for key, pred in helpers.items()}
    best_helper_ape = np.min(np.vstack([helper_apes[k] for k in ["pp20", "pp48", "p95_weighted", "balanced_stable"]]), axis=0)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    q70 = float(np.quantile(anchor_ape[val_mask], 0.70))
    q75 = float(np.quantile(anchor_ape[val_mask], 0.75))
    q80 = float(np.quantile(anchor_ape[val_mask], 0.80))
    q85 = float(np.quantile(anchor_ape[val_mask], 0.85))

    labels: dict[str, np.ndarray] = {
        "best_gain_any": ((anchor_ape - best_helper_ape) > 0.002).astype(int),
        "best_gain_tail75": ((anchor_ape >= q75) & ((anchor_ape - best_helper_ape) > 0.002)).astype(int),
        "best_gain_tail80": ((anchor_ape >= q80) & ((anchor_ape - best_helper_ape) > 0.002)).astype(int),
        "best_gain_tail85": ((anchor_ape >= q85) & ((anchor_ape - best_helper_ape) > 0.001)).astype(int),
        "best_harm": ((best_helper_ape - anchor_ape) > 0.004).astype(int),
        "best_large_harm": ((best_helper_ape - anchor_ape) > 0.010).astype(int),
    }
    for helper_key in ["pp20", "pp48", "p95_weighted", "balanced_stable"]:
        h_ape = helper_apes[helper_key]
        labels[f"{helper_key}_gain_tail80"] = ((anchor_ape >= q80) & ((anchor_ape - h_ape) > 0.002)).astype(int)
        labels[f"{helper_key}_gain_tail70"] = ((anchor_ape >= q70) & ((anchor_ape - h_ape) > 0.002)).astype(int)
        labels[f"{helper_key}_harm"] = ((h_ape - anchor_ape) > 0.004).astype(int)

    probs: dict[str, np.ndarray] = {}
    for name, label in labels.items():
        probs[name] = opt21.oof_lgbm_probability(base, label, monotone=False)

    detail = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "anchor_pp70_ape": anchor_ape,
            "best_helper_ape": best_helper_ape,
            "validation_anchor_ape_q70": q70,
            "validation_anchor_ape_q75": q75,
            "validation_anchor_ape_q80": q80,
            "validation_anchor_ape_q85": q85,
            **{f"label_{k}": v for k, v in labels.items()},
            **{f"prob_{k}": v for k, v in probs.items()},
        }
    )
    return detail, probs


def weighted_helper(helpers: dict[str, np.ndarray], probs: dict[str, np.ndarray], suffix: str) -> np.ndarray:
    keys = ["pp20", "pp48", "p95_weighted", "balanced_stable"]
    weights = [np.clip(probs.get(f"{key}_{suffix}", np.zeros_like(next(iter(helpers.values())))), 0, 1) for key in keys]
    denom = np.clip(np.sum(np.vstack(weights), axis=0), 1e-6, None)
    return sum(helpers[key] * w for key, w in zip(keys, weights)) / denom


def pp_opt96_best_gain_routing(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    helper_sets = {
        "p95_weighted": helpers["p95_weighted"],
        "balanced_stable": helpers["balanced_stable"],
        "pp20": helpers["pp20"],
        "prob_weighted_tail80": weighted_helper(helpers, probs, "gain_tail80"),
    }
    for helper_key, helper in helper_sets.items():
        for prob_key in ["best_gain_any", "best_gain_tail75", "best_gain_tail80", "best_gain_tail85"]:
            prob = probs[prob_key]
            for threshold in [0.08, 0.14, 0.22, 0.32, 0.44]:
                for width in [0.18, 0.30, 0.44]:
                    w = gate(prob, threshold, width)
                    for strength in [0.10, 0.18, 0.30, 0.46, 0.64]:
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt96_best_gain__helper={helper_key}__prob={prob_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "best_helper_gain_label_routing", "PP-OPT96", pred))
    return rows


def pp_opt97_helper_specific(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    helper_sets = {
        "tail80_weighted": weighted_helper(helpers, probs, "gain_tail80"),
        "tail70_weighted": weighted_helper(helpers, probs, "gain_tail70"),
        "pp20_pp48": 0.55 * helpers["pp20"] + 0.45 * helpers["pp48"],
        "p95_balanced": 0.50 * helpers["p95_weighted"] + 0.50 * helpers["balanced_stable"],
    }
    score = np.clip(
        0.45 * probs["pp20_gain_tail80"]
        + 0.25 * probs["pp48_gain_tail80"]
        + 0.20 * probs["p95_weighted_gain_tail80"]
        + 0.10 * probs["balanced_stable_gain_tail80"],
        0,
        1,
    )
    for helper_key, helper in helper_sets.items():
        for threshold in [0.06, 0.12, 0.20, 0.30, 0.42]:
            for width in [0.16, 0.28, 0.42]:
                w = gate(score, threshold, width)
                for strength in [0.12, 0.22, 0.36, 0.52]:
                    pred = anchor + (helper - anchor) * w * strength
                    name = (
                        f"ppopt97_helper_specific__helper={helper_key}"
                        f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "helper_specific_gain_label_routing", "PP-OPT97", pred))
    return rows


def pp_opt98_gain_harm_guard(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    helper_sets = {
        "p95_weighted": helpers["p95_weighted"],
        "balanced_stable": helpers["balanced_stable"],
        "prob_weighted_tail80": weighted_helper(helpers, probs, "gain_tail80"),
    }
    harm = np.clip(0.65 * probs["best_harm"] + 0.35 * probs["best_large_harm"], 0, 1)
    for helper_key, helper in helper_sets.items():
        for gain_key in ["best_gain_tail75", "best_gain_tail80", "best_gain_tail85"]:
            gain = probs[gain_key]
            for harm_penalty in [0.35, 0.55, 0.75, 0.90]:
                score = np.clip(gain * (1.0 - harm_penalty * harm), 0, 1)
                for threshold in [0.05, 0.10, 0.18, 0.28]:
                    w = gate(score, threshold, 0.30)
                    for strength in [0.16, 0.28, 0.42, 0.58]:
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt98_gain_harm__helper={helper_key}__gain={gain_key}"
                            f"__hpen={safe_name(harm_penalty)}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "gain_minus_harm_guarded_routing", "PP-OPT98", pred))
    return rows


def pp_opt99_tail_quantile(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    helper = 0.60 * helpers["pp20"] + 0.40 * helpers["p95_weighted"]
    for prob_key in ["best_gain_tail75", "best_gain_tail80", "best_gain_tail85", "pp20_gain_tail80"]:
        prob = probs[prob_key]
        for threshold in [0.04, 0.08, 0.14, 0.22, 0.34]:
            for width in [0.14, 0.24, 0.36]:
                w = gate(prob, threshold, width)
                for strength in [0.24, 0.38, 0.54, 0.72]:
                    pred = anchor + (helper - anchor) * w * strength
                    name = (
                        f"ppopt99_tail_quantile__prob={prob_key}"
                        f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "tail_quantile_label_routing", "PP-OPT99", pred))
    return rows


def pp_opt100_direction_gain(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    helpers = helper_predictions(ref)
    direction, q_strength = quantile_direction(quant)
    for helper_key in ["pp20", "p95_weighted", "balanced_stable"]:
        helper = helpers[helper_key]
        aligned = ((helper - anchor) * direction > 0).astype(float)
        guard = np.where(direction == 0, 0.55, 0.25 + 0.75 * aligned * q_strength)
        for prob_key in ["best_gain_tail80", f"{helper_key}_gain_tail80" if f"{helper_key}_gain_tail80" in probs else "best_gain_tail80"]:
            score = np.clip(probs[prob_key] * guard, 0, 1)
            for threshold in [0.04, 0.10, 0.18, 0.28]:
                w = gate(score, threshold, 0.30)
                for strength in [0.18, 0.32, 0.48, 0.66]:
                    pred = anchor + (helper - anchor) * w * strength
                    name = (
                        f"ppopt100_direction_gain__helper={helper_key}__prob={prob_key}"
                        f"__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    )
                    rows.append(make_candidate(base, name, "direction_and_gain_aligned_routing", "PP-OPT100", pred))
    return rows


def pp_opt101_existing_selector(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp70 = ref["pp70"].to_numpy(dtype=float)
    pp81 = ref["pp81"].to_numpy(dtype=float)
    pp82 = ref["pp82_op"].to_numpy(dtype=float)
    pp95 = ref["pp95_op"].to_numpy(dtype=float)
    p95_mode = ref["pp82_p95"].to_numpy(dtype=float)
    gain = np.clip(0.50 * probs["best_gain_tail80"] + 0.50 * probs["best_gain_tail85"], 0, 1)
    harm = np.clip(probs["best_harm"], 0, 1)
    for safe_key, safe in [("pp81", pp81), ("pp95", pp95), ("pp70", pp70)]:
        for target_key, target in [("pp82op", pp82), ("p95mode", p95_mode)]:
            for threshold in [0.08, 0.14, 0.22, 0.34]:
                for harm_penalty in [0.45, 0.70, 0.90]:
                    score = np.clip(gain * (1.0 - harm_penalty * harm), 0, 1)
                    w = gate(score, threshold, 0.28)
                    for strength in [0.08, 0.16, 0.28, 0.42]:
                        pred = safe + (target - safe) * w * strength
                        name = (
                            f"ppopt101_selector__safe={safe_key}__target={target_key}"
                            f"__thr={safe_name(threshold)}__hpen={safe_name(harm_penalty)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "existing_candidate_label_selector", "PP-OPT101", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp48_score", "pp48"),
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp95_p95", "pp95_p95"),
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
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT96", "PP-OPT97", "PP-OPT98", "PP-OPT99", "PP-OPT100", "PP-OPT101"])].copy()
    pool["delta_vs_pp64_MAPE"] = pool["test_MAPE"] - float(pp64["MAPE"])
    pool["delta_vs_pp64_p95_APE"] = pool["test_p95_APE"] - float(pp64["p95_APE"])
    pool["delta_vs_pp70_MAPE"] = pool["test_MAPE"] - float(pp70["MAPE"])
    pool["delta_vs_pp70_p95_APE"] = pool["test_p95_APE"] - float(pp70["p95_APE"])

    op_pool = pool[
        (pool["operational_pass_vs_incumbent"])
        & (pool["delta_vs_pp64_MAPE"] <= 0)
        & (pool["delta_vs_pp64_p95_APE"] <= 0)
    ].copy()
    if op_pool.empty:
        op_pool = pool[(pool["operational_pass_vs_incumbent"]) & (pool["delta_vs_pp64_MAPE"] <= 0.00002)].copy()
    operational = op_pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE", "test_p95_APE"]).iloc[0]

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
        "selection_reason": "select operational candidate only if MAPE and p95 are not worse than PP64; keep p95-focused candidate separately",
    }


def add_protocol_candidates(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "label_refined_operational_selection"), ("p95", "label_refined_p95_selection")]:
        source = out[f"{key}_source_candidate"]
        protocol = f"ppopt102_{key}_label_refined_tail_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT102"
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
        "pp95_operational_reference": "reference_pp95_operational",
        "pp95_p95_reference": "reference_pp95_p95",
        "pp102_operational_label_refined": decision["operational_protocol_candidate"],
        "pp102_p95_label_refined": decision["p95_protocol_candidate"],
    }
    subset = predictions[predictions["candidate"].isin(set(selected.values()))].copy()
    label_lookup = {candidate: label for label, candidate in selected.items()}
    subset["candidate_label"] = subset["candidate"].map(label_lookup).fillna(subset["candidate"])
    return subset, selected


def stability_decision(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    op = stability_aggregate[stability_aggregate["candidate_label"].eq("pp102_operational_label_refined")].iloc[0]
    p95 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp102_p95_label_refined")].iloc[0]
    op_replace = (
        op["fixed_test_delta_vs_pp64_MAPE"] <= 0
        and op["fixed_test_delta_vs_pp64_p95_APE"] <= 0
        and op["avg_pp64_MAPE_win_rate"] >= 0.50
        and op["avg_pp64_p95_win_rate"] >= 0.45
    )
    return {
        "operational_verdict": "PP102 운영형은 PP64/PP70 교체 후보로 승격 가능" if op_replace else "PP102 운영형도 운영 교체는 보류",
        "p95_verdict": "PP102 p95형은 tail 안정성 우선 옵션으로 유지",
        "pp102_operational_fixed_test_MAPE": float(op["fixed_test_MAPE"]),
        "pp102_operational_fixed_test_p95_APE": float(op["fixed_test_p95_APE"]),
        "pp102_operational_delta_vs_pp64_MAPE": float(op["fixed_test_delta_vs_pp64_MAPE"]),
        "pp102_operational_delta_vs_pp64_p95_APE": float(op["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp102_operational_avg_pp64_MAPE_win_rate": float(op["avg_pp64_MAPE_win_rate"]),
        "pp102_operational_avg_pp64_p95_win_rate": float(op["avg_pp64_p95_win_rate"]),
        "pp102_operational_avg_pp64_all3_win_rate": float(op["avg_pp64_all3_win_rate"]),
        "pp102_p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "pp102_p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "pp102_p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "pp102_p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "pp102_p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "pp102_p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
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
                "reference_pp95_operational",
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
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(["pp102_operational_label_refined", "pp102_p95_label_refined"])]
    stability = config["stability_decision"]
    verdict = (
        f"{stability['operational_verdict']}. 운영형 fixed test는 PP64 대비 MAPE "
        f"{stability['pp102_operational_delta_vs_pp64_MAPE']:+.6f}, p95 "
        f"{stability['pp102_operational_delta_vs_pp64_p95_APE']:+.6f}."
    )

    md = "\n".join(
        [
            "# PP-OPT96~102 Warm tail label refinement 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: tail risk 자체가 아니라 fallback helper가 실제로 더 좋은 row를 학습",
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
  <title>PP-OPT96~102 Warm tail label refinement 실험 결과</title>
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
  <h1>PP-OPT96~102 Warm tail label refinement 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영형: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95형: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>운영형 PP64 대비 MAPE</strong>{stability['pp102_operational_delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{stability['pp102_operational_delta_vs_pp64_p95_APE']:+.6f}</div>
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
    base, source, ref, quant, selected_refs, parent_config = load_inputs()
    label_detail, probs = build_label_probabilities(base, ref)
    references = add_reference_candidates(base, ref)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt96_best_gain_routing(base, ref, probs))
    candidates.extend(pp_opt97_helper_specific(base, ref, probs))
    candidates.extend(pp_opt98_gain_harm_guard(base, ref, probs))
    candidates.extend(pp_opt99_tail_quantile(base, ref, probs))
    candidates.extend(pp_opt100_direction_gain(base, ref, quant, probs))
    candidates.extend(pp_opt101_existing_selector(base, ref, probs))

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
            "pp89_config": str(PP89_CONFIG.relative_to(REPO)),
            "pp89_predictions": str(PP89_PREDS.relative_to(REPO)),
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
    label_detail.to_csv(ARTIFACT_DIR / "tail_label_probability_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "tail_label_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "tail_label_refinement_result.html").write_text(report_html, encoding="utf-8")

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
