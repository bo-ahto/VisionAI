# T6-E008 신뢰도/위험 구간 분석

- 날짜: `2026-05-18`
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
| `huber_cold__base_size_shape` | `test_cold` | `3d` | `32` | `1.3504` | `4.3690` | `4.78x` |
| `hist_quantile_cold__base` | `test_cold` | `3d` | `32` | `0.9734` | `3.4201` | `4.44x` |
| `huber_cold__base_size_shape` | `test_cold` | `extreme_shape` | `64` | `0.6649` | `3.0139` | `4.01x` |
| `catboost_warm_artist__base_medium_size` | `test_warm` | `low_artist_history` | `73` | `0.5735` | `3.3905` | `2.57x` |
| `hist_quantile_cold__base` | `test_cold` | `unbalanced_shape` | `315` | `0.5407` | `2.9614` | `3.02x` |
| `huber_cold__base_size_shape` | `test_cold` | `unbalanced_shape` | `315` | `0.5076` | `2.6766` | `2.87x` |
| `hist_quantile_cold__base` | `test_cold` | `extreme_shape` | `64` | `0.5028` | `3.0052` | `3.84x` |
| `catboost_warm_artist__base_medium_size` | `test_warm` | `large_q5` | `168` | `0.4815` | `1.6876` | `2.26x` |
| `huber_cold__base_size_shape` | `test_cold` | `small_q1` | `630` | `0.4351` | `1.8294` | `2.23x` |
| `hist_quantile_cold__base` | `test_cold` | `large_q5` | `695` | `0.3625` | `2.7067` | `2.50x` |
| `catboost_warm_artist__base_medium_size` | `test_warm` | `small_q1` | `117` | `0.3513` | `2.6372` | `2.07x` |

## 3. 가격 범위 해석

- `q80 range multiplier`는 예측 가격 주변에 80% 수준의 관찰 오차를 포함하려면 필요한 배율
- 예: multiplier가 `2.0x`이면 예측가 100만원 기준 대략 50만~200만원 범위를 의미
- 이 값은 서비스 최종 범위가 아니라, 현재 모델의 불확실성 크기를 보는 참고값

## 4. 결론

- T6-H7은 test 기준 검증 완료
- 단일 가격만 제공하기보다 Warm/Cold 및 위험 구간별 신뢰도 문구가 필요
- Cold는 median은 유지되지만 p95가 크므로 가격 범위 또는 경고 정책을 함께 두는 것이 안전
- 다음 단계는 최종 운영 후보와 artifact manifest 정리(T6-E009)
