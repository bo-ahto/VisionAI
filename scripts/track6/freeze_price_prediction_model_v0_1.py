#!/usr/bin/env python3
"""Freeze Track6 price prediction model policy v0.1.

The v0.1 folder is a reproducibility bundle, not a final production package.
It keeps the midterm-report model policy, the exact training split snapshot,
the key experiment evidence, and the scripts required to recreate the evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
VERSION = "v0.1"
MODEL_ROOT = REPO / "models" / "track6" / f"price_prediction_{VERSION}"

COPY_DIRS = [
    ("data/track6_split", "data/training/track6_split"),
    ("experiments/track6/PP-SVC2_warm_comparable_stats_stability", "evidence/experiments/PP-SVC2_warm_comparable_stats_stability"),
    ("experiments/track6/PP-SVC3_warm_svc_blend_routing", "evidence/experiments/PP-SVC3_warm_svc_blend_routing"),
    ("experiments/track6/PP-V8_warm_deployment_simplification", "evidence/experiments/PP-V8_warm_deployment_simplification"),
    ("experiments/track6/PP-Y18_cold_y16_top_candidate_stability", "evidence/experiments/PP-Y18_cold_y16_top_candidate_stability"),
]

COPY_FILES = [
    ("data/test_new_artworks_test_0604.csv", "data/evaluation/test_new_artworks_test_0604.csv"),
    ("data/test_new_artworks_test_noprice_0604.csv", "data/evaluation/test_new_artworks_test_noprice_0604.csv"),
    ("data/test_new_artworks_test_0604_artist_warm_cold_route.csv", "data/evaluation/test_new_artworks_test_0604_artist_warm_cold_route.csv"),
    ("data/test_new_artworks_test_0604_artist_warm_cold_summary.csv", "data/evaluation/test_new_artworks_test_0604_artist_warm_cold_summary.csv"),
    ("docs/track6/experiments/model_feature_selection_midterm_report.md", "evidence/reports/model_feature_selection_midterm_report.md"),
    ("docs/track6/experiments/model_feature_selection_midterm_report.html", "evidence/reports/model_feature_selection_midterm_report.html"),
    ("docs/track6/planning/service_model_operationalization_plan.md", "evidence/reports/service_model_operationalization_plan.md"),
    ("docs/track6/planning/service_api_detailed_spec.md", "evidence/reports/service_api_detailed_spec.md"),
    ("data/track6/artifacts/track6_artifact_manifest.json", "legacy_artifacts/track6_artifact_manifest.json"),
    ("data/track6/artifacts/track6_warm_huber.joblib", "legacy_artifacts/track6_warm_huber.joblib"),
    ("data/track6/artifacts/track6_cold_lightgbm.joblib", "legacy_artifacts/track6_cold_lightgbm.joblib"),
    ("data/track6/artifacts/track6_cold_catboost.cbm", "legacy_artifacts/track6_cold_catboost.cbm"),
    ("scripts/track6/run_pre_pp_experiments.py", "reproduction/scripts/run_pre_pp_experiments.py"),
    ("scripts/track6/run_pp_svc1_comparable_stats_feature_validation.py", "reproduction/scripts/run_pp_svc1_comparable_stats_feature_validation.py"),
    ("scripts/track6/run_pp_svc2_warm_comparable_stats_stability.py", "reproduction/scripts/run_pp_svc2_warm_comparable_stats_stability.py"),
    ("scripts/track6/run_pp_svc3_warm_svc_blend_routing.py", "reproduction/scripts/run_pp_svc3_warm_svc_blend_routing.py"),
    ("scripts/track6/run_pp_v_experiments.py", "reproduction/scripts/run_pp_v_experiments.py"),
    ("scripts/track6/run_pp_v6_v8_warm_gap_experiments.py", "reproduction/scripts/run_pp_v6_v8_warm_gap_experiments.py"),
    ("scripts/track6/run_pp_w_experiments.py", "reproduction/scripts/run_pp_w_experiments.py"),
    ("scripts/track6/run_pp_x_gallery_exhibition_revalidation.py", "reproduction/scripts/run_pp_x_gallery_exhibition_revalidation.py"),
    ("scripts/track6/run_pp_h_search_pilot_experiments.py", "reproduction/scripts/run_pp_h_search_pilot_experiments.py"),
    ("scripts/track6/run_pp_y_cold_combination_experiments.py", "reproduction/scripts/run_pp_y_cold_combination_experiments.py"),
    ("scripts/track6/run_pp_y15_oof_fixed_revalidation.py", "reproduction/scripts/run_pp_y15_oof_fixed_revalidation.py"),
    ("scripts/track6/run_pp_y17_y20_cold_gap_revalidation.py", "reproduction/scripts/run_pp_y17_y20_cold_gap_revalidation.py"),
    ("scripts/track6/run_0604_new_artworks_current_policy_readiness.py", "reproduction/scripts/run_0604_new_artworks_current_policy_readiness.py"),
    ("scripts/track6/extract_price_prediction_v0_1_features.py", "reproduction/scripts/extract_price_prediction_v0_1_features.py"),
]

SKIP_NAMES = {".DS_Store", "__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ignore_names(_dir: str, names: list[str]) -> set[str]:
    return {name for name in names if name in SKIP_NAMES}


def copy_file(src_rel: str, dst_rel: str, missing: list[str]) -> None:
    src = REPO / src_rel
    dst = MODEL_ROOT / dst_rel
    if not src.exists():
        missing.append(src_rel)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src_rel: str, dst_rel: str, missing: list[str]) -> None:
    src = REPO / src_rel
    dst = MODEL_ROOT / dst_rel
    if not src.exists():
        missing.append(src_rel)
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=ignore_names)


def model_policy() -> dict[str, Any]:
    return {
        "version": VERSION,
        "name": "price_prediction_v0.1",
        "status": "midterm_test_policy_freeze",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "중간 리포트 기준 후보를 신규 테스트/서비스 API 검증의 기준 버전으로 고정",
        "target": "ln_price_krw",
        "price_unit": "KRW",
        "routing_policy": {
            "warm": "matched_train_artist 또는 artist_key가 v0.1 학습 artist registry에 존재",
            "cold": "학습 artist registry에 없는 신규 작가",
        },
        "warm_policy": {
            "name": "Warm v0.1 current primary",
            "candidate": "PP-SVC3 blend_svcnum_ppv8_wsvc_0.70",
            "formula": "pred_log = 0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded",
            "metrics_test": {
                "MdAPE": 0.1405,
                "MAPE": 0.2748,
                "p95_APE": 0.8331,
                "RMSE_log": 0.3996,
            },
            "component_1": {
                "name": "svc_numeric_seed_mean",
                "description": "유사 작품 기반 가격 피처를 Warm Huber 입력에 추가한 후보의 seed 평균",
                "weight": 0.70,
            },
            "component_2": {
                "name": "pp_v8_compact_blend_mape_guarded",
                "description": "여러 Warm 후보 중 평균오차 안정성이 좋은 compact blend 후보",
                "weight": 0.30,
            },
            "operational_note": "현재 v0.1은 정책과 근거를 고정한다. 신규 데이터 직접 추론을 위해서는 PP-SVC3 component chain artifact화가 필요하다.",
        },
        "cold_policy": {
            "name": "Cold reference v0.1",
            "candidate": "PP-Y18 qwidth_bin_oof_min30_cap0.25",
            "model_family": "LightGBM Quantile + qwidth 구간 보정",
            "metrics_test": {
                "MdAPE": 0.4247,
                "MAPE": 0.9910,
                "p95_APE": 3.3053,
            },
            "display_policy": "확정 가격이 아니라 참고 예측가와 넓은 가격 범위로 표시",
            "operational_note": "Cold는 Warm보다 오차 위험이 커서 v0.1에서도 낮은 신뢰도/범위 중심으로만 사용한다.",
        },
        "legacy_artifacts": {
            "role": "smoke test / baseline only",
            "warning": "legacy artifact를 v0.1 current policy 결과로 해석하지 않는다.",
        },
        "new_test_0604": {
            "source": "data/test_new_artworks_test_0604.csv",
            "route_result": "6873 rows warm, 0 rows cold by matched_train_artist",
        },
    }


def readme_text() -> str:
    return f"""# 가격 예측 모델 {VERSION}

