#!/usr/bin/env python3
"""PP-ROUTE-CF6: full-history retrained Warm vs unified Warm-lite.

This is the strict full-history follow-up:
- Train Warm clean stack on the full Warm train distribution.
- Train unified Warm-lite on the full Warm train distribution.
- Evaluate both on the same Warm fixed-test 607 rows with full same-artist
  history available.

Warm side caveat:
- This retrains the regeneratable clean Warm stack axes used in CF3. It is not
  an exact historical WMIN8/PPV8 full artifact rebuild.
"""
from __future__ import annotations

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

import run_pp_route_cf3_retrained_warm_vs_warm_lite_k1_to_k6 as cf3  # noqa: E402
import run_pp_route_cf5_unified_warm_lite_operational_comparison as cf5  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF6_full_history_retrained_warm_vs_unified_warm_lite"
SEEDS = [20260612, 20260613, 20260614]


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


def seed_mean(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("_track6_row_id", as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )


def metric_table(warm: pd.DataFrame, lite_seed_mean: pd.DataFrame, lite_all: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, frame in [
        ("Warm clean full-history retrained", warm),
        ("Warm-lite unified full-history retrained", lite_seed_mean),
    ]:
        row = {"candidate": candidate, "condition": "full-history fixed-test"}
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), frame["pred_log"].to_numpy()))
        rows.append(row)

    for seed, part in lite_all.groupby("trunc_seed", sort=True):
        row = {"candidate": "Warm-lite unified full-history retrained", "condition": f"seed={int(seed)}"}
        row.update(metrics(part["actual_price"].to_numpy(), part["actual_log"].to_numpy(), part["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out


def paired_table(warm: pd.DataFrame, lite_seed_mean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    paired = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "pred_log"]].rename(
        columns={"pred_log": "warm_pred_log"}
    ).merge(
        lite_seed_mean[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "warm_lite_pred_log"}),
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    paired = add_ape(paired, "warm_pred_log", "warm_ape")
    paired = add_ape(paired, "warm_lite_pred_log", "warm_lite_ape")
    summary = pd.DataFrame(
        [
            {
                "n": int(len(paired)),
                "warm_better_share": float(np.mean(paired["warm_ape"] < paired["warm_lite_ape"])),
                "warm_lite_better_share": float(np.mean(paired["warm_lite_ape"] < paired["warm_ape"])),
                "tie_share": float(np.mean(np.isclose(paired["warm_ape"], paired["warm_lite_ape"]))),
                "median_ape_delta_warm_minus_warm_lite": float(np.nanmedian(paired["warm_ape"] - paired["warm_lite_ape"])),
                "mean_ape_delta_warm_minus_warm_lite": float(np.nanmean(paired["warm_ape"] - paired["warm_lite_ape"])),
            }
        ]
    )
    return summary, paired


def write_report(
    metrics_df: pd.DataFrame,
    paired_df: pd.DataFrame,
    warm_audit: pd.DataFrame,
    lite_training_audit: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    primary = metrics_df[metrics_df["condition"].eq("full-history fixed-test")]
    lines = [
        "# PP-ROUTE-CF6 Full-History Retrained Warm vs Unified Warm-lite",
        "",
        "## 1. 목적",
        "",
        "full-history 조건에서 Warm clean stack과 unified Warm-lite를 모두 새로 학습해 Warm fixed-test 607개에서 비교한다.",
        "",
        "## 2. 학습 조건",
        "",
        "- 두 후보 모두 같은 Warm train split을 사용한다.",
        "- 두 후보 모두 같은 Warm fixed-test 607개에서 평가한다.",
        "- Warm은 CF3의 재현 가능한 clean stack 축을 full-history 조건으로 재학습한다.",
        "- Warm-lite는 CF5의 unified 구조를 full Warm train distribution으로 seed 3개 재학습하고 seed-mean으로 평가한다.",
        "- 이 비교도 운영 WMIN8 전체 PPV8/V2 artifact의 완전 재생성은 아니다.",
        "",
        "## 3. Primary Metrics",
        "",
        md_table(primary, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 20),
        "",
        "## 4. Warm-lite Seed Metrics",
        "",
        md_table(metrics_df[metrics_df["condition"].str.startswith("seed=")], ["condition", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 5. Paired Row-Level Comparison",
        "",
        md_table(paired_df, ["n", "warm_better_share", "warm_lite_better_share", "tie_share", "median_ape_delta_warm_minus_warm_lite", "mean_ape_delta_warm_minus_warm_lite"], 10),
        "",
        "## 6. Warm Route Audit",
        "",
        md_table(warm_audit, ["route_to_alt_share", "median_risk_score", "route_threshold"], 10),
        "",
        "## 7. Warm-lite Training Audit",
        "",
        md_table(lite_training_audit, ["seed", "train_rows", "train_artists", "median_train_rows_per_artist"], 10),
        "",
        "## 8. 해석 주의",
        "",
        "- 이 비교는 학습 조건을 full-history로 맞춘 clean-stack 비교다.",
        "- 현재 운영 Warm WMIN8 artifact와 직접 같지는 않다. 운영 Warm WMIN8과의 직접 비교는 CF5를 함께 본다.",
        "- Cold/no-history 조건은 별도 라우트로 남는다.",
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

    warm_train, warm_val, warm_test, warm_eligibility, l10_features = cf3.load_frames([1])
    lite_train, lite_test, _lite_test_k, lite_eligibility = cf5.load_frames()
    if set(warm_test["_track6_row_id"].astype(int)) != set(lite_test["_track6_row_id"].astype(int)):
        raise RuntimeError("Warm and Warm-lite test rows do not align")

    warm_start = time.time()
    warm_pred, warm_route_audit = cf3.run_warm_retrained(
        warm_train,
        warm_val,
        warm_test,
        l10_features,
        seed=SEEDS[0],
        k=-1,
    )
    warm_pred["candidate"] = "Warm clean full-history retrained"
    print(json.dumps({"done": "warm_full_history", "rows": len(warm_pred), "seconds": round(time.time() - warm_start, 2)}, ensure_ascii=False), flush=True)

    lite_parts = []
    lite_training_rows = []
    for seed in SEEDS:
        seed_start = time.time()
        stack, audit = cf5.train_unified_stack(lite_train, seed)
        lite_training_rows.append(audit)
        pred = cf5.predict_full_history(lite_train, lite_test, stack, seed)
        pred["candidate"] = "Warm-lite unified full-history retrained"
        lite_parts.append(pred)
        print(
            json.dumps(
                {
                    "done": "warm_lite_unified_full_history",
                    "seed": seed,
                    "rows": len(pred),
                    "seconds": round(time.time() - seed_start, 2),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    lite_all = pd.concat(lite_parts, ignore_index=True)
    lite_seed_mean = seed_mean(lite_all)
    if not lite_seed_mean["seed_n"].eq(len(SEEDS)).all():
        raise RuntimeError("Warm-lite seed mean has missing seeds")
    lite_training_audit = pd.DataFrame(lite_training_rows)

    metrics_df = metric_table(warm_pred, lite_seed_mean, lite_all)
    paired_df, paired_rows = paired_table(warm_pred, lite_seed_mean)
    warm_audit_summary = pd.DataFrame(
        [
            {
                "route_to_alt_share": float(warm_pred["route_to_alternative"].mean()),
                "median_risk_score": float(warm_pred["risk_score"].median()),
                "route_threshold": float(warm_pred["route_threshold"].iloc[0]),
            }
        ]
    )

    warm_pred.to_csv(EXP / "outputs" / "warm_clean_full_history_predictions.csv", index=False)
    warm_route_audit.to_csv(EXP / "outputs" / "warm_clean_full_history_route_audit.csv", index=False)
    lite_all.to_csv(EXP / "outputs" / "warm_lite_unified_full_history_predictions_all_seeds.csv", index=False)
    lite_seed_mean.to_csv(EXP / "outputs" / "warm_lite_unified_full_history_seed_mean.csv", index=False)
    metrics_df.to_csv(EXP / "outputs" / "full_history_retrained_metrics.csv", index=False)
    paired_df.to_csv(EXP / "outputs" / "full_history_retrained_paired_summary.csv", index=False)
    paired_rows.to_csv(EXP / "outputs" / "full_history_retrained_paired_rows.csv", index=False)
    lite_training_audit.to_csv(EXP / "outputs" / "warm_lite_training_audit.csv", index=False)
    warm_audit_summary.to_csv(EXP / "outputs" / "warm_route_audit_summary.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF6",
        "experiment_slug": EXP.name,
        "seeds": SEEDS,
        "base_eval_set": "Warm fixed-test 607 rows",
        "warm_eligibility_audit": warm_eligibility,
        "warm_lite_eligibility_audit": lite_eligibility,
        "warm_training": {
            "train_distribution": "actual full Warm train distribution",
            "validation": "Warm validation split for Huber refit and router",
            "stack": "SVC comparable Huber + L10 generated-bucket sequential + Huber refit + risk router",
            "caveat": "clean stack, not exact historical WMIN8/PPV8 full artifact rebuild",
        },
        "warm_lite_training": {
            "train_distribution": "actual full Warm train distribution",
            "group_stats": "5-fold internal stats for train, full train stats for test",
            "stack": "LightGBM Quantile full/lean + LightGBM objective=huber residual",
            "aggregation": "seed-mean over three retrained seeds",
        },
        "limitations": [
            "This is a full-history retrained clean-stack comparison, not exact Warm WMIN8 operational artifact reproduction.",
            "Use CF5 for direct comparison against current Warm WMIN8 operational.",
            "Cold/no-history route remains separate.",
        ],
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, paired_df, warm_audit_summary, lite_training_audit, config)

    print("[primary metrics]")
    print(metrics_df.to_string(index=False))
    print("\n[paired]")
    print(paired_df.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
