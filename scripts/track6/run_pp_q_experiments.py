#!/usr/bin/env python3
"""Run Track6 PP-Q model-combination and model-custom tuning experiments."""
from __future__ import annotations

import html
import importlib.util
import json
import sys
import time
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXPERIMENTS = {
    "PP-Q1": {"slug": "PP-Q1_cold_width_routing_with_catboost_quantile", "title": "Cold Quantile width 라우팅 + CatBoost Quantile 추가"},
    "PP-Q2": {"slug": "PP-Q2_cold_weighted_blend_custom", "title": "Cold 모델 가중 결합 커스텀"},
    "PP-Q3": {"slug": "PP-Q3_cold_point_range_joint_policy", "title": "Cold 점 예측 + 가격 범위 joint policy"},
    "PP-Q4": {"slug": "PP-Q4_probabilistic_model_candidate_check", "title": "Probabilistic 모델 후보 검토"},
}

COLD_SOURCES = [
    ("baseline_lgb", "PP-B4_oof_base_residual_source", "baseline", "cold_lightgbm"),
    ("quantile_lgb_q50", "PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", None),
    ("catboost_quantile_q50", "PP-N2_cold_catboost_quantile_range", "catboost_quantile_q50", None),
    ("hgb", "PP-O2_cold_explainable_nonlinear_hgb", "hist_gradient_boosting", None),
]


