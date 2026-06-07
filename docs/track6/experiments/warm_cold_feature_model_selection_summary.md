# Warm/Cold 피처 및 모델 선정 정리

- 작성일: 2026-06-03
- 목적: Track6 가격 예측 실험에서 Warm과 Cold를 왜 분리했고, 각 그룹에서 어떤 피처와 모델을 기준으로 선정했는지 정리한다.
- 기준 문서:
  - `docs/track6/experiments/price_prediction_accuracy_experiment_result_report.md`
  - `docs/track6/experiments/track6_feature_influence_with_results.md`
  - `docs/track6/experiments/pp_v_execution_summary.md`
  - `docs/track6/experiments/pp_w_cold_artist_meta_execution_summary.md`
  - `docs/track6/experiments/pp_x_gallery_exhibition_revalidation_execution_summary.md`
  - `docs/track6/experiments/pp_y_cold_combination_execution_summary.md`
  - `docs/track6/experiments/pp_y_cold_closure_execution_summary.md`
  - `docs/track6/experiments/pp_y15_oof_fixed_revalidation_summary.md`
  - `docs/track6/experiments/pp_l10_warm_l8_feature_variant_execution_summary.md`
  - `docs/track6/experiments/pp_z_warm_coldstyle_extension_execution_summary.md`

## 1. 먼저 구분해야 하는 것

이 프로젝트에서 `모델 선정`은 두 층으로 나눠서 봐야 한다.

| 구분 | 의미 | 예시 |
|---|---|---|
| 후처리 전 기준 모델 | 기본 예측값 `pred_log`를 만드는 출발 모델 | Warm `Huber`, Cold `CatBoost`, Cold `LightGBM Quantile` |
| 후처리 포함 운영 후보 | 기준 모델 예측값에 조합, 보정, 라우팅, meta를 붙인 최종 후보 | Warm `PP-V1/PP-V2`, Cold `PP-Y2/PP-Y16` |

따라서 “Warm은 Huber를 쓴다”는 말은 Huber만 단독으로 최종 서비스한다는 뜻이 아니다.

- Warm은 Huber가 작가+크기 중심 가격선을 안정적으로 만들기 때문에 출발 모델로 적합하다.
- 최종 운영 후보는 Huber 중심선 위에 Quantile, CatBoost residual, fine blend, meta stacking을 더한 구조다.
- Cold는 작가 기준선이 약하므로 CatBoost/LightGBM/Quantile/Huber residual을 목적별로 나눠 쓴다.

## 2. Warm과 Cold를 분리한 이유

| 구분 | 데이터 상황 | 모델링 방향 |
|---|---|---|
| Warm | 같은 작가의 학습 이력이 있음 | `artist_key`로 작가 기준 가격선을 잡고, 크기와 작품 조건으로 조정 |
| Cold | 같은 작가 이력이 없거나 약함 | 작품 크기, 재료, 지지체, 형태, 작가 메타, 외부 정보로 가격대를 추정 |

Warm은 작가 기준선이 강하다. 그래서 선형 모델인 Huber가 가격 중심선을 안정적으로 잡을 수 있다.

Cold는 작가 기준선이 약하다. 같은 크기와 재료라도 작가의 시장 지위 차이로 가격 차이가 크게 날 수 있으므로, 단일 모델 하나로 끝내기 어렵다.

## 3. Warm 피처 선정

### 3.1 기준 피처셋

Warm의 기준 피처셋은 `base_existing_combo`다.

