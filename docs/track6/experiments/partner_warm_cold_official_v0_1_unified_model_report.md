# Official 0.1v Warm/Cold 최종 가격 예측 모델 리포트

- 작성일: 2026-06-17
- 보고 목적: 새로 승격한 official 0.1v 기본 모델 기준으로 Warm/Cold 가격 예측 구조, 피처, 산식, 검증 근거를 설명
- 기준 API 표기: `0.1v API`
- 현재 기본 Warm 정책: `1건 이상 -> Warm-lite unified route_gap_q50`
- Cold 정책: 같은 작가 가격 이력을 직접 쓰지 못하는 입력은 Cold 검색/방어 모델로 처리

## 1. 결론 요약

> **핵심 결론:** 현재 official 0.1v 기본 운영 모델은 예전의 `1~4건 Warm-lite, 5건 이상 Warm WMIN8` split 정책이 아니다.
 기본값은 `작가 매칭이 신뢰 가능하고 같은 작가 가격 이력이 1건 이상이면 Warm-lite unified route_gap_q50`를 사용한다.
 같은 작가 가격 이력이 없거나 작가 매칭이 신뢰 기준을 통과하지 못하면 Cold 또는 검수 경로로 보낸다.

| 구분 | 현재 기본 정책 | 설명 |
|---|---|---|
| Warm 경로 | `same_artist_training_price_count >= 1` | 같은 작가 가격 이력이 1건 이상이면 unified Warm-lite route_gap_q50 predictor를 사용한다. |
| Cold 경로 | 신뢰 가능한 작가 매칭이 없거나 사용 가능한 같은 작가 가격 이력이 0건 | 같은 작가 가격 이력을 기준가로 직접 쓰지 못하므로 작품 조건, 작가 메타, 검색 피처, 방어/신뢰도 정책을 사용한다. |
| Rollback | `PRICE_PREDICTION_OFFICIAL_V01_WARM_ROUTE_POLICY=current_split` | 필요하면 예전 split 정책인 `1~4건 Warm-lite current, 5건 이상 Warm WMIN8`로 되돌릴 수 있다. |

## 2. 문서 읽는 법과 용어

| 용어 | 의미 |
|---|---|
| `n` | 학습 작품 수가 아니라 성능 지표를 계산한 평가 행 수다. |
| 로그가격 | 가격에 자연로그를 취한 값이다. 고가 작품이 오차 지표를 과도하게 흔드는 것을 줄인다. |
| Quantile 예측 | 하나의 가격만 예측하지 않고 낮은 쪽, 중앙, 높은 쪽 가격을 함께 예측하는 방식이다. |
| 예측의 불확실성 폭 | `q90_log - q10_log`. 모델이 가능한 가격 범위를 얼마나 넓게 보고 있는지 나타낸다. |
| `clip(x, low, high)` | `x`가 하한보다 작으면 하한, 상한보다 크면 상한으로 자르는 함수다. 과도한 보정을 막기 위해 사용한다. |
| OOF / out-of-fold | 해당 row를 학습하지 않은 fold에서 나온 예측값이다. 자기 가격을 외우는 누수를 줄인다. |
| Frozen lookup | 실시간으로 새로 계산하지 않고, 검증된 파일에 고정해 둔 조회표다. |

## 3. 현재 라우팅 구조

```text
[작품 입력]
  - 작가명 또는 selected_artist_key
  - 작품 크기, 매체, 지지체
        |
        v
[작가 매칭 신뢰도 판단]
  - artist_match_score >= 0.80 이면 신뢰 가능한 작가 매칭
  - 동명이인/핵심 정보 충돌이 크면 review_required
        |
        v
[같은 작가 가격 이력 수 확인]
  - 같은 작가 가격 이력 1건 이상: Warm 경로
  - 같은 작가 가격 이력 0건 또는 매칭 미달: Cold 또는 검수 경로
        |
        v
[Warm]
  - Warm-lite unified route_gap_q50 predictor
  - current 후보와 CF7 방어 후보 중 조건부 선택

[Cold]
  - 작품 조건 + 작가 메타 + 검색 피처 기반 Cold guard+search
  - v0.4 confidence/display policy 적용
```

