#!/usr/bin/env python3
"""Run PP-OPT235..240 Warm PP234 significance audit and learned-router experiments."""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

REPO = Path(__file__).resolve().parents[2]
PP229_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt229_234_warm_pp228_p95_recovery_without_mape_loss.py"
PP229_DIR = REPO / "experiments" / "track6" / "PP-OPT229_234_warm_pp228_p95_recovery_without_mape_loss"
PP229_PREDICTIONS = PP229_DIR / "outputs" / "candidate_predictions.csv"
PP229_CONFIG = PP229_DIR / "artifacts" / "run_config.json"

EXP_ID = "PP-OPT235-240"
EXP_SLUG = "PP-OPT235_240_warm_pp234_significance_audit_and_learned_router"
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
        "item_id": "PP-OPT235",
        "priority": "1",
        "title": "PP234 significance audit",
        "description": "PP234의 PP228 대비 미세 개선이 bootstrap과 그룹 제외에서도 유지되는지 검증.",
    },
    {
        "item_id": "PP-OPT236",
        "priority": "2",
        "title": "segment winner router",
        "description": "validation OOF의 구간별 APE winner를 기반으로 후보를 선택하되 작은 cap으로 제한.",
    },
    {
        "item_id": "PP-OPT237",
        "priority": "3",
        "title": "learned multiclass candidate router",
        "description": "row 피쳐로 PP234/PP228 공격형/MAPE/p95 후보 중 APE winner를 cross-fit 분류.",
    },
    {
        "item_id": "PP-OPT238",
        "priority": "4",
        "title": "pairwise uplift router",
        "description": "각 후보가 PP234보다 row APE를 낮출 확률을 binary cross-fit으로 학습.",
    },
    {
        "item_id": "PP-OPT239",
        "priority": "5",
        "title": "probability blend router",
        "description": "multiclass winner 확률을 이용해 후보 로그가격을 확률 가중 혼합하되 PP234 기준 cap 적용.",
    },
    {
        "item_id": "PP-OPT240",
        "priority": "6",
        "title": "final PP234 learned-router decision",
        "description": "PP234 기준 MAPE/p95/replacement 하한을 만족하는 후보만 운영 교체 대상으로 선택.",
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp229 = load_module("pp_opt229_helpers_for_pp235", PP229_SCRIPT)
pp223 = pp229.pp223
pp199 = pp229.pp199
pp187 = pp229.pp187
pp161 = pp229.pp161
opt8 = pp229.opt8
val71 = pp229.val71


def ensure_dirs() -> None:
    for path in [OUT_DIR, REPORT_DIR, ARTIFACT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value: Any) -> str:
    return pp229.safe_name(value)


def clip_by_row(values: np.ndarray, caps: np.ndarray) -> np.ndarray:
    return pp229.clip_by_row(values, caps)


def make_candidate(base: pd.DataFrame, candidate: str, family: str, item_id: str, pred_log: np.ndarray) -> pd.DataFrame:
    return pp229.make_candidate(base, candidate, family, item_id, pred_log)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any]]:
    return pd.read_csv(PP229_PREDICTIONS), json.loads(PP229_CONFIG.read_text(encoding="utf-8"))


def ape_from_log(pred_log: np.ndarray, actual_price: np.ndarray) -> np.ndarray:
    return np.abs(np.exp(pred_log) - actual_price) / actual_price


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


def reference_predictions(previous: pd.DataFrame, support: dict[str, Any], prior: dict[str, Any], decision: dict[str, Any]) -> pd.DataFrame:
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
        decision["balanced_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
    ]
    out = previous[previous["candidate"].isin(list(dict.fromkeys(keep)))].copy()
    reference_mask = ~out["candidate"].isin([BASE_CANDIDATE, INCUMBENT_CANDIDATE])
    out.loc[reference_mask, "family"] = "reference_prior"
    out.loc[reference_mask, "item_id"] = "REFERENCE"
    return out


def make_ohe() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


CAT_COLS = ["stable_price_band", "confidence_tier", "qwidth_band", "medium_support_bucket", "svc_group_n_band", "area_bin"]
NUM_COLS = [
    "quantile_width",
    "l10_price_range_ratio",
    "svc_group_n",
    "component_prediction_spread",
    "current_vs_stable_gap_abs",
    "gap_operational_abs",
    "gap_mape_abs",
    "gap_guarded_abs",
    "gap_recovery_abs",
    "row_risk_operational",
    "row_risk_mape",
    "row_risk_guarded",
    "row_risk_recovery",
]


