#!/usr/bin/env python3
"""Audit and regenerate Warm Huber interpretability from the final artifact."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
FEATURE_DIR = REPO / "data" / "track6_split" / "features" / "warm"
LABEL_DIR = REPO / "data" / "track6_split" / "labels"
ARTIFACT = REPO / "data" / "track6" / "artifacts" / "track6_warm_huber.joblib"
MANIFEST = REPO / "data" / "track6" / "results" / "t6_e009_final_artifact_manifest.json"
OLD_INTERPRET_SCRIPT = REPO / "scripts" / "track6" / "generate_final_model_interpretability.py"

OUT_DIR = REPO / "experiments" / "track6" / "WARM_HUBER_interpretability_audit"
OUT = OUT_DIR / "outputs"
DOC_DIR = REPO / "docs" / "track6" / "experiments"

FINAL_FEATURES = [
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
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
    "artist_key",
]
NUMERIC_FEATURES = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
GROUP_ORDER = [
    "size",
    "depth_3d",
    "shape",
    "medium",
    "support",
    "medium_support",
    "artist",
    "other",
]


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


def combine_train_validation() -> pd.DataFrame:
    train = read_pair(FEATURE_DIR / "track6_train_warm_features.csv", LABEL_DIR / "track6_train_labels.csv")
    val = read_pair(FEATURE_DIR / "track6_val_warm_warm_features.csv", LABEL_DIR / "track6_val_warm_labels.csv")
    return pd.concat([train, val], ignore_index=True, sort=False)


def clean_x(df: pd.DataFrame) -> pd.DataFrame:
    x = df[FINAL_FEATURES].copy()
    for col in NUMERIC_FEATURES:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    for col in FINAL_FEATURES:
        if col not in NUMERIC_FEATURES:
            x[col] = x[col].fillna("__MISSING__").astype(str)
    return x


def warm_pipeline(epsilon: float = 1.35) -> Pipeline:
    numeric = NUMERIC_FEATURES
    categorical = [col for col in FINAL_FEATURES if col not in numeric]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore")
    prep = ColumnTransformer(
        [
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", Pipeline([("onehot", encoder)]), categorical),
        ]
    )
    return Pipeline(
        [
            ("prep", prep),
            ("model", HuberRegressor(alpha=0.0001, epsilon=epsilon, max_iter=3000)),
        ]
    )


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


def group_for_encoded_feature(feature: str) -> str:
    raw = feature.replace("num__", "", 1).replace("cat__", "", 1)
    if raw in {"width_cm", "height_cm", "area_cm2", "log_area"}:
        return "size"
    if raw in {"depth_cm"} or raw.startswith("has_depth_") or raw.startswith("is_3d_candidate_"):
        return "depth_3d"
    if raw in {"aspect_ratio"} or raw.startswith("is_extreme_aspect_ratio_"):
        return "shape"
    if raw.startswith("medium_category_"):
        return "medium"
    if raw.startswith("support_category_"):
        return "support"
    if raw.startswith("medium_support_bucket_"):
        return "medium_support"
    if raw.startswith("artist_key_"):
        return "artist"
    return "other"


def raw_feature_for_encoded_feature(feature: str) -> str:
    raw = feature.replace("num__", "", 1).replace("cat__", "", 1)
    for col in FINAL_FEATURES:
        if raw == col or raw.startswith(f"{col}_"):
            return col
    return raw.split("_")[0]


def direction(value: float) -> str:
    if value > 0:
        return "예측가격 상승 방향"
    if value < 0:
        return "예측가격 하락 방향"
    return "영향 거의 없음"


def transformed_array(x_transformed: Any) -> np.ndarray:
    if hasattr(x_transformed, "toarray"):
        return x_transformed.toarray()
    return np.asarray(x_transformed)


def scaler_stats(model: Any) -> dict[str, tuple[float, float]]:
    prep = model.named_steps["prep"]
    for name, transformer, cols in prep.transformers_:
        if name != "num":
            continue
        scaler = transformer.named_steps["scale"]
        return {str(col): (float(mean), float(scale)) for col, mean, scale in zip(cols, scaler.mean_, scaler.scale_)}
    return {}


def coefficient_table(model: Any, contribution: pd.DataFrame) -> pd.DataFrame:
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    names = [str(x) for x in prep.get_feature_names_out()]
    scale_by_feature = scaler_stats(model)
    coef = pd.DataFrame({"encoded_feature": names, "coef": reg.coef_})
    coef["raw_feature"] = coef["encoded_feature"].map(raw_feature_for_encoded_feature)
    coef["feature_group"] = coef["encoded_feature"].map(group_for_encoded_feature)
    coef["abs_coef"] = coef["coef"].abs()
    coef["coef_direction"] = coef["coef"].map(direction)
    coef["standardized_input"] = coef["raw_feature"].isin(NUMERIC_FEATURES)
    coef["original_unit_coef"] = np.nan
    for idx, row in coef.iterrows():
        if row["raw_feature"] in scale_by_feature:
            _mean, scale = scale_by_feature[row["raw_feature"]]
            coef.loc[idx, "original_unit_coef"] = row["coef"] / scale
    coef = coef.merge(contribution, on=["encoded_feature", "raw_feature", "feature_group"], how="left")
    coef["centered_coef"] = coef["coef"]
    for raw_feature, part in coef.loc[~coef["raw_feature"].isin(NUMERIC_FEATURES)].groupby("raw_feature"):
        weights = part["active_rate"].to_numpy(dtype=float)
        if weights.sum() <= 0:
            baseline = float(part["coef"].mean())
        else:
            baseline = float(np.average(part["coef"].to_numpy(dtype=float), weights=weights))
        coef.loc[coef["raw_feature"].eq(raw_feature), "centered_coef"] = (
            coef.loc[coef["raw_feature"].eq(raw_feature), "coef"] - baseline
        )
    coef["mean_abs_centered_contribution"] = np.where(
        coef["raw_feature"].isin(NUMERIC_FEATURES),
        coef["mean_abs_contribution"],
        coef["active_rate"] * coef["centered_coef"].abs(),
    )
    coef["mean_centered_contribution"] = np.where(
        coef["raw_feature"].isin(NUMERIC_FEATURES),
        coef["mean_contribution"],
        coef["active_rate"] * coef["centered_coef"],
    )
    coef["centered_direction"] = coef["mean_centered_contribution"].map(direction)
    coef["rank_by_abs_contribution"] = coef["mean_abs_contribution"].rank(ascending=False, method="min").astype(int)
    coef["rank_by_centered_abs_contribution"] = (
        coef["mean_abs_centered_contribution"].rank(ascending=False, method="min").astype(int)
    )
    coef["rank_by_abs_coef"] = coef["abs_coef"].rank(ascending=False, method="min").astype(int)
    return coef.sort_values(["rank_by_centered_abs_contribution", "encoded_feature"]).reset_index(drop=True)


def contribution_table(model: Any, df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    x = clean_x(df)
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    x_transformed = transformed_array(prep.transform(x))
    contributions = x_transformed * reg.coef_
    names = [str(x) for x in prep.get_feature_names_out()]
    out = pd.DataFrame(
        {
            "encoded_feature": names,
            "active_rate": np.asarray(x_transformed.mean(axis=0)).ravel(),
            "mean_abs_contribution": np.abs(contributions).mean(axis=0),
            "mean_contribution": contributions.mean(axis=0),
            "median_abs_contribution": np.median(np.abs(contributions), axis=0),
            "p95_abs_contribution": np.quantile(np.abs(contributions), 0.95, axis=0),
        }
    )
    out["raw_feature"] = out["encoded_feature"].map(raw_feature_for_encoded_feature)
    out["feature_group"] = out["encoded_feature"].map(group_for_encoded_feature)
    out["contribution_direction"] = out["mean_contribution"].map(direction)
    return out, x_transformed, contributions


def group_summary(coef: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group in GROUP_ORDER:
        part = coef.loc[coef["feature_group"].eq(group)]
        if part.empty:
            continue
        up = (
            part.loc[part["mean_centered_contribution"] > 0]
            .sort_values("mean_abs_centered_contribution", ascending=False)
            .head(5)
        )
        down = (
            part.loc[part["mean_centered_contribution"] < 0]
            .sort_values("mean_abs_centered_contribution", ascending=False)
            .head(5)
        )
        rows.append(
            {
                "feature_group": group,
                "encoded_feature_count": int(len(part)),
                "mean_abs_centered_contribution_sum": float(part["mean_abs_centered_contribution"].sum()),
                "top_features": " / ".join(
                    part.sort_values("mean_abs_centered_contribution", ascending=False).head(5)["encoded_feature"].tolist()
                ),
                "top_up_features": " / ".join(up["encoded_feature"].tolist()),
                "top_down_features": " / ".join(down["encoded_feature"].tolist()),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["rank"] = out["mean_abs_centered_contribution_sum"].rank(ascending=False, method="min").astype(int)
    return out.sort_values(["rank", "feature_group"]).reset_index(drop=True)


def sample_explanations(model: Any, df: pd.DataFrame, contributions: np.ndarray, pred_log: np.ndarray) -> pd.DataFrame:
    names = np.asarray([str(x) for x in model.named_steps["prep"].get_feature_names_out()])
    actual = df["price_krw"].to_numpy(dtype=float)
    pred_price = np.exp(pred_log)
    ape = np.abs(pred_price - actual) / actual
    selected = np.r_[np.argsort(ape)[-15:], np.linspace(0, len(df) - 1, min(35, len(df)), dtype=int)]
    rows = []
    for idx in pd.unique(selected):
        vals = contributions[idx]
        up_idx = np.argsort(vals)[::-1][:5]
        down_idx = np.argsort(vals)[:5]
        rows.append(
            {
                "_track6_row_id": df.iloc[idx]["_track6_row_id"],
                "actual_price": float(actual[idx]),
                "pred_price": float(pred_price[idx]),
                "APE": float(ape[idx]),
                "top_up_features": " / ".join(f"{names[j]}({vals[j]:.4f})" for j in up_idx),
                "top_down_features": " / ".join(f"{names[j]}({vals[j]:.4f})" for j in down_idx),
            }
        )
    return pd.DataFrame(rows).sort_values("APE", ascending=False).reset_index(drop=True)


def huber_outlier_summary(model: Any, df: pd.DataFrame, split_name: str) -> dict[str, float]:
    pred_log = model.predict(clean_x(df))
    residual = df["ln_price_krw"].to_numpy(dtype=float) - pred_log
    reg = model.named_steps["model"]
    threshold = float(reg.epsilon * reg.scale_)
    mask = np.abs(residual) > threshold
    return {
        "split": split_name,
        "rows": float(len(df)),
        "epsilon": float(reg.epsilon),
        "scale": float(reg.scale_),
        "outlier_threshold_log": threshold,
        "outlier_count": float(mask.sum()),
        "outlier_rate": float(mask.mean()),
        "median_abs_residual_log": float(np.median(np.abs(residual))),
        "p95_abs_residual_log": float(np.quantile(np.abs(residual), 0.95)),
    }


def epsilon_sensitivity() -> pd.DataFrame:
    train = read_pair(FEATURE_DIR / "track6_train_warm_features.csv", LABEL_DIR / "track6_train_labels.csv")
    val = read_pair(FEATURE_DIR / "track6_val_warm_warm_features.csv", LABEL_DIR / "track6_val_warm_labels.csv")
    test = read_pair(FEATURE_DIR / "track6_test_warm_warm_features.csv", LABEL_DIR / "track6_test_warm_labels.csv")
    rows = []
    for eps in [1.1, 1.35, 1.5, 1.75, 2.0]:
        model = warm_pipeline(eps)
        model.fit(clean_x(train), train["ln_price_krw"].astype(float))
        for split_name, df in [("val_warm", val), ("test_warm_locked", test)]:
            pred_log = model.predict(clean_x(df))
            item = {"epsilon": eps, "split": split_name, **metrics(df, pred_log)}
            item.update(
                {
                    "outlier_rate": huber_outlier_summary(model, df, split_name)["outlier_rate"],
                    "n_iter": float(model.named_steps["model"].n_iter_),
                    "scale": float(model.named_steps["model"].scale_),
                }
            )
            rows.append(item)
    return pd.DataFrame(rows)


def feature_alignment_audit() -> pd.DataFrame:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    warm = next(item for item in manifest["artifacts"] if item["key"] == "warm_price_model")
    script_text = OLD_INTERPRET_SCRIPT.read_text(encoding="utf-8")
    old_features = []
    in_block = False
    for line in script_text.splitlines():
        if line.startswith("WARM_FEATURES = ["):
            in_block = True
            continue
        if in_block and line.startswith("]"):
            break
        if in_block:
            value = line.strip().strip(",").strip('"')
            if value:
                old_features.append(value)
    final_features = list(warm["features"])
    rows = []
    for feature in sorted(set(final_features) | set(old_features)):
        rows.append(
            {
                "feature": feature,
                "final_artifact_feature": feature in final_features,
                "old_interpretability_feature": feature in old_features,
                "status": "일치" if feature in final_features and feature in old_features else "불일치",
            }
        )
    return pd.DataFrame(rows)


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
    metric_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    epsilon_df: pd.DataFrame,
    group_df: pd.DataFrame,
    coef_df: pd.DataFrame,
    sample_df: pd.DataFrame,
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
<head><meta charset="utf-8"><title>Warm Huber 해석 감사 보고서</title><style>{style}</style></head>
<body>
<h1>Warm Huber 해석 감사 보고서</h1>
<p>작성일: <code>{date.today().isoformat()}</code></p>
<div class="note">
현재 결론: 최종 Warm artifact는 <code>base_existing_combo + artist_key</code> 13개 피처로 학습되어 있으나,
기존 FINAL 해석 보고서는 7개 피처와 다른 split 경로를 사용했다. 따라서 기존 Warm 해석 HTML은 최종 Warm Huber의 전체 피처 해석으로 쓰기 어렵고,
아래 산출물이 최종 artifact 기준의 보정된 해석이다.
성능 관점에서는 최종 artifact의 test MdAPE가 기존 test 확인 결과와 유사하므로 즉시 모델을 갈아엎을 근거는 약하다.
다만 Huber outlier 비율과 epsilon 민감도는 후속 안정성 실험 후보로 남긴다.
</div>
<h2>1. 피처셋 일치성 감사</h2>
{dataframe_html(audit)}
<h2>2. 최종 artifact 성능 재확인</h2>
{dataframe_html(metric_df)}
<h2>3. Huber outlier 진단</h2>
{dataframe_html(outlier_df)}
<h2>4. Huber epsilon 민감도 추가 진단</h2>
{dataframe_html(epsilon_df)}
<h2>5. 피처 그룹별 실제 기여도</h2>
{dataframe_html(group_df)}
<div class="note">
범주형 피처는 one-hot 기준 원계수를 그대로 비교하지 않고, 같은 원본 피처 안의 평균 범주 효과를 뺀
<code>centered_coef</code>와 <code>mean_abs_centered_contribution</code>을 해석 우선 기준으로 사용한다.
이는 최종 artifact의 예측식을 바꾸는 것이 아니라, 더미 변수 공선성으로 인한 계수 해석 왜곡을 줄이기 위한 보고 방식이다.
</div>
<h2>6. 개별 계수/기여도 상위 80개</h2>
{dataframe_html(coef_df[["encoded_feature","raw_feature","feature_group","coef","centered_coef","original_unit_coef","active_rate","mean_abs_centered_contribution","mean_centered_contribution","coef_direction","centered_direction","rank_by_centered_abs_contribution"]], 80)}
<h2>7. 샘플별 예측 설명</h2>
{dataframe_html(sample_df)}
</body></html>"""


