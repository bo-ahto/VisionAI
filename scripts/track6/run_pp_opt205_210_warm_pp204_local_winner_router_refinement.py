#!/usr/bin/env python3
"""Run PP-OPT205..210 Warm PP204 local winner-router refinement experiments."""
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
PP199_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt199_204_warm_pp192_pp198_winner_router.py"
PP199_DIR = REPO / "experiments" / "track6" / "PP-OPT199_204_warm_pp192_pp198_winner_router"
PP199_PREDICTIONS = PP199_DIR / "outputs" / "candidate_predictions.csv"
PP199_CONFIG = PP199_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT205-210"
EXP_SLUG = "PP-OPT205_210_warm_pp204_local_winner_router_refinement"
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
        "item_id": "PP-OPT205",
        "priority": "1",
        "title": "PP204 local threshold/cap refinement",
        "description": "PP204 선택식 주변의 threshold, strength, base cap, risk shrink를 촘촘하게 재탐색.",
    },
    {
        "item_id": "PP-OPT206",
        "priority": "2",
        "title": "p95 guard sensitivity refinement",
        "description": "winner segment p95 손상 감지 기준과 guard 폭을 바꿔 p95 win rate 회복 여부 확인.",
    },
    {
        "item_id": "PP-OPT207",
        "priority": "3",
        "title": "PP192/PP198 gap-aware cap",
        "description": "PP192와 PP198 예측 차이가 큰 row는 이동 강도와 cap을 줄여 tail 손상을 방어.",
    },
    {
        "item_id": "PP-OPT208",
        "priority": "4",
        "title": "confidence-risk asymmetric shrink",
        "description": "저신뢰·고위험 row에서는 PP198 이동을 더 약하게, 고신뢰 row에서는 기존 강도 유지.",
    },
    {
        "item_id": "PP-OPT209",
        "priority": "5",
        "title": "PP204 second-stage residual nudge",
        "description": "PP204를 기준으로 두고 PP198 또는 PP192 방향으로 아주 작은 2차 이동을 적용.",
    },
    {
        "item_id": "PP-OPT210",
        "priority": "6",
        "title": "final PP204 local refinement decision",
        "description": "PP204와 신규 local refinement 후보를 fixed/repeated 기준으로 비교해 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp199 = load_module("pp_opt199_helpers_for_pp205", PP199_SCRIPT)
pp187 = pp199.pp187
pp161 = pp199.pp161
opt8 = pp199.opt8
val71 = pp199.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp199.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp199.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp199.clip_by_row(values, caps)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    return pp187.ape_from_log(base, pred_log)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp199.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(PP199_PREDICTIONS)
    config = json.loads(PP199_CONFIG.read_text(encoding="utf-8"))
    return predictions, config


def choose_support_candidates(config: dict[str, Any]) -> dict[str, str]:
    support = dict(config["support_candidates"])
    decision = config["selection_decision"]
    support.update(
        {
            "pp204_operational": decision["operational_protocol_candidate"],
            "pp204_mape": decision["mape_challenger_protocol_candidate"],
            "pp204_p95_guarded": decision["p95_guarded_protocol_candidate"],
            "pp204_p95_extreme": decision["p95_extreme_protocol_candidate"],
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
        support["pp204_operational"],
        support["pp204_mape"],
        support["pp204_p95_guarded"],
        support["pp204_p95_extreme"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def candidate_from_move(
    base: pd.DataFrame,
    source: np.ndarray,
    target: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray,
    cap: float | np.ndarray,
) -> pd.DataFrame:
    caps = np.full(len(base), cap) if isinstance(cap, (float, int)) else np.asarray(cap, dtype=float)
    pred = source + clip_by_row((target - source) * weight, caps)
    return make_candidate(base, name, family, item_id, pred)


def confidence_flags(base: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    conf = base["confidence_tier"].astype(str).str.lower()
    low = conf.str.contains("low", na=False).astype(float).to_numpy()
    high = conf.str.contains("high", na=False).astype(float).to_numpy()
    return low, high


def price_conf_components(
    base: pd.DataFrame,
    source: np.ndarray,
    target: np.ndarray,
    threshold: float,
    score_width: float,
    p95_threshold: float,
    p95_width: float,
    gain_threshold: float = -0.00008,
    gain_width: float = 0.00030,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    score, p95_delta, mean_gain, count = pp199.segment_win_signal(
        base,
        source,
        target,
        ["stable_price_band", "confidence_tier"],
    )
    score_w = gate(score, threshold, score_width)
    gain_w = gate(mean_gain, gain_threshold, gain_width)
    p95_guard = np.clip(1.0 - gate(p95_delta, p95_threshold, p95_width), 0, 1)
    count_guard = np.where(count > 0, gate(count, 8.0, 8.0), 1.0)
    return score_w * gain_w * p95_guard * count_guard, p95_delta, mean_gain, count


def pp_opt205_local_threshold_cap(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    for threshold in [-0.02, 0.00, 0.04, 0.08, 0.12]:
        for score_width in [0.22, 0.26]:
            base_w, _p95_delta, _mean_gain, _count = price_conf_components(
                base,
                pp192,
                pp198,
                threshold=threshold,
                score_width=score_width,
                p95_threshold=-0.00002,
                p95_width=0.00012,
            )
            for strength in [0.92, 1.00, 1.08, 1.16]:
                for base_cap in [0.0035, 0.0045, 0.0055, 0.0065]:
                    for shrink in [0.65, 0.80, 0.90]:
                        cap = np.clip(base_cap * (1.0 - shrink * risk), 0.0008, base_cap)
                        weight = base_w * strength
                        name = (
                            f"ppopt205_local_price_conf__thr={safe_name(threshold)}__width={safe_name(score_width)}"
                            f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(
                            candidate_from_move(base, pp192, pp198, name, "pp204_local_threshold_cap_refinement", "PP-OPT205", weight, cap)
                        )
    return rows


def pp_opt206_p95_guard_sensitivity(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    for p95_threshold in [-0.00008, -0.00004, -0.00002, 0.00000]:
        for p95_width in [0.00008, 0.00012, 0.00018]:
            base_w, _p95_delta, _mean_gain, _count = price_conf_components(
                base,
                pp192,
                pp198,
                threshold=0.08,
                score_width=0.26,
                p95_threshold=p95_threshold,
                p95_width=p95_width,
            )
            for strength in [0.85, 1.00, 1.10]:
                for base_cap in [0.0040, 0.0055, 0.0070]:
                    for shrink in [0.80, 1.00]:
                        cap = np.clip(base_cap * (1.0 - shrink * risk), 0.0007, base_cap)
                        weight = base_w * strength
                        name = (
                            f"ppopt206_p95_guard_sensitivity__p95thr={safe_name(p95_threshold)}"
                            f"__p95width={safe_name(p95_width)}__s={safe_name(strength)}"
                            f"__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(
                            candidate_from_move(base, pp192, pp198, name, "pp204_p95_guard_sensitivity_refinement", "PP-OPT206", weight, cap)
                        )
    return rows


def pp_opt207_gap_aware_cap(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    gap_abs = np.abs(pp198 - pp192)
    base_w, _p95_delta, _mean_gain, _count = price_conf_components(
        base,
        pp192,
        pp198,
        threshold=0.08,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    for gap_threshold in [0.003, 0.006, 0.010, 0.014]:
        for gap_width in [0.003, 0.006]:
            gap_guard = np.clip(1.0 - gate(gap_abs, gap_threshold, gap_width), 0, 1)
            for strength in [0.95, 1.05]:
                for base_cap in [0.0050, 0.0065]:
                    for shrink in [0.80, 0.95]:
                        cap = np.clip(base_cap * (1.0 - shrink * risk) * (0.65 + 0.35 * gap_guard), 0.0007, base_cap)
                        weight = base_w * strength * (0.75 + 0.25 * gap_guard)
                        name = (
                            f"ppopt207_gap_aware_cap__gapthr={safe_name(gap_threshold)}__gapwidth={safe_name(gap_width)}"
                            f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(candidate_from_move(base, pp192, pp198, name, "pp204_gap_aware_cap_refinement", "PP-OPT207", weight, cap))
    return rows


def pp_opt208_confidence_risk_shrink(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    low_conf, high_conf = confidence_flags(base)
    base_w, _p95_delta, _mean_gain, _count = price_conf_components(
        base,
        pp192,
        pp198,
        threshold=0.08,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    for low_share in [0.35, 0.55, 0.75]:
        for high_share in [1.00, 1.08]:
            confidence_scale = np.clip((1.0 - low_conf) + low_conf * low_share + high_conf * (high_share - 1.0), 0.25, 1.15)
            for risk_threshold in [0.50, 0.60]:
                high_risk_guard = np.clip(1.0 - gate(risk, risk_threshold, 0.22), 0, 1)
                for strength in [0.95, 1.05]:
                    for base_cap in [0.0045, 0.0060]:
                        cap = np.clip(base_cap * (0.70 + 0.30 * high_risk_guard) * confidence_scale, 0.0008, base_cap)
                        weight = base_w * strength * confidence_scale
                        name = (
                            f"ppopt208_conf_risk_shrink__lowshare={safe_name(low_share)}__highshare={safe_name(high_share)}"
                            f"__riskthr={safe_name(risk_threshold)}__s={safe_name(strength)}__basecap={safe_name(base_cap)}"
                        )
                        rows.append(
                            candidate_from_move(base, pp192, pp198, name, "pp204_confidence_risk_shrink_refinement", "PP-OPT208", weight, cap)
                        )
    return rows


def pp_opt209_second_stage_nudge(
    base: pd.DataFrame,
    pp192: np.ndarray,
    pp198: np.ndarray,
    pp204: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk_198 = pp199.row_risk(base, pp192, pp198)
    toward_198_w, _p95_delta, _mean_gain, _count = price_conf_components(
        base,
        pp204,
        pp198,
        threshold=0.00,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    toward_192_w, _p95_delta2, _mean_gain2, _count2 = price_conf_components(
        base,
        pp204,
        pp192,
        threshold=0.00,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    for direction, target, base_w in [
        ("toward_pp198", pp198, toward_198_w),
        ("rollback_pp192", pp192, toward_192_w),
    ]:
        for strength in [0.20, 0.35, 0.50]:
            for cap_base in [0.0008, 0.0012, 0.0018]:
                for shrink in [0.50, 0.80]:
                    cap = np.clip(cap_base * (1.0 - shrink * risk_198), 0.0003, cap_base)
                    name = (
                        f"ppopt209_second_stage_nudge__dir={direction}__s={safe_name(strength)}"
                        f"__cap={safe_name(cap_base)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(candidate_from_move(base, pp204, target, name, "pp204_second_stage_residual_nudge", "PP-OPT209", base_w * strength, cap))
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
        support["pp204_operational"],
        support["pp204_mape"],
        support["pp204_p95_guarded"],
        support["pp204_p95_extreme"],
    ]
    pp204 = metrics[metrics["candidate"].eq(support["pp204_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp204_mape = float(pp204["MAPE"])
    pp204_p95 = float(pp204["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= pp204_mape + 0.000010)
        & (new_pool["test_p95_APE"] <= pp204_p95 + 0.000006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(120)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= pp204_p95 + 0.000006].sort_values(["test_MAPE", "test_p95_APE"]).head(120)
    p95_pool = new_pool[
        (new_pool["test_MAPE"] <= pp204_mape + 0.000060)
        & (new_pool["test_p95_APE"] <= pp204_p95 + 0.000002)
    ].sort_values(["test_p95_APE", "test_MAPE"]).head(80)
    stability_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(100)
    selected = pd.concat([op_pool, mape_pool, p95_pool, stability_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
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
        support["pp204_operational"]: "pp204_operational_reference",
        support["pp204_mape"]: "pp204_mape_reference",
        support["pp204_p95_guarded"]: "pp204_p95_guarded_reference",
        support["pp204_p95_extreme"]: "pp204_p95_extreme_reference",
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
    pp204 = row_by_candidate(stability, support["pp204_operational"])
    pp204_guard = row_by_candidate(stability, support["pp204_p95_guarded"])
    pp198 = row_by_candidate(stability, support["pp198_operational"])
    pp192 = row_by_candidate(stability, support["pp192_operational"])
    pp186 = row_by_candidate(stability, support["pp186_operational"])
    pp172 = row_by_candidate(stability, support["pp172_operational"])
    pp166 = row_by_candidate(stability, support["pp166_operational"])
    pp148 = row_by_candidate(stability, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt20", regex=True)].copy()
    pp204_mape = float(pp204["fixed_test_MAPE"])
    pp204_p95 = float(pp204["fixed_test_p95_APE"])

    operational = pp204.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= pp204_mape + 0.000002)
        & (pool["fixed_test_p95_APE"] <= pp204_p95 + 0.000004)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp204["avg_pp64_MAPE_win_rate"]) - 0.0010)
        & (pool["replacement_score"] <= float(pp204["replacement_score"]) + 0.000002)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    mape_challenger = pp204.copy()
    mape_pool = pool[(pool["fixed_test_p95_APE"] <= pp204_p95 + 0.000004)].copy()
    if not mape_pool.empty:
        mape_challenger = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score", "fixed_test_p95_APE"]).iloc[0]

    p95_guarded = pp204_guard.copy()
    p95_pool = pool[
        (pool["fixed_test_p95_APE"] <= pp204_p95 + 0.000002)
        & (pool["fixed_test_MAPE"] <= pp204_mape + 0.000060)
    ].copy()
    if not p95_pool.empty:
        p95_guarded = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

    p95_extreme_pool = stability[
        (stability["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_extreme_pool = p95_extreme_pool[
        p95_extreme_pool["candidate"].astype(str).str.contains(
            "reference_pp148_p95|pp166_p95|pp172_p95|pp180_p95|pp186_p95|pp192_p95|pp198_p95|pp204_p95|ppopt20",
            regex=True,
        )
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
            f"{prefix}_delta_vs_pp186_MAPE": float(row["fixed_test_MAPE"]) - float(pp186["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp186_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp186["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp192_MAPE": float(row["fixed_test_MAPE"]) - float(pp192["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp192_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp192["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp198_MAPE": float(row["fixed_test_MAPE"]) - float(pp198["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp198_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp198["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp204_MAPE": float(row["fixed_test_MAPE"]) - pp204_mape,
            f"{prefix}_delta_vs_pp204_p95_APE": float(row["fixed_test_p95_APE"]) - pp204_p95,
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
        ("operational", "pp204_local_refinement_operational_selection"),
        ("mape_challenger", "pp204_local_refinement_mape_selection"),
        ("p95_guarded", "pp204_local_refinement_p95_guarded_selection"),
        ("p95_extreme", "pp204_local_refinement_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt210_{key}_pp204_local_refinement__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT210"
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
        support["pp204_operational"],
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
        f"PP204 대비 MAPE {decision['operational_delta_vs_pp204_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp204_p95_APE']:+.6f}, "
        f"replacement score {decision['operational_replacement_score']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT205~210 Warm PP204 local winner-router refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP204 winner-router 주변의 threshold/cap/shrink를 세밀하게 조정해 추가 개선 여부 확인",
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
<title>PP-OPT205~210 Warm PP204 local winner-router refinement 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT205~210 Warm PP204 local winner-router refinement 결과</h1>
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
    pp204 = pp187.prediction_array(previous, feature_base, support["pp204_operational"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt205_local_threshold_cap(feature_base, pp192, pp198))
    candidates.extend(pp_opt206_p95_guard_sensitivity(feature_base, pp192, pp198))
    candidates.extend(pp_opt207_gap_aware_cap(feature_base, pp192, pp198))
    candidates.extend(pp_opt208_confidence_risk_shrink(feature_base, pp192, pp198))
    candidates.extend(pp_opt209_second_stage_nudge(feature_base, pp192, pp198, pp204))

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
    label_map[decision["operational_protocol_candidate"]] = "pp210_operational_pp204_local_refinement_challenger"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp210_mape_pp204_local_refinement_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp210_p95_guarded_pp204_local_refinement_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp210_p95_extreme_pp204_local_refinement_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    price_conf_w, price_conf_p95, price_conf_gain, price_conf_count = price_conf_components(
        feature_base,
        pp192,
        pp198,
        threshold=0.08,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    pp204_vs_198_w, pp204_vs_198_p95, pp204_vs_198_gain, pp204_vs_198_count = price_conf_components(
        feature_base,
        pp204,
        pp198,
        threshold=0.00,
        score_width=0.26,
        p95_threshold=-0.00002,
        p95_width=0.00012,
    )
    feature_frame = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    feature_frame["pp192_log"] = pp192
    feature_frame["pp198_log"] = pp198
    feature_frame["pp204_log"] = pp204
    feature_frame["pp192_pp198_gap_abs"] = np.abs(pp198 - pp192)
    feature_frame["pp204_pp198_gap_abs"] = np.abs(pp198 - pp204)
    feature_frame["row_risk"] = pp199.row_risk(feature_base, pp192, pp198)
    feature_frame["price_conf_weight_default"] = price_conf_w
    feature_frame["price_conf_p95_delta"] = price_conf_p95
    feature_frame["price_conf_mean_gain"] = price_conf_gain
    feature_frame["price_conf_val_count"] = price_conf_count
    feature_frame["pp204_vs_198_weight"] = pp204_vs_198_w
    feature_frame["pp204_vs_198_p95_delta"] = pp204_vs_198_p95
    feature_frame["pp204_vs_198_mean_gain"] = pp204_vs_198_gain
    feature_frame["pp204_vs_198_val_count"] = pp204_vs_198_count

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP199_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP192 operational log price, or PP204 operational log price for second-stage nudge",
            "mape_candidate": "PP198 MAPE challenger log price",
            "main_final": "PP192 log price + clip((PP198 log price - PP192 log price) * winner_weight, tuned row_cap)",
            "second_stage_final": "PP204 log price + clip((target log price - PP204 log price) * second_stage_weight, tiny row_cap)",
            "winner_inputs": [
                "validation stable_price_band x confidence_tier PP198-vs-PP192 APE gain",
                "validation segment PP198-vs-PP192 p95 delta",
                "row uncertainty risk",
                "abs(PP198 log price - PP192 log price)",
                "confidence tier asymmetric shrink",
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
    feature_frame.to_csv(ARTIFACT_DIR / "local_winner_router_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp204_local_winner_router_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp204_local_winner_router_refinement_result.html").write_text(report_html, encoding="utf-8")

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
