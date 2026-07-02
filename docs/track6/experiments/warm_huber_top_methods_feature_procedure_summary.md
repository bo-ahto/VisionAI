# Warm Huber 최고 성능/안정성 조합 정리

- 작성일: 2026-06-08
- 대상: 지금까지 검증한 Warm 가격 예측 후처리 조합 중 성능과 안정성이 가장 높았던 5개 방법
- 표기 원칙: 실험 ID가 아니라 실제 계산 방법, 사용 피처, 적용 순서 기준으로 정리
- 결론: 점 예측 기본값은 `70:30 기준가 + 크기/신뢰도 잔차 Huber 보정`을 유지한다. 나머지는 연구 후보 또는 서비스 표시 정책으로 분리한다.

## 1. 전체 판단 요약

| 순위 | 방법 | 적용 대상 | fixed test MdAPE/MAPE/p95 | 0604 stress MdAPE/MAPE/p95 | 반복 안정성 | 판단 |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | 70:30 기준가 + 크기/신뢰도 잔차 Huber 보정 | Warm 점 예측 기본값 | `0.1388 / 0.2730 / 0.8064` | `0.2731 / 0.3744 / 0.9835` | row/artist OOF all3 `1.0 / 1.0` | 현재 기본 후보 |
| 2 | 기준가 gap 잔차 Huber + 저위험 라우팅 | Warm 연구 후보 | `0.1383 / 0.2729 / 0.8060` | `0.2734 / 0.3743 / 0.9835` | min any2/all3 `0.9333 / 0.4333` | fixed는 더 좋지만 운영 승격 보류 |
| 3 | p95 방어형 fallback-gap 라우팅 보정 | Warm p95 방어 후보 | `0.1382 / 0.2729 / 0.8063` | `0.2731 / 0.3745 / 0.9835` | min any2/all3 `0.8500 / 0.2833` | 참고 후보 |
| 4 | 방향 일치 segment 초미세 이동 | Warm tiny correction 후보 | `0.1388 / 0.2729 / 0.8062` | `0.2727 / 0.3744 / 0.9834` | 확장 반복 min any2/all3 `0.8085 / 0.2785` | fixed/0604 확인 후보 |
| 5 | quantile width 기반 가격범위/신뢰도 tier | 서비스 표시 정책 | 점 예측 대체 아님 | 점 예측 대체 아님 | high/low 위험도 분리 확인 | 가격 범위/신뢰도 표시용 |

평가 기준은 세 가지다.

- fixed test에서 MdAPE, MAPE, p95_APE가 기존 기준보다 동등하거나 개선되는지 확인한다.
- 0604 stress set에서 p95_APE가 무너지지 않는지 확인한다.
- row OOF와 artist OOF 반복 검증에서 MdAPE/MAPE/p95 세 지표가 동시에 개선되는 확률, 즉 all3 안정성을 본다.

## 2. 공통 계산 단위

모든 점 예측 후보는 원 가격이 아니라 로그 가격에서 보정한 뒤 다시 원 가격으로 환산한다.

```text
pred_price = exp(pred_log)
```

기준 로그 예측값은 아래 component 조합에서 출발한다.

```text
ppv8_log = 0.75 * pp_v2_log + 0.25 * l10_log
current_70_30_log = 0.70 * svc_log + 0.30 * ppv8_log
```

- `svc_log`: 유사 작품 기반 가격 component.
- `pp_v2_log`: 기존 후처리 후보 component.
- `l10_log`: Warm feature variant 계열 component.
- `ppv8_log`: 오차 안정화 목적의 방어적 component.
- `current_70_30_log`: 현재 v0.1 계열 Warm 기준값.

## 3. 70:30 기준가 + 크기/신뢰도 잔차 Huber 보정

### 목적

기존 `current_70_30_log`를 크게 바꾸지 않고, 남은 잔차 중 유사 작품 기준가의 신뢰도, 기준가 fallback, 크기 정보로 설명되는 작은 방향만 보정한다.

이 방법이 현재 최고 기본 후보인 이유는 fixed test, 0604 stress, 반복 OOF를 모두 통과했기 때문이다.

### 입력 피처