def source_prediction(folder: str, candidate: str, scope: str, split: str, model_source: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(candidate) & df["scope"].astype(str).eq(scope) & df["split"].astype(str).eq(split)
    if model_source and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(model_source)
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing prediction source folder={folder} candidate={candidate} scope={scope} split={split}")
    return out


def merge_sources(sources: list[tuple[str, str, str, str | None]], split: str) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, folder, candidate, model_source in sources:
        src = source_prediction(folder, candidate, "cold", split, model_source)
        part = src[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": label})
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part[["_track6_row_id", label]], on="_track6_row_id", how="inner")
    if merged is None or merged.empty:
        raise ValueError("empty merged predictions")
    return merged


def metric_frame(merged: pd.DataFrame) -> pd.DataFrame:
    return merged[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def prediction_frame(exp_id: str, candidate: str, split: str, merged: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "_track6_row_id": merged["_track6_row_id"],
        "actual_log": merged["actual_log"],
        "pred_log": pred_log,
        "actual_price": merged["actual_price"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, split: str, merged: pd.DataFrame, pred_log: np.ndarray, policy: str, extra: dict[str, Any] | None = None) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metrics(metric_frame(merged), pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def add_width(merged: pd.DataFrame, split: str) -> pd.DataFrame:
    width_src = source_prediction("PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range", "cold", split)
    w = width_src[["_track6_row_id", "range_low_log", "range_high_log"]].copy()
    w["routing_width"] = w["range_high_log"] - w["range_low_log"]
    return merged.merge(w[["_track6_row_id", "routing_width"]], on="_track6_row_id", how="inner")


def select_by_segment(val: pd.DataFrame, test: pd.DataFrame, candidates: list[str], objective: str) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    q1, q2 = np.quantile(val["routing_width"].to_numpy(dtype=float), [0.33, 0.66])
    segments = [(-np.inf, q1, "stable"), (q1, q2, "caution"), (q2, np.inf, "risk")]
    val_pred = pd.Series(index=val.index, dtype=float)
    test_pred = pd.Series(index=test.index, dtype=float)
    selected: list[dict[str, Any]] = []
    for low, high, name in segments:
        mask_val = (val["routing_width"] > low) & (val["routing_width"] <= high)
        mask_test = (test["routing_width"] > low) & (test["routing_width"] <= high)
        frame = metric_frame(val.loc[mask_val])
        scores = {}
        for cand in candidates:
            if not mask_val.any():
                scores[cand] = np.inf
            else:
                scores[cand] = metrics(frame, val.loc[mask_val, cand].to_numpy(dtype=float))[objective]
        if objective == "MAPE":
            base_mdape = metrics(frame, val.loc[mask_val, "baseline_lgb"].to_numpy(dtype=float))["MdAPE"] if mask_val.any() else np.inf
            guarded = {}
            for cand in candidates:
                if not mask_val.any():
                    guarded[cand] = np.inf
                    continue
                cand_mdape = metrics(frame, val.loc[mask_val, cand].to_numpy(dtype=float))["MdAPE"]
                guarded[cand] = scores[cand] if cand_mdape <= base_mdape * 1.08 else np.inf
            if min(guarded.values()) < np.inf:
                scores = guarded
        best = min(scores, key=scores.get)
        val_pred.loc[mask_val] = val.loc[mask_val, best].to_numpy(dtype=float)
        test_pred.loc[mask_test] = test.loc[mask_test, best].to_numpy(dtype=float)
        selected.append({
            "segment": name,
            "objective": objective,
            "width_low": float(low) if np.isfinite(low) else None,
            "width_high": float(high) if np.isfinite(high) else None,
            "selected_candidate": best,
            "validation_rows": int(mask_val.sum()),
            "test_rows": int(mask_test.sum()),
            **{f"val_{objective.lower()}_{k}": float(v) for k, v in scores.items()},
        })
    val_pred = val_pred.fillna(val["baseline_lgb"])
    test_pred = test_pred.fillna(test["baseline_lgb"])
    return val_pred.to_numpy(dtype=float), test_pred.to_numpy(dtype=float), selected


def run_q1() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = add_width(merge_sources(COLD_SOURCES, "validation"), "validation")
    test = add_width(merge_sources(COLD_SOURCES, "test"), "test")
    candidates = [s[0] for s in COLD_SOURCES]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split, merged in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-Q1", f"component_{cand}", split, merged, merged[cand].to_numpy(dtype=float), "routing_component")
    for objective in ["MdAPE", "MAPE"]:
        val_pred, test_pred, selected = select_by_segment(val, test, candidates, objective)
        maps.extend([{"experiment_id": "PP-Q1", **item} for item in selected])
        for split, merged, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
            candidate = f"width_routing_{objective.lower()}_objective"
            add_metric(rows, "PP-Q1", candidate, split, merged, pred, "width_segment_model_selection")
            preds.append(prediction_frame("PP-Q1", candidate, split, merged, pred, "width_segment_model_selection", {"routing_width": merged["routing_width"].to_numpy(dtype=float)}))
    return rows, preds, maps


def weight_grid(n: int, step: float = 0.25) -> list[tuple[float, ...]]:
    units = int(round(1 / step))
    out: list[tuple[float, ...]] = []
    for combo in product(range(units + 1), repeat=n):
        if sum(combo) == units:
            out.append(tuple(c / units for c in combo))
    return out


def best_weighted(val: pd.DataFrame, candidates: list[str], objective: str) -> tuple[tuple[float, ...], np.ndarray, float]:
    arr = [val[c].to_numpy(dtype=float) for c in candidates]
    frame = metric_frame(val)
    best_score = np.inf
    best_weights = tuple([1.0] + [0.0] * (len(candidates) - 1))
    best_pred = arr[0]
    for weights in weight_grid(len(candidates), 0.25):
        pred = sum(w * a for w, a in zip(weights, arr, strict=True))
        m = metrics(frame, pred)
        score = m[objective]
        if objective == "MAPE" and m["MdAPE"] > metrics(frame, val["baseline_lgb"].to_numpy(dtype=float))["MdAPE"] * 1.08:
            continue
        if score < best_score:
            best_score = score
            best_weights = weights
            best_pred = pred
    return best_weights, best_pred, float(best_score)


def run_q2() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_sources(COLD_SOURCES, "validation")
    test = merge_sources(COLD_SOURCES, "test")
    candidates = [s[0] for s in COLD_SOURCES]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for objective in ["MdAPE", "MAPE"]:
        weights, val_pred, score = best_weighted(val, candidates, objective)
        test_pred = sum(w * test[c].to_numpy(dtype=float) for w, c in zip(weights, candidates, strict=True))
        maps.append({
            "experiment_id": "PP-Q2",
            "objective": objective,
            "validation_score": score,
            **{f"weight_{c}": w for c, w in zip(candidates, weights, strict=True)},
        })
        for split, merged, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
            candidate = f"weighted_blend_{objective.lower()}_objective"
            add_metric(rows, "PP-Q2", candidate, split, merged, pred, "weighted_log_prediction_blend")
            preds.append(prediction_frame("PP-Q2", candidate, split, merged, pred, "weighted_log_prediction_blend"))
    for split, merged in [("validation", val), ("test", test)]:
        for cand in candidates:
            add_metric(rows, "PP-Q2", f"component_{cand}", split, merged, merged[cand].to_numpy(dtype=float), "blend_component")
    return rows, preds, maps


def range_stats(merged: pd.DataFrame, low: np.ndarray, high: np.ndarray) -> dict[str, float]:
    y = merged["actual_log"].to_numpy(dtype=float)
    lo = np.minimum(low, high)
    hi = np.maximum(low, high)
    return {
        "range_coverage": float(np.mean((y >= lo) & (y <= hi))),
        "median_range_ratio": float(np.median(np.exp(hi - lo))),
    }


def range_source(folder: str, candidate: str, split: str) -> pd.DataFrame:
    src = source_prediction(folder, candidate, "cold", split)
    required = {"_track6_row_id", "range_low_log", "range_high_log"}
    if not required.issubset(src.columns):
        raise ValueError(f"{folder}/{candidate} missing range columns")
    return src[["_track6_row_id", "range_low_log", "range_high_log"]]


def run_q3() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    point_sources = [
        ("q1_mdape", "PP-Q1_cold_width_routing_with_catboost_quantile", "width_routing_mdape_objective"),
        ("q1_mape", "PP-Q1_cold_width_routing_with_catboost_quantile", "width_routing_mape_objective"),
        ("q2_mdape", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mdape_objective"),
        ("q2_mape", "PP-Q2_cold_weighted_blend_custom", "weighted_blend_mape_objective"),
    ]
    range_sources = [
        ("n1_quantile_conformal", "PP-N1_cold_quantile_lightgbm_conformal_range", "quantile_lgbm_q50_conformal_range"),
        ("n2_catboost_quantile", "PP-N2_cold_catboost_quantile_range", "catboost_quantile_q50"),
        ("n3_conformal_80", "PP-N3_cold_conformal_baseline_range", "range_80pct_conformal"),
        ("n3_conformal_90", "PP-N3_cold_conformal_baseline_range", "range_90pct_conformal"),
    ]
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        for point_label, point_folder, point_candidate in point_sources:
            point = source_prediction(point_folder, point_candidate, "cold", split)
            frame = point[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].copy()
            for range_label, range_folder, range_candidate in range_sources:
                r = range_source(range_folder, range_candidate, split)
                merged = frame.merge(r, on="_track6_row_id", how="inner")
                pred = merged["pred_log"].to_numpy(dtype=float)
                extra = range_stats(merged, merged["range_low_log"].to_numpy(dtype=float), merged["range_high_log"].to_numpy(dtype=float))
                candidate = f"{point_label}_point__{range_label}_range"
                add_metric(rows, "PP-Q3", candidate, split, merged, pred, "point_range_joint_policy", extra)
                preds.append(prediction_frame("PP-Q3", candidate, split, merged, pred, "point_range_joint_policy", {
                    "range_low_log": merged["range_low_log"].to_numpy(dtype=float),
                    "range_high_log": merged["range_high_log"].to_numpy(dtype=float),
                }))
                if split == "validation":
                    maps.append({"experiment_id": "PP-Q3", "point_policy": point_label, "range_policy": range_label, **extra})
    return rows, preds, maps


def run_q4() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows = [{
        "experiment_id": "PP-Q4",
        "candidate": "ngboost_probabilistic_regression",
        "scope": "cold",
        "split": "not_run",
        "policy": "optional_probabilistic_model",
        "status": "blocked_missing_dependency" if importlib.util.find_spec("ngboost") is None else "available_not_executed",
        "notes": "NGBoost는 현재 로컬 환경에 설치되어 있지 않아 실행하지 않음. 설치 후 확률분포 예측 후보로 재검증 가능.",
    }]
    maps = [{"experiment_id": "PP-Q4", "dependency": "ngboost", "installed": importlib.util.find_spec("ngboost") is not None}]
    return rows, [], maps


def render(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 모델별 장점을 조합하고 커스텀해 Cold 성능 개선 가능성을 확인한다.",
        "- 기준: validation에서 선택한 조합/가중치/정책을 test에 그대로 적용한다.",
        "",
    ]
    if {"split", "MdAPE"}.issubset(metrics_df.columns):
        val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy()
        lines += [
            "## Validation 결과",
            "",
            "| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | coverage | range ratio |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in val.sort_values([c for c in ["MdAPE", "MAPE", "p95_APE"] if c in val.columns]).itertuples():
            lines.append(
                f"| `{getattr(row, 'candidate', '')}` | `{getattr(row, 'policy', '')}` | "
                f"`{getattr(row, 'MdAPE', float('nan')):.4f}` | `{getattr(row, 'MAPE', float('nan')):.4f}` | "
                f"`{getattr(row, 'p95_APE', float('nan')):.4f}` | `{getattr(row, 'RMSE_log', float('nan')):.4f}` | "
                f"`{getattr(row, 'range_coverage', float('nan')):.4f}` | `{getattr(row, 'median_range_ratio', float('nan')):.4f}` |"
            )
    else:
        lines += ["## 실행 상태", "", "| 항목 | 값 |", "|---|---|"]
        for row in metrics_df.to_dict("records"):
            for key, value in row.items():
                lines.append(f"| `{key}` | `{value}` |")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy Map</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
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
        pred_df[pred_df["split"].astype(str).eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
        pred_df[pred_df["split"].astype(str).eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "experiment_config.json").write_text(json.dumps({"experiment_id": exp_id, "title": EXPERIMENTS[exp_id]["title"], "run_id": datetime.now().strftime("%Y%m%d_%H%M%S")}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(map_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps({"target": "ln_price_krw", "mode": "prediction_combination"}, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    runners = {"PP-Q1": run_q1, "PP-Q2": run_q2, "PP-Q3": run_q3, "PP-Q4": run_q4}
    summary_rows: list[dict[str, Any]] = []
    for exp_id, runner in runners.items():
        rows, preds, maps = runner()
        write_exp(exp_id, rows, preds, maps)
        df = pd.DataFrame(rows)
        if {"split", "MdAPE"}.issubset(df.columns):
            val = df[df["split"].astype(str).eq("validation")].copy()
            if not val.empty:
                summary_rows.extend(val.sort_values([c for c in ["MdAPE", "MAPE", "p95_APE"] if c in val.columns]).head(3).to_dict("records"))
        else:
            summary_rows.extend(df.to_dict("records"))
    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-Q_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-Q_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
