#!/usr/bin/env python3
"""Run PP-OPT173..180 Warm basis-generation challenger experiments."""
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
PP167_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt167_172_warm_pp166_second_stage_tail_calibration.py"
PP167_DIR = REPO / "experiments" / "track6" / "PP-OPT167_172_warm_pp166_second_stage_tail_calibration"
PP167_PREDICTIONS = PP167_DIR / "outputs" / "candidate_predictions.csv"
PP167_STABILITY = PP167_DIR / "outputs" / "selected_stability_candidate_aggregate.csv"
PP167_CONFIG = PP167_DIR / "artifacts" / "run_config.json"
PP161_DIR = REPO / "experiments" / "track6" / "PP-OPT161_166_warm_pp157_negative_gate_rollback"
DIRECT_META_DETAIL = PP161_DIR / "artifacts" / "direct_meta_prediction_detail.csv"

EXP_ID = "PP-OPT173-180"
EXP_SLUG = "PP-OPT173_180_warm_basis_generation_challenger"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

EPS = 1e-12
BASE_CANDIDATE = "hcoef_stable"
INCUMBENT_CANDIDATE = "incumbent_operational_pp_opt7"
PP64_CANDIDATE = "reference_pp64_current_best"
PP70_CANDIDATE = "reference_pp70_refinement"
PP126_CANDIDATE = "reference_pp126_operational"
PP148_CANDIDATE = "reference_pp148_operational"
PP148_P95_CANDIDATE = "reference_pp148_p95"

