#!/usr/bin/env python3
"""Run PP-OPT59..64 Warm p95 guard experiments.

PP-OPT58 improved MAPE over PP52, but gave back a small amount of p95.
This batch keeps the PP58/PP52 improvement path and searches for guards that
recover p95 without discarding the MAPE gain.
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
OPT53_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt53_58_warm_rollback_router_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt53 = load_module("pp_opt53_helpers", OPT53_SCRIPT)
opt47 = opt53.opt47
opt42 = opt53.opt42
opt29 = opt53.opt29
opt9 = opt53.opt9
opt8 = opt53.opt8

EXP_ID = "PP-OPT59-64"
EXP_SLUG = "PP-OPT59_64_warm_p95_guard_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP53_DIR = REPO / "experiments" / "track6" / "PP-OPT53_58_warm_rollback_router_experiments"
PP53_PREDS = PP53_DIR / "outputs" / "candidate_predictions.csv"
PP53_AGG = PP53_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP53_CONFIG = PP53_DIR / "artifacts" / "run_config.json"
PP53_ROLLBACK = PP53_DIR / "artifacts" / "rollback_probability_detail.csv"
PP47_QUANT = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments" / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT59",
        "priority": "1",
        "title": "PP58 rollback threshold/strength fine grid",
        "description": "PP58 근처의 classifier rollback threshold, width, strength를 더 촘촘히 탐색한다.",
    },
    {
        "item_id": "PP-OPT60",
        "priority": "2",
        "title": "PP58 tail-risk guard",
        "description": "tail risk가 높은 row에서 PP58을 PP52/PP48/PP20 쪽으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT61",
        "priority": "3",
        "title": "rollback classifier probability calibration",
        "description": "rollback 확률을 OOF bin calibration한 뒤 classifier rollback을 다시 적용한다.",
    },
    {
        "item_id": "PP-OPT62",
        "priority": "4",
        "title": "segment별 rollback threshold",
        "description": "가격대/신뢰도/불확실성 구간별로 rollback threshold를 조정한다.",
    },
    {
        "item_id": "PP-OPT63",
        "priority": "5",
        "title": "MAPE 후보와 안정 후보 2단계 router",
        "description": "먼저 PP52/PP58 계열을 고르고, tail 위험 row만 안정 후보로 override한다.",
    },
    {
        "item_id": "PP-OPT64",
        "priority": "6",
        "title": "최종 p95 guard challenger 선택",
        "description": "PP58 대비 p95 회복과 MAPE 유지 조건을 함께 고려해 최종 후보를 선택한다.",
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


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_reference_candidates() -> dict[str, str]:
    cfg = load_json(PP53_CONFIG)
    # These reference names exist in PP53 candidate_predictions.csv.
    refs = {
        "pp20": PREV_CHALLENGER,
        "pp23": "reference_pp23",
        "pp30": "reference_pp30_best",
        "pp38": "reference_pp38_best",
        "pp45": "reference_pp45_challenger",
        "pp48_score": "reference_pp48_score",
        "pp52": "reference_pp52_challenger",
        "pp58": cfg["selection_decision"]["protocol_candidate"],
    }
    # PP48_mape was a PP47 reference used by PP53 but not emitted as a PP53
    # reference row, so load it via the PP53 helper from PP47 outputs.
    refs["pp48_mape"] = load_json(PP53_CONFIG)["selected_references"]["pp48_mape"]
    return refs


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    pp53_labels = {k: v for k, v in selected.items() if k != "pp48_mape"}
    needed = set(pp53_labels.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP53_PREDS, usecols=usecols, chunksize=160_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT53~58 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in pp53_labels.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")

    # Load PP48_mape through PP53's reference loader from PP47 outputs.
    prior_selected = opt53.select_reference_candidates()
    prior = opt53.load_reference_predictions(base, prior_selected)
    out["pp48_mape"] = prior["pp48_mape"].to_numpy(dtype=float)

    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing reference prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_rollback_detail(base: pd.DataFrame) -> pd.DataFrame:
    detail = pd.read_csv(PP53_ROLLBACK)
    return base[["eval_split", "_track6_row_id"]].merge(detail, on=["eval_split", "_track6_row_id"], how="left")


def load_quantiles(base: pd.DataFrame) -> pd.DataFrame:
    quant = pd.read_csv(PP47_QUANT)
    return base[["eval_split", "_track6_row_id"]].merge(quant, on=["eval_split", "_track6_row_id"], how="left")


def reliability_score(base: pd.DataFrame) -> np.ndarray:
    return opt42.reliability_score(base)


def risk_score(base: pd.DataFrame, quant: pd.DataFrame) -> np.ndarray:
    rel = reliability_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    q_res_width = np.maximum(quant["pp45_q75"].to_numpy(dtype=float) - quant["pp45_q25"].to_numpy(dtype=float), 0.0)
    return np.clip(
        0.34 * (1.0 - rel)
        + 0.22 * np.clip((qwidth - 1.25) / 0.85, 0, 1)
        + 0.18 * np.clip(spread / 0.18, 0, 1)
        + 0.10 * np.clip(gap / 0.06, 0, 1)
        + 0.16 * np.clip(q_res_width / 0.25, 0, 1),
        0,
        1,
    )


def bin_calibrate_probability(base: pd.DataFrame, raw_prob: np.ndarray, label: np.ndarray, bins: int = 8, smoothing: float = 18.0) -> np.ndarray:
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    p_val = raw_prob[val_mask]
    y_val = label[val_mask].astype(float)
    global_rate = float(y_val.mean()) if len(y_val) else 0.5
    edges = np.unique(np.quantile(p_val, np.linspace(0.0, 1.0, bins + 1)))
    if len(edges) < 3:
        return np.full_like(raw_prob, global_rate, dtype=float)
    bucket = np.clip(np.searchsorted(edges[1:-1], raw_prob, side="right"), 0, len(edges) - 2)
    calibrated = np.full_like(raw_prob, global_rate, dtype=float)
    for b in range(len(edges) - 1):
        train_idx = val_mask & (bucket == b)
        n = int(train_idx.sum())
        if n == 0:
            rate = global_rate
        else:
            rate = (float(label[train_idx].sum()) + smoothing * global_rate) / (n + smoothing)
        calibrated[bucket == b] = rate
    order = np.argsort(raw_prob)
    calibrated_sorted = np.maximum.accumulate(calibrated[order])
    out = np.empty_like(calibrated)
    out[order] = calibrated_sorted
    return np.clip(out, 0.0, 1.0)


def pp_opt59_fine_classifier_grid(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    for helper_key in ["pp48_mape", "pp48_score"]:
        helper = ref[helper_key].to_numpy(dtype=float)
        for threshold in [0.36, 0.40, 0.44, 0.48, 0.52]:
            for width in [0.32, 0.40, 0.48, 0.56]:
                base_w = gate(rollback_prob, threshold, width)
                for strength in [0.58, 0.66, 0.74, 0.82, 0.90]:
                    pred = pp52 + (helper - pp52) * base_w * strength
                    name = f"ppopt59_fine_classifier__helper={helper_key}__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "fine_classifier_rollback", "PP-OPT59", pred))
    return rows


def pp_opt60_tail_guard(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp58 = ref["pp58"].to_numpy(dtype=float)
    risk = risk_score(base, quant)
    combined = np.clip(0.60 * risk + 0.40 * rollback_prob, 0, 1)
    for helper_key in ["pp52", "pp48_score", "pp20", "pp30"]:
        helper = ref[helper_key].to_numpy(dtype=float)
        for score_name, score in [("risk", risk), ("combined", combined)]:
            for threshold in [0.42, 0.52, 0.62, 0.72]:
                w = gate(score, threshold, 0.36)
                for strength in [0.18, 0.30, 0.45, 0.60]:
                    pred = pp58 + (helper - pp58) * w * strength
                    name = f"ppopt60_tail_guard__helper={helper_key}__score={score_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "pp58_tail_risk_guard", "PP-OPT60", pred))
    return rows


def pp_opt61_calibrated_rollback(base: pd.DataFrame, ref: pd.DataFrame, raw_prob: np.ndarray, label: np.ndarray) -> tuple[list[pd.DataFrame], pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    calibrated = bin_calibrate_probability(base, raw_prob, label, bins=8, smoothing=20.0)
    geomean = np.sqrt(np.clip(raw_prob * calibrated, 0, 1))
    for prob_name, prob in [("calibrated", calibrated), ("geomean", geomean)]:
        for helper_key in ["pp48_mape", "pp48_score", "pp45"]:
            helper = ref[helper_key].to_numpy(dtype=float)
            for threshold in [0.08, 0.12, 0.18, 0.24, 0.32]:
                for width in [0.34, 0.46, 0.58]:
                    base_w = gate(prob, threshold, width)
                    for strength in [0.35, 0.55, 0.75, 0.90]:
                        pred = pp52 + (helper - pp52) * base_w * strength
                        name = (
                            f"ppopt61_calibrated_rollback__prob={prob_name}__helper={helper_key}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "calibrated_rollback_probability", "PP-OPT61", pred))
    detail = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "rollback_probability_raw": raw_prob,
            "rollback_probability_calibrated": calibrated,
            "rollback_probability_geomean": geomean,
            "rollback_label": label.astype(int),
        }
    )
    return rows, detail


def pp_opt62_segment_threshold(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    qband = base["qwidth_band"].astype(str) if "qwidth_band" in base.columns else pd.Series([""] * len(base))
    for helper_key in ["pp48_mape", "pp48_score", "pp45"]:
        helper = ref[helper_key].to_numpy(dtype=float)
        for base_thr in [0.28, 0.36, 0.44, 0.52]:
            for vh_shift in [-0.08, 0.00, 0.08]:
                for low_conf_shift in [-0.06, 0.00, 0.06]:
                    thr = np.full(len(base), base_thr, dtype=float)
                    thr[price.eq("very_high_price").to_numpy()] += vh_shift
                    thr[conf.eq("low_confidence").to_numpy()] += low_conf_shift
                    thr[qband.astype(str).str.contains("high|q4", case=False, regex=True).to_numpy()] += 0.04
                    w = np.clip((rollback_prob - thr) / 0.42, 0, 1)
                    for strength in [0.45, 0.65, 0.85]:
                        pred = pp52 + (helper - pp52) * w * strength
                        name = (
                            f"ppopt62_segment_threshold__helper={helper_key}__base={safe_name(base_thr)}"
                            f"__vh={safe_name(vh_shift)}__lowconf={safe_name(low_conf_shift)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "segment_rollback_threshold", "PP-OPT62", pred))
    return rows


def pp_opt63_two_stage_router(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    pp58 = ref["pp58"].to_numpy(dtype=float)
    mape_candidate = 0.55 * pp58 + 0.45 * pp52
    risk = risk_score(base, quant)
    combined = np.clip(0.50 * rollback_prob + 0.50 * risk, 0, 1)
    safe_sets = {
        "pp48score_pp20": 0.70 * ref["pp48_score"].to_numpy(dtype=float) + 0.30 * ref["pp20"].to_numpy(dtype=float),
        "pp48score_pp30": 0.70 * ref["pp48_score"].to_numpy(dtype=float) + 0.30 * ref["pp30"].to_numpy(dtype=float),
        "pp52_pp48score": 0.70 * pp52 + 0.30 * ref["pp48_score"].to_numpy(dtype=float),
        "pp52_pp20": 0.80 * pp52 + 0.20 * ref["pp20"].to_numpy(dtype=float),
    }
    for safe_name_key, safe_pred in safe_sets.items():
        for threshold in [0.36, 0.46, 0.56, 0.66]:
            base_w = gate(combined, threshold, 0.38)
            for max_w in [0.25, 0.40, 0.55, 0.75]:
                for sharp in [0.75, 1.00, 1.35]:
                    w = np.clip((base_w**sharp) * max_w, 0, 1)
                    pred = mape_candidate + (safe_pred - mape_candidate) * w
                    name = f"ppopt63_two_stage_router__safe={safe_name_key}__thr={safe_name(threshold)}__max={safe_name(max_w)}__sharp={safe_name(sharp)}"
                    rows.append(make_candidate(base, name, "two_stage_mape_stability_router", "PP-OPT63", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp23", "pp23"),
        ("reference_pp30_best", "pp30"),
        ("reference_pp38_best", "pp38"),
        ("reference_pp45_challenger", "pp45"),
        ("reference_pp48_score", "pp48_score"),
        ("reference_pp52_challenger", "pp52"),
        ("reference_pp58_challenger", "pp58"),
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
    pp58 = metrics[(metrics["candidate"].eq("reference_pp58_challenger")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pp52 = metrics[(metrics["candidate"].eq("reference_pp52_challenger")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT59", "PP-OPT60", "PP-OPT61", "PP-OPT62", "PP-OPT63"])].copy()
    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    if op.empty:
        selected = pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        op["delta_vs_pp58_MAPE"] = op["test_MAPE"] - float(pp58["MAPE"])
        op["delta_vs_pp58_p95_APE"] = op["test_p95_APE"] - float(pp58["p95_APE"])
        op["delta_vs_pp52_MAPE"] = op["test_MAPE"] - float(pp52["MAPE"])
        op["delta_vs_pp52_p95_APE"] = op["test_p95_APE"] - float(pp52["p95_APE"])
        preferred = op[
            (op["delta_vs_pp58_MAPE"] <= 0.000015)
            & (op["delta_vs_pp58_p95_APE"] < 0)
            & (op["test_delta_vs_incumbent_p95_APE"] <= 0)
        ].copy()
        if preferred.empty:
            preferred = op[
                (op["delta_vs_pp52_MAPE"] < 0)
                & (op["test_delta_vs_incumbent_p95_APE"] <= 0)
            ].copy()
        if preferred.empty:
            selected = op[op["test_delta_vs_incumbent_p95_APE"] <= 0].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
        else:
            selected = preferred.sort_values(["test_MAPE", "test_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]
    decision: dict[str, Any] = {
        "selected_source_candidate": str(selected["candidate"]),
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "prefer PP58 p95 recovery while preserving PP58 MAPE within 0.000015; fallback to PP52 MAPE improvement with p95 safe",
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
        if col in selected:
            decision[col] = float(selected[col])
    return decision


def add_protocol_candidate(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = decision["selected_source_candidate"]
    protocol = f"ppopt64_p95_guard_challenger__source={safe_name(source)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source)].copy()
    duplicate["candidate"] = protocol
    duplicate["family"] = "p95_guard_selection_protocol"
    duplicate["item_id"] = "PP-OPT64"
    out = dict(decision)
    out["protocol_candidate"] = protocol
    return pd.concat([predictions, duplicate], ignore_index=True), out


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
            "reference_pp58_challenger",
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
    pp58 = references[references["candidate"].eq("reference_pp58_challenger")]
    selected_test = selected_metrics[selected_metrics["eval_split"].eq("test")]
    if not pp58.empty and not selected_test.empty:
        verdict = (
            f"PP64 선택 후보는 PP58 대비 MAPE {float(selected_test.iloc[0]['MAPE']) - float(pp58.iloc[0]['MAPE']):+.6f}, "
            f"p95 {float(selected_test.iloc[0]['p95_APE']) - float(pp58.iloc[0]['p95_APE']):+.6f}이다."
        )
    else:
        verdict = "PP64 선택 후보를 산출했다."

    md = "\n".join(
        [
            "# PP-OPT59~64 Warm p95 guard 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            "- 비교 후보: PP20, PP23, PP30, PP38, PP45, PP52, PP58",
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
            "이번 배치는 PP58의 MAPE 이득을 유지하면서 p95를 회복하는 실험이다. 선택 후보가 PP58보다 MAPE를 거의 유지하고 p95를 낮추면 운영 후보로 더 균형적이다.",
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
  <title>PP-OPT59~64 Warm p95 guard 실험 결과</title>
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
  <h1>PP-OPT59~64 Warm p95 guard 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>선택 후보: <code>{html.escape(decision['protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision.get('test_delta_vs_incumbent_MAPE', float('nan')):.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision.get('test_delta_vs_incumbent_p95_APE', float('nan')):.6f}</div>
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
  <p>이번 배치는 PP58의 MAPE 이득을 유지하면서 p95를 회복하는 실험이다. 선택 후보가 PP58보다 MAPE를 거의 유지하고 p95를 낮추면 운영 후보로 더 균형적이다.</p>
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    pp53_config = load_json(PP53_CONFIG)
    selected = select_reference_candidates()
    ref = load_reference_predictions(base, selected)
    rollback = load_rollback_detail(base)
    quant = load_quantiles(base)
    raw_prob = rollback["pp52_rollback_probability"].fillna(0).to_numpy(dtype=float)
    label = rollback["pp52_worse_than_safe_label"].fillna(0).to_numpy(dtype=int)

    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt59_fine_classifier_grid(base, ref, raw_prob))
    candidates.extend(pp_opt60_tail_guard(base, ref, quant, raw_prob))
    pp61_rows, calibration_detail = pp_opt61_calibrated_rollback(base, ref, raw_prob, label)
    candidates.extend(pp61_rows)
    candidates.extend(pp_opt62_segment_threshold(base, ref, raw_prob))
    candidates.extend(pp_opt63_two_stage_router(base, ref, quant, raw_prob))

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
            "pp_opt53_config": pp53_config.get("experiment_slug", "PP-OPT53_58"),
            "pp_opt53_predictions": str(PP53_PREDS.relative_to(REPO)),
            "pp_opt53_aggregate": str(PP53_AGG.relative_to(REPO)),
            "pp_opt53_rollback": str(PP53_ROLLBACK.relative_to(REPO)),
            "pp_opt47_quantile": str(PP47_QUANT.relative_to(REPO)),
            "pp_opt53_helper": str(OPT53_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    calibration_detail.to_csv(ARTIFACT_DIR / "rollback_probability_calibration.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "p95_guard_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "p95_guard_result.html").write_text(report_html, encoding="utf-8")

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