def render_markdown(
    audit: pd.DataFrame,
    metric_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    epsilon_df: pd.DataFrame,
    group_df: pd.DataFrame,
    coef_df: pd.DataFrame,
) -> str:
    top_coef = coef_df[
        [
            "encoded_feature",
            "raw_feature",
            "feature_group",
            "coef",
            "centered_coef",
            "original_unit_coef",
            "active_rate",
            "mean_abs_centered_contribution",
            "mean_centered_contribution",
            "rank_by_centered_abs_contribution",
        ]
    ].head(30)
    return "\n\n".join(
        [
            "# Warm Huber 해석 감사 보고서",
            f"- 작성일: `{date.today().isoformat()}`",
            "- 결론: 기존 Warm 해석 산출물은 최종 artifact와 피처셋이 불일치하므로, 최종 Warm Huber 설명 근거로 그대로 쓰기 어렵다.",
            "- 보정: 최종 artifact `data/track6/artifacts/track6_warm_huber.joblib`를 직접 불러와 계수, 기여도, Huber outlier 진단을 재산출했다.",
            "- 해석 기준: 범주형 피처는 one-hot 원계수 대신 같은 원본 피처 안의 평균 범주 효과를 뺀 centered 기여도를 우선 사용한다.",
            "- 재실험 판단: 성능 관점에서는 즉시 모델 전체를 재실험할 근거는 약하다. 다만 `epsilon=1.1`은 validation MdAPE가 낮지만 수렴 실패와 test p95 악화가 있어, 별도 안정성 실험 후보로만 둔다.",
            "## 1. 피처셋 일치성 감사\n" + table_markdown(audit),
            "## 2. 최종 artifact 성능 재확인\n" + table_markdown(metric_df),
            "## 3. Huber outlier 진단\n" + table_markdown(outlier_df),
            "## 4. Huber epsilon 민감도 추가 진단\n" + table_markdown(epsilon_df),
            "## 5. 피처 그룹별 실제 기여도\n" + table_markdown(group_df),
            "## 6. 계수/기여도 상위 30개\n" + table_markdown(top_coef),
        ]
    ) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    model = joblib.load(ARTIFACT)

    train_val = combine_train_validation()
    test = read_pair(FEATURE_DIR / "track6_test_warm_warm_features.csv", LABEL_DIR / "track6_test_warm_labels.csv")

    pred_train_val = model.predict(clean_x(train_val))
    pred_test = model.predict(clean_x(test))
    metric_df = pd.DataFrame(
        [
            {"split": "train+validation(final artifact fit data)", **metrics(train_val, pred_train_val)},
            {"split": "test_warm", **metrics(test, pred_test)},
        ]
    )
    outlier_df = pd.DataFrame(
        [
            huber_outlier_summary(model, train_val, "train+validation"),
            huber_outlier_summary(model, test, "test_warm"),
        ]
    )
    epsilon_df = epsilon_sensitivity()
    contribution, _x_test, contributions = contribution_table(model, test)
    coef = coefficient_table(model, contribution)
    group = group_summary(coef)
    samples = sample_explanations(model, test, contributions, pred_test)
    audit = feature_alignment_audit()

    audit.to_csv(OUT / "warm_huber_feature_alignment_audit.csv", index=False)
    metric_df.to_csv(OUT / "warm_huber_final_artifact_metrics.csv", index=False)
    outlier_df.to_csv(OUT / "warm_huber_outlier_diagnostics.csv", index=False)
    epsilon_df.to_csv(OUT / "warm_huber_epsilon_sensitivity.csv", index=False)
    coef.to_csv(OUT / "warm_huber_final_coefficients_contributions.csv", index=False)
    group.to_csv(OUT / "warm_huber_feature_group_contribution_summary.csv", index=False)
    samples.to_csv(OUT / "warm_huber_sample_explanations.csv", index=False)

    html_text = render_html(audit, metric_df, outlier_df, epsilon_df, group, coef, samples)
    md_text = render_markdown(audit, metric_df, outlier_df, epsilon_df, group, coef)
    (DOC_DIR / "warm_huber_interpretability_audit_report.html").write_text(html_text, encoding="utf-8")
    (DOC_DIR / "warm_huber_interpretability_audit_report.md").write_text(md_text, encoding="utf-8")
    print(f"wrote {DOC_DIR / 'warm_huber_interpretability_audit_report.html'}")
    print(f"wrote {DOC_DIR / 'warm_huber_interpretability_audit_report.md'}")
    print(f"wrote outputs under {OUT}")


if __name__ == "__main__":
    main()
