#!/usr/bin/env python3
"""Run PP-HCOEF28: Huber risk model based shrinkage for Warm HCOEF candidates.

HCOEF27 showed that HCOEF26 low-risk fallback candidates can improve fixed test
MdAPE/MAPE while defending p95, but the repeated split/artist holdout signal is
not strong enough to promote them. HCOEF28 therefore does not tune fixed test
thresholds. It trains an interpretable Huber model on validation OOF residual
magnitude, predicts each row's large-error risk, and shrinks an existing
candidate's movement toward ``hcoef_stable`` when the predicted risk is high.

The experiment keeps the Huber coefficient interpretation surface:

    risk = HuberRegressor(risk_features -> abs(actual_log - hcoef_stable_log))
    weight = floor + (1 - floor) * (1 - alpha * normalized_risk)
    corrected_log = hcoef_stable_log + weight * (source_candidate_log - hcoef_stable_log)

Validation OOF chooses the risk model and shrink policy family. Fixed test and
0604 are confirmation/stress checks only.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import warnings


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.track6 import run_pp_hcoef24_warm_huber_price_basis_coefficient_refinement as h24


EXP_ID = "PP-HCOEF28"
EXP_SLUG = "PP-HCOEF28_warm_huber_price_basis_coefficient_refinement"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
H27_DIR = REPO / "experiments" / "track6" / "PP-HCOEF27_warm_huber_price_basis_coefficient_refinement"

BASELINE = "hcoef_stable"
REFERENCE = "current_70_30"
PPV8 = "ppv8_service_proxy"
SVC = "svc_numeric_seed_mean"
L10_CANDIDATE = "l10_seq_full_generated_bucket"
L10_COL = "l10_seq_pred_log"
SEED = 20260608
N_REPEATS = 500
ROW_FRACTION = 0.80
ARTIST_FRACTION = 0.80

KEY_COLS = ["scope", "split", "_track6_row_id"]
BASE_COMPONENTS = [BASELINE, REFERENCE, PPV8, SVC, L10_CANDIDATE]


RISK_FEATURES = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n_log",
    "hcoef23_risk_score",
    "stable_current_gap_abs",
    "stable_ppv8_gap_abs",
    "stable_svc_gap_abs",
    "ppv8_svc_gap_abs",
    "pred_spread_numeric",
    "log_area",
    "risk_qwidth_extreme",
    "risk_gap_020_plus",
    "risk_spread_extreme",
    "risk_low_n",
    "risk_n_10_19",
    "risk_artist_fallback",
]


@dataclass(frozen=True)
class PolicyConfig:
    source_candidate: str
    source_tag: str
    alpha: float
    floor: float
    guard_name: str
    guard_quantile: float | None
    guard_weight: float | None
    lowrisk_boost: float

    @property
    def candidate(self) -> str:
        return (
            f"hcoef28_{self.source_tag}"
            f"_a{fmt_token(self.alpha)}"
            f"_f{fmt_token(self.floor)}"
            f"_{self.guard_name}"
            f"_boost{fmt_token(self.lowrisk_boost)}"
        )


def fmt_token(value: float) -> str:
    return f"{value:.2f}".replace(".", "p").rstrip("0").rstrip("p")


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.exp(np.clip(pred_log, 0, 30))
    actual_price = np.asarray(actual_price, dtype=float)
    actual_log = np.asarray(actual_log, dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(actual_log) & np.isfinite(pred_log)
    if valid.sum() == 0:
        return {
            "n": 0,
            "MdAPE": np.nan,
            "MAPE": np.nan,
            "p95_APE": np.nan,
            "RMSE_log": np.nan,
            "Within_30": np.nan,
            "Within_50": np.nan,
            "over_2x_n": np.nan,
            "under_half_n": np.nan,
        }
    pred_price = pred_price[valid]
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred_log = np.asarray(pred_log, dtype=float)[valid]
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "over_2x_n": int(np.sum(pred_price >= actual_price * 2.0)),
        "under_half_n": int(np.sum(pred_price <= actual_price * 0.5)),
    }


def add_risk_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in [BASELINE, REFERENCE, PPV8, SVC, L10_COL, "quantile_width", "l10_price_range_ratio", "svc_group_n", "hcoef23_risk_score", "log_area"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["svc_group_n"] = out["svc_group_n"].fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    out["hcoef23_risk_score"] = out["hcoef23_risk_score"].fillna(0.0)
    out["stable_current_gap_abs"] = (out[BASELINE] - out[REFERENCE]).abs()
    out["stable_ppv8_gap_abs"] = (out[BASELINE] - out[PPV8]).abs()
    out["stable_svc_gap_abs"] = (out[BASELINE] - out[SVC]).abs()
    out["ppv8_svc_gap_abs"] = (out[PPV8] - out[SVC]).abs()
    component_cols = [BASELINE, REFERENCE, PPV8, SVC, L10_COL]
    out["pred_spread_numeric"] = out[component_cols].max(axis=1) - out[component_cols].min(axis=1)
    out["risk_qwidth_extreme"] = out["qwidth_band"].astype(str).eq("qwidth_extreme").astype(float)
    out["risk_gap_020_plus"] = out["gap_band"].astype(str).eq("gap_020_plus").astype(float)
    out["risk_spread_extreme"] = out["pred_spread_band"].astype(str).eq("spread_extreme").astype(float)
    out["risk_low_n"] = out["svc_group_n_band"].astype(str).isin(["n_0_4", "n_5_9"]).astype(float)
    out["risk_n_10_19"] = out["svc_group_n_band"].astype(str).eq("n_10_19").astype(float)
    out["risk_artist_fallback"] = out["svc_group_level"].astype(str).eq("artist").astype(float)
    for col in RISK_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def risk_matrix(frame: pd.DataFrame) -> np.ndarray:
    return frame[RISK_FEATURES].to_numpy(dtype=float)


def make_huber_pipeline(alpha: float = 0.001) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=1000)),
        ]
    )


def fit_model(X: np.ndarray, y: np.ndarray) -> Pipeline:
    model = make_huber_pipeline()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        try:
            model.fit(X, y)
            return model
        except Exception:
            fallback = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])
            fallback.fit(X, y)
            return fallback


def crossfit_risk(frame: pd.DataFrame, mode: str) -> tuple[np.ndarray, Pipeline]:
    X = risk_matrix(frame)
    y = (pd.to_numeric(frame["actual_log"], errors="coerce") - pd.to_numeric(frame[BASELINE], errors="coerce")).abs().fillna(0.0).to_numpy(dtype=float)
    pred = np.zeros(len(frame), dtype=float)
    rng = np.random.default_rng(SEED)
    if mode == "artist":
        groups = frame["artist_key"].fillna("unknown").astype(str).to_numpy()
        unique_groups = np.unique(groups)
        n_splits = min(5, len(unique_groups))
        if n_splits < 2:
            splitter = KFold(n_splits=5, shuffle=True, random_state=SEED)
            splits = splitter.split(X)
        else:
            splitter = GroupKFold(n_splits=n_splits)
            splits = splitter.split(X, y, groups)
    else:
        splitter = KFold(n_splits=5, shuffle=True, random_state=SEED)
        splits = splitter.split(X)

    for train_idx, hold_idx in splits:
        model = fit_model(X[train_idx], y[train_idx])
        pred[hold_idx] = model.predict(X[hold_idx])
    full = fit_model(X, y)
    pred = np.clip(pred, 0.0, None)
    jitter = rng.normal(0, 1e-9, size=len(pred))
    return pred + jitter, full


def select_sources() -> tuple[list[str], pd.DataFrame]:
    selected = pd.read_csv(H27_DIR / "outputs" / "selected_candidates.csv")
    fixed = selected[
        selected["decision"].eq("fixed 확인 후보")
        & ~selected["candidate"].isin(BASE_COMPONENTS)
    ].sort_values(["test_MdAPE", "test_MAPE", "test_p95_APE"])
    direct = selected[
        selected["candidate"].astype(str).str.contains("direct_huber", regex=False)
    ].sort_values(["repeated_min_any2_improve_prob", "repeated_min_all3_improve_prob"], ascending=False)
    sources: list[str] = []
    rows: list[dict[str, Any]] = []
    if not fixed.empty:
        cand = str(fixed.iloc[0]["candidate"])
        sources.append(cand)
        rows.append({"source_candidate": cand, "source_tag": "h26_lowrisk_fixed", "source_reason": "HCOEF26/HCOEF27 fixed test 2개 지표 개선 + p95 방어 후보"})
    if not direct.empty:
        cand = str(direct.iloc[0]["candidate"])
        if cand not in sources:
            sources.append(cand)
        rows.append({"source_candidate": cand, "source_tag": "h26_direct_guarded", "source_reason": "HCOEF27 반복 any2 개선 확률이 가장 높지만 fixed MdAPE가 악화된 후보"})
    return sources, pd.DataFrame(rows)


def load_base_predictions(sources: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(H27_DIR / "outputs" / "candidate_predictions.csv")
    raw = add_risk_features(raw)
    keep_existing = list(dict.fromkeys([*BASE_COMPONENTS, *sources]))
    existing = raw[raw["candidate"].isin(keep_existing)].copy()
    stable = raw[raw["candidate"].eq(BASELINE)].copy()
    stable = stable.drop_duplicates(KEY_COLS).copy()
    for source in sources:
        src = raw[raw["candidate"].eq(source)][[*KEY_COLS, "pred_log"]].rename(columns={"pred_log": f"{source}__pred_log"})
        stable = stable.merge(src, on=KEY_COLS, how="left", validate="one_to_one")
    return stable, existing


def attach_risk_predictions(stable: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = stable.copy()
    risk_rows: list[pd.DataFrame] = []
    row_val = out[out["scope"].eq("validation_oof_row")].copy()
    artist_val = out[out["scope"].eq("validation_oof_artist")].copy()
    row_pred, row_model = crossfit_risk(row_val, mode="row")
    artist_pred, artist_model = crossfit_risk(artist_val, mode="artist")

    q10, q33, q80, q90 = np.quantile(row_pred, [0.10, 0.33, 0.80, 0.90])
    denom = max(q90 - q10, 1e-9)

    full_row_model = fit_model(risk_matrix(row_val), (row_val["actual_log"] - row_val[BASELINE]).abs().to_numpy(dtype=float))

    out["risk_pred_abs_residual"] = np.nan
    out.loc[row_val.index, "risk_pred_abs_residual"] = row_pred
    out.loc[artist_val.index, "risk_pred_abs_residual"] = artist_pred
    other_idx = out["risk_pred_abs_residual"].isna()
    out.loc[other_idx, "risk_pred_abs_residual"] = np.clip(full_row_model.predict(risk_matrix(out.loc[other_idx])), 0.0, None)
    out["risk_norm"] = ((out["risk_pred_abs_residual"] - q10) / denom).clip(0.0, 1.0)
    out["risk_high_q80"] = (out["risk_pred_abs_residual"] >= q80).astype(float)
    out["risk_high_q90"] = (out["risk_pred_abs_residual"] >= q90).astype(float)
    out["risk_low_q33"] = (out["risk_pred_abs_residual"] <= q33).astype(float)

    for label, model in [("row_oof_full", row_model), ("artist_oof_full", artist_model), ("row_validation_full_for_test", full_row_model)]:
        estimator = model.named_steps["model"]
        coefs = getattr(estimator, "coef_", np.zeros(len(RISK_FEATURES)))
        for feature, coef in zip(RISK_FEATURES, coefs):
            risk_rows.append(
                {
                    "coefficient_scope": "risk_huber_abs_residual",
                    "model_label": label,
                    "feature": feature,
                    "coefficient": float(coef),
                    "interpretation": risk_feature_interpretation(feature, float(coef)),
                }
            )

    thresholds = pd.DataFrame(
        [
            {"threshold": "risk_q10", "value": float(q10), "meaning": "risk_norm 하한"},
            {"threshold": "risk_q33", "value": float(q33), "meaning": "low-risk boost 판단 경계"},
            {"threshold": "risk_q80", "value": float(q80), "meaning": "강한 shrink guard 시작"},
            {"threshold": "risk_q90", "value": float(q90), "meaning": "극단 risk shrink guard 시작"},
        ]
    )
    thresholds.to_csv(EXP_DIR / "outputs" / "risk_model_thresholds.csv", index=False)
    return out, pd.DataFrame(risk_rows)


def risk_feature_interpretation(feature: str, coef: float) -> str:
    direction = "위험 증가 방향" if coef > 0 else "위험 감소 방향"
    mapping = {
        "quantile_width": "예측 가격 범위가 넓을수록 큰 오차 위험이 커지는지 보는 피처",
        "l10_price_range_ratio": "q90/q10 가격 범위 비율이 큰 구간의 불확실성",
        "svc_group_n_log": "유사 작품 표본 수가 많을수록 기준가가 안정되는지 보는 피처",
        "hcoef23_risk_score": "HCOEF23에서 확인한 위험 신호의 합",
        "stable_current_gap_abs": "안정 후보와 기존 70:30 후보의 의견 차이",
        "stable_ppv8_gap_abs": "안정 후보와 PP-V8 component의 의견 차이",
        "stable_svc_gap_abs": "안정 후보와 유사 작품 기준가의 의견 차이",
        "ppv8_svc_gap_abs": "오차 안정화 후보와 유사 작품 기준가의 의견 차이",
        "pred_spread_numeric": "주요 후보 예측값 전체의 벌어짐",
        "log_area": "작품 크기 축",
        "risk_qwidth_extreme": "quantile width 극단 구간",
        "risk_gap_020_plus": "후보 간 gap이 0.20 log 이상인 구간",
        "risk_spread_extreme": "후보 예측 spread 극단 구간",
        "risk_low_n": "유사 표본 수 10건 미만 구간",
        "risk_n_10_19": "유사 표본 수 10~19건 구간",
        "risk_artist_fallback": "작가 전체 기준으로 fallback된 구간",
    }
    return f"{mapping.get(feature, feature)}; 계수 기준 {direction}"


def build_policy_configs(sources: list[str], source_basis: pd.DataFrame) -> list[PolicyConfig]:
    tag_map = dict(zip(source_basis["source_candidate"], source_basis["source_tag"]))
    configs: list[PolicyConfig] = []
    guard_options = [
        ("noguard", None, None),
        ("q80zero", 0.80, 0.0),
        ("q90zero", 0.90, 0.0),
        ("q80floor025", 0.80, 0.25),
    ]
    for source in sources:
        tag = tag_map.get(source, "source")
        for alpha in [0.25, 0.50, 0.75, 1.00]:
            for floor in [0.00, 0.25, 0.50]:
                for guard_name, guard_quantile, guard_weight in guard_options:
                    for boost in [0.00, 0.25]:
                        configs.append(
                            PolicyConfig(
                                source_candidate=source,
                                source_tag=tag,
                                alpha=alpha,
                                floor=floor,
                                guard_name=guard_name,
                                guard_quantile=guard_quantile,
                                guard_weight=guard_weight,
                                lowrisk_boost=boost,
                            )
                        )
    return configs


def generate_candidates(stable: pd.DataFrame, existing: pd.DataFrame, configs: list[PolicyConfig]) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[pd.DataFrame] = [existing.copy()]
    policy_rows: list[dict[str, Any]] = []
    q80 = stable.loc[stable["scope"].eq("validation_oof_row"), "risk_pred_abs_residual"].quantile(0.80)
    q90 = stable.loc[stable["scope"].eq("validation_oof_row"), "risk_pred_abs_residual"].quantile(0.90)
    guard_lookup = {0.80: q80, 0.90: q90}

    for cfg in configs:
        src_col = f"{cfg.source_candidate}__pred_log"
        if src_col not in stable:
            continue
        out = stable.copy()
        move = pd.to_numeric(out[src_col], errors="coerce") - pd.to_numeric(out[BASELINE], errors="coerce")
        weight = cfg.floor + (1.0 - cfg.floor) * (1.0 - cfg.alpha * out["risk_norm"].to_numpy(dtype=float))
        weight = np.clip(weight, 0.0, 1.25)
        if cfg.lowrisk_boost > 0:
            low = out["risk_low_q33"].eq(1.0).to_numpy()
            weight[low] = np.minimum(weight[low] * (1.0 + cfg.lowrisk_boost), 1.25)
        if cfg.guard_quantile is not None:
            threshold = guard_lookup[cfg.guard_quantile]
            high = out["risk_pred_abs_residual"].to_numpy(dtype=float) >= threshold
            guard_weight = 0.0 if cfg.guard_weight is None else cfg.guard_weight
            weight[high] = np.minimum(weight[high], guard_weight)
        pred_log = out[BASELINE] + move * weight
        out["candidate"] = cfg.candidate
        out["method"] = "risk_huber_shrink_move"
        out["source_candidate"] = cfg.source_candidate
        out["mask_name"] = cfg.guard_name
        out["mask_applied"] = (weight > 1e-9).astype(float)
        out["strength"] = cfg.alpha
        out["cap"] = np.nan
        out["move_weight"] = weight
        out["pred_log"] = pred_log
        out["pred_price"] = np.exp(np.clip(pred_log, 0, 30))
        out["policy_move_log"] = pred_log - out[BASELINE]
        out["residual_log"] = out["actual_log"] - out["pred_log"]
        out["ape"] = (out["pred_price"] - out["actual_price"]).abs() / out["actual_price"]
        records.append(out)
        policy_rows.append(
            {
                "candidate": cfg.candidate,
                "source_candidate": cfg.source_candidate,
                "source_tag": cfg.source_tag,
                "alpha": cfg.alpha,
                "floor": cfg.floor,
                "guard_name": cfg.guard_name,
                "guard_quantile": cfg.guard_quantile,
                "guard_weight": cfg.guard_weight,
                "lowrisk_boost": cfg.lowrisk_boost,
                "formula": "stable + weight * (source - stable)",
            }
        )

    predictions = pd.concat(records, ignore_index=True, sort=False)
    predictions["experiment_id"] = EXP_ID
    return predictions, pd.DataFrame(policy_rows)


def point_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    stable_metrics: dict[str, dict[str, float]] = {}
    reference_metrics: dict[str, dict[str, float]] = {}
    for (scope, split, candidate), group in predictions.groupby(["scope", "split", "candidate"], sort=False):
        metrics = metric_from_arrays(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy())
        key = f"{scope}::{split}"
        if candidate == BASELINE:
            stable_metrics[key] = metrics
        if candidate == REFERENCE:
            reference_metrics[key] = metrics
        rows.append({"scope": scope, "split": split, "candidate": candidate, **metrics})

    out = pd.DataFrame(rows)
    for idx, row in out.iterrows():
        key = f"{row['scope']}::{row['split']}"
        stable = stable_metrics.get(key, {})
        ref = reference_metrics.get(key, {})
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            out.at[idx, f"delta_{metric}_vs_stable"] = row[metric] - stable.get(metric, np.nan)
            out.at[idx, f"delta_{metric}_vs_current70_30"] = row[metric] - ref.get(metric, np.nan)
        out.at[idx, "improve_count_vs_stable"] = sum(
            row[m] < stable.get(m, -np.inf) for m in ["MdAPE", "MAPE", "p95_APE"]
        )
        out.at[idx, "improve_count_vs_current70_30"] = sum(
            row[m] < ref.get(m, -np.inf) for m in ["MdAPE", "MAPE", "p95_APE"]
        )
    weight_col = "move_weight" if "move_weight" in predictions.columns else "mask_applied"
    share = predictions.groupby(["scope", "split", "candidate"], sort=False)[weight_col].mean().reset_index(name="mean_move_weight")
    out = out.merge(share, on=["scope", "split", "candidate"], how="left")
    return out.sort_values(["scope", "candidate"]).reset_index(drop=True)


def repeated_validation(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    scopes = ["validation_oof_row", "validation_oof_artist"]
    detail_rows: list[dict[str, Any]] = []

    for scope in scopes:
        scoped = predictions[predictions["scope"].eq(scope)].copy()
        if scoped.empty:
            continue
        row_ids = scoped["_track6_row_id"].dropna().unique()
        artists = scoped[["_track6_row_id", "artist_key"]].drop_duplicates()["artist_key"].fillna("unknown").astype(str).unique()
        for scheme in ["row_subsample_80pct", "artist_holdout_80pct"]:
            for repeat in range(N_REPEATS):
                if scheme == "row_subsample_80pct":
                    n_take = max(1, int(len(row_ids) * ROW_FRACTION))
                    chosen = set(rng.choice(row_ids, size=n_take, replace=False))
                    subset = scoped[scoped["_track6_row_id"].isin(chosen)]
                else:
                    n_take = max(1, int(len(artists) * ARTIST_FRACTION))
                    chosen_artists = set(rng.choice(artists, size=n_take, replace=False))
                    subset = scoped[scoped["artist_key"].fillna("unknown").astype(str).isin(chosen_artists)]
                base_group = subset[subset["candidate"].eq(BASELINE)]
                base_metrics = metric_from_arrays(
                    base_group["actual_price"].to_numpy(),
                    base_group["actual_log"].to_numpy(),
                    base_group["pred_log"].to_numpy(),
                )
                for candidate, group in subset.groupby("candidate", sort=False):
                    metrics = metric_from_arrays(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy())
                    detail_rows.append(
                        {
                            "source_scope": scope,
                            "validation_scheme": scheme,
                            "repeat": repeat,
                            "candidate": candidate,
                            **metrics,
                            "delta_MdAPE_vs_stable": metrics["MdAPE"] - base_metrics["MdAPE"],
                            "delta_MAPE_vs_stable": metrics["MAPE"] - base_metrics["MAPE"],
                            "delta_p95_APE_vs_stable": metrics["p95_APE"] - base_metrics["p95_APE"],
                            "delta_RMSE_log_vs_stable": metrics["RMSE_log"] - base_metrics["RMSE_log"],
                            "MdAPE_improved": metrics["MdAPE"] < base_metrics["MdAPE"],
                            "MAPE_improved": metrics["MAPE"] < base_metrics["MAPE"],
                            "p95_improved": metrics["p95_APE"] < base_metrics["p95_APE"],
                        }
                    )

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return detail, detail
    detail["all3_improved"] = detail["MdAPE_improved"] & detail["MAPE_improved"] & detail["p95_improved"]
    detail["any2_improved"] = detail[["MdAPE_improved", "MAPE_improved", "p95_improved"]].sum(axis=1) >= 2
    summary_rows: list[dict[str, Any]] = []
    for (scope, scheme, candidate), group in detail.groupby(["source_scope", "validation_scheme", "candidate"], sort=False):
        row: dict[str, Any] = {
            "source_scope": scope,
            "validation_scheme": scheme,
            "candidate": candidate,
            "n_repeats": int(group["repeat"].nunique()),
        }
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{metric}_vs_stable"]
            row[f"mean_delta_{metric}_vs_stable"] = float(delta.mean())
            row[f"median_delta_{metric}_vs_stable"] = float(delta.median())
            row[f"q05_delta_{metric}_vs_stable"] = float(delta.quantile(0.05))
            row[f"q95_delta_{metric}_vs_stable"] = float(delta.quantile(0.95))
        for metric in ["MdAPE", "MAPE", "p95"]:
            row[f"{metric}_improve_prob"] = float(group[f"{metric}_improved"].mean())
        row["all3_improve_prob"] = float(group["all3_improved"].mean())
        row["any2_improve_prob"] = float(group["any2_improved"].mean())
        summary_rows.append(row)
    return detail, pd.DataFrame(summary_rows)


def selected_table(metrics: pd.DataFrame, repeated: pd.DataFrame, source_basis: pd.DataFrame) -> pd.DataFrame:
    def metric_slice(scope: str, prefix: str) -> pd.DataFrame:
        cols = [
            "candidate",
            "MdAPE",
            "MAPE",
            "p95_APE",
            "RMSE_log",
            "delta_MdAPE_vs_stable",
            "delta_MAPE_vs_stable",
            "delta_p95_APE_vs_stable",
            "improve_count_vs_stable",
            "mean_move_weight",
        ]
        return metrics[metrics["scope"].eq(scope)][cols].rename(
            columns={
                "MdAPE": f"{prefix}_MdAPE",
                "MAPE": f"{prefix}_MAPE",
                "p95_APE": f"{prefix}_p95_APE",
                "RMSE_log": f"{prefix}_RMSE_log",
                "delta_MdAPE_vs_stable": f"{prefix}_delta_MdAPE_vs_stable",
                "delta_MAPE_vs_stable": f"{prefix}_delta_MAPE_vs_stable",
                "delta_p95_APE_vs_stable": f"{prefix}_delta_p95_APE_vs_stable",
                "improve_count_vs_stable": f"{prefix}_improve_count_vs_stable",
                "mean_move_weight": f"{prefix}_mean_move_weight",
            }
        )

    out = metric_slice("validation_oof_row", "row_oof")
    for scope, prefix in [
        ("validation_oof_artist", "artist_oof"),
        ("fixed_confirmation", "test"),
        ("0604_stress", "stress0604"),
    ]:
        out = out.merge(metric_slice(scope, prefix), on="candidate", how="left")

    if not repeated.empty:
        prob = repeated.pivot_table(
            index="candidate",
            values=["all3_improve_prob", "any2_improve_prob", "MdAPE_improve_prob", "MAPE_improve_prob", "p95_improve_prob"],
            aggfunc=["min", "mean"],
        )
        prob.columns = [f"repeated_{stat}_{metric}" for stat, metric in prob.columns]
        out = out.merge(prob.reset_index(), on="candidate", how="left")

    source_map = dict(zip(source_basis["source_candidate"], source_basis["source_reason"]))
    out["source_reason"] = out["candidate"].map(source_map)
    stable_test_p95 = out.loc[out["candidate"].eq(BASELINE), "test_p95_APE"].min()
    stable_0604_p95 = out.loc[out["candidate"].eq(BASELINE), "stress0604_p95_APE"].min()
    out["fixed_test_p95_guard"] = out["test_p95_APE"] <= stable_test_p95
    out["stress0604_p95_guard"] = out["stress0604_p95_APE"] <= stable_0604_p95
    out["fixed_test_2of3"] = out["test_improve_count_vs_stable"] >= 2
    out["repeated_any2_gate"] = out["repeated_min_any2_improve_prob"].fillna(0.0) >= 0.90
    out["repeated_all3_gate"] = out["repeated_min_all3_improve_prob"].fillna(0.0) >= 0.90
    out["decision"] = np.select(
        [
            out["candidate"].eq(BASELINE),
            out["candidate"].eq(REFERENCE),
            out["candidate"].isin([PPV8, SVC, L10_CANDIDATE]),
            out["repeated_all3_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            out["repeated_any2_gate"] & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"] & out["fixed_test_2of3"],
            (out["test_improve_count_vs_stable"] >= 2) & out["fixed_test_p95_guard"] & out["stress0604_p95_guard"],
            (out["test_MAPE"] < out.loc[out["candidate"].eq(BASELINE), "test_MAPE"].min())
            & (out["test_MdAPE"] <= out.loc[out["candidate"].eq(BASELINE), "test_MdAPE"].min() + 0.003)
            & out["fixed_test_p95_guard"],
        ],
        ["현재 기준 후보", "최소 비교 기준", "component 대조군", "반복 검증 통과 후보", "반복 any2 검증 후보", "fixed 확인 후보", "MAPE 목적 후보"],
        default="보류",
    )
    order = {"현재 기준 후보": 0, "반복 검증 통과 후보": 1, "반복 any2 검증 후보": 2, "fixed 확인 후보": 3, "MAPE 목적 후보": 4, "최소 비교 기준": 5, "component 대조군": 6, "보류": 7}
    out["decision_order"] = out["decision"].map(order).fillna(9)
    return out.sort_values(["decision_order", "test_MdAPE", "test_MAPE", "test_p95_APE", "candidate"]).drop(columns=["decision_order"])


def residual_analysis(predictions: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    focus = list(dict.fromkeys([BASELINE, REFERENCE, *selected.head(12)["candidate"].tolist()]))
    segment_cols = ["qwidth_band", "svc_group_n_band", "gap_band", "pred_spread_band", "service_confidence_tier", "svc_group_level"]
    rows: list[dict[str, Any]] = []
    subset = predictions[predictions["candidate"].isin(focus)].copy()
    for (scope, split, candidate), cand_df in subset.groupby(["scope", "split", "candidate"], sort=False):
        overall = metric_from_arrays(cand_df["actual_price"].to_numpy(), cand_df["actual_log"].to_numpy(), cand_df["pred_log"].to_numpy())
        for seg in segment_cols:
            for value, group in cand_df.groupby(seg, dropna=False):
                if len(group) < 8:
                    continue
                metrics = metric_from_arrays(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy())
                rows.append(
                    {
                        "scope": scope,
                        "split": split,
                        "candidate": candidate,
                        "segment_col": seg,
                        "segment_value": str(value),
                        **metrics,
                        "delta_MdAPE_vs_candidate_overall": metrics["MdAPE"] - overall["MdAPE"],
                        "delta_MAPE_vs_candidate_overall": metrics["MAPE"] - overall["MAPE"],
                        "delta_p95_APE_vs_candidate_overall": metrics["p95_APE"] - overall["p95_APE"],
                        "median_residual_log": float(np.median(group["actual_log"] - group["pred_log"])),
                        "over_50pct_error_rate": float(np.mean(group["ape"] > 0.50)),
                    }
                )
    return pd.DataFrame(rows).sort_values(["scope", "candidate", "delta_p95_APE_vs_candidate_overall"], ascending=[True, True, False])


def write_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    repeated: pd.DataFrame,
    residuals: pd.DataFrame,
    coeffs: pd.DataFrame,
    policy_basis: pd.DataFrame,
    source_basis: pd.DataFrame,
) -> None:
    base = selected[selected["candidate"].eq(BASELINE)].iloc[0]
    accepted = selected[selected["decision"].isin(["반복 검증 통과 후보", "반복 any2 검증 후보", "fixed 확인 후보"])].copy()
    best_line = "새 운영 후보 채택 없음."
    if not accepted.empty:
        best = accepted.iloc[0]
        best_line = (
            f"상위 확인 후보: `{best['candidate']}` "
            f"(판단: {best['decision']}, fixed test `{best['test_MdAPE']:.4f}/{best['test_MAPE']:.4f}/{best['test_p95_APE']:.4f}`, "
            f"repeated min any2 `{best.get('repeated_min_any2_improve_prob', np.nan):.4f}`, "
            f"min all3 `{best.get('repeated_min_all3_improve_prob', np.nan):.4f}`)."
        )

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
        "repeated_min_any2_improve_prob",
        "repeated_min_all3_improve_prob",
        "fixed_test_p95_guard",
        "stress0604_p95_guard",
        "test_mean_move_weight",
    ]
    metric_cols = ["scope", "candidate", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_MdAPE_vs_stable", "delta_MAPE_vs_stable", "delta_p95_APE_vs_stable", "mean_move_weight"]
    repeat_cols = [
        "source_scope",
        "validation_scheme",
        "candidate",
        "mean_delta_MdAPE_vs_stable",
        "mean_delta_MAPE_vs_stable",
        "mean_delta_p95_APE_vs_stable",
        "MdAPE_improve_prob",
        "MAPE_improve_prob",
        "p95_improve_prob",
        "any2_improve_prob",
        "all3_improve_prob",
    ]
    top_repeat = repeated[repeat_cols].sort_values(["any2_improve_prob", "all3_improve_prob"], ascending=False).head(80) if not repeated.empty else repeated
    md = "\n".join(
        [
            f"# {EXP_ID} Warm Huber p95 risk-aware shrinkage 실험",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 목적: HCOEF26/27 후보 이동분을 그대로 쓰지 않고, Huber로 예측한 큰 오차 위험도에 따라 이동폭을 줄여 p95와 반복 안정성을 개선할 수 있는지 확인.",
            "- 후보 선택: validation OOF 기반 risk Huber와 반복 split/artist holdout 기준.",
            "- fixed test와 0604는 확인용으로만 사용.",
            "",
            "## 1. 실행 결론",
            "",
            f"- {best_line}",
            f"- 현재 기준 후보 `hcoef_stable` fixed test: `{base['test_MdAPE']:.4f}/{base['test_MAPE']:.4f}/{base['test_p95_APE']:.4f}`.",
            "- repeated all3/any2 gate를 통과하지 못하면 운영 후보가 아니라 연구 후보로만 유지.",
            "",
            "## 2. 보정 공식",
            "",
            "- 위험도 학습식: `risk = HuberRegressor(risk_features, abs(actual_log - hcoef_stable_log))`.",
            "- 위험도 정규화: validation row OOF risk의 q10~q90 구간을 0~1로 변환.",
            "- 적용식: `corrected_log = hcoef_stable_log + weight * (source_candidate_log - hcoef_stable_log)`.",
            "- 기본 weight: `floor + (1 - floor) * (1 - alpha * risk_norm)`.",
            "- high-risk guard: risk가 validation q80/q90 이상이면 weight를 0 또는 0.25 이하로 제한.",
            "- low-risk boost: risk가 validation q33 이하이면 일부 후보에서 weight를 25%만큼 키움.",
            "",
            "## 3. 사용한 source 후보",
            "",
            h24.md_table(source_basis, max_rows=20),
            "",
            "## 4. 최종 선택표",
            "",
            h24.md_table(selected[selected_cols].round(4), max_rows=60),
            "",
            "## 5. Scope별 metrics",
            "",
            h24.md_table(metrics[metric_cols].round(4), max_rows=120),
            "",
            "## 6. 반복 split/artist holdout 요약",
            "",
            h24.md_table(top_repeat.round(4), max_rows=80),
            "",
            "## 7. Huber risk 계수 해석",
            "",
            h24.md_table(coeffs.round(6), max_rows=80),
            "",
            "## 8. 정책 후보 설정",
            "",
            h24.md_table(policy_basis.head(80), max_rows=80),
            "",
            "## 9. 잔차/큰 오차 구간",
            "",
            h24.md_table(residuals.round(4), max_rows=100),
            "",
            "## 10. 다음 방향",
            "",
            "- risk Huber shrinkage가 repeated gate를 통과하면 HCOEF29에서 후보를 축소해 재검증.",
            "- 통과하지 못하면 점 예측 이동보다 가격 범위/신뢰도 정책 또는 독립 피처 신호 추가가 우선.",
            "",
            "## 11. 산출물",
            "",
            "- `outputs/metrics.csv`",
            "- `outputs/candidate_predictions.csv`",
            "- `outputs/feature_coefficients.csv`",
            "- `outputs/repeated_iteration_metrics.csv`",
            "- `outputs/bootstrap_or_repeated_split_summary.csv`",
            "- `outputs/residual_analysis.csv`",
            "- `outputs/selected_candidates.csv`",
            "- `outputs/policy_configurations.csv`",
            "- `outputs/risk_model_thresholds.csv`",
            "- `artifacts/experiment_config.json`",
        ]
    )
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(h24.md_to_html(md), encoding="utf-8")
    (DOC_ROOT / "pp_hcoef28_warm_huber_price_basis_coefficient_refinement_summary.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / "pp_hcoef28_warm_huber_price_basis_coefficient_refinement_summary.html").write_text(h24.md_to_html(md), encoding="utf-8")


def write_config(sources: list[str], configs: list[PolicyConfig]) -> None:
    payload = {
        "experiment_id": EXP_ID,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": "PP-HCOEF27",
        "baseline": BASELINE,
        "reference": REFERENCE,
        "sources": sources,
        "policy_count": len(configs),
        "risk_features": RISK_FEATURES,
        "risk_model": "HuberRegressor on validation OOF abs residual of hcoef_stable",
        "n_repeats": N_REPEATS,
        "row_fraction": ROW_FRACTION,
        "artist_fraction": ARTIST_FRACTION,
        "selection_rule": "validation OOF/repeated split first; fixed test and 0604 confirmation only",
    }
    (EXP_DIR / "artifacts" / "experiment_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    sources, source_basis = select_sources()
    if not sources:
        raise RuntimeError("No HCOEF27 source candidates found.")
    stable, existing = load_base_predictions(sources)
    stable, risk_coefficients = attach_risk_predictions(stable)
    configs = build_policy_configs(sources, source_basis)
    predictions, policy_basis = generate_candidates(stable, existing, configs)
    metrics = point_metrics(predictions)
    detail, repeated = repeated_validation(predictions)
    selected = selected_table(metrics, repeated, source_basis)
    residuals = residual_analysis(predictions, selected)

    policy_basis.to_csv(EXP_DIR / "outputs" / "policy_configurations.csv", index=False)
    metrics.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "candidate_predictions.csv", index=False)
    risk_coefficients.to_csv(EXP_DIR / "outputs" / "feature_coefficients.csv", index=False)
    detail.to_csv(EXP_DIR / "outputs" / "repeated_iteration_metrics.csv", index=False)
    repeated.to_csv(EXP_DIR / "outputs" / "bootstrap_or_repeated_split_summary.csv", index=False)
    residuals.to_csv(EXP_DIR / "outputs" / "residual_analysis.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_candidates.csv", index=False)
    source_basis.to_csv(EXP_DIR / "outputs" / "source_candidate_basis.csv", index=False)
    write_config(sources, configs)
    write_report(metrics, selected, repeated, residuals, risk_coefficients, policy_basis, source_basis)

    print(f"{EXP_ID} complete")
    print(EXP_DIR / "reports" / "result_report.md")


if __name__ == "__main__":
    main()
