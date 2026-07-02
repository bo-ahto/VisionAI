#!/usr/bin/env python3
"""Build a Warm PP252 upstream refreeze candidate.

This script does not replace the selected Warm report model.  It audits which
PP252 upstream pieces can be serialized for raw-input service use and checks the
gap against the original fixed-test PP258 inputs.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
PP253_SCRIPT = REPO / "scripts" / "track6" / "run_pp_opt253_258_warm_pp252_narrow_direction_residual_refinement.py"
PP258_SCRIPT = REPO / "experiments" / "track6" / "SUB-WARM-PP258_operational_fixed_test_submission" / "scripts" / "pp258_reproduce_fixed_test.py"
SOURCE_EXP = REPO / "experiments" / "track6" / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
SOURCE_DETAIL = SOURCE_EXP / "artifacts" / "pp252_narrow_refinement_feature_detail.csv"
PACKAGED_INPUT = (
    REPO
    / "experiments"
    / "track6"
    / "SUB-WARM-PP258_operational_fixed_test_submission"
    / "data"
    / "pp258_model_input_validation_test.csv"
)
PACKAGED_PREDICTIONS = (
    REPO
    / "experiments"
    / "track6"
    / "SUB-WARM-PP258_operational_fixed_test_submission"
    / "outputs"
    / "pp258_test_predictions.csv"
)
MODEL_DIR = REPO / "models" / "track6" / "warm_pp252_upstream_refreeze_candidate"
ARTIFACT_DIR = MODEL_DIR / "artifacts"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "warm_pp252_upstream_refreeze_candidate.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "warm_pp252_upstream_refreeze_candidate.md"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [ARTIFACT_DIR, DOC_JSON.parent]:
        path.mkdir(parents=True, exist_ok=True)


def prediction_probability(model: Any, features: pd.DataFrame) -> np.ndarray:
    classes = list(model.named_steps["clf"].classes_)
    proba = model.predict_proba(features)
    pos_idx = classes.index(1) if 1 in classes else None
    if pos_idx is None:
        return np.zeros(len(features), dtype=float)
    return np.nan_to_num(proba[:, pos_idx], nan=0.5, posinf=0.5, neginf=0.5)


def compare_array(name: str, actual: np.ndarray, expected: np.ndarray, mask: np.ndarray | None = None) -> dict[str, Any]:
    a = np.asarray(actual, dtype=float)
    e = np.asarray(expected, dtype=float)
    if mask is not None:
        a = a[mask]
        e = e[mask]
    diff = np.abs(a - e)
    return {
        "name": name,
        "n": int(len(diff)),
        "max_abs_diff": float(np.nanmax(diff)) if len(diff) else None,
        "mean_abs_diff": float(np.nanmean(diff)) if len(diff) else None,
        "p95_abs_diff": float(np.nanquantile(diff, 0.95)) if len(diff) else None,
        "allclose_1e_12": bool(np.allclose(a, e, rtol=0.0, atol=1e-12, equal_nan=True)) if len(diff) else False,
    }


def build_pp258_input(base: pd.DataFrame, pp252: np.ndarray, pp252_stability: np.ndarray, prob: np.ndarray, residual: np.ndarray) -> pd.DataFrame:
    wanted = [
        "eval_split",
        "split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "confidence_tier",
        "stable_price_band",
        "actual_log",
        "actual_price",
        "hcoef_stable",
        "current_70_30",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
    ]
    out = base[[col for col in wanted if col in base.columns]].copy()
    if "split" not in out.columns and "eval_split" in out.columns:
        out["split"] = out["eval_split"]
    out["pp252_log"] = pp252
    out["pp252_stability_log"] = pp252_stability
    out["prob_hist35_pp252"] = prob
    out["resid_huber_pp252"] = residual
    return out


def metrics_delta(pp258: Any, candidate_predictions: pd.DataFrame) -> dict[str, Any]:
    test = candidate_predictions[candidate_predictions["eval_split"].eq("test")].copy()
    candidate_metrics = pp258.metrics(test)
    result: dict[str, Any] = {"candidate_metrics": candidate_metrics}
    if PACKAGED_PREDICTIONS.exists():
        stored = pd.read_csv(PACKAGED_PREDICTIONS, low_memory=False)
        compare = candidate_predictions.merge(
            stored[["eval_split", "_track6_row_id", "final_price", "final_price_log"]],
            on=["eval_split", "_track6_row_id"],
            how="inner",
            suffixes=("_candidate", "_stored"),
        )
        test_compare = compare[compare["eval_split"].eq("test")].copy()
        result["stored_prediction_compare"] = {
            "n": int(len(test_compare)),
            "max_final_price_abs_diff": float(
                np.nanmax(
                    np.abs(
                        test_compare["final_price_candidate"].to_numpy(dtype=float)
                        - test_compare["final_price_stored"].to_numpy(dtype=float)
                    )
                )
            )
            if len(test_compare)
            else None,
            "max_final_log_abs_diff": float(
                np.nanmax(
                    np.abs(
                        test_compare["final_price_log_candidate"].to_numpy(dtype=float)
                        - test_compare["final_price_log_stored"].to_numpy(dtype=float)
                    )
                )
            )
            if len(test_compare)
            else None,
        }
    return result


def render_markdown(payload: dict[str, Any]) -> str:
    warm = payload["warm_refreeze"]
    rows = warm["parity_checks"]
    lines = [
        "# Warm PP252 상류 재동결 후보 감사",
        "",
        f"- 작성일: {payload['created_at']}",
        "- 목적: 보고서 기준 Warm 최종 모델을 raw 입력 서비스로 승격하기 위해 저장 가능한 상류 모델 범위 확인",
        "- 결론: 방향 분류와 Huber 잔차 보정은 full-fit 모델로 저장 가능. PP252 기준 후보값과 안정 후보값은 아직 이전 후보 생성 경로의 raw adapter가 필요",
        "",
        "## 1. 저장한 후보 아티팩트",
        "",
        "| 구분 | 파일 | 상태 |",
        "|---|---|---|",
        f"| 방향 분류 모델 | `{warm['artifacts']['direction_model']}` | 저장 완료 |",
        f"| Huber 잔차 모델 | `{warm['artifacts']['huber_residual_model']}` | 저장 완료 |",
        f"| 피처 스키마 | `{warm['artifacts']['feature_schema']}` | 저장 완료 |",
        f"| 입력 재생성 CSV | `{warm['artifacts']['candidate_input']}` | 저장 완료 |",
        "",
        "## 2. 원본 PP258 입력 대비 차이",
        "",
        "| 항목 | 구간 | n | 최대 차이 | 평균 차이 | p95 차이 | 1e-12 일치 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for item in rows:
        lines.append(
            "| {name} | {split} | {n} | {max_abs_diff} | {mean_abs_diff} | {p95_abs_diff} | {allclose} |".format(
                name=item["name"],
                split=item["split"],
                n=item["n"],
                max_abs_diff=item["max_abs_diff"],
                mean_abs_diff=item["mean_abs_diff"],
                p95_abs_diff=item["p95_abs_diff"],
                allclose="예" if item["allclose_1e_12"] else "아니오",
            )
        )
    metrics = warm["pp258_metrics_delta"]
    candidate = metrics["candidate_metrics"]
    compare = metrics.get("stored_prediction_compare", {})
    lines.extend(
        [
            "",
            "## 3. PP258 최종층 재계산 결과",
            "",
            "| 항목 | 값 |",
            "|---|---:|",
            f"| test n | {candidate['n']} |",
            f"| MdAPE | {candidate['MdAPE']:.12f} |",
            f"| MAPE | {candidate['MAPE']:.12f} |",
            f"| p95 APE | {candidate['p95_APE']:.12f} |",
            f"| RMSE log | {candidate['RMSE_log']:.12f} |",
            f"| 저장 결과 대비 최대 가격 차이 | {compare.get('max_final_price_abs_diff')} |",
            f"| 저장 결과 대비 최대 로그가격 차이 | {compare.get('max_final_log_abs_diff')} |",
            "",
            "## 4. 운영 adapter 승격 판단",
            "",
            "- 승격 가능: `prob_hist35_pp252`, `resid_huber_pp252`를 만드는 방향 분류/Huber 잔차 모델",
            "- 추가 필요: `pp252_log`, `pp252_stability_log`를 원시 입력에서 만드는 직전 후보 생성 adapter",
            "- 현재 의미: Warm 최종층 직전의 일부 상류 모델은 저장 가능 상태로 전환됨. 다만 전체 exact raw adapter는 아직 PP252 기준 후보 생성 경로가 남아 있음",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ensure_dirs()
    pp253 = load_module(PP253_SCRIPT, "warm_pp252_refreeze_pp253")
    pp258 = load_module(PP258_SCRIPT, "warm_pp252_refreeze_pp258")

    previous, previous_config = pp253.load_inputs()
    previous_decision = previous_config["selection_decision"]
    pp246_decision = previous_config["previous_decision"]
    base = pp253.pp187.base_frame(previous)
    feature_base = pp253.pp187.load_feature_frame(base)

    pp252 = pp253.pp187.prediction_array(previous, feature_base, previous_decision["balanced_protocol_candidate"])
    pp252_stability = pp253.pp187.prediction_array(previous, feature_base, previous_decision["operational_protocol_candidate"])
    pp252_recovery = pp253.pp187.prediction_array(previous, feature_base, previous_decision["p95_recovery_protocol_candidate"])
    pp252_guarded = pp253.pp187.prediction_array(previous, feature_base, previous_decision["p95_guarded_protocol_candidate"])
    pp252_extreme = pp253.pp187.prediction_array(previous, feature_base, previous_decision["p95_extreme_protocol_candidate"])
    pp246 = pp253.pp187.prediction_array(previous, feature_base, pp246_decision["balanced_protocol_candidate"])

    features = pp253.pp247.build_features(
        feature_base,
        pp252,
        pp246,
        pp252_stability,
        pp252_guarded,
        pp252_recovery,
        pp252_extreme,
    )
    val_mask = feature_base["eval_split"].eq("validation_oof").to_numpy()
    test_mask = feature_base["eval_split"].eq("test").to_numpy()
    residual_target = feature_base["actual_log"].to_numpy(dtype=float) - pp252
    direction_target = (residual_target[val_mask] > 0.0).astype(int)

    direction_model = pp253.pp247.make_classifier("hist_gbc", 35, 17)
    direction_model.fit(features.loc[val_mask], direction_target)
    fullfit_prob = prediction_probability(direction_model, features)

    huber_model = pp253.pp241.make_linear_model("huber", 1.15)
    huber_model.fit(features.loc[val_mask], residual_target[val_mask])
    fullfit_residual = np.nan_to_num(huber_model.predict(features), nan=0.0, posinf=0.0, neginf=0.0)

    source_detail = pd.read_csv(SOURCE_DETAIL, low_memory=False)
    packaged_input = pd.read_csv(PACKAGED_INPUT, low_memory=False)
    candidate_input = build_pp258_input(feature_base, pp252, pp252_stability, fullfit_prob, fullfit_residual)
    candidate_predictions = pp258.calculate_pp258_predictions(candidate_input)

    key_cols = ["eval_split", "_track6_row_id"]
    detail_compare = source_detail[key_cols + ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]].merge(
        candidate_input[key_cols + ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]],
        on=key_cols,
        suffixes=("_source", "_candidate"),
        how="inner",
    )
    packaged_compare = packaged_input[key_cols + ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]].merge(
        candidate_input[key_cols + ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]],
        on=key_cols,
        suffixes=("_packaged", "_candidate"),
        how="inner",
    )

    parity_checks: list[dict[str, Any]] = []
    split_masks = {
        "all": np.ones(len(detail_compare), dtype=bool),
        "validation_oof": detail_compare["eval_split"].eq("validation_oof").to_numpy(),
        "test": detail_compare["eval_split"].eq("test").to_numpy(),
    }
    for col in ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]:
        for split, mask in split_masks.items():
            item = compare_array(
                col,
                detail_compare[f"{col}_candidate"].to_numpy(dtype=float),
                detail_compare[f"{col}_source"].to_numpy(dtype=float),
                mask,
            )
            item["split"] = split
            parity_checks.append(item)

    package_masks = {
        "packaged_all": np.ones(len(packaged_compare), dtype=bool),
        "packaged_test": packaged_compare["eval_split"].eq("test").to_numpy(),
    }
    for col in ["pp252_log", "pp252_stability_log", "prob_hist35_pp252", "resid_huber_pp252"]:
        for split, mask in package_masks.items():
            item = compare_array(
                col,
                packaged_compare[f"{col}_candidate"].to_numpy(dtype=float),
                packaged_compare[f"{col}_packaged"].to_numpy(dtype=float),
                mask,
            )
            item["split"] = split
            parity_checks.append(item)

    direction_path = ARTIFACT_DIR / "direction_hist_gbc_35_seed17_fullfit.joblib"
    huber_path = ARTIFACT_DIR / "huber_residual_epsilon1p15_fullfit.joblib"
    schema_path = ARTIFACT_DIR / "feature_schema.json"
    candidate_input_path = ARTIFACT_DIR / "pp252_refreeze_candidate_pp258_input.csv"
    candidate_prediction_path = ARTIFACT_DIR / "pp252_refreeze_candidate_pp258_predictions.csv"
    manifest_path = MODEL_DIR / "manifest.json"
    joblib.dump(direction_model, direction_path)
    joblib.dump(huber_model, huber_path)
    schema = {
        "categorical_columns": list(pp253.pp247.CAT_COLS),
        "numeric_columns": list(pp253.pp247.NUM_COLS),
        "feature_columns": list(features.columns),
        "target_source": {
            "direction_target": "actual_log > pp252_log on validation_oof",
            "residual_target": "actual_log - pp252_log on validation_oof",
        },
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    candidate_input.to_csv(candidate_input_path, index=False)
    candidate_predictions.to_csv(candidate_prediction_path, index=False)

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "warm_refreeze": {
            "source_experiment": rel(SOURCE_EXP),
            "model_dir": rel(MODEL_DIR),
            "rows": {
                "total": int(len(feature_base)),
                "validation_oof": int(val_mask.sum()),
                "test": int(test_mask.sum()),
            },
            "artifacts": {
                "direction_model": rel(direction_path),
                "huber_residual_model": rel(huber_path),
                "feature_schema": rel(schema_path),
                "candidate_input": rel(candidate_input_path),
                "candidate_predictions": rel(candidate_prediction_path),
                "manifest": rel(manifest_path),
            },
            "parity_checks": parity_checks,
            "pp258_metrics_delta": metrics_delta(pp258, candidate_predictions),
            "remaining_blockers": [
                "pp252_log 기준 후보를 원시 입력에서 생성하는 직전 후보 adapter",
                "pp252_stability_log 안정 후보를 원시 입력에서 생성하는 직전 후보 adapter",
                "위 두 기준 후보의 하위 feature engineering과 모델 파일 패키징",
            ],
        },
    }
    manifest = {
        "model_id": "warm_pp252_upstream_refreeze_candidate",
        "created_at": payload["created_at"],
        "status": "partial_upstream_refreeze_candidate",
        "can_serve_new_raw_input_fully": False,
        "serialized_components": [
            "prob_hist35_pp252 direction classifier",
            "resid_huber_pp252 residual regressor",
        ],
        "remaining_csv_dependent_components": [
            "pp252_log",
            "pp252_stability_log",
        ],
        "docs": {
            "json": rel(DOC_JSON),
            "markdown": rel(DOC_MD),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
