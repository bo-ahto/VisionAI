#!/usr/bin/env python3
"""Run PP-HCOEF34: price-basis generation and Huber coefficient screening.

HCOEF33 showed that repeating ultra-micro corrections around the same stable
candidate is not enough to promote a new operating candidate. HCOEF34 moves one
step earlier in the prediction chain: it rebuilds several train-only Warm price
bases, then checks whether Huber can learn interpretable low-dimensional
coefficients for those bases and their reliability signals.

Selection principle:

* Comparable price bases are created from train data only.
* Candidate choice is based on validation OOF/repeated evidence.
* Fixed test and 0604 are confirmation checks only.
* Fixed test or 0604 residuals are never used to create weights or rules.
"""
from __future__ import annotations

import html
import json
import os
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef1_warm_huber_price_basis_coefficient_refinement as h1
from scripts.track6 import run_pp_hcoef3_warm_huber_residual_repeated_validation as h3


EXP_ID = "PP-HCOEF34"
EXP_SLUG = "PP-HCOEF34_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

TRAIN = REPO / "data" / "track6_split" / "track6_train.csv"

REFERENCE = "current_70_30"
STABLE_ALIAS = "hcoef_stable"
STABLE_CONFIG = next(
    item for item in h3.CANDIDATES if item["candidate"] == "hcoef2_size_reliability_cap005_s050"
)

SEED = 20260608
N_FOLDS = 5
N_REPEATS = 12
N_SIZE_BINS = 5
FALLBACK_MIN_NS = [5, 10]
SHRINK_KS = [5.0, 20.0, 50.0]

LEVEL_DEFS: dict[str, list[str]] = {
    "artist_overall": ["artist_key"],
    "artist_size": ["artist_key", "size_bin"],
    "artist_medium_support": ["artist_key", "medium_support_bucket"],
    "artist_size_medium_support": ["artist_key", "size_bin", "medium_support_bucket"],
}
FALLBACK_ORDER = [
    "artist_size_medium_support",
    "artist_medium_support",
    "artist_size",
    "artist_overall",
]

DIRECT_BASIS_COLS = [
    "basis_artist_overall_m1",
    "basis_artist_size_m5",
    "basis_artist_medium_support_m5",
    "basis_artist_size_medium_support_m5",
    "basis_fallback_m5",
    "basis_fallback_m10",
    "basis_shrink_k5",
    "basis_shrink_k20",
    "basis_shrink_k50",
]

META_FEATURE_SETS: dict[str, list[str]] = {
    "basis_trust_core": [
        STABLE_ALIAS,
        REFERENCE,
        "basis_fallback_m5",
        "basis_shrink_k20",
        "basis_fallback_m5_n_log",
        "basis_fallback_m5_iqr",
        "log_area",
    ],
    "basis_generation_all": [
        STABLE_ALIAS,
        REFERENCE,
        "basis_artist_overall_m1",
        "basis_artist_size_m5",
        "basis_artist_medium_support_m5",
        "basis_artist_size_medium_support_m5",
        "basis_fallback_m5",
        "basis_shrink_k5",
        "basis_shrink_k20",
        "basis_fallback_m5_n_log",
        "basis_fallback_m5_iqr",
        "basis_component_spread",
        "log_area",
    ],
    "basis_gap_reliability": [
        "fallback_stable_gap",
        "shrink20_stable_gap",
        "current_stable_gap",
        "fallback_shrink20_gap",
        "basis_fallback_m5_n_log",
        "basis_fallback_m5_iqr",
        "basis_component_spread",
        "log_area",
    ],
}

RESIDUAL_FEATURE_SETS: dict[str, list[str]] = {
    "basis_resid_core": [
        "fallback_stable_gap",
        "shrink20_stable_gap",
        "current_stable_gap",
        "basis_fallback_m5_n_log",
        "basis_fallback_m5_iqr",
        "log_area",
    ],
    "basis_resid_all": [
        "fallback_stable_gap",
        "shrink20_stable_gap",
        "basis_artist_overall_m1_gap",
        "basis_artist_size_m5_gap",
        "basis_artist_medium_support_m5_gap",
        "basis_artist_size_medium_support_m5_gap",
        "basis_component_spread",
        "basis_fallback_m5_n_log",
        "basis_fallback_m5_iqr",
        "log_area",
    ],
}


@dataclass(frozen=True)
class CandidateConfig:
    candidate: str
    kind: str
    feature_key: str | None = None
    alpha: float | None = None
    cap: float | None = None
    strength: float | None = None
    basis_col: str | None = None
    max_weight: float | None = None
    k: float | None = None
    clip_margin: float | None = None
    description: str = ""


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def norm(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    resid = actual_log - pred_log
    return {
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(resid**2))),
        "Within_30": float(np.nanmean(ape <= 0.30)),
        "Within_50": float(np.nanmean(ape <= 0.50)),
        "over_2x_n": int(np.nansum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.nansum(pred_price <= actual_price * 0.5)),
    }


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def size_edges_from_train(train: pd.DataFrame) -> np.ndarray:
    area = pd.to_numeric(train["area_cm2"], errors="coerce").to_numpy(dtype=float)
    finite = area[np.isfinite(area) & (area > 0)]
    return np.quantile(finite, [i / N_SIZE_BINS for i in range(1, N_SIZE_BINS)])


