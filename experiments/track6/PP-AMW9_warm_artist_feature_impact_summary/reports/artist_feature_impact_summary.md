# Warm 작가 관련 피처/처리별 영향도 종합

- 작성일: 2026-06-08
- 기준 모델: `blend_svcnum_ppv8_wsvc_0.70`
- 목적: 지금까지의 Warm 가격예측 보정 실험에서 작가 관련 피처와 처리 방식이 성능에 준 영향을 한 문서로 정리한다.
- 해석 기준: 여기서 말하는 영향도는 모델 내부의 일반적인 feature importance가 아니라, 기준 예측값에 잔차 보정을 적용했을 때 `MdAPE`, `MAPE`, `p95_APE`가 얼마나 개선되거나 악화됐는지를 뜻한다.

## 1. 기준 성능과 판단 기준

기준 모델 성능은 다음과 같다.

| split | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| validation | 0.3292 | 0.1305 | 0.2110 | 0.6580 | 0.7746 | 0.9075 |
| test | 0.3996 | 0.1405 | 0.2748 | 0.8331 | 0.7628 | 0.8781 |

개선 판단은 다음 순서로 본다.

1. validation OOF에서 개선되는가
2. 고정 test에서도 같은 방향으로 개선되는가
3. row bootstrap과 artist bootstrap에서 개선 확률이 충분한가
4. 평균 보정폭이 과하지 않은가
5. 피처 커버리지와 신규 데이터 재현 가능성이 충분한가

델타값은 기준 모델 대비 변화량이다. 음수는 개선, 양수는 악화다.

## 2. 피처별 영향도 요약

| 피처 그룹 | 대표 피처 | 관찰된 영향 | 판단 |
| --- | --- | --- | --- |
| 작가 세대 | `artist_birth_generation_bin` | validation과 test에서 p95_APE 방어가 반복적으로 확인됨. MAPE 개선 폭은 작지만 bootstrap 안정성이 좋음. | 가장 안정적인 보정축 |
| 작가 생년 | `artist_meta_birth_year` | validation 개선 폭이 크고, cap을 낮추면 test에서도 MdAPE/p95 개선. cap이 커지면 test MAPE 악화 가능. | 유효하지만 보정폭 제한 필요 |
| 작가 커리어 단계 | `artist_meta_career_stage` | 단일 피처 test에서 MdAPE/MAPE/p95를 모두 개선한 거의 유일한 축. 다만 validation MAPE는 강하지 않음. | 보조 후보로 유효 |
| 전시 횟수 | `artist_exhibition_solo_count`, `artist_exhibition_total_count_log` | validation에서는 일부 개선되지만 test에서는 지표가 엇갈림. 전시/갤러리 조합 Huber는 test에서 악화. | 현재는 진단용 |
| 시장 깊이/거래성 | `artist_meta_for_sale_works_log1p`, `artist_meta_followers_log1p` | p95_APE를 줄이는 신호는 있으나 MdAPE/MAPE가 흔들림. | 큰 오차 방어 후보이나 단독 채택 보류 |
| 갤러리 관련 | `gallery_tier_*`, `gallery_city_count`, `gallery_feature_source` | 커버리지 또는 값 다양성이 부족하고 test 재현성이 약함. | 현 데이터에서는 약함 |
| 작가 직접 식별자 | `artist_key`, `artist_name_ko`, `artist_name_standardized` | 작가 단위 OOF 기준에서 실질 개선이 0에 가까움. 신규 작가/블라인드에 취약. | 보정축으로 부적합 |

## 3. 유의미한 피처 상세

### 3.1 작가 세대 구간

`artist_birth_generation_bin`은 작가 생년을 세대 구간으로 변환한 범주형 피처다. 생년 자체보다 거칠게 묶기 때문에 특정 작가나 특정 연도에 과적합될 가능성이 낮다.

단일 피처 세그먼트 보정 결과:

| 설정 | validation delta MdAPE | validation delta MAPE | validation delta p95 | test delta MdAPE | test delta MAPE | test delta p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| generation bin, cap 0.05 | -0.0042 | -0.0012 | -0.0141 | -0.0016 | +0.0011 | -0.0063 |
| generation bin, cap 0.03 | -0.0011~-0.0034 | -0.0012~-0.0013 | -0.0141 | -0.0029 | +0.0004 | -0.0092 |

처리별로 보면 약한 Huber 잔차 보정에서 가장 안정적이었다.

