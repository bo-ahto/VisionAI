#!/usr/bin/env python3
"""Create Track6 per-variable screening experiment journals."""
from __future__ import annotations

import html
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_INDEX = REPO / "docs" / "track6" / "journals" / "variable_screening.html"

SOURCE_FILE = "data/track6/track6_feature_candidates_name_corrected.csv"
JOIN_KEY = "_track6_row_id"


EXPERIMENTS = [
    {
        "id": "T6-E054",
        "slug": "artist_name_variable_check",
        "title": "작가명 변수 영향 확인",
        "variable": "artist_name_ko",
        "hypothesis": "작가명 변수는 Warm 가격 예측에 영향을 미친다.",
        "warm_base": "ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho",
        "cold_base": "실험 제외",
        "cold_add": "실험 제외",
        "compare": "Warm에서 호수 only 모델과 작가명+호수 모델을 비교한다.",
        "note": "작가명은 작품 변수는 아니지만 Warm 기준 성능을 설명하기 위해 별도 확인한다.",
        "cold_excluded": "true",
        "cold_exclusion_reason": "Cold는 학습 데이터에 없는 신규 작가 예측 상황이므로 작가명을 직접 쓰면 학습된 작가 가격대를 활용할 수 없다.",
    },
    {
        "id": "T6-E055",
        "slug": "width_height_variable_check",
        "title": "가로/세로 변수 영향 확인",
        "variable": "width_cm + height_cm",
        "hypothesis": "가로와 세로 변수는 호수만 사용할 때보다 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + width_cm + height_cm",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + width_cm + height_cm",
        "compare": "호수 기준 모델과 가로/세로 추가 모델을 비교한다.",
        "note": "가로/세로는 사용자가 운영 단계에서 입력 가능한 기본 크기 정보다.",
    },
    {
        "id": "T6-E056",
        "slug": "area_log_area_variable_check",
        "title": "면적/로그면적 변수 영향 확인",
        "variable": "area_cm2 + log_area",
        "hypothesis": "면적과 로그면적 변수는 작품 크기 효과를 정리해 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + area_cm2 + log_area",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + area_cm2 + log_area",
        "compare": "호수 기준 모델과 면적/로그면적 추가 모델을 비교한다.",
        "note": "면적은 가로와 세로에서 생성되는 파생 변수이므로 중복 효과를 함께 확인한다.",
    },
    {
        "id": "T6-E057",
        "slug": "aspect_ratio_variable_check",
        "title": "가로세로 비율 변수 영향 확인",
        "variable": "aspect_ratio",
        "hypothesis": "가로세로 비율 변수는 같은 크기라도 형태 차이에 따른 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + aspect_ratio",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + aspect_ratio",
        "compare": "호수 기준 모델과 가로세로 비율 추가 모델을 비교한다.",
        "note": "극단 비율 여부는 후속 실험에서 별도로 확인한다.",
    },
    {
        "id": "T6-E058",
        "slug": "medium_category_variable_check",
        "title": "재료 대분류 변수 영향 확인",
        "variable": "medium_category",
        "hypothesis": "재료 대분류 변수는 작품 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + medium_category",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + medium_category",
        "compare": "호수 기준 모델과 재료 대분류 추가 모델을 비교한다.",
        "note": "재료는 운영 입력 가능성이 높은 핵심 작품 변수다.",
    },
    {
        "id": "T6-E059",
        "slug": "support_category_variable_check",
        "title": "지지체 대분류 변수 영향 확인",
        "variable": "support_category",
        "hypothesis": "지지체 대분류 변수는 작품 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + support_category",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + support_category",
        "compare": "호수 기준 모델과 지지체 대분류 추가 모델을 비교한다.",
        "note": "캔버스, 종이, 패널 등 지지체 차이의 설명력을 확인한다.",
    },
    {
        "id": "T6-E060",
        "slug": "medium_support_bucket_variable_check",
        "title": "재료+지지체 조합 변수 영향 확인",
        "variable": "medium_support_bucket",
        "hypothesis": "재료와 지지체 조합 변수는 재료나 지지체를 따로 쓰는 것보다 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho + medium_category + support_category",
        "warm_add": "artist_name_ko + ln_estimated_ho + medium_support_bucket",
        "cold_base": "ln_estimated_ho + medium_category + support_category",
        "cold_add": "ln_estimated_ho + medium_support_bucket",
        "compare": "재료/지지체 단독 모델과 재료+지지체 조합 모델을 비교한다.",
        "note": "조합 변수는 희소해질 수 있으므로 p95 APE도 함께 확인한다.",
    },
    {
        "id": "T6-E061",
        "slug": "depth_variable_check",
        "title": "깊이 변수 영향 확인",
        "variable": "depth_cm",
        "hypothesis": "깊이 변수는 입체성이 있는 작품의 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + depth_cm",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + depth_cm",
        "compare": "호수 기준 모델과 깊이 추가 모델을 비교하고 2D/3D 구간별 오차를 확인한다.",
        "note": "깊이 결측과 0값 처리 기준을 함께 기록한다.",
    },
    {
        "id": "T6-E062",
        "slug": "three_d_flag_variable_check",
        "title": "3D 후보 플래그 변수 영향 확인",
        "variable": "has_depth + is_3d_candidate",
        "hypothesis": "3D 후보 플래그 변수는 2D 작품과 3D 작품의 가격 예측 차이를 설명한다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + has_depth + is_3d_candidate",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + has_depth + is_3d_candidate",
        "compare": "호수 기준 모델과 3D 후보 플래그 추가 모델을 비교한다.",
        "note": "has_depth와 is_3d_candidate는 수집값이 아니라 생성 변수다.",
    },
    {
        "id": "T6-E063",
        "slug": "nant_material_idx_variable_check",
        "title": "난트 재료 번호 변수 영향 확인",
        "variable": "nant_material_idx",
        "hypothesis": "난트 재료 번호 변수는 재료 대분류보다 더 세밀하게 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho + medium_category",
        "warm_add": "artist_name_ko + ln_estimated_ho + medium_category + nant_material_idx",
        "cold_base": "ln_estimated_ho + medium_category",
        "cold_add": "ln_estimated_ho + medium_category + nant_material_idx",
        "compare": "재료 대분류 모델과 난트 재료 번호 추가 모델을 비교한다.",
        "note": "분류 번호가 너무 세분화되어 과적합되는지 함께 확인한다.",
    },
    {
        "id": "T6-E064",
        "slug": "nant_support_tool_variable_check",
        "title": "난트 지지체/도구 변수 영향 확인",
        "variable": "nant_support + nant_tool",
        "hypothesis": "난트 지지체와 도구 변수는 표준 재료/지지체 분류보다 추가적인 가격 설명 정보를 제공한다.",
        "warm_base": "artist_name_ko + ln_estimated_ho + medium_category + support_category",
        "warm_add": "artist_name_ko + ln_estimated_ho + medium_category + support_category + nant_support + nant_tool",
        "cold_base": "ln_estimated_ho + medium_category + support_category",
        "cold_add": "ln_estimated_ho + medium_category + support_category + nant_support + nant_tool",
        "compare": "표준 재료/지지체 모델과 난트 지지체/도구 추가 모델을 비교한다.",
        "note": "난트 분류는 운영 입력값이 아니라 정제 파이프라인에서 생성되는 표준화 값이다.",
    },
    {
        "id": "T6-E065",
        "slug": "raw_material_text_variable_check",
        "title": "원본 재료 문구 변수 영향 확인",
        "variable": "collected_material_raw",
        "hypothesis": "원본 재료 문구에서 만든 키워드 변수는 표준 재료 분류가 놓친 가격 차이를 설명한다.",
        "warm_base": "artist_name_ko + ln_estimated_ho + medium_category",
        "warm_add": "artist_name_ko + ln_estimated_ho + medium_category + collected_material_raw keyword flags",
        "cold_base": "ln_estimated_ho + medium_category",
        "cold_add": "ln_estimated_ho + medium_category + collected_material_raw keyword flags",
        "compare": "표준 재료 모델과 원본 재료 문구 키워드 추가 모델을 비교한다.",
        "note": "원본 문구는 그대로 쓰지 않고 키워드 flag로 변환해 사용한다.",
    },
    {
        "id": "T6-E066",
        "slug": "title_text_variable_check",
        "title": "작품 제목 문구 변수 영향 확인",
        "variable": "title_raw",
        "hypothesis": "작품 제목에서 만든 키워드 변수는 에디션, 세트, 포스터 같은 가격 차이를 설명한다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + title_raw keyword flags",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + title_raw keyword flags",
        "compare": "기준 모델과 제목 키워드 추가 모델을 비교한다.",
        "note": "제목 원문은 그대로 쓰지 않고 운영 가능한 키워드 flag로 변환한다.",
    },
    {
        "id": "T6-E067",
        "slug": "artist_works_log_variable_check",
        "title": "작가별 데이터 보유 작품 수 변수 영향 확인",
        "variable": "artist_works_log",
        "hypothesis": "작가별 데이터 보유 작품 수 변수는 Warm 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_works_log",
        "cold_base": "실험 제외",
        "cold_add": "실험 제외",
        "compare": "Warm에서 작가명+호수 모델과 작가별 데이터 보유 작품 수 추가 모델을 비교한다.",
        "note": "artist_works_log는 수집값이 아니라 데이터셋 안에서 작가별 작품 수를 계산한 뒤 로그 변환한 생성 변수다.",
        "cold_excluded": "true",
        "cold_exclusion_reason": "Cold는 학습 데이터에 없는 신규 작가 예측 상황이므로 해당 작가의 데이터 보유 작품 수를 학습 데이터에서 계산할 수 없어 비교 의미가 없다.",
    },
    {
        "id": "T6-E073",
        "slug": "artist_birth_year_variable_check",
        "title": "작가 생년 변수 영향 확인",
        "variable": "artist_meta_birth_year",
        "hypothesis": "작가 생년 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_birth_year",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_birth_year",
        "compare": "기준 모델과 작가 생년 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "생년은 작가 DB에서 비교적 표준화하기 쉬운 메타 후보지만 결측률을 함께 확인한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_birth_year_is_missing",
        "present_condition": "artist_meta_birth_year 값이 있는 작품",
        "missing_condition": "artist_meta_birth_year 값이 비어 있는 작품",
        "dataset_detail": "생년은 숫자형 원값으로 두고, 결측 작품은 결측 flag로 구분한다. 생년을 임의로 평균값으로 채우기 전에 원값 추가 효과를 먼저 본다.",
        "collection_decision": "생년 추가 모델이 전체와 생년 있음 구간에서 개선되면 작가 DB 생년 보강 후보로 둔다.",
    },
    {
        "id": "T6-E075",
        "slug": "artist_career_stage_variable_check",
        "title": "작가 경력 단계 변수 영향 확인",
        "variable": "artist_meta_career_stage",
        "hypothesis": "작가 경력 단계 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_career_stage",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_career_stage",
        "compare": "기준 모델과 작가 경력 단계 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "경력 단계는 경력 연차를 구간화한 변수이므로 연속값보다 안정적인지 확인한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_career_stage_is_missing",
        "present_condition": "artist_meta_career_stage 값이 있는 작품",
        "missing_condition": "artist_meta_career_stage 값이 비어 있는 작품",
        "dataset_detail": "경력 단계는 범주형 원값으로 사용하고, 결측은 unknown으로 합치기 전에 별도 결측 flag로 분리한다.",
        "collection_decision": "경력 단계가 개선되면 생년 또는 활동 시작 연도 기반 경력 단계 생성 로직을 보강한다.",
    },
    {
        "id": "T6-E076",
        "slug": "artist_nationality_variable_check",
        "title": "작가 국적 변수 영향 확인",
        "variable": "artist_meta_nationality",
        "hypothesis": "작가 국적 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_nationality",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_nationality",
        "compare": "기준 모델과 작가 국적 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "한글 국적 컬럼은 결측이 많아 보류하고, 현재는 수집 원본 국적 컬럼으로 먼저 확인한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_nationality_is_missing",
        "present_condition": "artist_meta_nationality 값이 있는 작품",
        "missing_condition": "artist_meta_nationality 값이 비어 있는 작품",
        "dataset_detail": "국적은 현재 수집 원본 국적 컬럼을 범주형으로 사용한다. 한글 국적 컬럼은 결측이 많아 이번 실험에서는 쓰지 않는다.",
        "collection_decision": "원본 국적이 개선되면 한글 국적 표준화와 다국적/미상 처리 규칙을 후속 정제로 보강한다.",
    },
    {
        "id": "T6-E078",
        "slug": "artist_total_works_variable_check",
        "title": "작가 등록 작품 수 변수 영향 확인",
        "variable": "artist_meta_total_works",
        "hypothesis": "작가 등록 작품 수 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_total_works",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_total_works",
        "compare": "기준 모델과 작가 등록 작품 수 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "등록 작품 수는 수집 출처의 규모 편향이 있을 수 있어 성능과 운영 재현성을 함께 본다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_total_works_is_missing",
        "present_condition": "artist_meta_total_works 값이 있는 작품",
        "missing_condition": "artist_meta_total_works 값이 비어 있는 작품",
        "dataset_detail": "등록 작품 수는 숫자형 원값과 필요 시 로그 변환 후보를 구분해 기록한다. 이번 일지는 원값 추가 효과를 먼저 본다.",
        "collection_decision": "등록 작품 수가 개선되면 작가 DB에서 작품 수를 안정적으로 갱신할 수 있는지 운영 가능성을 검토한다.",
    },
    {
        "id": "T6-E079",
        "slug": "artist_for_sale_works_variable_check",
        "title": "작가 판매 중 작품 수 변수 영향 확인",
        "variable": "artist_meta_for_sale_works",
        "hypothesis": "작가 판매 중 작품 수 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_for_sale_works",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_for_sale_works",
        "compare": "기준 모델과 작가 판매 중 작품 수 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "판매 중 작품 수는 시점에 따라 바뀌는 값이므로 운영에서 갱신 가능해야 한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_for_sale_works_is_missing",
        "present_condition": "artist_meta_for_sale_works 값이 있는 작품",
        "missing_condition": "artist_meta_for_sale_works 값이 비어 있는 작품",
        "dataset_detail": "판매 중 작품 수는 시점에 따라 변하는 숫자형 변수이므로, 원값과 결측 flag를 함께 두고 데이터 기준일을 결과에 기록한다.",
        "collection_decision": "판매 중 작품 수가 개선되면 운영에서 주기적으로 갱신 가능한 수집 항목인지 검토한다.",
    },
    {
        "id": "T6-E081",
        "slug": "artist_followers_variable_check",
        "title": "작가 팔로워 수 변수 영향 확인",
        "variable": "artist_meta_followers",
        "hypothesis": "작가 팔로워 수 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_followers",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_followers",
        "compare": "기준 모델과 작가 팔로워 수 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "팔로워 수는 특정 플랫폼 의존성이 커서 성능이 좋아도 운영 채택은 별도로 판단한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_followers_is_missing",
        "present_condition": "artist_meta_followers 값이 있는 작품",
        "missing_condition": "artist_meta_followers 값이 비어 있는 작품",
        "dataset_detail": "팔로워 수는 플랫폼 의존 숫자형 변수다. 원값 추가 효과를 먼저 보고, 큰 값 쏠림이 있으면 후속 실험에서 로그 변환을 검토한다.",
        "collection_decision": "팔로워 수가 개선되더라도 특정 플랫폼 편향이 크면 최종 피처가 아니라 참고 피처로 보류한다.",
    },
    {
        "id": "T6-E082",
        "slug": "artist_p1_flag_variable_check",
        "title": "플랫폼 주요 작가 여부 변수 영향 확인",
        "variable": "artist_meta_is_p1",
        "hypothesis": "플랫폼 주요 작가 여부 변수는 가격 예측에 영향을 미친다.",
        "warm_base": "artist_name_ko + ln_estimated_ho",
        "warm_add": "artist_name_ko + ln_estimated_ho + artist_meta_is_p1",
        "cold_base": "ln_estimated_ho",
        "cold_add": "ln_estimated_ho + artist_meta_is_p1",
        "compare": "기준 모델과 플랫폼 주요 작가 여부 변수 추가 모델을 Warm/Cold에서 각각 비교한다.",
        "note": "플랫폼 주요 작가 여부는 출처 편향 가능성이 높은 변수라 성능과 재현 가능성을 분리 판단한다.",
        "artist_meta_missing_check": "true",
        "missing_flag": "artist_meta_is_p1_is_missing",
        "present_condition": "artist_meta_is_p1 값이 있는 작품",
        "missing_condition": "artist_meta_is_p1 값이 비어 있는 작품",
        "dataset_detail": "플랫폼 주요 작가 여부는 이진 flag로 사용한다. 값이 없을 때 0으로 단순 처리하지 않고 결측 flag를 별도로 둔다.",
        "collection_decision": "플랫폼 주요 작가 여부가 개선되더라도 출처 편향이 크면 운영 최종 피처로 바로 채택하지 않는다.",
    },
]


