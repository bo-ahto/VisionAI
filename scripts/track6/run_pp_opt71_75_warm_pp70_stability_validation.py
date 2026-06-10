#!/usr/bin/env python3
"""Run PP-OPT71..75 Warm PP70 stability validation.

This batch does not tune new correction coefficients.  It stress-tests the
current top Warm candidates from PP64/PP70 on the existing non-submission
validation OOF and fixed test rows, then reports whether the PP70 micro gain is
stable enough to replace PP64 operationally.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
OPT65_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt65_70_warm_pp64_refinement_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt65 = load_module("pp_opt65_helpers", OPT65_SCRIPT)
opt8 = opt65.opt8
BASE_CANDIDATE = opt65.BASE_CANDIDATE
INCUMBENT = opt65.INCUMBENT

EXP_ID = "PP-OPT71-75"
EXP_SLUG = "PP-OPT71_75_warm_pp70_stability_validation"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP65_DIR = REPO / "experiments" / "track6" / "PP-OPT65_70_warm_pp64_refinement_experiments"
PP65_PREDS = PP65_DIR / "outputs" / "candidate_predictions.csv"
PP65_AGG = PP65_DIR / "outputs" / "aggregate_candidate_stability.csv"
PP65_ITEMS = PP65_DIR / "outputs" / "experiment_item_summary.csv"
PP65_CONFIG = PP65_DIR / "artifacts" / "run_config.json"

SEED = 20260609
EPS = 1e-12
REPEATS = 260
SAMPLE_FRAC = 0.72


ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT71",
        "priority": "1",
        "title": "fixed validation/test reference comparison",
        "description": "기존 fixed validation/test 전체 row에서 주요 후보를 다시 비교한다.",
    },
    {
        "item_id": "PP-OPT72",
        "priority": "2",
        "title": "validation repeated holdout stability",
        "description": "validation OOF에서 confidence, price, artist, risk 기반 반복 부분표본 승률을 계산한다.",
    },
    {
        "item_id": "PP-OPT73",
        "priority": "3",
        "title": "test bootstrap stress stability",
        "description": "fixed test를 재학습 없이 bootstrap/stratified resample하여 후보 간 승률을 계산한다.",
    },
    {
        "item_id": "PP-OPT74",
        "priority": "4",
        "title": "PP70 vs PP64 replacement decision",
        "description": "PP70의 미세 개선이 PP64 교체 근거로 충분한지 판단한다.",
    },
    {
        "item_id": "PP-OPT75",
        "priority": "5",
        "title": "next experiment recommendation",
        "description": "검증 결과를 바탕으로 다음 실험 방향을 정리한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 60) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 60) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def select_candidates() -> tuple[dict[str, str], dict[str, Any]]:
    config = load_json(PP65_CONFIG)
    agg = pd.read_csv(PP65_AGG)
    item_summary = pd.read_csv(PP65_ITEMS)
    pp70 = config["selection_decision"]["protocol_candidate"]

    labels: dict[str, str] = {
        "hcoef_stable_source": BASE_CANDIDATE,
        "incumbent_pp7": INCUMBENT,
        "pp20_p95_reference": "previous_challenger_pp20",
        "pp48_stability_reference": "reference_pp48_score",
        "pp52_quantile_reference": "reference_pp52_challenger",
        "pp58_mape_reference": "reference_pp58_challenger",
        "pp64_current_best": "reference_pp64_current_best",
        "pp70_refinement_candidate": pp70,
    }

    top_mape = agg.sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]
    top_p95_operational = agg[agg["operational_pass_vs_incumbent"]].sort_values(["test_p95_APE", "test_MAPE"]).iloc[0]["candidate"]
    labels["pp67_best_mape_non_operational"] = str(top_mape)
    labels["best_operational_p95_in_pp65_70"] = str(top_p95_operational)

    for item_id in ["PP-OPT65", "PP-OPT66", "PP-OPT68", "PP-OPT69"]:
        row = item_summary[item_summary["item_id"].eq(item_id)]
        if not row.empty:
            labels[f"{item_id.lower().replace('-', '_')}_best"] = str(row.iloc[0]["best_candidate"])

    # Preserve insertion order while removing duplicate candidate names.
    deduped: dict[str, str] = {}
    seen: set[str] = set()
    for label, candidate in labels.items():
        if candidate not in seen:
            deduped[label] = candidate
            seen.add(candidate)
    return deduped, config


def load_predictions(selected: dict[str, str]) -> pd.DataFrame:
    needed = set(selected.values())
    usecols = [
        "candidate",
        "family",
        "item_id",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "pred_log",
        "correction_log",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    chunks = []
    for chunk in pd.read_csv(PP65_PREDS, usecols=usecols, chunksize=240_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No selected predictions loaded")
    predictions = pd.concat(chunks, ignore_index=True)
    label_lookup = {candidate: label for label, candidate in selected.items()}
    predictions["candidate_label"] = predictions["candidate"].map(label_lookup).fillna(predictions["candidate"])
    return predictions


def build_matrix(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"].eq(eval_split)].copy()
    meta_cols = [
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "quantile_width",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
    ]
    first_label = subset["candidate_label"].iloc[0]
    meta = (
        subset[subset["candidate_label"].eq(first_label)][meta_cols]
        .drop_duplicates("_track6_row_id")
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )
    wide = subset.pivot_table(index="_track6_row_id", columns="candidate_label", values="pred_log", aggfunc="first")
    wide = wide.reindex(meta["_track6_row_id"]).reset_index(drop=True)
    return meta, wide


def metric_for_positions(meta: pd.DataFrame, wide: pd.DataFrame, positions: np.ndarray) -> pd.DataFrame:
    actual_price = meta.iloc[positions]["actual_price"].to_numpy(dtype=float)
    actual_log = meta.iloc[positions]["actual_log"].to_numpy(dtype=float)
    pred = wide.iloc[positions].to_numpy(dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0)
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred = pred[valid]
    ape = np.abs(safe_exp(pred) - actual_price[:, None]) / np.maximum(actual_price[:, None], EPS)
    return pd.DataFrame(
        {
            "candidate_label": list(wide.columns),
            "n": int(valid.sum()),
            "MdAPE": np.nanmedian(ape, axis=0),
            "MAPE": np.nanmean(ape, axis=0),
            "p95_APE": np.nanquantile(ape, 0.95, axis=0),
            "RMSE_log": np.sqrt(np.nanmean((pred - actual_log[:, None]) ** 2, axis=0)),
        }
    )


def risk_score(meta: pd.DataFrame) -> np.ndarray:
    qwidth = pd.to_numeric(meta["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(meta["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(meta["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    conf = meta["confidence_tier"].astype(str)
    price = meta["stable_price_band"].astype(str)
    return np.clip(
        0.38 * np.clip((qwidth - 1.20) / 0.95, 0, 1)
        + 0.22 * np.clip(spread / 0.18, 0, 1)
        + 0.14 * np.clip(gap / 0.06, 0, 1)
        + 0.16 * conf.eq("low_confidence").to_numpy(dtype=float)
        + 0.10 * price.eq("very_high_price").to_numpy(dtype=float),
        0,
        1,
    )


def sample_positions(meta: pd.DataFrame, eval_split: str) -> list[tuple[str, int, np.ndarray]]:
    rng = np.random.default_rng(SEED + (11 if eval_split == "test" else 0))
    all_positions = np.arange(len(meta))
    samples: list[tuple[str, int, np.ndarray]] = [("full_split", 0, all_positions)]

    tiers = meta["confidence_tier"].fillna("medium_confidence").astype(str).to_numpy()
    for repeat in range(REPEATS):
        selected: list[int] = []
        for tier in sorted(set(tiers)):
            idx = np.flatnonzero(tiers == tier)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            selected.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("confidence_stratified_rows", repeat, np.array(sorted(selected), dtype=int)))

    price = meta["stable_price_band"].fillna("unknown_price").astype(str).to_numpy()
    for repeat in range(REPEATS):
        selected = []
        for band in sorted(set(price)):
            idx = np.flatnonzero(price == band)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            selected.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("price_band_stratified_rows", repeat, np.array(sorted(selected), dtype=int)))

    artists = meta["artist_key"].fillna("__missing_artist__").astype(str)
    unique_artists = np.array(sorted(artists.unique()))
    for repeat in range(REPEATS):
        artist_n = max(1, int(round(len(unique_artists) * SAMPLE_FRAC)))
        chosen = set(rng.choice(unique_artists, size=artist_n, replace=False).tolist())
        idx = np.flatnonzero(artists.isin(chosen).to_numpy())
        samples.append(("artist_group_holdout", repeat, idx))

    for repeat in range(REPEATS):
        n = max(1, int(round(len(all_positions) * SAMPLE_FRAC)))
        samples.append(("row_bootstrap", repeat, rng.choice(all_positions, size=n, replace=True)))

    risk = risk_score(meta)
    threshold = float(np.quantile(risk, 0.58))
    risk_idx = np.flatnonzero(risk >= threshold)
    if len(risk_idx) > 10:
        for repeat in range(REPEATS):
            n = max(8, int(round(len(risk_idx) * 0.78)))
            samples.append(("risk_focus_bootstrap", repeat, rng.choice(risk_idx, size=n, replace=True)))

    return samples


def repeated_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for eval_split in ["validation_oof", "test"]:
        meta, wide = build_matrix(predictions, eval_split)
        for scenario, repeat, positions in sample_positions(meta, eval_split):
            metrics = metric_for_positions(meta, wide, positions)
            pp64 = metrics[metrics["candidate_label"].eq("pp64_current_best")].iloc[0]
            incumbent = metrics[metrics["candidate_label"].eq("incumbent_pp7")].iloc[0]
            pp70 = metrics[metrics["candidate_label"].eq("pp70_refinement_candidate")].iloc[0]
            for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                metrics[f"delta_vs_pp64_{metric}"] = metrics[metric] - float(pp64[metric])
                metrics[f"delta_vs_incumbent_{metric}"] = metrics[metric] - float(incumbent[metric])
                metrics[f"delta_vs_pp70_{metric}"] = metrics[metric] - float(pp70[metric])
            metrics["eval_split"] = eval_split
            metrics["scenario"] = scenario
            metrics["repeat"] = repeat
            rows.append(metrics)
    detail = pd.concat(rows, ignore_index=True)
    detail["wins_pp64_MAPE"] = detail["delta_vs_pp64_MAPE"] < 0
    detail["wins_pp64_p95"] = detail["delta_vs_pp64_p95_APE"] < 0
    detail["wins_pp64_MdAPE"] = detail["delta_vs_pp64_MdAPE"] < 0
    detail["wins_pp64_all3"] = detail["wins_pp64_MAPE"] & detail["wins_pp64_p95"] & detail["wins_pp64_MdAPE"]
    detail["wins_incumbent_MAPE"] = detail["delta_vs_incumbent_MAPE"] < 0
    detail["wins_incumbent_p95"] = detail["delta_vs_incumbent_p95_APE"] < 0
    detail["wins_incumbent_all3"] = (
        (detail["delta_vs_incumbent_MAPE"] < 0)
        & (detail["delta_vs_incumbent_p95_APE"] < 0)
        & (detail["delta_vs_incumbent_MdAPE"] < 0)
    )
    summary = (
        detail.groupby(["candidate_label", "eval_split", "scenario"])
        .agg(
            repeats=("repeat", "nunique"),
            mean_MAPE=("MAPE", "mean"),
            mean_p95_APE=("p95_APE", "mean"),
            mean_MdAPE=("MdAPE", "mean"),
            mean_delta_vs_pp64_MAPE=("delta_vs_pp64_MAPE", "mean"),
            median_delta_vs_pp64_MAPE=("delta_vs_pp64_MAPE", "median"),
            p10_delta_vs_pp64_MAPE=("delta_vs_pp64_MAPE", lambda s: float(np.quantile(s, 0.10))),
            p90_delta_vs_pp64_MAPE=("delta_vs_pp64_MAPE", lambda s: float(np.quantile(s, 0.90))),
            mean_delta_vs_pp64_p95_APE=("delta_vs_pp64_p95_APE", "mean"),
            median_delta_vs_pp64_p95_APE=("delta_vs_pp64_p95_APE", "median"),
            p10_delta_vs_pp64_p95_APE=("delta_vs_pp64_p95_APE", lambda s: float(np.quantile(s, 0.10))),
            p90_delta_vs_pp64_p95_APE=("delta_vs_pp64_p95_APE", lambda s: float(np.quantile(s, 0.90))),
            pp64_MAPE_win_rate=("wins_pp64_MAPE", "mean"),
            pp64_p95_win_rate=("wins_pp64_p95", "mean"),
            pp64_MdAPE_win_rate=("wins_pp64_MdAPE", "mean"),
            pp64_all3_win_rate=("wins_pp64_all3", "mean"),
            mean_delta_vs_incumbent_MAPE=("delta_vs_incumbent_MAPE", "mean"),
            mean_delta_vs_incumbent_p95_APE=("delta_vs_incumbent_p95_APE", "mean"),
            incumbent_MAPE_win_rate=("wins_incumbent_MAPE", "mean"),
            incumbent_p95_win_rate=("wins_incumbent_p95", "mean"),
            incumbent_all3_win_rate=("wins_incumbent_all3", "mean"),
        )
        .reset_index()
    )
    summary["stability_score_vs_pp64"] = (
        summary["mean_delta_vs_pp64_MAPE"].fillna(9)
        + 0.70 * np.maximum(summary["mean_delta_vs_pp64_p95_APE"].fillna(9), 0)
        + 0.20 * (1.0 - summary["pp64_MAPE_win_rate"].fillna(0))
        + 0.10 * (1.0 - summary["pp64_p95_win_rate"].fillna(0))
    )
    return detail, summary


def fixed_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    metrics = opt8.summarize_predictions(predictions.rename(columns={"candidate_label": "candidate_label_keep"}))
    label_map = predictions[["candidate", "candidate_label"]].drop_duplicates().set_index("candidate")["candidate_label"].to_dict()
    metrics["candidate_label"] = metrics["candidate"].map(label_map).fillna(metrics["candidate"])
    keep = [
        "candidate_label",
        "candidate",
        "family",
        "item_id",
        "eval_split",
        "n",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_vs_incumbent_MAPE",
        "delta_vs_incumbent_p95_APE",
    ]
    return metrics[keep].sort_values(["eval_split", "MAPE", "p95_APE"])


def aggregate_summary(summary: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    scenario_summary = (
        summary.groupby("candidate_label")
        .agg(
            scenario_count=("scenario", "nunique"),
            split_count=("eval_split", "nunique"),
            avg_delta_vs_pp64_MAPE=("mean_delta_vs_pp64_MAPE", "mean"),
            avg_delta_vs_pp64_p95_APE=("mean_delta_vs_pp64_p95_APE", "mean"),
            avg_pp64_MAPE_win_rate=("pp64_MAPE_win_rate", "mean"),
            avg_pp64_p95_win_rate=("pp64_p95_win_rate", "mean"),
            avg_pp64_all3_win_rate=("pp64_all3_win_rate", "mean"),
            avg_delta_vs_incumbent_MAPE=("mean_delta_vs_incumbent_MAPE", "mean"),
            avg_delta_vs_incumbent_p95_APE=("mean_delta_vs_incumbent_p95_APE", "mean"),
            avg_incumbent_MAPE_win_rate=("incumbent_MAPE_win_rate", "mean"),
            avg_incumbent_p95_win_rate=("incumbent_p95_win_rate", "mean"),
            avg_incumbent_all3_win_rate=("incumbent_all3_win_rate", "mean"),
            avg_stability_score_vs_pp64=("stability_score_vs_pp64", "mean"),
        )
        .reset_index()
    )
    test = fixed[fixed["eval_split"].eq("test")][
        ["candidate_label", "MAPE", "p95_APE", "MdAPE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].rename(
        columns={
            "MAPE": "fixed_test_MAPE",
            "p95_APE": "fixed_test_p95_APE",
            "MdAPE": "fixed_test_MdAPE",
            "RMSE_log": "fixed_test_RMSE_log",
            "delta_vs_incumbent_MAPE": "fixed_test_delta_vs_incumbent_MAPE",
            "delta_vs_incumbent_p95_APE": "fixed_test_delta_vs_incumbent_p95_APE",
        }
    )
    validation = fixed[fixed["eval_split"].eq("validation_oof")][
        ["candidate_label", "MAPE", "p95_APE", "MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].rename(
        columns={
            "MAPE": "fixed_validation_MAPE",
            "p95_APE": "fixed_validation_p95_APE",
            "MdAPE": "fixed_validation_MdAPE",
            "delta_vs_incumbent_MAPE": "fixed_validation_delta_vs_incumbent_MAPE",
            "delta_vs_incumbent_p95_APE": "fixed_validation_delta_vs_incumbent_p95_APE",
        }
    )
    out = scenario_summary.merge(validation, on="candidate_label", how="left").merge(test, on="candidate_label", how="left")
    pp64_test = out[out["candidate_label"].eq("pp64_current_best")].iloc[0]
    out["fixed_test_delta_vs_pp64_MAPE"] = out["fixed_test_MAPE"] - float(pp64_test["fixed_test_MAPE"])
    out["fixed_test_delta_vs_pp64_p95_APE"] = out["fixed_test_p95_APE"] - float(pp64_test["fixed_test_p95_APE"])
    out["replacement_score"] = (
        out["fixed_test_delta_vs_pp64_MAPE"].fillna(9)
        + 0.70 * np.maximum(out["fixed_test_delta_vs_pp64_p95_APE"].fillna(9), 0)
        + 0.50 * np.maximum(out["avg_delta_vs_pp64_MAPE"].fillna(9), 0)
        + 0.35 * np.maximum(out["avg_delta_vs_pp64_p95_APE"].fillna(9), 0)
        + 0.04 * (0.50 - out["avg_pp64_MAPE_win_rate"].fillna(0))
    )
    return out.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"])


def decision_text(aggregate: pd.DataFrame) -> tuple[str, str]:
    pp70 = aggregate[aggregate["candidate_label"].eq("pp70_refinement_candidate")].iloc[0]
    pp64 = aggregate[aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    if (
        pp70["fixed_test_delta_vs_pp64_MAPE"] <= 0
        and pp70["fixed_test_delta_vs_pp64_p95_APE"] <= 0
        and pp70["avg_pp64_MAPE_win_rate"] >= 0.50
        and pp70["avg_pp64_p95_win_rate"] >= 0.45
    ):
        verdict = "PP70을 PP64의 소폭 개선 운영 후보로 둘 수 있다."
        reason = "fixed test에서 MAPE와 p95가 모두 PP64보다 낮고, 반복 검증 평균에서도 PP64 대비 MAPE 승률이 50% 이상이다."
    else:
        verdict = "PP64를 운영 기준으로 유지하고 PP70은 보조 후보로 두는 것이 더 안전하다."
        reason = "PP70의 fixed test 개선폭이 매우 작거나 반복 검증 승률이 충분히 우세하지 않다."
    detail = (
        f"PP70 vs PP64 fixed test delta: MAPE {pp70['fixed_test_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {pp70['fixed_test_delta_vs_pp64_p95_APE']:+.6f}. "
        f"반복 검증 평균 승률: MAPE {pp70['avg_pp64_MAPE_win_rate']:.3f}, "
        f"p95 {pp70['avg_pp64_p95_win_rate']:.3f}, all3 {pp70['avg_pp64_all3_win_rate']:.3f}."
    )
    _ = pp64
    return verdict, f"{reason} {detail}"


def render_reports(
    fixed: pd.DataFrame,
    repeated_detail: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    aggregate: pd.DataFrame,
    selected: dict[str, str],
    parent_config: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    verdict, reason = decision_text(aggregate)
    fixed_cols = ["candidate_label", "eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    agg_cols = [
        "candidate_label",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_vs_pp64_MAPE",
        "fixed_test_delta_vs_pp64_p95_APE",
        "avg_delta_vs_pp64_MAPE",
        "avg_delta_vs_pp64_p95_APE",
        "avg_pp64_MAPE_win_rate",
        "avg_pp64_p95_win_rate",
        "avg_pp64_all3_win_rate",
        "avg_delta_vs_incumbent_MAPE",
        "avg_delta_vs_incumbent_p95_APE",
        "avg_incumbent_MAPE_win_rate",
        "avg_incumbent_p95_win_rate",
        "replacement_score",
    ]
    pp70_scenarios = repeated_summary[repeated_summary["candidate_label"].eq("pp70_refinement_candidate")].sort_values(
        ["eval_split", "scenario"]
    )
    scenario_cols = [
        "candidate_label",
        "eval_split",
        "scenario",
        "repeats",
        "mean_delta_vs_pp64_MAPE",
        "mean_delta_vs_pp64_p95_APE",
        "pp64_MAPE_win_rate",
        "pp64_p95_win_rate",
        "pp64_all3_win_rate",
        "mean_delta_vs_incumbent_MAPE",
        "mean_delta_vs_incumbent_p95_APE",
    ]
    selected_rows = [{"label": label, "candidate": candidate} for label, candidate in selected.items()]
    selected_df = pd.DataFrame(selected_rows)

    md = "\n".join(
        [
            "# PP-OPT71~75 Warm PP70 안정성 검증 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 검증 방식: 후보 추가 튜닝 없이 PP65~70 산출 후보를 반복 holdout/bootstrap으로 비교",
            f"- 결론: {verdict}",
            f"- 근거: {reason}",
            "",
            "## 후보 라벨",
            markdown_table(selected_df, ["label", "candidate"], 40),
            "",
            "## 전체 후보 안정성 순위",
            markdown_table(aggregate, agg_cols, 40),
            "",
            "## fixed validation/test metric",
            markdown_table(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 60),
            "",
            "## PP70 시나리오별 PP64 대비 안정성",
            markdown_table(pp70_scenarios, scenario_cols, 20),
            "",
            "## 해석",
            "- PP70은 fixed test에서 PP64보다 MAPE와 p95가 모두 낮지만 개선폭은 1e-5 미만이다.",
            "- 반복 검증에서 PP64 대비 승률이 압도적이지 않으면, PP70은 구조적 개선이라기보다 PP64의 미세 튜닝으로 해석해야 한다.",
            "- p95를 더 크게 낮추려면 PP20/PP48 계열 안정 후보를 위험 row에만 쓰는 tail 라우팅을 다시 별도 탐색해야 한다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT71~75 Warm PP70 안정성 검증 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1280px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    li {{ margin: 6px 0; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT71~75 Warm PP70 안정성 검증 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout"><strong>{html.escape(verdict)}</strong><br>{html.escape(reason)}</div>
  <div class="grid">
    <div class="panel"><strong>비교 후보</strong>{len(selected)}개</div>
    <div class="panel"><strong>반복 검증 row</strong>{len(repeated_detail):,}개 metric</div>
    <div class="panel"><strong>부모 후보</strong>{html.escape(parent_config['selection_decision']['protocol_candidate'][:44])}</div>
    <div class="panel"><strong>시나리오</strong>{repeated_summary['scenario'].nunique()}개</div>
  </div>
  <h2>1. 후보 라벨</h2>
  {table_html(selected_df, ["label", "candidate"], 40)}
  <h2>2. 전체 후보 안정성 순위</h2>
  {table_html(aggregate, agg_cols, 40)}
  <h2>3. fixed validation/test metric</h2>
  {table_html(fixed.sort_values(["eval_split", "MAPE", "p95_APE"]), fixed_cols, 60)}
  <h2>4. PP70 시나리오별 PP64 대비 안정성</h2>
  {table_html(pp70_scenarios, scenario_cols, 20)}
  <h2>5. 해석</h2>
  <ul>
    <li>PP70은 fixed test에서 PP64보다 MAPE와 p95가 모두 낮지만 개선폭은 1e-5 미만이다.</li>
    <li>반복 검증에서 PP64 대비 승률이 압도적이지 않으면, PP70은 구조적 개선이라기보다 PP64의 미세 튜닝으로 해석해야 한다.</li>
    <li>p95를 더 크게 낮추려면 PP20/PP48 계열 안정 후보를 위험 row에만 쓰는 tail 라우팅을 다시 별도 탐색해야 한다.</li>
  </ul>
  <h2>6. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    selected, parent_config = select_candidates()
    predictions = load_predictions(selected)
    fixed = fixed_metrics(predictions)
    repeated_detail, repeated_summary = repeated_metrics(predictions)
    aggregate = aggregate_summary(repeated_summary, fixed)
    verdict, reason = decision_text(aggregate)
    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "repeats_per_resample_scenario": REPEATS,
        "sample_fraction": SAMPLE_FRAC,
        "selected_candidates": selected,
        "candidate_count": len(selected),
        "validation_rows": int(predictions["eval_split"].eq("validation_oof").sum() / len(selected)),
        "test_rows": int(predictions["eval_split"].eq("test").sum() / len(selected)),
        "decision": {
            "verdict": verdict,
            "reason": reason,
        },
        "items": ITEMS,
        "sources": {
            "pp65_config": str(PP65_CONFIG.relative_to(REPO)),
            "pp65_predictions": str(PP65_PREDS.relative_to(REPO)),
            "pp65_aggregate": str(PP65_AGG.relative_to(REPO)),
            "pp65_item_summary": str(PP65_ITEMS.relative_to(REPO)),
            "pp65_helper": str(OPT65_SCRIPT.relative_to(REPO)),
        },
    }
    fixed.to_csv(OUT_DIR / "fixed_candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "stability_repeated_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "stability_repeated_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "stability_candidate_aggregate.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(fixed, repeated_detail, repeated_summary, aggregate, selected, parent_config, config)
    (REPORT_DIR / "pp70_stability_validation_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp70_stability_validation_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nAggregate:")
    print(
        aggregate[
            [
                "candidate_label",
                "fixed_test_MAPE",
                "fixed_test_p95_APE",
                "fixed_test_delta_vs_pp64_MAPE",
                "fixed_test_delta_vs_pp64_p95_APE",
                "avg_delta_vs_pp64_MAPE",
                "avg_delta_vs_pp64_p95_APE",
                "avg_pp64_MAPE_win_rate",
                "avg_pp64_p95_win_rate",
                "avg_pp64_all3_win_rate",
                "replacement_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
