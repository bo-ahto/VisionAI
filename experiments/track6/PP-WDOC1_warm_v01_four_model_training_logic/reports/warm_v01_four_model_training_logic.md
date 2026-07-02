# Warm v0.1 네 가지 예측 축의 학습 방식, 피쳐, 조합 수식

- 작성일: 2026-06-08
- 범위: Warm 작가, 즉 학습 데이터에 작가 식별자가 존재하는 작품의 가격 예측 구조
- 기준 후보: `blend_svcnum_ppv8_wsvc_0.70`
- 최종 정책 파일: `models/track6/price_prediction_v0.1/config/model_policy_v0.1.json`

이 문서는 실험명만 보고 이해해야 하는 구조를 피하기 위해, 코드 컬럼명을 사람이 읽기 쉬운 변수명으로 다시 정의한다. 원래 코드 컬럼명은 재현을 위해 별도 대응표에 남긴다.

## 1. 문서 읽는 순서

이 문서는 최종식을 먼저 설명하지 않고, 후보 1, 2, 3, 4가 각각 어떤 피쳐와 어떤 순서로 예측 로그가격을 만드는지 먼저 설명한다. 마지막에 네 후보를 한 번에 비교하고, 왜 최종 Warm 기준이 70:30 조합으로 선택됐는지 정리한다.

### 1.1 후보별 역할 요약

| 후보 축 | 자체 예측을 만드는 방식 | 최종 70:30 식에 들어가는가 |
|---|---|---|
| 유사작품통계 Huber seed 평균 | 유사작품 숫자 통계를 넣은 Huber 모델 10개 seed 평균 | 예. 70% 가중치 |
| 유사작품통계+신뢰피쳐 Huber seed 평균 | 숫자 통계에 그룹 수준/신뢰도 범주까지 넣은 Huber 모델 10개 seed 평균 | 아니오. 비교 후보로만 사용 |
| PPV6 다중후보 안정 블렌드 | 여러 Warm 후보 예측값을 validation 기준으로 가중 결합 | 아니오. 비교 후보로만 사용 |
| PPV8 compact 안정 블렌드 | V2 방어형 후보와 L10 생성버킷 후보를 75:25로 결합 | 예. 30% 가중치 |

이 표의 최종식은 뒤의 `최종 비교와 Warm 70:30 선택` 장에서 다시 설명한다. 중요한 점은 후보 1, 2, 3, 4가 모두 같은 예측식으로 움직이는 것이 아니라, 각자 다른 방식으로 예측 로그가격을 만든 뒤 마지막 비교 단계에서 선택된다는 것이다.

```text
1단계: 네 후보가 각각 자기 방식으로 예측 로그가격을 만든다.
  후보1 = 유사작품통계_Huber_seed평균_로그가격
  후보2 = 유사작품통계_신뢰피쳐포함_Huber_seed평균_로그가격
  후보3 = PPV6_다중후보_안정블렌드_로그가격
  후보4 = PPV8_안정블렌드_로그가격

2단계: validation에서 선택된 후보1과 후보4만 최종식에 넣는다.
```

## 2. 용어와 변수명

| 문서 변수명 | 코드 컬럼명 또는 후보명 | 의미 |
|---|---|---|
| `작품_실제_로그가격` | `ln_price_krw`, `actual_log` | 정답 가격을 KRW 기준 자연로그로 변환한 값 |
| `작품_예측_로그가격` | `pred_log` | 모델이 예측하는 값. 모든 결합은 가격이 아니라 로그가격에서 수행 |
| `유사작품그룹_중앙값_로그가격` | `svc_group_log_price_median` | 조건이 비슷한 학습 작품 그룹의 로그가격 중앙값 |
| `유사작품그룹_가격범위폭` | `svc_group_log_price_iqr` | 유사작품그룹의 75% 분위 로그가격 minus 25% 분위 로그가격 |
| `유사작품그룹_면적단가_중앙값` | `svc_group_log_unit_area_median` | `log(price_krw) - log(area_cm2)`의 그룹 중앙값 |
| `유사작품그룹_표본수_로그` | `svc_group_n_log` | `log(1 + svc_group_n)` |
| `유사작품그룹_선택수준` | `svc_group_level` | 작가+재료+크기, 작가+크기, 작가 전체 등 어떤 그룹을 사용했는지 |
| `유사작품그룹_신뢰구간` | `svc_coverage_tier` | 그룹 표본 수에 따른 `high_n`, `medium_n`, `low_n`, `fallback_global` |
| `유사작품통계_Huber_seed평균_로그가격` | `svc_numeric_seed_mean` | 유사작품 숫자 통계 피쳐를 넣은 Huber 모델 10개 seed 평균 |
| `유사작품통계_신뢰피쳐포함_Huber_seed평균_로그가격` | `svc_full_seed_mean` | 숫자 통계에 그룹 수준/신뢰도 범주 피쳐까지 넣은 Huber seed 평균 |
| `PPV6_다중후보_안정블렌드_로그가격` | `pp_v6_fine_blend_mape_guarded` | 여러 Warm 후보 예측값을 validation 기준으로 가중 결합한 후보 |
| `PPV8_안정블렌드_로그가격` | `pp_v8_compact_blend_mape_guarded` | 더 적은 후보만 사용하도록 단순화한 안정 블렌드 후보 |
| `최종_Warm_로그가격` | `blend_svcnum_ppv8_wsvc_0.70`, `WARM_BASE_RAW_V1` | Warm v0.1 최종 기준 로그가격 |

