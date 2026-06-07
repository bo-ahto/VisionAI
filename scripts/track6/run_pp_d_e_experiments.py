#!/usr/bin/env python3
"""Run Track6 PP-D model blend and PP-E conditional routing experiments."""
from __future__ import annotations

import html
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


EXPERIMENTS = {
    "PP-D1": {"slug": "PP-D1_simple_model_average", "title": "두 모델 단순 평균"},
    "PP-D2": {"slug": "PP-D2_weighted_model_average", "title": "두 모델 가중 평균"},
    "PP-D3": {"slug": "PP-D3_tail_defense_model_blend", "title": "큰 오차 방어용 모델 결합"},
    "PP-D4": {"slug": "PP-D4_warm_three_model_blend", "title": "Warm 모델 3종 예측값 결합"},
    "PP-D5": {"slug": "PP-D5_cold_three_model_blend", "title": "Cold 모델 3종 예측값 결합"},
    "PP-E1": {"slug": "PP-E1_warm_low_history_routing", "title": "Warm 저이력 작가 대체 적용"},
    "PP-E2": {"slug": "PP-E2_cold_meta_completeness_routing", "title": "Cold 메타 충분/부족 조건별 모델 선택"},
    "PP-E3": {"slug": "PP-E3_extreme_size_routing", "title": "극단 크기 조건별 모델 선택"},
    "PP-E4": {"slug": "PP-E4_material_classification_fallback_routing", "title": "NANT 분류 실패 조건별 모델 선택"},
    "PP-E5": {"slug": "PP-E5_pred_price_risk_routing", "title": "예측 가격대 위험 조건별 모델 선택"},
}

PAIR_WEIGHTS = [0.0, 0.25, 0.50, 0.75, 1.0]
THREE_WEIGHTS = [
    (a / 4, b / 4, (4 - a - b) / 4)
    for a in range(5)
    for b in range(5 - a)
]
MIN_SEGMENT_ROWS = 20


def pred_source(folder: str, candidate: str, label: str, scope: str, model_source: str | None = None) -> dict[str, Any]:
    return {"folder": folder, "candidate": candidate, "label": label, "scope": scope, "model_source": model_source}


SOURCES = {
    "warm_huber": pred_source("PP-B4_oof_base_residual_source", "baseline", "warm_huber", "warm", "warm_huber"),
    "warm_catboost": pred_source("PP-J3_warm_catboost_leaf_artist_size_calibration", "baseline", "warm_catboost", "warm"),
    "warm_tail_half": pred_source("PP-C5_correction_strength_tuning", "strength_0.50_corrected_pred_bin_size_tail_cap", "warm_tail_half", "warm", "warm_huber_ppj1_tail"),
    "warm_l8": pred_source("PP-L8_quantile_huber_catboost_sequential", "PP-L8_warm_quantile_features_huber_catboost_residual", "warm_l8", "warm"),
    "warm_l6": pred_source("PP-L6_huber_quantile_catboost_weighted_ensemble", "PP-L6_warm_validation_weighted_ensemble", "warm_l6", "warm"),
    "cold_catboost": pred_source("PP-B4_oof_base_residual_source", "baseline", "cold_catboost", "cold", "cold_catboost"),
    "cold_lightgbm": pred_source("PP-B4_oof_base_residual_source", "baseline", "cold_lightgbm", "cold", "cold_lightgbm"),
    "cold_j4": pred_source("PP-J4_cold_catboost_leaf_coverage_calibration", "corrected_leaf_segment_min_rows_20", "cold_j4", "cold"),
    "cold_j6": pred_source("PP-J6_cold_lightgbm_tail_calibration", "corrected_lgb_tail_support_size_cap_0.25", "cold_j6", "cold"),
    "cold_ppa7": pred_source("PP-A7_hierarchical_segment_residual_calibration", "corrected_hierarchical", "cold_ppa7", "cold"),
    "cold_l8": pred_source("PP-L8_quantile_huber_catboost_sequential", "PP-L8_cold_quantile_features_huber_catboost_residual", "cold_l8", "cold"),
    "cold_q50": pred_source("PP-L6_huber_quantile_catboost_weighted_ensemble", "B2_cold_Quantile_q50", "cold_q50", "cold"),
}


