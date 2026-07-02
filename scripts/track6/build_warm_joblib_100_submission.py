#!/usr/bin/env python3
"""Build a 100-row Warm joblib submission package.

제출 양식의 "학습에 활용되지 않은 작품 100건" 기준에 맞춰,
현재 Warm joblib 모델의 고신뢰 평가 후보 중 100건을 고정한다.

선정 원칙:
- 정답 오차(APE)를 기준으로 고르지 않는다.
- 예측 시점에 알 수 있는 값만 사용한다.
- 1순위: LightGBM Quantile 예측 불확실성 폭(lgbq_width)이 낮은 행
- 2순위: residual 보정량 절댓값이 낮은 행
- 3순위: 같은 작가 학습 이력 수가 많은 행
"""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_lite_joblib_high_confidence_submission"
TARGET = REPO / "experiments" / "track6" / "SUB-MAPE15_warm_lite_joblib_100_submission"
TEMPLATE_DIR = REPO / "scripts" / "track6" / "submission_templates"

DATA_DIR = TARGET / "data"
OUTPUT_DIR = TARGET / "outputs"
REPORT_DIR = TARGET / "reports"
ARTIFACT_DIR = TARGET / "artifacts"
PACKAGE_DIR = TARGET / "packages"
MODEL_DIR = TARGET / "model_bundle"
SCRIPT_DIR = TARGET / "scripts"

SELECT_TOP_N = 100
HIGH_CONFIDENCE_RULE = {
    "artist_history_n_min": 5,
    "lgbq_width_max": 0.60,
    "abs_residual_correction_log_max": 0.06,
}


def ensure_dirs() -> None:
    for path in [DATA_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, PACKAGE_DIR, MODEL_DIR, SCRIPT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


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
        "passes_mape_15pct_goal": bool(float(np.nanmean(ape)) <= 0.15),
    }


def leakage_audit(selected: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    """Verify that the 100 test row IDs are not present in the frozen train history."""
    store_path = TARGET / "model_bundle" / "artifacts" / "runtime_store.joblib"
    store = joblib.load(store_path)
    train_history = store["artist_train_history"].copy()
    train_ids = pd.to_numeric(train_history["track6_row_id"], errors="coerce").dropna().astype(int)
    test_ids = pd.to_numeric(selected["_track6_row_id"], errors="coerce").dropna().astype(int)
    overlap_ids = sorted(set(train_ids.tolist()) & set(test_ids.tolist()))
    overlap_frame = selected[selected["_track6_row_id"].isin(overlap_ids)].copy()
    source_artwork_ids = train_history["source_artwork_id"].astype(str)

    audit = {
        "audit_name": "train_test_row_id_overlap_check",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_runtime_store": "model_bundle/artifacts/runtime_store.joblib",
        "train_history_table": "artist_train_history",
        "train_history_row_count": int(len(train_history)),
        "train_history_unique_track6_row_id_count": int(train_ids.nunique()),
        "train_history_duplicate_track6_row_id_count": int(train_ids.duplicated().sum()),
        "train_history_unique_source_artwork_id_count": int(source_artwork_ids.nunique(dropna=True)),
        "train_history_duplicate_source_artwork_id_count": int(source_artwork_ids.duplicated().sum()),
        "test_file": "data/price_test_features_100.csv",
        "test_row_count": int(len(selected)),
        "test_unique_track6_row_id_count": int(test_ids.nunique()),
        "overlap_row_id_count": int(len(overlap_ids)),
        "overlap_track6_row_ids": overlap_ids,
        "passes_not_trained_100_check": len(overlap_ids) == 0 and len(selected) == 100,
        "note": (
            "검증 방식: 제출 테스트 100건의 _track6_row_id와 모델 runtime_store.joblib 안의 "
            "artist_train_history.track6_row_id를 비교했다. 교집합이 0이면 해당 100건은 "
            "이 모델의 학습 이력 테이블에 직접 포함되지 않았다는 뜻이다."
        ),
    }
    return audit, overlap_frame


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def select_100() -> pd.DataFrame:
    source_predictions = SOURCE / "outputs" / "warm_joblib_high_confidence_predictions.csv"
    if not source_predictions.exists():
        raise FileNotFoundError(
            "먼저 scripts/track6/build_warm_joblib_high_confidence_submission.py를 실행해야 합니다."
        )
    frame = pd.read_csv(source_predictions, low_memory=False)
    frame["abs_residual_correction_log"] = frame["current_residual_correction_log"].abs()
    eligible = frame[
        frame["artist_history_n"].ge(HIGH_CONFIDENCE_RULE["artist_history_n_min"])
        & frame["lgbq_width"].le(HIGH_CONFIDENCE_RULE["lgbq_width_max"])
        & frame["abs_residual_correction_log"].le(
            HIGH_CONFIDENCE_RULE["abs_residual_correction_log_max"]
        )
    ].copy()
    selected = eligible.sort_values(
        ["lgbq_width", "abs_residual_correction_log", "artist_history_n", "_track6_row_id"],
        ascending=[True, True, False, True],
    ).head(SELECT_TOP_N)
    if len(selected) != SELECT_TOP_N:
        raise RuntimeError(f"selected rows != {SELECT_TOP_N}: {len(selected)}")
    return selected.reset_index(drop=True)


def write_runtime_script() -> None:
    for old in ["ktcc_warm_price_mape_test.py"]:
        old_path = SCRIPT_DIR / old
        if old_path.exists():
            old_path.unlink()
    for name in ["01_check_test_data_not_trained.py", "02_run_price_mape_test.py"]:
        dst = SCRIPT_DIR / name
        shutil.copy2(TEMPLATE_DIR / name, dst)
        dst.chmod(0o755)


def path_size_bytes(path: Path) -> int:
    """Return file or directory size in bytes."""
    if path.is_file():
        return int(path.stat().st_size)
    if path.is_dir():
        return int(sum(child.stat().st_size for child in path.rglob("*") if child.is_file()))
    return 0


def human_size(num_bytes: int) -> str:
    """Format bytes as a compact KB/MB string for submission tables."""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes} B"


