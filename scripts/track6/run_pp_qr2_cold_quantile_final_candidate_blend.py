#!/usr/bin/env python3
"""Run PP-QR2 Cold final-candidate + quantile guard blend experiment.

PP-QR1 showed that CatBoost Quantile q50 is a better representative quantile
candidate, while q40 is useful for MAPE/p95 defense. PP-QR2 checks whether those
signals can improve the current Cold final candidates instead of standing alone.
"""
from __future__ import annotations

import html
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, REPO, metrics  # noqa: E402


EXP_ID = "PP-QR2"
SLUG = "PP-QR2_cold_quantile_final_candidate_blend"
TITLE = "Cold 최종 후보 + Quantile q40/q50 결합/라우팅 검증"
DOC_PATH = REPO / "docs" / "track6" / "experiments" / "pp_qr2_cold_quantile_final_candidate_blend_summary.md"

Y18_PATH = BASE_EXP_DIR / "PP-Y18_cold_y16_top_candidate_stability" / "outputs" / "predictions.csv"
Y2_PATH = BASE_EXP_DIR / "PP-Y2_cold_lgbq_search_external_combo" / "outputs" / "predictions.csv"
QR1_PATH = BASE_EXP_DIR / "PP-QR1_cold_quantile_regression_alpha_grid" / "outputs" / "predictions.csv"

Y2_CANDIDATE = "component_pp_y2_baseline"
Y18_CANDIDATE = "stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25"
Y18_EXTERNAL_CANDIDATE = "stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25"
Y18_P95_CANDIDATE = "stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35"

QUANTILE_CANDIDATES = {
    "cat_q40": "catboost_quantile_q40",
    "cat_q50": "catboost_quantile_q50",
    "lgb_q40": "lightgbm_quantile_q40",
    "lgb_q50": "lightgbm_quantile_q50",
    "linear_q50": "linear_quantile_regression_q50",
}


@dataclass(frozen=True)
class PredictionCandidate:
    candidate: str
    policy: str
    pred_log: np.ndarray
    notes: str


def load_y18_frame() -> pd.DataFrame:
    raw = pd.read_csv(Y18_PATH, low_memory=False)
    base = raw[raw["candidate"].eq(Y18_CANDIDATE)].copy()
    if base.empty:
        raise ValueError(f"missing candidate: {Y18_CANDIDATE}")
    keep = [
        "split",
        "_track6_row_id",
        "actual_log",
        "actual_price",
        "quantile_width_log",
        "price_range_ratio",
        "artist_key",
    ]
    base = base[keep + ["pred_log"]].rename(columns={"pred_log": "y18_qwidth_pred_log"})
    for alias, candidate in [
        ("y2", Y2_CANDIDATE),
        ("y18_external", Y18_EXTERNAL_CANDIDATE),
        ("y18_p95", Y18_P95_CANDIDATE),
    ]:
        part = raw[raw["candidate"].eq(candidate)][["split", "_track6_row_id", "pred_log"]].copy()
        if part.empty:
            raise ValueError(f"missing candidate: {candidate}")
        part = part.rename(columns={"pred_log": f"{alias}_pred_log"})
        base = base.merge(part, on=["split", "_track6_row_id"], how="inner")
    if base["quantile_width_log"].isna().all():
        y2_raw = pd.read_csv(Y2_PATH, low_memory=False)
        y2_qwidth = y2_raw[y2_raw["candidate"].eq("lgbq_search_all_external_interaction")][
            ["split", "_track6_row_id", "quantile_width_log", "price_range_ratio"]
        ].rename(columns={
            "quantile_width_log": "y2_quantile_width_log",
            "price_range_ratio": "y2_price_range_ratio",
        })
        base = base.merge(y2_qwidth, on=["split", "_track6_row_id"], how="left")
        base["quantile_width_log"] = base["y2_quantile_width_log"]
        base["price_range_ratio"] = base["y2_price_range_ratio"]
        base = base.drop(columns=["y2_quantile_width_log", "y2_price_range_ratio"])
    if base["quantile_width_log"].isna().any() and base["price_range_ratio"].notna().any():
        base["quantile_width_log"] = base["quantile_width_log"].fillna(np.log(base["price_range_ratio"].clip(lower=1.0)))
    if base["price_range_ratio"].isna().any() and base["quantile_width_log"].notna().any():
        base["price_range_ratio"] = base["price_range_ratio"].fillna(np.exp(base["quantile_width_log"].clip(lower=0.0, upper=8.0)))
    return base


