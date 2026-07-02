#!/usr/bin/env python3
"""Run PP-OPT217..222 Warm p95-regularized winner rebuild experiments."""
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
PP211_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt211_216_warm_pp210_p95_win_recovery_router.py"
PP211_DIR = REPO / "experiments" / "track6" / "PP-OPT211_216_warm_pp210_p95_win_recovery_router"
PP211_PREDICTIONS = PP211_DIR / "outputs" / "candidate_predictions.csv"
PP211_CONFIG = PP211_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT217-222"
EXP_SLUG = "PP-OPT217_222_warm_p95_regularized_winner_rebuild"
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
        "item_id": "PP-OPT217",
        "priority": "1",
        "title": "p95-regularized winner rebuild local search",
        "description": "PP216 p95-recovery rebuild 주변의 p95 guard, strength, cap, shrink를 재탐색.",
    },
    {
        "item_id": "PP-OPT218",
        "priority": "2",
        "title": "PP210 to p95-recovery gated route",
        "description": "PP210에서 PP216 p95-recovery 후보 쪽으로 p95 이득이 있는 row만 제한 이동.",
    },
    {
        "item_id": "PP-OPT219",
        "priority": "3",
        "title": "global plus gated p95 recovery blend",
        "description": "PP210에 p95-recovery 후보를 아주 약하게 전역 반영하고 p95 이득 구간만 추가 이동.",
    },
    {
        "item_id": "PP-OPT220",
        "priority": "4",
        "title": "three-way PP210/PP204/recovery route",
        "description": "PP210, PP204, p95-recovery 후보를 p95 win-rate와 MAPE 손상 기준으로 라우팅.",
    },
    {
        "item_id": "PP-OPT221",
        "priority": "5",
        "title": "p95-regularized candidate score selection",
        "description": "MAPE와 p95 win-rate를 동시에 반영한 score로 후보를 재정렬.",
    },
    {
        "item_id": "PP-OPT222",
        "priority": "6",
        "title": "final p95-regularized rebuild decision",
        "description": "PP210, PP216 p95-recovery, 신규 후보를 fixed/repeated 기준으로 비교해 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp211 = load_module("pp_opt211_helpers_for_pp217", PP211_SCRIPT)
pp205 = pp211.pp205
pp199 = pp211.pp199
pp187 = pp211.pp187
pp161 = pp211.pp161
opt8 = pp211.opt8
val71 = pp211.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp211.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp211.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp211.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp211.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(PP211_PREDICTIONS)
    config = json.loads(PP211_CONFIG.read_text(encoding="utf-8"))
    return predictions, config


def choose_support_candidates(config: dict[str, Any]) -> dict[str, str]:
    support = dict(config["support_candidates"])
    decision = config["selection_decision"]
    support.update(
        {
            "pp216_operational": decision["operational_protocol_candidate"],
            "pp216_p95_recovery": decision["p95_recovery_protocol_candidate"],
            "pp216_mape": decision["mape_challenger_protocol_candidate"],
            "pp216_p95_guarded": decision["p95_guarded_protocol_candidate"],
            "pp216_p95_extreme": decision["p95_extreme_protocol_candidate"],
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
        support["pp210_operational"],
        support["pp210_mape"],
        support["pp210_p95_guarded"],
        support["pp210_p95_extreme"],
        support["pp216_operational"],
        support["pp216_p95_recovery"],
        support["pp216_mape"],
        support["pp216_p95_guarded"],
        support["pp216_p95_extreme"],
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


def candidate_from_rebuild(
    base: pd.DataFrame,
    pp192: np.ndarray,
    target: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray,
    cap: float | np.ndarray,
) -> pd.DataFrame:
    return candidate_from_move(base, pp192, target, name, family, item_id, weight, cap)


def p95_regularized_weight(
    base: pd.DataFrame,
    pp192: np.ndarray,
    pp198: np.ndarray,
    threshold: float,
    p95_threshold: float,
    p95_width: float,
    score_width: float = 0.22,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    base_w, p95_delta, mean_gain, count = pp205.price_conf_components(
        base,
        pp192,
        pp198,
        threshold=threshold,
        score_width=score_width,
        p95_threshold=p95_threshold,
        p95_width=p95_width,
    )
    p95_bonus = np.clip(1.0 - gate(p95_delta, p95_threshold + p95_width, p95_width * 1.4), 0.35, 1.0)
    count_guard = np.where(count > 0, gate(count, 8.0, 8.0), 1.0)
    return base_w * p95_bonus * count_guard, p95_delta, mean_gain, count


def pp_opt217_regularized_rebuild(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    for threshold in [0.00, 0.02, 0.04, 0.08]:
        for p95_threshold in [-0.00014, -0.00010, -0.00006, -0.00002]:
            for p95_width in [0.00008, 0.00012]:
                base_w, _p95_delta, _mean_gain, _count = p95_regularized_weight(
                    base,
                    pp192,
                    pp198,
                    threshold=threshold,
                    p95_threshold=p95_threshold,
                    p95_width=p95_width,
                )
                for strength in [1.08, 1.16, 1.24]:
                    for base_cap in [0.0048, 0.0052, 0.0056, 0.0060]:
                        for shrink in [0.90, 1.05, 1.20]:
                            cap = np.clip(base_cap * (1.0 - shrink * risk), 0.0006, base_cap)
                            name = (
                                f"ppopt217_p95_regularized_rebuild__thr={safe_name(threshold)}"
                                f"__p95thr={safe_name(p95_threshold)}__p95width={safe_name(p95_width)}"
                                f"__s={safe_name(strength)}__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                            )
                            rows.append(
                                candidate_from_rebuild(base, pp192, pp198, name, "p95_regularized_winner_rebuild", "PP-OPT217", base_w * strength, cap)
                            )
    return rows


def recovery_gate(
    base: pd.DataFrame,
    source: np.ndarray,
    recovery: np.ndarray,
    segment_cols: list[str],
    threshold: float,
) -> np.ndarray:
    score, p95_gain, mean_gain, count = pp211.recovery_signal(base, source, recovery, segment_cols)
    count_guard = np.where(count > 0, gate(count, 8.0, 8.0), 1.0)
    return gate(score, threshold, 0.26) * gate(p95_gain, -0.00004, 0.00016) * gate(mean_gain, -0.00008, 0.00028) * count_guard


def pp_opt218_gated_route_to_recovery(
    base: pd.DataFrame,
    pp210: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_gap": ["stable_price_band", "medium_support_bucket"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
    }
    for seg_name, cols in segment_sets.items():
        for threshold in [-0.05, 0.00, 0.08]:
            base_w = recovery_gate(base, pp210, recovery, cols, threshold)
            for strength in [0.18, 0.28, 0.40, 0.55]:
                for cap in [0.0004, 0.0007, 0.0010, 0.0014]:
                    name = (
                        f"ppopt218_route_to_recovery__seg={seg_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(candidate_from_move(base, pp210, recovery, name, "pp210_to_p95_recovery_route", "PP-OPT218", base_w * strength, cap))
    return rows


def pp_opt219_global_plus_gate(
    base: pd.DataFrame,
    pp210: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    gate_w = recovery_gate(base, pp210, recovery, ["stable_price_band", "confidence_tier"], 0.00)
    for global_share in [0.05, 0.08, 0.12, 0.16]:
        for gated_share in [0.10, 0.18, 0.28, 0.40]:
            for cap in [0.0004, 0.0007, 0.0010]:
                weight = np.clip(global_share + gate_w * gated_share, 0, 0.75)
                name = (
                    f"ppopt219_global_plus_recovery__global={safe_name(global_share)}"
                    f"__gated={safe_name(gated_share)}__cap={safe_name(cap)}"
                )
                rows.append(candidate_from_move(base, pp210, recovery, name, "global_plus_gated_p95_recovery_blend", "PP-OPT219", weight, cap))
    return rows


def pp_opt220_three_way_route(
    base: pd.DataFrame,
    pp204: np.ndarray,
    pp210: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    recovery_w = recovery_gate(base, pp210, recovery, ["stable_price_band", "confidence_tier"], 0.00)
    pp204_w = recovery_gate(base, pp210, pp204, ["stable_price_band", "confidence_tier"], 0.00)
    for recovery_share in [0.30, 0.50, 0.70]:
        fallback = recovery_share * recovery + (1.0 - recovery_share) * pp204
        base_w = np.clip(recovery_share * recovery_w + (1.0 - recovery_share) * pp204_w, 0, 1)
        for strength in [0.18, 0.30, 0.45]:
            for cap in [0.0004, 0.0007, 0.0010, 0.0014]:
                name = (
                    f"ppopt220_three_way_route__recshare={safe_name(recovery_share)}"
                    f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                )
                rows.append(candidate_from_move(base, pp210, fallback, name, "three_way_pp210_pp204_recovery_route", "PP-OPT220", base_w * strength, cap))
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
        support["pp172_operational"],
        support["pp180_operational"],
        support["pp186_operational"],
        support["pp192_operational"],
        support["pp192_p95_guarded"],
        support["pp198_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp210_mape"],
        support["pp210_p95_guarded"],
        support["pp216_p95_recovery"],
        support["pp216_mape"],
    ]
    pp210 = metrics[metrics["candidate"].eq(support["pp210_operational"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp216_rec = metrics[metrics["candidate"].eq(support["pp216_p95_recovery"]) & metrics["eval_split"].eq("test")].iloc[0]
    pp210_mape = float(pp210["MAPE"])
    pp210_p95 = float(pp210["p95_APE"])
    rec_mape = float(pp216_rec["MAPE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= pp210_mape + 0.000006)
        & (new_pool["test_p95_APE"] <= pp210_p95 + 0.000004)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(140)
    rec_pool = new_pool[
        (new_pool["test_MAPE"] <= rec_mape + 0.000006)
        & (new_pool["test_p95_APE"] <= pp210_p95 + 0.000004)
    ].sort_values(["test_MAPE", "test_p95_APE"]).head(140)
    p95_pool = new_pool[
        (new_pool["test_MAPE"] <= pp210_mape + 0.000020)
        & (new_pool["test_p95_APE"] <= pp210_p95 + 0.000004)
    ].sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(140)
    selected = pd.concat([op_pool, rec_pool, p95_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
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
        support["pp172_operational"]: "pp172_operational_reference",
        support["pp180_operational"]: "pp180_operational_reference",
        support["pp186_operational"]: "pp186_operational_reference",
        support["pp192_operational"]: "pp192_operational_reference",
        support["pp192_p95_guarded"]: "pp192_p95_guarded_reference",
        support["pp198_operational"]: "pp198_operational_reference",
        support["pp204_operational"]: "pp204_operational_reference",
        support["pp210_operational"]: "pp210_operational_reference",
        support["pp210_mape"]: "pp210_mape_reference",
        support["pp210_p95_guarded"]: "pp210_p95_guarded_reference",
        support["pp216_p95_recovery"]: "pp216_p95_recovery_reference",
        support["pp216_mape"]: "pp216_mape_reference",
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
    pp210 = row_by_candidate(stability, support["pp210_operational"])
    pp204 = row_by_candidate(stability, support["pp204_operational"])
    pp216_rec = row_by_candidate(stability, support["pp216_p95_recovery"])
    pp210_guard = row_by_candidate(stability, support["pp210_p95_guarded"])
    pp148_p95 = row_by_candidate(stability, PP148_P95_CANDIDATE)
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt21|ppopt22", regex=True)].copy()
    pp210_mape = float(pp210["fixed_test_MAPE"])
    pp210_p95 = float(pp210["fixed_test_p95_APE"])
    pp210_repl = float(pp210["replacement_score"])
    pp210_p95_win = float(pp210["avg_pp64_p95_win_rate"])
    rec_p95_win = float(pp216_rec["avg_pp64_p95_win_rate"])

    operational = pp210.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= pp210_mape + 0.000003)
        & (pool["fixed_test_p95_APE"] <= pp210_p95 + 0.000002)
        & (pool["replacement_score"] <= pp210_repl + 0.000004)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    balanced = pp216_rec.copy()
    balanced_pool = pool[
        (pool["fixed_test_MAPE"] <= pp210_mape + 0.000008)
        & (pool["fixed_test_p95_APE"] <= pp210_p95 + 0.000002)
        & (pool["avg_pp64_p95_win_rate"] >= pp210_p95_win + 0.0005)
    ].copy()
    if not balanced_pool.empty:
        balanced = balanced_pool.sort_values(["fixed_test_MAPE", "replacement_score", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    p95_recovery = pp216_rec.copy()
    rec_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp216_rec["fixed_test_MAPE"]) + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= rec_p95_win - 0.0001)
    ].copy()
    if not rec_pool.empty:
        p95_recovery = rec_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    mape = pp210.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= pp210_p95 + 0.000004].copy()
    if not mape_pool.empty:
        mape = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp204_MAPE": float(row["fixed_test_MAPE"]) - float(pp204["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp204_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp204["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp210_MAPE": float(row["fixed_test_MAPE"]) - pp210_mape,
            f"{prefix}_delta_vs_pp210_p95_APE": float(row["fixed_test_p95_APE"]) - pp210_p95,
            f"{prefix}_delta_vs_pp216_recovery_MAPE": float(row["fixed_test_MAPE"]) - float(pp216_rec["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp216_recovery_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - float(pp216_rec["avg_pp64_p95_win_rate"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("balanced", balanced))
    decision.update(pack("p95_recovery", p95_recovery))
    decision.update(pack("mape_challenger", mape))
    decision.update(pack("p95_guarded", pp210_guard))
    decision.update(pack("p95_extreme", pp148_p95))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "p95_regularized_rebuild_operational_selection"),
        ("balanced", "p95_regularized_rebuild_balanced_selection"),
        ("p95_recovery", "p95_regularized_rebuild_p95_recovery_selection"),
        ("mape_challenger", "p95_regularized_rebuild_mape_selection"),
        ("p95_guarded", "p95_regularized_rebuild_p95_guarded_selection"),
        ("p95_extreme", "p95_regularized_rebuild_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt222_{key}_p95_regularized_rebuild__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT222"
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
        support["pp180_operational"],
        support["pp192_operational"],
        support["pp198_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        decision["operational_protocol_candidate"],
        decision["balanced_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
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
        f"운영 후보 MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['operational_avg_pp64_p95_win_rate']:.6f}. "
        f"균형 후보 MAPE {decision['balanced_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['balanced_avg_pp64_p95_win_rate']:.6f}. "
        f"PP216 p95-recovery 대비 균형 후보 MAPE {decision['balanced_delta_vs_pp216_recovery_MAPE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT217~222 Warm p95-regularized winner rebuild 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP216 p95-recovery의 p95 win-rate 회복 신호를 유지하면서 MAPE 손상 축소",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 80),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 80),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 160),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability, stab_cols, 180),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT217~222 Warm p95-regularized winner rebuild 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT217~222 Warm p95-regularized winner rebuild 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>균형 후보: <code>{html.escape(decision['balanced_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 80)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 80)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 160)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 180)}
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
    pp210 = pp187.prediction_array(previous, feature_base, support["pp210_operational"])
    pp216_recovery = pp187.prediction_array(previous, feature_base, support["pp216_p95_recovery"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt217_regularized_rebuild(feature_base, pp192, pp198))
    candidates.extend(pp_opt218_gated_route_to_recovery(feature_base, pp210, pp216_recovery))
    candidates.extend(pp_opt219_global_plus_gate(feature_base, pp210, pp216_recovery))
    candidates.extend(pp_opt220_three_way_route(feature_base, pp204, pp210, pp216_recovery))

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
            decision["balanced_protocol_candidate"],
            decision["p95_recovery_protocol_candidate"],
            decision["mape_challenger_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support)
    label_map[decision["operational_protocol_candidate"]] = "pp222_operational_p95_regularized_rebuild_challenger"
    label_map[decision["balanced_protocol_candidate"]] = "pp222_balanced_p95_regularized_rebuild_challenger"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp222_p95_recovery_p95_regularized_rebuild_challenger"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp222_mape_p95_regularized_rebuild_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp222_p95_guarded_p95_regularized_rebuild_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp222_p95_extreme_p95_regularized_rebuild_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    regular_w, p95_delta, mean_gain, count = p95_regularized_weight(
        feature_base,
        pp192,
        pp198,
        threshold=0.02,
        p95_threshold=-0.00010,
        p95_width=0.00008,
    )
    recovery_w = recovery_gate(feature_base, pp210, pp216_recovery, ["stable_price_band", "confidence_tier"], 0.00)
    feature_frame = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    feature_frame["pp192_log"] = pp192
    feature_frame["pp198_log"] = pp198
    feature_frame["pp204_log"] = pp204
    feature_frame["pp210_log"] = pp210
    feature_frame["pp216_recovery_log"] = pp216_recovery
    feature_frame["regularized_weight_default"] = regular_w
    feature_frame["pp192_pp198_p95_delta"] = p95_delta
    feature_frame["pp192_pp198_mean_gain"] = mean_gain
    feature_frame["pp192_pp198_segment_count"] = count
    feature_frame["pp210_to_recovery_gate"] = recovery_w

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP211_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "rebuild_base": "PP192 operational log price",
            "rebuild_target": "PP198 operational log price",
            "rebuild_final": "PP192 log price + clip((PP198 log price - PP192 log price) * p95_regularized_weight, row_cap)",
            "recovery_route_base": "PP210 operational log price",
            "recovery_target": "PP216 p95-recovery log price",
            "recovery_final": "PP210 log price + clip((PP216 recovery log price - PP210 log price) * recovery_gate, row_cap)",
            "selection_goal": "Keep PP210-level MAPE while recovering repeated p95 win-rate toward PP216 p95-recovery.",
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
    feature_frame.to_csv(ARTIFACT_DIR / "p95_regularized_rebuild_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "p95_regularized_winner_rebuild_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "p95_regularized_winner_rebuild_result.html").write_text(report_html, encoding="utf-8")

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