| 처리 방식 | 후보 설정 | test delta MdAPE | test delta MAPE | test delta p95 | 평균 보정폭 |
| --- | --- | ---: | ---: | ---: | ---: |
| Huber 잔차 보정 | generation, cap 0.03, strength 0.75 | -0.0023 | -0.0010 | -0.0191 | 0.0129 |
| Huber 잔차 보정 | generation, cap 0.03, strength 0.50 | -0.0019 | -0.0008 | -0.0222 | 0.0086 |
| 세그먼트 median 보정 | generation, cap 0.03 | -0.0029 | +0.0004 | -0.0092 | 0.0107 |

판단:

- 세대 구간은 현재까지 가장 안정적인 보정축이다.
- `strength=0.75`는 MAPE 개선 폭이 조금 더 좋고, `strength=0.50`은 보정폭이 작고 p95 방어가 더 보수적이다.
- 제출/운영 후보는 `cap=0.03` 이하를 기본으로 두는 것이 안전하다.

### 3.2 작가 생년

`artist_meta_birth_year`는 작가의 생년 수치 피처다. 직접적인 연도 정보라 신호는 강하지만, 커버리지가 validation 46.8%, test 35.1% 수준이라 결측과 보정폭 관리가 중요하다.

| 설정 | validation delta MdAPE | validation delta MAPE | validation delta p95 | test delta MdAPE | test delta MAPE | test delta p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| birth year, cap 0.08 | -0.0074 | -0.0007 | -0.0125 | +0.0041 | +0.0031 | +0.0031 |
| birth year, cap 0.05 | -0.0044 | -0.0012 | -0.0125 | -0.0023 | +0.0009 | +0.0031 |
| birth year, cap 0.03 | -0.0042 | -0.0013 | -0.0125 | -0.0035 | -0.0001 | -0.0091 |

판단:

- 생년은 신호가 강하지만 cap이 커지면 test에서 과보정된다.
- `cap=0.03`처럼 작은 보정폭으로 제한했을 때만 test 안정성이 유지된다.
- 세대 구간보다 세밀하지만, 신규 데이터에서 생년 커버리지가 낮으면 적용 대상이 줄어든다.

### 3.3 작가 커리어 단계

`artist_meta_career_stage`는 작가의 활동 단계 또는 커리어 성숙도를 나타내는 작가 메타 피처다. 단일 피처 test에서는 세 지표가 모두 개선됐다.

| 설정 | validation delta MdAPE | validation delta MAPE | validation delta p95 | test delta MdAPE | test delta MAPE | test delta p95 | 평균 보정폭 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| career stage, cap 0.03 | -0.0032 | +0.0005 | -0.0061 | -0.0028 | -0.0008 | -0.0039 | 0.0096 |
| career stage, cap 0.05 | -0.0032 | +0.0003 | -0.0061 | -0.0021 | -0.0011 | -0.0039 | 0.0112 |

판단:

- test에서 MdAPE/MAPE/p95가 모두 개선된 점은 긍정적이다.
- 다만 validation MAPE가 명확히 개선되지 않아 단독 기본값으로 승격하기에는 아직 약하다.
- 세대 Huber 보정의 보조 후보 또는 앙상블 후보로 재검증하는 것이 적절하다.

## 4. 약하거나 조건부인 피처

### 4.1 전시 횟수 계열

전시 횟수 계열은 `artist_exhibition_solo_count`, `artist_exhibition_total_count_log`, `artist_exhibition_fair_count` 등이 포함된다.

관찰 결과:

- validation에서는 MdAPE 또는 p95가 개선되는 경우가 있었다.
- test에서는 MAPE만 소폭 개선되거나 p95가 악화되는 식으로 지표가 엇갈렸다.
- 전시/갤러리 피처를 Huber로 묶은 후보는 test에서 MdAPE, MAPE, p95가 모두 악화됐다.

대표 결과:

| 피처/처리 | test delta MdAPE | test delta MAPE | test delta p95 | 판단 |
| --- | ---: | ---: | ---: | --- |
| solo count segment | +0.0002 | -0.0010 | +0.0058 | MAPE만 일부 개선 |
| total count log segment | +0.0010 | +0.0005 | +0.0056 | test 악화 |
| external gallery/exhibition Huber | +0.0026 | +0.0021 | +0.0016 | 채택 보류 |