def load_prediction(source_key: str) -> dict[str, pd.DataFrame]:
    src = SOURCES[source_key]
    df = pd.read_csv(BASE_EXP_DIR / src["folder"] / "outputs" / "predictions.csv")
    mask = df["candidate"].astype(str).eq(src["candidate"]) & df["scope"].astype(str).eq(src["scope"])
    if src.get("model_source") and "model_source" in df.columns:
        mask &= df["model_source"].astype(str).eq(src["model_source"])
    out: dict[str, pd.DataFrame] = {}
    for split in ["validation", "test"]:
        part = df[mask & df["split"].astype(str).eq(split)].copy()
        if part.empty:
            raise ValueError(f"missing prediction source={source_key} split={split}")
        out[split] = part.drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    return out


def merge_predictions(source_keys: list[str], split: str) -> pd.DataFrame:
    frames = []
    for key in source_keys:
        df = load_prediction(key)[split]
        frames.append(df[["_track6_row_id", "actual_log", "actual_price", "pred_log"]].rename(columns={"pred_log": key}))
    merged = frames[0]
    for key, frame in zip(source_keys[1:], frames[1:], strict=True):
        merged = merged.merge(frame[["_track6_row_id", key]], on="_track6_row_id", how="inner")
    return merged


def frame_from_merged(merged: pd.DataFrame) -> pd.DataFrame:
    return merged[["_track6_row_id", "actual_log", "actual_price"]].rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}).copy()


def pred_frame(exp_id: str, candidate: str, scope: str, split: str, merged: pd.DataFrame, pred_log: np.ndarray, policy: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
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
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, merged: pd.DataFrame, pred_log: np.ndarray, policy: str, notes: str = "") -> None:
    rows.append({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame_from_merged(merged), pred_log),
    })


def score(merged: pd.DataFrame, pred_log: np.ndarray, objective: str = "MdAPE") -> float:
    m = metrics(frame_from_merged(merged), pred_log)
    return float(m[objective])


def best_pair_weight(merged: pd.DataFrame, left: str, right: str, objective: str = "MdAPE") -> tuple[float, np.ndarray, float]:
    best = (999.0, 0.5, np.array([], dtype=float))
    for w in PAIR_WEIGHTS:
        pred = w * merged[left].to_numpy(dtype=float) + (1.0 - w) * merged[right].to_numpy(dtype=float)
        value = score(merged, pred, objective)
        if value < best[0]:
            best = (value, w, pred)
    return best[1], best[2], best[0]


def best_three_weight(merged: pd.DataFrame, cols: list[str], objective: str = "MdAPE") -> tuple[tuple[float, float, float], np.ndarray, float]:
    best = (999.0, (1 / 3, 1 / 3, 1 / 3), np.array([], dtype=float))
    arrs = [merged[col].to_numpy(dtype=float) for col in cols]
    for weights in THREE_WEIGHTS:
        pred = weights[0] * arrs[0] + weights[1] * arrs[1] + weights[2] * arrs[2]
        value = score(merged, pred, objective)
        if value < best[0]:
            best = (value, weights, pred)
    return best[1], best[2], best[0]


def conditions(scope: str) -> dict[str, pd.DataFrame]:
    features_by_key = artifact_features()
    if scope == "warm":
        features = list(dict.fromkeys(features_by_key["warm"] + ["artist_works_log", "artist_works_count_train", "medium_support_bucket", "collected_material_raw", "nant_support", "nant_tool", "nant_material_note", "nant_material_match_method"]))
    else:
        features = list(dict.fromkeys(features_by_key["cold_catboost"] + features_by_key["cold_lightgbm"] + ["medium_support_bucket", "collected_material_raw", "nant_support", "nant_tool", "nant_material_note", "nant_material_match_method"]))
    train, val, test = load_scope(scope, features)
    train = normalize(train, [c for c in features if c in train.columns])
    val = normalize(val, [c for c in features if c in val.columns])
    test = normalize(test, [c for c in features if c in test.columns])
    return {"train": train, "validation": val, "test": test}