| 피처 | 의미 | 계수 방향 |
| --- | --- | ---: |
| `svc_fallback` | 원 유사 작품 fallback 기준가 | `-0.4718` |
| `shrunk_svc_prior` | 표본 수를 반영해 완화한 유사 작품 prior | `0.2221` |
| `current_shrunk_huber_gap` | 현재 70:30 기준과 완화 Huber 기준의 차이 | `0.1308` |
| `ppv8_defensive` | 방어적 후처리 component | `0.1081` |
| `shrunk_huber_refit` | 완화 기준가로 다시 맞춘 Huber 중심선 | `0.0878` |
| `raw_shrunk_prior_gap` | 원 prior와 완화 prior의 차이 | `-0.0580` |
| `log_area` | 작품 면적의 로그값 | `0.0570` |
| `current_ppv8_gap` | 70:30 기준과 ppv8 component의 차이 | `0.0491` |
| `svc_group_n_log` | 유사 작품 그룹 표본 수 로그값 | `-0.0122` |
| `svc_prior_iqr` | 유사 작품 prior의 IQR, 즉 가격 분산 폭 | `0.0008` |

### 적용 순서

1. `current_70_30_log`를 기준 로그 예측값으로 둔다.
2. 학습 구간에서 `residual_log = actual_log - current_70_30_log`를 만든다.
3. 위 피처들을 표준화한다.
4. 표준화 피처로 Huber residual model을 학습한다.
5. Huber 설정은 `alpha = 0.01`이다.
6. 예측된 보정값을 로그 가격 기준 `[-0.05, 0.05]`로 자른다.
7. 잘린 보정값에 `strength = 0.50`을 곱한다.
8. 최종 로그 가격은 아래처럼 계산한다.

```text
raw_correction = HuberResidualModel(features)
limited_correction = clip(raw_correction, -0.05, 0.05) * 0.50
final_log = current_70_30_log + limited_correction
final_price = exp(final_log)
```

### 성능과 판단

| split | 기준 70:30 | 이 방법 | 개선폭 |
| --- | ---: | ---: | ---: |
| validation MdAPE/MAPE/p95 | `0.1305 / 0.2110 / 0.6580` | `0.1260 / 0.2082 / 0.6479` | `-0.0045 / -0.0028 / -0.0101` |
| fixed test MdAPE/MAPE/p95 | `0.1405 / 0.2748 / 0.8331` | `0.1388 / 0.2730 / 0.8064` | `-0.0017 / -0.0018 / -0.0267` |
| 0604 stress MdAPE/MAPE/p95 | `0.2779 / 0.3774 / 0.9871` | `0.2731 / 0.3744 / 0.9835` | `-0.0049 / -0.0030 / -0.0036` |

row OOF 80회와 artist OOF 80회에서 MdAPE/MAPE/p95 all3 개선확률이 모두 `1.0`이다. 따라서 현재 운영 기본 점 예측 후보로 유지한다.

## 4. 기준가 gap 잔차 Huber + 저위험 라우팅

### 목적

기본 후보보다 더 낮은 MdAPE/MAPE를 얻기 위해 train-only 기준가 component를 추가로 만들되, 전체 행에 적용하지 않는다. 기준가 component끼리 서로 크게 어긋나지 않고, 표본 수와 면적 조건이 안정적인 행에만 작은 보정값을 적용한다.

### 입력 피처

이 방법은 기본 후보의 `final_log`를 새 기준값으로 둔 뒤, 그 기준값과 여러 기준가 component 사이의 gap을 사용한다.

| 피처 | 의미 | 계수 방향 |
| --- | --- | ---: |
| `basis_artist_overall_m1_gap` | 같은 작가 전체 기준가와 기본 후보의 차이 | `-0.0389` |
| `basis_artist_medium_support_m5_gap` | 같은 작가+재료/지지체 기준가와 기본 후보의 차이 | `-0.0257` |
| `shrink20_stable_gap` | 20% shrink 기준가와 기본 후보의 차이 | `0.0255` |
| `basis_component_spread` | 여러 기준가 component 간 최대 차이 | `-0.0236` |
| `log_area` | 작품 면적 로그값 | `-0.0231` |
| `basis_artist_size_m5_gap` | 같은 작가+크기 기준가와 기본 후보의 차이 | `-0.0188` |
| `basis_artist_size_medium_support_m5_gap` | 같은 작가+크기+재료/지지체 기준가와 기본 후보의 차이 | `-0.0187` |
| `basis_fallback_m5_n_log` | fallback 기준가 표본 수 로그값 | `-0.0175` |
| `fallback_stable_gap` | fallback 기준가와 기본 후보의 차이 | `0.0118` |
| `basis_fallback_m5_iqr` | fallback 기준가의 가격 분산 폭 | `0.0095` |

### 적용 순서

1. 먼저 `70:30 기준가 + 크기/신뢰도 잔차 Huber 보정`으로 기본 로그 예측값을 만든다.
2. 학습 데이터만 사용해 여러 기준가 component를 만든다.
   - 같은 작가 전체 중앙값 기준가
   - 같은 작가+크기 기준가
   - 같은 작가+재료/지지체 기준가
   - 같은 작가+크기+재료/지지체 기준가
   - 작가 기준이 부족할 때 쓰는 fallback 기준가
