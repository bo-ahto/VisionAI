# Track 5 실험 기록 인덱스

- 목적: Track 5 개별 실험 기록을 한눈에 관리
- 정렬 기준: 최신 실험이 위로 오도록 관리

| 날짜 | 실험 ID | 연결 가설 | 상태 | 요약 | 기록 |
|---|---|---|---|---|---|
| 2026-05-18 | T5-E006 | T5-H9 | 완료 | 기준 모델 기반 size/support/3D 피처 ablation, Warm/Cold 모두 full_size 후보 유지 | [기록](2026-05-18_T5-E006_feature_ablation.md) |
| 2026-05-18 | T5-E005 | T5-H8 | 완료 | E002~E004 결과를 종합해 Warm/Cold 기준 모델과 기준 피처셋 고정 | [기록](2026-05-18_T5-E005_baseline_model_freeze.md) |
| 2026-05-18 | T5-E004 | T5-H4 | 완료 | Cold 모델군 비교 실행, QuantileRegressor가 median APE와 p95 APE 기준 최선 | [기록](2026-05-18_T5-E004_cold_model_comparison.md) |
| 2026-05-18 | T5-E003 | T5-H3 | 완료 | Warm 작가 피처 ablation 실행, 작가 key+이력+train 가격 통계가 구조-only 대비 크게 개선 | [기록](2026-05-18_T5-E003_warm_artist_ablation.md) |
| 2026-05-18 | T5-E002 | T5-H2 | 완료 | 구조-only baseline 실행, Huber가 Warm/Cold 모두에서 단순 중앙값보다 개선 | [기록](2026-05-18_T5-E002_structure_baseline.md) |
| 2026-05-18 | T5-E001 | T5-H1 | 완료 | Track5 split 생성, Warm test 표본 확대와 Cold/train 작가 분리 확인 | [기록](2026-05-18_T5-E001_split_generation.md) |
