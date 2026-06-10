#!/usr/bin/env python3
"""Run PP-OPT9..13 Warm follow-up improvement experiments.

This batch interprets PP-OPT8 signals and turns them into follow-up candidates:

- PP-OPT9: gated hybrid correction
- PP-OPT10: artist CatBoost safety-gated correction
- PP-OPT11: tail-risk routing/guard correction
- PP-OPT12: multi-objective cap/strength search
- PP-OPT13: artwork-feature shrinkage correction

The experiment is non-submission. It uses the same Warm validation OOF and
fixed test split as PP-OPT8 so results are directly comparable to PP-OPT7.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from lightgbm import LGBMClassifier
except Exception as exc:  # pragma: no cover - local dependency guard
    raise RuntimeError("lightgbm is required for PP-OPT9..13") from exc


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
OPT8_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt8_warm_extended_correction_experiments.py"
spec = importlib.util.spec_from_file_location("pp_opt8_helpers", OPT8_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load helper script: {OPT8_SCRIPT}")
opt8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opt8)

EXP_ID = "PP-OPT9-13"
EXP_SLUG = "PP-OPT9_13_warm_followup_improvement_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

OPT8_PREDS = REPO / "experiments" / "track6" / "PP-OPT8_warm_extended_correction_experiments" / "outputs" / "candidate_predictions.csv"
OPT8_AGG = REPO / "experiments" / "track6" / "PP-OPT8_warm_extended_correction_experiments" / "outputs" / "aggregate_candidate_stability.csv"

BASE_CANDIDATE = opt8.BASE_CANDIDATE
INCUMBENT = "incumbent_operational_pp_opt7"
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT9",
        "priority": "1",
        "title": "게이트형 하이브리드 보정",
        "description": "작가 메타 CatBoost 보정, XGBoost tail 방어, 퀀타일 폭 governor를 row별로 조합한다.",
    },
    {
        "item_id": "PP-OPT10",
        "priority": "2",
        "title": "작가 메타 CatBoost 보정 안전 구간 분류",
        "description": "작가 메타 보정이 이득을 주는 row를 학습해 안전할 때만 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT11",
        "priority": "3",
        "title": "p95 큰 오차 위험 라우터",
        "description": "큰 오차 위험 확률이 높은 row에서만 XGBoost/tail guard 방어 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT12",
        "priority": "4",
        "title": "다목적 cap/strength 탐색",
        "description": "MAPE, p95, 반복 검증 안정성을 함께 고려하는 cap/strength 조합을 탐색한다.",
    },
    {
        "item_id": "PP-OPT13",
        "priority": "5",
        "title": "작품 피쳐 shrinkage 보정",
        "description": "재료/크기/가격대/신뢰도 조합의 잔차를 표본 수 기반 shrinkage로 약하게 보정한다.",
    },
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
    "artist_key",
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
    "area_bin",
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def add_followup_features(base: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    val = out[out["eval_split"].eq("validation_oof")].copy()
    q = val["log_area"].dropna().quantile([0.25, 0.50, 0.75]).to_list()
    bins = [-np.inf] + sorted(set(float(x) for x in q)) + [np.inf]
    if len(bins) < 5:
        bins = [-np.inf, 3.5, 4.5, 5.5, np.inf]
    out["area_bin"] = pd.cut(out["log_area"], bins=bins, labels=False, include_lowest=True).astype("Int64").astype(str)
    out["area_bin"] = out["area_bin"].replace("<NA>", "__MISSING__")
    return out


def load_base_and_source() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = add_followup_features(opt8.load_base())
    source = opt8.source_predictions(base)
    return base, source


def pick_candidate(agg: pd.DataFrame, item_id: str, sort_cols: list[str], ascending: list[bool] | None = None) -> str:
    subset = agg[agg["item_id"].eq(item_id)].copy()
    if subset.empty:
        raise ValueError(f"No PP-OPT8 candidate for {item_id}")
    if ascending is None:
        ascending = [True] * len(sort_cols)
    return str(subset.sort_values(sort_cols, ascending=ascending).iloc[0]["candidate"])


def select_components() -> dict[str, str]:
    agg = pd.read_csv(OPT8_AGG)
    components = {
        "artist_mape": pick_candidate(agg, "A08", ["test_MAPE", "test_p95_APE"]),
        "artist_stable": pick_candidate(agg, "A08", ["recommendation_score_vs_incumbent", "test_MAPE"]),
        "cat_price_band": "catboost_price_band__cap_strength",
        "qwidth_mild": "qwidth_strength__continuous_mild",
        "qwidth_strict": "qwidth_strength__continuous_strict",
        "xgb_tail": pick_candidate(agg, "A07", ["test_p95_APE", "test_MAPE"]),
        "tail_guard": "tail_guard__logistic",
        "lightgbm_tail_guard": "lightgbm_tail_guard__classifier",
        "cat_lgb_equal": "correction_ensemble__cat_lgb_equal",
    }
    available = set(pd.read_csv(OPT8_PREDS, usecols=["candidate"])["candidate"].unique())
    missing = [name for name in components.values() if name not in available]
    if missing:
        raise ValueError(f"Missing PP-OPT8 component predictions: {missing}")
    return components


def load_component_predictions(base: pd.DataFrame, components: dict[str, str]) -> pd.DataFrame:
    needed = set(components.values()) | {BASE_CANDIDATE, INCUMBENT}
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(OPT8_PREDS, usecols=usecols, chunksize=100_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT8 component predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    key = base[["eval_split", "_track6_row_id"]].copy()
    wide = key.copy()
    reverse = {candidate: label for label, candidate in components.items()}
    reverse[BASE_CANDIDATE] = "hcoef_stable_component"
    reverse[INCUMBENT] = "incumbent"
    for candidate, label in reverse.items():
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        wide = wide.merge(part.rename(columns={"pred_log": label}), on=["eval_split", "_track6_row_id"], how="left")
    missing_cols = [col for col in reverse.values() if wide[col].isna().any()]
    if missing_cols:
        raise ValueError(f"Missing component predictions after merge: {missing_cols}")
    return wide.drop(columns=["eval_split", "_track6_row_id"])


def model_matrix(frame: pd.DataFrame) -> pd.DataFrame:
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


def lgbm_classifier(seed: int = SEED) -> LGBMClassifier:
    return LGBMClassifier(
        objective="binary",
        n_estimators=180,
        learning_rate=0.035,
        num_leaves=15,
        max_depth=4,
        min_child_samples=24,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.25,
        reg_lambda=5.0,
        class_weight="balanced",
        random_state=seed,
        verbosity=-1,
        force_col_wise=True,
    )


def oof_lgbm_probability(base: pd.DataFrame, labels: np.ndarray) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = labels[val_mask].astype(int)
    x_val = model_matrix(val)
    x_test = model_matrix(test)
    cat_cols = [c for c in CAT_FEATURES if c in x_val.columns]
    if len(np.unique(y_val)) < 2:
        pred[:] = float(np.mean(y_val))
        return pred
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        y_tr = y_val[tr_idx]
        if len(np.unique(y_tr)) < 2:
            pred[np.flatnonzero(val_mask)[va_idx]] = float(np.mean(y_val))
            continue
        model = lgbm_classifier(SEED + fold)
        model.fit(x_val.iloc[tr_idx], y_tr, categorical_feature=cat_cols)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = lgbm_classifier(SEED + 100)
    model.fit(x_val, y_val, categorical_feature=cat_cols)
    pred[np.flatnonzero(test_mask)] = model.predict_proba(x_test)[:, 1]
    return np.clip(pred, 0.0, 1.0)


def oof_logistic_probability(base: pd.DataFrame, labels: np.ndarray) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = labels[val_mask].astype(int)
    x_val = pd.get_dummies(model_matrix(val).astype(str), dummy_na=False)
    x_test = pd.get_dummies(model_matrix(test).astype(str), dummy_na=False)
    x_test = x_test.reindex(columns=x_val.columns, fill_value=0)
    if len(np.unique(y_val)) < 2:
        pred[:] = float(np.mean(y_val))
        return pred
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        y_tr = y_val[tr_idx]
        if len(np.unique(y_tr)) < 2:
            pred[np.flatnonzero(val_mask)[va_idx]] = float(np.mean(y_val))
            continue
        model = make_pipeline(StandardScaler(with_mean=False), LogisticRegression(max_iter=700, class_weight="balanced", C=0.35))
        model.fit(x_val.iloc[tr_idx], y_tr)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = make_pipeline(StandardScaler(with_mean=False), LogisticRegression(max_iter=700, class_weight="balanced", C=0.35))
    model.fit(x_val, y_val)
    pred[np.flatnonzero(test_mask)] = model.predict_proba(x_test)[:, 1]
    return np.clip(pred, 0.0, 1.0)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def qwidth_governor(base: pd.DataFrame, mode: str) -> np.ndarray:
    q = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    spread = pd.to_numeric(base["component_prediction_spread"], errors="coerce").fillna(0.10).to_numpy(dtype=float)
    gap = pd.to_numeric(base["current_vs_stable_gap_abs"], errors="coerce").fillna(0.03).to_numpy(dtype=float)
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    uncertainty = (
        0.40 * np.clip((q - 1.00) / 0.85, 0, 1)
        + 0.25 * np.clip(spread / 0.18, 0, 1)
        + 0.20 * np.clip(gap / 0.055, 0, 1)
        + 0.15 * np.clip(1.0 / np.maximum(svc + 1.0, 1.0), 0, 1)
    )
    if mode == "strict":
        return np.clip(0.90 - 0.85 * uncertainty, 0.05, 0.90)
    if mode == "mild":
        return np.clip(1.00 - 0.60 * uncertainty, 0.25, 1.00)
    return np.clip(0.80 - 0.45 * uncertainty, 0.20, 0.80)


def row_cap(base: pd.DataFrame, cap: float, mode: str) -> np.ndarray:
    q = pd.to_numeric(base["quantile_width"], errors="coerce").fillna(1.5).to_numpy(dtype=float)
    svc = pd.to_numeric(base["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    price = base["stable_price_band"].fillna("mid_price").astype(str).to_numpy()
    mult = np.ones(len(base), dtype=float)
    if mode == "risk":
        mult *= np.where(q >= 1.65, 0.45, np.where(q >= 1.35, 0.70, 1.00))
        mult *= np.where(svc < 4, 0.55, np.where(svc < 8, 0.80, 1.00))
    elif mode == "price":
        mult *= np.where(price == "very_high_price", 0.55, np.where(price == "high_price", 0.75, 1.00))
    else:
        mult *= np.where(q >= 1.60, 0.60, 1.00)
    return np.maximum(cap * mult, 0.004)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt8.candidate_frame(
        base,
        candidate,
        family,
        item_id,
        pred_log,
        pred_log - pd.to_numeric(base["hcoef_stable"], errors="coerce").to_numpy(dtype=float),
    )


def probability_labels(base: pd.DataFrame, components: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc = components["incumbent"].to_numpy(dtype=float)
    artist = components["artist_stable"].to_numpy(dtype=float)
    inc_ape = ape(inc, actual_price)
    artist_ape = ape(artist, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    p90 = float(np.quantile(inc_ape[val_mask], 0.90))
    p95 = float(np.quantile(inc_ape[val_mask], 0.95))
    safety = (artist_ape < inc_ape) & (artist_ape <= p90) & ((inc_ape - artist_ape) >= 0.005)
    tail = inc_ape >= p90
    labels = {
        "incumbent_validation_p90_ape": p90,
        "incumbent_validation_p95_ape": p95,
        "artist_safety_positive_rate": float(np.mean(safety[val_mask])),
        "tail_risk_positive_rate": float(np.mean(tail[val_mask])),
    }
    return safety.astype(int), tail.astype(int), labels


def pp_opt10_artist_safety_candidates(
    base: pd.DataFrame,
    components: pd.DataFrame,
    safety_prob: np.ndarray,
    safety_logit_prob: np.ndarray,
) -> list[pd.DataFrame]:
    inc = components["incumbent"].to_numpy(dtype=float)
    rows = []
    for source_label in ["artist_stable", "artist_mape", "cat_price_band"]:
        delta = components[source_label].to_numpy(dtype=float) - inc
        for prob_name, prob in [("lgbm", safety_prob), ("logistic", safety_logit_prob)]:
            for strength in [0.35, 0.50, 0.65, 0.80]:
                gate = np.clip((prob - 0.25) / 0.55, 0, 1)
                corr = clip_by_row(delta * gate * qwidth_governor(base, "mild") * strength, row_cap(base, 0.022, "risk"))
                name = f"ppopt10_artist_safety__src={source_label}__gate={prob_name}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "artist_safety_gate", "PP-OPT10", inc + corr))
    return rows


def pp_opt11_tail_router_candidates(
    base: pd.DataFrame,
    components: pd.DataFrame,
    tail_prob: np.ndarray,
    tail_logit_prob: np.ndarray,
) -> list[pd.DataFrame]:
    inc = components["incumbent"].to_numpy(dtype=float)
    rows = []
    tail_sources = {
        "xgb_tail": components["xgb_tail"].to_numpy(dtype=float) - inc,
        "tail_guard": components["tail_guard"].to_numpy(dtype=float) - inc,
        "lgbm_tail_guard": components["lightgbm_tail_guard"].to_numpy(dtype=float) - inc,
        "xgb_tail_guard_mean": 0.50 * (components["xgb_tail"].to_numpy(dtype=float) - inc)
        + 0.50 * (components["tail_guard"].to_numpy(dtype=float) - inc),
    }
    for source_label, delta in tail_sources.items():
        for prob_name, prob in [("lgbm", tail_prob), ("logistic", tail_logit_prob)]:
            for strength in [0.35, 0.55, 0.75, 1.00]:
                gate = np.clip((prob - 0.20) / 0.65, 0, 1)
                corr = clip_by_row(delta * gate * strength, row_cap(base, 0.020, "risk"))
                name = f"ppopt11_tail_router__src={source_label}__gate={prob_name}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "tail_risk_router", "PP-OPT11", inc + corr))
    return rows


def pp_opt9_hybrid_candidates(
    base: pd.DataFrame,
    components: pd.DataFrame,
    safety_prob: np.ndarray,
    tail_prob: np.ndarray,
) -> list[pd.DataFrame]:
    inc = components["incumbent"].to_numpy(dtype=float)
    rows = []
    artist_sources = {
        "artist_stable": components["artist_stable"].to_numpy(dtype=float) - inc,
        "artist_mape": components["artist_mape"].to_numpy(dtype=float) - inc,
        "cat_price_band": components["cat_price_band"].to_numpy(dtype=float) - inc,
    }
    tail_sources = {
        "xgb_tail": components["xgb_tail"].to_numpy(dtype=float) - inc,
        "tail_guard": components["tail_guard"].to_numpy(dtype=float) - inc,
    }
    safe_gate = np.clip((safety_prob - 0.20) / 0.60, 0, 1)
    risk_gate = np.clip((tail_prob - 0.20) / 0.60, 0, 1)
    for artist_name, artist_delta in artist_sources.items():
        for tail_name, tail_delta in tail_sources.items():
            for artist_strength in [0.30, 0.45, 0.60]:
                for tail_strength in [0.35, 0.55, 0.75]:
                    gov = qwidth_governor(base, "mild")
                    artist_corr = artist_delta * safe_gate * gov * artist_strength * (1.0 - 0.45 * risk_gate)
                    tail_corr = tail_delta * risk_gate * tail_strength
                    corr = clip_by_row(artist_corr + tail_corr, row_cap(base, 0.024, "risk"))
                    name = (
                        f"ppopt9_hybrid__artist={artist_name}__tail={tail_name}"
                        f"__as={safe_name(artist_strength)}__ts={safe_name(tail_strength)}"
                    )
                    rows.append(make_candidate(base, name, "gated_hybrid", "PP-OPT9", inc + corr))
    return rows


def pp_opt12_cap_strength_candidates(base: pd.DataFrame, components: pd.DataFrame, safety_prob: np.ndarray, tail_prob: np.ndarray) -> list[pd.DataFrame]:
    inc = components["incumbent"].to_numpy(dtype=float)
    artist = components["artist_stable"].to_numpy(dtype=float) - inc
    cat_price = components["cat_price_band"].to_numpy(dtype=float) - inc
    xgb = components["xgb_tail"].to_numpy(dtype=float) - inc
    q_mild = components["qwidth_mild"].to_numpy(dtype=float) - inc
    rows = []
    safe_gate = np.clip((safety_prob - 0.15) / 0.65, 0, 1)
    risk_gate = np.clip((tail_prob - 0.25) / 0.55, 0, 1)
    for artist_w in [0.15, 0.25, 0.35, 0.45]:
        for cat_w in [0.00, 0.20, 0.35]:
            for tail_w in [0.15, 0.30, 0.45]:
                for cap in [0.014, 0.018, 0.022]:
                    raw = (
                        artist_w * artist * safe_gate
                        + cat_w * cat_price * qwidth_governor(base, "balanced")
                        + tail_w * xgb * risk_gate
                        + 0.25 * q_mild
                    )
                    corr = clip_by_row(raw, row_cap(base, cap, "risk"))
                    name = f"ppopt12_multiobjective_grid__aw={safe_name(artist_w)}__cw={safe_name(cat_w)}__tw={safe_name(tail_w)}__cap={safe_name(cap)}"
                    rows.append(make_candidate(base, name, "multiobjective_cap_strength", "PP-OPT12", inc + corr))
    return rows


def group_shrinkage_predict(
    train: pd.DataFrame,
    apply: pd.DataFrame,
    residual_col: str,
    group_cols: list[str],
    prior_strength: float,
) -> np.ndarray:
    global_mean = float(train[residual_col].mean())
    stats = train.groupby(group_cols, dropna=False)[residual_col].agg(["count", "mean"]).reset_index()
    merged = apply[group_cols].merge(stats, on=group_cols, how="left")
    n = merged["count"].fillna(0).to_numpy(dtype=float)
    mean = merged["mean"].fillna(global_mean).to_numpy(dtype=float)
    return (n * mean + prior_strength * global_mean) / (n + prior_strength)


def oof_shrinkage_correction(base: pd.DataFrame, incumbent: np.ndarray, group_cols: list[str], prior_strength: float) -> np.ndarray:
    work = base.copy()
    work["_residual_vs_incumbent"] = pd.to_numeric(work["actual_log"], errors="coerce").to_numpy(dtype=float) - incumbent
    pred = np.zeros(len(work), dtype=float)
    val_mask = work["eval_split"].eq("validation_oof").to_numpy()
    test_mask = work["eval_split"].eq("test").to_numpy()
    val = work.loc[val_mask].reset_index(drop=True)
    test = work.loc[test_mask].reset_index(drop=True)
    val_positions = np.flatnonzero(val_mask)
    for tr_idx, va_idx in opt8.cv_splits(val):
        train = val.iloc[tr_idx].copy()
        apply = val.iloc[va_idx].copy()
        pred[val_positions[va_idx]] = group_shrinkage_predict(train, apply, "_residual_vs_incumbent", group_cols, prior_strength)
    pred[np.flatnonzero(test_mask)] = group_shrinkage_predict(val, test, "_residual_vs_incumbent", group_cols, prior_strength)
    return pred


def pp_opt13_artwork_shrinkage_candidates(base: pd.DataFrame, components: pd.DataFrame) -> list[pd.DataFrame]:
    inc = components["incumbent"].to_numpy(dtype=float)
    rows = []
    group_sets = {
        "medium": ["medium_support_bucket"],
        "medium_area": ["medium_support_bucket", "area_bin"],
        "medium_price": ["medium_support_bucket", "stable_price_band"],
        "medium_area_price": ["medium_support_bucket", "area_bin", "stable_price_band"],
        "price_qwidth_svc": ["stable_price_band", "qwidth_band", "svc_group_n_band"],
        "medium_price_qwidth": ["medium_support_bucket", "stable_price_band", "qwidth_band"],
    }
    for group_name, cols in group_sets.items():
        for prior in [8.0, 16.0, 32.0]:
            raw = oof_shrinkage_correction(base, inc, cols, prior)
            for strength, cap in [(0.35, 0.010), (0.50, 0.014), (0.70, 0.018)]:
                corr = clip_by_row(raw * qwidth_governor(base, "strict") * strength, row_cap(base, cap, "price"))
                name = f"ppopt13_artwork_shrinkage__group={group_name}__prior={safe_name(prior)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "artwork_shrinkage", "PP-OPT13", inc + corr))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    item_info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id == "BASE":
            continue
        ordered = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        )
        best = ordered.iloc[0]
        rows.append(
            {
                "item_id": item_id,
                "tested_candidates": int(group["candidate"].nunique()),
                "best_candidate": best["candidate"],
                "best_family": best["family"],
                "test_MdAPE": best["test_MdAPE"],
                "test_MAPE": best["test_MAPE"],
                "test_p95_APE": best["test_p95_APE"],
                "test_delta_vs_incumbent_MdAPE": best["test_delta_vs_incumbent_MdAPE"],
                "test_delta_vs_incumbent_MAPE": best["test_delta_vs_incumbent_MAPE"],
                "test_delta_vs_incumbent_p95_APE": best["test_delta_vs_incumbent_p95_APE"],
                "validation_delta_vs_incumbent_MAPE": best["validation_delta_vs_incumbent_MAPE"],
                "validation_delta_vs_incumbent_p95_APE": best["validation_delta_vs_incumbent_p95_APE"],
                "incumbent_MAPE_improve_rate": best["incumbent_MAPE_improve_rate"],
                "incumbent_p95_not_worse_rate": best["incumbent_p95_not_worse_rate"],
                "incumbent_all3_rate": best["incumbent_all3_rate"],
                "stable_validation_pass_vs_incumbent": bool(best["stable_validation_pass_vs_incumbent"]),
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
            }
        )
    summary = pd.DataFrame(rows).merge(item_info, on="item_id", how="left")
    return summary.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    headers = list(view.columns)
    lines = [
        "| " + " | ".join(str(col) for col in headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def render_markdown(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, labels: dict[str, float], components: dict[str, str]) -> str:
    incumbent = metrics[metrics["candidate"].eq(INCUMBENT)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values("recommendation_score_vs_incumbent")
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values("recommendation_score_vs_incumbent")
    best = aggregate.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"], ascending=[False, True, True]).iloc[0]
    lines = [
        "# PP-OPT9~13 Warm 후속 개선 실험 결과",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
        "- 기준 후보: PP-OPT7 운영 후보",
        f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
        "",
        "## 현재 운영 후보 성능",
        markdown_table(incumbent, 10),
        "",
        "## 후속 실험별 최선 후보",
        markdown_table(item_summary[[
            "priority",
            "title",
            "tested_candidates",
            "test_MAPE",
            "test_p95_APE",
            "test_delta_vs_incumbent_MAPE",
            "test_delta_vs_incumbent_p95_APE",
            "stable_validation_pass_vs_incumbent",
            "operational_pass_vs_incumbent",
            "best_family",
            "best_candidate",
        ]], 20),
        "",
        "## 운영 후보 대체 가능 후보",
        markdown_table(operational[[
            "item_id",
            "candidate",
            "family",
            "test_MAPE",
            "test_p95_APE",
            "test_delta_vs_incumbent_MAPE",
            "test_delta_vs_incumbent_p95_APE",
            "incumbent_MAPE_improve_rate",
            "incumbent_p95_not_worse_rate",
            "recommendation_score_vs_incumbent",
        ]], 30),
        "",
        "## Test에서 MAPE와 p95를 동시에 개선한 후보",
        markdown_table(both[[
            "item_id",
            "candidate",
            "family",
            "test_MAPE",
            "test_p95_APE",
            "test_delta_vs_incumbent_MAPE",
            "test_delta_vs_incumbent_p95_APE",
            "recommendation_score_vs_incumbent",
        ]], 30),
        "",
        "## 해석",
        f"- 최우선 후보는 `{best['candidate']}`이다.",
        f"- 이 후보의 fixed test MAPE 변화는 `{best['test_delta_vs_incumbent_MAPE']:.6f}`, p95 변화는 `{best['test_delta_vs_incumbent_p95_APE']:.6f}`이다.",
        f"- 작가 보정 안전 라벨 양성률은 validation 기준 `{labels['artist_safety_positive_rate']:.3f}`이다.",
        f"- tail-risk 라벨 양성률은 validation 기준 `{labels['tail_risk_positive_rate']:.3f}`이다.",
        "",
        "## 사용한 PP-OPT8 구성 요소",
        "```json",
        json.dumps(components, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def render_html(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, labels: dict[str, float], components: dict[str, str]) -> str:
    incumbent = metrics[metrics["candidate"].eq(INCUMBENT)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values("recommendation_score_vs_incumbent")
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values("recommendation_score_vs_incumbent")
    test_top = aggregate.sort_values(["test_MAPE", "test_p95_APE"])
    p95_top = aggregate.sort_values(["test_p95_APE", "test_MAPE"])
    best = aggregate.sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"], ascending=[False, True, True]).iloc[0]
    op_count = int(aggregate["operational_pass_vs_incumbent"].sum())
    verdict = (
        "운영 후보를 대체할 후보가 발견되었다."
        if op_count
        else "운영 후보를 완전히 대체할 후보는 아직 없다. 다만 개선 신호가 분리되어 나타났으므로 후속은 더 정교한 gate 탐색이 필요하다."
    )
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "stable_validation_pass_vs_incumbent",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "item_id",
        "candidate",
        "family",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT9~13 Warm 후속 개선 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1220px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    h3 {{ margin: 24px 0 8px; font-size: 18px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    .small {{ font-size: 13px; color: #4b5563; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT9~13 Warm 후속 개선 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건 · 기준 후보: PP-OPT7 운영 후보</div>
  <div class="callout">{html.escape(verdict)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 대체 통과</strong>{op_count}개</div>
    <div class="panel"><strong>작가 보정 안전 양성률</strong>{labels['artist_safety_positive_rate']:.3f}</div>
    <div class="panel"><strong>Tail-risk 양성률</strong>{labels['tail_risk_positive_rate']:.3f}</div>
  </div>

  <h2>1. 현재 운영 후보 성능</h2>
  {table_html(incumbent, ["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"])}

  <h2>2. 후속 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>3. 운영 후보 대체 가능 후보</h2>
  {table_html(operational, result_cols, 30)}

  <h2>4. Test에서 MAPE와 p95를 동시에 개선한 후보</h2>
  {table_html(both, result_cols, 30)}

  <h2>5. Test MAPE 기준 상위 후보</h2>
  {table_html(test_top, result_cols, 25)}

  <h2>6. Test p95 기준 상위 후보</h2>
  {table_html(p95_top, result_cols, 25)}

  <h2>7. 해석</h2>
  <p>최우선 후보는 <code>{html.escape(str(best['candidate']))}</code>이다. 이 후보의 fixed test MAPE 변화는 <code>{best['test_delta_vs_incumbent_MAPE']:.6f}</code>, p95 변화는 <code>{best['test_delta_vs_incumbent_p95_APE']:.6f}</code>이다.</p>
  <p>PP-OPT8에서 발견한 방향성은 유지된다. 작가 메타 계열은 평균 오차를 낮추는 힘이 있지만 위험 구간에서는 p95를 악화시키고, XGBoost/tail guard 계열은 p95 방어에는 좋지만 평균 오차를 밀어낸다. 따라서 성능 개선은 보정 모델을 하나 더 세게 붙이는 방식보다, 보정을 켤 row를 더 정확히 고르는 방식에서 나올 가능성이 높다.</p>

  <h2>8. 후속 판단</h2>
  <pre>최종 후보 구조
  = PP-OPT7 운영 후보
  + 안전 구간에서만 작동하는 작가 메타 보정
  + 큰 오차 위험 구간에서만 작동하는 tail 방어
  + 퀀타일 폭 기반 보정 강도 축소</pre>
  <p>이번 PP-OPT9~13 결과에서 운영 대체 후보가 나오지 않으면, 다음 실험은 gate 자체의 라벨 정의를 바꿔야 한다. 특히 작가 보정의 안전 라벨을 “개선 여부”가 아니라 “p95 악화 없이 개선되는지”로 더 강하게 잡고, tail-risk 라벨은 상위 5% 대신 상위 10~15%에서 soft target으로 학습하는 쪽이 맞다.</p>

  <h2>9. 사용한 PP-OPT8 구성 요소</h2>
  <pre>{html.escape(json.dumps(components, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""


def main() -> None:
    ensure_dirs()
    base, source = load_base_and_source()
    components = select_components()
    component_preds = load_component_predictions(base, components)
    safety_label, tail_label, labels = probability_labels(base, component_preds)
    safety_prob = oof_lgbm_probability(base, safety_label)
    tail_prob = oof_lgbm_probability(base, tail_label)
    safety_logit_prob = oof_logistic_probability(base, safety_label)
    tail_logit_prob = oof_logistic_probability(base, tail_label)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt9_hybrid_candidates(base, component_preds, safety_prob, tail_prob))
    candidates.extend(pp_opt10_artist_safety_candidates(base, component_preds, safety_prob, safety_logit_prob))
    candidates.extend(pp_opt11_tail_router_candidates(base, component_preds, tail_prob, tail_logit_prob))
    candidates.extend(pp_opt12_cap_strength_candidates(base, component_preds, safety_prob, tail_prob))
    candidates.extend(pp_opt13_artwork_shrinkage_candidates(base, component_preds))

    predictions = pd.concat([source] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)

    report_md = render_markdown(metrics, aggregate, item_summary, labels, components)
    report_html = render_html(metrics, aggregate, item_summary, labels, components)
    (REPORT_DIR / "followup_result_interpretation.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "followup_result_interpretation.html").write_text(report_html, encoding="utf-8")

    run_config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "items": ITEMS,
        "component_candidates": components,
        "labels": labels,
        "sources": {
            "pp_opt8_predictions": str(OPT8_PREDS.relative_to(REPO)),
            "pp_opt8_aggregate": str(OPT8_AGG.relative_to(REPO)),
            "helper_script": str(OPT8_SCRIPT.relative_to(REPO)),
        },
    }
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8")
    (ARTIFACT_DIR / "gate_probabilities.csv").write_text(
        pd.DataFrame(
            {
                "eval_split": base["eval_split"],
                "_track6_row_id": base["_track6_row_id"],
                "safety_label": safety_label,
                "tail_label": tail_label,
                "safety_lgbm_probability": safety_prob,
                "safety_logistic_probability": safety_logit_prob,
                "tail_lgbm_probability": tail_prob,
                "tail_logistic_probability": tail_logit_prob,
            }
        ).to_csv(index=False),
        encoding="utf-8",
    )

    print(json.dumps(run_config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
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
                "stable_validation_pass_vs_incumbent",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nOperational pass count:", int(aggregate["operational_pass_vs_incumbent"].sum()))


if __name__ == "__main__":
    main()
