#!/usr/bin/env python3
"""Run PP-OPT143..148 Warm row-level tail router experiments."""
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
PP135_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt135_138_warm_p95_aware_correction.py"
PP139_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt139_142_warm_direct_meta_stack.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp135 = load_module("pp_opt135_helpers_for_pp143", PP135_SCRIPT)
pp139 = load_module("pp_opt139_helpers_for_pp143", PP139_SCRIPT)
pp127 = pp135.pp127
opt8 = pp135.opt8
val71 = pp135.val71

EXP_ID = "PP-OPT143-148"
EXP_SLUG = "PP-OPT143_148_warm_row_level_tail_router"
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
        "item_id": "PP-OPT143",
        "priority": "1",
        "title": "tail-risk row-only direct-meta router",
        "description": "PP126을 기본값으로 두고 p95 위험 점수가 높은 row에서만 direct-meta p95 후보로 이동한다.",
    },
    {
        "item_id": "PP-OPT144",
        "priority": "2",
        "title": "learned adoption probability router",
        "description": "validation OOF에서 direct-meta 후보가 PP126보다 좋아진 row를 학습해 적용 확률로 사용한다.",
    },
    {
        "item_id": "PP-OPT145",
        "priority": "3",
        "title": "direction-consensus guarded router",
        "description": "direct-meta, quantile median, p95 후보의 이동 방향이 동의할 때만 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT146",
        "priority": "4",
        "title": "hard-switch quantile router",
        "description": "적용 확률 상위 row에만 아주 작은 hard switch를 허용하고 나머지는 PP126으로 유지한다.",
    },
    {
        "item_id": "PP-OPT147",
        "priority": "5",
        "title": "operation-tail dual router",
        "description": "중간 위험 구간은 PP134 운영 보정, 큰 tail 위험 구간은 direct-meta p95 보정을 섞는다.",
    },
    {
        "item_id": "PP-OPT148",
        "priority": "6",
        "title": "final row-level tail-router decision",
        "description": "PP126/PP134/PP139와 row-level router 후보를 같은 fixed/repeated 기준으로 비교한다.",
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


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return pp135.row_cap(base, cap, mode)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp135.make_candidate(base, candidate, family, item_id, pred_log)


def build_direct_targets(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    scores: dict[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    p95_risk = scores["p95_risk"]
    targets: dict[str, np.ndarray] = {}

    for key, strength, cap in [
        ("lgb_l2", 0.18, 0.010),
        ("lgb_q50", 0.18, 0.010),
        ("lgb_huber", 0.18, 0.010),
        ("lgb_l2", 0.28, 0.016),
        ("lgb_q50", 0.28, 0.016),
    ]:
        name = f"direct_{key}_s{safe_name(strength)}_cap{safe_name(cap)}"
        cap_arr = np.maximum(0.004, cap * (1.0 - 0.55 * p95_risk))
        targets[name] = safe + clip_by_row((meta[key] - safe) * strength, cap_arr)

    targets["pp126_p95"] = ref["pp126_p95"].to_numpy(dtype=float)
    targets["pp134_p95_recomputed"] = ref["pp134_p95_recomputed"].to_numpy(dtype=float)

    detail = base[["eval_split", "_track6_row_id"]].copy()
    detail["pp126_op"] = safe
    for name, pred in targets.items():
        detail[name] = pred
        detail[f"{name}_delta_from_pp126"] = pred - safe
    return targets, detail


def build_router_scores(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
    feature_matrix: pd.DataFrame,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    meta_width = np.abs(meta["lgb_q75"] - meta["lgb_q25"])
    direct_delta = targets["direct_lgb_l2_s0p18_cap0p01"] - safe
    tail_harm = np.maximum(signals["prob_plain_tail_harm"], signals["prob_plain_p95_harm"])
    tail_risk = np.clip(
        0.38 * scores["p95_risk"]
        + 0.24 * scores["tail_intent"]
        + 0.18 * tail_harm
        + 0.12 * gate(meta_width, 0.045, 0.085)
        + 0.08 * gate(np.abs(direct_delta), 0.006, 0.020),
        0,
        1,
    )

    ape_safe = ape_from_log(base, safe)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    safe_q80 = float(np.quantile(ape_safe[val_mask], 0.80))
    safe_q90 = float(np.quantile(ape_safe[val_mask], 0.90))

    learned: dict[str, np.ndarray] = {
        "meta_width": meta_width,
        "tail_risk": tail_risk,
        "tail_harm": tail_harm,
        "direct_delta_abs": np.abs(direct_delta),
        "pp126_validation_ape_q80": np.full(len(base), safe_q80),
        "pp126_validation_ape_q90": np.full(len(base), safe_q90),
    }
    for i, (target_name, target_pred) in enumerate(targets.items(), start=1):
        ape_target = ape_from_log(base, target_pred)
        gain_label = ((ape_target + 0.0010 < ape_safe) | ((ape_safe >= safe_q90) & (ape_target <= ape_safe + 0.0002))).astype(int)
        harm_label = ((ape_target > ape_safe + 0.0010) & (ape_safe >= safe_q80)).astype(int)
        learned[f"prob_{target_name}_gain"] = pp127.oof_lgbm_probability(base, feature_matrix, gain_label, seed_offset=1100 + 20 * i)
        learned[f"prob_{target_name}_harm"] = pp127.oof_lgbm_probability(base, feature_matrix, harm_label, seed_offset=1300 + 20 * i)
        learned[f"adopt_{target_name}"] = np.clip(
            learned[f"prob_{target_name}_gain"] * (1.0 - 0.70 * learned[f"prob_{target_name}_harm"]) * (0.60 + 0.40 * tail_risk),
            0,
            1,
        )

    detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in learned.items():
        detail[key] = value
    return learned, detail


def direction_consensus(safe: np.ndarray, meta: dict[str, np.ndarray], ref: pd.DataFrame, target: np.ndarray) -> np.ndarray:
    target_sign = np.sign(target - safe)
    q50_sign = np.sign(meta["lgb_q50"] - safe)
    l2_sign = np.sign(meta["lgb_l2"] - safe)
    p95_sign = np.sign(ref["pp126_p95"].to_numpy(dtype=float) - safe)
    agree = (target_sign == q50_sign).astype(float) + (target_sign == l2_sign).astype(float) + (target_sign == p95_sign).astype(float)
    return np.where(target_sign == 0, 0.0, agree / 3.0)


def pp_opt143_tail_risk_router(base: pd.DataFrame, ref: pd.DataFrame, scores: dict[str, np.ndarray], router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    tail_risk = router["tail_risk"]
    for target_name in ["direct_lgb_l2_s0p18_cap0p01", "direct_lgb_q50_s0p18_cap0p01", "pp134_p95_recomputed"]:
        delta = targets[target_name] - safe
        for threshold in [0.28, 0.36, 0.44, 0.52]:
            for width in [0.10, 0.16, 0.24]:
                base_w = gate(tail_risk, threshold, width)
                for strength in [0.35, 0.55, 0.75, 1.00]:
                    for cap in [0.006, 0.010, 0.014]:
                        cap_arr = np.maximum(0.0025, cap * (1.0 - 0.35 * router["tail_harm"]))
                        pred = safe + clip_by_row(delta * base_w * strength, cap_arr)
                        name = (
                            f"ppopt143_tail_risk_router__target={target_name}__thr={safe_name(threshold)}"
                            f"__w={safe_name(width)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "tail_risk_row_only_direct_meta_router", "PP-OPT143", pred))
    return rows


def pp_opt144_learned_adoption_router(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    for target_name in ["direct_lgb_l2_s0p18_cap0p01", "direct_lgb_q50_s0p18_cap0p01", "direct_lgb_huber_s0p18_cap0p01"]:
        delta = targets[target_name] - safe
        adopt = router[f"adopt_{target_name}"]
        for threshold in [0.16, 0.24, 0.32, 0.40, 0.50]:
            for width in [0.08, 0.14, 0.22]:
                prob_w = gate(adopt, threshold, width)
                for risk_weight in [0.20, 0.45, 0.70]:
                    weight = np.clip(prob_w * (1.0 - risk_weight * router[f"prob_{target_name}_harm"]), 0, 1)
                    for strength in [0.45, 0.65, 0.85, 1.00]:
                        for cap in [0.006, 0.010, 0.014]:
                            cap_arr = np.maximum(0.0025, cap * (1.0 - 0.30 * router["tail_harm"]))
                            pred = safe + clip_by_row(delta * weight * strength, cap_arr)
                            name = (
                                f"ppopt144_learned_adopt__target={target_name}__thr={safe_name(threshold)}"
                                f"__w={safe_name(width)}__hpen={safe_name(risk_weight)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "learned_adoption_probability_router", "PP-OPT144", pred))
    return rows


def pp_opt145_direction_consensus_router(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    router: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    for target_name in ["direct_lgb_l2_s0p18_cap0p01", "direct_lgb_q50_s0p18_cap0p01", "pp126_p95", "pp134_p95_recomputed"]:
        target = targets[target_name]
        delta = target - safe
        consensus = direction_consensus(safe, meta, ref, target)
        adopt = router.get(f"adopt_{target_name}", router["tail_risk"])
        for min_consensus in [0.34, 0.67, 1.00]:
            consensus_keep = (consensus >= min_consensus).astype(float)
            for threshold in [0.22, 0.32, 0.42]:
                prob_w = gate(adopt, threshold, 0.16) * consensus_keep
                for strength in [0.45, 0.65, 0.85]:
                    for cap in [0.006, 0.010, 0.014]:
                        cap_arr = np.maximum(0.0025, cap * (1.0 - 0.40 * router["tail_harm"]))
                        pred = safe + clip_by_row(delta * prob_w * strength, cap_arr)
                        name = (
                            f"ppopt145_direction_consensus__target={target_name}__minc={safe_name(min_consensus)}"
                            f"__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "direction_consensus_guarded_router", "PP-OPT145", pred))
    return rows


def pp_opt146_hard_switch_router(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    for target_name in ["direct_lgb_l2_s0p18_cap0p01", "direct_lgb_q50_s0p18_cap0p01"]:
        target = targets[target_name]
        adopt = router[f"adopt_{target_name}"]
        for threshold in [0.42, 0.50, 0.58, 0.66]:
            hard = (adopt >= threshold).astype(float)
            for tail_floor in [0.00, 0.25, 0.40]:
                keep = hard * (router["tail_risk"] >= tail_floor).astype(float)
                for strength in [0.40, 0.65, 1.00]:
                    for cap in [0.004, 0.007, 0.010]:
                        cap_arr = np.maximum(0.0020, cap * (1.0 - 0.50 * router[f"prob_{target_name}_harm"]))
                        pred = safe + clip_by_row((target - safe) * keep * strength, cap_arr)
                        name = (
                            f"ppopt146_hard_switch__target={target_name}__thr={safe_name(threshold)}"
                            f"__tail={safe_name(tail_floor)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "hard_switch_quantile_router", "PP-OPT146", pred))
    return rows


def pp_opt147_operation_tail_dual_router(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    pp134 = ref["pp134_op_recomputed"].to_numpy(dtype=float)
    tail_target = targets["direct_lgb_l2_s0p18_cap0p01"]
    mid_score = gate(router["tail_risk"], 0.18, 0.22) * np.clip(1.0 - router["tail_harm"], 0, 1)
    tail_score = gate(router["tail_risk"], 0.42, 0.20) * router["adopt_direct_lgb_l2_s0p18_cap0p01"]
    for mid_strength in [0.25, 0.45, 0.65]:
        for tail_strength in [0.25, 0.45, 0.65]:
            for harm_penalty in [0.25, 0.45, 0.65]:
                keep = np.clip(1.0 - harm_penalty * router["tail_harm"], 0, 1)
                corr = (pp134 - safe) * mid_score * mid_strength + (tail_target - safe) * tail_score * tail_strength
                for cap in [0.006, 0.010, 0.014, 0.018]:
                    cap_arr = np.maximum(0.0025, cap * keep)
                    pred = safe + clip_by_row(corr, cap_arr)
                    name = (
                        f"ppopt147_operation_tail_dual__mid={safe_name(mid_strength)}__tail={safe_name(tail_strength)}"
                        f"__hpen={safe_name(harm_penalty)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "operation_tail_dual_router", "PP-OPT147", pred))
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


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "row_level_tail_router_operational_selection"), ("p95", "row_level_tail_router_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt148_{key}_row_level_tail_router_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT148"
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


def render_reports(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    item_summary: pd.DataFrame,
    stability_aggregate: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        "reference_pp64_current_best",
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp134_operational_recomputed",
        "reference_pp134_p95_recomputed",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(
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
        "recommendation_score_vs_incumbent",
    ]
    stab_cols = [
        "candidate_label",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_vs_pp64_MAPE",
        "fixed_test_delta_vs_pp64_p95_APE",
        "avg_pp64_MAPE_win_rate",
        "avg_pp64_p95_win_rate",
        "replacement_score",
    ]
    verdict = (
        f"운영 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP126 대비 MAPE {decision['operational_delta_vs_pp126_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp126_p95_APE']:+.6f}. "
        f"p95 후보 fixed test MAPE {decision['p95_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['p95_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT143~148 Warm row-level tail router 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP126을 기본값으로 유지하면서 p95 위험 row만 direct-meta/보정 후보로 부분 전환",
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
            markdown_table(stability_aggregate, stab_cols, 80),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT143~148 Warm row-level tail router 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT143~148 Warm row-level tail router 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 30)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 30)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 80)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 80)}
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
    targets, target_detail = build_direct_targets(base, ref, meta, scores)
    router, router_detail = build_router_scores(base, ref, meta, scores, signals, targets, feature_matrix)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt143_tail_risk_router(base, ref, scores, router, targets))
    candidates.extend(pp_opt144_learned_adoption_router(base, ref, router, targets))
    candidates.extend(pp_opt145_direction_consensus_router(base, ref, meta, router, targets))
    candidates.extend(pp_opt146_hard_switch_router(base, ref, router, targets))
    candidates.extend(pp_opt147_operation_tail_dual_router(base, ref, router, targets))

    predictions = pd.concat([source] + pp135.reference_candidates(base, ref) + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = pp135.select_candidates_for_stability(metrics, aggregate)
    stability_predictions, label_map = pp135.label_for_stability(predictions, selected)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = pp135.select_protocol_candidates(stability_aggregate)
    predictions, decision = add_protocol_rows(predictions, decision)

    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = pp135.select_candidates_for_stability(metrics, aggregate)
    selected.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = pp135.label_for_stability(predictions, selected)
    label_map[decision["operational_protocol_candidate"]] = "pp148_operational_row_level_tail_router_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp148_p95_row_level_tail_router_challenger"
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
        "sources": {
            "pp135_helper": str(PP135_SCRIPT.relative_to(REPO)),
            "pp139_helper": str(PP139_SCRIPT.relative_to(REPO)),
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
    prior_signal_detail.to_csv(ARTIFACT_DIR / "prior_learned_signal_detail.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "p95_aware_signal_detail.csv", index=False)
    meta_detail.to_csv(ARTIFACT_DIR / "direct_meta_prediction_detail.csv", index=False)
    target_detail.to_csv(ARTIFACT_DIR / "direct_target_prediction_detail.csv", index=False)
    router_detail.to_csv(ARTIFACT_DIR / "row_level_router_signal_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "row_level_tail_router_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "row_level_tail_router_result.html").write_text(report_html, encoding="utf-8")

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
                "avg_pp64_MAPE_win_rate",
                "avg_pp64_p95_win_rate",
                "replacement_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
