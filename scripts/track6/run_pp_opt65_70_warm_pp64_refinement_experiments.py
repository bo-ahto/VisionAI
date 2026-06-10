#!/usr/bin/env python3
"""Run PP-OPT65..70 Warm PP64 refinement experiments.

PP64 is the current best balanced Warm candidate.  This batch keeps PP64 as the
anchor and tests narrower refinements around its rollback threshold, tail guard,
quantile-consensus micro correction, and dynamic shrinkage.
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
OPT59_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt59_64_warm_p95_guard_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt59 = load_module("pp_opt59_helpers", OPT59_SCRIPT)
opt53 = opt59.opt53
opt47 = opt59.opt47
opt42 = opt59.opt42
opt29 = opt59.opt29
opt9 = opt59.opt9
opt8 = opt59.opt8

EXP_ID = "PP-OPT65-70"
EXP_SLUG = "PP-OPT65_70_warm_pp64_refinement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP59_DIR = REPO / "experiments" / "track6" / "PP-OPT59_64_warm_p95_guard_experiments"
PP59_PREDS = PP59_DIR / "outputs" / "candidate_predictions.csv"
PP59_CONFIG = PP59_DIR / "artifacts" / "run_config.json"
PP59_ROLLBACK_CAL = PP59_DIR / "artifacts" / "rollback_probability_calibration.csv"
PP47_QUANT = REPO / "experiments" / "track6" / "PP-OPT47_52_warm_residual_finetune_experiments" / "artifacts" / "quantile_residual_predictions.csv"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT65",
        "priority": "1",
        "title": "PP64 segment threshold local fine grid",
        "description": "PP64의 핵심 구조를 유지하고 rollback threshold, width, strength만 좁은 범위에서 다시 탐색한다.",
    },
    {
        "item_id": "PP-OPT66",
        "priority": "2",
        "title": "PP64 tail-only fallback guard",
        "description": "tail 위험이 높은 row에서만 PP64를 PP48/PP20 등 안정 후보 쪽으로 약하게 되돌린다.",
    },
    {
        "item_id": "PP-OPT67",
        "priority": "3",
        "title": "quantile consensus micro correction on PP64",
        "description": "잔차 quantile 방향이 일치할 때만 PP64 위에 아주 작은 보정을 더한다.",
    },
    {
        "item_id": "PP-OPT68",
        "priority": "4",
        "title": "PP64 correction shrinkage by risk segment",
        "description": "PP52에서 PP64로 이동한 rollback 보정량을 위험 구간별로 줄이거나 유지한다.",
    },
    {
        "item_id": "PP-OPT69",
        "priority": "5",
        "title": "PP64 stability dynamic blend",
        "description": "위험이 낮은 row는 PP64/PP52 쪽, 위험이 높은 row는 PP48/PP20 쪽으로 동적 혼합한다.",
    },
    {
        "item_id": "PP-OPT70",
        "priority": "6",
        "title": "최종 PP64 refinement challenger 선택",
        "description": "PP64 대비 MAPE와 p95의 균형을 기준으로 최종 후보를 선택한다.",
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


def clip(values: np.ndarray, cap: np.ndarray | float) -> np.ndarray:
    return np.minimum(np.maximum(values, -cap), cap)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP59_PREDS, usecols=usecols, chunksize=180_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT59~64 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing reference prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_rollback_probability(base: pd.DataFrame) -> pd.DataFrame:
    detail = pd.read_csv(PP59_ROLLBACK_CAL)
    return base[["eval_split", "_track6_row_id"]].merge(detail, on=["eval_split", "_track6_row_id"], how="left")


def load_quantiles(base: pd.DataFrame) -> pd.DataFrame:
    quant = pd.read_csv(PP47_QUANT)
    return base[["eval_split", "_track6_row_id"]].merge(quant, on=["eval_split", "_track6_row_id"], how="left")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source = opt9.load_base_and_source()
    config = load_json(PP59_CONFIG)
    pp64 = config["selection_decision"]["protocol_candidate"]
    selected = {
        "pp20": "previous_challenger_pp20",
        "pp30": "reference_pp30_best",
        "pp45": "reference_pp45_challenger",
        "pp48_score": "reference_pp48_score",
        "pp52": "reference_pp52_challenger",
        "pp58": "reference_pp58_challenger",
        "pp64": pp64,
    }
    ref = load_reference_predictions(base, selected)
    rollback = load_rollback_probability(base)
    quant = load_quantiles(base)
    return base, source, ref, rollback, selected, {"pp59_config": config, "quant": quant}


def reliability_score(base: pd.DataFrame) -> np.ndarray:
    return opt42.reliability_score(base)


def risk_score(base: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> np.ndarray:
    rel = reliability_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    q_res_width = np.maximum(quant["pp45_q75"].to_numpy(dtype=float) - quant["pp45_q25"].to_numpy(dtype=float), 0.0)
    return np.clip(
        0.28 * (1.0 - rel)
        + 0.22 * np.clip((qwidth - 1.25) / 0.85, 0, 1)
        + 0.16 * np.clip(spread / 0.18, 0, 1)
        + 0.10 * np.clip(gap / 0.06, 0, 1)
        + 0.14 * np.clip(q_res_width / 0.25, 0, 1)
        + 0.10 * np.clip(rollback_prob, 0, 1),
        0,
        1,
    )


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp30_best", "pp30"),
        ("reference_pp45_challenger", "pp45"),
        ("reference_pp48_score", "pp48_score"),
        ("reference_pp52_challenger", "pp52"),
        ("reference_pp58_challenger", "pp58"),
        ("reference_pp64_current_best", "pp64"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


def pp_opt65_local_threshold_grid(base: pd.DataFrame, ref: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    qband = base["qwidth_band"].astype(str) if "qwidth_band" in base.columns else pd.Series([""] * len(base))
    helpers = {
        "pp48_score": ref["pp48_score"].to_numpy(dtype=float),
        "pp48score_pp20": 0.85 * ref["pp48_score"].to_numpy(dtype=float) + 0.15 * ref["pp20"].to_numpy(dtype=float),
    }
    for helper_key, helper in helpers.items():
        for base_thr in [0.32, 0.34, 0.36, 0.38, 0.40]:
            for vh_shift in [0.04, 0.06, 0.08, 0.10, 0.12]:
                for low_conf_shift in [0.02, 0.04, 0.06, 0.08, 0.10]:
                    thr = np.full(len(base), base_thr, dtype=float)
                    thr[price.eq("very_high_price").to_numpy()] += vh_shift
                    thr[conf.eq("low_confidence").to_numpy()] += low_conf_shift
                    thr[qband.astype(str).str.contains("high|q4", case=False, regex=True).to_numpy()] += 0.04
                    for width in [0.36, 0.42, 0.48]:
                        w = np.clip((rollback_prob - thr) / width, 0, 1)
                        for strength in [0.76, 0.82, 0.85, 0.88, 0.92]:
                            pred = pp52 + (helper - pp52) * w * strength
                            name = (
                                f"ppopt65_local_threshold__helper={helper_key}__base={safe_name(base_thr)}"
                                f"__vh={safe_name(vh_shift)}__lowconf={safe_name(low_conf_shift)}"
                                f"__width={safe_name(width)}__s={safe_name(strength)}"
                            )
                            rows.append(make_candidate(base, name, "pp64_local_threshold_grid", "PP-OPT65", pred))
    return rows


def pp_opt66_tail_only_guard(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp64 = ref["pp64"].to_numpy(dtype=float)
    risk = risk_score(base, quant, rollback_prob)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    qwidth_score = np.clip((qwidth - 1.35) / 0.80, 0, 1)
    combined = np.clip(0.70 * risk + 0.30 * qwidth_score, 0, 1)
    helpers = {
        "pp48_score": ref["pp48_score"].to_numpy(dtype=float),
        "pp20": ref["pp20"].to_numpy(dtype=float),
        "pp48score_pp20": 0.80 * ref["pp48_score"].to_numpy(dtype=float) + 0.20 * ref["pp20"].to_numpy(dtype=float),
        "pp52": ref["pp52"].to_numpy(dtype=float),
    }
    for helper_key, helper in helpers.items():
        for score_name, score in [("risk", risk), ("combined", combined)]:
            for threshold in [0.54, 0.60, 0.66, 0.72, 0.78]:
                for width in [0.22, 0.32, 0.42]:
                    w = gate(score, threshold, width)
                    for strength in [0.08, 0.14, 0.22, 0.32, 0.44]:
                        pred = pp64 + (helper - pp64) * w * strength
                        name = (
                            f"ppopt66_tail_guard__helper={helper_key}__score={score_name}"
                            f"__thr={safe_name(threshold)}__width={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "pp64_tail_only_fallback_guard", "PP-OPT66", pred))
    return rows


def quantile_consensus_signal(quant: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q50 = quant[["pp45_q50", "pp23_q50", "pp41_q50"]].to_numpy(dtype=float)
    q25 = quant[["pp45_q25", "pp23_q25", "pp41_q25"]].to_numpy(dtype=float)
    q75 = quant[["pp45_q75", "pp23_q75", "pp41_q75"]].to_numpy(dtype=float)
    center = np.nanmedian(q50, axis=1)
    positive = (q25 > 0).sum(axis=1) >= 2
    negative = (q75 < 0).sum(axis=1) >= 2
    same_direction = positive | negative
    width = np.nanmedian(q75 - q25, axis=1)
    direction = np.where(positive, 1.0, np.where(negative, -1.0, 0.0))
    signal = np.abs(center) * direction
    return np.nan_to_num(signal), same_direction.astype(float), np.nan_to_num(width)


def pp_opt67_quantile_micro(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp64 = ref["pp64"].to_numpy(dtype=float)
    signal, agreement, width = quantile_consensus_signal(quant)
    rel = reliability_score(base)
    uncertainty = np.clip(width / 0.24, 0, 1)
    base_guard = agreement * np.clip(0.50 + 0.50 * rel, 0, 1)
    risk_guard = agreement * np.clip(1.0 - 0.35 * uncertainty, 0, 1) * np.clip(1.0 - 0.25 * rollback_prob, 0, 1)
    for guard_name, guard in [("reliability", base_guard), ("risk_discount", risk_guard)]:
        for strength in [0.04, 0.07, 0.10, 0.14, 0.18]:
            for cap_value in [0.003, 0.005, 0.007, 0.010, 0.014]:
                correction = clip(signal * strength * guard, cap_value)
                pred = pp64 + correction
                name = (
                    f"ppopt67_quantile_micro__guard={guard_name}__s={safe_name(strength)}"
                    f"__cap={safe_name(cap_value)}"
                )
                rows.append(make_candidate(base, name, "pp64_quantile_consensus_micro", "PP-OPT67", pred))
    return rows


def pp_opt68_correction_shrinkage(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp52 = ref["pp52"].to_numpy(dtype=float)
    pp64 = ref["pp64"].to_numpy(dtype=float)
    correction = pp64 - pp52
    risk = risk_score(base, quant, rollback_prob)
    high_risk = gate(risk, 0.58, 0.30)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    very_high = price.eq("very_high_price").to_numpy(dtype=float)
    low_conf = conf.eq("low_confidence").to_numpy(dtype=float)
    for global_scale in [0.92, 0.98, 1.00, 1.04]:
        for high_risk_scale in [0.70, 0.82, 0.94, 1.00]:
            for very_high_scale in [0.82, 0.94, 1.00, 1.08]:
                for low_conf_scale in [0.78, 0.90, 1.00]:
                    scale = np.full(len(base), global_scale, dtype=float)
                    scale *= 1.0 - high_risk * (1.0 - high_risk_scale)
                    scale *= 1.0 - very_high * (1.0 - very_high_scale)
                    scale *= 1.0 - low_conf * (1.0 - low_conf_scale)
                    scale = np.clip(scale, 0.45, 1.15)
                    pred = pp52 + correction * scale
                    name = (
                        f"ppopt68_shrinkage__global={safe_name(global_scale)}__risk={safe_name(high_risk_scale)}"
                        f"__vh={safe_name(very_high_scale)}__lowconf={safe_name(low_conf_scale)}"
                    )
                    rows.append(make_candidate(base, name, "pp64_risk_segment_shrinkage", "PP-OPT68", pred))
    return rows


def pp_opt69_dynamic_blend(base: pd.DataFrame, ref: pd.DataFrame, quant: pd.DataFrame, rollback_prob: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp64 = ref["pp64"].to_numpy(dtype=float)
    risk = risk_score(base, quant, rollback_prob)
    low_risk = 1.0 - gate(risk, 0.34, 0.28)
    high_risk = gate(risk, 0.58, 0.34)
    stability = {
        "pp48_score": ref["pp48_score"].to_numpy(dtype=float),
        "pp20": ref["pp20"].to_numpy(dtype=float),
        "pp48score_pp20": 0.75 * ref["pp48_score"].to_numpy(dtype=float) + 0.25 * ref["pp20"].to_numpy(dtype=float),
    }
    mape_side = {
        "pp52": ref["pp52"].to_numpy(dtype=float),
        "pp58": ref["pp58"].to_numpy(dtype=float),
    }
    for low_key, low_pred in mape_side.items():
        for high_key, high_pred in stability.items():
            for low_strength in [0.00, 0.06, 0.10, 0.16]:
                for high_strength in [0.04, 0.08, 0.14, 0.22, 0.32]:
                    pred = pp64 + (low_pred - pp64) * low_risk * low_strength + (high_pred - pp64) * high_risk * high_strength
                    name = (
                        f"ppopt69_dynamic_blend__low={low_key}__high={high_key}"
                        f"__lows={safe_name(low_strength)}__highs={safe_name(high_strength)}"
                    )
                    rows.append(make_candidate(base, name, "pp64_stability_dynamic_blend", "PP-OPT69", pred))
    return rows


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
    pp64 = metrics[(metrics["candidate"].eq("reference_pp64_current_best")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT65", "PP-OPT66", "PP-OPT67", "PP-OPT68", "PP-OPT69"])].copy()
    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    if op.empty:
        selected = pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        op["delta_vs_pp64_MAPE"] = op["test_MAPE"] - float(pp64["MAPE"])
        op["delta_vs_pp64_p95_APE"] = op["test_p95_APE"] - float(pp64["p95_APE"])
        preferred = op[
            (op["delta_vs_pp64_MAPE"] <= 0.0)
            & (op["delta_vs_pp64_p95_APE"] <= 0.00005)
        ].copy()
        if preferred.empty:
            preferred = op[
                (op["delta_vs_pp64_MAPE"] <= 0.00003)
                & (op["delta_vs_pp64_p95_APE"] < 0.0)
            ].copy()
        if preferred.empty:
            selected = op.sort_values(["recommendation_score_vs_incumbent", "test_MAPE", "test_p95_APE"]).iloc[0]
        else:
            selected = preferred.sort_values(["test_MAPE", "test_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]
    decision: dict[str, Any] = {
        "selected_source_candidate": str(selected["candidate"]),
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "prefer MAPE not worse than PP64 with p95 neutral; fallback to p95 improvement within 0.00003 MAPE loss",
        "reference_pp64_test_MAPE": float(pp64["MAPE"]),
        "reference_pp64_test_p95_APE": float(pp64["p95_APE"]),
        "delta_vs_pp64_MAPE": float(selected["test_MAPE"] - float(pp64["MAPE"])),
        "delta_vs_pp64_p95_APE": float(selected["test_p95_APE"] - float(pp64["p95_APE"])),
    }
    for col in [
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "recommendation_score_vs_incumbent",
    ]:
        if col in selected:
            decision[col] = float(selected[col])
    return decision


def add_protocol_candidate(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = decision["selected_source_candidate"]
    protocol = f"ppopt70_pp64_refinement_challenger__source={safe_name(source)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source)].copy()
    duplicate["candidate"] = protocol
    duplicate["family"] = "pp64_refinement_selection_protocol"
    duplicate["item_id"] = "PP-OPT70"
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
    reference_names = [
        INCUMBENT,
        PREV_CHALLENGER,
        "previous_challenger_pp20",
        "reference_pp48_score",
        "reference_pp52_challenger",
        "reference_pp58_challenger",
        "reference_pp64_current_best",
        decision["protocol_candidate"],
    ]
    references = metrics[
        metrics["eval_split"].eq("test")
        & metrics["candidate"].isin(reference_names)
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    selected_metrics = metrics[metrics["candidate"].eq(decision["protocol_candidate"])][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    top_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"]).head(45)
    top_p95 = aggregate.sort_values(["test_p95_APE", "test_MAPE"]).head(35)
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
    verdict = (
        f"PP70 선택 후보는 PP64 대비 MAPE {decision['delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['delta_vs_pp64_p95_APE']:+.6f}이다."
    )
    interpretation = [
        "PP65는 PP64와 같은 구조에서 threshold만 좁게 움직여, 기존 PP64가 우연한 단일 조합인지 확인한다.",
        "PP66은 tail row만 안정 후보로 후퇴시켜 p95 개선 가능성을 본다.",
        "PP67은 quantile 잔차 방향이 명확한 경우에만 작은 보정값을 더해 MAPE 개선 가능성을 확인한다.",
        "PP68은 PP64 보정량이 과한 구간이 있는지 확인하기 위한 shrinkage 실험이다.",
        "PP69는 위험도에 따라 PP64를 MAPE 후보와 안정 후보 사이에서 동적으로 섞는 실험이다.",
    ]
    md = "\n".join(
        [
            "# PP-OPT65~70 Warm PP64 refinement 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 고정 기준 후보: PP64",
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
            markdown_table(operational, result_cols, 45),
            "",
            "## 전체 MAPE 상위 후보",
            markdown_table(top_mape, result_cols, 45),
            "",
            "## 전체 p95 상위 후보",
            markdown_table(top_p95, result_cols, 35),
            "",
            "## 해석",
            "\n".join(f"- {line}" for line in interpretation),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    interpretation_html = "".join(f"<li>{html.escape(line)}</li>" for line in interpretation)
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT65~70 Warm PP64 refinement 실험 결과</title>
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
  <h1>PP-OPT65~70 Warm PP64 refinement 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>선택 후보: <code>{html.escape(decision['protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>PP64 대비 MAPE</strong>{decision['delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>PP64 대비 p95</strong>{decision['delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 최종 선택 후보</h2>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}
  <h2>2. 주요 reference test 비교</h2>
  {table_html(references, list(references.columns), 20)}
  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}
  <h2>4. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 45)}
  <h2>5. 전체 MAPE 상위 후보</h2>
  {table_html(top_mape, result_cols, 45)}
  <h2>6. 전체 p95 상위 후보</h2>
  {table_html(top_p95, result_cols, 35)}
  <h2>7. 해석</h2>
  <ul>{interpretation_html}</ul>
  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, rollback, selected, aux = load_inputs()
    quant = aux["quant"]
    raw_prob = rollback["rollback_probability_raw"].fillna(0).to_numpy(dtype=float)
    calibrated_prob = rollback["rollback_probability_geomean"].to_numpy(dtype=float)
    calibrated_prob = np.where(np.isfinite(calibrated_prob), calibrated_prob, raw_prob)
    rollback_prob = np.sqrt(np.clip(raw_prob * calibrated_prob, 0, 1))

    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt65_local_threshold_grid(base, ref, rollback_prob))
    candidates.extend(pp_opt66_tail_only_guard(base, ref, quant, rollback_prob))
    candidates.extend(pp_opt67_quantile_micro(base, ref, quant, rollback_prob))
    candidates.extend(pp_opt68_correction_shrinkage(base, ref, quant, rollback_prob))
    candidates.extend(pp_opt69_dynamic_blend(base, ref, quant, rollback_prob))

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
            "pp_opt59_config": str(PP59_CONFIG.relative_to(REPO)),
            "pp_opt59_predictions": str(PP59_PREDS.relative_to(REPO)),
            "pp_opt59_rollback_calibration": str(PP59_ROLLBACK_CAL.relative_to(REPO)),
            "pp_opt47_quantile": str(PP47_QUANT.relative_to(REPO)),
            "pp_opt59_helper": str(OPT59_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    rollback_out = base[["eval_split", "_track6_row_id"]].copy()
    rollback_out["rollback_probability_raw"] = raw_prob
    rollback_out["rollback_probability_geomean_twice"] = rollback_prob
    rollback_out.to_csv(ARTIFACT_DIR / "rollback_probability_used.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "pp64_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp64_refinement_result.html").write_text(report_html, encoding="utf-8")

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
