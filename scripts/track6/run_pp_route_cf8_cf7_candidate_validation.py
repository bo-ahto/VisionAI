#!/usr/bin/env python3
"""PP-ROUTE-CF8: validate the CF7 Warm-lite tail-guard candidate.

This follow-up uses existing CF5/CF7 outputs, so it does not retrain models.

Checks:
1. Full-history Warm fixed-test bootstrap for current vs CF7 candidate.
2. k=1..6 capped-history stress using CF5 seed-level predictions.
3. Segment/top-error analysis for the remaining CF7 candidate tail rows.
"""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF8_cf7_candidate_validation"
CF5 = REPO / "experiments" / "track6" / "PP-ROUTE-CF5_unified_warm_lite_operational_comparison"
CF7 = REPO / "experiments" / "track6" / "PP-ROUTE-CF7_warm_lite_tail_guard"

N_BOOT = 2000
CF7_STRENGTH = 1.00
CF7_CAP = 0.15


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "scripts"]:
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


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


def add_ape(frame: pd.DataFrame, pred_col: str, out_col: str) -> pd.DataFrame:
    out = frame.copy()
    pred_price = np.clip(np.exp(pd.to_numeric(out[pred_col], errors="coerce")), 1_000.0, None)
    actual = pd.to_numeric(out["actual_price"], errors="coerce")
    out[out_col] = np.abs(pred_price - actual) / np.clip(actual, 1.0, None)
    out[f"{out_col}_signed_log_error"] = pd.to_numeric(out[pred_col], errors="coerce") - pd.to_numeric(out["actual_log"], errors="coerce")
    return out


def cf7_pred_from_qavg(frame: pd.DataFrame) -> np.ndarray:
    if "qavg_log" in frame.columns:
        qavg = frame["qavg_log"].to_numpy(dtype=float)
    else:
        qavg = 0.50 * frame["q50_full_log"].to_numpy(dtype=float) + 0.50 * frame["q50_lean_log"].to_numpy(dtype=float)
    residual = frame["lgb_huber_residual_log"].to_numpy(dtype=float)
    correction = np.clip(CF7_STRENGTH * residual, -CF7_CAP, CF7_CAP)
    return qavg + correction


def metric_rows(frame: pd.DataFrame, candidates: dict[str, str]) -> pd.DataFrame:
    rows = []
    for candidate, col in candidates.items():
        row = {"candidate": candidate}
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), frame[col].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out


def artist_cluster_bootstrap(
    frame: pd.DataFrame,
    candidate_a: str,
    candidate_b: str,
    label_a: str,
    label_b: str,
    n_boot: int = N_BOOT,
) -> pd.DataFrame:
    rng = np.random.default_rng(20260616)
    groups = list(frame.groupby(frame["artist_key"].astype(str)).indices.values())
    price = frame["actual_price"].to_numpy(dtype=float)
    actual_log = frame["actual_log"].to_numpy(dtype=float)
    pred_a = frame[candidate_a].to_numpy(dtype=float)
    pred_b = frame[candidate_b].to_numpy(dtype=float)
    wins_a = {metric: 0 for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]}
    wins_b = {metric: 0 for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]}
    deltas = {metric: [] for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]}
    for _ in range(n_boot):
        sampled = rng.choice(len(groups), size=len(groups), replace=True)
        idx = np.concatenate([groups[int(i)] for i in sampled])
        ma = metrics(price[idx], actual_log[idx], pred_a[idx])
        mb = metrics(price[idx], actual_log[idx], pred_b[idx])
        for metric in wins_a:
            wins_a[metric] += ma[metric] < mb[metric]
            wins_b[metric] += mb[metric] < ma[metric]
            deltas[metric].append(ma[metric] - mb[metric])
    rows = []
    for metric in wins_a:
        arr = np.asarray(deltas[metric], dtype=float)
        rows.append(
            {
                "candidate_a": label_a,
                "candidate_b": label_b,
                "metric": metric,
                "n_boot": n_boot,
                "p_a_better": wins_a[metric] / n_boot,
                "p_b_better": wins_b[metric] / n_boot,
                "delta_a_minus_b_mean": float(np.mean(arr)),
                "delta_a_minus_b_q05": float(np.quantile(arr, 0.05)),
                "delta_a_minus_b_q50": float(np.quantile(arr, 0.50)),
                "delta_a_minus_b_q95": float(np.quantile(arr, 0.95)),
            }
        )
    return pd.DataFrame(rows)