def add_condition_columns(scope: str, split: str, merged: pd.DataFrame, base_pred_col: str) -> pd.DataFrame:
    cond = conditions(scope)[split].copy()
    out = merged.merge(cond, on="_track6_row_id", how="left", suffixes=("", "__feature"))
    pred = out[base_pred_col].to_numpy(dtype=float)
    q33, q66 = np.quantile(pred, [0.33, 0.66])
    out["pred_risk_bin"] = np.select([pred <= q33, pred <= q66], ["pred_low", "pred_mid"], default="pred_high")
    area = pd.to_numeric(out["log_area"], errors="coerce")
    a10, a90 = np.nanquantile(area, [0.10, 0.90])
    out["extreme_size_bin"] = np.select([area <= a10, area >= a90], ["small_extreme", "large_extreme"], default="normal_size")
    if "artist_works_log" in out.columns:
        works = pd.to_numeric(out["artist_works_log"], errors="coerce")
        w33, w66 = np.nanquantile(works.fillna(0), [0.33, 0.66])
        out["artist_history_bin"] = np.select([works <= w33, works <= w66], ["low_history", "mid_history"], default="high_history")
    else:
        out["artist_history_bin"] = "not_applicable"
    material_cols = [c for c in ["medium_category", "support_category", "collected_material_raw", "nant_support", "nant_tool", "nant_material_note", "nant_material_match_method"] if c in out.columns]
    missing_count = np.zeros(len(out), dtype=int)
    for col in material_cols:
        s = out[col].astype("string").fillna("")
        missing_count += s.str.lower().isin(["", "nan", "none", "__missing__", "unknown", "미상"]).to_numpy(dtype=int)
    out["meta_missing_count"] = missing_count
    out["meta_bin"] = np.select([missing_count >= 3, missing_count >= 1], ["meta_poor", "meta_partial"], default="meta_ok")
    out["material_quality_bin"] = np.where(missing_count >= 2, "material_unclear", "material_ok")
    return out


