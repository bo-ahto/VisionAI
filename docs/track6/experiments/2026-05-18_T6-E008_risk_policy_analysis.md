# T6-E008 신뢰도/위험 구간 분석

- 날짜: `2026-05-29`
- 관련 가설: `T6-H7`
- 상태: 검증 완료
- 목적: test 예측 결과에서 단일 가격만 보여주기 위험한 구간을 식별
- 사용 스크립트: `scripts/track6/run_t6_e008_risk_policy_analysis.py`
- 결과 JSON: `data/track6/results/t6_e008_risk_policy_analysis.json`
- slice CSV: `data/track6/results/t6_e008_risk_policy_analysis_slices.csv`

## 1. 분석 원칙

- 새 모델을 고르거나 test 결과에 맞춰 모델을 튜닝하지 않음
- T6-E007 예측 결과를 사용해 위험 조건을 관찰
- 위험 구간은 전체 대비 median APE 또는 p95 APE가 15% 이상 나쁜 구간으로 표시
- 표본 수가 30건 미만이면 위험 후보로 확정하지 않음

## 2. 위험 후보 요약

| model | split | slice | n | median APE | p95 APE | q80 range multiplier |
|---|---|---|---:|---:|---:|---:|
| `lightgbm_cold__base_large_flags` | `test_cold` | `3d` | `42` | `0.7074` | `2.2786` | `4.07x` |
| `catboost_cold__base_medium_shape` | `test_cold` | `extreme_shape` | `50` | `0.7044` | `3.2608` | `3.45x` |
| `catboost_cold__base_medium_shape` | `test_cold` | `3d` | `42` | `0.7009` | `3.0203` | `3.84x` |
| `lightgbm_cold__base_support_size` | `test_cold` | `3d` | `42` | `0.6865` | `2.8995` | `3.95x` |
| `lightgbm_cold__base_large_flags` | `test_cold` | `extreme_shape` | `50` | `0.6593` | `3.9293` | `4.80x` |
| `lightgbm_cold__base_support_size` | `test_cold` | `extreme_shape` | `50` | `0.6220` | `3.8530` | `4.68x` |
| `catboost_cold__base_medium_shape` | `test_cold` | `unbalanced_shape` | `350` | `0.5710` | `2.4540` | `2.69x` |
| `lightgbm_cold__base_large_flags` | `test_cold` | `unbalanced_shape` | `350` | `0.5686` | `3.0612` | `2.63x` |
| `lightgbm_cold__base_large_flags` | `test_cold` | `large_q5` | `834` | `0.4915` | `7.0085` | `3.19x` |
| `huber_warm_artist__base_existing_combo` | `test_warm` | `low_artist_history` | `88` | `0.4886` | `2.0306` | `2.55x` |
| `lightgbm_cold__base_support_size` | `test_cold` | `large_q5` | `834` | `0.4746` | `7.1355` | `3.11x` |
| `catboost_cold__base_medium_shape` | `test_cold` | `large_q5` | `834` | `0.4560` | `7.6190` | `3.19x` |
| `huber_warm_artist__base_existing_combo` | `test_warm` | `small_q1` | `133` | `0.3239` | `1.7441` | `2.47x` |
| `huber_warm_artist__base_existing_combo` | `test_warm` | `unbalanced_shape` | `65` | `0.2751` | `3.5301` | `2.77x` |

## 3. 가격 범위 해석

- `q80 range multiplier`는 예측 가격 주변에 80% 수준의 관찰 오차를 포함하려면 필요한 배율
- 예: multiplier가 `2.0x`이면 예측가 100만원 기준 대략 50만~200만원 범위를 의미
- 이 값은 서비스 최종 범위가 아니라, 현재 모델의 불확실성 크기를 보는 참고값

## 4. 결론

- T6-H7은 test 기준 검증 완료
- 단일 가격만 제공하기보다 Warm/Cold 및 위험 구간별 신뢰도 문구가 필요
- Cold는 median은 유지되지만 p95가 크므로 가격 범위 또는 경고 정책을 함께 두는 것이 안전
- 다음 단계는 최종 운영 후보와 artifact manifest 정리(T6-E009)