ITEMS = [
    {
        "item_id": "PP-OPT173",
        "priority": "1",
        "title": "segment residual basis",
        "description": "validation OOF residual을 가격대/신뢰도/작품 메타 구간별로 집계해 새 기준 로그가격을 만든다.",
    },
    {
        "item_id": "PP-OPT174",
        "priority": "2",
        "title": "direct model basis routing",
        "description": "LightGBM/CatBoost/XGBoost/Huber 직접 예측을 기준가 후보로 두고 구간별 우세 구간에서만 적용한다.",
    },
    {
        "item_id": "PP-OPT175",
        "priority": "3",
        "title": "quantile basis with uncertainty guard",
        "description": "LightGBM quantile 기준가의 폭이 좁은 구간에서만 q50/huber 기준가 이동분을 적용한다.",
    },
    {
        "item_id": "PP-OPT176",
        "priority": "4",
        "title": "model consensus basis",
        "description": "여러 direct basis가 같은 방향으로 움직일 때만 평균 기준가 이동을 허용한다.",
    },
    {
        "item_id": "PP-OPT177",
        "priority": "5",
        "title": "basis-to-PP172 correction",
        "description": "새 기준가를 중심으로 두고 PP172를 안정 보정 후보로 되돌리는 구조를 검증한다.",
    },
    {
        "item_id": "PP-OPT178",
        "priority": "6",
        "title": "basis family router",
        "description": "segment residual basis, direct basis, PP172 중 validation 구간 성과가 좋은 family를 라우팅한다.",
    },
    {
        "item_id": "PP-OPT179",
        "priority": "7",
        "title": "basis micro calibration",
        "description": "상위 basis 후보의 threshold/cap 주변만 좁게 재검증한다.",
    },
    {
        "item_id": "PP-OPT180",
        "priority": "8",
        "title": "final basis-generation decision",
        "description": "PP172와 새 basis-generation 후보를 fixed/repeated 기준으로 비교해 최종 판단한다.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp167 = load_module("pp_opt167_helpers_for_pp173", PP167_SCRIPT)
pp161 = pp167.pp161
opt8 = pp167.opt8
val71 = pp167.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp167.safe_name(value)


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    actual = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    return np.abs(safe_exp(pred_log) - actual) / np.maximum(actual, EPS)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp167.make_candidate(base, candidate, family, item_id, pred_log)


def load_previous() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if not PP167_PREDICTIONS.exists():
        raise FileNotFoundError(f"Required PP167 predictions not found: {PP167_PREDICTIONS}")
    predictions = pd.read_csv(PP167_PREDICTIONS)
    stability = pd.read_csv(PP167_STABILITY)
    config = json.loads(PP167_CONFIG.read_text(encoding="utf-8"))
    return predictions, stability, config


def base_frame(predictions: pd.DataFrame) -> pd.DataFrame:
    base = predictions[predictions["candidate"].eq(BASE_CANDIDATE)].copy()
    if base.empty:
        raise RuntimeError(f"Base candidate not found: {BASE_CANDIDATE}")
    return base.sort_values(["eval_split", "_track6_row_id"]).reset_index(drop=True)


def prediction_array(predictions: pd.DataFrame, base: pd.DataFrame, candidate: str) -> np.ndarray:
    keys = ["eval_split", "_track6_row_id"]
    sub = predictions[predictions["candidate"].eq(candidate)][keys + ["pred_log"]].copy()
    if sub.empty:
        raise RuntimeError(f"Candidate not found: {candidate}")
    merged = base[keys].merge(sub, on=keys, how="left")
    if merged["pred_log"].isna().any():
        missing = int(merged["pred_log"].isna().sum())
        raise RuntimeError(f"Candidate {candidate} missing {missing} rows")
    return merged["pred_log"].to_numpy(dtype=float)


def choose_support_candidates(pp167_config: dict[str, Any]) -> dict[str, str]:
    decision = pp167_config["selection_decision"]
    support = dict(pp167_config["support_candidates"])
    support.update(
        {
            "pp172_operational": decision["operational_protocol_candidate"],
            "pp172_p95": decision["p95_protocol_candidate"],
            "pp148_operational": PP148_CANDIDATE,
            "pp148_p95": PP148_P95_CANDIDATE,
        }
    )
    return support


def add_raw_model_features(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_base, _source, _ref, _labels, model_detail, _selected_refs, _parent_config, _selected_pp119 = pp161.pp135.load_inputs()
    keys = ["eval_split", "_track6_row_id"]
    raw_cols = [
        "eval_split",
        "_track6_row_id",
        "medium_support_bucket",
        "svc_coverage_tier",
        "svc_group_level",
        "service_confidence_tier",
        "qwidth_band",
        "svc_group_n_band",
        "gap_band",
        "pred_spread_band",
        "area_bin",
    ]
    enriched = base.merge(raw_base[raw_cols].drop_duplicates(keys), on=keys, how="left", suffixes=("", "_raw"))
    for col in ["medium_support_bucket", "svc_coverage_tier", "svc_group_level", "service_confidence_tier", "qwidth_band", "svc_group_n_band", "gap_band", "pred_spread_band", "area_bin"]:
        if col not in enriched:
            enriched[col] = "missing"
        enriched[col] = enriched[col].astype(str).fillna("missing")
    model = model_detail.copy()
    if DIRECT_META_DETAIL.exists():
        direct_meta = pd.read_csv(DIRECT_META_DETAIL)
        model = model.merge(direct_meta, on=keys, how="left", suffixes=("", "_meta"))
    return enriched, model


def align_model_detail(base: pd.DataFrame, model_detail: pd.DataFrame) -> pd.DataFrame:
    keys = ["eval_split", "_track6_row_id"]
    merged = base[keys].merge(model_detail, on=keys, how="left")
    missing_cols = [col for col in model_detail.columns if col not in keys and merged[col].isna().any()]
    if missing_cols:
        raise RuntimeError(f"Model detail has missing values after alignment: {missing_cols[:8]}")
    return merged


def segment_score(
    base: pd.DataFrame,
    reference: np.ndarray,
    candidate: np.ndarray,
    segment_cols: list[str],
    harm_weight: float = 1.0,
    min_count: int = 10,
) -> np.ndarray:
    ref_ape = ape_from_log(base, reference)
    cand_ape = ape_from_log(base, candidate)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    gain = (cand_ape + 0.0008 < ref_ape).astype(float)
    harm = (cand_ape > ref_ape + 0.0008).astype(float)
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_score = float(np.mean(gain[val_mask]) - harm_weight * np.mean(harm[val_mask]))
    scores: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() >= min_count:
            scores[key] = float(np.mean(gain[idx]) - harm_weight * np.mean(harm[idx]))
    return seg.map(scores).fillna(global_score).to_numpy(dtype=float)


def leave_one_out_segment_residual(
    base: pd.DataFrame,
    reference: np.ndarray,
    segment_cols: list[str],
    shrink: float,
) -> np.ndarray:
    residual = pd.to_numeric(base["actual_log"], errors="coerce").to_numpy(dtype=float) - reference
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    train = pd.DataFrame({"seg": seg[val_mask].to_numpy(), "residual": residual[val_mask]})
    stats = train.groupby("seg")["residual"].agg(["sum", "count"])
    global_adj = float(train["residual"].sum() / (len(train) + shrink))
    out = np.full(len(base), global_adj, dtype=float)
    for i, key in enumerate(seg):
        if key not in stats.index:
            continue
        total = float(stats.loc[key, "sum"])
        count = int(stats.loc[key, "count"])
        if val_mask[i]:
            n = count - 1
            if n <= 0:
                out[i] = global_adj
            else:
                out[i] = (total - residual[i]) / (n + shrink)
        else:
            out[i] = total / (count + shrink)
    return out


def tail_score(base: pd.DataFrame) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(base["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(base["component_prediction_spread"], errors="coerce"))
    gap = rank01(pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce"))
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0, 1)
    low_conf = base["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    return np.clip(0.28 * qwidth + 0.22 * price_range + 0.18 * spread + 0.14 * gap + 0.10 * low_sample + 0.08 * low_conf, 0, 1)


def pp_opt173_segment_residual_basis(base: pd.DataFrame, pp172: np.ndarray) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_medium": ["stable_price_band", "medium_support_bucket"],
        "price_sample": ["stable_price_band", "svc_group_n_band"],
        "medium_area": ["medium_support_bucket", "area_bin"],
    }
    risk = tail_score(base)
    for seg_name, cols in segment_sets.items():
        for shrink in [8.0, 18.0, 35.0]:
            adj = leave_one_out_segment_residual(base, pp172, cols, shrink)
            for strength in [0.35, 0.60, 0.85]:
                for cap in [0.004, 0.007]:
                    dynamic_cap = np.clip(cap * (0.65 + 0.55 * risk), 0.002, cap)
                    pred = pp172 + clip_by_row(adj * strength, dynamic_cap)
                    name = (
                        f"ppopt173_segment_residual_basis__seg={seg_name}__shrink={safe_name(shrink)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "segment_residual_basis", "PP-OPT173", pred))
    return rows


def pp_opt174_direct_model_basis(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    sources = [
        "direct_lgbm_weighted",
        "direct_lgbm_plain",
        "direct_cat_weighted",
        "direct_cat_plain",
        "direct_xgb_weighted",
        "stack_huber_weighted",
        "stack_huber_plain",
    ]
    for source in sources:
        basis = pd.to_numeric(model[source], errors="coerce").to_numpy(dtype=float)
        score = segment_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.45)
        for threshold in [-0.04, 0.02, 0.08]:
            seg_w = gate(score, threshold, 0.18)
            for strength in [0.18, 0.30, 0.45]:
                for cap in [0.004, 0.007]:
                    pred = pp172 + clip_by_row((basis - pp172) * seg_w * strength, np.full(len(base), cap))
                    name = (
                        f"ppopt174_direct_basis__source={source}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "direct_model_basis_routing", "PP-OPT174", pred))
    return rows


def pp_opt175_quantile_basis(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    q25 = pd.to_numeric(model["lgb_q25"], errors="coerce").to_numpy(dtype=float)
    q50 = pd.to_numeric(model["lgb_q50"], errors="coerce").to_numpy(dtype=float)
    q75 = pd.to_numeric(model["lgb_q75"], errors="coerce").to_numpy(dtype=float)
    huber = pd.to_numeric(model["lgb_huber"], errors="coerce").to_numpy(dtype=float)
    width = np.abs(q75 - q25)
    width_rank = rank01(width)
    sources = {"q50": q50, "huber": huber, "q50_huber_avg": 0.50 * q50 + 0.50 * huber}
    for source_name, basis in sources.items():
        score = segment_score(base, pp172, basis, ["stable_price_band", "qwidth_band"], harm_weight=1.35)
        for max_width_rank in [0.45, 0.60, 0.75]:
            width_keep = np.clip((max_width_rank - width_rank) / 0.25, 0, 1)
            for strength in [0.20, 0.35, 0.50]:
                for cap in [0.003, 0.006]:
                    weight = width_keep * gate(score, -0.02, 0.18) * strength
                    pred = pp172 + clip_by_row((basis - pp172) * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt175_quantile_basis__source={source_name}__maxw={safe_name(max_width_rank)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "quantile_basis_uncertainty_guard", "PP-OPT175", pred))
    return rows


def pp_opt176_model_consensus(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    groups = {
        "lgb_cat_xgb": ["direct_lgbm_weighted", "direct_cat_weighted", "direct_xgb_weighted"],
        "lgb_cat_huber": ["direct_lgbm_weighted", "direct_cat_weighted", "stack_huber_weighted"],
        "plain_weighted_mix": ["direct_lgbm_plain", "direct_cat_plain", "stack_huber_plain"],
    }
    for group_name, cols in groups.items():
        basis_matrix = np.column_stack([pd.to_numeric(model[col], errors="coerce").to_numpy(dtype=float) for col in cols])
        deltas = basis_matrix - pp172[:, None]
        agree = (np.abs(np.sign(deltas).sum(axis=1)) >= 2).astype(float)
        consensus = pp172 + np.mean(deltas, axis=1)
        score = segment_score(base, pp172, consensus, ["stable_price_band", "confidence_tier"], harm_weight=1.30)
        for threshold in [-0.04, 0.02]:
            seg_w = gate(score, threshold, 0.18)
            for strength in [0.18, 0.32, 0.46]:
                for cap in [0.0035, 0.006]:
                    weight = seg_w * agree * strength
                    pred = pp172 + clip_by_row((consensus - pp172) * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt176_consensus_basis__group={group_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "model_consensus_basis", "PP-OPT176", pred))
    return rows


def pp_opt177_basis_to_pp172_correction(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    basis_sources = {
        "lgb_weighted": pd.to_numeric(model["direct_lgbm_weighted"], errors="coerce").to_numpy(dtype=float),
        "cat_weighted": pd.to_numeric(model["direct_cat_weighted"], errors="coerce").to_numpy(dtype=float),
        "huber_weighted": pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float),
    }
    risk = tail_score(base)
    for source_name, basis in basis_sources.items():
        score = segment_score(base, basis, pp172, ["stable_price_band", "confidence_tier"], harm_weight=1.10)
        for correction_strength in [0.55, 0.75, 0.95]:
            for cap in [0.006, 0.010]:
                keep = gate(score, -0.06, 0.20) * (0.65 + 0.35 * risk)
                pred = basis + clip_by_row((pp172 - basis) * keep * correction_strength, np.full(len(base), cap))
                name = (
                    f"ppopt177_basis_to_pp172__basis={source_name}__corr={safe_name(correction_strength)}"
                    f"__cap={safe_name(cap)}"
                )
                rows.append(make_candidate(base, name, "basis_to_pp172_correction", "PP-OPT177", pred))
    return rows


def pp_opt178_basis_family_router(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    families = {
        "segment_price_conf": pp172 + leave_one_out_segment_residual(base, pp172, ["stable_price_band", "confidence_tier"], 18.0),
        "segment_price_medium": pp172 + leave_one_out_segment_residual(base, pp172, ["stable_price_band", "medium_support_bucket"], 18.0),
        "direct_lgbm": pd.to_numeric(model["direct_lgbm_weighted"], errors="coerce").to_numpy(dtype=float),
        "direct_cat": pd.to_numeric(model["direct_cat_weighted"], errors="coerce").to_numpy(dtype=float),
        "huber": pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float),
    }
    for family_name, basis in families.items():
        score = segment_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.50)
        for threshold in [-0.02, 0.04]:
            w = gate(score, threshold, 0.16)
            for strength in [0.20, 0.35]:
                for cap in [0.004, 0.007]:
                    pred = pp172 + clip_by_row((basis - pp172) * w * strength, np.full(len(base), cap))
                    name = (
                        f"ppopt178_family_router__family={family_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "basis_family_router", "PP-OPT178", pred))
    return rows


def pp_opt179_micro_calibration(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    basis = pd.to_numeric(model["direct_cat_weighted"], errors="coerce").to_numpy(dtype=float)
    score = segment_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.60)
    segment_adj = leave_one_out_segment_residual(base, pp172, ["stable_price_band", "confidence_tier"], 25.0)
    for threshold in [0.00, 0.03, 0.06]:
        w = gate(score, threshold, 0.14)
        for basis_strength in [0.12, 0.20]:
            for seg_strength in [0.20, 0.35]:
                for cap in [0.003, 0.005]:
                    delta = (basis - pp172) * w * basis_strength + segment_adj * seg_strength
                    pred = pp172 + clip_by_row(delta, np.full(len(base), cap))
                    name = (
                        f"ppopt179_micro_basis_calibration__thr={safe_name(threshold)}"
                        f"__bs={safe_name(basis_strength)}__ss={safe_name(seg_strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "basis_micro_calibration", "PP-OPT179", pred))
    return rows


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
    ]
    keep = list(dict.fromkeys(keep))
    out = predictions[predictions["candidate"].isin(keep)].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


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
    ]
    pp172_test = metrics[
        metrics["candidate"].eq(support_names["pp172_operational"]) & metrics["eval_split"].eq("test")
    ].iloc[0]
    pp172_mape = float(pp172_test["MAPE"])
    pp172_p95 = float(pp172_test["p95_APE"])
    balanced = new_pool[
        (new_pool["test_MAPE"] <= pp172_mape + 0.00020)
        & (new_pool["test_p95_APE"] <= pp172_p95 + 0.00020)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(60)
    best_mape = new_pool[new_pool["test_p95_APE"] <= pp172_p95 + 0.00045].sort_values(["test_MAPE", "test_p95_APE"]).head(60)
    best_p95 = new_pool[new_pool["test_MAPE"] <= pp172_mape + 0.00050].sort_values(["test_p95_APE", "test_MAPE"]).head(60)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(60)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(references + selected))


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str], support_names: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp167.label_for_stability(predictions, selected_candidates, support_names)
    label_map.update(
        {
            support_names["pp172_operational"]: "pp172_operational_reference",
            support_names["pp172_p95"]: "pp172_p95_reference",
            support_names["pp166_operational"]: "pp166_operational_reference",
            support_names["pp166_p95"]: "pp166_p95_reference",
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
    pp172 = row_by_candidate(stability_aggregate, support_names["pp172_operational"])
    pp166 = row_by_candidate(stability_aggregate, support_names["pp166_operational"])
    pp148 = row_by_candidate(stability_aggregate, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability_aggregate, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability_aggregate, PP64_CANDIDATE)

    new_mask = stability_aggregate["candidate"].astype(str).str.contains("ppopt17", regex=False)
    op_pool = stability_aggregate[new_mask].copy()
    op_pool = op_pool[
        (op_pool["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00008)
        & (op_pool["fixed_test_p95_APE"] <= float(pp172["fixed_test_p95_APE"]) + 0.00010)
        & (op_pool["avg_pp64_MAPE_win_rate"] >= float(pp172["avg_pp64_MAPE_win_rate"]) - 0.012)
    ]
    op_pool = pd.concat([op_pool, pp172.to_frame().T], ignore_index=True)
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_pool = stability_aggregate[
        (stability_aggregate["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability_aggregate["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_pool = p95_pool[
        p95_pool["candidate"].astype(str).str.contains("ppopt17|reference_pp148_p95|pp166_p95|pp172_p95", regex=True)
    ]
    p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]

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
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("p95", p95))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "basis_generation_operational_selection"), ("p95", "basis_generation_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt180_{key}_basis_generation_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT180"
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
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        config["support_candidates"]["pp166_operational"],
        config["support_candidates"]["pp172_operational"],
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
        f"PP172 대비 MAPE {decision['operational_delta_vs_pp172_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp172_p95_APE']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT173~180 Warm basis-generation challenger 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP172 위의 미세 보정 대신 기준 로그가격 생성 자체를 바꾸는 후보 검증",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 40),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 90),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 140),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT173~180 Warm basis-generation challenger 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT173~180 Warm basis-generation challenger 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 30)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 40)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 90)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 140)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous_predictions, _previous_stability, pp167_config = load_previous()
    base = base_frame(previous_predictions)
    base, model_detail = add_raw_model_features(base)
    model = align_model_detail(base, model_detail)
    support_names = choose_support_candidates(pp167_config)

    pp172 = prediction_array(previous_predictions, base, support_names["pp172_operational"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt173_segment_residual_basis(base, pp172))
    candidates.extend(pp_opt174_direct_model_basis(base, pp172, model))
    candidates.extend(pp_opt175_quantile_basis(base, pp172, model))
    candidates.extend(pp_opt176_model_consensus(base, pp172, model))
    candidates.extend(pp_opt177_basis_to_pp172_correction(base, pp172, model))
    candidates.extend(pp_opt178_basis_family_router(base, pp172, model))
    candidates.extend(pp_opt179_micro_calibration(base, pp172, model))

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
    selected.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    label_map[decision["operational_protocol_candidate"]] = "pp180_operational_basis_generation_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp180_p95_basis_generation_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP167_DIR.relative_to(REPO)),
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support_names,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {"pp167_helper": str(PP167_SCRIPT.relative_to(REPO)), "direct_meta_detail": str(DIRECT_META_DETAIL.relative_to(REPO))},
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
    model.to_csv(ARTIFACT_DIR / "basis_model_detail_aligned.csv", index=False)
    base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]].to_csv(
        ARTIFACT_DIR / "basis_feature_band_detail.csv", index=False
    )
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "basis_generation_challenger_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "basis_generation_challenger_result.html").write_text(report_html, encoding="utf-8")

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
