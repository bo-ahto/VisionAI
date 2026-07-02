# Warm-lite Unified / Cold 가격 예측 모델 권장 리포트

- 작성일: 2026-06-16
- 문서 목적: 기존 Warm/Warm-lite/Cold 3분기 구조 이후 추가 실험을 반영한 차기 권장 라우팅과 성능 근거 정리
- 기준 문서: `partner_warm_cold_best_model_report.html`
- 문서 상태: 현재 0.1v API 구현값이 아니라, CF5~CF9 및 Q6 검증 이후의 권장안
- 핵심 결론: 같은 작가 가격 이력이 1건 이상이면 Warm-lite unified 계열로 통합하고, 0건이면 Cold를 유지한다. Warm-lite 내부에서는 기본 current 보정을 쓰되, tail 위험 조건에서는 CF7 tail guard를 조건부 적용한다.

## 1. 결론 요약

기존 라우팅은 같은 작가 가격 이력 수를 기준으로 세 경로를 나눴다.

```text
5건 이상 → Warm
1~4건   → Warm-lite
0건     → Cold
```

추가 실험 이후 권장 라우팅은 아래와 같다.

```text
1건 이상 → Warm-lite unified
0건     → Cold
```

그리고 Warm-lite unified 내부에서는 아래처럼 한 번 더 나눈다.

```text
기본 조건        → Warm-lite current
tail 위험 조건   → Warm-lite CF7 tail guard
```

최종 권장안은 다음 형태다.

```text
if same_artist_history_n == 0:
    Cold
else:
    if abs(q50_full_log - q50_lean_log) >= 0.0252975:
        Warm-lite CF7 tail guard
    else:
        Warm-lite current
```

이 조건부 라우터의 내부 실험명은 `route_gap_q50`이다. `0.0252975 log`는 validation에서 full/lean Quantile 중앙 예측값 차이의 중앙값으로 산출된 threshold다.

## 2. 최종 권장 라우팅

| 라우팅 경로 | 적용 조건 | 모델 역할 | 최종 상태 |
|---|---|---|---|
| Cold | 같은 작가 가격 이력 0건 | 작가 본인 가격 이력이 없을 때 작품/작가/검색 문맥 기반 예측 | 유지 |
| Warm-lite current | 같은 작가 가격 이력 1건 이상, full/lean 중앙 예측 차이 < 0.0252975 log | 중앙값 정확도 우선 기본 예측 | 권장 기본 |
| Warm-lite CF7 tail guard | 같은 작가 가격 이력 1건 이상, full/lean 중앙 예측 차이 >= 0.0252975 log | 큰 오차 방어를 위해 잔차 보정을 더 강하게 적용 | 조건부 권장 |
| 기존 Warm WMIN8 | 기존 5건 이상 Warm 경로 | 기존 운영 성능 비교 기준 | 차기 권장 라우팅에서는 기본 경로에서 제외 후보 |

중요한 해석은 다음과 같다.

- Warm WMIN8이 모든 지표에서 나쁜 모델이라는 뜻은 아니다. p95/RMSE log는 여전히 강하다.
- 다만 같은 fixed-test 조건에서 Warm-lite unified가 MdAPE/MAPE 기준으로 더 강했고, CF7 또는 조건부 라우터를 붙이면 tail 약점도 크게 줄었다.
- 따라서 5건 이상이라는 경계로 Warm과 Warm-lite를 나누는 근거는 약해졌다.
- Cold는 같은 작가 가격 이력이 없는 경우의 난이도가 다르므로 계속 별도 경로로 유지한다.

## 3. 성능 요약

### 3.1 Warm fixed-test 607건 동일 조건 비교

아래 표는 Warm fixed-test 607건에서 기존 Warm WMIN8, Warm-lite current, CF7 전체 적용, 조건부 라우터를 같은 행 기준으로 비교한 결과다.

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log | 해석 |
|---|---:|---:|---:|---:|---:|---|
| 기존 Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 | 기존 5건 이상 Warm 기준. p95/RMSE가 가장 낮음 |
| Warm-lite current | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 | MdAPE 최저. tail은 약함 |
| Warm-lite CF7 전체 적용 | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 | MAPE 최저에 가깝고 p95를 크게 개선. MdAPE는 current보다 악화 |
| 권장안 route_gap_q50 | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 | current 대비 MAPE/p95/RMSE 개선, MdAPE 손실은 제한적 |