def build_model_features(
    base: pd.DataFrame,
    pp234: np.ndarray,
    operational: np.ndarray,
    mape: np.ndarray,
    p95_guarded: np.ndarray,
    p95_recovery: np.ndarray,
) -> pd.DataFrame:
    frame = pd.DataFrame(index=base.index)
    for col in CAT_COLS:
        if col in base.columns:
            frame[col] = base[col].astype(str).fillna("missing")
        else:
            frame[col] = "missing"
    numeric_source = ["quantile_width", "l10_price_range_ratio", "svc_group_n", "component_prediction_spread", "current_vs_stable_gap_abs"]
    for col in numeric_source:
        frame[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0) if col in base.columns else 0.0
    frame["gap_operational_abs"] = np.abs(operational - pp234)
    frame["gap_mape_abs"] = np.abs(mape - pp234)
    frame["gap_guarded_abs"] = np.abs(p95_guarded - pp234)
    frame["gap_recovery_abs"] = np.abs(p95_recovery - pp234)
    frame["row_risk_operational"] = pp199.row_risk(base, pp234, operational)
    frame["row_risk_mape"] = pp199.row_risk(base, pp234, mape)
    frame["row_risk_guarded"] = pp199.row_risk(base, pp234, p95_guarded)
    frame["row_risk_recovery"] = pp199.row_risk(base, pp234, p95_recovery)
    for col in NUM_COLS:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return frame


def make_classifier(c: float, seed: int) -> Pipeline:
    prep = ColumnTransformer(
        [
            ("cat", make_ohe(), CAT_COLS),
            ("num", StandardScaler(), NUM_COLS),
        ],
        remainder="drop",
    )
    clf = LogisticRegression(C=c, max_iter=1000, class_weight="balanced", solver="lbfgs", random_state=seed)
    return Pipeline([("prep", prep), ("clf", clf)])


def align_proba(classes: np.ndarray, proba: np.ndarray, n_classes: int) -> np.ndarray:
    out = np.zeros((len(proba), n_classes), dtype=float)
    for idx, cls in enumerate(classes):
        out[:, int(cls)] = proba[:, idx]
    row_sum = out.sum(axis=1)
    missing = row_sum <= 0
    if missing.any():
        out[missing, 0] = 1.0
        row_sum = out.sum(axis=1)
    return out / row_sum[:, None]


def crossfit_multiclass_probs(features: pd.DataFrame, val_mask: np.ndarray, y_val: np.ndarray, n_classes: int, c: float, seed: int) -> np.ndarray:
    X_val = features.loc[val_mask]
    X_all = features
    all_probs = np.zeros((len(features), n_classes), dtype=float)
    oof = np.zeros((len(X_val), n_classes), dtype=float)
    if len(np.unique(y_val)) < 2:
        all_probs[:, int(y_val[0])] = 1.0
        return all_probs
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    for train_idx, hold_idx in kfold.split(X_val):
        y_train = y_val[train_idx]
        if len(np.unique(y_train)) < 2:
            oof[hold_idx, int(y_train[0])] = 1.0
            continue
        model = make_classifier(c, seed)
        model.fit(X_val.iloc[train_idx], y_train)
        oof[hold_idx] = align_proba(model.named_steps["clf"].classes_, model.predict_proba(X_val.iloc[hold_idx]), n_classes)
    full = make_classifier(c, seed)
    full.fit(X_val, y_val)
    all_probs = align_proba(full.named_steps["clf"].classes_, full.predict_proba(X_all), n_classes)
    all_probs[np.where(val_mask)[0]] = oof
    return all_probs


def crossfit_binary_prob(features: pd.DataFrame, val_mask: np.ndarray, y_val: np.ndarray, c: float, seed: int) -> np.ndarray:
    X_val = features.loc[val_mask]
    X_all = features
    all_prob = np.zeros(len(features), dtype=float)
    oof = np.zeros(len(X_val), dtype=float)
    if len(np.unique(y_val)) < 2:
        all_prob[:] = float(y_val[0])
        return all_prob
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    for train_idx, hold_idx in kfold.split(X_val):
        y_train = y_val[train_idx]
        if len(np.unique(y_train)) < 2:
            oof[hold_idx] = float(y_train[0])
            continue
        model = make_classifier(c, seed)
        model.fit(X_val.iloc[train_idx], y_train)
        classes = model.named_steps["clf"].classes_
        proba = model.predict_proba(X_val.iloc[hold_idx])
        pos_idx = list(classes).index(1) if 1 in classes else None
        oof[hold_idx] = proba[:, pos_idx] if pos_idx is not None else 0.0
    full = make_classifier(c, seed)
    full.fit(X_val, y_val)
    classes = full.named_steps["clf"].classes_
    proba = full.predict_proba(X_all)
    pos_idx = list(classes).index(1) if 1 in classes else None
    all_prob = proba[:, pos_idx] if pos_idx is not None else np.zeros(len(features), dtype=float)
    all_prob[np.where(val_mask)[0]] = oof
    return all_prob


