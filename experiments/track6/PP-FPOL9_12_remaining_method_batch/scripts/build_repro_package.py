#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
SOURCE_EXP = REPO / "experiments/track6/PP-FPOL9_12_remaining_method_batch"
PACKAGE_DIR = REPO / "experiments/track6/PP-FPOL9_12_remaining_method_repro_package"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reset_package() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    for sub in ["data", "scripts", "artifacts", "outputs", "reports", "experiments", "packages"]:
        (PACKAGE_DIR / sub).mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path, role: str, records: list[dict[str, object]]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    records.append(
        {
            "role": role,
            "source_path": str(src.relative_to(REPO)),
            "package_path": str(dst.relative_to(PACKAGE_DIR)),
            "size_bytes": dst.stat().st_size,
            "sha256": sha256_file(dst),
        }
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_package() -> None:
    reset_package()
    records: list[dict[str, object]] = []

    copy_file(
        REPO / "experiments/track6/PP-FPOL6_directional_price_bin_guard/outputs/candidate_predictions.csv",
        PACKAGE_DIR / "data/source_fpol6_candidate_predictions.csv",
        "공통 source 후보 예측 데이터: validation/test labeled predictions",
        records,
    )
    copy_file(
        REPO / "experiments/track6/PP-FPOL6_directional_price_bin_guard/outputs/candidate_metrics.csv",
        PACKAGE_DIR / "data/source_fpol6_candidate_metrics.csv",
        "공통 source 후보 성능표: FPOL6 top 후보 선택 기준",
        records,
    )
    for name, src in [
        ("aux_p2_predictions.csv", REPO / "experiments/track6/PP-P2_quantile_width_model_routing/outputs/predictions.csv"),
        ("aux_l4_predictions.csv", REPO / "experiments/track6/PP-L4_huber_quantile_width_risk_calibration/outputs/predictions.csv"),
        ("aux_m1_predictions.csv", REPO / "experiments/track6/PP-M1_warm_artist_median_huber_residual/outputs/predictions.csv"),
        ("aux_l8_predictions.csv", REPO / "experiments/track6/PP-L8_quantile_huber_catboost_sequential/outputs/predictions.csv"),
        ("aux_l9_predictions.csv", REPO / "experiments/track6/PP-L9_huber_quantile_catboost_residual_sequential/outputs/predictions.csv"),
    ]:
        copy_file(src, PACKAGE_DIR / f"data/{name}", f"보조 예측 입력: {name}", records)

    for name in ["train_index.csv", "valid_index.csv", "test_index.csv", "split_manifest.json", "feature_columns.json"]:
        src_base = REPO / "experiments/track6/PP-L4_huber_quantile_width_risk_calibration"
        src = src_base / "data" / name
        if not src.exists():
            src = src_base / "artifacts" / name
        copy_file(src, PACKAGE_DIR / "data" / name, f"원본 split/feature 재현 정보: {name}", records)

    copy_file(
        SOURCE_EXP / "scripts/run_remaining_methods.py",
        PACKAGE_DIR / "scripts/run_remaining_methods.py",
        "재현 실행 스크립트",
        records,
    )

    write_text(PACKAGE_DIR / "requirements.txt", "numpy\npandas\n")
    write_text(
        PACKAGE_DIR / "README.md",
        """# PP-FPOL9~12 남은 방법 재현 패키지

이 폴더는 FPOL6 상위 후보를 공통 source로 고정한 뒤, 남은 4개 방법을 동일 split과 동일 지표로 재현하기 위한 독립 패키지다.

## 재현 명령

```bash
python3 experiments/track6/PP-FPOL9_12_remaining_method_repro_package/scripts/run_remaining_methods.py --step all
```

패키지 폴더를 다른 위치로 옮긴 경우:

```bash
python3 scripts/run_remaining_methods.py --step all
```

## 포함 데이터

- `data/source_fpol6_candidate_predictions.csv`: FPOL6 상위 후보를 만들기 위한 validation/test row-level 예측 데이터
- `data/source_fpol6_candidate_metrics.csv`: FPOL6 후보 성능표
- `data/aux_p2_predictions.csv`: quantile width model routing 보조 예측
- `data/aux_l4_predictions.csv`: quantile width segment median 보조 예측
- `data/aux_m1_predictions.csv`: artist median + Huber residual 보조 예측
- `data/aux_l8_predictions.csv`: quantile feature + CatBoost residual 보조 예측
- `data/aux_l9_predictions.csv`: Huber quantile + CatBoost residual 보조 예측
- `data/train_index.csv`, `data/valid_index.csv`, `data/test_index.csv`: 원본 split 재현용 row id

## 실험 구성

1. `PP-FPOL9`: quantile width 기반 동적 cap/strength
2. `PP-FPOL10`: 모델 간 예측 gap 기반 라우팅
3. `PP-FPOL11`: tail-only 보정
4. `PP-FPOL12`: segment median + Huber residual 혼합

## 출력

실행 후 아래 파일이 생성된다.

- `reports/final_remaining_method_summary.md`
- `reports/final_remaining_method_summary.html`
- `outputs/final_remaining_method_recommendations.csv`
- `outputs/all_fpol9_12_test_metrics.csv`
- `experiments/PP-FPOL9_quantile_width_dynamic_cap_strength/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL10_model_gap_routing/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL11_tail_only_correction/outputs/candidate_metrics.csv`
- `experiments/PP-FPOL12_segment_median_huber_mix/outputs/candidate_metrics.csv`

## 주의

이 패키지는 새 원천 모델을 재학습하는 패키지가 아니라, 기존 학습/검증/test split에서 생성된 row-level 예측과 보조 예측을 입력으로 후처리 후보를 재현하는 패키지다. 정답 로그/가격은 validation/test 성능 계산에 포함되어 있으며, 후보 선택과 성능 검증의 재현성을 위해 함께 포함한다.
""",
    )

    manifest = {
        "package_id": "PP-FPOL9_12_remaining_method_repro_package",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "FPOL9~12 remaining-method batch reproducibility package",
        "run_command": "python3 scripts/run_remaining_methods.py --step all",
        "experiment_type": "row-level prediction post-processing and evaluation",
        "data_policy": {
            "train_data": "train_index.csv is included for split reproducibility; FPOL9~12 does not fit a new estimator on raw train rows.",
            "validation_data": "source_fpol6_candidate_predictions.csv and auxiliary prediction files include validation rows and labels for candidate scoring.",
            "test_data": "source_fpol6_candidate_predictions.csv and auxiliary prediction files include test rows and labels for final metrics.",
        },
        "files": records,
    }
    write_text(PACKAGE_DIR / "artifacts/repro_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def zip_package() -> Path:
    zip_path = PACKAGE_DIR / "packages/PP-FPOL9_12_remaining_method_repro_package.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path == zip_path or path.is_dir():
                continue
            zf.write(path, path.relative_to(PACKAGE_DIR))
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["build", "zip"], default="build")
    args = parser.parse_args()
    if args.mode == "build":
        build_package()
    else:
        zip_package()


if __name__ == "__main__":
    main()
