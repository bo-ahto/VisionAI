# Huber / Quantile / CatBoost 조합 성능 최적화 실험 계획

## 1. 실험 목적

- Huber, Quantile, CatBoost의 모델 특성을 조합해 가격 예측 성능을 개선한다.
- 단순히 MAPE만 낮추는 것이 아니라, 최종적으로 중요한 MdAPE를 유지하거나 개선하는 범위 안에서 MAPE와 큰 오차를 줄이는 것을 목표로 한다.
- 기존 Warm/Cold 기준 모델과 후처리 실험을 대체하는 것이 아니라, 후처리 후보가 한계에 도달했을 때 추가로 검증할 수 있는 모델 조합 실험으로 관리한다.

## 2. 핵심 판단 기준

- 1순위: MdAPE 유지 또는 개선
- 2순위: MAPE 감소
- 3순위: p95_APE 악화 방지
- 4순위: Warm/Cold 및 가격대별 성능 균형 유지

MAPE는 작품별 비율 오차의 평균값이므로 일부 큰 오차에 민감하다. 따라서 MAPE가 낮아져도 MdAPE가 악화되거나 p95_APE가 커지면 최종 후보로 바로 채택하지 않는다.

```text
APE = |실제 가격 - 예측 가격| / 실제 가격
MAPE = APE의 평균
MdAPE = APE의 중앙값
```

## 3. 모델별 역할 정의

| 모델 | 이 실험에서의 역할 | 기대 효과 | 주의점 |
|---|---|---|---|
| Huber | 안정적인 기본 가격선 생성 | 이상치 영향을 줄이고 Warm 기준 가격선을 안정적으로 생성 | 복잡한 피처 조합을 직접 나누는 능력은 제한적 |
| Quantile | 예측 하한/중앙/상한 산출 및 불확실성 지표 계산 | `q90_log - q10_log`와 `exp(q90_log - q10_log)`를 통해 불안정한 작품을 식별 | Quantile이 구간을 직접 출력하는 것은 아니며, 구간 경계는 validation에서 별도로 정의해야 함 |
| CatBoost | 조건 조합 학습 및 residual 보정 | 작가, 크기, 재료, 형태 조합별 반복 오차를 보정 | 깊은 트리나 세부 구간은 과적합 위험이 있음 |

## 4. 기본 가설

- Huber는 전체 가격 흐름을 안정적으로 잡는 데 유리하다.
- Quantile은 `q10_log`, `q50_log`, `q90_log`를 예측하고, 이 값으로 계산한 `quantile_width = q90_log - q10_log`와 `price_range_ratio = exp(quantile_width)`를 통해 예측 불확실성을 수치화하는 데 유리하다.
- CatBoost는 대칭 트리 구조를 통해 작가 x 크기, 재료 x 형태, 2D/3D x 크기 같은 조건 조합을 학습하는 데 유리하다.
- 따라서 Huber를 기본 가격선으로 두고, Quantile 예측값에서 계산한 `quantile_width`를 기준으로 validation에서 위험 구간을 정의한 뒤, CatBoost를 보정 또는 대체 모델로 사용하는 조합이 MAPE와 p95_APE를 낮출 가능성이 있다.

## 5. 실험 전제

- 데이터 분할은 기존 Track6 고정 train/validation/test 기준을 사용한다.
- 보정값, 가중치, 라우팅 기준은 validation에서만 결정한다.
- test는 최종 후보가 정해진 뒤 1회 확인용으로만 사용한다.
- Warm과 Cold는 분리해서 평가한다.
- 가격대별 저가/중가/고가 구간 MAPE를 함께 확인한다.
- Huber, Quantile, CatBoost가 사용하는 피처셋은 기존 기준 피처셋을 우선 사용한다.
- Quantile 모델은 low / mid / high 같은 구간명을 직접 출력하지 않는다. Quantile 모델은 `q10_log`, `q50_log`, `q90_log`를 출력하고, 구간 경계는 validation의 `quantile_width` 분포 또는 원가격 배수로 환산한 `price_range_ratio` 기준으로 별도 정의한다.

## 6. 논문용 실험 통제 기준

PP-L 실험은 후보가 많기 때문에 결과가 우연히 좋아질 위험이 있다. 논문 또는 외부 검증 수준의 데이터로 사용하려면 아래 기준을 사전에 고정한다.

### 6.1 검증 가설

| 가설 ID | 가설 | 검증 방법 | 채택 조건 |
|---|---|---|---|
| H1 | Quantile width 또는 price range ratio가 큰 구간은 실제 APE가 높다. | 구간별 APE/MAPE/p95_APE 비교, rank correlation 확인 | high 구간의 MAPE 또는 p95_APE가 low 구간보다 높음 |
| H2 | Quantile 구간별 Huber 재학습은 전체 Huber보다 중심 오차를 안정화한다. | 전체 Huber vs PP-L7-H 비교 | MdAPE 유지 또는 개선, stable 구간 악화 없음 |
| H3 | Quantile 구간별 CatBoost 재학습은 risk 구간의 큰 오차를 줄인다. | 전체 CatBoost vs PP-L7-CB 비교 | risk 구간 MAPE 또는 p95_APE 개선 |
| H4 | Quantile → Huber → CatBoost 순차 구조는 단순 결합보다 안정적이다. | PP-L8 vs 단순 가중 앙상블 비교 | MdAPE 유지, MAPE/p95_APE 개선 |
| H5 | Huber → Quantile residual → CatBoost 구조는 Huber residual을 더 잘 보정한다. | PP-L9 vs Huber + CatBoost residual 비교 | MAPE/p95_APE 개선, test 재현 |

### 6.2 필수 baseline 비교군

PP-L 결과는 아래 baseline과 모두 비교한다. 특정 실험만 단독으로 좋아졌다고 채택하지 않는다.

| baseline ID | 비교군 | 목적 |
|---|---|---|
| B0 | Warm Huber 단독 | Warm 기준선 |
| B1 | Cold CatBoost 단독 | Cold 기준선 |
| B2 | Quantile q50 단독 | Quantile 중앙 예측 단독 성능 확인 |
| B3 | 기준 모델 + 전체 median residual 보정 | 가장 단순한 보정 대비 효과 확인 |
| B4 | Huber + CatBoost residual | Quantile 없이 residual 보정만으로 충분한지 확인 |
| B5 | Huber + Quantile residual q50 | CatBoost 없이 Quantile residual만으로 충분한지 확인 |
| B6 | PP-L8 Quantile → Huber → CatBoost | Quantile 선행 진단 구조 |
| B7 | PP-L9 Huber → Quantile residual → CatBoost | Huber 선행 residual 구조 |
| B8 | Huber / Quantile / CatBoost 단순 가중 앙상블 | 복잡한 순차 구조 대비 단순 결합 기준 |

