#!/usr/bin/env python3
"""Run Track6 PRE-CAL correction-map experiments."""
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
    "PRE-CAL-W": {
        "slug": "PRE-CAL-W_warm_huber_correction_map",
        "title": "Warm Huber 상세 보정값 산출",
        "scope": "warm",
        "model": "huber",
        "feature_key": "warm",
        "segments": ["overall", "pred_bin", "size_bucket"],
    },
    "PRE-CAL-CB": {
        "slug": "PRE-CAL-CB_cold_catboost_correction_map",
        "title": "Cold CatBoost 상세 보정값 산출",
        "scope": "cold",
        "model": "catboost",
        "feature_key": "cold_catboost",
        "segments": ["overall", "leaf_segment", "medium_shape_bucket", "shape_bucket"],
    },
    "PRE-CAL-LGB": {
        "slug": "PRE-CAL-LGB_cold_lightgbm_correction_map",
        "title": "Cold LightGBM 상세 보정값 산출",
        "scope": "cold",
        "model": "lightgbm",
        "feature_key": "cold_lightgbm",
        "segments": ["overall", "pred_bin", "size_bucket", "support_size_bucket", "tail_risk_segment"],
    },
}


def pred_bins(pred_log: np.ndarray, low: float | None = None, high: float | None = None) -> tuple[np.ndarray, float, float]:
    if low is None or high is None:
        low, high = np.quantile(pred_log, [0.33, 0.66])
    bins = np.select([pred_log <= low, pred_log <= high], ["low", "mid"], default="high")
    return bins.astype(str), float(low), float(high)


def tail_segments(frame: pd.DataFrame, pred_log: np.ndarray, low: float | None = None, high: float | None = None) -> tuple[np.ndarray, float, float]:
    size = frame["size_bucket"].astype(str).to_numpy() if "size_bucket" in frame.columns else np.array(["unknown"] * len(frame))
    pred_bin, low_cut, high_cut = pred_bins(pred_log, low, high)
    return np.array([f"{p}__{s}" for p, s in zip(pred_bin, size, strict=False)]), low_cut, high_cut


