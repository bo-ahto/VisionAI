#!/usr/bin/env python3
"""PP-WLITE-Q6: exact native validation for the CF7 Warm-lite candidate.

Why this exists:
- Q3/Q4 output files do not store raw residual predictions.
- CF7 candidate uses `qavg + clip(1.00 * lgb_residual, -0.15, +0.15)`,
  so exact native Warm-lite validation requires recomputing qpred/residual.

Scopes:
1. Q1-like real low-history leave-one-out.
2. Q2-like Warm fixed-test k=1..4 truncation.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
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

import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-WLITE-Q6_cf7_candidate_native_validation"
WARM_LITE_PREDICTOR = (
    REPO / "models" / "track6" / "warm_lite_v0.1" / "predict" / "predict_warm_lite_v0_1.py"
)

Q1_SEEDS = [20260612, 20260613, 20260614]
TRUNC_SEEDS = [20260612, 20260613, 20260614]
KS = [1, 2, 3, 4]
ROWS_MIN, ROWS_MAX = 2, 5
N_BOOT = 400

CF7_STRENGTH = 1.00
CF7_CAP = 0.15

CANDIDATES = [
    "all6_current",
    "lgbq_full_lean_avg",
    "qavg_lgbres_s05_cap010_current",
    "qavg_lgbres_s10_cap015_cf7",
]


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def load_warm_lite_module():
    spec = importlib.util.spec_from_file_location("warm_lite_v0_1", WARM_LITE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Warm-lite predictor from {WARM_LITE_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fmt(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            return ""
        if abs(float(value) - round(float(value))) < 1e-9 and abs(float(value)) >= 1:
            return str(int(round(float(value))))
        return f"{float(value):.6f}"
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str], max_rows: int = 120) -> str:
    if frame.empty:
        return "_결과 없음_"
    view = frame[cols].head(max_rows).copy()
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Only first {max_rows} of {len(frame)} rows shown._")
    return "\n".join(lines)


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    pred_log = np.asarray(pred_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    pred_price = np.clip(np.exp(pred_log[valid]), 1_000.0, None)
    ape = np.abs(pred_price - actual_price[valid]) / np.clip(actual_price[valid], 1.0, None)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean((pred_log[valid] - actual_log[valid]) ** 2))),
    }


def add_candidate_predictions(out: pd.DataFrame, qpred: pd.DataFrame) -> None:
    qavg = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float)
    residual = qpred["lgb_residual"].to_numpy(dtype=float)
    out["lgbq_full_lean_avg_pred_log"] = qavg
    out["qavg_lgbres_s05_cap010_current_pred_log"] = qavg + np.clip(0.50 * residual, -0.10, 0.10)
    out["qavg_lgbres_s10_cap015_cf7_pred_log"] = qavg + np.clip(CF7_STRENGTH * residual, -CF7_CAP, CF7_CAP)
    out["lgb_residual_log"] = residual


def run_q1_seed(seed: int, train: pd.DataFrame, base_ladder: list) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = train.groupby("artist_key").size()
    low_artists = counts[(counts >= ROWS_MIN) & (counts <= ROWS_MAX)].index

    held_idx = []
    for artist in low_artists:
        idx = np.where(train["artist_key"].to_numpy() == artist)[0]
        held_idx.append(int(rng.choice(idx)))

    held = train.iloc[held_idx].reset_index(drop=True)
    tr_rest = train.drop(index=train.index[held_idx]).reset_index(drop=True)

    q3.cgrp.LADDER = q3.LITE_LADDER + base_ladder
    tr_s = q3.cgrp.train_with_internal_stats(tr_rest)
    held_s = q3.cgrp.assign_group_stats(tr_rest, held)
    q3.cgrp.LADDER = base_ladder

    stack = q3.train_stack(tr_s)
    qpred = q3.apply_stack(held_s, stack)
    huber_preds = q3.huber_component_predictions(tr_s, held_s)

    out = pd.DataFrame(
        {
            "seed": seed,
            "_row": held_idx,
            "artist_key": held["artist_key"].to_numpy(),
            "history_k": held["artist_key"].map(counts - 1).astype(int).to_numpy(),
            "actual_price": held["price_krw"].to_numpy(dtype=float),
            "actual_log": held["ln_price_krw"].to_numpy(dtype=float),
        }
    )
    out["all6_current_pred_log"] = huber_preds[[f"c{i}" for i in range(6)]].mean(axis=1).to_numpy(dtype=float)
    add_candidate_predictions(out, qpred)
    return out


def truncate_train(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep = []
    for artist, idx in train.groupby(train["artist_key"].astype(str)).indices.items():
        if artist in target_artists and len(idx) > k:
            keep.append(rng.choice(idx, size=k, replace=False))
        else:
            keep.append(idx)
    return train.iloc[np.concatenate(keep)].reset_index(drop=True)


def run_q2_condition(
    warm_lite,
    params: dict,
    huber_models: list,
    stack: dict[str, object],
    train_k: pd.DataFrame,
    test: pd.DataFrame,
    trunc_seed: int,
    k: int,
) -> pd.DataFrame:
    train_by_artist = {str(artist): group.copy() for artist, group in train_k.groupby("artist_key", sort=False)}
    parts = []
    for artist_key, group in test.groupby(test["artist_key"].astype(str), sort=False):
        artist_history = train_by_artist.get(str(artist_key))
        if artist_history is None or len(artist_history) < 1:
            raise RuntimeError(f"Missing truncated artist history for artist_key={artist_key!r}")
        fs = warm_lite.assign_stats(group.copy(), artist_history, params)
        qpred = q3.apply_stack(fs, stack)

        out = group[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
        out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
        out.insert(0, "k", k)
        out.insert(0, "trunc_seed", trunc_seed)
        out["artist_history_n"] = int(len(artist_history))

        fs_pp = q3.add_price_proxy(fs)
        huber_comp = []
        for model, cols in zip(huber_models, params["huber_num_cols"]):
            huber_comp.append(np.asarray(model.predict(fs_pp[cols + params["huber_cat_cols"]]), dtype=float))
        out["all6_current_pred_log"] = np.mean(huber_comp, axis=0)
        add_candidate_predictions(out, qpred)
        parts.append(out)
    return pd.concat(parts, ignore_index=True)


def metric_rows(preds: pd.DataFrame, group_col: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    overall_rows = []
    for candidate in CANDIDATES:
        col = f"{candidate}_pred_log"
        row = {"candidate": candidate}
        row.update(metrics(preds["actual_price"].to_numpy(dtype=float), preds["actual_log"].to_numpy(dtype=float), preds[col].to_numpy(dtype=float)))
        overall_rows.append(row)
    overall = pd.DataFrame(overall_rows)
    base = overall.loc[overall["candidate"].eq("qavg_lgbres_s05_cap010_current")].iloc[0]
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        overall[f"rank_{metric}"] = overall[metric].rank(method="min").astype(int)
        overall[f"delta_{metric}_minus_current"] = overall[metric] - float(base[metric])

    if group_col is None:
        return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), None

    grouped_rows = []
    for key, group in preds.groupby(group_col, sort=True):
        for candidate in CANDIDATES:
            col = f"{candidate}_pred_log"
            row = {group_col: int(key), "candidate": candidate}
            row.update(metrics(group["actual_price"].to_numpy(dtype=float), group["actual_log"].to_numpy(dtype=float), group[col].to_numpy(dtype=float)))
            grouped_rows.append(row)
    grouped = pd.DataFrame(grouped_rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        grouped[f"rank_{metric}"] = grouped.groupby(group_col)[metric].rank(method="min").astype(int)
    return overall.sort_values(["MAPE", "p95_APE", "MdAPE"]), grouped.sort_values([group_col, "MAPE", "p95_APE"])


def bootstrap_vs_current(preds: pd.DataFrame, candidate: str, group_keys: list[str] | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(20260616)
    rows = []
    if group_keys:
        group_iter = preds.groupby(group_keys, sort=True)
    else:
        group_iter = [((), preds)]
    for key, frame in group_iter:
        groups = pd.Series(np.arange(len(frame))).groupby(frame["artist_key"].astype(str).to_numpy()).apply(list)
        price = frame["actual_price"].to_numpy(dtype=float)
        actual_log = frame["actual_log"].to_numpy(dtype=float)
        cand = frame[f"{candidate}_pred_log"].to_numpy(dtype=float)
        cur = frame["qavg_lgbres_s05_cap010_current_pred_log"].to_numpy(dtype=float)
        wins_candidate = {metric: 0 for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]}
        wins_current = {metric: 0 for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]}
        for _ in range(N_BOOT):
            sampled = rng.choice(len(groups), size=len(groups), replace=True)
            idx = np.concatenate([groups.iloc[int(g)] for g in sampled])
            cm = metrics(price[idx], actual_log[idx], cand[idx])
            bm = metrics(price[idx], actual_log[idx], cur[idx])
            for metric in wins_candidate:
                wins_candidate[metric] += cm[metric] < bm[metric]
                wins_current[metric] += bm[metric] < cm[metric]
        row = {"candidate": candidate, "baseline": "qavg_lgbres_s05_cap010_current", "n_boot": N_BOOT}
        if group_keys:
            if not isinstance(key, tuple):
                key = (key,)
            for col, value in zip(group_keys, key):
                row[col] = int(value)
        for metric in wins_candidate:
            row[f"p_candidate_better_current_{metric}"] = wins_candidate[metric] / N_BOOT
            row[f"p_current_better_candidate_{metric}"] = wins_current[metric] / N_BOOT
        rows.append(row)
    return pd.DataFrame(rows)


def write_report(
    q1_overall: pd.DataFrame,
    q1_by_k: pd.DataFrame,
    q1_boot: pd.DataFrame,
    q2_overall: pd.DataFrame,
    q2_by_k: pd.DataFrame,
    q2_boot: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    lines = [
        "# PP-WLITE-Q6 CF7 Candidate Native Validation",
        "",
        "## 1. 목적",
        "",
        "CF7 후보를 기존 Warm-lite native 검증 설계에서 정확히 재평가한다.",
        "",
        "## 2. 후보",
        "",
        "- current: `qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)`",
        "- CF7: `qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)`",
        "",
        "## 3. Q1-like 실존 저이력 LOO Overall",
        "",
        md_table(q1_overall, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "delta_MdAPE_minus_current", "delta_MAPE_minus_current", "delta_p95_APE_minus_current", "delta_RMSE_log_minus_current"], 20),
        "",
        "## 4. Q1-like by history_k",
        "",
        md_table(q1_by_k, ["history_k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 5. Q1 Bootstrap vs Current",
        "",
        md_table(q1_boot, ["candidate", "baseline", "n_boot", "p_candidate_better_current_MdAPE", "p_candidate_better_current_MAPE", "p_candidate_better_current_p95_APE", "p_candidate_better_current_RMSE_log"], 20),
        "",
        "## 6. Q2-like k=1~4 Truncation Overall",
        "",
        md_table(q2_overall, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "delta_MdAPE_minus_current", "delta_MAPE_minus_current", "delta_p95_APE_minus_current", "delta_RMSE_log_minus_current"], 20),
        "",
        "## 7. Q2-like by k",
        "",
        md_table(q2_by_k, ["k", "candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 8. Q2 Bootstrap by seed/k vs Current",
        "",
        md_table(q2_boot, ["trunc_seed", "k", "candidate", "n_boot", "p_candidate_better_current_MdAPE", "p_candidate_better_current_MAPE", "p_candidate_better_current_p95_APE", "p_candidate_better_current_RMSE_log"], 80),
        "",
        "## 9. Config",
        "",
        "```json",
        json.dumps(config, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    (EXP / "reports" / "result_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()
    base_ladder = list(q3.cgrp.LADDER)

    feats = artifact_features()["cold_lightgbm"]
    need = list(dict.fromkeys(feats + ["medium_support_bucket", "ln_price_krw", "log_area", "price_krw", "artist_key"]))
    train, _, _ = load_scope("warm", feats + ["medium_support_bucket"])
    train = train[need].reset_index(drop=True)

    q1_parts = []
    for seed in Q1_SEEDS:
        seed_start = time.time()
        part = run_q1_seed(seed, train, base_ladder)
        part.to_csv(EXP / "outputs" / f"q1_preds_seed{seed}.csv", index=False)
        q1_parts.append(part)
        print(json.dumps({"done": "q1_seed", "seed": seed, "rows": len(part), "seconds": round(time.time() - seed_start, 2)}, ensure_ascii=False), flush=True)
    q1_preds = pd.concat(q1_parts, ignore_index=True)
    q1_preds.to_csv(EXP / "outputs" / "q1_predictions_all_seeds.csv", index=False)
    q1_overall, q1_by_k = metric_rows(q1_preds, "history_k")
    q1_boot = bootstrap_vs_current(q1_preds, "qavg_lgbres_s10_cap015_cf7")

    warm_lite = load_warm_lite_module()
    params = warm_lite.load_params()
    huber_models = warm_lite.load_models()
    warm_features = artifact_features()["warm"]
    needed = list(
        dict.fromkeys(
            warm_features
            + warm_lite.REQUIRED
            + [
                "_track6_row_id",
                "artist_key",
                "price_krw",
                "ln_price_krw",
                "log_area",
                "medium_support_bucket",
                "size_bucket",
                "medium_category",
                "support_category",
            ]
        )
    )
    train_w, _, test = load_scope("warm", needed)
    train_w = train_w[needed].reset_index(drop=True)
    test = test[needed].reset_index(drop=True)
    q3.cgrp.LADDER = q3.LITE_LADDER + base_ladder
    train_w_s = q3.cgrp.train_with_internal_stats(train_w)
    q3.cgrp.LADDER = base_ladder
    q2_stack = q3.train_stack(train_w_s)
    target_artists = set(test["artist_key"].astype(str))

    q2_parts = []
    for trunc_seed in TRUNC_SEEDS:
        for k in KS:
            cond_start = time.time()
            train_k = truncate_train(train_w, target_artists, trunc_seed, k)
            part = run_q2_condition(warm_lite, params, huber_models, q2_stack, train_k, test, trunc_seed, k)
            part.to_csv(EXP / "outputs" / f"q2_preds_trunc{trunc_seed}_k{k}.csv", index=False)
            q2_parts.append(part)
            print(json.dumps({"done": "q2_condition", "trunc_seed": trunc_seed, "k": k, "rows": len(part), "seconds": round(time.time() - cond_start, 2)}, ensure_ascii=False), flush=True)
    q2_preds = pd.concat(q2_parts, ignore_index=True)
    q2_preds.to_csv(EXP / "outputs" / "q2_predictions_all_conditions.csv", index=False)
    q2_overall, q2_by_k = metric_rows(q2_preds, "k")
    q2_boot = bootstrap_vs_current(q2_preds, "qavg_lgbres_s10_cap015_cf7", ["trunc_seed", "k"])

    q1_overall.to_csv(EXP / "outputs" / "q1_candidate_metrics_overall.csv", index=False)
    q1_by_k.to_csv(EXP / "outputs" / "q1_candidate_metrics_by_k.csv", index=False)
    q1_boot.to_csv(EXP / "outputs" / "q1_bootstrap_vs_current.csv", index=False)
    q2_overall.to_csv(EXP / "outputs" / "q2_candidate_metrics_overall.csv", index=False)
    q2_by_k.to_csv(EXP / "outputs" / "q2_candidate_metrics_by_k.csv", index=False)
    q2_boot.to_csv(EXP / "outputs" / "q2_bootstrap_by_seed_k_vs_current.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-WLITE-Q6",
        "experiment_slug": EXP.name,
        "q1_design": f"PP-WCUT5-equivalent real low-history leave-one-out, seeds {Q1_SEEDS}",
        "q2_design": f"PP-WCUT6-equivalent Warm fixed-test k-truncation, seeds {TRUNC_SEEDS}, k {KS}",
        "current_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
        "cf7_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
        "n_boot": N_BOOT,
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(q1_overall, q1_by_k, q1_boot, q2_overall, q2_by_k, q2_boot, config)

    print("[q1 overall]")
    print(q1_overall.to_string(index=False))
    print("\n[q2 overall]")
    print(q2_overall.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
