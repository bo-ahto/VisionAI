#!/usr/bin/env python3
"""Scaffold Track6 Group H/I/J configs after duplicate review."""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPLIT_ROOT = "data/track6_split_with_year_type_edition_size_artist_name"
BASE = REPO / "experiments" / "track6"

ARTWORK_BASIC = ["ln_estimated_ho", "nant_material_idx", "nant_tool", "nant_support"]
SIZE_EXTENDED = ["width_cm", "height_cm", "log_area", "aspect_ratio"]
EXHIBITION = [
    "artist_exhibition_solo_count",
    "artist_exhibition_group_count",
    "artist_exhibition_fair_count",
]
ACTIVITY = ["artist_meta_total_works", "artist_meta_for_sale_works"]
POPULARITY = ["artist_meta_followers", "artist_meta_is_p1"]
PROFILE = ["artist_meta_birth_year", *EXHIBITION, "artist_meta_nationality"]
PROFILE_NUMERIC = ["artist_meta_birth_year", *EXHIBITION]
FULL_META = [
    "artist_meta_birth_year",
    *EXHIBITION,
    "artist_meta_nationality",
    *ACTIVITY,
    *POPULARITY,
    "artist_meta_available_count",
    "artist_meta_completeness_score",
]
NUMERIC_BASE = [
    "ln_estimated_ho",
    "log_area",
    "depth_cm",
    "width_cm",
    "height_cm",
    "aspect_ratio",
    "artist_meta_birth_year",
    *EXHIBITION,
    *ACTIVITY,
    *POPULARITY,
    "artist_meta_available_count",
    "artist_meta_completeness_score",
]


def nn(left: str, right: str, output: str) -> dict[str, str]:
    return {"left_col": left, "right_col": right, "output_col": output}


def nc(numeric: str, category: str, prefix: str, top_n: int = 40) -> dict[str, object]:
    return {"numeric_col": numeric, "category_col": category, "output_prefix": prefix, "top_n": top_n}


def combo(cols: list[str], output: str, top_n: int = 120) -> dict[str, object]:
    return {"source_cols": cols, "combo_col": output, "top_n": top_n, "other_value": f"other_{output}"}


