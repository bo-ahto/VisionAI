#!/usr/bin/env python3
"""Run Track6 PP-I final tuning and integration experiments."""
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    ARTIFACT_MANIFEST,
    BASE_EXP_DIR,
    REPO,
    SEED,
    SPLIT_ROOT,
    artifact_features,
    cat_indices,
    cat_ready,
    load_scope,
    metrics,
    normalize,
    split_types,
)


EXPERIMENTS = {
    "PP-I1": {"slug": "PP-I1_huber_setting_tuning", "title": "Huber 설정값 조정"},
    "PP-I2": {"slug": "PP-I2_catboost_setting_tuning", "title": "CatBoost 설정값 조정"},
    "PP-I3": {"slug": "PP-I3_correction_strength_final_check", "title": "보정값 강도 조정"},
    "PP-I4": {"slug": "PP-I4_routing_threshold_final_check", "title": "조건별 모델 선택 기준 조정"},
    "PP-I5": {"slug": "PP-I5_final_integrated_candidate_validation", "title": "최종 후보 통합 검증"},
}


def prediction_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, notes: str = "") -> None:
    rows.append({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame, pred_log),
    })


def custom_huber(features: list[str], epsilon: float, alpha: float, scale_numeric: bool = True) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        steps: list[tuple[str, Any]] = [("impute", SimpleImputer(strategy="median"))]
        if scale_numeric:
            steps.append(("scale", StandardScaler()))
        transformers.append(("num", Pipeline(steps), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=4000)),
    ])


