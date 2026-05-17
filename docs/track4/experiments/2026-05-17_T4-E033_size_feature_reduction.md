# T4-E033 크기 피처 축소/대표 조합 실험

- 실험 ID: `T4-E033`
- 연결 가설: `T4-H15`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- 크기 피처를 많이 넣는 것이 좋은지 확인함
- `log_area + aspect_ratio` 같은 대표 조합만으로 충분한지 확인함
- Warm과 Cold에서 같은 크기 피처 정책을 써도 되는지 확인함

## 2. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 평가 데이터: `data/track4_split/track4_val_warm.csv`
- Cold 평가 데이터: `data/track4_split/track4_val_cold.csv`

## 3. 사용 모델

- Warm 모델
- `Ridge`
- 작가 key, support, 작가 이력 포함
- Cold 모델
- `QuantileRegressor`
- 작가 피처 제외

## 4. 비교한 크기 피처 조합

- `no_size`
- 크기 피처 제외
- `area_only`
- `log_area`만 사용
- `area_aspect`
- `log_area`, `aspect_ratio`
- `raw_width_height`
- `width_cm`, `height_cm`
- `full_size`
- `width_cm`, `height_cm`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`

## 5. 실행 명령

```bash
python3 scripts/track4/run_t4_e033_size_feature_reduction.py
```

## 6. 결과 파일

- 결과 JSON: `data/track4/results/t4_e033_size_feature_reduction_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e033_size_feature_reduction_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e033_size_feature_reduction.py`

## 7. 주요 결과

| 크기 피처 조합 | Warm median APE | Warm p95 APE | Cold median APE | Cold p95 APE | 해석 |
|---|---:|---:|---:|---:|---|
| no_size | 0.6206 | 3.2289 | 0.7316 | 3.9749 | 크기 피처 없이는 크게 악화 |
| area_only | 0.2852 | 1.5057 | 0.3613 | 1.1135 | 단순하고 tail 안정적 |
| area_aspect | 0.2597 | 1.5644 | 0.3642 | 1.1421 | Warm median 최선 |
| raw_width_height | 0.3125 | 1.7698 | 0.3646 | 1.5293 | 대표 조합보다 불리 |
| full_size | 0.2970 | 1.6821 | 0.3349 | 1.3041 | Cold median 최선, p95 악화 |

## 8. 해석

- 크기 피처는 Warm/Cold 모두 필수임
- Warm에서는 `area_aspect`가 median APE 기준 최선임
- Cold에서는 `full_size`가 median APE 기준 최선임
- Cold p95 APE 기준으로는 `area_only`가 가장 안정적임
- `width_cm`, `height_cm` 원본값만 쓰는 방식은 Warm/Cold 모두 강한 후보가 아님
- 따라서 크기 피처는 하나의 공통 정책보다 Warm/Cold 목적에 따라 나눠야 함

## 9. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H15`는 부분적으로 지지됨
- Warm은 대표 조합 `log_area + aspect_ratio` 우선
- Cold는 median APE를 중시하면 `full_size`, tail risk를 중시하면 `area_only`를 후보로 둠
- 운영 후보:
- Warm: `area_aspect`
- Cold: `full_size`와 `area_only`를 후속 위험 구간/범위 실험에서 비교

## 10. 후속 작업

- Cold 최종 후보 선정 시 median APE와 p95 APE의 우선순위를 명확히 정함
- `T4-H28` 조합 피처 실험에서 size/material 조합을 추가 확인
