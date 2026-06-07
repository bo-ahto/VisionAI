#!/usr/bin/env python3
"""Run Track6 PP-A residual calibration experiments."""
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
    fit_predict,
    load_scope,
    metrics,
    normalize,
)


EXPERIMENTS = {
    "PP-A1": {"slug": "PP-A1_global_residual_calibration", "title": "전체 예측 오차 보정"},
    "PP-A2": {"slug": "PP-A2_pred_price_bin_residual_calibration", "title": "예측 가격대별 예측 오차 보정"},
    "PP-A3": {"slug": "PP-A3_size_segment_residual_calibration", "title": "호수/크기 구간별 보정"},
    "PP-A4": {"slug": "PP-A4_medium_support_residual_calibration", "title": "재료/지지체 구간별 보정"},
    "PP-A5": {"slug": "PP-A5_warm_artist_history_residual_calibration", "title": "Warm 작가 학습량 구간 보정"},
    "PP-A6": {"slug": "PP-A6_cold_meta_completeness_residual_calibration", "title": "Cold 메타 정보량 구간 보정"},
    "PP-A7": {"slug": "PP-A7_hierarchical_segment_residual_calibration", "title": "계층형 구간 보정"},
    "PP-A8": {"slug": "PP-A8_min_rows_threshold_residual_calibration", "title": "최소 표본 수 기준 보정"},
}


def pred_bins(pred_log: np.ndarray, low: float | None = None, high: float | None = None) -> tuple[np.ndarray, float, float]:
    if low is None or high is None:
        low, high = np.quantile(pred_log, [0.33, 0.66])
    return np.select([pred_log <= low, pred_log <= high], ["low", "mid"], default="high").astype(str), float(low), float(high)


def quantile_bins(values: pd.Series, prefix: str) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().sum() < 10 or numeric.nunique(dropna=True) < 3:
        return np.array([f"{prefix}_unknown"] * len(values))
    cuts = np.nanquantile(numeric, [0.33, 0.66])
    return np.select([numeric <= cuts[0], numeric <= cuts[1]], [f"{prefix}_low", f"{prefix}_mid"], default=f"{prefix}_high").astype(str)


def residual_map(actual_log: np.ndarray, pred_log: np.ndarray, segment: np.ndarray, min_rows: int = 1) -> pd.DataFrame:
    residual = actual_log - pred_log
    rows = []
    for seg in sorted(pd.Series(segment).astype(str).unique()):
        mask = segment.astype(str) == seg
        n = int(mask.sum())
        rows.append({
            "segment": seg,
            "n": n,
            "median_residual_log": float(np.median(residual[mask])) if n else float("nan"),
            "usable": bool(n >= min_rows),
        })
    return pd.DataFrame(rows)


def apply_residual_map(pred_log: np.ndarray, segment: np.ndarray, cmap: pd.DataFrame, fallback: float = 0.0) -> np.ndarray:
    values = {str(row.segment): float(row.median_residual_log) for row in cmap.itertuples() if bool(row.usable)}
    correction = np.array([values.get(str(seg), fallback) for seg in segment], dtype=float)
    return pred_log + correction


def hierarchical_map(actual_log: np.ndarray, pred_log: np.ndarray, high_seg: np.ndarray, mid_seg: np.ndarray, low_seg: np.ndarray, min_rows: int) -> pd.DataFrame:
    residual = actual_log - pred_log
    rows = []
    for level, seg_values in [("low", low_seg), ("mid", mid_seg), ("high", high_seg)]:
        for seg in sorted(pd.Series(seg_values).astype(str).unique()):
            mask = seg_values.astype(str) == seg
            n = int(mask.sum())
            rows.append({
                "level": level,
                "segment": seg,
                "n": n,
                "median_residual_log": float(np.median(residual[mask])) if n else float("nan"),
                "usable": bool(n >= min_rows),
            })
    return pd.DataFrame(rows)


