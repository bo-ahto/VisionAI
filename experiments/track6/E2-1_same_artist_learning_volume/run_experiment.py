from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LinearRegression, Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


EXP_DIR = Path("experiments/track6/E2-1_same_artist_learning_volume")
SPLIT_ROOT = Path("data/track6_split_with_year_type_edition_size_artist_name")
FEATURE_ROOT = SPLIT_ROOT / "features" / "warm"
LABEL_ROOT = SPLIT_ROOT / "labels"

TRAIN_FEATURES = FEATURE_ROOT / "track6_train_warm_features.csv"
TEST_FEATURES = FEATURE_ROOT / "track6_test_warm_warm_features.csv"
TRAIN_LABELS = LABEL_ROOT / "track6_train_labels.csv"
TEST_LABELS = LABEL_ROOT / "track6_test_warm_labels.csv"

RANDOM_STATE = 42
CAPS = [5, 10, 20, 30]
MIN_TRAIN_COUNT_FOR_FIXED_TEST = max(CAPS)

# 학습량 효과만 보기 위해 피처는 Warm 기본 후보로 고정한다.
# artist_works_log는 이번 실험의 비교 대상이므로 모델 입력에서 제외한다.
NUMERIC_FEATURES = ["width_cm", "height_cm", "log_area", "aspect_ratio"]
CATEGORICAL_FEATURES = ["artist_name_ko"]
TARGET = "ln_price_krw"
ID_COL = "_track6_row_id"


def load_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_x = pd.read_csv(TRAIN_FEATURES)
    test_x = pd.read_csv(TEST_FEATURES)
    train_y = pd.read_csv(TRAIN_LABELS)[[ID_COL, "price_krw", TARGET]]
    test_y = pd.read_csv(TEST_LABELS)[[ID_COL, "price_krw", TARGET]]

    train = train_x.merge(train_y, on=ID_COL, how="inner")
    test = test_x.merge(test_y, on=ID_COL, how="inner")
    return train, test


def select_fixed_artists(train: pd.DataFrame, test: pd.DataFrame) -> list[str]:
    counts = train["artist_name_ko"].dropna().value_counts()
    enough_train = set(counts[counts >= MIN_TRAIN_COUNT_FOR_FIXED_TEST].index)
    test_artists = set(test["artist_name_ko"].dropna().unique())
    return sorted(enough_train & test_artists)


def sample_train_by_artist(train: pd.DataFrame, artists: list[str], cap: int) -> pd.DataFrame:
    pool = train[train["artist_name_ko"].isin(artists)].copy()
    parts = []
    for artist, group in pool.groupby("artist_name_ko", sort=True):
        parts.append(group.sample(n=cap, random_state=RANDOM_STATE))
    return pd.concat(parts, ignore_index=True).sort_values(ID_COL).reset_index(drop=True)


def build_model(model_name: str) -> Pipeline:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="__missing__")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ]
    )
    if model_name == "Huber":
        estimator = HuberRegressor(max_iter=1000)
    elif model_name == "Linear Regression":
        estimator = LinearRegression()
    elif model_name == "Ridge":
        estimator = Ridge(alpha=1.0)
    else:
        raise ValueError(f"Unknown model: {model_name}")
    return Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])


