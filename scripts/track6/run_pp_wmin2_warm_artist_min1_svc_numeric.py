#!/usr/bin/env python3
"""Run PP-WMIN2 Warm artist-ladder min_n=1 operational SVC check.

This experiment keeps the PP-SVC2 Warm svc_numeric pipeline shape, but changes
only the artist-containing comparable-stat ladder from min_n=5 to min_n=1.
Train features are cross-fitted by fold so a row never uses its own target
price. If a fold-excluded source table has no matching artist row, the ladder
falls through to the next level.
"""
from __future__ import annotations

import copy
import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WMIN2"
EXP_SLUG = "PP-WMIN2_warm_artist_min1_svc_numeric"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 작가 ladder 최소 표본 1건 운영형 SVC 검증"
SEEDS = list(range(202606030, 202606040))
BOOTSTRAP_ITERATIONS = 500
ARTIST_MIN_N_CURRENT = 5
ARTIST_MIN_N_CANDIDATE = 1
SOURCE_PREDICTIONS = EXP_ROOT / "PP-SVC2_warm_comparable_stats_stability" / "outputs" / "predictions.csv"
CURRENT_SVC = "current_svc_numeric_seed_mean_min5"
NEW_SVC = "wmin2_svc_numeric_seed_mean_min1"
PPV8 = "pp_v8_compact_blend_mape_guarded"
CURRENT_BLEND = "current_70_30_min5_svc_ppv8"
NEW_BLEND = "wmin2_70_30_min1_svc_ppv8"


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def group_defs_for_artist_min(min_n: int) -> list[dict[str, Any]]:
    group_defs = copy.deepcopy(svc1.GROUP_DEFS)
    for group_def in group_defs:
        if "artist_key" in group_def["keys"]:
            group_def["min_n"] = min_n
            group_def["wmin2_change"] = f"artist-containing ladder min_n {ARTIST_MIN_N_CURRENT}->{min_n}"
    return group_defs


def apply_comparable_stats_with_defs(
    source: pd.DataFrame,
    target: pd.DataFrame,
    group_defs: list[dict[str, Any]],
) -> pd.DataFrame:
    source_ready = svc1.comparable_ready(source)
    target_ready = svc1.comparable_ready(target)
    result = target_ready[["_track6_row_id"]].copy()
    for col in svc1.SVC_NUMERIC:
        result[col] = np.nan
    for col in svc1.SVC_CATEGORICAL:
        result[col] = "__UNASSIGNED__"
    result["svc_group_n"] = np.nan

    assigned = np.zeros(len(result), dtype=bool)
    stat_cols = [
        "svc_group_log_price_median",
        "svc_group_log_price_q25",
        "svc_group_log_price_q75",
        "svc_group_log_price_iqr",
        "svc_group_log_unit_area_median",
        "svc_group_log_unit_area_iqr",
        "svc_group_n",
    ]
    for group_def in group_defs:
        keys = group_def["keys"]
        stats = svc1.aggregate_stats(source_ready, keys)
        merged = target_ready[keys].merge(stats, on=keys, how="left")
        counts = pd.to_numeric(merged["svc_group_n"], errors="coerce").fillna(0)
        eligible = (~assigned) & (counts >= int(group_def["min_n"])).to_numpy()
        if not eligible.any():
            continue
        for col in stat_cols:
            result.loc[eligible, col] = merged.loc[eligible, col].to_numpy()
        result.loc[eligible, "svc_group_level"] = group_def["level"]
        result.loc[eligible, "svc_has_artist_level"] = str("artist_key" in keys)
        assigned |= eligible

    if (~assigned).any():
        global_stats = svc1.aggregate_stats(source_ready, [])
        for col in stat_cols:
            result.loc[~assigned, col] = global_stats.iloc[0][col]
        result.loc[~assigned, "svc_group_level"] = "global"
        result.loc[~assigned, "svc_has_artist_level"] = "False"

    result["svc_group_n_log"] = np.log1p(pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0))
    result["svc_coverage_tier"] = [
        svc1.coverage_tier(str(level), float(n))
        for level, n in zip(result["svc_group_level"], pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0))
    ]
    result["svc_has_artist_level"] = result["svc_has_artist_level"].astype(str)
    return result[["_track6_row_id", *svc1.SVC_NUMERIC, *svc1.SVC_CATEGORICAL, "svc_group_n"]]


