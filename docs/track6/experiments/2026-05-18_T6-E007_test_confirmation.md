# T6-E007 test 최종 확인

- 날짜: `2026-05-29`
- 관련 가설: `T6-H6`
- 상태: 검증 완료
- 목적: validation에서 고정한 후보가 test에서도 같은 방향으로 유지되는지 확인
- 사용 스크립트: `scripts/track6/run_t6_e007_test_confirmation.py`
- 결과 JSON: `data/track6/results/t6_e007_test_confirmation.json`
- 예측 CSV: `data/track6/predictions/t6_e007_test_confirmation_predictions.csv`

## 1. test 적용 원칙

- validation 결과를 보고 후보를 바꾸지 않음
- T6-E006에서 고정한 후보만 test에 적용
- 학습은 `track6_train_*_features.csv`와 `track6_train_labels.csv` 기준으로만 진행
- test 정답 가격은 예측 후 평가 단계에서만 결합

## 2. test 결과

| 구분 | 모델 | 피처셋 | val median | test median | val p95 | test p95 | 판단 |
|---|---|---|---:|---:|---:|---:|---|
| `test_warm` | `huber_warm_artist` | `base_existing_combo` | `0.2126` | `0.2274` | `1.3194` | `2.0130` | 주의 유지 |
| `test_cold` | `catboost_cold` | `base_medium_shape` | `0.4251` | `0.4839` | `2.4420` | `4.7974` | 주의 유지 |
| `test_cold` | `lightgbm_cold` | `base_support_size` | `0.3848` | `0.4859` | `2.0207` | `4.7612` | 보류 |
| `test_cold` | `lightgbm_cold` | `base_large_flags` | `0.3938` | `0.4921` | `1.9783` | `4.7924` | 주의 유지 |

## 3. 해석

- Warm 후보는 test에서 validation 대비 성능 변화를 확인해 최종 Warm 후보 유지 여부를 판단
- Cold 대표 오차 후보와 큰 오차 후보는 목적이 다르므로 둘 중 하나만 절대 우위로 보지 않음
- test에서 median은 좋지만 p95가 나쁘면 단일 가격 예측은 가능하더라도 신뢰도/가격 범위 정책이 필요

## 4. 결론

- `test_warm` / `huber_warm_artist` / `base_existing_combo`: 주의 유지
- `test_cold` / `catboost_cold` / `base_medium_shape`: 주의 유지
- `test_cold` / `lightgbm_cold` / `base_support_size`: 보류
- `test_cold` / `lightgbm_cold` / `base_large_flags`: 주의 유지
- 다음 단계는 신뢰도/가격 범위 정책 검증(T6-E008)