### 6.3 데이터 분할과 누수 방지

- train은 모델 학습에만 사용한다.
- validation은 구간 경계, 보정값, 가중치, 라우팅 기준 선택에만 사용한다.
- test는 최종 선택된 후보를 마지막으로 한 번 확인할 때만 사용한다.
- residual을 target으로 다시 학습하는 실험은 반드시 OOF 예측을 사용한다.
- 같은 샘플을 학습한 모델의 예측값으로 residual을 만들고 다시 학습하지 않는다.
- 구간 경계는 validation에서 정한 값을 test에 그대로 적용한다.

```text
OOF residual:
  train fold별로 자기 자신을 보지 않은 모델의 pred_log 생성
  residual_log = actual_log - oof_pred_log
  residual model은 이 residual_log만 학습
```

### 6.4 지표 우선순위

| 구분 | 지표 | 역할 |
|---|---|---|
| Primary | MdAPE | 대표 중앙 성능. 최우선 판단 기준 |
| Secondary | MAPE | 평균 비율 오차. 큰 오차와 저가 구간 영향 확인 |
| Constraint | p95_APE | 큰 오차 악화 방지 |
| Support | RMSE_log, Within_30, Within_50 | 보조 안정성 확인 |
| Slice | Warm/Cold, 가격대, stable/caution/risk | 구간별 성능 균형 확인 |

채택 기준은 다음 순서로 적용한다.

```text
1. MdAPE 유지 또는 개선
2. MAPE 개선
3. p95_APE 악화 없음
4. stable 구간 악화 없음
5. validation/test 방향 일치
```

### 6.5 통계 검증

단일 점수 개선만으로 결론을 내리지 않는다. 최종 후보는 baseline 대비 sample-level APE 차이를 기준으로 통계 검증한다.

| 검증 | 목적 | 적용 대상 |
|---|---|---|
| Paired bootstrap 95% CI | 개선폭 신뢰구간 확인 | MdAPE, MAPE, p95_APE |
| Wilcoxon signed-rank test | sample별 APE 개선 방향 확인 | baseline vs 최종 후보 |
| Seed 반복 평균/표준편차 | 학습 안정성 확인 | CatBoost, Quantile, residual 모델 |
| 구간별 bootstrap | stable/caution/risk별 개선 재현성 확인 | PP-L7~PP-L9 |

예시:

```text
delta_APE_i = APE_baseline_i - APE_candidate_i

delta_APE가 양수이면 candidate가 해당 샘플에서 개선된 것
bootstrap 95% CI가 0보다 크면 개선이 안정적이라고 판단
```

### 6.6 Multiple comparison 통제

PP-L은 후보가 많으므로 여러 실험 중 우연히 좋은 결과를 선택할 위험이 있다.

- 실험 실행 전 primary metric과 채택 기준을 고정한다.
- validation에서 가장 좋은 후보만 test로 보낸다.
- test 결과를 보고 후보나 구간 기준을 다시 바꾸지 않는다.
- PP-L7의 구간 기준은 33/66, 50/80, 70/90, 1.5/2.5배 후보를 비교하되, 최종 선택 기준은 validation에서만 확정한다.
- 최종 보고에는 개선된 실험뿐 아니라 보류/실패한 후보도 함께 기록한다.

### 6.7 구간 기준 민감도 분석

Quantile 구간 기준이 임의적이라는 지적을 피하기 위해 아래 기준을 비교한다.

| 기준 | 목적 |
|---|---|
| 33% / 66% | 초기 탐색. 표본 수 균형 확보 |
| 50% / 80% | 상위 위험 구간을 더 좁게 잡는 기준 |
| 70% / 90% | 극단 risk 구간 방어 효과 확인 |
| price_range_ratio 1.5배 / 2.5배 | 원가격 배수 기준의 설명 가능성 확인 |

각 기준별로 아래를 기록한다.

- 구간별 sample 수
- 구간별 MdAPE
- 구간별 MAPE
- 구간별 p95_APE
- 구간별 실제 APE 분포
- 구간별 fallback 발생률

### 6.8 복잡도 대비 개선 검증

순차 구조는 운영 복잡도가 높으므로 성능 개선만 보지 않는다.

| 항목 | 기록 내용 |
|---|---|
| 모델 수 | 최종 예측에 필요한 모델 개수 |
| 학습 단계 수 | Quantile, Huber, CatBoost, residual 모델 단계 수 |
| 구간 수 | stable/caution/risk 또는 low/mid/high |
| fallback 수 | 표본 부족 fallback 발생 횟수 |
| 추론 비용 | 예측 시 필요한 모델 호출 수 |
| 해석 가능성 | 상사/운영자가 설명 가능한 수준인지 |
| 운영 난이도 | 실제 서비스 적용 난이도 |

복잡한 PP-L 후보가 단순 Huber, CatBoost, PP-K 조합보다 개선폭이 작으면 보류한다.

## 7. Quantile 구간 기준 해석

Quantile 모델은 직접 구간을 만들어주는 모델이 아니다. Quantile 모델은 각 작품에 대해 낮은 쪽 예측값, 중앙 예측값, 높은 쪽 예측값을 출력한다.

```text
q10_log = 낮은 쪽 10% 분위 예측 로그 가격
q50_log = 중앙 50% 분위 예측 로그 가격
q90_log = 높은 쪽 90% 분위 예측 로그 가격
```

이 실험에서는 `q10_log`와 `q90_log`의 차이를 예측 불확실성 폭으로 사용한다.

```text
quantile_width = q90_log - q10_log
```

`quantile_width`는 로그 가격 기준 폭이다. 이 값을 원가격 기준으로 해석하려면 지수 변환을 적용한다.

```text
price_range_ratio = exp(quantile_width)
```

`price_range_ratio`는 Quantile 모델이 해당 작품에 대해 예측한 q90 가격이 q10 가격보다 몇 배 높은지를 의미한다.

예를 들어:

```text
quantile_width = 0.7
price_range_ratio = exp(0.7) ≈ 2.0
```

