#!/usr/bin/env python3
"""Run PP-WHUBER10 artwork-level cause diagnostics and cause-based correction.

This experiment checks whether the current best Warm candidate can be improved
by looking at per-artwork errors first, grouping the likely causes, and applying
small log-price residual corrections by cause group.

Important leakage rule:
- Test per-artwork errors are used only for diagnosis/reporting.
- Correction values are learned from validation calibration folds only.
- The selected correction policy is chosen by repeated artist-level holdout,
  then applied once to the fixed test set.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_whuber8_warm_residual_oof_revalidation as whuber8  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER10"
EXP_SLUG = "PP-WHUBER10_warm_artwork_error_cause_correction"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 작품별 오차 원인 기반 보정 실험"
SEED = 20260606
N_ARTIST_SPLITS = 5
N_ARTIST_REPEATS = 8
CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE

METRICS = ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]


HIERARCHIES: dict[str, list[list[str]]] = {
    "risk_pred": [["risk_cause", "pred_log_bin"], ["risk_cause"], ["pred_log_bin"], []],
    "pred_svc": [["pred_log_bin", "svc_reliability_bin"], ["pred_log_bin"], ["svc_reliability_bin"], []],
    "pred_size": [["pred_log_bin", "size_bin"], ["pred_log_bin"], ["size_bin"], []],
    "works_pred": [["artist_works_bin", "pred_log_bin"], ["artist_works_bin"], ["pred_log_bin"], []],
}
MIN_ROWS = [8, 20]
CAPS = [0.05, 0.08]
STRENGTHS = [0.25, 0.50]
SMOOTH_ROWS = [20]


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    val, test = whuber8.load_frames()
    return add_diagnostic_features(val), add_diagnostic_features(test)


def metric_from_pred(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return wcoef.metric_values(frame, np.asarray(pred_log, dtype=float))


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def simple_bin(value: Any) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "missing"
    return str(value).strip()


def medium_support_simple(value: Any) -> str:
    text = simple_bin(value).lower()
    if text == "missing":
        return "missing"
    if "unknown" in text or "other" in text or "기타" in text:
        return "unknown_or_other"
    if "canvas" in text:
        return "canvas_group"
    if "paper" in text:
        return "paper_group"
    if "panel" in text or "wood" in text:
        return "panel_wood_group"
    return "other_named_group"


def add_diagnostic_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().reset_index(drop=True)
    for col in ["svc_reliability_bin", "pred_log_bin", "size_bin", "artist_works_bin"]:
        if col not in out.columns:
            out[col] = "missing"
        out[col] = out[col].map(simple_bin)

    if "medium_support_bucket" in out.columns:
        out["medium_support_simple"] = out["medium_support_bucket"].map(medium_support_simple)
    else:
        out["medium_support_simple"] = "missing"

    svc_n = pd.to_numeric(out.get("svc_group_n", pd.Series([np.nan] * len(out))), errors="coerce")
    svc_iqr = pd.to_numeric(out.get("svc_group_log_price_iqr", pd.Series([np.nan] * len(out))), errors="coerce")
    artist_iqr = pd.to_numeric(out.get("artist_prior_iqr", pd.Series([np.nan] * len(out))), errors="coerce")

    risk: list[str] = []
    for idx, row in out.iterrows():
        svc = row["svc_reliability_bin"]
        pred = row["pred_log_bin"]
        size = row["size_bin"]
        works = row["artist_works_bin"]
        material = row["medium_support_simple"]
        n_value = svc_n.iloc[idx]
        svc_iqr_value = svc_iqr.iloc[idx]
        artist_iqr_value = artist_iqr.iloc[idx]

        if svc in {"low", "missing"} and works in {"low", "missing"}:
            label = "유사작품_적음+작가이력_적음"
        elif svc in {"low", "missing"} or (pd.notna(n_value) and n_value < 10):
            label = "유사작품_표본_부족"
        elif works in {"low", "missing"}:
            label = "작가이력_표본_부족"
        elif pred in {"high", "very_high"} and size in {"large", "very_large"}:
            label = "고가대형_꼬리구간"
        elif pred in {"high", "very_high", "mid_high"}:
            label = "고가_예측구간"
        elif pred in {"low", "very_low"} and size in {"small", "very_small"}:
            label = "저가소형_꼬리구간"
        elif material in {"unknown_or_other", "missing"}:
            label = "재료지지체_불확실"
        elif (pd.notna(svc_iqr_value) and svc_iqr_value >= 0.80) or (pd.notna(artist_iqr_value) and artist_iqr_value >= 1.00):
            label = "비교군_가격분산_큼"
        else:
            label = "중간_안정구간"
        risk.append(label)

    out["risk_cause"] = risk
    return out


def candidate_grid() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for hierarchy_name, hierarchy in HIERARCHIES.items():
        for min_rows in MIN_ROWS:
            for cap in CAPS:
                for strength in STRENGTHS:
                    for smooth_rows in SMOOTH_ROWS:
                        cap_code = str(cap).replace(".", "p")
                        strength_code = str(strength).replace(".", "p")
                        candidate = (
                            f"{EXP_ID}_cause_{hierarchy_name}_min{min_rows}"
                            f"_cap{cap_code}_s{strength_code}_smooth{smooth_rows}"
                        )
                        specs.append({
                            "candidate": candidate,
                            "hierarchy_name": hierarchy_name,
                            "hierarchy": hierarchy,
                            "min_rows": min_rows,
                            "cap": cap,
                            "strength": strength,
                            "smooth_rows": smooth_rows,
                        })
    return specs


def make_key(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    if not cols:
        return pd.Series(["__global__"] * len(frame), index=frame.index)
    return frame[cols].astype(str).agg("||".join, axis=1)


def correction_lookup(
    calibration: pd.DataFrame,
    target: pd.DataFrame,
    spec: dict[str, Any],
    base_pred_col: str = "current_pred_log",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    residual = calibration["ln_price_krw"].to_numpy(dtype=float) - calibration[base_pred_col].to_numpy(dtype=float)
    calibration = calibration.copy()
    calibration["_residual_for_correction"] = residual
    global_median = float(np.median(residual))

    correction = np.full(len(target), global_median, dtype=float)
    source_level = np.array(["global"] * len(target), dtype=object)
    source_n = np.full(len(target), len(calibration), dtype=float)

    for level, cols in enumerate(spec["hierarchy"]):
        if not cols:
            continue
        cal_key = make_key(calibration, cols)
        grouped = (
            calibration.assign(_key=cal_key)
            .groupby("_key", observed=False)["_residual_for_correction"]
            .agg(["median", "count"])
            .reset_index()
        )
        grouped = grouped[grouped["count"] >= int(spec["min_rows"])].copy()
        if grouped.empty:
            continue
        mapping = dict(zip(grouped["_key"], grouped["median"]))
        count_mapping = dict(zip(grouped["_key"], grouped["count"]))
        target_key = make_key(target, cols)
        mapped = target_key.map(mapping)
        mapped_n = target_key.map(count_mapping)
        mask = mapped.notna() & (source_level == "global")
        if mask.any():
            correction[mask.to_numpy()] = mapped[mask].to_numpy(dtype=float)
            source_n[mask.to_numpy()] = mapped_n[mask].to_numpy(dtype=float)
            source_level[mask.to_numpy()] = f"level{level + 1}:{'+'.join(cols)}"

    smooth_rows = float(spec["smooth_rows"])
    if smooth_rows > 0:
        shrink = source_n / np.clip(source_n + smooth_rows, 1.0, None)
        correction = correction * shrink

    raw_correction = correction.copy()
    correction = np.clip(correction, -float(spec["cap"]), float(spec["cap"])) * float(spec["strength"])
    return correction, raw_correction, source_n, source_level.tolist()


def add_metric_deltas(row: dict[str, Any], metric: dict[str, float], base: dict[str, float]) -> dict[str, Any]:
    for metric_name, value in metric.items():
        row[metric_name] = value
        if metric_name in base:
            row[f"delta_{metric_name}"] = value - base[metric_name]
    return row


def repeated_artist_holdout(val: pd.DataFrame, specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    val = val.reset_index(drop=True).copy()
    artist_series = val["artist_key"].astype(str).fillna("__MISSING__")
    artists = artist_series.unique()
    repeat_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    current_pred = val["current_pred_log"].to_numpy(dtype=float)

    for repeat in range(N_ARTIST_REPEATS):
        rng = np.random.default_rng(SEED + repeat)
        artist_folds = np.array_split(rng.permutation(artists), N_ARTIST_SPLITS)
        oof_preds = {spec["candidate"]: np.full(len(val), np.nan, dtype=float) for spec in specs}
        oof_abs_correction = {spec["candidate"]: [] for spec in specs}

        for fold, holdout_artists in enumerate(artist_folds, 1):
            holdout_mask = artist_series.isin(set(holdout_artists)).to_numpy()
            calibration = val.loc[~holdout_mask].copy()
            holdout = val.loc[holdout_mask].copy()
            holdout_idx = np.flatnonzero(holdout_mask)
            if calibration.empty or holdout.empty:
                continue
            fold_base = metric_from_pred(holdout, holdout["current_pred_log"].to_numpy(dtype=float))
            for spec in specs:
                correction, raw, source_n, source_level = correction_lookup(calibration, holdout, spec)
                pred = holdout["current_pred_log"].to_numpy(dtype=float) + correction
                oof_preds[spec["candidate"]][holdout_idx] = pred
                oof_abs_correction[spec["candidate"]].extend(np.abs(correction).tolist())
                metric = metric_from_pred(holdout, pred)
                row = {
                    "experiment_id": EXP_ID,
                    "split": "validation_artist_holdout_fold",
                    "repeat": repeat,
                    "fold": fold,
                    "candidate": spec["candidate"],
                    "hierarchy_name": spec["hierarchy_name"],
                    "min_rows": spec["min_rows"],
                    "cap": spec["cap"],
                    "strength": spec["strength"],
                    "smooth_rows": spec["smooth_rows"],
                    "n": len(holdout),
                    "n_artists_holdout": len(holdout_artists),
                    "mean_abs_correction": float(np.mean(np.abs(correction))),
                    "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
                    "raw_correction_median": float(np.median(raw)),
                    "median_source_n": float(np.median(source_n)),
                    "global_source_rate": float(np.mean(np.asarray(source_level, dtype=object) == "global")),
                }
                fold_rows.append(add_metric_deltas(row, metric, fold_base))

        for spec in specs:
            pred = oof_preds[spec["candidate"]]
            valid_mask = np.isfinite(pred)
            if not valid_mask.any():
                continue
            full_frame = val.loc[valid_mask].copy()
            base_metric = metric_from_pred(full_frame, current_pred[valid_mask])
            metric = metric_from_pred(full_frame, pred[valid_mask])
            abs_corr = np.asarray(oof_abs_correction[spec["candidate"]], dtype=float)
            row = {
                "experiment_id": EXP_ID,
                "split": "validation_artist_holdout_oof",
                "repeat": repeat,
                "candidate": spec["candidate"],
                "hierarchy_name": spec["hierarchy_name"],
                "min_rows": spec["min_rows"],
                "cap": spec["cap"],
                "strength": spec["strength"],
                "smooth_rows": spec["smooth_rows"],
                "mean_abs_correction": float(np.mean(abs_corr)),
                "p95_abs_correction": float(np.quantile(abs_corr, 0.95)),
            }
            repeat_rows.append(add_metric_deltas(row, metric, base_metric))

    return pd.DataFrame(repeat_rows), pd.DataFrame(fold_rows)


def summarize_validation(repeat_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in repeat_metrics.groupby("candidate", observed=False):
        first = group.iloc[0]
        row = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "hierarchy_name": first["hierarchy_name"],
            "min_rows": int(first["min_rows"]),
            "cap": float(first["cap"]),
            "strength": float(first["strength"]),
            "smooth_rows": int(first["smooth_rows"]),
            "repeats": int(group["repeat"].nunique()),
            "mean_abs_correction": float(group["mean_abs_correction"].mean()),
            "p95_abs_correction": float(group["p95_abs_correction"].mean()),
        }
        for metric in METRICS:
            delta = group[f"delta_{metric}"]
            row[f"mean_{metric}"] = float(group[metric].mean())
            row[f"mean_delta_{metric}"] = float(delta.mean())
            row[f"p10_delta_{metric}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric}"] = float(np.mean(delta < 0))
        row["balanced_score"] = (
            row["mean_delta_MdAPE"]
            + 0.50 * row["mean_delta_MAPE"]
            + 0.25 * row["mean_delta_p95_APE"]
        )
        row["tail_score"] = row["mean_delta_p95_APE"] + 0.50 * row["mean_delta_MAPE"]
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["balanced_score", "mean_delta_MdAPE", "mean_delta_MAPE"])


def select_specs(summary: pd.DataFrame, specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {spec["candidate"]: spec for spec in specs}
    selected_names: list[str] = []

    balanced_pool = summary[
        (summary["mean_delta_MdAPE"] < 0)
        & (summary["mean_delta_MAPE"] < 0)
        & (summary["mean_delta_p95_APE"] < 0)
        & (summary["improvement_probability_MdAPE"] >= 0.70)
        & (summary["improvement_probability_MAPE"] >= 0.70)
        & (summary["improvement_probability_p95_APE"] >= 0.70)
    ].sort_values(["balanced_score", "mean_delta_MdAPE"])
    tail_pool = summary[
        (summary["mean_delta_MAPE"] < 0)
        & (summary["mean_delta_p95_APE"] < 0)
        & (summary["improvement_probability_MAPE"] >= 0.70)
        & (summary["improvement_probability_p95_APE"] >= 0.70)
    ].sort_values(["tail_score", "mean_delta_p95_APE"])
    mdape_pool = summary[
        (summary["mean_delta_MdAPE"] < 0)
        & (summary["improvement_probability_MdAPE"] >= 0.70)
    ].sort_values(["mean_delta_MdAPE", "mean_delta_MAPE"])

    for pool in [balanced_pool, tail_pool, mdape_pool, summary.sort_values(["balanced_score"])]:
        for candidate in pool["candidate"].head(3).tolist():
            if candidate not in selected_names:
                selected_names.append(candidate)
            if len(selected_names) >= 6:
                break
        if len(selected_names) >= 6:
            break

    return [by_name[name] for name in selected_names if name in by_name]


def prediction_frame(
    split: str,
    candidate: str,
    role: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray | None,
    spec: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "split": split,
        "candidate": candidate,
        "role": role,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "source_artwork_id": frame.get("source_artwork_id", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "title_raw": frame.get("title_raw", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "current_pred_log": frame["current_pred_log"].to_numpy(dtype=float),
    })
    for col in [
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "medium_support_simple",
        "svc_reliability_bin",
        "pred_log_bin",
        "size_bin",
        "artist_works_bin",
        "risk_cause",
        "svc_group_n",
        "svc_group_log_price_median",
        "svc_group_log_price_iqr",
        "artist_prior_n_log",
        "artist_prior_iqr",
    ]:
        if col in frame.columns:
            out[col] = frame[col].to_numpy()
    if correction is None:
        correction = np.zeros(len(frame), dtype=float)
    out["correction_log"] = np.asarray(correction, dtype=float)
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    if spec:
        out["hierarchy_name"] = spec["hierarchy_name"]
        out["min_rows"] = spec["min_rows"]
        out["cap"] = spec["cap"]
        out["strength"] = spec["strength"]
        out["smooth_rows"] = spec["smooth_rows"]
    return out


def test_once_predictions(val: pd.DataFrame, test: pd.DataFrame, selected_specs: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    parts: list[pd.DataFrame] = []
    base_pred = test["current_pred_log"].to_numpy(dtype=float)
    base_metric = metric_from_pred(test, base_pred)
    base_row = {
        "experiment_id": EXP_ID,
        "split": "test_once",
        "candidate": CURRENT_CANDIDATE,
        "role": "현재 Warm 기준 조합",
        "hierarchy_name": "reference",
        "min_rows": np.nan,
        "cap": np.nan,
        "strength": np.nan,
        "smooth_rows": np.nan,
        "mean_abs_correction": 0.0,
        "p95_abs_correction": 0.0,
    }
    rows.append(add_metric_deltas(base_row, base_metric, base_metric))
    parts.append(prediction_frame("test_once", CURRENT_CANDIDATE, "현재 Warm 기준 조합", test, base_pred, None))

    for spec in selected_specs:
        correction, raw, source_n, source_level = correction_lookup(val, test, spec)
        pred = base_pred + correction
        metric = metric_from_pred(test, pred)
        row = {
            "experiment_id": EXP_ID,
            "split": "test_once",
            "candidate": spec["candidate"],
            "role": "원인 기반 보정 후보",
            "hierarchy_name": spec["hierarchy_name"],
            "min_rows": spec["min_rows"],
            "cap": spec["cap"],
            "strength": spec["strength"],
            "smooth_rows": spec["smooth_rows"],
            "mean_abs_correction": float(np.mean(np.abs(correction))),
            "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
            "raw_correction_median": float(np.median(raw)),
            "median_source_n": float(np.median(source_n)),
            "global_source_rate": float(np.mean(np.asarray(source_level, dtype=object) == "global")),
        }
        rows.append(add_metric_deltas(row, metric, base_metric))
        parts.append(prediction_frame("test_once", spec["candidate"], "원인 기반 보정 후보", test, pred, correction, spec))

    return pd.DataFrame(rows), pd.concat(parts, ignore_index=True)


def error_direction(residual_log: float, ape: float) -> str:
    if ape <= 0.30:
        return "정상범위"
    if residual_log > 0:
        return "과소예측"
    return "과대예측"


def error_severity(ape: float) -> str:
    if ape <= 0.30:
        return "정상"
    if ape <= 0.50:
        return "중간오차"
    if ape <= 1.00:
        return "큰오차"
    return "극단오차"


def diagnosis_text(row: pd.Series) -> str:
    severity = row["error_severity"]
    if severity == "정상":
        return "현재 조합이 허용 오차 안에서 작동"
    direction = row["error_direction"]
    risk = str(row["risk_cause"])
    if "유사작품" in risk or "작가이력" in risk:
        return f"{direction}. 같은 작가/유사 작품 표본이 적어 작가 가격 기준선이 약함"
    if "고가대형" in risk or "고가" in risk:
        return f"{direction}. 고가 구간은 분산이 커서 Huber가 평균적인 방향으로 눌러 예측할 수 있음"
    if "저가소형" in risk:
        return f"{direction}. 저가·소형 꼬리 구간은 작은 금액 차이도 비율 오차가 크게 보임"
    if "재료지지체" in risk:
        return f"{direction}. 재료/지지체 정보가 불확실해 유사 작품 묶음의 기준이 흔들릴 수 있음"
    if "가격분산" in risk:
        return f"{direction}. 같은 비교군 안에서도 가격 분산이 커 대표값 보정이 어려움"
    return f"{direction}. 현재 피처 조합으로 설명되지 않은 잔여 오차"


def artwork_error_diagnostics(test_predictions: pd.DataFrame, selected_candidate: str | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = test_predictions[test_predictions["candidate"].eq(CURRENT_CANDIDATE)].copy()
    base["error_direction"] = [error_direction(r, a) for r, a in zip(base["residual_log"], base["ape"])]
    base["error_severity"] = base["ape"].map(error_severity)
    base["diagnosis"] = base.apply(diagnosis_text, axis=1)

    if selected_candidate and selected_candidate in set(test_predictions["candidate"]):
        cand = test_predictions[test_predictions["candidate"].eq(selected_candidate)][[
            "_track6_row_id",
            "pred_log",
            "pred_price",
            "ape",
            "correction_log",
        ]].rename(columns={
            "pred_log": "adjusted_pred_log",
            "pred_price": "adjusted_pred_price",
            "ape": "adjusted_ape",
            "correction_log": "adjusted_correction_log",
        })
        base = base.merge(cand, on="_track6_row_id", how="left")
        base["delta_ape_after_adjustment"] = base["adjusted_ape"] - base["ape"]
        base["adjustment_result"] = np.where(
            base["delta_ape_after_adjustment"] < -0.01,
            "개선",
            np.where(base["delta_ape_after_adjustment"] > 0.01, "악화", "유지"),
        )
    else:
        base["adjusted_pred_log"] = np.nan
        base["adjusted_pred_price"] = np.nan
        base["adjusted_ape"] = np.nan
        base["adjusted_correction_log"] = np.nan
        base["delta_ape_after_adjustment"] = np.nan
        base["adjustment_result"] = "미적용"

    summary_rows: list[dict[str, Any]] = []
    for (risk, direction, severity), group in base.groupby(["risk_cause", "error_direction", "error_severity"], observed=False):
        row = {
            "risk_cause": risk,
            "error_direction": direction,
            "error_severity": severity,
            "n": int(len(group)),
            "current_MdAPE": float(group["ape"].median()),
            "current_MAPE": float(group["ape"].mean()),
            "current_p95_APE": float(group["ape"].quantile(0.95)),
            "median_residual_log": float(group["residual_log"].median()),
        }
        if "adjusted_ape" in group and group["adjusted_ape"].notna().any():
            row["adjusted_MdAPE"] = float(group["adjusted_ape"].median())
            row["adjusted_MAPE"] = float(group["adjusted_ape"].mean())
            row["adjusted_p95_APE"] = float(group["adjusted_ape"].quantile(0.95))
            row["delta_MdAPE_after_adjustment"] = row["adjusted_MdAPE"] - row["current_MdAPE"]
            row["improved_row_rate"] = float(np.mean(group["delta_ape_after_adjustment"] < -0.01))
            row["worsened_row_rate"] = float(np.mean(group["delta_ape_after_adjustment"] > 0.01))
        summary_rows.append(row)

    cause_summary = pd.DataFrame(summary_rows).sort_values(["current_p95_APE", "current_MAPE"], ascending=False)
    top_errors = base.sort_values("ape", ascending=False).head(80).copy()
    return base.sort_values("ape", ascending=False), cause_summary, top_errors


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    out = frame.copy()
    if max_rows is not None:
        out = out.head(max_rows)

    def fmt(value: Any) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.5g}"
        return str(value).replace("|", "\\|").replace("\n", " ")

    columns = [str(col) for col in out.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in out.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def md_to_html(markdown_text: str) -> str:
    body_lines: list[str] = []
    in_table = False
    for line in markdown_text.splitlines():
        if line.startswith("| ") and line.endswith(" |"):
            body_lines.append(line)
            in_table = True
            continue
        if in_table:
            in_table = False
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            body_lines.append(f"<p class='bullet'>{html.escape(line)}</p>")
        elif line.strip() == "":
            body_lines.append("")
        else:
            body_lines.append(f"<p>{html.escape(line)}</p>")

    # Convert markdown tables with pandas for readability.
    converted: list[str] = []
    table_buffer: list[str] = []
    for line in body_lines:
        if line.startswith("| "):
            table_buffer.append(line)
            continue
        if table_buffer:
            converted.append(markdown_table_to_html(table_buffer))
            table_buffer = []
        converted.append(line)
    if table_buffer:
        converted.append(markdown_table_to_html(table_buffer))

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(TITLE)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 32px; color: #1f2937; line-height: 1.55; }}
    h1 {{ font-size: 28px; margin-bottom: 12px; }}
    h2 {{ margin-top: 32px; border-bottom: 1px solid #d8dee9; padding-bottom: 8px; }}
    h3 {{ margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; font-size: 13px; }}
    th, td {{ border: 1px solid #d8dee9; padding: 7px 9px; vertical-align: top; }}
    th {{ background: #f3f4f6; text-align: left; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
    .bullet {{ margin: 3px 0; }}
  </style>
</head>
<body>
{chr(10).join(converted)}
</body>
</html>
"""


