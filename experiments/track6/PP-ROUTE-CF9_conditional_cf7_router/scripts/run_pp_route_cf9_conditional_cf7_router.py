#!/usr/bin/env python3
"""PP-ROUTE-CF9: conditional router for the CF7 Warm-lite tail guard.

CF7 improves tail metrics when applied globally, but it hurts MdAPE. This
experiment searches validation-only routing rules:

- default prediction: current Warm-lite correction
- routed prediction: CF7 stronger residual correction

The selected rules are then evaluated on:
1. full-history Warm fixed-test rows;
2. k=1..6 capped-history stress rows;
3. native Warm-lite Q1/Q2 outputs where residual-only routers can be applied.
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
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF9_conditional_cf7_router"
CF5 = REPO / "experiments" / "track6" / "PP-ROUTE-CF5_unified_warm_lite_operational_comparison"
CF7 = REPO / "experiments" / "track6" / "PP-ROUTE-CF7_warm_lite_tail_guard"
Q6 = REPO / "experiments" / "track6" / "PP-WLITE-Q6_cf7_candidate_native_validation"

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
    return out


def cf7_pred_from_frame(frame: pd.DataFrame) -> np.ndarray:
    if "qavg_log" in frame.columns:
        qavg = frame["qavg_log"].to_numpy(dtype=float)
    elif "lgbq_full_lean_avg_pred_log" in frame.columns:
        qavg = frame["lgbq_full_lean_avg_pred_log"].to_numpy(dtype=float)
    else:
        qavg = 0.50 * frame["q50_full_log"].to_numpy(dtype=float) + 0.50 * frame["q50_lean_log"].to_numpy(dtype=float)
    residual_col = "lgb_huber_residual_log" if "lgb_huber_residual_log" in frame.columns else "lgb_residual_log"
    residual = frame[residual_col].to_numpy(dtype=float)
    return qavg + np.clip(CF7_STRENGTH * residual, -CF7_CAP, CF7_CAP)


def prepare_router_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "current_pred_log" in out.columns:
        out["current_pred_log"] = out["current_pred_log"].to_numpy(dtype=float)
    elif "qavg_lgbres_s05_cap010_current_pred_log" in out.columns:
        out["current_pred_log"] = out["qavg_lgbres_s05_cap010_current_pred_log"].to_numpy(dtype=float)
    elif "pred_log" in out.columns:
        out["current_pred_log"] = out["pred_log"].to_numpy(dtype=float)
    else:
        raise KeyError("Cannot find current prediction column")
    out["cf7_pred_log"] = cf7_pred_from_frame(out)
    residual_col = "lgb_huber_residual_log" if "lgb_huber_residual_log" in out.columns else "lgb_residual_log"
    out["router_residual_log"] = out[residual_col].to_numpy(dtype=float)
    if "quantile_uncertainty_width_log" not in out.columns:
        out["quantile_uncertainty_width_log"] = np.nan
    if "full_lean_gap_abs_log" not in out.columns:
        if "q50_full_log" in out.columns and "q50_lean_log" in out.columns:
            out["full_lean_gap_abs_log"] = np.abs(out["q50_full_log"].to_numpy(dtype=float) - out["q50_lean_log"].to_numpy(dtype=float))
        else:
            out["full_lean_gap_abs_log"] = np.nan
    if "full_train_artist_history_n" not in out.columns:
        if "artist_history_n" in out.columns:
            out["full_train_artist_history_n"] = out["artist_history_n"].to_numpy(dtype=float)
        elif "history_k" in out.columns:
            out["full_train_artist_history_n"] = out["history_k"].to_numpy(dtype=float)
        else:
            out["full_train_artist_history_n"] = np.nan
    out["abs_residual_log"] = np.abs(out["router_residual_log"].to_numpy(dtype=float))
    return out


def build_specs(validation: pd.DataFrame) -> list[dict[str, Any]]:
    width_qs = {
        q: float(np.nanquantile(validation["quantile_uncertainty_width_log"], q))
        for q in [0.50, 0.60, 0.67, 0.75, 0.80, 0.90]
        if validation["quantile_uncertainty_width_log"].notna().any()
    }
    gap_qs = {
        q: float(np.nanquantile(validation["full_lean_gap_abs_log"], q))
        for q in [0.50, 0.67, 0.75, 0.80, 0.90]
        if validation["full_lean_gap_abs_log"].notna().any()
    }
    abs_qs = {
        q: float(np.nanquantile(validation["abs_residual_log"], q))
        for q in [0.50, 0.67, 0.75, 0.80, 0.90]
    }
    specs: list[dict[str, Any]] = [
        {"name": "current", "family": "reference"},
        {"name": "cf7_all", "family": "reference"},
        {"name": "route_residual_down", "family": "residual_direction", "direction": "down"},
        {"name": "route_residual_up", "family": "residual_direction", "direction": "up"},
    ]
    for q, threshold in width_qs.items():
        specs.append(
            {
                "name": f"route_width_q{int(q * 100)}",
                "family": "width",
                "width_threshold": threshold,
            }
        )
        specs.append(
            {
                "name": f"route_down_width_q{int(q * 100)}",
                "family": "down_and_width",
                "width_threshold": threshold,
            }
        )
        specs.append(
            {
                "name": f"route_down_or_width_q{int(q * 100)}",
                "family": "down_or_width",
                "width_threshold": threshold,
            }
        )
    for q, threshold in gap_qs.items():
        specs.append(
            {
                "name": f"route_gap_q{int(q * 100)}",
                "family": "gap",
                "gap_threshold": threshold,
            }
        )
        specs.append(
            {
                "name": f"route_down_gap_q{int(q * 100)}",
                "family": "down_and_gap",
                "gap_threshold": threshold,
            }
        )
    for q, threshold in abs_qs.items():
        specs.append(
            {
                "name": f"route_absres_q{int(q * 100)}",
                "family": "absres",
                "abs_threshold": threshold,
            }
        )
        specs.append(
            {
                "name": f"route_down_absres_q{int(q * 100)}",
                "family": "down_and_absres",
                "abs_threshold": threshold,
            }
        )
    for hist_max in [5, 10, 20]:
        specs.append(
            {
                "name": f"route_down_lowhist{hist_max}",
                "family": "down_and_low_history",
                "history_max": hist_max,
            }
        )
    return specs


def route_mask(frame: pd.DataFrame, spec: dict[str, Any]) -> np.ndarray:
    family = spec["family"]
    residual = frame["router_residual_log"].to_numpy(dtype=float)
    width = frame["quantile_uncertainty_width_log"].to_numpy(dtype=float)
    gap = frame["full_lean_gap_abs_log"].to_numpy(dtype=float)
    absres = frame["abs_residual_log"].to_numpy(dtype=float)
    hist = frame["full_train_artist_history_n"].to_numpy(dtype=float)
    down = residual < 0
    up = residual > 0
    if spec["name"] == "current":
        return np.zeros(len(frame), dtype=bool)
    if spec["name"] == "cf7_all":
        return np.ones(len(frame), dtype=bool)
    if family == "native_reference":
        return np.ones(len(frame), dtype=bool) if "cf7" in spec["name"] else np.zeros(len(frame), dtype=bool)
    if family == "residual_direction":
        return down if spec["direction"] == "down" else up
    if family == "width":
        return width >= float(spec["width_threshold"])
    if family == "down_and_width":
        return down & (width >= float(spec["width_threshold"]))
    if family == "down_or_width":
        return down | (width >= float(spec["width_threshold"]))
    if family == "gap":
        return gap >= float(spec["gap_threshold"])
    if family == "down_and_gap":
        return down & (gap >= float(spec["gap_threshold"]))
    if family == "absres":
        return absres >= float(spec["abs_threshold"])
    if family == "down_and_absres":
        return down & (absres >= float(spec["abs_threshold"]))
    if family == "down_and_low_history":
        return down & (hist <= float(spec["history_max"]))
    raise ValueError(f"Unknown spec: {spec}")


def apply_router(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    mask = route_mask(frame, spec)
    pred = frame["current_pred_log"].to_numpy(dtype=float).copy()
    pred[mask] = frame["cf7_pred_log"].to_numpy(dtype=float)[mask]
    return pred, mask


def evaluate_specs(split: str, frame: pd.DataFrame, specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    preds = []
    for spec in specs:
        pred, mask = apply_router(frame, spec)
        row = {
            "split": split,
            "candidate": spec["name"],
            "family": spec["family"],
            "route_share": float(np.mean(mask)),
            "spec": json.dumps(spec, ensure_ascii=False, sort_keys=True),
        }
        row.update(metrics(frame["actual_price"].to_numpy(), frame["actual_log"].to_numpy(), pred))
        rows.append(row)
        part = frame[["_track6_row_id", "actual_price", "actual_log"]].copy()
        if "artist_key" in frame.columns:
            part["artist_key"] = frame["artist_key"].to_numpy()
        part["split"] = split
        part["candidate"] = spec["name"]
        part["pred_log"] = pred
        part["route_to_cf7"] = mask
        preds.append(part)
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def select_candidates(validation_metrics: pd.DataFrame) -> pd.DataFrame:
    current = validation_metrics[validation_metrics["candidate"].eq("current")].iloc[0]
    candidates = validation_metrics.copy()
    candidates["delta_MdAPE"] = candidates["MdAPE"] - float(current["MdAPE"])
    candidates["delta_MAPE"] = candidates["MAPE"] - float(current["MAPE"])
    candidates["delta_p95_APE"] = candidates["p95_APE"] - float(current["p95_APE"])
    candidates["delta_RMSE_log"] = candidates["RMSE_log"] - float(current["RMSE_log"])
    candidates["strict_guard"] = (candidates["delta_MdAPE"] <= 0.001) & (candidates["delta_MAPE"] <= 0.001)
    candidates["loose_guard"] = (candidates["delta_MdAPE"] <= 0.003) & (candidates["delta_MAPE"] <= 0.002)
    candidates["balanced_score"] = (
        candidates["delta_p95_APE"]
        + 5.0 * candidates["delta_RMSE_log"]
        + 6.0 * np.maximum(candidates["delta_MdAPE"], 0)
        + 4.0 * np.maximum(candidates["delta_MAPE"], 0)
    )
    selected_parts = []
    strict = candidates[candidates["strict_guard"] & ~candidates["candidate"].isin(["current", "cf7_all"])].copy()
    loose = candidates[candidates["loose_guard"] & ~candidates["candidate"].isin(["current"])].copy()
    if not strict.empty:
        a = strict.sort_values(["p95_APE", "RMSE_log", "MAPE", "MdAPE"]).head(1).copy()
        a["selection_reason"] = "best_validation_p95_strict_guard"
        selected_parts.append(a)
        b = strict.sort_values(["RMSE_log", "p95_APE", "MAPE", "MdAPE"]).head(1).copy()
        b["selection_reason"] = "best_validation_rmse_strict_guard"
        selected_parts.append(b)
    if not loose.empty:
        c = loose.sort_values(["balanced_score", "p95_APE", "RMSE_log"]).head(1).copy()
        c["selection_reason"] = "best_validation_balanced_score_loose_guard"
        selected_parts.append(c)
    selected = pd.concat(selected_parts, ignore_index=True).drop_duplicates("candidate")
    return selected.reset_index(drop=True)


def load_full_history() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = pd.read_csv(CF7 / "outputs" / "seed_mean_feature_predictions.csv", low_memory=False)
    data = prepare_router_frame(data)
    val = data[data["split"].eq("validation")].copy().reset_index(drop=True)
    test = data[data["split"].eq("test")].copy().reset_index(drop=True)
    warm = pd.read_csv(CF5 / "outputs" / "warm_operational_full_history_predictions.csv", low_memory=False)
    warm = warm[["_track6_row_id", "pred_log"]].rename(columns={"pred_log": "warm_wmin8_pred_log"})
    test = test.merge(warm, on="_track6_row_id", how="left", validate="one_to_one")
    return val, test


def full_history_reference_metrics(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate, col in [
        ("Warm WMIN8 operational", "warm_wmin8_pred_log"),
        ("Warm-lite current", "current_pred_log"),
        ("Warm-lite CF7 all", "cf7_pred_log"),
    ]:
        row = {"candidate": candidate}
        row.update(metrics(test["actual_price"].to_numpy(), test["actual_log"].to_numpy(), test[col].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows)


def load_capped_predictions(selected_specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(CF5 / "outputs" / "capped_predictions_all_conditions.csv", low_memory=False)
    warm = raw[raw["candidate"].eq("Warm retrained clean stack")].copy()
    warm = warm[["_track6_row_id", "artist_key", "actual_price", "actual_log", "trunc_seed", "k", "pred_log"]]
    warm["candidate"] = "Warm retrained clean stack"

    lite = raw[raw["candidate"].eq("Warm-lite unified full-history retrained")].copy()
    lite = prepare_router_frame(lite)
    parts = [warm]
    for spec in [{"name": "current", "family": "reference"}, {"name": "cf7_all", "family": "reference"}] + selected_specs:
        pred, mask = apply_router(lite, spec)
        part = lite[["_track6_row_id", "artist_key", "actual_price", "actual_log", "trunc_seed", "k"]].copy()
        part["candidate"] = spec["name"]
        part["pred_log"] = pred
        part["route_to_cf7"] = mask
        parts.append(part)
    seed_level = pd.concat(parts, ignore_index=True, sort=False)
    seed_mean = (
        seed_level.groupby(["candidate", "k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            pred_log=("pred_log", "mean"),
            route_share=("route_to_cf7", "mean"),
            seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "candidate", "_track6_row_id"])
        .reset_index(drop=True)
    )
    return seed_level, seed_mean


def capped_metrics(seed_mean: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, k), group in seed_mean.groupby(["candidate", "k"], sort=True):
        row = {"candidate": candidate, "k": int(k), "condition": f"k={int(k)} seed-mean", "route_share": float(group["route_share"].mean())}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out.groupby("k")[metric].rank(method="min").astype(int)
    return out.sort_values(["k", "candidate"]).reset_index(drop=True)


def native_residual_router_metrics() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not Q6.exists():
        return pd.DataFrame(), pd.DataFrame()
    q1 = pd.read_csv(Q6 / "outputs" / "q1_predictions_all_seeds.csv", low_memory=False)
    q2 = pd.read_csv(Q6 / "outputs" / "q2_predictions_all_conditions.csv", low_memory=False)
    rows = []
    for label, frame, group_col in [
        ("q1_native", q1, "history_k"),
        ("q2_native", q2, "k"),
    ]:
        f = prepare_router_frame(frame)
        specs = [
            {"name": "native_current", "family": "native_reference"},
            {"name": "native_cf7_all", "family": "native_reference"},
            {"name": "native_route_residual_down", "family": "residual_direction", "direction": "down"},
        ]
        for spec in specs:
            pred, mask = apply_router(f, spec)
            row = {"scope": label, "group": "overall", "candidate": spec["name"], "route_share": float(np.mean(mask))}
            row.update(metrics(f["actual_price"].to_numpy(), f["actual_log"].to_numpy(), pred))
            rows.append(row)
            for key, group in f.groupby(group_col, sort=True):
                pred_g, mask_g = apply_router(group, spec)
                grow = {"scope": label, "group": f"{group_col}={int(key)}", "candidate": spec["name"], "route_share": float(np.mean(mask_g))}
                grow.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), pred_g))
                rows.append(grow)
    all_rows = pd.DataFrame(rows)
    overall = all_rows[all_rows["group"].eq("overall")].copy()
    return all_rows, overall


def write_report(
    val_metrics: pd.DataFrame,
    selected: pd.DataFrame,
    test_ref: pd.DataFrame,
    test_selected: pd.DataFrame,
    capped_m: pd.DataFrame,
    native_overall: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    lines = [
        "# PP-ROUTE-CF9 Conditional CF7 Router",
        "",
        "## 1. 목적",
        "",
        "Warm-lite current를 기본으로 유지하고, validation에서 선택한 조건에서만 CF7 tail guard를 적용한다.",
        "",
        "## 2. Validation Top Candidates",
        "",
        md_table(val_metrics.sort_values(["p95_APE", "RMSE_log", "MAPE", "MdAPE"]).head(20), ["candidate", "family", "route_share", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 3. Selected Routers",
        "",
        md_table(selected, ["candidate", "family", "selection_reason", "route_share", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE", "delta_MAPE", "delta_p95_APE", "delta_RMSE_log"], 10),
        "",
        "## 4. Full-History Test References",
        "",
        md_table(test_ref, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 10),
        "",
        "## 5. Full-History Selected Router Test Metrics",
        "",
        md_table(test_selected, ["candidate", "family", "route_share", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 10),
        "",
        "## 6. k=1~6 Stress Metrics",
        "",
        md_table(capped_m, ["candidate", "condition", "route_share", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"], 120),
        "",
        "## 7. Native Warm-lite Residual-Down Router Overall",
        "",
        md_table(native_overall, ["scope", "candidate", "route_share", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"], 20),
        "",
        "## 8. Config",
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

    val, test = load_full_history()
    specs = build_specs(val)
    val_metrics, val_preds = evaluate_specs("validation", val, specs)
    selected = select_candidates(val_metrics)
    selected_specs = [json.loads(s) for s in selected["spec"].tolist()]

    test_metrics, test_preds = evaluate_specs("test", test, specs)
    test_ref = full_history_reference_metrics(test)
    test_selected = test_metrics[test_metrics["candidate"].isin(selected["candidate"])].copy()

    capped_seed, capped_mean = load_capped_predictions(selected_specs)
    capped_m = capped_metrics(capped_mean)

    native_all, native_overall = native_residual_router_metrics()

    val_metrics.to_csv(EXP / "outputs" / "validation_router_candidate_metrics.csv", index=False)
    val_preds.to_csv(EXP / "outputs" / "validation_router_candidate_predictions.csv", index=False)
    selected.to_csv(EXP / "outputs" / "selected_routers_from_validation.csv", index=False)
    test_metrics.to_csv(EXP / "outputs" / "test_router_candidate_metrics.csv", index=False)
    test_preds.to_csv(EXP / "outputs" / "test_router_candidate_predictions.csv", index=False)
    test_ref.to_csv(EXP / "outputs" / "test_reference_metrics.csv", index=False)
    test_selected.to_csv(EXP / "outputs" / "selected_router_test_metrics.csv", index=False)
    capped_seed.to_csv(EXP / "outputs" / "capped_router_seed_level_predictions.csv", index=False)
    capped_mean.to_csv(EXP / "outputs" / "capped_router_seed_mean_predictions.csv", index=False)
    capped_m.to_csv(EXP / "outputs" / "capped_router_metrics_by_k.csv", index=False)
    native_all.to_csv(EXP / "outputs" / "native_residual_down_router_metrics.csv", index=False)
    native_overall.to_csv(EXP / "outputs" / "native_residual_down_router_overall.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF9",
        "experiment_slug": EXP.name,
        "source_experiments": [
            str(CF5.relative_to(REPO)),
            str(CF7.relative_to(REPO)),
            str(Q6.relative_to(REPO)) if Q6.exists() else None,
        ],
        "default_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
        "routed_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
        "selection_rule": "validation only; strict guard MdAPE<=current+0.001 and MAPE<=current+0.001, plus loose balanced score",
        "candidate_count": int(len(specs)),
        "seconds": round(time.time() - start, 2),
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(val_metrics, selected, test_ref, test_selected, capped_m, native_overall, config)

    print("[selected routers]")
    print(selected.to_string(index=False))
    print("\n[test references]")
    print(test_ref.to_string(index=False))
    print("\n[selected test metrics]")
    print(test_selected.to_string(index=False))
    print("\n[capped metrics]")
    print(capped_m.to_string(index=False))
    print("\n[native overall]")
    print(native_overall.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
