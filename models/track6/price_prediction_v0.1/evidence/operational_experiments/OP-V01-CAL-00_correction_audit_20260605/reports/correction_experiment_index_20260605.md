# v0.1 보정 실험 정리 및 후속 방향

## 1. 정리 목적

- 오늘 기존 데이터와 0604 신규 데이터로 확인한 보정 실험 내용을 v0.1 기준으로 정리한다.
- 현재 v0.1 기본 모델을 바로 교체해도 되는 보정 후보가 있는지 판단한다.
- 후속 보정 실험은 v0.1 폴더 안에서 별도 트랙으로 관리한다.

## 2. 현재 v0.1 기준 모델

| 구분 | 현재 기준 |
| --- | --- |
| Warm | 유사 작품 기반 가격 피처와 오차 안정화 후보를 결합한 Warm 후보 |
| Cold | LightGBM Quantile 기반 Cold 후보와 검색/작가 메타 기반 보정 후보 |
| 운영 예측 기본값 | `models/track6/price_prediction_v0.1/operational` 산출물 기준 |
| 신규 0604 데이터 성격 | 운영 유입 데이터 시뮬레이션 및 라벨 정합성 점검용 |

## 3. 오늘 확인한 0604 신규 데이터 분석

### 3.1 정확/근접 적중 분석

- 원본 위치: `experiments/track6/OP-0604_exact_match_analysis`
- 결과 보고서: `experiments/track6/OP-0604_exact_match_analysis/reports/result_report.md`

| 항목 | 결과 |
| --- | --- |
| 원화 기준 완전 일치 | 0건 |
| 1원 반올림 기준 완전 일치 | 0건 |
| APE 1% 이하 | 20건 / 837건 |
| APE 3% 이하 | 57건 / 837건 |
| APE 5% 이하 | 98건 / 837건 |
| 가장 근접한 사례 | 실제 993,600원, 예측 993,212원, 오차 388원 |

### 3.2 오차 원인 분석

- 원본 위치: `experiments/track6/OP-0604_comprehensive_error_analysis`
- 결과 보고서: `experiments/track6/OP-0604_comprehensive_error_analysis/reports/comprehensive_error_report.md`

| 구분 | 결과 |
| --- | --- |
| 전체 라벨 기준 MdAPE | 0.2342 |
| 전체 라벨 기준 MAPE | 14.2852 |
| 50달러 미만 라벨 제외 MdAPE | 0.2298 |
| 50달러 미만 라벨 제외 MAPE | 0.3359 |
| 50달러 미만 검수 대상 | 8건 |
| 50달러 이상 과대 예측 3배 초과 | 4건 |
| 50달러 이상 과소 예측 1/3 미만 | 58건 |
| 10만 달러 이상 고가 작품 | 8건 |

### 3.3 해석

- 0604 데이터의 MAPE가 크게 튄 주된 이유는 실제 가격이 매우 낮은 라벨 때문이다.
- 실제가 1달러, 10달러, 20달러처럼 낮으면 예측 가격이 조금만 높아도 퍼센트 오차가 폭발한다.
- 50달러 미만 라벨을 제외하면 MAPE가 14.2852에서 0.3359로 크게 내려간다.
- 따라서 0604 데이터는 모델 보정 전에 라벨 검수 기준을 먼저 적용해야 한다.
- 고가 작품은 모델이 가격 프리미엄을 충분히 올리지 못하는 과소 예측 문제가 남아 있다.

## 4. 오늘 확인한 기존 데이터 보정 실험

### 4.1 기존 split 원인별 보정

- 원본 위치: `experiments/track6/OP-0605_existing_split_error_cause_customization`
- 결과 보고서: `experiments/track6/OP-0605_existing_split_error_cause_customization/reports/result_report.md`

| 구분 | 기준선 | 보정 후 최선 후보 | 해석 |
| --- | --- | --- | --- |
| Warm MdAPE | 0.1632 | 0.1620 | 개선 폭이 작음 |
| Warm MAPE | 0.2816 | 0.2810 | 개선 폭이 작음 |
| Cold MdAPE | 0.4247 | 0.4140 | 개선 가능성 있음 |
| Cold MAPE | 0.9910 | 1.0062 | 평균 오차는 악화 |
| Cold p95_APE | 3.3053 | 3.1125 | 큰 오차는 일부 완화 |