## 3. 학습 데이터와 검증 기준

Warm 모델은 `data/track6_split` 및 `models/track6/price_prediction_v0.1/data/training/track6_split`의 고정 split을 사용한다.

| 구분 | 역할 | 확인된 행 수 |
|---|---|---:|
| Train | Huber 및 유사작품 통계 산출에 사용 | Warm Huber manifest 기준 27,433건 |
| Validation | 조합 가중치와 후보 선택에 사용 | 519건 |
| Test | 선택 후 최종 성능 확인에만 사용 | 607건 |

중요한 원칙은 validation에서 후보와 가중치를 선택하고, test는 선택된 후보가 실제로 유지되는지 확인하는 용도로만 쓴다는 점이다.

## 4. 공통 피쳐 생성

### 4.1 기본 작품/작가 피쳐

Warm Huber 계열의 기본 피쳐는 아래와 같다.

| 피쳐 묶음 | 사용 피쳐 |
|---|---|
| 크기/형태 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `is_extreme_aspect_ratio` |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` |
| 작가 식별 | `artist_key` |

추가로 유사작품 통계를 계산할 때는 `size_bucket`, `shape_bucket`, `medium_size_bucket`, `support_size_bucket`, `medium_shape_bucket`, `is_large_2d`, `is_large_3d` 같은 파생 버킷을 만든다. `size_bucket`은 train의 `log_area` 분위수로 만든 크기 구간이고, `shape_bucket`은 `aspect_ratio`를 세로형, 균형형, 가로형, 극단 가로형으로 나눈 값이다.

### 4.2 유사작품그룹 선택 로직

새 작품마다 아래 우선순서로 학습 데이터에서 유사작품그룹을 찾는다. 조건을 만족하는 첫 그룹을 사용한다.

| 우선순위 | 그룹 키 | 최소 표본 수 | 문서상 의미 |
|---:|---|---:|---|
| 1 | `artist_key + medium_support_bucket + size_bucket` | 5 | 같은 작가, 비슷한 재료/지지체, 비슷한 크기 |
| 2 | `artist_key + size_bucket` | 5 | 같은 작가, 비슷한 크기 |
| 3 | `artist_key` | 5 | 같은 작가 전체 이력 |
| 4 | `medium_support_bucket + size_bucket` | 30 | 비슷한 재료/지지체와 크기 |
| 5 | `medium_category + support_category + size_bucket` | 30 | 재료, 지지체, 크기 |
| 6 | `medium_category + size_bucket` | 50 | 재료와 크기 |
| 7 | 전체 train | 제한 없음 | 위 조건이 모두 실패할 때의 fallback |

각 그룹에서 계산하는 값은 다음과 같다.

```text
유사작품그룹_중앙값_로그가격 = median(log(price_krw))
유사작품그룹_Q25_로그가격 = quantile(log(price_krw), 0.25)
유사작품그룹_Q75_로그가격 = quantile(log(price_krw), 0.75)
유사작품그룹_가격범위폭 = 유사작품그룹_Q75_로그가격 - 유사작품그룹_Q25_로그가격

