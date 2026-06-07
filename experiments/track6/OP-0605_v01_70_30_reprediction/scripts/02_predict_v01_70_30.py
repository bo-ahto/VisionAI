#!/usr/bin/env python3
"""Run a reproducible v0.1 70:30 Warm prediction on the prepared feature file.

중요한 해석
-----------
v0.1 정책 식은 아래와 같이 고정되어 있다.

    pred_log = 0.70 * svc_numeric_seed_mean
             + 0.30 * pp_v8_compact_blend_mape_guarded

`svc_numeric_seed_mean`은 PP-SVC2 방식 그대로 train 비교군 피처와 seed 10개
Warm Huber를 재학습해 신규 데이터에 적용한다.

다만 `pp_v8_compact_blend_mape_guarded`의 원천 후보 전체가 신규 데이터용
단일 artifact로 저장되어 있지 않다. 그래서 이 스크립트는 기존 PP-V8
validation/test 예측값을 target으로 삼아 CatBoost distillation component를
만든 뒤, 그 component를 30% 축으로 사용한다.

따라서 결과 컬럼은 `v01_70_30_repred_*`로 저장하되, 재현 상태는
`distilled_ppv8_component`로 명시한다. 원천 후보들을 모두 분해한 완전 exact
artifact가 생기면 이 스크립트의 PP-V8 component 부분만 교체하면 된다.
"""
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
        if (current / "scripts" / "track6").exists() and (current / "experiments" / "track6").exists():
            return current
    raise RuntimeError(f"VisionAI repo root를 찾을 수 없습니다: {start}")


REPO = find_repo_root(Path(__file__).resolve())
SCRIPT_DIR = REPO / "scripts" / "track6"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_pp_svc1_comparable_stats_feature_validation as svc1  # noqa: E402
import run_pp_svc2_warm_comparable_stats_stability as svc2  # noqa: E402
from predict_price_prediction_v0_1_test_file import predict_legacy_pipeline  # noqa: E402
from run_pre_pp_experiments import GENERATED, artifact_features, load_scope  # noqa: E402


EXP_DIR = REPO / "experiments" / "track6" / "OP-0605_v01_70_30_reprediction"
MODEL_ROOT = REPO / "models" / "track6" / "price_prediction_v0.1"
DEFAULT_FEATURE_DIR = EXP_DIR / "data" / "features"
DEFAULT_OUTPUT_DIR = EXP_DIR / "outputs" / "predictions"

FX_KRW_PER_UNIT = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "JPY": 9.5,
}

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

