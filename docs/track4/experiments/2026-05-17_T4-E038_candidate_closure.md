# T4-E038 최종 후보 validation/test 닫기 실험

- 날짜: 2026-05-17
- 연결 가설: T4-H1, T4-H2, T4-H3, T4-H4, T4-H15, T4-H21, T4-H23
- 목적: 순서도상 `후보 피처 기반 최종 모델 비교` 단계로 넘어가기 위해 Warm / Cold 후보를 validation과 test에서 동시에 평가
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_cold.csv`

## 실험 방법

- train으로만 모델을 학습함
- validation에서 후보 성능을 확인함
- test에서 validation 결과가 유지되는지 확인함
- Warm / Cold는 분리 평가함
- source는 모델 피처로 사용하지 않고 slice 감사로만 확인함
- 금지 피처 manifest 검사를 함께 실행함

## 후보 모델

- Warm 후보
- `warm_structure_only`: 작가 정보 없는 비교 기준
- `warm_operational_artist_count`: 작가 key + 작가 작품 수
- `warm_performance_artist_price_stats`: 작가 key + train 기준 작가 가격 통계

- Cold 후보
- `cold_area_only`: medium + log_area
- `cold_full_size`: medium + width/height/log_area/aspect/3D

## 결과

- 결과 파일: `data/track4/results/t4_e038_candidate_closure_metrics.json`
- 예측 파일: `data/track4/predictions/t4_e038_candidate_closure_predictions.csv`

| 후보 | validation median APE | validation p95 APE | test median APE | test p95 APE |
|---|---:|---:|---:|---:|
| warm_structure_only | 0.5400 | 2.6357 | 0.5590 | 3.5465 |
| warm_operational_artist_count | 0.2597 | 1.5644 | 0.2810 | 2.5504 |
| warm_performance_artist_price_stats | 0.2326 | 1.0538 | 0.2201 | 1.1118 |
| cold_area_only | 0.3613 | 1.1135 | 0.4365 | 2.9177 |
| cold_full_size | 0.3349 | 1.3041 | 0.4199 | 2.7609 |

## 해석

- Warm
- `warm_performance_artist_price_stats`가 validation과 test 모두에서 가장 좋음
- test median APE `0.2201`, p95 APE `1.1118`
- 성능 기준으로는 현재 Track 4 Warm 최고 후보임
- 단, 작가별 과거 가격 통계를 운영에서 만들 수 있어야 최종 채택 가능함

- Cold
- `cold_full_size`가 validation과 test 모두 median APE 기준으로 우세함
- test median APE `0.4199`
- 다만 test p95 APE `2.7609`로 큰 오차 위험이 큼
- Cold는 단일 가격 모델만으로 최종 확정하기 어렵고 가격 범위/신뢰도 정책이 필요함

## 가설 상태 판단

- 검증 완료 전환 가능
- T4-H2: Warm에서 작가 정보가 성능을 개선한다는 점은 test에서도 확인됨
- T4-H21: Warm/Cold 분리 후보가 필요하다는 방향은 유지됨

- 부분 검증 유지
- T4-H3: 가격 통계 피처 성능은 좋지만 운영 가능성 확인 필요
- T4-H4: Cold robust 후보는 median 기준 우세하나 tail risk가 큼
- T4-H15: Cold 크기 피처는 median과 p95 기준 결론이 갈림
- T4-H23: source slice는 validation 중심이라 test source slice 보완 필요

- 세부 가설 필요
- Cold p95 APE를 줄이는 별도 가설 필요
- Cold 저위험 구간만 서비스 가능한지 확인하는 별도 가설 필요
- Warm 가격 통계 피처를 운영 DB로 만들 수 있는지 확인하는 별도 가설 필요

## 결론

- Warm 모델은 성능 후보를 거의 확정할 수 있는 단계로 이동함
- Cold 모델은 median 성능 후보는 정해졌지만, 가격 범위/위험 경고 없이 서비스 적용하기 어려움
- 다음 실험은 `가격 범위/신뢰도 정책 보완`을 우선 진행해야 함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e038_candidate_closure.py
```
