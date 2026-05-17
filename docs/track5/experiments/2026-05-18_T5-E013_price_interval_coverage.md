# T5-E013 가격 범위 커버리지 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H16
- 목적: validation 오차로 만든 가격 범위가 test에서 실제 가격을 어느 정도 포함하는지 확인

## 1. 실험 배경

- 단일 가격 예측은 이해하기 쉽지만 오차가 큰 작품에서는 위험함
- 가격 범위를 함께 주려면 범위가 실제 가격을 충분히 포함해야 함
- 동시에 범위가 너무 넓으면 서비스에서 의미가 약해짐

## 2. 사용 데이터

- 범위 계산 기준: validation 예측 오차
  - Warm: T5-E008 Warm Huber + full_size validation 예측
  - Cold: T5-E008 Cold Quantile + full_size validation 예측
- 범위 검증 대상: test 예측 오차
  - Warm: T5-E010 Warm Huber + full_size test 예측
  - Cold: T5-E010 Cold Quantile + full_size test 예측
- 결과: `data/track5/results/t5_e013_price_interval_coverage_metrics.json`

## 3. 실험 방법

- validation에서 절대 로그 오차를 계산함
- 그 오차의 p50, p80, p90 값을 가격 범위 폭으로 사용함
- test에서 해당 범위가 실제 가격을 포함하는 비율을 확인함
- 해석 기준
  - coverage: 실제 가격이 예측 범위 안에 들어온 비율
  - price multiplier: 예측 가격에서 위아래로 곱해지는 배수
  - full width ratio: 범위 상한이 하한보다 몇 배 넓은지

## 4. 결과

| 후보 | 범위 기준 | 가격 배수 | 상한/하한 폭 | test coverage | 해석 |
|---|---|---:|---:|---:|---|
| Warm Huber full_size | p50 | 1.17배 | 1.36배 | 0.4853 | 절반 수준 포함 |
| Warm Huber full_size | p80 | 1.46배 | 2.14배 | 0.7828 | 실무 검토 가능 |
| Warm Huber full_size | p90 | 1.73배 | 2.99배 | 0.8806 | 안정적이지만 범위가 넓어짐 |
| Cold Quantile full_size | p50 | 1.40배 | 1.97배 | 0.4399 | 절반 미만 포함 |
| Cold Quantile full_size | p80 | 2.15배 | 4.63배 | 0.7845 | 포함률은 높지만 범위가 큼 |
| Cold Quantile full_size | p90 | 2.83배 | 8.03배 | 0.8771 | 범위가 너무 넓어 실무 해석 어려움 |

## 5. 해석

- Warm
  - p80 범위는 coverage `0.7828`, 상한/하한 폭 `2.14배`
  - 단일 가격 + 보조 가격 범위 형태로 검토 가능함
- Cold
  - p80 범위는 coverage `0.7845`지만 상한/하한 폭이 `4.63배`
  - p90 범위는 coverage가 올라가지만 상한/하한 폭이 `8.03배`까지 커짐
  - Cold는 가격 범위만 붙인다고 서비스 가능성이 충분해지는 것은 아님
- 결론적으로 Cold는 예측값보다 `신뢰도 낮음`, `참고 범위`, `추가 정보 필요` 정책이 더 중요함

## 6. 결론

- Warm 가격 범위 정책은 후속 운영안 후보로 유지
- Cold 가격 범위 정책은 단독으로는 한계가 큼
- Cold는 다음 조건에서 경고를 우선 적용하는 방향이 필요함
  - 지지체 정보 없음
  - 재료 정보 없음
  - 초대형 작품
  - Cold 전체 예측
