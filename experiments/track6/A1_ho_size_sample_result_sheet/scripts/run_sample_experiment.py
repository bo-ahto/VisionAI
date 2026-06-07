#!/usr/bin/env python3
"""Track6 A1 Ho/Size full split result-sheet experiment.

This experiment follows the spreadsheet-style template:
- Warm models: A=Huber, B=Linear Regression, C=Ridge
- Cold models: D=Huber, E=Quantile-LAD, F=LightGBM
- Variable blocks: Ho, ln Ho, Size, ln Size

Data policy:
- Training uses the fixed Track6 train split only.
- Warm evaluation uses the fixed Track6 warm test split only.
- Cold evaluation uses the fixed Track6 cold test split only.
- Feature files and label files are read separately, then joined by
  `_track6_row_id` only inside this experiment script.
- No sampling is applied in the official run. All rows that have the required
  A1 features and labels are used.
"""
from __future__ import annotations

import html
import json
import math
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import HuberRegressor, LinearRegression, QuantileRegressor, Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments" / "track6" / "A1_ho_size_sample_result_sheet"
DATA_DIR = EXP_DIR / "data"
OUT_DIR = EXP_DIR / "outputs"
LOG_DIR = EXP_DIR / "logs"

SEED = 20260521

# 학습 기준:
# - Track6에서 이미 고정한 train split만 사용한다.
# - Warm용/Cold용 학습 파일을 따로 만들지 않고 같은 train split으로 학습한다.
# - Warm/Cold 차이는 평가 대상과 사용 모델/피처 정책에서 구분한다.
TRAIN_FEATURES = REPO / "data" / "track6_split" / "features" / "warm" / "track6_train_warm_features.csv"
TRAIN_LABELS = REPO / "data" / "track6_split" / "labels" / "track6_train_labels.csv"

# Warm 평가 기준:
# - 학습 데이터에 등장한 작가의 미사용 작품을 평가한다.
# - 이 실험에서는 A1 크기 변수만 보므로 작가명은 피처로 쓰지 않는다.
WARM_FEATURES = REPO / "data" / "track6_split" / "features" / "warm" / "track6_test_warm_warm_features.csv"
WARM_LABELS = REPO / "data" / "track6_split" / "labels" / "track6_test_warm_labels.csv"

# Cold 평가 기준:
# - 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 평가한다.
# - Cold 평가는 신규 작가 상황이므로 작가명 피처를 쓰지 않는다.
COLD_FEATURES = REPO / "data" / "track6_split" / "features" / "cold" / "track6_test_cold_cold_features.csv"
COLD_LABELS = REPO / "data" / "track6_split" / "labels" / "track6_test_cold_labels.csv"

HO_TABLE_F = {
    0: 180,
    1: 364,
    2: 520,
    3: 727,
    4: 1084,
    5: 1167,
    6: 1338,
    8: 1818,
    10: 2412,
    12: 2757,
    15: 3478,
    20: 4304,
    25: 5323,
    30: 5858,
    40: 7320,
    50: 9128,
    60: 12636,
    80: 16918,
    100: 21245,
    120: 25740,
    150: 33894,
    200: 43980,
    300: 67060,
    500: 121898,
}

VARIABLE_BLOCKS = [
    {
        "name": "Ho",
        "feature": "estimated_ho",
        "description": "작품 면적을 가장 가까운 F형 호수로 환산한 값",
    },
    {
        "name": "ln Ho",
        "feature": "ln_estimated_ho",
        "description": "호수에 로그 변환을 적용한 값",
    },
    {
        "name": "Size",
        "feature": "area_cm2",
        "description": "가로 x 세로로 계산한 실제 면적(cm²)",
    },
    {
        "name": "ln Size",
        "feature": "log_area",
        "description": "면적에 로그 변환을 적용한 값",
    },
]

MODEL_ROWS = [
    {"code": "A", "scope": "Warm", "name": "Huber", "kind": "huber"},
    {"code": "B", "scope": "Warm", "name": "Linear Regression", "kind": "linear"},
    {"code": "C", "scope": "Warm", "name": "Ridge", "kind": "ridge"},
    {"code": "D", "scope": "Cold", "name": "Huber", "kind": "huber"},
    {"code": "E", "scope": "Cold", "name": "Quantile-LAD", "kind": "quantile"},
    {"code": "F", "scope": "Cold", "name": "LightGBM", "kind": "lightgbm"},
]