현재 service DB의 `artist_registry`는 등록 작가 기준 `valid_price_count` 최소값이 1이다. 따라서 `selected_artist_key` 기반 등록 작가 0건 샘플은 현재 DB에서 구성되지 않았다. 미등록 작가명은 가격 모델 이전에 작가 확인이 필요하므로 `review_required`로 빠질 수 있다.

## 4. 성능 기준 요약

| 경로 | 평가 기준 | n | MdAPE | MAPE | p95 APE | RMSE log | 해석 |
|---|---|---|---|---|---|---|---|
| Warm 기본값 | CF9 fixed test | 607 | 0.086405 | 0.223590 | 0.758056 | 0.380030 | 현재 기본 Warm 라우팅 후보인 route_gap_q50의 test split 성능 |
| Warm 기본값 | CF9 validation | 519 | 0.079075 | 0.167521 | 0.560746 | 0.298469 | route_gap_q50 후보 선택과 검증에 사용된 validation split 성능 |
| Cold 점예측 | fixed test | 3,099 | 0.409820 | 0.849260 | 2.346465 | 비교값 없음 | Cold 최고 성능 연구 기준인 v0.3 guard+search 점예측 |

- Warm과 Cold는 입력 조건이 다르므로 성능 숫자를 단순 순위로 비교하면 안 된다.
- Warm은 같은 작가 가격 이력을 직접 사용할 수 있는 경로다.
- Cold는 같은 작가 가격 이력을 직접 기준가로 쓰지 못하므로 절대 난이도가 훨씬 높다.
- Cold의 RMSE log는 같은 조건의 보조 비교값이 없으므로 이 표에서는 제외한다.

## 5. Warm 경로 상세

### 5.1 목적

현재 Warm 경로는 작가가 신뢰도 높게 매칭되고 같은 작가 가격 이력이 1건 이상 있을 때 사용한다. 예전 구조처럼 1~4건과 5건 이상을 서로 다른 운영 모델로 나누지 않고, `Warm-lite unified route_gap_q50` predictor가 전체 1건 이상 구간을 처리한다.

목표는 두 가지다.

- 같은 작가 가격 이력을 쓰되, 이력이 적은 작가와 많은 작가를 하나의 통합 방식으로 처리한다.
- 중앙값 정확도만 보지 않고 MAPE와 p95 큰 오차를 줄이기 위해 조건부 tail guard를 적용한다.

### 5.2 학습 단계

```text
[학습 데이터 구성]
  - 실제 로그가격이 있는 warm scope train 데이터
  - train rows: 26,914
  - train artists: 1,773
        |
        v
[같은 작가 이력 통계 생성]
  - 작가 + 매체/지지체 + 크기 구간
  - 없으면 작가 + 크기 구간
  - 없으면 작가 전체
  - 통계 생성 실패 시 global fallback 사용
        |
        v
[피처 생성]
  - 작품 크기/면적/비율/입체 여부
  - 매체/지지체/크기 bucket
  - 작가 이력 가격 통계
  - 작가 이력 표본 수와 matching level
        |
        v
[LightGBM Quantile 모델 학습]
  - full q10/q50/q90 모델
  - lean q50 모델
  - seed: 20260612, 20260613, 20260614
        |
        v
[LightGBM Huber residual 모델 학습]
  - Quantile 평균 기준가격에서 남은 잔차를 학습
        |
        v
[route_gap_q50 후보 선택]
  - full q50과 lean q50 차이가 큰 row는 CF7 방어 후보로 전환
  - threshold는 validation에서 선택한 0.0252975144340901
        |
        v
[동결 산출물]
  - 모델 파일
  - 파라미터 JSON
  - fixed replay feature store
  - predictor
```

### 5.3 사용 단계