이 경우 q90 예측 가격이 q10 예측 가격보다 약 2배 높다는 뜻이다. 즉, 모델이 해당 작품의 가능한 가격 범위를 넓게 보고 있으며 예측 불확실성이 높다고 해석한다.

### 7.1 33% / 66% 기준을 쓰는 이유

33% / 66% 기준은 최종 운영 기준이 아니라 초기 탐색 기준이다.

초기 탐색에서는 불확실성 낮음, 중간, 높음 구간을 비슷한 표본 수로 나누어 각 구간의 오차 차이가 실제로 존재하는지 확인해야 한다. validation의 `quantile_width` 분포를 3등분하면 각 구간의 표본 수를 비교적 균형 있게 확보할 수 있다.

```text
low uncertainty:
  quantile_width <= validation 33% 분위값

mid uncertainty:
  validation 33% 분위값 < quantile_width <= validation 66% 분위값

high uncertainty:
  quantile_width > validation 66% 분위값
```

이 기준은 아래 질문을 확인하기 위한 1차 기준이다.

- Quantile width가 작은 작품은 실제 오차도 작은가?
- Quantile width가 큰 작품은 실제 MAPE 또는 p95_APE도 높은가?
- low / mid / high 구간별로 Huber와 CatBoost의 적합성이 달라지는가?

### 7.2 추가 비교 기준

33% / 66% 기준으로 구간별 성능 차이가 확인되면 더 실무적인 기준도 함께 비교한다.

```text
위험 중심 기준:
  50% / 80%
  70% / 90%

원가격 배수 기준:
  1.5배 / 2.5배
```

`price_range_ratio` 기준은 상사 보고나 운영 정책 설명에 더 적합하다.

```text
stable range:
  price_range_ratio <= 1.5배

caution range:
  1.5배 < price_range_ratio <= 2.5배

risk range:
  price_range_ratio > 2.5배
```

이 기준의 의미는 다음과 같다.

- 1.5배 이하: Quantile 모델이 예측 가격 범위를 비교적 좁게 보고 있으므로 안정 구간으로 본다.
- 1.5~2.5배: 예측 가격 범위가 어느 정도 벌어지므로 주의 구간으로 본다.
- 2.5배 초과: 예측 가격 범위가 크게 벌어지므로 위험 구간으로 본다.

단, 1.5배와 2.5배는 초기 가설이다. 최종 기준은 validation에서 구간별 실제 APE, MdAPE, MAPE, p95_APE, 표본 수를 확인한 뒤 확정한다.

## 8. 실험 목록

### PP-L1. CatBoost MAPE 목적 최적화 실험

- 목적:
  - CatBoost 자체 학습 설정을 MAPE 감소 방향으로 조정했을 때 기존 CatBoost보다 개선되는지 확인한다.
- 실험 방식:
  - 기존 CatBoost 기준 모델과 MAPE 중심 설정 CatBoost를 비교한다.
  - 가능 후보는 MAE 계열, Quantile 계열, 저가 구간 sample weight 적용 CatBoost로 둔다.
- 확인할 결과:
  - 전체 MAPE가 감소하는지 확인한다.
  - 저가 구간만 좋아지고 중가/고가 구간이 악화되는지 확인한다.
  - MdAPE와 p95_APE가 함께 유지되는지 확인한다.
- 기대 결과:
  - Cold에서는 작품 조건 조합이 중요하므로 CatBoost 설정 조정 효과가 있을 가능성이 있다.

### PP-L2. CatBoost 학습 옵션별 MAPE 민감도 실험

- 목적:
  - CatBoost의 트리 깊이, 학습률, 규제 강도에 따라 MAPE가 어떻게 변하는지 확인한다.
- 실험 옵션:
  - `depth`: 4, 6, 8
  - `learning_rate`: 0.03, 0.05, 0.1
  - `l2_leaf_reg`: 3, 10, 30
  - `iterations`: early stopping 기준으로 관리
- 확인할 결과:
  - 깊은 트리가 조건 조합을 더 잘 잡는지 확인한다.
  - 깊은 트리가 과적합으로 p95_APE를 키우는지 확인한다.
  - 규제를 강하게 했을 때 MAPE와 p95_APE가 안정되는지 확인한다.
- 기대 결과:
  - Warm은 과도한 트리 깊이보다 안정적인 설정이 유리할 수 있다.
  - Cold는 조건 조합이 많아 CatBoost 설정 차이가 더 크게 나타날 수 있다.

### PP-L3. Huber 선행 + CatBoost residual 보정

- 목적:
  - Huber가 만든 안정적인 기본 가격선 위에 CatBoost가 남은 오차를 보정할 수 있는지 확인한다.
- 계산 구조:

```text
huber_pred_log = Huber가 예측한 로그 가격
residual_log = actual_log - huber_pred_log
catboost_residual_pred = CatBoost가 예측한 residual_log
final_pred_log = huber_pred_log + catboost_residual_pred
```

- 진행 방식:
  - Huber 예측값은 내부 교차 예측 방식으로 만든다.
  - CatBoost residual 모델은 Huber가 학습에 직접 본 샘플의 오차를 그대로 학습하지 않도록 OOF 기반으로 학습한다.
  - validation에서 residual 보정 적용 전후를 비교한다.
- 확인할 결과:
  - Huber 단독보다 MAPE가 낮아지는지 확인한다.
  - MdAPE가 유지되는지 확인한다.
  - p95_APE가 함께 줄어드는지 확인한다.
- 기대 결과:
  - Huber가 설명하지 못한 작가 x 크기 x 재료 조합 오차를 CatBoost가 보정할 수 있다.

### PP-L4. Huber + Quantile width 기반 위험 구간 보정

- 목적:
  - Quantile 모델의 `q10_log`, `q90_log` 예측값으로 `quantile_width`를 계산하고, validation에서 정의한 위험 구간에만 보정을 적용한다.
- 계산 구조:

```text
huber_pred_log = Huber 예측 로그 가격
q10_log = Quantile 하위 예측 로그 가격
q50_log = Quantile 중앙 예측 로그 가격
q90_log = Quantile 상위 예측 로그 가격
quantile_width = q90_log - q10_log
price_range_ratio = exp(quantile_width)
```

