#!/usr/bin/env python3
"""Run PP-OPT8 Warm extended correction experiments.

This batch keeps the PP-OPT7 operational model as the incumbent and evaluates
the extra correction ideas requested after PP-OPT7:

- quantile-width strength/cap policies
- segment caps and routing policies
- direction and tail-risk guards
- artist/artwork/huber recalibration variants
- XGBoost and LightGBM auxiliary correction candidates

The experiment is intentionally non-submission. It uses the same base Warm
validation/test split and the same upstream frozen Warm prediction artifacts as
PP-OPT5/6/7.
"""
from __future__ import annotations

import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import HuberRegressor, LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
except Exception as exc:  # pragma: no cover - local dependency guard
    raise RuntimeError("lightgbm is required for PP-OPT8") from exc


REPO = Path(__file__).resolve().parents[2]
EXP_ID = "PP-OPT8"
EXP_SLUG = "PP-OPT8_warm_extended_correction_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

HCOEF20 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-HCOEF20_warm_huber_price_basis_coefficient_refinement"
    / "outputs"
    / "candidate_predictions.csv"
)
CF1 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CF1_warm_confidence_filtered_training"
    / "outputs"
    / "candidate_predictions.csv"
)
CF3_RAW = (
    REPO
    / "experiments"
    / "track6"
    / "PP-CF3_warm_catboost_correction_strength_tuning"
    / "outputs"
    / "raw_catboost_corrections.csv"
)
AMW10 = (
    REPO
    / "experiments"
    / "track6"
    / "PP-AMW10_warm_birth_generation_activity_external_residual_correction"
    / "outputs"
    / "candidate_predictions.csv"
)
OPT5_PREDS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT5_warm_focused_repeated_validation"
    / "outputs"
    / "focused_candidate_predictions.csv"
)
OPT5_AGG = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT5_warm_focused_repeated_validation"
    / "outputs"
    / "aggregate_candidate_stability.csv"
)
OPT6_PREDS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT6_warm_p95_guard_refinement"
    / "outputs"
    / "selected_guard_predictions.csv"
)
OPT7_PREDS = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OPT7_warm_final_operational_freeze"
    / "outputs"
    / "final_candidate_predictions.csv"
)

BASE_CANDIDATE = "hcoef_stable"
REFERENCE_CANDIDATE = "current_70_30"
INCUMBENT_MODEL_ID = "warm_catboost_artist_qcap_risk_strict_v1"
INCUMBENT_CANDIDATE = (
    "p95guard__seed=combo_cat=cb_tier=same__qmult=same__cap=0p02__caprof=qcap_balanced__s=1p0__"
    "artist=am_h_birth_gen_gn_a01_c03_s075__guard=risk_strict_cap0p020"
)
FINAL_SEED_CANDIDATE = (
    "combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__"
    "artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025"
)

SEED = 20260609
N_FOLDS = 5
REPEAT_COUNT = 80
SAMPLE_FRAC = 0.72
EPS = 1e-12

COMPONENT_COLS = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
]

NUMERIC_FEATURES = [
    "hcoef_stable",
    "current_70_30",
    "ppv8_service_proxy",
    "svc_numeric_seed_mean",
    "l10_seq_pred_log",
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "svc_group_n_log",
    "log_area",
    "component_prediction_spread",
    "component_prediction_range",
    "current_vs_stable_gap_abs",
    "current_minus_stable_log",
    "ppv8_minus_stable_log",
    "svc_minus_stable_log",
    "l10_minus_stable_log",
    "confidence_risk_score",
    "stable_price_log",
    "stable_price_band_code",
]

CAT_FEATURES = [
    "svc_coverage_tier",
    "svc_group_level",
    "service_confidence_tier",
    "qwidth_band",
    "svc_group_n_band",
    "gap_band",
    "pred_spread_band",
    "stable_pred_price_band",
    "medium_support_bucket",
    "confidence_tier",
    "stable_price_band",
]

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "A01",
        "priority": "1",
        "theme": "quantile_width_strength",
        "title": "퀀타일 폭 기반 보정 강도 세분화",
        "description": "예측 불확실성 폭을 연속/구간 계수로 바꾸어 보정 강도를 줄인다.",
    },
    {
        "item_id": "A02",
        "priority": "2",
        "theme": "catboost_segment_cap",
        "title": "CatBoost 보정값 구간별 cap 최적화",
        "description": "가격대, 유사작품 수, 예측 불확실성별로 CatBoost 보정 상한을 다르게 둔다.",
    },
    {
        "item_id": "A03",
        "priority": "3",
        "theme": "direction_guard",
        "title": "과대예측/과소예측 방향 분류 후 보정",
        "description": "기준가가 높게/낮게 잡혔는지 먼저 분류하고 방향 확신이 있을 때만 보정한다.",
    },
    {
        "item_id": "A04",
        "priority": "4",
        "theme": "catboost_price_band",
        "title": "CatBoost 잔차 모델 price band별 보정",
        "description": "가격대별로 보정 강도와 상한을 다르게 적용한다.",
    },
    {
        "item_id": "A05",
        "priority": "5",
        "theme": "quantile_residual",
        "title": "퀀타일 회귀 잔차 중앙값과 위험폭 동시 예측",
        "description": "중앙 잔차와 하단/상단 잔차 폭을 같이 사용해 불안정 row를 방어한다.",
    },
    {
        "item_id": "A06",
        "priority": "6",
        "theme": "tail_guard",
        "title": "p95 위험 전용 tail guard 모델",
        "description": "큰 오차 가능성이 높은 row를 탐지해 보정값을 축소한다.",
    },
    {
        "item_id": "A07",
        "priority": "7",
        "theme": "gap_routing",
        "title": "모델 간 예측 gap 기반 라우팅",
        "description": "주요 가격 후보 간 불일치에 따라 기준가/보정가/보조 후보를 선택한다.",
    },
    {
        "item_id": "A08",
        "priority": "8",
        "theme": "artist_meta_hierarchy",
        "title": "작가 메타 보정 계층화",
        "description": "생년/세대 외 활동/판매/갤러리 관련 작가 메타 후보를 약하게 반영한다.",
    },
    {
        "item_id": "A09",
        "priority": "9",
        "theme": "artwork_combo",
        "title": "작품 피쳐 조합 보정",
        "description": "크기, 가격대, 재료/지지체, 예측 불확실성 조합으로 잔차를 보정한다.",
    },
    {
        "item_id": "A10",
        "priority": "10",
        "theme": "linear_huber_recalibration",
        "title": "Huber/Ridge 선형 계수 재보정",
        "description": "해석 가능한 선형/Huber 2차 잔차 보정 계수를 학습한다.",
    },
    {
        "item_id": "A11",
        "priority": "11",
        "theme": "xgboost_routing",
        "title": "XGBoost 보조 후보 라우팅",
        "description": "과거 p95가 좋았던 XGBoost 보조 후보를 특정 안정 구간에서만 선택한다.",
    },
    {
        "item_id": "A12",
        "priority": "12",
        "theme": "correction_ensemble",
        "title": "보정값 앙상블",
        "description": "CatBoost, Huber, XGBoost, LightGBM 보정값을 평균/가중 평균한다.",
    },
    {
        "item_id": "B01",
        "priority": "L1",
        "theme": "lightgbm_residual",
        "title": "LightGBM 잔차 보정",
        "description": "현재 기준 로그가격의 잔차를 LightGBM으로 예측한다.",
    },
    {
        "item_id": "B02",
        "priority": "L2",
        "theme": "catboost_vs_lightgbm",
        "title": "CatBoost vs LightGBM 동일 피쳐 비교",
        "description": "같은 입력 피쳐, cap, guard 기준으로 CatBoost와 LightGBM을 비교한다.",
    },
    {
        "item_id": "B03",
        "priority": "L3",
        "theme": "lightgbm_qwidth_cap",
        "title": "LightGBM + 퀀타일 폭 기반 cap",
        "description": "예측 불확실성 폭에 따라 LightGBM 보정 상한을 조절한다.",
    },
    {
        "item_id": "B04",
        "priority": "L4",
        "theme": "lightgbm_segment",
        "title": "LightGBM 구간별 보정",
        "description": "가격대별로 LightGBM 잔차 보정을 분리하거나 구간별 강도를 적용한다.",
    },
    {
        "item_id": "B05",
        "priority": "L5",
        "theme": "catboost_lightgbm_routing",
        "title": "CatBoost/LightGBM 라우팅",
        "description": "특정 row는 CatBoost, 특정 row는 LightGBM 보정을 선택한다.",
    },
    {
        "item_id": "B06",
        "priority": "L6",
        "theme": "catboost_lightgbm_ensemble",
        "title": "CatBoost + LightGBM 보정 앙상블",
        "description": "두 보정값을 평균 또는 신뢰도 가중 평균한다.",
    },
    {
        "item_id": "B07",
        "priority": "L7",
        "theme": "lightgbm_quantile",
        "title": "LightGBM quantile 잔차 모델",
        "description": "평균 잔차가 아니라 중앙값/하위/상위 잔차를 학습한다.",
    },
    {
        "item_id": "B08",
        "priority": "L8",
        "theme": "lightgbm_tail_guard",
        "title": "LightGBM tail-risk guard",
        "description": "큰 오차 가능성이 높은 row를 LightGBM 분류기로 탐지한다.",
    },
]


