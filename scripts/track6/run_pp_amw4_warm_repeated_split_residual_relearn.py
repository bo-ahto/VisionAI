#!/usr/bin/env python3
"""Run PP-AMW4 repeated split residual relearning for Warm AMW correction.

This is the stronger follow-up to PP-AMW3. PP-AMW3 used frozen PP-V8
predictions and bootstrapped them. PP-AMW4 rebuilds a Warm Huber baseline and
the AMW residual corrections on each repeated split.

The goal is not exact PP-V8 reproduction. PP-V8 is a compact blend of several
upstream candidates whose source predictions are not decomposed for arbitrary
new splits. This experiment isolates the core question: when the Warm model is
retrained and correction values are relearned on a new validation holdout, do
artist metadata and search-context corrections still improve the evaluation
holdout?
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, huber_model, normalize  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-AMW4"
EXP_SLUG = "PP-AMW4_warm_repeated_split_residual_relearn"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

POOL_FILES = [
    REPO / "data/track6_split/track6_train.csv",
    REPO / "data/track6_split/track6_val_warm.csv",
    REPO / "data/track6_split/track6_test_warm.csv",
]
SEARCH_SNAPSHOT_PATH = REPO / "data/track6/external_search/operational/track6_artist_search_operational_snapshot_latest.csv"
SEARCH_STANDARDIZED_PATH = REPO / "data/track6/external_search/operational/track6_artist_search_operational_standardized_latest.csv"

SEED = 20260606
ITERATIONS = 20
TARGET_VAL_ROWS = 520
TARGET_TEST_ROWS = 610
MIN_TRAIN_ROWS_PER_EVAL_ARTIST = 5

BASE_FEATURES = artifact_features()["warm"]

POLICIES = [
    {
        "candidate": "artist_meta_only_for_sale_conservative",
        "artist_weight": 1.0,
        "search_weight": 0.0,
        "total_cap": 0.03,
        "artist_min_rows": 30,
        "artist_cap": 0.03,
        "artist_shrink_k": 50.0,
        "search_cap": 0.05,
        "note": "작가 판매중 작품 수 구간 보정만 적용",
    },
    {
        "candidate": "search_only_gallery_conservative",
        "artist_weight": 0.0,
        "search_weight": 1.0,
        "total_cap": 0.03,
        "artist_min_rows": 30,
        "artist_cap": 0.03,
        "artist_shrink_k": 50.0,
        "search_cap": 0.05,
        "note": "갤러리/미술관 검색 출처 비중 보정만 적용",
    },
    {
        "candidate": "stack_conservative_half_half",
        "artist_weight": 0.5,
        "search_weight": 0.5,
        "total_cap": 0.03,
        "artist_min_rows": 30,
        "artist_cap": 0.03,
        "artist_shrink_k": 50.0,
        "search_cap": 0.05,
        "note": "PP-AMW2 보수 후보: 작가 메타 50% + 검색 50%, 전체 보정 ±0.03",
    },
    {
        "candidate": "stack_exploratory_full",
        "artist_weight": 1.0,
        "search_weight": 1.0,
        "total_cap": 0.05,
        "artist_min_rows": 30,
        "artist_cap": 0.03,
        "artist_shrink_k": 20.0,
        "search_cap": 0.05,
        "note": "PP-AMW2 탐색 후보: 작가 메타 100% + 검색 100%, 전체 보정 ±0.05",
    },
]


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def clean_artist_name(name: Any) -> str:
    value = "" if pd.isna(name) else str(name)
    value = re.sub(r"_[A-Z]+$", "", value).strip()
    return re.sub(r"\s+", " ", value)


def load_pool() -> pd.DataFrame:
    frames = []
    for path in POOL_FILES:
        frame = pd.read_csv(path, low_memory=False)
        frame["source_split_file"] = path.name
        frames.append(frame)
    pool = pd.concat(frames, ignore_index=True)
    pool = pool.drop_duplicates("_track6_row_id", keep="first").copy()
    pool["price_krw"] = pd.to_numeric(pool["price_krw"], errors="coerce")
    pool["ln_price_krw"] = pd.to_numeric(pool["ln_price_krw"], errors="coerce")
    pool = pool.dropna(subset=["price_krw", "ln_price_krw", "artist_key"]).copy()
    pool = pool[pool["price_krw"].gt(0)].copy()
    return pool.sort_values("_track6_row_id").reset_index(drop=True)


def load_search_features() -> pd.DataFrame:
    snapshot = pd.read_csv(SEARCH_SNAPSHOT_PATH, low_memory=False)
    snapshot["artist_search_name"] = snapshot["artist_search_name"].map(clean_artist_name)
    if SEARCH_STANDARDIZED_PATH.exists():
        standard = pd.read_csv(SEARCH_STANDARDIZED_PATH, low_memory=False)
        if {"artist_search_name", "source_group"}.issubset(standard.columns):
            standard["artist_search_name"] = standard["artist_search_name"].map(clean_artist_name)
            counts = standard.groupby(["artist_search_name", "source_group"], dropna=False).size().unstack(fill_value=0)
            total = counts.sum(axis=1).replace(0, np.nan)
            if "gallery_museum" not in counts.columns:
                counts["gallery_museum"] = 0
            ratios = (counts["gallery_museum"] / total).rename("source_group_gallery_museum_ratio").reset_index()
            snapshot = snapshot.drop(columns=["source_group_gallery_museum_ratio"], errors="ignore").merge(
                ratios,
                on="artist_search_name",
                how="left",
            )
    needed = [
        "artist_search_name",
        "search_quality_score",
        "source_group_gallery_museum_ratio",
        "search_collected_flag",
    ]
    for col in needed:
        if col not in snapshot.columns:
            snapshot[col] = np.nan
    return snapshot[needed].drop_duplicates("artist_search_name", keep="last")


def attach_search(frame: pd.DataFrame, search: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["artist_search_name"] = out["artist_name_ko"].map(clean_artist_name)
    out = out.merge(search, on="artist_search_name", how="left")
    out["has_search_feature"] = out["search_quality_score"].notna()
    out["source_group_gallery_museum_ratio"] = pd.to_numeric(out["source_group_gallery_museum_ratio"], errors="coerce")
    return out


def sample_eval(pool: pd.DataFrame, rng: np.random.Generator) -> tuple[pd.Index, pd.Index]:
    counts = pool["artist_key"].astype(str).value_counts()
    eligible = counts[counts >= MIN_TRAIN_ROWS_PER_EVAL_ARTIST + 2].index.to_numpy()
    rng.shuffle(eligible)
    midpoint = len(eligible) // 2
    test_artists = eligible[:midpoint]
    val_artists = eligible[midpoint:]

    def pick_rows(artists: np.ndarray, target_rows: int) -> list[int]:
        selected: list[int] = []
        artists = artists.copy()
        rng.shuffle(artists)
        for artist in artists:
            artist_rows = pool.index[pool["artist_key"].astype(str).eq(str(artist))].to_numpy()
            max_holdout = min(3, max(0, len(artist_rows) - MIN_TRAIN_ROWS_PER_EVAL_ARTIST))
            if max_holdout <= 0:
                continue
            n = int(rng.integers(1, max_holdout + 1))
            selected.extend(rng.choice(artist_rows, size=n, replace=False).tolist())
            if len(selected) >= target_rows:
                break
        return selected[:target_rows]

    test_idx = pick_rows(test_artists, TARGET_TEST_ROWS)
    val_idx = pick_rows(val_artists, TARGET_VAL_ROWS)
    if len(test_idx) < TARGET_TEST_ROWS * 0.8 or len(val_idx) < TARGET_VAL_ROWS * 0.8:
        raise RuntimeError(f"Insufficient repeated split rows: val={len(val_idx)}, test={len(test_idx)}")
    return pd.Index(val_idx), pd.Index(test_idx)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
    actual = frame["price_krw"].to_numpy(dtype=float)
    pred = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred - actual) / np.maximum(actual, 1.0)
    ratio = pred / np.maximum(actual, 1.0)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean(np.square(pred_log - actual_log)))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "over_3x_n": int(np.sum(ratio > 3.0)),
        "under_1_3x_n": int(np.sum(ratio < 1.0 / 3.0)),
    }


def add_equal_freq_bin(train_values: pd.Series, values: pd.Series, name: str, q: int = 3) -> pd.Series:
    clean = pd.to_numeric(train_values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.nunique() < 2:
        return pd.Series(f"{name}_all", index=values.index, dtype="string")
    edges = np.unique(np.nanquantile(clean, np.linspace(0, 1, q + 1)))
    if len(edges) < 3:
        return pd.Series(f"{name}_all", index=values.index, dtype="string")
    edges[0] = -np.inf
    edges[-1] = np.inf
    labels = [f"{name}_q{i + 1}" for i in range(len(edges) - 1)]
    binned = pd.cut(pd.to_numeric(values, errors="coerce"), bins=edges, labels=labels, include_lowest=True)
    return binned.astype("string").fillna(f"{name}_missing")


def build_artist_correction(validation: pd.DataFrame, target: pd.DataFrame, min_rows: int, cap: float, shrink_k: float) -> np.ndarray:
    val = validation.copy()
    tar = target.copy()
    val["artist_meta_for_sale_works_log"] = np.log1p(pd.to_numeric(val["artist_meta_for_sale_works"], errors="coerce").clip(lower=0))
    tar["artist_meta_for_sale_works_log"] = np.log1p(pd.to_numeric(tar["artist_meta_for_sale_works"], errors="coerce").clip(lower=0))
    val["for_sale_bin"] = add_equal_freq_bin(val["artist_meta_for_sale_works_log"], val["artist_meta_for_sale_works_log"], "for_sale_bin")
    tar["for_sale_bin"] = add_equal_freq_bin(val["artist_meta_for_sale_works_log"], tar["artist_meta_for_sale_works_log"], "for_sale_bin")
    stats = val.groupby("for_sale_bin", dropna=False)["base_residual_log"].agg(["count", "median"]).reset_index()
    stats["shrink"] = stats["count"] / (stats["count"] + shrink_k)
    stats["correction"] = (stats["median"].astype(float) * stats["shrink"]).clip(lower=-cap, upper=cap)
    usable = stats[stats["count"].ge(min_rows)].copy()
    correction_map = dict(zip(usable["for_sale_bin"].astype(str), usable["correction"].astype(float), strict=False))
    return tar["for_sale_bin"].astype(str).map(correction_map).fillna(0.0).to_numpy(dtype=float)


def search_segments(validation: pd.DataFrame, target: pd.DataFrame) -> pd.Series:
    valid = validation[validation["has_search_feature"] & validation["source_group_gallery_museum_ratio"].notna()].copy()
    if valid["source_group_gallery_museum_ratio"].nunique(dropna=True) < 3:
        threshold = float(valid["source_group_gallery_museum_ratio"].median()) if len(valid) else 0.0

        def assign_binary(row: pd.Series) -> str:
            if not bool(row["has_search_feature"]) or pd.isna(row["source_group_gallery_museum_ratio"]):
                return "no_search"
            return "high" if float(row["source_group_gallery_museum_ratio"]) >= threshold else "low"

        return target.apply(assign_binary, axis=1)
    q33, q66 = valid["source_group_gallery_museum_ratio"].quantile([0.33, 0.66]).tolist()
    if not np.isfinite(q33) or not np.isfinite(q66) or q33 == q66:
        threshold = float(valid["source_group_gallery_museum_ratio"].median())

        def assign_fallback(row: pd.Series) -> str:
            if not bool(row["has_search_feature"]) or pd.isna(row["source_group_gallery_museum_ratio"]):
                return "no_search"
            return "high" if float(row["source_group_gallery_museum_ratio"]) >= threshold else "low"

        return target.apply(assign_fallback, axis=1)

    def assign_quantile(row: pd.Series) -> str:
        if not bool(row["has_search_feature"]) or pd.isna(row["source_group_gallery_museum_ratio"]):
            return "no_search"
        value = float(row["source_group_gallery_museum_ratio"])
        if value <= q33:
            return "low"
        if value <= q66:
            return "mid"
        return "high"

    return target.apply(assign_quantile, axis=1)


def build_search_correction(validation: pd.DataFrame, target: pd.DataFrame, cap: float) -> np.ndarray:
    val = validation.copy()
    tar = target.copy()
    val["search_segment"] = search_segments(val, val)
    tar["search_segment"] = search_segments(val, tar)
    rows = []
    for segment, group in val.groupby("search_segment", dropna=False):
        count = int(len(group))
        raw = float(group["base_residual_log"].median()) if segment != "no_search" and count >= 18 else 0.0
        rows.append({"search_segment": segment, "correction": float(np.clip(raw, -cap, cap))})
    correction_map = {row["search_segment"]: row["correction"] for row in rows}
    return tar["search_segment"].astype(str).map(correction_map).fillna(0.0).to_numpy(dtype=float)


def prediction_rows(iteration: int, split: str, frame: pd.DataFrame, candidate: str, pred_log: np.ndarray, policy_note: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "iteration": iteration,
        "split": split,
        "candidate": candidate,
        "policy_note": policy_note,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame["artist_key"].astype(str).to_numpy(),
        "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.maximum(out["actual_price"], 1.0)
    return out


def run_iteration(pool: pd.DataFrame, search: pd.DataFrame, iteration: int, rng: np.random.Generator) -> tuple[list[dict[str, Any]], list[pd.DataFrame], dict[str, Any]]:
    val_idx, test_idx = sample_eval(pool, rng)
    val = pool.loc[val_idx].copy()
    test = pool.loc[test_idx].copy()
    train = pool.drop(index=val_idx.union(test_idx)).copy()

    train_counts = train["artist_key"].astype(str).value_counts()
    val_min_train = int(val["artist_key"].astype(str).map(train_counts).min())
    test_min_train = int(test["artist_key"].astype(str).map(train_counts).min())

    train = normalize(train, BASE_FEATURES)
    val = normalize(val, BASE_FEATURES)
    test = normalize(test, BASE_FEATURES)
    val = attach_search(val, search)
    test = attach_search(test, search)

    model = huber_model(BASE_FEATURES)
    model.fit(train[BASE_FEATURES], train["ln_price_krw"].to_numpy(dtype=float))
    val_base = np.asarray(model.predict(val[BASE_FEATURES]), dtype=float)
    test_base = np.asarray(model.predict(test[BASE_FEATURES]), dtype=float)
    val["base_pred_log"] = val_base
    test["base_pred_log"] = test_base
    val["base_residual_log"] = val["ln_price_krw"].to_numpy(dtype=float) - val_base

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    for split_name, frame, pred in [("validation", val, val_base), ("test", test, test_base)]:
        metric_rows.append({
            "experiment_id": EXP_ID,
            "iteration": iteration,
            "split": split_name,
            "candidate": "baseline_warm_huber",
            "policy_note": "split마다 재학습한 Warm Huber 기준선",
            **metric_values(frame, pred),
        })
        pred_frames.append(prediction_rows(iteration, split_name, frame, "baseline_warm_huber", pred, "split마다 재학습한 Warm Huber 기준선"))

    for policy in POLICIES:
        for split_name, target, base_pred in [("validation", val, val_base), ("test", test, test_base)]:
            artist_corr = build_artist_correction(
                val,
                target,
                min_rows=int(policy["artist_min_rows"]),
                cap=float(policy["artist_cap"]),
                shrink_k=float(policy["artist_shrink_k"]),
            )
            search_corr = build_search_correction(val, target, cap=float(policy["search_cap"]))
            total_corr = np.clip(
                float(policy["artist_weight"]) * artist_corr + float(policy["search_weight"]) * search_corr,
                -float(policy["total_cap"]),
                float(policy["total_cap"]),
            )
            pred = base_pred + total_corr
            metric_rows.append({
                "experiment_id": EXP_ID,
                "iteration": iteration,
                "split": split_name,
                "candidate": str(policy["candidate"]),
                "policy_note": str(policy["note"]),
                "mean_abs_correction": float(np.mean(np.abs(total_corr))),
                "max_abs_correction": float(np.max(np.abs(total_corr))),
                **metric_values(target, pred),
            })
            pred_frames.append(prediction_rows(iteration, split_name, target, str(policy["candidate"]), pred, str(policy["note"])))

    split_row = {
        "iteration": iteration,
        "train_n": int(len(train)),
        "validation_n": int(len(val)),
        "test_n": int(len(test)),
        "train_artist_n": int(train["artist_key"].nunique()),
        "validation_artist_n": int(val["artist_key"].nunique()),
        "test_artist_n": int(test["artist_key"].nunique()),
        "validation_min_train_rows_per_artist": val_min_train,
        "test_min_train_rows_per_artist": test_min_train,
        "validation_search_coverage": float(val["has_search_feature"].mean()),
        "test_search_coverage": float(test["has_search_feature"].mean()),
    }
    return metric_rows, pred_frames, split_row


def add_deltas(metrics: pd.DataFrame) -> pd.DataFrame:
    out = metrics.copy()
    baseline = out[out["candidate"].eq("baseline_warm_huber")][
        ["iteration", "split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(columns={
        "MdAPE": "baseline_MdAPE",
        "MAPE": "baseline_MAPE",
        "p95_APE": "baseline_p95_APE",
        "RMSE_log": "baseline_RMSE_log",
    })
    out = out.merge(baseline, on=["iteration", "split"], how="left")
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"improvement_{metric}"] = out[f"baseline_{metric}"] - out[metric]
    return out


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidates = metrics[~metrics["candidate"].eq("baseline_warm_huber")].copy()
    for (split, candidate), group in candidates.groupby(["split", "candidate"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "split": split,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
            "MdAPE_mean": float(group["MdAPE"].mean()),
            "MAPE_mean": float(group["MAPE"].mean()),
            "p95_APE_mean": float(group["p95_APE"].mean()),
            "RMSE_log_mean": float(group["RMSE_log"].mean()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"improvement_{metric}"].astype(float).to_numpy()
            row[f"improvement_{metric}_mean"] = float(np.mean(values))
            row[f"improvement_{metric}_median"] = float(np.median(values))
            row[f"improvement_{metric}_prob"] = float(np.mean(values > 0))
            row[f"improvement_{metric}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"improvement_{metric}_ci_high"] = float(np.quantile(values, 0.975))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["split", "improvement_MAPE_mean", "improvement_MdAPE_mean"], ascending=[True, False, False])


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_결과 없음_"
    view = df.head(max_rows).copy() if max_rows else df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.6f}")
        else:
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else str(x).replace("\n", " "))
    lines = [
        "| " + " | ".join(view.columns.astype(str)) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def render_html(title: str, summary_text: str, tables: dict[str, pd.DataFrame]) -> str:
    body = [
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937;line-height:1.55}"
        "table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0 28px}th,td{border:1px solid #d8dee9;padding:7px 8px;text-align:right}"
        "th:first-child,td:first-child{text-align:left}th{background:#eef2f7}.note{white-space:pre-wrap;background:#f8fafc;border-left:4px solid #2563eb;padding:12px 14px}</style>",
        "</head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f"<div class='note'>{html.escape(summary_text)}</div>",
    ]
    for name, table in tables.items():
        body.append(f"<h2>{html.escape(name)}</h2>")
        body.append(table.to_html(index=False, escape=True, float_format=lambda value: f"{value:.6f}"))
    body.append("</body></html>")
    return "\n".join(body)


def main() -> None:
    ensure_dirs()
    pool = load_pool()
    search = load_search_features()
    rng = np.random.default_rng(SEED)
    all_metrics: list[dict[str, Any]] = []
    all_predictions: list[pd.DataFrame] = []
    split_rows: list[dict[str, Any]] = []
    for iteration in range(ITERATIONS):
        metric_rows, pred_frames, split_row = run_iteration(pool, search, iteration, rng)
        all_metrics.extend(metric_rows)
        if iteration < 3:
            all_predictions.extend(pred_frames)
        split_rows.append(split_row)

    metrics_df = add_deltas(pd.DataFrame(all_metrics))
    summary_df = summarize(metrics_df)
    split_df = pd.DataFrame(split_rows)
    predictions_df = pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()

    metrics_df.to_csv(OUT_DIR / "metrics_by_iteration.csv", index=False)
    summary_df.to_csv(OUT_DIR / "summary_by_candidate.csv", index=False)
    split_df.to_csv(OUT_DIR / "split_diagnostics.csv", index=False)
    predictions_df.to_csv(OUT_DIR / "prediction_samples_first3_iterations.csv", index=False)

    test_summary = summary_df[summary_df["split"].eq("test")].copy()
    val_summary = summary_df[summary_df["split"].eq("validation")].copy()
    best_test = test_summary.sort_values(["improvement_MAPE_mean", "improvement_MdAPE_mean"], ascending=[False, False]).iloc[0]
    summary_text = "\n".join([
        "- 목적: Warm Huber를 반복 split마다 재학습하고 작가 메타/검색 보정값도 매번 다시 계산",
        f"- 반복 수: {ITERATIONS}",
        "- 기준선: 반복 split별 Warm Huber",
        "- 보정 후보: 작가 판매중 작품 수 구간, 갤러리/미술관 검색 출처 비중, 두 보정 결합",
        "- 한계: PP-V8 compact blend 전체를 새 split마다 재현한 것은 아님",
        "",
        "핵심 test 결과:",
        f"- test 평균 MAPE 개선 최선: {best_test['candidate']}",
        f"- MAPE 평균 개선 {best_test['improvement_MAPE_mean']:.6f}, 개선확률 {best_test['improvement_MAPE_prob']:.3f}",
        f"- MdAPE 평균 개선 {best_test['improvement_MdAPE_mean']:.6f}, 개선확률 {best_test['improvement_MdAPE_prob']:.3f}",
        f"- p95 평균 개선 {best_test['improvement_p95_APE_mean']:.6f}, 개선확률 {best_test['improvement_p95_APE_prob']:.3f}",
        "",
        "판단:",
        "- 반복 split에서도 개선확률이 높으면 보정 신호가 특정 고정 test 우연일 가능성이 낮아진다.",
        "- PP-V8 최종 반영 전에는 PP-V8 원천 후보의 source-decomposed 재현이 추가로 필요하다.",
    ])

    report = f"""# PP-AMW4 Warm 반복 split 잔차 보정 재학습 검증

