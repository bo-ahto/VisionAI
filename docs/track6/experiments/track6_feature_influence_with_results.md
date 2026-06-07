# Track6 피처별 영향도 해석 및 실험 결과

- 작성일: 2026-06-01
- 목적: 모델별 피처 영향도를 단순 설명이 아니라 실제 실험 결과와 함께 해석한다.
- 연결 문서: `track6_junior_project_onboarding.md`
- 핵심 원칙: 피처 영향도는 모델 구조에 맞게 해석하고, 가능하면 실제 제거 실험이나 permutation 결과와 함께 본다.

이 문서에서 쓰는 주요 용어는 다음과 같다.

| 용어 | 쉬운 설명 |
| --- | --- |
| artifact | 학습이 끝난 뒤 저장된 모델 산출물. 모델 파일, 피처 목록, 전처리 설정을 포함한다. |
| final artifact | 현재 기준으로 최종 사용하기로 한 저장 모델 산출물이다. |
| validation | 모델이나 피처 후보를 고르는 중간 검증 데이터다. |
| test | 선택이 끝난 뒤 마지막으로 확인하는 데이터다. |
| OOF | 학습 데이터 안에서 다시 나눠 만든 검증 예측값이다. 자기 자신이 포함된 묶음으로 학습한 모델이 아니라, 다른 묶음으로 학습한 모델이 예측한 값이다. |
| feature export | 실험에서 쓴 입력 피처를 운영 예측에서도 같은 방식으로 만들어 낼 수 있는지 확인하는 것이다. |
| MdAPE | 예측 오차의 중앙값이다. 일반적인 대표 오차를 볼 때 쓴다. |
| p95_APE | 큰 오차 상위 5% 지점이다. 크게 틀리는 위험을 볼 때 쓴다. |
| RMSE_log | 로그 가격 기준 평균 제곱 오차다. 전체적인 로그 오차를 볼 때 쓴다. |
| residual | 실제값과 예측값의 차이다. 여기서는 주로 `actual_log - pred_log`를 뜻한다. |
| SHAP | 트리 모델 예측값을 피처별 영향으로 나눠 보는 해석 방법이다. |
| permutation | 피처 값을 일부러 섞어 모델 성능이 얼마나 나빠지는지 보는 중요도 확인 방법이다. |
| interaction | 두 피처가 함께 작동하는 효과다. 예를 들어 크기와 깊이가 같이 가격 구간을 나누는 경우다. |
| leaf | 트리 모델에서 조건들을 지난 뒤 최종 도착하는 판단 구간이다. |
| tail | 크게 틀리는 끝단 구간이다. p95_APE 같은 큰 오차 지표와 연결된다. |
| fallback | 세부 기준의 표본이 부족할 때 더 넓은 기준으로 내려가 보정하는 방식이다. |
| bucket | 값을 구간으로 나눈 것이다. 예를 들어 크기를 q1~q5로 나눈 `size_bucket`이 있다. |

---

## 1. 전체 요약

| 모델 | 핵심 피처 축 | 실험 근거 | 후처리 연결 |
| --- | --- | --- | --- |
| Warm Huber | 작가 기준선, 크기 정보 | `PRE-WARM-07` group-drop | 전체 residual, 크기 구간, 작가 학습량 구간 |
| Cold CatBoost | 크기, 깊이, 재료/형태 조합 | SHAP, interaction, leaf segment | leaf/segment residual + fallback |
| Cold LightGBM | 크기 피처, support/size 조합, tail slice | permutation, split importance, tail slice | pred_bin, size/support bucket, tail 안정화 |

가장 중요한 결론은 다음이다.

```text
Warm Huber는 작가와 크기가 핵심이다.
Cold CatBoost는 크기 단독보다 크기 x 깊이 x 재료 조합을 본다.
Cold LightGBM은 크기 피처에 민감하고 일부 leaf/tail 구간에서 큰 오차가 생길 수 있다.
```

이 문서는 다음 흐름으로 읽으면 된다.

| 순서 | 내용 | 목적 |
| --- | --- | --- |
| 1 | Warm Huber 기준 피처셋과 group-drop 결과 | 선형 모델에서 어떤 피처 축이 실제로 필요한지 확인 |
| 2 | Warm 후보 재선정 결과 | 현재 후처리 기준 후보를 왜 유지하는지 확인 |
| 3 | Cold CatBoost/LightGBM 피처셋 구성 근거 | Cold 모델도 Warm과 같은 기준으로 피처셋 근거를 확인 |
| 4 | Cold 모델별 영향도 결과 | CatBoost와 LightGBM의 구조에 맞춰 영향도 해석 |
| 5 | 후처리 연결 | 영향도 해석을 보정 실험 기준으로 연결 |

