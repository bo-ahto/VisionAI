#!/usr/bin/env python3
"""Track6 A1-1 Warm Huber Ho vs ln Ho experiment.

Data policy:
- Training uses the fixed Track6 train split only.
- Warm evaluation uses the fixed Track6 warm test split only.
- Feature files and label files are read separately, then joined by
  `_track6_row_id` inside this script.
- Labels are used only as the training target and for metric calculation.
- No sampling is applied.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[4]
EXP_DIR = REPO / "experiments" / "track6" / "A1-1_warm_huber_ho_vs_ln_ho"
DATA_DIR = EXP_DIR / "data"
OUT_DIR = EXP_DIR / "outputs"
LOG_DIR = EXP_DIR / "logs"

SEED = 20260521

# 학습 기준:
# - Track6에서 고정한 train split 전체를 사용한다.
# - A1-1은 Warm Huber 실험이므로 Warm 평가 split만 사용한다.
TRAIN_FEATURES = REPO / "data" / "track6_split" / "features" / "warm" / "track6_train_warm_features.csv"
TRAIN_LABELS = REPO / "data" / "track6_split" / "labels" / "track6_train_labels.csv"
WARM_FEATURES = REPO / "data" / "track6_split" / "features" / "warm" / "track6_test_warm_warm_features.csv"
WARM_LABELS = REPO / "data" / "track6_split" / "labels" / "track6_test_warm_labels.csv"

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

VARIABLES = [
    {
        "experiment_id": "A1-1",
        "variable_name": "Ho",
        "feature": "estimated_ho",
        "description": "작품 면적을 가장 가까운 F형 호수로 환산한 원값",
    },
    {
        "experiment_id": "A1-1",
        "variable_name": "ln Ho",
        "feature": "ln_estimated_ho",
        "description": "환산 호수에 로그 변환을 적용한 값",
    },
]


def area_to_ho(area: float) -> float:
    if not np.isfinite(area) or area <= 0:
        return np.nan
    return float(min(HO_TABLE_F, key=lambda ho: abs(float(HO_TABLE_F[ho]) - float(area))))


def load_join(features_path: Path, labels_path: Path) -> pd.DataFrame:
    """Load feature and label files separately and join by `_track6_row_id`."""
    features = pd.read_csv(features_path, low_memory=False)
    labels = pd.read_csv(labels_path, low_memory=False)
    df = features.merge(labels[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    df["area_cm2"] = pd.to_numeric(df["area_cm2"], errors="coerce")
    df["estimated_ho"] = df["area_cm2"].apply(area_to_ho)
    df["ln_estimated_ho"] = np.log(df["estimated_ho"].clip(lower=0.01))
    return (
        df.dropna(subset=["price_krw", "ln_price_krw", "area_cm2", "estimated_ho", "ln_estimated_ho"])
        .sort_values("_track6_row_id")
        .reset_index(drop=True)
    )


def write_experiment_data_files(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    feature_cols = ["_track6_row_id", "estimated_ho", "ln_estimated_ho"]
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    files = {}
    for name, frame in [("train", train), ("test_warm", test)]:
        feature_path = DATA_DIR / f"{name}_features.csv"
        label_path = DATA_DIR / f"{name}_labels.csv"
        frame[feature_cols].to_csv(feature_path, index=False)
        frame[label_cols].to_csv(label_path, index=False)
        files[f"{name}_features"] = str(feature_path.relative_to(REPO))
        files[f"{name}_labels"] = str(label_path.relative_to(REPO))
    return files


def build_huber() -> Pipeline:
    return Pipeline(
        [
            ("preprocess", ColumnTransformer([("num", StandardScaler(), ["__feature__"])])),
            ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)),
        ]
    )


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, feature: str) -> np.ndarray:
    x_train = train[[feature]].rename(columns={feature: "__feature__"})
    x_test = test[[feature]].rename(columns={feature: "__feature__"})
    model = build_huber()
    model.fit(x_train, train["ln_price_krw"].to_numpy())
    return np.exp(model.predict(x_test))


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


def run_experiment(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable in VARIABLES:
        pred = fit_predict(train, test, variable["feature"])
        metrics = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)
        rows.append(
            {
                "experiment_id": variable["experiment_id"],
                "scope": "Warm",
                "model_code": "A",
                "model_name": "Huber",
                "variable_name": variable["variable_name"],
                "feature": variable["feature"],
                "n_train": int(len(train)),
                "n_test": int(len(test)),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def fmt(value: float) -> str:
    return f"{float(value):.4f}" if pd.notna(value) else ""


def render_html(results: pd.DataFrame, files: dict[str, str], manifest: dict) -> str:
    result_rows = "".join(
        "<tr>"
        f"<td>{html.escape(r.variable_name)}</td>"
        f"<td><code>{html.escape(r.feature)}</code></td>"
        f"<td>{html.escape(r.model_name)}</td>"
        f"<td>{fmt(r.R2)}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        f"<td>{fmt(r.Within_30)}</td>"
        f"<td>{fmt(r.Within_50)}</td>"
        f"<td>{fmt(r.MAPE)}</td>"
        "</tr>"
        for r in results.itertuples()
    )
    file_items = "".join(f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>" for k, v in files.items())
    source = manifest["source_files"]
    best = results.sort_values("MdAPE").iloc[0]
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Track6 A1-1 Warm Huber Ho vs ln Ho</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    h1 {{ margin-top: 0; font-size: 34px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
    ul {{ line-height: 1.8; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Track6 A1-1 Warm Huber Ho vs ln Ho</h1>
    <ul>
      <li>목적: Warm Huber 모델에서 Ho 원값과 ln Ho 중 어느 표현이 더 나은지 비교</li>
      <li>실험 ID: <code>A1-1</code></li>
      <li>모델: <code>Warm Huber</code></li>
      <li>결론 요약: <code>{html.escape(best.variable_name)}</code>가 MdAPE 기준 가장 낮음</li>
      <li>생성일: <code>{html.escape(manifest['created_at'])}</code></li>
    </ul>
  </div>
  <div class="card">
    <h2>실험 입력 정보</h2>
    <table>
      <tr><th>항목</th><th>구분</th><th>내용</th></tr>
      <tr><td>사용 데이터</td><td>학습 원본</td><td><code>{html.escape(source['train_features'])}</code><br><code>{html.escape(source['train_labels'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>Warm 테스트 원본</td><td><code>{html.escape(source['warm_features'])}</code><br><code>{html.escape(source['warm_labels'])}</code></td></tr>
      <tr><td>사용 데이터</td><td>실험용 생성 파일</td><td><code>{html.escape(files['train_features'])}</code><br><code>{html.escape(files['train_labels'])}</code><br><code>{html.escape(files['test_warm_features'])}</code><br><code>{html.escape(files['test_warm_labels'])}</code></td></tr>
      <tr><td>사용 코드</td><td>실행 스크립트</td><td><code>{html.escape(manifest['code_file'])}</code></td></tr>
      <tr><td>사용 프롬프트</td><td>지시 기록</td><td><code>{html.escape(manifest['prompt_file'])}</code></td></tr>
      <tr><td>데이터 기준</td><td>샘플링 여부</td><td><code>{html.escape(manifest['run_mode'])}</code></td></tr>
    </table>
  </div>
  <div class="card">
    <h2>결과</h2>
    <table>
      <thead>
        <tr><th>실험 변수명</th><th>사용 피처</th><th>모델</th><th>R2</th><th>MdAPE</th><th>p95 APE</th><th>Within-30</th><th>Within-50</th><th>MAPE</th></tr>
      </thead>
      <tbody>{result_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>생성 파일</h2>
    <ul>{file_items}</ul>
  </div>
</body>
</html>
"""


