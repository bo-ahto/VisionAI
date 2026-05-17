# T4-E051 최종 모델 기준 생성 피처 조합 감사

- 날짜: 2026-05-17
- 관련 가설: T4-H39
- 상태: 완료
- 목적: 생성 피처 조합 실험이 최종 모델 기준으로 누락되지 않았는지 확인

## 1. 실험 배경

- T4-E035에서 재료-크기 조합 피처 실험은 진행했었다.
- 하지만 당시 모델은 Warm `Ridge`, Cold `Huber`였다.
- 이후 최종 후보가 Warm `RandomForest`, Cold `Quantile`로 정리되었기 때문에 같은 생성 피처를 최종 모델 기준으로 다시 확인할 필요가 있었다.

## 2. 확인하려는 것

- 생성 조합 피처가 최종 Warm 모델에서도 성능을 개선하는가
- 생성 조합 피처가 최종 Cold 모델에서도 성능을 개선하는가
- validation에서 좋아 보이는 피처가 test에서도 유지되는가
- 최종 피처셋에 추가할 만한 생성 피처가 남아 있는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 검증 데이터: `data/track4_split/track4_val_warm.csv`
- Warm 테스트 데이터: `data/track4_split/track4_test_warm.csv`
- Cold 검증 데이터: `data/track4_split/track4_val_cold.csv`
- Cold 테스트 데이터: `data/track4_split/track4_test_cold.csv`

## 4. 비교 기준

- Warm 모델: `RandomForest`
- Cold 모델: `Quantile`
- Warm baseline:
  - 최종 Warm 조건부 작가 통계 피처셋
- Cold baseline:
  - 최종 Cold full-size 피처셋

## 5. 비교한 생성 피처

- `medium_size_bucket`
  - 재료와 크기 구간을 묶은 피처
- `support_size_bucket`
  - 지지체와 크기 구간을 묶은 피처
- `combo_flags`
  - `is_large_oil`
  - `is_large_acrylic`
  - `is_large_mixed_media`
  - `is_small_print`
  - `is_large_unknown_support`

## 6. 결과

| 피처셋 | Warm val median APE | Warm test median APE | Cold val median APE | Cold test median APE |
|---|---:|---:|---:|---:|
| baseline_final | 0.1902 | 0.1927 | 0.3347 | 0.4195 |
| medium_size_bucket | 0.1905 | 0.1978 | 0.3366 | 0.4263 |
| support_size_bucket | 0.1692 | 0.2042 | 0.3561 | 0.4271 |
| combo_flags | 0.1859 | 0.1959 | 0.3470 | 0.4306 |

| 피처셋 | Warm test p95 APE | Cold test p95 APE | 해석 |
|---|---:|---:|---|
| baseline_final | 0.9221 | 2.7604 | 최종 기준 |
| medium_size_bucket | 0.9384 | 2.7444 | Cold p95는 소폭 개선이나 median 악화 |
| support_size_bucket | 0.8993 | 2.7918 | Warm p95는 개선이나 median 악화 |
| combo_flags | 0.9284 | 2.7350 | Cold p95는 소폭 개선이나 median 악화 |

## 7. 해석

- Warm:
  - `support_size_bucket`은 validation median APE를 개선했지만 test median APE는 악화되었다.
  - `combo_flags`는 Warm test median APE가 baseline보다 약간 나쁘다.
  - 따라서 Warm 최종 피처셋에는 생성 조합 피처를 추가하지 않는다.
- Cold:
  - 모든 생성 조합 피처가 Cold test median APE를 baseline보다 악화시켰다.
  - 일부 p95 APE는 소폭 개선되지만 대표 오차가 나빠진다.
  - 따라서 Cold 최종 피처셋에도 생성 조합 피처를 추가하지 않는다.

## 8. 결론

- 생성 피처 조합 실험 누락은 보완되었다.
- 최종 모델 기준으로는 생성 조합 피처를 채택하지 않는다.
- 현재 최종 피처셋을 유지한다.
- 생성 조합 피처는 모델 입력보다 위험 구간 분석용 보조 피처로만 남긴다.

## 9. 산출물

- 실행 스크립트: `scripts/track4/run_t4_e051_final_model_feature_combo_audit.py`
- 결과 JSON: `data/track4/results/t4_e051_final_model_feature_combo_audit_metrics.json`
