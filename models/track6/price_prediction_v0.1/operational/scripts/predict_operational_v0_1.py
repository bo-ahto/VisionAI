#!/usr/bin/env python3
"""Run operational price_prediction v0.1 inference from feature files."""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


def find_repo_root(start: Path) -> Path:
    for current in [start, *start.parents]:
        if (current / "scripts" / "track6").exists() and (current / "models" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
from run_pp_l10_warm_l8_feature_variant_experiments import (  # noqa: E402
    add_quantile_features,
    cat_indices as l10_cat_indices,
    cat_ready as l10_cat_ready,
    normalize_frame as l10_normalize_frame,
)


MODEL_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1"
OP_ROOT = MODEL_ROOT / "operational"
ARTIFACT_DIR = OP_ROOT / "artifacts"
DEFAULT_FEATURE_DIR = OP_ROOT / "outputs" / "0604_features"
DEFAULT_OUTPUT_DIR = OP_ROOT / "outputs" / "0604_predictions"

FX_KRW_PER_UNIT = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}

SERVICE_PRIMARY_CANDIDATE = "pp_v8_compact_blend_mape_guarded"
REPORT_70_30_CANDIDATE = "v01_operational"

ID_COLUMNS = [
    "_v01_row_id",
    "_track6_row_id",
    "slug",
    "title",
    "artist_name",
    "artist_slug",
    "matched_train_artist",
    "artist_key",
    "artist_match_source",
    "artist_match_status",
    "warm_cold_route",
    "artwork_url",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run operational v0.1 inference.")
    parser.add_argument("--feature-dir", type=Path, default=DEFAULT_FEATURE_DIR, help="feature output directory")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="prediction output directory")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def add_price_columns(frame: pd.DataFrame, log_col: str, price_col: str) -> None:
    frame[price_col] = safe_exp(frame[log_col])
    prefix = price_col.removesuffix("_krw")
    for currency, rate in FX_KRW_PER_UNIT.items():
        frame[f"{prefix}_{currency.lower()}"] = frame[price_col] / rate


def load_manifest() -> dict[str, Any]:
    path = ARTIFACT_DIR / "operational_policy_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"operational manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_catboost(rel_path: str) -> CatBoostRegressor:
    model = CatBoostRegressor()
    model.load_model(REPO / rel_path)
    return model


def ensure_dummy_label_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "ln_price_krw" not in out.columns:
        out["ln_price_krw"] = 0.0
    if "price_krw" not in out.columns:
        out["price_krw"] = 1.0
    return out


def ensure_svc_features(frame: pd.DataFrame, manifest: dict[str, Any]) -> pd.DataFrame:
    required = [*svc1.SVC_NUMERIC, *svc1.SVC_CATEGORICAL, "svc_group_n"]
    if all(col in frame.columns for col in required):
        return frame
    source_path = REPO / manifest["components"]["svc_numeric_seed_mean"]["comparable_source"]
    source = pd.read_csv(source_path, low_memory=False)
    target = ensure_dummy_label_columns(frame)
    stats = svc1.apply_comparable_stats(source, target)
    return frame.drop(columns=required, errors="ignore").merge(stats, on="_track6_row_id", how="left")


def predict_svc_seed_mean(frame: pd.DataFrame, manifest: dict[str, Any]) -> np.ndarray:
    payload = joblib.load(REPO / manifest["components"]["svc_numeric_seed_mean"]["artifact"])
    features = payload["features"]
    prepared = svc1.normalize(frame.copy(), features)
    preds = []
    for model in payload["models"]:
        preds.append(np.asarray(model.predict(prepared[features]), dtype=float))
    return np.mean(np.vstack(preds), axis=0)