def add_qr1_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(QR1_PATH, low_memory=False)
    out = frame.copy()
    for alias, candidate in QUANTILE_CANDIDATES.items():
        part = raw[raw["candidate"].eq(candidate)][["split", "_track6_row_id", "pred_log"]].copy()
        if part.empty:
            raise ValueError(f"missing QR1 candidate: {candidate}")
        part = part.rename(columns={"pred_log": f"{alias}_pred_log"})
        out = out.merge(part, on=["split", "_track6_row_id"], how="inner")
    out["cat_q40_q50_mid_pred_log"] = 0.5 * out["cat_q40_pred_log"] + 0.5 * out["cat_q50_pred_log"]
    out["lgb_q40_q50_mid_pred_log"] = 0.5 * out["lgb_q40_pred_log"] + 0.5 * out["lgb_q50_pred_log"]
    return out


def metric_frame(split_df: pd.DataFrame) -> pd.DataFrame:
    return split_df.rename(columns={"actual_log": "ln_price_krw", "actual_price": "price_krw"})


def prediction_frame(split_df: pd.DataFrame, item: PredictionCandidate) -> pd.DataFrame:
    pred_price = np.clip(np.exp(item.pred_log), 1_000.0, None)
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": item.candidate,
        "scope": "cold",
        "split": split_df["split"].to_numpy(),
        "policy": item.policy,
        "_track6_row_id": split_df["_track6_row_id"].to_numpy(),
        "actual_log": split_df["actual_log"].to_numpy(dtype=float),
        "pred_log": item.pred_log,
        "actual_price": split_df["actual_price"].to_numpy(dtype=float),
        "pred_price": pred_price,
        "quantile_width_log": split_df["quantile_width_log"].to_numpy(dtype=float),
        "price_range_ratio": split_df["price_range_ratio"].to_numpy(dtype=float),
        "notes": item.notes,
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def add_metric(rows: list[dict[str, Any]], split_df: pd.DataFrame, item: PredictionCandidate) -> None:
    rows.append({
        "experiment_id": EXP_ID,
        "candidate": item.candidate,
        "scope": "cold",
        "split": str(split_df["split"].iloc[0]),
        "policy": item.policy,
        "notes": item.notes,
        **metrics(metric_frame(split_df), item.pred_log),
    })


def fixed_candidates(split_df: pd.DataFrame) -> list[PredictionCandidate]:
    return [
        PredictionCandidate("component_pp_y2_baseline", "control", split_df["y2_pred_log"].to_numpy(dtype=float), "기존 PP-Y2 기준선"),
        PredictionCandidate("component_pp_y18_qwidth_bin", "control", split_df["y18_qwidth_pred_log"].to_numpy(dtype=float), "기존 Cold 대표 개선 후보"),
        PredictionCandidate("component_pp_y18_external_x_qwidth", "control", split_df["y18_external_pred_log"].to_numpy(dtype=float), "기존 MdAPE 최저 참고 후보"),
        PredictionCandidate("component_pp_y18_p95_guard", "control", split_df["y18_p95_pred_log"].to_numpy(dtype=float), "기존 p95 방어 후보"),
        PredictionCandidate("component_catboost_quantile_q40", "quantile_component", split_df["cat_q40_pred_log"].to_numpy(dtype=float), "PP-QR1 MAPE/p95 방어형 단독 후보"),
        PredictionCandidate("component_catboost_quantile_q50", "quantile_component", split_df["cat_q50_pred_log"].to_numpy(dtype=float), "PP-QR1 대표 정확도 단독 후보"),
        PredictionCandidate("component_lightgbm_quantile_q40", "quantile_component", split_df["lgb_q40_pred_log"].to_numpy(dtype=float), "PP-QR1 LightGBM q40 단독 후보"),
        PredictionCandidate("component_linear_quantile_q50", "quantile_component", split_df["linear_q50_pred_log"].to_numpy(dtype=float), "PP-QR1 선형 Quantile Regression q50 단독 후보"),
    ]