---

## 2. Warm Huber 피처 영향도

### 2.1 해석 기준

Warm Huber는 선형 모델이다.

```text
pred_log_price = intercept + Σ(coefficient_j * transformed_feature_j)
pred_price = exp(pred_log_price)
```

따라서 피처 영향도는 기본적으로 계수와 기여도로 해석할 수 있다.

다만 실제 해석에서는 계수만 보면 안 된다.

- 숫자형 피처는 표준화 후 들어간다.
- 범주형 피처는 one-hot으로 바뀐다.
- 범주형 one-hot은 기준 범주와 희소 범주 문제 때문에 원계수만 비교하면 위험하다.
- 그래서 실제 샘플에서 `입력값 x 계수`가 만든 기여도와 group-drop 결과를 같이 본다.

### 2.2 `base_existing_combo` 구성

`base_existing_combo`는 Warm Huber final artifact의 기준 피처셋이다.

이 이름은 “기본 작품 구조 피처와 기존 조합 피처를 묶은 피처셋”이라는 뜻이다. 실제 모델에서는 여기에 Warm 작가 기준선을 잡기 위한 `artist_key`가 함께 들어간다.

| 그룹 | 피처 | 모델에서 기대하는 역할 |
| --- | --- | --- |
| 작가 기준선 | `artist_key` | 같은 작가의 과거 가격대를 반영 |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모에 따른 가격대 반영 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 작품 또는 깊이 있는 작품의 차이 반영 |
| 형태 | `aspect_ratio`, `is_extreme_aspect_ratio` | 비율이 극단적인 작품의 차이 반영 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 재료와 바탕에 따른 가격 차이 반영 |

`base_existing_combo`에 포함되지 않는 피처는 다음과 같다.

| 제외 피처 | 제외된 의미 |
| --- | --- |
| `artist_name_ko` | 한글 작가명 기반 식별값 |
| `artist_works_log` | 작가 학습 작품 수 |
| `ln_estimated_ho` | 호수 기반 크기 표현 |
| `artist_key x ho interaction` | 작가별 호수 프리미엄 |
| `artist_name_ko x log_area` | 작가별 면적 프리미엄 |

따라서 `base_existing_combo`는 넓고 운영 호환성이 좋은 기준 피처셋이지만, 작가 학습량이나 작가별 크기 프리미엄까지 세밀하게 반영하는 피처셋은 아니다.

### 2.3 `base_existing_combo` 구성 근거

`base_existing_combo`는 한 번의 단일 실험에서 갑자기 선택된 피처셋이 아니다. Track6에서 작품 가격을 설명할 수 있는 기본 피처를 단계적으로 검토한 뒤, Warm Huber final artifact에서 운영 가능성과 validation 안정성을 기준으로 고정한 피처셋이다.

구성 흐름은 다음과 같다.

| 단계 | 확인한 질문 | 관련 실험/검토 | 구성에 반영된 피처 |
| --- | --- | --- | --- |
| Warm/Cold 분리 | 같은 작가의 과거 거래가 있는 Warm에서는 작가 기준선을 쓸 수 있는가? | `T6-E046`, `PRE-WARM` | `artist_key` |
| 크기 정보 확인 | 작품이 커질수록 가격대가 달라지는가? | `T6-E040`, `T6-E047`, `T6-E055`, `T6-E056` | `width_cm`, `height_cm`, `area_cm2`, `log_area` |
| 형태 정보 확인 | 같은 크기라도 세로/가로 비율이 가격 패턴을 바꾸는가? | `T6-E057`, `PRE-WARM-07` | `aspect_ratio`, `is_extreme_aspect_ratio` |
| 깊이/입체 정보 확인 | 평면 작품과 입체 후보가 다른 가격 패턴을 보이는가? | `T6-E043`, `T6-E051`, `T6-E061`, `T6-E062`, `PRE-WARM-07` | `depth_cm`, `has_depth`, `is_3d_candidate` |
| 재료/지지체 확인 | 재료와 바탕 조합이 가격 차이를 설명하는가? | `T6-E041`, `T6-E042`, `T6-E059`, `T6-E060`, `A9`, `PRE-WARM-07` | `medium_category`, `support_category`, `medium_support_bucket` |
| 운영 artifact 고정 | 실험 후보 중 실제 feature pipeline에서 안정적으로 생성 가능한가? | final artifact 구성 확인, `PRE-WARM-08` | 현재 13개 피처 유지 |

