# Warm 최종 운영 모델 상세 정리

- 모델 ID: `warm_catboost_artist_qcap_risk_strict_v1`
- 실험 ID: `PP-OPT7_warm_final_operational_freeze`
- 기준 모델: `hcoef_stable`
- 최종 후보: `p95guard__seed=combo_cat=cb_tier=same__qmult=same__cap=0p02__caprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__guard=risk_strict_cap0p020`
- 원 seed 후보: `combo_focus__cat=cb_tier=same__qmult=same__cap=0p02__capprof=qcap_balanced__s=1p0__artist=am_h_birth_gen_gn_a01_c03_s075__cw=1p0__aw=0p5__totalcap=0p025`

## 1. 모델의 목적

이 모델은 Warm 구간 작품의 가격을 예측하기 위한 후처리 보정 모델이다.  
기준 가격을 새로 만드는 모델이 아니라, 기존 Warm Huber 계수보정 계열에서 가장 안정적이었던 `hcoef_stable` 로그가격을 기준값으로 놓고, 그 위에 작은 로그 보정값을 더한다.

핵심 목표는 다음과 같다.

1. 기준 모델인 `hcoef_stable`보다 MdAPE와 MAPE를 낮춘다.
2. p95 오차가 크게 악화되지 않도록 보정값을 제한한다.
3. 작가 메타 보정은 적극 사용하되, 불확실성이 큰 구간에서는 보정 강도를 낮춘다.
4. 최종 산식이 재현 가능하도록 모든 보정 단계와 계수를 고정한다.

## 2. 최종 성능

이 성능표는 **제출용 고신뢰 100건 샘플 기준이 아니라**, 지금까지 Warm 실험들이 사용한 기본 학습/검증/테스트 split 기준이다. 따라서 아래의 test MAPE `0.271395`는 기본 fixed test 607건 전체 기준이며, 제출용 100건 MAPE와 직접 비교하면 안 된다.

| 항목 | 파일/기준 | row 수 | 사용 목적 |
| --- | --- | ---: | --- |
| 기본 학습 데이터 | `data/track6_split_with_year_type_edition_size_artist_name/track6_train.csv` | 26914 | upstream Warm 후보와 보정 모델 학습 기준 |
| Warm validation | `data/track6_split_with_year_type_edition_size_artist_name/track6_val_warm.csv` | 519 | OOF 검증 성능 비교 |
| Warm fixed test | `data/track6_split_with_year_type_edition_size_artist_name/track6_test_warm.csv` | 607 | 최종 holdout test 성능 비교 |
| 최종 예측 테이블 | `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_predictions.csv` | validation 519 + test 607, 모델별 2벌 | 기준 모델과 최종 모델의 row별 예측값 |

재현 감사 결과, `final_candidate_predictions.csv`의 row id는 Warm validation 519건과 Warm fixed test 607건에 정확히 일치한다. 재계산된 지표와 문서에 보고된 지표의 최대 차이는 부동소수점 반올림 수준(`2.75e-15`)이다.

| 구분 | split | n | MdAPE | MAPE | p95 APE | 기준 대비 MdAPE | 기준 대비 MAPE | 기준 대비 p95 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 기준 `hcoef_stable` | validation OOF | 519 | 0.125993 | 0.208206 | 0.647948 | 0.000000 | 0.000000 | 0.000000 |
| 최종 모델 | validation OOF | 519 | 0.125923 | 0.207023 | 0.636595 | -0.000070 | -0.001183 | -0.011353 |
| 기준 `hcoef_stable` | fixed test | 607 | 0.138803 | 0.272989 | 0.806366 | 0.000000 | 0.000000 | 0.000000 |
| 최종 모델 | fixed test | 607 | 0.136893 | 0.271395 | 0.808130 | -0.001911 | -0.001594 | +0.001764 |

해석:

- test에서 MdAPE와 MAPE는 개선됐다.
- test p95는 완전히 개선되지는 않았지만 악화 폭이 `+0.001764`로 제한됐다.
- guard 적용 전 seed 후보는 test MAPE 개선 폭이 더 컸지만 p95 악화가 `+0.003967`이었다.
- 최종 모델은 p95 악화 폭을 줄이기 위해 MAPE 개선 일부를 포기한 운영 안정형 후보이다.

## 3. 전체 예측 흐름

```text
입력 작품/작가/비교군 정보
        |
        v
[1] Warm Huber 계수보정 기준 로그가격 생성
        |
        v
[2] CatBoost 잔차 보정 계산
        |
        v
[3] 작가 생년/세대 Huber 보정 계산
        |
        v
[4] CatBoost 보정과 작가 보정을 합산
        |
        v
[5] 신뢰도/불확실성 기반 위험 구간 판정
        |
        v
[6] 위험 구간별 보정 강도 축소
        |
        v
[7] 최종 로그가격 산출
        |
        v
[8] exp 변환으로 최종 KRW 가격 산출
```

