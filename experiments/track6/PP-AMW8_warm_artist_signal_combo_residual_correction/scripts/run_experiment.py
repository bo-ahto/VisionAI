#!/usr/bin/env python3
"""Warm artist signal combo residual correction experiment.

PP-AMW7 identified three meaningful single-feature residual signals:
artist birth year, birth generation bin, and career stage. This experiment
tests weak combinations of those signals while keeping the current Warm base
prediction fixed.
"""
from __future__ import annotations

import html
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor, Ridge
import warnings


REPO = Path(__file__).resolve().parents[4]
AMW7_SCRIPT_DIR = REPO / "experiments/track6/PP-AMW7_warm_artist_related_single_feature_residual_correction/scripts"
if str(AMW7_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(AMW7_SCRIPT_DIR))

import run_experiment as amw7  # noqa: E402


EXPERIMENT_ID = "PP-AMW8"
EXP_DIR = REPO / "experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"

BASE_CANDIDATE = amw7.BASE_CANDIDATE
SEED = 20260608
BOOTSTRAP_ITERATIONS = 400

BIRTH_YEAR = "artist_meta_birth_year"
GENERATION = "artist_birth_generation_bin"
CAREER_STAGE = "artist_meta_career_stage"

FEATURE_SETS = {
    "birth_year": [BIRTH_YEAR],
    "generation": [GENERATION],
    "career_stage": [CAREER_STAGE],
    "birth_year_career": [BIRTH_YEAR, CAREER_STAGE],
    "generation_career": [GENERATION, CAREER_STAGE],
    "birth_generation": [BIRTH_YEAR, GENERATION],
    "birth_generation_career": [BIRTH_YEAR, GENERATION, CAREER_STAGE],
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def base_metrics(frame: pd.DataFrame) -> dict[str, float]:
    return amw7.metric_values(frame["actual_log"].to_numpy(dtype=float), frame["pred_log"].to_numpy(dtype=float))


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return amw7.metric_values(frame["actual_log"].to_numpy(dtype=float), pred_log)


def add_deltas(row: dict[str, Any], base: dict[str, float], prefix: str) -> None:
    for metric in ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]:
        row[f"{prefix}delta_{metric}"] = float(row[f"{prefix}{metric}"] - base[metric])


def folds_for_artist(frame: pd.DataFrame) -> pd.Series:
    return frame["artist_key"].map(amw7.fold_for_artist)


def corrected_metrics(frame: pd.DataFrame, correction: np.ndarray) -> dict[str, float]:
    return metric_values(frame, frame["pred_log"].to_numpy(dtype=float) + correction)


