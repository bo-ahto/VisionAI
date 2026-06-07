#!/usr/bin/env python3
"""Run Cold gap revalidation experiments PP-Y17~PP-Y20.

These experiments intentionally reuse existing prediction artifacts. The goal
is not broad test-set searching, but closing the remaining validation/OOF and
stability gaps around strong Cold candidates.
"""
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

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, SEED, metrics  # noqa: E402
from run_pp_w_experiments import base_feature_sets, load_cold_with_meta  # noqa: E402


EXPERIMENTS = {
    "PP-Y17": {"slug": "PP-Y17_cold_y10_oof_fixed_routing_revalidation", "title": "Cold PP-Y10 validation 고정 라우팅 재검증"},
    "PP-Y18": {"slug": "PP-Y18_cold_y16_top_candidate_stability", "title": "Cold PP-Y16 test 상위 후보 안정성 검증"},
    "PP-Y19": {"slug": "PP-Y19_cold_y2_artist_bootstrap_stability", "title": "Cold PP-Y2 split/작가 bootstrap 안정성"},
    "PP-Y20": {"slug": "PP-Y20_cold_mape_p95_purpose_routing", "title": "Cold MAPE/p95 목적별 라우팅 결합"},
}

SUMMARY_PATH = BASE_EXP_DIR / "PP-Y17_Y20_cold_gap_summary_metrics.csv"
COMBINED_SUMMARY_PATH = BASE_EXP_DIR / "PP-Y_cold_combination_summary_metrics.csv"

Y2_SOURCE = ("PP-Y2_cold_lgbq_search_external_combo", "lgbq_search_all_external_interaction")
W4_SOURCE = ("PP-W4_cold_lightgbm_quantile_artist_meta_catboost_residual", "base_lightgbm_quantile_meta_all")
Y16_DEFENSIVE = ("PP-Y16_cold_y15_oof_fixed_revalidation", "lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35")
Y16_P95_SOURCE = ("PP-Y16_cold_y15_oof_fixed_revalidation", "lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15")


def metric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["_track6_row_id", "actual_log", "actual_price"]].rename(
        columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"}
    )


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(metric_frame(frame), pred_log)


def source_prediction(folder: str, candidate: str, split: str, *, allow_validation_oof: bool = False) -> pd.DataFrame:
    df = pd.read_csv(BASE_EXP_DIR / folder / "outputs" / "predictions.csv", low_memory=False)
    split_values = [split]
    if allow_validation_oof and split == "validation":
        split_values = ["validation", "validation_oof"]
    mask = (
        df["candidate"].astype(str).eq(candidate)
        & df["scope"].astype(str).eq("cold")
        & df["split"].astype(str).isin(split_values)
    )
    out = df[mask].drop_duplicates("_track6_row_id").sort_values("_track6_row_id").reset_index(drop=True)
    if out.empty:
        raise ValueError(f"missing source: {folder} {candidate} {split}")
    return out


