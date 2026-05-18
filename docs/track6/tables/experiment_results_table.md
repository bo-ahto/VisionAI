# Track 6 실험 결과 요약표

- 목적: Track6 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-18
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록
- 상태: T6-E001C feature/label 분리 완료

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
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
