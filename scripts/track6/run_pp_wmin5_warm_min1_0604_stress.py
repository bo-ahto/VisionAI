#!/usr/bin/env python3
"""Run PP-WMIN5: 0604 stress safety check for the selected WMIN4 Warm candidate.

This is a stress/safety experiment only.  The 0604 labels are never used to
select a new threshold or tune a candidate.  The script compares the already
selected WMIN4 candidate, ``min1_huber_refit_partial``, against the current
PP258-compatible report-layer proxy on the 0604 new-label set.
"""
from __future__ import annotations

import html
import importlib.util
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as hcoef1  # noqa: E402
import run_pp_wmin2_warm_artist_min1_svc_numeric as wmin2  # noqa: E402
import run_pp_wmin3_warm_min1_hcoef_refit as wmin3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-WMIN5"
EXP_SLUG = "PP-WMIN5_warm_min1_0604_stress"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
TITLE = "Warm WMIN4 min1 채택 후보 0604 stress 안전성 확인"

OPS_LABELS = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "operational"
    / "outputs"
    / "0604_evaluation"
    / "operational_predictions_with_actual.csv"
)
OPS_WARM_FEATURES = (
    REPO
    / "models"
    / "track6"
    / "price_prediction_v0.1"
    / "data"
    / "evaluation"
    / "test_new_artworks_test_noprice_0604_features"
    / "warm_features_v0_1.csv"
)
PP258_SCRIPT = (
    REPO
    / "experiments"
    / "track6"
    / "SUB-WARM-PP258_operational_fixed_test_submission"
    / "scripts"
    / "pp258_reproduce_fixed_test.py"
)
WARM_REFREEZE_DIR = REPO / "models" / "track6" / "warm_pp252_upstream_refreeze_candidate" / "artifacts"

PP258_PROXY = "pp258_report_layer_proxy"
WMIN4_SELECTED = "wmin4_min1_huber_refit_partial"
WMIN4_BASIS = "wmin4_min1_70_30_basis"
MIN1_SVC = "wmin5_min1_svc_numeric_seed_mean"
CURRENT_70_30 = "current_v01_70_30"
CURRENT_PPV8 = "current_ppv8_service_primary"
STRESS_P95_TOL = 0.010
STRESS_MAPE_TOL = 0.005


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_exp(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.exp(np.clip(np.asarray(values, dtype=float), math.log(1_000.0), math.log(1_000_000_000_000.0)))


def metric(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    pred = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(frame["actual_log"].to_numpy(dtype=float)) & np.isfinite(pred)
    actual_price = frame.loc[valid, "actual_price"].to_numpy(dtype=float)
    actual_log = frame.loc[valid, "actual_log"].to_numpy(dtype=float)
    pred = pred[valid]
    pred_price = safe_exp(pred)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred - actual_log) ** 2))),
        "Within_30": float(np.nanmean(ape <= 0.30)),
        "Within_50": float(np.nanmean(ape <= 0.50)),
    }


