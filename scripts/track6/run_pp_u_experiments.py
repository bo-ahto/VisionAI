#!/usr/bin/env python3
"""Run Track6 PP-U Warm/Cold feature swap and refinement experiments."""
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
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    BASE_NUMERIC,
    GENERATED,
    REPO,
    SEED,
    artifact_features,
    load_scope,
    metrics,
)


EXTRA_NUMERIC = ["artist_works_log", "artist_works_count_train"]
NUMERIC_FEATURES = set(BASE_NUMERIC + EXTRA_NUMERIC)


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def build_experiments() -> dict[str, dict[str, Any]]:
    features = artifact_features()
    warm_base = features["warm"]
    cold_catboost_base = features["cold_catboost"]
    cold_lightgbm_base = features["cold_lightgbm"]

    warm_artist_size = ["artist_key", "width_cm", "height_cm", "area_cm2", "log_area"]
    warm_artist_size_aspect = warm_artist_size + ["aspect_ratio", "is_extreme_aspect_ratio"]
    warm_artist_size_depth = warm_artist_size + ["depth_cm", "has_depth", "is_3d_candidate"]
    warm_artist_size_material = warm_artist_size + ["medium_category", "support_category", "medium_support_bucket"]
    warm_artist_size_works = warm_artist_size + ["artist_works_log"]
    warm_artist_size_buckets = warm_artist_size + ["size_bucket", "shape_bucket", "support_size_bucket", "medium_shape_bucket"]
    warm_full_plus_generated = unique(warm_base + ["artist_works_log", "size_bucket", "shape_bucket", "support_size_bucket", "medium_shape_bucket", "is_large_2d", "is_large_3d"])

    cold_raw = [
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "has_depth",
        "is_3d_candidate",
        "medium_category",
        "support_category",
    ]
    cold_support_shape = unique(cold_raw + ["size_bucket", "shape_bucket", "support_size_bucket", "medium_shape_bucket"])
    cold_generated_all = unique(cold_raw + ["medium_support_bucket", "is_extreme_aspect_ratio"] + GENERATED)
    cold_raw_material_only = unique(cold_raw + ["medium_support_bucket", "is_extreme_aspect_ratio"])
    cold_medium_size_combo = unique(cold_raw + ["size_bucket", "medium_size_bucket", "medium_shape_bucket"])
    cold_depth_shape_combo = unique([
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "aspect_ratio",
        "has_depth",
        "is_3d_candidate",
        "shape_bucket",
        "is_large_2d",
        "is_large_3d",
    ])

    warm_candidates = [
        ("baseline_base_existing_combo", "기준 피처셋", warm_base, "현재 Warm Huber final artifact와 같은 피처셋"),
        ("artist_size_only", "작가+크기 핵심축만 유지", warm_artist_size, "기존 group-drop에서 핵심으로 확인된 작가와 크기만 남겼을 때 노이즈가 줄어드는지 확인"),
        ("artist_size_aspect", "작가+크기+형태", warm_artist_size_aspect, "형태/aspect가 Warm에서 약한 보조 신호인지 재확인"),
        ("artist_size_depth", "작가+크기+깊이/입체", warm_artist_size_depth, "depth/3D가 Warm에서는 독립 설명력이 약했는지 재확인"),
        ("artist_size_material", "작가+크기+재료/지지체", warm_artist_size_material, "재료/지지체 조합이 Warm에서 노이즈인지 보조 신호인지 확인"),
        ("artist_size_works", "작가+크기+작가 학습량", warm_artist_size_works, "artist_works_log가 p95 안정성 보조 피처로 작동하는지 확인"),
        ("artist_size_generated_buckets", "작가+크기+생성 bucket", warm_artist_size_buckets, "size/shape/support bucket을 쓰면 선형 Huber가 구간 효과를 더 잘 반영하는지 확인"),
        ("full_plus_generated_buckets", "기준 피처셋+생성 bucket", warm_full_plus_generated, "기준 피처셋에 생성 bucket을 추가해 구간 정보를 더 넣는 것이 도움이 되는지 확인"),
    ]

    cold_candidates = [
        ("baseline_base_support_size", "LightGBM 기준 support-size 피처셋", cold_lightgbm_base, "현재 Cold LightGBM final artifact와 같은 피처셋"),
        ("catboost_swap_medium_shape", "CatBoost 기준 medium-shape 피처셋 교환", cold_catboost_base, "LightGBM에도 CatBoost형 재료+형태 조합을 넣으면 개선되는지 확인"),
        ("support_shape_combo", "support-size + medium-shape 결합", cold_support_shape, "두 Cold 모델의 강한 bucket을 함께 쓰면 상호 보완되는지 확인"),
        ("generated_all_combo", "전체 생성 bucket 확장", cold_generated_all, "size/shape/material/support 관련 생성 bucket을 모두 넣었을 때 과적합 없이 개선되는지 확인"),
        ("raw_material_no_bucket", "원본 크기+재료 중심", cold_raw_material_only, "bucket 없이 원본 피처만으로 모델이 충분히 구간을 학습하는지 확인"),
        ("medium_size_combo", "medium-size 조합", cold_medium_size_combo, "재료와 크기 조합이 Cold 가격대를 더 잘 나누는지 확인"),
        ("depth_shape_combo", "depth-shape 조합", cold_depth_shape_combo, "크기+깊이+형태 조합만으로 2D/3D 및 형태 효과가 설명되는지 확인"),
    ]

    cold_catboost_candidates = [
        ("baseline_base_medium_shape", "CatBoost 기준 medium-shape 피처셋", cold_catboost_base, "현재 Cold CatBoost final artifact와 같은 피처셋"),
        ("lightgbm_swap_support_size", "LightGBM 기준 support-size 피처셋 교환", cold_lightgbm_base, "CatBoost에도 LightGBM형 support-size 구간을 넣으면 개선되는지 확인"),
        ("support_shape_combo", "support-size + medium-shape 결합", cold_support_shape, "CatBoost 대칭 트리가 두 bucket 조합을 함께 나눌 수 있는지 확인"),
        ("generated_all_combo", "전체 생성 bucket 확장", cold_generated_all, "생성 bucket을 모두 넣었을 때 CatBoost가 유효한 조합만 고르는지 확인"),
        ("raw_material_no_bucket", "원본 크기+재료 중심", cold_raw_material_only, "명시 bucket 없이 CatBoost split만으로 조합을 찾는지 확인"),
        ("medium_size_combo", "medium-size 조합", cold_medium_size_combo, "재료와 크기 조합이 medium-shape보다 나은지 확인"),
        ("depth_shape_combo", "depth-shape 조합", cold_depth_shape_combo, "CatBoost에서 depth/shape interaction만 강조했을 때 tail이 줄어드는지 확인"),
    ]

    return {
        "PP-U1": {
            "slug": "PP-U1_warm_huber_feature_swap",
            "title": "Warm Huber 피처 교환/축소/확장 비교",
            "scope": "warm",
            "model": "huber",
            "baseline_candidate": "baseline_base_existing_combo",
            "candidates": warm_candidates,
        },
        "PP-U2": {
            "slug": "PP-U2_warm_catboost_feature_swap",
            "title": "Warm CatBoost 피처 교환/축소/확장 비교",
            "scope": "warm",
            "model": "catboost",
            "baseline_candidate": "baseline_base_existing_combo",
            "candidates": warm_candidates,
        },
        "PP-U3": {
            "slug": "PP-U3_cold_lightgbm_feature_swap",
            "title": "Cold LightGBM 피처 교환/확장 비교",
            "scope": "cold",
            "model": "lightgbm",
            "baseline_candidate": "baseline_base_support_size",
            "candidates": cold_candidates,
        },
        "PP-U4": {
            "slug": "PP-U4_cold_catboost_feature_swap",
            "title": "Cold CatBoost 피처 교환/확장 비교",
            "scope": "cold",
            "model": "catboost",
            "baseline_candidate": "baseline_base_medium_shape",
            "candidates": cold_catboost_candidates,
        },
    }


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [col for col in features if col in NUMERIC_FEATURES]
    categorical = [col for col in features if col not in numeric]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def huber_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
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


