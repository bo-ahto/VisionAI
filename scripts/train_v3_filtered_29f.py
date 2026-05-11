"""PR-29F: 29-feature artifact bundle 학습 — default + B winner 동시 산출.

Pre-context:
- Layer 1 audit: ho_price_level / medium_price_level (dead 2) PASS_WITHIN_NOISE
- Layer 1+ audit: + source 제거 PASS_WITHIN_NOISE (Δ cold +0.67pp / Δ warm +0.07pp)
- User 결정: 서비스 운영에서 source 입력 불가 → train/serve mismatch 해소
- Codex R2 검수: 신규 variant + 자체 artifact 재발행 → legacy 32f variant는 전환 전까지 유지

Artifact 산출 (각 prefix별 5 file):
- integrated_v3_filtered_tuned_29f_*               (default unified 29f)
- integrated_v3_filtered_tuned_b_warm_29f_*       (B winner 29f / CB copy + XGB retrain)

설계 (PR-WARM-B Stage 1 / retrain_v3_filtered_b_warm.py 정합):
- default 29f: CB + XGB 신규 학습 (full data / 기존 best_params 재사용)
- b_warm 29f: CB copy from default 29f (cold path bit-identical) + XGB warm-only 재학습
  (warm_only_retuned_best_params.json 재사용 — params는 32f B winner와 동일)

Usage:
    PYTHONPATH=src python3 scripts/train_v3_filtered_29f.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor, Pool

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # type: ignore
    _warm_mask,
    load_data,
    prepare_features,
)

from visionai.price_engine.api.primary_predictor import (
    CAT_FEATURES_29,
    CB_FEATURES_BASE_29,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "model_test_results"
DEFAULT_BEST_PARAMS_PATH = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
B_WARM_PARAMS_PATH = OUT_DIR / "warm_only_retuned_best_params.json"

DEFAULT_29F_PREFIX = "integrated_v3_filtered_tuned_29f"
B_WARM_29F_PREFIX = "integrated_v3_filtered_tuned_b_warm_29f"
WARM_MIN_COUNT = 5  # tune_primary_market_v3_filtered.WARM_MIN_COUNT 정합


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def _cb_pool_29(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES_29 if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb_29(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    X_train_e = X_train.copy()
    X_test_e = X_test.copy()
    label_maps: dict[str, dict[str, int]] = {}
    for col in CAT_FEATURES_29:
        if col not in X_train_e.columns:
            continue
        train_vals = X_train_e[col].unique()
        mapping = {v: i for i, v in enumerate(sorted(train_vals))}
        unseen_idx = len(mapping)
        label_maps[col] = mapping
        X_train_e[col] = X_train_e[col].map(mapping).astype(float)
        X_test_e[col] = X_test_e[col].map(mapping).fillna(unseen_idx).astype(float)
    return X_train_e, X_test_e, label_maps


def _save_default_29f_artifacts(
    cb_final: CatBoostRegressor,
    xgb_final: xgb.Booster,
    label_maps: dict,
    warm_artists: list,
    n_warm: int,
    best_params: dict,
    metrics_summary: dict,
    data_info: dict,
) -> None:
    """Default 29f artifact bundle 5 file 저장."""
    cb_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_catboost.cbm"
    xgb_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_xgboost.json"
    label_maps_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_xgboost_label_maps.json"
    warm_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_warm_artists.json"
    metrics_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_metrics.json"
    best_params_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_best_params.json"
    calib_path = OUT_DIR / f"{DEFAULT_29F_PREFIX}_source_calibration.json"

    cb_final.save_model(str(cb_path))
    xgb_final.save_model(str(xgb_path))
    label_maps_path.write_text(json.dumps(label_maps, ensure_ascii=False, indent=2))
    warm_path.write_text(
        json.dumps(
            {
                "warm_artist_slugs": warm_artists,
                "n_artists": len(warm_artists),
                "n_warm_works": n_warm,
                "min_count": WARM_MIN_COUNT,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    metrics_path.write_text(
        json.dumps(
            {
                "model": DEFAULT_29F_PREFIX,
                "data": data_info,
                "features": len(CB_FEATURES_BASE_29),
                "feature_list": CB_FEATURES_BASE_29,
                "cat_features": CAT_FEATURES_29,
                "best_params": best_params,
                "metrics_summary": metrics_summary,
                "note": "PR-29F: dead 2 + source 제거 (32→29). best_params 재사용.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    best_params_path.write_text(json.dumps(best_params, ensure_ascii=False, indent=2))
    # source_calibration.json — neutral cells (factor=1.0) — calibration 재산출은 별도 step
    calib_path.write_text(
        json.dumps(
            {
                "model_target": "v3_filtered_tuned_29f",
                "version": "29f_v0_no_op",
                "cold_factors": {},
                "warm_factors": {},
                "note": "PR-29F initial: factor=1.0 default. source feature 제거되어 cell-based calibration 자체가 의미 변경됨 — 후속 재설계 필요.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    logger.info("Default 29f artifacts saved:")
    for p in [
        cb_path,
        xgb_path,
        label_maps_path,
        warm_path,
        metrics_path,
        best_params_path,
        calib_path,
    ]:
        logger.info(f"  {p.name}")


def train_default_29f(df: pd.DataFrame) -> dict:
    """Default 29f training. Returns dict with cb/xgb models + metadata."""
    logger.info("=" * 70)
    logger.info("Default 29f training")
    logger.info("=" * 70)

    with DEFAULT_BEST_PARAMS_PATH.open() as f:
        best_params = json.load(f)
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]
    logger.info("CB best params: %s", cb_best)
    logger.info("XGB best params: %s", xgb_best)

    df_train = df[df["is_excluded_for_training"] == 0].copy()
    X_full, y, groups = prepare_features(df_train)
    X = X_full[CB_FEATURES_BASE_29].copy()
    logger.info(
        "Data: %d rows, %d artists, %d features", len(df_train), len(set(groups)), len(X.columns)
    )
    assert len(X.columns) == 29

    warm_mask_arr = _warm_mask(groups)
    X_warm = X.iloc[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]
    g_warm = groups[warm_mask_arr]
    n_warm = int(warm_mask_arr.sum())
    n_warm_artists = int(pd.Series(g_warm).nunique())
    logger.info("Warm slice: %d works, %d artists", n_warm, n_warm_artists)

    # CatBoost final fit on full data
    logger.info("CatBoost final fit (full data)...")
    t0 = time.time()
    cb_final = CatBoostRegressor(
        **cb_best,
        loss_function="RMSE",
        verbose=100,
        random_seed=42,
        allow_writing_files=False,
    )
    cb_final.fit(_cb_pool_29(X, y))
    logger.info(f"CatBoost done ({time.time()-t0:.1f}s)")

    # XGBoost final fit on warm slice
    logger.info("XGBoost final fit (warm slice)...")
    t0 = time.time()
    Xe_warm, _, label_maps = _label_encode_xgb_29(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    xgb_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain,
        num_boost_round=xgb_best.get("num_boost_round", 1000),
    )
    logger.info(f"XGBoost done ({time.time()-t0:.1f}s)")

    warm_artists = sorted(set(g_warm.tolist()))
    n_excluded = int((df["is_excluded_for_training"] == 1).sum())
    data_info = (
        f"{len(df_train)} = filtered (excluded {n_excluded}), 29f variant (dead 2 + source 제거)"
    )

    return {
        "cb_final": cb_final,
        "xgb_final": xgb_final,
        "label_maps": label_maps,
        "warm_artists": warm_artists,
        "n_warm": n_warm,
        "best_params": best_params,
        "data_info": data_info,
        "X": X,
        "y": y,
        "groups": groups,
    }


def _save_b_warm_29f_artifacts(
    cb_src_path: Path,
    xgb_b_warm_final: xgb.Booster,
    label_maps_src_path: Path,
    warm_src_path: Path,
    calib_src_path: Path,
    xgb_best: dict,
    cb_best: dict,
    metrics_summary: dict,
    data_info: dict,
) -> None:
    """B winner 29f artifact bundle 8 file 저장."""
    cb_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_catboost.cbm"
    xgb_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_xgboost.json"
    label_maps_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_xgboost_label_maps.json"
    warm_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_warm_artists.json"
    calib_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_source_calibration.json"
    metrics_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_metrics.json"
    best_params_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_best_params.json"
    manifest_dst = OUT_DIR / f"{B_WARM_29F_PREFIX}_manifest.json"

    # 1) CatBoost: COPY (bit-identical cold path to default-29f)
    shutil.copy2(cb_src_path, cb_dst)
    # 2) XGBoost: NEW (B-retuned params on 29f warm)
    xgb_b_warm_final.save_model(str(xgb_dst))
    # 3) Label maps / warm artists: COPY
    shutil.copy2(label_maps_src_path, label_maps_dst)
    shutil.copy2(warm_src_path, warm_dst)
    # 4) Calibration: COPY + model_target rename
    calib_data = json.loads(calib_src_path.read_text())
    calib_data["model_target"] = "v3_filtered_tuned_b_warm_29f"
    calib_dst.write_text(json.dumps(calib_data, ensure_ascii=False, indent=2))

    # 5) metrics + best_params + manifest
    metrics_dst.write_text(
        json.dumps(
            {
                "model": B_WARM_29F_PREFIX,
                "data": data_info,
                "features": len(CB_FEATURES_BASE_29),
                "feature_list": CB_FEATURES_BASE_29,
                "cat_features": CAT_FEATURES_29,
                "best_params": {"catboost": cb_best, "xgboost": xgb_best},
                "metrics_summary": metrics_summary,
                "note": "PR-29F: B winner 29f. CB copy from default-29f / XGB B-retuned warm fit on 29f.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    best_params_dst.write_text(
        json.dumps(
            {
                "catboost": cb_best,
                "xgboost": xgb_best,
                "provenance": {
                    "catboost": "default-29f (bit-identical copy from integrated_v3_filtered_tuned_29f)",
                    "xgboost": "B winner warm-only retuned params (warm_only_retuned_best_params.json) on 29f warm slice",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    manifest_dst.write_text(
        json.dumps(
            {
                "model": B_WARM_29F_PREFIX,
                "created_at": datetime.now(UTC).isoformat(),
                "git_commit": _git_commit(),
                "artifact_sha256": {
                    "catboost.cbm": _sha256_file(cb_dst),
                    "xgboost.json": _sha256_file(xgb_dst),
                    "xgboost_label_maps.json": _sha256_file(label_maps_dst),
                    "warm_artists.json": _sha256_file(warm_dst),
                    "source_calibration.json": _sha256_file(calib_dst),
                },
                "cb_provenance": "bit-identical copy from default-29f",
                "xgb_provenance": "B-retuned params (32f B winner) on 29f warm slice",
                "features_count": len(CB_FEATURES_BASE_29),
                "cat_features_count": len(CAT_FEATURES_29),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    logger.info("B winner 29f artifacts saved:")
    for p in [
        cb_dst,
        xgb_dst,
        label_maps_dst,
        warm_dst,
        calib_dst,
        metrics_dst,
        best_params_dst,
        manifest_dst,
    ]:
        logger.info(f"  {p.name}")


def train_b_warm_29f(default_29f_result: dict) -> None:
    """B winner 29f: CB copy from default-29f + XGB B-retuned on 29f warm."""
    logger.info("=" * 70)
    logger.info("B winner 29f training (CB copy + XGB retrain)")
    logger.info("=" * 70)

    # B winner XGB params (warm-only retuned)
    if not B_WARM_PARAMS_PATH.exists():
        raise FileNotFoundError(
            f"B winner XGB params missing: {B_WARM_PARAMS_PATH} — run cycle B first"
        )
    with B_WARM_PARAMS_PATH.open() as f:
        b_warm_data = json.load(f)
    xgb_b_best = b_warm_data["xgb_retuned_warm"]
    cb_default = default_29f_result["best_params"]["catboost"]
    logger.info("XGB B-warm params: %s", xgb_b_best)

    X = default_29f_result["X"]
    y = default_29f_result["y"]
    groups = default_29f_result["groups"]
    warm_mask_arr = _warm_mask(groups)
    X_warm = X.iloc[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]

    # XGBoost warm fit with B-retuned params
    logger.info("XGBoost warm fit (B-retuned)...")
    t0 = time.time()
    Xe_warm, _, _ = _label_encode_xgb_29(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_b_best.items() if k != "num_boost_round"}
    xgb_b_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain,
        num_boost_round=xgb_b_best.get("num_boost_round", 1000),
    )
    logger.info(f"XGBoost done ({time.time()-t0:.1f}s)")

    # Save artifacts: cb COPY from default-29f, xgb NEW
    cb_src = OUT_DIR / f"{DEFAULT_29F_PREFIX}_catboost.cbm"
    label_maps_src = OUT_DIR / f"{DEFAULT_29F_PREFIX}_xgboost_label_maps.json"
    warm_src = OUT_DIR / f"{DEFAULT_29F_PREFIX}_warm_artists.json"
    calib_src = OUT_DIR / f"{DEFAULT_29F_PREFIX}_source_calibration.json"

    _save_b_warm_29f_artifacts(
        cb_src_path=cb_src,
        xgb_b_warm_final=xgb_b_final,
        label_maps_src_path=label_maps_src,
        warm_src_path=warm_src,
        calib_src_path=calib_src,
        xgb_best=xgb_b_best,
        cb_best=cb_default,
        metrics_summary={
            "source": "Layer 1+ isolated cycle (separate run) — Δ_cold +0.67pp / Δ_warm +0.07pp within noise"
        },
        data_info=default_29f_result["data_info"],
    )


def main() -> None:
    t0_total = time.time()

    df = load_data()
    logger.info("Data loaded: %d rows", len(df))

    # Stage 1: Default 29f
    result = train_default_29f(df)
    _save_default_29f_artifacts(
        cb_final=result["cb_final"],
        xgb_final=result["xgb_final"],
        label_maps=result["label_maps"],
        warm_artists=result["warm_artists"],
        n_warm=result["n_warm"],
        best_params=result["best_params"],
        metrics_summary={
            "source": "Layer 1+ isolated cycle — Δ_cold +0.67pp / Δ_warm +0.02pp within noise"
        },
        data_info=result["data_info"],
    )

    # Stage 2: B winner 29f (CB copy + XGB retune)
    train_b_warm_29f(result)

    logger.info("=" * 70)
    logger.info(f"PR-29F training complete (total {time.time()-t0_total:.1f}s)")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