def predict_l10_generated(frame: pd.DataFrame, manifest: dict[str, Any]) -> dict[str, np.ndarray]:
    info = manifest["components"]["l10_generated_bucket_seq"]
    base_features = info["base_features"]
    enriched_features = info["enriched_features"]
    numeric = set(info["numeric_features"])

    quantile_preds: dict[str, dict[str, np.ndarray]] = {"q10": {}, "q50": {}, "q90": {}}
    for label in ["q10", "q50", "q90"]:
        model = load_catboost(info["quantile_models"][label])
        quantile_preds[label]["operation"] = np.asarray(
            model.predict(l10_cat_ready(frame, base_features, numeric_for_base(base_features, numeric))),
            dtype=float,
        )
    op_q = {
        "q10": {"operation": quantile_preds["q10"]["operation"]},
        "q50": {"operation": quantile_preds["q50"]["operation"]},
        "q90": {"operation": quantile_preds["q90"]["operation"]},
    }
    enriched = add_quantile_features(frame, op_q, "operation")
    huber_payload = joblib.load(REPO / info["huber_centerline"])
    huber_model = huber_payload["model"]
    prepared = l10_normalize_frame(enriched, enriched_features, numeric)
    center = np.asarray(huber_model.predict(prepared[enriched_features]), dtype=float)
    residual_model = load_catboost(info["residual_catboost"])
    residual = np.asarray(
        residual_model.predict(l10_cat_ready(enriched, enriched_features, numeric)),
        dtype=float,
    )
    return {
        "q10": quantile_preds["q10"]["operation"],
        "q50": quantile_preds["q50"]["operation"],
        "q90": quantile_preds["q90"]["operation"],
        "sequence": center + residual,
        "quantile_width": quantile_preds["q90"]["operation"] - quantile_preds["q10"]["operation"],
        "price_range_ratio": np.exp(
            np.clip(
                quantile_preds["q90"]["operation"] - quantile_preds["q10"]["operation"],
                0.0,
                math.log(1_000.0),
            )
        ),
    }


def numeric_for_base(features: list[str], enriched_numeric: set[str]) -> set[str]:
    return {feature for feature in features if feature in enriched_numeric}


def distill_ready(frame: pd.DataFrame, features: list[str], numeric: set[str]) -> pd.DataFrame:
    out = frame[features].copy()
    for col in features:
        if col in numeric:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = out[col].astype(str).fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def predict_v2_defensive(frame: pd.DataFrame, manifest: dict[str, Any]) -> np.ndarray:
    info = manifest["components"]["pp_v2_defensive_component"]
    features = info["features"]
    numeric = set(info["numeric_features"])
    model = load_catboost(info["artifact"])
    return np.asarray(model.predict(distill_ready(frame, features, numeric)), dtype=float)


def service_confidence(frame: pd.DataFrame) -> pd.Series:
    """Assign a display tier from comparable sample count and model range width."""
    n = pd.to_numeric(frame.get("svc_group_n"), errors="coerce").fillna(0.0)
    ratio = pd.to_numeric(frame.get("l10_price_range_ratio"), errors="coerce").replace([np.inf, -np.inf], np.nan)
    ratio = ratio.fillna(ratio.median() if ratio.notna().any() else 999.0)
    confidence = pd.Series("low", index=frame.index, dtype=object)
    confidence[(n >= 10) & (ratio <= 8.0)] = "medium"
    confidence[(n >= 30) & (ratio <= 4.0)] = "high"
    return confidence


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# operational v0.1 예측 결과

- 생성일: {summary['created_at']}
- 입력 피처: `{summary['feature_file']}`
- 전체 행: {summary['total_rows']:,}
- Warm 행: {summary['warm_rows']:,}
- Cold 행: {summary['cold_rows']:,}

## 주요 컬럼

- `svc_numeric_seed_mean_pred_price_krw`
- `pp_v2_defensive_pred_price_krw`
- `l10_generated_bucket_seq_pred_price_krw`
- `pp_v8_compact_blend_mape_guarded_pred_price_krw`
- `v01_operational_pred_price_krw`
- `service_primary_pred_price_krw`
- `service_range_low_price_krw`
- `service_range_high_price_krw`
- `service_confidence_tier`

## 예측식