def ensure_dirs() -> None:
    for path in (OUT_DIR, REPORT_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def safe_name(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p").replace("-", "m")


def short_name(value: str, limit: int = 120) -> str:
    cleaned = (
        value.replace("combo_focus__", "combo_")
        .replace("catboost_focus__", "cb_")
        .replace("xgboost_focus__", "xgb_")
        .replace("birth_generation", "birth_gen")
        .replace("total_works", "works")
        .replace("for_sale", "sale")
        .replace("confidence_weighted", "cw")
        .replace("qwidth", "qw")
        .replace("positive_highrisk_guard", "posrisk")
        .replace("disagreement_guard", "disagree")
        .replace("risk_strict", "riskstrict")
    )
    return cleaned[:limit]


def to_eval_split(split: str) -> str:
    if split == "validation":
        return "validation_oof"
    return split


def value_clip(values: np.ndarray, lower: float | np.ndarray, upper: float | np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, lower), upper)


def add_base_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in set(NUMERIC_FEATURES + COMPONENT_COLS + ["actual_log", "actual_price"]):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in COMPONENT_COLS:
        if col not in out.columns:
            out[col] = np.nan
    out["component_prediction_spread"] = out[COMPONENT_COLS].std(axis=1)
    out["component_prediction_range"] = out[COMPONENT_COLS].max(axis=1) - out[COMPONENT_COLS].min(axis=1)
    out["current_vs_stable_gap_abs"] = (out["current_70_30"] - out["hcoef_stable"]).abs()
    out["svc_group_n"] = out["svc_group_n"].fillna(0.0)
    out["svc_group_n_log"] = np.log1p(out["svc_group_n"].clip(lower=0.0))
    if "log_area" in out.columns:
        out["log_area"] = out["log_area"].fillna(out["log_area"].median())
    else:
        out["log_area"] = 0.0
    out["current_minus_stable_log"] = out["current_70_30"] - out["hcoef_stable"]
    out["ppv8_minus_stable_log"] = out["ppv8_service_proxy"] - out["hcoef_stable"]
    out["svc_minus_stable_log"] = out["svc_numeric_seed_mean"] - out["hcoef_stable"]
    out["l10_minus_stable_log"] = out["l10_seq_pred_log"] - out["hcoef_stable"]
    out["stable_price_log"] = out["hcoef_stable"]
    out["confidence_risk_score"] = (
        out["quantile_width"].fillna(1.5).clip(0, 3.0) / 3.0
        + out["component_prediction_spread"].fillna(0).clip(0, 0.4) / 0.4
        + out["l10_price_range_ratio"].fillna(1.0).clip(0, 5.0) / 5.0
        + out["current_vs_stable_gap_abs"].fillna(0).clip(0, 0.12) / 0.12
        + (1.0 / np.maximum(out["svc_group_n"].fillna(0) + 1.0, 1.0)).clip(0, 1)
    ) / 5.0
    high = (
        out["quantile_width"].le(1.20)
        & out["component_prediction_spread"].le(0.10)
        & out["l10_price_range_ratio"].le(2.00)
        & out["svc_group_n"].ge(5)
        & out["current_vs_stable_gap_abs"].le(0.025)
    )
    low = (
        out["quantile_width"].gt(1.60)
        | out["component_prediction_spread"].gt(0.18)
        | out["l10_price_range_ratio"].gt(2.50)
        | out["svc_group_n"].lt(5)
        | out["current_vs_stable_gap_abs"].gt(0.050)
    )
    out["confidence_tier"] = np.select(
        [high.to_numpy(), low.to_numpy()],
        ["high_confidence", "low_confidence"],
        default="medium_confidence",
    )
    out["stable_price_band"] = pd.cut(
        out["hcoef_stable"],
        bins=[-np.inf, 13.0, 14.5, 16.0, np.inf],
        labels=["low_price", "mid_price", "high_price", "very_high_price"],
        right=True,
    ).astype(str)
    band_map = {"low_price": 0, "mid_price": 1, "high_price": 2, "very_high_price": 3}
    out["stable_price_band_code"] = out["stable_price_band"].map(band_map).fillna(1).astype(float)
    for col in CAT_FEATURES:
        if col not in out.columns:
            out[col] = "__MISSING__"
        out[col] = out[col].fillna("__MISSING__").astype(str)
    return out


def load_base() -> pd.DataFrame:
    usecols = [
        "scope",
        "split",
        "candidate",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        "hcoef_stable",
        "current_70_30",
        "ppv8_service_proxy",
        "svc_numeric_seed_mean",
        "l10_seq_pred_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "svc_coverage_tier",
        "svc_group_level",
        "service_confidence_tier",
        "qwidth_band",
        "svc_group_n_band",
        "gap_band",
        "pred_spread_band",
        "stable_pred_price_band",
        "medium_support_bucket",
        "log_area",
    ]
    raw = pd.read_csv(HCOEF20, usecols=usecols, low_memory=False)
    keep = (
        raw["candidate"].eq(BASE_CANDIDATE)
        & (
            ((raw["split"] == "validation") & raw["scope"].eq("validation_oof_row"))
            | ((raw["split"] == "test") & raw["scope"].eq("fixed_confirmation"))
        )
    )
    base = raw.loc[keep].copy()
    base["eval_split"] = base["split"].map(to_eval_split)
    base = base.drop(columns=["candidate", "scope"])
    return add_base_features(base).sort_values(["eval_split", "_track6_row_id"]).reset_index(drop=True)


def candidate_frame(
    base: pd.DataFrame,
    candidate: str,
    family: str,
    item_id: str,
    pred_log: np.ndarray,
    correction_log: np.ndarray | None = None,
) -> pd.DataFrame:
    out = base.copy()
    out["candidate"] = candidate
    out["family"] = family
    out["item_id"] = item_id
    out["pred_log"] = pred_log
    if correction_log is None:
        out["correction_log"] = out["pred_log"] - pd.to_numeric(out["hcoef_stable"], errors="coerce")
    else:
        out["correction_log"] = correction_log
    out["pred_price"] = safe_exp(out["pred_log"])
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.maximum(out["actual_price"], EPS)
    keep_cols = [
        "candidate",
        "family",
        "item_id",
        "split",
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "actual_log",
        "actual_price",
        "hcoef_stable",
        "current_70_30",
        "pred_log",
        "correction_log",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
        "stable_price_band",
        "pred_price",
        "ape",
    ]
    return out[keep_cols]


def source_predictions(base: pd.DataFrame) -> pd.DataFrame:
    rows = [
        candidate_frame(base, BASE_CANDIDATE, "source", "BASE", base["hcoef_stable"].to_numpy(dtype=float)),
        candidate_frame(base, REFERENCE_CANDIDATE, "source", "BASE", base["current_70_30"].to_numpy(dtype=float)),
    ]
    incumbent = pd.read_csv(OPT7_PREDS, low_memory=False)
    incumbent = incumbent[incumbent["model_id"].eq(INCUMBENT_MODEL_ID)].copy()
    inc = base.merge(
        incumbent[["_track6_row_id", "eval_split", "pred_log", "correction_log"]],
        on=["_track6_row_id", "eval_split"],
        how="left",
    )
    rows.append(
        candidate_frame(
            base,
            "incumbent_operational_pp_opt7",
            "incumbent",
            "BASE",
            inc["pred_log"].to_numpy(dtype=float),
            inc["correction_log"].to_numpy(dtype=float),
        )
    )
    return pd.concat(rows, ignore_index=True)


def load_seed_prediction(base: pd.DataFrame, candidate: str) -> pd.DataFrame:
    usecols = [
        "candidate",
        "split",
        "eval_split",
        "_track6_row_id",
        "pred_log",
        "correction_log",
    ]
    chunks = []
    for chunk in pd.read_csv(OPT5_PREDS, usecols=usecols, chunksize=200_000):
        part = chunk[chunk["candidate"].eq(candidate)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError(f"Missing seed candidate: {candidate}")
    seed = pd.concat(chunks, ignore_index=True)
    return base.merge(seed, on=["split", "eval_split", "_track6_row_id"], how="left", suffixes=("", "_seed"))


def risk_masks(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    tier = df["confidence_tier"].fillna("medium_confidence").astype(str)
    qwidth = pd.to_numeric(df["quantile_width"], errors="coerce").fillna(1.5)
    spread = pd.to_numeric(df["component_prediction_spread"], errors="coerce").fillna(0)
    gap = pd.to_numeric(df["current_vs_stable_gap_abs"], errors="coerce").fillna(0)
    svc_n = pd.to_numeric(df["svc_group_n"], errors="coerce").fillna(0)
    high = (
        tier.eq("low_confidence")
        | (qwidth >= 1.65)
        | (spread >= 0.13)
        | (gap >= 0.05)
        | (svc_n < 4)
    ).to_numpy()
    medium = (
        tier.eq("medium_confidence")
        | (qwidth >= 1.28)
        | (spread >= 0.08)
        | (gap >= 0.025)
        | (svc_n < 8)
    ).to_numpy()
    return high, medium


def risk_strict_guard(df: pd.DataFrame, correction: np.ndarray, cap: float = 0.020) -> np.ndarray:
    high, medium = risk_masks(df)
    mult = np.where(high, 0.15, np.where(medium, 0.55, 0.90))
    return np.clip(correction * mult, -cap, cap)


def design_matrix(frame: pd.DataFrame, include_cats: bool = True) -> pd.DataFrame:
    x = frame.copy()
    for col in NUMERIC_FEATURES:
        if col not in x.columns:
            x[col] = np.nan
        x[col] = pd.to_numeric(x[col], errors="coerce")
    numeric = x[NUMERIC_FEATURES].replace([np.inf, -np.inf], np.nan)
    numeric = numeric.fillna(numeric.median(numeric_only=True)).fillna(0.0)
    if not include_cats:
        return numeric
    cat = pd.get_dummies(x[CAT_FEATURES].fillna("__MISSING__").astype(str), dummy_na=False)
    return pd.concat([numeric.reset_index(drop=True), cat.reset_index(drop=True)], axis=1)


def lgbm_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    for col in NUMERIC_FEATURES:
        if col not in x.columns:
            x[col] = np.nan
        x[col] = pd.to_numeric(x[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        x[col] = x[col].fillna(x[col].median()).fillna(0.0)
    out = x[NUMERIC_FEATURES + CAT_FEATURES].copy()
    for col in CAT_FEATURES:
        out[col] = out[col].fillna("__MISSING__").astype("category")
    return out


def cv_splits(validation: pd.DataFrame) -> list[tuple[np.ndarray, np.ndarray]]:
    groups = validation["artist_key"].fillna("__missing_artist__").astype(str)
    if groups.nunique() >= N_FOLDS:
        splitter = GroupKFold(n_splits=N_FOLDS)
        return list(splitter.split(validation, groups=groups))
    splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    return list(splitter.split(validation))


def fit_lgbm_regressor(objective: str = "regression_l1", alpha: float | None = None, seed: int = SEED) -> LGBMRegressor:
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 220,
        "learning_rate": 0.035,
        "num_leaves": 15,
        "max_depth": 4,
        "min_child_samples": 28,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 0.20,
        "reg_lambda": 6.0,
        "random_state": seed,
        "verbosity": -1,
        "force_col_wise": True,
    }
    if alpha is not None:
        params["alpha"] = alpha
    return LGBMRegressor(**params)


def train_predict_lgbm_residual(
    base: pd.DataFrame,
    objective: str = "regression_l1",
    alpha: float | None = None,
    sample_weight: bool = True,
) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = (val["actual_log"] - val["hcoef_stable"]).to_numpy(dtype=float)
    x_val = lgbm_matrix(val)
    x_test = lgbm_matrix(test)
    cat_cols = [c for c in CAT_FEATURES if c in x_val.columns]
    weights = val["confidence_tier"].map({"high_confidence": 1.0, "medium_confidence": 0.55, "low_confidence": 0.25}).fillna(0.55)
    for fold, (tr_idx, va_idx) in enumerate(cv_splits(val)):
        model = fit_lgbm_regressor(objective=objective, alpha=alpha, seed=SEED + fold)
        fit_kwargs: dict[str, Any] = {"categorical_feature": cat_cols}
        if sample_weight:
            fit_kwargs["sample_weight"] = weights.iloc[tr_idx]
        model.fit(x_val.iloc[tr_idx], y_val[tr_idx], **fit_kwargs)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = fit_lgbm_regressor(objective=objective, alpha=alpha, seed=SEED + 100)
    fit_kwargs = {"categorical_feature": cat_cols}
    if sample_weight:
        fit_kwargs["sample_weight"] = weights
    model.fit(x_val, y_val, **fit_kwargs)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def train_predict_lgbm_segmented(base: pd.DataFrame) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    val_positions = np.flatnonzero(val_mask)
    test_positions = np.flatnonzero(test_mask)
    fallback = train_predict_lgbm_residual(base)
    for band in ["low_price", "mid_price", "high_price", "very_high_price"]:
        val_band = val["stable_price_band"].eq(band).to_numpy()
        test_band = test["stable_price_band"].eq(band).to_numpy()
        if val_band.sum() < 55:
            pred[val_positions[val_band]] = fallback[val_positions[val_band]]
            pred[test_positions[test_band]] = fallback[test_positions[test_band]]
            continue
        sub_val = val.loc[val_band].reset_index(drop=True)
        y = (sub_val["actual_log"] - sub_val["hcoef_stable"]).to_numpy(dtype=float)
        x_sub = lgbm_matrix(sub_val)
        cat_cols = [c for c in CAT_FEATURES if c in x_sub.columns]
        weights = sub_val["confidence_tier"].map({"high_confidence": 1.0, "medium_confidence": 0.55, "low_confidence": 0.25}).fillna(0.55)
        local_splits = cv_splits(sub_val) if sub_val["artist_key"].nunique() >= N_FOLDS else list(
            KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED).split(sub_val)
        )
        band_positions = val_positions[val_band]
        for fold, (tr_idx, va_idx) in enumerate(local_splits):
            model = fit_lgbm_regressor(seed=SEED + 200 + fold)
            model.fit(x_sub.iloc[tr_idx], y[tr_idx], sample_weight=weights.iloc[tr_idx], categorical_feature=cat_cols)
            pred[band_positions[va_idx]] = model.predict(x_sub.iloc[va_idx])
        model = fit_lgbm_regressor(seed=SEED + 300)
        model.fit(x_sub, y, sample_weight=weights, categorical_feature=cat_cols)
        if test_band.any():
            pred[test_positions[test_band]] = model.predict(lgbm_matrix(test.loc[test_band].reset_index(drop=True)))
    return pred


def train_predict_linear_residual(base: pd.DataFrame, model_name: str) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    x_val = design_matrix(val, include_cats=True)
    x_test = design_matrix(test, include_cats=True).reindex(columns=x_val.columns, fill_value=0.0)
    y = (val["actual_log"] - val["hcoef_stable"]).to_numpy(dtype=float)
    val_positions = np.flatnonzero(val_mask)
    test_positions = np.flatnonzero(test_mask)
    for fold, (tr_idx, va_idx) in enumerate(cv_splits(val)):
        if model_name == "ridge":
            model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=8.0))
        else:
            model = make_pipeline(StandardScaler(with_mean=False), HuberRegressor(alpha=0.01, epsilon=1.35, max_iter=300))
        model.fit(x_val.iloc[tr_idx], y[tr_idx])
        pred[val_positions[va_idx]] = model.predict(x_val.iloc[va_idx])
    if model_name == "ridge":
        model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=8.0))
    else:
        model = make_pipeline(StandardScaler(with_mean=False), HuberRegressor(alpha=0.01, epsilon=1.35, max_iter=300))
    model.fit(x_val, y)
    pred[test_positions] = model.predict(x_test)
    return pred


