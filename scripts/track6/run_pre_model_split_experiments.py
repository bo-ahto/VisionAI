#!/usr/bin/env python3
"""Run Track6 PRE-MODEL and PRE-SPLIT cold checks."""
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
    fit_predict,
    load_scope,
    metrics,
    normalize,
)
from catboost import CatBoostRegressor  # noqa: E402


EXPERIMENTS = {
    "PRE-MODEL-CCB": {
        "slug": "PRE-MODEL-CCB_cold_catboost_vs_lightgbm",
        "title": "Cold CatBoost 적합성 재검증",
    },
    "PRE-SPLIT-CCB": {
        "slug": "PRE-SPLIT-CCB_cold_catboost_segmented_training",
        "title": "Cold CatBoost 구분 학습",
    },
}


def pred_frame(exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str = "") -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "segment_rule": segment_rule,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def fit_catboost(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(cat_ready(train, features), train["ln_price_krw"].to_numpy(dtype=float), cat_features=cat_indices(features))
    return {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def depth_3d_segment(frame: pd.DataFrame) -> np.ndarray:
    is_3d = frame["is_3d_candidate"].astype(str).str.lower().isin(["true", "1", "yes"])
    has_depth = frame["has_depth"].astype(str).str.lower().isin(["true", "1", "yes"])
    return np.select([is_3d, has_depth], ["3d_candidate", "has_depth"], default="flat_2d").astype(str)


def segmented_catboost(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    segment_rule: str,
    min_rows: int = 250,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    baseline = fit_catboost(train, val, test, features)
    if segment_rule == "size_bucket":
        train_seg = train["size_bucket"].astype(str).to_numpy()
        val_seg = val["size_bucket"].astype(str).to_numpy()
        test_seg = test["size_bucket"].astype(str).to_numpy()
    elif segment_rule == "depth_3d_segment":
        train_seg = depth_3d_segment(train)
        val_seg = depth_3d_segment(val)
        test_seg = depth_3d_segment(test)
    elif segment_rule == "medium_shape_bucket":
        train_seg = train["medium_shape_bucket"].astype(str).to_numpy()
        val_seg = val["medium_shape_bucket"].astype(str).to_numpy()
        test_seg = test["medium_shape_bucket"].astype(str).to_numpy()
    else:
        raise ValueError(segment_rule)

    out = {"validation": baseline["validation"].copy(), "test": baseline["test"].copy()}
    rows = []
    for seg in sorted(pd.Series(train_seg).dropna().unique()):
        train_mask = train_seg == seg
        n_train = int(train_mask.sum())
        val_mask = val_seg == seg
        test_mask = test_seg == seg
        status = "fallback_baseline"
        if n_train >= min_rows and (val_mask.sum() > 0 or test_mask.sum() > 0):
            sub_train = train.loc[train_mask].reset_index(drop=True)
            sub_pred = fit_catboost(sub_train, val, test, features)
            out["validation"][val_mask] = sub_pred["validation"][val_mask]
            out["test"][test_mask] = sub_pred["test"][test_mask]
            status = "segment_model"
        rows.append({
            "segment_rule": segment_rule,
            "segment": str(seg),
            "n_train": n_train,
            "n_validation": int(val_mask.sum()),
            "n_test": int(test_mask.sum()),
            "status": status,
            "min_rows": min_rows,
        })
    return out, pd.DataFrame(rows)


def render(exp_id: str, title: str, metrics_df: pd.DataFrame, segment_df: pd.DataFrame | None = None) -> tuple[str, str]:
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "## Validation 결과",
        "",
        "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.candidate}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    if exp_id == "PRE-MODEL-CCB":
        lines.append("- Cold CatBoost와 Cold LightGBM을 같은 split에서 다시 비교해 후속 보정의 기준 모델을 확인한다.")
    else:
        lines.append("- 조건별 구분 학습이 baseline보다 나아지면 PP-J/PP-E의 조건별 보정 또는 라우팅 근거로 사용한다.")
    if segment_df is not None and not segment_df.empty:
        lines.append(f"- segment model 사용 구간: `{int(segment_df['status'].eq('segment_model').sum())}`개.")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1>{metrics_df.to_html(index=False, escape=True)}
{'' if segment_df is None else '<h2>Segments</h2>' + segment_df.to_html(index=False, escape=True)}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, info: dict[str, str], metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], config: dict[str, Any], segment_df: pd.DataFrame | None = None) -> None:
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    if segment_df is not None:
        segment_df.to_csv(exp_dir / "outputs" / "segment_definition.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO))}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, info["title"], metrics_df, segment_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def add_metrics(rows: list[dict[str, Any]], exp_id: str, candidate: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, model: str, segment_rule: str = "") -> None:
    rows.append({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "model": model,
        "segment_rule": segment_rule,
        **metrics(frame, pred_log),
    })


def main() -> None:
    start = time.time()
    features_by_key = artifact_features()
    summary_rows = []

    # PRE-MODEL-CCB
    cat_features = features_by_key["cold_catboost"]
    lgb_features = features_by_key["cold_lightgbm"]
    cat_train, cat_val, cat_test = load_scope("cold", cat_features)
    cat_train, cat_val, cat_test = normalize(cat_train, cat_features), normalize(cat_val, cat_features), normalize(cat_test, cat_features)
    lgb_train, lgb_val, lgb_test = load_scope("cold", lgb_features)
    lgb_train, lgb_val, lgb_test = normalize(lgb_train, lgb_features), normalize(lgb_val, lgb_features), normalize(lgb_test, lgb_features)
    cat_pred = fit_catboost(cat_train, cat_val, cat_test, cat_features)
    lgb_pred = fit_predict("lightgbm", lgb_train, lgb_val, lgb_test, lgb_features)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for candidate, model, val_frame, test_frame, pred in [
        ("cold_catboost_base_medium_shape", "catboost", cat_val, cat_test, cat_pred),
        ("cold_lightgbm_base_support_size", "lightgbm", lgb_val, lgb_test, lgb_pred),
    ]:
        for split_name, frame in [("validation", val_frame), ("test", test_frame)]:
            add_metrics(rows, "PRE-MODEL-CCB", candidate, split_name, frame, pred[split_name], model)
            preds.append(pred_frame("PRE-MODEL-CCB", candidate, split_name, frame, pred[split_name]))
    config = {
        "experiment_id": "PRE-MODEL-CCB",
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "feature_columns": {"catboost": cat_features, "lightgbm": lgb_features},
        "model_manifest": {"models": ["catboost", "lightgbm"], "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))},
    }
    write_exp("PRE-MODEL-CCB", EXPERIMENTS["PRE-MODEL-CCB"], rows, preds, config)
    best = pd.DataFrame(rows)
    row = best[best["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0].to_dict()
    row["folder"] = str((BASE_EXP_DIR / EXPERIMENTS["PRE-MODEL-CCB"]["slug"]).relative_to(REPO))
    summary_rows.append(row)

    # PRE-SPLIT-CCB
    rows = []
    preds = []
    base_pred = fit_catboost(cat_train, cat_val, cat_test, cat_features)
    segment_defs = []
    for split_name, frame in [("validation", cat_val), ("test", cat_test)]:
        add_metrics(rows, "PRE-SPLIT-CCB", "baseline_catboost", split_name, frame, base_pred[split_name], "catboost", "none")
        preds.append(pred_frame("PRE-SPLIT-CCB", "baseline_catboost", split_name, frame, base_pred[split_name], "none"))
    for segment_rule in ["size_bucket", "depth_3d_segment", "medium_shape_bucket"]:
        seg_pred, seg_df = segmented_catboost(cat_train, cat_val, cat_test, cat_features, segment_rule)
        segment_defs.append(seg_df)
        for split_name, frame in [("validation", cat_val), ("test", cat_test)]:
            candidate = f"segmented_by_{segment_rule}"
            add_metrics(rows, "PRE-SPLIT-CCB", candidate, split_name, frame, seg_pred[split_name], "catboost", segment_rule)
            preds.append(pred_frame("PRE-SPLIT-CCB", candidate, split_name, frame, seg_pred[split_name], segment_rule))
    segment_df = pd.concat(segment_defs, ignore_index=True)
    config = {
        "experiment_id": "PRE-SPLIT-CCB",
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "feature_columns": {"catboost": cat_features},
        "model_manifest": {
            "model": "catboost",
            "segment_rules": ["size_bucket", "depth_3d_segment", "medium_shape_bucket"],
            "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
        },
    }
    write_exp("PRE-SPLIT-CCB", EXPERIMENTS["PRE-SPLIT-CCB"], rows, preds, config, segment_df)
    best = pd.DataFrame(rows)
    row = best[best["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0].to_dict()
    row["folder"] = str((BASE_EXP_DIR / EXPERIMENTS["PRE-SPLIT-CCB"]["slug"]).relative_to(REPO))
    summary_rows.append(row)

    pd.DataFrame(summary_rows).to_csv(BASE_EXP_DIR / "PRE-MODEL_SPLIT_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PRE-MODEL_SPLIT_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
