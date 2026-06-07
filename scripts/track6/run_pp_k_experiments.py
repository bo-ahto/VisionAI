#!/usr/bin/env python3
"""Run Track6 PP-K auxiliary combination experiments."""
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
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    ARTIFACT_MANIFEST,
    BASE_EXP_DIR,
    BASE_NUMERIC,
    REPO,
    SEED,
    SPLIT_ROOT,
    artifact_features,
    fit_predict,
    huber_model,
    load_scope,
    metrics,
    normalize,
    split_types,
)


EXPERIMENTS = {
    "PP-K1": {"slug": "PP-K1_quantile_price_range_auxiliary", "title": "Quantile 가격 범위 보조 모델"},
    "PP-K2": {"slug": "PP-K2_linear_baseline_comparison", "title": "Ridge/ElasticNet 선형 기준선 비교"},
    "PP-K3": {"slug": "PP-K3_similar_artwork_fallback", "title": "유사 작품 fallback 예측"},
    "PP-K4": {"slug": "PP-K4_huber_catboost_residual_reference", "title": "Huber 선행 + CatBoost residual 보정"},
    "PP-K5": {"slug": "PP-K5_huber_catboost_segment_reference", "title": "Huber 선행 + CatBoost segment 규칙 보정"},
    "PP-K6": {"slug": "PP-K6_oof_stacking_combination", "title": "OOF stacking 조합"},
    "PP-K7": {"slug": "PP-K7_huber_quantile_risk_reference", "title": "Huber + Quantile 위험 구간 보정"},
    "PP-K8": {"slug": "PP-K8_huber_quantile_weight_reference", "title": "Huber + Quantile 중앙 예측 가중 평균"},
    "PP-K9": {"slug": "PP-K9_huber_residual_quantile_reference", "title": "Huber residual Quantile 보정"},
    "PP-K10": {"slug": "PP-K10_huber_quantile_catboost_routing_reference", "title": "Huber + Quantile 위험도 기반 CatBoost 라우팅"},
}

REFERENCE_MAP = {
    "PP-K4": ("PP-L3_huber_catboost_residual", "PP-L3"),
    "PP-K5": ("PP-J3_warm_catboost_leaf_artist_size_calibration", "PP-J3"),
    "PP-K7": ("PP-L4_huber_quantile_width_risk_calibration", "PP-L4"),
    "PP-K8": ("PP-L6_huber_quantile_catboost_weighted_ensemble", "PP-L6"),
    "PP-K9": ("PP-L9_huber_quantile_catboost_residual_sequential", "PP-L9"),
    "PP-K10": ("PP-L8_quantile_huber_catboost_sequential", "PP-L8"),
}


def prediction_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
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
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, policy: str, notes: str = "", extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def quantile_model(features: list[str], alpha: float) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=320,
            learning_rate=0.04,
            num_leaves=31,
            min_child_samples=35,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=2.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def run_k1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features_by_key = artifact_features()
    specs = {
        "warm": ("warm", "huber", features_by_key["warm"]),
        "cold": ("cold", "lightgbm", features_by_key["cold_lightgbm"]),
    }
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for scope, (scope_name, base_model, features) in specs.items():
        train, val, test = load_scope(scope_name, features)
        train = normalize(train, features)
        val = normalize(val, features)
        test = normalize(test, features)
        base = fit_predict(base_model, train, val, test, features)
        q_preds: dict[str, dict[str, np.ndarray]] = {"validation": {}, "test": {}}
        for alpha in [0.10, 0.50, 0.90]:
            model = quantile_model(features, alpha)
            model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
            q_preds["validation"][f"q{int(alpha * 100):02d}"] = np.asarray(model.predict(val[features]), dtype=float)
            q_preds["test"][f"q{int(alpha * 100):02d}"] = np.asarray(model.predict(test[features]), dtype=float)
        for split, frame in [("validation", val), ("test", test)]:
            q10 = q_preds[split]["q10"]
            q50 = q_preds[split]["q50"]
            q90 = q_preds[split]["q90"]
            lo = np.minimum(q10, q90)
            hi = np.maximum(q10, q90)
            covered = (frame["ln_price_krw"].to_numpy(dtype=float) >= lo) & (frame["ln_price_krw"].to_numpy(dtype=float) <= hi)
            width = hi - lo
            add_metric(rows, "PP-K1", "baseline", scope, split, frame, base[split], "base_model")
            add_metric(rows, "PP-K1", "quantile_q50", scope, split, frame, q50, "quantile_q50", extra={
                "coverage_10_90": float(np.mean(covered)),
                "median_width_log": float(np.median(width)),
                "p90_width_log": float(np.quantile(width, 0.90)),
                "median_price_range_ratio": float(np.median(np.exp(width))),
            })
            preds.append(prediction_frame("PP-K1", "baseline", scope, split, frame, base[split], "base_model"))
            preds.append(prediction_frame("PP-K1", "quantile_q50", scope, split, frame, q50, "quantile_q50", {
                "q10_log": lo,
                "q50_log": q50,
                "q90_log": hi,
                "quantile_width": width,
                "price_range_ratio": np.exp(width),
                "covered_10_90": covered,
            }))
            maps.append({
                "experiment_id": "PP-K1",
                "scope": scope,
                "split": split,
                "coverage_10_90": float(np.mean(covered)),
                "median_width_log": float(np.median(width)),
                "p90_width_log": float(np.quantile(width, 0.90)),
                "median_price_range_ratio": float(np.median(np.exp(width))),
            })
    return rows, preds, maps


