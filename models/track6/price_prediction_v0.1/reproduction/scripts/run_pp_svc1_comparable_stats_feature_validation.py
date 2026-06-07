#!/usr/bin/env python3
"""Run PP-SVC1 comparable-stat feature validation.

PP-SVC1 checks whether service-facing comparable statistics can also improve
Warm/Cold model predictions. Validation/test statistics are computed from train
only. Train statistics are cross-fitted so each train row does not use its own
target price in the comparable group.
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
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC1"
EXP_SLUG = "PP-SVC1_comparable_stats_feature_validation"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "서비스 비교군 통계 피처 검증"
SEED = 20260603

BASE_NUMERIC = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
]
GROUPING_FEATURES = [
    "artist_key",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "size_bucket",
    "area_cm2",
    "log_area",
]
SVC_NUMERIC = [
    "svc_group_log_price_median",
    "svc_group_log_price_q25",
    "svc_group_log_price_q75",
    "svc_group_log_price_iqr",
    "svc_group_log_unit_area_median",
    "svc_group_log_unit_area_iqr",
    "svc_group_n_log",
]
SVC_CATEGORICAL = [
    "svc_group_level",
    "svc_coverage_tier",
    "svc_has_artist_level",
]
GROUP_DEFS = [
    {
        "level": "artist_medium_support_size",
        "keys": ["artist_key", "medium_support_bucket", "size_bucket"],
        "min_n": 5,
        "service_label": "작가+재료/지지체+크기",
    },
    {
        "level": "artist_size",
        "keys": ["artist_key", "size_bucket"],
        "min_n": 5,
        "service_label": "작가+크기",
    },
    {
        "level": "artist",
        "keys": ["artist_key"],
        "min_n": 5,
        "service_label": "작가 전체",
    },
    {
        "level": "medium_support_size",
        "keys": ["medium_support_bucket", "size_bucket"],
        "min_n": 30,
        "service_label": "재료/지지체+크기",
    },
    {
        "level": "medium_category_support_size",
        "keys": ["medium_category", "support_category", "size_bucket"],
        "min_n": 30,
        "service_label": "재료+지지체+크기",
    },
    {
        "level": "medium_size",
        "keys": ["medium_category", "size_bucket"],
        "min_n": 50,
        "service_label": "재료+크기",
    },
]


EXPERIMENTS = [
    {
        "experiment_id": "PP-SVC1-W",
        "scope": "warm",
        "model": "huber",
        "feature_key": "warm",
        "title": "Warm Huber 비교군 통계 피처",
    },
    {
        "experiment_id": "PP-SVC1-CB",
        "scope": "cold",
        "model": "catboost",
        "feature_key": "cold_catboost",
        "title": "Cold CatBoost 비교군 통계 피처",
    },
    {
        "experiment_id": "PP-SVC1-LGBM",
        "scope": "cold",
        "model": "lightgbm",
        "feature_key": "cold_lightgbm",
        "title": "Cold LightGBM 비교군 통계 피처",
    },
]


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def comparable_ready(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in ["price_krw", "ln_price_krw", "area_cm2"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    area = np.clip(out["area_cm2"].astype(float).to_numpy(), 1.0, None)
    out["svc_source_log_unit_area"] = out["ln_price_krw"].astype(float).to_numpy() - np.log(area)
    for col in ["artist_key", "medium_category", "support_category", "medium_support_bucket", "size_bucket"]:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def aggregate_stats(source: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    if key_cols:
        grouped = source.groupby(key_cols, dropna=False, observed=False)
        stats = grouped.agg(
            svc_group_log_price_median=("ln_price_krw", "median"),
            svc_group_log_price_q25=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.25))),
            svc_group_log_price_q75=("ln_price_krw", lambda x: float(np.quantile(x.astype(float), 0.75))),
            svc_group_log_unit_area_median=("svc_source_log_unit_area", "median"),
            svc_group_log_unit_area_q25=("svc_source_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.25))),
            svc_group_log_unit_area_q75=("svc_source_log_unit_area", lambda x: float(np.quantile(x.astype(float), 0.75))),
            svc_group_n=("ln_price_krw", "size"),
        ).reset_index()
    else:
        stats = pd.DataFrame([{
            "svc_group_log_price_median": float(source["ln_price_krw"].median()),
            "svc_group_log_price_q25": float(source["ln_price_krw"].quantile(0.25)),
            "svc_group_log_price_q75": float(source["ln_price_krw"].quantile(0.75)),
            "svc_group_log_unit_area_median": float(source["svc_source_log_unit_area"].median()),
            "svc_group_log_unit_area_q25": float(source["svc_source_log_unit_area"].quantile(0.25)),
            "svc_group_log_unit_area_q75": float(source["svc_source_log_unit_area"].quantile(0.75)),
            "svc_group_n": int(len(source)),
        }])
    stats["svc_group_log_price_iqr"] = stats["svc_group_log_price_q75"] - stats["svc_group_log_price_q25"]
    stats["svc_group_log_unit_area_iqr"] = (
        stats["svc_group_log_unit_area_q75"] - stats["svc_group_log_unit_area_q25"]
    )
    return stats


def coverage_tier(level: str, n: float) -> str:
    if level == "global":
        return "fallback_global"
    if n >= 50:
        return "high_n"
    if n >= 15:
        return "medium_n"
    return "low_n"


def apply_comparable_stats(source: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    source_ready = comparable_ready(source)
    target_ready = comparable_ready(target)
    result = target_ready[["_track6_row_id"]].copy()
    for col in SVC_NUMERIC:
        result[col] = np.nan
    for col in SVC_CATEGORICAL:
        result[col] = "__UNASSIGNED__"
    result["svc_group_n"] = np.nan

    assigned = np.zeros(len(result), dtype=bool)
    stat_cols = [
        "svc_group_log_price_median",
        "svc_group_log_price_q25",
        "svc_group_log_price_q75",
        "svc_group_log_price_iqr",
        "svc_group_log_unit_area_median",
        "svc_group_log_unit_area_iqr",
        "svc_group_n",
    ]
    for group_def in GROUP_DEFS:
        keys = group_def["keys"]
        stats = aggregate_stats(source_ready, keys)
        merged = target_ready[keys].merge(stats, on=keys, how="left")
        eligible = (~assigned) & (pd.to_numeric(merged["svc_group_n"], errors="coerce").fillna(0) >= group_def["min_n"]).to_numpy()
        if not eligible.any():
            continue
        for col in stat_cols:
            result.loc[eligible, col] = merged.loc[eligible, col].to_numpy()
        result.loc[eligible, "svc_group_level"] = group_def["level"]
        result.loc[eligible, "svc_has_artist_level"] = str("artist_key" in keys)
        assigned |= eligible

    if (~assigned).any():
        global_stats = aggregate_stats(source_ready, [])
        for col in stat_cols:
            result.loc[~assigned, col] = global_stats.iloc[0][col]
        result.loc[~assigned, "svc_group_level"] = "global"
        result.loc[~assigned, "svc_has_artist_level"] = "False"

    result["svc_group_n_log"] = np.log1p(pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0))
    result["svc_coverage_tier"] = [
        coverage_tier(str(level), float(n))
        for level, n in zip(result["svc_group_level"], pd.to_numeric(result["svc_group_n"], errors="coerce").fillna(0))
    ]
    result["svc_has_artist_level"] = result["svc_has_artist_level"].astype(str)
    return result[["_track6_row_id", *SVC_NUMERIC, *SVC_CATEGORICAL, "svc_group_n"]]


def crossfit_train_stats(train: pd.DataFrame) -> pd.DataFrame:
    folds = min(5, max(2, len(train) // 1000))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    parts: list[pd.DataFrame] = []
    for source_idx, holdout_idx in kfold.split(train):
        source = train.iloc[source_idx].copy()
        target = train.iloc[holdout_idx].copy()
        parts.append(apply_comparable_stats(source, target))
    return pd.concat(parts, ignore_index=True)


def add_service_features(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats = crossfit_train_stats(train)
    val_stats = apply_comparable_stats(train, val)
    test_stats = apply_comparable_stats(train, test)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
    )


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [col for col in features if col in set(BASE_NUMERIC + SVC_NUMERIC)]
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
        transformers.append(("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=4000)),
    ])


def lightgbm_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
        ]), numeric))
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
    numeric, _categorical = split_types(features)
    numeric_set = set(numeric)
    return [idx for idx, col in enumerate(features) if col not in numeric_set]


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


def metric_values(frame: pd.DataFrame, pred_log: np.ndarray | pd.Series) -> dict[str, float]:
    actual_price = frame["price_krw"].to_numpy(dtype=float)
    actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
    pred = np.asarray(pred_log, dtype=float)
    pred_price = np.clip(np.exp(pred), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / np.clip(actual_price, 1.0, None)
    return {
        "n": int(len(frame)),
        "RMSE_log": float(np.sqrt(np.mean((pred - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def prediction_frame(
    experiment_id: str,
    candidate: str,
    scope: str,
    split: str,
    frame: pd.DataFrame,
    pred_log: np.ndarray,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": experiment_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "svc_group_level": frame.get("svc_group_level", pd.Series([""] * len(frame))).to_numpy(),
        "svc_coverage_tier": frame.get("svc_coverage_tier", pd.Series([""] * len(frame))).to_numpy(),
        "svc_group_n": frame.get("svc_group_n", pd.Series([np.nan] * len(frame))).to_numpy(),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def coverage_summary(frames_by_scope: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scope, split_frames in frames_by_scope.items():
        for split, frame in split_frames.items():
            for level, group in frame.groupby("svc_group_level", dropna=False):
                rows.append({
                    "scope": scope,
                    "split": split,
                    "svc_group_level": level,
                    "rows": int(len(group)),
                    "share": float(len(group) / len(frame)),
                    "median_group_n": float(pd.to_numeric(group["svc_group_n"], errors="coerce").median()),
                })
            for tier, group in frame.groupby("svc_coverage_tier", dropna=False):
                rows.append({
                    "scope": scope,
                    "split": split,
                    "svc_group_level": f"tier:{tier}",
                    "rows": int(len(group)),
                    "share": float(len(group) / len(frame)),
                    "median_group_n": float(pd.to_numeric(group["svc_group_n"], errors="coerce").median()),
                })
    return pd.DataFrame(rows)


def candidate_features(base_features: list[str]) -> dict[str, list[str]]:
    return {
        "baseline": list(base_features),
        "svc_numeric": list(dict.fromkeys([*base_features, *SVC_NUMERIC])),
        "svc_full": list(dict.fromkeys([*base_features, *SVC_NUMERIC, *SVC_CATEGORICAL])),
    }


def render_report(metrics_df: pd.DataFrame, coverage_df: pd.DataFrame) -> tuple[str, str]:
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["scope", "experiment_id", "MdAPE", "MAPE"])
    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 서비스 비교군 통계값을 API 표시값과 모델 피처로 동시에 쓸 수 있는지 검증한다.",
        "- 현재 split에는 `estimated_ho`가 없어 이번 실험은 호당가 직접값이 아니라 `면적 기준 단가`를 사용했다.",
        "- validation/test 비교군 통계는 train 데이터만 사용했고, train 피처는 5-fold 방식으로 자기 가격이 들어가지 않게 만들었다.",
        "",
        "## 1. Test 결과",
        "",
        "| 실험 | scope | 모델 | 후보 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in test.itertuples():
        lines.append(
            f"| `{row.experiment_id}` | {row.scope} | {row.model} | `{row.candidate}` | "
            f"{row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )

    lines += ["", "## 2. Baseline 대비 test 변화", "", "| 실험 | 후보 | MdAPE 변화 | MAPE 변화 | p95 변화 | 해석 |", "|---|---|---:|---:|---:|---|"]
    for exp_id, group in test.groupby("experiment_id", dropna=False):
        base = group[group["candidate"].eq("baseline")]
        if base.empty:
            continue
        b = base.iloc[0]
        for row in group[group["candidate"].ne("baseline")].itertuples():
            md_delta = b.MdAPE - row.MdAPE
            mape_delta = b.MAPE - row.MAPE
            p95_delta = b.p95_APE - row.p95_APE
            if md_delta > 0 and mape_delta > 0:
                comment = "대표/평균 오차 모두 개선"
            elif md_delta > 0:
                comment = "대표 오차 개선, 평균/꼬리 확인 필요"
            elif mape_delta > 0 or p95_delta > 0:
                comment = "방어 후보 가능, 대표 후보는 보류"
            else:
                comment = "추가 피처 효과 제한적"
            lines.append(
                f"| `{exp_id}` | `{row.candidate}` | {md_delta:.4f} | {mape_delta:.4f} | {p95_delta:.4f} | {comment} |"
            )

    lines += ["", "## 3. 비교군 coverage", "", "| scope | split | level/tier | rows | share | median N |", "|---|---|---|---:|---:|---:|"]
    for row in coverage_df.itertuples():
        lines.append(
            f"| {row.scope} | {row.split} | `{row.svc_group_level}` | {row.rows} | {row.share:.3f} | {row.median_group_n:.1f} |"
        )

    lines += [
        "",
        "## 4. 해석 기준",
        "",
        "- Warm에서 작가 기반 비교군이 많이 잡히면 Huber의 작가 기준선을 보완하는 피처로 해석한다.",
        "- Cold에서 global 또는 재료/크기 fallback 비중이 크면, 작가별 prior보다는 작품 조건별 가격대 prior로 해석한다.",
        "- 성능이 개선되지 않아도 coverage가 안정적이면 API 표시값으로는 사용할 수 있다.",
        "- `estimated_ho`가 추가되면 `면적 기준 단가`를 실제 `호당가`로 교체해 재검증한다.",
        "",
        "## 5. 실행 결론",
        "",
        "- 비교군 중앙값을 그대로 예측값으로 쓰는 방식이 충분하지 않다면, 개선은 중앙값 대체가 아니라 모델이 비교군 통계를 prior로 사용한 결과로 해석한다.",
        "- Warm에서 비교군 통계 후보가 크게 개선되면 최종 후보 편입 전 반복 split 또는 bootstrap 안정성 검증 대상으로 올린다.",
        "- Cold에서 MdAPE 개선이 약하고 MAPE/p95만 개선되면 대표 모델 교체보다 큰 오차 방어와 API 표시 근거 피처로 우선 활용한다.",
    ]
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(EXP_ID)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933;line-height:1.5}}
h1,h2{{margin-top:28px}} table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 24px}}
th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}} th{{background:#eef2f7}} code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}
.note{{background:#f8fafc;border:1px solid #d8dee4;border-radius:6px;padding:12px;margin:12px 0}}
</style></head><body>
<h1>{html.escape(EXP_ID)} {html.escape(TITLE)}</h1>
<div class="note">현재 split에는 estimated_ho가 없어 면적 기준 단가로 대체 검증했습니다. validation/test 통계는 train-only 기준입니다.</div>
<h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Coverage</h2>{coverage_df.to_html(index=False, escape=True)}
<h2>Conclusion</h2><ul>
<li>비교군 중앙값 직접 예측이 충분하지 않다면, 개선은 중앙값 대체가 아니라 모델이 비교군 통계를 prior로 사용한 결과로 해석합니다.</li>
<li>Warm에서 비교군 통계 후보가 크게 개선되면 최종 후보 편입 전 반복 split 또는 bootstrap 안정성 검증 대상으로 올립니다.</li>
<li>Cold에서 MdAPE 개선이 약하고 MAPE/p95만 개선되면 대표 모델 교체보다 큰 오차 방어와 API 표시 근거 피처로 우선 활용합니다.</li>
</ul>
</body></html>"""
    return md, html_doc


