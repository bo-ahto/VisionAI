#!/usr/bin/env python3
"""Run PP-L10 Warm PP-L8 sequential structure with feature variants.

The original PP-L8 used:
  Quantile predictions -> Huber centerline -> CatBoost residual correction

PP-L10 keeps that model order fixed and changes only the Warm feature set.
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import BASE_EXP_DIR, GENERATED, REPO, SEED, artifact_features, metrics  # noqa: E402
from run_pp_z_warm_coldstyle_extension_experiments import (  # noqa: E402
    EXTERNAL_ALL,
    META_ALL,
    NUMERIC_FEATURES,
    SEARCH_ALL,
    load_warm_full,
    unique,
)


EXPERIMENT_ID = "PP-L10"
SLUG = "PP-L10_warm_l8_feature_variant_sequential"
TITLE = "Warm PP-L8 순차 구조 피처 변형 비교"
SUMMARY_PATH = BASE_EXP_DIR / "PP-L10_warm_l8_feature_variant_summary_metrics.csv"

SEQUENTIAL_NUMERIC = {
    "q10_log",
    "q50_log",
    "q90_log",
    "quantile_width",
    "price_range_ratio",
}


def feature_candidates() -> list[tuple[str, str, list[str], str]]:
    warm_base = artifact_features()["warm"]
    artist_size = ["artist_key", "width_cm", "height_cm", "area_cm2", "log_area"]
    artist_size_works = artist_size + ["artist_works_log", "artist_works_count_train"]
    generated = [
        "artist_works_log",
        "artist_works_count_train",
        "size_bucket",
        "shape_bucket",
        "support_size_bucket",
        "medium_shape_bucket",
        "is_large_2d",
        "is_large_3d",
    ]
    return [
        (
            "base_existing_combo",
            "Warm 기준 피처셋",
            warm_base,
            "기존 PP-L8과 같은 기준 피처셋으로 재현 기준을 만든다.",
        ),
        (
            "artist_size_only",
            "작가+크기 핵심축",
            artist_size,
            "Warm 핵심축만 남기면 순차 구조에서 노이즈가 줄어드는지 확인한다.",
        ),
        (
            "artist_size_works",
            "작가+크기+작가 학습량",
            artist_size_works,
            "작가별 학습량을 Huber 중심선과 CatBoost residual에 함께 제공한다.",
        ),
        (
            "full_plus_generated_buckets",
            "기준 피처셋+생성 bucket",
            unique(warm_base + generated),
            "PP-U1에서 개선 신호가 있던 생성 bucket을 PP-L8 구조에 넣는다.",
        ),
        (
            "warm_base_search_all",
            "기준 피처셋+검색 전체",
            unique(warm_base + ["artist_works_log", "artist_works_count_train"] + META_ALL + SEARCH_ALL),
            "PP-Z1에서 Huber baseline 개선 신호가 있던 검색 피처를 순차 구조에 넣는다.",
        ),
        (
            "warm_base_artist_meta_all",
            "기준 피처셋+작가 메타 전체",
            unique(warm_base + ["artist_works_log", "artist_works_count_train"] + META_ALL),
            "작가 기준선을 보완하는 메타 피처가 residual 보정까지 유효한지 확인한다.",
        ),
        (
            "warm_base_meta_external_search_all",
            "기준 피처셋+작가 메타+전시/갤러리+검색 전체",
            unique(warm_base + ["artist_works_log", "artist_works_count_train"] + META_ALL + EXTERNAL_ALL + SEARCH_ALL),
            "Cold식 확장 피처 전체를 PP-L8 순차 구조에 넣었을 때 개선되는지 확인한다.",
        ),
    ]


def numeric_for(features: list[str]) -> set[str]:
    return {feature for feature in features if feature in NUMERIC_FEATURES or feature in SEQUENTIAL_NUMERIC}


def normalize_frame(frame: pd.DataFrame, features: list[str], numeric: set[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in features:
        if col in numeric:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def onehot_model(features: list[str], numeric: set[str]) -> Pipeline:
    numeric_cols = [col for col in features if col in numeric]
    categorical_cols = [col for col in features if col not in numeric]
    transformers = []
    if numeric_cols:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_cols))
    if categorical_cols:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical_cols))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)),
    ])


def cat_ready(frame: pd.DataFrame, features: list[str], numeric: set[str]) -> pd.DataFrame:
    out = frame[features].copy()
    for col in features:
        if col in numeric:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = out[col].astype(str).fillna("__MISSING__")
    return out


def cat_indices(features: list[str], numeric: set[str]) -> list[int]:
    return [idx for idx, col in enumerate(features) if col not in numeric]


def cat_model(loss: str = "RMSE", iterations: int = 220, depth: int = 6) -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function=loss,
        iterations=iterations,
        learning_rate=0.04,
        depth=depth,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    return metrics(frame[["_track6_row_id", "ln_price_krw", "price_krw"]], pred_log)


def prediction_frame(
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    model_stage: str,
    feature_strategy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXPERIMENT_ID,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "model_stage": model_stage,
        "feature_strategy": feature_strategy,
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


def add_metric(
    rows: list[dict[str, Any]],
    candidate: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    model_stage: str,
    feature_strategy: str,
    n_features: int,
    notes: str,
) -> None:
    rows.append({
        "experiment_id": EXPERIMENT_ID,
        "candidate": candidate,
        "scope": "warm",
        "split": split,
        "model_stage": model_stage,
        "feature_strategy": feature_strategy,
        "n_features": n_features,
        "notes": notes,
        **metric_values(frame, pred_log),
    })


def fit_huber(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], numeric: set[str]) -> dict[str, np.ndarray]:
    train_n = normalize_frame(train, features, numeric)
    val_n = normalize_frame(val, features, numeric)
    test_n = normalize_frame(test, features, numeric)
    model = onehot_model(features, numeric)
    model.fit(train_n[features], train_n["ln_price_krw"].to_numpy(dtype=float))
    return {
        "train": np.asarray(model.predict(train_n[features]), dtype=float),
        "validation": np.asarray(model.predict(val_n[features]), dtype=float),
        "test": np.asarray(model.predict(test_n[features]), dtype=float),
    }


def oof_huber(train: pd.DataFrame, features: list[str], numeric: set[str], folds: int = 3) -> np.ndarray:
    train_n = normalize_frame(train, features, numeric)
    pred = np.full(len(train_n), np.nan)
    kf = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    for train_idx, holdout_idx in kf.split(train_n):
        model = onehot_model(features, numeric)
        model.fit(train_n.iloc[train_idx][features], train_n.iloc[train_idx]["ln_price_krw"].to_numpy(dtype=float))
        pred[holdout_idx] = model.predict(train_n.iloc[holdout_idx][features])
    return pred


def fit_catboost(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    numeric: set[str],
    target: np.ndarray,
    *,
    loss: str = "RMSE",
    iterations: int = 220,
    depth: int = 6,
) -> dict[str, np.ndarray]:
    train_n = normalize_frame(train, features, numeric)
    val_n = normalize_frame(val, features, numeric)
    test_n = normalize_frame(test, features, numeric)
    model = cat_model(loss=loss, iterations=iterations, depth=depth)
    model.fit(cat_ready(train_n, features, numeric), target, cat_features=cat_indices(features, numeric))
    return {
        "train": np.asarray(model.predict(cat_ready(train_n, features, numeric)), dtype=float),
        "validation": np.asarray(model.predict(cat_ready(val_n, features, numeric)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test_n, features, numeric)), dtype=float),
    }


def quantile_predictions(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str], numeric: set[str]) -> dict[str, dict[str, np.ndarray]]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    out: dict[str, dict[str, np.ndarray]] = {}
    for label, alpha in [("q10", 0.10), ("q50", 0.50), ("q90", 0.90)]:
        out[label] = fit_catboost(
            train,
            val,
            test,
            features,
            numeric,
            y,
            loss=f"Quantile:alpha={alpha}",
            iterations=220,
            depth=6,
        )
    return out


def add_quantile_features(frame: pd.DataFrame, q: dict[str, dict[str, np.ndarray]], split: str) -> pd.DataFrame:
    out = frame.copy()
    q10 = np.minimum(q["q10"][split], q["q90"][split])
    q90 = np.maximum(q["q10"][split], q["q90"][split])
    q50 = q["q50"][split]
    out["q10_log"] = q10
    out["q50_log"] = q50
    out["q90_log"] = q90
    out["quantile_width"] = q90 - q10
    out["price_range_ratio"] = np.exp(np.clip(out["quantile_width"].to_numpy(dtype=float), -10.0, 10.0))
    return out


def run_candidate(
    name: str,
    strategy: str,
    features: list[str],
    hypothesis: str,
    base_train: pd.DataFrame,
    base_val: pd.DataFrame,
    base_test: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    numeric = numeric_for(features)
    q = quantile_predictions(base_train, base_val, base_test, features, numeric)

    direct_huber = fit_huber(base_train, base_val, base_test, features, numeric)
    q50 = {"validation": q["q50"]["validation"], "test": q["q50"]["test"]}

    train_enriched = add_quantile_features(base_train, q, "train")
    val_enriched = add_quantile_features(base_val, q, "validation")
    test_enriched = add_quantile_features(base_test, q, "test")
    enriched_features = unique(features + ["q10_log", "q50_log", "q90_log", "quantile_width", "price_range_ratio"])
    enriched_numeric = numeric_for(enriched_features)
    seq_huber = fit_huber(train_enriched, val_enriched, test_enriched, enriched_features, enriched_numeric)
    seq_oof = oof_huber(train_enriched, enriched_features, enriched_numeric)
    residual_target = train_enriched["ln_price_krw"].to_numpy(dtype=float) - seq_oof
    residual_pred = fit_catboost(
        train_enriched,
        val_enriched,
        test_enriched,
        enriched_features,
        enriched_numeric,
        residual_target,
        loss="RMSE",
        iterations=220,
        depth=5,
    )
    seq_pred = {
        "validation": seq_huber["validation"] + residual_pred["validation"],
        "test": seq_huber["test"] + residual_pred["test"],
    }

    candidates = [
        (f"huber_direct__{name}", "direct_huber", direct_huber, "피처셋만 바꾼 Huber 단독 기준"),
        (f"quantile_q50__{name}", "quantile_q50", q50, "CatBoost Quantile q50 단독 기준"),
        (f"l8_seq__{name}", "quantile_huber_catboost", seq_pred, "Quantile -> Huber -> CatBoost residual 순차 구조"),
    ]
    for candidate, stage, pred_dict, notes in candidates:
        for split, frame in [("validation", base_val), ("test", base_test)]:
            pred_log = pred_dict[split]
            add_metric(rows, candidate, split, frame, pred_log, stage, strategy, len(features), notes)
            extra = {
                "n_features": len(features),
                "hypothesis": hypothesis,
            }
            if stage in {"quantile_q50", "quantile_huber_catboost"}:
                extra["q10_log"] = q["q10"][split]
                extra["q50_log"] = q["q50"][split]
                extra["q90_log"] = q["q90"][split]
                extra["quantile_width"] = np.maximum(q["q90"][split], q["q10"][split]) - np.minimum(q["q90"][split], q["q10"][split])
            preds.append(prediction_frame(candidate, split, frame, pred_log, stage, strategy, extra))

    feature_map = {
        "candidate_feature_set": name,
        "feature_strategy": strategy,
        "hypothesis": hypothesis,
        "n_features": len(features),
        "features": ", ".join(features),
        "sequential_features": ", ".join(enriched_features),
    }
    return rows, preds, feature_map


def render_report(metrics_df: pd.DataFrame, feature_map: pd.DataFrame) -> tuple[str, str]:
    test_top = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(15)
    val_top = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(15)
    md = f"""# {EXPERIMENT_ID} {TITLE}

