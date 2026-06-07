#!/usr/bin/env python3
"""Run Track6 PP-F price range and confidence policy experiments."""
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

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, SPLIT_ROOT, metrics  # noqa: E402


EXPERIMENTS = {
    "PP-F1": {"slug": "PP-F1_warm_price_range_policy", "title": "Warm 가격 범위 검증"},
    "PP-F2": {"slug": "PP-F2_cold_price_range_policy", "title": "Cold 가격 범위 검증"},
    "PP-F3": {"slug": "PP-F3_confidence_grade_policy", "title": "신뢰도 등급 기준"},
    "PP-F4": {"slug": "PP-F4_confidence_tiered_price_range", "title": "신뢰도별 가격 범위 차등 적용"},
}

RANGE_LEVELS = [0.70, 0.80, 0.90]


SOURCES = {
    "warm_huber": ("PP-B4_oof_base_residual_source", "baseline", "warm", "warm_huber"),
    "warm_best": ("PP-D4_warm_three_model_blend", "weighted_warm_huber_catboost_l8_w_0.25_0.00_0.75", "warm", None),
    "cold_lightgbm": ("PP-B4_oof_base_residual_source", "baseline", "cold", "cold_lightgbm"),
    "cold_quantile_q50": ("PP-K1_quantile_price_range_auxiliary", "quantile_q50", "cold", None),
}


def load_source(key: str, split: str) -> pd.DataFrame:
    folder, candidate, scope, model_source = SOURCES[key]
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq(scope) & df["split"].astype(str).eq(split)
    if model_source and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(model_source)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source {key} {split}")
    return out


def frame(df: pd.DataFrame) -> pd.DataFrame:
    return df[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def range_predictions(exp_id: str, candidate: str, scope: str, split: str, df: pd.DataFrame, width: float, policy: str, confidence: np.ndarray | None = None) -> pd.DataFrame:
    pred_log = df["pred_log"].to_numpy(dtype=float)
    actual_log = df["actual_log"].to_numpy(dtype=float)
    lower_log = pred_log - width
    upper_log = pred_log + width
    covered = (actual_log >= lower_log) & (actual_log <= upper_log)
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "_track6_row_id": df["_track6_row_id"],
        "actual_log": df["actual_log"],
        "pred_log": pred_log,
        "actual_price": df["actual_price"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "lower_price": np.clip(np.exp(lower_log), 1_000.0, None),
        "upper_price": np.clip(np.exp(upper_log), 1_000.0, None),
        "range_width_log": 2.0 * width,
        "range_ratio": np.exp(2.0 * width),
        "covered": covered,
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if confidence is not None:
        out["confidence_grade"] = confidence
    return out


def metric_row(exp_id: str, candidate: str, scope: str, split: str, df: pd.DataFrame, pred_log: np.ndarray, policy: str, coverage: float | None = None, median_ratio: float | None = None, notes: str = "") -> dict[str, Any]:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame(df), pred_log),
    }
    if coverage is not None:
        row["range_coverage"] = float(coverage)
    if median_ratio is not None:
        row["median_range_ratio"] = float(median_ratio)
    return row