### 4.2 원인별 라우팅 보정

- 원본 위치: `experiments/track6/OP-0605_cause_aware_correction_routing`
- 결과 보고서: `experiments/track6/OP-0605_cause_aware_correction_routing/reports/result_report.md`

| 구분 | 기준선 MdAPE | 보정 후 MdAPE | 기준선 MAPE | 보정 후 MAPE | 기준선 p95_APE | 보정 후 p95_APE |
| --- | --- | --- | --- | --- | --- | --- |
| Warm | 0.1632 | 0.1563 | 0.2816 | 0.2789 | 0.9311 | 0.9253 |
| Cold | 0.4247 | 0.4174 | 0.9910 | 0.9659 | 3.3053 | 3.0306 |

### 4.3 반복 split 재검증

- 원본 위치: `experiments/track6/OP-0605_cause_aware_correction_routing`
- 결과 보고서: `experiments/track6/OP-0605_cause_aware_correction_routing/reports/repeated_split_revalidation_report.md`

| 구분 | 반복 검증 결과 |
| --- | --- |
| Warm | 평균 개선 폭이 매우 작고 일부 seed에서 기준선보다 악화 |
| Cold row 반복 | MdAPE, MAPE, p95_APE가 안정적으로 개선 |
| Cold artist 반복 | p95_APE와 MAPE는 일부 개선, MdAPE는 seed별로 흔들림 |

### 4.4 작가 단위 재학습 검증

- 원본 위치: `experiments/track6/OP-0605_artist_level_model_retrain_revalidation`
- 결과 보고서: `experiments/track6/OP-0605_artist_level_model_retrain_revalidation/reports/artist_level_model_retrain_revalidation_report.md`

| 구분 | 기준선 | 원인별 보정 후 | 판단 |
| --- | --- | --- | --- |
| Warm MdAPE 평균 | 0.1716 | 0.1727 | 악화 |
| Warm MAPE 평균 | 0.3582 | 0.3602 | 악화 |
| Cold MdAPE 평균 | 0.3276 | 0.3290 | 악화 |
| Cold MAPE 평균 | 0.6301 | 0.6316 | 악화 |
| Cold p95_APE 평균 | 2.0126 | 2.0025 | 소폭 개선 |

## 5. 현재 판단

- 오늘 확인한 원인별 보정 후보는 v0.1 기본 점가격 모델로 바로 승격하지 않는다.
- Warm은 기존 데이터에서 보정 효과가 작고 재학습 반복 검증에서 개선이 유지되지 않았다.
- Cold는 고정 split에서는 개선 신호가 있었지만, 작가 단위 재학습 검증에서는 MdAPE와 MAPE가 좋아지지 않았다.
- 추가 결합 비율 재검증에서는 historical test 성능 개선이 확인됐지만, 0604 외부 확인에서는 강한 유사 작품 기반 결합이 불안정했다.
- 보정은 점가격 교체보다 가격 범위, 신뢰도, 고위험 구간 표시부터 적용하는 것이 더 안전하다.
- 0604 신규 데이터는 라벨 검수 전까지 보정값 학습용으로 쓰지 않는다.
- `fixed_125_width`는 v0.1 기본 운영 정책에 아직 반영하지 않는다.
- 현재 상태는 “v0.1 기준 범위/신뢰도 보정 후보”이며, 별도 API/프론트 테스트 후 반영 여부를 판단한다.

## 6. 후속 보정 실험 방향

- 상세 실행 계획: `next_correction_experiment_plan.md`

### 6.1 라벨 검수 기반 평가 분리

