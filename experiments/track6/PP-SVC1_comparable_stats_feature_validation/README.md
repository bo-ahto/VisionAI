# PP-SVC1 서비스 비교군 통계 피처 검증

- 작성일: 2026-06-03 20:50
- 목적: 서비스 비교군 통계값을 API 표시값과 모델 피처로 동시에 쓸 수 있는지 검증한다.
- 현재 split에는 `estimated_ho`가 없어 이번 실험은 호당가 직접값이 아니라 `면적 기준 단가`를 사용했다.
- validation/test 비교군 통계는 train 데이터만 사용했고, train 피처는 5-fold 방식으로 자기 가격이 들어가지 않게 만들었다.

## 1. Test 결과

| 실험 | scope | 모델 | 후보 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---|---:|---:|---:|---:|
| `PP-SVC1-CB` | cold | catboost | `baseline` | 0.4808 | 1.4852 | 5.9854 | 0.9697 |
| `PP-SVC1-CB` | cold | catboost | `svc_numeric` | 0.4885 | 1.1445 | 3.4749 | 0.9014 |
| `PP-SVC1-CB` | cold | catboost | `svc_full` | 0.4933 | 1.1782 | 3.6577 | 0.9072 |
| `PP-SVC1-DIRECT-COLD` | cold | service_prior | `svc_group_log_price_median` | 0.5223 | 1.1957 | 3.8200 | 1.0238 |
| `PP-SVC1-LGBM` | cold | lightgbm | `svc_numeric` | 0.4855 | 1.1844 | 3.5868 | 0.9148 |
| `PP-SVC1-LGBM` | cold | lightgbm | `svc_full` | 0.4856 | 1.2295 | 3.7608 | 0.9231 |
| `PP-SVC1-LGBM` | cold | lightgbm | `baseline` | 0.4873 | 1.3920 | 4.4602 | 0.9625 |
| `PP-SVC1-DIRECT-WARM` | warm | service_prior | `svc_group_log_price_median` | 0.3100 | 0.7193 | 2.2352 | 0.7632 |
| `PP-SVC1-W` | warm | huber | `svc_full` | 0.1496 | 0.2965 | 0.9499 | 0.4248 |
| `PP-SVC1-W` | warm | huber | `svc_numeric` | 0.1528 | 0.2956 | 0.9694 | 0.4255 |
| `PP-SVC1-W` | warm | huber | `baseline` | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

## 2. Baseline 대비 test 변화

| 실험 | 후보 | MdAPE 변화 | MAPE 변화 | p95 변화 | 해석 |
|---|---|---:|---:|---:|---|
| `PP-SVC1-CB` | `svc_numeric` | -0.0078 | 0.3407 | 2.5105 | 방어 후보 가능, 대표 후보는 보류 |
| `PP-SVC1-CB` | `svc_full` | -0.0125 | 0.3070 | 2.3277 | 방어 후보 가능, 대표 후보는 보류 |
| `PP-SVC1-LGBM` | `svc_numeric` | 0.0018 | 0.2076 | 0.8735 | 대표/평균 오차 모두 개선 |
| `PP-SVC1-LGBM` | `svc_full` | 0.0016 | 0.1625 | 0.6994 | 대표/평균 오차 모두 개선 |
| `PP-SVC1-W` | `svc_full` | 0.0778 | 0.1987 | 1.0631 | 대표/평균 오차 모두 개선 |
| `PP-SVC1-W` | `svc_numeric` | 0.0747 | 0.1996 | 1.0436 | 대표/평균 오차 모두 개선 |

## 3. 비교군 coverage