def render_readme(manifest: dict, results: pd.DataFrame) -> str:
    best = results.sort_values("MdAPE").iloc[0]
    return f"""# Track6 A1-1 Warm Huber Ho vs ln Ho

- 실험 목적: Warm Huber 모델에서 Ho 원값과 ln Ho 중 어느 표현이 더 나은지 비교
- 학습 데이터: `data/track6_split/features/warm/track6_train_warm_features.csv` + `data/track6_split/labels/track6_train_labels.csv`
- Warm 테스트 데이터: `data/track6_split/features/warm/track6_test_warm_warm_features.csv` + `data/track6_split/labels/track6_test_warm_labels.csv`
- 사용 코드: `{manifest['code_file']}`
- 사용 프롬프트: `{manifest['prompt_file']}`
- 학습 데이터 건수: `{manifest['rows']['train']:,}`건
- Warm 테스트 건수: `{manifest['rows']['test_warm']:,}`건
- 최저 MdAPE 변수: `{best.variable_name}`

## 비교 조건

- `Ho`: `estimated_ho`
- `ln Ho`: `ln_estimated_ho`

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

    train = load_join(TRAIN_FEATURES, TRAIN_LABELS)
    test_warm = load_join(WARM_FEATURES, WARM_LABELS)
    files = write_experiment_data_files(train, test_warm)
    results = run_experiment(train, test_warm)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": "A1-1",
        "description": "Warm Huber comparison between Ho and ln Ho",
        "run_mode": "full_split_no_sampling",
        "seed": SEED,
        "code_file": str(Path(__file__).resolve().relative_to(REPO)),
        "prompt_file": str((EXP_DIR / "prompts" / "used_prompt.md").relative_to(REPO)),
        "data_policy": {
            "train": "fixed Track6 train split only",
            "warm_test": "fixed Track6 warm test split only",
            "join_key": "_track6_row_id",
            "label_usage": "labels are used for train target and test metric calculation, not as model input",
            "sampling": "disabled",
        },
        "source_files": {
            "train_features": str(TRAIN_FEATURES.relative_to(REPO)),
            "train_labels": str(TRAIN_LABELS.relative_to(REPO)),
            "warm_features": str(WARM_FEATURES.relative_to(REPO)),
            "warm_labels": str(WARM_LABELS.relative_to(REPO)),
        },
        "rows": {"train": len(train), "test_warm": len(test_warm)},
        "features": {v["variable_name"]: v["feature"] for v in VARIABLES},
        "model": {"scope": "Warm", "name": "Huber"},
        "generated_files": files,
    }

    results.to_csv(OUT_DIR / "metrics_long.csv", index=False)
    results.to_csv(OUT_DIR / "result_sheet.csv", index=False)
    (OUT_DIR / "result_sheet.html").write_text(render_html(results, files, manifest), encoding="utf-8")
    (OUT_DIR / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (EXP_DIR / "README.md").write_text(render_readme(manifest, results), encoding="utf-8")
    (LOG_DIR / "run.log").write_text(
        f"{manifest['created_at']} A1-1 Warm Huber Ho vs ln Ho completed. rows={manifest['rows']}\n",
        encoding="utf-8",
    )
    print(f"saved: {(OUT_DIR / 'result_sheet.html').relative_to(REPO)}")
    print(results[["variable_name", "feature", "model_name", "R2", "MdAPE", "p95_APE", "Within_30", "Within_50"]].to_string(index=False))


if __name__ == "__main__":
    main()