def area_to_ho(area: float) -> float:
    if not np.isfinite(area) or area <= 0:
        return np.nan
    return float(min(HO_TABLE_F, key=lambda ho: abs(float(HO_TABLE_F[ho]) - float(area))))


def load_join(features_path: Path, labels_path: Path) -> pd.DataFrame:
    """Read features and labels separately, then join by row key.

    Labels are needed for training targets and metric calculation, but they are
    not treated as model input features. The join key is `_track6_row_id`.
    """
    features = pd.read_csv(features_path, low_memory=False)
    labels = pd.read_csv(labels_path, low_memory=False)
    df = features.merge(labels[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    df["area_cm2"] = pd.to_numeric(df["area_cm2"], errors="coerce")
    df["log_area"] = pd.to_numeric(df["log_area"], errors="coerce")
    df["estimated_ho"] = df["area_cm2"].apply(area_to_ho)
    df["ln_estimated_ho"] = np.log(df["estimated_ho"].clip(lower=0.01))
    return df.dropna(subset=["price_krw", "ln_price_krw", "area_cm2", "log_area", "estimated_ho", "ln_estimated_ho"])


def use_full_split(df: pd.DataFrame) -> pd.DataFrame:
    """Use all valid rows from the fixed Track6 split.

    Rows with missing target price or missing A1 size features are already
    removed by `load_join`. No row-count cap or random sample is applied.
    """
    return df.sort_values("_track6_row_id").reset_index(drop=True)


def write_experiment_data_files(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["_track6_row_id", "estimated_ho", "ln_estimated_ho", "area_cm2", "log_area"]
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    files = {}
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        feature_path = DATA_DIR / f"{name}_features.csv"
        label_path = DATA_DIR / f"{name}_labels.csv"
        frame[cols].to_csv(feature_path, index=False)
        frame[label_cols].to_csv(label_path, index=False)
        files[f"{name}_features"] = str(feature_path.relative_to(REPO))
        files[f"{name}_labels"] = str(label_path.relative_to(REPO))
    return files


def build_model(kind: str) -> Pipeline | lgb.LGBMRegressor:
    if kind == "linear":
        model = LinearRegression()
    elif kind == "ridge":
        model = Ridge(alpha=1.0)
    elif kind == "huber":
        model = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)
    elif kind == "quantile":
        model = QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")
    elif kind == "lightgbm":
        return lgb.LGBMRegressor(
            objective="regression",
            n_estimators=120,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=30,
            random_state=SEED,
            verbosity=-1,
        )
    else:
        raise ValueError(f"unknown model kind: {kind}")

    return Pipeline(
        [
            ("preprocess", ColumnTransformer([("num", StandardScaler(), ["__feature__"])])),
            ("model", model),
        ]
    )


def fit_predict(kind: str, train: pd.DataFrame, test: pd.DataFrame, feature: str) -> np.ndarray:
    x_train = train[[feature]].rename(columns={feature: "__feature__"})
    x_test = test[[feature]].rename(columns={feature: "__feature__"})
    y_train = train["ln_price_krw"].to_numpy()
    model = build_model(kind)
    model.fit(x_train, y_train)
    pred_log = model.predict(x_test)
    return np.exp(pred_log)


def calc_metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_price: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.asarray(pred_price, dtype=float), 1_000.0, None)
    actual_price = np.asarray(actual_price, dtype=float)
    pred_log = np.log(pred_price)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "R2": float(r2_score(actual_log, pred_log)),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "MAPE": float(np.mean(ape)),
    }


def run_models(train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block in VARIABLE_BLOCKS:
        for model_spec in MODEL_ROWS:
            test = warm if model_spec["scope"] == "Warm" else cold
            pred = fit_predict(model_spec["kind"], train, test, block["feature"])
            m = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)
            rows.append(
                {
                    "experiment_id": "A1",
                    "variable_block": block["name"],
                    "feature": block["feature"],
                    "scope": model_spec["scope"],
                    "model_code": model_spec["code"],
                    "model_name": model_spec["name"],
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    **m,
                }
            )
    return pd.DataFrame(rows)


def fmt(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.4f}"