- 진행 방식:
  - validation에서 `quantile_width`와 `price_range_ratio`를 계산한다.
  - 기본 실험은 validation `quantile_width`의 33%, 66% 분위값으로 low / mid / high 구간을 정의한다.
  - 보고와 운영 해석용으로는 `price_range_ratio` 기준을 함께 확인한다.
  - 예시는 `price_range_ratio <= 1.5배`는 안정 구간, `1.5배~2.5배`는 주의 구간, `2.5배 초과`는 위험 구간으로 본다.
  - 표본 수가 부족하면 2구간 기준으로 `price_range_ratio <= 2.5배`는 normal, `2.5배 초과`는 high risk로 사용한다.
  - 정의된 high uncertainty 구간에만 validation residual 중앙값 보정을 적용한다.
  - 일반 구간은 Huber 예측값을 유지한다.
- 확인할 결과:
  - 위험 구간의 MAPE가 줄어드는지 확인한다.
  - `price_range_ratio`가 큰 구간일수록 실제 APE가 커지는지 확인한다.
  - 전체 MdAPE가 악화되지 않는지 확인한다.
  - p95_APE가 줄어드는지 확인한다.
- 기대 결과:
  - 안정적인 작품은 건드리지 않고, 큰 오차 가능성이 높은 작품만 보정할 수 있다.

### PP-L5. Huber + Quantile + CatBoost 라우팅

- 목적:
  - Huber, Quantile, CatBoost를 각각 기본 예측, 위험도 지표 계산, 조건 조합 보정 역할로 나누어 최종 예측값을 선택한다.
- 라우팅 구조:

```text
if quantile_width 낮음:
    final_pred_log = huber_pred_log

if quantile_width 높고 CatBoost 보정이 validation에서 우수:
    final_pred_log = huber_pred_log + catboost_residual_pred

if quantile_width 높고 CatBoost 대체 예측이 우수:
    final_pred_log = catboost_pred_log
```

- 확인할 결과:
  - Huber 단독보다 MAPE가 줄어드는지 확인한다.
  - 모든 작품을 CatBoost로 바꾸는 것보다 위험 구간만 CatBoost를 쓰는 방식이 안정적인지 확인한다.
  - 라우팅 기준이 너무 복잡하지 않고 운영 적용 가능한지 확인한다.
- 기대 결과:
  - 일반 구간은 Huber의 안정성을 유지하고, 위험 구간만 CatBoost의 조건 조합 학습 능력을 활용할 수 있다.

### PP-L6. Huber / Quantile / CatBoost 가중 앙상블

- 목적:
  - 세 모델의 예측값을 가중 평균해 MAPE를 낮출 수 있는지 확인한다.
- 계산 구조:

```text
final_pred_log =
  w1 * huber_pred_log
  + w2 * quantile_q50_log
  + w3 * catboost_pred_log

w1 + w2 + w3 = 1
```

- 가중치 후보:

| 후보 | Huber | Quantile q50 | CatBoost | 의도 |
|---|---:|---:|---:|---|
| Huber 중심 | 0.6 | 0.2 | 0.2 | 안정성 우선 |
| CatBoost 중심 | 0.3 | 0.2 | 0.5 | 조건 조합 반영 |
| Quantile 중심 | 0.3 | 0.5 | 0.2 | 중앙 비율 오차 보정 |
| 균등 평균 | 0.33 | 0.33 | 0.34 | 단순 앙상블 기준 |

- 확인할 결과:
  - 단일 모델보다 MAPE가 낮아지는지 확인한다.
  - MdAPE와 p95_APE가 악화되지 않는지 확인한다.
  - validation에서 선택한 가중치가 test에서도 재현되는지 확인한다.
- 기대 결과:
  - 단순하고 운영 적용이 쉬운 조합 후보를 찾을 수 있다.

### PP-L7. Quantile 구간 기반 3단계 상세 학습 실험

- 목적:
  - Quantile 모델의 `q10_log`, `q90_log` 예측값으로 `quantile_width`를 계산하고, validation에서 정의한 불확실성 구간을 기준으로 샘플을 나눈다.
  - 그 뒤 Huber 상세 학습, CatBoost 상세 학습, Huber+CatBoost 결합 학습을 분리해서 비교한다.
  - 단순히 예측 후 중앙값을 더하는 것이 아니라, validation에서 정의한 Quantile width 구간을 학습 분기 기준으로 사용해 구간별 가격선을 더 세밀하게 만든다.
- 핵심 개념:
  - Quantile 모델은 하나의 가격만 예측하는 것이 아니라 낮은 가격 가능성, 중앙 가격 가능성, 높은 가격 가능성을 수치로 출력한다.
  - Quantile 모델이 low / mid / high 구간을 직접 만들어주는 것은 아니다.
  - `q90_log - q10_log`가 크면 해당 작품의 예측 가격 범위가 넓다는 뜻이고, 이는 모델이 해당 작품을 불확실하게 보고 있다는 신호로 해석한다.
  - 로그 폭인 `quantile_width`는 `exp(quantile_width)`로 원가격 배수 폭으로 환산할 수 있다.
  - 예를 들어 `quantile_width = 0.7`이면 `exp(0.7) ≈ 2.0`이므로, q90 예측 가격이 q10 예측 가격보다 약 2배 높다는 뜻이다.
  - low / mid / high uncertainty 구간은 validation의 `quantile_width` 분포 또는 `price_range_ratio` 기준으로 우리가 정의한다.
  - 이렇게 정의한 불확실성 구간별로 Huber와 CatBoost를 각각 따로 실험하면, 어떤 모델이 어떤 불확실성 구간에 적합한지 분리해서 판단할 수 있다.
  - 구간별 표본 수가 부족한 경우에는 별도 모델을 학습하지 않고 전체 모델 또는 residual 중앙값 보정으로 fallback한다.
- 계산 구조:

```text
q10_log = Quantile 하위 예측 로그 가격
q50_log = Quantile 중앙 예측 로그 가격
q90_log = Quantile 상위 예측 로그 가격

quantile_width = q90_log - q10_log
price_range_ratio = exp(quantile_width)

validation에서 구간 경계 정의:
  low uncertainty = quantile_width <= validation 33% 분위값
  mid uncertainty = validation 33% 분위값 < quantile_width <= validation 66% 분위값
  high uncertainty = quantile_width > validation 66% 분위값

원가격 배수 기준 해석:
  stable range = price_range_ratio <= 1.5배
  caution range = 1.5배 < price_range_ratio <= 2.5배
  risk range = price_range_ratio > 2.5배

표본 수 부족 시 2구간 fallback:
  normal uncertainty = price_range_ratio <= 2.5배
  high uncertainty = price_range_ratio > 2.5배

각 uncertainty_segment 안에서:
  1. Huber 구간별 학습
  2. CatBoost 구간별 학습
  3. Huber + CatBoost 결합 학습/보정

segment_pred_log = 해당 구간 전용 모델 또는 결합 모델의 예측 로그 가격

표본 수가 부족한 구간:
  base_pred_log = 전체 기준 모델 예측 로그 가격
  residual_log = actual_log - base_pred_log
  segment_correction = 같은 구간 residual_log의 중앙값
  corrected_pred_log = base_pred_log + segment_correction
```