```text
[새 작품 입력]
  - 작가 key 또는 작가명
  - 작품 크기/매체/지지체
        |
        v
[같은 작가 가격 이력 조회]
  - 사용 가능한 이력 1건 이상이면 Warm 경로
        |
        v
[같은 작가 이력 통계 생성]
  - 학습 때 동결한 사다리 규칙으로 통계 생성
        |
        v
[Quantile 예측]
  - full q10/q50/q90
  - lean q50
  - qavg = full q50과 lean q50 중심값의 평균 계열
        |
        v
[current 후보 계산]
  - qavg + clip(0.50 * Huber residual, -0.10, +0.10)
        |
        v
[CF7 방어 후보 계산]
  - qavg + clip(1.00 * seed_mean(Huber residual), -0.15, +0.15)
        |
        v
[route_gap_q50 라우팅]
  - seed_mean(abs(full_q50 - lean_q50)) >= 0.0252975144340901 이면 CF7 방어 후보
  - 아니면 current 후보
        |
        v
[최종 Warm 가격]
  - exp(최종 Warm 로그가격)
```

### 5.4 피처와 로직

| 피처 그룹 | 예시 | 사용 이유 |
|---|---|---|
| 작품 크기 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `aspect_ratio` | 작품의 물리적 규모와 형태가 가격 기준을 크게 좌우한다. |
| 작품 유형 | `medium_category`, `support_category`, `medium_support_bucket` | 회화, 조각, 종이, 캔버스 등 재료/지지체 차이를 반영한다. |
| 크기 bucket | `size_bucket`, `support_size_bucket` | 작품 크기의 연속값을 가격대별 구간 효과로 안정화한다. |
| 같은 작가 이력 통계 | 작가 로그가격 중앙값, q25/q75, IQR, 면적단가 중앙값, 표본 수 | 같은 작가의 기존 가격대와 변동성을 기준가격에 반영한다. |
| Quantile 피처 | `q10_log`, `q50_log`, `q90_log`, `q90_log - q10_log` | 중심 가격과 예측 불확실성을 함께 만든다. |
| Residual 피처 | Quantile 기준가격, 작품 피처, 작가 이력 통계 | 기준가격에서 남은 오차를 제한적으로 보정한다. |

### 5.5 route_gap_q50 라우터

`route_gap_q50`는 가격을 직접 임의로 깎는 규칙이 아니다. 먼저 두 후보 가격을 계산한 뒤, 두 Quantile 중심 예측이 얼마나 불일치하는지 보고 방어 후보를 쓸지 결정한다.

```text
gap_log =
  seed_mean(abs(full_q50_log - lean_q50_log))

if gap_log >= 0.0252975144340901:
  최종 Warm 로그가격 = CF7 방어 후보
else:
  최종 Warm 로그가격 = current 후보
```

> **해석:** full q50과 lean q50이 거의 같으면 모델이 중심 가격에 대해 비교적 안정적으로 보고 있으므로 current 후보를 유지한다.
 두 q50이 벌어지면 피처를 넓게 쓴 모델과 흔들림을 줄인 모델의 판단이 갈린 것이므로, MAPE/p95 방어 성격의 CF7 후보를 사용한다.

### 5.6 검증 근거

| 검증 | 결과 | 판단 |
|---|---|---|
| CF9 fixed test | 607행, MdAPE 0.086405, MAPE 0.223590, p95 0.758056 | Warm WMIN8보다 MdAPE/MAPE 우세, Warm-lite current보다 p95 방어 개선 |
| CF9 validation | 519행, MdAPE 0.079075, MAPE 0.167521, p95 0.560746 | route_gap_q50 후보 선택과 검증에 사용 |
| Bundle replay parity | 1,126행, max abs log diff 5.329070518200751e-15, route mismatch 0 | 실험 CSV 산출물을 동결 predictor가 row-level 재현 |
| HTTP API parity | 1,126행, API-direct log diff 0.0, direct-CF9 diff 5.329070518200751e-15 | official 0.1v endpoint와 동결 predictor가 일치 |
| Deterministic check | 등록 작가 1건/4건/5건 모두 warm_lite, report adapter, deterministic true | 현재 기본 라우팅이 1건 이상 통합 Warm 경로로 고정됨 |

## 6. Cold 경로 상세

### 6.1 목적

Cold 경로는 같은 작가 가격 이력을 직접 기준가격으로 쓸 수 없는 경우를 위한 가격 예측 경로다. Warm처럼 작가별 실제 가격 이력을 직접 쓰지 못하므로, 작품 자체 정보, 작가 메타, 작가명 검색 피처, 예측 불확실성 방어, 신뢰도 표시 정책을 함께 사용한다.

