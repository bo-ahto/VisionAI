# Track6 가격 예측 모델 후속 실험 온보딩 문서

- 작성일: 2026-06-01
- 대상: Track6 가격 예측 프로젝트에 새로 참여하는 후임
- 목적: 지금까지의 실험 흐름, 모델별 특성, 피처 영향도, 현재 후보, 후처리 계획을 이해하고 후속 실험에 같은 기준으로 참여할 수 있게 한다.
- 범위: 프로젝트 배경, 모델 구조, 피처 영향도, 지금까지의 실험 결과, 후속 실험 계획을 다룬다.

---

## 1. 문서 목적

이 문서는 Track6 가격 예측 프로젝트의 현재 상태를 처음 보는 사람이 따라올 수 있도록 정리한 문서다.

후속 실험을 같이 진행하려면 단순히 어떤 모델의 성능이 좋았는지만 알면 부족하다. 다음 내용을 함께 이해해야 한다.

- 가격 예측이 어떤 방식으로 계산되는지
- 왜 Warm과 Cold를 분리했는지
- 왜 Warm은 Huber를 중심으로 보고, Cold는 CatBoost와 LightGBM을 보는지
- 피처별 영향도를 모델별로 어떻게 다르게 해석해야 하는지
- 지금까지 어떤 실험을 했고, 어떤 결론이 나왔는지
- 후처리 실험을 어떤 순서로 진행해야 하는지

핵심 메시지는 다음과 같다.

```text
Warm은 작가 이력이 있는 문제라 작가 기준선과 크기 정보가 핵심이다.
Cold는 작가 기준선이 없으므로 작품 자체의 크기, 재료, 지지체, 형태 조합이 중요하다.
모델 구조가 다르기 때문에 피처 영향도 해석과 후처리 방식도 모델별로 달라야 한다.
```

이 문서는 다음 순서로 읽으면 된다.

| 읽는 순서 | 확인할 내용 | 이유 |
| --- | --- | --- |
| 1 | 프로젝트 목표와 데이터 기준 | 어떤 문제를 풀고 어떤 지표로 판단하는지 먼저 고정 |
| 2 | Warm/Cold 구분 | 같은 가격 예측이라도 사용할 수 있는 정보가 다르기 때문 |
| 3 | 현재 모델 후보와 피처셋 구성 | 지금 기준으로 무엇을 후처리 대상으로 삼는지 확인 |
| 4 | 모델별 가격 예측 방식 | Huber, CatBoost, LightGBM이 가격을 계산하는 방식 이해 |
| 5 | 피처 영향도와 실험 결과 | 왜 특정 피처와 조합을 중요하게 보는지 확인 |
| 6 | 후처리 실험 계획 | 모델별 약점을 어떤 방식으로 보정할지 연결 |

---

## 2. 먼저 알아야 할 용어

이 문서에서 반복해서 쓰는 용어는 다음처럼 이해하면 된다.

| 용어 | 쉬운 설명 | 이 프로젝트에서의 의미 |
| --- | --- | --- |
| 피처, feature | 모델에 넣는 입력값 | 작품 크기, 재료, 지지체, 작가 정보처럼 가격 예측에 쓰는 값 |
| target | 모델이 맞히려는 정답값 | 실제 가격을 로그로 바꾼 `ln_price_krw` |
| split | 데이터를 역할별로 나눈 것 | train, validation, test로 나누어 실험 |
| train | 모델이 공부하는 데이터 | 모델 계수를 학습하거나 트리를 만드는 데 사용 |
| validation | 후보를 고르는 중간 검증 데이터 | 모델/피처/보정값을 선택하는 기준 데이터 |
| test | 마지막 확인 데이터 | 이미 정한 기준이 잘 유지되는지 최종 확인만 하는 데이터 |
| artifact | 학습이 끝나 저장된 산출물 | 실제 재사용할 모델 파일, 피처 목록, 전처리 설정 등을 묶은 결과물 |
| final artifact | 현재 운영 기준으로 고정된 최종 산출물 | 후처리 실험의 기준이 되는 저장 모델과 피처셋 |
| pipeline | 같은 처리를 반복하기 위한 절차 묶음 | 결측 처리, 인코딩, 스케일링, 모델 예측까지 이어지는 처리 흐름 |
| feature export | 실험에서 쓴 입력값을 운영에서도 똑같이 만들어 내는 것 | 모델 후보가 실제 서비스 예측에도 적용 가능한지 확인하는 기준 |
| residual | 예측이 얼마나 빗나갔는지 | `actual_log - pred_log`, 즉 실제 로그 가격과 예측 로그 가격의 차이 |
| calibration, 보정 | 예측값의 반복적인 치우침을 수정하는 작업 | 특정 구간에서 계속 높게/낮게 예측하면 그만큼 조정 |
| OOF | 학습 데이터 내부 검증 예측 | train을 다시 여러 조각으로 나누어, 각 조각을 자기 자신으로 학습하지 않은 모델로 예측한 값 |
| one-hot | 범주 값을 0/1 컬럼으로 바꾸는 방식 | 작가명, 재료 같은 문자 값을 모델이 읽을 수 있게 변환 |
| bucket | 연속값이나 조합을 구간으로 나눈 값 | 크기를 q1~q5로 나누거나 재료+형태를 묶은 구간 |
| interaction | 두 피처가 함께 작동하는 효과 | 크기 단독이 아니라 `작가 x 크기`, `깊이 x 재료`처럼 조합으로 생기는 영향 |
| SHAP | 예측값을 피처별로 나눠 설명하는 방법 | CatBoost에서 각 피처가 예측을 얼마나 올리거나 내렸는지 보는 기준 |
| permutation | 피처 값을 섞어 중요도를 확인하는 방법 | 어떤 피처를 망가뜨렸을 때 성능이 얼마나 나빠지는지 확인 |
| leaf | 트리 모델에서 최종 도착한 판단 구간 | 여러 조건을 지난 뒤 모델이 가격을 정하는 마지막 구간 |
| segment | 비슷한 조건을 가진 데이터 묶음 | 같은 leaf, 같은 크기 구간, 같은 재료/형태 조합 등 |
| fallback | 세부 기준이 부족할 때 쓰는 대체 기준 | leaf 표본이 적으면 medium_shape, 그래도 부족하면 전체 보정 사용 |
| tail | 크게 틀리는 끝단 구간 | p95_APE처럼 상위 큰 오차가 모인 위험 구간 |
| outlier | 일반 패턴에서 많이 벗어난 샘플 | Huber가 학습 영향력을 낮추는 큰 오차 샘플 |

---

## 3. 프로젝트 개요

Track6의 목표는 미술품의 가격을 예측하는 것이다.

입력값은 작품의 크기, 재료, 지지체, 작가 정보, 작가 메타 정보 등이고, 출력값은 예측 가격이다. 다만 모델은 원 가격을 바로 예측하지 않고 `ln_price_krw`, 즉 로그 가격을 먼저 예측한다.

전체 흐름은 다음과 같다.

```text
작품/작가 정보 입력
-> 모델 입력 피처 생성
-> log(price) 예측
-> exp 변환으로 원 가격 복원
-> 후처리 보정 또는 가격 범위 적용
-> 최종 예측 가격/신뢰도 제공
```

Track6에서는 예측 상황을 크게 Warm과 Cold로 나눈다.