```text
pp_v8 = 0.75 * pp_v2_defensive + 0.25 * l10_generated_bucket_seq
report_70_30 = 0.70 * svc_numeric_seed_mean + 0.30 * pp_v8
service_primary = pp_v8
```
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    feature_dir = resolve(args.feature_dir)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_file = feature_dir / "features_all_v0_1.csv"
    if not feature_file.exists():
        raise FileNotFoundError(f"feature file not found: {feature_file}")
    manifest = load_manifest()
    features = pd.read_csv(feature_file, low_memory=False)
    warm = features[features["warm_cold_route"].astype(str).eq("warm")].copy()
    cold = features[~features["warm_cold_route"].astype(str).eq("warm")].copy()
    warm = ensure_svc_features(warm, manifest)

    out = warm[[col for col in ID_COLUMNS if col in warm.columns]].copy()
    for col in [
        "width_cm",
        "height_cm",
        "depth_cm",
        "area_cm2",
        "log_area",
        "medium_category",
        "support_category",
        "medium_support_bucket",
        "svc_group_level",
        "svc_coverage_tier",
        "svc_group_n",
    ]:
        if col in warm.columns:
            out[col] = warm[col]

    out["svc_numeric_seed_mean_pred_log"] = predict_svc_seed_mean(warm, manifest)
    l10_pred = predict_l10_generated(warm, manifest)
    out["l10_q10_pred_log"] = l10_pred["q10"]
    out["l10_q50_pred_log"] = l10_pred["q50"]
    out["l10_q90_pred_log"] = l10_pred["q90"]
    out["l10_quantile_width"] = l10_pred["quantile_width"]
    out["l10_price_range_ratio"] = l10_pred["price_range_ratio"]
    out["l10_generated_bucket_seq_pred_log"] = l10_pred["sequence"]
    out["pp_v2_defensive_pred_log"] = predict_v2_defensive(warm, manifest)
    out["pp_v8_compact_blend_mape_guarded_pred_log"] = (
        0.75 * out["pp_v2_defensive_pred_log"]
        + 0.25 * out["l10_generated_bucket_seq_pred_log"]
    )
    out["v01_operational_pred_log"] = (
        0.70 * out["svc_numeric_seed_mean_pred_log"]
        + 0.30 * out["pp_v8_compact_blend_mape_guarded_pred_log"]
    )
    for log_col, price_col in [
        ("svc_numeric_seed_mean_pred_log", "svc_numeric_seed_mean_pred_price_krw"),
        ("l10_generated_bucket_seq_pred_log", "l10_generated_bucket_seq_pred_price_krw"),
        ("pp_v2_defensive_pred_log", "pp_v2_defensive_pred_price_krw"),
        ("pp_v8_compact_blend_mape_guarded_pred_log", "pp_v8_compact_blend_mape_guarded_pred_price_krw"),
        ("v01_operational_pred_log", "v01_operational_pred_price_krw"),
        ("l10_q10_pred_log", "l10_q10_pred_price_krw"),
        ("l10_q50_pred_log", "l10_q50_pred_price_krw"),
        ("l10_q90_pred_log", "l10_q90_pred_price_krw"),
    ]:
        add_price_columns(out, log_col, price_col)
    out["service_primary_candidate"] = SERVICE_PRIMARY_CANDIDATE
    out["service_primary_pred_log"] = out[f"{SERVICE_PRIMARY_CANDIDATE}_pred_log"]
    add_price_columns(out, "service_primary_pred_log", "service_primary_pred_price_krw")
    out["service_range_low_price_krw"] = out["l10_q10_pred_price_krw"]
    out["service_range_high_price_krw"] = out["l10_q90_pred_price_krw"]
    out["service_range_low_price_usd"] = out["service_range_low_price_krw"] / FX_KRW_PER_UNIT["USD"]
    out["service_range_high_price_usd"] = out["service_range_high_price_krw"] / FX_KRW_PER_UNIT["USD"]
    out["service_confidence_tier"] = service_confidence(out)
    out["report_70_30_candidate"] = REPORT_70_30_CANDIDATE
    out["operational_model_version"] = "v0.1-operational"
    out["prediction_status"] = "warm_active"

    if not cold.empty:
        cold_out = cold[[col for col in ID_COLUMNS if col in cold.columns]].copy()
        cold_out["operational_model_version"] = "v0.1-operational"
        cold_out["prediction_status"] = "cold_reference_pending_full_artifact"
        out = pd.concat([out, cold_out], ignore_index=True, sort=False)

    pred_path = output_dir / "predictions_all.csv"
    out.to_csv(pred_path, index=False)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "feature_file": str(feature_file.relative_to(REPO)),
        "output_dir": str(output_dir.relative_to(REPO)),
        "total_rows": int(len(features)),
        "warm_rows": int(len(warm)),
        "cold_rows": int(len(cold)),
        "prediction_file": str(pred_path.relative_to(REPO)),
        "manifest": str((ARTIFACT_DIR / "operational_policy_manifest.json").relative_to(REPO)),
    }
    (output_dir / "prediction_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(output_dir, summary)
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