EXPERIMENTS = [
    {
        "id": "H1",
        "folder": "H1_artist_name_x_ln_ho",
        "title": "Track6 H1 작가명 x 호수 교차항 실험 결과",
        "purpose": "같은 호수라도 작가명에 따라 가격대가 다른지 확인",
        "export": ["artist_name_ko", "ln_estimated_ho"],
        "numeric": ["ln_estimated_ho"],
        "numeric_categorical_interactions": [nc("ln_estimated_ho", "artist_name_ko", "ln_ho_x_artist_name_ko", 80)],
        "blocks": [
            ("H1 기준: 작가명 + 호수", ["artist_name_ko", "ln_estimated_ho"], "작가명과 호수의 개별 효과만 사용"),
            (
                "H1 교차항: 작가명 x 호수",
                ["artist_name_ko", "ln_estimated_ho"],
                "작가별 호수 프리미엄 교차항 추가",
                ["ln_ho_x_artist_name_ko_"],
            ),
        ],
        "comment": {
            "실험군": "Group H: 작가명과 작품 변수 교차항",
            "해석 중심": "작가명이 포함되므로 Warm 결과를 중심으로 판단한다.",
            "중복 검토": "H2/H3/H4는 기존 D8/D9/D10과 중복되어 신규 실행하지 않고 결과 매핑한다.",
        },
    },
    {
        "id": "H5",
        "folder": "H5_artist_name_x_depth",
        "title": "Track6 H5 작가명 x 깊이 교차항 실험 결과",
        "purpose": "같은 3D/깊이 조건이라도 작가명에 따라 가격 효과가 다른지 확인",
        "export": ["artist_name_ko", "depth_cm"],
        "numeric": ["depth_cm"],
        "numeric_categorical_interactions": [nc("depth_cm", "artist_name_ko", "depth_x_artist_name_ko", 80)],
        "blocks": [
            ("H5 기준: 작가명 + 깊이", ["artist_name_ko", "depth_cm"], "작가명과 깊이의 개별 효과만 사용"),
            (
                "H5 교차항: 작가명 x 깊이",
                ["artist_name_ko", "depth_cm"],
                "작가별 입체성 프리미엄 교차항 추가",
                ["depth_x_artist_name_ko_"],
            ),
        ],
        "comment": {
            "실험군": "Group H: 작가명과 작품 변수 교차항",
            "해석 중심": "작가명이 포함되므로 Warm 결과를 중심으로 판단한다.",
        },
    },
    {
        "id": "I1",
        "folder": "I1_ho_birth_exhibition_cold_candidate",
        "title": "Track6 I1 호수 + 세대/경력 메타 실험 결과",
        "purpose": "호수와 세대/경력 메타를 함께 쓰면 작가명 없이도 가격 예측력이 높아지는지 확인",
        "export": ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION],
        "numeric": ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION],
        "blocks": [
            ("I1 기준: 호수 only", ["ln_estimated_ho"], "최소 크기 피처만 사용"),
            ("I1 후보: 호수 + 세대/경력", ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION], "작가명 없는 최소 메타 조합 추가"),
        ],
        "comment": {"실험군": "Group I: 작가명 없는 Cold 후보 조합", "해석 중심": "Cold 결과 중심으로 판단한다."},
    },
    {
        "id": "I2",
        "folder": "I2_basic_artwork_birth_exhibition_cold_candidate",
        "title": "Track6 I2 작품 기본 피처 + 세대/경력 메타 실험 결과",
        "purpose": "작품 기본 피처와 세대/경력 메타를 함께 쓰면 Cold 예측력이 개선되는지 확인",
        "export": [*ARTWORK_BASIC, "artist_meta_birth_year", *EXHIBITION],
        "numeric": ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION],
        "blocks": [
            ("I2 기준: 작품 기본 피처", ARTWORK_BASIC, "호수 + 난트 재료/도구/지지체"),
            ("I2 후보: 작품 기본 피처 + 세대/경력", [*ARTWORK_BASIC, "artist_meta_birth_year", *EXHIBITION], "작품 기본 피처에 생년/전시 횟수 추가"),
        ],
        "comment": {"실험군": "Group I: 작가명 없는 Cold 후보 조합", "해석 중심": "Cold 결과 중심으로 판단한다."},
    },
    {
        "id": "I3",
        "folder": "I3_basic_artwork_activity_popularity_cold_candidate",
        "title": "Track6 I3 작품 기본 피처 + 활동량/인지도 메타 실험 결과",
        "purpose": "작품 기본 변수와 활동량/인지도 메타를 함께 쓰면 시장 노출 정도가 가격 예측에 도움 되는지 확인",
        "export": [*ARTWORK_BASIC, *ACTIVITY, *POPULARITY],
        "numeric": ["ln_estimated_ho", *ACTIVITY, *POPULARITY],
        "blocks": [
            ("I3 기준: 작품 기본 피처", ARTWORK_BASIC, "호수 + 난트 재료/도구/지지체"),
            ("I3 후보: 작품 기본 피처 + 활동량/인지도", [*ARTWORK_BASIC, *ACTIVITY, *POPULARITY], "시장 노출 메타 추가"),
        ],
        "comment": {"실험군": "Group I: 작가명 없는 Cold 후보 조합", "해석 중심": "Cold 결과 중심으로 판단한다."},
    },
    {
        "id": "I5",
        "folder": "I5_basic_artwork_market_exposure_information",
        "title": "Track6 I5 작품 기본 피처 + 시장 노출/정보량 실험 결과",
        "purpose": "작품 기본 변수에 시장 노출/정보량 피처를 더하면 큰 오차 구간을 줄이는지 확인",
        "export": [*ARTWORK_BASIC, *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
        "numeric": ["ln_estimated_ho", *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
        "blocks": [
            ("I5 기준: 작품 기본 피처", ARTWORK_BASIC, "호수 + 난트 재료/도구/지지체"),
            (
                "I5 후보: 작품 기본 피처 + 시장 노출/정보량",
                [*ARTWORK_BASIC, *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
                "활동량/인지도와 메타 정보량 추가",
            ),
        ],
        "comment": {"실험군": "Group I: 작가명 없는 Cold 후보 조합", "해석 중심": "Cold MdAPE와 p95 APE를 함께 본다."},
    },
    {
        "id": "I6",
        "folder": "I6_extended_size_full_artist_meta",
        "title": "Track6 I6 실제 크기 확장 + 전체 작가 메타 실험 결과",
        "purpose": "실제 크기 정보와 전체 작가 메타 묶음을 함께 쓰면 호수 중심 모델보다 안정적인지 확인",
        "export": [*SIZE_EXTENDED, *FULL_META],
        "numeric": [*SIZE_EXTENDED, "artist_meta_birth_year", *EXHIBITION, *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
        "blocks": [
            ("I6 기준: 실제 크기 확장", SIZE_EXTENDED, "가로/세로/면적/비율만 사용"),
            ("I6 후보: 실제 크기 확장 + 전체 작가 메타", [*SIZE_EXTENDED, *FULL_META], "실제 크기 확장 피처에 전체 작가 메타 추가"),
        ],
        "comment": {"실험군": "Group I: 작가명 없는 Cold 후보 조합", "해석 중심": "Cold 결과 중심으로 판단한다."},
    },
    {
        "id": "J1",
        "folder": "J1_profile_x_ln_ho",
        "title": "Track6 J1 세대/경력 x 호수 교차항 실험 결과",
        "purpose": "작가의 세대/경력 단계에 따라 호수 효과가 다르게 나타나는지 확인",
        "export": ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION],
        "numeric": ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION],
        "numeric_numeric_interactions": [
            nn("artist_meta_birth_year", "ln_estimated_ho", "birth_year_x_ln_ho"),
            *[nn(col, "ln_estimated_ho", f"{col}_x_ln_ho") for col in EXHIBITION],
        ],
        "blocks": [
            ("J1 기준: 호수 + 세대/경력", ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION], "개별 효과만 사용"),
            (
                "J1 교차항: 세대/경력 x 호수",
                ["ln_estimated_ho", "artist_meta_birth_year", *EXHIBITION, "birth_year_x_ln_ho", *[f"{col}_x_ln_ho" for col in EXHIBITION]],
                "세대/경력별 호수 프리미엄 추가",
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항", "해석 중심": "Cold 후보 가능성 중심으로 판단한다."},
    },
    {
        "id": "J2",
        "folder": "J2_profile_x_material",
        "title": "Track6 J2 세대/경력 x 재료 교차항 실험 결과",
        "purpose": "작가의 세대/경력 단계에 따라 재료 효과가 다르게 나타나는지 확인",
        "export": ["artist_meta_birth_year", *EXHIBITION, "nant_material_idx", "nant_tool"],
        "numeric": ["artist_meta_birth_year", *EXHIBITION],
        "numeric_categorical_interactions": [
            *[nc(col, "nant_material_idx", f"{col}_x_nant_material_idx", 35) for col in PROFILE_NUMERIC],
            *[nc(col, "nant_tool", f"{col}_x_nant_tool", 35) for col in PROFILE_NUMERIC],
        ],
        "blocks": [
            ("J2 기준: 세대/경력 + 재료", ["artist_meta_birth_year", *EXHIBITION, "nant_material_idx", "nant_tool"], "개별 효과만 사용"),
            (
                "J2 교차항: 세대/경력 x 재료",
                ["artist_meta_birth_year", *EXHIBITION, "nant_material_idx", "nant_tool"],
                "세대/경력별 재료 프리미엄 추가",
                [f"{col}_x_nant_material_idx_" for col in PROFILE_NUMERIC] + [f"{col}_x_nant_tool_" for col in PROFILE_NUMERIC],
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
    {
        "id": "J3",
        "folder": "J3_profile_x_support",
        "title": "Track6 J3 세대/경력 x 지지체 교차항 실험 결과",
        "purpose": "작가의 세대/경력 단계에 따라 난트 지지체 효과가 다르게 나타나는지 확인",
        "export": ["artist_meta_birth_year", *EXHIBITION, "nant_support"],
        "numeric": ["artist_meta_birth_year", *EXHIBITION],
        "numeric_categorical_interactions": [*[nc(col, "nant_support", f"{col}_x_nant_support", 35) for col in PROFILE_NUMERIC]],
        "blocks": [
            ("J3 기준: 세대/경력 + 지지체", ["artist_meta_birth_year", *EXHIBITION, "nant_support"], "개별 효과만 사용"),
            (
                "J3 교차항: 세대/경력 x 지지체",
                ["artist_meta_birth_year", *EXHIBITION, "nant_support"],
                "세대/경력별 지지체 프리미엄 추가",
                [f"{col}_x_nant_support_" for col in PROFILE_NUMERIC],
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
    {
        "id": "J4",
        "folder": "J4_activity_popularity_x_ln_ho",
        "title": "Track6 J4 활동량/인지도 x 호수 교차항 실험 결과",
        "purpose": "작가의 활동량/인지도에 따라 호수 효과가 다르게 나타나는지 확인",
        "export": ["ln_estimated_ho", *ACTIVITY, *POPULARITY],
        "numeric": ["ln_estimated_ho", *ACTIVITY, *POPULARITY],
        "numeric_numeric_interactions": [*[nn(col, "ln_estimated_ho", f"{col}_x_ln_ho") for col in [*ACTIVITY, *POPULARITY]]],
        "blocks": [
            ("J4 기준: 활동량/인지도 + 호수", ["ln_estimated_ho", *ACTIVITY, *POPULARITY], "개별 효과만 사용"),
            (
                "J4 교차항: 활동량/인지도 x 호수",
                ["ln_estimated_ho", *ACTIVITY, *POPULARITY, *[f"{col}_x_ln_ho" for col in [*ACTIVITY, *POPULARITY]]],
                "시장 노출 수준별 호수 프리미엄 추가",
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
    {
        "id": "J5",
        "folder": "J5_activity_popularity_x_log_area",
        "title": "Track6 J5 활동량/인지도 x 면적 교차항 실험 결과",
        "purpose": "작가의 활동량/인지도에 따라 면적 효과가 다르게 나타나는지 확인",
        "export": ["log_area", *ACTIVITY, *POPULARITY],
        "numeric": ["log_area", *ACTIVITY, *POPULARITY],
        "numeric_numeric_interactions": [*[nn(col, "log_area", f"{col}_x_log_area") for col in [*ACTIVITY, *POPULARITY]]],
        "blocks": [
            ("J5 기준: 활동량/인지도 + 면적", ["log_area", *ACTIVITY, *POPULARITY], "개별 효과만 사용"),
            (
                "J5 교차항: 활동량/인지도 x 면적",
                ["log_area", *ACTIVITY, *POPULARITY, *[f"{col}_x_log_area" for col in [*ACTIVITY, *POPULARITY]]],
                "시장 노출 수준별 대형작 프리미엄 추가",
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
    {
        "id": "J6",
        "folder": "J6_profile_x_material",
        "title": "Track6 J6 기본 프로필 x 재료 교차항 실험 결과",
        "purpose": "작가 기본 프로필에 따라 재료 효과가 다르게 나타나는지 확인",
        "export": [*PROFILE, "nant_material_idx", "nant_tool"],
        "numeric": PROFILE_NUMERIC,
        "combo_features": [
            combo(["artist_meta_nationality", "nant_material_idx"], "nationality_material_idx_combo", 120),
            combo(["artist_meta_nationality", "nant_tool"], "nationality_tool_combo", 120),
        ],
        "numeric_categorical_interactions": [
            *[nc(col, "nant_material_idx", f"{col}_x_nant_material_idx", 35) for col in PROFILE_NUMERIC],
            *[nc(col, "nant_tool", f"{col}_x_nant_tool", 35) for col in PROFILE_NUMERIC],
        ],
        "blocks": [
            ("J6 기준: 기본 프로필 + 재료", [*PROFILE, "nant_material_idx", "nant_tool"], "개별 효과만 사용"),
            (
                "J6 교차항: 기본 프로필 x 재료",
                [*PROFILE, "nant_material_idx", "nant_tool", "nationality_material_idx_combo", "nationality_tool_combo"],
                "세대/경력/국적별 재료 프리미엄 추가",
                [f"{col}_x_nant_material_idx_" for col in PROFILE_NUMERIC] + [f"{col}_x_nant_tool_" for col in PROFILE_NUMERIC],
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
    {
        "id": "J7",
        "folder": "J7_market_exposure_x_depth",
        "title": "Track6 J7 시장 노출/정보량 x 깊이 교차항 실험 결과",
        "purpose": "작가의 시장 노출/정보량에 따라 입체성 효과가 다르게 나타나는지 확인",
        "export": ["depth_cm", *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
        "numeric": ["depth_cm", *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"],
        "numeric_numeric_interactions": [
            *[nn(col, "depth_cm", f"{col}_x_depth") for col in [*ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"]]
        ],
        "blocks": [
            ("J7 기준: 시장 노출/정보량 + 깊이", ["depth_cm", *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"], "개별 효과만 사용"),
            (
                "J7 교차항: 시장 노출/정보량 x 깊이",
                ["depth_cm", *ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score", *[f"{col}_x_depth" for col in [*ACTIVITY, *POPULARITY, "artist_meta_available_count", "artist_meta_completeness_score"]]],
                "시장 노출/정보량별 입체성 프리미엄 추가",
            ),
        ],
        "comment": {"실험군": "Group J: 작가 메타와 작품 변수 교차항"},
    },
]


MAPPED = [
    ("H2", "D8", "artist_name_ko x log_area", "기존 D8 artist_name x log_area 숫자형 교차항 결과를 매핑"),
    ("H3", "D9", "artist_name_ko x nant_material_idx/nant_tool", "기존 D9 artist_name x 재료 조합 결과를 매핑"),
    ("H4", "D10", "artist_name_ko x nant_support", "기존 D10 artist_name x 지지체 조합 결과를 매핑"),
    ("I4", "G8", "작품 기본 피처 + 생년/전시/국적", "기존 G8 작품 기본 피처 + 기본 작가 프로필 결과를 매핑"),
]


def dedupe(values: list[str]) -> list[str]:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def generated_outputs(item: dict) -> list[str]:
    outputs = []
    for combo_item in item.get("combo_features", []):
        outputs.append(combo_item["combo_col"])
    for interaction in item.get("numeric_numeric_interactions", []):
        outputs.append(interaction["output_col"])
    for interaction in item.get("numeric_categorical_interactions", []):
        top_n = int(interaction.get("top_n", 20))
        outputs.extend(f"{interaction['output_prefix']}_{i:02d}" for i in range(1, top_n + 1))
    return outputs


def write_experiment(item: dict) -> None:
    exp_dir = BASE / item["folder"]
    prompt_dir = exp_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    export_cols = dedupe([*item["export"], *generated_outputs(item)])
    numeric_cols = dedupe([*item["numeric"], *[x["output_col"] for x in item.get("numeric_numeric_interactions", [])], *generated_outputs({"numeric_categorical_interactions": item.get("numeric_categorical_interactions", [])})])
    variable_blocks = []
    for block in item["blocks"]:
        name, features, description = block[:3]
        row = {"name": name, "features": features, "description": description}
        if len(block) > 3:
            row["feature_prefixes"] = block[3]
        variable_blocks.append(row)
    config = {
        "experiment_id": item["id"],
        "title": item["title"],
        "purpose": item["purpose"],
        "description": f"Track6 Group H/I/J experiment: {item['id']}",
        "exp_dir": f"experiments/track6/{item['folder']}",
        "prompt_file": f"experiments/track6/{item['folder']}/prompts/used_prompt.md",
        "split_root": SPLIT_ROOT,
        "export_feature_columns": export_cols,
        "numeric_features": numeric_cols,
        "variable_blocks": variable_blocks,
        "comment": {
            "실험 목적": item["purpose"],
            "학습 피처": " / ".join(", ".join(block[1]) for block in item["blocks"]),
            "테스트 피처": "학습 피처와 동일",
            "사용 모델": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
            "데이터 기준": "작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.",
            "평가 지표": "R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE",
            **item["comment"],
        },
    }
    for key in ["combo_features", "numeric_categorical_interactions", "numeric_numeric_interactions"]:
        if item.get(key):
            config[key] = item[key]
    (exp_dir / "experiment_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
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
        "- 교차항은 설정 파일에 명시한 방식으로만 생성",
        "",
        "## 사용 피처",
    ]
    for block in item["blocks"]:
        prompt.append(f"- {block[0]}: `{', '.join(block[1])}` - {block[2]}")
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


def write_mapping_doc() -> None:
    out = REPO / "docs" / "track6" / "experiments" / "group_h_i_j_duplicate_mapping.md"
    lines = [
        "# Track6 Group H/I/J 중복 매핑 검토",
        "",
        "- 목적: H/I/J 신규 제안 중 기존 실험과 중복되는 항목을 재실행하지 않고 기존 결과에 매핑",
        "",
        "| 신규 라벨 | 매핑 실험 | 피처 | 처리 |",
        "|---|---|---|---|",
    ]
    for new_id, old_id, features, note in MAPPED:
        lines.append(f"| {new_id} | {old_id} | `{features}` | {note} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)


def main() -> None:
    for item in EXPERIMENTS:
        write_experiment(item)
        print(item["id"], BASE / item["folder"])
    write_mapping_doc()


if __name__ == "__main__":
    main()