def blend_candidates(split_df: pd.DataFrame) -> list[PredictionCandidate]:
    out: list[PredictionCandidate] = []
    base_cols = {
        "y18": "y18_qwidth_pred_log",
        "y2": "y2_pred_log",
    }
    comp_cols = {
        "cat_q40": "cat_q40_pred_log",
        "cat_q50": "cat_q50_pred_log",
        "cat_q40_q50_mid": "cat_q40_q50_mid_pred_log",
        "lgb_q40": "lgb_q40_pred_log",
        "linear_q50": "linear_q50_pred_log",
    }
    weights = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    for base_name, base_col in base_cols.items():
        base = split_df[base_col].to_numpy(dtype=float)
        for comp_name, comp_col in comp_cols.items():
            comp = split_df[comp_col].to_numpy(dtype=float)
            for weight in weights:
                pred = (1.0 - weight) * base + weight * comp
                out.append(PredictionCandidate(
                    f"blend_{base_name}_{comp_name}_w{weight:.2f}".replace(".", "p"),
                    "fixed_weight_log_blend",
                    pred,
                    f"{base_name} 예측 {1.0 - weight:.2f} + {comp_name} 예측 {weight:.2f}",
                ))
    return out


def validation_thresholds(val_df: pd.DataFrame) -> dict[str, float]:
    gap = val_df["y18_qwidth_pred_log"].to_numpy(dtype=float) - val_df["cat_q40_pred_log"].to_numpy(dtype=float)
    return {
        "qwidth_q67": float(val_df["quantile_width_log"].quantile(0.67)),
        "qwidth_q80": float(val_df["quantile_width_log"].quantile(0.80)),
        "pred_q67": float(val_df["y18_qwidth_pred_log"].quantile(0.67)),
        "gap_q50": float(np.quantile(gap, 0.50)),
        "gap_q67": float(np.quantile(gap, 0.67)),
    }


def guarded_candidates(split_df: pd.DataFrame, thresholds: dict[str, float]) -> list[PredictionCandidate]:
    out: list[PredictionCandidate] = []
    base = split_df["y18_qwidth_pred_log"].to_numpy(dtype=float)
    qwidth = split_df["quantile_width_log"].to_numpy(dtype=float)
    pred_level = split_df["y18_qwidth_pred_log"].to_numpy(dtype=float)
    comp_map = {
        "cat_q40": split_df["cat_q40_pred_log"].to_numpy(dtype=float),
        "cat_q50": split_df["cat_q50_pred_log"].to_numpy(dtype=float),
        "lgb_q40": split_df["lgb_q40_pred_log"].to_numpy(dtype=float),
        "linear_q50": split_df["linear_q50_pred_log"].to_numpy(dtype=float),
    }
    mask_defs = {
        "qwidth67_down": lambda comp: (qwidth >= thresholds["qwidth_q67"]) & (comp < base),
        "qwidth80_down": lambda comp: (qwidth >= thresholds["qwidth_q80"]) & (comp < base),
        "qwidth67_highpred_down": lambda comp: (qwidth >= thresholds["qwidth_q67"]) & (pred_level >= thresholds["pred_q67"]) & (comp < base),
        "gap67_down": lambda comp: ((base - comp) >= thresholds["gap_q67"]) & (comp < base),
        "qwidth67_gap50_down": lambda comp: (qwidth >= thresholds["qwidth_q67"]) & ((base - comp) >= thresholds["gap_q50"]) & (comp < base),
    }
    for comp_name, comp in comp_map.items():
        for mask_name, mask_fn in mask_defs.items():
            mask = mask_fn(comp)
            for weight in [0.15, 0.25, 0.35, 0.50]:
                pred = base.copy()
                pred[mask] = (1.0 - weight) * base[mask] + weight * comp[mask]
                out.append(PredictionCandidate(
                    f"guard_y18_{comp_name}_{mask_name}_w{weight:.2f}".replace(".", "p"),
                    "validation_threshold_guarded_blend",
                    pred,
                    f"validation threshold mask={mask_name}, weight={weight:.2f}, applied_rows={int(mask.sum())}",
                ))
    return out