BASE_NUMERIC = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict v0.1 70:30 Warm candidate on prepared features.")
    parser.add_argument("--feature-dir", type=Path, default=DEFAULT_FEATURE_DIR, help="01 스크립트의 feature output dir")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="예측 출력 폴더")
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


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def ensure_artist_volume(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "artist_works_count_train" not in out.columns:
        out["artist_works_count_train"] = np.nan
    out["artist_works_count_train"] = pd.to_numeric(out["artist_works_count_train"], errors="coerce")
    if "artist_works_log" not in out.columns:
        out["artist_works_log"] = np.log1p(out["artist_works_count_train"].fillna(0))
    else:
        out["artist_works_log"] = pd.to_numeric(out["artist_works_log"], errors="coerce")
    return out


def ensure_dummy_label_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Add harmless label placeholders for helper functions that expect labels.

    `svc1.apply_comparable_stats` only needs target rows as grouping keys, but its
    shared normalizer expects `ln_price_krw` and `price_krw` to exist.  The target
    values are not used in the returned comparable statistics, so fixed dummy
    values are safe for no-price operation inputs.
    """
    out = frame.copy()
    if "ln_price_krw" not in out.columns:
        out["ln_price_krw"] = 0.0
    if "price_krw" not in out.columns:
        out["price_krw"] = 1.0
    return out


def drop_existing_svc_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop(columns=[*svc1.SVC_NUMERIC, *svc1.SVC_CATEGORICAL, "svc_group_n"], errors="ignore")


def build_svc_numeric_seed_mean(new_features: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Recreate PP-SVC2 `svc_numeric_seed_mean` for new rows."""
    base_features = artifact_features()["warm"]
    requested = unique([*base_features, *svc1.GROUPING_FEATURES])
    train_base, _val_base, _test_base = load_scope("warm", requested)
    new_base = ensure_dummy_label_columns(ensure_artist_volume(drop_existing_svc_columns(new_features)))
    new_stats = svc1.apply_comparable_stats(train_base, new_base)
    new_with_stats = new_base.merge(new_stats, on="_track6_row_id", how="left")
    model_features = unique([*base_features, *svc1.SVC_NUMERIC])

    seed_preds: list[np.ndarray] = []
    seed_rows: list[dict[str, Any]] = []
    for seed in svc2.SEEDS:
        train_stats = svc2.crossfit_train_stats(train_base, seed)
        train_s = train_base.merge(train_stats, on="_track6_row_id", how="left")
        train_n = svc1.normalize(train_s, model_features)
        new_n = svc1.normalize(new_with_stats, model_features)
        pred = svc1.fit_predict("huber", train_n, new_n, new_n, model_features)["validation"]
        seed_preds.append(np.asarray(pred, dtype=float))
        seed_rows.append({
            "seed": int(seed),
            "pred_log_mean": float(np.nanmean(pred)),
            "pred_log_std": float(np.nanstd(pred)),
        })
    seed_matrix = np.vstack(seed_preds)
    diagnostics = pd.DataFrame(seed_rows)
    diagnostics.loc[:, "component"] = "svc_numeric_seed"
    return np.nanmean(seed_matrix, axis=0), diagnostics


def cat_ready(frame: pd.DataFrame, features: list[str], numeric: set[str]) -> pd.DataFrame:
    out = frame[features].copy()
    for col in features:
        if col in numeric:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = out[col].astype(str).fillna("__MISSING__").replace({"": "__MISSING__"})
    return out


def cat_indices(features: list[str], numeric: set[str]) -> list[int]:
    return [idx for idx, col in enumerate(features) if col not in numeric]


def metric_fidelity(actual: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    diff = pred - actual
    return {
        "n": int(len(actual)),
        "MAE_log": float(np.mean(np.abs(diff))),
        "MdAE_log": float(np.median(np.abs(diff))),
        "RMSE_log": float(np.sqrt(np.mean(diff**2))),
        "p95_abs_log_error": float(np.quantile(np.abs(diff), 0.95)),
    }


def load_ppv8_target() -> pd.DataFrame:
    path = REPO / "experiments" / "track6" / "PP-V8_warm_deployment_simplification" / "outputs" / "predictions.csv"
    df = pd.read_csv(path, low_memory=False)
    target = df[
        df["scope"].astype(str).eq("warm")
        & df["candidate"].astype(str).eq("compact_blend_mape_guarded")
        & df["split"].astype(str).isin(["validation", "test"])
    ][["split", "_track6_row_id", "pred_log"]].copy()
    target = target.rename(columns={"pred_log": "pp_v8_target_pred_log"})
    if target.empty:
        raise ValueError(f"PP-V8 target prediction not found: {path}")
    return target


def build_distillation_split_features(new_features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], set[str]]:
    base_features = artifact_features()["warm"]
    distill_features = unique([
        *base_features,
        *GENERATED,
        "artist_works_log",
        "artist_works_count_train",
        *svc1.SVC_NUMERIC,
        *svc1.SVC_CATEGORICAL,
        "svc_group_n",
    ])
    requested = unique([feature for feature in distill_features if feature not in svc1.SVC_NUMERIC + svc1.SVC_CATEGORICAL + ["svc_group_n"]])
    train_base, val_base, test_base = load_scope("warm", requested)
    train_s, val_s, test_s = svc2.add_service_features_seed(train_base, val_base, test_base, svc2.SEEDS[0])
    new_s = ensure_artist_volume(new_features.copy())

    available = [col for col in distill_features if col in val_s.columns and col in test_s.columns and col in new_s.columns]
    numeric = {col for col in available if col in BASE_NUMERIC}
    return val_s, test_s, new_s, available, numeric


def build_ppv8_distilled_component(new_features: pd.DataFrame) -> tuple[np.ndarray, dict[str, Any]]:
    """Distill PP-V8 compact blend predictions into a deployable component."""
    val_s, test_s, new_s, features, numeric = build_distillation_split_features(new_features)
    target = load_ppv8_target()
    val_train = val_s.merge(target[target["split"].eq("validation")], on="_track6_row_id", how="inner")
    test_eval = test_s.merge(target[target["split"].eq("test")], on="_track6_row_id", how="inner")
    train_all = pd.concat([val_train, test_eval], ignore_index=True)

    model_params = {
        "loss_function": "RMSE",
        "iterations": 450,
        "learning_rate": 0.035,
        "depth": 6,
        "l2_leaf_reg": 8.0,
        "random_seed": 20260602,
        "verbose": False,
        "allow_writing_files": False,
    }

    validation_model = CatBoostRegressor(**model_params)
    validation_model.fit(
        cat_ready(val_train, features, numeric),
        val_train["pp_v8_target_pred_log"].to_numpy(dtype=float),
        cat_features=cat_indices(features, numeric),
    )
    test_pred = np.asarray(validation_model.predict(cat_ready(test_eval, features, numeric)), dtype=float)
    fidelity = metric_fidelity(test_eval["pp_v8_target_pred_log"].to_numpy(dtype=float), test_pred)

    final_model = CatBoostRegressor(**model_params)
    final_model.fit(
        cat_ready(train_all, features, numeric),
        train_all["pp_v8_target_pred_log"].to_numpy(dtype=float),
        cat_features=cat_indices(features, numeric),
    )
    new_pred = np.asarray(final_model.predict(cat_ready(new_s, features, numeric)), dtype=float)
    info = {
        "component": "pp_v8_compact_blend_mape_guarded_distilled",
        "target_source": "experiments/track6/PP-V8_warm_deployment_simplification/outputs/predictions.csv",
        "distillation_model": "CatBoostRegressor",
        "features": features,
        "numeric_features": sorted(numeric),
        "train_rows_final": int(len(train_all)),
        "fidelity_test_from_validation_only": fidelity,
        "interpretation": "PP-V8 원천 후보 전체가 단일 artifact로 없어 기존 PP-V8 예측값을 모사한 component",
    }
    return new_pred, info


def add_legacy_huber_predictions(new_features: pd.DataFrame, output: pd.DataFrame) -> None:
    model_path = MODEL_ROOT / "legacy_artifacts" / "track6_warm_huber.joblib"
    if not model_path.exists() or new_features.empty:
        output["legacy_warm_huber_pred_log"] = np.nan
        return
    model = joblib.load(model_path)
    output["legacy_warm_huber_pred_log"] = predict_legacy_pipeline(model, new_features)
    add_price_columns(output, "legacy_warm_huber_pred_log", "legacy_warm_huber_pred_price_krw")


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""# v0.1 70:30 재예측 산출물

- 생성일: {summary['created_at']}
- 입력 피처: `{summary['feature_file']}`
- 전체 행: {summary['total_rows']:,}
- Warm 행: {summary['warm_rows']:,}
- Cold 행: {summary['cold_rows']:,}

## 실행한 후보

- `svc_numeric_seed_mean_pred_log`: PP-SVC2 방식으로 seed 10개 Warm Huber를 재학습해 평균낸 예측 로그값
- `pp_v8_distilled_pred_log`: 기존 PP-V8 `compact_blend_mape_guarded` 예측값을 CatBoost로 모사한 재현용 component
- `v01_70_30_repred_log`: `0.70 * svc_numeric_seed_mean_pred_log + 0.30 * pp_v8_distilled_pred_log`

## exact 여부

- v0.1 정책 식 70:30은 그대로 적용했다.
- 단, PP-V8 30% 축은 원천 후보들을 모두 분해 실행한 값이 아니라 기존 PP-V8 예측을 모사한 distillation component다.
- 원천 후보별 단일 artifact가 준비되면 `pp_v8_distilled_pred_log`를 원천 PP-V8 예측값으로 교체해야 완전한 source-decomposed exact 실행이 된다.

## 생성 파일

- `predictions_all.csv`
- `component_diagnostics.csv`
- `prediction_summary.json`
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

    features = pd.read_csv(feature_file, low_memory=False)
    warm = features[features["warm_cold_route"].astype(str).eq("warm")].copy()
    if len(warm) != len(features):
        raise ValueError("이번 재예측 스크립트는 Warm v0.1 70:30 후보만 처리한다. Cold 행이 있으면 별도 스크립트를 추가해야 한다.")

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

    out["svc_group_median_pred_log"] = pd.to_numeric(warm["svc_group_log_price_median"], errors="coerce")
    add_price_columns(out, "svc_group_median_pred_log", "svc_group_median_pred_price_krw")

    add_legacy_huber_predictions(warm, out)
    out["legacy_log_blend_svc0p7_huber0p3_pred_log"] = (
        0.70 * out["svc_group_median_pred_log"].astype(float)
        + 0.30 * out["legacy_warm_huber_pred_log"].astype(float)
    )
    add_price_columns(out, "legacy_log_blend_svc0p7_huber0p3_pred_log", "legacy_log_blend_svc0p7_huber0p3_pred_price_krw")

    svc_seed_pred, svc_diag = build_svc_numeric_seed_mean(warm)
    out["svc_numeric_seed_mean_pred_log"] = svc_seed_pred
    add_price_columns(out, "svc_numeric_seed_mean_pred_log", "svc_numeric_seed_mean_pred_price_krw")

    ppv8_pred, ppv8_info = build_ppv8_distilled_component(warm)
    out["pp_v8_distilled_pred_log"] = ppv8_pred
    add_price_columns(out, "pp_v8_distilled_pred_log", "pp_v8_distilled_pred_price_krw")

    out["v01_70_30_repred_log"] = 0.70 * out["svc_numeric_seed_mean_pred_log"] + 0.30 * out["pp_v8_distilled_pred_log"]
    add_price_columns(out, "v01_70_30_repred_log", "v01_70_30_repred_price_krw")
    out["v01_70_30_reproduction_status"] = "policy_formula_exact_with_distilled_ppv8_component"

    predictions_path = output_dir / "predictions_all.csv"
    out.to_csv(predictions_path, index=False)
    diagnostics = pd.concat([
        svc_diag,
        pd.DataFrame([{
            "component": ppv8_info["component"],
            "seed": np.nan,
            "pred_log_mean": float(np.nanmean(ppv8_pred)),
            "pred_log_std": float(np.nanstd(ppv8_pred)),
        }]),
    ], ignore_index=True)
    diagnostics.to_csv(output_dir / "component_diagnostics.csv", index=False)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "feature_file": str(feature_file.relative_to(REPO)),
        "output_dir": str(output_dir.relative_to(REPO)),
        "total_rows": int(len(features)),
        "warm_rows": int(len(warm)),
        "cold_rows": int(len(features) - len(warm)),
        "formula": "v01_70_30_repred_log = 0.70 * svc_numeric_seed_mean_pred_log + 0.30 * pp_v8_distilled_pred_log",
        "reproduction_status": "policy_formula_exact_with_distilled_ppv8_component",
        "pp_v8_component_info": ppv8_info,
        "output_files": {
            "predictions_all": str(predictions_path.relative_to(REPO)),
            "component_diagnostics": str((output_dir / "component_diagnostics.csv").relative_to(REPO)),
            "summary": str((output_dir / "prediction_summary.json").relative_to(REPO)),
        },
    }
    (output_dir / "prediction_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(output_dir, summary)
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
