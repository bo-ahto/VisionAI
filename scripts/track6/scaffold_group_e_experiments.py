#!/usr/bin/env python3
"""Scaffold Group E artist-variable experiment configs and prompts."""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = "data/track6_split_with_year_type_edition_size_artist_name"
BASE = REPO / "experiments" / "track6"


EXPERIMENTS = [
    {
        "id": "E1",
        "folder": "E1_artist_name_only",
        "title": "Track6 E1 작가명 단독 실험 결과",
        "purpose": "작가명만으로도 작품 가격대의 일부를 설명할 수 있는지 확인",
        "export": ["artist_name_ko"],
        "numeric": [],
        "blocks": [
            ("작가명 only", ["artist_name_ko"], "작품 변수 없이 작가명 한글만 사용"),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "해석 중심": "작가명이 학습 데이터에 있는 Warm 결과를 중심으로 판단한다.",
            "Cold 해석 주의": "Cold는 신규 작가명이라 대부분 미학습 카테고리로 처리되므로 참고값으로만 본다.",
        },
    },
    {
        "id": "E2",
        "folder": "E2_artist_work_count_only",
        "title": "Track6 E2 작가별 학습 작품 수 단독 실험 결과",
        "purpose": "학습 데이터 안에 작품 수가 많은 작가일수록 예측이 안정적인지 확인",
        "export": ["artist_works_log"],
        "numeric": ["artist_works_log"],
        "blocks": [
            ("작가별 학습 작품 수 로그", ["artist_works_log"], "train 기준 작가별 작품 수를 log1p 변환한 생성 변수"),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "변수 성격": "수집값이 아니라 split의 train 기준 작가별 작품 수로 만든 생성 변수",
            "해석 중심": "Warm에서 작가별 학습량이 성능 안정성에 영향을 주는지 본다.",
            "Cold 해석 주의": "Cold 신규 작가는 학습 작품 수가 0이므로 Cold 결과는 참고값으로만 본다.",
        },
    },
    {
        "id": "E3",
        "folder": "E3_artist_birth_year_only",
        "title": "Track6 E3 작가 생년 단독 실험 결과",
        "purpose": "작가의 생년 정보가 가격 차이를 설명할 수 있는지 확인",
        "export": ["artist_meta_birth_year", "artist_meta_birth_year_is_missing"],
        "numeric": ["artist_meta_birth_year", "artist_meta_birth_year_is_missing"],
        "blocks": [
            ("생년 원값", ["artist_meta_birth_year"], "작가 출생연도 숫자값만 사용"),
            ("생년 원값 + 결측 여부", ["artist_meta_birth_year", "artist_meta_birth_year_is_missing"], "생년 값과 값이 없는 상태를 함께 사용"),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "해석 중심": "생년 또는 세대 정보가 단독으로 가격대 차이를 설명하는지 본다.",
            "결측 주의": "메타가 있는 작품만 골라 평가하지 않고 결측 flag를 함께 비교한다.",
        },
    },
    {
        "id": "E4",
        "folder": "E4_artist_exhibition_counts_only",
        "title": "Track6 E4 작가 전시/아트페어 횟수 단독 실험 결과",
        "purpose": "개인전, 그룹전, 아트페어 횟수가 가격 차이를 설명할 수 있는지 확인",
        "export": [
            "artist_exhibition_solo_count",
            "artist_exhibition_group_count",
            "artist_exhibition_fair_count",
            "artist_exhibition_total_count",
            "artist_exhibition_available_count",
            "artist_exhibition_solo_count_is_missing",
            "artist_exhibition_group_count_is_missing",
            "artist_exhibition_fair_count_is_missing",
        ],
        "numeric": [
            "artist_exhibition_solo_count",
            "artist_exhibition_group_count",
            "artist_exhibition_fair_count",
            "artist_exhibition_total_count",
            "artist_exhibition_available_count",
            "artist_exhibition_solo_count_is_missing",
            "artist_exhibition_group_count_is_missing",
            "artist_exhibition_fair_count_is_missing",
        ],
        "blocks": [
            ("개인전 횟수", ["artist_exhibition_solo_count"], "개인전 횟수만 사용"),
            ("그룹전 횟수", ["artist_exhibition_group_count"], "그룹전 횟수만 사용"),
            ("아트페어 횟수", ["artist_exhibition_fair_count"], "아트페어 횟수만 사용"),
            ("전시 총횟수", ["artist_exhibition_total_count"], "개인전/그룹전/아트페어 합산 횟수 사용"),
            (
                "전시 횟수 묶음 + 결측",
                [
                    "artist_exhibition_solo_count",
                    "artist_exhibition_group_count",
                    "artist_exhibition_fair_count",
                    "artist_exhibition_available_count",
                    "artist_exhibition_solo_count_is_missing",
                    "artist_exhibition_group_count_is_missing",
                    "artist_exhibition_fair_count_is_missing",
                ],
                "전시 횟수 3종과 정보 보유 상태를 함께 사용",
            ),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "표준화": "원본 saatchi 전시 횟수에서 200 초과 값은 연도 오입력으로 보고 결측 처리했다.",
            "해석 중심": "경력 횟수 자체가 가격대 차이를 설명하는지 확인한다.",
        },
    },
    {
        "id": "E5",
        "folder": "E5_artist_nationality_only",
        "title": "Track6 E5 작가 국적 단독 실험 결과",
        "purpose": "작가 국적 정보가 가격 차이를 설명할 수 있는지 확인",
        "export": ["artist_meta_nationality", "artist_meta_nationality_is_missing"],
        "numeric": ["artist_meta_nationality_is_missing"],
        "blocks": [
            ("국적 only", ["artist_meta_nationality"], "작가 국적 범주값만 사용"),
            ("국적 + 결측 여부", ["artist_meta_nationality", "artist_meta_nationality_is_missing"], "국적 값과 값이 없는 상태를 함께 사용"),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "해석 중심": "국적별 가격대 차이가 모델 성능으로 나타나는지 확인한다.",
            "주의": "국적은 출처/표본 수 편차가 있을 수 있어 단독 채택보다 후속 통제 실험이 필요하다.",
        },
    },
    {
        "id": "E6",
        "folder": "E6_artist_activity_sale_exposure_only",
        "title": "Track6 E6 작가 활동량/판매 노출량 단독 실험 결과",
        "purpose": "등록 작품 수와 판매 중 작품 수가 가격 예측에 도움 되는지 확인",
        "export": [
            "artist_meta_total_works",
            "artist_meta_for_sale_works",
            "artist_meta_total_works_is_missing",
            "artist_meta_for_sale_works_is_missing",
        ],
        "numeric": [
            "artist_meta_total_works",
            "artist_meta_for_sale_works",
            "artist_meta_total_works_is_missing",
            "artist_meta_for_sale_works_is_missing",
        ],
        "blocks": [
            ("등록 작품 수", ["artist_meta_total_works"], "작가 플랫폼 등록 작품 수만 사용"),
            ("판매 중 작품 수", ["artist_meta_for_sale_works"], "작가 판매 중 작품 수만 사용"),
            (
                "활동량 + 판매 노출량 + 결측",
                [
                    "artist_meta_total_works",
                    "artist_meta_for_sale_works",
                    "artist_meta_total_works_is_missing",
                    "artist_meta_for_sale_works_is_missing",
                ],
                "작품 등록량과 판매 노출량, 결측 상태를 함께 사용",
            ),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "해석 중심": "작가의 시장 노출량이 가격대 예측에 도움 되는지 확인한다.",
            "주의": "플랫폼별 수집 시점 차이가 있으므로 성능이 좋아도 운영 재현성을 별도로 확인한다.",
        },
    },
    {
        "id": "E7",
        "folder": "E7_artist_popularity_only",
        "title": "Track6 E7 작가 인지도 단독 실험 결과",
        "purpose": "팔로워 수와 주요 작가 여부가 가격 예측에 도움 되는지 확인",
        "export": [
            "artist_meta_followers",
            "artist_meta_is_p1",
            "artist_meta_followers_is_missing",
            "artist_meta_is_p1_is_missing",
        ],
        "numeric": [
            "artist_meta_followers",
            "artist_meta_is_p1",
            "artist_meta_followers_is_missing",
            "artist_meta_is_p1_is_missing",
        ],
        "blocks": [
            ("팔로워 수", ["artist_meta_followers"], "플랫폼 팔로워 수만 사용"),
            ("주요 작가 여부", ["artist_meta_is_p1"], "플랫폼이 표시한 주요 작가 여부만 사용"),
            (
                "인지도 묶음 + 결측",
                [
                    "artist_meta_followers",
                    "artist_meta_is_p1",
                    "artist_meta_followers_is_missing",
                    "artist_meta_is_p1_is_missing",
                ],
                "팔로워 수, 주요 작가 여부, 결측 상태를 함께 사용",
            ),
        ],
        "comment": {
            "실험군": "Group E: 작가 변수만",
            "해석 중심": "플랫폼 인지도 정보가 가격대 예측에 도움 되는지 확인한다.",
            "주의": "네이버 검색량은 현재 데이터셋에 없으므로 이번 실험에서는 제외한다.",
        },
    },
]


