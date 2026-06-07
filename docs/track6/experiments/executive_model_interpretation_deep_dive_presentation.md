# Track6 가격 예측 모델 상세 해석 및 후처리 계획 발표자료

- 발표 대상: 상사 및 임원
- 작성일: 2026-06-01
- 예상 발표 시간: 25~30분
- 목적: 가격예측 로직, 피처별 영향도 계산 방식, 모델 특성에 따른 해석과 후처리 계획을 임원도 이해할 수 있게 설명한다.

---

## 1. 오늘 보고의 목적

- 단순히 “어떤 모델의 성능이 높다”가 아니라, 모델이 가격을 어떤 로직으로 계산하는지 설명한다.
- 피처 영향도를 모델별로 어떻게 계산했는지 설명한다.
- 수치가 높고 낮게 나온 원인을 모델 구조와 데이터 특성으로 해석한다.
- 그 해석을 바탕으로 피처 조합과 후처리 방향을 제안한다.

**오늘의 결론**

Warm은 선형 Huber 특성상 피처별 기여도를 직접 설명할 수 있고, Cold는 CatBoost와 LightGBM의 트리 구조 차이에 맞춰 서로 다르게 해석해야 한다.

---

## 2. 전체 가격 예측 흐름

```text
작품 정보 입력
  → Warm/Cold 조건 분리
  → 모델별 log(price) 예측
  → exp 변환으로 원 가격 복원
  → 모델별 후처리 보정
  → 최종 가격/신뢰도/위험 구간 제시
```

**왜 log(price)를 예측하는가**

- 미술품 가격은 낮은 가격부터 매우 높은 가격까지 범위가 넓다.
- 원 가격을 그대로 예측하면 고가 작품의 영향이 과도해진다.
- 로그 가격으로 바꾸면 가격 차이를 비율 관점으로 안정적으로 학습할 수 있다.

---

## 3. Warm과 Cold를 분리한 이유

| 구분 | 데이터 조건 | 가격 판단의 핵심 |
| --- | --- | --- |
| Warm | 같은 작가가 과거 데이터에 있음 | 작가의 과거 가격대 + 작품 특성 |
| Cold | 처음 보는 작가 또는 작가 이력 부족 | 작품 크기, 재료, 지지체, 형태 |

**핵심**

Warm은 작가의 과거 가격대가 기준선 역할을 한다.  
Cold는 작가 기준선이 없기 때문에 작품 자체 정보가 가격 기준선 역할을 한다.

---

## 4. 최종 모델과 피처 조합

| 영역 | 모델 | 최종 피처 조합 | 이유 |
| --- | --- | --- | --- |
| Warm | HuberRegressor | `size + medium_support + artist_key` | 선형 기여도에서 핵심 축 |
| Cold | CatBoost | `size + depth_3d + medium/shape` | 대칭 트리 interaction에서 핵심 조합 |
| Cold | LightGBM | `area/size + support_size_bucket` | leaf-wise tail risk에서 핵심 구간 |

**선정 기준**

- validation 성능
- locked test 확인
- 최종 artifact 기준 영향도 재산출
- 모델 구조와 해석 지표의 일치성
- 후처리 기준으로 쓸 수 있는 반복 오차 존재 여부

---

## 5. 성능 지표를 어떻게 읽는가

| 지표 | 의미 | 발표에서의 해석 |
| --- | --- | --- |
| MdAPE | 중앙값 기준 절대 비율 오차 | 일반적인 예측 오차 수준 |
| p95 APE | 상위 5% 큰 오차 수준 | 크게 틀리는 위험 구간 |
| RMSE_log | 로그 가격 기준 평균 오차 | 가격 비율 관점의 전체 흔들림 |
| Within_30 | 30% 이내 예측 비율 | 운영 체감 정확도 |

**중요**

평균 성능이 비슷해도 p95가 높으면 운영에서는 위험하다.  
가격 예측은 대표 오차와 큰 오차 위험을 함께 봐야 한다.

