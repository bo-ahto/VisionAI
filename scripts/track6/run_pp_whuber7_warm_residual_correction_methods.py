#!/usr/bin/env python3
"""Run PP-WHUBER7 Warm residual Huber correction method experiments.

PP-WHUBER5 showed that the useful direction is not replacing the current Warm
candidate, but applying a small Huber residual correction on top of it. This
follow-up keeps the same base prediction and compares correction application
policies:

1. hard clipped residual correction
2. smooth tanh capped correction
3. reliability shrink correction
4. asymmetric under/over prediction correction
5. prediction-bin-specific cap correction
6. hybrid reliability + prediction-bin correction
"""
from __future__ import annotations

import html
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import KFold


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_wcoef_warm_huber_feature_coefficient_refinement as wcoef  # noqa: E402
import run_pp_whuber_warm_huber_loss_regularization_tuning as whuber  # noqa: E402


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", message="Skipping features without any observed values.*")


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-WHUBER7"
EXP_SLUG = "PP-WHUBER7_warm_residual_huber_correction_methods"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm residual Huber 보정 방식 세분화 실험"
SEED = 20260606
BOOTSTRAP_ITERATIONS = 300

CURRENT_CANDIDATE = wcoef.CURRENT_CANDIDATE

EPSILONS = [1.05, 1.20, 1.35, 1.60]
ALPHAS = [0.001, 0.01]
GLOBAL_CAPS = [0.04, 0.06, 0.08]
GLOBAL_STRENGTHS = [0.20, 0.25, 0.30]

RELIABILITY_POLICIES = {
    "soft_rel": {"high": 1.00, "mid": 0.80, "low": 0.55, "missing": 0.35},
    "strict_rel": {"high": 1.00, "mid": 0.70, "low": 0.40, "missing": 0.20},
}

PRED_BIN_CAP_POLICIES = {
    "mid_open_tail_guard": {"low": 0.70, "mid_low": 1.00, "mid_high": 1.00, "high": 0.75, "missing": 0.60},
    "tail_open_mid_guard": {"low": 1.00, "mid_low": 0.80, "mid_high": 0.80, "high": 1.00, "missing": 0.60},
}

DIRECTIONAL_POLICIES = {
    "under_guard": {"positive": 0.20, "negative": 0.30},
    "over_guard": {"positive": 0.30, "negative": 0.20},
    "balanced_direction": {"positive": 0.25, "negative": 0.25},
}


def ensure_dirs() -> None:
    for subdir in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def load_reference_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    train, val, test = wcoef.load_frames()
    train, val, test = whuber.add_combined_segments(train, val, test)
    val_ref, test_ref, _ = wcoef.add_reference_prediction_features(val, test)
    return val_ref, test_ref


def feature_sets() -> dict[str, list[str]]:
    return {
        "pred_size_svc": whuber.residual_feature_sets()["pred_size_svc"],
        "pred_size_material_svc_artist": whuber.residual_feature_sets()["pred_size_material_svc_artist"],
    }


