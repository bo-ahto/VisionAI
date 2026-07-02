#!/usr/bin/env python3
"""Build a reproducible submission-style package for the selected Warm PP258 model."""
from __future__ import annotations

import json
import math
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE_EXP = REPO / "experiments" / "track6" / "PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement"
TARGET_EXP = REPO / "experiments" / "track6" / "SUB-WARM-PP258_operational_fixed_test_submission"

SOURCE_CONFIG = SOURCE_EXP / "artifacts" / "run_config.json"
SOURCE_FEATURE_DETAIL = SOURCE_EXP / "artifacts" / "pp252_narrow_refinement_feature_detail.csv"
SOURCE_PREDICTIONS = SOURCE_EXP / "outputs" / "candidate_predictions.csv"
SOURCE_REPORTS = SOURCE_EXP / "reports"

DATA_DIR = TARGET_EXP / "data"
SCRIPT_DIR = TARGET_EXP / "scripts"
OUTPUT_DIR = TARGET_EXP / "outputs"
REPORT_DIR = TARGET_EXP / "reports"
ARTIFACT_DIR = TARGET_EXP / "artifacts"
PACKAGE_DIR = TARGET_EXP / "packages"

MODEL_PARAMS = {
    "direction_confidence_threshold": 0.12,
    "huber_residual_strength": 0.025,
    "stability_target_strength": 0.0,
    "positive_log_cap": 0.00005,
    "negative_log_cap": 0.000035,
    "quantile_width_shrink": 0.55,
    "row_risk_shrink": 0.80,
    "minimum_log_cap": 0.000006,
}