def calc_metrics(y_log_true: np.ndarray, y_log_pred: np.ndarray, y_price_true: np.ndarray) -> dict:
    y_price_pred = np.exp(y_log_pred)
    ape = np.abs(y_price_pred - y_price_true) / np.maximum(y_price_true, 1.0)
    return {
        "R2": r2_score(y_log_true, y_log_pred),
        "RMSE_log": math.sqrt(np.mean((y_log_pred - y_log_true) ** 2)),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.percentile(ape, 95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "MAPE": float(np.mean(ape)),
    }


def write_html(summary: pd.DataFrame, per_artist: pd.DataFrame, meta: dict) -> None:
    rows = []
    for _, r in summary.iterrows():
        rows.append(
            "<tr>"
            f"<td>{int(r['train_per_artist'])}</td>"
            f"<td>{r['model_name']}</td>"
            f"<td>{r['MdAPE']:.4f}</td>"
            f"<td>{r['p95_APE']:.4f}</td>"
            f"<td>{r['Within_30']:.4f}</td>"
            f"<td>{r['RMSE_log']:.4f}</td>"
            f"<td>{r['R2']:.4f}</td>"
            "</tr>"
        )

    best = summary.sort_values(["MdAPE", "p95_APE", "RMSE_log"]).iloc[0]
    artist_rows = []
    for _, r in per_artist.head(30).iterrows():
        artist_rows.append(
            "<tr>"
            f"<td>{r['artist_name_ko']}</td>"
            f"<td>{int(r['train_per_artist'])}</td>"
            f"<td>{r['model_name']}</td>"
            f"<td>{r['MdAPE']:.4f}</td>"
            f"<td>{int(r['n_test'])}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>E2-1 같은 작가 학습량 비교 실험</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5efe3;color:#17211d;margin:0;padding:32px;line-height:1.65}}
    .wrap{{max-width:1180px;margin:0 auto}}
    section{{background:#fffaf0;border:1px solid #d7c39e;border-radius:18px;padding:24px;margin:20px 0}}
    h1{{font-size:38px;margin:0 0 10px}}
    h2{{border-left:6px solid #1f3b5c;padding-left:12px}}
    table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}}
    th,td{{border:1px solid #cdbb9a;padding:9px;vertical-align:top}}
    th{{background:#e4d6bf;text-align:left}}
    code{{background:#eee5d5;border-radius:5px;padding:1px 5px}}
  </style>
</head>
<body><div class="wrap">
  <section>
    <h1>E2-1 같은 작가 학습량 비교 실험</h1>
    <ul>
      <li>가설: 같은 작가라도 학습 작품 수가 많아질수록 Warm 예측이 안정적일 수 있다.</li>
      <li>핵심 통제: 테스트 작가와 테스트 작품은 고정하고, 학습 작품 수만 바꾼다.</li>
      <li>대상 작가: train에 최소 {MIN_TRAIN_COUNT_FOR_FIXED_TEST}개 이상 있고 Warm test에도 있는 작가 {meta['n_artists']}명</li>
      <li>고정 테스트 작품 수: {meta['n_test']}건</li>
      <li>사용 피처: <code>{', '.join(CATEGORICAL_FEATURES + NUMERIC_FEATURES)}</code></li>
      <li>제외 피처: <code>artist_works_log</code>는 학습량 효과를 직접 보기 위해 입력에서 제외</li>
    </ul>
  </section>
  <section>
    <h2>결론</h2>
    <ul>
      <li>최고 결과: 학습량 {int(best['train_per_artist'])}개/작가, {best['model_name']}, MdAPE {best['MdAPE']:.4f}</li>
      <li>이 실험은 작가별 학습량 자체가 예측 안정성에 미치는 영향을 보는 실험이다.</li>
      <li>학습량이 늘어도 성능이 일관되게 좋아지지 않으면, 작품 수는 예측 피처보다 신뢰도/라우팅 기준으로 쓰는 것이 적절하다.</li>
    </ul>
  </section>
  <section>
    <h2>전체 결과</h2>
    <table>
      <thead><tr><th>작가당 학습 수</th><th>모델</th><th>MdAPE</th><th>p95_APE</th><th>Within_30</th><th>RMSE_log</th><th>R2</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </section>
  <section>
    <h2>작가별 결과 일부</h2>
    <p>작가별 MdAPE가 큰 순서 일부입니다. 특정 작가에서 학습량 증가가 실제 안정화로 이어지는지 확인할 때 사용합니다.</p>
    <table>
      <thead><tr><th>작가</th><th>작가당 학습 수</th><th>모델</th><th>MdAPE</th><th>테스트 수</th></tr></thead>
      <tbody>{''.join(artist_rows)}</tbody>
    </table>
  </section>
</div></body></html>"""
    (EXP_DIR / "outputs" / "result_sheet.html").write_text(html, encoding="utf-8")


def main() -> None:
    for p in [TRAIN_FEATURES, TEST_FEATURES, TRAIN_LABELS, TEST_LABELS]:
        shutil.copy2(p, EXP_DIR / "source_data" / p.name)

    train, test = load_split()
    artists = select_fixed_artists(train, test)
    fixed_test = test[test["artist_name_ko"].isin(artists)].copy()

    source_meta = {
        "experiment_id": "E2-1",
        "description": "same artist learning volume comparison",
        "caps": CAPS,
        "n_artists": len(artists),
        "n_test": int(len(fixed_test)),
        "fixed_artists": artists,
        "features": CATEGORICAL_FEATURES + NUMERIC_FEATURES,
        "excluded_features": ["artist_works_log"],
        "source_split": str(SPLIT_ROOT),
    }
    (EXP_DIR / "outputs" / "experiment_manifest.json").write_text(
        json.dumps(source_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    fixed_test[[ID_COL] + CATEGORICAL_FEATURES + NUMERIC_FEATURES].to_csv(
        EXP_DIR / "data" / "fixed_test_features.csv", index=False
    )
    fixed_test[[ID_COL, "price_krw", TARGET]].to_csv(EXP_DIR / "data" / "fixed_test_labels.csv", index=False)

    summary_rows = []
    pred_rows = []
    per_artist_rows = []

    for cap in CAPS:
        train_cap = sample_train_by_artist(train, artists, cap)
        train_cap[[ID_COL] + CATEGORICAL_FEATURES + NUMERIC_FEATURES].to_csv(
            EXP_DIR / "data" / f"train_cap_{cap}_features.csv", index=False
        )
        train_cap[[ID_COL, "price_krw", TARGET]].to_csv(EXP_DIR / "data" / f"train_cap_{cap}_labels.csv", index=False)

        for model_name in ["Huber", "Linear Regression", "Ridge"]:
            model = build_model(model_name)
            model.fit(train_cap[CATEGORICAL_FEATURES + NUMERIC_FEATURES], train_cap[TARGET].to_numpy())
            pred_log = model.predict(fixed_test[CATEGORICAL_FEATURES + NUMERIC_FEATURES])
            metrics = calc_metrics(
                fixed_test[TARGET].to_numpy(),
                pred_log,
                fixed_test["price_krw"].to_numpy(),
            )
            row = {
                "experiment_id": "E2-1",
                "train_per_artist": cap,
                "model_name": model_name,
                "n_artists": len(artists),
                "n_train": len(train_cap),
                "n_test": len(fixed_test),
                **metrics,
            }
            summary_rows.append(row)

            pred_df = fixed_test[[ID_COL, "artist_name_ko", "price_krw", TARGET]].copy()
            pred_df["train_per_artist"] = cap
            pred_df["model_name"] = model_name
            pred_df["pred_ln_price_krw"] = pred_log
            pred_df["pred_price_krw"] = np.exp(pred_log)
            pred_df["APE"] = np.abs(pred_df["pred_price_krw"] - pred_df["price_krw"]) / np.maximum(
                pred_df["price_krw"], 1.0
            )
            pred_rows.append(pred_df)

            for artist, g in pred_df.groupby("artist_name_ko"):
                per_artist_rows.append(
                    {
                        "artist_name_ko": artist,
                        "train_per_artist": cap,
                        "model_name": model_name,
                        "n_test": len(g),
                        "MdAPE": float(g["APE"].median()),
                        "p95_APE": float(np.percentile(g["APE"], 95)),
                        "Within_30": float((g["APE"] <= 0.30).mean()),
                    }
                )

    summary = pd.DataFrame(summary_rows).sort_values(["model_name", "train_per_artist"])
    predictions = pd.concat(pred_rows, ignore_index=True)
    per_artist = pd.DataFrame(per_artist_rows).sort_values(["MdAPE"], ascending=False)

    summary.to_csv(EXP_DIR / "outputs" / "metrics_by_cap.csv", index=False)
    predictions.to_csv(EXP_DIR / "outputs" / "predictions.csv", index=False)
    per_artist.to_csv(EXP_DIR / "outputs" / "per_artist_metrics.csv", index=False)

    # 모델별로 학습량 증가 추세를 보기 쉽게 별도 요약을 만든다.
    trend = (
        summary.pivot(index="train_per_artist", columns="model_name", values="MdAPE")
        .reset_index()
        .sort_values("train_per_artist")
    )
    trend.to_csv(EXP_DIR / "outputs" / "mdape_trend_by_model.csv", index=False)

    write_html(summary.sort_values(["train_per_artist", "MdAPE"]), per_artist, source_meta)


if __name__ == "__main__":
    main()
