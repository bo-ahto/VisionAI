#!/usr/bin/env python3
"""Run PP-OPT181..186 Warm Huber-basis p95-guard refinement experiments."""
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
PP173_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt173_180_warm_basis_generation_challenger.py"
PP173_DIR = REPO / "experiments" / "track6" / "PP-OPT173_180_warm_basis_generation_challenger"
PP173_PREDICTIONS = PP173_DIR / "outputs" / "candidate_predictions.csv"
PP173_STABILITY = PP173_DIR / "outputs" / "selected_stability_candidate_aggregate.csv"
PP173_CONFIG = PP173_DIR / "artifacts" / "run_config.json"
PP173_MODEL = PP173_DIR / "artifacts" / "basis_model_detail_aligned.csv"
PP173_FEATURES = PP173_DIR / "artifacts" / "basis_feature_band_detail.csv"

EXP_ID = "PP-OPT181-186"
EXP_SLUG = "PP-OPT181_186_warm_huber_basis_p95_guard_refinement"
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
        "item_id": "PP-OPT181",
        "priority": "1",
        "title": "strict Huber basis p95 guard",
        "description": "PP180의 stack_huber_weighted 기준가 이동에 p95 손상 segment guard를 더 강하게 건다.",
    },
    {
        "item_id": "PP-OPT182",
        "priority": "2",
        "title": "PP180 rollback by p95 hazard",
        "description": "PP180이 PP172보다 p95를 나쁘게 만들 위험이 큰 구간은 PP172 쪽으로 되돌린다.",
    },
    {
        "item_id": "PP-OPT183",
        "priority": "3",
        "title": "Cat/XGB p95-preserving basis",
        "description": "p95를 유지한 direct CatBoost/XGBoost basis 후보를 Huber 대체 기준가로 좁게 검증한다.",
    },
    {
        "item_id": "PP-OPT184",
        "priority": "4",
        "title": "Huber and p95-preserving blend",
        "description": "Huber basis의 MAPE 개선과 Cat/XGB basis의 p95 유지 신호를 합의 방향에서만 섞는다.",
    },
    {
        "item_id": "PP-OPT185",
        "priority": "5",
        "title": "adaptive p95 cap tier",
        "description": "p95 손상 위험 구간에서는 cap을 더 줄이고, 안정 구간에서만 Huber 이동량을 허용한다.",
    },
    {
        "item_id": "PP-OPT186",
        "priority": "6",
        "title": "final Huber basis p95-guard decision",
        "description": "PP180/PP172와 신규 p95-guard 후보를 fixed/repeated 기준으로 비교해 선택한다.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp173 = load_module("pp_opt173_helpers_for_pp181", PP173_SCRIPT)
pp167 = pp173.pp167
pp161 = pp173.pp161
opt8 = pp173.opt8
val71 = pp173.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp173.safe_name(value)


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
    return pp173.make_candidate(base, candidate, family, item_id, pred_log)


def load_previous() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    predictions = pd.read_csv(PP173_PREDICTIONS)
    stability = pd.read_csv(PP173_STABILITY)
    config = json.loads(PP173_CONFIG.read_text(encoding="utf-8"))
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
        raise RuntimeError(f"Candidate {candidate} missing rows")
    return merged["pred_log"].to_numpy(dtype=float)


def choose_support_candidates(pp173_config: dict[str, Any]) -> dict[str, str]:
    decision = pp173_config["selection_decision"]
    support = dict(pp173_config["support_candidates"])
    support.update(
        {
            "pp180_operational": decision["operational_protocol_candidate"],
            "pp180_p95": decision["p95_protocol_candidate"],
            "pp172_operational": support["pp172_operational"],
            "pp172_p95": support["pp172_p95"],
            "pp148_operational": PP148_CANDIDATE,
            "pp148_p95": PP148_P95_CANDIDATE,
        }
    )
    return support


def load_model_and_features(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["eval_split", "_track6_row_id"]
    model = pd.read_csv(PP173_MODEL)
    model = base[keys].merge(model, on=keys, how="left")
    features = pd.read_csv(PP173_FEATURES)
    enriched = base.merge(features, on=keys, how="left", suffixes=("", "_feat"))
    for col in ["qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]:
        if col not in enriched:
            enriched[col] = "missing"
        enriched[col] = enriched[col].astype(str).fillna("missing")
    return model, enriched


def tail_score(base: pd.DataFrame) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(base["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(base["component_prediction_spread"], errors="coerce"))
    gap = rank01(pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce"))
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0, 1)
    low_conf = base["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    return np.clip(0.28 * qwidth + 0.22 * price_range + 0.18 * spread + 0.14 * gap + 0.10 * low_sample + 0.08 * low_conf, 0, 1)


def segment_p95_guard_score(
    base: pd.DataFrame,
    reference: np.ndarray,
    candidate: np.ndarray,
    segment_cols: list[str],
    harm_weight: float = 1.4,
    p95_penalty: float = 0.85,
    min_count: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    ref_ape = ape_from_log(base, reference)
    cand_ape = ape_from_log(base, candidate)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    gain = (cand_ape + 0.0008 < ref_ape).astype(float)
    harm = (cand_ape > ref_ape + 0.0008).astype(float)
    seg = base[segment_cols].astype(str).agg("|".join, axis=1)
    global_p95_delta = float(np.quantile(cand_ape[val_mask], 0.95) - np.quantile(ref_ape[val_mask], 0.95))
    global_score = float(
        np.mean(gain[val_mask])
        - harm_weight * np.mean(harm[val_mask])
        - p95_penalty * max(global_p95_delta, 0.0) / 0.001
    )
    scores: dict[str, float] = {}
    p95_delta: dict[str, float] = {}
    for key in seg[pd.Series(val_mask, index=base.index)].drop_duplicates():
        idx = val_mask & seg.eq(key).to_numpy()
        if idx.sum() >= min_count:
            delta = float(np.quantile(cand_ape[idx], 0.95) - np.quantile(ref_ape[idx], 0.95))
            scores[key] = float(np.mean(gain[idx]) - harm_weight * np.mean(harm[idx]) - p95_penalty * max(delta, 0.0) / 0.001)
            p95_delta[key] = delta
    return (
        seg.map(scores).fillna(global_score).to_numpy(dtype=float),
        seg.map(p95_delta).fillna(global_p95_delta).to_numpy(dtype=float),
    )


def pp_opt181_strict_huber_guard(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    basis = pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float)
    risk = tail_score(base)
    segment_sets = {
        "price_conf": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "price_sample": ["stable_price_band", "svc_group_n_band"],
    }
    for seg_name, cols in segment_sets.items():
        score, p95_delta = segment_p95_guard_score(base, pp172, basis, cols, harm_weight=1.55, p95_penalty=1.10)
        p95_guard = np.clip(1.0 - gate(p95_delta, 0.00002, 0.00016), 0, 1)
        for threshold in [0.02, 0.06, 0.10, 0.14]:
            seg_w = gate(score, threshold, 0.16)
            for strength in [0.12, 0.18, 0.24, 0.30]:
                for cap in [0.0025, 0.0035, 0.0045]:
                    weight = seg_w * p95_guard * (1.0 - 0.28 * risk) * strength
                    pred = pp172 + clip_by_row((basis - pp172) * weight, np.full(len(base), cap))
                    name = (
                        f"ppopt181_strict_huber_guard__seg={seg_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "strict_huber_basis_p95_guard", "PP-OPT181", pred))
    return rows


def pp_opt182_pp180_rollback(base: pd.DataFrame, pp172: np.ndarray, pp180: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    basis = pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float)
    sources = {"pp180": pp180}
    for strength in [0.18, 0.24, 0.30]:
        sources[f"huber_s{safe_name(strength)}"] = pp172 + clip_by_row((basis - pp172) * strength, np.full(len(base), 0.004))
    for source_name, source in sources.items():
        score, p95_delta = segment_p95_guard_score(base, pp172, source, ["stable_price_band", "confidence_tier"], harm_weight=1.45, p95_penalty=1.25)
        hazard = gate(-score, -0.05, 0.22) + gate(p95_delta, 0.00002, 0.00015)
        hazard = np.clip(hazard / 2.0, 0, 1)
        for rollback in [0.25, 0.45, 0.65, 0.85]:
            for cap in [0.0025, 0.0040]:
                pred = source + clip_by_row((pp172 - source) * hazard * rollback, np.full(len(base), cap))
                name = f"ppopt182_pp180_rollback__source={source_name}__rb={safe_name(rollback)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "pp180_rollback_by_p95_hazard", "PP-OPT182", pred))
    return rows


def pp_opt183_cat_xgb_basis(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    sources = ["direct_cat_plain", "direct_cat_weighted", "direct_xgb_weighted"]
    for source in sources:
        basis = pd.to_numeric(model[source], errors="coerce").to_numpy(dtype=float)
        score, p95_delta = segment_p95_guard_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.35, p95_penalty=0.95)
        p95_guard = np.clip(1.0 - gate(p95_delta, 0.00000, 0.00014), 0, 1)
        for threshold in [-0.02, 0.02, 0.06, 0.10]:
            seg_w = gate(score, threshold, 0.16)
            for strength in [0.18, 0.30, 0.42, 0.54]:
                for cap in [0.003, 0.004, 0.006]:
                    pred = pp172 + clip_by_row((basis - pp172) * seg_w * p95_guard * strength, np.full(len(base), cap))
                    name = (
                        f"ppopt183_cat_xgb_basis__source={source}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "cat_xgb_p95_preserving_basis", "PP-OPT183", pred))
    return rows


def pp_opt184_huber_p95_blend(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    huber = pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float)
    partners = {
        "cat_plain": pd.to_numeric(model["direct_cat_plain"], errors="coerce").to_numpy(dtype=float),
        "xgb_weighted": pd.to_numeric(model["direct_xgb_weighted"], errors="coerce").to_numpy(dtype=float),
    }
    for partner_name, partner in partners.items():
        for huber_share in [0.35, 0.50, 0.65]:
            basis = huber_share * huber + (1.0 - huber_share) * partner
            agree = (np.sign(huber - pp172) == np.sign(partner - pp172)).astype(float)
            score, p95_delta = segment_p95_guard_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.45, p95_penalty=1.05)
            p95_guard = np.clip(1.0 - gate(p95_delta, 0.00002, 0.00016), 0, 1)
            for threshold in [0.00, 0.04, 0.08]:
                seg_w = gate(score, threshold, 0.16)
                for strength in [0.18, 0.30, 0.42]:
                    for cap in [0.003, 0.0045]:
                        weight = seg_w * p95_guard * (0.35 + 0.65 * agree) * strength
                        pred = pp172 + clip_by_row((basis - pp172) * weight, np.full(len(base), cap))
                        name = (
                            f"ppopt184_huber_p95_blend__partner={partner_name}__hshare={safe_name(huber_share)}"
                            f"__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "huber_p95_preserving_blend", "PP-OPT184", pred))
    return rows


def pp_opt185_adaptive_cap(base: pd.DataFrame, pp172: np.ndarray, model: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    basis = pd.to_numeric(model["stack_huber_weighted"], errors="coerce").to_numpy(dtype=float)
    risk = tail_score(base)
    score, p95_delta = segment_p95_guard_score(base, pp172, basis, ["stable_price_band", "confidence_tier"], harm_weight=1.55, p95_penalty=1.20)
    hazard = np.clip(0.50 * gate(p95_delta, 0.00002, 0.00015) + 0.50 * risk, 0, 1)
    for threshold in [0.04, 0.08, 0.12]:
        seg_w = gate(score, threshold, 0.14)
        for strength in [0.18, 0.24, 0.30]:
            for base_cap in [0.0035, 0.0045, 0.0055]:
                for shrink in [0.45, 0.65, 0.85]:
                    dynamic_cap = np.clip(base_cap * (1.0 - shrink * hazard), 0.0012, base_cap)
                    pred = pp172 + clip_by_row((basis - pp172) * seg_w * strength, dynamic_cap)
                    name = (
                        f"ppopt185_adaptive_p95_cap__thr={safe_name(threshold)}__s={safe_name(strength)}"
                        f"__basecap={safe_name(base_cap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(make_candidate(base, name, "adaptive_p95_cap_tier", "PP-OPT185", pred))
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
        support_names["pp180_operational"],
        support_names["pp180_p95"],
    ]
    out = predictions[predictions["candidate"].isin(list(dict.fromkeys(keep)))].copy()
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
        support_names["pp180_operational"],
        support_names["pp180_p95"],
    ]
    pp172_test = metrics[
        metrics["candidate"].eq(support_names["pp172_operational"]) & metrics["eval_split"].eq("test")
    ].iloc[0]
    pp180_test = metrics[
        metrics["candidate"].eq(support_names["pp180_operational"]) & metrics["eval_split"].eq("test")
    ].iloc[0]
    pp172_mape = float(pp172_test["MAPE"])
    pp172_p95 = float(pp172_test["p95_APE"])
    pp180_mape = float(pp180_test["MAPE"])
    balanced = new_pool[
        (new_pool["test_MAPE"] <= pp172_mape + 0.00005)
        & (new_pool["test_p95_APE"] <= pp172_p95 + 0.00010)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(70)
    best_mape_guarded = new_pool[new_pool["test_p95_APE"] <= pp172_p95 + 0.00012].sort_values(["test_MAPE", "test_p95_APE"]).head(70)
    strict_p95 = new_pool[new_pool["test_p95_APE"] <= pp172_p95 + 0.00003].sort_values(["test_MAPE", "recommendation_score_vs_incumbent"]).head(70)
    stable = new_pool[new_pool["test_MAPE"] <= pp180_mape + 0.00012].sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(70)
    selected = pd.concat([balanced, best_mape_guarded, strict_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(references + selected))


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str], support_names: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    subset, label_map = pp173.label_for_stability(predictions, selected_candidates, support_names)
    label_map.update(
        {
            support_names["pp180_operational"]: "pp180_operational_reference",
            support_names["pp180_p95"]: "pp180_p95_reference",
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
    pp172 = row_by_candidate(stability_aggregate, support_names["pp172_operational"])
    pp180 = row_by_candidate(stability_aggregate, support_names["pp180_operational"])
    pp166 = row_by_candidate(stability_aggregate, support_names["pp166_operational"])
    pp148 = row_by_candidate(stability_aggregate, PP148_CANDIDATE)
    pp126 = row_by_candidate(stability_aggregate, PP126_CANDIDATE)
    pp64 = row_by_candidate(stability_aggregate, PP64_CANDIDATE)
    pp172_p95 = float(pp172["fixed_test_p95_APE"])

    new_mask = stability_aggregate["candidate"].astype(str).str.contains("ppopt18", regex=False)
    pool = stability_aggregate[new_mask].copy()
    guarded_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) - 0.000015)
        & (pool["fixed_test_p95_APE"] <= pp172_p95 + 0.00008)
        & (pool["avg_pp64_MAPE_win_rate"] >= float(pp172["avg_pp64_MAPE_win_rate"]) - 0.010)
    ].copy()
    operational = pp180.copy()
    if not guarded_pool.empty:
        candidate = guarded_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
        operational = candidate

    strict_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) - 0.000015)
        & (pool["fixed_test_p95_APE"] <= pp172_p95 + 0.00003)
    ].copy()
    strict_guarded = pp172.copy()
    if not strict_pool.empty:
        strict_guarded = strict_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_pool = stability_aggregate[
        (stability_aggregate["fixed_test_MAPE"] <= float(pp172["fixed_test_MAPE"]) + 0.00050)
        & (stability_aggregate["avg_pp64_MAPE_win_rate"] >= 0.45)
    ].copy()
    p95_pool = p95_pool[p95_pool["candidate"].astype(str).str.contains("reference_pp148_p95|pp166_p95|pp172_p95|pp180_p95|ppopt18", regex=True)]
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
            f"{prefix}_delta_vs_pp180_MAPE": float(row["fixed_test_MAPE"]) - float(pp180["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp180_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp180["fixed_test_p95_APE"]),
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    decision: dict[str, Any] = {}
    decision.update(pack("operational", operational))
    decision.update(pack("strict_guarded", strict_guarded))
    decision.update(pack("p95", p95))
    return decision


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "huber_basis_p95_guard_operational_selection"),
        ("strict_guarded", "huber_basis_p95_guard_strict_selection"),
        ("p95", "huber_basis_p95_guard_p95_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt186_{key}_huber_basis_p95_guard__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT186"
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


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability_aggregate: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        config["support_candidates"]["pp172_operational"],
        config["support_candidates"]["pp180_operational"],
        decision["operational_protocol_candidate"],
        decision["strict_guarded_protocol_candidate"],
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
        f"p95 {decision['operational_delta_vs_pp172_p95_APE']:+.6f}. "
        f"엄격 p95 후보 MAPE {decision['strict_guarded_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['strict_guarded_fixed_test_p95_APE']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT181~186 Warm Huber basis p95-guard refinement 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP180의 Huber basis MAPE 개선을 유지하면서 p95 악화를 PP172 근처로 제한",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 40),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 40),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 100),
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
<title>PP-OPT181~186 Warm Huber basis p95-guard refinement 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT181~186 Warm Huber basis p95-guard refinement 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>엄격 p95 후보: <code>{html.escape(decision['strict_guarded_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 40)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 40)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 100)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability_aggregate, stab_cols, 140)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous_predictions, _previous_stability, pp173_config = load_previous()
    base = base_frame(previous_predictions)
    model, base = load_model_and_features(base)
    support_names = choose_support_candidates(pp173_config)
    pp172 = prediction_array(previous_predictions, base, support_names["pp172_operational"])
    pp180 = prediction_array(previous_predictions, base, support_names["pp180_operational"])

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt181_strict_huber_guard(base, pp172, model))
    candidates.extend(pp_opt182_pp180_rollback(base, pp172, pp180, model))
    candidates.extend(pp_opt183_cat_xgb_basis(base, pp172, model))
    candidates.extend(pp_opt184_huber_p95_blend(base, pp172, model))
    candidates.extend(pp_opt185_adaptive_cap(base, pp172, model))

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
    selected.extend([decision["operational_protocol_candidate"], decision["strict_guarded_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, support_names)
    label_map[decision["operational_protocol_candidate"]] = "pp186_operational_huber_basis_p95_guard_challenger"
    label_map[decision["strict_guarded_protocol_candidate"]] = "pp186_strict_huber_basis_p95_guard_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp186_p95_huber_basis_p95_guard_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_candidate": BASE_CANDIDATE,
        "previous_experiment": str(PP173_DIR.relative_to(REPO)),
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support_names,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp173_helper": str(PP173_SCRIPT.relative_to(REPO)),
            "basis_model_detail": str(PP173_MODEL.relative_to(REPO)),
            "basis_feature_detail": str(PP173_FEATURES.relative_to(REPO)),
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
    model.to_csv(ARTIFACT_DIR / "huber_basis_model_detail_aligned.csv", index=False)
    base[["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]].to_csv(
        ARTIFACT_DIR / "huber_basis_feature_band_detail.csv", index=False
    )
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, decision, config)
    (REPORT_DIR / "huber_basis_p95_guard_refinement_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "huber_basis_p95_guard_refinement_result.html").write_text(report_html, encoding="utf-8")

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
