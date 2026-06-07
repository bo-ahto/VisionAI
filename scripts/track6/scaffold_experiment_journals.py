#!/usr/bin/env python3
"""Scaffold Track6 planned experiment journal folders and an index page."""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
EXP_ROOT = REPO / "experiments" / "track6"
DOC_INDEX = REPO / "docs" / "track6" / "journals" / "index.html"
BASIC_FEATURE_INDEX = REPO / "docs" / "track6" / "journals" / "basic_feature_definition.html"

BASIC_FEATURE_EXPERIMENT_IDS = {
    "T6-E011",
    "T6-E012",
    "T6-E013",
    "T6-E018",
    "T6-E019",
    "T6-E020",
    "T6-E021",
}

COMPLETED_INDEX_EXPERIMENTS = [
    {
        "id": "T6-E010",
        "slug": "hedonic_artist_ho_log",
        "title": "작가명 + 호수 / ln 변환 초기 실험",
        "goal": "T6-G2 기본 예측 가능성 확인",
        "hypothesis": "작가명(한글)과 호수만으로 가격 예측 신호가 있는지 확인하고, ln 변환이 성능을 개선하는지 검증한다.",
        "model": "Ridge 기반 Hedonic Linear Regression",
        "train_features": "Warm: artist_name_ko + estimated_ho / ln_estimated_ho, Cold: estimated_ho / ln_estimated_ho",
        "test_features": "학습 피처와 동일. Cold 모델은 artist_name_ko 제외",
        "target": "price_krw / ln_price_krw",
        "compare": "원값 모델 vs ln 변환 모델, Warm 모델 vs Cold 모델",
        "success": "ln 변환 효과와 Warm/Cold 분리 필요성 확인",
        "phase": "초기 실행 완료",
    },
]


