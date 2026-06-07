#!/usr/bin/env python3
"""Run Track6 PP-B OOF residual correction experiments."""
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
    cat_indices,
    cat_ready,
    huber_model,
    lightgbm_model,
    load_scope,
    metrics,
    normalize,
)


EXPERIMENTS = {
    "PP-B4": {
        "slug": "PP-B4_oof_base_residual_source",
        "title": "학습 내부 교차 예측 기반 오차 보정 준비",
    },
    "PP-B1": {
        "slug": "PP-B1_ridge_residual_correction",
        "title": "Ridge 남은 예측 오차 보정",
        "residual_model": "ridge",
    },
    "PP-B2": {
        "slug": "PP-B2_huber_residual_correction",
        "title": "Huber 남은 예측 오차 보정",
        "residual_model": "huber",
    },
    "PP-B3": {
        "slug": "PP-B3_lightgbm_residual_correction",
        "title": "LightGBM 남은 예측 오차 보정",
        "residual_model": "lightgbm",
    },
    "PP-B5": {
        "slug": "PP-B5_warm_cold_separate_residual_correction",
        "title": "Warm/Cold 분리 오차 보정 모델",
        "residual_model": "best_by_scope",
    },
}

MODEL_SOURCES = {
    "warm_huber": {
        "scope": "warm",
        "model": "huber",
        "feature_key": "warm",
        "label": "Warm Huber(base_existing_combo)",
    },
    "cold_catboost": {
        "scope": "cold",
        "model": "catboost",
        "feature_key": "cold_catboost",
        "label": "Cold CatBoost(base_medium_shape)",
    },
    "cold_lightgbm": {
        "scope": "cold",
        "model": "lightgbm",
        "feature_key": "cold_lightgbm",
        "label": "Cold LightGBM(base_support_size)",
    },
}

RESIDUAL_CAP = 0.50
N_SPLITS = 5


def base_estimator(model_name: str, features: list[str]) -> Any:
    if model_name == "huber":
        return huber_model(features)
    if model_name == "lightgbm":
        return lightgbm_model(features)
    return CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def fit_base(model_name: str, train: pd.DataFrame, features: list[str]) -> Any:
    model = base_estimator(model_name, features)
    y = train["ln_price_krw"].to_numpy(dtype=float)
    if model_name == "catboost":
        model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
    else:
        model.fit(train[features], y)
    return model


def predict_base(model_name: str, model: Any, frame: pd.DataFrame, features: list[str]) -> np.ndarray:
    if model_name == "catboost":
        return np.asarray(model.predict(cat_ready(frame, features)), dtype=float)
    return np.asarray(model.predict(frame[features]), dtype=float)


def oof_predict(model_name: str, train: pd.DataFrame, features: list[str]) -> np.ndarray:
    pred = np.full(len(train), np.nan, dtype=float)
    kfold = KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    for tr_idx, hold_idx in kfold.split(train):
        fold_train = train.iloc[tr_idx].reset_index(drop=True)
        fold_hold = train.iloc[hold_idx].reset_index(drop=True)
        model = fit_base(model_name, fold_train, features)
        pred[hold_idx] = predict_base(model_name, model, fold_hold, features)
    if np.isnan(pred).any():
        raise RuntimeError("OOF prediction contains NaN")
    return pred


def feature_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in features if c in BASE_NUMERIC or c in {"pred_log"}]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def residual_model(model_name: str, features: list[str]) -> Pipeline:
    numeric, categorical = feature_types(features)
    transformers = []
    if numeric:
        scale = model_name in {"ridge", "huber"}
        steps: list[tuple[str, Any]] = [("impute", SimpleImputer(strategy="median"))]
        if scale:
            steps.append(("scale", StandardScaler()))
        transformers.append(("num", Pipeline(steps), numeric))
    if categorical:
        if model_name == "lightgbm":
            encoder: Any = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        else:
            try:
                encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
            except TypeError:
                encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    if model_name == "ridge":
        estimator: Any = Ridge(alpha=8.0, random_state=SEED)
    elif model_name == "huber":
        estimator = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)
    else:
        estimator = LGBMRegressor(
            objective="regression",
            n_estimators=220,
            learning_rate=0.035,
            num_leaves=15,
            min_child_samples=45,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=4.0,
            random_state=SEED,
            verbosity=-1,
        )
    return Pipeline([("prep", ColumnTransformer(transformers)), ("model", estimator)])


def residual_features(frame: pd.DataFrame, pred_log: np.ndarray, base_features: list[str]) -> tuple[pd.DataFrame, list[str]]:
    cols = list(dict.fromkeys(["pred_log", *base_features]))
    out = frame[base_features].copy()
    out.insert(0, "pred_log", pred_log)
    for col in cols:
        if col in BASE_NUMERIC or col == "pred_log":
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out[cols], cols