### 3.1 최종 산식 한눈에 보기

이 모델의 핵심은 아래 한 줄이다. 단, 여기서 덧셈은 KRW 가격이 아니라 **로그가격 공간**에서 수행된다.

```text
최종예측_로그가격 = 최종기준_로그가격 + 최종적용_보정로그값
최종예측_KRW가격 = exp(최종예측_로그가격)
```

이를 코드 변수명으로 쓰면 다음과 같다.

```text
pred_log   = hcoef_stable + final_correction_log
pred_price = exp(pred_log)
```

KRW 가격 관점으로 바꾸면 보정값은 단순 덧셈이 아니라 곱셈 배율이 된다.

```text
최종기준_KRW가격 = exp(최종기준_로그가격)
보정배율 = exp(최종적용_보정로그값)
최종예측_KRW가격 = 최종기준_KRW가격 * 보정배율
```

### 3.2 기준가 생성 계층

최종 운영 모델의 기준가는 `hcoef_stable`이다. 이 값은 OPT7에서 새로 학습하지 않고, 이전 Huber 계수보정 계열에서 선택된 안정 기준가를 그대로 가져온다. 실험 코드와 폴더명에서는 이 계열을 `HCOEF`, 즉 Huber coefficient 계열로 표기하지만, 아래 설명에서는 의미가 바로 보이도록 `Huber잔차보정`이라는 변수명을 사용한다.

```text
최종기준_로그가격 = hcoef_stable
```

`hcoef_stable`은 아래처럼 기존 Warm 70:30 기준가에 작은 Huber 잔차 보정을 더한 값이다.

```text
hcoef_stable
  = 기존Warm70대30_로그가격 + Huber잔차보정_로그값
```

기존 Warm 70:30 기준가는 다음과 같다.

```text
기존Warm70대30_로그가격
  = 0.70 * 유사작품통계_HuberSeed평균_로그가격
  + 0.30 * PPV8_안정블렌드_로그가격
```

여기서 PPV8 안정 블렌드는 다시 두 후보의 로그가격 조합이다.

```text
PPV8_안정블렌드_로그가격
  = 0.75 * V2_방어형후보_로그가격
  + 0.25 * L10_생성버킷_순차보정_로그가격
```

따라서 기준가 계층을 모두 펼치면 아래 구조다.

```text
최종기준_로그가격
  = hcoef_stable

hcoef_stable
  = (
      0.70 * 유사작품통계_HuberSeed평균_로그가격
    + 0.30 * PPV8_안정블렌드_로그가격
    )
    + Huber잔차보정_로그값

PPV8_안정블렌드_로그가격
  = 0.75 * V2_방어형후보_로그가격
  + 0.25 * L10_생성버킷_순차보정_로그가격
```

`Huber잔차보정_로그값`은 실제 후보명 `hcoef2_size_reliability_cap005_s050` 계열에서 온다.

```text
Huber잔차보정_학습타깃 = actual_log - 기존Warm70대30_로그가격

Huber원시잔차보정
  = HuberRegressor(
      입력피쳐 = [
        ppv8_defensive,
        svc_fallback,
        shrunk_huber_refit,
        shrunk_svc_prior,
        log_area,
        svc_group_n_log,
        svc_prior_iqr,
        current_ppv8_gap,
        current_shrunk_huber_gap,
        raw_shrunk_prior_gap
      ],
      target = Huber잔차보정_학습타깃,
      epsilon = 1.35,
      alpha = 0.01
    )

Huber잔차보정_로그값
  = clip(Huber원시잔차보정, -0.05, +0.05) * 0.50
```

Huber 잔차 보정의 처리 순서는 다음과 같다.

```text
1. 기존Warm70대30_로그가격을 기준 예측으로 둔다.
2. actual_log - 기존Warm70대30_로그가격을 잔차 타깃으로 만든다.
3. 가격 후보 간 차이, 유사작품 표본 수, 작품 면적, 유사작품 가격분산을 피쳐로 만든다.
4. 숫자 피쳐는 median imputation 후 표준화한다.
5. HuberRegressor가 잔차를 예측한다.
6. 예측 잔차를 -0.05 ~ +0.05 로그 범위로 자른다.
7. strength 0.50을 곱해 보정 강도를 절반으로 낮춘다.
8. 기존Warm70대30_로그가격에 더해 hcoef_stable을 만든다.
```

### 3.3 최종 OPT7 보정값 생성 계층

최종 OPT7에서 새로 추가되는 보정값은 두 모델 보정과 하나의 rule-based guard로 구성된다.

```text
최종적용_보정로그값 = final_correction_log
```

전체 식은 아래와 같다.

```text
CatBoost보정
  = clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한)

작가보정
  = clip(작가Huber원시잔차보정, -0.03, +0.03) * 0.75

1차보정
  = clip(
      1.0 * CatBoost보정
    + 0.5 * 작가보정,
    -0.025,
    +0.025
    )

최종적용_보정로그값
  = clip(1차보정 * 위험계수, -0.020, +0.020)

최종예측_로그가격
  = hcoef_stable + 최종적용_보정로그값
```

