# T5-E005 기준 모델 선정 및 고정

- 날짜: 2026-05-18
- 관련 가설: T5-H8
- 상태: 완료
- 목적: 이후 피처 실험의 비교 기준이 되는 Warm / Cold 기준 모델과 기준 피처셋 고정

## 1. 확인하려는 것

- 피처 실험을 시작하기 전에 기준 모델이 명확한가
- Warm과 Cold를 같은 기준으로 비교하지 않고 상황별 기준선을 분리했는가
- 이후 피처 추가/제거 실험에서 비교할 기준값이 명확한가

## 2. 근거 실험

- T5-E002:
  - 구조-only baseline
  - Huber 기준 Warm median APE `0.4662`, Cold median APE `0.3718`
- T5-E003:
  - Warm 작가 피처 ablation
  - 작가 key + 이력 + train 가격 통계가 Warm median APE `0.2279`로 최선
- T5-E004:
  - Cold 모델군 비교
  - QuantileRegressor가 Cold median APE `0.3564`, p95 `1.8218`로 최선

## 3. Warm 기준 모델

- 기준 모델:
  - `Ridge`
- 기준 피처:
  - `artist_key`
  - `medium_category`
  - `support_category`
  - `artist_works_log`
  - `artist_works_count_train`
  - `artist_train_median_log_price`
  - `artist_train_mean_log_price`
  - `artist_train_iqr_log_price`
  - `log_area`
  - `aspect_ratio`
- 기준 성능:
  - validation median APE: `0.2279`
  - validation p95 APE: `0.9083`

## 4. Cold 기준 모델

- 기준 모델:
  - `QuantileRegressor`
- 기준 피처:
  - `medium_category`
  - `support_category`
  - `log_area`
  - `aspect_ratio`
  - `has_depth`
  - `is_3d_candidate`
- 기준 성능:
  - validation median APE: `0.3564`
  - validation p95 APE: `1.8218`

## 5. 이후 실험 규칙

- Warm 피처 실험은 Warm 기준 모델 대비 비교
- Cold 피처 실험은 Cold 기준 모델 대비 비교
- validation에서 후보를 고르고 test는 최종 확인에만 사용
- Warm과 Cold에서 효과가 다른 피처는 모델별로 분리 적용
- 운영에서 만들 수 없는 피처는 성능이 좋아도 최종 후보에서 제외

## 6. 결론

- 기준 모델 선정 단계를 완료했다.
- 다음 단계는 피처 추가/제거/생성 실험이다.
- 첫 피처 실험은 크기/지지체/3D 피처 조합을 기준선 대비 비교한다.
