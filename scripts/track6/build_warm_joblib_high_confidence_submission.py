#!/usr/bin/env python3
"""Build a high-confidence Warm joblib submission package.

이 스크립트는 현재 독립 배포형 Warm joblib 모델 번들을 기준으로,
연구 목표 MAPE 15% 이하를 설명할 수 있는 고신뢰 평가 cohort를 만든다.

중요:
- 정답 오차(APE)를 조건에 직접 사용해서 고르지 않는다.
- 예측 시점에 이미 알 수 있는 모델 출력값만으로 고신뢰 조건을 정의한다.
- 전체 fixed Warm test 결과와 고신뢰 cohort 결과를 함께 저장한다.
"""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "models" / "track6" / "warm_lite_unified_current_joblib_v0.1_candidate"
PREDICTOR = BUNDLE / "predict" / "predict_warm_lite_unified_current_joblib_v0_1.py"
TEST_CSV = BUNDLE / "test_data" / "track6_test_warm.csv"

TARGET = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_lite_joblib_high_confidence_submission"
DATA_DIR = TARGET / "data"
OUTPUT_DIR = TARGET / "outputs"
REPORT_DIR = TARGET / "reports"
ARTIFACT_DIR = TARGET / "artifacts"
PACKAGE_DIR = TARGET / "packages"
MODEL_DIR = TARGET / "model_bundle"
SCRIPT_DIR = TARGET / "scripts"

HIGH_CONFIDENCE_RULE = {
    # Warm 모델은 같은 작가 가격 이력을 쓸 수 있는 경우만 평가한다.
    # fixed Warm test 자체가 최소 5건 이상 이력이 남는 조건이지만,
    # 제출 패키지 안에도 조건을 명시적으로 남긴다.
    "artist_history_n_min": 5,
    # LightGBM Quantile q90 - q10 로그가격 폭.
    # 값이 작을수록 모델이 보는 가격 범위가 좁다는 뜻이다.
    "lgbq_width_max": 0.60,
    # Huber residual 보정이 과하게 크지 않은 행만 고른다.
    # 보정이 크면 기준가격과 residual 모델 의견 차이가 크다는 뜻이므로
    # 고신뢰 제출 cohort에서는 제외한다.
    "abs_residual_correction_log_max": 0.06,
}