### 3.2 current 대비 권장안 개선폭

| 비교 | MdAPE 변화 | MAPE 변화 | p95 APE 변화 | RMSE log 변화 |
|---|---:|---:|---:|---:|
| route_gap_q50 - Warm-lite current | +0.001920 | -0.001624 | -0.045147 | -0.002141 |
| CF7 전체 적용 - Warm-lite current | +0.004742 | -0.001294 | -0.057690 | -0.002209 |

해석:

- CF7 전체 적용은 p95를 가장 크게 낮추지만 MdAPE 손실도 더 크다.
- route_gap_q50은 CF7의 tail 개선 일부를 가져오면서 MdAPE 손실을 줄인다.
- 최종 권장안은 성능 균형상 route_gap_q50이다.

### 3.3 기존 Warm WMIN8 대비 권장안

| 비교 | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|
| 기존 Warm WMIN8 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| route_gap_q50 | 0.086405 | 0.223590 | 0.758056 | 0.380030 |
| 차이(route - Warm) | -0.017921 | -0.012224 | +0.018640 | +0.002840 |

해석:

- route_gap_q50은 Warm WMIN8보다 MdAPE/MAPE가 좋다.
- p95/RMSE log는 Warm WMIN8이 아직 약간 더 좋다.
- 그러나 기존 Warm-lite current의 가장 큰 약점이었던 p95 `0.803203`을 `0.758056`까지 낮췄기 때문에, 통합 라우팅 후보로 실용성이 생겼다.

## 4. 라우팅 변경 근거

### 4.1 왜 5건 이상 Warm 고정이 약해졌나

추가 비교 실험은 같은 작품 행 또는 같은 학습 조건에서 Warm과 Warm-lite 계열을 다시 비교했다.

| 실험 | 목적 | 핵심 결과 |
|---|---|---|
| PP-ROUTE-CF3 | k=1~6 조건별 Warm clean stack과 Warm-lite를 각각 재학습해 비교 | Warm-lite가 k=1~6 대부분 지표에서 Warm clean stack보다 우세 |
| PP-ROUTE-CF4 | k=1~6 전체 조건을 한 Warm-lite 모델로 학습 | 단일 Warm-lite pooled 후보가 다수 k에서 Warm clean stack보다 우세 |
| PP-ROUTE-CF5 | full Warm train distribution으로 Warm-lite unified를 학습해 현재 Warm WMIN8과 비교 | Warm-lite unified가 MdAPE/MAPE 우세, p95/RMSE는 Warm WMIN8 우세 |
| PP-ROUTE-CF6 | full-history 조건에서 Warm clean stack과 Warm-lite unified를 모두 재학습 | Warm-lite unified가 Warm clean full-history retrained보다 모든 주요 지표 우세 |

이 결과는 기존 5건 경계가 “작가 이력이 5건 이상이면 반드시 Warm이 더 좋다”는 실험 근거로는 더 이상 충분하지 않다는 뜻이다.

### 4.2 왜 Cold는 그대로 유지하나

Cold는 같은 작가 가격 이력이 없는 상황이다. Warm-lite unified는 같은 작가의 가격 이력이 최소 1건은 있어야 작가 통계와 residual 보정이 의미를 가진다.

따라서 라우팅 통합 범위는 아래로 제한한다.

```text
같은 작가 가격 이력 1건 이상: Warm-lite unified 계열
같은 작가 가격 이력 0건: Cold
```

Cold까지 Warm-lite로 통합하지 않는다.

## 5. Warm-lite Unified 계산 구조

### 5.1 기본 계산식

Warm-lite unified current는 두 Quantile 중앙 예측값의 평균 위에 LightGBM Huber residual 보정을 더한다.

