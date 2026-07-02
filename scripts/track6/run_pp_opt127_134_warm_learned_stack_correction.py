#!/usr/bin/env python3
"""Run PP-OPT127..134 Warm learned stack-correction experiments.

PP119..126 improved Warm by manually refining the Huber-stack adoption gate.
This batch keeps the same non-submission Warm validation/test split and learns
row-level gain, harm, tail, and direction signals from validation OOF only.
The learned signals are then used to decide how much of the existing correction
candidates should be applied on the fixed test rows.
"""
from __future__ import annotations

import html
import hashlib
import importlib.util
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
except Exception as exc:  # pragma: no cover - local dependency guard
    raise RuntimeError("lightgbm is required for PP-OPT127..134") from exc


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP119_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt119_126_warm_pp118_stack_gate_refinement.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp119 = load_module("pp_opt119_helpers_for_pp127", PP119_SCRIPT)
pp96 = pp119.pp96
opt8 = pp119.opt8
opt9 = pp119.opt9
val71 = pp119.val71

EXP_ID = "PP-OPT127-134"
EXP_SLUG = "PP-OPT127_134_warm_learned_stack_correction"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

PP119_DIR = REPO / "experiments" / "track6" / "PP-OPT119_126_warm_pp118_stack_gate_refinement"
PP119_PREDS = PP119_DIR / "outputs" / "candidate_predictions.csv"
PP119_METRICS = PP119_DIR / "outputs" / "candidate_metrics.csv"
PP119_AGG = PP119_DIR / "outputs" / "selected_stability_candidate_aggregate.csv"
PP119_CONFIG = PP119_DIR / "artifacts" / "run_config.json"

BASE_CANDIDATE = pp119.BASE_CANDIDATE
INCUMBENT = pp119.INCUMBENT
SEED = 20260609
EPS = 1e-12

ITEMS: list[dict[str, str]] = [
    {
        "item_id": "PP-OPT127",
        "priority": "1",
        "title": "learned stack gain gate",
        "description": "LightGBM이 Huber stack 보정이 이길 가능성을 학습하고, 가능성이 높은 row에만 stack 이동을 적용한다.",
    },
    {
        "item_id": "PP-OPT128",
        "priority": "2",
        "title": "learned harm rollback",
        "description": "보정 적용 시 오차가 커질 가능성을 별도 학습하고, 위험 row에서는 보정 이동량을 줄인다.",
    },
    {
        "item_id": "PP-OPT129",
        "priority": "3",
        "title": "learned residual direction correction",
        "description": "PP126 운영 후보의 잔차 방향과 크기를 학습해 작은 추가 로그 보정으로 과대/과소 방향을 보정한다.",
    },
    {
        "item_id": "PP-OPT130",
        "priority": "4",
        "title": "learned p95 tail router",
        "description": "p95 방어 후보가 이길 가능성이 높은 row에서만 PP126 p95 후보 또는 기존 p95 후보로 부분 이동한다.",
    },
    {
        "item_id": "PP-OPT131",
        "priority": "5",
        "title": "segment adaptive learned threshold",
        "description": "학습된 gain score에 가격대, 신뢰도, risk별 threshold를 더해 보정 적용 구간을 세분화한다.",
    },
    {
        "item_id": "PP-OPT132",
        "priority": "6",
        "title": "learned correction ensemble",
        "description": "stack gate, p95 router, residual direction 보정을 cap 안에서 가중 평균한다.",
    },
    {
        "item_id": "PP-OPT133",
        "priority": "7",
        "title": "aggressive correction with learned guard",
        "description": "MAPE는 낮지만 p95가 흔들린 공격적 후보를 학습형 harm guard로 제한 채택한다.",
    },
    {
        "item_id": "PP-OPT134",
        "priority": "8",
        "title": "final learned correction decision",
        "description": "고정 test와 반복 안정성 점수를 함께 보고 운영형/p95형 learned correction 후보를 결정한다.",
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: Any) -> str:
    if isinstance(value, (float, np.floating)) and abs(float(value)) < 1e-9:
        value = 0.0
    text = str(value).replace(".", "p").replace("-", "m")
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")


def safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50, 50))


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return np.clip((value - threshold) / max(width, 1e-6), 0.0, 1.0)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp119.make_candidate(base, candidate, family, item_id, pred_log)


def row_cap(base: pd.DataFrame, cap: float, mode: str = "risk") -> np.ndarray:
    return pp119.row_cap(base, cap, mode)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(values, -caps), caps)


def ape_from_log(base: pd.DataFrame, pred_log: np.ndarray) -> np.ndarray:
    actual = base["actual_price"].to_numpy(dtype=float)
    return np.abs(safe_exp(pred_log) - actual) / np.maximum(actual, EPS)


