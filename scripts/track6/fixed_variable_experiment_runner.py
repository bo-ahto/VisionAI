#!/usr/bin/env python3
"""Fixed Track6 variable experiment runner.

This runner keeps the experiment code, data split, model set, metrics, label
usage, and output format fixed. Each experiment changes only its config file:
variable blocks, exported feature columns, prompt path, and comments.
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LinearRegression, QuantileRegressor, Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SEED = 20260521

DEFAULT_SPLIT_ROOT = REPO / "data" / "track6_split"

MODEL_ROWS = [
    {"code": "A", "scope": "Warm", "name": "Huber", "kind": "huber"},
    {"code": "B", "scope": "Warm", "name": "Linear Regression", "kind": "linear"},
    {"code": "C", "scope": "Warm", "name": "Ridge", "kind": "ridge"},
    {"code": "D", "scope": "Cold", "name": "Huber", "kind": "huber"},
    {"code": "E", "scope": "Cold", "name": "Quantile-LAD", "kind": "quantile"},
    {"code": "F", "scope": "Cold", "name": "LightGBM", "kind": "lightgbm"},
]


def generated_feature_columns(config: dict[str, Any]) -> list[str]:
    generated_cols = []
    for bucket in config.get("bucket_features", []):
        generated_cols.append(bucket["bucket_col"])
    for combo in config.get("combo_features", []):
        generated_cols.append(combo["combo_col"])
    for interaction in config.get("numeric_categorical_interactions", []):
        prefix = interaction["output_prefix"]
        top_n = int(interaction.get("top_n", 20))
        generated_cols.extend(f"{prefix}_{i:02d}" for i in range(1, top_n + 1))
    for interaction in config.get("numeric_numeric_interactions", []):
        generated_cols.append(interaction["output_col"])
    return generated_cols


def export_feature_columns(config: dict[str, Any]) -> list[str]:
    cols = []
    for col in [*config.get("export_feature_columns", []), *generated_feature_columns(config)]:
        if col not in cols:
            cols.append(col)
    return cols


def read_config(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["config_path"] = str(config_path.relative_to(REPO))
    config["exp_dir"] = str((REPO / config["exp_dir"]).resolve())
    return config


def split_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = REPO / config.get("split_root", str(DEFAULT_SPLIT_ROOT.relative_to(REPO)))
    return {
        "train_features": root / "features" / "warm" / "track6_train_warm_features.csv",
        "train_labels": root / "labels" / "track6_train_labels.csv",
        "warm_features": root / "features" / "warm" / "track6_test_warm_warm_features.csv",
        "warm_labels": root / "labels" / "track6_test_warm_labels.csv",
        "cold_features": root / "features" / "cold" / "track6_test_cold_cold_features.csv",
        "cold_labels": root / "labels" / "track6_test_cold_labels.csv",
    }


def all_required_feature_columns(config: dict[str, Any]) -> list[str]:
    cols = set(config.get("export_feature_columns", []))
    for block in config["variable_blocks"]:
        cols.update(block["features"])
    generated_cols = set()
    for bucket in config.get("bucket_features", []):
        cols.add(bucket["source_col"])
        generated_cols.add(bucket["bucket_col"])
    for combo in config.get("combo_features", []):
        cols.update(combo["source_cols"])
        generated_cols.add(combo["combo_col"])
    for interaction in config.get("numeric_categorical_interactions", []):
        cols.add(interaction["numeric_col"])
        cols.add(interaction["category_col"])
        prefix = interaction["output_prefix"]
        top_n = int(interaction.get("top_n", 20))
        generated_cols.update(f"{prefix}_{i:02d}" for i in range(1, top_n + 1))
    for interaction in config.get("numeric_numeric_interactions", []):
        cols.add(interaction["left_col"])
        cols.add(interaction["right_col"])
        generated_cols.add(interaction["output_col"])
    cols -= generated_cols
    return sorted(cols)


def load_join(features_path: Path, labels_path: Path, required_cols: list[str]) -> pd.DataFrame:
    features = pd.read_csv(features_path, low_memory=False)
    missing = [c for c in required_cols if c not in features.columns]
    if missing:
        raise ValueError(f"{features_path} missing columns: {missing}")
    labels = pd.read_csv(labels_path, low_memory=False)
    df = features.merge(labels[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def normalize_values(config: dict[str, Any], train: pd.DataFrame, *tests: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    frames = [train.copy(), *[t.copy() for t in tests]]
    required_cols = all_required_feature_columns(config)
    numeric_features = set(config.get("numeric_features", []))
    for frame in frames:
        for col in required_cols:
            if col not in frame.columns:
                continue
            if col in numeric_features:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
                continue
            frame[col] = frame[col].astype("string").fillna("__missing__").replace({"": "__missing__"})
            if col.endswith("_idx"):
                frame[col] = frame[col].str.replace(r"\.0$", "", regex=True)

    for bucket in config.get("bucket_features", []):
        source_col = bucket["source_col"]
        bucket_col = bucket["bucket_col"]
        top_n = int(bucket.get("top_n", 80))
        other_value = bucket.get("other_value", f"other_{source_col}")
        top_values = set(frames[0][source_col].value_counts().head(top_n).index)
        for frame in frames:
            frame[bucket_col] = np.where(frame[source_col].isin(top_values), frame[source_col], other_value)
    for combo in config.get("combo_features", []):
        source_cols = combo["source_cols"]
        combo_col = combo["combo_col"]
        sep = combo.get("separator", "__")
        top_n = int(combo.get("top_n", 120))
        other_value = combo.get("other_value", f"other_{combo_col}")
        for frame in frames:
            frame[combo_col] = frame[source_cols].astype("string").fillna("__missing__").agg(sep.join, axis=1)
        top_values = set(frames[0][combo_col].value_counts().head(top_n).index)
        for frame in frames:
            frame[combo_col] = np.where(frame[combo_col].isin(top_values), frame[combo_col], other_value)

    interaction_mappings = []
    for interaction in config.get("numeric_categorical_interactions", []):
        numeric_col = interaction["numeric_col"]
        category_col = interaction["category_col"]
        prefix = interaction["output_prefix"]
        top_n = int(interaction.get("top_n", 20))
        train_categories = list(frames[0][category_col].value_counts().head(top_n).index)
        for i in range(1, top_n + 1):
            category = train_categories[i - 1] if i <= len(train_categories) else None
            output_col = f"{prefix}_{i:02d}"
            interaction_mappings.append(
                {
                    "output_col": output_col,
                    "numeric_col": numeric_col,
                    "category_col": category_col,
                    "category_value": str(category) if category is not None else "__unused__",
                }
            )
            for frame in frames:
                numeric_value = pd.to_numeric(frame[numeric_col], errors="coerce")
                if category is None:
                    frame[output_col] = 0.0
                else:
                    frame[output_col] = np.where(frame[category_col].eq(category), numeric_value, 0.0)
    if interaction_mappings:
        config["_numeric_categorical_interaction_mappings"] = interaction_mappings
    numeric_numeric_mappings = []
    numeric_features.update(
        interaction["output_col"] for interaction in config.get("numeric_numeric_interactions", [])
    )
    config["numeric_features"] = list(dict.fromkeys([*config.get("numeric_features", []), *numeric_features]))
    for interaction in config.get("numeric_numeric_interactions", []):
        left_col = interaction["left_col"]
        right_col = interaction["right_col"]
        output_col = interaction["output_col"]
        numeric_numeric_mappings.append(
            {"output_col": output_col, "left_col": left_col, "right_col": right_col}
        )
        for frame in frames:
            left = pd.to_numeric(frame[left_col], errors="coerce")
            right = pd.to_numeric(frame[right_col], errors="coerce")
            frame[output_col] = left * right
    if numeric_numeric_mappings:
        config["_numeric_numeric_interaction_mappings"] = numeric_numeric_mappings
    return tuple(frames)


def write_experiment_data_files(
    config: dict[str, Any], train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame
) -> dict[str, str]:
    data_dir = Path(config["exp_dir"]) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    feature_cols = ["_track6_row_id", *export_feature_columns(config)]
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    files = {}
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        feature_path = data_dir / f"{name}_features.csv"
        label_path = data_dir / f"{name}_labels.csv"
        frame[feature_cols].to_csv(feature_path, index=False)
        frame[label_cols].to_csv(label_path, index=False)
        files[f"{name}_features"] = str(feature_path.relative_to(REPO))
        files[f"{name}_labels"] = str(label_path.relative_to(REPO))
    return files


def expand_variable_block_features(config: dict[str, Any], frame: pd.DataFrame) -> None:
    for block in config["variable_blocks"]:
        features = list(block["features"])
        for prefix in block.get("feature_prefixes", []):
            features.extend([c for c in frame.columns if c.startswith(prefix)])
        deduped = []
        for feature in features:
            if feature in frame.columns and feature not in deduped:
                deduped.append(feature)
        block["features"] = deduped


def copy_source_files(config: dict[str, Any], paths: dict[str, Path]) -> dict[str, str]:
    source_data_dir = Path(config["exp_dir"]) / "source_data"
    source_data_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        "train_features_source": paths["train_features"],
        "train_labels_source": paths["train_labels"],
        "test_warm_features_source": paths["warm_features"],
        "test_warm_labels_source": paths["warm_labels"],
        "test_cold_features_source": paths["cold_features"],
        "test_cold_labels_source": paths["cold_labels"],
    }
    copied = {}
    for key, src in sources.items():
        dst = source_data_dir / src.name
        shutil.copy2(src, dst)
        copied[key] = str(dst.relative_to(REPO))
    return copied


def make_encoder(features: list[str], numeric_features: list[str] | None = None) -> ColumnTransformer:
    numeric_features = [c for c in (numeric_features or []) if c in features]
    categorical_features = [c for c in features if c not in numeric_features]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = []
    if categorical_features:
        transformers.append(("cat", encoder, categorical_features))
    if numeric_features:
        numeric_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("num", numeric_pipeline, numeric_features))
    return ColumnTransformer(transformers)


def build_model(kind: str, features: list[str], numeric_features: list[str] | None = None) -> Pipeline:
    if kind == "linear":
        model = LinearRegression()
    elif kind == "ridge":
        model = Ridge(alpha=1.0)
    elif kind == "huber":
        model = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)
    elif kind == "quantile":
        model = QuantileRegressor(quantile=0.5, alpha=0.001, solver="highs")
    elif kind == "lightgbm":
        model = lgb.LGBMRegressor(
            objective="regression",
            n_estimators=160,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=30,
            random_state=SEED,
            verbosity=-1,
        )
    else:
        raise ValueError(f"unknown model kind: {kind}")
    return Pipeline([("preprocess", make_encoder(features, numeric_features)), ("model", model)])


def fit_predict(
    kind: str, train: pd.DataFrame, test: pd.DataFrame, features: list[str], numeric_features: list[str] | None = None
) -> np.ndarray:
    model = build_model(kind, features, numeric_features)
    model.fit(train[features], train["ln_price_krw"].to_numpy())
    return np.exp(model.predict(test[features]))


def calc_metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_price: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.asarray(pred_price, dtype=float), 1_000.0, None)
    actual_price = np.asarray(actual_price, dtype=float)
    pred_log = np.log(pred_price)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "R2": float(r2_score(actual_log, pred_log)),
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
        "MAPE": float(np.mean(ape)),
    }


def run_models(config: dict[str, Any], train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    numeric_features = list(config.get("numeric_features", []))
    for block in config["variable_blocks"]:
        for model_spec in MODEL_ROWS:
            test = warm if model_spec["scope"] == "Warm" else cold
            pred = fit_predict(model_spec["kind"], train, test, block["features"], numeric_features)
            metrics = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)
            rows.append(
                {
                    "experiment_id": config["experiment_id"],
                    "variable_block": block["name"],
                    "features": ", ".join(block["features"]),
                    "scope": model_spec["scope"],
                    "model_code": model_spec["code"],
                    "model_name": model_spec["name"],
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def fmt(value: float) -> str:
    return f"{float(value):.4f}" if pd.notna(value) else ""


def build_comment(config: dict[str, Any], results: pd.DataFrame) -> dict[str, str]:
    best_warm = results[results["scope"].eq("Warm")].sort_values("MdAPE").iloc[0]
    best_cold = results[results["scope"].eq("Cold")].sort_values("MdAPE").iloc[0]
    template = dict(config.get("comment", {}))
    template.setdefault("purpose", config["purpose"])
    template.setdefault(
        "summary",
        f"Warm 최고는 {best_warm.variable_block} + {best_warm.model_name}(MdAPE {best_warm.MdAPE:.4f}), "
        f"Cold 최고는 {best_cold.variable_block} + {best_cold.model_name}(MdAPE {best_cold.MdAPE:.4f})이다.",
    )
    return template


def render_html(config: dict[str, Any], results: pd.DataFrame, files: dict[str, str], manifest: dict) -> str:
    model_table = "".join(
        f"<tr><td>{m['scope']}</td><td>{m['code']}</td><td>{html.escape(m['name'])}</td></tr>" for m in MODEL_ROWS
    )
    sections = []
    for block in config["variable_blocks"]:
        sub = results[results["variable_block"].eq(block["name"])].copy()
        rows = "".join(
            "<tr>"
            f"<td>{html.escape(r.model_code)}</td>"
            f"<td>{html.escape(r.scope)}</td>"
            f"<td>{html.escape(r.model_name)}</td>"
            f"<td>{fmt(r.R2)}</td>"
            f"<td>{fmt(r.RMSE_log)}</td>"
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
            <section class="card">
              <h2>{html.escape(block['name'])}</h2>
              <p><strong>사용 피처:</strong> <code>{html.escape(', '.join(block['features']))}</code> · {html.escape(block.get('description', ''))}</p>
              <table>
                <thead><tr><th>모델 코드</th><th>분류</th><th>모델</th><th>R2</th><th>RMSE(log)</th><th>MdAPE</th><th>p95 APE</th><th>Within-30</th><th>Within-50</th><th>MAPE</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </section>
            """
        )

    source = manifest["source_files"]
    copied = manifest["copied_source_files"]
    generated = manifest["generated_files"]
    best_warm = results[results["scope"].eq("Warm")].sort_values("MdAPE").iloc[0]
    best_cold = results[results["scope"].eq("Cold")].sort_values("MdAPE").iloc[0]
    comment = build_comment(config, results)
    numeric_feature_text = ", ".join(config.get("numeric_features", [])) or "없음"
    file_items = "".join(f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>" for k, v in files.items())
    source_file_items = "".join(
        f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>"
        for k, v in manifest["copied_source_files"].items()
    )
    comment_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in comment.items()
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(config['title'])}</title>
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
    <h1>{html.escape(config['title'])}</h1>
    <ul>
      <li>목적: {html.escape(config['purpose'])}</li>
      <li>실험 ID: <code>{html.escape(config['experiment_id'])}</code></li>
      <li>Warm 최고: <code>{html.escape(best_warm.variable_block)}</code> / <code>{html.escape(best_warm.model_name)}</code> / MdAPE {fmt(best_warm.MdAPE)}</li>
      <li>Cold 최고: <code>{html.escape(best_cold.variable_block)}</code> / <code>{html.escape(best_cold.model_name)}</code> / MdAPE {fmt(best_cold.MdAPE)}</li>
      <li>생성일: <code>{html.escape(manifest['created_at'])}</code></li>
    </ul>
  </div>
  <div class="card">
    <h2>실험 입력 정보</h2>
    <table>
      <tr><th>항목</th><th>구분</th><th>내용</th></tr>
      <tr><td>복사한 사용 데이터</td><td>학습 원본 복사본</td><td><code>{html.escape(copied['train_features_source'])}</code><br><code>{html.escape(copied['train_labels_source'])}</code></td></tr>
      <tr><td>복사한 사용 데이터</td><td>Warm 테스트 원본 복사본</td><td><code>{html.escape(copied['test_warm_features_source'])}</code><br><code>{html.escape(copied['test_warm_labels_source'])}</code></td></tr>
      <tr><td>복사한 사용 데이터</td><td>Cold 테스트 원본 복사본</td><td><code>{html.escape(copied['test_cold_features_source'])}</code><br><code>{html.escape(copied['test_cold_labels_source'])}</code></td></tr>
      <tr><td>생성 데이터</td><td>학습용 생성 파일</td><td><code>{html.escape(generated['train_features'])}</code><br><code>{html.escape(generated['train_labels'])}</code></td></tr>
      <tr><td>생성 데이터</td><td>Warm 테스트 생성 파일</td><td><code>{html.escape(generated['test_warm_features'])}</code><br><code>{html.escape(generated['test_warm_labels'])}</code></td></tr>
      <tr><td>생성 데이터</td><td>Cold 테스트 생성 파일</td><td><code>{html.escape(generated['test_cold_features'])}</code><br><code>{html.escape(generated['test_cold_labels'])}</code></td></tr>
      <tr><td>원본 위치 참고</td><td>학습 원본 위치</td><td><code>{html.escape(source['train_features'])}</code><br><code>{html.escape(source['train_labels'])}</code></td></tr>
      <tr><td>원본 위치 참고</td><td>Warm 테스트 원본 위치</td><td><code>{html.escape(source['warm_features'])}</code><br><code>{html.escape(source['warm_labels'])}</code></td></tr>
      <tr><td>원본 위치 참고</td><td>Cold 테스트 원본 위치</td><td><code>{html.escape(source['cold_features'])}</code><br><code>{html.escape(source['cold_labels'])}</code></td></tr>
      <tr><td>사용 코드</td><td>공통 실행기</td><td><code>{html.escape(manifest['runner_file'])}</code></td></tr>
      <tr><td>사용 설정</td><td>실험 설정 파일</td><td><code>{html.escape(manifest['config_file'])}</code></td></tr>
      <tr><td>사용 프롬프트</td><td>지시 기록</td><td><code>{html.escape(manifest['prompt_file'])}</code></td></tr>
      <tr><td>데이터 기준</td><td>샘플링 여부</td><td><code>{html.escape(manifest['run_mode'])}</code></td></tr>
      <tr><td>피처 처리</td><td>숫자형 피처</td><td><code>{html.escape(numeric_feature_text)}</code><br>숫자형은 one-hot 변환하지 않고 중앙값 결측 보정 후 <code>StandardScaler</code> 적용</td></tr>
    </table>
  </div>
  <div class="card">
    <h2>모델 종류</h2>
    <table>
      <tr><th>분류</th><th>모델 코드</th><th>모델</th></tr>
      {model_table}
    </table>
  </div>
  <div class="card">
    <h2>코멘트</h2>
    <table>
      <tr><th>구분</th><th>내용</th></tr>
      {comment_rows}
    </table>
  </div>
  {''.join(sections)}
  <div class="card">
    <h2>생성 파일</h2>
    <ul>{file_items}</ul>
  </div>
  <div class="card">
    <h2>복사한 원본 데이터</h2>
    <ul>{source_file_items}</ul>
  </div>