def lightgbm_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="regression",
            n_estimators=350,
            learning_rate=0.04,
            num_leaves=31,
            min_child_samples=40,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def cat_ready(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame[features].copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in categorical:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out


def cat_indices(features: list[str]) -> list[int]:
    numeric, _ = split_types(features)
    return [idx for idx, col in enumerate(features) if col not in numeric]


def fit_predict(model_name: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    if model_name == "huber":
        model = huber_model(features)
        model.fit(train[features], y)
        return {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    if model_name == "lightgbm":
        model = lightgbm_model(features)
        model.fit(train[features], y)
        return {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
    return {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def prediction_frame(
    exp_id: str,
    candidate: str,
    scope: str,
    model: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    feature_strategy: str,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "model": model,
        "split": split,
        "feature_strategy": feature_strategy,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def add_baseline_deltas(metrics_df: pd.DataFrame, baseline_candidate: str) -> pd.DataFrame:
    out = metrics_df.copy()
    for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
        out[f"delta_{metric}_vs_baseline"] = np.nan
    for split in out["split"].unique():
        mask = out["split"].eq(split)
        base = out[mask & out["candidate"].eq(baseline_candidate)]
        if base.empty:
            continue
        base_row = base.iloc[0]
        for metric in ["MdAPE", "MAPE", "p95_APE", "RMSE_log"]:
            out.loc[mask, f"delta_{metric}_vs_baseline"] = out.loc[mask, metric] - float(base_row[metric])
    return out


def render_report(exp_id: str, info: dict[str, Any], metrics_df: pd.DataFrame, feature_map: pd.DataFrame) -> tuple[str, str]:
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    baseline = info["baseline_candidate"]
    val_best = val.iloc[0]
    test_best = test.iloc[0]

    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "## 실험 계획",
        "",
        "- 목적: 기존 실험에서 확인된 피처 영향도를 바탕으로 피처셋을 교환, 축소, 확장했을 때 성능이 어떻게 바뀌는지 확인한다.",
        f"- 대상: `{info['scope']}` 데이터, `{info['model']}` 모델.",
        "- 통제 기준: 데이터 split, target(`ln_price_krw`), 모델 설정, 평가 지표는 고정하고 피처셋만 바꾼다.",
        "- 선택 기준: validation에서 후보를 고르고 test는 선택된 후보의 재현성 확인으로만 사용한다.",
        "- 기대 결과: 어떤 피처 조합이 모델 특성에 맞는지 확인하고, 후속 모델 조합/보정 실험의 입력 후보를 갱신한다.",
        "",
        "## 후보 피처셋",
        "",
        "| 후보 | 전략 | 피처 수 | 가설 |",
        "|---|---|---:|---|",
    ]
    for row in feature_map.itertuples():
        lines.append(f"| `{row.candidate}` | {row.feature_strategy} | {row.n_features} | {row.hypothesis} |")

    lines += [
        "",
        "## Validation 결과",
        "",
        "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {row.delta_MdAPE_vs_baseline:+.4f} |"
        )

    lines += [
        "",
        "## Test 확인 결과",
        "",
        "| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | baseline 대비 MdAPE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in test.itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {row.delta_MdAPE_vs_baseline:+.4f} |"
        )

    lines += [
        "",
        "## 코멘터리",
        "",
        f"- validation 기준 1위 후보는 `{val_best.candidate}`이고, 기준 후보 `{baseline}` 대비 MdAPE 변화는 `{val_best.delta_MdAPE_vs_baseline:+.4f}`이다.",
        f"- test 기준 1위 후보는 `{test_best.candidate}`이고, 기준 후보 `{baseline}` 대비 MdAPE 변화는 `{test_best.delta_MdAPE_vs_baseline:+.4f}`이다.",
        "- validation과 test의 1위가 다르면 즉시 교체하지 않고, 후속 조합/보정 후보로만 둔다.",
        "- 피처 교환 실험은 모델을 바꾸는 실험이 아니라, 같은 모델에서 어떤 입력 정보 구조가 더 맞는지 확인하는 사전 검증이다.",
    ]
    md = "\n".join(lines) + "\n"

    style = """
body{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}
table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}
th,td{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}
th{background:#eef2f7}
code{background:#f3f4f6;padding:2px 4px;border-radius:4px}
.note{background:#f8fafc;border:1px solid #d8dee4;padding:12px;margin:12px 0}
"""
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title><style>{style}</style></head>
<body>
<h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1>
<div class="note">
<p><b>목적</b>: 모델 설정은 고정하고 피처셋만 바꿔 Warm/Cold 모델별 입력 피처 구조의 적합성을 비교한다.</p>
<p><b>선택 기준</b>: validation 기준으로 후보를 고르고 test는 재현성 확인으로만 사용한다.</p>
</div>
<h2>후보 피처셋</h2>{feature_map.to_html(index=False, escape=True)}
<h2>Metrics</h2>{metrics_df.sort_values(['split','MdAPE','MAPE','p95_APE']).to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_experiment(
    exp_id: str,
    info: dict[str, Any],
    metrics_df: pd.DataFrame,
    predictions: list[pd.DataFrame],
    feature_map: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    pred_df = pd.concat(predictions, ignore_index=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    feature_map.to_csv(exp_dir / "outputs" / "feature_set_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    split_manifest = {
        "split_root": "data/track6_split",
        "train": "track6_train",
        "validation": f"track6_val_{info['scope']}",
        "test": f"track6_test_{info['scope']}",
    }
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps(split_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(exp_id, info, metrics_df, feature_map)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def run_experiment(exp_id: str, info: dict[str, Any]) -> pd.DataFrame:
    candidates = info["candidates"]
    all_features = unique([feature for _candidate, _strategy, features, _hypothesis in candidates for feature in features])
    train, val, test = load_scope(info["scope"], all_features)
    train = normalize(train, all_features)
    val = normalize(val, all_features)
    test = normalize(test, all_features)

    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    feature_map_rows: list[dict[str, Any]] = []

    for candidate, strategy, features, hypothesis in candidates:
        pred = fit_predict(info["model"], train, val, test, features)
        feature_map_rows.append({
            "experiment_id": exp_id,
            "candidate": candidate,
            "feature_strategy": strategy,
            "hypothesis": hypothesis,
            "n_features": len(features),
            "features": ", ".join(features),
        })
        for split, frame in [("validation", val), ("test", test)]:
            pred_log = pred[split]
            rows.append({
                "experiment_id": exp_id,
                "candidate": candidate,
                "scope": info["scope"],
                "model": info["model"],
                "split": split,
                "feature_strategy": strategy,
                "hypothesis": hypothesis,
                "n_features": len(features),
                "features": ", ".join(features),
                **metrics(frame, pred_log),
            })
            preds.append(prediction_frame(exp_id, candidate, info["scope"], info["model"], split, frame, pred_log, strategy))

    metrics_df = add_baseline_deltas(pd.DataFrame(rows), info["baseline_candidate"])
    feature_map = pd.DataFrame(feature_map_rows)
    config = {
        "experiment_id": exp_id,
        "title": info["title"],
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "scope": info["scope"],
        "model": info["model"],
        "baseline_candidate": info["baseline_candidate"],
        "feature_columns": {row["candidate"]: row["features"].split(", ") for row in feature_map_rows},
        "model_manifest": {
            "model": info["model"],
            "target": "ln_price_krw",
            "numeric_features": sorted(NUMERIC_FEATURES),
            "source_artifact_manifest": "data/track6/artifacts/track6_artifact_manifest.json",
        },
    }
    write_experiment(exp_id, info, metrics_df, preds, feature_map, config)
    return metrics_df


def main() -> None:
    start = time.time()
    experiments = build_experiments()
    all_rows: list[pd.DataFrame] = []
    for exp_id, info in experiments.items():
        all_rows.append(run_experiment(exp_id, info))
    summary = pd.concat(all_rows, ignore_index=True)
    summary.to_csv(BASE_EXP_DIR / "PP-U_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-U_summary_metrics.csv",
        "experiments": {exp_id: str((BASE_EXP_DIR / info["slug"]).relative_to(REPO)) for exp_id, info in experiments.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
