#!/usr/bin/env python3
"""Run Track6 B2 artist_name_ko encoding comparison."""
from __future__ import annotations

import html
import json
import shutil
import sys
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


REPO = Path(__file__).resolve().parents[4]
SEED = 20260521

MODEL_ROWS = [
    {"code": "A", "scope": "Warm", "name": "Huber", "kind": "huber"},
    {"code": "B", "scope": "Warm", "name": "Linear Regression", "kind": "linear"},
    {"code": "C", "scope": "Warm", "name": "Ridge", "kind": "ridge"},
    {"code": "D", "scope": "Cold", "name": "Huber", "kind": "huber"},
    {"code": "E", "scope": "Cold", "name": "Quantile-LAD", "kind": "quantile"},
    {"code": "F", "scope": "Cold", "name": "LightGBM", "kind": "lightgbm"},
]


def read_config() -> dict[str, Any]:
    path = REPO / "experiments" / "track6" / "B2_artist_name_encoding_compare" / "experiment_config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["config_path"] = str(path.relative_to(REPO))
    config["exp_dir_abs"] = str((REPO / config["exp_dir"]).resolve())
    return config


def split_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = REPO / config["split_root"]
    return {
        "train_features": root / "features" / "warm" / "track6_train_warm_features.csv",
        "train_labels": root / "labels" / "track6_train_labels.csv",
        "warm_features": root / "features" / "warm" / "track6_test_warm_warm_features.csv",
        "warm_labels": root / "labels" / "track6_test_warm_labels.csv",
        "cold_features": root / "features" / "cold" / "track6_test_cold_cold_features.csv",
        "cold_labels": root / "labels" / "track6_test_cold_labels.csv",
    }


def load_join(features_path: Path, labels_path: Path) -> pd.DataFrame:
    features = pd.read_csv(features_path, low_memory=False)
    labels = pd.read_csv(labels_path, low_memory=False)
    required = {"_track6_row_id", "artist_name_ko"}
    missing = required - set(features.columns)
    if missing:
        raise ValueError(f"{features_path} missing columns: {sorted(missing)}")
    df = features[["_track6_row_id", "artist_name_ko"]].merge(
        labels[["_track6_row_id", "price_krw", "ln_price_krw"]],
        on="_track6_row_id",
        how="inner",
    )
    df["artist_name_ko"] = df["artist_name_ko"].astype("string").fillna("__missing__").replace({"": "__missing__"})
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def add_encoding_features(config: dict[str, Any], train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame):
    global_mean = float(train["ln_price_krw"].mean())
    smoothing_m = float(config.get("target_encoding_smoothing_m", 10))

    stats = (
        train.groupby("artist_name_ko", dropna=False)["ln_price_krw"]
        .agg(["count", "sum", "mean"])
        .rename(columns={"count": "artist_train_count", "sum": "artist_train_sum", "mean": "artist_target_mean_log"})
        .reset_index()
    )
    stats["artist_frequency_log"] = np.log1p(stats["artist_train_count"].astype(float))
    stats["artist_smoothed_target_mean_log"] = (
        stats["artist_train_sum"].astype(float) + global_mean * smoothing_m
    ) / (stats["artist_train_count"].astype(float) + smoothing_m)

    frames = []
    for frame in [train.copy(), warm.copy(), cold.copy()]:
        out = frame.merge(
            stats[
                [
                    "artist_name_ko",
                    "artist_frequency_log",
                    "artist_target_mean_log",
                    "artist_smoothed_target_mean_log",
                ]
            ],
            on="artist_name_ko",
            how="left",
        )
        out["artist_frequency_log"] = out["artist_frequency_log"].fillna(0.0)
        out["artist_target_mean_log"] = out["artist_target_mean_log"].fillna(global_mean)
        out["artist_smoothed_target_mean_log"] = out["artist_smoothed_target_mean_log"].fillna(global_mean)
        frames.append(out)
    return tuple(frames), {
        "global_mean_ln_price": global_mean,
        "target_encoding_smoothing_m": smoothing_m,
        "train_artist_count": int(stats.shape[0]),
    }


def make_encoder(features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    numeric_features = [c for c in numeric_features if c in features]
    categorical_features = [c for c in features if c not in numeric_features]
    try:
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = []
    if categorical_features:
        transformers.append(("cat", one_hot, categorical_features))
    if numeric_features:
        transformers.append(
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric_features,
            )
        )
    return ColumnTransformer(transformers)