def load_full_history_frame() -> pd.DataFrame:
    cf7_features = pd.read_csv(CF7 / "outputs" / "seed_mean_feature_predictions.csv", low_memory=False)
    test = cf7_features[cf7_features["split"].eq("test")].copy().reset_index(drop=True)
    test["warm_lite_current_pred_log"] = test["current_pred_log"].to_numpy(dtype=float)
    test["warm_lite_cf7_pred_log"] = cf7_pred_from_qavg(test)

    warm = pd.read_csv(CF5 / "outputs" / "warm_operational_full_history_predictions.csv", low_memory=False)
    warm = warm[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "warm_wmin8_pred_log"})
    out = test.merge(warm, on="_track6_row_id", how="inner", validate="one_to_one")
    if len(out) != len(test):
        raise RuntimeError(f"Warm merge mismatch: {len(out)} vs {len(test)}")
    for col in ["warm_lite_current_pred_log", "warm_lite_cf7_pred_log", "warm_wmin8_pred_log"]:
        out = add_ape(out, col, col.replace("_pred_log", "_ape"))
    return out


def load_capped_frame() -> pd.DataFrame:
    raw = pd.read_csv(CF5 / "outputs" / "capped_predictions_all_conditions.csv", low_memory=False)
    warm = raw[raw["candidate"].eq("Warm retrained clean stack")].copy()
    warm["candidate"] = "Warm retrained clean stack"
    warm = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "candidate", "trunc_seed", "k", "pred_log"]]

    lite = raw[raw["candidate"].eq("Warm-lite unified full-history retrained")].copy()
    lite["qavg_log"] = 0.50 * lite["q50_full_log"].to_numpy(dtype=float) + 0.50 * lite["q50_lean_log"].to_numpy(dtype=float)
    lite["current_pred_log"] = lite["pred_log"].to_numpy(dtype=float)
    lite["cf7_pred_log"] = cf7_pred_from_qavg(lite)

    current = lite[["_track6_row_id", "artist_key", "actual_price", "actual_log", "trunc_seed", "k", "current_pred_log"]].copy()
    current["candidate"] = "Warm-lite current s0.50 cap0.10"
    current = current.rename(columns={"current_pred_log": "pred_log"})

    cf7 = lite[["_track6_row_id", "artist_key", "actual_price", "actual_log", "trunc_seed", "k", "cf7_pred_log"]].copy()
    cf7["candidate"] = "Warm-lite CF7 s1.00 cap0.15"
    cf7 = cf7.rename(columns={"cf7_pred_log": "pred_log"})

    return pd.concat([warm, current, cf7], ignore_index=True, sort=False)