def assign_bins(values: pd.Series | np.ndarray, edges: list[float]) -> np.ndarray:
    left, right = float(edges[0]), float(edges[1])
    if not np.isfinite(left):
        left = 0.0
    if not np.isfinite(right):
        right = 0.0
    if left >= right:
        eps = max(abs(left) * 1e-9, 1e-9)
        left -= eps
        right += eps
    return pd.cut(values, bins=[-np.inf, left, right, np.inf], labels=["low", "mid", "high"], include_lowest=True).astype(str).to_numpy()


def segment_thresholds(val_df: pd.DataFrame) -> dict[str, list[float]]:
    gap = val_df["y18_qwidth_pred_log"] - val_df["cat_q40_pred_log"]
    return {
        "qwidth": [float(val_df["quantile_width_log"].quantile(0.33)), float(val_df["quantile_width_log"].quantile(0.66))],
        "pred": [float(val_df["y18_qwidth_pred_log"].quantile(0.33)), float(val_df["y18_qwidth_pred_log"].quantile(0.66))],
        "gap": [float(gap.quantile(0.33)), float(gap.quantile(0.66))],
    }


def add_segment_columns(df: pd.DataFrame, thresholds: dict[str, list[float]]) -> pd.DataFrame:
    out = df.copy()
    out["qwidth_bin2"] = assign_bins(out["quantile_width_log"], thresholds["qwidth"])
    out["pred_bin2"] = assign_bins(out["y18_qwidth_pred_log"], thresholds["pred"])
    out["cat_q40_gap"] = out["y18_qwidth_pred_log"] - out["cat_q40_pred_log"]
    out["gap_bin2"] = assign_bins(out["cat_q40_gap"], thresholds["gap"])
    return out


def fit_corrections(
    val_df: pd.DataFrame,
    segment_cols: list[str],
    *,
    min_rows: int,
    cap: float,
) -> tuple[dict[tuple[str, ...], float], float]:
    residual = val_df["actual_log"] - val_df["y18_qwidth_pred_log"]
    work = val_df.copy()
    work["residual_log_fit"] = residual
    grouped = work.groupby(segment_cols, dropna=False)["residual_log_fit"].agg(["median", "count"]).reset_index()
    corrections: dict[tuple[str, ...], float] = {}
    for row in grouped.itertuples(index=False):
        values = tuple(str(getattr(row, col)) for col in segment_cols)
        if int(row.count) >= min_rows:
            corrections[values] = float(np.clip(row.median, -cap, cap))
    global_corr = float(np.clip(residual.median(), -cap, cap))
    return corrections, global_corr


def apply_corrections(
    split_df: pd.DataFrame,
    segment_cols: list[str],
    corrections: dict[tuple[str, ...], float],
    global_corr: float,
    *,
    strength: float,
) -> tuple[np.ndarray, int]:
    keys = list(zip(*[split_df[col].astype(str).to_numpy() for col in segment_cols]))
    values = np.asarray([corrections.get(tuple(key), global_corr) for key in keys], dtype=float)
    pred = split_df["y18_qwidth_pred_log"].to_numpy(dtype=float) + strength * values
    matched = sum(tuple(key) in corrections for key in keys)
    return pred, matched


