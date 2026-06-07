#!/usr/bin/env python3
"""Generate interpretability artifacts for Track6 final Warm/Cold candidates."""
from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "experiments" / "track6" / "FINAL_model_interpretability"
SPLIT_ROOT = REPO / "data" / "track6_split_with_year_type_edition_size_artist_name"
SEED = 20260528
NEAR_ZERO_COEF_THRESHOLD = 0.01

WARM_FEATURES = [
    "artist_name_ko",
    "width_cm",
    "height_cm",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_log_is_missing",
]
WARM_NUMERIC = [
    "width_cm",
    "height_cm",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_log_is_missing",
]
COLD_FEATURES = [
    "ln_estimated_ho",
    "nant_material_idx",
    "nant_tool",
    "nant_support",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_is_p1",
]
COLD_NUMERIC = [
    "ln_estimated_ho",
    "nant_material_idx",
    "artist_meta_total_works",
    "artist_meta_for_sale_works",
    "artist_meta_followers",
    "artist_meta_is_p1",
]


def read_join(feature_path: Path, label_path: Path, features: list[str]) -> pd.DataFrame:
    x = pd.read_csv(feature_path, low_memory=False)
    missing = [c for c in features if c not in x.columns]
    if missing:
        raise ValueError(f"{feature_path} missing columns: {missing}")
    y = pd.read_csv(label_path, low_memory=False)
    df = x.merge(y[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def normalize(df: pd.DataFrame, features: list[str], numeric: list[str]) -> pd.DataFrame:
    out = df.copy()
    numeric_set = set(numeric)
    for col in features:
        if col in numeric_set:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__missing__").replace({"": "__missing__"})
    return out


def preprocessor(features: list[str], numeric: list[str]) -> ColumnTransformer:
    num_cols = [c for c in numeric if c in features]
    cat_cols = [c for c in features if c not in num_cols]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = []
    if cat_cols:
        transformers.append(("cat", encoder, cat_cols))
    if num_cols:
        transformers.append(("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols))
    return ColumnTransformer(transformers)


def feature_names(pre: ColumnTransformer) -> list[str]:
    names: list[str] = []
    for name, transformer, cols in pre.transformers_:
        if name == "remainder":
            continue
        if name == "cat":
            enc = transformer
            values = enc.get_feature_names_out(cols)
            names.extend([str(v) for v in values])
        elif name == "num":
            names.extend([str(c) for c in cols])
    return names


def calc_metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def warm_huber() -> dict[str, object]:
    train = read_join(
        SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
        SPLIT_ROOT / "labels" / "track6_train_labels.csv",
        WARM_FEATURES,
    )
    test = read_join(
        SPLIT_ROOT / "features" / "warm" / "track6_test_warm_warm_features.csv",
        SPLIT_ROOT / "labels" / "track6_test_warm_labels.csv",
        WARM_FEATURES,
    )
    train = normalize(train, WARM_FEATURES, WARM_NUMERIC)
    test = normalize(test, WARM_FEATURES, WARM_NUMERIC)
    pre = preprocessor(WARM_FEATURES, WARM_NUMERIC)
    x_train = pre.fit_transform(train[WARM_FEATURES])
    x_test = pre.transform(test[WARM_FEATURES])
    model = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)
    model.fit(x_train, train["ln_price_krw"].to_numpy())
    pred = model.predict(x_test)
    metrics = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)
    names = feature_names(pre)
    coef = pd.DataFrame({"feature": names, "coef": model.coef_})
    coef["direction"] = np.where(coef["coef"] >= 0, "예측가격 상승 방향", "예측가격 하락 방향")
    coef["abs_coef"] = coef["coef"].abs()
    coef["rank_abs"] = coef["abs_coef"].rank(ascending=False, method="min").astype(int)
    coef = coef.sort_values(["rank_abs", "feature"]).reset_index(drop=True)
    coef.to_csv(OUT_DIR / "outputs" / "warm_huber_coefficients.csv", index=False)

    coef_importance = coef[["feature", "coef", "abs_coef", "direction", "rank_abs"]].copy()
    total_abs = float(coef_importance["abs_coef"].sum()) or 1.0
    coef_importance["importance_pct"] = coef_importance["abs_coef"] / total_abs * 100.0
    coef_importance = coef_importance.rename(columns={"rank_abs": "rank"})
    coef_importance.to_csv(OUT_DIR / "outputs" / "warm_huber_coefficient_importance.csv", index=False)

    contributions = x_test * model.coef_
    contribution = pd.DataFrame({
        "feature": names,
        "mean_abs_contribution": np.abs(contributions).mean(axis=0),
        "mean_contribution": contributions.mean(axis=0),
    })
    contribution["direction"] = np.where(
        contribution["mean_contribution"] >= 0,
        "평균적으로 예측가격 상승",
        "평균적으로 예측가격 하락",
    )
    contribution = contribution.sort_values("mean_abs_contribution", ascending=False).reset_index(drop=True)
    contribution["rank"] = np.arange(1, len(contribution) + 1)
    contribution.to_csv(OUT_DIR / "outputs" / "warm_huber_linear_contribution_summary.csv", index=False)

    sample_n = min(50, x_test.shape[0])
    sample_idx = np.linspace(0, x_test.shape[0] - 1, sample_n, dtype=int)
    row_ids = test["_track6_row_id"].to_numpy()[sample_idx]
    pred_sample = pred[sample_idx]
    actual_price = test["price_krw"].to_numpy()[sample_idx]
    explanation_rows = []
    for i, row_id in enumerate(row_ids):
        vals = contributions[sample_idx[i]]
        order_up = np.argsort(vals)[::-1][:3]
        order_down = np.argsort(vals)[:3]
        explanation_rows.append({
            "_track6_row_id": row_id,
            "pred_price": float(np.exp(pred_sample[i])),
            "actual_price": float(actual_price[i]),
            "ape": float(abs(np.exp(pred_sample[i]) - actual_price[i]) / actual_price[i]),
            "top_up_features": ", ".join(f"{names[j]}({vals[j]:.4f})" for j in order_up),
            "top_down_features": ", ".join(f"{names[j]}({vals[j]:.4f})" for j in order_down),
        })
    explanation = pd.DataFrame(explanation_rows)
    explanation.to_csv(OUT_DIR / "outputs" / "warm_huber_sample_linear_explanations.csv", index=False)

    numeric_coef = coef[coef["feature"].isin(WARM_NUMERIC)].copy()
    numeric_coef.to_csv(OUT_DIR / "outputs" / "warm_huber_numeric_coefficients.csv", index=False)

    artist_coef = coef[coef["feature"].str.startswith("artist_name_ko_")].copy()
    artist_coef["artist_name_ko"] = artist_coef["feature"].str.replace("artist_name_ko_", "", regex=False)
    counts = train["artist_name_ko"].value_counts().rename_axis("artist_name_ko").reset_index(name="train_count")
    artist_coef = artist_coef.merge(counts, on="artist_name_ko", how="left")
    artist_coef.to_csv(OUT_DIR / "outputs" / "warm_huber_artist_coefficients.csv", index=False)
    return {
        "metrics": metrics,
        "coef": coef,
        "importance": coef_importance,
        "contribution": contribution,
        "explanation": explanation,
        "numeric_coef": numeric_coef,
        "artist_coef": artist_coef,
    }


def cold_catboost() -> dict[str, object]:
    train = read_join(
        SPLIT_ROOT / "features" / "warm" / "track6_train_warm_features.csv",
        SPLIT_ROOT / "labels" / "track6_train_labels.csv",
        COLD_FEATURES,
    )
    test = read_join(
        SPLIT_ROOT / "features" / "cold" / "track6_test_cold_cold_features.csv",
        SPLIT_ROOT / "labels" / "track6_test_cold_labels.csv",
        COLD_FEATURES,
    )
    train = normalize(train, COLD_FEATURES, COLD_NUMERIC)
    test = normalize(test, COLD_FEATURES, COLD_NUMERIC)
    pre = preprocessor(COLD_FEATURES, COLD_NUMERIC)
    x_train = pre.fit_transform(train[COLD_FEATURES])
    x_test = pre.transform(test[COLD_FEATURES])
    names = feature_names(pre)
    model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=220,
        learning_rate=0.05,
        depth=5,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(x_train, train["ln_price_krw"].to_numpy())
    pred = model.predict(x_test)
    metrics = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)

    importance = pd.DataFrame({"feature": names, "importance": model.get_feature_importance()})
    importance = importance.sort_values("importance", ascending=False).reset_index(drop=True)
    importance["rank"] = np.arange(1, len(importance) + 1)
    importance.to_csv(OUT_DIR / "outputs" / "cold_catboost_feature_importance.csv", index=False)

    sample_n = min(1000, x_test.shape[0])
    sample_idx = np.linspace(0, x_test.shape[0] - 1, sample_n, dtype=int)
    shap_values = model.get_feature_importance(Pool(x_test[sample_idx], label=test["ln_price_krw"].to_numpy()[sample_idx]), type="ShapValues")
    shap_feature = shap_values[:, :-1]
    shap_df = pd.DataFrame({
        "feature": names,
        "mean_abs_shap": np.abs(shap_feature).mean(axis=0),
        "mean_shap": shap_feature.mean(axis=0),
    })
    shap_df["direction"] = np.where(shap_df["mean_shap"] >= 0, "평균적으로 예측가격 상승", "평균적으로 예측가격 하락")
    shap_df = shap_df.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    shap_df["rank"] = np.arange(1, len(shap_df) + 1)
    shap_df.to_csv(OUT_DIR / "outputs" / "cold_catboost_shap_summary.csv", index=False)

    row_ids = test["_track6_row_id"].to_numpy()[sample_idx]
    pred_sample = pred[sample_idx]
    actual_log = test["ln_price_krw"].to_numpy()[sample_idx]
    actual_price = test["price_krw"].to_numpy()[sample_idx]
    rows = []
    for i, row_id in enumerate(row_ids[:50]):
        vals = shap_feature[i]
        order_up = np.argsort(vals)[::-1][:3]
        order_down = np.argsort(vals)[:3]
        rows.append({
            "_track6_row_id": row_id,
            "pred_price": float(np.exp(pred_sample[i])),
            "actual_price": float(actual_price[i]),
            "ape": float(abs(np.exp(pred_sample[i]) - actual_price[i]) / actual_price[i]),
            "top_up_features": ", ".join(f"{names[j]}({vals[j]:.4f})" for j in order_up),
            "top_down_features": ", ".join(f"{names[j]}({vals[j]:.4f})" for j in order_down),
        })
    explanation = pd.DataFrame(rows)
    explanation.to_csv(OUT_DIR / "outputs" / "cold_catboost_sample_shap_explanations.csv", index=False)
    return {"metrics": metrics, "importance": importance, "shap": shap_df, "explanation": explanation}


def fmt(v: float) -> str:
    return f"{v:.4f}"


def table_html(df: pd.DataFrame, cols: list[str], n: int = 12) -> str:
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    rows = []
    for _, row in df.head(n).iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                v = f"{v:.4f}"
            cells.append(f"<td>{html.escape(str(v))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def render_html(warm: dict[str, object], cold: dict[str, object]) -> None:
    warm_metrics = warm["metrics"]
    cold_metrics = cold["metrics"]
    warm_numeric_coef = warm["numeric_coef"].copy()
    warm_numeric_main = warm_numeric_coef[warm_numeric_coef["abs_coef"] >= NEAR_ZERO_COEF_THRESHOLD].copy()
    warm_numeric_near_zero = warm_numeric_coef[warm_numeric_coef["abs_coef"] < NEAR_ZERO_COEF_THRESHOLD].copy()
    content = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 최종 후보 모델 해석 산출물</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #17231c; }}
    section {{ background: #fffdf7; border: 1px solid #d5c4aa; border-radius: 18px; padding: 20px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border: 1px solid #d5c4aa; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #e6d8c2; }}
    code {{ background: #efe6d4; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <h1>Track6 최종 후보 모델 해석 산출물</h1>
  <section>
    <h2>Warm Huber 피처 중요도 / 선형 기여도 해석</h2>
    <p>성능: MdAPE <code>{fmt(warm_metrics['MdAPE'])}</code>, p95_APE <code>{fmt(warm_metrics['p95_APE'])}</code>, Within_30 <code>{fmt(warm_metrics['Within_30'])}</code>, RMSE_log <code>{fmt(warm_metrics['RMSE_log'])}</code></p>
    <p>Huber는 선형 모델이므로 CatBoost의 TreeSHAP 대신 계수 크기와 <code>입력값 × 계수</code>를 중요도와 기여도로 봅니다. 양수는 예측 로그가격을 올리는 방향, 음수는 낮추는 방향입니다.</p>
    <h3>계수 기반 피처 중요도 상위</h3>
    {table_html(warm['importance'], ['rank', 'feature', 'importance_pct', 'coef', 'direction'], 20)}
    <h3>평균 선형 기여도 상위</h3>
    {table_html(warm['contribution'], ['rank', 'feature', 'mean_abs_contribution', 'mean_contribution', 'direction'], 20)}
    <h3>개별 예측 설명 샘플</h3>
    {table_html(warm['explanation'], ['_track6_row_id', 'pred_price', 'actual_price', 'ape', 'top_up_features', 'top_down_features'], 10)}
    <h2>Warm Huber 계수 상세</h2>
    <p><code>abs_coef &lt; {NEAR_ZERO_COEF_THRESHOLD}</code>인 피처는 HTML 요약표에서 주요 계수로 보지 않습니다. 원본 CSV에는 남겨 감사와 재현에 사용합니다.</p>
    <h3>숫자형 피처 계수: 주요 해석 대상</h3>
    {table_html(warm_numeric_main, ['feature', 'coef', 'direction', 'abs_coef', 'rank_abs'], 20)}
    <h3>숫자형 피처 계수: 거의 0이라 해석 제외</h3>
    <p>아래 피처는 이 Huber 계수 기준으로는 가격을 직접 움직이는 영향이 거의 없습니다. 다만 성능 비교에서 보조 피처로 남긴 경우가 있으므로, 제거 여부는 계수만이 아니라 ablation 결과와 함께 판단합니다.</p>
    {table_html(warm_numeric_near_zero, ['feature', 'coef', 'direction', 'abs_coef', 'rank_abs'], 20)}
    <h3>작가명 계수 상위</h3>
    {table_html(warm['artist_coef'].sort_values('coef', ascending=False), ['artist_name_ko', 'coef', 'direction', 'train_count'], 12)}
    <h3>작가명 계수 하위</h3>
    {table_html(warm['artist_coef'].sort_values('coef', ascending=True), ['artist_name_ko', 'coef', 'direction', 'train_count'], 12)}
  </section>
  <section>
    <h2>Cold CatBoost 피처 중요도 / SHAP 해석</h2>
    <p>성능: MdAPE <code>{fmt(cold_metrics['MdAPE'])}</code>, p95_APE <code>{fmt(cold_metrics['p95_APE'])}</code>, Within_30 <code>{fmt(cold_metrics['Within_30'])}</code>, RMSE_log <code>{fmt(cold_metrics['RMSE_log'])}</code></p>
    <p>피처 중요도는 모델 전체에서 많이 사용된 정도입니다. SHAP은 개별 예측에서 가격을 올리거나 낮춘 정도를 설명합니다.</p>
    <h3>피처 중요도 상위</h3>
    {table_html(cold['importance'], ['rank', 'feature', 'importance'], 20)}
    <h3>평균 SHAP 상위</h3>
    {table_html(cold['shap'], ['rank', 'feature', 'mean_abs_shap', 'mean_shap', 'direction'], 20)}
    <h3>개별 예측 설명 샘플</h3>
    {table_html(cold['explanation'], ['_track6_row_id', 'pred_price', 'actual_price', 'ape', 'top_up_features', 'top_down_features'], 10)}
  </section>
</body>
</html>
"""
    (OUT_DIR / "outputs" / "interpretability_report.html").write_text(content, encoding="utf-8")


def main() -> None:
    (OUT_DIR / "outputs").mkdir(parents=True, exist_ok=True)
    manifest = {
        "purpose": "Track6 final Warm/Cold candidate interpretability artifacts",
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "warm_model": "Huber",
        "warm_features": WARM_FEATURES,
        "cold_model": "CatBoost",
        "cold_features": COLD_FEATURES,
    }
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    warm = warm_huber()
    cold = cold_catboost()
    render_html(warm, cold)
    print("warm", warm["metrics"])
    print("cold", cold["metrics"])
    print("outputs", OUT_DIR / "outputs")


if __name__ == "__main__":
    main()
