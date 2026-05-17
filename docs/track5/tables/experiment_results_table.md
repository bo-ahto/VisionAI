# Track 5 실험 결과 요약표

- 목적: Track 5 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-18
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-18 | T5-E006 | T5-H9 | 완료 | track5 train, val_warm, val_cold | Warm Ridge, Cold Quantile | size/support/3D 피처 조합 | warm_full_size median `0.2326`, p95 `0.8465`; area_only median `0.2298` | cold_full_size median `0.3432`, p95 `1.8235` | Warm/Cold 모두 full_size 후보 유지, 생성 조합 피처 후속 검증 필요 | [기록](../experiments/2026-05-18_T5-E006_feature_ablation.md), [결과](../../../data/track5/results/t5_e006_feature_ablation_metrics.json) |
| 2026-05-18 | T5-E005 | T5-H8 | 완료 | T5-E002~E004 결과 | 모델 미사용 | 기준 모델/피처 | Warm 기준 Ridge+작가 key/이력/가격통계, median APE `0.2279` | Cold 기준 Quantile+구조 피처, median APE `0.3564` | 이후 피처 실험 기준선 고정 | [기록](../experiments/2026-05-18_T5-E005_baseline_model_freeze.md) |
| 2026-05-18 | T5-E004 | T5-H4 | 완료 | track5 train, val_cold | Quantile, Huber, Ridge, RF, HGB, LightGBM, XGBoost, CatBoost | Cold 구조-only | - | Quantile median APE `0.3564`, p95 `1.8218` | Cold 기준 모델은 QuantileRegressor로 설정 | [기록](../experiments/2026-05-18_T5-E004_cold_model_comparison.md), [결과](../../../data/track5/results/t5_e004_cold_model_comparison_metrics.json) |
| 2026-05-18 | T5-E003 | T5-H3 | 완료 | track5 train, val_warm | Ridge | 구조, 작가 key, 작가 이력, train 가격 통계 | best median APE `0.2279`, p95 `0.9083` | - | Warm은 작가 key+이력+train 가격 통계 후보 유지 | [기록](../experiments/2026-05-18_T5-E003_warm_artist_ablation.md), [결과](../../../data/track5/results/t5_e003_warm_artist_ablation_metrics.json) |
| 2026-05-18 | T5-E002 | T5-H2 | 완료 | track5 train, val_warm, val_cold | Dummy, Ridge, Huber | 구조-only | Huber median APE `0.4662`, p95 `2.9250` | Huber median APE `0.3718`, p95 `1.8598` | 구조-only 기준 모델은 Huber로 설정 | [기록](../experiments/2026-05-18_T5-E002_structure_baseline.md), [결과](../../../data/track5/results/t5_e002_structure_baseline_metrics.json) |
| 2026-05-18 | T5-E001 | T5-H1 | 완료 | Track4 feature candidates | 모델 미사용 | split 기준 | test_warm `511`건, `215`명 | test_cold `2,896`건, `216`명, train 작가 겹침 `0` | Track5 모델 실험 기준 split으로 사용 가능 | [기록](../experiments/2026-05-18_T5-E001_split_generation.md), [보고서](../dataset/split_report.md) |

## 다음 실험 후보

- T5-E007: 생성 조합 피처 검증
