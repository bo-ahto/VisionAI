# Track 6 실험 결과 요약표

- 목적: Track6 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-18
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록
- 상태: T6-E001C feature/label 분리 완료

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-18 | T6-E009 | T6-H8 | 검증 완료 | Track6 train+validation | CatBoost / HistQuantile / Huber | 최종 후보 피처 | artifact 생성 | artifact 생성 | 최종 후보 manifest ready | [기록](../experiments/2026-05-18_T6-E009_final_artifact_manifest.md) |
| 2026-05-18 | T6-E008 | T6-H7 | 검증 완료 | Track6 name-corrected split | slice 분석 | risk flags | 위험 구간 분석 | 위험 후보 `11`개 | 신뢰도/가격 범위 정책 필요 | [기록](../experiments/2026-05-18_T6-E008_risk_policy_analysis.md) |
| 2026-05-18 | T6-E007 | T6-H6 | 검증 완료 | Track6 name-corrected split | CatBoost / HistQuantile / Huber | T6-E006 선정 후보 | test `0.3407` (`base_medium_size`) | median test `0.3799`, p95 test `2.2865` | test holdout 확인 완료 | [기록](../experiments/2026-05-18_T6-E007_test_confirmation.md) |
| 2026-05-18 | T6-E006 | T6-H6 | 부분 검증 | Track6 name-corrected split | 후보 선정 로직 | validation 후보 피처 | Warm 후보 `0.2665` (`base_medium_size`) | Cold 후보 median `0.3782`, p95 `1.3835` | test 전 후보 고정 | [기록](../experiments/2026-05-18_T6-E006_validation_candidate_selection.md) |
| 2026-05-18 | T6-E005 | T6-H5 | 검증 완료 | Track6 name-corrected split | CatBoost / HistQuantile / Huber | 운영 가능 조합 피처 | best `0.2665` (`base_medium_size`) | median best `0.3782` (`base`), p95 best `1.3835` (`base_size_shape`) | Warm/Cold별 후보 피처셋 분리 필요 | [기록](../experiments/2026-05-18_T6-E005_feature_combo_ablation.md) |
| 2026-05-18 | T6-E004 | T6-H4 | 검증 완료 | Track6 name-corrected split | hist_quantile_ordinal / huber_onehot | Cold 구조 피처 | - | median best `0.3903` (`hist_quantile_ordinal`), p95 best `1.4674` (`huber_onehot`) | Cold 모델 후보 기준 확보 | [기록](../experiments/2026-05-18_T6-E004_cold_model_compare.md) |
| 2026-05-18 | T6-E003 | T6-H3 | 검증 완료 | Track6 name-corrected split | CatBoost | Warm 작가 피처 ablation | best `0.2737` (`structure_plus_artist_key`), 구조-only 대비 `0.2248` 개선 | - | Warm 작가 피처 유지 가치 확인 | [기록](../experiments/2026-05-18_T6-E003_warm_artist_ablation.md) |
| 2026-05-18 | T6-E002 | T6-H2 | 검증 완료 | Track6 name-corrected split | hist_gbdt_ordinal / lightgbm_basic | 구조-only 피처 | best `0.4579` (`hist_gbdt_ordinal`) | best `0.4029` (`lightgbm_basic`) | 구조 피처 baseline 기준 확보 | [기록](../experiments/2026-05-18_T6-E002_structure_only_baseline.md) |
| 2026-05-18 | T6-E001C | T6-H1 | 검증 완료 | Track6 name-corrected split | 모델 미사용 | feature/label manifest | Warm feature 누수 컬럼 0 | Cold feature 누수 컬럼 0 | feature/label 분리 상태 `pass` | [기록](../experiments/2026-05-18_T6-E001C_feature_label_pipeline.md), [보고서](../dataset/feature_label_pipeline_report.md) |
| 2026-05-18 | T6-E001B | T6-H1 | 검토 완료 | Track6 name-corrected split | 모델 미사용 | column quality metadata | Warm 1작품 작가 0, train 누락 0 | Cold 이름 겹침 0, artist history 0 | fail 0, review 14. 모델 실험 진행 가능 | [기록](../experiments/2026-05-18_T6-E001B_column_quality_validation.md), [보고서](../dataset/column_quality_report.md) |
| 2026-05-18 | T6-E001 | T6-H1 | 검증 완료 | Track6 보정 후보 데이터 | 모델 미사용 | split metadata | val `523`건 / test `607`건 | val `2,793`건 / test `3,240`건, 이름 겹침 0 | Track6 name-corrected split 상태 `pass` | [기록](../experiments/2026-05-18_T6-E001_strict_split_generation.md), [보고서](../dataset/split_report.md) |

## 다음 실험 후보

- T6-E002: 구조-only baseline
- T6-E003: Warm 작가 피처 ablation
- T6-E004: Cold 모델 비교
- T6-E005: 피처 조합 실험
- T6-E006: validation 기준 최종 후보 선정
- T6-E007: test 최종 확인
- T6-E008: 가격 범위/신뢰도 정책 검증
- T6-E009: 최종 artifact 생성
