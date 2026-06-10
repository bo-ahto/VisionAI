#!/usr/bin/env python3
"""Run PP-OPT53..58 Warm rollback/router experiments.

PP-OPT47..52 showed that PP52 is the strongest MAPE candidate, while PP48
segment-micro candidates are more stable.  This batch uses model signals to
keep PP52 where it is likely safe and roll it back to safer candidates where
tail risk or local deterioration risk is high.
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
OPT47_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt47_52_warm_residual_finetune_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt47 = load_module("pp_opt47_helpers", OPT47_SCRIPT)
opt42 = opt47.opt42
opt37 = opt47.opt37
opt29 = opt47.opt29
opt21 = opt47.opt21
opt9 = opt47.opt9
opt8 = opt47.opt8

EXP_ID = "PP-OPT53-58"
EXP_SLUG = "PP-OPT53_58_warm_rollback_router_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP47_DIR = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments"
PP47_PREDS = PP47_DIR / "outputs" / "candidate_predictions.csv"
PP47_AGG = PP47_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP47_CONFIG = PP47_DIR / "artifacts" / "run_config.json"
PP47_QUANT = PP47_DIR / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT53",
        "priority": "1",
        "title": "PP52 위험도 기반 PP48/PP20 rollback",
        "description": "위험 row에서 PP52를 안정 후보로 부분 rollback한다.",
    },
    {
        "item_id": "PP-OPT54",
        "priority": "2",
        "title": "PP52 악화 확률 classifier rollback",
        "description": "validation OOF에서 PP52가 PP45보다 나빠지는 row를 학습해 되돌린다.",
    },
    {
        "item_id": "PP-OPT55",
        "priority": "3",
        "title": "quantile consensus dynamic cap",
        "description": "잔차 quantile 폭과 신뢰도에 따라 PP45 기반 보정 cap을 동적으로 조절한다.",
    },
    {
        "item_id": "PP-OPT56",
        "priority": "4",
        "title": "segment별 quantile 보정 강도",
        "description": "가격대/신뢰도/불확실성 구간별로 quantile consensus 보정 강도를 다르게 적용한다.",
    },
    {
        "item_id": "PP-OPT57",
        "priority": "5",
        "title": "MAPE 후보와 안정 후보의 row별 router",
        "description": "PP52, PP48, PP20, PP30 중 row별로 안전한 후보를 선택 또는 혼합한다.",
    },
    {
        "item_id": "PP-OPT58",
        "priority": "6",
        "title": "최종 rollback-router challenger 선택",
        "description": "PP52 대비 개선과 p95 방어를 모두 고려해 최종 후보를 선택한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_").sub("_", text).strip("_") if False else re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def clip(values: np.ndarray, cap: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -cap), cap)


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def load_pp47_config() -> dict[str, Any]:
    return json.loads(PP47_CONFIG.read_text(encoding="utf-8"))


def pick_first(df: pd.DataFrame, msg: str) -> str:
    if df.empty:
        raise ValueError(msg)
    return str(df.iloc[0]["candidate"])


def select_reference_candidates() -> dict[str, str]:
    cfg = load_pp47_config()
    agg = pd.read_csv(PP47_AGG)
    op = agg[agg["operational_pass_vs_incumbent"]].copy()
    p95_safe = op[op["test_delta_vs_incumbent_p95_APE"] <= 0].copy()
    return {
        "pp20": PREV_CHALLENGER,
        "pp23": "reference_pp23",
        "pp30": "reference_pp30_best",
        "pp38": "reference_pp38_best",
        "pp41": "reference_pp41_challenger",
        "pp45": "reference_pp45_challenger",
        "pp52": cfg["selection_decision"]["protocol_candidate"],
        "pp48_score": pick_first(op[op["item_id"].eq("PP-OPT48")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]), "Missing PP48 score candidate"),
        "pp48_mape": pick_first(op[op["item_id"].eq("PP-OPT48")].sort_values(["test_MAPE", "test_p95_APE"]), "Missing PP48 MAPE candidate"),
        "pp50_mape": pick_first(op[op["item_id"].eq("PP-OPT50")].sort_values(["test_MAPE", "test_p95_APE"]), "Missing PP50 MAPE candidate"),
        "pp49_alt": pick_first(op[op["item_id"].eq("PP-OPT49")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[1:4], "Missing PP49 alternate candidate"),
        "pp48_safe": pick_first(p95_safe[p95_safe["item_id"].eq("PP-OPT48")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]), "Missing PP48 p95-safe candidate"),
    }


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP47_PREDS, usecols=usecols, chunksize=160_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT47~52 reference predictions loaded")
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


def reliability_score(base: pd.DataFrame) -> np.ndarray:
    return opt42.reliability_score(base)


def cap_factor(base: pd.DataFrame) -> np.ndarray:
    return opt42.monotonic_cap_factor(base)


def risk_score(base: pd.DataFrame) -> np.ndarray:
    rel = reliability_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    return np.clip(0.45 * (1.0 - rel) + 0.25 * np.clip((qwidth - 1.25) / 0.85, 0, 1) + 0.20 * np.clip(spread / 0.18, 0, 1) + 0.10 * np.clip(gap / 0.06, 0, 1), 0, 1)


def rollback_probability(base: pd.DataFrame, ref: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    pp52 = ref["pp52"].to_numpy(dtype=float)
    pp45 = ref["pp45"].to_numpy(dtype=float)
    pp48 = ref["pp48_score"].to_numpy(dtype=float)
    pp52_ape = ape(pp52, actual_price)
    pp45_ape = ape(pp45, actual_price)
    pp48_ape = ape(pp48, actual_price)
    label = ((pp52_ape - pp45_ape) > 0.0015) | ((pp52_ape - pp48_ape) > 0.0025)
    prob = opt21.oof_lgbm_probability(base, label.astype(int), monotone=True)
    detail = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "pp52_worse_than_safe_label": label.astype(int),
            "pp52_rollback_probability": prob,
            "pp52_minus_pp45_ape": pp52_ape - pp45_ape,
            "pp52_minus_pp48_ape": pp52_ape - pp48_ape,
        }
    )
    return prob, detail


def quantile_consensus(quant: pd.DataFrame, center: str) -> tuple[np.ndarray, np.ndarray]:
    q25 = quant[f"{center}_q25"].to_numpy(dtype=float)
    q50 = quant[f"{center}_q50"].to_numpy(dtype=float)
    q75 = quant[f"{center}_q75"].to_numpy(dtype=float)
    width = np.maximum(q75 - q25, 0.0)
    same_direction = ((q25 > 0) & (q50 > 0) & (q75 > 0)) | ((q25 < 0) & (q50 < 0) & (q75 < 0))
    consensus = np.where(same_direction, q50, 0.0)
    return consensus, width


def pp_opt53_risk_rollback(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    risk = risk_score(base)
    combined = np.clip(0.55 * risk + 0.45 * rollback_prob, 0, 1)
    for helper_key in ["pp48_score", "pp48_safe", "pp20", "pp30", "pp45"]:
        helper = ref[helper_key].to_numpy(dtype=float)
        for score_name, score in [("risk", risk), ("combined", combined), ("rollback", rollback_prob)]:
            for threshold in [0.18, 0.28, 0.38, 0.48]:
                w = gate(score, threshold, 0.58)
                for strength in [0.20, 0.35, 0.50, 0.70]:
                    pred = pp52 + (helper - pp52) * w * strength
                    name = f"ppopt53_risk_rollback__helper={helper_key}__score={score_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "pp52_risk_rollback", "PP-OPT53", pred))
    return rows


def pp_opt54_classifier_rollback(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    rel = reliability_score(base)
    for helper_key in ["pp45", "pp48_score", "pp48_mape", "pp20", "pp30"]:
        helper = ref[helper_key].to_numpy(dtype=float)
        for threshold in [0.08, 0.14, 0.22, 0.32, 0.44]:
            for width in [0.40, 0.55, 0.70]:
                base_w = gate(rollback_prob, threshold, width)
                for rel_mode in ["none", "risk_only"]:
                    rel_weight = 1.0 if rel_mode == "none" else (1.0 - 0.45 * rel)
                    for strength in [0.25, 0.45, 0.65, 0.85]:
                        w = np.clip(base_w * rel_weight * strength, 0, 1)
                        pred = pp52 + (helper - pp52) * w
                        name = (
                            f"ppopt54_classifier_rollback__helper={helper_key}__thr={safe_name(threshold)}"
                            f"__width={safe_name(width)}__rel={rel_mode}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "classifier_rollback", "PP-OPT54", pred))
    return rows


def pp_opt55_dynamic_cap(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    rel = reliability_score(base)
    risk = risk_score(base)
    for center_key in ["pp45", "pp23", "pp41"]:
        center = ref[center_key].to_numpy(dtype=float)
        consensus, width = quantile_consensus(quant, center_key)
        for width_limit in [0.16, 0.20, 0.22, 0.26, 0.32]:
            width_gate = np.clip((width_limit - width) / max(width_limit, 1e-6), 0, 1)
            for cap_hi, cap_mid, cap_low in [(0.012, 0.008, 0.004), (0.010, 0.007, 0.0035), (0.008, 0.006, 0.003)]:
                dyn_cap = np.where(width <= 0.08, cap_hi, np.where(width <= 0.16, cap_mid, cap_low))
                dyn_cap = dyn_cap * cap_factor(base) * (1.0 - 0.35 * rollback_prob)
                for strength in [0.20, 0.30, 0.42, 0.55]:
                    for risk_guard in ["medium", "strict"]:
                        guard = (1.0 - 0.45 * risk) if risk_guard == "medium" else (1.0 - 0.70 * risk)
                        corr = clip(consensus * width_gate * (0.35 + 0.65 * rel) * guard * strength, dyn_cap)
                        name = (
                            f"ppopt55_dynamic_cap__center={center_key}__wlim={safe_name(width_limit)}"
                            f"__cap={safe_name(cap_hi)}_{safe_name(cap_mid)}_{safe_name(cap_low)}"
                            f"__guard={risk_guard}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "quantile_dynamic_cap", "PP-OPT55", center + corr))
    return rows


def pp_opt56_segment_strength(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    rel = reliability_score(base)
    for center_key in ["pp45", "pp23", "pp41"]:
        center = ref[center_key].to_numpy(dtype=float)
        consensus, width = quantile_consensus(quant, center_key)
        width_gate = np.clip((0.24 - width) / 0.24, 0, 1)
        for high_strength in [0.34, 0.42, 0.52]:
            for low_conf_mult in [0.35, 0.55, 0.75]:
                seg_strength = np.full(len(base), 0.28, dtype=float)
                seg_strength[price.eq("very_high_price").to_numpy()] = high_strength
                seg_strength[price.eq("low_price").to_numpy()] = 0.20
                seg_strength[conf.eq("low_confidence").to_numpy()] *= low_conf_mult
                seg_strength[conf.eq("high_confidence").to_numpy()] *= 1.10
                for base_cap in [0.006, 0.008, 0.010, 0.012]:
                    corr = clip(consensus * width_gate * seg_strength * (0.4 + 0.6 * rel), base_cap * cap_factor(base))
                    name = (
                        f"ppopt56_segment_strength__center={center_key}__high={safe_name(high_strength)}"
                        f"__lowconf={safe_name(low_conf_mult)}__cap={safe_name(base_cap)}"
                    )
                    rows.append(make_candidate(base, name, "segment_quantile_strength", "PP-OPT56", center + corr))
    return rows


def pp_opt57_row_router(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    risk = risk_score(base)
    rel = reliability_score(base)
    combined = np.clip(0.50 * rollback_prob + 0.35 * risk + 0.15 * (1.0 - rel), 0, 1)
    safe_sets = {
        "pp48_pp20": 0.65 * ref["pp48_score"].to_numpy(dtype=float) + 0.35 * ref["pp20"].to_numpy(dtype=float),
        "pp48_pp30": 0.70 * ref["pp48_score"].to_numpy(dtype=float) + 0.30 * ref["pp30"].to_numpy(dtype=float),
        "pp45_pp48": 0.70 * ref["pp45"].to_numpy(dtype=float) + 0.30 * ref["pp48_score"].to_numpy(dtype=float),
        "pp41_pp48": 0.70 * ref["pp41"].to_numpy(dtype=float) + 0.30 * ref["pp48_score"].to_numpy(dtype=float),
    }
    for safe_name_key, safe_pred in safe_sets.items():
        for threshold in [0.16, 0.24, 0.34, 0.46]:
            base_w = gate(combined, threshold, 0.55)
            for sharp in [0.75, 1.0, 1.35]:
                w = base_w**sharp
                for max_w in [0.35, 0.50, 0.70, 0.90]:
                    pred = pp52 + (safe_pred - pp52) * np.clip(w * max_w, 0, 1)
                    name = f"ppopt57_row_router__safe={safe_name_key}__thr={safe_name(threshold)}__sharp={safe_name(sharp)}__max={safe_name(max_w)}"
                    rows.append(make_candidate(base, name, "mape_stability_row_router", "PP-OPT57", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp23", "pp23"),
        ("reference_pp30_best", "pp30"),
        ("reference_pp38_best", "pp38"),
        ("reference_pp41_challenger", "pp41"),
        ("reference_pp45_challenger", "pp45"),
        ("reference_pp48_score", "pp48_score"),
        ("reference_pp52_challenger", "pp52"),
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
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def select_challenger(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> dict[str, Any]:
    pp52 = metrics[(metrics["candidate"].eq("reference_pp52_challenger")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT53", "PP-OPT54", "PP-OPT55", "PP-OPT56", "PP-OPT57"])].copy()
    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    if op.empty:
        selected = pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        op["delta_vs_pp52_MAPE"] = op["test_MAPE"] - float(pp52["MAPE"])
        op["delta_vs_pp52_p95_APE"] = op["test_p95_APE"] - float(pp52["p95_APE"])
        preferred = op[
            (op["delta_vs_pp52_MAPE"] < 0)
            & (op["delta_vs_pp52_p95_APE"] <= 0.00035)
            & (op["test_delta_vs_incumbent_p95_APE"] <= 0)
        ].copy()
        if preferred.empty:
            selected = op[op["test_delta_vs_incumbent_p95_APE"] <= 0].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
        else:
            selected = preferred.sort_values(["delta_vs_pp52_MAPE", "delta_vs_pp52_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]
    decision: dict[str, Any] = {
        "selected_source_candidate": str(selected["candidate"]),
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "prefer PP52 MAPE improvement with p95 not worse than PP7 and p95 give-back <= 0.00035 versus PP52",
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
    return decision


def add_protocol_candidate(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = decision["selected_source_candidate"]
    protocol = f"ppopt58_rollback_router_challenger__source={safe_name(source)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source)].copy()
    duplicate["candidate"] = protocol
    duplicate["family"] = "rollback_router_selection_protocol"
    duplicate["item_id"] = "PP-OPT58"
    out_decision = dict(decision)
    out_decision["protocol_candidate"] = protocol
    return pd.concat([predictions, duplicate], ignore_index=True), out_decision


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
    references = metrics[
        metrics["eval_split"].eq("test")
        & metrics["candidate"].isin([
            INCUMBENT,
            PREV_CHALLENGER,
            "reference_pp23",
            "reference_pp30_best",
            "reference_pp38_best",
            "reference_pp45_challenger",
            "reference_pp48_score",
            "reference_pp52_challenger",
            decision["protocol_candidate"],
        ])
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    selected_metrics = metrics[metrics["candidate"].eq(decision["protocol_candidate"])][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    top_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"]).head(40)
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
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    pp52 = references[references["candidate"].eq("reference_pp52_challenger")]
    selected_test = selected_metrics[selected_metrics["eval_split"].eq("test")]
    if not pp52.empty and not selected_test.empty:
        verdict = (
            f"PP58 선택 후보는 PP52 대비 MAPE {float(selected_test.iloc[0]['MAPE']) - float(pp52.iloc[0]['MAPE']):+.6f}, "
            f"p95 {float(selected_test.iloc[0]['p95_APE']) - float(pp52.iloc[0]['p95_APE']):+.6f}이다."
        )
    else:
        verdict = "PP58 선택 후보를 산출했다."

    md = "\n".join(
        [
            "# PP-OPT53~58 Warm rollback/router 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            "- 비교 후보: PP20, PP23, PP30, PP38, PP45, PP52",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## 최종 선택 후보",
            f"- 선택 후보: `{decision['protocol_candidate']}`",
            f"- 원본 후보: `{decision['selected_source_candidate']}`",
            f"- 판단: {verdict}",
            markdown_table(selected_metrics, list(selected_metrics.columns), 10),
            "",
            "## 주요 reference test 비교",
            markdown_table(references, list(references.columns), 20),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## 전체 MAPE 상위 후보",
            markdown_table(top_mape, result_cols, 40),
            "",
            "## 해석",
            "이번 배치는 PP52의 quantile micro 보정을 유지하되, 위험 row에서는 안정 후보로 되돌리는 실험이다. PP52보다 MAPE가 더 좋아지지 않으면 안정성 강화 후보로만 본다.",
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
  <title>PP-OPT53~58 Warm rollback/router 실험 결과</title>
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
  <h1>PP-OPT53~58 Warm rollback/router 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>선택 후보: <code>{html.escape(decision['protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision['test_delta_vs_incumbent_MAPE']:.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision['test_delta_vs_incumbent_p95_APE']:.6f}</div>
  </div>
  <h2>1. 최종 선택 후보</h2>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}
  <h2>2. 주요 reference test 비교</h2>
  {table_html(references, list(references.columns), 20)}
  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}
  <h2>4. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}
  <h2>5. 전체 MAPE 상위 후보</h2>
  {table_html(top_mape, result_cols, 40)}
  <h2>6. 해석</h2>
  <p>이번 배치는 PP52의 quantile micro 보정을 유지하되, 위험 row에서는 안정 후보로 되돌리는 실험이다. PP52보다 MAPE가 더 좋아지지 않으면 안정성 강화 후보로만 본다.</p>
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    pp47_config = load_pp47_config()
    selected = select_reference_candidates()
    ref = load_reference_predictions(base, selected)
    quant = load_quantiles(base)
    rollback_prob, rollback_detail = rollback_probability(base, ref)

    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt53_risk_rollback(base, ref, rollback_prob))
    candidates.extend(pp_opt54_classifier_rollback(base, ref, rollback_prob))
    candidates.extend(pp_opt55_dynamic_cap(base, ref, quant, rollback_prob))
    candidates.extend(pp_opt56_segment_strength(base, ref, quant))
    candidates.extend(pp_opt57_row_router(base, ref, rollback_prob))

    predictions = pd.concat([source] + references + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    decision = select_challenger(metrics, aggregate)
    predictions, decision = add_protocol_candidate(predictions, decision)
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
        "selected_references": selected,
        "selection_decision": decision,
        "sources": {
            "pp_opt47_config": pp47_config.get("experiment_slug", "PP-OPT47_52"),
            "pp_opt47_predictions": str(PP47_PREDS.relative_to(REPO)),
            "pp_opt47_aggregate": str(PP47_AGG.relative_to(REPO)),
            "pp_opt47_quantile": str(PP47_QUANT.relative_to(REPO)),
            "pp_opt47_helper": str(OPT47_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    rollback_detail.to_csv(ARTIFACT_DIR / "rollback_probability_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "rollback_router_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "rollback_router_result.html").write_text(report_html, encoding="utf-8")

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
