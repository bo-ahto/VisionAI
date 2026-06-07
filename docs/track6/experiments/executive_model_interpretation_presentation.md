# Track6 가격 예측 모델 해석 및 후처리 계획 발표자료

- 발표 대상: 상사 및 임원
- 작성일: 2026-05-31
- 기준 문서: `supervisor_model_feature_postprocessing_report.md`

---

## 1. 오늘 보고의 핵심

- 가격 예측 모델을 단순히 “성능이 높은 모델”로만 보지 않고, 왜 그런 예측을 하는지까지 검증했다.
- Warm과 Cold는 데이터 조건이 다르기 때문에 서로 다른 모델과 해석 방식을 적용했다.
- 피처 영향도는 모델 구조에 맞게 다르게 해석했다.
- 후처리도 하나의 공통 보정이 아니라 모델별 약점에 맞춰 다르게 설계해야 한다.

**임원용 한 줄 결론**

현재 모델은 설명 가능한 수준까지 해석 근거를 확보했으며, 후처리는 Warm은 적용 후보, Cold는 tail risk를 줄이는 방향으로 추가 검증이 필요하다.

---

## 2. Warm과 Cold를 나눈 이유

| 구분 | 의미 | 모델 방향 |
| --- | --- | --- |
| Warm | 학습 데이터에 같은 작가가 존재하는 경우 | 작가 이력과 작품 특성을 함께 사용 |
| Cold | 처음 보는 작가 또는 작가 이력이 부족한 경우 | 작품 자체의 물리 정보와 재료/형태 중심 |

**핵심 메시지**

- Warm은 “이 작가가 과거에 어느 가격대였는가”를 활용할 수 있다.
- Cold는 작가 이력이 없기 때문에 “작품 자체가 어떤 조건인가”를 더 강하게 본다.
- 그래서 Warm과 Cold는 같은 피처라도 영향이 다르게 나타나는 것이 정상이다.

---

## 3. 최종 모델 구성

| 영역 | 최종 모델 | 선택 피처 조합 |
| --- | --- | --- |
| Warm | HuberRegressor | `size + medium_support + artist_key` |
| Cold | CatBoost | `size + depth_3d + medium/shape` |
| Cold | LightGBM | `area/size + support_size_bucket` |

**선택 기준**

- 성능 지표만 본 것이 아니라, 모델 안에서 실제로 어떤 피처가 가격을 움직였는지 확인했다.
- 피처 조합이 모델 구조와 맞는지 확인했다.
- 후처리 기준으로 사용할 수 있는 반복 오차가 있는지 확인했다.

---

## 4. 기준 성능 요약

기준 성능은 최종 artifact를 직접 재해석한 test 기준이다.

| 모델 | Test MdAPE | Test p95 APE | 해석 |
| --- | ---: | ---: | --- |
| Warm Huber | 0.2241 | 2.0209 | 대표 오차는 가장 안정적 |
| Cold CatBoost | 0.4843 | 4.4183 | Cold 조건에서 비교적 균형적 |
| Cold LightGBM | 0.4797 | 5.0569 | 대표 오차는 유사하나 큰 오차 위험이 큼 |

**읽는 방법**

- MdAPE는 일반적인 예측 오차 수준이다.
- p95 APE는 크게 틀리는 상위 위험 구간이다.
- Cold 모델은 Warm보다 어렵다. 작가 이력이 없기 때문에 가격 기준선을 잡기 어렵다.

---

## 5. Warm Huber는 가격을 어떻게 계산하는가

Warm Huber는 로그 가격을 선형식으로 계산한 뒤 원 가격으로 되돌린다.

```text
pred_log_price = intercept + sum(beta_j * feature_j)
pred_price = exp(pred_log_price)
```

Huber의 특징은 큰 오차 샘플에 과하게 끌려가지 않는다는 점이다.

```text
작은 오차: 제곱 손실로 정밀하게 학습
큰 오차: 선형 손실로 완화해서 이상치 영향 축소
```

**의미**