---

## 6. 기준 성능 요약

기준 성능은 최종 artifact를 직접 재해석한 test 기준이다.

| 모델 | Test MdAPE | Test p95 APE | 해석 |
| --- | ---: | ---: | --- |
| Warm Huber | 0.2241 | 2.0209 | 대표 오차가 가장 안정적 |
| Cold CatBoost | 0.4843 | 4.4183 | Cold 조건에서 비교적 균형적 |
| Cold LightGBM | 0.4797 | 5.0569 | 대표 오차는 유사하나 큰 오차 위험이 큼 |

**해석**

Cold는 작가 이력이 없기 때문에 Warm보다 어렵다.  
LightGBM은 MdAPE는 CatBoost와 비슷하지만 p95가 높아 tail 관리가 필요하다.

---

## 7. Warm Huber 가격 계산 공식

Warm Huber는 로그 가격을 선형식으로 계산한다.

```text
z_num = StandardScaler(x_num)
z_cat = OneHotEncoder(x_cat)

pred_log_price = intercept + Σ(beta_j × z_j)
pred_price = exp(pred_log_price)
```

**의미**

- 각 피처는 `beta_j × z_j`만큼 로그 가격을 올리거나 내린다.
- 그래서 Huber는 피처별 영향도를 직접 계산할 수 있다.
- 최종 가격은 로그 가격을 `exp`로 원 가격으로 되돌린 값이다.

---

## 8. Huber 손실 함수와 모델 특성

Huber는 일반 선형 회귀와 달리 큰 오차를 완화한다.

```text
residual = actual_log_price - pred_log_price

작은 residual: 제곱 손실
큰 residual: 선형 손실
```

수식으로는 다음과 같이 볼 수 있다.

```text
loss(u) =
  0.5 × u²                         if |u| <= epsilon
  epsilon × |u| - 0.5 × epsilon²    if |u| > epsilon
```

**왜 이 모델이 적합한가**

- 미술품 가격에는 특이하게 비싸거나 싼 사례가 있다.
- Huber는 이런 이상치에 과하게 끌려가지 않는다.
- 따라서 Warm 조건에서 안정적인 선형 설명이 가능하다.

---

## 9. Warm Huber 피처 영향도 계산 방법

| 계산 항목 | 계산 방식 | 해석 |
| --- | --- | --- |
| 계수 | `beta_j` | 피처가 로그 가격을 올리는지/내리는지 |
| 원 단위 환산 계수 | `beta_j / scale_j` | cm, 면적 단위 기준 영향 |
| 샘플별 기여도 | `beta_j × z_ij` | 특정 작품에서 해당 피처가 예측값에 준 영향 |
| 평균 절대 기여도 | `mean(abs(beta_j × z_ij))` | 전체 test에서 영향의 크기 |
| 범주형 centered contribution | `active_rate × centered_coef` | one-hot 기준 왜곡을 줄인 범주 영향 |

**핵심**

계수가 큰 피처와 실제 영향이 큰 피처는 다를 수 있다.  
따라서 계수만 보지 않고 실제 test contribution을 함께 봤다.

---

## 10. Warm Huber 피처 영향 결과

| 피처/그룹 | 결과 | 원인 |
| --- | --- | --- |
| size | contribution 1위 | 같은 작가라도 크기에 따라 가격대가 달라짐 |
| medium_support | contribution 2위 | 재료와 지지체 조합이 작품 유형과 시장 가격대를 반영 |
| artist_key | 주요 설명 축 | 기존 작가의 과거 가격대가 기준선 역할 |
| depth/shape | 낮은 영향 | 선형 모델에서는 조합 효과가 직접 표현되지 않음 |

**중요 해석**

`area_cm2`의 음의 계수는 면적이 가격을 낮춘다는 뜻이 아니다.  
`log_area`, `width_cm`, `height_cm`와 중복된 크기 정보 사이에서 과대 상승을 조정하는 역할이다.

---