작품_로그면적단가 = log(price_krw) - log(max(area_cm2, 1))
유사작품그룹_면적단가_중앙값 = median(작품_로그면적단가)
유사작품그룹_면적단가_범위폭 = Q75(작품_로그면적단가) - Q25(작품_로그면적단가)
유사작품그룹_표본수_로그 = log(1 + 유사작품그룹_표본수)
```

신뢰구간은 표본 수로 나눈다.

```text
if 그룹수준 == "global": 유사작품그룹_신뢰구간 = "fallback_global"
else if 표본수 >= 50: 유사작품그룹_신뢰구간 = "high_n"
else if 표본수 >= 15: 유사작품그룹_신뢰구간 = "medium_n"
else: 유사작품그룹_신뢰구간 = "low_n"
```

## 5. 후보 1: 유사작품통계 Huber seed 평균

문서 변수명은 `유사작품통계_Huber_seed평균_로그가격`이다. 코드 후보명은 `svc_numeric_seed_mean`이다.

이 축은 유사작품 통계의 숫자 피쳐만 추가한 Huber 회귀 모델이다. 단일 모델을 한 번만 학습하지 않고, train 내부 유사작품 통계 산출 fold를 바꾸는 seed 10개를 반복한 뒤 평균을 낸다.

### 5.1 후보 1의 사용 피쳐

```text
기본 Warm 피쳐
+ 유사작품그룹_중앙값_로그가격
+ 유사작품그룹_Q25_로그가격
+ 유사작품그룹_Q75_로그가격
+ 유사작품그룹_가격범위폭
+ 유사작품그룹_면적단가_중앙값
+ 유사작품그룹_면적단가_범위폭
+ 유사작품그룹_표본수_로그
```

피쳐를 코드 컬럼명으로 쓰면 아래와 같다.

| 묶음 | 코드 컬럼 |
|---|---|
| 기본 크기/형태 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `is_extreme_aspect_ratio` |
| 기본 재료/작가 | `medium_category`, `support_category`, `medium_support_bucket`, `artist_key` |
| 유사작품 숫자 통계 | `svc_group_log_price_median`, `svc_group_log_price_q25`, `svc_group_log_price_q75`, `svc_group_log_price_iqr`, `svc_group_log_unit_area_median`, `svc_group_log_unit_area_iqr`, `svc_group_n_log` |

### 5.2 후보 1의 학습/예측 순서

1. Train을 5개 fold로 나눈다.
2. 각 train 행의 유사작품 통계는 자기 자신의 가격이 새지 않도록, 해당 행이 속한 fold를 제외한 train으로만 계산한다.
3. Validation과 test의 유사작품 통계는 전체 train으로 계산한다.
4. 숫자 피쳐는 median imputation 후 표준화한다.
5. 범주 피쳐는 결측을 `__MISSING__`으로 채우고 one-hot encoding한다.
6. HuberRegressor를 target `log(price_krw)`에 맞춰 학습한다.
7. seed 10개 모델의 예측 로그가격을 평균한다.

### 5.3 후보 1의 예측식

```text
각 seed s에 대해:
  유사작품숫자_Huber_s = HuberRegressor(
      epsilon = 1.35,
      alpha = 0.0001,
      max_iter = 4000
  )

  seed별_예측로그가격_s = 유사작품숫자_Huber_s(작품피쳐, 유사작품숫자통계)

유사작품통계_Huber_seed평균_로그가격
  = average(seed별_예측로그가격_202606030 ... seed별_예측로그가격_202606039)
```

Huber 회귀는 큰 오차 샘플의 영향이 과도하게 커지지 않도록 아래 형태의 robust loss를 최소화한다.

```text
minimize_beta sum_i HuberLoss_epsilon(실제로그가격_i - 예측로그가격_i)
              + alpha * ||beta||^2