def ensure_dirs() -> None:
    for path in [DATA_DIR, SCRIPT_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, PACKAGE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def row_risk(frame: pd.DataFrame, source: np.ndarray, target: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(frame["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(frame["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(frame["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(target - source))
    low_conf = frame["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0.0, 1.0)
    return np.clip(
        0.25 * qwidth
        + 0.20 * price_range
        + 0.20 * spread
        + 0.18 * model_gap
        + 0.09 * low_conf
        + 0.08 * low_sample,
        0.0,
        1.0,
    )


def calculate_pp258_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    source = pd.to_numeric(out["pp252_log"], errors="coerce").to_numpy(dtype=float)
    stability_target = pd.to_numeric(out["pp252_stability_log"], errors="coerce").to_numpy(dtype=float)
    prob_up = pd.to_numeric(out["prob_hist35_pp252"], errors="coerce").to_numpy(dtype=float)
    residual = pd.to_numeric(out["resid_huber_pp252"], errors="coerce").to_numpy(dtype=float)

    direction_confidence = np.abs(prob_up - 0.5) * 2.0
    apply_confidence = confidence_weight(prob_up, MODEL_PARAMS["direction_confidence_threshold"])
    residual_direction_match = direction_alignment(residual, prob_up)
    stability_delta = stability_target - source
    stability_direction_match = direction_alignment(stability_delta, prob_up)

    raw_correction = (
        residual
        * residual_direction_match
        * apply_confidence
        * MODEL_PARAMS["huber_residual_strength"]
    )
    raw_correction += (
        stability_delta
        * stability_direction_match
        * apply_confidence
        * MODEL_PARAMS["stability_target_strength"]
    )

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(
        raw_correction >= 0.0,
        MODEL_PARAMS["positive_log_cap"],
        MODEL_PARAMS["negative_log_cap"],
    )
    applied_cap = directional_base_cap
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["quantile_width_shrink"] * q_rank)
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["row_risk_shrink"] * np.clip(risk, 0.0, 1.0))
    applied_cap = np.clip(applied_cap, MODEL_PARAMS["minimum_log_cap"], directional_base_cap)
    applied_correction = np.minimum(np.maximum(raw_correction, -applied_cap), applied_cap)
    final_log = source + applied_correction

    out["direction_confidence"] = direction_confidence
    out["apply_confidence"] = apply_confidence
    out["residual_direction_match"] = residual_direction_match
    out["raw_correction_log"] = raw_correction
    out["uncertainty_rank"] = q_rank
    out["row_risk"] = risk
    out["directional_base_cap_log"] = directional_base_cap
    out["applied_cap_log"] = applied_cap
    out["applied_correction_log"] = applied_correction
    out["final_price_log"] = final_log
    out["final_price"] = safe_exp(final_log)
    if {"actual_price", "actual_log"}.issubset(out.columns):
        actual = pd.to_numeric(out["actual_price"], errors="coerce").to_numpy(dtype=float)
        out["absolute_percentage_error"] = np.abs(out["final_price"].to_numpy(dtype=float) - actual) / np.clip(actual, 1.0, None)
        out["log_error"] = pd.to_numeric(out["actual_log"], errors="coerce").to_numpy(dtype=float) - final_log
    return out


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    valid = (
        pd.to_numeric(frame["actual_price"], errors="coerce").gt(0)
        & pd.to_numeric(frame["actual_log"], errors="coerce").notna()
        & pd.to_numeric(frame["final_price_log"], errors="coerce").notna()
    )
    subset = frame.loc[valid].copy()
    ape = pd.to_numeric(subset["absolute_percentage_error"], errors="coerce").to_numpy(dtype=float)
    log_error = pd.to_numeric(subset["log_error"], errors="coerce").to_numpy(dtype=float)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def load_submission_frame() -> tuple[pd.DataFrame, dict[str, Any]]:
    config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    selected_candidate = config["selection_decision"]["operational_candidate"]
    predictions = pd.read_csv(SOURCE_PREDICTIONS, low_memory=False)
    selected = predictions[predictions["candidate"].eq(selected_candidate)].copy()
    feature_detail = pd.read_csv(SOURCE_FEATURE_DETAIL, low_memory=False)
    feature_cols = [
        "eval_split",
        "_track6_row_id",
        "pp252_log",
        "pp252_stability_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
    ]
    merged = selected.merge(
        feature_detail[feature_cols],
        on=["eval_split", "_track6_row_id"],
        how="left",
        validate="one_to_one",
    )
    if merged[feature_cols[2:]].isna().any().any():
        raise RuntimeError("Missing PP258 formula input columns after merge.")
    return merged, config


def write_reproduction_script() -> None:
    content = r'''#!/usr/bin/env python3
"""Reproduce the selected Warm PP258 fixed-test predictions from packaged CSV files."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MODEL_PARAMS = {
    "direction_confidence_threshold": 0.12,
    "huber_residual_strength": 0.025,
    "stability_target_strength": 0.0,
    "positive_log_cap": 0.00005,
    "negative_log_cap": 0.000035,
    "quantile_width_shrink": 0.55,
    "row_risk_shrink": 0.80,
    "minimum_log_cap": 0.000006,
}


def safe_exp(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return np.exp(np.clip(arr, math.log(1_000.0), math.log(1_000_000_000_000.0)))


def rank01(values: pd.Series | np.ndarray) -> np.ndarray:
    series = pd.Series(values).replace([np.inf, -np.inf], np.nan)
    series = series.fillna(series.median())
    if series.nunique(dropna=True) <= 1:
        return np.full(len(series), 0.5)
    return series.rank(pct=True).to_numpy(dtype=float)


def direction_alignment(delta: np.ndarray, prob_up: np.ndarray) -> np.ndarray:
    expected = np.where(prob_up >= 0.5, 1.0, -1.0)
    return (np.sign(delta) == expected).astype(float)


def confidence_weight(prob_up: np.ndarray, threshold: float) -> np.ndarray:
    confidence = np.abs(prob_up - 0.5) * 2.0
    return np.clip((confidence - threshold) / max(1e-9, 1.0 - threshold), 0.0, 1.0)


def row_risk(frame: pd.DataFrame, source: np.ndarray, target: np.ndarray) -> np.ndarray:
    qwidth = rank01(pd.to_numeric(frame["quantile_width"], errors="coerce"))
    price_range = rank01(pd.to_numeric(frame["l10_price_range_ratio"], errors="coerce"))
    spread = rank01(pd.to_numeric(frame["component_prediction_spread"], errors="coerce"))
    model_gap = rank01(np.abs(target - source))
    low_conf = frame["confidence_tier"].astype(str).str.contains("low", case=False, na=False).astype(float).to_numpy()
    svc = pd.to_numeric(frame["svc_group_n"], errors="coerce").fillna(0).to_numpy(dtype=float)
    low_sample = np.clip((10.0 - svc) / 10.0, 0.0, 1.0)
    return np.clip(
        0.25 * qwidth
        + 0.20 * price_range
        + 0.20 * spread
        + 0.18 * model_gap
        + 0.09 * low_conf
        + 0.08 * low_sample,
        0.0,
        1.0,
    )


def calculate_pp258_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    source = pd.to_numeric(out["pp252_log"], errors="coerce").to_numpy(dtype=float)
    stability_target = pd.to_numeric(out["pp252_stability_log"], errors="coerce").to_numpy(dtype=float)
    prob_up = pd.to_numeric(out["prob_hist35_pp252"], errors="coerce").to_numpy(dtype=float)
    residual = pd.to_numeric(out["resid_huber_pp252"], errors="coerce").to_numpy(dtype=float)

    direction_confidence = np.abs(prob_up - 0.5) * 2.0
    apply_confidence = confidence_weight(prob_up, MODEL_PARAMS["direction_confidence_threshold"])
    residual_direction_match = direction_alignment(residual, prob_up)
    stability_delta = stability_target - source
    stability_direction_match = direction_alignment(stability_delta, prob_up)

    raw_correction = (
        residual
        * residual_direction_match
        * apply_confidence
        * MODEL_PARAMS["huber_residual_strength"]
    )
    raw_correction += (
        stability_delta
        * stability_direction_match
        * apply_confidence
        * MODEL_PARAMS["stability_target_strength"]
    )

    q_rank = rank01(pd.to_numeric(out["quantile_width"], errors="coerce"))
    risk = row_risk(out, source, stability_target)
    directional_base_cap = np.where(
        raw_correction >= 0.0,
        MODEL_PARAMS["positive_log_cap"],
        MODEL_PARAMS["negative_log_cap"],
    )
    applied_cap = directional_base_cap
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["quantile_width_shrink"] * q_rank)
    applied_cap = applied_cap * (1.0 - MODEL_PARAMS["row_risk_shrink"] * np.clip(risk, 0.0, 1.0))
    applied_cap = np.clip(applied_cap, MODEL_PARAMS["minimum_log_cap"], directional_base_cap)
    applied_correction = np.minimum(np.maximum(raw_correction, -applied_cap), applied_cap)
    final_log = source + applied_correction

    out["direction_confidence"] = direction_confidence
    out["apply_confidence"] = apply_confidence
    out["residual_direction_match"] = residual_direction_match
    out["raw_correction_log"] = raw_correction
    out["uncertainty_rank"] = q_rank
    out["row_risk"] = risk
    out["directional_base_cap_log"] = directional_base_cap
    out["applied_cap_log"] = applied_cap
    out["applied_correction_log"] = applied_correction
    out["final_price_log"] = final_log
    out["final_price"] = safe_exp(final_log)
    if {"actual_price", "actual_log"}.issubset(out.columns):
        actual = pd.to_numeric(out["actual_price"], errors="coerce").to_numpy(dtype=float)
        out["absolute_percentage_error"] = np.abs(out["final_price"].to_numpy(dtype=float) - actual) / np.clip(actual, 1.0, None)
        out["log_error"] = pd.to_numeric(out["actual_log"], errors="coerce").to_numpy(dtype=float) - final_log
    return out


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    valid = (
        pd.to_numeric(frame["actual_price"], errors="coerce").gt(0)
        & pd.to_numeric(frame["actual_log"], errors="coerce").notna()
        & pd.to_numeric(frame["final_price_log"], errors="coerce").notna()
    )
    subset = frame.loc[valid].copy()
    ape = pd.to_numeric(subset["absolute_percentage_error"], errors="coerce").to_numpy(dtype=float)
    log_error = pd.to_numeric(subset["log_error"], errors="coerce").to_numpy(dtype=float)
    return {
        "n": int(valid.sum()),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15": float(np.nanmean(ape <= 0.15)),
        "within_30": float(np.nanmean(ape <= 0.30)),
        "within_50": float(np.nanmean(ape <= 0.50)),
        "over_50pct_error_rate": float(np.nanmean(ape > 0.50)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Package root. Defaults to parent of this script.")
    parser.add_argument("--input", default="data/pp258_model_input_validation_test.csv")
    parser.add_argument("--split", default="test", choices=["test", "validation_oof", "all"])
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(root / args.input, low_memory=False)
    predictions = calculate_pp258_predictions(frame)
    if args.split == "all":
        evaluated = predictions
    else:
        evaluated = predictions[predictions["eval_split"].eq(args.split)].copy()
    result_metrics = metrics(evaluated)

    evaluated.to_csv(output_dir / f"pp258_{args.split}_predictions.csv", index=False)
    pd.DataFrame([result_metrics]).to_csv(output_dir / f"pp258_{args.split}_metrics.csv", index=False)
    (output_dir / f"pp258_{args.split}_metrics.json").write_text(
        json.dumps(
            {
                "split": args.split,
                "model_params": MODEL_PARAMS,
                "metrics": result_metrics,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Warm PP258 최종 운영 모델 재현 결과")
    print(f"- split: {args.split}")
    print(f"- rows: {result_metrics['n']}")
    print(f"- MdAPE: {result_metrics['MdAPE']:.6f}")
    print(f"- MAPE: {result_metrics['MAPE']:.6f}")
    print(f"- p95_APE: {result_metrics['p95_APE']:.6f}")
    print(f"- RMSE_log: {result_metrics['RMSE_log']:.6f}")
    print(f"- output: {output_dir}")


if __name__ == "__main__":
    main()
'''
    script_path = SCRIPT_DIR / "pp258_reproduce_fixed_test.py"
    script_path.write_text(content, encoding="utf-8")
    script_path.chmod(0o755)


def write_docs(config: dict[str, Any], test_metrics: dict[str, Any], validation_metrics: dict[str, Any]) -> None:
    readme = f"""# Warm PP258 최종 운영 모델 제출용 재현 패키지

작성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이 패키지는 `Warm 가격 예측 최종 운영 모델 상세 리포트`에 나온 PP258 최종 운영 모델을 fixed test 기준으로 재현하기 위한 제출 후보 패키지다.

## 중요한 전제

- 이 패키지는 제출용 고신뢰 100건 MAPE 15% 실험이 아니다.
- 이 패키지는 현재 리포트 모델의 기존 Warm fixed test 607건 기준 재현 패키지다.
- raw 작품 정보만 넣어 처음부터 Warm 후보 전체를 생성하는 API형 패키지가 아니다.
- 입력 CSV에는 최종 PP258 미세 보정에 필요한 선행 Warm 로그가격과 보정 신호가 이미 포함되어 있다.

## 실행 방법

```bash
pip install -r requirements.txt
python scripts/pp258_reproduce_fixed_test.py
```

기본 실행은 `data/pp258_model_input_validation_test.csv`를 읽고 `test` split 607건을 평가한다.

## 포함 파일

- `data/pp258_model_input_validation_test.csv`: validation/test 전체 1,126건 재현 입력
- `data/pp258_fixed_test_features.csv`: fixed test 607건 feature-only 입력
- `data/pp258_fixed_test_labels.csv`: fixed test 607건 label
- `scripts/pp258_reproduce_fixed_test.py`: PP258 최종 산식 재현 스크립트
- `outputs/pp258_test_predictions.csv`: fixed test 예측 결과
- `outputs/pp258_test_metrics.json`: fixed test 성능 지표
- `artifacts/model_config.json`: 모델 파라미터와 원 실험 정보
- `reports/`: 상세 리포트와 설명 자료

## 모델 공식 요약

```text
최종로그가격 = 미세보정전_기준로그가격 + 최종보정_적용값

최종보정_원시값
  = 0.025
    * Huber잔차예측값
    * 잔차방향일치여부
    * 적용확신도

최종보정_적용값
  = clip(최종보정_원시값, -row별_보정상한, +row별_보정상한)

최종가격 = exp(최종로그가격)
```

## fixed test 607건 재현 결과

| 지표 | 값 |
|---|---:|
| n | {test_metrics['n']} |
| MdAPE | {test_metrics['MdAPE']:.6f} |
| MAPE | {test_metrics['MAPE']:.6f} |
| p95 APE | {test_metrics['p95_APE']:.6f} |
| RMSE log | {test_metrics['RMSE_log']:.6f} |

## validation OOF 519건 참고 결과

| 지표 | 값 |
|---|---:|
| n | {validation_metrics['n']} |
| MdAPE | {validation_metrics['MdAPE']:.6f} |
| MAPE | {validation_metrics['MAPE']:.6f} |
| p95 APE | {validation_metrics['p95_APE']:.6f} |
| RMSE log | {validation_metrics['RMSE_log']:.6f} |

## 원 실험 후보

- experiment: `{config['experiment_slug']}`
- selected candidate: `{config['selection_decision']['operational_candidate']}`
- selected protocol: `{config['selection_decision']['operational_protocol_candidate']}`
"""
    (TARGET_EXP / "README.md").write_text(readme, encoding="utf-8")
    (TARGET_EXP / "requirements.txt").write_text("numpy\npandas\n", encoding="utf-8")

    model_config = {
        "package_created_at": datetime.now().isoformat(timespec="seconds"),
        "package_type": "fixed_test_reproduction_submission_candidate",
        "source_experiment": str(SOURCE_EXP.relative_to(REPO)),
        "selected_candidate": config["selection_decision"]["operational_candidate"],
        "selected_protocol_candidate": config["selection_decision"]["operational_protocol_candidate"],
        "model_params": MODEL_PARAMS,
        "test_metrics": test_metrics,
        "validation_oof_metrics": validation_metrics,
        "scope_note": "This package reproduces the report model on the existing Warm fixed test split. It is not a raw blind-test inference API package.",
    }
    (ARTIFACT_DIR / "model_config.json").write_text(json.dumps(model_config, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_reports() -> None:
    report_names = [
        "warm_pp258_selected_model_detailed_report.md",
        "warm_pp258_selected_model_detailed_report.html",
        "warm_pp258_boss_briefing_guide.md",
        "warm_pp258_boss_briefing_guide.html",
        "warm_pp258_concept_deep_dive_for_briefing.md",
        "warm_pp258_concept_deep_dive_for_briefing.html",
    ]
    for name in report_names:
        src = SOURCE_REPORTS / name
        if src.exists():
            shutil.copy2(src, REPORT_DIR / name)


def write_zip() -> Path:
    zip_path = PACKAGE_DIR / "Warm_PP258_operational_fixed_test_submission.zip"
    if zip_path.exists():
        zip_path.unlink()
    include_dirs = ["data", "scripts", "outputs", "reports", "artifacts"]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in ["README.md", "requirements.txt"]:
            path = TARGET_EXP / filename
            zf.write(path, arcname=f"Warm_PP258_operational_fixed_test_submission/{filename}")
        for dirname in include_dirs:
            root = TARGET_EXP / dirname
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, arcname=f"Warm_PP258_operational_fixed_test_submission/{path.relative_to(TARGET_EXP)}")
    return zip_path


def main() -> None:
    ensure_dirs()
    frame, config = load_submission_frame()
    calculated = calculate_pp258_predictions(frame)
    source_diff = float(np.nanmax(np.abs(calculated["final_price_log"].to_numpy(dtype=float) - calculated["pred_log"].to_numpy(dtype=float))))
    if source_diff > 1e-10:
        raise RuntimeError(f"PP258 formula reproduction mismatch: max log diff={source_diff}")

    input_cols = [
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
        "pp252_log",
        "pp252_stability_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
        "quantile_width",
        "l10_price_range_ratio",
        "svc_group_n",
        "component_prediction_spread",
        "current_vs_stable_gap_abs",
    ]
    frame[input_cols].to_csv(DATA_DIR / "pp258_model_input_validation_test.csv", index=False)

    test_input = frame[frame["eval_split"].eq("test")].copy()
    feature_cols = [col for col in input_cols if col not in {"actual_log", "actual_price"}]
    test_input[feature_cols].to_csv(DATA_DIR / "pp258_fixed_test_features.csv", index=False)
    test_input[["eval_split", "_track6_row_id", "actual_log", "actual_price"]].to_csv(DATA_DIR / "pp258_fixed_test_labels.csv", index=False)

    predictions_cols = [
        "eval_split",
        "_track6_row_id",
        "artist_key",
        "artist_name_ko",
        "actual_log",
        "actual_price",
        "pp252_log",
        "prob_hist35_pp252",
        "resid_huber_pp252",
        "direction_confidence",
        "apply_confidence",
        "residual_direction_match",
        "raw_correction_log",
        "row_risk",
        "applied_cap_log",
        "applied_correction_log",
        "final_price_log",
        "final_price",
        "absolute_percentage_error",
        "log_error",
    ]
    calculated[calculated["eval_split"].eq("test")][predictions_cols].to_csv(OUTPUT_DIR / "pp258_test_predictions.csv", index=False)
    calculated[calculated["eval_split"].eq("validation_oof")][predictions_cols].to_csv(OUTPUT_DIR / "pp258_validation_oof_predictions.csv", index=False)

    test_metrics = metrics(calculated[calculated["eval_split"].eq("test")])
    validation_metrics = metrics(calculated[calculated["eval_split"].eq("validation_oof")])
    pd.DataFrame([test_metrics]).to_csv(OUTPUT_DIR / "pp258_test_metrics.csv", index=False)
    (OUTPUT_DIR / "pp258_test_metrics.json").write_text(json.dumps({"metrics": test_metrics}, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([validation_metrics]).to_csv(OUTPUT_DIR / "pp258_validation_oof_metrics.csv", index=False)
    (OUTPUT_DIR / "pp258_validation_oof_metrics.json").write_text(json.dumps({"metrics": validation_metrics}, ensure_ascii=False, indent=2), encoding="utf-8")

    write_reproduction_script()
    copy_reports()
    write_docs(config, test_metrics, validation_metrics)
    zip_path = write_zip()

    print("Warm PP258 submission-style package built")
    print(f"- package root: {TARGET_EXP}")
    print(f"- zip: {zip_path}")
    print(f"- source reproduction max log diff: {source_diff:.3e}")
    print(f"- test MAPE: {test_metrics['MAPE']:.9f}")
    print(f"- test p95_APE: {test_metrics['p95_APE']:.9f}")


if __name__ == "__main__":
    main()
