# H17 작가 이력 피처 안정성 재검증 기록

- 실험 ID: `H17_artist_history_stability_confirm`
- 날짜: 2026-05-13
- 단계: 후속 재검증 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 실행 스크립트:
- `scripts/track3/h17_artist_history_stability_confirm.py`
- 결과 파일:
- `data/track3_h17_artist_history_stability_results.json`

## 1. 목적

- H10에서 확인된 작가 이력 피처 개선이 seed 변화에도 유지되는지 확인
- 단일 실행 결과가 우연인지 확인

## 2. 가설

- H17
- 작가 이력 피처의 Warm 개선 효과는 반복 학습에서도 안정적으로 유지될 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- seed: `11`, `22`, `33`

## 4. 비교 모델

- V0
- 작품 피처 + `artist_name_ko`
- V1
- 작품 피처 + 작가 이력 피처
- V2
- 작품 피처 + `artist_name_ko` + 작가 이력 피처

## 5. 사용 피처

- 작품 피처
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `aspect_ratio`
- 작가 이력 피처
- `artist_works_log`
- `artist_ln_price_median`
- `artist_ln_price_mean`
- `artist_ln_price_iqr`

## 6. 결과

- V0 artist name
- 평균 Warm median APE: `0.2363`
- 표준편차: `0.0027`
- V1 history only
- 평균 Warm median APE: `0.1192`
- 표준편차: `0.0049`
- V2 artist name + history
- 평균 Warm median APE: `0.1147`
- 표준편차: `0.0051`

## 7. 해석

- 작가 이력 피처는 3개 seed 모두에서 작가명 단독보다 크게 우세함
- `artist_name_ko + 작가 이력 피처` 조합이 가장 좋음
- 표준편차가 작아 반복 학습 안정성도 충분함
- 다만 H16 결과상 temporal-safe 검증은 날짜 컬럼 확보 전까지 불가능함

## 8. 결론

- 채택 / 보류 / 중단:
- 채택
- 이유:
- Warm median APE 평균이 `0.2363 -> 0.1147`로 안정적으로 개선됨
- 참고 상태:
- H17 검증 완료
- 운영 확정 전 H16 조건 해결 필요

## 9. 다음 액션

- Warm 최종 후보 모델은 H17의 V2를 기준 후보로 둠
- 날짜 컬럼 확보 후 temporal-safe 방식으로 재검증함
