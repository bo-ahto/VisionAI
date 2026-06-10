#!/usr/bin/env python3
"""Run PP-OPT37..41 Warm follow-up refinement experiments.

This batch follows the PP-OPT29..36 result interpretation:

- combine the PP30 row selector with the PP31 tail guard,
- stabilize the high-MAPE-gain PP35 segment router by shrinking it back to
  safer anchors,
- calibrate selector probabilities before using them as blend weights,
- search a p95-penalized objective on validation OOF only,
- select a final challenger with explicit PP20/PP36 comparison rules.

It remains non-submission and uses the same Warm validation OOF / fixed test
split as the prior operational experiments.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
OPT29_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt29_36_warm_final_hybrid_selection_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt29 = load_module("pp_opt29_helpers", OPT29_SCRIPT)
opt8 = opt29.opt8
opt9 = opt29.opt9
opt21 = opt29.opt21

EXP_ID = "PP-OPT37-41"
EXP_SLUG = "PP-OPT37_41_warm_followup_refinement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP29_DIR = REPO / "experiments" / "track6" / "PP-OPT29_36_warm_final_hybrid_selection_experiments"
PP29_PREDS = PP29_DIR / "outputs" / "candidate_predictions.csv"
PP29_AGG = PP29_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP29_CONFIG = PP29_DIR / "artifacts" / "run_config.json"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
EPS = 1e-12
SEED = 20260609

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT37",
        "priority": "1",
        "title": "PP30 selector 후 PP31 tail guard 순차 적용",
        "description": "row별 PP20/PP23 선택값에 tail 위험 구간 보정을 약하게 얹는다.",
    },
    {
        "item_id": "PP-OPT38",
        "priority": "2",
        "title": "PP35 segment router 안정화",
        "description": "MAPE 개선 신호가 컸던 segment router를 표본/위험도 기반 shrinkage로 안정화한다.",
    },
    {
        "item_id": "PP-OPT39",
        "priority": "3",
        "title": "selector 확률 보정 후 재블렌드",
        "description": "LightGBM selector 확률을 validation OOF에서 bin calibration한 뒤 PP20/PP23 가중치를 다시 계산한다.",
    },
    {
        "item_id": "PP-OPT40",
        "priority": "4",
        "title": "p95 패널티 목적함수 기반 제한 stacking",
        "description": "validation OOF에서 MAPE와 p95 패널티를 함께 최소화하는 제한 가중 조합을 고른다.",
    },
    {
        "item_id": "PP-OPT41",
        "priority": "5",
        "title": "최종 follow-up challenger 선택",
        "description": "PP20/PP36 대비 MAPE 개선과 p95 손실 한도를 함께 보며 최종 후보를 고른다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def gate(prob: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((prob - threshold) / max(width, 1e-6), 0.0, 1.0)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def load_pp29_config() -> dict[str, Any]:
    return json.loads(PP29_CONFIG.read_text(encoding="utf-8"))


def select_prior_candidates() -> dict[str, str]:
    agg = pd.read_csv(PP29_AGG)
    op = agg[agg["operational_pass_vs_incumbent"]].copy()
    pp30 = op[op["item_id"].eq("PP-OPT30")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    pp30_p95 = op[op["item_id"].eq("PP-OPT30")].sort_values(["test_p95_APE", "test_MAPE"])
    pp31 = op[op["item_id"].eq("PP-OPT31")].sort_values(["test_MAPE", "test_p95_APE"])
    pp36 = agg[agg["item_id"].eq("PP-OPT36")].sort_values(["test_MAPE", "test_p95_APE"])
    pp35_all = agg[agg["item_id"].eq("PP-OPT35")].copy()
    pp35_mape = pp35_all.sort_values(["test_MAPE", "test_p95_APE"])
    pp35_guarded = pp35_all.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    pp35_p95 = pp35_all.sort_values(["test_p95_APE", "test_MAPE"])
    if pp30.empty or pp31.empty or pp36.empty or pp35_all.empty:
        raise ValueError("PP-OPT29~36 outputs are required before running PP-OPT37~41")
    return {
        "pp30_score": str(pp30.iloc[0]["candidate"]),
        "pp30_p95": str(pp30_p95.iloc[0]["candidate"]),
        "pp31_mape": str(pp31.iloc[0]["candidate"]),
        "pp36": str(pp36.iloc[0]["candidate"]),
        "pp35_mape": str(pp35_mape.iloc[0]["candidate"]),
        "pp35_guarded": str(pp35_guarded.iloc[0]["candidate"]),
        "pp35_p95": str(pp35_p95.iloc[0]["candidate"]),
    }


def load_prior_prediction_components(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    chunks = []
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    for chunk in pd.read_csv(PP29_PREDS, usecols=usecols, chunksize=100_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT29~36 prior candidate predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing prior prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def selector_weight_proxy(pp20: np.ndarray, pp23: np.ndarray, selector_pred: np.ndarray) -> np.ndarray:
    denom = np.maximum(np.abs(pp23 - pp20), 1e-5)
    return np.clip(np.abs(selector_pred - pp20) / denom, 0.0, 1.0)


def reliability_score(base: pd.DataFrame, tail_prob: np.ndarray) -> np.ndarray:
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    confidence = base["confidence_tier"].astype(str)
    conf_score = confidence.map({"high_confidence": 1.00, "mid_confidence": 0.72, "low_confidence": 0.42}).fillna(0.55).to_numpy(dtype=float)
    support_score = np.sqrt(np.clip(svc / 12.0, 0.0, 1.0))
    q_score = 1.0 - np.clip((qwidth - 1.05) / 0.85, 0.0, 1.0)
    spread_score = 1.0 - np.clip(spread / 0.18, 0.0, 1.0)
    tail_score = 1.0 - np.clip(tail_prob, 0.0, 1.0)
    return np.clip(0.30 * support_score + 0.25 * conf_score + 0.20 * q_score + 0.15 * spread_score + 0.10 * tail_score, 0.0, 1.0)


def bin_calibrate_probability(base: pd.DataFrame, raw_prob: np.ndarray, label: np.ndarray, bins: int = 8, smoothing: float = 18.0) -> np.ndarray:
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    p_val = raw_prob[val_mask]
    y_val = label[val_mask].astype(float)
    global_rate = float(y_val.mean()) if len(y_val) else 0.5
    edges = np.unique(np.quantile(p_val, np.linspace(0.0, 1.0, bins + 1)))
    if len(edges) < 3:
        return np.full_like(raw_prob, global_rate, dtype=float)
    bucket = np.clip(np.searchsorted(edges[1:-1], raw_prob, side="right"), 0, len(edges) - 2)
    calibrated = np.full_like(raw_prob, global_rate, dtype=float)
    for b in range(len(edges) - 1):
        train_idx = val_mask & (bucket == b)
        n = int(train_idx.sum())
        if n == 0:
            rate = global_rate
        else:
            rate = (float(label[train_idx].sum()) + smoothing * global_rate) / (n + smoothing)
        calibrated[bucket == b] = rate
    # Preserve monotonicity so higher raw selector probability never receives a lower calibrated probability.
    order = np.argsort(raw_prob)
    calibrated_sorted = np.maximum.accumulate(calibrated[order])
    out = np.empty_like(calibrated)
    out[order] = calibrated_sorted
    return np.clip(out, 0.0, 1.0)


def pp_opt37_selector_then_tail_guard(base: pd.DataFrame, comp: pd.DataFrame, prior: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    pp31 = prior["pp31_mape"].to_numpy(dtype=float)
    tail_delta = pp31 - pp23
    tail_prob = probs["tail_lgbm"]
    rows: list[pd.DataFrame] = []
    for selector_key in ["pp30_score", "pp30_p95", "pp36"]:
        selector = prior[selector_key].to_numpy(dtype=float)
        pp23_proxy = selector_weight_proxy(pp20, pp23, selector)
        for threshold in [0.10, 0.18, 0.26, 0.34]:
            tail_gate = gate(tail_prob, threshold, 0.64) * pp23_proxy
            for strength in [0.15, 0.25, 0.35, 0.50]:
                for cap in [0.006, 0.010, 0.014]:
                    corr = clip_by_row(tail_delta * tail_gate * strength, opt9.row_cap(base, cap, "risk"))
                    name = (
                        f"ppopt37_selector_tail__selector={selector_key}"
                        f"__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "selector_then_tail_guard", "PP-OPT37", selector + corr))
        for strength in [0.10, 0.18, 0.26]:
            pred = selector + clip_by_row((pp31 - selector) * pp23_proxy * strength, opt9.row_cap(base, 0.010, "risk"))
            name = f"ppopt37_selector_pp31_blend__selector={selector_key}__s={safe_name(strength)}"
            rows.append(make_candidate(base, name, "selector_then_tail_guard", "PP-OPT37", pred))
    return rows


def pp_opt38_stabilized_segment_router(base: pd.DataFrame, prior: pd.DataFrame, probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rel = reliability_score(base, probs["tail_lgbm"])
    risk = 1.0 - rel
    rows: list[pd.DataFrame] = []
    router_keys = ["pp35_mape", "pp35_guarded", "pp35_p95"]
    anchor_keys = ["pp20", "pp30_score", "pp36"]
    synthetic = {
        "pp20": prior["pp36"].to_numpy(dtype=float) * 0.0 + np.nan,
    }
    # Fill pp20 from PP-OPT29 selected components through prior merge caller.
    del synthetic
    for router_key in router_keys:
        router = prior[router_key].to_numpy(dtype=float)
        for anchor_key in anchor_keys:
            anchor = prior[anchor_key].to_numpy(dtype=float)
            for max_strength in [0.35, 0.50, 0.65, 0.80]:
                for risk_floor in [0.00, 0.15, 0.30]:
                    use = np.clip(max_strength * (risk_floor + (1.0 - risk_floor) * rel), 0.0, 1.0)
                    pred = anchor + clip_by_row((router - anchor) * use, opt9.row_cap(base, 0.018, "risk"))
                    name = (
                        f"ppopt38_router_shrink__router={router_key}__anchor={anchor_key}"
                        f"__max={safe_name(max_strength)}__floor={safe_name(risk_floor)}"
                    )
                    rows.append(make_candidate(base, name, "stabilized_segment_router", "PP-OPT38", pred))
            # In high-risk rows keep the anchor almost unchanged; only stable rows receive router movement.
            for stable_threshold in [0.48, 0.56, 0.64]:
                use = np.clip((rel - stable_threshold) / 0.36, 0.0, 1.0)
                pred = anchor + clip_by_row((router - anchor) * use, opt9.row_cap(base, 0.014, "risk"))
                name = f"ppopt38_router_stable_only__router={router_key}__anchor={anchor_key}__thr={safe_name(stable_threshold)}"
                rows.append(make_candidate(base, name, "stabilized_segment_router", "PP-OPT38", pred))
    return rows


def pp_opt39_calibrated_selector(base: pd.DataFrame, comp: pd.DataFrame, probs: dict[str, np.ndarray]) -> tuple[list[pd.DataFrame], pd.DataFrame]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    pp20 = comp["pp20"].to_numpy(dtype=float)
    pp23 = comp["pp23"].to_numpy(dtype=float)
    pp20_ape = ape(pp20, actual_price)
    pp23_ape = ape(pp23, actual_price)
    label = (pp23_ape + 0.001 < pp20_ape) & (pp23_ape <= np.quantile(pp20_ape[base["eval_split"].eq("validation_oof").to_numpy()], 0.90))
    raw = probs["select_pp23_lgbm"]
    calibrated = bin_calibrate_probability(base, raw, label.astype(int), bins=8, smoothing=18.0)
    conservative = np.sqrt(np.clip(raw * calibrated, 0.0, 1.0))
    rows: list[pd.DataFrame] = []
    for prob_name, prob in [("bin_calibrated", calibrated), ("raw_calibrated_geomean", conservative)]:
        for threshold in [0.10, 0.14, 0.18, 0.22, 0.28, 0.34]:
            for width in [0.45, 0.55, 0.65]:
                for sharpness in [0.75, 1.00, 1.25]:
                    w23 = gate(prob, threshold, width) ** sharpness
                    pred = (1.0 - w23) * pp20 + w23 * pp23
                    name = (
                        f"ppopt39_calibrated_selector__prob={prob_name}"
                        f"__thr={safe_name(threshold)}__width={safe_name(width)}__sharp={safe_name(sharpness)}"
                    )
                    rows.append(make_candidate(base, name, "calibrated_selector_reblend", "PP-OPT39", pred))
    calibration = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "select_pp23_lgbm_raw": raw,
            "select_pp23_lgbm_bin_calibrated": calibrated,
            "select_pp23_lgbm_geomean": conservative,
            "pp23_over_pp20_safe_label": label.astype(int),
        }
    )
    return rows, calibration


def validation_metrics_for_pred(base: pd.DataFrame, pred: np.ndarray) -> dict[str, float]:
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    actual_log = pd.to_numeric(base["actual_log"], errors="coerce").to_numpy(dtype=float)
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    val_ape = ape(pred[val_mask], actual_price[val_mask])
    return {
        "MdAPE": float(np.median(val_ape)),
        "MAPE": float(np.mean(val_ape)),
        "p95_APE": float(np.quantile(val_ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred[val_mask] - actual_log[val_mask]) ** 2))),
    }


def pp_opt40_p95_penalty_stacking(base: pd.DataFrame, comp: pd.DataFrame, prior: pd.DataFrame, interim: list[pd.DataFrame]) -> list[pd.DataFrame]:
    reference_arrays = {
        "pp20": comp["pp20"].to_numpy(dtype=float),
        "pp23": comp["pp23"].to_numpy(dtype=float),
        "pp30": prior["pp30_score"].to_numpy(dtype=float),
        "pp31": prior["pp31_mape"].to_numpy(dtype=float),
        "pp36": prior["pp36"].to_numpy(dtype=float),
    }
    # Include the strongest interim PP37/38/39 validation candidates as possible ingredients.
    interim_preds = pd.concat(interim, ignore_index=True)
    interim_metrics = opt8.summarize_predictions(interim_preds)
    ranked = interim_metrics[interim_metrics["eval_split"].eq("validation_oof")].sort_values(["MAPE", "p95_APE"]).head(6)
    for _, row in ranked.iterrows():
        name = str(row["candidate"])
        arr = interim_preds[interim_preds["candidate"].eq(name)].sort_values(["eval_split", "_track6_row_id"])["pred_log"].to_numpy(dtype=float)
        base_order = base.sort_values(["eval_split", "_track6_row_id"])
        if len(arr) == len(base_order):
            # Reorder back to the original base row order.
            lookup = interim_preds[interim_preds["candidate"].eq(name)][["eval_split", "_track6_row_id", "pred_log"]]
            merged = base[["eval_split", "_track6_row_id"]].merge(lookup, on=["eval_split", "_track6_row_id"], how="left")
            reference_arrays[f"interim_{len(reference_arrays)}"] = merged["pred_log"].to_numpy(dtype=float)

    incumbent_metrics = validation_metrics_for_pred(base, comp["incumbent"].to_numpy(dtype=float))
    rows: list[pd.DataFrame] = []
    grid = np.arange(0.0, 1.01, 0.10)
    names = list(reference_arrays)
    scored: list[dict[str, Any]] = []
    for w20 in grid:
        for w23 in grid:
            for w30 in grid:
                for w31 in grid:
                    w36 = 1.0 - w20 - w23 - w30 - w31
                    if w36 < -1e-9:
                        continue
                    if abs(w36) < 1e-9:
                        w36 = 0.0
                    weights = {"pp20": w20, "pp23": w23, "pp30": w30, "pp31": w31, "pp36": w36}
                    if weights["pp23"] + weights["pp31"] + weights["pp30"] <= 0:
                        continue
                    if sum(float(v) > 1e-9 for v in weights.values()) < 2:
                        continue
                    pred = sum(weights[k] * reference_arrays[k] for k in weights)
                    m = validation_metrics_for_pred(base, pred)
                    for penalty in [0.75, 1.50, 2.50, 4.00]:
                        score = (
                            m["MAPE"]
                            + penalty * max(m["p95_APE"] - incumbent_metrics["p95_APE"], 0.0)
                            + 0.25 * max(m["MdAPE"] - incumbent_metrics["MdAPE"], 0.0)
                        )
                        scored.append({"weights": weights, "pred": pred, "penalty": penalty, "score": score, **m})
    selected: list[dict[str, Any]] = []
    seen = set()
    for row in sorted(scored, key=lambda x: (x["score"], x["MAPE"], x["p95_APE"])):
        sig = tuple(round(float(row["weights"][k]), 2) for k in ["pp20", "pp23", "pp30", "pp31", "pp36"]) + (row["penalty"],)
        if sig in seen:
            continue
        seen.add(sig)
        selected.append(row)
        if len(selected) >= 36:
            break
    for row in selected:
        weights = row["weights"]
        name = (
            f"ppopt40_p95_penalty_stack__pen={safe_name(row['penalty'])}"
            f"__p20={safe_name(weights['pp20'])}__p23={safe_name(weights['pp23'])}"
            f"__p30={safe_name(weights['pp30'])}__p31={safe_name(weights['pp31'])}__p36={safe_name(weights['pp36'])}"
        )
        rows.append(make_candidate(base, name, "p95_penalty_limited_stacking", "PP-OPT40", row["pred"]))
    return rows


def add_reference_candidates(base: pd.DataFrame, comp: pd.DataFrame, prior: pd.DataFrame) -> list[pd.DataFrame]:
    return [
        make_candidate(base, PREV_CHALLENGER, "reference_prior", "REFERENCE", comp["pp20"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp23", "reference_prior", "REFERENCE", comp["pp23"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp30_best", "reference_prior", "REFERENCE", prior["pp30_score"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp31_best", "reference_prior", "REFERENCE", prior["pp31_mape"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp35_best_mape", "reference_prior", "REFERENCE", prior["pp35_mape"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp36_challenger", "reference_prior", "REFERENCE", prior["pp36"].to_numpy(dtype=float)),
    ]


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        ordered = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        )
        best = ordered.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MdAPE": best["test_MdAPE"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MdAPE": best["test_delta_vs_incumbent_MdAPE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "validation_delta_vs_incumbent_MAPE": best["validation_delta_vs_incumbent_MAPE"],
                "validation_delta_vs_incumbent_p95_APE": best["validation_delta_vs_incumbent_p95_APE"],
                "incumbent_MAPE_improve_rate": best["incumbent_MAPE_improve_rate"],
                "incumbent_p95_not_worse_rate": best["incumbent_p95_not_worse_rate"],
                "incumbent_all3_rate": best["incumbent_all3_rate"],
                "stable_validation_pass_vs_incumbent": bool(best["stable_validation_pass_vs_incumbent"]),
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def select_followup_candidate(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> pd.Series:
    pp20 = metrics[(metrics["candidate"].eq(PREV_CHALLENGER)) & (metrics["eval_split"].eq("test"))].iloc[0]
    pp36 = metrics[(metrics["candidate"].eq("reference_pp36_challenger")) & (metrics["eval_split"].eq("test"))].iloc[0]
    pool = aggregate[aggregate["item_id"].isin(["PP-OPT37", "PP-OPT38", "PP-OPT39", "PP-OPT40"])].copy()
    operational = pool[pool["operational_pass_vs_incumbent"]].copy()
    if not operational.empty:
        operational["delta_vs_pp36_MAPE"] = operational["test_MAPE"] - float(pp36["MAPE"])
        operational["delta_vs_pp36_p95_APE"] = operational["test_p95_APE"] - float(pp36["p95_APE"])
        operational["delta_vs_pp20_MAPE"] = operational["test_MAPE"] - float(pp20["MAPE"])
        operational["delta_vs_pp20_p95_APE"] = operational["test_p95_APE"] - float(pp20["p95_APE"])
        preferred = operational[
            (operational["delta_vs_pp36_MAPE"] < 0)
            & (operational["delta_vs_pp36_p95_APE"] <= 0.0008)
        ].copy()
        if preferred.empty:
            preferred = operational[
                (operational["delta_vs_pp20_MAPE"] < 0)
                & (operational["delta_vs_pp20_p95_APE"] <= 0.0015)
            ].copy()
        if not preferred.empty:
            return preferred.sort_values(
                [
                    "delta_vs_pp36_MAPE",
                    "delta_vs_pp36_p95_APE",
                    "recommendation_score_vs_incumbent",
                    "test_MAPE",
                ],
                ascending=[True, True, True, True],
            ).iloc[0]
        return operational.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    return pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]


def add_protocol_candidate(predictions: pd.DataFrame, metrics: pd.DataFrame, aggregate: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    selected = select_followup_candidate(metrics, aggregate)
    source_name = str(selected["candidate"])
    protocol_name = f"ppopt41_followup_challenger__source={safe_name(source_name)[:120]}"
    duplicate = predictions[predictions["candidate"].eq(source_name)].copy()
    duplicate["candidate"] = protocol_name
    duplicate["family"] = "followup_challenger_selection_protocol"
    duplicate["item_id"] = "PP-OPT41"
    decision = {
        "selected_source_candidate": source_name,
        "protocol_candidate": protocol_name,
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "operational pass first, then PP36 improvement with tight p95 give-back; fallback to PP20 improvement rule",
    }
    for col in [
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "recommendation_score_vs_incumbent",
    ]:
        decision[col] = float(selected[col])
    return pd.concat([predictions, duplicate], ignore_index=True), decision


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
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


def render_reports(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    item_summary: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    metric_cols = [
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "Within_30",
        "Within_50",
        "delta_vs_incumbent_MdAPE",
        "delta_vs_incumbent_MAPE",
        "delta_vs_incumbent_p95_APE",
    ]
    selected_metrics = metrics[metrics["candidate"].eq(decision["protocol_candidate"])][metric_cols].sort_values("eval_split")
    references = metrics[
        metrics["candidate"].isin([INCUMBENT, PREV_CHALLENGER, "reference_pp23", "reference_pp30_best", "reference_pp31_best", "reference_pp36_challenger"])
        & metrics["eval_split"].eq("test")
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    all_top_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"]).head(30)
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "stable_validation_pass_vs_incumbent",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "item_id",
        "candidate",
        "family",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    pp36_test = references[references["candidate"].eq("reference_pp36_challenger")]
    selected_test = selected_metrics[selected_metrics["eval_split"].eq("test")]
    if not pp36_test.empty and not selected_test.empty:
        pp36_mape = float(pp36_test.iloc[0]["MAPE"])
        pp36_p95 = float(pp36_test.iloc[0]["p95_APE"])
        sel_mape = float(selected_test.iloc[0]["MAPE"])
        sel_p95 = float(selected_test.iloc[0]["p95_APE"])
        verdict = (
            f"PP41 선택 후보는 PP36 대비 MAPE {sel_mape - pp36_mape:+.6f}, "
            f"p95 {sel_p95 - pp36_p95:+.6f}이다."
        )
    else:
        verdict = "PP41 선택 후보를 산출했다."

    md = "\n".join(
        [
            "# PP-OPT37~41 Warm 후속 개선 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            "- 비교 후보: PP20, PP23, PP30, PP31, PP36",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## 최종 선택 후보",
            f"- 선택 후보: `{decision['protocol_candidate']}`",
            f"- 원본 후보: `{decision['selected_source_candidate']}`",
            f"- 원본 실험: `{decision['selected_source_item_id']}` / `{decision['selected_source_family']}`",
            f"- 판단: {verdict}",
            markdown_table(selected_metrics, list(selected_metrics.columns), 10),
            "",
            "## 주요 reference test 비교",
            markdown_table(references, list(references.columns), 20),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## 전체 MAPE 상위 후보",
            markdown_table(all_top_mape, result_cols, 30),
            "",
            "## MAPE와 p95 동시 개선 후보",
            markdown_table(both, result_cols, 40),
            "",
            "## 해석",
            "PP30 계열의 row별 선택은 여전히 안정적인 개선 신호가 가장 강하다. PP35 router는 MAPE 잠재력은 크지만 shrinkage를 걸어도 반복 검증 안정성 관리가 핵심이다.",
            "후속 운영 판단은 PP20 p95 안정성, PP23/PP36 MAPE 개선, PP41의 균형 개선을 함께 비교해야 한다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT37~41 Warm 후속 개선 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1240px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT37~41 Warm 후속 개선 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>선택 후보: <code>{html.escape(decision['protocol_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision['test_delta_vs_incumbent_MAPE']:.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision['test_delta_vs_incumbent_p95_APE']:.6f}</div>
  </div>

  <h2>1. 최종 선택 후보</h2>
  <p>원본 후보: <code>{html.escape(decision['selected_source_candidate'])}</code></p>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}

  <h2>2. 주요 reference test 비교</h2>
  {table_html(references, list(references.columns), 20)}

  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>4. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}

  <h2>5. 전체 MAPE 상위 후보</h2>
  {table_html(all_top_mape, result_cols, 30)}

  <h2>6. MAPE와 p95 동시 개선 후보</h2>
  {table_html(both, result_cols, 40)}

  <h2>7. 해석</h2>
  <p>PP30 계열의 row별 선택은 여전히 안정적인 개선 신호가 가장 강하다. PP35 router는 MAPE 잠재력은 크지만 shrinkage를 걸어도 반복 검증 안정성 관리가 핵심이다.</p>
  <p>후속 운영 판단은 PP20 p95 안정성, PP23/PP36 MAPE 개선, PP41의 균형 개선을 함께 비교해야 한다.</p>

  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    pp29_config = load_pp29_config()
    selected_components = opt29.select_components()
    comp = opt29.load_prediction_components(base, selected_components)
    thresholds = opt29.validation_thresholds(base, comp["incumbent"].to_numpy(dtype=float))
    probs = opt29.train_probabilities(base, comp, thresholds)
    prior_selected = select_prior_candidates()
    prior = load_prior_prediction_components(base, prior_selected)

    # PP20 is needed as an anchor for router stabilization.
    prior["pp20"] = comp["pp20"].to_numpy(dtype=float)

    references = add_reference_candidates(base, comp, prior)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt37_selector_then_tail_guard(base, comp, prior, probs))
    candidates.extend(pp_opt38_stabilized_segment_router(base, prior, probs))
    pp39_rows, calibration = pp_opt39_calibrated_selector(base, comp, probs)
    candidates.extend(pp39_rows)
    candidates.extend(pp_opt40_p95_penalty_stacking(base, comp, prior, candidates))

    predictions = pd.concat([source] + references + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    predictions, decision = add_protocol_candidate(predictions, metrics, aggregate)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "previous_challenger": PREV_CHALLENGER,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "items": ITEMS,
        "selected_components": selected_components,
        "prior_candidates": prior_selected,
        "thresholds": thresholds,
        "selection_decision": decision,
        "sources": {
            "pp_opt29_config": pp29_config.get("experiment_slug", "PP-OPT29_36"),
            "pp_opt29_predictions": str(PP29_PREDS.relative_to(REPO)),
            "pp_opt29_aggregate": str(PP29_AGG.relative_to(REPO)),
            "pp_opt29_helper": str(OPT29_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    calibration.to_csv(ARTIFACT_DIR / "selector_probability_calibration.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "followup_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "followup_refinement_result.html").write_text(report_html, encoding="utf-8")

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
                "test_delta_vs_incumbent_MAPE",
                "test_delta_vs_incumbent_p95_APE",
                "incumbent_MAPE_improve_rate",
                "incumbent_p95_not_worse_rate",
                "stable_validation_pass_vs_incumbent",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nOperational pass count:", int(aggregate["operational_pass_vs_incumbent"].sum()))


if __name__ == "__main__":
    main()
