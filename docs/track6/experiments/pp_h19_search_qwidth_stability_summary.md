# PP-H19 검색 신뢰도 x q-width 보정 안정성 검증 요약

- 실행일: 2026-06-03
- 목적: H12B 보수 라벨 기반 H18 보정 후보가 특정 test 구성에서만 좋아진 것인지 확인한다.
- 결론: 검색 신뢰도와 q-width를 결합한 보정은 큰 오차 방어에 유효하다. 다만 목적 지표에 따라 후보를 분리해야 한다.

## 1. 실험 배경

- H11에서 외부 검색 수집은 가능하다는 것을 확인했다.
- H12에서 작가 일치/동명이인 자동 판정을 만들었다.
- H12B에서 검색 UI 링크와 무관 결과를 더 보수적으로 제외했다.
- H14/H18에서 H12B 라벨을 활용해 가격 범위와 잔차 보정을 다시 적용했다.

PP-H19는 이 결과가 안정적인지 확인하는 검증 단계다.

## 2. 검증 방식

| 항목 | 내용 |
|---|---|
| 기준 모델 | `PP-Y2 lgbq_search_all_external_interaction` |
| 보정 입력 | H12B 기반 `qwidth_bin x recommended_action` segment |
| 보정값 | validation segment별 `median residual_log` |
| 검증 데이터 | test cold 3,099건 |
| row bootstrap | 작품 row를 600회 다시 뽑아 안정성 확인 |
| artist bootstrap | 작가 단위로 600회 다시 뽑아 특정 작가 의존성 확인 |

delta 해석:

```text
delta = 기준 모델 점수 - 보정 후보 점수
```

- MdAPE, MAPE, p95_APE, RMSE_log는 delta가 양수이면 보정 후보가 더 좋다.
- Within_30, Within_50은 후보의 비율에서 기준 모델의 비율을 뺀 값이므로 양수이면 후보가 더 좋다.

## 3. Test 전체 점수

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 해석 |
|---|---:|---:|---:|---:|---|
| PP-Y2 기준 | 0.4421 | 1.0484 | 3.3537 | 0.8567 | 기준선 |
| `min80_cap0.2` | 0.4253 | 1.0471 | 3.0077 | 0.8621 | MdAPE 최우선 후보 |
| `min80_cap0.1` | 0.4271 | 1.0342 | 3.0077 | 0.8613 | MdAPE 개선, RMSE 악화 |
| `min30_cap0.1` | 0.4316 | 0.9832 | 3.0077 | 0.8504 | 안정 후보 |
| `min30_cap0.2` | 0.4347 | 0.9602 | 3.0077 | 0.8437 | MAPE/RMSE 균형 후보 |

## 4. Bootstrap 안정성 결과

| 후보 | 기준 | MdAPE 개선확률 | MAPE 개선확률 | p95 개선확률 | RMSE 개선확률 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `min30_cap0.1` | row | 0.9650 | 1.0000 | 1.0000 | 1.0000 | 작품 단위 매우 안정 |
| `min30_cap0.1` | artist | 0.8517 | 1.0000 | 0.9650 | 0.7600 | 작가 단위도 비교적 안정 |
| `min30_cap0.2` | row | 0.9050 | 1.0000 | 1.0000 | 1.0000 | 평균 오차 개선 강함 |
| `min30_cap0.2` | artist | 0.7317 | 0.9417 | 0.8467 | 0.7583 | 작가 구성에 다소 민감 |
| `min80_cap0.2` | row | 1.0000 | 0.6233 | 0.9650 | 0.0000 | MdAPE 중심 후보 |
| `min80_cap0.2` | artist | 0.9383 | 0.5400 | 0.5467 | 0.2100 | MdAPE 외 지표는 불안정 |

## 5. 해석

- `min80_cap0.2`는 MdAPE 개선 확률이 높다.
- 그러나 MAPE와 RMSE_log 개선 확률이 낮아 운영 기본 보정값으로 바로 쓰기에는 위험하다.
- `min30_cap0.2`는 MAPE와 RMSE_log 개선이 가장 크지만, 작가 단위 MdAPE 안정성이 낮아 수동 검수 후 재확인이 필요하다.
- `min30_cap0.1`은 개선 폭은 작지만 MAPE와 p95_APE 개선이 row/artist 기준 모두 안정적이다.
- 따라서 현재 운영 안전 후보는 `min30_cap0.1`, 성능 탐색 후보는 `min30_cap0.2`, MdAPE 전용 후보는 `min80_cap0.2`로 분리한다.

## 6. 다음 의사결정

| 용도 | 후보 | 이유 |
|---|---|---|
| 운영 안전안 | `min30_cap0.1` | 작가 단위에서도 MAPE/p95 개선이 안정적 |
| 평균 오차 개선안 | `min30_cap0.2` | MAPE/RMSE가 가장 크게 개선 |
| 대표 오차 개선안 | `min80_cap0.2` | MdAPE가 가장 낮음 |
| 최종 채택 전 필수 작업 | 수동 라벨 기반 재실행 | H12B는 자동 보수 라벨이므로 최종 검수 필요 |

## 7. 산출물

| 산출물 | 경로 |
|---|---|
| 실행 리포트 | `experiments/track6/PP-H19_search_qwidth_policy_stability/reports/result_report.html` |
| metrics | `experiments/track6/PP-H19_search_qwidth_policy_stability/outputs/metrics.csv` |
| bootstrap summary | `experiments/track6/PP-H19_search_qwidth_policy_stability/outputs/bootstrap_summary.csv` |
| 후보별 예측값 | `experiments/track6/PP-H19_search_qwidth_policy_stability/outputs/candidate_predictions.csv` |