3. 각 기준가 component와 기본 로그 예측값의 차이를 gap 피처로 만든다.
4. `stable_residual_log = actual_log - stable_log`를 목표값으로 Huber residual model을 학습한다.
5. Huber 설정은 `alpha = 0.001`, correction cap은 `0.005`, strength는 `0.50`이다.
6. 보정 후보는 아래처럼 만든다.

```text
raw_basis_correction = HuberResidualModel(basis_gap_features)
basis_correction = clip(raw_basis_correction, -0.005, 0.005) * 0.50
candidate_log = stable_log + basis_correction
```

7. 단, 아래 low-risk 조건을 만족하는 행에만 `candidate_log`를 적용한다.

```text
svc_group_n >= 5
basis_component_spread <= 1.0532
5.9339 <= log_area <= 9.9587
```

8. 조건을 만족하지 않으면 기본 후보 `stable_log`를 그대로 쓴다.

```text
if low_risk_condition:
    final_log = candidate_log
else:
    final_log = stable_log
```

### 성능과 판단

- fixed test: `0.1383 / 0.2729 / 0.8060`
- 기본 후보 대비 fixed test 개선폭: `MdAPE -0.0005`, `MAPE -0.0001`, `p95 -0.0003`
- 0604 stress: `0.2734 / 0.3743 / 0.9835`
- row/artist 반복 검증 min any2/all3: `0.9333 / 0.4333`

fixed test에서는 기본 후보보다 세 지표가 모두 소폭 좋다. 하지만 all3 안정성이 `0.90` 기준에 크게 못 미친다. 따라서 운영 기본 후보로 바로 교체하지 않고, 가장 유력한 연구 후보로 보관한다.

## 5. p95 방어형 fallback-gap 라우팅 보정

### 목적

기준가 gap 기반 보정이 p95를 악화시키는 문제를 줄이기 위해, fallback 기준가와 기본 후보가 크게 어긋나지 않는 행에만 더 작은 보정을 적용한다.

이 방법은 평균 성능을 크게 밀기보다 p95_APE 방어를 우선한다.

### 입력 피처

피처 구성은 `기준가 gap 잔차 Huber + 저위험 라우팅`과 거의 같다. 차이는 보정폭과 적용 조건이다.

- 기준가 component gap 피처
- `basis_component_spread`
- `fallback_stable_gap`
- `basis_fallback_m5_n_log`
- `basis_fallback_m5_iqr`
- `log_area`

### 적용 순서

1. 기본 후보 `stable_log`를 만든다.
2. 기준가 gap 피처로 `actual_log - stable_log` 잔차 Huber를 학습한다.
3. Huber 설정은 `alpha = 0.001`이다.
4. correction cap은 `0.0075`, strength는 `0.20`으로 둔다.
5. fallback 기준가와 기본 후보의 절대 차이가 validation 하위 75% 안에 있는 행만 보정한다.

```text
abs_fallback_stable_gap <= 0.6607
```

6. 적용식은 아래와 같다.

```text
raw_correction = HuberResidualModel(basis_gap_features)
micro_correction = clip(raw_correction, -0.0075, 0.0075) * 0.20

if abs_fallback_stable_gap <= 0.6607:
    final_log = stable_log + micro_correction
else:
    final_log = stable_log
```

### 성능과 판단

- fixed test: `0.1382 / 0.2729 / 0.8063`
- 0604 stress: `0.2731 / 0.3745 / 0.9835`
- 반복 검증 min any2/all3: `0.8500 / 0.2833`

fixed test MdAPE는 더 낮지만 반복 all3가 약하다. 운영 후보가 아니라 p95 방어형 참고 후보로만 남긴다.

## 6. 방향 일치 segment 초미세 이동

### 목적

기본 후보보다 강한 source 후보들은 validation OOF에서 MAPE/p95 신호가 좋았지만 fixed test에서 MdAPE나 p95를 악화시키는 문제가 있었다. 이 방법은 source 후보를 그대로 쓰지 않고, row OOF와 artist OOF에서 방향이 일치한 segment에만 매우 작은 이동을 허용한다.

### 핵심 아이디어

source 후보의 전체 예측값을 쓰지 않는다. 아래 조건을 통과한 segment에서만 `source_log - stable_log` 방향으로 미세 이동한다.

1. segment의 실제 잔차 중앙값 `median(actual_log - stable_log)`를 계산한다.
2. source 후보 이동 방향 `median(source_log - stable_log)`를 계산한다.
3. row OOF와 artist OOF 양쪽에서 두 값의 부호가 같은지 확인한다.
4. p95가 기준보다 나빠지지 않는 segment만 남긴다.
5. top segment 2개만 사용한다.