| 구분 | 의미 | 핵심 특징 |
| --- | --- | --- |
| Warm | 학습 데이터에 이미 등장한 작가의 작품 예측 | 작가 기준 가격대를 활용할 수 있음 |
| Cold | 학습 데이터에 없거나 작가 이력이 부족한 작품 예측 | 작가 기준선이 약하므로 작품 자체 정보가 중요함 |

Warm과 Cold를 나누는 이유는 예측 난이도와 사용할 수 있는 정보가 다르기 때문이다. Warm은 같은 작가의 과거 작품 가격대를 기준선으로 삼을 수 있지만, Cold는 그런 기준선이 약하거나 없다.

---

## 4. 데이터 구조와 실험 기준

Track6 실험은 고정 split, 즉 데이터를 train/validation/test로 미리 나눠 둔 기준을 사용해 진행한다.

| 데이터 | 역할 |
| --- | --- |
| train | 모델 학습 | 모델이 공부하는 데이터 |
| validation | 후보 선택, 보정값 산출, 설정 결정 | 모델과 보정 방식을 고르는 중간 검증 데이터 |
| test | 최종 확인 | 이미 정한 기준을 마지막으로 확인하는 데이터 |

중요한 원칙은 test를 보고 보정값이나 모델을 다시 정하지 않는 것이다. test는 이미 결정된 기준이 실제로 유지되는지 확인하는 마지막 검증용이다.

### Target

모델이 학습하는 값은 다음이다.

```text
target = ln_price_krw = log(price_krw)
```

가격은 범위가 매우 넓다. 원 가격을 바로 예측하면 고가 작품 몇 개가 모델을 크게 흔들 수 있다. 그래서 로그 가격으로 변환해 가격 범위를 압축한다.

### 평가 지표

| 지표 | 의미 | 해석 |
| --- | --- | --- |
| MdAPE | 중앙값 기준 절대 비율 오차 | 일반적인 예측 오차 |
| p95_APE | 상위 5% 큰 오차 | 크게 틀리는 위험 구간 |
| RMSE_log | 로그 가격 기준 평균 제곱 오차 | 로그 공간에서의 전체 오차 |
| Within_30 | 실제 가격 대비 30% 이내 예측 비율 | 실무적으로 가까운 예측 비율 |
| Within_50 | 실제 가격 대비 50% 이내 예측 비율 | 넓은 허용 범위 내 예측 비율 |

이 프로젝트에서는 MdAPE를 대표 정확도 지표로 보고, p95_APE를 운영 위험 지표로 본다.

---

## 5. 가격 예측 기본 로직

모든 모델은 최종적으로 로그 가격을 예측한다.

```text
pred_log_price = model(features)
pred_price = exp(pred_log_price)
```

예를 들어 모델이 `pred_log_price = 16.1`을 예측했다면 최종 가격은 다음처럼 복원된다.

```text
pred_price = exp(16.1)
```

후처리도 대부분 로그 가격 기준에서 진행한다. 이유는 로그 공간에서 오차가 더 안정적이고, 과대/과소 예측을 보정하기 쉽기 때문이다.

대표적인 residual은 다음과 같이 계산한다.

```text
residual_log = actual_log_price - pred_log_price
```

예측이 실제보다 낮으면 residual은 양수다. 예측이 실제보다 높으면 residual은 음수다.

전체 보정의 기본 구조는 다음과 같다.

```text
correction = median(residual_log)
corrected_pred_log = pred_log_price + correction
corrected_pred_price = exp(corrected_pred_log)
```

여기서 `median(residual_log)`는 residual_log를 작은 값부터 큰 값까지 정렬했을 때 가운데에 있는 값, 즉 중앙값이다. 평균은 큰 오차 몇 개에 흔들릴 수 있으므로, 미술품 가격처럼 이상치가 많은 데이터에서는 중앙값이 더 안정적이다.

---

## 6. Warm / Cold 모델 구분

### Warm

Warm은 학습 데이터에 이미 등장한 작가의 작품을 예측하는 경우다.

Warm에서는 작가 정보가 가격의 기준선 역할을 한다. 예를 들어 같은 크기의 작품이라도 작가가 누구인지에 따라 가격대가 크게 달라질 수 있다.

Warm에서 중요한 질문은 다음이다.

```text
이 작가의 기본 가격대는 어느 정도인가?
이 작가의 작품에서 크기가 커질 때 가격이 얼마나 올라가는가?
작가 이력이나 학습 작품 수가 예측 안정성에 영향을 주는가?
```

### Cold

Cold는 작가 이력이 없거나 부족한 경우다.

Cold에서는 작가 기준선을 직접 사용하기 어렵다. 그래서 작품 자체 정보가 더 중요해진다.

Cold에서 중요한 질문은 다음이다.

```text
작품의 크기, 재료, 지지체, 형태만으로 어느 정도 가격대를 구분할 수 있는가?
특정 재료/크기/형태 조합에서 큰 오차가 반복되는가?
모델이 크게 틀리는 tail 구간을 어떻게 줄일 수 있는가?
```

---

## 7. 현재 모델 후보와 피처셋 구성

현재 기준 모델과 보조 후보는 다음과 같다.

| 영역 | 기준/후보 | 모델 | 피처셋 | 현재 판단 |
| --- | --- | --- | --- | --- |
| Warm | 기준 | Huber | `base_existing_combo` | validation 기준 가장 보수적 |
| Warm | 보조 후보 | Huber | `artist_key + size + ho interaction` | OOF, 즉 학습 데이터 내부 검증 MdAPE와 test p95가 좋아 보조 후보 유지 |
| Warm | 보류 후보 | Huber | `artist_name_ko + size + artist_works` | test는 좋지만 validation 성능과 feature export 정합성 문제로 보류 |
| Cold | 1순위 | CatBoost | `base_medium_shape` | Cold 기준 주력 후보 |
| Cold | 보조/비교 | LightGBM | `base_support_size` | tail 안정화 비교 후보 |

Warm은 최근 `PRE-WARM` 계열 실험으로 후보를 다시 확인했다. test 기준으로는 compact `artist_name_ko` 후보가 좋아 보였지만, validation 기준에서는 final artifact와 호환되는 `base_existing_combo`가 가장 좋았다. 따라서 후처리 기준은 우선 `base_existing_combo`를 유지한다.

Cold는 CatBoost와 LightGBM 모두 Warm보다 어렵다. Cold는 작가 기준선이 없기 때문에 p95_APE가 커지는 문제가 있고, 후처리에서는 큰 오차 방어가 중요하다.

아래 7.1~7.3은 “현재 후보 피처셋이 무엇으로 구성되어 있고, 왜 그 구성으로 고정됐는지”를 설명한다. 모델이 실제로 가격을 계산하는 방식은 8장에서 따로 설명한다.

### 7.1 `base_existing_combo`란 무엇인가

`base_existing_combo`는 Warm Huber의 현재 final artifact, 즉 운영 기준으로 저장된 최종 모델 산출물에서 사용하는 피처셋 이름이다. 이름만 보면 의미가 모호하지만, 실제로는 “작가 기준선 + 작품의 기본 구조 정보 + 기존에 만들어 둔 재료/형태 조합 피처”를 묶은 운영용 피처셋이다.

이 피처셋은 다음 13개 피처로 구성된다.