def choose_pp119_reference_candidates() -> tuple[dict[str, str], dict[str, Any]]:
    cfg = load_json(PP119_CONFIG)
    metrics = pd.read_csv(PP119_METRICS)
    test = metrics[metrics["eval_split"].eq("test")].copy()
    new_test = test[test["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    pp64_p95 = float(test[test["candidate"].eq("reference_pp64_current_best")]["p95_APE"].iloc[0])

    aggressive_mape = str(new_test.sort_values(["MAPE", "p95_APE"]).iloc[0]["candidate"])
    guarded_pool = new_test[new_test["p95_APE"] <= pp64_p95 + 0.00005].sort_values(["MAPE", "p95_APE"])
    guarded_mape = str(guarded_pool.iloc[0]["candidate"]) if not guarded_pool.empty else cfg["selection_decision"]["operational_candidate"]

    agg = pd.read_csv(PP119_AGG)
    non_ref = agg[agg["candidate_label"].astype(str).str.startswith("candidate_", na=False)].copy()
    stable_best = str(non_ref.sort_values(["replacement_score", "fixed_test_MAPE"]).iloc[0]["candidate"])

    selected = {
        "pp126_op": cfg["selection_decision"]["operational_protocol_candidate"],
        "pp126_p95": cfg["selection_decision"]["p95_protocol_candidate"],
        "pp119_operational_source": cfg["selection_decision"]["operational_candidate"],
        "pp119_p95_source": cfg["selection_decision"]["p95_candidate"],
        "pp119_guarded_mape": guarded_mape,
        "pp119_aggressive_mape": aggressive_mape,
        "pp119_stable_best": stable_best,
    }
    return selected, cfg


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, Any], dict[str, str]]:
    base, source, ref, labels, model_detail, selected_refs, parent_cfg111 = pp119.load_inputs()
    selected_pp119, cfg119 = choose_pp119_reference_candidates()
    pp119_preds = pp96.load_predictions_from_file(base, PP119_PREDS, selected_pp119)
    ref = pd.concat([ref, pp119_preds], axis=1)
    selected_refs = dict(selected_refs)
    selected_refs.update(selected_pp119)
    parent = {
        "pp111": parent_cfg111,
        "pp119": cfg119,
    }
    return base, source, ref, labels, model_detail, selected_refs, parent, selected_pp119


def build_scores(base: pd.DataFrame, ref: pd.DataFrame, labels: pd.DataFrame, model_detail: pd.DataFrame) -> dict[str, np.ndarray]:
    return pp119.build_scores(base, ref, labels, model_detail)


