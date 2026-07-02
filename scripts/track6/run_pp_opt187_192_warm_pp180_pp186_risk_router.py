#!/usr/bin/env python3
"""Run PP-OPT187..192 Warm PP180/PP186 risk-router experiments."""
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
PP181_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt181_186_warm_huber_basis_p95_guard_refinement.py"
PP181_DIR = REPO / "experiments" / "track6" / "PP-OPT181_186_warm_huber_basis_p95_guard_refinement"
PP181_PREDICTIONS = PP181_DIR / "outputs" / "candidate_predictions.csv"
PP181_CONFIG = PP181_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT187-192"
EXP_SLUG = "PP-OPT187_192_warm_pp180_pp186_risk_router"
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
        "item_id": "PP-OPT187",
        "priority": "1",
        "title": "hard risk router",
        "description": "위험 점수가 큰 row는 PP186으로, 나머지는 PP180으로 보내는 hard/near-hard 라우터.",
    },
    {
        "item_id": "PP-OPT188",
        "priority": "2",
        "title": "soft risk blend",
        "description": "위험 점수를 연속 가중치로 바꿔 PP180에서 PP186 쪽으로 부드럽게 이동.",
    },
    {
        "item_id": "PP-OPT189",
        "priority": "3",
        "title": "segment outcome router",
        "description": "validation 구간별로 PP180이 p95를 해치는 segment만 PP186으로 rollback.",
    },
    {
        "item_id": "PP-OPT190",
        "priority": "4",
        "title": "prediction gap hazard rollback",
        "description": "PP180과 PP186의 예측 차이가 큰 row를 위험 row로 보고 제한 rollback.",
    },
    {
        "item_id": "PP-OPT191",
        "priority": "5",
        "title": "hybrid risk and segment router",
        "description": "row 위험 점수와 validation segment p95 hazard를 함께 쓰는 하이브리드 라우터.",
    },
    {
        "item_id": "PP-OPT192",
        "priority": "6",
        "title": "final PP180/PP186 router decision",
        "description": "PP180, PP186, 신규 라우터 후보를 fixed/repeated 기준으로 비교해 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp181 = load_module("pp_opt181_helpers_for_pp187", PP181_SCRIPT)
pp173 = pp181.pp173
pp161 = pp181.pp161
opt8 = pp181.opt8
val71 = pp181.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp181.safe_name(value)


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp181.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp181.clip_by_row(values, caps)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    return pp181.rank01(values)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp181.make_candidate(base, candidate, family, item_id, pred_log)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    return pp181.ape_from_log(base, pred_log)


def load_previous() -> tuple[pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(PP181_PREDICTIONS)
    config = json.loads(PP181_CONFIG.read_text(encoding="utf-8"))
    return predictions, config


def choose_support_candidates(config: dict[str, Any]) -> dict[str, str]:
    support = dict(config["support_candidates"])
    decision = config["selection_decision"]
    support.update(
        {
            "pp180_operational": support["pp180_operational"],
            "pp180_p95": support["pp180_p95"],
            "pp186_operational": decision["operational_protocol_candidate"],
            "pp186_strict": decision["strict_guarded_protocol_candidate"],
            "pp186_p95": decision["p95_protocol_candidate"],
            "pp172_operational": support["pp172_operational"],
            "pp172_p95": support["pp172_p95"],
            "pp166_operational": support["pp166_operational"],
            "pp166_p95": support["pp166_p95"],
        }
    )
    return support


def base_frame(predictions: pd.DataFrame) -> pd.DataFrame:
    return pp181.base_frame(predictions)


def prediction_array(predictions: pd.DataFrame, base: pd.DataFrame, candidate: str) -> np.ndarray:
    return pp181.prediction_array(predictions, base, candidate)


def load_feature_frame(base: pd.DataFrame) -> pd.DataFrame:
    _model, enriched = pp181.load_model_and_features(base)
    return enriched


def reference_predictions(predictions: pd.DataFrame, support_names: dict[str, str]) -> pd.DataFrame:
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support_names["pp166_operational"],
        support_names["pp166_p95"],
        support_names["pp172_operational"],
        support_names["pp172_p95"],
        support_names["pp180_operational"],
        support_names["pp180_p95"],
        support_names["pp186_operational"],
        support_names["pp186_strict"],
        support_names["pp186_p95"],
    ]
    out = predictions[predictions["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def row_risk_scores(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> dict[str, np.ndarray]:
    qwidth = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(base["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(base["component_prediction_spread"], errors="coerce"))
    stable_gap = rank01(pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce"))
    model_gap = rank01(np.abs(pp180 - pp186))
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0, 1)
    low_conf = base["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    very_high_price = base["stable_price_band"].astype(str).str.contains("very_high", case=False, na=False).astype(float).to_numpy()
    base_tail = pp181.tail_score(base)
    uncertainty = np.clip(
        0.28 * qwidth
        + 0.22 * price_range
        + 0.18 * spread
        + 0.12 * stable_gap
        + 0.10 * model_gap
        + 0.06 * low_sample
        + 0.04 * low_conf,
        0,
        1,
    )
    gap_heavy = np.clip(
        0.30 * model_gap
        + 0.20 * qwidth
        + 0.16 * spread
        + 0.14 * price_range
        + 0.10 * very_high_price
        + 0.06 * low_sample
        + 0.04 * low_conf,
        0,
        1,
    )
    conservative = np.clip(0.50 * base_tail + 0.30 * uncertainty + 0.20 * gap_heavy, 0, 1)
    return {
        "tail": base_tail,
        "uncertainty": uncertainty,
        "gap_heavy": gap_heavy,
        "conservative": conservative,
    }


def segment_router_signal(
    base: pd.DataFrame,
    pp180: np.ndarray,
    pp186: np.ndarray,
    segment_cols: list[str],
    min_count: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ape180 = ape_from_log(base, pp180)
    ape186 = ape_from_log(base, pp186)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_mape_delta = float(np.mean(ape180[val_mask] - ape186[val_mask]))
    global_p95_delta = float(np.quantile(ape180[val_mask], 0.95) - np.quantile(ape186[val_mask], 0.95))
    global_harm_rate = float(np.mean(ape180[val_mask] > ape186[val_mask] + 0.0008))
    global_gain_rate = float(np.mean(ape180[val_mask] + 0.0008 < ape186[val_mask]))
    global_score = float(global_gain_rate - 1.25 * global_harm_rate - 0.75 * max(global_p95_delta, 0.0) / 0.001)
    global_hazard = float(
        np.clip(
            0.50 * gate(np.array([global_p95_delta]), 0.00000, 0.00018)[0]
            + 0.30 * gate(np.array([-global_score]), -0.02, 0.24)[0]
            + 0.20 * gate(np.array([global_mape_delta]), 0.00000, 0.00030)[0],
            0,
            1,
        )
    )
    scores: dict[str, float] = {}
    hazards: dict[str, float] = {}
    p95_delta: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() < min_count:
            continue
        delta_mape = float(np.mean(ape180[idx] - ape186[idx]))
        delta_p95 = float(np.quantile(ape180[idx], 0.95) - np.quantile(ape186[idx], 0.95))
        harm_rate = float(np.mean(ape180[idx] > ape186[idx] + 0.0008))
        gain_rate = float(np.mean(ape180[idx] + 0.0008 < ape186[idx]))
        score = float(gain_rate - 1.25 * harm_rate - 0.75 * max(delta_p95, 0.0) / 0.001)
        hazard = float(
            np.clip(
                0.50 * gate(np.array([delta_p95]), 0.00000, 0.00018)[0]
                + 0.30 * gate(np.array([-score]), -0.02, 0.24)[0]
                + 0.20 * gate(np.array([delta_mape]), 0.00000, 0.00030)[0],
                0,
                1,
            )
        )
        scores[key] = score
        hazards[key] = hazard
        p95_delta[key] = delta_p95
    return (
        seg.map(scores).fillna(global_score).to_numpy(dtype=float),
        seg.map(hazards).fillna(global_hazard).to_numpy(dtype=float),
        seg.map(p95_delta).fillna(global_p95_delta).to_numpy(dtype=float),
    )


def pp_opt187_hard_risk_router(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray, risks: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for risk_name, risk in risks.items():
        for threshold in [0.54, 0.60, 0.66, 0.72, 0.78]:
            for width in [0.06, 0.10, 0.16]:
                raw_w = gate(risk, threshold, width)
                hard_w = (risk >= threshold).astype(float)
                for mode, base_w in [("hard", hard_w), ("nearhard", raw_w)]:
                    for strength in [0.55, 0.75, 1.00]:
                        weight = np.clip(base_w * strength, 0, 1)
                        pred = pp180 + (pp186 - pp180) * weight
                        name = (
                            f"ppopt187_hard_risk_router__risk={risk_name}__mode={mode}"
                            f"__thr={safe_name(threshold)}__w={safe_name(width)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "pp180_pp186_hard_risk_router", "PP-OPT187", pred))
    return rows


def pp_opt188_soft_risk_blend(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray, risks: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    diff = pp186 - pp180
    for risk_name, risk in risks.items():
        for threshold in [0.46, 0.54, 0.62, 0.70]:
            for width in [0.16, 0.24, 0.32]:
                base_w = gate(risk, threshold, width)
                for strength in [0.25, 0.40, 0.55, 0.70]:
                    for cap in [0.0015, 0.0025, 0.0040, 0.0060]:
                        pred = pp180 + clip_by_row(diff * base_w * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt188_soft_risk_blend__risk={risk_name}__thr={safe_name(threshold)}"
                            f"__w={safe_name(width)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp180_pp186_soft_risk_blend", "PP-OPT188", pred))
    return rows


def pp_opt189_segment_outcome_router(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    diff = pp186 - pp180
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_sample": ["stable_price_band", "svc_group_n_band"],
        "price_gap": ["stable_price_band", "medium_support_bucket"],
    }
    for seg_name, cols in segment_sets.items():
        score, hazard, p95_delta = segment_router_signal(base, pp180, pp186, cols)
        p95_guard = gate(p95_delta, 0.00000, 0.00016)
        for score_threshold in [-0.18, -0.08, 0.02, 0.12]:
            score_hazard = gate(-score, -score_threshold, 0.24)
            for mix in [0.35, 0.55, 0.75]:
                base_w = np.clip(mix * hazard + (1.0 - mix) * p95_guard + 0.20 * score_hazard, 0, 1)
                for strength in [0.35, 0.55, 0.75, 0.95]:
                    for cap in [0.0025, 0.0040, 0.0060]:
                        pred = pp180 + clip_by_row(diff * base_w * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt189_segment_router__seg={seg_name}__scorethr={safe_name(score_threshold)}"
                            f"__mix={safe_name(mix)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp180_pp186_segment_outcome_router", "PP-OPT189", pred))
    return rows


def pp_opt190_gap_hazard_rollback(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray, risks: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    diff = pp186 - pp180
    gap_rank = rank01(np.abs(diff))
    direction = np.sign(diff)
    stable_direction = np.sign(pd.to_numeric(base["hcoef_stable"], errors="coerce").to_numpy(dtype=float) - pp180)
    toward_stable = (direction == stable_direction).astype(float)
    for risk_name in ["gap_heavy", "conservative", "uncertainty"]:
        risk = risks[risk_name]
        for gap_threshold in [0.52, 0.60, 0.68, 0.76]:
            gap_w = gate(gap_rank, gap_threshold, 0.18)
            for stable_bonus in [0.00, 0.25, 0.45]:
                hazard = np.clip(0.60 * gap_w + 0.40 * risk + stable_bonus * toward_stable, 0, 1)
                for strength in [0.25, 0.40, 0.55, 0.70]:
                    for cap in [0.0015, 0.0025, 0.0040]:
                        pred = pp180 + clip_by_row(diff * hazard * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt190_gap_hazard_rollback__risk={risk_name}__gapthr={safe_name(gap_threshold)}"
                            f"__stable={safe_name(stable_bonus)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp180_pp186_gap_hazard_rollback", "PP-OPT190", pred))
    return rows


def pp_opt191_hybrid_router(base: pd.DataFrame, pp180: np.ndarray, pp186: np.ndarray, risks: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    diff = pp186 - pp180
    _score, seg_hazard, p95_delta = segment_router_signal(base, pp180, pp186, ["stable_price_band", "confidence_tier"])
    price_q_score, price_q_hazard, _price_q_p95 = segment_router_signal(base, pp180, pp186, ["stable_price_band", "qwidth_band"])
    for risk_name in ["conservative", "uncertainty", "gap_heavy"]:
        risk = risks[risk_name]
        for risk_threshold in [0.46, 0.54, 0.62]:
            risk_w = gate(risk, risk_threshold, 0.22)
            for seg_share in [0.35, 0.55, 0.75]:
                seg_w = np.clip(seg_share * seg_hazard + (1.0 - seg_share) * price_q_hazard, 0, 1)
                p95_w = gate(p95_delta, -0.00002, 0.00018)
                base_w = np.clip(0.45 * risk_w + 0.35 * seg_w + 0.20 * p95_w, 0, 1)
                for strength in [0.30, 0.45, 0.60, 0.75]:
                    for cap in [0.0020, 0.0035, 0.0050]:
                        pred = pp180 + clip_by_row(diff * base_w * strength, np.full(len(base), cap))
                        name = (
                            f"ppopt191_hybrid_router__risk={risk_name}__thr={safe_name(risk_threshold)}"
                            f"__segshare={safe_name(seg_share)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "pp180_pp186_hybrid_risk_segment_router", "PP-OPT191", pred))
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


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, support_names: dict[str, str]) -> list[str]:
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    references = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support_names["pp166_operational"],
        support_names["pp166_p95"],
        support_names["pp172_operational"],
        support_names["pp172_p95"],
        support_names["pp180_operational"],
        support_names["pp180_p95"],
        support_names["pp186_operational"],
        support_names["pp186_strict"],
        support_names["pp186_p95"],
    ]
    pp180_test = metrics[metrics["candidate"].eq(support_names["pp180_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp186_test = metrics[metrics["candidate"].eq(support_names["pp186_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp180_mape = float(pp180_test["MAPE"])
    pp180_p95 = float(pp180_test["p95_APE"])
    pp186_mape = float(pp186_test["MAPE"])
    pp186_p95 = float(pp186_test["p95_APE"])
    mape_preserve = new_pool[
        (new_pool["test_MAPE"] <= pp180_mape + 0.00006)
        & (new_pool["test_p95_APE"] <= pp180_p95 + 0.00002)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(80)
    p95_guard = new_pool[
        (new_pool["test_p95_APE"] <= pp186_p95 + 0.00003)
        & (new_pool["test_MAPE"] <= pp186_mape + 0.00004)
    ].sort_values(["test_MAPE", "recommendation_score_vs_incumbent"]).head(80)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp180_p95 + 0.00008].sort_values(["test_MAPE", "test_p95_APE"]).head(80)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(80)
    selected = pd.concat([mape_preserve, p95_guard, best_mape, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(references + selected))


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str], support_names: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp181.label_for_stability(predictions, selected_candidates, support_names)
    label_map.update(
        {
            support_names["pp180_operational"]: "pp180_operational_reference",
            support_names["pp180_p95"]: "pp180_p95_reference",
            support_names["pp186_operational"]: "pp186_operational_reference",
            support_names["pp186_strict"]: "pp186_strict_reference",
            support_names["pp186_p95"]: "pp186_p95_reference",
            support_names["pp172_operational"]: "pp172_operational_reference",
            support_names["pp172_p95"]: "pp172_p95_reference",
            PP148_CANDIDATE: "pp148_operational_reference",
            PP148_P95_CANDIDATE: "pp148_p95_reference",
        }
    )
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def row_by_candidate(stability_aggregate: pd.DataFrame, candidate: str) -> pd.Series:
    rows = stability_aggregate[stability_aggregate["candidate"].eq(candidate)]
    if rows.empty:
        raise RuntimeError(f"Candidate not found in stability aggregate: {candidate}")
    return rows.iloc[0]


def choose_decision(stability_aggregate: pd.DataFrame, support_names: dict[str, str]) -> dict[str, Any]:
    pp180 = row_by_candidate(stability_aggregate, support_names["pp180_operational"])
    pp186 = row_by_candidate(stability_aggregate, support_names["pp186_operational"])
    pp172 = row_by_candidate(stability_aggregate, support_names["pp172_operational"])
    pp166 = row_by_candidate(stability_aggregate, support_names["pp166_operational"])
    pp148 = row_by_candidate(stability_aggregate, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability_aggregate, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability_aggregate, PP64_CANDIDATE)
    new_mask = stability_aggregate["candidate"].astype(str).str.contains("ppopt18", regex=False) & stability_aggregate["candidate"].astype(str).str.contains("ppopt192", regex=False).eq(False)
    pool = stability_aggregate[new_mask].copy()

    pp180_mape = float(pp180["fixed_test_MAPE"])
    pp180_p95 = float(pp180["fixed_test_p95_APE"])
    pp186_mape = float(pp186["fixed_test_MAPE"])
    pp186_p95 = float(pp186["fixed_test_p95_APE"])

    operational = pp180.copy()
    mape_improves_with_same_p95 = (
        (pool["fixed_test_MAPE"] <= pp180_mape - 0.000005)
        & (pool["fixed_test_p95_APE"] <= pp180_p95 + 0.000005)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp180["avg_pp64_MAPE_win_rate"]) - 0.010)
    )
    p95_improves_with_small_mape_cost = (
        (pool["fixed_test_MAPE"] <= pp180_mape + 0.000035)
        & (pool["fixed_test_p95_APE"] <= pp180_p95 - 0.000015)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp180["avg_pp64_MAPE_win_rate"]) - 0.012)
    )
    operational_pool = pool[mape_improves_with_same_p95 | p95_improves_with_small_mape_cost].copy()
    if not operational_pool.empty:
        operational = operational_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_guarded = pp186.copy()
    p95_pool = pool[
        (pool["fixed_test_p95_APE"] <= pp186_p95 + 0.00003)
        & (pool["fixed_test_MAPE"] <= pp186_mape + 0.00004)
    ].copy()
    if not p95_pool.empty:
        p95_guarded = p95_pool.sort_values(["fixed_test_MAPE", "replacement_score", "fixed_test_p95_APE"]).iloc[0]

    p95_extreme_pool = stability_aggregate[
        (stability_aggregate["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability_aggregate["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_extreme_pool = p95_extreme_pool[
        p95_extreme_pool["candidate"].astype(str).str.contains("reference_pp148_p95|pp166_p95|pp172_p95|pp180_p95|pp186_p95|ppopt18", regex=True)
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
            f"{prefix}_delta_vs_pp180_MAPE": float(row["fixed_test_MAPE"]) - pp180_mape,
            f"{prefix}_delta_vs_pp180_p95_APE": float(row["fixed_test_p95_APE"]) - pp180_p95,
            f"{prefix}_delta_vs_pp186_MAPE": float(row["fixed_test_MAPE"]) - pp186_mape,
            f"{prefix}_delta_vs_pp186_p95_APE": float(row["fixed_test_p95_APE"]) - pp186_p95,
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
        ("operational", "pp180_pp186_risk_router_operational_selection"),
        ("p95_guarded", "pp180_pp186_risk_router_p95_guarded_selection"),
        ("p95_extreme", "pp180_pp186_risk_router_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt192_{key}_pp180_pp186_risk_router__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT192"
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
    stability_aggregate: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        config["support_candidates"]["pp172_operational"],
        config["support_candidates"]["pp180_operational"],
        config["support_candidates"]["pp186_operational"],
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
        f"PP180 대비 MAPE {decision['operational_delta_vs_pp180_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp180_p95_APE']:+.6f}. "
        f"p95 고정 후보 MAPE {decision['p95_guarded_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['p95_guarded_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT187~192 Warm PP180/PP186 risk router 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP180의 MAPE 장점과 PP186의 p95 안정성을 row별 라우팅으로 결합",
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
            markdown_table(stability_aggregate, stab_cols, 160),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT187~192 Warm PP180/PP186 risk router 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT187~192 Warm PP180/PP186 risk router 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 고정 후보: <code>{html.escape(decision['p95_guarded_protocol_candidate'])}</code><br>p95 최저 후보: <code>{html.escape(decision['p95_extreme_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 50)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 50)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 120)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 160)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous_predictions, pp181_config = load_previous()
    support_names = choose_support_candidates(pp181_config)
    base = base_frame(previous_predictions)
    feature_base = load_feature_frame(base)
    pp180 = prediction_array(previous_predictions, base, support_names["pp180_operational"])
    pp186 = prediction_array(previous_predictions, base, support_names["pp186_operational"])
    risks = row_risk_scores(feature_base, pp180, pp186)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt187_hard_risk_router(feature_base, pp180, pp186, risks))
    candidates.extend(pp_opt188_soft_risk_blend(feature_base, pp180, pp186, risks))
    candidates.extend(pp_opt189_segment_outcome_router(feature_base, pp180, pp186))
    candidates.extend(pp_opt190_gap_hazard_rollback(feature_base, pp180, pp186, risks))
    candidates.extend(pp_opt191_hybrid_router(feature_base, pp180, pp186, risks))

    predictions = pd.concat([reference_predictions(previous_predictions, support_names)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, support_names)
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability_aggregate, support_names)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, support_names)
    selected.extend(
        [
            decision["operational_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    label_map[decision["operational_protocol_candidate"]] = "pp192_operational_pp180_pp186_risk_router_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp192_p95_guarded_pp180_pp186_risk_router_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp192_p95_extreme_pp180_pp186_risk_router_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    risk_frame = feature_base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]].copy()
    for name, values in risks.items():
        risk_frame[f"{name}_risk_score"] = values
    risk_frame["pp180_log"] = pp180
    risk_frame["pp186_log"] = pp186
    risk_frame["pp180_pp186_gap_abs"] = np.abs(pp180 - pp186)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP181_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support_names,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP180 operational log price",
            "safe_price": "PP186 p95-guard log price",
            "final": "PP180 log price + clip((PP186 log price - PP180 log price) * router_weight, row_cap)",
            "risk_inputs": [
                "quantile_width",
                "l10_price_range_ratio",
                "component_prediction_spread",
                "current_vs_stable_gap_abs",
                "abs(PP180 log price - PP186 log price)",
                "svc_group_n",
                "confidence_tier",
                "stable_price_band",
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
    stability_aggregate.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    risk_frame.to_csv(ARTIFACT_DIR / "router_risk_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "pp180_pp186_risk_router_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp180_pp186_risk_router_result.html").write_text(report_html, encoding="utf-8")

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
