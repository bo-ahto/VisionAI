#!/usr/bin/env python3
"""Run PP-WHUBER9 purpose-specific validation for Warm residual Huber corrections.

PP-WHUBER8 showed that the Warm residual Huber correction should not be
promoted as one generic replacement. This follow-up validates the same
candidate family by purpose:

- representative accuracy
- conservative stability
- large-error defense
- MdAPE-only research signal

The main added check is artist-level repeated holdout. Rows from the same
artist are held out together, so the residual correction must work on an
artist group it did not see during calibration.
"""
from __future__ import annotations

import html
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_whuber8_warm_residual_oof_revalidation as whuber8  # noqa: E402


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values.*")


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER9"
EXP_SLUG = "PP-WHUBER9_warm_purpose_specific_residual_validation"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm residual Huber 목적별 추가 검증"
SEED = 20260606
N_ARTIST_SPLITS = 5
N_ARTIST_REPEATS = 12
BOOTSTRAP_ITERATIONS = 400
MIN_SEGMENT_ROWS = 20

CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE

PURPOSE_SPECS: list[dict[str, Any]] = [
    {
        "purpose": "대표 정확도 후보",
        "candidate": "PP-WHUBER7_balanced_all_metric_predbin_mid_open_tail_guard",
        "description": "test에서 MdAPE/MAPE/p95가 모두 개선된 균형 후보",
        "primary_metrics": ["MdAPE", "MAPE", "p95_APE"],
        "decision_focus": "중앙 정확도 개선을 우선하되 p95 악화가 없어야 함",
    },
    {
        "purpose": "보수형 안정성 후보",
        "candidate": "PP-WHUBER7_validation_balanced_predbin_mid_open_tail_guard",
        "description": "반복 OOF에서 가장 안정적으로 개선된 후보",
        "primary_metrics": ["MdAPE", "MAPE", "p95_APE"],
        "decision_focus": "작가 단위 holdout에서도 세 지표 개선 확률이 높아야 함",
    },
    {
        "purpose": "큰 오차 방어 후보",
        "candidate": "PP-WHUBER7_tail_guard_directional_under",
        "description": "test에서 p95_APE와 MAPE 방어가 가장 명확한 후보",
        "primary_metrics": ["MAPE", "p95_APE"],
        "decision_focus": "MdAPE 개선폭보다 MAPE와 p95_APE 감소를 우선함",
    },
    {
        "purpose": "MdAPE 연구 후보",
        "candidate": "PP-WHUBER7_mdape_best_predbin_mid_open_tail_guard",
        "description": "test MdAPE는 가장 낮지만 p95_APE가 악화된 후보",
        "primary_metrics": ["MdAPE"],
        "decision_focus": "운영 기본 후보가 아니라 중앙값 정확도 개선 원인 분석용",
    },
]