def add_metric(
    rows: list[dict[str, Any]],
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        **metric_values(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def prediction_frame(
    exp_id: str,
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": "cold",
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["actual_log"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["actual_price"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    for col in ["quantile_width_log", "price_range_ratio", "selected_source", "artist_key"]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def select_by_validation(metrics_df: pd.DataFrame, id_col: str = "candidate") -> list[tuple[str, pd.Series]]:
    val = metrics_df[metrics_df["split"].astype(str).eq("validation")].copy()
    if val.empty:
        raise ValueError("empty validation metrics for selection")
    best_mdape = float(val["MdAPE"].min())
    val["balanced_rank"] = (
        0.50 * val["MdAPE"].rank(method="min")
        + 0.25 * val["MAPE"].rank(method="min")
        + 0.25 * val["p95_APE"].rank(method="min")
    )
    selectors = [
        ("validation_best_mdape", val.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]),
        ("validation_mape_guarded", val.assign(_score=np.where(val["MdAPE"] <= best_mdape * 1.08, val["MAPE"], np.inf)).sort_values(["_score", "MdAPE", "p95_APE"]).iloc[0]),
        ("validation_p95_guarded", val.assign(_score=np.where(val["MdAPE"] <= best_mdape * 1.10, val["p95_APE"], np.inf)).sort_values(["_score", "MdAPE", "MAPE"]).iloc[0]),
        ("validation_balanced_rank", val.sort_values(["balanced_rank", "MdAPE", "MAPE", "p95_APE"]).iloc[0]),
    ]
    return [(name, row) for name, row in selectors if pd.notna(row[id_col])]


def run_y17() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    metrics_df = pd.read_csv(BASE_EXP_DIR / "PP-Y10_cold_uncertainty_width_routing" / "outputs" / "metrics.csv")
    selected = select_by_validation(metrics_df)
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for selector, row in selected:
        source_candidate = str(row["candidate"])
        candidate = f"y10_fixed_{selector}"
        maps.append({
            "experiment_id": "PP-Y17",
            "selector": selector,
            "source_candidate": source_candidate,
            "stable_source": row.get("stable_source", ""),
            "risk_source": row.get("risk_source", ""),
            "threshold": row.get("threshold", np.nan),
            "validation_MdAPE": row["MdAPE"],
            "validation_MAPE": row["MAPE"],
            "validation_p95_APE": row["p95_APE"],
        })
        for split in ["validation", "test"]:
            src = source_prediction("PP-Y10_cold_uncertainty_width_routing", source_candidate, split)
            pred = src["pred_log"].to_numpy(dtype=float)
            add_metric(rows, "PP-Y17", candidate, split, src, pred, "y10_validation_fixed_routing", {
                "selector": selector,
                "source_candidate": source_candidate,
                "stable_source": row.get("stable_source", ""),
                "risk_source": row.get("risk_source", ""),
                "threshold": row.get("threshold", np.nan),
            })
            preds.append(prediction_frame("PP-Y17", candidate, split, src, pred, "y10_validation_fixed_routing", {
                "selector": selector,
                "source_candidate": source_candidate,
            }))
    return rows, preds, maps


def ape_from(frame: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    return np.abs(pred_price - frame["actual_price"].to_numpy(dtype=float)) / frame["actual_price"].to_numpy(dtype=float)


def metric_from_ape(frame: pd.DataFrame, pred_log: np.ndarray, ape: np.ndarray, indices: np.ndarray) -> dict[str, float]:
    actual_log = frame["actual_log"].to_numpy(dtype=float)[indices]
    pred = pred_log[indices]
    a = ape[indices]
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(a)),
        "MAPE": float(np.mean(a)),
        "p95_APE": float(np.quantile(a, 0.95)),
    }


def bootstrap_delta(
    frame: pd.DataFrame,
    base_pred: np.ndarray,
    candidate_pred: np.ndarray,
    *,
    group_col: str | None,
    n_boot: int = 800,
) -> dict[str, float]:
    rng = np.random.default_rng(SEED)
    base_ape = ape_from(frame, base_pred)
    cand_ape = ape_from(frame, candidate_pred)
    n = len(frame)
    if group_col and group_col in frame.columns:
        groups = frame[group_col].astype(str).fillna("__MISSING__").to_numpy()
        unique_groups = np.unique(groups)
        index_by_group = {group: np.flatnonzero(groups == group) for group in unique_groups}
        samples = []
        for _ in range(n_boot):
            picked = rng.choice(unique_groups, size=len(unique_groups), replace=True)
            samples.append(np.concatenate([index_by_group[group] for group in picked]))
    else:
        samples = [rng.integers(0, n, size=n) for _ in range(n_boot)]

    deltas = {"MdAPE": [], "MAPE": [], "p95_APE": []}
    for idx in samples:
        base_m = metric_from_ape(frame, base_pred, base_ape, idx)
        cand_m = metric_from_ape(frame, candidate_pred, cand_ape, idx)
        for key in deltas:
            deltas[key].append(base_m[key] - cand_m[key])

    out: dict[str, float] = {}
    prefix = "artist_bootstrap" if group_col else "row_bootstrap"
    for key, values in deltas.items():
        arr = np.asarray(values, dtype=float)
        out[f"{prefix}_{key}_delta_median"] = float(np.median(arr))
        out[f"{prefix}_{key}_delta_ci_low"] = float(np.quantile(arr, 0.025))
        out[f"{prefix}_{key}_delta_ci_high"] = float(np.quantile(arr, 0.975))
        out[f"{prefix}_{key}_prob_improve"] = float(np.mean(arr > 0))
    return out


def cold_artist_map() -> pd.DataFrame:
    _, val, test = load_cold_with_meta(base_feature_sets()["cold_lgb"])
    return pd.concat([val[["_track6_row_id", "artist_key"]], test[["_track6_row_id", "artist_key"]]], ignore_index=True).drop_duplicates("_track6_row_id")


def y16_candidate_list() -> list[str]:
    metrics_df = pd.read_csv(BASE_EXP_DIR / "PP-Y16_cold_y15_oof_fixed_revalidation" / "outputs" / "metrics.csv")
    top_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(5)["candidate"].astype(str).tolist()
    select = pd.read_csv(BASE_EXP_DIR / "PP-Y16_cold_y15_oof_fixed_revalidation" / "outputs" / "selection_summary.csv")
    selected = select["candidate"].astype(str).tolist()
    return list(dict.fromkeys([*selected, *top_test]))


def run_y18() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    artist_map = cold_artist_map()
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        base = source_prediction(*Y2_SOURCE, split)
        if split == "validation":
            base = base.rename(columns={"split": "_source_split"})
        base = base.merge(artist_map, on="_track6_row_id", how="left")
        base_pred = base["pred_log"].to_numpy(dtype=float)
        add_metric(rows, "PP-Y18", "component_pp_y2_baseline", split, base, base_pred, "stability_component")
        preds.append(prediction_frame("PP-Y18", "component_pp_y2_baseline", split, base, base_pred, "stability_component"))
        for source_candidate in y16_candidate_list():
            cand = source_prediction("PP-Y16_cold_y15_oof_fixed_revalidation", source_candidate, split, allow_validation_oof=True)
            cand = cand.merge(artist_map, on="_track6_row_id", how="left")
            merged = base[["_track6_row_id", "actual_log", "actual_price", "pred_log", "artist_key"]].rename(columns={"pred_log": "base_pred"}).merge(
                cand[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "candidate_pred"}),
                on="_track6_row_id",
                how="inner",
            )
            pred = merged["candidate_pred"].to_numpy(dtype=float)
            candidate = f"stability_{source_candidate}"
            extra = {"source_candidate": source_candidate}
            if split == "test":
                extra.update(bootstrap_delta(merged, merged["base_pred"].to_numpy(dtype=float), pred, group_col=None))
                extra.update(bootstrap_delta(merged, merged["base_pred"].to_numpy(dtype=float), pred, group_col="artist_key"))
                maps.append({"experiment_id": "PP-Y18", "candidate": candidate, **extra})
            add_metric(rows, "PP-Y18", candidate, split, merged, pred, "y16_candidate_stability", extra)
            preds.append(prediction_frame("PP-Y18", candidate, split, merged, pred, "y16_candidate_stability", {"source_candidate": source_candidate}))
    return rows, preds, maps


def bootstrap_metric_ci(frame: pd.DataFrame, pred_log: np.ndarray, *, group_col: str | None, n_boot: int = 800) -> dict[str, float]:
    rng = np.random.default_rng(SEED)
    ape = ape_from(frame, pred_log)
    n = len(frame)
    if group_col and group_col in frame.columns:
        groups = frame[group_col].astype(str).fillna("__MISSING__").to_numpy()
        unique_groups = np.unique(groups)
        index_by_group = {group: np.flatnonzero(groups == group) for group in unique_groups}
        samples = [
            np.concatenate([index_by_group[group] for group in rng.choice(unique_groups, size=len(unique_groups), replace=True)])
            for _ in range(n_boot)
        ]
    else:
        samples = [rng.integers(0, n, size=n) for _ in range(n_boot)]
    values = {"MdAPE": [], "MAPE": [], "p95_APE": []}
    for idx in samples:
        m = metric_from_ape(frame, pred_log, ape, idx)
        for key in values:
            values[key].append(m[key])
    prefix = "artist_bootstrap" if group_col else "row_bootstrap"
    out: dict[str, float] = {}
    for key, vals in values.items():
        arr = np.asarray(vals, dtype=float)
        out[f"{prefix}_{key}_median"] = float(np.median(arr))
        out[f"{prefix}_{key}_ci_low"] = float(np.quantile(arr, 0.025))
        out[f"{prefix}_{key}_ci_high"] = float(np.quantile(arr, 0.975))
    return out


def run_y19() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    artist_map = cold_artist_map()
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    for split in ["validation", "test"]:
        frame = source_prediction(*Y2_SOURCE, split).merge(artist_map, on="_track6_row_id", how="left")
        pred = frame["pred_log"].to_numpy(dtype=float)
        extra: dict[str, Any] = {}
        if split == "test":
            extra.update(bootstrap_metric_ci(frame, pred, group_col=None))
            extra.update(bootstrap_metric_ci(frame, pred, group_col="artist_key"))
            maps.append({"experiment_id": "PP-Y19", "candidate": "pp_y2_baseline_stability", **extra})
        add_metric(rows, "PP-Y19", "pp_y2_baseline_stability", split, frame, pred, "pp_y2_bootstrap_stability", extra)
        preds.append(prediction_frame("PP-Y19", "pp_y2_baseline_stability", split, frame, pred, "pp_y2_bootstrap_stability"))
    return rows, preds, maps


def merge_y20_sources(split: str) -> pd.DataFrame:
    y2 = source_prediction(*Y2_SOURCE, split)
    w4 = source_prediction(*W4_SOURCE, split)
    y16 = source_prediction(*Y16_DEFENSIVE, split, allow_validation_oof=True)
    y16_p95 = source_prediction(*Y16_P95_SOURCE, split, allow_validation_oof=True)
    merged = y2[["_track6_row_id", "actual_log", "actual_price", "pred_log", "quantile_width_log", "price_range_ratio"]].rename(columns={"pred_log": "pp_y2_pred"}).merge(
        w4[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "pp_w4_mape_pred"}),
        on="_track6_row_id",
        how="inner",
    ).merge(
        y16[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "pp_y16_defensive_pred"}),
        on="_track6_row_id",
        how="inner",
    ).merge(
        y16_p95[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "pp_y16_p95_pred"}),
        on="_track6_row_id",
        how="inner",
    )
    return merged