전시 횟수는 작가의 시장 노출과 관련될 수 있지만, 현재 데이터에서는 노이즈와 커버리지 문제가 커서 기본 보정축으로 쓰기 어렵다.

### 4.2 팔로워/작품 수/판매 작품 수

`artist_meta_followers`, `artist_meta_followers_log1p`, `artist_meta_for_sale_works_log1p`는 큰 오차를 줄이는 신호가 일부 있었다.

관찰 결과:

- `artist_meta_for_sale_works_log1p`는 test p95를 약 0.0076 줄였지만 MdAPE/MAPE가 악화됐다.
- 팔로워 계열은 validation p95는 좋아졌지만 test MAPE/MdAPE가 흔들렸다.
- 시장성 피처는 대표 정확도 개선보다 큰 오차 방어에 더 가까운 신호다.

판단:

- 단독 기본 보정축으로 쓰기보다는 고위험 구간 gating 또는 p95 전용 보정에만 제한적으로 검토한다.
- 보정폭은 `cap=0.03` 이하로 제한하는 것이 좋다.

### 4.3 갤러리 관련 피처

갤러리 피처는 현재 실험에서 영향도가 약했다.

원인:

- 일부 값은 거의 상수처럼 동작한다.
- `gallery_tier_validated_score`는 validation non-null 3건, test 0건으로 재현성이 없다.
- test에서 MAPE/p95 개선이 안정적으로 확인되지 않았다.

판단:

- 현재 데이터 품질에서는 갤러리 피처를 보정축으로 쓰지 않는다.
- 외부 검증 갤러리 등급 데이터가 충분히 채워진 뒤 재평가해야 한다.

### 4.4 작가 직접 식별자

`artist_key`, `artist_name_ko`, `artist_name_standardized`는 직접 식별자다. 단일 피처 보정 실험에서 실질적인 개선은 0에 가까웠다.

판단:

- 작가별 보정값을 외우는 방식은 기존 작가에는 좋아 보일 수 있지만 신규 작가와 블라인드 테스트에 취약하다.
- 작가 단위 OOF에서는 같은 작가가 train과 validation에 동시에 들어가지 않도록 막았기 때문에 직접 식별자 효과가 사라진다.
- 제출/운영 모델에서는 직접 식별자 보정 대신 세대, 생년, 커리어 단계처럼 일반화 가능한 피처를 사용해야 한다.

## 5. 처리 방식별 영향도

### 5.1 단일 피처 세그먼트 median 보정

로직:

1. 기준 모델의 log 예측값을 만든다.
2. 실제 log 가격과 기준 log 예측값의 차이를 잔차로 계산한다.
3. 피처 값별 또는 구간별로 validation train fold의 잔차 median을 계산한다.
4. 표본 수가 `min_n`보다 작은 구간은 보정하지 않는다.
5. 보정값에 shrink를 곱하고 `cap` 범위로 제한한다.
6. 기준 log 예측값에 제한된 보정값을 더한다.

수식:

```text
base_residual_log = actual_log_price - base_prediction_log
segment_correction = median(base_residual_log in same segment)
safe_correction = clip(segment_correction * strength, -cap, +cap)
corrected_prediction_log = base_prediction_log + safe_correction
```

영향:

- 단일 피처의 방향성을 확인하기 좋다.
- 생년, 세대, 커리어 단계처럼 해석 가능한 피처에서 의미 있는 신호가 보였다.
- 값이 세밀하거나 결측이 많은 피처는 validation 개선이 test로 이어지지 않을 수 있다.

### 5.2 Huber 잔차 보정

로직:

1. 기준 모델의 잔차를 목표값으로 둔다.
2. 선택한 피처를 입력으로 하여 Huber 손실 기반 잔차 모델을 학습한다.
3. 잔차 예측값에 strength를 곱한다.
4. `cap`으로 보정폭을 제한한다.
5. 기준 log 예측값에 제한된 잔차 보정값을 더한다.

수식:

```text
target_residual_log = actual_log_price - base_prediction_log
estimated_residual_log = HuberResidualModel(selected_features)
safe_correction = clip(estimated_residual_log * strength, -cap, +cap)
corrected_prediction_log = base_prediction_log + safe_correction
```

영향:

- 이상치가 섞인 가격 데이터에서 Ridge보다 보수적으로 동작한다.
- 세대 구간 단독 Huber가 test와 bootstrap에서 가장 안정적이었다.
- 다중 피처를 강하게 넣으면 validation은 좋아도 test MAPE가 악화되는 경우가 많았다.