현재 Cold 설명은 두 층으로 분리한다.

- 점예측 가격: `cold_prediction_v0.3`의 guard+search 경로
- 운영 표시/신뢰도 정책: `cold_prediction_v0.4` confidence/display policy

### 6.2 학습 단계

```text
[Cold 학습 데이터 구성]
  - 같은 작가 가격 이력을 직접 쓰지 않는 fixed test/validation 구성
  - 작품 크기, 매체, 지지체, 작가 메타, 검색 피처 결합
        |
        v
[검색 피처 포함 LightGBM Quantile 학습]
  - 낮은 분위, 중앙 분위, 높은 분위 예측
  - 검색 피처와 작가 메타가 포함된 대표 로그가격 생성
        |
        v
[예측구간폭 기반 안정화]
  - q90 - q10으로 예측 불확실성 폭 계산
  - 예측구간폭 구간별 OOF 잔차 중앙값 보정
        |
        v
[과대예측 방어 guard 검증]
  - qwidth 임계값과 gap 임계값을 validation에서 고정
  - 위험 row는 LightGBM 40분위 로그가격 쪽으로 50% 낮춤
        |
        v
[작가 검색 보정 frozen lookup 생성]
  - 갤러리/미술관 문맥 기반 작가별 search delta 저장
        |
        v
[v0.4 표시 정책 동결]
  - confidence tier
  - review flag
  - 미커버 작가 fallback delta
```

### 6.3 사용 단계

```text
[Cold 입력]
  - 작품 크기/매체/지지체
  - 작가명 또는 작가 key
  - 작가 메타와 검색 캐시
        |
        v
[검색포함 대표 로그가격]
  - LightGBM Quantile 중앙값 기반
  - 예측구간폭 구간별 잔차 보정 적용
        |
        v
[과대예측 방어]
  - qwidth가 넓고 대표 로그가격이 q40보다 높게 튀면
    대표 로그가격을 q40 쪽으로 50% 이동
        |
        v
[작가 검색 보정]
  - frozen lookup에 작가별 delta가 있으면 더함
  - 없으면 0 또는 v0.4 fallback 정책 적용
        |
        v
[최종 Cold 로그가격]
        |
        v
[최종 Cold 가격 = exp(최종 로그가격)]
        |
        v
[신뢰도/표시 정책]
  - high/medium/low tier
  - 검수 권장 flag
  - 가격 범위 표시
```

### 6.4 피처와 로직

| 피처 그룹 | 예시 | 역할 |
|---|---|---|
| 작품 피처 | `width_cm`, `height_cm`, `area_cm2`, `log_area`, `aspect_ratio` | 작품의 물리적 규모와 형태를 설명한다. |
| 매체/지지체 | `medium_category`, `support_category`, `support_size_bucket` | 재료와 지지체별 가격 차이를 반영한다. |
| 작가 메타 | 생년, 활동단계, 국적, 전체 작품 수, 판매 중 작품 수, 팔로워 수 | 같은 작가 가격 이력 대신 작가의 공개 시장 신호를 보조로 사용한다. |
| 검색 피처 | 검색 결과 수, 미술 문맥, 전시 문맥, 갤러리/미술관 문맥, 동명이인 위험, 검색 품질 | 작가의 검색 문맥과 시장 노출 신호를 가격 보정에 사용한다. |
| Quantile 피처 | q10/q50/q90, qwidth | 기준 가격과 불확실성 폭을 만든다. |
| Guard 피처 | qwidth, 대표 로그가격과 q40 로그가격의 gap | 대표값이 높게 튀는 row를 보수 분위 쪽으로 낮춘다. |

```text
검색포함_대표로그가격
  = 검색기반_중앙분위_로그가격
  + clip(예측구간폭_구간별_잔차중앙값, -0.25, +0.25)

방어조건 =
  예측구간폭 >= 1.4612207078910142
  AND 검색포함_대표로그가격 - LightGBM_40분위_로그가격 >= 0.07715547281151025
  AND LightGBM_40분위_로그가격 < 검색포함_대표로그가격

과대예측방어_로그가격 =
  if 방어조건:
    0.50 * 검색포함_대표로그가격 + 0.50 * LightGBM_40분위_로그가격
  else:
    검색포함_대표로그가격

최종_Cold_로그가격 =
  과대예측방어_로그가격 + 작가검색보정_로그값

최종_Cold_가격_KRW = exp(최종_Cold_로그가격)
```

