#!/usr/bin/env python3
"""Run Track6 PP-V follow-up experiments from the final accuracy report."""
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
    "PP-V1": {"slug": "PP-V1_warm_ppu_feature_augmented_fine_blend", "title": "Warm PP-U 피처 후보 추가 fine blend"},
    "PP-V2": {"slug": "PP-V2_warm_ppu_feature_augmented_meta_stacking", "title": "Warm PP-U 피처 후보 추가 meta stacking"},
    "PP-V3": {"slug": "PP-V3_cold_ppu_feature_augmented_fine_blend", "title": "Cold PP-U 피처 후보 추가 fine blend"},
    "PP-V4": {"slug": "PP-V4_cold_ppu_feature_augmented_meta_stacking", "title": "Cold PP-U 피처 후보 추가 cross-fitted meta stacking"},
    "PP-V5": {"slug": "PP-V5_objective_policy_refresh", "title": "Warm/Cold 목적별 정책 재정리"},
}

WARM_SOURCES = [
    ("huber", "PP-D4_warm_three_model_blend", "baseline_warm_huber", None),
    ("l8_seq", "PP-L8_quantile_huber_catboost_sequential", "PP-L8_warm_quantile_features_huber_catboost_residual", None),
    ("l9_seq", "PP-L9_huber_quantile_catboost_residual_sequential", "PP-L9_warm_huber_quantile_residual_catboost_remaining", None),
    ("d4_blend", "PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75", None),
    ("r5_p95", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_p95_guarded", None),
    ("r5_mape", "PP-R5_warm_final_candidate_residual_stabilization", "warm_residual_stabilized_mape_guarded", None),
    ("e1_history", "PP-E1_warm_low_history_routing", "routed_by_artist_history_bin", None),
    ("k3_similar", "PP-K3_similar_artwork_fallback", "similar_fallback_min_rows_3", None),
    ("u1_full_generated", "PP-U1_warm_huber_feature_swap", "full_plus_generated_buckets", None),
    ("u1_artist_size_works", "PP-U1_warm_huber_feature_swap", "artist_size_works", None),
]

COLD_SOURCES = [
    ("baseline_lgb", "PP-B4_oof_base_residual_source", "baseline", "cold_lightgbm"),
    ("q2_mape_blend", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", None),
    ("r4_huber_meta", "PP-R4_cold_validation_meta_calibration", "huber_meta_component_range_clipped", None),
    ("s1_mdape", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.2_s1", None),
    ("s1_p95", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.5_s1", None),
    ("s4_huber", "PP-S4_cold_crossfit_meta_stacking", "huber_crossfit_component_range_clipped", None),
    ("u3_medium_size", "PP-U3_cold_lightgbm_feature_swap", "medium_size_combo", None),
    ("u3_support_shape", "PP-U3_cold_lightgbm_feature_swap", "support_shape_combo", None),
    ("u4_support_size_catboost", "PP-U4_cold_catboost_feature_swap", "lightgbm_swap_support_size", None),
]


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


def merge_sources(
    sources: list[tuple[str, str, str, str | None]],
    scope: str,
    split: str,
) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate, model_source in sources:
        src = source_prediction(folder, candidate, scope, split, model_source)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError(f"empty merged sources scope={scope} split={split}")
    return add_width(merged, scope, split)


def add_width(merged: pd.DataFrame, scope: str, split: str) -> pd.DataFrame:
    if scope == "warm":
        width = source_prediction("PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "warm", split)
        return merged.merge(width[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")
    width = source_prediction("PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", "cold", split)
    w = width[["_track6_row_id", "range_low_log", "range_high_log"]].copy()
    w["routing_width"] = w["range_high_log"] - w["range_low_log"]
    return merged.merge(w[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    scope: str,
    split: str,
    frame: pd.DataFrame,
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
        **metrics(metric_frame(frame), pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    scope: str,
    split: str,
    frame: pd.DataFrame,
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


def weight_grid(n: int, step: float) -> list[tuple[float, ...]]:
    units = int(round(1 / step))
    out: list[tuple[float, ...]] = []

    def build(position: int, remaining: int, acc: list[int]) -> None:
        if position == n - 1:
            out.append(tuple([*acc, remaining][idx] / units for idx in range(n)))
            return
        for value in range(remaining + 1):
            build(position + 1, remaining - value, [*acc, value])

    build(0, units, [])
    return out


def blend_prediction(frame: pd.DataFrame, candidates: list[str], weights: tuple[float, ...]) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    for cand, weight in zip(candidates, weights, strict=True):
        pred += weight * frame[cand].to_numpy(dtype=float)
    return pred


def metric_values(actual_log: np.ndarray, actual_price: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def best_blend(
    val: pd.DataFrame,
    candidates: list[str],
    objective: str,
    step: float,
    mdape_guard: float,
) -> tuple[tuple[float, ...], dict[str, float]]:
    actual_log = val["actual_log"].to_numpy(dtype=float)
    actual_price = val["actual_price"].to_numpy(dtype=float)
    pred_matrix = val[candidates].to_numpy(dtype=float)
    component_metrics = {
        cand: metric_values(actual_log, actual_price, pred_matrix[:, idx])
        for idx, cand in enumerate(candidates)
    }
    best_single_mdape = min(score["MdAPE"] for score in component_metrics.values())
    best_score = np.inf
    best_weights = tuple([1.0] + [0.0] * (len(candidates) - 1))
    best_metrics: dict[str, float] = {}
    for weights in weight_grid(len(candidates), step):
        weight_arr = np.asarray(weights, dtype=float)
        pred = pred_matrix @ weight_arr
        m = metric_values(actual_log, actual_price, pred)
        if objective == "mdape":
            score = m["MdAPE"]
        elif objective == "mape_guarded":
            score = m["MAPE"] if m["MdAPE"] <= best_single_mdape * mdape_guard else np.inf
        elif objective == "p95_guarded":
            score = m["p95_APE"] if m["MdAPE"] <= best_single_mdape * mdape_guard else np.inf
        else:
            raise ValueError(objective)
        if score < best_score:
            best_score = score
            best_weights = weights
            best_metrics = m
    return best_weights, best_metrics


def run_fine_blend(
    exp_id: str,
    scope: str,
    sources: list[tuple[str, str, str, str | None]],
    step: float,
    mdape_guard: float,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(sources, scope, "validation")
    test = merge_sources(sources, scope, "test")
    candidates = [label for label, *_ in sources]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []

    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, exp_id, f"component_{cand}", scope, split, frame, frame[cand].to_numpy(dtype=float), "fine_blend_component")

    for objective in ["mdape", "mape_guarded", "p95_guarded"]:
        weights, selected_metrics = best_blend(val, candidates, objective, step, mdape_guard)
        maps.append({
            "experiment_id": exp_id,
            "objective": objective,
            "step": step,
            "mdape_guard": mdape_guard,
            **{f"weight_{cand}": weight for cand, weight in zip(candidates, weights, strict=True)},
            **{f"validation_{k}": v for k, v in selected_metrics.items()},
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred = blend_prediction(frame, candidates, weights)
            candidate = f"fine_blend_{objective}"
            add_metric(rows, exp_id, candidate, scope, split, frame, pred, "feature_augmented_fine_blend")
            preds.append(prediction_frame(exp_id, candidate, scope, split, frame, pred, "feature_augmented_fine_blend", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def meta_features(frame: pd.DataFrame, candidates: list[str], base_col: str) -> pd.DataFrame:
    preds = frame[candidates].copy()
    out = preds.copy()
    out["base_pred_log"] = frame[base_col].to_numpy(dtype=float)
    out["pred_mean"] = preds.mean(axis=1)
    out["pred_std"] = preds.std(axis=1)
    out["pred_range"] = preds.max(axis=1) - preds.min(axis=1)
    out["routing_width"] = frame["routing_width"].to_numpy(dtype=float)
    for cand in candidates:
        out[f"diff_{cand}_base"] = frame[cand].to_numpy(dtype=float) - frame[base_col].to_numpy(dtype=float)
    return out


def meta_models() -> dict[str, Pipeline]:
    return {
        "ridge_1": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        "ridge_10": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))]),
        "huber": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))]),
    }


def run_meta_stacking(
    exp_id: str,
    scope: str,
    sources: list[tuple[str, str, str, str | None]],
    base_col: str,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(sources, scope, "validation")
    test = merge_sources(sources, scope, "test")
    candidates = [label for label, *_ in sources]
    x_val = meta_features(val, candidates, base_col)
    x_test = meta_features(test, candidates, base_col)
    y_val = val["actual_log"].to_numpy(dtype=float)

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, exp_id, f"component_{cand}", scope, split, frame, frame[cand].to_numpy(dtype=float), "meta_component")

    cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
    lower_val = val[candidates].min(axis=1).to_numpy(dtype=float) - 0.03
    upper_val = val[candidates].max(axis=1).to_numpy(dtype=float) + 0.03
    lower_test = test[candidates].min(axis=1).to_numpy(dtype=float) - 0.03
    upper_test = test[candidates].max(axis=1).to_numpy(dtype=float) + 0.03

    for model_name in meta_models():
        oof = np.zeros(len(val), dtype=float)
        for train_idx, hold_idx in cv.split(x_val):
            fold_model = meta_models()[model_name]
            fold_model.fit(x_val.iloc[train_idx], y_val[train_idx])
            oof[hold_idx] = np.asarray(fold_model.predict(x_val.iloc[hold_idx]), dtype=float)
        final_model = meta_models()[model_name]
        final_model.fit(x_val, y_val)
        test_pred = np.asarray(final_model.predict(x_test), dtype=float)
        for clip_mode, vp, tp in [
            ("raw", oof, test_pred),
            ("component_range_clipped", np.clip(oof, lower_val, upper_val), np.clip(test_pred, lower_test, upper_test)),
        ]:
            candidate = f"{model_name}_{clip_mode}"
            cv_metrics = metrics(metric_frame(val), vp)
            maps.append({
                "experiment_id": exp_id,
                "meta_model": model_name,
                "clip_mode": clip_mode,
                **{f"validation_cv_{k}": v for k, v in cv_metrics.items()},
            })
            for split, frame, pred in [("validation", val, vp), ("test", test, tp)]:
                add_metric(rows, exp_id, candidate, scope, split, frame, pred, "feature_augmented_meta_stacking")
                preds.append(prediction_frame(exp_id, candidate, scope, split, frame, pred, "feature_augmented_meta_stacking", {
                    "routing_width": frame["routing_width"].to_numpy(dtype=float),
                }))
    return rows, preds, maps


def run_policy_refresh() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    warm_sources = [
        ("pp_t1_mape", "PP-T1_warm_candidate_fine_blend", "fine_blend_mape_guarded", None),
        ("pp_t1_mdape", "PP-T1_warm_candidate_fine_blend", "fine_blend_mdape", None),
        ("pp_t2_huber", "PP-T2_warm_crossfit_meta_stacking", "huber_crossfit_component_range_clipped", None),
        ("pp_v1_mape", "PP-V1_warm_ppu_feature_augmented_fine_blend", "fine_blend_mape_guarded", None),
        ("pp_v1_p95", "PP-V1_warm_ppu_feature_augmented_fine_blend", "fine_blend_p95_guarded", None),
        ("pp_v2_huber", "PP-V2_warm_ppu_feature_augmented_meta_stacking", "huber_component_range_clipped", None),
    ]
    cold_sources = [
        ("pp_s1_mdape", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.2_s1", None),
        ("pp_s1_p95", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.5_s1", None),
        ("pp_s4_huber", "PP-S4_cold_crossfit_meta_stacking", "huber_crossfit_component_range_clipped", None),
        ("pp_q2_mape", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", None),
        ("pp_v3_mape", "PP-V3_cold_ppu_feature_augmented_fine_blend", "fine_blend_mape_guarded", None),
        ("pp_v3_p95", "PP-V3_cold_ppu_feature_augmented_fine_blend", "fine_blend_p95_guarded", None),
        ("pp_v4_huber", "PP-V4_cold_ppu_feature_augmented_meta_stacking", "huber_component_range_clipped", None),
    ]

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for scope, sources in [("warm", warm_sources), ("cold", cold_sources)]:
        val = merge_sources(sources, scope, "validation")
        test = merge_sources(sources, scope, "test")
        labels = [label for label, *_ in sources]
        for split, frame in [("validation", val), ("test", test)]:
            for label in labels:
                add_metric(rows, "PP-V5", f"component_{label}", scope, split, frame, frame[label].to_numpy(dtype=float), "policy_component")
        val_metrics = {label: metrics(metric_frame(val), val[label].to_numpy(dtype=float)) for label in labels}
        base_mdape = min(m["MdAPE"] for m in val_metrics.values())
        selectors = {
            "mdape_first": lambda label: val_metrics[label]["MdAPE"],
            "mape_guarded": lambda label: val_metrics[label]["MAPE"] if val_metrics[label]["MdAPE"] <= base_mdape * 1.08 else np.inf,
            "p95_guarded": lambda label: val_metrics[label]["p95_APE"] if val_metrics[label]["MdAPE"] <= base_mdape * 1.10 else np.inf,
        }
        for objective, score_fn in selectors.items():
            selected = min(labels, key=score_fn)
            maps.append({
                "experiment_id": "PP-V5",
                "scope": scope,
                "objective": objective,
                "selected_label": selected,
                **{f"validation_{k}": v for k, v in val_metrics[selected].items()},
            })
            for split, frame in [("validation", val), ("test", test)]:
                pred = frame[selected].to_numpy(dtype=float)
                candidate = f"{scope}_policy_{objective}"
                add_metric(rows, "PP-V5", candidate, scope, split, frame, pred, "objective_policy_refresh", {"selected_source": selected})
                preds.append(prediction_frame("PP-V5", candidate, scope, split, frame, pred, "objective_policy_refresh", {
                    "selected_source": selected,
                    "routing_width": frame["routing_width"].to_numpy(dtype=float),
                }))
    return rows, preds, maps


def render_report(exp_id: str, info: dict[str, Any], metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "- 목적: 종합 보고서에서 남은 후속 후보를 기존 조합 구조에 넣어 추가 개선 여부를 확인한다.",
        "- 선택 기준: validation에서 조합/정책을 정하고 test에서 재현성을 확인한다.",
        "",
        "## Test 결과 상위",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in test.head(20).itertuples():
        lines.append(f"| `{row.scope}` | `{row.candidate}` | `{row.policy}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += ["", "## 선택/가중치 맵", ""]
    if map_df.empty:
        lines.append("- 별도 map 없음")
    else:
        lines.append(markdown_table(map_df))
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy / Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as Markdown without optional tabulate dependency."""
    safe = df.copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_markdown_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    rows = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in safe.itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep, *rows])


def format_markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


def write_exp(exp_id: str, rows: list[dict[str, Any]], preds: list[pd.DataFrame], maps: list[dict[str, Any]]) -> None:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()
    map_df = pd.DataFrame(maps)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "policy_map.csv", index=False)
    if not pred_df.empty:
        pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
        pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "target": "ln_price_krw",
        "source_report": "docs/track6/experiments/price_prediction_accuracy_experiment_result_report.md",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, info, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {
        "PP-V1": lambda: run_fine_blend("PP-V1", "warm", WARM_SOURCES, step=0.10, mdape_guard=1.08),
        "PP-V2": lambda: run_meta_stacking("PP-V2", "warm", WARM_SOURCES, base_col="r5_p95"),
        "PP-V3": lambda: run_fine_blend("PP-V3", "cold", COLD_SOURCES, step=0.10, mdape_guard=1.08),
        "PP-V4": lambda: run_meta_stacking("PP-V4", "cold", COLD_SOURCES, base_col="s1_mdape"),
        "PP-V5": run_policy_refresh,
    }
    summary_frames: list[pd.DataFrame] = []
    for exp_id in ["PP-V1", "PP-V2", "PP-V3", "PP-V4", "PP-V5"]:
        rows, preds, maps = runners[exp_id]()
        write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        df["folder"] = str((BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]).relative_to(REPO))
        summary_frames.append(df)
    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(BASE_EXP_DIR / "PP-V_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-V_summary_metrics.csv",
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