```

### 5.4 후보 1의 역할

후보 1은 최종 Warm 70:30 식의 70% 축으로 선택됐다. 고정 test 성능은 `MdAPE 0.1520`, `MAPE 0.2942`, `p95_APE 0.9381`, `RMSE_log 0.4179`였다. 단독 성능보다 최종 조합 성능이 좋아진 이유는 후보 4의 평균오차 방어 성격과 결합되기 때문이다.

## 6. 후보 2: 유사작품통계와 신뢰피쳐를 모두 넣은 Huber seed 평균

문서 변수명은 `유사작품통계_신뢰피쳐포함_Huber_seed평균_로그가격`이다. 코드 후보명은 `svc_full_seed_mean`이다.

후보 2는 후보 1과 같은 Huber seed 평균 구조를 쓰지만, 유사작품그룹의 숫자 통계 외에 그룹 수준과 신뢰도 범주 피쳐를 함께 넣는다. 즉 유사작품그룹이 작가 단위인지, 재료/크기 단위인지, 표본 수가 충분한지까지 모델이 직접 보게 하는 후보이다.

### 6.1 후보 2의 사용 피쳐

후보 2는 후보 1의 모든 피쳐를 사용하고 아래 범주 피쳐를 추가한다.

```text
유사작품그룹_선택수준 = svc_group_level
유사작품그룹_신뢰구간 = svc_coverage_tier
작가수준_그룹사용여부 = svc_has_artist_level
```

| 묶음 | 코드 컬럼 |
|---|---|
| 후보 1 전체 피쳐 | 후보 1의 기본 피쳐 + 유사작품 숫자 통계 |
| 유사작품 신뢰 범주 | `svc_group_level`, `svc_coverage_tier`, `svc_has_artist_level` |

### 6.2 후보 2의 학습/예측 순서

1. Train을 5개 fold로 나눈다.
2. 각 train 행의 유사작품 숫자 통계와 신뢰 범주는 자기 fold를 제외한 train으로 계산한다.
3. Validation과 test의 유사작품 통계와 신뢰 범주는 전체 train으로 계산한다.
4. 숫자 피쳐는 median imputation 후 표준화한다.
5. 범주 피쳐는 결측을 `__MISSING__`으로 채우고 one-hot encoding한다.
6. HuberRegressor를 target `log(price_krw)`에 맞춰 학습한다.
7. seed 10개 모델의 예측 로그가격을 평균한다.

### 6.3 후보 2의 예측식

```text
각 seed s에 대해:
  유사작품신뢰포함_Huber_s = HuberRegressor(
      epsilon = 1.35,
      alpha = 0.0001,
      max_iter = 4000
  )

  seed별_예측로그가격_s
    = 유사작품신뢰포함_Huber_s(작품피쳐, 유사작품숫자통계, 유사작품신뢰범주)

유사작품통계_신뢰피쳐포함_Huber_seed평균_로그가격
  = average(신뢰피쳐포함_Huber_seed별_예측로그가격_s)
```

### 6.4 후보 2의 역할

후보 2는 최종식에는 들어가지 않았다. 1번 축보다 p95는 조금 낫지만, 최종 선택에서는 MAPE와 결합 안정성이 더 좋은 후보 1이 선택됐다. 고정 test 성능은 `MdAPE 0.1533`, `MAPE 0.2956`, `p95_APE 0.9190`, `RMSE_log 0.4168`였다.

## 7. 후보 3: PPV6 다중후보 안정 블렌드

문서 변수명은 `PPV6_다중후보_안정블렌드_로그가격`이다. 코드 후보명은 `pp_v6_fine_blend_mape_guarded`이다.

이 축은 새 회귀 모델을 학습하는 방식이 아니라, 이미 만들어진 여러 Warm 후보의 로그가격 예측값을 validation 기준으로 가중 결합한다. 즉 final layer에서 사용하는 피쳐는 원본 작품 피쳐가 아니라 후보 모델들의 `예측 로그가격`이다.

### 7.1 후보 3의 사용 피쳐

후보 3의 직접 입력은 작품 원본 피쳐가 아니라 아래 하위 후보들의 예측 로그가격이다.

| 문서 변수명 | 역할 |
|---|---|
| `L9_Huber_Quantile_Residual_로그가격` | Huber, quantile, residual 보정을 순차 적용한 후보 |
| `작가이력_라우팅_로그가격` | 작가 이력 구간에 따라 후보를 라우팅한 예측값 |
| `유사작품_Fallback_로그가격` | 유사작품 기반 fallback 후보 |
| `L10_작가메타_외부검색_순차보정_로그가격` | 작가 메타/외부 검색 피쳐를 반영한 순차 보정 후보 |
| `L10_생성버킷_순차보정_로그가격` | 생성 버킷 피쳐를 반영한 순차 보정 후보 |

### 7.2 후보 3의 결합 순서

1. 각 하위 후보의 validation/test 예측 로그가격을 불러온다.
2. `_track6_row_id` 기준으로 같은 작품 row에 맞춰 병합한다.
3. Validation에서 0.10 단위 weight grid를 탐색한다.
4. `MdAPE`가 validation 최저 단일 후보의 `1.08배` 이내인 조합만 허용한다.
5. 허용된 조합 중 `MAPE`가 가장 낮은 조합을 `mape_guarded`로 선택한다.
6. 선택된 weight를 test와 운영 후보 비교에 그대로 적용한다.

### 7.3 후보 3의 예측식

```text
PPV6_다중후보_안정블렌드_로그가격
  = 0.10 * L9_Huber_Quantile_Residual_로그가격
  + 0.30 * 작가이력_라우팅_로그가격
  + 0.20 * 유사작품_Fallback_로그가격
  + 0.20 * L10_작가메타_외부검색_순차보정_로그가격
  + 0.20 * L10_생성버킷_순차보정_로그가격