STYLE = """
:root{--paper:#fffdf7;--ink:#1d251f;--line:#d8cdb8;--muted:#687268;--green:#27684a;--amber:#9b6124}
body{margin:0;color:var(--ink);background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7);font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.62}
main{max-width:1120px;margin:0 auto;padding:32px 22px 72px}
header,section{background:rgba(255,253,247,.96);border:1px solid var(--line);border-radius:24px;padding:26px;margin-top:18px;box-shadow:0 12px 34px rgba(42,34,22,.08)}
h1{margin:0;font-size:40px;letter-spacing:-.055em}h2{margin:0 0 12px;font-size:22px;letter-spacing:-.03em}
ul{margin:8px 0 0;padding-left:21px}code{background:#eee5d4;border-radius:7px;padding:2px 6px;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;background:var(--paper)}th,td{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}th{background:#eadfcd}
.badge{display:inline-flex;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:800;margin-right:6px}.planned{background:rgba(155,97,36,.14);color:var(--amber)}.goal{background:rgba(39,104,74,.14);color:var(--green)}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:16px}
a{color:#174f73;font-weight:800}
"""


def esc(value: str) -> str:
    return html.escape(value)


def render_log(item: dict[str, str]) -> str:
    is_cold_excluded = item.get("cold_excluded") == "true"
    needs_artist_meta_missing_check = item.get("artist_meta_missing_check") == "true"
    missing_flag = item.get("missing_flag", f"{item['variable']}_is_missing")
    present_condition = item.get("present_condition", f"{item['variable']} 값이 있는 작품")
    missing_condition = item.get("missing_condition", f"{item['variable']} 값이 비어 있는 작품")
    dataset_detail = item.get(
        "dataset_detail",
        "원값 피처와 결측 여부 피처를 함께 생성하고, 결측 작품을 제거하지 않는다.",
    )
    collection_decision = item.get(
        "collection_decision",
        "성능 개선이 확인될 때만 결측 처리와 추가 수집을 검토한다.",
    )
    cold_exclusion_reason = item.get(
        "cold_exclusion_reason",
        "Cold는 학습 데이터에 없는 신규 작가 예측 상황이므로 해당 작가 변수가 과거 가격 정보를 제공하지 못한다.",
    )
    artist_meta_missing_section = (
        f"""<section>
    <h2>6. 작가 메타 결측/수집 가치 판단</h2>
    <ul>
      <li>먼저 볼 것: <code>{esc(item['variable'])}</code>가 가격 예측에 실제로 영향을 주는지 확인한다.</li>
      <li>1차 판단: 기준 모델보다 <code>median APE</code> 또는 <code>p95 APE</code>가 낮아지는지 본다.</li>
      <li>2차 판단: 전체 데이터, <code>{esc(present_condition)}</code>, <code>{esc(missing_condition)}</code> 구간을 나눠 성능을 확인한다.</li>
      <li>결측 처리 판단: 성능 개선이 확인될 때만 결측 대체값, 결측 여부 flag, 추가 수집을 검토한다.</li>
      <li>수집 가치 판단: {esc(collection_decision)}</li>
      <li>운영 판단: 작가 DB로 안정적으로 다시 만들 수 없는 변수는 성능이 좋아도 최종 피처 채택을 보류한다.</li>
    </ul>
  </section>"""
        if needs_artist_meta_missing_check
        else ""
    )
    artist_meta_dataset_section = (
        f"""<section>
    <h2>3. 작가 메타 실험용 데이터셋 구축 기준</h2>
    <ul>
      <li>기본 split은 바꾸지 않는다. 메타 정보가 없다는 이유로 train/test 작품을 제거하지 않는다.</li>
      <li>변수 효과와 결측 영향을 분리하기 위해 원값과 결측 상태를 함께 생성한다.</li>
      <li>원값 피처: <code>{esc(item['variable'])}</code></li>
      <li>결측 여부 피처: <code>{esc(missing_flag)}</code></li>
      <li>값 있음 구간: <code>{esc(present_condition)}</code></li>
      <li>값 없음 구간: <code>{esc(missing_condition)}</code></li>
      <li>정보량 피처: 사용 가능한 작가 메타 개수와 비율을 <code>artist_meta_available_count</code>, <code>artist_meta_completeness_score</code>로 기록한다.</li>
      <li>변수별 처리 기준: {esc(dataset_detail)}</li>
      <li>학습/테스트 파일에는 같은 피처 컬럼을 둔다. 값이 없으면 빈값 또는 정해진 결측값으로 두고, <code>{esc(missing_flag)}</code>로 구분한다.</li>
      <li>결과 파일에는 전체 / <code>{esc(present_condition)}</code> / <code>{esc(missing_condition)}</code> 구간의 성능을 따로 기록한다.</li>
      <li>주의: 메타가 있는 작품만 골라 학습하거나 평가하지 않는다. 그렇게 하면 데이터가 쉬운 케이스로 치우칠 수 있다.</li>
    </ul>
  </section>"""
        if needs_artist_meta_missing_check
        else ""
    )
    cold_data_rows = (
        "<tr><td>Cold 실험 여부</td><td>실험 제외</td></tr>"
        f"<tr><td>Cold 제외 이유</td><td>{esc(cold_exclusion_reason)}</td></tr>"
        if is_cold_excluded
        else f"<tr><td>Cold 기준 모델 학습 피처</td><td><code>{esc(item['cold_base'])}</code></td></tr>"
        f"<tr><td>Cold 변수 추가 모델 학습 피처</td><td><code>{esc(item['cold_add'])}</code></td></tr>"
        "<tr><td>Cold 테스트 피처</td><td>각 모델의 학습 피처와 같은 컬럼을 사용하되, <code>artist_name_ko</code>는 제외한다.</td></tr>"
    )
    cold_section = (
        f"""<section>
    <h2>4. 초기 실험 테스트: Cold</h2>
    <ul>
      <li>Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황</li>
      <li>본 실험에서는 Cold 평가를 수행하지 않는다.</li>
      <li>제외 이유: {esc(cold_exclusion_reason)}</li>
      <li>Cold 성능은 호수, 크기, 재료, 지지체처럼 작품 자체 변수 실험에서 확인한다.</li>
      <li>Cold 모델은 작가명을 쓰지 않는다.</li>
      <li>기록 방식: <code>outputs/summary.md</code>에 Cold 제외 사유를 남긴다.</li>
    </ul>
  </section>"""
        if is_cold_excluded
        else f"""<section>
    <h2>4. 초기 실험 테스트: Cold</h2>
    <ul>
      <li>Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황</li>
      <li>Cold 학습 X Cold Test: 학습 데이터에 없는 작가들의 작품만 평가한다.</li>
      <li>Cold 학습 X Warm Test: Cold 방식 모델을 기존 작가 작품에 적용해 Warm 모델과 비교한다.</li>
      <li>Cold 모델은 작가명을 쓰지 않는다.</li>
      <li>Cold 모델은 호수, 로그 호수, 이후 추가될 작품 자체 변수만 사용한다.</li>
      <li>Cold 학습 데이터: <code>data/train_features.csv</code> + <code>data/train_labels.csv</code></li>
      <li>Cold 테스트 데이터: <code>data/test_cold_features.csv</code> + <code>data/test_cold_labels.csv</code></li>
      <li>작품 연결 키: <code>{JOIN_KEY}</code></li>
      <li>제외 피처: <code>artist_name_ko</code></li>
      <li>기준 모델 학습 피처: <code>{esc(item['cold_base'])}</code></li>
      <li>변수 추가 모델 학습 피처: <code>{esc(item['cold_add'])}</code></li>
      <li>테스트 피처: 학습 피처와 같은 컬럼을 <code>data/test_cold_features.csv</code>에서 사용한다.</li>
      <li>비교 방식: <code>{esc(item['cold_base'])}</code> 모델과 <code>{esc(item['cold_add'])}</code> 모델을 비교한다.</li>
    </ul>
  </section>"""
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(item['id'])} {esc(item['title'])}</title>
  <style>{STYLE}</style>
