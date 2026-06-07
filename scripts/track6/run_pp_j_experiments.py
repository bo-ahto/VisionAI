#!/usr/bin/env python3
"""Run Track6 PP-J model-specific calibration experiments."""
from __future__ import annotations

import html
import json
import sys
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

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pre_pp_experiments import (  # noqa: E402
    ARTIFACT_MANIFEST,
    BASE_EXP_DIR,
    BASE_NUMERIC,
    REPO,
    SEED,
    SPLIT_ROOT,
    artifact_features,
    cat_indices,
    cat_ready,
    load_scope,
    metrics,
    normalize,
)


EXPERIMENTS = {
    "PP-J1": {"slug": "PP-J1_warm_huber_tail_segment_calibration", "title": "Warm Huber 큰 오차 구간 보정"},
    "PP-J2": {"slug": "PP-J2_warm_huber_contribution_segment_calibration", "title": "Warm Huber 계수 기여도 구간 보정"},
    "PP-J3": {"slug": "PP-J3_warm_catboost_leaf_artist_size_calibration", "title": "Warm CatBoost leaf/artist-size 보정"},
    "PP-J4": {"slug": "PP-J4_cold_catboost_leaf_coverage_calibration", "title": "Cold CatBoost leaf coverage 보정"},
    "PP-J5": {"slug": "PP-J5_cold_catboost_depth_size_calibration", "title": "Cold CatBoost 2D/3D x 크기 보정"},
    "PP-J6": {"slug": "PP-J6_cold_lightgbm_tail_calibration", "title": "Cold LightGBM tail 구간 보정"},
}


def split_types(features: list[str]) -> tuple[list[str], list[str]]:
    numeric = [c for c in features if c in BASE_NUMERIC]
    categorical = [c for c in features if c not in numeric]
    return numeric, categorical


def huber_pipeline(features: list[str]) -> Pipeline:
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


def lightgbm_pipeline(features: list[str]) -> Pipeline:
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


def cat_model(train: pd.DataFrame, features: list[str]) -> CatBoostRegressor:
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
    model.fit(cat_ready(train, features), train["ln_price_krw"].to_numpy(dtype=float), cat_features=cat_indices(features))
    return model


def pred_bins(pred_log: np.ndarray, low: float | None = None, high: float | None = None) -> tuple[np.ndarray, float, float]:
    if low is None or high is None:
        low, high = np.quantile(pred_log, [0.33, 0.66])
    return np.select([pred_log <= low, pred_log <= high], ["low", "mid"], default="high").astype(str), float(low), float(high)


def contribution_bins(values: np.ndarray, prefix: str, cuts: tuple[float, float] | None = None) -> tuple[np.ndarray, tuple[float, float]]:
    if cuts is None:
        cuts = tuple(float(x) for x in np.quantile(values, [0.33, 0.66]))
    low, high = cuts
    labels = np.select([values <= low, values <= high], [f"{prefix}_low", f"{prefix}_mid"], default=f"{prefix}_high").astype(str)
    return labels, (low, high)


def depth_3d_segment(frame: pd.DataFrame) -> np.ndarray:
    is_3d = frame["is_3d_candidate"].astype(str).str.lower().isin(["true", "1", "yes"])
    has_depth = frame["has_depth"].astype(str).str.lower().isin(["true", "1", "yes"])
    return np.select([is_3d, has_depth], ["3d_candidate", "has_depth"], default="flat_2d").astype(str)


def residual_map(actual_log: np.ndarray, pred_log: np.ndarray, segment: np.ndarray, min_rows: int = 30, cap: float | None = None) -> pd.DataFrame:
    residual = actual_log - pred_log
    rows = []
    for seg in sorted(pd.Series(segment).astype(str).unique()):
        mask = segment.astype(str) == seg
        n = int(mask.sum())
        med = float(np.median(residual[mask])) if n else float("nan")
        if cap is not None and not np.isnan(med):
            med = float(np.clip(med, -cap, cap))
        rows.append({"segment": seg, "n": n, "median_residual_log": med, "usable": bool(n >= min_rows)})
    return pd.DataFrame(rows)


def apply_map(pred_log: np.ndarray, segment: np.ndarray, cmap: pd.DataFrame, fallback: float = 0.0) -> np.ndarray:
    values = {str(r.segment): float(r.median_residual_log) for r in cmap.itertuples() if bool(r.usable)}
    return pred_log + np.array([values.get(str(seg), fallback) for seg in segment], dtype=float)


