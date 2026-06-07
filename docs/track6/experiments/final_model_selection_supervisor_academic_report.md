# 가격 예측 모델 선정 및 보정 전략 상사용 논문식 리포트

- 작성일: 2026-06-04
- 대상: 실험 결과의 모델링 근거, 수식, 피처 영향도, 최종 후보 선정 논리를 검토하는 상사/기술 검토자
- 기준 문서: `final_model_feature_selection_customization_report.md`
- 핵심 결론: Warm은 Huber 중심선 + 비교군 통계 + PP-V8 방어 후보 결합을 최종 후보로 유지. Cold는 안정성 검증이 된 PP-Y18을 기준 후보로 두고, PP-QR3 guard/segment 보정은 추가 개선 후보로 관리

## 초록

본 리포트는 미술품 가격 예측 실험에서 Warm/Cold 조건을 분리하고, 각 조건에 적합한 모델과 후처리 방식을 선정한 근거를 정리한다.

- Warm 조건: 학습 데이터에 동일 작가의 과거 거래 이력이 존재
- Cold 조건: 동일 작가의 학습 이력이 없거나 작가 매칭 신뢰도가 낮음
- Warm 최종 후보: `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
- Warm 최종 성능: test MdAPE `0.1405`, MAPE `0.2748`, p95_APE `0.8331`
- Cold 검증 기준 후보: `PP-Y18 qwidth_bin_oof_min30_cap0.25`
- Cold 검증 기준 성능: MdAPE `0.4247`, MAPE `0.9910`, p95_APE `3.3053`
- Cold 추가 개선 후보: `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`
- Cold 추가 개선 성능: MdAPE `0.4178`, MAPE `0.9640`, p95_APE `2.5377`
- 최종 판단: Warm은 서비스 점 예측 후보로 사용 가능, Cold는 단일 확정 가격보다 참고 예측가와 불확실성 범위로 제공 필요

핵심 연구 질문:

- 같은 작가 이력이 있는 Warm에서 Huber 모델이 왜 적합한가
- 비교군 통계 피처가 단순 표시값을 넘어 실제 예측 성능을 개선하는가
- 기존 compact blend 후보의 평균오차 방어력을 왜 30% 결합했는가
- Cold에서 CatBoost와 LightGBM Quantile의 구조적 차이가 어떤 보정 전략으로 연결되는가
- 최종 후보 선정이 단일 test 점수 최적화가 아니라 반복 검증과 모델 구조에 의해 설명 가능한가

## 1. 문제 정의

### 1.1 예측 대상

가격 예측은 실제 가격을 바로 예측하지 않고 로그 가격을 예측한 뒤 원 단위 가격으로 복원한다.

```text
y_i = log(price_i)
pred_log_i = model(x_i)
pred_price_i = exp(pred_log_i)
```

로그 가격을 사용하는 이유:

- 미술품 가격은 고가 작품 때문에 오른쪽으로 길게 치우친 분포
- 실제 가격 단위에서 학습하면 고가 작품이 손실을 과도하게 지배
- 로그 가격에서는 배율 차이를 더 안정적으로 반영
- 후처리 residual도 로그 단위에서 해석 가능

### 1.2 Warm/Cold 분리

Warm과 Cold는 같은 가격 예측 문제처럼 보이지만, 통계적으로 다른 문제다.

| 구분 | 데이터 조건 | 핵심 난점 | 적합한 모델 방향 |
|---|---|---|---|
| Warm | 같은 작가의 학습 이력 존재 | 작가별 기준 가격을 안정적으로 재사용 | 작가 기준선이 해석 가능한 Huber |
| Cold | 같은 작가의 학습 이력 부족 또는 없음 | 작가 시장 가격대를 직접 알 수 없음 | 작품 조건, 작가 메타, 외부 활동성, 불확실성 모델 |

분리 이유:

- Warm은 `artist_key`가 가격 기준선 역할
- Cold는 `artist_key`를 직접 사용할 수 없거나 신뢰도가 낮음
- Warm/Cold를 합쳐 하나의 지표로 보면 Cold의 큰 오차 위험이 숨겨질 수 있음
- 운영에서도 Warm은 점 예측, Cold는 참고 예측가와 넓은 범위로 다르게 제공해야 함

Figure 1. Warm/Cold 라우팅과 운영 출력 구조:

```text
입력 작품
  |
  |-- 동일 작가의 학습 이력 있음
  |      |
  |      +-- Warm 경로
  |            - Huber 작가/크기 중심선
  |            - 비교군 통계 피처
  |            - PP-V8 평균오차 방어 후보 결합
  |            - 출력: 점 예측 가격 + 가격 범위 + 비교군 통계
  |
  |-- 동일 작가의 학습 이력 부족 또는 없음
         |
         +-- Cold 경로
               - LightGBM Quantile q10/q50/q90
               - qwidth 기반 위험 구간 보정
               - 외부 활동성/검색 피처 참고
               - 출력: 참고 예측가 + 넓은 범위 + 낮은 신뢰도
