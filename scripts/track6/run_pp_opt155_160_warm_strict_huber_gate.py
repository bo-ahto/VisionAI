#!/usr/bin/env python3
"""Run PP-OPT155..160 Warm strict Huber gate experiments."""
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
PP149_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt149_154_warm_huber_adoption_stabilization.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp149 = load_module("pp_opt149_helpers_for_pp155", PP149_SCRIPT)
pp143 = pp149.pp143
pp135 = pp149.pp135
pp127 = pp149.pp127
pp139 = pp149.pp139
opt8 = pp149.opt8
val71 = pp149.val71

EXP_ID = "PP-OPT155-160"
EXP_SLUG = "PP-OPT155_160_warm_strict_huber_gate"
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
        "item_id": "PP-OPT155",
        "priority": "1",
        "title": "strict stable-gain Huber gate",
        "description": "Huber 후보가 안정적으로 이길 확률이 높은 row만 작은 cap으로 보정한다.",
    },
    {
        "item_id": "PP-OPT156",
        "priority": "2",
        "title": "PP148 plus strict Huber micro-gate",
        "description": "PP148 운영 후보 위에 stable-gain 확률이 높은 row만 미세 Huber 보정을 더한다.",
    },
    {
        "item_id": "PP-OPT157",
        "priority": "3",
        "title": "segment quantile strict Huber gate",
        "description": "가격대/신뢰도 구간별 validation score 상위 row에만 Huber 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT158",
        "priority": "4",
        "title": "tail-safe strict Huber gate",
        "description": "p95 위험 방어를 우선해 tail harm, quantile width가 높은 row의 Huber 이동량을 줄인다.",
    },
    {
        "item_id": "PP-OPT159",
        "priority": "5",
        "title": "PP148 and strict Huber ensemble",
        "description": "PP148의 안정성과 strict Huber의 MAPE 개선 신호를 작은 비율로 결합한다.",
    },
    {
        "item_id": "PP-OPT160",
        "priority": "6",
        "title": "final strict Huber gate decision",
        "description": "PP126/PP148와 strict Huber 후보를 fixed/repeated 기준으로 비교한다.",
    },
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


