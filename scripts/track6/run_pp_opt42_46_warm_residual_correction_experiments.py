#!/usr/bin/env python3
"""Run PP-OPT42..46 Warm residual correction experiments.

This batch moves beyond candidate blending.  PP-OPT29..41 showed that simple
mixing is close to saturated, while residual bias remains in high-price,
high-uncertainty, and wide-spread segments.  The experiments below therefore
learn small residual corrections around the strongest current anchors.
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
OPT37_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt37_41_warm_followup_refinement_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt37 = load_module("pp_opt37_helpers", OPT37_SCRIPT)
opt29 = opt37.opt29
opt21 = opt37.opt21
opt9 = opt37.opt9
opt8 = opt37.opt8

EXP_ID = "PP-OPT42-46"
EXP_SLUG = "PP-OPT42_46_warm_residual_correction_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP37_DIR = REPO / "experiments" / "track6" / "PP-OPT37_41_warm_followup_refinement_experiments"
PP37_PREDS = PP37_DIR / "outputs" / "candidate_predictions.csv"
PP37_AGG = PP37_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP37_CONFIG = PP37_DIR / "artifacts" / "run_config.json"

BASE_CANDIDATE = opt29.BASE_CANDIDATE
INCUMBENT = opt29.INCUMBENT
PREV_CHALLENGER = opt29.PREV_CHALLENGER
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT42",
        "priority": "1",
        "title": "잔차 방향 분류 후 비대칭 cap 보정",
        "description": "과대/과소예측 방향 확신이 있을 때만 서로 다른 상한으로 보정한다.",
    },
    {
        "item_id": "PP-OPT43",
        "priority": "2",
        "title": "구간별 residual median shrinkage",
        "description": "가격대/신뢰도/불확실성 구간의 잔차 중앙값을 표본 수 기반으로 축소해 적용한다.",
    },
    {
        "item_id": "PP-OPT44",
        "priority": "3",
        "title": "LightGBM quantile residual correction",
        "description": "잔차 q25/q50/q75를 학습하고 예측구간 폭이 넓으면 보정 강도를 줄인다.",
    },
    {
        "item_id": "PP-OPT45",
        "priority": "4",
        "title": "very-high-price 전용 PP30/PP38 fallback",
        "description": "대부분은 PP23/PP41을 유지하고 초고가 구간에서만 안정 후보로 부분 fallback한다.",
    },
    {
        "item_id": "PP-OPT46",
        "priority": "5",
        "title": "monotonic correction cap 재설계",
        "description": "유사작품 수가 적고 불확실성이 클수록 보정 상한을 단조적으로 줄인다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def clip_asym(values: np.ndarray, positive_cap: np.ndarray, negative_cap: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -negative_cap), positive_cap)


def gate(prob: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((prob - threshold) / max(width, 1e-6), 0.0, 1.0)


def load_pp37_config() -> dict[str, Any]:
    return json.loads(PP37_CONFIG.read_text(encoding="utf-8"))


def select_reference_candidates() -> dict[str, str]:
    agg = pd.read_csv(PP37_AGG)
    op = agg[agg["operational_pass_vs_incumbent"]].copy()
    pp38_score = op[op["item_id"].eq("PP-OPT38")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    pp38_mape = agg[agg["item_id"].eq("PP-OPT38")].sort_values(["test_MAPE", "test_p95_APE"])
    pp39_score = op[op["item_id"].eq("PP-OPT39")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    pp40_score = op[op["item_id"].eq("PP-OPT40")].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    pp41 = agg[agg["item_id"].eq("PP-OPT41")].sort_values(["test_MAPE", "test_p95_APE"])
    needed = [pp38_score, pp38_mape, pp39_score, pp40_score, pp41]
    if any(df.empty for df in needed):
        raise ValueError("PP-OPT37~41 outputs are required before running PP-OPT42~46")
    return {
        "pp20": PREV_CHALLENGER,
        "pp23": "reference_pp23",
        "pp30": "reference_pp30_best",
        "pp36": "reference_pp36_challenger",
        "pp41": str(pp41.iloc[0]["candidate"]),
        "pp38_score": str(pp38_score.iloc[0]["candidate"]),
        "pp38_mape": str(pp38_mape.iloc[0]["candidate"]),
        "pp39_score": str(pp39_score.iloc[0]["candidate"]),
        "pp40_score": str(pp40_score.iloc[0]["candidate"]),
    }


def load_reference_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP37_PREDS, usecols=usecols, chunksize=100_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT37~41 reference predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing reference prediction columns: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def reliability_score(base: pd.DataFrame) -> np.ndarray:
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    confidence = base["confidence_tier"].astype(str)
    conf_score = confidence.map({"high_confidence": 1.00, "medium_confidence": 0.72, "mid_confidence": 0.72, "low_confidence": 0.42}).fillna(0.55).to_numpy(dtype=float)
    support_score = np.sqrt(np.clip(svc / 12.0, 0.0, 1.0))
    q_score = 1.0 - np.clip((qwidth - 1.05) / 0.85, 0.0, 1.0)
    spread_score = 1.0 - np.clip(spread / 0.18, 0.0, 1.0)
    return np.clip(0.35 * support_score + 0.25 * conf_score + 0.25 * q_score + 0.15 * spread_score, 0.0, 1.0)


def monotonic_cap_factor(base: pd.DataFrame) -> np.ndarray:
    rel = reliability_score(base)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    q_factor = 1.0 - 0.45 * np.clip((qwidth - 1.05) / 0.95, 0.0, 1.0)
    svc_factor = 0.55 + 0.45 * np.sqrt(np.clip(svc / 10.0, 0.0, 1.0))
    return np.clip(0.35 + 0.65 * rel, 0.25, 1.0) * q_factor * svc_factor


def sign_probabilities(base: pd.DataFrame, center: np.ndarray, margin: float) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    residual = pd.to_numeric(base["actual_log"], errors="coerce").to_numpy(dtype=float) - center
    under_label = residual > margin
    over_label = residual < -margin
    under_prob = opt21.oof_lgbm_probability(base, under_label.astype(int), monotone=True)
    over_prob = opt21.oof_lgbm_probability(base, over_label.astype(int), monotone=True)
    detail = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "center_residual_log": residual,
            "underprediction_label": under_label.astype(int),
            "overprediction_label": over_label.astype(int),
            "underprediction_probability": under_prob,
            "overprediction_probability": over_prob,
        }
    )
    return under_prob, over_prob, detail


def oof_segment_residual_median(base: pd.DataFrame, center: np.ndarray, group_cols: list[str], shrinkage: float) -> np.ndarray:
    residual = pd.to_numeric(base["actual_log"], errors="coerce").to_numpy(dtype=float) - center
    out = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    val_res = residual[val_mask]
    global_med = float(np.median(val_res))

    def fit_map(train_frame: pd.DataFrame, train_res: np.ndarray) -> tuple[pd.Series, pd.Series]:
        tmp = train_frame[group_cols].astype(str).copy()
        tmp["_residual"] = train_res
        grouped = tmp.groupby(group_cols, observed=True)["_residual"].agg(["median", "count"])
        shrink = grouped["count"] / (grouped["count"] + shrinkage)
        corr = grouped["median"] * shrink
        return corr, grouped["count"]

    def apply_map(frame: pd.DataFrame, corr: pd.Series) -> np.ndarray:
        key_frame = frame[group_cols].astype(str)
        values = []
        for _, row in key_frame.iterrows():
            key = tuple(row[col] for col in group_cols)
            if len(group_cols) == 1:
                key = key[0]
            values.append(float(corr.get(key, global_med)))
        return np.asarray(values, dtype=float)

    val_positions = np.flatnonzero(val_mask)
    for tr_idx, va_idx in opt8.cv_splits(val):
        corr, _ = fit_map(val.iloc[tr_idx], val_res[tr_idx])
        out[val_positions[va_idx]] = apply_map(val.iloc[va_idx], corr)
    corr, _ = fit_map(val, val_res)
    out[np.flatnonzero(test_mask)] = apply_map(test, corr)
    return out


def pp_opt42_directional_asymmetric_cap(base: pd.DataFrame, ref: pd.DataFrame, quant: dict[str, np.ndarray], probs: tuple[np.ndarray, np.ndarray]) -> list[pd.DataFrame]:
    under_prob, over_prob = probs
    rows: list[pd.DataFrame] = []
    rel = reliability_score(base)
    direction_strength = np.clip(np.abs(under_prob - over_prob), 0.0, 1.0)
    direction_sign = np.sign(under_prob - over_prob)
    q50 = quant["q50"]
    signed_mag = direction_sign * np.abs(q50)
    base_center_options = ["pp41", "pp23", "pp38_score"]
    for center_key in base_center_options:
        center = ref[center_key].to_numpy(dtype=float)
        for prob_threshold in [0.08, 0.16, 0.24]:
            confidence_gate = gate(direction_strength, prob_threshold, 0.55)
            for strength in [0.20, 0.35, 0.50, 0.65]:
                for pos_cap, neg_cap in [(0.008, 0.012), (0.010, 0.016), (0.014, 0.010)]:
                    pos = pos_cap * (0.45 + 0.55 * rel)
                    neg = neg_cap * (0.45 + 0.55 * rel)
                    corr = clip_asym(signed_mag * confidence_gate * strength, pos, neg)
                    name = (
                        f"ppopt42_direction_asym__center={center_key}__thr={safe_name(prob_threshold)}"
                        f"__s={safe_name(strength)}__pcap={safe_name(pos_cap)}__ncap={safe_name(neg_cap)}"
                    )
                    rows.append(make_candidate(base, name, "directional_asymmetric_residual", "PP-OPT42", center + corr))
    return rows


def pp_opt43_segment_median_shrinkage(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    group_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_spread": ["stable_price_band", "pred_spread_band"],
        "price_conf_qwidth": ["stable_price_band", "confidence_tier", "qwidth_band"],
        "price_support_spread": ["stable_price_band", "svc_group_n_band", "pred_spread_band"],
    }
    for center_key in ["pp41", "pp23", "pp38_score"]:
        center = ref[center_key].to_numpy(dtype=float)
        for group_name, cols in group_sets.items():
            available_cols = [c for c in cols if c in base.columns]
            if not available_cols:
                continue
            for shrinkage in [10.0, 18.0, 32.0, 55.0]:
                raw_corr = oof_segment_residual_median(base, center, available_cols, shrinkage)
                for strength in [0.35, 0.55, 0.75]:
                    for cap in [0.008, 0.012, 0.016]:
                        corr = clip_asym(raw_corr * strength, cap * monotonic_cap_factor(base), cap * monotonic_cap_factor(base))
                        name = (
                            f"ppopt43_segment_median__center={center_key}__group={group_name}"
                            f"__shrink={safe_name(shrinkage)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "segment_median_residual_shrinkage", "PP-OPT43", center + corr))
    return rows


def pp_opt44_quantile_residual(base: pd.DataFrame, ref: pd.DataFrame, quant_by_center: dict[str, dict[str, np.ndarray]]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    rel = reliability_score(base)
    cap_factor = monotonic_cap_factor(base)
    for center_key, quant in quant_by_center.items():
        center = ref[center_key].to_numpy(dtype=float)
        width = np.maximum(quant["q75"] - quant["q25"], 0.0)
        width_shrink = 1.0 / (1.0 + np.clip(width / 0.16, 0.0, 5.0))
        q50 = quant["q50"]
        consensus = np.where(q50 >= 0, np.maximum(quant["q25"], 0.0), np.minimum(quant["q75"], 0.0))
        for source_name, raw_corr in [("q50", q50), ("consensus", consensus), ("q50_width", q50 * width_shrink)]:
            for strength in [0.25, 0.40, 0.55, 0.70]:
                for cap in [0.008, 0.012, 0.016, 0.020]:
                    corr = clip_asym(raw_corr * strength * (0.45 + 0.55 * rel), cap * cap_factor, cap * cap_factor)
                    name = (
                        f"ppopt44_quantile_residual__center={center_key}__src={source_name}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "quantile_residual_correction", "PP-OPT44", center + corr))
    return rows


def pp_opt45_high_price_fallback(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    price = base["stable_price_band"].astype(str)
    qwidth = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    very_high = price.eq("very_high_price").to_numpy()
    risk_gate = np.clip((qwidth - 1.35) / 0.80, 0.0, 1.0) * 0.55 + np.clip(spread / 0.18, 0.0, 1.0) * 0.45
    for base_key in ["pp23", "pp41"]:
        base_pred = ref[base_key].to_numpy(dtype=float)
        for fallback_key in ["pp30", "pp38_score", "pp20"]:
            fallback = ref[fallback_key].to_numpy(dtype=float)
            for mode in ["all_very_high", "risky_very_high"]:
                mask_weight = very_high.astype(float)
                if mode == "risky_very_high":
                    mask_weight = mask_weight * risk_gate
                for strength in [0.20, 0.35, 0.50, 0.65, 0.80]:
                    pred = base_pred + (fallback - base_pred) * mask_weight * strength
                    name = f"ppopt45_high_price_fallback__base={base_key}__fallback={fallback_key}__mode={mode}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "very_high_price_fallback", "PP-OPT45", pred))
    return rows


def pp_opt46_monotonic_cap(base: pd.DataFrame, ref: pd.DataFrame, quant: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    cap_factor = monotonic_cap_factor(base)
    q50 = quant["q50"]
    segment_corr = oof_segment_residual_median(base, ref["pp41"].to_numpy(dtype=float), ["stable_price_band", "confidence_tier"], 24.0)
    for center_key in ["pp41", "pp23", "pp38_score"]:
        center = ref[center_key].to_numpy(dtype=float)
        for source_name, raw_corr in [("q50", q50), ("segment", segment_corr), ("q50_segment_avg", 0.5 * q50 + 0.5 * segment_corr)]:
            for base_cap in [0.008, 0.012, 0.016, 0.020]:
                for strength in [0.25, 0.40, 0.55, 0.70]:
                    cap = base_cap * cap_factor
                    corr = clip_asym(raw_corr * strength, cap, cap)
                    name = (
                        f"ppopt46_monotonic_cap__center={center_key}__src={source_name}"
                        f"__s={safe_name(strength)}__cap={safe_name(base_cap)}"
                    )
                    rows.append(make_candidate(base, name, "monotonic_correction_cap", "PP-OPT46", center + corr))
    return rows


def add_reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    return [
        make_candidate(base, PREV_CHALLENGER, "reference_prior", "REFERENCE", ref["pp20"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp23", "reference_prior", "REFERENCE", ref["pp23"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp30_best", "reference_prior", "REFERENCE", ref["pp30"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp36_challenger", "reference_prior", "REFERENCE", ref["pp36"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp38_best", "reference_prior", "REFERENCE", ref["pp38_score"].to_numpy(dtype=float)),
        make_candidate(base, "reference_pp41_challenger", "reference_prior", "REFERENCE", ref["pp41"].to_numpy(dtype=float)),
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


def select_best_candidate(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> dict[str, Any]:
    refs = metrics[(metrics["eval_split"].eq("test")) & (metrics["candidate"].isin(["reference_pp23", "reference_pp41_challenger", "reference_pp38_best", PREV_CHALLENGER]))]
    pp41 = refs[refs["candidate"].eq("reference_pp41_challenger")].iloc[0]
    pp23 = refs[refs["candidate"].eq("reference_pp23")].iloc[0]
    pool = aggregate[aggregate["item_id"].isin([item["item_id"] for item in ITEMS])].copy()
    op = pool[pool["operational_pass_vs_incumbent"]].copy()
    if op.empty:
        selected = pool.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    else:
        op["delta_vs_pp41_MAPE"] = op["test_MAPE"] - float(pp41["MAPE"])
        op["delta_vs_pp41_p95_APE"] = op["test_p95_APE"] - float(pp41["p95_APE"])
        op["delta_vs_pp23_MAPE"] = op["test_MAPE"] - float(pp23["MAPE"])
        op["delta_vs_pp23_p95_APE"] = op["test_p95_APE"] - float(pp23["p95_APE"])
        preferred = op[
            (op["delta_vs_pp41_MAPE"] < 0)
            & (op["delta_vs_pp41_p95_APE"] <= 0.0008)
            & (op["test_delta_vs_incumbent_p95_APE"] <= 0)
        ].copy()
        if not preferred.empty:
            selected = preferred.sort_values(["delta_vs_pp41_MAPE", "delta_vs_pp41_p95_APE", "recommendation_score_vs_incumbent"]).iloc[0]
        else:
            conservative = op[op["test_delta_vs_incumbent_p95_APE"] <= 0].copy()
            if not conservative.empty:
                selected = conservative.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
            else:
                selected = op.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    decision: dict[str, Any] = {
        "selected_candidate": str(selected["candidate"]),
        "selected_item_id": str(selected["item_id"]),
        "selected_family": str(selected["family"]),
        "selection_reason": "operational pass first; prefer PP41 MAPE improvement with p95 not worse than PP7; fallback to p95-safe recommendation score",
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
    return decision


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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    refs = metrics[
        metrics["eval_split"].eq("test")
        & metrics["candidate"].isin([INCUMBENT, PREV_CHALLENGER, "reference_pp23", "reference_pp30_best", "reference_pp36_challenger", "reference_pp38_best", "reference_pp41_challenger"])
    ][["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("MAPE")
    selected_metrics = metrics[metrics["candidate"].eq(decision["selected_candidate"])][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    top_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"]).head(40)
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
    pp41 = refs[refs["candidate"].eq("reference_pp41_challenger")]
    selected_test = selected_metrics[selected_metrics["eval_split"].eq("test")]
    if not pp41.empty and not selected_test.empty:
        verdict = (
            f"선택 후보는 PP41 대비 MAPE {float(selected_test.iloc[0]['MAPE']) - float(pp41.iloc[0]['MAPE']):+.6f}, "
            f"p95 {float(selected_test.iloc[0]['p95_APE']) - float(pp41.iloc[0]['p95_APE']):+.6f}이다."
        )
    else:
        verdict = "선택 후보를 산출했다."

    md = "\n".join(
        [
            "# PP-OPT42~46 Warm 잔차 보정 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            "- 비교 후보: PP20, PP23, PP30, PP36, PP38, PP41",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## 선택 후보",
            f"- 선택 후보: `{decision['selected_candidate']}`",
            f"- 원본 실험: `{decision['selected_item_id']}` / `{decision['selected_family']}`",
            f"- 판단: {verdict}",
            markdown_table(selected_metrics, list(selected_metrics.columns), 10),
            "",
            "## 주요 reference test 비교",
            markdown_table(refs, list(refs.columns), 20),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## 전체 MAPE 상위 후보",
            markdown_table(top_mape, result_cols, 40),
            "",
            "## MAPE와 p95 동시 개선 후보",
            markdown_table(both, result_cols, 40),
            "",
            "## 해석",
            "이번 배치는 기존 후보 블렌드가 아니라 남은 잔차 자체를 보정했다. 선택 후보가 PP41보다 명확히 좋아지지 않으면 잔차 보정은 운영 반영보다 분석용으로 유지하는 것이 안전하다.",
            "구간 중앙값과 quantile 잔차 보정이 안정적으로 작동하면 다음 단계는 해당 보정을 더 작은 cap으로 freeze하는 것이다.",
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
  <title>PP-OPT42~46 Warm 잔차 보정 실험 결과</title>
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
  <h1>PP-OPT42~46 Warm 잔차 보정 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>선택 후보: <code>{html.escape(decision['selected_candidate'])}</code></div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision['test_delta_vs_incumbent_MAPE']:.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision['test_delta_vs_incumbent_p95_APE']:.6f}</div>
  </div>

  <h2>1. 선택 후보</h2>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}

  <h2>2. 주요 reference test 비교</h2>
  {table_html(refs, list(refs.columns), 20)}

  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>4. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}

  <h2>5. 전체 MAPE 상위 후보</h2>
  {table_html(top_mape, result_cols, 40)}

  <h2>6. MAPE와 p95 동시 개선 후보</h2>
  {table_html(both, result_cols, 40)}

  <h2>7. 해석</h2>
  <p>이번 배치는 기존 후보 블렌드가 아니라 남은 잔차 자체를 보정했다. 선택 후보가 PP41보다 명확히 좋아지지 않으면 잔차 보정은 운영 반영보다 분석용으로 유지하는 것이 안전하다.</p>
  <p>구간 중앙값과 quantile 잔차 보정이 안정적으로 작동하면 다음 단계는 해당 보정을 더 작은 cap으로 freeze하는 것이다.</p>

  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    pp37_config = load_pp37_config()
    selected_references = select_reference_candidates()
    ref = load_reference_predictions(base, selected_references)

    center = ref["pp41"].to_numpy(dtype=float)
    under_prob, over_prob, direction_detail = sign_probabilities(base, center, margin=0.045)
    quant_pp41 = opt21.oof_lgbm_quantile_residual(base, center)
    quant_by_center = {
        "pp41": quant_pp41,
        "pp23": opt21.oof_lgbm_quantile_residual(base, ref["pp23"].to_numpy(dtype=float)),
        "pp38_score": opt21.oof_lgbm_quantile_residual(base, ref["pp38_score"].to_numpy(dtype=float)),
    }

    references = add_reference_candidates(base, ref)
    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt42_directional_asymmetric_cap(base, ref, quant_pp41, (under_prob, over_prob)))
    candidates.extend(pp_opt43_segment_median_shrinkage(base, ref))
    candidates.extend(pp_opt44_quantile_residual(base, ref, quant_by_center))
    candidates.extend(pp_opt45_high_price_fallback(base, ref))
    candidates.extend(pp_opt46_monotonic_cap(base, ref, quant_pp41))

    predictions = pd.concat([source] + references + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    decision = select_best_candidate(metrics, aggregate)

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
        "selected_references": selected_references,
        "selection_decision": decision,
        "sources": {
            "pp_opt37_config": pp37_config.get("experiment_slug", "PP-OPT37_41"),
            "pp_opt37_predictions": str(PP37_PREDS.relative_to(REPO)),
            "pp_opt37_aggregate": str(PP37_AGG.relative_to(REPO)),
            "pp_opt37_helper": str(OPT37_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    direction_detail.to_csv(ARTIFACT_DIR / "direction_probability_detail.csv", index=False)
    quant_artifact = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            **{f"pp41_{k}": v for k, v in quant_pp41.items()},
        }
    )
    quant_artifact.to_csv(ARTIFACT_DIR / "pp41_quantile_residual_predictions.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "residual_correction_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "residual_correction_result.html").write_text(report_html, encoding="utf-8")

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