def prediction_frame(exp_id: str, candidate: str, source: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, residual_model_name: str, status: str = "ok") -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "model_source": source,
        "scope": MODEL_SOURCES[source]["scope"],
        "split": split,
        "residual_model": residual_model_name,
        "status": status,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def metric_row(exp_id: str, candidate: str, source: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, residual_model_name: str, notes: str = "") -> dict[str, Any]:
    return {
        "experiment_id": exp_id,
        "candidate": candidate,
        "model_source": source,
        "scope": MODEL_SOURCES[source]["scope"],
        "split": split,
        "base_model": MODEL_SOURCES[source]["model"],
        "residual_model": residual_model_name,
        "notes": notes,
        **metrics(frame, pred_log),
    }


def correction_summary(exp_id: str, source: str, model_name: str, split: str, residual_pred: np.ndarray) -> dict[str, Any]:
    return {
        "experiment_id": exp_id,
        "model_source": source,
        "split": split,
        "residual_model": model_name,
        "residual_cap": RESIDUAL_CAP,
        "n": int(len(residual_pred)),
        "median_predicted_residual_log": float(np.median(residual_pred)),
        "mean_predicted_residual_log": float(np.mean(residual_pred)),
        "p95_abs_predicted_residual_log": float(np.quantile(np.abs(residual_pred), 0.95)),
    }