EXPERIMENTS = [
    {
        "id": "T6-E011",
        "slug": "ho_only_warm_cold_baseline",
        "title": "호수 only Warm/Cold 기준 실험",
        "goal": "T6-G2 기본 예측 가능성 확인",
        "hypothesis": "작가명 없이 호수만으로도 Warm/Cold 가격대의 최소 신호를 확인할 수 있다.",
        "model": "Hedonic Ridge / Huber 후보",
        "train_features": "ln_estimated_ho",
        "test_features": "ln_estimated_ho",
        "target": "ln_price_krw",
        "compare": "T6-E010 Warm log / Cold log",
        "success": "작가명 제거 후 성능 하락 폭을 수치화하고, 호수 단독 baseline을 확정",
    },
    {
        "id": "T6-E012",
        "slug": "artist_only_warm_baseline",
        "title": "작가명 only Warm 기준 실험",
        "goal": "T6-G3 Warm 성능 개선",
        "hypothesis": "Warm에서는 작가명만으로도 작가별 기본 가격대를 상당 부분 설명할 수 있다.",
        "model": "Hedonic Ridge",
        "train_features": "artist_name_ko",
        "test_features": "artist_name_ko",
        "target": "ln_price_krw",
        "compare": "artist_name_ko only vs artist_name_ko + ln_estimated_ho",
        "success": "작가명 효과와 크기 효과를 분리 설명",
    },
    {
        "id": "T6-E013",
        "slug": "ho_representation_compare",
        "title": "호수 표현 방식 비교",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "호수는 원값보다 로그값, 구간값, 대형 플래그 등으로 표현할 때 더 안정적일 수 있다.",
        "model": "T6-E017 이전 임시 Ridge baseline",
        "train_features": "estimated_ho / ln_estimated_ho / ho_bucket / is_large_ho / is_extra_large_ho",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "호수 표현별 Warm/Cold median APE",
        "success": "후속 실험에서 사용할 호수 대표 표현 선정",
    },
    {
        "id": "T6-E014",
        "slug": "linear_model_family_compare",
        "title": "헤도닉 선형 모델군 비교",
        "goal": "T6-G6 모델 안정성 확인",
        "hypothesis": "같은 피처에서는 Ridge 외 Huber/Quantile 계열이 tail risk를 줄일 수 있다.",
        "model": "Linear / Ridge / Lasso / ElasticNet / Huber / Quantile",
        "train_features": "artist_name_ko, ln_estimated_ho",
        "test_features": "artist_name_ko, ln_estimated_ho",
        "target": "ln_price_krw",
        "compare": "선형 모델군 Warm/Cold 성능",
        "success": "기준 선형 모델 후보 확정",
    },
    {
        "id": "T6-E015",
        "slug": "warm_nonlinear_model_compare",
        "title": "Warm 비선형 모델 비교",
        "goal": "T6-G3 Warm 성능 개선",
        "hypothesis": "Warm에서는 작가명과 크기 관계가 비선형이므로 트리 모델이 선형보다 나을 수 있다.",
        "model": "LightGBM / CatBoost / XGBoost / HistGradientBoosting",
        "train_features": "artist_name_ko, ln_estimated_ho",
        "test_features": "artist_name_ko, ln_estimated_ho",
        "target": "ln_price_krw",
        "compare": "Warm Ridge baseline",
        "success": "Warm 기준 모델 후보 선정",
    },
    {
        "id": "T6-E016",
        "slug": "cold_basic_model_compare",
        "title": "Cold 기본 모델 비교",
        "goal": "T6-G4 Cold 성능 개선",
        "hypothesis": "Cold에서는 작가명 없이도 robust 선형 또는 단순 트리 모델이 호수 기반 예측을 안정화할 수 있다.",
        "model": "Ridge / Huber / Quantile / LightGBM / CatBoost",
        "train_features": "ln_estimated_ho",
        "test_features": "ln_estimated_ho",
        "target": "ln_price_krw",
        "compare": "Cold Ridge log baseline",
        "success": "Cold 기준 모델 후보 선정",
    },
    {
        "id": "T6-E017",
        "slug": "baseline_model_freeze",
        "title": "기본 피처 기반 Warm/Cold 후보 모델 선정",
        "goal": "T6-G6 모델 안정성 확인",
        "hypothesis": "같은 후보 모델군을 Warm과 Cold에 모두 적용하면 모델별 강점과 약점을 공정하게 비교할 수 있다.",
        "model": "Linear/Ridge/Huber/Quantile-LAD, LightGBM/XGBoost/CatBoost/HistGradientBoosting",
        "train_features": "Warm: artist_name_ko + ln_estimated_ho + medium_category + support_category, Cold: ln_estimated_ho + medium_category + support_category",
        "test_features": "학습 피처와 동일. Cold 후보는 artist_name_ko 제외",
        "target": "ln_price_krw",
        "compare": "같은 기본 피처셋에서 모델별 Warm/Cold median APE, p95 APE, Within-30/50 비교",
        "success": "1차 후보 전체를 기본 설정으로 실행한 뒤 Warm 상위 2~3개와 Cold 상위 2~3개를 압축하고, 이후 후보만 세부 검증",
    },
    {
        "id": "T6-E018",
        "slug": "material_feature_addition",
        "title": "재료 피처 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "재료 정보는 작품 가격 예측에서 크기 외 추가 설명력을 제공한다.",
        "model": "T6-E017 고정 모델",
        "train_features": "baseline + medium_category + nant_material_idx + nant_tool",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "baseline vs 재료 추가",
        "success": "Warm/Cold별 재료 피처 유지 여부 결정",
    },
    {
        "id": "T6-E019",
        "slug": "support_feature_addition",
        "title": "지지체 피처 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "캔버스/종이/패널 등 지지체 정보는 가격 차이를 설명할 수 있다.",
        "model": "T6-E017 고정 모델",
        "train_features": "baseline + support_category + nant_support",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "baseline vs 지지체 추가",
        "success": "지지체 피처 유지 여부 결정",
    },
    {
        "id": "T6-E020",
        "slug": "size_derived_feature_addition",
        "title": "크기 파생 피처 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "호수 외 면적, 가로/세로, 비율 피처가 추가 설명력을 줄 수 있다.",
        "model": "T6-E017 고정 모델",
        "train_features": "baseline + area_cm2 + log_area + width_cm + height_cm + aspect_ratio",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "호수 only vs 크기 파생 추가",
        "success": "호수만 쓸지, 크기 파생을 유지할지 결정",
    },
    {
        "id": "T6-E021",
        "slug": "depth_3d_feature_addition",
        "title": "3D/depth 피처 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "3D 작품은 면적보다 depth/부피성 피처가 가격 설명에 더 중요할 수 있다.",
        "model": "T6-E017 고정 모델",
        "train_features": "baseline + depth_cm + has_depth + is_3d_candidate",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "2D/3D slice별 성능",
        "success": "3D 분기 또는 전용 피처 필요 여부 판단",
    },
    {
        "id": "T6-E022",
        "slug": "warm_feature_ablation",
        "title": "Warm 피처 제거 ablation",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "Warm 후보 피처 중 일부는 중복되거나 성능 기여가 작을 수 있다.",
        "model": "Warm 고정 모델",
        "train_features": "Warm 후보 전체 피처에서 하나씩 제거",
        "test_features": "동일 제거 피처셋",
        "target": "ln_price_krw",
        "compare": "전체 피처 vs one-drop 피처",
        "success": "최종 Warm 필수 피처와 제외 피처 구분",
    },
    {
        "id": "T6-E023",
        "slug": "cold_feature_ablation",
        "title": "Cold 피처 제거 ablation",
        "goal": "T6-G4 Cold 성능 개선",
        "hypothesis": "Cold 후보 피처 중 일부는 신규 작가 예측에서 오히려 불안정할 수 있다.",
        "model": "Cold 고정 모델",
        "train_features": "Cold 후보 전체 피처에서 하나씩 제거",
        "test_features": "동일 제거 피처셋",
        "target": "ln_price_krw",
        "compare": "전체 피처 vs one-drop 피처",
        "success": "최종 Cold 필수 피처와 제외 피처 구분",
    },
    {
        "id": "T6-E024",
        "slug": "material_ho_interaction",
        "title": "재료 x 호수 조합 피처 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "같은 호수라도 재료에 따라 가격 증가 패턴이 다를 수 있다.",
        "model": "고정 모델",
        "train_features": "baseline + medium_ho_bucket + nant_material_idx_x_ho_bucket",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "단독 피처 vs 조합 피처",
        "success": "재료-크기 조합 피처 유지 여부 결정",
    },
    {
        "id": "T6-E025",
        "slug": "artist_ho_interaction",
        "title": "작가명 x 호수 조합 실험",
        "goal": "T6-G3 Warm 성능 개선",
        "hypothesis": "Warm에서는 작가별 크기 가격대 차이를 조합 피처로 반영할 수 있다.",
        "model": "Warm 고정 모델",
        "train_features": "baseline + artist_ho_bucket",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "artist + ho vs artist x ho 조합",
        "success": "Warm 전용 조합 피처 효과 확인",
    },
    {
        "id": "T6-E026",
        "slug": "support_material_interaction",
        "title": "지지체 x 재료 조합 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "재료와 지지체의 조합은 단독 피처보다 가격을 더 잘 설명할 수 있다.",
        "model": "고정 모델",
        "train_features": "baseline + medium_support_bucket + nant_support_nant_tool_bucket",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "단독 피처 vs 조합 피처",
        "success": "운영 가능 조합 피처 후보 선정",
    },
    {
        "id": "T6-E027",
        "slug": "artist_meta_basic_features",
        "title": "작가 기본 메타 피처 추가 실험",
        "goal": "T6-G3 Warm 성능 개선",
        "hypothesis": "작가 국적, 생년, 경력 연차 등 기본 메타 정보는 가격 예측을 개선할 수 있다.",
        "model": "Warm/Cold 고정 모델",
        "train_features": "baseline + artist_meta_nationality + artist_meta_birth_year + artist_meta_career_age",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "baseline vs 작가 기본 메타 추가",
        "success": "작가 DB 연동 가치 확인",
    },
    {
        "id": "T6-E028",
        "slug": "artist_activity_features",
        "title": "작가 활동량 피처 실험",
        "goal": "T6-G3 Warm 성능 개선",
        "hypothesis": "작품 수, 판매 수, 팔로워 수 등 활동량은 가격대 설명에 도움을 줄 수 있다.",
        "model": "Warm/Cold 고정 모델",
        "train_features": "baseline + artist_meta_total_works + artist_meta_for_sale_works + artist_meta_followers",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "baseline vs 활동량 피처 추가",
        "success": "작가 활동량 피처 구축 우선순위 판단",
    },
    {
        "id": "T6-E029",
        "slug": "cold_material_size_model",
        "title": "Cold 재료 + 크기 모델 실험",
        "goal": "T6-G4 Cold 성능 개선",
        "hypothesis": "Cold에서는 작가명 대신 재료와 크기 정보가 예측 성능을 보완할 수 있다.",
        "model": "Cold 고정 후보 모델",
        "train_features": "ln_estimated_ho + medium_category + support_category + nant_material_idx",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "Cold ho only vs 재료+크기",
        "success": "Cold median APE와 p95 APE 개선",
    },
    {
        "id": "T6-E030",
        "slug": "cold_2d_3d_branch",
        "title": "Cold 2D/3D 분기 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "Cold 3D 작품은 전체 모델보다 별도 분기 모델이 더 안정적일 수 있다.",
        "model": "Cold 전체 모델 / 2D 모델 / 3D 모델",
        "train_features": "Cold 후보 피처 + 3D/depth 피처",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "전체 Cold 모델 vs 2D/3D 분기",
        "success": "3D slice p95 개선 또는 분기 불필요 결론",
    },
    {
        "id": "T6-E031",
        "slug": "cold_risk_slice_analysis",
        "title": "Cold 위험 구간 분석",
        "goal": "T6-G7 신뢰도/가격 범위 정책",
        "hypothesis": "Cold 큰 오차는 특정 크기, 재료, 호수 구간에 집중될 수 있다.",
        "model": "Cold 후보 모델",
        "train_features": "Cold 후보 피처",
        "test_features": "Cold 후보 피처",
        "target": "ln_price_krw",
        "compare": "전체 Cold vs 위험 slice",
        "success": "서비스 신뢰도 경고 후보 구간 정의",
    },
    {
        "id": "T6-E032",
        "slug": "warm_candidate_feature_set_compare",
        "title": "Warm 후보 피처 조합 비교",
        "goal": "T6-G8 최종 운영 후보 확정",
        "hypothesis": "Warm은 작가명, 크기, 재료, 작가 메타를 조합할 때 최적 성능을 얻을 수 있다.",
        "model": "Warm 후보 모델",
        "train_features": "최소 / 재료 추가 / 크기 추가 / 작가 메타 추가 조합",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "Warm 피처셋별 성능/복잡도",
        "success": "Warm 최종 피처 후보 선정",
    },
    {
        "id": "T6-E033",
        "slug": "cold_candidate_feature_set_compare",
        "title": "Cold 후보 피처 조합 비교",
        "goal": "T6-G8 최종 운영 후보 확정",
        "hypothesis": "Cold는 작가명 없이 호수, 재료, 지지체, 크기 파생 조합으로 성능을 개선할 수 있다.",
        "model": "Cold 후보 모델",
        "train_features": "호수 only / 재료 / 지지체 / 크기 파생 / 작가 메타 조합",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "Cold 피처셋별 median/p95",
        "success": "Cold 최종 피처 후보 선정",
    },
    {
        "id": "T6-E034",
        "slug": "warm_final_model_compare",
        "title": "Warm 최종 후보 모델 비교",
        "goal": "T6-G8 최종 운영 후보 확정",
        "hypothesis": "최종 Warm 피처셋에서는 비선형 모델이 선형 모델보다 더 높은 정확도를 낼 수 있다.",
        "model": "Hedonic Ridge / Huber / CatBoost / LightGBM / XGBoost",
        "train_features": "T6-E032 선정 Warm 피처셋",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "최종 Warm 모델 후보 전체",
        "success": "Warm 최종 모델 확정",
    },
    {
        "id": "T6-E035",
        "slug": "cold_final_model_compare",
        "title": "Cold 최종 후보 모델 비교",
        "goal": "T6-G8 최종 운영 후보 확정",
        "hypothesis": "최종 Cold 피처셋에서는 robust 선형 또는 단순 트리 모델이 가장 안정적일 수 있다.",
        "model": "Ridge / Huber / Quantile / CatBoost / LightGBM",
        "train_features": "T6-E033 선정 Cold 피처셋",
        "test_features": "동일 피처셋",
        "target": "ln_price_krw",
        "compare": "최종 Cold 모델 후보 전체",
        "success": "Cold 최종 모델 확정",
    },
    {
        "id": "T6-E036",
        "slug": "warm_cold_routing_policy",
        "title": "Warm/Cold 라우팅 기준 실험",
        "goal": "T6-G8 최종 운영 후보 확정",
        "hypothesis": "학습 데이터 내 작가 존재 여부와 작품 수 기준을 함께 쓰면 모델 선택 안정성이 높아진다.",
        "model": "Warm 최종 후보 / Cold 최종 후보",
        "train_features": "최종 후보 피처셋",
        "test_features": "최종 후보 피처셋",
        "target": "ln_price_krw",
        "compare": "작가 존재 여부 only vs 작품 수 threshold",
        "success": "서비스 모델 선택 규칙 확정",
    },
    {
        "id": "T6-E037",
        "slug": "price_interval_confidence_policy",
        "title": "가격 범위 / 신뢰도 표시 정책 실험",
        "goal": "T6-G7 신뢰도/가격 범위 정책",
        "hypothesis": "단일 가격 예측보다 가격 범위와 신뢰도 경고를 함께 제공하는 것이 실무적으로 더 안전하다.",
        "model": "최종 Warm/Cold 후보",
        "train_features": "최종 후보 피처셋",
        "test_features": "최종 후보 피처셋",
        "target": "ln_price_krw",
        "compare": "단일 예측 vs 가격 범위 coverage",
        "success": "서비스 출력 정책 후보 확정",
    },
    {
        "id": "T6-E038",
        "slug": "artwork_variable_selection",
        "title": "작품 변수 선정 실험 일지",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "호수, 실제 크기, 재료, 지지체, 3D 피처가 가격 예측을 개선하는지 비교 대상별로 검증한다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준: ln_estimated_ho, Warm: artist_name_ko 추가, 후속: 크기/재료/지지체/3D 묶음 추가",
        "test_features": "학습 피처와 동일한 입력 피처 사용, 가격 라벨은 평가 단계에서만 결합",
        "target": "price_krw / ln_price_krw",
        "compare": "기준 모델 vs 피처 추가 모델, 단독 피처 vs 조합 피처, 공통 피처 vs Warm/Cold 분리 피처",
        "success": "median APE 또는 p95 APE 개선, 운영 입력 가능성, Warm/Cold 분리 필요성 확인",
    },
    {
        "id": "T6-E039",
        "slug": "ho_signal_baseline",
        "title": "호수 변수 영향 확인",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "호수 변수가 가격 예측에 영향을 미친다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm 1차: artist_name_ko + ln_estimated_ho, Warm 2차: ln_estimated_ho, Cold: ln_estimated_ho",
        "test_features": "Warm 1차: artist_name_ko + ln_estimated_ho, Warm 2차: ln_estimated_ho, Cold: ln_estimated_ho",
        "target": "ln_price_krw",
        "compare": "가격 중앙값 기준 모델, 작가명+호수 모델, 호수 only 모델 비교",
        "success": "같은 split과 같은 모델에서 median APE 또는 p95 APE가 낮아지면 유지",
    },
    {
        "id": "T6-E040",
        "slug": "actual_size_feature_group",
        "title": "실제 크기 정보 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "실제 크기 정보는 호수만 사용할 때보다 가격 예측을 개선한다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm: artist_name_ko + ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio, Cold: ln_estimated_ho + width_cm + height_cm + log_area + aspect_ratio",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "기준 모델에 실제 크기 묶음 추가",
        "success": "Warm/Cold 중 하나 이상에서 median APE가 낮아지면 후보 유지",
    },
    {
        "id": "T6-E041",
        "slug": "material_feature_group",
        "title": "재료 정보 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "재료 정보는 기준 모델보다 가격 예측을 개선한다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm: artist_name_ko + ln_estimated_ho + medium_category + nant_material_idx + nant_tool, Cold: ln_estimated_ho + medium_category + nant_material_idx + nant_tool",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "기준 모델에 재료 묶음 추가",
        "success": "median APE 또는 p95 APE 개선 시 후보 유지",
    },
    {
        "id": "T6-E042",
        "slug": "support_feature_group",
        "title": "지지체 정보 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "지지체 정보는 기준 모델 + 재료 피처보다 가격 예측을 개선한다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm: artist_name_ko + ln_estimated_ho + 재료 묶음 + support_category + nant_support, Cold: ln_estimated_ho + 재료 묶음 + support_category + nant_support",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "기준 모델 + 재료 피처에 지지체 묶음 추가",
        "success": "성능 개선 시 후보 유지",
    },
    {
        "id": "T6-E043",
        "slug": "depth_3d_feature_group",
        "title": "깊이/3D 정보 추가 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "깊이/3D 정보는 2D와 3D 작품을 구분해 예측하는 데 도움이 된다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm: artist_name_ko + ln_estimated_ho + depth_cm + has_depth + is_3d_candidate, Cold: ln_estimated_ho + depth_cm + has_depth + is_3d_candidate",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "깊이/3D 피처 추가 전후와 2D/3D slice별 오차 비교",
        "success": "3D slice의 median APE 또는 p95 APE가 개선되면 후보 유지",
    },
    {
        "id": "T6-E044",
        "slug": "material_size_interaction",
        "title": "재료 x 크기 조합 피처 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "재료와 크기 조합 피처는 재료와 크기를 따로 넣는 것보다 가격 예측을 개선한다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "Warm/Cold 각각 기준 피처 + 단독 피처 또는 조합 피처",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "단독 피처 모델과 조합 피처 모델 비교",
        "success": "조합 피처 모델이 단독 피처 모델보다 성능이 좋으면 유지",
    },
    {
        "id": "T6-E045",
        "slug": "staged_feature_selection",
        "title": "단계적 피처 선택 절차 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "단계적 피처 선택 방식은 전체 조합 탐색 없이도 기준 모델보다 좋은 피처 조합을 찾을 수 있다.",
        "model": "Warm/Cold 기준 후보 모델",
        "train_features": "단계별 선택 피처셋",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "단일 추가, 그룹 추가, 제거 실험 순서로 후보 축소",
        "success": "최종 선택 조합이 기준 모델보다 성능 개선되면 절차 채택",
    },
    {
        "id": "T6-E046",
        "slug": "warm_cold_feature_split",
        "title": "Warm/Cold 작품 피처 분리 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "Warm과 Cold는 동일한 작품 피처 조합보다 각각 다른 피처 조합을 사용할 때 성능이 좋아질 수 있다.",
        "model": "Warm/Cold 기준 후보 모델",
        "train_features": "Warm 전용 후보 피처셋, Cold 전용 후보 피처셋",
        "test_features": "각 split에 맞는 전용 피처셋",
        "target": "ln_price_krw",
        "compare": "공통 피처 모델과 Warm/Cold 분리 피처 모델 비교",
        "success": "분리 피처 모델의 각 성능이 더 좋으면 채택",
    },
    {
        "id": "T6-E047",
        "slug": "size_representative_vs_full",
        "title": "크기 대표값 vs 전체 크기 피처 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "크기 대표값 중심 피처는 전체 크기 피처를 모두 쓰는 방식보다 예측 오차를 줄일 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "대표 크기 피처셋 또는 전체 크기 피처셋",
        "test_features": "학습 피처와 동일",
        "target": "ln_price_krw",
        "compare": "대표 크기 피처 모델과 전체 크기 피처 모델 비교",
        "success": "대표값 모델이 성능 유지 또는 p95 APE 개선 시 채택",
    },
    {
        "id": "T6-E048",
        "slug": "raw_material_keyword_addition",
        "title": "원본 재료 문구 키워드 추가 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "원본 재료 문구에는 표준 재료 분류가 담지 못한 가격 차이 설명 정보가 있을 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준: medium_category + nant_material_idx, 추가: collected_material_raw keyword flags",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "표준 재료 피처 모델과 원본 재료 키워드 추가 모델 비교",
        "success": "원본 키워드 추가 시 median APE 또는 특정 재료 slice 오차 개선",
    },
    {
        "id": "T6-E049",
        "slug": "title_keyword_feature",
        "title": "작품 제목 키워드 피처 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "작품 제목에는 에디션, 세트, 포스터 등 가격 차이를 설명하는 정보가 있을 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준 피처 + title_raw keyword flags",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "기준 모델과 제목 키워드 flag 추가 모델 비교",
        "success": "전체 성능 또는 해당 키워드 slice 오차 개선",
    },
    {
        "id": "T6-E050",
        "slug": "extreme_aspect_ratio_flag",
        "title": "극단 가로세로 비율 플래그 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "극단적인 가로세로 비율 작품은 일반 작품과 가격 예측 오차 패턴이 다를 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준: aspect_ratio, 추가: is_extreme_aspect_ratio",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "비율 원값 모델과 극단 비율 flag 추가 모델 비교",
        "success": "극단 비율 slice의 p95 APE 감소",
    },
    {
        "id": "T6-E051",
        "slug": "depth_bucket_feature",
        "title": "깊이 구간화 피처 실험",
        "goal": "T6-G5 약점 구간 보완",
        "hypothesis": "0에 가까운 깊이와 실제 3D에 가까운 깊이는 가격 차이를 다르게 설명할 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준: has_depth + is_3d_candidate, 추가: depth_bucket",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "has_depth만 사용한 모델과 depth 구간화 모델 비교",
        "success": "3D/depth slice 오차 개선",
    },
    {
        "id": "T6-E052",
        "slug": "nant_material_grouping",
        "title": "난트 재료 분류 그룹화 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "난트 재료 분류 번호가 너무 세분화되어 있으면 그룹화했을 때 더 안정적인 가격 예측이 가능할 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "nant_material_idx 원본 vs nant_material_group",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "원본 idx 모델과 상위 그룹화 모델 비교",
        "success": "Cold p95 APE 감소 또는 성능 유지",
    },
    {
        "id": "T6-E053",
        "slug": "max_min_side_size_feature",
        "title": "긴 변/짧은 변 크기 피처 실험",
        "goal": "T6-G5 운영 가능 피처 선정",
        "hypothesis": "가격 예측에는 면적보다 긴 변 또는 짧은 변 정보가 더 도움이 될 수 있다.",
        "model": "Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM",
        "train_features": "기준: log_area, 추가: max_side_cm + min_side_cm",
        "test_features": "학습 피처와 동일한 컬럼 구성 사용",
        "target": "ln_price_krw",
        "compare": "면적 중심 모델과 긴 변/짧은 변 모델 비교",
        "success": "전체 또는 대형 작품 slice 오차 개선",
    },

]


