#!/usr/bin/env python3
"""Create A9 split experiment configs and prompts.

A9 is split into smaller, auditable experiments so that support/material/size
effects are not hidden inside one broad representative run.
"""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BASE_DIR = REPO / "experiments" / "track6"
SPLIT_ROOT = "data/track6_split_with_year_type_edition_size"
COMMON_NUMERIC = ["ln_estimated_ho", "log_area", "width_cm", "height_cm"]


def run_py(slug: str) -> str:
    return f'''#!/usr/bin/env python3
"""Run {slug} with the fixed Track6 variable experiment runner."""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
CONFIG = REPO / "experiments" / "track6" / "{slug}" / "experiment_config.json"
sys.path.insert(0, str(REPO))

from scripts.track6.fixed_variable_experiment_runner import run_from_config  # noqa: E402


def main() -> None:
    results = run_from_config(CONFIG)
    print(
        results[
            ["variable_block", "scope", "model_code", "model_name", "R2", "MdAPE", "p95_APE"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
'''


def prompt_text(exp: dict) -> str:
    block_lines = "\n".join(
        f"- {b['name']}: `{', '.join(b['features'])}`" for b in exp["variable_blocks"]
    )
    return f"""# Track6 {exp['experiment_id']} 실험 지시 기록

## 실험 제목

- {exp['title']}

## 실험 목적

- {exp['purpose']}
- A9 대표 실험을 세부 실험으로 나누어 어떤 조건에서 지지체/재료/크기 조합이 실제로 도움이 되는지 확인한다.

## 사용 데이터

- 기준 split: `{SPLIT_ROOT}`
- 학습 입력: `{SPLIT_ROOT}/features/warm/track6_train_warm_features.csv`
- 학습 정답: `{SPLIT_ROOT}/labels/track6_train_labels.csv`
- Warm 테스트 입력: `{SPLIT_ROOT}/features/warm/track6_test_warm_warm_features.csv`
- Warm 테스트 정답: `{SPLIT_ROOT}/labels/track6_test_warm_labels.csv`
- Cold 테스트 입력: `{SPLIT_ROOT}/features/cold/track6_test_cold_cold_features.csv`
- Cold 테스트 정답: `{SPLIT_ROOT}/labels/track6_test_cold_labels.csv`

## 라벨 사용 기준

- 가격 라벨은 학습 target과 평가 지표 계산에만 사용한다.
- 입력 피처와 정답 가격은 `_track6_row_id`로만 연결한다.
- 가격 라벨은 모델 입력 피처에 포함하지 않는다.

## 공통 실행 기준

- 공통 실행 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 실험별 차이는 `experiment_config.json`의 변수 조합만 바꾼다.
- 숫자형 피처는 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
- 범주형 피처는 문자열화 후 결측을 `__missing__`으로 두고 one-hot encoding한다.

## 모델군

- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 실험 변수 조합

{block_lines}

## 평가 지표

- R2
- MdAPE
- p95 APE
- Within-30
- Within-50
- MAPE

## 판단 기준

- 같은 모델군과 같은 split에서 MdAPE가 낮아지면 대표 오차가 개선된 것으로 본다.
- p95 APE가 함께 낮아지면 큰 오차 안정성도 개선된 것으로 본다.
- Warm과 Cold 결과는 합치지 않고 별도로 판단한다.
- Warm에서만 좋은 조합과 Cold에서만 좋은 조합은 분리 후보로 둔다.
"""


def build_config(exp: dict) -> dict:
    export_cols = set()
    for block in exp["variable_blocks"]:
        export_cols.update(block["features"])
    for bucket in exp.get("bucket_features", []):
        export_cols.add(bucket["source_col"])
        export_cols.add(bucket["bucket_col"])
    for combo in exp.get("combo_features", []):
        export_cols.update(combo["source_cols"])
        export_cols.add(combo["combo_col"])
    config = {
        "experiment_id": exp["experiment_id"],
        "title": exp["title"],
        "purpose": exp["purpose"],
        "description": exp["description"],
        "split_root": SPLIT_ROOT,
        "exp_dir": f"experiments/track6/{exp['slug']}",
        "prompt_file": f"experiments/track6/{exp['slug']}/prompts/used_prompt.md",
        "export_feature_columns": sorted(export_cols),
        "numeric_features": COMMON_NUMERIC,
        "variable_blocks": exp["variable_blocks"],
        "comment": {
            "실험 목적": exp["purpose"],
            "실험 위치": f"Group A의 A9 세부 실험 중 {exp['experiment_id']}에 해당한다.",
            "공통 실행 코드": "scripts/track6/fixed_variable_experiment_runner.py",
            "숫자형 처리": "숫자형 피처는 중앙값 결측 보정 후 StandardScaler를 적용한다.",
            "범주형 처리": "범주형 피처는 one-hot encoding으로 처리한다.",
            "판단 기준": "Warm/Cold를 분리해 MdAPE, p95 APE, R2를 비교한다.",
            "재현성 확인": "동일 설정으로 재실행해 주요 지표가 같은지 비교한다.",
        },
    }
    if "bucket_features" in exp:
        config["bucket_features"] = exp["bucket_features"]
    if "combo_features" in exp:
        config["combo_features"] = exp["combo_features"]
    return config