def run_i1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()["warm"]
    train, val, test = load_scope("warm", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    configs = [
        ("baseline_eps1.35_alpha0.0001", 1.35, 0.0001, True),
        ("eps1.20_alpha0.0001", 1.20, 0.0001, True),
        ("eps1.50_alpha0.0001", 1.50, 0.0001, True),
        ("eps1.35_alpha0.001", 1.35, 0.001, True),
        ("eps1.35_alpha0.00001", 1.35, 0.00001, True),
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for name, epsilon, alpha, scale in configs:
        model = custom_huber(features, epsilon, alpha, scale)
        model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
        for split, frame in [("validation", val), ("test", test)]:
            pred = np.asarray(model.predict(frame[features]), dtype=float)
            add_metric(rows, "PP-I1", name, "warm", split, frame, pred, "huber_setting_grid", f"epsilon={epsilon}, alpha={alpha}, scale={scale}")
            preds.append(prediction_frame("PP-I1", name, "warm", split, frame, pred, "huber_setting_grid"))
        maps.append({"experiment_id": "PP-I1", "candidate": name, "epsilon": epsilon, "alpha": alpha, "scale_numeric": scale})
    return rows, preds, maps


def run_i2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()["cold_catboost"]
    train, val, test = load_scope("cold", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    configs = [
        ("baseline_depth6_lr0.04_l2_6", 6, 0.04, 6.0, 500),
        ("depth5_lr0.04_l2_8", 5, 0.04, 8.0, 500),
        ("depth6_lr0.03_l2_8", 6, 0.03, 8.0, 650),
        ("depth7_lr0.03_l2_10", 7, 0.03, 10.0, 650),
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for name, depth, lr, l2, iterations in configs:
        model = CatBoostRegressor(
            loss_function="RMSE",
            iterations=iterations,
            learning_rate=lr,
            depth=depth,
            l2_leaf_reg=l2,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
        for split, frame in [("validation", val), ("test", test)]:
            pred = np.asarray(model.predict(cat_ready(frame, features)), dtype=float)
            add_metric(rows, "PP-I2", name, "cold", split, frame, pred, "catboost_setting_grid", f"depth={depth}, lr={lr}, l2={l2}, iterations={iterations}")
            preds.append(prediction_frame("PP-I2", name, "cold", split, frame, pred, "catboost_setting_grid"))
        maps.append({"experiment_id": "PP-I2", "candidate": name, "depth": depth, "learning_rate": lr, "l2_leaf_reg": l2, "iterations": iterations})
    return rows, preds, maps


def source_prediction(folder: str, candidate: str, scope: str, split: str, model_source: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq(scope) & df["split"].astype(str).eq(split)
    if model_source and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(model_source)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {folder} {candidate} {scope} {split}")
    return out


def frame_from_source(df: pd.DataFrame) -> pd.DataFrame:
    return df[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def copy_reference(exp_id: str, refs: list[tuple[str, str, str, str | None, str]]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for folder, candidate, scope, model_source, label in refs:
        for split in ["validation", "test"]:
            df = source_prediction(folder, candidate, scope, split, model_source)
            frame = frame_from_source(df)
            pred = df["pred_log"].to_numpy(dtype=float)
            add_metric(rows, exp_id, label, scope, split, frame, pred, f"reference_{folder}", f"source_candidate={candidate}")
            out = prediction_frame(exp_id, label, scope, split, frame, pred, f"reference_{folder}")
            preds.append(out)
        maps.append({"experiment_id": exp_id, "label": label, "source_folder": folder, "source_candidate": candidate, "scope": scope, "model_source": model_source})
    return rows, preds, maps


def run_i3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    refs = [
        ("PP-C5_correction_strength_tuning", "strength_0.50_corrected_pred_bin_size_tail_cap", "warm", "warm_huber_ppj1_tail", "warm_tail_strength_0.50"),
        ("PP-C5_correction_strength_tuning", "strength_1.00_corrected_leaf_segment_min_rows_20", "cold", "cold_catboost_ppj4_leaf", "cold_catboost_leaf_strength_1.00"),
        ("PP-C5_correction_strength_tuning", "strength_0.25_corrected_lgb_tail_support_size_cap_0.25", "cold", "cold_lightgbm_ppj6_tail", "cold_lightgbm_tail_strength_0.25"),
    ]
    return copy_reference("PP-I3", refs)


def run_i4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    refs = [
        ("PP-E1_warm_low_history_routing", "routed_by_artist_history_bin", "warm", None, "warm_artist_history_routing"),
        ("PP-E3_extreme_size_routing", "routed_by_extreme_size_bin", "cold", None, "cold_extreme_size_routing_reference"),
        ("PP-E5_pred_price_risk_routing", "routed_by_pred_risk_bin", "cold", None, "cold_pred_risk_routing_reference"),
    ]
    return copy_reference("PP-I4", refs)


def run_i5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    refs = [
        ("PP-B4_oof_base_residual_source", "baseline", "warm", "warm_huber", "warm_baseline_huber"),
        ("PP-L8_quantile_huber_catboost_sequential", "PP-L8_warm_quantile_features_huber_catboost_residual", "warm", None, "warm_pp_l8_sequential"),
        ("PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75", "warm", None, "warm_pp_d4_integrated"),
        ("PP-E1_warm_low_history_routing", "routed_by_artist_history_bin", "warm", None, "warm_pp_e1_routing"),
        ("PP-K3_similar_artwork_fallback", "similar_fallback_min_rows_3", "warm", None, "warm_pp_k3_similar_fallback"),
        ("PP-B4_oof_base_residual_source", "baseline", "cold", "cold_lightgbm", "cold_baseline_lightgbm"),
        ("PP-J4_cold_catboost_leaf_coverage_calibration", "corrected_leaf_segment_min_rows_20", "cold", None, "cold_pp_j4_leaf"),
        ("PP-A7_hierarchical_segment_residual_calibration", "corrected_hierarchical", "cold", None, "cold_pp_a7_hierarchical"),
        ("PP-J6_cold_lightgbm_tail_calibration", "corrected_lgb_tail_support_size_cap_0.25", "cold", None, "cold_pp_j6_lgb_tail"),
        ("PP-D3_tail_defense_model_blend", "tail_weighted_corrected_cold_pair_w_0.75_cold_j4", "cold", None, "cold_pp_d3_tail_blend"),
    ]
    rows, preds, maps = copy_reference("PP-I5", refs)
    df = pd.DataFrame(rows)
    for scope in ["warm", "cold"]:
        val = df[(df["scope"].eq(scope)) & (df["split"].eq("validation"))].sort_values(["MdAPE", "MAPE", "p95_APE"])
        if not val.empty:
            best = val.iloc[0].to_dict()
            maps.append({"experiment_id": "PP-I5", "scope": scope, "selected_by_validation": best["candidate"], "validation_MdAPE": best["MdAPE"], "validation_MAPE": best["MAPE"], "validation_p95_APE": best["p95_APE"]})
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy()
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.",
        "- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.sort_values([c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]).itertuples():
        lines.append(f"| `{row.scope}` | `{row.candidate}` | `{row.policy}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Decision Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], pred_frames: list[pd.DataFrame], map_rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(pred_frames, ignore_index=True)
    map_df = pd.DataFrame(map_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].astype(str).eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].astype(str).eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "final validation selection and test confirmation"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(map_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {"PP-I1": run_i1, "PP-I2": run_i2, "PP-I3": run_i3, "PP-I4": run_i4, "PP-I5": run_i5}
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runners.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps, {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {"source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))},
            "model_manifest": {"target": "ln_price_krw", "mode": "final_tuning_integration"},
        })
        df = pd.DataFrame(rows)
        val = df[df["split"].astype(str).eq("validation")].copy()
        if not val.empty:
            summary_rows.extend(val.sort_values([c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]).groupby("scope", as_index=False).head(1).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-I_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-I_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