def norm_str(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def load_0604_base() -> pd.DataFrame:
    ops = pd.read_csv(OPS_LABELS, low_memory=False)
    ops = ops[ops["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(ops.get("actual_price_usd_equiv"), errors="coerce")
    ops = ops[~(usd < 50.0)].copy().reset_index(drop=True)
    if OPS_WARM_FEATURES.exists():
        warm_features = pd.read_csv(OPS_WARM_FEATURES, low_memory=False)
        warm_features = warm_features.drop_duplicates("_v01_row_id")
        ops = ops.merge(warm_features, on="_v01_row_id", how="left", suffixes=("", "_warm_feature"))
        for warm_col in [col for col in ops.columns if col.endswith("_warm_feature")]:
            col = warm_col.removesuffix("_warm_feature")
            ops[col] = ops[col].fillna(ops[warm_col]) if col in ops.columns else ops[warm_col]
            ops = ops.drop(columns=[warm_col])
        for col in warm_features.columns:
            if col == "_v01_row_id" or col in ops.columns:
                continue
            warm_col = f"{col}_warm_feature"
            if warm_col in ops.columns:
                ops[col] = ops[col].fillna(ops[warm_col]) if col in ops.columns else ops[warm_col]
                ops = ops.drop(columns=[warm_col])
    ops["price_krw"] = pd.to_numeric(ops["actual_price_krw"], errors="coerce")
    ops["ln_price_krw"] = np.log(np.clip(ops["price_krw"].to_numpy(dtype=float), 1.0, None))
    if "artist_name_ko" not in ops.columns:
        ops["artist_name_ko"] = ops.get("artist_name", "")
    if "artist_works_count_train" not in ops.columns:
        ops["artist_works_count_train"] = np.nan
    # Recompute comparable stats from train.  Drop shipped svc_* columns to avoid
    # accidental reuse of the min5 operational stats.
    drop_cols = [col for col in ops.columns if col.startswith("svc_")]
    return ops.drop(columns=drop_cols).reset_index(drop=True)


def compute_min1_svc_0604() -> tuple[pd.DataFrame, pd.DataFrame]:
    base_features = artifact_features()["warm"]
    requested = list(dict.fromkeys([*base_features, *wmin2.svc1.GROUPING_FEATURES]))
    train_base, val_base, _test_base = load_scope("warm", requested)
    ops_base = load_0604_base()
    group_defs = wmin2.group_defs_for_artist_min(wmin2.ARTIST_MIN_N_CANDIDATE)
    svc_features = list(dict.fromkeys([*base_features, *wmin2.svc1.SVC_NUMERIC]))

    pred_columns: list[pd.Series] = []
    seed0_frame: pd.DataFrame | None = None
    coverage_rows: list[pd.DataFrame] = []
    for seed in wmin2.SEEDS:
        train_s, _val_s, ops_s, _audit = wmin2.add_service_features_seed(train_base, val_base, ops_base, seed, group_defs)
        if seed == wmin2.SEEDS[0]:
            seed0_frame = ops_s.copy()
        train_n = wmin2.svc1.normalize(train_s, svc_features)
        ops_n = wmin2.svc1.normalize(ops_s, svc_features)
        model = wmin2.svc1.huber_model(svc_features)
        y_train = pd.to_numeric(train_n["ln_price_krw"], errors="coerce").to_numpy(dtype=float)
        model.fit(train_n[svc_features], y_train)
        pred = pd.Series(np.asarray(model.predict(ops_n[svc_features]), dtype=float), name=f"seed_{seed}")
        pred_columns.append(pred)
        cov = ops_s[["_track6_row_id", "svc_group_level", "svc_coverage_tier", "svc_group_n"]].copy()
        cov["seed"] = seed
        coverage_rows.append(cov)

    if seed0_frame is None:
        raise RuntimeError("min1 SVC seed0 frame missing")
    seed_preds = pd.concat(pred_columns, axis=1)
    out = seed0_frame.copy()
    out[MIN1_SVC] = seed_preds.mean(axis=1).to_numpy(dtype=float)
    out["min1_seed_pred_std"] = seed_preds.std(axis=1).to_numpy(dtype=float)
    return out, pd.concat(coverage_rows, ignore_index=True)


def _rank_like(value: float, scale: float) -> float:
    if not math.isfinite(value) or scale <= 0:
        return 0.0
    return float(np.clip(value / scale, 0.0, 1.0))


def _price_band_from_log(log_price: float) -> str:
    if log_price < math.log(5_000_000):
        return "low_price"
    if log_price < math.log(20_000_000):
        return "mid_price"
    if log_price < math.log(80_000_000):
        return "high_price"
    return "very_high_price"


def _qwidth_band(width: float) -> str:
    if width < 0.60:
        return "qwidth_low"
    if width < 1.10:
        return "qwidth_mid"
    if width < 1.75:
        return "qwidth_high"
    return "qwidth_extreme"


def _svc_group_n_band(value: float) -> str:
    if value >= 50:
        return "n_50_plus"
    if value >= 20:
        return "n_20_49"
    if value >= 10:
        return "n_10_19"
    if value >= 5:
        return "n_5_9"
    return "n_1_4"


def _area_bin(area_cm2: float) -> str:
    if area_cm2 < 1_200:
        return "0"
    if area_cm2 < 7_000:
        return "2"
    return "3"


def prediction_probability(model: Any, features: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["clf"].classes_)
    proba = model.predict_proba(features)
    pos_idx = classes.index(1) if 1 in classes else None
    if pos_idx is None:
        return np.full(len(features), 0.5, dtype=float)
    return np.nan_to_num(proba[:, pos_idx], nan=0.5, posinf=0.5, neginf=0.5)


def warm_refreeze_features(row: pd.Series, source_log: float, stability_log: float, component_values: list[float], columns: list[str]) -> dict[str, Any]:
    qwidth = float(row.get("l10_quantile_width") or 0.0)
    price_range = float(row.get("l10_price_range_ratio") or 0.0)
    svc_n = float(row.get("svc_group_n") or 0.0)
    spread = float(max(component_values) - min(component_values))
    gap = abs(stability_log - source_log)
    area = float(row.get("area_cm2") or 0.0)
    confidence = str(row.get("service_confidence_tier") or "low")
    if not confidence.endswith("_confidence"):
        confidence = f"{confidence}_confidence"
    risk = np.clip(
        0.25 * _rank_like(qwidth, 2.0)
        + 0.20 * _rank_like(math.log(max(price_range, 1.0)), 2.5)
        + 0.20 * _rank_like(spread, 1.2)
        + 0.18 * _rank_like(gap, 0.8)
        + 0.09 * (1.0 if "low" in confidence else 0.0)
        + 0.08 * np.clip((10.0 - svc_n) / 10.0, 0.0, 1.0),
        0.0,
        1.0,
    )
    feature = {
        "stable_price_band": _price_band_from_log(source_log),
        "confidence_tier": confidence,
        "qwidth_band": _qwidth_band(qwidth),
        "medium_support_bucket": str(row.get("medium_support_bucket") or "__MISSING__"),
        "svc_group_n_band": _svc_group_n_band(svc_n),
        "area_bin": _area_bin(area),
        "quantile_width": qwidth,
        "l10_price_range_ratio": price_range,
        "svc_group_n": svc_n,
        "component_prediction_spread": spread,
        "current_vs_stable_gap_abs": gap,
        "gap_operational_abs": gap,
        "gap_mape_abs": gap,
        "gap_guarded_abs": gap,
        "gap_recovery_abs": gap,
        "row_risk_operational": risk,
        "row_risk_mape": risk,
        "row_risk_guarded": risk,
        "row_risk_recovery": risk,
        "pp246_minus_pp234_abs": gap,
        "p95_recovery_delta_abs": gap,
        "operational_delta_abs": gap,
        "p95_guarded_delta_abs": gap,
        "p95_extreme_delta_abs": gap,
        "pp246_log_centered": source_log - math.log(10_000_000),
        "qwidth_rank": _rank_like(qwidth, 2.0),
        "component_spread_rank": _rank_like(spread, 1.2),
        "model_gap_rank": _rank_like(gap, 0.8),
    }
    return {col: feature.get(col, 0.0) for col in columns}


def build_pp258_proxy_0604(ops: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pp258 = load_module(PP258_SCRIPT, "pp_wmin5_pp258_reproduce")
    schema = json.loads((WARM_REFREEZE_DIR / "feature_schema.json").read_text(encoding="utf-8"))
    feature_columns = schema.get("feature_columns") or []
    direction_model = joblib.load(WARM_REFREEZE_DIR / "direction_hist_gbc_35_seed17_fullfit.joblib")
    huber_residual_model = joblib.load(WARM_REFREEZE_DIR / "huber_residual_epsilon1p15_fullfit.joblib")

    feature_rows: list[dict[str, Any]] = []
    input_rows: list[dict[str, Any]] = []
    for _, row in ops.iterrows():
        source_log = float(row["v01_operational_pred_log"])
        stability_log = float(row["pp_v8_compact_blend_mape_guarded_pred_log"])
        component_values = [
            float(row["svc_numeric_seed_mean_pred_log"]),
            float(row["l10_generated_bucket_seq_pred_log"]),
            float(row["pp_v2_defensive_pred_log"]),
            float(row["pp_v8_compact_blend_mape_guarded_pred_log"]),
            source_log,
        ]
        feature_rows.append(warm_refreeze_features(row, source_log, stability_log, component_values, feature_columns))
    features = pd.DataFrame(feature_rows)
    prob = prediction_probability(direction_model, features)
    residual_raw = np.asarray(huber_residual_model.predict(features), dtype=float)
    residual = np.clip(residual_raw, -0.8, 0.8)
    for idx, (_, row) in enumerate(ops.iterrows()):
        component_values = [
            float(row["svc_numeric_seed_mean_pred_log"]),
            float(row["l10_generated_bucket_seq_pred_log"]),
            float(row["pp_v2_defensive_pred_log"]),
            float(row["pp_v8_compact_blend_mape_guarded_pred_log"]),
            float(row["v01_operational_pred_log"]),
        ]
        input_rows.append({
            "eval_split": "0604_stress",
            "_track6_row_id": row["_track6_row_id"],
            "artist_key": row["artist_key"],
            "artist_name_ko": row.get("artist_name", ""),
            "actual_log": row["actual_log"],
            "actual_price": row["actual_price"],
            "pp252_log": row["v01_operational_pred_log"],
            "pp252_stability_log": row["pp_v8_compact_blend_mape_guarded_pred_log"],
            "prob_hist35_pp252": prob[idx],
            "resid_huber_pp252": residual[idx],
            "resid_huber_raw_pp252": residual_raw[idx],
            "quantile_width": row["l10_quantile_width"],
            "l10_price_range_ratio": row["l10_price_range_ratio"],
            "component_prediction_spread": max(component_values) - min(component_values),
            "confidence_tier": row.get("service_confidence_tier", "low"),
            "svc_group_n": row.get("svc_group_n", 0.0),
            "svc_group_level": row.get("svc_group_level", ""),
            "svc_coverage_tier": row.get("svc_coverage_tier", ""),
            "stable_price_band": _price_band_from_log(float(row["v01_operational_pred_log"])),
        })
    pp258_input = pd.DataFrame(input_rows)
    predictions = pp258.calculate_pp258_predictions(pp258_input)
    return pp258_input, predictions


def build_wmin4_0604_frame(ops_min1: pd.DataFrame) -> pd.DataFrame:
    shrunk_pred, raw_prior, shrunk_prior, _size_edges = hcoef1.train_shrunk_huber_refit()
    base = hcoef1.build_0604_frame(shrunk_pred, raw_prior, shrunk_prior)
    min1_cols = [
        "_track6_row_id",
        MIN1_SVC,
        "min1_seed_pred_std",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "svc_group_log_price_iqr",
    ]
    m = base.merge(
        ops_min1[[col for col in min1_cols if col in ops_min1.columns]].rename(
            columns={
                "svc_group_level": "svc_group_level_min1",
                "svc_coverage_tier": "svc_coverage_tier_min1",
                "svc_group_n": "svc_group_n_min1",
                "svc_group_log_price_iqr": "svc_group_log_price_iqr_min1",
            }
        ),
        on="_track6_row_id",
        how="left",
    )
    if m[MIN1_SVC].isna().any():
        raise ValueError(f"Missing min1 SVC on 0604 rows: {int(m[MIN1_SVC].isna().sum())}")
    m["old_current_70_30"] = m["current_70_30"]
    m["old_svc_fallback"] = m["svc_fallback"]
    m["current_70_30"] = 0.70 * pd.to_numeric(m[MIN1_SVC], errors="coerce") + 0.30 * pd.to_numeric(m["ppv8_defensive"], errors="coerce")
    m["svc_fallback"] = pd.to_numeric(m[MIN1_SVC], errors="coerce")
    m["svc_group_level"] = m["svc_group_level_min1"].astype(str)
    m["svc_coverage_tier"] = m["svc_coverage_tier_min1"].astype(str)
    m["svc_group_n"] = pd.to_numeric(m["svc_group_n_min1"], errors="coerce")
    m["svc_group_n_log"] = np.log1p(m["svc_group_n"].fillna(0.0))
    if "svc_group_log_price_iqr_min1" in m.columns:
        m["svc_group_log_price_iqr"] = pd.to_numeric(m["svc_group_log_price_iqr_min1"], errors="coerce")
    refreshed = hcoef1.add_derived_features(m, "0604_stress")
    refreshed[WMIN4_BASIS] = refreshed["current_70_30"]
    refreshed[MIN1_SVC] = m[MIN1_SVC]
    refreshed["min1_seed_pred_std"] = m["min1_seed_pred_std"]
    return refreshed


def prediction_frame(frame: pd.DataFrame, candidate: str, pred_log: np.ndarray | pd.Series, source: str) -> pd.DataFrame:
    pred = np.asarray(pred_log, dtype=float)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_price = safe_exp(pred)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "source": source,
        "eval_split": "0604_stress",
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame["artist_key"].astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": actual_log,
        "actual_price": actual_price,
        "pred_log": pred,
        "pred_price": pred_price,
        "absolute_percentage_error": ape,
        "log_error": actual_log - pred,
        "svc_group_level": frame.get("svc_group_level", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_coverage_tier": frame.get("svc_coverage_tier", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_group_n": pd.to_numeric(frame.get("svc_group_n", pd.Series([np.nan] * len(frame))), errors="coerce").to_numpy(dtype=float),
        "quantile_width": pd.to_numeric(frame.get("l10_quantile_width", frame.get("quantile_width", pd.Series([np.nan] * len(frame)))), errors="coerce").to_numpy(dtype=float),
    })
    out["svc_group_n_bin"] = pd.cut(
        pd.to_numeric(out["svc_group_n"], errors="coerce").fillna(0),
        bins=[-0.1, 0.9, 4.9, 9.9, 19.9, 49.9, np.inf],
        labels=["0", "1_4", "5_9", "10_19", "20_49", "50_plus"],
    ).astype(str)
    return out


def metrics_by_group(predictions: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    rows: list[dict[str, Any]] = []
    grouped = predictions.groupby(["candidate", *group_cols], dropna=False)
    for key, group in grouped:
        if not isinstance(key, tuple):
            key = (key,)
        row = {"candidate": key[0]}
        for col, value in zip(group_cols, key[1:]):
            row[col] = value
        m = metric(group.rename(columns={"actual_price": "actual_price", "actual_log": "actual_log"}), group["pred_log"].to_numpy(dtype=float))
        rows.append({**row, **m})
    return pd.DataFrame(rows)


def compare_against(predictions: pd.DataFrame, baseline: str, candidate: str, group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or []
    metrics = metrics_by_group(predictions[predictions["candidate"].isin([baseline, candidate])].copy(), group_cols)
    base = metrics[metrics["candidate"].eq(baseline)].copy()
    cand = metrics[metrics["candidate"].eq(candidate)].copy()
    if group_cols:
        merged = cand.merge(base, on=group_cols, suffixes=("_candidate", "_baseline"), how="left")
    else:
        merged = pd.concat(
            [
                cand.reset_index(drop=True).add_suffix("_candidate"),
                base.reset_index(drop=True).add_suffix("_baseline"),
            ],
            axis=1,
        )
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        merged[f"delta_{col}_candidate_minus_baseline"] = merged[f"{col}_candidate"] - merged[f"{col}_baseline"]
    return merged.sort_values([f"delta_p95_APE_candidate_minus_baseline", f"delta_MAPE_candidate_minus_baseline"], ascending=False)


def markdown_table(frame: pd.DataFrame, max_rows: int = 80) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame.head(max_rows).copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.6f}"
        return str(value)

    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in view.columns) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def render_report(overall: pd.DataFrame, comparison: pd.DataFrame, slice_tables: dict[str, pd.DataFrame], decision: dict[str, Any]) -> str:
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: WMIN4 채택 후보 `min1_huber_refit_partial`이 0604 신규 라벨 stress에서 현행 PP258 대비 명확히 악화되는지 확인한다.",
        "- 금지: 0604 결과로 후보나 경계값을 선택하지 않는다. 0604는 안전 확인 전용이다.",
        "- PP258 기준: 신규 입력 raw 호환 PP258 report-layer proxy. exact PP258 upstream raw adapter가 아직 없으므로, 현재 서비스 adapter와 같은 proxy 입력 매핑을 사용한다.",
        "- WMIN4 기준: validation에서 선택된 partial Huber refit을 그대로 학습하고 0604에는 한 번만 적용한다.",
        "",
        "## 1. Gate 판단",
        "",
        f"- status: `{decision['status']}`",
        f"- reason: {decision['reason']}",
        f"- p95 tolerance: {STRESS_P95_TOL:.3f}, MAPE tolerance: {STRESS_MAPE_TOL:.3f}",
        "",
        "## 2. 0604 전체 지표",
        "",
        markdown_table(overall.round(6)),
        "",
        "## 3. WMIN4 vs PP258 proxy",
        "",
        markdown_table(comparison.round(6)),
    ]
    for title, table in slice_tables.items():
        lines.extend(["", f"## {title}", "", markdown_table(table.round(6), max_rows=120)])
    lines.extend([
        "",
        "## 산출물",
        "",
        "- `outputs/0604_candidate_predictions.csv`",
        "- `outputs/0604_overall_metrics.csv`",
        "- `outputs/0604_wmin4_vs_pp258_comparison.csv`",
        "- `outputs/0604_slice_*_comparison.csv`",
        "- `artifacts/run_config.json`",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    start = time.time()
    ensure_dirs()

    ops_min1, min1_coverage = compute_min1_svc_0604()
    ops_for_pp258 = pd.read_csv(OPS_LABELS, low_memory=False)
    ops_for_pp258 = ops_for_pp258[ops_for_pp258["actual_price_krw"].notna()].copy()
    usd = pd.to_numeric(ops_for_pp258.get("actual_price_usd_equiv"), errors="coerce")
    ops_for_pp258 = ops_for_pp258[~(usd < 50.0)].copy().reset_index(drop=True)
    ops_for_pp258["actual_price"] = pd.to_numeric(ops_for_pp258["actual_price_krw"], errors="coerce")
    ops_for_pp258["actual_log"] = np.log(np.clip(ops_for_pp258["actual_price"].to_numpy(dtype=float), 1.0, None))

    pp258_input, pp258_pred = build_pp258_proxy_0604(ops_for_pp258)
    wmin4_frame = build_wmin4_0604_frame(ops_min1)
    validation_frame = wmin3.make_variant_frames("partial")["validation"].reset_index(drop=True)
    wmin4_pred, wmin4_model = wmin3.fit_refit_candidate(validation_frame, wmin4_frame)

    pred_rows = [
        prediction_frame(wmin4_frame, MIN1_SVC, wmin4_frame[MIN1_SVC].to_numpy(dtype=float), "min1_svc_seed_mean"),
        prediction_frame(wmin4_frame, WMIN4_BASIS, wmin4_frame[WMIN4_BASIS].to_numpy(dtype=float), "min1_70_30_basis"),
        prediction_frame(wmin4_frame, WMIN4_SELECTED, wmin4_pred, "validation_fit_partial_huber_refit"),
        prediction_frame(
            wmin4_frame.assign(
                svc_group_level=pp258_pred["svc_group_level"].to_numpy(),
                svc_coverage_tier=pp258_pred["svc_coverage_tier"].to_numpy(),
                svc_group_n=pp258_pred["svc_group_n"].to_numpy(),
                l10_quantile_width=pp258_pred["quantile_width"].to_numpy(),
            ),
            PP258_PROXY,
            pp258_pred["final_price_log"].to_numpy(dtype=float),
            "pp258_report_layer_proxy",
        ),
        prediction_frame(wmin4_frame, CURRENT_70_30, ops_for_pp258["v01_operational_pred_log"].to_numpy(dtype=float), "current_v01_70_30"),
        prediction_frame(wmin4_frame, CURRENT_PPV8, ops_for_pp258["pp_v8_compact_blend_mape_guarded_pred_log"].to_numpy(dtype=float), "current_service_primary_ppv8"),
    ]
    predictions = pd.concat(pred_rows, ignore_index=True)
    overall = metrics_by_group(predictions).sort_values(["MAPE", "p95_APE", "MdAPE"]).reset_index(drop=True)
    comparison = compare_against(predictions, PP258_PROXY, WMIN4_SELECTED)

    slice_tables = {
        "4. svc_group_level별 악화 분해": compare_against(predictions, PP258_PROXY, WMIN4_SELECTED, ["svc_group_level"]),
        "5. svc_coverage_tier별 악화 분해": compare_against(predictions, PP258_PROXY, WMIN4_SELECTED, ["svc_coverage_tier"]),
        "6. svc_group_n_bin별 악화 분해": compare_against(predictions, PP258_PROXY, WMIN4_SELECTED, ["svc_group_n_bin"]),
    }
    cmp_row = comparison.iloc[0].to_dict()
    delta_mape = float(cmp_row["delta_MAPE_candidate_minus_baseline"])
    delta_p95 = float(cmp_row["delta_p95_APE_candidate_minus_baseline"])
    if delta_mape <= STRESS_MAPE_TOL and delta_p95 <= STRESS_P95_TOL:
        status = "pass_continue"
        reason = (
            f"WMIN4 0604 stress가 PP258 proxy 대비 명확한 악화를 보이지 않음 "
            f"(MAPE delta {delta_mape:+.6f}, p95 delta {delta_p95:+.6f}). PP-WMIN6 이후 진행 가능."
        )
    else:
        status = "hold_for_staleness_diagnosis"
        reason = (
            f"WMIN4가 0604에서 PP258 proxy 대비 tolerance를 초과해 악화 "
            f"(MAPE delta {delta_mape:+.6f}, p95 delta {delta_p95:+.6f}). min1 정밀 매칭/prior staleness 분해 필요."
        )
    decision = {"status": status, "reason": reason, "delta_MAPE": delta_mape, "delta_p95_APE": delta_p95}

    predictions.to_csv(EXP_DIR / "outputs" / "0604_candidate_predictions.csv", index=False)
    overall.to_csv(EXP_DIR / "outputs" / "0604_overall_metrics.csv", index=False)
    comparison.to_csv(EXP_DIR / "outputs" / "0604_wmin4_vs_pp258_comparison.csv", index=False)
    min1_coverage.to_csv(EXP_DIR / "outputs" / "0604_min1_coverage_by_seed.csv", index=False)
    pp258_input.to_csv(EXP_DIR / "outputs" / "0604_pp258_proxy_input.csv", index=False)
    for title, table in slice_tables.items():
        slug = title.split(" ", 1)[1].replace("별 악화 분해", "").replace("svc_", "svc_").replace(" ", "_")
        table.to_csv(EXP_DIR / "outputs" / f"0604_slice_{slug}_comparison.csv", index=False)

    coeffs = wmin3.hcoef3.coefficient_frame(wmin4_model, wmin3.STABLE_CONFIG)
    coeffs.to_csv(EXP_DIR / "outputs" / "wmin4_partial_huber_coefficients.csv", index=False)
    run_config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selection_policy": "0604 stress only; no candidate or threshold selection from 0604",
        "baseline": PP258_PROXY,
        "candidate": WMIN4_SELECTED,
        "stress_p95_tolerance": STRESS_P95_TOL,
        "stress_mape_tolerance": STRESS_MAPE_TOL,
        "decision": decision,
        "inputs": {
            "ops_labels": rel(OPS_LABELS),
            "ops_warm_features": rel(OPS_WARM_FEATURES),
            "pp258_script": rel(PP258_SCRIPT),
            "warm_refreeze_dir": rel(WARM_REFREEZE_DIR),
            "wmin2_script": rel(Path(wmin2.__file__)),
            "wmin3_script": rel(Path(wmin3.__file__)),
        },
        "notes": [
            "PP258 exact upstream raw adapter is not available; use the same raw-compatible PP258 proxy mapping exposed by the v0.1 service adapter.",
            "WMIN4 partial Huber model is fitted on validation only and applied once to 0604.",
            "0604 is not used to tune any threshold or candidate.",
        ],
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_report(overall, comparison, slice_tables, decision)
    html_doc = md_to_html(md)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_wmin5_warm_min1_0604_stress_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed status={status}\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "completed",
        "decision": decision,
        "seconds": round(time.time() - start, 2),
        "experiment_dir": rel(EXP_DIR),
        "report": rel(EXP_DIR / "reports" / "result_report.md"),
        "summary_doc": rel(DOC_ROOT / "pp_wmin5_warm_min1_0604_stress_summary.md"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