- 목적: 중간 리포트 기준 후보를 신규 테스트와 서비스 API 검증의 기준 버전으로 고정
- 상태: 중간 확정 테스트 기준
- 최종 배포 여부: 아님
- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. 버전 정의

- `price_prediction_{VERSION}`은 모델 정책, 학습 데이터, 실험 근거, 재현 스크립트를 한 폴더에 묶은 재현용 번들
- Warm 기준 후보: `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
- Cold 기준 후보: `PP-Y18 qwidth_bin_oof_min30_cap0.25`
- 기존 `data/track6/artifacts` 모델은 baseline smoke test 용도이며 v0.1 현재 후보가 아님

## 2. 폴더 구조

| 경로 | 내용 |
|---|---|
| `config/model_policy_v0.1.json` | v0.1 모델 정책 |
| `data/training/track6_split/` | 학습/검증/테스트 split 스냅샷 |
| `data/evaluation/` | 2026-06-04 신규 테스트 데이터와 Warm/Cold 라우팅 결과 |
| `evidence/experiments/` | v0.1 선정 근거 실험 산출물 |
| `evidence/reports/` | 중간 리포트와 서비스 적용 문서 |
| `legacy_artifacts/` | 이전 baseline artifact |
| `reproduction/scripts/` | 근거 실험 재현에 필요한 스크립트 |
| `manifest/files_manifest.csv` | 파일별 크기/checksum |
| `manifest/MANIFEST.sha256` | 재현성 확인용 checksum |

## 3. Warm v0.1

- 예측식: `pred_log = 0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded`
- test MdAPE: `0.1405`
- test MAPE: `0.2748`
- test p95_APE: `0.8331`
- 해석: 같은 작가의 과거 가격 기준과 오차 안정화 후보를 함께 사용

## 4. Cold reference v0.1

- 기준 후보: `LightGBM Quantile + qwidth 구간 보정`
- test MdAPE: `0.4247`
- test MAPE: `0.9910`
- test p95_APE: `3.3053`
- 해석: Cold는 확정 가격보다 참고 예측가와 넓은 범위 표시 중심

## 5. 재현 기준

- 학습 데이터는 이 폴더의 `data/training/track6_split/` 스냅샷 사용
- 실험 근거는 `evidence/experiments/`의 metrics/predictions/config 사용
- 파일 무결성은 `manifest/MANIFEST.sha256`로 확인

## 6. 신규 무가격 CSV 피처 추출

- 기본 입력: `data/test_new_artworks_test_noprice_0604.csv`
- v0.1 폴더 내 입력 사본: `data/evaluation/test_new_artworks_test_noprice_0604.csv`
- 실행 스크립트: `reproduction/scripts/extract_price_prediction_v0_1_features.py`
- 기본 실행:

```bash
python3 models/track6/price_prediction_v0.1/reproduction/scripts/extract_price_prediction_v0_1_features.py
```

- 다른 입력 파일 실행:

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \\
  --input data/new_artworks.csv \\
  --output-dir models/track6/price_prediction_v0.1/data/evaluation/new_artworks_features
```