```

## 2. 평가 지표

### 2.1 개별 오차

```text
APE_i = abs(actual_price_i - pred_price_i) / actual_price_i
```

해석:

- `APE_i = 0.20`: 실제 가격 대비 20% 오차
- 가격 단위가 큰 작품과 작은 작품을 같은 비율 기준으로 비교 가능

### 2.2 대표 정확도

```text
MdAPE = median(APE_i)
```

해석:

- 전체 샘플 중 중간 수준의 절대 비율 오차
- 일반적인 샘플에서 모델이 얼마나 잘 맞는지 확인
- 본 프로젝트의 핵심 품질 지표

### 2.3 평균오차

```text
MAPE = mean(APE_i)
```

해석:

- 큰 오차 샘플의 영향이 MdAPE보다 크게 반영
- 서비스에서 “몇 개 샘플이 크게 틀리는 문제”를 확인하는 보조 핵심 지표
- Warm 최종 결합에서 PP-V8의 평균오차 방어력을 반영한 이유

### 2.4 큰 오차 위험

```text
p95_APE = percentile(APE_i, 95)
```

해석:

- 오차가 큰 상위 5% 지점
- 가격 예측 서비스에서 과도한 실패 사례를 확인하는 지표
- Cold는 p95_APE가 Warm보다 높아 단일 확정 가격으로 제공하기 어려움

### 2.5 로그 RMSE

```text
RMSE_log = sqrt(mean((actual_log_i - pred_log_i)^2))
```

해석:

- 로그 가격 공간에서의 평균 제곱 오차
- 모델 학습 공간과 직접 연결되는 지표
- 로그 단위의 큰 잔차를 확인하는 보조 지표

## 3. 모델 이론과 본 실험에서의 역할

### 3.1 Warm Huber 모델

Huber는 선형 모델의 해석 가능성과 이상치 방어를 동시에 갖는 모델이다.

가격 예측식:

```text
pred_log_price = beta_0 + beta_1*x_1 + beta_2*x_2 + ... + beta_p*x_p
pred_price = exp(pred_log_price)
```

피처 영향도 해석:

```text
feature_contribution_j = beta_j * x_j
```

의미:

- `beta_j`: 해당 피처가 로그 가격을 올리거나 낮추는 방향과 크기
- `x_j`: 해당 작품의 변환된 피처값
- 선형 구조라 피처별 영향 방향과 상대 기여도를 설명하기 쉬움
- `artist_key`는 작가별 가격 기준선 역할
- 크기 피처는 작품 규모에 따른 가격 중심선 조정 역할

Huber 손실함수:

```text
residual_i = actual_log_i - pred_log_i

if abs(residual_i) <= delta:
    loss_i = 0.5 * residual_i^2
else:
    loss_i = delta * (abs(residual_i) - 0.5 * delta)
```

Huber 손실의 의미:

- 작은 오차: 일반 제곱오차처럼 정밀하게 학습
- 큰 오차: 절대오차처럼 완만하게 반응
- 고가/저가 특이 작품이 전체 계수를 과도하게 흔드는 문제 완화
- 미술품 가격처럼 이상치가 많은 데이터에 적합

Warm에서 Huber가 적합한 이유:

- 같은 작가 이력이 있어 `artist_key` 계수가 의미 있는 기준선이 됨
- 선형 계수로 작가, 크기, 재료 피처의 방향성을 설명 가능
- 극단 가격 작품에 대해 일반 선형 회귀보다 안정적
- residual 기반 후처리와 결합 후보 생성이 단순하고 재현 가능

Figure 2. Warm Huber의 예측과 보정 연결 구조:

```text
작가/크기/재료/지지체 피처
        |
        v
피처 변환 및 인코딩
        |
        v
Huber 선형 예측
pred_log_price = beta_0 + sum(beta_j * x_j)
        |
        +-------------------------------+
        |                               |
        v                               v
pred_price = exp(pred_log_price)   residual_log = actual_log - pred_log
        |                               |
        v                               v
기본 예측 가격                    구간별 median residual 보정 후보
        |                               |
        +---------------+---------------+
                        v
              최종 Warm 후보 결합