- 전체 진행 방식:
  - 1단계로 Quantile 모델을 학습해 `q10_log`, `q50_log`, `q90_log`를 생성한다.
  - validation에서 `quantile_width`와 `price_range_ratio = exp(quantile_width)`를 계산한다.
  - 기본 실험은 validation `quantile_width`의 33%, 66% 분위값을 기준으로 low / mid / high uncertainty 구간 경계를 정의한다.
  - 해석용 기준으로는 `price_range_ratio` 1.5배 이하, 1.5~2.5배, 2.5배 초과 구간을 함께 확인한다.
  - 구간별 표본 수가 부족하면 `price_range_ratio` 2.5배 기준으로 normal / high 2구간만 사용한다.
  - 이후 Huber 상세 실험, CatBoost 상세 실험, Huber+CatBoost 결합 실험을 순서대로 실행한다.
  - test에는 validation에서 정한 구간 경계, 모델 선택 기준, fallback 기준을 그대로 적용한다.

#### PP-L7-0. Quantile 구간 생성 및 검증

- 목적:
  - Quantile이 예측한 범위 폭이 실제 오차 위험을 잘 구분하는지 먼저 확인한다.
- 진행 방식:
  - `q10_log`, `q50_log`, `q90_log`를 만든다.
  - `quantile_width`와 `price_range_ratio`를 계산한다.
  - validation에서 low / mid / high 또는 normal / high 구간을 정의한다.
  - 구간별 실제 APE, MdAPE, MAPE, p95_APE, 표본 수를 확인한다.
- 성공 기준:
  - `price_range_ratio`가 큰 구간에서 실제 APE 또는 p95_APE가 높게 나타난다.
  - 구간별 표본 수가 후속 Huber/CatBoost 학습에 충분하다.

#### PP-L7-H. Quantile 구간별 Huber 상세 학습

- 목적:
  - Quantile 불확실성 구간별로 Huber를 따로 학습했을 때 중앙 가격선이 더 안정적으로 맞는지 확인한다.
- 적용 대상:
  - Warm 우선 적용
  - Cold에서도 선형 기준선 비교가 필요할 경우 보조 적용
- 진행 방식:
  - low / mid / high uncertainty 구간별로 Huber 모델을 따로 학습한다.
  - 각 구간의 Huber 계수, outlier 비율, residual 중앙값을 확인한다.
  - 표본 수가 부족한 구간은 전체 Huber 또는 residual 중앙값 보정으로 fallback한다.
- 비교군:
  - 전체 Huber 단독
  - 전체 Huber + 전체 median residual 보정
  - Quantile 구간별 Huber 재학습
  - Quantile 구간별 Huber 재학습 + 구간별 residual 중앙값 보정
- 확인할 결과:
  - 안정 구간에서 MdAPE가 유지 또는 개선되는지 확인한다.
  - 위험 구간에서 MAPE와 p95_APE가 줄어드는지 확인한다.
  - 구간별 계수 방향이 해석 가능한지 확인한다.
- 기대 결과:
  - Huber는 선형 모델이므로 구간별 가격선과 계수 해석이 가능하다.
  - 안정 구간에서는 Huber의 강점을 유지하고, 위험 구간에서는 별도 가격선으로 과대/과소 예측을 줄일 수 있다.

#### PP-L7-CB. Quantile 구간별 CatBoost 상세 학습

- 목적:
  - Quantile 불확실성 구간별로 CatBoost를 따로 학습했을 때 조건 조합 학습이 더 잘 되는지 확인한다.
- 적용 대상:
  - Cold 우선 적용
  - Warm high uncertainty 구간에서 보조 비교
- 진행 방식:
  - low / mid / high uncertainty 구간별로 CatBoost를 따로 학습한다.
  - 각 구간에서 CatBoost depth, learning_rate, l2_leaf_reg를 제한적으로 비교한다.
  - leaf/segment별 residual과 표본 수를 확인한다.
  - 표본 수가 부족한 구간은 전체 CatBoost 또는 상위 구간 CatBoost로 fallback한다.
- 비교군:
  - 전체 CatBoost 단독
  - 전체 CatBoost + residual 중앙값 보정
  - Quantile 구간별 CatBoost 재학습
  - Quantile 구간별 CatBoost 재학습 + leaf/segment residual 보정
- 확인할 결과:
  - 위험 구간에서 MAPE와 p95_APE가 줄어드는지 확인한다.
  - low uncertainty 구간에서 오히려 과적합이 생기지 않는지 확인한다.
  - CatBoost leaf/segment가 실제 고오차 구간을 더 잘 나누는지 확인한다.
- 기대 결과:
  - CatBoost는 작가, 크기, 재료, 형태 조합을 나누는 데 강하므로 high uncertainty 구간에서 Huber보다 유리할 수 있다.
  - 다만 표본 수가 부족하면 과적합 위험이 있으므로 fallback 기준이 필요하다.

#### PP-L7-HCB. Quantile 구간별 Huber + CatBoost 결합 실험

- 목적:
  - Huber와 CatBoost를 경쟁 모델로만 보지 않고, Quantile 구간별로 역할을 나누어 조합했을 때 성능이 개선되는지 확인한다.
- 진행 방식:
  - low uncertainty 구간은 Huber 예측을 기본으로 둔다.
  - mid uncertainty 구간은 Huber와 CatBoost의 단순 평균 또는 validation 가중 평균을 비교한다.
  - high uncertainty 구간은 CatBoost residual 보정 또는 CatBoost 대체 예측을 비교한다.
  - 모든 선택 기준은 validation에서 정하고 test에는 그대로 적용한다.
- 라우팅 예시:

```text
stable range:
  final_pred_log = Huber 구간 모델 예측

caution range:
  final_pred_log = w * Huber 구간 모델 예측 + (1 - w) * CatBoost 구간 모델 예측

risk range:
  final_pred_log = Huber 구간 모델 예측 + CatBoost residual 예측
  또는 final_pred_log = CatBoost 구간 모델 예측
```

