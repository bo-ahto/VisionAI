#!/usr/bin/env python3
"""Audit and regenerate Cold CatBoost/LightGBM interpretability from final artifacts."""
from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "track6"))

from run_t6_e005_feature_combo_ablation import add_generated_features, cat_feature_indices, cat_ready  # noqa: E402


COLD_FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "cold"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
CATBOOST_ARTIFACT = REPO / "data" / "track6" / "artifacts" / "track6_cold_catboost.cbm"
LIGHTGBM_ARTIFACT = REPO / "data" / "track6" / "artifacts" / "track6_cold_lightgbm.joblib"
MANIFEST = REPO / "data" / "track6" / "results" / "t6_e009_final_artifact_manifest.json"
OLD_INTERPRET_SCRIPT = REPO / "scripts" / "track6" / "generate_final_model_interpretability.py"

OUT_DIR = REPO / "experiments" / "track6" / "COLD_models_interpretability_audit"
OUT = OUT_DIR / "outputs"
DOC_DIR = REPO / "docs" / "track6" / "experiments"

CATBOOST_FEATURES = [
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
    "shape_bucket",
    "medium_shape_bucket",
]
LIGHTGBM_FEATURES = [
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
    "size_bucket",
    "support_size_bucket",
]
NUMERIC_FEATURES = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]


def read_pair(feature_path: Path, label_path: Path) -> pd.DataFrame:
    feature = pd.read_csv(feature_path, low_memory=False)
    label = pd.read_csv(label_path, low_memory=False)
    df = feature.merge(
        label[["_track6_row_id", "price_krw", "ln_price_krw"]],
        on="_track6_row_id",
        how="inner",
        validate="one_to_one",
    )
    return df.dropna(subset=["price_krw", "ln_price_krw"]).reset_index(drop=True)


def load_cold_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = read_pair(COLD_FEATURE_DIR / "track6_train_cold_features.csv", LABEL_DIR / "track6_train_labels.csv")
    val = read_pair(COLD_FEATURE_DIR / "track6_val_cold_cold_features.csv", LABEL_DIR / "track6_val_cold_labels.csv")
    test = read_pair(COLD_FEATURE_DIR / "track6_test_cold_cold_features.csv", LABEL_DIR / "track6_test_cold_labels.csv")
    train_val = pd.concat([train, val], ignore_index=True, sort=False)
    train_val_gen, test_gen = add_generated_features(train_val, test)
    return train_val_gen, test_gen


