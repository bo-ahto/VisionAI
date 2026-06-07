#!/usr/bin/env python3
"""Scaffold Group F/G artist meta combo experiment configs and prompts."""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = "data/track6_split_with_year_type_edition_size_artist_name"
BASE = REPO / "experiments" / "track6"

ARTWORK_BASIC = ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"]
EXHIBITION_COUNTS = [
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
]
EXHIBITION_MISSING = [
    "artist_exhibition_solo_count_is_missing",
    "artist_exhibition_group_count_is_missing",
    "artist_exhibition_fair_count_is_missing",
]
ACTIVITY = ["artist_meta_total_works", "artist_meta_for_sale_works"]
ACTIVITY_MISSING = ["artist_meta_total_works_is_missing", "artist_meta_for_sale_works_is_missing"]
POPULARITY = ["artist_meta_followers", "artist_meta_is_p1"]
POPULARITY_MISSING = ["artist_meta_followers_is_missing", "artist_meta_is_p1_is_missing"]
PROFILE = ["artist_meta_birth_year", *EXHIBITION_COUNTS, "artist_meta_nationality"]
PROFILE_MISSING = ["artist_meta_birth_year_is_missing", *EXHIBITION_MISSING, "artist_meta_nationality_is_missing"]
FULL_META = [
    "artist_meta_birth_year",
    *EXHIBITION_COUNTS,
    "artist_meta_nationality",
    *ACTIVITY,
    *POPULARITY,
    "artist_meta_available_count",
    "artist_meta_completeness_score",
    "artist_exhibition_available_count",
    *PROFILE_MISSING,
    *ACTIVITY_MISSING,
    *POPULARITY_MISSING,
]
ALL_NUMERIC = [
    "ln_estimated_ho",
    "artist_meta_birth_year",
    "artist_meta_birth_year_is_missing",
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
    "artist_exhibition_total_count",
    "artist_exhibition_available_count",
    *EXHIBITION_MISSING,
    *ACTIVITY,
    *ACTIVITY_MISSING,
    *POPULARITY,
    *POPULARITY_MISSING,
    "artist_meta_available_count",
    "artist_meta_completeness_score",
    "artist_meta_nationality_is_missing",
    "artist_works_log",
]