```text
qavg_log =
    0.50 * q50_full_log
  + 0.50 * q50_lean_log

Warm-lite current 로그가격 =
    qavg_log
  + clip(0.50 * LightGBM_Huber_residual_log, -0.10, +0.10)
```

여기서:

- `q50_full_log`: 전체 피처 기반 LightGBM Quantile 중앙값 예측
- `q50_lean_log`: 흔들림을 줄인 축소 피처 기반 LightGBM Quantile 중앙값 예측
- `qavg_log`: 두 중앙값 예측의 평균 기준 로그가격
- `LightGBM_Huber_residual_log`: 기준 로그가격에서 남은 오차를 예측한 값
- `clip(x, -0.10, +0.10)`: 보정값이 -0.10보다 작으면 -0.10, +0.10보다 크면 +0.10으로 제한

### 5.2 CF7 tail guard 계산식

CF7은 같은 residual을 더 강하게 반영하되, 과도한 보정을 막기 위해 clip 상한을 둔다.

```text
Warm-lite CF7 로그가격 =
    qavg_log
  + clip(1.00 * LightGBM_Huber_residual_log, -0.15, +0.15)
```

CF7의 목적은 중앙값을 더 맞히는 것이 아니라 큰 오차를 줄이는 것이다.

### 5.3 조건부 라우터 route_gap_q50

route_gap_q50은 full/lean 두 중앙 예측이 충분히 다를 때만 CF7을 적용한다.

```text
gap_log = abs(q50_full_log - q50_lean_log)

if gap_log >= 0.0252975:
    final_log = Warm-lite CF7 로그가격
else:
    final_log = Warm-lite current 로그가격
```

이 threshold는 validation에서 `gap_log`의 중앙값(q50)으로 산출됐다.

의미:

- full/lean 두 예측축이 거의 같으면 모델이 비교적 안정적이라고 보고 current를 유지한다.
- 두 예측축이 갈라지면 불확실성이 있다고 보고 CF7 tail guard를 켠다.
- 이 방식은 CF7 전체 적용보다 보수적이며, MdAPE 손실을 줄이려는 균형형 라우터다.

## 6. 학습 단계와 사용 단계

### 6.1 학습 단계

학습 단계에서는 실제 가격이 있는 과거 데이터를 사용한다.

```text
[Warm train 데이터]
  - 작품 크기/면적/비율
  - 매체/지지체
  - 같은 작가 가격 이력 통계
  - 실제 로그가격
        |
        v
[작가 이력 통계 생성]
  - fold 내부 통계로 자기 가격 누수 차단
  - 같은 작가 + 매체/지지체 + 크기 구간
  - 같은 작가 + 크기 구간
  - 같은 작가 전체
        |
        v
[LightGBM Quantile 학습]
  - q10/q50/q90 full 축
  - q50 lean 축
        |
        v
[OOF residual 생성]
  - residual = 실제 로그가격 - OOF(qavg_log)
        |
        v
[LightGBM Huber residual 학습]
  - 작품 피처 + 작가 이력 통계 + Quantile 예측값으로 residual 예측
        |
        v
[라우터 threshold 산출]
  - gap_log = abs(q50_full_log - q50_lean_log)
  - validation gap_log q50 = 0.0252975
```

학습 단계에서 실제 가격은 모델과 threshold를 만들기 위해 사용된다. 사용 단계에서는 실제 가격을 알 수 없으므로 쓰지 않는다.

### 6.2 사용 단계

새 작품이 들어오면 동결된 통계, 모델, threshold만 사용한다.

```text
[새 작품 입력]
  - 작가명/작가 식별 결과
  - 작품 크기
  - 매체/지지체
  - 작품 메타
        |
        v
[같은 작가 가격 이력 확인]
  - 0건이면 Cold
  - 1건 이상이면 Warm-lite unified
        |
        v
[Warm-lite unified]
  - 작가 이력 통계 생성
  - q50_full_log 계산
  - q50_lean_log 계산
  - qavg_log 계산
  - LightGBM_Huber_residual_log 계산
        |
        v
[조건부 tail guard]
  - gap_log = abs(q50_full_log - q50_lean_log)
  - gap_log >= 0.0252975이면 CF7
  - 아니면 current
        |
        v
[최종 가격]
  - final_price_krw = exp(final_log)
```

