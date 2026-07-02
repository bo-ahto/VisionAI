#!/usr/bin/env python3
"""PP-ROUTE-CF1: same-row history exposure counterfactual.

Purpose:
- Compare Warm, Warm-lite, and Cold on the same 607 Warm fixed-test artworks.
- Vary only available same-artist price history exposure:
  * Warm: final WMIN8 prediction on 5+ history route.
  * Warm-lite: same rows with same-artist train history truncated to k=1..4,
    using the adopted Quantile + LightGBM Huber residual candidate from Q4.
  * Cold: same rows with same-artist price history hidden, using frozen Cold v0.5.

This is a route-boundary explanation experiment, not a replacement for each
route's native operating benchmark.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import GENERATED, SPLIT_ROOT, add_generated, artifact_features, load_scope, read_join  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP = REPO / "experiments" / "track6" / "PP-ROUTE-CF1_same_row_history_exposure_counterfactual"

WARM_WMIN8 = REPO / "models" / "track6" / "warm_wmin8_operational_candidate" / "artifacts" / "wmin8_selected_candidate_predictions.csv"
WLITE_Q4 = REPO / "experiments" / "track6" / "PP-WLITE-Q4_quantile_final_comparison" / "outputs" / "q2_final_comparison_rows.csv"
COLD_PREDICTOR = REPO / "models" / "track6" / "cold_prediction_v0.5_operational" / "predict" / "predict_cold_operational_v0_5.py"

WARM_CANDIDATE = "min1_route_w850_risk_q50_altlower_gap005"
WLITE_CANDIDATE_COL = "residual_lgb_s05_cap010"


def ensure_dirs() -> None:
    for sub in ("artifacts", "outputs", "reports", "logs", "scripts"):
        (EXP / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), EXP / "scripts" / Path(__file__).name)


def load_cold_module():
    spec = importlib.util.spec_from_file_location("cold_v05", COLD_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import Cold predictor from {COLD_PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    pred_price = np.clip(np.exp(out[pred_col].astype(float)), 1_000.0, None)
    out[out_col] = np.abs(pred_price - out["actual_price"].astype(float)) / np.clip(out["actual_price"].astype(float), 1.0, None)
    return out


def load_warm_predictions() -> pd.DataFrame:
    raw = pd.read_csv(WARM_WMIN8, low_memory=False)
    warm = raw[
        raw["eval_split"].eq("test")
        & raw["candidate_label"].eq(WARM_CANDIDATE)
    ].copy()
    if warm["_track6_row_id"].nunique() != len(warm):
        raise RuntimeError("Warm WMIN8 test predictions are not unique by _track6_row_id")
    cols = ["_track6_row_id", "artist_key", "actual_price", "actual_log", "pred_log"]
    warm = warm[cols].rename(columns={"pred_log": "warm_wmin8_pred_log"}).sort_values("_track6_row_id").reset_index(drop=True)
    if len(warm) != 607:
        raise RuntimeError(f"Expected 607 Warm fixed-test rows, got {len(warm)}")
    return warm


def load_warm_lite_seed_mean() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(WLITE_Q4)
    required = {"trunc_seed", "k", "_track6_row_id", "artist_key", "actual_price", "actual_log", WLITE_CANDIDATE_COL}
    missing = required - set(raw.columns)
    if missing:
        raise RuntimeError(f"Warm-lite Q4 output missing columns: {sorted(missing)}")

    condition = raw[
        ["trunc_seed", "k", "_track6_row_id", "artist_key", "actual_price", "actual_log", "artist_history_n", WLITE_CANDIDATE_COL]
    ].rename(columns={WLITE_CANDIDATE_COL: "warm_lite_pred_log"}).copy()
    condition["candidate"] = condition["k"].map(lambda k: f"warm_lite_k{int(k)}")

    seed_mean = (
        condition.groupby(["k", "_track6_row_id"], as_index=False)
        .agg(
            artist_key=("artist_key", "first"),
            actual_price=("actual_price", "first"),
            actual_log=("actual_log", "first"),
            warm_lite_pred_log=("warm_lite_pred_log", "mean"),
            trunc_seed_n=("trunc_seed", "nunique"),
        )
        .sort_values(["k", "_track6_row_id"])
        .reset_index(drop=True)
    )
    if not seed_mean["trunc_seed_n"].eq(3).all():
        raise RuntimeError("Expected three Warm-lite truncation seeds per row/k")
    return seed_mean, condition


def warm_test_frame_with_cold_buckets(cold_module) -> pd.DataFrame:
    cold_train, _cold_val, _cold_test = load_scope("cold", cold_module.REQUIRED)

    feature_path = SPLIT_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv"
    label_path = SPLIT_ROOT / "labels" / "track6_test_warm_labels.csv"
    generation_inputs = ["area_cm2", "log_area", "aspect_ratio", "is_3d_candidate", "medium_category", "support_category"]
    raw_cols = list(dict.fromkeys([c for c in cold_module.REQUIRED if c not in GENERATED] + generation_inputs))
    warm_raw = read_join(feature_path, label_path, raw_cols)
    _cold_train_rebucketed, warm_cold_buckets = add_generated(cold_train, warm_raw)
    return warm_cold_buckets.sort_values("_track6_row_id").reset_index(drop=True)


def load_forced_cold_predictions(warm_ids: set[int]) -> pd.DataFrame:
    cold = load_cold_module()
    frame = warm_test_frame_with_cold_buckets(cold)
    if set(frame["_track6_row_id"]) != warm_ids:
        missing = sorted(warm_ids - set(frame["_track6_row_id"]))
        extra = sorted(set(frame["_track6_row_id"]) - warm_ids)
        raise RuntimeError(f"Cold forced frame row mismatch: missing={missing[:5]} extra={extra[:5]}")
    pred = cold.predict(frame)
    out = pred[["_track6_row_id", "defense_pred_log", "qwidth_log", "representative_pred_log", "q40_pred_log"]].copy()
    return out.rename(columns={"defense_pred_log": "cold_forced_pred_log"}).sort_values("_track6_row_id").reset_index(drop=True)


def scope_overlap_audit() -> dict[str, int]:
    feats = artifact_features()
    _wtrain, _wval, wtest = load_scope("warm", feats["warm"])
    ctrain, cval, ctest = load_scope("cold", feats["cold_lightgbm"])
    wids = set(wtest["_track6_row_id"].astype(int))
    return {
        "warm_test_n": int(len(wids)),
        "warm_test_vs_cold_train_overlap": int(len(wids & set(ctrain["_track6_row_id"].astype(int)))),
        "warm_test_vs_cold_val_overlap": int(len(wids & set(cval["_track6_row_id"].astype(int)))),
        "warm_test_vs_cold_test_overlap": int(len(wids & set(ctest["_track6_row_id"].astype(int)))),
    }


def build_wide(warm: pd.DataFrame, wlite_seed_mean: pd.DataFrame, cold: pd.DataFrame) -> pd.DataFrame:
    wide = warm.merge(cold, on="_track6_row_id", how="left", validate="one_to_one")
    for k, group in wlite_seed_mean.groupby("k", sort=True):
        cols = ["_track6_row_id", "warm_lite_pred_log"]
        wide = wide.merge(
            group[cols].rename(columns={"warm_lite_pred_log": f"warm_lite_k{int(k)}_pred_log"}),
            on="_track6_row_id",
            how="left",
            validate="one_to_one",
        )
    pred_cols = ["warm_wmin8_pred_log", "cold_forced_pred_log"] + [f"warm_lite_k{k}_pred_log" for k in [1, 2, 3, 4]]
    for col in pred_cols:
        if wide[col].isna().any():
            raise RuntimeError(f"Missing predictions in {col}: {int(wide[col].isna().sum())}")
    return wide.sort_values("_track6_row_id").reset_index(drop=True)


def same_n_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidates = {
        "Warm WMIN8, 5+ history": "warm_wmin8_pred_log",
        "Warm-lite forced k=1": "warm_lite_k1_pred_log",
        "Warm-lite forced k=2": "warm_lite_k2_pred_log",
        "Warm-lite forced k=3": "warm_lite_k3_pred_log",
        "Warm-lite forced k=4": "warm_lite_k4_pred_log",
        "Cold forced, no same-artist price history": "cold_forced_pred_log",
    }
    for candidate, col in candidates.items():
        row = {"candidate": candidate, "pred_col": col}
        row.update(metrics(wide["actual_price"].to_numpy(), wide["actual_log"].to_numpy(), wide[col].to_numpy()))
        rows.append(row)
    out = pd.DataFrame(rows)
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"rank_{metric}"] = out[metric].rank(method="min").astype(int)
    return out.sort_values(["MAPE", "p95_APE", "MdAPE"]).reset_index(drop=True)


def condition_metrics(condition: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (seed, k), group in condition.groupby(["trunc_seed", "k"], sort=True):
        row = {"trunc_seed": int(seed), "k": int(k), "candidate": f"Warm-lite forced k={int(k)}"}
        row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["warm_lite_pred_log"].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["k", "trunc_seed"]).reset_index(drop=True)


def paired_comparisons(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = wide.copy()
    for col in ["warm_wmin8_pred_log", "cold_forced_pred_log"] + [f"warm_lite_k{k}_pred_log" for k in [1, 2, 3, 4]]:
        df = add_ape(df, col, col.replace("_pred_log", "_ape"))

    pairs: list[tuple[str, str, str, str]] = [
        ("Warm WMIN8", "warm_wmin8_ape", "Cold forced", "cold_forced_ape"),
    ]
    for k in [1, 2, 3, 4]:
        pairs.append(("Warm WMIN8", "warm_wmin8_ape", f"Warm-lite k={k}", f"warm_lite_k{k}_ape"))
        pairs.append((f"Warm-lite k={k}", f"warm_lite_k{k}_ape", "Cold forced", "cold_forced_ape"))

    rows: list[dict[str, Any]] = []
    for a_name, a_col, b_name, b_col in pairs:
        a = df[a_col].to_numpy(dtype=float)
        b = df[b_col].to_numpy(dtype=float)
        rows.append(
            {
                "candidate_a": a_name,
                "candidate_b": b_name,
                "n": int(len(df)),
                "a_better_share": float(np.mean(a < b)),
                "b_better_share": float(np.mean(b < a)),
                "tie_share": float(np.mean(np.isclose(a, b))),
                "median_ape_delta_a_minus_b": float(np.nanmedian(a - b)),
                "mean_ape_delta_a_minus_b": float(np.nanmean(a - b)),
            }
        )
    ape_cols = ["_track6_row_id", "artist_key", "actual_price", "actual_log"] + [
        "warm_wmin8_ape",
        "cold_forced_ape",
        "warm_lite_k1_ape",
        "warm_lite_k2_ape",
        "warm_lite_k3_ape",
        "warm_lite_k4_ape",
    ]
    return pd.DataFrame(rows), df[ape_cols].copy()


def fmt(value: Any) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if np.isfinite(value) and abs(value - round(value)) < 1e-9 and abs(value) >= 1:
            return str(int(round(value)))
        return f"{float(value):.6f}"
    return str(value)


def md_table(frame: pd.DataFrame, cols: list[str]) -> str:
    view = frame[cols].copy()
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in cols) + " |")
    return "\n".join(lines)


def write_report(metrics_df: pd.DataFrame, condition_df: pd.DataFrame, paired_df: pd.DataFrame, config: dict[str, Any]) -> None:
    focused_condition = condition_df.copy()
    by_name = metrics_df.set_index("candidate")
    warm = by_name.loc["Warm WMIN8, 5+ history"]
    cold = by_name.loc["Cold forced, no same-artist price history"]
    k1 = by_name.loc["Warm-lite forced k=1"]
    k4 = by_name.loc["Warm-lite forced k=4"]
    best_by_metric = {
        metric: str(metrics_df.sort_values(metric).iloc[0]["candidate"])
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    }
    lines = [
        "# PP-ROUTE-CF1 Same-Row History Exposure Counterfactual",
        "",
        "## 1. 목적",
        "",
        "Warm fixed-test 607개 동일 작품에 대해 작가 가격 이력 노출량만 바꿔 Warm, Warm-lite, Cold 경로를 비교한다.",
        "",
        "## 2. 해석 범위",
        "",
        "- 같은 작품·같은 n 기준이므로 경로별 native benchmark보다 직접 비교성이 높다.",
        "- Warm-lite는 같은 작품에서 같은 작가 train 이력을 k=1~4로 제한한 강제 시나리오다.",
        "- Cold는 같은 작품에서 같은 작가 가격 이력을 숨긴 강제 시나리오다.",
        "- 이 결과는 라우팅 경계 설명용이며, 실제 Warm-lite/Cold 운영 분포의 성능표를 대체하지 않는다.",
        "",
        "## 3. Same-n metrics",
        "",
        md_table(metrics_df, ["candidate", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "rank_MAPE", "rank_p95_APE"]),
        "",
        "## 4. Observed interpretation",
        "",
        f"- Best by MdAPE: `{best_by_metric['MdAPE']}`.",
        f"- Best by MAPE: `{best_by_metric['MAPE']}`.",
        f"- Best by p95 APE: `{best_by_metric['p95_APE']}`.",
        f"- Best by RMSE log: `{best_by_metric['RMSE_log']}`.",
        f"- Warm WMIN8 vs Warm-lite k=4: MdAPE `{warm['MdAPE']:.6f}` vs `{k4['MdAPE']:.6f}`, MAPE `{warm['MAPE']:.6f}` vs `{k4['MAPE']:.6f}`, p95 `{warm['p95_APE']:.6f}` vs `{k4['p95_APE']:.6f}`.",
        f"- Warm-lite improves as k increases: k=1 MAPE `{k1['MAPE']:.6f}` -> k=4 MAPE `{k4['MAPE']:.6f}`.",
        f"- Cold forced is much harder on the same rows: Cold MAPE `{cold['MAPE']:.6f}`, p95 `{cold['p95_APE']:.6f}`.",
        "",
        "Interpretation: the same-row test supports keeping Cold separate. It also supports that more same-artist history improves prediction stability. Warm WMIN8 remains stronger on median/tail/log-error stability, while Warm-lite k=4 is very close and slightly better on mean APE in this counterfactual. Therefore this result is evidence for route separation, but not a claim that Warm dominates Warm-lite on every metric.",
        "",
        "## 5. Warm-lite repeated condition metrics",
        "",
        md_table(focused_condition, ["trunc_seed", "k", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]),
        "",
        "## 6. Paired row-level comparisons",
        "",
        md_table(paired_df, ["candidate_a", "candidate_b", "n", "a_better_share", "b_better_share", "median_ape_delta_a_minus_b", "mean_ape_delta_a_minus_b"]),
        "",
        "## 7. 주요 해석",
        "",
        "- 5건 이상 이력이 있는 동일 작품에서는 Warm WMIN8이 Warm-lite 강제 k=1~4보다 전체적으로 낮은 오차를 보이는지 확인한다.",
        "- Warm-lite k가 커질수록 성능이 개선되는지 확인해, 이력 수 증가가 가격 예측 안정성에 주는 효과를 본다.",
        "- Cold forced 결과는 같은 작가 가격 이력을 숨겼을 때 난이도가 얼마나 올라가는지 보여주는 하한 비교다.",
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
    ensure_dirs()
    warm = load_warm_predictions()
    wlite_seed_mean, wlite_condition = load_warm_lite_seed_mean()
    cold = load_forced_cold_predictions(set(warm["_track6_row_id"].astype(int)))
    wide = build_wide(warm, wlite_seed_mean, cold)

    metrics_df = same_n_metrics(wide)
    condition_df = condition_metrics(wlite_condition)
    paired_df, row_ape_df = paired_comparisons(wide)
    overlap = scope_overlap_audit()

    wide.to_csv(EXP / "outputs" / "same_row_predictions_wide.csv", index=False)
    metrics_df.to_csv(EXP / "outputs" / "same_n_metrics.csv", index=False)
    condition_df.to_csv(EXP / "outputs" / "warm_lite_repeated_condition_metrics.csv", index=False)
    paired_df.to_csv(EXP / "outputs" / "paired_row_level_comparisons.csv", index=False)
    row_ape_df.to_csv(EXP / "outputs" / "row_level_ape.csv", index=False)
    wlite_condition.to_csv(EXP / "outputs" / "warm_lite_condition_predictions.csv", index=False)
    cold.to_csv(EXP / "outputs" / "cold_forced_predictions.csv", index=False)

    config = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "PP-ROUTE-CF1",
        "experiment_slug": EXP.name,
        "evaluation_rows": int(len(wide)),
        "base_eval_set": "Warm fixed-test rows",
        "warm_source": str(WARM_WMIN8.relative_to(REPO)),
        "warm_candidate": WARM_CANDIDATE,
        "warm_lite_source": str(WLITE_Q4.relative_to(REPO)),
        "warm_lite_candidate": WLITE_CANDIDATE_COL,
        "warm_lite_design": "same Warm fixed-test rows, same-artist train history truncated to k=1..4, three truncation seeds, seed-mean for same-n table",
        "cold_source": str(COLD_PREDICTOR.relative_to(REPO)),
        "cold_design": "same Warm fixed-test rows, no same-artist price history, cold-train bucket generation basis, frozen Cold v0.5",
        "scope_overlap_audit": overlap,
        "limitations": [
            "Counterfactual on Warm fixed-test distribution; does not replace native Warm-lite/Cold operating benchmark.",
            "Warm-lite same-n table averages three truncation seeds per row/k.",
            "Cold forced comparison hides same-artist price history but still evaluates on Warm fixed-test artwork distribution.",
        ],
    }
    (EXP / "artifacts" / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, condition_df, paired_df, config)

    print("[same-n metrics]")
    print(metrics_df.to_string(index=False))
    print("\n[paired comparisons]")
    print(paired_df.to_string(index=False))
    print("\n[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