- 확인할 결과:
  - Huber 단독, CatBoost 단독보다 MdAPE가 유지 또는 개선되는지 확인한다.
  - MAPE와 p95_APE가 함께 줄어드는지 확인한다.
  - 라우팅 기준이 복잡해지면서 test 재현성이 떨어지지 않는지 확인한다.
- 기대 결과:
  - 안정 구간은 Huber의 해석성과 안정성을 활용한다.
  - 위험 구간은 CatBoost의 조건 조합 학습 능력을 활용한다.
  - 중간 구간은 두 모델의 가중 평균으로 변동성을 낮출 수 있다.

- 비교군:
  - 기준 모델 단독
  - Quantile `q50_log` 단독
  - 기준 모델 + 전체 median residual 보정
  - PP-L7-H: Quantile width 구간별 Huber 재학습
  - PP-L7-CB: Quantile width 구간별 CatBoost 재학습
  - PP-L7-HCB: Quantile width 구간별 Huber + CatBoost 결합
- 확인할 결과:
  - Quantile width가 큰 구간에서 MAPE가 줄어드는지 확인한다.
  - `price_range_ratio`가 큰 구간이 실제 고오차 구간과 일치하는지 확인한다.
  - 전체 MdAPE가 유지 또는 개선되는지 확인한다.
  - p95_APE가 악화되지 않는지 확인한다.
  - low / mid / high uncertainty 구간별 표본 수가 별도 모델 학습에 충분한지 확인한다.
  - 구간별 재학습이 단순 residual 중앙값 보정보다 더 나은지 확인한다.
- 기대 결과:
  - 예측 불확실성이 낮은 작품은 Huber 중심의 안정적인 가격선을 유지하고, 불확실성이 큰 작품은 CatBoost의 조건 조합 학습 또는 구간별 재학습으로 보완할 수 있다.
  - 단순 전체 보정보다 더 세밀하게 MdAPE, MAPE, p95_APE를 함께 개선할 수 있다.
- 주의점:
  - Quantile 구간 경계, 구간별 모델 선택 기준, 보정값은 validation에서만 정한다.
  - `price_range_ratio`의 1.5배/2.5배 기준은 초기 가설이며, 최종 기준은 validation 성능과 구간별 표본 수를 함께 보고 확정한다.
  - test 결과를 보고 구간 경계나 모델 선택 기준을 다시 조정하지 않는다.
  - test에서는 validation에서 정한 구간 경계를 그대로 사용해 각 샘플의 uncertainty 구간만 판정한다.
  - 구간별 표본 수가 부족하면 별도 모델을 학습하지 않고 상위 구간 모델, 전체 모델, 또는 residual 중앙값 보정으로 fallback한다.

### PP-L8. Quantile-Huber-CatBoost 순차 학습 실험

- 목적:
  - Quantile, Huber, CatBoost를 단순 평균으로 결합하지 않고 각 모델의 장점을 순서대로 사용하는 파이프라인을 검증한다.
  - Quantile은 선행 진단 모델로 사용하고, Huber는 안정적인 중심 가격선을 만들며, CatBoost는 Huber가 남긴 조건 조합 오차를 보정하는 역할로 분리한다.
- 핵심 구조:

```text
1단계: Quantile 선행 진단
  q10_log, q50_log, q90_log 예측
  quantile_width = q90_log - q10_log
  price_range_ratio = exp(quantile_width)
  validation에서 stable / caution / risk 구간 정의

2단계: Huber 중심 가격선 생성
  각 구간에서 Huber 예측값 생성
  필요 시 stable / caution / risk 구간별 Huber 재학습
  huber_pred_log 생성

3단계: CatBoost residual 보정
  residual_log = actual_log - huber_pred_log
  CatBoost가 residual_log를 학습
  final_pred_log = huber_pred_log + catboost_residual_pred
```

- 구간별 적용 전략:

| 구간 | 판단 기준 예시 | Huber 역할 | CatBoost 역할 | 최종 처리 |
|---|---|---|---|---|
| stable | `price_range_ratio <= 1.5배` | 기본 예측 유지 | 적용하지 않거나 약한 보정만 비교 | Huber 중심 |
| caution | `1.5배 < price_range_ratio <= 2.5배` | 구간별 Huber 재학습 | residual 약한 보정 비교 | Huber + CatBoost 보정 비교 |
| risk | `price_range_ratio > 2.5배` | 중심 가격선 제공 | residual 보정 또는 대체 예측 비교 | CatBoost 보정/대체 우선 검증 |

- 진행 방식:
  - Quantile 구간 경계는 validation에서만 정의한다.
  - Huber 예측값은 OOF 방식으로 생성해 CatBoost residual 학습의 과적합을 줄인다.
  - CatBoost residual 모델은 `residual_log = actual_log - huber_pred_log`를 target으로 학습한다.
  - stable / caution / risk 구간별로 CatBoost residual 보정 강도를 다르게 비교한다.
  - test에는 validation에서 정한 구간 경계, Huber 모델, CatBoost residual 모델, 보정 강도를 그대로 적용한다.
- 비교군:
  - Huber 단독
  - CatBoost 단독
  - Huber + CatBoost residual
  - Quantile 구간별 Huber 재학습
  - Quantile 구간별 CatBoost 재학습
  - Quantile → Huber → CatBoost residual 순차 구조
  - Huber / Quantile / CatBoost 단순 가중 앙상블
- 확인할 결과:
  - 단순 가중 앙상블보다 순차 구조가 MdAPE를 더 안정적으로 유지하는지 확인한다.
  - risk 구간에서 MAPE와 p95_APE가 줄어드는지 확인한다.
  - stable 구간에서 불필요한 CatBoost 보정으로 성능이 악화되지 않는지 확인한다.
  - CatBoost residual 보정이 Huber의 선형 중심선을 실제로 보완하는지 확인한다.
- 기대 결과:
  - Quantile은 예측 불확실성을 먼저 진단하고, Huber는 안정적인 기준 가격선을 만들며, CatBoost는 조건 조합 오차를 보정하는 구조가 된다.
  - 단순 결합보다 모델별 역할이 명확하므로 상사 보고와 후속 운영 정책 설명이 쉽다.
- 주의점:
  - 단계가 많아 validation 과적합 위험이 있으므로 OOF 예측을 사용한다.
  - Quantile 구간 기준, Huber/CatBoost 선택 기준, residual 보정 강도는 test를 보지 않고 validation에서만 확정한다.
  - 단순 Huber, 단순 CatBoost, 단순 가중 앙상블 대비 개선이 명확하지 않으면 채택하지 않는다.