def render_html(results: pd.DataFrame, files: dict[str, str], manifest: dict) -> str:
    model_table = "".join(
        f"<tr><td>{m['scope']}</td><td>{m['code']}</td><td>{html.escape(m['name'])}</td></tr>" for m in MODEL_ROWS
    )
    source = manifest["source_files"]
    code_path = manifest["code_file"]
    prompt_path = manifest["prompt_file"]
    sections = []
    for block in VARIABLE_BLOCKS:
        sub = results[results["variable_block"].eq(block["name"])].copy()
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(r.model_code)}</td>"
            f"<td>{html.escape(r.scope)}</td>"
            f"<td>{html.escape(r.model_name)}</td>"
            f"<td>{fmt(r.R2)}</td>"
            f"<td>{fmt(r.MdAPE)}</td>"
            f"<td>{fmt(r.p95_APE)}</td>"
            f"<td>{fmt(r.Within_30)}</td>"
            f"<td>{fmt(r.Within_50)}</td>"
            f"<td>{fmt(r.MAPE)}</td>"
            "</tr>"
            for r in sub.itertuples()
        )
        sections.append(
            f"""
            <section class="block">
              <h2>실험 변수명: {html.escape(block['name'])}</h2>
              <p><strong>사용 피처:</strong> <code>{html.escape(block['feature'])}</code> · {html.escape(block['description'])}</p>
              <table>
                <thead><tr><th>모델 코드</th><th>분류</th><th>모델</th><th>R2</th><th>MdAPE</th><th>p95 APE</th><th>Within-30</th><th>Within-50</th><th>MAPE</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </section>
            """
        )
    file_items = "".join(f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>" for k, v in files.items())
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 A1 Ho/Size 전체 데이터 실험 결과</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card, .block {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    h1 {{ margin-top: 0; font-size: 36px; }}
    h2 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    ul {{ line-height: 1.8; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Track6 A1 Ho/Size 전체 데이터 실험 결과</h1>
    <ul>
      <li>목적: Ho / ln Ho / Size / ln Size 변수별 가격 예측 효과를 Warm/Cold 모델로 비교</li>
      <li>실험 ID: <code>A1</code></li>
      <li>사용 데이터: 고정된 Track6 train / warm test / cold test 전체 split</li>
      <li>라벨 사용 기준: feature 파일과 label 파일을 <code>_track6_row_id</code>로 연결해 학습과 성능 계산에만 사용</li>
      <li>생성일: <code>{html.escape(manifest['created_at'])}</code></li>
    </ul>
  </div>
  <div class="card">
    <h2>실험 입력 정보</h2>
    <table>
      <tr><th>항목</th><th>구분</th><th>내용</th></tr>
      <tr><td>실험</td><td>ID</td><td><code>{html.escape(manifest['experiment_id'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>학습 원본</td><td><code>{html.escape(source['train_features'])}</code><br><code>{html.escape(source['train_labels'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>Warm 테스트 원본</td><td><code>{html.escape(source['warm_features'])}</code><br><code>{html.escape(source['warm_labels'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>Cold 테스트 원본</td><td><code>{html.escape(source['cold_features'])}</code><br><code>{html.escape(source['cold_labels'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>실험용 생성 파일</td><td><code>{html.escape(files['train_features'])}</code><br><code>{html.escape(files['train_labels'])}</code><br><code>{html.escape(files['test_warm_features'])}</code><br><code>{html.escape(files['test_warm_labels'])}</code><br><code>{html.escape(files['test_cold_features'])}</code><br><code>{html.escape(files['test_cold_labels'])}</code></td></tr>
      <tr><td>사용 코드</td><td>실행 스크립트</td><td><code>{html.escape(code_path)}</code></td></tr>
      <tr><td>사용 프롬프트</td><td>지시 기록</td><td><code>{html.escape(prompt_path)}</code></td></tr>
      <tr><td>데이터 기준</td><td>샘플링 여부</td><td><code>{html.escape(manifest['run_mode'])}</code></td></tr>
    </table>
  </div>
  <div class="grid">
    <div class="card">
      <h2>사용 데이터</h2>
      <table>
        <tr><th>구분</th><th>건수</th></tr>
        <tr><td>학습 데이터</td><td>{manifest['rows']['train']:,}</td></tr>
        <tr><td>Warm 테스트 데이터</td><td>{manifest['rows']['test_warm']:,}</td></tr>
        <tr><td>Cold 테스트 데이터</td><td>{manifest['rows']['test_cold']:,}</td></tr>
      </table>
    </div>
    <div class="card">
      <h2>모델 종류</h2>
      <table>
        <tr><th>분류</th><th>모델 코드</th><th>모델</th></tr>
        {model_table}
      </table>
    </div>
  </div>
  {''.join(sections)}
  <div class="card">
    <h2>생성 파일</h2>
    <ul>{file_items}</ul>
  </div>
</body>
</html>
"""


def render_readme(manifest: dict) -> str:
    return f"""# Track6 A1 Ho/Size 전체 데이터 실험

- 실험 목적: 결과 양식 기준으로 `Ho / ln Ho / Size / ln Size` 변수별 Warm/Cold 모델 결과를 기록
- 기준 데이터: 고정된 Track6 feature/label split
- 학습 데이터: `data/track6_split/features/warm/track6_train_warm_features.csv` + `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split/labels/track6_test_warm_labels.csv`
- Cold 테스트 데이터: `data/track6_split/features/cold/track6_test_cold_cold_features.csv` + `data/track6_split/labels/track6_test_cold_labels.csv`
- 사용 코드: `{manifest['code_file']}`
- 사용 프롬프트: `{manifest['prompt_file']}`
- 학습 데이터 건수: `{manifest['rows']['train']:,}`건
- Warm 테스트 건수: `{manifest['rows']['test_warm']:,}`건
- Cold 테스트 건수: `{manifest['rows']['test_cold']:,}`건

## 데이터 사용 기준

- feature 파일은 모델 입력값이다.
- label 파일은 정답 가격이다.
- 학습 시에는 `train_features.csv`와 `train_labels.csv`를 `_track6_row_id`로 연결해 학습한다.
- 평가 시에는 테스트 feature로 예측한 뒤, 테스트 label과 `_track6_row_id`로 연결해 성능을 계산한다.
- 이 실험에서는 샘플링하지 않고 전체 split에서 A1 필수 값이 있는 행을 모두 사용한다.

## 모델 코드

- `A`: Warm Huber
- `B`: Warm Linear Regression
- `C`: Warm Ridge
- `D`: Cold Huber
- `E`: Cold Quantile-LAD
- `F`: Cold LightGBM

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
"""


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    train_full = load_join(TRAIN_FEATURES, TRAIN_LABELS)
    warm_full = load_join(WARM_FEATURES, WARM_LABELS)
    cold_full = load_join(COLD_FEATURES, COLD_LABELS)
    train = use_full_split(train_full)
    warm = use_full_split(warm_full)
    cold = use_full_split(cold_full)

    files = write_experiment_data_files(train, warm, cold)
    results = run_models(train, warm, cold)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "A1",
        "description": "Ho / ln Ho / Size / ln Size full Track6 split result-sheet experiment",
        "run_mode": "full_split_no_sampling",
        "seed": SEED,
        "code_file": str(Path(__file__).resolve().relative_to(REPO)),
        "prompt_file": str((EXP_DIR / "prompts" / "used_prompt.md").relative_to(REPO)),
        "data_policy": {
            "train": "fixed Track6 train split only",
            "warm_test": "fixed Track6 warm test split only",
            "cold_test": "fixed Track6 cold test split only",
            "join_key": "_track6_row_id",
            "label_usage": "labels are used for train target and test metric calculation, not as model input",
            "sampling": "disabled",
        },
        "source_files": {
            "train_features": str(TRAIN_FEATURES.relative_to(REPO)),
            "train_labels": str(TRAIN_LABELS.relative_to(REPO)),
            "warm_features": str(WARM_FEATURES.relative_to(REPO)),
            "warm_labels": str(WARM_LABELS.relative_to(REPO)),
            "cold_features": str(COLD_FEATURES.relative_to(REPO)),
            "cold_labels": str(COLD_LABELS.relative_to(REPO)),
        },
        "rows": {"train": len(train), "test_warm": len(warm), "test_cold": len(cold)},
        "features": {b["name"]: b["feature"] for b in VARIABLE_BLOCKS},
        "models": MODEL_ROWS,
        "generated_files": files,
    }

    results.to_csv(OUT_DIR / "metrics_long.csv", index=False)
    results.to_csv(OUT_DIR / "result_sheet.csv", index=False)
    (OUT_DIR / "result_sheet.html").write_text(render_html(results, files, manifest), encoding="utf-8")
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "README.md").write_text(render_readme(manifest), encoding="utf-8")
    (LOG_DIR / "run.log").write_text(
        f"{manifest['created_at']} A1 full split experiment completed. rows={manifest['rows']}\n",
        encoding="utf-8",
    )
    print(f"saved: {(OUT_DIR / 'result_sheet.html').relative_to(REPO)}")
    print(results[["variable_block", "scope", "model_code", "model_name", "R2", "MdAPE", "p95_APE"]].to_string(index=False))


if __name__ == "__main__":
    main()
