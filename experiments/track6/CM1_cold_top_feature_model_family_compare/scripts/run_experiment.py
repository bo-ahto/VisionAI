#!/usr/bin/env python3
"""Run Track6 CM1 Cold model-family comparison.

This experiment fixes Cold top feature sets and changes only the model family.
Cold models never use artist_name_ko because the target artist is unseen in
training.
"""
from __future__ import annotations

import html
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, LinearRegression, QuantileRegressor, Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor


REPO = Path(__file__).resolve().parents[4]
SEED = 20260528


def read_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[1] / "experiment_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["config_path"] = str(config_path.relative_to(REPO))
    config["exp_dir"] = str((REPO / config["exp_dir"]).resolve())
    return config


def split_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = REPO / config["split_root"]
    return {
        "train_features": root / "features" / "warm" / "track6_train_warm_features.csv",
        "train_labels": root / "labels" / "track6_train_labels.csv",
        "test_features": root / "features" / "cold" / "track6_test_cold_cold_features.csv",
        "test_labels": root / "labels" / "track6_test_cold_labels.csv",
    }


def generated_columns(config: dict[str, Any]) -> list[str]:
    return [item["output_col"] for item in config.get("numeric_numeric_interactions", [])]


def required_columns(config: dict[str, Any]) -> list[str]:
    cols = set()
    generated = set(generated_columns(config))
    for feature_set in config["feature_sets"]:
        cols.update(feature_set["features"])
    for item in config.get("numeric_numeric_interactions", []):
        cols.add(item["left_col"])
        cols.add(item["right_col"])
    cols -= generated
    if "artist_name_ko" in cols:
        raise ValueError("Cold CM1 must not use artist_name_ko")
    return sorted(cols)


def load_join(feature_path: Path, label_path: Path, required: list[str]) -> pd.DataFrame:
    features = pd.read_csv(feature_path, low_memory=False)
    missing = [c for c in required if c not in features.columns]
    if missing:
        raise ValueError(f"{feature_path} missing columns: {missing}")
    labels = pd.read_csv(label_path, low_memory=False)
    df = features.merge(labels[["_track6_row_id", "price_krw", "ln_price_krw"]], on="_track6_row_id", how="inner")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def normalize(config: dict[str, Any], train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = [train.copy(), test.copy()]
    numeric = set(config.get("numeric_features", []))
    for frame in frames:
        for col in required_columns(config):
            if col not in frame.columns:
                continue
            if col in numeric:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            else:
                frame[col] = frame[col].astype("string").fillna("__missing__").replace({"": "__missing__"})

    mappings = []
    for item in config.get("numeric_numeric_interactions", []):
        left_col = item["left_col"]
        right_col = item["right_col"]
        output_col = item["output_col"]
        mappings.append(item)
        for frame in frames:
            left = pd.to_numeric(frame[left_col], errors="coerce").fillna(0.0)
            right = pd.to_numeric(frame[right_col], errors="coerce").fillna(0.0)
            frame[output_col] = left * right

    config["_numeric_numeric_interaction_mappings"] = mappings
    config["numeric_features"] = list(dict.fromkeys([*config.get("numeric_features", []), *generated_columns(config)]))
    return frames[0], frames[1]


def expand_features(config: dict[str, Any], train: pd.DataFrame) -> None:
    for feature_set in config["feature_sets"]:
        features = list(feature_set["features"])
        feature_set["features"] = list(dict.fromkeys([c for c in features if c in train.columns]))
        if "artist_name_ko" in feature_set["features"]:
            raise ValueError(f"{feature_set['name']} includes artist_name_ko, which is invalid for Cold")


def make_preprocessor(features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    numeric = [c for c in numeric_features if c in features]
    categorical = [c for c in features if c not in numeric]
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    transformers = []
    if categorical:
        transformers.append(("cat", encoder, categorical))
    if numeric:
        transformers.append(
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric,
            )
        )
    return ColumnTransformer(transformers)


def model_specs() -> list[dict[str, Any]]:
    return [
        {"name": "Linear Regression", "model": LinearRegression()},
        {"name": "Ridge", "model": Ridge(alpha=1.0)},
        {"name": "Huber", "model": HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000)},
        {"name": "Quantile-LAD", "model": QuantileRegressor(quantile=0.5, alpha=0.0001, solver="highs")},
        {
            "name": "LightGBM",
            "model": lgb.LGBMRegressor(
                objective="regression",
                n_estimators=220,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=30,
                random_state=SEED,
                verbosity=-1,
            ),
        },
        {
            "name": "XGBoost",
            "model": XGBRegressor(
                objective="reg:squarederror",
                n_estimators=220,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=SEED,
                n_jobs=4,
                verbosity=0,
            ),
        },
        {
            "name": "CatBoost",
            "model": CatBoostRegressor(
                loss_function="RMSE",
                iterations=220,
                learning_rate=0.05,
                depth=5,
                random_seed=SEED,
                verbose=False,
                allow_writing_files=False,
            ),
        },
        {
            "name": "HistGradientBoosting",
            "model": HistGradientBoostingRegressor(
                loss="squared_error",
                max_iter=220,
                learning_rate=0.05,
                l2_regularization=0.1,
                random_state=SEED,
            ),
        },
    ]


