# Track6 후처리 실험 최종 의사결정 보고서

- 작성일: 2026-06-02
- 기준 문서: `docs/track6/experiments/postprocessing_experiment_matrix.md`
- 실행 현황: `PRE-PP`부터 `PP-I`까지 실행 완료
- 기준 데이터: `data/track6_split` 고정 train / validation / test
- 선택 원칙: validation에서 보정값, 가중치, 라우팅 기준을 확정하고 test는 재현성 확인으로만 사용

## 1. 최종 결론

| 구분 | 최종 판단 | 이유 | 운영 적용 방식 |
|---|---|---|---|
| Warm 점 예측 | `PP-D4 warm_pp_d4_integrated`를 1차 운영 후보로 권장 | test MdAPE가 `0.2274 -> 0.1760`으로 가장 강하게 개선되고 MAPE, p95도 함께 개선 | Warm Huber 기준 예측에 PP-L8 순차 후보를 중심으로 결합 |
| Warm 검증 기준 후보 | `PP-E1 warm_pp_e1_routing` 유지 | validation MdAPE `0.1644`로 Warm 후보 중 1위 | 작가 학습 이력 구간별 라우팅 후보로 보조 관리 |
| Cold 점 예측 | baseline LightGBM 유지 | validation 보정 후보는 강하지만 test MdAPE에서는 baseline LightGBM이 `0.4909`로 가장 안정적 | 단일 가격은 참고값으로 제공 |
| Cold 보정 후보 | `PP-D3`, `PP-A7`, `PP-J4`는 보조 정책으로 유지 | validation MdAPE와 p95는 개선되지만 test MdAPE 재현성이 약함 | 큰 오차 위험, 신뢰도, 가격 범위 표시용으로 사용 |
| 가격 범위/신뢰도 | Warm은 적용 가능, Cold는 보수화 필요 | Warm tiered range test 포함률 `0.7974`, Cold는 `0.7115`로 부족 | Warm은 가격 범위 제공, Cold는 더 넓은 범위와 낮은 신뢰도 문구 필요 |
| 외부/검색 데이터 | 현재 보류 | 신규 외부 데이터와 검색/소셜 컬럼이 로컬 split에 없음 | 컬럼 수집 후 `PP-G`, `PP-H` 재실행 |

## 2. 왜 이렇게 판단했는가

- Warm은 같은 작가가 학습 데이터에 존재하므로 작가 기준선과 작품 크기 정보가 가격 예측의 핵심이다.
- Warm Huber baseline은 이미 안정적이지만, 단순 residual 보정보다는 Quantile, Huber, CatBoost residual을 순차적으로 쓰거나 작가 이력별로 라우팅할 때 개선폭이 컸다.
- Cold는 학습 데이터에 없는 작가를 예측하므로 작가명 기준선을 쓸 수 없다.
- Cold에서는 CatBoost leaf 보정, 계층형 보정, tail blend가 validation에서 크게 개선됐지만 test에서는 점 예측 정확도가 안정적으로 재현되지 않았다.
- 따라서 Cold는 보정 모델을 바로 주 예측값으로 쓰기보다, 위험 구간 판단과 가격 범위 표시의 보조 근거로 쓰는 것이 안전하다.

## 3. Warm 후보 비교

| 후보 | 실험 | validation MdAPE | validation MAPE | validation p95 | test MdAPE | test MAPE | test p95 | 판단 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline Huber | 기준 | `0.2126` | `0.4167` | `1.3194` | `0.2274` | `0.4952` | `2.0130` | 기준선 |
| PP-L8 순차 모델 | Quantile -> Huber -> CatBoost residual | `0.1808` | `0.3152` | `0.9341` | `0.1777` | `0.3383` | `1.1047` | 강한 후보 |
| PP-D4 통합 결합 | Huber + PP-L8 중심 weighted blend | `0.1687` | `0.3053` | `0.9460` | `0.1760` | `0.3293` | `1.1248` | 1차 권장 |
| PP-E1 라우팅 | 작가 이력 구간별 후보 선택 | `0.1644` | `0.2887` | `0.8346` | `0.1856` | `0.3579` | `1.3398` | 검증 기준 1위 |
| PP-K3 유사 작품 fallback | 비슷한 작품 가격 fallback | `0.1996` | `0.3672` | `1.1230` | `0.2042` | `0.3499` | 확인 필요 | 보조 후보 |

