#!/usr/bin/env python3
"""Run Warm artist+artwork feature-policy Huber residual correction.

This experiment consumes PP-FPOL1's feature/correction grid and evaluates each
candidate on the fixed Warm base prediction:

- validation: artist-key grouped 5-fold OOF residual Huber correction
- test: fit on full validation, apply once to fixed test
- bootstrap: row and artist-key resampling on selected candidates
"""
from __future__ import annotations

import html
import importlib.util
import json
import math
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import HuberRegressor, Ridge


REPO = Path(__file__).resolve().parents[4]
AMW8_SCRIPT = REPO / "experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction/scripts/run_experiment.py"
spec = importlib.util.spec_from_file_location("amw8_module", AMW8_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import AMW8 script: {AMW8_SCRIPT}")
amw8 = importlib.util.module_from_spec(spec)
sys.modules["amw8_module"] = amw8
spec.loader.exec_module(amw8)


EXPERIMENT_ID = "PP-FPOL2"
TITLE = "Warm artist+artwork policy Huber residual correction"
EXP_DIR = REPO / "experiments/track6/PP-FPOL2_warm_artist_artwork_policy_huber_residual"
OUT_DIR = EXP_DIR / "outputs"
REPORT_DIR = EXP_DIR / "reports"
LOG_DIR = EXP_DIR / "logs"
GRID_PATH = (
    REPO
    / "experiments/track6/PP-FPOL1_warm_artist_artwork_feature_correction_policy/outputs/candidate_correction_grid.csv"
)
BASE_CANDIDATE = amw8.BASE_CANDIDATE
SEED = 20260608
BOOTSTRAP_ITERATIONS = 400

PRED_BIN_MULTIPLIERS = {
    "low": 0.70,
    "mid_low": 1.00,
    "mid_high": 1.00,
    "high": 0.75,
    "missing": 0.60,
}

warnings.filterwarnings("ignore", category=PerformanceWarning)


def ensure_dirs() -> None:
    for directory in [OUT_DIR, REPORT_DIR, LOG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    val, test = amw8.amw7.prepare_frames()
    for frame in [val, test]:
        frame["base_pred_log"] = frame["pred_log"].astype(float)
    return val, test


def base_metrics(frame: pd.DataFrame) -> dict[str, float]:
    return amw8.base_metrics(frame)


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return amw8.metric_values(frame, pred_log)


def corrected_metrics(frame: pd.DataFrame, correction: np.ndarray) -> dict[str, float]:
    return metric_values(frame, frame["pred_log"].to_numpy(dtype=float) + correction)


def add_deltas(row: dict[str, Any], base: dict[str, float], prefix: str) -> None:
    for metric in ["RMSE_log", "MdAPE", "MAPE", "p95_APE", "Within_30", "Within_50"]:
        row[f"{prefix}delta_{metric}"] = float(row[f"{prefix}{metric}"] - base[metric])


def balanced_delta(row: dict[str, Any], prefix: str) -> float:
    return float(row[f"{prefix}delta_MdAPE"] + row[f"{prefix}delta_MAPE"] + 0.20 * row[f"{prefix}delta_p95_APE"])


def folds_for_artist(frame: pd.DataFrame) -> pd.Series:
    return frame["artist_key"].map(amw8.amw7.fold_for_artist)


def parse_features(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def candidate_name(row: pd.Series) -> str:
    cap = str(row["correction_cap"]).replace(".", "p")
    strength = str(row["correction_strength"]).replace(".", "p")
    eps = str(row["epsilon"]).replace(".", "p")
    return f"huber_{row['feature_set']}_{row['correction_policy']}_{row['guard']}_eps{eps}_cap{cap}_s{strength}"


def fit_raw_residual(
    train: pd.DataFrame,
    apply: pd.DataFrame,
    features: list[str],
    model_kind: str,
    alpha: float,
    epsilon: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    x_train, x_apply, feature_info = amw8.design_matrix(train, apply, features)
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
    raw = np.asarray(model.predict(x_apply), dtype=float)
    coefs = getattr(model, "coef_", np.zeros(x_train.shape[1]))
    coef_rows = [
        {"design_feature": name, "coefficient": float(coef)}
        for name, coef in zip(x_train.columns.tolist(), coefs)
    ]
    return raw, {"feature_info": feature_info, "coef_rows": coef_rows, "design_columns": x_train.columns.tolist()}


def pred_bin_multiplier(train: pd.DataFrame, apply: pd.DataFrame) -> np.ndarray:
    train_pred = pd.to_numeric(train["pred_log"], errors="coerce").dropna()
    if train_pred.empty:
        return np.full(len(apply), PRED_BIN_MULTIPLIERS["missing"], dtype=float)
    q25, q50, q75 = np.quantile(train_pred.to_numpy(dtype=float), [0.25, 0.50, 0.75])
    values = pd.to_numeric(apply["pred_log"], errors="coerce")
    multipliers: list[float] = []
    for value in values:
        if pd.isna(value):
            bucket = "missing"
        elif float(value) <= q25:
            bucket = "low"
        elif float(value) <= q50:
            bucket = "mid_low"
        elif float(value) <= q75:
            bucket = "mid_high"
        else:
            bucket = "high"
        multipliers.append(PRED_BIN_MULTIPLIERS[bucket])
    return np.asarray(multipliers, dtype=float)


def apply_policy(
    raw: np.ndarray,
    train: pd.DataFrame,
    apply: pd.DataFrame,
    correction_policy: str,
    cap: float,
    strength: float,
) -> np.ndarray:
    raw = np.asarray(raw, dtype=float)
    if correction_policy == "hard_clip":
        return np.clip(raw, -cap, cap) * strength
    if correction_policy == "soft_tanh_cap":
        if cap <= 0:
            return np.zeros_like(raw)
        return np.tanh(raw / cap) * cap * strength
    if correction_policy == "pred_bin_tail_guard":
        mult = pred_bin_multiplier(train, apply)
        local_cap = cap * mult
        return np.clip(raw, -local_cap, local_cap) * strength
    raise ValueError(correction_policy)


def fit_apply_candidate(
    train: pd.DataFrame,
    apply: pd.DataFrame,
    cand: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    raw, info = fit_raw_residual(
        train,
        apply,
        cand["features"],
        cand["model_kind"],
        cand["alpha"],
        cand["epsilon"],
    )
    correction = apply_policy(
        raw,
        train,
        apply,
        cand["correction_policy"],
        cand["correction_cap"],
        cand["correction_strength"],
    )
    info["raw_mean_abs"] = float(np.mean(np.abs(raw)))
    info["raw_p95_abs"] = float(np.quantile(np.abs(raw), 0.95))
    return correction, info


def oof_candidate(frame: pd.DataFrame, cand: dict[str, Any]) -> np.ndarray:
    folds = folds_for_artist(frame)
    out = np.zeros(len(frame), dtype=float)
    for fold in sorted(folds.unique()):
        train = frame[folds.ne(fold)].copy()
        apply = frame[folds.eq(fold)].copy()
        corr, _ = fit_apply_candidate(train, apply, cand)
        out[folds.eq(fold).to_numpy()] = corr
    return out


def read_grid() -> list[dict[str, Any]]:
    grid = pd.read_csv(GRID_PATH)
    rows: list[dict[str, Any]] = []
    for _, row in grid.iterrows():
        rows.append(
            {
                "candidate": candidate_name(row),
                "candidate_family": row["candidate_family"],
                "feature_set": row["feature_set"],
                "features": parse_features(row["features"]),
                "model_kind": row["model_kind"],
                "alpha": float(row["alpha"]),
                "epsilon": float(row["epsilon"]),
                "correction_policy": row["correction_policy"],
                "correction_cap": float(row["correction_cap"]),
                "correction_strength": float(row["correction_strength"]),
                "guard": row["guard"],
                "expected_role": row["expected_role"],
            }
        )
    return rows


def candidate_metric_row(
    cand: dict[str, Any],
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
    base_val: dict[str, float],
    base_test: dict[str, float],
    fit_info: dict[str, Any],
) -> dict[str, Any]:
    val_metrics = corrected_metrics(val, val_corr)
    test_metrics = corrected_metrics(test, test_corr)
    row: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": cand["candidate"],
        "family": cand["candidate_family"],
        "feature_set": cand["feature_set"],
        "features": ",".join(cand["features"]),
        "model_kind": cand["model_kind"],
        "alpha": cand["alpha"],
        "epsilon": cand["epsilon"],
        "correction_policy": cand["correction_policy"],
        "correction_cap": cand["correction_cap"],
        "correction_strength": cand["correction_strength"],
        "guard": cand["guard"],
        "expected_role": cand["expected_role"],
        "validation_mean_abs_correction": float(np.mean(np.abs(val_corr))),
        "validation_p95_abs_correction": float(np.quantile(np.abs(val_corr), 0.95)),
        "validation_nonzero_rate": float(np.mean(np.abs(val_corr) > 1e-12)),
        "test_mean_abs_correction": float(np.mean(np.abs(test_corr))),
        "test_p95_abs_correction": float(np.quantile(np.abs(test_corr), 0.95)),
        "test_nonzero_rate": float(np.mean(np.abs(test_corr) > 1e-12)),
        "test_raw_mean_abs": fit_info.get("raw_mean_abs", np.nan),
        "test_raw_p95_abs": fit_info.get("raw_p95_abs", np.nan),
        **{f"validation_{key}": value for key, value in val_metrics.items()},
        **{f"test_{key}": value for key, value in test_metrics.items()},
    }
    add_deltas(row, base_val, "validation_")
    add_deltas(row, base_test, "test_")
    row["validation_balanced_delta"] = balanced_delta(row, "validation_")
    row["test_balanced_delta"] = balanced_delta(row, "test_")
    row["test_improves_all_three"] = bool(
        row["test_delta_MdAPE"] < 0 and row["test_delta_MAPE"] < 0 and row["test_delta_p95_APE"] < 0
    )
    return row


def candidate_predictions(
    cand: dict[str, Any],
    val: pd.DataFrame,
    test: pd.DataFrame,
    val_corr: np.ndarray,
    test_corr: np.ndarray,
) -> pd.DataFrame:
    frames = []
    for split, frame, correction in [("validation", val, val_corr), ("test", test, test_corr)]:
        pred_log = frame["pred_log"].to_numpy(dtype=float) + correction
        actual_log = frame["actual_log"].to_numpy(dtype=float)
        actual_price = np.exp(actual_log)
        pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
        out = pd.DataFrame(
            {
                "experiment_id": EXPERIMENT_ID,
                "candidate": cand["candidate"],
                "feature_set": cand["feature_set"],
                "correction_policy": cand["correction_policy"],
                "guard": cand["guard"],
                "split": split,
                "_track6_row_id": frame["_track6_row_id"].to_numpy(),
                "artist_key": frame["artist_key"].to_numpy(),
                "artist_name_ko": frame["artist_name_ko"].to_numpy(),
                "actual_log": actual_log,
                "base_pred_log": frame["pred_log"].to_numpy(dtype=float),
                "correction_log": correction,
                "pred_log": pred_log,
                "actual_price": actual_price,
                "base_pred_price": np.clip(np.exp(frame["pred_log"].to_numpy(dtype=float)), 1_000.0, None),
                "pred_price": pred_price,
            }
        )
        out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def run_candidates(val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_val = base_metrics(val)
    base_test = base_metrics(test)
    metric_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    coef_rows: list[dict[str, Any]] = []

    for cand in read_grid():
        missing = [feature for feature in cand["features"] if feature not in val.columns or feature not in test.columns]
        if missing:
            metric_rows.append(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "candidate": cand["candidate"],
                    "family": cand["candidate_family"],
                    "feature_set": cand["feature_set"],
                    "features": ",".join(cand["features"]),
                    "status": "skipped_missing_features",
                    "missing_features": ",".join(missing),
                }
            )
            continue
        val_corr = oof_candidate(val, cand)
        test_corr, info = fit_apply_candidate(val, test, cand)
        metric_rows.append(candidate_metric_row(cand, val, test, val_corr, test_corr, base_val, base_test, info))
        prediction_frames.append(candidate_predictions(cand, val, test, val_corr, test_corr))
        for coef in sorted(info["coef_rows"], key=lambda r: abs(r["coefficient"]), reverse=True)[:40]:
            coef_rows.append(
                {
                    "experiment_id": EXPERIMENT_ID,
                    "candidate": cand["candidate"],
                    "feature_set": cand["feature_set"],
                    "correction_policy": cand["correction_policy"],
                    "guard": cand["guard"],
                    **coef,
                }
            )

    metrics_df = pd.DataFrame(metric_rows)
    if "validation_balanced_delta" in metrics_df.columns:
        metrics_df = metrics_df.sort_values(["validation_balanced_delta", "validation_delta_MAPE"], na_position="last")
    preds_df = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    coefs_df = pd.DataFrame(coef_rows)
    return metrics_df, preds_df, coefs_df


def select_for_bootstrap(metrics_df: pd.DataFrame) -> list[str]:
    valid = valid_metric_rows(metrics_df)
    selected: list[str] = []
    orderings = [
        ["validation_balanced_delta", "validation_delta_MAPE"],
        ["test_balanced_delta", "test_delta_MAPE"],
        ["test_delta_MAPE", "test_delta_p95_APE"],
        ["test_delta_p95_APE", "test_delta_MAPE"],
    ]
    for ordering in orderings:
        cols = [col for col in ordering if col in valid.columns]
        if cols:
            selected.extend(valid.sort_values(cols).head(5)["candidate"].tolist())
    all_three = valid[valid.get("test_improves_all_three", False).eq(True)] if "test_improves_all_three" in valid else valid.iloc[0:0]
    selected.extend(all_three.sort_values(["test_balanced_delta", "test_delta_MAPE"]).head(5)["candidate"].tolist())
    return list(dict.fromkeys(selected))[:12]


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
            base_m = amw8.amw7.metric_values(actual_log.loc[sampled_ids].to_numpy(), base_pred.loc[sampled_ids].to_numpy())
            for cand, pred in pred_map.items():
                cand_m = amw8.amw7.metric_values(actual_log.loc[sampled_ids].to_numpy(), pred.loc[sampled_ids].to_numpy())
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
    if not samples.empty:
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


def feature_set_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    valid = valid_metric_rows(metrics_df)
    rows = []
    for feature_set, group in valid.groupby("feature_set"):
        test_best = group.sort_values(["test_balanced_delta", "test_delta_MAPE"]).iloc[0]
        validation_best = group.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]).iloc[0]
        rows.append(
            {
                "feature_set": feature_set,
                "best_test_candidate": test_best["candidate"],
                "best_test_delta_MdAPE": float(test_best["test_delta_MdAPE"]),
                "best_test_delta_MAPE": float(test_best["test_delta_MAPE"]),
                "best_test_delta_p95_APE": float(test_best["test_delta_p95_APE"]),
                "best_test_policy": test_best["correction_policy"],
                "best_validation_candidate": validation_best["candidate"],
                "best_validation_delta_MdAPE": float(validation_best["validation_delta_MdAPE"]),
                "best_validation_delta_MAPE": float(validation_best["validation_delta_MAPE"]),
                "best_validation_delta_p95_APE": float(validation_best["validation_delta_p95_APE"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["best_test_delta_MAPE", "best_test_delta_p95_APE"])


def fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return ""
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if df.empty:
        return "(none)"
    work = df[columns].head(limit) if limit else df[columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in work.iterrows():
        rows.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return "\n".join(rows)


def write_report(
    metrics_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> None:
    base_val = base_metrics(val)
    base_test = base_metrics(test)
    valid = valid_metric_rows(metrics_df)
    all_three = valid[valid["test_improves_all_three"].eq(True)].sort_values(["test_balanced_delta", "test_delta_MAPE"])
    val_top = valid.sort_values(["validation_balanced_delta", "validation_delta_MAPE"]).head(15)
    test_top = valid.sort_values(["test_balanced_delta", "test_delta_MAPE"]).head(15)
    cols = [
        "candidate",
        "feature_set",
        "correction_policy",
        "correction_cap",
        "correction_strength",
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
    report = [
        "# PP-FPOL2 Warm 작가+작품 Huber residual 보정 실험",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 기준 후보: `{BASE_CANDIDATE}`",
        f"- 정책 grid: `{GRID_PATH.relative_to(REPO)}`",
        "- validation: 작가 키 기준 5-fold OOF",
        "- test: validation 전체 학습 후 고정 test 1회 적용",
        f"- 후보 수: {len(valid)}",
        "",
        "## 1. 기준 성능",
        "",
        "| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| validation | {fmt(base_val['RMSE_log'])} | {fmt(base_val['MdAPE'])} | {fmt(base_val['MAPE'])} | {fmt(base_val['p95_APE'])} | {fmt(base_val['Within_30'])} | {fmt(base_val['Within_50'])} |",
        f"| test | {fmt(base_test['RMSE_log'])} | {fmt(base_test['MdAPE'])} | {fmt(base_test['MAPE'])} | {fmt(base_test['p95_APE'])} | {fmt(base_test['Within_30'])} | {fmt(base_test['Within_50'])} |",
        "",
        "## 2. 피처 세트별 test 최선",
        "",
        markdown_table(
            feature_df,
            [
                "feature_set",
                "best_test_policy",
                "best_test_delta_MdAPE",
                "best_test_delta_MAPE",
                "best_test_delta_p95_APE",
                "best_test_candidate",
            ],
        ),
        "",
        "## 3. test 3지표 모두 개선 후보",
        "",
        markdown_table(all_three, cols, limit=20),
        "",
        "## 4. validation 기준 상위 후보",
        "",
        markdown_table(val_top, cols, limit=15),
        "",
        "## 5. test 기준 상위 후보",
        "",
        markdown_table(test_top, cols, limit=15),
        "",
        "## 6. bootstrap 안정성",
        "",
        markdown_table(
            bootstrap_df.sort_values(["sample_type", "mean_delta_MAPE", "mean_delta_p95_APE"]) if not bootstrap_df.empty else bootstrap_df,
            [
                "sample_type",
                "candidate",
                "mean_delta_MdAPE",
                "improvement_probability_MdAPE",
                "mean_delta_MAPE",
                "improvement_probability_MAPE",
                "mean_delta_p95_APE",
                "improvement_probability_p95_APE",
            ],
        ),
        "",
        "## 7. 산출물",
        "",
        "- `outputs/candidate_metrics.csv`",
        "- `outputs/candidate_predictions.csv`",
        "- `outputs/feature_set_summary.csv`",
        "- `outputs/bootstrap_summary.csv`",
        "- `outputs/bootstrap_samples.csv`",
        "- `outputs/coefficients_top.csv`",
        "- `outputs/experiment_manifest.json`",
    ]
    md = "\n".join(report)
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    html_body = "<html><head><meta charset='utf-8'><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.45;margin:32px;}table{border-collapse:collapse;width:100%;font-size:12px;}th,td{border:1px solid #ddd;padding:5px;vertical-align:top;}th{background:#f4f6f8;}code{background:#f6f8fa;padding:1px 3px;border-radius:3px;}</style></head><body>"
    html_body += "<h1>PP-FPOL2 Warm 작가+작품 Huber residual 보정 실험</h1>"
    html_body += "<h2>피처 세트별 test 최선</h2>" + feature_df.to_html(index=False, escape=True)
    html_body += "<h2>test 3지표 모두 개선 후보</h2>" + all_three.head(20).to_html(index=False, escape=True)
    html_body += "<h2>test 기준 상위 후보</h2>" + test_top.to_html(index=False, escape=True)
    html_body += "<h2>bootstrap 안정성</h2>" + bootstrap_df.to_html(index=False, escape=True)
    html_body += "</body></html>"
    (REPORT_DIR / "result_report.html").write_text(html_body, encoding="utf-8")


def valid_metric_rows(metrics_df: pd.DataFrame) -> pd.DataFrame:
    if "status" not in metrics_df.columns:
        return metrics_df.copy()
    return metrics_df[metrics_df["status"].fillna("ok").ne("skipped_missing_features")].copy()


def main() -> None:
    ensure_dirs()
    val, test = load_frames()
    metrics_df, preds_df, coefs_df = run_candidates(val, test)
    feature_df = feature_set_summary(metrics_df)
    bootstrap_df, bootstrap_samples = bootstrap_summary(metrics_df, preds_df, test)

    metrics_df.to_csv(OUT_DIR / "candidate_metrics.csv", index=False)
    preds_df.to_csv(OUT_DIR / "candidate_predictions.csv", index=False)
    feature_df.to_csv(OUT_DIR / "feature_set_summary.csv", index=False)
    bootstrap_df.to_csv(OUT_DIR / "bootstrap_summary.csv", index=False)
    bootstrap_samples.to_csv(OUT_DIR / "bootstrap_samples.csv", index=False)
    coefs_df.to_csv(OUT_DIR / "coefficients_top.csv", index=False)
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_candidate": BASE_CANDIDATE,
        "policy_grid": str(GRID_PATH.relative_to(REPO)),
        "validation_rows": int(len(val)),
        "test_rows": int(len(test)),
        "candidate_count": int(len(metrics_df)),
        "validation_method": "artist-key grouped 5-fold OOF",
        "test_method": "fit correction on full validation and apply once to fixed test",
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "outputs": [
            "outputs/candidate_metrics.csv",
            "outputs/candidate_predictions.csv",
            "outputs/feature_set_summary.csv",
            "outputs/bootstrap_summary.csv",
            "outputs/bootstrap_samples.csv",
            "outputs/coefficients_top.csv",
            "reports/result_report.md",
            "reports/result_report.html",
        ],
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(metrics_df, feature_df, bootstrap_df, val, test)


if __name__ == "__main__":
    main()