### 6.5 신뢰도/표시 정책

`cold_prediction_v0.4`는 점예측을 새로 바꾸는 모델이 아니라, v0.3 점예측 위에 신뢰도와 표시 정책을 얹는 레이어다.

| 항목 | 값 또는 규칙 | 의미 |
|---|---|---|
| high tier | `qwidth <= 0.7349424254094605` AND `model_gap <= 0.15320873993739603` AND 검색 커버 | 불확실성 폭과 모델 간 gap이 작고 검색 커버가 있는 안정 구간 |
| low tier | `qwidth >= 2.1572852836013667` OR `model_gap >= 0.42534619182266353` | 가격 범위가 넓거나 모델 간 차이가 큰 저신뢰 구간 |
| review flag | `qwidth >= 1.4612207078910142` OR 검색 미커버 | 검수 또는 주의 표시가 필요한 구간 |
| 미커버 fallback | `delta = -0.03129536658906122`, cap 0.2 | 검색 미커버 작가의 p95 방어 목적. 기본 활성화. |

### 6.6 검증 근거

| 단계 | MdAPE | MAPE | p95 APE | 해석 |
|---|---|---|---|---|
| 검색포함 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 | 검색 피처 포함 LightGBM Quantile 기반 대표값 |
| 과대예측 방어 로그가격 | 0.417765 | 0.963963 | 2.537708 | qwidth/gap 조건에서 보수 분위 쪽으로 낮춘 값 |
| 최종 검색보정 로그가격 | 0.409820 | 0.849260 | 2.346465 | guard + search delta를 합친 최고 성능 점예측 |

| 재현 검증 항목 | 값 |
|---|---|
| test row 수 | 3,099 |
| validation row 수 | 2,753 |
| 검색 lookup 작가 수 | 372 |
| test 검색 커버리지 | 1.000000 |
| 후처리기와 독립 계산식의 로그가격 최대 차이 | 0.000e+00 |
| frozen lookup delta와 원천 delta의 test 최대 차이 | 2.665e-15 |
| 전체 재현 통과 여부 | true |

## 7. Warm/Cold 비교

| 항목 | Warm | Cold |
|---|---|---|
| 적용 조건 | 신뢰 가능한 작가 매칭 + 같은 작가 가격 이력 1건 이상 | 같은 작가 가격 이력을 직접 쓰지 못하거나 작가 매칭 신뢰가 부족한 경우 |
| 핵심 기준 | 같은 작가 가격 이력 통계 + Quantile/Huber residual | 작품 조건 + 작가 메타 + 검색 피처 + guard/search 보정 |
| 주요 불확실성 처리 | full q50과 lean q50의 gap으로 CF7 방어 후보 조건부 선택 | qwidth/gap 조건으로 과대예측 방어, confidence tier와 review flag 표시 |
| 출력 | 단일 최종 Warm 가격과 계산 근거 | Cold 가격, 가격 범위, 신뢰도/검수 표시 |
| 주의 | 이전 WMIN8 split 정책과 혼동하지 않음 | Cold는 Warm보다 절대 난이도가 높아 성능 숫자를 직접 비교하지 않음 |

## 8. 데이터 추가 수집을 통한 개선 가능성

Warm·Cold 모두 현재 모델 구조는 성숙 단계에 있고, 남은 개선 레버는 데이터다. 단 두 경로가 필요로 하는 데이터의 **종류가 다르다**. 아래는 학습곡선 실험으로 확인한 결과다.

> **한 줄 요약:** Warm은 **같은 작가의 가격 데이터**가 쌓이면 좋아지고(입증됨), Cold는 작품을 더 모으는 게 아니라 **신규 작가의 프로필 메타(생년·경력·작품수·전시 이력 등)**를 채워야 좋아진다.

