# H9 결측 상황 대응 마스킹 학습 실험 기록

- 실험 ID: `H9_masking_robustness_confirm`
- 날짜: 2026-05-13
- 단계: 후속 신뢰도 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h9_masking_robustness_results.json`
- 실행 스크립트:
- `scripts/track3/h9_masking_robustness_confirm.py`

## 1. 목적

- 실제 운영 입력에서 일부 정보가 빠졌을 때 모델이 얼마나 버티는지 확인
- 학습 중 일부 정보를 의도적으로 가린 모델이 결측 상황에서 더 안정적인지 확인
- H15에서 현재 release split 결측이 0건으로 확인됐기 때문에, H9에서는 결측 상황을 인위적으로 만들어 검증함

## 2. 가설

- H9
- 일부 정보를 의도적으로 가리고 학습한 모델이 결측 상황에서 더 잘 버틸 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`
- train: `34,629`
- test warm: `1,685`
- test cold: `3,823`

## 4. 사용 피처

- 공통 피처
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `artist_works_log`
- `aspect_ratio`
- `missing_medium`
- `missing_support`
- `missing_size`
- `missing_count`
- `info_completeness_score`
- Warm 추가 피처
- `artist_name_ko`

## 5. 연구 방법

- 비교군 1: 일반 학습 모델
- train 데이터를 그대로 사용
- 비교군 2: 마스킹 학습 모델
- train 데이터 일부에서 재료 정보와 크기 정보를 의도적으로 가림
- 재료 마스킹 비율: 약 `25.2%`
- 크기 마스킹 비율: 약 `24.8%`
- 평가 시나리오
- clean: 평가 데이터를 그대로 사용
- material_missing: 재료와 지지체 정보를 가림
- size_missing: 크기 관련 정보를 가림
- material_size_missing: 재료와 크기 정보를 함께 가림

## 6. 결과

- clean
- Cold: `0.3207 -> 0.3352`
- Warm: `0.2056 -> 0.2837`
- material_missing
- Cold: `0.3794 -> 0.4014`
- Warm: `0.3230 -> 0.3386`
- size_missing
- Cold: `0.7476 -> 0.7396`
- Warm: `0.6887 -> 0.6332`
- material_size_missing
- Cold: `0.7543 -> 0.7493`
- Warm: `0.6773 -> 0.6609`

## 7. 해석

- 마스킹 학습은 크기 결측 상황에서는 일부 완화 효과가 있음
- 특히 Warm size_missing에서는 `median APE 0.6887 -> 0.6332`로 개선됨
- 하지만 clean 성능이 크게 악화됨
- Warm clean은 `0.2056 -> 0.2837`로 악화 폭이 큼
- Cold clean도 `0.3207 -> 0.3352`로 악화됨
- 재료 결측 상황에서도 개선되지 않고 오히려 악화됨
- 운영 기본 모델은 대부분 정상 입력을 받을 가능성이 높으므로 clean 성능 손실이 큰 방식은 채택하기 어려움

## 8. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- 결측 상황 일부에서는 도움이 되지만, 정상 입력과 재료 결측에서 성능 손실이 커서 기본 모델 학습 방식으로 채택하지 않음
- 참고 상태:
- H9 검증 완료

## 9. 다음 액션

- 전체 학습 방식으로 마스킹을 섞는 방식은 중단함
- 결측 대응은 별도 fallback 또는 입력 품질 경고 방식으로 검토함
- H15는 실제 운영 결측 데이터가 확보되면 다시 검증함