이 구성을 채택한 근거는 두 종류로 나눠서 봐야 한다.

| 근거 종류 | 설명 | 문서에서 보는 위치 |
| --- | --- | --- |
| 구성 근거 | 가격 예측에 필요한 기본 정보가 무엇인지 정한 근거 | `T6-E040~T6-E047`, `T6-E051~T6-E062`, `A9`, `T6-E046` |
| 유지 근거 | 현재 후처리 기준으로 계속 사용할지 판단한 근거 | `PRE-WARM`, `PRE-WARM-07`, `PRE-WARM-08` 결과 |

따라서 `base_existing_combo`의 의미는 “성능이 가장 좋아서 모든 피처가 강하게 중요하다는 뜻”이 아니다. 더 정확히는 “Warm Huber final artifact에서 안정적으로 생성 가능하고, validation 기준으로 후처리의 출발점으로 삼을 수 있는 보수적 기준 피처셋”이다.

이 피처셋을 현재 후처리 기준으로 유지하는 이유는 다음이다.

- validation MdAPE가 가장 낮다.
- final artifact와 직접 호환된다.
- 운영 feature pipeline에서 안정적으로 생성 가능하다.
- Warm의 핵심인 `artist_key`와 size 그룹을 모두 포함한다.

한계는 다음이다.

- test 기준에서는 compact `artist_name_ko + size` 후보가 더 좋은 결과를 보였다.
- `PRE-WARM-07`에서 `medium/support`, `aspect`, `depth/3D`는 제거해도 성능이 유지되거나 일부 개선됐다.
- 따라서 후처리에서 모든 `base_existing_combo` 피처를 동일하게 중요하게 보면 안 된다.

### 2.4 PRE-WARM-07 Group-Drop 실험 요약

`PRE-WARM-07`은 Warm 후보에서 특정 피처 그룹을 제거한 뒤 다시 학습한 실험이다.

| 제거 그룹 | 대표 결과 | 해석 |
| --- | --- | --- |
| 작가 정보 제거 | MdAPE 약 `0.48~0.49`로 악화 | 작가 기준선이 필수 |
| 크기 정보 제거 | MdAPE 약 `0.55~0.56`, p95 약 `5.2~5.4`로 악화 | 크기는 가격 예측의 핵심 |
| aspect 제거 | 일부 후보에서 MdAPE 개선 | Warm Huber에서는 aspect가 필수는 아님 |
| medium/support 제거 | final artifact 후보에서 소폭 개선 | Warm에서는 재료/지지체가 핵심축은 아님 |
| artist_works 제거 | p95 소폭 악화 | 작가 학습량은 안정성 보조 피처 |
| ho interaction 제거 | p95 악화 | 작가별 호수 효과는 tail 방어 보조 |

---

## 3. PRE-WARM-07 상세 결과

### 3.1 GDA-01: Final Artifact Base Existing Combo

이 후보는 현재 final artifact와 같은 계열이다.

| 비교 | 사용 피처 변화 | MdAPE | p95_APE | RMSE_log | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| baseline | 전체 `base_existing_combo` | `0.2274` | `2.0128` | `0.6091` | 현재 기준 Warm 후보 |
| drop artist | `artist_key` 제거 | `0.4843` | `2.9767` | `0.9421` | 작가 기준선 제거 시 대표 오차 급락 |
| drop size | `width/height/area/log_area` 제거 | `0.5508` | `5.2275` | `1.0513` | 크기 제거 시 tail까지 크게 악화 |
| drop depth/3D | `depth/has_depth/is_3d` 제거 | `0.2276` | `2.0259` | `0.6103` | 영향 작음 |
| drop medium/support | `medium/support/bucket` 제거 | `0.2254` | `1.9958` | `0.6149` | 제거 후 소폭 개선 |
| drop aspect | `aspect/is_extreme` 제거 | `0.2262` | `2.0077` | `0.6100` | 제거 후 소폭 개선 |

해석:

