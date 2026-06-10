#!/usr/bin/env python3
"""Run PP-OPT21..28 Warm model-characteristic experiments.

The previous batches showed that row-level gates matter more than simply
adding another residual model. This batch tests model characteristics that can
improve those gates:

- PP-OPT21: uplift model correction selection
- PP-OPT22: quantile residual shrinkage
- PP-OPT23: monotonic constrained gate
- PP-OPT24: conformal risk gate
- PP-OPT25: CatBoost categorical specialist
- PP-OPT26: LightGBM risk classifier specialist
- PP-OPT27: two-stage micro residual
- PP-OPT28: segment-level model router

The experiment remains non-submission and uses the same Warm validation OOF /
fixed test split as PP-OPT8..20.
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
from catboost import CatBoostClassifier, CatBoostRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
OPT8_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt8_warm_extended_correction_experiments.py"
OPT9_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt9_13_warm_followup_improvement_experiments.py"
OPT14_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt14_20_warm_gate_refinement_experiments.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opt8 = load_module("pp_opt8_helpers", OPT8_SCRIPT)
opt9 = load_module("pp_opt9_helpers", OPT9_SCRIPT)
opt14 = load_module("pp_opt14_helpers", OPT14_SCRIPT)

EXP_ID = "PP-OPT21-28"
EXP_SLUG = "PP-OPT21_28_warm_model_characteristic_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP14_PREDS = REPO / "experiments" / "track6" / "PP-OPT14_20_warm_gate_refinement_experiments" / "outputs" / "candidate_predictions.csv"
PP14_AGG = REPO / "experiments" / "track6" / "PP-OPT14_20_warm_gate_refinement_experiments" / "outputs" / "aggregate_candidate_stability.csv"
PP14_CONFIG = REPO / "experiments" / "track6" / "PP-OPT14_20_warm_gate_refinement_experiments" / "artifacts" / "run_config.json"

BASE_CANDIDATE = opt8.BASE_CANDIDATE
INCUMBENT = "incumbent_operational_pp_opt7"
PREV_CHALLENGER = "previous_challenger_pp20"
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {"item_id": "PP-OPT21", "priority": "1", "title": "uplift model 기반 보정 선택", "description": "row별로 보정하면 좋아지는지를 직접 학습한다."},
    {"item_id": "PP-OPT22", "priority": "2", "title": "quantile residual shrinkage", "description": "잔차의 q25/q50/q75를 학습해 불확실성이 큰 보정은 줄인다."},
    {"item_id": "PP-OPT23", "priority": "3", "title": "monotonic constrained gate", "description": "불확실성이 커질수록 보정 사용 확률이 줄도록 제약을 둔다."},
    {"item_id": "PP-OPT24", "priority": "4", "title": "conformal risk gate", "description": "예측구간 폭과 비순응 점수로 위험한 row의 보정을 축소한다."},
    {"item_id": "PP-OPT25", "priority": "5", "title": "CatBoost categorical specialist", "description": "범주형 상호작용을 잘 다루는 CatBoost로 보정/선택을 전담시킨다."},
    {"item_id": "PP-OPT26", "priority": "6", "title": "LightGBM risk classifier specialist", "description": "LightGBM을 가격 보정이 아니라 tail-risk gate 전용으로 사용한다."},
    {"item_id": "PP-OPT27", "priority": "7", "title": "two-stage micro residual", "description": "선택 후보 이후 남은 잔차만 아주 작은 cap으로 2차 보정한다."},
    {"item_id": "PP-OPT28", "priority": "8", "title": "segment별 model-of-models router", "description": "구간별로 PP-OPT7/20/15/19/14 후보 중 가장 안정적인 후보를 선택한다."},
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def load_pp14_config() -> dict[str, Any]:
    return json.loads(PP14_CONFIG.read_text(encoding="utf-8"))


def select_components() -> dict[str, str]:
    agg = pd.read_csv(PP14_AGG)
    cfg = load_pp14_config()
    decision = cfg["selection_decision"]
    op = agg[agg["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    if op.empty:
        raise ValueError("PP-OPT14..20 has no operational pass candidate")
    selected = {
        "pp20_protocol": decision["protocol_candidate"],
        "pp20_source": decision["selected_source_candidate"],
        "pp19_best_score": str(op[op["item_id"].eq("PP-OPT19")].iloc[0]["candidate"]),
        "pp14_best_score": str(op[op["item_id"].eq("PP-OPT14")].iloc[0]["candidate"]),
        "pp15_best_mape": str(agg[agg["item_id"].eq("PP-OPT15")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
        "pp16_best_score": str(op[op["item_id"].eq("PP-OPT16")].iloc[0]["candidate"]),
        "pp17_best_score": str(op[op["item_id"].eq("PP-OPT17")].iloc[0]["candidate"]),
        "pp18_best_mape": str(agg[agg["item_id"].eq("PP-OPT18")].sort_values(["test_MAPE", "test_p95_APE"]).iloc[0]["candidate"]),
    }
    selected.update({f"opt8_{k}": v for k, v in opt9.select_components().items()})
    return selected


def load_pp14_component_predictions(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    pp14_keys = [k for k in selected if not k.startswith("opt8_")]
    needed = {selected[k] for k in pp14_keys}
    usecols = ["candidate", "eval_split", "_track6_row_id", "pred_log"]
    chunks = []
    for chunk in pd.read_csv(PP14_PREDS, usecols=usecols, chunksize=100_000):
        part = chunk[chunk["candidate"].isin(needed)].copy()
        if not part.empty:
            chunks.append(part)
    if not chunks:
        raise ValueError("No PP-OPT14..20 component predictions loaded")
    long = pd.concat(chunks, ignore_index=True)
    out = base[["eval_split", "_track6_row_id"]].copy()
    for key in pp14_keys:
        candidate = selected[key]
        part = long[long["candidate"].eq(candidate)][["eval_split", "_track6_row_id", "pred_log"]]
        out = out.merge(part.rename(columns={"pred_log": key}), on=["eval_split", "_track6_row_id"], how="left")
    missing = [col for col in pp14_keys if out[col].isna().any()]
    if missing:
        raise ValueError(f"Missing PP-OPT14 components after merge: {missing}")
    return out.drop(columns=["eval_split", "_track6_row_id"])


def load_components(base: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    opt8_selected = {k.removeprefix("opt8_"): v for k, v in selected.items() if k.startswith("opt8_")}
    opt8_preds = opt9.load_component_predictions(base, opt8_selected).add_prefix("opt8_")
    # Restore incumbent naming from the PP-OPT8 loader.
    opt8_preds = opt8_preds.rename(columns={"opt8_incumbent": "incumbent"})
    pp14_preds = load_pp14_component_predictions(base, selected)
    return pd.concat([opt8_preds, pp14_preds], axis=1)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt8.candidate_frame(
        base,
        candidate,
        family,
        item_id,
        pred_log,
        pred_log - pd.to_numeric(base["hcoef_stable"], errors="coerce").to_numpy(dtype=float),
    )


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def qwidth_governor(base: pd.DataFrame, mode: str) -> np.ndarray:
    return opt9.qwidth_governor(base, mode)


def row_cap(base: pd.DataFrame, cap: float, mode: str) -> np.ndarray:
    return opt9.row_cap(base, cap, mode)


def gate(prob: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((prob - threshold) / max(width, 1e-6), 0.0, 1.0)


def validation_thresholds(base: pd.DataFrame, incumbent: np.ndarray) -> dict[str, float]:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(incumbent, actual_price)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    return {
        "p85": float(np.quantile(inc_ape[val_mask], 0.85)),
        "p90": float(np.quantile(inc_ape[val_mask], 0.90)),
        "p95": float(np.quantile(inc_ape[val_mask], 0.95)),
    }


def uplift_label(base: pd.DataFrame, incumbent: np.ndarray, candidate_pred: np.ndarray, p90: float) -> np.ndarray:
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(incumbent, actual_price)
    cand_ape = ape(candidate_pred, actual_price)
    return ((inc_ape - cand_ape) > 0.0025) & (cand_ape <= p90 + 0.02)


def lgbm_classifier(seed: int = SEED, monotone: list[int] | None = None) -> LGBMClassifier:
    params: dict[str, Any] = {
        "objective": "binary",
        "n_estimators": 180,
        "learning_rate": 0.035,
        "num_leaves": 15,
        "max_depth": 4,
        "min_child_samples": 24,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 0.25,
        "reg_lambda": 5.0,
        "class_weight": "balanced",
        "random_state": seed,
        "verbosity": -1,
        "force_col_wise": True,
    }
    if monotone is not None:
        params["monotone_constraints"] = monotone
    return LGBMClassifier(**params)


def oof_lgbm_probability(base: pd.DataFrame, labels: np.ndarray, monotone: bool = False) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = labels[val_mask].astype(int)
    x_val = opt9.model_matrix(val)
    x_test = opt9.model_matrix(test)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    constraints: list[int] | None = None
    if monotone:
        constraints = []
        for col in x_val.columns:
            if col in {"quantile_width", "component_prediction_spread", "component_prediction_range", "current_vs_stable_gap_abs", "confidence_risk_score", "l10_price_range_ratio"}:
                constraints.append(-1)
            elif col in {"svc_group_n", "svc_group_n_log"}:
                constraints.append(1)
            else:
                constraints.append(0)
    if len(np.unique(y_val)) < 2:
        pred[:] = float(np.mean(y_val))
        return pred
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        y_tr = y_val[tr_idx]
        if len(np.unique(y_tr)) < 2:
            pred[np.flatnonzero(val_mask)[va_idx]] = float(np.mean(y_val))
            continue
        model = lgbm_classifier(SEED + fold, monotone=constraints)
        model.fit(x_val.iloc[tr_idx], y_tr, categorical_feature=cat_cols)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = lgbm_classifier(SEED + 100, monotone=constraints)
    model.fit(x_val, y_val, categorical_feature=cat_cols)
    pred[np.flatnonzero(test_mask)] = model.predict_proba(x_test)[:, 1]
    return np.clip(pred, 0.0, 1.0)


def oof_catboost_probability(base: pd.DataFrame, labels: np.ndarray) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = labels[val_mask].astype(int)
    x_val = opt9.model_matrix(val).astype(str)
    x_test = opt9.model_matrix(test).astype(str)
    cat_features = list(range(x_val.shape[1]))
    if len(np.unique(y_val)) < 2:
        pred[:] = float(np.mean(y_val))
        return pred
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        y_tr = y_val[tr_idx]
        if len(np.unique(y_tr)) < 2:
            pred[np.flatnonzero(val_mask)[va_idx]] = float(np.mean(y_val))
            continue
        model = CatBoostClassifier(
            iterations=140,
            learning_rate=0.045,
            depth=4,
            l2_leaf_reg=8.0,
            loss_function="Logloss",
            random_seed=SEED + fold,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(x_val.iloc[tr_idx], y_tr, cat_features=cat_features)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = CatBoostClassifier(
        iterations=140,
        learning_rate=0.045,
        depth=4,
        l2_leaf_reg=8.0,
        loss_function="Logloss",
        random_seed=SEED + 100,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(x_val, y_val, cat_features=cat_features)
    pred[np.flatnonzero(test_mask)] = model.predict_proba(x_test)[:, 1]
    return np.clip(pred, 0.0, 1.0)


def oof_lgbm_quantile_residual(base: pd.DataFrame, center: np.ndarray) -> dict[str, np.ndarray]:
    pred: dict[str, np.ndarray] = {k: np.zeros(len(base), dtype=float) for k in ["q25", "q50", "q75"]}
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float) - center[val_mask]
    x_val = opt9.model_matrix(val)
    x_test = opt9.model_matrix(test)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    for label, alpha in [("q25", 0.25), ("q50", 0.50), ("q75", 0.75)]:
        for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
            model = LGBMRegressor(
                objective="quantile",
                alpha=alpha,
                n_estimators=190,
                learning_rate=0.035,
                num_leaves=15,
                max_depth=4,
                min_child_samples=24,
                subsample=0.85,
                colsample_bytree=0.85,
                reg_alpha=0.25,
                reg_lambda=5.0,
                random_state=SEED + fold,
                verbosity=-1,
                force_col_wise=True,
            )
            model.fit(x_val.iloc[tr_idx], y_val[tr_idx], categorical_feature=cat_cols)
            pred[label][np.flatnonzero(val_mask)[va_idx]] = model.predict(x_val.iloc[va_idx])
        model = LGBMRegressor(
            objective="quantile",
            alpha=alpha,
            n_estimators=190,
            learning_rate=0.035,
            num_leaves=15,
            max_depth=4,
            min_child_samples=24,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.25,
            reg_lambda=5.0,
            random_state=SEED + 100,
            verbosity=-1,
            force_col_wise=True,
        )
        model.fit(x_val, y_val, categorical_feature=cat_cols)
        pred[label][np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_catboost_residual(base: pd.DataFrame, center: np.ndarray) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float) - center[val_mask]
    x_val = opt9.model_matrix(val).astype(str)
    x_test = opt9.model_matrix(test).astype(str)
    cat_features = list(range(x_val.shape[1]))
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = CatBoostRegressor(
            iterations=180,
            learning_rate=0.035,
            depth=4,
            l2_leaf_reg=10.0,
            loss_function="MAE",
            random_seed=SEED + fold,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(x_val.iloc[tr_idx], y_val[tr_idx], cat_features=cat_features)
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = CatBoostRegressor(
        iterations=180,
        learning_rate=0.035,
        depth=4,
        l2_leaf_reg=10.0,
        loss_function="MAE",
        random_seed=SEED + 100,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(x_val, y_val, cat_features=cat_features)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_ridge_micro_residual(base: pd.DataFrame, center: np.ndarray) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    y_val = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float) - center[val_mask]
    x_val = pd.get_dummies(opt9.model_matrix(val).astype(str), dummy_na=False)
    x_test = pd.get_dummies(opt9.model_matrix(test).astype(str), dummy_na=False).reindex(columns=x_val.columns, fill_value=0)
    for tr_idx, va_idx in opt8.cv_splits(val):
        model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=18.0))
        model.fit(x_val.iloc[tr_idx], y_val[tr_idx])
        pred[np.flatnonzero(val_mask)[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=18.0))
    model.fit(x_val, y_val)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def pp_opt21_uplift_candidates(base: pd.DataFrame, comp: pd.DataFrame, thresholds: dict[str, float]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    source_keys = ["pp15_best_mape", "pp19_best_score", "pp14_best_score", "pp20_protocol", "opt8_artist_mape"]
    for source_key in source_keys:
        source_pred = comp[source_key].to_numpy(dtype=float)
        delta = source_pred - inc
        label = uplift_label(base, inc, source_pred, thresholds["p90"])
        probs = {
            "lgbm": oof_lgbm_probability(base, label),
            "catboost": oof_catboost_probability(base, label),
        }
        for model_name, prob in probs.items():
            for threshold in [0.18, 0.28, 0.38]:
                for strength in [0.55, 0.75, 0.95]:
                    g = gate(prob, threshold, 0.60)
                    corr = clip_by_row(delta * g * strength * qwidth_governor(base, "mild"), row_cap(base, 0.024, "risk"))
                    name = f"ppopt21_uplift_gate__src={source_key}__model={model_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "uplift_correction_selector", "PP-OPT21", inc + corr))
    return rows


def pp_opt22_quantile_candidates(base: pd.DataFrame, comp: pd.DataFrame) -> tuple[list[pd.DataFrame], dict[str, np.ndarray]]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    quant = oof_lgbm_quantile_residual(base, inc)
    width = np.maximum(quant["q75"] - quant["q25"], 0.0)
    shrink = 1.0 / (1.0 + np.clip(width / 0.18, 0.0, 4.0))
    rows: list[pd.DataFrame] = []
    for strength in [0.25, 0.40, 0.55]:
        for cap in [0.010, 0.014, 0.018]:
            corr = clip_by_row(quant["q50"] * shrink * strength, row_cap(base, cap, "risk"))
            name = f"ppopt22_quantile_residual__s={safe_name(strength)}__cap={safe_name(cap)}"
            rows.append(make_candidate(base, name, "quantile_residual_shrinkage", "PP-OPT22", inc + corr))
    return rows, quant


def pp_opt23_monotonic_candidates(base: pd.DataFrame, comp: pd.DataFrame, thresholds: dict[str, float]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    for source_key in ["pp15_best_mape", "pp19_best_score", "opt8_cat_price_band"]:
        source_pred = comp[source_key].to_numpy(dtype=float)
        delta = source_pred - inc
        label = uplift_label(base, inc, source_pred, thresholds["p90"])
        prob = oof_lgbm_probability(base, label, monotone=True)
        for threshold in [0.16, 0.26, 0.36]:
            for strength in [0.45, 0.65, 0.85]:
                corr = clip_by_row(delta * gate(prob, threshold, 0.60) * strength, row_cap(base, 0.022, "risk"))
                name = f"ppopt23_monotonic_gate__src={source_key}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "monotonic_constrained_gate", "PP-OPT23", inc + corr))
    return rows


def pp_opt24_conformal_candidates(base: pd.DataFrame, comp: pd.DataFrame, quant: dict[str, np.ndarray], thresholds: dict[str, float]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    rows: list[pd.DataFrame] = []
    width = np.maximum(quant["q75"] - quant["q25"], 0.0)
    conformal_width = np.clip(width / max(float(np.nanquantile(width, 0.80)), 1e-6), 0.0, 3.0)
    risk_shrink = 1.0 / (1.0 + conformal_width)
    p95_prob = oof_lgbm_probability(
        base,
        (ape(inc, pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)) >= thresholds["p95"]).astype(int),
    )
    for source_key in ["pp20_protocol", "pp19_best_score", "pp15_best_mape"]:
        delta = comp[source_key].to_numpy(dtype=float) - inc
        for strength in [0.55, 0.75, 0.95]:
            for cap in [0.018, 0.022]:
                shrink = risk_shrink * (1.0 - 0.35 * gate(p95_prob, 0.18, 0.60))
                corr = clip_by_row(delta * shrink * strength, row_cap(base, cap, "risk"))
                name = f"ppopt24_conformal_gate__src={source_key}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "conformal_risk_gate", "PP-OPT24", inc + corr))
    return rows


def pp_opt25_catboost_specialist_candidates(base: pd.DataFrame, comp: pd.DataFrame, thresholds: dict[str, float]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    residual = oof_catboost_residual(base, inc)
    rows: list[pd.DataFrame] = []
    for strength in [0.25, 0.40, 0.55]:
        for cap in [0.010, 0.014, 0.018]:
            corr = clip_by_row(residual * qwidth_governor(base, "strict") * strength, row_cap(base, cap, "risk"))
            name = f"ppopt25_catboost_residual__s={safe_name(strength)}__cap={safe_name(cap)}"
            rows.append(make_candidate(base, name, "catboost_categorical_specialist", "PP-OPT25", inc + corr))
    # CatBoost as an uplift selector for the strongest MAPE candidate.
    src = comp["pp15_best_mape"].to_numpy(dtype=float)
    label = uplift_label(base, inc, src, thresholds["p90"])
    prob = oof_catboost_probability(base, label)
    delta = src - inc
    for threshold in [0.20, 0.32, 0.44]:
        for strength in [0.55, 0.75, 0.95]:
            corr = clip_by_row(delta * gate(prob, threshold, 0.60) * strength, row_cap(base, 0.022, "risk"))
            name = f"ppopt25_catboost_uplift__thr={safe_name(threshold)}__s={safe_name(strength)}"
            rows.append(make_candidate(base, name, "catboost_categorical_specialist", "PP-OPT25", inc + corr))
    return rows


def pp_opt26_lgbm_risk_specialist_candidates(base: pd.DataFrame, comp: pd.DataFrame, thresholds: dict[str, float]) -> list[pd.DataFrame]:
    inc = comp["incumbent"].to_numpy(dtype=float)
    actual_price = pd.to_numeric(base["actual_price"], errors="coerce").to_numpy(dtype=float)
    inc_ape = ape(inc, actual_price)
    rows: list[pd.DataFrame] = []
    risk_probs = {
        "p85": oof_lgbm_probability(base, (inc_ape >= thresholds["p85"]).astype(int)),
        "p90": oof_lgbm_probability(base, (inc_ape >= thresholds["p90"]).astype(int)),
        "p95": oof_lgbm_probability(base, (inc_ape >= thresholds["p95"]).astype(int)),
    }
    tail_delta = comp["opt8_xgb_tail"].to_numpy(dtype=float) - inc
    pp16_delta = comp["pp16_best_score"].to_numpy(dtype=float) - inc
    for label_name, prob in risk_probs.items():
        for source_name, delta in [("xgb_tail", tail_delta), ("pp16_best", pp16_delta)]:
            for threshold in [0.14, 0.22, 0.32]:
                for strength in [0.45, 0.65, 0.85]:
                    corr = clip_by_row(delta * gate(prob, threshold, 0.60) * strength, row_cap(base, 0.022, "risk"))
                    name = f"ppopt26_lgbm_risk__label={label_name}__src={source_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "lightgbm_risk_classifier_specialist", "PP-OPT26", inc + corr))
    return rows


def pp_opt27_micro_residual_candidates(base: pd.DataFrame, comp: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for center_key in ["pp20_protocol", "pp19_best_score", "pp14_best_score"]:
        center = comp[center_key].to_numpy(dtype=float)
        micro = oof_ridge_micro_residual(base, center)
        for strength in [0.20, 0.35, 0.50]:
            for cap in [0.004, 0.007, 0.010]:
                corr = clip_by_row(micro * qwidth_governor(base, "strict") * strength, row_cap(base, cap, "risk"))
                name = f"ppopt27_micro_residual__center={center_key}__s={safe_name(strength)}__cap={safe_name(cap)}"
                rows.append(make_candidate(base, name, "two_stage_micro_residual", "PP-OPT27", center + corr))
    return rows


def segment_router_predictions(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    candidate_keys: list[str],
    group_cols: list[str],
    objective: str,
) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val = base.loc[val_mask].reset_index(drop=True)
    test = base.loc[test_mask].reset_index(drop=True)
    val_pos = np.flatnonzero(val_mask)
    test_pos = np.flatnonzero(test_mask)
    actual_price_val = pd.to_numeric(val["actual_price"], errors="coerce").to_numpy(dtype=float)
    actual_price_test = pd.to_numeric(test["actual_price"], errors="coerce").to_numpy(dtype=float)
    matrix_val = pd.DataFrame({key: comp.loc[val_mask, key].to_numpy(dtype=float) for key in candidate_keys})
    matrix_test = pd.DataFrame({key: comp.loc[test_mask, key].to_numpy(dtype=float) for key in candidate_keys})

    def choose(train_frame: pd.DataFrame, train_matrix: pd.DataFrame) -> dict[tuple[Any, ...], str]:
        choices: dict[tuple[Any, ...], str] = {}
        global_scores = {}
        train_actual = pd.to_numeric(train_frame["actual_price"], errors="coerce").to_numpy(dtype=float)
        for key in candidate_keys:
            err = ape(train_matrix[key].to_numpy(dtype=float), train_actual)
            global_scores[key] = float(np.mean(err) + (0.45 if objective == "guarded" else 0.20) * np.quantile(err, 0.95))
        global_best = min(global_scores, key=global_scores.get)
        for group_value, idx in train_frame.groupby(group_cols, dropna=False).groups.items():
            idx_arr = np.array(list(idx), dtype=int)
            if len(idx_arr) < 18:
                choices[group_value if isinstance(group_value, tuple) else (group_value,)] = global_best
                continue
            scores = {}
            actual = train_actual[idx_arr]
            for key in candidate_keys:
                err = ape(train_matrix.iloc[idx_arr][key].to_numpy(dtype=float), actual)
                penalty = 0.45 * np.quantile(err, 0.95) if objective == "guarded" else 0.20 * np.quantile(err, 0.95)
                scores[key] = float(np.mean(err) + penalty)
            choices[group_value if isinstance(group_value, tuple) else (group_value,)] = min(scores, key=scores.get)
        choices[("__GLOBAL__",)] = global_best
        return choices

    def apply_choices(apply_frame: pd.DataFrame, apply_matrix: pd.DataFrame, choices: dict[tuple[Any, ...], str]) -> np.ndarray:
        out = np.zeros(len(apply_frame), dtype=float)
        default = choices[("__GLOBAL__",)]
        for i, row in apply_frame[group_cols].reset_index(drop=True).iterrows():
            key_tuple = tuple(row[col] for col in group_cols)
            chosen = choices.get(key_tuple, default)
            out[i] = float(apply_matrix.iloc[i][chosen])
        return out

    for tr_idx, va_idx in opt8.cv_splits(val):
        choices = choose(val.iloc[tr_idx].reset_index(drop=True), matrix_val.iloc[tr_idx].reset_index(drop=True))
        pred[val_pos[va_idx]] = apply_choices(val.iloc[va_idx].reset_index(drop=True), matrix_val.iloc[va_idx].reset_index(drop=True), choices)
    choices = choose(val, matrix_val)
    pred[test_pos] = apply_choices(test, matrix_test, choices)
    return pred


def pp_opt28_segment_router_candidates(base: pd.DataFrame, comp: pd.DataFrame) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    candidate_keys = ["incumbent", "pp20_protocol", "pp19_best_score", "pp14_best_score", "pp15_best_mape", "pp16_best_score"]
    group_sets = {
        "price": ["stable_price_band"],
        "confidence": ["confidence_tier"],
        "price_confidence": ["stable_price_band", "confidence_tier"],
        "price_qwidth": ["stable_price_band", "qwidth_band"],
        "svc_qwidth": ["svc_group_n_band", "qwidth_band"],
        "price_support": ["stable_price_band", "svc_group_n_band"],
    }
    for group_name, cols in group_sets.items():
        for objective in ["mape", "guarded"]:
            pred = segment_router_predictions(base, comp, candidate_keys, cols, objective)
            name = f"ppopt28_segment_router__group={group_name}__obj={objective}"
            rows.append(make_candidate(base, name, "segment_model_router", "PP-OPT28", pred))
    return rows


def previous_challenger_frame(base: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    pred = comp["pp20_protocol"].to_numpy(dtype=float)
    return make_candidate(base, PREV_CHALLENGER, "previous_challenger", "PREV", pred)


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    item_info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "PREV"}:
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


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 40) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = [
        "| " + " | ".join(str(col) for col in view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, config: dict[str, Any]) -> tuple[str, str]:
    incumbent = metrics[metrics["candidate"].eq(INCUMBENT)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"]].sort_values("eval_split")
    previous = metrics[metrics["candidate"].eq(PREV_CHALLENGER)][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("eval_split")
    operational = aggregate[aggregate["operational_pass_vs_incumbent"]].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    best = operational.iloc[0] if not operational.empty else aggregate.sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).iloc[0]
    best_metrics = metrics[metrics["candidate"].eq(best["candidate"])][["eval_split", "n", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50", "delta_vs_incumbent_MdAPE", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]].sort_values("eval_split")
    both = aggregate[(aggregate["test_delta_vs_incumbent_MAPE"] < 0) & (aggregate["test_delta_vs_incumbent_p95_APE"] < 0)].sort_values(["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True])
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "stable_validation_pass_vs_incumbent",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "item_id",
        "candidate",
        "family",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MdAPE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "incumbent_all3_rate",
        "recommendation_score_vs_incumbent",
    ]
    md = "\n".join(
        [
            "# PP-OPT21~28 Warm 모델 특성 기반 추가 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, Warm validation OOF 519건 + fixed test 607건",
            "- 기준 후보: PP-OPT7 운영 후보",
            f"- 전체 후보 수: {aggregate['candidate'].nunique()}",
            f"- 운영 대체 통과 후보 수: {int(aggregate['operational_pass_vs_incumbent'].sum())}",
            "",
            "## 최우선 후보",
            f"- 후보: `{best['candidate']}`",
            f"- 실험: `{best['item_id']}` / `{best['family']}`",
            markdown_table(best_metrics, list(best_metrics.columns), 10),
            "",
            "## 이전 challenger PP-OPT20",
            markdown_table(previous, list(previous.columns), 10),
            "",
            "## 현재 운영 후보 PP-OPT7",
            markdown_table(incumbent, list(incumbent.columns), 10),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 20),
            "",
            "## 운영 대체 통과 후보 상위",
            markdown_table(operational, result_cols, 40),
            "",
            "## Test에서 MAPE와 p95를 동시에 개선한 후보",
            markdown_table(both, result_cols, 40),
            "",
            "## 해석",
            "이번 실험은 모델 특성 자체를 보정 구조에 넣는 실험이다. 가장 중요한 비교 기준은 PP-OPT7 대비 개선뿐 아니라 PP-OPT20 challenger 대비 추가 개선 여부다.",
            "uplift gate와 segment router 계열이 강하면 보정 선택 문제로, quantile/conformal/monotonic 계열이 강하면 위험도 축소 문제로 다음 단계를 좁히면 된다.",
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    verdict = "운영 후보 대체 조건을 통과한 후보가 발견되었다." if int(aggregate["operational_pass_vs_incumbent"].sum()) else "운영 후보 대체 조건 통과 후보는 없다."
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT21~28 Warm 모델 특성 기반 추가 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1240px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .panel {{ border: 1px solid #d8dee6; background: #fbfcfd; border-radius: 8px; padding: 14px; }}
    .panel strong {{ display: block; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 22px; }}
    th, td {{ border: 1px solid #d8dee6; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f1f3f5; text-align: left; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    pre {{ background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; overflow-x: auto; }}
    @media (max-width: 900px) {{ main {{ padding: 28px 16px 56px; }} .grid {{ grid-template-columns: 1fr; }} table {{ font-size: 12px; }} }}
  </style>
</head>
<body>
<main>
  <h1>PP-OPT21~28 Warm 모델 특성 기반 추가 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)} 최우선 후보는 <code>{html.escape(str(best['candidate']))}</code>이다.</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>운영 통과</strong>{int(aggregate['operational_pass_vs_incumbent'].sum())}개</div>
    <div class="panel"><strong>최우선 test MAPE 변화</strong>{float(best['test_delta_vs_incumbent_MAPE']):.6f}</div>
    <div class="panel"><strong>최우선 test p95 변화</strong>{float(best['test_delta_vs_incumbent_p95_APE']):.6f}</div>
  </div>

  <h2>1. 최우선 후보</h2>
  <p>실험: <code>{html.escape(str(best['item_id']))}</code> / <code>{html.escape(str(best['family']))}</code></p>
  {table_html(best_metrics, list(best_metrics.columns), 10)}

  <h2>2. 이전 challenger PP-OPT20</h2>
  {table_html(previous, list(previous.columns), 10)}

  <h2>3. 현재 운영 후보 PP-OPT7</h2>
  {table_html(incumbent, list(incumbent.columns), 10)}

  <h2>4. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 20)}

  <h2>5. 운영 대체 통과 후보 상위</h2>
  {table_html(operational, result_cols, 40)}

  <h2>6. Test에서 MAPE와 p95를 동시에 개선한 후보</h2>
  {table_html(both, result_cols, 40)}

  <h2>7. 해석</h2>
  <p>이번 실험은 모델 특성 자체를 보정 구조에 넣는 실험이다. 최우선 판단은 PP-OPT7 대비 개선뿐 아니라 PP-OPT20 challenger 대비 추가 개선 여부를 함께 봐야 한다.</p>
  <p>uplift gate와 segment router 계열이 강하면 보정 선택 문제가 핵심이고, quantile/conformal/monotonic 계열이 강하면 위험도 축소 문제가 핵심이다.</p>

  <h2>8. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source = opt9.load_base_and_source()
    selected = select_components()
    comp = load_components(base, selected)
    thresholds = validation_thresholds(base, comp["incumbent"].to_numpy(dtype=float))

    candidates: list[pd.DataFrame] = [previous_challenger_frame(base, comp)]
    candidates.extend(pp_opt21_uplift_candidates(base, comp, thresholds))
    q_candidates, quant = pp_opt22_quantile_candidates(base, comp)
    candidates.extend(q_candidates)
    candidates.extend(pp_opt23_monotonic_candidates(base, comp, thresholds))
    candidates.extend(pp_opt24_conformal_candidates(base, comp, quant, thresholds))
    candidates.extend(pp_opt25_catboost_specialist_candidates(base, comp, thresholds))
    candidates.extend(pp_opt26_lgbm_risk_specialist_candidates(base, comp, thresholds))
    candidates.extend(pp_opt27_micro_residual_candidates(base, comp))
    candidates.extend(pp_opt28_segment_router_candidates(base, comp))

    predictions = pd.concat([source] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "base_candidate": BASE_CANDIDATE,
        "incumbent_candidate": INCUMBENT,
        "previous_challenger": PREV_CHALLENGER,
        "validation_rows": int(base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "items": ITEMS,
        "selected_components": selected,
        "thresholds": thresholds,
        "sources": {
            "pp_opt14_predictions": str(PP14_PREDS.relative_to(REPO)),
            "pp_opt14_aggregate": str(PP14_AGG.relative_to(REPO)),
            "pp_opt14_config": str(PP14_CONFIG.relative_to(REPO)),
            "pp_opt8_helper": str(OPT8_SCRIPT.relative_to(REPO)),
            "pp_opt9_helper": str(OPT9_SCRIPT.relative_to(REPO)),
            "pp_opt14_helper": str(OPT14_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, config)
    (REPORT_DIR / "model_characteristic_result_interpretation.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "model_characteristic_result_interpretation.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
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
                "incumbent_MAPE_improve_rate",
                "incumbent_p95_not_worse_rate",
                "stable_validation_pass_vs_incumbent",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nOperational pass count:", int(aggregate["operational_pass_vs_incumbent"].sum()))


if __name__ == "__main__":
    main()
