# H11 가격 범위 / 신뢰도 출력 실험 기록

- 실험 ID: `H11_prediction_interval_confirm`
- 날짜: 2026-05-13
- 단계: 후속 신뢰도 출력 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h11_prediction_interval_results.json`
- 실행 스크립트:
- `scripts/track3/h11_prediction_interval_confirm.py`

## 1. 목적

- 가격 하나만 예측하는 방식보다 가격 범위와 신뢰도를 같이 주는 방식이 실용적인지 확인
- Warm / Cold 각각에서 예측 구간이 실제 가격을 충분히 포함하는지 확인
- 예측 구간 폭이 실무적으로 받아들일 수 있는 수준인지 확인

## 2. 가설

- H11
- 정보량에 따라 가격 범위와 신뢰도를 함께 주는 방식이 더 실용적일 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`
- fit rows: `29,435`
- calibration rows: `5,194`
- test warm: `1,685`
- test cold: `3,823`

## 4. 사용 모델

- Warm
- H10의 작가 이력 기반 LightGBM 구조
- Cold
- LAD 계열 구조 모델

## 5. 연구 방법

- train 내부를 fit / calibration으로 나눔
- fit 데이터로 모델을 학습함
- calibration 데이터에서 `실제 로그가격 - 예측 로그가격`의 절대값을 계산함
- calibration residual의 분위수를 사용해 80% / 90% 예측 구간을 만듦
- release warm / cold에서 실제 coverage와 구간 폭을 확인함

## 6. 결과

- Warm 80% 구간
- 실제 coverage: `0.701`
- 구간 폭 중앙값: `0.554`
- median APE: `0.1235`
- Warm 90% 구간
- 실제 coverage: `0.810`
- 구간 폭 중앙값: `0.928`
- median APE: `0.1235`
- Cold 80% 구간
- 실제 coverage: `0.855`
- 구간 폭 중앙값: `2.179`
- median APE: `0.3257`
- Cold 90% 구간
- 실제 coverage: `0.922`
- 구간 폭 중앙값: `3.486`
- median APE: `0.3257`

## 7. 해석

- Warm은 목표 coverage보다 실제 coverage가 낮음
- 80% 목표인데 실제는 `70.1%`
- 90% 목표인데 실제는 `81.0%`
- 따라서 Warm 예측 구간은 현재 방식 그대로는 과신 위험이 있음
- Cold는 coverage는 목표를 넘지만 구간 폭이 큼
- Cold 80% 구간 폭 중앙값 `2.179`는 예측 가격 대비 범위가 매우 넓다는 뜻임
- 가격 범위 출력은 서비스적으로 의미가 있지만, 현재 방식은 calibration 보완 없이는 바로 채택하기 어려움

## 8. 결론

- 채택 / 보류 / 중단:
- 보류
- 이유:
- Warm은 coverage 부족
- Cold는 구간 폭이 커서 실무 해석성이 떨어짐
- 참고 상태:
- H11 검증 완료
- point prediction 대체가 아니라 보조 출력 후보로 유지

## 9. 다음 액션

- H18에서 calibration quantile grid를 추가 확인함
- Warm 80% 구간은 q 0.90 기준으로 coverage `0.810`까지 보완 가능함
- Cold는 q 0.80에서도 coverage는 `0.855`로 충분하지만 구간 폭이 `2.179`로 커서 가격 범위보다 신뢰도 경고 중심으로 검토함
- 최종 모델 선택 이후 예측 구간을 다시 보정함