### Warm 권장안

- 운영 1차 후보는 `PP-D4 warm_pp_d4_integrated`로 둔다.
- 이유는 validation 성능도 높고, test에서도 MdAPE와 MAPE가 가장 안정적으로 개선됐기 때문이다.
- validation 원칙만 엄격하게 적용해야 하는 보고 체계에서는 `PP-E1 warm_pp_e1_routing`을 선택 후보로 함께 제시한다.
- 두 후보의 차이는 다음과 같다.
  - `PP-E1`: 작가 학습 이력에 따라 모델/보정값을 다르게 쓰는 방식이다. validation에서는 가장 좋다.
  - `PP-D4`: Huber와 PP-L8 순차 모델을 결합하는 방식이다. test에서 가장 좋고 구조가 비교적 단순하다.

## 4. Cold 후보 비교

| 후보 | 실험 | validation MdAPE | validation MAPE | validation p95 | test MdAPE | test MAPE | test p95 | 판단 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline LightGBM | 기준 | `0.3851` | `0.7169` | `2.0250` | `0.4909` | `1.4131` | `4.8212` | 점 예측 기준 유지 |
| PP-D3 tail blend | CatBoost/LightGBM 보정 후보 결합 | `0.3370` | `0.5862` | `1.8242` | `0.4966` | `1.4187` | `4.1672` | 위험 방어 후보 |
| PP-J4 CatBoost leaf | leaf coverage 보정 | `0.3440` | `0.5876` | `1.8586` | `0.4979` | `1.4624` | `4.6329` | 보조 후보 |
| PP-A7 계층형 보정 | segment fallback 보정 | `0.3567` | `0.5662` | `1.6593` | `0.5093` | `1.4160` | `3.6424` | p95 방어 후보 |
| PP-I2 CatBoost 설정 튜닝 | depth/lr/l2 grid | baseline 유지 | baseline 유지 | baseline 유지 | `0.4772` | 확인 필요 | `5.3276` | MdAPE만 개선, p95 악화 |

### Cold 권장안

- Cold 점 예측은 baseline LightGBM을 유지한다.
- CatBoost leaf 보정과 계층형 보정은 validation에서는 강하지만 test MdAPE가 baseline을 넘지 못했다.
- 단, `PP-D3`, `PP-A7`, `PP-J4`는 큰 오차 위험을 알려주는 보조 정책으로 가치가 있다.
- 특히 `PP-A7`은 test p95를 `4.8212 -> 3.6424`로 낮춰, 단일 가격 정확도보다 위험 표시에서 의미가 크다.

## 5. 모델별 가격 예측 로직과 후처리 의미

### Warm Huber

```text
pred_log_price = intercept + sum(beta_j * transformed_feature_j)
pred_price = exp(pred_log_price)
```

- Huber는 선형 모델이다.
- 각 피처는 로그 가격에 더해지는 값으로 작동한다.
- 큰 오차는 일반 선형회귀처럼 계속 크게 벌주지 않고, 일정 기준을 넘으면 영향력을 줄인다.
- 그래서 미술품처럼 고가 이상치가 많은 데이터에서 작가, 크기, 재료의 기본 방향을 안정적으로 잡는 데 유리하다.

```text
residual_log = actual_log_price - pred_log_price
corrected_pred_log = pred_log_price + correction_value
corrected_pred_price = exp(corrected_pred_log)
```

- Warm에서 단순 전체 보정보다 세부 보정이 필요한 이유는 오차가 전체 평균 하나로 설명되지 않기 때문이다.
- 작가 이력, 예측 가격대, 크기 구간에 따라 반복 오차가 달라진다.
- 따라서 `PP-E1`, `PP-D4`, `PP-L8`처럼 작가 이력, 불확실성, residual을 나누어 다루는 방식이 더 적합했다.