EXPERIMENTS = [
    {
        "id": "F1",
        "folder": "F1_artist_birth_exhibition_combo",
        "title": "Track6 F1 작가 생년 + 전시 경력 조합 실험 결과",
        "purpose": "작가 생년과 전시 경력 횟수를 함께 쓰면 세대/경력 가격대 차이를 더 잘 설명하는지 확인",
        "blocks": [
            ("생년 + 전시 경력", ["artist_meta_birth_year", *EXHIBITION_COUNTS], "생년과 개인전/그룹전/아트페어 횟수 조합"),
            (
                "생년 + 전시 경력 + 결측",
                ["artist_meta_birth_year", *EXHIBITION_COUNTS, "artist_exhibition_available_count", "artist_meta_birth_year_is_missing", *EXHIBITION_MISSING],
                "생년/전시 횟수 조합에 결측 상태를 함께 반영",
            ),
        ],
        "comment": {
            "실험군": "Group F: 작가 메타 변수 조합",
            "확인 결과 활용": "세대와 경력 정보가 함께 유효하면 작가명 없이도 기본 작가 프로필 피처 후보로 둔다.",
        },
    },
    {
        "id": "F2",
        "folder": "F2_artist_activity_popularity_combo",
        "title": "Track6 F2 작가 활동량 + 인지도 조합 실험 결과",
        "purpose": "작품 수, 판매 중 작품 수, 팔로워 수, 주요 작가 여부가 시장 노출 효과를 설명하는지 확인",
        "blocks": [
            ("활동량 + 인지도", [*ACTIVITY, *POPULARITY], "등록/판매 노출량과 인지도 정보 조합"),
            ("활동량 + 인지도 + 결측", [*ACTIVITY, *POPULARITY, *ACTIVITY_MISSING, *POPULARITY_MISSING], "활동량/인지도 조합에 결측 상태를 함께 반영"),
        ],
        "comment": {
            "실험군": "Group F: 작가 메타 변수 조합",
            "확인 결과 활용": "시장 노출 정보가 유효하면 작가명 대체 또는 보조 메타 피처 후보로 둔다.",
        },
    },
    {
        "id": "F3",
        "folder": "F3_artist_basic_profile_combo",
        "title": "Track6 F3 작가 기본 프로필 조합 실험 결과",
        "purpose": "생년, 전시 경력, 국적을 함께 쓰면 작가 기본 프로필 효과를 설명하는지 확인",
        "blocks": [
            ("기본 작가 프로필", PROFILE, "생년, 전시 경력 횟수, 국적 조합"),
            ("기본 작가 프로필 + 결측", [*PROFILE, *PROFILE_MISSING], "기본 프로필 조합에 결측 상태를 함께 반영"),
        ],
        "comment": {
            "실험군": "Group F: 작가 메타 변수 조합",
            "확인 결과 활용": "작가 기본 프로필 묶음이 유효하면 작가 DB 우선 수집 항목을 정할 근거로 사용한다.",
        },
    },
    {
        "id": "F4",
        "folder": "F4_artist_activity_popularity_information_combo",
        "title": "Track6 F4 활동량/인지도 + 정보량 조합 실험 결과",
        "purpose": "활동량/인지도 정보에 메타 정보량 피처를 더하면 가격 예측과 신뢰도 판단에 도움이 되는지 확인",
        "blocks": [
            (
                "활동량 + 인지도 + 정보량",
                [*ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score", *ACTIVITY_MISSING, *POPULARITY_MISSING],
                "F2 조합에 작가 메타 보유 개수와 완성도 점수를 추가",
            ),
        ],
        "comment": {
            "실험군": "Group F: 작가 메타 변수 조합",
            "검토 반영": "기존 F2와 중복되지 않도록 F4는 정보량/결측 피처까지 포함한 조합으로 수정했다.",
            "확인 결과 활용": "정보량 피처가 유효하면 예측 신뢰도 보조 피처로 분리 관리한다.",
        },
    },
    {
        "id": "F5",
        "folder": "F5_artist_full_meta_bundle",
        "title": "Track6 F5 전체 작가 메타 묶음 실험 결과",
        "purpose": "작가명 없이 전체 작가 메타 묶음만으로 가격 예측이 가능한지 확인",
        "blocks": [
            ("전체 작가 메타 묶음", FULL_META, "생년/전시/국적/활동량/인지도/정보량 전체 조합"),
        ],
        "comment": {
            "실험군": "Group F: 작가 메타 변수 조합",
            "확인 결과 활용": "작가명 대체 가능성이 낮으면 작가 메타는 단독 모델보다 보조 피처로만 사용한다.",
        },
    },
    {
        "id": "G1",
        "folder": "G1_basic_artwork_plus_artist_name",
        "title": "Track6 G1 작품 기본 피처 + 작가명 실험 결과",
        "purpose": "호수·재료·지지체를 통제한 뒤에도 작가명이 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 작가명", [*ARTWORK_BASIC, "artist_name_ko"], "작품 조건 통제 후 작가명 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수", "해석 중심": "Warm 결과 중심. Cold의 작가명 효과는 참고값이다."},
    },
    {
        "id": "G2",
        "folder": "G2_basic_artwork_plus_artist_work_count",
        "title": "Track6 G2 작품 기본 피처 + 작가별 학습 작품 수 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가별 데이터 보유량이 예측 안정성에 도움 되는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 작가별 학습 작품 수", [*ARTWORK_BASIC, "artist_works_log"], "작품 조건 통제 후 작가별 학습량 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G3",
        "folder": "G3_basic_artwork_plus_birth_year",
        "title": "Track6 G3 작품 기본 피처 + 작가 생년 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가 생년/세대 정보가 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 생년", [*ARTWORK_BASIC, "artist_meta_birth_year"], "작품 조건 통제 후 생년 추가"),
            ("작품 기본 피처 + 생년 + 결측", [*ARTWORK_BASIC, "artist_meta_birth_year", "artist_meta_birth_year_is_missing"], "생년 값과 결측 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G4",
        "folder": "G4_basic_artwork_plus_exhibition_counts",
        "title": "Track6 G4 작품 기본 피처 + 전시 경력 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가 전시 경력 횟수가 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 전시 경력", [*ARTWORK_BASIC, *EXHIBITION_COUNTS], "작품 조건 통제 후 전시 횟수 3종 추가"),
            ("작품 기본 피처 + 전시 경력 + 결측", [*ARTWORK_BASIC, *EXHIBITION_COUNTS, "artist_exhibition_available_count", *EXHIBITION_MISSING], "전시 횟수와 정보 보유 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G5",
        "folder": "G5_basic_artwork_plus_nationality",
        "title": "Track6 G5 작품 기본 피처 + 작가 국적 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가 국적 정보가 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 국적", [*ARTWORK_BASIC, "artist_meta_nationality"], "작품 조건 통제 후 국적 추가"),
            ("작품 기본 피처 + 국적 + 결측", [*ARTWORK_BASIC, "artist_meta_nationality", "artist_meta_nationality_is_missing"], "국적 값과 결측 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G6",
        "folder": "G6_basic_artwork_plus_activity",
        "title": "Track6 G6 작품 기본 피처 + 작가 활동량 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가 활동량/판매 노출량이 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 활동량", [*ARTWORK_BASIC, *ACTIVITY], "작품 조건 통제 후 등록 작품 수와 판매 중 작품 수 추가"),
            ("작품 기본 피처 + 활동량 + 결측", [*ARTWORK_BASIC, *ACTIVITY, *ACTIVITY_MISSING], "활동량 값과 결측 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G7",
        "folder": "G7_basic_artwork_plus_popularity",
        "title": "Track6 G7 작품 기본 피처 + 작가 인지도 실험 결과",
        "purpose": "작품 조건을 통제한 후 작가 인지도 정보가 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 인지도", [*ARTWORK_BASIC, *POPULARITY], "작품 조건 통제 후 팔로워 수와 주요 작가 여부 추가"),
            ("작품 기본 피처 + 인지도 + 결측", [*ARTWORK_BASIC, *POPULARITY, *POPULARITY_MISSING], "인지도 값과 결측 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G8",
        "folder": "G8_basic_artwork_plus_basic_profile",
        "title": "Track6 G8 작품 기본 피처 + 기본 작가 프로필 실험 결과",
        "purpose": "작품 조건을 통제한 후 기본 작가 프로필 묶음이 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 기본 작가 프로필", [*ARTWORK_BASIC, *PROFILE], "작품 조건 통제 후 생년/전시/국적 묶음 추가"),
            ("작품 기본 피처 + 기본 작가 프로필 + 결측", [*ARTWORK_BASIC, *PROFILE, *PROFILE_MISSING], "기본 프로필과 결측 상태 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
    {
        "id": "G9",
        "folder": "G9_basic_artwork_plus_full_artist_meta",
        "title": "Track6 G9 작품 기본 피처 + 전체 작가 메타 실험 결과",
        "purpose": "작품 조건을 통제한 후 전체 작가 메타 묶음이 가격 예측력을 높이는지 확인",
        "blocks": [
            ("작품 기본 피처", ARTWORK_BASIC, "호수, 난트 재료, 난트 도구, 난트 지지체"),
            ("작품 기본 피처 + 전체 작가 메타", [*ARTWORK_BASIC, *FULL_META], "작품 조건 통제 후 작가 메타 전체 묶음 추가"),
        ],
        "comment": {"실험군": "Group G: 작가 메타/작가명 + 작품 변수"},
    },
]


def dedupe(seq: list[str]) -> list[str]:
    out = []
    for value in seq:
        if value not in out:
            out.append(value)
    return out


def write_experiment(item: dict) -> None:
    exp_dir = BASE / item["folder"]
    prompt_dir = exp_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    export_cols = dedupe([col for _, features, _ in item["blocks"] for col in features])
    numeric_cols = [col for col in ALL_NUMERIC if col in export_cols]
    config = {
        "experiment_id": item["id"],
        "title": item["title"],
        "purpose": item["purpose"],
        "description": f"Group F/G artist meta experiment: {item['id']}",
        "exp_dir": f"experiments/track6/{item['folder']}",
        "prompt_file": f"experiments/track6/{item['folder']}/prompts/used_prompt.md",
        "split_root": SPLIT_ROOT,
        "export_feature_columns": export_cols,
        "numeric_features": numeric_cols,
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
            "통제 기준": "Group G는 작품 기본 피처 묶음(ln_estimated_ho + nant_material_idx + nant_tool + nant_support)을 기준선으로 둔다.",
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
    prompt.extend(
        [
            "",
            "## 모델",
            "- Warm: Huber / Linear Regression / Ridge",
            "- Cold: Huber / Quantile-LAD / LightGBM",
            "",
            "## 평가 지표",
            "- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE",
        ]
    )
    prompt_dir.joinpath("used_prompt.md").write_text("\n".join(prompt) + "\n", encoding="utf-8")


def main() -> None:
    for item in EXPERIMENTS:
        write_experiment(item)
        print(item["id"], BASE / item["folder"])


if __name__ == "__main__":
    main()