이 식의 의미는 다음과 같다.

| 단계 | 수식 | 해석 |
| --- | --- | --- |
| CatBoost 보정 제한 | `clip(CatBoost원시잔차보정, -CatBoost동적상한, +CatBoost동적상한)` | 작품 피쳐, 신뢰도, 모델 간 불일치가 만든 잔차 보정을 먼저 제한한다. `quantile_width`가 크면 상한을 더 낮춘다. |
| 작가 보정 제한 | `clip(작가Huber원시잔차보정, -0.03, +0.03) * 0.75` | 작가 생년/세대에서 온 보정을 ±0.03 안으로 자른 뒤 75%만 사용한다. |
| 두 보정 합산 | `1.0 * CatBoost보정 + 0.5 * 작가보정` | CatBoost 보정은 주 보정이므로 전부 반영하고, 작가 보정은 보조 신호이므로 절반만 반영한다. |
| 1차 cap | `clip(..., -0.025, +0.025)` | 두 보정이 같은 방향으로 커져도 전체 이동을 ±0.025 로그 안으로 제한한다. |
| 위험계수 적용 | `1차보정 * 위험계수` | 불확실성이 큰 row는 보정 자체를 약하게 만든다. |
| 최종 cap | `clip(..., -0.020, +0.020)` | 최종적으로 기준가에서 ±0.020 로그 이상 움직이지 못하게 막는다. |

숫자로 보면 아래와 같다.

```text
예시:
  CatBoost보정 = +0.018
  작가보정 = +0.012

1차보정 전 합산
  = 1.0 * 0.018 + 0.5 * 0.012
  = 0.018 + 0.006
  = +0.024

1차보정
  = clip(+0.024, -0.025, +0.025)
  = +0.024

정상 구간 최종보정
  = clip(+0.024 * 0.90, -0.020, +0.020)
  = clip(+0.0216, -0.020, +0.020)
  = +0.020

중위험 최종보정
  = clip(+0.024 * 0.55, -0.020, +0.020)
  = +0.0132

고위험 최종보정
  = clip(+0.024 * 0.15, -0.020, +0.020)
  = +0.0036
```

따라서 같은 CatBoost/작가 보정이 나와도, 위험 구간에서는 실제 가격 이동이 크게 줄어든다.

처리 순서는 다음과 같다.

```text
1. hcoef_stable을 최종기준_로그가격으로 읽는다.
2. CatBoost 잔차 모델이 actual_log - hcoef_stable 방향의 보정값을 예측한다.
3. quantile_width에 따라 CatBoost 보정 상한을 0.02 또는 0.01로 정한다.
4. 작가 생년/세대 Huber 모델이 actual_log - hcoef_stable 방향의 작가 보정값을 예측한다.
5. CatBoost보정 1.0배와 작가보정 0.5배를 합산한다.
6. 합산 보정값을 -0.025 ~ +0.025로 제한한다.
7. 신뢰도, quantile 폭, 모델 간 spread, 표본 수로 위험계수를 정한다.
8. 위험계수를 곱하고 최종 보정값을 -0.020 ~ +0.020으로 다시 제한한다.
9. hcoef_stable + 최종보정으로 최종 로그가격을 만든다.
10. exp()로 KRW 가격을 만든다.
```

### 3.4 사용 모델과 역할

| 단계 | 사용 모델/방식 | 학습 타깃 | 주요 입력 | 출력 |
| --- | --- | --- | --- | --- |
| 기존 Warm 70:30 | 로그가격 가중 평균 | 별도 학습 없음 | `svc_numeric_seed_mean`, `ppv8_service_proxy` | `current_70_30` |
| 유사작품통계 기준가 | HuberRegressor seed 평균 | `log(price_krw)` | 작품 크기/재료/작가키, 유사작품 가격 통계 | `svc_numeric_seed_mean` |
| PPV8 안정 블렌드 | 로그가격 가중 평균 | 별도 학습 없음 | V2 방어형 후보, L10 순차보정 후보 | `ppv8_service_proxy` |
| Huber 기준가 보정 | HuberRegressor residual correction | `actual_log - current_70_30` | 가격 후보 간 gap, 유사작품 신뢰도, 면적, IQR | `hcoef_stable` |
| 최종 작품/신뢰도 보정 | CatBoostRegressor residual correction | `actual_log - hcoef_stable` | 기준/보조 예측값, quantile 폭, spread, 표본 수, 작품 면적, 신뢰도 구간 | `CatBoost보정` |
| 최종 작가 보정 | HuberRegressor residual correction | `actual_log - hcoef_stable` | 작가 생년, 작가 세대 구간 | `작가보정` |
| 최종 guard | rule-based cap/scale | 학습 없음 | confidence tier, quantile width, spread, gap, svc 표본 수 | `final_correction_log` |