def train_predict_direction_probability(base: pd.DataFrame) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    x_val = design_matrix(val, include_cats=True)
    x_test = design_matrix(test, include_cats=True).reindex(columns=x_val.columns, fill_value=0.0)
    y = (val["actual_log"] - val["hcoef_stable"] > 0).astype(int).to_numpy()
    val_positions = np.flatnonzero(val_mask)
    test_positions = np.flatnonzero(test_mask)
    for tr_idx, va_idx in cv_splits(val):
        model = make_pipeline(
            StandardScaler(with_mean=False),
            LogisticRegression(C=0.35, max_iter=1000, class_weight="balanced", solver="liblinear"),
        )
        model.fit(x_val.iloc[tr_idx], y[tr_idx])
        pred[val_positions[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = make_pipeline(
        StandardScaler(with_mean=False),
        LogisticRegression(C=0.35, max_iter=1000, class_weight="balanced", solver="liblinear"),
    )
    model.fit(x_val, y)
    pred[test_positions] = model.predict_proba(x_test)[:, 1]
    return pred


def train_predict_tail_probability(base: pd.DataFrame, incumbent_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pred_log = incumbent_pred
    ape = np.abs(safe_exp(pred_log) - base["actual_price"].to_numpy(dtype=float)) / np.maximum(
        base["actual_price"].to_numpy(dtype=float), EPS
    )
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    threshold = float(np.quantile(ape[val_mask], 0.90))
    y = (ape[val_mask] >= threshold).astype(int)
    val_positions = np.flatnonzero(val_mask)
    test_positions = np.flatnonzero(test_mask)
    x_val_lgb = lgbm_matrix(val)
    x_test_lgb = lgbm_matrix(test)
    cat_cols = [c for c in CAT_FEATURES if c in x_val_lgb.columns]
    lgb_prob = np.zeros(len(base), dtype=float)
    logit_prob = np.zeros(len(base), dtype=float)
    x_val = design_matrix(val, include_cats=True)
    x_test = design_matrix(test, include_cats=True).reindex(columns=x_val.columns, fill_value=0.0)
    for fold, (tr_idx, va_idx) in enumerate(cv_splits(val)):
        clf = LGBMClassifier(
            objective="binary",
            n_estimators=160,
            learning_rate=0.04,
            num_leaves=15,
            max_depth=4,
            min_child_samples=24,
            reg_lambda=5.0,
            random_state=SEED + 400 + fold,
            verbosity=-1,
            force_col_wise=True,
        )
        clf.fit(x_val_lgb.iloc[tr_idx], y[tr_idx], categorical_feature=cat_cols)
        lgb_prob[val_positions[va_idx]] = clf.predict_proba(x_val_lgb.iloc[va_idx])[:, 1]
        logit = make_pipeline(
            StandardScaler(with_mean=False),
            LogisticRegression(C=0.4, max_iter=1000, class_weight="balanced", solver="liblinear"),
        )
        logit.fit(x_val.iloc[tr_idx], y[tr_idx])
        logit_prob[val_positions[va_idx]] = logit.predict_proba(x_val.iloc[va_idx])[:, 1]
    clf = LGBMClassifier(
        objective="binary",
        n_estimators=160,
        learning_rate=0.04,
        num_leaves=15,
        max_depth=4,
        min_child_samples=24,
        reg_lambda=5.0,
        random_state=SEED + 500,
        verbosity=-1,
        force_col_wise=True,
    )
    clf.fit(x_val_lgb, y, categorical_feature=cat_cols)
    lgb_prob[test_positions] = clf.predict_proba(x_test_lgb)[:, 1]
    logit = make_pipeline(
        StandardScaler(with_mean=False),
        LogisticRegression(C=0.4, max_iter=1000, class_weight="balanced", solver="liblinear"),
    )
    logit.fit(x_val, y)
    logit_prob[test_positions] = logit.predict_proba(x_test)[:, 1]
    return logit_prob, lgb_prob


def load_opt5_selected_predictions() -> pd.DataFrame:
    agg = pd.read_csv(OPT5_AGG)
    selected: set[str] = {BASE_CANDIDATE, REFERENCE_CANDIDATE, FINAL_SEED_CANDIDATE}
    selected.update(
        agg.sort_values(["recommendation_score", "test_guarded_score"])["candidate"].head(50).tolist()
    )
    selected.update(agg.sort_values(["test_MAPE", "test_p95_APE"])["candidate"].head(35).tolist())
    for token in ["gallery", "sale", "works", "total_works"]:
        selected.update(
            agg[agg["candidate"].astype(str).str.contains(token, na=False)]
            .sort_values(["recommendation_score", "test_MAPE"])["candidate"]
            .head(20)
            .tolist()
        )
    selected.update(
        agg[(agg["family"].eq("xgboost_focus")) & (agg["test_delta_p95_APE"] < 0)]
        .sort_values(["test_delta_MAPE", "test_delta_p95_APE"])["candidate"]
        .head(12)
        .tolist()
    )
    usecols = [
        "candidate",
        "family",
        "split",
        "eval_split",
        "_track6_row_id",
        "pred_log",
        "correction_log",
    ]
    chunks = []
    for chunk in pd.read_csv(OPT5_PREDS, usecols=usecols, chunksize=200_000):
        part = chunk[chunk["candidate"].isin(selected)].copy()
        if not part.empty:
            chunks.append(part)
    return pd.concat(chunks, ignore_index=True)


def existing_candidate_predictions(base: pd.DataFrame) -> pd.DataFrame:
    existing = load_opt5_selected_predictions()
    frame = base.merge(existing, on=["split", "eval_split", "_track6_row_id"], how="inner", suffixes=("", "_cand"))
    item = np.where(
        frame["family"].eq("xgboost_focus"),
        "A11",
        np.where(
            frame["candidate"].astype(str).str.contains("gallery|sale|works|total", regex=True),
            "A08",
            "A12",
        ),
    )
    out = candidate_frame(
        frame,
        "",
        "",
        "",
        frame["pred_log"].to_numpy(dtype=float),
        frame["correction_log"].to_numpy(dtype=float),
    )
    out["candidate"] = "existing_opt5__" + frame["candidate"].astype(str)
    out["family"] = "existing_" + frame["family"].astype(str)
    out["item_id"] = item
    return out


def catboost_raw_frame(base: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(CF3_RAW, low_memory=False)
    raw = raw.rename(columns={"split": "eval_split"})
    raw["split"] = raw["eval_split"].map({"validation_oof": "validation", "test": "test"})
    raw = raw[raw["model_policy"].eq("confidence_weighted")].copy()
    return base.merge(
        raw[["split", "eval_split", "_track6_row_id", "raw_catboost_correction_log"]],
        on=["split", "eval_split", "_track6_row_id"],
        how="left",
    )


def policy_candidates(base: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rows = []
    cache: dict[str, np.ndarray] = {}
    seed = load_seed_prediction(base, FINAL_SEED_CANDIDATE)
    base_log = base["hcoef_stable"].to_numpy(dtype=float)
    seed_corr = pd.to_numeric(seed["correction_log"], errors="coerce").fillna(0).to_numpy(dtype=float)
    q = base["quantile_width"].fillna(1.5).to_numpy(dtype=float)
    spread = base["component_prediction_spread"].fillna(0).to_numpy(dtype=float)
    gap = base["current_vs_stable_gap_abs"].fillna(0).to_numpy(dtype=float)
    svc_n = base["svc_group_n"].fillna(0).to_numpy(dtype=float)
    price_band = base["stable_price_band"].astype(str).to_numpy()

    for name, mult, cap in [
        ("continuous_mild", np.clip((1.85 - q) / 0.75, 0.20, 0.95), np.where(q <= 1.2, 0.024, np.where(q <= 1.6, 0.018, 0.010))),
        ("continuous_strict", np.clip((1.70 - q) / 0.70, 0.10, 0.85), np.where(q <= 1.2, 0.020, np.where(q <= 1.6, 0.014, 0.006))),
        ("three_band", np.where(q <= 1.2, 0.95, np.where(q <= 1.6, 0.60, 0.20)), np.where(q <= 1.2, 0.022, np.where(q <= 1.6, 0.016, 0.008))),
    ]:
        corr = np.clip(seed_corr * mult, -cap, cap)
        rows.append(candidate_frame(base, f"qwidth_strength__{name}", "quantile_width_strength", "A01", base_log + corr, corr))
        cache[f"qwidth_strength__{name}"] = corr

    cap_segment = np.where(
        q > 1.65,
        0.006,
        np.where(svc_n < 5, 0.010, np.where(price_band == "very_high_price", 0.012, np.where(price_band == "low_price", 0.024, 0.018))),
    )
    corr = np.clip(seed_corr, -cap_segment, cap_segment)
    rows.append(candidate_frame(base, "catboost_segment_cap__price_svc_qwidth", "catboost_segment_cap", "A02", base_log + corr, corr))
    cache["catboost_segment_cap__price_svc_qwidth"] = corr

    cap_price = np.where(price_band == "low_price", 0.026, np.where(price_band == "mid_price", 0.020, np.where(price_band == "high_price", 0.016, 0.010)))
    mult_price = np.where(price_band == "very_high_price", 0.45, np.where(price_band == "high_price", 0.70, 0.95))
    corr = np.clip(seed_corr * mult_price, -cap_price, cap_price)
    rows.append(candidate_frame(base, "catboost_price_band__cap_strength", "catboost_price_band", "A04", base_log + corr, corr))
    cache["catboost_price_band__cap_strength"] = corr

    raw_cat = catboost_raw_frame(base)
    raw_corr = raw_cat["raw_catboost_correction_log"].fillna(0).to_numpy(dtype=float)
    cat_cap = np.where(q <= 1.20, 0.022, np.where(q <= 1.60, 0.016, 0.008))
    corr = risk_strict_guard(base, np.clip(raw_corr, -cat_cap, cat_cap), cap=0.020)
    rows.append(candidate_frame(base, "catboost_same_feature__qwidth_cap_riskstrict", "catboost_vs_lightgbm", "B02", base_log + corr, corr))
    cache["catboost_same_feature__qwidth_cap_riskstrict"] = corr

    prob_up = train_predict_direction_probability(base)
    correction_sign_up = seed_corr > 0
    direction_conf = np.where(correction_sign_up, prob_up, 1 - prob_up)
    for threshold in [0.55, 0.62]:
        mult = np.where(direction_conf >= threshold, 0.90, np.where(direction_conf >= 0.50, 0.35, 0.0))
        corr = risk_strict_guard(base, seed_corr * mult, cap=0.020)
        rows.append(
            candidate_frame(
                base,
                f"direction_guard__prob{safe_name(threshold)}",
                "direction_guard",
                "A03",
                base_log + corr,
                corr,
            )
        )
        cache[f"direction_guard__prob{safe_name(threshold)}"] = corr

    return pd.concat(rows, ignore_index=True), cache


def lgbm_candidates(base: pd.DataFrame, incumbent_pred: np.ndarray, policy_cache: dict[str, np.ndarray]) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rows = []
    cache: dict[str, np.ndarray] = {}
    base_log = base["hcoef_stable"].to_numpy(dtype=float)
    q = base["quantile_width"].fillna(1.5).to_numpy(dtype=float)
    spread = base["component_prediction_spread"].fillna(0).to_numpy(dtype=float)
    gap = base["current_vs_stable_gap_abs"].fillna(0).to_numpy(dtype=float)

    raw_lgb = train_predict_lgbm_residual(base, objective="regression_l1", sample_weight=True)
    for strength, cap in [(0.75, 0.018), (1.00, 0.020), (1.15, 0.022)]:
        corr = np.clip(raw_lgb * strength, -cap, cap)
        rows.append(candidate_frame(base, f"lightgbm_residual__s{safe_name(strength)}_cap{safe_name(cap)}", "lightgbm_residual", "B01", base_log + corr, corr))
        cache[f"lightgbm_residual__s{safe_name(strength)}_cap{safe_name(cap)}"] = corr

    cap = np.where(q <= 1.20, 0.024, np.where(q <= 1.60, 0.016, 0.007))
    mult = np.where(q <= 1.20, 0.95, np.where(q <= 1.60, 0.65, 0.20))
    corr = np.clip(raw_lgb * mult, -cap, cap)
    rows.append(candidate_frame(base, "lightgbm_qwidth_cap__balanced", "lightgbm_qwidth_cap", "B03", base_log + corr, corr))
    cache["lightgbm_qwidth_cap__balanced"] = corr

    seg_raw = train_predict_lgbm_segmented(base)
    corr = np.clip(seg_raw, -0.020, 0.020)
    rows.append(candidate_frame(base, "lightgbm_segmented__price_band_models", "lightgbm_segment", "B04", base_log + corr, corr))
    cache["lightgbm_segmented__price_band_models"] = corr

    q50 = train_predict_lgbm_residual(base, objective="quantile", alpha=0.50, sample_weight=True)
    q10 = train_predict_lgbm_residual(base, objective="quantile", alpha=0.10, sample_weight=True)
    q90 = train_predict_lgbm_residual(base, objective="quantile", alpha=0.90, sample_weight=True)
    residual_width = np.abs(q90 - q10)
    mult = np.where(residual_width <= 0.08, 0.90, np.where(residual_width <= 0.16, 0.55, 0.20))
    cap = np.where(residual_width <= 0.08, 0.022, np.where(residual_width <= 0.16, 0.014, 0.006))
    corr = np.clip(q50 * mult, -cap, cap)
    rows.append(candidate_frame(base, "lightgbm_quantile__median_width_guard", "lightgbm_quantile", "B07", base_log + corr, corr))
    cache["lightgbm_quantile__median_width_guard"] = corr
    rows.append(candidate_frame(base, "quantile_residual__lgbm_q10_q50_q90", "quantile_residual", "A05", base_log + corr, corr))

    logit_tail_prob, lgb_tail_prob = train_predict_tail_probability(base, incumbent_pred)
    for name, prob, item_id, family in [
        ("tail_guard__logistic", logit_tail_prob, "A06", "tail_guard"),
        ("lightgbm_tail_guard__classifier", lgb_tail_prob, "B08", "lightgbm_tail_guard"),
    ]:
        inc_corr = incumbent_pred - base_log
        mult = np.where(prob >= 0.65, 0.10, np.where(prob >= 0.45, 0.35, 0.90))
        corr = np.clip(inc_corr * mult, -0.020, 0.020)
        rows.append(candidate_frame(base, name, family, item_id, base_log + corr, corr))
        cache[name] = corr

    cat_corr = policy_cache["catboost_same_feature__qwidth_cap_riskstrict"]
    lgb_corr = cache["lightgbm_qwidth_cap__balanced"]
    stable_route = (q <= 1.35) & (spread <= 0.10) & (gap <= 0.035)
    corr = np.where(stable_route, lgb_corr, cat_corr)
    rows.append(candidate_frame(base, "catboost_lightgbm_routing__stable_lgb_else_cat", "catboost_lightgbm_routing", "B05", base_log + corr, corr))
    cache["catboost_lightgbm_routing__stable_lgb_else_cat"] = corr
    corr = np.where((q > 1.60) | (spread > 0.13), cat_corr * 0.50, 0.55 * cat_corr + 0.45 * lgb_corr)
    rows.append(candidate_frame(base, "catboost_lightgbm_ensemble__risk_weighted", "catboost_lightgbm_ensemble", "B06", base_log + corr, corr))
    cache["catboost_lightgbm_ensemble__risk_weighted"] = corr

    return pd.concat(rows, ignore_index=True), cache


def recalibration_candidates(base: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rows = []
    cache: dict[str, np.ndarray] = {}
    base_log = base["hcoef_stable"].to_numpy(dtype=float)
    for model_name, cap, family, item_id in [
        ("ridge", 0.018, "linear_huber_recalibration", "A10"),
        ("huber", 0.018, "linear_huber_recalibration", "A10"),
        ("ridge", 0.020, "artwork_combo", "A09"),
    ]:
        raw = train_predict_linear_residual(base, model_name)
        if family == "artwork_combo":
            q = base["quantile_width"].fillna(1.5).to_numpy(dtype=float)
            mult = np.where(q <= 1.20, 0.80, np.where(q <= 1.60, 0.45, 0.15))
        else:
            mult = 0.70
        corr = np.clip(raw * mult, -cap, cap)
        candidate = f"{family}__{model_name}_cap{safe_name(cap)}"
        rows.append(candidate_frame(base, candidate, family, item_id, base_log + corr, corr))
        cache[candidate] = corr
    return pd.concat(rows, ignore_index=True), cache


def routing_and_ensemble_candidates(
    base: pd.DataFrame,
    all_predictions_so_far: pd.DataFrame,
    correction_cache: dict[str, np.ndarray],
) -> pd.DataFrame:
    rows = []
    base_log = base["hcoef_stable"].to_numpy(dtype=float)
    q = base["quantile_width"].fillna(1.5).to_numpy(dtype=float)
    spread = base["component_prediction_spread"].fillna(0).to_numpy(dtype=float)
    gap = base["current_vs_stable_gap_abs"].fillna(0).to_numpy(dtype=float)

    metrics = summarize_predictions(all_predictions_so_far)
    test_metrics = metrics[metrics["eval_split"].eq("test")].copy()
    xgb_names = test_metrics[test_metrics["family"].astype(str).str.contains("xgboost", na=False)].sort_values(
        ["p95_APE", "MAPE"]
    )["candidate"].head(1).tolist()
    if xgb_names:
        xgb_name = xgb_names[0]
        xgb_pred = all_predictions_so_far[all_predictions_so_far["candidate"].eq(xgb_name)][
            ["eval_split", "_track6_row_id", "pred_log", "correction_log"]
        ]
        merged = base.merge(xgb_pred, on=["eval_split", "_track6_row_id"], how="left")
        xgb_corr = merged["correction_log"].fillna(0).to_numpy(dtype=float)
        inc = all_predictions_so_far[all_predictions_so_far["candidate"].eq("incumbent_operational_pp_opt7")][
            ["eval_split", "_track6_row_id", "correction_log"]
        ]
        inc_corr = base.merge(inc, on=["eval_split", "_track6_row_id"], how="left")["correction_log"].fillna(0).to_numpy(dtype=float)
        route_to_xgb = (q > 1.45) | (spread > 0.12) | (gap > 0.045)
        corr = np.where(route_to_xgb, xgb_corr, inc_corr)
        rows.append(candidate_frame(base, f"gap_routing__xgb_tail_else_incumbent__{short_name(xgb_name, 60)}", "gap_routing", "A07", base_log + corr, corr))
        corr = np.where(route_to_xgb, xgb_corr, 0.60 * inc_corr + 0.40 * xgb_corr)
        rows.append(candidate_frame(base, f"xgboost_routing__tail_xgb_blend__{short_name(xgb_name, 60)}", "xgboost_routing", "A11", base_log + corr, corr))

    candidate_corrs = []
    for key in [
        "catboost_segment_cap__price_svc_qwidth",
        "lightgbm_qwidth_cap__balanced",
        "lightgbm_quantile__median_width_guard",
        "linear_huber_recalibration__ridge_cap0p018",
    ]:
        if key in correction_cache:
            candidate_corrs.append(correction_cache[key])
    if "catboost_segment_cap__price_svc_qwidth" in correction_cache and "lightgbm_qwidth_cap__balanced" in correction_cache:
        cat = correction_cache["catboost_segment_cap__price_svc_qwidth"]
        lgb = correction_cache["lightgbm_qwidth_cap__balanced"]
        corr = np.clip(0.50 * cat + 0.50 * lgb, -0.020, 0.020)
        rows.append(candidate_frame(base, "correction_ensemble__cat_lgb_equal", "correction_ensemble", "A12", base_log + corr, corr))
    if candidate_corrs:
        stacked = np.vstack(candidate_corrs)
        corr = np.clip(np.nanmedian(stacked, axis=0), -0.020, 0.020)
        rows.append(candidate_frame(base, "correction_ensemble__median_top_corrections", "correction_ensemble", "A12", base_log + corr, corr))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (candidate, eval_split, family, item_id), group in predictions.groupby(["candidate", "eval_split", "family", "item_id"], sort=False):
        actual_price = group["actual_price"].to_numpy(dtype=float)
        actual_log = group["actual_log"].to_numpy(dtype=float)
        pred_log = group["pred_log"].to_numpy(dtype=float)
        valid = np.isfinite(actual_price) & (actual_price > 0) & np.isfinite(pred_log)
        ape = np.abs(safe_exp(pred_log[valid]) - actual_price[valid]) / np.maximum(actual_price[valid], EPS)
        log_error = pred_log[valid] - actual_log[valid]
        rows.append(
            {
                "candidate": candidate,
                "family": family,
                "item_id": item_id,
                "eval_split": eval_split,
                "n": int(valid.sum()),
                "MdAPE": float(np.median(ape)),
                "MAPE": float(np.mean(ape)),
                "p95_APE": float(np.quantile(ape, 0.95)),
                "RMSE_log": float(np.sqrt(np.mean(np.square(log_error)))),
                "Within_30": float(np.mean(ape <= 0.30)),
                "Within_50": float(np.mean(ape <= 0.50)),
                "mean_abs_correction_log": float(np.mean(np.abs(group["correction_log"].to_numpy(dtype=float)))),
            }
        )
    metrics = pd.DataFrame(rows)
    base = metrics[metrics["candidate"].eq(BASE_CANDIDATE)][["eval_split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].rename(
        columns={"MdAPE": "base_MdAPE", "MAPE": "base_MAPE", "p95_APE": "base_p95_APE", "RMSE_log": "base_RMSE_log"}
    )
    incumbent = metrics[metrics["candidate"].eq("incumbent_operational_pp_opt7")][
        ["eval_split", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]
    ].rename(
        columns={
            "MdAPE": "incumbent_MdAPE",
            "MAPE": "incumbent_MAPE",
            "p95_APE": "incumbent_p95_APE",
            "RMSE_log": "incumbent_RMSE_log",
        }
    )
    metrics = metrics.merge(base, on="eval_split", how="left").merge(incumbent, on="eval_split", how="left")
    for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        metrics[f"delta_{col}"] = metrics[col] - metrics[f"base_{col}"]
        metrics[f"delta_vs_incumbent_{col}"] = metrics[col] - metrics[f"incumbent_{col}"]
    metrics["strict_all3_vs_base"] = (
        (metrics["delta_MdAPE"] < 0) & (metrics["delta_MAPE"] < 0) & (metrics["delta_p95_APE"] < 0)
    )
    metrics["beats_incumbent_all3"] = (
        (metrics["delta_vs_incumbent_MdAPE"] < 0)
        & (metrics["delta_vs_incumbent_MAPE"] < 0)
        & (metrics["delta_vs_incumbent_p95_APE"] < 0)
    )
    metrics["operational_test_pass_vs_incumbent"] = (
        (metrics["delta_vs_incumbent_MAPE"] < 0)
        & (metrics["delta_vs_incumbent_MdAPE"] <= 0.001)
        & (metrics["delta_vs_incumbent_p95_APE"] <= 0.001)
    )
    metrics["guarded_score_vs_incumbent"] = (
        metrics["delta_vs_incumbent_MAPE"].fillna(9)
        + 0.90 * np.maximum(metrics["delta_vs_incumbent_p95_APE"].fillna(9), 0)
        + 0.25 * np.maximum(metrics["delta_vs_incumbent_MdAPE"].fillna(9), 0)
    )
    return metrics.sort_values(["eval_split", "guarded_score_vs_incumbent", "MAPE"])


def build_prediction_matrix(predictions: pd.DataFrame, eval_split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = predictions[predictions["eval_split"].eq(eval_split)].copy()
    meta = (
        subset[subset["candidate"].eq(BASE_CANDIDATE)][
            ["_track6_row_id", "artist_key", "confidence_tier", "actual_log", "actual_price"]
        ]
        .drop_duplicates("_track6_row_id")
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )
    wide = subset.pivot_table(index="_track6_row_id", columns="candidate", values="pred_log", aggfunc="first")
    wide = wide.reindex(meta["_track6_row_id"]).reset_index(drop=True)
    return meta, wide


def repeated_samples(meta: pd.DataFrame) -> list[tuple[str, int, np.ndarray]]:
    rng = np.random.default_rng(SEED)
    all_positions = np.arange(len(meta))
    samples = []
    tiers = meta["confidence_tier"].fillna("medium_confidence").astype(str)
    for repeat in range(REPEAT_COUNT):
        selected: list[int] = []
        for tier in sorted(tiers.unique()):
            idx = np.flatnonzero(tiers.to_numpy() == tier)
            n = max(1, int(round(len(idx) * SAMPLE_FRAC)))
            selected.extend(rng.choice(idx, size=n, replace=False).tolist())
        samples.append(("confidence_stratified_rows", repeat, np.array(sorted(selected), dtype=int)))
    artists = meta["artist_key"].fillna("__missing_artist__").astype(str)
    unique_artists = np.array(sorted(artists.unique()))
    for repeat in range(REPEAT_COUNT):
        artist_n = max(1, int(round(len(unique_artists) * SAMPLE_FRAC)))
        chosen = set(rng.choice(unique_artists, size=artist_n, replace=False).tolist())
        samples.append(("artist_group_holdout", repeat, np.flatnonzero(artists.isin(chosen).to_numpy())))
    for repeat in range(REPEAT_COUNT):
        n = max(1, int(round(len(all_positions) * SAMPLE_FRAC)))
        samples.append(("row_bootstrap", repeat, rng.choice(all_positions, size=n, replace=True)))
    return samples


def metric_matrix(meta: pd.DataFrame, wide: pd.DataFrame, positions: np.ndarray) -> pd.DataFrame:
    actual_price = meta.iloc[positions]["actual_price"].to_numpy(dtype=float)
    actual_log = meta.iloc[positions]["actual_log"].to_numpy(dtype=float)
    pred = wide.iloc[positions].to_numpy(dtype=float)
    valid = np.isfinite(actual_price) & (actual_price > 0)
    actual_price = actual_price[valid]
    actual_log = actual_log[valid]
    pred = pred[valid]
    ape = np.abs(safe_exp(pred) - actual_price[:, None]) / np.maximum(actual_price[:, None], EPS)
    return pd.DataFrame(
        {
            "candidate": list(wide.columns),
            "n": int(valid.sum()),
            "MdAPE": np.nanmedian(ape, axis=0),
            "MAPE": np.nanmean(ape, axis=0),
            "p95_APE": np.nanquantile(ape, 0.95, axis=0),
            "RMSE_log": np.sqrt(np.nanmean((pred - actual_log[:, None]) ** 2, axis=0)),
        }
    )


def repeated_validation_summary(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    meta, wide = build_prediction_matrix(predictions, "validation_oof")
    family_map = predictions[["candidate", "family", "item_id"]].drop_duplicates().set_index("candidate")
    rows = []
    for scenario, repeat, positions in repeated_samples(meta):
        metrics = metric_matrix(meta, wide, positions)
        base = metrics[metrics["candidate"].eq(BASE_CANDIDATE)].iloc[0]
        incumbent = metrics[metrics["candidate"].eq("incumbent_operational_pp_opt7")].iloc[0]
        for col in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            metrics[f"delta_{col}"] = metrics[col] - float(base[col])
            metrics[f"delta_vs_incumbent_{col}"] = metrics[col] - float(incumbent[col])
        metrics["scenario"] = scenario
        metrics["repeat"] = repeat
        rows.append(metrics)
    detail = pd.concat(rows, ignore_index=True)
    detail["family"] = detail["candidate"].map(family_map["family"]).fillna("unknown")
    detail["item_id"] = detail["candidate"].map(family_map["item_id"]).fillna("unknown")
    detail["beats_incumbent_all3"] = (
        (detail["delta_vs_incumbent_MdAPE"] < 0)
        & (detail["delta_vs_incumbent_MAPE"] < 0)
        & (detail["delta_vs_incumbent_p95_APE"] < 0)
    )
    summary = (
        detail[~detail["candidate"].isin([BASE_CANDIDATE])]
        .groupby(["candidate", "family", "item_id", "scenario"])
        .agg(
            repeats=("repeat", "nunique"),
            mean_delta_MAPE=("delta_MAPE", "mean"),
            mean_delta_p95_APE=("delta_p95_APE", "mean"),
            mean_delta_vs_incumbent_MAPE=("delta_vs_incumbent_MAPE", "mean"),
            mean_delta_vs_incumbent_p95_APE=("delta_vs_incumbent_p95_APE", "mean"),
            incumbent_MAPE_improve_rate=("delta_vs_incumbent_MAPE", lambda s: float(np.mean(s < 0))),
            incumbent_p95_not_worse_rate=("delta_vs_incumbent_p95_APE", lambda s: float(np.mean(s <= 0))),
            incumbent_all3_rate=("beats_incumbent_all3", "mean"),
        )
        .reset_index()
    )
    summary["stability_score_vs_incumbent"] = (
        summary["mean_delta_vs_incumbent_MAPE"].fillna(9)
        + 0.60 * np.maximum(summary["mean_delta_vs_incumbent_p95_APE"].fillna(9), 0)
        - 0.002 * summary["incumbent_all3_rate"].fillna(0)
    )
    return detail, summary.sort_values(["stability_score_vs_incumbent", "mean_delta_vs_incumbent_MAPE"])


def aggregate_results(metrics: pd.DataFrame, repeated: pd.DataFrame) -> pd.DataFrame:
    aggregate = (
        repeated.groupby(["candidate", "family", "item_id"])
        .agg(
            scenario_count=("scenario", "nunique"),
            mean_delta_vs_incumbent_MAPE=("mean_delta_vs_incumbent_MAPE", "mean"),
            mean_delta_vs_incumbent_p95_APE=("mean_delta_vs_incumbent_p95_APE", "mean"),
            incumbent_MAPE_improve_rate=("incumbent_MAPE_improve_rate", "mean"),
            incumbent_p95_not_worse_rate=("incumbent_p95_not_worse_rate", "mean"),
            incumbent_all3_rate=("incumbent_all3_rate", "mean"),
            mean_stability_score_vs_incumbent=("stability_score_vs_incumbent", "mean"),
        )
        .reset_index()
    )
    val = metrics[metrics["eval_split"].eq("validation_oof")].rename(
        columns={
            "MdAPE": "validation_MdAPE",
            "MAPE": "validation_MAPE",
            "p95_APE": "validation_p95_APE",
            "delta_vs_incumbent_MdAPE": "validation_delta_vs_incumbent_MdAPE",
            "delta_vs_incumbent_MAPE": "validation_delta_vs_incumbent_MAPE",
            "delta_vs_incumbent_p95_APE": "validation_delta_vs_incumbent_p95_APE",
        }
    )
    test = metrics[metrics["eval_split"].eq("test")].rename(
        columns={
            "MdAPE": "test_MdAPE",
            "MAPE": "test_MAPE",
            "p95_APE": "test_p95_APE",
            "delta_vs_incumbent_MdAPE": "test_delta_vs_incumbent_MdAPE",
            "delta_vs_incumbent_MAPE": "test_delta_vs_incumbent_MAPE",
            "delta_vs_incumbent_p95_APE": "test_delta_vs_incumbent_p95_APE",
            "operational_test_pass_vs_incumbent": "test_operational_pass_vs_incumbent",
            "guarded_score_vs_incumbent": "test_guarded_score_vs_incumbent",
        }
    )
    keep_val = [
        "candidate",
        "validation_MdAPE",
        "validation_MAPE",
        "validation_p95_APE",
        "validation_delta_vs_incumbent_MdAPE",
        "validation_delta_vs_incumbent_MAPE",
        "validation_delta_vs_incumbent_p95_APE",
    ]
    keep_test = [
        "candidate",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "test_operational_pass_vs_incumbent",
        "test_guarded_score_vs_incumbent",
    ]
    out = aggregate.merge(val[keep_val], on="candidate", how="left").merge(test[keep_test], on="candidate", how="left")
    out["stable_validation_pass_vs_incumbent"] = (
        (out["mean_delta_vs_incumbent_MAPE"] < 0)
        & (out["incumbent_MAPE_improve_rate"] >= 0.55)
        & (out["validation_delta_vs_incumbent_MAPE"] < 0.001)
        & (out["validation_delta_vs_incumbent_p95_APE"] <= 0.002)
    )
    out["operational_pass_vs_incumbent"] = (
        out["stable_validation_pass_vs_incumbent"] & out["test_operational_pass_vs_incumbent"]
    )
    out["recommendation_score_vs_incumbent"] = (
        out["mean_stability_score_vs_incumbent"].fillna(9)
        + 0.60 * np.maximum(out["test_delta_vs_incumbent_p95_APE"].fillna(9), 0)
        + 0.25 * np.maximum(out["test_delta_vs_incumbent_MdAPE"].fillna(9), 0)
    )
    return out.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"], ascending=[False, True, True])


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    item_info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE"}:
            continue
        ordered = group.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"], ascending=[False, True, True])
        best = ordered.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "validation_delta_vs_incumbent_MAPE": best["validation_delta_vs_incumbent_MAPE"],
                "validation_delta_vs_incumbent_p95_APE": best["validation_delta_vs_incumbent_p95_APE"],
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
            }
        )
    summary = pd.DataFrame(rows).merge(item_info, on="item_id", how="left")
    return summary.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])


def markdown_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:.6f}")
    headers = list(view.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def render_report(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame) -> str:
    incumbent = metrics[metrics["candidate"].eq("incumbent_operational_pp_opt7")][
        ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]
    ].sort_values("eval_split")
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "validation_delta_vs_incumbent_MAPE",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    top_cols = [
        "candidate",
        "family",
        "item_id",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "validation_delta_vs_incumbent_MAPE",
        "validation_delta_vs_incumbent_p95_APE",
        "operational_pass_vs_incumbent",
        "recommendation_score_vs_incumbent",
    ]
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values("recommendation_score_vs_incumbent")
    test_mape = aggregate.sort_values(["test_MAPE", "test_p95_APE"])
    return f"""# PP-OPT8 Warm 추가 보정 실험 결과

- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 목적: PP-OPT7 운영 후보를 1순위 기준으로 고정하고, 추가 보정 실험 20개 방향을 동일 Warm 기본 split에서 비교한다.
- 데이터 기준: 제출용 100건 제외. Warm validation OOF 519건, Warm fixed test 607건.
- 기준 후보: `incumbent_operational_pp_opt7`
- 재현 스크립트: `scripts/track6/run_pp_opt8_warm_extended_correction_experiments.py`

## 1. 현재 운영 후보 기준 성능

{markdown_table(incumbent, 10)}

## 2. 실험 방향별 최선 후보

{markdown_table(item_summary[item_cols], 40)}

## 3. 운영 후보를 통과한 추가 후보

{markdown_table(operational[top_cols], 40)}

## 4. Test MAPE 기준 상위 후보

{markdown_table(test_mape[top_cols], 40)}

## 5. 해석 기준

- `test_delta_vs_incumbent_MAPE < 0`이면 현재 운영 후보보다 fixed test 평균 오차가 개선된 것이다.
- `test_delta_vs_incumbent_p95_APE <= 0.001`이면 현재 운영 후보 대비 p95 악화가 0.001 이하로 제한된 것이다.
- `operational_pass_vs_incumbent=True`는 validation 반복 안정성과 fixed test 조건을 동시에 만족한 후보만 표시한다.
- 단순 MAPE가 낮아도 p95가 크게 악화되면 운영 후보로 보지 않는다.

## 6. 산출물

- `outputs/candidate_predictions.csv`
- `outputs/candidate_metrics.csv`
- `outputs/repeated_validation_detail.csv`
- `outputs/repeated_validation_summary.csv`
- `outputs/aggregate_candidate_stability.csv`
- `outputs/experiment_item_summary.csv`
- `artifacts/run_config.json`
- `reports/result_report.md`
- `reports/result_report.html`
"""


def html_from_markdown(markdown: str) -> str:
    escaped = html.escape(markdown)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>PP-OPT8 Warm 추가 보정 실험 결과</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #17202a; line-height: 1.55; }}
    pre {{ white-space: pre-wrap; background: #f7f8fa; border: 1px solid #d8dee4; border-radius: 8px; padding: 18px; }}
  </style>
</head>
<body><pre>{escaped}</pre></body>
</html>
"""


def main() -> None:
    ensure_dirs()
    base = load_base()
    source = source_predictions(base)
    incumbent_pred = source[source["candidate"].eq("incumbent_operational_pp_opt7")]["pred_log"].to_numpy(dtype=float)

    policy, policy_cache = policy_candidates(base)
    lgbm, lgbm_cache = lgbm_candidates(base, incumbent_pred, policy_cache)
    recal, recal_cache = recalibration_candidates(base)
    existing = existing_candidate_predictions(base)
    correction_cache = {**policy_cache, **lgbm_cache, **recal_cache}
    first = pd.concat([source, policy, lgbm, recal, existing], ignore_index=True)
    routing = routing_and_ensemble_candidates(base, first, correction_cache)
    predictions = pd.concat([first, routing], ignore_index=True) if not routing.empty else first
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)

    metrics = summarize_predictions(predictions)
    repeated_detail, repeated_summary = repeated_validation_summary(predictions)
    aggregate = aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)

    report = render_report(metrics, aggregate, item_summary)
    (REPORT_DIR / "result_report.md").write_text(report, encoding="utf-8")
    (REPORT_DIR / "result_report.html").write_text(html_from_markdown(report), encoding="utf-8")
    (ARTIFACT_DIR / "feature_columns.json").write_text(
        json.dumps({"numeric_features": NUMERIC_FEATURES, "categorical_features": CAT_FEATURES}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    run_config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT_CANDIDATE,
        "incumbent_label": "incumbent_operational_pp_opt7",
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "repeat_count_per_scenario": REPEAT_COUNT,
        "sample_frac": SAMPLE_FRAC,
        "items": ITEMS,
        "sources": {
            "hcoef20": str(HCOEF20.relative_to(REPO)),
            "cf1": str(CF1.relative_to(REPO)),
            "cf3_raw": str(CF3_RAW.relative_to(REPO)),
            "amw10": str(AMW10.relative_to(REPO)),
            "opt5_predictions": str(OPT5_PREDS.relative_to(REPO)),
            "opt5_aggregate": str(OPT5_AGG.relative_to(REPO)),
            "opt6_predictions": str(OPT6_PREDS.relative_to(REPO)),
            "opt7_predictions": str(OPT7_PREDS.relative_to(REPO)),
        },
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(run_config, ensure_ascii=False, indent=2))
    print("\nTop item summary:")
    print(
        item_summary[
            [
                "priority",
                "title",
                "tested_candidates",
                "test_MAPE",
                "test_p95_APE",
                "test_delta_vs_incumbent_MAPE",
                "test_delta_vs_incumbent_p95_APE",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