def segment_correction_candidates(split_df: pd.DataFrame, val_binned: pd.DataFrame, split_binned: pd.DataFrame) -> list[PredictionCandidate]:
    out: list[PredictionCandidate] = []
    segment_sets = {
        "qwidth": ["qwidth_bin2"],
        "qwidth_gap": ["qwidth_bin2", "gap_bin2"],
        "pred_gap": ["pred_bin2", "gap_bin2"],
        "qwidth_pred_gap": ["qwidth_bin2", "pred_bin2", "gap_bin2"],
    }
    for seg_name, cols in segment_sets.items():
        for min_rows in [30, 50, 100]:
            for cap in [0.10, 0.15, 0.25]:
                corrections, global_corr = fit_corrections(val_binned, cols, min_rows=min_rows, cap=cap)
                for strength in [0.50, 0.75, 1.00]:
                    pred, matched = apply_corrections(split_binned, cols, corrections, global_corr, strength=strength)
                    out.append(PredictionCandidate(
                        f"segment_y18_{seg_name}_min{min_rows}_cap{cap:.2f}_s{strength:.2f}".replace(".", "p"),
                        "quantile_gap_segment_residual_correction",
                        pred,
                        f"segments={'+'.join(cols)}, corrections={len(corrections)}, matched_rows={matched}, global_corr={global_corr:.4f}",
                    ))
    return out


def candidate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    val = df[df["split"].eq("validation")].copy().reset_index(drop=True)
    test = df[df["split"].eq("test")].copy().reset_index(drop=True)
    thresholds = validation_thresholds(val)
    seg_thresholds = segment_thresholds(val)
    val_binned = add_segment_columns(val, seg_thresholds)
    test_binned = add_segment_columns(test, seg_thresholds)

    metric_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    selection_inputs: list[dict[str, Any]] = []
    for split_df, split_binned in [(val, val_binned), (test, test_binned)]:
        candidates = []
        candidates.extend(fixed_candidates(split_df))
        candidates.extend(blend_candidates(split_df))
        candidates.extend(guarded_candidates(split_df, thresholds))
        candidates.extend(segment_correction_candidates(split_df, val_binned, split_binned))
        for item in candidates:
            add_metric(metric_rows, split_df, item)
            pred_frames.append(prediction_frame(split_df, item))
            if split_df["split"].iloc[0] == "validation":
                m = metrics(metric_frame(split_df), item.pred_log)
                selection_inputs.append({"candidate": item.candidate, "policy": item.policy, **m})

    metrics_df = pd.DataFrame(metric_rows)
    pred_df = pd.concat(pred_frames, ignore_index=True)
    selection_df = build_selection(metrics_df)
    return metrics_df, pred_df, selection_df


def build_selection(metrics_df: pd.DataFrame) -> pd.DataFrame:
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    base = val[val["candidate"].eq("component_pp_y18_qwidth_bin")].iloc[0]
    choices: list[dict[str, Any]] = []

    def add_choice(objective: str, pool: pd.DataFrame, sort_cols: list[str]) -> None:
        if pool.empty:
            pool = val
        picked = pool.sort_values(sort_cols).iloc[0]
        test_row = test[test["candidate"].eq(picked["candidate"])].iloc[0]
        choices.append({
            "objective": objective,
            "selected_by_validation": picked["candidate"],
            "policy": picked["policy"],
            "validation_MdAPE": picked["MdAPE"],
            "validation_MAPE": picked["MAPE"],
            "validation_p95_APE": picked["p95_APE"],
            "test_MdAPE": test_row["MdAPE"],
            "test_MAPE": test_row["MAPE"],
            "test_p95_APE": test_row["p95_APE"],
            "test_RMSE_log": test_row["RMSE_log"],
        })

    add_choice("mdape_first", val, ["MdAPE", "MAPE", "p95_APE"])
    add_choice("mape_guard_mdape_plus_0p02", val[val["MdAPE"].le(float(base["MdAPE"]) + 0.02)], ["MAPE", "MdAPE", "p95_APE"])
    add_choice("p95_guard_mdape_plus_0p03", val[val["MdAPE"].le(float(base["MdAPE"]) + 0.03)], ["p95_APE", "MdAPE", "MAPE"])

    scored = val.copy()
    for col in ["MdAPE", "MAPE", "p95_APE"]:
        denom = scored[col].max() - scored[col].min()
        scored[f"{col}_norm"] = 0.0 if denom == 0 else (scored[col] - scored[col].min()) / denom
    scored["balanced_score"] = 0.45 * scored["MdAPE_norm"] + 0.35 * scored["MAPE_norm"] + 0.20 * scored["p95_APE_norm"]
    add_choice("balanced_validation_score", scored, ["balanced_score", "MdAPE", "MAPE"])
    return pd.DataFrame(choices)