| 피처 그룹 | 포함 피처 | 의미 |
| --- | --- | --- |
| 작가 기준선 | `artist_key` | 같은 작가의 과거 가격대를 반영하는 Warm 핵심 피처 |
| 기본 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품의 실제 규모와 가격대 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 작품 또는 깊이 정보 |
| 형태 | `aspect_ratio`, `is_extreme_aspect_ratio` | 세로/가로 비율과 극단 형태 여부 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 작품 재료, 바탕, 재료-지지체 조합 |

`base_existing_combo`라는 이름은 다음 뜻으로 이해하면 된다.

```text
base = 크기, 깊이, 형태 같은 기본 작품 구조 피처
existing_combo = 기존 데이터 파이프라인에서 이미 생성되어 있던 조합 피처
artist_key = Warm에서 작가 기준 가격대를 잡기 위해 추가된 작가 식별 피처
```

즉 `base_existing_combo`는 새로운 외부 데이터를 추가한 피처셋이 아니라, 현재 운영 데이터에서 안정적으로 만들 수 있는 기본 피처와 기존 조합 피처를 묶은 것이다.

이 구성이 나온 흐름은 다음과 같이 이해하면 된다.

| 단계 | 판단 내용 | 관련 실험/검토 | `base_existing_combo`에 반영된 내용 |
| --- | --- | --- | --- |
| 1. Warm/Cold 분리 | Warm은 같은 작가의 과거 작품이 있으므로 작가 기준선을 사용할 수 있다고 판단 | `T6-E046` Warm/Cold 피처 분리 검토, `PRE-WARM` 재선정 | `artist_key` 포함 |
| 2. 크기 피처 확인 | 가격 예측에서 작품 규모가 가장 기본적인 설명 변수라고 판단 | `T6-E040`, `T6-E047`, `T6-E055`, `T6-E056` | `width_cm`, `height_cm`, `area_cm2`, `log_area` 포함 |
| 3. 형태 피처 확인 | 같은 면적이라도 세로/가로 비율이 극단적인 작품은 가격 패턴이 다를 수 있다고 판단 | `T6-E057`, `PRE-WARM-07` group-drop | `aspect_ratio`, `is_extreme_aspect_ratio` 포함 |
| 4. 깊이/입체 피처 확인 | 평면 작품과 입체 후보는 가격 형성 방식이 다를 수 있다고 판단 | `T6-E043`, `T6-E051`, `T6-E061`, `T6-E062`, `PRE-WARM-07` group-drop | `depth_cm`, `has_depth`, `is_3d_candidate` 포함 |
| 5. 재료/지지체 피처 확인 | 재료와 바탕은 작품 가격 차이를 설명할 수 있는 기본 작품 정보라고 판단 | `T6-E041`, `T6-E042`, `T6-E059`, `T6-E060`, `A9`, `PRE-WARM-07` group-drop | `medium_category`, `support_category`, `medium_support_bucket` 포함 |
| 6. 운영 artifact 정리 | 실험에서 만든 피처 중 운영 feature pipeline에서 안정적으로 생성 가능한 피처를 우선 | final artifact 구성 확인, `PRE-WARM-08` validation/test/OOF 재검증 | 현재 13개 피처 구성으로 고정 |

중요한 점은 `base_existing_combo`가 한 번의 단일 실험에서 갑자기 정해진 피처셋이 아니라는 것이다. 초기 작품 변수 실험에서는 크기, 재료, 지지체, 깊이/입체, 형태 정보를 각각 후보로 검토했고, 이후 Warm/Cold를 분리하면서 Warm에는 작가 기준선이 필요하다고 판단했다. 그 결과 Warm Huber final artifact에는 “작가 기준선 + 작품 구조 + 기존 조합 피처” 형태의 운영용 피처셋이 들어가게 됐다.

다만 구성 논리와 최종 채택 근거는 구분해야 한다.

| 구분 | 의미 | 관련 실험/확인 |
| --- | --- | --- |
| 구성 논리 | 어떤 종류의 피처를 후보에 넣을지 정한 근거 | `T6-E040~T6-E047`, `T6-E051~T6-E062`, `A9`, `T6-E046` |
| 채택 근거 | 현재 후처리 기준으로 이 피처셋을 유지할지 판단한 근거 | `PRE-WARM`, `PRE-WARM-07`, `PRE-WARM-08` |

Warm Huber에서 이 피처셋을 기준으로 쓰는 이유는 다음과 같다.

- validation 기준에서 가장 안정적이었다.
- final artifact와 이미 호환된다.
- `artist_key`가 포함되어 Warm의 작가 기준선을 반영할 수 있다.
- 크기, 재료, 지지체, 형태, 깊이 정보를 모두 포함해 운영 입력값으로 설명하기 쉽다.

다만 한계도 있다.

- `PRE-WARM-07`에서 `medium/support`, `aspect`, `depth/3D`는 제거해도 성능이 크게 나빠지지 않았다.
- test 기준으로는 compact `artist_name_ko + size` 계열 후보가 더 좋아 보이는 구간이 있었다.
- 따라서 `base_existing_combo`는 “절대적으로 가장 좋은 피처셋”이라기보다, 현재 validation과 운영 정합성을 고려한 보수적 기준 피처셋이다.

### 7.2 Cold CatBoost `base_medium_shape`란 무엇인가

`base_medium_shape`는 Cold CatBoost final artifact, 즉 저장된 최종 CatBoost 모델에서 사용하는 기준 피처셋이다. Cold는 Warm과 달리 작가 기준선인 `artist_key`를 사용할 수 없으므로, 작품 자체 정보만으로 가격 구간을 나눠야 한다.

이 피처셋은 다음 12개 피처로 구성된다.

| 피처 그룹 | 포함 피처 | 의미 |
| --- | --- | --- |
| 기본 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모와 가격대 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 작품 또는 깊이 조건 |
| 형태 | `aspect_ratio`, `shape_bucket` | 작품 비율과 형태 구간 |
| 재료/지지체 | `medium_category`, `support_category` | 작품 재료와 바탕 |
| 재료-형태 조합 | `medium_shape_bucket` | 같은 형태라도 재료에 따라 가격 구간이 달라지는지 반영 |

`base_medium_shape`라는 이름은 다음 뜻으로 이해하면 된다.

```text
base = 크기, 깊이, 재료, 지지체 같은 기본 작품 정보
medium = 재료 대분류
shape = 형태 구간
medium_shape = 재료와 형태를 함께 본 조합 피처
```

이 구성이 나온 흐름은 다음과 같다.

| 단계 | 판단 내용 | 관련 실험/검토 | `base_medium_shape`에 반영된 내용 |
| --- | --- | --- | --- |
| 1. Cold 조건 정의 | Cold는 작가 기준선을 쓸 수 없으므로 작품 자체 정보만 사용 | Warm/Cold 분리 원칙, `T6-E046` | `artist_key`, `artist_name_ko` 제외 |
| 2. 기본 크기 유지 | Cold에서도 크기는 가장 강한 가격 설명 축 | `T6-E005`, Cold 해석 감사 | `width_cm`, `height_cm`, `area_cm2`, `log_area` 포함 |
| 3. 깊이/입체 유지 | CatBoost interaction에서 깊이가 크기/재료/형태와 함께 작동 | Cold CatBoost SHAP/interaction | `depth_cm`, `has_depth`, `is_3d_candidate` 포함 |
| 4. 형태 구간 추가 | CatBoost 대칭 트리는 반복 split으로 조건 조합을 나누므로 형태 구간이 segment 해석에 유리 | `T6-E005`, Cold CatBoost interaction | `aspect_ratio`, `shape_bucket` 포함 |
| 5. 재료-형태 조합 추가 | CatBoost는 범주형과 조합 조건을 잘 다루므로 재료와 형태의 결합을 명시 | `T6-E005`, `T6-E006` | `medium_category`, `support_category`, `medium_shape_bucket` 포함 |
| 6. CatBoost 후보 선정 | CatBoost 후보 중 validation median APE가 가장 낮은 조합을 선택 | `T6-E006` | `base_medium_shape`를 CatBoost 기준으로 고정 |

