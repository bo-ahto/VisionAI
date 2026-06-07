#!/usr/bin/env python3
"""Run Track6 PP-S order-changing and custom-objective follow-up experiments."""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    REPO,
    SEED,
    artifact_features,
    load_scope,
    metrics,
    normalize,
    split_types,
)


EXPERIMENTS = {
    "PP-S1": {"slug": "PP-S1_cold_catboost_first_huber_residual", "title": "Cold CatBoost 선행 + Huber residual 안정화"},
    "PP-S2": {"slug": "PP-S2_cold_quantile_lgb_first_catboost_residual", "title": "Cold Quantile LightGBM 선행 + CatBoost residual"},
    "PP-S3": {"slug": "PP-S3_cold_lightgbm_objective_custom", "title": "Cold LightGBM 목적함수 커스텀"},
    "PP-S4": {"slug": "PP-S4_cold_crossfit_meta_stacking", "title": "Cold cross-fitted meta stacking"},
    "PP-S5": {"slug": "PP-S5_cold_objective_policy_comparison", "title": "Cold 목적별 최종 정책 비교"},
}

BASE_SOURCES = [
    ("baseline_lgb", "PP-B4_oof_base_residual_source", "baseline", "cold", "cold_lightgbm"),
    ("p2_width_routing", "PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "cold", None),
    ("q2_mape_blend", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", "cold", None),
    ("n1_quantile_lgb", "PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", "cold", None),
    ("n2_catboost_quantile", "PP-N2_cold_catboost_quantile_range", "catboost_quantile_q50", "cold", None),
    ("r4_huber_meta", "PP-R4_cold_validation_meta_calibration", "huber_meta_component_range_clipped", "cold", None),
]


def source_prediction(folder: str, candidate: str, scope: str, split: str, model_source: str | None = None) -> pd.DataFrame:
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
        raise ValueError(f"missing source folder={folder} candidate={candidate} scope={scope} split={split}")
    return out


def merge_sources(sources: list[tuple[str, str, str, str, str | None]], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate, scope, model_source in sources:
        src = source_prediction(folder, candidate, scope, split, model_source)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty merged source frame")
    return add_width(merged, split)


def add_width(merged: pd.DataFrame, split: str) -> pd.DataFrame:
    src = source_prediction("PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", "cold", split)
    width = src[["_track6_row_id", "range_low_log", "range_high_log"]].copy()
    width["routing_width"] = width["range_high_log"] - width["range_low_log"]
    return merged.merge(width[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


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
        "scope": "cold",
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
        "scope": "cold",
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


def meta_features(frame: pd.DataFrame, base_col: str) -> pd.DataFrame:
    pred_cols = [label for label, *_rest in BASE_SOURCES if label in frame.columns]
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


def residual_models() -> dict[str, Any]:
    return {
        "ridge_1": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
        "ridge_10": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=10.0))]),
        "huber": Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", HuberRegressor(epsilon=1.35, alpha=0.001, max_iter=1000))]),
    }


def fit_residual_candidates(
    exp_id: str,
    base_col: str,
    val: pd.DataFrame,
    test: pd.DataFrame,
    include_catboost: bool,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    x_val = meta_features(val, base_col)
    x_test = meta_features(test, base_col)
    y_resid = val["actual_log"].to_numpy(dtype=float) - val[base_col].to_numpy(dtype=float)
    model_map = residual_models()
    if include_catboost:
        model_map["catboost_mae_residual"] = CatBoostRegressor(
            loss_function="MAE",
            iterations=250,
            learning_rate=0.04,
            depth=4,
            l2_leaf_reg=8.0,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )
        model_map["catboost_quantile_residual"] = CatBoostRegressor(
            loss_function="Quantile:alpha=0.5",
            iterations=250,
            learning_rate=0.04,
            depth=4,
            l2_leaf_reg=8.0,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )

    for split, frame in [("validation", val), ("test", test)]:
        add_metric(rows, exp_id, f"base_{base_col}", split, frame, frame[base_col].to_numpy(dtype=float), "stage1_base_model")

    for model_name, model in model_map.items():
        model.fit(x_val, y_resid)
        val_resid = np.asarray(model.predict(x_val), dtype=float)
        test_resid = np.asarray(model.predict(x_test), dtype=float)
        for cap in [0.20, 0.35, 0.50]:
            for strength in [0.50, 1.00]:
                val_pred = val[base_col].to_numpy(dtype=float) + np.clip(val_resid, -cap, cap) * strength
                test_pred = test[base_col].to_numpy(dtype=float) + np.clip(test_resid, -cap, cap) * strength
                candidate = f"{base_col}_{model_name}_cap{cap:g}_s{strength:g}"
                maps.append({
                    "experiment_id": exp_id,
                    "base_col": base_col,
                    "residual_model": model_name,
                    "cap": cap,
                    "strength": strength,
                    "training_scope": "validation_residual_to_test",
                })
                for split, frame, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
                    add_metric(rows, exp_id, candidate, split, frame, pred, "ordered_residual_model")
                    preds.append(prediction_frame(exp_id, candidate, split, frame, pred, "ordered_residual_model", {
                        "routing_width": frame["routing_width"].to_numpy(dtype=float),
                    }))
    return rows, preds, maps


def run_s1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(BASE_SOURCES, "validation")
    test = merge_sources(BASE_SOURCES, "test")
    return fit_residual_candidates("PP-S1", "n2_catboost_quantile", val, test, include_catboost=False)


def run_s2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(BASE_SOURCES, "validation")
    test = merge_sources(BASE_SOURCES, "test")
    return fit_residual_candidates("PP-S2", "n1_quantile_lgb", val, test, include_catboost=True)


def lgbm_pipeline(features: list[str], objective: str) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 350,
        "learning_rate": 0.04,
        "num_leaves": 31,
        "min_child_samples": 40,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "random_state": SEED,
        "verbosity": -1,
    }
    if objective in {"huber", "quantile"}:
        params["alpha"] = 0.5
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", LGBMRegressor(**params))])


def run_s3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()["cold_lightgbm"]
    train, val_raw, test_raw = load_scope("cold", features)
    train = normalize(train, features)
    val = normalize(val_raw, features)
    test = normalize(test_raw, features)
    objectives = ["regression", "regression_l1", "huber", "mape", "quantile"]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for objective in objectives:
        model = lgbm_pipeline(features, objective)
        model.fit(train[features], y)
        maps.append({"experiment_id": "PP-S3", "objective": objective, "features": json.dumps(features, ensure_ascii=False)})
        for split, frame in [("validation", val), ("test", test)]:
            pred = np.asarray(model.predict(frame[features]), dtype=float)
            temp = frame[["_track6_row_id", "ln_price_krw", "price_krw"]].rename(
                columns={"ln_price_krw": "actual_log", "price_krw": "actual_price"}
            )
            candidate = f"lgbm_objective_{objective}"
            add_metric(rows, "PP-S3", candidate, split, temp, pred, "lightgbm_objective_custom")
            preds.append(prediction_frame("PP-S3", candidate, split, temp, pred, "lightgbm_objective_custom"))
    return rows, preds, maps


def run_s4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(BASE_SOURCES, "validation")
    test = merge_sources(BASE_SOURCES, "test")
    candidate_models = residual_models()
    x_val = meta_features(val, "q2_mape_blend")
    x_test = meta_features(test, "q2_mape_blend")
    y_val = val["actual_log"].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
    for name, model in candidate_models.items():
        oof = np.zeros(len(val), dtype=float)
        for train_idx, hold_idx in cv.split(x_val):
            fold_model = residual_models()[name]
            fold_model.fit(x_val.iloc[train_idx], y_val[train_idx])
            oof[hold_idx] = np.asarray(fold_model.predict(x_val.iloc[hold_idx]), dtype=float)
        cv_metrics = metrics(metric_frame(val), oof)
        final_model = residual_models()[name]
        final_model.fit(x_val, y_val)
        test_pred = np.asarray(final_model.predict(x_test), dtype=float)
        for clip_mode, val_pred, tst_pred in [
            ("raw", oof, test_pred),
            (
                "component_range_clipped",
                np.clip(oof, val[[label for label, *_ in BASE_SOURCES]].min(axis=1).to_numpy(dtype=float) - 0.05, val[[label for label, *_ in BASE_SOURCES]].max(axis=1).to_numpy(dtype=float) + 0.05),
                np.clip(test_pred, test[[label for label, *_ in BASE_SOURCES]].min(axis=1).to_numpy(dtype=float) - 0.05, test[[label for label, *_ in BASE_SOURCES]].max(axis=1).to_numpy(dtype=float) + 0.05),
            ),
        ]:
            candidate = f"{name}_crossfit_{clip_mode}"
            maps.append({"experiment_id": "PP-S4", "meta_model": name, "clip_mode": clip_mode, **{f"cv_{k}": v for k, v in cv_metrics.items()}})
            for split, frame, pred in [("validation", val, val_pred), ("test", test, tst_pred)]:
                add_metric(rows, "PP-S4", candidate, split, frame, pred, "crossfitted_meta_stacking")
                preds.append(prediction_frame("PP-S4", candidate, split, frame, pred, "crossfitted_meta_stacking", {
                    "routing_width": frame["routing_width"].to_numpy(dtype=float),
                }))
    return rows, preds, maps


def collect_policy_sources(split: str) -> pd.DataFrame:
    sources = [
        ("pp_p2_mdape", "PP-P2_quantile_width_model_routing", "quantile_width_model_routing", "cold", None),
        ("pp_q2_mape", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective", "cold", None),
        ("pp_r4_p95", "PP-R4_cold_validation_meta_calibration", "huber_meta_component_range_clipped", "cold", None),
        ("pp_s1_catboost_huber_mdape", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.2_s1", "cold", None),
        ("pp_s1_catboost_huber_mape", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.5_s0.5", "cold", None),
        ("pp_s1_catboost_huber_p95", "PP-S1_cold_catboost_first_huber_residual", "n2_catboost_quantile_huber_cap0.5_s1", "cold", None),
        ("pp_s2_quantile_huber", "PP-S2_cold_quantile_lgb_first_catboost_residual", "n1_quantile_lgb_huber_cap0.5_s1", "cold", None),
        ("pp_s2_quantile_catboost", "PP-S2_cold_quantile_lgb_first_catboost_residual", "n1_quantile_lgb_catboost_mae_residual_cap0.2_s0.5", "cold", None),
        ("pp_s3_lgbm_huber", "PP-S3_cold_lightgbm_objective_custom", "lgbm_objective_huber", "cold", None),
        ("pp_s3_lgbm_mape", "PP-S3_cold_lightgbm_objective_custom", "lgbm_objective_mape", "cold", None),
        ("pp_s4_crossfit_huber", "PP-S4_cold_crossfit_meta_stacking", "huber_crossfit_component_range_clipped", "cold", None),
    ]
    return merge_sources(sources, split)


def run_s5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = collect_policy_sources("validation")
    test = collect_policy_sources("test")
    candidates = [col for col in val.columns if col not in {"_track6_row_id", "actual_log", "actual_price", "routing_width"}]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, frame in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-S5", f"component_{cand}", split, frame, frame[cand].to_numpy(dtype=float), "policy_component")
    base_mdape = min(metrics(metric_frame(val), val[c].to_numpy(dtype=float))["MdAPE"] for c in candidates)
    objectives = {
        "mdape_first": lambda m: m["MdAPE"],
        "mape_guarded": lambda m: m["MAPE"] if m["MdAPE"] <= base_mdape * 1.08 else np.inf,
        "p95_guarded": lambda m: m["p95_APE"] if m["MdAPE"] <= base_mdape * 1.10 else np.inf,
    }
    for objective, score_fn in objectives.items():
        scored: list[tuple[float, str, dict[str, float]]] = []
        for cand in candidates:
            m = metrics(metric_frame(val), val[cand].to_numpy(dtype=float))
            scored.append((score_fn(m), cand, m))
        score, best, val_metrics = min(scored, key=lambda item: item[0])
        maps.append({"experiment_id": "PP-S5", "objective": objective, "selected_candidate": best, "validation_score": score, **{f"validation_{k}": v for k, v in val_metrics.items()}})
        for split, frame in [("validation", val), ("test", test)]:
            pred = frame[best].to_numpy(dtype=float)
            candidate = f"policy_{objective}"
            add_metric(rows, "PP-S5", candidate, split, frame, pred, "objective_policy_selection", {"selected_source": best})
            preds.append(prediction_frame("PP-S5", candidate, split, frame, pred, "objective_policy_selection", {
                "routing_width": frame["routing_width"].to_numpy(dtype=float),
            }))
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.",
        "- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.",
        "- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.",
        "",
        "## Metrics",
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
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f6f8fa;padding:1px 4px;border-radius:4px}}</style></head>
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
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps({"target": "ln_price_krw", "mode": "order_change_custom_objective_meta"}, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {
        "PP-S1": run_s1,
        "PP-S2": run_s2,
        "PP-S3": run_s3,
        "PP-S4": run_s4,
        "PP-S5": run_s5,
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
    summary.to_csv(BASE_EXP_DIR / "PP-S_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-S_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
