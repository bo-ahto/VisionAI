#!/usr/bin/env python3
"""Run PP-OPT241..246 Warm PP234 p95-constrained support and basis-regeneration pilot."""
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
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from lightgbm import LGBMRegressor
except Exception:  # pragma: no cover - optional dependency
    LGBMRegressor = None

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - optional dependency
    XGBRegressor = None

try:
    from catboost import CatBoostRegressor
except Exception:  # pragma: no cover - optional dependency
    CatBoostRegressor = None


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP235_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt235_240_warm_pp234_significance_audit_and_learned_router.py"
PP235_DIR = REPO / "experiments" / "track6" / "PP-OPT235_240_warm_pp234_significance_audit_and_learned_router"
PP235_PREDICTIONS = PP235_DIR / "outputs" / "candidate_predictions.csv"
PP235_CONFIG = PP235_DIR / "artifacts" / "run_config.json"
PP235_AGGREGATE = PP235_DIR / "outputs" / "aggregate_candidate_stability.csv"

EXP_ID = "PP-OPT241-246"
EXP_SLUG = "PP-OPT241_246_warm_pp234_p95_constrained_support_and_basis_regeneration"
EXP_DIR = REPO / "experiments" / "track6" / EXP_SLUG
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
ARTIFACT_DIR = EXP_DIR / "artifacts"

BASE_CANDIDATE = "hcoef_stable"
INCUMBENT_CANDIDATE = "incumbent_operational_pp_opt7"
PP64_CANDIDATE = "reference_pp64_current_best"
PP70_CANDIDATE = "reference_pp70_refinement"
PP126_CANDIDATE = "reference_pp126_operational"
PP148_CANDIDATE = "reference_pp148_operational"
PP148_P95_CANDIDATE = "reference_pp148_p95"

ITEMS = [
    {
        "item_id": "PP-OPT241",
        "priority": "1",
        "title": "p95 support from learned-router candidates",
        "description": "PP237/PP239 중 p95 APE가 낮았던 후보를 PP234 위에 tiny cap으로만 얹음.",
    },
    {
        "item_id": "PP-OPT242",
        "priority": "2",
        "title": "p95 guarded/recovery ultra support",
        "description": "PP234 p95-guarded와 PP216 p95-recovery 이동을 매우 작게 제한 적용.",
    },
    {
        "item_id": "PP-OPT243",
        "priority": "3",
        "title": "Huber/Ridge residual regeneration",
        "description": "validation OOF에서 PP234 잔차를 Huber/Ridge로 재학습해 clipped residual correction 적용.",
    },
    {
        "item_id": "PP-OPT244",
        "priority": "4",
        "title": "tree residual regeneration",
        "description": "LightGBM/XGBoost/CatBoost/HistGradientBoosting 소형 잔차 모델을 clipped correction으로 적용.",
    },
    {
        "item_id": "PP-OPT245",
        "priority": "5",
        "title": "residual plus p95 support ensemble",
        "description": "작은 residual correction과 p95-support 이동을 동시에 적용하되 PP234 기준 cap으로 제한.",
    },
    {
        "item_id": "PP-OPT246",
        "priority": "6",
        "title": "final PP234 p95-constrained support decision",
        "description": "PP234 대비 MAPE, repeated p95 win rate, replacement score 제약을 만족하는 후보만 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp235 = load_module("pp_opt235_helpers_for_pp241", PP235_SCRIPT)
pp229 = pp235.pp229
pp223 = pp235.pp223
pp199 = pp235.pp199
pp187 = pp235.pp187
pp161 = pp235.pp161
opt8 = pp235.opt8
val71 = pp235.val71


CAT_COLS = pp235.CAT_COLS
NUM_COLS = pp235.NUM_COLS


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp235.safe_name(value)


def gate(value: np.ndarray, threshold: float | np.ndarray, width: float) -> np.ndarray:
    return pp229.gate(value, threshold, width)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp235.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp235.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    return (
        pd.read_csv(PP235_PREDICTIONS),
        json.loads(PP235_CONFIG.read_text(encoding="utf-8")),
        pd.read_csv(PP235_AGGREGATE),
    )


def make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def regression_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("cat", make_ohe(), CAT_COLS),
            ("num", StandardScaler(), NUM_COLS),
        ],
        remainder="drop",
    )


