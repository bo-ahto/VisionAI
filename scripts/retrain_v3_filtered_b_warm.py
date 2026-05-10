"""B-retuned warm artifact 학습 — PR-WARM-B Stage 1.

Prereg: docs/pr_warm_b_deployment_prereg_20260510.md (R1 LGTM with minor 반영)
Decision binding: ✅ YES (cycle B / commit 3a27002 ADOPT_warm_retuned 운영 적용 Stage 1)

설계 (Stage 1 첫 run 후 cold byte-identity 검증 결과 fix):
- CatBoost cold artifact: **default tuned에서 COPY** (cold path bit-identical 보장 / data/lib 버전 차이로 재학습 시 다른 binary 산출되는 이슈 회피)
- XGBoost warm artifact: **B-retuned params로 신규 학습** (warm slice / cycle B Δ_warm=-1.62pp 정합)
- label_maps / warm_artists / source_calibration: COPY from default tuned (cold path 정합 / source_calibration는 model_target rename)

산출 artifact (8 file / b_warm_ prefix):
- catboost.cbm (COPY / bit-identical to default tuned)
- xgboost.json (NEW / B-retuned warm)
- xgboost_label_maps.json (COPY)
- warm_artists.json (COPY)
- source_calibration.json (COPY + model_target rename / warm_factors 재추정 deferred)
- metrics.json (NEW / GroupKFold cold + KFold warm)
- best_params.json (NEW / catboost: default / xgboost: B-retuned / provenance)
- manifest.json (NEW / SHA256 + dataset fingerprint + integrity)

R1 amendment 반영:
- artifact manifest 생성
- warm_artists.json / label_maps.json / catboost.cbm exact hash 검증 (COPY → guaranteed match)
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import xgboost as xgb

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from train_primary_market_v3_filtered import (  # type: ignore
    CB_FEATURES,
    _label_encode_xgb,
    _warm_mask,
    load_data,
    prepare_features,
)
from tune_primary_market_v3_filtered import (  # type: ignore
    WARM_MIN_COUNT,
    _final_cv_groupkfold_5,
    _final_cv_kfold_5,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = REPO / "model_test_results"
DEFAULT_BEST_PARAMS_PATH = OUT_DIR / "integrated_v3_filtered_tuned_best_params.json"
B_WARM_PARAMS_PATH = OUT_DIR / "warm_only_retuned_best_params.json"
PREFIX = "integrated_v3_filtered_tuned_b_warm"
DEFAULT_PREFIX = "integrated_v3_filtered_tuned"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def _dataset_fingerprint(df: pd.DataFrame) -> tuple[str, dict]:
    payload = df.sort_index(axis=1).to_csv(index=True).encode("utf-8")
    sha256 = hashlib.sha256(payload).hexdigest()
    return sha256, {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "sha256": sha256,
    }


def main() -> None:
    logger.info("=" * 70)
    logger.info("PR-WARM-B Stage 1: B-retuned warm artifact 학습")
    logger.info("=" * 70)

    # CatBoost params: 기존 default tuned 재사용
    with DEFAULT_BEST_PARAMS_PATH.open() as f:
        default_best = json.load(f)
    cb_best = default_best["catboost"]
    logger.info("CatBoost best params (default tuned 재사용): %s", cb_best)

    # XGBoost params: B-retuned warm (cycle B 결과)
    if not B_WARM_PARAMS_PATH.exists():
        raise FileNotFoundError(
            f"B-retuned warm params 없음 ({B_WARM_PARAMS_PATH}) — cycle B (commit 3a27002) 산출물 필요"
        )
    with B_WARM_PARAMS_PATH.open() as f:
        b_warm = json.load(f)
    xgb_best = dict(b_warm["xgb_retuned_warm"])
    logger.info("XGBoost best params (B-retuned warm): %s", xgb_best)

    # Data load (default tuned 재학습과 동일 데이터)
    df = load_data()
    df = df[df["is_excluded_for_training"] == 0].copy()
    X, y, groups = prepare_features(df)
    source = df["source"].astype(str).to_numpy()
    dataset_sha, dataset_meta = _dataset_fingerprint(df)
    logger.info("Data: %d rows / %d artists / %d features / fingerprint=%s...",
                len(df), len(set(groups)), len(CB_FEATURES), dataset_sha[:12])

    warm_mask = _warm_mask(groups)
    X_warm = X.iloc[warm_mask].reset_index(drop=True)
    y_warm = y[warm_mask]
    n_warm = int(warm_mask.sum())
    n_warm_artists = int(pd.Series(groups[warm_mask]).nunique())
    logger.info("Warm slice: %d works / %d artists", n_warm, n_warm_artists)

    # Final 5-fold CV (B-retuned XGB params로)
    logger.info("--- GroupKFold 5 (cold) ---")
    gkf_metrics = _final_cv_groupkfold_5(X, y, groups, source, cb_best, xgb_best)
    logger.info("--- KFold 5 (warm) ---")
    warm_groups = groups[warm_mask]
    warm_source = source[warm_mask]
    kf_metrics = _final_cv_kfold_5(X_warm, y_warm, cb_best, xgb_best,
                                    groups=warm_groups, source=warm_source)
    kf_metrics["_note"] = (
        f"Evaluated on warm slice only ({n_warm} works, {n_warm_artists} artists, "
        f"artist 작품수>={WARM_MIN_COUNT}) / B-retuned XGB params"
    )

    # XGB warm 신규 학습 (B-retuned params로)
    logger.info("--- XGB warm 신규 학습 (B-retuned params) ---")
    Xe_warm, _, label_maps = _label_encode_xgb(X_warm, X_warm.iloc[:1])
    dtrain = xgb.DMatrix(Xe_warm, label=y_warm)
    xgb_p = {k: v for k, v in xgb_best.items() if k != "num_boost_round"}
    xgb_final = xgb.train(
        params={**xgb_p, "objective": "reg:squarederror", "verbosity": 1, "seed": 42},
        dtrain=dtrain, num_boost_round=xgb_best.get("num_boost_round", 1000),
    )

    # Save artifacts
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cbm_path = OUT_DIR / f"{PREFIX}_catboost.cbm"
    xgbjson_path = OUT_DIR / f"{PREFIX}_xgboost.json"
    label_maps_path = OUT_DIR / f"{PREFIX}_xgboost_label_maps.json"
    warm_artists_path = OUT_DIR / f"{PREFIX}_warm_artists.json"
    calib_path = OUT_DIR / f"{PREFIX}_source_calibration.json"
    metrics_path = OUT_DIR / f"{PREFIX}_metrics.json"
    best_params_path = OUT_DIR / f"{PREFIX}_best_params.json"
    manifest_path = OUT_DIR / f"{PREFIX}_manifest.json"

    # COPY cold artifacts from default tuned (cold path bit-identical 보장)
    import shutil
    logger.info("--- COPY cold artifacts (catboost / label_maps / warm_artists / calibration) ---")
    default_cb_path = OUT_DIR / f"{DEFAULT_PREFIX}_catboost.cbm"
    default_label_maps_path = OUT_DIR / f"{DEFAULT_PREFIX}_xgboost_label_maps.json"
    default_warm_artists_path = OUT_DIR / f"{DEFAULT_PREFIX}_warm_artists.json"
    default_calib_path = OUT_DIR / f"{DEFAULT_PREFIX}_source_calibration.json"

    for src, dst, label in [
        (default_cb_path, cbm_path, "catboost.cbm"),
        (default_label_maps_path, label_maps_path, "label_maps.json"),
        (default_warm_artists_path, warm_artists_path, "warm_artists.json"),
    ]:
        if not src.exists():
            raise FileNotFoundError(f"default {label} 없음 ({src}) — Stage 1 prerequisite")
        shutil.copyfile(src, dst)
        logger.info("  COPY %s ✓", label)

    # source_calibration: model_target rename
    with default_calib_path.open() as f:
        calib_data = json.load(f)
    calib_data["model_target"] = "v3_filtered_tuned_b_warm"
    calib_data["_carry_forward_note"] = (
        "Carried forward from integrated_v3_filtered_tuned_source_calibration.json (PR-WARM-B Stage 1). "
        "Cold path bit-identical (CB COPY) → cold_factors 그대로 적용 가능. "
        "Warm path는 XGB params 변경 (B-retuned) → warm_factors 재추정은 별도 후속 단계 권고. "
        "현 carry-forward는 conservative non-regression baseline (warm factors 모두 ~1.0 / no-op-ish)."
    )
    with calib_path.open("w") as f:
        json.dump(calib_data, f, ensure_ascii=False, indent=2)
    logger.info("  COPY source_calibration.json + model_target rename ✓")

    # XGB warm new save
    xgb_final.save_model(str(xgbjson_path))

    n_excluded = int((df["is_excluded_for_training"] == 1).sum())
    metrics_doc = {
        "model": PREFIX,
        "data": f"{len(df)} = filtered (excluded {n_excluded}), B-retuned warm artifact",
        "features": len(CB_FEATURES),
        "artists": len(set(groups)),
        "best_params": {"catboost": cb_best, "xgboost": xgb_best},
        "groupkfold": gkf_metrics,
        "kfold": kf_metrics,
        "label_maps": label_maps,
        "note": "PR-WARM-B Stage 1 / cycle B (commit 3a27002) ADOPT_warm_retuned 운영 적용",
    }
    with metrics_path.open("w") as f:
        json.dump(metrics_doc, f, ensure_ascii=False, indent=2)

    # Force-add 대상: best_params + manifest
    with best_params_path.open("w") as f:
        json.dump({
            "catboost": cb_best,
            "xgboost": xgb_best,
            "_provenance": {
                "catboost_source": "integrated_v3_filtered_tuned_best_params.json (default tuned)",
                "xgboost_source": "warm_only_retuned_best_params.json (B-retuned / cycle 3a27002)",
                "cycle_b_baseline_warm_cv": b_warm.get("baseline_warm_cv"),
                "cycle_b_best_warm_cv": b_warm.get("best_warm_cv"),
                "cycle_b_n_trials": b_warm.get("n_trials"),
            },
        }, f, ensure_ascii=False, indent=2)

    # R1 amendment: artifact integrity check (COPY → exact hash 보장)
    integrity = {
        "catboost_match": _sha256_file(cbm_path) == _sha256_file(default_cb_path),
        "warm_artists_match": _sha256_file(warm_artists_path) == _sha256_file(default_warm_artists_path),
        "label_maps_match": _sha256_file(label_maps_path) == _sha256_file(default_label_maps_path),
        "calibration_carry_forward": {
            "source": default_calib_path.name,
            "model_target_renamed": "v3_filtered_tuned_b_warm",
            "warm_factors_re_fit_status": "deferred (carry-forward conservative baseline)",
        },
    }
    for k in ("catboost_match", "warm_artists_match", "label_maps_match"):
        status = "✅" if integrity[k] else "⚠️"
        logger.info("%s %s exact hash match vs default tuned", status, k)

    # Manifest
    artifact_files = [cbm_path, xgbjson_path, label_maps_path, warm_artists_path,
                      calib_path, metrics_path, best_params_path]
    manifest = {
        "prefix": PREFIX,
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "dataset": dataset_meta,
        "params_provenance": {
            "catboost_from": "integrated_v3_filtered_tuned_best_params.json",
            "xgboost_from": "warm_only_retuned_best_params.json (cycle B)",
            "cycle_b_commit": "3a27002",
        },
        "artifact_files": {p.name: {"sha256": _sha256_file(p), "size": p.stat().st_size}
                           for p in artifact_files},
        "integrity_check": integrity,
        "cv_summary": {
            "groupkfold_cold_ensemble": gkf_metrics.get("ensemble", {}).get("MdAPE"),
            "kfold_warm_ensemble": kf_metrics.get("ensemble", {}).get("MdAPE"),
        },
    }
    with manifest_path.open("w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info("=" * 70)
    logger.info("PR-WARM-B Stage 1 완료 — artifact bundle 7 file 산출")
    logger.info("=" * 70)
    logger.info("Manifest: %s", manifest_path.name)
    logger.info("warm_artists exact match: %s", integrity.get("warm_artists_match"))
    logger.info("label_maps exact match: %s", integrity.get("label_maps_match"))
    if "ensemble" in gkf_metrics:
        logger.info("GroupKFold ensemble cold MdAPE: %.2f%%", gkf_metrics["ensemble"]["MdAPE"])
    if "ensemble" in kf_metrics:
        logger.info("KFold warm ensemble MdAPE: %.2f%%", kf_metrics["ensemble"]["MdAPE"])


if __name__ == "__main__":
    main()
