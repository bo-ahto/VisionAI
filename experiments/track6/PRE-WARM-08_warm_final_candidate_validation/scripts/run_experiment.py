#!/usr/bin/env python3
"""Run Track6 PRE-WARM-08 validation/OOF comparison for Warm candidates."""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[4]
SEED = 20260521


def read_config() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "experiment_config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["config_path"] = str(path.relative_to(REPO))
    config["exp_dir"] = str((REPO / config["exp_dir"]).resolve())
    return config


def split_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = REPO / config["split_root"]
    return {
        "train_features": root / "features" / "warm" / "track6_train_warm_features.csv",
        "train_labels": root / "labels" / "track6_train_labels.csv",
        "val_features": root / "features" / "warm" / "track6_val_warm_warm_features.csv",
        "val_labels": root / "labels" / "track6_val_warm_labels.csv",
        "test_features": root / "features" / "warm" / "track6_test_warm_warm_features.csv",
        "test_labels": root / "labels" / "track6_test_warm_labels.csv",
    }


def generated_columns(config: dict[str, Any]) -> list[str]:
    cols: list[str] = []
    for item in config.get("numeric_categorical_interactions", []):
        cols.extend(f"{item['output_prefix']}_{i:02d}" for i in range(1, int(item.get("top_n", 10)) + 1))
    return cols


def required_columns(config: dict[str, Any]) -> list[str]:
    cols = set()
    generated = set(generated_columns(config))
    for fs in config["feature_sets"]:
        cols.update(fs["features"])
    for item in config.get("numeric_categorical_interactions", []):
        cols.add(item["numeric_col"])
        cols.add(item["category_col"])
    cols -= generated
    return sorted(cols)


def load_join(feature_path: Path, label_path: Path, required: list[str]) -> tuple[pd.DataFrame, list[str]]:
    features = pd.read_csv(feature_path, low_memory=False)
    feature_cols = set(features.columns)
    labels = pd.read_csv(label_path, low_memory=False)
    label_cols = [c for c in labels.columns if c not in {"price_krw", "ln_price_krw"}]
    labels_meta = labels[label_cols + ["price_krw", "ln_price_krw"]].copy()
    df = features.merge(labels_meta, on="_track6_row_id", how="inner", suffixes=("", "__label"))
    metadata_filled: list[str] = []
    for col in required:
        label_col = f"{col}__label"
        if col not in feature_cols and col in labels.columns and col not in metadata_filled:
            metadata_filled.append(col)
        if col not in df.columns and col in labels.columns:
            df[col] = labels.set_index("_track6_row_id").loc[df["_track6_row_id"], col].to_numpy()
        elif col in df.columns and label_col in df.columns:
            df[col] = df[col].where(df[col].notna(), df[label_col])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{feature_path} missing columns after label metadata fill: {missing}")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["ln_price_krw"] = pd.to_numeric(df["ln_price_krw"], errors="coerce")
    return df.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True), metadata_filled


def normalize(config: dict[str, Any], *frames: pd.DataFrame) -> list[pd.DataFrame]:
    numeric = set(config.get("numeric_features", []))
    required = required_columns(config)
    out = [frame.copy() for frame in frames]
    for frame in out:
        for col in required:
            if col in numeric:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            else:
                frame[col] = frame[col].astype("string").fillna("__missing__").replace({"": "__missing__"})
    mappings = []
    for item in config.get("numeric_categorical_interactions", []):
        numeric_col = item["numeric_col"]
        category_col = item["category_col"]
        prefix = item["output_prefix"]
        top_n = int(item.get("top_n", 10))
        top_values = list(out[0][category_col].value_counts().head(top_n).index)
        for i in range(1, top_n + 1):
            category = top_values[i - 1] if i <= len(top_values) else None
            col = f"{prefix}_{i:02d}"
            mappings.append({
                "output_col": col,
                "numeric_col": numeric_col,
                "category_col": category_col,
                "category_value": str(category) if category is not None else "__unused__",
            })
            for frame in out:
                values = pd.to_numeric(frame[numeric_col], errors="coerce")
                frame[col] = np.where(frame[category_col].eq(category), values, 0.0) if category is not None else 0.0
    config["_interaction_mappings"] = mappings
    config["numeric_features"] = list(dict.fromkeys([*config.get("numeric_features", []), *generated_columns(config)]))
    for fs in config["feature_sets"]:
        features = list(fs["features"])
        for prefix in fs.get("feature_prefixes", []):
            features.extend([c for c in out[0].columns if c.startswith(prefix)])
        fs["features"] = list(dict.fromkeys([c for c in features if c in out[0].columns]))
    return out


