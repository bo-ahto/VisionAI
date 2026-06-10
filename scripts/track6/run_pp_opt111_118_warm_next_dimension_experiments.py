#!/usr/bin/env python3
"""Run PP-OPT111..118 Warm next-dimension improvement experiments.

PP110 showed that guard refinement can improve the stability of PP102-style
post-processing, but fixed-test gains remain very small.  This batch therefore
tests two broader directions on the same non-submission Warm validation/test
split:

1. candidate-level meta routing across the strongest existing Warm candidates;
2. regenerating or stacking the price basis with LightGBM/CatBoost/XGBoost and
   confidence-weighted residual models.

Every learned component is cross-fitted on validation_oof and then refit once
on the full validation_oof split for the fixed test rows.
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
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP96_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt96_102_warm_tail_label_refinement_experiments.py"
PP103_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt103_110_warm_pp102_guard_refinement_experiments.py"
PP71_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt71_75_warm_pp70_stability_validation.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp96 = load_module("pp_opt96_helpers_for_pp111", PP96_SCRIPT)
pp103 = load_module("pp_opt103_helpers_for_pp111", PP103_SCRIPT)
val71 = load_module("pp_opt71_helpers_for_pp111", PP71_SCRIPT)
opt8 = pp96.opt8
opt9 = pp96.opt9
opt29 = pp96.opt29

EXP_ID = "PP-OPT111-118"
EXP_SLUG = "PP-OPT111_118_warm_next_dimension_experiments"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP103_DIR = REPO / "experiments" / "track6" / "PP-OPT103_110_warm_pp102_guard_refinement_experiments"
PP103_PREDS = PP103_DIR / "outputs" / "candidate_predictions.csv"
PP103_CONFIG = PP103_DIR / "artifacts" / "run_config.json"
PP96_LABELS = REPO / "experiments" / "track6" / "PP-OPT96_102_warm_tail_label_refinement_experiments" / "artifacts" / "tail_label_probability_detail.csv"

BASE_CANDIDATE = pp96.BASE_CANDIDATE
INCUMBENT = pp96.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT111",
        "priority": "1",
        "title": "candidate meta-router",
        "description": "PP81/PP95/PP110/p95 후보 중 row별로 이길 후보를 학습해 선택 또는 가중 평균한다.",
    },
    {
        "item_id": "PP-OPT112",
        "priority": "2",
        "title": "basis regeneration regressors",
        "description": "LightGBM, CatBoost, XGBoost로 로그가격 기준가를 직접 재생성하고 안정 후보와 제한적으로 결합한다.",
    },
    {
        "item_id": "PP-OPT113",
        "priority": "3",
        "title": "over/under direction correction",
        "description": "기준가가 과대/과소인지 먼저 분류하고 방향 확신이 있을 때만 작은 보정을 적용한다.",
    },
    {
        "item_id": "PP-OPT114",
        "priority": "4",
        "title": "confidence weighted residual model",
        "description": "고신뢰 row에 더 큰 sample weight를 주어 남은 잔차를 학습한다.",
    },
    {
        "item_id": "PP-OPT115",
        "priority": "5",
        "title": "comparable proxy basis stack",
        "description": "SVC/PPV8/L10/PP110 등 기존 유사작품 proxy 예측값을 선형/Huber 스택킹으로 다시 결합한다.",
    },
    {
        "item_id": "PP-OPT116",
        "priority": "6",
        "title": "hybrid model stack router",
        "description": "재생성 기준가와 기존 후보 사이의 gap, risk, gain 확률을 보고 제한적으로 채택한다.",
    },
    {
        "item_id": "PP-OPT117",
        "priority": "7",
        "title": "stability-selected next candidate",
        "description": "고정 test뿐 아니라 반복 안정성 점수까지 사용해 후보를 선별한다.",
    },
    {
        "item_id": "PP-OPT118",
        "priority": "8",
        "title": "final next-dimension decision",
        "description": "선택 후보를 운영형/p95형으로 복제하고 PP81/PP95/PP110과 비교한다.",
    },
]

REF_LABELS = {
    "pp64": "reference_pp64_current_best",
    "pp70": "reference_pp70_refinement",
    "pp81": "reference_pp81_best",
    "pp82_op": "reference_pp82_operational",
    "pp82_p95": "reference_pp82_p95",
    "pp95_op": "reference_pp95_operational",
    "pp95_p95": "reference_pp95_p95",
    "pp102_op": "reference_pp102_operational",
    "pp110_op": "pp110_operational_guarded_pp102_challenger",
    "pp110_p95": "pp110_p95_guarded_pp102_challenger",
}


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(value: np.ndarray, threshold: float, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return opt29.make_candidate(base, candidate, family, item_id, pred_log)


def ape(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(opt8.safe_exp(pred_log) - actual_price) / np.maximum(actual_price, EPS)


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return opt9.row_cap(base, cap, mode)


def qwidth_governor(base: pd.DataFrame, mode: str = "strict") -> np.ndarray:
    return opt9.qwidth_governor(base, mode)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def confidence_weights(frame: pd.DataFrame, risk: np.ndarray | None = None) -> np.ndarray:
    weights = frame["confidence_tier"].map({"high_confidence": 1.0, "medium_confidence": 0.58, "low_confidence": 0.28}).fillna(0.55).to_numpy(dtype=float)
    if risk is not None:
        weights = weights * (1.0 - 0.35 * np.clip(risk, 0.0, 1.0))
    return np.clip(weights, 0.15, 1.0)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any]]:
    base, source, _, _, _, _ = pp96.load_inputs()
    cfg = load_json(PP103_CONFIG)
    selected = dict(REF_LABELS)
    selected["pp110_op"] = cfg["selection_decision"]["operational_protocol_candidate"]
    selected["pp110_p95"] = cfg["selection_decision"]["p95_protocol_candidate"]
    ref = pp96.load_predictions_from_file(base, PP103_PREDS, selected)
    labels = base[["eval_split", "_track6_row_id"]].merge(pd.read_csv(PP96_LABELS), on=["eval_split", "_track6_row_id"], how="left")
    return base, source, ref, labels, selected, cfg


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp95_p95", "pp95_p95"),
        ("reference_pp102_operational", "pp102_op"),
        ("reference_pp110_operational", "pp110_op"),
        ("reference_pp110_p95", "pp110_p95"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


def feature_frame(base: pd.DataFrame, ref: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    for key in ref.columns:
        out[f"pred_{key}"] = pd.to_numeric(ref[key], errors="coerce")
        out[f"gap_{key}_vs_pp81"] = out[f"pred_{key}"] - pd.to_numeric(ref["pp81"], errors="coerce")
    component_cols = [f"pred_{key}" for key in ref.columns]
    out["candidate_pred_mean"] = out[component_cols].mean(axis=1)
    out["candidate_pred_std"] = out[component_cols].std(axis=1).fillna(0.0)
    out["candidate_pred_range"] = out[component_cols].max(axis=1) - out[component_cols].min(axis=1)
    for col in labels.columns:
        if col.startswith("prob_"):
            out[col] = pd.to_numeric(labels[col], errors="coerce").fillna(0.0)
    return out


def lgbm_feature_matrix(frame: pd.DataFrame, extra_numeric: list[str]) -> pd.DataFrame:
    x = frame.copy()
    numeric_cols = list(dict.fromkeys(opt9.NUMERIC_FEATURES + extra_numeric))
    for col in numeric_cols:
        if col not in x.columns:
            x[col] = np.nan
        x[col] = pd.to_numeric(x[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        x[col] = x[col].fillna(x[col].median()).fillna(0.0)
    out = x[numeric_cols + opt9.CAT_FEATURES].copy()
    for col in opt9.CAT_FEATURES:
        out[col] = out[col].fillna("__MISSING__").astype("category")
    return out


def dummy_feature_matrix(frame: pd.DataFrame, extra_numeric: list[str]) -> pd.DataFrame:
    x = lgbm_feature_matrix(frame, extra_numeric)
    numeric_cols = [c for c in x.columns if c not in opt9.CAT_FEATURES]
    num = x[numeric_cols].reset_index(drop=True)
    cat = pd.get_dummies(x[opt9.CAT_FEATURES].astype(str), dummy_na=False).reset_index(drop=True)
    out = pd.concat([num, cat], axis=1)
    out.columns = [f"f_{i}_{safe_name(col)}" for i, col in enumerate(out.columns)]
    return out


def catboost_feature_matrix(frame: pd.DataFrame, extra_numeric: list[str]) -> tuple[pd.DataFrame, list[int]]:
    x = lgbm_feature_matrix(frame, extra_numeric).copy()
    for col in opt9.CAT_FEATURES:
        x[col] = x[col].astype(str)
    cat_features = [x.columns.get_loc(col) for col in opt9.CAT_FEATURES if col in x.columns]
    return x, cat_features


def extra_numeric_columns(ref: pd.DataFrame, labels: pd.DataFrame) -> list[str]:
    cols = []
    for key in ref.columns:
        cols.append(f"pred_{key}")
        cols.append(f"gap_{key}_vs_pp81")
    cols.extend(["candidate_pred_mean", "candidate_pred_std", "candidate_pred_range"])
    cols.extend([col for col in labels.columns if col.startswith("prob_")])
    return cols


def lgbm_regressor(seed: int, objective: str = "regression_l1", alpha: float | None = None) -> LGBMRegressor:
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 240,
        "learning_rate": 0.032,
        "num_leaves": 15,
        "max_depth": 4,
        "min_child_samples": 26,
        "subsample": 0.86,
        "colsample_bytree": 0.86,
        "reg_alpha": 0.25,
        "reg_lambda": 7.0,
        "random_state": seed,
        "verbosity": -1,
        "force_col_wise": True,
    }
    if alpha is not None:
        params["alpha"] = alpha
    return LGBMRegressor(**params)


def lgbm_classifier(seed: int, objective: str = "binary", num_class: int | None = None) -> LGBMClassifier:
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 190,
        "learning_rate": 0.035,
        "num_leaves": 15,
        "max_depth": 4,
        "min_child_samples": 24,
        "subsample": 0.86,
        "colsample_bytree": 0.86,
        "reg_alpha": 0.25,
        "reg_lambda": 6.0,
        "random_state": seed,
        "verbosity": -1,
        "force_col_wise": True,
    }
    if num_class is not None:
        params["num_class"] = num_class
    return LGBMClassifier(**params)


def oof_lgbm_direct(frame: pd.DataFrame, extra_cols: list[str], sample_weighted: bool = False, objective: str = "regression_l1") -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    y = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float)
    x_val = lgbm_feature_matrix(val, extra_cols)
    x_test = lgbm_feature_matrix(test, extra_cols)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    risk = val71.risk_score(val)
    weights = confidence_weights(val, risk)
    val_pos = np.flatnonzero(val_mask)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = lgbm_regressor(SEED + fold, objective=objective)
        kwargs: dict[str, Any] = {"categorical_feature": cat_cols}
        if sample_weighted:
            kwargs["sample_weight"] = weights[tr_idx]
        model.fit(x_val.iloc[tr_idx], y[tr_idx], **kwargs)
        pred[val_pos[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = lgbm_regressor(SEED + 100, objective=objective)
    kwargs = {"categorical_feature": cat_cols}
    if sample_weighted:
        kwargs["sample_weight"] = weights
    model.fit(x_val, y, **kwargs)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_catboost_direct(frame: pd.DataFrame, extra_cols: list[str], sample_weighted: bool = False) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    y = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float)
    x_val, cat_features = catboost_feature_matrix(val, extra_cols)
    x_test, _ = catboost_feature_matrix(test, extra_cols)
    weights = confidence_weights(val, val71.risk_score(val))
    val_pos = np.flatnonzero(val_mask)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = CatBoostRegressor(
            iterations=220,
            learning_rate=0.035,
            depth=4,
            l2_leaf_reg=12.0,
            loss_function="MAE",
            random_seed=SEED + fold,
            verbose=False,
            allow_writing_files=False,
        )
        kwargs: dict[str, Any] = {"cat_features": cat_features}
        if sample_weighted:
            kwargs["sample_weight"] = weights[tr_idx]
        model.fit(x_val.iloc[tr_idx], y[tr_idx], **kwargs)
        pred[val_pos[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = CatBoostRegressor(
        iterations=220,
        learning_rate=0.035,
        depth=4,
        l2_leaf_reg=12.0,
        loss_function="MAE",
        random_seed=SEED + 100,
        verbose=False,
        allow_writing_files=False,
    )
    kwargs = {"cat_features": cat_features}
    if sample_weighted:
        kwargs["sample_weight"] = weights
    model.fit(x_val, y, **kwargs)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_xgb_direct(frame: pd.DataFrame, extra_cols: list[str]) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    y = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float)
    x_val = dummy_feature_matrix(val, extra_cols)
    x_test = dummy_feature_matrix(test, extra_cols).reindex(columns=x_val.columns, fill_value=0.0)
    weights = confidence_weights(val, val71.risk_score(val))
    val_pos = np.flatnonzero(val_mask)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=210,
            learning_rate=0.035,
            max_depth=3,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.20,
            reg_lambda=7.0,
            min_child_weight=8.0,
            random_state=SEED + fold,
            n_jobs=1,
            verbosity=0,
        )
        model.fit(x_val.iloc[tr_idx], y[tr_idx], sample_weight=weights[tr_idx])
        pred[val_pos[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=210,
        learning_rate=0.035,
        max_depth=3,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.20,
        reg_lambda=7.0,
        min_child_weight=8.0,
        random_state=SEED + 100,
        n_jobs=1,
        verbosity=0,
    )
    model.fit(x_val, y, sample_weight=weights)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_residual_lgbm(frame: pd.DataFrame, extra_cols: list[str], center: np.ndarray, sample_weighted: bool = True) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    y = pd.to_numeric(val["actual_log"], errors="coerce").to_numpy(dtype=float) - center[val_mask]
    x_val = lgbm_feature_matrix(val, extra_cols)
    x_test = lgbm_feature_matrix(test, extra_cols)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    weights = confidence_weights(val, val71.risk_score(val))
    val_pos = np.flatnonzero(val_mask)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = lgbm_regressor(SEED + 300 + fold)
        kwargs: dict[str, Any] = {"categorical_feature": cat_cols}
        if sample_weighted:
            kwargs["sample_weight"] = weights[tr_idx]
        model.fit(x_val.iloc[tr_idx], y[tr_idx], **kwargs)
        pred[val_pos[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = lgbm_regressor(SEED + 400)
    kwargs = {"categorical_feature": cat_cols}
    if sample_weighted:
        kwargs["sample_weight"] = weights
    model.fit(x_val, y, **kwargs)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def oof_direction_probabilities(frame: pd.DataFrame, extra_cols: list[str], center: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    residual = pd.to_numeric(frame["actual_log"], errors="coerce").to_numpy(dtype=float) - center
    y_pos = (residual[val_mask] > 0.018).astype(int)
    y_neg = (residual[val_mask] < -0.018).astype(int)
    x_val = lgbm_feature_matrix(val, extra_cols)
    x_test = lgbm_feature_matrix(test, extra_cols)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    val_pos_idx = np.flatnonzero(val_mask)
    test_idx = np.flatnonzero(test_mask)
    out_pos = np.zeros(len(frame), dtype=float)
    out_neg = np.zeros(len(frame), dtype=float)

    def fit_label(y: np.ndarray, offset: int) -> np.ndarray:
        out = np.zeros(len(frame), dtype=float)
        if len(np.unique(y)) < 2:
            out[:] = float(np.mean(y))
            return out
        for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
            model = lgbm_classifier(SEED + offset + fold)
            model.fit(x_val.iloc[tr_idx], y[tr_idx], categorical_feature=cat_cols)
            out[val_pos_idx[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
        model = lgbm_classifier(SEED + offset + 100)
        model.fit(x_val, y, categorical_feature=cat_cols)
        out[test_idx] = model.predict_proba(x_test)[:, 1]
        return out

    out_pos = fit_label(y_pos, 500)
    out_neg = fit_label(y_neg, 700)
    return out_pos, out_neg


def oof_meta_router(frame: pd.DataFrame, ref: pd.DataFrame, candidate_keys: list[str], extra_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    pred = np.zeros(len(frame), dtype=float)
    max_prob = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    val = frame.loc[val_mask].reset_index(drop=True)
    test = frame.loc[test_mask].reset_index(drop=True)
    actual_price = pd.to_numeric(frame["actual_price"], errors="coerce").to_numpy(dtype=float)
    err = np.vstack([ape(ref[key].to_numpy(dtype=float), actual_price) for key in candidate_keys]).T
    y = np.argmin(err[val_mask], axis=1).astype(int)
    x_val = lgbm_feature_matrix(val, extra_cols)
    x_test = lgbm_feature_matrix(test, extra_cols)
    cat_cols = [c for c in opt9.CAT_FEATURES if c in x_val.columns]
    val_idx = np.flatnonzero(val_mask)
    test_idx = np.flatnonzero(test_mask)
    mat = np.vstack([ref[key].to_numpy(dtype=float) for key in candidate_keys]).T
    if len(np.unique(y)) < 2:
        chosen = int(np.bincount(y).argmax())
        pred[:] = mat[:, chosen]
        max_prob[:] = 1.0
        return pred, max_prob
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = lgbm_classifier(SEED + 900 + fold, objective="multiclass", num_class=len(candidate_keys))
        model.fit(x_val.iloc[tr_idx], y[tr_idx], categorical_feature=cat_cols)
        prob = model.predict_proba(x_val.iloc[va_idx])
        if isinstance(prob, list):
            prob = np.vstack([p[:, 1] for p in prob]).T
        if prob.shape[1] != len(candidate_keys):
            full = np.zeros((len(va_idx), len(candidate_keys)), dtype=float)
            for cls_i, cls in enumerate(model.classes_):
                full[:, int(cls)] = prob[:, cls_i]
            prob = full
        pred[val_idx[va_idx]] = np.sum(mat[val_idx[va_idx]] * prob, axis=1)
        max_prob[val_idx[va_idx]] = np.max(prob, axis=1)
    model = lgbm_classifier(SEED + 1000, objective="multiclass", num_class=len(candidate_keys))
    model.fit(x_val, y, categorical_feature=cat_cols)
    prob = model.predict_proba(x_test)
    if prob.shape[1] != len(candidate_keys):
        full = np.zeros((len(test), len(candidate_keys)), dtype=float)
        for cls_i, cls in enumerate(model.classes_):
            full[:, int(cls)] = prob[:, cls_i]
        prob = full
    pred[test_idx] = np.sum(mat[test_idx] * prob, axis=1)
    max_prob[test_idx] = np.max(prob, axis=1)
    return pred, max_prob


def oof_linear_stack(frame: pd.DataFrame, ref: pd.DataFrame, candidate_keys: list[str], model_name: str, weighted: bool) -> np.ndarray:
    pred = np.zeros(len(frame), dtype=float)
    val_mask = frame["eval_split"].eq("validation_oof").to_numpy()
    test_mask = frame["eval_split"].eq("test").to_numpy()
    y = pd.to_numeric(frame.loc[val_mask, "actual_log"], errors="coerce").to_numpy(dtype=float)
    x = pd.DataFrame({key: ref[key].to_numpy(dtype=float) for key in candidate_keys})
    x["mean"] = x[candidate_keys].mean(axis=1)
    x["std"] = x[candidate_keys].std(axis=1).fillna(0.0)
    x["range"] = x[candidate_keys].max(axis=1) - x[candidate_keys].min(axis=1)
    x_val = x.loc[val_mask].reset_index(drop=True)
    x_test = x.loc[test_mask].reset_index(drop=True)
    weights = confidence_weights(frame.loc[val_mask].reset_index(drop=True), val71.risk_score(frame.loc[val_mask].reset_index(drop=True)))
    val_idx = np.flatnonzero(val_mask)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(frame.loc[val_mask].reset_index(drop=True))):
        if model_name == "huber":
            model = make_pipeline(StandardScaler(), HuberRegressor(epsilon=1.25, alpha=0.010, max_iter=400))
        else:
            model = make_pipeline(StandardScaler(), Ridge(alpha=8.0))
        kwargs = {}
        if weighted:
            kwargs = {"huberregressor__sample_weight" if model_name == "huber" else "ridge__sample_weight": weights[tr_idx]}
        model.fit(x_val.iloc[tr_idx], y[tr_idx], **kwargs)
        pred[val_idx[va_idx]] = model.predict(x_val.iloc[va_idx])
    if model_name == "huber":
        model = make_pipeline(StandardScaler(), HuberRegressor(epsilon=1.25, alpha=0.010, max_iter=400))
    else:
        model = make_pipeline(StandardScaler(), Ridge(alpha=8.0))
    kwargs = {}
    if weighted:
        kwargs = {"huberregressor__sample_weight" if model_name == "huber" else "ridge__sample_weight": weights}
    model.fit(x_val, y, **kwargs)
    pred[np.flatnonzero(test_mask)] = model.predict(x_test)
    return pred


def pp_opt111_meta_router(base: pd.DataFrame, ref: pd.DataFrame, frame: pd.DataFrame, extra_cols: list[str]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp81"].to_numpy(dtype=float)
    candidate_sets = {
        "operational": ["pp81", "pp95_op", "pp110_op", "pp102_op", "pp70"],
        "tail_mix": ["pp81", "pp110_op", "pp82_op", "pp110_p95", "pp82_p95"],
    }
    for set_name, keys in candidate_sets.items():
        routed, max_prob = oof_meta_router(frame, ref, keys, extra_cols)
        for threshold in [0.22, 0.32, 0.44]:
            p_gate = gate(max_prob, threshold, 0.45)
            for strength in [0.35, 0.55, 0.75, 1.0]:
                pred = safe + (routed - safe) * p_gate * strength
                name = f"ppopt111_meta_router__set={set_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "candidate_meta_router", "PP-OPT111", pred))
    return rows


def pp_opt112_basis_regeneration(base: pd.DataFrame, ref: pd.DataFrame, model_preds: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    anchors = {"pp81": ref["pp81"].to_numpy(dtype=float), "pp110": ref["pp110_op"].to_numpy(dtype=float)}
    for model_name, model_pred in model_preds.items():
        for anchor_name, anchor in anchors.items():
            delta = model_pred - anchor
            for cap in [0.010, 0.018, 0.030, 0.045]:
                for strength in [0.25, 0.45, 0.65]:
                    corr = clip_by_row(delta * strength * qwidth_governor(base, "mild"), row_cap(base, cap, "risk"))
                    name = f"ppopt112_basis_regen__model={model_name}__anchor={anchor_name}__cap={safe_name(cap)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "basis_regeneration_regressor", "PP-OPT112", anchor + corr))
    return rows


def pp_opt113_directional(base: pd.DataFrame, ref: pd.DataFrame, frame: pd.DataFrame, extra_cols: list[str]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for anchor_key in ["pp81", "pp110_op"]:
        anchor = ref[anchor_key].to_numpy(dtype=float)
        pos, neg = oof_direction_probabilities(frame, extra_cols, anchor)
        margin = pos - neg
        for threshold in [0.04, 0.08, 0.14, 0.22]:
            confidence = gate(np.abs(margin), threshold, 0.36)
            direction = np.sign(margin)
            for cap in [0.004, 0.007, 0.011, 0.016]:
                for strength in [0.35, 0.55, 0.75]:
                    corr = direction * confidence * row_cap(base, cap, "risk") * strength * qwidth_governor(base, "strict")
                    name = f"ppopt113_direction__anchor={anchor_key}__thr={safe_name(threshold)}__cap={safe_name(cap)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "over_under_direction_correction", "PP-OPT113", anchor + corr))
    return rows


def pp_opt114_confidence_residual(base: pd.DataFrame, ref: pd.DataFrame, residual_preds: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    centers = {"pp81": ref["pp81"].to_numpy(dtype=float), "pp110": ref["pp110_op"].to_numpy(dtype=float)}
    for pred_name, residual in residual_preds.items():
        center_key = "pp110" if "pp110" in pred_name else "pp81"
        center = centers[center_key]
        for cap in [0.004, 0.007, 0.011, 0.016, 0.024]:
            for strength in [0.20, 0.35, 0.55, 0.75]:
                corr = clip_by_row(residual * strength * qwidth_governor(base, "strict"), row_cap(base, cap, "risk"))
                name = f"ppopt114_conf_residual__src={pred_name}__cap={safe_name(cap)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "confidence_weighted_residual_model", "PP-OPT114", center + corr))
    return rows


def pp_opt115_proxy_stack(base: pd.DataFrame, ref: pd.DataFrame, stack_preds: dict[str, np.ndarray]) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for stack_name, stack_pred in stack_preds.items():
        for anchor_key in ["pp81", "pp110_op"]:
            anchor = ref[anchor_key].to_numpy(dtype=float)
            delta = stack_pred - anchor
            for cap in [0.010, 0.018, 0.030]:
                for strength in [0.25, 0.45, 0.65, 0.85]:
                    corr = clip_by_row(delta * strength, row_cap(base, cap, "risk"))
                    name = f"ppopt115_proxy_stack__model={stack_name}__anchor={anchor_key}__cap={safe_name(cap)}__s={safe_name(strength)}"
                    rows.append(make_candidate(base, name, "comparable_proxy_basis_stack", "PP-OPT115", anchor + corr))
    return rows


def pp_opt116_hybrid_router(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    labels: pd.DataFrame,
    model_preds: dict[str, np.ndarray],
    stack_preds: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp81"].to_numpy(dtype=float)
    op = ref["pp110_op"].to_numpy(dtype=float)
    risk = val71.risk_score(base)
    gain = labels["prob_best_gain_tail75"].to_numpy(dtype=float)
    harm = labels["prob_best_harm"].to_numpy(dtype=float)
    target_preds = {
        "lgbm_weighted": model_preds["lgbm_weighted"],
        "cat_weighted": model_preds["cat_weighted"],
        "ridge_stack_weighted": stack_preds["ridge_weighted"],
        "huber_stack_weighted": stack_preds["huber_weighted"],
    }
    for target_name, target in target_preds.items():
        improvement_score = np.clip(gain - 0.70 * harm - 0.18 * risk, 0, 1)
        gap = np.abs(target - op)
        gap_gate = 1.0 - gate(gap, 0.055, 0.085)
        score = improvement_score * gap_gate
        for threshold in [0.02, 0.06, 0.12, 0.20]:
            w = gate(score, threshold, 0.24)
            for strength in [0.20, 0.35, 0.55, 0.75]:
                pred = safe + (target - safe) * w * strength
                name = f"ppopt116_hybrid_stack_router__target={target_name}__thr={safe_name(threshold)}__s={safe_name(strength)}"
                rows.append(make_candidate(base, name, "hybrid_model_stack_router", "PP-OPT116", pred))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(
            ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent", "test_MAPE"],
            ascending=[False, True, True],
        ).iloc[0]
        p95_pool = group[group["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"])
        if p95_pool.empty:
            p95_pool = group.sort_values(["test_p95_APE", "test_MAPE"])
        p95 = p95_pool.iloc[0]
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
                "incumbent_MAPE_improve_rate": best["incumbent_MAPE_improve_rate"],
                "incumbent_p95_not_worse_rate": best["incumbent_p95_not_worse_rate"],
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
                "p95_candidate": p95["candidate"],
                "p95_test_MAPE": p95["test_MAPE"],
                "p95_test_p95_APE": p95["test_p95_APE"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["operational_pass_vs_incumbent", "recommendation_score_vs_incumbent"], ascending=[False, True]
    )


def select_candidates_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame) -> list[str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    pp64_mape = float(test[test["candidate"].eq("reference_pp64_current_best")]["MAPE"].iloc[0])
    pp64_p95 = float(test[test["candidate"].eq("reference_pp64_current_best")]["p95_APE"].iloc[0])
    new_pool = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].copy()
    new_pool["delta_vs_pp64_MAPE"] = new_pool["test_MAPE"] - pp64_mape
    new_pool["delta_vs_pp64_p95_APE"] = new_pool["test_p95_APE"] - pp64_p95
    balanced = new_pool[
        (new_pool["delta_vs_pp64_MAPE"] <= 0.00008)
        & (new_pool["delta_vs_pp64_p95_APE"] <= 0.00008)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(20)
    best_mape = new_pool.sort_values(["test_MAPE", "test_p95_APE"]).head(20)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(20)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(20)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    references = [
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp102_operational",
        "reference_pp110_operational",
        "reference_pp110_p95",
        "reference_pp82_operational",
        "reference_pp82_p95",
        INCUMBENT,
        BASE_CANDIDATE,
    ]
    return references + [candidate for candidate in selected if candidate not in references]


def label_for_stability(predictions: pd.DataFrame, selected_candidates: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT: "incumbent_pp7",
        "reference_pp64_current_best": "pp64_current_best",
        "reference_pp70_refinement": "pp70_refinement_candidate",
        "reference_pp81_best": "pp81_stable_reference",
        "reference_pp95_operational": "pp95_operational_reference",
        "reference_pp102_operational": "pp102_operational_reference",
        "reference_pp110_operational": "pp110_operational_reference",
        "reference_pp110_p95": "pp110_p95_reference",
        "reference_pp82_operational": "pp82_operational_reference",
        "reference_pp82_p95": "pp82_p95_reference",
    }
    subset = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    for candidate in selected_candidates:
        if candidate not in label_map:
            label_map[candidate] = f"candidate_{safe_name(candidate)[:120]}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def attach_candidate_names(stability_aggregate: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    if "candidate" in stability_aggregate.columns:
        return stability_aggregate
    lookup = fixed[["candidate_label", "candidate"]].drop_duplicates("candidate_label")
    return stability_aggregate.merge(lookup, on="candidate_label", how="left")


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp102_operational_reference",
        "pp110_operational_reference",
        "pp110_p95_reference",
        "pp82_operational_reference",
        "pp82_p95_reference",
        "incumbent_pp7",
        "hcoef_stable_source",
    }
    pool = stability_aggregate[~stability_aggregate["candidate_label"].isin(refs)].copy()
    if pool.empty:
        raise ValueError("No new stability candidates available")
    pool["fixed_test_delta_vs_pp64_MAPE"] = pool["fixed_test_MAPE"] - float(pp64["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp64_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp64["fixed_test_p95_APE"])
    op_pool = pool[
        (pool["fixed_test_delta_vs_pp64_MAPE"] <= 0.00003)
        & (pool["fixed_test_delta_vs_pp64_p95_APE"] <= 0.00003)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.50)
    ].copy()
    if op_pool.empty:
        op_pool = pool.sort_values(["replacement_score", "fixed_test_MAPE"]).head(20).copy()
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00020)
        & (pool["fixed_test_p95_APE"] < float(pp64["fixed_test_p95_APE"]) - 0.00003)
    ].copy()
    if p95_pool.empty:
        p95_pool = pool[pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00035].copy()
    if p95_pool.empty:
        p95_pool = pool.copy()
    p95 = p95_pool.sort_values(["fixed_test_p95_APE", "fixed_test_MAPE", "replacement_score"]).iloc[0]
    return {
        "operational_label": str(operational["candidate_label"]),
        "operational_candidate": str(operational["candidate"]),
        "operational_fixed_test_MAPE": float(operational["fixed_test_MAPE"]),
        "operational_fixed_test_p95_APE": float(operational["fixed_test_p95_APE"]),
        "operational_delta_vs_pp64_MAPE": float(operational["fixed_test_delta_vs_pp64_MAPE"]),
        "operational_delta_vs_pp64_p95_APE": float(operational["fixed_test_delta_vs_pp64_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "next_dimension_operational_selection"), ("p95", "next_dimension_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt118_{key}_next_dimension_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT118"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
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


def render_reports(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    item_summary: pd.DataFrame,
    stability_aggregate: pd.DataFrame,
    stability_summary: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected_names = [
        "reference_pp64_current_best",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp110_operational",
        decision["operational_protocol_candidate"],
        decision["p95_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected_names)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].str.startswith("PP-OPT", na=False)].sort_values(
        ["recommendation_score_vs_incumbent", "test_MAPE"]
    )
    top_p95 = aggregate[
        (aggregate["item_id"].str.startswith("PP-OPT", na=False))
        & (aggregate["test_delta_vs_incumbent_MAPE"] < 0)
    ].sort_values(["test_p95_APE", "test_MAPE"])
    item_cols = [
        "priority",
        "title",
        "tested_candidates",
        "test_MAPE",
        "test_p95_APE",
        "p95_test_MAPE",
        "p95_test_p95_APE",
        "operational_pass_vs_incumbent",
        "best_family",
        "best_candidate",
    ]
    result_cols = [
        "candidate",
        "item_id",
        "family",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_vs_incumbent_MAPE",
        "test_delta_vs_incumbent_p95_APE",
        "incumbent_MAPE_improve_rate",
        "incumbent_p95_not_worse_rate",
        "recommendation_score_vs_incumbent",
    ]
    stab_cols = [
        "candidate_label",
        "fixed_test_MAPE",
        "fixed_test_p95_APE",
        "fixed_test_delta_vs_pp64_MAPE",
        "fixed_test_delta_vs_pp64_p95_APE",
        "avg_delta_vs_pp64_MAPE",
        "avg_delta_vs_pp64_p95_APE",
        "avg_pp64_MAPE_win_rate",
        "avg_pp64_p95_win_rate",
        "replacement_score",
    ]
    scenario_cols = [
        "candidate_label",
        "eval_split",
        "scenario",
        "mean_delta_vs_pp64_MAPE",
        "mean_delta_vs_pp64_p95_APE",
        "pp64_MAPE_win_rate",
        "pp64_p95_win_rate",
        "pp64_all3_win_rate",
    ]
    focus_labels = [
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp110_operational_reference",
        "pp118_operational_next_dimension_challenger",
        "pp118_p95_next_dimension_challenger",
    ]
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(focus_labels)]
    verdict = (
        f"운영 후보 {decision['operational_label']} fixed test MAPE "
        f"{decision['operational_fixed_test_MAPE']:.6f}, p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP64 대비 MAPE {decision['operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp64_p95_APE']:+.6f}."
    )
    interpretation = (
        "기준가 재생성/스택킹은 기존 보정과 다른 차원의 접근이다. 고정 test에서 더 낮은 후보가 나오더라도 "
        "validation 반복 안정성이 PP81/PP95 또는 PP110보다 낮으면 운영 교체 근거는 약하다."
    )
    md = "\n".join(
        [
            "# PP-OPT111~118 Warm next-dimension 실험 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: 후보 라우터, 기준가 재생성, 방향 분류 보정, 신뢰도 가중 잔차, 유사작품 proxy 스택킹 검증",
            f"- 결론: {verdict}",
            f"- 해석: {interpretation}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 30),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 30),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 60),
            "",
            "## p95 후보 상위",
            markdown_table(top_p95, result_cols, 40),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability_aggregate, stab_cols, 80),
            "",
            "## 선택 후보 시나리오별 안정성",
            markdown_table(scenario_focus, scenario_cols, 80),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PP-OPT111~118 Warm next-dimension 실험 결과</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6f8; color: #17202a; line-height: 1.58; }}
    main {{ max-width: 1280px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 40px 28px 72px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.25; }}
    h2 {{ margin: 38px 0 12px; padding-top: 20px; border-top: 1px solid #d8dee6; font-size: 22px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    .callout {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 18px; margin: 20px 0; }}
    .warn {{ border-left: 4px solid #b45309; background: #fff7ed; padding: 16px 18px; margin: 20px 0; }}
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
  <h1>PP-OPT111~118 Warm next-dimension 실험 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="warn">{html.escape(interpretation)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>안정성 검증 후보</strong>{stability_aggregate['candidate_label'].nunique()}개</div>
    <div class="panel"><strong>운영형 PP64 대비 MAPE</strong>{decision['operational_delta_vs_pp64_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP64 대비 p95</strong>{decision['operational_delta_vs_pp64_p95_APE']:+.6f}</div>
  </div>
  <h2>1. 주요 후보 test 비교</h2>
  {table_html(selected_test, list(selected_test.columns), 30)}
  <h2>2. 실험별 최선 후보</h2>
  {table_html(item_summary, item_cols, 30)}
  <h2>3. 탐색 후보 상위</h2>
  {table_html(top_new, result_cols, 60)}
  <h2>4. p95 후보 상위</h2>
  {table_html(top_p95, result_cols, 40)}
  <h2>5. 선택 후보 반복 안정성</h2>
  {table_html(stability_aggregate, stab_cols, 80)}
  <h2>6. 선택 후보 시나리오별 안정성</h2>
  {table_html(scenario_focus, scenario_cols, 80)}
  <h2>7. 실행 설정</h2>
  <pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main>
</body>
</html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    base, source, ref, labels, selected_refs, parent_config = load_inputs()
    frame = feature_frame(base, ref, labels)
    extra_cols = extra_numeric_columns(ref, labels)

    model_preds = {
        "lgbm_plain": oof_lgbm_direct(frame, extra_cols, sample_weighted=False),
        "lgbm_weighted": oof_lgbm_direct(frame, extra_cols, sample_weighted=True),
        "cat_plain": oof_catboost_direct(frame, extra_cols, sample_weighted=False),
        "cat_weighted": oof_catboost_direct(frame, extra_cols, sample_weighted=True),
        "xgb_weighted": oof_xgb_direct(frame, extra_cols),
    }
    residual_preds = {
        "lgbm_pp81_weighted": oof_residual_lgbm(frame, extra_cols, ref["pp81"].to_numpy(dtype=float), sample_weighted=True),
        "lgbm_pp110_weighted": oof_residual_lgbm(frame, extra_cols, ref["pp110_op"].to_numpy(dtype=float), sample_weighted=True),
        "lgbm_pp110_plain": oof_residual_lgbm(frame, extra_cols, ref["pp110_op"].to_numpy(dtype=float), sample_weighted=False),
    }
    stack_keys = ["pp81", "pp95_op", "pp110_op", "pp70", "pp102_op", "pp82_op", "pp110_p95", "ppv8_proxy", "svc_proxy", "l10_proxy"]
    stack_ref = ref.copy()
    stack_ref["ppv8_proxy"] = pd.to_numeric(base["ppv8_service_proxy"], errors="coerce")
    stack_ref["svc_proxy"] = pd.to_numeric(base["svc_numeric_seed_mean"], errors="coerce")
    stack_ref["l10_proxy"] = pd.to_numeric(base["l10_seq_pred_log"], errors="coerce")
    stack_preds = {
        "ridge_plain": oof_linear_stack(frame, stack_ref, stack_keys, "ridge", weighted=False),
        "ridge_weighted": oof_linear_stack(frame, stack_ref, stack_keys, "ridge", weighted=True),
        "huber_plain": oof_linear_stack(frame, stack_ref, stack_keys, "huber", weighted=False),
        "huber_weighted": oof_linear_stack(frame, stack_ref, stack_keys, "huber", weighted=True),
    }

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt111_meta_router(base, ref, frame, extra_cols))
    candidates.extend(pp_opt112_basis_regeneration(base, ref, model_preds))
    candidates.extend(pp_opt113_directional(base, ref, frame, extra_cols))
    candidates.extend(pp_opt114_confidence_residual(base, ref, residual_preds))
    candidates.extend(pp_opt115_proxy_stack(base, ref, stack_preds))
    candidates.extend(pp_opt116_hybrid_router(base, ref, labels, model_preds, stack_preds))

    predictions = pd.concat([source] + reference_candidates(base, ref) + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected_for_stability = select_candidates_for_stability(metrics, aggregate)
    stability_predictions, label_map = label_for_stability(predictions, selected_for_stability)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = select_protocol_candidates(stability_aggregate)
    predictions, decision = add_protocol_rows(predictions, decision)

    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected_for_stability = select_candidates_for_stability(metrics, aggregate)
    selected_for_stability.extend([decision["operational_protocol_candidate"], decision["p95_protocol_candidate"]])
    selected_for_stability = list(dict.fromkeys(selected_for_stability))
    stability_predictions, label_map = label_for_stability(predictions, selected_for_stability)
    label_map[decision["operational_protocol_candidate"]] = "pp118_operational_next_dimension_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp118_p95_next_dimension_challenger"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability_aggregate = attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    config = {
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
        "selected_references": selected_refs,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp103_config": str(PP103_CONFIG.relative_to(REPO)),
            "pp103_predictions": str(PP103_PREDS.relative_to(REPO)),
            "pp96_label_probabilities": str(PP96_LABELS.relative_to(REPO)),
            "pp96_helper": str(PP96_SCRIPT.relative_to(REPO)),
            "pp103_helper": str(PP103_SCRIPT.relative_to(REPO)),
            "pp71_validation_helper": str(PP71_SCRIPT.relative_to(REPO)),
        },
    }

    predictions.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    metrics.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    repeated_detail.to_csv(OUT_DIR / "repeated_validation_detail.csv", index=False)
    repeated_summary.to_csv(OUT_DIR / "repeated_validation_summary.csv", index=False)
    aggregate.to_csv(OUT_DIR / "aggregate_candidate_stability.csv", index=False)
    item_summary.to_csv(OUT_DIR / "experiment_item_summary.csv", index=False)
    fixed.to_csv(OUT_DIR / "selected_fixed_candidate_metrics.csv", index=False)
    stability_detail.to_csv(OUT_DIR / "selected_stability_repeated_detail.csv", index=False)
    stability_summary.to_csv(OUT_DIR / "selected_stability_repeated_summary.csv", index=False)
    stability_aggregate.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    model_detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in model_preds.items():
        model_detail[f"direct_{key}"] = value
    for key, value in residual_preds.items():
        model_detail[f"residual_{key}"] = value
    for key, value in stack_preds.items():
        model_detail[f"stack_{key}"] = value
    model_detail.to_csv(ARTIFACT_DIR / "next_dimension_model_prediction_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "next_dimension_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "next_dimension_result.html").write_text(report_html, encoding="utf-8")

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
                "p95_test_MAPE",
                "p95_test_p95_APE",
                "operational_pass_vs_incumbent",
                "best_family",
            ]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability_aggregate[
            [
                "candidate_label",
                "fixed_test_MAPE",
                "fixed_test_p95_APE",
                "fixed_test_delta_vs_pp64_MAPE",
                "fixed_test_delta_vs_pp64_p95_APE",
                "avg_delta_vs_pp64_MAPE",
                "avg_delta_vs_pp64_p95_APE",
                "avg_pp64_MAPE_win_rate",
                "avg_pp64_p95_win_rate",
                "replacement_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
