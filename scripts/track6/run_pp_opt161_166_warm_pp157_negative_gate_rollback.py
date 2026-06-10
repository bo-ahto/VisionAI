#!/usr/bin/env python3
"""Run PP-OPT161..166 Warm PP157 negative-gate rollback experiments."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP155_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt155_160_warm_strict_huber_gate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp155 = load_module("pp_opt155_helpers_for_pp161", PP155_SCRIPT)
pp149 = pp155.pp149
pp143 = pp155.pp143
pp135 = pp155.pp135
pp127 = pp155.pp127
pp139 = pp155.pp139
opt8 = pp155.opt8
val71 = pp155.val71

EXP_ID = "PP-OPT161-166"
EXP_SLUG = "PP-OPT161_166_warm_pp157_negative_gate_rollback"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = pp135.BASE_CANDIDATE
INCUMBENT = pp135.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS = [
    {
        "item_id": "PP-OPT161",
        "priority": "1",
        "title": "PP157 harm-probability rollback",
        "description": "PP157이 PP148보다 나빠질 확률이 높은 row를 PP148 쪽으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT162",
        "priority": "2",
        "title": "PP157 gain-harm gated adoption",
        "description": "PP157 gain 확률과 harm 확률을 동시에 써서 PP148에서 PP157로 이동할 row만 선택한다.",
    },
    {
        "item_id": "PP-OPT163",
        "priority": "3",
        "title": "segment outcome rollback",
        "description": "validation에서 PP157 손해율이 높은 가격대/불확실성 구간은 PP157 적용을 제한한다.",
    },
    {
        "item_id": "PP-OPT164",
        "priority": "4",
        "title": "hard negative classifier block",
        "description": "negative classifier가 위험하다고 본 row는 PP157 이동을 완전히 차단한다.",
    },
    {
        "item_id": "PP-OPT165",
        "priority": "5",
        "title": "PP148 and negative-gated PP157 ensemble",
        "description": "PP148의 안정성을 유지하면서 PP157의 MAPE 개선분만 작은 비율로 섞는다.",
    },
    {
        "item_id": "PP-OPT166",
        "priority": "6",
        "title": "final PP157 negative-gate decision",
        "description": "PP148/PP157 negative-gate 후보를 fixed/repeated 기준으로 비교한다.",
    },
]

PP157_CONFIGS = [
    {"name": "price_qwidth_q084_s100_cap008", "seg": "price_qwidth", "cols": ["stable_price_band_code", "qwidth_band"], "q": 0.84, "strength": 1.00, "cap": 0.0080},
    {"name": "price_qwidth_q084_s100_cap0065", "seg": "price_qwidth", "cols": ["stable_price_band_code", "qwidth_band"], "q": 0.84, "strength": 1.00, "cap": 0.0065},
    {"name": "price_qwidth_q084_s090_cap005", "seg": "price_qwidth", "cols": ["stable_price_band_code", "qwidth_band"], "q": 0.84, "strength": 0.90, "cap": 0.0050},
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp135.safe_name(value)


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    actual = base["actual_price"].to_numpy(dtype=float)
    return np.abs(safe_exp(pred_log) - actual) / np.maximum(actual, EPS)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp135.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp135.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp135.make_candidate(base, candidate, family, item_id, pred_log)


def build_pp157_targets(base: pd.DataFrame, ref: pd.DataFrame, strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    delta = targets["direct_lgb_huber_s0p18_cap0p01"] - safe
    out: dict[str, np.ndarray] = {}
    detail = base[["eval_split", "_track6_row_id"]].copy()
    detail["pp126_op"] = safe
    for cfg in PP157_CONFIGS:
        keep = pp155.segment_keep(base, strict["strict_huber_score"], cfg["q"], cfg["cols"])
        cap_arr = np.maximum(0.0018, cfg["cap"] * (1.0 - 0.40 * strict["width_risk"]))
        pred = safe + clip_by_row(delta * keep * cfg["strength"], cap_arr)
        key = f"pp157_{cfg['name']}"
        out[key] = pred
        detail[key] = pred
        detail[f"{key}_keep"] = keep
        detail[f"{key}_delta_from_pp126"] = pred - safe
    return out, detail


def build_negative_gate_signals(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    strict: dict[str, np.ndarray],
    pp157_targets: dict[str, np.ndarray],
    feature_matrix: pd.DataFrame,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    pp148 = strict["pp148_operational"]
    primary = pp157_targets["pp157_price_qwidth_q084_s100_cap008"]
    ape_pp148 = ape_from_log(base, pp148)
    ape_primary = ape_from_log(base, primary)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    q75 = float(np.quantile(ape_pp148[val_mask], 0.75))
    q85 = float(np.quantile(ape_pp148[val_mask], 0.85))
    q90 = float(np.quantile(ape_pp148[val_mask], 0.90))
    labels = {
        "pp157_gain_vs_pp148": (ape_primary + 0.0008 < ape_pp148).astype(int),
        "pp157_stable_gain_vs_pp148": ((ape_primary + 0.0008 < ape_pp148) & (ape_primary <= np.maximum(ape_pp148, q85))).astype(int),
        "pp157_harm_vs_pp148": (ape_primary > ape_pp148 + 0.0008).astype(int),
        "pp157_large_harm_vs_pp148": ((ape_primary > ape_pp148 + 0.0015) | ((ape_pp148 >= q85) & (ape_primary > ape_pp148 + 0.0005))).astype(int),
        "pp157_tail_harm_vs_pp148": ((ape_pp148 >= q75) & (ape_primary > ape_pp148 + 0.0004)).astype(int),
    }
    learned: dict[str, np.ndarray] = {}
    for i, (name, label) in enumerate(labels.items(), start=1):
        learned[f"prob_{name}"] = pp127.oof_lgbm_probability(base, feature_matrix, label, seed_offset=2100 + 20 * i)
    harm_mix = np.clip(
        0.45 * learned["prob_pp157_harm_vs_pp148"]
        + 0.35 * learned["prob_pp157_large_harm_vs_pp148"]
        + 0.20 * learned["prob_pp157_tail_harm_vs_pp148"],
        0,
        1,
    )
    gain_mix = np.clip(
        0.60 * learned["prob_pp157_stable_gain_vs_pp148"]
        + 0.25 * learned["prob_pp157_gain_vs_pp148"]
        + 0.15 * strict["direction_agree"],
        0,
        1,
    )
    learned.update(
        {
            "pp148_operational": pp148,
            "pp157_primary": primary,
            "ape_pp148_validation_q75": np.full(len(base), q75),
            "ape_pp148_validation_q85": np.full(len(base), q85),
            "ape_pp148_validation_q90": np.full(len(base), q90),
            "pp157_harm_mix": harm_mix,
            "pp157_gain_mix": gain_mix,
            "pp157_net_score": np.clip(gain_mix * (1.0 - 0.70 * harm_mix), 0, 1),
        }
    )
    detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in learned.items():
        detail[key] = value
    for key, value in labels.items():
        detail[f"label_{key}"] = value
    return learned, detail


def segment_outcome_score(base: pd.DataFrame, pp148: np.ndarray, pp157: np.ndarray, segment_cols: list[str], harm_weight: float) -> np.ndarray:
    ape148 = ape_from_log(base, pp148)
    ape157 = ape_from_log(base, pp157)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    gain = (ape157 + 0.0008 < ape148).astype(float)
    harm = (ape157 > ape148 + 0.0008).astype(float)
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_score = float(np.mean(gain[val_mask]) - harm_weight * np.mean(harm[val_mask]))
    scores: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() >= 12:
            scores[key] = float(np.mean(gain[idx]) - harm_weight * np.mean(harm[idx]))
    return seg.map(scores).fillna(global_score).to_numpy(dtype=float)


def pp_opt161_harm_probability_rollback(base: pd.DataFrame, negative: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = negative["pp148_operational"]
    harm = negative["pp157_harm_mix"]
    for target_name, pp157 in pp157_targets.items():
        delta = pp157 - pp148
        for harm_threshold in [0.30, 0.40]:
            for width in [0.14]:
                rollback_w = gate(harm, harm_threshold, width)
                for rollback in [0.55, 0.75, 1.00]:
                    keep = np.clip(1.0 - rollback * rollback_w, 0, 1)
                    for strength in [0.85, 1.00]:
                        for cap in [0.006, 0.008]:
                            pred = pp148 + clip_by_row(delta * keep * strength, np.full(len(base), cap))
                            name = (
                                f"ppopt161_harm_rollback__target={target_name}__hthr={safe_name(harm_threshold)}"
                                f"__w={safe_name(width)}__rb={safe_name(rollback)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "pp157_harm_probability_rollback", "PP-OPT161", pred))
    return rows


def pp_opt162_gain_harm_adoption(base: pd.DataFrame, negative: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = negative["pp148_operational"]
    score = negative["pp157_net_score"]
    for target_name, pp157 in pp157_targets.items():
        delta = pp157 - pp148
        for threshold in [0.18, 0.24, 0.30]:
            for width in [0.10]:
                base_w = gate(score, threshold, width)
                for harm_penalty in [0.50, 0.75]:
                    weight = np.clip(base_w * (1.0 - harm_penalty * negative["pp157_harm_mix"]), 0, 1)
                    for strength in [0.85, 1.00]:
                        for cap in [0.006, 0.008]:
                            pred = pp148 + clip_by_row(delta * weight * strength, np.full(len(base), cap))
                            name = (
                                f"ppopt162_gain_harm_adopt__target={target_name}__thr={safe_name(threshold)}"
                                f"__w={safe_name(width)}__hpen={safe_name(harm_penalty)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "pp157_gain_harm_gated_adoption", "PP-OPT162", pred))
    return rows


def pp_opt163_segment_outcome_rollback(base: pd.DataFrame, negative: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = negative["pp148_operational"]
    segment_sets = {
        "price_qwidth": ["stable_price_band_code", "qwidth_band"],
        "price_conf": ["stable_price_band_code", "confidence_tier"],
    }
    for target_name, pp157 in pp157_targets.items():
        delta = pp157 - pp148
        for seg_name, cols in segment_sets.items():
            for harm_weight in [1.20, 1.60]:
                seg_score = segment_outcome_score(base, pp148, pp157, cols, harm_weight)
                for score_threshold in [0.00, 0.08]:
                    keep = (seg_score >= score_threshold).astype(float)
                    for strength in [0.85, 1.00]:
                        for cap in [0.006, 0.008]:
                            pred = pp148 + clip_by_row(delta * keep * strength, np.full(len(base), cap))
                            name = (
                                f"ppopt163_segment_outcome__target={target_name}__seg={seg_name}__hw={safe_name(harm_weight)}"
                                f"__thr={safe_name(score_threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "segment_outcome_pp157_rollback", "PP-OPT163", pred))
    return rows


def pp_opt164_hard_negative_block(base: pd.DataFrame, negative: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = negative["pp148_operational"]
    for target_name, pp157 in pp157_targets.items():
        delta = pp157 - pp148
        for harm_threshold in [0.35, 0.45]:
            harm_keep = (negative["pp157_harm_mix"] <= harm_threshold).astype(float)
            for gain_threshold in [0.12, 0.20]:
                gain_keep = (negative["pp157_gain_mix"] >= gain_threshold).astype(float)
                keep = harm_keep * gain_keep
                for strength in [0.85, 1.00]:
                    for cap in [0.006, 0.008]:
                        pred = pp148 + clip_by_row(delta * keep * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt164_hard_block__target={target_name}__hthr={safe_name(harm_threshold)}"
                            f"__gthr={safe_name(gain_threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "hard_negative_classifier_block", "PP-OPT164", pred))
    return rows


def pp_opt165_pp148_pp157_ensemble(base: pd.DataFrame, negative: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = negative["pp148_operational"]
    score = negative["pp157_net_score"]
    for target_name, pp157 in pp157_targets.items():
        delta = pp157 - pp148
        for threshold in [0.18, 0.24]:
            adopt_w = gate(score, threshold, 0.12)
            for pp157_strength in [0.35, 0.50]:
                for harm_penalty in [0.55, 0.80]:
                    weight = np.clip(adopt_w * pp157_strength * (1.0 - harm_penalty * negative["pp157_harm_mix"]), 0, 1)
                    for cap in [0.005, 0.007]:
                        pred = pp148 + clip_by_row(delta * weight, np.full(len(base), cap))
                        name = (
                            f"ppopt165_pp148_pp157_ensemble__target={target_name}__thr={safe_name(threshold)}"
                            f"__p157={safe_name(pp157_strength)}__hpen={safe_name(harm_penalty)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp148_negative_gated_pp157_ensemble", "PP-OPT165", pred))
    return rows


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray], pp157_targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows = pp149.reference_candidates(base, ref, router, targets)
    for key in ["pp157_price_qwidth_q084_s100_cap008", "pp157_price_qwidth_q084_s100_cap0065"]:
        rows.append(make_candidate(base, f"reference_{key}", "reference_prior", "REFERENCE", pp157_targets[key]))
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
    pp126_p95 = float(test[test["candidate"].eq("reference_pp126_operational")]["p95_APE"].iloc[0])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    balanced = new_pool[
        (new_pool["test_p95_APE"] <= pp126_p95 + 0.00008)
        & (new_pool["incumbent_MAPE_improve_rate"] >= 0.76)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(40)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp126_p95 + 0.00045].sort_values(["test_MAPE", "test_p95_APE"]).head(40)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(40)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(40)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
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
        "reference_pp148_operational",
        "reference_pp148_p95",
        "reference_pp157_price_qwidth_q084_s100_cap008",
        "reference_pp157_price_qwidth_q084_s100_cap0065",
    ]
    return references + [candidate for candidate in selected if candidate not in references]


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp149.label_for_stability(predictions, selected_candidates)
    label_map.update(
        {
            "reference_pp157_price_qwidth_q084_s100_cap008": "pp157_price_qwidth_q084_s100_cap008_reference",
            "reference_pp157_price_qwidth_q084_s100_cap0065": "pp157_price_qwidth_q084_s100_cap0065_reference",
        }
    )
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    return pp149.select_protocol_candidates(stability_aggregate)


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "pp157_negative_gate_operational_selection"), ("p95", "pp157_negative_gate_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt166_{key}_pp157_negative_gate_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT166"
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
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability_aggregate: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        "reference_pp64_current_best",
        "reference_pp126_operational",
        "reference_pp148_operational",
        "reference_pp157_price_qwidth_q084_s100_cap008",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"운영 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP126 대비 MAPE {decision['operational_delta_vs_pp126_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp126_p95_APE']:+.6f}. "
        f"PP148 대비 MAPE {decision['operational_delta_vs_pp148_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp148_p95_APE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT161~166 Warm PP157 negative-gate rollback 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP157의 MAPE 개선 신호를 유지하면서 PP148 대비 손해 row를 rollback",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 30),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 80),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 100),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT161~166 Warm PP157 negative-gate rollback 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT161~166 Warm PP157 negative-gate rollback 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 30)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 30)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 80)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 100)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, labels, model_detail, selected_refs, parent_config, selected_pp119 = pp135.load_inputs()
    scores = pp135.build_scores(base, ref, labels, model_detail)
    feature_matrix = pp127.build_feature_matrix(base, ref, labels, model_detail, scores)
    prior_signals, prior_signal_detail = pp127.build_learned_signals(base, ref, model_detail, feature_matrix)
    signals, signal_detail = pp135.build_p95_aware_signals(base, ref, model_detail, feature_matrix, prior_signals)
    ref, ref_notes = pp135.add_reference_predictions(base, ref, model_detail, scores, signals)
    meta, meta_detail = pp139.build_meta_predictions(base, feature_matrix)
    targets, target_detail = pp143.build_direct_targets(base, ref, meta, scores)
    router, router_detail = pp143.build_router_scores(base, ref, meta, scores, signals, targets, feature_matrix)
    strict, strict_detail = pp155.build_strict_huber_scores(base, ref, meta, router, targets, feature_matrix)
    pp157_targets, pp157_detail = build_pp157_targets(base, ref, strict, targets)
    negative, negative_detail = build_negative_gate_signals(base, ref, strict, pp157_targets, feature_matrix)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt161_harm_probability_rollback(base, negative, pp157_targets))
    candidates.extend(pp_opt162_gain_harm_adoption(base, negative, pp157_targets))
    candidates.extend(pp_opt163_segment_outcome_rollback(base, negative, pp157_targets))
    candidates.extend(pp_opt164_hard_negative_block(base, negative, pp157_targets))
    candidates.extend(pp_opt165_pp148_pp157_ensemble(base, negative, pp157_targets))

    predictions = pd.concat([source] + reference_candidates(base, ref, router, targets, pp157_targets) + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_candidates_for_stability(metrics, aggregate)
    stability_predictions, label_map = label_for_stability(predictions, selected)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = select_protocol_candidates(stability_aggregate)
    predictions, decision = add_protocol_rows(predictions, decision)

    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_candidates_for_stability(metrics, aggregate)
    selected.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected)
    label_map[decision["operational_protocol_candidate"]] = "pp166_operational_pp157_negative_gate_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp166_p95_pp157_negative_gate_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

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
        "pp157_configs": PP157_CONFIGS,
        "selected_references": selected_refs,
        "selected_pp119_sources": selected_pp119,
        "recomputed_reference_notes": ref_notes,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {"pp155_helper": str(PP155_SCRIPT.relative_to(REPO))},
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
    prior_signal_detail.to_csv(ARTIFACT_DIR / "prior_learned_signal_detail.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "p95_aware_signal_detail.csv", index=False)
    meta_detail.to_csv(ARTIFACT_DIR / "direct_meta_prediction_detail.csv", index=False)
    target_detail.to_csv(ARTIFACT_DIR / "direct_target_prediction_detail.csv", index=False)
    router_detail.to_csv(ARTIFACT_DIR / "row_level_router_signal_detail.csv", index=False)
    strict_detail.to_csv(ARTIFACT_DIR / "strict_huber_gate_signal_detail.csv", index=False)
    pp157_detail.to_csv(ARTIFACT_DIR / "pp157_target_prediction_detail.csv", index=False)
    negative_detail.to_csv(ARTIFACT_DIR / "pp157_negative_gate_signal_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "pp157_negative_gate_rollback_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp157_negative_gate_rollback_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family"]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability_aggregate[
            ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