def leaf_segment(model: CatBoostRegressor, frame: pd.DataFrame, features: list[str], n_trees: int = 16) -> np.ndarray:
    leaves = model.calc_leaf_indexes(cat_ready(frame, features))
    clipped = leaves[:, : min(n_trees, leaves.shape[1])]
    return np.array(["leaf_" + str(abs(hash(tuple(row.tolist()))) % 100000) for row in clipped])


def pred_frame(exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str, status: str = "ok") -> pd.DataFrame:
    out = pd.DataFrame({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "segment_rule": segment_rule,
        "status": status,
        "_track6_row_id": frame["_track6_row_id"],
        "actual_log": frame["ln_price_krw"],
        "pred_log": pred_log,
        "actual_price": frame["price_krw"],
        "pred_price": np.clip(np.exp(pred_log), 1_000.0, None),
    })
    out["ape"] = np.abs(out["pred_price"] - out["actual_price"]) / out["actual_price"]
    out["residual_log"] = out["actual_log"] - out["pred_log"]
    return out


def add_metric(rows: list[dict[str, Any]], exp_id: str, candidate: str, scope: str, split: str, frame: pd.DataFrame, pred_log: np.ndarray, segment_rule: str, status: str = "ok", notes: str = "") -> None:
    rows.append({
        "experiment_id": exp_id,
        "candidate": candidate,
        "scope": scope,
        "split": split,
        "segment_rule": segment_rule,
        "status": status,
        "notes": notes,
        **metrics(frame, pred_log),
    })