def write_experiment(item: dict) -> None:
    exp_dir = BASE / item["folder"]
    prompt_dir = exp_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "experiment_id": item["id"],
        "title": item["title"],
        "purpose": item["purpose"],
        "description": f"Group E artist variable experiment: {item['id']}",
        "exp_dir": f"experiments/track6/{item['folder']}",
        "prompt_file": f"experiments/track6/{item['folder']}/prompts/used_prompt.md",
        "split_root": SPLIT_ROOT,
        "export_feature_columns": item["export"],
        "numeric_features": item["numeric"],
        "variable_blocks": [
            {"name": name, "features": features, "description": description}
            for name, features, description in item["blocks"]
        ],
        "comment": {
            "실험 목적": item["purpose"],
            "학습 피처": " / ".join(", ".join(features) for _, features, _ in item["blocks"]),
            "테스트 피처": "학습 피처와 동일",
            "사용 모델": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
            "데이터 기준": "작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.",
            "평가 지표": "R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE",
            **item["comment"],
        },
    }
    (exp_dir / "experiment_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    prompt = [
        f"# {item['id']} 실험 프롬프트",
        "",
        f"- 실험 목적: {item['purpose']}",
        "- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`",
        "- split: `data/track6_split_with_year_type_edition_size_artist_name`",
        "- sampling 없음, 전체 split 사용",
        "- feature와 label은 `_track6_row_id` 기준으로 결합",
        "- label은 학습 target과 평가 지표 계산에만 사용",
        "- 가격/출처/URL 컬럼은 모델 입력 금지",
        "- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용",
        "- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리",
        "",
        "## 사용 피처",
    ]
    for name, features, description in item["blocks"]:
        prompt.append(f"- {name}: `{', '.join(features)}` - {description}")
    prompt.append("")
    prompt.append("## 모델")
    prompt.append("- Warm: Huber / Linear Regression / Ridge")
    prompt.append("- Cold: Huber / Quantile-LAD / LightGBM")
    prompt.append("")
    prompt.append("## 평가 지표")
    prompt.append("- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE")
    prompt_dir.joinpath("used_prompt.md").write_text("\n".join(prompt) + "\n", encoding="utf-8")


def main() -> None:
    for item in EXPERIMENTS:
        write_experiment(item)
        print(item["id"], BASE / item["folder"])


if __name__ == "__main__":
    main()