```

### 7.4 후보 3의 역할

후보 3은 최종식에는 들어가지 않았다. PP계열 비교 후보로 사용됐고, 후보 4인 PPV8보다 MAPE가 높아 최종 30% 축으로 선택되지 않았다. 고정 test 성능은 `MdAPE 0.1613`, `MAPE 0.2889`, `p95_APE 0.9314`, `RMSE_log 0.4079`였다.

## 8. 후보 4: PPV8 compact 안정 블렌드

문서 변수명은 `PPV8_안정블렌드_로그가격`이다. 코드 후보명은 `pp_v8_compact_blend_mape_guarded`이다.

PPV8은 PPV6보다 배포 구조를 단순화하기 위해 네 개 후보만 사용한다. 최종 선택된 MAPE 방어형 compact blend는 실제로 두 후보만 남겼다.

### 8.1 후보 4의 사용 피쳐

후보 4도 원본 작품 피쳐를 직접 넣는 모델이 아니라, 아래 하위 후보들의 예측 로그가격을 입력으로 쓰는 블렌드이다.

| 문서 변수명 | 원래 후보 |
|---|---|
| `V1_대표후보_로그가격` | `v1_representative` |
| `V2_방어형후보_로그가격` | `v2_defensive` |
| `L10_생성버킷_순차보정_로그가격` | `l10_generated_bucket_seq` |
| `L10_작가메타_외부검색_순차보정_로그가격` | `l10_meta_external_search_seq` |

후보 4의 최종식에는 네 입력 중 두 입력만 남았다. 즉 `V1_대표후보_로그가격`과 `L10_작가메타_외부검색_순차보정_로그가격`은 validation 탐색 후보였지만 최종 weight가 0이라 실제 PPV8 계산식에는 들어가지 않는다.

### 8.2 V2 방어형 후보의 내부 구조

`V2_방어형후보_로그가격`은 코드상 `PP-V2_warm_ppu_feature_augmented_meta_stacking` 실험의 `huber_component_range_clipped` 후보이다. 이 값은 단일 원본 피쳐 모델이 아니라, 여러 기존 Warm 후보의 예측 로그가격을 다시 입력으로 넣은 Huber meta-stacking 결과이다.

입력으로 쓰는 하위 예측값은 다음과 같다.

| 입력 예측값 | 의미 |
|---|---|
| `기본_Huber_로그가격` | Warm 기본 Huber 후보 |
| `L8_순차보정_로그가격` | Quantile/Huber/CatBoost 계열 순차 후보 |
| `L9_순차보정_로그가격` | Huber/Quantile/residual 계열 순차 후보 |
| `D4_블렌드_로그가격` | 기존 Warm 세 모델 블렌드 후보 |
| `R5_p95방어_로그가격` | p95 오차 방어 목적 후보 |
| `R5_MAPE방어_로그가격` | MAPE 방어 목적 후보 |
| `작가이력_라우팅_로그가격` | 작가 이력 구간에 따른 라우팅 후보 |
| `유사작품_fallback_로그가격` | 유사작품 fallback 후보 |
| `U1_생성버킷확장_로그가격` | 생성 bucket 피쳐 확장 후보 |
| `U1_작가크기작품수_로그가격` | 작가+크기+작가 학습량 후보 |

V2는 위 입력 예측값들을 그대로만 쓰지 않고, meta feature를 추가로 만든다.

```text
예측값_평균 = mean(하위후보_예측로그가격들)
예측값_표준편차 = std(하위후보_예측로그가격들)
예측값_범위 = max(하위후보_예측로그가격들) - min(하위후보_예측로그가격들)
기준후보와의_차이_j = 하위후보_j_로그가격 - 기준후보_로그가격
불확실성_폭 = routing_width
```

그 다음 Huber meta-model을 validation에서 5-fold OOF 방식으로 학습한다.

```text
V2_raw_로그가격
  = HuberMetaModel(
      하위후보_예측로그가격들,
      예측값_평균,
      예측값_표준편차,
      예측값_범위,
      기준후보와의_차이들,
      불확실성_폭
    )