### PP-L9. Huber-Quantile-CatBoost residual 순차 학습 실험

- 목적:
  - Huber를 먼저 적용해 안정적인 기준 가격선을 만든 뒤, Quantile로 Huber 예측 오차의 범위를 추정하고, CatBoost로 남은 조건 조합 오차를 보정하는 구조를 검증한다.
  - Quantile을 가격 자체의 불확실성 추정이 아니라 Huber residual의 불확실성 추정에 사용한다.
- 핵심 구조:

```text
1단계: Huber 중심 가격선 생성
  huber_pred_log = Huber 예측 로그 가격

2단계: Quantile residual 범위 추정
  residual_log = actual_log - huber_pred_log
  residual_q10 = Quantile이 예측한 낮은 쪽 residual
  residual_q50 = Quantile이 예측한 중앙 residual
  residual_q90 = Quantile이 예측한 높은 쪽 residual
  residual_width = residual_q90 - residual_q10
  residual_range_ratio = exp(residual_width)

3단계: CatBoost residual 보정
  quantile_corrected_pred_log = huber_pred_log + residual_q50
  remaining_residual_log = actual_log - quantile_corrected_pred_log
  CatBoost가 remaining_residual_log를 학습
  final_pred_log = huber_pred_log + residual_q50 + catboost_remaining_residual_pred
```

- 이 실험의 의미:
  - PP-L8은 Quantile을 먼저 사용해 작품의 예측 불확실성 구간을 정의한다.
  - PP-L9는 Huber를 먼저 사용해 기준 가격선을 만들고, Quantile은 Huber가 얼마나 틀릴 수 있는지 residual 범위를 추정한다.
  - 따라서 PP-L9는 Warm Huber 기준 모델을 유지하면서 보정 구조를 고도화하는 실험으로 볼 수 있다.
- 구간별 적용 전략:

| 구간 | 판단 기준 예시 | Quantile residual 해석 | CatBoost 적용 |
|---|---|---|---|
| residual stable | `residual_range_ratio <= 1.5배` | Huber residual 범위가 좁음 | CatBoost 보정 없음 또는 약한 보정 |
| residual caution | `1.5배 < residual_range_ratio <= 2.5배` | Huber residual 범위가 중간 | residual q50 보정 + CatBoost 약한 보정 비교 |
| residual risk | `residual_range_ratio > 2.5배` | Huber residual 범위가 큼 | CatBoost remaining residual 보정 우선 검증 |

- 진행 방식:
  - Huber 예측값은 OOF 방식으로 생성한다.
  - OOF Huber 예측값으로 `residual_log = actual_log - huber_pred_log`를 만든다.
  - Quantile 모델은 가격이 아니라 Huber residual을 target으로 학습한다.
  - Quantile residual의 `residual_q50`을 1차 보정값으로 적용한다.
  - CatBoost는 Quantile residual 보정 후 남은 `remaining_residual_log`를 학습한다.
  - test에는 validation에서 정한 residual 위험 구간, residual q50 보정, CatBoost 보정 기준을 그대로 적용한다.
- 비교군:
  - Huber 단독
  - Huber + 전체 median residual 보정
  - Huber + Quantile residual q50 보정
  - Huber + CatBoost residual 보정
  - Huber + Quantile residual q50 + CatBoost remaining residual 보정
  - PP-L8 Quantile → Huber → CatBoost 순차 구조
- 확인할 결과:
  - Huber 단독보다 MdAPE가 유지 또는 개선되는지 확인한다.
  - Huber residual risk 구간에서 MAPE와 p95_APE가 줄어드는지 확인한다.
  - Quantile residual q50 보정만으로 충분한지, CatBoost remaining residual 보정까지 필요한지 확인한다.
  - PP-L8과 비교해 어떤 순차 구조가 더 안정적인지 확인한다.
- 기대 결과:
  - Huber 기준 모델을 유지하면서, Huber가 불확실하게 예측한 구간만 Quantile과 CatBoost로 보완할 수 있다.
  - Warm Huber 중심의 설명 구조를 유지하면서 MAPE와 큰 오차를 줄일 가능성이 있다.
- 주의점:
  - Huber residual을 학습하므로 OOF 예측이 필수다.
  - Quantile residual 모델과 CatBoost remaining residual 모델을 같은 validation에 과도하게 맞추지 않도록 단순한 설정부터 비교한다.
  - Huber 단독 또는 Huber + CatBoost residual보다 개선이 명확하지 않으면 채택하지 않는다.

### PP-L10. Warm PP-L8 피처 변형 비교

- 목적:
  - `PP-L8`의 `Quantile -> Huber -> CatBoost residual` 구조를 그대로 유지하고 Warm 피처셋만 바꿔 개선 가능성을 확인한다.
  - `PP-U1`에서 개선 신호가 있던 생성 bucket과 `PP-Z1`에서 개선 신호가 있던 검색/외부 피처가 순차 구조에서도 유효한지 확인한다.
- 고정 구조:

```text
CatBoost Quantile q10/q50/q90
-> q10_log, q50_log, q90_log, quantile_width, price_range_ratio 생성
-> Huber 중심 가격선 학습
-> OOF Huber residual을 CatBoost가 학습
-> final_pred_log = huber_pred_log + catboost_residual_pred
```

- 비교 피처셋:
  - `base_existing_combo`
  - `artist_size_only`
  - `artist_size_works`
  - `full_plus_generated_buckets`
  - `warm_base_search_all`
  - `warm_base_artist_meta_all`
  - `warm_base_meta_external_search_all`
- 비교 기준:
  - 각 피처셋별 Huber 단독, Quantile q50 단독, PP-L8 순차 구조를 함께 비교한다.
  - 기존 `PP-L8`, `PP-V1`, `PP-V2`와 test 지표를 비교한다.
- 실행 결과 요약:
  - best MdAPE: `l8_seq__warm_base_meta_external_search_all`, test MdAPE `0.1708`, MAPE `0.3363`, p95 `1.1432`.
  - best MAPE/p95 균형: `l8_seq__full_plus_generated_buckets`, test MdAPE `0.1743`, MAPE `0.3265`, p95 `0.9818`.
  - 기존 Warm 최종 후보 `PP-V1/PP-V2`보다 약하므로 대표 후보 교체는 보류한다.

## 9. 추천 실행 순서

