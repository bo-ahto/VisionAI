#!/usr/bin/env python3
"""Run Track6 PP-C prediction recalibration experiments."""
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
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LinearRegression

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
    load_scope,
    metrics,
    normalize,
)
from run_pp_b_experiments import MODEL_SOURCES, fit_base, predict_base  # noqa: E402


EXPERIMENTS = {
    "PP-C1": {
        "slug": "PP-C1_linear_prediction_recalibration",
        "title": "전체 예측값 직선 재보정",
    },
    "PP-C3": {
        "slug": "PP-C3_monotonic_prediction_recalibration",
        "title": "예측 순서를 유지하는 비선형 재보정",
    },
    "PP-C5": {
        "slug": "PP-C5_correction_strength_tuning",
        "title": "보정 강도 줄이기 실험",
    },
}

STRENGTHS = [0.25, 0.50, 0.75, 1.00]
C5_SOURCES = [
    {
        "label": "warm_huber_ppj1_tail",
        "folder": "PP-J1_warm_huber_tail_segment_calibration",
        "scope": "warm",
        "candidate": "corrected_pred_bin_size_tail_cap",
        "base_candidate": "baseline",
    },
    {
        "label": "cold_catboost_ppj4_leaf",
        "folder": "PP-J4_cold_catboost_leaf_coverage_calibration",
        "scope": "cold",
        "candidate": "corrected_leaf_segment_min_rows_20",
        "base_candidate": "baseline",
    },
    {
        "label": "cold_lightgbm_ppj6_tail",
        "folder": "PP-J6_cold_lightgbm_tail_calibration",
        "scope": "cold",
        "candidate": "corrected_lgb_tail_support_size_cap_0.25",
        "base_candidate": "baseline",
    },
    {
        "label": "cold_catboost_ppa7_hierarchical",
        "folder": "PP-A7_hierarchical_segment_residual_calibration",
        "scope": "cold",
        "candidate": "corrected_hierarchical",
        "base_candidate": "baseline",
    },
]