def fit_catboost_for_leaf(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
    val_pred = np.asarray(model.predict(cat_ready(val, features)), dtype=float)
    test_pred = np.asarray(model.predict(cat_ready(test, features)), dtype=float)
    val_leaf = model.calc_leaf_indexes(cat_ready(val, features))
    test_leaf = model.calc_leaf_indexes(cat_ready(test, features))
    return val_pred, test_pred, val_leaf, test_leaf, np.asarray(model.predict(cat_ready(train, features)), dtype=float)


def leaf_segment(leaf_index: np.ndarray, n_trees: int = 16) -> np.ndarray:
    clipped = leaf_index[:, : min(n_trees, leaf_index.shape[1])]
    return np.array(["leaf_" + str(abs(hash(tuple(row.tolist()))) % 100000) for row in clipped])


def correction_map(actual_log: np.ndarray, pred_log: np.ndarray, segment: np.ndarray, min_rows: int = 30) -> pd.DataFrame:
    residual = actual_log - pred_log
    rows = []
    for seg in sorted(pd.Series(segment).dropna().astype(str).unique()):
        mask = segment.astype(str) == seg
        n = int(mask.sum())
        rows.append({
            "segment": seg,
            "n": n,
            "median_residual_log": float(np.median(residual[mask])) if n else float("nan"),
            "mean_residual_log": float(np.mean(residual[mask])) if n else float("nan"),
            "usable": bool(n >= min_rows),
        })
    return pd.DataFrame(rows)


def apply_map(pred_log: np.ndarray, segment: np.ndarray, cmap: pd.DataFrame, fallback: float = 0.0) -> np.ndarray:
    values = {str(row.segment): float(row.median_residual_log) for row in cmap.itertuples() if bool(row.usable)}
    correction = np.array([values.get(str(seg), fallback) for seg in segment], dtype=float)
    return pred_log + correction


def render(exp_id: str, info: dict[str, Any], metrics_df: pd.DataFrame, maps: dict[str, pd.DataFrame]) -> tuple[str, str]:
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "- 목적: 후속 PP-A/PP-J에서 사용할 수 있는 모델별 residual correction map을 생성한다.",
        "- 기준: correction map은 validation residual에서 산출하고 test에는 같은 map을 그대로 적용한다.",
        "- 해석: 보정 후 p95_APE가 줄고 MdAPE가 악화되지 않으면 해당 segment는 후속 보정 후보로 유지한다.",
        "",
        "## Validation 결과",
        "",
        "| 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.candidate}` | `{row.segment_rule}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    baseline = val[val["candidate"].eq("baseline")]
    if not baseline.empty:
        b = baseline.iloc[0]
        for row in val[val["candidate"].ne("baseline")].itertuples():
            lines.append(
                f"- `{row.segment_rule}` 보정: MdAPE delta `{row.MdAPE - b.MdAPE:.4f}`, "
                f"MAPE delta `{row.MAPE - b.MAPE:.4f}`, p95 delta `{row.p95_APE - b.p95_APE:.4f}`."
            )
    for name, df in maps.items():
        usable = int(df["usable"].sum()) if not df.empty else 0
        lines.append(f"- `{name}` correction map: usable segment `{usable}`개.")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Correction maps</h2>{''.join(f'<h3>{html.escape(k)}</h3>' + v.head(80).to_html(index=False, escape=True) for k, v in maps.items())}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, info: dict[str, Any], metrics_rows: list[dict[str, Any]], pred_df: pd.DataFrame, maps: dict[str, pd.DataFrame], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    pd.concat([df.assign(segment_rule=name) for name, df in maps.items()], ignore_index=True).to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "policy": "validation residual creates correction map; same map applied to test",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps({k: v.to_dict(orient="records") for k, v in maps.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, info, metrics_df, maps)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def pred_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "segment_rule": segment_rule,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def main() -> None:
    start = time.time()
    features_by_key = artifact_features()
    summary_rows = []
    for exp_id, info in EXPERIMENTS.items():
        features = features_by_key[info["feature_key"]]
        train, val, test = load_scope(info["scope"], features)
        train = normalize(train, features)
        val = normalize(val, features)
        test = normalize(test, features)
        if info["model"] == "catboost":
            val_pred, test_pred, val_leaf, test_leaf, _train_pred = fit_catboost_for_leaf(train, val, test, features)
        else:
            pred = fit_predict(info["model"], train, val, test, features)
            val_pred, test_pred = pred["validation"], pred["test"]
            val_leaf = test_leaf = np.empty((0, 0))

        metric_rows = []
        pred_frames = []
        maps: dict[str, pd.DataFrame] = {}
        for split_name, frame, pred_log in [("validation", val, val_pred), ("test", test, test_pred)]:
            pf = pred_frame(exp_id, "baseline", info["scope"], split_name, frame, pred_log, "none")
            pred_frames.append(pf)
            metric_rows.append({
                "experiment_id": exp_id,
                "candidate": "baseline",
                "segment_rule": "none",
                "scope": info["scope"],
                "split": split_name,
                **metrics(frame, pred_log),
            })

        pred_bin_val, pred_low, pred_high = pred_bins(val_pred)
        pred_bin_test, _l, _h = pred_bins(test_pred, pred_low, pred_high)
        tail_val, tail_low, tail_high = tail_segments(val, val_pred)
        tail_test, _tl, _th = tail_segments(test, test_pred, tail_low, tail_high)
        segment_values = {
            "overall": (np.array(["overall"] * len(val)), np.array(["overall"] * len(test))),
            "pred_bin": (pred_bin_val, pred_bin_test),
            "size_bucket": (val["size_bucket"].astype(str).to_numpy(), test["size_bucket"].astype(str).to_numpy()),
            "support_size_bucket": (
                val["support_size_bucket"].astype(str).to_numpy() if "support_size_bucket" in val.columns else np.array(["unknown"] * len(val)),
                test["support_size_bucket"].astype(str).to_numpy() if "support_size_bucket" in test.columns else np.array(["unknown"] * len(test)),
            ),
            "medium_shape_bucket": (
                val["medium_shape_bucket"].astype(str).to_numpy() if "medium_shape_bucket" in val.columns else np.array(["unknown"] * len(val)),
                test["medium_shape_bucket"].astype(str).to_numpy() if "medium_shape_bucket" in test.columns else np.array(["unknown"] * len(test)),
            ),
            "shape_bucket": (
                val["shape_bucket"].astype(str).to_numpy() if "shape_bucket" in val.columns else np.array(["unknown"] * len(val)),
                test["shape_bucket"].astype(str).to_numpy() if "shape_bucket" in test.columns else np.array(["unknown"] * len(test)),
            ),
            "tail_risk_segment": (tail_val, tail_test),
        }
        if info["model"] == "catboost":
            segment_values["leaf_segment"] = (leaf_segment(val_leaf), leaf_segment(test_leaf))

        for segment_rule in info["segments"]:
            val_seg, test_seg = segment_values[segment_rule]
            cmap = correction_map(val["ln_price_krw"].to_numpy(dtype=float), val_pred, val_seg)
            maps[segment_rule] = cmap
            fallback = float(cmap.loc[cmap["segment"].eq("overall"), "median_residual_log"].iloc[0]) if segment_rule == "overall" and not cmap.empty else 0.0
            val_corr = apply_map(val_pred, val_seg, cmap, fallback=fallback)
            test_corr = apply_map(test_pred, test_seg, cmap, fallback=fallback)
            for split_name, frame, corr_pred in [("validation", val, val_corr), ("test", test, test_corr)]:
                pf = pred_frame(exp_id, f"corrected_{segment_rule}", info["scope"], split_name, frame, corr_pred, segment_rule)
                pred_frames.append(pf)
                metric_rows.append({
                    "experiment_id": exp_id,
                    "candidate": f"corrected_{segment_rule}",
                    "segment_rule": segment_rule,
                    "scope": info["scope"],
                    "split": split_name,
                    **metrics(frame, corr_pred),
                })
        config = {
            "experiment_id": exp_id,
            "title": info["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {"baseline": features},
            "model_manifest": {
                "model": info["model"],
                "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
                "target": "ln_price_krw",
                "segments": info["segments"],
            },
        }
        write_exp(exp_id, info, metric_rows, pd.concat(pred_frames, ignore_index=True), maps, config)
        val_best = pd.DataFrame(metric_rows)
        best = val_best[val_best["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0].to_dict()
        best["folder"] = str((BASE_EXP_DIR / info["slug"]).relative_to(REPO))
        summary_rows.append(best)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(BASE_EXP_DIR / "PRE-CAL_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PRE-CAL_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
