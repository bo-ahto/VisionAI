#!/usr/bin/env python3
"""Run PP-SVC5 multilevel comparable-stat feature experiment.

This experiment extends PP-SVC1. PP-SVC1 selects one fallback comparable group
per row. PP-SVC5 exposes multiple comparable-group levels at the same time so
Warm Huber can learn which level to trust.
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import artifact_features, load_scope  # noqa: E402
from run_pp_svc1_comparable_stats_feature_validation import (  # noqa: E402
    GROUP_DEFS,
    GROUPING_FEATURES,
    SVC_NUMERIC,
    add_service_features,
    aggregate_stats,
    comparable_ready,
)


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_ROOT = REPO / "docs" / "track6" / "experiments"
EXP_ID = "PP-SVC5"
EXP_SLUG = "PP-SVC5_warm_multilevel_comparable_stats"
EXP_DIR = EXP_ROOT / EXP_SLUG
TITLE = "Warm 다층 비교군 통계 피처 실험"
SEED = 20260604
PP_SVC3_PREDICTIONS = EXP_ROOT / "PP-SVC3_warm_svc_blend_routing" / "outputs" / "predictions.csv"

BASE_NUMERIC = [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
]

STAT_SOURCE_COLS = [
    "svc_group_log_price_median",
    "svc_group_log_price_q25",
    "svc_group_log_price_q75",
    "svc_group_log_price_iqr",
    "svc_group_log_unit_area_median",
    "svc_group_log_unit_area_iqr",
    "svc_group_n",
]
STAT_SUFFIXES = {
    "svc_group_log_price_median": "price_median",
    "svc_group_log_price_q25": "price_q25",
    "svc_group_log_price_q75": "price_q75",
    "svc_group_log_price_iqr": "price_iqr",
    "svc_group_log_unit_area_median": "unit_area_median",
    "svc_group_log_unit_area_iqr": "unit_area_iqr",
}

THRESHOLD_POLICIES = {
    "default": {
        "artist_medium_support_size": 5,
        "artist_size": 5,
        "artist": 5,
        "medium_support_size": 30,
        "medium_category_support_size": 30,
        "medium_size": 50,
    },
    "loose": {
        "artist_medium_support_size": 3,
        "artist_size": 3,
        "artist": 3,
        "medium_support_size": 20,
        "medium_category_support_size": 20,
        "medium_size": 30,
    },
    "strict": {
        "artist_medium_support_size": 10,
        "artist_size": 10,
        "artist": 10,
        "medium_support_size": 50,
        "medium_category_support_size": 50,
        "medium_size": 80,
    },
}


def ensure_dirs() -> None:
    for sub in ["outputs", "reports", "artifacts", "logs", "data"]:
        (EXP_DIR / sub).mkdir(parents=True, exist_ok=True)
    DOC_ROOT.mkdir(parents=True, exist_ok=True)


def prefixed(level: str, name: str, policy: str) -> str:
    return f"svcml_{policy}_{level}_{name}"


def policy_group_defs(policy: str) -> list[dict[str, Any]]:
    thresholds = THRESHOLD_POLICIES[policy]
    out: list[dict[str, Any]] = []
    for group_def in GROUP_DEFS:
        item = dict(group_def)
        item["min_n"] = thresholds[item["level"]]
        out.append(item)
    return out


def apply_multilevel_stats(source: pd.DataFrame, target: pd.DataFrame, policy: str) -> pd.DataFrame:
    source_ready = comparable_ready(source)
    target_ready = comparable_ready(target)
    result = target_ready[["_track6_row_id"]].copy()

    for group_def in policy_group_defs(policy):
        level = group_def["level"]
        keys = group_def["keys"]
        stats = aggregate_stats(source_ready, keys)
        merged = target_ready[keys].merge(stats, on=keys, how="left")
        n = pd.to_numeric(merged["svc_group_n"], errors="coerce")
        eligible = n.fillna(0).ge(group_def["min_n"]).to_numpy()
        for source_col, suffix in STAT_SUFFIXES.items():
            col = prefixed(level, suffix, policy)
            values = pd.to_numeric(merged[source_col], errors="coerce").to_numpy(dtype=float)
            result[col] = np.where(eligible, values, np.nan)
        result[prefixed(level, "n_log", policy)] = np.where(eligible, np.log1p(n.fillna(0).to_numpy(dtype=float)), 0.0)
        result[prefixed(level, "covered", policy)] = eligible.astype(float)

    global_stats = aggregate_stats(source_ready, [])
    for source_col, suffix in STAT_SUFFIXES.items():
        result[prefixed("global", suffix, policy)] = float(global_stats.iloc[0][source_col])
    result[prefixed("global", "n_log", policy)] = float(np.log1p(global_stats.iloc[0]["svc_group_n"]))
    result[prefixed("global", "covered", policy)] = 1.0
    return result


def crossfit_multilevel_stats(train: pd.DataFrame, policy: str) -> pd.DataFrame:
    folds = min(5, max(2, len(train) // 1000))
    kfold = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    parts: list[pd.DataFrame] = []
    for source_idx, holdout_idx in kfold.split(train):
        parts.append(apply_multilevel_stats(train.iloc[source_idx].copy(), train.iloc[holdout_idx].copy(), policy))
    return pd.concat(parts, ignore_index=True)


def add_multilevel_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    policy: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_stats = crossfit_multilevel_stats(train, policy)
    val_stats = apply_multilevel_stats(train, val, policy)
    test_stats = apply_multilevel_stats(train, test, policy)
    return (
        train.merge(train_stats, on="_track6_row_id", how="left"),
        val.merge(val_stats, on="_track6_row_id", how="left"),
        test.merge(test_stats, on="_track6_row_id", how="left"),
    )


def policy_feature_groups(policy: str) -> dict[str, list[str]]:
    median_n: list[str] = []
    full_numeric: list[str] = []
    levels = [group_def["level"] for group_def in GROUP_DEFS] + ["global"]
    for level in levels:
        median_n.extend([
            prefixed(level, "price_median", policy),
            prefixed(level, "unit_area_median", policy),
            prefixed(level, "n_log", policy),
            prefixed(level, "covered", policy),
        ])
        for suffix in [*STAT_SUFFIXES.values(), "n_log", "covered"]:
            full_numeric.append(prefixed(level, suffix, policy))
    return {
        f"multi_{policy}_median_n": list(dict.fromkeys(median_n)),
        f"multi_{policy}_full_numeric": list(dict.fromkeys(full_numeric)),
    }


def all_numeric_features() -> set[str]:
    out = set(BASE_NUMERIC + SVC_NUMERIC)
    for policy in THRESHOLD_POLICIES:
        for group in policy_feature_groups(policy).values():
            out.update(group)
    return out


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric_all = all_numeric_features()
    numeric = [feature for feature in features if feature in numeric_all]
    categorical = [feature for feature in features if feature not in numeric_all]
    return numeric, categorical


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical:
        out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def huber_model(features: list[str], alpha: float) -> Pipeline:
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
        ("model", HuberRegressor(epsilon=1.35, alpha=alpha, max_iter=5000)),
    ])


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


def fit_predict(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    features: list[str],
    alpha: float,
) -> dict[str, np.ndarray]:
    model = huber_model(features, alpha)
    model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
    return {
        "validation": np.asarray(model.predict(val[features]), dtype=float),
        "test": np.asarray(model.predict(test[features]), dtype=float),
    }


def prediction_frame(candidate: str, method: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": EXP_ID,
        "candidate": candidate,
        "method": method,
        "scope": "warm",
        "split": split,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
        "artist_key": frame.get("artist_key", pd.Series([""] * len(frame))).to_numpy(),
        "artist_name_ko": frame.get("artist_name_ko", pd.Series([""] * len(frame))).to_numpy(),
        "svc_group_level": frame.get("svc_group_level", pd.Series([""] * len(frame))).to_numpy(),
        "svc_coverage_tier": frame.get("svc_coverage_tier", pd.Series([""] * len(frame))).to_numpy(),
        "svc_group_n": frame.get("svc_group_n", pd.Series([np.nan] * len(frame))).to_numpy(),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / np.clip(out["actual_price"], 1.0, None)
    return out


def load_pp_v8_predictions() -> pd.DataFrame:
    if not PP_SVC3_PREDICTIONS.exists():
        raise FileNotFoundError(f"PP-SVC3 predictions not found: {PP_SVC3_PREDICTIONS}")
    pred = pd.read_csv(PP_SVC3_PREDICTIONS, low_memory=False)
    pred = pred[
        pred["candidate"].isin([
            "pp_v8_compact_blend_mape_guarded",
            "blend_svcnum_ppv8_wsvc_0.70",
        ])
        & pred["split"].isin(["validation", "test"])
    ].copy()
    return pred[["candidate", "split", "_track6_row_id", "pred_log"]]


def add_reference_and_blend_candidates(
    metrics_rows: list[dict[str, Any]],
    predictions: list[pd.DataFrame],
    val: pd.DataFrame,
    test: pd.DataFrame,
    base_predictions: dict[str, dict[str, np.ndarray]],
) -> None:
    ref = load_pp_v8_predictions()
    refs = {
        candidate: group.pivot_table(index=["split", "_track6_row_id"], values="pred_log", aggfunc="last")
        for candidate, group in ref.groupby("candidate")
    }
    for candidate, pivot in refs.items():
        for split_name, frame in [("validation", val), ("test", test)]:
            joined = frame[["_track6_row_id"]].assign(split=split_name).join(
                pivot,
                on=["split", "_track6_row_id"],
                how="left",
            )
            pred_log = joined["pred_log"].to_numpy(dtype=float)
            metrics_rows.append({
                "candidate": candidate,
                "method": "reference",
                "split": split_name,
                "n_features": 0,
                "features": "reference_prediction",
                **metric_values(frame, pred_log),
            })
            predictions.append(prediction_frame(candidate, "reference", split_name, frame, pred_log))

    if "pp_v8_compact_blend_mape_guarded" not in refs:
        return
    ppv8 = refs["pp_v8_compact_blend_mape_guarded"]
    validation_frames: list[dict[str, Any]] = []
    for base_candidate, by_split in base_predictions.items():
        for weight in np.round(np.arange(0.50, 0.91, 0.05), 2):
            label = f"blend_{base_candidate}_ppv8_wsvc_{weight:.2f}"
            for split_name, frame in [("validation", val), ("test", test)]:
                ppv8_pred = frame[["_track6_row_id"]].assign(split=split_name).join(
                    ppv8,
                    on=["split", "_track6_row_id"],
                    how="left",
                )["pred_log"].to_numpy(dtype=float)
                pred_log = weight * by_split[split_name] + (1.0 - weight) * ppv8_pred
                row = {
                    "candidate": label,
                    "method": "weighted_blend_with_ppv8",
                    "split": split_name,
                    "n_features": 0,
                    "features": f"{weight:.2f} * {base_candidate} + {1.0 - weight:.2f} * pp_v8",
                    **metric_values(frame, pred_log),
                }
                metrics_rows.append(row)
                predictions.append(prediction_frame(label, "weighted_blend_with_ppv8", split_name, frame, pred_log))
                if split_name == "validation":
                    validation_frames.append(row)

    val_df = pd.DataFrame(validation_frames)
    ppv8_val = pd.DataFrame(metrics_rows)
    ppv8_val = ppv8_val[(ppv8_val["candidate"].eq("pp_v8_compact_blend_mape_guarded")) & (ppv8_val["split"].eq("validation"))]
    if ppv8_val.empty or val_df.empty:
        return
    mdape_guard = float(ppv8_val.iloc[0]["MdAPE"])
    guarded = val_df[val_df["MdAPE"].le(mdape_guard)]
    if guarded.empty:
        guarded = val_df
    selected = guarded.sort_values(["MAPE", "MdAPE", "p95_APE"]).iloc[0]
    (EXP_DIR / "artifacts" / "selected_blend_candidate.json").write_text(
        json.dumps(
            {
                "selection_basis": "validation MAPE with PP-V8 MdAPE guard",
                "pp_v8_validation_MdAPE_guard": mdape_guard,
                "selected_candidate": selected["candidate"],
                "validation_metrics": {
                    "MdAPE": float(selected["MdAPE"]),
                    "MAPE": float(selected["MAPE"]),
                    "p95_APE": float(selected["p95_APE"]),
                    "RMSE_log": float(selected["RMSE_log"]),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def coverage_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for policy in THRESHOLD_POLICIES:
        for group_def in GROUP_DEFS:
            level = group_def["level"]
            covered = pd.to_numeric(frame[prefixed(level, "covered", policy)], errors="coerce").fillna(0).to_numpy()
            n_log = pd.to_numeric(frame[prefixed(level, "n_log", policy)], errors="coerce").fillna(0)
            covered_mask = covered > 0
            rows.append({
                "policy": policy,
                "level": level,
                "rows": int(len(frame)),
                "covered_rows": int(covered_mask.sum()),
                "covered_share": float(covered_mask.mean()),
                "median_n_when_covered": float(np.expm1(n_log[covered_mask].median())) if covered_mask.any() else 0.0,
            })
    return pd.DataFrame(rows)


def render_report(metrics_df: pd.DataFrame, coverage_df: pd.DataFrame) -> tuple[str, str]:
    test = metrics_df[metrics_df["split"].eq("test")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    validation = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MAPE", "MdAPE", "p95_APE"])
    selected_path = EXP_DIR / "artifacts" / "selected_blend_candidate.json"
    selected = json.loads(selected_path.read_text(encoding="utf-8")) if selected_path.exists() else {}
    selected_candidate = selected.get("selected_candidate", "")
    selected_test = test[test["candidate"].eq(selected_candidate)]

    lines = [
        f"# {EXP_ID} {TITLE}",
        "",
        f"- 작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 비교군 통계를 하나만 고르는 기존 fallback 방식보다 여러 비교군 수준을 동시에 넣는 방식이 더 좋은지 확인",
        "- 대상: Warm Huber",
        "- 데이터 통제: train/validation/test split 고정",
        "- 누수 통제: train 비교군 통계는 5-fold 교차검증 방식, validation/test는 train-only 방식",
        "",
        "## 1. 실험 구성",
        "",
        "- `baseline_huber`: 기존 Warm Huber 기준 피처만 사용",
        "- `fallback_numeric`: 기존 PP-SVC1 방식의 선택된 비교군 통계 사용",
        "- `multi_*_alpha001`: 다층 비교군 피처를 강한 정규화 Huber로 학습",
        "- `multi_default_median_n_alpha001`: 여러 비교군 수준의 중앙값/면적단가/표본 수를 동시에 사용",
        "- `multi_default_full_numeric_alpha001`: 여러 비교군 수준의 중앙값/분위값/범위/면적단가/표본 수를 동시에 사용",
        "- `multi_loose_median_n_alpha001`: 최소 표본 기준 완화",
        "- `multi_strict_median_n_alpha001`: 최소 표본 기준 강화",
        "- `multi_plus_fallback_alpha001`: 기존 fallback 통계와 다층 통계를 함께 사용",
        "- `blend_*_ppv8_*`: 새 비교군 후보와 기존 PP-V8 방어형 후보를 로그 가격 기준으로 결합",
        "",
        "## 2. Test 결과 상위 후보",
        "",
        "| 후보 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in test.head(18).itertuples():
        lines.append(
            f"| `{row.candidate}` | {row.method} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} | {row.RMSE_log:.4f} |"
        )

    lines += [
        "",
        "## 3. Validation MAPE 기준 상위 후보",
        "",
        "| 후보 | 방식 | MdAPE | MAPE | p95_APE |",
        "|---|---|---:|---:|---:|",
    ]
    for row in validation.head(12).itertuples():
        lines.append(f"| `{row.candidate}` | {row.method} | {row.MdAPE:.4f} | {row.MAPE:.4f} | {row.p95_APE:.4f} |")

    lines += [
        "",
        "## 4. 선택 후보",
        "",
    ]
    if selected_candidate and not selected_test.empty:
        row = selected_test.iloc[0]
        lines += [
            f"- 선택 기준: {selected.get('selection_basis', '')}",
            f"- 선택 후보: `{selected_candidate}`",
            f"- test MdAPE: `{row['MdAPE']:.4f}`",
            f"- test MAPE: `{row['MAPE']:.4f}`",
            f"- test p95_APE: `{row['p95_APE']:.4f}`",
        ]
    else:
        lines.append("- 선택 후보: 생성되지 않음")

    lines += [
        "",
        "## 5. Coverage 요약",
        "",
        "| 정책 | 비교군 수준 | covered share | covered rows | median N |",
        "|---|---|---:|---:|---:|",
    ]
    for row in coverage_df.itertuples():
        lines.append(
            f"| {row.policy} | `{row.level}` | {row.covered_share:.3f} | {row.covered_rows} | {row.median_n_when_covered:.1f} |"
        )

    lines += [
        "",
        "## 6. 해석",
        "",
        "- 다층 비교군 후보가 기존 `fallback_numeric`보다 좋아지면 Huber가 여러 비교군 기준을 조합해 가격 기준선을 더 잘 잡는다는 의미",
        "- 다층 비교군 후보가 약하면 현재 데이터에서는 가장 신뢰 가능한 비교군 하나를 고르는 fallback 방식이 더 안정적이라는 의미",
        "- 결합 후보가 기존 `PP-SVC3`보다 좋아지면 Warm 서비스 후보를 `PP-SVC6` 반복 holdout 검증으로 승격",
        "- 결합 후보가 기존 `PP-SVC3`보다 약하면 기존 `svc_numeric 70% + PP-V8 30%` 정책 유지",
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
<div class="note">Warm Huber 대상. 다층 비교군 통계와 기존 PP-V8 방어 후보 결합까지 확인.</div>
<h2>Metrics</h2>{metrics_df.sort_values(['split','MdAPE','MAPE']).to_html(index=False, escape=True)}
<h2>Coverage</h2>{coverage_df.to_html(index=False, escape=True)}
</body></html>"""
    return md, html_doc


