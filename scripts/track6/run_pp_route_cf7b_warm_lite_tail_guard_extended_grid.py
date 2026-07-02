#!/usr/bin/env python3
"""PP-ROUTE-CF7B: extended residual grid over CF7 predictions.

CF7 selected strength=1.00, cap=0.150 on validation. Because that was the
largest cap searched in CF7, this follow-up reuses the CF7 seed-mean prediction
features and searches a wider residual correction grid without retraining.
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
SRC = REPO / "experiments" / "track6" / "PP-ROUTE-CF7_warm_lite_tail_guard"
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF7B_warm_lite_tail_guard_extended_grid"


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
    return out


def residual_values(frame: pd.DataFrame, source: str) -> np.ndarray:
    if source == "lgb":
        return frame["lgb_huber_residual_log"].to_numpy(dtype=float)
    if source == "catboost":
        return frame["catboost_residual_log"].to_numpy(dtype=float)
    if source == "avg":
        return 0.50 * frame["lgb_huber_residual_log"].to_numpy(dtype=float) + 0.50 * frame["catboost_residual_log"].to_numpy(dtype=float)
    raise ValueError(source)


def candidate_specs() -> list[dict[str, Any]]:
    specs = [
        {"name": "current_s05_cap010", "source": "lgb", "strength": 0.50, "cap_pos": 0.10, "cap_neg": 0.10},
    ]
    for source in ["lgb", "catboost", "avg"]:
        for strength in [0.50, 0.75, 1.00, 1.25, 1.50]:
            for cap in [0.10, 0.15, 0.20, 0.25, 0.30]:
                specs.append(
                    {
                        "name": f"{source}_s{strength:.2f}_cap{cap:.3f}".replace(".", "p"),
                        "source": source,
                        "strength": strength,
                        "cap_pos": cap,
                        "cap_neg": cap,
                    }
                )
    for source in ["lgb", "avg"]:
        for strength in [0.75, 1.00, 1.25]:
            for cap_neg in [0.15, 0.20, 0.25, 0.30]:
                for cap_pos in [0.10, 0.15, 0.20, 0.25]:
                    specs.append(
                        {
                            "name": f"{source}_asym_s{strength:.2f}_neg{cap_neg:.3f}_pos{cap_pos:.3f}".replace(".", "p"),
                            "source": source,
                            "strength": strength,
                            "cap_pos": cap_pos,
                            "cap_neg": cap_neg,
                        }
                    )
    return list({spec["name"]: spec for spec in specs}.values())


def apply_candidate(frame: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    residual = residual_values(frame, str(spec["source"]))
    corr = float(spec["strength"]) * residual
    corr = np.minimum(np.maximum(corr, -float(spec["cap_neg"])), float(spec["cap_pos"]))
    return frame["qavg_log"].to_numpy(dtype=float) + corr


def evaluate(frame: pd.DataFrame, split: str, specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_parts = []
    for spec in specs:
        pred = apply_candidate(frame, spec)
        row = {
            "split": split,
            "candidate": spec["name"],
            "source": spec["source"],
            "strength": float(spec["strength"]),
            "cap_pos": float(spec["cap_pos"]),
            "cap_neg": float(spec["cap_neg"]),
            "spec": json.dumps(spec, ensure_ascii=False, sort_keys=True),
        }
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), pred))
        rows.append(row)
        part = frame[["_track6_row_id", "actual_price", "actual_log"]].copy()
        part["split"] = split
        part["candidate"] = spec["name"]
        part["pred_log"] = pred
        pred_parts.append(part)
    return pd.DataFrame(rows), pd.concat(pred_parts, ignore_index=True)


def select_candidates(validation_metrics: pd.DataFrame) -> pd.DataFrame:
    current = validation_metrics[validation_metrics["candidate"].eq("current_s05_cap010")].iloc[0]
    candidates = validation_metrics.copy()
    candidates["passes_balance_guard"] = (
        (candidates["MAPE"] <= float(current["MAPE"]) + 0.005)
        & (candidates["MdAPE"] <= float(current["MdAPE"]) + 0.005)
    )
    guarded = candidates[candidates["passes_balance_guard"]].copy()
    if guarded.empty:
        guarded = candidates.copy()
    best_p95 = guarded.sort_values(["p95_APE", "MAPE", "MdAPE"], ascending=True).head(1).copy()
    best_mape = candidates.sort_values(["MAPE", "p95_APE", "MdAPE"], ascending=True).head(1).copy()
    best_rmse = guarded.sort_values(["RMSE_log", "MAPE", "p95_APE"], ascending=True).head(1).copy()
    selected = pd.concat([best_p95, best_mape, best_rmse], ignore_index=True)
    selected["selection_reason"] = ["best_validation_p95_with_balance_guard", "best_validation_mape", "best_validation_rmse_with_balance_guard"][: len(selected)]
    return selected.drop_duplicates("candidate").reset_index(drop=True)


def paired_vs_current(frame: pd.DataFrame, selected_preds: pd.DataFrame) -> pd.DataFrame:
    base = frame[["_track6_row_id", "actual_price", "actual_log", "current_pred_log"]].copy()
    base = add_ape(base, "current_pred_log", "current_ape")
    rows = []
    for candidate, part in selected_preds.groupby("candidate", sort=True):
        wide = base.merge(
            part[["_track6_row_id", "pred_log"]],
            on="_track6_row_id",
            how="inner",
            validate="one_to_one",
        )
        wide = add_ape(wide, "pred_log", "candidate_ape")
        rows.append(
            {
                "candidate": candidate,
                "n": int(len(wide)),
                "candidate_better_share": float(np.mean(wide["candidate_ape"] < wide["current_ape"])),
                "current_better_share": float(np.mean(wide["current_ape"] < wide["candidate_ape"])),
                "median_ape_delta_current_minus_candidate": float(np.nanmedian(wide["current_ape"] - wide["candidate_ape"])),
                "mean_ape_delta_current_minus_candidate": float(np.nanmean(wide["current_ape"] - wide["candidate_ape"])),
            }
        )
    return pd.DataFrame(rows)


def write_report(
    val_metrics: pd.DataFrame,
    test_metrics: pd.DataFrame,
    selected: pd.DataFrame,
    selected_test: pd.DataFrame,
    paired_test: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    lines = [
        "# PP-ROUTE-CF7B Warm-lite Tail Guard Extended Grid",
        "",
        "## 1. 목적",
        "",
        "CF7에서 선택 후보가 residual cap grid의 상한에 걸렸기 때문에, 재학습 없이 보정 강도와 cap 범위를 확장해 확인한다.",
        "",
        "## 2. Validation Top Candidates by p95",
        "",
        md_table(val_metrics.sort_values(["p95_APE", "MAPE", "MdAPE"]).head(20), ["candidate", "source", "strength", "cap_neg", "cap_pos", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 3. Selected Candidates",
        "",
        md_table(selected, ["candidate", "source", "strength", "cap_neg", "cap_pos", "selection_reason", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 10),
        "",
        "## 4. Selected Candidate Test Metrics",
        "",
        md_table(selected_test.sort_values(["p95_APE", "MAPE", "MdAPE"]), ["candidate", "source", "strength", "cap_neg", "cap_pos", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 5. Test Paired vs Current",
        "",
        md_table(paired_test, ["candidate", "n", "candidate_better_share", "current_better_share", "median_ape_delta_current_minus_candidate", "mean_ape_delta_current_minus_candidate"], 20),
        "",
        "## 6. Config",
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
    source_path = SRC / "outputs" / "seed_mean_feature_predictions.csv"
    if not source_path.exists():
        raise FileNotFoundError(f"Run CF7 first: {source_path}")
    data = pd.read_csv(source_path, low_memory=False)
    val = data[data["split"].eq("validation")].copy().reset_index(drop=True)
    test = data[data["split"].eq("test")].copy().reset_index(drop=True)
    specs = candidate_specs()
    val_metrics, val_preds = evaluate(val, "validation", specs)
    test_metrics, test_preds = evaluate(test, "test", specs)
    selected = select_candidates(val_metrics)
    selected_test = test_metrics[test_metrics["candidate"].isin(selected["candidate"])].copy()
    paired_test = paired_vs_current(test, test_preds[test_preds["candidate"].isin(selected["candidate"])].copy())

    val_metrics.to_csv(EXP / "outputs" / "validation_extended_grid_metrics.csv", index=False)
    test_metrics.to_csv(EXP / "outputs" / "test_extended_grid_metrics.csv", index=False)
    selected.to_csv(EXP / "outputs" / "selected_candidates_from_validation.csv", index=False)
    selected_test.to_csv(EXP / "outputs" / "selected_candidates_test_metrics.csv", index=False)
    paired_test.to_csv(EXP / "outputs" / "selected_candidates_test_paired_vs_current.csv", index=False)
    val_preds.to_csv(EXP / "outputs" / "validation_extended_grid_predictions.csv", index=False)
    test_preds.to_csv(EXP / "outputs" / "test_extended_grid_predictions.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF7B",
        "experiment_slug": EXP.name,
        "source_experiment": str(SRC.relative_to(REPO)),
        "source_predictions": str(source_path.relative_to(REPO)),
        "selection_rule": "Choose on validation. p95 candidates must keep MAPE and MdAPE within +0.005 absolute of current_s05_cap010.",
        "candidate_count": int(len(specs)),
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(val_metrics, test_metrics, selected, selected_test, paired_test, config)

    print("[selected candidates from validation]")
    print(selected.to_string(index=False))
    print("\n[test selected metrics]")
    print(selected_test.sort_values(["p95_APE", "MAPE", "MdAPE"]).to_string(index=False))
    print("\n[test paired vs current]")
    print(paired_test.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
