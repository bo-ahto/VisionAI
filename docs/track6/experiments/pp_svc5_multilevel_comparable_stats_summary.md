# PP-SVC5 Warm 다층 비교군 통계 피처 실험

- 작성일: 2026-06-04 00:48
- 목적: 비교군 통계를 하나만 고르는 기존 fallback 방식보다 여러 비교군 수준을 동시에 넣는 방식이 더 좋은지 확인
- 대상: Warm Huber
- 데이터 통제: train/validation/test split 고정
- 누수 통제: train 비교군 통계는 5-fold 교차검증 방식, validation/test는 train-only 방식

## 1. 실험 구성

- `baseline_huber`: 기존 Warm Huber 기준 피처만 사용
- `fallback_numeric`: 기존 PP-SVC1 방식의 선택된 비교군 통계 사용
- `multi_*_alpha001`: 다층 비교군 피처를 강한 정규화 Huber로 학습
- `multi_default_median_n_alpha001`: 여러 비교군 수준의 중앙값/면적단가/표본 수를 동시에 사용
- `multi_default_full_numeric_alpha001`: 여러 비교군 수준의 중앙값/분위값/범위/면적단가/표본 수를 동시에 사용
- `multi_loose_median_n_alpha001`: 최소 표본 기준 완화
- `multi_strict_median_n_alpha001`: 최소 표본 기준 강화
- `multi_plus_fallback_alpha001`: 기존 fallback 통계와 다층 통계를 함께 사용
- `blend_*_ppv8_*`: 새 비교군 후보와 기존 PP-V8 방어형 후보를 로그 가격 기준으로 결합

## 2. Test 결과 상위 후보

| 후보 | 방식 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `blend_fallback_numeric_ppv8_wsvc_0.60` | weighted_blend_with_ppv8 | 0.1362 | 0.2717 | 0.8329 | 0.4003 |
| `blend_fallback_numeric_ppv8_wsvc_0.55` | weighted_blend_with_ppv8 | 0.1376 | 0.2706 | 0.8414 | 0.3987 |
| `blend_fallback_numeric_ppv8_wsvc_0.65` | weighted_blend_with_ppv8 | 0.1382 | 0.2733 | 0.8432 | 0.4024 |
| `blend_fallback_numeric_ppv8_wsvc_0.70` | weighted_blend_with_ppv8 | 0.1401 | 0.2751 | 0.8351 | 0.4047 |
| `blend_fallback_numeric_ppv8_wsvc_0.50` | weighted_blend_with_ppv8 | 0.1402 | 0.2699 | 0.8472 | 0.3973 |
| `blend_svcnum_ppv8_wsvc_0.70` | reference | 0.1405 | 0.2748 | 0.8331 | 0.3996 |
| `blend_fallback_numeric_ppv8_wsvc_0.85` | weighted_blend_with_ppv8 | 0.1425 | 0.2835 | 0.9259 | 0.4137 |
| `blend_fallback_numeric_ppv8_wsvc_0.75` | weighted_blend_with_ppv8 | 0.1430 | 0.2774 | 0.8669 | 0.4074 |
| `blend_fallback_numeric_ppv8_wsvc_0.80` | weighted_blend_with_ppv8 | 0.1430 | 0.2802 | 0.9075 | 0.4104 |
| `blend_fallback_numeric_ppv8_wsvc_0.90` | weighted_blend_with_ppv8 | 0.1465 | 0.2872 | 0.9411 | 0.4174 |
| `fallback_numeric` | warm_huber | 0.1528 | 0.2956 | 0.9694 | 0.4255 |
| `pp_v8_compact_blend_mape_guarded` | reference | 0.1632 | 0.2816 | 0.9311 | 0.4028 |
| `baseline_huber` | warm_huber | 0.2274 | 0.4952 | 2.0130 | 0.6081 |

- `multi_*` 직접 투입 후보는 수렴 불안정으로 비정상 예측값 발생
- 세부 수치는 `outputs/metrics.csv`에 보존
- 보고/의사결정 후보에서는 제외

## 3. Validation MAPE 기준 상위 후보

