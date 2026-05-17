# Track 4 실험 결과 요약표

- 목적: Track 4 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-17
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-17 | T4-E028 | T4-H21, T4-H22 | 완료 | `track4_train` 내부 반복 split 5회 | 공유 Quantile, 분리 Warm Ridge/Cold Quantile | 공유 구조-only vs 분리 정책 | 분리 정책 median APE 평균 `0.3559`, 공유 `0.5325`보다 우세 | Cold median APE 평균 `0.4280`, 표준편차 `0.0454` | Warm/Cold 분리 정책 유지, 후속 실험도 반복 검증 권장 | [기록](../experiments/2026-05-17_T4-E028_shared_vs_split_repeated.md), [결과](../../../data/track4/results/t4_e028_shared_vs_split_repeated_metrics.json) |
| 2026-05-17 | T4-E027 | T4-H8, T4-H16, T4-H27 | 완료 | `track4_train`, `val_warm`, `val_cold` | Warm Ridge, Cold Quantile | base size, depth/volume, 3D fallback | Warm 3D는 1건이라 참고만 가능 | conditional fallback 전체 median APE `0.3545`, 3D median `0.6106`, 3D p95 `6.7154` | 3D 별도 관리는 필요하지만 fallback은 tail risk 악화로 보류 | [기록](../experiments/2026-05-17_T4-E027_3d_depth_slice.md), [결과](../../../data/track4/results/t4_e027_3d_depth_slice_metrics.json) |
| 2026-05-17 | T4-E026 | T4-H6, T4-H14 | 완료 | `track4_train`, `val_warm`, `val_cold` | Warm Ridge, Cold Quantile | support 제외/포함/unknown flag/bucket | support_category median APE `0.2697`로 최선 | no_support median APE `0.3410`로 최선, unknown 구간 오차 큼 | Warm은 support 유지, Cold는 예측 피처 제외와 위험 flag 분리 검토 | [기록](../experiments/2026-05-17_T4-E026_support_unknown_ablation.md), [결과](../../../data/track4/results/t4_e026_support_unknown_ablation_metrics.json) |
| 2026-05-17 | T4-E025 | T4-H4 | 완료 | `track4_train`, `val_cold` | Quantile, Huber, Ridge, LightGBM, XGBoost, CatBoost 등 | 구조-only: medium/support/size/3D | - | Quantile median APE `0.3486`, Huber p95 APE `1.2373` | Cold는 robust 선형 계열 우세, Quantile/Huber를 후보 유지 | [기록](../experiments/2026-05-17_T4-E025_cold_model_comparison.md), [결과](../../../data/track4/results/t4_e025_cold_model_comparison_metrics.json) |
| 2026-05-17 | T4-E024 | T4-H2, T4-H20 | 완료 | `track4_train`, `val_warm` | Ridge | 구조-only, 작가 이력, 작가 key | 작가 key+이력 median APE `0.2697`, 구조-only `0.4619`보다 개선 | - | Warm 작가 key는 유지 후보, 이력 단독 대체는 불리 | [기록](../experiments/2026-05-17_T4-E024_warm_artist_ablation.md), [결과](../../../data/track4/results/t4_e024_warm_artist_ablation_metrics.json) |
| 2026-05-17 | T4-E023 | T4-H1 | 완료 | `track4_train`, `val_warm`, `val_cold` | Dummy median, Ridge, Huber | 구조-only: medium/support/size/3D | Huber median APE `0.4148`, dummy `0.7027`보다 개선 | Huber median APE `0.3567`, dummy `0.7424`보다 개선 | 구조-only baseline은 Huber를 기준 후보로 부분 채택 | [기록](../experiments/2026-05-17_T4-E023_structure_baseline.md), [결과](../../../data/track4/results/t4_e023_structure_baseline_metrics.json) |
| 2026-05-17 | T4-E022 | T4-H13~T4-H30 | 완료 | Track 3 가설표, Track 4 데이터 품질 리포트 | 모델 미사용 | 가설/연구방법 문서 | - | - | Track 3 가설 축을 Track 4 1차 시장 데이터 특성에 맞게 확장 | [기록](../experiments/2026-05-17_T4-E022_hypothesis_expansion.md), [가설표](hypothesis_table.md) |
| 2026-05-17 | T4-E021 | - | 완료 | 문서 기준 | 모델 미사용 | 문서/대시보드 구조 | - | - | Track 4 가설표, 결과표, 자동 대시보드 체계 구축 | [기록](../experiments/2026-05-17_T4-E021_experiment_dashboard_framework.md), [대시보드](../dashboard/experiment_dashboard.html) |
| 2026-05-17 | T4-E020 | T4-H5, T4-H7 | 완료 | `cleaned_v2`, `track4_split` | 모델 미사용 | 데이터셋 검증 | Warm split 작가 train 존재 확인, val_warm `67`, test_warm `137` | Cold/train 작가 겹침 `0`, Cold `artist_works_log > 0` `0` | 모델 실험 가능한 데이터셋으로 확정 | [기록](../experiments/2026-05-17_T4-E020_dataset_pipeline_update.md), [품질 검토](../dataset/final_quality_review_2026-05-17.md) |
| 2026-05-15 | T4-E019 | - | 완료 | 문서 기준 | 모델 미사용 | 문서 구조 | - | - | 데이터 준비 체크포인트와 모델 가설 분리 | [기록](../experiments/2026-05-15_T4-E019_plan_structure_cleanup.md) |
| 2026-05-15 | T4-E018 | T4-H1~T4-H5 | 완료 | 문서 기준 | 모델 미사용 | Warm/Cold 프로세스 | - | - | Warm / Cold 분리 실험 절차 문서화 | [기록](../experiments/2026-05-15_T4-E018_warm_cold_process_design.md) |
| 2026-05-15 | T4-E017 | - | 완료 | raw/cleaned pipeline | 모델 미사용 | 데이터 파이프라인 | - | - | 클렌징 파이프라인 실행 구조 문서화 | [기록](../experiments/2026-05-15_T4-E017_cleaning_pipeline_documentation.md) |

## 다음 실험 후보

- T4-E029: T4-H10/T4-H19 작가 작품 수 기준 라우팅 threshold
- T4-E030: T4-H17/T4-H24 Cold 위험 구간 및 출력 정책 후보
- T4-E031: T4-H18/T4-H29 가격 범위와 신뢰도 calibration
