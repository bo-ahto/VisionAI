"""PR-FOLLOWERS-FALLBACK: 29-feature (28 + has_followers) artifact bundle 학습.

Pre-context:
- PR-28F (직전 commit): for_sale_ratio 제거 (29→28) — Layer 2.B PASS
- User 결정: 신규 작가 운영 시 followers 수집 거의 불가 → "0 = real zero" vs "0 = unknown" collapse
- Step A isolated cycle (28 → 29_hf, ADD has_followers): PASS_NEUTRAL
  - Δ_cold +0.58pp / Δ_warm xgb -0.07pp / Δ_warm ens -0.05pp vs 28f
  - 91.5% has_followers=1 / 8.5% has_followers=0 (training distribution)
- Codex R2 GO: "safe to deploy for fidelity reasons" — atomic PR

Inline 생성: has_followers = (ln_followers > 0).astype(int) (학습 데이터 재생성 불필요)
신규 features: 28 + 1 = 29 (cat_features 변동 없음)

Artifact 산출 (각 prefix별 8 file):
- integrated_v3_filtered_tuned_29f_hf_*           (default unified)
- integrated_v3_filtered_tuned_b_warm_29f_hf_*    (B winner / CB copy + XGB retrain)

Usage:
    PYTHONPATH=src python3 scripts/train_v3_filtered_29f_hf.py
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
    CB_FEATURES_BASE_28,
    CB_FEATURES_BASE_29_HF,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "model_test_results"
DEFAULT_BEST_PARAMS_PATH = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
B_WARM_PARAMS_PATH = OUT_DIR / "warm_only_retuned_best_params.json"

DEFAULT_29F_HF_PREFIX = "integrated_v3_filtered_tuned_29f_hf"
B_WARM_29F_HF_PREFIX = "integrated_v3_filtered_tuned_b_warm_29f_hf"
WARM_MIN_COUNT = 5


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def _cb_pool(X: pd.DataFrame, y: np.ndarray | None = None) -> Pool:
    cat_idx = [X.columns.get_loc(c) for c in CAT_FEATURES_29 if c in X.columns]
    return Pool(X, label=y, cat_features=cat_idx)


def _label_encode_xgb(
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


def _prepare_29f_hf_features(
    df_train: pd.DataFrame,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """28f + has_followers (inline)."""
    X_full, y, groups = prepare_features(df_train)
    X = X_full[CB_FEATURES_BASE_28].copy()
    X["has_followers"] = (X["ln_followers"] > 0).astype(int)
    X = X[CB_FEATURES_BASE_29_HF]
    assert len(X.columns) == 29
    assert "has_followers" in X.columns
    return X, y, groups


def _save_default_artifacts(
    cb_final: CatBoostRegressor,
    xgb_final: xgb.Booster,
    label_maps: dict,
    warm_artists: list,
    n_warm: int,
    best_params: dict,
    data_info: dict,
) -> None:
    cb_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_catboost.cbm"
    xgb_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_xgboost.json"
    label_maps_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_xgboost_label_maps.json"
    warm_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_warm_artists.json"
    metrics_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_metrics.json"
    best_params_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_best_params.json"
    calib_path = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_source_calibration.json"

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
                "model": DEFAULT_29F_HF_PREFIX,
                "data": data_info,
                "features": len(CB_FEATURES_BASE_29_HF),
                "feature_list": CB_FEATURES_BASE_29_HF,
                "cat_features": CAT_FEATURES_29,
                "best_params": best_params,
                "note": "PR-FOLLOWERS-FALLBACK: 28 + has_followers (Step A PASS_NEUTRAL). best_params 재사용.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    best_params_path.write_text(json.dumps(best_params, ensure_ascii=False, indent=2))
    calib_path.write_text(
        json.dumps(
            {
                "model_target": "v3_filtered_tuned_29f_hf",
                "version": "29f_hf_v0_no_op",
                "cold_factors": {},
                "warm_factors": {},
                "note": "PR-FOLLOWERS-FALLBACK initial: factor=1.0 default. source 제거된 상태 계승.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    logger.info("Default 29f_hf artifacts saved (7 file):")
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


def train_default_29f_hf(df: pd.DataFrame) -> dict:
    logger.info("=" * 70)
    logger.info("Default 29f_hf training")
    logger.info("=" * 70)

    with DEFAULT_BEST_PARAMS_PATH.open() as f:
        best_params = json.load(f)
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]

    df_train = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = _prepare_29f_hf_features(df_train)
    n_has_followers = int(X["has_followers"].sum())
    logger.info(
        "Data: %d rows, %d artists, %d features (has_followers=1: %d/%d = %.1f%%)",
        len(df_train),
        len(set(groups)),
        len(X.columns),
        n_has_followers,
        len(X),
        100 * n_has_followers / len(X),
    )

    warm_mask_arr = _warm_mask(groups)
    X_warm = X.iloc[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]
    g_warm = groups[warm_mask_arr]
    n_warm = int(warm_mask_arr.sum())
    logger.info("Warm slice: %d works, %d artists", n_warm, len(set(g_warm.tolist())))

    logger.info("CatBoost final fit (full data)...")
    t0 = time.time()
    cb_final = CatBoostRegressor(
        **cb_best,
        loss_function="RMSE",
        verbose=100,
        random_seed=42,
        allow_writing_files=False,
    )
    cb_final.fit(_cb_pool(X, y))
    logger.info(f"CatBoost done ({time.time()-t0:.1f}s)")

    logger.info("XGBoost final fit (warm slice)...")
    t0 = time.time()
    Xe_warm, _, label_maps = _label_encode_xgb(X_warm, X_warm.iloc[:1])
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
    data_info = f"{len(df_train)} = filtered (excluded {n_excluded}), 29f_hf (28 + has_followers)"

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


def _save_b_warm_artifacts(
    cb_src: Path,
    xgb_b_final: xgb.Booster,
    label_maps_src: Path,
    warm_src: Path,
    calib_src: Path,
    xgb_best: dict,
    cb_best: dict,
    data_info: dict,
) -> None:
    cb_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_catboost.cbm"
    xgb_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_xgboost.json"
    label_maps_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_xgboost_label_maps.json"
    warm_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_warm_artists.json"
    calib_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_source_calibration.json"
    metrics_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_metrics.json"
    best_params_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_best_params.json"
    manifest_dst = OUT_DIR / f"{B_WARM_29F_HF_PREFIX}_manifest.json"

    shutil.copy2(cb_src, cb_dst)
    xgb_b_final.save_model(str(xgb_dst))
    shutil.copy2(label_maps_src, label_maps_dst)
    shutil.copy2(warm_src, warm_dst)
    calib_data = json.loads(calib_src.read_text())
    calib_data["model_target"] = "v3_filtered_tuned_b_warm_29f_hf"
    calib_dst.write_text(json.dumps(calib_data, ensure_ascii=False, indent=2))

    metrics_dst.write_text(
        json.dumps(
            {
                "model": B_WARM_29F_HF_PREFIX,
                "data": data_info,
                "features": len(CB_FEATURES_BASE_29_HF),
                "feature_list": CB_FEATURES_BASE_29_HF,
                "cat_features": CAT_FEATURES_29,
                "best_params": {"catboost": cb_best, "xgboost": xgb_best},
                "note": "PR-FOLLOWERS-FALLBACK: B winner 29f_hf. CB copy from default-29f_hf / XGB B-retuned warm fit on 29f_hf.",
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
                    "catboost": "default-29f_hf (bit-identical copy)",
                    "xgboost": "B winner warm-only retuned params on 29f_hf warm slice",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    manifest_dst.write_text(
        json.dumps(
            {
                "model": B_WARM_29F_HF_PREFIX,
                "created_at": datetime.now(UTC).isoformat(),
                "git_commit": _git_commit(),
                "artifact_sha256": {
                    "catboost.cbm": _sha256_file(cb_dst),
                    "xgboost.json": _sha256_file(xgb_dst),
                    "xgboost_label_maps.json": _sha256_file(label_maps_dst),
                    "warm_artists.json": _sha256_file(warm_dst),
                    "source_calibration.json": _sha256_file(calib_dst),
                },
                "cb_provenance": "bit-identical copy from default-29f_hf",
                "xgb_provenance": "B-retuned params on 29f_hf warm slice",
                "features_count": len(CB_FEATURES_BASE_29_HF),
                "cat_features_count": len(CAT_FEATURES_29),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    logger.info("B winner 29f_hf artifacts saved (8 file):")
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


def train_b_warm_29f_hf(default_result: dict) -> None:
    logger.info("=" * 70)
    logger.info("B winner 29f_hf training (CB copy + XGB retrain)")
    logger.info("=" * 70)

    if not B_WARM_PARAMS_PATH.exists():
        raise FileNotFoundError(f"B winner XGB params missing: {B_WARM_PARAMS_PATH}")
    with B_WARM_PARAMS_PATH.open() as f:
        b_warm_data = json.load(f)
    xgb_b_best = b_warm_data["xgb_retuned_warm"]
    cb_default = default_result["best_params"]["catboost"]

    X = default_result["X"]
    y = default_result["y"]
    groups = default_result["groups"]
    warm_mask_arr = _warm_mask(groups)
    X_warm = X.iloc[warm_mask_arr].reset_index(drop=True)
    y_warm = y[warm_mask_arr]

    logger.info("XGBoost warm fit (B-retuned)...")
    t0 = time.time()
    Xe_warm, _, _ = _label_encode_xgb(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_b_best.items() if k != "num_boost_round"}
    xgb_b_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain,
        num_boost_round=xgb_b_best.get("num_boost_round", 1000),
    )
    logger.info(f"XGBoost done ({time.time()-t0:.1f}s)")

    cb_src = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_catboost.cbm"
    label_maps_src = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_xgboost_label_maps.json"
    warm_src = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_warm_artists.json"
    calib_src = OUT_DIR / f"{DEFAULT_29F_HF_PREFIX}_source_calibration.json"

    _save_b_warm_artifacts(
        cb_src=cb_src,
        xgb_b_final=xgb_b_final,
        label_maps_src=label_maps_src,
        warm_src=warm_src,
        calib_src=calib_src,
        xgb_best=xgb_b_best,
        cb_best=cb_default,
        data_info=default_result["data_info"],
    )


def main() -> None:
    t0_total = time.time()

    df = load_data()
    logger.info("Data loaded: %d rows", len(df))

    result = train_default_29f_hf(df)
    _save_default_artifacts(
        cb_final=result["cb_final"],
        xgb_final=result["xgb_final"],
        label_maps=result["label_maps"],
        warm_artists=result["warm_artists"],
        n_warm=result["n_warm"],
        best_params=result["best_params"],
        data_info=result["data_info"],
    )

    train_b_warm_29f_hf(result)

    logger.info("=" * 70)
    logger.info(f"PR-FOLLOWERS-FALLBACK training complete (total {time.time()-t0_total:.1f}s)")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