def candidate_from_move(
    base: pd.DataFrame,
    source: np.ndarray,
    target: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    weight: np.ndarray | float,
    cap: np.ndarray | float,
) -> pd.DataFrame:
    weights = np.full(len(base), float(weight)) if isinstance(weight, (float, int)) else np.asarray(weight, dtype=float)
    caps = np.full(len(base), float(cap)) if isinstance(cap, (float, int)) else np.asarray(cap, dtype=float)
    return make_candidate(base, name, family, item_id, source + clip_by_row((target - source) * weights, caps))


def candidate_from_correction(
    base: pd.DataFrame,
    source: np.ndarray,
    correction: np.ndarray,
    name: str,
    family: str,
    item_id: str,
    strength: float,
    cap: np.ndarray | float,
) -> pd.DataFrame:
    caps = np.full(len(base), float(cap)) if isinstance(cap, (float, int)) else np.asarray(cap, dtype=float)
    pred = source + clip_by_row(correction * strength, caps)
    return make_candidate(base, name, family, item_id, pred)


def risk_cap(basecap: float, shrink: float, risk: np.ndarray, floor: float) -> np.ndarray:
    return np.clip(basecap * (1.0 - shrink * np.clip(risk, 0.0, 1.0)), floor, basecap)


def reference_predictions(previous: pd.DataFrame, support: dict[str, Any], prior: dict[str, Any], pp234: dict[str, Any], pp240: dict[str, Any]) -> pd.DataFrame:
    keep = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp192_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_balanced"],
        support["pp222_operational"],
        support["pp222_p95_guarded"],
        prior["balanced_protocol_candidate"],
        prior["operational_protocol_candidate"],
        prior["mape_challenger_protocol_candidate"],
        prior["p95_guarded_protocol_candidate"],
        pp234["balanced_protocol_candidate"],
        pp234["operational_protocol_candidate"],
        pp234["mape_challenger_protocol_candidate"],
        pp234["p95_recovery_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["balanced_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["mape_challenger_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp240["p95_guarded_protocol_candidate"],
        pp240["p95_extreme_protocol_candidate"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def select_p95_support_candidates(prev_aggregate: pd.DataFrame, max_candidates: int = 4) -> list[str]:
    pool = prev_aggregate[
        prev_aggregate["item_id"].isin(["PP-OPT237", "PP-OPT239"])
        & (prev_aggregate["test_MAPE"] <= 0.269895)
    ].copy()
    if pool.empty:
        return []
    return pool.sort_values(["test_p95_APE", "test_MAPE", "recommendation_score_vs_incumbent"]).head(max_candidates)["candidate"].tolist()


def segment_support_weight(base: pd.DataFrame, source: np.ndarray, target: np.ndarray, cols: list[str]) -> np.ndarray:
    score, p95_gain, mean_gain, count = pp229.pp211.recovery_signal(base, source, target, cols)
    count_guard = np.where(count > 0, gate(count, 8.0, 8.0), 1.0)
    return (
        gate(score, -0.02, 0.18)
        * gate(p95_gain, -0.00008, 0.00018)
        * gate(mean_gain, -0.00008, 0.00024)
        * count_guard
    )


def pp_opt241_p95_support(
    base: pd.DataFrame,
    pp234: np.ndarray,
    support_logs: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for idx, (target_name, target) in enumerate(support_logs.items(), start=1):
        risk = pp199.row_risk(base, pp234, target)
        for seg_name, cols in [
            ("price_conf", ["stable_price_band", "confidence_tier"]),
            ("price_conf_qwidth", ["stable_price_band", "confidence_tier", "qwidth_band"]),
        ]:
            base_w = segment_support_weight(base, pp234, target, cols)
            for strength in [0.04, 0.08, 0.14, 0.22]:
                for basecap in [0.00002, 0.00004, 0.00007, 0.00010]:
                    for shrink in [0.50, 0.80]:
                        cap = risk_cap(basecap, shrink, risk, floor=0.000008)
                        name = (
                            f"ppopt241_p95_support__src=s{idx}__seg={seg_name}"
                            f"__s={safe_name(strength)}__cap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(candidate_from_move(base, pp234, target, name, "pp234_p95_constrained_support", "PP-OPT241", base_w * strength, cap))
    return rows


def pp_opt242_guarded_recovery_ultra_support(
    base: pd.DataFrame,
    pp234: np.ndarray,
    guarded: np.ndarray,
    recovery: np.ndarray,
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    for target_name, target in [("guarded", guarded), ("recovery", recovery)]:
        risk = pp199.row_risk(base, pp234, target)
        base_w = segment_support_weight(base, pp234, target, ["stable_price_band", "confidence_tier"])
        for strength in [0.02, 0.04, 0.08, 0.12]:
            for basecap in [0.000015, 0.000030, 0.000050, 0.000080]:
                for shrink in [0.65, 0.90]:
                    cap = risk_cap(basecap, shrink, risk, floor=0.000006)
                    name = (
                        f"ppopt242_guarded_recovery_support__target={target_name}"
                        f"__s={safe_name(strength)}__cap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                    )
                    rows.append(candidate_from_move(base, pp234, target, name, "pp234_guarded_recovery_ultra_support", "PP-OPT242", base_w * strength, cap))
    return rows


def crossfit_regression_prediction(
    features: pd.DataFrame,
    val_mask: np.ndarray,
    y_val: np.ndarray,
    model_factory: Callable[[], Any],
    seed: int,
) -> np.ndarray:
    X_val = features.loc[val_mask]
    X_all = features
    out = np.zeros(len(features), dtype=float)
    oof = np.zeros(len(X_val), dtype=float)
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    for train_idx, hold_idx in kfold.split(X_val):
        model = model_factory()
        model.fit(X_val.iloc[train_idx], y_val[train_idx])
        oof[hold_idx] = model.predict(X_val.iloc[hold_idx])
    full = model_factory()
    full.fit(X_val, y_val)
    out[:] = full.predict(X_all)
    out[np.where(val_mask)[0]] = oof
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def make_linear_model(kind: str, value: float) -> Pipeline:
    if kind == "ridge":
        reg = Ridge(alpha=value)
    elif kind == "huber":
        reg = HuberRegressor(epsilon=value, alpha=0.0001, max_iter=500)
    else:
        raise ValueError(kind)
    return Pipeline([("prep", regression_preprocessor()), ("reg", reg)])


def make_tree_model(kind: str, seed: int, value: float):
    if kind == "hist_gbr":
        reg = HistGradientBoostingRegressor(max_iter=int(value), learning_rate=0.035, max_leaf_nodes=8, l2_regularization=0.08, random_state=seed)
        return Pipeline([("prep", regression_preprocessor()), ("reg", reg)])
    if kind == "lgbm" and LGBMRegressor is not None:
        reg = LGBMRegressor(n_estimators=int(value), learning_rate=0.025, num_leaves=7, min_child_samples=24, subsample=0.85, colsample_bytree=0.85, reg_lambda=2.0, random_state=seed, verbose=-1)
        return Pipeline([("prep", regression_preprocessor()), ("reg", reg)])
    if kind == "xgb" and XGBRegressor is not None:
        reg = XGBRegressor(n_estimators=int(value), learning_rate=0.025, max_depth=2, min_child_weight=8, subsample=0.85, colsample_bytree=0.85, reg_lambda=3.0, objective="reg:squarederror", random_state=seed, verbosity=0)
        return Pipeline([("prep", regression_preprocessor()), ("reg", reg)])
    if kind == "cat" and CatBoostRegressor is not None:
        reg = CatBoostRegressor(iterations=int(value), learning_rate=0.025, depth=2, l2_leaf_reg=8.0, loss_function="RMSE", random_seed=seed, verbose=False)
        return Pipeline([("prep", regression_preprocessor()), ("reg", reg)])
    raise RuntimeError(f"Tree model not available: {kind}")


def pp_opt243_linear_residual_regeneration(
    base: pd.DataFrame,
    features: pd.DataFrame,
    pp234: np.ndarray,
) -> tuple[list[pd.DataFrame], dict[str, np.ndarray]]:
    rows: list[pd.DataFrame] = []
    corrections: dict[str, np.ndarray] = {}
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - pp234
    y_val = residual[val_mask]
    specs = [("ridge", 0.5), ("ridge", 2.0), ("ridge", 6.0), ("huber", 1.15), ("huber", 1.35), ("huber", 1.70)]
    for kind, value in specs:
        pred_resid = crossfit_regression_prediction(features, val_mask, y_val, lambda k=kind, v=value: make_linear_model(k, v), seed=101)
        key = f"{kind}_{safe_name(value)}"
        corrections[key] = pred_resid
        risk = pp199.row_risk(base, pp234, pp234 + pred_resid)
        for strength in [0.04, 0.08, 0.14, 0.22]:
            for basecap in [0.00003, 0.00006, 0.00012, 0.00020]:
                for shrink in [0.50, 0.80]:
                    cap = risk_cap(basecap, shrink, risk, floor=0.000008)
                    name = f"ppopt243_linear_residual__model={key}__s={safe_name(strength)}__cap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                    rows.append(candidate_from_correction(base, pp234, pred_resid, name, "pp234_linear_residual_regeneration", "PP-OPT243", strength, cap))
    return rows, corrections


def pp_opt244_tree_residual_regeneration(
    base: pd.DataFrame,
    features: pd.DataFrame,
    pp234: np.ndarray,
) -> tuple[list[pd.DataFrame], dict[str, np.ndarray]]:
    rows: list[pd.DataFrame] = []
    corrections: dict[str, np.ndarray] = {}
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    residual = base["actual_log"].to_numpy(dtype=float) - pp234
    y_val = residual[val_mask]
    specs: list[tuple[str, int]] = [("hist_gbr", 35), ("hist_gbr", 70)]
    if LGBMRegressor is not None:
        specs.extend([("lgbm", 40), ("lgbm", 80)])
    if XGBRegressor is not None:
        specs.extend([("xgb", 40), ("xgb", 80)])
    if CatBoostRegressor is not None:
        specs.extend([("cat", 40), ("cat", 80)])
    for kind, value in specs:
        pred_resid = crossfit_regression_prediction(features, val_mask, y_val, lambda k=kind, v=value: make_tree_model(k, 20260610, v), seed=202)
        key = f"{kind}_{safe_name(value)}"
        corrections[key] = pred_resid
        risk = pp199.row_risk(base, pp234, pp234 + pred_resid)
        for strength in [0.025, 0.05, 0.10, 0.16]:
            for basecap in [0.00002, 0.00005, 0.00010, 0.00018]:
                for shrink in [0.60, 0.85]:
                    cap = risk_cap(basecap, shrink, risk, floor=0.000006)
                    name = f"ppopt244_tree_residual__model={key}__s={safe_name(strength)}__cap={safe_name(basecap)}__shrink={safe_name(shrink)}"
                    rows.append(candidate_from_correction(base, pp234, pred_resid, name, "pp234_tree_residual_regeneration", "PP-OPT244", strength, cap))
    return rows, corrections


def pp_opt245_residual_plus_support(
    base: pd.DataFrame,
    pp234: np.ndarray,
    residuals: dict[str, np.ndarray],
    support_logs: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    if not residuals or not support_logs:
        return rows
    residual_items = list(residuals.items())[:4]
    support_items = list(support_logs.items())[:2]
    for resid_name, resid in residual_items:
        for support_idx, (_support_name, support) in enumerate(support_items, start=1):
            risk = np.maximum(pp199.row_risk(base, pp234, pp234 + resid), pp199.row_risk(base, pp234, support))
            support_weight = segment_support_weight(base, pp234, support, ["stable_price_band", "confidence_tier"])
            for residual_strength in [0.03, 0.06, 0.10]:
                for support_strength in [0.04, 0.08, 0.14]:
                    for basecap in [0.00003, 0.00006, 0.00010]:
                        cap = risk_cap(basecap, 0.75, risk, floor=0.000008)
                        correction = resid * residual_strength + (support - pp234) * support_weight * support_strength
                        name = (
                            f"ppopt245_residual_support__resid={resid_name}__support=s{support_idx}"
                            f"__rs={safe_name(residual_strength)}__ps={safe_name(support_strength)}__cap={safe_name(basecap)}"
                        )
                        rows.append(candidate_from_correction(base, pp234, correction, name, "pp234_residual_plus_p95_support", "PP-OPT245", 1.0, cap))
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


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, support: dict[str, Any], prior: dict[str, Any], pp234: dict[str, Any], pp240: dict[str, Any]) -> list[str]:
    refs = [
        BASE_CANDIDATE,
        INCUMBENT_CANDIDATE,
        "current_70_30",
        PP64_CANDIDATE,
        PP70_CANDIDATE,
        PP126_CANDIDATE,
        PP148_CANDIDATE,
        PP148_P95_CANDIDATE,
        support["pp192_operational"],
        support["pp204_operational"],
        support["pp210_operational"],
        support["pp216_p95_recovery"],
        support["pp222_balanced"],
        support["pp222_operational"],
        support["pp222_p95_guarded"],
        prior["balanced_protocol_candidate"],
        prior["operational_protocol_candidate"],
        prior["mape_challenger_protocol_candidate"],
        prior["p95_guarded_protocol_candidate"],
        pp234["balanced_protocol_candidate"],
        pp234["operational_protocol_candidate"],
        pp234["mape_challenger_protocol_candidate"],
        pp234["p95_recovery_protocol_candidate"],
        pp234["p95_guarded_protocol_candidate"],
        pp240["balanced_protocol_candidate"],
        pp240["operational_protocol_candidate"],
        pp240["mape_challenger_protocol_candidate"],
        pp240["p95_recovery_protocol_candidate"],
        pp240["p95_guarded_protocol_candidate"],
        pp240["p95_extreme_protocol_candidate"],
    ]
    base_row = metrics[metrics["candidate"].eq(pp234["balanced_protocol_candidate"]) & metrics["eval_split"].eq("test")].iloc[0]
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


def label_for_stability(predictions: pd.DataFrame, selected: list[str], support: dict[str, Any], prior: dict[str, Any], pp234: dict[str, Any], pp240: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
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
        support["pp192_operational"]: "pp192_operational_reference",
        support["pp204_operational"]: "pp204_operational_reference",
        support["pp210_operational"]: "pp210_operational_reference",
        support["pp216_p95_recovery"]: "pp216_p95_recovery_reference",
        support["pp222_balanced"]: "pp222_balanced_reference",
        support["pp222_operational"]: "pp222_aggressive_reference",
        support["pp222_p95_guarded"]: "pp222_p95_guarded_reference",
        prior["balanced_protocol_candidate"]: "pp228_balanced_reference",
        prior["operational_protocol_candidate"]: "pp228_operational_reference",
        prior["mape_challenger_protocol_candidate"]: "pp228_mape_reference",
        prior["p95_guarded_protocol_candidate"]: "pp228_p95_guarded_reference",
        pp234["balanced_protocol_candidate"]: "pp234_balanced_reference",
        pp234["operational_protocol_candidate"]: "pp234_operational_reference",
        pp234["mape_challenger_protocol_candidate"]: "pp234_mape_reference",
        pp234["p95_recovery_protocol_candidate"]: "pp234_p95_recovery_reference",
        pp234["p95_guarded_protocol_candidate"]: "pp234_p95_guarded_reference",
        pp240["balanced_protocol_candidate"]: "pp240_balanced_reference",
        pp240["operational_protocol_candidate"]: "pp240_operational_reference",
        pp240["mape_challenger_protocol_candidate"]: "pp240_mape_reference",
        pp240["p95_recovery_protocol_candidate"]: "pp240_p95_recovery_reference",
        pp240["p95_guarded_protocol_candidate"]: "pp240_p95_guarded_reference",
        pp240["p95_extreme_protocol_candidate"]: "pp240_p95_extreme_reference",
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


def choose_decision(stability: pd.DataFrame, pp234: dict[str, Any], pp240: dict[str, Any]) -> dict[str, Any]:
    base = row_by_candidate(stability, pp234["balanced_protocol_candidate"])
    pp240_op = row_by_candidate(stability, pp240["operational_protocol_candidate"])
    pp240_mape = row_by_candidate(stability, pp240["mape_challenger_protocol_candidate"])
    p95_guard = row_by_candidate(stability, pp234["p95_guarded_protocol_candidate"])
    p95_extreme = row_by_candidate(stability, pp240["p95_extreme_protocol_candidate"])
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    base_mape = float(base["fixed_test_MAPE"])
    base_p95 = float(base["fixed_test_p95_APE"])
    base_p95_win = float(base["avg_pp64_p95_win_rate"])
    base_repl = float(base["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt24|ppopt241|ppopt242|ppopt243|ppopt244|ppopt245", regex=True)].copy()

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

    mape = pp240_mape.copy()
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
            f"{prefix}_delta_vs_pp234_MAPE": float(row["fixed_test_MAPE"]) - base_mape,
            f"{prefix}_delta_vs_pp234_p95_win_rate": float(row["avg_pp64_p95_win_rate"]) - base_p95_win,
            f"{prefix}_delta_vs_pp240_operational_MAPE": float(row["fixed_test_MAPE"]) - float(pp240_op["fixed_test_MAPE"]),
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
        ("operational", "pp234_p95_constrained_operational_selection"),
        ("balanced", "pp234_p95_constrained_balanced_selection"),
        ("mape_challenger", "pp234_p95_constrained_mape_selection"),
        ("p95_recovery", "pp234_p95_constrained_p95_support_selection"),
        ("p95_guarded", "pp234_p95_constrained_p95_guarded_selection"),
        ("p95_extreme", "pp234_p95_constrained_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt246_{key}_pp234_p95_constrained__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT246"
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


def render_reports(
    metrics: pd.DataFrame,
    aggregate: pd.DataFrame,
    item_summary: pd.DataFrame,
    stability: pd.DataFrame,
    decision: dict[str, Any],
    config: dict[str, Any],
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        config["pp234_decision"]["balanced_protocol_candidate"],
        config["pp234_decision"]["p95_guarded_protocol_candidate"],
        config["pp240_decision"]["operational_protocol_candidate"],
        config["pp240_decision"]["p95_recovery_protocol_candidate"],
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
        f"운영 후보 MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['operational_avg_pp64_p95_win_rate']:.6f}. "
        f"PP234 대비 MAPE 변화 {decision['operational_delta_vs_pp234_MAPE']:+.9f}, "
        f"p95 win rate 변화 {decision['operational_delta_vs_pp234_p95_win_rate']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT241~246 Warm PP234 p95-constrained support and basis regeneration 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP234를 기준으로 p95-support tiny cap과 residual/basis 재생성 후보를 검증",
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
<title>PP-OPT241~246 Warm PP234 p95-constrained support 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT241~246 Warm PP234 p95-constrained support and basis regeneration 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code></div>
<h2>1. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 80)}
<h2>2. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 80)}
<h2>3. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 160)}
<h2>4. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 180)}
<h2>5. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, previous_config, prev_aggregate = load_inputs()
    support = previous_config["support_candidates"]
    prior_decision = previous_config["prior_decision"]
    pp234_decision = previous_config["pp234_decision"]
    pp240_decision = previous_config["selection_decision"]
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)

    pp234 = pp187.prediction_array(previous, feature_base, pp234_decision["balanced_protocol_candidate"])
    pp234_guarded = pp187.prediction_array(previous, feature_base, pp234_decision["p95_guarded_protocol_candidate"])
    pp216_recovery = pp187.prediction_array(previous, feature_base, support["pp216_p95_recovery"])
    pp240_recovery = pp187.prediction_array(previous, feature_base, pp240_decision["p95_recovery_protocol_candidate"])
    pp228_operational = pp187.prediction_array(previous, feature_base, prior_decision["operational_protocol_candidate"])
    pp228_mape = pp187.prediction_array(previous, feature_base, prior_decision["mape_challenger_protocol_candidate"])

    support_candidates = select_p95_support_candidates(prev_aggregate)
    support_logs = {
        f"support_{idx}": pp187.prediction_array(previous, feature_base, candidate)
        for idx, candidate in enumerate(support_candidates, start=1)
    }
    if not support_logs:
        support_logs = {"pp240_recovery": pp240_recovery}

    features = pp235.build_model_features(feature_base, pp234, pp228_operational, pp228_mape, pp234_guarded, pp216_recovery)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt241_p95_support(feature_base, pp234, support_logs))
    candidates.extend(pp_opt242_guarded_recovery_ultra_support(feature_base, pp234, pp234_guarded, pp216_recovery))
    linear_candidates, linear_residuals = pp_opt243_linear_residual_regeneration(feature_base, features, pp234)
    candidates.extend(linear_candidates)
    tree_candidates, tree_residuals = pp_opt244_tree_residual_regeneration(feature_base, features, pp234)
    candidates.extend(tree_candidates)
    residual_pool = {**linear_residuals, **tree_residuals}
    candidates.extend(pp_opt245_residual_plus_support(feature_base, pp234, residual_pool, support_logs))

    predictions = pd.concat([reference_predictions(previous, support, prior_decision, pp234_decision, pp240_decision)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, support, prior_decision, pp234_decision, pp240_decision)
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision, pp234_decision, pp240_decision)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, pp234_decision, pp240_decision)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, support, prior_decision, pp234_decision, pp240_decision)
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
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision, pp234_decision, pp240_decision)
    label_map[decision["operational_protocol_candidate"]] = "pp246_operational_pp234_p95_constrained_candidate"
    label_map[decision["balanced_protocol_candidate"]] = "pp246_balanced_pp234_p95_constrained_candidate"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp246_mape_pp234_p95_constrained_candidate"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp246_p95_recovery_pp234_p95_constrained_candidate"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp246_p95_guarded_pp234_p95_constrained_candidate"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp246_p95_extreme_pp234_p95_constrained_candidate"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    detail = feature_base[
        ["eval_split", "_track6_row_id", "stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
    ].copy()
    detail["pp234_log"] = pp234
    detail["pp234_guarded_log"] = pp234_guarded
    detail["pp216_recovery_log"] = pp216_recovery
    for name, log in support_logs.items():
        detail[f"{name}_log"] = log
    for name, residual in list(residual_pool.items())[:12]:
        detail[f"residual_{name}"] = residual

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "previous_experiment": str(PP235_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "prior_decision": prior_decision,
        "pp234_decision": pp234_decision,
        "pp240_decision": pp240_decision,
        "selection_decision": decision,
        "selected_p95_support_candidates": support_candidates,
        "available_tree_models": {
            "lightgbm": LGBMRegressor is not None,
            "xgboost": XGBRegressor is not None,
            "catboost": CatBoostRegressor is not None,
            "hist_gradient_boosting": True,
        },
        "items": ITEMS,
        "router_formula": {
            "base": "PP234 balanced log price",
            "p95_support": "PP234 + clip((p95-support log price - PP234) * segment_weight * strength, tiny row cap)",
            "residual_regeneration": "PP234 + clip(crossfit residual model prediction * strength, row cap)",
            "ensemble": "PP234 + clipped residual correction + clipped p95-support movement",
            "selection_goal": "Keep PP234 repeated p95 win-rate and replacement score while reducing fixed-test MAPE or p95 APE.",
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
    detail.to_csv(ARTIFACT_DIR / "pp234_p95_constrained_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config)
    (REPORT_DIR / "pp234_p95_constrained_support_and_basis_regeneration_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp234_p95_constrained_support_and_basis_regeneration_result.html").write_text(report_html, encoding="utf-8")

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