```

마지막으로 과도한 외삽을 막기 위해 component range clipping을 적용한다.

```text
하위후보_최소값 = min(하위후보_예측로그가격들)
하위후보_최대값 = max(하위후보_예측로그가격들)

V2_방어형후보_로그가격
  = clip(V2_raw_로그가격, 하위후보_최소값 - 0.03, 하위후보_최대값 + 0.03)
```

따라서 V2는 “기존 후보들의 의견을 보고, Huber 방식으로 한 번 더 안정화한 뒤, 후보 범위 밖으로 너무 멀리 나가지 않게 자른 예측값”으로 이해하면 된다.

### 8.3 L10 생성버킷 순차보정 후보의 내부 구조

`L10_생성버킷_순차보정_로그가격`은 코드상 `PP-L10_warm_l8_feature_variant_sequential` 실험의 `l8_seq__full_plus_generated_buckets` 후보이다. 이 값은 `Quantile -> Huber -> CatBoost residual` 순서로 만든다.

사용 피쳐는 Warm 기본 피쳐에 생성 bucket과 작가 학습량 피쳐를 더한 21개 피쳐이다.

| 묶음 | 사용 피쳐 |
|---|---|
| Warm 기본 피쳐 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `medium_support_bucket`, `is_extreme_aspect_ratio`, `artist_key` |
| 작가 학습량 | `artist_works_log`, `artist_works_count_train` |
| 생성 bucket | `size_bucket`, `shape_bucket`, `support_size_bucket`, `medium_shape_bucket`, `is_large_2d`, `is_large_3d` |

처리 순서는 다음과 같다.

1. CatBoost Quantile 모델 3개를 학습해 q10, q50, q90 로그가격을 예측한다.
2. q10과 q90 차이로 가격 불확실성 폭을 만든다.
3. 원래 피쳐에 q10, q50, q90, quantile_width, price_range_ratio를 추가한다.
4. 추가된 피쳐셋으로 Huber 중심선을 학습한다.
5. train에서 Huber OOF 예측을 만들고, 실제 로그가격과의 차이를 residual target으로 둔다.
6. CatBoost가 residual target을 학습한다.
7. 최종 예측은 Huber 중심선과 CatBoost residual 보정을 더해서 만든다.

수식으로 쓰면 아래와 같다.

```text
q10_log, q50_log, q90_log = CatBoostQuantile(작품피쳐, 생성bucket피쳐)

quantile_width = q90_log - q10_log
price_range_ratio = exp(clip(quantile_width, -10, 10))

L10_Huber_중심선_로그가격
  = Huber(작품피쳐, 생성bucket피쳐, q10_log, q50_log, q90_log, quantile_width, price_range_ratio)

잔차_target
  = 실제_로그가격 - L10_Huber_OOF_중심선_로그가격

CatBoost_잔차보정
  = CatBoostRegressor(작품피쳐, 생성bucket피쳐, quantile피쳐들)

L10_생성버킷_순차보정_로그가격
  = L10_Huber_중심선_로그가격 + CatBoost_잔차보정
```

따라서 L10 생성버킷 후보는 “가격대의 불확실성 폭을 먼저 추정하고, Huber로 중심 가격을 잡은 뒤, 남은 잔차를 CatBoost로 보정한 예측값”으로 이해하면 된다.

### 8.4 후보 4의 결합 순서

1. 네 하위 후보의 validation/test 예측 로그가격을 불러온다.
2. `_track6_row_id` 기준으로 같은 작품 row에 맞춰 병합한다.
3. Validation에서 0.25 단위 weight grid를 탐색한다.
4. `MdAPE`가 validation 최저 단일 후보의 `1.08배` 이내인 조합만 허용한다.
5. 허용된 조합 중 `MAPE`가 가장 낮은 조합을 선택한다.
6. 선택된 weight를 test와 최종 Warm 후보 비교에 그대로 적용한다.

### 8.5 후보 4의 예측식

Validation에서 선택된 `compact_blend_mape_guarded` weight는 아래와 같다.

| 하위 후보 | 선택 weight |
|---|---:|
| `V1_대표후보_로그가격` | 0.00 |
| `V2_방어형후보_로그가격` | 0.75 |
| `L10_생성버킷_순차보정_로그가격` | 0.25 |
| `L10_작가메타_외부검색_순차보정_로그가격` | 0.00 |

그래서 실제 PPV8 안정 블렌드 식은 아래처럼 두 항만 남는다.

```text
PPV8_안정블렌드_로그가격
  = 0.75 * V2_방어형후보_로그가격
  + 0.25 * L10_생성버킷_순차보정_로그가격