def actual_log_array(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_numeric(frame["ln_price_krw"], errors="coerce").to_numpy(dtype=float)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    return wcoef.metric_values(frame, pred_log)


def safe_label(value: float | str) -> str:
    return str(value).replace(".", "p").replace("-", "m")


def crossfit_residual(frame: pd.DataFrame, features: list[str], alpha: float, epsilon: float) -> np.ndarray:
    folds = min(5, max(2, len(frame) // 100))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    pred = np.zeros(len(frame), dtype=float)
    y = actual_log_array(frame) - frame["current_pred_log"].to_numpy(dtype=float)
    for train_idx, holdout_idx in kfold.split(frame):
        model = whuber.huber_model(features, alpha, epsilon)
        tr = whuber.normalize(frame.iloc[train_idx].copy(), features)
        ho = whuber.normalize(frame.iloc[holdout_idx].copy(), features)
        model.fit(tr[features], y[train_idx])
        pred[holdout_idx] = np.asarray(model.predict(ho[features]), dtype=float)
    return pred


def fit_raw_residual_models(val: pd.DataFrame, test: pd.DataFrame) -> dict[str, dict[str, Any]]:
    raw_models: dict[str, dict[str, Any]] = {}
    y_val = actual_log_array(val) - val["current_pred_log"].to_numpy(dtype=float)
    for feature_set_name, raw_features in feature_sets().items():
        features = whuber.feature_exists(val, raw_features)
        va = whuber.normalize(val, features)
        te = whuber.normalize(test, features)
        for epsilon in EPSILONS:
            for alpha in ALPHAS:
                label = f"{feature_set_name}_eps{epsilon:.2f}_alpha{safe_label(alpha)}"
                val_raw = crossfit_residual(val, features, alpha, epsilon)
                model = whuber.huber_model(features, alpha, epsilon)
                model.fit(va[features], y_val)
                test_raw = np.asarray(model.predict(te[features]), dtype=float)
                raw_models[label] = {
                    "feature_set": feature_set_name,
                    "features": features,
                    "epsilon": epsilon,
                    "alpha": alpha,
                    "validation_raw": val_raw,
                    "test_raw": test_raw,
                }
    return raw_models


def rel_multiplier(frame: pd.DataFrame, policy_name: str) -> np.ndarray:
    policy = RELIABILITY_POLICIES[policy_name]
    rel = frame.get("svc_reliability_bin", pd.Series(["missing"] * len(frame))).astype(str)
    return rel.map(policy).fillna(policy["missing"]).to_numpy(dtype=float)


def pred_bin_cap(frame: pd.DataFrame, base_cap: float, policy_name: str) -> np.ndarray:
    policy = PRED_BIN_CAP_POLICIES[policy_name]
    bins = frame.get("pred_log_bin", pd.Series(["missing"] * len(frame))).astype(str)
    scale = bins.map(policy).fillna(policy["missing"]).to_numpy(dtype=float)
    return base_cap * scale


def correction_variants(frame: pd.DataFrame, raw: np.ndarray) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    raw = np.asarray(raw, dtype=float)

    for cap in GLOBAL_CAPS:
        for strength in GLOBAL_STRENGTHS:
            correction = np.clip(raw, -cap, cap) * strength
            variants.append({
                "method": "hard_clip",
                "suffix": f"clip_cap{safe_label(cap)}_s{safe_label(strength)}",
                "correction": correction,
                "correction_cap": cap,
                "correction_strength": strength,
                "policy": "global",
            })

            smooth = cap * np.tanh(raw / max(cap, 1e-6)) * strength
            variants.append({
                "method": "soft_tanh_cap",
                "suffix": f"tanh_cap{safe_label(cap)}_s{safe_label(strength)}",
                "correction": smooth,
                "correction_cap": cap,
                "correction_strength": strength,
                "policy": "global",
            })

    for cap in [0.06, 0.08]:
        for strength in [0.25, 0.35]:
            base = np.clip(raw, -cap, cap) * strength
            for policy_name in RELIABILITY_POLICIES:
                correction = base * rel_multiplier(frame, policy_name)
                variants.append({
                    "method": "reliability_shrink",
                    "suffix": f"rel_{policy_name}_cap{safe_label(cap)}_s{safe_label(strength)}",
                    "correction": correction,
                    "correction_cap": cap,
                    "correction_strength": strength,
                    "policy": policy_name,
                })

            for policy_name in PRED_BIN_CAP_POLICIES:
                caps = pred_bin_cap(frame, cap, policy_name)
                correction = np.clip(raw, -caps, caps) * strength
                variants.append({
                    "method": "pred_bin_cap",
                    "suffix": f"predbin_{policy_name}_cap{safe_label(cap)}_s{safe_label(strength)}",
                    "correction": correction,
                    "correction_cap": cap,
                    "correction_strength": strength,
                    "policy": policy_name,
                })

    for cap in [0.06, 0.08]:
        for policy_name, policy in DIRECTIONAL_POLICIES.items():
            clipped = np.clip(raw, -cap, cap)
            correction = np.where(
                clipped >= 0,
                clipped * policy["positive"],
                clipped * policy["negative"],
            )
            variants.append({
                "method": "directional_strength",
                "suffix": f"dir_{policy_name}_cap{safe_label(cap)}",
                "correction": correction,
                "correction_cap": cap,
                "correction_strength": np.nan,
                "policy": policy_name,
            })

    for cap in [0.08]:
        for strength in [0.25, 0.35]:
            for rel_policy in RELIABILITY_POLICIES:
                for bin_policy in PRED_BIN_CAP_POLICIES:
                    caps = pred_bin_cap(frame, cap, bin_policy)
                    correction = np.clip(raw, -caps, caps) * strength
                    correction = correction * rel_multiplier(frame, rel_policy)
                    variants.append({
                        "method": "hybrid_rel_predbin",
                        "suffix": f"hybrid_{rel_policy}_{bin_policy}_cap{safe_label(cap)}_s{safe_label(strength)}",
                        "correction": correction,
                        "correction_cap": cap,
                        "correction_strength": strength,
                        "policy": f"{rel_policy}+{bin_policy}",
                    })
    return variants


def prediction_frame(
    sub_experiment: str,
    candidate: str,
    method: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "candidate": candidate,
        "method": method,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": np.asarray(pred_log, dtype=float),
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).astype(str).to_numpy(),
        "svc_reliability_bin": frame.get("svc_reliability_bin", pd.Series(["missing"] * len(frame))).astype(str).to_numpy(),
        "pred_log_bin": frame.get("pred_log_bin", pd.Series(["missing"] * len(frame))).astype(str).to_numpy(),
        "size_bin": frame.get("size_bin", pd.Series(["missing"] * len(frame))).astype(str).to_numpy(),
        "artist_works_bin": frame.get("artist_works_bin", pd.Series(["missing"] * len(frame))).astype(str).to_numpy(),
    })
    out["pred_price"] = np.clip(np.exp(out["pred_log"].to_numpy(dtype=float)), 1_000.0, None)
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    if extra:
        for key, value in extra.items():
            if np.isscalar(value):
                out[key] = value
            else:
                out[key] = value
    return out


def add_metric_row(
    rows: list[dict[str, Any]],
    sub_experiment: str,
    family: str,
    candidate: str,
    split: str,
    method: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    raw_info: dict[str, Any] | None = None,
    variant_info: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": EXP_ID,
        "sub_experiment": sub_experiment,
        "family": family,
        "candidate": candidate,
        "split": split,
        "method": method,
        **metric_values(frame, pred_log),
    }
    if raw_info:
        row.update({
            "raw_model": raw_info["raw_model"],
            "feature_set": raw_info["feature_set"],
            "epsilon": raw_info["epsilon"],
            "alpha": raw_info["alpha"],
        })
    if variant_info:
        row.update({
            "correction_cap": variant_info.get("correction_cap", np.nan),
            "correction_strength": variant_info.get("correction_strength", np.nan),
            "correction_policy": variant_info.get("policy", ""),
            "mean_abs_correction": float(np.mean(np.abs(variant_info["correction"]))),
            "p95_abs_correction": float(np.quantile(np.abs(variant_info["correction"]), 0.95)),
        })
    rows.append(row)


def run_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []

    for split_name, frame in [("validation", val), ("test", test)]:
        current_pred = frame["current_pred_log"].to_numpy(dtype=float)
        add_metric_row(
            rows,
            "REFERENCE",
            "reference",
            CURRENT_CANDIDATE,
            split_name,
            "reference_prediction",
            frame,
            current_pred,
        )
        preds.append(prediction_frame("REFERENCE", CURRENT_CANDIDATE, "reference_prediction", split_name, frame, current_pred))

    raw_models = fit_raw_residual_models(val, test)
    for raw_label, raw_info in raw_models.items():
        raw_meta = {
            "raw_model": raw_label,
            "feature_set": raw_info["feature_set"],
            "epsilon": raw_info["epsilon"],
            "alpha": raw_info["alpha"],
        }
        for split_name, frame, raw in [
            ("validation", val, raw_info["validation_raw"]),
            ("test", test, raw_info["test_raw"]),
        ]:
            current = frame["current_pred_log"].to_numpy(dtype=float)
            for variant in correction_variants(frame, raw):
                candidate = f"{EXP_ID}_{raw_label}_{variant['suffix']}"
                pred = current + variant["correction"]
                add_metric_row(
                    rows,
                    EXP_ID,
                    variant["method"],
                    candidate,
                    split_name,
                    variant["method"],
                    frame,
                    pred,
                    raw_meta,
                    variant,
                )
                preds.append(prediction_frame(
                    EXP_ID,
                    candidate,
                    variant["method"],
                    split_name,
                    frame,
                    pred,
                    {
                        "raw_model": raw_label,
                        "feature_set": raw_info["feature_set"],
                        "epsilon": raw_info["epsilon"],
                        "alpha": raw_info["alpha"],
                        "correction_cap": variant.get("correction_cap", np.nan),
                        "correction_strength": variant.get("correction_strength", np.nan),
                        "correction_policy": variant.get("policy", ""),
                        "correction_log": variant["correction"],
                    },
                ))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def select_validation_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    val = metrics[metrics["split"].eq("validation")].copy()
    current = val[val["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    val["balanced_score"] = (
        0.45 * val["MdAPE"] / float(current["MdAPE"])
        + 0.35 * val["MAPE"] / float(current["MAPE"])
        + 0.20 * val["p95_APE"] / float(current["p95_APE"])
    )
    non_ref = val[~val["sub_experiment"].eq("REFERENCE")].copy()
    selectors = {
        "MdAPE 우선": (non_ref, ["MdAPE", "MAPE", "p95_APE"]),
        "MAPE 우선 + MdAPE 3% 이내": (
            non_ref[non_ref["MdAPE"] <= float(current["MdAPE"]) * 1.03].copy(),
            ["MAPE", "MdAPE", "p95_APE"],
        ),
        "p95 우선 + MdAPE 5% 이내": (
            non_ref[non_ref["MdAPE"] <= float(current["MdAPE"]) * 1.05].copy(),
            ["p95_APE", "MdAPE", "MAPE"],
        ),
        "균형 점수": (non_ref, ["balanced_score", "MdAPE", "MAPE", "p95_APE"]),
    }
    rows: list[dict[str, Any]] = []
    test = metrics[metrics["split"].eq("test")].set_index("candidate")
    for objective, (pool, sort_cols) in selectors.items():
        if pool.empty:
            pool = non_ref
        selected = pool.sort_values(sort_cols).iloc[0]
        row = {
            "selection_objective": objective,
            "selected_candidate": selected["candidate"],
            "method": selected["method"],
            "family": selected["family"],
            "validation_MdAPE": float(selected["MdAPE"]),
            "validation_MAPE": float(selected["MAPE"]),
            "validation_p95_APE": float(selected["p95_APE"]),
            "validation_RMSE_log": float(selected["RMSE_log"]),
        }
        if row["selected_candidate"] in test.index:
            test_row = test.loc[row["selected_candidate"]]
            if isinstance(test_row, pd.DataFrame):
                test_row = test_row.iloc[0]
            row.update({
                "test_MdAPE": float(test_row["MdAPE"]),
                "test_MAPE": float(test_row["MAPE"]),
                "test_p95_APE": float(test_row["p95_APE"]),
                "test_RMSE_log": float(test_row["RMSE_log"]),
            })
        rows.append(row)
    return pd.DataFrame(rows).drop_duplicates("selected_candidate")


def metric_from_arrays(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
    }


def bootstrap_candidates(predictions: pd.DataFrame, selected: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    test = predictions[predictions["split"].eq("test")].copy()
    top_test = (
        test.groupby("candidate", as_index=False)
        .agg(MdAPE=("ape", "median"), MAPE=("ape", "mean"), p95_APE=("ape", lambda x: float(np.quantile(x, 0.95))))
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(10)["candidate"]
        .tolist()
    )
    candidates = [CURRENT_CANDIDATE] + selected["selected_candidate"].dropna().tolist() + top_test
    candidates = list(dict.fromkeys(candidates))
    wide = test[test["candidate"].isin(candidates)].pivot_table(
        index=["_track6_row_id", "artist_key"],
        columns="candidate",
        values="pred_log",
        aggfunc="last",
    ).reset_index()
    actual = test[["_track6_row_id", "artist_key", "actual_log", "actual_price"]].drop_duplicates("_track6_row_id")
    wide = wide.merge(actual, on=["_track6_row_id", "artist_key"], how="inner").reset_index(drop=True)
    candidates = [candidate for candidate in candidates if candidate in wide.columns and wide[candidate].notna().all()]

    rng = np.random.default_rng(SEED)
    artists = wide["artist_key"].astype(str).unique()
    artist_to_indices = {artist: wide.index[wide["artist_key"].astype(str).eq(artist)].to_numpy() for artist in artists}
    samples: list[dict[str, Any]] = []

    def add_sample(indices: np.ndarray, sample_type: str, iteration: int) -> None:
        actual_price = wide.loc[indices, "actual_price"].to_numpy(dtype=float)
        actual_log = wide.loc[indices, "actual_log"].to_numpy(dtype=float)
        current_metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, CURRENT_CANDIDATE].to_numpy(dtype=float))
        for candidate in candidates:
            metric = metric_from_arrays(actual_price, actual_log, wide.loc[indices, candidate].to_numpy(dtype=float))
            row = {"sample_type": sample_type, "iteration": iteration, "candidate": candidate}
            for name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
                row[name] = metric[name]
                row[f"delta_{name}"] = metric[name] - current_metric[name]
            samples.append(row)

    n = len(wide)
    for iteration in range(BOOTSTRAP_ITERATIONS):
        add_sample(rng.integers(0, n, size=n), "row_bootstrap", iteration)
        sampled_artists = rng.choice(artists, size=len(artists), replace=True)
        add_sample(np.concatenate([artist_to_indices[artist] for artist in sampled_artists]), "artist_bootstrap", iteration)

    samples_df = pd.DataFrame(samples)
    summary_rows: list[dict[str, Any]] = []
    for (sample_type, candidate), group in samples_df.groupby(["sample_type", "candidate"], observed=False):
        row = {
            "experiment_id": EXP_ID,
            "sample_type": sample_type,
            "candidate": candidate,
            "iterations": int(group["iteration"].nunique()),
        }
        for name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            delta = group[f"delta_{name}"]
            row[f"mean_delta_{name}"] = float(delta.mean())
            row[f"p10_delta_{name}"] = float(delta.quantile(0.10))
            row[f"p90_delta_{name}"] = float(delta.quantile(0.90))
            row[f"improvement_probability_{name}"] = float(np.mean(delta < 0))
        summary_rows.append(row)
    return pd.DataFrame(summary_rows), samples_df


def segment_diagnostics(predictions: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    test = predictions[predictions["split"].eq("test") & predictions["candidate"].isin(candidates)].copy()
    rows: list[dict[str, Any]] = []
    for segment_col in ["svc_reliability_bin", "pred_log_bin", "size_bin", "artist_works_bin"]:
        for (candidate, segment_value), group in test.groupby(["candidate", segment_col], observed=False):
            if len(group) < 10:
                continue
            rows.append({
                "experiment_id": EXP_ID,
                "candidate": candidate,
                "segment_col": segment_col,
                "segment_value": segment_value,
                "n": int(len(group)),
                "MdAPE": float(group["ape"].median()),
                "MAPE": float(group["ape"].mean()),
                "p95_APE": float(group["ape"].quantile(0.95)),
                "mean_residual_log": float(group["residual_log"].mean()),
            })
    return pd.DataFrame(rows)


def render_report(
    metrics: pd.DataFrame,
    selected: pd.DataFrame,
    bootstrap: pd.DataFrame,
    segments: pd.DataFrame,
) -> tuple[str, str]:
    test = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    validation = metrics[metrics["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).copy()
    current_test = test[test["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    current_val = validation[validation["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    top_test = test.head(30).copy()
    top_val = validation.head(30).copy()
    boot_view = bootstrap.sort_values(["sample_type", "mean_delta_MdAPE", "mean_delta_MAPE"]).head(40).copy()
    seg_view = segments.sort_values(["segment_col", "segment_value", "MdAPE"]).head(120).copy()
    non_ref_test = test[~test["candidate"].eq(CURRENT_CANDIDATE)].copy()
    all_improve = non_ref_test[
        (non_ref_test["MdAPE"] < float(current_test["MdAPE"]))
        & (non_ref_test["MAPE"] < float(current_test["MAPE"]))
        & (non_ref_test["p95_APE"] < float(current_test["p95_APE"]))
    ].sort_values(["MdAPE", "MAPE", "p95_APE"])
    balanced = all_improve.iloc[0] if not all_improve.empty else None
    tail_pool = non_ref_test[non_ref_test["MdAPE"] <= float(current_test["MdAPE"])].copy()
    tail_guard = tail_pool.sort_values(["p95_APE", "MAPE", "MdAPE"]).iloc[0] if not tail_pool.empty else None

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 현재 Warm 1순위 후보 위에 적용할 Huber residual 보정 방법을 세분화해 검증",
        f"- 기준 후보: `{CURRENT_CANDIDATE}`",
        f"- 기준 validation MdAPE/MAPE/p95: `{current_val['MdAPE']:.4f}` / `{current_val['MAPE']:.4f}` / `{current_val['p95_APE']:.4f}`",
        f"- 기준 test MdAPE/MAPE/p95: `{current_test['MdAPE']:.4f}` / `{current_test['MAPE']:.4f}` / `{current_test['p95_APE']:.4f}`",
        "",
        "## 0. 실험 계획",
        "",
        "- 기준 예측값은 현재 Warm 1순위 `blend_svcnum_ppv8_wsvc_0.70`로 고정",
        "- validation 내부 교차검증으로 residual Huber 보정값을 만들고 validation 성능을 확인",
        "- test에는 validation 전체로 학습한 residual Huber 보정식을 한 번만 적용",
        "- 보정 방법은 hard clip, soft tanh, 신뢰도별 축소, 방향별 강도, 예측 가격 구간별 cap, 혼합 정책으로 분리",
        "- test 결과는 후보 탐색 결과로만 보고, 운영 반영 전 반복 split 또는 OOF 재검증 필요",
        "",
        "## 1. 실행 결론",
        "",
    ]
    best = top_test.iloc[0]
    lines += [
        f"- test 최상위 후보: `{best['candidate']}`",
        f"- test 최상위 후보 성능: MdAPE `{best['MdAPE']:.4f}`, MAPE `{best['MAPE']:.4f}`, p95_APE `{best['p95_APE']:.4f}`",
        f"- 세 지표를 모두 개선한 후보 수: `{len(all_improve)}`",
    ]
    if balanced is not None:
        lines += [
            f"- 균형 후보: `{balanced['candidate']}`",
            f"- 균형 후보 성능: MdAPE `{balanced['MdAPE']:.4f}`, MAPE `{balanced['MAPE']:.4f}`, p95_APE `{balanced['p95_APE']:.4f}`",
        ]
    if tail_guard is not None:
        lines += [
            f"- 큰 오차 방어 후보: `{tail_guard['candidate']}`",
            f"- 큰 오차 방어 후보 성능: MdAPE `{tail_guard['MdAPE']:.4f}`, MAPE `{tail_guard['MAPE']:.4f}`, p95_APE `{tail_guard['p95_APE']:.4f}`",
        ]
    lines += [
        "- 현재 split에서는 residual Huber 보정 방식 세분화로 추가 개선 후보가 확인됨",
        "- 다만 validation 선택 후보와 test 최상위 후보가 다를 수 있으므로, v0.1 반영 전 안정성 재검증 필요",
        "",
        "## 2. Validation 기준 선택 후보",
        "",
        "| 선택 기준 | 후보 | 방식 | val MdAPE | val MAPE | val p95 | test MdAPE | test MAPE | test p95 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected.itertuples(index=False):
        lines.append(
            f"| {row.selection_objective} | `{row.selected_candidate}` | {row.method} | "
            f"{row.validation_MdAPE:.4f} | {row.validation_MAPE:.4f} | {row.validation_p95_APE:.4f} | "
            f"{row.test_MdAPE:.4f} | {row.test_MAPE:.4f} | {row.test_p95_APE:.4f} |"
        )
    lines += [
        "",
        "## 3. Test 상위 후보",
        "",
        "| 순위 | 후보 | 방식 | feature set | epsilon | alpha | cap | strength | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_test.itertuples(index=False), 1):
        lines.append(
            f"| {rank} | `{row.candidate}` | {row.method} | {row.feature_set} | "
            f"{row.epsilon:.2f} | {row.alpha:.3f} | {row.correction_cap:.2f} | "
            f"{row.correction_strength if pd.notna(row.correction_strength) else ''} | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )
    lines += [
        "",
        "## 4. Bootstrap 안정성 요약",
        "",
        "| 표본 추출 방식 | 후보 | MdAPE 평균 차이 | MdAPE 개선 확률 | MAPE 개선 확률 | p95 개선 확률 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in boot_view.itertuples(index=False):
        lines.append(
            f"| {row.sample_type} | `{row.candidate}` | {row.mean_delta_MdAPE:.5f} | "
            f"{row.improvement_probability_MdAPE:.3f} | {row.improvement_probability_MAPE:.3f} | "
            f"{row.improvement_probability_p95_APE:.3f} |"
        )
    lines += [
        "",
        "## 5. 구간별 진단",
        "",
        "- 구간별 진단은 `outputs/segment_diagnostics.csv`에 전체 저장",
        "- 리포트에는 상위 일부만 표시",
        "",
    ]
    md = "\n".join(lines) + "\n"

    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}} th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}} .note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">현재 Warm 1순위 예측값 위에 residual Huber 보정값을 어떻게 적용할지 비교한 리포트.</div>
<h2>실행 결론</h2>
<ul>
<li>기준 후보: <code>{html.escape(CURRENT_CANDIDATE)}</code></li>
<li>기준 test MdAPE/MAPE/p95: {current_test['MdAPE']:.4f} / {current_test['MAPE']:.4f} / {current_test['p95_APE']:.4f}</li>
<li>test 최상위 후보: <code>{html.escape(str(best['candidate']))}</code></li>
<li>test 최상위 후보 성능: MdAPE {best['MdAPE']:.4f} / MAPE {best['MAPE']:.4f} / p95_APE {best['p95_APE']:.4f}</li>
<li>세 지표를 모두 개선한 후보 수: {len(all_improve)}</li>
{f"<li>균형 후보: <code>{html.escape(str(balanced['candidate']))}</code>, MdAPE {balanced['MdAPE']:.4f} / MAPE {balanced['MAPE']:.4f} / p95_APE {balanced['p95_APE']:.4f}</li>" if balanced is not None else ""}
{f"<li>큰 오차 방어 후보: <code>{html.escape(str(tail_guard['candidate']))}</code>, MdAPE {tail_guard['MdAPE']:.4f} / MAPE {tail_guard['MAPE']:.4f} / p95_APE {tail_guard['p95_APE']:.4f}</li>" if tail_guard is not None else ""}
<li>운영 반영 전 반복 split 또는 OOF 재검증 필요.</li>
</ul>
<h2>Validation 기준 선택 후보</h2>{selected.to_html(index=False, escape=True)}
<h2>Test 상위 후보</h2>{top_test.to_html(index=False, escape=True)}
<h2>Validation 상위 후보</h2>{top_val.to_html(index=False, escape=True)}
<h2>Bootstrap 안정성 요약</h2>{boot_view.to_html(index=False, escape=True)}
<h2>구간별 진단 일부</h2>{seg_view.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    selected: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    bootstrap_samples: pd.DataFrame,
    segments: pd.DataFrame,
) -> None:
    metrics.to_csv(EXP_DIR / "outputs" / "all_candidate_metrics.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    selected.to_csv(EXP_DIR / "outputs" / "selected_validation_candidates.csv", index=False)
    bootstrap_summary.to_csv(EXP_DIR / "outputs" / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(EXP_DIR / "outputs" / "bootstrap_samples.csv", index=False)
    segments.to_csv(EXP_DIR / "outputs" / "segment_diagnostics.csv", index=False)
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "current_candidate": CURRENT_CANDIDATE,
        "epsilons": EPSILONS,
        "alphas": ALPHAS,
        "global_caps": GLOBAL_CAPS,
        "global_strengths": GLOBAL_STRENGTHS,
        "reliability_policies": RELIABILITY_POLICIES,
        "pred_bin_cap_policies": PRED_BIN_CAP_POLICIES,
        "directional_policies": DIRECTIONAL_POLICIES,
        "leakage_control": {
            "validation": "internal cross-fitted residual Huber correction",
            "test": "residual model fitted on full validation and applied once to test",
            "base_prediction": "fixed current Warm candidate prediction",
        },
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics, selected, bootstrap_summary, segments)
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.md").write_text(md, encoding="utf-8")
    (DOC_ROOT / f"{EXP_SLUG}.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    val, test = load_reference_frames()
    metrics, predictions = run_candidates(val, test)
    selected = select_validation_candidates(metrics)
    bootstrap_summary, bootstrap_samples = bootstrap_candidates(predictions, selected)
    top_candidates = (
        metrics[metrics["split"].eq("test")]
        .sort_values(["MdAPE", "MAPE", "p95_APE"])
        .head(10)["candidate"]
        .tolist()
    )
    segment_candidates = list(dict.fromkeys([CURRENT_CANDIDATE] + selected["selected_candidate"].dropna().tolist() + top_candidates))
    segments = segment_diagnostics(predictions, segment_candidates)
    write_outputs(metrics, predictions, selected, bootstrap_summary, bootstrap_samples, segments)

    test_metrics = metrics[metrics["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    current = test_metrics[test_metrics["candidate"].eq(CURRENT_CANDIDATE)].iloc[0]
    best = test_metrics.iloc[0]
    print(f"[{EXP_ID}] completed")
    print(f"current test MdAPE/MAPE/p95: {current['MdAPE']:.4f} / {current['MAPE']:.4f} / {current['p95_APE']:.4f}")
    print(f"best test candidate: {best['candidate']}")
    print(f"best test MdAPE/MAPE/p95: {best['MdAPE']:.4f} / {best['MAPE']:.4f} / {best['p95_APE']:.4f}")
    print(f"report: {EXP_DIR / 'reports' / 'result_report.html'}")


if __name__ == "__main__":
    main()