- 실행 상태: 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-01_label_qc_eval_split`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-01_label_qc_eval_split/reports/result_report.md`
- 목적: 0604 신규 데이터에서 낮은 실제 가격 라벨이 MAPE를 왜곡하는지 분리 확인
- 방식: 50달러 미만, 10만 달러 이상, 통화/단위 의심 라벨을 별도 그룹으로 분리
- 결과물: 전체 지표와 검수 제외 지표를 동시에 제공
- 후속 작업: 운영 평가 화면에서도 검수 필요 라벨을 별도 표시
- 확인 결과:
  - 전체 숫자 라벨 837건 기준 MAPE는 `14.2852`
  - 50달러 미만 8건을 제외하면 MAPE는 `0.3359`
  - 50달러 이상 10만 달러 미만 핵심 구간 MAPE는 `0.3308`
  - 10만 달러 이상 고가 꼬리 구간은 범위 포함률이 `0.0000`으로 고가 과소 예측 방어가 필요

### 6.2 저가/소형 작품 과대 예측 방어

- 실행 상태: 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-02_low_small_overprediction_guard`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-02_low_small_overprediction_guard/reports/result_report.md`
- 목적: 실제 가격이 낮은 작품을 과하게 예측하는 문제 완화
- 방식: 면적, 예측 가격, 유사 작품 표본 수, 가격 범위 폭을 기준으로 보정 후보 생성
- 주의: 실제 정답 가격은 추론 시점에 없으므로 보정 조건에 사용하지 않음
- 채택 기준: MAPE와 over 3x 건수를 줄이되 MdAPE를 악화시키지 않아야 함
- 확인 결과:
  - 기준선 test MdAPE는 `0.1632`, MAPE는 `0.2816`, p95_APE는 `0.9311`
  - 전역 하향 보정 후보는 test MdAPE `0.1618`, MAPE `0.2803`, p95_APE `0.9281`
  - 다만 over 3x 건수는 `6건`에서 줄지 않음
  - 점가격 기본 보정으로 바로 채택하지 않고, 가격 범위/신뢰도 보정 후보로만 보류

### 6.3 고가 작품 과소 예측 방어

- 실행 상태: 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-03_high_value_underprediction_guard`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-03_high_value_underprediction_guard/reports/result_report.md`
- 목적: 고가 작가나 대형 작품에서 가격을 낮게 잡는 문제 완화
- 방식: 작가 가격 기준선, 가격 범위 상단, 검색/전시/갤러리 신호를 활용
- 우선 적용: 점가격을 무리하게 올리기보다 가격 범위 상단과 신뢰도 표시를 먼저 조정
- 채택 기준: under 1/3x 건수를 줄이고 p95_APE를 개선해야 함
- 확인 결과:
  - 기준선 test MdAPE는 `0.1632`, MAPE는 `0.2816`, p95_APE는 `0.9311`
  - 최선 후보는 under 1/3x를 `7건`에서 `6건`으로 줄임
  - 다만 MAPE는 `0.2853`, p95_APE는 `0.9332`로 악화
  - over 3x도 `6건`에서 `7건`으로 증가
  - 점가격 상향 보정으로 채택하지 않고 가격 범위/신뢰도 보정 후보로 이동

### 6.4 위험도 기반 가격 범위 보정

- 실행 상태: 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-04_risk_adjusted_range_confidence`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-04_risk_adjusted_range_confidence/reports/result_report.md`
- 목적: 점가격이 틀릴 가능성이 큰 샘플에서 화면 범위를 넓혀 과신을 줄임
- 방식: 예측 불확실성 폭, 표본 수 부족, 검색 품질 낮음, 작가 이력 부족을 위험 신호로 사용
- 결과물: 점가격 유지 후보와 범위 확장 후보를 분리 평가
- 채택 기준: 범위 포함률이 올라가고 과도하게 넓은 범위가 늘지 않아야 함
- 확인 결과:
  - 기준 범위 포함률은 `0.9226`
  - `fixed_125_width` 후보의 범위 포함률은 `0.9588`
  - 기준 median range ratio는 `4.0492`
  - `fixed_125_width` median range ratio는 `5.7440`
  - 점가격은 유지하고, 표시 범위와 신뢰도 보정 후보로 유지 가능
  - v0.1 기본 운영 정책에는 아직 미반영
  - `fixed_150_width`는 포함률 `0.9753`이지만 p90 range ratio가 너무 커 서비스 기본 후보에서는 제외

### 6.5 모델 재학습 포함 보정 검증

