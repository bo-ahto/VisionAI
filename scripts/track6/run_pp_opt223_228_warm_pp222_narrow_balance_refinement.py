#!/usr/bin/env python3
"""Run PP-OPT223..228 Warm PP222 narrow balance refinement experiments."""
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
PP217_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt217_222_warm_p95_regularized_winner_rebuild.py"
PP217_DIR = REPO / "experiments" / "track6" / "PP-OPT217_222_warm_p95_regularized_winner_rebuild"
PP217_PREDICTIONS = PP217_DIR / "outputs" / "candidate_predictions.csv"
PP217_CONFIG = PP217_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT223-228"
EXP_SLUG = "PP-OPT223_228_warm_pp222_narrow_balance_refinement"
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
        "item_id": "PP-OPT223",
        "priority": "1",
        "title": "PP222 balanced neighborhood search",
        "description": "PP222 균형 후보 주변의 threshold, p95 guard, strength, cap, shrink를 좁게 재탐색.",
    },
    {
        "item_id": "PP-OPT224",
        "priority": "2",
        "title": "risk-shaped cap refinement",
        "description": "동일 weight에서 row risk별 cap 곡선을 조정해 p95 win rate를 유지하며 MAPE를 낮춤.",
    },
    {
        "item_id": "PP-OPT225",
        "priority": "3",
        "title": "balanced-to-aggressive micro blend",
        "description": "PP222 균형 후보에서 공격형 MAPE 후보로 아주 작게 이동.",
    },
    {
        "item_id": "PP-OPT226",
        "priority": "4",
        "title": "balanced-to-recovery p95 support blend",
        "description": "p95 win rate 회복 신호가 있는 row만 PP216 p95-recovery 후보 쪽으로 미세 이동.",
    },
    {
        "item_id": "PP-OPT227",
        "priority": "5",
        "title": "candidate score selection",
        "description": "MAPE, replacement, p95 win rate 하한을 같이 적용해 후보를 재선택.",
    },
    {
        "item_id": "PP-OPT228",
        "priority": "6",
        "title": "final PP222 narrow balance decision",
        "description": "PP222 균형/공격형 후보와 신규 후보를 fixed/repeated 기준으로 비교해 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp217 = load_module("pp_opt217_helpers_for_pp223", PP217_SCRIPT)
pp211 = pp217.pp211
pp205 = pp217.pp205
pp199 = pp217.pp199
pp187 = pp217.pp187
pp161 = pp217.pp161
opt8 = pp217.opt8
val71 = pp217.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp217.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp217.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp217.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp217.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    return pd.read_csv(PP217_PREDICTIONS), json.loads(PP217_CONFIG.read_text(encoding="utf-8"))


def choose_support_candidates(config: dict[str, Any]) -> dict[str, str]:
    support = dict(config["support_candidates"])
    decision = config["selection_decision"]
    support.update(
        {
            "pp222_operational": decision["operational_protocol_candidate"],
            "pp222_balanced": decision["balanced_protocol_candidate"],
            "pp222_p95_recovery": decision["p95_recovery_protocol_candidate"],
            "pp222_mape": decision["mape_challenger_protocol_candidate"],
            "pp222_p95_guarded": decision["p95_guarded_protocol_candidate"],
            "pp222_p95_extreme": decision["p95_extreme_protocol_candidate"],
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
        support["pp222_operational"],
        support["pp222_balanced"],
        support["pp222_p95_recovery"],
        support["pp222_mape"],
        support["pp222_p95_guarded"],
        support["pp222_p95_extreme"],
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


def rebuild_candidate(
    base: pd.DataFrame,
    pp192: np.ndarray,
    pp198: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray,
    cap: float | np.ndarray,
) -> pd.DataFrame:
    return candidate_from_move(base, pp192, pp198, name, family, item_id, weight, cap)


def pp_opt223_neighborhood(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    for threshold in [0.015, 0.020, 0.025]:
        for p95_threshold in [-0.00016, -0.00014, -0.00012]:
            for p95_width in [0.00010, 0.00012]:
                base_w, _p95_delta, _mean_gain, _count = pp217.p95_regularized_weight(
                    base,
                    pp192,
                    pp198,
                    threshold=threshold,
                    p95_threshold=p95_threshold,
                    p95_width=p95_width,
                    score_width=0.22,
                )
                for strength in [1.22, 1.24, 1.26]:
                    for basecap in [0.00515, 0.00525, 0.00535, 0.00545]:
                        for shrink in [0.88, 0.90, 0.92, 0.94]:
                            cap = np.clip(basecap * (1.0 - shrink * risk), 0.0006, basecap)
                            name = (
                                f"ppopt223_neighborhood__thr={safe_name(threshold)}__p95thr={safe_name(p95_threshold)}"
                                f"__p95width={safe_name(p95_width)}__s={safe_name(strength)}"
                                f"__basecap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                            )
                            rows.append(rebuild_candidate(base, pp192, pp198, name, "pp222_balanced_neighborhood_search", "PP-OPT223", base_w * strength, cap))
    return rows


def pp_opt224_risk_shaped_cap(base: pd.DataFrame, pp192: np.ndarray, pp198: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    risk = pp199.row_risk(base, pp192, pp198)
    base_w, _p95_delta, _mean_gain, _count = pp217.p95_regularized_weight(
        base,
        pp192,
        pp198,
        threshold=0.02,
        p95_threshold=-0.00014,
        p95_width=0.00012,
        score_width=0.22,
    )
    for curve in [0.75, 1.00, 1.25]:
        shaped_risk = np.power(np.clip(risk, 0, 1), curve)
        for strength in [1.22, 1.24, 1.26]:
            for basecap in [0.0052, 0.0053, 0.0054]:
                for shrink in [0.86, 0.90, 0.94]:
                    cap = np.clip(basecap * (1.0 - shrink * shaped_risk), 0.00055, basecap)
                    name = (
                        f"ppopt224_risk_shaped_cap__curve={safe_name(curve)}__s={safe_name(strength)}"
                        f"__basecap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(rebuild_candidate(base, pp192, pp198, name, "pp222_risk_shaped_cap_refinement", "PP-OPT224", base_w * strength, cap))
    return rows


def recovery_gate(base: pd.DataFrame, source: np.ndarray, recovery: np.ndarray) -> np.ndarray:
    score, p95_gain, mean_gain, count = pp211.recovery_signal(base, source, recovery, ["stable_price_band", "confidence_tier"])
    count_guard = np.where(count > 0, gate(count, 8.0, 8.0), 1.0)
    return gate(score, 0.0, 0.26) * gate(p95_gain, -0.00004, 0.00016) * gate(mean_gain, -0.00008, 0.00028) * count_guard


def pp_opt225_micro_blend(base: pd.DataFrame, balanced: np.ndarray, aggressive: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for share in [0.20, 0.35, 0.50, 0.65, 0.80]:
        for cap in [0.00025, 0.00040, 0.00060, 0.00080]:
            weight = np.full(len(base), share, dtype=float)
            name = f"ppopt225_balanced_to_aggressive__share={safe_name(share)}__cap={safe_name(cap)}"
            rows.append(candidate_from_move(base, balanced, aggressive, name, "pp222_balanced_to_aggressive_micro_blend", "PP-OPT225", weight, cap))
    return rows


def pp_opt226_recovery_support(base: pd.DataFrame, balanced: np.ndarray, recovery: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    gate_w = recovery_gate(base, balanced, recovery)
    for strength in [0.10, 0.18, 0.28, 0.40]:
        for cap in [0.00025, 0.00040, 0.00060]:
            name = f"ppopt226_recovery_support__s={safe_name(strength)}__cap={safe_name(cap)}"
            rows.append(candidate_from_move(base, balanced, recovery, name, "pp222_balanced_to_recovery_support", "PP-OPT226", gate_w * strength, cap))
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
        support["pp180_operational"],
        support["pp192_operational"],
        support["pp198_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_operational"],
        support["pp222_balanced"],
        support["pp222_mape"],
        support["pp222_p95_guarded"],
    ]
    pp222_bal = metrics[metrics["candidate"].eq(support["pp222_balanced"]) & metrics["eval_split"].eq("test")].iloc[0]
    bal_mape = float(pp222_bal["MAPE"])
    bal_p95 = float(pp222_bal["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= bal_mape + 0.000004)
        & (new_pool["test_p95_APE"] <= bal_p95 + 0.000004)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(140)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= bal_p95 + 0.000004].sort_values(["test_MAPE", "test_p95_APE"]).head(120)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(120)
    selected = pd.concat([op_pool, mape_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
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
        support["pp180_operational"]: "pp180_operational_reference",
        support["pp192_operational"]: "pp192_operational_reference",
        support["pp198_operational"]: "pp198_operational_reference",
        support["pp204_operational"]: "pp204_operational_reference",
        support["pp210_operational"]: "pp210_operational_reference",
        support["pp216_p95_recovery"]: "pp216_p95_recovery_reference",
        support["pp222_operational"]: "pp222_aggressive_reference",
        support["pp222_balanced"]: "pp222_balanced_reference",
        support["pp222_mape"]: "pp222_mape_reference",
        support["pp222_p95_guarded"]: "pp222_p95_guarded_reference",
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
    balanced_ref = row_by_candidate(stability, support["pp222_balanced"])
    aggressive_ref = row_by_candidate(stability, support["pp222_operational"])
    p95_guard = row_by_candidate(stability, support["pp222_p95_guarded"])
    p95_extreme = row_by_candidate(stability, PP148_P95_CANDIDATE)
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    bal_mape = float(balanced_ref["fixed_test_MAPE"])
    bal_p95 = float(balanced_ref["fixed_test_p95_APE"])
    bal_p95_win = float(balanced_ref["avg_pp64_p95_win_rate"])
    bal_repl = float(balanced_ref["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt22", regex=True)].copy()

    balanced = balanced_ref.copy()
    balanced_pool = pool[
        (pool["fixed_test_MAPE"] <= bal_mape + 0.000002)
        & (pool["fixed_test_p95_APE"] <= bal_p95 + 0.000002)
        & (pool["avg_pp64_p95_win_rate"] >= bal_p95_win - 0.000001)
        & (pool["replacement_score"] <= bal_repl + 0.000002)
    ].copy()
    if not balanced_pool.empty:
        balanced = balanced_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    operational = balanced.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= bal_mape + 0.000002)
        & (pool["fixed_test_p95_APE"] <= bal_p95 + 0.000002)
        & (pool["replacement_score"] <= bal_repl + 0.000002)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    mape = aggressive_ref.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= bal_p95 + 0.000002].copy()
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
            f"{prefix}_delta_vs_pp222_balanced_MAPE": float(row["fixed_test_MAPE"]) - bal_mape,
            f"{prefix}_delta_vs_pp222_balanced_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - bal_p95_win,
            f"{prefix}_delta_vs_pp222_aggressive_MAPE": float(row["fixed_test_MAPE"]) - float(aggressive_ref["fixed_test_MAPE"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("balanced", balanced))
    decision.update(pack("mape_challenger", mape))
    decision.update(pack("p95_guarded", p95_guard))
    decision.update(pack("p95_extreme", p95_extreme))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "pp222_narrow_balance_operational_selection"),
        ("balanced", "pp222_narrow_balance_balanced_selection"),
        ("mape_challenger", "pp222_narrow_balance_mape_selection"),
        ("p95_guarded", "pp222_narrow_balance_p95_guarded_selection"),
        ("p95_extreme", "pp222_narrow_balance_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt228_{key}_pp222_narrow_balance__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT228"
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    support = config["support_candidates"]
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp192_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_operational"],
        support["pp222_balanced"],
        decision["operational_protocol_candidate"],
        decision["balanced_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "operational_pass_vs_incumbent", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"운영 후보 MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['operational_avg_pp64_p95_win_rate']:.6f}. "
        f"균형 후보 MAPE {decision['balanced_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['balanced_avg_pp64_p95_win_rate']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT223~228 Warm PP222 narrow balance refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP222 균형 후보와 공격형 후보 사이의 좁은 cap/strength/shrink 탐색",
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
<title>PP-OPT223~228 Warm PP222 narrow balance refinement 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT223~228 Warm PP222 narrow balance refinement 결과</h1>
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
    balanced = pp187.prediction_array(previous, feature_base, support["pp222_balanced"])
    aggressive = pp187.prediction_array(previous, feature_base, support["pp222_operational"])
    recovery = pp187.prediction_array(previous, feature_base, support["pp216_p95_recovery"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt223_neighborhood(feature_base, pp192, pp198))
    candidates.extend(pp_opt224_risk_shaped_cap(feature_base, pp192, pp198))
    candidates.extend(pp_opt225_micro_blend(feature_base, balanced, aggressive))
    candidates.extend(pp_opt226_recovery_support(feature_base, balanced, recovery))

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
            decision["mape_challenger_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support)
    label_map[decision["operational_protocol_candidate"]] = "pp228_operational_pp222_narrow_balance_challenger"
    label_map[decision["balanced_protocol_candidate"]] = "pp228_balanced_pp222_narrow_balance_challenger"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp228_mape_pp222_narrow_balance_challenger"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp228_p95_guarded_pp222_narrow_balance_challenger"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp228_p95_extreme_pp222_narrow_balance_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    base_w, p95_delta, mean_gain, count = pp217.p95_regularized_weight(
        feature_base,
        pp192,
        pp198,
        threshold=0.02,
        p95_threshold=-0.00014,
        p95_width=0.00012,
        score_width=0.22,
    )
    feature_frame = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    feature_frame["pp192_log"] = pp192
    feature_frame["pp198_log"] = pp198
    feature_frame["pp222_balanced_log"] = balanced
    feature_frame["pp222_aggressive_log"] = aggressive
    feature_frame["pp216_recovery_log"] = recovery
    feature_frame["default_weight"] = base_w
    feature_frame["p95_delta"] = p95_delta
    feature_frame["mean_gain"] = mean_gain
    feature_frame["segment_count"] = count

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP217_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP192 operational log price",
            "target": "PP198 operational log price",
            "main_final": "PP192 log price + clip((PP198 log price - PP192 log price) * p95_regularized_weight, row_cap)",
            "micro_blend": "PP222 balanced log price + clip((target log price - PP222 balanced log price) * share, row_cap)",
            "selection_goal": "Keep PP222 balanced p95 win-rate while moving MAPE toward PP222 aggressive.",
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
    feature_frame.to_csv(ARTIFACT_DIR / "pp222_narrow_balance_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp222_narrow_balance_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp222_narrow_balance_refinement_result.html").write_text(report_html, encoding="utf-8")

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
