#!/usr/bin/env python3
"""Run Track6 PP-L postprocessing experiments.

The PP-L group checks whether Huber, Quantile, and CatBoost combinations can
reduce MAPE and p95_APE without hurting MdAPE.  The script keeps the current
Track6 final artifact feature sets fixed and writes one independent folder per
PP-L experiment under experiments/track6.
"""
from __future__ import annotations

import html
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from scipy.stats import wilcoxon
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = REPO / "data" / "track6_split"
ARTIFACT_MANIFEST = REPO / "data" / "track6" / "artifacts" / "track6_artifact_manifest.json"
BASE_EXP_DIR = REPO / "experiments" / "track6"
SEED = 20260602

BASE_NUMERIC = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
BASE_CATEGORICAL = ["has_depth", "is_3d_candidate", "medium_category", "support_category"]
GENERATED = [
    "size_bucket",
    "shape_bucket",
    "medium_size_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]

EXPERIMENTS = {
    "PP-L1": {
        "slug": "PP-L1_catboost_mape_objective",
        "title": "CatBoost MAPE 목적 최적화",
    },
    "PP-L2": {
        "slug": "PP-L2_catboost_mape_sensitivity",
        "title": "CatBoost 옵션별 MAPE 민감도",
    },
    "PP-L3": {
        "slug": "PP-L3_huber_catboost_residual",
        "title": "Huber 선행 + CatBoost residual 보정",
    },
    "PP-L4": {
        "slug": "PP-L4_huber_quantile_width_risk_calibration",
        "title": "Huber + Quantile width 위험 구간 보정",
    },
    "PP-L5": {
        "slug": "PP-L5_huber_quantile_catboost_routing",
        "title": "Huber + Quantile + CatBoost 라우팅",
    },
    "PP-L6": {
        "slug": "PP-L6_huber_quantile_catboost_weighted_ensemble",
        "title": "Huber / Quantile / CatBoost 가중 앙상블",
    },
    "PP-L7-0": {
        "slug": "PP-L7_0_quantile_segment_validation",
        "title": "Quantile 구간 생성 및 검증",
    },
    "PP-L7-H": {
        "slug": "PP-L7_H_quantile_segment_huber_refit",
        "title": "Quantile 구간별 Huber 상세 학습",
    },
    "PP-L7-CB": {
        "slug": "PP-L7_CB_quantile_segment_catboost_refit",
        "title": "Quantile 구간별 CatBoost 상세 학습",
    },
    "PP-L7-HCB": {
        "slug": "PP-L7_HCB_quantile_segment_huber_catboost_combo",
        "title": "Quantile 구간별 Huber + CatBoost 결합",
    },
    "PP-L8": {
        "slug": "PP-L8_quantile_huber_catboost_sequential",
        "title": "Quantile-Huber-CatBoost 순차 학습",
    },
    "PP-L9": {
        "slug": "PP-L9_huber_quantile_catboost_residual_sequential",
        "title": "Huber-Quantile-CatBoost residual 순차 학습",
    },
}


@dataclass
class ScopeData:
    scope: str
    features: list[str]
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    numeric_features: list[str]


def load_manifest_features() -> dict[str, list[str]]:
    manifest = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for item in manifest["artifacts"]:
        if item["key"] == "warm_price_model":
            out["warm"] = item["features"]
        elif item["key"] == "cold_catboost_price_model":
            out["cold"] = item["features"]
    return out


def read_join(feature_path: Path, label_path: Path, columns: list[str]) -> pd.DataFrame:
    features = pd.read_csv(feature_path, low_memory=False)
    labels = pd.read_csv(label_path, low_memory=False)
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    for col in ["artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]:
        if col in labels.columns and col not in label_cols:
            label_cols.append(col)
    merged = features.merge(labels[label_cols], on="_track6_row_id", how="inner", suffixes=("", "__label"))
    for col in columns:
        label_col = f"{col}__label"
        if col not in merged.columns and col in labels.columns:
            merged[col] = labels.set_index("_track6_row_id").loc[merged["_track6_row_id"], col].to_numpy()
        elif col in merged.columns and label_col in merged.columns:
            merged[col] = merged[col].where(merged[col].notna(), merged[label_col])
    missing = [col for col in columns if col not in merged.columns]
    if missing:
        raise ValueError(f"{feature_path} missing required columns: {missing}")
    merged["price_krw"] = pd.to_numeric(merged["price_krw"], errors="coerce")
    merged["ln_price_krw"] = pd.to_numeric(merged["ln_price_krw"], errors="coerce")
    return merged.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def size_edges(train: pd.DataFrame) -> np.ndarray:
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    quantiles = np.quantile(values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    quantiles[0] = -np.inf
    quantiles[-1] = np.inf
    return np.unique(quantiles)


def add_generated_features(train: pd.DataFrame, *frames: pd.DataFrame) -> list[pd.DataFrame]:
    edges = size_edges(train)
    large_cut = float(np.nanquantile(pd.to_numeric(train["area_cm2"], errors="coerce"), 0.80))

    def transform(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        log_area = pd.to_numeric(out["log_area"], errors="coerce")
        aspect = pd.to_numeric(out["aspect_ratio"], errors="coerce")
        area = pd.to_numeric(out["area_cm2"], errors="coerce")
        is_3d = out["is_3d_candidate"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])
        labels = [f"q{i + 1}" for i in range(len(edges) - 1)]
        out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
        out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
        out["shape_bucket"] = np.select(
            [aspect.isna(), aspect < 0.65, aspect <= 1.55, aspect <= 2.5, aspect > 2.5],
            ["__MISSING__", "tall", "balanced", "wide", "extreme_wide"],
            default="__MISSING__",
        )
        out["medium_size_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["support_size_bucket"] = out["support_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["medium_shape_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["shape_bucket"].astype(str)
        out["is_large_2d"] = ((area >= large_cut) & ~is_3d).astype(str)
        out["is_large_3d"] = ((area >= large_cut) & is_3d).astype(str)
        return out

    return [transform(frame) for frame in (train, *frames)]


def normalize(frame: pd.DataFrame, columns: list[str], numeric_features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        if col in numeric_features:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def load_scope(scope: str, features: list[str]) -> ScopeData:
    feature_dir = SPLIT_ROOT / "features" / scope
    label_dir = SPLIT_ROOT / "labels"
    prefix = "warm" if scope == "warm" else "cold"
    train_f = feature_dir / f"track6_train_{prefix}_features.csv"
    val_f = feature_dir / f"track6_val_{prefix}_{prefix}_features.csv"
    test_f = feature_dir / f"track6_test_{prefix}_{prefix}_features.csv"
    generation_inputs = ["area_cm2", "log_area", "aspect_ratio", "is_3d_candidate", "medium_category", "support_category"]
    source_features = [col for col in features if col not in GENERATED]
    required = list(dict.fromkeys(source_features + generation_inputs))
    train = read_join(train_f, label_dir / "track6_train_labels.csv", required)
    val = read_join(val_f, label_dir / f"track6_val_{prefix}_labels.csv", required)
    test = read_join(test_f, label_dir / f"track6_test_{prefix}_labels.csv", required)
    train, val, test = add_generated_features(train, val, test)
    numeric = [col for col in BASE_NUMERIC if col in features]
    train = normalize(train, features, numeric)
    val = normalize(val, features, numeric)
    test = normalize(test, features, numeric)
    for frame in [train, val, test]:
        frame["scope"] = scope
    return ScopeData(scope=scope, features=features, train=train, val=val, test=test, numeric_features=numeric)


def onehot_model(features: list[str], numeric_features: list[str]) -> Pipeline:
    numeric = [c for c in numeric_features if c in features]
    categorical = [c for c in features if c not in numeric]
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)),
    ])


def cat_frame(frame: pd.DataFrame, features: list[str], numeric_features: list[str]) -> pd.DataFrame:
    out = frame[features].copy()
    for col in features:
        if col in numeric_features:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = out[col].astype(str).fillna("__MISSING__")
    return out


def cat_indices(features: list[str], numeric_features: list[str]) -> list[int]:
    return [idx for idx, col in enumerate(features) if col not in numeric_features]


def cat_model(**overrides: Any) -> CatBoostRegressor:
    params = {
        "loss_function": "RMSE",
        "iterations": 260,
        "learning_rate": 0.04,
        "depth": 6,
        "l2_leaf_reg": 6.0,
        "random_seed": SEED,
        "verbose": False,
        "allow_writing_files": False,
    }
    params.update(overrides)
    return CatBoostRegressor(**params)


def metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def prediction_rows(
    experiment_id: str,
    candidate: str,
    scope: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": experiment_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"].to_numpy(),
        "actual_log": frame["ln_price_krw"].to_numpy(dtype=float),
        "pred_log": pred_log,
        "actual_price": frame["price_krw"].to_numpy(dtype=float),
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    if extra:
        for key, value in extra.items():
            out[key] = value
    return out


def metric_row(experiment_id: str, candidate: str, scope: str, split: str, pred: pd.DataFrame, notes: str = "") -> dict[str, Any]:
    m = metrics(pred["actual_price"].to_numpy(), pred["actual_log"].to_numpy(), pred["pred_log"].to_numpy())
    return {
        "experiment_id": experiment_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "n": int(len(pred)),
        "notes": notes,
        **m,
    }


def train_huber(scope: ScopeData, features: list[str] | None = None) -> tuple[Pipeline, dict[str, np.ndarray]]:
    cols = features or scope.features
    model = onehot_model(cols, scope.numeric_features)
    model.fit(scope.train[cols], scope.train["ln_price_krw"].to_numpy())
    return model, {
        "train": np.asarray(model.predict(scope.train[cols]), dtype=float),
        "validation": np.asarray(model.predict(scope.val[cols]), dtype=float),
        "test": np.asarray(model.predict(scope.test[cols]), dtype=float),
    }


def train_catboost(
    scope: ScopeData,
    *,
    target: np.ndarray | None = None,
    features: list[str] | None = None,
    sample_weight: np.ndarray | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[CatBoostRegressor, dict[str, np.ndarray]]:
    cols = features or scope.features
    model = cat_model(**(params or {}))
    x_train = cat_frame(scope.train, cols, scope.numeric_features)
    y = target if target is not None else scope.train["ln_price_krw"].to_numpy()
    model.fit(x_train, y, cat_features=cat_indices(cols, scope.numeric_features), sample_weight=sample_weight)
    return model, {
        "train": np.asarray(model.predict(x_train), dtype=float),
        "validation": np.asarray(model.predict(cat_frame(scope.val, cols, scope.numeric_features)), dtype=float),
        "test": np.asarray(model.predict(cat_frame(scope.test, cols, scope.numeric_features)), dtype=float),
    }


def oof_huber(scope: ScopeData, folds: int = 3) -> np.ndarray:
    pred = np.full(len(scope.train), np.nan)
    kf = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    for train_idx, holdout_idx in kf.split(scope.train):
        fold = onehot_model(scope.features, scope.numeric_features)
        fold.fit(scope.train.iloc[train_idx][scope.features], scope.train.iloc[train_idx]["ln_price_krw"].to_numpy())
        pred[holdout_idx] = fold.predict(scope.train.iloc[holdout_idx][scope.features])
    return pred


def quantile_preds(scope: ScopeData, target: np.ndarray | None = None) -> dict[str, dict[str, np.ndarray]]:
    out: dict[str, dict[str, np.ndarray]] = {}
    y = target if target is not None else scope.train["ln_price_krw"].to_numpy()
    for label, alpha in [("q10", 0.10), ("q50", 0.50), ("q90", 0.90)]:
        _model, pred = train_catboost(scope, target=y, params={"loss_function": f"Quantile:alpha={alpha}", "iterations": 220})
        out[label] = pred
    return out


def uncertainty_segment(width: np.ndarray, low_cut: float, high_cut: float) -> np.ndarray:
    return np.select([width <= low_cut, width <= high_cut], ["low", "mid"], default="high")


def residual_correction_by_segment(actual_log: np.ndarray, pred_log: np.ndarray, segment: np.ndarray) -> dict[str, float]:
    residual = actual_log - pred_log
    return {seg: float(np.median(residual[segment == seg])) for seg in sorted(set(segment))}


def apply_segment_correction(pred_log: np.ndarray, segment: np.ndarray, correction: dict[str, float]) -> np.ndarray:
    out = pred_log.copy()
    for seg, value in correction.items():
        out[segment == seg] = out[segment == seg] + value
    return out


def low_price_weights(price: np.ndarray) -> np.ndarray:
    q25 = np.quantile(price, 0.25)
    q50 = np.quantile(price, 0.50)
    return np.select([price <= q25, price <= q50], [2.0, 1.35], default=1.0).astype(float)


def choose_weights(val_preds: list[np.ndarray], actual_price: np.ndarray, actual_log: np.ndarray) -> tuple[list[float], np.ndarray]:
    grids = np.linspace(0.0, 1.0, 6)
    best_score = (math.inf, math.inf)
    best_weights = [1.0, 0.0, 0.0]
    best_pred = val_preds[0]
    for w0 in grids:
        for w1 in grids:
            for w2 in grids:
                s = w0 + w1 + w2
                if s <= 0:
                    continue
                weights = np.array([w0, w1, w2], dtype=float) / s
                pred = sum(weights[i] * val_preds[i] for i in range(3))
                m = metrics(actual_price, actual_log, pred)
                score = (m["MdAPE"], m["MAPE"])
                if score < best_score:
                    best_score = score
                    best_weights = [float(x) for x in weights]
                    best_pred = pred
    return best_weights, best_pred


def seed_repeat_rows(scope: ScopeData, exp_id: str, specs: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seeds = [SEED, SEED + 1, SEED + 2]
    for candidate, params in specs:
        metric_values: list[dict[str, float]] = []
        for seed in seeds:
            run_params = dict(params)
            run_params["random_seed"] = seed
            _model, pred = train_catboost(scope, params=run_params)
            metric_values.append(metrics(
                scope.val["price_krw"].to_numpy(),
                scope.val["ln_price_krw"].to_numpy(),
                pred["validation"],
            ))
        for metric_name in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            values = np.array([m[metric_name] for m in metric_values], dtype=float)
            rows.append({
                "experiment_id": exp_id,
                "test_type": "seed_repeat",
                "scope": scope.scope,
                "candidate": candidate,
                "baseline": "",
                "seed_count": len(seeds),
                "metric": metric_name,
                "seed_mean": float(np.mean(values)),
                "seed_std": float(np.std(values, ddof=1)),
                "seeds": ",".join(str(s) for s in seeds),
            })
    return rows


def bootstrap_ci(base_ape: np.ndarray, cand_ape: np.ndarray, iterations: int = 300) -> tuple[float, float, float]:
    rng = np.random.default_rng(SEED)
    diffs = []
    n = len(base_ape)
    for _ in range(iterations):
        idx = rng.integers(0, n, size=n)
        diffs.append(float(np.mean(cand_ape[idx] - base_ape[idx])))
    arr = np.asarray(diffs)
    return float(np.mean(cand_ape - base_ape)), float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


def wilcoxon_p(base_ape: np.ndarray, cand_ape: np.ndarray) -> float:
    try:
        return float(wilcoxon(cand_ape, base_ape, zero_method="zsplit").pvalue)
    except Exception:
        return float("nan")


def make_slice_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys in [["experiment_id", "candidate", "scope", "split"], ["experiment_id", "candidate", "scope", "split", "uncertainty_segment"]]:
        if any(key not in predictions.columns for key in keys):
            continue
        for values, group in predictions.groupby(keys, dropna=False):
            values_tuple = values if isinstance(values, tuple) else (values,)
            row = dict(zip(keys, values_tuple, strict=False))
            row.update(metrics(group["actual_price"].to_numpy(), group["actual_log"].to_numpy(), group["pred_log"].to_numpy()))
            row["n"] = int(len(group))
            rows.append(row)
    return pd.DataFrame(rows)


def render_report(exp_id: str, title: str, metrics_df: pd.DataFrame, stats_df: pd.DataFrame, segment_df: pd.DataFrame) -> tuple[str, str]:
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        f"- 실행 시각: `{datetime.now().isoformat(timespec='seconds')}`",
        "- 데이터 기준: `data/track6_split` 고정 train / validation / test",
        "- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋",
        "- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용",
        "",
        "## Validation 결과",
        "",
        "| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.candidate}` | `{row.scope}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` | `{row.n}` |")
    lines += [
        "",
        "## 통계 검증 요약",
        "",
        "- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.",
        "- bootstrap CI는 validation paired bootstrap 기준이다.",
        "",
    ]
    if not stats_df.empty:
        lines += ["| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |", "|---|---|---|---:|---:|---:|---:|"]
        for row in stats_df.itertuples():
            lines.append(f"| `{row.candidate}` | `{row.scope}` | `{row.baseline}` | `{row.mean_ape_delta:.4f}` | `{row.ci_low:.4f}` | `{row.ci_high:.4f}` | `{row.wilcoxon_p:.4f}` |")
    lines += [
        "",
        "## 구간 기준",
        "",
    ]
    if not segment_df.empty:
        for row in segment_df.itertuples():
            lines.append(f"- `{row.scope}` `{row.segment_rule}`: low_cut=`{row.low_cut:.6f}`, high_cut=`{row.high_cut:.6f}`")
    md = "\n".join(lines) + "\n"
    html_table = val.to_html(index=False, escape=True)
    html_stats = stats_df.to_html(index=False, escape=True) if not stats_df.empty else "<p>통계 검증 대상 없음</p>"
    html_segment = segment_df.to_html(index=False, escape=True) if not segment_df.empty else "<p>구간 기준 없음</p>"
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)} {html.escape(title)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1>
<p>기준 split과 final artifact 피처셋을 고정하고 validation 기준으로 보정값을 산정했다.</p>
<h2>Validation 결과</h2>{html_table}
<h2>통계 검증</h2>{html_stats}
<h2>구간 기준</h2>{html_segment}
</body></html>"""
    return md, html_doc


def write_experiment(
    exp_id: str,
    config: dict[str, Any],
    metrics_rows: list[dict[str, Any]],
    predictions: list[pd.DataFrame],
    oof_predictions: pd.DataFrame,
    residuals: pd.DataFrame,
    segments: list[dict[str, Any]],
    complexity: list[dict[str, Any]],
    calibration_map: dict[str, Any],
    routing_policy: dict[str, Any],
    seed_stats: list[dict[str, Any]],
) -> None:
    info = EXPERIMENTS[exp_id]
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    segment_df = pd.DataFrame(segments)
    slice_df = make_slice_metrics(pred_df) if not pred_df.empty else pd.DataFrame()
    residual_df = residuals
    stats_rows = []
    if not pred_df.empty:
        val_pred = pred_df[pred_df["split"].eq("validation")]
        for scope in sorted(val_pred["scope"].dropna().unique()):
            baseline_name = "B0_Warm_Huber" if scope == "warm" else "B1_Cold_CatBoost"
            base = val_pred[(val_pred["scope"].eq(scope)) & (val_pred["candidate"].eq(baseline_name))]
            if base.empty:
                continue
            base = base.sort_values("_track6_row_id")
            for cand in sorted(val_pred.loc[val_pred["scope"].eq(scope), "candidate"].unique()):
                if cand == baseline_name:
                    continue
                cur = val_pred[(val_pred["scope"].eq(scope)) & (val_pred["candidate"].eq(cand))].sort_values("_track6_row_id")
                merged = base[["_track6_row_id", "ape"]].merge(cur[["_track6_row_id", "ape"]], on="_track6_row_id", suffixes=("_base", "_candidate"))
                if len(merged) < 5:
                    continue
                mean_delta, ci_low, ci_high = bootstrap_ci(merged["ape_base"].to_numpy(), merged["ape_candidate"].to_numpy())
                stats_rows.append({
                    "experiment_id": exp_id,
                    "test_type": "paired_bootstrap_wilcoxon",
                    "scope": scope,
                    "candidate": cand,
                    "baseline": baseline_name,
                    "mean_ape_delta": mean_delta,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "wilcoxon_p": wilcoxon_p(merged["ape_base"].to_numpy(), merged["ape_candidate"].to_numpy()),
                })
                if "uncertainty_segment" in cur.columns:
                    cur_seg = cur[["_track6_row_id", "ape", "uncertainty_segment"]]
                    merged_seg = base[["_track6_row_id", "ape"]].merge(cur_seg, on="_track6_row_id", suffixes=("_base", "_candidate"))
                    for segment, seg_group in merged_seg.groupby("uncertainty_segment", dropna=True):
                        if len(seg_group) < 10:
                            continue
                        s_delta, s_low, s_high = bootstrap_ci(seg_group["ape_base"].to_numpy(), seg_group["ape_candidate"].to_numpy())
                        stats_rows.append({
                            "experiment_id": exp_id,
                            "test_type": "segment_bootstrap",
                            "scope": scope,
                            "candidate": cand,
                            "baseline": baseline_name,
                            "segment": segment,
                            "segment_n": int(len(seg_group)),
                            "mean_ape_delta": s_delta,
                            "ci_low": s_low,
                            "ci_high": s_high,
                            "wilcoxon_p": float("nan"),
                        })
    stats_rows.extend(seed_stats)
    stats_df = pd.DataFrame(stats_rows)
    complexity_df = pd.DataFrame(complexity)

    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    slice_df.to_csv(exp_dir / "outputs" / "slice_metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    oof_predictions.to_csv(exp_dir / "outputs" / "oof_predictions.csv", index=False)
    residual_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    segment_df.to_csv(exp_dir / "outputs" / "segment_definition.csv", index=False)
    stats_df.to_csv(exp_dir / "outputs" / "statistical_tests.csv", index=False)
    complexity_df.to_csv(exp_dir / "outputs" / "complexity_report.csv", index=False)

    split_manifest = {
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "train": "track6_train",
        "validation": ["track6_val_warm", "track6_val_cold"],
        "test": ["track6_test_warm", "track6_test_cold"],
        "index_files": {
            "train": "data/train_index.csv",
            "validation": "data/valid_index.csv",
            "test": "data/test_index.csv",
        },
        "policy": "validation-only calibration; test used for final reporting only",
    }
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps(split_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if not pred_df.empty:
        index_cols = ["scope", "split", "_track6_row_id"]
        pred_df.loc[pred_df["split"].eq("validation"), index_cols].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
        pred_df.loc[pred_df["split"].eq("test"), index_cols].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    if not oof_predictions.empty:
        train_index = oof_predictions[["scope", "_track6_row_id"]].drop_duplicates().copy()
        train_index.insert(1, "split", "train")
        train_index.to_csv(exp_dir / "data" / "train_index.csv", index=False)
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(calibration_map, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "routing_policy.json").write_text(json.dumps(routing_policy, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, info["title"], metrics_df, stats_df, segment_df)
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(
        f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed metrics={len(metrics_df)} predictions={len(pred_df)}\n",
        encoding="utf-8",
    )


def add_candidate(
    exp_store: dict[str, dict[str, Any]],
    exp_id: str,
    candidate: str,
    scope: ScopeData,
    preds: dict[str, np.ndarray],
    notes: str = "",
    extra: dict[str, dict[str, Any]] | None = None,
) -> None:
    store = exp_store[exp_id]
    for split_name, frame in [("validation", scope.val), ("test", scope.test)]:
        extra_split = extra.get(split_name, {}) if extra else {}
        pred_df = prediction_rows(exp_id, candidate, scope.scope, split_name, frame, preds[split_name], extra_split)
        store["predictions"].append(pred_df)
        store["metrics"].append(metric_row(exp_id, candidate, scope.scope, split_name, pred_df, notes))


def main() -> None:
    start = time.time()
    manifest_features = load_manifest_features()
    warm = load_scope("warm", manifest_features["warm"])
    cold = load_scope("cold", manifest_features["cold"])
    scopes = [warm, cold]
    exp_store: dict[str, dict[str, Any]] = {
        exp_id: {
            "metrics": [],
            "predictions": [],
            "segments": [],
            "complexity": [],
            "calibration": {},
            "routing": {},
            "seed_stats": [],
        }
        for exp_id in EXPERIMENTS
    }

    feature_columns = {scope.scope: scope.features for scope in scopes}
    model_manifest = {"seed": SEED, "target": "ln_price_krw", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}

    oof_frames = []
    residual_frames = []
    base_preds: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    quantiles: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    segment_info: dict[str, dict[str, Any]] = {}

    for scope in scopes:
        huber_model, huber_pred = train_huber(scope)
        catboost_model, catboost_pred = train_catboost(scope)
        huber_oof = oof_huber(scope)
        residual_target = scope.train["ln_price_krw"].to_numpy() - huber_oof
        _, residual_pred = train_catboost(scope, target=residual_target, params={"iterations": 220, "depth": 5})
        huber_cb_pred = {k: huber_pred[k] + residual_pred[k] for k in huber_pred}
        q = quantile_preds(scope)
        width_val = q["q90"]["validation"] - q["q10"]["validation"]
        low_cut, high_cut = np.quantile(width_val, [0.33, 0.66])
        width_train = q["q90"]["train"] - q["q10"]["train"]
        width_test = q["q90"]["test"] - q["q10"]["test"]
        seg_train = uncertainty_segment(width_train, low_cut, high_cut)
        seg_val = uncertainty_segment(width_val, low_cut, high_cut)
        seg_test = uncertainty_segment(width_test, low_cut, high_cut)
        segment_info[scope.scope] = {
            "low_cut": float(low_cut),
            "high_cut": float(high_cut),
            "train": seg_train,
            "validation": seg_val,
            "test": seg_test,
            "width": {"train": width_train, "validation": width_val, "test": width_test},
            "price_range_ratio": {
                "train": np.exp(width_train),
                "validation": np.exp(width_val),
                "test": np.exp(width_test),
            },
        }
        base_preds[scope.scope] = {"huber": huber_pred, "catboost": catboost_pred, "huber_catboost_residual": huber_cb_pred}
        quantiles[scope.scope] = q
        oof_frames.append(pd.DataFrame({
            "_track6_row_id": scope.train["_track6_row_id"],
            "scope": scope.scope,
            "actual_log": scope.train["ln_price_krw"],
            "huber_oof_pred_log": huber_oof,
            "huber_oof_residual_log": residual_target,
        }))
        residual_frames.append(pd.DataFrame({
            "_track6_row_id": scope.train["_track6_row_id"],
            "scope": scope.scope,
            "split": "train_oof",
            "base_model": "Huber",
            "residual_log": residual_target,
        }))

    oof_df = pd.concat(oof_frames, ignore_index=True)
    residual_df = pd.concat(residual_frames, ignore_index=True)

    for scope in scopes:
        baseline_name = "B0_Warm_Huber" if scope.scope == "warm" else "B1_Cold_CatBoost"
        baseline_preds = base_preds[scope.scope]["huber"] if scope.scope == "warm" else base_preds[scope.scope]["catboost"]
        for exp_id in EXPERIMENTS:
            add_candidate(exp_store, exp_id, baseline_name, scope, baseline_preds, "final artifact baseline")
        add_candidate(exp_store, "PP-L6", f"B2_{scope.scope}_Quantile_q50", scope, quantiles[scope.scope]["q50"], "CatBoost Quantile q50 standalone")
        add_candidate(exp_store, "PP-L3", f"B4_{scope.scope}_Huber_CatBoost_residual", scope, base_preds[scope.scope]["huber_catboost_residual"], "OOF Huber residual learned by CatBoost")

    for scope in scopes:
        # PP-L1: CatBoost objective variants.
        variants = {
            "PP-L1_A_existing_CatBoost": ({}, None),
            "PP-L1_B_eval_metric_MAPE": ({"eval_metric": "MAPE"}, None),
            "PP-L1_C_low_price_weight": ({}, low_price_weights(scope.train["price_krw"].to_numpy())),
            "PP-L1_D_MAE_loss": ({"loss_function": "MAE"}, None),
            "PP-L1_D_Quantile_050": ({"loss_function": "Quantile:alpha=0.5"}, None),
        }
        for name, (params, weights) in variants.items():
            _, pred = train_catboost(scope, sample_weight=weights, params=params)
            add_candidate(exp_store, "PP-L1", f"{name}_{scope.scope}", scope, pred, "CatBoost objective/weight variant")

        # PP-L2: limited sensitivity grid.
        for depth in [4, 6, 8]:
            for lr in [0.03, 0.05]:
                params = {"depth": depth, "learning_rate": lr, "iterations": 220, "l2_leaf_reg": 6.0}
                _, pred = train_catboost(scope, params=params)
                add_candidate(exp_store, "PP-L2", f"PP-L2_depth{depth}_lr{lr}_{scope.scope}", scope, pred, "limited CatBoost option grid")
        for l2 in [3.0, 10.0]:
            _, pred = train_catboost(scope, params={"depth": 6, "learning_rate": 0.04, "l2_leaf_reg": l2, "iterations": 220})
            add_candidate(exp_store, "PP-L2", f"PP-L2_l2_{l2:g}_{scope.scope}", scope, pred, "limited CatBoost regularization grid")

        exp_store["PP-L1"]["seed_stats"].extend(seed_repeat_rows(scope, "PP-L1", [
            (f"PP-L1_A_existing_CatBoost_{scope.scope}", {"loss_function": "RMSE", "iterations": 220}),
            (f"PP-L1_D_MAE_loss_{scope.scope}", {"loss_function": "MAE", "iterations": 220}),
            (f"PP-L1_D_Quantile_050_{scope.scope}", {"loss_function": "Quantile:alpha=0.5", "iterations": 220}),
        ]))
        exp_store["PP-L2"]["seed_stats"].extend(seed_repeat_rows(scope, "PP-L2", [
            (f"PP-L2_depth6_lr0.04_{scope.scope}", {"loss_function": "RMSE", "depth": 6, "learning_rate": 0.04, "iterations": 220}),
            (f"PP-L2_depth8_lr0.05_{scope.scope}", {"loss_function": "RMSE", "depth": 8, "learning_rate": 0.05, "iterations": 220}),
        ]))
        exp_store["PP-L6"]["seed_stats"].extend(seed_repeat_rows(scope, "PP-L6", [
            (f"B2_{scope.scope}_Quantile_q50", {"loss_function": "Quantile:alpha=0.5", "iterations": 220}),
        ]))

    for scope in scopes:
        seg = segment_info[scope.scope]
        for exp_id in ["PP-L4", "PP-L7-0"]:
            exp_store[exp_id]["segments"].append({
                "experiment_id": exp_id,
                "scope": scope.scope,
                "segment_rule": "validation_quantile_width_33_66",
                "low_cut": seg["low_cut"],
                "high_cut": seg["high_cut"],
                "price_range_ratio_low_cut": float(np.exp(seg["low_cut"])),
                "price_range_ratio_high_cut": float(np.exp(seg["high_cut"])),
            })
        correction = residual_correction_by_segment(
            scope.val["ln_price_krw"].to_numpy(),
            base_preds[scope.scope]["huber"]["validation"],
            seg["validation"],
        )
        corrected = {
            "validation": apply_segment_correction(base_preds[scope.scope]["huber"]["validation"], seg["validation"], correction),
            "test": apply_segment_correction(base_preds[scope.scope]["huber"]["test"], seg["test"], correction),
        }
        add_candidate(
            exp_store,
            "PP-L4",
            f"PP-L4_{scope.scope}_Huber_quantile_width_segment_median",
            scope,
            corrected,
            "Huber corrected by validation median residual per quantile-width segment",
            extra={
                "validation": {"uncertainty_segment": seg["validation"], "quantile_width": seg["width"]["validation"], "price_range_ratio": seg["price_range_ratio"]["validation"]},
                "test": {"uncertainty_segment": seg["test"], "quantile_width": seg["width"]["test"], "price_range_ratio": seg["price_range_ratio"]["test"]},
            },
        )
        exp_store["PP-L4"]["calibration"][scope.scope] = correction

        # PP-L5: uncertainty routing.
        routed = {}
        for split in ["validation", "test"]:
            routed[split] = base_preds[scope.scope]["huber"][split].copy()
            routed[split][seg[split] == "high"] = base_preds[scope.scope]["huber_catboost_residual"][split][seg[split] == "high"]
            routed[split][seg[split] == "mid"] = corrected[split][seg[split] == "mid"]
        add_candidate(
            exp_store,
            "PP-L5",
            f"PP-L5_{scope.scope}_low_huber_mid_calibrated_high_residual",
            scope,
            routed,
            "low uses Huber, mid uses segment correction, high uses CatBoost residual",
            extra={
                "validation": {"uncertainty_segment": seg["validation"], "quantile_width": seg["width"]["validation"]},
                "test": {"uncertainty_segment": seg["test"], "quantile_width": seg["width"]["test"]},
            },
        )
        exp_store["PP-L5"]["routing"][scope.scope] = {"low": "Huber", "mid": "Huber + segment median residual", "high": "Huber + CatBoost residual"}

        # PP-L6: validation-selected weighted ensemble.
        weights, val_pred = choose_weights(
            [
                base_preds[scope.scope]["huber"]["validation"],
                quantiles[scope.scope]["q50"]["validation"],
                base_preds[scope.scope]["huber_catboost_residual"]["validation"],
            ],
            scope.val["price_krw"].to_numpy(),
            scope.val["ln_price_krw"].to_numpy(),
        )
        test_pred = sum(weights[i] * arr for i, arr in enumerate([
            base_preds[scope.scope]["huber"]["test"],
            quantiles[scope.scope]["q50"]["test"],
            base_preds[scope.scope]["huber_catboost_residual"]["test"],
        ]))
        add_candidate(exp_store, "PP-L6", f"PP-L6_{scope.scope}_validation_weighted_ensemble", scope, {"validation": val_pred, "test": test_pred}, "weights selected on validation")
        exp_store["PP-L6"]["calibration"][scope.scope] = {"weights": {"huber": weights[0], "quantile_q50": weights[1], "huber_catboost_residual": weights[2]}}

        # PP-L7-0 segment validation uses q50 standalone with segment metadata.
        add_candidate(
            exp_store,
            "PP-L7-0",
            f"PP-L7_0_{scope.scope}_quantile_q50_segment_view",
            scope,
            quantiles[scope.scope]["q50"],
            "Quantile q50 evaluated by quantile-width segment",
            extra={
                "validation": {"uncertainty_segment": seg["validation"], "quantile_width": seg["width"]["validation"]},
                "test": {"uncertainty_segment": seg["test"], "quantile_width": seg["width"]["test"]},
            },
        )

        # PP-L7 segment-specific model refits.
        for model_kind, exp_id in [("huber", "PP-L7-H"), ("catboost", "PP-L7-CB")]:
            pred_by_split = {}
            for split_name, eval_frame in [("validation", scope.val), ("test", scope.test)]:
                pred_by_split[split_name] = np.full(len(eval_frame), np.nan)
            for segment_name in ["low", "mid", "high"]:
                train_mask = seg["train"] == segment_name
                if int(train_mask.sum()) < 50:
                    fallback = base_preds[scope.scope]["huber" if model_kind == "huber" else "catboost"]
                    for split_name in ["validation", "test"]:
                        pred_by_split[split_name][seg[split_name] == segment_name] = fallback[split_name][seg[split_name] == segment_name]
                    continue
                sub_scope = ScopeData(scope.scope, scope.features, scope.train.loc[train_mask].reset_index(drop=True), scope.val, scope.test, scope.numeric_features)
                if model_kind == "huber":
                    _, sub_pred = train_huber(sub_scope)
                else:
                    _, sub_pred = train_catboost(sub_scope)
                for split_name in ["validation", "test"]:
                    pred_by_split[split_name][seg[split_name] == segment_name] = sub_pred[split_name][seg[split_name] == segment_name]
            add_candidate(exp_store, exp_id, f"{exp_id}_{scope.scope}_segment_{model_kind}_refit", scope, pred_by_split, "separate model by quantile-width segment")

        hcb_pred = {}
        for split_name in ["validation", "test"]:
            hcb_pred[split_name] = base_preds[scope.scope]["huber"][split_name].copy()
            hcb_pred[split_name][seg[split_name] == "high"] = base_preds[scope.scope]["huber_catboost_residual"][split_name][seg[split_name] == "high"]
        add_candidate(exp_store, "PP-L7-HCB", f"PP-L7_HCB_{scope.scope}_segment_huber_catboost", scope, hcb_pred, "segment Huber baseline with high-risk CatBoost residual")

        # PP-L8: Quantile -> Huber -> CatBoost.
        enriched_features = list(dict.fromkeys(scope.features + ["q10_log", "q50_log", "q90_log", "quantile_width", "price_range_ratio"]))
        train_enriched = scope.train.copy()
        val_enriched = scope.val.copy()
        test_enriched = scope.test.copy()
        for frame, split_name in [(train_enriched, "train"), (val_enriched, "validation"), (test_enriched, "test")]:
            frame["q10_log"] = quantiles[scope.scope]["q10"][split_name]
            frame["q50_log"] = quantiles[scope.scope]["q50"][split_name]
            frame["q90_log"] = quantiles[scope.scope]["q90"][split_name]
            frame["quantile_width"] = seg["width"][split_name]
            frame["price_range_ratio"] = seg["price_range_ratio"][split_name]
        seq_scope = ScopeData(scope.scope, enriched_features, train_enriched, val_enriched, test_enriched, scope.numeric_features + ["q10_log", "q50_log", "q90_log", "quantile_width", "price_range_ratio"])
        _, seq_huber = train_huber(seq_scope)
        seq_oof = oof_huber(seq_scope)
        seq_residual = seq_scope.train["ln_price_krw"].to_numpy() - seq_oof
        _, seq_residual_pred = train_catboost(seq_scope, target=seq_residual, params={"iterations": 220, "depth": 5})
        seq_pred = {split: seq_huber[split] + seq_residual_pred[split] for split in ["validation", "test"]}
        add_candidate(exp_store, "PP-L8", f"PP-L8_{scope.scope}_quantile_features_huber_catboost_residual", scope, seq_pred, "Quantile price range features feed Huber, then CatBoost residual")

        # PP-L9: Huber -> Quantile residual -> CatBoost remaining residual.
        huber_train_resid = scope.train["ln_price_krw"].to_numpy() - oof_df[oof_df["scope"].eq(scope.scope)]["huber_oof_pred_log"].to_numpy()
        residual_scope = ScopeData(scope.scope, scope.features, scope.train, scope.val, scope.test, scope.numeric_features)
        q_res = quantile_preds(residual_scope, target=huber_train_resid)
        remaining = huber_train_resid - q_res["q50"]["train"]
        residual_width = q_res["q90"]["validation"] - q_res["q10"]["validation"]
        r_low, r_high = np.quantile(residual_width, [0.33, 0.66])
        _, rem_pred = train_catboost(scope, target=remaining, params={"iterations": 220, "depth": 5})
        pp_l9_pred = {
            "validation": base_preds[scope.scope]["huber"]["validation"] + q_res["q50"]["validation"] + rem_pred["validation"],
            "test": base_preds[scope.scope]["huber"]["test"] + q_res["q50"]["test"] + rem_pred["test"],
        }
        add_candidate(exp_store, "PP-L9", f"PP-L9_{scope.scope}_huber_quantile_residual_catboost_remaining", scope, pp_l9_pred, "Huber residual range is modeled by Quantile, remaining residual by CatBoost")
        exp_store["PP-L9"]["segments"].append({
            "experiment_id": "PP-L9",
            "scope": scope.scope,
            "segment_rule": "validation_residual_width_33_66",
            "low_cut": float(r_low),
            "high_cut": float(r_high),
            "price_range_ratio_low_cut": float("nan"),
            "price_range_ratio_high_cut": float("nan"),
        })

    base_config = {
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "feature_columns": feature_columns,
        "model_manifest": model_manifest,
        "metric_policy": {
            "primary": "MdAPE",
            "secondary": ["MAPE", "p95_APE", "RMSE_log", "Within_30", "Within_50"],
            "adoption_rule": "MdAPE must not worsen materially even when MAPE improves",
        },
    }
    for exp_id in EXPERIMENTS:
        store = exp_store[exp_id]
        complexity = store["complexity"] or [{
            "experiment_id": exp_id,
            "model_stage_count": 1 if exp_id in ["PP-L1", "PP-L2", "PP-L7-0"] else 2,
            "segment_count": 3 if exp_id in ["PP-L4", "PP-L5", "PP-L7-0", "PP-L7-H", "PP-L7-CB", "PP-L7-HCB", "PP-L8", "PP-L9"] else 0,
            "inference_model_calls": 1 if exp_id in ["PP-L1", "PP-L2"] else 2,
            "notes": "Complexity is estimated from the experiment design.",
        }]
        write_experiment(
            exp_id,
            {**base_config, "experiment_id": exp_id, "title": EXPERIMENTS[exp_id]["title"]},
            store["metrics"],
            store["predictions"],
            oof_df,
            residual_df,
            store["segments"],
            complexity,
            store["calibration"],
            store["routing"],
            store["seed_stats"],
        )

    summary_rows = []
    for exp_id in EXPERIMENTS:
        metrics_path = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"] / "outputs" / "metrics.csv"
        df = pd.read_csv(metrics_path)
        best = df[df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(1)
        if not best.empty:
            row = best.iloc[0].to_dict()
            row["experiment_id"] = exp_id
            row["folder"] = str((BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]).relative_to(REPO))
            summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary_path = BASE_EXP_DIR / "PP-L_summary_metrics.csv"
    summary.to_csv(summary_path, index=False)
    report_rows = []
    for exp_id, info in EXPERIMENTS.items():
        df = pd.read_csv(BASE_EXP_DIR / info["slug"] / "outputs" / "metrics.csv")
        for scope in ["warm", "cold"]:
            scoped = df[(df["split"].eq("validation")) & (df["scope"].eq(scope))].sort_values(["MdAPE", "MAPE", "p95_APE"])
            if scoped.empty:
                continue
            best = scoped.iloc[0].to_dict()
            baseline_name = "B0_Warm_Huber" if scope == "warm" else "B1_Cold_CatBoost"
            baseline = scoped[scoped["candidate"].eq(baseline_name)]
            if not baseline.empty:
                base = baseline.iloc[0]
                best["MdAPE_delta_vs_baseline"] = float(best["MdAPE"] - base["MdAPE"])
                best["MAPE_delta_vs_baseline"] = float(best["MAPE"] - base["MAPE"])
                best["p95_delta_vs_baseline"] = float(best["p95_APE"] - base["p95_APE"])
            else:
                best["MdAPE_delta_vs_baseline"] = float("nan")
                best["MAPE_delta_vs_baseline"] = float("nan")
                best["p95_delta_vs_baseline"] = float("nan")
            best["experiment_id"] = exp_id
            best["title"] = info["title"]
            best["folder"] = str((BASE_EXP_DIR / info["slug"]).relative_to(REPO))
            report_rows.append(best)
    report_df = pd.DataFrame(report_rows).sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    report_csv = BASE_EXP_DIR / "PP-L_summary_by_scope.csv"
    report_df.to_csv(report_csv, index=False)
    report_md = BASE_EXP_DIR / "PP-L_summary_report.md"
    report_html = BASE_EXP_DIR / "PP-L_summary_report.html"
    md_lines = [
        "# PP-L Huber / Quantile / CatBoost 후처리 실험 종합 요약",
        "",
        f"- 실행 시각: `{datetime.now().isoformat(timespec='seconds')}`",
        "- 목적: MdAPE를 유지하거나 개선하면서 MAPE와 p95_APE를 낮추는 조합을 검증",
        "- 기준 모델: Warm `Huber`, Cold `CatBoost`",
        "- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`",
        "- 판단 기준: validation 우선, test는 최종 확인 보조 자료",
        "",
        "## Scope별 Validation Best",
        "",
        "| scope | 실험 | 후보 | MdAPE | MAPE | p95_APE | MdAPE delta | MAPE delta | p95 delta |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report_df.itertuples():
        md_lines.append(
            f"| `{row.scope}` | `{row.experiment_id}` | `{row.candidate}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | "
            f"`{row.p95_APE:.4f}` | `{row.MdAPE_delta_vs_baseline:.4f}` | `{row.MAPE_delta_vs_baseline:.4f}` | `{row.p95_delta_vs_baseline:.4f}` |"
        )
    md_lines += [
        "",
        "## 1차 판단",
        "",
        "- Warm에서는 `PP-L8 Quantile -> Huber -> CatBoost`와 `PP-L9 Huber -> Quantile residual -> CatBoost`가 기준 대비 MdAPE, MAPE, p95_APE를 함께 낮춘 후보로 나타났다.",
        "- Cold에서는 `PP-L1`의 저가 가중/MAE/Quantile 계열 CatBoost와 `PP-L6`의 Quantile q50/가중 앙상블이 MAPE 완화 후보로 보인다.",
        "- Cold `PP-L9`는 기준 대비 MAPE와 MdAPE가 악화되어 보류 후보로 기록한다.",
        "- Huber fold 일부에서 수렴 경고가 발생했으므로 Warm 후보 확정 전 max_iter/수렴 상태 재확인이 필요하다.",
        "",
        "## 산출물",
        "",
        f"- 전체 best CSV: `{summary_path.relative_to(REPO)}`",
        f"- scope별 summary CSV: `{report_csv.relative_to(REPO)}`",
        "- 각 실험 폴더의 `reports/result_report.html`에서 후보별 상세 결과와 통계 검증을 확인한다.",
        "",
    ]
    report_md.write_text("\n".join(md_lines), encoding="utf-8")
    report_html.write_text(
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>PP-L Summary</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}"
        "table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #d8dee4;padding:7px;text-align:left}"
        "th{background:#eef2f7}code{background:#f3f4f6;padding:2px 4px;border-radius:4px}</style></head><body>"
        "<h1>PP-L Huber / Quantile / CatBoost 후처리 실험 종합 요약</h1>"
        "<p>Validation 기준 scope별 best와 기준 모델 대비 delta를 정리했다.</p>"
        + report_df.to_html(index=False, escape=True)
        + "<h2>1차 판단</h2><ul>"
        "<li>Warm에서는 PP-L8과 PP-L9가 기준 대비 대표오차와 평균오차를 함께 낮춘 후보로 나타났다.</li>"
        "<li>Cold에서는 PP-L1, PP-L6 계열이 MAPE 완화 후보이며 PP-L9는 보류 후보로 기록한다.</li>"
        "<li>Huber 수렴 경고가 있어 Warm 최종 확정 전 수렴 재확인이 필요하다.</li>"
        "</ul></body></html>",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": str(summary_path.relative_to(REPO)),
        "summary_report": str(report_md.relative_to(REPO)),
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