def build_strict_huber_scores(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    router: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
    feature_matrix: pd.DataFrame,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    pp148 = pp149.pp148_reference_predictions(ref, router, targets)["pp148_operational"]
    huber = targets["direct_lgb_huber_s0p18_cap0p01"]
    l2 = targets["direct_lgb_l2_s0p18_cap0p01"]
    ape_safe = ape_from_log(base, safe)
    ape_pp148 = ape_from_log(base, pp148)
    ape_huber = ape_from_log(base, huber)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    q75 = float(np.quantile(ape_safe[val_mask], 0.75))
    q85 = float(np.quantile(ape_safe[val_mask], 0.85))
    q90 = float(np.quantile(ape_safe[val_mask], 0.90))
    meta_width = np.abs(meta["lgb_q75"] - meta["lgb_q25"])

    labels = {
        "huber_gain": (ape_huber + 0.0010 < ape_safe).astype(int),
        "huber_stable_gain": ((ape_huber + 0.0010 < ape_safe) & (ape_huber <= np.maximum(ape_safe, q85))).astype(int),
        "huber_pp148_gain": (ape_huber + 0.0008 < ape_pp148).astype(int),
        "huber_tail_safe_gain": ((ape_safe >= q75) & (ape_huber + 0.0005 < ape_safe) & (ape_huber <= q90)).astype(int),
        "huber_large_harm": ((ape_huber > ape_safe + 0.0010) | ((ape_safe >= q85) & (ape_huber > ape_safe + 0.0003))).astype(int),
        "huber_pp148_harm": (ape_huber > ape_pp148 + 0.0010).astype(int),
    }
    learned: dict[str, np.ndarray] = {}
    for i, (name, label) in enumerate(labels.items(), start=1):
        learned[f"prob_{name}"] = pp127.oof_lgbm_probability(base, feature_matrix, label, seed_offset=1700 + 20 * i)

    direction_agree = (
        (np.sign(huber - safe) == np.sign(l2 - safe)).astype(float)
        + (np.sign(huber - safe) == np.sign(meta["lgb_q50"] - safe)).astype(float)
        + (np.sign(huber - safe) == np.sign(ref["pp126_p95"].to_numpy(dtype=float) - safe)).astype(float)
    ) / 3.0
    width_risk = gate(meta_width, 0.040, 0.080)
    base_score = np.clip(
        0.45 * learned["prob_huber_stable_gain"]
        + 0.25 * learned["prob_huber_pp148_gain"]
        + 0.20 * learned["prob_huber_tail_safe_gain"]
        + 0.10 * direction_agree,
        0,
        1,
    )
    strict_score = np.clip(
        base_score
        * (1.0 - 0.70 * learned["prob_huber_large_harm"])
        * (1.0 - 0.45 * learned["prob_huber_pp148_harm"])
        * (1.0 - 0.35 * width_risk),
        0,
        1,
    )

    learned.update(
        {
            "pp148_operational": pp148,
            "meta_width": meta_width,
            "width_risk": width_risk,
            "direction_agree": direction_agree,
            "strict_huber_score": strict_score,
            "huber_delta_abs": np.abs(huber - safe),
            "safe_ape_validation_q75": np.full(len(base), q75),
            "safe_ape_validation_q85": np.full(len(base), q85),
            "safe_ape_validation_q90": np.full(len(base), q90),
        }
    )

    detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in learned.items():
        detail[key] = value
    for key, value in labels.items():
        detail[f"label_{key}"] = value
    return learned, detail


def segment_keep(base: pd.DataFrame, score: np.ndarray, quantile: float, segment_cols: list[str]) -> np.ndarray:
    val_mask = base["eval_split"].eq("validation_oof")
    global_thr = float(np.quantile(score[val_mask.to_numpy()], quantile))
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    thresholds: dict[str, float] = {}
    for key in seg[val_mask].drop_duplicates():
        idx = val_mask.to_numpy() & seg.eq(key).to_numpy()
        if idx.sum() >= 12:
            thresholds[key] = float(np.quantile(score[idx], quantile))
    row_thr = seg.map(thresholds).fillna(global_thr).to_numpy(dtype=float)
    return (score >= row_thr).astype(float)


def pp_opt155_strict_stable_gain(base: pd.DataFrame, ref: pd.DataFrame, strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    delta = targets["direct_lgb_huber_s0p18_cap0p01"] - safe
    score = strict["strict_huber_score"]
    for threshold in [0.26, 0.30, 0.34, 0.38, 0.42]:
        for width in [0.05, 0.08, 0.12]:
            base_w = gate(score, threshold, width)
            for direction_min in [0.00, 0.34, 0.67]:
                direction_keep = (strict["direction_agree"] >= direction_min).astype(float)
                for strength in [0.50, 0.70, 0.90, 1.00]:
                    for cap in [0.0030, 0.0045, 0.0060, 0.0075]:
                        cap_arr = np.maximum(0.0016, cap * (1.0 - 0.45 * strict["prob_huber_large_harm"]))
                        pred = safe + clip_by_row(delta * base_w * direction_keep * strength, cap_arr)
                        name = (
                            f"ppopt155_strict_huber__thr={safe_name(threshold)}__w={safe_name(width)}"
                            f"__dmin={safe_name(direction_min)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "strict_stable_gain_huber_gate", "PP-OPT155", pred))
    return rows


def pp_opt156_pp148_micro_gate(base: pd.DataFrame, strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    pp148 = strict["pp148_operational"]
    delta = targets["direct_lgb_huber_s0p18_cap0p01"] - pp148
    score = strict["strict_huber_score"]
    for threshold in [0.28, 0.32, 0.36, 0.40, 0.44]:
        for width in [0.05, 0.08, 0.12]:
            base_w = gate(score, threshold, width)
            for strength in [0.15, 0.25, 0.35, 0.50]:
                for cap in [0.0015, 0.0025, 0.0035, 0.0050]:
                    cap_arr = np.maximum(0.0010, cap * (1.0 - 0.55 * strict["prob_huber_pp148_harm"]))
                    pred = pp148 + clip_by_row(delta * base_w * strength, cap_arr)
                    name = (
                        f"ppopt156_pp148_strict_micro__thr={safe_name(threshold)}__w={safe_name(width)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "pp148_plus_strict_huber_micro_gate", "PP-OPT156", pred))
    return rows


def pp_opt157_segment_quantile_gate(base: pd.DataFrame, ref: pd.DataFrame, strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    delta = targets["direct_lgb_huber_s0p18_cap0p01"] - safe
    score = strict["strict_huber_score"]
    segment_sets = {
        "price_conf": ["stable_price_band_code", "confidence_tier"],
        "price_qwidth": ["stable_price_band_code", "qwidth_band"],
        "conf_qwidth": ["confidence_tier", "qwidth_band"],
    }
    for seg_name, cols in segment_sets.items():
        for quantile in [0.70, 0.78, 0.84, 0.90]:
            keep = segment_keep(base, score, quantile, cols)
            for strength in [0.50, 0.70, 0.90, 1.00]:
                for cap in [0.0035, 0.0050, 0.0065, 0.0080]:
                    cap_arr = np.maximum(0.0018, cap * (1.0 - 0.40 * strict["width_risk"]))
                    pred = safe + clip_by_row(delta * keep * strength, cap_arr)
                    name = (
                        f"ppopt157_segment_quantile__seg={seg_name}__q={safe_name(quantile)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "segment_quantile_strict_huber_gate", "PP-OPT157", pred))
    return rows


def pp_opt158_tail_safe_gate(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    delta = targets["direct_lgb_huber_s0p18_cap0p01"] - safe
    tail_safe_score = np.clip(
        strict["strict_huber_score"]
        * (0.55 + 0.45 * strict["prob_huber_tail_safe_gain"])
        * (1.0 - 0.55 * router["tail_harm"])
        * (1.0 - 0.35 * strict["width_risk"]),
        0,
        1,
    )
    for threshold in [0.22, 0.28, 0.34, 0.40]:
        for width in [0.06, 0.10, 0.16]:
            base_w = gate(tail_safe_score, threshold, width)
            for strength in [0.45, 0.65, 0.85, 1.00]:
                for cap in [0.0035, 0.0050, 0.0065, 0.0080]:
                    cap_arr = np.maximum(0.0018, cap * (1.0 - 0.50 * router["tail_harm"]) * (1.0 - 0.35 * strict["width_risk"]))
                    pred = safe + clip_by_row(delta * base_w * strength, cap_arr)
                    name = (
                        f"ppopt158_tail_safe_huber__thr={safe_name(threshold)}__w={safe_name(width)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "tail_safe_strict_huber_gate", "PP-OPT158", pred))
    return rows


def pp_opt159_pp148_strict_ensemble(base: pd.DataFrame, ref: pd.DataFrame, strict: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    pp148 = strict["pp148_operational"]
    huber_delta = targets["direct_lgb_huber_s0p18_cap0p01"] - safe
    score = strict["strict_huber_score"]
    for threshold in [0.28, 0.32, 0.36, 0.40]:
        for width in [0.06, 0.10, 0.14]:
            huber_w = gate(score, threshold, width)
            for pp148_strength in [0.70, 0.85, 1.00]:
                for huber_strength in [0.15, 0.25, 0.35, 0.50]:
                    corr = (pp148 - safe) * pp148_strength + huber_delta * huber_w * huber_strength
                    for cap in [0.0050, 0.0070, 0.0090, 0.0110]:
                        cap_arr = np.maximum(0.0018, cap * (1.0 - 0.35 * strict["prob_huber_large_harm"]))
                        pred = safe + clip_by_row(corr, cap_arr)
                        name = (
                            f"ppopt159_pp148_strict_ensemble__thr={safe_name(threshold)}__w={safe_name(width)}"
                            f"__p148={safe_name(pp148_strength)}__hs={safe_name(huber_strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp148_strict_huber_ensemble", "PP-OPT159", pred))
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
        & (new_pool["incumbent_MAPE_improve_rate"] >= 0.74)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(36)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp126_p95 + 0.00045].sort_values(["test_MAPE", "test_p95_APE"]).head(36)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(36)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(36)
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
    ]
    return references + [candidate for candidate in selected if candidate not in references]


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp149.label_for_stability(predictions, selected_candidates)
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
    for key, family in [("operational", "strict_huber_gate_operational_selection"), ("p95", "strict_huber_gate_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt160_{key}_strict_huber_gate_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT160"
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
        "reference_pp148_p95",
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
            "# PP-OPT155~160 Warm strict Huber gate 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP149의 낮은 MAPE 신호를 더 엄격한 적용 gate로 안정화",
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
<title>PP-OPT155~160 Warm strict Huber gate 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT155~160 Warm strict Huber gate 결과</h1>
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
    strict, strict_detail = build_strict_huber_scores(base, ref, meta, router, targets, feature_matrix)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt155_strict_stable_gain(base, ref, strict, targets))
    candidates.extend(pp_opt156_pp148_micro_gate(base, strict, targets))
    candidates.extend(pp_opt157_segment_quantile_gate(base, ref, strict, targets))
    candidates.extend(pp_opt158_tail_safe_gate(base, ref, router, strict, targets))
    candidates.extend(pp_opt159_pp148_strict_ensemble(base, ref, strict, targets))

    predictions = pd.concat([source] + pp149.reference_candidates(base, ref, router, targets) + candidates, ignore_index=True)
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
    label_map[decision["operational_protocol_candidate"]] = "pp160_operational_strict_huber_gate_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp160_p95_strict_huber_gate_challenger"
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
        "selected_references": selected_refs,
        "selected_pp119_sources": selected_pp119,
        "recomputed_reference_notes": ref_notes,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {"pp149_helper": str(PP149_SCRIPT.relative_to(REPO))},
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
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "strict_huber_gate_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "strict_huber_gate_result.html").write_text(report_html, encoding="utf-8")

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
