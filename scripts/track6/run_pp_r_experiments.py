#!/usr/bin/env python3
"""Run Track6 PP-R follow-up combination and staged calibration experiments."""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXPERIMENTS = {
    "PP-R1": {"slug": "PP-R1_cold_objective_constrained_fine_blend", "title": "Cold 목적 제약 fine blend"},
    "PP-R2": {"slug": "PP-R2_cold_ensemble_then_residual_stage_calibration", "title": "Cold 앙상블 후 residual 단계 보정"},
    "PP-R3": {"slug": "PP-R3_cold_risk_threshold_routing_search", "title": "Cold 위험 구간 라우팅 threshold 탐색"},
    "PP-R4": {"slug": "PP-R4_cold_validation_meta_calibration", "title": "Cold validation meta 보정"},
    "PP-R5": {"slug": "PP-R5_warm_final_candidate_residual_stabilization", "title": "Warm 최종 후보 잔차 안정화"},
}

COLD_CANDIDATES = [
    ("baseline_lgb", "PP-B4_oof_base_residual_source", "baseline", "cold", "cold_lightgbm"),
    ("p2_width_routing", "PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "cold", None),
    ("q2_mape_blend", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", "cold", None),
    ("n2_catboost_quantile", "PP-N2_cold_catboost_quantile_range", "catboost_quantile_q50", "cold", None),
    ("a7_hierarchical", "PP-A7_hierarchical_segment_residual_calibration", "corrected_hierarchical", "cold", None),
]

WARM_D4_CANDIDATE = "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75"


def source_prediction(
    folder: str,
    candidate: str,
    scope: str,
    split: str,
    model_source: str | None = None,
) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = (
        df["candidate"].astype(str).eq(candidate)
        & df["scope"].astype(str).eq(scope)
        & df["split"].astype(str).eq(split)
    )
    if model_source and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(model_source)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing prediction source folder={folder} candidate={candidate} scope={scope} split={split}")
    return out


def merge_candidate_sources(sources: list[tuple[str, str, str, str, str | None]], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate, scope, model_source in sources:
        src = source_prediction(folder, candidate, scope, split, model_source)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty merged predictions")
    return merged


def add_cold_width(merged: pd.DataFrame, split: str) -> pd.DataFrame:
    src = source_prediction(
        "PP-N1_cold_quantile_lightgbm_conformal_range",
        "quantile_lgbm_q50_conformal_range",
        "cold",
        split,
    )
    width = src[["_track6_row_id", "range_low_log", "range_high_log"]].copy()
    width["routing_width"] = width["range_high_log"] - width["range_low_log"]
    return merged.merge(width[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


def add_warm_width(merged: pd.DataFrame, split: str) -> pd.DataFrame:
    src = source_prediction("PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "warm", split)
    return merged.merge(src[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


def metric_frame(merged: pd.DataFrame) -> pd.DataFrame:
    return merged[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    scope: str,
    split: str,
    merged: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        **metrics(metric_frame(merged), pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    scope: str,
    split: str,
    merged: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "_track6_row_id": merged["_track6_row_id"].to_numpy(),
        "actual_log": merged["actual_log"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": merged["actual_price"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def weight_grid(n: int, step: float) -> list[tuple[float, ...]]:
    units = int(round(1 / step))
    out: list[tuple[float, ...]] = []
    for combo in product(range(units + 1), repeat=n):
        if sum(combo) == units:
            out.append(tuple(c / units for c in combo))
    return out


def blend_prediction(frame: pd.DataFrame, candidates: list[str], weights: tuple[float, ...]) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    for cand, weight in zip(candidates, weights, strict=True):
        pred += weight * frame[cand].to_numpy(dtype=float)
    return pred


def best_fine_blend(
    val: pd.DataFrame,
    candidates: list[str],
    objective: str,
    step: float = 0.10,
) -> tuple[tuple[float, ...], dict[str, float]]:
    base_scores = {cand: metrics(metric_frame(val), val[cand].to_numpy(dtype=float)) for cand in candidates}
    best_single_mdape = min(score["MdAPE"] for score in base_scores.values())
    best_score = np.inf
    best_weights = tuple([1.0] + [0.0] * (len(candidates) - 1))
    best_metrics: dict[str, float] = {}
    for weights in weight_grid(len(candidates), step):
        pred = blend_prediction(val, candidates, weights)
        m = metrics(metric_frame(val), pred)
        if objective == "mape_guarded" and m["MdAPE"] > best_single_mdape * 1.08:
            continue
        if objective == "p95_guarded" and m["MdAPE"] > best_single_mdape * 1.10:
            continue
        if objective == "mdape":
            score = m["MdAPE"]
        elif objective == "mape_guarded":
            score = m["MAPE"]
        elif objective == "p95_guarded":
            score = m["p95_APE"]
        else:
            raise ValueError(objective)
        if score < best_score:
            best_score = score
            best_weights = weights
            best_metrics = m
    return best_weights, best_metrics


def run_r1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_candidate_sources(COLD_CANDIDATES, "validation")
    test = merge_candidate_sources(COLD_CANDIDATES, "test")
    candidates = [item[0] for item in COLD_CANDIDATES]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-R1", f"component_{cand}", "cold", split, frame, frame[cand].to_numpy(dtype=float), "fine_blend_component")
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        weights, selected_metrics = best_fine_blend(val, candidates, objective)
        maps.append({
            "experiment_id": "PP-R1",
            "objective": objective,
            **{f"weight_{cand}": weight for cand, weight in zip(candidates, weights, strict=True)},
            **{f"validation_{k}": v for k, v in selected_metrics.items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = blend_prediction(frame, candidates, weights)
            candidate = f"fine_blend_{objective}"
            add_metric(rows, "PP-R1", candidate, "cold", split, frame, pred, "objective_constrained_fine_blend")
            preds.append(prediction_frame("PP-R1", candidate, "cold", split, frame, pred, "objective_constrained_fine_blend"))
    return rows, preds, maps


def assign_segments(frame: pd.DataFrame, pred_edges: np.ndarray, width_edges: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    pred_labels = [f"pred_q{i + 1}" for i in range(len(pred_edges) - 1)]
    width_labels = [f"width_q{i + 1}" for i in range(len(width_edges) - 1)]
    out["pred_bin"] = pd.cut(out["base_pred_log"], bins=pred_edges, labels=pred_labels, include_lowest=True).astype(str)
    out["width_bin"] = pd.cut(out["routing_width"], bins=width_edges, labels=width_labels, include_lowest=True).astype(str)
    out["pred_width_bin"] = out["pred_bin"].astype(str) + "__" + out["width_bin"].astype(str)
    return out


def correction_edges(val: pd.DataFrame, base_col: str) -> tuple[np.ndarray, np.ndarray]:
    pred_values = val[base_col].to_numpy(dtype=float)
    width_values = val["routing_width"].to_numpy(dtype=float)
    pred_edges = np.unique(np.quantile(pred_values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    width_edges = np.unique(np.quantile(width_values, [0.0, 0.33, 0.66, 1.0]))
    pred_edges[0], pred_edges[-1] = -np.inf, np.inf
    width_edges[0], width_edges[-1] = -np.inf, np.inf
    return pred_edges, width_edges


def build_correction_map(
    val: pd.DataFrame,
    segment_col: str,
    cap: float,
    strength: float,
    min_rows: int,
) -> dict[str, float]:
    residual = val["actual_log"] - val["base_pred_log"]
    temp = val[[segment_col]].copy()
    temp["residual_log"] = residual
    grouped = temp.groupby(segment_col, dropna=False)["residual_log"].agg(["size", "median"]).reset_index()
    corrections: dict[str, float] = {}
    for row in grouped.itertuples(index=False):
        segment = str(getattr(row, segment_col))
        if int(row.size) < min_rows:
            continue
        corrections[segment] = float(np.clip(row.median, -cap, cap) * strength)
    return corrections


def apply_correction(frame: pd.DataFrame, segment_col: str, corrections: dict[str, float]) -> np.ndarray:
    correction = frame[segment_col].astype(str).map(corrections).fillna(0.0).to_numpy(dtype=float)
    return frame["base_pred_log"].to_numpy(dtype=float) + correction


def best_segment_correction(
    val: pd.DataFrame,
    objective: str,
    min_rows: int = 50,
    strengths: list[float] | None = None,
    caps: list[float] | None = None,
) -> tuple[dict[str, Any], dict[str, float]]:
    strengths = strengths or [0.25, 0.50, 0.75, 1.00]
    caps = caps or [0.05, 0.10, 0.20, 0.35]
    segment_cols = ["pred_bin", "width_bin", "pred_width_bin"]
    base_m = metrics(metric_frame(val), val["base_pred_log"].to_numpy(dtype=float))
    best_score = np.inf
    best_spec: dict[str, Any] = {}
    best_map: dict[str, float] = {}
    for segment_col in segment_cols:
        for cap in caps:
            for strength in strengths:
                corrections = build_correction_map(val, segment_col, cap, strength, min_rows)
                pred = apply_correction(val, segment_col, corrections)
                m = metrics(metric_frame(val), pred)
                if objective == "mape_guarded" and m["MdAPE"] > base_m["MdAPE"] * 1.05:
                    continue
                if objective == "mdape":
                    score = m["MdAPE"]
                elif objective == "mape_guarded":
                    score = m["MAPE"]
                elif objective == "p95_guarded":
                    if m["MdAPE"] > base_m["MdAPE"] * 1.08:
                        continue
                    score = m["p95_APE"]
                else:
                    raise ValueError(objective)
                if score < best_score:
                    best_score = score
                    best_spec = {
                        "objective": objective,
                        "segment_col": segment_col,
                        "cap": cap,
                        "strength": strength,
                        "min_rows": min_rows,
                        **{f"validation_{k}": v for k, v in m.items()},
                    }
                    best_map = corrections
    return best_spec, best_map


def prepare_r2_frame(split: str) -> pd.DataFrame:
    base = source_prediction("PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", "cold", split)
    frame = base[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": "base_pred_log"})
    return add_cold_width(frame, split)


def run_r2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = prepare_r2_frame("validation")
    test = prepare_r2_frame("test")
    pred_edges, width_edges = correction_edges(val, "base_pred_log")
    val = assign_segments(val, pred_edges, width_edges)
    test = assign_segments(test, pred_edges, width_edges)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, "PP-R2", "base_q2_mape_blend", "cold", split, frame, frame["base_pred_log"].to_numpy(dtype=float), "stage0_ensemble")
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        spec, correction_map = best_segment_correction(val, objective)
        maps.append({"experiment_id": "PP-R2", **spec, "correction_map": json.dumps(correction_map, ensure_ascii=False)})
        for split, frame in [("validation", val), ("test", test)]:
            pred = apply_correction(frame, spec["segment_col"], correction_map)
            candidate = f"stage2_residual_{objective}"
            add_metric(rows, "PP-R2", candidate, "cold", split, frame, pred, "ensemble_then_segment_residual")
            preds.append(prediction_frame("PP-R2", candidate, "cold", split, frame, pred, "ensemble_then_segment_residual", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
                "segment_col": spec["segment_col"],
            }))
    return rows, preds, maps


def choose_routing(val: pd.DataFrame, candidates: list[str], thresholds: tuple[float, float], objective: str) -> tuple[list[dict[str, Any]], np.ndarray]:
    q1, q2 = np.quantile(val["routing_width"].to_numpy(dtype=float), thresholds)
    segments = [(-np.inf, q1, "stable"), (q1, q2, "caution"), (q2, np.inf, "risk")]
    pred = pd.Series(index=val.index, dtype=float)
    selected: list[dict[str, Any]] = []
    for low, high, name in segments:
        mask = (val["routing_width"] > low) & (val["routing_width"] <= high)
        frame = metric_frame(val.loc[mask])
        scores: dict[str, float] = {}
        for cand in candidates:
            if not mask.any():
                scores[cand] = np.inf
            else:
                m = metrics(frame, val.loc[mask, cand].to_numpy(dtype=float))
                if objective == "mdape":
                    scores[cand] = m["MdAPE"]
                elif objective == "mape_guarded":
                    base_m = metrics(frame, val.loc[mask, "baseline_lgb"].to_numpy(dtype=float))
                    scores[cand] = m["MAPE"] if m["MdAPE"] <= base_m["MdAPE"] * 1.08 else np.inf
                elif objective == "p95_guarded":
                    base_m = metrics(frame, val.loc[mask, "baseline_lgb"].to_numpy(dtype=float))
                    scores[cand] = m["p95_APE"] if m["MdAPE"] <= base_m["MdAPE"] * 1.10 else np.inf
                else:
                    raise ValueError(objective)
        if min(scores.values()) == np.inf:
            best = "baseline_lgb"
        else:
            best = min(scores, key=scores.get)
        pred.loc[mask] = val.loc[mask, best].to_numpy(dtype=float)
        selected.append({
            "segment": name,
            "selected_candidate": best,
            "width_low": float(low) if np.isfinite(low) else None,
            "width_high": float(high) if np.isfinite(high) else None,
            "validation_rows": int(mask.sum()),
            **{f"score_{k}": v for k, v in scores.items()},
        })
    return selected, pred.fillna(val["baseline_lgb"]).to_numpy(dtype=float)


def apply_routing(frame: pd.DataFrame, selected: list[dict[str, Any]]) -> np.ndarray:
    pred = pd.Series(index=frame.index, dtype=float)
    for item in selected:
        low = -np.inf if item["width_low"] is None else float(item["width_low"])
        high = np.inf if item["width_high"] is None else float(item["width_high"])
        mask = (frame["routing_width"] > low) & (frame["routing_width"] <= high)
        pred.loc[mask] = frame.loc[mask, item["selected_candidate"]].to_numpy(dtype=float)
    return pred.fillna(frame["baseline_lgb"]).to_numpy(dtype=float)


def run_r3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = add_cold_width(merge_candidate_sources(COLD_CANDIDATES, "validation"), "validation")
    test = add_cold_width(merge_candidate_sources(COLD_CANDIDATES, "test"), "test")
    candidates = [item[0] for item in COLD_CANDIDATES]
    threshold_candidates = [(0.20, 0.50), (0.25, 0.75), (0.33, 0.66), (0.50, 0.80)]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        best_score = np.inf
        best_selected: list[dict[str, Any]] = []
        best_thresholds = threshold_candidates[0]
        best_val_pred = val["baseline_lgb"].to_numpy(dtype=float)
        for thresholds in threshold_candidates:
            selected, val_pred = choose_routing(val, candidates, thresholds, objective)
            m = metrics(metric_frame(val), val_pred)
            if objective == "mdape":
                score = m["MdAPE"]
            elif objective == "mape_guarded":
                score = m["MAPE"] if m["MdAPE"] <= metrics(metric_frame(val), val["baseline_lgb"].to_numpy(dtype=float))["MdAPE"] * 1.08 else np.inf
            else:
                score = m["p95_APE"] if m["MdAPE"] <= metrics(metric_frame(val), val["baseline_lgb"].to_numpy(dtype=float))["MdAPE"] * 1.10 else np.inf
            if score < best_score:
                best_score = score
                best_selected = selected
                best_thresholds = thresholds
                best_val_pred = val_pred
        test_pred = apply_routing(test, best_selected)
        maps.extend([
            {"experiment_id": "PP-R3", "objective": objective, "threshold_low_q": best_thresholds[0], "threshold_high_q": best_thresholds[1], **item}
            for item in best_selected
        ])
        for split, frame, pred in [("validation", val, best_val_pred), ("test", test, test_pred)]:
            candidate = f"threshold_routing_{objective}"
            add_metric(rows, "PP-R3", candidate, "cold", split, frame, pred, "risk_threshold_routing_search")
            preds.append(prediction_frame("PP-R3", candidate, "cold", split, frame, pred, "risk_threshold_routing_search", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def meta_features(frame: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    preds = frame[candidates].copy()
    out = preds.copy()
    out["pred_mean"] = preds.mean(axis=1)
    out["pred_std"] = preds.std(axis=1)
    out["pred_range"] = preds.max(axis=1) - preds.min(axis=1)
    out["routing_width"] = frame["routing_width"].to_numpy(dtype=float)
    return out


def run_r4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = add_cold_width(merge_candidate_sources(COLD_CANDIDATES, "validation"), "validation")
    test = add_cold_width(merge_candidate_sources(COLD_CANDIDATES, "test"), "test")
    candidates = [item[0] for item in COLD_CANDIDATES]
    x_val = meta_features(val, candidates)
    x_test = meta_features(test, candidates)
    y_val = val["actual_log"].to_numpy(dtype=float)
    models = {
        "positive_linear": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", LinearRegression(positive=True))]),
        "ridge_0_1": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=0.1))]),
        "ridge_1": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        "ridge_10": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))]),
        "huber_meta": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))]),
    }
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for name, model in models.items():
        model.fit(x_val, y_val)
        val_pred = np.asarray(model.predict(x_val), dtype=float)
        test_pred = np.asarray(model.predict(x_test), dtype=float)
        lower_val = val[candidates].min(axis=1).to_numpy(dtype=float) - 0.05
        upper_val = val[candidates].max(axis=1).to_numpy(dtype=float) + 0.05
        lower_test = test[candidates].min(axis=1).to_numpy(dtype=float) - 0.05
        upper_test = test[candidates].max(axis=1).to_numpy(dtype=float) + 0.05
        for clip_mode, vp, tp in [
            ("raw", val_pred, test_pred),
            ("component_range_clipped", np.clip(val_pred, lower_val, upper_val), np.clip(test_pred, lower_test, upper_test)),
        ]:
            candidate = f"{name}_{clip_mode}"
            for split, frame, pred in [("validation", val, vp), ("test", test, tp)]:
                add_metric(rows, "PP-R4", candidate, "cold", split, frame, pred, "validation_meta_calibration")
                preds.append(prediction_frame("PP-R4", candidate, "cold", split, frame, pred, "validation_meta_calibration", {
                    "routing_width": frame["routing_width"].to_numpy(dtype=float),
                }))
        maps.append({
            "experiment_id": "PP-R4",
            "model": name,
            "features": json.dumps(list(x_val.columns), ensure_ascii=False),
            "training_scope": "validation_only_meta_calibration",
        })
    return rows, preds, maps


def prepare_r5_frame(split: str) -> pd.DataFrame:
    base = source_prediction("PP-D4_warm_three_model_blend", WARM_D4_CANDIDATE, "warm", split)
    frame = base[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": "base_pred_log"})
    return add_warm_width(frame, split)


def run_r5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = prepare_r5_frame("validation")
    test = prepare_r5_frame("test")
    pred_edges, width_edges = correction_edges(val, "base_pred_log")
    val = assign_segments(val, pred_edges, width_edges)
    test = assign_segments(test, pred_edges, width_edges)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, "PP-R5", "base_pp_d4_warm", "warm", split, frame, frame["base_pred_log"].to_numpy(dtype=float), "stage0_warm_best_candidate")
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        spec, correction_map = best_segment_correction(
            val,
            objective,
            min_rows=25,
            strengths=[0.25, 0.50],
            caps=[0.03, 0.05, 0.10, 0.20],
        )
        maps.append({"experiment_id": "PP-R5", **spec, "correction_map": json.dumps(correction_map, ensure_ascii=False)})
        for split, frame in [("validation", val), ("test", test)]:
            pred = apply_correction(frame, spec["segment_col"], correction_map)
            candidate = f"warm_residual_stabilized_{objective}"
            add_metric(rows, "PP-R5", candidate, "warm", split, frame, pred, "warm_final_candidate_residual_stabilization")
            preds.append(prediction_frame("PP-R5", candidate, "warm", split, frame, pred, "warm_final_candidate_residual_stabilization", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
                "segment_col": spec["segment_col"],
            }))
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    md_lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: PP-Q 이후 남은 개선 여지를 모델 조합, 단계 보정, 라우팅, 메타 보정으로 확인한다.",
        "- 기준: 가중치, 보정값, threshold, meta 모델은 validation에서만 정하고 test에는 그대로 적용한다.",
        "",
        "## Metrics",
        "",
        "| 후보 | scope | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    if not metrics_df.empty:
        sort_cols = [c for c in ["split", "MdAPE", "MAPE", "p95_APE"] if c in metrics_df.columns]
        for row in metrics_df.sort_values(sort_cols).itertuples(index=False):
            md_lines.append(
                f"| `{getattr(row, 'candidate', '')}` | `{getattr(row, 'scope', '')}` | `{getattr(row, 'split', '')}` | "
                f"`{getattr(row, 'policy', '')}` | `{getattr(row, 'MdAPE', float('nan')):.4f}` | "
                f"`{getattr(row, 'MAPE', float('nan')):.4f}` | `{getattr(row, 'p95_APE', float('nan')):.4f}` | "
                f"`{getattr(row, 'RMSE_log', float('nan')):.4f}` |"
            )
    md = "\n".join(md_lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f6f8fa;padding:1px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy / Correction Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], pred_frames: list[pd.DataFrame], map_rows: list[dict[str, Any]]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(pred_frames, ignore_index=True) if pred_frames else pd.DataFrame()
    map_df = pd.DataFrame(map_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    if not pred_df.empty:
        for split in ["validation", "test"]:
            pred_df[pred_df["split"].astype(str).eq(split)][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(
                exp_dir / "data" / f"{split}_index.csv",
                index=False,
            )
    (exp_dir / "experiment_config.json").write_text(
        json.dumps({"experiment_id": exp_id, "title": EXPERIMENTS[exp_id]["title"], "run_id": datetime.now().strftime("%Y%m%d_%H%M%S")}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(map_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(
        json.dumps({"target": "ln_price_krw", "mode": "followup_combination_and_staged_calibration"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {
        "PP-R1": run_r1,
        "PP-R2": run_r2,
        "PP-R3": run_r3,
        "PP-R4": run_r4,
        "PP-R5": run_r5,
    }
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runners.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        if {"split", "MdAPE"}.issubset(df.columns):
            for scope in sorted(df["scope"].astype(str).unique()):
                test = df[(df["split"].astype(str).eq("test")) & (df["scope"].astype(str).eq(scope))].copy()
                if not test.empty:
                    summary_rows.extend(test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(5).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-R_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-R_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