채택 근거는 다음이다.

| 근거 | 내용 |
| --- | --- |
| validation 후보 선정 | `T6-E006`에서 CatBoost 후보 중 `base_medium_shape`가 validation median APE `0.4251`로 CatBoost 내 최저 |
| 모델 구조 적합성 | CatBoost는 대칭 트리 구조라 단일 피처보다 반복되는 조건 조합과 segment 해석이 중요 |
| 해석 결과 | 최종 artifact 기준 SHAP/interaction에서 크기, 깊이, 재료/형태 조합이 핵심으로 확인 |
| 후처리 연결 | leaf/segment residual, `medium_shape_bucket`, `shape_bucket` 기반 보정과 연결 가능 |

다만 한계도 있다.

- Cold 전체 후보 중 대표 오차는 LightGBM `base_support_size`가 더 낮다.
- CatBoost `base_medium_shape`는 Cold의 주력 비교 후보이지만, 모든 Cold 상황에서 최저 오차 모델이라는 뜻은 아니다.
- leaf pattern coverage, 즉 같은 leaf 패턴에 충분한 데이터가 모이는 비율이 낮기 때문에 leaf 단독 보정보다는 `medium_shape_bucket`, `shape_bucket`, overall residual로 내려가는 fallback 구조가 필요하다.

### 7.3 Cold LightGBM `base_support_size`란 무엇인가

`base_support_size`는 Cold LightGBM final artifact, 즉 저장된 최종 LightGBM 모델에서 사용하는 기준 피처셋이다. LightGBM은 leaf-wise 방식으로 손실이 큰 구간을 깊게 나누는 모델이므로, 크기 구간과 지지체-크기 조합을 명시적으로 넣어 tail 구간을 관리하는 방향으로 구성됐다.

이 피처셋은 다음 12개 피처로 구성된다.

| 피처 그룹 | 포함 피처 | 의미 |
| --- | --- | --- |
| 기본 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모와 가격대 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 작품 또는 깊이 조건 |
| 형태 | `aspect_ratio` | 작품 비율 |
| 재료/지지체 | `medium_category`, `support_category` | 작품 재료와 바탕 |
| 크기 구간 | `size_bucket` | 크기 분위 구간 |
| 지지체-크기 조합 | `support_size_bucket` | 같은 크기라도 지지체에 따라 가격 위험이 달라지는지 반영 |

`base_support_size`라는 이름은 다음 뜻으로 이해하면 된다.

```text
base = 크기, 깊이, 재료, 지지체 같은 기본 작품 정보
support = 작품 바탕/지지체
size = 크기 구간
support_size = 지지체와 크기를 함께 본 조합 피처
```

이 구성이 나온 흐름은 다음과 같다.

| 단계 | 판단 내용 | 관련 실험/검토 | `base_support_size`에 반영된 내용 |
| --- | --- | --- | --- |
| 1. Cold 조건 정의 | 작가 기준선 없이 작품 조건만으로 가격 예측 | Warm/Cold 분리 원칙, `T6-E046` | 작가 식별 피처 제외 |
| 2. 크기 원피처 유지 | LightGBM은 크기 피처, 특히 `area_cm2`에 매우 민감 | `T6-E005`, LightGBM permutation | `width_cm`, `height_cm`, `area_cm2`, `log_area` 포함 |
| 3. 크기 구간 추가 | leaf-wise 구조에서는 특정 크기 구간에서 큰 오차가 반복될 수 있음 | `T6-E005`, tail slice 진단 | `size_bucket` 포함 |
| 4. 지지체-크기 조합 추가 | 큰 캔버스, 종이, 패널 등 지지체와 크기의 조합이 tail risk를 만들 수 있음 | `T6-E005`, LightGBM tail slice | `support_category`, `support_size_bucket` 포함 |
| 5. 기본 작품 조건 유지 | 깊이, 형태, 재료는 split 후보와 tail slice 해석에 필요 | Cold 해석 감사 | `depth_cm`, `has_depth`, `is_3d_candidate`, `aspect_ratio`, `medium_category` 포함 |
| 6. LightGBM 후보 선정 | LightGBM 후보 중 validation median APE가 가장 낮은 조합을 선택 | `T6-E006` | `base_support_size`를 LightGBM 기준으로 고정 |

채택 근거는 다음이다.

| 근거 | 내용 |
| --- | --- |
| validation 후보 선정 | `T6-E006`에서 `base_support_size`가 LightGBM 내 validation median APE `0.3848`로 최저 |
| Cold 대표 오차 | 같은 실험에서 Cold 전체 대표 오차 기준으로도 가장 낮은 후보 |
| 모델 구조 적합성 | LightGBM은 leaf-wise 구조라 크기/지지체 구간별 tail 관리가 중요 |
| 해석 결과 | permutation에서 `area_cm2` 교란 시 MdAPE와 p95가 크게 악화되어 크기 축의 중요성이 확인 |
| 후처리 연결 | `pred_bin`, `size_bucket`, `support_size_bucket` 기반 tail 안정화와 연결 가능 |

다만 한계도 있다.

- p95_APE 기준으로는 `base_large_flags`가 더 좋은 후보였다.
- LightGBM은 leaf-wise 구조 때문에 특정 tail 구간을 과하게 세분화할 수 있다.
- 따라서 `base_support_size`는 대표 오차 기준 후보이며, 후처리에서는 p95 안정화를 별도 목표로 둬야 한다.

---

## 8. 모델별 가격 예측 방식

7장에서 피처셋 구성을 먼저 확인했다면, 8장에서는 각 모델이 그 피처를 사용해 어떤 방식으로 로그 가격을 예측하는지 본다.

### 8.1 Warm Huber

Warm Huber는 선형 모델이다. 가격 계산 구조는 다음과 같다.

```text
pred_log_price = intercept + beta_1*x_1 + beta_2*x_2 + ... + beta_n*x_n
pred_price = exp(pred_log_price)
```

쉽게 말하면 다음과 같다.

```text
예측 로그 가격
= 기본값
+ 작가 효과
+ 크기 효과
+ 재료/지지체 효과
+ 형태 효과
+ 기타 보조 효과
```

Huber는 일반 선형 회귀와 비슷하지만 손실 함수가 다르다.

#### Huber 손실 함수

오차를 `r = y - pred`라고 하면 Huber loss는 다음 구조다.

```text
작은 오차: 0.5 * r^2
큰 오차: epsilon * (|r| - 0.5 * epsilon)
```

작은 오차는 제곱 손실처럼 다루고, 큰 오차는 선형 손실처럼 다룬다. 즉 너무 큰 이상치가 모델 계수를 과하게 흔들지 못하게 한다.

미술품 가격은 극단적으로 비싼 작품이나 낮은 가격의 작품이 섞여 있으므로 Huber가 Warm에 적합하다.

#### Huber에서 피처 영향도 해석