def exp_dir(item: dict[str, str]) -> Path:
    return EXP_ROOT / f"{item['id']}_{item['slug']}"


def render_log(item: dict[str, str]) -> str:
    is_basic_feature = item["id"] in BASIC_FEATURE_EXPERIMENT_IDS
    phase_badge = "기본 피처 정의 상세 실험" if is_basic_feature else "후속 실험"
    phase_note = (
        "이 실험은 최종 모델을 고르는 실험이 아니라, 이후 후보 모델 비교에 넣을 기본 입력 피처를 정하기 위한 상세 검증입니다."
        if is_basic_feature
        else "이 실험은 기본 피처 정의 이후의 모델/피처 조합/운영 정책 검증입니다."
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(item['id'])} 실험 일지</title>
  <style>
    :root {{ --bg:#f5efe4; --paper:#fffdf7; --ink:#1d251f; --line:#d8cdb8; --muted:#687268; --green:#27684a; --amber:#9b6124; }}
    body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; line-height:1.62; }}
    main {{ max-width:1120px; margin:0 auto; padding:32px 22px 72px; }}
    header, section {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:24px; padding:26px; margin-top:18px; box-shadow:0 12px 34px rgba(42,34,22,.08); }}
    h1 {{ margin:0; font-size:42px; letter-spacing:-.055em; }}
    h2 {{ margin:0 0 12px; font-size:22px; letter-spacing:-.03em; }}
    ul {{ margin:8px 0 0; padding-left:21px; }}
    code {{ background:#eee5d4; border-radius:7px; padding:2px 6px; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; background:var(--paper); }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:14px; }}
    th {{ background:#eadfcd; }}
    .badge {{ display:inline-flex; padding:5px 9px; border-radius:999px; font-size:12px; font-weight:800; margin-right:6px; }}
    .planned {{ background:rgba(155,97,36,.14); color:var(--amber); }}
    .goal {{ background:rgba(39,104,74,.14); color:var(--green); }}
    .note {{ color:var(--muted); }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
  </style>
</head>
<body>
<main>
  <header>
    <span class="badge planned">예정 실험</span>
    <span class="badge phase">{html.escape(phase_badge)}</span>
    <span class="badge goal">{html.escape(item['goal'])}</span>
    <h1>{html.escape(item['id'])} {html.escape(item['title'])}</h1>
    <p class="note">이 문서는 실행 전 실험 일지 템플릿입니다. 실행 후 결과 지표와 해석을 같은 파일에 갱신합니다.</p>
    <p><strong>실험 단계:</strong> {html.escape(phase_badge)}</p>
    <p><strong>단계 설명:</strong> {html.escape(phase_note)}</p>
  </header>

  <section>
    <h2>1. 가설</h2>
    <ul><li>{html.escape(item['hypothesis'])}</li></ul>
  </section>

  <section>
    <h2>2. 이 실험이 기본 피처 정의에 필요한 이유</h2>
    <ul>
      <li>{html.escape(phase_note)}</li>
      <li>이 단계에서는 최고 성능 모델을 찾기보다, 어떤 피처를 기본 입력값으로 유지할지 판단합니다.</li>
      <li>판단 결과는 이후 <code>기본 피처로 후보 모델 비교</code> 단계의 입력 피처셋으로 넘어갑니다.</li>
    </ul>
  </section>

  <section>
    <h2>3. 실험 방법</h2>
    <div class="table-wrap">
      <table>
        <tr><th>항목</th><th>내용</th></tr>
        <tr><td>테스트 모델</td><td>{html.escape(item['model'])}</td></tr>
        <tr><td>학습에 사용된 피처</td><td><code>{html.escape(item['train_features'])}</code></td></tr>
        <tr><td>테스트에 사용된 피처</td><td><code>{html.escape(item['test_features'])}</code></td></tr>
        <tr><td>학습 정답값</td><td><code>{html.escape(item['target'])}</code></td></tr>
        <tr><td>비교 기준</td><td>{html.escape(item['compare'])}</td></tr>
        <tr><td>유의미함 기준</td><td>{html.escape(item['success'])}</td></tr>
      </table>
    </div>
  </section>

  <section>
    <h2>4. 사용 모델 상세</h2>
    <div class="table-wrap">
      <table>
        <tr><th>항목</th><th>내용</th></tr>
        <tr><td>실험 모델군</td><td>{html.escape(item['model'])}</td></tr>
        <tr><td>모델 역할</td><td>해당 가설을 검증하기 위한 후보 모델 또는 기준 모델</td></tr>
        <tr><td>기본 입력 처리</td><td>범주형 피처는 인코딩, 수치형 피처는 필요 시 스케일링 또는 로그 변환</td></tr>
        <tr><td>목표값 처리</td><td><code>{html.escape(item['target'])}</code>를 학습 정답값으로 사용</td></tr>
        <tr><td>비교 방식</td><td>{html.escape(item['compare'])}</td></tr>
        <tr><td>모델 선택 기준</td><td>median APE, p95 APE, Within-30/50, Warm/Cold 분리 성능, 운영 가능성</td></tr>
      </table>
    </div>
  </section>

  <section>
    <h2>5. 생성할 데이터 파일</h2>
    <ul>
      <li><code>data/train_features.csv</code>: 학습에 사용된 피처</li>
      <li><code>data/train_labels.csv</code>: 학습 정답값</li>
      <li><code>data/test_warm_features.csv</code>: Warm 테스트 입력 피처</li>
      <li><code>data/test_warm_labels.csv</code>: Warm 테스트 정답값</li>
      <li><code>data/test_cold_features.csv</code>: Cold 테스트 입력 피처</li>
      <li><code>data/test_cold_labels.csv</code>: Cold 테스트 정답값</li>
    </ul>
  </section>

  <section>
    <h2>참고: 초기 실험 테스트 해석 기준</h2>
    <ul>
      <li>Warm 정의: 학습 데이터에 같은 작가가 있는 작품을 예측하는 상황</li>
      <li>Warm 학습 X Warm Test: 학습 데이터에 등장한 작가의 미사용 작품으로 평가</li>
      <li>Warm 학습 X Cold Test: Warm 방식 모델을 신규 작가 작품에 적용했을 때 성능이 무너지는지 확인</li>
      <li>Cold 정의: 학습 데이터에 한 번도 등장하지 않은 작가의 작품을 예측하는 상황</li>
      <li>Cold 학습 X Cold Test: 학습 데이터에 없는 작가들의 작품만 평가</li>
      <li>Cold 학습 X Warm Test: Cold 방식 모델을 기존 작가 작품에 적용해 Warm 모델과 비교</li>
      <li>주의: Warm과 Cold는 같은 평가 지표를 쓰지만 결과는 합치지 않음</li>
    </ul>
  </section>

  <section>
    <h2>6. 결과 기록 위치</h2>
    <ul>
      <li><code>outputs/metrics.csv</code>: 전체 지표</li>
      <li><code>outputs/predictions.csv</code>: 예측값과 실제값 비교</li>
      <li><code>outputs/slice_metrics.csv</code>: 구간별 오차</li>
      <li><code>outputs/summary.md</code>: 결과 해석 요약</li>
      <li><code>logs/run.log</code>: 실행 로그</li>
    </ul>
  </section>

  <section>
    <h2>7. 실행 후 채워야 할 결론</h2>
    <ul>
      <li>Warm median APE / p95 APE</li>
      <li>Cold median APE / p95 APE</li>
      <li>Within-30 / Within-50</li>
      <li>baseline 대비 개선 여부</li>
      <li>채택 / 보류 / 중단 판단</li>
      <li>다음 실험으로 넘길 피처 또는 모델 후보</li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def render_readme(item: dict[str, str]) -> str:
    is_basic_feature = item["id"] in BASIC_FEATURE_EXPERIMENT_IDS
    phase = "기본 피처 정의 상세 실험" if is_basic_feature else "후속 실험"
    phase_note = (
        "최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험"
        if is_basic_feature
        else "기본 피처 정의 이후 진행할 후속 실험"
    )
    return f"""# {item['id']} {item['title']}

- 상태: 예정
- 실험 단계: {phase}
- 단계 설명: {phase_note}
- 세부 목표: {item['goal']}
- 가설: {item['hypothesis']}
- 테스트 모델: {item['model']}
- 학습에 사용된 피처: `{item['train_features']}`
- 테스트에 사용된 피처: `{item['test_features']}`
- 학습 정답값: `{item['target']}`
- 비교 기준: {item['compare']}
- 유의미함 기준: {item['success']}
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
"""


def render_config(item: dict[str, str]) -> str:
    phase = "basic_feature_definition" if item["id"] in BASIC_FEATURE_EXPERIMENT_IDS else "followup"
    return f"""experiment_id: {item['id']}
status: planned
phase: {phase}
title: {item['title']}
goal: {item['goal']}
hypothesis: {item['hypothesis']}
model: {item['model']}
train_features: {item['train_features']}
test_features: {item['test_features']}
target: {item['target']}
compare_against: {item['compare']}
success_criteria: {item['success']}
"""


def render_index() -> str:
    rows = []
    for item in COMPLETED_INDEX_EXPERIMENTS + EXPERIMENTS:
        folder = exp_dir(item)
        log_rel = Path("../../../experiments/track6") / folder.name / "experiment_log.html"
        phase = item.get(
            "phase",
            "기본 피처 정의" if item["id"] in BASIC_FEATURE_EXPERIMENT_IDS else "후속",
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['id'])}</td>"
            f"<td>{html.escape(phase)}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['goal'])}</td>"
            f"<td>{html.escape(item['hypothesis'])}</td>"
            f"<td><code>{html.escape(item['train_features'])}</code></td>"
            f"<td><code>{html.escape(item['test_features'])}</code></td>"
            f"<td>{html.escape(item['model'])}</td>"
            "<td class='actions'>"
            f"<a class='open-link' href='{html.escape(str(log_rel))}'>일지 보기</a>"
            "</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track6 실험 일지 모음</title>
  <style>
    :root {{ --bg:#f5efe4; --paper:#fffdf7; --ink:#1d251f; --line:#d8cdb8; --green:#27684a; }}
    body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1280px; margin:0 auto; padding:34px 22px 72px; }}
    header {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:28px; padding:32px; box-shadow:0 12px 34px rgba(42,34,22,.08); }}
    h1 {{ margin:0; font-size:48px; letter-spacing:-.055em; }}
    section {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:20px; padding:18px; margin-top:18px; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
    table {{ width:100%; border-collapse:collapse; background:var(--paper); min-width:1500px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; position:sticky; top:0; }}
    code {{ background:#eee5d4; border-radius:7px; padding:2px 6px; overflow-wrap:anywhere; }}
    a {{ color:#174f73; font-weight:800; }}
    .actions {{ width:120px; min-width:120px; background:var(--paper); position:sticky; right:0; z-index:1; box-shadow:-8px 0 12px rgba(42,34,22,.06); }}
    .actions .open-link {{
      display:block; box-sizing:border-box; width:100%; padding:8px 10px; border-radius:10px;
      background:#e9f0e7; color:#174f73; font-weight:800; text-decoration:none; text-align:center;
      cursor:pointer; margin:0 0 8px;
    }}
    @media(max-width:920px) {{ h1 {{ font-size:34px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Track6 실험 일지 모음</h1>
    <p>실험별 폴더에 생성된 HTML 일지를 한곳에서 확인하는 페이지입니다. 리스트에서 학습 피처와 테스트 피처를 바로 비교할 수 있습니다.</p>
    <p><a href="basic_feature_definition.html">기본 피처 정의 상세 실험만 보기</a></p>
    <p><a href="artwork_feature_selection.html">작품 피처 가설별 실험 일지만 보기</a></p>
    <p>생성일: {date.today().isoformat()} / 실행 완료 기준 실험: {len(COMPLETED_INDEX_EXPERIMENTS)}개 / 예정 실험: {len(EXPERIMENTS)}개</p>
  </header>
  <section>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>실험 ID</th><th>단계</th><th>제목</th><th>목표</th><th>가설</th>
            <th>학습 피처</th><th>테스트 피처</th><th>모델</th><th>일지</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>
</main>
</body>
</html>
"""


def render_basic_feature_index() -> str:
    items = [item for item in EXPERIMENTS if item["id"] in BASIC_FEATURE_EXPERIMENT_IDS]
    rows = []
    for item in items:
        folder = exp_dir(item)
        log_rel = Path("../../../experiments/track6") / folder.name / "experiment_log.html"
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['id'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['hypothesis'])}</td>"
            f"<td><code>{html.escape(item['train_features'])}</code></td>"
            f"<td><code>{html.escape(item['test_features'])}</code></td>"
            f"<td>{html.escape(item['model'])}</td>"
            f"<td>{html.escape(item['success'])}</td>"
            "<td class='actions'>"
            f"<a class='open-link' href='{html.escape(str(log_rel))}'>일지 보기</a>"
            "</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Track6 기본 피처 정의 실험 모음</title>
  <style>
    :root {{ --bg:#f5efe4; --paper:#fffdf7; --ink:#1d251f; --line:#d8cdb8; --green:#27684a; }}
    body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#efe7d7,#f8f5ec 48%,#e9f0e7); font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1180px; margin:0 auto; padding:34px 22px 72px; }}
    header {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:28px; padding:32px; box-shadow:0 12px 34px rgba(42,34,22,.08); }}
    h1 {{ margin:0; font-size:44px; letter-spacing:-.055em; }}
    section {{ background:rgba(255,253,247,.96); border:1px solid var(--line); border-radius:20px; padding:18px; margin-top:18px; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--line); border-radius:16px; }}
    table {{ width:100%; border-collapse:collapse; background:var(--paper); min-width:1120px; }}
    th,td {{ padding:11px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ background:#eadfcd; position:sticky; top:0; }}
    code {{ background:#eee5d4; border-radius:7px; padding:2px 6px; overflow-wrap:anywhere; }}
    a {{ color:#174f73; font-weight:800; }}
    .actions {{ width:120px; min-width:120px; background:var(--paper); position:sticky; right:0; z-index:1; box-shadow:-8px 0 12px rgba(42,34,22,.06); }}
    .actions .open-link {{
      display:block; box-sizing:border-box; width:100%; padding:8px 10px; border-radius:10px;
      background:#e9f0e7; color:#174f73; font-weight:800; text-decoration:none; text-align:center;
      cursor:pointer; margin:0;
    }}
    @media(max-width:860px) {{ h1 {{ font-size:32px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Track6 기본 피처 정의 상세 실험</h1>
    <p>이 페이지는 최종 모델 비교 전에 기본 입력 피처를 정하기 위한 실험만 모아둔 페이지입니다.</p>
    <p>목적: 작가명, 호수, 호수 표현, 크기 파생, 재료, 지지체, 3D/depth 중 무엇을 기본 피처로 둘지 결정합니다.</p>
    <p><a href="index.html">전체 실험 일지 모음으로 돌아가기</a></p>
  </header>
  <section>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>실험 ID</th><th>제목</th><th>가설</th><th>학습 피처</th>
            <th>테스트 피처</th><th>모델</th><th>판단 기준</th><th>일지</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    for item in EXPERIMENTS:
        folder = exp_dir(item)
        for sub in ["data", "scripts", "outputs", "logs"]:
            (folder / sub).mkdir(parents=True, exist_ok=True)
        (folder / "README.md").write_text(render_readme(item), encoding="utf-8")
        (folder / "experiment_config.yaml").write_text(render_config(item), encoding="utf-8")
        (folder / "experiment_log.html").write_text(render_log(item), encoding="utf-8")

    DOC_INDEX.parent.mkdir(parents=True, exist_ok=True)
    DOC_INDEX.write_text(render_index(), encoding="utf-8")
    BASIC_FEATURE_INDEX.write_text(render_basic_feature_index(), encoding="utf-8")
    print(DOC_INDEX)
    print(BASIC_FEATURE_INDEX)
    print(f"created_or_updated={len(EXPERIMENTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
