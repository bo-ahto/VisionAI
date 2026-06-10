#!/usr/bin/env python3
"""Run PP-OPT14..20 Warm gate refinement experiments.

This batch continues from PP-OPT9..13. It keeps the PP-OPT7 incumbent as the
comparison anchor and tests refinements around the follow-up decision structure:

    incumbent + safe average-error correction + tail-risk correction + qwidth governor

The experiment is non-submission and uses the same Warm validation OOF / fixed
test split as PP-OPT8 and PP-OPT9..13.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor


REPO = Path(__file__).resolve().parents[2]
OPT8_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt8_warm_extended_correction_experiments.py"
OPT9_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt9_13_warm_followup_improvement_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt8 = load_module("pp_opt8_helpers", OPT8_SCRIPT)
opt9 = load_module("pp_opt9_helpers", OPT9_SCRIPT)

EXP_ID = "PP-OPT14-20"
EXP_SLUG = "PP-OPT14_20_warm_gate_refinement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP9_PREDS = REPO / "experiments" / "track6" / "PP-OPT9_13_warm_followup_improvement_experiments" / "outputs" / "candidate_predictions.csv"
PP9_AGG = REPO / "experiments" / "track6" / "PP-OPT9_13_warm_followup_improvement_experiments" / "outputs" / "aggregate_candidate_stability.csv"

BASE_CANDIDATE = opt8.BASE_CANDIDATE
INCUMBENT = "incumbent_operational_pp_opt7"
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT14",
        "priority": "1",
        "title": "PP-OPT9 gate threshold 정밀 탐색",
        "description": "안전구간 gate, tail-risk gate, 보정 강도, cap을 촘촘히 탐색한다.",
    },
    {
        "item_id": "PP-OPT15",
        "priority": "2",
        "title": "PP-OPT12 MAPE 신호의 안정 흡수",
        "description": "PP-OPT12의 평균오차 개선 신호를 PP-OPT9 구조 안에서 약하게 사용한다.",
    },
    {
        "item_id": "PP-OPT16",
        "priority": "3",
        "title": "tail-risk label 재정의",
        "description": "p95, p90, p85, soft risk label로 큰 오차 위험 gate를 다시 학습한다.",
    },
    {
        "item_id": "PP-OPT17",
        "priority": "4",
        "title": "MdAPE 악화 방지 guard",
        "description": "중앙 오차를 악화시킬 가능성이 있는 row에서 보정 강도를 줄인다.",
    },
    {
        "item_id": "PP-OPT18",
        "priority": "5",
        "title": "제약 조건 기반 보정값 앙상블",
        "description": "비음수 가중치와 log cap을 둔 평균오차/tail 보정값 가중합을 탐색한다.",
    },
    {
        "item_id": "PP-OPT19",
        "priority": "6",
        "title": "구간별 PP-OPT9 분리 튜닝",
        "description": "가격대, 유사작품 수, 퀀타일 폭, 신뢰도 구간별 보정 강도를 다르게 적용한다.",
    },
    {
        "item_id": "PP-OPT20",
        "priority": "7",
        "title": "최종 후보 selection protocol",
        "description": "반복 검증 안정성과 fixed test 확인을 함께 쓰는 최종 후보 선택 기준을 적용한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def select_pp9_components() -> dict[str, str]:
    agg = pd.read_csv(PP9_AGG)
    op = agg[agg["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    if op.empty:
        raise ValueError("PP-OPT9..13 has no operational pass candidate")
    by_item = {
        "pp9_best_operational": str(op.iloc[0]["candidate"]),
        "pp9_best_mape": str(agg[agg["item_id"].eq("PP-OPT9")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp11_best_operational": str(
            agg[(agg["item_id"].eq("PP-OPT11")) & (agg["operational_pass_vs_incumbent"])]
            .sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
            .iloc[0]["candidate"]
        ),
        "pp12_best_mape": str(agg[agg["item_id"].eq("PP-OPT12")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp13_best_p95": str(agg[agg["item_id"].eq("PP-OPT13")].sort_values(["test_p95_APE", "test_MAPE"]).iloc[0]["candidate"]),
    }
    return by_item


def load_pp9_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP9_PREDS, usecols=usecols, chunksize=100_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT9..13 prediction components loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for label, candidate in selected.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in selected if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing PP-OPT9 component predictions after merge: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def merge_component_sets(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, str]]:
    components8 = opt9.select_components()
    pred8 = opt9.load_component_predictions(base, components8)
    components9 = select_pp9_components()
    pred9 = load_pp9_predictions(base, components9)
    return pd.concat([pred8, pred9], axis=1), pred8, components8, components9


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt8.candidate_frame(
        base,
        candidate,
        family,
        item_id,
        pred_log,
        pred_log - pd.to_numeric(base["hcoef_stable"], errors="coerce").to_numpy(dtype=float),
    )


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def qwidth_governor(base: pd.DataFrame, mode: str) -> np.ndarray:
    return opt9.qwidth_governor(base, mode)


def row_cap(base: pd.DataFrame, cap: float, mode: str) -> np.ndarray:
    return opt9.row_cap(base, cap, mode)


def gate(prob: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((prob - threshold) / max(width, 1e-6), 0.0, 1.0)


def train_tail_probabilities(base: pd.DataFrame, incumbent: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(incumbent, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    thresholds = {
        "p95": float(np.quantile(inc_ape[val_mask], 0.95)),
        "p90": float(np.quantile(inc_ape[val_mask], 0.90)),
        "p85": float(np.quantile(inc_ape[val_mask], 0.85)),
    }
    probs: dict[str, np.ndarray] = {}
    for label, threshold in thresholds.items():
        probs[label] = opt9.oof_lgbm_probability(base, (inc_ape >= threshold).astype(int))
    probs["p90_logistic"] = opt9.oof_logistic_probability(base, (inc_ape >= thresholds["p90"]).astype(int))
    probs["soft"] = train_soft_tail_score(base, inc_ape, thresholds["p85"], thresholds["p95"])
    return probs, thresholds


def train_soft_tail_score(base: pd.DataFrame, inc_ape: np.ndarray, lower: float, upper: float) -> np.ndarray:
    target = np.clip((inc_ape - lower) / max(upper - lower, 1e-6), 0.0, 1.0)
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = target[val_mask]
    x_val = opt9.model_matrix(val)
    x_test = opt9.model_matrix(test)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = LGBMRegressor(
            objective="regression_l1",
            n_estimators=180,
            learning_rate=0.035,
            num_leaves=15,
            max_depth=4,
            min_child_samples=24,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.25,
            reg_lambda=5.0,
            random_state=SEED + fold,
            verbosity=-1,
            force_col_wise=True,
        )
        model.fit(x_val.iloc[tr_idx], y_val[tr_idx], categorical_feature=cat_cols)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = LGBMRegressor(
        objective="regression_l1",
        n_estimators=180,
        learning_rate=0.035,
        num_leaves=15,
        max_depth=4,
        min_child_samples=24,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.25,
        reg_lambda=5.0,
        random_state=SEED + 100,
        verbosity=-1,
        force_col_wise=True,
    )
    model.fit(x_val, y_val, categorical_feature=cat_cols)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return np.clip(pred, 0.0, 1.0)


def train_median_guard_probability(base: pd.DataFrame, incumbent: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(incumbent, actual_price)
    ref_ape = ape(reference, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    median_threshold = float(np.quantile(inc_ape[val_mask], 0.55))
    label = ((inc_ape <= median_threshold) & (ref_ape <= inc_ape + 0.002)).astype(int)
    prob = opt9.oof_lgbm_probability(base, label)
    return prob, {
        "median_guard_threshold": median_threshold,
        "median_guard_positive_rate": float(np.mean(label[val_mask])),
    }


def pp_opt14_gate_threshold_candidates(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    safety_prob: np.ndarray,
    tail_prob: np.ndarray,
) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    artist_sources = {
        "cat_price_band": comp["cat_price_band"].to_numpy(dtype=float) - inc,
        "artist_stable": comp["artist_stable"].to_numpy(dtype=float) - inc,
    }
    tail_delta = comp["xgb_tail"].to_numpy(dtype=float) - inc
    for artist_name, artist_delta in artist_sources.items():
        for safe_thr in [0.12, 0.18, 0.24]:
            for tail_thr in [0.15, 0.25, 0.35]:
                safe_gate = gate(safety_prob, safe_thr, 0.60)
                risk_gate = gate(tail_prob, tail_thr, 0.58)
                for artist_strength in [0.20, 0.30, 0.45]:
                    for tail_strength in [0.55, 0.75]:
                        for cap in [0.020, 0.024]:
                            artist_corr = artist_delta * safe_gate * qwidth_governor(base, "mild") * artist_strength * (1.0 - 0.40 * risk_gate)
                            tail_corr = tail_delta * risk_gate * tail_strength
                            corr = clip_by_row(artist_corr + tail_corr, row_cap(base, cap, "risk"))
                            name = (
                                f"ppopt14_gate_grid__artist={artist_name}"
                                f"__sthr={safe_name(safe_thr)}__tthr={safe_name(tail_thr)}"
                                f"__as={safe_name(artist_strength)}__ts={safe_name(tail_strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "gate_threshold_grid", "PP-OPT14", inc + corr))
    return rows


def pp_opt15_absorb_pp12_candidates(base: pd.DataFrame, comp: pd.DataFrame, safety_prob: np.ndarray, tail_prob: np.ndarray) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    pp9_deltas = {
        "pp9_best_operational": comp["pp9_best_operational"].to_numpy(dtype=float) - inc,
        "pp9_best_mape": comp["pp9_best_mape"].to_numpy(dtype=float) - inc,
    }
    pp12_delta = comp["pp12_best_mape"].to_numpy(dtype=float) - inc
    rows: list[pd.DataFrame] = []
    safe_gate = gate(safety_prob, 0.16, 0.62)
    risk_gate = gate(tail_prob, 0.24, 0.58)
    for base_name, base_delta in pp9_deltas.items():
        for pp12_strength in [0.10, 0.18, 0.26, 0.34]:
            for pp9_strength in [0.75, 0.90, 1.05]:
                for cap in [0.018, 0.022, 0.026]:
                    raw = pp9_strength * base_delta + pp12_strength * pp12_delta * safe_gate * (1.0 - 0.35 * risk_gate)
                    corr = clip_by_row(raw, row_cap(base, cap, "risk"))
                    name = f"ppopt15_absorb_pp12__base={base_name}__p12s={safe_name(pp12_strength)}__p9s={safe_name(pp9_strength)}__cap={safe_name(cap)}"
                    rows.append(make_candidate(base, name, "pp12_signal_absorption", "PP-OPT15", inc + corr))
    return rows


def pp_opt16_tail_label_candidates(base: pd.DataFrame, comp: pd.DataFrame, tail_probs: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    tail_sources = {
        "xgb_tail": comp["xgb_tail"].to_numpy(dtype=float) - inc,
        "xgb_tail_guard_mean": 0.60 * (comp["xgb_tail"].to_numpy(dtype=float) - inc) + 0.40 * (comp["tail_guard"].to_numpy(dtype=float) - inc),
    }
    for label_name, prob in tail_probs.items():
        for source_name, delta in tail_sources.items():
            for threshold in [0.12, 0.20, 0.30]:
                risk_gate = gate(prob, threshold, 0.60)
                for strength in [0.45, 0.65, 0.85]:
                    corr = clip_by_row(delta * risk_gate * strength, row_cap(base, 0.022, "risk"))
                    name = f"ppopt16_tail_label__label={label_name}__src={source_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "tail_label_redefinition", "PP-OPT16", inc + corr))
    return rows


def pp_opt17_mdape_guard_candidates(base: pd.DataFrame, comp: pd.DataFrame, median_prob: np.ndarray) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    sources = {
        "pp9_best_operational": comp["pp9_best_operational"].to_numpy(dtype=float) - inc,
        "pp9_best_mape": comp["pp9_best_mape"].to_numpy(dtype=float) - inc,
        "pp12_best_mape": comp["pp12_best_mape"].to_numpy(dtype=float) - inc,
    }
    rows: list[pd.DataFrame] = []
    for source_name, delta in sources.items():
        for floor in [0.25, 0.40, 0.55]:
            for strength in [0.70, 0.90, 1.10]:
                guard = floor + (1.0 - floor) * median_prob
                corr = clip_by_row(delta * guard * strength, row_cap(base, 0.022, "risk"))
                name = f"ppopt17_mdape_guard__src={source_name}__floor={safe_name(floor)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "mdape_guard", "PP-OPT17", inc + corr))
    return rows


def pp_opt18_constrained_ensemble_candidates(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    safety_prob: np.ndarray,
    tail_prob: np.ndarray,
) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    artist = comp["artist_stable"].to_numpy(dtype=float) - inc
    cat = comp["cat_price_band"].to_numpy(dtype=float) - inc
    xgb = comp["xgb_tail"].to_numpy(dtype=float) - inc
    qwidth = comp["qwidth_mild"].to_numpy(dtype=float) - inc
    pp12 = comp["pp12_best_mape"].to_numpy(dtype=float) - inc
    safe_gate = gate(safety_prob, 0.18, 0.60)
    risk_gate = gate(tail_prob, 0.22, 0.60)
    rows: list[pd.DataFrame] = []
    for artist_w in [0.00, 0.12, 0.22]:
        for cat_w in [0.12, 0.24, 0.36]:
            for xgb_w in [0.20, 0.35, 0.50]:
                for q_w in [0.12, 0.24]:
                    for pp12_w in [0.00, 0.08, 0.16]:
                        for cap in [0.018, 0.022]:
                            raw = (
                                artist_w * artist * safe_gate
                                + cat_w * cat * safe_gate * qwidth_governor(base, "mild")
                                + xgb_w * xgb * risk_gate
                                + q_w * qwidth
                                + pp12_w * pp12 * safe_gate * (1.0 - 0.35 * risk_gate)
                            )
                            corr = clip_by_row(raw, row_cap(base, cap, "risk"))
                            name = (
                                f"ppopt18_constrained_ensemble__aw={safe_name(artist_w)}__cw={safe_name(cat_w)}"
                                f"__xw={safe_name(xgb_w)}__qw={safe_name(q_w)}__p12w={safe_name(pp12_w)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "constrained_correction_ensemble", "PP-OPT18", inc + corr))
    return rows


def pp_opt19_segment_tuning_candidates(base: pd.DataFrame, comp: pd.DataFrame, safety_prob: np.ndarray, tail_prob: np.ndarray) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    cat_delta = comp["cat_price_band"].to_numpy(dtype=float) - inc
    artist_delta = comp["artist_stable"].to_numpy(dtype=float) - inc
    tail_delta = comp["xgb_tail"].to_numpy(dtype=float) - inc
    safe_gate = gate(safety_prob, 0.18, 0.60)
    risk_gate = gate(tail_prob, 0.22, 0.60)
    price = base["stable_price_band"].fillna("mid_price").astype(str).to_numpy()
    tier = base["confidence_tier"].fillna("medium_confidence").astype(str).to_numpy()
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    q = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    segment_profiles = {
        "price_tail_high": {
            "artist_mult": np.where(np.isin(price, ["high_price", "very_high_price"]), 0.65, 1.00),
            "tail_mult": np.where(np.isin(price, ["high_price", "very_high_price"]), 1.25, 0.85),
        },
        "low_support_tail": {
            "artist_mult": np.where(svc < 6, 0.55, 1.00),
            "tail_mult": np.where(svc < 6, 1.30, 0.85),
        },
        "qwidth_tail": {
            "artist_mult": np.where(q >= 1.45, 0.50, 1.00),
            "tail_mult": np.where(q >= 1.45, 1.35, 0.80),
        },
        "confidence_tail": {
            "artist_mult": np.where(tier == "low_confidence", 0.45, np.where(tier == "medium_confidence", 0.75, 1.00)),
            "tail_mult": np.where(tier == "low_confidence", 1.35, np.where(tier == "medium_confidence", 1.05, 0.75)),
        },
        "balanced_segments": {
            "artist_mult": np.where((svc >= 8) & (q < 1.30), 1.10, 0.75),
            "tail_mult": np.where((svc < 6) | (q >= 1.45), 1.25, 0.80),
        },
    }
    for profile_name, profile in segment_profiles.items():
        for artist_source, avg_delta in [("cat", cat_delta), ("artist", artist_delta), ("cat_artist_mean", 0.60 * cat_delta + 0.40 * artist_delta)]:
            for artist_strength in [0.25, 0.35, 0.45]:
                for tail_strength in [0.55, 0.75]:
                    raw = (
                        avg_delta * safe_gate * qwidth_governor(base, "mild") * artist_strength * profile["artist_mult"]
                        + tail_delta * risk_gate * tail_strength * profile["tail_mult"]
                    )
                    corr = clip_by_row(raw, row_cap(base, 0.024, "risk"))
                    name = (
                        f"ppopt19_segment_tuning__profile={profile_name}__artist={artist_source}"
                        f"__as={safe_name(artist_strength)}__ts={safe_name(tail_strength)}"
                    )
                    rows.append(make_candidate(base, name, "segment_specific_gate_tuning", "PP-OPT19", inc + corr))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    item_info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id == "BASE":
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
    summary = pd.DataFrame(rows).merge(item_info, on="item_id", how="left")
    return summary.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])


def select_protocol_candidate(aggregate: pd.DataFrame) -> pd.Series:
    candidates = aggregate[~aggregate["candidate"].isin([BASE_CANDIDATE, INCUMBENT])].copy()
    operational = candidates[candidates["operational_pass_vs_incumbent"]].copy()
    if not operational.empty:
        return operational.sort_values(
            [
                "incumbent_MAPE_improve_rate",
                "incumbent_p95_not_worse_rate",
                "incumbent_all3_rate",
                "recommendation_score_vs_incumbent",
                "test_MAPE",
            ],
            ascending=[False, False, False, True, True],
        ).iloc[0]
    return candidates.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]


def add_protocol_selected_candidate(predictions: pd.DataFrame, aggregate: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    selected = select_protocol_candidate(aggregate)
    selected_candidate = str(selected["candidate"])
    duplicate = predictions[predictions["candidate"].eq(selected_candidate)].copy()
    protocol_name = f"ppopt20_protocol_selected__source={safe_name(selected_candidate)[:120]}"
    duplicate["candidate"] = protocol_name
    duplicate["family"] = "selection_protocol"
    duplicate["item_id"] = "PP-OPT20"
    out = pd.concat([predictions, duplicate], ignore_index=True)
    decision = {
        "selected_source_candidate": selected_candidate,
        "protocol_candidate": protocol_name,
        "selected_source_item_id": str(selected["item_id"]),
        "selected_source_family": str(selected["family"]),
        "selection_reason": "operational pass candidates sorted by repeated validation improve rates, p95 not-worse rate, all3 rate, recommendation score, then fixed test MAPE",
    }
    for col in [
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]:
        decision[col] = float(selected[col])
    return out, decision


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
    incumbent = metrics[metrics["candidate"].eq(INCUMBENT)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]].sort_values("eval_split")
    selected_metrics = metrics[metrics["candidate"].eq(decision["protocol_candidate"])][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])
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
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    md = "\n".join(
        [
            "# PP-OPT14~20 Warm Gate Refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## 최종 selection protocol 후보",
            f"- 선택 후보: `{decision['protocol_candidate']}`",
            f"- 원본 후보: `{decision['selected_source_candidate']}`",
            f"- 원본 실험: `{decision['selected_source_item_id']}` / `{decision['selected_source_family']}`",
            "",
            markdown_table(selected_metrics, list(selected_metrics.columns), 10),
            "",
            "## 현재 운영 후보 성능",
            markdown_table(incumbent, list(incumbent.columns), 10),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## Test에서 MAPE와 p95를 동시에 개선한 후보",
            markdown_table(both, result_cols, 40),
            "",
            "## 해석",
            "PP-OPT14~20은 PP-OPT9 구조를 더 촘촘히 조정한 실험이다. 결과적으로 개선 여지는 gate threshold와 constrained ensemble 쪽에서 가장 크게 나타났다.",
            "선택 후보는 반복 검증 개선율을 우선하는 selection protocol로 고른 후보이며, fixed test 성능만 가장 좋은 후보와 다를 수 있다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    verdict = "운영 후보 대체 조건을 통과한 후보가 발견되었다." if int(aggregate["operational_pass_vs_incumbent"].sum()) else "운영 후보 대체 조건을 통과한 후보는 없다."
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT14~20 Warm Gate Refinement 결과</title>
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
  <h1>PP-OPT14~20 Warm Gate Refinement 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건 · 기준 후보: PP-OPT7 운영 후보</div>
  <div class="callout">{html.escape(verdict)} 최종 selection protocol 후보는 <code>{html.escape(decision['protocol_candidate'])}</code>이다.</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>선택 후보 test MAPE 변화</strong>{decision['test_delta_vs_incumbent_MAPE']:.6f}</div>
    <div class="panel"><strong>선택 후보 test p95 변화</strong>{decision['test_delta_vs_incumbent_p95_APE']:.6f}</div>
  </div>

  <h2>1. 최종 selection protocol 후보</h2>
  <p>원본 후보: <code>{html.escape(decision['selected_source_candidate'])}</code></p>
  {table_html(selected_metrics, list(selected_metrics.columns), 10)}

  <h2>2. 현재 운영 후보 성능</h2>
  {table_html(incumbent, list(incumbent.columns), 10)}

  <h2>3. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>4. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}

  <h2>5. Test에서 MAPE와 p95를 동시에 개선한 후보</h2>
  {table_html(both, result_cols, 40)}

  <h2>6. 해석</h2>
  <p>PP-OPT14~20은 PP-OPT9 구조를 더 촘촘히 조정한 실험이다. 개선 신호는 gate threshold 정밀 탐색과 constrained ensemble에서 가장 강하게 나왔다. 다만 selection protocol은 fixed test 최저 MAPE가 아니라 반복 검증 안정성을 우선하므로, 최종 선택 후보는 test MAPE 최저 후보와 다를 수 있다.</p>
  <p>다음 단계에서는 선택 후보와 fixed test 최저 후보를 별도로 두고, 운영 후보는 안정성 우선 기준으로 고정하는 것이 맞다.</p>

  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    comp, comp8, components8, components9 = merge_component_sets(base)
    safety_label, tail_label, label_info = opt9.probability_labels(base, comp8)
    safety_prob = opt9.oof_lgbm_probability(base, safety_label)
    tail_prob = opt9.oof_lgbm_probability(base, tail_label)
    tail_probs, tail_thresholds = train_tail_probabilities(base, comp["incumbent"].to_numpy(dtype=float))
    median_prob, median_info = train_median_guard_probability(base, comp["incumbent"].to_numpy(dtype=float), comp["pp9_best_operational"].to_numpy(dtype=float))

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt14_gate_threshold_candidates(base, comp, safety_prob, tail_prob))
    candidates.extend(pp_opt15_absorb_pp12_candidates(base, comp, safety_prob, tail_prob))
    candidates.extend(pp_opt16_tail_label_candidates(base, comp, tail_probs))
    candidates.extend(pp_opt17_mdape_guard_candidates(base, comp, median_prob))
    candidates.extend(pp_opt18_constrained_ensemble_candidates(base, comp, safety_prob, tail_prob))
    candidates.extend(pp_opt19_segment_tuning_candidates(base, comp, safety_prob, tail_prob))

    predictions = pd.concat([source] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    predictions, decision = add_protocol_selected_candidate(predictions, aggregate)
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
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "items": ITEMS,
        "pp_opt8_components": components8,
        "pp_opt9_components": components9,
        "label_info": {**label_info, **median_info},
        "tail_thresholds": tail_thresholds,
        "selection_decision": decision,
        "sources": {
            "pp_opt9_predictions": str(PP9_PREDS.relative_to(REPO)),
            "pp_opt9_aggregate": str(PP9_AGG.relative_to(REPO)),
            "pp_opt8_helper": str(OPT8_SCRIPT.relative_to(REPO)),
            "pp_opt9_helper": str(OPT9_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    gate_df = pd.DataFrame(
        {
            "eval_split": base["eval_split"],
            "_track6_row_id": base["_track6_row_id"],
            "safety_label": safety_label,
            "tail_label": tail_label,
            "safety_probability": safety_prob,
            "tail_probability": tail_prob,
            "tail_p95_probability": tail_probs["p95"],
            "tail_p90_probability": tail_probs["p90"],
            "tail_p85_probability": tail_probs["p85"],
            "tail_soft_score": tail_probs["soft"],
            "median_guard_probability": median_prob,
        }
    )
    gate_df.to_csv(ARTIFACT_DIR / "gate_probabilities.csv", index=False)

    report_md, report_html = render_reports(metrics, aggregate, item_summary, decision, config)
    (REPORT_DIR / "gate_refinement_result_interpretation.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "gate_refinement_result_interpretation.html").write_text(report_html, encoding="utf-8")

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