- `artist_key`와 size 그룹은 필수다.
- `medium/support`, `aspect`, `depth/3D`는 Warm Huber에서 독립적인 설명력이 약하거나 일부 노이즈를 만들 수 있다.
- 따라서 Warm 후처리에서 재료/지지체 기반 보정은 우선순위를 낮춘다.

### 3.2 GDA-05: Compact Artist Name + Size + Artist Works

이 후보는 test MdAPE가 낮게 나온 compact 계열이다.

| 비교 | 사용 피처 변화 | MdAPE | p95_APE | RMSE_log | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| baseline | `artist_name_ko + size + artist_works + aspect` | `0.2221` | `1.9218` | `0.6233` | compact 기준 후보 |
| drop artist_name | `artist_name_ko` 제거 | `0.4797` | `2.8258` | `0.9643` | 작가명 제거 시 성능 급락 |
| drop size | `width/height/log_area` 제거 | `0.5559` | `5.3860` | `1.0598` | 크기 제거 시 가장 크게 악화 |
| drop artist_works | `artist_works_log` 제거 | `0.2223` | `1.9467` | `0.6235` | MdAPE 변화는 작지만 p95 악화 |
| drop aspect | `aspect_ratio` 제거 | `0.2208` | `1.9234` | `0.6229` | MdAPE는 가장 낮음 |

해석:

- 작가명과 크기 정보가 핵심이다.
- `artist_works_log`는 대표 오차보다 p95 안정성에 더 가까운 보조 피처다.
- `aspect_ratio`는 이 후보에서 제거해도 MdAPE가 좋아졌다.
- 하지만 이 후보는 `artist_name_ko` feature export 정합성 문제가 있어 운영 후보로 바로 확정하지 않았다.

### 3.3 GDA-06C: Compact Artist Key + Size + Ho Interaction

이 후보는 운영에 더 적합한 `artist_key`를 사용하고, 작가별 호수 효과를 반영한 후보다.

| 비교 | 사용 피처 변화 | MdAPE | p95_APE | RMSE_log | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| baseline | `artist_key + size + ho interaction` | `0.2271` | `1.8977` | `0.6239` | p95 안정성이 좋은 보조 후보 |
| drop artist_key | `artist_key` 및 교차항 제거 | `0.4921` | `2.8499` | `0.9617` | 작가 기준선 제거 시 성능 급락 |
| drop size | `width/height/log_area` 제거 | `0.2596` | `1.9160` | `0.7526` | MdAPE 악화, p95 악화는 제한적 |
| drop ho interaction | `ln_estimated_ho` 및 교차항 제거 | `0.2311` | `1.9469` | `0.6240` | ho interaction은 p95 방어에 기여 |
| drop aspect | `aspect_ratio` 제거 | `0.2306` | `1.8847` | `0.6235` | MdAPE는 악화, p95는 소폭 개선 |

해석:

- `artist_key`는 필수다.
- `ho interaction`은 대표 오차보다 p95 안정성에 기여한다.
- 이 후보는 MdAPE 최저 후보라기보다 큰 오차 방어 후보로 보는 것이 맞다.

---

## 4. PRE-WARM 후보 재선정 결과

`PRE-WARM`은 기존에 더 좋아 보였던 Warm 후보와 현재 final artifact 후보를 운영 기준 전처리로 다시 비교한 실험이다.

운영 기준:

```text
OneHotEncoder(min_frequency=10)
HuberRegressor(max_iter=3000)
```

| 후보 | Test MdAPE | Test p95_APE | RMSE_log | 판단 |
| --- | ---: | ---: | ---: | --- |
| `final artifact base_existing_combo` | `0.2274` | `2.0128` | `0.6091` | 현재 artifact 기준 재현 |
| `compact artist_name size` | `0.2223` | `1.9467` | `0.6235` | test MdAPE 개선 |
| `compact artist_name size + area interaction` | `0.2251` | `1.9165` | `0.6240` | p95 일부 개선 |
| `compact artist_name size + ho interaction` | `0.2242` | `1.8996` | `0.6234` | p95 개선 |
| `compact artist_name size + artist works` | `0.2221` | `1.9218` | `0.6233` | test MdAPE 1위권 |
| `compact artist_key size` | `0.2311` | `1.9469` | `0.6240` | 운영용이지만 MdAPE 낮음 |
| `compact artist_key size + area interaction` | `0.2290` | `1.9140` | `0.6245` | p95 일부 개선 |
| `compact artist_key size + ho interaction` | `0.2271` | `1.8977` | `0.6239` | 운영용 p95 안정 후보 |