def prediction_frame(exp_id: str, candidate: str, source: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, calibration: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "model_source": source,
        "scope": MODEL_SOURCES.get(source, {}).get("scope", source.split("_")[0]),
        "split": split,
        "calibration": calibration,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def metric_row(exp_id: str, candidate: str, source: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, calibration: str, notes: str = "") -> dict[str, Any]:
    return {
        "experiment_id": exp_id,
        "candidate": candidate,
        "model_source": source,
        "scope": MODEL_SOURCES.get(source, {}).get("scope", source.split("_")[0]),
        "split": split,
        "calibration": calibration,
        "notes": notes,
        **metrics(frame, pred_log),
    }


def prepare_base_predictions() -> dict[str, dict[str, Any]]:
    features_by_key = artifact_features()
    prepared: dict[str, dict[str, Any]] = {}
    for source, cfg in MODEL_SOURCES.items():
        features = features_by_key[cfg["feature_key"]]
        train, val, test = load_scope(cfg["scope"], features)
        train = normalize(train, features)
        val = normalize(val, features)
        test = normalize(test, features)
        model = fit_base(cfg["model"], train, features)
        val_pred = predict_base(cfg["model"], model, val, features)
        test_pred = predict_base(cfg["model"], model, test, features)
        prepared[source] = {
            "features": features,
            "val": val,
            "test": test,
            "val_pred": val_pred,
            "test_pred": test_pred,
        }
    return prepared


def run_c1_c3(exp_id: str, prepared: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    corr: list[dict[str, Any]] = []
    for source, d in prepared.items():
        val = d["val"]
        test = d["test"]
        val_pred = d["val_pred"]
        test_pred = d["test_pred"]
        for split, frame, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
            rows.append(metric_row(exp_id, "baseline", source, split, frame, pred, "none"))
            preds.append(prediction_frame(exp_id, "baseline", source, split, frame, pred, "none"))

        if exp_id == "PP-C1":
            model = LinearRegression()
            model.fit(val_pred.reshape(-1, 1), val["ln_price_krw"].to_numpy(dtype=float))
            val_cal = np.asarray(model.predict(val_pred.reshape(-1, 1)), dtype=float)
            test_cal = np.asarray(model.predict(test_pred.reshape(-1, 1)), dtype=float)
            params = {"slope": float(model.coef_[0]), "intercept": float(model.intercept_)}
            name = "linear_slope_intercept"
        else:
            model = IsotonicRegression(out_of_bounds="clip")
            model.fit(val_pred, val["ln_price_krw"].to_numpy(dtype=float))
            val_cal = np.asarray(model.predict(val_pred), dtype=float)
            test_cal = np.asarray(model.predict(test_pred), dtype=float)
            params = {
                "n_thresholds": int(len(model.X_thresholds_)),
                "min_threshold": float(np.min(model.X_thresholds_)),
                "max_threshold": float(np.max(model.X_thresholds_)),
            }
            name = "monotonic_isotonic"

        for split, frame, pred in [("validation", val, val_cal), ("test", test, test_cal)]:
            rows.append(metric_row(exp_id, f"corrected_{name}", source, split, frame, pred, name))
            preds.append(prediction_frame(exp_id, f"corrected_{name}", source, split, frame, pred, name))
        corr.append({
            "experiment_id": exp_id,
            "model_source": source,
            "calibration": name,
            "validation_n": int(len(val)),
            **params,
        })
    return rows, preds, corr


def frame_from_prediction_rows(rows: pd.DataFrame) -> pd.DataFrame:
    return rows[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def run_c5() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    corr: list[dict[str, Any]] = []
    for src in C5_SOURCES:
        pred_path = BASE_EXP_DIR / src["folder"] / "outputs" / "predictions.csv"
        pred_df = pd.read_csv(pred_path)
        for split in ["validation", "test"]:
            base = pred_df[(pred_df["split"].eq(split)) & (pred_df["candidate"].eq(src["base_candidate"])) & (pred_df["scope"].eq(src["scope"]))].copy()
            corrected = pred_df[(pred_df["split"].eq(split)) & (pred_df["candidate"].eq(src["candidate"])) & (pred_df["scope"].eq(src["scope"]))].copy()
            base = base.drop_duplicates("_track6_row_id").sort_values("_track6_row_id")
            corrected = corrected.drop_duplicates("_track6_row_id").sort_values("_track6_row_id")
            merged = base[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].merge(
                corrected[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "corrected_pred_log"}),
                on="_track6_row_id",
                how="inner",
            )
            frame = frame_from_prediction_rows(merged)
            base_pred = merged["pred_log"].to_numpy(dtype=float)
            corr_pred = merged["corrected_pred_log"].to_numpy(dtype=float)
            delta = corr_pred - base_pred
            if split == "validation":
                rows.append(metric_row("PP-C5", "baseline", src["label"], split, frame, base_pred, "none", src["folder"]))
                preds.append(prediction_frame("PP-C5", "baseline", src["label"], split, frame, base_pred, "none"))
            else:
                rows.append(metric_row("PP-C5", "baseline", src["label"], split, frame, base_pred, "none", src["folder"]))
                preds.append(prediction_frame("PP-C5", "baseline", src["label"], split, frame, base_pred, "none"))
            for strength in STRENGTHS:
                scaled = base_pred + strength * delta
                candidate = f"strength_{strength:.2f}_{src['candidate']}"
                rows.append(metric_row("PP-C5", candidate, src["label"], split, frame, scaled, "strength_scaled", src["folder"]))
                preds.append(prediction_frame("PP-C5", candidate, src["label"], split, frame, scaled, "strength_scaled"))
                corr.append({
                    "experiment_id": "PP-C5",
                    "model_source": src["label"],
                    "source_folder": src["folder"],
                    "source_candidate": src["candidate"],
                    "split": split,
                    "strength": strength,
                    "median_original_delta_log": float(np.median(delta)),
                    "p95_abs_original_delta_log": float(np.quantile(np.abs(delta), 0.95)),
                })
    return rows, preds, corr


def render(exp_id: str, metrics_df: pd.DataFrame, corr_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["model_source", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 예측값 자체를 다시 맞추거나, 이미 효과가 있던 보정값의 강도를 조정해 과보정을 줄인다.",
        "- 기준: 보정식은 validation에서만 확정하고 같은 식을 test에 적용한다.",
        "",
        "## Validation 결과",
        "",
        "| 모델 소스 | 후보 | 보정 방식 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.model_source}` | `{row.candidate}` | `{row.calibration}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    for source in sorted(val["model_source"].unique()):
        scoped = val[val["model_source"].eq(source)]
        baseline = scoped[scoped["candidate"].eq("baseline")]
        if baseline.empty:
            continue
        b = baseline.iloc[0]
        best = scoped.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]
        lines.append(
            f"- `{source}` best `{best.candidate}`: baseline 대비 MdAPE `{best.MdAPE - b.MdAPE:.4f}`, "
            f"MAPE `{best.MAPE - b.MAPE:.4f}`, p95 `{best.p95_APE - b.p95_APE:.4f}`."
        )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Calibration Map</h2>{corr_df.to_html(index=False, escape=True) if not corr_df.empty else '<p>No calibration map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], corr_rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
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
        "policy": "validation calibration function applied to test",
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


def main() -> None:
    start = time.time()
    prepared = prepare_base_predictions()
    summary_rows: list[dict[str, Any]] = []
    feature_columns = {source: d["features"] for source, d in prepared.items()}
    model_manifest = {
        "base_sources": MODEL_SOURCES,
        "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
        "target": "ln_price_krw",
    }
    for exp_id in ["PP-C1", "PP-C3"]:
        rows, preds, corr = run_c1_c3(exp_id, prepared)
        write_exp(exp_id, rows, preds, corr, {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": feature_columns,
            "model_manifest": model_manifest,
        })
        df = pd.DataFrame(rows)
        summary_rows.extend(df.query("split == 'validation'").sort_values(["model_source", "MdAPE", "MAPE"]).groupby("model_source", as_index=False).head(1).to_dict("records"))

    rows, preds, corr = run_c5()
    write_exp("PP-C5", rows, preds, corr, {
        "experiment_id": "PP-C5",
        "title": EXPERIMENTS["PP-C5"]["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "feature_columns": {"source_candidates": C5_SOURCES},
        "model_manifest": {**model_manifest, "strengths": STRENGTHS},
    })
    df = pd.DataFrame(rows)
    summary_rows.extend(df.query("split == 'validation'").sort_values(["model_source", "MdAPE", "MAPE"]).groupby("model_source", as_index=False).head(1).to_dict("records"))

    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-C_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-C_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