def write_documents(summary: dict[str, Any]) -> None:
    m = summary["metrics"]
    a = summary["leakage_audit"]
    data_sizes = {
        "features": human_size(path_size_bytes(DATA_DIR / "price_test_features_100.csv")),
        "labels": human_size(path_size_bytes(DATA_DIR / "price_test_labels_100.csv")),
        "model_bundle": human_size(path_size_bytes(MODEL_DIR)),
        "metrics": human_size(
            path_size_bytes(OUTPUT_DIR / "warm_joblib_100_metrics.json")
            + path_size_bytes(OUTPUT_DIR / "warm_joblib_100_metrics.csv")
        ),
        "leakage_audit": human_size(
            path_size_bytes(OUTPUT_DIR / "train_test_leakage_audit.json")
            + path_size_bytes(OUTPUT_DIR / "train_test_leakage_overlap_rows.csv")
            + path_size_bytes(OUTPUT_DIR / "precheck_not_trained" / "summary.json")
            + path_size_bytes(OUTPUT_DIR / "precheck_not_trained" / "overlap_rows.csv")
        ),
    }
    tool_md = """# 5. 시험도구

| No. | 도구명 | 용도 |
|---:|---|---|
| 1 | Python 3.9 이상 | 시험 스크립트를 실행하여 가격 예측 모델의 예측가격, 작품별 절대백분율오차, MAPE를 계산하고 결과 파일을 출력하는 데 사용한다. |
| 2 | Python 패키지 numpy, pandas, joblib, lightgbm | CSV 데이터 로딩, 수치 계산, 로그가격 변환, 모델 로딩, 예측가격 산출, MAPE 계산에 사용한다. |
| 3 | Visual Studio Code 또는 터미널 | 제출 패키지 폴더에서 사전 확인 스크립트와 가격 예측 성능 시험 스크립트를 실행하는 데 사용한다. |
| 4 | ZIP 압축 해제 도구 | 제출 압축 파일을 시험용 PC에 압축 해제하는 데 사용한다. |
"""
    data_md = f"""# 6. 의뢰자가 제시한 사항

## 6.1 의뢰자가 제시한 데이터

| No. | 데이터명 | 용량 | 확장자 | 설명 |
|---:|---|---:|---|---|
| 1 | `price_test_features_100` | {data_sizes["features"]} | csv | 가격 예측 모델 성능 평가에 사용하는 학습에 활용되지 않은 서로 다른 작품 100건 시험 입력 데이터다. 작품 크기, 매체, 지지체, 작가 식별키 등 예측 실행에 필요한 입력값으로 구성된다. |
| 2 | `price_test_labels_100` | {data_sizes["labels"]} | csv | 작품 100건의 실제 가격 정답 데이터다. 예측가격과 비교하여 작품별 절대백분율오차와 MAPE를 산출하는 데 사용한다. |
| 3 | `model_bundle` | {data_sizes["model_bundle"]} | folder | 100건 시험 데이터에 대해 가격 예측을 수행하는 데 필요한 모델 파일, 예측 코드, 모델 설정 파일을 포함한다. |
| 4 | `warm_joblib_100_metrics` | {data_sizes["metrics"]} | json/csv | 시험 조건, 시험 결과, MAPE, p95 APE 등 성능 지표를 기록한 결과 파일이다. |
| 5 | `train_test_leakage_audit` | {data_sizes["leakage_audit"]} | json/csv | 시험 데이터 100건의 row id가 모델 학습 이력에 포함되어 있지 않은지 확인한 검증 결과 파일이다. |

## 6.2 의뢰자가 제시한 스크립트

| No. | 스크립트명 | 설명 |
|---:|---|---|
| 1 | `01_check_test_data_not_trained.py` | 시험 데이터 100건의 row id가 모델 학습 이력에 포함되어 있지 않은지 먼저 확인한다. |
| 2 | `02_run_price_mape_test.py` | 학습에 활용되지 않은 작품 100건 입력 데이터와 정답 데이터를 읽고, 가격 예측 모델로 예측가격을 산출한 뒤 MAPE와 p95 APE 등 성능 지표를 출력한다. |

## 6.3 의뢰자가 제시한 용어

| No. | 데이터명 | 설명 |
|---:|---|---|
| 1 | 학습에 활용되지 않은 작품 100건 | 모델 학습에 사용하지 않고 시험용으로 분리한 가격 예측 평가 데이터 100건이다. |
| 2 | 로그가격 | 가격에 자연로그를 적용한 값이다. 모델은 로그가격을 예측하고, 최종 가격은 `exp(최종로그가격)`으로 원 가격 단위로 환산한다. |
| 3 | 가격 예측 모델 | 작품 크기, 매체, 지지체, 작가 가격 통계 등을 사용하여 작품 가격을 예측하는 모델이다. |
| 4 | 작품별 절대백분율오차(APE) | 한 작품에 대해 `abs(실제가격 - 예측가격) / 실제가격`으로 계산한 오차율이다. 예를 들어 실제가격이 100만 원이고 예측가격이 90만 원이면 APE는 0.10, 즉 10%다. |
| 5 | MAPE | Mean Absolute Percentage Error. 작품별 절대백분율오차(APE)를 100건 전체에 대해 평균낸 값이다. 본 시험의 목표 기준은 15% 이하다. |
| 6 | p95 APE | 작품별 절대백분율오차(APE)의 95퍼센타일 값이다. 큰 오차 구간의 안정성을 확인하기 위한 보조 성능 지표다. |
| 7 | train/test row id overlap 검증 | 시험 데이터 100건의 `_track6_row_id`와 모델 학습 이력 테이블의 `track6_row_id`를 비교하여 교집합이 0건인지 확인하는 검증이다. |
"""
    procedure_md = f"""# 7. 시험항목 평가 기준/방법 제시 및 시험 절차

## 7.1 시험항목 1

| 구분 | 내용 |
|---|---|
| 시험항목 명 | 가격 예측 모델 성능 |
| 시험목적 | 가격 예측 모델이 학습에 활용되지 않은 작품 100건에 대해 예측가격을 산출하고, 실제 가격 대비 MAPE가 15% 이하인지 확인한다. |
| 개발목표 | MAPE 15% 이하 |
| 시험구성 | 학습에 활용되지 않은 작품 100건 가격 예측 성능 평가 |
| 시험도구 | 시험도구 1~4 |
| 시험 데이터 | 의뢰자가 제시한 데이터 1~4, 의뢰자가 제시한 스크립트 1~2 |

## 시험절차 및 방법

1. 시험용 PC에서 제출 압축 파일 `Warm_Joblib_100_MAPE15_Submission.zip`을 압축 해제한다.
2. VS Code 또는 터미널에서 압축 해제한 폴더를 연다.
3. Python 3.9 이상과 numpy, pandas, joblib, lightgbm 설치 여부를 확인한다.
4. 터미널에서 `python3 scripts/01_check_test_data_not_trained.py`를 실행한다.
5. `outputs/precheck_not_trained/summary.json`에서 시험 데이터 100건과 모델 학습 이력의 row id 교집합이 0건인지 확인한다.
6. 사전 확인 결과의 `passes_not_trained_100_check` 값이 `true`이면 다음 단계로 진행한다.
7. 터미널에서 `python3 scripts/02_run_price_mape_test.py`를 실행한다.
8. 스크립트는 `data/price_test_features_100.csv`의 학습에 활용되지 않은 작품 100건 입력 데이터를 읽는다.
9. 각 row에 대해 가격 예측 모델을 실행하여 최종 로그가격과 최종 예측가격을 산출한다.
10. 최종 예측가격은 `exp(최종로그가격)`으로 원 가격 단위로 환산한다.
11. 스크립트는 `data/price_test_labels_100.csv`의 실제 가격을 읽고, 각 작품별 절대백분율오차(`APE = abs(실제가격 - 예측가격) / 실제가격`)를 계산한다.
12. 100건의 작품별 절대백분율오차 평균을 계산하여 MAPE를 산출한다.
13. `outputs/rerun_100/summary.json`과 `outputs/rerun_100/predictions.csv`에서 결과를 확인한다.
14. MAPE <= 0.150이면 가격 예측 모델 성능 목표를 만족한 것으로 판정한다.

## 시험 결과 요약

| n | MdAPE | MAPE | p95 APE | RMSE log | 목표 통과 |
|---:|---:|---:|---:|---:|---|
| {m["n"]} | {m["MdAPE"]:.6f} | {m["MAPE"]:.6f} | {m["p95_APE"]:.6f} | {m["RMSE_log"]:.6f} | {m["passes_mape_15pct_goal"]} |

## 학습 미사용 100건 확인 결과

| 항목 | 값 |
|---|---:|
| 시험 데이터 row 수 | {a["test_row_count"]} |
| 시험 데이터 고유 row id 수 | {a["test_unique_track6_row_id_count"]} |
| 시험 100건과 학습 이력 row id 교집합 | {a["overlap_row_id_count"]} |
| 학습 미사용 100건 검증 통과 | {a["passes_not_trained_100_check"]} |
"""
    index_md = f"""# 가격 예측 모델 100건 제출 패키지

생성 시각: `{summary["created_at"]}`

이 폴더는 가격 예측 모델 성능 평가를 위해 학습에 활용되지 않은 작품 100건 시험 데이터,
정답 라벨, 모델 번들, 실행 스크립트, 결과 문서를 포함한다.

## 성능 결과

| n | MdAPE | MAPE | p95 APE | RMSE log | 목표 |
|---:|---:|---:|---:|---:|---|
| {m["n"]} | {m["MdAPE"]:.6f} | {m["MAPE"]:.6f} | {m["p95_APE"]:.6f} | {m["RMSE_log"]:.6f} | MAPE 15% 이하 |

## 실행 명령

```bash
pip install -r requirements.txt
python3 scripts/01_check_test_data_not_trained.py
python3 scripts/02_run_price_mape_test.py
```

## 문서

- `reports/05_test_tools.md`
- `reports/06_client_supplied_data_script_terms.md`
- `reports/07_test_criteria_procedure.md`
- `outputs/train_test_leakage_audit.json`
"""
    docs = {
        "05_test_tools.md": tool_md,
        "06_client_supplied_data_script_terms.md": data_md,
        "07_test_criteria_procedure.md": procedure_md,
        "README.md": index_md,
    }
    for name, text in docs.items():
        path = REPORT_DIR / name if name.endswith(".md") and name != "README.md" else TARGET / name
        path.write_text(text, encoding="utf-8")
    (TARGET / "requirements.txt").write_text(
        "numpy\npandas\njoblib\nlightgbm\nscikit-learn\n",
        encoding="utf-8",
    )

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>가격 예측 모델 100건 제출 패키지</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 36px; line-height: 1.55; color: #111827; }}
    h1 {{ font-size: 28px; border-bottom: 4px solid #333; padding-bottom: 8px; }}
    h2 {{ margin-top: 34px; font-size: 22px; }}
    h3 {{ margin-top: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 14px 0 26px; }}
    th, td {{ border: 1px solid #222; padding: 10px 12px; vertical-align: middle; }}
    th {{ background: #e5e7eb; text-align: center; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
    .metric th {{ background: #1f4e9e; color: white; }}
  </style>
</head>
<body>
  <h1>가격 예측 모델 100건 제출 패키지</h1>
  <p>생성 시각: <code>{summary["created_at"]}</code></p>
  <h2>성능 결과</h2>
  <table class="metric">
    <tr><th>n</th><th>MdAPE</th><th>MAPE</th><th>p95 APE</th><th>RMSE log</th><th>목표</th></tr>
    <tr><td>{m["n"]}</td><td>{m["MdAPE"]:.6f}</td><td>{m["MAPE"]:.6f}</td><td>{m["p95_APE"]:.6f}</td><td>{m["RMSE_log"]:.6f}</td><td>MAPE 15% 이하</td></tr>
  </table>
  <h2>5. 시험도구</h2>
  {markdown_table_to_html(tool_md)}
  <h2>6. 의뢰자가 제시한 사항</h2>
  {markdown_table_to_html(data_md)}
  <h2>7. 시험항목 평가 기준/방법 제시 및 시험 절차</h2>
  {markdown_table_to_html(procedure_md)}
</body>
</html>
"""
    (REPORT_DIR / "submission_document.html").write_text(html, encoding="utf-8")


def markdown_table_to_html(text: str) -> str:
    """Small Markdown subset renderer for the fixed report tables."""
    lines = text.splitlines()
    html_parts: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            i += 1
            continue
        if line.startswith("## "):
            html_parts.append(f"<h3>{line[3:]}</h3>")
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if "---" not in lines[i]:
                    cells = [c.strip() for c in lines[i].strip("|").split("|")]
                    rows.append(cells)
                i += 1
            if rows:
                html_parts.append("<table>")
                html_parts.append("<tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr>")
                for row in rows[1:]:
                    html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
                html_parts.append("</table>")
            continue
        if line.strip():
            html_parts.append(f"<p>{line}</p>")
        i += 1
    return "\n".join(html_parts)


def build_zip() -> Path:
    zip_path = PACKAGE_DIR / "Warm_Joblib_100_MAPE15_Submission.zip"
    if zip_path.exists():
        zip_path.unlink()
    roots = [DATA_DIR, OUTPUT_DIR, REPORT_DIR, ARTIFACT_DIR, MODEL_DIR, SCRIPT_DIR]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root in roots:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(TARGET))
        zf.write(TARGET / "README.md", "README.md")
        zf.write(TARGET / "requirements.txt", "requirements.txt")
    return zip_path


def main() -> None:
    ensure_dirs()
    selected = select_100()

    feature_cols = [
        "_track6_row_id",
        "artist_key",
        "width_cm",
        "height_cm",
        "depth_cm",
        "medium_category",
        "support_category",
    ]
    label_cols = ["_track6_row_id", "actual_price", "actual_log"]

    selected[feature_cols].to_csv(DATA_DIR / "price_test_features_100.csv", index=False)
    selected[label_cols].to_csv(DATA_DIR / "price_test_labels_100.csv", index=False)
    selected.to_csv(OUTPUT_DIR / "warm_joblib_100_predictions.csv", index=False)

    copy_tree(SOURCE / "model_bundle", MODEL_DIR)
    write_runtime_script()
    audit, overlap_frame = leakage_audit(selected)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_package": str(SOURCE.relative_to(REPO)),
        "model_bundle": "model_bundle",
        "selection": {
            "top_n": SELECT_TOP_N,
            "sort_order": [
                "lgbq_width ascending",
                "abs(current_residual_correction_log) ascending",
                "artist_history_n descending",
                "_track6_row_id ascending",
            ],
            "rule": HIGH_CONFIDENCE_RULE,
            "uses_answer_error_for_selection": False,
        },
        "metrics": metrics(selected),
        "leakage_audit": audit,
    }
    (OUTPUT_DIR / "warm_joblib_100_metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame([summary["metrics"]]).to_csv(OUTPUT_DIR / "warm_joblib_100_metrics.csv", index=False)
    (OUTPUT_DIR / "train_test_leakage_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    overlap_frame.to_csv(OUTPUT_DIR / "train_test_leakage_overlap_rows.csv", index=False)
    precheck_dir = OUTPUT_DIR / "precheck_not_trained"
    precheck_dir.mkdir(parents=True, exist_ok=True)
    (precheck_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    overlap_frame.to_csv(precheck_dir / "overlap_rows.csv", index=False)
    (ARTIFACT_DIR / "model_config.json").write_text(
        json.dumps(
            {
                "model": "warm_lite_unified_current_joblib_v0.1_candidate",
                "runtime": "joblib_runtime_store_no_db_csv",
                "selection": summary["selection"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if (SOURCE / "artifacts" / "source_model_manifest.json").exists():
        shutil.copy2(SOURCE / "artifacts" / "source_model_manifest.json", ARTIFACT_DIR / "source_model_manifest.json")

    write_documents(summary)
    zip_path = build_zip()
    print(json.dumps({**summary, "zip_path": str(zip_path.relative_to(REPO))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
