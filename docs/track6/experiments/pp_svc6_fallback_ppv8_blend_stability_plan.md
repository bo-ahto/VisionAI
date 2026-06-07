# PP-SVC6 Warm fallback 비교군 + PP-V8 결합 비율 안정성 검증 계획

## 1. 실험 목적

- `PP-SVC5`에서 확인된 추가 가능성 검증
- test 기준 `fallback_numeric + PP-V8` 결합의 `wsvc=0.55~0.60` 후보가 기존 `PP-SVC3`보다 좋아 보였음
- 단, validation 기준 선택 후보는 `wsvc=0.75`
- 따라서 test 결과만 보고 0.55~0.60을 채택하면 과적합 위험 존재
- 이번 실험은 validation 내부 반복 holdout으로 결합 비율이 안정적으로 선택되는지 확인

## 2. 이전 실험 근거

| 기준 | 후보 | MdAPE | MAPE | p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| 기존 서비스 1순위 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` | 0.1405 | 0.2748 | 0.8331 | 현재 기준 후보 |
| PP-SVC5 test 최상위 | `blend_fallback_numeric_ppv8_wsvc_0.60` | 0.1362 | 0.2717 | 0.8329 | test 기준 소폭 개선 |
| PP-SVC5 test MAPE 최저권 | `blend_fallback_numeric_ppv8_wsvc_0.55` | 0.1376 | 0.2706 | 0.8414 | MAPE는 낮지만 p95는 소폭 악화 |
| PP-SVC5 validation 선택 | `blend_fallback_numeric_ppv8_wsvc_0.75` | 0.1273 | 0.2107 | 0.6234 | validation 기준 선택 후보 |

## 3. 실험 대상

- 대상 모델
  - Warm 최종 후보군
- 입력 예측값
  - `fallback_numeric`: 기존 PP-SVC1 방식의 선택형 비교군 통계 Huber 예측
  - `PP-V8 compact_blend_mape_guarded`: 평균오차와 큰 오차를 방어하는 Warm 방어형 후보
- 비교 기준
  - 기존 `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
  - 단독 `fallback_numeric`
  - 단독 `PP-V8`

## 4. 결합식

- 로그 가격 기준 결합

```text
final_pred_log = w * fallback_numeric_pred_log + (1 - w) * pp_v8_pred_log
final_price = exp(final_pred_log)
```

- `w`의 의미
  - `w`가 높을수록 비교군 통계 후보를 더 신뢰
  - `w`가 낮을수록 PP-V8 방어 후보를 더 신뢰

## 5. 결합 비율 후보

- 후보 범위
  - `w = 0.40 ~ 0.90`
- 탐색 간격
  - `0.025`
- 이유
  - 기존 PP-SVC5에서 0.55~0.60이 test 상위였고 0.75가 validation 상위
  - 0.05 간격보다 촘촘하게 확인해 안정 구간을 찾기 위함

## 6. 검증 방식

- validation 데이터를 반복적으로 둘로 나눔
  - selection subset: 결합 비율 선택에만 사용
  - holdout subset: 선택된 결합 비율이 같은 validation 안의 미사용 구간에서도 유지되는지 확인
- holdout 방식
  - row holdout: 작품 row 기준 무작위 분할
  - artist holdout: 작가 기준 분할
- 반복 횟수
  - 방식별 200회
- test 데이터
  - 선택 후 최종 확인 전용
  - 결합 비율 선택에는 사용하지 않음

## 7. 선택 기준

| 선택 기준 | 설명 | 목적 |
|---|---|---|
| `mape_guarded_ppv8` | PP-V8보다 MdAPE가 나빠지지 않는 후보 중 MAPE 최소 | 평균오차 개선 |
| `mape_guarded_reference` | 기존 PP-SVC3보다 MdAPE가 나빠지지 않는 후보 중 MAPE 최소 | 기존 후보 대비 안전 개선 |
| `balanced_reference` | 기존 PP-SVC3 대비 MdAPE/MAPE/p95를 균형 점수로 비교 | 종합 성능 |
| `mdape_primary` | MdAPE 최저 후보 선택 | 대표 정확도 한계 확인 |

## 8. 채택 기준

- 1순위 채택 가능 조건
  - row holdout과 artist holdout에서 비슷한 weight 구간이 반복 선택
  - holdout MAPE가 기존 PP-SVC3 대비 개선 또는 동일 수준
  - test에서 MdAPE/MAPE/p95 중 2개 이상이 기존 PP-SVC3보다 개선
- 보류 조건
  - selection에서는 좋아 보이나 holdout/test에서 방향이 다름
  - 선택 weight가 row/artist holdout에서 크게 흔들림
  - MAPE는 개선되지만 p95 또는 MdAPE 악화가 큼

## 9. 후속 판단

- 안정적으로 0.55~0.60이 선택될 경우
  - Warm 서비스 후보를 `fallback_numeric + PP-V8` 결합으로 갱신 검토
  - 최종 후보명 예시: `warm_pp_svc6_fallback_ppv8_wfallback_0.60`
- 0.70~0.75가 안정적으로 선택될 경우
  - 기존 PP-SVC3 70:30 계열 유지
  - PP-SVC5의 0.55~0.60 test 개선은 우연 가능성으로 처리
- weight가 불안정할 경우
  - 기존 PP-SVC3 후보 유지
  - 결합 비율 재조정은 서비스 반영 보류

