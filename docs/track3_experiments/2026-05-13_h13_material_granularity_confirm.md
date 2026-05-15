# H13 재료 세분화 피처 확인 기록

- 실험 ID: `H13_material_granularity_confirm`
- 날짜: 2026-05-13
- 단계: 후속 약점 보완 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h13_material_granularity_results.json`
- 기록 유형:
- 단일 실험

## 1. 목적

- H13을 검증함
- 재료를 더 세분화한 flag와 희소도 피처가 Cold 정확도를 개선하는지 확인함
- 재료 피처는 Warm / Cold 공통으로 만들 수 있으므로 Warm도 함께 확인함

## 2. 가설

- H13
- 재료를 더 세분화한 피처가 Cold 정확도를 개선할 것이다

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
- `is_oil`
- `is_acrylic`
- `is_mixed_media`
- `is_print_like`
- `is_water_based`
- `is_drawing`
- `is_pigment`
- `is_other_medium`
- `medium_rarity_bucket`

## 5. 사용 모델

- Cold:
- LAD
- Warm:
- tuned LightGBM

## 6. 비교군

- `V0_base`
- 기존 baseline
- `V1_flags`
- 재료 flag 추가
- `V2_rarity`
- 재료 희소도 bucket 추가
- `V3_flags_rarity`
- 재료 flag와 희소도 bucket 모두 추가

## 7. 성공 기준

- Cold median APE가 baseline보다 의미 있게 낮아져야 함
- Warm median APE가 크게 악화되지 않아야 함
- paired win-rate와 큰 오차 지표가 악화되지 않아야 함
- 개선 폭이 작고 설명력이 낮으면 채택하지 않음

## 8. 실행 내용

- 실행 스크립트:
- `scripts/track3/h13_material_granularity_confirm.py`
- 실행 일시:
- 2026-05-13
- 산출물:
- `data/track3_h13_material_granularity_results.json`

## 9. 결과

### Warm

- `V0_base`
- `median APE 0.2056`
- `V1_flags`
- `median APE 0.2286`
- 변화: `+0.0230` 악화
- `V2_rarity`
- `median APE 0.2170`
- 변화: `+0.0114` 악화
- `V3_flags_rarity`
- `median APE 0.2128`
- 변화: `+0.0072` 악화

### Cold

- `V0_base`
- `median APE 0.3207`
- `V1_flags`
- `median APE 0.3207`
- 변화: `+0.0000`
- `V2_rarity`
- `median APE 0.3207`
- 변화: `+0.0000`
- `V3_flags_rarity`
- `median APE 0.3207`
- 변화: `+0.0000`
- 판단:
- Cold는 어떤 재료 세분화 피처도 baseline 대비 개선하지 못함

## 10. 해석

- `medium_category`가 이미 범주형 변수로 들어가 있어, 단순 재료 flag는 새로운 정보를 거의 추가하지 못함
- Cold에서는 재료 flag와 희소도 bucket 모두 대표 오차를 낮추지 못함
- Warm에서는 모든 variant가 baseline보다 악화됨
- 따라서 현재 방식의 재료 세분화 피처는 공통 운영 피처로 채택하기 어렵음

## 11. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- Cold 개선이 없고 Warm이 악화됨
- 이미 `medium_category`와 `medium_ho_bucket`이 재료 정보를 충분히 담고 있는 것으로 보임
- 참고 상태:
- H13 검증 완료

## 12. 다음 액션

- H13은 추가 실험 없이 중단
- 재료 정보는 기존 `medium_category`, `medium_ho_bucket` 유지
- 다음 검증은 H14 크기-재료 조합 피처 또는 H15 결측 패턴으로 이동