- 피처별 계수와 실제 기여도를 직접 설명할 수 있다.
- 고가/저가 이상치가 일부 있어도 모델이 과도하게 흔들리지 않는다.

---

## 6. Warm Huber에서 중요한 피처와 이유

| 피처 | 관측 결과 | 근본 원인 |
| --- | --- | --- |
| 작품 크기 | contribution 1위 | 같은 작가라도 큰 작품과 작은 작품은 가격대가 달라짐 |
| 재료/지지체 조합 | contribution 2위 | 같은 크기라도 캔버스/종이/재료 조합이 시장 가격대를 바꿈 |
| 작가 식별값 | Warm 전용 핵심 피처 | 기존 작가의 과거 가격대가 기준선 역할을 함 |
| 깊이/형태 | Warm에서는 낮음 | 선형 모델에서는 조합 효과를 직접 만들기 어려움 |

**중요한 해석**

`area_cm2`가 음수 방향으로 보인 것은 면적이 가격을 낮춘다는 뜻이 아니다.  
`log_area`, `width_cm`, `height_cm`과 정보가 겹치기 때문에 선형 모델 안에서 과대 상승을 조정하는 역할로 해석해야 한다.

---

## 7. Cold CatBoost는 가격을 어떻게 계산하는가

CatBoost는 여러 개의 대칭 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + sum(tree_leaf_value)
pred_price = exp(pred_log_price)
```

CatBoost의 핵심은 대칭 트리 구조다.

- 같은 깊이의 노드가 같은 조건으로 나뉜다.
- 단일 피처보다 피처 조합과 분기 경로가 중요하다.
- 범주형 피처를 비교적 안정적으로 처리한다.

---

## 8. Cold CatBoost에서 중요한 피처와 이유

| 피처/조합 | 관측 결과 | 근본 원인 |
| --- | --- | --- |
| 크기 피처 | SHAP 상위 1~4위 | 작가 이력이 없으므로 작품 크기가 가격 기준선 역할 |
| depth_cm | SHAP 5위, interaction 상위 | 2D/3D, 오브제성, 설치 가능성을 구분 |
| width x depth | interaction 1위 | 큰 평면 작품과 큰 입체 작품을 다른 가격 경로로 분리 |
| medium/support | 중위권이지만 조합에서 중요 | 재료와 지지체가 depth/size의 의미를 바꿈 |

**중요한 해석**

CatBoost에서 `width_cm`이 높다는 것은 “가로가 길면 무조건 비싸다”가 아니다.  
특정 크기 구간으로 들어가는 트리 경로가 달라지고, 그 경로에서 예측 가격이 바뀐다는 의미다.

---

## 9. Cold LightGBM은 가격을 어떻게 계산하는가

LightGBM도 여러 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + learning_rate * sum(tree_leaf_value)
pred_price = exp(pred_log_price)
```

LightGBM의 핵심은 leaf-wise 성장 방식이다.

- 손실을 크게 줄일 수 있는 leaf를 우선적으로 깊게 확장한다.
- 평균 성능은 좋아질 수 있다.
- 대신 일부 좁은 구간에서 큰 오차가 생길 수 있다.

---

## 10. Cold LightGBM에서 중요한 피처와 이유

| 피처/구간 | 관측 결과 | 근본 원인 |
| --- | --- | --- |
| area_cm2 | permutation 영향 최대 | 면적 기준 split이 가격 구간을 강하게 나눔 |
| width/height/log_area | 상위권 | 면적 외 형태 차이를 보완 |
| canvas__q5 | p95 APE 최상위 | 대형 캔버스는 가격 분산이 커 큰 오차가 발생 |
| acrylic | tail 위험 구간 | 표본은 많지만 내부 가격 편차가 큼 |

**중요한 해석**

LightGBM은 면적을 강하게 본다.  
이것은 평균 예측에는 도움이 되지만, 대형 작품처럼 가격 편차가 큰 구간에서는 큰 오차 위험으로 이어진다.

---

## 11. 피처 조합은 어떻게 찾았는가

