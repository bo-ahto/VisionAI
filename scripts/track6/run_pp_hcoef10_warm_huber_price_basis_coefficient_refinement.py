#!/usr/bin/env python3
"""Run PP-HCOEF10: cause-segment residual correction for Warm Huber.

HCOEF4~HCOEF9 showed that richer comparable-price bases improve MdAPE/MAPE,
but the p95_APE guard fails when the correction is applied too broadly.
This experiment keeps HCOEF3 as the stable anchor and learns tiny residual
corrections only for interpretable cause segments:

- predicted price bin
- comparable-basis sample count and spread
- size bin
- medium/support bucket
- basis/current disagreement sign

Candidate choice is driven by repeated validation OOF. Fixed test and 0604 are
confirmation only.
"""
from __future__ import annotations

import html
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_hcoef5_warm_basis_hcoef_blend_repeated_validation as hcoef5  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-HCOEF10"
EXP_SLUG = "PP-HCOEF10_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

REFERENCE = hcoef5.REFERENCE
STABLE = hcoef5.STABLE
N_FOLDS = 5
N_REPEATS = 20
SEED = 20260613


@dataclass(frozen=True)
class SegmentConfig:
    name: str
    keys: tuple[str, ...]
    min_n: int
    cap: float
    strength: float
    purpose: str


BASE_SEGMENTS = [
    {
        "name": "pred_bin",
        "keys": ("pred_bin",),
        "min_n": 20,
        "purpose": "예측 가격대별 반복 편향 보정",
    },
    {
        "name": "basis_reliability",
        "keys": ("basis_n_bucket", "basis_iqr_bucket"),
        "min_n": 15,
        "purpose": "유사 작품 기준가 표본 수/분산별 편향 보정",
    },
    {
        "name": "basis_level",
        "keys": ("basis_level_simple",),
        "min_n": 20,
        "purpose": "작가 기반/시장 기반 fallback level별 편향 보정",
    },
    {
        "name": "pred_reliability",
        "keys": ("pred_bin", "basis_n_bucket"),
        "min_n": 12,
        "purpose": "가격대와 기준가 표본 수를 함께 본 편향 보정",
    },
    {
        "name": "size_reliability",
        "keys": ("size_bin", "basis_n_bucket"),
        "min_n": 12,
        "purpose": "작품 크기와 기준가 표본 수 조합별 편향 보정",
    },
    {
        "name": "medium_support",
        "keys": ("medium_support_bucket_clean",),
        "min_n": 15,
        "purpose": "재료/지지체 묶음별 반복 편향 보정",
    },
    {
        "name": "medium_size",
        "keys": ("medium_support_bucket_clean", "size_bin"),
        "min_n": 20,
        "purpose": "재료/지지체와 크기 조합별 편향 보정",
    },
    {
        "name": "basis_gap_sign",
        "keys": ("basis_gap_sign", "ppv8_gap_sign"),
        "min_n": 15,
        "purpose": "기준가와 기존 후보 간 방향 차이에 따른 편향 보정",
    },
]

CAP_STRENGTH_GRID = [
    {"cap": 0.02, "strength": 0.25},
    {"cap": 0.02, "strength": 0.50},
    {"cap": 0.03, "strength": 0.25},
    {"cap": 0.03, "strength": 0.50},
    {"cap": 0.05, "strength": 0.25},
    {"cap": 0.05, "strength": 0.50},
]

