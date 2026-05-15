# H8 Cold 2D 한정 fallback 확인 기록

- 실험 ID: `H8_cold_2d_fallback_confirm`
- 날짜: 2026-05-13
- 단계: 후속 약점 보완 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 이전 실험:
- [`2026-05-13_pr17_pr18_pr19_depth_branch.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_pr17_pr18_pr19_depth_branch.md:1)
- 관련 결과 파일:
- `data/track3_h8_cold_2d_fallback_results.json`
- 기록 유형:
- 단일 실험

## 1. 목적

- H7에서 확인된 `Cold 2D` 개선 신호가 실제 release split에서도 쓸 수 있는지 확인
- 전체 Cold 모델을 바꾸지 않고 `Cold 2D`에만 별도 fallback을 적용하는 방식이 효율적인지 검증

## 2. 가설

- H8
- Cold 2D 한정 fallback이 전체 Cold 모델 교체보다 효율적일 것이다

## 3. 사용 데이터

- 학습 데이터:
- `data/release_split/track3_train.csv`
- 평가 데이터:
- `data/release_split/track3_test_cold.csv`
- split 기준:
- train과 test_cold 작가 겹침 없음
- Warm 평가:
- 해당 없음
- 이유:
- 이번 실험은 신규 피처 추가가 아니라 Cold 전용 라우팅 구조 확인임

## 4. 사용 변수

- baseline Cold 변수:
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `artist_works_log`
- `aspect_ratio`
- 2D fallback 변수:
- `medium_category`
- `support_category`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `artist_works_log`
- `aspect_ratio`
- 제외:
- `source_platform`
- `artist_name_ko` 직접 피처

## 5. 사용 모델

- baseline:
- 전체 train으로 학습한 Cold LAD
- variant:
- Cold 2D 작품만 train 2D로 학습한 별도 LAD 사용
- Cold 3D 작품은 기존 baseline 예측 유지

## 6. 성공 기준

- 전체 Cold median APE가 나빠지지 않아야 함
- Cold 2D median APE 또는 Within-30%가 개선되어야 함
- Cold 3D는 기존 baseline과 같아야 함
- p95 / p99 같은 큰 오차 지표가 악화되지 않아야 함

## 7. 실행 내용

- 실행 스크립트:
- `scripts/track3/h8_cold_2d_fallback_confirm.py`
- 실행 일시:
- 2026-05-13
- 산출물:
- `data/track3_h8_cold_2d_fallback_results.json`

## 8. 결과

### Warm

- 해당 없음
- 이번 실험은 Cold 전용 라우팅 구조 실험임

### Cold

- 전체 Cold
- baseline: `median APE 0.3207`
- fallback: `median APE 0.3267`
- 변화: `+0.0060` 악화
- `Within-30%`: `0.4640 -> 0.4557`
- paired win-rate: `0.0693`
- Cold 2D
- baseline: `median APE 0.3871`
- fallback: `median APE 0.4735`
- 변화: `+0.0863` 악화
- `Within-30%`: `0.3033 -> 0.2478`
- paired win-rate: `0.4593`
- Cold 3D
- baseline: `median APE 0.3103`
- fallback: `median APE 0.3103`
- 변화 없음
- tail
- 전체 p95: `2.3712 -> 2.3451`
- 전체 p99: `4.4446 -> 4.4028`
- 2D p95 / p99는 줄었지만, 대표 오차와 Within-30%가 크게 악화됨

## 9. 해석

- H7에서 보였던 `Cold 2D` 개선 신호는 release split의 2D fallback 구조에서는 재현되지 않음
- 2D 전용 모델은 극단 오차 일부를 줄였지만, 일반적인 예측 정확도는 나빠짐
- 전체 Cold도 baseline보다 악화됨
- 3D는 baseline을 그대로 쓰므로 변하지 않았음
- 따라서 `Cold 2D만 별도 expert로 교체`하는 방식은 현재 기준에서 채택할 수 없음

## 10. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- 전체 Cold와 Cold 2D median APE가 모두 악화됨
- Cold 2D `Within-30%`도 크게 낮아짐
- 운영 복잡도를 늘릴 만큼의 개선 근거가 없음
- 참고 상태:
- H8 검증 완료

## 11. 다음 액션

- H8은 추가 실험 없이 중단
- H7의 2D / 3D 분기 실험선도 현재 기준 운영 채택하지 않음
- 다음 후속 실험은 H13~H15처럼 공통 피처 기반 약점 보완으로 이동