1. 여러 피처 조합을 validation에서 비교했다.
2. 후보 조합을 locked test에서 확인했다.
3. 최종 artifact 기준으로 해석 산출물을 다시 만들었다.
4. 모델 구조에 맞는 영향도 지표를 사용했다.
5. 반복 오차가 있는 구간을 후처리 후보로 연결했다.

| 모델 | 최종 조합 | 조합 이유 |
| --- | --- | --- |
| Warm Huber | size + medium_support + artist_key | 선형 contribution에서 핵심 축 |
| CatBoost | size + depth + medium/shape | 대칭 트리 interaction에서 핵심 조합 |
| LightGBM | area/size + support_size_bucket | leaf-wise tail risk에서 핵심 구간 |

---

## 12. 후처리 방향

| 모델 | 현재 판단 | 후처리 방향 |
| --- | --- | --- |
| Warm Huber | 채택 후보 | 전체/예측구간 로그 잔차 보정 |
| Cold CatBoost | 단순 보정 보류 | leaf/segment residual + fallback |
| Cold LightGBM | 조건부 후보 | pred_log bin + size/support bucket tail 안정화 |

**핵심 메시지**

- 모든 모델에 같은 보정을 적용하면 안 된다.
- Warm은 선형 편향 보정이 자연스럽다.
- CatBoost는 트리 경로와 segment 기반 보정이 맞다.
- LightGBM은 큰 오차 구간을 안정화하는 보정이 맞다.

---

## 13. 1차 후처리 실험 결과

아래 표는 1차 residual calibration 실험의 baseline 기준이다.  
슬라이드 4의 최종 artifact 재해석 수치와 소폭 차이가 있으므로, 여기서는 보정 전후의 방향성을 판단하는 용도로 사용한다.

| 영역 | Baseline MdAPE | 보정 후 후보 MdAPE | Baseline p95 | 보정 후 후보 p95 | 판단 |
| --- | ---: | ---: | ---: | ---: | --- |
| Warm | 0.2274 | 0.2211 | 2.0130 | 1.9736 | 채택 후보 |
| CatBoost | 0.4839 | 0.4880 | 4.7974 | 3.9490 | MdAPE 악화로 보류 |
| LightGBM | 0.4859 | 0.4873 | 4.7612 | 4.2199 | tail 안정화 후보 |

**해석**

- Warm은 대표 오차와 큰 오차가 모두 개선 가능하다.
- CatBoost는 단순 median 보정으로는 대표 오차가 나빠진다.
- LightGBM은 대표 오차를 크게 해치지 않는 범위에서 큰 오차를 줄이는 방향이 맞다.

---

## 14. 향후 실행 계획

| 단계 | 작업 | 목적 |
| --- | --- | --- |
| 1 | Warm PP-A1-W 확정 검증 | 로그 잔차 보정 적용 가능성 확인 |
| 2 | CatBoost segment fallback 실험 | 대칭 트리 구조에 맞는 보정 검증 |
| 3 | LightGBM tail 안정화 실험 | p95 큰 오차 완화 |
| 4 | 공통 신뢰도/가격 범위 표시 | 위험 구간에서 점예측 한계 보완 |

**검증 원칙**

보정값은 test 데이터에서 만들지 않는다.  
validation 또는 OOF에서 보정값을 만들고, locked test는 최종 확인에만 사용한다.

---

## 15. 최종 의사결정 요청

- Warm Huber 후처리 보정은 적용 후보로 두고 검증을 진행한다.
- Cold CatBoost는 단순 보정이 아니라 segment fallback 방식으로 재실험한다.
- Cold LightGBM은 tail risk 완화 목적의 보정 실험을 진행한다.
- 모델 설명 자료는 최종 artifact 기준 해석 리포트로 교체한다.

**임원 의사결정 포인트**

정확도 개선만 볼 것이 아니라, 예측이 크게 틀릴 수 있는 구간을 식별하고 신뢰도/범위 표시까지 포함하는 방향으로 운영 안정성을 높인다.