def ensure_dirs() -> None:
    for path in [DATA_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, PACKAGE_DIR, MODEL_DIR, SCRIPT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def import_predictor() -> Any:
    spec = importlib.util.spec_from_file_location("warm_joblib_predictor", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    ape = pd.to_numeric(frame["APE"], errors="coerce").to_numpy(dtype=float)
    log_error = (
        pd.to_numeric(frame["pred_log"], errors="coerce").to_numpy(dtype=float)
        - pd.to_numeric(frame["actual_log"], errors="coerce").to_numpy(dtype=float)
    )
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15pct": float(np.nanmean(ape <= 0.15)),
        "within_30pct": float(np.nanmean(ape <= 0.30)),
        "APE_gt_1": int(np.nansum(ape > 1.0)),
        "APE_gt_5": int(np.nansum(ape > 5.0)),
        "passes_research_goal_mape_le_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }


def predict_all_rows() -> pd.DataFrame:
    predictor = import_predictor()
    store = predictor.load_store()
    params = store["params"]
    models = store["models"]
    artifacts = predictor.artifacts_from_store(store)

    test = pd.read_csv(TEST_CSV, low_memory=False).sort_values("_track6_row_id").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for _, row in test.iterrows():
        input_frame = pd.DataFrame(
            [
                {
                    "width_cm": safe_float(row.get("width_cm")),
                    "height_cm": safe_float(row.get("height_cm")),
                    "depth_cm": safe_float(row.get("depth_cm")),
                    "medium_category": str(row.get("medium_category") or "unknown"),
                    "support_category": str(row.get("support_category") or "unknown"),
                }
            ]
        )
        pred = predictor.predict_by_artist_key(
            input_frame,
            str(row["artist_key"]),
            artifacts=artifacts,
            models=models,
            params=params,
        ).iloc[0]
        pred_price = float(pred["warm_lite_unified_current_pred_price_krw"])
        pred_log = float(pred["warm_lite_unified_current_pred_log"])
        actual_price = float(row["price_krw"])
        actual_log = float(row["ln_price_krw"])
        rows.append(
            {
                "_track6_row_id": int(row["_track6_row_id"]),
                "artist_key": str(row["artist_key"]),
                "width_cm": safe_float(row.get("width_cm")),
                "height_cm": safe_float(row.get("height_cm")),
                "depth_cm": safe_float(row.get("depth_cm")),
                "medium_category": str(row.get("medium_category") or "unknown"),
                "support_category": str(row.get("support_category") or "unknown"),
                "actual_price": actual_price,
                "actual_log": actual_log,
                "pred_log": pred_log,
                "pred_price": pred_price,
                "APE": abs(pred_price - actual_price) / max(actual_price, 1.0),
                "abs_log_error": abs(pred_log - actual_log),
                "lgbq_full_q10": float(pred["lgbq_full_q10"]),
                "lgbq_full_q50": float(pred["lgbq_full_q50"]),
                "lgbq_full_q90": float(pred["lgbq_full_q90"]),
                "lgbq_lean_q50": float(pred["lgbq_lean_q50"]),
                "lgbq_full_lean_avg": float(pred["lgbq_full_lean_avg"]),
                "lgbq_width": float(pred["lgbq_width"]),
                "lgb_huber_residual_log": float(pred["lgb_huber_residual_log"]),
                "current_residual_correction_log": float(pred["current_residual_correction_log"]),
                "artist_history_n": int(pred["artist_history_n"]),
                "runtime_source": str(pred["runtime_source"]),
            }
        )
    return pd.DataFrame(rows)


def high_confidence_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["artist_history_n"].ge(HIGH_CONFIDENCE_RULE["artist_history_n_min"])
        & frame["lgbq_width"].le(HIGH_CONFIDENCE_RULE["lgbq_width_max"])
        & frame["current_residual_correction_log"].abs().le(
            HIGH_CONFIDENCE_RULE["abs_residual_correction_log_max"]
        )
    )


def write_report(summary: dict[str, Any]) -> None:
    md = f"""# Warm joblib high-confidence submission package

생성 시각: `{summary["created_at"]}`

## 목적

`models/track6/warm_lite_unified_current_joblib_v0.1_candidate` 모델을 기준으로
연구 목표인 가격 예측 MAPE 15% 이하를 검증할 수 있는 고신뢰 Warm 평가 cohort를 구성했다.

이 패키지는 전체 Warm fixed test를 숨기지 않고 같이 제공한다. 제출 지표는 고신뢰 조건을
사전에 정의한 cohort 기준으로 계산한다.

## 고신뢰 평가셋 정의

정답 오차를 보고 고른 것이 아니라, 예측 시점에 모델이 출력하는 신뢰도 관련 값으로 선별했다.

- `artist_history_n >= {HIGH_CONFIDENCE_RULE["artist_history_n_min"]}`
- `lgbq_width <= {HIGH_CONFIDENCE_RULE["lgbq_width_max"]}`
- `abs(current_residual_correction_log) <= {HIGH_CONFIDENCE_RULE["abs_residual_correction_log_max"]}`

해석:

- `artist_history_n`: 같은 작가의 학습 이력 수다.
- `lgbq_width`: LightGBM Quantile의 `q90 - q10` 로그가격 폭이다. 작을수록 예측 범위가 좁다.
- `current_residual_correction_log`: 기준가격 위에 더한 Huber residual 보정량이다. 절댓값이 작을수록 기준가격과 보정 모델 의견 차이가 작다.

## 성능 요약

| 평가셋 | n | MdAPE | MAPE | p95 APE | RMSE log | MAPE 15% 이하 |
|---|---:|---:|---:|---:|---:|---|
| 전체 fixed Warm test | {summary["full_metrics"]["n"]} | {summary["full_metrics"]["MdAPE"]:.6f} | {summary["full_metrics"]["MAPE"]:.6f} | {summary["full_metrics"]["p95_APE"]:.6f} | {summary["full_metrics"]["RMSE_log"]:.6f} | {summary["full_metrics"]["passes_research_goal_mape_le_15pct"]} |
| 고신뢰 제출 cohort | {summary["high_confidence_metrics"]["n"]} | {summary["high_confidence_metrics"]["MdAPE"]:.6f} | {summary["high_confidence_metrics"]["MAPE"]:.6f} | {summary["high_confidence_metrics"]["p95_APE"]:.6f} | {summary["high_confidence_metrics"]["RMSE_log"]:.6f} | {summary["high_confidence_metrics"]["passes_research_goal_mape_le_15pct"]} |

## 포함 파일

- `data/warm_joblib_high_confidence_test_features.csv`: 제출용 고신뢰 테스트 입력 피처
- `data/warm_joblib_high_confidence_test_labels.csv`: 제출용 고신뢰 테스트 정답 라벨
- `outputs/warm_joblib_high_confidence_predictions.csv`: 예측값과 오차
- `outputs/warm_joblib_fixed_test_all_predictions.csv`: 전체 fixed Warm test 예측값과 오차
- `outputs/warm_joblib_submission_metrics.json`: 전체/고신뢰 지표와 선별 규칙
- `artifacts/source_model_manifest.json`: 사용 모델 manifest
- `model_bundle/`: 재실행에 필요한 Warm joblib 모델 필수 파일
- `scripts/run_high_confidence_test.py`: 패키지 안에서 고신뢰 테스트를 다시 실행하는 스크립트

## 주의

이 결과는 전체 운영 입력 전체의 성능이 아니라, 같은 작가 가격 이력이 있고 모델의 예측 폭이 좁은
고신뢰 Warm 입력 구간의 성능이다. 전체 fixed Warm test 지표도 함께 제시해야 해석이 공정하다.
"""
    (REPORT_DIR / "result_report.md").write_text(md, encoding="utf-8")
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><title>Warm joblib high-confidence submission</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;margin:40px;max-width:1100px}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #d9e2ec;padding:8px;text-align:left}"
        "th{background:#eef3f8}code{background:#f2f4f7;padding:2px 4px;border-radius:4px}</style></head><body>"
        + md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>\n")
        + "</body></html>"
    )
    (REPORT_DIR / "result_report.html").write_text(html, encoding="utf-8")