Huber는 선형 모델이므로 피처 영향도를 계수로 볼 수 있다.

```text
feature_contribution = coefficient * transformed_feature_value
```

다만 숫자형 피처는 표준화되고, 범주형 피처는 one-hot으로 변환된다. 그래서 원계수만 바로 비교하면 안 된다.

해석할 때는 다음을 함께 본다.

- 계수
- 원 단위 환산 계수
- 실제 샘플에서 `입력값 x 계수`가 만든 기여도
- Huber가 outlier로 본 샘플 여부
- group-drop ablation 결과

---

### 8.2 Cold CatBoost

CatBoost는 트리 기반 모델이다. 여러 개의 작은 트리를 순서대로 쌓으면서 예측 오차를 줄인다.

CatBoost의 중요한 특징은 대칭 트리 구조다.

```text
같은 depth의 노드들이 같은 split 조건을 공유한다.
```

이 구조에서는 피처 하나가 독립적으로 가격을 결정한다고 말하기보다, 반복되는 split 조건과 피처 조합이 가격 구간을 나눈다고 해석하는 것이 더 맞다.

예를 들어 CatBoost가 `width_cm`, `depth_cm`, `medium_category`를 중요하게 봤다면 다음처럼 해석한다.

```text
큰 작품인가?
깊이가 있는가?
어떤 재료인가?
이 조건 조합이 특정 가격대 leaf로 이동하게 하는가?
```

#### CatBoost 영향도 해석 기준

CatBoost에서는 다음을 함께 본다.

- SHAP: 각 피처가 예측값을 얼마나 움직였는지
- interaction: 어떤 피처 조합이 같이 작동했는지
- leaf segment residual: 특정 leaf 패턴에서 오차가 반복되는지

CatBoost는 범주형 피처를 잘 다룰 수 있고, 피처 조합을 자동으로 학습한다. 그래서 Cold에서 `medium_shape_bucket`, `shape_bucket`, `depth_cm` 같은 조합 피처가 중요하게 나타날 수 있다.

---

### 8.3 Cold LightGBM

LightGBM도 트리 기반 모델이지만 CatBoost와 구조가 다르다.

LightGBM은 leaf-wise 방식으로 트리를 확장한다. 손실을 가장 많이 줄일 수 있는 leaf를 우선적으로 깊게 확장한다.

이 방식은 빠르고 강력하지만, 일부 구간을 너무 세밀하게 나누면서 큰 오차가 생길 수 있다.

#### LightGBM 영향도 해석 기준

LightGBM에서는 다음을 함께 본다.

- split importance: 어떤 피처가 자주 split에 쓰였는지
- permutation importance: 해당 피처를 섞었을 때 성능이 얼마나 나빠지는지
- tail slice: 특정 구간에서 p95_APE가 크게 튀는지
- leaf-wise 진단: 일부 leaf에서 큰 오차가 반복되는지

LightGBM은 특히 크기 계열 피처에 민감하다. `area_cm2`, `width_cm`, `height_cm`, `log_area`, `size_bucket`, `support_size_bucket`을 어떻게 조합하는지가 중요하다.

---

## 9. 피처 그룹 사전

7장에서 모델별 기준 피처셋을 설명했으므로, 여기서는 문서 전반에 반복해서 나오는 피처 그룹을 사전처럼 정리한다. 후속 실험이나 후처리 계획을 볼 때 피처 이름이 어떤 의미인지 확인하는 용도다.

| 피처 그룹 | 주요 피처 | 의미 |
| --- | --- | --- |
| 작가 정보 | `artist_key`, `artist_name_ko` | 작가별 기본 가격대 |
| 작가 이력량 | `artist_works_log`, `artist_works_count_train` | 해당 작가의 학습 작품 수 또는 활동량 |
| 크기 정보 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `ln_estimated_ho` | 작품 규모와 가격대 |
| 형태 정보 | `aspect_ratio`, `is_extreme_aspect_ratio` | 세로/가로 비율과 극단 형태 |
| 깊이/입체 정보 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 작품 여부와 깊이 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 작품 재료와 바탕 |
| 버킷/조합 피처 | `shape_bucket`, `size_bucket`, `medium_shape_bucket`, `support_size_bucket` | 트리 모델이 구간을 더 쉽게 나누도록 만든 피처 |
| 교차항 | `artist_key x ho`, `artist_name_ko x log_area` | 작가별 크기/호수 프리미엄 |

### 9.1 Warm 기준 피처셋의 그룹 위치

`base_existing_combo`는 위 피처 그룹 중 다음을 포함한다.

```text
작가 정보: artist_key
크기 정보: width_cm, height_cm, area_cm2, log_area
형태 정보: aspect_ratio, is_extreme_aspect_ratio
깊이/입체 정보: depth_cm, has_depth, is_3d_candidate
재료/지지체 정보: medium_category, support_category, medium_support_bucket
```

반대로 다음은 `base_existing_combo`에 포함되지 않는다.

```text
artist_name_ko
artist_works_log
ln_estimated_ho
artist_key x ho interaction
artist_name_ko x log_area interaction
artist_name_ko x ln_estimated_ho interaction
```

따라서 `base_existing_combo`는 작가 기준선과 작품 구조를 넓게 포함하지만, 작가 학습량이나 작가별 호수 프리미엄까지 반영하는 피처셋은 아니다. 이 부분은 후속 후보인 `artist_key + size + ho interaction` 또는 compact `artist_name_ko` 후보에서 별도로 검토했다.

---

## 10. 피처별 영향도 해석

피처별 영향도 해석은 별도 문서로 분리했다.

- 상세 문서: `docs/track6/experiments/track6_feature_influence_with_results.md`

이 문서에서는 다음 내용을 실험 결과표와 함께 확인할 수 있다.

- Warm Huber의 `PRE-WARM-07` group-drop 결과
- Warm 후보 재선정 `PRE-WARM` 결과
- Warm validation/test/OOF 비교 `PRE-WARM-08` 결과
- Cold CatBoost의 SHAP, interaction, leaf segment 해석
- Cold LightGBM의 permutation, tail slice, leaf-wise 해석
- 모델별 후처리 연결 기준

온보딩 문서에서는 핵심 결론만 기억하면 된다.

| 모델 | 피처 영향도 핵심 | 후처리 연결 |
| --- | --- | --- |
| Warm Huber | 작가 기준선과 크기 정보가 핵심 | 전체 residual, 크기 구간, 작가 이력량 구간 |
| Cold CatBoost | 크기 x 깊이 x 재료/형태 조합이 중요 | leaf/segment residual + fallback |
| Cold LightGBM | 크기 피처와 support/size 조합, tail slice가 중요 | pred_bin, size/support bucket, tail 안정화 |

---

## 11. 지금까지의 핵심 실험 정리

### 11.1 A~J 피처 실험

A~J 실험은 피처 후보를 넓게 탐색한 단계다.

목적은 다음이었다.

- 어떤 피처 그룹이 Warm/Cold에서 유효한지 확인
- 작가명, 크기, 재료, 지지체, 작가 메타, 교차항의 효과 비교
- Warm과 Cold에서 같은 피처가 다르게 작동하는지 확인

이 단계에서 Warm은 작가명과 크기 조합이 강했고, Cold는 작품 자체 정보와 조합 피처가 중요하다는 방향이 확인됐다.

### 11.2 WM1 / OPT-W 계열

WM1과 OPT-W 계열은 Warm 후보를 더 좁혀본 실험이다.