def clean_x(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    x = df[columns].copy()
    for col in columns:
        if col in NUMERIC_FEATURES:
            x[col] = pd.to_numeric(x[col], errors="coerce")
        else:
            x[col] = x[col].fillna("__MISSING__").astype(str)
    return x


def metrics(df: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual = df["price_krw"].to_numpy(dtype=float)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual) / actual
    return {
        "rows": float(len(df)),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p90_APE": float(np.quantile(ape, 0.90)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - df["ln_price_krw"].to_numpy(dtype=float)) ** 2))),
    }


def group_for_feature(feature: str) -> str:
    raw = feature.replace("num__", "", 1).replace("cat__", "", 1)
    if raw in {"width_cm", "height_cm", "area_cm2", "log_area", "size_bucket", "support_size_bucket"}:
        return "size"
    if raw in {"depth_cm", "has_depth", "is_3d_candidate"}:
        return "depth_3d"
    if raw in {"aspect_ratio", "shape_bucket", "medium_shape_bucket"}:
        return "shape"
    if raw == "medium_category":
        return "medium"
    if raw == "support_category":
        return "support"
    return "other"


def direction(value: float) -> str:
    if value > 0:
        return "평균적으로 예측가격 상승"
    if value < 0:
        return "평균적으로 예측가격 하락"
    return "영향 거의 없음"


def parse_old_cold_features() -> list[str]:
    script_text = OLD_INTERPRET_SCRIPT.read_text(encoding="utf-8")
    old_features = []
    in_block = False
    for line in script_text.splitlines():
        if line.startswith("COLD_FEATURES = ["):
            in_block = True
            continue
        if in_block and line.startswith("]"):
            break
        if in_block:
            value = line.strip().strip(",").strip('"')
            if value:
                old_features.append(value)
    return old_features


def feature_alignment_audit() -> pd.DataFrame:
    old_features = parse_old_cold_features()
    rows = []
    for model_name, final_features in [
        ("cold_catboost", CATBOOST_FEATURES),
        ("cold_lightgbm", LIGHTGBM_FEATURES),
    ]:
        for feature in sorted(set(final_features) | set(old_features)):
            rows.append(
                {
                    "model": model_name,
                    "feature": feature,
                    "final_artifact_feature": feature in final_features,
                    "old_interpretability_feature": feature in old_features,
                    "status": "일치" if feature in final_features and feature in old_features else "불일치",
                }
            )
    return pd.DataFrame(rows)


def catboost_interpretability(
    test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    model = CatBoostRegressor()
    model.load_model(CATBOOST_ARTIFACT)
    x_test = cat_ready(clean_x(test, CATBOOST_FEATURES), CATBOOST_FEATURES)
    y_test = test["ln_price_krw"].to_numpy(dtype=float)
    pred_log = np.asarray(model.predict(x_test), dtype=float)
    pool = Pool(x_test, label=y_test, cat_features=cat_feature_indices(CATBOOST_FEATURES))

    importance = pd.DataFrame(
        {
            "feature": CATBOOST_FEATURES,
            "importance": model.get_feature_importance(pool, type="PredictionValuesChange"),
        }
    )
    importance["feature_group"] = importance["feature"].map(group_for_feature)
    importance = importance.sort_values("importance", ascending=False).reset_index(drop=True)
    importance["rank"] = np.arange(1, len(importance) + 1)

    shap_values = model.get_feature_importance(pool, type="ShapValues")
    shap_feature = shap_values[:, :-1]
    shap = pd.DataFrame(
        {
            "feature": CATBOOST_FEATURES,
            "mean_abs_shap": np.abs(shap_feature).mean(axis=0),
            "mean_shap": shap_feature.mean(axis=0),
        }
    )
    shap["feature_group"] = shap["feature"].map(group_for_feature)
    shap["direction"] = shap["mean_shap"].map(direction)
    shap = shap.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    shap["rank"] = np.arange(1, len(shap) + 1)
    samples = shap_samples(test, pred_log, shap_feature, CATBOOST_FEATURES)
    interactions = catboost_interactions(model, pool)
    leaf_segments = catboost_leaf_segments(model, pool, test, pred_log)
    structure = catboost_structure_summary(model, leaf_segments)
    return importance, shap, interactions, leaf_segments, structure, samples, pred_log


def catboost_interactions(model: CatBoostRegressor, pool: Pool) -> pd.DataFrame:
    raw = model.get_feature_importance(pool, type="Interaction")
    rows = []
    for first_idx, second_idx, score in raw:
        first = CATBOOST_FEATURES[int(first_idx)]
        second = CATBOOST_FEATURES[int(second_idx)]
        rows.append(
            {
                "feature_1": first,
                "feature_2": second,
                "feature_group_1": group_for_feature(first),
                "feature_group_2": group_for_feature(second),
                "interaction_score": float(score),
            }
        )
    out = pd.DataFrame(rows).sort_values("interaction_score", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def catboost_leaf_segments(model: CatBoostRegressor, pool: Pool, test: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    leaves = model.calc_leaf_indexes(pool)
    residual_log = test["ln_price_krw"].to_numpy(dtype=float) - pred_log
    actual = test["price_krw"].to_numpy(dtype=float)
    ape = np.abs(np.exp(pred_log) - actual) / actual
    top_tree_count = min(50, leaves.shape[1])
    keys = ["|".join(map(str, row[:top_tree_count])) for row in leaves]
    segment = pd.DataFrame({"leaf_pattern_50": keys, "residual_log": residual_log, "APE": ape})
    out = (
        segment.groupby("leaf_pattern_50", as_index=False)
        .agg(
            rows=("APE", "size"),
            median_residual_log=("residual_log", "median"),
            MdAPE=("APE", "median"),
            p95_APE=("APE", lambda s: float(np.quantile(s, 0.95))),
        )
        .sort_values(["rows", "p95_APE"], ascending=[False, False])
        .reset_index(drop=True)
    )
    out["coverage_rate"] = out["rows"] / len(segment)
    return out


def catboost_structure_summary(model: CatBoostRegressor, leaf_segments: pd.DataFrame) -> pd.DataFrame:
    leaf_counts = np.asarray(model.get_tree_leaf_counts(), dtype=float)
    return pd.DataFrame(
        [
            {
                "model": "cold_catboost",
                "tree_count": int(model.tree_count_),
                "mean_leaf_count_per_tree": float(leaf_counts.mean()),
                "median_leaf_count_per_tree": float(np.median(leaf_counts)),
                "inferred_depth": float(np.log2(np.median(leaf_counts))),
                "leaf_pattern_50_unique_count": int(len(leaf_segments)),
                "top_10_leaf_pattern_coverage": float(leaf_segments.head(10)["coverage_rate"].sum()),
                "interpretation": "CatBoost 대칭 트리 구조상 같은 depth에서 동일 split 조건을 반복 적용하므로, 단독 중요도보다 interaction과 leaf segment 잔차를 함께 해석한다.",
            }
        ]
    )


def shap_samples(df: pd.DataFrame, pred_log: np.ndarray, shap_values: np.ndarray, names: list[str]) -> pd.DataFrame:
    actual = df["price_krw"].to_numpy(dtype=float)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual) / actual
    selected = np.r_[np.argsort(ape)[-15:], np.linspace(0, len(df) - 1, min(35, len(df)), dtype=int)]
    rows = []
    names_arr = np.asarray(names)
    for idx in pd.unique(selected):
        vals = shap_values[idx]
        up_idx = np.argsort(vals)[::-1][:5]
        down_idx = np.argsort(vals)[:5]
        rows.append(
            {
                "_track6_row_id": df.iloc[idx]["_track6_row_id"],
                "actual_price": float(actual[idx]),
                "pred_price": float(pred_price[idx]),
                "APE": float(ape[idx]),
                "top_up_features": " / ".join(f"{names_arr[j]}({vals[j]:.4f})" for j in up_idx),
                "top_down_features": " / ".join(f"{names_arr[j]}({vals[j]:.4f})" for j in down_idx),
            }
        )
    return pd.DataFrame(rows).sort_values("APE", ascending=False).reset_index(drop=True)


def lightgbm_interpretability(test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    model = joblib.load(LIGHTGBM_ARTIFACT)
    x_test = clean_x(test, LIGHTGBM_FEATURES)
    pred_log = np.asarray(model.predict(x_test), dtype=float)
    names = [str(x).replace("num__", "").replace("cat__", "") for x in model.named_steps["prep"].get_feature_names_out()]
    lgbm = model.named_steps["model"]
    importance = pd.DataFrame({"feature": names, "importance": lgbm.feature_importances_})
    importance["feature_group"] = importance["feature"].map(group_for_feature)
    importance = importance.sort_values("importance", ascending=False).reset_index(drop=True)
    importance["rank"] = np.arange(1, len(importance) + 1)

    permutation = permutation_delta(model, x_test, test, pred_log)
    leaf_diag = lightgbm_leaf_diagnostics(model, x_test, test, pred_log)
    tail = tail_slice_diagnostics(test, pred_log, LIGHTGBM_FEATURES)
    return importance, permutation, leaf_diag, tail, pred_log


def lightgbm_leaf_diagnostics(model: Any, x_test: pd.DataFrame, test: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    lgbm = model.named_steps["model"]
    transformed = prep.transform(x_test)
    leaves = lgbm.predict(transformed, pred_leaf=True)
    actual = test["price_krw"].to_numpy(dtype=float)
    ape = np.abs(np.exp(pred_log) - actual) / actual
    residual_log = test["ln_price_krw"].to_numpy(dtype=float) - pred_log
    rows = []
    for tree_idx in range(leaves.shape[1]):
        frame = pd.DataFrame({"leaf": leaves[:, tree_idx], "APE": ape, "residual_log": residual_log})
        grouped = frame.groupby("leaf").agg(rows=("APE", "size"), MdAPE=("APE", "median"), median_residual_log=("residual_log", "median"))
        rows.append(
            {
                "tree_idx": int(tree_idx),
                "used_leaf_count": int(grouped.shape[0]),
                "max_leaf_rows": int(grouped["rows"].max()),
                "max_leaf_row_rate": float(grouped["rows"].max() / len(frame)),
                "worst_leaf_MdAPE": float(grouped["MdAPE"].max()),
                "worst_leaf_rows": int(grouped.sort_values("MdAPE", ascending=False).iloc[0]["rows"]),
            }
        )
    out = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "tree_idx": "summary",
                "used_leaf_count": float(out["used_leaf_count"].mean()),
                "max_leaf_rows": float(out["max_leaf_rows"].median()),
                "max_leaf_row_rate": float(out["max_leaf_row_rate"].median()),
                "worst_leaf_MdAPE": float(out["worst_leaf_MdAPE"].median()),
                "worst_leaf_rows": float(out["worst_leaf_rows"].median()),
            }
        ]
    )
    return pd.concat([summary, out.sort_values("worst_leaf_MdAPE", ascending=False).head(20)], ignore_index=True)


def tail_slice_diagnostics(test: pd.DataFrame, pred_log: np.ndarray, columns: list[str]) -> pd.DataFrame:
    actual = test["price_krw"].to_numpy(dtype=float)
    ape = np.abs(np.exp(pred_log) - actual) / actual
    frame = test[columns].copy()
    frame["APE"] = ape
    rows = []
    for feature in ["size_bucket", "support_size_bucket", "support_category", "medium_category", "is_3d_candidate"]:
        if feature not in frame.columns:
            continue
        grouped = frame.groupby(feature, dropna=False)
        for value, part in grouped:
            if len(part) < 30:
                continue
            rows.append(
                {
                    "slice_feature": feature,
                    "slice_value": str(value),
                    "rows": int(len(part)),
                    "MdAPE": float(part["APE"].median()),
                    "p95_APE": float(np.quantile(part["APE"], 0.95)),
                    "mean_APE": float(part["APE"].mean()),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["p95_APE", "rows"], ascending=[False, False]).reset_index(drop=True)


def permutation_delta(model: Any, x_test: pd.DataFrame, test: pd.DataFrame, base_pred: np.ndarray) -> pd.DataFrame:
    rng = np.random.default_rng(20260531)
    base = metrics(test, base_pred)
    rows = []
    for feature in x_test.columns:
        x_perm = x_test.copy()
        x_perm[feature] = rng.permutation(x_perm[feature].to_numpy())
        pred = np.asarray(model.predict(x_perm), dtype=float)
        m = metrics(test, pred)
        rows.append(
            {
                "feature": feature,
                "feature_group": group_for_feature(feature),
                "MdAPE_delta": m["MdAPE"] - base["MdAPE"],
                "p95_APE_delta": m["p95_APE"] - base["p95_APE"],
                "RMSE_log_delta": m["RMSE_log"] - base["RMSE_log"],
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["MdAPE_delta", "RMSE_log_delta"], ascending=False).reset_index(drop=True)


def group_summary(cat_shap: pd.DataFrame, lgb_perm: pd.DataFrame) -> pd.DataFrame:
    cat_group = cat_shap.groupby("feature_group", as_index=False)["mean_abs_shap"].sum()
    lgb_group = lgb_perm.groupby("feature_group", as_index=False)[["MdAPE_delta", "RMSE_log_delta"]].sum()
    out = cat_group.merge(lgb_group, on="feature_group", how="outer").fillna(0.0)
    out["catboost_rank"] = out["mean_abs_shap"].rank(ascending=False, method="min").astype(int)
    out["lightgbm_perm_rank"] = out["MdAPE_delta"].rank(ascending=False, method="min").astype(int)
    return out.sort_values(["catboost_rank", "lightgbm_perm_rank"]).reset_index(drop=True)


def dataframe_html(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    return view.to_html(index=False, escape=True, border=0, classes="data-table")


def table_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_데이터 없음_"
    columns = [str(col) for col in view.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in view.itertuples(index=False):
        values = []
        for value in row:
            if pd.isna(value):
                values.append("-")
            elif isinstance(value, float):
                values.append(f"{value:.6g}")
            else:
                values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_html(
    audit: pd.DataFrame,
    metrics_df: pd.DataFrame,
    group_df: pd.DataFrame,
    cat_importance: pd.DataFrame,
    cat_shap: pd.DataFrame,
    cat_interactions: pd.DataFrame,
    cat_leaf_segments: pd.DataFrame,
    cat_structure: pd.DataFrame,
    lgb_importance: pd.DataFrame,
    lgb_perm: pd.DataFrame,
    lgb_leaf: pd.DataFrame,
    lgb_tail: pd.DataFrame,
    cat_samples: pd.DataFrame,
) -> str:
    style = """
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:32px;color:#1f2933;line-height:1.55}
    h1{font-size:26px;margin-bottom:8px} h2{font-size:20px;margin-top:32px;border-bottom:1px solid #d9e2ec;padding-bottom:6px}
    .note{background:#f5f7fa;border-left:4px solid #486581;padding:12px 14px;margin:16px 0}
    table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}
    th,td{border:1px solid #d9e2ec;padding:7px 8px;vertical-align:top} th{background:#f0f4f8;text-align:left}
    code{background:#f0f4f8;padding:2px 4px;border-radius:4px}
    """
    return f"""<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>Cold 모델 해석 감사 보고서</title><style>{style}</style></head>
<body>
<h1>Cold 모델 해석 감사 보고서</h1>
<p>작성일: <code>{date.today().isoformat()}</code></p>
<div class="note">
현재 결론: 기존 Cold 해석 보고서는 <code>artist_meta_*</code>, <code>ln_estimated_ho</code>, <code>nant_*</code> 피처를 기준으로 만들어졌지만,
최종 Cold artifact는 CatBoost <code>base_medium_shape</code>, LightGBM <code>base_support_size</code>를 사용한다.
따라서 기존 Cold 해석 HTML은 최종 Cold 모델 설명 근거로 그대로 쓰기 어렵고, 아래 산출물이 최종 artifact 기준의 보정된 해석이다.
</div>
<h2>1. 피처셋 일치성 감사</h2>
{dataframe_html(audit)}
<h2>2. 최종 artifact 성능 재확인</h2>
{dataframe_html(metrics_df)}
<h2>3. 모델별/그룹별 해석 요약</h2>
{dataframe_html(group_df)}
<h2>4. Cold CatBoost 중요도</h2>
{dataframe_html(cat_importance)}
<h2>5. Cold CatBoost SHAP</h2>
{dataframe_html(cat_shap)}
<h2>6. CatBoost 대칭 트리 구조 요약</h2>
{dataframe_html(cat_structure)}
<h2>7. CatBoost Interaction</h2>
{dataframe_html(cat_interactions, 30)}
<h2>8. CatBoost Leaf Segment 잔차</h2>
{dataframe_html(cat_leaf_segments, 30)}
<h2>9. Cold LightGBM Split Importance</h2>
{dataframe_html(lgb_importance)}
<h2>10. Cold LightGBM Permutation 진단</h2>
{dataframe_html(lgb_perm)}
<h2>11. LightGBM Leaf-wise 분화 진단</h2>
{dataframe_html(lgb_leaf)}
<h2>12. LightGBM Tail Slice 진단</h2>
{dataframe_html(lgb_tail, 40)}
<h2>13. CatBoost 샘플별 SHAP 설명</h2>
{dataframe_html(cat_samples)}
<h2>14. 재실험/추가 실험 판단</h2>
<div class="note">
기존 Cold 해석 산출물은 최종 artifact와 피처셋이 다르므로 반드시 교체해야 한다.
CatBoost는 최종 artifact 기준 SHAP 해석이 가능하며, 크기 피처가 가장 강하고 depth/support/medium이 보조한다.
LightGBM은 MdAPE는 CatBoost와 비슷하지만 p95_APE가 더 높아 tail risk 진단이 필요하다.
특히 permutation 결과에서 <code>area_cm2</code> 교란 시 MdAPE와 p95가 크게 흔들려,
크기 파생 피처 중복성과 tail 안정성 추가 실험을 권장한다.
</div>
</body></html>"""


def render_markdown(
    audit: pd.DataFrame,
    metrics_df: pd.DataFrame,
    group_df: pd.DataFrame,
    cat_importance: pd.DataFrame,
    cat_shap: pd.DataFrame,
    cat_interactions: pd.DataFrame,
    cat_leaf_segments: pd.DataFrame,
    cat_structure: pd.DataFrame,
    lgb_importance: pd.DataFrame,
    lgb_perm: pd.DataFrame,
    lgb_leaf: pd.DataFrame,
    lgb_tail: pd.DataFrame,
) -> str:
    return "\n\n".join(
        [
            "# Cold 모델 해석 감사 보고서",
            f"- 작성일: `{date.today().isoformat()}`",
            "- 결론: 기존 Cold 해석 산출물은 최종 artifact와 피처셋이 불일치하므로, 최종 Cold 모델 설명 근거로 그대로 쓰기 어렵다.",
            "- 보정: 최종 CatBoost/LightGBM artifact를 직접 불러와 성능, 중요도, SHAP 또는 permutation 진단을 재산출했다.",
            "- 해석 기준: CatBoost는 SHAP을 우선하고, LightGBM은 split importance와 permutation delta를 함께 본다.",
            "- 재실험 판단: CatBoost는 최종 artifact 기준 해석 산출물 교체가 우선이다. LightGBM은 p95 tail risk와 크기 파생 피처 중복성 추가 진단이 필요하다.",
            "## 1. 피처셋 일치성 감사\n" + table_markdown(audit),
            "## 2. 최종 artifact 성능 재확인\n" + table_markdown(metrics_df),
            "## 3. 모델별/그룹별 해석 요약\n" + table_markdown(group_df),
            "## 4. CatBoost 중요도\n" + table_markdown(cat_importance),
            "## 5. CatBoost SHAP\n" + table_markdown(cat_shap),
            "## 6. CatBoost 대칭 트리 구조 요약\n" + table_markdown(cat_structure),
            "## 7. CatBoost interaction\n" + table_markdown(cat_interactions, 30),
            "## 8. CatBoost leaf segment 잔차\n" + table_markdown(cat_leaf_segments, 30),
            "## 9. LightGBM split importance\n" + table_markdown(lgb_importance),
            "## 10. LightGBM permutation 진단\n" + table_markdown(lgb_perm),
            "## 11. LightGBM leaf-wise 분화 진단\n" + table_markdown(lgb_leaf),
            "## 12. LightGBM tail slice 진단\n" + table_markdown(lgb_tail, 40),
            "\n".join(
                [
                    "## 13. 재실험/추가 실험 판단",
                    "- 기존 Cold 해석 산출물은 최종 artifact와 피처셋이 다르므로 교체가 필요하다.",
                    "- CatBoost는 SHAP 기준 해석이 가능하며, 크기 피처가 가장 강하고 depth/support/medium이 보조한다.",
                    "- LightGBM은 MdAPE는 CatBoost와 비슷하지만 p95_APE가 더 높아 tail risk 진단이 필요하다.",
                    "- LightGBM permutation에서 `area_cm2` 교란 영향이 커서, `width_cm`, `height_cm`, `area_cm2`, `log_area` 중복성 및 tail 안정성 추가 실험이 필요하다.",
                    "- 권장 후속: `C-LGBM-size-ablation`, `C-LGBM-tail-slice`, `C-CB-shap-stability`, `Cold-final-interpretability-report-update`.",
                ]
            ),
        ]
    ) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    _train_val, test = load_cold_frames()
    audit = feature_alignment_audit()

    cat_importance, cat_shap, cat_interactions, cat_leaf_segments, cat_structure, cat_samples, cat_pred = catboost_interpretability(test)
    lgb_importance, lgb_perm, lgb_leaf, lgb_tail, lgb_pred = lightgbm_interpretability(test)
    metrics_df = pd.DataFrame(
        [
            {"model": "cold_catboost", "feature_set": "base_medium_shape", **metrics(test, cat_pred)},
            {"model": "cold_lightgbm", "feature_set": "base_support_size", **metrics(test, lgb_pred)},
        ]
    )
    group_df = group_summary(cat_shap, lgb_perm)

    audit.to_csv(OUT / "cold_feature_alignment_audit.csv", index=False)
    metrics_df.to_csv(OUT / "cold_final_artifact_metrics.csv", index=False)
    group_df.to_csv(OUT / "cold_feature_group_interpretation_summary.csv", index=False)
    cat_importance.to_csv(OUT / "cold_catboost_final_feature_importance.csv", index=False)
    cat_shap.to_csv(OUT / "cold_catboost_final_shap_summary.csv", index=False)
    cat_interactions.to_csv(OUT / "cold_catboost_final_interactions.csv", index=False)
    cat_leaf_segments.to_csv(OUT / "cold_catboost_leaf_segment_residuals.csv", index=False)
    cat_structure.to_csv(OUT / "cold_catboost_structure_summary.csv", index=False)
    cat_samples.to_csv(OUT / "cold_catboost_final_sample_shap_explanations.csv", index=False)
    lgb_importance.to_csv(OUT / "cold_lightgbm_final_feature_importance.csv", index=False)
    lgb_perm.to_csv(OUT / "cold_lightgbm_final_permutation_diagnostics.csv", index=False)
    lgb_leaf.to_csv(OUT / "cold_lightgbm_leafwise_diagnostics.csv", index=False)
    lgb_tail.to_csv(OUT / "cold_lightgbm_tail_slice_diagnostics.csv", index=False)

    html_text = render_html(
        audit,
        metrics_df,
        group_df,
        cat_importance,
        cat_shap,
        cat_interactions,
        cat_leaf_segments,
        cat_structure,
        lgb_importance,
        lgb_perm,
        lgb_leaf,
        lgb_tail,
        cat_samples,
    )
    md_text = render_markdown(
        audit,
        metrics_df,
        group_df,
        cat_importance,
        cat_shap,
        cat_interactions,
        cat_leaf_segments,
        cat_structure,
        lgb_importance,
        lgb_perm,
        lgb_leaf,
        lgb_tail,
    )
    (DOC_DIR / "cold_models_interpretability_audit_report.html").write_text(html_text, encoding="utf-8")
    (DOC_DIR / "cold_models_interpretability_audit_report.md").write_text(md_text, encoding="utf-8")
    print(f"wrote {DOC_DIR / 'cold_models_interpretability_audit_report.html'}")
    print(f"wrote {DOC_DIR / 'cold_models_interpretability_audit_report.md'}")
    print(f"wrote outputs under {OUT}")


if __name__ == "__main__":
    main()