```

이 식은 “V2 방어형 후보를 75% 기준으로 삼고, L10 생성버킷 순차보정 후보를 25%만 섞어 보조 보정한다”는 뜻이다. 가격을 직접 75:25로 더하는 것이 아니라, 두 후보의 `로그가격`을 75:25로 더한 뒤 필요할 때 `exp()`로 KRW 가격으로 변환한다.

### 8.6 후보 4의 역할

후보 4는 최종 Warm 70:30 식의 30% 축으로 선택됐다. 단독 MdAPE는 후보 1보다 약하지만, MAPE가 후보 1, 2, 3보다 낮아 평균오차 방어 역할을 한다. 고정 test 성능은 `MdAPE 0.1632`, `MAPE 0.2816`, `p95_APE 0.9311`, `RMSE_log 0.4028`였다.

## 9. 최종 비교와 Warm 70:30 선택

Warm 최종 결합 실험은 아래 네 후보를 같은 validation/test row에 맞춰 놓고 비교한다.

```text
후보1 = 유사작품통계_Huber_seed평균_로그가격
후보2 = 유사작품통계_신뢰피쳐포함_Huber_seed평균_로그가격
후보3 = PPV6_다중후보_안정블렌드_로그가격
후보4 = PPV8_안정블렌드_로그가격
```

### 9.1 후보 1-4 종합 성능 비교

| 후보 축 | Validation MdAPE | Validation MAPE | Validation p95 | Test MdAPE | Test MAPE | Test p95 |
|---|---:|---:|---:|---:|---:|---:|
| 후보 1. 유사작품통계 Huber seed 평균 | 0.1272 | 0.2177 | 0.6504 | 0.1520 | 0.2942 | 0.9381 |
| 후보 2. 유사작품통계+신뢰피쳐 Huber seed 평균 | 0.1274 | 0.2186 | 0.6495 | 0.1533 | 0.2956 | 0.9190 |
| 후보 3. PPV6 다중후보 안정 블렌드 | 0.1530 | 0.2566 | 0.7935 | 0.1613 | 0.2889 | 0.9314 |
| 후보 4. PPV8 compact 안정 블렌드 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 |

해석은 다음과 같다.

- 후보 1과 후보 2는 유사작품통계 Huber 계열이라 validation MdAPE가 낮다.
- 후보 4는 단독 MdAPE는 낮지 않지만 test MAPE가 후보 1, 2, 3보다 낮아 평균오차 방어 축으로 쓸 근거가 있다.
- 후보 3은 PP계열 비교 후보였지만 후보 4보다 MAPE가 높아 최종 PP축으로 선택되지 않았다.

### 9.2 조합 탐색 방식

`후보1 또는 후보2`와 `후보3 또는 후보4`를 로그가격에서 0.05 단위로 섞어 검증한다.

```text
조합로그가격(weight)
  = weight * 유사작품계열_로그가격
  + (1 - weight) * PP계열_로그가격

weight 후보 = 0.00, 0.05, 0.10, ..., 1.00
```

Validation에서는 여러 목적 후보가 나왔지만, MAPE 방어 목적에서 선택된 후보가 test에서도 가장 균형이 좋았다.

### 9.3 최종 선택식

```text
최종_Warm_로그가격
  = 0.70 * 유사작품통계_Huber_seed평균_로그가격
  + 0.30 * PPV8_안정블렌드_로그가격