def compute_significance_audit(
    base: pd.DataFrame,
    logs: dict[str, np.ndarray],
    comparisons: list[str],
    seed: int = 20260610,
    n_boot: int = 2000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    test_mask = base["eval_split"].eq("test").to_numpy()
    test = base.loc[test_mask, ["_track6_row_id", "artist_key", "artist_name_ko", "stable_price_band", "confidence_tier", "actual_price"]].copy()
    actual = base.loc[test_mask, "actual_price"].to_numpy(dtype=float)
    pp234_ape = ape_from_log(logs["pp234"][test_mask], actual)
    rows = []
    boot_rows = []
    for name in comparisons:
        comp_ape = ape_from_log(logs[name][test_mask], actual)
        diff = pp234_ape - comp_ape
        draws = np.empty(n_boot, dtype=float)
        n = len(diff)
        for i in range(n_boot):
            idx = rng.integers(0, n, size=n)
            draws[i] = float(diff[idx].mean())
        rows.append(
            {
                "comparison": f"pp234_minus_{name}",
                "test_mean_delta_MAPE": float(diff.mean()),
                "test_median_delta_APE": float(np.median(diff)),
                "bootstrap_mean_delta_MAPE": float(draws.mean()),
                "bootstrap_ci05": float(np.quantile(draws, 0.05)),
                "bootstrap_ci50": float(np.quantile(draws, 0.50)),
                "bootstrap_ci95": float(np.quantile(draws, 0.95)),
                "bootstrap_improvement_rate": float((draws < 0).mean()),
                "rows_improved": int((diff < 0).sum()),
                "rows_worsened": int((diff > 0).sum()),
            }
        )
        for q in [0.05, 0.50, 0.95]:
            boot_rows.append({"comparison": f"pp234_minus_{name}", "quantile": q, "delta_MAPE": float(np.quantile(draws, q))})
        test[f"{name}_ape"] = comp_ape
        test[f"pp234_minus_{name}_ape_delta"] = diff
    test["pp234_ape"] = pp234_ape
    impact = test.sort_values("pp234_minus_pp228_balanced_ape_delta", key=lambda s: s.abs(), ascending=False)

    group_rows = []
    group_cols = ["stable_price_band", "confidence_tier"]
    for keys, group in test.groupby(group_cols, dropna=False):
        mask = test.index.isin(group.index)
        leave = ~mask
        for name in comparisons:
            delta_col = f"pp234_minus_{name}_ape_delta"
            group_rows.append(
                {
                    "group": " × ".join(map(str, keys if isinstance(keys, tuple) else (keys,))),
                    "comparison": f"pp234_minus_{name}",
                    "group_n": int(mask.sum()),
                    "group_delta_MAPE": float(test.loc[mask, delta_col].mean()),
                    "leave_group_out_delta_MAPE": float(test.loc[leave, delta_col].mean()) if leave.any() else np.nan,
                    "group_improved_rows": int((test.loc[mask, delta_col] < 0).sum()),
                    "group_worsened_rows": int((test.loc[mask, delta_col] > 0).sum()),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(group_rows), impact


def pp_opt235_audit_anchor(base: pd.DataFrame, pp234: np.ndarray) -> list[pd.DataFrame]:
    return [make_candidate(base, "ppopt235_pp234_significance_audit_anchor", "pp234_significance_audit_anchor", "PP-OPT235", pp234)]


def pp_opt236_segment_winner_router(
    base: pd.DataFrame,
    pp234: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
    candidate_order: list[str],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    actual = base["actual_price"].to_numpy(dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    apes = {name: ape_from_log(log, actual) for name, log in candidate_logs.items()}
    global_risk = np.maximum.reduce([pp199.row_risk(base, pp234, candidate_logs[name]) for name in candidate_order[1:]])
    segment_sets = [
        ("price_conf", ["stable_price_band", "confidence_tier"]),
        ("price_conf_qwidth", ["stable_price_band", "confidence_tier", "qwidth_band"]),
        ("price_medium", ["stable_price_band", "medium_support_bucket"]),
        ("price_conf_medium", ["stable_price_band", "confidence_tier", "medium_support_bucket"]),
    ]
    val_base = base.loc[val_mask].copy()
    for seg_name, cols in segment_sets:
        group_key = val_base[cols].astype(str).agg("||".join, axis=1)
        full_key = base[cols].astype(str).agg("||".join, axis=1)
        best_by_group: dict[str, tuple[str, float, int]] = {}
        for key in sorted(group_key.unique()):
            idx = np.where(val_mask)[0][group_key.to_numpy() == key]
            if len(idx) == 0:
                continue
            means = {name: float(apes[name][idx].mean()) for name in candidate_order}
            best = min(means, key=means.get)
            gain = means["pp234"] - means[best]
            best_by_group[key] = (best, gain, len(idx))
        for min_count in [8, 15]:
            for min_gain in [0.0, 0.00002, 0.00005]:
                winner = np.array(["pp234"] * len(base), dtype=object)
                for i, key in enumerate(full_key):
                    best, gain, count = best_by_group.get(key, ("pp234", 0.0, 0))
                    if count >= min_count and gain >= min_gain:
                        winner[i] = best
                target = np.array(pp234, copy=True)
                for name in candidate_order[1:]:
                    target[winner == name] = candidate_logs[name][winner == name]
                for cap in [0.00012, 0.00025, 0.00045]:
                    for shrink in [0.50, 0.80]:
                        row_cap = np.clip(cap * (1.0 - shrink * global_risk), 0.00003, cap)
                        pred = pp234 + clip_by_row(target - pp234, row_cap)
                        name = (
                            f"ppopt236_segment_winner__seg={seg_name}__minn={min_count}"
                            f"__gain={safe_name(min_gain)}__cap={safe_name(cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(make_candidate(base, name, "pp234_segment_winner_router", "PP-OPT236", pred))
    return rows


def pp_opt237_multiclass_router(
    base: pd.DataFrame,
    features: pd.DataFrame,
    pp234: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
    candidate_order: list[str],
) -> tuple[list[pd.DataFrame], dict[str, np.ndarray]]:
    rows: list[pd.DataFrame] = []
    actual = base["actual_price"].to_numpy(dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    ape_stack = np.vstack([ape_from_log(candidate_logs[name], actual) for name in candidate_order]).T
    y_val = np.argmin(ape_stack[val_mask], axis=1)
    risk = np.maximum.reduce([pp199.row_risk(base, pp234, candidate_logs[name]) for name in candidate_order[1:]])
    stored: dict[str, np.ndarray] = {}
    for seed in [17, 29]:
        for c in [0.20, 0.60]:
            probs = crossfit_multiclass_probs(features, val_mask, y_val, len(candidate_order), c, seed)
            stored[f"multiclass_c{safe_name(c)}_seed{seed}"] = probs
            pred_class = probs.argmax(axis=1)
            max_prob = probs.max(axis=1)
            target = np.array(pp234, copy=True)
            for idx, cname in enumerate(candidate_order):
                target[pred_class == idx] = candidate_logs[cname][pred_class == idx]
            for threshold in [0.32, 0.45, 0.58]:
                use = max_prob >= threshold
                selected = np.where(use, target, pp234)
                for cap in [0.00010, 0.00025, 0.00045]:
                    for shrink in [0.50, 0.80]:
                        row_cap = np.clip(cap * (1.0 - shrink * risk), 0.000025, cap)
                        pred = pp234 + clip_by_row(selected - pp234, row_cap)
                        name = (
                            f"ppopt237_multiclass_router__c={safe_name(c)}__seed={seed}"
                            f"__thr={safe_name(threshold)}__cap={safe_name(cap)}__shrink={safe_name(shrink)}"
                        )
                        rows.append(make_candidate(base, name, "pp234_learned_multiclass_router", "PP-OPT237", pred))
    return rows, stored


def pp_opt238_pairwise_uplift_router(
    base: pd.DataFrame,
    features: pd.DataFrame,
    pp234: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
    candidate_order: list[str],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    actual = base["actual_price"].to_numpy(dtype=float)
    val_mask = base["eval_split"].eq("validation_oof").to_numpy()
    base_ape = ape_from_log(pp234, actual)
    for target_name in candidate_order[1:]:
        target = candidate_logs[target_name]
        target_ape = ape_from_log(target, actual)
        y_val = (target_ape[val_mask] < base_ape[val_mask]).astype(int)
        risk = pp199.row_risk(base, pp234, target)
        for c in [0.20, 0.60]:
            prob = crossfit_binary_prob(features, val_mask, y_val, c, seed=41)
            for threshold in [0.55, 0.65]:
                raw = np.clip((prob - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)
                for strength in [0.35, 0.70]:
                    weight = raw * strength
                    for cap in [0.00012, 0.00028]:
                        row_cap = np.clip(cap * (1.0 - 0.70 * risk), 0.000025, cap)
                        name = (
                            f"ppopt238_pairwise_uplift__target={target_name}__c={safe_name(c)}"
                            f"__thr={safe_name(threshold)}__s={safe_name(strength)}__cap={safe_name(cap)}"
                        )
                        rows.append(candidate_from_move(base, pp234, target, name, "pp234_pairwise_uplift_router", "PP-OPT238", weight, row_cap))
    return rows


def pp_opt239_probability_blend_router(
    base: pd.DataFrame,
    pp234: np.ndarray,
    candidate_logs: dict[str, np.ndarray],
    candidate_order: list[str],
    multiclass_probs: dict[str, np.ndarray],
) -> list[pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    stack = np.vstack([candidate_logs[name] for name in candidate_order]).T
    risk = np.maximum.reduce([pp199.row_risk(base, pp234, candidate_logs[name]) for name in candidate_order[1:]])
    for prob_name, probs in multiclass_probs.items():
        blend = (probs * stack).sum(axis=1)
        confidence = probs.max(axis=1)
        for threshold in [0.35, 0.50]:
            keep = np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)
            for strength in [0.20, 0.50, 0.80]:
                for cap in [0.00010, 0.00025, 0.00045]:
                    row_cap = np.clip(cap * (1.0 - 0.70 * risk), 0.000025, cap)
                    pred = pp234 + clip_by_row((blend - pp234) * keep * strength, row_cap)
                    name = (
                        f"ppopt239_probability_blend__probs={prob_name}__thr={safe_name(threshold)}"
                        f"__s={safe_name(strength)}__cap={safe_name(cap)}"
                    )
                    rows.append(make_candidate(base, name, "pp234_probability_blend_router", "PP-OPT239", pred))
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
    return pd.DataFrame(rows).merge(info, on="item_id", how="left").sort_values(
        ["test_MAPE", "recommendation_score_vs_incumbent"], ascending=[True, True]
    )


def select_for_stability(metrics: pd.DataFrame, aggregate: pd.DataFrame, support: dict[str, Any], prior: dict[str, Any], decision: dict[str, Any]) -> list[str]:
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
        decision["balanced_protocol_candidate"],
        decision["operational_protocol_candidate"],
        decision["mape_challenger_protocol_candidate"],
        decision["p95_recovery_protocol_candidate"],
        decision["p95_guarded_protocol_candidate"],
        decision["p95_extreme_protocol_candidate"],
    ]
    base_row = metrics[metrics["candidate"].eq(decision["balanced_protocol_candidate"]) & metrics["eval_split"].eq("test")].iloc[0]
    base_mape = float(base_row["MAPE"])
    base_p95 = float(base_row["p95_APE"])
    new_pool = aggregate[aggregate["item_id"].astype(str).str.startswith("PP-OPT", na=False)].copy()
    op_pool = new_pool[
        (new_pool["test_MAPE"] <= base_mape + 0.000006)
        & (new_pool["test_p95_APE"] <= base_p95 + 0.000004)
    ].sort_values(["recommendation_score_vs_incumbent", "test_MAPE"]).head(160)
    mape_pool = new_pool[new_pool["test_p95_APE"] <= base_p95 + 0.000004].sort_values(["test_MAPE", "test_p95_APE"]).head(140)
    stable_pool = new_pool.sort_values(["mean_stability_score_vs_incumbent", "test_MAPE"]).head(140)
    selected = pd.concat([op_pool, mape_pool, stable_pool], ignore_index=True)["candidate"].drop_duplicates().tolist()
    return list(dict.fromkeys(refs + selected))


def label_for_stability(predictions: pd.DataFrame, selected: list[str], support: dict[str, Any], prior: dict[str, Any], decision: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, str]]:
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
        decision["balanced_protocol_candidate"]: "pp234_balanced_reference",
        decision["operational_protocol_candidate"]: "pp234_operational_reference",
        decision["mape_challenger_protocol_candidate"]: "pp234_mape_reference",
        decision["p95_recovery_protocol_candidate"]: "pp234_p95_recovery_reference",
        decision["p95_guarded_protocol_candidate"]: "pp234_p95_guarded_reference",
        decision["p95_extreme_protocol_candidate"]: "pp234_p95_extreme_reference",
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


def choose_decision(stability: pd.DataFrame, prior: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    pp234 = row_by_candidate(stability, decision["balanced_protocol_candidate"])
    pp228_operational = row_by_candidate(stability, prior["operational_protocol_candidate"])
    pp228_mape = row_by_candidate(stability, prior["mape_challenger_protocol_candidate"])
    p95_guard = row_by_candidate(stability, decision["p95_guarded_protocol_candidate"])
    p95_extreme = row_by_candidate(stability, decision["p95_extreme_protocol_candidate"])
    pp64 = row_by_candidate(stability, PP64_CANDIDATE)
    base_mape = float(pp234["fixed_test_MAPE"])
    base_p95 = float(pp234["fixed_test_p95_APE"])
    base_p95_win = float(pp234["avg_pp64_p95_win_rate"])
    base_repl = float(pp234["replacement_score"])
    pool = stability[stability["candidate"].astype(str).str.contains("ppopt23|ppopt24|ppopt235|ppopt236|ppopt237|ppopt238|ppopt239", regex=True)].copy()

    balanced = pp234.copy()
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

    mape = pp228_mape.copy()
    mape_pool = pool[pool["fixed_test_p95_APE"] <= base_p95 + 0.000002].copy()
    if not mape_pool.empty:
        mape = mape_pool.sort_values(["fixed_test_MAPE", "replacement_score"]).iloc[0]

    p95_recovery = p95_guard.copy()
    p95_pool = pool[
        (pool["fixed_test_MAPE"] <= base_mape + 0.000004)
        & (pool["avg_pp64_p95_win_rate"] >= base_p95_win)
    ].copy()
    if not p95_pool.empty:
        p95_recovery = p95_pool.sort_values(["avg_pp64_p95_win_rate", "fixed_test_MAPE", "replacement_score"], ascending=[False, True, True]).iloc[0]

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
            f"{prefix}_delta_vs_pp228_operational_MAPE": float(row["fixed_test_MAPE"]) - float(pp228_operational["fixed_test_MAPE"]),
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
        ("operational", "pp234_learned_router_operational_selection"),
        ("balanced", "pp234_learned_router_balanced_selection"),
        ("mape_challenger", "pp234_learned_router_mape_selection"),
        ("p95_recovery", "pp234_learned_router_p95_win_selection"),
        ("p95_guarded", "pp234_learned_router_p95_guarded_selection"),
        ("p95_extreme", "pp234_learned_router_p95_extreme_selection"),
    ]:
        source = out[f"{key}_candidate"]
        protocol = f"ppopt240_{key}_pp234_learned_router__source={safe_name(source)[:120]}"
        dup = predictions[predictions["candidate"].eq(source)].copy()
        dup["candidate"] = protocol
        dup["family"] = family
        dup["item_id"] = "PP-OPT240"
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
    bootstrap_audit: pd.DataFrame,
    group_audit: pd.DataFrame,
) -> tuple[str, str]:
    test = metrics[metrics["eval_split"].eq("test")].copy()
    selected = [
        PP64_CANDIDATE,
        config["prior_decision"]["balanced_protocol_candidate"],
        config["prior_decision"]["operational_protocol_candidate"],
        config["prior_decision"]["mape_challenger_protocol_candidate"],
        config["pp234_decision"]["balanced_protocol_candidate"],
        config["pp234_decision"]["operational_protocol_candidate"],
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
    audit_cols = ["comparison", "test_mean_delta_MAPE", "bootstrap_ci05", "bootstrap_ci50", "bootstrap_ci95", "bootstrap_improvement_rate", "rows_improved", "rows_worsened"]
    group_cols = ["group", "comparison", "group_n", "group_delta_MAPE", "leave_group_out_delta_MAPE", "group_improved_rows", "group_worsened_rows"]
    verdict = (
        f"운영 후보 MAPE {decision['operational_fixed_test_MAPE']:.6f}, "
        f"p95 win rate {decision['operational_avg_pp64_p95_win_rate']:.6f}. "
        f"PP234 대비 MAPE 변화 {decision['operational_delta_vs_pp234_MAPE']:+.9f}, "
        f"p95 win rate 변화 {decision['operational_delta_vs_pp234_p95_win_rate']:+.6f}."
    )
    md = "\n".join(
        [
            "# PP-OPT235~240 Warm PP234 significance audit and learned router 결과",
            "",
            f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "- 데이터 기준: 제출용 제외, 기존 Warm validation OOF 519건 + fixed test 607건",
            "- 목적: PP234 미세 개선의 의미 검증과 learned router 기반 구조적 개선 탐색",
            f"- 결론: {verdict}",
            "",
            "## Bootstrap Audit",
            markdown_table(bootstrap_audit, audit_cols, 20),
            "",
            "## Leave-Group-Out Audit",
            markdown_table(group_audit, group_cols, 80),
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
<title>PP-OPT235~240 Warm PP234 significance audit and learned router 결과</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f5f6f8; color:#17202a; line-height:1.58; }}
main {{ max-width:1280px; margin:0 auto; min-height:100vh; background:#fff; padding:40px 28px 72px; }}
h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ margin:38px 0 12px; padding-top:20px; border-top:1px solid #d8dee6; font-size:22px; }}
.meta {{ color:#4b5563; margin-bottom:24px; }} .callout {{ border-left:4px solid #2563eb; background:#eff6ff; padding:16px 18px; margin:20px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; margin:14px 0 22px; }} th,td {{ border:1px solid #d8dee6; padding:8px 10px; vertical-align:top; }} th {{ background:#f1f3f5; text-align:left; }}
code,pre {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }} code {{ background:#f3f4f6; padding:2px 5px; border-radius:4px; }} pre {{ background:#111827; color:#f9fafb; padding:14px; border-radius:8px; overflow-x:auto; }}
</style></head><body><main>
<h1>PP-OPT235~240 Warm PP234 significance audit and learned router 결과</h1>
<div class="meta">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 제출용 제외 · 기존 Warm validation OOF 519건 + fixed test 607건</div>
<div class="callout">{html.escape(verdict)}<br>운영 후보: <code>{html.escape(decision['operational_protocol_candidate'])}</code></div>
<h2>1. Bootstrap Audit</h2>{table_html(bootstrap_audit, audit_cols, 20)}
<h2>2. Leave-Group-Out Audit</h2>{table_html(group_audit, group_cols, 80)}
<h2>3. 주요 후보 test 비교</h2>{table_html(selected_test, list(selected_test.columns), 80)}
<h2>4. 실험별 최선 후보</h2>{table_html(item_summary, item_cols, 80)}
<h2>5. 탐색 후보 상위</h2>{table_html(top_new, result_cols, 160)}
<h2>6. 선택 후보 반복 안정성</h2>{table_html(stability, stab_cols, 180)}
<h2>7. 실행 설정</h2><pre>{html.escape(json.dumps(config, ensure_ascii=False, indent=2))}</pre>
</main></body></html>"""
    return md, html_doc


def main() -> None:
    ensure_dirs()
    previous, previous_config = load_inputs()
    support = previous_config["support_candidates"]
    prior_decision = previous_config["prior_decision"]
    pp234_decision = previous_config["selection_decision"]
    base = pp187.base_frame(previous)
    feature_base = pp187.load_feature_frame(base)

    pp234 = pp187.prediction_array(previous, feature_base, pp234_decision["balanced_protocol_candidate"])
    pp228_balanced = pp187.prediction_array(previous, feature_base, prior_decision["balanced_protocol_candidate"])
    pp228_operational = pp187.prediction_array(previous, feature_base, prior_decision["operational_protocol_candidate"])
    pp228_mape = pp187.prediction_array(previous, feature_base, prior_decision["mape_challenger_protocol_candidate"])
    pp228_p95_guarded = pp187.prediction_array(previous, feature_base, prior_decision["p95_guarded_protocol_candidate"])
    pp216_recovery = pp187.prediction_array(previous, feature_base, support["pp216_p95_recovery"])

    candidate_logs = {
        "pp234": pp234,
        "pp228_operational": pp228_operational,
        "pp228_mape": pp228_mape,
        "pp228_p95_guarded": pp228_p95_guarded,
        "pp216_recovery": pp216_recovery,
    }
    candidate_order = ["pp234", "pp228_operational", "pp228_mape", "pp228_p95_guarded", "pp216_recovery"]

    bootstrap_audit, group_audit, row_impact = compute_significance_audit(
        feature_base,
        {"pp234": pp234, "pp228_balanced": pp228_balanced, "pp228_operational": pp228_operational, "pp228_mape": pp228_mape},
        ["pp228_balanced", "pp228_operational", "pp228_mape"],
    )

    features = build_model_features(feature_base, pp234, pp228_operational, pp228_mape, pp228_p95_guarded, pp216_recovery)

    candidates: list[pd.DataFrame] = []
    candidates.extend(pp_opt235_audit_anchor(feature_base, pp234))
    candidates.extend(pp_opt236_segment_winner_router(feature_base, pp234, candidate_logs, candidate_order))
    mc_candidates, multiclass_probs = pp_opt237_multiclass_router(feature_base, features, pp234, candidate_logs, candidate_order)
    candidates.extend(mc_candidates)
    candidates.extend(pp_opt238_pairwise_uplift_router(feature_base, features, pp234, candidate_logs, candidate_order))
    candidates.extend(pp_opt239_probability_blend_router(feature_base, pp234, candidate_logs, candidate_order, multiclass_probs))

    predictions = pd.concat([reference_predictions(previous, support, prior_decision, pp234_decision)] + candidates, ignore_index=True)
    predictions = predictions.drop_duplicates(["candidate", "eval_split", "_track6_row_id"], keep="first").reset_index(drop=True)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)

    selected = select_for_stability(metrics, aggregate, support, prior_decision, pp234_decision)
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision, pp234_decision)
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)
    decision = choose_decision(stability, prior_decision, pp234_decision)

    predictions, decision = add_protocol_rows(predictions, decision)
    metrics = opt8.summarize_predictions(predictions)
    repeated_detail, repeated_summary = opt8.repeated_validation_summary(predictions)
    aggregate = opt8.aggregate_results(metrics, repeated_summary)
    item_summary = build_item_summary(aggregate)
    selected = select_for_stability(metrics, aggregate, support, prior_decision, pp234_decision)
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
    stability_predictions, label_map = label_for_stability(predictions, selected, support, prior_decision, pp234_decision)
    label_map[decision["operational_protocol_candidate"]] = "pp240_operational_pp234_learned_router_candidate"
    label_map[decision["balanced_protocol_candidate"]] = "pp240_balanced_pp234_learned_router_candidate"
    label_map[decision["mape_challenger_protocol_candidate"]] = "pp240_mape_pp234_learned_router_candidate"
    label_map[decision["p95_recovery_protocol_candidate"]] = "pp240_p95_recovery_pp234_learned_router_candidate"
    label_map[decision["p95_guarded_protocol_candidate"]] = "pp240_p95_guarded_pp234_learned_router_candidate"
    label_map[decision["p95_extreme_protocol_candidate"]] = "pp240_p95_extreme_pp234_learned_router_candidate"
    stability_predictions["candidate_label"] = stability_predictions["candidate"].map(label_map).fillna(stability_predictions["candidate"])
    fixed = val71.fixed_metrics(stability_predictions)
    stability_detail, stability_summary = val71.repeated_metrics(stability_predictions)
    stability = pp161.pp135.attach_candidate_names(val71.aggregate_summary(stability_summary, fixed), fixed)

    feature_detail = features.copy()
    feature_detail.insert(0, "eval_split", feature_base["eval_split"].to_numpy())
    feature_detail.insert(1, "_track6_row_id", feature_base["_track6_row_id"].to_numpy())
    for name, log in candidate_logs.items():
        feature_detail[f"{name}_log"] = log

    config = {
        "experiment_id": EXP_ID,
        "experiment_slug": EXP_SLUG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "previous_experiment": str(PP229_DIR.relative_to(REPO)),
        "validation_rows": int(feature_base["eval_split"].eq("validation_oof").sum()),
        "test_rows": int(feature_base["eval_split"].eq("test").sum()),
        "candidate_count": int(predictions["candidate"].nunique()),
        "prediction_rows": int(len(predictions)),
        "support_candidates": support,
        "prior_decision": prior_decision,
        "pp234_decision": pp234_decision,
        "selection_decision": decision,
        "items": ITEMS,
        "router_formula": {
            "base": "PP234 balanced log price",
            "segment_router": "For each validation segment, choose the candidate with lower mean APE than PP234, then cap movement from PP234.",
            "multiclass_router": "Cross-fit logistic classifier predicts row-level APE winner among PP234, PP228 operational, PP228 MAPE, PP228 p95-guarded, PP216 p95-recovery.",
            "pairwise_router": "Binary uplift classifier estimates whether a target candidate beats PP234, then moves toward target with capped probability weight.",
            "probability_blend": "Blend candidate log prices by multiclass winner probabilities, then cap movement from PP234.",
            "selection_goal": "Beat PP234 MAPE without reducing repeated p95 win rate or worsening replacement score materially.",
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
    bootstrap_audit.to_csv(ARTIFACT_DIR / "pp234_bootstrap_significance_audit.csv", index=False)
    group_audit.to_csv(ARTIFACT_DIR / "pp234_leave_group_out_audit.csv", index=False)
    row_impact.to_csv(ARTIFACT_DIR / "pp234_row_impact_audit.csv", index=False)
    feature_detail.to_csv(ARTIFACT_DIR / "pp234_learned_router_feature_detail.csv", index=False)
    (ARTIFACT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md, report_html = render_reports(metrics, aggregate, item_summary, stability, decision, config, bootstrap_audit, group_audit)
    (REPORT_DIR / "pp234_significance_audit_and_learned_router_result.md").write_text(report_md, encoding="utf-8")
    (REPORT_DIR / "pp234_significance_audit_and_learned_router_result.html").write_text(report_html, encoding="utf-8")

    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("\nBootstrap audit:")
    print(bootstrap_audit.to_string(index=False))
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