## 목적
- 기존 `PP-L8`의 `Quantile -> Huber -> CatBoost residual` 구조를 유지하고 Warm 피처셋만 바꿔 성능을 비교한다.
- `PP-U1`에서 가능성이 있던 생성 bucket, `PP-Z1`에서 가능성이 있던 검색 피처를 같은 순차 구조에 넣어 확인한다.

## Validation Top 15
```csv
{val_top.to_csv(index=False)}```

## Test Top 15
```csv
{test_top.to_csv(index=False)}```

## 피처셋
```csv
{feature_map.to_csv(index=False)}```
"""
    style = "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:28px;color:#17202a}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #d8dee9;padding:7px;text-align:left}th{background:#eef2f7}h1,h2{margin-top:22px}"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXPERIMENT_ID)}</title><style>{style}</style></head>
<body><h1>{html.escape(EXPERIMENT_ID)} {html.escape(TITLE)}</h1>
<h2>Validation Top 15</h2>{val_top.to_html(index=False, escape=True)}
<h2>Test Top 15</h2>{test_top.to_html(index=False, escape=True)}
<h2>Feature Sets</h2>{feature_map.to_html(index=False, escape=True)}</body></html>"""
    return md, html_doc


def main() -> None:
    start = time.time()
    candidates = feature_candidates()
    all_features = unique([feature for _name, _strategy, features, _hypothesis in candidates for feature in features])
    train, val, test = load_warm_full(all_features)
    all_rows: list[dict[str, Any]] = []
    all_preds: list[pd.DataFrame] = []
    feature_maps: list[dict[str, Any]] = []

    for name, strategy, features, hypothesis in candidates:
        rows, preds, feature_map = run_candidate(name, strategy, features, hypothesis, train, val, test)
        all_rows.extend(rows)
        all_preds.extend(preds)
        feature_maps.append(feature_map)
        print(json.dumps({"candidate": name, "rows": len(rows), "elapsed_sec": round(time.time() - start, 3)}, ensure_ascii=False))

    exp_dir = BASE_EXP_DIR / SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    metrics_df = pd.DataFrame(all_rows)
    pred_df = pd.concat(all_preds, ignore_index=True)
    feature_map_df = pd.DataFrame(feature_maps)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    feature_map_df.to_csv(exp_dir / "outputs" / "feature_set_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    config = {
        "experiment_id": EXPERIMENT_ID,
        "title": TITLE,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": SEED,
        "scope": "warm",
        "model_order": "CatBoost Quantile -> Huber -> CatBoost residual",
        "source_reference": "PP-L8",
        "summary_path": str(SUMMARY_PATH.relative_to(REPO)),
        "feature_sets": feature_maps,
    }
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, feature_map_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXPERIMENT_ID} completed\n", encoding="utf-8")
    metrics_df.to_csv(SUMMARY_PATH, index=False)
    print(json.dumps({
        "status": "ok",
        "summary": str(SUMMARY_PATH.relative_to(REPO)),
        "rows": int(len(metrics_df)),
        "runtime_sec": round(time.time() - start, 3),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