| 피처 그룹 | 실제 피처 | 역할 |
|---|---|---|
| 작가 기준선 | `artist_key` | 같은 작가의 과거 가격대를 반영 |
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area` | 작품 규모에 따른 가격 차이 반영 |
| 깊이/입체 | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체 또는 깊이 있는 작품 보정 |
| 형태 | `aspect_ratio`, `is_extreme_aspect_ratio` | 극단적 비율 보정 |
| 재료/지지체 | `medium_category`, `support_category`, `medium_support_bucket` | 재료와 바탕에 따른 보조 설명 |

### 3.2 피처 선정 근거

| 피처 축 | 실험 근거 | 판단 |
|---|---|---|
| 작가 정보 | `PRE-WARM-07`에서 작가 정보 제거 시 MdAPE가 약 `0.48~0.49`로 악화 | 필수 |
| 크기 정보 | 크기 제거 시 MdAPE가 약 `0.55~0.56`, p95가 약 `5.2~5.4`로 악화 | 필수 |
| 재료/지지체 | 제거해도 성능이 유지되거나 소폭 개선되는 후보 존재 | 핵심축보다는 보조 피처 |
| depth/aspect | 제거 영향이 작거나 후보별 방향이 다름 | 단독 핵심 피처는 아님 |
| 생성 bucket | `PP-U1 full_plus_generated_buckets` test MdAPE `0.2131`로 개선 신호 | 후속 조합 후보이나 즉시 교체는 보류 |

Warm 피처 선정의 핵심은 `artist_key + size`다.

나머지 피처는 모두 중요도가 같지 않다. 재료/지지체, depth, aspect는 설명 보조 또는 후처리 segment 후보로 보는 것이 맞다.

## 4. Warm 모델 선정

### 4.1 Huber를 기준 모델로 둔 이유

Huber는 선형 모델이지만 이상치에 둔감한 손실을 쓴다.

```text
pred_log_price = intercept + Σ(coefficient_j * transformed_feature_j)
pred_price = exp(pred_log_price)
```

Warm에서는 `artist_key`가 작가 기준 가격선을 제공한다. 여기에 크기 계열 피처가 붙으면 선형 구조만으로도 상당히 안정적인 중심 예측이 가능하다.

Huber를 Warm 기준 모델로 유지한 이유는 다음이다.

- 작가별 가격 기준선을 직접 설명할 수 있다.
- 크기 효과를 계수와 기여도로 해석할 수 있다.
- 고가/저가 이상치에 일반 선형 회귀보다 덜 흔들린다.
- CatBoost 단독보다 Warm 주모델로 안정적이었다.

### 4.2 Warm 최종 후보

| 목적 | 후보 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| 대표 점 예측 | `PP-V1 / PP-T1 fine_blend_mape_guarded` | 0.1621 | 0.3044 | 1.0335 | 대표 가격 후보 |
| 큰 오차 방어/평균 오차 | `PP-V2 huber_component_range_clipped` | 0.1680 | 0.2873 | 0.9287 | MAPE/p95 방어 후보 |
| p95 균형 | `PP-V1 fine_blend_mdape` | 0.1668 | 0.3067 | 0.9580 | 대표와 p95 균형 후보 |
| 기준 모델 | Warm Huber baseline | 0.2274 | 0.4952 | 2.0130 | 후처리 전 기준선 |

Warm 결론은 다음이다.

- 기준 모델은 Huber가 맞다.
- 최종 서비스 후보는 Huber 단독이 아니라 Huber 중심선 기반 조합 모델이다.
- Warm은 단일 가격으로 서비스할 수 있는 수준까지 개선됐다.
- 다만 대표 가격 후보와 p95 방어 후보는 분리해서 관리하는 것이 좋다.

### 4.3 PP-L8 순차 구조의 피처 변형 확인

기존 `PP-L8`은 `Quantile -> Huber -> CatBoost residual` 순차 구조였다.

이번에 `PP-L10`으로 같은 구조를 유지한 채 Warm 피처셋만 바꿔 재실행했다.

| 후보 | 구조 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| `PP-L10 l8_seq__warm_base_meta_external_search_all` | Quantile -> Huber -> CatBoost | 0.1708 | 0.3363 | 1.1432 | PP-L10 내부 MdAPE 최상 |
| `PP-L10 l8_seq__full_plus_generated_buckets` | Quantile -> Huber -> CatBoost | 0.1743 | 0.3265 | 0.9818 | MAPE/p95 균형 최상 |
| `PP-L10 l8_seq__base_existing_combo` | Quantile -> Huber -> CatBoost | 0.1742 | 0.3386 | 1.0888 | 기존 PP-L8 구조 재현 후보 |
| `PP-V1 / PP-T1 fine_blend_mape_guarded` | Warm 최종 조합 | 0.1621 | 0.3044 | 1.0335 | 대표 후보 유지 |
| `PP-V2 huber_component_range_clipped` | Warm p95/MAPE 방어 | 0.1680 | 0.2873 | 0.9287 | 방어 후보 유지 |

해석은 다음이다.

- PP-L8 구조는 피처셋을 바꾸면 성능 차이가 분명히 난다.
- 외부 피처 전체를 넣은 후보는 MdAPE를 가장 낮췄고, 생성 bucket 후보는 MAPE/p95 균형이 가장 좋았다.
- 그러나 기존 Warm 최종 후보 `PP-V1/PP-V2`를 넘지는 못했다.
- 따라서 PP-L10은 최종 후보 교체가 아니라, Warm 조합 후보의 추가 component 또는 후속 블렌딩 후보로 보는 것이 적절하다.

### 4.4 Cold식 확장 피처를 Warm에 적용한 추가 확인

Cold에서는 작가 메타, 전시/갤러리, 검색 피처와 LightGBM Quantile/CatBoost 조합이 성능 개선에 도움이 됐다.

그래서 Warm에도 같은 축을 직접 적용하는 `PP-Z1~PP-Z4`를 추가 실행했다.

| 실험 | 방식 | Test MdAPE | Test MAPE | Test p95_APE | 판단 |
|---|---|---:|---:|---:|---|
| `PP-Z1 warm_base_search_all` | Warm Huber + 검색 전체 피처 | 0.2195 | 0.4854 | 1.8119 | Huber baseline보다 개선, 최종 후보보다 약함 |
| `PP-Z1 warm_base_artist_volume` | Warm Huber + 작가 학습량 | 0.2214 | 0.4813 | 1.9083 | 약한 개선 신호 |
| `PP-Z3 warm_base_artist_meta_all` | Warm CatBoost + 작가 메타 전체 | 0.3186 | 0.4663 | 1.3889 | MAPE/p95는 일부 개선이나 MdAPE 악화 큼 |
| `PP-Z4 pred_x_qwidth_min30_cap0.25` | Warm LightGBM Quantile + q-width 보정 | 0.3171 | 0.5553 | 1.7701 | 최종 후보 대체 불가 |

해석은 다음이다.

- Warm에서는 `artist_key`가 이미 작가 기준 가격선을 강하게 설명한다.
- Cold에서 유효했던 작가 메타/전시/검색 피처는 Warm에서 `artist_key`와 정보가 겹치는 부분이 크다.
- 따라서 확장 피처를 넣으면 Huber baseline 대비 소폭 개선은 가능하지만, `PP-V1/PP-V2`의 조합/보정 후보를 넘지는 못했다.
- Warm 최종 후보는 기존 `PP-V1/PP-V2`를 유지한다.

## 5. Cold 피처 선정

### 5.1 기본 피처 축

Cold는 작가 기준 가격선이 약하므로 작품 자체 조건과 외부 보조 정보를 최대한 활용해야 한다.

| 피처 축 | 주요 피처 | 역할 |
|---|---|---|
| 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `size_bucket` | 가격대의 기본 규모 추정 |
| 깊이/3D | `depth_cm`, `has_depth`, `is_3d_candidate` | 입체/대형/깊이 조건 분리 |
| 재료/형태 | `medium_category`, `shape_bucket`, `medium_shape_bucket` | CatBoost가 조건 조합을 나누는 핵심 |
| 지지체/크기 | `support_category`, `support_size_bucket` | LightGBM이 세밀한 구간을 나누는 기준 |
| 작가 메타 | 작품 수, 판매 작품 수, 팔로워, 출생연도, 국적, source 등 | Cold에서 부족한 작가 기준선을 보완 |
| 전시/갤러리 | 개인전/단체전/아트페어 수, 갤러리 tier, 정보 가용 flag | 작가 활동성과 시장 노출 보조 |
| 검색 피처 | 검색 품질, 검색 결과 수, 문맥 count, source count | 인지도와 불확실성 보조 |
| 품질/가용성 flag | 검색 품질, 갤러리/전시 정보 존재 여부, quantile width | 모델 선택/위험 구간 라우팅 기준 |

### 5.2 피처 선정 근거

| 피처 축 | 실험 근거 | 판단 |
|---|---|---|
| 크기/depth/3D | `PRE-PP-CB`, `PRE-PP-LGB`에서 제거 시 성능 악화 | Cold 필수 축 |
| `medium_shape_bucket` | Cold CatBoost 기준 피처셋, `PP-U4`에서도 CatBoost 기준 피처 유지 | CatBoost에 적합 |
| `support_size_bucket` | LightGBM 기준 피처셋, PRE-CAL-LGB에서 보정 여지 확인 | LightGBM에 적합 |
| 작가 메타 | `PP-W2 generated_all_meta_all` test MdAPE `0.4497` | Cold 대표 정확도 개선 |
| 전시/갤러리 | `PP-X3 LightGBM Quantile + 전시/갤러리` test MdAPE `0.4451` | 대표 정확도 개선, p95 악화 주의 |
| 검색+전시/갤러리 | `PP-Y2` test MdAPE `0.4421`, MAPE `1.0484` | 최신 단일 모델 후보 |
| quantile width/segment | `PP-Y16` OOF 고정 선택 후보 test p95 `2.8025` | 큰 오차 방어용 정책 후보 |

Cold는 특정 피처 하나가 가격을 결정한다고 설명하기 어렵다.

크기, 깊이, 재료, 지지체, 작가 메타, 외부 정보가 함께 조건 구간을 만들고, 그 구간별로 오차가 달라진다.

## 6. Cold 모델 선정

### 6.1 모델별 역할

| 모델 | 구조적 특성 | 이번 실험에서 맡은 역할 |
|---|---|---|
| CatBoost | 대칭 트리, 범주형/조합 피처 처리 강점 | 재료/형태/작가 메타 조합을 나눔 |
| CatBoost Quantile | 분위 손실 기반 CatBoost | 평균 오차와 tail 위험 완화 |
| LightGBM | leaf-wise 트리 | 크기/지지체/외부 피처 구간을 세밀하게 분리 |
| LightGBM Quantile | 분위 예측 + q10/q50/q90 생성 | 중앙 예측과 불확실성 폭 산출 |
| Huber residual | 이상치에 둔감한 잔차 보정 | 큰 residual을 과도하게 따라가지 않고 제한 보정 |

### 6.2 Cold 주요 모델 흐름

| 단계 | 후보 | Test MdAPE | Test MAPE | Test p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| 기존 기준 | Cold LightGBM baseline | 0.4909 | 1.4131 | 4.8212 | 초기 기준선 |
| 기존 기준 비교 | Cold CatBoost baseline | 0.4867 | 1.4803 | 4.6329 | CatBoost 단독은 충분하지 않음 |
| 작가 메타 추가 | `PP-W2 generated_all_meta_all` | 0.4497 | 1.1111 | 4.1587 | 대표 정확도 개선, p95 악화 |
| 전시/갤러리 추가 | `PP-X3 LightGBM Quantile + 전시/갤러리` | 0.4451 | 1.1277 | 3.8935 | MdAPE 개선, tail 악화 |
| 검색+전시/갤러리 | `PP-Y2 lgbq_search_all_external_interaction` | 0.4421 | 1.0484 | 3.3537 | 최신 단일 모델 대표 후보 |
| OOF 고정 보정 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | 대표 정확도는 유지, 큰 오차 방어 강함 |
| 탐색상 최고 | `PP-Y15/PP-Y16` 일부 segment/cap 후보 | 약 0.424~0.425 | 약 0.99~1.07 | 약 3.30~3.41 | test 탐색상 좋지만 OOF 선택 기준으로 바로 채택 보류 |

### 6.3 Cold 최종 판단

Cold는 Warm처럼 “하나의 최종 모델”로 끝내기 어렵다.

| 목적 | 현재 권장 후보 | 이유 |
|---|---|---|
| 대표 점 예측 | `PP-Y2 lgbq_search_all_external_interaction` | 단일 모델 기준 MdAPE `0.4421`, MAPE `1.0484`로 균형 좋음 |
| 큰 오차 방어 | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | p95를 `3.3537`에서 `2.8025`로 낮춤 |
| 보수적 평균오차/범위 후보 | `PP-W4 lightgbm_quantile_meta_all_huber_cap0.5_s1` | MAPE `0.9584`, p95 `3.0073`, 단 MdAPE `0.4949` |
| 탐색 재검증 후보 | `PP-Y15/PP-Y16` test MdAPE 상위 segment/cap 후보 | 다른 split 또는 OOF 선택 기준에서 재현 확인 필요 |

Cold 모델 선정의 핵심은 다음이다.

- CatBoost 단독 RMSE 모델만으로는 부족했다.
- CatBoost는 범주형/조합 피처 해석과 작가 메타 결합에서 의미가 있었다.
- LightGBM Quantile은 전시/갤러리/검색 피처를 활용해 대표 정확도를 크게 개선했다.
- Huber residual과 segment/cap 보정은 대표 정확도보다 큰 오차 방어에 더 적합했다.
- 서비스에서는 Cold를 단일 가격 확정값이 아니라, 대표 가격 + 범위 + 신뢰도/위험 표시로 제공하는 것이 안전하다.

## 7. Warm/Cold 선정 결과 요약

| 구분 | 기준 피처 | 기준 모델 | 후처리 포함 대표 후보 | 큰 오차 방어 후보 | 운영 판단 |
|---|---|---|---|---|---|
| Warm | `artist_key + size + base_existing_combo` | Huber | `PP-V1/PP-T1 fine_blend_mape_guarded` | `PP-V2 huber_component_range_clipped` | 단일 가격 제공 가능, 목적별 후보 분리 |
| Cold | 작품 구조 + 작가 메타 + 검색/전시/갤러리 | LightGBM Quantile / CatBoost 보조 | `PP-Y2 lgbq_search_all_external_interaction` | `PP-Y16 pred_x_qwidth_oof_min30_cap0.35` | 단일 가격만 제공하기보다 범위/신뢰도 병행 |

## 8. 모델 상세 설명

### 8.1 Warm Huber

Warm Huber는 같은 작가의 과거 거래 이력이 있는 작품을 대상으로 한다.

핵심 아이디어는 단순하다.

```text
작가 기준 가격선 + 작품 크기 효과 + 작품 조건 보정 = 예측 로그가격
```

모델이 계산하는 값은 원가격이 아니라 로그 가격이다.

```text
pred_log_price = intercept
               + artist_effect
               + size_effect
               + depth_effect
               + shape_effect
               + medium_support_effect

