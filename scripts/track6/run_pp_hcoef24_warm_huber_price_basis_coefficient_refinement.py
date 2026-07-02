#!/usr/bin/env python3
"""Run PP-HCOEF24: risk-aware basis price generation for Warm Huber.

HCOEF4/5 already showed that a loose comparable-basis Huber model can improve
MdAPE/MAPE, but may increase p95. HCOEF23 then identified where the current
stable Warm candidate still has residual risk: wide quantile ranges, large
component disagreement, mid-low comparable counts, and extreme prediction
spread.

HCOEF24 uses those validation/OOF-derived risk signals to make the basis price
less aggressive before testing Huber coefficient candidates. Fixed test and
0604 are confirmation/stress checks only; no threshold is selected from their
residuals.
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
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef20_warm_huber_price_basis_coefficient_refinement as h20
from scripts.track6 import run_pp_hcoef4_warm_basis_generation_refinement as h4


EXP_ID = "PP-HCOEF24"
EXP_SLUG = "PP-HCOEF24_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"

BASELINE = h20.BASELINE
REFERENCE = h20.REFERENCE
PPV8 = h20.PPV8
SVC = h20.SVC
L10_COL = h20.L10_COL
SEED = 20260608
N_BOOTSTRAP = 300
STABLE_TEST_P95 = h20.STABLE_TEST_P95
STABLE_0604_P95 = h20.STABLE_0604_P95

POLICIES = ("loose", "default", "strict")
RISK_LEVELS = [
    "artist_medium_support_size",
    "artist_size",
    "artist",
    "medium_support_size",
    "medium_category_support_size",
    "medium_size",
    "global",
]


@dataclass(frozen=True)
class CandidateConfig:
    candidate: str
    method: str
    features: tuple[str, ...] = ()
    alpha: float | None = None
    cap: float | None = None
    strength: float | None = None
    source_col: str | None = None
    gap_col: str | None = None
    purpose: str = ""


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def fmt_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, max_rows: int | None = None, empty: str = "| 없음 |\n| --- |") -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return empty
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt_cell(v) for v in row) + " |")
    return "\n".join(lines)


def slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    return h20.safe_exp(values)


def metric(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return h20.metric_from_arrays(
        frame["actual_price"].to_numpy(dtype=float),
        frame["actual_log"].to_numpy(dtype=float),
        np.asarray(pred_log, dtype=float),
    )


def prefix_basis_columns(policy: str, basis: pd.DataFrame) -> pd.DataFrame:
    keep = ["_track6_row_id"] + [col for col in basis.columns if col.startswith("basis_")]
    out = basis[keep].copy()
    rename = {col: f"{policy}_{col}" for col in out.columns if col != "_track6_row_id"}
    return out.rename(columns=rename)


def load_basis_augmented_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load HCOEF20 base frame and merge HCOEF4 basis features for all policies."""
    base = h20.load_base_frame().copy()
    coverage_frames: list[pd.DataFrame] = []
    for policy in POLICIES:
        policy_features = h4.build_basis_features(policy)
        coverage_frames.append(coverage_summary_for_policy(policy, policy_features))
        for split in ["validation", "test", "0604_ex50"]:
            part = prefix_basis_columns(policy, policy_features[split])
            idx = base["split"].eq(split)
            merged = base.loc[idx, ["_track6_row_id"]].merge(part, on="_track6_row_id", how="left")
            for col in [c for c in merged.columns if c != "_track6_row_id"]:
                base.loc[idx, col] = merged[col].to_numpy()
    return add_risk_aware_basis_features(base), pd.concat(coverage_frames, ignore_index=True)