이전에는 `artist_name_ko + size` 계열 후보가 test MdAPE `0.154~0.157` 수준으로 좋아 보였다. 하지만 이 결과는 전체 one-hot에 가까운 전처리 조건에서 나온 값이다.

운영 기준 전처리인 `OneHotEncoder(min_frequency=10)`과 `Huber max_iter=3000`로 다시 맞추면 compact 후보는 test MdAPE `0.222~0.225` 수준으로 나온다.

따라서 과거 고성능 후보는 그대로 최종 후보로 채택하지 않고, 운영 기준으로 재검증해야 했다.

### 11.3 FINAL Interpretability

FINAL interpretability 리포트는 모델 내부 해석을 위한 산출물이다.

다만 기존 리포트는 일부 피처셋과 최종 artifact의 피처셋이 다를 수 있어, 이후 Warm/Cold 모델별 해석 리포트를 보강했다.

현재는 다음 방향으로 해석한다.

- Warm Huber: 계수, 실제 기여도, outlier 여부
- Cold CatBoost: SHAP, interaction, leaf segment residual
- Cold LightGBM: permutation, tail slice, leaf-wise 진단

### 11.4 PRE-WARM 계열

Warm 기준 모델을 다시 확인하기 위해 PRE-WARM 실험을 진행했다.

| 실험 | 목적 | 핵심 결론 |
| --- | --- | --- |
| PRE-WARM | final artifact와 기존 compact 후보 비교 | 운영 기준에서는 compact 후보 개선폭이 제한적 |
| PRE-WARM-07 | 후보별 group-drop | 작가와 크기가 핵심, aspect/medium/support 우선순위 낮음 |
| PRE-WARM-08 | validation/test/OOF 비교 | 후처리 기준은 `base_existing_combo` 유지, `artist_key + size + ho interaction`은 보조 후보 |

#### PRE-WARM 결과 상세

`PRE-WARM`은 기존에 더 좋아 보였던 Warm 후보와 현재 final artifact 후보를 운영 기준 전처리로 다시 비교한 실험이다. 여기서 운영 기준 전처리는 `OneHotEncoder(min_frequency=10)`과 `HuberRegressor(max_iter=3000)`이다.

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

이 실험에서 알 수 있는 점은 두 가지다.

- test 기준으로는 compact `artist_name_ko` 후보가 final artifact보다 좋아 보인다.
- 하지만 운영 적용성을 고려하면 `artist_key` 기반 후보도 같이 봐야 한다.

그래서 바로 모델을 교체하지 않고 `PRE-WARM-07`과 `PRE-WARM-08`로 이어서 검증했다.

#### PRE-WARM-07 결과 상세

`PRE-WARM-07`은 위 후보 중 중요한 후보를 대상으로 피처 그룹을 제거해 본 실험이다.

| 핵심 질문 | 실험 결과 | 결론 |
| --- | --- | --- |
| 작가 정보가 정말 필요한가? | 제거 시 MdAPE `0.48~0.49` | 필수 |
| 크기 정보가 정말 필요한가? | 제거 시 MdAPE `0.55~0.56`, p95 `5.2~5.4` | 필수 |
| aspect가 필요한가? | 일부 후보에서 제거 시 MdAPE 개선 | 우선순위 낮음 |
| medium/support가 필요한가? | final artifact에서 제거 시 소폭 개선 | Warm에서는 우선순위 낮음 |
| artist_works가 필요한가? | 제거 시 p95 소폭 악화 | 안정성 보조 피처 |
| ho interaction이 필요한가? | 제거 시 p95 악화 | tail 안정성 보조 피처 |

이 결과 때문에 Warm 후처리 우선순위가 다음처럼 정리됐다.

```text
1순위: 전체 residual 보정
2순위: 크기 구간 보정
3순위: 작가 학습량 또는 ho interaction 기반 안정성 확인
후순위: medium/support, aspect 기반 보정
```

#### PRE-WARM-08 결과 상세

`PRE-WARM-08`은 test 결과만 보고 모델을 바꾸는 위험을 막기 위해 validation, test, train OOF를 함께 비교한 실험이다. 여기서 OOF는 학습 데이터 안에서 다시 검증 예측을 만든 값이다.

| 후보 | Validation MdAPE | Validation p95 | Test MdAPE | Test p95 | OOF MdAPE | 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `final artifact base_existing_combo` | `0.2124` | `1.3191` | `0.2274` | `2.0128` | `0.1942` | 후처리 기준 유지 |
| `artist_key + size + ho interaction` | `0.2260` | `1.4768` | `0.2271` | `1.8977` | `0.1834` | 보조 후보 |
| `artist_name_ko + size + artist_works` | `0.2299` | `1.4667` | `0.2221` | `1.9218` | `0.1981` | 보류 |
| `artist_name_ko + size + artist_works no aspect` | `0.2305` | `1.4835` | `0.2208` | `1.9234` | `0.1987` | 보류 |

`PRE-WARM-08`의 결론은 다음이다.

- validation 기준으로는 `base_existing_combo`가 가장 좋다.
- test 기준으로는 compact `artist_name_ko` 후보가 좋아 보인다.
- OOF 기준으로는 `artist_key + size + ho interaction`의 MdAPE가 좋다.
- 따라서 test만 보고 모델을 바꾸지 않는다.
- 후처리 기준은 `base_existing_combo`를 유지한다.
- `artist_key + size + ho interaction`은 보조 비교 후보로 둔다.
- `artist_name_ko` 후보는 validation 성능과 feature export 정합성 문제로 보류한다.

---

## 12. Warm 기준 모델 재검토 결과

Warm 모델을 다시 본 이유는 test 기준으로 더 좋아 보이는 후보가 있었기 때문이다.

그러나 모델을 바꿀 때는 test 성능만 보면 안 된다. validation, OOF, 운영 feature export 가능성을 함께 봐야 한다. feature export는 실험에서 쓴 피처를 실제 운영 예측 입력으로도 같은 방식으로 뽑아낼 수 있는지를 뜻한다.

PRE-WARM-08 결과는 다음과 같다.

| 후보 | Validation MdAPE | Test MdAPE | OOF MdAPE | 판단 |
| --- | ---: | ---: | ---: | --- |
| `base_existing_combo` | `0.2124` | `0.2274` | `0.1942` | 후처리 기준 유지 |
| `artist_key + size + ho interaction` | `0.2260` | `0.2271` | `0.1834` | 보조 후보 |
| `artist_name_ko + size + artist_works` | `0.2299` | `0.2221` | `0.1981` | feature export 정합성 문제로 보류 |
| `artist_name_ko + size + artist_works no aspect` | `0.2305` | `0.2208` | `0.1987` | test는 좋지만 validation에서 낮아 보류 |

현재 결론은 다음이다.

```text
Warm 후처리 기준 모델은 base_existing_combo를 유지한다.
artist_key + size + ho interaction은 tail 안정성 보조 후보로 남긴다.
artist_name_ko compact 후보는 feature export 정합성 수정 전에는 운영 후보로 확정하지 않는다.
```

### 12.1 Warm CatBoost 추가 검증 가설

현재 Warm 기준은 Huber지만, Warm에서도 CatBoost를 추가로 실험해볼 필요가 있다.

가설은 다음이다.

