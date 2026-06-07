#!/usr/bin/env python3
"""Run PP-QR1 Cold quantile family alpha-grid comparison.

This experiment compares three quantile families on the same Cold split:
- LightGBM quantile loss
- CatBoost quantile loss
- Linear Quantile Regression

The goal is to separate "quantile level choice" from "model family choice" before
using quantile outputs for MAPE reduction, interval display, or routing.
"""
from __future__ import annotations

import argparse
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
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    BASE_EXP_DIR,
    REPO,
    SEED,
    artifact_features,
    cat_indices,
    cat_ready,
    fit_predict,
    load_scope,
    metrics,
    normalize,
    split_types,
)


EXP_ID = "PP-QR1"
SLUG = "PP-QR1_cold_quantile_regression_alpha_grid"
TITLE = "Cold Quantile Regression 포함 분위수 종류별 비교"
DOC_PATH = REPO / "docs" / "track6" / "experiments" / "pp_qr1_cold_quantile_regression_alpha_grid_summary.md"


def parse_alphas(raw: str) -> list[float]:
    values = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = float(item)
        if not 0.0 < value < 1.0:
            raise ValueError(f"alpha must be between 0 and 1: {value}")
        values.append(value)
    return sorted(dict.fromkeys(values))


def alpha_key(alpha: float) -> str:
    return f"{alpha:.2f}".replace(".", "p")


def alpha_label(alpha: float) -> str:
    return f"q{int(round(alpha * 100)):02d}"


def lgbm_quantile_model(features: list[str], quantile: float, *, n_estimators: int) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            n_estimators=n_estimators,
            learning_rate=0.035,
            num_leaves=31,
            min_child_samples=35,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.2,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def catboost_quantile_model(quantile: float, *, iterations: int) -> CatBoostRegressor:
    return CatBoostRegressor(
        loss_function=f"Quantile:alpha={quantile}",
        iterations=iterations,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=8.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )


def one_hot_encoder() -> OneHotEncoder:
    kwargs: dict[str, Any] = {
        "handle_unknown": "infrequent_if_exist",
        "min_frequency": 20,
        "max_categories": 350,
    }
    try:
        return OneHotEncoder(sparse_output=True, **kwargs)
    except TypeError:
        kwargs.pop("max_categories", None)
        return OneHotEncoder(handle_unknown="ignore", min_frequency=20)


def linear_quantile_model(features: list[str], quantile: float, *, regularization: float) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler(with_mean=False)),
        ]), numeric))
    if categorical:
        transformers.append(("cat", one_hot_encoder(), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers, sparse_threshold=0.3)),
        ("model", QuantileRegressor(quantile=quantile, alpha=regularization, solver="highs")),
    ])


def maybe_sample_train(train: pd.DataFrame, limit: int) -> pd.DataFrame:
    if limit <= 0 or len(train) <= limit:
        return train
    return train.sample(n=limit, random_state=SEED).sort_values("_track6_row_id").reset_index(drop=True)