def write_outputs(metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], frames_by_scope: dict[str, dict[str, pd.DataFrame]], config: dict[str, Any]) -> None:
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    cov_df = coverage_summary(frames_by_scope)
    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    cov_df.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    feature_cols = ["scope", "split", "_track6_row_id", *SVC_NUMERIC, *SVC_CATEGORICAL, "svc_group_n"]
    all_feature_rows = []
    snapshots = []
    for scope, split_frames in frames_by_scope.items():
        for split, frame in split_frames.items():
            full = frame.copy()
            full["scope"] = scope
            full["split"] = split
            all_feature_rows.append(full[[col for col in feature_cols if col in full.columns]])
            part = frame.head(50).copy()
            part["scope"] = scope
            part["split"] = split
            snapshots.append(part[[col for col in feature_cols if col in part.columns]])
    pd.concat(all_feature_rows, ignore_index=True).to_csv(EXP_DIR / "outputs" / "comparable_features.csv", index=False)
    pd.concat(snapshots, ignore_index=True).to_csv(EXP_DIR / "outputs" / "comparable_feature_snapshot.csv", index=False)
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "feature_manifest.json").write_text(json.dumps(config["feature_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "data" / "group_definitions.json").write_text(json.dumps(GROUP_DEFS, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, cov_df)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc1_comparable_stats_feature_validation_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()
    features_by_key = artifact_features()
    metrics_rows: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    frames_by_scope: dict[str, dict[str, pd.DataFrame]] = {}
    feature_manifest: dict[str, Any] = {}
    direct_prior_scopes: set[str] = set()

    for exp in EXPERIMENTS:
        base_features = features_by_key[exp["feature_key"]]
        requested_features = list(dict.fromkeys([*base_features, *GROUPING_FEATURES]))
        train, val, test = load_scope(exp["scope"], requested_features)
        train, val, test = add_service_features(train, val, test)
        frames_by_scope.setdefault(exp["scope"], {})
        for split_name, frame in [("train_oof", train), ("validation", val), ("test", test)]:
            frames_by_scope[exp["scope"]][split_name] = frame

        if exp["scope"] not in direct_prior_scopes:
            direct_prior_scopes.add(exp["scope"])
            direct_exp_id = f"PP-SVC1-DIRECT-{exp['scope'].upper()}"
            for split_name, frame in [("validation", val), ("test", test)]:
                pred_log = frame["svc_group_log_price_median"].to_numpy(dtype=float)
                metrics_rows.append({
                    "experiment_id": direct_exp_id,
                    "title": "비교군 중앙값 직접 예측 기준선",
                    "scope": exp["scope"],
                    "model": "service_prior",
                    "candidate": "svc_group_log_price_median",
                    "split": split_name,
                    "n_features": 1,
                    "features": "svc_group_log_price_median",
                    **metric_values(frame, pred_log),
                })
                predictions.append(prediction_frame(direct_exp_id, "svc_group_log_price_median", exp["scope"], split_name, frame, pred_log))

        candidates = candidate_features(base_features)
        feature_manifest[exp["experiment_id"]] = candidates
        for candidate, features in candidates.items():
            train_n = normalize(train, features)
            val_n = normalize(val, features)
            test_n = normalize(test, features)
            pred = fit_predict(exp["model"], train_n, val_n, test_n, features)
            for split_name, frame, pred_log in [
                ("validation", val_n, pred["validation"]),
                ("test", test_n, pred["test"]),
            ]:
                metrics_rows.append({
                    "experiment_id": exp["experiment_id"],
                    "title": exp["title"],
                    "scope": exp["scope"],
                    "model": exp["model"],
                    "candidate": candidate,
                    "split": split_name,
                    "n_features": len(features),
                    "features": ", ".join(features),
                    **metric_values(frame, pred_log),
                })
                predictions.append(prediction_frame(exp["experiment_id"], candidate, exp["scope"], split_name, frame, pred_log))

    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "source_split_root": "data/track6_split",
        "unit_price_definition": "ln_price_krw - log(area_cm2); estimated_ho is not present in current split",
        "leakage_control": {
            "train_features": "5-fold cross-fitted comparable stats",
            "validation_test_features": "train-only comparable stats",
            "target_usage": "price is used only to create train-derived comparable tables and evaluation labels",
        },
        "group_definitions": GROUP_DEFS,
        "service_numeric_features": SVC_NUMERIC,
        "service_categorical_features": SVC_CATEGORICAL,
        "feature_manifest": feature_manifest,
    }
    write_outputs(metrics_rows, predictions, frames_by_scope, config)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc1_comparable_stats_feature_validation_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