| 순서 | 실험 | 이유 |
|---:|---|---|
| 1 | PP-L1 CatBoost MAPE 목적 최적화 | CatBoost 단독 개선 가능성을 먼저 확인 |
| 2 | PP-L2 CatBoost 옵션 민감도 | CatBoost가 MAPE 목표에 맞게 조정 가능한지 확인 |
| 3 | PP-L3 Huber + CatBoost residual | Huber 안정성 + CatBoost 보정 효과 확인 |
| 4 | PP-L4 Huber + Quantile width 기반 위험 구간 보정 | Quantile 예측값으로 계산한 width를 위험 구간 판단에 활용 |
| 5 | PP-L7-0 Quantile 구간 생성 및 검증 | Quantile width와 price_range_ratio가 실제 오차 위험을 구분하는지 확인 |
| 6 | PP-L7-H Quantile 구간별 Huber 상세 학습 | 구간별 Huber 재학습이 중앙 가격선을 안정화하는지 확인 |
| 7 | PP-L7-CB Quantile 구간별 CatBoost 상세 학습 | 구간별 CatBoost 재학습이 조건 조합 오차를 줄이는지 확인 |
| 8 | PP-L7-HCB Quantile 구간별 Huber + CatBoost 결합 | 안정 구간은 Huber, 위험 구간은 CatBoost를 쓰는 조합이 유효한지 확인 |
| 9 | PP-L8 Quantile-Huber-CatBoost 순차 학습 | Quantile 진단, Huber 중심선, CatBoost residual 보정의 순차 구조 검증 |
| 10 | PP-L9 Huber-Quantile-CatBoost residual 순차 학습 | Huber 중심선 이후 Quantile residual과 CatBoost remaining residual 보정 구조 검증 |
| 11 | PP-L10 Warm PP-L8 피처 변형 비교 | PP-L8 구조를 고정하고 Warm 피처셋만 바꿔 개선 가능성 검증 |
| 12 | PP-L5 Huber + Quantile + CatBoost 라우팅 | 세 모델의 역할 조합 검증 |
| 12 | PP-L6 가중 앙상블 | 단순 결합 후보와 복잡한 라우팅 후보 비교 |

## 10. 채택 기준

| 구분 | 채택 판단 |
|---|---|
| 최우선 채택 | MdAPE 개선 + MAPE 개선 + p95_APE 개선 |
| 채택 가능 | MdAPE 유지 + MAPE 개선 + p95_APE 악화 없음 |
| 조건부 채택 | MdAPE 소폭 악화 + MAPE 큰 폭 개선. 단, 특정 위험 구간 방어 목적일 때만 |
| 보류 | MAPE만 개선되고 MdAPE 또는 p95_APE가 악화 |
| 중단 | validation에서만 개선되고 test에서 재현되지 않음 |

## 11. 예상 산출물

- 모델별 기본 성능 비교표
- Warm/Cold 분리 성능표
- 가격대별 MAPE 비교표
- Quantile width 및 price_range_ratio 구간별 실제 APE 분포표
- Huber 단독 vs Huber+CatBoost residual 비교표
- Huber 단독 vs Huber+Quantile width 기반 위험 구간 보정 비교표
- PP-L7-0 Quantile 구간별 실제 오차 위험 검증표
- PP-L7-H Quantile 구간별 Huber 재학습 결과표
- PP-L7-CB Quantile 구간별 CatBoost 재학습 결과표
- PP-L7-HCB Quantile 구간별 Huber + CatBoost 결합 결과표
- PP-L8 Quantile-Huber-CatBoost 순차 학습 결과표
- PP-L9 Huber-Quantile-CatBoost residual 순차 학습 결과표
- PP-L10 Warm PP-L8 피처 변형 비교 결과표
- Huber residual Quantile 범위 및 residual_range_ratio 구간별 실제 오차표
- Quantile width 구간별 중앙값 보정 결과표
- Quantile width 구간별 표본 수 및 fallback 기준표
- Huber/Quantile/CatBoost 라우팅 결과표
- baseline 전체 비교표
- paired bootstrap 95% CI 결과표
- Wilcoxon signed-rank test 결과표
- seed 반복 평균/표준편차 표
- 구간 기준 민감도 분석표
- 모델 복잡도 대비 성능 개선표
- 실패/보류 실험 기록표
- 최종 채택/보류/중단 판단표

## 12. 상사 보고용 요약

MAPE 감소를 목표로 Huber, Quantile, CatBoost를 조합한 성능 최적화 실험을 추가로 진행하려고 한다.

Huber는 이상치 영향을 줄이며 안정적인 기본 가격선을 만드는 데 강점이 있고, Quantile은 `q10_log`, `q50_log`, `q90_log`를 통해 예측 범위 폭을 계산하는 데 유리하다. 특히 `price_range_ratio = exp(q90_log - q10_log)`로 환산하면 예측 가격 범위가 몇 배 벌어지는지 설명할 수 있다. CatBoost는 작가, 작품 크기, 재료, 형태처럼 조건 조합에 따라 가격이 달라지는 구조를 학습하는 데 강점이 있다.

따라서 이번 실험은 먼저 Quantile 예측값에서 계산한 `quantile_width`와 `price_range_ratio`를 기준으로 validation에서 위험 구간과 불확실성 구간을 정의한다. 이후 1단계로 구간별 Huber 재학습, 2단계로 구간별 CatBoost 재학습, 3단계로 Huber + CatBoost 결합을 순차적으로 비교한다. 추가로 Quantile을 선행 진단 모델, Huber를 중심 가격선 모델, CatBoost를 residual 보정 모델로 사용하는 PP-L8 순차 구조와, Huber를 먼저 적용한 뒤 Quantile로 Huber residual 범위를 추정하고 CatBoost로 남은 residual을 보정하는 PP-L9 순차 구조를 별도 검증한다. 이를 통해 안정 구간은 Huber의 해석성과 안정성을 활용하고, 위험 구간은 CatBoost의 조건 조합 학습 능력을 활용할 수 있는지 검증한다. 또한 CatBoost 자체의 학습 옵션을 MAPE 목표에 맞게 조정하는 실험과 세 모델의 가중 앙상블도 함께 비교한다.

평가 기준은 전체 MAPE만 보지 않고 MdAPE, p95_APE, Warm/Cold별 MAPE, 가격대별 MAPE를 함께 확인한다. 최종적으로는 MdAPE를 유지하거나 개선하는 범위 안에서 MAPE와 큰 오차를 줄이는 조합만 채택한다.