def render(exp_id: str, metrics_df: pd.DataFrame, corr_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["model_source", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 1차 모델이 남긴 오차가 별도 모델로 안정적으로 학습되는지 확인한다.",
        "- 기준: residual 학습 target은 validation 오차가 아니라 train 내부 OOF 예측으로 만든 `actual_log - oof_pred_log`이다.",
        f"- 과보정 방지: 2단계 residual 예측값은 로그 기준 `±{RESIDUAL_CAP}`로 제한했다.",
        "",
        "## Validation 결과",
        "",
        "| 모델 소스 | 후보 | 2단계 모델 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.model_source}` | `{row.candidate}` | `{row.residual_model}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    for source in sorted(val["model_source"].unique()):
        scoped = val[val["model_source"].eq(source)]
        baseline = scoped[scoped["candidate"].eq("baseline")]
        if baseline.empty:
            continue
        b = baseline.iloc[0]
        for row in scoped[scoped["candidate"].ne("baseline")].itertuples():
            lines.append(
                f"- `{source}` `{row.candidate}`: baseline 대비 MdAPE `{row.MdAPE - b.MdAPE:.4f}`, "
                f"MAPE `{row.MAPE - b.MAPE:.4f}`, p95 `{row.p95_APE - b.p95_APE:.4f}`."
            )
    if not corr_df.empty:
        lines.append(f"- residual model summary rows: `{len(corr_df)}`.")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Residual Model Summary</h2>{corr_df.to_html(index=False, escape=True) if not corr_df.empty else '<p>No residual model summary</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], corr_rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    corr_df = pd.DataFrame(corr_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    corr_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "train_policy": "5-fold OOF base prediction for residual target",
        "validation_policy": "base model fitted on full train, residual model fitted on train OOF residual",
        "test_policy": "same fitted base/residual models applied without refitting",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(corr_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, corr_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def prepare_sources() -> dict[str, dict[str, Any]]:
    features_by_key = artifact_features()
    prepared: dict[str, dict[str, Any]] = {}
    for source, cfg in MODEL_SOURCES.items():
        features = features_by_key[cfg["feature_key"]]
        train, val, test = load_scope(cfg["scope"], features)
        train = normalize(train, features)
        val = normalize(val, features)
        test = normalize(test, features)
        oof = oof_predict(cfg["model"], train, features)
        full_model = fit_base(cfg["model"], train, features)
        val_pred = predict_base(cfg["model"], full_model, val, features)
        test_pred = predict_base(cfg["model"], full_model, test, features)
        train_resid_x, resid_features = residual_features(train, oof, features)
        val_resid_x, _ = residual_features(val, val_pred, features)
        test_resid_x, _ = residual_features(test, test_pred, features)
        prepared[source] = {
            "features": features,
            "residual_features": resid_features,
            "train": train,
            "val": val,
            "test": test,
            "oof_pred": oof,
            "val_pred": val_pred,
            "test_pred": test_pred,
            "train_resid_x": train_resid_x,
            "val_resid_x": val_resid_x,
            "test_resid_x": test_resid_x,
            "resid_target": train["ln_price_krw"].to_numpy(dtype=float) - oof,
        }
    return prepared


def run_b4(prepared: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    corr: list[dict[str, Any]] = []
    for source, d in prepared.items():
        rows.append(metric_row("PP-B4", "oof_baseline", source, "train_oof", d["train"], d["oof_pred"], "none", "OOF base prediction"))
        preds.append(prediction_frame("PP-B4", "oof_baseline", source, "train_oof", d["train"], d["oof_pred"], "none"))
        for split, frame, pred in [("validation", d["val"], d["val_pred"]), ("test", d["test"], d["test_pred"])]:
            rows.append(metric_row("PP-B4", "baseline", source, split, frame, pred, "none", "Full-train base model"))
            preds.append(prediction_frame("PP-B4", "baseline", source, split, frame, pred, "none"))
        corr.append({
            "experiment_id": "PP-B4",
            "model_source": source,
            "split": "train_oof",
            "residual_model": "none",
            "residual_cap": RESIDUAL_CAP,
            "n": int(len(d["resid_target"])),
            "median_predicted_residual_log": float(np.median(d["resid_target"])),
            "mean_predicted_residual_log": float(np.mean(d["resid_target"])),
            "p95_abs_predicted_residual_log": float(np.quantile(np.abs(d["resid_target"]), 0.95)),
        })
    return rows, preds, corr


def run_residual_experiment(exp_id: str, model_name: str, prepared: dict[str, dict[str, Any]], selected: dict[str, str] | None = None) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    corr: list[dict[str, Any]] = []
    for source, d in prepared.items():
        residual_name = selected[source] if selected else model_name
        model = residual_model(residual_name, d["residual_features"])
        model.fit(d["train_resid_x"], d["resid_target"])
        train_resid_pred = np.clip(np.asarray(model.predict(d["train_resid_x"]), dtype=float), -RESIDUAL_CAP, RESIDUAL_CAP)
        val_resid_pred = np.clip(np.asarray(model.predict(d["val_resid_x"]), dtype=float), -RESIDUAL_CAP, RESIDUAL_CAP)
        test_resid_pred = np.clip(np.asarray(model.predict(d["test_resid_x"]), dtype=float), -RESIDUAL_CAP, RESIDUAL_CAP)
        candidates = [
            ("train_oof", d["train"], d["oof_pred"], train_resid_pred),
            ("validation", d["val"], d["val_pred"], val_resid_pred),
            ("test", d["test"], d["test_pred"], test_resid_pred),
        ]
        for split, frame, base_pred, resid_pred in candidates:
            if split != "train_oof":
                rows.append(metric_row(exp_id, "baseline", source, split, frame, base_pred, "none", "Full-train base model"))
                preds.append(prediction_frame(exp_id, "baseline", source, split, frame, base_pred, "none"))
            corrected = base_pred + resid_pred
            rows.append(metric_row(exp_id, f"corrected_{residual_name}_residual", source, split, frame, corrected, residual_name, "OOF residual model correction"))
            preds.append(prediction_frame(exp_id, f"corrected_{residual_name}_residual", source, split, frame, corrected, residual_name))
            corr.append(correction_summary(exp_id, source, residual_name, split, resid_pred))
    return rows, preds, corr


def main() -> None:
    start = time.time()
    prepared = prepare_sources()
    summary_rows: list[dict[str, Any]] = []

    feature_columns = {
        source: {
            "base_features": d["features"],
            "residual_features": d["residual_features"],
        }
        for source, d in prepared.items()
    }
    model_manifest = {
        "base_sources": MODEL_SOURCES,
        "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
        "target": "ln_price_krw",
        "residual_target": "actual_log - oof_pred_log",
        "n_splits": N_SPLITS,
        "residual_cap_log": RESIDUAL_CAP,
    }

    rows, preds, corr = run_b4(prepared)
    write_exp("PP-B4", rows, preds, corr, {
        "experiment_id": "PP-B4",
        "title": EXPERIMENTS["PP-B4"]["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "feature_columns": feature_columns,
        "model_manifest": model_manifest,
    })
    summary_rows.extend(pd.DataFrame(rows).query("split == 'validation'").sort_values(["model_source", "MdAPE", "MAPE"]).groupby("model_source", as_index=False).head(1).to_dict("records"))

    residual_results: dict[str, pd.DataFrame] = {}
    for exp_id in ["PP-B1", "PP-B2", "PP-B3"]:
        model_name = EXPERIMENTS[exp_id]["residual_model"]
        rows, preds, corr = run_residual_experiment(exp_id, model_name, prepared)
        write_exp(exp_id, rows, preds, corr, {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": feature_columns,
            "model_manifest": {**model_manifest, "residual_model": model_name},
        })
        df = pd.DataFrame(rows)
        residual_results[model_name] = df
        summary_rows.extend(df.query("split == 'validation'").sort_values(["model_source", "MdAPE", "MAPE"]).groupby("model_source", as_index=False).head(1).to_dict("records"))

    selected: dict[str, str] = {}
    for source in MODEL_SOURCES:
        candidates = []
        for model_name, df in residual_results.items():
            subset = df[(df["model_source"].eq(source)) & (df["split"].eq("validation")) & (df["candidate"].ne("baseline"))]
            if not subset.empty:
                row = subset.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]
                candidates.append((model_name, row.MdAPE, row.MAPE, row.p95_APE))
        selected[source] = sorted(candidates, key=lambda item: (item[1], item[2], item[3]))[0][0]

    rows, preds, corr = run_residual_experiment("PP-B5", "best_by_scope", prepared, selected=selected)
    write_exp("PP-B5", rows, preds, corr, {
        "experiment_id": "PP-B5",
        "title": EXPERIMENTS["PP-B5"]["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "feature_columns": feature_columns,
        "model_manifest": {**model_manifest, "selected_residual_model_by_source": selected},
    })
    summary_rows.extend(pd.DataFrame(rows).query("split == 'validation'").sort_values(["model_source", "MdAPE", "MAPE"]).groupby("model_source", as_index=False).head(1).to_dict("records"))

    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-B_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-B_summary_metrics.csv",
        "selected_residual_model_by_source": selected,
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