pred_price = exp(pred_log_price)
```

Huber가 일반 선형 회귀와 다른 점은 손실 함수다.

```text
residual = actual_log_price - pred_log_price

if abs(residual) <= delta:
    loss = 0.5 * residual^2
else:
    loss = delta * (abs(residual) - 0.5 * delta)
```

쉽게 말하면 작은 오차는 일반 회귀처럼 세밀하게 줄이고, 너무 큰 오차는 과하게 따라가지 않는다.

이 특성 때문에 Warm에 잘 맞는다.

| 항목 | 설명 |
|---|---|
| 작가 기준선 | `artist_key`가 작가별 평균 가격대를 잡는다. |
| 크기 효과 | 같은 작가 안에서도 큰 작품이 더 비싼 경향을 반영한다. |
| 이상치 방어 | 특이하게 비싼 작품이나 낮은 낙찰가에 모델이 과하게 끌려가지 않는다. |
| 해석 가능성 | 계수와 기여도를 통해 어떤 피처가 가격을 올리거나 내렸는지 설명할 수 있다. |

Warm에서 Huber를 기준 모델로 둔 이유는 성능만이 아니다.

- 작가 기준 가격선을 설명할 수 있다.
- 크기 증가가 가격에 주는 방향을 해석할 수 있다.
- 후처리에서 남은 오차를 계산하기 쉽다.
- 서비스 설명 문구로 연결하기 쉽다.

### 8.2 Warm CatBoost

Warm CatBoost는 보조 후보로 검토했다.

CatBoost는 대칭 트리 구조를 사용한다. 한 단계의 split 조건이 같은 깊이의 모든 노드에 동일하게 적용되는 구조다.

```text
depth 1: 모든 샘플을 같은 피처 조건으로 1차 분리
depth 2: 각 가지에서 다시 같은 피처 조건으로 2차 분리
depth 3: 같은 방식으로 반복
```

Warm에서 CatBoost가 기대됐던 이유는 다음이다.

| 기대 | 의미 |
|---|---|
| 작가 x 크기 조합 | 특정 작가는 작은 작품과 큰 작품의 가격 차이가 다를 수 있다. |
| 작가 x 재료 조합 | 같은 작가라도 회화/드로잉/입체에서 가격 패턴이 다를 수 있다. |
| 구간형 분기 | 선형 Huber가 놓치는 특정 크기 구간의 가격 차이를 나눌 수 있다. |

하지만 실험 결과 Warm 주모델로는 Huber보다 약했다.

이유는 다음과 같이 해석한다.

- Warm에서는 `artist_key` 자체가 이미 매우 강한 기준선이다.
- Huber는 작가 기준선을 직접 계수로 잡기 때문에 안정적이다.
- CatBoost는 조합을 잘 나누지만, Warm에서는 조합 분기가 작가 기준선보다 더 안정적인 개선으로 이어지지 않았다.
- 따라서 Warm CatBoost는 주모델보다 Huber가 남긴 잔차를 보조적으로 설명하는 역할이 더 적합하다.

### 8.3 Cold CatBoost

Cold CatBoost는 작가 이력이 부족한 상황에서 작품 조건 조합을 보기 위해 사용했다.

Cold에서는 `artist_key`가 강한 기준선 역할을 하지 못한다. 그래서 모델은 작품 자체의 조건을 더 많이 본다.

CatBoost가 Cold에서 보는 대표 조합은 다음과 같다.

```text
크기 + 재료 + 형태
크기 + 깊이/3D 여부
재료 + 지지체
작가 메타 + 작품 조건
갤러리/전시 정보 + 작품 조건
```

CatBoost에 적합한 피처는 단독 숫자보다 범주형/구간형 조합이다.

| 피처 | CatBoost에서 의미 있는 이유 |
|---|---|
| `medium_category` | 회화, 드로잉, 판화, 입체 등 매체 차이를 조건으로 나눌 수 있다. |
| `shape_bucket` | 세로형/가로형/정방형 등 형태 차이를 나눌 수 있다. |
| `medium_shape_bucket` | 재료와 형태의 조합을 한 번에 반영한다. |
| `has_depth`, `is_3d_candidate` | 평면과 입체 후보를 다른 가격 구간으로 볼 수 있다. |
| 작가 메타 범주 | 국적, source, career stage 같은 범주형 정보를 조건 조합으로 쓸 수 있다. |

다만 RMSE CatBoost 단독은 최종 후보로 충분하지 않았다.

| 이유 | 설명 |
|---|---|
| 작가 기준선 부족 | 작품 조건이 비슷해도 작가 시장 가격 차이를 충분히 설명하기 어렵다. |
| 평균 중심 학습 | RMSE 목적은 큰 가격 오차에 민감하지만, MAPE나 MdAPE를 직접 최적화하지 않는다. |
| tail 위험 | 일부 조건 조합에서 큰 오차가 남는다. |

그래서 Cold에서는 CatBoost를 단독 최종 모델로 쓰기보다, Quantile 또는 residual 보조 모델로 쓰는 방향이 더 적합했다.

### 8.4 Cold LightGBM Quantile

LightGBM은 leaf-wise 트리 구조다.

쉽게 말하면 성능 개선 여지가 큰 가지를 더 깊게 파고드는 방식이다.

```text
일반적인 균형 트리:
    모든 가지를 비슷한 깊이로 확장