```

### 3.2 Cold CatBoost 모델

CatBoost는 대칭 트리 구조를 사용하는 부스팅 모델이다.

예측식:

```text
pred_log_price = F_0 + eta * tree_1(x) + eta * tree_2(x) + ... + eta * tree_M(x)
```

구성:

- `F_0`: 손실함수 기준의 초기 예측값
- `tree_m(x)`: m번째 트리에서 해당 샘플이 도착한 leaf 값
- `eta`: learning rate
- 최종 예측값은 여러 트리의 leaf 값을 더한 값

대칭 트리 구조:

```text
depth 1: 모든 샘플에 같은 split 조건 적용
depth 2: 다시 모든 노드에 같은 split 조건 적용
depth 3: 같은 방식 반복
```

해석상 장점:

- 같은 깊이에서 같은 분기 조건을 사용하므로 구조가 규칙적
- `크기 x 재료 x 형태 x 깊이` 같은 조건 조합을 해석하기 좋음
- 범주형 피처와 조합 피처를 자연스럽게 다룸

해석상 한계:

- 피처 하나가 독립적으로 가격을 결정한다고 보기 어려움
- 하나의 피처 중요도가 높아도 실제 가격은 여러 split 조합의 결과
- 따라서 단일 피처 계수보다 SHAP, interaction, leaf/segment residual로 해석해야 함

Figure 3. CatBoost 대칭 트리 구조의 해석 방식:

```text
전체 샘플
  |
  | depth 1: 같은 split 조건 A를 전체 노드에 적용
  v
노드 A-                         노드 A+
  |                               |
  | depth 2: 같은 split 조건 B를 양쪽에 적용
  v                               v
A-/B-      A-/B+            A+/B-      A+/B+
  |          |                |          |
  | depth 3: 같은 split 조건 C 반복
  v          v                v          v
leaf       leaf             leaf       leaf

해석 단위:
- 단일 피처 = 독립 계수 아님
- 실제 가격 영향 = A, B, C split 조합으로 도착한 leaf 값
- 적합한 해석 = SHAP + interaction + leaf/segment residual
```

Cold에서 CatBoost의 역할:

- 단독 최종 가격 모델로는 부족
- `medium_shape_bucket`, `shape_bucket`, `depth_cm`, `support_category` 같은 조합 분리에 유용
- 큰 오차 구간의 residual 보정이나 segment 보정의 보조 모델로 적합

### 3.3 Cold LightGBM Quantile 모델

LightGBM은 leaf-wise 방식으로 트리를 확장한다.

예측식:

```text
pred_log_price = F_0 + eta * tree_1(x) + eta * tree_2(x) + ... + eta * tree_M(x)
```

leaf-wise 구조:

- 모든 가지를 균등하게 확장하지 않음
- 손실 감소가 큰 leaf를 우선적으로 더 세밀하게 분할
- 특정 조건 구간의 오차를 빠르게 줄일 수 있음
- 대신 데이터가 적은 구간에서는 과적합 위험 존재

Quantile 손실:

```text
u_i = actual_log_i - pred_quantile_log_i

if u_i >= 0:
    loss_tau_i = tau * u_i
else:
    loss_tau_i = (tau - 1) * u_i
```

분위수 예측:

```text
q10_log = model_tau_0.10(x)
q50_log = model_tau_0.50(x)
q90_log = model_tau_0.90(x)
```

불확실성 지표:

```text
quantile_width = q90_log - q10_log
price_range_ratio = exp(q90_log) / exp(q10_log)
```

해석:

- `q50_log`: 중앙 가격 예측
- `q10_log~q90_log`: 모델이 보는 낮은 가격대부터 높은 가격대까지의 범위
- `quantile_width`가 클수록 모델이 해당 샘플을 불확실하게 본다는 의미
- Cold처럼 작가 기준선이 부족한 조건에서 가격 범위와 신뢰도 판단에 적합

Figure 4. LightGBM Quantile의 범위 예측과 qwidth 보정:

```text
입력 피처
  |
  v
LightGBM Quantile
  |
  +-- q10_log: 낮은 가격대 예측
  +-- q50_log: 중앙 가격 예측
  +-- q90_log: 높은 가격대 예측
        |
        v
quantile_width = q90_log - q10_log
        |
        v
qwidth 구간화
  |
  +-- 폭 작음: 상대적으로 신뢰도 높음
  +-- 폭 중간: 일반 보정
  +-- 폭 큼: 위험 구간, 넓은 가격 범위와 낮은 신뢰도 표시
        |
        v