## 4. 기준 로그가격

최종 모델의 중심값은 `hcoef_stable`이다.

```text
기준로그가격 = hcoef_stable
```

`hcoef_stable`은 Warm Huber 계수보정 계열에서 선택된 안정 기준가다. 이 값은 다음 계열의 정보를 이미 반영한 기준 예측 로그가격으로 사용된다.

| 피쳐/값 | 의미 |
| --- | --- |
| `svc_numeric_seed_mean` | 유사 작품 통계 기반 로그가격 후보 |
| `ppv8_service_proxy` | PPV8 계열 안정 블렌드 로그가격 후보 |
| `current_70_30` | 기존 Warm 70:30 계열 참조 후보 |
| `l10_seq_pred_log` | L10 생성 버킷 순차 모델 로그가격 후보 |
| `quantile_width` | L10 quantile 폭. 가격 예측 불확실성 신호 |
| `l10_price_range_ratio` | L10 가격 범위 비율. 가격 분산 신호 |
| `svc_group_n` | 유사 작품 그룹의 표본 수 |
| `log_area` | 작품 면적 로그값 |

최종 모델은 기준값 자체를 다시 학습하지 않는다. 기준값은 고정하고, 그 위에 작은 보정만 더한다.

## 5. CatBoost 잔차 보정

CatBoost 보정은 기준 로그가격이 실제 로그가격과 얼마나 차이 나는지를 학습한 잔차 모델이다.

```text
CatBoost 학습타깃 = 실제로그가격 - hcoef_stable
```

최종 모델에서 사용한 CatBoost 설정은 다음과 같다.

| 항목 | 값 |
| --- | --- |
| 모델 | CatBoostRegressor |
| 학습 타깃 | `actual_log - hcoef_stable` |
| loss | MAE |
| iterations | 180 |
| depth | 4 |
| learning_rate | 0.04 |
| l2_leaf_reg | 12.0 |
| train policy | `confidence_weighted` |
| sample weight | high 1.00, medium 0.45, low 0.15 |
| validation 방식 | artist_key 기반 GroupKFold 우선 |
| 보정 strength | 1.0 |
| CatBoost cap profile | `qcap_balanced` |
| 기본 cap | 0.02 |

CatBoost 입력 피쳐는 아래와 같다.

### 5.1 숫자 피쳐

| 피쳐 | 의미 |
| --- | --- |
| `hcoef_stable` | 기준 로그가격 |
| `current_70_30` | 기존 70:30 Warm 참조 로그가격 |
| `ppv8_service_proxy` | PPV8 계열 보조 로그가격 |
| `svc_numeric_seed_mean` | 유사작품 통계 로그가격 |
| `l10_seq_pred_log` | L10 생성 버킷 순차 모델 로그가격 |
| `quantile_width` | L10 q90-q10 로그 폭 |
| `l10_price_range_ratio` | L10 가격범위/중앙가격 비율 |
| `svc_group_n` | 유사작품 그룹 표본 수 |
| `svc_group_n_log` | `log1p(svc_group_n)` |
| `log_area` | 작품 면적 로그값 |
| `component_prediction_spread` | 주요 후보 로그가격의 표준편차 |
| `component_prediction_range` | 주요 후보 로그가격의 최대-최소 범위 |
| `current_vs_stable_gap_abs` | `abs(current_70_30 - hcoef_stable)` |
| `current_minus_stable_log` | `current_70_30 - hcoef_stable` |
| `ppv8_minus_stable_log` | `ppv8_service_proxy - hcoef_stable` |
| `svc_minus_stable_log` | `svc_numeric_seed_mean - hcoef_stable` |
| `l10_minus_stable_log` | `l10_seq_pred_log - hcoef_stable` |
| `confidence_risk_score` | quantile 폭, 모델 spread, 가격범위, gap, 표본 수를 합친 위험 점수 |

### 5.2 범주형 피쳐

| 피쳐 | 의미 |
| --- | --- |
| `svc_coverage_tier` | 유사작품 비교군 커버리지 구간 |
| `svc_group_level` | 유사작품 그룹 수준 |
| `service_confidence_tier` | 서비스 레벨 confidence tier |
| `qwidth_band` | quantile width 구간화 값 |
| `svc_group_n_band` | 유사작품 표본 수 구간 |
| `gap_band` | 기준 후보 간 gap 구간 |
| `pred_spread_band` | 예측 후보 spread 구간 |
| `stable_pred_price_band` | 기준 예측가격대 구간 |
| `medium_support_bucket` | medium/support 계열 버킷 |

### 5.3 CatBoost 보정값 산식

원시 CatBoost 잔차를 먼저 구한다.

```text
CatBoost원시보정 = CatBoostResidualModel(입력피쳐)
```

이후 `qcap_balanced` cap을 적용한다.