def markdown_table_to_html(lines: list[str]) -> str:
    rows = []
    for idx, line in enumerate(lines):
        if idx == 1 and set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        tag = "th" if idx == 0 else "td"
        rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
    return "<table>" + "\n".join(rows) + "</table>"


def render_report(
    validation_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    selected_specs: list[dict[str, Any]],
    cause_summary: pd.DataFrame,
    top_errors: pd.DataFrame,
    selected_candidate: str | None,
) -> tuple[str, str]:
    top_validation = validation_summary[[
        "candidate",
        "hierarchy_name",
        "min_rows",
        "cap",
        "strength",
        "smooth_rows",
        "mean_delta_MdAPE",
        "mean_delta_MAPE",
        "mean_delta_p95_APE",
        "improvement_probability_MdAPE",
        "improvement_probability_MAPE",
        "improvement_probability_p95_APE",
        "balanced_score",
    ]].head(15).copy()

    test_view = test_metrics[[
        "candidate",
        "role",
        "hierarchy_name",
        "MdAPE",
        "MAPE",
        "p95_APE",
        "RMSE_log",
        "delta_MdAPE",
        "delta_MAPE",
        "delta_p95_APE",
        "mean_abs_correction",
        "p95_abs_correction",
    ]].copy()

    selected_view = pd.DataFrame([{
        "candidate": spec["candidate"],
        "hierarchy": " > ".join(["+".join(level) if level else "global" for level in spec["hierarchy"]]),
        "min_rows": spec["min_rows"],
        "cap": spec["cap"],
        "strength": spec["strength"],
        "smooth_rows": spec["smooth_rows"],
    } for spec in selected_specs])

    cause_view = cause_summary[[
        "risk_cause",
        "error_direction",
        "error_severity",
        "n",
        "current_MdAPE",
        "current_MAPE",
        "current_p95_APE",
        "median_residual_log",
        "adjusted_MdAPE",
        "adjusted_MAPE",
        "adjusted_p95_APE",
        "delta_MdAPE_after_adjustment",
        "improved_row_rate",
        "worsened_row_rate",
    ]].head(30).copy()

    top_error_view = top_errors[[
        "_track6_row_id",
        "title_raw",
        "artist_name_ko",
        "actual_price",
        "pred_price",
        "ape",
        "error_direction",
        "error_severity",
        "risk_cause",
        "diagnosis",
        "adjusted_pred_price",
        "adjusted_ape",
        "delta_ape_after_adjustment",
        "adjustment_result",
    ]].head(30).copy()

    best_test = test_metrics.sort_values(["MdAPE", "MAPE"]).iloc[0]
    base_test = test_metrics[test_metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    selected_test = None
    if selected_candidate and selected_candidate in set(test_metrics["candidate"]):
        selected_test = test_metrics[test_metrics["candidate"].eq(selected_candidate)].iloc[0]

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 Warm 후보: `{CURRENT_CANDIDATE}`",
        "- 기존 확인: PP-WHUBER9에는 구간별 진단은 있었지만, 작품별 원인 라벨을 만들고 그 원인별 보정값을 검증한 실험은 별도로 확인되지 않았음",
        "- 이번 실험: 작품별 오차 원인을 먼저 정리하고, 같은 원인군에서 반복되는 로그 오차 중앙값을 작은 보정값으로 적용",
        "- 누수 방지: test 오차는 분석표 작성에만 사용. 보정값 선택은 validation 작가 단위 holdout에서만 진행",
        "",
        "## 1. 실행 결론",
        "",
        f"- 기준 후보 test MdAPE/MAPE/p95: `{base_test['MdAPE']:.4f}` / `{base_test['MAPE']:.4f}` / `{base_test['p95_APE']:.4f}`",
        f"- 원인 기반 보정 test 최상위 MdAPE/MAPE/p95: `{best_test['MdAPE']:.4f}` / `{best_test['MAPE']:.4f}` / `{best_test['p95_APE']:.4f}`",
        f"- 작품별 상세 비교 적용 후보: `{selected_candidate or '없음'}`",
        (
            f"- 상세 비교 후보 test MdAPE/MAPE/p95: `{selected_test['MdAPE']:.4f}` / `{selected_test['MAPE']:.4f}` / `{selected_test['p95_APE']:.4f}`"
            if selected_test is not None
            else "- 상세 비교 후보 test 성능: 없음"
        ),
        "- 주의: test 최상위 후보는 사후 확인값이며, 운영 후보 판단은 validation 작가 holdout 선택 순서를 우선함",
        "- 판단: 원인 기반 보정은 MdAPE 또는 p95_APE를 일부 낮추는 후보가 있으나 MAPE가 동반 악화되어 현재 v0.1 기본 모델 대체 후보로는 부족함",
        "- 활용 방향: 큰 오차 방어, 특정 원인군 진단, 후속 보정 설계의 근거로 사용",
        "- 해석: Huber Warm은 큰 오차를 완전히 따라가지 않도록 눌러 학습하므로, 반복적으로 남는 원인군에 작은 로그 보정을 더하면 특정 구간의 오차를 낮출 수 있음",
        "- 단, 작품별 원인을 보고 만든 보정은 과적합 위험이 커서 validation 작가 holdout과 test 악화 작품 수를 함께 봐야 함",
        "",
        "## 2. 실험 방법",
        "",
        "- 1단계: 현재 Warm 최고 조합의 test 예측값과 실제값을 작품별로 비교",
        "- 2단계: 오차 방향을 과소예측/과대예측으로 나누고, 유사 작품 표본 부족, 작가 이력 부족, 고가·대형 꼬리 구간, 재료/지지체 불확실, 비교군 가격 분산 큼 등으로 원인 라벨 부여",
        "- 3단계: validation에서 같은 원인군의 `실제 로그가격 - 예측 로그가격` 중앙값을 보정값으로 계산",
        "- 4단계: 보정값은 최대 보정폭과 적용 강도를 제한해 Huber의 안정성을 유지",
        "- 5단계: 작가 단위 holdout으로 보정 규칙을 고르고, test에는 한 번만 적용",
        "",
        "## 3. 선택된 원인 기반 보정 후보",
        "",
        markdown_table(selected_view),
        "",
        "## 4. Validation 작가 holdout 상위 후보",
        "",
        markdown_table(top_validation),
        "",
        "## 5. Test 성능 비교",
        "",
        markdown_table(test_view),
        "",
        "## 6. 작품별 원인 요약",
        "",
        markdown_table(cause_view),
        "",
        "## 7. 오차 큰 작품 예시",
        "",
        markdown_table(top_error_view),
        "",
        "## 8. 산출물",
        "",
        "- `outputs/validation_artist_holdout_summary.csv`: validation 기준 후보별 안정성",
        "- `outputs/test_once_metrics.csv`: test 기준 성능 비교",
        "- `outputs/test_artwork_error_diagnostics.csv`: 작품별 실제값/예측값/오차 원인/보정 후 변화",
        "- `outputs/test_cause_summary.csv`: 원인군별 개선·악화 요약",
        "- `outputs/test_top_error_examples.csv`: 오차 상위 작품 예시",
    ]
    markdown = "\n".join(lines)
    return markdown, md_to_html(markdown)