SEGMENT_CONFIGS = [
    SegmentConfig(
        name=f"hcoef10_{segment['name']}_cap{item['cap']:.2f}_s{item['strength']:.2f}",
        keys=tuple(segment["keys"]),
        min_n=int(segment["min_n"]),
        cap=float(item["cap"]),
        strength=float(item["strength"]),
        purpose=str(segment["purpose"]),
    )
    for segment in BASE_SEGMENTS
    for item in CAP_STRENGTH_GRID
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def build_frames() -> dict[str, pd.DataFrame]:
    return hcoef5.build_frames()


def metric_from_frame(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return hcoef5.metric_from_frame(frame, pred_log)


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.row_folds(n, seed)


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return hcoef5.artist_folds(frame, seed)


def quantile_edges(values: np.ndarray, q: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < 2:
        return np.asarray([-np.inf, np.inf])
    edges = np.quantile(arr, np.linspace(0.0, 1.0, q + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)
    if len(edges) < 3:
        return np.asarray([-np.inf, np.inf])
    return edges


def assign_bin(values: pd.Series | np.ndarray, edges: np.ndarray, prefix: str) -> np.ndarray:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
    idx = np.searchsorted(edges, arr, side="right") - 1
    idx = np.clip(idx, 0, max(len(edges) - 2, 0))
    out = np.asarray([f"{prefix}{int(i):02d}" for i in idx], dtype=object)
    out[~np.isfinite(arr)] = f"{prefix}missing"
    return out


def bucket_basis_n(n: pd.Series) -> np.ndarray:
    values = pd.to_numeric(n, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    return np.select(
        [values < 5, values < 10, values < 20, values >= 20],
        ["n_lt5", "n_5_9", "n_10_19", "n_ge20"],
        default="n_missing",
    ).astype(object)


def bucket_iqr(iqr: pd.Series) -> np.ndarray:
    values = pd.to_numeric(iqr, errors="coerce").to_numpy(dtype=float)
    out = np.select(
        [values <= 0.75, values <= 1.00, values > 1.00],
        ["iqr_low", "iqr_mid", "iqr_high"],
        default="iqr_missing",
    ).astype(object)
    out[~np.isfinite(values)] = "iqr_missing"
    return out


def simple_basis_level(level: pd.Series) -> np.ndarray:
    text = level.astype("string").fillna("missing").to_numpy(dtype=str)
    out = []
    for item in text:
        if item.startswith("artist_medium") or item.startswith("artist_size"):
            out.append("artist_detail")
        elif item.startswith("artist"):
            out.append("artist_overall")
        elif item.startswith("medium"):
            out.append("market_medium")
        elif item.startswith("global"):
            out.append("global")
        else:
            out.append("missing")
    return np.asarray(out, dtype=object)


def sign_bucket(values: pd.Series, name: str) -> np.ndarray:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.select([arr < -0.25, arr <= 0.25, arr > 0.25], [f"{name}_neg", f"{name}_flat", f"{name}_pos"], default=f"{name}_missing")
    out = out.astype(object)
    out[~np.isfinite(arr)] = f"{name}_missing"
    return out


def add_segment_features(
    train: pd.DataFrame,
    eval_frame: pd.DataFrame,
    train_pred: np.ndarray,
    eval_pred: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_out = train.copy()
    eval_out = eval_frame.copy()
    pred_edges = quantile_edges(train_pred, 10)
    size_edges = quantile_edges(pd.to_numeric(train_out["log_area"], errors="coerce").to_numpy(dtype=float), 5)

    train_out["pred_bin"] = assign_bin(train_pred, pred_edges, "pred")
    eval_out["pred_bin"] = assign_bin(eval_pred, pred_edges, "pred")
    train_out["size_bin"] = assign_bin(train_out["log_area"], size_edges, "size")
    eval_out["size_bin"] = assign_bin(eval_out["log_area"], size_edges, "size")

    for frame in [train_out, eval_out]:
        frame["basis_n_bucket"] = bucket_basis_n(frame.get("basis_relaxed_n", pd.Series(index=frame.index, dtype=float)))
        frame["basis_iqr_bucket"] = bucket_iqr(frame.get("basis_relaxed_iqr", pd.Series(index=frame.index, dtype=float)))
        frame["basis_level_simple"] = simple_basis_level(frame.get("basis_relaxed_level", pd.Series(index=frame.index, dtype=str)))
        frame["basis_gap_sign"] = sign_bucket(frame.get("basis_relaxed_vs_current_gap", pd.Series(index=frame.index, dtype=float)), "basis")
        frame["ppv8_gap_sign"] = sign_bucket(frame.get("current_ppv8_gap", pd.Series(index=frame.index, dtype=float)), "ppv8")
        frame["medium_support_bucket_clean"] = (
            frame.get("medium_support_bucket", pd.Series(index=frame.index, dtype=str))
            .astype("string")
            .fillna("__MISSING__")
            .replace({"": "__MISSING__"})
            .astype(str)
        )
    return train_out, eval_out


def key_tuple(row: pd.Series, keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row[key]) for key in keys)


def fit_segment_maps(
    train_features: pd.DataFrame,
    residual: np.ndarray,
    keys: tuple[str, ...],
    min_n: int,
) -> dict[str, Any]:
    frame = train_features[list(keys)].copy()
    frame["_residual"] = np.asarray(residual, dtype=float)
    maps: list[dict[tuple[str, ...], dict[str, float]]] = []
    key_levels: list[tuple[str, ...]] = []
    for width in range(len(keys), 0, -1):
        sub_keys = keys[:width]
        grouped = frame.groupby(list(sub_keys), dropna=False, observed=False)["_residual"].agg(["median", "count"]).reset_index()
        grouped = grouped[grouped["count"].ge(min_n)].copy()
        group_map: dict[tuple[str, ...], dict[str, float]] = {}
        for _, row in grouped.iterrows():
            group_map[tuple(str(row[key]) for key in sub_keys)] = {
                "median": float(row["median"]),
                "count": float(row["count"]),
            }
        maps.append(group_map)
        key_levels.append(sub_keys)
    overall = float(np.median(np.asarray(residual, dtype=float)))
    return {"keys": keys, "key_levels": key_levels, "maps": maps, "overall": overall, "min_n": min_n}


def apply_segment_map(eval_features: pd.DataFrame, fitted: dict[str, Any], cap: float, strength: float) -> tuple[np.ndarray, list[dict[str, Any]]]:
    corrections = np.zeros(len(eval_features), dtype=float)
    applied_rows: list[dict[str, Any]] = []
    key_levels: list[tuple[str, ...]] = fitted["key_levels"]
    maps: list[dict[tuple[str, ...], dict[str, float]]] = fitted["maps"]
    full_keys: tuple[str, ...] = fitted["keys"]
    for idx, (_, row) in enumerate(eval_features.iterrows()):
        raw = float(fitted["overall"])
        matched_level = "overall"
        matched_count = 0.0
        matched_key = ("overall",)
        for sub_keys, group_map in zip(key_levels, maps, strict=True):
            key = key_tuple(row, sub_keys)
            if key in group_map:
                raw = float(group_map[key]["median"])
                matched_level = "+".join(sub_keys)
                matched_count = float(group_map[key]["count"])
                matched_key = key
                break
        limited = float(np.clip(raw, -cap, cap) * strength)
        corrections[idx] = limited
        applied_rows.append(
            {
                "segment_keys": "+".join(full_keys),
                "matched_level": matched_level,
                "matched_key": "|".join(matched_key),
                "matched_n": matched_count,
                "raw_median_residual_log": raw,
                "limited_correction_log": limited,
            }
        )
    return corrections, applied_rows


def candidate_prediction(
    train: pd.DataFrame,
    eval_frame: pd.DataFrame,
    config: SegmentConfig,
) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    train_pred, _ = hcoef5.hcoef2_prediction(train, train)
    eval_pred, _ = hcoef5.hcoef2_prediction(train, eval_frame)
    train_features, eval_features = add_segment_features(train, eval_frame, train_pred, eval_pred)
    residual = train["actual_log"].to_numpy(dtype=float) - train_pred
    fitted = fit_segment_maps(train_features, residual, config.keys, config.min_n)
    correction, applied_rows = apply_segment_map(eval_features, fitted, config.cap, config.strength)
    pred = eval_pred + correction

    correction_rows = []
    for level_keys, group_map in zip(fitted["key_levels"], fitted["maps"], strict=True):
        for key, values in group_map.items():
            raw = float(values["median"])
            correction_rows.append(
                {
                    "candidate": config.name,
                    "segment_keys": "+".join(config.keys),
                    "matched_level": "+".join(level_keys),
                    "matched_key": "|".join(key),
                    "matched_n": int(values["count"]),
                    "raw_median_residual_log": raw,
                    "limited_correction_log": float(np.clip(raw, -config.cap, config.cap) * config.strength),
                    "cap": config.cap,
                    "strength": config.strength,
                    "min_n": config.min_n,
                    "purpose": config.purpose,
                }
            )
    correction_rows.append(
        {
            "candidate": config.name,
            "segment_keys": "+".join(config.keys),
            "matched_level": "overall",
            "matched_key": "overall",
            "matched_n": len(train),
            "raw_median_residual_log": float(fitted["overall"]),
            "limited_correction_log": float(np.clip(fitted["overall"], -config.cap, config.cap) * config.strength),
            "cap": config.cap,
            "strength": config.strength,
            "min_n": config.min_n,
            "purpose": config.purpose,
        }
    )
    applied = pd.DataFrame(applied_rows)
    return pred, pd.DataFrame(correction_rows), applied


def stable_prediction(train: pd.DataFrame, eval_frame: pd.DataFrame) -> np.ndarray:
    pred, _ = hcoef5.hcoef2_prediction(train, eval_frame)
    return pred


def prediction_frame(frame: pd.DataFrame, candidate: str, split: str, pred: np.ndarray, method: str) -> pd.DataFrame:
    pred = np.asarray(pred, dtype=float)
    price = np.clip(np.exp(pred), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred,
            "pred_price": price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred,
            "ape": np.abs(price - actual) / np.clip(actual, 1.0, None),
        }
    )


def repeated_oof(validation: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []

    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            seed = SEED + repeat
            folds = row_folds(len(validation), seed) if scheme == "row_oof" else artist_folds(validation, seed)
            oof: dict[str, np.ndarray] = {STABLE: np.full(len(validation), np.nan, dtype=float)}
            for config in SEGMENT_CONFIGS:
                oof[config.name] = np.full(len(validation), np.nan, dtype=float)

            for train_idx, hold_idx in folds:
                train = validation.iloc[train_idx].copy()
                hold = validation.iloc[hold_idx].copy()
                stable_pred = stable_prediction(train, hold)
                oof[STABLE][hold_idx] = stable_pred
                for config in SEGMENT_CONFIGS:
                    pred, _, _ = candidate_prediction(train, hold, config)
                    oof[config.name][hold_idx] = pred

            ref_metric = metric_from_frame(validation, oof[STABLE])
            for candidate, pred in oof.items():
                metric = metric_from_frame(validation, pred)
                metric_rows.append(
                    {
                        "validation_scheme": scheme,
                        "repeat": repeat,
                        "candidate": candidate,
                        "n": len(validation),
                        **metric,
                        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - ref_metric["MdAPE"],
                        "delta_MAPE_vs_hcoef2": metric["MAPE"] - ref_metric["MAPE"],
                        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - ref_metric["p95_APE"],
                        "improve_count_vs_hcoef2": int(metric["MdAPE"] < ref_metric["MdAPE"])
                        + int(metric["MAPE"] < ref_metric["MAPE"])
                        + int(metric["p95_APE"] < ref_metric["p95_APE"]),
                    }
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, candidate, f"validation_{scheme}_repeat0", pred, "repeated_oof"))

    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True)


def fixed_confirmation(
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    applied_rows: list[pd.DataFrame] = []

    stable_by_split: dict[str, np.ndarray] = {}
    for split in ["validation", "test", "0604_ex50"]:
        stable = stable_prediction(validation, frames[split])
        stable_by_split[split] = stable
        metric_rows.append(metric_row(split, STABLE, "hcoef3_stable_anchor", frames[split], stable, stable))
        pred_rows.append(prediction_frame(frames[split], STABLE, split, stable, "hcoef3_stable_anchor"))

    for config in SEGMENT_CONFIGS:
        for split in ["validation", "test", "0604_ex50"]:
            pred, corrections, applied = candidate_prediction(validation, frames[split], config)
            metric_rows.append(metric_row(split, config.name, "cause_segment_median_residual", frames[split], pred, stable_by_split[split]))
            pred_rows.append(prediction_frame(frames[split], config.name, split, pred, "cause_segment_median_residual"))
            if split == "test":
                coef_rows.append(corrections)
            applied["candidate"] = config.name
            applied["split"] = split
            applied_rows.append(applied)

    predictions = pd.concat(pred_rows, ignore_index=True)
    residuals = residual_analysis(predictions)
    applied_all = pd.concat(applied_rows, ignore_index=True)
    return pd.DataFrame(metric_rows), predictions, pd.concat(coef_rows, ignore_index=True), residuals, applied_all


def metric_row(split: str, candidate: str, method: str, frame: pd.DataFrame, pred: np.ndarray, stable_pred: np.ndarray) -> dict[str, Any]:
    metric = metric_from_frame(frame, pred)
    stable = metric_from_frame(frame, stable_pred)
    return {
        "validation_scheme": "fixed_confirmation",
        "repeat": -1,
        "candidate": candidate,
        "method": method,
        "split": split,
        "n": len(frame),
        **metric,
        "delta_MdAPE_vs_hcoef2": metric["MdAPE"] - stable["MdAPE"],
        "delta_MAPE_vs_hcoef2": metric["MAPE"] - stable["MAPE"],
        "delta_p95_APE_vs_hcoef2": metric["p95_APE"] - stable["p95_APE"],
        "improve_count_vs_hcoef2": int(metric["MdAPE"] < stable["MdAPE"])
        + int(metric["MAPE"] < stable["MAPE"])
        + int(metric["p95_APE"] < stable["p95_APE"]),
    }


def summarize_repeated(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    repeated = metrics[metrics["repeat"].ge(0)].copy()
    for (scheme, candidate), group in repeated.groupby(["validation_scheme", "candidate"], observed=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "mean_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].mean()),
                "mean_delta_MAPE_vs_hcoef2": float(group["delta_MAPE_vs_hcoef2"].mean()),
                "mean_delta_p95_APE_vs_hcoef2": float(group["delta_p95_APE_vs_hcoef2"].mean()),
                "std_delta_MdAPE_vs_hcoef2": float(group["delta_MdAPE_vs_hcoef2"].std()),
                "MdAPE_improve_prob_vs_hcoef2": float((group["delta_MdAPE_vs_hcoef2"] < 0).mean()),
                "MAPE_improve_prob_vs_hcoef2": float((group["delta_MAPE_vs_hcoef2"] < 0).mean()),
                "p95_improve_prob_vs_hcoef2": float((group["delta_p95_APE_vs_hcoef2"] < 0).mean()),
                "all3_improve_prob_vs_hcoef2": float((group["improve_count_vs_hcoef2"] == 3).mean()),
                "mean_improve_count_vs_hcoef2": float(group["improve_count_vs_hcoef2"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["all3_improve_prob_vs_hcoef2", "mean_delta_MdAPE_vs_hcoef2", "mean_delta_MAPE_vs_hcoef2"],
        ascending=[False, True, True],
    )


def select_candidates(summary: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    row = summary[summary["validation_scheme"].eq("row_oof")].set_index("candidate")
    artist = summary[summary["validation_scheme"].eq("artist_oof")].set_index("candidate")
    test = fixed[fixed["split"].eq("test")].set_index("candidate")
    ops = fixed[fixed["split"].eq("0604_ex50")].set_index("candidate")
    candidates = sorted(set(row.index) & set(artist.index) & set(test.index))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate": candidate,
                "row_all3_prob": row.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "artist_all3_prob": artist.loc[candidate, "all3_improve_prob_vs_hcoef2"],
                "row_delta_MdAPE": row.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "row_delta_MAPE": row.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "row_delta_p95_APE": row.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "artist_delta_MdAPE": artist.loc[candidate, "mean_delta_MdAPE_vs_hcoef2"],
                "artist_delta_MAPE": artist.loc[candidate, "mean_delta_MAPE_vs_hcoef2"],
                "artist_delta_p95_APE": artist.loc[candidate, "mean_delta_p95_APE_vs_hcoef2"],
                "test_delta_MdAPE": test.loc[candidate, "delta_MdAPE_vs_hcoef2"],
                "test_delta_MAPE": test.loc[candidate, "delta_MAPE_vs_hcoef2"],
                "test_delta_p95_APE": test.loc[candidate, "delta_p95_APE_vs_hcoef2"],
                "ops0604_delta_MdAPE": ops.loc[candidate, "delta_MdAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_MAPE": ops.loc[candidate, "delta_MAPE_vs_hcoef2"] if candidate in ops.index else np.nan,
                "ops0604_delta_p95_APE": ops.loc[candidate, "delta_p95_APE_vs_hcoef2"] if candidate in ops.index else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["passes_repeat_gate"] = (
        out["row_all3_prob"].ge(0.90)
        & out["artist_all3_prob"].ge(0.90)
        & out["row_delta_MdAPE"].lt(0)
        & out["row_delta_MAPE"].le(0)
        & out["row_delta_p95_APE"].le(0)
        & out["artist_delta_MdAPE"].lt(0)
        & out["artist_delta_MAPE"].le(0)
        & out["artist_delta_p95_APE"].le(0)
    )
    out["passes_fixed_guard"] = out["test_delta_MdAPE"].lt(0) & out["test_delta_MAPE"].le(0) & out["test_delta_p95_APE"].le(0)
    out["purpose"] = np.select(
        [
            out["passes_repeat_gate"] & out["passes_fixed_guard"],
            out["row_delta_p95_APE"].lt(0) & out["artist_delta_p95_APE"].lt(0) & out["test_delta_p95_APE"].le(0),
            out["row_delta_MAPE"].lt(0) & out["artist_delta_MAPE"].lt(0) & out["test_delta_p95_APE"].le(0.01),
        ],
        ["operational_candidate", "p95_guard_candidate", "repeat_mape_candidate"],
        default="hold_or_reject",
    )
    return out.sort_values(
        ["passes_repeat_gate", "passes_fixed_guard", "row_delta_p95_APE", "artist_delta_p95_APE", "test_delta_p95_APE"],
        ascending=[False, False, True, True, True],
    )


def residual_analysis(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in predictions.groupby(["split", "candidate"], observed=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": int(len(group)),
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "candidate"])


def applied_summary(applied: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in applied.groupby(["split", "candidate"], observed=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "mean_abs_correction_log": float(group["limited_correction_log"].abs().mean()),
                "max_abs_correction_log": float(group["limited_correction_log"].abs().max()),
                "overall_fallback_share": float((group["matched_level"].eq("overall")).mean()),
                "median_matched_n": float(group["matched_n"].median()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split", "mean_abs_correction_log"], ascending=[True, False])


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    lines = ["| " + " | ".join(map(str, data.columns)) + " |", "| " + " | ".join(["---"] * len(data.columns)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for i, line in enumerate(table):
            if i == 1:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        body.append("<table>" + "".join(rows) + "</table>")
        table.clear()

    for line in md.splitlines():
        if line.startswith("| "):
            table.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
        "p{line-height:1.55}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    summary: pd.DataFrame,
    fixed: pd.DataFrame,
    selection: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    applied: pd.DataFrame,
) -> None:
    fixed_test = fixed[fixed["split"].eq("test")].sort_values(["p95_APE", "MdAPE", "MAPE"])
    applied_stats = applied_summary(applied)
    decision = "새 운영 기본 후보 채택 없음"
    if not selection.empty:
        top = selection.iloc[0]
        if bool(top["passes_repeat_gate"]) and bool(top["passes_fixed_guard"]):
            decision = f"운영 후보 가능: `{top['candidate']}`"
        elif str(top["purpose"]) != "hold_or_reject":
            decision = f"목적별 보류 후보: `{top['candidate']}`"

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 원인 구간 기반 약한 보정 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF3 안정 후보의 남은 큰 오차가 특정 가격대, 기준가 신뢰도, 크기, 재료/지지체 구간에서 반복되는지 확인하고 해당 구간에만 작은 잔차 보정을 적용.",
            f"- 기준 후보: `{STABLE}`.",
            "- 방식: validation 내부 train fold에서 segment별 residual_log 중앙값을 만들고, cap/strength로 제한해 holdout fold에 적용.",
            f"- 반복 설정: row OOF {N_REPEATS}회, artist OOF {N_REPEATS}회, 각 {N_FOLDS} folds.",
            "- 후보 선택: 반복 OOF 우선, fixed test/0604는 확인용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {decision}.",
            "- p95_APE와 반복 안정성을 동시에 통과하지 못하면 기본 후보로 채택하지 않는다.",
            "",
            "## 2. 후보 선택표",
            "",
            markdown_table(selection.round(4), max_rows=24),
            "",
            "## 3. 반복 OOF 요약",
            "",
            markdown_table(summary.round(4), max_rows=40),
            "",
            "## 4. Fixed test p95 상위 후보",
            "",
            markdown_table(
                fixed_test[
                    [
                        "candidate",
                        "method",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_hcoef2",
                        "delta_MAPE_vs_hcoef2",
                        "delta_p95_APE_vs_hcoef2",
                    ]
                ].round(4),
                max_rows=28,
            ),
            "",
            "## 5. 보정 적용 규모",
            "",
            markdown_table(applied_stats.round(4), max_rows=28),
            "",
            "## 6. 구간별 보정값 예시",
            "",
            markdown_table(
                coeffs.sort_values(["candidate", "matched_level", "matched_n"], ascending=[True, True, False]).head(50).round(5),
            ),
            "",
            "## 7. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=36),
            "",
            "## 8. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/segment_application_summary.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef10_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef10_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"])
    fixed_metrics, fixed_predictions, coeffs, residuals, applied = fixed_confirmation(frames)
    summary = summarize_repeated(repeated_metrics)
    selection = select_candidates(summary, fixed_metrics)
    app_summary = applied_summary(applied)

    metrics = pd.concat([repeated_metrics, fixed_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([repeated_predictions, fixed_predictions], ignore_index=True, sort=False)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selection.to_csv(out / "selected_candidates.csv", index=False)
    app_summary.to_csv(out / "segment_application_summary.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": STABLE,
        "original_warm_reference": REFERENCE,
        "n_repeats": N_REPEATS,
        "n_folds": N_FOLDS,
        "seed": SEED,
        "segment_configs": [config.__dict__ for config in SEGMENT_CONFIGS],
        "selection_policy": "row/artist repeated OOF first; fixed test p95 must not worsen",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, fixed_metrics, selection, coeffs, residuals, applied)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected candidates ---")
    print(selection.round(4).head(20).to_string(index=False))
    print("--- fixed test p95 top ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["p95_APE", "MdAPE", "MAPE"])[
            [
                "candidate",
                "method",
                "MdAPE",
                "MAPE",
                "p95_APE",
                "delta_MdAPE_vs_hcoef2",
                "delta_MAPE_vs_hcoef2",
                "delta_p95_APE_vs_hcoef2",
            ]
        ]
        .round(4)
        .head(18)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
