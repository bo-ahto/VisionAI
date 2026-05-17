# T5-E011 Warm Huber 수렴 재검증

- 날짜: 2026-05-18
- 관련 가설: T5-H14
- 목적: Warm 최종 후보인 HuberRegressor가 수렴 설정 때문에 성능 판단이 흔들리는지 확인

## 1. 실험 배경

- T5-E010 실행 중 HuberRegressor에서 수렴 경고가 발생함
- 수렴 경고가 있어도 예측값은 생성되지만, 최종 후보로 쓰기 전 기술적 안정성을 확인해야 함
- 동일한 Warm full_size 피처셋에서 `max_iter`만 바꿔 결과 변화를 확인함

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- validation: `data/track5_split/track5_val_warm.csv`
- test: `data/track5_split/track5_test_warm.csv`
- 결과: `data/track5/results/t5_e011_warm_huber_convergence_recheck_metrics.json`
- 예측값: `data/track5/predictions/t5_e011_warm_huber_convergence_recheck_predictions.csv`

## 3. 실험 방법

- 피처는 Warm full_size 후보로 고정함
- 모델은 HuberRegressor로 고정함
- 비교 설정
  - `max_iter=1000`
  - `max_iter=3000`
  - `max_iter=5000`
- 확인 항목
  - 실제 사용 반복 횟수
  - validation median APE / p95 APE
  - test median APE / p95 APE

## 4. 결과

| 설정 | 실제 반복 횟수 | val median APE | val p95 APE | test median APE | test p95 APE |
|---|---:|---:|---:|---:|---:|
| max_iter 1000 | 1000 | 0.1494 | 0.7032 | 0.1585 | 0.8738 |
| max_iter 3000 | 2133 | 0.1499 | 0.7037 | 0.1580 | 0.8723 |
| max_iter 5000 | 2133 | 0.1499 | 0.7037 | 0.1580 | 0.8723 |

## 5. 해석

- `max_iter=1000`은 반복 횟수 한도에 도달해 경고가 발생함
- `max_iter=3000` 이상에서는 2133회에서 멈추므로 수렴 설정은 충분함
- 성능 차이는 매우 작음
  - test median APE: `0.1585` → `0.1580`
  - test p95 APE: `0.8738` → `0.8723`
- 따라서 Warm 최종 후보 판단은 수렴 경고 때문에 뒤집히지 않음

## 6. 결론

- Warm Huber 후보는 유지 가능함
- 운영 후보 학습 설정은 `max_iter=3000` 이상으로 두는 것이 안전함
- `max_iter=5000`은 3000과 결과가 같으므로 우선 3000을 권장함