구간별 median residual 보정 후 참고 예측가 산출
```

## 4. 피처 설계와 영향도 해석

### 4.1 Warm 기준 피처셋

Warm 기준 피처셋은 `base_existing_combo`다.

구성:

- 작가 기준 가격대
- 작품 크기
- 깊이/입체 여부
- 형태 비율
- 재료/지지체

핵심 피처와 영향:

| 피처 그룹 | 주요 피처 | 모델상 역할 | 근거 |
|---|---|---|---|
| 작가 기준선 | `artist_key` | 같은 작가의 과거 가격 수준 반영 | 제거 시 MdAPE 약 `0.48~0.49`로 급락 |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모에 따른 가격 중심선 조정 | 제거 시 MdAPE 약 `0.55~0.56`, p95 약 `5.2~5.4`로 악화 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체/깊이 조건 보조 | 특이 작품 경고와 범위 정책에 유용 |
| 형태 | `aspect_ratio`, `is_extreme_aspect_ratio` | 극단적 형태 보조 | 단독 핵심축은 아님 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 재료와 바탕 조합 차이 보조 | 조건 설명에 필요 |

해석:

- Warm의 1차 가격 기준은 작가와 크기
- Huber는 이 기준을 선형 계수로 안정적으로 학습
- 비교군 통계는 기본 피처 이후 추가된 핵심 보강축

### 4.2 비교군 통계 피처

비교군 통계는 유사 조건의 과거 거래 가격을 요약한 값이다.

비교군 선정 순서:

| 순서 | 비교군 수준 | 의미 | 최소 표본 |
|---:|---|---|---:|
| 1 | `artist_medium_support_size` | 같은 작가 + 같은 재료/지지체 + 비슷한 크기 | 5 |
| 2 | `artist_size` | 같은 작가 + 비슷한 크기 | 5 |
| 3 | `artist` | 같은 작가 전체 | 5 |
| 4 | `medium_support_size` | 같은 재료/지지체 + 비슷한 크기 | 30 |
| 5 | `medium_category_support_size` | 같은 재료 + 같은 지지체 + 비슷한 크기 | 30 |
| 6 | `medium_size` | 같은 재료 + 비슷한 크기 | 50 |
| 7 | `global` | 위 조건 부족 시 전체 train 기준 | 전체 |

비교군 통계 계산:

```text
group_price_median = median(log_price in selected_group)
group_price_q25 = percentile(log_price in selected_group, 25)
group_price_q75 = percentile(log_price in selected_group, 75)
group_price_iqr = group_price_q75 - group_price_q25
group_n_log = log(1 + group_sample_count)
```

단순 중앙값 대체와의 차이:

- `direct median`: 비교군 중앙값 자체를 예측값으로 사용
- `svc_numeric`: 비교군 통계를 Huber 피처로 넣어 기존 작가/크기 계수와 함께 학습
- 실험 결과상 direct median은 MdAPE `0.3100`으로 약함
- 성능 개선 원인은 “가격을 중앙값으로 대체”가 아니라 “비교군 통계를 피처로 추가”한 효과

### 4.3 Cold 피처

Cold는 작가 기준선이 부족하므로 작가 외부 정보와 작품 조건을 함께 사용한다.

| 피처 축 | 주요 피처 | 역할 |
|---|---|---|
| 작품 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `size_bucket` | 물리적 가격 기준 |
| 형태/재료 | `medium_category`, `shape_bucket`, `medium_shape_bucket` | CatBoost 조합 분기 |
| 지지체/크기 | `support_category`, `support_size_bucket` | LightGBM leaf 구간 분리 |
| 작가 메타 | 작품 수, 팔로워, 출생연도, 국적, 판매 작품 수 | 작가 시장 지위 간접 보완 |
| 전시/갤러리 | 개인전, 단체전, 아트페어, 갤러리 tier | 활동성/시장 노출 |
| 검색 피처 | 검색 결과 수, 문맥 count, 검색 품질 | 인지도와 정보 가용성 |
| 불확실성 | `quantile_width`, `price_range_ratio` | 위험 구간과 신뢰도 판단 |

## 5. 실험 설계

### 5.1 후보 선정 원칙

최종 후보는 단일 test 지표만으로 선정하지 않는다.

선정 기준:

- 대표 정확도: MdAPE
- 평균오차 방어: MAPE
- 큰 오차 방어: p95_APE
- 반복 검증 안정성: seed, row holdout, artist holdout, bootstrap
- 모델 구조와 피처 영향 설명 가능성
- 서비스 운영 재현 가능성

### 5.2 후처리 표준식

로그 residual 기반 보정:

```text
residual_log = actual_log - pred_log
segment_correction = median(residual_log in same_segment)
corrected_pred_log = pred_log + clipped(segment_correction)
corrected_price = exp(corrected_pred_log)
```

median을 쓰는 이유:

- 가격 데이터는 이상치가 많음
- 평균은 극단값에 민감
- median은 반복적으로 나타나는 중심 오차를 안정적으로 반영

clipping을 쓰는 이유:

- 보정값이 너무 커져 모델 예측을 과도하게 덮는 문제 방지
- 특히 Cold와 작은 segment에서 중요

### 5.3 Warm 실험군

| 실험 | 목적 | 핵심 판단 |
|---|---|---|
| PP-SVC1 | 비교군 통계 피처가 성능에 도움이 되는지 확인 | `svc_numeric`, `svc_full` 모두 기준선 대비 크게 개선 |
| PP-SVC2 | seed 반복으로 비교군 후보 안정성 확인 | 비교군 후보는 MdAPE 강점, PP-V8은 MAPE 방어 강점 |
| PP-SVC3 | 비교군 후보와 PP-V8 결합 | 70:30 결합이 test 세 지표 모두 개선 |
| PP-SVC4 | 70:30 결합 반복 holdout 검증 | `mape_guarded` 기준 70:30이 안정적으로 재선택 |
| PP-SVC5 | 다층 비교군 통계와 fallback 후보 검토 | 다층 원시 피처는 Huber 수렴 불안정 |
| PP-SVC6 | fallback 후보와 PP-V8 결합 비율 재검증 | 0.575~0.600 test는 좋으나 반복 안정성 부족 |

### 5.4 Cold 실험군

| 실험 | 목적 | 핵심 판단 |
|---|---|---|
| PP-W2 | 작가 메타 추가 | MdAPE `0.4497`로 기준선 개선 |
| PP-X3 | 전시/갤러리 활동성 추가 | MdAPE `0.4451` |
| PP-Y2 | 검색+전시/갤러리 통합 LightGBM Quantile | Cold 보수적 기준선 |
| PP-Y18 | qwidth 기반 구간 보정 | bootstrap/holdout 안정성이 확인된 검증 기준 후보 |
| PP-QR3 | qwidth와 q40/q50 차이 기반 guard/segment 보정 | test 기준 추가 개선 후보, 최종 교체 전 split 재검증 필요 |
| PP-Y16 | pred_bin x qwidth 보정 | Y계열 기존 후보 중 p95 방어 우수 |
| PP-Y21 | Cold 보정 후보 holdout 안정성 | 개선확률은 있으나 Warm 수준의 단일 확정 후보는 아님 |

## 6. 결과

### 6.1 Warm 결과

| 후보 | 설명 | MdAPE | MAPE | p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| Warm Huber baseline | 비교군 통계 없는 기준선 | 0.2274 | 0.4952 | 2.0130 | 후처리 전 기준 |
| `svc_numeric` | 비교군 숫자 통계 피처 추가 | 0.1528 | 0.2956 | 0.9694 | 대표 정확도 크게 개선 |
| `svc_full` | 숫자+범주 비교군 통계 추가 | 0.1496 | 0.2965 | 0.9499 | MdAPE 최저이나 최종 결합 전 후보 |
| `svc_numeric_seed_mean` | seed 평균 비교군 후보 | 0.1520 | 0.2942 | 0.9381 | 안정성 확인 |
| PP-V6 | 기존 fine blend | 0.1613 | 0.2889 | 0.9314 | 기존 비교 기준 |
| PP-V8 | 기존 compact blend | 0.1632 | 0.2816 | 0.9311 | MAPE/p95 방어 후보 |
| PP-SVC3 | `svc_numeric_seed_mean` 70% + PP-V8 30% | 0.1405 | 0.2748 | 0.8331 | Warm 최종 후보 |

핵심 해석:

- Huber baseline 대비 비교군 통계 추가로 MdAPE가 `0.2274 -> 0.1528`로 개선
- 비교군 후보는 대표 정확도 강점
- PP-V8은 대표 정확도는 낮지만 MAPE와 p95 방어 강점
- PP-SVC3는 두 후보의 장점을 로그 가격에서 결합

### 6.2 Warm 최종 결합 공식

```text
pred_log_final = 0.70 * pred_log_svc_numeric + 0.30 * pred_log_pp_v8
pred_price_final = exp(pred_log_final)
```

비율 해석:

- 70%: 비교군 통계 후보의 가격 중심선
- 30%: PP-V8의 평균오차/큰 오차 방어력
- 결합 공간: 실제 가격이 아니라 로그 가격
- 이유: 고가 작품의 과도한 영향 완화

Figure 5. Warm 최종 후보 PP-SVC3 결합 구조:

```text
svc_numeric_seed_mean
비교군 통계 피처를 사용한 Huber 후보
  - 강점: MdAPE 개선
  - 역할: 대표 가격 중심선
          |
          | 70%
          v
    로그 가격 결합 ----> pred_log_final ----> exp ----> 최종 예측 가격
          ^
          | 30%
          |