def coverage_summary_for_policy(policy: str, policy_features: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split in ["validation", "test", "0604_ex50"]:
        frame = policy_features[split]
        for level in RISK_LEVELS[:-1]:
            covered_col = f"basis_{level}_covered"
            n_col = f"basis_{level}_n"
            if covered_col not in frame.columns:
                continue
            covered = pd.to_numeric(frame[covered_col], errors="coerce").fillna(0.0).gt(0)
            n = pd.to_numeric(frame[n_col], errors="coerce").fillna(0.0)
            rows.append(
                {
                    "policy": policy,
                    "split": split,
                    "basis_level": level,
                    "rows": len(frame),
                    "covered_rows": int(covered.sum()),
                    "covered_share": float(covered.mean()),
                    "median_n_when_covered": float(n[covered].median()) if covered.any() else 0.0,
                }
            )
    return pd.DataFrame(rows)


def first_finite(frame: pd.DataFrame, cols: list[str], fallback: pd.Series) -> pd.Series:
    values = frame[cols].apply(pd.to_numeric, errors="coerce") if cols else pd.DataFrame(index=frame.index)
    out = pd.to_numeric(fallback, errors="coerce").copy()
    for col in reversed(cols):
        out = pd.to_numeric(frame[col], errors="coerce").combine_first(out)
    return out


def add_risk_aware_basis_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["risk_qwidth_extreme"] = out["qwidth_band"].astype(str).eq("qwidth_extreme").astype(float)
    out["risk_gap_020_plus"] = out["gap_band"].astype(str).eq("gap_020_plus").astype(float)
    out["risk_n_10_19"] = out["svc_group_n_band"].astype(str).eq("n_10_19").astype(float)
    out["risk_low_n"] = out["svc_group_n_band"].astype(str).isin(["n_0_4", "n_5_9"]).astype(float)
    out["risk_spread_extreme"] = out["pred_spread_band"].astype(str).eq("spread_extreme").astype(float)
    out["hcoef23_risk_score"] = (
        out["risk_qwidth_extreme"]
        + out["risk_gap_020_plus"]
        + out["risk_n_10_19"]
        + out["risk_spread_extreme"]
    )
    out["hcoef23_risk_factor"] = np.select(
        [
            out["hcoef23_risk_score"] >= 3,
            out["hcoef23_risk_score"] == 2,
            out["hcoef23_risk_score"] == 1,
            out["risk_low_n"].eq(1.0),
        ],
        [0.40, 0.55, 0.75, 0.60],
        default=1.0,
    )

    for policy in POLICIES:
        price_cols = [f"{policy}_basis_{level}_price_log" for level in RISK_LEVELS if f"{policy}_basis_{level}_price_log" in out.columns]
        unit_cols = [f"{policy}_basis_{level}_unit_area_log" for level in RISK_LEVELS if f"{policy}_basis_{level}_unit_area_log" in out.columns]
        n_cols = [f"{policy}_basis_{level}_n" for level in RISK_LEVELS if f"{policy}_basis_{level}_n" in out.columns]
        iqr_cols = [f"{policy}_basis_{level}_iqr" for level in RISK_LEVELS if f"{policy}_basis_{level}_iqr" in out.columns]

        raw_price = first_finite(out, price_cols, out[BASELINE])
        raw_unit = first_finite(out, unit_cols, raw_price)
        raw_n = first_finite(out, n_cols, pd.Series(0.0, index=out.index)).fillna(0.0).clip(lower=0.0)
        raw_iqr = first_finite(out, iqr_cols, pd.Series(np.nan, index=out.index))

        out[f"{policy}_basis_first_price_log"] = raw_price
        out[f"{policy}_basis_first_unit_area_log"] = raw_unit
        out[f"{policy}_basis_first_n"] = raw_n
        out[f"{policy}_basis_first_n_log"] = np.log1p(raw_n)
        out[f"{policy}_basis_first_iqr"] = raw_iqr
        out[f"{policy}_basis_missing"] = raw_price.isna().astype(float)
        out[f"{policy}_basis_first_price_log"] = out[f"{policy}_basis_first_price_log"].fillna(out[BASELINE])
        out[f"{policy}_basis_first_unit_area_log"] = out[f"{policy}_basis_first_unit_area_log"].fillna(out[f"{policy}_basis_first_price_log"])

        artist_col = f"{policy}_basis_artist_price_log"
        global_col = f"{policy}_basis_global_price_log"
        artist_prior = pd.to_numeric(out.get(artist_col), errors="coerce").fillna(pd.to_numeric(out.get(global_col), errors="coerce"))
        artist_prior = artist_prior.fillna(out[BASELINE])
        out[f"{policy}_basis_artist_prior_log"] = artist_prior

        for k in [8.0, 16.0]:
            reliability_weight = raw_n / (raw_n + k)
            risk_weight = np.clip(reliability_weight * out["hcoef23_risk_factor"], 0.0, 1.0)
            k_tag = f"k{int(k)}"
            out[f"{policy}_basis_reliability_weight_{k_tag}"] = reliability_weight
            out[f"{policy}_basis_risk_weight_{k_tag}"] = risk_weight
            # Move from the current stable candidate toward the train-derived basis only as much as
            # the validation-derived reliability/risk signal allows.
            source = out[f"{policy}_basis_first_price_log"]
            fallback_source = 0.65 * source + 0.35 * artist_prior
            out[f"{policy}_risk_shrunk_basis_{k_tag}"] = out[BASELINE] + risk_weight * (fallback_source - out[BASELINE])
            out[f"{policy}_risk_shrunk_basis_{k_tag}_gap"] = out[f"{policy}_risk_shrunk_basis_{k_tag}"] - out[BASELINE]

        out[f"{policy}_basis_vs_stable_gap"] = out[f"{policy}_basis_first_price_log"] - out[BASELINE]
        out[f"{policy}_unit_basis_vs_stable_gap"] = out[f"{policy}_basis_first_unit_area_log"] - out[BASELINE]
    return out


def build_candidate_configs() -> list[CandidateConfig]:
    configs: list[CandidateConfig] = [
        CandidateConfig(BASELINE, "source", source_col=BASELINE, purpose="현재 HCOEF 안정 후보"),
        CandidateConfig(REFERENCE, "source", source_col=REFERENCE, purpose="서비스 v0.1 70:30 기준 후보"),
        CandidateConfig(PPV8, "source", source_col=PPV8, purpose="PP-V8/service component proxy"),
        CandidateConfig(SVC, "source", source_col=SVC, purpose="유사 작품 기반 가격 피처"),
        CandidateConfig("l10_seq_full_generated_bucket", "source", source_col=L10_COL, purpose="PP-L10 순차 component"),
    ]
    for policy in POLICIES:
        for k_tag in ["k8", "k16"]:
            gap = f"{policy}_risk_shrunk_basis_{k_tag}_gap"
            for cap in [0.03, 0.05, 0.08]:
                for strength in [0.25, 0.50, 0.75]:
                    configs.append(
                        CandidateConfig(
                            candidate=f"hcoef24_{policy}_risk_basis_{k_tag}_cap{slug_float(cap)}_s{slug_float(strength)}",
                            method="basis_component",
                            gap_col=gap,
                            cap=cap,
                            strength=strength,
                            purpose="HCOEF23 위험 구간에서 기준가 이동을 줄인 capped basis component",
                        )
                    )

        feature_sets = {
            "risk_basis_core": (
                f"{policy}_risk_shrunk_basis_k8_gap",
                "current_minus_stable",
                "ppv8_minus_stable",
                "svc_minus_stable",
                "pred_spread",
                "quantile_width",
                "svc_group_n_log",
                "coverage_numeric",
                "hcoef23_risk_score",
            ),
            "risk_basis_reliability": (
                f"{policy}_risk_shrunk_basis_k16_gap",
                f"{policy}_basis_first_n_log",
                f"{policy}_basis_first_iqr",
                f"{policy}_basis_risk_weight_k16",
                "quantile_width",
                "l10_price_range_ratio",
                "pred_spread",
                "coverage_numeric",
                "hcoef23_risk_score",
                "risk_gap_020_plus",
                "risk_qwidth_extreme",
            ),
        }
        for fs_name, features in feature_sets.items():
            for alpha in [0.001, 0.01]:
                for cap in [0.02, 0.03, 0.05]:
                    for strength in [0.25, 0.50]:
                        configs.append(
                            CandidateConfig(
                                candidate=(
                                    f"hcoef24_resid_huber_{policy}_{fs_name}_"
                                    f"a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}"
                                ),
                                method="residual_huber",
                                features=features,
                                alpha=alpha,
                                cap=cap,
                                strength=strength,
                                purpose="위험도 완화 기준가와 component gap을 사용한 저차원 Huber 잔차 보정",
                            )
                        )

        direct_features = (
            BASELINE,
            REFERENCE,
            PPV8,
            SVC,
            L10_COL,
            f"{policy}_risk_shrunk_basis_k8",
            f"{policy}_basis_first_unit_area_log",
            f"{policy}_basis_first_n_log",
            "quantile_width",
            "pred_spread",
            "svc_group_n_log",
            "coverage_numeric",
            "log_area_filled",
            "hcoef23_risk_score",
        )
        for alpha in [0.01, 0.1]:
            for cap in [0.05, 0.08]:
                for strength in [0.50, 0.75]:
                    configs.append(
                        CandidateConfig(
                            candidate=(
                                f"hcoef24_direct_huber_capped_{policy}_"
                                f"a{slug_float(alpha)}_cap{slug_float(cap)}_s{slug_float(strength)}"
                            ),
                            method="direct_huber_capped",
                            features=direct_features,
                            alpha=alpha,
                            cap=cap,
                            strength=strength,
                            purpose="기준가/component를 직접 학습하되 안정 후보 대비 이동폭을 cap으로 제한",
                        )
                    )

    return configs


def estimator(config: CandidateConfig):
    if config.method in {"residual_huber", "direct_huber_capped"}:
        model = HuberRegressor(epsilon=1.35, alpha=float(config.alpha or 0.001), max_iter=5000)
    elif config.method == "residual_ridge":
        model = Ridge(alpha=float(config.alpha or 1.0))
    else:
        raise ValueError(f"No estimator for {config.method}")
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), model)