</head>
<body>
<main>
  <header>
    <span class="badge planned">예정</span>
    <span class="badge goal">개별 변수 확인</span>
    <h1>{esc(item['id'])} {esc(item['title'])}</h1>
    <ul>
      <li>상위 흐름: 기본 피처 정의 단계</li>
      <li>목적: 변수 하나 또는 변수 묶음 하나가 가격 예측에 영향을 미치는지 독립적으로 확인</li>
      <li>상태: 실험 일지 생성 완료, 실행 전</li>
    </ul>
  </header>

  <section>
    <h2>1. 실험 일지</h2>
    <ul>
      <li>가설: {esc(item['hypothesis'])}</li>
      <li>확인 변수: <code>{esc(item['variable'])}</code></li>
      <li>유의미함 기준: 같은 모델과 같은 split에서 <code>median APE</code> 또는 <code>p95 APE</code>가 낮아지면 가격 예측에 영향을 주는 후보로 본다.</li>
      {'<li>Cold 판단: 본 가설은 Warm 전용으로만 판단한다.</li>' if is_cold_excluded else ''}
      <li>테스트 모델: Warm <code>Huber / Linear Regression / Ridge</code>, Cold <code>Huber / Quantile-LAD / LightGBM</code></li>
    </ul>
  </section>

  <section>
    <h2>2. 초기 실험 데이터</h2>
    <ul>
      <li>기준 원천 파일: <code>{SOURCE_FILE}</code></li>
      <li>학습 입력과 정답 가격은 분리해서 생성한다.</li>
      <li>정답 가격은 <code>train_labels.csv</code>, <code>test_warm_labels.csv</code>, <code>test_cold_labels.csv</code>에만 둔다.</li>
      <li>입력 피처와 정답 라벨은 <code>{JOIN_KEY}</code>로 연결한다.</li>
      <li>Warm 학습 피처에는 <code>artist_name_ko</code>를 둘 수 있지만, 이 실험의 판단 대상은 <code>{esc(item['variable'])}</code>다.</li>
      <li>Cold 테스트에는 작가명을 사용하지 않는다.</li>
      <li>{esc(item['note'])}</li>
    </ul>
    <div class="table-wrap">
      <table>
        <tr><th>구분</th><th>파일/피처</th></tr>
        <tr><td>생성 파일</td><td><code>data/train_features.csv</code>, <code>data/train_labels.csv</code>, <code>data/test_warm_features.csv</code>, <code>data/test_warm_labels.csv</code>, <code>data/test_cold_features.csv</code>, <code>data/test_cold_labels.csv</code></td></tr>
        <tr><td>Warm 기준 모델 학습 피처</td><td><code>{esc(item['warm_base'])}</code></td></tr>
        <tr><td>Warm 변수 추가 모델 학습 피처</td><td><code>{esc(item['warm_add'])}</code></td></tr>
        <tr><td>Warm 테스트 피처</td><td>각 모델의 학습 피처와 같은 컬럼을 사용한다.</td></tr>
        {cold_data_rows}
      </table>
    </div>
  </section>

  {artist_meta_dataset_section}

  <section>
    <h2>{'4' if needs_artist_meta_missing_check else '3'}. 초기 실험 테스트: Warm</h2>
    <ul>
      <li>Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황</li>
      <li>Warm 학습 X Warm Test: 학습 데이터에 등장한 작가의 미사용 작품으로 평가한다.</li>
      <li>Warm 학습 X Cold Test: Warm 방식 모델을 신규 작가 작품에 적용했을 때 성능이 무너지는지 확인한다.</li>
      <li>주의: Warm과 Cold는 같은 평가 지표를 쓰지만 결과는 합치지 않는다.</li>
      <li>Warm 학습 데이터: <code>data/train_features.csv</code> + <code>data/train_labels.csv</code></li>
      <li>Warm 테스트 데이터: <code>data/test_warm_features.csv</code> + <code>data/test_warm_labels.csv</code></li>
      <li>작품 연결 키: <code>{JOIN_KEY}</code></li>
      <li>기준 모델 학습 피처: <code>{esc(item['warm_base'])}</code></li>
      <li>변수 추가 모델 학습 피처: <code>{esc(item['warm_add'])}</code></li>
      <li>테스트 피처: 학습 피처와 같은 컬럼을 <code>data/test_warm_features.csv</code>에서 사용한다.</li>
      <li>비교 방식: <code>{esc(item['warm_base'])}</code> 모델과 <code>{esc(item['warm_add'])}</code> 모델을 비교한다.</li>
    </ul>
  </section>

  {cold_section.replace('<h2>4. 초기 실험 테스트: Cold</h2>', f"<h2>{'5' if needs_artist_meta_missing_check else '4'}. 초기 실험 테스트: Cold</h2>")}

  {artist_meta_missing_section}

  <section>
    <h2>{'7' if needs_artist_meta_missing_check else '5'}. 결과 기록</h2>
    <ul>
      <li>결과 파일: <code>outputs/metrics.csv</code></li>
      <li>예측 비교 파일: <code>outputs/predictions.csv</code></li>
      <li>구간별 오차 파일: <code>outputs/slice_metrics.csv</code></li>
      <li>요약 파일: <code>outputs/summary.md</code></li>
      <li>실행 로그: <code>logs/run.log</code></li>
    </ul>
  </section>

  <section>
    <h2>{'8' if needs_artist_meta_missing_check else '6'}. 판단 기준</h2>
    <ul>
      <li>Warm과 Cold의 <code>median APE</code>를 각각 확인한다.</li>
      <li><code>p95 APE</code>가 줄어드는지 확인해 큰 오차가 줄었는지 본다.</li>
      {'<li>본 실험은 Warm 전용 실험이므로 Cold 개선 여부는 판단하지 않는다.</li>' if is_cold_excluded else '<li>Warm에서만 개선되면 Warm 전용 후보로 둔다.</li><li>Cold에서만 개선되면 Cold 전용 후보로 둔다.</li>'}
      {'<li>작가 메타는 예측 성능 개선이 먼저 확인되어야 결측 처리나 추가 수집 후보로 둔다.</li><li>작가 메타가 있는 구간에서만 좋아지고 전체 성능이 좋아지지 않으면 보조 피처 또는 추가 수집 보류로 판단한다.</li>' if needs_artist_meta_missing_check else ''}
      <li>운영에서 입력하기 어렵거나 재현하기 어려운 변수는 성능이 좋아도 보류한다.</li>
      <li>결론 표기: 채택 / 보류 / 중단</li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def render_readme(item: dict[str, str]) -> str:
    needs_artist_meta_missing_check = item.get("artist_meta_missing_check") == "true"
    missing_flag = item.get("missing_flag", f"{item['variable']}_is_missing")
    present_condition = item.get("present_condition", f"{item['variable']} 값이 있는 작품")
    missing_condition = item.get("missing_condition", f"{item['variable']} 값이 비어 있는 작품")
    cold_exclusion_reason = item.get(
        "cold_exclusion_reason",
        "Cold는 신규 작가 예측 상황이므로 해당 작가 변수가 과거 가격 정보를 제공하지 못함",
    )
    cold_lines = (
        "- Cold 실험 여부: 실험 제외\n"
        f"- Cold 제외 이유: {cold_exclusion_reason}\n"
        if item.get("cold_excluded") == "true"
        else f"- Cold 기준 모델 학습 피처: `{item['cold_base']}`\n"
        f"- Cold 변수 추가 모델 학습 피처: `{item['cold_add']}`\n"
        "- Cold 테스트 피처: 학습 피처와 같은 컬럼 사용, `artist_name_ko` 제외\n"
    )
    return f"""# {item['id']} {item['title']}

- 단계: 기본 피처 정의 - 개별 변수 확인
- 가설: {item['hypothesis']}
- 확인 변수: `{item['variable']}`
- 테스트 모델: Warm `Huber / Linear Regression / Ridge`, Cold `Huber / Quantile-LAD / LightGBM`
- Warm 기준 모델 학습 피처: `{item['warm_base']}`
- Warm 변수 추가 모델 학습 피처: `{item['warm_add']}`
- Warm 테스트 피처: 학습 피처와 같은 컬럼 사용
{cold_lines.rstrip()}
- 연결 키: `{JOIN_KEY}`
- HTML 일지: `experiment_log.html`
{f"- 작가 메타 데이터셋: 기본 split은 유지하고, 메타 결측 때문에 작품을 제거하지 않음\n- 작가 메타 원값 피처: `{item['variable']}`\n- 작가 메타 결측 피처: `{missing_flag}`\n- 결측 비교: 전체 / {present_condition} / {missing_condition} 구간 성능을 따로 기록\n- 작가 메타 판단: 예측 성능 개선이 확인될 때만 결측 처리와 추가 수집을 검토\n" if needs_artist_meta_missing_check else ""}

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
"""