PP-V8 compact_blend_mape_guarded
기존 Warm compact blend 후보
  - 강점: MAPE/p95 방어
  - 역할: 평균오차와 큰 오차 완화
```

### 6.3 PP-SVC6 후보를 바로 채택하지 않은 이유

PP-SVC6 고정 test 결과:

| 후보 | MdAPE | MAPE | p95_APE | 해석 |
|---|---:|---:|---:|---|
| 기존 PP-SVC3 70:30 | 0.1405 | 0.2748 | 0.8331 | 현재 서비스 1순위 |
| `fallback + PP-V8`, `w=0.575` | 0.1348 | 0.2711 | 0.8362 | MdAPE/MAPE 개선, p95 소폭 악화 |
| `fallback + PP-V8`, `w=0.600` | 0.1362 | 0.2717 | 0.8329 | 세 지표 소폭 개선 |

보류 근거:

- `wsvc_0.70`과 `wfallback_0.600`은 기준 후보가 다름
- 고정 test에서는 0.575~0.600이 좋아 보임
- 반복 holdout 선택 중앙값은 `0.725~0.875`로 더 높은 비교군 비중을 선호
- selection/holdout 반복에서 0.575~0.600이 안정적으로 선택되지 않음
- 논문식 기준으로는 단일 test 개선보다 반복 검증 안정성을 우선

### 6.4 Cold 결과

| 후보 | 설명 | MdAPE | MAPE | p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| LightGBM baseline | 작품 조건 기준 | 0.4909 | 1.4131 | 4.8212 | 한계 큼 |
| PP-W2 | 작가 메타 추가 | 0.4497 | 1.1111 | 4.1587 | 작가 메타 효과 |
| PP-X3 | 전시/갤러리 활동성 추가 | 0.4451 | 1.1277 | 3.8935 | 활동성 피처 효과 |
| PP-Y2 | 검색+전시/갤러리 통합 | 0.4421 | 1.0484 | 3.3537 | 보수적 기준선 |
| PP-Y18 qwidth_bin | 불확실성 폭 구간 보정 | 0.4247 | 0.9910 | 3.3053 | Cold 검증 기준 후보 |
| PP-QR3 segment | qwidth + q40/q50 차이 기반 segment 보정 | 0.4175 | 1.0029 | 3.0018 | MdAPE 추가 개선 후보 |
| PP-QR3 guard | qwidth + LightGBM q40 guard 보정 | 0.4178 | 0.9640 | 2.5377 | MAPE/p95 추가 개선 후보 |
| PP-Y16 pred_x_qwidth | 예측값 구간 x 불확실성 구간 보정 | 0.4438 | 1.1083 | 2.8025 | Y계열 기존 p95 방어 후보 |

Cold 해석:

- 단계별 피처 추가와 보정으로 개선은 확인
- 하지만 Warm 대비 MdAPE, MAPE, p95 모두 높음
- 작가 기준선 부재가 구조적 한계
- 단일 확정 가격보다 참고 예측가, 넓은 가격 범위, 낮은 신뢰도 표시가 적합

Figure 6. Cold 최종 운영 정책 도식:

```text
Cold 입력 작품
  |
  v
