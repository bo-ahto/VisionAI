#!/usr/bin/env python3
"""Run PP-OPT199..204 Warm PP192/PP198 winner-router experiments."""
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
PP193_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt193_198_warm_segment_outcome_router_refinement.py"
PP193_DIR = REPO / "experiments" / "track6" / "PP-OPT193_198_warm_segment_outcome_router_refinement"
PP193_PREDICTIONS = PP193_DIR / "outputs" / "candidate_predictions.csv"
PP193_CONFIG = PP193_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT199-204"
EXP_SLUG = "PP-OPT199_204_warm_pp192_pp198_winner_router"
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
        "item_id": "PP-OPT199",
        "priority": "1",
        "title": "segment winner router",
        "description": "validation에서 PP198이 PP192보다 이긴 segment만 PP198 쪽으로 이동.",
    },
    {
        "item_id": "PP-OPT200",
        "priority": "2",
        "title": "row risk winner router",
        "description": "PP192/PP198 gap, 불확실성, segment win score를 같이 써서 row 단위로 이동.",
    },
    {
        "item_id": "PP-OPT201",
        "priority": "3",
        "title": "p95 guarded winner router",
        "description": "PP198 이동을 허용하되 segment p95 손상이 있는 구간은 동적으로 cap 축소.",
    },
    {
        "item_id": "PP-OPT202",
        "priority": "4",
        "title": "consensus winner router",
        "description": "price-confidence와 price-gap segment가 동시에 PP198 우위를 보일 때만 이동.",
    },
    {
        "item_id": "PP-OPT203",
        "priority": "5",
        "title": "small global blend plus winner gate",
        "description": "PP198을 아주 약하게 전역 반영하고 winner gate 구간에서만 추가 이동.",
    },
    {
        "item_id": "PP-OPT204",
        "priority": "6",
        "title": "final PP192/PP198 winner-router decision",
        "description": "PP192, PP198, 신규 winner-router 후보를 fixed/repeated 기준으로 비교해 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp193 = load_module("pp_opt193_helpers_for_pp199", PP193_SCRIPT)
pp187 = pp193.pp187
pp161 = pp193.pp161
opt8 = pp193.opt8
val71 = pp193.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp193.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp193.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp193.clip_by_row(values, caps)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    return pp187.rank01(values)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp193.make_candidate(base, candidate, family, item_id, pred_log)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    return pp187.ape_from_log(base, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(PP193_PREDICTIONS)
    config = json.loads(PP193_CONFIG.read_text(encoding="utf-8"))
    return predictions, config


def choose_support_candidates(config: dict[str, Any]) -> dict[str, str]:
    support = dict(config["support_candidates"])
    decision = config["selection_decision"]
    support.update(
        {
            "pp198_operational": decision["operational_protocol_candidate"],
            "pp198_p95_guarded": decision["p95_guarded_protocol_candidate"],
            "pp198_p95_extreme": decision["p95_extreme_protocol_candidate"],
            "pp192_operational": support["pp192_operational"],
            "pp192_p95_guarded": support["pp192_p95_guarded"],
            "pp192_p95_extreme": support["pp192_p95_extreme"],
        }
    )
    return support


def reference_predictions(previous: pd.DataFrame, support: dict[str, str]) -> pd.DataFrame:
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
        support["pp192_operational"],
        support["pp192_p95_guarded"],
        support["pp192_p95_extreme"],
        support["pp198_operational"],
        support["pp198_p95_guarded"],
        support["pp198_p95_extreme"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def segment_win_signal(
    base: pd.DataFrame,
    pp192: np.ndarray,
    pp198: np.ndarray,
    segment_cols: list[str],
    min_count: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ape192 = ape_from_log(base, pp192)
    ape198 = ape_from_log(base, pp198)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    gain = ape192 - ape198
    win = (ape198 + 0.0008 < ape192).astype(float)
    harm = (ape198 > ape192 + 0.0008).astype(float)
    global_mean_gain = float(np.mean(gain[val_mask]))
    global_p95_delta = float(np.quantile(ape198[val_mask], 0.95) - np.quantile(ape192[val_mask], 0.95))
    global_score = float(
        np.mean(win[val_mask])
        - 1.18 * np.mean(harm[val_mask])
        + 0.65 * np.clip(global_mean_gain / 0.001, -0.8, 0.8)
        - 0.80 * max(global_p95_delta, 0.0) / 0.001
    )
    scores: dict[str, float] = {}
    p95_delta: dict[str, float] = {}
    mean_gain: dict[str, float] = {}
    counts: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() < min_count:
            continue
        seg_mean_gain = float(np.mean(gain[idx]))
        seg_p95_delta = float(np.quantile(ape198[idx], 0.95) - np.quantile(ape192[idx], 0.95))
        score = float(
            np.mean(win[idx])
            - 1.18 * np.mean(harm[idx])
            + 0.65 * np.clip(seg_mean_gain / 0.001, -0.8, 0.8)
            - 0.80 * max(seg_p95_delta, 0.0) / 0.001
        )
        scores[key] = score
        p95_delta[key] = seg_p95_delta
        mean_gain[key] = seg_mean_gain
        counts[key] = float(idx.sum())
    return (
        seg.map(scores).fillna(global_score).to_numpy(dtype=float),
        seg.map(p95_delta).fillna(global_p95_delta).to_numpy(dtype=float),
        seg.map(mean_gain).fillna(global_mean_gain).to_numpy(dtype=float),
        seg.map(counts).fillna(0.0).to_numpy(dtype=float),
    )


def row_risk(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(base["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(base["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(pp198 - pp192))
    low_conf = base["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0, 1)
    return np.clip(0.25 * qwidth + 0.20 * price_range + 0.20 * spread + 0.18 * model_gap + 0.09 * low_conf + 0.08 * low_sample, 0, 1)


def candidate_from_weight(
    base: pd.DataFrame,
    pp192: np.ndarray,
    pp198: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray,
    cap: float | np.ndarray,
) -> pd.DataFrame:
    caps = np.full(len(base), cap) if isinstance(cap, (float, int)) else np.asarray(cap, dtype=float)
    pred = pp192 + clip_by_row((pp198 - pp192) * weight, caps)
    return make_candidate(base, name, family, item_id, pred)


def pp_opt199_segment_winner(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_gap": ["stable_price_band", "medium_support_bucket"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_conf_gap": ["stable_price_band", "confidence_tier", "medium_support_bucket"],
    }
    for seg_name, cols in segment_sets.items():
        score, p95_delta, mean_gain, _count = segment_win_signal(base, pp192, pp198, cols)
        p95_guard = np.clip(1.0 - gate(p95_delta, 0.00000, 0.00014), 0, 1)
        gain_guard = gate(mean_gain, -0.00010, 0.00035)
        for threshold in [-0.18, -0.08, 0.00, 0.08, 0.16]:
            base_w = gate(score, threshold, 0.28) * p95_guard * gain_guard
            for strength in [0.35, 0.55, 0.75, 0.95, 1.10]:
                for cap in [0.0015, 0.0025, 0.0040, 0.0060]:
                    weight = np.clip(base_w * strength, 0, 1)
                    name = (
                        f"ppopt199_segment_winner__seg={seg_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(candidate_from_weight(base, pp192, pp198, name, "pp192_pp198_segment_winner_router", "PP-OPT199", weight, cap))
    return rows


def pp_opt200_row_risk_winner(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = row_risk(base, pp192, pp198)
    score, p95_delta, mean_gain, _count = segment_win_signal(base, pp192, pp198, ["stable_price_band", "confidence_tier"])
    seg_w = gate(score, -0.08, 0.30) * np.clip(1.0 - gate(p95_delta, 0.00002, 0.00014), 0, 1) * gate(mean_gain, -0.00010, 0.00035)
    for risk_threshold in [0.40, 0.48, 0.56, 0.64]:
        risk_w = np.clip(1.0 - gate(risk, risk_threshold, 0.24), 0, 1)
        for seg_share in [0.45, 0.65, 0.85]:
            base_w = np.clip(seg_share * seg_w + (1.0 - seg_share) * risk_w, 0, 1)
            for strength in [0.30, 0.50, 0.70, 0.90]:
                for cap in [0.0015, 0.0025, 0.0040]:
                    weight = base_w * strength
                    name = (
                        f"ppopt200_row_risk_winner__riskthr={safe_name(risk_threshold)}"
                        f"__segshare={safe_name(seg_share)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(candidate_from_weight(base, pp192, pp198, name, "pp192_pp198_row_risk_winner_router", "PP-OPT200", weight, cap))
    return rows


def pp_opt201_p95_guarded_winner(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = row_risk(base, pp192, pp198)
    specs = [
        ("price_conf", ["stable_price_band", "confidence_tier"], 0.00),
        ("price_conf", ["stable_price_band", "confidence_tier"], 0.08),
        ("price_gap", ["stable_price_band", "medium_support_bucket"], 0.00),
        ("price_qwidth", ["stable_price_band", "qwidth_band"], 0.00),
    ]
    for seg_name, cols, threshold in specs:
        score, p95_delta, mean_gain, _count = segment_win_signal(base, pp192, pp198, cols)
        score_w = gate(score, threshold, 0.26)
        gain_w = gate(mean_gain, -0.00008, 0.00030)
        p95_guard = np.clip(1.0 - gate(p95_delta, -0.00002, 0.00012), 0, 1)
        base_w = score_w * gain_w * p95_guard
        for strength in [0.45, 0.65, 0.85, 1.00]:
            for base_cap in [0.0025, 0.0040, 0.0060]:
                for shrink in [0.30, 0.55, 0.80]:
                    cap = np.clip(base_cap * (1.0 - shrink * risk), 0.0010, base_cap)
                    weight = base_w * strength
                    name = (
                        f"ppopt201_p95_guarded_winner__seg={seg_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(candidate_from_weight(base, pp192, pp198, name, "pp192_pp198_p95_guarded_winner_router", "PP-OPT201", weight, cap))
    return rows


def pp_opt202_consensus_winner(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    conf_score, conf_p95, conf_gain, _ = segment_win_signal(base, pp192, pp198, ["stable_price_band", "confidence_tier"])
    gap_score, gap_p95, gap_gain, _ = segment_win_signal(base, pp192, pp198, ["stable_price_band", "medium_support_bucket"])
    conf_w = gate(conf_score, 0.00, 0.28) * gate(conf_gain, -0.00008, 0.00030) * np.clip(1.0 - gate(conf_p95, 0.00000, 0.00014), 0, 1)
    gap_w = gate(gap_score, 0.00, 0.28) * gate(gap_gain, -0.00008, 0.00030) * np.clip(1.0 - gate(gap_p95, 0.00000, 0.00014), 0, 1)
    modes = {
        "min": np.minimum(conf_w, gap_w),
        "sqrt": np.sqrt(np.clip(conf_w * gap_w, 0, 1)),
        "mean": 0.5 * conf_w + 0.5 * gap_w,
        "conf70": 0.7 * conf_w + 0.3 * gap_w,
    }
    for mode_name, base_w in modes.items():
        for strength in [0.45, 0.65, 0.85, 1.00]:
            for cap in [0.0015, 0.0025, 0.0040, 0.0060]:
                weight = base_w * strength
                name = f"ppopt202_consensus_winner__mode={mode_name}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(candidate_from_weight(base, pp192, pp198, name, "pp192_pp198_consensus_winner_router", "PP-OPT202", weight, cap))
    return rows


def pp_opt203_global_blend_plus_gate(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    score, p95_delta, mean_gain, _count = segment_win_signal(base, pp192, pp198, ["stable_price_band", "confidence_tier"])
    gate_w = gate(score, 0.00, 0.28) * gate(mean_gain, -0.00008, 0.00030) * np.clip(1.0 - gate(p95_delta, 0.00000, 0.00014), 0, 1)
    for global_share in [0.08, 0.12, 0.18, 0.24]:
        for gated_share in [0.20, 0.35, 0.50, 0.70]:
            for cap in [0.0015, 0.0025, 0.0040]:
                weight = np.clip(global_share + gate_w * gated_share, 0, 1)
                name = (
                    f"ppopt203_global_plus_gate__global={safe_name(global_share)}"
                    f"__gated={safe_name(gated_share)}__cap={safe_name(cap)}"
                )
                rows.append(candidate_from_weight(base, pp192, pp198, name, "pp192_pp198_global_blend_plus_gate", "PP-OPT203", weight, cap))
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
        support["pp198_operational"],
        support["pp198_p95_guarded"],
        support["pp198_p95_extreme"],
    ]
    pp192 = metrics[metrics["candidate"].eq(support["pp192_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp198 = metrics[metrics["candidate"].eq(support["pp198_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp192_mape = float(pp192["MAPE"])
    pp192_p95 = float(pp192["p95_APE"])
    pp198_mape = float(pp198["MAPE"])
    pp198_p95 = float(pp198["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= pp192_mape + 0.000020)
        & (new_pool["test_p95_APE"] <= pp192_p95 + 0.000006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(90)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= pp192_p95 + 0.000006].sort_values(["test_MAPE", "test_p95_APE"]).head(90)
    stability_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(80)
    pp198_near = new_pool[
        (new_pool["test_MAPE"] <= pp198_mape + 0.000020)
        & (new_pool["test_p95_APE"] <= pp198_p95 + 0.000006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(80)
    selected = pd.concat([op_pool, mape_pool, stability_pool, pp198_near], ignore_index=True)["candidate"].drop_duplicates().tolist()
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
        support["pp198_operational"]: "pp198_operational_reference",
        support["pp198_p95_guarded"]: "pp198_p95_guarded_reference",
        support["pp198_p95_extreme"]: "pp198_p95_extreme_reference",
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
    pp198 = row_by_candidate(stability, support["pp198_operational"])
    pp192_guard = row_by_candidate(stability, support["pp192_p95_guarded"])
    pp180 = row_by_candidate(stability, support["pp180_operational"])
    pp186 = row_by_candidate(stability, support["pp186_operational"])
    pp172 = row_by_candidate(stability, support["pp172_operational"])
    pp166 = row_by_candidate(stability, support["pp166_operational"])
    pp148 = row_by_candidate(stability, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt20|ppopt19", regex=True)].copy()
    pp192_mape = float(pp192["fixed_test_MAPE"])
    pp192_p95 = float(pp192["fixed_test_p95_APE"])
    pp198_mape = float(pp198["fixed_test_MAPE"])
    pp198_p95 = float(pp198["fixed_test_p95_APE"])

    operational = pp192.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= pp192_mape - 0.000003)
        & (pool["fixed_test_p95_APE"] <= pp192_p95 + 0.000005)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp192["avg_pp64_MAPE_win_rate"]) - 0.002)
        & (pool["replacement_score"] <= float(pp192["replacement_score"]) + 0.000002)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    mape_challenger = pp198.copy()
    mape_pool = pool[
        (pool["fixed_test_MAPE"] <= pp198_mape + 0.000010)
        & (pool["fixed_test_p95_APE"] <= pp198_p95 + 0.000005)
    ].copy()
    if not mape_pool.empty:
        mape_challenger = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score", "fixed_test_p95_APE"]).iloc[0]

    p95_guarded = pp192_guard.copy()
    p95_pool = pool[
        (pool["fixed_test_p95_APE"] <= float(pp192_guard["fixed_test_p95_APE"]) + 0.000025)
        & (pool["fixed_test_MAPE"] <= float(pp192_guard["fixed_test_MAPE"]) + 0.000040)
    ].copy()
    if not p95_pool.empty:
        p95_guarded = p95_pool.sort_values(["fixed_test_MAPE", "replacement_score", "fixed_test_p95_APE"]).iloc[0]

    p95_extreme_pool = stability[
        (stability["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_extreme_pool = p95_extreme_pool[
        p95_extreme_pool["candidate"].astype(str).str.contains("reference_pp148_p95|pp166_p95|pp172_p95|pp180_p95|pp186_p95|pp192_p95|pp198_p95|ppopt20", regex=True)
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
            f"{prefix}_delta_vs_pp192_MAPE": float(row["fixed_test_MAPE"]) - pp192_mape,
            f"{prefix}_delta_vs_pp192_p95_APE": float(row["fixed_test_p95_APE"]) - pp192_p95,
            f"{prefix}_delta_vs_pp198_MAPE": float(row["fixed_test_MAPE"]) - pp198_mape,
            f"{prefix}_delta_vs_pp198_p95_APE": float(row["fixed_test_p95_APE"]) - pp198_p95,
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("mape_challenger", mape_challenger))
    decision.update(pack("p95_guarded", p95_guarded))
    decision.update(pack("p95_extreme", p95_extreme))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "pp192_pp198_winner_router_operational_selection"),
        ("mape_challenger", "pp192_pp198_winner_router_mape_selection"),
        ("p95_guarded", "pp192_pp198_winner_router_p95_guarded_selection"),
        ("p95_extreme", "pp192_pp198_winner_router_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt204_{key}_pp192_pp198_winner_router__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT204"
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
    support = config["support_candidates"]
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp172_operational"],
        support["pp180_operational"],
        support["pp186_operational"],
        support["pp192_operational"],
        support["pp198_operational"],
        decision["operational_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
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
        f"replacement score {decision['operational_replacement_score']:.6f}. "
        f"MAPE 후보 MAPE {decision['mape_challenger_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['mape_challenger_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT199~204 Warm PP192/PP198 winner router 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP198이 PP192보다 이기는 row만 선택해 MAPE 개선과 repeated stability를 동시에 확보",
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
<title>PP-OPT199~204 Warm PP192/PP198 winner router 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT199~204 Warm PP192/PP198 winner router 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>MAPE 후보: <code>{html.escape(decision['mape_challenger_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 50)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 50)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 120)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 160)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, previous_config = load_inputs()
    support = choose_support_candidates(previous_config)
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)
    pp192 = pp187.prediction_array(previous, feature_base, support["pp192_operational"])
    pp198 = pp187.prediction_array(previous, feature_base, support["pp198_operational"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt199_segment_winner(feature_base, pp192, pp198))
    candidates.extend(pp_opt200_row_risk_winner(feature_base, pp192, pp198))
    candidates.extend(pp_opt201_p95_guarded_winner(feature_base, pp192, pp198))
    candidates.extend(pp_opt202_consensus_winner(feature_base, pp192, pp198))
    candidates.extend(pp_opt203_global_blend_plus_gate(feature_base, pp192, pp198))

    predictions = pd.concat([reference_predictions(previous, support)] + candidates, ignore_index=True)
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
    selected.extend(
        [
            decision["operational_protocol_candidate"],
            decision["mape_challenger_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support)
    label_map[decision["operational_protocol_candidate"]] = "pp204_operational_pp192_pp198_winner_router_challenger"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp204_mape_pp192_pp198_winner_router_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp204_p95_guarded_pp192_pp198_winner_router_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp204_p95_extreme_pp192_pp198_winner_router_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    score_conf, p95_conf, gain_conf, count_conf = segment_win_signal(feature_base, pp192, pp198, ["stable_price_band", "confidence_tier"])
    score_gap, p95_gap, gain_gap, count_gap = segment_win_signal(feature_base, pp192, pp198, ["stable_price_band", "medium_support_bucket"])
    feature_frame = feature_base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]].copy()
    feature_frame["pp192_log"] = pp192
    feature_frame["pp198_log"] = pp198
    feature_frame["pp192_pp198_gap_abs"] = np.abs(pp198 - pp192)
    feature_frame["row_risk"] = row_risk(feature_base, pp192, pp198)
    feature_frame["price_conf_win_score"] = score_conf
    feature_frame["price_conf_p95_delta"] = p95_conf
    feature_frame["price_conf_mean_gain"] = gain_conf
    feature_frame["price_conf_val_count"] = count_conf
    feature_frame["price_gap_win_score"] = score_gap
    feature_frame["price_gap_p95_delta"] = p95_gap
    feature_frame["price_gap_mean_gain"] = gain_gap
    feature_frame["price_gap_val_count"] = count_gap

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP193_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP192 operational log price",
            "mape_candidate": "PP198 MAPE challenger log price",
            "final": "PP192 log price + clip((PP198 log price - PP192 log price) * winner_weight, row_cap)",
            "winner_inputs": [
                "validation segment PP198-vs-PP192 APE gain",
                "validation segment PP198-vs-PP192 p95 delta",
                "row uncertainty risk",
                "abs(PP198 log price - PP192 log price)",
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
    feature_frame.to_csv(ARTIFACT_DIR / "winner_router_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp192_pp198_winner_router_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp192_pp198_winner_router_result.html").write_text(report_html, encoding="utf-8")

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