## 7. 피처와 로직 설명

### 7.1 공통 작품 피처

| 피처 | 사용 이유 |
|---|---|
| width_cm, height_cm, depth_cm | 작품 물리 크기 |
| area_cm2, log_area | 가격과 강하게 연결되는 면적 신호 |
| aspect_ratio | 세로형/가로형/극단 비율 구분 |
| has_depth, is_3d_candidate | 입체 작품 여부 |
| medium_category | 재료/매체 계열 |
| support_category | 지지체 계열 |
| size_bucket | 크기 구간화 |

### 7.2 작가 이력 통계 피처

| 피처 | 의미 |
|---|---|
| grp_log_price_median | 같은 작가 비교군의 로그가격 중앙값 |
| grp_log_price_q25/q75 | 같은 작가 비교군 가격 분포의 하위/상위 분위 |
| grp_log_price_iqr | q75 - q25, 가격 분산 정도 |
| grp_unit_area_median | 면적당 가격 중앙값 |
| grp_unit_area_iqr | 면적당 가격 변동 폭 |
| grp_n_log | 비교군 표본 수를 log1p로 변환한 값 |
| grp_match_level | 어떤 단계의 비교군이 매칭됐는지 나타내는 값 |

비교군 매칭은 좁은 조건부터 넓은 조건으로 찾는다.

```text
1. 같은 작가 + 같은 매체/지지체 + 같은 크기 구간
2. 같은 작가 + 같은 크기 구간
3. 같은 작가 전체
4. 통계 생성 실패 시 fallback 통계
```

### 7.3 full/lean Quantile 축

full 축은 정보를 넓게 사용한다.

```text
작품 피처 + 작가 이력 통계 + 매체/지지체/크기 구간
  → q10_log, q50_full_log, q90_log
```

lean 축은 흔들림을 줄인 피처 구성이다.

```text
핵심 작품 피처 + 핵심 작가 이력 통계
  → q50_lean_log
```

두 축을 같이 쓰는 이유:

- full 축은 정보량이 많아 평균 성능에 유리할 수 있다.
- lean 축은 저표본/잡음 상황에서 안정적일 수 있다.
- 두 축의 차이가 크면 예측 불확실성이 커진 것으로 해석한다.

## 8. 실험 근거

### 8.1 CF5: Warm-lite unified 가능성

CF5는 Warm-lite unified를 full Warm train distribution으로 학습하고, Warm fixed-test 607건에서 현재 Warm WMIN8과 비교했다.

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 |
| Warm-lite unified full-history retrained | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |

해석:

- Warm-lite unified는 MdAPE/MAPE에서 개선됐다.
- p95/RMSE는 Warm WMIN8이 더 좋았다.
- 따라서 통합 가능성은 생겼지만 tail guard가 필요했다.

### 8.2 CF6: full-history 재학습 비교

CF6는 Warm clean stack과 Warm-lite unified를 모두 full-history 조건으로 재학습해 비교했다.

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm clean full-history retrained | 607 | 0.114838 | 0.244538 | 0.816909 | 0.387520 |
| Warm-lite unified full-history retrained | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |

해석:

- 같은 full-history 재학습 조건에서는 Warm-lite unified가 Warm clean stack보다 전 지표 우세했다.
- 기존 Warm WMIN8 artifact와 완전히 같은 재현은 아니므로 CF5와 함께 해석한다.

### 8.3 CF7: tail guard 후보

CF7은 residual 보정 강도와 clip 상한을 검증했다.

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm-lite current | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |
| CF7 tail guard | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 |

해석:

- CF7은 p95/RMSE를 크게 개선했다.
- MdAPE는 악화됐다.
- 따라서 전체 적용보다는 조건부 적용이 더 적합하다.

### 8.4 CF8: bootstrap 및 k=1~6 stress

CF8은 CF7 후보를 artist-cluster bootstrap과 k=1~6 capped-history stress로 검증했다.