</body>
</html>
"""


def render_readme(config: dict[str, Any], manifest: dict, results: pd.DataFrame) -> str:
    best_warm = results[results["scope"].eq("Warm")].sort_values("MdAPE").iloc[0]
    best_cold = results[results["scope"].eq("Cold")].sort_values("MdAPE").iloc[0]
    comment = build_comment(config, results)
    comment_lines = "\n".join(f"- {k}: {v}" for k, v in comment.items())
    return f"""# {config['title']}

- 실험 목적: {config['purpose']}
- 학습 데이터 건수: `{manifest['rows']['train']:,}`건
- Warm 테스트 건수: `{manifest['rows']['test_warm']:,}`건
- Cold 테스트 건수: `{manifest['rows']['test_cold']:,}`건
- Warm 최고: `{best_warm.variable_block}` / `{best_warm.model_name}` / MdAPE `{best_warm.MdAPE:.4f}`
- Cold 최고: `{best_cold.variable_block}` / `{best_cold.model_name}` / MdAPE `{best_cold.MdAPE:.4f}`
- 사용 코드: `{manifest['runner_file']}`
- 사용 설정: `{manifest['config_file']}`
- 사용 프롬프트: `{manifest['prompt_file']}`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

{comment_lines}

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
"""


def run_from_config(config_path: Path) -> pd.DataFrame:
    config = read_config(config_path)
    exp_dir = Path(config["exp_dir"])
    data_dir = exp_dir / "data"
    out_dir = exp_dir / "outputs"
    log_dir = exp_dir / "logs"
    for path in [data_dir, out_dir, log_dir, exp_dir / "source_data"]:
        path.mkdir(parents=True, exist_ok=True)

    required_cols = all_required_feature_columns(config)
    paths = split_paths(config)
    train = load_join(paths["train_features"], paths["train_labels"], required_cols)
    warm = load_join(paths["warm_features"], paths["warm_labels"], required_cols)
    cold = load_join(paths["cold_features"], paths["cold_labels"], required_cols)
    train, warm, cold = normalize_values(config, train, warm, cold)
    expand_variable_block_features(config, train)

    files = write_experiment_data_files(config, train, warm, cold)
    copied_source_files = copy_source_files(config, paths)
    results = run_models(config, train, warm, cold)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": config["experiment_id"],
        "description": config.get("description", config["purpose"]),
        "run_mode": "full_split_no_sampling",
        "split_root": str((REPO / config.get("split_root", str(DEFAULT_SPLIT_ROOT.relative_to(REPO)))).relative_to(REPO)),
        "seed": SEED,
        "runner_file": str(Path(__file__).resolve().relative_to(REPO)),
        "config_file": config["config_path"],
        "prompt_file": config["prompt_file"],
        "feature_processing": {
            "numeric_features": list(config.get("numeric_features", [])),
            "numeric_imputation": "median",
            "numeric_scaler": "StandardScaler",
            "categorical_encoding": "one_hot_handle_unknown_ignore",
            "numeric_categorical_interactions": config.get("numeric_categorical_interactions", []),
            "numeric_categorical_interaction_mappings": config.get(
                "_numeric_categorical_interaction_mappings", []
            ),
            "numeric_numeric_interactions": config.get("numeric_numeric_interactions", []),
            "numeric_numeric_interaction_mappings": config.get("_numeric_numeric_interaction_mappings", []),
        },
        "data_policy": {
            "train": "fixed Track6 train split only",
            "warm_test": "fixed Track6 warm test split only",
            "cold_test": "fixed Track6 cold test split only",
            "join_key": "_track6_row_id",
            "label_usage": "labels are used for train target and test metric calculation, not as model input",
            "sampling": "disabled",
        },
        "source_files": {
            "train_features": str(paths["train_features"].relative_to(REPO)),
            "train_labels": str(paths["train_labels"].relative_to(REPO)),
            "warm_features": str(paths["warm_features"].relative_to(REPO)),
            "warm_labels": str(paths["warm_labels"].relative_to(REPO)),
            "cold_features": str(paths["cold_features"].relative_to(REPO)),
            "cold_labels": str(paths["cold_labels"].relative_to(REPO)),
        },
        "rows": {"train": len(train), "test_warm": len(warm), "test_cold": len(cold)},
        "variable_blocks": config["variable_blocks"],
        "bucket_features": config.get("bucket_features", []),
        "combo_features": config.get("combo_features", []),
        "numeric_categorical_interactions": config.get("numeric_categorical_interactions", []),
        "numeric_categorical_interaction_mappings": config.get("_numeric_categorical_interaction_mappings", []),
        "numeric_numeric_interactions": config.get("numeric_numeric_interactions", []),
        "numeric_numeric_interaction_mappings": config.get("_numeric_numeric_interaction_mappings", []),
        "models": MODEL_ROWS,
        "generated_files": files,
        "copied_source_files": copied_source_files,
    }
    interaction_mappings = config.get("_numeric_categorical_interaction_mappings", [])
    if interaction_mappings:
        mapping_path = out_dir / "interaction_mapping.csv"
        pd.DataFrame(interaction_mappings).to_csv(mapping_path, index=False)
        manifest["generated_files"]["interaction_mapping"] = str(mapping_path.relative_to(REPO))
    numeric_numeric_mappings = config.get("_numeric_numeric_interaction_mappings", [])
    if numeric_numeric_mappings:
        mapping_path = out_dir / "numeric_numeric_interaction_mapping.csv"
        pd.DataFrame(numeric_numeric_mappings).to_csv(mapping_path, index=False)
        manifest["generated_files"]["numeric_numeric_interaction_mapping"] = str(mapping_path.relative_to(REPO))

    results.to_csv(out_dir / "metrics_long.csv", index=False)
    results.to_csv(out_dir / "result_sheet.csv", index=False)
    (out_dir / "result_sheet.html").write_text(render_html(config, results, files, manifest), encoding="utf-8")
    (out_dir / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "README.md").write_text(render_readme(config, manifest, results), encoding="utf-8")
    (log_dir / "run.log").write_text(
        f"{manifest['created_at']} {config['experiment_id']} fixed variable experiment completed. rows={manifest['rows']}\n",
        encoding="utf-8",
    )
    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run fixed Track6 variable experiment from config JSON.")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    results = run_from_config(args.config)
    print(
        results[
            ["variable_block", "scope", "model_code", "model_name", "R2", "RMSE_log", "MdAPE", "p95_APE"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