해석:

- test 기준으로는 compact `artist_name_ko` 후보가 좋아 보인다.
- 하지만 운영 적용성을 고려하면 `artist_key` 기반 후보도 같이 봐야 한다.
- 그래서 바로 모델을 교체하지 않고 validation/OOF 기준까지 확인했다.

---

## 5. PRE-WARM-08 Validation / Test / OOF 비교

`PRE-WARM-08`은 test 결과만 보고 모델을 바꾸는 위험을 막기 위해 validation, test, train OOF를 함께 비교한 실험이다.

| 후보 | Validation MdAPE | Validation p95 | Test MdAPE | Test p95 | OOF MdAPE | 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `final artifact base_existing_combo` | `0.2124` | `1.3191` | `0.2274` | `2.0128` | `0.1942` | 후처리 기준 유지 |
| `artist_key + size + ho interaction` | `0.2260` | `1.4768` | `0.2271` | `1.8977` | `0.1834` | 보조 후보 |
| `artist_name_ko + size + artist_works` | `0.2299` | `1.4667` | `0.2221` | `1.9218` | `0.1981` | 보류 |
| `artist_name_ko + size + artist_works no aspect` | `0.2305` | `1.4835` | `0.2208` | `1.9234` | `0.1987` | 보류 |

해석:

- validation 기준으로는 `base_existing_combo`가 가장 좋다.
- test 기준으로는 compact `artist_name_ko` 후보가 좋아 보인다.
- OOF 기준으로는 `artist_key + size + ho interaction`의 MdAPE가 좋다.
- 따라서 test만 보고 모델을 바꾸지 않는다.
- 후처리 기준은 `base_existing_combo`를 유지한다.
- `artist_key + size + ho interaction`은 보조 비교 후보로 둔다.
- `artist_name_ko` 후보는 validation 성능과 feature export 정합성 문제로 보류한다.

---

## 6. Cold 피처셋 구성 근거

Cold는 Warm과 달리 작가 기준선이 없다. 따라서 피처셋 구성 논리도 “작가 효과 + 작품 구조”가 아니라 “작품 자체 조건만으로 가격 구간을 얼마나 잘 나눌 수 있는가”에 맞춰야 한다.

현재 Cold final artifact는 모델별로 다른 기준 피처셋을 사용한다.

| 모델 | 기준 피처셋 | 구성 방향 | 선정 근거 |
| --- | --- | --- | --- |
| CatBoost | `base_medium_shape` | 크기, 깊이, 재료/형태 조합으로 segment 구분 | CatBoost 내 validation median APE 최저 |
| LightGBM | `base_support_size` | 크기, 지지체-크기 조합으로 대표 오차와 tail 관리 | LightGBM 내 validation median APE 최저, Cold 대표 오차 최저 |

### 6.1 Cold CatBoost `base_medium_shape`

`base_medium_shape`는 CatBoost의 대칭 트리 구조에 맞춰 구성된 Cold 피처셋이다. CatBoost는 같은 depth에서 같은 split 조건을 반복 적용하므로, 단일 피처보다 “크기 + 깊이 + 재료/형태”의 조건 조합을 해석하는 것이 중요하다.

| 그룹 | 피처 | 구성 이유 |
| --- | --- | --- |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | Cold에서 작가 기준선을 대신하는 가장 강한 가격 축 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 크기/재료/형태와 interaction을 만들 수 있는 조건 |
| 형태 | `aspect_ratio`, `shape_bucket` | 비율과 형태 구간을 leaf segment로 나누기 위함 |
| 재료/지지체 | `medium_category`, `support_category` | 작품 자체 조건의 기본 범주 |
| 조합 피처 | `medium_shape_bucket` | 재료와 형태가 함께 가격 구간을 나누는지 반영 |

구성 근거는 다음이다.

| 단계 | 확인한 질문 | 관련 실험/검토 | 결론 |
| --- | --- | --- | --- |
| Cold 조건 정의 | 작가 기준선 없이 예측해야 하는가? | Warm/Cold 분리 원칙, `T6-E046` | 작가 식별 피처 제외 |
| 후보 조합 비교 | CatBoost에서 어떤 조합이 대표 오차를 가장 낮추는가? | `T6-E005` | `base_medium_shape`가 CatBoost 내 상위 후보 |
| validation 선정 | test 전에 어떤 후보를 고정할 것인가? | `T6-E006` | CatBoost 내 validation median APE `0.4251`로 최저 |
| 구조 해석 | CatBoost 구조상 어떤 피처 조합을 봐야 하는가? | Cold 해석 감사 | 크기 x 깊이, 깊이 x 재료, 깊이 x 형태 interaction 중요 |