def fit_model(train: pd.DataFrame, config: CandidateConfig):
    model = estimator(config)
    x = train[list(config.features)]
    if config.method.startswith("residual_"):
        y = train["actual_log"].to_numpy(dtype=float) - train[BASELINE].to_numpy(dtype=float)
    else:
        y = train["actual_log"].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x, y)
    return model


def predict_source(frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, np.ndarray]:
    source = config.source_col or BASELINE
    pred = pd.to_numeric(frame[source], errors="coerce").to_numpy(dtype=float)
    pred = np.where(np.isfinite(pred), pred, frame[BASELINE].to_numpy(dtype=float))
    return pred, pred - frame[BASELINE].to_numpy(dtype=float)


def predict_basis_component(frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, np.ndarray]:
    if not config.gap_col:
        raise ValueError(f"{config.candidate} missing gap_col")
    raw_gap = pd.to_numeric(frame[config.gap_col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    cap = float(config.cap or 0.0)
    strength = float(config.strength or 1.0)
    move = np.clip(raw_gap, -cap, cap) * strength
    return frame[BASELINE].to_numpy(dtype=float) + move, move


def predict_with_model(model: Any, frame: pd.DataFrame, config: CandidateConfig) -> tuple[np.ndarray, np.ndarray]:
    raw = np.asarray(model.predict(frame[list(config.features)]), dtype=float)
    cap = float(config.cap or 0.0)
    strength = float(config.strength or 1.0)
    if config.method.startswith("residual_"):
        move = np.clip(raw, -cap, cap) * strength
    elif config.method == "direct_huber_capped":
        move = np.clip(raw - frame[BASELINE].to_numpy(dtype=float), -cap, cap) * strength
    else:
        move = raw - frame[BASELINE].to_numpy(dtype=float)
    return frame[BASELINE].to_numpy(dtype=float) + move, move


def validation_oof_predictions(validation: pd.DataFrame, configs: list[CandidateConfig], scheme: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for config in configs:
        if config.method == "source":
            result[config.candidate] = predict_source(validation, config)
            continue
        if config.method == "basis_component":
            result[config.candidate] = predict_basis_component(validation, config)
            continue
        pred = np.full(len(validation), np.nan, dtype=float)
        move = np.full(len(validation), np.nan, dtype=float)
        for train_idx, hold_idx in h20.split_iter(validation, scheme):
            model = fit_model(validation.iloc[train_idx].copy(), config)
            hold_pred, hold_move = predict_with_model(model, validation.iloc[hold_idx].copy(), config)
            pred[hold_idx] = hold_pred
            move[hold_idx] = hold_move
        result[config.candidate] = (pred, move)
    return result


def fixed_predictions(validation: pd.DataFrame, frame: pd.DataFrame, configs: list[CandidateConfig]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for config in configs:
        if config.method == "source":
            result[config.candidate] = predict_source(frame, config)
            continue
        if config.method == "basis_component":
            result[config.candidate] = predict_basis_component(frame, config)
            continue
        model = fit_model(validation, config)
        result[config.candidate] = predict_with_model(model, frame, config)
    return result


def metric_row(
    scope: str,
    split: str,
    candidate: str,
    method: str,
    n: int,
    m: dict[str, float],
    stable_metric: dict[str, float],
    reference_metric: dict[str, float],
    move: np.ndarray,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "split": split,
        "candidate": candidate,
        "method": method,
        "n": n,
        **m,
        "delta_MdAPE_vs_stable": m["MdAPE"] - stable_metric["MdAPE"],
        "delta_MAPE_vs_stable": m["MAPE"] - stable_metric["MAPE"],
        "delta_p95_APE_vs_stable": m["p95_APE"] - stable_metric["p95_APE"],
        "delta_RMSE_log_vs_stable": m["RMSE_log"] - stable_metric["RMSE_log"],
        "delta_MdAPE_vs_current70_30": m["MdAPE"] - reference_metric["MdAPE"],
        "delta_MAPE_vs_current70_30": m["MAPE"] - reference_metric["MAPE"],
        "delta_p95_APE_vs_current70_30": m["p95_APE"] - reference_metric["p95_APE"],
        "improve_count_vs_stable": int(m["MdAPE"] < stable_metric["MdAPE"])
        + int(m["MAPE"] < stable_metric["MAPE"])
        + int(m["p95_APE"] < stable_metric["p95_APE"]),
        "improve_count_vs_current70_30": int(m["MdAPE"] < reference_metric["MdAPE"])
        + int(m["MAPE"] < reference_metric["MAPE"])
        + int(m["p95_APE"] < reference_metric["p95_APE"]),
        "mean_policy_move_log": float(np.nanmean(move)),
        "mean_abs_policy_move_log": float(np.nanmean(np.abs(move))),
    }


def prediction_frame(scope: str, split: str, frame: pd.DataFrame, config: CandidateConfig, pred: np.ndarray, move: np.ndarray) -> pd.DataFrame:
    pred_price = safe_exp(pred)
    actual_price = frame["actual_price"].to_numpy(dtype=float)
    out = pd.DataFrame(
        {
            "experiment_id": EXP_ID,
            "scope": scope,
            "split": split,
            "candidate": config.candidate,
            "method": config.method,
            "_track6_row_id": frame["_track6_row_id"].to_numpy(),
            "artist_key": frame["artist_key"].fillna("").astype(str).to_numpy(),
            "artist_name_ko": frame.get("artist_name_ko", pd.Series("", index=frame.index)).fillna("").astype(str).to_numpy(),
            "actual_log": frame["actual_log"].to_numpy(dtype=float),
            "actual_price": actual_price,
            "pred_log": pred,
            "pred_price": pred_price,
            "policy_move_log": move,
            BASELINE: frame[BASELINE].to_numpy(dtype=float),
            REFERENCE: frame[REFERENCE].to_numpy(dtype=float),
            PPV8: frame[PPV8].to_numpy(dtype=float),
            SVC: frame[SVC].to_numpy(dtype=float),
            L10_COL: frame[L10_COL].to_numpy(dtype=float),
            "quantile_width": frame["quantile_width"].to_numpy(dtype=float),
            "l10_price_range_ratio": frame["l10_price_range_ratio"].to_numpy(dtype=float),
            "svc_group_n": frame["svc_group_n"].to_numpy(dtype=float),
            "svc_coverage_tier": frame["svc_coverage_tier"].astype(str).to_numpy(),
            "svc_group_level": frame["svc_group_level"].astype(str).to_numpy(),
            "service_confidence_tier": frame["service_confidence_tier"].astype(str).to_numpy(),
            "qwidth_band": frame["qwidth_band"].astype(str).to_numpy(),
            "svc_group_n_band": frame["svc_group_n_band"].astype(str).to_numpy(),
            "gap_band": frame["gap_band"].astype(str).to_numpy(),
            "pred_spread_band": frame["pred_spread_band"].astype(str).to_numpy(),
            "stable_pred_price_band": frame["stable_pred_price_band"].astype(str).to_numpy(),
            "medium_support_bucket": frame["medium_support_bucket"].astype(str).to_numpy(),
            "log_area": frame["log_area"].to_numpy(dtype=float),
            "hcoef23_risk_score": frame["hcoef23_risk_score"].to_numpy(dtype=float),
            "hcoef23_risk_factor": frame["hcoef23_risk_factor"].to_numpy(dtype=float),
        }
    )
    for policy in POLICIES:
        for col in [
            f"{policy}_basis_first_price_log",
            f"{policy}_basis_first_unit_area_log",
            f"{policy}_basis_first_n",
            f"{policy}_basis_first_iqr",
            f"{policy}_risk_shrunk_basis_k8",
            f"{policy}_risk_shrunk_basis_k16",
            f"{policy}_basis_risk_weight_k8",
            f"{policy}_basis_risk_weight_k16",
        ]:
            if col in frame.columns:
                out[col] = pd.to_numeric(frame[col], errors="coerce").to_numpy(dtype=float)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def evaluate_all(base: pd.DataFrame, configs: list[CandidateConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    validation = base[base["split"].eq("validation")].reset_index(drop=True)
    test = base[base["split"].eq("test")].reset_index(drop=True)
    stress = base[base["split"].eq("0604_ex50")].reset_index(drop=True)
    metric_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []

    for scheme in ["row", "artist"]:
        pred_map = validation_oof_predictions(validation, configs, scheme)
        stable_metric = metric(validation, pred_map[BASELINE][0])
        reference_metric = metric(validation, pred_map[REFERENCE][0])
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = metric(validation, pred)
            scope = f"validation_oof_{scheme}"
            metric_rows.append(metric_row(scope, "validation", config.candidate, config.method, len(validation), m, stable_metric, reference_metric, move))
            prediction_rows.append(prediction_frame(scope, "validation", validation, config, pred, move))

    for split, frame in [("test", test), ("0604_ex50", stress)]:
        pred_map = fixed_predictions(validation, frame, configs)
        stable_metric = metric(frame, pred_map[BASELINE][0])
        reference_metric = metric(frame, pred_map[REFERENCE][0])
        scope = "fixed_confirmation" if split == "test" else "0604_stress"
        for config in configs:
            pred, move = pred_map[config.candidate]
            m = metric(frame, pred)
            metric_rows.append(metric_row(scope, split, config.candidate, config.method, len(frame), m, stable_metric, reference_metric, move))
            prediction_rows.append(prediction_frame(scope, split, frame, config, pred, move))
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)


def bootstrap_summary(predictions: pd.DataFrame, configs: list[CandidateConfig]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(SEED)
    candidates = [config.candidate for config in configs]
    for scope in ["validation_oof_row", "validation_oof_artist"]:
        focus = predictions[predictions["scope"].eq(scope)].copy()
        if focus.empty:
            continue
        pivot = focus.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
        meta = focus.drop_duplicates("_track6_row_id").set_index("_track6_row_id")
        common = pivot.index[pivot[BASELINE].notna()]
        pivot = pivot.loc[common]
        meta = meta.loc[common]
        actual_price = meta["actual_price"].to_numpy(dtype=float)
        actual_log = meta["actual_log"].to_numpy(dtype=float)
        artists = meta["artist_key"].astype(str).to_numpy()
        unique_artists = np.unique(artists)
        for scheme in ["row_bootstrap", "artist_bootstrap"]:
            stable_pred = pivot[BASELINE].to_numpy(dtype=float)
            deltas: dict[str, list[tuple[float, float, float, float]]] = {candidate: [] for candidate in candidates}
            for _ in range(N_BOOTSTRAP):
                if scheme == "row_bootstrap":
                    idx = rng.integers(0, len(pivot), len(pivot))
                else:
                    sampled_artists = rng.choice(unique_artists, size=len(unique_artists), replace=True)
                    idx = np.concatenate([np.flatnonzero(artists == artist) for artist in sampled_artists])
                    if len(idx) == 0:
                        continue
                stable_m = h20.metric_from_arrays(actual_price[idx], actual_log[idx], stable_pred[idx])
                for candidate in candidates:
                    pred = pivot[candidate].to_numpy(dtype=float)
                    m = h20.metric_from_arrays(actual_price[idx], actual_log[idx], pred[idx])
                    deltas[candidate].append(
                        (
                            m["MdAPE"] - stable_m["MdAPE"],
                            m["MAPE"] - stable_m["MAPE"],
                            m["p95_APE"] - stable_m["p95_APE"],
                            m["RMSE_log"] - stable_m["RMSE_log"],
                        )
                    )
            for config in configs:
                arr = np.asarray(deltas[config.candidate], dtype=float)
                if arr.size == 0:
                    continue
                rows.append(
                    {
                        "source_scope": scope,
                        "validation_scheme": scheme,
                        "candidate": config.candidate,
                        "method": config.method,
                        "n_bootstrap": len(arr),
                        "mean_delta_MdAPE_vs_stable": float(arr[:, 0].mean()),
                        "mean_delta_MAPE_vs_stable": float(arr[:, 1].mean()),
                        "mean_delta_p95_APE_vs_stable": float(arr[:, 2].mean()),
                        "mean_delta_RMSE_log_vs_stable": float(arr[:, 3].mean()),
                        "MdAPE_improve_prob": float((arr[:, 0] < 0).mean()),
                        "MAPE_improve_prob": float((arr[:, 1] < 0).mean()),
                        "p95_improve_prob": float((arr[:, 2] < 0).mean()),
                        "all3_improve_prob": float(((arr[:, 0] < 0) & (arr[:, 1] < 0) & (arr[:, 2] < 0)).mean()),
                        "any2_improve_prob": float(
                            (
                                (arr[:, 0] < 0).astype(int)
                                + (arr[:, 1] < 0).astype(int)
                                + (arr[:, 2] < 0).astype(int)
                                >= 2
                            ).mean()
                        ),
                    }
                )
    return pd.DataFrame(rows)


def selection_table(metrics_df: pd.DataFrame, bootstrap_df: pd.DataFrame) -> pd.DataFrame:
    def metric_slice(scope: str, prefix: str) -> pd.DataFrame:
        cols = [
            "candidate",
            "method",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "improve_count_vs_stable",
            "improve_count_vs_current70_30",
            "mean_abs_policy_move_log",
        ]
        return metrics_df[metrics_df["scope"].eq(scope)][cols].rename(
            columns={
                "MdAPE": f"{prefix}_MdAPE",
                "MAPE": f"{prefix}_MAPE",
                "p95_APE": f"{prefix}_p95_APE",
                "RMSE_log": f"{prefix}_RMSE_log",
                "delta_MdAPE_vs_stable": f"{prefix}_delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable": f"{prefix}_delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable": f"{prefix}_delta_p95_APE_vs_stable",
                "improve_count_vs_stable": f"{prefix}_improve_count_vs_stable",
                "improve_count_vs_current70_30": f"{prefix}_improve_count_vs_current70_30",
                "mean_abs_policy_move_log": f"{prefix}_mean_abs_policy_move_log",
            }
        )

    out = metric_slice("validation_oof_row", "row_oof")
    for scope, prefix in [
        ("validation_oof_artist", "artist_oof"),
        ("fixed_confirmation", "test"),
        ("0604_stress", "stress0604"),
    ]:
        out = out.merge(metric_slice(scope, prefix).drop(columns=["method"], errors="ignore"), on="candidate", how="left")

    if not bootstrap_df.empty:
        boot = bootstrap_df.pivot_table(
            index="candidate",
            columns=["source_scope", "validation_scheme"],
            values=["all3_improve_prob", "any2_improve_prob"],
            aggfunc="first",
        )
        boot.columns = [f"{scope}_{scheme}_{metric}" for metric, scope, scheme in boot.columns]
        out = out.merge(boot.reset_index(), on="candidate", how="left")

    row_all3 = out.get("validation_oof_row_row_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    artist_all3 = out.get("validation_oof_artist_artist_bootstrap_all3_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    row_any2 = out.get("validation_oof_row_row_bootstrap_any2_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    artist_any2 = out.get("validation_oof_artist_artist_bootstrap_any2_improve_prob", pd.Series(0.0, index=out.index)).fillna(0.0)
    out["bootstrap_all3_gate"] = (row_all3 >= 0.90) & (artist_all3 >= 0.90)
    out["bootstrap_any2_gate"] = (row_any2 >= 0.90) & (artist_any2 >= 0.90)
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= STABLE_TEST_P95
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= STABLE_0604_P95
    out["fixed_test_2of3"] = out["test_improve_count_vs_stable"] >= 2
    out["row_artist_2of3"] = (out["row_oof_improve_count_vs_stable"] >= 2) & (out["artist_oof_improve_count_vs_stable"] >= 2)
    out["mape_special_guard"] = (
        out["test_MAPE"].lt(out.loc[out["candidate"].eq(BASELINE), "test_MAPE"].min())
        & (out["test_MdAPE"] <= out.loc[out["candidate"].eq(BASELINE), "test_MdAPE"].min() + 0.003)
        & (out["test_p95_APE"] <= STABLE_TEST_P95 + 0.015)
    )

    conditions = [
        out["bootstrap_all3_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
        out["bootstrap_any2_gate"] & out["fixed_test_p95_guard"] & out["fixed_test_2of3"],
        out["mape_special_guard"],
        out["test_p95_APE"].lt(out.loc[out["candidate"].eq(BASELINE), "test_p95_APE"].min())
        & (out["test_MdAPE"] <= out.loc[out["candidate"].eq(BASELINE), "test_MdAPE"].min() + 0.003),
        out["row_artist_2of3"],
    ]
    choices = ["운영 후보 검토", "반복 검증 통과 후보", "MAPE 특화 후보", "p95 방어 후보", "OOF 개선 후보"]
    out["decision"] = np.select(conditions, choices, default="보류")
    out.loc[out["candidate"].eq(BASELINE), "decision"] = "현재 기준 후보"
    out.loc[out["candidate"].eq(REFERENCE), "decision"] = "최소 비교 기준"
    out.loc[out["method"].eq("source") & ~out["candidate"].isin([BASELINE, REFERENCE]), "decision"] = "component 대조군"
    order = {
        "현재 기준 후보": 0,
        "운영 후보 검토": 1,
        "반복 검증 통과 후보": 2,
        "MAPE 특화 후보": 3,
        "p95 방어 후보": 4,
        "OOF 개선 후보": 5,
        "최소 비교 기준": 6,
        "component 대조군": 7,
        "보류": 8,
    }
    out["decision_order"] = out["decision"].map(order).fillna(9)
    return out.sort_values(["decision_order", "test_MdAPE", "test_MAPE", "test_p95_APE", "candidate"]).drop(columns=["decision_order"])


def coefficient_table(validation: pd.DataFrame, configs: list[CandidateConfig], selected: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    focus = set(selected) | {BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket"}
    for config in configs:
        if config.candidate not in focus:
            continue
        if config.method == "source":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": config.source_col,
                    "standardized_coefficient": 1.0,
                    "raw_role": "source_prediction",
                    "direction": "positive",
                    "interpretation": config.purpose,
                }
            )
            continue
        if config.method == "basis_component":
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": config.gap_col,
                    "standardized_coefficient": float(config.strength or 1.0),
                    "raw_role": "capped_basis_move",
                    "direction": "raises_or_lowers_with_basis",
                    "interpretation": "위험도 완화 기준가와 안정 후보의 차이를 cap 안에서만 반영한다.",
                }
            )
            continue
        model = fit_model(validation, config)
        final = model.steps[-1][1]
        coefs = getattr(final, "coef_", np.zeros(len(config.features)))
        for feature, coef in zip(config.features, coefs):
            rows.append(
                {
                    "candidate": config.candidate,
                    "method": config.method,
                    "feature": feature,
                    "standardized_coefficient": float(coef),
                    "raw_role": "residual_log" if config.method.startswith("residual_") else "actual_log_capped_to_stable",
                    "direction": "raises prediction" if coef > 0 else "lowers prediction" if coef < 0 else "neutral",
                    "interpretation": feature_interpretation(feature),
                }
            )
    return pd.DataFrame(rows)


def feature_interpretation(feature: str) -> str:
    if feature == "hcoef23_risk_score":
        return "HCOEF23에서 확인한 위험 신호 개수다. 클수록 기준가 이동을 보수적으로 봐야 한다."
    if feature in {"risk_gap_020_plus", "risk_qwidth_extreme"}:
        return "후보 간 의견 차이 또는 예측 범위가 큰 구간인지 나타내는 위험 flag다."
    if "risk_shrunk_basis" in feature:
        return "유사 작품 기준가를 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가다."
    if "basis_first_n" in feature:
        return "선택된 기준가를 만든 유사 표본 수다. 많을수록 기준가 신뢰도가 높다."
    if "basis_first_iqr" in feature:
        return "기준가 그룹 내부 가격 분산이다. 클수록 같은 그룹 안 가격 편차가 크다."
    if feature in {BASELINE, REFERENCE, PPV8, SVC, L10_COL}:
        return "기존 Warm component 또는 후보 예측값이다."
    if feature == "quantile_width":
        return "퀀타일 예측 폭이다. 클수록 예측 불확실성이 큰 신호다."
    if feature == "pred_spread":
        return "여러 component 예측값 사이의 차이다. 클수록 모델 의견 차이가 크다."
    if feature == "svc_group_n_log":
        return "유사 작품 표본 수를 로그 변환한 신뢰도 피처다."
    if feature == "coverage_numeric":
        return "유사 작품 표본 coverage 등급을 숫자로 바꾼 피처다."
    if feature == "log_area_filled":
        return "작품 크기 효과를 나타내는 로그 면적 피처다."
    return "저차원 Huber 보정에 사용하는 보조 피처다."


def residual_analysis(predictions: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    focus_candidates = list(dict.fromkeys([BASELINE, REFERENCE, PPV8, SVC, "l10_seq_full_generated_bucket", *selected]))
    focus = predictions[predictions["candidate"].isin(focus_candidates)].copy()
    rows: list[dict[str, Any]] = []
    segment_cols = [
        "qwidth_band",
        "gap_band",
        "svc_group_n_band",
        "pred_spread_band",
        "svc_group_level",
        "stable_pred_price_band",
        "hcoef23_risk_score",
        "medium_support_bucket",
    ]
    for col in segment_cols:
        if col not in focus.columns:
            continue
        for (scope, split, candidate, value), group in focus.groupby(["scope", "split", "candidate", col], dropna=False):
            if len(group) < 10:
                continue
            rows.append(
                {
                    "scope": scope,
                    "split": split,
                    "candidate": candidate,
                    "segment_col": col,
                    "segment_value": value,
                    "n": len(group),
                    "MdAPE": float(group["ape"].median()),
                    "MAPE": float(group["ape"].mean()),
                    "p95_APE": float(group["ape"].quantile(0.95)),
                    "median_residual_log": float(group["residual_log"].median()),
                    "mean_residual_log": float(group["residual_log"].mean()),
                    "mean_abs_move_log": float(group["policy_move_log"].abs().mean()),
                    "over_50pct_error_rate": float((group["ape"] > 0.50).mean()),
                    "over_100pct_error_rate": float((group["ape"] > 1.00).mean()),
                }
            )
    return pd.DataFrame(rows).sort_values(["scope", "split", "segment_col", "MAPE"], ascending=[True, True, True, False])


def md_to_html(markdown: str) -> str:
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

    for line in markdown.splitlines():
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
        "th,td{border:1px solid #d8dee9;padding:6px 9px;font-size:13px;text-align:left;vertical-align:top}"
        "th{background:#f3f4f6} h1,h2{margin-top:24px}"
    )
    return f"<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>{EXP_ID}</title><style>{style}</style></head><body>{''.join(body)}</body></html>"


def write_report(
    metrics_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    coefficients: pd.DataFrame,
    residuals: pd.DataFrame,
    coverage: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
) -> None:
    test = metrics_df[metrics_df["scope"].eq("fixed_confirmation")].copy()
    row_oof = metrics_df[metrics_df["scope"].eq("validation_oof_row")].copy()
    artist_oof = metrics_df[metrics_df["scope"].eq("validation_oof_artist")].copy()
    stress = metrics_df[metrics_df["scope"].eq("0604_stress")].copy()
    baseline_test = test[test["candidate"].eq(BASELINE)].iloc[0]
    ref_test = test[test["candidate"].eq(REFERENCE)].iloc[0]

    candidates_for_report = selected_df[
        ~selected_df["decision"].isin(["현재 기준 후보", "보류", "component 대조군", "최소 비교 기준"])
    ].copy()
    operating = candidates_for_report[candidates_for_report["decision"].isin(["운영 후보 검토", "반복 검증 통과 후보"])].copy()
    if not operating.empty:
        best = operating.iloc[0]
        best_line = (
            f"상위 운영 검토 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test MdAPE/MAPE/p95 "
            f"`{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`)."
        )
    elif not candidates_for_report.empty:
        best = candidates_for_report.iloc[0]
        best_line = (
            f"새 운영 기본 후보는 없음. 상위 목적별 후보는 `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test MdAPE/MAPE/p95 "
            f"`{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`). "
            "`hcoef_stable`은 계속 현재 기준 후보로 유지."
        )
    else:
        best_line = "새 운영 후보 또는 목적별 후보 없음. 현재 기준 후보 `hcoef_stable` 유지."

    top_cols = ["candidate", "method", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable"]
    selected_cols = [
        "candidate",
        "decision",
        "row_oof_MdAPE",
        "row_oof_MAPE",
        "row_oof_p95_APE",
        "artist_oof_MdAPE",
        "artist_oof_MAPE",
        "artist_oof_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "stress0604_MdAPE",
        "stress0604_MAPE",
        "stress0604_p95_APE",
        "bootstrap_all3_gate",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
    ]

    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber 위험 완화 기준가 생성 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF23에서 확인한 위험 구간에서 유사 작품 기준가 이동을 줄이고, Huber 계수 후보가 현재 Warm 안정 후보를 넘는지 검증.",
            "- 현재 기준 후보: `hcoef_stable`.",
            "- 최소 비교 기준: `current_70_30`.",
            "- 선택 원칙: validation OOF/bootstrap에서 후보를 고르고 fixed test/0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 기준 fixed test: MdAPE `{baseline_test['MdAPE']:.4f}`, MAPE `{baseline_test['MAPE']:.4f}`, p95 `{baseline_test['p95_APE']:.4f}`, RMSE_log `{baseline_test['RMSE_log']:.4f}`.",
            f"- 최소 비교 기준 fixed test: MdAPE `{ref_test['MdAPE']:.4f}`, MAPE `{ref_test['MAPE']:.4f}`, p95 `{ref_test['p95_APE']:.4f}`, RMSE_log `{ref_test['RMSE_log']:.4f}`.",
            "- HCOEF24는 HCOEF4/5의 loose 기준가를 반복하지 않고, `qwidth_extreme`, `gap_020_plus`, `n_10_19`, `spread_extreme` 구간에서 기준가 반영 강도를 낮춘 실험임.",
            "",
            "## 2. 후보 선택표",
            "",
            md_table(selected_df[selected_cols].round(4), max_rows=30),
            "",
            "## 3. Validation OOF 상위 후보",
            "",
            "### Row OOF",
            "",
            md_table(row_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "### Artist OOF",
            "",
            md_table(artist_oof.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "## 4. Fixed Test 상위 후보",
            "",
            md_table(test.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=24),
            "",
            "## 5. 0604 Stress Test 상위 후보",
            "",
            md_table(stress.sort_values(["MdAPE", "MAPE", "p95_APE"])[top_cols].round(4), max_rows=20),
            "",
            "## 6. 주요 계수 해석",
            "",
            "- 계수는 표준화된 피처 기준이며 방향성과 상대 영향 비교용.",
            "- `risk_shrunk_basis` 계열은 유사 작품 기준가를 그대로 쓰지 않고 표본 수와 위험도에 따라 안정 후보 쪽으로 줄인 기준가.",
            "- `quantile_width`, `pred_spread`, `hcoef23_risk_score`는 가격을 직접 결정하는 피처라기보다 기준가를 얼마나 믿을지 판단하는 위험 신호.",
            "",
            md_table(coefficients.sort_values(["candidate", "standardized_coefficient"], ascending=[True, False]).round(5), max_rows=80),
            "",
            "## 7. 기준가 Coverage",
            "",
            md_table(coverage.round(4), max_rows=54),
            "",
            "## 8. 잔차/큰 오차 구간",
            "",
            md_table(residuals.round(4), max_rows=60),
            "",
            "## 9. Bootstrap 요약",
            "",
            md_table(bootstrap_df.sort_values(["all3_improve_prob", "any2_improve_prob"], ascending=[False, False]).round(4), max_rows=40),
            "",
            "## 10. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/coverage_summary.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef24_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef24_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(md_to_html(md), encoding="utf-8")


def write_config(configs: list[CandidateConfig], coverage: pd.DataFrame) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": BASELINE,
        "reference": REFERENCE,
        "policies": list(POLICIES),
        "risk_signals_from_hcoef23": [
            "qwidth_extreme",
            "gap_020_plus",
            "svc_group_n_band=n_10_19",
            "pred_spread_band=spread_extreme",
        ],
        "selection_rule": "validation/OOF/bootstrap first; fixed test and 0604 confirmation only",
        "candidate_count": len(configs),
        "outputs": [
            "metrics.csv",
            "candidate_predictions.csv",
            "feature_coefficients.csv",
            "residual_analysis.csv",
            "bootstrap_or_repeated_split_summary.csv",
            "coverage_summary.csv",
            "selected_candidates.csv",
        ],
        "coverage_rows": int(len(coverage)),
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    base, coverage = load_basis_augmented_frame()
    configs = build_candidate_configs()
    metrics_df, predictions = evaluate_all(base, configs)
    bootstrap_df = bootstrap_summary(predictions, configs)
    selected_df = selection_table(metrics_df, bootstrap_df)
    selected_names = selected_df.head(12)["candidate"].astype(str).tolist()
    coefficients = coefficient_table(base[base["split"].eq("validation")].reset_index(drop=True), configs, selected_names)
    residuals = residual_analysis(predictions, selected_names)

    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    bootstrap_df.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    coverage.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    selected_df.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    write_config(configs, coverage)
    write_report(metrics_df, selected_df, coefficients, residuals, coverage, bootstrap_df)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