def run_blend(exp_id: str, rows: list[dict[str, Any]], preds: list[pd.DataFrame], policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    corr: list[dict[str, Any]] = []
    for policy in policies:
        sources = policy["sources"]
        scope = policy["scope"]
        val = merge_predictions(sources, "validation")
        test = merge_predictions(sources, "test")
        baseline_key = policy["baseline"]
        for split, merged in [("validation", val), ("test", test)]:
            add_metric(rows, exp_id, f"baseline_{baseline_key}", scope, split, merged, merged[baseline_key].to_numpy(dtype=float), "baseline")
            preds.append(pred_frame(exp_id, f"baseline_{baseline_key}", scope, split, merged, merged[baseline_key].to_numpy(dtype=float), "baseline"))
        if policy["mode"] == "simple_pair":
            pred_val = np.mean([val[s].to_numpy(dtype=float) for s in sources], axis=0)
            pred_test = np.mean([test[s].to_numpy(dtype=float) for s in sources], axis=0)
            candidate = policy["candidate"]
            selected: dict[str, Any] = {"mode": "simple_average", "sources": sources}
        elif policy["mode"] == "weighted_pair":
            w, pred_val, value = best_pair_weight(val, sources[0], sources[1], policy.get("objective", "MdAPE"))
            pred_test = w * test[sources[0]].to_numpy(dtype=float) + (1.0 - w) * test[sources[1]].to_numpy(dtype=float)
            candidate = f"{policy['candidate']}_w_{w:.2f}_{sources[0]}"
            selected = {"mode": "weighted_pair", "sources": sources, "weight_on_first": w, "validation_objective": policy.get("objective", "MdAPE"), "validation_score": value}
        else:
            weights, pred_val, value = best_three_weight(val, sources, policy.get("objective", "MdAPE"))
            pred_test = sum(w * test[s].to_numpy(dtype=float) for w, s in zip(weights, sources, strict=True))
            candidate = f"{policy['candidate']}_w_{weights[0]:.2f}_{weights[1]:.2f}_{weights[2]:.2f}"
            selected = {"mode": "weighted_three", "sources": sources, "weights": dict(zip(sources, weights, strict=True)), "validation_objective": policy.get("objective", "MdAPE"), "validation_score": value}
        for split, merged, pred in [("validation", val, pred_val), ("test", test, pred_test)]:
            add_metric(rows, exp_id, candidate, scope, split, merged, pred, policy["mode"], json.dumps(selected, ensure_ascii=False))
            preds.append(pred_frame(exp_id, candidate, scope, split, merged, pred, policy["mode"]))
        corr.append({"experiment_id": exp_id, "candidate": candidate, "scope": scope, **selected})
    return corr


def choose_by_segment(val: pd.DataFrame, candidates: list[str], segment_col: str) -> pd.DataFrame:
    rows = []
    for segment, part in val.groupby(segment_col):
        if len(part) < MIN_SEGMENT_ROWS:
            best = candidates[0]
            reason = "fallback_min_rows"
        else:
            scores = []
            frame = frame_from_merged(part)
            for cand in candidates:
                m = metrics(frame, part[cand].to_numpy(dtype=float))
                scores.append((cand, m["MdAPE"], m["MAPE"], m["p95_APE"], len(part)))
            best = sorted(scores, key=lambda x: (x[1], x[2], x[3]))[0][0]
            reason = "validation_best"
        rows.append({"segment": str(segment), "selected_candidate": best, "n_validation": int(len(part)), "reason": reason})
    return pd.DataFrame(rows)


def apply_route(frame: pd.DataFrame, route: pd.DataFrame, segment_col: str, fallback: str) -> np.ndarray:
    mapping = {str(r.segment): str(r.selected_candidate) for r in route.itertuples()}
    pred = []
    for row in frame.itertuples(index=False):
        segment = str(getattr(row, segment_col))
        selected = mapping.get(segment, fallback)
        pred.append(float(getattr(row, selected)))
    return np.array(pred, dtype=float)


def run_route(exp_id: str, scope: str, sources: list[str], segment_col: str, base_pred_col: str, baseline: str) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    corr: list[dict[str, Any]] = []
    val = add_condition_columns(scope, "validation", merge_predictions(sources, "validation"), base_pred_col)
    test = add_condition_columns(scope, "test", merge_predictions(sources, "test"), base_pred_col)
    for split, merged in [("validation", val), ("test", test)]:
        add_metric(rows, exp_id, f"baseline_{baseline}", scope, split, merged, merged[baseline].to_numpy(dtype=float), "baseline")
        preds.append(pred_frame(exp_id, f"baseline_{baseline}", scope, split, merged, merged[baseline].to_numpy(dtype=float), "baseline"))
    route = choose_by_segment(val, sources, segment_col)
    val_pred = apply_route(val, route, segment_col, baseline)
    test_pred = apply_route(test, route, segment_col, baseline)
    for split, merged, pred in [("validation", val, val_pred), ("test", test, test_pred)]:
        add_metric(rows, exp_id, f"routed_by_{segment_col}", scope, split, merged, pred, segment_col)
        preds.append(pred_frame(exp_id, f"routed_by_{segment_col}", scope, split, merged, pred, segment_col))
    for r in route.to_dict("records"):
        corr.append({"experiment_id": exp_id, "scope": scope, "segment_col": segment_col, **r})
    return rows, preds, corr


def render(exp_id: str, metrics_df: pd.DataFrame, corr_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 단일 후보보다 예측값 결합 또는 조건별 선택이 안정적인지 확인한다.",
        "- 기준: 결합 가중치와 선택 규칙은 validation에서만 확정하고 test에는 그대로 적용한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.scope}` | `{row.candidate}` | `{row.policy}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    for scope in sorted(val["scope"].unique()):
        scoped = val[val["scope"].eq(scope)]
        baseline = scoped[scoped["candidate"].str.startswith("baseline")]
        if baseline.empty:
            continue
        b = baseline.iloc[0]
        best = scoped.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]
        lines.append(
            f"- `{scope}` best `{best.candidate}`: baseline 대비 MdAPE `{best.MdAPE - b.MdAPE:.4f}`, "
            f"MAPE `{best.MAPE - b.MAPE:.4f}`, p95 `{best.p95_APE - b.p95_APE:.4f}`."
        )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Policy Map</h2>{corr_df.to_html(index=False, escape=True) if not corr_df.empty else '<p>No policy map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, metrics_rows: list[dict[str, Any]], pred_rows: list[pd.DataFrame], corr_rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(pred_rows, ignore_index=True)
    corr_df = pd.DataFrame(corr_rows)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    corr_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "policy": "validation selected blend/routing policy applied to test",
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
    summary_rows: list[dict[str, Any]] = []
    model_manifest = {
        "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
        "prediction_sources": SOURCES,
        "target": "ln_price_krw",
        "selection_policy": "validation_only",
        "seed": SEED,
    }
    configs = {"feature_columns": {"prediction_sources": SOURCES}, "model_manifest": model_manifest}

    blend_policies = {
        "PP-D1": [
            {"scope": "warm", "sources": ["warm_huber", "warm_catboost"], "baseline": "warm_huber", "mode": "simple_pair", "candidate": "simple_avg_warm_huber_catboost"},
            {"scope": "cold", "sources": ["cold_catboost", "cold_lightgbm"], "baseline": "cold_lightgbm", "mode": "simple_pair", "candidate": "simple_avg_cold_catboost_lightgbm"},
        ],
        "PP-D2": [
            {"scope": "warm", "sources": ["warm_huber", "warm_catboost"], "baseline": "warm_huber", "mode": "weighted_pair", "candidate": "weighted_warm_huber_catboost"},
            {"scope": "cold", "sources": ["cold_catboost", "cold_lightgbm"], "baseline": "cold_lightgbm", "mode": "weighted_pair", "candidate": "weighted_cold_catboost_lightgbm"},
        ],
        "PP-D3": [
            {"scope": "cold", "sources": ["cold_catboost", "cold_lightgbm"], "baseline": "cold_lightgbm", "mode": "weighted_pair", "candidate": "tail_weighted_raw_cold_pair", "objective": "p95_APE"},
            {"scope": "cold", "sources": ["cold_j4", "cold_j6"], "baseline": "cold_j4", "mode": "weighted_pair", "candidate": "tail_weighted_corrected_cold_pair", "objective": "p95_APE"},
        ],
        "PP-D4": [
            {"scope": "warm", "sources": ["warm_huber", "warm_catboost", "warm_l8"], "baseline": "warm_huber", "mode": "weighted_three", "candidate": "weighted_warm_huber_catboost_l8"},
            {"scope": "warm", "sources": ["warm_huber", "warm_l6", "warm_l8"], "baseline": "warm_huber", "mode": "weighted_three", "candidate": "weighted_warm_huber_l6_l8"},
        ],
        "PP-D5": [
            {"scope": "cold", "sources": ["cold_catboost", "cold_lightgbm", "cold_q50"], "baseline": "cold_lightgbm", "mode": "weighted_three", "candidate": "weighted_cold_raw_q50"},
            {"scope": "cold", "sources": ["cold_j4", "cold_j6", "cold_l8"], "baseline": "cold_j4", "mode": "weighted_three", "candidate": "weighted_cold_corrected_l8"},
        ],
    }

    for exp_id, policies in blend_policies.items():
        rows: list[dict[str, Any]] = []
        preds: list[pd.DataFrame] = []
        corr = run_blend(exp_id, rows, preds, policies)
        write_exp(exp_id, rows, preds, corr, {"experiment_id": exp_id, "title": EXPERIMENTS[exp_id]["title"], "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"), **configs})
        df = pd.DataFrame(rows)
        summary_rows.extend(df.query("split == 'validation'").sort_values(["scope", "MdAPE", "MAPE"]).groupby("scope", as_index=False).head(1).to_dict("records"))

    route_specs = {
        "PP-E1": ("warm", ["warm_huber", "warm_tail_half", "warm_catboost", "warm_l8"], "artist_history_bin", "warm_huber", "warm_huber"),
        "PP-E2": ("cold", ["cold_catboost", "cold_lightgbm", "cold_j4", "cold_j6", "cold_l8"], "meta_bin", "cold_lightgbm", "cold_lightgbm"),
        "PP-E3": ("cold", ["cold_catboost", "cold_lightgbm", "cold_j4", "cold_j6", "cold_ppa7", "cold_l8"], "extreme_size_bin", "cold_lightgbm", "cold_lightgbm"),
        "PP-E4": ("cold", ["cold_catboost", "cold_lightgbm", "cold_j4", "cold_j6", "cold_ppa7"], "material_quality_bin", "cold_lightgbm", "cold_lightgbm"),
        "PP-E5": ("cold", ["cold_catboost", "cold_lightgbm", "cold_j4", "cold_j6", "cold_ppa7", "cold_l8"], "pred_risk_bin", "cold_lightgbm", "cold_lightgbm"),
    }
    for exp_id, (scope, sources, segment_col, base_pred_col, baseline) in route_specs.items():
        rows, preds, corr = run_route(exp_id, scope, sources, segment_col, base_pred_col, baseline)
        write_exp(exp_id, rows, preds, corr, {"experiment_id": exp_id, "title": EXPERIMENTS[exp_id]["title"], "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"), **configs})
        df = pd.DataFrame(rows)
        summary_rows.extend(df.query("split == 'validation'").sort_values(["scope", "MdAPE", "MAPE"]).groupby("scope", as_index=False).head(1).to_dict("records"))

    summary = pd.DataFrame(summary_rows)
    summary["folder"] = summary["experiment_id"].map({k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()})
    summary.to_csv(BASE_EXP_DIR / "PP-D_E_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-D_E_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
