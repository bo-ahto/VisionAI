# T4-E024 Warm 작가 피처 ablation

- 실험 ID: `T4-E024`
- 연결 가설: `T4-H2`, `T4-H20`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Warm 예측에서 작가 정보가 실제로 성능을 개선하는지 확인함
- 작가명/작가 key 자체와 작가 이력 피처의 효과를 분리해서 봄
- 운영에서 작가 정보를 어떤 방식으로 사용할지 판단하기 위한 기준을 만듦

## 2. 확인하려는 질문

- Warm에서는 작가 key를 넣으면 구조-only 모델보다 좋아지는가
- 작가 작품 수 같은 이력 피처만으로도 작가 key를 대체할 수 있는가
- 작가 key와 작가 이력 피처를 함께 쓰면 추가 개선이 있는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- Warm 평가 데이터: `data/track4_split/track4_val_warm.csv`
- Cold 평가 데이터: 사용하지 않음
- calibration 데이터: 사용하지 않음

| 구분 | rows | 작가 수 | 가격 중앙값 | 작가 작품 수 중앙값 |
|---|---:|---:|---:|---:|
| train | 28,905 | 1,834 | 3,091,200 | 41 |
| val_warm | 67 | 67 | 2,346,000 | 9 |

## 4. 사용 피처

- 공통 구조 피처
- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`
- 작가 이력 피처
- `artist_works_log`
- `artist_works_count_train`
- 작가 key 피처
- `artist_key`

## 5. 사용 모델

- `Ridge`
- 이유
- 작가 key처럼 범주 수가 많은 피처를 안정적으로 비교하기 위해 사용
- 이번 실험의 목적은 최종 모델 선정이 아니라 피처 효과 확인임

## 6. 비교 기준

- `structure_only`
- 작가 정보 없이 작품 구조 피처만 사용
- `structure_plus_artist_history`
- 작품 구조 피처 + 작가 작품 수
- `structure_plus_artist_key`
- 작품 구조 피처 + 작가 key
- `structure_plus_artist_key_history`
- 작품 구조 피처 + 작가 key + 작가 작품 수

## 7. 실행 명령

```bash
python3 scripts/track4/run_t4_e024_warm_artist_ablation.py
```

## 8. 결과 파일

- 결과 JSON: `data/track4/results/t4_e024_warm_artist_ablation_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e024_warm_artist_ablation_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e024_warm_artist_ablation.py`

## 9. 주요 결과

| 피처 조합 | median APE | MAPE | RMSE(log) | Within-30% | Within-50% | p95 APE |
|---|---:|---:|---:|---:|---:|---:|
| structure_only | 0.4619 | 0.9191 | 0.7977 | 0.3433 | 0.5075 | 3.1280 |
| structure_plus_artist_history | 0.5076 | 0.9055 | 0.7971 | 0.3284 | 0.4925 | 3.1985 |
| structure_plus_artist_key | 0.2869 | 0.4838 | 0.6125 | 0.5224 | 0.6418 | 1.6608 |
| structure_plus_artist_key_history | 0.2697 | 0.4846 | 0.6125 | 0.5224 | 0.6567 | 1.6488 |

## 10. 해석

- 작가 key를 넣으면 Warm median APE가 `0.4619`에서 `0.2869`로 개선됨
- 작가 key와 작가 이력을 함께 쓰면 Warm median APE가 `0.2697`로 가장 좋음
- 작가 이력 피처만 추가한 경우 median APE는 `0.5076`으로 오히려 나빠짐
- 따라서 작가 작품 수만으로 작가 key를 대체하기는 어려움
- 다만 이번 결과는 `val_warm` 67건 기준이므로 반복 검증이 필요함

## 11. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H2`: Warm에서 작가 정보가 성능을 개선한다는 가설은 validation 기준 지지됨
- `T4-H20`: 작가명보다 이력 피처가 더 안정적일 수 있다는 가설은 현재 결과만으로는 지지되지 않음
- 운영 후보:
- Warm에서는 `artist_key` 사용 가능성을 유지함
- 작가 이력 피처는 단독 대체가 아니라 보조 피처로만 검토함

## 12. 후속 작업

- 반복 split 또는 test 확인으로 작가 key 효과가 안정적인지 확인
- 동명이인/작가명 표기 흔들림이 있을 때 작가 key 생성 정책을 재검토
- `T4-H10`, `T4-H19`와 연결해 저이력 Warm 라우팅 기준을 확인