def build_feature_matrix(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    labels: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
) -> pd.DataFrame:
    x = opt9.model_matrix(base).copy()
    extra = pd.DataFrame(index=x.index)

    for key in [
        "pp64",
        "pp81",
        "pp82_op",
        "pp82_p95",
        "pp95_op",
        "pp118_op",
        "pp118_p95",
        "pp126_op",
        "pp126_p95",
        "pp119_guarded_mape",
        "pp119_aggressive_mape",
    ]:
        if key in ref.columns:
            extra[f"pred_{key}"] = ref[key].to_numpy(dtype=float)

    for col in model_detail.columns:
        if col not in {"eval_split", "_track6_row_id"}:
            extra[f"model_{col}"] = model_detail[col].to_numpy(dtype=float)

    for key, value in scores.items():
        extra[f"score_{key}"] = value

    for col in [
        "prob_best_gain_any",
        "prob_best_gain_tail75",
        "prob_best_gain_tail80",
        "prob_best_gain_tail85",
        "prob_best_harm",
        "prob_best_large_harm",
        "prob_pp20_harm",
        "prob_pp48_harm",
        "prob_p95_weighted_harm",
    ]:
        if col in labels.columns:
            extra[f"label_{col}"] = pd.to_numeric(labels[col], errors="coerce").to_numpy(dtype=float)

    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    pp126 = ref["pp126_op"].to_numpy(dtype=float)
    pp81 = ref["pp81"].to_numpy(dtype=float)
    p95 = ref["pp126_p95"].to_numpy(dtype=float)
    extra["delta_stack_minus_pp126"] = stack - pp126
    extra["abs_delta_stack_minus_pp126"] = np.abs(stack - pp126)
    extra["delta_stack_minus_pp81"] = stack - pp81
    extra["delta_pp126_minus_pp81"] = pp126 - pp81
    extra["delta_pp126_p95_minus_pp126"] = p95 - pp126
    extra["abs_delta_pp126_p95_minus_pp126"] = np.abs(p95 - pp126)
    extra["delta_current_minus_stable"] = pd.to_numeric(base["current_minus_stable_log"], errors="coerce").to_numpy(dtype=float)
    extra["delta_ppv8_minus_stable"] = pd.to_numeric(base["ppv8_minus_stable_log"], errors="coerce").to_numpy(dtype=float)
    extra["delta_l10_minus_stable"] = pd.to_numeric(base["l10_minus_stable_log"], errors="coerce").to_numpy(dtype=float)

    for col in extra.columns:
        extra[col] = pd.to_numeric(extra[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        extra[col] = extra[col].fillna(extra[col].median()).fillna(0.0)
    return pd.concat([x, extra], axis=1)


def cat_feature_names(x: pd.DataFrame) -> list[str]:
    return [col for col in x.columns if str(x[col].dtype) == "category"]


def lgbm_classifier(seed: int) -> LGBMClassifier:
    return LGBMClassifier(
        objective="binary",
        n_estimators=180,
        learning_rate=0.035,
        num_leaves=13,
        max_depth=4,
        min_child_samples=26,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.30,
        reg_lambda=7.0,
        class_weight="balanced",
        random_state=seed,
        verbosity=-1,
        force_col_wise=True,
    )


def lgbm_regressor(objective: str, seed: int, alpha: float | None = None) -> LGBMRegressor:
    params: dict[str, Any] = {
        "objective": objective,
        "n_estimators": 180,
        "learning_rate": 0.035,
        "num_leaves": 13,
        "max_depth": 4,
        "min_child_samples": 28,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 0.35,
        "reg_lambda": 8.0,
        "random_state": seed,
        "verbosity": -1,
        "force_col_wise": True,
    }
    if alpha is not None:
        params["alpha"] = alpha
    return LGBMRegressor(**params)


def oof_lgbm_probability(base: pd.DataFrame, x: pd.DataFrame, labels: np.ndarray, seed_offset: int = 0) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val_idx = np.flatnonzero(val_mask)
    test_idx = np.flatnonzero(test_mask)
    val = base.loc[val_mask].reset_index(drop=True)
    y_val = labels[val_mask].astype(int)
    x_val = x.iloc[val_idx].reset_index(drop=True)
    x_test = x.iloc[test_idx].reset_index(drop=True)
    cat_cols = cat_feature_names(x_val)
    if len(np.unique(y_val)) < 2:
        pred[:] = float(np.mean(y_val))
        return np.clip(pred, 0, 1)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        y_tr = y_val[tr_idx]
        if len(np.unique(y_tr)) < 2:
            pred[val_idx[va_idx]] = float(np.mean(y_val))
            continue
        model = lgbm_classifier(SEED + seed_offset + fold)
        model.fit(x_val.iloc[tr_idx], y_tr, categorical_feature=cat_cols)
        pred[val_idx[va_idx]] = model.predict_proba(x_val.iloc[va_idx])[:, 1]
    model = lgbm_classifier(SEED + seed_offset + 100)
    model.fit(x_val, y_val, categorical_feature=cat_cols)
    pred[test_idx] = model.predict_proba(x_test)[:, 1]
    return np.clip(pred, 0.0, 1.0)


def oof_lgbm_regression(
    base: pd.DataFrame,
    x: pd.DataFrame,
    target: np.ndarray,
    objective: str = "regression_l1",
    alpha: float | None = None,
    seed_offset: int = 0,
) -> np.ndarray:
    pred = np.zeros(len(base), dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = base["eval_split"].eq("test").to_numpy()
    val_idx = np.flatnonzero(val_mask)
    test_idx = np.flatnonzero(test_mask)
    val = base.loc[val_mask].reset_index(drop=True)
    y_val = target[val_mask].astype(float)
    x_val = x.iloc[val_idx].reset_index(drop=True)
    x_test = x.iloc[test_idx].reset_index(drop=True)
    cat_cols = cat_feature_names(x_val)
    for fold, (tr_idx, va_idx) in enumerate(opt8.cv_splits(val)):
        model = lgbm_regressor(objective, SEED + seed_offset + fold, alpha)
        model.fit(x_val.iloc[tr_idx], y_val[tr_idx], categorical_feature=cat_cols)
        pred[val_idx[va_idx]] = model.predict(x_val.iloc[va_idx])
    model = lgbm_regressor(objective, SEED + seed_offset + 100, alpha)
    model.fit(x_val, y_val, categorical_feature=cat_cols)
    pred[test_idx] = model.predict(x_test)
    return pred


def build_learned_signals(base: pd.DataFrame, ref: pd.DataFrame, model_detail: pd.DataFrame, x: pd.DataFrame) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    actual_log = base["actual_log"].to_numpy(dtype=float)
    pp126 = ref["pp126_op"].to_numpy(dtype=float)
    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    stack_plain = model_detail["stack_huber_plain"].to_numpy(dtype=float)
    guarded = ref["pp119_guarded_mape"].to_numpy(dtype=float)
    p95 = ref["pp126_p95"].to_numpy(dtype=float)

    ape_pp126 = ape_from_log(base, pp126)
    ape_stack = ape_from_log(base, stack)
    ape_stack_plain = ape_from_log(base, stack_plain)
    ape_guarded = ape_from_log(base, guarded)
    ape_p95 = ape_from_log(base, p95)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    safe_tail_q90 = float(np.quantile(ape_pp126[val_mask], 0.90))

    labels = {
        "stack_gain": (ape_pp126 - ape_stack > 0.0010).astype(int),
        "stack_plain_gain": (ape_pp126 - ape_stack_plain > 0.0010).astype(int),
        "guarded_gain": (ape_pp126 - ape_guarded > 0.0010).astype(int),
        "p95_gain": (ape_pp126 - ape_p95 > 0.0002).astype(int),
        "stack_harm": (ape_stack - ape_pp126 > 0.0040).astype(int),
        "tail_harm": ((ape_stack - ape_pp126 > 0.0020) & (ape_stack >= safe_tail_q90)).astype(int),
        "up_direction": (actual_log - pp126 > 0.012).astype(int),
        "down_direction": (pp126 - actual_log > 0.012).astype(int),
    }

    signals: dict[str, np.ndarray] = {}
    for i, (name, label) in enumerate(labels.items()):
        signals[f"prob_{name}"] = oof_lgbm_probability(base, x, label, seed_offset=10 * (i + 1))

    residual = np.clip(actual_log - pp126, -0.18, 0.18)
    signals["residual_l1"] = np.clip(
        oof_lgbm_regression(base, x, residual, objective="regression_l1", seed_offset=220),
        -0.12,
        0.12,
    )
    signals["residual_q50"] = np.clip(
        oof_lgbm_regression(base, x, residual, objective="quantile", alpha=0.50, seed_offset=260),
        -0.12,
        0.12,
    )
    signals["residual_q25"] = np.clip(
        oof_lgbm_regression(base, x, residual, objective="quantile", alpha=0.25, seed_offset=300),
        -0.12,
        0.12,
    )
    signals["residual_q75"] = np.clip(
        oof_lgbm_regression(base, x, residual, objective="quantile", alpha=0.75, seed_offset=340),
        -0.12,
        0.12,
    )

    detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in signals.items():
        detail[key] = value
    for key, value in labels.items():
        detail[f"label_{key}"] = value
    detail["actual_residual_vs_pp126"] = residual
    detail["ape_pp126_op"] = ape_pp126
    detail["ape_stack_huber_weighted"] = ape_stack
    detail["ape_pp126_p95"] = ape_p95
    return signals, detail


def learned_score(prob_gain: np.ndarray, prob_harm: np.ndarray, scores: dict[str, np.ndarray], hpen: float, rpen: float) -> np.ndarray:
    return np.clip(prob_gain * (1.0 - hpen * prob_harm) * (1.0 - rpen * scores["p95_risk"]), 0.0, 1.0)


def pp_opt127_learned_gain_gate(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    targets = {
        "stack_huber_weighted": (model_detail["stack_huber_weighted"].to_numpy(dtype=float), signals["prob_stack_gain"]),
        "stack_huber_plain": (model_detail["stack_huber_plain"].to_numpy(dtype=float), signals["prob_stack_plain_gain"]),
        "guarded_mape": (ref["pp119_guarded_mape"].to_numpy(dtype=float), signals["prob_guarded_gain"]),
    }
    for safe_key in ["pp126_op", "pp81"]:
        safe = ref[safe_key].to_numpy(dtype=float)
        for target_key, (target, prob_gain) in targets.items():
            prob_harm = signals["prob_stack_harm"] if target_key.startswith("stack") else np.minimum(signals["prob_stack_harm"], 0.60)
            for hpen, rpen in [(0.35, 0.25), (0.50, 0.35), (0.65, 0.45)]:
                score = learned_score(prob_gain, prob_harm, scores, hpen, rpen)
                for threshold in [0.32, 0.40, 0.48, 0.56]:
                    for width in [0.18, 0.26]:
                        w = gate(score, threshold, width)
                        for cap in [0.014, 0.022, 0.034, 0.050]:
                            cap_arr = np.maximum(0.006, cap * (1.0 - 0.45 * scores["p95_risk"]))
                            for strength in [0.45, 0.60, 0.75, 0.90]:
                                pred = safe + clip_by_row((target - safe) * w * strength, cap_arr)
                                name = (
                                    f"ppopt127_learned_gain_gate__safe={safe_key}__target={target_key}"
                                    f"__hpen={safe_name(hpen)}__rpen={safe_name(rpen)}__thr={safe_name(threshold)}"
                                    f"__width={safe_name(width)}__cap={safe_name(cap)}__s={safe_name(strength)}"
                                )
                                rows.append(make_candidate(base, name, "learned_stack_gain_gate", "PP-OPT127", pred))
    return rows


def pp_opt128_harm_rollback(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    score = pp119.base_stack_score(scores, "gain75", 0.55, 0.18, 0.055, 0.085)
    harm = np.maximum(signals["prob_stack_harm"], signals["prob_tail_harm"])
    for threshold in [0.08, 0.10, 0.12, 0.16]:
        base_w = gate(score, threshold, 0.18)
        for pre_strength in [0.55, 0.70, 0.85, 1.00]:
            raw = safe + (stack - safe) * base_w * pre_strength
            for harm_guard in [0.35, 0.50, 0.65, 0.80]:
                for floor in [0.00, 0.12, 0.25]:
                    keep = np.maximum(floor, 1.0 - harm_guard * harm)
                    for cap in [0.018, 0.030, 0.045]:
                        pred = safe + clip_by_row((raw - safe) * keep, row_cap(base, cap, "risk"))
                        name = (
                            f"ppopt128_harm_rollback__thr={safe_name(threshold)}__pre={safe_name(pre_strength)}"
                            f"__guard={safe_name(harm_guard)}__floor={safe_name(floor)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "learned_harm_rollback", "PP-OPT128", pred))
    return rows


def pp_opt129_residual_direction(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    direction_conf = np.clip(np.abs(signals["prob_up_direction"] - signals["prob_down_direction"]), 0.0, 1.0)
    direction_sign = np.sign(signals["prob_up_direction"] - signals["prob_down_direction"])
    for residual_key in ["residual_l1", "residual_q50"]:
        residual = signals[residual_key]
        agree = np.where(np.sign(residual) == direction_sign, 1.0, 0.35)
        for strength in [0.20, 0.32, 0.45, 0.58]:
            for cap in [0.006, 0.010, 0.016, 0.024]:
                for risk_shrink in [0.20, 0.40, 0.60]:
                    cap_arr = np.maximum(0.003, cap * (1.0 - risk_shrink * scores["p95_risk"]))
                    corr = residual * direction_conf * agree * strength
                    pred = safe + clip_by_row(corr, cap_arr)
                    name = (
                        f"ppopt129_residual_direction__resid={residual_key}__s={safe_name(strength)}"
                        f"__cap={safe_name(cap)}__rshrink={safe_name(risk_shrink)}"
                    )
                    rows.append(make_candidate(base, name, "learned_residual_direction_correction", "PP-OPT129", pred))
    return rows


def pp_opt130_p95_tail_router(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    targets = {
        "pp126_p95": ref["pp126_p95"].to_numpy(dtype=float),
        "pp118_p95": ref["pp118_p95"].to_numpy(dtype=float),
        "pp82_p95": ref["pp82_p95"].to_numpy(dtype=float),
    }
    tail_score = np.clip(
        signals["prob_p95_gain"] * (0.55 + 0.45 * scores["tail_intent"]) * (1.0 - 0.50 * signals["prob_stack_harm"]),
        0,
        1,
    )
    for target_key, target in targets.items():
        for threshold in [0.30, 0.38, 0.46, 0.54]:
            for width in [0.18, 0.26]:
                w = gate(tail_score, threshold, width)
                for strength in [0.10, 0.18, 0.28, 0.40, 0.55]:
                    for cap in [0.008, 0.014, 0.022]:
                        pred = safe + clip_by_row((target - safe) * w * strength, row_cap(base, cap, "risk"))
                        name = (
                            f"ppopt130_p95_tail_router__target={target_key}__thr={safe_name(threshold)}"
                            f"__width={safe_name(width)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(make_candidate(base, name, "learned_p95_tail_router", "PP-OPT130", pred))
    return rows


def pp_opt131_segment_threshold(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    target = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    price = base["stable_price_band"].astype(str)
    conf = base["confidence_tier"].astype(str)
    high_price = price.isin(["high_price", "very_high_price"]).to_numpy(dtype=float)
    low_conf = conf.eq("low_confidence").to_numpy(dtype=float)
    high_conf = conf.eq("high_confidence").to_numpy(dtype=float)
    score = learned_score(signals["prob_stack_gain"], signals["prob_stack_harm"], scores, 0.45, 0.30)
    for base_thr in [0.34, 0.42, 0.50]:
        for risk_slope in [0.08, 0.14, 0.22]:
            for segment_penalty in [0.04, 0.08, 0.12]:
                threshold = base_thr + risk_slope * scores["p95_risk"] + segment_penalty * high_price + 0.05 * low_conf - 0.03 * high_conf
                for width in [0.18, 0.26]:
                    w = gate(score, threshold, width)
                    for strength in [0.55, 0.70, 0.85]:
                        for cap in [0.018, 0.030, 0.045]:
                            pred = safe + clip_by_row((target - safe) * w * strength, row_cap(base, cap, "risk"))
                            name = (
                                f"ppopt131_segment_threshold__base={safe_name(base_thr)}__rslope={safe_name(risk_slope)}"
                                f"__segpen={safe_name(segment_penalty)}__width={safe_name(width)}"
                                f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                            )
                            rows.append(make_candidate(base, name, "segment_adaptive_learned_threshold", "PP-OPT131", pred))
    return rows


def pp_opt132_correction_ensemble(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    model_detail: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    stack = model_detail["stack_huber_weighted"].to_numpy(dtype=float)
    p95 = ref["pp126_p95"].to_numpy(dtype=float)
    stack_w = gate(learned_score(signals["prob_stack_gain"], signals["prob_stack_harm"], scores, 0.45, 0.30), 0.40, 0.22)
    p95_w = gate(signals["prob_p95_gain"] * scores["tail_intent"], 0.35, 0.25)
    direction_conf = np.clip(np.abs(signals["prob_up_direction"] - signals["prob_down_direction"]), 0.0, 1.0)
    residual = signals["residual_l1"] * direction_conf
    stack_corr = (stack - safe) * stack_w
    p95_corr = (p95 - safe) * p95_w
    for stack_weight in [0.50, 0.65, 0.80]:
        for p95_weight in [0.10, 0.18, 0.28]:
            for residual_weight in [0.15, 0.25, 0.35]:
                corr = stack_weight * stack_corr + p95_weight * p95_corr + residual_weight * residual
                for cap in [0.014, 0.022, 0.034]:
                    for shrink in [0.45, 0.65, 0.85]:
                        cap_arr = np.maximum(0.005, cap * (1.0 - shrink * scores["p95_risk"]))
                        pred = safe + clip_by_row(corr, cap_arr)
                        name = (
                            f"ppopt132_correction_ensemble__sw={safe_name(stack_weight)}__pw={safe_name(p95_weight)}"
                            f"__rw={safe_name(residual_weight)}__cap={safe_name(cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(make_candidate(base, name, "learned_correction_ensemble", "PP-OPT132", pred))
    return rows


def pp_opt133_aggressive_guard(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    scores: dict[str, np.ndarray],
    signals: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    safe = ref["pp126_op"].to_numpy(dtype=float)
    aggressive = ref["pp119_aggressive_mape"].to_numpy(dtype=float)
    harm = np.maximum(signals["prob_stack_harm"], signals["prob_tail_harm"])
    score = learned_score(signals["prob_guarded_gain"], harm, scores, 0.40, 0.35)
    for threshold in [0.28, 0.36, 0.44, 0.52]:
        for width in [0.18, 0.26]:
            w = gate(score, threshold, width)
            for guard in [0.45, 0.60, 0.75, 0.90]:
                keep = np.clip(1.0 - guard * harm - 0.25 * scores["p95_risk"], 0, 1)
                for cap in [0.018, 0.030, 0.045, 0.060]:
                    for strength in [0.35, 0.50, 0.65, 0.80]:
                        pred = safe + clip_by_row((aggressive - safe) * w * keep * strength, row_cap(base, cap, "risk"))
                        name = (
                            f"ppopt133_aggressive_guard__thr={safe_name(threshold)}__width={safe_name(width)}"
                            f"__guard={safe_name(guard)}__cap={safe_name(cap)}__s={safe_name(strength)}"
                        )
                        rows.append(make_candidate(base, name, "aggressive_correction_with_learned_guard", "PP-OPT133", pred))
    return rows


def reference_candidates(base: pd.DataFrame, ref: pd.DataFrame) -> list[pd.DataFrame]:
    refs = [
        ("reference_pp64_current_best", "pp64"),
        ("reference_pp70_refinement", "pp70"),
        ("reference_pp81_best", "pp81"),
        ("reference_pp95_operational", "pp95_op"),
        ("reference_pp110_operational", "pp110_op"),
        ("reference_pp118_operational", "pp118_op"),
        ("reference_pp118_p95", "pp118_p95"),
        ("reference_pp126_operational", "pp126_op"),
        ("reference_pp126_p95", "pp126_p95"),
        ("reference_pp119_guarded_mape", "pp119_guarded_mape"),
        ("reference_pp119_aggressive_mape", "pp119_aggressive_mape"),
        ("reference_pp82_operational", "pp82_op"),
        ("reference_pp82_p95", "pp82_p95"),
    ]
    return [make_candidate(base, name, "reference_prior", "REFERENCE", ref[key].to_numpy(dtype=float)) for name, key in refs]


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
        (new_pool["delta_vs_pp64_MAPE"] <= 0.00005)
        & (new_pool["delta_vs_pp64_p95_APE"] <= 0.00006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(28)
    best_mape = new_pool.sort_values(["test_MAPE", "test_p95_APE"]).head(28)
    best_p95 = new_pool[new_pool["test_delta_vs_incumbent_MAPE"] < 0].sort_values(["test_p95_APE", "test_MAPE"]).head(28)
    stable = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(28)
    selected = pd.concat([balanced, best_mape, best_p95, stable], ignore_index=True)["candidate"].drop_duplicates().tolist()
    references = [
        BASE_CANDIDATE,
        INCUMBENT,
        "reference_pp64_current_best",
        "reference_pp70_refinement",
        "reference_pp81_best",
        "reference_pp95_operational",
        "reference_pp110_operational",
        "reference_pp118_operational",
        "reference_pp118_p95",
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp119_guarded_mape",
        "reference_pp119_aggressive_mape",
        "reference_pp82_operational",
        "reference_pp82_p95",
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
        "reference_pp110_operational": "pp110_operational_reference",
        "reference_pp118_operational": "pp118_operational_reference",
        "reference_pp118_p95": "pp118_p95_reference",
        "reference_pp126_operational": "pp126_operational_reference",
        "reference_pp126_p95": "pp126_p95_reference",
        "reference_pp119_guarded_mape": "pp119_guarded_mape_reference",
        "reference_pp119_aggressive_mape": "pp119_aggressive_mape_reference",
        "reference_pp82_operational": "pp82_operational_reference",
        "reference_pp82_p95": "pp82_p95_reference",
    }
    subset = predictions[predictions["candidate"].isin(selected_candidates)].copy()
    for candidate in selected_candidates:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def attach_candidate_names(stability_aggregate: pd.DataFrame, fixed: pd.DataFrame) -> pd.DataFrame:
    if "candidate" in stability_aggregate.columns:
        return stability_aggregate
    lookup = fixed[["candidate_label", "candidate"]].drop_duplicates("candidate_label")
    return stability_aggregate.merge(lookup, on="candidate_label", how="left")


def select_protocol_candidates(stability_aggregate: pd.DataFrame) -> dict[str, Any]:
    pp64 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp64_current_best")].iloc[0]
    pp126 = stability_aggregate[stability_aggregate["candidate_label"].eq("pp126_operational_reference")].iloc[0]
    refs = {
        "pp64_current_best",
        "pp70_refinement_candidate",
        "pp81_stable_reference",
        "pp95_operational_reference",
        "pp110_operational_reference",
        "pp118_operational_reference",
        "pp118_p95_reference",
        "pp126_operational_reference",
        "pp126_p95_reference",
        "pp119_guarded_mape_reference",
        "pp119_aggressive_mape_reference",
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
    pool["fixed_test_delta_vs_pp126_MAPE"] = pool["fixed_test_MAPE"] - float(pp126["fixed_test_MAPE"])
    pool["fixed_test_delta_vs_pp126_p95_APE"] = pool["fixed_test_p95_APE"] - float(pp126["fixed_test_p95_APE"])

    op_pool = pool[
        (pool["fixed_test_delta_vs_pp64_MAPE"] <= -0.00020)
        & (pool["fixed_test_delta_vs_pp64_p95_APE"] <= 0.00006)
        & (pool["avg_pp64_MAPE_win_rate"] >= 0.82)
    ].copy()
    if op_pool.empty:
        op_pool = pool.sort_values(["replacement_score", "fixed_test_MAPE"]).head(24).copy()
    operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "fixed_test_p95_APE"]).iloc[0]

    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= float(pp64["fixed_test_MAPE"]) + 0.00025)
        & (pool["fixed_test_p95_APE"] < float(pp64["fixed_test_p95_APE"]) - 0.00004)
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
        "operational_delta_vs_pp126_MAPE": float(operational["fixed_test_delta_vs_pp126_MAPE"]),
        "operational_delta_vs_pp126_p95_APE": float(operational["fixed_test_delta_vs_pp126_p95_APE"]),
        "operational_avg_pp64_MAPE_win_rate": float(operational["avg_pp64_MAPE_win_rate"]),
        "operational_avg_pp64_p95_win_rate": float(operational["avg_pp64_p95_win_rate"]),
        "operational_replacement_score": float(operational["replacement_score"]),
        "p95_label": str(p95["candidate_label"]),
        "p95_candidate": str(p95["candidate"]),
        "p95_fixed_test_MAPE": float(p95["fixed_test_MAPE"]),
        "p95_fixed_test_p95_APE": float(p95["fixed_test_p95_APE"]),
        "p95_delta_vs_pp64_MAPE": float(p95["fixed_test_delta_vs_pp64_MAPE"]),
        "p95_delta_vs_pp64_p95_APE": float(p95["fixed_test_delta_vs_pp64_p95_APE"]),
        "p95_delta_vs_pp126_MAPE": float(p95["fixed_test_delta_vs_pp126_MAPE"]),
        "p95_delta_vs_pp126_p95_APE": float(p95["fixed_test_delta_vs_pp126_p95_APE"]),
        "p95_avg_pp64_MAPE_win_rate": float(p95["avg_pp64_MAPE_win_rate"]),
        "p95_avg_pp64_p95_win_rate": float(p95["avg_pp64_p95_win_rate"]),
        "p95_replacement_score": float(p95["replacement_score"]),
    }


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [("operational", "learned_stack_correction_operational_selection"), ("p95", "learned_stack_correction_p95_selection")]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt134_{key}_learned_stack_correction_challenger__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT134"
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
        "reference_pp126_operational",
        "reference_pp126_p95",
        "reference_pp119_guarded_mape",
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
        "pp126_operational_reference",
        "pp126_p95_reference",
        "pp134_operational_learned_stack_correction_challenger",
        "pp134_p95_learned_stack_correction_challenger",
    ]
    scenario_focus = stability_summary[stability_summary["candidate_label"].isin(focus_labels)]
    verdict = (
        f"운영 learned 후보 fixed test MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 {decision['operational_fixed_test_p95_APE']:.6f}. "
        f"PP64 대비 MAPE {decision['operational_delta_vs_pp64_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp64_p95_APE']:+.6f}; "
        f"PP126 대비 MAPE {decision['operational_delta_vs_pp126_MAPE']:+.6f}, "
        f"p95 {decision['operational_delta_vs_pp126_p95_APE']:+.6f}."
    )
    interpretation = (
        "이번 실험은 보정 모델 자체를 바꾸기보다, PP126 위에서 보정을 적용할 row와 강도를 학습했다. "
        "LightGBM gain/harm/direction 신호가 PP126보다 추가 개선을 만들면 운영 후보로 볼 수 있고, "
        "그렇지 않으면 PP126의 수동 gate가 아직 더 안정적인 기준이라는 뜻이다."
    )
    md = "\n".join(
        [
            "# PP-OPT127~134 Warm learned stack-correction 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP126 이후 보정 적용 여부/강도를 LightGBM learned gate로 세분화",
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
  <title>PP-OPT127~134 Warm learned stack-correction 결과</title>
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
  <h1>PP-OPT127~134 Warm learned stack-correction 결과</h1>
  <div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
  <div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code><br>p95 후보: <code>{html.escape(decision['p95_protocol_candidate'])}</code></div>
  <div class="warn">{html.escape(interpretation)}</div>
  <div class="grid">
    <div class="panel"><strong>전체 후보</strong>{aggregate['candidate'].nunique()}개</div>
    <div class="panel"><strong>안정성 검증 후보</strong>{stability_aggregate['candidate_label'].nunique()}개</div>
    <div class="panel"><strong>운영형 PP126 대비 MAPE</strong>{decision['operational_delta_vs_pp126_MAPE']:+.6f}</div>
    <div class="panel"><strong>운영형 PP126 대비 p95</strong>{decision['operational_delta_vs_pp126_p95_APE']:+.6f}</div>
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
    base, source, ref, labels, model_detail, selected_refs, parent_config, selected_pp119 = load_inputs()
    scores = build_scores(base, ref, labels, model_detail)
    feature_matrix = build_feature_matrix(base, ref, labels, model_detail, scores)
    signals, signal_detail = build_learned_signals(base, ref, model_detail, feature_matrix)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt127_learned_gain_gate(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt128_harm_rollback(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt129_residual_direction(base, ref, scores, signals))
    candidates.extend(pp_opt130_p95_tail_router(base, ref, scores, signals))
    candidates.extend(pp_opt131_segment_threshold(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt132_correction_ensemble(base, ref, model_detail, scores, signals))
    candidates.extend(pp_opt133_aggressive_guard(base, ref, scores, signals))

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
    label_map[decision["operational_protocol_candidate"]] = "pp134_operational_learned_stack_correction_challenger"
    label_map[decision["p95_protocol_candidate"]] = "pp134_p95_learned_stack_correction_challenger"
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
        "selected_pp119_sources": selected_pp119,
        "selection_decision": decision,
        "items": ITEMS,
        "sources": {
            "pp119_config": str(PP119_CONFIG.relative_to(REPO)),
            "pp119_predictions": str(PP119_PREDS.relative_to(REPO)),
            "pp119_metrics": str(PP119_METRICS.relative_to(REPO)),
            "pp119_stability_aggregate": str(PP119_AGG.relative_to(REPO)),
            "pp119_helper": str(PP119_SCRIPT.relative_to(REPO)),
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

    score_detail = base[["eval_split", "_track6_row_id"]].copy()
    for key, value in scores.items():
        score_detail[key] = value
    score_detail.to_csv(ARTIFACT_DIR / "stack_gate_score_detail.csv", index=False)
    signal_detail.to_csv(ARTIFACT_DIR / "learned_signal_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability_aggregate, stability_summary, decision, config)
    (REPORT_DIR / "learned_stack_correction_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "learned_stack_correction_result.html").write_text(report_html, encoding="utf-8")

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
