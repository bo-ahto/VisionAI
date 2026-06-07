#!/usr/bin/env python3
"""Run Track6 PRE-PP group-drop experiments in postprocessing order."""
from __future__ import annotations

import html
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = REPO / "data" / "track6_split"
ARTIFACT_MANIFEST = REPO / "data" / "track6" / "artifacts" / "track6_artifact_manifest.json"
BASE_EXP_DIR = REPO / "experiments" / "track6"
SEED = 20260602

BASE_NUMERIC = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio"]
GENERATED = [
    "size_bucket",
    "shape_bucket",
    "medium_size_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]

EXPERIMENTS = {
    "PRE-PP-W": {
        "slug": "PRE-PP-W_warm_huber_group_drop_ablation",
        "title": "Warm Huber group-drop ablation",
        "scope": "warm",
        "model": "huber",
        "feature_key": "warm",
        "drop_groups": {
            "drop_size": ["width_cm", "height_cm", "area_cm2", "log_area"],
            "drop_medium_support": ["medium_category", "support_category", "medium_support_bucket"],
            "drop_depth_3d": ["depth_cm", "has_depth", "is_3d_candidate"],
            "drop_shape_aspect": ["aspect_ratio", "is_extreme_aspect_ratio"],
        },
    },
    "PRE-PP-CB": {
        "slug": "PRE-PP-CB_cold_catboost_group_drop_ablation",
        "title": "Cold CatBoost group-drop ablation",
        "scope": "cold",
        "model": "catboost",
        "feature_key": "cold_catboost",
        "drop_groups": {
            "drop_depth_3d": ["depth_cm", "has_depth", "is_3d_candidate"],
            "drop_shape": ["shape_bucket", "aspect_ratio"],
            "drop_medium_shape": ["medium_shape_bucket"],
            "drop_size": ["width_cm", "height_cm", "area_cm2", "log_area"],
        },
    },
    "PRE-PP-LGB": {
        "slug": "PRE-PP-LGB_cold_lightgbm_group_drop_ablation",
        "title": "Cold LightGBM group-drop ablation",
        "scope": "cold",
        "model": "lightgbm",
        "feature_key": "cold_lightgbm",
        "drop_groups": {
            "drop_size_bucket": ["size_bucket"],
            "drop_support_size": ["support_size_bucket"],
            "drop_raw_size": ["width_cm", "height_cm", "area_cm2", "log_area"],
            "drop_depth_3d": ["depth_cm", "has_depth", "is_3d_candidate"],
        },
    },
}


def artifact_features() -> dict[str, list[str]]:
    manifest = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for item in manifest["artifacts"]:
        if item["key"] == "warm_price_model":
            out["warm"] = item["features"]
        elif item["key"] == "cold_catboost_price_model":
            out["cold_catboost"] = item["features"]
        elif item["key"] == "cold_lightgbm_price_model":
            out["cold_lightgbm"] = item["features"]
    return out


def read_join(feature_path: Path, label_path: Path, columns: list[str]) -> pd.DataFrame:
    features = pd.read_csv(feature_path, low_memory=False)
    labels = pd.read_csv(label_path, low_memory=False)
    label_cols = ["_track6_row_id", "price_krw", "ln_price_krw"]
    for col in ["artist_key", "artist_name_ko", "has_depth", "is_3d_candidate"]:
        if col in labels.columns:
            label_cols.append(col)
    merged = features.merge(labels[label_cols], on="_track6_row_id", how="inner", suffixes=("", "__label"))
    for col in columns:
        label_col = f"{col}__label"
        if col not in merged.columns and col in labels.columns:
            merged[col] = labels.set_index("_track6_row_id").loc[merged["_track6_row_id"], col].to_numpy()
        elif col in merged.columns and label_col in merged.columns:
            merged[col] = merged[col].where(merged[col].notna(), merged[label_col])
    missing = [c for c in columns if c not in merged.columns and c not in GENERATED]
    if missing:
        raise ValueError(f"{feature_path} missing columns: {missing}")
    merged["price_krw"] = pd.to_numeric(merged["price_krw"], errors="coerce")
    merged["ln_price_krw"] = pd.to_numeric(merged["ln_price_krw"], errors="coerce")
    return merged.dropna(subset=["price_krw", "ln_price_krw"]).sort_values("_track6_row_id").reset_index(drop=True)


def add_generated(train: pd.DataFrame, *frames: pd.DataFrame) -> list[pd.DataFrame]:
    values = pd.to_numeric(train["log_area"], errors="coerce").dropna()
    edges = np.quantile(values, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)
    large_cut = float(np.nanquantile(pd.to_numeric(train["area_cm2"], errors="coerce"), 0.80))

    def transform(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        log_area = pd.to_numeric(out["log_area"], errors="coerce")
        aspect = pd.to_numeric(out["aspect_ratio"], errors="coerce")
        area = pd.to_numeric(out["area_cm2"], errors="coerce")
        is_3d = out["is_3d_candidate"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])
        labels = [f"q{i + 1}" for i in range(len(edges) - 1)]
        out["size_bucket"] = pd.cut(log_area, bins=edges, labels=labels, include_lowest=True).astype(str)
        out.loc[log_area.isna(), "size_bucket"] = "__MISSING__"
        out["shape_bucket"] = np.select(
            [aspect.isna(), aspect < 0.65, aspect <= 1.55, aspect <= 2.5, aspect > 2.5],
            ["__MISSING__", "tall", "balanced", "wide", "extreme_wide"],
            default="__MISSING__",
        )
        out["medium_size_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["support_size_bucket"] = out["support_category"].fillna("__MISSING__").astype(str) + "__" + out["size_bucket"].astype(str)
        out["medium_shape_bucket"] = out["medium_category"].fillna("__MISSING__").astype(str) + "__" + out["shape_bucket"].astype(str)
        out["is_large_2d"] = ((area >= large_cut) & ~is_3d).astype(str)
        out["is_large_3d"] = ((area >= large_cut) & is_3d).astype(str)
        return out

    return [transform(frame) for frame in (train, *frames)]


def load_scope(scope: str, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_dir = SPLIT_ROOT / "features" / scope
    label_dir = SPLIT_ROOT / "labels"
    prefix = "warm" if scope == "warm" else "cold"
    generation_inputs = ["area_cm2", "log_area", "aspect_ratio", "is_3d_candidate", "medium_category", "support_category"]
    required = list(dict.fromkeys([c for c in features if c not in GENERATED] + generation_inputs))
    train = read_join(feature_dir / f"track6_train_{prefix}_features.csv", label_dir / "track6_train_labels.csv", required)
    val = read_join(feature_dir / f"track6_val_{prefix}_{prefix}_features.csv", label_dir / f"track6_val_{prefix}_labels.csv", required)
    test = read_join(feature_dir / f"track6_test_{prefix}_{prefix}_features.csv", label_dir / f"track6_test_{prefix}_labels.csv", required)
    return tuple(add_generated(train, val, test))  # type: ignore[return-value]


def normalize(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in features:
        if col in BASE_NUMERIC:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("string").fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in features if c in BASE_NUMERIC]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def huber_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10, sparse_output=True)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", min_frequency=10)
        transformers.append(("cat", encoder, categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=3000)),
    ])