```text
Warm 가격 예측에서는 작가별 기준 가격대뿐 아니라,
작가별로 작품 크기, 재료, 형태가 가격에 반영되는 방식이 다를 수 있다.

Huber는 선형 모델이라 작가 효과와 크기 효과를 더하는 방식으로 설명한다.
반면 CatBoost는 대칭 트리 구조를 사용하므로,
작가별 작품 크기 구간이나 작가 x 크기 x 재료 조합을 조건 분기로 나누어 학습할 수 있다.

따라서 Warm에서도 CatBoost가 Huber보다 특정 작가/크기 구간의 가격 패턴을 더 잘 잡을 수 있는지 확인한다.
```

쉽게 말하면 다음과 같다.

```text
Huber:
작가 효과 + 크기 효과 + 재료 효과를 더해서 예측

Warm CatBoost:
작가가 누구인가?
그 작가의 작품이 큰 편인가?
재료나 형태가 어떤가?
이 조건 조합이 어떤 가격 구간으로 가는가?
```

이 실험에서 기대하는 효과는 다음이다.

| 기대 효과 | 설명 |
| --- | --- |
| 작가별 크기 구간 학습 | 어떤 작가는 대형 작품에서 가격이 크게 오르고, 어떤 작가는 크기 효과가 약할 수 있음 |
| 작가 x 재료/형태 조합 학습 | 특정 작가의 특정 재료나 형태가 가격대와 연결될 수 있음 |
| 비선형 가격 구조 반영 | Huber의 선형 계수로 설명하기 어려운 조건 조합을 CatBoost가 나눌 수 있음 |
| tail 구간 개선 가능성 | 특정 작가/크기 구간에서 반복되는 큰 오차를 줄일 가능성 |

다만 이 실험은 반드시 validation, OOF, test를 함께 봐야 한다. CatBoost는 작가 정보를 너무 강하게 외울 수 있으므로, test만 좋아졌다고 바로 기준 모델로 바꾸면 안 된다.

우선 비교할 실험은 다음이다.

| 실험 ID | 대상 | 기준 비교 | 목적 |
| --- | --- | --- | --- |
| `W-CB-01` | Warm CatBoost `base_existing_combo` | Warm Huber `base_existing_combo` | 같은 피처셋에서 모델 구조만 바꿨을 때 성능이 개선되는지 확인 |
| `W-CB-02` | Warm CatBoost `artist_key + size` 계열 | Warm Huber 보조 후보 | 작가별 크기 구간을 CatBoost가 더 잘 잡는지 확인 |
| `W-CB-03` | Warm CatBoost `artist_key + size + material/support` | Warm Huber 기준 후보 | 작가 x 크기 x 재료/지지체 조합 효과 확인 |

성공 기준은 다음이다.

```text
validation MdAPE가 Huber보다 개선된다.
또는 p95_APE가 줄어든다.
또는 특정 작가/크기 구간의 큰 오차가 줄고 전체 성능이 유지된다.
```

실패 또는 보류 기준은 다음이다.

```text
validation은 나빠지고 test만 좋아진다.
OOF와 validation이 불안정하다.
작가 수가 적은 구간에서만 성능이 좋아진다.
feature export 또는 운영 적용이 어렵다.
```

---

## 13. Cold 모델 현재 상태

Cold는 Warm보다 어렵다. 이유는 작가 기준 가격대를 직접 사용하기 어렵기 때문이다.

현재 Cold 후보는 다음과 같다.

| 모델 | 피처셋 | 역할 |
| --- | --- | --- |
| CatBoost | `base_medium_shape` | Cold 주력 후보 |
| LightGBM | `base_support_size` | Cold 보조/비교 후보 |

CatBoost와 LightGBM은 모두 트리 모델이지만 구조가 다르다.

CatBoost는 대칭 트리 구조이므로 반복되는 조건 조합을 안정적으로 나누는 데 강점이 있다. 따라서 `leaf/segment`, `medium_shape_bucket`, `shape_bucket` 기반 후처리가 적합하다.

LightGBM은 leaf-wise 구조이므로 특정 구간을 깊게 파고들 수 있다. 이 때문에 일부 tail 구간에서 큰 오차가 생길 수 있다. 따라서 `pred_bin`, `size_bucket`, `support_size_bucket` 기반 보정과 tail 안정화가 중요하다.

---

## 14. 후처리 실험 계획

후처리는 모델이 반복적으로 높게 또는 낮게 예측하는 구간을 조정하는 작업이다.

후처리를 하기 전에 기준 모델을 확정해야 한다. 기준 모델이 바뀌면 residual이 바뀌고, residual이 바뀌면 보정값도 모두 달라진다.

현재 후처리 우선순위는 다음과 같다.

### 14.1 상세 보정값 산출 실험

후처리 실험의 첫 단계는 보정값을 더 상세하게 뽑는 것이다. 전체 모델에 하나의 보정값만 적용하면 어떤 조건에서 반복 오차가 생기는지 알기 어렵다.

추가로 Warm과 Cold 모두에서 CatBoost를 구분 학습한 뒤 보정값을 비교한다. 이 실험은 “구분 학습 자체가 예측을 개선하는지”뿐 아니라, “구분 학습 후 필요한 보정값이 줄어드는지”를 확인하기 위한 것이다.

구분 학습의 의미는 다음과 같다.

```text
전체 CatBoost:
모든 Warm 또는 Cold 작품을 한 모델로 학습

구분 학습 CatBoost:
작품 크기, 작가 학습량, 작가 x 크기, 2D/3D, 재료/형태 구간별로 데이터를 나누고
각 구간에 맞는 CatBoost 모델을 따로 학습
```

비교 구조는 다음이다.

| 비교 대상 | 확인 내용 |
| --- | --- |
| 전체 CatBoost 보정 전 | 하나의 CatBoost 모델이 만든 기본 예측 성능 |
| 전체 CatBoost + 상세 보정 | 모델은 하나로 두고 segment 보정만 적용했을 때 효과 |
| 구분 학습 CatBoost 보정 전 | 조건별 모델 학습 자체가 성능을 개선하는지 |
| 구분 학습 CatBoost + 상세 보정 | 조건별 학습과 조건별 보정을 함께 쓰면 보정값과 성능이 안정되는지 |

그 다음 validation 기준으로 correction map을 만든다.

```text
pred_log = model.predict(features)
residual_log = actual_log - pred_log
segment_correction = median(residual_log in same segment)
corrected_pred_log = pred_log + segment_correction
corrected_pred_price = exp(corrected_pred_log)
```

여기서 `segment_correction`은 같은 구간에 속한 샘플들의 residual_log 중앙값이다.

우선 산출할 보정값은 다음이다.

| 대상 모델 | 우선 보정 구간 | 목적 |
| --- | --- | --- |
| Warm Huber | overall, pred_bin, size_bucket | 전체/예측가/크기 구간 편향 확인 |
| Warm Huber | artist_works_bucket, artist_size_segment | 작가 학습량과 작가별 크기 구간 편향 확인 |
| Warm CatBoost 후보 | pred_bin, size_bucket, artist_size_segment, leaf_segment | CatBoost가 잡은 작가/크기 조건 조합의 반복 오차 확인 |
| Warm 구분 학습 CatBoost | split_segment, artist_size_segment, leaf_segment | 구분 학습 후에도 남는 보정값 확인 |
| Cold CatBoost | leaf_segment, medium_shape_bucket, shape_bucket, overall | 대칭 트리 segment 기반 보정값 산출 |
| Cold 구분 학습 CatBoost | split_segment, leaf_segment, medium_shape_bucket | 구분 학습 후에도 남는 보정값 확인 |
| Cold LightGBM | pred_bin, size_bucket, support_size_bucket, tail_risk_segment | tail 위험 구간 보정값 산출 |