LightGBM Quantile q50 예측
  |
  +-- q10~q90 가격 범위 산출
  +-- qwidth로 불확실성 구간 판단
  +-- qwidth_bin residual 보정
  |
  v
Cold 참고 예측가
  |
  +-- qwidth 작음: 참고 가능
  +-- qwidth 큼: 낮은 신뢰도, 넓은 범위, 수동 검수 flag
  |
  v
서비스 표시: 참고 예측가 + 가격 범위 + 비교군 통계 + 신뢰도
```

## 7. 모델 특성 기반 최종 선정 논리

### 7.1 Warm 선정 논리

Warm 최종 후보:

```text
Huber 중심선
+ 비교군 통계 피처
+ PP-V8 compact blend 방어 후보
+ 로그 가격 70:30 결합
= PP-SVC3
```

선정 근거:

- Huber는 Warm의 작가/크기 중심선을 선형 계수로 안정적으로 설명
- 비교군 통계는 작가/크기 중심선에 실제 시장 비교 기준을 추가
- direct median이 약했으므로 단순 중앙값 대체가 아닌 피처 학습 효과로 해석 가능
- PP-V8은 MAPE/p95 방어력이 있어 비교군 후보의 약점을 보완
- 반복 holdout에서 같은 결합 계열이 row `0.930`, artist `0.950` 비율로 유지
- 고정 test에서는 PP-SVC6 일부 후보도 매력적이었으나, 반복 검증 안정성 기준에서는 PP-SVC3 유지가 더 보수적인 선택

### 7.2 Cold 선정 논리

Cold 검증 기준 후보:

```text
LightGBM Quantile q50 점 예측
+ q10~q90 불확실성 범위
+ quantile_width 구간별 residual 보정
= PP-Y18 qwidth_bin_oof_min30_cap0.25
```

선정 근거:

- Cold는 동일 작가 기준선이 없어 Huber식 작가 계수 효과를 기대하기 어려움
- CatBoost는 조합 분리에 강하지만 단독 대표 모델로는 MdAPE가 `0.48`대 수준
- LightGBM Quantile은 불확실성 폭을 직접 산출해 Cold의 위험 구간을 설명 가능
- `qwidth_bin` 보정은 모델이 스스로 불확실하다고 본 구간에서 반복 residual을 줄이는 구조
- PP-QR3 guard/segment는 qwidth와 q40/q50 차이를 제한적으로 사용해 test 지표를 추가 개선
- 다만 PP-QR3는 최종 교체 전 동일 split 정책의 반복 재검증이 필요
- Cold 개선확률은 있으나 p95_APE가 여전히 높아 서비스에서는 확정 가격이 아닌 참고값으로 제공

## 8. 피처 영향도 해석 방법

### 8.1 Huber

해석 방법:

- 계수 확인
- 피처별 실제 기여도 확인
- group-drop으로 피처군 제거 시 성능 악화 확인

공식:

```text
contribution_j = beta_j * transformed_feature_j
pred_log_price = beta_0 + sum(contribution_j)
```

본 실험 해석:

- `artist_key`: 작가별 가격 기준선
- 크기 피처: 가격 중심선의 주요 조정축
- 비교군 통계: 시장 비교 기준을 보강하는 가격 중심선 피처

### 8.2 CatBoost

해석 방법:

- SHAP
- feature interaction
- leaf/segment별 residual
- 피처 제거 비교 실험

이유:

- CatBoost는 대칭 트리 조합 구조
- 단일 피처 하나의 독립 계수 해석이 어려움
- `medium_shape_bucket`, `depth_cm`, `support_category` 같은 조합 피처를 중심으로 해석해야 함

### 8.3 LightGBM Quantile

해석 방법:

- split importance
- permutation importance
- qwidth bin별 residual
- tail slice 분석

이유:

- LightGBM은 leaf-wise로 특정 오차 구간을 세밀하게 나눔
- Quantile은 q10/q50/q90을 통해 예측 범위와 불확실성을 제공
- Cold에서는 “정확한 단일 가격”보다 “불확실성이 큰 구간 식별”이 중요

## 9. 서비스 적용 방향

| 항목 | 적용 방향 |
|---|---|
| Warm 점 예측 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` 적용 |
| Warm 화면 | 예측 가격, 가격 범위, 비교군 통계 함께 표시 |
| Cold 점 예측 | 참고 예측가로만 표시 |
| Cold 화면 | 넓은 가격 범위, 낮은 신뢰도, 비교군 통계, 검수 flag |
| 비교군 통계 | 비교군 가격 중앙값, 범위, 매체별 분포, 표본 수 N 제공 |
| 호당가 | 기존 `estimated_ho` 산출식 기준으로 제공 |
| 외부 검색 | 실시간 기본값 비활성화, 캐시/수동 검수 중심 |