```

가격 변환은 아래처럼 한다.

```text
최종_Warm_KRW가격 = exp(최종_Warm_로그가격)
```

운영 재예측 스크립트에서는 표시 안전성을 위해 극단값을 아래 범위로 clip한 뒤 통화별 가격을 계산한다.

```text
표시용_KRW가격 = exp(clip(최종_Warm_로그가격, log(1,000), log(1,000,000,000,000)))
USD가격 = 표시용_KRW가격 / 1380
EUR가격 = 표시용_KRW가격 / 1530
GBP가격 = 표시용_KRW가격 / 1780
HKD가격 = 표시용_KRW가격 / 178
JPY가격 = 표시용_KRW가격 / 9.5
```

최종 선택 후보의 고정 test 성능은 `MdAPE 0.1405`, `MAPE 0.2748`, `p95_APE 0.8331`, `RMSE_log 0.3996`이다. 최종 70:30 후보는 네 단일 후보보다 test의 MdAPE, MAPE, p95를 모두 개선했다.

## 10. 운영 재예측에서의 artifact 상태

현재 Warm v0.1 정책은 고정되어 있지만, 모든 내부 후보가 단일 inference artifact로 완전히 저장되어 있지는 않다. 그래서 `OP-0605_v01_70_30_reprediction` 운영 재예측 스크립트는 다음 방식으로 재현했다.

```text
운영재예측_최종_Warm_로그가격
  = 0.70 * 운영재학습_유사작품통계_Huber_seed평균_로그가격
  + 0.30 * CatBoost로_증류한_PPV8_안정블렌드_로그가격
```

운영재예측에서 직접 재학습한 부분:

- `유사작품통계_Huber_seed평균_로그가격`: PP-SVC2 방식 그대로 seed 10개 Huber를 재학습한다.

운영재예측에서 증류한 부분:

- `PPV8_안정블렌드_로그가격`: 원천 후보 전체 chain이 단일 artifact로 없어서, 기존 PPV8 validation/test 예측값을 target으로 삼아 CatBoostRegressor가 그 값을 모사한다.
- 증류 모델 학습 row 수: validation 519건 + test 607건 = 1,126건
- 증류 모델 feature: 기본 Warm 피쳐, 생성 버킷, 작가 train 작품 수, 유사작품 숫자/범주 통계
- 증류 fidelity: test-from-validation 기준 `RMSE_log 0.3427`, `MdAE_log 0.1521`

따라서 정책 수식은 같지만, 신규 무가격 데이터에 대해 PPV8 30% 축은 원천 후보를 모두 다시 실행한 값이 아니라 증류 component라는 점을 명시해야 한다.

## 11. 재현 경로

| 목적 | 파일 |
|---|---|
| Warm v0.1 정책 | `models/track6/price_prediction_v0.1/config/model_policy_v0.1.json` |
| Warm 기본 Huber 피쳐와 train row manifest | `data/track6/artifacts/track6_artifact_manifest.json` |
| 유사작품 통계 계산과 Huber seed 반복 | `scripts/track6/run_pp_svc2_warm_comparable_stats_stability.py` |
| 유사작품 통계 feature set | `experiments/track6/PP-SVC2_warm_comparable_stats_stability/artifacts/feature_manifest.json` |
| 네 후보 결합과 최종 70:30 선택 | `scripts/track6/run_pp_svc3_warm_svc_blend_routing.py` |
| 최종 후보 성능 | `experiments/track6/PP-SVC3_warm_svc_blend_routing/outputs/selected_candidate_metrics.csv` |
| PPV6/PPV8 내부 블렌드 생성 | `scripts/track6/run_pp_v6_v8_warm_gap_experiments.py` |
| PPV6 가중치 | `experiments/track6/PP-V6_warm_l10_refreshed_fine_blend/outputs/policy_map.csv` |
| PPV8 가중치 | `experiments/track6/PP-V8_warm_deployment_simplification/outputs/policy_map.csv` |
| 운영 신규 데이터용 재예측 | `experiments/track6/OP-0605_v01_70_30_reprediction/scripts/02_predict_v01_70_30.py` |

## 12. 이 문서 기준 결론

Warm 기준 4개 예측 축은 모두 같은 로그가격 단위에서 움직인다. 최종 가격은 단순 평균이 아니라 validation에서 선택된 로그가격 가중 결합이다. 현재 고정 기준은 `유사작품통계 Huber seed 평균 70% + PPV8 compact 안정 블렌드 30%`이며, 이 조합이 단일 후보들보다 test에서 더 낮은 MAPE와 p95를 보였다.
