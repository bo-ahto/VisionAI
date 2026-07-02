#!/usr/bin/env python3
"""Run PP-OPT103..110 Warm PP102 guard refinement experiments.

PP102 improved the fixed-test MAPE very slightly, but its validation
risk-focus bootstrap rows were weaker than the stable PP81/PP95 references.
This batch keeps the same non-submission Warm validation/test data and tests
whether the PP102 correction should be shrunk, rolled back, or gated on rows
where the learned gain probability is not strong enough.
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
PP96_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt96_102_warm_tail_label_refinement_experiments.py"
PP71_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt71_75_warm_pp70_stability_validation.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp96 = load_module("pp_opt96_helpers_for_pp103", PP96_SCRIPT)
val71 = load_module("pp_opt71_helpers_for_pp103", PP71_SCRIPT)
opt8 = pp96.opt8
opt29 = pp96.opt29

EXP_ID = "PP-OPT103-110"
EXP_SLUG = "PP-OPT103_110_warm_pp102_guard_refinement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP96_DIR = REPO / "experiments" / "track6" / "PP-OPT96_102_warm_tail_label_refinement_experiments"
PP96_PREDS = PP96_DIR / "outputs" / "candidate_predictions.csv"
PP96_CONFIG = PP96_DIR / "artifacts" / "run_config.json"
PP96_LABELS = PP96_DIR / "artifacts" / "tail_label_probability_detail.csv"

BASE_CANDIDATE = pp96.BASE_CANDIDATE
INCUMBENT = pp96.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT103",
        "priority": "1",
        "title": "PP102 risk-score shrink",
        "description": "기존 risk score가 높은 row에서 PP102 이동량을 PP81/PP95 안정 기준으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT104",
        "priority": "2",
        "title": "gain-harm margin gate",
        "description": "개선 확률이 손상 확률과 risk penalty를 충분히 이길 때만 PP102 보정을 허용한다.",
    },
    {
        "item_id": "PP-OPT105",
        "priority": "3",
        "title": "risk adaptive correction cap",
        "description": "PP102 보정 로그 이동량을 risk/quantile 폭에 따라 다른 cap으로 제한한다.",
    },
    {
        "item_id": "PP-OPT106",
        "priority": "4",
        "title": "stable-baseline gated adoption",
        "description": "PP81/PP95 안정 후보를 기준으로 두고 확률 margin이 충분한 row만 PP102로 이동한다.",
    },
    {
        "item_id": "PP-OPT107",
        "priority": "5",
        "title": "risk rollback router",
        "description": "risk가 높거나 harm 확률이 큰 row는 PP102에서 안정 후보로 rollback한다.",
    },
    {
        "item_id": "PP-OPT108",
        "priority": "6",
        "title": "tail-purpose hybrid router",
        "description": "운영형 PP102와 p95형 후보를 risk/gain 조건에 따라 제한적으로 섞는다.",
    },
    {
        "item_id": "PP-OPT109",
        "priority": "7",
        "title": "stability-score selected challenger",
        "description": "고정 test와 반복 안정성 점수를 함께 사용해 최종 후보를 고른다.",
    },
    {
        "item_id": "PP-OPT110",
        "priority": "8",
        "title": "final guarded PP102 decision",
        "description": "선택 후보를 운영형과 p95형으로 복제하고 PP64/PP70/PP81/PP95와 비교한다.",
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


def load_pp96_selected_predictions(base: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    selected = {
        "pp64": "reference_pp64_current_best",
        "pp70": "reference_pp70_refinement",
        "pp81": "reference_pp81_best",
        "pp82_op": "reference_pp82_operational",
        "pp82_p95": "reference_pp82_p95",
        "pp95_op": "reference_pp95_operational",
        "pp95_p95": "reference_pp95_p95",
        "pp102_op": config["selection_decision"]["operational_protocol_candidate"],
        "pp102_p95": config["selection_decision"]["p95_protocol_candidate"],
    }
    ref = pp96.load_predictions_from_file(base, PP96_PREDS, selected)
    return ref, selected


def load_label_detail(base: pd.DataFrame) -> pd.DataFrame:
    detail = pd.read_csv(PP96_LABELS)
    key = ["eval_split", "_track6_row_id"]
    merged = base[key].merge(detail, on=key, how="left")
    missing = merged.filter(regex=r"^prob_").isna().any(axis=1).sum()
    if missing:
        raise ValueError(f"Missing PP96 label probabilities for {missing} rows")
    return merged


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp95_p95", "pp95_p95"),
        ("reference_pp102_operational", "pp102_op"),
        ("reference_pp102_p95", "pp102_p95"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


def feature_scores(base: pd.DataFrame, detail: pd.DataFrame) -> dict[str, np.ndarray]:
    risk = val71.risk_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    gain_any = detail["prob_best_gain_any"].to_numpy(dtype=float)
    gain75 = detail["prob_best_gain_tail75"].to_numpy(dtype=float)
    gain80 = detail["prob_best_gain_tail80"].to_numpy(dtype=float)
    gain85 = detail["prob_best_gain_tail85"].to_numpy(dtype=float)
    harm = np.clip(
        0.55 * detail["prob_best_harm"].to_numpy(dtype=float)
        + 0.20 * detail["prob_pp20_harm"].to_numpy(dtype=float)
        + 0.15 * detail["prob_pp48_harm"].to_numpy(dtype=float)
        + 0.10 * detail["prob_p95_weighted_harm"].to_numpy(dtype=float),
        0.0,
        1.0,
    )
    uncertainty = np.clip(
        0.46 * risk
        + 0.20 * np.clip((qwidth - 1.10) / 1.05, 0, 1)
        + 0.16 * np.clip(spread / 0.20, 0, 1)
        + 0.10 * np.clip(gap / 0.07, 0, 1)
        + 0.08 * conf.eq("low_confidence").to_numpy(dtype=float),
        0.0,
        1.0,
    )
    tail_intent = np.clip(
        0.55 * gain80
        + 0.25 * gain85
        + 0.12 * price.eq("very_high_price").to_numpy(dtype=float)
        + 0.08 * np.clip((qwidth - 1.20) / 0.90, 0, 1),
        0.0,
        1.0,
    )
    return {
        "risk": risk,
        "qwidth": qwidth,
        "spread": spread,
        "gap": gap,
        "gain_any": gain_any,
        "gain75": gain75,
        "gain80": gain80,
        "gain85": gain85,
        "harm": harm,
        "uncertainty": uncertainty,
        "tail_intent": tail_intent,
    }


def pp_opt103_risk_shrink(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp102 = ref["pp102_op"].to_numpy(dtype=float)
    risk = scores["risk"]
    for safe_key in ["pp70", "pp81", "pp95_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for threshold in [0.42, 0.52, 0.62, 0.72]:
            for width in [0.16, 0.26, 0.38]:
                risk_gate = gate(risk, threshold, width)
                for shrink in [0.25, 0.45, 0.65, 0.85, 1.0]:
                    keep = np.clip(1.0 - shrink * risk_gate, 0.0, 1.0)
                    pred = safe + (pp102 - safe) * keep
                    name = (
                        f"ppopt103_risk_shrink__safe={safe_key}"
                        f"__thr={safe_name(threshold)}__width={safe_name(width)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(make_candidate(base, name, "pp102_risk_score_shrink", "PP-OPT103", pred))
    return rows


def pp_opt104_margin_gate(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    pp102 = ref["pp102_op"].to_numpy(dtype=float)
    for gain_key in ["gain_any", "gain75", "gain80"]:
        gain = scores[gain_key]
        for harm_penalty in [0.45, 0.65, 0.85, 1.05]:
            for risk_penalty in [0.00, 0.10, 0.18, 0.26]:
                margin = gain - harm_penalty * scores["harm"] - risk_penalty * scores["uncertainty"]
                for threshold in [0.00, 0.04, 0.08, 0.14]:
                    w = gate(margin, threshold, 0.24)
                    for strength in [0.35, 0.55, 0.75, 1.0]:
                        pred = anchor + (pp102 - anchor) * w * strength
                        name = (
                            f"ppopt104_margin_gate__gain={gain_key}__hpen={safe_name(harm_penalty)}"
                            f"__rpen={safe_name(risk_penalty)}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "gain_harm_margin_gate", "PP-OPT104", pred))
    return rows


def pp_opt105_adaptive_cap(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchor = ref["pp70"].to_numpy(dtype=float)
    delta = ref["pp102_op"].to_numpy(dtype=float) - anchor
    risk = scores["risk"]
    q_gate = gate(scores["qwidth"], 1.20, 0.95)
    for base_cap in [0.010, 0.016, 0.024, 0.034, 0.050]:
        for min_cap in [0.004, 0.008, 0.012]:
            for risk_shrink in [0.25, 0.45, 0.65, 0.85]:
                cap = np.maximum(min_cap, base_cap * (1.0 - risk_shrink * np.maximum(risk, q_gate)))
                pred = anchor + np.clip(delta, -cap, cap)
                name = (
                    f"ppopt105_adaptive_cap__basecap={safe_name(base_cap)}"
                    f"__mincap={safe_name(min_cap)}__rshrink={safe_name(risk_shrink)}"
                )
                rows.append(make_candidate(base, name, "risk_adaptive_correction_cap", "PP-OPT105", pred))
    return rows


def pp_opt106_stable_adoption(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp102 = ref["pp102_op"].to_numpy(dtype=float)
    for safe_key in ["pp81", "pp95_op", "pp70"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for gain_key in ["gain75", "gain80", "tail_intent"]:
            gain = scores[gain_key]
            for harm_penalty in [0.45, 0.70, 0.95]:
                for risk_penalty in [0.12, 0.22, 0.34]:
                    score = np.clip(gain * (1.0 - harm_penalty * scores["harm"]) * (1.0 - risk_penalty * scores["risk"]), 0, 1)
                    for threshold in [0.03, 0.07, 0.12, 0.20]:
                        w = gate(score, threshold, 0.24)
                        pred = safe + (pp102 - safe) * w
                        name = (
                            f"ppopt106_stable_adoption__safe={safe_key}__gain={gain_key}"
                            f"__hpen={safe_name(harm_penalty)}__rpen={safe_name(risk_penalty)}__thr={safe_name(threshold)}"
                        )
                        rows.append(make_candidate(base, name, "stable_baseline_gated_adoption", "PP-OPT106", pred))
    return rows


def pp_opt107_rollback_router(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp102 = ref["pp102_op"].to_numpy(dtype=float)
    for safe_key in ["pp70", "pp81", "pp95_op"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for risk_threshold in [0.44, 0.54, 0.64, 0.74]:
            risk_part = gate(scores["risk"], risk_threshold, 0.24)
            for harm_threshold in [0.02, 0.04, 0.07, 0.11]:
                harm_part = gate(scores["harm"], harm_threshold, 0.18)
                rollback_score = np.maximum(risk_part, harm_part)
                for rollback_strength in [0.25, 0.45, 0.65, 0.85, 1.0]:
                    pred = pp102 + (safe - pp102) * rollback_score * rollback_strength
                    name = (
                        f"ppopt107_rollback__safe={safe_key}__rthr={safe_name(risk_threshold)}"
                        f"__hthr={safe_name(harm_threshold)}__s={safe_name(rollback_strength)}"
                    )
                    rows.append(make_candidate(base, name, "risk_harm_rollback_router", "PP-OPT107", pred))
    return rows


def pp_opt108_tail_hybrid(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp81"].to_numpy(dtype=float)
    op = ref["pp102_op"].to_numpy(dtype=float)
    p95_targets = {
        "pp82_p95": ref["pp82_p95"].to_numpy(dtype=float),
        "pp95_p95": ref["pp95_p95"].to_numpy(dtype=float),
        "pp102_p95": ref["pp102_p95"].to_numpy(dtype=float),
    }
    op_margin = scores["gain75"] - 0.70 * scores["harm"] - 0.12 * scores["risk"]
    for target_key, target in p95_targets.items():
        for op_thr in [0.02, 0.06, 0.10, 0.16]:
            op_w = gate(op_margin, op_thr, 0.22)
            for tail_thr in [0.08, 0.14, 0.22, 0.32]:
                tail_w_raw = gate(scores["tail_intent"] - 0.55 * scores["harm"], tail_thr, 0.26)
                for tail_strength in [0.10, 0.18, 0.28, 0.40]:
                    tail_w = np.minimum(1.0 - op_w, tail_w_raw * tail_strength)
                    pred = safe + op_w * (op - safe) + tail_w * (target - safe)
                    name = (
                        f"ppopt108_tail_hybrid__target={target_key}"
                        f"__opthr={safe_name(op_thr)}__tailthr={safe_name(tail_thr)}__tails={safe_name(tail_strength)}"
                    )
                    rows.append(make_candidate(base, name, "tail_purpose_hybrid_router", "PP-OPT108", pred))
    return rows


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
    new_pool = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].copy()
    new_pool["delta_vs_pp64_MAPE"] = new_pool["test_MAPE"] - pp64_mape
    new_pool["delta_vs_pp64_p95_APE"] = new_pool["test_p95_APE"] - pp64_p95
    balanced = new_pool[
        (new_pool["delta_vs_pp64_MAPE"] <= 0.00002)
        & (new_pool["delta_vs_pp64_p95_APE"] <= 0.00005)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(18)
    best_mape = new_pool.sort_values(["test_MAPE", "test_p95_APE"]).head(18)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(18)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(18)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    references = [
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp82_operational",
        "reference_pp82_p95",
        "reference_pp95_operational",
        "reference_pp95_p95",
        "reference_pp102_operational",
        "reference_pp102_p95",
        INCUMBENT,
        BASE_CANDIDATE,
    ]
    return references + [candidate for candidate in selected if candidate not in references]


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT: "incumbent_pp7",
        "reference_pp64_current_best": "pp64_current_best",
        "reference_pp70_refinement": "pp70_refinement_candidate",
        "reference_pp81_best": "pp81_stable_reference",
        "reference_pp82_operational": "pp82_operational_reference",
        "reference_pp82_p95": "pp82_p95_reference",
        "reference_pp95_operational": "pp95_operational_reference",
        "reference_pp95_p95": "pp95_p95_reference",
        "reference_pp102_operational": "pp102_operational_reference",
        "reference_pp102_p95": "pp102_p95_reference",
    }
    subset = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    for candidate in selected_candidates:
        if candidate not in label_map:
            label_map[candidate] = f"candidate_{safe_name(candidate)[:120]}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp82_operational_reference",
        "pp82_p95_reference",
        "pp95_operational_reference",
        "pp95_p95_reference",
        "pp102_operational_reference",
        "pp102_p95_reference",
        "incumbent_pp7",
        "hcoef_stable_source",
    }
    pool = stability_aggregate[~stability_aggregate["candidate_label"].isin(refs)].copy()
    if pool.empty:
        raise ValueError("No new stability candidates available")
    pool["fixed_test_delta_vs_pp64_MAPE"] = pool["fixed_test_MAPE"] - float(pp64["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp64_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp64["fixed_test_p95_APE"])
    op_pool = pool[
        (pool["fixed_test_delta_vs_pp64_MAPE"] <= 0.00002)
        & (pool["fixed_test_delta_vs_pp64_p95_APE"] <= 0.00002)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.50)
    ].copy()
    if op_pool.empty:
        op_pool = pool.sort_values(["replacement_score", "fixed_test_MAPE"]).head(20).copy()
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00015)
        & (pool["fixed_test_p95_APE"] < float(pp64["fixed_test_p95_APE"]) - 0.00020)
    ].copy()
    if p95_pool.empty:
        p95_pool = pool[pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00030].copy()
    if p95_pool.empty:
        p95_pool = pool.copy()
    p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

    return {
        "operational_label": str(operational["candidate_label"]),
        "operational_candidate": str(operational["candidate"]),
        "operational_fixed_test_MAPE": float(operational["fixed_test_MAPE"]),
        "operational_fixed_test_p95_APE": float(operational["fixed_test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["fixed_test_delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["fixed_test_delta_vs_pp64_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def attach_candidate_names(stability_aggregate: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    lookup = fixed[["candidate_label", "candidate"]].drop_duplicates("candidate_label")
    if "candidate" in stability_aggregate.columns:
        return stability_aggregate
    return stability_aggregate.merge(lookup, on="candidate_label", how="left")


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "guarded_pp102_operational_selection"), ("p95", "guarded_pp102_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt110_{key}_guarded_pp102_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT110"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


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
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp102_operational",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected_names)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
    top_p95 = aggregate[
        (aggregate["item_id"].str.startswith("PP-OPT", na=False))
        & (aggregate["test_delta_vs_incumbent_MAPE"] < 0)
    ].sort_values(["test_p95_APE", "test_MAPE"])
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
    scenario_focus = stability_summary[
        stability_summary["candidate_label"].isin(
            [
                "pp81_stable_reference",
                "pp95_operational_reference",
                "pp102_operational_reference",
                decision["operational_label"],
                decision["p95_label"],
            ]
        )
    ]
    verdict = (
        f"운영 후보 {decision['operational_label']} fixed test MAPE "
        f"{decision['operational_fixed_test_MAPE']:.6f}, p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP64 대비 MAPE {decision['operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp64_p95_APE']:+.6f}."
    )
    interpretation = (
        "의미 있는 모델 특성 실험이다. PP102의 보정은 validation에서 배운 gain label을 쓰기 때문에 "
        "확률 margin이 약하거나 기존 risk score가 높은 row에서는 보정을 줄이는 것이 Huber/잔차 보정 계열의 "
        "보수적 특성과 맞는다. 다만 개선폭이 1e-5 수준이면 운영 교체는 안정성 지표까지 같이 봐야 한다."
    )

    md = "\n".join(
        [
            "# PP-OPT103~110 Warm PP102 guard refinement 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP102 보정값을 risk/gain/harm 조건에 맞춰 줄이거나 rollback하여 안정성을 개선",
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
            markdown_table(top_new, result_cols, 50),
            "",
            "## p95 후보 상위",
            markdown_table(top_p95, result_cols, 40),
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
  <title>PP-OPT103~110 Warm PP102 guard refinement 실험 결과</title>
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
  <h1>PP-OPT103~110 Warm PP102 guard refinement 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="warn">{html.escape(interpretation)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>안정성 검증 후보</strong>{stability_aggregate['candidate_label'].nunique()}개</div>
    <div class="panel"><strong>운영형 PP64 대비 MAPE</strong>{decision['operational_delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{decision['operational_delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 주요 후보 test 비교</h2>
  {table_html(selected_test, list(selected_test.columns), 30)}
  <h2>2. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 30)}
  <h2>3. 탐색 후보 상위</h2>
  {table_html(top_new, result_cols, 50)}
  <h2>4. p95 후보 상위</h2>
  {table_html(top_p95, result_cols, 40)}
  <h2>5. 선택 후보 반복 안정성</h2>
  {table_html(stability_aggregate, stab_cols, 80)}
  <h2>6. 선택 후보 시나리오별 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 80)}
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    parent_config = load_json(PP96_CONFIG)
    base, source, _, _, _, _ = pp96.load_inputs()
    ref, selected_refs = load_pp96_selected_predictions(base, parent_config)
    label_detail = load_label_detail(base)
    scores = feature_scores(base, label_detail)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt103_risk_shrink(base, ref, scores))
    candidates.extend(pp_opt104_margin_gate(base, ref, scores))
    candidates.extend(pp_opt105_adaptive_cap(base, ref, scores))
    candidates.extend(pp_opt106_stable_adoption(base, ref, scores))
    candidates.extend(pp_opt107_rollback_router(base, ref, scores))
    candidates.extend(pp_opt108_tail_hybrid(base, ref, scores))

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
    stability_aggregate = val71.aggregate_summary(stability_summary, fixed)
    stability_aggregate = attach_candidate_names(stability_aggregate, fixed)
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
    label_map[decision["operational_protocol_candidate"]] = "pp110_operational_guarded_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp110_p95_guarded_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = val71.aggregate_summary(stability_summary, fixed)
    stability_aggregate = attach_candidate_names(stability_aggregate, fixed)

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
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp96_config": str(PP96_CONFIG.relative_to(REPO)),
            "pp96_predictions": str(PP96_PREDS.relative_to(REPO)),
            "pp96_label_probabilities": str(PP96_LABELS.relative_to(REPO)),
            "pp96_helper": str(PP96_SCRIPT.relative_to(REPO)),
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
    score_detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in scores.items():
        score_detail[key] = value
    score_detail.to_csv(ARTIFACT_DIR / "guard_score_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "pp102_guard_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp102_guard_refinement_result.html").write_text(report_html, encoding="utf-8")

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