def run_y20() -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]]]:
    val = merge_y20_sources("validation")
    test = merge_y20_sources("test")
    thresholds = np.quantile(val["quantile_width_log"].to_numpy(dtype=float), [0.33, 0.50, 0.66, 0.80])
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    maps: list[dict[str, Any]] = []
    component_cols = ["pp_y2_pred", "pp_w4_mape_pred", "pp_y16_defensive_pred", "pp_y16_p95_pred"]
    for split, frame in [("validation", val), ("test", test)]:
        for col in component_cols:
            add_metric(rows, "PP-Y20", f"component_{col}", split, frame, frame[col].to_numpy(dtype=float), "purpose_routing_component")

    route_rows: list[dict[str, Any]] = []
    route_preds: dict[tuple[str, str], tuple[pd.DataFrame, np.ndarray, np.ndarray]] = {}
    for low in thresholds:
        for high in thresholds:
            if high <= low:
                continue
            candidate = f"route_y2_w4_y16_qwidth_{low:.3f}_{high:.3f}"
            maps.append({
                "experiment_id": "PP-Y20",
                "candidate": candidate,
                "low_threshold": float(low),
                "high_threshold": float(high),
                "rule": "qwidth<=low: PP-Y2, low<qwidth<=high: PP-W4, qwidth>high: PP-Y16 defensive",
            })
            for split, frame in [("validation", val), ("test", test)]:
                qwidth = frame["quantile_width_log"].to_numpy(dtype=float)
                selected = np.where(qwidth <= low, "pp_y2", np.where(qwidth <= high, "pp_w4_mape", "pp_y16_defensive"))
                pred = np.where(
                    qwidth <= low,
                    frame["pp_y2_pred"].to_numpy(dtype=float),
                    np.where(qwidth <= high, frame["pp_w4_mape_pred"].to_numpy(dtype=float), frame["pp_y16_defensive_pred"].to_numpy(dtype=float)),
                )
                extra = {
                    "low_threshold": float(low),
                    "high_threshold": float(high),
                    "pp_y2_rate": float(np.mean(selected == "pp_y2")),
                    "pp_w4_rate": float(np.mean(selected == "pp_w4_mape")),
                    "pp_y16_rate": float(np.mean(selected == "pp_y16_defensive")),
                }
                row = {
                    "experiment_id": "PP-Y20",
                    "candidate": candidate,
                    "scope": "cold",
                    "split": split,
                    "policy": "mape_p95_purpose_routing",
                    **metric_values(frame, pred),
                    **extra,
                }
                rows.append(row)
                route_rows.append(row)
                route_preds[(candidate, split)] = (frame, pred, selected)

    route_df = pd.DataFrame(route_rows)
    selected = select_by_validation(route_df)
    for selector, row in selected:
        source_candidate = str(row["candidate"])
        candidate = f"purpose_fixed_{selector}"
        maps.append({
            "experiment_id": "PP-Y20",
            "candidate": candidate,
            "selector": selector,
            "source_candidate": source_candidate,
            "validation_MdAPE": row["MdAPE"],
            "validation_MAPE": row["MAPE"],
            "validation_p95_APE": row["p95_APE"],
        })
        for split in ["validation", "test"]:
            frame, pred, selected_source = route_preds[(source_candidate, split)]
            add_metric(rows, "PP-Y20", candidate, split, frame, pred, "mape_p95_purpose_routing_fixed", {
                "selector": selector,
                "source_candidate": source_candidate,
            })
            out_frame = frame.copy()
            out_frame["selected_source"] = selected_source
            preds.append(prediction_frame("PP-Y20", candidate, split, out_frame, pred, "mape_p95_purpose_routing_fixed", {
                "selector": selector,
                "source_candidate": source_candidate,
            }))
    return rows, preds, maps


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6g}"
    return str(value).replace("\n", " ").replace("|", "\\|")


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "- 없음"
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        safe[col] = safe[col].map(format_cell)
    header = "| " + " | ".join(str(col) for col in safe.columns) + " |"
    sep = "| " + " | ".join("---" for _ in safe.columns) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in safe.itertuples(index=False, name=None)]
    return "\n".join([header, sep, *body])


