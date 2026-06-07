# OP-V01-CAL-05 범위 정책 반복 검증 결과

## 1. 실행 요약

- 기준 정책: `baseline`
- 후보 정책: `fixed_125`
- 점가격: 변경 없음
- 검증 대상: 기존 Warm validation/test split
- 반복 검증: test row bootstrap 100회, test artist bootstrap 100회

## 2. validation/test 전체 지표

| sample | n | baseline_coverage | fixed_125_coverage | delta_coverage | baseline_p90_range_ratio | fixed_125_p90_range_ratio | width_penalty | baseline_top5_coverage | fixed_125_top5_coverage | baseline_severe_coverage | fixed_125_severe_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 519 | 0.9480 | 0.9595 | 0.0116 | 9.8223 | 17.3889 | 1.7704 | 0.8846 | 0.8846 | 0.3333 | 0.3333 |
| test | 607 | 0.9226 | 0.9588 | 0.0362 | 8.6048 | 14.7375 | 1.7127 | 0.8710 | 0.9032 | 0.3571 | 0.6429 |

## 3. bootstrap 요약

| mode | runs | delta_coverage_mean | delta_coverage_std | delta_coverage_min | delta_coverage_p05 | delta_coverage_median | delta_coverage_max | positive_delta_rate | width_penalty_median | width_penalty_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_bootstrap | 100 | 0.0359 | 0.0075 | 0.0214 | 0.0262 | 0.0354 | 0.0564 | 1.0000 | 1.7160 | 1.7517 |
| row_bootstrap | 100 | 0.0363 | 0.0072 | 0.0148 | 0.0246 | 0.0362 | 0.0527 | 1.0000 | 1.7122 | 1.7385 |

## 4. 판단

- test 범위 포함률 변화: 0.0362
- row bootstrap 양수 개선 비율: 1.0000
- artist bootstrap 양수 개선 비율: 1.0000
- 판단: 범위/신뢰도 보정 후보 유지

## 5. 해석

- `fixed_125`는 점가격을 바꾸지 않고 표시 범위만 25% 넓히는 정책이다.
- row bootstrap과 artist bootstrap 모두에서 포함률 개선이 반복되면, 특정 샘플에만 맞춘 결과일 가능성이 낮다.
- 이 검증은 모델 재학습 검증이 아니라 범위 표시 정책 검증이다.
- 이 결과는 운영 반영 승인이 아니라 범위/신뢰도 보정 후보 유지 판단이다.
- 운영 반영 전에는 별도 후보 출력 필드로 API/프론트 테스트를 진행해야 한다.

## 6. 산출물

- `outputs/overall_metrics.csv`
- `outputs/bootstrap_metrics.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/test_predictions_with_ranges.csv`
- `reports/result_report.md`
- `reports/result_report.html`