EXPERIMENTS = [
    {
        "experiment_id": "A9-1",
        "slug": "A9-1_basic_artwork_feature_bundle",
        "title": "Track6 A9-1 작품 기본 피처 묶음 정의 실험 결과",
        "purpose": "호수, NANT 재료, NANT 지지체를 기준으로 작품 기본 피처 묶음을 정의한다.",
        "description": "Define candidate base artwork feature bundles for A9.",
        "variable_blocks": [
            {
                "name": "호수 + NANT 재료 + NANT 지지체",
                "features": ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "작품 기본 피처 묶음 후보",
            },
            {
                "name": "호수 + 로그면적 + NANT 재료 + NANT 지지체",
                "features": ["ln_estimated_ho", "log_area", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "기본 묶음에 로그 면적 추가",
            },
            {
                "name": "전체 크기 + NANT 재료 + NANT 지지체",
                "features": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "A8-1 확장 크기 묶음에 NANT 재료와 지지체 추가",
            },
        ],
    },
    {
        "experiment_id": "A9-2",
        "slug": "A9-2_support_representation_compare",
        "title": "Track6 A9-2 지지체 표현 비교 실험 결과",
        "purpose": "수집 지지체 대분류와 NANT 지지체 중 어떤 표현이 더 안정적인지 확인한다.",
        "description": "Compare collected support category and NANT support in size/material context.",
        "variable_blocks": [
            {
                "name": "로그면적 + NANT 재료 번호 + 수집 지지체 대분류",
                "features": ["log_area", "nant_material_idx", "support_category"],
                "description": "수집 지지체 대분류 사용",
            },
            {
                "name": "로그면적 + NANT 재료 번호 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "nant_support"],
                "description": "NANT 지지체 사용",
            },
            {
                "name": "로그면적 + NANT 재료 번호 + 수집 지지체 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "support_category", "nant_support"],
                "description": "두 지지체 표현을 함께 사용해 중복 효과 확인",
            },
        ],
    },
    {
        "experiment_id": "A9-3",
        "slug": "A9-3_material_representation_with_support",
        "title": "Track6 A9-3 재료 표현별 지지체 추가 실험 결과",
        "purpose": "재료 표현 방식이 달라질 때 지지체 추가 효과가 어떻게 달라지는지 확인한다.",
        "description": "Compare material representations while support is included.",
        "bucket_features": [
            {
                "source_col": "collected_material_raw",
                "bucket_col": "collected_material_raw_bucket",
                "top_n": 80,
                "other_value": "other_raw_material",
                "description": "수집 원문 재료명을 학습 데이터 빈도 기준으로 묶은 변수",
            }
        ],
        "variable_blocks": [
            {
                "name": "로그면적 + 수집 재료 대분류 + NANT 지지체",
                "features": ["log_area", "medium_category", "nant_support"],
                "description": "수집 재료 대분류 기준",
            },
            {
                "name": "로그면적 + 수집 원문 재료 묶음 + NANT 지지체",
                "features": ["log_area", "collected_material_raw_bucket", "nant_support"],
                "description": "수집 원문 재료명 빈도 묶음 기준",
            },
            {
                "name": "로그면적 + NANT 재료 번호 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "nant_support"],
                "description": "NANT 재료 번호 기준",
            },
            {
                "name": "로그면적 + NANT 도구명 + NANT 지지체",
                "features": ["log_area", "nant_tool", "nant_support"],
                "description": "NANT 도구명 기준",
            },
            {
                "name": "로그면적 + NANT 재료 번호 + 도구명 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "NANT 재료 번호와 도구명을 함께 사용",
            },
        ],
    },
    {
        "experiment_id": "A9-4",
        "slug": "A9-4_size_representation_with_material_support",
        "title": "Track6 A9-4 크기 표현별 재료/지지체 조합 실험 결과",
        "purpose": "크기 표현 방식에 따라 재료와 지지체 조합의 성능이 달라지는지 확인한다.",
        "description": "Compare size representations while material and support are included.",
        "variable_blocks": [
            {
                "name": "호수 + NANT 재료 + NANT 지지체",
                "features": ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "호수 기반 크기 표현",
            },
            {
                "name": "로그면적 + NANT 재료 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "로그 면적 기반 크기 표현",
            },
            {
                "name": "가로세로 + NANT 재료 + NANT 지지체",
                "features": ["width_cm", "height_cm", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "가로/세로 기반 크기 표현",
            },
            {
                "name": "전체 크기 + NANT 재료 + NANT 지지체",
                "features": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "호수, 면적, 가로세로를 모두 사용",
            },
        ],
    },
    {
        "experiment_id": "A9-5",
        "slug": "A9-5_material_support_combo_bucket",
        "title": "Track6 A9-5 재료+지지체 조합 변수 실험 결과",
        "purpose": "재료와 지지체를 따로 쓰는 것보다 조합 변수로 묶었을 때 가격 예측력이 개선되는지 확인한다.",
        "description": "Compare generated material-support combo buckets.",
        "combo_features": [
            {
                "source_cols": ["nant_material_idx", "nant_support"],
                "combo_col": "nant_material_support_bucket",
                "top_n": 120,
                "other_value": "other_material_support",
                "description": "NANT 재료 번호와 NANT 지지체를 결합한 조합 변수",
            },
            {
                "source_cols": ["nant_support", "nant_tool"],
                "combo_col": "nant_support_nant_tool_bucket",
                "top_n": 120,
                "other_value": "other_support_tool",
                "description": "NANT 지지체와 NANT 도구명을 결합한 조합 변수",
            },
        ],
        "variable_blocks": [
            {
                "name": "로그면적 + NANT 재료 + NANT 지지체",
                "features": ["log_area", "nant_material_idx", "nant_support"],
                "description": "조합 변수 비교를 위한 분리 피처 기준",
            },
            {
                "name": "로그면적 + 재료지지체 조합",
                "features": ["log_area", "nant_material_support_bucket"],
                "description": "NANT 재료 번호와 지지체를 하나의 조합 변수로 사용",
            },
            {
                "name": "호수 + 재료지지체 조합",
                "features": ["ln_estimated_ho", "nant_material_support_bucket"],
                "description": "호수와 재료지지체 조합 변수 사용",
            },
            {
                "name": "전체 크기 + 재료지지체 조합",
                "features": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "nant_material_support_bucket"],
                "description": "전체 크기 표현과 재료지지체 조합 변수 사용",
            },
            {
                "name": "로그면적 + 지지체도구 조합",
                "features": ["log_area", "nant_support_nant_tool_bucket"],
                "description": "NANT 지지체와 도구명을 하나의 조합 변수로 사용",
            },
        ],
    },
    {
        "experiment_id": "A9-6",
        "slug": "A9-6_warm_cold_feature_set_split",
        "title": "Track6 A9-6 Warm/Cold 작품 피처 묶음 분리 실험 결과",
        "purpose": "Warm과 Cold에서 같은 작품 피처 묶음을 써도 되는지, 분리 후보가 필요한지 확인한다.",
        "description": "Compare candidate artwork feature sets for Warm and Cold separately.",
        "bucket_features": [
            {
                "source_col": "collected_material_raw",
                "bucket_col": "collected_material_raw_bucket",
                "top_n": 80,
                "other_value": "other_raw_material",
                "description": "수집 원문 재료명을 학습 데이터 빈도 기준으로 묶은 변수",
            }
        ],
        "variable_blocks": [
            {
                "name": "공통 기본 후보",
                "features": ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"],
                "description": "Warm/Cold 공통 적용 가능한 최소 기본 후보",
            },
            {
                "name": "공통 로그면적 후보",
                "features": ["log_area", "nant_material_idx", "nant_support"],
                "description": "로그면적 중심 공통 후보",
            },
            {
                "name": "Warm 후보: 전체 크기 + 원문 재료 묶음 + NANT 지지체",
                "features": ["ln_estimated_ho", "log_area", "width_cm", "height_cm", "collected_material_raw_bucket", "nant_support"],
                "description": "A8-2/A9 대표 실행에서 Warm 쪽이 좋았던 확장 후보",
            },
            {
                "name": "Cold 후보: 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류",
                "features": ["log_area", "medium_category", "support_category"],
                "description": "A9 대표 실행에서 Cold 쪽이 좋았던 단순 후보",
            },
        ],
    },
]


def main() -> None:
    for exp in EXPERIMENTS:
        exp_dir = BASE_DIR / exp["slug"]
        (exp_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (exp_dir / "scripts").mkdir(parents=True, exist_ok=True)
        config = build_config(exp)
        (exp_dir / "experiment_config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (exp_dir / "prompts" / "used_prompt.md").write_text(prompt_text(exp), encoding="utf-8")
        run_path = exp_dir / "scripts" / "run_experiment.py"
        run_path.write_text(run_py(exp["slug"]), encoding="utf-8")
        run_path.chmod(0o755)
        print(f"created {exp['experiment_id']} {exp_dir.relative_to(REPO)}")


if __name__ == "__main__":
    main()