def render_report(exp_id: str, metrics_df: pd.DataFrame, map_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    test = metrics_df[metrics_df["split"].astype(str).eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: Cold 후속 실험에서 남은 validation 고정/재현성 gap을 닫는다.",
        "- 원칙: test 결과만 보고 후보를 새로 고르지 않고, validation/OOF 또는 bootstrap 근거를 함께 기록한다.",
        "",
        "## Test 결과 상위",
        "",
        "| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in test.head(25).itertuples():
        lines.append(f"| `{row.candidate}` | `{row.policy}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")
    lines += ["", "## Map / Bootstrap", "", markdown_table(map_df)]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Map / Bootstrap</h2>{map_df.to_html(index=False, escape=True) if not map_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, rows: list[dict[str, Any]], preds: list[pd.DataFrame], maps: list[dict[str, Any]]) -> pd.DataFrame:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(rows)
    pred_df = pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()
    map_df = pd.DataFrame(maps)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    map_df.to_csv(exp_dir / "outputs" / "policy_map.csv", index=False)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "selection_policy": "validation_or_bootstrap_first",
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, metrics_df, map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")
    metrics_df["folder"] = str(exp_dir.relative_to(REPO))
    return metrics_df


def update_combined_summary(summary: pd.DataFrame) -> None:
    if COMBINED_SUMMARY_PATH.exists():
        prior = pd.read_csv(COMBINED_SUMMARY_PATH, low_memory=False)
        combined = pd.concat([prior, summary], ignore_index=True, sort=False)
        combined = combined.drop_duplicates(["experiment_id", "candidate", "scope", "split", "policy"], keep="last")
    else:
        combined = summary
    combined.to_csv(COMBINED_SUMMARY_PATH, index=False)


def main() -> None:
    start = time.time()
    runners = {
        "PP-Y17": run_y17,
        "PP-Y18": run_y18,
        "PP-Y19": run_y19,
        "PP-Y20": run_y20,
    }
    summary_frames: list[pd.DataFrame] = []
    for exp_id in ["PP-Y17", "PP-Y18", "PP-Y19", "PP-Y20"]:
        rows, preds, maps = runners[exp_id]()
        summary_frames.append(write_exp(exp_id, rows, preds, maps))
    summary = pd.concat(summary_frames, ignore_index=True, sort=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    update_combined_summary(summary)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": str(SUMMARY_PATH.relative_to(REPO)),
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
