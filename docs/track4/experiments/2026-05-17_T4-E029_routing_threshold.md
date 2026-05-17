# T4-E029 작가 작품 수 기준 라우팅 threshold

- 실험 ID: `T4-E029`
- 연결 가설: `T4-H10`, `T4-H19`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Warm / Cold 라우팅 기준을 작가 존재 여부만으로 둘지 확인함
- 학습 데이터에 작가가 있더라도 작품 수가 적으면 Cold 모델로 보내는 것이 더 안정적인지 확인함
- 저이력 Warm 작가가 실제로 더 어려운 구간인지 확인함

## 2. 확인하려는 질문

- 작가 작품 수가 1건 이상이면 Warm으로 봐도 되는가
- 작가 작품 수가 3/5/10/20건 이상일 때만 Warm 모델을 쓰면 성능이 좋아지는가
- 저이력 Warm을 Cold 모델로 보내면 오차가 줄어드는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 평가 데이터: `data/track4_split/track4_val_warm.csv`
- Cold 평가 데이터: `data/track4_split/track4_val_cold.csv`

## 4. 사용 모델

- Warm 모델
- `Ridge`
- 사용 피처: 구조 피처 + `support_category` + `artist_key` + 작가 이력 피처
- Cold 모델
- `QuantileRegressor`
- 사용 피처: `medium_category`, `log_area`, `aspect_ratio`

## 5. 라우팅 기준

- 기본 기준
- 학습 데이터에 작가가 있으면 Warm 모델 사용
- 학습 데이터에 작가가 없으면 Cold 모델 사용
- threshold 실험 기준
- `artist_works_count_train >= threshold`이면 Warm 모델 사용
- `artist_works_count_train < threshold`이면 Cold 모델 사용
- 비교 threshold
- `1`
- `3`
- `5`
- `10`
- `20`

## 6. 실행 명령

```bash
python3 scripts/track4/run_t4_e029_routing_threshold.py
```

## 7. 결과 파일

- 결과 JSON: `data/track4/results/t4_e029_routing_threshold_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e029_routing_threshold_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e029_routing_threshold.py`

## 8. 기본 비교 결과

| 구분 | rows | median APE | p95 APE | Within-30% | Within-50% |
|---|---:|---:|---:|---:|---:|
| Warm 전체를 Warm 모델로 예측 | 67 | 0.2597 | 1.5644 | 0.5522 | 0.6567 |
| Warm 전체를 Cold 모델로 예측 | 67 | 0.4394 | 2.0152 | 0.3731 | 0.5373 |
| Cold 전체를 Cold 모델로 예측 | 1,814 | 0.3642 | 1.1421 | 0.4305 | 0.6389 |

## 9. threshold별 Warm 결과

| threshold | Cold로 보낸 Warm rows | Warm median APE | Warm p95 APE | Within-30% | 해석 |
|---:|---:|---:|---:|---:|---|
| 1 | 0 | 0.2597 | 1.5644 | 0.5522 | 기본 기준, 최선 |
| 3 | 9 | 0.2763 | 1.5644 | 0.5224 | 기본보다 악화 |
| 5 | 18 | 0.3009 | 1.7441 | 0.4925 | 악화 |
| 10 | 39 | 0.3009 | 2.0152 | 0.4925 | 악화 |
| 20 | 49 | 0.3503 | 1.9728 | 0.4627 | 악화 |

## 10. 해석

- Warm 평가셋에서는 작가 작품 수 threshold를 높일수록 전체 Warm 성능이 악화됨
- 저이력 Warm을 Cold 모델로 보내는 방식은 현재 validation 기준에서 이득이 없음
- 작가 작품 수가 많은 구간은 median APE가 낮아지는 경향이 있음
- 하지만 저이력 작가도 Cold 모델보다 Warm 모델을 쓰는 편이 전체적으로 나음
- 따라서 라우팅 기준은 우선 “작가가 train에 있으면 Warm”으로 유지하는 것이 적절함

## 11. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H10`: 작가 작품 수 threshold를 높이는 라우팅은 현재 결과에서 지지되지 않음
- `T4-H19`: 저이력 Warm이 더 위험할 수 있다는 신호는 있으나, Cold 모델로 보내는 방식은 부적절함
- 운영 후보:
- Warm/Cold 라우팅은 작가 존재 여부 기준 유지
- `artist_works_count_train`은 라우팅 기준보다 신뢰도/경고 기준 후보로 유지

## 12. 후속 작업

- 저이력 Warm은 가격 범위/신뢰도 실험에서 별도 위험 구간으로 확인
- 반복 split에서 threshold 결과가 유지되는지 필요 시 재검증
