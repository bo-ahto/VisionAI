# H18 가격 범위 calibration 보완 실험 기록

- 실험 ID: `H18_interval_calibration_grid`
- 날짜: 2026-05-13
- 단계: 후속 신뢰도 출력 보완 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 실행 스크립트:
- `scripts/track3/h18_interval_calibration_grid.py`
- 결과 파일:
- `data/track3_h18_interval_calibration_grid.json`

## 1. 목적

- H11에서 Warm coverage가 부족했던 문제를 calibration quantile 조정으로 보완할 수 있는지 확인
- Cold 예측 구간은 coverage가 충분하지만 폭이 너무 넓은 문제를 다시 확인

## 2. 가설

- H18
- 예측 구간 calibration quantile을 조정하면 Warm coverage 부족을 줄일 수 있다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`

## 4. 연구 방법

- train 내부를 fit / calibration으로 나눔
- calibration residual 분위수를 여러 단계로 바꿔 release split에서 coverage와 폭을 비교함
- 비교 quantile
- `0.80`
- `0.85`
- `0.90`
- `0.925`
- `0.95`
- `0.975`

## 5. 결과

- Warm
- q 0.800: coverage `0.701`, width `0.554`
- q 0.850: coverage `0.753`, width `0.700`
- q 0.900: coverage `0.810`, width `0.928`
- q 0.925: coverage `0.838`, width `1.106`
- q 0.950: coverage `0.880`, width `1.456`
- q 0.975: coverage `0.926`, width `2.117`
- Cold
- q 0.800: coverage `0.855`, width `2.179`
- q 0.850: coverage `0.888`, width `2.657`
- q 0.900: coverage `0.922`, width `3.486`
- q 0.925: coverage `0.935`, width `4.220`
- q 0.950: coverage `0.959`, width `5.511`
- q 0.975: coverage `0.997`, width `20.269`

## 6. 해석

- Warm 80% 구간은 q 0.90을 쓰면 실제 coverage `0.810`으로 목표를 넘김
- Warm 90% 구간은 q 0.975를 써야 coverage `0.926`으로 목표를 넘기지만 폭이 `2.117`로 커짐
- Cold는 q 0.80에서도 coverage `0.855`로 목표를 넘김
- 하지만 Cold 구간 폭은 q 0.80에서도 `2.179`로 큼
- 따라서 Cold 신뢰구간은 “정확한 범위”보다 “불확실성이 높다”는 경고성 출력에 가깝게 봐야 함

## 7. 결론

- 채택 / 보류 / 중단:
- 부분 채택
- 이유:
- Warm 80% 보조 구간은 q 0.90 기준으로 사용 가능성이 있음
- Warm 90%와 Cold 구간은 폭이 커서 바로 운영 채택하기 어려움
- 참고 상태:
- H18 검증 완료

## 8. 다음 액션

- Warm 보조 출력은 `80% 구간 중심`으로 검토
- Cold는 넓은 범위 대신 신뢰도 등급 또는 경고 문구로 표현하는 방안 검토
- 최종 모델이 확정되면 H18 calibration을 다시 수행함
