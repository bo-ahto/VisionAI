# H15 결측 패턴 피처 감사 기록

- 실험 ID: `H15_missing_pattern_audit`
- 날짜: 2026-05-13
- 단계: 후속 신뢰도 실험 사전 점검
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h15_missing_pattern_audit.json`
- 기록 유형:
- 데이터 감사

## 1. 목적

- H15를 현재 release split에서 바로 실험할 수 있는지 확인
- 결측 패턴 자체가 피처로 의미 있으려면 결측 여부에 분산이 있어야 함

## 2. 가설

- H15
- 결측 패턴 자체가 신뢰도와 가격 오차를 설명할 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`

## 4. 점검 변수

- `artist_name_ko`
- `medium_category`
- `support_category`
- `depth_cm`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `orientation`

## 5. 실행 내용

- 실행 스크립트:
- `scripts/track3/h15_missing_pattern_audit.py`
- 산출물:
- `data/track3_h15_missing_pattern_audit.json`

## 6. 결과

- `track3_train.csv`
- 전체 작품 수: `34,629`
- 결측이 하나라도 있는 작품 수: `0`
- 결측 신호 존재 여부: `False`
- `track3_test_warm.csv`
- 전체 작품 수: `1,685`
- 결측이 하나라도 있는 작품 수: `0`
- 결측 신호 존재 여부: `False`
- `track3_test_cold.csv`
- 전체 작품 수: `3,823`
- 결측이 하나라도 있는 작품 수: `0`
- 결측 신호 존재 여부: `False`
- 최종 판단:
- `can_run=False`

## 7. 해석

- 현재 release split에서는 핵심 입력 변수의 결측이 없음
- `missing_count`, `info_completeness_score` 같은 피처를 만들어도 모든 값이 같아짐
- 값이 모두 같으면 모델이 결측 패턴과 가격 오차의 관계를 학습할 수 없음
- 따라서 H15는 현재 데이터로 모델 실험을 진행하면 의미 없는 실험이 됨
- H15 자체가 불필요하다는 뜻은 아님
- 실제 운영 입력에서 결측이 생기면 다시 검증할 수 있음
- H9 masking 실험은 별도로 실행했고, 전체 마스킹 학습 방식은 채택하지 않음

## 8. 결론

- 채택 / 보류 / 중단:
- 보류
- 이유:
- 현재 고정 데이터에는 결측 신호가 없어 결측 패턴 피처의 효과를 검증할 수 없음
- 참고 상태:
- H15 데이터 감사 완료

## 9. 다음 액션

- 운영 입력 데이터에서 실제 결측 사례가 쌓이면 H15를 재검증함
- H9 masking 결과는 별도 문서에서 관리함
- [`2026-05-13_h9_masking_robustness_confirm.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h9_masking_robustness_confirm.md:1)