def seed_mean_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    return (
        predictions.groupby(["candidate", "k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "candidate", "_track6_row_id"])
        .reset_index(drop=True)
    )


def capped_metrics(seed_mean: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} seed-mean"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out.groupby("k")[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def capped_paired(seed_mean: pd.DataFrame) -> pd.DataFrame:
    base = seed_mean[seed_mean["candidate"].eq("Warm-lite current s0.50 cap0.10")].rename(columns={"pred_log": "current_pred_log"})
    cf7 = seed_mean[seed_mean["candidate"].eq("Warm-lite CF7 s1.00 cap0.15")].rename(columns={"pred_log": "cf7_pred_log"})
    warm = seed_mean[seed_mean["candidate"].eq("Warm retrained clean stack")].rename(columns={"pred_log": "warm_pred_log"})
    wide = (
        base[["_track6_row_id", "artist_key", "actual_price", "actual_log", "k", "current_pred_log"]]
        .merge(cf7[["_track6_row_id", "k", "cf7_pred_log"]], on=["_track6_row_id", "k"], how="inner", validate="one_to_one")
        .merge(warm[["_track6_row_id", "k", "warm_pred_log"]], on=["_track6_row_id", "k"], how="inner", validate="one_to_one")
    )
    for col in ["current_pred_log", "cf7_pred_log", "warm_pred_log"]:
        wide = add_ape(wide, col, col.replace("_pred_log", "_ape"))
    rows = []
    for k, group in wide.groupby("k", sort=True):
        rows.append(
            {
                "k": int(k),
                "n": int(len(group)),
                "cf7_better_than_current_share": float(np.mean(group["cf7_ape"] < group["current_ape"])),
                "current_better_than_cf7_share": float(np.mean(group["current_ape"] < group["cf7_ape"])),
                "cf7_better_than_warm_share": float(np.mean(group["cf7_ape"] < group["warm_ape"])),
                "warm_better_than_cf7_share": float(np.mean(group["warm_ape"] < group["cf7_ape"])),
                "mean_ape_delta_current_minus_cf7": float(np.nanmean(group["current_ape"] - group["cf7_ape"])),
                "mean_ape_delta_warm_minus_cf7": float(np.nanmean(group["warm_ape"] - group["cf7_ape"])),
            }
        )
    return pd.DataFrame(rows)


def segment_bins(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    hist = out["full_train_artist_history_n"].to_numpy(dtype=float)
    out["history_bin"] = np.select(
        [hist <= 5, hist <= 10, hist <= 20, hist <= 50, hist > 50],
        ["5", "6-10", "11-20", "21-50", "51+"],
        default="unknown",
    )
    out["price_bin"] = pd.qcut(out["actual_log"], q=4, labels=["price_q1_low", "price_q2", "price_q3", "price_q4_high"], duplicates="drop").astype(str)
    out["qwidth_bin"] = pd.qcut(
        out["quantile_uncertainty_width_log"],
        q=4,
        labels=["width_q1_low", "width_q2", "width_q3", "width_q4_high"],
        duplicates="drop",
    ).astype(str)
    corr = np.clip(out["lgb_huber_residual_log"].to_numpy(dtype=float), -CF7_CAP, CF7_CAP)
    out["cf7_correction_log"] = corr
    out["correction_direction"] = np.select([corr > 1e-12, corr < -1e-12], ["up", "down"], default="zero")
    return out


def segment_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for seg_col in ["history_bin", "price_bin", "qwidth_bin", "correction_direction"]:
        for seg, group in frame.groupby(seg_col, sort=True):
            row = {"segment_axis": seg_col, "segment": str(seg)}
            for label, pred_col in [
                ("current", "warm_lite_current_pred_log"),
                ("cf7", "warm_lite_cf7_pred_log"),
                ("warm", "warm_wmin8_pred_log"),
            ]:
                mt = metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group[pred_col].to_numpy())
                for metric, value in mt.items():
                    row[f"{label}_{metric}"] = value
            row["cf7_minus_current_MAPE"] = row["cf7_MAPE"] - row["current_MAPE"]
            row["cf7_minus_current_p95"] = row["cf7_p95_APE"] - row["current_p95_APE"]
            rows.append(row)
    return pd.DataFrame(rows)


def top_error_rows(frame: pd.DataFrame) -> pd.DataFrame:
    threshold = float(np.nanquantile(frame["warm_lite_cf7_ape"], 0.95))
    cols = [
        "_track6_row_id",
        "artist_key",
        "actual_price",
        "actual_log",
        "full_train_artist_history_n",
        "qavg_log",
        "lgb_huber_residual_log",
        "cf7_correction_log",
        "quantile_uncertainty_width_log",
        "full_lean_gap_abs_log",
        "warm_lite_current_pred_log",
        "warm_lite_cf7_pred_log",
        "warm_wmin8_pred_log",
        "warm_lite_current_ape",
        "warm_lite_cf7_ape",
        "warm_wmin8_ape",
        "history_bin",
        "price_bin",
        "qwidth_bin",
        "correction_direction",
    ]
    return frame[frame["warm_lite_cf7_ape"] >= threshold].sort_values("warm_lite_cf7_ape", ascending=False)[cols].reset_index(drop=True)


def write_report(
    full_metrics: pd.DataFrame,
    boot: pd.DataFrame,
    capped_m: pd.DataFrame,
    capped_pair: pd.DataFrame,
    seg_m: pd.DataFrame,
    top_rows: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    lines = [
        "# PP-ROUTE-CF8 CF7 Candidate Validation",
        "",
        "## 1. 목적",
        "",
        "CF7에서 선택된 Warm-lite tail guard 후보를 full-history, k=1~6 stress, bootstrap, segment tail 관점에서 검증한다.",
        "",
        "## 2. 후보",
        "",
        "- 기존 Warm-lite: `qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)`",
        "- CF7 후보: `qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)`",
        "",
        "## 3. Full-History Test Metrics",
        "",
        md_table(full_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MdAPE", "rank_MAPE", "rank_p95_APE", "rank_RMSE_log"], 20),
        "",
        "## 4. Artist-Cluster Bootstrap",
        "",
        md_table(boot, ["candidate_a", "candidate_b", "metric", "n_boot", "p_a_better", "p_b_better", "delta_a_minus_b_mean", "delta_a_minus_b_q05", "delta_a_minus_b_q50", "delta_a_minus_b_q95"], 40),
        "",
        "## 5. k=1~6 Capped-History Stress Metrics",
        "",
        md_table(capped_m, ["candidate", "condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 6. k=1~6 Paired Shares",
        "",
        md_table(capped_pair, ["k", "n", "cf7_better_than_current_share", "current_better_than_cf7_share", "cf7_better_than_warm_share", "warm_better_than_cf7_share", "mean_ape_delta_current_minus_cf7", "mean_ape_delta_warm_minus_cf7"], 20),
        "",
        "## 7. Segment Metrics",
        "",
        md_table(seg_m, ["segment_axis", "segment", "current_n", "current_MAPE", "current_p95_APE", "cf7_MAPE", "cf7_p95_APE", "warm_MAPE", "warm_p95_APE", "cf7_minus_current_MAPE", "cf7_minus_current_p95"], 80),
        "",
        "## 8. Top CF7 Tail Rows",
        "",
        md_table(top_rows.head(20), ["_track6_row_id", "artist_key", "actual_price", "full_train_artist_history_n", "warm_lite_cf7_ape", "warm_lite_current_ape", "warm_wmin8_ape", "quantile_uncertainty_width_log", "cf7_correction_log", "history_bin", "price_bin", "qwidth_bin"], 20),
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

    full = segment_bins(load_full_history_frame())
    full_metrics = metric_rows(
        full,
        {
            "Warm WMIN8 operational": "warm_wmin8_pred_log",
            "Warm-lite current s0.50 cap0.10": "warm_lite_current_pred_log",
            "Warm-lite CF7 s1.00 cap0.15": "warm_lite_cf7_pred_log",
        },
    )
    boot = pd.concat(
        [
            artist_cluster_bootstrap(
                full,
                "warm_lite_cf7_pred_log",
                "warm_lite_current_pred_log",
                "Warm-lite CF7 s1.00 cap0.15",
                "Warm-lite current s0.50 cap0.10",
            ),
            artist_cluster_bootstrap(
                full,
                "warm_lite_cf7_pred_log",
                "warm_wmin8_pred_log",
                "Warm-lite CF7 s1.00 cap0.15",
                "Warm WMIN8 operational",
            ),
        ],
        ignore_index=True,
    )

    capped_seed = load_capped_frame()
    capped_mean = seed_mean_predictions(capped_seed)
    capped_m = capped_metrics(capped_mean)
    capped_pair = capped_paired(capped_mean)

    seg_m = segment_metrics(full)
    top_rows = top_error_rows(full)

    full.to_csv(EXP / "outputs" / "full_history_cf7_candidate_rows.csv", index=False)
    full_metrics.to_csv(EXP / "outputs" / "full_history_metrics.csv", index=False)
    boot.to_csv(EXP / "outputs" / "full_history_artist_cluster_bootstrap.csv", index=False)
    capped_seed.to_csv(EXP / "outputs" / "capped_seed_level_predictions.csv", index=False)
    capped_mean.to_csv(EXP / "outputs" / "capped_seed_mean_predictions.csv", index=False)
    capped_m.to_csv(EXP / "outputs" / "capped_metrics_by_k.csv", index=False)
    capped_pair.to_csv(EXP / "outputs" / "capped_paired_by_k.csv", index=False)
    seg_m.to_csv(EXP / "outputs" / "full_history_segment_metrics.csv", index=False)
    top_rows.to_csv(EXP / "outputs" / "full_history_top_cf7_tail_rows.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF8",
        "experiment_slug": EXP.name,
        "source_experiments": [
            str(CF5.relative_to(REPO)),
            str(CF7.relative_to(REPO)),
        ],
        "candidate_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
        "baseline_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
        "n_boot": N_BOOT,
        "bootstrap_unit": "artist_key cluster bootstrap",
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(full_metrics, boot, capped_m, capped_pair, seg_m, top_rows, config)

    print("[full history metrics]")
    print(full_metrics.to_string(index=False))
    print("\n[bootstrap]")
    print(boot.to_string(index=False))
    print("\n[capped metrics]")
    print(capped_m.to_string(index=False))
    print("\n[capped paired]")
    print(capped_pair.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