### 8.1 Warm — 가격 데이터가 늘면 정확도가 오른다 (입증됨)

fixed test split은 고정하고 Warm 학습 데이터만 25→100%로 늘린 학습곡선(동일 cohort, PP-ROUTE-CF12). 평가 대상이 바뀐 게 아니라 순수 학습 데이터 증가 효과다.

| 학습 비율 | 학습 작가 | MdAPE | MAPE | p95 APE |
|---|---|---|---|---|
| 25% | 443 | 0.1533 | 0.3636 | 0.990 |
| 50% | 886 | 0.1142 | 0.2563 | 0.908 |
| 75% | 1,330 | 0.1024 | 0.2345 | 0.816 |
| 100% | 1,773 | 0.0886 | 0.2296 | 0.806 |

- 25%→100%에서 **MdAPE −44%**(0.153→0.089), MAPE −0.134, p95 −0.184. 아직 포화하지 않았다.
- 즉 품질 검수(가격 라벨·작가 매칭·작품 피처)를 통과한 가격 데이터가 더 쌓이면 Warm은 계속 좋아질 근거가 있다.

### 8.2 Cold — 작품이 아니라 "작가 메타"를 채워야 한다 (PP-CDATA1/2)

Cold는 처음 보는 작가 예측이라, 같은 cold 작가에 가격을 더 주면 그 작가는 Warm이 된다. 따라서 질문은 "학습 작가/작품을 늘리면 *처음 보는* cold 작가가 좋아지는가"이다. cold test(3,099행/200작가, train과 작가 완전 분리)를 고정하고 학습 데이터를 늘려 측정했다.

| 늘린 데이터 / 신호 | MdAPE 변화 | 해석 |
|---|---|---|
| 작품 피처만, 학습 작가 25→100% | 0.50 → 0.50 (평평) | 작품 데이터만 늘려선 **효과 없음** |
| +작가 메타, 학습 작가 25→100% | 0.496 → 0.471 (−5%) | 메타가 있으면 데이터에 따라 개선·스케일 |
| +작가 메타, 작가당 작품수 1→all | 0.513 → 0.467 (−9%) | 작품 깊이도 메타가 있을 때만 약간 도움 |
| **작가 메타 완성도: 빈약 → 풍부** | **0.497 → 0.348 (−30%)** | **압도적 레버** — 메타를 충분히 채운 작가가 30% 정확 |

- 메타 완성도별 cold test: 빈약(0~2개) MdAPE 0.497 / 보통(3~4개) 0.580 / **풍부(5~6개) 0.348**. 메타는 *충분히* 채워야 효과가 난다(어중간하면 오히려 tail 악화).
- 피처 중요도에서 **작가 메타가 전체의 54%**를 차지(1위 총 작품 수, 2위 경력 단계). 즉 cold 작가의 가격 수준을 추정할 유일한 사전 신호다.
- 반대로 작품 이미지·크기·매체만 더 모으는 것은 Cold 개선에 도움이 되지 않는다.

### 8.3 수집해야 할 로우데이터 (우선순위)

| 우선 | 수집 항목 (로우데이터) | 소스 예시 | 현재 커버리지 |
|---|---|---|---|
| 1 | 작가 총 작품 수 / 활동량 | 작가 프로필·갤러리 등록 | 74% |
| 2 | 경력 단계 / 데뷔 시점 | 작가 CV·약력 | 52% |
| 3 | 팔로워 / 인지도 | Instagram·Artsy 등 | 69% |
| 4 | 전시 이력 (개인전·단체전·아트페어 횟수) | 작가 CV·전시 DB | 37% ⚠ |
| 5 | 생년 | 작가 약력 | 25% ⚠ |
| 6 | 소속·전시 갤러리 등급 | 갤러리 정보 | 56% |
| — | (궁극) 작가의 첫 판매·거래 가격 | 거래 기록 → Warm 전환 | — |

