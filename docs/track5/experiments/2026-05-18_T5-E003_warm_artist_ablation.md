# T5-E003 Warm 작가 피처 ablation

- 날짜: 2026-05-18
- 관련 가설: T5-H3
- 상태: 완료
- 목적: Warm 상황에서 작가 key, 작가 이력, train 기준 작가 가격 통계가 성능을 개선하는지 확인

## 1. 확인하려는 것

- Warm에서 작품 구조 정보만으로는 한계가 있는가
- 작가 key를 넣으면 성능이 개선되는가
- 작가 작품 수와 train 기준 작가 가격 통계가 추가 개선을 주는가

## 2. 사용 데이터

- 학습: `data/track5_split/track5_train.csv`
- 검증: `data/track5_split/track5_val_warm.csv`
- test는 사용하지 않음

## 3. 사용 모델

- `Ridge`
- 목적: 피처 효과를 먼저 보기 위해 단순하고 안정적인 모델로 비교

## 4. 비교 피처셋

- `structure_only`
- `structure_plus_artist_history`
- `structure_plus_artist_key`
- `structure_plus_artist_key_history`
- `structure_plus_artist_key_history_price_stats`

## 5. 결과

| 피처셋 | Warm median APE | Warm p95 APE | Within-30 | Within-50 |
|---|---:|---:|---:|---:|
| structure_only | 0.4707 | 3.3077 | 0.2986 | 0.5204 |
| structure_plus_artist_history | 0.4622 | 2.9924 | 0.3258 | 0.5294 |
| structure_plus_artist_key | 0.2775 | 1.3941 | 0.5520 | 0.7466 |
| structure_plus_artist_key_history | 0.2738 | 1.3583 | 0.5385 | 0.7557 |
| structure_plus_artist_key_history_price_stats | 0.2279 | 0.9083 | 0.6290 | 0.7873 |

## 6. 해석

- Warm에서는 작가 key가 성능 개선에 가장 큰 영향을 준다.
- 작가 작품 수만 추가하는 효과는 제한적이다.
- train 기준 작가 가격 통계까지 추가하면 median APE와 p95 APE가 모두 개선된다.
- 단, 작가 가격 통계는 예측 대상 작품 가격을 포함하면 안 되고 train/과거 데이터 기준으로만 계산해야 한다.

## 7. 결론

- T5-H3는 validation 기준 검증 완료로 본다.
- Warm 후보 피처셋은 `structure_plus_artist_key_history_price_stats`를 우선 후보로 둔다.
- 다음 단계에서는 Cold 모델군 비교를 진행한다.

## 8. 산출물

- 실행 스크립트: `scripts/track5/run_t5_e003_warm_artist_ablation.py`
- 결과 JSON: `data/track5/results/t5_e003_warm_artist_ablation_metrics.json`
- 예측 결과: `data/track5/predictions/t5_e003_warm_artist_ablation_predictions.csv`
