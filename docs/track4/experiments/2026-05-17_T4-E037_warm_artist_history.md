# T4-E037 Warm 작가 이력 피처 검증

- 날짜: 2026-05-17
- 연결 가설: T4-H3
- 목적: Warm에서 작가 이력 피처를 train 기준으로만 계산했을 때 성능이 개선되는지 확인
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`

## 가설

- Warm 작가 이력 피처는 예측 시점 이전 정보만으로 계산해도 성능이 유지되거나 개선될 것이다.

## 실험 방법

- validation 정답값은 피처 계산에 사용하지 않음
- 작가별 통계는 `track4_train.csv`에서만 계산함
- 비교 피처셋을 나눠서 어떤 작가 정보가 효과적인지 확인함
- 모델: Ridge
- 평가 지표: Warm median APE, p95 APE, RMSE(log), Within-30%

## 비교 피처셋

- `structure_only`
- 작가 관련 피처 제외

- `artist_key_only`
- 작가 key만 추가

- `artist_count_only`
- train 기준 작가 작품 수만 추가

- `artist_price_stats_only`
- train 기준 작가 가격 통계만 추가
- `artist_train_median_log_price`
- `artist_train_mean_log_price`
- `artist_train_iqr_log_price`

- `artist_key_count`
- 기존 Warm 후보
- 작가 key + 작가 작품 수

- `artist_key_price_stats`
- 작가 key + train 기준 작가 가격 통계

## 결과

- 결과 파일: `data/track4/results/t4_e037_warm_artist_history_metrics.json`
- 예측 파일: `data/track4/predictions/t4_e037_warm_artist_history_predictions.csv`

| 피처셋 | Warm median APE | Warm p95 APE | RMSE(log) | Within-30% |
|---|---:|---:|---:|---:|
| structure_only | 0.5400 | 2.6357 | 0.7725 | 0.3582 |
| artist_key_only | 0.2665 | 1.4996 | 0.5999 | 0.5373 |
| artist_count_only | 0.5040 | 2.5784 | 0.7675 | 0.2836 |
| artist_price_stats_only | 0.3007 | 1.2280 | 0.6773 | 0.4925 |
| artist_key_count | 0.2597 | 1.5644 | 0.6000 | 0.5522 |
| artist_key_price_stats | 0.2326 | 1.0538 | 0.6082 | 0.5970 |

## 해석

- Warm에서는 작가 정보가 성능에 크게 중요함
- 작가 작품 수만으로는 충분하지 않음
- 작가 key만 넣어도 구조-only보다 크게 개선됨
- train 기준 작가 가격 통계는 p95 APE 개선에 특히 효과가 있음
- `artist_key_price_stats`가 median APE `0.2326`으로 현재까지 Warm validation 기준 가장 좋은 조합임
- 다만 작가별 과거 가격 통계는 운영에서 확보 가능한 데이터인지 확인이 필요함
- 운영에서 과거 가격 통계를 만들 수 없다면 `artist_key_count` 또는 `artist_key_only`를 보수적 후보로 둬야 함

## 결론

- T4-H3은 부분 검증으로 처리함
- 성능 기준 Warm 최고 후보: `artist_key_price_stats`
- 운영 보수 후보: `artist_key_count`
- 다음 단계에서는 가격 통계 피처의 운영 가능성과 test 성능을 별도로 확인해야 함

## 실행 명령

```bash
python3 scripts/track4/run_t4_e037_warm_artist_history.py
```