def make_model(features: list[str], numeric_features: list[str]) -> Pipeline:
    numeric = [c for c in numeric_features if c in features]
    categorical = [c for c in features if c not in numeric]
    transformers = []
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), categorical))
    if numeric:
        transformers.append(("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric))
    return Pipeline([
        ("preprocess", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)),
    ])


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


def score_split(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> tuple[dict[str, float], np.ndarray]:
    pred = np.asarray(model.predict(frame[features]), dtype=float)
    metrics = calc_metrics(frame["price_krw"].to_numpy(), frame["ln_price_krw"].to_numpy(), pred)
    return metrics, pred


def oof_score(train: pd.DataFrame, features: list[str], numeric_features: list[str], folds: int) -> dict[str, float]:
    pred = np.full(len(train), np.nan, dtype=float)
    kf = KFold(n_splits=folds, shuffle=True, random_state=SEED)
    y = train["ln_price_krw"].to_numpy()
    for train_idx, holdout_idx in kf.split(train):
        model = make_model(features, numeric_features)
        model.fit(train.iloc[train_idx][features], y[train_idx])
        pred[holdout_idx] = model.predict(train.iloc[holdout_idx][features])
    return calc_metrics(train["price_krw"].to_numpy(), y, pred)


def run(config: dict[str, Any], train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    predictions = []
    numeric_features = config.get("numeric_features", [])
    for fs in config["feature_sets"]:
        features = fs["features"]
        model = make_model(features, numeric_features)
        model.fit(train[features], train["ln_price_krw"].to_numpy())
        for split_name, frame in [("validation", val), ("test", test)]:
            metrics, pred = score_split(model, frame, features)
            rows.append({
                "experiment_id": config["experiment_id"],
                "candidate": fs["name"],
                "candidate_source": fs.get("candidate_source", ""),
                "operability": fs.get("operability", ""),
                "split": split_name,
                "features": ", ".join(features),
                **metrics,
            })
            predictions.append(pd.DataFrame({
                "_track6_row_id": frame["_track6_row_id"],
                "split": split_name,
                "candidate": fs["name"],
                "actual_log": frame["ln_price_krw"],
                "pred_log": pred,
                "actual_price": frame["price_krw"],
                "pred_price": np.clip(np.exp(pred), 1_000.0, None),
            }))
        oof = oof_score(train, features, numeric_features, int(config.get("oof_folds", 5)))
        rows.append({
            "experiment_id": config["experiment_id"],
            "candidate": fs["name"],
            "candidate_source": fs.get("candidate_source", ""),
            "operability": fs.get("operability", ""),
            "split": "train_oof",
            "features": ", ".join(features),
            **oof,
        })
    return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)


def fmt(v: float) -> str:
    return "" if pd.isna(v) else f"{float(v):.4f}"


def render_html(config: dict[str, Any], results: pd.DataFrame, metadata_filled: dict[str, list[str]]) -> str:
    pivot = results.pivot_table(index=["candidate", "operability"], columns="split", values=["MdAPE", "p95_APE", "RMSE_log"], aggfunc="first")
    rows = []
    for idx, values in pivot.sort_values(("MdAPE", "validation")).iterrows():
        candidate, operability = idx
        rows.append(
            "<tr>"
            f"<td>{html.escape(candidate)}<br><code>{html.escape(operability)}</code></td>"
            f"<td>{fmt(values.get(('MdAPE', 'validation'), np.nan))}</td>"
            f"<td>{fmt(values.get(('p95_APE', 'validation'), np.nan))}</td>"
            f"<td>{fmt(values.get(('MdAPE', 'test'), np.nan))}</td>"
            f"<td>{fmt(values.get(('p95_APE', 'test'), np.nan))}</td>"
            f"<td>{fmt(values.get(('MdAPE', 'train_oof'), np.nan))}</td>"
            f"<td>{fmt(values.get(('RMSE_log', 'validation'), np.nan))}</td>"
            "</tr>"
        )
    meta_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(', '.join(v) or '-')}</td></tr>" for k, v in metadata_filled.items())
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{html.escape(config['title'])}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;margin:32px;color:#1f2933}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8dee4;padding:8px;vertical-align:top}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(config['title'])}</h1>
<p>{html.escape(config['purpose'])}</p>
<h2>후보별 요약</h2>
<table><thead><tr><th>후보</th><th>Val MdAPE</th><th>Val p95</th><th>Test MdAPE</th><th>Test p95</th><th>OOF MdAPE</th><th>Val RMSE_log</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Label Metadata 보강</h2>
<table><thead><tr><th>split</th><th>보강 컬럼</th></tr></thead><tbody>{meta_rows}</tbody></table>
</body></html>"""


def render_readme(config: dict[str, Any], results: pd.DataFrame, metadata_filled: dict[str, list[str]]) -> str:
    val = results[results["split"].eq("validation")].sort_values(["MdAPE", "p95_APE"])
    test = results[results["split"].eq("test")].sort_values(["MdAPE", "p95_APE"])
    oof = results[results["split"].eq("train_oof")].sort_values(["MdAPE", "p95_APE"])
    lines = [
        f"# {config['title']}",
        "",
        f"- 목적: {config['purpose']}",
        "- 결과 HTML: `outputs/result_sheet.html`",
        "- 결과 CSV: `outputs/result_sheet.csv`",
        "- 예측 CSV: `outputs/predictions.csv`",
        "",
        "## Validation 순위",
        "",
        "| 순위 | 후보 | 운영성 | MdAPE | p95_APE | RMSE_log |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for i, row in enumerate(val.itertuples(), 1):
        lines.append(f"| {i} | `{row.candidate}` | `{row.operability}` | `{row.MdAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## Test 순위", "", "| 순위 | 후보 | MdAPE | p95_APE | RMSE_log |", "|---:|---|---:|---:|---:|"]
    for i, row in enumerate(test.itertuples(), 1):
        lines.append(f"| {i} | `{row.candidate}` | `{row.MdAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## OOF 순위", "", "| 순위 | 후보 | MdAPE | p95_APE | RMSE_log |", "|---:|---|---:|---:|---:|"]
    for i, row in enumerate(oof.itertuples(), 1):
        lines.append(f"| {i} | `{row.candidate}` | `{row.MdAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += [
        "",
        "## 데이터 정합성 메모",
        "",
    ]
    for split, cols in metadata_filled.items():
        lines.append(f"- `{split}`: label metadata에서 보강한 컬럼 = `{', '.join(cols) if cols else '-'}`")
    lines += [
        "",
        "## 판단",
        "",
        "- 최종 판단은 validation MdAPE를 우선한다.",
        "- test 결과는 기존 관측 성능이 유지되는지 확인하는 보조 근거로만 사용한다.",
        "- `artist_name_ko` 후보가 채택되려면 validation/test feature export에 `artist_name_ko`를 명시적으로 포함하도록 데이터 파이프라인을 수정해야 한다.",
        "- 운영 정합성을 우선하면 `artist_key` 기반 후보를 별도 최종 후보로 유지한다.",
    ]
    return "\n".join(lines) + "\n"


def copy_sources(paths: dict[str, Path], exp_dir: Path) -> dict[str, str]:
    source = exp_dir / "source_data"
    source.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, src in paths.items():
        dst = source / src.name
        shutil.copy2(src, dst)
        out[key] = str(dst.relative_to(REPO))
    return out


def main() -> None:
    config = read_config()
    exp_dir = Path(config["exp_dir"])
    out_dir = exp_dir / "outputs"
    log_dir = exp_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    paths = split_paths(config)
    req = required_columns(config)
    train, train_fill = load_join(paths["train_features"], paths["train_labels"], req)
    val, val_fill = load_join(paths["val_features"], paths["val_labels"], req)
    test, test_fill = load_join(paths["test_features"], paths["test_labels"], req)
    train, val, test = normalize(config, train, val, test)
    results, predictions = run(config, train, val, test)
    metadata_filled = {"train": train_fill, "validation": val_fill, "test": test_fill}
    results.to_csv(out_dir / "result_sheet.csv", index=False)
    results.to_csv(out_dir / "metrics_long.csv", index=False)
    predictions.to_csv(out_dir / "predictions.csv", index=False)
    if config.get("_interaction_mappings"):
        pd.DataFrame(config["_interaction_mappings"]).to_csv(out_dir / "interaction_mapping.csv", index=False)
    source_files = copy_sources(paths, exp_dir)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment_id": config["experiment_id"],
        "config": config["config_path"],
        "source_files": source_files,
        "metadata_filled": metadata_filled,
        "run_mode": config["run_mode"],
    }
    (out_dir / "experiment_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "result_sheet.html").write_text(render_html(config, results, metadata_filled), encoding="utf-8")
    (exp_dir / "README.md").write_text(render_readme(config, results, metadata_filled), encoding="utf-8")
    (log_dir / "run.log").write_text(f"{datetime.now().isoformat(timespec='seconds')} PRE-WARM-08 completed rows={len(results)}\n", encoding="utf-8")
    print(results.sort_values(["split", "MdAPE", "p95_APE"]).to_string(index=False))


if __name__ == "__main__":
    main()