### Cold CatBoost

```text
pred_log_price = base_value + sum(each_tree_leaf_value)
pred_price = exp(pred_log_price)
```

- CatBoost는 대칭 트리 구조를 사용한다.
- 같은 깊이의 트리에서 동일한 기준으로 데이터를 반복 분기하므로, 피처 하나의 독립 영향보다 피처 조합이 중요하다.
- 예를 들어 크기, 2D/3D 여부, 재료/지지체 조합이 함께 leaf를 만들고, 해당 leaf의 평균적인 가격 보정값이 예측에 더해진다.
- 그래서 CatBoost 보정은 전체 중앙값 보정보다 leaf 또는 segment별 residual 중앙값 보정이 더 적합하다.

```text
segment_residual = actual_log_price - pred_log_price
segment_correction = median(segment_residual values in same leaf_or_segment)
corrected_pred_log = pred_log_price + segment_correction
```

- 여기서 median은 같은 구간의 residual을 작은 값부터 큰 값까지 정렬했을 때 가운데 값이다.
- 평균보다 극단값에 덜 흔들리므로 가격 이상치가 많은 데이터에서 보정값으로 쓰기 적합하다.
- 다만 Cold에서는 validation에 맞춘 leaf 보정이 test에서 그대로 재현되지 않았다.
- 따라서 CatBoost 보정은 주 예측값보다 위험 구간과 신뢰도 산정에 먼저 활용하는 것이 맞다.

### Cold LightGBM

- LightGBM도 트리 모델이지만 CatBoost와 달리 leaf-wise 방식으로 손실을 많이 줄이는 leaf를 우선 확장한다.
- 복잡한 비선형 패턴을 잘 잡지만, 특정 구간에 과하게 맞을 수 있다.
- 이번 실험에서는 Cold 원 모델 기준으로 LightGBM이 CatBoost보다 test 점 예측이 안정적이었다.
- 따라서 Cold 점 예측은 LightGBM을 유지하고, CatBoost 계열 보정은 보조 위험 판단으로 분리한다.

## 6. 피처 영향도 관점의 해석

| 모델 | 핵심 피처/구간 | 왜 중요하게 작동했는가 | 후처리 연결 |
|---|---|---|---|
| Warm Huber | 작가 기준선 | Warm은 기존 작가가 학습 데이터에 있으므로 작가별 과거 가격대가 절편 보정처럼 작동 | 작가 이력 구간별 라우팅 |
| Warm Huber | 작품 크기 | 같은 작가라도 크기에 따라 가격대가 달라지고, 선형 모델에서 가장 안정적인 공통 축 | size bucket, tail segment 보정 |
| Warm Huber | 재료/지지체 | 같은 크기라도 시장에서 인식되는 작품 유형이 다름 | medium/support fallback 보정 |
| Cold CatBoost | leaf segment | 작가명 없이 크기, 재료, 2D/3D 조합으로 가격 구간을 나눔 | leaf/segment residual 보정 |
| Cold LightGBM | 예측 가격대/tail | leaf-wise 구조가 고위험 구간을 잘 분리하지만 일부 tail에서 흔들림 | tail blend, p95 방어 정책 |
| Quantile 보조 모델 | q10/q50/q90 폭 | 예측 불확실성이 큰 작품과 작은 작품을 구분 | 가격 범위와 신뢰도 등급 |

## 7. 가격 범위와 신뢰도 정책

| 정책 | validation 결과 | test 결과 | 판단 |
|---|---|---|---|
| Warm 80% range | 포함률 `0.7996`, 중앙 범위비 `3.32x` | 포함률 `0.7578` | 적용 가능하나 약간 보수화 필요 |
| Warm tiered range | 중앙 범위비 `2.8457x` | 포함률 `0.7974` | 권장 |
| Cold 80% range | 포함률 `0.7999`, 중앙 범위비 `4.94x` | 포함률 `0.6799` | 부족 |
| Cold tiered range | 중앙 범위비 `4.9696x` | 포함률 `0.7115` | 더 넓은 범위 필요 |
| Quantile confidence grade | 저신뢰 구간 오차가 높게 분리됨 | Warm/Cold 모두 위험 구간 분리 가능 | 신뢰도 등급 입력값으로 사용 |