def prediction_frame(
    candidate: str,
    model_family: str,
    quantile: float | None,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    extra: dict[str, Any] | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "model_family": model_family,
        "quantile": quantile,
        "split": split,
        "policy": policy,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
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
    model_family: str,
    quantile: float | None,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
    policy: str,
    notes: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    row = {
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "scope": "cold",
        "model_family": model_family,
        "quantile": quantile,
        "split": split,
        "policy": policy,
        "notes": notes,
        **metrics(frame, pred_log),
    }
    if extra:
        row.update(extra)
    rows.append(row)


def fit_lgbm_quantiles(
    features: list[str],
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    alphas: list[float],
    *,
    n_estimators: int,
) -> dict[float, dict[str, np.ndarray]]:
    preds: dict[float, dict[str, np.ndarray]] = {}
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for alpha in alphas:
        model = lgbm_quantile_model(features, alpha, n_estimators=n_estimators)
        model.fit(train[features], y)
        preds[alpha] = {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    return preds


def fit_catboost_quantiles(
    features: list[str],
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    alphas: list[float],
    *,
    iterations: int,
) -> dict[float, dict[str, np.ndarray]]:
    preds: dict[float, dict[str, np.ndarray]] = {}
    y = train["ln_price_krw"].to_numpy(dtype=float)
    train_x = cat_ready(train, features)
    val_x = cat_ready(val, features)
    test_x = cat_ready(test, features)
    cats = cat_indices(features)
    for alpha in alphas:
        model = catboost_quantile_model(alpha, iterations=iterations)
        model.fit(train_x, y, cat_features=cats)
        preds[alpha] = {
            "validation": np.asarray(model.predict(val_x), dtype=float),
            "test": np.asarray(model.predict(test_x), dtype=float),
        }
    return preds


def fit_linear_quantiles(
    features: list[str],
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    alphas: list[float],
    *,
    regularization: float,
    train_limit: int,
) -> tuple[dict[float, dict[str, np.ndarray]], int]:
    train_fit = maybe_sample_train(train, train_limit)
    preds: dict[float, dict[str, np.ndarray]] = {}
    y = train_fit["ln_price_krw"].to_numpy(dtype=float)
    for alpha in alphas:
        model = linear_quantile_model(features, alpha, regularization=regularization)
        model.fit(train_fit[features], y)
        preds[alpha] = {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    return preds, len(train_fit)


def range_metrics(
    frame: pd.DataFrame,
    low_log: np.ndarray,
    mid_log: np.ndarray,
    high_log: np.ndarray,
    low_alpha: float,
    high_alpha: float,
) -> dict[str, float]:
    actual = frame["ln_price_krw"].to_numpy(dtype=float)
    low = np.minimum(low_log, high_log)
    high = np.maximum(low_log, high_log)
    width = np.clip(high - low, 0.0, 8.0)
    return {
        "low_quantile": low_alpha,
        "high_quantile": high_alpha,
        "target_coverage": high_alpha - low_alpha,
        "actual_coverage": float(np.mean((actual >= low) & (actual <= high))),
        "median_width_log": float(np.median(width)),
        "median_price_range_ratio": float(np.median(np.exp(width))),
        "mean_width_log": float(np.mean(width)),
        "mid_RMSE_log": metrics(frame, mid_log)["RMSE_log"],
        "mid_MdAPE": metrics(frame, mid_log)["MdAPE"],
        "mid_MAPE": metrics(frame, mid_log)["MAPE"],
        "mid_p95_APE": metrics(frame, mid_log)["p95_APE"],
    }


def add_range_rows(
    rows: list[dict[str, Any]],
    model_family: str,
    split: str,
    frame: pd.DataFrame,
    preds: dict[float, dict[str, np.ndarray]],
    low_alpha: float,
    high_alpha: float,
) -> None:
    if low_alpha not in preds or high_alpha not in preds:
        return
    mid_alpha = 0.5 if 0.5 in preds else min(preds, key=lambda a: abs(a - 0.5))
    low = preds[low_alpha][split]
    mid = preds[mid_alpha][split]
    high = preds[high_alpha][split]
    adjacent = sorted(preds)
    crossings = []
    for left, right in zip(adjacent, adjacent[1:]):
        crossings.append(preds[left][split] > preds[right][split])
    crossing_rate = float(np.mean(np.column_stack(crossings))) if crossings else 0.0
    rows.append({
        "experiment_id": EXP_ID,
        "scope": "cold",
        "model_family": model_family,
        "split": split,
        "range_name": f"{alpha_label(low_alpha)}_{alpha_label(high_alpha)}",
        "mid_quantile": mid_alpha,
        "quantile_crossing_rate": crossing_rate,
        **range_metrics(frame, low, mid, high, low_alpha, high_alpha),
    })


def render_markdown(metrics_df: pd.DataFrame, range_df: pd.DataFrame, config: dict[str, Any]) -> str:
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    q50 = test[np.isclose(test["quantile"].fillna(-1), 0.5)].sort_values(["MdAPE", "MAPE", "p95_APE"])
    best_test = test.iloc[0]
    best_q50 = q50.iloc[0] if not q50.empty else best_test
    range_test = range_df[range_df["split"].eq("test")].sort_values(["actual_coverage", "mid_MdAPE"], ascending=[False, True])

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        "## 1. 실험 목적",
        "",
        "- 기존 Cold Quantile 실험은 LightGBM q10/q50/q90, CatBoost q10/q50/q90 중심으로 진행됨.",
        "- 이번 실험은 선형 Quantile Regression을 포함하여, 분위수 종류별 예측값이 가격 정확도와 가격 범위 산출에 어떤 차이를 만드는지 확인.",
        "- 같은 데이터 분할, 같은 Cold 기준 피처셋, 같은 평가 지표로 비교하여 모델 특성 차이와 분위수 선택 효과를 분리.",
        "",
        "## 2. 고정 조건",
        "",
        f"- 데이터 범위: Cold train/validation/test split.",
        f"- 기준 피처셋: `{config['feature_profile']}`.",
        f"- 사용 피처 수: `{len(config['feature_columns'])}`.",
        f"- 목표값: 실제 가격의 로그값 `ln_price_krw`.",
        "- 평가지표: MdAPE, MAPE, p95_APE, RMSE_log, Within_30, Within_50.",
        "- 점예측 비교: 각 분위수 예측값을 그대로 가격 예측값으로 사용.",
        "- 범위 비교: q10~q90, q05~q95 구간의 실제 포함률과 구간 폭을 계산.",
        "",
        "## 3. 모델별 의미",
        "",
        "- LightGBM Quantile: 트리 리프를 이용해 비선형 구간별 분위수를 학습. Cold처럼 표본이 작고 가격 분포가 긴 경우, 고가/저가 꼬리 구간을 분리해 잡는 데 유리.",
        "- CatBoost Quantile: 대칭 트리 구조로 범주형 조합을 안정적으로 반영. 작가, 매체, 크기 조합이 반복되는 구간에서 보수적인 분위수 예측을 확인하기 좋음.",
        "- 선형 Quantile Regression: pinball loss로 특정 분위수를 직접 맞추는 선형 기준선. 트리 모델의 복잡한 분기 없이 피처 방향성을 확인하는 해석 기준으로 사용.",
        "",
        "## 4. Test 핵심 결과",
        "",
        f"- 전체 후보 중 test MdAPE 최저: `{best_test.candidate}` / MdAPE `{best_test.MdAPE:.4f}`, MAPE `{best_test.MAPE:.4f}`, p95_APE `{best_test.p95_APE:.4f}`.",
        f"- q50 후보 중 test MdAPE 최저: `{best_q50.candidate}` / MdAPE `{best_q50.MdAPE:.4f}`, MAPE `{best_q50.MAPE:.4f}`, p95_APE `{best_q50.p95_APE:.4f}`.",
        "",
        "## 5. Test 상위 후보",
        "",
        "| 후보 | 모델 | 분위수 | MdAPE | MAPE | p95_APE | RMSE_log | Within_50 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in test.head(12).itertuples():
        q = "" if pd.isna(row.quantile) else f"{row.quantile:.2f}"
        lines.append(f"| `{row.candidate}` | {row.model_family} | {q} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} | {row.Within_50:.4f} |")

    lines += [
        "",
        "## 6. q50 중심 비교",
        "",
        "| 후보 | 모델 | MdAPE | MAPE | p95_APE | 해석 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in q50.itertuples():
        if row.model_family == "LightGBM Quantile":
            comment = "중앙값 기준의 비선형 구간 예측. Cold의 일반 오차 기준 후보."
        elif row.model_family == "CatBoost Quantile":
            comment = "범주형 조합을 대칭 트리로 반영한 중앙값 후보."
        else:
            comment = "선형 Quantile Regression 기준선. 복잡한 분기 없이 중앙값을 직접 학습."
        lines.append(f"| `{row.candidate}` | {row.model_family} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {comment} |")

    lines += [
        "",
        "## 7. 가격 범위 후보",
        "",
        "| 모델 | 범위 | 실제 포함률 | 목표 포함률 | 중앙 범위 배율 | q50 MdAPE | q50 MAPE | crossing |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in range_test.itertuples():
        lines.append(
            f"| {row.model_family} | {row.range_name} | {row.actual_coverage:.4f} | {row.target_coverage:.4f} | "
            f"{row.median_price_range_ratio:.3f} | {row.mid_MdAPE:.4f} | {row.mid_MAPE:.4f} | {row.quantile_crossing_rate:.4f} |"
        )

    lines += [
        "",
        "## 8. 방법론 판단",
        "",
        "- MdAPE 최적화에는 q50 또는 q50 근처 분위수가 우선 후보.",
        "- MAPE만 보면 q10/q25처럼 낮은 분위수가 유리해 보일 수 있으나, MdAPE가 크게 악화되므로 대표 가격 후보로는 부적합.",
        "- q10/q25는 점예측 후보보다 하단 가격 또는 보수적 가격 범위 해석에 가깝게 사용.",
        "- q40은 q50 대비 MdAPE 악화가 제한적이면서 MAPE와 p95_APE를 줄여 MAPE 방어형 후속 조합 후보로 볼 수 있음.",
        "- MAPE는 큰 오차에 민감하므로 q40/q50/q60 주변을 비교하여 과대/과소 예측 방향을 확인해야 함.",
        "- q10/q90, q05/q95는 점예측 후보라기보다 가격 범위와 신뢰도 산출용 후보.",
        "- q05~q95도 test 실제 포함률이 목표 90%보다 낮으므로, 서비스 표시 범위로 쓰려면 conformal 보정 또는 segment별 폭 보정이 필요.",
        "- Quantile Regression은 최종 성능 모델이라기보다 선형 기준선과 피처 방향성 점검용으로 활용하는 것이 적합.",
        "",
        "## 9. 산출물",
        "",
        f"- 실험 폴더: `experiments/track6/{SLUG}`.",
        "- `outputs/metrics.csv`: 분위수별 점예측 성능.",
        "- `outputs/range_metrics.csv`: q10~q90, q05~q95 범위 성능.",
        "- `outputs/predictions.csv`: validation/test 샘플별 예측값.",
        "- `experiment_config.json`: split, 피처, 모델 설정.",
        "",
    ]
    return "\n".join(lines)


def render_html(md: str, metrics_df: pd.DataFrame, range_df: pd.DataFrame) -> str:
    escaped = html.escape(md)
    body = escaped.replace("\n", "<br>\n")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{html.escape(EXP_ID)} {html.escape(TITLE)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.55}}
h1,h2{{color:#17212b}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left;vertical-align:top}}
th{{background:#eef2f7}}
code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}
.section{{margin:24px 0}}
</style>
</head>
<body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="section">{body}</div>
<h2>전체 Metrics</h2>
{metrics_df.to_html(index=False, escape=True)}
<h2>Range Metrics</h2>
{range_df.to_html(index=False, escape=True)}
</body></html>"""


def write_outputs(
    metrics_rows: list[dict[str, Any]],
    pred_frames: list[pd.DataFrame],
    range_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, str]:
    exp_dir = BASE_EXP_DIR / SLUG
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    range_df = pd.DataFrame(range_rows)
    pred_df = pd.concat(pred_frames, ignore_index=True)

    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    range_df.to_csv(exp_dir / "outputs" / "range_metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_markdown(metrics_df, range_df, config)
    html_doc = render_html(md, metrics_df, range_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    DOC_PATH.write_text(md, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")
    return {
        "experiment_dir": str(exp_dir.relative_to(REPO)),
        "report": str((exp_dir / "reports" / "result_report.md").relative_to(REPO)),
        "html": str((exp_dir / "reports" / "result_report.html").relative_to(REPO)),
        "docs_summary": str(DOC_PATH.relative_to(REPO)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree-alphas", default="0.05,0.10,0.25,0.40,0.50,0.60,0.75,0.90,0.95")
    parser.add_argument("--linear-alphas", default="0.10,0.25,0.50,0.75,0.90")
    parser.add_argument("--linear-regularization", type=float, default=0.001)
    parser.add_argument("--linear-train-limit", type=int, default=0, help="0 means use all train rows")
    parser.add_argument("--lgbm-estimators", type=int, default=430)
    parser.add_argument("--catboost-iterations", type=int, default=520)
    args = parser.parse_args()

    start = time.time()
    feature_profile = "cold_lightgbm_final_artifact_common_features"
    features = artifact_features()["cold_lightgbm"]
    train, val, test = load_scope("cold", features)
    train = normalize(train, features)
    val = normalize(val, features)
    test = normalize(test, features)

    tree_alphas = parse_alphas(args.tree_alphas)
    linear_alphas = parse_alphas(args.linear_alphas)
    metrics_rows: list[dict[str, Any]] = []
    pred_frames: list[pd.DataFrame] = []
    range_rows: list[dict[str, Any]] = []

    baseline_lgb = fit_predict("lightgbm", train, val, test, features)
    baseline_cat = fit_predict("catboost", train, val, test, features)
    for candidate, model_family, preds in [
        ("baseline_lightgbm_regression", "LightGBM Regression", baseline_lgb),
        ("baseline_catboost_rmse", "CatBoost RMSE", baseline_cat),
    ]:
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(metrics_rows, candidate, model_family, None, split, frame, preds[split], "baseline_point_prediction")
            pred_frames.append(prediction_frame(candidate, model_family, None, split, frame, preds[split], "baseline_point_prediction"))

    lgb_preds = fit_lgbm_quantiles(features, train, val, test, tree_alphas, n_estimators=args.lgbm_estimators)
    for alpha, preds in lgb_preds.items():
        candidate = f"lightgbm_quantile_{alpha_label(alpha)}"
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(metrics_rows, candidate, "LightGBM Quantile", alpha, split, frame, preds[split], "pinball_loss_tree_quantile")
            pred_frames.append(prediction_frame(candidate, "LightGBM Quantile", alpha, split, frame, preds[split], "pinball_loss_tree_quantile"))

    cat_preds = fit_catboost_quantiles(features, train, val, test, tree_alphas, iterations=args.catboost_iterations)
    for alpha, preds in cat_preds.items():
        candidate = f"catboost_quantile_{alpha_label(alpha)}"
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(metrics_rows, candidate, "CatBoost Quantile", alpha, split, frame, preds[split], "pinball_loss_symmetric_tree_quantile")
            pred_frames.append(prediction_frame(candidate, "CatBoost Quantile", alpha, split, frame, preds[split], "pinball_loss_symmetric_tree_quantile"))

    linear_preds, linear_fit_rows = fit_linear_quantiles(
        features,
        train,
        val,
        test,
        linear_alphas,
        regularization=args.linear_regularization,
        train_limit=args.linear_train_limit,
    )
    linear_note = (
        f"QuantileRegressor uses grouped one-hot categorical encoding; fit rows={linear_fit_rows}; "
        f"L1 regularization={args.linear_regularization}"
    )
    for alpha, preds in linear_preds.items():
        candidate = f"linear_quantile_regression_{alpha_label(alpha)}"
        for split, frame in [("validation", val), ("test", test)]:
            add_metric(metrics_rows, candidate, "Linear Quantile Regression", alpha, split, frame, preds[split], "linear_pinball_loss_quantile", notes=linear_note)
            pred_frames.append(prediction_frame(candidate, "Linear Quantile Regression", alpha, split, frame, preds[split], "linear_pinball_loss_quantile"))

    for model_family, preds in [
        ("LightGBM Quantile", lgb_preds),
        ("CatBoost Quantile", cat_preds),
        ("Linear Quantile Regression", linear_preds),
    ]:
        for split, frame in [("validation", val), ("test", test)]:
            add_range_rows(range_rows, model_family, split, frame, preds, 0.10, 0.90)
            add_range_rows(range_rows, model_family, split, frame, preds, 0.05, 0.95)
            add_range_rows(range_rows, model_family, split, frame, preds, 0.25, 0.75)

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "scope": "cold",
        "feature_profile": feature_profile,
        "feature_columns": features,
        "tree_alphas": tree_alphas,
        "linear_alphas": linear_alphas,
        "linear_regularization": args.linear_regularization,
        "linear_train_limit": args.linear_train_limit,
        "lgbm_estimators": args.lgbm_estimators,
        "catboost_iterations": args.catboost_iterations,
        "model_manifest": {
            "target": "ln_price_krw",
            "baseline_models": ["LightGBM regression", "CatBoost RMSE"],
            "quantile_models": ["LightGBM quantile", "CatBoost quantile", "sklearn QuantileRegressor"],
            "source_artifact_feature_key": "cold_lightgbm_price_model",
        },
    }
    paths = write_outputs(metrics_rows, pred_frames, range_rows, config)
    metrics_df = pd.DataFrame(metrics_rows)
    best_test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"]).head(6)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "paths": paths,
        "best_test": best_test[["candidate", "model_family", "quantile", "MdAPE", "MAPE", "p95_APE", "RMSE_log"]].to_dict(orient="records"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