### 6.2 Cold LightGBM `base_support_size`

`base_support_size`는 LightGBM의 leaf-wise 구조에 맞춰 구성된 Cold 피처셋이다. LightGBM은 손실이 큰 leaf를 깊게 나누기 때문에, 크기 구간과 지지체-크기 조합에서 tail risk가 생기는지 보는 것이 중요하다.

| 그룹 | 피처 | 구성 이유 |
| --- | --- | --- |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | LightGBM에서 가장 민감한 가격 설명 축 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 2D/3D 구간 분리와 tail 진단 |
| 형태 | `aspect_ratio` | 극단 형태나 비율 차이 반영 |
| 재료/지지체 | `medium_category`, `support_category` | 재료와 바탕에 따른 가격대 차이 |
| 크기 구간 | `size_bucket` | leaf-wise 분기가 특정 크기 구간에 몰리는지 확인 |
| 조합 피처 | `support_size_bucket` | 지지체와 크기 조합별 큰 오차 방어 |

구성 근거는 다음이다.

| 단계 | 확인한 질문 | 관련 실험/검토 | 결론 |
| --- | --- | --- | --- |
| Cold 조건 정의 | 작가 기준선 없이 예측해야 하는가? | Warm/Cold 분리 원칙, `T6-E046` | 작가 식별 피처 제외 |
| 후보 조합 비교 | LightGBM에서 어떤 조합이 대표 오차를 가장 낮추는가? | `T6-E005` | `base_support_size`가 LightGBM 내 median APE 최저 |
| validation 선정 | test 전에 어떤 후보를 고정할 것인가? | `T6-E006` | validation median APE `0.3848`, p95 `2.0207` |
| 구조 해석 | LightGBM 구조상 어떤 피처 조합을 봐야 하는가? | Cold 해석 감사 | `area_cm2`, `size_bucket`, `support_size_bucket` 중심 tail 진단 필요 |

따라서 Cold도 Warm과 동일하게 “구성 근거”와 “유지 근거”를 분리해서 봐야 한다.

| 구분 | CatBoost | LightGBM |
| --- | --- | --- |
| 구성 근거 | 대칭 트리에서 반복 조건 조합을 잘 나누기 위한 `medium_shape` 중심 구성 | leaf-wise 구조에서 크기/지지체 구간 tail을 보기 위한 `support_size` 중심 구성 |
| 유지 근거 | `T6-E006`에서 CatBoost 내 validation median APE 최저 | `T6-E006`에서 LightGBM 내 validation median APE 최저 및 Cold 대표 오차 최저 |
| 후처리 연결 | leaf/segment residual + `medium_shape_bucket` fallback | `pred_bin`, `size_bucket`, `support_size_bucket` tail 안정화 |

## 7. Cold CatBoost 피처 영향도

### 7.1 해석 기준

CatBoost는 트리 기반 모델이고, 특히 대칭 트리 구조를 사용한다.

```text
같은 depth의 노드들이 동일한 split 조건을 공유한다.
```

따라서 CatBoost에서는 특정 피처 하나가 독립적으로 가격을 결정한다고 해석하기보다, 반복 split과 피처 조합이 가격 구간을 나눈다고 해석하는 것이 맞다.

### 7.2 주요 SHAP 결과

| 순위 | 피처 | mean_abs_SHAP | 해석 |
| ---: | --- | ---: | --- |
| 1 | `width_cm` | `0.2629` | 크기 축 중 가장 강한 단독 영향 |
| 2 | `area_cm2` | `0.2217` | 면적 기반 가격대 분리 |
| 3 | `log_area` | `0.1974` | 로그 크기 기반 가격대 안정화 |
| 4 | `height_cm` | `0.1266` | 세로 크기 보조 |
| 5 | `depth_cm` | `0.0940` | 입체/깊이 조건에서 가격대 분기 |

### 7.3 주요 Interaction 결과