def render_config(item: dict[str, str]) -> str:
    needs_artist_meta_missing_check = item.get("artist_meta_missing_check") == "true"
    missing_flag = item.get("missing_flag", f"{item['variable']}_is_missing")
    present_condition = item.get("present_condition", f"{item['variable']} present")
    missing_condition = item.get("missing_condition", f"{item['variable']} missing")
    cold_exclusion_reason = item.get(
        "cold_exclusion_reason",
        "Cold is unseen-artist prediction, so this artist feature does not provide learned artist price information.",
    )
    cold_block = (
        "cold_experiment: excluded\n"
        f"cold_exclusion_reason: {cold_exclusion_reason}\n"
        if item.get("cold_excluded") == "true"
        else f"cold_base_train_features: {item['cold_base']}\n"
        f"cold_candidate_train_features: {item['cold_add']}\n"
        "cold_test_features: same_as_train_features_without_artist_name_ko\n"
    )
    return f"""experiment_id: {item['id']}
status: planned
phase: individual_variable_screening
title: {item['title']}
hypothesis: {item['hypothesis']}
source_file: {SOURCE_FILE}
join_key: {JOIN_KEY}
variable: {item['variable']}
warm_models: Huber / Linear Regression / Ridge
cold_models: Huber / Quantile-LAD / LightGBM
warm_base_train_features: {item['warm_base']}
warm_candidate_train_features: {item['warm_add']}
warm_test_features: same_as_train_features
{cold_block.rstrip()}
target: ln_price_krw
compare_against: {item['compare']}
artist_meta_missing_check: {"required" if needs_artist_meta_missing_check else "not_required"}
artist_meta_decision_rule: {"measure_effect_first_then_decide_missing_imputation_or_collection" if needs_artist_meta_missing_check else "not_applicable"}
artist_meta_dataset_rule: {"keep_original_split_add_raw_missing_flags_and_completeness_score" if needs_artist_meta_missing_check else "not_applicable"}
artist_meta_missing_flag: {missing_flag if needs_artist_meta_missing_check else "not_applicable"}
artist_meta_present_slice: {present_condition if needs_artist_meta_missing_check else "not_applicable"}
artist_meta_missing_slice: {missing_condition if needs_artist_meta_missing_check else "not_applicable"}
"""