사용된 대표 segment rule은 아래와 같다.

```text
svc_group_level = artist
OR
qwidth_band = qwidth_low AND gap_band = gap_005_010
```

### 적용 순서

1. 기본 후보 `stable_log`를 만든다.
2. component gap 기반 source 후보를 만든다. 이 source는 `svc`, `ppv8`, `l10`, quantile width, component gap, 위험도 피처를 사용해 기본 후보에서 움직일 방향을 제안한다.
3. validation row OOF와 artist OOF에서 segment별 방향 일치 여부를 계산한다.
4. 통과한 segment에서만 source 방향으로 이동한다.
5. 이동 weight는 `0.025`, cap은 `0.001`이다.

```text
directional_move = source_log - stable_log
micro_move = clip(0.025 * directional_move, -0.001, 0.001)

if row_artist_direction_consensus_segment:
    final_log = stable_log + micro_move
else:
    final_log = stable_log
```

### 성능과 판단

- fixed test: `0.1388 / 0.2729 / 0.8062`
- 0604 stress: `0.2727 / 0.3744 / 0.9834`
- 확장 반복 검증 min any2/all3: `0.8085 / 0.2785`

fixed test와 0604에서는 거의 모든 지표가 아주 작게 좋아진다. 하지만 개선폭이 너무 작고 반복 all3 안정성이 낮다. 따라서 p95-neutral tiny correction 후보로만 관리한다.

## 7. quantile width 기반 가격범위/신뢰도 tier

### 목적

이 방법은 점 예측값을 바꾸기 위한 후보가 아니다. 기본 점 예측은 유지하되, 예측 가격 범위와 신뢰도 표시를 안정적으로 나누기 위한 정책이다.

### 입력 피처

| 피처 | 의미 |
| --- | --- |
| `quantile_width` | q10~q90 로그 가격 범위의 폭 |
| `pred_spread` | 주요 component 예측값 간 분산 |
| `svc_group_n` | 유사 작품 그룹 표본 수 |
| `price_range_ratio` | 원화 가격 범위의 상대 폭 |
| `q10_log`, `q50_log`, `q90_log` | quantile model 기반 가격 범위 |

### 적용 순서

1. 기본 점 예측은 `70:30 기준가 + 크기/신뢰도 잔차 Huber 보정`을 사용한다.
2. 별도로 q10/q50/q90 예측값을 만든다.
3. `quantile_width = q90_log - q10_log`를 계산한다.
4. validation에서 고정한 경계를 사용해 width tier를 나눈다.

```text
qwidth_q33 = 1.2116
qwidth_q66 = 1.5114
qwidth_q80 = 1.7065
pred_spread_q66 = 0.2611
pred_spread_q80 = 0.3789
```

5. 예시는 아래처럼 해석한다.

```text
if quantile_width <= 1.2116 and pred_spread <= 0.2611:
    confidence = high
elif quantile_width <= 1.5114:
    confidence = medium
elif quantile_width <= 1.7065:
    confidence = low
else:
    confidence = very_low
```

6. high confidence 구간은 point estimate를 그대로 노출하고, low/very_low 구간은 가격 범위와 주의 문구를 함께 보여준다.

### 성능과 판단

- high confidence tier는 validation/test에서 MdAPE와 큰 오차율이 낮게 분리됐다.
- test high tier MdAPE는 약 `0.1148`, q10~q90 포함률은 약 `0.8636`으로 확인됐다.
- low tier는 p95가 크게 높아져 위험도 분리 신호가 뚜렷했다.

따라서 이 방법은 점 예측 후보로 쓰지 않는다. 서비스에서 가격 범위, 신뢰도 badge, 검토 필요 여부를 나누는 표시 정책으로 유지한다.

## 8. 최종 권장안

운영 기본 점 예측은 아래 순서를 사용한다.

```text
1. svc_log, ppv8_log, l10_log 등 운영 component를 만든다.
2. current_70_30_log = 0.70 * svc_log + 0.30 * ppv8_log를 계산한다.
3. 크기/신뢰도 잔차 Huber 피처를 만든다.
4. Huber residual correction을 계산한다.
5. correction을 [-0.05, 0.05]로 clip하고 0.50만 반영한다.
6. final_log = current_70_30_log + limited_correction.
7. final_price = exp(final_log).
8. quantile_width 기반 confidence/range tier를 별도로 계산해 표시 정책에 사용한다.
```

기준가 gap low-risk routing은 fixed test에서 더 좋아 보이지만, 반복 all3 안정성이 부족하므로 기본값으로 교체하지 않는다. 다음 개선 작업은 이 라우팅 후보의 all3 안정성을 끌어올리는 방향이어야 한다.

