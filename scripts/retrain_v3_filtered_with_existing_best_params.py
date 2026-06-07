"""기존 best_params 재사용 한 v3-filtered 재학습 — Phase 3 of HO_TABLE 통합 cycle.

Pre-registered: docs/ho_table_operational_integration_prereg_20260508.md
Decision binding: ✅ YES (Phase 3 / 운영 artifact bundle 재생성)

기존 `integrated_v3_filtered_tuned_best_params.json` 재사용 / Optuna 미실행.
새 ho 영역 의 dataset (Phase 2 재생성) 으로 학습.

산출 artifact (5 file):
- integrated_v3_filtered_tuned_catboost.cbm
- integrated_v3_filtered_tuned_xgboost.json
- integrated_v3_filtered_tuned_xgboost_label_maps.json
- integrated_v3_filtered_tuned_metrics.json
- integrated_v3_filtered_tuned_warm_artists.json

(best_params.json = 재사용 / source_calibration.json = 별도 calibrate_source_bias 실행)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # type: ignore  # noqa: E402
    CB_FEATURES,
    CAT_FEATURES,
    _cb_pool,
    _label_encode_xgb,
    _mdape,
    _summary,
    _warm_mask,
    cv_groupkfold,
    cv_kfold,
    load_data,
    prepare_features,
)

# tune script 의 final logic 그대로
from tune_primary_market_v3_filtered import (  # type: ignore  # noqa: E402
    WARM_MIN_COUNT,
    _final_cv_groupkfold_5,
    _final_cv_kfold_5,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "model_test_results"
BEST_PARAMS_PATH = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"


def main() -> None:
    logger.info("=" * 70)
    logger.info("v3-filtered RETRAIN (기존 best_params 재사용 / Optuna 미실행)")
    logger.info("=" * 70)

    # 기존 best_params load
    with open(BEST_PARAMS_PATH) as f:
        best_params = json.load(f)
    cb_best = best_params["catboost"]
    xgb_best = best_params["xgboost"]
    logger.info("CatBoost best params (재사용): %s", cb_best)
    logger.info("XGBoost best params (재사용): %s", xgb_best)

    # Data load (새 ho 영역 적용된 parquet)
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    logger.info("Data: %d rows, %d artists, %d features", len(df), len(set(groups)), len(CB_FEATURES))

    warm_mask = _warm_mask(groups)
    X_warm = X.iloc[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    n_warm = int(warm_mask.sum())
    n_warm_artists = int(pd.Series(groups[warm_mask]).nunique())
    logger.info("Warm slice: %d works, %d artists", n_warm, n_warm_artists)

    # Final 5-fold CV (best params 재사용)
    logger.info("--- GroupKFold 5 (cold) ---")
    gkf_metrics = _final_cv_groupkfold_5(X, y, groups, source, cb_best, xgb_best)
    logger.info("--- KFold 5 (warm) ---")
    warm_groups = groups[warm_mask]
    warm_source = source[warm_mask]
    kf_metrics = _final_cv_kfold_5(X_warm, y_warm, cb_best, xgb_best,
                                    groups=warm_groups, source=warm_source)
    kf_metrics["_note"] = (
        f"Evaluated on warm slice only ({n_warm} works, {n_warm_artists} artists, "
        f"artist 작품수>={WARM_MIN_COUNT})"
    )

    # Final training on full data
    logger.info("--- Final training on full data ---")
    cb_final = CatBoostRegressor(
        **cb_best, loss_function="RMSE", verbose=100, random_seed=42, allow_writing_files=False,
    )
    cb_final.fit(_cb_pool(X, y))

    Xe_warm, _, label_maps = _label_encode_xgb(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    xgb_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )

    # Save artifacts
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cb_final.save_model(str(OUT_DIR / "integrated_v3_filtered_tuned_catboost.cbm"))
    xgb_final.save_model(str(OUT_DIR / "integrated_v3_filtered_tuned_xgboost.json"))
    with (OUT_DIR / "integrated_v3_filtered_tuned_xgboost_label_maps.json").open("w") as f:
        json.dump(label_maps, f, ensure_ascii=False, indent=2)

    warm_artists_set = sorted(set(groups[warm_mask].tolist()))
    with (OUT_DIR / "integrated_v3_filtered_tuned_warm_artists.json").open("w") as f:
        json.dump({
            "warm_artist_slugs": warm_artists_set,
            "n_artists": len(warm_artists_set),
            "n_warm_works": int(warm_mask.sum()),
            "min_count": int(WARM_MIN_COUNT),
        }, f, ensure_ascii=False, indent=2)

    n_excluded = int((df["is_excluded_for_training"] == 1).sum())
    metrics_doc = {
        "model": "integrated_v3_filtered_tuned",
        "data": f"{len(df)} = filtered (excluded {n_excluded}), retrained with HO standard table integration",
        "features": len(CB_FEATURES),
        "artists": len(set(groups)),
        "best_params": best_params,
        "groupkfold": gkf_metrics,
        "kfold": kf_metrics,
        "label_maps": label_maps,
        "note": "Phase 3 of HO_TABLE 통합 cycle / best_params 재사용 / Optuna 미실행",
    }
    with (OUT_DIR / "integrated_v3_filtered_tuned_metrics.json").open("w") as f:
        json.dump(metrics_doc, f, ensure_ascii=False, indent=2)

    logger.info("=" * 70)
    logger.info("Phase 3 완료 — artifact bundle 5 file 산출")
    logger.info("=" * 70)
    if "ensemble" in gkf_metrics:
        logger.info("GroupKFold ensemble cold MdAPE: %.2f%%", gkf_metrics["ensemble"]["MdAPE"])
    if "ensemble" in kf_metrics:
        logger.info("KFold warm ensemble MdAPE: %.2f%%", kf_metrics["ensemble"]["MdAPE"])


if __name__ == "__main__":
    main()
