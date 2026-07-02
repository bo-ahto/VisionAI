#!/usr/bin/env python3
"""Run PP-OPT247..252 Warm PP246 residual-direction gated correction experiments."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover - optional dependency
    LGBMClassifier = None

try:
    from catboost import CatBoostClassifier
except Exception:  # pragma: no cover - optional dependency
    CatBoostClassifier = None


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP241_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt241_246_warm_pp234_p95_constrained_support_and_basis_regeneration.py"
PP241_DIR = REPO / "experiments" / "track6" / "PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration"
PP241_PREDICTIONS = PP241_DIR / "outputs" / "candidate_predictions.csv"
PP241_CONFIG = PP241_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT247-252"
EXP_SLUG = "PP-OPT247_252_warm_pp246_residual_direction_gated_correction"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

ITEMS = [
    {
        "item_id": "PP-OPT247",
        "priority": "1",
        "title": "residual direction probability gate",
        "description": "validation residual sign classifier로 보정 방향을 먼저 고른 뒤 후보 이동량을 제한 적용.",
    },
    {
        "item_id": "PP-OPT248",
        "priority": "2",
        "title": "asymmetric quantile residual cap",
        "description": "잔차 보정의 상향 cap과 하향 cap을 quantile width/risk에 따라 따로 적용.",
    },
    {
        "item_id": "PP-OPT249",
        "priority": "3",
        "title": "direction-gated residual correction",
        "description": "잔차 회귀값이 방향 분류 확신과 일치할 때만 Huber/Ridge/LightGBM 계열 보정을 적용.",
    },
    {
        "item_id": "PP-OPT250",
        "priority": "4",
        "title": "segment residual-direction router",
        "description": "구간별 validation 성과와 잔차 방향을 함께 사용해 후보별 이동을 제한 라우팅.",
    },
    {
        "item_id": "PP-OPT251",
        "priority": "5",
        "title": "direction residual plus p95 support ensemble",
        "description": "방향 gate 잔차 보정과 p95 recovery/support 이동을 신뢰도 가중 평균으로 결합.",
    },
    {
        "item_id": "PP-OPT252",
        "priority": "6",
        "title": "final PP246 gated correction decision",
        "description": "PP246 대비 MAPE, p95 win rate, replacement score 제약을 만족하는 후보를 최종 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp241 = load_module("pp_opt241_helpers_for_pp247", PP241_SCRIPT)
pp235 = pp241.pp235
pp229 = pp241.pp229
pp199 = pp241.pp199
pp187 = pp241.pp187
pp161 = pp241.pp161
opt8 = pp241.opt8
val71 = pp241.val71

BASE_CANDIDATE = pp241.BASE_CANDIDATE
INCUMBENT_CANDIDATE = pp241.INCUMBENT_CANDIDATE
PP64_CANDIDATE = pp241.PP64_CANDIDATE
PP70_CANDIDATE = pp241.PP70_CANDIDATE
PP126_CANDIDATE = pp241.PP126_CANDIDATE
PP148_CANDIDATE = pp241.PP148_CANDIDATE
PP148_P95_CANDIDATE = pp241.PP148_P95_CANDIDATE

CAT_COLS = pp241.CAT_COLS
BASE_NUM_COLS = pp241.NUM_COLS
EXTRA_NUM_COLS = [
    "pp246_minus_pp234_abs",
    "p95_recovery_delta_abs",
    "operational_delta_abs",
    "p95_guarded_delta_abs",
    "p95_extreme_delta_abs",
    "pp246_log_centered",
    "qwidth_rank",
    "component_spread_rank",
    "model_gap_rank",
]
NUM_COLS = list(dict.fromkeys(BASE_NUM_COLS + EXTRA_NUM_COLS))


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp241.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp229.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp241.clip_by_row(values, caps)


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    return pp199.rank01(values)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp241.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    return (
        pd.read_csv(PP241_PREDICTIONS),
        json.loads(PP241_CONFIG.read_text(encoding="utf-8")),
    )


def make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def model_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("cat", make_ohe(), CAT_COLS),
            ("num", StandardScaler(), NUM_COLS),
        ],
        remainder="drop",
    )


def make_classifier(kind: str, value: float, seed: int) -> Pipeline:
    if kind == "logistic":
        clf = LogisticRegression(C=float(value), max_iter=1000, class_weight="balanced", solver="lbfgs", random_state=seed)
    elif kind == "hist_gbc":
        clf = HistGradientBoostingClassifier(max_iter=int(value), learning_rate=0.035, max_leaf_nodes=8, l2_regularization=0.08, random_state=seed)
    elif kind == "lgbm" and LGBMClassifier is not None:
        clf = LGBMClassifier(
            n_estimators=int(value),
            learning_rate=0.025,
            num_leaves=7,
            min_child_samples=24,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=2.0,
            class_weight="balanced",
            random_state=seed,
            verbose=-1,
        )
    elif kind == "cat" and CatBoostClassifier is not None:
        clf = CatBoostClassifier(
            iterations=int(value),
            learning_rate=0.025,
            depth=2,
            l2_leaf_reg=8.0,
            loss_function="Logloss",
            auto_class_weights="Balanced",
            random_seed=seed,
            verbose=False,
        )
    else:
        raise RuntimeError(f"Classifier not available: {kind}")
    return Pipeline([("prep", model_preprocessor()), ("clf", clf)])


def crossfit_binary_prob(features: pd.DataFrame, val_mask: np.ndarray, y_val: np.ndarray, model_factory: Callable[[], Any], seed: int) -> np.ndarray:
    X_val = features.loc[val_mask]
    X_all = features
    out = np.zeros(len(features), dtype=float)
    oof = np.zeros(len(X_val), dtype=float)
    if len(np.unique(y_val)) < 2:
        out[:] = float(y_val[0])
        return out
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    for train_idx, hold_idx in kfold.split(X_val):
        y_train = y_val[train_idx]
        if len(np.unique(y_train)) < 2:
            oof[hold_idx] = float(y_train[0])
            continue
        model = model_factory()
        model.fit(X_val.iloc[train_idx], y_train)
        classes = list(model.named_steps["clf"].classes_)
        proba = model.predict_proba(X_val.iloc[hold_idx])
        pos_idx = classes.index(1) if 1 in classes else None
        oof[hold_idx] = proba[:, pos_idx] if pos_idx is not None else 0.0
    full = model_factory()
    full.fit(X_val, y_val)
    classes = list(full.named_steps["clf"].classes_)
    proba = full.predict_proba(X_all)
    pos_idx = classes.index(1) if 1 in classes else None
    out[:] = proba[:, pos_idx] if pos_idx is not None else 0.0
    out[np.where(val_mask)[0]] = oof
    return np.nan_to_num(out, nan=0.5, posinf=0.5, neginf=0.5)


def build_features(
    base: pd.DataFrame,
    pp246: np.ndarray,
    pp234: np.ndarray,
    operational: np.ndarray,
    p95_guarded: np.ndarray,
    p95_recovery: np.ndarray,
    p95_extreme: np.ndarray,
) -> pd.DataFrame:
    frame = pp235.build_model_features(base, pp246, operational, operational, p95_guarded, p95_recovery)
    frame["pp246_minus_pp234_abs"] = np.abs(pp246 - pp234)
    frame["p95_recovery_delta_abs"] = np.abs(p95_recovery - pp246)
    frame["operational_delta_abs"] = np.abs(operational - pp246)
    frame["p95_guarded_delta_abs"] = np.abs(p95_guarded - pp246)
    frame["p95_extreme_delta_abs"] = np.abs(p95_extreme - pp246)
    frame["pp246_log_centered"] = pp246 - float(np.nanmedian(pp246))
    frame["qwidth_rank"] = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    frame["component_spread_rank"] = rank01(pd.to_numeric(base["component_prediction_spread"], errors="coerce"))
    frame["model_gap_rank"] = rank01(np.abs(p95_recovery - pp246))
    for col in NUM_COLS:
        if col not in frame.columns:
            frame[col] = 0.0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return frame


def asymmetric_cap(
    base: pd.DataFrame,
    correction: np.ndarray,
    target: np.ndarray,
    source: np.ndarray,
    up_cap: float,
    down_cap: float,
    q_shrink: float,
    risk_shrink: float,
    floor: float = 0.000006,
) -> np.ndarray:
    q_rank = rank01(pd.to_numeric(base["quantile_width"], errors="coerce"))
    risk = pp199.row_risk(base, source, target)
    directional_base = np.where(correction >= 0.0, up_cap, down_cap)
    cap = directional_base * (1.0 - q_shrink * q_rank) * (1.0 - risk_shrink * np.clip(risk, 0.0, 1.0))
    return np.clip(cap, floor, directional_base)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def candidate_from_correction(base: pd.DataFrame, source: np.ndarray, correction: np.ndarray, name: str, family: str, item_id: str, cap: np.ndarray) -> pd.DataFrame:
    pred = source + clip_by_row(correction, cap)
    return make_candidate(base, name, family, item_id, pred)


def reference_predictions(previous: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    support = config["support_candidates"]
    prior = config["prior_decision"]
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["selection_decision"]
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp216_p95_recovery"],
        support["pp222_balanced"],
        support["pp222_operational"],
        support["pp222_p95_guarded"],
        prior["balanced_protocol_candidate"],
        prior["operational_protocol_candidate"],
        prior["mape_challenger_protocol_candidate"],
        pp234["balanced_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp240["p95_extreme_protocol_candidate"],
        pp246["balanced_protocol_candidate"],
        pp246["operational_protocol_candidate"],
        pp246["mape_challenger_protocol_candidate"],
        pp246["p95_recovery_protocol_candidate"],
        pp246["p95_guarded_protocol_candidate"],
        pp246["p95_extreme_protocol_candidate"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def build_direction_probs(base: pd.DataFrame, features: pd.DataFrame, pp246: np.ndarray) -> dict[str, np.ndarray]:
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - pp246
    y_val = (residual[val_mask] > 0.0).astype(int)
    specs: list[tuple[str, str, float, int]] = [
        ("log_c0p2_seed17", "logistic", 0.20, 17),
        ("log_c0p6_seed29", "logistic", 0.60, 29),
        ("log_c1p4_seed41", "logistic", 1.40, 41),
        ("hist35_seed17", "hist_gbc", 35, 17),
        ("hist70_seed29", "hist_gbc", 70, 29),
    ]
    if LGBMClassifier is not None:
        specs.extend([("lgbm40_seed17", "lgbm", 40, 17), ("lgbm80_seed29", "lgbm", 80, 29)])
    if CatBoostClassifier is not None:
        specs.append(("cat50_seed17", "cat", 50, 17))
    out: dict[str, np.ndarray] = {}
    for label, kind, value, seed in specs:
        out[label] = crossfit_binary_prob(features, val_mask, y_val, lambda k=kind, v=value, s=seed: make_classifier(k, v, s), seed)
    return out


def build_residual_predictions(base: pd.DataFrame, features: pd.DataFrame, pp246: np.ndarray) -> dict[str, np.ndarray]:
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - pp246
    y_val = residual[val_mask]
    specs: list[tuple[str, Callable[[], Any], int]] = [
        ("ridge_2p0", lambda: pp241.make_linear_model("ridge", 2.0), 101),
        ("ridge_6p0", lambda: pp241.make_linear_model("ridge", 6.0), 103),
        ("huber_1p15", lambda: pp241.make_linear_model("huber", 1.15), 107),
        ("huber_1p70", lambda: pp241.make_linear_model("huber", 1.70), 109),
        ("hist_gbr_60", lambda: pp241.make_tree_model("hist_gbr", 20260610, 60), 113),
    ]
    if pp241.LGBMRegressor is not None:
        specs.append(("lgbm_60", lambda: pp241.make_tree_model("lgbm", 20260610, 60), 127))
    if pp241.CatBoostRegressor is not None:
        specs.append(("cat_60", lambda: pp241.make_tree_model("cat", 20260610, 60), 131))
    out: dict[str, np.ndarray] = {}
    for label, factory, seed in specs:
        out[label] = pp241.crossfit_regression_prediction(features, val_mask, y_val, factory, seed)
    return out


def pp_opt247_direction_gate(
    base: pd.DataFrame,
    pp246: np.ndarray,
    direction_probs: dict[str, np.ndarray],
    target_logs: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for prob_name, prob_up in direction_probs.items():
        for target_name, target in target_logs.items():
            delta = target - pp246
            aligned = direction_alignment(delta, prob_up)
            risk = pp199.row_risk(base, pp246, target)
            for threshold in [0.12, 0.24]:
                conf = confidence_weight(prob_up, threshold) * aligned
                for strength in [0.25, 0.55]:
                    for basecap in [0.00002, 0.00006, 0.00010]:
                        for shrink in [0.60, 0.85]:
                            cap = np.clip(basecap * (1.0 - shrink * risk), 0.000006, basecap)
                            correction = delta * conf * strength
                            name = (
                                f"ppopt247_direction_gate__prob={prob_name}__target={target_name}"
                                f"__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                            )
                            rows.append(candidate_from_correction(base, pp246, correction, name, "pp246_residual_direction_gate", "PP-OPT247", cap))
    return rows


def pp_opt248_asymmetric_quantile_cap(
    base: pd.DataFrame,
    pp246: np.ndarray,
    residuals: dict[str, np.ndarray],
    p95_recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for resid_name, residual in residuals.items():
        target = pp246 + residual
        for strength in [0.04, 0.08, 0.14]:
            correction = residual * strength
            for up_cap, down_cap in [(0.00004, 0.00002), (0.00006, 0.00003), (0.00010, 0.00005), (0.00006, 0.00006)]:
                for q_shrink in [0.30, 0.55]:
                    cap = asymmetric_cap(base, correction, p95_recovery, pp246, up_cap, down_cap, q_shrink, risk_shrink=0.70)
                    name = (
                        f"ppopt248_asym_quantile_cap__resid={resid_name}__s={safe_name(strength)}"
                        f"__up={safe_name(up_cap)}__down={safe_name(down_cap)}__qshrink={safe_name(q_shrink)}"
                    )
                    rows.append(candidate_from_correction(base, pp246, correction, name, "pp246_asymmetric_quantile_residual_cap", "PP-OPT248", cap))
    return rows


def pp_opt249_direction_gated_residual(
    base: pd.DataFrame,
    pp246: np.ndarray,
    direction_probs: dict[str, np.ndarray],
    residuals: dict[str, np.ndarray],
    p95_recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for prob_name, prob_up in list(direction_probs.items())[:5]:
        for resid_name, residual in list(residuals.items())[:5]:
            aligned = direction_alignment(residual, prob_up)
            for threshold in [0.10, 0.22]:
                conf = confidence_weight(prob_up, threshold) * aligned
                for strength in [0.08, 0.14]:
                    correction = residual * conf * strength
                    for up_cap, down_cap in [(0.00004, 0.00002), (0.00008, 0.00004)]:
                        cap = asymmetric_cap(base, correction, p95_recovery, pp246, up_cap, down_cap, q_shrink=0.45, risk_shrink=0.75)
                        name = (
                            f"ppopt249_direction_residual__prob={prob_name}__resid={resid_name}"
                            f"__thr={safe_name(threshold)}__s={safe_name(strength)}__up={safe_name(up_cap)}__down={safe_name(down_cap)}"
                        )
                        rows.append(candidate_from_correction(base, pp246, correction, name, "pp246_direction_gated_residual", "PP-OPT249", cap))
    return rows


def segment_best_target(
    base: pd.DataFrame,
    pp246: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
    cols: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    actual = base["actual_price"].to_numpy(dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    val = base.loc[val_mask].copy()
    full_key = base[cols].astype(str).agg("||".join, axis=1)
    val_key = val[cols].astype(str).agg("||".join, axis=1)
    candidate_order = ["base"] + list(candidate_logs.keys())
    logs = {"base": pp246, **candidate_logs}
    apes = {name: pp235.ape_from_log(log, actual) for name, log in logs.items()}
    residual = base["actual_log"].to_numpy(dtype=float) - pp246
    best_by_group: dict[str, tuple[str, float, int, float]] = {}
    for key in sorted(val_key.unique()):
        idx = np.where(val_mask)[0][val_key.to_numpy() == key]
        means = {name: float(apes[name][idx].mean()) for name in candidate_order}
        best = min(means, key=means.get)
        gain = means["base"] - means[best]
        direction = float(np.sign(np.nanmean(residual[idx])))
        best_by_group[key] = (best, gain, len(idx), direction)
    target = np.array(pp246, copy=True)
    gain_arr = np.zeros(len(base), dtype=float)
    count_arr = np.zeros(len(base), dtype=float)
    direction_arr = np.zeros(len(base), dtype=float)
    for i, key in enumerate(full_key):
        best, gain, count, direction = best_by_group.get(key, ("base", 0.0, 0, 0.0))
        target[i] = logs[best][i]
        gain_arr[i] = gain
        count_arr[i] = count
        direction_arr[i] = direction
    return target, gain_arr, count_arr * np.sign(direction_arr)


def pp_opt250_segment_direction_router(
    base: pd.DataFrame,
    pp246: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    segment_sets = [
        ("price_conf", ["stable_price_band", "confidence_tier"]),
        ("price_qwidth", ["stable_price_band", "qwidth_band"]),
        ("price_medium", ["stable_price_band", "medium_support_bucket"]),
        ("price_conf_qwidth", ["stable_price_band", "confidence_tier", "qwidth_band"]),
    ]
    for seg_name, cols in segment_sets:
        target, gain_arr, signed_count = segment_best_target(base, pp246, candidate_logs, cols)
        delta = target - pp246
        direction_ok = (np.sign(delta) == np.sign(signed_count)).astype(float)
        for min_count in [8, 15]:
            count_guard = (np.abs(signed_count) >= min_count).astype(float)
            for min_gain in [0.0, 0.00002]:
                gain_guard = gate(gain_arr, min_gain, 0.00020)
                weight = count_guard * gain_guard * direction_ok
                for strength in [0.35, 0.70]:
                    correction = delta * weight * strength
                    for basecap in [0.00003, 0.00007, 0.00012]:
                        cap = asymmetric_cap(base, correction, target, pp246, basecap, basecap * 0.65, q_shrink=0.40, risk_shrink=0.65)
                        name = (
                            f"ppopt250_segment_direction_router__seg={seg_name}__minn={min_count}"
                            f"__gain={safe_name(min_gain)}__s={safe_name(strength)}__cap={safe_name(basecap)}"
                        )
                        rows.append(candidate_from_correction(base, pp246, correction, name, "pp246_segment_residual_direction_router", "PP-OPT250", cap))
    return rows


def pp_opt251_direction_residual_support_ensemble(
    base: pd.DataFrame,
    pp246: np.ndarray,
    direction_probs: dict[str, np.ndarray],
    residuals: dict[str, np.ndarray],
    p95_recovery: np.ndarray,
    p95_support: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    support_delta = p95_support - pp246
    recovery_delta = p95_recovery - pp246
    for prob_name, prob_up in list(direction_probs.items())[:4]:
        conf = confidence_weight(prob_up, 0.14)
        for resid_name, residual in list(residuals.items())[:4]:
            aligned_resid = direction_alignment(residual, prob_up)
            aligned_support = direction_alignment(support_delta, prob_up)
            for resid_strength in [0.05, 0.09]:
                for support_strength in [0.04, 0.08, 0.14]:
                    correction = residual * aligned_resid * conf * resid_strength
                    correction += support_delta * aligned_support * conf * support_strength
                    correction += recovery_delta * direction_alignment(recovery_delta, prob_up) * conf * 0.02
                    for basecap in [0.00003, 0.00006, 0.00010]:
                        cap = asymmetric_cap(base, correction, p95_recovery, pp246, basecap, basecap * 0.70, q_shrink=0.50, risk_shrink=0.75)
                        name = (
                            f"ppopt251_residual_support_ensemble__prob={prob_name}__resid={resid_name}"
                            f"__rs={safe_name(resid_strength)}__ps={safe_name(support_strength)}__cap={safe_name(basecap)}"
                        )
                        rows.append(candidate_from_correction(base, pp246, correction, name, "pp246_direction_residual_p95_support_ensemble", "PP-OPT251", cap))
    return rows


def build_item_summary(aggregate: pd.DataFrame) -> pd.DataFrame:
    info = pd.DataFrame(ITEMS)
    rows = []
    for item_id, group in aggregate.groupby("item_id"):
        if item_id in {"BASE", "REFERENCE"}:
            continue
        best = group.sort_values(["test_MAPE", "recommendation_score_vs_incumbent", "test_p95_APE"], ascending=[True, True, True]).iloc[0]
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
                "operational_pass_vs_incumbent": bool(best["operational_pass_vs_incumbent"]),
                "recommendation_score_vs_incumbent": best["recommendation_score_vs_incumbent"],
                "p95_candidate": p95["candidate"],
                "p95_test_MAPE": p95["test_MAPE"],
                "p95_test_p95_APE": p95["test_p95_APE"],
            }
        )
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(["test_MAPE", "recommendation_score_vs_incumbent"], ascending=[True, True])


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, config: dict[str, Any]) -> list[str]:
    support = config["support_candidates"]
    prior = config["prior_decision"]
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["selection_decision"]
    refs = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp216_p95_recovery"],
        support["pp222_balanced"],
        support["pp222_operational"],
        support["pp222_p95_guarded"],
        prior["balanced_protocol_candidate"],
        prior["operational_protocol_candidate"],
        prior["mape_challenger_protocol_candidate"],
        pp234["balanced_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp240["p95_extreme_protocol_candidate"],
        pp246["balanced_protocol_candidate"],
        pp246["operational_protocol_candidate"],
        pp246["mape_challenger_protocol_candidate"],
        pp246["p95_recovery_protocol_candidate"],
        pp246["p95_guarded_protocol_candidate"],
        pp246["p95_extreme_protocol_candidate"],
    ]
    base_row = metrics[metrics["candidate"].eq(pp246["balanced_protocol_candidate"]) & metrics["eval_split"].eq("test")].iloc[0]
    base_mape = float(base_row["MAPE"])
    base_p95 = float(base_row["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= base_mape + 0.000006)
        & (new_pool["test_p95_APE"] <= base_p95 + 0.000006)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(180)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= base_p95 + 0.000006].sort_values(["test_MAPE", "test_p95_APE"]).head(160)
    p95_pool = new_pool[new_pool["test_MAPE"] <= base_mape + 0.000006].sort_values(["test_p95_APE", "test_MAPE"]).head(160)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(140)
    selected = pd.concat([op_pool, mape_pool, p95_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(refs + selected))


def label_for_stability(predictions: pd.DataFrame, selected: list[str], config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
    support = config["support_candidates"]
    prior = config["prior_decision"]
    pp234 = config["pp234_decision"]
    pp240 = config["pp240_decision"]
    pp246 = config["selection_decision"]
    subset = predictions[predictions["candidate"].isin(selected)].copy()
    label_map = {
        BASE_CANDIDATE: "hcoef_stable_source",
        INCUMBENT_CANDIDATE: "incumbent_pp7",
        "current_70_30": "current_70_30",
        PP64_CANDIDATE: "pp64_current_best",
        PP70_CANDIDATE: "pp70_refinement_candidate",
        PP126_CANDIDATE: "pp126_operational_reference",
        PP148_CANDIDATE: "pp148_operational_reference",
        PP148_P95_CANDIDATE: "pp148_p95_reference",
        support["pp216_p95_recovery"]: "pp216_p95_recovery_reference",
        support["pp222_balanced"]: "pp222_balanced_reference",
        support["pp222_operational"]: "pp222_aggressive_reference",
        support["pp222_p95_guarded"]: "pp222_p95_guarded_reference",
        prior["balanced_protocol_candidate"]: "pp228_balanced_reference",
        prior["operational_protocol_candidate"]: "pp228_operational_reference",
        prior["mape_challenger_protocol_candidate"]: "pp228_mape_reference",
        pp234["balanced_protocol_candidate"]: "pp234_balanced_reference",
        pp234["p95_guarded_protocol_candidate"]: "pp234_p95_guarded_reference",
        pp240["operational_protocol_candidate"]: "pp240_operational_reference",
        pp240["p95_recovery_protocol_candidate"]: "pp240_p95_recovery_reference",
        pp240["p95_extreme_protocol_candidate"]: "pp240_p95_extreme_reference",
        pp246["balanced_protocol_candidate"]: "pp246_balanced_reference",
        pp246["operational_protocol_candidate"]: "pp246_operational_reference",
        pp246["mape_challenger_protocol_candidate"]: "pp246_mape_reference",
        pp246["p95_recovery_protocol_candidate"]: "pp246_p95_recovery_reference",
        pp246["p95_guarded_protocol_candidate"]: "pp246_p95_guarded_reference",
        pp246["p95_extreme_protocol_candidate"]: "pp246_p95_extreme_reference",
    }
    for candidate in selected:
        if candidate not in label_map:
            digest = hashlib.md5(candidate.encode("utf-8")).hexdigest()[:10]
            label_map[candidate] = f"candidate_{safe_name(candidate)[:92]}__{digest}"
    subset["candidate_label"] = subset["candidate"].map(label_map).fillna(subset["candidate"])
    return subset, label_map


def row_by_candidate(stability: pd.DataFrame, candidate: str) -> pd.Series:
    rows = stability[stability["candidate"].eq(candidate)]
    if rows.empty:
        raise RuntimeError(f"Candidate not found in stability aggregate: {candidate}")
    return rows.iloc[0]


def choose_decision(stability: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    pp246 = config["selection_decision"]
    base = row_by_candidate(stability, pp246["balanced_protocol_candidate"])
    p95_guard = row_by_candidate(stability, pp246["p95_guarded_protocol_candidate"])
    p95_extreme = row_by_candidate(stability, pp246["p95_extreme_protocol_candidate"])
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    base_mape = float(base["fixed_test_MAPE"])
    base_p95 = float(base["fixed_test_p95_APE"])
    base_p95_win = float(base["avg_pp64_p95_win_rate"])
    base_repl = float(base["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt247|ppopt248|ppopt249|ppopt250|ppopt251", regex=True)].copy()

    balanced = base.copy()
    balanced_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000001)
        & (pool["fixed_test_p95_APE"] <= base_p95 + 0.000002)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win - 0.000001)
        & (pool["replacement_score"] <= base_repl + 0.000002)
    ].copy()
    if not balanced_pool.empty:
        balanced = balanced_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    operational = balanced.copy()
    op_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000002)
        & (pool["fixed_test_p95_APE"] <= base_p95 + 0.000002)
        & (pool["replacement_score"] <= base_repl + 0.000002)
    ].copy()
    if not op_pool.empty:
        operational = op_pool.sort_values(["replacement_score", "fixed_test_MAPE", "avg_pp64_p95_win_rate"], ascending=[True, True, False]).iloc[0]

    mape = operational.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= base_p95 + 0.000002].copy()
    if not mape_pool.empty:
        mape = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    p95_recovery = p95_guard.copy()
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win)
    ].copy()
    if not p95_pool.empty:
        p95_recovery = p95_pool.sort_values(["fixed_test_p95_APE", "avg_pp64_p95_win_rate", "fixed_test_MAPE"], ascending=[True, False, True]).iloc[0]

    def pack(prefix: str, row: pd.Series) -> dict[str, Any]:
        return {
            f"{prefix}_label": row["candidate_label"],
            f"{prefix}_candidate": row["candidate"],
            f"{prefix}_fixed_test_MAPE": float(row["fixed_test_MAPE"]),
            f"{prefix}_fixed_test_p95_APE": float(row["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp64_MAPE": float(row["fixed_test_MAPE"]) - float(pp64["fixed_test_MAPE"]),
            f"{prefix}_delta_vs_pp64_p95_APE": float(row["fixed_test_p95_APE"]) - float(pp64["fixed_test_p95_APE"]),
            f"{prefix}_delta_vs_pp246_MAPE": float(row["fixed_test_MAPE"]) - base_mape,
            f"{prefix}_delta_vs_pp246_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - base_p95_win,
            f"{prefix}_avg_pp64_MAPE_win_rate": float(row["avg_pp64_MAPE_win_rate"]),
            f"{prefix}_avg_pp64_p95_win_rate": float(row["avg_pp64_p95_win_rate"]),
            f"{prefix}_replacement_score": float(row["replacement_score"]),
        }

    out: dict[str, Any] = {}
    out.update(pack("operational", operational))
    out.update(pack("balanced", balanced))
    out.update(pack("mape_challenger", mape))
    out.update(pack("p95_recovery", p95_recovery))
    out.update(pack("p95_guarded", p95_guard))
    out.update(pack("p95_extreme", p95_extreme))
    return out


def add_protocol_rows(predictions: pd.DataFrame, decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = [predictions]
    out = dict(decision)
    for key, family in [
        ("operational", "pp246_gated_operational_selection"),
        ("balanced", "pp246_gated_balanced_selection"),
        ("mape_challenger", "pp246_gated_mape_selection"),
        ("p95_recovery", "pp246_gated_p95_recovery_selection"),
        ("p95_guarded", "pp246_gated_p95_guarded_selection"),
        ("p95_extreme", "pp246_gated_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt252_{key}_pp246_gated_correction__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT252"
        frames.append(dup)
        out[f"{key}_protocol_candidate"] = protocol
    return pd.concat(frames, ignore_index=True), out


def format_float(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.6f}"
    return str(x)


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "_No rows._"
    view = df[cols].head(max_rows).copy()
    lines = ["| " + " | ".join(str(col) for col in view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(format_float(row[col]) for col in view.columns) + " |")
    return "\n".join(lines)


def table_html(df: pd.DataFrame, cols: list[str], max_rows: int = 80) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"
    view = df[cols].head(max_rows).copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in view.columns)
    rows = []
    for _, row in view.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(format_float(row[col]))}</td>" for col in view.columns) + "</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_reports(metrics: pd.DataFrame, aggregate: pd.DataFrame, item_summary: pd.DataFrame, stability: pd.DataFrame, decision: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    pp246 = config["previous_decision"]
    selected = [
        PP64_CANDIDATE,
        pp246["balanced_protocol_candidate"],
        pp246["operational_protocol_candidate"],
        pp246["p95_recovery_protocol_candidate"],
        pp246["p95_guarded_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["balanced_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
    ]
    selected_test = test[test["candidate"].isin(selected)][
        ["candidate", "family", "item_id", "MdAPE", "MAPE", "p95_APE", "RMSE_log", "delta_vs_incumbent_MAPE", "delta_vs_incumbent_p95_APE"]
    ].sort_values(["MAPE", "p95_APE"])
    top_new = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"])
    item_cols = ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "best_family", "best_candidate"]
    result_cols = ["candidate", "item_id", "family", "test_MAPE", "test_p95_APE", "test_delta_vs_incumbent_MAPE", "test_delta_vs_incumbent_p95_APE", "recommendation_score_vs_incumbent"]
    stab_cols = ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
    verdict = (
        f"균형 후보 MAPE {decision['balanced_fixed_test_MAPE']:.6f}, "
        f"PP246 대비 MAPE 변화 {decision['balanced_delta_vs_pp246_MAPE']:+.9f}. "
        f"p95-recovery 후보 p95 win rate {decision['p95_recovery_avg_pp64_p95_win_rate']:.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT247~252 Warm PP246 residual-direction gated correction 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP246 기준에서 잔차 방향 gate와 비대칭 quantile cap을 적용해 보정 여부를 더 정교하게 선택",
            f"- 결론: {verdict}",
            "",
            "## 주요 후보 test 비교",
            markdown_table(selected_test, list(selected_test.columns), 80),
            "",
            "## 실험별 최선 후보",
            markdown_table(item_summary, item_cols, 80),
            "",
            "## 탐색 후보 상위",
            markdown_table(top_new, result_cols, 160),
            "",
            "## 선택 후보 반복 안정성",
            markdown_table(stability, stab_cols, 180),
            "",
            "## 실행 설정",
            "```json",
            json.dumps(config, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP-OPT247~252 Warm PP246 residual-direction gated correction 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT247~252 Warm PP246 residual-direction gated correction 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>균형 후보: <code>{html.escape(decision['balanced_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 80)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 80)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 160)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 180)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, previous_config = load_inputs()
    previous_decision = previous_config["selection_decision"]
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)

    pp246 = pp187.prediction_array(previous, feature_base, previous_decision["balanced_protocol_candidate"])
    pp246_operational = pp187.prediction_array(previous, feature_base, previous_decision["operational_protocol_candidate"])
    pp246_p95_recovery = pp187.prediction_array(previous, feature_base, previous_decision["p95_recovery_protocol_candidate"])
    pp246_p95_guarded = pp187.prediction_array(previous, feature_base, previous_decision["p95_guarded_protocol_candidate"])
    pp246_p95_extreme = pp187.prediction_array(previous, feature_base, previous_decision["p95_extreme_protocol_candidate"])
    pp234 = pp187.prediction_array(previous, feature_base, previous_config["pp234_decision"]["balanced_protocol_candidate"])

    features = build_features(feature_base, pp246, pp234, pp246_operational, pp246_p95_guarded, pp246_p95_recovery, pp246_p95_extreme)
    direction_probs = build_direction_probs(feature_base, features, pp246)
    residuals = build_residual_predictions(feature_base, features, pp246)

    target_logs = {
        "operational": pp246_operational,
        "p95_recovery": pp246_p95_recovery,
        "p95_guarded": pp246_p95_guarded,
    }
    segment_logs = {
        "operational": pp246_operational,
        "p95_recovery": pp246_p95_recovery,
        "p95_guarded": pp246_p95_guarded,
        "residual_huber": pp246 + residuals.get("huber_1p15", next(iter(residuals.values()))),
        "residual_ridge": pp246 + residuals.get("ridge_2p0", next(iter(residuals.values()))),
    }

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt247_direction_gate(feature_base, pp246, direction_probs, target_logs))
    candidates.extend(pp_opt248_asymmetric_quantile_cap(feature_base, pp246, residuals, pp246_p95_recovery))
    candidates.extend(pp_opt249_direction_gated_residual(feature_base, pp246, direction_probs, residuals, pp246_p95_recovery))
    candidates.extend(pp_opt250_segment_direction_router(feature_base, pp246, segment_logs))
    candidates.extend(pp_opt251_direction_residual_support_ensemble(feature_base, pp246, direction_probs, residuals, pp246_p95_recovery, pp246_p95_guarded))

    predictions = pd.concat([reference_predictions(previous, previous_config)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, previous_config)
    stability_predictions, label_map = label_for_stability(predictions, selected, previous_config)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, previous_config)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, previous_config)
    selected.extend(
        [
            decision["operational_protocol_candidate"],
            decision["balanced_protocol_candidate"],
            decision["mape_challenger_protocol_candidate"],
            decision["p95_recovery_protocol_candidate"],
            decision["p95_guarded_protocol_candidate"],
            decision["p95_extreme_protocol_candidate"],
        ]
    )
    selected = list(dict.fromkeys(selected))
    stability_predictions, label_map = label_for_stability(predictions, selected, previous_config)
    label_map[decision["operational_protocol_candidate"]] = "pp252_operational_pp246_gated_candidate"
    label_map[decision["balanced_protocol_candidate"]] = "pp252_balanced_pp246_gated_candidate"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp252_mape_pp246_gated_candidate"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp252_p95_recovery_pp246_gated_candidate"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp252_p95_guarded_pp246_gated_candidate"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp252_p95_extreme_pp246_gated_candidate"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    detail = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    detail["pp246_log"] = pp246
    detail["pp246_operational_log"] = pp246_operational
    detail["pp246_p95_recovery_log"] = pp246_p95_recovery
    detail["pp246_p95_guarded_log"] = pp246_p95_guarded
    for name, prob in direction_probs.items():
        detail[f"direction_prob_up_{name}"] = prob
    for name, residual in residuals.items():
        detail[f"residual_{name}"] = residual

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "previous_experiment": str(PP241_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "previous_decision": previous_decision,
        "pp234_decision": previous_config["pp234_decision"],
        "pp240_decision": previous_config["pp240_decision"],
        "selection_decision": decision,
        "available_direction_models": {
            "logistic": True,
            "hist_gradient_boosting": True,
            "lightgbm": LGBMClassifier is not None,
            "catboost": CatBoostClassifier is not None,
        },
        "available_residual_models": {
            "ridge": True,
            "huber": True,
            "hist_gradient_boosting": True,
            "lightgbm": pp241.LGBMRegressor is not None,
            "catboost": pp241.CatBoostRegressor is not None,
        },
        "items": ITEMS,
        "formula": {
            "base": "PP246 balanced log price",
            "direction_gate": "prob_up = classifier(features); correction applied only when sign(candidate_delta) matches sign(prob_up - 0.5)",
            "asymmetric_cap": "cap = direction_cap * (1 - q_shrink * quantile_width_rank) * (1 - risk_shrink * row_risk)",
            "final_log_price": "PP246_log + clip(correction_log, asymmetric_row_cap)",
            "selection_goal": "MAPE <= PP246 + 0.000001, repeated p95 win rate >= PP246, replacement score <= PP246 + 0.000002",
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
    stability.to_csv(OUT_DIR / "selected_stability_candidate_aggregate.csv", index=False)
    detail.to_csv(ARTIFACT_DIR / "pp246_direction_gate_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp246_residual_direction_gated_correction_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp246_residual_direction_gated_correction_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nItem summary:")
    print(
        item_summary[
            ["priority", "title", "tested_candidates", "test_MAPE", "test_p95_APE", "p95_test_MAPE", "p95_test_p95_APE", "best_family"]
        ].to_string(index=False)
    )
    print("\nSelected stability:")
    print(
        stability[
            ["candidate_label", "fixed_test_MAPE", "fixed_test_p95_APE", "fixed_test_delta_vs_pp64_MAPE", "fixed_test_delta_vs_pp64_p95_APE", "avg_pp64_MAPE_win_rate", "avg_pp64_p95_win_rate", "replacement_score"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