| scope | split | level/tier | rows | share | median N |
|---|---|---|---:|---:|---:|
| warm | train_oof | `artist` | 5665 | 0.210 | 12.0 |
| warm | train_oof | `artist_medium_support_size` | 15125 | 0.562 | 16.0 |
| warm | train_oof | `artist_size` | 3022 | 0.112 | 9.0 |
| warm | train_oof | `global` | 151 | 0.006 | 21531.0 |
| warm | train_oof | `medium_size` | 302 | 0.011 | 1105.0 |
| warm | train_oof | `medium_support_size` | 2649 | 0.098 | 709.0 |
| warm | train_oof | `tier:fallback_global` | 151 | 0.006 | 21531.0 |
| warm | train_oof | `tier:high_n` | 5513 | 0.205 | 137.0 |
| warm | train_oof | `tier:low_n` | 12805 | 0.476 | 8.0 |
| warm | train_oof | `tier:medium_n` | 8445 | 0.314 | 24.0 |
| warm | validation | `artist` | 252 | 0.486 | 9.0 |
| warm | validation | `artist_medium_support_size` | 202 | 0.389 | 8.0 |
| warm | validation | `artist_size` | 65 | 0.125 | 6.0 |
| warm | validation | `tier:high_n` | 5 | 0.010 | 54.0 |
| warm | validation | `tier:low_n` | 421 | 0.811 | 7.0 |
| warm | validation | `tier:medium_n` | 93 | 0.179 | 20.0 |
| warm | test | `artist` | 295 | 0.486 | 7.0 |
| warm | test | `artist_medium_support_size` | 247 | 0.407 | 8.0 |
| warm | test | `artist_size` | 65 | 0.107 | 6.0 |
| warm | test | `tier:high_n` | 17 | 0.028 | 68.0 |
| warm | test | `tier:low_n` | 479 | 0.789 | 7.0 |
| warm | test | `tier:medium_n` | 111 | 0.183 | 20.0 |
| cold | train_oof | `artist` | 5665 | 0.210 | 12.0 |
| cold | train_oof | `artist_medium_support_size` | 15125 | 0.562 | 16.0 |
| cold | train_oof | `artist_size` | 3022 | 0.112 | 9.0 |
| cold | train_oof | `global` | 151 | 0.006 | 21531.0 |
| cold | train_oof | `medium_size` | 302 | 0.011 | 1105.0 |
| cold | train_oof | `medium_support_size` | 2649 | 0.098 | 709.0 |
| cold | train_oof | `tier:fallback_global` | 151 | 0.006 | 21531.0 |
| cold | train_oof | `tier:high_n` | 5513 | 0.205 | 137.0 |
| cold | train_oof | `tier:low_n` | 12805 | 0.476 | 8.0 |
| cold | train_oof | `tier:medium_n` | 8445 | 0.314 | 24.0 |
| cold | validation | `global` | 44 | 0.016 | 26914.0 |
| cold | validation | `medium_size` | 134 | 0.049 | 1584.0 |
| cold | validation | `medium_support_size` | 2575 | 0.935 | 1212.0 |
| cold | validation | `tier:fallback_global` | 44 | 0.016 | 26914.0 |
| cold | validation | `tier:high_n` | 2606 | 0.947 | 1248.0 |
| cold | validation | `tier:medium_n` | 103 | 0.037 | 45.0 |
| cold | test | `global` | 141 | 0.045 | 26914.0 |
| cold | test | `medium_size` | 276 | 0.089 | 1584.0 |
| cold | test | `medium_support_size` | 2682 | 0.865 | 983.0 |
| cold | test | `tier:fallback_global` | 141 | 0.045 | 26914.0 |
| cold | test | `tier:high_n` | 2796 | 0.902 | 1115.0 |
| cold | test | `tier:medium_n` | 162 | 0.052 | 40.0 |

## 4. 해석 기준

- Warm에서 작가 기반 비교군이 많이 잡히면 Huber의 작가 기준선을 보완하는 피처로 해석한다.
- Cold에서 global 또는 재료/크기 fallback 비중이 크면, 작가별 prior보다는 작품 조건별 가격대 prior로 해석한다.
- 성능이 개선되지 않아도 coverage가 안정적이면 API 표시값으로는 사용할 수 있다.
- `estimated_ho`가 추가되면 `면적 기준 단가`를 실제 `호당가`로 교체해 재검증한다.

## 5. 실행 결론

- 비교군 중앙값을 그대로 예측값으로 쓰는 방식은 Warm test MdAPE `0.3100`, Cold test MdAPE `0.5223`으로 충분하지 않았다.
- 따라서 이번 개선은 단순히 비교군 중앙값으로 가격을 대체한 결과가 아니다.
- Warm에서는 Huber가 기존 작품 피처와 비교군 통계 피처를 함께 사용하면서 작가/조건별 가격 중심선을 더 잘 잡았다.
- Warm `svc_full`은 test MdAPE `0.1496`으로 기존 Warm Huber baseline `0.2274`보다 크게 좋아졌다.
- Cold에서는 CatBoost `svc_numeric`이 MAPE `1.4852 -> 1.1445`, p95 `5.9854 -> 3.4749`로 큰 오차 방어에 효과가 있었지만 MdAPE는 `0.4808 -> 0.4885`로 소폭 악화됐다.
- Cold LightGBM `svc_numeric`은 MdAPE `0.4873 -> 0.4855`, MAPE `1.3920 -> 1.1844`, p95 `4.4602 -> 3.5868`로 세 지표가 모두 개선됐다.
- 현재 판단은 Warm은 최종 후보 편입 전 반복 검증 대상으로 올리고, Cold는 대표 모델 교체보다 MAPE/p95 방어와 API 표시 근거 피처로 우선 활용하는 것이다.