def add_size_bin(frame: pd.DataFrame, edges: np.ndarray) -> pd.DataFrame:
    out = frame.copy()
    out["artist_key"] = norm(out["artist_key"])
    out["medium_category"] = norm(out["medium_category"])
    out["support_category"] = norm(out["support_category"])
    if "medium_support_bucket" not in out.columns:
        out["medium_support_bucket"] = out["medium_category"] + "__" + out["support_category"]
    out["medium_support_bucket"] = norm(out["medium_support_bucket"])
    area = pd.to_numeric(out["area_cm2"], errors="coerce").to_numpy(dtype=float)
    out["size_bin"] = pd.Series(np.digitize(np.nan_to_num(area, nan=-1.0), edges, right=False)).astype(str).to_numpy()
    return out


def key_for(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    return frame[cols].astype(str).agg("||".join, axis=1)


def build_basis_stats() -> tuple[dict[str, dict[str, tuple[float, int, float]]], float, float, np.ndarray]:
    train = pd.read_csv(TRAIN, low_memory=False)
    edges = size_edges_from_train(train)
    work = add_size_bin(train, edges)
    y = pd.to_numeric(work["ln_price_krw"], errors="coerce")
    work = work[y.notna()].copy()
    work["_y"] = y[y.notna()].to_numpy(dtype=float)
    global_median = float(np.nanmedian(work["_y"]))
    global_iqr = float(np.nanquantile(work["_y"], 0.75) - np.nanquantile(work["_y"], 0.25))
    stats: dict[str, dict[str, tuple[float, int, float]]] = {}
    for level, cols in LEVEL_DEFS.items():
        grouped = (
            work.assign(_key=key_for(work, cols))
            .groupby("_key")["_y"]
            .agg(["median", "count", lambda s: s.quantile(0.75) - s.quantile(0.25)])
        )
        grouped = grouped.rename(columns={"<lambda_0>": "iqr"})
        stats[level] = {
            str(idx): (float(row["median"]), int(row["count"]), float(row["iqr"]))
            for idx, row in grouped.iterrows()
        }
    return stats, global_median, global_iqr, edges


def direct_level_prior(
    keys: pd.DataFrame,
    stats: dict[str, dict[str, tuple[float, int, float]]],
    global_median: float,
    global_iqr: float,
    level: str,
    min_n: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    level_stats = stats[level]
    values: list[float] = []
    counts: list[int] = []
    iqrs: list[float] = []
    lookup = key_for(keys, LEVEL_DEFS[level]).to_numpy()
    for key in lookup:
        item = level_stats.get(str(key))
        if item is not None and item[1] >= min_n:
            values.append(item[0])
            counts.append(item[1])
            iqrs.append(item[2])
        else:
            values.append(global_median)
            counts.append(0)
            iqrs.append(global_iqr)
    return np.asarray(values, dtype=float), np.asarray(counts, dtype=float), np.asarray(iqrs, dtype=float)


def fallback_prior(
    keys: pd.DataFrame,
    stats: dict[str, dict[str, tuple[float, int, float]]],
    global_median: float,
    global_iqr: float,
    min_n: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    key_lookup = {level: key_for(keys, LEVEL_DEFS[level]).to_numpy() for level in LEVEL_DEFS}
    values: list[float] = []
    counts: list[int] = []
    iqrs: list[float] = []
    levels: list[str] = []
    for idx in range(len(keys)):
        chosen = (global_median, 0, global_iqr, "global")
        for level in FALLBACK_ORDER:
            item = stats[level].get(str(key_lookup[level][idx]))
            if item is not None and item[1] >= min_n:
                chosen = (item[0], item[1], item[2], level)
                break
        values.append(float(chosen[0]))
        counts.append(int(chosen[1]))
        iqrs.append(float(chosen[2]))
        levels.append(str(chosen[3]))
    return np.asarray(values, dtype=float), np.asarray(counts, dtype=float), np.asarray(iqrs, dtype=float), levels


def shrunk_prior(
    keys: pd.DataFrame,
    stats: dict[str, dict[str, tuple[float, int, float]]],
    global_median: float,
    k: float,
) -> np.ndarray:
    key_lookup = {level: key_for(keys, LEVEL_DEFS[level]).to_numpy() for level in LEVEL_DEFS}
    out = np.full(len(keys), global_median, dtype=float)
    for idx in range(len(keys)):
        est = global_median
        # artist_overall is the parent. artist_size and artist_medium_support
        # are sibling refinements, and the most specific key is applied last.
        for level in ["artist_overall", "artist_size", "artist_medium_support", "artist_size_medium_support"]:
            item = stats[level].get(str(key_lookup[level][idx]))
            if item is None:
                continue
            median, count, _ = item
            weight = count / (count + k)
            est = weight * median + (1.0 - weight) * est
        out[idx] = est
    return out


def add_basis_columns(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    stats, global_median, global_iqr, edges = build_basis_stats()
    out: dict[str, pd.DataFrame] = {}
    for split, frame in frames.items():
        work = add_size_bin(frame, edges)
        level_map = {
            "basis_artist_overall_m1": ("artist_overall", 1),
            "basis_artist_size_m5": ("artist_size", 5),
            "basis_artist_medium_support_m5": ("artist_medium_support", 5),
            "basis_artist_size_medium_support_m5": ("artist_size_medium_support", 5),
        }
        for col, (level, min_n) in level_map.items():
            pred, n, iqr = direct_level_prior(work, stats, global_median, global_iqr, level, min_n)
            work[col] = pred
            work[f"{col}_n"] = n
            work[f"{col}_iqr"] = iqr
        for min_n in FALLBACK_MIN_NS:
            pred, n, iqr, level = fallback_prior(work, stats, global_median, global_iqr, min_n)
            work[f"basis_fallback_m{min_n}"] = pred
            work[f"basis_fallback_m{min_n}_n"] = n
            work[f"basis_fallback_m{min_n}_n_log"] = np.log1p(np.clip(n, 0, None))
            work[f"basis_fallback_m{min_n}_iqr"] = iqr
            work[f"basis_fallback_m{min_n}_level"] = level
        for k in SHRINK_KS:
            work[f"basis_shrink_k{int(k)}"] = shrunk_prior(work, stats, global_median, k)
        component_cols = DIRECT_BASIS_COLS + [REFERENCE, STABLE_ALIAS]
        for col in component_cols:
            work[col] = pd.to_numeric(work[col], errors="coerce")
        work["basis_component_spread"] = work[DIRECT_BASIS_COLS].max(axis=1) - work[DIRECT_BASIS_COLS].min(axis=1)
        work["fallback_stable_gap"] = work["basis_fallback_m5"] - work[STABLE_ALIAS]
        work["shrink20_stable_gap"] = work["basis_shrink_k20"] - work[STABLE_ALIAS]
        work["current_stable_gap"] = work[REFERENCE] - work[STABLE_ALIAS]
        work["fallback_shrink20_gap"] = work["basis_fallback_m5"] - work["basis_shrink_k20"]
        for col in [
            "basis_artist_overall_m1",
            "basis_artist_size_m5",
            "basis_artist_medium_support_m5",
            "basis_artist_size_medium_support_m5",
        ]:
            work[f"{col}_gap"] = work[col] - work[STABLE_ALIAS]
        work["basis_fallback_m5_reliability"] = np.clip(
            work["basis_fallback_m5_n"] / (work["basis_fallback_m5_n"] + 20.0),
            0.0,
            1.0,
        )
        out[split] = work
    return out


def add_stable_predictions(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    validation = frames["validation"].copy()
    out: dict[str, pd.DataFrame] = {}
    for split, frame in frames.items():
        pred, _ = h3.correction_prediction(validation, frame.copy(), STABLE_CONFIG)
        work = frame.copy()
        work[STABLE_ALIAS] = pred
        out[split] = work
    return out


def build_frames() -> dict[str, pd.DataFrame]:
    frames = h3.build_frames()
    frames = add_stable_predictions(frames)
    return add_basis_columns(frames)


def linear_pipeline(alpha: float) -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("huber", HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=5000)),
        ]
    )


def clip_component_range(frame: pd.DataFrame, pred: np.ndarray, margin: float) -> np.ndarray:
    cols = [STABLE_ALIAS, REFERENCE, "basis_fallback_m5", "basis_shrink_k20", "ppv8_defensive"]
    lo = frame[cols].min(axis=1).to_numpy(dtype=float) - margin
    hi = frame[cols].max(axis=1).to_numpy(dtype=float) + margin
    return np.clip(np.asarray(pred, dtype=float), lo, hi)


def variable_weight_prediction(frame: pd.DataFrame, config: CandidateConfig) -> np.ndarray:
    if config.basis_col is None or config.max_weight is None or config.k is None:
        raise ValueError(config)
    n = pd.to_numeric(frame["basis_fallback_m5_n"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    weight = np.clip(n / (n + float(config.k)), 0.0, 1.0) * float(config.max_weight)
    base = frame[STABLE_ALIAS].to_numpy(dtype=float)
    basis = frame[config.basis_col].to_numpy(dtype=float)
    return (1.0 - weight) * base + weight * basis


def fit_meta_model(train: pd.DataFrame, config: CandidateConfig) -> Pipeline:
    if config.feature_key is None or config.alpha is None:
        raise ValueError(config)
    features = META_FEATURE_SETS[config.feature_key]
    target = train["actual_log"].to_numpy(dtype=float)
    model = linear_pipeline(float(config.alpha))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(train[features], target)
    return model


def fit_residual_model(train: pd.DataFrame, config: CandidateConfig) -> Pipeline:
    if config.feature_key is None or config.alpha is None:
        raise ValueError(config)
    features = RESIDUAL_FEATURE_SETS[config.feature_key]
    target = train["actual_log"].to_numpy(dtype=float) - train[STABLE_ALIAS].to_numpy(dtype=float)
    model = linear_pipeline(float(config.alpha))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(train[features], target)
    return model


def predict_candidate(train: pd.DataFrame, eval_frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, Pipeline | None]:
    if config.kind == "direct":
        if config.basis_col is None:
            raise ValueError(config)
        return eval_frame[config.basis_col].to_numpy(dtype=float), None
    if config.kind == "variable_weight":
        return variable_weight_prediction(eval_frame, config), None
    if config.kind == "meta_huber":
        model = fit_meta_model(train, config)
        pred = np.asarray(model.predict(eval_frame[META_FEATURE_SETS[config.feature_key or ""]]), dtype=float)
        if config.clip_margin is not None:
            pred = clip_component_range(eval_frame, pred, float(config.clip_margin))
        return pred, model
    if config.kind == "residual_huber":
        model = fit_residual_model(train, config)
        raw = np.asarray(model.predict(eval_frame[RESIDUAL_FEATURE_SETS[config.feature_key or ""]]), dtype=float)
        correction = np.clip(raw, -float(config.cap), float(config.cap)) * float(config.strength)
        return eval_frame[STABLE_ALIAS].to_numpy(dtype=float) + correction, model
    raise ValueError(f"Unknown kind: {config.kind}")


def candidate_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = []
    for col in DIRECT_BASIS_COLS:
        configs.append(
            CandidateConfig(
                candidate=f"hcoef34_direct_{col}",
                kind="direct",
                basis_col=col,
                description=f"train-only {col} 기준가 단독",
            )
        )
    for basis_col in ["basis_fallback_m5", "basis_shrink_k20"]:
        for max_weight in [0.10, 0.20, 0.30]:
            for k in [5.0, 20.0]:
                configs.append(
                    CandidateConfig(
                        candidate=(
                            f"hcoef34_vw_{basis_col}_max{slug(max_weight)}"
                            f"_k{int(k)}"
                        ),
                        kind="variable_weight",
                        basis_col=basis_col,
                        max_weight=max_weight,
                        k=k,
                        description="유사 표본 수가 많을수록 기준가 비중을 늘리는 가변 결합",
                    )
                )
    for feature_key in META_FEATURE_SETS:
        for alpha in [0.001, 0.01]:
            for clip_margin in [None, 0.20]:
                configs.append(
                    CandidateConfig(
                        candidate=(
                            f"hcoef34_meta_{feature_key}_a{slug(alpha)}"
                            + ("" if clip_margin is None else "_clip0p20")
                        ),
                        kind="meta_huber",
                        feature_key=feature_key,
                        alpha=alpha,
                        clip_margin=clip_margin,
                        description="기준가와 신뢰도 피처를 입력해 actual log price를 Huber로 재학습",
                    )
                )
    for feature_key in RESIDUAL_FEATURE_SETS:
        for alpha in [0.001, 0.01]:
            for cap in [0.005, 0.010, 0.020]:
                for strength in [0.25, 0.50]:
                    configs.append(
                        CandidateConfig(
                            candidate=(
                                f"hcoef34_resid_{feature_key}_a{slug(alpha)}"
                                f"_cap{slug(cap)}_s{slug(strength)}"
                            ),
                            kind="residual_huber",
                            feature_key=feature_key,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            description="stable 후보가 남긴 잔차를 기준가 gap/신뢰도 축으로 Huber 보정",
                        )
                    )
    return configs


def slug(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def row_folds(n: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.arange(n))
    folds = np.array_split(order, N_FOLDS)
    all_idx = np.arange(n)
    return [(np.setdiff1d(all_idx, hold, assume_unique=False), hold) for hold in folds]


def artist_folds(frame: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    artists = frame["artist_key"].astype(str).to_numpy()
    unique = rng.permutation(np.unique(artists))
    fold_of = {artist: idx % N_FOLDS for idx, artist in enumerate(unique)}
    all_idx = np.arange(len(frame))
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_id in range(N_FOLDS):
        hold = np.flatnonzero([fold_of[artist] == fold_id for artist in artists])
        train = np.setdiff1d(all_idx, hold, assume_unique=False)
        out.append((train, hold))
    return out


def metric_row(
    scope: str,
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    ref_metric: dict[str, float],
    stable_metric: dict[str, float],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "scope": scope,
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": n,
        **m,
        "delta_MdAPE_vs_reference": m["MdAPE"] - ref_metric["MdAPE"],
        "delta_MAPE_vs_reference": m["MAPE"] - ref_metric["MAPE"],
        "delta_p95_APE_vs_reference": m["p95_APE"] - ref_metric["p95_APE"],
        "delta_RMSE_log_vs_reference": m["RMSE_log"] - ref_metric["RMSE_log"],
        "delta_MdAPE_vs_stable": m["MdAPE"] - stable_metric["MdAPE"],
        "delta_MAPE_vs_stable": m["MAPE"] - stable_metric["MAPE"],
        "delta_p95_APE_vs_stable": m["p95_APE"] - stable_metric["p95_APE"],
        "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_metric["RMSE_log"],
        "improve_count_vs_reference": int(m["MdAPE"] < ref_metric["MdAPE"])
        + int(m["MAPE"] < ref_metric["MAPE"])
        + int(m["p95_APE"] < ref_metric["p95_APE"]),
        "improve_count_vs_stable": int(m["MdAPE"] < stable_metric["MdAPE"])
        + int(m["MAPE"] < stable_metric["MAPE"])
        + int(m["p95_APE"] < stable_metric["p95_APE"]),
    }
    if extra:
        row.update(extra)
    return row


def prediction_frame(frame: pd.DataFrame, candidate: str, method: str, split: str, pred_log: np.ndarray) -> pd.DataFrame:
    pred_log = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    actual = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "candidate": candidate,
            "method": method,
            "split": split,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].astype(str).to_numpy(),
            "artist_name_ko": frame["artist_name_ko"].astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual,
            "pred_log": pred_log,
            "pred_price": pred_price,
            "residual_log": frame["actual_log"].to_numpy(dtype=float) - pred_log,
            "ape": np.abs(pred_price - actual) / np.clip(actual, 1.0, None),
            "hcoef_stable": frame[STABLE_ALIAS].to_numpy(dtype=float),
            "current_70_30": frame[REFERENCE].to_numpy(dtype=float),
            "basis_fallback_m5": frame["basis_fallback_m5"].to_numpy(dtype=float),
            "basis_shrink_k20": frame["basis_shrink_k20"].to_numpy(dtype=float),
            "basis_fallback_m5_n": frame["basis_fallback_m5_n"].to_numpy(dtype=float),
            "basis_fallback_m5_level": frame["basis_fallback_m5_level"].astype(str).to_numpy(),
            "medium_support_bucket": frame["medium_support_bucket"].astype(str).to_numpy(),
            "log_area": frame["log_area"].to_numpy(dtype=float),
        }
    )
    return out


def fixed_confirmation(frames: dict[str, pd.DataFrame], configs: list[CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validation = frames["validation"]
    metric_rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    baselines = [
        (REFERENCE, "baseline_reference", REFERENCE),
        (STABLE_ALIAS, "baseline_stable", STABLE_ALIAS),
        ("basis_fallback_m5", "basis_component", "basis_fallback_m5"),
        ("basis_shrink_k20", "basis_component", "basis_shrink_k20"),
    ]
    for split, frame in frames.items():
        ref_metric = metric(frame, frame[REFERENCE].to_numpy(dtype=float))
        stable_metric = metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
        for candidate, method, col in baselines:
            pred = frame[col].to_numpy(dtype=float)
            m = metric(frame, pred)
            metric_rows.append(metric_row("fixed_confirmation", split, candidate, method, len(frame), m, ref_metric, stable_metric))
            pred_rows.append(prediction_frame(frame, candidate, method, split, pred))

    for config in configs:
        for split, frame in frames.items():
            pred, model = predict_candidate(validation, frame, config)
            ref_metric = metric(frame, frame[REFERENCE].to_numpy(dtype=float))
            stable_metric = metric(frame, frame[STABLE_ALIAS].to_numpy(dtype=float))
            m = metric(frame, pred)
            metric_rows.append(metric_row("fixed_confirmation", split, config.candidate, config.kind, len(frame), m, ref_metric, stable_metric))
            pred_rows.append(prediction_frame(frame, config.candidate, config.kind, split, pred))
            if split == "test" and model is not None:
                coef_rows.append(coefficient_frame(model, config))
    return pd.DataFrame(metric_rows), pd.concat(pred_rows, ignore_index=True), pd.concat(coef_rows, ignore_index=True)


def repeated_oof(validation: pd.DataFrame, configs: list[CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    pred_rows: list[pd.DataFrame] = []
    ref_metric = metric(validation, validation[REFERENCE].to_numpy(dtype=float))
    stable_metric = metric(validation, validation[STABLE_ALIAS].to_numpy(dtype=float))
    for scheme in ["row_oof", "artist_oof"]:
        for repeat in range(N_REPEATS):
            folds = row_folds(len(validation), SEED + repeat) if scheme == "row_oof" else artist_folds(validation, SEED + repeat)
            for config in configs:
                oof = np.full(len(validation), np.nan, dtype=float)
                for train_idx, hold_idx in folds:
                    train = validation.iloc[train_idx].copy()
                    hold = validation.iloc[hold_idx].copy()
                    pred, _ = predict_candidate(train, hold, config)
                    oof[hold_idx] = pred
                m = metric(validation, oof)
                rows.append(
                    metric_row(
                        "repeated_oof",
                        f"validation_{scheme}",
                        config.candidate,
                        config.kind,
                        len(validation),
                        m,
                        ref_metric,
                        stable_metric,
                        {"repeat": repeat, "validation_scheme": scheme},
                    )
                )
                if repeat == 0:
                    pred_rows.append(prediction_frame(validation, config.candidate, config.kind, f"validation_{scheme}_repeat0", oof))
    for candidate, method, col in [
        (REFERENCE, "baseline_reference", REFERENCE),
        (STABLE_ALIAS, "baseline_stable", STABLE_ALIAS),
    ]:
        pred = validation[col].to_numpy(dtype=float)
        m = metric(validation, pred)
        rows.append(
            metric_row(
                "repeated_oof",
                "validation_reference",
                candidate,
                method,
                len(validation),
                m,
                ref_metric,
                stable_metric,
                {"repeat": -1, "validation_scheme": "reference"},
            )
        )
    return pd.DataFrame(rows), pd.concat(pred_rows, ignore_index=True)


def summarize_repeated(metrics_df: pd.DataFrame) -> pd.DataFrame:
    repeated = metrics_df[metrics_df["scope"].eq("repeated_oof") & metrics_df["validation_scheme"].isin(["row_oof", "artist_oof"])].copy()
    rows: list[dict[str, Any]] = []
    for (scheme, candidate), group in repeated.groupby(["validation_scheme", "candidate"], sort=False):
        rows.append(
            {
                "validation_scheme": scheme,
                "candidate": candidate,
                "n_repeats": int(group["repeat"].nunique()),
                "mean_MdAPE": float(group["MdAPE"].mean()),
                "mean_MAPE": float(group["MAPE"].mean()),
                "mean_p95_APE": float(group["p95_APE"].mean()),
                "mean_RMSE_log": float(group["RMSE_log"].mean()),
                "mean_delta_MdAPE_vs_reference": float(group["delta_MdAPE_vs_reference"].mean()),
                "mean_delta_MAPE_vs_reference": float(group["delta_MAPE_vs_reference"].mean()),
                "mean_delta_p95_APE_vs_reference": float(group["delta_p95_APE_vs_reference"].mean()),
                "mean_delta_MdAPE_vs_stable": float(group["delta_MdAPE_vs_stable"].mean()),
                "mean_delta_MAPE_vs_stable": float(group["delta_MAPE_vs_stable"].mean()),
                "mean_delta_p95_APE_vs_stable": float(group["delta_p95_APE_vs_stable"].mean()),
                "ref_any2_improve_prob": float((group["improve_count_vs_reference"] >= 2).mean()),
                "stable_any2_improve_prob": float((group["improve_count_vs_stable"] >= 2).mean()),
                "stable_all3_improve_prob": float((group["improve_count_vs_stable"] == 3).mean()),
                "stable_p95_improve_prob": float((group["delta_p95_APE_vs_stable"] < 0).mean()),
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    gates = summary.pivot_table(
        index="candidate",
        columns="validation_scheme",
        values=["stable_any2_improve_prob", "stable_all3_improve_prob", "ref_any2_improve_prob"],
        aggfunc="first",
    )
    gates.columns = [f"{scheme}_{metric}" for metric, scheme in gates.columns]
    return summary.merge(gates.reset_index(), on="candidate", how="left")


def coefficient_frame(model: Pipeline, config: CandidateConfig) -> pd.DataFrame:
    if config.kind == "meta_huber":
        features = META_FEATURE_SETS[config.feature_key or ""]
        target = "actual_log"
    elif config.kind == "residual_huber":
        features = RESIDUAL_FEATURE_SETS[config.feature_key or ""]
        target = "stable_residual_log"
    else:
        return pd.DataFrame()
    huber = model.named_steps["huber"]
    rows: list[dict[str, Any]] = []
    for feature, coefficient in zip(features, huber.coef_, strict=True):
        rows.append(
            {
                "candidate": config.candidate,
                "kind": config.kind,
                "feature_set": config.feature_key,
                "target": target,
                "feature": feature,
                "coefficient_on_scaled_feature": float(coefficient),
                "abs_coefficient": float(abs(coefficient)),
                "direction": "예측 로그가격/보정값을 올리는 방향" if coefficient > 0 else "예측 로그가격/보정값을 낮추는 방향",
                "alpha": config.alpha,
                "cap": config.cap,
                "strength": config.strength,
                "clip_margin": config.clip_margin,
            }
        )
    return pd.DataFrame(rows).sort_values("abs_coefficient", ascending=False)


def residual_analysis(predictions: pd.DataFrame, focus_candidates: set[str]) -> pd.DataFrame:
    focus = predictions[predictions["candidate"].isin(focus_candidates) & predictions["split"].isin(["test", "0604_ex50"])].copy()
    rows: list[dict[str, Any]] = []
    for (split, candidate), group in focus.groupby(["split", "candidate"], sort=False):
        rows.append(
            {
                "split": split,
                "candidate": candidate,
                "n": int(len(group)),
                "median_residual_log": float(group["residual_log"].median()),
                "mean_residual_log": float(group["residual_log"].mean()),
                "residual_std": float(group["residual_log"].std()),
                "ape_median": float(group["ape"].median()),
                "ape_mean": float(group["ape"].mean()),
                "ape_p95": float(group["ape"].quantile(0.95)),
                "ape_gt_100pct_n": int((group["ape"] > 1.0).sum()),
                "over_2x_n": int((group["pred_price"] >= group["actual_price"] * 2.0).sum()),
                "under_half_n": int((group["pred_price"] <= group["actual_price"] * 0.5).sum()),
            }
        )
    return pd.DataFrame(rows)


def basis_coverage(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split, frame in frames.items():
        vc = frame["basis_fallback_m5_level"].astype(str).value_counts(normalize=True)
        rows.append(
            {
                "split": split,
                "n": int(len(frame)),
                "fallback_global_pct": float(vc.get("global", 0.0) * 100),
                "fallback_artist_pct": float(vc.get("artist_overall", 0.0) * 100),
                "fallback_artist_size_pct": float(vc.get("artist_size", 0.0) * 100),
                "fallback_artist_medium_support_pct": float(vc.get("artist_medium_support", 0.0) * 100),
                "fallback_artist_size_medium_support_pct": float(vc.get("artist_size_medium_support", 0.0) * 100),
                "median_fallback_n": float(frame["basis_fallback_m5_n"].median()),
                "median_fallback_iqr": float(frame["basis_fallback_m5_iqr"].median()),
            }
        )
    return pd.DataFrame(rows)


def select_candidates(fixed_metrics: pd.DataFrame, repeated_summary: pd.DataFrame) -> pd.DataFrame:
    base = repeated_summary.drop_duplicates("candidate")[
        [
            "candidate",
            "row_oof_ref_any2_improve_prob",
            "artist_oof_ref_any2_improve_prob",
            "row_oof_stable_any2_improve_prob",
            "artist_oof_stable_any2_improve_prob",
            "row_oof_stable_all3_improve_prob",
            "artist_oof_stable_all3_improve_prob",
        ]
    ].copy()
    test = fixed_metrics[fixed_metrics["split"].eq("test")][
        [
            "candidate",
            "method",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_reference",
            "delta_MAPE_vs_reference",
            "delta_p95_APE_vs_reference",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "improve_count_vs_reference",
            "improve_count_vs_stable",
        ]
    ].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "RMSE_log": "test_RMSE_log",
        }
    )
    stress = fixed_metrics[fixed_metrics["split"].eq("0604_ex50")][
        ["candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "improve_count_vs_stable"]
    ].rename(
        columns={
            "MdAPE": "stress0604_MdAPE",
            "MAPE": "stress0604_MAPE",
            "p95_APE": "stress0604_p95_APE",
            "RMSE_log": "stress0604_RMSE_log",
            "improve_count_vs_stable": "stress0604_improve_count_vs_stable",
        }
    )
    out = base.merge(test, on="candidate", how="left").merge(stress, on="candidate", how="left")
    out["passes_reference_gate"] = (
        (out["row_oof_ref_any2_improve_prob"] >= 0.90)
        & (out["artist_oof_ref_any2_improve_prob"] >= 0.90)
        & (out["improve_count_vs_reference"] >= 2)
    )
    out["passes_stable_gate"] = (
        (out["row_oof_stable_any2_improve_prob"] >= 0.90)
        & (out["artist_oof_stable_any2_improve_prob"] >= 0.90)
        & (out["improve_count_vs_stable"] >= 2)
        & (out["test_p95_APE"] <= 0.806366 + 1e-9)
    )
    out["passes_strong_stable_gate"] = (
        (out["row_oof_stable_all3_improve_prob"] >= 0.90)
        & (out["artist_oof_stable_all3_improve_prob"] >= 0.90)
        & (out["improve_count_vs_stable"] == 3)
        & (out["test_p95_APE"] <= 0.806366 + 1e-9)
    )
    conditions = [
        out["passes_strong_stable_gate"],
        out["passes_stable_gate"],
        out["passes_reference_gate"],
    ]
    choices = ["운영 후보 검토", "Warm 안정 후보 재검증", "기존 70:30 대비 개선 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    return out.sort_values(
        ["passes_strong_stable_gate", "passes_stable_gate", "passes_reference_gate", "test_MdAPE", "test_MAPE"],
        ascending=[False, False, False, True, True],
    )


def markdown_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_결과 없음_"
    data = frame.head(max_rows).copy() if max_rows else frame.copy()

    def fmt(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        if pd.isna(value):
            return ""
        return str(value)

    cols = [str(col) for col in data.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in data.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    if max_rows is not None and len(frame) > max_rows:
        lines.append(f"\n_상위 {max_rows}개만 표시. 전체 {len(frame)}개._")
    return "\n".join(lines)


def md_to_html(md: str) -> str:
    body: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows: list[str] = []
        for idx, line in enumerate(table):
            if idx == 1:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
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
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.strip().startswith("- "):
            body.append(f"<p>{html.escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;color:#1f2937}"
        "table{border-collapse:collapse;margin:12px 0;width:100%}"
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6}p{line-height:1.55}h1,h2,h3{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    fixed_metrics: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    selected: pd.DataFrame,
    coeffs: pd.DataFrame,
    residuals: pd.DataFrame,
    coverage: pd.DataFrame,
) -> None:
    test = fixed_metrics[fixed_metrics["split"].eq("test")].copy()
    top_test = test.sort_values(["MdAPE", "MAPE", "p95_APE"]).head(15)
    focus = fixed_metrics[
        fixed_metrics["candidate"].isin([REFERENCE, STABLE_ALIAS, "basis_fallback_m5", "basis_shrink_k20"])
        & fixed_metrics["split"].isin(["validation", "test", "0604_ex50"])
    ].copy()
    selected_focus = selected.head(12).copy()
    adopted = selected[selected["decision"].isin(["운영 후보 검토", "Warm 안정 후보 재검증"])].copy()
    if adopted.empty:
        conclusion = (
            "새 기준가 생성 방식은 기존 70:30 대비 개선 후보는 만들 수 있지만, "
            "현재 hcoef_stable을 반복 검증과 fixed p95 기준에서 명확히 넘는 운영 후보는 아직 없음."
        )
    else:
        best = adopted.iloc[0]
        conclusion = (
            f"`{best['candidate']}`를 Warm 개선 재검증 후보로 분리. "
            f"test MdAPE/MAPE/p95 {best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}."
        )

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 기준가 생성/계수 조정 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: 유사 작품 기반 가격 피처를 여러 방식으로 다시 만들고, Huber가 기준가와 신뢰도 피처의 계수를 안정적으로 학습하는지 확인.",
            "- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.",
            "- 안정 비교 후보: `hcoef_stable` = 기존 70:30 위에 작은 Huber 잔차 보정을 더한 현재 안정 후보.",
            "- 선택 원칙: validation 반복 OOF로 후보를 먼저 고르고 fixed test/0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {conclusion}",
            "- HCOEF34는 기준가 자체를 바꾸는 broad screening 실험이므로, 좋은 후보가 있더라도 HCOEF35에서 반복 수를 늘려 재검증해야 함.",
            "",
            "## 2. 생성한 기준가 방식",
            "",
            "- `basis_artist_overall_m1`: 작가 전체 과거 거래 중앙값. 같은 작가의 전반적 가격 기준선.",
            "- `basis_artist_size_m5`: 작가+크기 구간 중앙값. 크기별 가격 차이를 반영하되 표본 5개 미만은 global로 완화.",
            "- `basis_artist_medium_support_m5`: 작가+재료/지지체 중앙값. 재료와 지지체에 따른 가격 차이를 반영.",
            "- `basis_artist_size_medium_support_m5`: 작가+크기+재료/지지체 중앙값. 가장 세밀하지만 표본 부족 위험이 큼.",
            "- `basis_fallback_m5/m10`: 세밀한 기준부터 찾고 표본이 부족하면 상위 기준으로 이동하는 fallback 기준가.",
            "- `basis_shrink_k*`: 표본 수가 적을수록 작가 전체/전역 기준으로 부드럽게 당기는 shrink 기준가.",
            "",
            "## 3. 기준가 fallback 분포",
            "",
            markdown_table(coverage.round(4)),
            "",
            "## 4. 기준 후보와 기준가 컴포넌트 고정 지표",
            "",
            markdown_table(
                focus[
                    [
                        "split",
                        "candidate",
                        "method",
                        "n",
                        "MdAPE",
                        "MAPE",
                        "p95_APE",
                        "RMSE_log",
                        "delta_MdAPE_vs_reference",
                        "delta_MAPE_vs_reference",
                        "delta_p95_APE_vs_reference",
                        "delta_MdAPE_vs_stable",
                        "delta_MAPE_vs_stable",
                        "delta_p95_APE_vs_stable",
                    ]
                ].round(4),
                max_rows=40,
            ),
            "",
            "## 5. 후보 선택 판단",
            "",
            markdown_table(
                selected_focus[
                    [
                        "candidate",
                        "decision",
                        "method",
                        "test_MdAPE",
                        "test_MAPE",
                        "test_p95_APE",
                        "stress0604_MdAPE",
                        "stress0604_MAPE",
                        "stress0604_p95_APE",
                        "row_oof_ref_any2_improve_prob",
                        "artist_oof_ref_any2_improve_prob",
                        "row_oof_stable_any2_improve_prob",
                        "artist_oof_stable_any2_improve_prob",
                    ]
                ].round(4),
                max_rows=12,
            ),
            "",
            "## 6. Fixed test 상위 후보",
            "",
            markdown_table(top_test[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "improve_count_vs_reference", "improve_count_vs_stable"]].round(4)),
            "",
            "## 7. 반복 OOF 요약",
            "",
            markdown_table(
                repeated_summary.sort_values(
                    ["row_oof_ref_any2_improve_prob", "artist_oof_ref_any2_improve_prob", "mean_MdAPE"],
                    ascending=[False, False, True],
                )[
                    [
                        "candidate",
                        "validation_scheme",
                        "n_repeats",
                        "mean_MdAPE",
                        "mean_MAPE",
                        "mean_p95_APE",
                        "mean_delta_MdAPE_vs_reference",
                        "mean_delta_MAPE_vs_reference",
                        "mean_delta_p95_APE_vs_reference",
                        "ref_any2_improve_prob",
                        "stable_any2_improve_prob",
                        "stable_all3_improve_prob",
                    ]
                ].round(4),
                max_rows=30,
            ),
            "",
            "## 8. Huber 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준. 절대 원화 단위 계수가 아니라 방향성과 상대 영향 비교용.",
            "- 양수 계수: 해당 피처가 커질수록 예측 로그가격 또는 stable 잔차 보정값을 올리는 방향.",
            "- 음수 계수: 해당 피처가 커질수록 예측 로그가격 또는 stable 잔차 보정값을 낮추는 방향.",
            "- 기준가 피처 계수가 크고 신뢰도 피처가 함께 움직이면, Huber가 '어떤 기준가를 얼마나 믿을지'를 학습했다는 의미.",
            markdown_table(coeffs.head(60).round(5), max_rows=60),
            "",
            "## 9. 잔차/큰 오차 요약",
            "",
            markdown_table(residuals.round(4), max_rows=40),
            "",
            "## 10. 다음 보정 방향",
            "",
            "- HCOEF34에서 안정 후보가 나오면 HCOEF35에서 반복 횟수를 늘려 row/artist/bootstrap 재검증.",
            "- 안정 후보가 없으면 기준가 직접 반영보다 신뢰도별 routing 또는 가격 범위/신뢰도 정책으로 분리.",
            "- fixed test만 좋은 후보는 채택하지 않고, validation OOF 기준으로 동일 방향이 반복되는지 먼저 확인.",
            "",
            "## 11. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/basis_coverage.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef34_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef34_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    frames = build_frames()
    configs = candidate_configs()
    fixed_metrics, fixed_predictions, coeffs = fixed_confirmation(frames, configs)
    repeated_metrics, repeated_predictions = repeated_oof(frames["validation"], configs)
    metrics = pd.concat([fixed_metrics, repeated_metrics], ignore_index=True, sort=False)
    predictions = pd.concat([fixed_predictions, repeated_predictions], ignore_index=True, sort=False)
    repeated_summary = summarize_repeated(metrics)
    selected = select_candidates(fixed_metrics, repeated_summary)
    focus_candidates = set(selected.head(12)["candidate"].astype(str)) | {REFERENCE, STABLE_ALIAS, "basis_fallback_m5", "basis_shrink_k20"}
    residuals = residual_analysis(predictions, focus_candidates)
    coverage = basis_coverage(frames)

    out = EXP_DIR / "outputs"
    metrics.to_csv(out / "metrics.csv", index=False)
    predictions.to_csv(out / "candidate_predictions.csv", index=False)
    coeffs.to_csv(out / "feature_coefficients.csv", index=False)
    residuals.to_csv(out / "residual_analysis.csv", index=False)
    repeated_summary.to_csv(out / "bootstrap_or_repeated_split_summary.csv", index=False)
    selected.to_csv(out / "selected_candidates.csv", index=False)
    coverage.to_csv(out / "basis_coverage.csv", index=False)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reference_candidate": REFERENCE,
        "stable_candidate": STABLE_CONFIG,
        "n_folds": N_FOLDS,
        "n_repeats": N_REPEATS,
        "seed": SEED,
        "basis_levels": LEVEL_DEFS,
        "fallback_order": FALLBACK_ORDER,
        "fallback_min_ns": FALLBACK_MIN_NS,
        "shrink_ks": SHRINK_KS,
        "meta_feature_sets": META_FEATURE_SETS,
        "residual_feature_sets": RESIDUAL_FEATURE_SETS,
        "candidate_count": len(configs),
        "selection_policy": "validation repeated OOF first, fixed test/0604 confirmation only",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(fixed_metrics, repeated_summary, selected, coeffs, residuals, coverage)

    print(f"[{EXP_ID}] wrote {EXP_DIR}")
    print("--- selected candidates ---")
    print(
        selected.head(15)[
            [
                "candidate",
                "decision",
                "test_MdAPE",
                "test_MAPE",
                "test_p95_APE",
                "row_oof_ref_any2_improve_prob",
                "artist_oof_ref_any2_improve_prob",
                "row_oof_stable_any2_improve_prob",
                "artist_oof_stable_any2_improve_prob",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    print("--- fixed test top 10 ---")
    print(
        fixed_metrics[fixed_metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(10)[["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "improve_count_vs_reference", "improve_count_vs_stable"]]
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