def apply_hierarchical(pred_log: np.ndarray, high_seg: np.ndarray, mid_seg: np.ndarray, low_seg: np.ndarray, hmap: pd.DataFrame) -> np.ndarray:
    levels = {
        "high": {str(r.segment): float(r.median_residual_log) for r in hmap[hmap["level"].eq("high")].itertuples() if bool(r.usable)},
        "mid": {str(r.segment): float(r.median_residual_log) for r in hmap[hmap["level"].eq("mid")].itertuples() if bool(r.usable)},
        "low": {str(r.segment): float(r.median_residual_log) for r in hmap[hmap["level"].eq("low")].itertuples() if bool(r.usable)},
    }
    correction = []
    for hi, mid, low in zip(high_seg, mid_seg, low_seg, strict=False):
        correction.append(levels["high"].get(str(hi), levels["mid"].get(str(mid), levels["low"].get(str(low), 0.0))))
    return pred_log + np.array(correction, dtype=float)


def pred_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str, status: str = "ok") -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "segment_rule": segment_rule,
        "status": status,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str, status: str = "ok", notes: str = "") -> None:
    rows.append({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "segment_rule": segment_rule,
        "status": status,
        "notes": notes,
        **metrics(frame, pred_log),
    })


def material_segment(scope: str, frame: pd.DataFrame) -> np.ndarray:
    if scope == "warm":
        if "medium_support_bucket" in frame.columns:
            return frame["medium_support_bucket"].astype(str).to_numpy()
        return (frame["medium_category"].astype(str) + "__" + frame["support_category"].astype(str)).to_numpy()
    if "medium_shape_bucket" in frame.columns:
        return frame["medium_shape_bucket"].astype(str).to_numpy()
    return (frame["medium_category"].astype(str) + "__" + frame["support_category"].astype(str)).to_numpy()


