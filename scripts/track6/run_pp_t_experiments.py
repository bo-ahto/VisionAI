#!/usr/bin/env python3
"""Run Track6 PP-T Warm follow-up combination and meta-calibration experiments."""
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
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402


EXPERIMENTS = {
    "PP-T1": {"slug": "PP-T1_warm_candidate_fine_blend", "title": "Warm 후보 fine blend"},
    "PP-T2": {"slug": "PP-T2_warm_crossfit_meta_stacking", "title": "Warm cross-fitted meta stacking"},
    "PP-T3": {"slug": "PP-T3_warm_r5_second_pass_residual_stabilization", "title": "Warm PP-R5 2차 residual 안정화"},
    "PP-T4": {"slug": "PP-T4_warm_objective_policy_comparison", "title": "Warm 목적별 최종 정책 비교"},
}

BLEND_SOURCES = [
    ("huber", "PP-D4_warm_three_model_blend", "baseline_warm_huber"),
    ("l8_seq", "PP-L8_quantile_huber_catboost_sequential", "PP-L8_warm_quantile_features_huber_catboost_residual"),
    ("l9_seq", "PP-L9_huber_quantile_catboost_residual_sequential", "PP-L9_warm_huber_quantile_residual_catboost_remaining"),
    ("d4_blend", "PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75"),
    ("r5_p95", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_p95_guarded"),
    ("r5_mape", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_mape_guarded"),
    ("e1_history", "PP-E1_warm_low_history_routing", "routed_by_artist_history_bin"),
    ("k3_similar", "PP-K3_similar_artwork_fallback", "similar_fallback_min_rows_3"),
]

META_SOURCES = BLEND_SOURCES + [
    ("j1_tail", "PP-J1_warm_huber_tail_segment_calibration", "corrected_pred_bin_size_tail_cap"),
    ("j3_catboost", "PP-J3_warm_catboost_leaf_artist_size_calibration", "corrected_warm_catboost_leaf_artist_size"),
]


def source_prediction(folder: str, candidate: str, split: str) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = (
        df["candidate"].astype(str).eq(candidate)
        & df["scope"].astype(str).eq("warm")
        & df["split"].astype(str).eq(split)
    )
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing warm source folder={folder} candidate={candidate} split={split}")
    return out


def add_width(merged: pd.DataFrame, split: str) -> pd.DataFrame:
    src = source_prediction("PP-P2_quantile_width_model_routing", "quantile_width_model_routing", split)
    return merged.merge(src[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


def merge_sources(sources: list[tuple[str, str, str]], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate in sources:
        src = source_prediction(folder, candidate, split)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty warm source frame")
    return add_width(merged, split)


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        **metrics(metric_frame(frame), pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["actual_log"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["actual_price"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def weight_grid(n: int, step: float = 0.10) -> list[tuple[float, ...]]:
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


def best_blend(val: pd.DataFrame, candidates: list[str], objective: str) -> tuple[tuple[float, ...], dict[str, float]]:
    base_metrics = {cand: metrics(metric_frame(val), val[cand].to_numpy(dtype=float)) for cand in candidates}
    best_single_mdape = min(m["MdAPE"] for m in base_metrics.values())
    best_score = np.inf
    best_weights = tuple([1.0] + [0.0] * (len(candidates) - 1))
    best_metrics: dict[str, float] = {}
    for weights in weight_grid(len(candidates), 0.10):
        pred = blend_prediction(val, candidates, weights)
        m = metrics(metric_frame(val), pred)
        if objective == "mdape":
            score = m["MdAPE"]
        elif objective == "mape_guarded":
            score = m["MAPE"] if m["MdAPE"] <= best_single_mdape * 1.05 else np.inf
        elif objective == "p95_guarded":
            score = m["p95_APE"] if m["MdAPE"] <= best_single_mdape * 1.08 else np.inf
        else:
            raise ValueError(objective)
        if score < best_score:
            best_score = score
            best_weights = weights
            best_metrics = m
    return best_weights, best_metrics


def run_t1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(BLEND_SOURCES, "validation")
    test = merge_sources(BLEND_SOURCES, "test")
    candidates = [label for label, *_ in BLEND_SOURCES]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-T1", f"component_{cand}", split, frame, frame[cand].to_numpy(dtype=float), "fine_blend_component")
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        weights, selected = best_blend(val, candidates, objective)
        maps.append({
            "experiment_id": "PP-T1",
            "objective": objective,
            **{f"weight_{cand}": weight for cand, weight in zip(candidates, weights, strict=True)},
            **{f"validation_{k}": v for k, v in selected.items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = blend_prediction(frame, candidates, weights)
            candidate = f"fine_blend_{objective}"
            add_metric(rows, "PP-T1", candidate, split, frame, pred, "warm_fine_blend")
            preds.append(prediction_frame("PP-T1", candidate, split, frame, pred, "warm_fine_blend", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def meta_features(frame: pd.DataFrame, base_col: str = "r5_p95") -> pd.DataFrame:
    pred_cols = [label for label, *_ in META_SOURCES if label in frame.columns]
    preds = frame[pred_cols].copy()
    out = preds.copy()
    out["base_pred_log"] = frame[base_col].to_numpy(dtype=float)
    out["pred_mean"] = preds.mean(axis=1)
    out["pred_std"] = preds.std(axis=1)
    out["pred_range"] = preds.max(axis=1) - preds.min(axis=1)
    out["routing_width"] = frame["routing_width"].to_numpy(dtype=float)
    for col in pred_cols:
        out[f"diff_{col}_base"] = frame[col].to_numpy(dtype=float) - frame[base_col].to_numpy(dtype=float)
    return out


def meta_models() -> dict[str, Pipeline]:
    return {
        "ridge_1": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        "ridge_10": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))]),
        "huber": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))]),
    }


def run_t2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(META_SOURCES, "validation")
    test = merge_sources(META_SOURCES, "test")
    x_val = meta_features(val)
    x_test = meta_features(test)
    y_val = val["actual_log"].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    pred_cols = [label for label, *_ in META_SOURCES]
    cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
    for name in meta_models():
        oof = np.zeros(len(val), dtype=float)
        for train_idx, hold_idx in cv.split(x_val):
            fold_model = meta_models()[name]
            fold_model.fit(x_val.iloc[train_idx], y_val[train_idx])
            oof[hold_idx] = np.asarray(fold_model.predict(x_val.iloc[hold_idx]), dtype=float)
        final_model = meta_models()[name]
        final_model.fit(x_val, y_val)
        test_pred = np.asarray(final_model.predict(x_test), dtype=float)
        lower_val = val[pred_cols].min(axis=1).to_numpy(dtype=float) - 0.03
        upper_val = val[pred_cols].max(axis=1).to_numpy(dtype=float) + 0.03
        lower_test = test[pred_cols].min(axis=1).to_numpy(dtype=float) - 0.03
        upper_test = test[pred_cols].max(axis=1).to_numpy(dtype=float) + 0.03
        for clip_mode, vp, tp in [
            ("raw", oof, test_pred),
            ("component_range_clipped", np.clip(oof, lower_val, upper_val), np.clip(test_pred, lower_test, upper_test)),
        ]:
            candidate = f"{name}_crossfit_{clip_mode}"
            cv_m = metrics(metric_frame(val), vp)
            maps.append({"experiment_id": "PP-T2", "meta_model": name, "clip_mode": clip_mode, **{f"cv_{k}": v for k, v in cv_m.items()}})
            for split, frame, pred in [("validation", val, vp), ("test", test, tp)]:
                add_metric(rows, "PP-T2", candidate, split, frame, pred, "warm_crossfit_meta_stacking")
                preds.append(prediction_frame("PP-T2", candidate, split, frame, pred, "warm_crossfit_meta_stacking", {
                    "routing_width": frame["routing_width"].to_numpy(dtype=float),
                }))
    return rows, preds, maps


def edges(values: np.ndarray, qs: list[float]) -> np.ndarray:
    out = np.unique(np.quantile(values, qs))
    out[0], out[-1] = -np.inf, np.inf
    return out


def assign_segments(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_edges = edges(val["base_pred_log"].to_numpy(dtype=float), [0, 0.2, 0.4, 0.6, 0.8, 1])
    width_edges = edges(val["routing_width"].to_numpy(dtype=float), [0, 0.33, 0.66, 1])
    disagreement_edges = edges(val["pred_std"].to_numpy(dtype=float), [0, 0.33, 0.66, 1])

    def transform(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        out["pred_bin"] = pd.cut(out["base_pred_log"], pred_edges, labels=[f"pred_q{i+1}" for i in range(len(pred_edges) - 1)], include_lowest=True).astype(str)
        out["width_bin"] = pd.cut(out["routing_width"], width_edges, labels=[f"width_q{i+1}" for i in range(len(width_edges) - 1)], include_lowest=True).astype(str)
        out["disagreement_bin"] = pd.cut(out["pred_std"], disagreement_edges, labels=[f"disagree_q{i+1}" for i in range(len(disagreement_edges) - 1)], include_lowest=True).astype(str)
        out["pred_width_bin"] = out["pred_bin"] + "__" + out["width_bin"]
        return out

    return transform(val), transform(test)


def correction_map(val: pd.DataFrame, segment_col: str, cap: float, strength: float, min_rows: int) -> dict[str, float]:
    residual = val["actual_log"] - val["base_pred_log"]
    temp = val[[segment_col]].copy()
    temp["residual_log"] = residual
    grouped = temp.groupby(segment_col, dropna=False)["residual_log"].agg(["size", "median"]).reset_index()
    out: dict[str, float] = {}
    for row in grouped.itertuples(index=False):
        if int(row.size) >= min_rows:
            out[str(getattr(row, segment_col))] = float(np.clip(row.median, -cap, cap) * strength)
    return out


def apply_correction(frame: pd.DataFrame, segment_col: str, corr: dict[str, float]) -> np.ndarray:
    return frame["base_pred_log"].to_numpy(dtype=float) + frame[segment_col].astype(str).map(corr).fillna(0.0).to_numpy(dtype=float)


def best_second_pass(val: pd.DataFrame, objective: str) -> tuple[dict[str, Any], dict[str, float]]:
    base_m = metrics(metric_frame(val), val["base_pred_log"].to_numpy(dtype=float))
    best_score = np.inf
    best_spec: dict[str, Any] = {}
    best_map: dict[str, float] = {}
    for segment_col in ["pred_bin", "width_bin", "disagreement_bin", "pred_width_bin"]:
        for cap in [0.02, 0.03, 0.05, 0.08, 0.10]:
            for strength in [0.25, 0.50, 0.75]:
                corr = correction_map(val, segment_col, cap, strength, min_rows=25)
                pred = apply_correction(val, segment_col, corr)
                m = metrics(metric_frame(val), pred)
                if objective == "mdape":
                    score = m["MdAPE"]
                elif objective == "mape_guarded":
                    score = m["MAPE"] if m["MdAPE"] <= base_m["MdAPE"] * 1.03 else np.inf
                elif objective == "p95_guarded":
                    score = m["p95_APE"] if m["MdAPE"] <= base_m["MdAPE"] * 1.05 else np.inf
                else:
                    raise ValueError(objective)
                if score < best_score:
                    best_score = score
                    best_spec = {
                        "objective": objective,
                        "segment_col": segment_col,
                        "cap": cap,
                        "strength": strength,
                        **{f"validation_{k}": v for k, v in m.items()},
                    }
                    best_map = corr
    return best_spec, best_map


def run_t3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(META_SOURCES, "validation")
    test = merge_sources(META_SOURCES, "test")
    for frame in [val, test]:
        frame["base_pred_log"] = frame["r5_p95"].to_numpy(dtype=float)
        frame["pred_std"] = frame[[label for label, *_ in META_SOURCES]].std(axis=1).to_numpy(dtype=float)
    val, test = assign_segments(val, test)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, "PP-T3", "base_r5_p95", split, frame, frame["base_pred_log"].to_numpy(dtype=float), "stage0_r5")
    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        spec, corr = best_second_pass(val, objective)
        maps.append({"experiment_id": "PP-T3", **spec, "correction_map": json.dumps(corr, ensure_ascii=False)})
        for split, frame in [("validation", val), ("test", test)]:
            pred = apply_correction(frame, spec["segment_col"], corr)
            candidate = f"second_pass_{objective}"
            add_metric(rows, "PP-T3", candidate, split, frame, pred, "warm_r5_second_pass_residual")
            preds.append(prediction_frame("PP-T3", candidate, split, frame, pred, "warm_r5_second_pass_residual", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
                "pred_std": frame["pred_std"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def collect_policy_sources(split: str) -> pd.DataFrame:
    sources = [
        ("pp_r5_p95", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_p95_guarded"),
        ("pp_r5_mape", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_mape_guarded"),
        ("pp_t1_mdape", "PP-T1_warm_candidate_fine_blend", "fine_blend_mdape"),
        ("pp_t1_mape", "PP-T1_warm_candidate_fine_blend", "fine_blend_mape_guarded"),
        ("pp_t1_p95", "PP-T1_warm_candidate_fine_blend", "fine_blend_p95_guarded"),
        ("pp_t2_huber", "PP-T2_warm_crossfit_meta_stacking", "huber_crossfit_component_range_clipped"),
        ("pp_t2_ridge10", "PP-T2_warm_crossfit_meta_stacking", "ridge_10_crossfit_component_range_clipped"),
        ("pp_t3_mdape", "PP-T3_warm_r5_second_pass_residual_stabilization", "second_pass_mdape"),
        ("pp_t3_mape", "PP-T3_warm_r5_second_pass_residual_stabilization", "second_pass_mape_guarded"),
        ("pp_t3_p95", "PP-T3_warm_r5_second_pass_residual_stabilization", "second_pass_p95_guarded"),
    ]
    return merge_sources(sources, split)


def run_t4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = collect_policy_sources("validation")
    test = collect_policy_sources("test")
    candidates = [col for col in val.columns if col not in {"_track6_row_id", "actual_log", "actual_price", "routing_width"}]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-T4", f"component_{cand}", split, frame, frame[cand].to_numpy(dtype=float), "policy_component")
    base_mdape = min(metrics(metric_frame(val), val[c].to_numpy(dtype=float))["MdAPE"] for c in candidates)
    objectives = {
        "mdape_first": lambda m: m["MdAPE"],
        "mape_guarded": lambda m: m["MAPE"] if m["MdAPE"] <= base_mdape * 1.05 else np.inf,
        "p95_guarded": lambda m: m["p95_APE"] if m["MdAPE"] <= base_mdape * 1.08 else np.inf,
    }
    for objective, score_fn in objectives.items():
        scored: list[tuple[float, str, dict[str, float]]] = []
        for cand in candidates:
            m = metrics(metric_frame(val), val[cand].to_numpy(dtype=float))
            scored.append((score_fn(m), cand, m))
        score, best, val_m = min(scored, key=lambda item: item[0])
        maps.append({"experiment_id": "PP-T4", "objective": objective, "selected_candidate": best, "validation_score": score, **{f"validation_{k}": v for k, v in val_m.items()}})
        for split, frame in [("validation", val), ("test", test)]:
            pred = frame[best].to_numpy(dtype=float)
            candidate = f"policy_{objective}"
            add_metric(rows, "PP-T4", candidate, split, frame, pred, "warm_objective_policy_selection", {"selected_source": best})
            preds.append(prediction_frame("PP-T4", candidate, split, frame, pred, "warm_objective_policy_selection", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: Warm 최종 후보 PP-R5 이후에도 조합, 메타 보정, 2차 residual 안정화로 개선 여지가 있는지 확인한다.",
        "- 기준: 가중치, meta 모델, 보정값, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.",
        "",
        "| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    if not metrics_df.empty:
        sort_cols = [c for c in ["split", "MdAPE", "MAPE", "p95_APE"] if c in metrics_df.columns]
        for row in metrics_df.sort_values(sort_cols).itertuples(index=False):
            lines.append(
                f"| `{getattr(row, 'candidate', '')}` | `{getattr(row, 'split', '')}` | `{getattr(row, 'policy', '')}` | "
                f"`{getattr(row, 'MdAPE', float('nan')):.4f}` | `{getattr(row, 'MAPE', float('nan')):.4f}` | "
                f"`{getattr(row, 'p95_APE', float('nan')):.4f}` | `{getattr(row, 'RMSE_log', float('nan')):.4f}` |"
            )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy / Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
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
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps({"target": "ln_price_krw", "mode": "warm_followup_combination_meta"}, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {
        "PP-T1": run_t1,
        "PP-T2": run_t2,
        "PP-T3": run_t3,
        "PP-T4": run_t4,
    }
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runners.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        if {"split", "MdAPE"}.issubset(df.columns):
            test = df[df["split"].astype(str).eq("test")].copy()
            if not test.empty:
                summary_rows.extend(test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(5).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-T_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-T_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