Bootstrap에서 CF7이 current보다 좋을 확률:

| 지표 | CF7이 current보다 좋은 비율 |
|---|---:|
| MdAPE | 0.1945 |
| MAPE | 0.7835 |
| p95 APE | 0.8305 |
| RMSE log | 0.9550 |

해석:

- CF7은 MdAPE 개선 후보가 아니다.
- CF7은 MAPE/p95/RMSE 개선 후보다.
- 특히 RMSE log 개선은 bootstrap에서 안정적이었다.

k=1~6 stress에서 CF7 전체 적용은 p95 기준으로 current보다 모든 k에서 좋았다. 다만 k=1/3에서는 MAPE/RMSE가 아주 작게 흔들렸다.

### 8.5 Q6: Warm-lite native 정확 검증

Q6는 기존 Warm-lite native 검증 구조에서 CF7 후보를 정확히 재평가했다.

| 검증 | 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---|---:|---:|---:|---:|---:|
| Q1 native | current | 1,947 | 0.107246 | 0.275773 | 0.852026 | 0.423003 |
| Q1 native | CF7 전체 적용 | 1,947 | 0.112221 | 0.275745 | 0.851658 | 0.419824 |
| Q2 native | current | 7,284 | 0.154475 | 0.303435 | 1.000528 | 0.482084 |
| Q2 native | CF7 전체 적용 | 7,284 | 0.159414 | 0.301687 | 0.988525 | 0.480387 |

해석:

- CF7 전체 적용은 native 검증에서도 MAPE/p95/RMSE를 개선했다.
- MdAPE 악화가 반복 확인됐다.
- 조건부 라우터가 필요하다는 판단이 강화됐다.

### 8.6 CF9: 조건부 CF7 라우터

CF9는 validation에서 조건부 라우터 후보를 고르고 test에 적용했다.

선택된 후보:

```text
route_gap_q50
조건: abs(q50_full_log - q50_lean_log) >= 0.0252975
validation route share: 0.500963
test route share: 0.565074
```

Test 결과:

| 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---:|---:|---:|---:|---:|
| Warm-lite current | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 |
| route_gap_q50 | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 |

해석:

- current 대비 MAPE/p95/RMSE 모두 개선됐다.
- MdAPE 손실은 CF7 전체 적용보다 작다.
- 따라서 최종 권장 라우터는 route_gap_q50이다.

## 9. k=1~6 stress 상세

CF9의 k=1~6 capped-history stress 결과는 아래와 같다.

| k | 후보 | n | MdAPE | MAPE | p95 APE | RMSE log | 해석 |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | current | 519 | 0.172755 | 0.311118 | 0.890055 | 0.446076 | current가 MdAPE/MAPE/RMSE 우세 |
| 1 | route_gap_q50 | 519 | 0.174032 | 0.311709 | 0.897335 | 0.447839 | k=1에서는 route_gap_q50 비권장 신호 |
| 2 | current | 519 | 0.161448 | 0.304920 | 0.889889 | 0.423878 | current보다 route가 평균/tail 개선 |
| 2 | route_gap_q50 | 519 | 0.158753 | 0.302751 | 0.869473 | 0.423962 | RMSE는 거의 동일 |
| 3 | current | 519 | 0.142914 | 0.257082 | 0.877410 | 0.430237 | route가 전 지표 소폭 개선 |
| 3 | route_gap_q50 | 519 | 0.141770 | 0.256938 | 0.876824 | 0.430150 | 균형 양호 |
| 4 | current | 519 | 0.111142 | 0.255190 | 0.841395 | 0.397345 | route가 MAPE/p95/RMSE 개선 |
| 4 | route_gap_q50 | 519 | 0.112640 | 0.252787 | 0.816695 | 0.395484 | MdAPE 소폭 악화 |
| 5 | current | 519 | 0.119911 | 0.230864 | 0.676274 | 0.369027 | route가 p95/RMSE 개선 |
| 5 | route_gap_q50 | 519 | 0.121648 | 0.230832 | 0.660076 | 0.368844 | MdAPE 악화 |
| 6 | current | 519 | 0.114118 | 0.226295 | 0.764952 | 0.370710 | route가 MAPE/p95 개선 |
| 6 | route_gap_q50 | 519 | 0.114295 | 0.225356 | 0.756899 | 0.370603 | 거의 동일한 MdAPE |

