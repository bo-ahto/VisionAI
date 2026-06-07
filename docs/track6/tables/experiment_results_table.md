# Track 6 실험 결과 요약표

- 목적: Track6 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-19
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록
- 상태: T6-E010 헤도닉 작가명 + 호수 / ln 변환 실험 완료

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-19 | T6-E010 | T6-H9, T6-H10 | 검증 완료 | `track6_feature_candidates_name_corrected.csv` 기반 실험 전용 split | Ridge hedonic linear regression | artist_name_ko, estimated_ho, ln_estimated_ho | log 최고 median APE `0.1946`, Within-50 `0.8519` | Cold 전용 log median APE `0.5083`, Warm모델 Cold적용 log `0.4840` | ln 변환 채택, Warm은 작가명+ln호수 유효, Cold는 추가 피처 필요 | [기록](../experiments/2026-05-19_T6-E010_hedonic_artist_ho_log.md), [HTML 일지](../../../experiments/track6/T6-E010_hedonic_artist_ho_log/experiment_log.html) |
| 2026-05-29 | T6-E009 | T6-H8 | 검증 완료 | Track6 train+validation | Huber / CatBoost / LightGBM | 최종 후보 피처 | artifact 생성 | artifact 생성 | 최종 후보 manifest ready | [기록](../experiments/2026-05-18_T6-E009_final_artifact_manifest.md) |
| 2026-05-29 | T6-E008 | T6-H7 | 검증 완료 | Track6 name-corrected split | slice 분석 | risk flags | 위험 구간 분석 | 위험 후보 `14`개 | 신뢰도/가격 범위 정책 필요 | [기록](../experiments/2026-05-18_T6-E008_risk_policy_analysis.md) |
| 2026-05-29 | T6-E007 | T6-H6 | 검증 완료 | Track6 name-corrected split | Huber / CatBoost / LightGBM | T6-E006 선정 후보 | test `0.2274` (`base_existing_combo`) | median test `0.4859`, p95 test `4.7612` | test holdout 확인 완료 | [기록](../experiments/2026-05-18_T6-E007_test_confirmation.md) |
| 2026-05-29 | T6-E006 | T6-H6 | 부분 검증 | Track6 name-corrected split | 후보 선정 로직 | validation 후보 피처 | Warm 후보 `0.2126` (`base_existing_combo`) | Cold 후보 median `0.3848`, p95 `1.9783` | test 전 후보 고정 | [기록](../experiments/2026-05-18_T6-E006_validation_candidate_selection.md) |
| 2026-05-29 | T6-E005 | T6-H5 | 검증 완료 | Track6 name-corrected split | Huber / CatBoost / LightGBM | 운영 가능 조합 피처 | best `0.2129` (`base_existing_combo`) | median best `0.3848` (`base_support_size`), p95 best `1.9783` (`base_large_flags`) | Warm/Cold별 후보 피처셋 분리 필요 | [기록](../experiments/2026-05-18_T6-E005_feature_combo_ablation.md) |
| 2026-05-29 | T6-E005 | T6-H5 | 검증 완료 | Track6 name-corrected split | Huber / CatBoost / LightGBM | 운영 가능 조합 피처 | best `0.2126` (`base_existing_combo`) | median best `0.3848` (`base_support_size`), p95 best `1.9783` (`base_large_flags`) | Warm/Cold별 후보 피처셋 분리 필요 | [기록](../experiments/2026-05-18_T6-E005_feature_combo_ablation.md) |
| 2026-05-18 | T6-E004 | T6-H4 | 검증 완료 | Track6 name-corrected split | hist_quantile_ordinal / huber_onehot | Cold 구조 피처 | - | median best `0.3903` (`hist_quantile_ordinal`), p95 best `1.4674` (`huber_onehot`) | Cold 모델 후보 기준 확보 | [기록](../experiments/2026-05-18_T6-E004_cold_model_compare.md) |
| 2026-05-18 | T6-E003 | T6-H3 | 검증 완료 | Track6 name-corrected split | CatBoost | Warm 작가 피처 ablation | best `0.2737` (`structure_plus_artist_key`), 구조-only 대비 `0.2248` 개선 | - | Warm 작가 피처 유지 가치 확인 | [기록](../experiments/2026-05-18_T6-E003_warm_artist_ablation.md) |
| 2026-05-18 | T6-E002 | T6-H2 | 검증 완료 | Track6 name-corrected split | hist_gbdt_ordinal / lightgbm_basic | 구조-only 피처 | best `0.4579` (`hist_gbdt_ordinal`) | best `0.4029` (`lightgbm_basic`) | 구조 피처 baseline 기준 확보 | [기록](../experiments/2026-05-18_T6-E002_structure_only_baseline.md) |
| 2026-05-18 | T6-E001C | T6-H1 | 검증 완료 | Track6 name-corrected split | 모델 미사용 | feature/label manifest | Warm feature 누수 컬럼 0 | Cold feature 누수 컬럼 0 | feature/label 분리 상태 `pass` | [기록](../experiments/2026-05-18_T6-E001C_feature_label_pipeline.md), [보고서](../dataset/feature_label_pipeline_report.md) |
| 2026-05-18 | T6-E001B | T6-H1 | 검토 완료 | Track6 name-corrected split | 모델 미사용 | column quality metadata | Warm 1작품 작가 0, train 누락 0 | Cold 이름 겹침 0, artist history 0 | fail 0, review 14. 모델 실험 진행 가능 | [기록](../experiments/2026-05-18_T6-E001B_column_quality_validation.md), [보고서](../dataset/column_quality_report.md) |
| 2026-05-18 | T6-E001 | T6-H1 | 검증 완료 | Track6 보정 후보 데이터 | 모델 미사용 | split metadata | val `523`건 / test `607`건 | val `2,793`건 / test `3,240`건, 이름 겹침 0 | Track6 name-corrected split 상태 `pass` | [기록](../experiments/2026-05-18_T6-E001_strict_split_generation.md), [보고서](../dataset/split_report.md) |

## 완료된 실험 흐름

- T6-E001~T6-E001C: split, 컬럼 품질, feature/label 분리 검증
- T6-E002: 구조-only baseline 확인
- T6-E003: Warm 작가 피처 효과 확인
- T6-E004: Cold 모델 후보 비교
- T6-E005: 운영 가능 피처 조합 비교
- T6-E006: validation 기준 후보 고정
- T6-E007: test holdout 최종 확인
- T6-E008: 신뢰도/위험 구간 분석
- T6-E009: 최종 후보 artifact manifest 생성

## 후속 작업

- 서비스 입력 스키마와 Track6 피처 생성 로직 연결
- Warm/Cold 라우팅 로직 구현
- 신뢰도 경고 문구와 가격 범위 표시 정책 구현
