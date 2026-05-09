"""Operational Adoption — Per-source artifact retrain (PR1).

prereg = docs/operational_adoption_prereg_20260509.md
Decision binding ✅ YES (artifact 변경).

P1 fix 적용 (코덱스 round 1-3):
1. Filtered 28,376 retrain (raw 29,361 X / 운영 anchor)
2. No-op calibration (per-source / loader schema 정합)
3. Source-별 warm_artists (작품수 ≥ 5 / source-별 분리)
4. Per-artifact provenance (`<artifact>.provenance.json` / helper 규약)
5. Bundle: catboost / xgboost / label_maps / warm_artists / source_calibration / metrics

Output prefix: source_conditional_v1_{artsy,saatchi}_*
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _label_encode_xgb,
    _mdape,
    _warm_mask,
    load_data,
    prepare_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = REPO / "model_test_results"
PREFIX = "source_conditional_v1"
WARM_MIN_COUNT = 5


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None, cat_features: list[str]) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in cat_features if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    import subprocess
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO))
        return out.decode().strip()
    except Exception:
        return "unknown"


def write_provenance(artifact_path: Path, model_target: str, data_paths: dict) -> Path:
    """Per-artifact provenance (helper 규약 / `<artifact>.provenance.json`)."""
    manifest = artifact_path.with_suffix(artifact_path.suffix + ".provenance.json")
    payload = {
        "model_target": model_target,
        "artifact_path": str(artifact_path.relative_to(REPO)),
        "data_paths": {k: str(v) for k, v in data_paths.items()},
        "git_commit": _git_commit(),
        "artifact_hashes": {
            "main": {
                "path": str(artifact_path.relative_to(REPO)),
                "sha256": _sha256(artifact_path),
                "exists": True,
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return manifest


def retrain_source(
    df_filtered: pd.DataFrame, source_name: str, cb_best: dict, xgb_best: dict,
    data_paths: dict,
) -> dict:
    """Per-source artifact bundle 산출."""
    t0 = time.time()
    logger.info(f"\n=== Retrain: {source_name} ===")

    df_src = df_filtered[df_filtered["source"] == source_name].reset_index(drop=True)
    logger.info(f"  Data: {len(df_src)} rows")

    X, y, groups = prepare_features(df_src)
    cat_features_iter = [c for c in CAT_FEATURES if c in X.columns]

    model_target = f"{PREFIX}_{source_name}"

    # ─── CatBoost ─────────────────────────────────────────────────────
    logger.info(f"  CatBoost retrain")
    cb = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=0, random_seed=42,
        allow_writing_files=False,
    )
    cb.fit(_cb_pool(X, y, cat_features_iter))
    cb_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_catboost.cbm"
    cb.save_model(str(cb_path))
    logger.info(f"    saved {cb_path.name}")

    # ─── XGBoost ──────────────────────────────────────────────────────
    logger.info(f"  XGBoost retrain")
    Xe, _, label_maps = _label_encode_xgb(X, X.iloc[:1])
    dtrain = xgb.DMatrix(Xe, label=y)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    booster = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 0, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )
    xgb_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_xgboost.json"
    booster.save_model(str(xgb_path))
    logger.info(f"    saved {xgb_path.name}")

    # ─── Label maps ───────────────────────────────────────────────────
    label_maps_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_xgboost_label_maps.json"
    label_maps_path.write_text(json.dumps(label_maps, indent=2, ensure_ascii=False))
    logger.info(f"    saved {label_maps_path.name}")

    # ─── Warm artists (source-별 / P1 fix) ────────────────────────────
    warm_mask = _warm_mask(groups)
    warm_artist_slugs = sorted(set(groups[warm_mask].tolist()))
    warm_payload = {
        "warm_artist_slugs": warm_artist_slugs,
        "n_artists": len(warm_artist_slugs),
        "n_warm_works": int(warm_mask.sum()),
        "min_count": WARM_MIN_COUNT,
        "source": source_name,
        "note": f"source-conditional v1 / {source_name} only / 작품수 >= {WARM_MIN_COUNT}",
    }
    warm_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_warm_artists.json"
    warm_path.write_text(json.dumps(warm_payload, indent=2, ensure_ascii=False))
    logger.info(f"    saved {warm_path.name} (n={len(warm_artist_slugs)} warm artists)")

    # ─── No-op calibration (loader schema 정합 / P1 fix) ──────────────
    if source_name == "artsy":
        cells = ["artsy_gallery", "artsy_online"]
    else:
        cells = ["saatchi_online"]
    calib_payload = {
        "version": "v1-source-conditional-noop",
        "model_target": model_target,
        "method": "no-op identity (Phase 2 cycle 별도 prereg 재산출)",
        "cold_factors": {c: 1.0 for c in cells},
        "warm_factors": {c: 1.0 for c in cells},
    }
    calib_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_source_calibration.json"
    calib_path.write_text(json.dumps(calib_payload, indent=2, ensure_ascii=False))
    logger.info(f"    saved {calib_path.name} (no-op / cells={cells})")

    # ─── Metrics (sanity) ─────────────────────────────────────────────
    # In-sample metric (sanity / not for model selection)
    cb_pred = cb.predict(_cb_pool(X, None, cat_features_iter))
    xgb_pred = booster.predict(xgb.DMatrix(Xe))
    ens_pred = (cb_pred + xgb_pred) / 2.0
    y_price = np.exp(y)
    metrics = {
        "model_target": model_target,
        "data": f"{len(df_src)} rows / {source_name} only / filtered (is_excluded_for_training==0)",
        "n_rows": int(len(df_src)),
        "n_artists": int(pd.Series(groups).nunique()),
        "n_warm_artists": len(warm_artist_slugs),
        "in_sample_mdape_catboost": float(_mdape(y_price, np.exp(cb_pred))),
        "in_sample_mdape_xgboost": float(_mdape(y_price, np.exp(xgb_pred))),
        "in_sample_mdape_ensemble": float(_mdape(y_price, np.exp(ens_pred))),
        "best_params": {"catboost": cb_best, "xgboost": xgb_best},
        "note": "In-sample metrics for sanity only / SourceCond CHAMPION 평가 = Holdout (별도 cycle)",
    }
    metrics_path = ARTIFACTS_DIR / f"{PREFIX}_{source_name}_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    logger.info(f"    saved {metrics_path.name}")

    # ─── Per-artifact provenance (P1 fix / helper 규약) ───────────────
    cb_prov = write_provenance(cb_path, model_target, data_paths)
    xgb_prov = write_provenance(xgb_path, model_target, data_paths)
    calib_prov = write_provenance(calib_path, model_target, data_paths)
    logger.info(f"    saved 3 provenance.json")

    elapsed = round(time.time() - t0, 1)
    logger.info(f"  {source_name} bundle done ({elapsed}s)")

    return {
        "source": source_name,
        "model_target": model_target,
        "n_rows": int(len(df_src)),
        "n_artists": int(pd.Series(groups).nunique()),
        "n_warm_artists": len(warm_artist_slugs),
        "n_warm_works": int(warm_mask.sum()),
        "in_sample_mdape_ensemble": float(_mdape(y_price, np.exp(ens_pred))),
        "artifacts": {
            "catboost": str(cb_path.relative_to(REPO)),
            "xgboost": str(xgb_path.relative_to(REPO)),
            "label_maps": str(label_maps_path.relative_to(REPO)),
            "warm_artists": str(warm_path.relative_to(REPO)),
            "source_calibration": str(calib_path.relative_to(REPO)),
            "metrics": str(metrics_path.relative_to(REPO)),
            "provenance_catboost": str(cb_prov.relative_to(REPO)),
            "provenance_xgboost": str(xgb_prov.relative_to(REPO)),
            "provenance_calibration": str(calib_prov.relative_to(REPO)),
        },
        "elapsed_sec": elapsed,
    }


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Operational Adoption — Per-source Artifact Retrain (PR1)")
    logger.info("=" * 70)

    best_params = json.loads(
        (ARTIFACTS_DIR / "integrated_v3_filtered_tuned_best_params.json").read_text()
    )
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]
    logger.info(f"CB best_params: {cb_best}")
    logger.info(f"XGB best_params: {xgb_best}")

    df = load_data()
    df_filtered = df[df["is_excluded_for_training"] == 0].reset_index(drop=True).copy()
    logger.info(f"\nFiltered (is_excluded_for_training==0): {len(df_filtered)} rows")
    logger.info(f"  Artsy: {(df_filtered['source'] == 'artsy').sum()}")
    logger.info(f"  Saatchi: {(df_filtered['source'] == 'saatchi').sum()}")

    data_paths = {
        "artsy": "data/primary_market_dataset.parquet",
        "saatchi": "data/saatchi_cleaned.parquet",
    }

    results = []
    for source_name in ["artsy", "saatchi"]:
        result = retrain_source(df_filtered, source_name, cb_best, xgb_best, data_paths)
        results.append(result)

    summary = {
        "prereg": "docs/operational_adoption_prereg_20260509.md",
        "decision_binding": True,
        "prefix": PREFIX,
        "filtered_n": int(len(df_filtered)),
        "raw_n": int(len(df)),
        "results": results,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    summary_path = Path(__file__).parent / "artifact_retrain_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    logger.info(f"\n[OK] {summary_path.name} (total {summary['elapsed_sec']}s)")

    print("\n" + "=" * 80)
    print("Operational Adoption PR1 — Artifact Retrain Summary")
    print("=" * 80)
    for r in results:
        print(f"\n{r['source']} bundle ({r['model_target']}):")
        print(f"  n_rows: {r['n_rows']} / n_artists: {r['n_artists']} / n_warm: {r['n_warm_artists']}")
        print(f"  In-sample Ensemble MdAPE: {r['in_sample_mdape_ensemble']:.3f}")
        print(f"  Artifacts:")
        for k, v in r['artifacts'].items():
            print(f"    {k}: {v}")
    print(f"\n[total elapsed: {summary['elapsed_sec']}s]")


if __name__ == "__main__":
    main()
