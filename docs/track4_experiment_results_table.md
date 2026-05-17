# Track 4 실험 결과 요약표

- 목적: Track 4 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-17
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-17 | T4-E021 | - | 완료 | 문서 기준 | 모델 미사용 | 문서/대시보드 구조 | - | - | Track 4 가설표, 결과표, 자동 대시보드 체계 구축 | [기록](track4_experiments/2026-05-17_T4-E021_experiment_dashboard_framework.md), [대시보드](track4_experiment_dashboard.html) |
| 2026-05-17 | T4-E020 | T4-H5, T4-H7 | 완료 | `cleaned_v2`, `track4_split` | 모델 미사용 | 데이터셋 검증 | Warm split 작가 train 존재 확인, val_warm `67`, test_warm `137` | Cold/train 작가 겹침 `0`, Cold `artist_works_log > 0` `0` | 모델 실험 가능한 데이터셋으로 확정 | [기록](track4_experiments/2026-05-17_T4-E020_dataset_pipeline_update.md), [품질 검토](track4_dataset_final_quality_review_2026-05-17.md) |
| 2026-05-15 | T4-E019 | - | 완료 | 문서 기준 | 모델 미사용 | 문서 구조 | - | - | 데이터 준비 체크포인트와 모델 가설 분리 | [기록](track4_experiments/2026-05-15_T4-E019_plan_structure_cleanup.md) |
| 2026-05-15 | T4-E018 | T4-H1~T4-H5 | 완료 | 문서 기준 | 모델 미사용 | Warm/Cold 프로세스 | - | - | Warm / Cold 분리 실험 절차 문서화 | [기록](track4_experiments/2026-05-15_T4-E018_warm_cold_process_design.md) |
| 2026-05-15 | T4-E017 | - | 완료 | raw/cleaned pipeline | 모델 미사용 | 데이터 파이프라인 | - | - | 클렌징 파이프라인 실행 구조 문서화 | [기록](track4_experiments/2026-05-15_T4-E017_cleaning_pipeline_documentation.md) |

## 다음 실험 후보

- T4-E022: T4-H1 구조-only Warm / Cold baseline
- T4-E023: T4-H2 Warm 작가 피처 ablation
- T4-E024: T4-H4 Cold robust 모델 비교
- T4-E025: T4-H6 support unknown 처리 ablation
- T4-E026: T4-H8 2D/3D slice 및 depth 피처 실험