PURPOSE_CANDIDATES = [spec["candidate"] for spec in PURPOSE_SPECS]
CANDIDATE_SPECS = [spec for spec in whuber8.CANDIDATE_SPECS if spec["candidate"] in PURPOSE_CANDIDATES]
SEGMENT_COLUMNS = ["svc_reliability_bin", "pred_log_bin", "size_bin", "artist_works_bin"]


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_pred(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return wcoef.metric_values(frame, pred_log)


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


def candidate_features(spec: dict[str, Any], frame: pd.DataFrame) -> list[str]:
    return whuber8.candidate_features(spec, frame)


def predict_candidate(calibration: pd.DataFrame, target: pd.DataFrame, spec: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    features = candidate_features(spec, calibration)
    raw = whuber8.fit_predict_raw(calibration, target, features, float(spec["alpha"]), float(spec["epsilon"]))
    correction = whuber8.apply_correction(target, raw, spec)
    pred = target["current_pred_log"].to_numpy(dtype=float) + correction
    return pred, correction


def prediction_frame(
    split: str,
    candidate: str,
    role: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    correction: np.ndarray | None = None,
    repeat: int | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "split": split,
        "repeat": np.nan if repeat is None else repeat,
        "candidate": candidate,
        "role": role,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "current_pred_log": frame["current_pred_log"].to_numpy(dtype=float),
    })
    for col in SEGMENT_COLUMNS:
        out[col] = frame.get(col, pd.Series(["missing"] * len(frame))).astype(str).to_numpy()
    if correction is None:
        correction = np.zeros(len(frame), dtype=float)
    out["correction_log"] = np.asarray(correction, dtype=float)
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def add_metric_deltas(row: dict[str, Any], metric: dict[str, float], base: dict[str, float]) -> dict[str, Any]:
    for name, value in metric.items():
        row[name] = value
        if name in base:
            row[f"delta_{name}"] = value - base[name]
    return row


def repeated_artist_holdout(val: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    val = val.reset_index(drop=True).copy()
    artist_series = val["artist_key"].astype(str).fillna("__MISSING__")
    artists = artist_series.unique()
    repeat_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    prediction_parts: list[pd.DataFrame] = []

    current_pred = val["current_pred_log"].to_numpy(dtype=float)
    current_metric = metric_from_pred(val, current_pred)

    for repeat in range(N_ARTIST_REPEATS):
        rng = np.random.default_rng(SEED + repeat)
        shuffled = rng.permutation(artists)
        artist_folds = np.array_split(shuffled, N_ARTIST_SPLITS)
        oof_preds = {spec["candidate"]: np.full(len(val), np.nan, dtype=float) for spec in CANDIDATE_SPECS}
        oof_corrections = {spec["candidate"]: np.zeros(len(val), dtype=float) for spec in CANDIDATE_SPECS}

        for fold, holdout_artists in enumerate(artist_folds, 1):
            holdout_mask = artist_series.isin(set(holdout_artists)).to_numpy()
            calibration = val.loc[~holdout_mask].copy()
            holdout = val.loc[holdout_mask].copy()
            holdout_idx = np.flatnonzero(holdout_mask)
            if holdout.empty or calibration.empty:
                continue
            current_holdout = holdout["current_pred_log"].to_numpy(dtype=float)
            fold_base = metric_from_pred(holdout, current_holdout)

            for spec in CANDIDATE_SPECS:
                pred, correction = predict_candidate(calibration, holdout, spec)
                oof_preds[spec["candidate"]][holdout_idx] = pred
                oof_corrections[spec["candidate"]][holdout_idx] = correction
                metric = metric_from_pred(holdout, pred)
                row = {
                    "experiment_id": EXP_ID,
                    "split": "validation_artist_holdout_fold",
                    "repeat": repeat,
                    "fold": fold,
                    "candidate": spec["candidate"],
                    "role": spec["role"],
                    "method": spec["method"],
                    "feature_set": spec["feature_set"],
                    "epsilon": spec["epsilon"],
                    "alpha": spec["alpha"],
                    "correction_cap": spec["cap"],
                    "correction_strength": spec["strength"],
                    "correction_policy": spec["policy"],
                    "n_artists_holdout": int(len(holdout_artists)),
                    "mean_abs_correction": float(np.mean(np.abs(correction))),
                    "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
                }
                fold_rows.append(add_metric_deltas(row, metric, fold_base))

        for spec in CANDIDATE_SPECS:
            pred = oof_preds[spec["candidate"]]
            correction = oof_corrections[spec["candidate"]]
            valid_mask = np.isfinite(pred)
            full_frame = val.loc[valid_mask].copy()
            metric = metric_from_pred(full_frame, pred[valid_mask])
            repeat_base = metric_from_pred(full_frame, current_pred[valid_mask])
            row = {
                "experiment_id": EXP_ID,
                "split": "validation_artist_holdout_oof",
                "repeat": repeat,
                "candidate": spec["candidate"],
                "role": spec["role"],
                "method": spec["method"],
                "feature_set": spec["feature_set"],
                "epsilon": spec["epsilon"],
                "alpha": spec["alpha"],
                "correction_cap": spec["cap"],
                "correction_strength": spec["strength"],
                "correction_policy": spec["policy"],
                "mean_abs_correction": float(np.mean(np.abs(correction[valid_mask]))),
                "p95_abs_correction": float(np.quantile(np.abs(correction[valid_mask]), 0.95)),
            }
            repeat_rows.append(add_metric_deltas(row, metric, repeat_base))
            prediction_parts.append(prediction_frame(
                "validation_artist_holdout_oof",
                spec["candidate"],
                spec["role"],
                full_frame,
                pred[valid_mask],
                correction[valid_mask],
                repeat,
            ))

    return pd.DataFrame(repeat_rows), pd.DataFrame(fold_rows), pd.concat(prediction_parts, ignore_index=True)


def summarize_repeated_metrics(repeat_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate, group in repeat_metrics.groupby("candidate", observed=False):
        first = group.iloc[0]
        row = {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "role": first["role"],
            "method": first["method"],
            "feature_set": first["feature_set"],
            "epsilon": first["epsilon"],
            "alpha": first["alpha"],
            "correction_cap": first["correction_cap"],
            "correction_strength": first["correction_strength"],
            "correction_policy": first["correction_policy"],
            "repeats": int(group["repeat"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]:
            delta = group[f"delta_{metric}"]
            row[f"mean_{metric}"] = float(group[metric].mean())
            row[f"std_{metric}"] = float(group[metric].std(ddof=0))
            row[f"mean_delta_{metric}"] = float(delta.mean())
            row[f"p10_delta_{metric}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric}"] = float(np.mean(delta < 0))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["mean_delta_MdAPE", "mean_delta_MAPE", "mean_delta_p95_APE"])


def test_once_predictions(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    parts: list[pd.DataFrame] = []
    base_pred = test["current_pred_log"].to_numpy(dtype=float)
    base_metric = metric_from_pred(test, base_pred)
    base_row = {
        "experiment_id": EXP_ID,
        "split": "test_once",
        "candidate": CURRENT_CANDIDATE,
        "role": "기준 후보",
        "method": "reference",
        "feature_set": "reference",
        "epsilon": np.nan,
        "alpha": np.nan,
        "correction_cap": np.nan,
        "correction_strength": np.nan,
        "correction_policy": "",
        "mean_abs_correction": 0.0,
        "p95_abs_correction": 0.0,
    }
    rows.append(add_metric_deltas(base_row, base_metric, base_metric))
    parts.append(prediction_frame("test_once", CURRENT_CANDIDATE, "기준 후보", test, base_pred, None))

    for spec in CANDIDATE_SPECS:
        pred, correction = predict_candidate(val, test, spec)
        metric = metric_from_pred(test, pred)
        row = {
            "experiment_id": EXP_ID,
            "split": "test_once",
            "candidate": spec["candidate"],
            "role": spec["role"],
            "method": spec["method"],
            "feature_set": spec["feature_set"],
            "epsilon": spec["epsilon"],
            "alpha": spec["alpha"],
            "correction_cap": spec["cap"],
            "correction_strength": spec["strength"],
            "correction_policy": spec["policy"],
            "mean_abs_correction": float(np.mean(np.abs(correction))),
            "p95_abs_correction": float(np.quantile(np.abs(correction), 0.95)),
        }
        rows.append(add_metric_deltas(row, metric, base_metric))
        parts.append(prediction_frame("test_once", spec["candidate"], spec["role"], test, pred, correction))
    return pd.DataFrame(rows), pd.concat(parts, ignore_index=True)


def bootstrap_test_predictions(test_predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    wide = test_predictions.pivot_table(
        index=["_track6_row_id", "artist_key"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    actual = test_predictions[[
        "_track6_row_id",
        "artist_key",
        "actual_log",
        "actual_price",
    ]].drop_duplicates("_track6_row_id")
    wide = wide.merge(actual, on=["_track6_row_id", "artist_key"], how="inner").reset_index(drop=True)
    candidates = [CURRENT_CANDIDATE] + [candidate for candidate in PURPOSE_CANDIDATES if candidate in wide.columns]
    rng = np.random.default_rng(SEED + 910)
    artists = wide["artist_key"].astype(str).unique()
    artist_to_indices = {artist: wide.index[wide["artist_key"].astype(str).eq(artist)].to_numpy() for artist in artists}
    sample_rows: list[dict[str, Any]] = []

    def add_sample(indices: np.ndarray, sample_type: str, iteration: int) -> None:
        actual_price = wide.loc[indices, "actual_price"].to_numpy(dtype=float)
        actual_log = wide.loc[indices, "actual_log"].to_numpy(dtype=float)
        base_metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, CURRENT_CANDIDATE].to_numpy(dtype=float))
        for candidate in candidates:
            metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, candidate].to_numpy(dtype=float))
            row = {
                "experiment_id": EXP_ID,
                "sample_type": sample_type,
                "iteration": iteration,
                "candidate": candidate,
            }
            sample_rows.append(add_metric_deltas(row, metric, base_metric))

    n = len(wide)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        add_sample(rng.integers(0, n, size=n), "row_bootstrap", iteration)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        add_sample(np.concatenate([artist_to_indices[artist] for artist in sampled_artists]), "artist_bootstrap", iteration)

    samples = pd.DataFrame(sample_rows)
    summary_rows: list[dict[str, Any]] = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"], observed=False):
        row = {
            "experiment_id": EXP_ID,
            "sample_type": sample_type,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]:
            delta = group[f"delta_{metric}"]
            row[f"mean_delta_{metric}"] = float(delta.mean())
            row[f"p10_delta_{metric}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{metric}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{metric}"] = float(np.mean(delta < 0))
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), samples


def segment_diagnostics(test_predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    base = test_predictions[test_predictions["candidate"].eq(CURRENT_CANDIDATE)].copy()
    for segment_col in SEGMENT_COLUMNS:
        for segment_value, segment_base in base.groupby(segment_col, observed=False):
            if len(segment_base) < MIN_SEGMENT_ROWS:
                continue
            ids = set(segment_base["_track6_row_id"].tolist())
            base_metric = metric_from_arrays(
                segment_base["actual_price"].to_numpy(dtype=float),
                segment_base["actual_log"].to_numpy(dtype=float),
                segment_base["pred_log"].to_numpy(dtype=float),
            )
            for candidate in PURPOSE_CANDIDATES:
                sub = test_predictions[
                    test_predictions["candidate"].eq(candidate)
                    & test_predictions["_track6_row_id"].isin(ids)
                ].copy()
                if len(sub) != len(segment_base):
                    continue
                metric = metric_from_arrays(
                    sub["actual_price"].to_numpy(dtype=float),
                    sub["actual_log"].to_numpy(dtype=float),
                    sub["pred_log"].to_numpy(dtype=float),
                )
                row = {
                    "experiment_id": EXP_ID,
                    "candidate": candidate,
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "n": int(len(sub)),
                }
                rows.append(add_metric_deltas(row, metric, base_metric))
    return pd.DataFrame(rows)


def worse_segment_count(segment_diag: pd.DataFrame, candidate: str, metrics: list[str]) -> int:
    sub = segment_diag[segment_diag["candidate"].eq(candidate)].copy()
    if sub.empty:
        return 0
    mask = np.zeros(len(sub), dtype=bool)
    for metric in metrics:
        mask |= sub[f"delta_{metric}"].to_numpy(dtype=float) > 0
    return int(mask.sum())


def lookup_metric(frame: pd.DataFrame, candidate: str, **filters: Any) -> pd.Series | None:
    sub = frame[frame["candidate"].eq(candidate)].copy()
    for key, value in filters.items():
        sub = sub[sub[key].eq(value)]
    if sub.empty:
        return None
    return sub.iloc[0]


def decision_text(
    purpose: str,
    candidate: str,
    primary_metrics: list[str],
    artist_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    segment_diag: pd.DataFrame,
) -> str:
    artist_row = lookup_metric(artist_summary, candidate)
    test_row = lookup_metric(test_metrics, candidate)
    artist_boot = lookup_metric(bootstrap_summary, candidate, sample_type="artist_bootstrap")
    if artist_row is None or test_row is None or artist_boot is None:
        return "판단 보류: 필요한 검증 결과가 부족함"

    artist_probs = [float(artist_row[f"improvement_probability_{metric}"]) for metric in primary_metrics]
    test_deltas = [float(test_row[f"delta_{metric}"]) for metric in primary_metrics]
    boot_probs = [float(artist_boot[f"improvement_probability_{metric}"]) for metric in primary_metrics]
    worse_count = worse_segment_count(segment_diag, candidate, primary_metrics)

    if purpose == "큰 오차 방어 후보":
        if all(delta < 0 for delta in test_deltas) and min(artist_probs) >= 0.80 and min(boot_probs) >= 0.70:
            return "채택 가능성 높음: 큰 오차 방어 목적의 보조 정책 후보"
        if all(delta < 0 for delta in test_deltas):
            return "조건부 후보: test 방어력은 좋지만 반복/segment 안정성 추가 확인 필요"
        return "보류: 큰 오차 방어 목적에서도 지표 악화가 남음"

    if purpose == "MdAPE 연구 후보":
        if float(test_row["delta_p95_APE"]) > 0:
            return "운영 보류: MdAPE는 좋지만 p95_APE 악화로 연구/원인 분석용"
        return "조건부 후보: MdAPE 목적 연구 후보"

    if all(delta < 0 for delta in test_deltas) and min(artist_probs) >= 0.70 and min(boot_probs) >= 0.70:
        if worse_count <= 2:
            return "채택 가능성 있음: 목적 지표와 작가 단위 검증이 함께 개선"
        return "조건부 후보: 전체 지표는 개선되지만 악화 segment 점검 필요"
    if all(delta < 0 for delta in test_deltas) and min(artist_probs) >= 0.70:
        return "조건부 후보: test와 작가 holdout은 개선됐지만 test artist bootstrap 확률 또는 악화 segment가 충분히 안정적이지 않음"
    if any(delta < 0 for delta in test_deltas) and min(artist_probs) >= 0.70:
        return "보수적 보류: 일부 목적 지표는 개선됐지만 전체 목적 지표를 안정적으로 개선했다고 보기 어려움"
    return "보류: 목적별 기준에서 안정적 개선이라고 보기 어려움"


def build_purpose_summary(
    artist_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    segment_diag: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for purpose_spec in PURPOSE_SPECS:
        candidate = purpose_spec["candidate"]
        artist_row = lookup_metric(artist_summary, candidate)
        test_row = lookup_metric(test_metrics, candidate)
        row_boot = lookup_metric(bootstrap_summary, candidate, sample_type="row_bootstrap")
        artist_boot = lookup_metric(bootstrap_summary, candidate, sample_type="artist_bootstrap")
        if artist_row is None or test_row is None or row_boot is None or artist_boot is None:
            continue
        primary_metrics = purpose_spec["primary_metrics"]
        row = {
            "purpose": purpose_spec["purpose"],
            "candidate": candidate,
            "description": purpose_spec["description"],
            "decision_focus": purpose_spec["decision_focus"],
            "test_MdAPE": float(test_row["MdAPE"]),
            "test_MAPE": float(test_row["MAPE"]),
            "test_p95_APE": float(test_row["p95_APE"]),
            "test_delta_MdAPE": float(test_row["delta_MdAPE"]),
            "test_delta_MAPE": float(test_row["delta_MAPE"]),
            "test_delta_p95_APE": float(test_row["delta_p95_APE"]),
            "artist_holdout_delta_MdAPE": float(artist_row["mean_delta_MdAPE"]),
            "artist_holdout_delta_MAPE": float(artist_row["mean_delta_MAPE"]),
            "artist_holdout_delta_p95_APE": float(artist_row["mean_delta_p95_APE"]),
            "artist_holdout_prob_MdAPE": float(artist_row["improvement_probability_MdAPE"]),
            "artist_holdout_prob_MAPE": float(artist_row["improvement_probability_MAPE"]),
            "artist_holdout_prob_p95_APE": float(artist_row["improvement_probability_p95_APE"]),
            "test_row_boot_prob_MdAPE": float(row_boot["improvement_probability_MdAPE"]),
            "test_row_boot_prob_MAPE": float(row_boot["improvement_probability_MAPE"]),
            "test_row_boot_prob_p95_APE": float(row_boot["improvement_probability_p95_APE"]),
            "test_artist_boot_prob_MdAPE": float(artist_boot["improvement_probability_MdAPE"]),
            "test_artist_boot_prob_MAPE": float(artist_boot["improvement_probability_MAPE"]),
            "test_artist_boot_prob_p95_APE": float(artist_boot["improvement_probability_p95_APE"]),
            "worse_segment_count_for_purpose": worse_segment_count(segment_diag, candidate, primary_metrics),
            "decision": decision_text(
                purpose_spec["purpose"],
                candidate,
                primary_metrics,
                artist_summary,
                test_metrics,
                bootstrap_summary,
                segment_diag,
            ),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_결과 없음_"

    def format_value(value: Any) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.5g}"
        return str(value).replace("|", "\\|").replace("\n", " ")

    columns = [str(col) for col in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(format_value(value) for value in row) + " |")
    return "\n".join(lines)


def render_report(
    purpose_summary: pd.DataFrame,
    artist_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    segment_diag: pd.DataFrame,
) -> tuple[str, str]:
    purpose_view = purpose_summary.copy()
    artist_view = artist_summary.copy()
    test_view = test_metrics.copy()
    boot_view = bootstrap_summary.copy()
    segment_view = segment_diag.sort_values(["candidate", "segment_col", "delta_p95_APE"]).copy()

    best_lines = []
    for row in purpose_view.itertuples(index=False):
        best_lines.append(
            f"- {row.purpose}: `{row.candidate}`. test MdAPE/MAPE/p95 "
            f"`{row.test_MdAPE:.4f}` / `{row.test_MAPE:.4f}` / `{row.test_p95_APE:.4f}`. "
            f"판단: {row.decision}"
        )

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        f"- 추가 검증: validation 작가 단위 holdout `{N_ARTIST_REPEATS}`회 x `{N_ARTIST_SPLITS}`fold, test row/artist bootstrap `{BOOTSTRAP_ITERATIONS}`회",
        "- 검증 목적: PP-WHUBER7/8의 보정 후보를 하나로 고르지 않고 목적별로 채택 가능성을 분리 판단",
        "",
        "## 1. 실행 결론",
        "",
        *best_lines,
        "",
        "## 2. 목적별 요약",
        "",
        markdown_table(purpose_view),
        "",
        "## 3. 작가 단위 반복 holdout 요약",
        "",
        markdown_table(artist_view),
        "",
        "## 4. Test 1회 성능",
        "",
        markdown_table(test_view),
        "",
        "## 5. Test bootstrap 요약",
        "",
        markdown_table(boot_view),
        "",
        "## 6. Segment 진단",
        "",
        markdown_table(segment_view),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/purpose_summary.csv`",
        "- `outputs/artist_holdout_summary.csv`",
        "- `outputs/artist_holdout_repeat_metrics.csv`",
        "- `outputs/artist_holdout_fold_metrics.csv`",
        "- `outputs/artist_holdout_predictions.csv`",
        "- `outputs/test_once_metrics.csv`",
        "- `outputs/test_once_predictions.csv`",
        "- `outputs/test_bootstrap_summary.csv`",
        "- `outputs/test_bootstrap_samples.csv`",
        "- `outputs/segment_diagnostics.csv`",
    ]
    md = "\n".join(lines) + "\n"

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">목적별 후보를 작가 단위 holdout, test bootstrap, segment 진단으로 추가 검증한 리포트.</div>
<h2>실행 결론</h2>
<ul>{''.join(f'<li>{html.escape(line[2:])}</li>' for line in best_lines)}</ul>
<h2>목적별 요약</h2>{purpose_view.to_html(index=False, escape=True)}
<h2>작가 단위 반복 holdout 요약</h2>{artist_view.to_html(index=False, escape=True)}
<h2>Test 1회 성능</h2>{test_view.to_html(index=False, escape=True)}
<h2>Test bootstrap 요약</h2>{boot_view.to_html(index=False, escape=True)}
<h2>Segment 진단</h2>{segment_view.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    purpose_summary: pd.DataFrame,
    artist_summary: pd.DataFrame,
    artist_repeats: pd.DataFrame,
    artist_folds: pd.DataFrame,
    artist_predictions: pd.DataFrame,
    test_metrics: pd.DataFrame,
    test_predictions: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    bootstrap_samples: pd.DataFrame,
    segment_diag: pd.DataFrame,
) -> None:
    purpose_summary.to_csv(EXP_DIR / "outputs" / "purpose_summary.csv", index=False)
    artist_summary.to_csv(EXP_DIR / "outputs" / "artist_holdout_summary.csv", index=False)
    artist_repeats.to_csv(EXP_DIR / "outputs" / "artist_holdout_repeat_metrics.csv", index=False)
    artist_folds.to_csv(EXP_DIR / "outputs" / "artist_holdout_fold_metrics.csv", index=False)
    artist_predictions.to_csv(EXP_DIR / "outputs" / "artist_holdout_predictions.csv", index=False)
    test_metrics.to_csv(EXP_DIR / "outputs" / "test_once_metrics.csv", index=False)
    test_predictions.to_csv(EXP_DIR / "outputs" / "test_once_predictions.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "test_bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "test_bootstrap_samples.csv", index=False)
    segment_diag.to_csv(EXP_DIR / "outputs" / "segment_diagnostics.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "current_candidate": CURRENT_CANDIDATE,
        "n_artist_splits": N_ARTIST_SPLITS,
        "n_artist_repeats": N_ARTIST_REPEATS,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "purpose_specs": PURPOSE_SPECS,
        "candidate_specs": CANDIDATE_SPECS,
        "leakage_control": {
            "artist_holdout": "validation artists are split by artist_key; holdout rows are predicted by residual models fitted on other validation artists",
            "test_once": "residual model is fitted on full validation and applied once to test",
            "test_bootstrap": "bootstrap evaluates already fixed test predictions only",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(purpose_summary, artist_summary, test_metrics, bootstrap_summary, segment_diag)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    val, test = whuber8.load_frames()
    artist_repeats, artist_folds, artist_predictions = repeated_artist_holdout(val)
    artist_summary = summarize_repeated_metrics(artist_repeats)
    test_metrics, test_predictions = test_once_predictions(val, test)
    bootstrap_summary, bootstrap_samples = bootstrap_test_predictions(test_predictions)
    segment_diag = segment_diagnostics(test_predictions)
    purpose_summary = build_purpose_summary(artist_summary, test_metrics, bootstrap_summary, segment_diag)
    write_outputs(
        purpose_summary,
        artist_summary,
        artist_repeats,
        artist_folds,
        artist_predictions,
        test_metrics,
        test_predictions,
        bootstrap_summary,
        bootstrap_samples,
        segment_diag,
    )
    print(f"[{EXP_ID}] completed")
    for row in purpose_summary.itertuples(index=False):
        print(
            f"{row.purpose}: {row.candidate} | "
            f"test {row.test_MdAPE:.4f}/{row.test_MAPE:.4f}/{row.test_p95_APE:.4f} | "
            f"{row.decision}"
        )
    print(f"report: {EXP_DIR / 'reports' / 'result_report.html'}")


if __name__ == "__main__":
    main()