def key_counts(source_ready: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return source_ready.groupby(keys, dropna=False, observed=False).size().reset_index(name="n")


def audit_fold(
    full_ready: pd.DataFrame,
    source_ready: pd.DataFrame,
    target_ready: pd.DataFrame,
    assigned_stats: pd.DataFrame,
    group_defs: list[dict[str, Any]],
    seed: int,
    fold: int,
) -> list[dict[str, Any]]:
    source_ids = set(pd.to_numeric(source_ready["_track6_row_id"], errors="coerce").dropna().astype(int).tolist())
    target_ids = set(pd.to_numeric(target_ready["_track6_row_id"], errors="coerce").dropna().astype(int).tolist())
    rows: list[dict[str, Any]] = [{
        "seed": seed,
        "fold": fold,
        "audit_type": "fold_overlap",
        "level": "__fold__",
        "keys": "",
        "target_rows": int(len(target_ready)),
        "source_rows": int(len(source_ready)),
        "full_train_rows": int(len(full_ready)),
        "source_target_overlap_count": int(len(source_ids & target_ids)),
        "full_count_ge_min_rows": np.nan,
        "source_count_ge_min_rows": np.nan,
        "source_zero_after_fold_exclusion_rows": np.nan,
        "assigned_level_rows": np.nan,
        "self_leakage_violations": int(len(source_ids & target_ids)),
    }]
    assigned = assigned_stats[["_track6_row_id", "svc_group_level"]].copy()
    for group_def in group_defs:
        if "artist_key" not in group_def["keys"]:
            continue
        keys = group_def["keys"]
        min_n = int(group_def["min_n"])
        full_counts = key_counts(full_ready, keys).rename(columns={"n": "full_n"})
        source_counts = key_counts(source_ready, keys).rename(columns={"n": "source_n"})
        merged = (
            target_ready[["_track6_row_id", *keys]]
            .merge(full_counts, on=keys, how="left")
            .merge(source_counts, on=keys, how="left")
            .merge(assigned, on="_track6_row_id", how="left")
        )
        full_n = pd.to_numeric(merged["full_n"], errors="coerce").fillna(0)
        source_n = pd.to_numeric(merged["source_n"], errors="coerce").fillna(0)
        rows.append({
            "seed": seed,
            "fold": fold,
            "audit_type": "artist_ladder_level",
            "level": group_def["level"],
            "keys": "+".join(keys),
            "target_rows": int(len(target_ready)),
            "source_rows": int(len(source_ready)),
            "full_train_rows": int(len(full_ready)),
            "source_target_overlap_count": 0,
            "full_count_ge_min_rows": int((full_n >= min_n).sum()),
            "source_count_ge_min_rows": int((source_n >= min_n).sum()),
            "source_zero_after_fold_exclusion_rows": int(((full_n >= 1) & (source_n == 0)).sum()),
            "assigned_level_rows": int(merged["svc_group_level"].astype(str).eq(group_def["level"]).sum()),
            "self_leakage_violations": 0,
        })
    return rows


def crossfit_train_stats(
    train: pd.DataFrame,
    seed: int,
    group_defs: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    full_ready = svc1.comparable_ready(train)
    parts: list[pd.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    for fold, (source_idx, holdout_idx) in enumerate(kfold.split(train)):
        source = train.iloc[source_idx].copy()
        target = train.iloc[holdout_idx].copy()
        stats = apply_comparable_stats_with_defs(source, target, group_defs)
        parts.append(stats)
        audit_rows.extend(
            audit_fold(
                full_ready,
                svc1.comparable_ready(source),
                svc1.comparable_ready(target),
                stats,
                group_defs,
                seed,
                fold,
            )
        )
    return pd.concat(parts, ignore_index=True), pd.DataFrame(audit_rows)


def add_service_features_seed(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    seed: int,
    group_defs: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats, audit = crossfit_train_stats(train, seed, group_defs)
    val_stats = apply_comparable_stats_with_defs(train, val, group_defs)
    test_stats = apply_comparable_stats_with_defs(train, test, group_defs)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
        audit,
    )


def prediction_rows(
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    seed: int | None,
    base_candidate: str,
    source: str,
) -> pd.DataFrame:
    out = svc1.prediction_frame(EXP_ID, candidate, "warm", split, frame, pred_log)
    out["seed"] = seed
    out["base_candidate"] = base_candidate
    out["source"] = source
    return out


def load_warm_meta() -> pd.DataFrame:
    frames = []
    for split, filename in [("validation", "track6_val_warm.csv"), ("test", "track6_test_warm.csv")]:
        df = pd.read_csv(REPO / "data" / "track6_split" / filename, low_memory=False)
        keep = [
            col
            for col in ["_track6_row_id", "artist_key", "artist_name_ko", "artist_works_count_train"]
            if col in df.columns
        ]
        part = df[keep].drop_duplicates("_track6_row_id").copy()
        part["split"] = split
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def make_seed_mean(pred_df: pd.DataFrame, frame_by_split: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    seeds = pred_df[pred_df["base_candidate"].eq("wmin2_svc_numeric")].copy()
    for split, group in seeds.groupby("split", dropna=False):
        pivot = group.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last")
        mean_pred = pivot.mean(axis=1).rename("pred_log").reset_index()
        frame = frame_by_split[str(split)].merge(mean_pred, on="_track6_row_id", how="inner")
        rows.append(
            prediction_rows(
                NEW_SVC,
                str(split),
                frame,
                frame["pred_log"].to_numpy(dtype=float),
                None,
                "wmin2_svc_numeric",
                "seed_mean",
            )
        )
    return pd.concat(rows, ignore_index=True)


def load_current_reference_predictions() -> pd.DataFrame:
    if not SOURCE_PREDICTIONS.exists():
        raise FileNotFoundError(f"Missing source predictions: {SOURCE_PREDICTIONS}")
    df = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    df = df[
        df["split"].astype(str).isin(["validation", "test"])
        & df["candidate"].astype(str).isin(["svc_numeric_seed_mean", PPV8])
    ].copy()
    rename = {"svc_numeric_seed_mean": CURRENT_SVC}
    df["candidate"] = df["candidate"].replace(rename)
    df["experiment_id"] = EXP_ID
    df["base_candidate"] = df["candidate"]
    df["source"] = np.where(df["candidate"].eq(CURRENT_SVC), "PP-SVC2_current_min5", "PP-V8_reference")
    keep = [
        "experiment_id",
        "candidate",
        "scope",
        "split",
        "_track6_row_id",
        "actual_log",
        "pred_log",
        "actual_price",
        "pred_price",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
        "residual_log",
        "ape",
        "seed",
        "base_candidate",
        "source",
    ]
    return df[[col for col in keep if col in df.columns]].copy()


def add_blend_predictions(long_df: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["split", "_track6_row_id", "actual_log", "actual_price"]
    base = long_df[base_cols].drop_duplicates(["split", "_track6_row_id"]).copy()
    meta_cols = ["split", "_track6_row_id", "svc_group_level", "svc_coverage_tier", "svc_group_n"]
    meta = (
        long_df[meta_cols]
        .replace({"": np.nan})
        .dropna(subset=["svc_group_level"])
        .drop_duplicates(["split", "_track6_row_id"])
    )
    wide = long_df.pivot_table(
        index=["split", "_track6_row_id"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    wide.columns.name = None
    needed = [CURRENT_SVC, NEW_SVC, PPV8]
    missing = [col for col in needed if col not in wide.columns]
    if missing:
        raise ValueError(f"Missing predictions for blend: {missing}")
    frame = base.merge(meta, on=["split", "_track6_row_id"], how="left").merge(wide, on=["split", "_track6_row_id"], how="inner")
    rows: list[pd.DataFrame] = []
    for candidate, svc_col in [(CURRENT_BLEND, CURRENT_SVC), (NEW_BLEND, NEW_SVC)]:
        pred_log = 0.70 * frame[svc_col].to_numpy(dtype=float) + 0.30 * frame[PPV8].to_numpy(dtype=float)
        part = pd.DataFrame({
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "scope": "warm",
            "split": frame["split"],
            "_track6_row_id": frame["_track6_row_id"],
            "actual_log": frame["actual_log"],
            "pred_log": pred_log,
            "actual_price": frame["actual_price"],
            "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
            "svc_group_level": frame.get("svc_group_level", pd.Series([""] * len(frame))),
            "svc_coverage_tier": frame.get("svc_coverage_tier", pd.Series([""] * len(frame))),
            "svc_group_n": frame.get("svc_group_n", pd.Series([np.nan] * len(frame))),
            "seed": np.nan,
            "base_candidate": candidate,
            "source": "computed_70_30",
        })
        part["residual_log"] = part["actual_log"] - part["pred_log"]
        part["ape"] = np.abs(part["pred_price"] - part["actual_price"]) / np.clip(part["actual_price"], 1.0, None)
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def metric_from_group(group: pd.DataFrame) -> dict[str, float]:
    pred_log = group["pred_log"].to_numpy(dtype=float)
    actual_log = group["actual_log"].to_numpy(dtype=float)
    actual_price = group["actual_price"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(group)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def build_metrics(long_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (candidate, split), group in long_df.groupby(["candidate", "split"], dropna=False):
        if str(split) not in {"validation", "test"}:
            continue
        rows.append({
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "split": split,
            "scope": "warm",
            "source": str(group["source"].iloc[0]) if "source" in group.columns else "",
            **metric_from_group(group),
        })
    order = ["split", "MdAPE", "MAPE", "p95_APE", "candidate"]
    return pd.DataFrame(rows).sort_values(order).reset_index(drop=True)


def bootstrap_compare(long_df: pd.DataFrame, baseline: str, candidate: str) -> pd.DataFrame:
    validation = long_df[long_df["split"].eq("validation")].copy()
    base = validation[["split", "_track6_row_id", "actual_log", "actual_price", "artist_key"]].drop_duplicates(["split", "_track6_row_id"])
    wide = validation.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="last").reset_index()
    data = base.merge(wide, on="_track6_row_id", how="inner").dropna(subset=[baseline, candidate])
    rng = np.random.default_rng(20260612)
    row_indices = np.arange(len(data))
    artist_keys = data["artist_key"].fillna("__MISSING__").astype(str).to_numpy()
    unique_artists = np.unique(artist_keys)
    artist_to_indices = {artist: np.flatnonzero(artist_keys == artist) for artist in unique_artists}
    rows: list[dict[str, Any]] = []
    for iteration in range(BOOTSTRAP_ITERATIONS):
        row_sample = rng.choice(row_indices, size=len(row_indices), replace=True)
        artist_sample_keys = rng.choice(unique_artists, size=len(unique_artists), replace=True)
        artist_sample = np.concatenate([artist_to_indices[artist] for artist in artist_sample_keys])
        for mode, indices in [("row_bootstrap", row_sample), ("artist_bootstrap", artist_sample)]:
            sample = data.iloc[indices].copy()
            base_metrics = metric_from_group(sample.rename(columns={baseline: "pred_log"})[["actual_log", "actual_price", "pred_log"]])
            cand_metrics = metric_from_group(sample.rename(columns={candidate: "pred_log"})[["actual_log", "actual_price", "pred_log"]])
            row: dict[str, Any] = {
                "experiment_id": EXP_ID,
                "baseline": baseline,
                "candidate": candidate,
                "split": "validation",
                "bootstrap_mode": mode,
                "iteration": iteration,
                "n": int(len(sample)),
            }
            for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[f"baseline_{metric}"] = base_metrics[metric]
                row[f"candidate_{metric}"] = cand_metrics[metric]
                row[f"delta_{metric}"] = base_metrics[metric] - cand_metrics[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def summarize_bootstrap(samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (baseline, candidate, mode), group in samples.groupby(["baseline", "candidate", "bootstrap_mode"], dropna=False):
        row: dict[str, Any] = {
            "experiment_id": EXP_ID,
            "split": "validation",
            "baseline": baseline,
            "candidate": candidate,
            "bootstrap_mode": mode,
            "iterations": int(group["iteration"].nunique()),
            "median_n": float(group["n"].median()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = group[f"delta_{metric}"].astype(float).to_numpy()
            row[f"delta_{metric}_median"] = float(np.median(values))
            row[f"delta_{metric}_ci_low"] = float(np.quantile(values, 0.025))
            row[f"delta_{metric}_ci_high"] = float(np.quantile(values, 0.975))
            row[f"delta_{metric}_prob_improve"] = float(np.mean(values > 0))
        rows.append(row)
    return pd.DataFrame(rows)


def coverage_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, frame in frames.items():
        for col in ["svc_group_level", "svc_coverage_tier"]:
            for value, group in frame.groupby(col, dropna=False):
                rows.append({
                    "experiment_id": EXP_ID,
                    "split": split,
                    "column": col,
                    "value": value,
                    "rows": int(len(group)),
                    "share": float(len(group) / len(frame)),
                    "median_group_n": float(pd.to_numeric(group["svc_group_n"], errors="coerce").median()),
                })
    return pd.DataFrame(rows)


def render_report(
    metrics: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    leakage_audit: pd.DataFrame,
    coverage: pd.DataFrame,
) -> tuple[str, str]:
    validation = metrics[metrics["split"].eq("validation")].copy()
    test = metrics[metrics["split"].eq("test")].copy()
    val_lookup = validation.set_index("candidate")
    test_lookup = test.set_index("candidate")

    def delta_text(base: str, cand: str, split_lookup: pd.DataFrame) -> str:
        if base not in split_lookup.index or cand not in split_lookup.index:
            return "-"
        b = split_lookup.loc[base]
        c = split_lookup.loc[cand]
        return (
            f"MdAPE {b.MdAPE - c.MdAPE:+.4f}, "
            f"MAPE {b.MAPE - c.MAPE:+.4f}, "
            f"p95 {b.p95_APE - c.p95_APE:+.4f}"
        )

    overlap = leakage_audit["self_leakage_violations"].fillna(0).astype(int).sum() if not leakage_audit.empty else 0
    zero_rows = (
        leakage_audit[leakage_audit["audit_type"].eq("artist_ladder_level")]
        .groupby("level", dropna=False)["source_zero_after_fold_exclusion_rows"]
        .sum()
        .reset_index()
        if not leakage_audit.empty
        else pd.DataFrame()
    )
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: Warm SVC의 작가 포함 비교군 ladder 최소 표본을 5건에서 1건으로 낮췄을 때 운영형 70:30 기준가까지 개선되는지 확인한다.",
        "- 변경점: `artist_key`가 포함된 ladder(`artist_medium_support_size`, `artist_size`, `artist`)의 `min_n`만 1로 변경한다.",
        "- 유지점: 기본 Warm 피처, Huber 학습 방식, SVC numeric 피처, PP-V8 참조 후보, 70:30 결합식은 기존 PP-SVC2/PP-SVC3와 동일하게 둔다.",
        "- 검증 원칙: validation과 train OOF audit로 판단하고, fixed test는 최종 확인용으로만 기록한다.",
        "",
        "## 1. Validation 판단",
        "",
        "| 비교 | 변화량(기존-후보, 양수면 개선) |",
        "|---|---:|",
        f"| SVC 단독 `{CURRENT_SVC}` → `{NEW_SVC}` | {delta_text(CURRENT_SVC, NEW_SVC, val_lookup)} |",
        f"| 70:30 `{CURRENT_BLEND}` → `{NEW_BLEND}` | {delta_text(CURRENT_BLEND, NEW_BLEND, val_lookup)} |",
        "",
        "## 2. Fixed Test 확인",
        "",
        "| 비교 | 변화량(기존-후보, 양수면 개선) |",
        "|---|---:|",
        f"| SVC 단독 `{CURRENT_SVC}` → `{NEW_SVC}` | {delta_text(CURRENT_SVC, NEW_SVC, test_lookup)} |",
        f"| 70:30 `{CURRENT_BLEND}` → `{NEW_BLEND}` | {delta_text(CURRENT_BLEND, NEW_BLEND, test_lookup)} |",
        "",
        "## 3. 전체 지표",
        "",
        "| split | 후보 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in metrics.sort_values(["split", "MdAPE", "MAPE", "p95_APE"]).itertuples():
        lines.append(
            f"| {row.split} | `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += [
        "",
        "## 4. Validation bootstrap",
        "",
        "| baseline | 후보 | mode | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | MdAPE delta 중앙값 |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in bootstrap_summary.itertuples():
        lines.append(
            f"| `{row.baseline}` | `{row.candidate}` | {row.bootstrap_mode} | "
            f"{row.delta_MdAPE_prob_improve:.3f} | {row.delta_MAPE_prob_improve:.3f} | "
            f"{row.delta_p95_APE_prob_improve:.3f} | {row.delta_MdAPE_median:.4f} |"
        )
    lines += [
        "",
        "## 5. 누수 방어 audit",
        "",
        f"- source/holdout row id 중복 합계: `{overlap}`",
        "- train 피처는 5-fold cross-fit으로 생성되므로 holdout row의 가격은 해당 row의 비교군 통계 계산에 들어가지 않는다.",
        "- fold 제외 후 작가 포함 ladder의 source count가 0이면 다음 ladder로 fallback한다.",
        "",
        "| artist ladder level | fold 제외 후 source 0건 fallback 필요 row 합계 |",
        "|---|---:|",
    ]
    if zero_rows.empty:
        lines.append("| - | 0 |")
    else:
        for row in zero_rows.itertuples():
            lines.append(f"| `{row.level}` | {int(row.source_zero_after_fold_exclusion_rows)} |")
    lines += [
        "",
        "## 6. Coverage",
        "",
        "| split | column | value | rows | share | median group N |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in coverage.itertuples():
        lines.append(
            f"| {row.split} | {row.column} | `{row.value}` | {row.rows} | {row.share:.3f} | {row.median_group_n:.1f} |"
        )
    lines += [
        "",
        "## 7. 다음 판단",
        "",
        "- validation에서 SVC 단독과 70:30 모두 개선되고 bootstrap 개선확률이 높으면 PP-WMIN3에서 기존 보정 stack과 결합해 확인한다.",
        "- SVC 단독은 개선되지만 70:30에서 사라지면 PP-V8과의 결합 비율 또는 보정 stack에서 신호가 희석되는지 분해한다.",
        "- validation에서 불안정하면 fixed test 개선이 있어도 채택하지 않고 slice별 원인을 분해한다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}.note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px;margin:12px 0}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">artist-containing ladder min_n=1, train cross-fit leakage audit included. Fixed test is confirmation only.</div>
<h2>Metrics</h2>{metrics.to_html(index=False, escape=True)}
<h2>Validation Bootstrap Summary</h2>{bootstrap_summary.to_html(index=False, escape=True)}
<h2>Leakage Audit</h2>{leakage_audit.to_html(index=False, escape=True)}
<h2>Coverage</h2>{coverage.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    ensure_dirs()
    group_defs = group_defs_for_artist_min(ARTIST_MIN_N_CANDIDATE)
    base_features = artifact_features()["warm"]
    requested = list(dict.fromkeys([*base_features, *svc1.GROUPING_FEATURES]))
    train_base, val_base, test_base = load_scope("warm", requested)
    svc_numeric_features = list(dict.fromkeys([*base_features, *svc1.SVC_NUMERIC]))

    predictions: list[pd.DataFrame] = []
    audit_rows: list[pd.DataFrame] = []
    frame_by_split: dict[str, pd.DataFrame] = {}
    coverage_frames: dict[str, pd.DataFrame] = {}

    for seed in SEEDS:
        train_s, val_s, test_s, audit = add_service_features_seed(train_base, val_base, test_base, seed, group_defs)
        audit_rows.append(audit)
        if seed == SEEDS[0]:
            frame_by_split = {"validation": val_s, "test": test_s}
            coverage_frames = {"train_oof_seed0": train_s, "validation": val_s, "test": test_s}
        train_n = svc1.normalize(train_s, svc_numeric_features)
        val_n = svc1.normalize(val_s, svc_numeric_features)
        test_n = svc1.normalize(test_s, svc_numeric_features)
        pred = svc1.fit_predict("huber", train_n, val_n, test_n, svc_numeric_features)
        for split, frame, pred_log in [("validation", val_n, pred["validation"]), ("test", test_n, pred["test"])]:
            predictions.append(
                prediction_rows(
                    f"wmin2_svc_numeric_seed_{seed}",
                    split,
                    frame,
                    pred_log,
                    seed,
                    "wmin2_svc_numeric",
                    "PP-WMIN2_seed_repeat",
                )
            )

    min1_seed_pred = pd.concat(predictions, ignore_index=True)
    min1_mean_pred = make_seed_mean(min1_seed_pred, frame_by_split)
    reference_pred = load_current_reference_predictions()
    combined = pd.concat([min1_seed_pred, min1_mean_pred, reference_pred], ignore_index=True)
    blend_pred = add_blend_predictions(combined)
    combined = pd.concat([combined, blend_pred], ignore_index=True)

    meta = load_warm_meta()
    combined = combined.merge(meta, on=["split", "_track6_row_id"], how="left", suffixes=("", "_meta"))
    for col in ["artist_key", "artist_name_ko", "artist_works_count_train"]:
        meta_col = f"{col}_meta"
        if meta_col in combined.columns:
            combined[col] = combined[col].fillna(combined[meta_col]) if col in combined.columns else combined[meta_col]
            combined = combined.drop(columns=[meta_col])

    metrics = build_metrics(
        combined[
            combined["candidate"].isin([CURRENT_SVC, NEW_SVC, PPV8, CURRENT_BLEND, NEW_BLEND])
        ].copy()
    )
    bootstrap_samples = pd.concat(
        [
            bootstrap_compare(combined, CURRENT_SVC, NEW_SVC),
            bootstrap_compare(combined, CURRENT_BLEND, NEW_BLEND),
        ],
        ignore_index=True,
    )
    bootstrap_summary = summarize_bootstrap(bootstrap_samples)
    leakage_audit = pd.concat(audit_rows, ignore_index=True)
    coverage = coverage_summary(coverage_frames)

    combined.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "validation_bootstrap_samples.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "validation_bootstrap_summary.csv", index=False)
    leakage_audit.to_csv(EXP_DIR / "outputs" / "leakage_audit.csv", index=False)
    coverage.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    pd.concat(
        [
            frame.assign(split=split)[
                ["split", "_track6_row_id", *svc1.SVC_NUMERIC, *svc1.SVC_CATEGORICAL, "svc_group_n"]
            ]
            for split, frame in coverage_frames.items()
        ],
        ignore_index=True,
    ).to_csv(EXP_DIR / "outputs" / "comparable_features_min1.csv", index=False)

    run_config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "source_predictions": str(SOURCE_PREDICTIONS.relative_to(REPO)),
        "seeds": SEEDS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "change": {
            "current_artist_min_n": ARTIST_MIN_N_CURRENT,
            "candidate_artist_min_n": ARTIST_MIN_N_CANDIDATE,
            "changed_levels": [g["level"] for g in group_defs if "artist_key" in g["keys"]],
            "unchanged_levels": [g["level"] for g in group_defs if "artist_key" not in g["keys"]],
        },
        "leakage_control": {
            "train_features": "5-fold cross-fitted comparable stats for each seed",
            "fold_rule": "target fold rows are excluded from source stats; zero-count artist matches fall back to the next ladder level",
            "validation_test_features": "full train-only comparable stats",
            "self_overlap_audit": "source_target_overlap_count must be 0 for all folds",
        },
        "blend_formula": {
            CURRENT_BLEND: f"0.70 * {CURRENT_SVC} + 0.30 * {PPV8}",
            NEW_BLEND: f"0.70 * {NEW_SVC} + 0.30 * {PPV8}",
        },
        "feature_set": {
            "svc_numeric": svc_numeric_features,
            "svc_numeric_features": svc1.SVC_NUMERIC,
            "grouping_features": svc1.GROUPING_FEATURES,
        },
        "group_definitions": group_defs,
    }
    (EXP_DIR / "artifacts" / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "feature_manifest.json").write_text(json.dumps(run_config["feature_set"], ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "data" / "group_definitions_min1.json").write_text(json.dumps(group_defs, ensure_ascii=False, indent=2), encoding="utf-8")

    md, html_doc = render_report(metrics, bootstrap_summary, leakage_audit, coverage)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_wmin2_warm_artist_min1_svc_numeric_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")

    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_wmin2_warm_artist_min1_svc_numeric_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