def main() -> None:
    ensure_dirs()
    val, test = load_frames()
    specs = candidate_grid()
    repeat_metrics, fold_metrics = repeated_artist_holdout(val, specs)
    validation_summary = summarize_validation(repeat_metrics)
    selected_specs = select_specs(validation_summary, specs)
    test_metrics, test_predictions = test_once_predictions(val, test, selected_specs)

    non_base = test_metrics[~test_metrics["candidate"].eq(CURRENT_CANDIDATE)].copy()
    if selected_specs:
        selected_candidate = selected_specs[0]["candidate"]
    elif non_base.empty:
        selected_candidate = None
    else:
        selected_candidate = non_base.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]["candidate"]

    diagnostics, cause_summary, top_errors = artwork_error_diagnostics(test_predictions, selected_candidate)
    markdown, html_report = render_report(validation_summary, test_metrics, selected_specs, cause_summary, top_errors, selected_candidate)

    repeat_metrics.to_csv(EXP_DIR / "outputs" / "validation_artist_holdout_repeat_metrics.csv", index=False)
    fold_metrics.to_csv(EXP_DIR / "outputs" / "validation_artist_holdout_fold_metrics.csv", index=False)
    validation_summary.to_csv(EXP_DIR / "outputs" / "validation_artist_holdout_summary.csv", index=False)
    test_metrics.to_csv(EXP_DIR / "outputs" / "test_once_metrics.csv", index=False)
    test_predictions.to_csv(EXP_DIR / "outputs" / "test_once_predictions.csv", index=False)
    diagnostics.to_csv(EXP_DIR / "outputs" / "test_artwork_error_diagnostics.csv", index=False)
    cause_summary.to_csv(EXP_DIR / "outputs" / "test_cause_summary.csv", index=False)
    top_errors.to_csv(EXP_DIR / "outputs" / "test_top_error_examples.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "current_candidate": CURRENT_CANDIDATE,
        "seed": SEED,
        "n_artist_splits": N_ARTIST_SPLITS,
        "n_artist_repeats": N_ARTIST_REPEATS,
        "hierarchies": HIERARCHIES,
        "min_rows": MIN_ROWS,
        "caps": CAPS,
        "strengths": STRENGTHS,
        "smooth_rows": SMOOTH_ROWS,
        "selected_candidates": [spec["candidate"] for spec in selected_specs],
        "validation_selected_candidate_for_artwork_diagnostics": selected_candidate,
        "best_test_candidate": None if non_base.empty else non_base.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]["candidate"],
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path = EXP_DIR / "reports" / "PP-WHUBER10_warm_artwork_error_cause_correction.md"
    html_path = EXP_DIR / "reports" / "PP-WHUBER10_warm_artwork_error_cause_correction.html"
    doc_md_path = DOC_ROOT / "PP-WHUBER10_warm_artwork_error_cause_correction.md"
    doc_html_path = DOC_ROOT / "PP-WHUBER10_warm_artwork_error_cause_correction.html"
    for path, content in [
        (report_path, markdown),
        (doc_md_path, markdown),
        (html_path, html_report),
        (doc_html_path, html_report),
    ]:
        path.write_text(content, encoding="utf-8")

    print(f"[{EXP_ID}] validation candidates: {len(validation_summary)}")
    print(f"[{EXP_ID}] selected candidates: {[spec['candidate'] for spec in selected_specs]}")
    best_test_candidate = None if non_base.empty else non_base.sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0]["candidate"]
    print(f"[{EXP_ID}] validation-selected diagnostics candidate: {selected_candidate}")
    print(f"[{EXP_ID}] best test candidate: {best_test_candidate}")
    print(test_metrics[["candidate", "MdAPE", "MAPE", "p95_APE", "delta_MdAPE", "delta_MAPE", "delta_p95_APE"]].to_string(index=False))
    print(f"[{EXP_ID}] report: {report_path}")


if __name__ == "__main__":
    main()