def calc_metrics(actual_price: np.ndarray, actual_log: np.ndarray, pred_log: np.ndarray) -> dict[str, float]:
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
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


def run_models(config: dict[str, Any], train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    numeric_features = config.get("numeric_features", [])
    y_train = train["ln_price_krw"].to_numpy()
    y_test_log = test["ln_price_krw"].to_numpy()
    y_test_price = test["price_krw"].to_numpy()
    for feature_set in config["feature_sets"]:
        features = feature_set["features"]
        for spec in model_specs():
            start = time.time()
            status = "ok"
            error = ""
            try:
                pipe = Pipeline([("preprocess", make_preprocessor(features, numeric_features)), ("model", spec["model"])])
                pipe.fit(train[features], y_train)
                pred_log = pipe.predict(test[features])
                metrics = calc_metrics(y_test_price, y_test_log, pred_log)
            except Exception as exc:
                status = "error"
                error = repr(exc)
                metrics = {k: np.nan for k in ["R2", "RMSE_log", "MdAPE", "p95_APE", "Within_30", "Within_50", "MAPE"]}
            rows.append(
                {
                    "experiment_id": config["experiment_id"],
                    "feature_set": feature_set["name"],
                    "features": ", ".join(features),
                    "model_name": spec["name"],
                    "status": status,
                    "error": error,
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    "fit_seconds": round(time.time() - start, 3),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def copy_source(paths: dict[str, Path], exp_dir: Path) -> dict[str, str]:
    source_dir = exp_dir / "source_data"
    source_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, src in paths.items():
        dst = source_dir / src.name
        shutil.copy2(src, dst)
        out[key] = str(dst.relative_to(REPO))
    return out


def write_data(config: dict[str, Any], train: pd.DataFrame, test: pd.DataFrame) -> dict[str, str]:
    data_dir = Path(config["exp_dir"]) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    feature_cols = ["_track6_row_id", *sorted(set(sum([fs["features"] for fs in config["feature_sets"]], [])))]
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    files = {
        "train_features": data_dir / "train_features.csv",
        "train_labels": data_dir / "train_labels.csv",
        "test_cold_features": data_dir / "test_cold_features.csv",
        "test_cold_labels": data_dir / "test_cold_labels.csv",
    }
    train[feature_cols].to_csv(files["train_features"], index=False)
    train[label_cols].to_csv(files["train_labels"], index=False)
    test[feature_cols].to_csv(files["test_cold_features"], index=False)
    test[label_cols].to_csv(files["test_cold_labels"], index=False)
    return {k: str(v.relative_to(REPO)) for k, v in files.items()}


def fmt(v: float) -> str:
    return "" if pd.isna(v) else f"{float(v):.4f}"


def feature_display(feature_set: str, raw_features: str) -> str:
    replacements = {
        "total_works_x_log_area": "artist_meta_total_works × log_area",
        "followers_x_log_area": "artist_meta_followers × log_area",
        "for_sale_works_x_log_area": "artist_meta_for_sale_works × log_area",
        "total_works_x_ln_ho": "artist_meta_total_works × ln_estimated_ho",
        "followers_x_ln_ho": "artist_meta_followers × ln_estimated_ho",
        "for_sale_works_x_ln_ho": "artist_meta_for_sale_works × ln_estimated_ho",
    }
    parts = [p.strip() for p in raw_features.split(",") if p.strip()]
    readable = [replacements.get(p, p) for p in parts]
    return f"{feature_set}<br><code>{html.escape(', '.join(readable))}</code>"


def render_html(config: dict[str, Any], results: pd.DataFrame, generated_files: dict[str, str], source_files: dict[str, str]) -> str:
    ok = results[results["status"].eq("ok")]
    best = ok.sort_values(["MdAPE", "p95_APE"]).iloc[0]
    stable = ok.sort_values(["p95_APE", "MdAPE"]).iloc[0]
    feature_lookup = {row["feature_set"]: row["features"] for _, row in results.iterrows()}
    rows = "".join(
        "<tr>"
        f"<td>{feature_display(r.feature_set, feature_lookup.get(r.feature_set, r.features))}</td>"
        f"<td>{html.escape(r.model_name)}</td>"
        f"<td>{html.escape(r.status)}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        f"<td>{fmt(r.Within_30)}</td>"
        f"<td>{fmt(r.RMSE_log)}</td>"
        f"<td>{fmt(r.R2)}</td>"
        f"<td>{html.escape(str(r.fit_seconds))}</td>"
        "</tr>"
        for r in results.sort_values(["feature_set", "MdAPE", "p95_APE"]).itertuples()
    )
    best_by_feature = (
        ok.sort_values(["feature_set", "MdAPE", "p95_APE"])
        .groupby("feature_set", as_index=False)
        .first()
    )
    best_rows = "".join(
        "<tr>"
        f"<td>{feature_display(r.feature_set, feature_lookup.get(r.feature_set, ''))}</td>"
        f"<td>{html.escape(r.model_name)}</td>"
        f"<td>{fmt(r.MdAPE)}</td>"
        f"<td>{fmt(r.p95_APE)}</td>"
        f"<td>{fmt(r.Within_30)}</td>"
        f"<td>{fmt(r.RMSE_log)}</td>"
        f"<td>{fmt(r.R2)}</td>"
        "</tr>"
        for r in best_by_feature.sort_values("MdAPE").itertuples()
    )
    file_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td><code>{html.escape(v)}</code></td></tr>"
        for k, v in {**generated_files, **source_files}.items()
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(config['title'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; margin: 32px; background: #fbf7ed; color: #18231d; }}
    .card {{ background: #fffdf6; border: 1px solid #d6c7ad; border-radius: 18px; padding: 22px; margin-bottom: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fffdf8; }}
    th, td {{ border: 1px solid #d6c7ad; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #e8dcc8; }}
    code {{ background: #eee6d6; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <section class="card">
    <h1>{html.escape(config['title'])}</h1>
    <ul>
      <li>목적: {html.escape(config['purpose'])}</li>
      <li>정확도 최고: <code>{html.escape(best.feature_set)}</code> + <code>{html.escape(best.model_name)}</code> / MdAPE {fmt(best.MdAPE)}</li>
      <li>큰 오차 안정성 최고: <code>{html.escape(stable.feature_set)}</code> + <code>{html.escape(stable.model_name)}</code> / p95_APE {fmt(stable.p95_APE)}</li>
      <li>Cold 원칙: <code>artist_name_ko</code> 미사용</li>
      <li>생성일: <code>{datetime.now().isoformat(timespec='seconds')}</code></li>
    </ul>
  </section>
  <section class="card">
    <h2>피처 조합별 1위 모델</h2>
    <table><thead><tr><th>피처 조합 / 실제 피처명</th><th>모델</th><th>MdAPE</th><th>p95_APE</th><th>Within_30</th><th>RMSE_log</th><th>R2</th></tr></thead><tbody>{best_rows}</tbody></table>
  </section>
  <section class="card">
    <h2>전체 모델 비교 결과</h2>
    <table><thead><tr><th>피처 조합 / 실제 피처명</th><th>모델</th><th>상태</th><th>MdAPE</th><th>p95_APE</th><th>Within_30</th><th>RMSE_log</th><th>R2</th><th>학습초</th></tr></thead><tbody>{rows}</tbody></table>
  </section>
  <section class="card">
    <h2>사용 파일</h2>
    <table><thead><tr><th>구분</th><th>경로</th></tr></thead><tbody>{file_rows}</tbody></table>
  </section>
</body>
</html>"""


def render_readme(config: dict[str, Any], results: pd.DataFrame) -> str:
    ok = results[results["status"].eq("ok")]
    best = ok.sort_values(["MdAPE", "p95_APE"]).iloc[0]
    stable = ok.sort_values(["p95_APE", "MdAPE"]).iloc[0]
    feature_lines = "\n".join(
        f"- `{fs['name']}`: `{', '.join(fs['features'])}`"
        for fs in config["feature_sets"]
    )
    return f"""# {config['title']}

- 목적: {config['purpose']}
- 정확도 최고: `{best.feature_set}` + `{best.model_name}` / MdAPE `{fmt(best.MdAPE)}`
- 큰 오차 안정성 최고: `{stable.feature_set}` + `{stable.model_name}` / p95_APE `{fmt(stable.p95_APE)}`
- Cold 원칙: `artist_name_ko` 미사용
- 실행 모드: `{config['run_mode']}`

## 피처 조합별 실제 피처명

{feature_lines}

## 주요 결과 파일

- HTML: `outputs/result_sheet.html`
- 전체 지표: `outputs/metrics_long.csv`
- 사용 데이터: `data/`
- 원본 복사본: `source_data/`
"""


def main() -> None:
    config = read_config()
    exp_dir = Path(config["exp_dir"])
    paths = split_paths(config)
    required = required_columns(config)
    train = load_join(paths["train_features"], paths["train_labels"], required)
    test = load_join(paths["test_features"], paths["test_labels"], required)
    train, test = normalize(config, train, test)
    expand_features(config, train)
    generated_files = write_data(config, train, test)
    source_files = copy_source(paths, exp_dir)
    results = run_models(config, train, test)

    out_dir = exp_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / "metrics_long.csv"
    html_path = out_dir / "result_sheet.html"
    result_path = out_dir / "result_sheet.csv"
    manifest_path = out_dir / "experiment_manifest.json"
    interaction_path = out_dir / "numeric_numeric_interaction_mapping.csv"
    results.to_csv(metrics_path, index=False)
    results.sort_values(["MdAPE", "p95_APE"]).to_csv(result_path, index=False)
    if config.get("_numeric_numeric_interaction_mappings"):
        pd.DataFrame(config["_numeric_numeric_interaction_mappings"]).to_csv(interaction_path, index=False)
    html_path.write_text(render_html(config, results, generated_files, source_files), encoding="utf-8")
    (exp_dir / "README.md").write_text(render_readme(config, results), encoding="utf-8")
    manifest = {
        "experiment_id": config["experiment_id"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": config["config_path"],
        "generated_files": generated_files,
        "source_files": source_files,
        "outputs": {
            "metrics_long": str(metrics_path.relative_to(REPO)),
            "result_sheet_csv": str(result_path.relative_to(REPO)),
            "result_sheet_html": str(html_path.relative_to(REPO)),
            "manifest": str(manifest_path.relative_to(REPO)),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(results.sort_values(["MdAPE", "p95_APE"]).head(20).to_string(index=False))


if __name__ == "__main__":
    main()
