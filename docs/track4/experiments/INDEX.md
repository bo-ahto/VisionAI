# Track 4 실험 기록 인덱스

- 목적: Track 4 개별 실험 기록을 한눈에 관리
- 정렬 기준: 최신 실험이 위로 오도록 관리

| 날짜 | 실험 ID | 연결 가설 | 상태 | 요약 | 기록 |
|---|---|---|---|---|---|
| 2026-05-17 | T4-E050 | T4-H37 | 완료 | Cold 최종 full-size 피처셋 기준 모델군 재비교, Quantile 후보 유지 확인 | [기록](2026-05-17_T4-E050_cold_final_feature_model_comparison.md) |
| 2026-05-17 | T4-E049 | T4-H38 | 완료 | Warm RandomForest artifact 생성, Ridge 대비 test median APE와 p95 APE 개선 확인 | [기록](2026-05-17_T4-E049_warm_random_forest_artifact_dry_run.md) |
| 2026-05-17 | T4-E048 | T4-H36,H37,H38 | 완료 | 피처 확정 후 모델 비교가 빠진 유사 사례를 점검하고 후속 우선순위 정리 | [기록](2026-05-17_T4-E048_experiment_gap_audit.md) |
| 2026-05-17 | T4-E047 | T4-H36 | 완료 | Warm 최종 피처셋 기준 비선형 모델 비교, RandomForest가 Ridge보다 우세 | [기록](2026-05-17_T4-E047_warm_nonlinear_model_comparison.md) |
| 2026-05-17 | T4-E046 | T4-H12,H30,H35 | 완료 | Track 4 최종 후보 모델, 피처, 라우팅, 출력 정책을 최종 보고서로 고정 | [기록](2026-05-17_T4-E046_final_summary_report.md) |
| 2026-05-17 | T4-E045 | T4-H12,H30,H35 | 완료 | 조건부 허용 manifest 기반 최종 Warm/Cold artifact 생성, 최종 후보 성능 재현 확인 | [기록](2026-05-17_T4-E045_final_artifact_dry_run.md) |
| 2026-05-17 | T4-E044 | T4-H34 | 완료 | Warm 과거 가격 통계 피처 조건부 허용 검증, 성능 개선 폭이 커서 조건부 허용 권장 | [기록](2026-05-17_T4-E044_warm_price_stats_policy.md) |
| 2026-05-17 | T4-E043 | T4-H12,H30 | 완료 | 최종 운영 후보 dry-run 실행, 배포 가능 artifact 생성과 Warm 가격 통계 피처 정책 이슈 확인 | [기록](2026-05-17_T4-E043_production_dry_run.md) |
| 2026-05-17 | T4-E042 | T4-H33 | 완료 | Cold low_risk 범위 폭 축소 후보를 비교했으나 coverage 유지와 폭 축소를 동시에 만족한 후보 없음 | [기록](2026-05-17_T4-E042_cold_low_risk_width_reduction.md) |
| 2026-05-17 | T4-E041 | T4-H3,H32 | 완료 | Warm low_history 구간 가격 범위 검증, 경고와 더 넓은 범위 필요 확인 | [기록](2026-05-17_T4-E041_warm_low_history_policy.md) |
| 2026-05-17 | T4-E040 | T4-H31 | 완료 | Cold low_risk 구간만 제한적 가격 범위 후보인지 검증, mid/high는 범위 과대로 보류 | [기록](2026-05-17_T4-E040_cold_low_risk_policy.md) |
| 2026-05-17 | T4-E039 | T4-H11,H24,H29 | 완료 | 가격 범위와 신뢰도 정책 보완, Cold 전체 적용은 범위 과대로 세부 가설 분리 | [기록](2026-05-17_T4-E039_interval_policy.md) |
| 2026-05-17 | T4-E038 | T4-H1,H2,H3,H4,H15,H21,H23 | 완료 | 최종 후보 validation/test 닫기 실험, Warm은 강하고 Cold는 신뢰도 정책 필요 | [기록](2026-05-17_T4-E038_candidate_closure.md) |
| 2026-05-17 | T4-E037 | T4-H3 | 완료 | Warm 작가 이력 피처 검증, artist_key와 train-only 가격 통계 조합이 최고 성능 | [기록](2026-05-17_T4-E037_warm_artist_history.md) |
| 2026-05-17 | T4-E036 | T4-H23 | 완료 | 출처별 성능/결측 감사, source는 모델 피처 제외 유지 | [기록](2026-05-17_T4-E036_source_slice_audit.md) |
| 2026-05-17 | T4-E035 | T4-H28 | 완료 | 재료-크기 조합 피처 실험, Cold 개선 신호 있으나 Warm 기본 채택은 보류 | [기록](2026-05-17_T4-E035_medium_size_combo.md) |
| 2026-05-17 | T4-E034 | T4-H25 | 완료 | 금지 피처 manifest 검사 구현, source/price/gallery 누수 예시 차단 확인 | [기록](2026-05-17_T4-E034_feature_manifest_check.md) |
| 2026-05-17 | T4-E033 | T4-H15 | 완료 | 크기 피처 축소 실험, Warm은 area_aspect, Cold는 median/tail 기준 후보 분리 | [기록](2026-05-17_T4-E033_size_feature_reduction.md) |
| 2026-05-17 | T4-E032 | T4-H13 | 완료 | 재료 세분화 피처 실험, 개선 폭이 작아 단독 채택 보류 | [기록](2026-05-17_T4-E032_material_granularity.md) |
| 2026-05-17 | T4-E031 | T4-H18, T4-H29 | 완료 | validation 기반 가격 범위와 신뢰도 calibration, Warm은 목표 근접, Cold는 부족 | [기록](2026-05-17_T4-E031_calibration_confidence.md) |
| 2026-05-17 | T4-E030 | T4-H9, T4-H17, T4-H24, T4-H26 | 완료 | Cold 위험 구간 분석, low risk와 high risk의 median APE 차이 확인 | [기록](2026-05-17_T4-E030_cold_risk_policy.md) |
| 2026-05-17 | T4-E029 | T4-H10, T4-H19 | 완료 | 작가 작품 수 기준 라우팅 threshold 실험, 기본 Warm 라우팅 유지 결론 | [기록](2026-05-17_T4-E029_routing_threshold.md) |
| 2026-05-17 | T4-E028 | T4-H21, T4-H22 | 완료 | 공유 모델/분리 모델 반복 검증, Warm은 분리 정책 우세, Cold는 split 민감도 확인 | [기록](2026-05-17_T4-E028_shared_vs_split_repeated.md) |
| 2026-05-17 | T4-E027 | T4-H8, T4-H16, T4-H27 | 완료 | 2D/3D slice 및 depth 피처 실험, 3D fallback은 median 개선이나 tail risk 악화로 보류 | [기록](2026-05-17_T4-E027_3d_depth_slice.md) |
| 2026-05-17 | T4-E026 | T4-H6, T4-H14 | 완료 | support unknown ablation 실행, Warm은 support 유지, Cold는 support 제외와 위험 flag 분리 검토 | [기록](2026-05-17_T4-E026_support_unknown_ablation.md) |
| 2026-05-17 | T4-E025 | T4-H4 | 완료 | Cold 모델 비교 실행, Quantile median APE `0.3486`, Huber p95 APE `1.2373` 확인 | [기록](2026-05-17_T4-E025_cold_model_comparison.md) |
| 2026-05-17 | T4-E024 | T4-H2, T4-H20 | 완료 | Warm 작가 피처 ablation 실행, 작가 key+이력 median APE `0.2697` 확인 | [기록](2026-05-17_T4-E024_warm_artist_ablation.md) |
| 2026-05-17 | T4-E023 | T4-H1 | 완료 | 구조-only Warm/Cold baseline 실행, Huber 기준 Warm `0.4148`, Cold `0.3567` 확인 | [기록](2026-05-17_T4-E023_structure_baseline.md) |
| 2026-05-17 | T4-E022 | T4-H13~T4-H30 | 완료 | Track 3 가설 축을 Track 4 1차 시장 데이터 특성에 맞게 확장 | [기록](2026-05-17_T4-E022_hypothesis_expansion.md) |
| 2026-05-17 | T4-E021 | - | 완료 | Track 4 모델 실험 전 가설표, 결과표, 대시보드 자동 생성 체계 구축 | [기록](2026-05-17_T4-E021_experiment_dashboard_framework.md) |
| 2026-05-17 | T4-E020 | - | 완료 | 추가 데이터 반영에 대비해 Track 4 데이터셋 파이프라인과 실행 후 누수/품질 확인 기준 정리 | [기록](2026-05-17_T4-E020_dataset_pipeline_update.md) |
| 2026-05-15 | T4-E019 | - | 완료 | 데이터 준비 체크포인트와 모델 실험 가설을 분리하도록 Track 4 계획서 구조 정리 | [기록](2026-05-15_T4-E019_plan_structure_cleanup.md) |
| 2026-05-15 | T4-E018 | T4-H1~T4-H5 | 완료 | Track 4 모델 실험을 Warm / Cold로 분리해서 진행하는 프로세스 문서화 | [기록](2026-05-15_T4-E018_warm_cold_process_design.md) |
| 2026-05-15 | T4-E017 | T4-H0 | 완료 | 추가 데이터 수집 후 재실행 가능한 Track 4 클렌징 파이프라인 문서화 및 실행 스크립트 추가 | [기록](2026-05-15_T4-E017_cleaning_pipeline_documentation.md) |
| 2026-05-15 | T4-E016 | T4-C1~T4-C7 | 완료 | cleaned_v2 전체 94개 컬럼 값 정합성 재점검, 파생값 계산 불일치 0건 확인 | [기록](2026-05-15_T4-E016_column_value_consistency_audit.md) |
| 2026-05-15 | T4-E015 | T4-H0 | 완료 | Track 4 Warm/Cold split 생성, `artist_name_ko` 포함 train `28,930`건 확보 | [기록](2026-05-15_T4-E015_split_generation.md) |
| 2026-05-15 | T4-E014 | T4-C1~T4-C7 | 완료 | 감사 결과 반영 `cleaned_v2` 생성, 학습 후보 `34,239`건과 한글 작가명 `54,840`건 확보 | [기록](2026-05-15_T4-E014_cleaned_v2_generation.md) |
| 2026-05-15 | T4-E013 | T4-C7 | 완료 | 갤러리 메타데이터 점검, 티어 직접 매칭 `331`건으로 기본 피처 제외 판단 | [기록](2026-05-15_T4-E013_gallery_metadata_audit.md) |
| 2026-05-15 | T4-E012 | T4-C6 | 완료 | 출처 편향 점검, source는 모델 피처 제외 원칙 재확인 | [기록](2026-05-15_T4-E012_source_bias_audit.md) |
| 2026-05-15 | T4-E011 | T4-C5 | 완료 | 중복 정합성 감사, 같은 출처 의미 중복 `954`그룹과 출처 간 엄격 중복 `4`그룹 확인 | [기록](2026-05-15_T4-E011_duplicate_consistency_audit.md) |
| 2026-05-15 | T4-E010 | T4-C3 | 완료 | 재료/지지체 1차 매핑 감사, 재료 정상 후보 `53,646`건 확인 | [기록](2026-05-15_T4-E010_medium_support_consistency_audit.md) |
| 2026-05-15 | T4-E009 | T4-C4 | 완료 | 작가명 정합성 감사, split 후보 작가 key `3,033`개와 artist master 후보 `120`명 확인 | [기록](2026-05-15_T4-E009_artist_consistency_audit.md) |
| 2026-05-15 | T4-E008 | T4-C2 | 완료 | raw collected 기준 크기 정합성 감사, 정상 후보 `54,441`건 확인 | [기록](2026-05-15_T4-E008_size_consistency_audit.md) |
| 2026-05-15 | T4-E007 | T4-C1 | 완료 | raw collected 기준 가격 정합성 감사, 정상 후보 `34,883`건 확인 | [기록](2026-05-15_T4-E007_price_consistency_audit.md) |
| 2026-05-15 | T4-E006 | T4-H0 | 완료 | raw collected 기반 클렌징 실험 계획 수립 | [기록](2026-05-15_T4-E006_cleaning_experiment_plan.md) |
| 2026-05-15 | T4-E005 | T4-H0 | 완료 | 원본 컬럼 보존 raw collected `54,842`건 생성 | [기록](2026-05-15_T4-E005_raw_collected_union.md) |
| 2026-05-15 | T4-E004 | T4-H0 | 완료 | raw 통합본에서 원본 수집값/파싱값/파생값/관리값 구분 | [기록](2026-05-15_T4-E004_raw_column_provenance.md) |
| 2026-05-15 | T4-E003 | T4-H0 | 완료 | cleaned v1 생성, 학습 후보 `32,343`건 및 갤러리 티어 기준표 매칭 `1,231`건 확인 | [기록](2026-05-15_T4-E003_primary_market_cleaned_v1.md) |
| 2026-05-15 | T4-E002 | T4-H0 | 완료 | raw 통합본 컬럼 감사, 가격/크기/연도 이상값 확인 | [기록](2026-05-15_T4-E002_primary_market_column_audit.md) |
| 2026-05-15 | T4-E001 | T4-H0 | 1차 완료 | 1차 시장 raw 통합본 `33,276`건 생성 | [기록](2026-05-15_T4-E001_primary_market_raw_union.md) |
| 2026-05-15 | - | - | 준비 | Track 4 문서 구조 생성 | - |
