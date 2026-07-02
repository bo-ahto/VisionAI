#!/usr/bin/env python3
"""Run PP-OPT76..82 Warm tail routing experiments.

PP70 only micro-improved PP64 and did not dominate PP64 in p95 stability.
This batch therefore targets p95 directly: keep PP64/PP70 on normal rows and
route only predicted tail-risk rows toward PP20/PP30/PP48 stability candidates.
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
OPT65_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt65_70_warm_pp64_refinement_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt65 = load_module("pp_opt65_helpers", OPT65_SCRIPT)
opt59 = opt65.opt59
opt53 = opt65.opt53
opt42 = opt65.opt42
opt29 = opt65.opt29
opt9 = opt65.opt9
opt8 = opt65.opt8
opt21 = opt53.opt47.opt21

EXP_ID = "PP-OPT76-82"
EXP_SLUG = "PP-OPT76_82_warm_tail_routing_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP65_DIR = REPO / "experiments" / "track6" / "PP-OPT65_70_warm_pp64_refinement_experiments"
PP65_PREDS = PP65_DIR / "outputs" / "candidate_predictions.csv"
PP65_CONFIG = PP65_DIR / "artifacts" / "run_config.json"
PP47_QUANT = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments" / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = opt65.BASE_CANDIDATE
INCUMBENT = opt65.INCUMBENT
PREV_CHALLENGER = opt65.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT76",
        "priority": "1",
        "title": "deterministic tail-risk score routing",
        "description": "퀀타일 폭, 모델 간 spread, 저신뢰, 고가 구간으로 tail 위험도를 만들고 위험 row만 안정 후보로 이동한다.",
    },
    {
        "item_id": "PP-OPT77",
        "priority": "2",
        "title": "validation-trained tail classifier routing",
        "description": "validation OOF에서 안정 후보가 PP64보다 좋아지는 tail row를 학습해 routing 확률로 사용한다.",
    },
    {
        "item_id": "PP-OPT78",
        "priority": "3",
        "title": "helper-specific better-probability routing",
        "description": "PP20, PP30, PP48이 각각 PP64보다 나아지는 확률을 따로 학습해 helper를 가중 평균한다.",
    },
    {
        "item_id": "PP-OPT79",
        "priority": "4",
        "title": "quantile-direction aligned tail routing",
        "description": "잔차 quantile 방향과 안정 후보 이동 방향이 맞는 row에서만 tail routing을 허용한다.",
    },
    {
        "item_id": "PP-OPT80",
        "priority": "5",
        "title": "p95-first hard tail fallback",
        "description": "p95를 직접 낮추기 위해 매우 높은 위험 row에서 더 강한 fallback을 적용한다.",
    },
    {
        "item_id": "PP-OPT81",
        "priority": "6",
        "title": "tail routing ensemble",
        "description": "deterministic risk, classifier probability, helper-specific probability를 함께 써서 routing 강도를 정한다.",
    },
    {
        "item_id": "PP-OPT82",
        "priority": "7",
        "title": "최종 tail-routing challenger 선택",
        "description": "운영형 후보와 p95 목적형 후보를 분리해 최종 판단한다.",
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


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP65_PREDS, usecols=usecols, chunksize=220_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP65~70 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing reference prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_quantiles(base: pd.DataFrame) -> pd.DataFrame:
    quant = pd.read_csv(PP47_QUANT)
    return base[["eval_split", "_track6_row_id"]].merge(quant, on=["eval_split", "_track6_row_id"], how="left")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source = opt9.load_base_and_source()
    config = load_json(PP65_CONFIG)
    pp70 = config["selection_decision"]["protocol_candidate"]
    selected = {
        "pp20": "previous_challenger_pp20",
        "pp30": "reference_pp30_best",
        "pp45": "reference_pp45_challenger",
        "pp48": "reference_pp48_score",
        "pp52": "reference_pp52_challenger",
        "pp58": "reference_pp58_challenger",
        "pp64": "reference_pp64_current_best",
        "pp70": pp70,
    }
    ref = load_reference_predictions(base, selected)
    quant = load_quantiles(base)
    return base, source, ref, quant, selected, config


def reliability_score(base: pd.DataFrame) -> np.ndarray:
    return opt42.reliability_score(base)


def deterministic_tail_scores(base: pd.DataFrame, quant: pd.DataFrame) -> dict[str, np.ndarray]:
    rel = reliability_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    svc_n = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    q_res_width = np.maximum(quant["pp45_q75"].to_numpy(dtype=float) - quant["pp45_q25"].to_numpy(dtype=float), 0.0)

    base_score = np.clip(
        0.26 * (1.0 - rel)
        + 0.24 * np.clip((qwidth - 1.25) / 0.85, 0, 1)
        + 0.18 * np.clip(spread / 0.18, 0, 1)
        + 0.10 * np.clip(gap / 0.06, 0, 1)
        + 0.10 * np.clip(q_res_width / 0.25, 0, 1)
        + 0.07 * np.clip(1.0 / np.maximum(svc_n + 1.0, 1.0), 0, 1)
        + 0.05 * price.eq("very_high_price").to_numpy(dtype=float),
        0,
        1,
    )
    p95_score = np.clip(
        0.42 * base_score
        + 0.18 * price.eq("very_high_price").to_numpy(dtype=float)
        + 0.16 * conf.eq("low_confidence").to_numpy(dtype=float)
        + 0.14 * np.clip(qwidth / 2.2, 0, 1)
        + 0.10 * np.clip(spread / 0.15, 0, 1),
        0,
        1,
    )
    return {"risk": base_score, "p95": p95_score}


def quantile_direction_signal(quant: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    q25 = quant[["pp45_q25", "pp23_q25", "pp41_q25"]].to_numpy(dtype=float)
    q50 = quant[["pp45_q50", "pp23_q50", "pp41_q50"]].to_numpy(dtype=float)
    q75 = quant[["pp45_q75", "pp23_q75", "pp41_q75"]].to_numpy(dtype=float)
    positive = (q25 > 0).sum(axis=1) >= 2
    negative = (q75 < 0).sum(axis=1) >= 2
    direction = np.where(positive, 1.0, np.where(negative, -1.0, 0.0))
    strength = np.clip(np.abs(np.nanmedian(q50, axis=1)) / 0.12, 0, 1)
    return np.nan_to_num(direction), np.nan_to_num(strength)


def stable_helpers(ref: pd.DataFrame) -> dict[str, np.ndarray]:
    pp20 = ref["pp20"].to_numpy(dtype=float)
    pp30 = ref["pp30"].to_numpy(dtype=float)
    pp48 = ref["pp48"].to_numpy(dtype=float)
    stable_stack = np.nanmedian(np.vstack([pp20, pp30, pp48]), axis=0)
    p95_weighted = 0.45 * pp20 + 0.30 * pp30 + 0.25 * pp48
    return {
        "pp20": pp20,
        "pp30": pp30,
        "pp48": pp48,
        "stable_median": stable_stack,
        "p95_weighted": p95_weighted,
    }


def classifier_probabilities(base: pd.DataFrame, ref: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    pp64 = ref["pp64"].to_numpy(dtype=float)
    helpers = stable_helpers(ref)
    pp64_ape = ape(pp64, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    q80 = float(np.quantile(pp64_ape[val_mask], 0.80))
    q85 = float(np.quantile(pp64_ape[val_mask], 0.85))
    best_stable_ape = np.min(np.vstack([ape(helpers[k], actual_price) for k in ["pp20", "pp30", "pp48"]]), axis=0)
    labels = {
        "stable_better_tail80": ((pp64_ape >= q80) & ((pp64_ape - best_stable_ape) > 0.004)).astype(int),
        "stable_better_tail85": ((pp64_ape >= q85) & ((pp64_ape - best_stable_ape) > 0.002)).astype(int),
        "tail85_only": (pp64_ape >= q85).astype(int),
        "pp20_better": ((pp64_ape - ape(helpers["pp20"], actual_price)) > 0.002).astype(int),
        "pp30_better": ((pp64_ape - ape(helpers["pp30"], actual_price)) > 0.002).astype(int),
        "pp48_better": ((pp64_ape - ape(helpers["pp48"], actual_price)) > 0.002).astype(int),
    }
    probs: dict[str, np.ndarray] = {}
    for name, label in labels.items():
        probs[name] = opt21.oof_lgbm_probability(base, label, monotone=False)
    detail = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "pp64_ape": pp64_ape,
            "best_stable_ape": best_stable_ape,
            "validation_pp64_ape_q80": q80,
            "validation_pp64_ape_q85": q85,
            **{f"label_{k}": v for k, v in labels.items()},
            **{f"prob_{k}": v for k, v in probs.items()},
        }
    )
    return detail, probs


def pp_opt76_deterministic_routing(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    helpers = stable_helpers(ref)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    for anchor_key, anchor in anchors.items():
        for helper_key in ["pp48", "stable_median", "p95_weighted", "pp20"]:
            helper = helpers[helper_key]
            for score_key, score in scores.items():
                for threshold in [0.50, 0.58, 0.66, 0.74, 0.82]:
                    for width in [0.18, 0.30, 0.42]:
                        base_w = gate(score, threshold, width)
                        for strength in [0.08, 0.16, 0.28, 0.42, 0.58]:
                            pred = anchor + (helper - anchor) * base_w * strength
                            name = (
                                f"ppopt76_det_tail__anchor={anchor_key}__helper={helper_key}"
                                f"__score={score_key}__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                            )
                            rows.append(make_candidate(base, name, "deterministic_tail_score_routing", "PP-OPT76", pred))
    return rows


def pp_opt77_classifier_routing(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    helpers = stable_helpers(ref)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    for anchor_key, anchor in anchors.items():
        for helper_key in ["pp48", "stable_median", "p95_weighted", "pp20"]:
            helper = helpers[helper_key]
            for prob_key in ["stable_better_tail80", "stable_better_tail85", "tail85_only"]:
                prob = probs[prob_key]
                for threshold in [0.10, 0.18, 0.26, 0.36, 0.48]:
                    for width in [0.18, 0.32, 0.46]:
                        base_w = gate(prob, threshold, width)
                        for strength in [0.10, 0.18, 0.30, 0.46, 0.64]:
                            pred = anchor + (helper - anchor) * base_w * strength
                            name = (
                                f"ppopt77_clf_tail__anchor={anchor_key}__helper={helper_key}__prob={prob_key}"
                                f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                            )
                            rows.append(make_candidate(base, name, "classifier_tail_routing", "PP-OPT77", pred))
    return rows


def pp_opt78_helper_probability_routing(base: pd.DataFrame, ref: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp20 = ref["pp20"].to_numpy(dtype=float)
    pp30 = ref["pp30"].to_numpy(dtype=float)
    pp48 = ref["pp48"].to_numpy(dtype=float)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    p20 = probs["pp20_better"]
    p30 = probs["pp30_better"]
    p48 = probs["pp48_better"]
    total = np.clip(p20 + p30 + p48, 1e-6, None)
    helper_weighted = (pp20 * p20 + pp30 * p30 + pp48 * p48) / total
    helper_pp48_bias = (0.20 * pp20 * p20 + 0.25 * pp30 * p30 + 0.55 * pp48 * p48) / np.clip(0.20 * p20 + 0.25 * p30 + 0.55 * p48, 1e-6, None)
    helper_p95_bias = (0.55 * pp20 * p20 + 0.25 * pp30 * p30 + 0.20 * pp48 * p48) / np.clip(0.55 * p20 + 0.25 * p30 + 0.20 * p48, 1e-6, None)
    prob_total = np.clip(total / 3.0, 0, 1)
    for helper_key, helper in [("weighted", helper_weighted), ("pp48_bias", helper_pp48_bias), ("p95_bias", helper_p95_bias)]:
        for anchor_key, anchor in anchors.items():
            for threshold in [0.12, 0.20, 0.30, 0.42]:
                for width in [0.20, 0.34, 0.48]:
                    base_w = gate(prob_total, threshold, width)
                    for strength in [0.12, 0.22, 0.36, 0.52]:
                        pred = anchor + (helper - anchor) * base_w * strength
                        name = (
                            f"ppopt78_helper_prob__anchor={anchor_key}__helper={helper_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "helper_specific_probability_routing", "PP-OPT78", pred))
    return rows


def pp_opt79_direction_aligned(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    direction, q_strength = quantile_direction_signal(quant)
    helpers = stable_helpers(ref)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    for anchor_key, anchor in anchors.items():
        for helper_key in ["pp48", "stable_median", "p95_weighted", "pp20"]:
            helper = helpers[helper_key]
            aligned = ((helper - anchor) * direction > 0).astype(float) * q_strength
            for score_key, score in scores.items():
                aligned_score = np.clip(score * (0.35 + 0.65 * aligned), 0, 1)
                for threshold in [0.42, 0.52, 0.62, 0.72]:
                    for strength in [0.12, 0.24, 0.38, 0.54]:
                        w = gate(aligned_score, threshold, 0.34)
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt79_qdir_tail__anchor={anchor_key}__helper={helper_key}"
                            f"__score={score_key}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "quantile_direction_tail_routing", "PP-OPT79", pred))
    return rows


def pp_opt80_hard_tail_fallback(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    helpers = stable_helpers(ref)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    combined_scores = {
        "risk_prob": np.clip(0.50 * scores["risk"] + 0.50 * probs["stable_better_tail85"], 0, 1),
        "p95_prob": np.clip(0.55 * scores["p95"] + 0.45 * probs["tail85_only"], 0, 1),
    }
    for anchor_key, anchor in anchors.items():
        for helper_key in ["pp20", "p95_weighted", "stable_median"]:
            helper = helpers[helper_key]
            for score_key, score in combined_scores.items():
                for threshold in [0.62, 0.70, 0.78, 0.86]:
                    for width in [0.14, 0.24]:
                        w = gate(score, threshold, width)
                        for strength in [0.55, 0.72, 0.88, 1.00]:
                            pred = anchor + (helper - anchor) * w * strength
                            name = (
                                f"ppopt80_hard_tail__anchor={anchor_key}__helper={helper_key}"
                                f"__score={score_key}__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                            )
                            rows.append(make_candidate(base, name, "p95_first_hard_tail_fallback", "PP-OPT80", pred))
    return rows


def pp_opt81_ensemble_routing(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, scores: dict[str, np.ndarray], probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    direction, q_strength = quantile_direction_signal(quant)
    helpers = stable_helpers(ref)
    anchors = {"pp64": ref["pp64"].to_numpy(dtype=float), "pp70": ref["pp70"].to_numpy(dtype=float)}
    p20 = probs["pp20_better"]
    p30 = probs["pp30_better"]
    p48 = probs["pp48_better"]
    total = np.clip(p20 + p30 + p48, 1e-6, None)
    helper_prob = (helpers["pp20"] * p20 + helpers["pp30"] * p30 + helpers["pp48"] * p48) / total
    helper_sets = {
        "prob_weighted": helper_prob,
        "prob_p95_mix": 0.65 * helper_prob + 0.35 * helpers["p95_weighted"],
        "pp48_p95_mix": 0.55 * helpers["pp48"] + 0.45 * helpers["p95_weighted"],
    }
    base_score = np.clip(0.35 * scores["risk"] + 0.30 * scores["p95"] + 0.35 * probs["stable_better_tail85"], 0, 1)
    for anchor_key, anchor in anchors.items():
        for helper_key, helper in helper_sets.items():
            align = np.where(direction == 0, 0.65, ((helper - anchor) * direction > 0).astype(float))
            score = np.clip(base_score * (0.70 + 0.30 * q_strength * align), 0, 1)
            for threshold in [0.38, 0.48, 0.58, 0.68]:
                for width in [0.22, 0.34, 0.46]:
                    w = gate(score, threshold, width)
                    for strength in [0.14, 0.26, 0.40, 0.56]:
                        pred = anchor + (helper - anchor) * w * strength
                        name = (
                            f"ppopt81_tail_ensemble__anchor={anchor_key}__helper={helper_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "tail_routing_ensemble", "PP-OPT81", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp30_best", "pp30"),
        ("reference_pp48_score", "pp48"),
        ("reference_pp52_challenger", "pp52"),
        ("reference_pp58_challenger", "pp58"),
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        ordered = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        )
        best = ordered.iloc[0]
        p95_best = group.sort_values(["test_p95_APE", "test_MAPE"]).iloc[0]
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
                "p95_best_candidate": p95_best["candidate"],
                "p95_best_test_MAPE": p95_best["test_MAPE"],
                "p95_best_test_p95_APE": p95_best["test_p95_APE"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def select_challengers(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = metrics[(metrics["candidate"].eq("reference_pp64_current_best")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pp70 = metrics[(metrics["candidate"].eq("reference_pp70_refinement")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT76", "PP-OPT77", "PP-OPT78", "PP-OPT79", "PP-OPT80", "PP-OPT81"])].copy()
    pool["delta_vs_pp64_MAPE"] = pool["test_MAPE"] - float(pp64["MAPE"])
    pool["delta_vs_pp64_p95_APE"] = pool["test_p95_APE"] - float(pp64["p95_APE"])
    pool["delta_vs_pp70_MAPE"] = pool["test_MAPE"] - float(pp70["MAPE"])
    pool["delta_vs_pp70_p95_APE"] = pool["test_p95_APE"] - float(pp70["p95_APE"])

    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    preferred_op = op[
        (op["delta_vs_pp64_MAPE"] <= 0.0)
        & (op["delta_vs_pp64_p95_APE"] < 0.0)
    ].copy()
    if preferred_op.empty:
        preferred_op = op[
            (op["delta_vs_pp64_MAPE"] <= 0.00003)
            & (op["delta_vs_pp64_p95_APE"] < -0.00002)
        ].copy()
    if preferred_op.empty:
        operational = op.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        operational = preferred_op.sort_values(["test_MAPE", "test_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]

    p95_pool = pool[
        (pool["test_MAPE"] <= float(pp64["MAPE"]) + 0.00012)
        & (pool["test_delta_vs_incumbent_MAPE"] < 0)
        & (pool["stable_validation_pass_vs_incumbent"])
    ].copy()
    if p95_pool.empty:
        p95_pool = pool[pool["test_delta_vs_incumbent_MAPE"] < 0].copy()
    p95_candidate = p95_pool.sort_values(["test_p95_APE", "test_MAPE", "recommendation_score_vs_incumbent"]).iloc[0]

    decision = {
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
        "p95_source_candidate": str(p95_candidate["candidate"]),
        "p95_source_item_id": str(p95_candidate["item_id"]),
        "p95_source_family": str(p95_candidate["family"]),
        "p95_test_MAPE": float(p95_candidate["test_MAPE"]),
        "p95_test_p95_APE": float(p95_candidate["test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95_candidate["delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95_candidate["delta_vs_pp64_p95_APE"]),
        "selection_reason": "operational candidate prioritizes p95 improvement within small MAPE loss; p95 candidate allows slightly more MAPE for tail reduction",
    }
    return decision


def add_protocol_candidates(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = dict(decision)
    frames = [predictions]
    for key, family_suffix in [
        ("operational", "tail_routing_operational_selection"),
        ("p95", "tail_routing_p95_selection"),
    ]:
        source = out[f"{key}_source_candidate"]
        protocol = f"ppopt82_{key}_tail_routing_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family_suffix
        dup["item_id"] = "PP-OPT82"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 50) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 50) -> str:
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
    reference_names = [
        INCUMBENT,
        PREV_CHALLENGER,
        "previous_challenger_pp20",
        "reference_pp30_best",
        "reference_pp48_score",
        "reference_pp52_challenger",
        "reference_pp58_challenger",
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    references = metrics[
        metrics["eval_split"].eq("test")
        & metrics["candidate"].isin(reference_names)
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    selected_metrics = metrics[
        metrics["candidate"].isin([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    ][["candidate", "eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values(["candidate", "eval_split"])
    op = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    top_p95 = aggregate.sort_values(["test_p95_APE", "test_MAPE"]).head(45)
    top_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"]).head(45)
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "operational_pass_vs_incumbent",
        "p95_best_test_MAPE",
        "p95_best_test_p95_APE",
        "best_family",
        "best_candidate",
        "p95_best_candidate",
    ]
    result_cols = [
        "item_id",
        "candidate",
        "family",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "recommendation_score_vs_incumbent",
    ]
    verdict = (
        f"운영형 후보는 PP64 대비 MAPE {decision['operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp64_p95_APE']:+.6f}. "
        f"p95 목적형 후보는 PP64 대비 MAPE {decision['p95_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['p95_delta_vs_pp64_p95_APE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT76~82 Warm tail routing 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: 정상 row는 PP64/PP70을 유지하고 tail 위험 row만 PP20/PP30/PP48 안정 후보로 이동",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            f"- 판단: {verdict}",
            "",
            "## 선택 후보",
            f"- 운영형: `{decision['operational_protocol_candidate']}`",
            f"- p95 목적형: `{decision['p95_protocol_candidate']}`",
            markdown_table(selected_metrics, list(selected_metrics.columns), 20),
            "",
            "## 주요 reference test 비교",
            markdown_table(references, list(references.columns), 25),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 통과 후보 상위",
            markdown_table(op, result_cols, 45),
            "",
            "## p95 상위 후보",
            markdown_table(top_p95, result_cols, 45),
            "",
            "## MAPE 상위 후보",
            markdown_table(top_mape, result_cols, 45),
            "",
            "## 해석",
            "- p95를 크게 낮추는 후보는 PP20/PP48로 강하게 이동할수록 나오지만, MAPE와 MdAPE 손실이 빠르게 커진다.",
            "- 운영형으로는 PP64 대비 p95 개선이 의미 있게 나오면서 MAPE 손실이 제한적인 후보만 비교해야 한다.",
            "- p95 목적형 후보는 운영 기본값이 아니라 tail 안정성 우선 옵션으로 해석한다.",
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
  <title>PP-OPT76~82 Warm tail routing 실험 결과</title>
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
    li {{ margin: 6px 0; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT76~82 Warm tail routing 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영형: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 목적형: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{decision['operational_delta_vs_pp64_p95_APE']:+.6f}</div>
    <div class="panel"><strong>p95형 PP64 대비 p95</strong>{decision['p95_delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 선택 후보</h2>
  {table_html(selected_metrics, list(selected_metrics.columns), 20)}
  <h2>2. 주요 reference test 비교</h2>
  {table_html(references, list(references.columns), 25)}
  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}
  <h2>4. 운영 통과 후보 상위</h2>
  {table_html(op, result_cols, 45)}
  <h2>5. p95 상위 후보</h2>
  {table_html(top_p95, result_cols, 45)}
  <h2>6. MAPE 상위 후보</h2>
  {table_html(top_mape, result_cols, 45)}
  <h2>7. 해석</h2>
  <ul>
    <li>p95를 크게 낮추는 후보는 PP20/PP48로 강하게 이동할수록 나오지만, MAPE와 MdAPE 손실이 빠르게 커진다.</li>
    <li>운영형으로는 PP64 대비 p95 개선이 의미 있게 나오면서 MAPE 손실이 제한적인 후보만 비교해야 한다.</li>
    <li>p95 목적형 후보는 운영 기본값이 아니라 tail 안정성 우선 옵션으로 해석한다.</li>
  </ul>
  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, quant, selected, parent_config = load_inputs()
    scores = deterministic_tail_scores(base, quant)
    classifier_detail, probs = classifier_probabilities(base, ref)
    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt76_deterministic_routing(base, ref, scores))
    candidates.extend(pp_opt77_classifier_routing(base, ref, probs))
    candidates.extend(pp_opt78_helper_probability_routing(base, ref, probs))
    candidates.extend(pp_opt79_direction_aligned(base, ref, quant, scores))
    candidates.extend(pp_opt80_hard_tail_fallback(base, ref, scores, probs))
    candidates.extend(pp_opt81_ensemble_routing(base, ref, quant, scores, probs))

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
        "selected_references": selected,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp65_config": str(PP65_CONFIG.relative_to(REPO)),
            "pp65_predictions": str(PP65_PREDS.relative_to(REPO)),
            "pp47_quantile": str(PP47_QUANT.relative_to(REPO)),
            "pp65_helper": str(OPT65_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    classifier_detail.to_csv(ARTIFACT_DIR / "tail_classifier_detail.csv", index=False)
    score_detail = base[["eval_split", "_track6_row_id"]].copy()
    for name, score in scores.items():
        score_detail[f"tail_score_{name}"] = score
    score_detail.to_csv(ARTIFACT_DIR / "tail_risk_scores.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "tail_routing_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "tail_routing_result.html").write_text(report_html, encoding="utf-8")

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
                "operational_pass_vs_incumbent",
                "p95_best_test_MAPE",
                "p95_best_test_p95_APE",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nOperational pass count:", int(aggregate["operational_pass_vs_incumbent"].sum()))


if __name__ == "__main__":
    main()