```text
CatBoost동적상한 =
  0.02 if quantile_width <= 1.60
  0.01 if quantile_width > 1.60

CatBoost보정 = clip(CatBoost원시보정, -CatBoost동적상한, +CatBoost동적상한)
```

## 6. 작가 생년/세대 Huber 보정

작가 보정은 CatBoost와 별도로 작가 메타의 경향을 반영하는 작은 잔차 보정이다.

최종 모델에서 사용한 작가 보정 후보는 다음 원 seed의 일부다.

```text
huber_birth_generation_gatenone_alpha0p01_cap0p03_s0p75
```

의미:

| 항목 | 값 |
| --- | --- |
| 모델 | Huber residual correction |
| 사용 피쳐 | 작가 생년/세대 구간 |
| gate | none |
| alpha | 0.01 |
| cap | 0.03 |
| strength | 0.75 |
| 최종 조합 내 가중치 | 0.5 |

작가 보정은 다음 식으로 해석할 수 있다.

```text
작가세대잔차 = HuberResidualModel(작가 생년/세대 구간)
작가보정 = clip(작가세대잔차, -0.03, +0.03) * 0.75
```

이 보정은 작가별 개별 ID를 직접 강하게 외우는 방식이 아니라, 생년과 세대 구간의 가격 잔차 경향을 약하게 반영하는 방식이다.

### 6.1 세대 구간 생성 로직

최종 작가 보정에서 "세대"는 작가 메타의 생년 컬럼에서 파생한다.

| 문서 변수명 | 실제 컬럼명 | 의미 |
| --- | --- | --- |
| 작가생년원본값 | `artist_meta_birth_year` | 외부 작가 메타에서 들어온 생년 값 |
| 작가생년숫자값 | `birth_year_numeric` | 생년을 숫자로 변환한 값 |
| 작가세대구간 | `artist_birth_generation_bin` | 숫자 생년을 구간화한 범주형 값 |
| 생년결측여부 | `artist_meta_birth_year_missing` | 생년이 없으면 1, 있으면 0 |

세대 구간은 실제 스크립트에서 아래처럼 계산된다.

```text
작가생년숫자값 = to_numeric(artist_meta_birth_year)

작가세대구간 =
  "__MISSING__" if 작가생년숫자값 is missing
  "pre_1940"  if 작가생년숫자값 <= 1940
  "1940s"     if 1940 < 작가생년숫자값 <= 1950
  "1950s"     if 1950 < 작가생년숫자값 <= 1960
  "1960s"     if 1960 < 작가생년숫자값 <= 1970
  "1970s"     if 1970 < 작가생년숫자값 <= 1980
  "1980s"     if 1980 < 작가생년숫자값 <= 1990
  "1990_plus" if 1990 < 작가생년숫자값
```

구현 관점에서는 `pd.cut`을 사용한다.

```text
bins   = [-inf, 1940, 1950, 1960, 1970, 1980, 1990, inf]
labels = ["pre_1940", "1940s", "1950s", "1960s", "1970s", "1980s", "1990_plus"]
```

주의할 점은 라벨명이 "1940s", "1950s"처럼 보이지만, 실제 구간은 `pd.cut`의 우측 닫힌 구간 기준이다. 예를 들어 `1950`년생은 `"1940s"` 구간에 들어가고, `1951`년생부터 `"1950s"` 구간에 들어간다. 문서는 의미상 세대명을 쓰되, 재현 기준은 위의 구간식을 따른다.

결측 생년은 임의로 평균 생년으로만 대체하지 않는다. `artist_birth_generation_bin="__MISSING__"`와 `artist_meta_birth_year_missing=1`을 별도 신호로 넣어, "생년 정보가 없는 작가"의 잔차 경향도 따로 학습한다.

### 6.2 Huber 모델에 들어가는 세대 변수

최종 선택 작가 보정의 feature set은 `birth_generation`이며 실제 입력 피쳐는 두 개다.

```text
입력피쳐 = [
  artist_meta_birth_year,
  artist_birth_generation_bin
]
```

학습용 설계행렬에서는 다음처럼 변환된다.

```text
생년대체값 =
  artist_meta_birth_year if 생년이 존재
  학습셋_생년_median if 생년이 결측

생년표준화값 =
  (생년대체값 - 학습셋_생년_mean) / 학습셋_생년_std

생년결측여부 =
  1 if artist_meta_birth_year is missing
  0 otherwise

세대더미_pre_1940  = 1 if artist_birth_generation_bin == "pre_1940" else 0
세대더미_1940s     = 1 if artist_birth_generation_bin == "1940s" else 0
세대더미_1950s     = 1 if artist_birth_generation_bin == "1950s" else 0
세대더미_1960s     = 1 if artist_birth_generation_bin == "1960s" else 0
세대더미_1970s     = 1 if artist_birth_generation_bin == "1970s" else 0
세대더미_1980s     = 1 if artist_birth_generation_bin == "1980s" else 0
세대더미_1990_plus = 1 if artist_birth_generation_bin == "1990_plus" else 0
세대더미_missing   = 1 if artist_birth_generation_bin == "__MISSING__" else 0
```