def render_index() -> str:
    rows = []
    for item in EXPERIMENTS:
        rel = Path("../../../experiments/track6") / f"{item['id']}_{item['slug']}" / "experiment_log.html"
        cold_cell = (
            f"실험 제외<br><span>{esc(item.get('cold_exclusion_reason', '신규 작가 예측에서는 해당 작가 변수를 직접 사용하지 않음'))}</span>"
            if item.get("cold_excluded") == "true"
            else f"학습: <code>{esc(item['cold_base'])}</code><br>추가 학습: <code>{esc(item['cold_add'])}</code><br>테스트: 학습 피처와 동일, 작가명 제외"
        )
        rows.append(
            "<tr>"
            f"<td>{esc(item['id'])}</td>"
            f"<td>{esc(item['title'])}</td>"
            f"<td>{esc(item['variable'])}</td>"
            f"<td>{esc(item['hypothesis'])}</td>"
            f"<td>학습: <code>{esc(item['warm_base'])}</code><br>추가 학습: <code>{esc(item['warm_add'])}</code><br>테스트: 학습 피처와 동일</td>"
            f"<td>{cold_cell}</td>"
            f"<td><a href='{esc(str(rel))}'>일지 보기</a></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track6 개별 변수 확인 실험 일지</title>
  <style>{STYLE} table{{min-width:1280px}}</style>
</head>
<body>
<main>
  <header>
    <h1>Track6 개별 변수 확인 실험 일지</h1>
    <ul>
      <li>목적: 호수 실험과 같은 방식으로 각 변수의 가격 예측 영향 여부를 독립 확인</li>
      <li>공통 원칙: Warm과 Cold를 분리 평가하고, 입력 피처와 라벨은 <code>{JOIN_KEY}</code>로 연결</li>
      <li>총 실험 수: {len(EXPERIMENTS)}개</li>
    </ul>
  </header>
  <section>
    <div class="table-wrap">
      <table>
        <tr><th>실험 ID</th><th>제목</th><th>확인 변수</th><th>가설</th><th>Warm 학습/테스트 피처</th><th>Cold 학습/테스트 피처</th><th>일지</th></tr>
        {''.join(rows)}
      </table>
    </div>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    for item in EXPERIMENTS:
        folder = EXP_ROOT / f"{item['id']}_{item['slug']}"
        for sub in ["data", "scripts", "outputs", "logs"]:
            (folder / sub).mkdir(parents=True, exist_ok=True)
        (folder / "experiment_log.html").write_text(render_log(item), encoding="utf-8")
        (folder / "README.md").write_text(render_readme(item), encoding="utf-8")
        (folder / "experiment_config.yaml").write_text(render_config(item), encoding="utf-8")
    DOC_INDEX.parent.mkdir(parents=True, exist_ok=True)
    DOC_INDEX.write_text(render_index(), encoding="utf-8")
    print(DOC_INDEX)
    print(f"created_or_updated={len(EXPERIMENTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