해석:

- route_gap_q50은 k=2~6에서 대체로 유효하다.
- k=1에서는 current가 더 안정적이다.
- 운영 라우터를 더 보수적으로 만들려면 `same_artist_history_n == 1`에서는 current를 유지하는 추가 조건을 검토할 수 있다.

## 10. 보수 대안: residual_down 라우터

native Warm-lite 검증에서는 `residual_down` 라우터가 안정적인 대안으로 확인됐다.

```text
if LightGBM_Huber_residual_log < 0:
    CF7 tail guard
else:
    current
```

| 검증 | 후보 | n | MdAPE | MAPE | p95 APE | RMSE log |
|---|---|---:|---:|---:|---:|---:|
| Q1 native | current | 1,947 | 0.107246 | 0.275773 | 0.852026 | 0.423003 |
| Q1 native | residual_down | 1,947 | 0.108689 | 0.272493 | 0.834596 | 0.422073 |
| Q2 native | current | 7,284 | 0.154475 | 0.303435 | 1.000528 | 0.482084 |
| Q2 native | residual_down | 7,284 | 0.157698 | 0.298540 | 0.978524 | 0.481631 |

해석:

- residual_down은 저이력 native 검증에서 MAPE/p95/RMSE를 개선했다.
- MdAPE는 소폭 나빠진다.
- route_gap_q50이 full-history 운영 후보라면, residual_down은 저이력 안정성 중심의 보수 대안이다.

최종 리포트 권장안은 route_gap_q50을 1순위로 둔다. 다만 API 반영 전 마지막 acceptance gate에서는 k=1 구간을 current 유지로 둘지 함께 검토한다.

## 11. 권장 구현안

### 11.1 라우팅 정책

```text
1. 작가 매칭 결과와 같은 작가 가격 이력 수를 확인한다.

2. 같은 작가 가격 이력이 0건이면 Cold로 보낸다.

3. 같은 작가 가격 이력이 1건 이상이면 Warm-lite unified로 보낸다.

4. Warm-lite unified 안에서:
   gap_log = abs(q50_full_log - q50_lean_log)

   if gap_log >= 0.0252975:
       final_log = qavg_log + clip(1.00 * LightGBM_Huber_residual_log, -0.15, +0.15)
   else:
       final_log = qavg_log + clip(0.50 * LightGBM_Huber_residual_log, -0.10, +0.10)

5. 최종 가격:
   final_price_krw = exp(final_log)
```

### 11.2 k=1 보수 옵션

k=1 stress에서는 route_gap_q50이 current보다 불리했다. 따라서 API 반영 시 아래 보수 옵션을 검토할 수 있다.

```text
if same_artist_history_n == 1:
    Warm-lite current
else:
    route_gap_q50
```

이 옵션은 k=1 안정성을 우선할 때 사용한다. 다만 full-history 607건 기준의 route_gap_q50 test 성능은 위 옵션 없이 계산된 값이다.

## 12. 기존 0.1v API와의 차이

| 항목 | 현재 0.1v API 구현 | 새 권장안 |
|---|---|---|
| Warm 경로 | 매칭점수 0.80 이상 + 이력 5건 이상 | 기본 라우팅에서 제거 후보 |
| Warm-lite 경로 | 매칭점수 0.80 이상 + 이력 1~4건 | 이력 1건 이상 전체로 확장 |
| Cold 경로 | 이력 0건, 매칭 실패, 검수 필요 | 유지 |
| Warm-lite 보정 | current 보정 | current + 조건부 CF7 tail guard |
| tail guard | 없음 | full/lean q50 gap 기준으로 조건부 적용 |

새 권장안은 현재 0.1v API 동작과 동일하지 않다. API 반영 전에는 번들 동결, API parity, 모니터링 기준 업데이트가 필요하다.

## 13. 운영 모니터링 기준

