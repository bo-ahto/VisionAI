# H14 크기와 재료 조합 피처 확인 기록

- 실험 ID: `H14_medium_size_combo_confirm`
- 날짜: 2026-05-13
- 단계: 후속 약점 보완 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h14_medium_size_combo_results.json`
- 기록 유형:
- 단일 실험

## 1. 목적

- H14를 검증함
- 크기와 재료를 함께 묶은 조합 피처가 단독 피처보다 가격을 더 잘 설명하는지 확인함
- 조합 피처는 Warm / Cold 공통으로 만들 수 있으므로 두 평가셋을 모두 확인함

## 2. 가설

- H14
- 크기와 재료의 조합 효과가 단독 피처보다 가격을 더 잘 설명할 것이다

## 3. 사용 데이터

- 학습 데이터:
- `data/release_split/track3_train.csv`
- Warm 평가 데이터:
- `data/release_split/track3_test_warm.csv`
- Cold 평가 데이터:
- `data/release_split/track3_test_cold.csv`

## 4. 사용 변수

- baseline:
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `artist_works_log`
- `aspect_ratio`
- 추가 후보:
- `medium_size_bucket`
- `is_large_oil`
- `is_large_acrylic`
- `is_large_other`
- `is_small_drawing`
- `is_large_2d`
- `is_small_2d`

## 5. 사용 모델

- Cold:
- LAD
- Warm:
- tuned LightGBM

## 6. 비교군

- `V0_base`
- 기존 baseline
- `V1_combo_cat`
- `medium_size_bucket` 추가
- `V2_combo_flags`
- 조합 flag 추가
- `V3_combo_all`
- 조합 category와 flag 모두 추가

## 7. 성공 기준

- Cold median APE가 baseline보다 의미 있게 낮아져야 함
- Warm median APE가 크게 악화되지 않아야 함
- paired win-rate와 큰 오차 지표가 악화되지 않아야 함
- 기존 `medium_ho_bucket`보다 추가 가치가 있어야 함

## 8. 실행 내용

- 실행 스크립트:
- `scripts/track3/h14_medium_size_combo_confirm.py`
- 실행 일시:
- 2026-05-13
- 산출물:
- `data/track3_h14_medium_size_combo_results.json`

## 9. 결과

### Warm

- `V0_base`
- `median APE 0.2056`
- `V1_combo_cat`
- `median APE 0.2056`
- 변화: `+0.0000`
- `V2_combo_flags`
- `median APE 0.2021`
- 변화: `-0.0035` 개선
- `V3_combo_all`
- `median APE 0.2021`
- 변화: `-0.0035` 개선

### Cold

- `V0_base`
- `median APE 0.3207`
- `V1_combo_cat`
- `median APE 0.3207`
- 변화: `+0.0000`
- `V2_combo_flags`
- `median APE 0.3223`
- 변화: `+0.0016` 악화
- `V3_combo_all`
- `median APE 0.3223`
- 변화: `+0.0016` 악화

## 10. 해석

- `medium_size_bucket`은 기존 `medium_ho_bucket`과 거의 같은 정보를 담아 추가 개선이 없음
- 조합 flag는 Warm에서 소폭 개선됐지만 Cold에서는 악화됨
- H14의 주 목적은 H2 이후 Cold 약점 보완이므로 Cold 악화가 있으면 공통 피처로 채택하기 어려움
- 현재 기준으로는 기존 `medium_ho_bucket` 이상으로 확실한 추가 가치를 만들지 못함

## 11. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- Cold 개선이 없고 일부 variant는 Cold를 악화시킴
- Warm 개선 폭도 작아 공통 피처 복잡도를 늘릴 근거가 부족함
- 참고 상태:
- H14 검증 완료

## 12. 다음 액션

- H14는 추가 실험 없이 중단
- 기존 `medium_ho_bucket` 유지
- 다음 검증은 H15 결측 패턴 피처로 이동
