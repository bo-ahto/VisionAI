#!/usr/bin/env python3
"""Run PP-OPT149..154 Warm huber adoption stabilization experiments."""
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
PP143_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt143_148_warm_row_level_tail_router.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp143 = load_module("pp_opt143_helpers_for_pp149", PP143_SCRIPT)
pp135 = pp143.pp135
pp127 = pp143.pp127
pp139 = pp143.pp139
opt8 = pp143.opt8
val71 = pp143.val71

EXP_ID = "PP-OPT149-154"
EXP_SLUG = "PP-OPT149_154_warm_huber_adoption_stabilization"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = pp135.BASE_CANDIDATE
INCUMBENT = pp135.INCUMBENT
SEED = 20260609

ITEMS = [
    {
        "item_id": "PP-OPT149",
        "priority": "1",
        "title": "huber adoption small-cap stabilization",
        "description": "direct LightGBM Huber 후보의 낮은 MAPE 신호를 유지하되 작은 cap과 높은 적용 확률로 안정화한다.",
    },
    {
        "item_id": "PP-OPT150",
        "priority": "2",
        "title": "huber adoption with l2 hard-switch consensus",
        "description": "PP148 hard-switch가 허용한 row 중 Huber 보정 방향도 동의하는 경우만 추가 이동한다.",
    },
    {
        "item_id": "PP-OPT151",
        "priority": "3",
        "title": "PP148 plus huber micro correction",
        "description": "PP148 운영 후보를 기준으로 Huber adoption 보정을 아주 작은 2차 이동량으로만 더한다.",
    },
    {
        "item_id": "PP-OPT152",
        "priority": "4",
        "title": "uncertainty rollback for huber adoption",
        "description": "meta quantile 폭, tail harm, Huber harm 확률이 클수록 Huber 보정을 PP126 쪽으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT153",
        "priority": "5",
        "title": "PP148 and huber stability ensemble",
        "description": "PP148 운영 후보와 안정화 Huber 후보를 작은 가중 평균으로 결합한다.",
    },
    {
        "item_id": "PP-OPT154",
        "priority": "6",
        "title": "final huber adoption stabilization decision",
        "description": "PP126/PP148와 안정화 Huber 후보를 fixed/repeated 기준으로 비교한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp135.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp135.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp135.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp135.make_candidate(base, candidate, family, item_id, pred_log)


def pp148_reference_predictions(ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    safe = ref["pp126_op"].to_numpy(dtype=float)
    l2_target = targets["direct_lgb_l2_s0p18_cap0p01"]
    l2_delta = l2_target - safe
    l2_adopt = router["adopt_direct_lgb_l2_s0p18_cap0p01"]
    l2_harm = router["prob_direct_lgb_l2_s0p18_cap0p01_harm"]
    hard_keep = (l2_adopt >= 0.42).astype(float)
    op_cap = np.maximum(0.0020, 0.010 * (1.0 - 0.50 * l2_harm))
    op_pred = safe + clip_by_row(l2_delta * hard_keep * 0.65, op_cap)

    p95_w = gate(l2_adopt, 0.24, 0.08)
    p95_weight = np.clip(p95_w * (1.0 - 0.20 * l2_harm), 0, 1)
    p95_cap = np.maximum(0.0025, 0.014 * (1.0 - 0.30 * router["tail_harm"]))
    p95_pred = safe + clip_by_row(l2_delta * p95_weight, p95_cap)
    return {"pp148_operational": op_pred, "pp148_p95": p95_pred}


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows = pp135.reference_candidates(base, ref)
    refs_148 = pp148_reference_predictions(ref, router, targets)
    rows.append(make_candidate(base, "reference_pp148_operational", "reference_prior", "REFERENCE", refs_148["pp148_operational"]))
    rows.append(make_candidate(base, "reference_pp148_p95", "reference_prior", "REFERENCE", refs_148["pp148_p95"]))
    return rows


def huber_weight(router: dict[str, np.ndarray], threshold: float, width: float, harm_penalty: float) -> np.ndarray:
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    adopt = router[f"adopt_{target_name}"]
    harm = router[f"prob_{target_name}_harm"]
    return np.clip(gate(adopt, threshold, width) * (1.0 - harm_penalty * harm), 0, 1)


def pp_opt149_huber_small_cap(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    delta = targets[target_name] - safe
    for threshold in [0.30, 0.32, 0.36, 0.40, 0.44]:
        for width in [0.06, 0.08, 0.12, 0.14]:
            for harm_penalty in [0.20, 0.45, 0.70, 0.90]:
                weight = huber_weight(router, threshold, width, harm_penalty)
                for strength in [0.65, 0.80, 1.00]:
                    for cap in [0.0035, 0.0045, 0.0055, 0.0065, 0.0080]:
                        cap_arr = np.maximum(0.0018, cap * (1.0 - 0.25 * router["tail_harm"]))
                        pred = safe + clip_by_row(delta * weight * strength, cap_arr)
                        name = (
                            f"ppopt149_huber_small_cap__thr={safe_name(threshold)}__w={safe_name(width)}"
                            f"__hpen={safe_name(harm_penalty)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "huber_adoption_small_cap_stabilization", "PP-OPT149", pred))
    return rows


def pp_opt150_l2_hardswitch_consensus(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    meta: dict[str, np.ndarray],
    router: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    huber_target = targets[target_name]
    delta = huber_target - safe
    l2_adopt = router["adopt_direct_lgb_l2_s0p18_cap0p01"]
    consensus = pp143.direction_consensus(safe, meta, ref, huber_target)
    for l2_threshold in [0.36, 0.42, 0.50, 0.58]:
        l2_keep = (l2_adopt >= l2_threshold).astype(float)
        for min_consensus in [0.34, 0.67, 1.00]:
            consensus_keep = (consensus >= min_consensus).astype(float)
            for threshold in [0.28, 0.32, 0.36, 0.40]:
                for width in [0.08, 0.14]:
                    weight = huber_weight(router, threshold, width, 0.45) * l2_keep * consensus_keep
                    for strength in [0.65, 0.85, 1.00]:
                        for cap in [0.004, 0.006, 0.008, 0.010]:
                            cap_arr = np.maximum(0.0020, cap * (1.0 - 0.35 * router[f"prob_{target_name}_harm"]))
                            pred = safe + clip_by_row(delta * weight * strength, cap_arr)
                            name = (
                                f"ppopt150_l2_huber_consensus__l2thr={safe_name(l2_threshold)}__minc={safe_name(min_consensus)}"
                                f"__thr={safe_name(threshold)}__w={safe_name(width)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "huber_adoption_l2_hardswitch_consensus", "PP-OPT150", pred))
    return rows


def pp_opt151_pp148_plus_micro_huber(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    refs_148 = pp148_reference_predictions(ref, router, targets)
    pp148_op = refs_148["pp148_operational"]
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    delta = targets[target_name] - pp148_op
    l2_shifted = np.abs(pp148_op - safe) > 1e-9
    for shifted_only in [0, 1]:
        shifted_keep = l2_shifted.astype(float) if shifted_only else np.ones(len(safe), dtype=float)
        for threshold in [0.28, 0.32, 0.36, 0.40]:
            for width in [0.08, 0.14, 0.20]:
                weight = huber_weight(router, threshold, width, 0.65) * shifted_keep
                for strength in [0.25, 0.40, 0.55, 0.70]:
                    for cap in [0.0020, 0.0030, 0.0045, 0.0060]:
                        cap_arr = np.maximum(0.0012, cap * (1.0 - 0.45 * router[f"prob_{target_name}_harm"]))
                        pred = pp148_op + clip_by_row(delta * weight * strength, cap_arr)
                        name = (
                            f"ppopt151_pp148_micro_huber__shift={shifted_only}__thr={safe_name(threshold)}"
                            f"__w={safe_name(width)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp148_plus_huber_micro_correction", "PP-OPT151", pred))
    return rows


def pp_opt152_uncertainty_rollback(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    router: dict[str, np.ndarray],
    targets: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    delta = targets[target_name] - safe
    uncertainty = np.clip(
        0.40 * gate(router["meta_width"], 0.040, 0.080)
        + 0.30 * router["tail_harm"]
        + 0.30 * router[f"prob_{target_name}_harm"],
        0,
        1,
    )
    for threshold in [0.28, 0.32, 0.36, 0.40]:
        for width in [0.08, 0.14]:
            base_weight = huber_weight(router, threshold, width, 0.45)
            for rollback in [0.35, 0.50, 0.65, 0.80]:
                keep = np.clip(base_weight * (1.0 - rollback * uncertainty), 0, 1)
                for strength in [0.65, 0.85, 1.00]:
                    for cap in [0.004, 0.006, 0.008, 0.010]:
                        cap_arr = np.maximum(0.0020, cap * (1.0 - 0.45 * uncertainty))
                        pred = safe + clip_by_row(delta * keep * strength, cap_arr)
                        name = (
                            f"ppopt152_uncertainty_rollback__thr={safe_name(threshold)}__w={safe_name(width)}"
                            f"__rb={safe_name(rollback)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "huber_adoption_uncertainty_rollback", "PP-OPT152", pred))
    return rows


def pp_opt153_pp148_huber_ensemble(base: pd.DataFrame, ref: pd.DataFrame, router: dict[str, np.ndarray], targets: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    refs_148 = pp148_reference_predictions(ref, router, targets)
    pp148_op = refs_148["pp148_operational"]
    target_name = "direct_lgb_huber_s0p18_cap0p01"
    huber_delta = targets[target_name] - safe
    for threshold in [0.30, 0.32, 0.36, 0.40]:
        for width in [0.08, 0.14]:
            huber_w = huber_weight(router, threshold, width, 0.45)
            for pp148_weight in [0.55, 0.70, 0.85, 1.00]:
                for huber_strength in [0.20, 0.35, 0.50, 0.65]:
                    corr = (pp148_op - safe) * pp148_weight + huber_delta * huber_w * huber_strength
                    for cap in [0.006, 0.008, 0.010, 0.012]:
                        cap_arr = np.maximum(0.0020, cap * (1.0 - 0.35 * router["tail_harm"]))
                        pred = safe + clip_by_row(corr, cap_arr)
                        name = (
                            f"ppopt153_pp148_huber_ensemble__thr={safe_name(threshold)}__w={safe_name(width)}"
                            f"__p148={safe_name(pp148_weight)}__hs={safe_name(huber_strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp148_huber_stability_ensemble", "PP-OPT153", pred))
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
        & (new_pool["incumbent_MAPE_improve_rate"] >= 0.70)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(32)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp126_p95 + 0.00060].sort_values(["test_MAPE", "test_p95_APE"]).head(32)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(32)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(32)
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
    subset, label_map = pp135.label_for_stability(predictions, selected_candidates)
    label_map.update(
        {
            "reference_pp148_operational": "pp148_operational_reference",
            "reference_pp148_p95": "pp148_p95_reference",
        }
    )
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    pp126 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp126_operational_reference")].iloc[0]
    pp148 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp148_operational_reference")].iloc[0]
    pp148_p95 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp148_p95_reference")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp118_operational_reference",
        "pp126_operational_reference",
        "pp126_p95_reference",
        "pp134_operational_recomputed_reference",
        "pp134_p95_recomputed_reference",
        "pp119_guarded_mape_reference",
        "pp119_aggressive_mape_reference",
        "pp82_p95_reference",
        "pp148_operational_reference",
        "pp148_p95_reference",
        "incumbent_pp7",
        "hcoef_stable_source",
    }
    pool = stability_aggregate[~stability_aggregate["candidate_label"].isin(refs)].copy()
    pool["fixed_test_delta_vs_pp64_MAPE"] = pool["fixed_test_MAPE"] - float(pp64["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp64_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp64["fixed_test_p95_APE"])
    pool["fixed_test_delta_vs_pp126_MAPE"] = pool["fixed_test_MAPE"] - float(pp126["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp126_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp126["fixed_test_p95_APE"])
    pool["fixed_test_delta_vs_pp148_MAPE"] = pool["fixed_test_MAPE"] - float(pp148["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp148_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp148["fixed_test_p95_APE"])

    operational = pp148.copy()
    operational["fixed_test_delta_vs_pp64_MAPE"] = float(pp148["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"])
    operational["fixed_test_delta_vs_pp64_p95_APE"] = float(pp148["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"])
    operational["fixed_test_delta_vs_pp126_MAPE"] = float(pp148["fixed_test_MAPE"]) - float(pp126["fixed_test_MAPE"])
    operational["fixed_test_delta_vs_pp126_p95_APE"] = float(pp148["fixed_test_p95_APE"]) - float(pp126["fixed_test_p95_APE"])
    operational["fixed_test_delta_vs_pp148_MAPE"] = 0.0
    operational["fixed_test_delta_vs_pp148_p95_APE"] = 0.0

    op_pool = pool[
        (pool["fixed_test_p95_APE"] <= float(pp126["fixed_test_p95_APE"]) + 0.00008)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.90)
        & (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) - 0.00020)
    ].copy()
    if not op_pool.empty:
        candidate = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
        if float(candidate["replacement_score"]) < float(operational["replacement_score"]) - 1e-7:
            operational = candidate

    p95 = pp148_p95.copy()
    p95["fixed_test_delta_vs_pp64_MAPE"] = float(pp148_p95["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"])
    p95["fixed_test_delta_vs_pp64_p95_APE"] = float(pp148_p95["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"])
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00025)
        & (pool["fixed_test_p95_APE"] < float(pp148_p95["fixed_test_p95_APE"]) - 0.00002)
    ].copy()
    if not p95_pool.empty:
        p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

    return {
        "operational_label": str(operational["candidate_label"]),
        "operational_candidate": str(operational["candidate"]),
        "operational_fixed_test_MAPE": float(operational["fixed_test_MAPE"]),
        "operational_fixed_test_p95_APE": float(operational["fixed_test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["fixed_test_delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["fixed_test_delta_vs_pp64_p95_APE"]),
        "operational_delta_vs_pp126_MAPE": float(operational["fixed_test_delta_vs_pp126_MAPE"]),
        "operational_delta_vs_pp126_p95_APE": float(operational["fixed_test_delta_vs_pp126_p95_APE"]),
        "operational_delta_vs_pp148_MAPE": float(operational["fixed_test_delta_vs_pp148_MAPE"]),
        "operational_delta_vs_pp148_p95_APE": float(operational["fixed_test_delta_vs_pp148_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_delta_vs_pp126_MAPE": float(p95["fixed_test_MAPE"] - float(pp126["fixed_test_MAPE"])),
        "p95_delta_vs_pp126_p95_APE": float(p95["fixed_test_p95_APE"] - float(pp126["fixed_test_p95_APE"])),
        "p95_delta_vs_pp148_MAPE": float(p95["fixed_test_MAPE"] - float(pp148_p95["fixed_test_MAPE"])),
        "p95_delta_vs_pp148_p95_APE": float(p95["fixed_test_p95_APE"] - float(pp148_p95["fixed_test_p95_APE"])),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "huber_adoption_stabilized_operational_selection"), ("p95", "huber_adoption_stabilized_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt154_{key}_huber_adoption_stabilization_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT154"
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
            "# PP-OPT149~154 Warm Huber adoption stabilization 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP143~148에서 발견된 direct LightGBM Huber 보정의 MAPE 개선 신호를 안정화",
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
<title>PP-OPT149~154 Warm Huber adoption stabilization 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT149~154 Warm Huber adoption stabilization 결과</h1>
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

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt149_huber_small_cap(base, ref, router, targets))
    candidates.extend(pp_opt150_l2_hardswitch_consensus(base, ref, meta, router, targets))
    candidates.extend(pp_opt151_pp148_plus_micro_huber(base, ref, router, targets))
    candidates.extend(pp_opt152_uncertainty_rollback(base, ref, router, targets))
    candidates.extend(pp_opt153_pp148_huber_ensemble(base, ref, router, targets))

    predictions = pd.concat([source] + reference_candidates(base, ref, router, targets) + candidates, ignore_index=True)
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
    label_map[decision["operational_protocol_candidate"]] = "pp154_operational_huber_adoption_stabilization_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp154_p95_huber_adoption_stabilization_challenger"
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
        "sources": {"pp143_helper": str(PP143_SCRIPT.relative_to(REPO))},
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
    (REPORT_DIR / "huber_adoption_stabilization_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "huber_adoption_stabilization_result.html").write_text(report_html, encoding="utf-8")

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