def write_outputs(
    metrics_rows: list[dict[str, Any]],
    predictions: list[pd.DataFrame],
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    feature_manifest: dict[str, dict[str, Any]],
) -> None:
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    coverage_df = coverage_summary(test)
    metrics_df.to_csv(EXP_DIR / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    coverage_df.to_csv(EXP_DIR / "outputs" / "coverage_summary.csv", index=False)
    feature_cols = ["_track6_row_id"]
    feature_cols.extend(sorted([col for col in train.columns if col.startswith("svcml_") or col.startswith("svc_group_") or col.startswith("svc_coverage")]))
    for split_name, frame in [("train_oof", train), ("validation", val), ("test", test)]:
        frame[[col for col in feature_cols if col in frame.columns]].to_csv(
            EXP_DIR / "outputs" / f"comparable_multilevel_features_{split_name}.csv",
            index=False,
        )
    config = {
        "experiment_id": EXP_ID,
        "title": TITLE,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": SEED,
        "scope": "warm",
        "model": "HuberRegressor",
        "source_split_root": "data/track6_split",
        "leakage_control": {
            "train_multilevel_features": "5-fold cross-fitted comparable stats",
            "validation_test_multilevel_features": "train-only comparable stats",
            "blend_selection": "validation only",
        },
        "threshold_policies": THRESHOLD_POLICIES,
        "group_definitions": GROUP_DEFS,
        "feature_manifest": feature_manifest,
    }
    (EXP_DIR / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "artifacts" / "feature_manifest.json").write_text(json.dumps(feature_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render_report(metrics_df, coverage_df)
    (EXP_DIR / "README.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (DOC_ROOT / "pp_svc5_multilevel_comparable_stats_summary.md").write_text(md, encoding="utf-8")
    (EXP_DIR / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {EXP_ID} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    ensure_dirs()
    base_features = artifact_features()["warm"]
    requested = list(dict.fromkeys([*base_features, *GROUPING_FEATURES]))
    train, val, test = load_scope("warm", requested)
    train, val, test = add_service_features(train, val, test)
    for policy in THRESHOLD_POLICIES:
        train, val, test = add_multilevel_features(train, val, test, policy)

    candidates: dict[str, dict[str, Any]] = {
        "baseline_huber": {
            "features": list(base_features),
            "alpha": 0.0001,
            "blend_eligible": False,
        },
        "fallback_numeric": {
            "features": list(dict.fromkeys([*base_features, *SVC_NUMERIC])),
            "alpha": 0.0001,
            "blend_eligible": True,
        },
    }
    for policy in THRESHOLD_POLICIES:
        groups = policy_feature_groups(policy)
        candidates[f"multi_{policy}_median_n_alpha001"] = {
            "features": list(dict.fromkeys([*base_features, *groups[f"multi_{policy}_median_n"]])),
            "alpha": 0.01,
            "blend_eligible": True,
        }
        candidates[f"multi_{policy}_median_n_alpha01"] = {
            "features": list(dict.fromkeys([*base_features, *groups[f"multi_{policy}_median_n"]])),
            "alpha": 0.1,
            "blend_eligible": True,
        }
        if policy == "default":
            candidates[f"multi_{policy}_full_numeric_alpha001"] = {
                "features": list(dict.fromkeys([*base_features, *groups[f"multi_{policy}_full_numeric"]])),
                "alpha": 0.01,
                "blend_eligible": True,
            }
    candidates["multi_plus_fallback_alpha001"] = {
        "features": list(dict.fromkeys([
            *base_features,
            *SVC_NUMERIC,
            *policy_feature_groups("default")["multi_default_median_n"],
        ])),
        "alpha": 0.01,
        "blend_eligible": True,
    }
    candidates["multi_plus_fallback_alpha01"] = {
        "features": list(dict.fromkeys([
            *base_features,
            *SVC_NUMERIC,
            *policy_feature_groups("default")["multi_default_median_n"],
        ])),
        "alpha": 0.1,
        "blend_eligible": True,
    }

    metrics_rows: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    base_predictions: dict[str, dict[str, np.ndarray]] = {}

    for candidate, config in candidates.items():
        features = config["features"]
        alpha = float(config["alpha"])
        train_n = normalize(train, features)
        val_n = normalize(val, features)
        test_n = normalize(test, features)
        pred = fit_predict(train_n, val_n, test_n, features, alpha)
        val_metrics = metric_values(val_n, pred["validation"])
        if (
            bool(config["blend_eligible"])
            and np.isfinite(val_metrics["MAPE"])
            and np.isfinite(val_metrics["MdAPE"])
            and val_metrics["MAPE"] < 1.0
            and val_metrics["MdAPE"] < 0.5
        ):
            base_predictions[candidate] = {
                "validation": pred["validation"],
                "test": pred["test"],
            }
        for split_name, frame, pred_log in [
            ("validation", val_n, pred["validation"]),
            ("test", test_n, pred["test"]),
        ]:
            metrics_rows.append({
                "candidate": candidate,
                "method": "warm_huber",
                "split": split_name,
                "n_features": len(features),
                "features": ", ".join(features),
                "alpha": alpha,
                **metric_values(frame, pred_log),
            })
            predictions.append(prediction_frame(candidate, "warm_huber", split_name, frame, pred_log))

    add_reference_and_blend_candidates(metrics_rows, predictions, val, test, base_predictions)
    write_outputs(metrics_rows, predictions, train, val, test, candidates)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "experiment_dir": str(EXP_DIR.relative_to(REPO)),
        "report": str((EXP_DIR / "reports" / "result_report.md").relative_to(REPO)),
        "summary_doc": str((DOC_ROOT / "pp_svc5_multilevel_comparable_stats_summary.md").relative_to(REPO)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
