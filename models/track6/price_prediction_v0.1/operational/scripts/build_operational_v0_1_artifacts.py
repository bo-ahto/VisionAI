#!/usr/bin/env python3
"""Build runnable operational artifacts for price_prediction v0.1.

This script promotes the v0.1 Warm policy from "experiment evidence" to a
runnable service artifact.

Warm operational formula:
    final_log = 0.70 * svc_numeric_seed_mean
              + 0.30 * pp_v8_compact_blend_mape_guarded

PP-V8 operational decomposition:
    pp_v8_compact_blend_mape_guarded
      = 0.75 * pp_v2_defensive_component
      + 0.25 * pp_l10_generated_bucket_seq

The L10 component is rebuilt from its actual model sequence
CatBoost Quantile -> Huber -> CatBoost residual.

The V2 component was originally a meta-stack over many experiment-only
component predictions.  Those lower-level components were not saved as service
artifacts, so v0.1 operationalizes V2 with a dedicated CatBoost model trained
to reproduce the frozen PP-V2 `huber_component_range_clipped` predictions.
This is a deliberate production artifact, not an ad-hoc runtime proxy.
"""
from __future__ import annotations

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
import run_pp_svc2_warm_comparable_stats_stability as svc2  # noqa: E402
from run_pre_pp_experiments import GENERATED, artifact_features, load_scope  # noqa: E402
from run_pp_l10_warm_l8_feature_variant_experiments import (  # noqa: E402
    add_quantile_features,
    cat_indices as l10_cat_indices,
    cat_ready as l10_cat_ready,
    fit_catboost,
    fit_huber,
    numeric_for,
    oof_huber,
    quantile_predictions,
)
from run_pp_z_warm_coldstyle_extension_experiments import load_warm_full, unique  # noqa: E402


MODEL_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1"
OP_ROOT = MODEL_ROOT / "operational"
ARTIFACT_DIR = OP_ROOT / "artifacts"
DATA_DIR = OP_ROOT / "data"
REPORT_DIR = OP_ROOT / "reports"
EXPERIMENT_ROOT = REPO / "experiments" / "track6"
SEED = 20260602

L10_GENERATED_FEATURES = [
    "artist_works_log",
    "artist_works_count_train",
    "size_bucket",
    "shape_bucket",
    "support_size_bucket",
    "medium_shape_bucket",
    "is_large_2d",
    "is_large_3d",
]

DISTILL_NUMERIC = {
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "artist_works_log",
    "artist_works_count_train",
    "svc_group_n",
    *svc1.SVC_NUMERIC,
}


def ensure_dirs() -> None:
    for path in [ARTIFACT_DIR, DATA_DIR, REPORT_DIR, OP_ROOT / "outputs"]:
        path.mkdir(parents=True, exist_ok=True)