## 1. 실행 요약

{summary_text}

## 2. test 요약

{markdown_table(test_summary)}

## 3. validation 요약

{markdown_table(val_summary)}

## 4. split 진단

{markdown_table(split_df.describe(include="all").reset_index())}

## 5. iteration별 지표 샘플

{markdown_table(metrics_df.head(80))}

## 6. 산출물

- `outputs/metrics_by_iteration.csv`
- `outputs/summary_by_candidate.csv`
- `outputs/split_diagnostics.csv`
- `outputs/prediction_samples_first3_iterations.csv`
- `reports/result_report.md`
- `reports/result_report.html`
"""
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(
        render_html(
            "PP-AMW4 Warm 반복 split 잔차 보정 재학습 검증",
            summary_text,
            {
                "test 요약": test_summary,
                "validation 요약": val_summary,
                "split 진단": split_df.describe(include="all").reset_index(),
                "iteration별 지표 샘플": metrics_df.head(80),
            },
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps({
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "iterations": ITERATIONS,
        "baseline": "Warm Huber retrained per repeated split",
        "base_features": BASE_FEATURES,
        "policies": POLICIES,
        "pool_files": [str(path.relative_to(REPO)) for path in POOL_FILES],
        "search_snapshot_path": str(SEARCH_SNAPSHOT_PATH.relative_to(REPO)),
        "search_standardized_path": str(SEARCH_STANDARDIZED_PATH.relative_to(REPO)),
        "limitation": "Not exact PP-V8 source-decomposed repeated retraining.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "experiment_id": EXP_ID,
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "best_test": best_test.to_dict(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
