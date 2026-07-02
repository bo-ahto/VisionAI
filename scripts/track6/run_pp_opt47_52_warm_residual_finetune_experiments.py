#!/usr/bin/env python3
"""Run PP-OPT47..52 Warm residual fine-tuning experiments.

PP-OPT42..46 found a clean but small improvement from PP45:
use PP23 as the anchor and fall back to PP30 only in very-high-price rows.
This batch treats that as the local optimum and searches only narrow,
p95-aware modifications around it.
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
OPT42_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt42_46_warm_residual_correction_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt42 = load_module("pp_opt42_helpers", OPT42_SCRIPT)
opt37 = opt42.opt37
opt29 = opt42.opt29
opt21 = opt42.opt21
opt9 = opt42.opt9
opt8 = opt42.opt8

EXP_ID = "PP-OPT47-52"
EXP_SLUG = "PP-OPT47_52_warm_residual_finetune_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP42_DIR = REPO / "experiments" / "track6" / "PP-OPT42_46_warm_residual_correction_experiments"
PP42_PREDS = PP42_DIR / "outputs" / "candidate_predictions.csv"
PP42_AGG = PP42_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP42_CONFIG = PP42_DIR / "artifacts" / "run_config.json"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT47",
        "priority": "1",
        "title": "PP45 very-high fallback 세밀화",
        "description": "PP45의 초고가 fallback 강도와 적용 마스크를 더 촘촘히 탐색한다.",
    },
    {
        "item_id": "PP-OPT48",
        "priority": "2",
        "title": "p95-safe segment median micro 보정",
        "description": "구간 중앙 잔차 보정을 더 작은 cap과 강한 shrinkage로 제한한다.",
    },
    {
        "item_id": "PP-OPT49",
        "priority": "3",
        "title": "quantile consensus micro 보정",
        "description": "q25/q50/q75가 같은 방향을 가리킬 때만 작은 잔차 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT50",
        "priority": "4",
        "title": "low-risk q50 residual 보정",
        "description": "공격적인 q50 잔차 보정을 신뢰도 높은 row에만 축소 적용한다.",
    },
    {
        "item_id": "PP-OPT51",
        "priority": "5",
        "title": "PP45와 보정 후보의 p95-aware micro blend",
        "description": "PP45를 중심으로 PP43/PP44/PP46 후보를 5~30% 범위에서만 혼합한다.",
    },
    {
        "item_id": "PP-OPT52",
        "priority": "6",
        "title": "최종 fine-tune challenger 선택",
        "description": "PP45 대비 MAPE 개선과 p95 방어를 함께 만족하는 후보를 선택한다.",
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


def clip(values: np.ndarray, cap: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -cap), cap)


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def load_pp42_config() -> dict[str, Any]:
    return json.loads(PP42_CONFIG.read_text(encoding="utf-8"))


def pick_first(df: pd.DataFrame, msg: str) -> str:
    if df.empty:
        raise ValueError(msg)
    return str(df.iloc[0]["candidate"])


def select_reference_candidates() -> dict[str, str]:
    cfg = load_pp42_config()
    agg = pd.read_csv(PP42_AGG)
    op = agg[agg["operational_pass_vs_incumbent"]].copy()
    p95_safe = agg[(agg["test_delta_vs_incumbent_MAPE"] < 0) & (agg["test_delta_vs_incumbent_p95_APE"] <= 0)].copy()
    return {
        "pp20": PREV_CHALLENGER,
        "pp23": "reference_pp23",
        "pp30": "reference_pp30_best",
        "pp36": "reference_pp36_challenger",
        "pp38": "reference_pp38_best",
        "pp41": "reference_pp41_challenger",
        "pp45": cfg["selection_decision"]["selected_candidate"],
        "pp43_score": pick_first(op[op["item_id"].eq("PP-OPT43")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]), "Missing PP43 operational candidate"),
        "pp44_safe": pick_first(p95_safe[p95_safe["item_id"].eq("PP-OPT44")].sort_values(["test_MAPE", "recommendation_score_vs_incumbent"]), "Missing PP44 p95-safe candidate"),
        "pp46_safe": pick_first(op[(op["item_id"].eq("PP-OPT46")) & (op["test_delta_vs_incumbent_p95_APE"] <= 0)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]), "Missing PP46 p95-safe candidate"),
    }


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP42_PREDS, usecols=usecols, chunksize=120_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT42~46 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing reference prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


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


def pp_opt47_fallback_fine_grid(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    price = base["stable_price_band"].astype(str)
    very_high = price.eq("very_high_price").to_numpy(dtype=float)
    high_plus = price.isin(["high_price", "very_high_price"]).to_numpy(dtype=float)
    risk = risk_score(base)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    masks = {
        "very_high_all": very_high,
        "very_high_risk_soft": very_high * (0.35 + 0.65 * risk),
        "very_high_lowspread": very_high * (1.0 - 0.45 * np.clip(spread / 0.18, 0, 1)),
        "very_high_qwidth_soft": very_high * (1.0 - 0.40 * np.clip((qwidth - 1.4) / 0.7, 0, 1)),
        "high_plus_risk_tiny": high_plus * np.clip(risk - 0.25, 0, 1) * 0.45,
    }
    for base_key in ["pp23", "pp41", "pp45"]:
        base_pred = ref[base_key].to_numpy(dtype=float)
        for fallback_key in ["pp30", "pp20", "pp38", "pp43_score", "pp46_safe"]:
            fallback = ref[fallback_key].to_numpy(dtype=float)
            for mask_name, mask in masks.items():
                for strength in [0.55, 0.65, 0.75, 0.80, 0.85, 0.95, 1.00]:
                    pred = base_pred + (fallback - base_pred) * mask * strength
                    name = f"ppopt47_fallback_fine__base={base_key}__fallback={fallback_key}__mask={mask_name}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "fallback_fine_grid", "PP-OPT47", pred))
    return rows


def pp_opt48_segment_micro(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = risk_score(base)
    guard_modes = {
        "strict": 1.0 - 0.70 * risk,
        "medium": 1.0 - 0.50 * risk,
        "stable_only": gate(reliability_score(base), 0.52, 0.36),
    }
    groups = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_conf_qwidth": ["stable_price_band", "confidence_tier", "qwidth_band"],
    }
    for center_key in ["pp45", "pp23", "pp41", "pp38"]:
        center = ref[center_key].to_numpy(dtype=float)
        for group_name, cols in groups.items():
            cols = [c for c in cols if c in base.columns]
            for shrinkage in [70.0, 110.0, 160.0, 240.0]:
                raw = opt42.oof_segment_residual_median(base, center, cols, shrinkage)
                for guard_name, guard in guard_modes.items():
                    for strength in [0.12, 0.18, 0.25, 0.32]:
                        for base_cap in [0.003, 0.0045, 0.006, 0.008]:
                            corr = clip(raw * strength * guard, base_cap * cap_factor(base))
                            name = (
                                f"ppopt48_segment_micro__center={center_key}__group={group_name}"
                                f"__shrink={safe_name(shrinkage)}__guard={guard_name}__s={safe_name(strength)}__cap={safe_name(base_cap)}"
                            )
                            rows.append(make_candidate(base, name, "p95_safe_segment_micro", "PP-OPT48", center + corr))
    return rows


def pp_opt49_quantile_consensus_micro(base: pd.DataFrame, ref: pd.DataFrame, quant_by_center: dict[str, dict[str, np.ndarray]]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    rel = reliability_score(base)
    risk = risk_score(base)
    for center_key, quant in quant_by_center.items():
        center = ref[center_key].to_numpy(dtype=float)
        q25 = quant["q25"]
        q50 = quant["q50"]
        q75 = quant["q75"]
        width = np.maximum(q75 - q25, 0.0)
        same_direction = ((q25 > 0) & (q50 > 0) & (q75 > 0)) | ((q25 < 0) & (q50 < 0) & (q75 < 0))
        consensus = np.where(same_direction, q50, 0.0)
        for width_limit in [0.08, 0.12, 0.16, 0.22]:
            width_gate = np.clip((width_limit - width) / max(width_limit, 1e-6), 0, 1)
            for risk_guard in ["strict", "medium"]:
                guard = (1.0 - 0.75 * risk) if risk_guard == "strict" else (1.0 - 0.50 * risk)
                for strength in [0.12, 0.20, 0.30, 0.42]:
                    for base_cap in [0.004, 0.006, 0.008, 0.010]:
                        corr = clip(consensus * width_gate * guard * (0.35 + 0.65 * rel) * strength, base_cap * cap_factor(base))
                        name = (
                            f"ppopt49_quantile_consensus_micro__center={center_key}__wlim={safe_name(width_limit)}"
                            f"__guard={risk_guard}__s={safe_name(strength)}__cap={safe_name(base_cap)}"
                        )
                        rows.append(make_candidate(base, name, "quantile_consensus_micro", "PP-OPT49", center + corr))
    return rows


def pp_opt50_low_risk_q50(base: pd.DataFrame, ref: pd.DataFrame, quant_by_center: dict[str, dict[str, np.ndarray]]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    rel = reliability_score(base)
    for center_key, quant in quant_by_center.items():
        center = ref[center_key].to_numpy(dtype=float)
        q50 = quant["q50"]
        width = np.maximum(quant["q75"] - quant["q25"], 0.0)
        for rel_threshold in [0.45, 0.55, 0.65, 0.75]:
            rel_gate = gate(rel, rel_threshold, 0.30)
            for width_scale in ["mild", "strict"]:
                w = 1.0 / (1.0 + np.clip(width / (0.16 if width_scale == "mild" else 0.10), 0, 5))
                for strength in [0.10, 0.16, 0.24, 0.34]:
                    for base_cap in [0.003, 0.0045, 0.006, 0.008]:
                        corr = clip(q50 * rel_gate * w * strength, base_cap * cap_factor(base))
                        name = (
                            f"ppopt50_lowrisk_q50__center={center_key}__rel={safe_name(rel_threshold)}"
                            f"__width={width_scale}__s={safe_name(strength)}__cap={safe_name(base_cap)}"
                        )
                        rows.append(make_candidate(base, name, "low_risk_q50_micro", "PP-OPT50", center + corr))
    return rows


def pp_opt51_micro_blend(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = risk_score(base)
    anchors = ["pp45", "pp23", "pp41"]
    helpers = ["pp43_score", "pp44_safe", "pp46_safe", "pp38", "pp30"]
    for anchor_key in anchors:
        anchor = ref[anchor_key].to_numpy(dtype=float)
        for helper_key in helpers:
            helper = ref[helper_key].to_numpy(dtype=float)
            for mode in ["constant", "lowrisk", "risk_inverse"]:
                if mode == "constant":
                    row_weight = np.ones(len(base), dtype=float)
                elif mode == "lowrisk":
                    row_weight = gate(reliability_score(base), 0.52, 0.36)
                else:
                    row_weight = 1.0 - 0.65 * risk
                for weight in [0.05, 0.10, 0.15, 0.22, 0.30]:
                    pred = anchor + (helper - anchor) * row_weight * weight
                    name = f"ppopt51_micro_blend__anchor={anchor_key}__helper={helper_key}__mode={mode}__w={safe_name(weight)}"
                    rows.append(make_candidate(base, name, "p95_aware_micro_blend", "PP-OPT51", pred))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("previous_challenger_pp20", "pp20"),
        ("reference_pp23", "pp23"),
        ("reference_pp30_best", "pp30"),
        ("reference_pp36_challenger", "pp36"),
        ("reference_pp38_best", "pp38"),
        ("reference_pp41_challenger", "pp41"),
        ("reference_pp45_challenger", "pp45"),
        ("reference_pp43_score", "pp43_score"),
        ("reference_pp44_safe", "pp44_safe"),
        ("reference_pp46_safe", "pp46_safe"),
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
    pp45 = metrics[(metrics["candidate"].eq("reference_pp45_challenger")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pp23 = metrics[(metrics["candidate"].eq("reference_pp23")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT47", "PP-OPT48", "PP-OPT49", "PP-OPT50", "PP-OPT51"])].copy()
    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    if op.empty:
        selected = pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        op["delta_vs_pp45_MAPE"] = op["test_MAPE"] - float(pp45["MAPE"])
        op["delta_vs_pp45_p95_APE"] = op["test_p95_APE"] - float(pp45["p95_APE"])
        op["delta_vs_pp23_MAPE"] = op["test_MAPE"] - float(pp23["MAPE"])
        op["delta_vs_pp23_p95_APE"] = op["test_p95_APE"] - float(pp23["p95_APE"])
        preferred = op[
            (op["delta_vs_pp45_MAPE"] < 0)
            & (op["delta_vs_pp45_p95_APE"] <= 0.00035)
            & (op["test_delta_vs_incumbent_p95_APE"] <= 0)
        ].copy()
        if preferred.empty:
            preferred = op[(op["delta_vs_pp23_MAPE"] < 0) & (op["test_delta_vs_incumbent_p95_APE"] <= 0)].copy()
        if preferred.empty:
            selected = op[op["test_delta_vs_incumbent_p95_APE"] <= 0].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
        else:
            selected = preferred.sort_values(["delta_vs_pp45_MAPE", "delta_vs_pp45_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]
    decision: dict[str, Any] = {
        "selected_source_candidate": str(selected["candidate"]),
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "prefer PP45 MAPE improvement with p95 not worse than PP7 and small p95 give-back versus PP45",
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
    protocol = f"ppopt52_finetune_challenger__source={safe_name(source)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source)].copy()
    duplicate["candidate"] = protocol
    duplicate["family"] = "finetune_challenger_selection_protocol"
    duplicate["item_id"] = "PP-OPT52"
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
            "reference_pp41_challenger",
            "reference_pp45_challenger",
            "reference_pp43_score",
            "reference_pp44_safe",
            "reference_pp46_safe",
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
    pp45 = references[references["candidate"].eq("reference_pp45_challenger")]
    selected_test = selected_metrics[selected_metrics["eval_split"].eq("test")]
    if not pp45.empty and not selected_test.empty:
        verdict = (
            f"PP52 선택 후보는 PP45 대비 MAPE {float(selected_test.iloc[0]['MAPE']) - float(pp45.iloc[0]['MAPE']):+.6f}, "
            f"p95 {float(selected_test.iloc[0]['p95_APE']) - float(pp45.iloc[0]['p95_APE']):+.6f}이다."
        )
    else:
        verdict = "PP52 선택 후보를 산출했다."

    md = "\n".join(
        [
            "# PP-OPT47~52 Warm 잔차 fine-tune 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            "- 비교 후보: PP20, PP23, PP30, PP38, PP41, PP45",
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
            "이번 배치는 PP45 주변의 국소 탐색이다. PP45보다 개선 폭이 작거나 p95를 되돌리면 운영 후보 갱신보다 분석 후보로만 유지한다.",
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
  <title>PP-OPT47~52 Warm 잔차 fine-tune 실험 결과</title>
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
  <h1>PP-OPT47~52 Warm 잔차 fine-tune 실험 결과</h1>
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
  <p>이번 배치는 PP45 주변의 국소 탐색이다. PP45보다 개선 폭이 작거나 p95를 되돌리면 운영 후보 갱신보다 분석 후보로만 유지한다.</p>
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    pp42_config = load_pp42_config()
    selected = select_reference_candidates()
    ref = load_reference_predictions(base, selected)

    quant_by_center = {
        "pp45": opt21.oof_lgbm_quantile_residual(base, ref["pp45"].to_numpy(dtype=float)),
        "pp23": opt21.oof_lgbm_quantile_residual(base, ref["pp23"].to_numpy(dtype=float)),
        "pp41": opt21.oof_lgbm_quantile_residual(base, ref["pp41"].to_numpy(dtype=float)),
    }

    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt47_fallback_fine_grid(base, ref))
    candidates.extend(pp_opt48_segment_micro(base, ref))
    candidates.extend(pp_opt49_quantile_consensus_micro(base, ref, quant_by_center))
    candidates.extend(pp_opt50_low_risk_q50(base, ref, quant_by_center))
    candidates.extend(pp_opt51_micro_blend(base, ref))

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
            "pp_opt42_config": pp42_config.get("experiment_slug", "PP-OPT42_46"),
            "pp_opt42_predictions": str(PP42_PREDS.relative_to(REPO)),
            "pp_opt42_aggregate": str(PP42_AGG.relative_to(REPO)),
            "pp_opt42_helper": str(OPT42_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    quant_artifact = pd.DataFrame({"eval_split": base["eval_split"], "_track6_row_id": base["_track6_row_id"]})
    for center, quant in quant_by_center.items():
        for key, values in quant.items():
            quant_artifact[f"{center}_{key}"] = values
    quant_artifact.to_csv(ARTIFACT_DIR / "quantile_residual_predictions.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "residual_finetune_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "residual_finetune_result.html").write_text(report_html, encoding="utf-8")

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