- **즉시 효과 큰 보강 = 생년(현재 25%)·전시 이력(현재 37%)** — 가장 비어 있으면서 중요도도 높다.
- 가장 큰 개선은 그 작가의 **첫 가격 데이터**를 수집해 Cold→Warm으로 전환되는 것이다(이때 §8.1의 Warm 개선 효과가 적용된다).
- 근거: `experiments/track6/PP-CDATA1_cold_data_growth_learning_curve/` (학습곡선·메타 완성도·breadth/depth), Warm은 `PP-ROUTE-CF12_warm_unified_learning_curve`.

> **측정 한계:** Cold 메타 완성도 tier는 관측 분할이라 "메타 풍부 작가가 본질적으로 쉬운 작가"일 가능성(선택 bias)을 완전히 배제하진 못한다. "개선 상한 근사치"로 해석한다. 다만 메타를 피처로 넣었을 때 일관되게 개선하고 중요도 54%인 점이 인과 방향을 뒷받침한다.

## 9. 재현 가능성과 운영 확인

| 구분 | 파일 또는 명령 | 결과 |
|---|---|---|
| Warm bundle manifest | `shasum -c models/track6/warm_lite_unified_route_gap_q50_v0.1_candidate/manifest/MANIFEST.sha256` | 전체 OK |
| Warm bundle replay parity | `scripts/track6/verify_warm_lite_unified_route_gap_q50_bundle_parity.py` | 1,126행 passed true |
| Warm HTTP API parity | `scripts/track6/verify_official_v0_1_warm_lite_unified_route_gap_q50_api_parity.py --split both` | 1,126행 passed true |
| Cold v0.3 reproducibility | `scripts/track6/verify_cold_best_research_reproducibility.py` | 전체 재현 통과 |
| Cold v0.4 confidence policy | `models/track6/cold_prediction_v0.4` | tier mismatch 0행, review flag mismatch 0행 |

> **문서상 주의:** 내부 artifact 이름에 `v0.2`, `v0.3`, `v0.4`가 들어가더라도 API 버전은 `0.1v API`다.
 이 문서에서 `0.1v`는 외부 API 기준이고, Cold의 v0.x는 내부 모델 artifact 버전명이다.

## 10. 내부 추적 정보

| 문서용 이름 | 내부 추적 ID / 파일 | 역할 |
|---|---|---|
| 현재 Warm 기본 모델 | `warm_lite_unified_route_gap_q50_v0.1_candidate` | 1건 이상 같은 작가 이력용 unified Warm predictor |
| Warm route_gap 후보 | `PP-ROUTE-CF9_conditional_cf7_router` | current 후보와 CF7 방어 후보를 gap 조건으로 선택 |
| Warm bundle parity | `PP-ROUTE-CF10_unified_route_gap_q50_bundle_parity` | 동결 predictor가 CF9 산출물을 재현하는지 검증 |
| Warm API parity | `PP-ROUTE-CF11_unified_route_gap_q50_api_parity` | official 0.1v HTTP API와 동결 predictor 일치 검증 |
| Cold 점예측 | `cold_prediction_v0.3 guard+search` | 검색 피처 포함 Cold 최고 성능 점예측 |
| Cold 표시 정책 | `cold_prediction_v0.4 confidence/display policy` | 신뢰도 tier, review flag, 미커버 fallback 표시 정책 |

## 11. 최종 설명 문장

```text
현재 official 0.1v 가격 예측은 작가 매칭과 같은 작가 가격 이력 수로 Warm과 Cold를 나눈다.
작가가 신뢰도 높게 매칭되고 같은 작가 가격 이력이 1건 이상이면 Warm-lite unified route_gap_q50 모델을 사용한다.
이 모델은 같은 작가 이력 통계와 작품 피처로 Quantile 중심 가격을 만들고, Huber residual로 제한 보정한 뒤,
full q50과 lean q50의 차이가 클 때만 CF7 방어 후보를 선택한다.

같은 작가 가격 이력을 직접 쓰기 어렵거나 작가 매칭이 불확실하면 Cold 경로를 사용한다.
Cold는 작품 크기, 매체, 지지체, 작가 메타, 검색 피처를 사용해 LightGBM Quantile 기준가격을 만들고,
예측구간폭과 gap이 큰 경우 보수 분위 가격 쪽으로 낮춘다.
마지막으로 작가 검색 보정 lookup과 v0.4 신뢰도/표시 정책을 적용한다.
```