correction map에는 최소한 다음 정보를 남긴다.

```text
model_name
segment_type
segment_value
rows
median_residual_log
MdAPE_before / MdAPE_after
p95_APE_before / p95_APE_after
RMSE_log_before / RMSE_log_after
```

안전장치는 다음과 같다.

```text
segment rows >= 50이면 해당 segment 보정값 사용
segment rows < 50이면 상위 fallback 보정값 사용
보정값이 너무 크면 clip 적용
validation에서 계산한 보정값을 test에 그대로 적용
```

이 실험의 목적은 단순히 성능표를 보는 것이 아니라, “어떤 조건에서 어떤 방향으로 얼마나 보정해야 하는가”를 표로 남기는 것이다.

### 14.2 모델별 커스텀 보정

상세 보정값을 뽑은 뒤에는 모델별 특성에 맞는 보정을 따로 검증한다. 같은 residual 보정이라도 Huber, CatBoost, LightGBM에 맞는 기준은 다르다.

| 대상 모델 | 커스텀 보정 기준 | 이유 |
| --- | --- | --- |
| Warm Huber | 큰 오차 구간, 예측가 구간, 크기 구간 | Huber는 큰 오차 샘플의 학습 영향력을 줄이므로, 학습 후에도 남는 큰 오차 구간을 별도로 확인해야 한다. |
| Warm Huber | size/medium/artist 계수 기여도 구간 | 선형 모델은 피처별 기여도를 직접 계산할 수 있으므로, 특정 피처 기여가 큰 구간에서 반복 오차가 남는지 볼 수 있다. |
| Warm CatBoost 후보 | leaf_segment, artist_size_segment | CatBoost는 조건 조합을 leaf로 나누므로, 작가 x 크기 조합이나 leaf별 반복 오차를 보는 것이 자연스럽다. |
| Cold CatBoost | leaf_segment, medium_shape_bucket, shape_bucket | Cold는 작가 기준선이 약하므로, CatBoost가 나눈 작품 조건 조합별 보정이 중요하다. |
| Cold CatBoost | depth_3d_segment, size_bucket, medium_shape_bucket | 2D/3D와 크기 조합은 큰 오차가 생기기 쉬운 구간이므로 따로 확인한다. |
| Cold LightGBM | high pred_bin, support_size_bucket, tail_risk_segment | LightGBM은 세밀한 구간을 깊게 나누기 쉬워 고가/큰 오차 tail 구간 보정이 중요하다. |

이 단계의 핵심은 “어떤 모델에 어떤 보정이 더 맞는지”를 설명 가능하게 만드는 것이다.

### 14.3 Warm 후처리

기준 모델:

```text
Warm Huber base_existing_combo
```

보조 비교 후보:

```text
Warm Huber artist_key + size + ho interaction
```

우선 실험:

| 실험 | 목적 | 기준 |
| --- | --- | --- |
| PP-A1-W | 전체 median residual 보정 | 전체적으로 높게/낮게 치우쳤는지 확인 |
| PP-A3-W | 크기 구간별 residual 보정 | size 제거 시 성능이 급락했으므로 필수 |
| PP-A5-W | 작가 학습량 구간 보정 | artist_works가 p95에 일부 기여했으므로 확인 |

Warm에서는 medium/support나 aspect 기반 보정의 우선순위를 낮춘다.

### 14.4 Cold CatBoost 후처리

기준 모델:

```text
Cold CatBoost base_medium_shape
```

우선 실험:

| 실험 | 목적 |
| --- | --- |
| CatBoost leaf/segment residual 보정 | 트리 leaf 패턴별 반복 오차 확인 |
| medium_shape fallback 보정 | leaf 표본 부족 시 상위 구간 보정 |
| shape/medium fallback 보정 | 더 넓은 구간 기준 보정 |
| overall residual fallback | 표본 부족 구간의 최종 안전장치 |

CatBoost는 전체 보정보다 segment 기반 보정이 더 자연스럽다.

### 14.5 Cold LightGBM 후처리

기준 모델:

```text
Cold LightGBM base_support_size
```

우선 실험:

| 실험 | 목적 |
| --- | --- |
| pred_log bin 보정 | 예측 가격대별 치우침 확인 |
| size_bucket 보정 | 크기 구간별 tail 위험 확인 |
| support_size_bucket 보정 | 지지체 x 크기 조합별 오차 확인 |
| tail slice 안정화 | p95_APE가 큰 구간 방어 |

LightGBM은 tail risk가 크므로 MdAPE 개선보다 p95 안정화를 더 중요하게 봐야 한다.

---

## 15. 앞으로의 실행 순서

후속 실험은 다음 순서로 진행한다.

```text
1. 상세 보정값 산출
   - Warm Huber correction map
   - Warm CatBoost 후보 correction map
   - Cold CatBoost correction map
   - Cold LightGBM correction map

2. 모델별 커스텀 보정 검증
   - Warm Huber 큰 오차/계수 기여도 보정
   - Warm CatBoost leaf/artist-size 보정
   - Cold CatBoost leaf/medium-shape 보정
   - Cold LightGBM tail 구간 보정

3. Warm 기준 후처리 실행
   - PP-A1-W
   - PP-A3-W
   - PP-A5-W

4. Cold CatBoost 후처리 실행
   - leaf/segment residual
   - medium_shape fallback
   - shape/medium fallback

5. Cold LightGBM 후처리 실행
   - pred_bin residual
   - size/support_size residual
   - tail slice 안정화

6. 가격 범위/신뢰도 실험
   - Warm/Cold별 가격 범위
   - 신뢰도 등급
   - 고위험 구간 표시

7. 최종 후보 통합 비교
   - 보정 전/후 비교
   - validation 기준 선택
   - test 최종 확인
```

각 단계에서 반드시 지켜야 할 원칙은 다음이다.

- validation에서 보정 기준을 만든다.
- test는 최종 확인에만 사용한다.
- Warm과 Cold는 합쳐서 판단하지 않는다.
- 모델 구조에 맞는 후처리 방식을 사용한다.
- MdAPE만 보지 않고 p95_APE를 함께 본다.
- 운영에서 만들 수 없는 피처는 최종 후보에서 제외한다.

---

## 16. 참고 파일 목록

| 구분 | 파일 |
| --- | --- |
| 발표용 온보딩 | `docs/track6/experiments/junior_presentation_onboarding_guide.md` |
| 모델 구조 해석 | `docs/track6/experiments/model_structure_based_interpretation_report.md` |
| 후속 실험 계획 | `docs/track6/experiments/followup_experiment_plan.md` |
| 후처리 실험 매트릭스 | `docs/track6/experiments/postprocessing_experiment_matrix.md` |
| Warm 재선정 실험 | `experiments/track6/PRE-WARM_warm_baseline_reselection/README.md` |
| Warm group-drop | `experiments/track6/PRE-WARM-07_warm_group_drop_ablation/README.md` |
| Warm validation/OOF 비교 | `experiments/track6/PRE-WARM-08_warm_final_candidate_validation/README.md` |
| 최종 interpretability HTML | `experiments/track6/FINAL_model_interpretability/outputs/interpretability_report.html` |