def linear_model(kind: str, features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    if kind == "ridge":
        estimator: Any = Ridge(alpha=8.0, random_state=SEED)
    elif kind == "elasticnet":
        estimator = ElasticNet(alpha=0.001, l1_ratio=0.15, max_iter=5000, random_state=SEED)
    else:
        estimator = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", estimator)])


def run_k2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features = artifact_features()["warm"]
    train, val, test = load_scope("warm", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for kind in ["huber", "ridge", "elasticnet"]:
        model = linear_model(kind, features)
        model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
        for split, frame in [("validation", val), ("test", test)]:
            pred = np.asarray(model.predict(frame[features]), dtype=float)
            add_metric(rows, "PP-K2", kind, "warm", split, frame, pred, "linear_baseline")
            preds.append(prediction_frame("PP-K2", kind, "warm", split, frame, pred, "linear_baseline"))
        maps.append({"experiment_id": "PP-K2", "scope": "warm", "model": kind, "features": features})
    return rows, preds, maps


def add_size_bucket(train: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    edges = np.quantile(values, [0.0, 0.25, 0.50, 0.75, 1.0])
    edges[0], edges[-1] = -np.inf, np.inf
    out["size_bucket"] = pd.cut(pd.to_numeric(out["log_area"], errors="coerce"), bins=np.unique(edges), labels=False, include_lowest=True).astype("Int64").astype(str)
    out["size_bucket"] = out["size_bucket"].replace("<NA>", "__MISSING__")
    return out


def fallback_map(train: pd.DataFrame, keys: list[str], min_rows: int) -> pd.DataFrame:
    g = train.groupby(keys, dropna=False)["ln_price_krw"].agg(["count", "median"]).reset_index()
    g = g[g["count"] >= min_rows].copy()
    return g.rename(columns={"count": "n", "median": "fallback_log"})


def apply_fallback(frame: pd.DataFrame, fmap: pd.DataFrame, keys: list[str], base_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    merged = frame.reset_index().merge(fmap, on=keys, how="left").sort_values("index")
    used = merged["fallback_log"].notna().to_numpy()
    pred = base_pred.copy()
    pred[used] = merged.loc[used, "fallback_log"].to_numpy(dtype=float)
    return pred, used


def run_k3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    features_by_key = artifact_features()
    specs = {
        "warm": ("warm", "huber", features_by_key["warm"], ["artist_key", "size_bucket", "medium_support_bucket"]),
        "cold": ("cold", "lightgbm", features_by_key["cold_lightgbm"], ["size_bucket", "support_size_bucket"]),
    }
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for scope, (scope_name, model_name, features, keys) in specs.items():
        train, val, test = load_scope(scope_name, features)
        train = add_size_bucket(train, train)
        val = add_size_bucket(train, val)
        test = add_size_bucket(train, test)
        train = normalize(train, list(dict.fromkeys(features + keys)))
        val = normalize(val, list(dict.fromkeys(features + keys)))
        test = normalize(test, list(dict.fromkeys(features + keys)))
        base = fit_predict(model_name, train, val, test, features)
        for min_rows in [3, 5, 10]:
            fmap = fallback_map(train, keys, min_rows)
            for split, frame in [("validation", val), ("test", test)]:
                pred, used = apply_fallback(frame, fmap, keys, base[split])
                candidate = f"similar_fallback_min_rows_{min_rows}"
                add_metric(rows, "PP-K3", "baseline", scope, split, frame, base[split], "base_model")
                add_metric(rows, "PP-K3", candidate, scope, split, frame, pred, "similar_artwork_fallback", extra={"coverage": float(np.mean(used)), "min_rows": min_rows})
                preds.append(prediction_frame("PP-K3", "baseline", scope, split, frame, base[split], "base_model"))
                preds.append(prediction_frame("PP-K3", candidate, scope, split, frame, pred, "similar_artwork_fallback", {"fallback_used": used, "min_rows": min_rows}))
            maps.append({"experiment_id": "PP-K3", "scope": scope, "keys": keys, "min_rows": min_rows, "map_rows": int(len(fmap))})
    return rows, preds, maps


def frame_from_prediction(df: pd.DataFrame) -> pd.DataFrame:
    return df[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def run_k6() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    src = pd.read_csv(BASE_EXP_DIR / "PP-B4_oof_base_residual_source" / "outputs" / "predictions.csv")
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    cold_oof = src[(src["split"].eq("train_oof")) & (src["model_source"].isin(["cold_catboost", "cold_lightgbm"]))].copy()
    wide = cold_oof.pivot_table(index="_track6_row_id", columns="model_source", values="pred_log", aggfunc="first")
    actual = cold_oof.drop_duplicates("_track6_row_id").set_index("_track6_row_id")[["actual_log", "actual_price"]]
    train_meta = wide.join(actual).dropna().reset_index()
    model = Ridge(alpha=2.0, random_state=SEED)
    model.fit(train_meta[["cold_catboost", "cold_lightgbm"]], train_meta["actual_log"])
    for split in ["validation", "test"]:
        parts = src[(src["split"].eq(split)) & (src["model_source"].isin(["cold_catboost", "cold_lightgbm"]))].copy()
        w = parts.pivot_table(index="_track6_row_id", columns="model_source", values="pred_log", aggfunc="first")
        a = parts.drop_duplicates("_track6_row_id").set_index("_track6_row_id")[["actual_log", "actual_price"]]
        merged = w.join(a).dropna().reset_index()
        pred = np.asarray(model.predict(merged[["cold_catboost", "cold_lightgbm"]]), dtype=float)
        frame = frame_from_prediction(merged)
        add_metric(rows, "PP-K6", "baseline_cold_lightgbm", "cold", split, frame, merged["cold_lightgbm"].to_numpy(dtype=float), "baseline")
        add_metric(rows, "PP-K6", "ridge_oof_stack_cold_catboost_lightgbm", "cold", split, frame, pred, "oof_stacking")
        preds.append(prediction_frame("PP-K6", "baseline_cold_lightgbm", "cold", split, frame, merged["cold_lightgbm"].to_numpy(dtype=float), "baseline"))
        preds.append(prediction_frame("PP-K6", "ridge_oof_stack_cold_catboost_lightgbm", "cold", split, frame, pred, "oof_stacking"))
    maps.append({"experiment_id": "PP-K6", "scope": "cold", "model": "Ridge", "features": ["cold_catboost_pred_log", "cold_lightgbm_pred_log"], "coef_catboost": float(model.coef_[0]), "coef_lightgbm": float(model.coef_[1]), "intercept": float(model.intercept_)})
    return rows, preds, maps


def run_reference(exp_id: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    folder, ref_id = REFERENCE_MAP[exp_id]
    metric_path = BASE_EXP_DIR / folder / "outputs" / "metrics.csv"
    pred_path = BASE_EXP_DIR / folder / "outputs" / "predictions.csv"
    mdf = pd.read_csv(metric_path)
    pdf = pd.read_csv(pred_path)
    rows: list[dict[str, Any]] = []
    for row in mdf.to_dict("records"):
        out = dict(row)
        out["experiment_id"] = exp_id
        out["policy"] = f"reference_to_{ref_id}"
        out["notes"] = f"대체 실행: {folder} 결과를 PP-K 목적에 맞춰 참조"
        rows.append(out)
    pred = pdf.copy()
    pred["experiment_id"] = exp_id
    pred["policy"] = f"reference_to_{ref_id}"
    maps = [{"experiment_id": exp_id, "reference_experiment": ref_id, "reference_folder": folder, "reason": "이미 더 구체적인 선행/순차 실험으로 실행되어 중복 재학습 대신 결과를 참조"}]
    return rows, [pred], maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy() if "split" in metrics_df.columns else metrics_df.copy()
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.",
        "- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.sort_values([c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]).itertuples():
        lines.append(
            f"| `{getattr(row, 'scope', '')}` | `{getattr(row, 'candidate', '')}` | `{getattr(row, 'policy', '')}` | "
            f"`{getattr(row, 'MdAPE', float('nan')):.4f}` | `{getattr(row, 'MAPE', float('nan')):.4f}` | "
            f"`{getattr(row, 'p95_APE', float('nan')):.4f}` | `{getattr(row, 'RMSE_log', float('nan')):.4f}` |"
        )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
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
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "PP-K auxiliary experiment or reference result"}, ensure_ascii=False, indent=2), encoding="utf-8")
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
    runners = {"PP-K1": run_k1, "PP-K2": run_k2, "PP-K3": run_k3, "PP-K6": run_k6}
    summary_rows: list[dict[str, Any]] = []
    for exp_id in EXPERIMENTS:
        if exp_id in runners:
            rows, preds, maps = runners[exp_id]()
        else:
            rows, preds, maps = run_reference(exp_id)
        write_exp(exp_id, rows, preds, maps, {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {"source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))},
            "model_manifest": {"target": "ln_price_krw", "mode": "new_run" if exp_id in runners else "reference_run"},
        })
        df = pd.DataFrame(rows)
        if "split" in df.columns:
            val = df[df["split"].astype(str).eq("validation")].copy()
            if not val.empty and "MdAPE" in val.columns:
                summary_rows.extend(val.sort_values([c for c in ["scope", "MdAPE", "MAPE", "p95_APE"] if c in val.columns]).groupby("scope", as_index=False).head(1).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-K_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-K_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