fixed test 적용 시에는 validation 전체를 학습셋으로 사용하므로 생년 표준화 기준은 다음과 같았다.

| 값 | 수치 |
| --- | ---: |
| validation 생년 median | 1983.000000 |
| validation 생년 mean | 1980.805395 |
| validation 생년 std | 10.799749 |
| validation 생년 보유 row | 243 / 519 |
| test 생년 보유 row | 213 / 607 |

validation OOF 검증에서는 각 fold마다 "해당 fold를 제외한 학습 fold"의 median/mean/std를 다시 계산한다. 그래서 검증은 누수 없이 계산되고, test는 validation 전체 학습 후 한 번 적용된다.

### 6.3 Huber 잔차 학습식

작가 Huber 모델은 가격 자체가 아니라 기준 모델의 잔차를 학습한다.

```text
기준로그가격_i = hcoef_stable_i
실제로그가격_i = actual_log_i

작가잔차타깃_i = 실제로그가격_i - 기준로그가격_i
```

Huber 모델은 아래 목적함수를 최소화한다.

```text
예측잔차_i = 절편 + Σ(계수_j * 입력피쳐_ij)
오차_i = 작가잔차타깃_i - 예측잔차_i

HuberLoss_epsilon(오차_i) =
  0.5 * 오차_i^2                         if |오차_i| <= epsilon
  epsilon * (|오차_i| - 0.5 * epsilon)   if |오차_i| > epsilon

학습목표 =
  minimize Σ HuberLoss_1.35(오차_i) + 0.01 * ||계수||^2
```

따라서 세대가 최종 가격에 들어가는 경로는 다음이다.

```text
작가세대잔차 =
    절편
  + β_birth_year * 생년표준화값
  + β_birth_missing * 생년결측여부
  + β_pre_1940  * 세대더미_pre_1940
  + β_1940s     * 세대더미_1940s
  + β_1950s     * 세대더미_1950s
  + β_1960s     * 세대더미_1960s
  + β_1970s     * 세대더미_1970s
  + β_1980s     * 세대더미_1980s
  + β_1990_plus * 세대더미_1990_plus
  + β_missing   * 세대더미_missing

작가보정 = clip(작가세대잔차, -0.03, +0.03) * 0.75
```

`gate=none`이므로 생년이 없다는 이유로 row를 제외하지 않는다. 생년이 없으면 `__MISSING__` 구간과 결측 플래그로 계산한다.

### 6.4 세대 계수와 해석

`PP-AMW10`의 full validation fit에서 저장된 상위 계수는 다음과 같다. 이 값은 표준화된 생년값과 one-hot 세대 더미에 대한 계수이므로, 원 생년 1년당 효과로 직접 읽으면 안 된다.

| 설계 피쳐 | 계수 |
| --- | ---: |
| `artist_birth_generation_bin=1940s` | +0.533422 |
| `artist_birth_generation_bin=pre_1940` | -0.404488 |
| `artist_meta_birth_year` | -0.092801 |
| `artist_birth_generation_bin=1960s` | -0.077801 |
| `artist_birth_generation_bin=1950s` | +0.036050 |
| `artist_birth_generation_bin=1980s` | -0.032350 |
| `artist_birth_generation_bin=1990_plus` | +0.029008 |
| `artist_meta_birth_year_missing` | -0.020904 |
| `artist_birth_generation_bin=__MISSING__` | -0.020904 |
| `artist_birth_generation_bin=1970s` | -0.014170 |

계수가 크게 보여도 실제 가격 이동은 강하게 제한된다. 작가 보정 단독 상한은 다음과 같다.

```text
|작가보정| <= 0.03 * 0.75 = 0.0225 로그포인트
```

최종 조합에서는 작가보정에 다시 `0.5`를 곱한다.

```text
|최종조합_작가성분| <= 0.5 * 0.0225 = 0.01125 로그포인트
```

risk strict guard까지 적용하면 세대/생년 보정이 단독으로 움직일 수 있는 최대 범위는 아래 수준이다.

| 위험 구간 | 위험계수 | 세대/생년 보정 단독 최대 로그 이동 | 가격 배율 근사 |
| --- | ---: | ---: | ---: |
| 정상 구간 | 0.90 | 0.010125 | 약 ±1.02% |
| 중위험 | 0.55 | 0.006188 | 약 ±0.62% |
| 고위험 | 0.15 | 0.001688 | 약 ±0.17% |

즉, 세대는 방향성을 주는 보조 신호로 쓰이지만 최종 가격을 크게 흔드는 피쳐는 아니다.

## 7. 1차 합산 보정

CatBoost 보정과 작가 보정을 합쳐 1차 보정값을 만든다.