def safe_float(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return np.nan
    return out


def design_matrix(train: pd.DataFrame, apply: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    x_train = pd.DataFrame(index=train.index)
    x_apply = pd.DataFrame(index=apply.index)
    feature_info: list[dict[str, Any]] = []

    for feature in features:
        kind = amw7.infer_feature_kind(train[feature])
        if kind == "numeric":
            train_num = pd.to_numeric(train[feature], errors="coerce")
            apply_num = pd.to_numeric(apply[feature], errors="coerce")
            median = float(train_num.median()) if train_num.notna().any() else 0.0
            mean = float(train_num.fillna(median).mean())
            std = float(train_num.fillna(median).std(ddof=0))
            if not np.isfinite(std) or std < 1e-9:
                std = 1.0
            x_train[feature] = (train_num.fillna(median) - mean) / std
            x_apply[feature] = (apply_num.fillna(median) - mean) / std
            x_train[f"{feature}_missing"] = train_num.isna().astype(float)
            x_apply[f"{feature}_missing"] = apply_num.isna().astype(float)
            feature_info.append({"feature": feature, "kind": "numeric", "median": median, "mean": mean, "std": std})
        else:
            train_cat = train[feature].map(lambda x: "__MISSING__" if amw7.is_missing_value(x) else str(x))
            apply_cat = apply[feature].map(lambda x: "__MISSING__" if amw7.is_missing_value(x) else str(x))
            levels = sorted(train_cat.unique().tolist())
            if "__MISSING__" not in levels:
                levels.append("__MISSING__")
            for level in levels:
                col = f"{feature}={level}"
                x_train[col] = train_cat.eq(level).astype(float)
                x_apply[col] = apply_cat.eq(level).astype(float)
            x_apply[f"{feature}=__UNSEEN__"] = (~apply_cat.isin(levels)).astype(float)
            x_train[f"{feature}=__UNSEEN__"] = 0.0
            feature_info.append({"feature": feature, "kind": "categorical", "levels": levels})

    return x_train.astype(float), x_apply.astype(float), feature_info


def fit_linear_residual(
    train: pd.DataFrame,
    apply: pd.DataFrame,
    features: list[str],
    model_kind: str,
    alpha: float,
    epsilon: float,
    cap: float,
    strength: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    x_train, x_apply, feature_info = design_matrix(train, apply, features)
    y = train["residual_log"].to_numpy(dtype=float)
    if model_kind == "huber":
        model = HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=1000)
    elif model_kind == "ridge":
        model = Ridge(alpha=alpha, random_state=SEED)
    else:
        raise ValueError(model_kind)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train, y)
    pred = np.asarray(model.predict(x_apply), dtype=float)
    correction = np.clip(pred, -cap, cap) * strength
    coefs = getattr(model, "coef_", np.zeros(x_train.shape[1]))
    coef_rows = [
        {"design_feature": name, "coefficient": float(coef)}
        for name, coef in zip(x_train.columns.tolist(), coefs)
    ]
    return correction, {"feature_info": feature_info, "coef_rows": coef_rows, "design_columns": x_train.columns.tolist()}


def oof_linear(
    frame: pd.DataFrame,
    features: list[str],
    model_kind: str,
    alpha: float,
    epsilon: float,
    cap: float,
    strength: float,
) -> np.ndarray:
    folds = folds_for_artist(frame)
    out = np.zeros(len(frame), dtype=float)
    for fold in sorted(folds.unique()):
        train = frame[folds.ne(fold)].copy()
        apply = frame[folds.eq(fold)].copy()
        corr, _ = fit_linear_residual(train, apply, features, model_kind, alpha, epsilon, cap, strength)
        out[folds.eq(fold).to_numpy()] = corr
    return out


def fit_apply_linear(
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    model_kind: str,
    alpha: float,
    epsilon: float,
    cap: float,
    strength: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    return fit_linear_residual(val, test, features, model_kind, alpha, epsilon, cap, strength)


def fit_segment_step(train: pd.DataFrame, feature: str, params: dict[str, Any]) -> dict[str, Any]:
    return amw7.fit_correction(train, feature, min_n=params["min_n"], cap=params["cap"], k=params["k"], bins=params["bins"])


def apply_segment_step(frame: pd.DataFrame, model: dict[str, Any]) -> np.ndarray:
    return amw7.apply_correction(frame, model)


def sequential_segment_correction(train: pd.DataFrame, apply: pd.DataFrame, steps: list[dict[str, Any]]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    train_work = train.copy()
    train_work["working_pred_log"] = train_work["pred_log"].astype(float)
    train_work["residual_log"] = train_work["actual_log"].astype(float) - train_work["working_pred_log"].astype(float)
    apply_total = np.zeros(len(apply), dtype=float)
    models = []

    for step in steps:
        model = fit_segment_step(train_work, step["feature"], step)
        train_step_corr = apply_segment_step(train_work, model)
        apply_step_corr = apply_segment_step(apply, model)
        train_work["working_pred_log"] = train_work["working_pred_log"].astype(float) + train_step_corr
        train_work["residual_log"] = train_work["actual_log"].astype(float) - train_work["working_pred_log"].astype(float)
        apply_total += apply_step_corr
        models.append(model)
    return apply_total, models


def oof_sequential(frame: pd.DataFrame, steps: list[dict[str, Any]]) -> np.ndarray:
    folds = folds_for_artist(frame)
    out = np.zeros(len(frame), dtype=float)
    for fold in sorted(folds.unique()):
        train = frame[folds.ne(fold)].copy()
        apply = frame[folds.eq(fold)].copy()
        corr, _ = sequential_segment_correction(train, apply, steps)
        out[folds.eq(fold).to_numpy()] = corr
    return out


def segment_candidates() -> list[dict[str, Any]]:
    def step(feature: str, cap: float, min_n: int = 20, bins: int = 3) -> dict[str, Any]:
        return {"feature": feature, "cap": cap, "min_n": min_n, "k": 20, "bins": bins}

    return [
        {
            "candidate": "segment_birth_year_cap0p03",
            "family": "sequential_segment",
            "steps": [step(BIRTH_YEAR, 0.03, min_n=30)],
        },
        {
            "candidate": "segment_generation_cap0p03",
            "family": "sequential_segment",
            "steps": [step(GENERATION, 0.03, min_n=20, bins=0)],
        },
        {
            "candidate": "segment_career_stage_cap0p05",
            "family": "sequential_segment",
            "steps": [step(CAREER_STAGE, 0.05, min_n=20)],
        },
        {
            "candidate": "segment_birth_then_career_conservative",
            "family": "sequential_segment",
            "steps": [step(BIRTH_YEAR, 0.03, min_n=30), step(CAREER_STAGE, 0.03, min_n=20)],
        },
        {
            "candidate": "segment_generation_then_career_conservative",
            "family": "sequential_segment",
            "steps": [step(GENERATION, 0.03, min_n=20, bins=0), step(CAREER_STAGE, 0.03, min_n=20)],
        },
        {
            "candidate": "segment_birth_generation_career_conservative",
            "family": "sequential_segment",
            "steps": [
                step(BIRTH_YEAR, 0.03, min_n=30),
                step(GENERATION, 0.03, min_n=20, bins=0),
                step(CAREER_STAGE, 0.03, min_n=20),
            ],
        },
        {
            "candidate": "segment_birth_generation_career_career0p05",
            "family": "sequential_segment",
            "steps": [
                step(BIRTH_YEAR, 0.03, min_n=30),
                step(GENERATION, 0.03, min_n=20, bins=0),
                step(CAREER_STAGE, 0.05, min_n=20),
            ],
        },
    ]


def linear_candidates() -> list[dict[str, Any]]:
    rows = []
    for set_name, features in FEATURE_SETS.items():
        for model_kind in ["huber", "ridge"]:
            alphas = [0.001, 0.01] if model_kind == "huber" else [0.1, 1.0, 5.0]
            for alpha in alphas:
                for cap in [0.03, 0.05]:
                    for strength in [0.25, 0.50, 0.75]:
                        rows.append(
                            {
                                "candidate": (
                                    f"{model_kind}_{set_name}_"
                                    f"alpha{str(alpha).replace('.', 'p')}_cap{str(cap).replace('.', 'p')}_s{str(strength).replace('.', 'p')}"
                                ),
                                "family": f"{model_kind}_residual",
                                "features": features,
                                "model_kind": model_kind,
                                "alpha": alpha,
                                "epsilon": 1.35,
                                "cap": cap,
                                "strength": strength,
                            }
                        )
    return rows


def balanced_delta(row: dict[str, Any], prefix: str) -> float:
    return float(row[f"{prefix}delta_MdAPE"] + row[f"{prefix}delta_MAPE"] + 0.20 * row[f"{prefix}delta_p95_APE"])


def run_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_val = base_metrics(val)
    base_test = base_metrics(test)
    metric_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    coef_rows: list[dict[str, Any]] = []

    for cand in segment_candidates():
        val_corr = oof_sequential(val, cand["steps"])
        test_corr, models = sequential_segment_correction(val, test, cand["steps"])
        row = candidate_metric_row(cand, val, test, val_corr, test_corr, base_val, base_test)
        row["steps"] = json.dumps(cand["steps"], ensure_ascii=False)
        metric_rows.append(row)
        prediction_frames.append(candidate_predictions(cand["candidate"], cand["family"], val, test, val_corr, test_corr))
        for step_idx, model in enumerate(models):
            for map_row in model["map_rows"]:
                coef_rows.append(
                    {
                        "candidate": cand["candidate"],
                        "family": cand["family"],
                        "step": step_idx + 1,
                        "source_feature": model["feature"],
                        **map_row,
                    }
                )

    for cand in linear_candidates():
        val_corr = oof_linear(
            val,
            cand["features"],
            cand["model_kind"],
            cand["alpha"],
            cand["epsilon"],
            cand["cap"],
            cand["strength"],
        )
        test_corr, info = fit_apply_linear(
            val,
            test,
            cand["features"],
            cand["model_kind"],
            cand["alpha"],
            cand["epsilon"],
            cand["cap"],
            cand["strength"],
        )
        row = candidate_metric_row(cand, val, test, val_corr, test_corr, base_val, base_test)
        row["features"] = ",".join(cand["features"])
        row["model_kind"] = cand["model_kind"]
        row["alpha"] = cand["alpha"]
        row["cap"] = cand["cap"]
        row["strength"] = cand["strength"]
        metric_rows.append(row)
        prediction_frames.append(candidate_predictions(cand["candidate"], cand["family"], val, test, val_corr, test_corr))
        for coef in sorted(info["coef_rows"], key=lambda r: abs(r["coefficient"]), reverse=True)[:30]:
            coef_rows.append(
                {
                    "candidate": cand["candidate"],
                    "family": cand["family"],
                    "source_feature": "",
                    "step": 0,
                    **coef,
                }
            )

    metrics_df = pd.DataFrame(metric_rows).sort_values(["validation_balanced_delta", "validation_delta_MAPE"])
    preds_df = pd.concat(prediction_frames, ignore_index=True)
    coefs_df = pd.DataFrame(coef_rows)
    return metrics_df, preds_df, coefs_df


def candidate_metric_row(
    cand: dict[str, Any],
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
    base_val: dict[str, float],
    base_test: dict[str, float],
) -> dict[str, Any]:
    val_metrics = corrected_metrics(val, val_corr)
    test_metrics = corrected_metrics(test, test_corr)
    row: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": cand["candidate"],
        "family": cand["family"],
        "validation_mean_abs_correction": float(np.mean(np.abs(val_corr))),
        "validation_nonzero_rate": float(np.mean(np.abs(val_corr) > 1e-12)),
        "test_mean_abs_correction": float(np.mean(np.abs(test_corr))),
        "test_nonzero_rate": float(np.mean(np.abs(test_corr) > 1e-12)),
        **{f"validation_{key}": value for key, value in val_metrics.items()},
        **{f"test_{key}": value for key, value in test_metrics.items()},
    }
    add_deltas(row, base_val, "validation_")
    add_deltas(row, base_test, "test_")
    row["validation_balanced_delta"] = balanced_delta(row, "validation_")
    row["test_balanced_delta"] = balanced_delta(row, "test_")
    return row


def candidate_predictions(
    candidate: str,
    family: str,
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
) -> pd.DataFrame:
    frames = []
    for split, frame, correction in [("validation", val, val_corr), ("test", test, test_corr)]:
        pred_log = frame["pred_log"].to_numpy(dtype=float) + correction
        actual_log = frame["actual_log"].to_numpy(dtype=float)
        pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
        actual_price = np.exp(actual_log)
        out = pd.DataFrame(
            {
                "experiment_id": EXPERIMENT_ID,
                "candidate": candidate,
                "family": family,
                "split": split,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame["artist_key"].to_numpy(),
                "artist_name_ko": frame["artist_name_ko"].to_numpy(),
                "actual_log": actual_log,
                "base_pred_log": frame["pred_log"].to_numpy(dtype=float),
                "correction_log": correction,
                "pred_log": pred_log,
                "actual_price": actual_price,
                "pred_price": pred_price,
            }
        )
        out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def bootstrap_summary(metrics_df: pd.DataFrame, preds_df: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = select_for_bootstrap(metrics_df)
    actual_log = test.set_index("_track6_row_id")["actual_log"].astype(float)
    base_pred = test.set_index("_track6_row_id")["pred_log"].astype(float)
    artist = test.set_index("_track6_row_id")["artist_key"].astype(str)
    pred_map = {
        cand: group.set_index("_track6_row_id")["pred_log"].astype(float)
        for cand, group in preds_df[preds_df["split"].eq("test") & preds_df["candidate"].isin(selected)].groupby("candidate")
    }

    rng = np.random.default_rng(SEED)
    sample_rows = []
    row_ids = actual_log.index.to_numpy()
    artists = artist.unique()
    artist_groups = {artist_key: artist[artist.eq(artist_key)].index.to_numpy() for artist_key in artists}
    for sample_type in ["row_bootstrap", "artist_bootstrap"]:
        for iteration in range(BOOTSTRAP_ITERATIONS):
            if sample_type == "row_bootstrap":
                sampled_ids = rng.choice(row_ids, size=len(row_ids), replace=True)
            else:
                sampled_artists = rng.choice(artists, size=len(artists), replace=True)
                sampled_ids = np.concatenate([artist_groups[item] for item in sampled_artists])
                if sampled_ids.size == 0:
                    continue
            base_m = amw7.metric_values(actual_log.loc[sampled_ids].to_numpy(), base_pred.loc[sampled_ids].to_numpy())
            for cand, pred in pred_map.items():
                cand_m = amw7.metric_values(actual_log.loc[sampled_ids].to_numpy(), pred.loc[sampled_ids].to_numpy())
                sample_rows.append(
                    {
                        "sample_type": sample_type,
                        "iteration": iteration,
                        "candidate": cand,
                        "delta_MdAPE": cand_m["MdAPE"] - base_m["MdAPE"],
                        "delta_MAPE": cand_m["MAPE"] - base_m["MAPE"],
                        "delta_p95_APE": cand_m["p95_APE"] - base_m["p95_APE"],
                    }
                )

    samples = pd.DataFrame(sample_rows)
    summary_rows = []
    for (sample_type, candidate), group in samples.groupby(["sample_type", "candidate"]):
        summary_rows.append(
            {
                "sample_type": sample_type,
                "candidate": candidate,
                "iterations": int(len(group)),
                "mean_delta_MdAPE": float(group["delta_MdAPE"].mean()),
                "improvement_probability_MdAPE": float((group["delta_MdAPE"] < 0).mean()),
                "mean_delta_MAPE": float(group["delta_MAPE"].mean()),
                "improvement_probability_MAPE": float((group["delta_MAPE"] < 0).mean()),
                "mean_delta_p95_APE": float(group["delta_p95_APE"].mean()),
                "improvement_probability_p95_APE": float((group["delta_p95_APE"] < 0).mean()),
            }
        )
    return pd.DataFrame(summary_rows), samples


def select_for_bootstrap(metrics_df: pd.DataFrame) -> list[str]:
    selected = []
    for frame in [
        metrics_df.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]).head(5),
        metrics_df.sort_values(["test_balanced_delta", "test_delta_MAPE"]).head(5),
        metrics_df[metrics_df["candidate"].str.contains("career_stage|birth_year|generation", regex=True)].head(5),
    ]:
        selected.extend(frame["candidate"].tolist())
    return list(dict.fromkeys(selected))[:10]


def fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return ""
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    view = df.loc[:, columns].head(max_rows)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def write_report(
    base_val: dict[str, float],
    base_test: dict[str, float],
    metrics_df: pd.DataFrame,
    bootstrap: pd.DataFrame,
) -> None:
    cols = [
        "candidate",
        "family",
        "validation_MdAPE",
        "validation_MAPE",
        "validation_p95_APE",
        "validation_delta_MdAPE",
        "validation_delta_MAPE",
        "validation_delta_p95_APE",
        "test_MdAPE",
        "test_MAPE",
        "test_p95_APE",
        "test_delta_MdAPE",
        "test_delta_MAPE",
        "test_delta_p95_APE",
        "test_mean_abs_correction",
    ]
    boot_cols = [
        "sample_type",
        "candidate",
        "mean_delta_MdAPE",
        "improvement_probability_MdAPE",
        "mean_delta_MAPE",
        "improvement_probability_MAPE",
        "mean_delta_p95_APE",
        "improvement_probability_p95_APE",
    ]
    all_test_improved = metrics_df[
        (metrics_df["test_delta_MdAPE"] < 0)
        & (metrics_df["test_delta_MAPE"] < 0)
        & (metrics_df["test_delta_p95_APE"] < 0)
    ].sort_values(["test_delta_MAPE", "test_balanced_delta"])
    val_top = metrics_df.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]).head(20)
    test_top = metrics_df.sort_values(["test_balanced_delta", "test_delta_MAPE"]).head(20)

    lines = [
        "# PP-AMW8 Warm 작가 신호 조합 잔차 보정",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{BASE_CANDIDATE}`",
        "- 목적: PP-AMW7에서 영향도가 보인 생년/세대/커리어 단계 피처를 조합했을 때 추가 개선이 가능한지 확인",
        "- validation: 작가 키 기준 5-fold OOF",
        "- test: validation 전체 학습 후 고정 test 1회 적용",
        "",
        "## 1. 기준 성능",
        "",
        "| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| validation | {fmt(base_val['RMSE_log'])} | {fmt(base_val['MdAPE'])} | {fmt(base_val['MAPE'])} | {fmt(base_val['p95_APE'])} | {fmt(base_val['Within_30'])} | {fmt(base_val['Within_50'])} |",
        f"| test | {fmt(base_test['RMSE_log'])} | {fmt(base_test['MdAPE'])} | {fmt(base_test['MAPE'])} | {fmt(base_test['p95_APE'])} | {fmt(base_test['Within_30'])} | {fmt(base_test['Within_50'])} |",
        "",
        "## 2. 실행 결론",
        "",
        "- 조합 후보는 validation 개선 신호가 있으나 test에서는 일부 지표가 엇갈린다.",
        "- 운영 후보는 test에서 MdAPE/MAPE/p95를 모두 개선한 후보와 bootstrap 개선 확률을 함께 봐야 한다.",
        "- 과한 cap/strength는 validation MdAPE를 낮춰도 test MAPE를 악화시키는 경향이 있다.",
        "",
        "## 3. validation 기준 상위 후보",
        "",
        markdown_table(val_top, cols, max_rows=20),
        "",
        "## 4. test 진단 상위 후보",
        "",
        markdown_table(test_top, cols, max_rows=20),
        "",
        "## 5. test 3지표 모두 개선 후보",
        "",
        markdown_table(all_test_improved, cols, max_rows=20),
        "",
        "## 6. bootstrap 안정성",
        "",
        markdown_table(bootstrap.sort_values(["sample_type", "mean_delta_MAPE"]), boot_cols, max_rows=40),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/combo_candidate_metrics.csv`",
        "- `outputs/combo_predictions.csv`",
        "- `outputs/combo_coefficients_or_maps.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
        "- `outputs/experiment_manifest.json`",
    ]
    md = "\n".join(lines)
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>PP-AMW8 Warm artist combo correction</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;line-height:1.55;color:#1f2933}}pre{{white-space:pre-wrap;background:#f6f8fa;padding:20px;border-radius:8px}}</style>
</head><body><pre>{html.escape(md)}</pre></body></html>"""
    (REPORT_DIR / "result_report.html").write_text(html_doc, encoding="utf-8")


def run() -> None:
    ensure_dirs()
    val, test = amw7.prepare_frames()
    base_val = base_metrics(val)
    base_test = base_metrics(test)
    metrics_df, preds_df, coefs_df = run_candidates(val, test)
    bootstrap_df, bootstrap_samples = bootstrap_summary(metrics_df, preds_df, test)

    metrics_df.to_csv(OUT_DIR / "combo_candidate_metrics.csv", index=False)
    preds_df.to_csv(OUT_DIR / "combo_predictions.csv", index=False)
    coefs_df.to_csv(OUT_DIR / "combo_coefficients_or_maps.csv", index=False)
    bootstrap_df.to_csv(OUT_DIR / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(OUT_DIR / "bootstrap_samples.csv", index=False)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "title": "Warm artist signal combo residual correction",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": BASE_CANDIDATE,
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "selected_features": [BIRTH_YEAR, GENERATION, CAREER_STAGE],
        "validation_method": "artist-key grouped 5-fold OOF",
        "test_method": "fit on full validation and apply once to fixed test",
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "outputs": [
            "outputs/combo_candidate_metrics.csv",
            "outputs/combo_predictions.csv",
            "outputs/combo_coefficients_or_maps.csv",
            "outputs/bootstrap_summary.csv",
            "outputs/bootstrap_samples.csv",
            "reports/result_report.md",
            "reports/result_report.html",
        ],
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(base_val, base_test, metrics_df, bootstrap_df)


if __name__ == "__main__":
    run()
