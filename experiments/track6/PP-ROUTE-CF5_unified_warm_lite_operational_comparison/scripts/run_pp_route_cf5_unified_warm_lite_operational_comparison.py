#!/usr/bin/env python3
"""PP-ROUTE-CF5: unified Warm-lite operational comparison.

Question:
- If we operate one Warm-lite-style model for all same-artist-history warm rows,
  does it compete with the current Warm/Warm-lite split?

This differs from CF4:
- CF4 trained Warm-lite on pooled k=1..6 exposure-augmented rows.
- CF5 trains a single Warm-lite-style model on the actual full Warm train
  distribution, then evaluates:
  1. full-history Warm fixed-test 607 rows vs current Warm WMIN8 operational;
  2. k=1..6 capped-history stress comparison against CF3 Warm clean stack.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning


warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=ConvergenceWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_cgrp1_cold_group_price_stats_base as cgrp  # noqa: E402
import run_pp_wlite_q3_quantile_residual_correction_validation as q3  # noqa: E402
from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF5_unified_warm_lite_operational_comparison"
WARM_OPERATIONAL = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "artifacts" / "wmin8_selected_candidate_predictions.csv"
CF3_PREDS = REPO / "experiments" / "track6" / "PP-ROUTE-CF3_retrained_warm_vs_warm_lite_k1_to_k6" / "outputs" / "predictions_all_conditions.csv"

SEEDS = [20260612, 20260613, 20260614]
KS = [1, 2, 3, 4, 5, 6]
WARM_CANDIDATE = "min1_route_w850_risk_q50_altlower_gap005"


def ensure_dirs() -> None:
    for sub in ["artifacts", "outputs", "reports", "logs", "scripts"]:
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


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


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
    return out


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    warm_base = artifact_features()["warm"]
    needed = unique(
        warm_base
        + q3.cb3.NUM_BASE
        + q3.CAT_COLS
        + ["medium_support_bucket", "ln_price_krw", "price_krw", "_track6_row_id", "artist_key"]
    )
    needed = [col for col in needed if col != "grp_price_proxy"]
    train, _val, test = load_scope("warm", needed)
    train = train[unique([c for c in needed if c in train.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)
    test = test[unique([c for c in needed if c in test.columns] + ["ln_price_krw", "price_krw"])].reset_index(drop=True)

    counts = train.groupby(train["artist_key"].astype(str)).size()
    test["full_train_artist_history_n"] = test["artist_key"].astype(str).map(counts).fillna(0).astype(int)
    eligible_k = test["full_train_artist_history_n"] >= max(KS)
    test_k = test.loc[eligible_k].sort_values("_track6_row_id").reset_index(drop=True)
    audit = {
        "warm_fixed_test_rows_total": int(len(test)),
        "k1_to_k6_eligible_rows": int(len(test_k)),
        "excluded_rows_with_less_than_6_history": int((~eligible_k).sum()),
        "full_history_min": int(test["full_train_artist_history_n"].min()),
        "full_history_max": int(test["full_train_artist_history_n"].max()),
    }
    return train, test.sort_values("_track6_row_id").reset_index(drop=True), test_k, audit


def train_stack_seed(train_s: pd.DataFrame, seed: int) -> dict[str, object]:
    train_s = q3.add_price_proxy(train_s)
    q_oof = q3.oof_quantiles(train_s, seed=seed)
    q_models = q3.fit_quantile_models(train_s, seed=seed)
    residual_models = q3.fit_residual_models(train_s, q_oof)
    return {"q_models": q_models, "residual_models": residual_models}


def train_unified_stack(train: pd.DataFrame, seed: int) -> tuple[dict[str, object], dict[str, Any]]:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        train_s = cgrp.train_with_internal_stats(train)
    finally:
        cgrp.LADDER = base_ladder
    stack = train_stack_seed(train_s, seed)
    audit = {
        "seed": seed,
        "train_rows": int(len(train_s)),
        "train_artists": int(train_s["artist_key"].astype(str).nunique()),
        "median_train_rows_per_artist": float(train_s.groupby(train_s["artist_key"].astype(str)).size().median()),
    }
    return stack, audit


def apply_unified_stack(stack: dict[str, object], frame_s: pd.DataFrame) -> pd.DataFrame:
    qpred = q3.apply_stack(frame_s, stack)
    correction = np.clip(0.50 * qpred["lgb_residual"].to_numpy(dtype=float), -0.10, 0.10)
    out = qpred.copy()
    out["applied_residual_correction_log"] = correction
    out["pred_log"] = qpred["lgbq_full_lean_avg"].to_numpy(dtype=float) + correction
    return out


def truncate_target_artists(train: pd.DataFrame, target_artists: set[str], seed: int, k: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keep: list[np.ndarray] = []
    for artist, idx in train.groupby(train["artist_key"].astype(str), sort=False).indices.items():
        idx_arr = np.asarray(idx, dtype=int)
        if artist in target_artists and len(idx_arr) > k:
            keep.append(np.asarray(rng.choice(idx_arr, size=k, replace=False), dtype=int))
        else:
            keep.append(idx_arr)
    return train.iloc[np.concatenate(keep)].sort_values("_track6_row_id").reset_index(drop=True)


def predict_full_history(train: pd.DataFrame, test: pd.DataFrame, stack: dict[str, object], seed: int) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        test_s = cgrp.assign_group_stats(train, test)
    finally:
        cgrp.LADDER = base_ladder
    pred = apply_unified_stack(stack, test_s)
    out = test[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw", "full_train_artist_history_n"]].copy()
    out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
    out["candidate"] = "Warm-lite unified full-history retrained"
    out["trunc_seed"] = seed
    out["k"] = -1
    out["pred_log"] = pred["pred_log"].to_numpy(dtype=float)
    out["q50_full_log"] = pred["lgbq_full_q50"].to_numpy(dtype=float)
    out["q50_lean_log"] = pred["lgbq_lean_q50"].to_numpy(dtype=float)
    out["quantile_uncertainty_width_log"] = pred["lgbq_width"].to_numpy(dtype=float)
    out["lgb_huber_residual_log"] = pred["lgb_residual"].to_numpy(dtype=float)
    out["applied_residual_correction_log"] = pred["applied_residual_correction_log"].to_numpy(dtype=float)
    return out.sort_values("_track6_row_id").reset_index(drop=True)


def predict_capped_k(train: pd.DataFrame, test_k: pd.DataFrame, stack: dict[str, object], seed: int) -> pd.DataFrame:
    base_ladder = list(cgrp.LADDER)
    target_artists = set(test_k["artist_key"].astype(str))
    parts = []
    cgrp.LADDER = q3.LITE_LADDER + base_ladder
    try:
        for k in KS:
            train_k = truncate_target_artists(train, target_artists, seed, k)
            test_s = cgrp.assign_group_stats(train_k, test_k)
            pred = apply_unified_stack(stack, test_s)
            out = test_k[["_track6_row_id", "artist_key", "price_krw", "ln_price_krw"]].copy()
            out = out.rename(columns={"price_krw": "actual_price", "ln_price_krw": "actual_log"})
            out["candidate"] = "Warm-lite unified full-history retrained"
            out["trunc_seed"] = seed
            out["k"] = k
            out["pred_log"] = pred["pred_log"].to_numpy(dtype=float)
            out["q50_full_log"] = pred["lgbq_full_q50"].to_numpy(dtype=float)
            out["q50_lean_log"] = pred["lgbq_lean_q50"].to_numpy(dtype=float)
            out["quantile_uncertainty_width_log"] = pred["lgbq_width"].to_numpy(dtype=float)
            out["lgb_huber_residual_log"] = pred["lgb_residual"].to_numpy(dtype=float)
            out["applied_residual_correction_log"] = pred["applied_residual_correction_log"].to_numpy(dtype=float)
            parts.append(out)
    finally:
        cgrp.LADDER = base_ladder
    return pd.concat(parts, ignore_index=True)


def load_warm_operational(row_ids: set[int]) -> pd.DataFrame:
    raw = pd.read_csv(WARM_OPERATIONAL, low_memory=False)
    warm = raw[
        raw["eval_split"].eq("test")
        & raw["candidate_label"].eq(WARM_CANDIDATE)
        & raw["_track6_row_id"].astype(int).isin(row_ids)
    ].copy()
    if warm["_track6_row_id"].nunique() != len(row_ids):
        raise RuntimeError(f"Warm operational row mismatch: got {warm['_track6_row_id'].nunique()} expected {len(row_ids)}")
    out = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "pred_log"]].copy()
    out["candidate"] = "Warm WMIN8 operational"
    out["trunc_seed"] = 0
    out["k"] = -1
    return out.sort_values("_track6_row_id").reset_index(drop=True)


def load_cf3_warm(test_ids: set[int]) -> pd.DataFrame:
    raw = pd.read_csv(CF3_PREDS)
    warm = raw[raw["candidate"].eq("Warm retrained clean stack")].copy()
    warm = warm[warm["_track6_row_id"].astype(int).isin(test_ids)].copy()
    expected = len(test_ids) * len(SEEDS) * len(KS)
    if len(warm) != expected:
        raise RuntimeError(f"CF3 Warm row mismatch: got {len(warm)} expected {expected}")
    keep = ["_track6_row_id", "artist_key", "actual_price", "actual_log", "candidate", "trunc_seed", "k", "pred_log"]
    return warm[keep].copy()


def full_history_metrics(full_preds: pd.DataFrame, warm_operational: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seed_mean = (
        full_preds.groupby("_track6_row_id", as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values("_track6_row_id")
    )
    rows = []
    for name, frame, col in [
        ("Warm WMIN8 operational", warm_operational, "pred_log"),
        ("Warm-lite unified full-history retrained", seed_mean, "pred_log"),
    ]:
        row = {"candidate": name}
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), frame[col].to_numpy()))
        rows.append(row)
    metric_df = pd.DataFrame(rows)

    paired = warm_operational[["_track6_row_id", "actual_price", "actual_log", "pred_log"]].rename(columns={"pred_log": "warm_pred_log"}).merge(
        seed_mean[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "warm_lite_unified_pred_log"}),
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    paired = add_ape(paired, "warm_pred_log", "warm_ape")
    paired = add_ape(paired, "warm_lite_unified_pred_log", "warm_lite_unified_ape")
    summary = pd.DataFrame(
        [
            {
                "n": int(len(paired)),
                "warm_better_share": float(np.mean(paired["warm_ape"] < paired["warm_lite_unified_ape"])),
                "warm_lite_unified_better_share": float(np.mean(paired["warm_lite_unified_ape"] < paired["warm_ape"])),
                "median_ape_delta_warm_minus_unified": float(np.nanmedian(paired["warm_ape"] - paired["warm_lite_unified_ape"])),
                "mean_ape_delta_warm_minus_unified": float(np.nanmean(paired["warm_ape"] - paired["warm_lite_unified_ape"])),
            }
        ]
    )
    return metric_df, summary


def repeated_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, seed, k), group in predictions.groupby(["candidate", "trunc_seed", "k"], sort=True):
        row = {"candidate": candidate, "trunc_seed": int(seed), "k": int(k)}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "candidate", "trunc_seed"]).reset_index(drop=True)


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


def capped_same_n_metrics(seed_mean: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} seed-mean"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def capped_paired_by_k(seed_mean: pd.DataFrame) -> pd.DataFrame:
    warm = seed_mean[seed_mean["candidate"].eq("Warm retrained clean stack")].rename(columns={"pred_log": "warm_pred_log"})
    lite = seed_mean[seed_mean["candidate"].eq("Warm-lite unified full-history retrained")].rename(columns={"pred_log": "warm_lite_unified_pred_log"})
    wide = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "k", "warm_pred_log"]].merge(
        lite[["_track6_row_id", "k", "warm_lite_unified_pred_log"]],
        on=["_track6_row_id", "k"],
        how="inner",
        validate="one_to_one",
    )
    wide = add_ape(wide, "warm_pred_log", "warm_ape")
    wide = add_ape(wide, "warm_lite_unified_pred_log", "warm_lite_unified_ape")
    rows = []
    for k, group in wide.groupby("k", sort=True):
        rows.append(
            {
                "k": int(k),
                "n": int(len(group)),
                "warm_better_share": float(np.mean(group["warm_ape"] < group["warm_lite_unified_ape"])),
                "warm_lite_unified_better_share": float(np.mean(group["warm_lite_unified_ape"] < group["warm_ape"])),
                "median_ape_delta_warm_minus_unified": float(np.nanmedian(group["warm_ape"] - group["warm_lite_unified_ape"])),
                "mean_ape_delta_warm_minus_unified": float(np.nanmean(group["warm_ape"] - group["warm_lite_unified_ape"])),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    full_metrics: pd.DataFrame,
    full_paired: pd.DataFrame,
    capped_metrics: pd.DataFrame,
    capped_paired: pd.DataFrame,
    repeated: pd.DataFrame,
    training_audit: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    lines = [
        "# PP-ROUTE-CF5 Unified Warm-lite Operational Comparison",
        "",
        "## 1. 목적",
        "",
        "Warm과 Warm-lite를 나누지 않고 Warm-lite 계열 단일 모델로 1건 이상 warm row 전체를 처리할 수 있는지 검증한다.",
        "",
        "## 2. 핵심 설계",
        "",
        "- Warm-lite unified 모델은 실제 full Warm train distribution으로 seed별 1개씩 학습한다.",
        "- 학습 시 train row 통계는 5-fold internal stats로 자기 가격 누수를 막는다.",
        "- 운영형 비교는 Warm fixed-test 607개에 전체 작가 train history를 그대로 넣고, 현재 Warm WMIN8 operational과 비교한다.",
        "- 보조 비교는 같은 unified 모델을 k=1~6 capped history로 평가해 CF3 Warm clean stack과 비교한다.",
        "",
        "## 3. Full-history operational comparison",
        "",
        md_table(full_metrics, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 4. Full-history paired comparison",
        "",
        md_table(full_paired, ["n", "warm_better_share", "warm_lite_unified_better_share", "median_ape_delta_warm_minus_unified", "mean_ape_delta_warm_minus_unified"], 10),
        "",
        "## 5. k=1~6 capped-history stress metrics",
        "",
        md_table(capped_metrics, ["candidate", "condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 80),
        "",
        "## 6. k=1~6 capped paired comparison",
        "",
        md_table(capped_paired, ["k", "n", "warm_better_share", "warm_lite_unified_better_share", "median_ape_delta_warm_minus_unified", "mean_ape_delta_warm_minus_unified"], 20),
        "",
        "## 7. Repeated seed metrics",
        "",
        md_table(repeated, ["candidate", "trunc_seed", "k", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 80),
        "",
        "## 8. Training audit",
        "",
        md_table(training_audit, ["seed", "train_rows", "train_artists", "median_train_rows_per_artist"], 20),
        "",
        "## 9. 해석 주의",
        "",
        "- 이 결과는 단일 Warm-lite 운영 후보의 가능성 검증이다.",
        "- full-history 표는 현재 Warm WMIN8 operational과 직접 비교하므로 운영 단순화 판단에 가장 중요하다.",
        "- capped-history 표는 같은 unified 모델의 저이력/중이력 스트레스 테스트다.",
        "- Cold처럼 같은 작가 가격 이력이 0건인 경우는 이 실험 대상이 아니다.",
        "",
        "## 10. Config",
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
    train, test_full, test_k, eligibility_audit = load_frames()
    warm_operational = load_warm_operational(set(test_full["_track6_row_id"].astype(int)))
    cf3_warm = load_cf3_warm(set(test_k["_track6_row_id"].astype(int)))

    full_parts = []
    capped_parts = []
    training_rows = []
    for seed in SEEDS:
        seed_start = time.time()
        stack, train_audit = train_unified_stack(train, seed)
        training_rows.append(train_audit)
        full_parts.append(predict_full_history(train, test_full, stack, seed))
        capped_parts.append(predict_capped_k(train, test_k, stack, seed))
        print(
            json.dumps(
                {
                    "done": "unified_seed",
                    "seed": seed,
                    "full_rows": len(test_full),
                    "capped_rows": len(capped_parts[-1]),
                    "seconds": round(time.time() - seed_start, 2),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    full_preds = pd.concat(full_parts, ignore_index=True)
    capped_lite = pd.concat(capped_parts, ignore_index=True)
    training_audit = pd.DataFrame(training_rows)

    full_metrics, full_paired = full_history_metrics(full_preds, warm_operational)
    capped_predictions = pd.concat([cf3_warm, capped_lite], ignore_index=True, sort=False)
    repeated = repeated_metrics(capped_predictions)
    seed_mean = seed_mean_predictions(capped_predictions)
    capped_metrics = capped_same_n_metrics(seed_mean)
    capped_paired = capped_paired_by_k(seed_mean)

    full_preds.to_csv(EXP / "outputs" / "warm_lite_unified_full_history_predictions.csv", index=False)
    warm_operational.to_csv(EXP / "outputs" / "warm_operational_full_history_predictions.csv", index=False)
    full_metrics.to_csv(EXP / "outputs" / "full_history_operational_metrics.csv", index=False)
    full_paired.to_csv(EXP / "outputs" / "full_history_paired_comparison.csv", index=False)
    capped_predictions.to_csv(EXP / "outputs" / "capped_predictions_all_conditions.csv", index=False)
    repeated.to_csv(EXP / "outputs" / "capped_repeated_condition_metrics.csv", index=False)
    seed_mean.to_csv(EXP / "outputs" / "capped_seed_mean_predictions_by_k.csv", index=False)
    capped_metrics.to_csv(EXP / "outputs" / "capped_same_n_metrics_by_k.csv", index=False)
    capped_paired.to_csv(EXP / "outputs" / "capped_paired_warm_vs_unified_by_k.csv", index=False)
    training_audit.to_csv(EXP / "outputs" / "training_audit.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF5",
        "experiment_slug": EXP.name,
        "seeds": SEEDS,
        "k_values_for_stress_test": KS,
        "base_eval_set": "Warm fixed-test rows",
        "eligibility_audit": eligibility_audit,
        "unified_warm_lite_training": {
            "train_distribution": "actual full Warm train distribution",
            "group_stats": "5-fold internal stats for train, full train stats for full-history test",
            "model": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
            "candidate": "lgbq_full_lean_avg + clip(0.50 * lgb_huber_residual, -0.10, +0.10)",
        },
        "comparators": {
            "full_history": "Warm WMIN8 operational",
            "capped_k1_to_k6": "CF3 Warm retrained clean stack",
        },
        "limitations": [
            "This experiment covers same-artist-history warm rows only; Cold/no-history routing remains separate.",
            "The k=1~6 capped table is a stress test; the full-history table is the primary operational simplification comparison.",
            "CF3 Warm clean stack is not exact historical WMIN8/PPV8 full artifact rebuild.",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(full_metrics, full_paired, capped_metrics, capped_paired, repeated, training_audit, config)

    print("[full-history operational metrics]")
    print(full_metrics.to_string(index=False))
    print("\n[full-history paired]")
    print(full_paired.to_string(index=False))
    print("\n[capped k metrics]")
    print(capped_metrics.to_string(index=False))
    print("\n[capped paired]")
    print(capped_paired.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