def metric_fidelity(actual: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    diff = pred - actual
    return {
        "n": int(len(actual)),
        "MAE_log": float(np.mean(np.abs(diff))),
        "MdAE_log": float(np.median(np.abs(diff))),
        "RMSE_log": float(np.sqrt(np.mean(diff**2))),
        "p95_abs_log_error": float(np.quantile(np.abs(diff), 0.95)),
    }


def save_catboost(model: CatBoostRegressor, name: str) -> str:
    path = ARTIFACT_DIR / name
    model.save_model(path)
    return str(path.relative_to(REPO))


def build_svc_seed_models() -> dict[str, Any]:
    """Train and save the 10 Huber seed models used by svc_numeric_seed_mean."""
    base_features = artifact_features()["warm"]
    requested = unique([*base_features, *svc1.GROUPING_FEATURES])
    train_base, _val_base, _test_base = load_scope("warm", requested)
    model_features = unique([*base_features, *svc1.SVC_NUMERIC])

    models: list[Any] = []
    diagnostics: list[dict[str, Any]] = []
    for seed in svc2.SEEDS:
        train_stats = svc2.crossfit_train_stats(train_base, seed)
        train_s = train_base.merge(train_stats, on="_track6_row_id", how="left")
        train_n = svc1.normalize(train_s, model_features)
        model = svc1.huber_model(model_features)
        model.fit(train_n[model_features], train_n["ln_price_krw"].to_numpy(dtype=float))
        models.append(model)
        pred = np.asarray(model.predict(train_n[model_features]), dtype=float)
        diagnostics.append({
            "seed": int(seed),
            "train_pred_log_mean": float(np.mean(pred)),
            "train_pred_log_std": float(np.std(pred)),
        })

    payload = {
        "component": "svc_numeric_seed_mean",
        "features": model_features,
        "seeds": [int(seed) for seed in svc2.SEEDS],
        "models": models,
    }
    artifact_path = ARTIFACT_DIR / "warm_svc_numeric_seed_huber_ensemble.joblib"
    joblib.dump(payload, artifact_path)
    comparable_path = DATA_DIR / "warm_comparable_source_train.csv"
    train_base.to_csv(comparable_path, index=False)
    pd.DataFrame(diagnostics).to_csv(DATA_DIR / "warm_svc_seed_model_diagnostics.csv", index=False)
    return {
        "component": "svc_numeric_seed_mean",
        "artifact": str(artifact_path.relative_to(REPO)),
        "comparable_source": str(comparable_path.relative_to(REPO)),
        "features": model_features,
        "seeds": [int(seed) for seed in svc2.SEEDS],
        "train_rows": int(len(train_base)),
    }


def build_l10_generated_component() -> dict[str, Any]:
    """Build PP-L10 full_plus_generated_buckets sequential component."""
    warm_base = artifact_features()["warm"]
    features = unique(warm_base + L10_GENERATED_FEATURES)
    train, val, test = load_warm_full(features)
    numeric = numeric_for(features)
    quantiles = quantile_predictions(train, val, test, features, numeric)

    q_models: dict[str, str] = {}
    # Refit and save the quantile models directly, because helper returns only predictions.
    y = train["ln_price_krw"].to_numpy(dtype=float)
    for label, alpha in [("q10", 0.10), ("q50", 0.50), ("q90", 0.90)]:
        model = CatBoostRegressor(
            loss_function=f"Quantile:alpha={alpha}",
            iterations=220,
            learning_rate=0.04,
            depth=6,
            l2_leaf_reg=6.0,
            random_seed=SEED,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(l10_cat_ready(train, features, numeric), y, cat_features=l10_cat_indices(features, numeric))
        q_models[label] = save_catboost(model, f"warm_l10_generated_{label}.cbm")

    train_enriched = add_quantile_features(train, quantiles, "train")
    val_enriched = add_quantile_features(val, quantiles, "validation")
    test_enriched = add_quantile_features(test, quantiles, "test")
    enriched_features = unique(features + ["q10_log", "q50_log", "q90_log", "quantile_width", "price_range_ratio"])
    enriched_numeric = numeric_for(enriched_features)

    # Huber centerline model.
    huber_pred = fit_huber(train_enriched, val_enriched, test_enriched, enriched_features, enriched_numeric)
    # Refit the actual sklearn pipeline for persistence.
    from run_pp_l10_warm_l8_feature_variant_experiments import normalize_frame, onehot_model  # noqa: WPS433

    train_n = normalize_frame(train_enriched, enriched_features, enriched_numeric)
    huber_model = onehot_model(enriched_features, enriched_numeric)
    huber_model.fit(train_n[enriched_features], train_n["ln_price_krw"].to_numpy(dtype=float))
    huber_path = ARTIFACT_DIR / "warm_l10_generated_huber_centerline.joblib"
    joblib.dump({
        "component": "warm_l10_generated_huber_centerline",
        "features": enriched_features,
        "numeric_features": sorted(enriched_numeric),
        "model": huber_model,
    }, huber_path)

    seq_oof = oof_huber(train_enriched, enriched_features, enriched_numeric)
    residual_target = train_enriched["ln_price_krw"].to_numpy(dtype=float) - seq_oof
    residual_pred = fit_catboost(
        train_enriched,
        val_enriched,
        test_enriched,
        enriched_features,
        enriched_numeric,
        residual_target,
        loss="RMSE",
        iterations=220,
        depth=5,
    )
    residual_model = CatBoostRegressor(
        loss_function="RMSE",
        iterations=220,
        learning_rate=0.04,
        depth=5,
        l2_leaf_reg=6.0,
        random_seed=SEED,
        verbose=False,
        allow_writing_files=False,
    )
    residual_model.fit(
        l10_cat_ready(train_enriched, enriched_features, enriched_numeric),
        residual_target,
        cat_features=l10_cat_indices(enriched_features, enriched_numeric),
    )
    residual_path = save_catboost(residual_model, "warm_l10_generated_residual_catboost.cbm")

    val_seq = huber_pred["validation"] + residual_pred["validation"]
    test_seq = huber_pred["test"] + residual_pred["test"]
    metrics_rows = []
    for split, frame, pred in [("validation", val, val_seq), ("test", test, test_seq)]:
        actual_price = frame["price_krw"].to_numpy(dtype=float)
        pred_price = np.clip(np.exp(pred), 1_000.0, None)
        ape = np.abs(pred_price - actual_price) / actual_price
        metrics_rows.append({
            "component": "l10_generated_bucket_seq",
            "split": split,
            "n": int(len(frame)),
            "MdAPE": float(np.median(ape)),
            "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95)),
            "RMSE_log": float(np.sqrt(np.mean((pred - frame["ln_price_krw"].to_numpy(dtype=float)) ** 2))),
        })
    pd.DataFrame(metrics_rows).to_csv(DATA_DIR / "warm_l10_generated_component_metrics.csv", index=False)

    return {
        "component": "l10_generated_bucket_seq",
        "base_features": features,
        "enriched_features": enriched_features,
        "numeric_features": sorted(enriched_numeric),
        "quantile_models": q_models,
        "huber_centerline": str(huber_path.relative_to(REPO)),
        "residual_catboost": residual_path,
        "metrics": metrics_rows,
    }


def distill_features(frame: pd.DataFrame, features: list[str], numeric: set[str]) -> pd.DataFrame:
    out = frame[features].copy()
    for col in features:
        if col in numeric:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = out[col].astype(str).fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def build_v2_defensive_component() -> dict[str, Any]:
    """Train a deployable model for PP-V2 huber_component_range_clipped."""
    base_features = artifact_features()["warm"]
    features = unique([
        *base_features,
        *GENERATED,
        "artist_works_log",
        "artist_works_count_train",
        *svc1.SVC_NUMERIC,
        *svc1.SVC_CATEGORICAL,
        "svc_group_n",
    ])
    requested = unique([feature for feature in features if feature not in svc1.SVC_NUMERIC + svc1.SVC_CATEGORICAL + ["svc_group_n"]])
    train_base, val_base, test_base = load_scope("warm", requested)
    _train_s, val_s, test_s = svc2.add_service_features_seed(train_base, val_base, test_base, svc2.SEEDS[0])

    target_path = EXPERIMENT_ROOT / "PP-V2_warm_ppu_feature_augmented_meta_stacking" / "outputs" / "predictions.csv"
    target = pd.read_csv(target_path, low_memory=False)
    target = target[
        target["scope"].astype(str).eq("warm")
        & target["candidate"].astype(str).eq("huber_component_range_clipped")
        & target["split"].astype(str).isin(["validation", "test"])
    ][["split", "_track6_row_id", "pred_log"]].rename(columns={"pred_log": "target_pred_log"})
    val_train = val_s.merge(target[target["split"].eq("validation")], on="_track6_row_id", how="inner")
    test_eval = test_s.merge(target[target["split"].eq("test")], on="_track6_row_id", how="inner")
    train_all = pd.concat([val_train, test_eval], ignore_index=True)
    available = [col for col in features if col in val_train.columns and col in test_eval.columns]
    numeric = {col for col in available if col in DISTILL_NUMERIC}

    params = {
        "loss_function": "RMSE",
        "iterations": 500,
        "learning_rate": 0.035,
        "depth": 6,
        "l2_leaf_reg": 8.0,
        "random_seed": SEED,
        "verbose": False,
        "allow_writing_files": False,
    }
    fidelity_model = CatBoostRegressor(**params)
    fidelity_model.fit(
        distill_features(val_train, available, numeric),
        val_train["target_pred_log"].to_numpy(dtype=float),
        cat_features=[idx for idx, col in enumerate(available) if col not in numeric],
    )
    test_pred = np.asarray(fidelity_model.predict(distill_features(test_eval, available, numeric)), dtype=float)
    fidelity = metric_fidelity(test_eval["target_pred_log"].to_numpy(dtype=float), test_pred)

    final_model = CatBoostRegressor(**params)
    final_model.fit(
        distill_features(train_all, available, numeric),
        train_all["target_pred_log"].to_numpy(dtype=float),
        cat_features=[idx for idx, col in enumerate(available) if col not in numeric],
    )
    path = save_catboost(final_model, "warm_pp_v2_defensive_component.cbm")
    return {
        "component": "pp_v2_defensive_component",
        "artifact": path,
        "target_source": str(target_path.relative_to(REPO)),
        "features": available,
        "numeric_features": sorted(numeric),
        "train_rows_final": int(len(train_all)),
        "fidelity_test_from_validation_only": fidelity,
        "method": "CatBoost model trained to reproduce frozen PP-V2 huber_component_range_clipped predictions",
    }


def write_policy_manifest(svc_info: dict[str, Any], l10_info: dict[str, Any], v2_info: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "version": "v0.1-operational",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "price_unit": "KRW",
        "target": "ln_price_krw",
        "routing": {
            "warm": "artist_key가 v0.1 학습 registry에 존재",
            "cold": "v0.1 operational package에서는 reference/low confidence로만 표시",
        },
        "warm_formula": {
            "service_primary": "pp_v8_compact_blend_mape_guarded",
            "report_70_30_candidate": "0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded",
            "pp_v8": "0.75 * pp_v2_defensive_component + 0.25 * l10_generated_bucket_seq",
        },
        "service_primary": {
            "warm_candidate": "pp_v8_compact_blend_mape_guarded",
            "prediction_column": "service_primary_pred_price_krw",
            "reason": "0604 신규 Warm 라벨에서 70:30 결합보다 MdAPE, MAPE, p95_APE가 낮아 운영 기본값으로 사용",
        },
        "components": {
            "svc_numeric_seed_mean": svc_info,
            "l10_generated_bucket_seq": l10_info,
            "pp_v2_defensive_component": v2_info,
        },
        "status": {
            "warm": "active_service_artifact",
            "cold": "reference_only_pending_full_qwidth_artifact",
        },
        "notes": [
            "Warm final prediction is fully runnable from saved operational artifacts.",
            "The report-stage 70:30 candidate is retained as a comparison column, but service_primary uses PP-V8 because the latest labeled 0604 operation test favored it.",
            "PP-V2 is operationalized as a dedicated model trained to reproduce frozen PP-V2 defensive predictions because lower-level PP-V2 experiment components were not saved as service artifacts.",
            "Cold qwidth reference remains an evidence-backed policy but is not promoted to automatic service artifact in this build.",
        ],
    }
    path = ARTIFACT_DIR / "operational_policy_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_readme(manifest: dict[str, Any]) -> None:
    v2_fidelity = manifest["components"]["pp_v2_defensive_component"]["fidelity_test_from_validation_only"]
    l10_test = [
        row for row in manifest["components"]["l10_generated_bucket_seq"]["metrics"]
        if row["split"] == "test"
    ][0]
    text = f"""# price_prediction v0.1 운영용 artifact

## 상태

- 생성일: {manifest['created_at']}
- Warm: 운영 추론 가능
- Cold: reference/low confidence, 별도 qwidth artifact화 필요

## Warm 운영 예측식

```text
service_primary_log = pp_v8_compact_blend_mape_guarded

pp_v8_compact_blend_mape_guarded
          = 0.75 * pp_v2_defensive_component
          + 0.25 * l10_generated_bucket_seq

report_70_30_log = 0.70 * svc_numeric_seed_mean
                 + 0.30 * pp_v8_compact_blend_mape_guarded
```

## 저장 artifact

- `artifacts/warm_svc_numeric_seed_huber_ensemble.joblib`
- `artifacts/warm_pp_v2_defensive_component.cbm`
- `artifacts/warm_l10_generated_q10.cbm`
- `artifacts/warm_l10_generated_q50.cbm`
- `artifacts/warm_l10_generated_q90.cbm`
- `artifacts/warm_l10_generated_huber_centerline.joblib`
- `artifacts/warm_l10_generated_residual_catboost.cbm`
- `artifacts/operational_policy_manifest.json`

## 검증 메모

- L10 생성 bucket 순차 component test MdAPE: `{l10_test['MdAPE']:.4f}`
- PP-V2 방어 component distillation fidelity RMSE_log: `{v2_fidelity['RMSE_log']:.4f}`
- PP-V2 방어 component distillation fidelity MdAE_log: `{v2_fidelity['MdAE_log']:.4f}`

## 실행

피처 추출:

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \\
  --input data/test_new_artworks_test_noprice_0604.csv \\
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features
```

운영 예측:

```bash
python3 models/track6/price_prediction_v0.1/operational/scripts/predict_operational_v0_1.py \\
  --feature-dir models/track6/price_prediction_v0.1/operational/outputs/0604_features \\
  --output-dir models/track6/price_prediction_v0.1/operational/outputs/0604_predictions
```
"""
    (OP_ROOT / "README.md").write_text(text, encoding="utf-8")
    (REPORT_DIR / "operational_artifact_summary.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    svc_info = build_svc_seed_models()
    l10_info = build_l10_generated_component()
    v2_info = build_v2_defensive_component()
    manifest = write_policy_manifest(svc_info, l10_info, v2_info)
    write_readme(manifest)
    print(json.dumps({
        "status": "completed",
        "operational_root": str(OP_ROOT.relative_to(REPO)),
        "manifest": str((ARTIFACT_DIR / "operational_policy_manifest.json").relative_to(REPO)),
        "readme": str((OP_ROOT / "README.md").relative_to(REPO)),
        "warm_status": manifest["status"]["warm"],
        "cold_status": manifest["status"]["cold"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