- 주요 출력: `features_all_v0_1.csv`, `warm_features_v0_1.csv`, `cold_features_v0_1.csv`, `routing_v0_1.csv`, `feature_quality_report.csv`
- 주의: 이 단계는 가격 예측 전 입력 변환 단계이며, 가격 예측값 생성은 별도 추론 스크립트에서 수행

## 7. 주의

- 이 버전은 중간 리포트 기준을 고정한 테스트용 버전
- PP-SVC3는 현재 단일 inference artifact가 아니라 실험 예측값 결합 정책
- 신규 데이터 직접 추론을 위해서는 다음 단계에서 PP-SVC3 component chain을 artifact화해야 함
"""


def collect_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(MODEL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(MODEL_ROOT).as_posix()
        rows.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def write_manifest(rows: list[dict[str, Any]]) -> None:
    manifest_dir = MODEL_ROOT / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    csv_path = manifest_dir / "files_manifest.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    sha_path = manifest_dir / "MANIFEST.sha256"
    lines = [f"{row['sha256']}  {row['path']}" for row in rows]
    sha_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def freeze(overwrite: bool) -> None:
    if MODEL_ROOT.exists():
        if not overwrite:
            raise FileExistsError(f"{MODEL_ROOT} already exists. Use --overwrite to rebuild.")
        shutil.rmtree(MODEL_ROOT)

    missing: list[str] = []
    for subdir in ["config", "manifest", "data", "evidence", "legacy_artifacts", "reproduction"]:
        (MODEL_ROOT / subdir).mkdir(parents=True, exist_ok=True)

    for src, dst in COPY_DIRS:
        copy_dir(src, dst, missing)
    for src, dst in COPY_FILES:
        copy_file(src, dst, missing)

    policy = model_policy()
    policy["missing_sources"] = missing
    (MODEL_ROOT / "config" / "model_policy_v0.1.json").write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
    (MODEL_ROOT / "README.md").write_text(readme_text(), encoding="utf-8")

    rows = collect_manifest()
    write_manifest(rows)
    (MODEL_ROOT / "manifest" / "freeze_summary.json").write_text(json.dumps({
        "version": VERSION,
        "model_root": str(MODEL_ROOT.relative_to(REPO)),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "missing_sources": missing,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "completed",
        "model_root": str(MODEL_ROOT.relative_to(REPO)),
        "file_count": len(rows),
        "total_mb": round(sum(row["bytes"] for row in rows) / (1024 * 1024), 2),
        "missing_sources": missing,
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="Rebuild the v0.1 folder if it already exists.")
    args = parser.parse_args()
    freeze(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