| 순위 | interaction | score | 해석 |
| ---: | --- | ---: | --- |
| 1 | `width_cm x depth_cm` | `5.5493` | 크기와 깊이 조합으로 2D/3D 또는 대형작 조건 구분 |
| 2 | `height_cm x depth_cm` | `5.2242` | 세로 크기와 깊이 조합으로 가격 구간 분화 |
| 3 | `depth_cm x aspect_ratio` | `5.1604` | 깊이와 형태 비율이 함께 작동 |
| 4 | `depth_cm x medium_category` | `4.8243` | 입체/깊이 효과가 재료에 따라 다르게 작동 |
| 5 | `depth_cm x area_cm2` | `4.6171` | 면적과 깊이 조합이 큰 작품 구간 설명 |

해석:

- CatBoost는 크기 단독보다 `크기 x 깊이`, `깊이 x 재료`, `깊이 x 형태`를 중요하게 본다.
- Cold에서는 작가 기준선이 없으므로 작품 자체 조건 조합이 가격 구간을 나누는 핵심이다.
- CatBoost 후처리는 전체 상수 보정보다 leaf/segment 기반 residual 보정이 더 자연스럽다.

---

## 8. Cold LightGBM 피처 영향도

### 8.1 해석 기준

LightGBM은 leaf-wise 방식으로 트리를 확장한다.

손실을 가장 많이 줄일 수 있는 leaf를 우선적으로 깊게 확장하기 때문에, 일부 구간에서 매우 세밀한 분기가 생길 수 있다. 이 구조는 평균 성능을 높일 수 있지만, 특정 tail 구간에서는 큰 오차가 생길 수 있다.

### 8.2 주요 결과

| 관점 | 핵심 피처 | 해석 |
| --- | --- | --- |
| split importance | `depth_cm`, `aspect_ratio`, `area_cm2`, `width_cm`, `height_cm` | 깊이, 형태, 크기 피처를 많이 사용 |
| permutation MdAPE delta | `area_cm2` `+0.2542` | 면적 교란 시 대표 오차가 크게 악화 |
| permutation p95 delta | `area_cm2` `+7.5139` | 면적이 tail risk에도 큰 영향 |
| tail slice | `canvas__q5`, `acrylic`, `q3`, `canvas__q3` | 특정 크기/지지체/재료 구간에서 큰 오차 발생 |

해석:

- LightGBM은 크기 피처에 매우 민감하다.
- 특히 `area_cm2`는 대표 오차와 tail risk 모두에 큰 영향을 준다.
- LightGBM의 후처리는 `pred_bin`, `size_bucket`, `support_size_bucket` 기준이 적합하다.
- MdAPE 개선보다 p95 안정화가 중요하다.

---

## 9. 후처리 연결

| 모델 | 영향도 결론 | 후처리 우선순위 |
| --- | --- | --- |
| Warm Huber | 작가 + 크기 핵심 | global residual, size bin, artist history slice |
| Cold CatBoost | 크기/깊이/재료 조합 핵심 | leaf/segment residual + fallback |
| Cold LightGBM | 크기 민감도와 tail risk 큼 | pred_bin, size/support bucket, tail stabilization |

Warm 후처리에서는 `medium/support`와 `aspect`를 우선 보정 기준으로 삼지 않는다. `PRE-WARM-07`에서 제거해도 성능이 유지되거나 개선됐기 때문이다.

CatBoost 후처리에서는 leaf pattern만 쓰면 표본 수가 부족할 수 있으므로 fallback 구조가 필요하다.

LightGBM 후처리에서는 큰 오차가 발생하는 tail slice를 먼저 식별하고, p95_APE를 줄이는 방향으로 보정해야 한다.

---

## 10. 참고 산출물

| 구분 | 파일 |
| --- | --- |
| PRE-WARM 결과 | `experiments/track6/PRE-WARM_warm_baseline_reselection/outputs/result_sheet.csv` |
| PRE-WARM-07 결과 | `experiments/track6/PRE-WARM-07_warm_group_drop_ablation/outputs/result_sheet.csv` |
| PRE-WARM-08 결과 | `experiments/track6/PRE-WARM-08_warm_final_candidate_validation/outputs/result_sheet.csv` |
| 모델 구조 해석 | `docs/track6/experiments/model_structure_based_interpretation_report.md` |
| Warm Huber 해석 HTML | `docs/track6/experiments/warm_huber_interpretability_audit_report.html` |
| Cold 모델 해석 HTML | `docs/track6/experiments/cold_models_interpretability_audit_report.html` |