서비스 API에 포함할 모델 설명 필드:

```text
model_policy: warm_huber_pp_svc3 또는 cold_lgb_quantile_reference
postprocessing_policy: svc_blend_070 또는 qwidth_bin_oof_min30_cap025
routing_reason: warm_artist_seen 또는 cold_artist_unseen
uncertainty_level: low / medium / high
comparable_group_level: 비교군 fallback 단계
comparable_sample_count: 비교군 표본 수 N
```

## 10. 한계와 후속 검증

한계:

- Warm 최종 결합은 저장된 예측 산출물 기반 결합으로 검증
- 운영 파이프라인에서 `svc_numeric`과 PP-V8 산출물을 재현하는 테스트 필요
- PP-SVC1 비교군 통계 실험 일부 split에서는 면적 단가를 대체 사용
- Cold는 p95_APE가 높아 단일 확정 가격으로는 위험
- 외부 검색 피처는 동명이인, 검색 provider 차이, 수집 시점 변동성 존재

후속 검증:

- Warm 운영 산출물 재현성 테스트
- 기존 `estimated_ho` 기준으로 호당가 통계 재계산 및 서비스 표시 검증
- Cold qwidth 기반 신뢰도 표시 정책 검증
- 외부 검색 피처 캐시/검수 정책 확정
- Cold CatBoost segment residual 보정의 제한적 재검증