LightGBM leaf-wise:
    오차를 가장 많이 줄일 수 있는 leaf를 우선 확장
```

이 구조는 Cold에서 장점이 있었다.

| 장점 | 설명 |
|---|---|
| 세밀한 구간 분리 | 크기, 지지체, 전시/갤러리, 검색 피처를 세밀하게 나눌 수 있다. |
| Quantile 예측 | q10/q50/q90을 만들어 중앙 예측과 불확실성 폭을 함께 볼 수 있다. |
| 외부 피처 활용 | 전시/갤러리/검색 피처가 들어왔을 때 MdAPE 개선이 컸다. |

LightGBM Quantile의 예측 구조는 다음과 같이 이해하면 된다.

```text
q50_log = 중앙 가격 예측
q10_log = 낮은 분위 예측
q90_log = 높은 분위 예측

quantile_width = q90_log - q10_log
price_range_ratio = exp(q90_log) / exp(q10_log)
```

`quantile_width`가 크다는 것은 모델이 해당 작품의 가격 범위를 넓게 보고 있다는 뜻이다.

이 값은 단순한 성능 지표가 아니라, Cold에서 위험 구간을 나누는 피처로도 썼다.

### 8.5 Huber Residual / Segment-Cap 보정

Huber residual과 segment/cap 보정은 새로운 1차 모델이 아니라, 이미 만들어진 예측값을 안정화하는 후처리다.

기본 구조는 다음과 같다.

```text
residual_log = actual_log - pred_log
segment_correction = median(residual_log in same segment)
corrected_pred_log = pred_log + clipped(segment_correction)
```

여기서 segment는 예측 가격대, quantile width, 외부 피처 가용성 같은 운영 시점에 알 수 있는 정보로 만든다.

| 구성 | 의미 |
|---|---|
| residual 중앙값 | 해당 구간에서 반복적으로 높게/낮게 예측하는 방향 |
| cap | 보정값이 너무 커지는 것을 막는 제한값 |
| fallback | 표본 수가 부족한 segment는 더 넓은 segment 또는 전체 보정으로 대체 |
| OOF 검증 | 보정 기준이 test에 맞춰지는 것을 막기 위한 내부 교차 검증 |

`PP-Y16`에서 확인한 핵심은 다음이다.

- test 탐색상 최고 MdAPE 후보는 있었지만 OOF 선택 기준으로 바로 채택하기는 어렵다.
- OOF 기준으로 선택하면 대표 정확도 개선은 크지 않다.
- 대신 p95 큰 오차 방어는 뚜렷하게 좋아진다.

따라서 segment/cap 보정은 Cold 대표 가격 모델이 아니라, 위험 구간 방어 정책으로 보는 것이 맞다.

## 9. 피처 상세 설명

### 9.1 Warm 피처 상세

| 피처 | 그룹 | 모델에서의 의미 | 해석 |
|---|---|---|---|
| `artist_key` | 작가 기준선 | 작가별 기본 가격대를 계수로 학습 | Warm에서 가장 중요한 피처 |
| `width_cm`, `height_cm` | 크기 | 작품의 가로/세로 크기 | 크기가 클수록 가격대가 달라지는 기본 신호 |
| `area_cm2` | 크기 | 면적 원값 | 실제 크기 차이를 직접 반영 |
| `log_area` | 크기 | 면적 로그값 | 큰 작품의 과도한 영향 완화 |
| `depth_cm` | 깊이 | 깊이 수치 | 입체/오브제 후보 보조 |
| `has_depth` | 깊이 | 깊이 정보 존재 여부 | 깊이 값의 결측/존재 자체가 정보가 될 수 있음 |
| `is_3d_candidate` | 깊이/입체 | 입체 후보 flag | 평면과 입체를 구분하는 보조 신호 |
| `aspect_ratio` | 형태 | 가로세로 비율 | 극단적인 형태의 가격 차이 보조 |
| `is_extreme_aspect_ratio` | 형태 | 극단 비율 여부 | 비정상적 비율의 tail 위험 보조 |
| `medium_category` | 재료 | 작품 매체 | Warm에서는 핵심보다 보조 |
| `support_category` | 지지체 | 캔버스/종이 등 바탕 | Warm에서는 보조 |
| `medium_support_bucket` | 재료+지지체 | 매체와 바탕 조합 | 일부 조건 조합 보조 |

Warm에서 우선순위는 명확하다.

```text
1순위: artist_key
2순위: width/height/area/log_area
3순위: depth/aspect/medium/support 보조 피처
```

### 9.2 Cold CatBoost 피처 상세

Cold CatBoost의 기준 피처셋은 `base_medium_shape` 계열이다.

| 피처 | 그룹 | CatBoost에서의 의미 | 해석 |
|---|---|---|---|
| `width_cm`, `height_cm`, `area_cm2`, `log_area` | 크기 | 가격대 기본 분기 | 작가 기준선이 없으므로 핵심 |
| `depth_cm`, `has_depth`, `is_3d_candidate` | 깊이/3D | 평면/입체 조건 분기 | 3D 후보의 가격 구간을 나눔 |
| `aspect_ratio` | 형태 | 형태 조건 분기 | 형태가 다른 작품군 구분 |
| `medium_category` | 재료 | 매체 조건 | CatBoost 범주형 처리에 적합 |
| `support_category` | 지지체 | 바탕 조건 | 재료와 함께 가격 구간을 나눔 |
| `shape_bucket` | 형태 bucket | 형태를 구간화 | 대칭 트리 split에 적합 |
| `medium_shape_bucket` | 재료+형태 조합 | 매체와 형태를 함께 분기 | Cold CatBoost 핵심 조합 피처 |

CatBoost는 “피처 하나가 가격을 얼마 올린다”보다 “이 조건 조합에 속하면 다른 가격 구간으로 간다”에 가깝다.

예를 들면 다음과 같다.

```text
medium_shape_bucket = painting_vertical
log_area = large
is_3d_candidate = false
```

이런 조합이 하나의 가격 판단 구간을 만들고, 그 구간별 평균적 예측값이 달라진다.

### 9.3 Cold LightGBM / LightGBM Quantile 피처 상세

LightGBM 기준 피처셋은 `base_support_size` 계열이고, 최신 후보에서는 작가 메타, 전시/갤러리, 검색 피처가 추가됐다.

| 피처 | 그룹 | LightGBM에서의 의미 | 해석 |
|---|---|---|---|
| `size_bucket` | 크기 bucket | 크기별 leaf 분리 | 단순 수치보다 구간 분리에 적합 |
| `support_size_bucket` | 지지체+크기 | 지지체와 크기 조합 | LightGBM 기준 피처로 중요 |
| `artist_meta_total_works` | 작가 메타 | 작가 활동량 | Cold의 작가 기준선 부족 보완 |
| `artist_meta_for_sale_works` | 작가 메타 | 시장 노출 작품 수 | 판매 시장 활동성 보조 |
| `artist_meta_followers` | 작가 메타 | 인지도 proxy | 단독보다 다른 피처와 함께 의미 |
| `artist_meta_birth_year` | 작가 메타 | 세대/경력 proxy | career stage와 함께 사용 |
| `artist_meta_nationality` | 작가 메타 | 시장권/국적 정보 | 범주형 보조 |
| 전시 count | 전시/활동 | 개인전/단체전/아트페어 활동량 | LightGBM Quantile에서 MdAPE 개선 |
| 갤러리 tier | 갤러리 | 갤러리 신뢰도/시장 노출 | coverage와 품질 주의 |
| 검색 품질 | 검색 | 검색 결과의 신뢰도 | 위험 구간/fallback 기준 |
| 검색 결과 수 | 검색 | 인지도 proxy | tail 방어와 MAPE 개선 보조 |
| `quantile_width_log` | 불확실성 | q90-q10 폭 | 모델이 불확실하게 보는 구간 표시 |
| `price_range_ratio` | 불확실성 | 예측 가격 범위 비율 | 서비스 범위/신뢰도 표시 후보 |

LightGBM Quantile이 Cold에서 강했던 이유는 외부 피처를 넣었을 때 가격 중앙값을 더 잘 잡았기 때문이다.

하지만 leaf-wise 구조는 특정 leaf가 과하게 세분화되면 p95가 악화될 수 있다.

그래서 LightGBM Quantile은 다음처럼 써야 한다.

```text
대표 점 예측: q50_log
위험도 판단: q90_log - q10_log
범위 표시: exp(q10_log) ~ exp(q90_log)
후처리 기준: quantile_width, price_range_ratio, pred_bin
```

### 9.4 외부 피처 사용 시 주의점

외부 피처는 Cold 개선에 도움이 됐지만, 운영 리스크도 있다.

| 피처군 | 장점 | 주의점 |
|---|---|---|
| 작가 메타 | Cold 대표 정확도 개선 | 서비스에서 항상 수집 가능한지 확인 필요 |
| 전시 활동 | LightGBM Quantile MdAPE 개선 | CatBoost에서는 전시 결합 시 악화되는 경우 있음 |
| 갤러리 tier | CatBoost에서 소폭 개선 | 검증 tier coverage가 낮음 |
| 검색 피처 | MAPE/p95 보조 | 동명이인, 검색 품질 오염 관리 필요 |
| quantile width | 위험 구간 판단 가능 | 직접 가격을 맞추는 피처가 아니라 신뢰도/라우팅 피처 |

## 10. 모델과 피처 연결 요약

| 모델 | 잘 맞는 피처 | 잘 맞는 이유 | 이번 실험의 결론 |
|---|---|---|---|
| Warm Huber | `artist_key`, 크기 피처, 제한적 검색 피처 | 작가 기준선과 크기 효과를 선형적으로 설명 가능 | Warm 기준 모델로 유지. `PP-Z1`에서 검색 전체 피처는 baseline 대비 개선했지만 최종 후보는 대체 못함 |
| Warm CatBoost | 작가 x 크기 x 재료 조합, 작가 메타 | 조건 조합 분기가 가능 | `PP-Z3`에서도 MdAPE가 크게 악화되어 단독 주모델은 보류, residual/보조 후보 |
| Cold CatBoost | `medium_shape_bucket`, 범주형 작가 메타 | 대칭 트리가 범주형 조합을 안정적으로 분기 | 작가 메타 결합에서 의미 있음 |
| Cold LightGBM | `support_size_bucket`, 크기/지지체 구간 | leaf-wise 구조가 세밀한 구간 분리 | 기준선/비교 모델로 유효 |
| Cold LightGBM Quantile | 작가 메타, 전시/갤러리, 검색, q-width | 중앙 예측과 불확실성 폭을 함께 산출 | 최신 Cold 대표 후보의 핵심 |
| Huber residual | 1차 예측값, residual, segment | 큰 residual을 과하게 따라가지 않음 | p95 방어와 안정화에 적합 |

## 11. 상사 보고용 핵심 문장

- Warm은 작가 이력이 있기 때문에 `artist_key`와 작품 크기만으로도 가격 중심선이 안정적으로 형성된다.
- 따라서 Warm의 기준 모델은 해석 가능하고 이상치에 강한 Huber가 적합하다.
- Warm 최종 성능 개선은 Huber를 버린 것이 아니라, Huber 중심선 위에 Quantile, CatBoost residual, fine blend/meta를 얹어서 만든 결과다.
- Cold는 작가 기준선이 없기 때문에 작품 조건만으로는 가격 설명이 부족하다.
- Cold에서는 작가 메타, 전시/갤러리, 검색 피처를 추가하면서 LightGBM Quantile의 대표 정확도 개선 효과가 가장 뚜렷했다.
- 다만 Cold는 p95 큰 오차 위험이 계속 남기 때문에, 대표 점 예측 모델과 큰 오차 방어 정책을 분리해야 한다.
- 현재 Warm은 서비스 단일 가격 후보로 사용할 수 있는 수준이고, Cold는 대표 가격과 범위/신뢰도를 함께 제공하는 정책형 모델로 접근하는 것이 맞다.

## 12. 남은 확인 사항

| 항목 | 이유 |
|---|---|
| Cold `PP-Y2` 후보의 다른 split 재현성 | 최신 단일 모델 대표 후보이므로 split 안정성 확인 필요 |
| `PP-Y16` p95 방어 정책의 서비스 적용 기준 | MdAPE는 소폭 악화될 수 있어 위험 구간에만 쓸지 결정 필요 |
| Cold 외부 피처 운영 가능성 | 검색/전시/갤러리/작가 메타를 서비스 API에서 안정적으로 생성해야 함 |
| Warm `PP-V2` 후보의 운영 복잡도 | p95/MAPE는 좋지만 meta 구조이므로 배포 난이도 확인 필요 |
