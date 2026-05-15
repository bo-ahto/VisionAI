# H68 Warm 라우팅 기준 검증 기록

- 날짜: 2026-05-14
- 실험 ID: `H68_warm_routing_threshold`
- 관련 가설: H68
- 실행 스크립트: `scripts/track3/h68_warm_routing_threshold.py`
- 결과 파일: `data/track3_h68_warm_routing_threshold_results.json`

## 1. 실험 목적

- 현재 운영 기준은 작가가 학습 데이터에 1건 이상 있으면 Warm 모델을 사용함
- 저이력 작가는 Warm 오차가 높게 나타났기 때문에, Warm 사용 기준을 3건/5건 이상으로 올리는 것이 나은지 확인함
- 기준 미만 작가는 Cold fallback을 적용했을 때 성능이 좋아지는지 검증함

## 2. 사용 데이터

- 학습 데이터: `data/release_split/track3_train.csv`
- 평가 데이터: `data/release_split/track3_test_warm.csv`
- train: 34,629건
- Warm 평가: 1,685건

## 3. 사용 모델

- Warm 모델
- H66 `larger_low_lr` LightGBM
- seed `11`, `22`, `33` 평균 예측
- fallback 모델
- Cold base Quantile/LAD 모델
- Cold 기본 피처셋 사용
- 평가 지표
- Warm median APE
- p95 APE
- 낮을수록 좋음

## 4. 비교 정책

- `count >= 1`
- 작가 학습 작품이 1건 이상이면 Warm 사용
- 현재 기준
- `count >= 2`
- 2건 이상이면 Warm, 1건이면 Cold fallback
- `count >= 3`
- 3건 이상이면 Warm, 1~2건은 Cold fallback
- `count >= 5`
- 5건 이상이면 Warm, 1~4건은 Cold fallback
- `count >= 10`
- 10건 이상이면 Warm, 1~9건은 Cold fallback
- `count >= 20`
- 20건 이상이면 Warm, 1~19건은 Cold fallback
- `count >= 50`
- 50건 이상이면 Warm, 나머지는 Cold fallback

## 5. 전체 결과

| 정책 | median APE | p95 APE | Warm 사용 | fallback 사용 |
|---|---:|---:|---:|---:|
| 항상 Warm / `count >= 1` | `0.1024` | `0.9653` | 1,685 | 0 |
| `count >= 2` | `0.1188` | `1.1285` | 1,516 | 169 |
| `count >= 3` | `0.1369` | `1.3495` | 1,350 | 335 |
| `count >= 5` | `0.1828` | `1.7265` | 1,113 | 572 |
| `count >= 10` | `0.2655` | `2.1063` | 756 | 929 |
| `count >= 20` | `0.3791` | `2.3679` | 430 | 1,255 |
| `count >= 50` | `0.4711` | `2.5304` | 158 | 1,527 |
| 항상 Cold fallback | `0.4982` | - | 0 | 1,685 |

## 6. 저이력 구간 비교

- 작가 학습 작품 수 1건
- Warm median APE `0.2596`
- Cold fallback median APE `0.5651`
- fallback 승률 `31.95%`
- 작가 학습 작품 수 1~2건
- Warm median APE `0.2038`
- Cold fallback median APE `0.5810`
- fallback 승률 `27.16%`
- 작가 학습 작품 수 1~5건
- Warm median APE `0.1480`
- Cold fallback median APE `0.5505`
- fallback 승률 `24.70%`

## 7. 해석

- 작품 수 기준을 높일수록 전체 Warm 성능이 악화됨
- 저이력 작가에서도 Cold fallback보다 Warm 모델이 더 나음
- 특히 `count >= 5` 정책은 median APE가 `0.1024 -> 0.1828`로 크게 악화됨
- 다만 작가 학습 작품 수 1건 구간은 Warm에서도 p95 APE `2.9022`로 매우 불안정함
- 따라서 모델을 Cold로 바꾸는 것보다 Warm을 유지하고 신뢰도 경고/넓은 가격 범위를 주는 것이 적절함

## 8. 결론

- Warm 라우팅 기준은 기존처럼 `artist_train_count >= 1` 유지
- `artist_train_count < 5` 또는 특히 `== 1`인 작가는 낮은 신뢰도 등급으로 표시
- 저이력 작가를 Cold 모델로 보내는 정책은 기각

## 9. 다음 작업

- H47/H50/H51의 Warm 신뢰도 등급 정책에 H68 결과를 반영
- 운영 라우팅 문서에 `artist_train_count >= 1` 기준을 명시