## 11. Warm Huber 조합 판단

| 조합 요소 | 채택 이유 | 후처리 의미 |
| --- | --- | --- |
| size | 가장 큰 실제 기여도 | size bucket 편향 확인 |
| medium_support | 크기 다음 설명 축 | 재료/지지체 조합별 residual 확인 |
| artist_key | Warm 전용 가격 기준선 | 저이력 작가 신뢰도 표시 |

**결론**

Warm에서는 `size + medium_support + artist_key` 조합이 성능뿐 아니라 설명 가능성 측면에서도 가장 타당하다.

---

## 12. Cold CatBoost 가격 계산 공식

CatBoost는 여러 개의 대칭 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + Σ leaf_value_t(x)
pred_price = exp(pred_log_price)
```

**트리 예측 과정**

1. 작품 피처가 트리의 조건을 따라 이동한다.
2. 각 트리에서 하나의 leaf에 도달한다.
3. 해당 leaf의 값들이 모두 더해진다.
4. 더해진 로그 가격을 원 가격으로 변환한다.

---

## 13. CatBoost 모델 특성

CatBoost는 대칭 트리, 즉 Oblivious Tree 구조를 사용한다.

| 특성 | 의미 | 해석 영향 |
| --- | --- | --- |
| 대칭 트리 | 같은 depth에서 동일 split 조건 사용 | 피처 조합과 경로 해석이 중요 |
| ordered boosting | 데이터 순서를 고려해 누수 완화 | 범주형 평균 가격 정보 과적합 완화 |
| 범주형 처리 | 범주형 피처를 안정적으로 처리 | medium/support 해석에 유리 |

**핵심**

CatBoost는 단일 피처가 아니라 `어떤 조건 조합으로 어떤 leaf에 들어갔는가`가 중요하다.

---

## 14. CatBoost 피처 영향도 계산 방법

| 계산 항목 | 계산 방식 | 해석 |
| --- | --- | --- |
| PredictionValuesChange | 피처 split이 예측값을 얼마나 바꿨는지 | 전반적 중요도 |
| SHAP | 각 샘플 예측에서 피처가 기여한 로그가격 변화 | 피처별 영향 방향과 크기 |
| mean_abs_shap | `mean(abs(shap_j))` | 전체 test에서 영향 크기 |
| interaction score | 두 피처가 같은 예측 경로에서 함께 만든 변화 | 피처 조합 중요도 |
| leaf residual | leaf/segment별 실제값-예측값 잔차 | 후처리 후보 |

**핵심**

CatBoost는 SHAP 상위 피처와 interaction 상위 조합을 함께 봐야 한다.

---

## 15. CatBoost 피처 영향 결과

| 피처/조합 | 결과 | 원인 |
| --- | --- | --- |
| width/area/log_area/height | SHAP 상위 1~4위 | Cold에서는 크기가 가격 기준선 역할 |
| depth_cm | SHAP 5위, interaction 상위 | 2D/3D, 오브제성, 설치 가능성 구분 |
| width × depth | interaction 1위 | 큰 평면과 큰 입체 작품을 다른 경로로 분리 |
| depth × medium | interaction 상위 | 입체성의 가격 의미가 재료에 따라 달라짐 |

**중요**

`width_cm`이 높다는 것은 “가로가 길면 무조건 비싸다”가 아니다.  
특정 크기 구간으로 들어가는 트리 경로가 예측값을 바꾼다는 뜻이다.

---

## 16. CatBoost 조합 판단

| 조합 요소 | 채택 이유 | 후처리 의미 |
| --- | --- | --- |
| size | Cold에서 가격 기준선 역할 | size segment residual |
| depth_3d | size와 강한 interaction | size-depth segment |
| medium/shape | depth의 의미를 바꾸는 조절 변수 | medium_shape fallback |

**결론**

CatBoost는 `size + depth_3d + medium/shape` 조합으로 설명해야 하며, 보정도 leaf/segment 기반으로 설계해야 한다.

---

## 17. Cold LightGBM 가격 계산 공식

LightGBM도 여러 트리를 더해 로그 가격을 예측한다.

```text
pred_log_price = base_score + learning_rate × Σ leaf_value_t(x)
pred_price = exp(pred_log_price)
```

**트리 예측 과정**

1. 작품 피처가 split 조건을 따라 leaf로 이동한다.
2. 각 트리의 leaf 값이 더해진다.
3. learning_rate가 적용된다.
4. 로그 가격을 원 가격으로 복원한다.

---

## 18. LightGBM 모델 특성

LightGBM은 leaf-wise 방식으로 트리를 성장시킨다.

| 특성 | 의미 | 해석 영향 |
| --- | --- | --- |
| leaf-wise 성장 | 손실 감소가 큰 leaf를 우선 확장 | 일부 구간을 깊게 파고듦 |
| 강한 연속형 split | 면적/크기 같은 연속 피처를 잘 활용 | area_cm2 의존도 증가 |
| tail risk | 좁은 구간에서 큰 오차 가능 | p95와 slice 진단 필요 |

**핵심**

LightGBM은 평균 성능이 좋아 보여도, 특정 구간의 큰 오차를 반드시 확인해야 한다.

---

## 19. LightGBM 피처 영향도 계산 방법

| 계산 항목 | 계산 방식 | 해석 |
| --- | --- | --- |
| split importance | 트리에서 피처가 split에 사용된 횟수 | 자주 사용된 피처 |
| permutation delta | 피처 값을 섞었을 때 오차가 얼마나 악화되는지 | 실제 예측 의존도 |
| MdAPE_delta | permutation 후 MdAPE 증가분 | 대표 오차 영향 |
| p95_APE_delta | permutation 후 p95 증가분 | 큰 오차 영향 |
| tail slice | 특정 구간의 p95/MdAPE | 운영 위험 구간 |
| leaf-wise 진단 | leaf별 worst MdAPE | 과분화 위험 확인 |

**핵심**

LightGBM은 split importance만 보면 부족하다.  
permutation과 tail slice를 함께 봐야 실제 위험을 설명할 수 있다.

---

## 20. LightGBM 피처 영향 결과

| 피처/구간 | 결과 | 원인 |
| --- | --- | --- |
| area_cm2 | permutation 영향 최대 | 면적 기준 split이 가격 구간을 강하게 나눔 |
| width/height/log_area | 상위권 | 면적 외 형태 차이를 보완 |
| canvas__q5 | p95 APE 최상위 | 대형 캔버스는 가격 분산이 큼 |
| acrylic | tail 위험 구간 | 표본은 많지만 내부 가격 편차가 큼 |

**중요**

LightGBM의 면적 의존성은 평균 예측에는 도움이 되지만, 대형 작품 구간에서는 큰 오차 위험으로 이어진다.

---

## 21. LightGBM 조합 판단

| 조합 요소 | 채택 이유 | 후처리 의미 |
| --- | --- | --- |
| area/size | permutation 영향 최대 | size/pred bin 안정화 |
| support_size_bucket | 대형 캔버스 tail risk | support-size 구간 보정 |
| medium × size | 특정 재료의 내부 가격 분산 | medium-size slice 확인 |

**결론**

LightGBM은 대표 오차보다 tail risk 관리가 중요하므로 `area/size + support_size_bucket` 중심으로 해석하고 보정해야 한다.

---

## 22. 모델별 영향도 계산 방식 비교

| 모델 | 가격 계산 방식 | 영향도 계산 | 핵심 해석 단위 |
| --- | --- | --- | --- |
| Huber | 선형식 | 계수, contribution | 피처별 직접 기여도 |
| CatBoost | 대칭 트리 합산 | SHAP, interaction, leaf residual | 피처 조합과 경로 |
| LightGBM | leaf-wise 트리 합산 | permutation, tail slice, leaf 진단 | 의존도와 위험 구간 |

**핵심**

모두 가격을 예측하지만, 피처 영향도를 계산하고 해석하는 방식은 서로 다르다.

---

## 23. 피처 조합을 찾은 과정

1. 여러 feature set을 validation에서 비교했다.
2. 후보 조합을 locked test에서 확인했다.
3. 최종 artifact 기준으로 해석 산출물을 다시 만들었다.
4. 모델별 특성에 맞는 영향도 지표를 사용했다.
5. 반복 오차가 있는 구간을 후처리 후보로 연결했다.

**원칙**

좋은 조합은 성능만 좋은 조합이 아니라, 모델 안에서 실제로 예측값을 움직이고 후처리 기준으로도 쓸 수 있는 조합이다.

---

## 24. 1차 후처리 실험 결과

아래 표는 1차 residual calibration 실험의 baseline 기준이다.  
최종 artifact 재해석 수치와 소폭 차이가 있으므로, 보정 전후 방향성을 판단하는 용도로 사용한다.

| 영역 | Baseline MdAPE | 후보 MdAPE | Baseline p95 | 후보 p95 | 판단 |
| --- | ---: | ---: | ---: | ---: | --- |
| Warm | 0.2274 | 0.2211 | 2.0130 | 1.9736 | 채택 후보 |
| CatBoost | 0.4839 | 0.4880 | 4.7974 | 3.9490 | MdAPE 악화로 보류 |
| LightGBM | 0.4859 | 0.4873 | 4.7612 | 4.2199 | tail 안정화 후보 |

---

## 25. 모델별 후처리 설계

| 모델 | 보정 방향 | 이유 |
| --- | --- | --- |
| Warm Huber | overall/pred_bin median residual | 선형 로그가격 예측이므로 편향을 로그 공간에서 더하는 방식이 자연스러움 |
| CatBoost | leaf/segment residual + fallback | 대칭 트리 경로와 interaction segment에서 반복 오차 확인 필요 |
| LightGBM | pred_log bin + size/support bucket | leaf-wise tail risk가 커서 위험 구간 안정화 필요 |

**중요**

테스트 데이터로 보정값을 만들면 안 된다.  
보정값은 validation 또는 OOF에서 만들고, test는 최종 확인에만 사용한다.

---

## 26. 후처리 보정식

공통적으로 로그 공간에서 residual을 계산한다.

```text
residual_log = actual_log_price - pred_log_price
correction = median(residual_log)
corrected_pred_log = pred_log_price + correction
corrected_price = exp(corrected_pred_log)
```

**모델별 차이**

- Warm: 전체 또는 예측 구간별 median residual
- CatBoost: leaf/segment별 median residual, 부족하면 fallback
- LightGBM: pred_bin, size_bucket, support_size_bucket 기준 tail 안정화

---

## 27. 향후 실행 계획

| 단계 | 작업 | 목적 |
| --- | --- | --- |
| 1 | Warm PP-A1-W 확정 검증 | 로그 잔차 보정 적용 가능성 확인 |
| 2 | CatBoost segment fallback 실험 | 대칭 트리 구조에 맞는 보정 검증 |
| 3 | LightGBM tail 안정화 실험 | p95 큰 오차 완화 |
| 4 | 공통 신뢰도/가격 범위 표시 | 위험 구간에서 점예측 한계 보완 |

---

## 28. 최종 의사결정 요청

- Warm Huber 후처리 보정은 적용 후보로 두고 검증을 진행한다.
- Cold CatBoost는 단순 보정이 아니라 segment fallback 방식으로 재실험한다.
- Cold LightGBM은 tail risk 완화 목적의 보정 실험을 진행한다.
- 모델 설명 자료는 최종 artifact 기준 해석 리포트로 교체한다.

**의사결정 포인트**

정확도 개선뿐 아니라 크게 틀릴 수 있는 구간을 식별하고, 신뢰도와 가격 범위 표시까지 포함하는 방향으로 운영 안정성을 높인다.