## 11. 결론

최종 결론:

- Warm은 Huber가 모델 구조상 적합
- 이유: 같은 작가 이력이 있어 작가 기준선 계수 해석 가능
- Huber의 이상치 방어 손실은 미술품 가격의 극단값에 적합
- 비교군 통계 피처는 단순 표시값이 아니라 예측 성능 개선 피처로 검증
- PP-SVC3는 비교군 통계 후보의 대표 정확도와 PP-V8의 평균오차/큰 오차 방어력을 결합
- PP-SVC6의 일부 test 개선 후보는 반복 안정성이 부족해 보류
- Cold는 LightGBM Quantile 기반 qwidth 보정이 안정성 검증 기준 후보
- PP-QR3 guard/segment 보정은 test 지표를 추가 개선했지만 최종 교체 전 split 재검증 필요
- Cold는 작가 기준선 부재와 높은 p95 위험 때문에 확정 가격이 아니라 참고 예측가와 범위로 제공

최종 선택:

| 구분 | 선택 |
|---|---|
| Warm 서비스 1순위 | `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70` |
| Cold 검증 기준 참고 후보 | `PP-Y18 qwidth_bin_oof_min30_cap0.25` |
| Cold 추가 개선 참고 후보 | `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50`, `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` |
| Cold Y계열 큰 오차 방어 참고 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` |
| 서비스 정책 | Warm 점 예측, Cold 참고값/범위/낮은 신뢰도 |

## 부록 A. 내부 후보명 해석

| 내부명 | 해석 |
|---|---|
| `PP-SVC3` | Warm 비교군 통계 후보와 PP-V8을 결합한 최종 후보 실험 |
| `blend_svcnum_ppv8_wsvc_0.70` | 비교군 숫자 통계 후보 70% + PP-V8 30% |
| `PP-V8` | 기존 Warm compact blend 후보, MAPE/p95 방어 역할 |
| `compact_blend_mape_guarded` | 핵심 후보만 남긴 단순 결합, MdAPE를 크게 해치지 않는 조건에서 MAPE 낮은 후보 |
| `svc_numeric` | 비교군 숫자 통계 피처만 Huber에 추가 |
| `svc_full` | 비교군 숫자 통계와 범주 통계를 함께 추가 |
| `fallback_numeric` | 가장 신뢰 가능한 비교군 하나를 fallback 순서로 고른 숫자 통계 후보 |
| `PP-Y18 qwidth_bin_oof_min30_cap0.25` | Cold 불확실성 폭 구간별 residual 보정 후보 |
| `PP-QR3 guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | qwidth가 크고 LightGBM q40 기준으로 과대 예측 위험이 있는 구간을 제한 보정한 후보 |
| `PP-QR3 segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | qwidth와 기존 예측값-q40/q50 차이를 segment로 묶어 median residual을 제한 보정한 후보 |
| `qwidth` | q90과 q10 사이의 로그 가격 폭 |
| `oof` | 자기 자신을 직접 맞히지 않은 교차검증 예측값 |
| `min30` | 구간 표본 최소 30개 조건 |
| `cap0.25` | 로그 보정값 ±0.25 제한 |

## 부록 B. 보고용 핵심 문장

- Warm은 같은 작가의 과거 거래 이력이 있어 Huber의 선형 작가 기준선이 구조적으로 적합
- Huber 손실은 큰 오차 샘플의 영향력을 완만하게 처리해 미술품 가격의 이상치에 강건
- 비교군 통계는 단순 중앙값 대체가 아니라 Huber의 작가/크기 계수와 함께 학습되는 시장 기준 피처
- 최종 Warm 후보는 비교군 통계 후보 70%와 PP-V8 방어 후보 30%를 로그 가격에서 결합
- PP-V8은 대표 정확도보다는 MAPE/p95 방어력이 좋아 보조 후보로 사용
- Cold는 작가 기준선이 없어 CatBoost/LightGBM이 피처 조합과 불확실성 구간을 학습해야 하는 문제
- Cold에서는 LightGBM Quantile의 q10/q50/q90 구조가 가격 범위와 신뢰도 설명에 가장 적합
- 따라서 Warm은 서비스 점 예측, Cold는 참고 예측가와 넓은 가격 범위로 제공