```text
1차보정 = clip(
    1.0 * CatBoost보정
  + 0.5 * 작가보정,
  -0.025,
  +0.025
)
```

가중치 해석:

| 보정 | 가중치 | 역할 |
| --- | ---: | --- |
| CatBoost보정 | 1.0 | 작품/신뢰도/모델 불일치 기반 주 보정 |
| 작가보정 | 0.5 | 생년/세대 기반 보조 보정 |

작가 보정은 의미 있는 신호지만 p95를 흔들 수 있으므로 절반 가중치로 제한했다.

## 8. 위험 구간 판정

1차 보정값을 그대로 쓰지 않고, 신뢰도와 불확실성 피쳐로 위험 구간을 판정한다.

### 8.1 고위험 조건

아래 조건 중 하나라도 만족하면 고위험이다.

```text
고위험 =
    confidence_tier == low_confidence
 OR quantile_width >= 1.65
 OR component_prediction_spread >= 0.13
 OR current_vs_stable_gap_abs >= 0.05
 OR svc_group_n < 4
```

| 조건 | 의미 |
| --- | --- |
| `low_confidence` | 기존 신뢰도 판정상 저신뢰 |
| `quantile_width >= 1.65` | L10 예측 구간이 넓어 가격 불확실성이 큼 |
| `component_prediction_spread >= 0.13` | 후보 모델들의 로그가격 차이가 큼 |
| `current_vs_stable_gap_abs >= 0.05` | 기존 70:30 후보와 안정 기준가 차이가 큼 |
| `svc_group_n < 4` | 유사작품 표본이 매우 적음 |

### 8.2 중위험 조건

고위험이 아니면서 아래 조건 중 하나라도 만족하면 중위험이다.

```text
중위험 =
    confidence_tier == medium_confidence
 OR quantile_width >= 1.28
 OR component_prediction_spread >= 0.08
 OR current_vs_stable_gap_abs >= 0.025
 OR svc_group_n < 8
```

### 8.3 위험계수

```text
위험계수 =
  0.15 if 고위험
  0.55 if 중위험
  0.90 otherwise
```

위험계수의 역할은 불확실성이 큰 구간의 보정값을 줄여 p95 악화를 방어하는 것이다.

위험계수는 보정값을 새로 만드는 모델이 아니라, 이미 계산된 `1차보정`을 얼마나 믿고 적용할지 정하는 축소 계수다.

| 위험 구간 | 위험계수 | 의미 |
| --- | ---: | --- |
| 정상 구간 | 0.90 | 보정 방향을 비교적 신뢰하되, 그래도 10%는 줄인다. |
| 중위험 | 0.55 | 보정 방향은 일부 믿지만 절반 수준만 반영한다. |
| 고위험 | 0.15 | 보정 방향을 거의 믿지 않고 아주 작은 움직임만 허용한다. |

예를 들어 `1차보정 = +0.020`이면 실제 적용값은 아래처럼 줄어든다.

```text
정상 구간: +0.020 * 0.90 = +0.018
중위험:   +0.020 * 0.55 = +0.011
고위험:   +0.020 * 0.15 = +0.003
```

## 9. 최종 보정과 가격 산출

위험계수를 곱한 뒤 최종 보정값을 다시 cap으로 제한한다.

```text
최종보정 = clip(1차보정 * 위험계수, -0.020, +0.020)
```

최종 로그가격과 최종 원화 가격은 다음과 같다.

```text
최종로그가격 = hcoef_stable + 최종보정

최종KRW가격 = exp(최종로그가격)
```

## 10. 한 row 기준 계산 순서

```text
1. hcoef_stable을 읽는다.
2. CatBoost 입력 피쳐를 만든다.
3. CatBoost 원시 잔차 보정값을 예측한다.
4. quantile_width에 따라 CatBoost 보정 상한을 정한다.
5. CatBoost 보정값을 동적 상한으로 clip한다.
6. 작가 생년/세대 Huber 보정값을 읽거나 계산한다.
7. CatBoost보정 + 0.5 * 작가보정을 합산한다.
8. 합산 보정값을 -0.025 ~ +0.025로 clip한다.
9. high risk 또는 medium risk 여부를 판정한다.
10. 위험계수 0.15, 0.55, 0.90 중 하나를 적용한다.
11. 최종 보정값을 -0.020 ~ +0.020으로 다시 clip한다.
12. hcoef_stable + 최종보정으로 최종 로그가격을 만든다.
13. exp(최종로그가격)으로 최종 KRW 가격을 만든다.
```

## 11. 변수명 대응표