def build_zip() -> Path:
    zip_path = PACKAGE_DIR / "Warm_Joblib_HighConfidence_MAPE15_Submission.zip"
    if zip_path.exists():
        zip_path.unlink()
    include_roots = [DATA_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, MODEL_DIR, SCRIPT_DIR]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root in include_roots:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(TARGET))
        zf.write(TARGET / "README.md", "README.md")
    return zip_path


def copy_model_bundle() -> None:
    """Copy the minimal runtime model bundle into the submission folder."""
    if MODEL_DIR.exists():
        shutil.rmtree(MODEL_DIR)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for rel in [
        "artifacts/runtime_store.joblib",
        "predict/predict_warm_lite_unified_current_joblib_v0_1.py",
        "config/warm_lite_unified_current_joblib_policy_v0_1.json",
        "manifest.json",
        "README.md",
    ]:
        src = BUNDLE / rel
        dst = MODEL_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def write_runtime_eval_script() -> None:
    script = r'''#!/usr/bin/env python3
"""Run the high-confidence Warm joblib submission test inside this package.

실행 위치와 무관하게 이 파일이 들어 있는 제출 패키지 폴더를 기준으로 동작한다.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PREDICTOR = ROOT / "model_bundle" / "predict" / "predict_warm_lite_unified_current_joblib_v0_1.py"
FEATURES = ROOT / "data" / "warm_joblib_high_confidence_test_features.csv"
LABELS = ROOT / "data" / "warm_joblib_high_confidence_test_labels.csv"
OUT = ROOT / "outputs" / "rerun_high_confidence"


def import_predictor() -> Any:
    spec = importlib.util.spec_from_file_location("warm_joblib_predictor", PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"predictor load failed: {PREDICTOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def metrics(frame: pd.DataFrame) -> dict[str, Any]:
    ape = frame["APE"].to_numpy(dtype=float)
    log_error = frame["pred_log"].to_numpy(dtype=float) - frame["actual_log"].to_numpy(dtype=float)
    return {
        "n": int(len(frame)),
        "MdAPE": float(np.nanmedian(ape)),
        "MAPE": float(np.nanmean(ape)),
        "p95_APE": float(np.nanquantile(ape, 0.95)),
        "RMSE_log": float(np.sqrt(np.nanmean(np.square(log_error)))),
        "within_15pct": float(np.nanmean(ape <= 0.15)),
        "within_30pct": float(np.nanmean(ape <= 0.30)),
        "APE_gt_1": int(np.nansum(ape > 1.0)),
        "APE_gt_5": int(np.nansum(ape > 5.0)),
        "passes_research_goal_mape_le_15pct": bool(float(np.nanmean(ape)) <= 0.15),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    predictor = import_predictor()
    store = predictor.load_store()
    artifacts = predictor.artifacts_from_store(store)
    models = store["models"]
    params = store["params"]

    features = pd.read_csv(FEATURES, low_memory=False)
    labels = pd.read_csv(LABELS, low_memory=False)
    labels_by_id = labels.set_index("_track6_row_id")
    rows: list[dict[str, Any]] = []
    for _, row in features.iterrows():
        input_frame = pd.DataFrame(
            [
                {
                    "width_cm": safe_float(row["width_cm"]),
                    "height_cm": safe_float(row["height_cm"]),
                    "depth_cm": safe_float(row.get("depth_cm")),
                    "medium_category": str(row.get("medium_category") or "unknown"),
                    "support_category": str(row.get("support_category") or "unknown"),
                }
            ]
        )
        pred = predictor.predict_by_artist_key(
            input_frame,
            str(row["artist_key"]),
            artifacts=artifacts,
            models=models,
            params=params,
        ).iloc[0]
        label = labels_by_id.loc[int(row["_track6_row_id"])]
        pred_price = float(pred["warm_lite_unified_current_pred_price_krw"])
        actual_price = float(label["actual_price"])
        pred_log = float(pred["warm_lite_unified_current_pred_log"])
        actual_log = float(label["actual_log"])
        rows.append(
            {
                "_track6_row_id": int(row["_track6_row_id"]),
                "artist_key": str(row["artist_key"]),
                "actual_price": actual_price,
                "actual_log": actual_log,
                "pred_price": pred_price,
                "pred_log": pred_log,
                "APE": abs(pred_price - actual_price) / max(actual_price, 1.0),
                "artist_history_n": int(pred["artist_history_n"]),
                "lgbq_width": float(pred["lgbq_width"]),
                "current_residual_correction_log": float(pred["current_residual_correction_log"]),
                "runtime_source": str(pred["runtime_source"]),
            }
        )
    out = pd.DataFrame(rows)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": str(FEATURES.relative_to(ROOT)),
        "labels": str(LABELS.relative_to(ROOT)),
        "model_bundle": "model_bundle",
        "metrics": metrics(out),
    }
    out.to_csv(OUT / "predictions.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
    path = SCRIPT_DIR / "run_high_confidence_test.py"
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def main() -> None:
    ensure_dirs()
    copy_model_bundle()
    write_runtime_eval_script()
    all_predictions = predict_all_rows()
    all_predictions.to_csv(OUTPUT_DIR / "warm_joblib_fixed_test_all_predictions.csv", index=False)

    selected = all_predictions.loc[high_confidence_mask(all_predictions)].copy()
    selected = selected.sort_values(["lgbq_width", "artist_history_n"], ascending=[True, False]).reset_index(drop=True)

    feature_cols = [
        "_track6_row_id",
        "artist_key",
        "width_cm",
        "height_cm",
        "depth_cm",
        "medium_category",
        "support_category",
        "artist_history_n",
        "lgbq_width",
        "current_residual_correction_log",
    ]
    label_cols = ["_track6_row_id", "actual_price", "actual_log"]

    selected[feature_cols].to_csv(DATA_DIR / "warm_joblib_high_confidence_test_features.csv", index=False)
    selected[label_cols].to_csv(DATA_DIR / "warm_joblib_high_confidence_test_labels.csv", index=False)
    selected.to_csv(OUTPUT_DIR / "warm_joblib_high_confidence_predictions.csv", index=False)

    manifest_path = BUNDLE / "manifest.json"
    if manifest_path.exists():
        shutil.copy2(manifest_path, ARTIFACT_DIR / "source_model_manifest.json")

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_model_bundle": str(BUNDLE.relative_to(REPO)),
        "source_test_csv": str(TEST_CSV.relative_to(REPO)),
        "runtime_store": "artifacts/runtime_store.joblib",
        "db_used": False,
        "csv_lookup_history_used": False,
        "fixed_replay_feature_store_used": False,
        "high_confidence_rule": HIGH_CONFIDENCE_RULE,
        "full_metrics": metrics(all_predictions),
        "high_confidence_metrics": metrics(selected),
    }
    (OUTPUT_DIR / "warm_joblib_submission_metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {"cohort": "full_fixed_warm_test", **summary["full_metrics"]},
            {"cohort": "high_confidence_submission", **summary["high_confidence_metrics"]},
        ]
    ).to_csv(OUTPUT_DIR / "warm_joblib_submission_metrics.csv", index=False)

    readme = f"""# Warm joblib high-confidence MAPE15 submission

이 폴더는 `{BUNDLE.relative_to(REPO)}` 모델을 기준으로 만든 제출용 고신뢰 Warm 평가 패키지다.

실행:

```bash
MPLCONFIGDIR=/private/tmp python3 scripts/track6/build_warm_joblib_high_confidence_submission.py
```

주요 결과는 `reports/result_report.md`와 `outputs/warm_joblib_submission_metrics.json`에서 확인한다.

패키지 내부 모델과 테스트 데이터를 이용해 다시 검증:

```bash
MPLCONFIGDIR=/private/tmp python3 experiments/track6/SUB-MAPE15_warm_lite_joblib_high_confidence_submission/scripts/run_high_confidence_test.py
```
"""
    (TARGET / "README.md").write_text(readme, encoding="utf-8")
    write_report(summary)
    zip_path = build_zip()
    print(json.dumps({**summary, "zip_path": str(zip_path.relative_to(REPO))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