- 실행 상태: 범위 정책 반복 검증 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-05_range_policy_revalidation`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-05_range_policy_revalidation/reports/result_report.md`
- 목적: 고정 split에서만 좋아지는 보정 후보를 걸러냄
- 방식: row 반복, artist 반복, artist-level 재학습 검증 순서로 진행
- Warm 판단 기준: MdAPE와 MAPE가 동시에 개선되어야 함
- Cold 판단 기준: 작가 단위 재학습 검증에서 개선이 유지되어야 함
- 확인 결과:
  - 대상 후보는 점가격 보정이 아니라 `fixed_125_width` 범위 정책
  - validation 범위 포함률은 `0.9480 -> 0.9595`
  - test 범위 포함률은 `0.9226 -> 0.9588`
  - row bootstrap 100회 양수 개선 비율은 `1.0000`
  - artist bootstrap 100회 양수 개선 비율은 `1.0000`
  - 범위/신뢰도 보정 후보로 유지 가능
  - v0.1 기본 운영 정책에는 아직 미반영
  - 단, 모델 재학습 검증이 아니라 범위 표시 정책 검증으로 해석해야 함

### 6.6 유사 작품 기반 예측값 결합 비율 재검증

- 실행 상태: 완료
- 실행 위치: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-06_adaptive_blend_reweighting`
- 결과 보고서: `models/track6/price_prediction_v0.1/evidence/operational_experiments/OP-V01-CAL-06_adaptive_blend_reweighting/reports/result_report.md`
- 목적: 유사 작품 기반 예측값과 PP-V8 운영 후보의 결합 비율을 다시 조정하면 점가격 성능이 좋아지는지 확인
- 방식: historical validation에서 후보를 선택하고, historical test와 0604 신규 라벨에서 별도 확인
- 확인 결과:
  - historical test 기준 PP-V8 MAPE는 `0.2816`, MdAPE는 `0.1632`, p95_APE는 `0.9311`
  - historical test에서 `svc 60% + PP-V8 40%` 후보는 MAPE `0.2717`, MdAPE `0.1362`, p95_APE `0.8329`
  - 0604 50달러 미만 제외 기준 PP-V8 MAPE는 `0.3359`, MdAPE는 `0.2298`, p95_APE는 `0.9273`
  - 0604 50달러 미만 제외에서 `svc 20% + PP-V8 80%` 후보는 MAPE `0.3330`, MdAPE `0.2385`, p95_APE `0.9122`
- 판단:
  - historical split에서는 결합 비율 조정으로 성능 개선 가능성이 있다.
  - 0604에서는 강한 svc 결합이 성능을 악화시키므로 전역 결합을 v0.1 기본 점가격으로 반영하지 않는다.
  - 낮은 비율 결합 또는 조건부 결합만 별도 API 후보로 비교하는 것이 안전하다.

## 7. 운영 반영 전 확인 단계

- `fixed_125_width`는 실험 후보로만 유지한다.
- v0.1 운영 예측 기본값은 변경하지 않는다.
- 별도 후보 출력 필드를 만들어 기존 점가격/범위와 후보 점가격/범위를 동시에 내려보낸다.
- 0604 신규 데이터는 라벨 검수 후 후보 범위가 실제 서비스 화면에서 과도하게 넓지 않은지 확인한다.
- 결합 비율 후보는 `svc 10~20% + PP-V8 80~90%` 같은 낮은 비율 후보부터 비교한다.
- 프론트 테스트에서는 사용자가 “범위가 넓어졌지만 납득 가능한지”를 확인한다.
- API/프론트 테스트 결과가 안정적이면 `v0.1.1` 또는 `v0.1-range-policy-test` 같은 별도 버전으로 승격한다.

## 8. 관리 결론

- 관리 차원에서 0.1v 폴더링은 필요하다.
- 다만 명칭은 현재 폴더와 맞춰 `v0.1`로 통일한다.
- 기존 실험 원본은 `experiments/track6`에 둔다.
- v0.1 패키지 안에는 운영 적용 관점의 요약, 판단, 후속 실험 계획을 남긴다.
- 후속 반영은 v0.1 기본값 수정이 아니라 별도 후보 테스트 패키지에서 진행한다.