def render(exp_id: str, metrics_df: pd.DataFrame, cmap_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: validation residual 중앙값으로 보정값을 만들고 같은 기준을 test에 적용한다.",
        "- 해석: MdAPE가 유지/개선되고 p95_APE가 악화되지 않으면 PP-A 후보로 유지한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log | 상태 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.scope}` | `{row.candidate}` | `{row.segment_rule}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` | `{row.status}` |")
    lines += ["", "## 코멘터리", ""]
    for scope in sorted(val["scope"].unique()):
        scoped = val[val["scope"].eq(scope)]
        baseline = scoped[scoped["candidate"].eq("baseline")]
        if baseline.empty:
            continue
        b = baseline.iloc[0]
        for row in scoped[scoped["candidate"].ne("baseline")].itertuples():
            lines.append(
                f"- `{scope}` `{row.segment_rule}`: MdAPE delta `{row.MdAPE - b.MdAPE:.4f}`, "
                f"MAPE delta `{row.MAPE - b.MAPE:.4f}`, p95 delta `{row.p95_APE - b.p95_APE:.4f}`."
            )
    if not cmap_df.empty:
        lines.append(f"- correction map rows: `{len(cmap_df)}`.")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Correction Map</h2>{cmap_df.head(120).to_html(index=False, escape=True) if not cmap_df.empty else '<p>No correction map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], maps: list[pd.DataFrame], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    map_df = pd.concat(maps, ignore_index=True) if maps else pd.DataFrame()
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "validation correction map applied to test"}, ensure_ascii=False, indent=2), encoding="utf-8")
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
    features_by_key = artifact_features()
    scopes = {
        "warm": {"features": features_by_key["warm"], "model": "huber"},
        "cold": {"features": features_by_key["cold_catboost"], "model": "catboost"},
    }
    data: dict[str, dict[str, Any]] = {}
    for scope, cfg in scopes.items():
        train, val, test = load_scope(scope, cfg["features"])
        train = normalize(train, cfg["features"])
        val = normalize(val, cfg["features"])
        test = normalize(test, cfg["features"])
        pred = fit_predict(cfg["model"], train, val, test, cfg["features"])
        data[scope] = {"train": train, "val": val, "test": test, "pred": pred, **cfg}

    summary_rows = []
    for exp_id in EXPERIMENTS:
        metric_rows: list[dict[str, Any]] = []
        pred_rows: list[pd.DataFrame] = []
        maps: list[pd.DataFrame] = []
        for scope, d in data.items():
            val, test = d["val"], d["test"]
            val_pred, test_pred = d["pred"]["validation"], d["pred"]["test"]
            if exp_id == "PP-A5" and scope != "warm":
                continue
            if exp_id == "PP-A6" and scope != "cold":
                continue
            for split_name, frame, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
                add_metric(metric_rows, exp_id, "baseline", scope, split_name, frame, pred, "none")
                pred_rows.append(pred_frame(exp_id, "baseline", scope, split_name, frame, pred, "none"))

            rules: list[tuple[str, np.ndarray, np.ndarray, int, str]] = []
            if exp_id == "PP-A1":
                rules = [("overall", np.array(["overall"] * len(val)), np.array(["overall"] * len(test)), 1, "ok")]
            elif exp_id == "PP-A2":
                val_seg, lo, hi = pred_bins(val_pred)
                test_seg, _lo, _hi = pred_bins(test_pred, lo, hi)
                rules = [("pred_bin", val_seg, test_seg, 1, "ok")]
            elif exp_id == "PP-A3":
                rules = [("size_bucket", val["size_bucket"].astype(str).to_numpy(), test["size_bucket"].astype(str).to_numpy(), 1, "ok")]
            elif exp_id == "PP-A4":
                rules = [("material_support", material_segment(scope, val), material_segment(scope, test), 30, "ok")]
            elif exp_id == "PP-A5":
                col = "artist_works_log" if "artist_works_log" in val.columns else "artist_works_count_train"
                rules = [("artist_works_bucket", quantile_bins(val[col], "works"), quantile_bins(test[col], "works"), 1, "ok")]
            elif exp_id == "PP-A6":
                meta_cols = [c for c in val.columns if "meta" in c or "artist_" in c and c not in {"artist_key"}]
                if not meta_cols:
                    rules = [("meta_completeness_unavailable", np.array(["unavailable"] * len(val)), np.array(["unavailable"] * len(test)), 1, "column_unavailable")]
                else:
                    val_missing = val[meta_cols].isna().sum(axis=1)
                    test_missing = test[meta_cols].isna().sum(axis=1)
                    rules = [("meta_missing_count", quantile_bins(val_missing, "meta_missing"), quantile_bins(test_missing, "meta_missing"), 1, "ok")]
            elif exp_id == "PP-A7":
                pred_val, lo, hi = pred_bins(val_pred)
                pred_test, _lo, _hi = pred_bins(test_pred, lo, hi)
                size_val = val["size_bucket"].astype(str).to_numpy()
                size_test = test["size_bucket"].astype(str).to_numpy()
                mat_val = np.array([f"{p}__{s}__{m}" for p, s, m in zip(pred_val, size_val, material_segment(scope, val), strict=False)])
                mat_test = np.array([f"{p}__{s}__{m}" for p, s, m in zip(pred_test, size_test, material_segment(scope, test), strict=False)])
                hmap = hierarchical_map(val["ln_price_krw"].to_numpy(dtype=float), val_pred, mat_val, np.array([f"{p}__{s}" for p, s in zip(pred_val, size_val, strict=False)]), pred_val, 30)
                corrected = {
                    "validation": apply_hierarchical(val_pred, mat_val, np.array([f"{p}__{s}" for p, s in zip(pred_val, size_val, strict=False)]), pred_val, hmap),
                    "test": apply_hierarchical(test_pred, mat_test, np.array([f"{p}__{s}" for p, s in zip(pred_test, size_test, strict=False)]), pred_test, hmap),
                }
                hmap.insert(0, "scope", scope)
                hmap.insert(1, "experiment_id", exp_id)
                hmap.insert(2, "segment_rule", "hierarchical_pred_size_material")
                maps.append(hmap)
                for split_name, frame, pred in [("validation", val, corrected["validation"]), ("test", test, corrected["test"])]:
                    add_metric(metric_rows, exp_id, "corrected_hierarchical", scope, split_name, frame, pred, "hierarchical_pred_size_material")
                    pred_rows.append(pred_frame(exp_id, "corrected_hierarchical", scope, split_name, frame, pred, "hierarchical_pred_size_material"))
                continue
            elif exp_id == "PP-A8":
                pred_val, lo, hi = pred_bins(val_pred)
                pred_test, _lo, _hi = pred_bins(test_pred, lo, hi)
                size_val = val["size_bucket"].astype(str).to_numpy()
                size_test = test["size_bucket"].astype(str).to_numpy()
                high_val = np.array([f"{p}__{s}__{m}" for p, s, m in zip(pred_val, size_val, material_segment(scope, val), strict=False)])
                high_test = np.array([f"{p}__{s}__{m}" for p, s, m in zip(pred_test, size_test, material_segment(scope, test), strict=False)])
                mid_val = np.array([f"{p}__{s}" for p, s in zip(pred_val, size_val, strict=False)])
                mid_test = np.array([f"{p}__{s}" for p, s in zip(pred_test, size_test, strict=False)])
                for min_rows in [30, 50, 100]:
                    hmap = hierarchical_map(val["ln_price_krw"].to_numpy(dtype=float), val_pred, high_val, mid_val, pred_val, min_rows)
                    corrected_val = apply_hierarchical(val_pred, high_val, mid_val, pred_val, hmap)
                    corrected_test = apply_hierarchical(test_pred, high_test, mid_test, pred_test, hmap)
                    hmap.insert(0, "scope", scope)
                    hmap.insert(1, "experiment_id", exp_id)
                    hmap.insert(2, "segment_rule", f"hierarchical_min_rows_{min_rows}")
                    maps.append(hmap)
                    for split_name, frame, pred in [("validation", val, corrected_val), ("test", test, corrected_test)]:
                        candidate = f"corrected_min_rows_{min_rows}"
                        add_metric(metric_rows, exp_id, candidate, scope, split_name, frame, pred, f"hierarchical_min_rows_{min_rows}")
                        pred_rows.append(pred_frame(exp_id, candidate, scope, split_name, frame, pred, f"hierarchical_min_rows_{min_rows}"))
                continue

            for rule_name, val_seg, test_seg, min_rows, status in rules:
                cmap = residual_map(val["ln_price_krw"].to_numpy(dtype=float), val_pred, val_seg, min_rows=min_rows)
                cmap.insert(0, "scope", scope)
                cmap.insert(1, "experiment_id", exp_id)
                cmap.insert(2, "segment_rule", rule_name)
                maps.append(cmap)
                if status == "column_unavailable":
                    corrected = {"validation": val_pred.copy(), "test": test_pred.copy()}
                    notes = "required operational metadata columns are unavailable in current cold feature split"
                else:
                    corrected = {
                        "validation": apply_residual_map(val_pred, val_seg, cmap),
                        "test": apply_residual_map(test_pred, test_seg, cmap),
                    }
                    notes = ""
                for split_name, frame, pred in [("validation", val, corrected["validation"]), ("test", test, corrected["test"])]:
                    add_metric(metric_rows, exp_id, f"corrected_{rule_name}", scope, split_name, frame, pred, rule_name, status=status, notes=notes)
                    pred_rows.append(pred_frame(exp_id, f"corrected_{rule_name}", scope, split_name, frame, pred, rule_name, status=status))

        config = {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {scope: d["features"] for scope, d in data.items()},
            "model_manifest": {
                "warm": "Huber(base_existing_combo)",
                "cold": "CatBoost(base_medium_shape)",
                "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
            },
        }
        write_exp(exp_id, metric_rows, pred_rows, maps, config)
        best = pd.DataFrame(metric_rows)
        row = best[best["split"].eq("validation")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"]).groupby("scope").head(1)
        for _idx, item in row.iterrows():
            out = item.to_dict()
            out["folder"] = str((BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]).relative_to(REPO))
            summary_rows.append(out)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(BASE_EXP_DIR / "PP-A_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-A_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