| 문서 변수명 | 실제 컬럼/후보명 | 설명 |
| --- | --- | --- |
| 기준로그가격 | `hcoef_stable` | 최종 모델의 기준 로그가격 |
| 기존 70:30 참조가격 | `current_70_30` | 기존 Warm 참조 후보 |
| PPV8 보조가격 | `ppv8_service_proxy` | PPV8 계열 보조 로그가격 |
| 유사작품 통계가격 | `svc_numeric_seed_mean` | 유사작품 통계 기반 로그가격 |
| L10 순차가격 | `l10_seq_pred_log` | L10 생성 버킷 순차 로그가격 |
| 예측구간폭 | `quantile_width` | q90-q10 로그 폭 |
| 가격범위비율 | `l10_price_range_ratio` | L10 가격범위/중앙가격 비율 |
| 유사작품표본수 | `svc_group_n` | 비교 가능한 유사작품 수 |
| 후보가격분산 | `component_prediction_spread` | 주요 후보 로그가격의 표준편차 |
| 기준가격차이 | `current_vs_stable_gap_abs` | `current_70_30`과 `hcoef_stable`의 절대 차이 |
| 신뢰도구간 | `confidence_tier` | high/medium/low confidence |
| CatBoost보정 | `CatBoost residual correction` | 작품/신뢰도/불일치 기반 잔차 보정 |
| 작가보정 | `huber_birth_generation...` | 작가 생년/세대 Huber 잔차 보정 |
| 최종보정 | `correction_log` | 최종 모델이 기준로그가격에 더하는 로그 보정값 |
| 최종로그가격 | `pred_log` | 최종 예측 로그가격 |
| 최종KRW가격 | `pred_price` | 최종 예측 원화 가격 |

## 12. 최종 후보 선정 근거

비교 후보는 크게 세 부류였다.

| 후보군 | 장점 | 한계 | 최종 판단 |
| --- | --- | --- | --- |
| CatBoost + 작가보정 원 seed | MAPE 개선 폭이 큼 | p95 악화가 약 +0.004 수준 | guard 전 후보로만 사용 |
| XGBoost medium-only | test에서 MdAPE/MAPE/p95 모두 개선 | 반복 validation 안정성이 낮음 | 운영 후보 제외 |
| CatBoost + 작가보정 + risk_strict guard | MdAPE/MAPE 개선 유지, p95 악화 제한 | p95 완전 개선은 아님 | 최종 운영 후보 채택 |

최종 모델은 "최대 MAPE 개선" 후보가 아니라 "운영 안정성을 고려한 균형 후보"다.

## 13. 재현 산출물

| 파일 | 설명 |
| --- | --- |
| `scripts/track6/run_pp_opt7_warm_final_operational_freeze.py` | 최종 후보 고정 및 문서 생성 스크립트 |
| `scripts/track6/audit_pp_opt7_warm_full_split_reproducibility.py` | 기본 Warm validation/test split row coverage와 성능 재계산 검증 스크립트 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/artifacts/final_model_config.json` | 최종 모델 설정 JSON |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_predictions.csv` | 기준 모델과 최종 모델의 row별 예측값 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_metrics.csv` | validation/test 성능 지표 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_candidate_stability.csv` | 반복 validation 안정성 지표 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/outputs/final_logic_steps.csv` | 최종 로직 단계 표 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reproduction/full_split_recomputed_metrics.csv` | 기본 Warm validation/test split에서 재계산한 전체 성능 지표 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reproduction/full_split_row_coverage_audit.csv` | 기본 split row id와 예측 테이블 row id 일치 여부 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reproduction/full_split_reported_metric_comparison.csv` | 재계산 지표와 보고 지표의 차이 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reproduction/full_split_reproducibility_audit.json` | 재현 감사 요약 JSON |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reproduction/full_split_reproducibility_report.md` | 기본 split 기준 재현 감사 리포트 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reports/final_model_report.md` | 결과 중심 요약 |
| `experiments/track6/PP-OPT7_warm_final_operational_freeze/reports/final_model_detailed_technical_summary.md` | 본 상세 설명 문서 |

## 14. 재현 실행 명령

```bash
python3 scripts/track6/run_pp_opt7_warm_final_operational_freeze.py
python3 scripts/track6/audit_pp_opt7_warm_full_split_reproducibility.py
```

첫 번째 명령은 최종 후보 설정, 성능표, 예측 CSV, 로직 표, 요약 문서를 다시 생성한다.
두 번째 명령은 제출용 100건이 아니라 기본 Warm validation 519건과 fixed test 607건 기준으로 row coverage를 확인하고 MdAPE/MAPE/p95를 재계산한다.

주의할 점은 PP-OPT7이 `track6_train.csv` 하나에서 전체 upstream 후보를 처음부터 다시 학습하는 단일 스크립트가 아니라는 점이다. 현재 재현 구조는 이전 실험에서 고정된 PP-SVC3/HCOEF/L10/CatBoost/작가보정 후보 산출물을 입력으로 받아 최종 후보를 freeze하고, 기본 split 기준 성능을 정확히 재계산하는 구조다. raw train 데이터부터 end-to-end 재학습까지 제출하려면 upstream 후보 생성 체인까지 별도 artifact로 묶어야 한다.