def build_model(kind: str, features: list[str], numeric_features: list[str]) -> Pipeline:
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
    for block in config["encoding_blocks"]:
        features = block["features"]
        numeric_features = block["numeric_features"]
        for model_spec in MODEL_ROWS:
            test = warm if model_spec["scope"] == "Warm" else cold
            model = build_model(model_spec["kind"], features, numeric_features)
            model.fit(train[features], train["ln_price_krw"].to_numpy())
            pred = np.exp(model.predict(test[features]))
            metrics = calc_metrics(test["price_krw"].to_numpy(), test["ln_price_krw"].to_numpy(), pred)
            rows.append(
                {
                    "experiment_id": config["experiment_id"],
                    "encoding_block": block["name"],
                    "features": ", ".join(features),
                    "scope": model_spec["scope"],
                    "model_code": model_spec["code"],
                    "model_name": model_spec["name"],
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def write_data_files(config: dict[str, Any], train: pd.DataFrame, warm: pd.DataFrame, cold: pd.DataFrame) -> dict[str, str]:
    data_dir = Path(config["exp_dir_abs"]) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    feature_cols = [
        "_track6_row_id",
        "artist_name_ko",
        "artist_frequency_log",
        "artist_target_mean_log",
        "artist_smoothed_target_mean_log",
    ]
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    files = {}
    for name, frame in [("train", train), ("test_warm", warm), ("test_cold", cold)]:
        fp = data_dir / f"{name}_features.csv"
        lp = data_dir / f"{name}_labels.csv"
        frame[feature_cols].to_csv(fp, index=False)
        frame[label_cols].to_csv(lp, index=False)
        files[f"{name}_features"] = str(fp.relative_to(REPO))
        files[f"{name}_labels"] = str(lp.relative_to(REPO))
    return files


def copy_source_files(config: dict[str, Any], paths: dict[str, Path]) -> dict[str, str]:
    source_dir = Path(config["exp_dir_abs"]) / "source_data"
    source_dir.mkdir(parents=True, exist_ok=True)
    copied = {}
    for key, src in paths.items():
        dst = source_dir / src.name
        shutil.copy2(src, dst)
        copied[key] = str(dst.relative_to(REPO))
    return copied


def fmt(value: float) -> str:
    return f"{float(value):.4f}" if pd.notna(value) else ""


def render_html(config: dict[str, Any], results: pd.DataFrame, files: dict[str, str], manifest: dict[str, Any]) -> str:
    best_warm = results[results["scope"].eq("Warm")].sort_values("MdAPE").iloc[0]
    best_cold = results[results["scope"].eq("Cold")].sort_values("MdAPE").iloc[0]
    result_rows = "".join(
        "<tr>"
        f"<td>{html.escape(r.encoding_block)}</td>"
        f"<td>{html.escape(r.scope)}</td>"
        f"<td>{html.escape(r.model_code)}</td>"
        f"<td>{html.escape(r.model_name)}</td>"
        f"<td>{fmt(r.R2)}</td>"
        f"<td>{fmt(r.RMSE_log)}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        f"<td>{fmt(r.Within_30)}</td>"
        f"<td>{fmt(r.Within_50)}</td>"
        f"<td>{fmt(r.MAPE)}</td>"
        "</tr>"
        for r in results.sort_values(["scope", "encoding_block", "model_code"]).itertuples()
    )
    config_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in config["comment"].items()
    )
    block_rows = "".join(
        f"<tr><td>{html.escape(b['name'])}</td><td><code>{html.escape(', '.join(b['features']))}</code></td>"
        f"<td><code>{html.escape(', '.join(b['numeric_features']) or '없음')}</code></td><td>{html.escape(b['description'])}</td></tr>"
        for b in config["encoding_blocks"]
    )
    file_rows = "".join(f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>" for k, v in files.items())
    source_rows = "".join(
        f"<li><code>{html.escape(k)}</code>: <code>{html.escape(v)}</code></li>"
        for k, v in manifest["copied_source_files"].items()
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
  <section class="card">
    <h1>{html.escape(config['title'])}</h1>
    <ul>
      <li>실험 ID: <code>{html.escape(config['experiment_id'])}</code></li>
      <li>목적: {html.escape(config['purpose'])}</li>
      <li>Warm 최고: <code>{html.escape(best_warm.encoding_block)}</code> / <code>{html.escape(best_warm.model_name)}</code> / MdAPE {fmt(best_warm.MdAPE)} / RMSE(log) {fmt(best_warm.RMSE_log)}</li>
      <li>Cold 최고: <code>{html.escape(best_cold.encoding_block)}</code> / <code>{html.escape(best_cold.model_name)}</code> / MdAPE {fmt(best_cold.MdAPE)} / RMSE(log) {fmt(best_cold.RMSE_log)}</li>
      <li>생성일: <code>{html.escape(manifest['created_at'])}</code></li>
    </ul>
  </section>
  <section class="card">
    <h2>실험 코멘트</h2>
    <table><tr><th>항목</th><th>내용</th></tr>{config_rows}</table>
  </section>
  <section class="card">
    <h2>encoding 비교 구성</h2>
    <table><tr><th>encoding</th><th>사용 피처</th><th>숫자형 피처</th><th>설명</th></tr>{block_rows}</table>
  </section>
  <section class="card">
    <h2>실행 결과</h2>
    <table>
      <thead><tr><th>encoding</th><th>분류</th><th>모델 코드</th><th>모델</th><th>R2</th><th>RMSE(log)</th><th>MdAPE</th><th>p95 APE</th><th>Within-30</th><th>Within-50</th><th>MAPE</th></tr></thead>
      <tbody>{result_rows}</tbody>
    </table>
  </section>
  <section class="card">
    <h2>생성 데이터</h2>
    <ul>{file_rows}</ul>
  </section>
  <section class="card">
    <h2>복사한 원본 데이터</h2>
    <ul>{source_rows}</ul>
  </section>
</body>
</html>
"""


def render_readme(config: dict[str, Any], manifest: dict[str, Any], results: pd.DataFrame) -> str:
    best_warm = results[results["scope"].eq("Warm")].sort_values("MdAPE").iloc[0]
    best_cold = results[results["scope"].eq("Cold")].sort_values("MdAPE").iloc[0]
    return f"""# {config['title']}

- 실험 목적: {config['purpose']}
- 학습 데이터 건수: `{manifest['rows']['train']:,}`건
- Warm 테스트 건수: `{manifest['rows']['test_warm']:,}`건
- Cold 테스트 건수: `{manifest['rows']['test_cold']:,}`건
- Warm 최고: `{best_warm.encoding_block}` / `{best_warm.model_name}` / MdAPE `{best_warm.MdAPE:.4f}` / RMSE(log) `{best_warm.RMSE_log:.4f}`
- Cold 최고: `{best_cold.encoding_block}` / `{best_cold.model_name}` / MdAPE `{best_cold.MdAPE:.4f}` / RMSE(log) `{best_cold.RMSE_log:.4f}`
- 사용 코드: `experiments/track6/B2_artist_name_encoding_compare/scripts/run_experiment.py`
- 사용 설정: `{manifest['config_file']}`
- 사용 프롬프트: `{manifest['prompt_file']}`

## 주의

- target encoding 계열은 train label만 사용해 계산했다.
- Warm 결과를 중심으로 판단한다.
- Cold 결과는 신규 작가명 상황의 한계 확인용 참고값이다.
"""


def main() -> None:
    config = read_config()
    exp_dir = Path(config["exp_dir_abs"])
    for rel in ["data", "outputs", "logs", "source_data"]:
        (exp_dir / rel).mkdir(parents=True, exist_ok=True)

    paths = split_paths(config)
    train = load_join(paths["train_features"], paths["train_labels"])
    warm = load_join(paths["warm_features"], paths["warm_labels"])
    cold = load_join(paths["cold_features"], paths["cold_labels"])
    (train, warm, cold), encoding_meta = add_encoding_features(config, train, warm, cold)

    files = write_data_files(config, train, warm, cold)
    copied = copy_source_files(config, paths)
    results = run_models(config, train, warm, cold)

    out_dir = exp_dir / "outputs"
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": config["experiment_id"],
        "config_file": config["config_path"],
        "prompt_file": config["prompt_file"],
        "split_root": config["split_root"],
        "seed": SEED,
        "runner_file": str(Path(__file__).resolve().relative_to(REPO)),
        "encoding_meta": encoding_meta,
        "data_policy": {
            "join_key": "_track6_row_id",
            "label_usage": "train labels are used for model target and train-only target encoding; test labels are used only for metrics",
            "sampling": "disabled",
        },
        "rows": {"train": len(train), "test_warm": len(warm), "test_cold": len(cold)},
        "generated_files": files,
        "copied_source_files": copied,
        "encoding_blocks": config["encoding_blocks"],
        "models": MODEL_ROWS,
    }
    results.to_csv(out_dir / "metrics_long.csv", index=False)
    results.to_csv(out_dir / "result_sheet.csv", index=False)
    (out_dir / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "result_sheet.html").write_text(render_html(config, results, files, manifest), encoding="utf-8")
    (exp_dir / "README.md").write_text(render_readme(config, manifest, results), encoding="utf-8")
    (exp_dir / "logs" / "run.log").write_text(
        f"{manifest['created_at']} B2 artist encoding comparison completed. rows={manifest['rows']}\n",
        encoding="utf-8",
    )
    print(
        results[
            ["encoding_block", "scope", "model_code", "model_name", "R2", "RMSE_log", "MdAPE", "p95_APE"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    sys.exit(main())
