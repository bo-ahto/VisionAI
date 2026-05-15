# H26-H28 크기 피처 축소 실험 기록

- 실험 ID: `H26_H28_size_feature_reduction`
- 날짜: 2026-05-13
- 단계: H4 후속 피처 축소 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 실행 스크립트:
- `scripts/track3/h26_h28_size_feature_reduction.py`
- 결과 파일:
- `data/track3_h26_h28_size_feature_reduction_results.json`

## 1. 목적

- 크기 관련 피처가 중복되어 있는지 확인
- 가로/세로 원값을 줄여도 성능이 유지되는지 확인
- `estimated_ho`와 `log_area` 중 하나만 남겨도 되는지 확인
- 운영 입력을 단순화할 수 있는지 확인

## 2. 가설

- H26
- 크기 관련 피처가 중복되어 있어 일부를 제거하면 성능이 유지되거나 안정성이 좋아질 것이다
- H27
- `estimated_ho`와 `log_area` 중 하나만 남겨도 성능 차이가 크지 않을 것이다
- H28
- `width_cm`, `height_cm`는 `log_area`, `aspect_ratio`로 대체 가능할 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`
- train: `34,629`
- test warm: `1,685`
- test cold: `3,823`

## 4. 사용 모델

- Warm
- LightGBM
- Cold
- LAD / QuantileRegressor 계열

## 5. 비교 피처 구성

- V0 all size
- `depth_cm`, `width_cm`, `height_cm`, `log_area`, `estimated_ho`, `aspect_ratio`
- V1 no width height
- `depth_cm`, `log_area`, `estimated_ho`, `aspect_ratio`
- V2 log area only
- `depth_cm`, `log_area`, `aspect_ratio`
- V3 ho only
- `depth_cm`, `estimated_ho`
- V4 log area no aspect
- `depth_cm`, `log_area`
- V5 log ho bucket
- `depth_cm`, `log_ho`

## 6. 결과

- V0 all size
- Cold median APE: `0.3237`
- Warm median APE: `0.2045`
- V1 no width height
- Cold median APE: `0.3207`
- Warm median APE: `0.2056`
- V2 log area only
- Cold median APE: `0.3231`
- Warm median APE: `0.2087`
- V3 ho only
- Cold median APE: `0.4071`
- Warm median APE: `0.2086`
- V4 log area no aspect
- Cold median APE: `0.3260`
- Warm median APE: `0.2223`
- V5 log ho bucket
- Cold median APE: `0.3237`
- Warm median APE: `0.2086`

## 7. 해석

- `width_cm`, `height_cm`를 제거하고 `log_area`, `estimated_ho`, `aspect_ratio`를 유지한 V1이 가장 균형적임
- V1은 Cold가 `0.3237 -> 0.3207`로 개선되고 Warm은 `0.2045 -> 0.2056`으로 거의 유지됨
- `log_area + aspect_ratio`만 쓰는 V2도 성능 악화가 작아 운영 단순화 후보가 될 수 있음
- `estimated_ho`만 남기는 V3는 Cold가 `0.4071`로 크게 악화되어 기각
- `aspect_ratio`를 제거한 V4는 Warm이 크게 악화되어 기각
- 호수를 로그값으로만 쓰는 V5는 큰 개선이 없어 우선순위가 낮음

## 8. 결론

- 채택 / 보류 / 중단:
- 부분 채택
- 이유:
- `width_cm`, `height_cm`는 제거 가능성이 있음
- `log_area`, `estimated_ho`, `aspect_ratio`, `depth_cm`는 유지 가치가 있음
- `estimated_ho`만 남기는 축소안은 Cold 악화가 커서 중단
- 참고 상태:
- H26 검증 완료
- H27 검증 완료
- H28 검증 완료

## 9. 다음 액션

- 후속 피처 실험의 기본 크기 구성은 V1을 기준 후보로 둠
- `depth_cm`, `log_area`, `estimated_ho`, `aspect_ratio` 유지
- `width_cm`, `height_cm`는 운영 단순화 후보로 제외 가능
- H19~H22 호수 표현 실험은 V1 기준 위에서 진행함