def lightgbm_model(features: list[str]) -> Pipeline:
    numeric, categorical = split_types(features)
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), numeric))
    if categorical:
        transformers.append(("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical))
    return Pipeline([
        ("prep", ColumnTransformer(transformers)),
        ("model", LGBMRegressor(
            objective="regression",
            n_estimators=350,
            learning_rate=0.04,
            num_leaves=31,
            min_child_samples=40,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=SEED,
            verbosity=-1,
        )),
    ])


def cat_ready(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    out = frame[features].copy()
    numeric, categorical = split_types(features)
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in categorical:
        out[col] = out[col].astype(str).fillna("__MISSING__")
    return out


def cat_indices(features: list[str]) -> list[int]:
    numeric, _ = split_types(features)
    return [idx for idx, col in enumerate(features) if col not in numeric]


def fit_predict(model_name: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    y = train["ln_price_krw"].to_numpy(dtype=float)
    if model_name == "huber":
        model = huber_model(features)
        model.fit(train[features], y)
        return {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    if model_name == "lightgbm":
        model = lightgbm_model(features)
        model.fit(train[features], y)
        return {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=500,
        learning_rate=0.04,
        depth=6,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(cat_ready(train, features), y, cat_features=cat_indices(features))
    return {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def metrics(frame: pd.DataFrame, pred_log: np.ndarray) -> dict[str, float]:
    actual_price = frame["price_krw"].to_numpy(dtype=float)
    actual_log = frame["ln_price_krw"].to_numpy(dtype=float)
    pred_price = np.clip(np.exp(pred_log), 1_000.0, None)
    ape = np.abs(pred_price - actual_price) / actual_price
    return {
        "RMSE_log": float(np.sqrt(np.mean((pred_log - actual_log) ** 2))),
        "MdAPE": float(np.median(ape)),
        "MAPE": float(np.mean(ape)),
        "p95_APE": float(np.quantile(ape, 0.95)),
        "Within_30": float(np.mean(ape <= 0.30)),
        "Within_50": float(np.mean(ape <= 0.50)),
    }


def prediction_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray) -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    return out


def render(exp_id: str, info: dict[str, Any], metrics_df: pd.DataFrame) -> tuple[str, str]:
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {info['title']}",
        "",
        "- 목적: 후처리 보정 기준으로 사용할 피처/구간 그룹의 실제 성능 기여를 확인한다.",
        "- 방법: final artifact 기준 피처셋에서 그룹을 하나씩 제거하고 같은 split/모델 설정으로 재학습한다.",
        "- 해석: 제거 후 성능이 악화되면 해당 그룹은 후처리 segment 기준으로 유지할 근거가 있다.",
        "",
        "## Validation 결과",
        "",
        "| 후보 | 제거 그룹 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.candidate}` | `{row.drop_group}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    baseline = val[val["candidate"].eq("baseline")]
    if not baseline.empty:
        b = baseline.iloc[0]
        lines += ["", "## 코멘터리", ""]
        for row in val[val["candidate"].ne("baseline")].itertuples():
            md_delta = row.MdAPE - b.MdAPE
            p95_delta = row.p95_APE - b.p95_APE
            direction = "악화" if md_delta > 0 else "개선"
            lines.append(
                f"- `{row.drop_group}` 제거: MdAPE delta `{md_delta:.4f}`, p95 delta `{p95_delta:.4f}`로 `{direction}`. "
                "악화라면 해당 그룹은 보정 기준으로 남길 근거가 있다."
            )
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(info['title'])}</h1>{metrics_df.to_html(index=False, escape=True)}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, info: dict[str, Any], metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / info["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    split_manifest = {
        "split_root": str(SPLIT_ROOT.relative_to(REPO)),
        "train": "track6_train",
        "validation": f"track6_val_{info['scope']}",
        "test": f"track6_test_{info['scope']}",
    }
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps(split_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, info, metrics_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def main() -> None:
    start = time.time()
    features_by_key = artifact_features()
    summary_rows = []
    for exp_id, info in EXPERIMENTS.items():
        features = features_by_key[info["feature_key"]]
        train, val, test = load_scope(info["scope"], features)
        train = normalize(train, features)
        val = normalize(val, features)
        test = normalize(test, features)
        candidates: list[tuple[str, str, list[str]]] = [("baseline", "none", features)]
        for group_name, drop_cols in info["drop_groups"].items():
            cols = [col for col in features if col not in set(drop_cols)]
            candidates.append((f"without_{group_name}", group_name, cols))

        rows: list[dict[str, Any]] = []
        preds: list[pd.DataFrame] = []
        for candidate, drop_group, cols in candidates:
            pred = fit_predict(info["model"], train, val, test, cols)
            for split_name, frame in [("validation", val), ("test", test)]:
                pred_df = prediction_frame(exp_id, candidate, info["scope"], split_name, frame, pred[split_name])
                m = metrics(frame, pred[split_name])
                row = {
                    "experiment_id": exp_id,
                    "candidate": candidate,
                    "drop_group": drop_group,
                    "scope": info["scope"],
                    "split": split_name,
                    "model": info["model"],
                    "n_features": len(cols),
                    "features": ", ".join(cols),
                    **m,
                }
                rows.append(row)
                preds.append(pred_df)
        config = {
            "experiment_id": exp_id,
            "title": info["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            "feature_columns": {"baseline": features, "candidates": {c: cols for c, _g, cols in candidates}},
            "model_manifest": {
                "model": info["model"],
                "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO)),
                "target": "ln_price_krw",
            },
        }
        write_exp(exp_id, info, rows, preds, config)
        best = pd.DataFrame(rows)
        val_best = best[best["split"].eq("validation")].sort_values(["MdAPE", "MAPE", "p95_APE"]).iloc[0].to_dict()
        val_best["folder"] = str((BASE_EXP_DIR / info["slug"]).relative_to(REPO))
        summary_rows.append(val_best)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(BASE_EXP_DIR / "PRE-PP_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PRE-PP_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