## 8. 채택, 보류, 제외 목록

| 분류 | 실험 | 판단 | 사유 |
|---|---|---|---|
| 채택 후보 | `PP-D4` | Warm 1차 운영 후보 | validation/test 모두 강하고 test MdAPE 1위 |
| 채택 후보 | `PP-F4` | Warm 가격 범위 정책 | test 포함률이 목표에 근접 |
| 검증 기준 후보 | `PP-E1` | Warm 라우팅 후보 | validation 1위, 작가 이력 설명 가능 |
| 보조 후보 | `PP-L8` | Warm 순차 모델 | Quantile, Huber, CatBoost 장점을 연결 |
| 보조 후보 | `PP-K3` | Warm fallback | 유사 작품 기반 보조 설명 가능 |
| 유지 | baseline LightGBM | Cold 점 예측 기준 | test MdAPE 기준 가장 안정적 |
| 보조 후보 | `PP-D3`, `PP-A7`, `PP-J4` | Cold 위험/신뢰도 정책 | p95, 위험 구간 방어에 의미 |
| 보류 | `PP-B` residual model | 단독 채택 보류 | validation 개선 대비 test 재현성 부족 |
| 보류 | `PP-C` recalibration | 단독 채택 보류 | validation 과적합 위험 |
| 보류 | `PP-G`, `PP-H` | 데이터 수집 후 재실행 | 신규 외부/검색 데이터 없음 |

## 9. 최종 운영 제안

### Warm

- 기본 예측값은 `PP-D4 warm_pp_d4_integrated`를 사용한다.
- 보고 기준상 validation 원칙을 더 강하게 적용해야 하면 `PP-E1 warm_pp_e1_routing`을 병렬 후보로 유지한다.
- 사용자에게는 점 예측 가격과 함께 Warm tiered range를 제공한다.
- 저이력 작가, 극단 크기, 높은 quantile width 구간은 신뢰도 문구를 낮춘다.

### Cold

- 기본 점 예측값은 baseline LightGBM을 사용한다.
- CatBoost leaf 보정, 계층형 보정, tail blend는 점 예측을 바꾸는 목적보다 위험 구간과 가격 범위를 조정하는 데 사용한다.
- Cold는 단일 가격을 확정값처럼 보여주지 않는다.
- 가격 범위는 Warm보다 넓게 잡고, 낮은 신뢰도 안내를 기본 정책으로 둔다.

## 10. 후속 작업

| 우선순위 | 작업 | 목적 |
|---:|---|---|
| 1 | Warm `PP-D4`와 `PP-E1` 최종 비교 리뷰 | 운영 후보를 하나로 고정 |
| 2 | Cold baseline LightGBM + 위험 정책 설계 | 점 예측과 신뢰도 표시 분리 |
| 3 | Cold 가격 범위 보수화 실험 | test 포함률을 80% 근처로 올림 |
| 4 | 신규 외부/검색 데이터 수집 | `PP-G`, `PP-H` 재실행 가능하게 함 |
| 5 | 최종 artifact 업데이트 | 운영 코드와 리포트 기준 후보 일치 |

## 11. 참고 산출물

- 실행 진행 현황: `experiments/track6/postprocessing_execution_progress.md`
- 실험 리스트: `docs/track6/experiments/postprocessing_experiment_matrix.md`
- 모델/피처 해석 보고서: `docs/track6/experiments/supervisor_model_feature_postprocessing_report.md`
- Warm PP-D4: `experiments/track6/PP-D4_warm_three_model_blend/reports/result_report.md`
- Warm PP-E1: `experiments/track6/PP-E1_warm_low_history_routing/reports/result_report.md`
- Warm PP-L8: `experiments/track6/PP-L8_quantile_huber_catboost_sequential/reports/result_report.md`
- 최종 통합 검증: `experiments/track6/PP-I5_final_integrated_candidate_validation/reports/result_report.md`