def render_markdown(metrics_df: pd.DataFrame, selection_df: pd.DataFrame) -> str:
    test = metrics_df[metrics_df["split"].eq("test")].copy()
    val = metrics_df[metrics_df["split"].eq("validation")].copy()
    control_names = [
        "component_pp_y2_baseline",
        "component_pp_y18_qwidth_bin",
        "component_pp_y18_external_x_qwidth",
        "component_pp_y18_p95_guard",
        "component_catboost_quantile_q40",
        "component_catboost_quantile_q50",
    ]
    controls = test[test["candidate"].isin(control_names)].sort_values(["MdAPE", "MAPE", "p95_APE"])
    best_test = test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    best_val = val.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(12)
    y18_test = test[test["candidate"].eq("component_pp_y18_qwidth_bin")].iloc[0]
    best = best_test.iloc[0]

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 1. 실험 목적",
        "",
        "- `PP-QR1`에서 확인된 CatBoost Quantile q40/q50 신호가 기존 Cold 최종 후보에 실제로 도움이 되는지 검증.",
        "- q50은 대표 가격 후보, q40은 MAPE/p95 방어 후보로 분리해서 결합.",
        "- 기존 Cold 대표 개선 후보 `PP-Y18 qwidth_bin_oof_min30_cap0.25`를 기준으로 단순 결합, 위험 구간 결합, segment residual 보정을 비교.",
        "",
        "## 2. 사용 데이터와 기준 후보",
        "",
        "- 데이터 split: 기존 Cold validation/test 고정.",
        "- 기준 후보: `PP-Y2 component_pp_y2_baseline`, `PP-Y18 qwidth_bin`, `PP-Y18 external_x_qwidth`, `PP-Y18 p95_guard`.",
        "- 추가 Quantile 후보: `PP-QR1 CatBoost q40/q50`, `LightGBM q40/q50`, `Linear Quantile Regression q50`.",
        "- 선택 기준: validation에서 후보를 고르고 test는 확인용으로만 사용.",
        "",
        "## 3. 기존 후보와 Quantile 단독 후보",
        "",
        "| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in controls.itertuples():
        lines.append(f"| `{row.candidate}` | {row.policy} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |")

    lines += [
        "",
        "## 4. Validation 선택 후보의 Test 결과",
        "",
        "| 선택 목적 | validation 선택 후보 | 정책 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selection_df.itertuples():
        lines.append(
            f"| {row.objective} | `{row.selected_by_validation}` | {row.policy} | "
            f"{row.validation_MdAPE:.4f} | {row.validation_MAPE:.4f} | {row.validation_p95_APE:.4f} | "
            f"{row.test_MdAPE:.4f} | {row.test_MAPE:.4f} | {row.test_p95_APE:.4f} |"
        )

    lines += [
        "",
        "## 5. Test 기준 상위 후보",
        "",
        "| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 비고 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in best_test.itertuples():
        delta = row.MdAPE - y18_test.MdAPE
        note = "기존 PP-Y18보다 개선" if delta < 0 else "기존 PP-Y18보다 악화/동률"
        lines.append(f"| `{row.candidate}` | {row.policy} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {note} |")

    lines += [
        "",
        "## 6. 해석",
        "",
        f"- 기존 대표 후보 `component_pp_y18_qwidth_bin`: test MdAPE `{y18_test.MdAPE:.4f}`, MAPE `{y18_test.MAPE:.4f}`, p95 `{y18_test.p95_APE:.4f}`.",
        f"- 이번 후보 중 test MdAPE 최저: `{best.candidate}` / MdAPE `{best.MdAPE:.4f}`, MAPE `{best.MAPE:.4f}`, p95 `{best.p95_APE:.4f}`.",
    ]
    if best.MdAPE < y18_test.MdAPE:
        lines.append("- Quantile q40/q50 신호가 기존 Cold 대표 후보를 추가로 개선할 가능성이 확인됨.")
    else:
        lines.append("- Quantile q40/q50을 단순히 섞는 것만으로는 기존 Cold 대표 후보를 명확히 넘지 못함.")
    lines += [
        "- q40 계열은 MAPE/p95 방어 성격이 있으나, 전체 샘플에 강하게 적용하면 대표 오차가 악화될 수 있음.",
        "- 최종 Cold 모델에 반영하려면 q40 단독이 아니라 `qwidth`, `pred_gap`, `high-pred` 같은 조건부 보정축으로 제한하는 방식이 더 적합.",
        "",
        "## 7. 산출물",
        "",
        f"- 실험 폴더: `experiments/track6/{SLUG}`.",
        "- `outputs/metrics.csv`: 전체 후보 성능.",
        "- `outputs/predictions.csv`: validation/test 샘플별 예측값.",
        "- `outputs/selection_summary.csv`: validation 선택 후보의 test 결과.",
        "",
    ]
    return "\n".join(lines)


def render_html(md: str, metrics_df: pd.DataFrame, selection_df: pd.DataFrame) -> str:
    body = html.escape(md).replace("\n", "<br>\n")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{html.escape(EXP_ID)} {html.escape(TITLE)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}
th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}
</style>
</head>
<body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div>{body}</div>
<h2>Selection Summary</h2>
{selection_df.to_html(index=False, escape=True)}
<h2>Metrics</h2>
{metrics_df.to_html(index=False, escape=True)}
</body>
</html>"""


def write_outputs(metrics_df: pd.DataFrame, pred_df: pd.DataFrame, selection_df: pd.DataFrame, config: dict[str, Any]) -> dict[str, str]:
    exp_dir = BASE_EXP_DIR / SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    selection_df.to_csv(exp_dir / "outputs" / "selection_summary.csv", index=False)
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    md = render_markdown(metrics_df, selection_df)
    html_doc = render_html(md, metrics_df, selection_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_PATH.write_text(md, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    return {
        "experiment_dir": str(exp_dir.relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.md").relative_to(REPO)),
        "html": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
        "docs_summary": str(DOC_PATH.relative_to(REPO)),
    }


def main() -> None:
    start = time.time()
    frame = add_qr1_predictions(load_y18_frame())
    metrics_df, pred_df, selection_df = candidate_rows(frame)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "scope": "cold",
        "inputs": {
            "pp_y18_predictions": str(Y18_PATH.relative_to(REPO)),
            "pp_qr1_predictions": str(QR1_PATH.relative_to(REPO)),
            "base_candidate": Y18_CANDIDATE,
            "quantile_candidates": QUANTILE_CANDIDATES,
        },
        "model_manifest": {
            "type": "prediction_level_postprocessing",
            "target": "ln_price_krw",
            "strategies": [
                "fixed_weight_log_blend",
                "validation_threshold_guarded_blend",
                "quantile_gap_segment_residual_correction",
            ],
            "selection_rule": "validation only; test is confirmation",
        },
    }
    paths = write_outputs(metrics_df, pred_df, selection_df, config)
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(8)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "paths": paths,
        "selection": selection_df.to_dict(orient="records"),
        "best_test": test[["candidate", "policy", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