### 5.3 Ridge 잔차 보정

로직은 Huber와 유사하지만 잔차 모델에 Ridge 회귀를 사용한다.

영향:

- validation p95나 MdAPE는 크게 좋아지는 후보가 있었다.
- 하지만 test MAPE가 0 또는 양수로 돌아서는 경우가 많아 기본 후보로는 Huber보다 약하다.
- 약한 strength와 작은 cap에서는 보조 비교군으로 의미가 있다.

### 5.4 다중 피처 조합 보정

조합 대상:

- 작가 생년
- 작가 세대 구간
- 작가 커리어 단계

관찰 결과:

| 조합 처리 | validation 경향 | test 경향 | 판단 |
| --- | --- | --- | --- |
| 생년+세대+커리어 Ridge | validation MdAPE/p95 강한 개선 | test MdAPE/MAPE 악화 가능 | 과적합 위험 |
| 생년+세대+커리어 Huber | validation p95 강한 개선 | test MdAPE/MAPE 악화 가능 | 과보정 위험 |
| 세대 단독 Huber | validation/test 모두 완만 개선 | bootstrap 안정성 양호 | 우선 후보 |
| 커리어 단독 segment | test 3지표 개선 | validation MAPE 약함 | 보조 후보 |

결론:

- 이번 단계에서는 피처를 많이 넣을수록 좋은 결과가 나오지 않았다.
- 성능을 올린 핵심은 피처 수가 아니라 보정폭 제한, 강건 손실, 일반화 가능한 축 선택이었다.

## 6. 현재 기준 추천 순위

| 순위 | 추천 처리 | 사용 피처 | 추천 이유 | 주의점 |
| ---: | --- | --- | --- | --- |
| 1 | 약한 Huber 잔차 보정 | 작가 세대 구간 | test MdAPE/MAPE/p95 모두 개선, bootstrap MAPE/p95 안정성 양호 | MdAPE 개선 확률은 중간 수준 |
| 2 | 더 보수적인 Huber 잔차 보정 | 작가 세대 구간 | 보정폭이 작고 p95 방어가 좋음 | MAPE 개선 폭은 1순위보다 작음 |
| 3 | 단일 세그먼트 보정 | 작가 생년, cap 0.03 | 생년 신호가 강하고 test에서도 개선 | 생년 커버리지 낮음 |
| 4 | 단일 세그먼트 보정 | 작가 커리어 단계 | test 3지표가 모두 개선 | validation MAPE 개선이 약함 |
| 5 | 제한적 p95 방어 후보 | 판매 작품 수/팔로워 계열 | 큰 오차 방어 신호 일부 | 대표 정확도 악화 가능 |

가장 먼저 운영 artifact로 검토할 후보:

```text
처리 방식: Huber 잔차 보정
사용 피처: 작가 세대 구간
보정 cap: 0.03
strength 후보: 0.75 또는 0.50
적용 위치: 기준 Warm log 예측값 산출 후, 최종 가격 변환 전 log 공간에서 보정
```

## 7. 다음 실험 제안

다음 단계는 새 피처를 더 넣기보다, 현재 가장 안정적인 축을 블라인드 조건에 가깝게 재검증하는 것이다.

1. 세대 Huber `cap=0.03`, `strength=0.50/0.75`를 신규 split과 0604 데이터에서 반복 검증한다.
2. 생년 cap 0.03과 커리어 단계 cap 0.03을 보조 후보로 같은 조건에서 재검증한다.
3. validation/test 고정 평가 외에 작가 단위 cluster bootstrap을 유지한다.
4. 직접 식별자, 갤러리, 전시 조합은 기본 후보에서 제외하고 진단표에만 남긴다.
5. p95를 목표로 할 때만 판매 작품 수/팔로워 계열을 gated correction으로 별도 실험한다.

## 8. 참고 산출물

- 단일 피처 영향도: `experiments/track6/PP-AMW7_warm_artist_related_single_feature_residual_correction/reports/result_report.md`
- 피처 조합 처리 영향도: `experiments/track6/PP-AMW8_warm_artist_signal_combo_residual_correction/reports/result_report.md`
- 반복 재검증: `experiments/track6/PP-AMW6_warm_artist_meta_residual_revalidation/reports/result_report.md`
- 이전 작가 메타 Huber 후보: `experiments/track6/PP-AMW5_warm_artist_meta_external_coefficient_correction/reports/result_report.md`

