#!/usr/bin/env python3
"""Run PP-OPT193..198 Warm segment-outcome router refinement experiments."""
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
PP187_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt187_192_warm_pp180_pp186_risk_router.py"
PP181_DIR = REPO / "experiments" / "track6" / "PP-OPT181_186_warm_huber_basis_p95_guard_refinement"
PP181_PREDICTIONS = PP181_DIR / "outputs" / "candidate_predictions.csv"
PP181_CONFIG = PP181_DIR / "artifacts" / "run_config.json"
PP187_DIR = REPO / "experiments" / "track6" / "PP-OPT187_192_warm_pp180_pp186_risk_router"
PP187_CONFIG = PP187_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT193-198"
EXP_SLUG = "PP-OPT193_198_warm_segment_outcome_router_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = "hcoef_stable"
INCUMBENT_CANDIDATE = "incumbent_operational_pp_opt7"
PP64_CANDIDATE = "reference_pp64_current_best"
PP70_CANDIDATE = "reference_pp70_refinement"
PP126_CANDIDATE = "reference_pp126_operational"
PP148_CANDIDATE = "reference_pp148_operational"
PP148_P95_CANDIDATE = "reference_pp148_p95"

ITEMS = [
    {
        "item_id": "PP-OPT193",
        "priority": "1",
        "title": "price-gap segment router refinement",
        "description": "PP192가 선택한 stable price band x medium/support 구간 라우터 주변 파라미터를 좁게 재탐색.",
    },
    {
        "item_id": "PP-OPT194",
        "priority": "2",
        "title": "price-confidence segment router refinement",
        "description": "test MAPE가 가장 낮았던 stable price band x confidence tier 라우터 주변을 안정성 기준으로 재검증.",
    },
    {
        "item_id": "PP-OPT195",
        "priority": "3",
        "title": "price-gap and confidence combined router",
        "description": "price-gap hazard와 price-confidence hazard를 가중 결합해 단일 segment 편향을 줄인다.",
    },
    {
        "item_id": "PP-OPT196",
        "priority": "4",
        "title": "p95-constrained dynamic cap router",
        "description": "segment p95 hazard가 큰 구간은 cap을 줄이고 안정 구간만 더 크게 이동한다.",
    },
    {
        "item_id": "PP-OPT197",
        "priority": "5",
        "title": "segment consensus router",
        "description": "price-gap과 confidence segment가 동시에 위험하다고 보는 row만 PP186 쪽으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT198",
        "priority": "6",
        "title": "final segment router decision",
        "description": "PP192와 신규 세분화 후보를 fixed/repeated 기준으로 비교해 운영 후보를 선택한다.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp187 = load_module("pp_opt187_helpers_for_pp193", PP187_SCRIPT)
pp181 = pp187.pp181
pp161 = pp187.pp161
opt8 = pp187.opt8
val71 = pp187.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp187.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp187.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp187.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp187.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    predictions = pd.read_csv(PP181_PREDICTIONS)
    pp181_config = json.loads(PP181_CONFIG.read_text(encoding="utf-8"))
    pp187_config = json.loads(PP187_CONFIG.read_text(encoding="utf-8"))
    return predictions, pp181_config, pp187_config


def choose_support_candidates(pp181_config: dict[str, Any], pp187_config: dict[str, Any]) -> dict[str, str]:
    support = dict(pp181_config["support_candidates"])
    pp181_decision = pp181_config["selection_decision"]
    pp187_decision = pp187_config["selection_decision"]
    support.update(
        {
            "pp172_operational": support["pp172_operational"],
            "pp172_p95": support["pp172_p95"],
            "pp166_operational": support["pp166_operational"],
            "pp166_p95": support["pp166_p95"],
            "pp180_operational": support["pp180_operational"],
            "pp180_p95": support["pp180_p95"],
            "pp186_operational": pp181_decision["operational_protocol_candidate"],
            "pp186_strict": pp181_decision["strict_guarded_protocol_candidate"],
            "pp186_p95": pp181_decision["p95_protocol_candidate"],
            "pp192_operational": pp187_decision["operational_protocol_candidate"],
            "pp192_p95_guarded": pp187_decision["p95_guarded_protocol_candidate"],
            "pp192_p95_extreme": pp187_decision["p95_extreme_protocol_candidate"],
        }
    )
    return support


def segment_weight(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray, segment: str, scorethr: float, mix: float) -> np.ndarray:
    cols = {
        "price_gap": ["stable_price_band", "medium_support_bucket"],
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
    }[segment]
    score, hazard, p95_delta = pp187.segment_router_signal(base, pp180, pp186, cols)
    p95_guard = gate(p95_delta, 0.00000, 0.00016)
    score_hazard = gate(-score, -scorethr, 0.24)
    return np.clip(mix * hazard + (1.0 - mix) * p95_guard + 0.20 * score_hazard, 0, 1)


def segment_prediction(
    base: pd.DataFrame,
    pp180: np.ndarray,
    pp186: np.ndarray,
    segment: str,
    scorethr: float,
    mix: float,
    strength: float,
    cap: float,
) -> np.ndarray:
    weight = segment_weight(base, pp180, pp186, segment, scorethr, mix)
    return pp180 + clip_by_row((pp186 - pp180) * weight * strength, np.full(len(base), cap))


def p95_guarded_prediction(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> np.ndarray:
    risks = pp187.row_risk_scores(base, pp180, pp186)
    weight = (risks["uncertainty"] >= 0.78).astype(float) * 0.75
    return pp180 + (pp186 - pp180) * weight


def reference_predictions(
    previous: pd.DataFrame,
    base: pd.DataFrame,
    support: dict[str, str],
    pp180: np.ndarray,
    pp186: np.ndarray,
) -> pd.DataFrame:
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp166_operational"],
        support["pp166_p95"],
        support["pp172_operational"],
        support["pp172_p95"],
        support["pp180_operational"],
        support["pp180_p95"],
        support["pp186_operational"],
        support["pp186_p95"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    op192 = segment_prediction(base, pp180, pp186, "price_gap", 0.02, 0.75, 0.95, 0.0025)
    guard192 = p95_guarded_prediction(base, pp180, pp186)
    p95_extreme = pp187.prediction_array(previous, base, PP148_P95_CANDIDATE)
    out = pd.concat(
        [
            out,
            make_candidate(base, support["pp192_operational"], "reference_prior", "REFERENCE", op192),
            make_candidate(base, support["pp192_p95_guarded"], "reference_prior", "REFERENCE", guard192),
            make_candidate(base, support["pp192_p95_extreme"], "reference_prior", "REFERENCE", p95_extreme),
        ],
        ignore_index=True,
    )
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def pp_opt193_price_gap(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for scorethr in [-0.08, 0.00, 0.02, 0.06, 0.12]:
        for mix in [0.70, 0.75, 0.80, 0.85]:
            for strength in [0.85, 0.95, 1.05]:
                for cap in [0.0015, 0.0025, 0.0035, 0.0050]:
                    pred = segment_prediction(base, pp180, pp186, "price_gap", scorethr, mix, strength, cap)
                    name = (
                        f"ppopt193_price_gap_refine__scorethr={safe_name(scorethr)}__mix={safe_name(mix)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "segment_price_gap_refinement", "PP-OPT193", pred))
    return rows


def pp_opt194_price_conf(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for scorethr in [-0.08, 0.00, 0.02, 0.08, 0.12, 0.16]:
        for mix in [0.25, 0.35, 0.45, 0.55]:
            for strength in [0.85, 0.95, 1.05]:
                for cap in [0.0025, 0.0040, 0.0060, 0.0080]:
                    pred = segment_prediction(base, pp180, pp186, "price_conf", scorethr, mix, strength, cap)
                    name = (
                        f"ppopt194_price_conf_refine__scorethr={safe_name(scorethr)}__mix={safe_name(mix)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "segment_price_conf_refinement", "PP-OPT194", pred))
    return rows


def pp_opt195_combined(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    gap_weights = {
        scorethr: segment_weight(base, pp180, pp186, "price_gap", scorethr, 0.75)
        for scorethr in [-0.08, 0.02]
    }
    conf_weights = {
        scorethr: segment_weight(base, pp180, pp186, "price_conf", scorethr, 0.35)
        for scorethr in [0.02, 0.12]
    }
    for gap_thr, gap_w in gap_weights.items():
        for conf_thr, conf_w in conf_weights.items():
            for gap_share in [0.30, 0.50, 0.70]:
                base_w = np.clip(gap_share * gap_w + (1.0 - gap_share) * conf_w, 0, 1)
                for strength in [0.85, 0.95, 1.05]:
                    for cap in [0.0025, 0.0040, 0.0060]:
                        pred = pp180 + clip_by_row((pp186 - pp180) * base_w * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt195_gap_conf_combined__gapthr={safe_name(gap_thr)}__confthr={safe_name(conf_thr)}"
                            f"__gapshare={safe_name(gap_share)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "segment_gap_conf_combined_router", "PP-OPT195", pred))
    return rows


def pp_opt196_dynamic_cap(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp187.row_risk_scores(base, pp180, pp186)["conservative"]
    specs = [
        ("price_gap", 0.02, 0.75),
        ("price_gap", -0.08, 0.75),
        ("price_conf", 0.02, 0.35),
        ("price_conf", 0.12, 0.35),
    ]
    for segment, scorethr, mix in specs:
        base_w = segment_weight(base, pp180, pp186, segment, scorethr, mix)
        for strength in [0.85, 0.95, 1.05]:
            for base_cap in [0.0025, 0.0040, 0.0060]:
                for shrink in [0.30, 0.55, 0.80]:
                    cap = np.clip(base_cap * (1.0 - shrink * risk), 0.0012, base_cap)
                    pred = pp180 + clip_by_row((pp186 - pp180) * base_w * strength, cap)
                    name = (
                        f"ppopt196_dynamic_cap__seg={segment}__scorethr={safe_name(scorethr)}__mix={safe_name(mix)}"
                        f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(make_candidate(base, name, "segment_dynamic_cap_router", "PP-OPT196", pred))
    return rows


def pp_opt197_consensus(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    gap_w = segment_weight(base, pp180, pp186, "price_gap", 0.02, 0.75)
    conf_w = segment_weight(base, pp180, pp186, "price_conf", 0.12, 0.35)
    reducers = {
        "min": np.minimum(gap_w, conf_w),
        "mean": 0.5 * gap_w + 0.5 * conf_w,
        "sqrt": np.sqrt(np.clip(gap_w * conf_w, 0, 1)),
    }
    for reducer_name, base_w in reducers.items():
        for strength in [0.85, 0.95, 1.05, 1.15]:
            for cap in [0.0025, 0.0040, 0.0060]:
                pred = pp180 + clip_by_row((pp186 - pp180) * base_w * strength, np.full(len(base), cap))
                name = f"ppopt197_consensus__mode={reducer_name}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "segment_consensus_router", "PP-OPT197", pred))
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


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, support: dict[str, str]) -> list[str]:
    refs = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp166_operational"],
        support["pp166_p95"],
        support["pp172_operational"],
        support["pp172_p95"],
        support["pp180_operational"],
        support["pp180_p95"],
        support["pp186_operational"],
        support["pp186_p95"],
        support["pp192_operational"],
        support["pp192_p95_guarded"],
        support["pp192_p95_extreme"],
    ]
    pp192 = metrics[metrics["candidate"].eq(support["pp192_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp192_guard = metrics[metrics["candidate"].eq(support["pp192_p95_guarded"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp192_mape = float(pp192["MAPE"])
    pp192_p95 = float(pp192["p95_APE"])
    guard_mape = float(pp192_guard["MAPE"])
    guard_p95 = float(pp192_guard["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= pp192_mape + 0.000035)
        & (new_pool["test_p95_APE"] <= pp192_p95 + 0.000010)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(90)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= pp192_p95 + 0.000010].sort_values(["test_MAPE", "test_p95_APE"]).head(90)
    p95_pool = new_pool[
        (new_pool["test_p95_APE"] <= guard_p95 + 0.000030)
        & (new_pool["test_MAPE"] <= guard_mape + 0.000035)
    ].sort_values(["test_MAPE", "recommendation_score_vs_incumbent"]).head(70)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(70)
    selected = pd.concat([op_pool, mape_pool, p95_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(refs + selected))


def label_for_stability(predictions: pd.DataFrame, selected: list[str], support: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset = predictions[predictions["candidate"].isin(selected)].copy()
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT_CANDIDATE: "incumbent_pp7",
        "current_70_30": "current_70_30",
        PP64_CANDIDATE: "pp64_current_best",
        PP70_CANDIDATE: "pp70_refinement_candidate",
        PP126_CANDIDATE: "pp126_operational_reference",
        PP148_CANDIDATE: "pp148_operational_reference",
        PP148_P95_CANDIDATE: "pp148_p95_reference",
        support["pp166_operational"]: "pp166_operational_reference",
        support["pp166_p95"]: "pp166_p95_reference",
        support["pp172_operational"]: "pp172_operational_reference",
        support["pp172_p95"]: "pp172_p95_reference",
        support["pp180_operational"]: "pp180_operational_reference",
        support["pp180_p95"]: "pp180_p95_reference",
        support["pp186_operational"]: "pp186_operational_reference",
        support["pp186_p95"]: "pp186_p95_reference",
        support["pp192_operational"]: "pp192_operational_reference",
        support["pp192_p95_guarded"]: "pp192_p95_guarded_reference",
        support["pp192_p95_extreme"]: "pp192_p95_extreme_reference",
    }
    for candidate in selected:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def row_by_candidate(stability: pd.DataFrame, candidate: str) -> pd.Series:
    rows = stability[stability["candidate"].eq(candidate)]
    if rows.empty:
        raise RuntimeError(f"Candidate not found in stability aggregate: {candidate}")
    return rows.iloc[0]


def choose_decision(stability: pd.DataFrame, support: dict[str, str]) -> dict[str, Any]:
    pp192 = row_by_candidate(stability, support["pp192_operational"])
    pp192_guard = row_by_candidate(stability, support["pp192_p95_guarded"])
    pp180 = row_by_candidate(stability, support["pp180_operational"])
    pp186 = row_by_candidate(stability, support["pp186_operational"])
    pp172 = row_by_candidate(stability, support["pp172_operational"])
    pp166 = row_by_candidate(stability, support["pp166_operational"])
    pp148 = row_by_candidate(stability, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt19", regex=False)].copy()
    pp192_mape = float(pp192["fixed_test_MAPE"])
    pp192_p95 = float(pp192["fixed_test_p95_APE"])
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= pp192_mape - 0.000003)
        & (pool["fixed_test_p95_APE"] <= pp192_p95 + 0.000005)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp192["avg_pp64_MAPE_win_rate"]) - 0.004)
    ].copy()
    operational = pp192.copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
    p95_pool = pool[
        (pool["fixed_test_p95_APE"] <= float(pp192_guard["fixed_test_p95_APE"]) + 0.000025)
        & (pool["fixed_test_MAPE"] <= float(pp192_guard["fixed_test_MAPE"]) + 0.000040)
    ].copy()
    p95_guarded = pp192_guard.copy()
    if not p95_pool.empty:
        p95_guarded = p95_pool.sort_values(["fixed_test_MAPE", "replacement_score", "fixed_test_p95_APE"]).iloc[0]
    p95_extreme_pool = stability[
        (stability["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_extreme_pool = p95_extreme_pool[
        p95_extreme_pool["candidate"].astype(str).str.contains("reference_pp148_p95|pp166_p95|pp172_p95|pp180_p95|pp186_p95|pp192_p95|ppopt19", regex=True)
    ]
    p95_extreme = p95_extreme_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp126_MAPE": float(row["fixed_test_MAPE"]) - float(pp126["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp126_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp126["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp148_MAPE": float(row["fixed_test_MAPE"]) - float(pp148["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp148_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp148["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp166_MAPE": float(row["fixed_test_MAPE"]) - float(pp166["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp166_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp166["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp172_MAPE": float(row["fixed_test_MAPE"]) - float(pp172["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp172_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp172["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp180_MAPE": float(row["fixed_test_MAPE"]) - float(pp180["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp180_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp180["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp186_MAPE": float(row["fixed_test_MAPE"]) - float(pp186["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp186_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp186["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp192_MAPE": float(row["fixed_test_MAPE"]) - float(pp192["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp192_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp192["fixed_test_p95_APE"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("p95_guarded", p95_guarded))
    decision.update(pack("p95_extreme", p95_extreme))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "segment_router_refinement_operational_selection"),
        ("p95_guarded", "segment_router_refinement_p95_guarded_selection"),
        ("p95_extreme", "segment_router_refinement_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt198_{key}_segment_router_refinement__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT198"
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
    lines = ["| " + " | ".join(str(col) for col in view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
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
    stability: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    support = config["support_candidates"]
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp172_operational"],
        support["pp180_operational"],
        support["pp186_operational"],
        support["pp192_operational"],
        support["pp192_p95_guarded"],
        decision["operational_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
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
        f"PP192 대비 MAPE {decision['operational_delta_vs_pp192_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp192_p95_APE']:+.6f}. "
        f"p95 후보 MAPE {decision['p95_guarded_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['p95_guarded_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT193~198 Warm segment outcome router refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP192 segment outcome router 주변 파라미터를 좁게 재탐색",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 50),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 50),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 120),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability, stab_cols, 160),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT193~198 Warm segment outcome router refinement 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT193~198 Warm segment outcome router refinement 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_guarded_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 50)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 50)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 120)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 160)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, pp181_config, pp187_config = load_inputs()
    support = choose_support_candidates(pp181_config, pp187_config)
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)
    pp180 = pp187.prediction_array(previous, feature_base, support["pp180_operational"])
    pp186 = pp187.prediction_array(previous, feature_base, support["pp186_operational"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt193_price_gap(feature_base, pp180, pp186))
    candidates.extend(pp_opt194_price_conf(feature_base, pp180, pp186))
    candidates.extend(pp_opt195_combined(feature_base, pp180, pp186))
    candidates.extend(pp_opt196_dynamic_cap(feature_base, pp180, pp186))
    candidates.extend(pp_opt197_consensus(feature_base, pp180, pp186))

    predictions = pd.concat([reference_predictions(previous, feature_base, support, pp180, pp186)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, support)
    stability_predictions, label_map = label_for_stability(predictions, selected, support)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, support)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, support)
    selected.extend([decision["operational_protocol_candidate"], decision["p95_guarded_protocol_candidate"], decision["p95_extreme_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support)
    label_map[decision["operational_protocol_candidate"]] = "pp198_operational_segment_router_refinement_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp198_p95_guarded_segment_router_refinement_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp198_p95_extreme_segment_router_refinement_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    risk_frame = feature_base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]].copy()
    risk_frame["price_gap_weight_pp192"] = segment_weight(feature_base, pp180, pp186, "price_gap", 0.02, 0.75)
    risk_frame["price_conf_weight_mapebest"] = segment_weight(feature_base, pp180, pp186, "price_conf", 0.12, 0.35)
    risk_frame["pp180_log"] = pp180
    risk_frame["pp186_log"] = pp186
    risk_frame["pp180_pp186_gap_abs"] = np.abs(pp180 - pp186)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP187_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP192 uses PP180 operational log price as base",
            "safe_price": "PP186 p95-guard log price",
            "final": "PP180 log price + clip((PP186 log price - PP180 log price) * segment_weight * strength, row_cap)",
            "segments": [
                "stable_price_band x medium_support_bucket",
                "stable_price_band x confidence_tier",
                "combined segment weights",
            ],
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
    stability.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    risk_frame.to_csv(ARTIFACT_DIR / "segment_router_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "segment_outcome_router_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "segment_outcome_router_refinement_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family"]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability[
            ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