def run_range(exp_id: str, source_key: str, scope: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = load_source(source_key, "validation")
    test = load_source(source_key, "test")
    abs_resid = np.abs(val["actual_log"].to_numpy(dtype=float) - val["pred_log"].to_numpy(dtype=float))
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, df in [("validation", val), ("test", test)]:
        rows.append(metric_row(exp_id, "baseline_point_prediction", scope, split, df, df["pred_log"].to_numpy(dtype=float), "point_prediction"))
    for level in RANGE_LEVELS:
        width = float(np.quantile(abs_resid, level))
        candidate = f"range_{int(level * 100)}pct"
        for split, df in [("validation", val), ("test", test)]:
            pred_df = range_predictions(exp_id, candidate, scope, split, df, width, "global_abs_residual_quantile")
            preds.append(pred_df)
            rows.append(metric_row(exp_id, candidate, scope, split, df, df["pred_log"].to_numpy(dtype=float), "global_abs_residual_quantile", pred_df["covered"].mean(), pred_df["range_ratio"].median()))
        maps.append({"experiment_id": exp_id, "scope": scope, "source": source_key, "target_coverage": level, "half_width_log": width, "range_ratio": float(np.exp(2 * width))})
    baseline_preds = []
    for split, df in [("validation", val), ("test", test)]:
        base = range_predictions(exp_id, "baseline_point_prediction", scope, split, df, 0.0, "point_prediction")
        baseline_preds.append(base)
    return rows, baseline_preds + preds, maps


def confidence_inputs(scope: str, split: str, source_key: str) -> pd.DataFrame:
    base = load_source(source_key, split)
    q = pd.read_csv(BASE_EXP_DIR / "PP-K1_quantile_price_range_auxiliary" / "outputs" / "predictions.csv")
    q = q[(q["scope"].astype(str).eq(scope)) & (q["split"].astype(str).eq(split)) & (q["candidate"].astype(str).eq("quantile_q50"))]
    q = q[["_track6_row_id", "quantile_width", "price_range_ratio"]].drop_duplicates("_track6_row_id")
    return base.merge(q, on="_track6_row_id", how="left")


def grade_by_width(val: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    q = val["quantile_width"].fillna(val["quantile_width"].median())
    low, high = np.quantile(q, [0.33, 0.66])
    w = df["quantile_width"].fillna(q.median()).to_numpy(dtype=float)
    return np.select([w <= low, w <= high], ["high", "medium"], default="low")


def run_f3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    specs = {"warm": "warm_huber", "cold": "cold_lightgbm"}
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for scope, source in specs.items():
        val = confidence_inputs(scope, "validation", source)
        test = confidence_inputs(scope, "test", source)
        for split, df in [("validation", val), ("test", test)]:
            grade = grade_by_width(val, df)
            pred = range_predictions("PP-F3", "confidence_grade", scope, split, df, 0.0, "quantile_width_grade", grade)
            preds.append(pred)
            rows.append(metric_row("PP-F3", "confidence_grade", scope, split, df, df["pred_log"].to_numpy(dtype=float), "quantile_width_grade"))
            for g in ["high", "medium", "low"]:
                part = pred[pred["confidence_grade"].eq(g)].copy()
                if part.empty:
                    continue
                rows.append(metric_row("PP-F3", f"grade_{g}", scope, split, part, part["pred_log"].to_numpy(dtype=float), "quantile_width_grade", notes=f"n={len(part)}"))
        for g, part in preds[-2].groupby("confidence_grade"):
            maps.append({"experiment_id": "PP-F3", "scope": scope, "grade": g, "validation_n": int(len(part)), "median_quantile_width": float(part.get("quantile_width", pd.Series(dtype=float)).median()) if "quantile_width" in part else None})
    return rows, preds, maps


def run_f4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    specs = {"warm": "warm_huber", "cold": "cold_lightgbm"}
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for scope, source in specs.items():
        val = confidence_inputs(scope, "validation", source)
        test = confidence_inputs(scope, "test", source)
        val_grade = grade_by_width(val, val)
        val = val.copy()
        val["confidence_grade"] = val_grade
        width_by_grade = {}
        for grade, level in [("high", 0.70), ("medium", 0.80), ("low", 0.90)]:
            part = val[val["confidence_grade"].eq(grade)]
            resid = np.abs(part["actual_log"].to_numpy(dtype=float) - part["pred_log"].to_numpy(dtype=float))
            width_by_grade[grade] = float(np.quantile(resid, level)) if len(resid) else float(np.quantile(np.abs(val["actual_log"] - val["pred_log"]), 0.80))
        for split, df in [("validation", val), ("test", test)]:
            grade = grade_by_width(val, df)
            pred_log = df["pred_log"].to_numpy(dtype=float)
            widths = np.array([width_by_grade[g] for g in grade], dtype=float)
            actual_log = df["actual_log"].to_numpy(dtype=float)
            covered = (actual_log >= pred_log - widths) & (actual_log <= pred_log + widths)
            out = pd.DataFrame({
                "experiment_id": "PP-F4",
                "candidate": "tiered_range_by_confidence",
                "scope": scope,
                "split": split,
                "policy": "confidence_tiered_range",
                "_track6_row_id": df["_track6_row_id"],
                "actual_log": df["actual_log"],
                "pred_log": pred_log,
                "actual_price": df["actual_price"],
                "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
                "lower_price": np.clip(np.exp(pred_log - widths), 1_000.0, None),
                "upper_price": np.clip(np.exp(pred_log + widths), 1_000.0, None),
                "range_width_log": 2 * widths,
                "range_ratio": np.exp(2 * widths),
                "covered": covered,
                "confidence_grade": grade,
            })
            out["residual_log"] = out["actual_log"] - out["pred_log"]
            out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
            preds.append(out)
            rows.append(metric_row("PP-F4", "tiered_range_by_confidence", scope, split, df, pred_log, "confidence_tiered_range", out["covered"].mean(), out["range_ratio"].median()))
        for grade, width in width_by_grade.items():
            maps.append({"experiment_id": "PP-F4", "scope": scope, "grade": grade, "half_width_log": width, "range_ratio": float(np.exp(2 * width))})
    return rows, preds, maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy()
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 단일 가격 예측을 서비스에서 어떤 범위와 신뢰도 문구로 보여줄지 검증한다.",
        "- 기준: 범위 폭과 등급 기준은 validation에서 정하고 test에는 그대로 적용한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | 포함률 | 범위비 중앙값 |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in val.sort_values([c for c in ["scope", "candidate"] if c in val.columns]).itertuples():
        lines.append(
            f"| `{row.scope}` | `{row.candidate}` | `{row.policy}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | "
            f"`{getattr(row, 'range_coverage', float('nan')):.4f}` | `{getattr(row, 'median_range_ratio', float('nan')):.4f}` |"
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
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "validation display policy applied to test"}, ensure_ascii=False, indent=2), encoding="utf-8")
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
    runs = {
        "PP-F1": lambda: run_range("PP-F1", "warm_huber", "warm"),
        "PP-F2": lambda: run_range("PP-F2", "cold_lightgbm", "cold"),
        "PP-F3": run_f3,
        "PP-F4": run_f4,
    }
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runs.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps, {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {"prediction_sources": SOURCES},
            "model_manifest": {"target": "ln_price_krw", "mode": "display_policy"},
        })
        df = pd.DataFrame(rows)
        val = df[df["split"].astype(str).eq("validation")].copy()
        if not val.empty:
            summary_rows.extend(val.sort_values([c for c in ["scope", "candidate"] if c in val.columns]).to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-F_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-F_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