| 후보 | 방식 | MdAPE | MAPE | p95_APE |
|---|---|---:|---:|---:|
| `blend_fallback_numeric_ppv8_wsvc_0.75` | weighted_blend_with_ppv8 | 0.1273 | 0.2107 | 0.6234 |
| `blend_fallback_numeric_ppv8_wsvc_0.70` | weighted_blend_with_ppv8 | 0.1285 | 0.2107 | 0.6541 |
| `blend_svcnum_ppv8_wsvc_0.70` | reference | 0.1305 | 0.2110 | 0.6580 |
| `blend_fallback_numeric_ppv8_wsvc_0.80` | weighted_blend_with_ppv8 | 0.1249 | 0.2112 | 0.6252 |
| `blend_fallback_numeric_ppv8_wsvc_0.65` | weighted_blend_with_ppv8 | 0.1367 | 0.2113 | 0.6445 |
| `blend_fallback_numeric_ppv8_wsvc_0.85` | weighted_blend_with_ppv8 | 0.1200 | 0.2123 | 0.6419 |
| `blend_fallback_numeric_ppv8_wsvc_0.60` | weighted_blend_with_ppv8 | 0.1362 | 0.2125 | 0.6613 |
| `blend_fallback_numeric_ppv8_wsvc_0.90` | weighted_blend_with_ppv8 | 0.1200 | 0.2136 | 0.6424 |
| `blend_fallback_numeric_ppv8_wsvc_0.55` | weighted_blend_with_ppv8 | 0.1372 | 0.2140 | 0.6760 |
| `blend_fallback_numeric_ppv8_wsvc_0.50` | weighted_blend_with_ppv8 | 0.1325 | 0.2159 | 0.6895 |
| `fallback_numeric` | warm_huber | 0.1212 | 0.2170 | 0.6502 |
| `pp_v8_compact_blend_mape_guarded` | reference | 0.1544 | 0.2544 | 0.8084 |

## 4. 선택 후보

- 선택 기준: validation MAPE with PP-V8 MdAPE guard
- 선택 후보: `blend_fallback_numeric_ppv8_wsvc_0.75`
- test MdAPE: `0.1430`
- test MAPE: `0.2774`
- test p95_APE: `0.8669`

## 5. Coverage 요약

| 정책 | 비교군 수준 | covered share | covered rows | median N |
|---|---|---:|---:|---:|
| default | `artist_medium_support_size` | 0.407 | 247 | 8.0 |
| default | `artist_size` | 0.514 | 312 | 9.0 |
| default | `artist` | 1.000 | 607 | 13.0 |
| default | `medium_support_size` | 0.909 | 552 | 983.0 |
| default | `medium_category_support_size` | 0.909 | 552 | 983.0 |
| default | `medium_size` | 0.970 | 589 | 1606.0 |
| loose | `artist_medium_support_size` | 0.583 | 354 | 7.0 |
| loose | `artist_size` | 0.713 | 433 | 7.0 |
| loose | `artist` | 1.000 | 607 | 13.0 |
| loose | `medium_support_size` | 0.949 | 576 | 937.4 |
| loose | `medium_category_support_size` | 0.949 | 576 | 937.4 |
| loose | `medium_size` | 0.977 | 593 | 1606.0 |
| strict | `artist_medium_support_size` | 0.186 | 113 | 17.0 |
| strict | `artist_size` | 0.250 | 152 | 17.0 |
| strict | `artist` | 0.598 | 363 | 21.0 |
| strict | `medium_support_size` | 0.871 | 529 | 1059.0 |
| strict | `medium_category_support_size` | 0.871 | 529 | 1059.0 |
| strict | `medium_size` | 0.957 | 581 | 1606.0 |

## 6. 해석

- 다층 비교군 후보가 기존 `fallback_numeric`보다 좋아지면 Huber가 여러 비교군 기준을 조합해 가격 기준선을 더 잘 잡는다는 의미
- 다층 비교군 후보가 약하면 현재 데이터에서는 가장 신뢰 가능한 비교군 하나를 고르는 fallback 방식이 더 안정적이라는 의미
- 결합 후보가 기존 `PP-SVC3`보다 좋아지면 Warm 서비스 후보를 `PP-SVC6` 반복 holdout 검증으로 승격
- 결합 후보가 기존 `PP-SVC3`보다 약하면 기존 `svc_numeric 70% + PP-V8 30%` 정책 유지

## 7. 실행 결론

- 다층 비교군 원시 피처 직접 투입 방식은 보류
- 이유: Huber가 비교군별 중앙값/분위값/표본 수의 강한 중복 구조에서 수렴 불안정
- 정규화 강화 후에도 `multi_*` 후보의 test 오차가 비정상적으로 커짐
- 해석: 비교군을 무조건 더 많이 쪼개서 넣는 방식은 현재 Warm Huber 구조와 맞지 않음
- 안정 후보: 기존 fallback 비교군 통계 `fallback_numeric`
- 추가로 확인된 가능성: `fallback_numeric + PP-V8` 결합 비율 재조정
- test 기준 최상위 후보: `blend_fallback_numeric_ppv8_wsvc_0.60`
- test MdAPE: `0.1362`
- test MAPE: `0.2717`
- test p95_APE: `0.8329`
- 기존 PP-SVC3 reference `blend_svcnum_ppv8_wsvc_0.70` 대비 test MdAPE/MAPE 소폭 개선
- 단, validation 선택 후보는 `blend_fallback_numeric_ppv8_wsvc_0.75`
- 따라서 test 상위 후보를 바로 채택하지 않고 `PP-SVC6` 반복 holdout 검증 필요
