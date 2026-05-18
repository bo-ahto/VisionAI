# Track 5 실험 기록 인덱스

- 목적: Track 5 개별 실험 기록을 한눈에 관리
- 정렬 기준: 최신 실험이 위로 오도록 관리

| 날짜 | 실험 ID | 연결 가설 | 상태 | 요약 | 기록 |
|---|---|---|---|---|---|
| 2026-05-18 | T5-E021 | T5-H24 | 완료 | 최종 artifact 생성 전 핵심 파일 존재와 SHA256 manifest 생성 확인 | [기록](2026-05-18_T5-E021_artifact_precheck.md) |
| 2026-05-18 | T5-E020 | T5-H23 | 완료 | Cold 가격대 보정과 위험 경고 정책 결합, hybrid 정책이 baseline 대비 개선 | [기록](2026-05-18_T5-E020_cold_correction_policy.md) |
| 2026-05-18 | T5-E019 | T5-H22 | 완료 | Warm OOF extended 후보를 최종 Huber 설정으로 재검증, 1순위 교체는 보류 | [기록](2026-05-18_T5-E019_warm_oof_extended_final_setting.md) |
| 2026-05-18 | T5-E018 | T5-H21 | 완료 | Cold 예측 가격대별 residual 보정으로 median/Within 개선, p95는 개선 없음 | [기록](2026-05-18_T5-E018_cold_price_band_correction.md) |
| 2026-05-18 | T5-E017 | T5-H20 | 완료 | support_unknown 전용 fallback은 전체 median 소폭 개선이나 해당 구간 p95 악화로 보류 | [기록](2026-05-18_T5-E017_cold_support_unknown_fallback.md) |
| 2026-05-18 | T5-E016 | T5-H19 | 완료 | Cold missing flag 추가는 기준선 대비 성능 개선이 없어 미채택 | [기록](2026-05-18_T5-E016_cold_missing_flags.md) |
| 2026-05-18 | T5-E015 | T5-H18 | 완료 | Warm OOF 작가 통계 검증, 확장 통계에서 p95 개선 신호 확인 | [기록](2026-05-18_T5-E015_warm_oof_artist_stats.md) |
| 2026-05-18 | T5-E014 | T5-H17 | 완료 | Warm 작가 가격 통계 확장 단독 추가는 median/p95 개선 없어 보류 | [기록](2026-05-18_T5-E014_warm_artist_stat_expansion.md) |
| 2026-05-18 | T5-E013 | T5-H16 | 완료 | validation 오차 기반 가격 범위가 test에서 어느 정도 실제 가격을 포함하는지 확인 | [기록](2026-05-18_T5-E013_price_interval_coverage.md) |
| 2026-05-18 | T5-E012 | T5-H15 | 완료 | Cold final 후보 예측 결과를 위험 구간별로 나누어 support/medium unknown 위험 신호 확인 | [기록](2026-05-18_T5-E012_cold_risk_slice_analysis.md) |
| 2026-05-18 | T5-E011 | T5-H14 | 완료 | Warm Huber 반복 횟수 재검증, max_iter 3000에서 수렴 경고 해소와 후보 판단 유지 확인 | [기록](2026-05-18_T5-E011_warm_huber_convergence_recheck.md) |
| 2026-05-18 | T5-E010 | T5-H13 | 완료 | validation에서 고정한 최종 후보를 test에 적용, Warm 후보 유지와 Cold 가격 범위 정책 필요 확인 | [기록](2026-05-18_T5-E010_final_candidate_test.md) |
| 2026-05-18 | T5-E009 | T5-H12 | 완료 | test를 보기 전 Warm/Cold 최종 확인 후보와 판단 기준을 문서로 고정 | [기록](2026-05-18_T5-E009_candidate_freeze_before_test.md) |
| 2026-05-18 | T5-E008 | T5-H11 | 완료 | 후보 피처셋 기반 모델군 재비교, Warm은 Huber+full_size, Cold는 Quantile+full_size 1순위 | [기록](2026-05-18_T5-E008_candidate_model_comparison.md) |
| 2026-05-18 | T5-E007 | T5-H10 | 완료 | 생성 조합 피처 검증, 일부 개선 신호는 있으나 단일 강한 승자는 없어 보조 후보 유지 | [기록](2026-05-18_T5-E007_combo_feature_validation.md) |
| 2026-05-18 | T5-E006 | T5-H9 | 완료 | 기준 모델 기반 size/support/3D 피처 ablation, Warm/Cold 모두 full_size 후보 유지 | [기록](2026-05-18_T5-E006_feature_ablation.md) |
| 2026-05-18 | T5-E005 | T5-H8 | 완료 | E002~E004 결과를 종합해 Warm/Cold 기준 모델과 기준 피처셋 고정 | [기록](2026-05-18_T5-E005_baseline_model_freeze.md) |
| 2026-05-18 | T5-E004 | T5-H4 | 완료 | Cold 모델군 비교 실행, QuantileRegressor가 median APE와 p95 APE 기준 최선 | [기록](2026-05-18_T5-E004_cold_model_comparison.md) |
| 2026-05-18 | T5-E003 | T5-H3 | 완료 | Warm 작가 피처 ablation 실행, 작가 key+이력+train 가격 통계가 구조-only 대비 크게 개선 | [기록](2026-05-18_T5-E003_warm_artist_ablation.md) |
| 2026-05-18 | T5-E002 | T5-H2 | 완료 | 구조-only baseline 실행, Huber가 Warm/Cold 모두에서 단순 중앙값보다 개선 | [기록](2026-05-18_T5-E002_structure_baseline.md) |
| 2026-05-18 | T5-E001 | T5-H1 | 완료 | Track5 split 생성, Warm test 표본 확대와 Cold/train 작가 분리 확인 | [기록](2026-05-18_T5-E001_split_generation.md) |