권장안 반영 시 최소한 아래 항목을 모니터링한다.

| 항목 | 확인 내용 | 경고 기준 예시 |
|---|---|---|
| route share | Warm-lite 중 CF7 tail guard가 켜지는 비율 | validation/test 기준 50~57%에서 크게 벗어나면 점검 |
| k=1 구간 성능 | 이력 1건 작가에서 route가 current보다 악화되는지 | k=1 MAPE/RMSE 악화 지속 시 current 강제 |
| p95 APE | tail 개선이 유지되는지 | current 대비 p95 개선폭이 사라지면 점검 |
| RMSE log | 로그가격 큰 오차가 줄어드는지 | current 대비 RMSE 악화 시 점검 |
| residual 방향 | 양수/음수 residual에서 각각 성능이 어떻게 달라지는지 | 양수 방향에서 과보정 발생 시 residual_down 대안 검토 |
| 작가 매칭 신뢰도 | 동명이인/오매칭이 라우팅에 섞이는지 | 매칭 신뢰도 0.80 미만 또는 충돌 정보 존재 시 Cold/검수대기 |

## 14. 남은 작업

최종 API 반영 전 필요한 작업은 아래다.

| 단계 | 필요 작업 | 목적 |
|---|---|---|
| 1 | Warm-lite unified + route_gap_q50 번들 동결 | 실험 코드를 운영 artifact로 고정 |
| 2 | API adapter 연결 | 0.1v 또는 차기 API에서 같은 계산이 나오게 연결 |
| 3 | parity 검증 | 실험 산출값과 API 응답 로그가격 차이 확인 |
| 4 | k=1 보수 옵션 검토 | 저이력 1건 구간에서 current 유지 여부 결정 |
| 5 | 문서/발표자료 갱신 | 기존 Warm/Warm-lite/Cold 3분기 설명을 새 권장안으로 정리 |

## 15. 최종 판단

최종 권장안은 다음과 같다.

```text
Cold:
  same_artist_history_n == 0

Warm-lite unified current:
  same_artist_history_n >= 1
  AND abs(q50_full_log - q50_lean_log) < 0.0252975

Warm-lite CF7 tail guard:
  same_artist_history_n >= 1
  AND abs(q50_full_log - q50_lean_log) >= 0.0252975
```

이 구조는 기존 `Warm / Warm-lite / Cold` 3분기보다 단순하다.

```text
기존: 5건 이상 Warm, 1~4건 Warm-lite, 0건 Cold
권장: 1건 이상 Warm-lite unified, 0건 Cold
```

단, Warm-lite unified 내부에서는 current와 CF7 tail guard를 조건부로 나눠 중앙값 정확도와 tail 안정성을 함께 관리한다.

현재 실험 기준으로 가장 균형 잡힌 선택은 `route_gap_q50`이며, 저이력 1건 구간 보수 운영이 필요하면 `same_artist_history_n == 1`에서 current를 유지하는 옵션을 추가 검토한다.

## 16. 근거 파일

| 근거 | 파일 |
|---|---|
| 기존 종합 리포트 | `docs/track6/experiments/partner_warm_cold_best_model_report.html` |
| CF5 Warm-lite unified operational comparison | `experiments/track6/PP-ROUTE-CF5_unified_warm_lite_operational_comparison/reports/result_report.md` |
| CF6 full-history retrained comparison | `experiments/track6/PP-ROUTE-CF6_full_history_retrained_warm_vs_unified_warm_lite/reports/result_report.md` |
| CF7 tail guard 실험 | `experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard/reports/result_report.md` |
| CF8 CF7 후보 bootstrap/k stress/segment 검증 | `experiments/track6/PP-ROUTE-CF8_cf7_candidate_validation/reports/result_report.md` |
| Q6 Warm-lite native 정확 검증 | `experiments/track6/PP-WLITE-Q6_cf7_candidate_native_validation/reports/result_report.md` |
| CF9 조건부 CF7 라우터 | `experiments/track6/PP-ROUTE-CF9_conditional_cf7_router/reports/result_report.md` |