def model_predictions(scope: str, model_name: str, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[Any, dict[str, np.ndarray]]:
    if model_name == "huber":
        model = huber_pipeline(features)
        model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
        return model, {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    if model_name == "lightgbm":
        model = lightgbm_pipeline(features)
        model.fit(train[features], train["ln_price_krw"].to_numpy(dtype=float))
        return model, {
            "validation": np.asarray(model.predict(val[features]), dtype=float),
            "test": np.asarray(model.predict(test[features]), dtype=float),
        }
    model = cat_model(train, features)
    return model, {
        "validation": np.asarray(model.predict(cat_ready(val, features)), dtype=float),
        "test": np.asarray(model.predict(cat_ready(test, features)), dtype=float),
    }


def huber_contributions(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict[str, np.ndarray]:
    prep = model.named_steps["prep"]
    reg = model.named_steps["model"]
    matrix = prep.transform(frame[features])
    names = list(prep.get_feature_names_out())
    coef = reg.coef_
    contrib = matrix.multiply(coef).toarray() if hasattr(matrix, "multiply") else matrix * coef
    groups = {
        "size": ["width_cm", "height_cm", "area_cm2", "log_area", "aspect_ratio"],
        "medium_support": ["medium_category", "support_category", "medium_support_bucket"],
        "artist": ["artist_key"],
    }
    out = {}
    for group, tokens in groups.items():
        idx = [i for i, name in enumerate(names) if any(token in name for token in tokens)]
        out[group] = contrib[:, idx].sum(axis=1) if idx else np.zeros(len(frame))
    return out


def render(exp_id: str, metrics_df: pd.DataFrame, cmap_df: pd.DataFrame) -> tuple[str, str]:
    title = EXPERIMENTS[exp_id]["title"]
    val = metrics_df[metrics_df["split"].eq("validation")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"])
    lines = [
        f"# {exp_id} {title}",
        "",
        "- 목적: 모델 구조에 맞춘 segment 기준으로 residual 보정 후보를 검증한다.",
        "- 기준: validation residual로 correction map을 만들고 test에는 같은 map을 적용한다.",
        "",
        "## Validation 결과",
        "",
        "| scope | 후보 | segment 기준 | MdAPE | MAPE | p95_APE | RMSE_log |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in val.itertuples():
        lines.append(f"| `{row.scope}` | `{row.candidate}` | `{row.segment_rule}` | `{row.MdAPE:.4f}` | `{row.MAPE:.4f}` | `{row.p95_APE:.4f}` | `{row.RMSE_log:.4f}` |")
    lines += ["", "## 코멘터리", ""]
    baseline = val[val["candidate"].eq("baseline")]
    if not baseline.empty:
        b = baseline.iloc[0]
        for row in val[val["candidate"].ne("baseline")].itertuples():
            lines.append(
                f"- `{row.segment_rule}`: MdAPE delta `{row.MdAPE - b.MdAPE:.4f}`, "
                f"MAPE delta `{row.MAPE - b.MAPE:.4f}`, p95 delta `{row.p95_APE - b.p95_APE:.4f}`."
            )
    if not cmap_df.empty:
        usable = int(cmap_df["usable"].sum()) if "usable" in cmap_df.columns else 0
        lines.append(f"- usable correction segment: `{usable}`개.")
    md = "\n".join(lines) + "\n"
    html_doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(exp_id)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif;margin:28px;color:#1f2933}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border:1px solid #d8dee4;padding:7px;text-align:left}}th{{background:#eef2f7}}</style></head>
<body><h1>{html.escape(exp_id)} {html.escape(title)}</h1><h2>Metrics</h2>{metrics_df.to_html(index=False, escape=True)}
<h2>Correction Map</h2>{cmap_df.head(140).to_html(index=False, escape=True) if not cmap_df.empty else '<p>No map</p>'}</body></html>"""
    return md, html_doc


def write_exp(exp_id: str, metrics_rows: list[dict[str, Any]], predictions: list[pd.DataFrame], maps: list[pd.DataFrame], config: dict[str, Any]) -> None:
    exp_dir = BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]
    for sub in ["data", "outputs", "reports", "artifacts", "logs"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)
    metrics_df = pd.DataFrame(metrics_rows)
    pred_df = pd.concat(predictions, ignore_index=True)
    cmap_df = pd.concat(maps, ignore_index=True) if maps else pd.DataFrame()
    metrics_df.to_csv(exp_dir / "outputs" / "metrics.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "predictions.csv", index=False)
    pred_df.to_csv(exp_dir / "outputs" / "residuals.csv", index=False)
    cmap_df.to_csv(exp_dir / "outputs" / "correction_map.csv", index=False)
    pred_df[pred_df["split"].eq("validation")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "valid_index.csv", index=False)
    pred_df[pred_df["split"].eq("test")][["scope", "split", "_track6_row_id"]].drop_duplicates().to_csv(exp_dir / "data" / "test_index.csv", index=False)
    (exp_dir / "data" / "split_manifest.json").write_text(json.dumps({"split_root": str(SPLIT_ROOT.relative_to(REPO)), "policy": "validation correction map applied to test"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "data" / "feature_columns.json").write_text(json.dumps(config["feature_columns"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "model_manifest.json").write_text(json.dumps(config["model_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "artifacts" / "calibration_map.json").write_text(json.dumps(cmap_df.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    md, html_doc = render(exp_id, metrics_df, cmap_df)
    (exp_dir / "README.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.md").write_text(md, encoding="utf-8")
    (exp_dir / "reports" / "result_report.html").write_text(html_doc, encoding="utf-8")
    (exp_dir / "logs" / "run_log.txt").write_text(f"{datetime.now().isoformat(timespec='seconds')} {exp_id} completed\n", encoding="utf-8")


def run_calibrated(
    exp_id: str,
    scope: str,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    pred: dict[str, np.ndarray],
    val_seg: np.ndarray,
    test_seg: np.ndarray,
    segment_rule: str,
    min_rows: int = 30,
    cap: float | None = None,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for split_name, frame, p in [("validation", val, pred["validation"]), ("test", test, pred["test"])]:
        add_metric(rows, exp_id, "baseline", scope, split_name, frame, p, "none")
        preds.append(pred_frame(exp_id, "baseline", scope, split_name, frame, p, "none"))
    cmap = residual_map(val["ln_price_krw"].to_numpy(dtype=float), pred["validation"], val_seg, min_rows=min_rows, cap=cap)
    corr_val = apply_map(pred["validation"], val_seg, cmap)
    corr_test = apply_map(pred["test"], test_seg, cmap)
    for split_name, frame, p in [("validation", val, corr_val), ("test", test, corr_test)]:
        add_metric(rows, exp_id, f"corrected_{segment_rule}", scope, split_name, frame, p, segment_rule)
        preds.append(pred_frame(exp_id, f"corrected_{segment_rule}", scope, split_name, frame, p, segment_rule))
    cmap.insert(0, "experiment_id", exp_id)
    cmap.insert(1, "scope", scope)
    cmap.insert(2, "segment_rule", segment_rule)
    return rows, preds, cmap


def main() -> None:
    start = time.time()
    features = artifact_features()
    warm_features = features["warm"]
    cold_cb_features = features["cold_catboost"]
    cold_lgb_features = features["cold_lightgbm"]

    warm_train, warm_val, warm_test = load_scope("warm", warm_features)
    warm_train, warm_val, warm_test = normalize(warm_train, warm_features), normalize(warm_val, warm_features), normalize(warm_test, warm_features)
    cold_train, cold_val, cold_test = load_scope("cold", cold_cb_features)
    cold_train, cold_val, cold_test = normalize(cold_train, cold_cb_features), normalize(cold_val, cold_cb_features), normalize(cold_test, cold_cb_features)
    lgb_train, lgb_val, lgb_test = load_scope("cold", cold_lgb_features)
    lgb_train, lgb_val, lgb_test = normalize(lgb_train, cold_lgb_features), normalize(lgb_val, cold_lgb_features), normalize(lgb_test, cold_lgb_features)

    warm_huber, warm_pred = model_predictions("warm", "huber", warm_train, warm_val, warm_test, warm_features)
    warm_cat, warm_cat_pred = model_predictions("warm", "catboost", warm_train, warm_val, warm_test, warm_features)
    cold_cat, cold_pred = model_predictions("cold", "catboost", cold_train, cold_val, cold_test, cold_cb_features)
    lgb_model, lgb_pred = model_predictions("cold", "lightgbm", lgb_train, lgb_val, lgb_test, cold_lgb_features)

    summary_rows = []
    experiment_outputs: dict[str, tuple[list[dict[str, Any]], list[pd.DataFrame], list[pd.DataFrame], dict[str, Any]]] = {}

    # PP-J1: Warm Huber high-risk pred x size with capped correction.
    val_bin, lo, hi = pred_bins(warm_pred["validation"])
    test_bin, _lo, _hi = pred_bins(warm_pred["test"], lo, hi)
    val_seg = np.array([f"{p}__{s}" for p, s in zip(val_bin, warm_val["size_bucket"].astype(str), strict=False)])
    test_seg = np.array([f"{p}__{s}" for p, s in zip(test_bin, warm_test["size_bucket"].astype(str), strict=False)])
    rows, preds, cmap = run_calibrated("PP-J1", "warm", warm_train, warm_val, warm_test, warm_pred, val_seg, test_seg, "pred_bin_size_tail_cap", min_rows=20, cap=0.45)
    experiment_outputs["PP-J1"] = (rows, preds, [cmap], {"feature_columns": {"warm": warm_features}, "model_manifest": {"model": "Warm Huber", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    # PP-J2: Huber coefficient contribution bins.
    val_contrib = huber_contributions(warm_huber, warm_val, warm_features)
    test_contrib = huber_contributions(warm_huber, warm_test, warm_features)
    size_val, size_cuts = contribution_bins(val_contrib["size"], "size_contrib")
    size_test, _ = contribution_bins(test_contrib["size"], "size_contrib", size_cuts)
    med_val, med_cuts = contribution_bins(val_contrib["medium_support"], "medium_support_contrib")
    med_test, _ = contribution_bins(test_contrib["medium_support"], "medium_support_contrib", med_cuts)
    artist_val, artist_cuts = contribution_bins(val_contrib["artist"], "artist_contrib")
    artist_test, _ = contribution_bins(test_contrib["artist"], "artist_contrib", artist_cuts)
    val_seg = np.array([f"{s}__{m}__{a}" for s, m, a in zip(size_val, med_val, artist_val, strict=False)])
    test_seg = np.array([f"{s}__{m}__{a}" for s, m, a in zip(size_test, med_test, artist_test, strict=False)])
    rows, preds, cmap = run_calibrated("PP-J2", "warm", warm_train, warm_val, warm_test, warm_pred, val_seg, test_seg, "huber_contribution_bins", min_rows=15, cap=0.45)
    experiment_outputs["PP-J2"] = (rows, preds, [cmap], {"feature_columns": {"warm": warm_features}, "model_manifest": {"model": "Warm Huber", "contribution_cuts": {"size": size_cuts, "medium_support": med_cuts, "artist": artist_cuts}, "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    # PP-J3: Warm CatBoost leaf with artist-size fallback style segment.
    leaf_val = leaf_segment(warm_cat, warm_val, warm_features)
    leaf_test = leaf_segment(warm_cat, warm_test, warm_features)
    artist_size_val = np.array([f"{a}__{s}" for a, s in zip(warm_val["artist_key"].astype(str), warm_val["size_bucket"].astype(str), strict=False)])
    artist_size_test = np.array([f"{a}__{s}" for a, s in zip(warm_test["artist_key"].astype(str), warm_test["size_bucket"].astype(str), strict=False)])
    val_seg = np.array([f"{l}__{a}" for l, a in zip(leaf_val, artist_size_val, strict=False)])
    test_seg = np.array([f"{l}__{a}" for l, a in zip(leaf_test, artist_size_test, strict=False)])
    rows, preds, cmap = run_calibrated("PP-J3", "warm", warm_train, warm_val, warm_test, warm_cat_pred, val_seg, test_seg, "warm_catboost_leaf_artist_size", min_rows=10, cap=0.50)
    experiment_outputs["PP-J3"] = (rows, preds, [cmap], {"feature_columns": {"warm_catboost": warm_features}, "model_manifest": {"model": "Warm CatBoost candidate", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    # PP-J4: Cold CatBoost leaf coverage, compare min rows.
    maps: list[pd.DataFrame] = []
    all_rows: list[dict[str, Any]] = []
    all_preds: list[pd.DataFrame] = []
    leaf_val = leaf_segment(cold_cat, cold_val, cold_cb_features)
    leaf_test = leaf_segment(cold_cat, cold_test, cold_cb_features)
    for min_rows in [20, 50, 100]:
        rows, preds, cmap = run_calibrated("PP-J4", "cold", cold_train, cold_val, cold_test, cold_pred, leaf_val, leaf_test, f"leaf_segment_min_rows_{min_rows}", min_rows=min_rows, cap=0.60)
        all_rows.extend(rows)
        all_preds.extend(preds)
        maps.append(cmap)
    experiment_outputs["PP-J4"] = (all_rows, all_preds, maps, {"feature_columns": {"cold_catboost": cold_cb_features}, "model_manifest": {"model": "Cold CatBoost", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    # PP-J5: Cold CatBoost 2D/3D x size x medium-shape.
    val_seg = np.array([f"{d}__{s}__{m}" for d, s, m in zip(depth_3d_segment(cold_val), cold_val["size_bucket"].astype(str), cold_val["medium_shape_bucket"].astype(str), strict=False)])
    test_seg = np.array([f"{d}__{s}__{m}" for d, s, m in zip(depth_3d_segment(cold_test), cold_test["size_bucket"].astype(str), cold_test["medium_shape_bucket"].astype(str), strict=False)])
    rows, preds, cmap = run_calibrated("PP-J5", "cold", cold_train, cold_val, cold_test, cold_pred, val_seg, test_seg, "depth_3d_size_medium_shape", min_rows=30, cap=0.60)
    experiment_outputs["PP-J5"] = (rows, preds, [cmap], {"feature_columns": {"cold_catboost": cold_cb_features}, "model_manifest": {"model": "Cold CatBoost", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    # PP-J6: Cold LightGBM tail with cap.
    pred_bin_val, lo, hi = pred_bins(lgb_pred["validation"])
    pred_bin_test, _lo, _hi = pred_bins(lgb_pred["test"], lo, hi)
    val_seg = np.array([f"{p}__{s}" for p, s in zip(pred_bin_val, lgb_val["support_size_bucket"].astype(str), strict=False)])
    test_seg = np.array([f"{p}__{s}" for p, s in zip(pred_bin_test, lgb_test["support_size_bucket"].astype(str), strict=False)])
    maps = []
    all_rows = []
    all_preds = []
    for cap in [0.25, 0.50, 0.75]:
        rows, preds, cmap = run_calibrated("PP-J6", "cold", lgb_train, lgb_val, lgb_test, lgb_pred, val_seg, test_seg, f"lgb_tail_support_size_cap_{cap}", min_rows=30, cap=cap)
        all_rows.extend(rows)
        all_preds.extend(preds)
        maps.append(cmap)
    experiment_outputs["PP-J6"] = (all_rows, all_preds, maps, {"feature_columns": {"cold_lightgbm": cold_lgb_features}, "model_manifest": {"model": "Cold LightGBM", "source_artifact_manifest": str(ARTIFACT_MANIFEST.relative_to(REPO))}})

    for exp_id, (rows, preds, maps, config) in experiment_outputs.items():
        full_config = {
            "experiment_id": exp_id,
            "title": EXPERIMENTS[exp_id]["title"],
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "seed": SEED,
            **config,
        }
        write_exp(exp_id, rows, preds, maps, full_config)
        df = pd.DataFrame(rows)
        best = df[df["split"].eq("validation")].sort_values(["scope", "MdAPE", "MAPE", "p95_APE"]).groupby("scope").head(1)
        for _idx, item in best.iterrows():
            out = item.to_dict()
            out["folder"] = str((BASE_EXP_DIR / EXPERIMENTS[exp_id]["slug"]).relative_to(REPO))
            summary_rows.append(out)

    pd.DataFrame(summary_rows).to_csv(BASE_EXP_DIR / "PP-J_summary_metrics.csv", index=False)
    print(json.dumps({
        "status": "completed",
        "seconds": round(time.time() - start, 2),
        "summary": "experiments/track6/PP-J_summary_metrics.csv",
        "experiments": {k: str((BASE_EXP_DIR / v["slug"]).relative_to(REPO)) for k, v in EXPERIMENTS.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
