# K-Auction 가격 예측 엔진 기획서 (상세)

> **문서 버전**: v2.0
> **작성일**: 2026-03-26
> **리뷰 방식**: GitHub PR → Claude(아키텍처) + Codex(검증/보완) 듀얼 인라인 리뷰
> **관련 문서**: `art_price_prediction_research.md`, `price_prediction_system_spec.md`, `data_feature_mapping.md`, `implementation_strategy.md`

---

## 0. 문서 목적과 읽는 법

이 문서는 **K-Auction 경매 데이터 기반 가격 예측 엔진**의 전체 설계를 담고 있다.
엔진이 "왜 이렇게 동작하는지"를 누구나 이해할 수 있도록, 각 단계마다 **수학 공식 → 구현 로직 → 논문 근거**를 명시한다.

```
문서 구조:
  1장 — 현재 상태 (데이터 + 기존 모델 성능)
  2장 — 수학적 기반 (예측 공식의 이론적 근거)
  3장 — 피처 엔지니어링 (입력 변수 설계 + 변환 공식)
  4장 — 모델 학습 (학습 절차 + 하이퍼파라미터)
  5장 — 예측 파이프라인 (입력 → 출력 전체 흐름)
  6장 — 평가 체계 (성과지표 공식 + 해석법)
  7장 — 엔진 테스트 페이지 (별도 HTML로 작동 확인)
  8장 — 리스크 & 완화
  9장 — 마일스톤
  10장 — Codex 리뷰 가이드
```

---

## 1. 현재 상태 요약

### 1.1 보유 데이터

| 항목 | 규모 | 위치 |
|------|------|------|
| 작품 낙찰 데이터 | 43,866건 (전량 낙찰) | `data/k-auction-works-20260325.csv` |
| 작가 통계 | 3,286명 | `data/k-auction-artists-20260325.csv` |
| 경매 타입 | 위클리 28,554 / 프리미엄 8,485 / 메이저 6,827 | — |

### 1.2 가격 분포 특성

```
가격대별 분포:
  <100만          15,828건 (36.1%)   → 극저가, 변동성 극대
  100만~500만     16,554건 (37.7%)   → 최다 구간
  500만~3000만     8,094건 (18.4%)
  3000만~1억       2,485건 ( 5.7%)
  1억~10억           875건 ( 2.0%)
  10억+               30건 ( 0.1%)   → 극소수 초고가

  핵심: 73.8%가 500만 원 이하, 상위 2.1%가 1억 원 이상
  → 극단적 우편향(right-skewed) → log 변환 필수
```

### 1.3 Baseline 모델 성능 (이미 확보)

| 세그먼트 | MAPE | MdAPE | R² | ±20% 이내 | ±30% 이내 | 건수 |
|----------|------|-------|-----|----------|----------|------|
| **전체** | **40.17%** | 26.75% | 0.902 | 40.1% | 54.0% | 6,582 |
| 메이저 | **20.58%** | 15.84% | 0.931 | 59.1% | 75.5% | 1,025 |
| 프리미엄 | **32.93%** | 23.61% | 0.791 | 44.1% | 60.8% | 1,273 |
| 위클리 | **47.02%** | 32.72% | 0.571 | 34.4% | 46.8% | 4,284 |
| 3000만~1억 | **14.82%** | 10.80% | 0.428 | 73.1% | 87.0% | 353 |
| 1억+ | **20.82%** | 18.25% | 0.785 | 54.1% | 74.0% | 146 |

### 1.4 피처 기여도 (Ablation 실측)

```
실측 기여도:                          명세서 예상 → 실측
  추정가 관련:  68.28%                  32% → 68%  (2배 이상 중요)
  작가 관련:    14.40%                  31% → 14%  (예상 절반)
  경매 관련:    10.15%                  —
  물리적 속성:   4.08%                   9% → 4%   (추정가에 내포)
  기타:          3.09%

  → 추정가가 "절대적 앵커" (제거 시 MAPE +11.85%p 상승)
  → 크기는 제거해도 MAPE 변화 없음 (-0.02%p)
```

---

## 2. 수학적 기반: 예측 공식의 이론적 근거

### 2.1 문제 정의 프레임: 헤도닉 가격 모델

헤도닉 가격 모델은 미술품 가격을 관찰 가능한 특성들의 함수로 분해하는 **경제학적 문제 정의 프레임워크**다.
본 엔진에서는 이 프레임을 "가격이 특성의 함수다"라는 문제 정의로 채택하되, 함수의 구체적 형태는 ML 모델(CatBoost)이 데이터에서 학습한다.

**헤도닉 모델의 선형 공식** (참조용):
```
ln(P_i) = α + Σ_{j=1}^{J} β_j · X_{ij} + Σ_{t=1}^{T} γ_t · D_{it} + ε_i

  P_i       : 작품 i의 낙찰가 (원)
  X_{ij}    : 작품 i의 j번째 특성 (크기, 매체, 작가 통계 등)
  D_{it}    : 시간 더미 변수 (시장 트렌드 반영)
  β_j       : 특성 j의 암묵 가격 (implicit price)
  γ_t       : 시점 t의 시장 가격 지수
  ε_i       : 오차항 (분포는 데이터에서 검증 필요 — 정규성 가정하지 않음)
```

**왜 ln(P)인가?**
1. 미술품 가격은 극단적 우편향 → log 변환으로 분포 대칭화
2. 계수 β_j의 해석:
   - 근사식: β_j가 작을 때 "X가 1단위 증가 시 가격이 약 β_j × 100% 변화"
   - **정확식: 가격 변화율 = 100 · (exp(β_j) - 1)%**  (β > 0.1이면 근사 오차 큼)
3. 이분산성(heteroscedasticity) 완화 — 고가 작품의 절대 오차가 자연히 조정됨

**중요: 이 선형 모델은 본 엔진에서 직접 사용하지 않는다.** 비선형 상호작용이 풍부한 미술 데이터에서는 GBM 계열이 더 적합하므로, 2.2절의 비선형 모델로 대체한다. 헤도닉 모델은 "왜 이런 피처를 쓰는가"의 경제학적 근거로만 참조한다.

> **출처**: Rosen, S. (1974). "Hedonic Prices and Implicit Markets." *Journal of Political Economy*, 82(1), 34-55.

### 2.2 함수 근사기: Gradient Boosted Trees

헤도닉 모델이 "가격 = f(특성)"이라는 문제를 정의한다면, GBM은 그 f를 데이터에서 비선형적으로 학습하는 **함수 근사기**다. 피처 간 상호작용, 비선형 효과를 자동으로 포착한다.

**학습 목표**:
```
θ* = argmin_θ  (1/N) Σ_{i=1}^{N} L(y_i, f(X_i; θ))

  y_i = ln(P_i)              : log 변환된 실제 낙찰가
  f(X_i; θ)                  : 트리 앙상블 예측 함수
  L                           : 손실 함수
  θ                           : 트리 파라미터 (분기 규칙, 리프 값)
```

**손실 함수 선택**:
```
본 프로젝트: RMSE (Root Mean Squared Error on log-price)

  L(y, ŷ) = (y - ŷ)²

  log-price 공간에서 RMSE를 최소화하면, 원래 스케일에서의 상대 오차를
  줄이는 경향이 있다. 단, RMSE와 MAPE는 목적함수가 동치가 아니며,
  MAPE 직접 최적화를 원하면 별도 커스텀 목적함수가 필요하다.

  대안 검토:
    Huber Loss — 이상치에 강건하나, 초고가 "서프라이즈" 과소학습 위험
    Quantile Loss — 가격 범위 예측에 유용 (Phase 2에서 검토)
    MAPE Loss — 직접 MAPE를 최적화하는 커스텀 목적함수 (CatBoost 지원)
```

**⚠️ 재변환 편향 (Retransformation Bias)**:
```
log 공간 예측을 원래 스케일로 복원할 때 주의가 필요하다.

  문제: E[ln(P)|X] ≠ ln(E[P|X])
        → exp(E[ln(P)|X]) < E[P|X]   (Jensen 부등식)
        → 단순 exp() 복원은 체계적 과소추정을 유발

  보정 방법 (Duan's Smearing Estimator):
    P̂_corrected = exp(ŷ) × (1/N) Σ exp(e_i)
    여기서 e_i = y_i - ŷ_i (학습 잔차)

  실무 판단:
    트리 모델(GBM)은 조건부 평균이 아닌 조건부 중앙값에 가까운 예측을
    하므로, 선형 회귀 대비 재변환 편향이 작다. 그러나 고가 구간에서
    체계적 과소추정 여부를 반드시 holdout에서 검증해야 한다.
    → Phase 1에서 "가격대별 예측/실제 비율 분포"를 확인하여 보정 필요성 판단
```

> **출처**: Friedman, J.H. (2001). "Greedy Function Approximation: A Gradient Boosting Machine." *Annals of Statistics*.
> Duan, N. (1983). "Smearing Estimate: A Nonparametric Retransformation Method." *JASA*.

### 2.3 CatBoost가 본 도메인에 적합한 이유

```
미술 경매 데이터의 핵심 특성:
  1. 고카디널리티 범주형 변수 — 작가명 3,289개, 매체 2,154개
  2. 순서형 데이터 — 시간 순서가 있는 경매 데이터
  3. 결측값 다수 — 제작연도 38.6%, 재료 6.2%

CatBoost의 대응 메커니즘:

  1. Ordered Target Statistics (OTS)
     범주형 변수를 타겟 기반 수치로 인코딩하되, 랜덤 permutation 순서에
     따라 "해당 샘플 이전에 등장한 동일 카테고리 샘플의 타겟 평균"만 사용.
     이는 단순 "작가 평균 가격 치환"이 아니라, permutation 기반의 leakage 완화 메커니즘이다.

  2. Ordered Boosting
     각 부스팅 단계에서 잔차 계산에 사용하는 모델을 해당 샘플이
     포함되지 않은 데이터로 학습하여 target leakage를 줄인다.
     ⚠️ 이것은 "시간순 정렬"이 아니라 랜덤 permutation 기반이다.
     시계열 미래 누수 방지는 CatBoost가 보장하지 않으며,
     데이터 분할과 피처 생성에서 별도로 시간순 제약을 지켜야 한다. (→ 3.3절)

  3. 내장 NaN 처리 — 결측값을 최적 분기에 자동 할당
```

> **출처**: Prokhorenkova, L. et al. (2018). "CatBoost: unbiased boosting with categorical features." *NeurIPS 2018*.

### 2.4 K-Auction 데이터의 핵심 패턴: 추정가 할인 낙찰

```
추정가 중앙값 대비 낙찰가 비율:
  중앙값:         0.600  (추정가의 60% 수준에서 낙찰)
  추정가 이상:    13.3%  (추정가를 초과하는 낙찰은 소수)
  추정가 50% 이하: 30.2%

이것은 서양 경매소(Christie's, Sotheby's)와 다른 패턴이다.
서양: 추정가 ≈ 낙찰가 하한 (추정가 이상 낙찰이 일반적)
K-Auction: 추정가 ≈ 낙찰가 상한 (추정가 대비 할인이 일반적)

→ 모델이 학습해야 할 핵심 패턴:
  "추정가에서 얼마나 할인될 것인가?" = f(작가 인기, 경매 타입, 시장 분위기)
```

### 2.5 Two-Step 접근법 (향후 적용 검토)

Kim & Kim(2024)이 한국 경매 데이터에서 제안한 2단계 모델:

```
Step 1 — 분류: "추정가 이상으로 낙찰될 것인가?"
  ŷ_class = Classifier(X)  →  {상향 프리미엄, 하향 할인}

Step 2 — 조건부 회귀:
  if 상향:  P̂ = Regressor_up(X)     — 프리미엄 크기 예측
  if 하향:  P̂ = Regressor_down(X)   — 할인 크기 예측

장점: 비대칭 분포를 명시적으로 분리 → 각 그룹의 특성을 정밀 학습
단점: 1단계 분류 오류가 2단계로 전파
```

> **출처**: Kim, K. & Kim, J.B. (2024). "Two-step model based on XGBoost for predicting artwork prices." *KES Journal*.

---

## 3. 피처 엔지니어링: 입력 변수 설계

### 3.1 전체 피처 목록 (22개 → 35개)

#### Phase 1 기본 피처 (22개)

```
No  이름                  타입    변환 공식                                   근거
── ──────────────────── ────── ──────────────────────────────────────────── ──────
 1  artist_name          CAT    원본 작가명 (3,289 카테고리)                  헤도닉 모델 핵심 변수
 2  medium_category      CAT    재료 텍스트 → 10종 매체 분류                  매체별 가격 수준 차이 유의
 3  support_category     CAT    재료 텍스트 → 7종 지지체 분류                 캔버스>종이 프리미엄
 4  auction_type         CAT    위클리/프리미엄/메이저 (3종)                  가격대 세그먼트
 5  is_3d                BOOL   크기 파싱 시 3D 패턴 감지                    조각/공예 구분
 6  is_untitled          BOOL   제목에 "무제"|"Untitled" 포함 여부            구체적 제목 = 높은 가격
 7  ln_estimate_mid      FLOAT  ln((estimate_low + estimate_high) / 2)      ★ 기여도 61% — 핵심 앵커
 8  estimate_ratio       FLOAT  estimate_high / estimate_low                불확실성 지표
 9  estimate_range       FLOAT  estimate_high - estimate_low                절대 범위
10  height_cm            FLOAT  크기 문자열 파싱 (정규식)                     작품 규모
11  width_cm             FLOAT  크기 문자열 파싱 (정규식)                     작품 규모
12  surface_area         FLOAT  height_cm × width_cm                        면적 = 가격 양의 상관
13  aspect_ratio         FLOAT  height_cm / width_cm                        종횡비 (정방형 vs 세로형)
14  lot_number           INT    원본 LOT 번호                                출품 순서 효과
15  session_number       INT    경매 회차 (시간순서 proxy)                    시장 트렌드
16  artist_total_sold    INT    작가 통계: 총 낙찰 건수                      작가 시장 활동도
17  artist_avg_price     INT    작가 통계: 평균 낙찰가                       작가 가격 수준
18  artist_max_price     INT    작가 통계: 최고 낙찰가                       작가 천장가
19  artist_sell_rate     FLOAT  작가 통계: 낙찰률                            작가 인기도
20  is_size_imputed      BOOL   크기 결측 대체 여부 플래그                    데이터 품질 신호
21  is_year_missing      BOOL   제작연도 결측 여부 플래그                     고미술/공예 시그널
22  is_new_artist        BOOL   학습 데이터에 없는 작가 여부                  Cold Start 식별
```

#### Phase 2 고급 파생 피처 (13개 추가)

```
No  이름                      변환 공식                                       주의사항
── ──────────────────────── ──────────────────────────────────────────────── ──────
23  artist_recent_avg_3      해당 회차 이전 최근 3건 낙찰가 평균                시계열 누수 방지 필수
24  artist_recent_avg_10     해당 회차 이전 최근 10건 낙찰가 평균               동상
25  artist_price_trend       최근 10건 선형회귀 기울기 β₁                      β₁ > 0이면 가격 상승 추세
                             (ln(P) = β₀ + β₁·t + ε, t=건 순번)
26  artist_price_volatility  최근 20건 ln(낙찰가) 표준편차                     변동성 = 예측 불확실성
                             std(ln(P_{t-20:t-1}))
27  artist_days_since_last   이전 낙찰 건과의 회차 간격                        오래 안 나온 작가 = 프리미엄?
28  artist_premium_avg       작가의 과거 (낙찰가/추정가중앙값) 평균             추정가 대비 할인/프리미엄 패턴
                             mean(P_k / estimate_mid_k) for k < t
29  artist_premium_std       상동 표준편차                                     패턴의 안정성
30  market_avg_premium_10    최근 10회차 전체 (낙찰가/추정가중앙값) 평균        시장 전체 분위기
31  market_avg_price_10      최근 10회차 전체 평균 낙찰가                      시장 가격 수준
32  same_medium_avg_10       동일 매체 최근 10회차 평균 낙찰가                 매체별 시장 트렌드
33  estimate_tier            추정가 5단계 구간화                               가격 세그먼트
                             (<500만/500~3000만/3000만~1억/1억~10억/10억+)
34  artist_price_rank        작가 가격 순위 백분위                             작가 상대적 위치
                             percentile_rank(artist_avg_price)
35  work_age                 경매시점 연도 - 제작연도                          작품 나이 (결측 시 NaN)
```

### 3.2 피처 변환 상세 공식

#### 3.2.1 크기 파싱 (dimension_parser)

```python
# 5개 패턴 우선순위 (97.3% 파싱 성공률)

패턴 1 — 2D 표준:     "81×116cm" or "81x116"
  정규식: r'(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)'
  결과:   height=81.0, width=116.0, is_3d=False

패턴 2 — 3D 표준:     "31×13×22(h)cm"
  정규식: r'(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)'
  결과:   height=max(31,13), width=min(31,13) 중 첫 두 값, is_3d=True

패턴 3 — 높이만:      "高48" or "H48cm"
  정규식: r'[高Hh]\s*(\d+\.?\d*)'
  결과:   height=48.0, width=NaN, is_3d=True

패턴 4 — 원형:        "diameter 6.5cm" or "Ø6.5"
  정규식: r'[Øø]?\s*(?:diameter|지름)?\s*(\d+\.?\d*)'
  결과:   height=6.5, width=6.5 (정사각 가정)

패턴 5 — 호수 표기:   "20호"
  매핑 테이블 사용: HO_TO_CM[20] → (72.7, 60.6)

파생 피처:
  surface_area  = height × width          (cm²)
  aspect_ratio  = height / width          (무차원)

결측 대체 (1,187건, 2.7%):
  1순위: median(surface_area | 동일 작가 + 동일 매체)
  2순위: median(surface_area | 동일 매체)
  3순위: median(surface_area | 전체) ≈ 2,800 cm²
  + is_size_imputed = 1
```

#### 3.2.2 재료 파싱 (medium_parser)

```python
# 2,154개 고유값 → 10종 매체 + 7종 지지체로 정규화

매체 분류 규칙 (우선순위 순):
  "유채"|"오일"|"oil"           → 유화        (9,748건)
  "수묵"|"먹"|"ink"             → 수묵        (8,637건)
  "석판화"|"실크스크린"|"print"  → 판화        (6,626건)
  "아크릴"|"acrylic"            → 아크릴      (4,385건)
  "혼합"|"미디어"|"mixed"       → 혼합재료    (2,665건)
  "채색"|"담채"                 → 채색          (865건)
  "bronze"|"도자"|"ceramic"     → 조각/공예      (724건)
  "사진"|"c-print"|"digital"   → 사진/디지털    (515건)
  재료 결측                     → unknown     (2,698건)
  위 해당 없음                  → 기타        (7,003건)

지지체 분류 규칙:
  "캔버스"|"canvas"             → 캔버스     (13,639건)
  "종이"|"paper"|"지"           → 종이       (12,568건)
  "비단"|"silk"|"견"            → 비단          (994건)
  "목재"|"wood"|"나무"          → 목재        (1,899건)
  "패널"|"panel"|"보드"         → 패널          (529건)
  재료 결측                     → unknown     (2,698건)
  위 해당 없음                  → 기타       (11,539건)
```

#### 3.2.3 추정가 파생 피처

```
입력: estimate_low (최저), estimate_high (최고)

  estimate_mid   = (estimate_low + estimate_high) / 2
  estimate_range = estimate_high - estimate_low
  estimate_ratio = estimate_high / estimate_low       ← 0 나누기 방지: low=0이면 NaN
  ln_estimate_mid = ln(estimate_mid)                  ← ★ 기여도 61.02%

해석:
  ln_estimate_mid  — 가격 수준의 log 스케일 앵커 (모델의 주력 입력)
  estimate_ratio   — 경매사의 불확실성 크기 (ratio가 크면 변동성 큼)
  estimate_range   — 절대 범위 (고가 작품은 range도 큼)
```

#### 3.2.4 작가 통계 조인 & Cold Start 처리

```
조인: works.작가 = artists.작가명
  성공: ~39,840건 (작가 결측 9.2% 제외 후 대부분)
  실패:     39건 (works에만 있는 작가)

Cold Start 전략 (1,511명, 45.9%가 1건만 보유):

  학습 시 (해당 건 이전 데이터가 없는 경우):
    작가 통계 = 동일 estimate_tier + auction_type 그룹 평균
    is_new_artist = 1

  예측 시 (완전 신규 작가):
    artist_name = "__NEW_ARTIST__"
    작가 통계 = 동일 estimate_tier + auction_type 그룹 평균
    → 모델은 주로 추정가, 크기, 재료에 의존하여 예측
    → confidence = "D" (저신뢰)

작자미상 처리:
    "작자미상"|빈값|NaN → artist_name = "__UNKNOWN__"
    작가 통계: 전체 "작자미상" 그룹의 집계값 사용
    → 고미술/골동품에서 "작자미상"은 특정 가격대를 형성 (학습 가능)
```

### 3.3 시계열 누수(Leakage) 방지 — 엄격 규칙

```
핵심 원칙: 예측 시점(t) 이후의 데이터는 절대 사용 불가

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
규칙 1: 모든 집계 피처는 fold별 train window 안에서 재계산
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ❌ 잘못된 방식:
    artist_stats 테이블을 전체 기간으로 사전 집계 → 조인
    → 미래 낙찰 데이터가 포함되어 target leakage 발생

  ✅ 올바른 방식:
    각 fold(train/valid/test)별로, train window의 데이터만 사용하여
    artist_avg_price, artist_total_sold 등을 동적으로 재계산

    예: Fold k의 train 기간 = 회차 1~380인 경우
        artist_avg_price = mean(낙찰가 | 작가=A, 회차 ≤ 380)
        → 회차 381 이후 데이터는 절대 미포함

  Cold Start fallback의 그룹 평균도 동일 규칙 적용:
    estimate_tier + auction_type 그룹 평균 →
    해당 fold의 train window 데이터로만 계산

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
규칙 2: auction_type별 독립 시간축 사용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  session_number는 auction_type별로 별도 축이므로,
  전체 데이터를 단일 session_number로 정렬하면 타입 간 시간축이 혼재.

  ✅ auction_type별로 독립적인 시간축 정렬 후 피처 계산:
    for atype in ['위클리', '프리미엄', '메이저']:
      subset = works[works['auction_type'] == atype].sort_values('session_number')
      # 이 subset 안에서만 rolling/expanding 피처 계산

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
규칙 3: 동일 회차 내 lot 간 정보 차단
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  같은 session_number 내 여러 lot가 있을 때:
    past_mask = session_number < current_session  (strict <, not <=)
  → 동일 세션 내 earlier lot 정보도 사용하지 않음 (보수적 접근)
  → 실 운영에서는 예측 시점이 "경매 시작 전"이므로 이 접근이 정확함

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
규칙 4: 누수 단위 테스트 (leakage unit test)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  각 집계 피처가 미래 데이터 없이 생성됐는지 fold별 자동 검증:
    for each sample in test_fold:
      assert all aggregate features computed only from data
             where session_number < sample.session_number

데이터 분할 (시간축 기반):
  ╔═══════════════════════════════════════════════╗
  ║  Train (70%)     │ Valid (15%)  │ Test (15%)  ║
  ║  과거 ←────────→ │ ←─────────→ │ ←────────→  ║
  ╚═══════════════════════════════════════════════╝

  위클리:   Train: 회차 1~380 / Valid: 381~430 / Test: 431~486
  프리미엄: Train: 회차 55~180 / Valid: 181~200 / Test: 201~224
  메이저:   Train: 회차 98~160 / Valid: 161~175 / Test: 176~195

  ❌ 금지: random shuffle split (미래 데이터 누수)
```

> **출처**: Spec 문서 5.3절, Implementation Strategy Step 1-1

### 3.4 추가 검토 피처 (Codex 리뷰 반영)

```
Codex 리뷰에서 지적된 빠진 피처 — Phase 2에서 순차 추가 검토:

  빠진 중요 피처:
    - genre_category    작품 장르 (회화/조각/도자/고미술 등) — medium과 별도
    - is_signed         서명 여부 (판화/사진에서 가격 영향 큼)
    - edition_info      에디션 번호, AP/EA 여부
    - ln_surface_area   log(면적+1) — 원값보다 안정적
    - sale_month        경매 시점 월 (시즌성 반영)
    - sale_quarter      분기 (봄/가을 메이저 시즌)
    - artist_is_alive   작가 생존 여부 (사망 프리미엄 효과)
    - artist_birth_year 작가 출생연도

  중복 정리 검토 (ablation으로 결정):
    - height/width/area/aspect_ratio 4개 → area + aspect_ratio 2개로 축소 검토
    - estimate_mid/range/ratio/tier 4개 → ln_estimate_mid + estimate_ratio 2개로 축소 검토
    - artist_avg/max/rank 3개 → 상관 분석 후 대표 1~2개 선택

  ⚠️ 현재 데이터에 없는 피처(서명, 에디션, 생존여부)는
     데이터 수집 가능성 확인 후 추가 여부 결정
```

---

## 4. 모델 학습

### 4.1 Phase 1: CatBoost Baseline

```python
from catboost import CatBoostRegressor

model = CatBoostRegressor(
    iterations=3000,           # 최대 반복 (early stopping으로 조기 종료)
    depth=8,                   # 트리 깊이 — 피처 상호작용 복잡도
    learning_rate=0.05,        # 학습률 — 작을수록 정밀, 느림
    l2_leaf_reg=5,             # L2 정규화 — 과적합 방지
    loss_function='RMSE',      # log-price 공간에서 RMSE
    cat_features=[0,1,2,3,4,5], # 범주형 피처 인덱스
    random_seed=42,
    verbose=100,
    early_stopping_rounds=200, # 200 라운드 개선 없으면 종료
    task_type='CPU',
)

model.fit(
    X_train, y_train,          # y = ln(낙찰가)
    eval_set=(X_valid, y_valid),
    use_best_model=True,       # 검증 최적 모델 사용
)

# 실제 결과: 948 iterations에서 수렴
```

### 4.2 Phase 2: 모델 개선 전략 — 우선순위별 비교 실험

Codex 리뷰 반영: 3-model stacking을 기본 경로로 고정하지 않고, 아래 순서로 비교 실험을 수행한다.
CatBoost/LightGBM/XGBoost는 편향 구조가 크게 다르지 않아 stacking 이득이 제한적일 수 있으므로, 더 직접적인 대안을 먼저 검증한다.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실험 우선순위 (Codex 권장 + Claude 설계)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ① CatBoost 단일모델 고도화 (Phase 2 피처 추가)
     → Baseline 22개 → 35개 피처로 확장 후 재학습
     → 이것만으로 MAPE 3~5%p 개선 기대

  ② 타깃 변환: log(price / estimate_mid) 회귀
     → 절대 가격이 아닌 "추정가 대비 할인/프리미엄율" 직접 예측
     → K-Auction의 핵심 패턴(추정가 60% 낙찰)과 정확히 정렬
     → 추정가 지배력 문제를 구조적으로 해소

     공식:
       y_new = ln(P_i / estimate_mid_i)   ← 할인율의 log
       P̂_i = estimate_mid_i × exp(ŷ_new)  ← 복원

  ③ auction_type별 분리 모델
     → 위클리/프리미엄/메이저의 가격 패턴이 완전히 다름
     → 통합 모델 vs 분리 모델 MAPE 비교 후 결정
     → 분리 모델이 위클리(47%→?) 개선에 효과적일 수 있음

  ④ Two-Step (분류 → 조건부 회귀)
     → Step 1: "추정가 이상 낙찰 여부" 이진 분류
     → Step 2: 상향/하향 그룹별 회귀
     → Kim & Kim(2024) 한국 경매 데이터에서 효과 보고

  ⑤ 3-Model Stacking 앙상블 (위 실험 결과가 불충분할 때)
     → CatBoost + LightGBM + XGBoost
     → Meta-Learner: Ridge Regression
     → 5-Fold Expanding Window CV (시계열 누수 방지)

     주의: fold 설계가 시계열 expanding window여야 하며,
           메타러너 학습 시에도 validation leakage 없어야 함

     ┌────────────────────────────────────────┐
     │ Fold 1: Train[────] Valid[──]          │
     │ Fold 2: Train[──────] Valid[──]        │
     │ Fold 3: Train[────────] Valid[──]      │
     │ Fold 4: Train[──────────] Valid[──]    │
     │ Fold 5: Train[────────────] Valid[──]  │
     │  (Expanding window — 과거 누적 학습)    │
     └────────────────────────────────────────┘

비교 기준:
  전체 MAPE, 타입별 MAPE, MdAPE, Within-20%를 동일 test set에서 비교
  → 가장 좋은 전략 선택 (복합 전략도 가능)
```

> **출처**: Wolpert, D.H. (1992). "Stacked Generalization." *Neural Networks*.
> Kim & Kim (2024). Two-step XGBoost. *KES Journal*.

### 4.3 Optuna 하이퍼파라미터 최적화

```python
import optuna

def objective(trial):
    params = {
        'iterations':    trial.suggest_int('iterations', 1000, 8000),
        'depth':         trial.suggest_int('depth', 4, 10),
        'learning_rate': trial.suggest_float('lr', 0.01, 0.2, log=True),
        'l2_leaf_reg':   trial.suggest_float('l2', 1, 10),
    }
    model = CatBoostRegressor(**params, ...)
    model.fit(X_train, y_train, eval_set=(X_valid, y_valid))
    y_pred = np.exp(model.predict(X_valid))
    y_true = np.exp(y_valid)
    mape = np.mean(np.abs(y_true - y_pred) / y_true) * 100
    return mape

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)
```

---

## 5. 예측 파이프라인: 입력 → 출력 전체 흐름

### 5.1 전체 파이프라인 다이어그램

```
사용자 입력 (테스트 페이지)
  │
  │  작가명, 크기(cm 또는 호수), 재료, 경매타입, 추정가(최저/최고)
  │
  ▼
┌──────────────────────────────────────────────┐
│  Step 1: 입력 정규화                           │
│  ├── 호수 → cm 변환 (HO_TO_CM 매핑)           │
│  ├── 재료 → medium_category + support_category │
│  ├── 크기 → height, width, area, aspect_ratio  │
│  └── 추정가 → mid, range, ratio, ln_mid       │
└──────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────┐
│  Step 2: 작가 통계 조회                        │
│  ├── 기존 작가 → artist_stats 테이블 조인      │
│  ├── 신규 작가 → Cold Start 대체값             │
│  └── 작자미상 → __UNKNOWN__ 그룹 통계          │
└──────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────┐
│  Step 3: 피처 벡터 조립 (22~35개)              │
│  ├── 범주형: [artist, medium, support, type,   │
│  │           is_3d, is_untitled]               │
│  ├── 수치형: [ln_est_mid, est_ratio, ...,     │
│  │           artist_avg, artist_max, ...]      │
│  └── 플래그: [is_size_imputed, is_new_artist]  │
└──────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────┐
│  Step 4: 모델 추론                             │
│  ├── Phase 1: CatBoost 단독                   │
│  └── Phase 2: Ensemble(Cat+LGB+XGB) → Ridge  │
│                                                │
│  출력: ln(P̂) → P̂ = exp(ln(P̂))               │
└──────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────────────────────┐
│  Step 5: 후처리 & 신뢰도 산정                   │
│  ├── 예측가: P̂ (원)                           │
│  ├── 가격 범위: [P̂ × 0.8, P̂ × 1.2]  (±20%)  │
│  │   또는 [exp(ln(P̂)-σ), exp(ln(P̂)+σ)]      │
│  ├── 신뢰도 등급: A/B/C/D                     │
│  └── 추정가 대비 비율: P̂ / estimate_mid       │
└──────────────────────────────────────────────┘
  │
  ▼
테스트 페이지에 결과 표시
```

### 5.2 신뢰도 등급 산정

**⚠️ Codex 리뷰 반영**: 피처 중요도(feature importance)와 예측 신뢰도(confidence)는 다른 개념이다. Ablation 기반 가중치를 confidence 스코어로 직접 전용하는 것은 개념적 오류가 있으므로, 2단계 접근을 취한다.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 규칙 기반 (초기 버전 — calibration 검증 전)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  임시 규칙 (holdout calibration으로 가중치 조정 예정):

  confidence_grade 결정 기준:
    A등급: 추정가 있음 + 작가 낙찰 ≥ 20건 + 최근 2년 내 거래 있음
    B등급: 추정가 있음 + 작가 낙찰 ≥ 6건
    C등급: 추정가 있음 + 작가 낙찰 1~5건
    D등급: 추정가 있음 + 신규/미상 작가, 또는 데이터 부족

  ⚠️ 이 규칙은 초기 출발점일 뿐이며, Phase 1 완료 후
     holdout에서 grade별 실제 커버리지를 검증하여 반드시 조정한다.

  필수 검증 테이블 (Phase 1 산출물):
    ┌────────┬──────────┬──────────┬──────────┐
    │ 등급   │ 샘플 수   │ ±20% 적중│ ±30% 적중│
    ├────────┼──────────┼──────────┼──────────┤
    │ A      │ ?건      │ ?%       │ ?%       │
    │ B      │ ?건      │ ?%       │ ?%       │
    │ C      │ ?건      │ ?%       │ ?%       │
    │ D      │ ?건      │ ?%       │ ?%       │
    └────────┴──────────┴──────────┴──────────┘
  → 이 테이블이 "A등급 70%+ within-20%"를 만족하지 않으면 규칙 재조정

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: Calibration 기반 Reliability Model (목표)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  holdout set에서 각 샘플의 실제 오차(APE)를 구한 뒤,
  입력 메타피처로 "이 예측이 얼마나 믿을 만한가"를 학습한다.

  Reliability Model 입력 피처:
    - artist_sold_count        (작가 낙찰 건수)
    - artist_premium_std       (작가 프리미엄 변동성)
    - artist_recent_count_2y   (최근 2년 거래 건수)
    - estimate_ratio           (추정가 불확실성)
    - is_new_artist            (Cold Start 여부)
    - ensemble_disagreement    (앙상블 모델 간 예측 분산)
    - quantile_width           (Q10-Q90 구간 크기)

  Reliability Model 타깃:
    Pr(APE ≤ 0.2 | X_meta)   → "±20% 이내일 확률"
    Pr(APE ≤ 0.3 | X_meta)   → "±30% 이내일 확률"

  등급 산정:
    Pr(APE ≤ 0.2) ≥ 0.65  →  A
    Pr(APE ≤ 0.3) ≥ 0.60  →  B
    Pr(APE ≤ 0.3) ≥ 0.40  →  C
    나머지                  →  D

  → 규칙이 아닌 데이터 기반으로 confidence를 산정하므로,
    실제 커버리지와 grade가 자동 정렬됨
```

### 5.3 가격 범위 계산 방식

```
방법 1 — 고정 비율 (Phase 1):
  lower = P̂ × (1 - margin)
  upper = P̂ × (1 + margin)

  margin은 신뢰도에 따라 결정:
    A등급: margin = 0.20  (±20%)
    B등급: margin = 0.30  (±30%)
    C등급: margin = 0.50  (±50%)
    D등급: margin = 0.70  (±70%)

방법 2 — 모델 기반 (Phase 2):
  CatBoost의 virtual_ensembles로 예측 분산 추정:
    predictions = model.virtual_ensembles_predict(X, prediction_type='TotalUncertainty')
    mean_pred = predictions[:, 0]
    variance  = predictions[:, 1]
    lower = exp(mean_pred - 1.96 * sqrt(variance))
    upper = exp(mean_pred + 1.96 * sqrt(variance))

방법 3 — 분위수 회귀 (Phase 2):
  Q10 모델 (10번째 백분위)과 Q90 모델 (90번째 백분위)을 별도 학습:
    lower = exp(Q10_model.predict(X))
    upper = exp(Q90_model.predict(X))
```

---

## 6. 평가 체계

### 6.1 성과지표 공식

```
MAPE (Mean Absolute Percentage Error) — 주 지표:
  MAPE = (100/N) × Σ|P_i - P̂_i| / P_i

  해석: "예측이 실제 가격에서 평균 몇 % 벗어나는가?"
  주의: 저가 작품에서 과대 평가 경향 (100만 원 작품의 50만 오차 = 50%)

MdAPE (Median APE) — 이상치 강건 지표:
  MdAPE = Median(|P_i - P̂_i| / P_i) × 100

  해석: "전체 예측의 절반이 이 오차율 이내"
  현재: 26.75% → 절반 이상의 예측이 27% 이내

R² (결정계수):
  R² = 1 - Σ(y_i - ŷ_i)² / Σ(y_i - ȳ)²

  해석: "모델이 가격 변동의 몇 %를 설명하는가?"
  현재: 0.9017 → log-price 기준 90% 설명

Within-K%:
  Within-20% = |{i : |P_i - P̂_i|/P_i < 0.20}| / N × 100

  해석: "예측의 몇 %가 실제가의 ±20% 범위 안에 드는가?"
  현재: 40.1% → 10건 중 4건
```

### 6.2 세그먼트별 평가 (필수)

```
가격대별 MAPE를 반드시 분리 보고한다:

이유: 전체 MAPE는 저가 작품(73.8%)의 높은 오차에 왜곡됨
     메이저 경매(MAPE 20.58%)의 우수한 성능이 가려짐

보고 세그먼트:
  1. 경매 타입별: 위클리 / 프리미엄 / 메이저
  2. 가격대별:   <100만 / 100~500만 / 500~3000만 / 3000만~1억 / 1억+
  3. 신뢰도별:   A / B / C / D
```

### 6.3 목표 성능

| Phase | 전체 MAPE | 메이저 | 프리미엄 | 위클리 |
|-------|----------|--------|----------|--------|
| Baseline (현재) | 40.17% | 20.58% | 32.93% | 47.02% |
| Phase 1 개선 | < 38% | < 19% | < 30% | < 42% |
| Phase 2 앙상블 | < 33% | < 15% | < 27% | < 38% |

---

## 7. 엔진 테스트 페이지

기존 `frontend/index.html`과 **별도**로, 엔진 작동을 확인하는 독립 테스트 페이지를 구축한다.

### 7.1 페이지 구성

```
frontend/engine_test.html  (독립 페이지)

┌─────────────────────────────────────────────────┐
│  VisionAI — 가격 예측 엔진 테스트                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  [입력 영역]                                      │
│  ├── 작가명:        [텍스트 입력]                  │
│  ├── 경매 타입:     [위클리|프리미엄|메이저]         │
│  ├── 크기 입력 방식: [cm 직접입력|호수 선택]         │
│  │   ├── 가로(cm):  [   ]  세로(cm): [   ]       │
│  │   └── 호수:      [10|20|30|50|100호]           │
│  ├── 재료:          [텍스트 입력]                  │
│  ├── 추정가 최저:   [           원]                │
│  ├── 추정가 최고:   [           원]                │
│  └── 제작연도:      [    ] (선택사항)              │
│                                                  │
│  [예측 실행] 버튼                                  │
│                                                  │
├─────────────────────────────────────────────────┤
│  [결과 영역]                                      │
│  ├── 예측 낙찰가:       ₩ 65,000,000             │
│  ├── 가격 범위:         ₩ 52,000,000 ~ 78,000,000│
│  ├── 추정가 대비:       81.3% (할인 18.7%)         │
│  ├── 신뢰도:            A등급                      │
│  └── 피처 기여도 차트:  [막대 그래프]               │
│                                                  │
├─────────────────────────────────────────────────┤
│  [디버그 영역] (접을 수 있음)                       │
│  ├── 파싱된 피처 벡터 (22개) JSON 표시              │
│  ├── 작가 통계 조회 결과                           │
│  ├── 모델 버전 / 학습 일자                         │
│  ├── 추론 소요 시간                                │
│  └── Raw 모델 출력 (log-price)                    │
│                                                  │
├─────────────────────────────────────────────────┤
│  [배치 테스트] 탭                                  │
│  ├── CSV 업로드 → 일괄 예측                        │
│  ├── 결과 테이블 (실제가 vs 예측가 vs 오차)          │
│  └── 세그먼트별 MAPE 요약                          │
└─────────────────────────────────────────────────┘
```

### 7.2 연동 방식

```
Phase 1 — 정적 JSON 기반:
  1. scripts/generate_predictions.py로 전체 예측 JSON 생성
  2. engine_test.html에서 predictions.json을 fetch
  3. 입력값으로 가장 근사한 작가/크기 조합 룩업

Phase 2 — 실시간 API 기반:
  1. FastAPI 서버 로컬 실행 (localhost:8000)
  2. engine_test.html에서 POST /api/v1/predict_price 호출
  3. 실시간 추론 결과 표시
```

---

## 8. 리스크 & 완화 전략

### 8.1 기존 식별 리스크

| # | 리스크 | 심각도 | 완화 전략 |
|---|--------|--------|----------|
| 1 | **추정가 지배력** — 모델이 추정가 복사기가 됨 | 높음 | 추정가 제외 모델 병행. `log(price/estimate_mid)` 타깃 변환 실험 (4.2절 ②) |
| 2 | **저가 MAPE 과대** — <100만 구간 56.44% | 중간 | 가격대별 MAPE 분리 보고. 신뢰도 등급(A~D). MdAPE 병행 |
| 3 | **Cold Start** — 45.9% 작가가 1건만 | 중간 | estimate_tier + auction_type 그룹 평균 fallback (train window 한정) |
| 4 | **유찰 데이터 부재** — 선택 편향 | 낮음 | "낙찰 기준" 명시. 유찰 데이터 확보 시 Heckman IMR 보정 |
| 5 | **회차 ≠ 시간** — 시계열 근사 | 중간 | auction_date 필드 확보 추진. 타입별 독립 시간축 (3.3절 규칙 2) |
| 6 | **고가 서프라이즈** — 추정가 상단 초과 예측 불가 | 중간 | Two-Step 분류기 (4.2절 ④). 작가별 동적 프리미엄 피처 |

### 8.2 Codex 리뷰에서 추가 식별된 리스크

| # | 리스크 | 심각도 | 완화 전략 |
|---|--------|--------|----------|
| 7 | **Schema Drift** — 재료 표기, 추정가 형식, 크기 문자열 패턴 변경 시 parser 조용히 실패 | 높음 | parser failure rate 모니터링. 파싱 실패 건수가 주간 1% 초과 시 알림. 정규식 패턴 버전 관리 |
| 8 | **Distribution Shift** — 작가 사망, 전시 이벤트, 경기 충격 반영 부족 | 높음 | 입력 분포 드리프트 모니터링 (PSI/KS). segment별 rolling MAPE 추적 |
| 9 | **Calibration Drift** — MAPE는 유지돼도 confidence grade 적중률 붕괴 | 중간 | grade별 within-20%/30% coverage를 주간 모니터링. 임계치 이탈 시 reliability model 재학습 |
| 10 | **Feedback Loop** — 내부 사용자가 모델 예측을 참고해 추정가 조정 → 자기강화 | 중간 | 모델 예측이 추정가 설정에 사용되는지 추적. 필요 시 추정가 독립성 감사 |
| 11 | **Fairness** — 신작가/작자미상에 구조적 저평가 강화 | 중간 | D등급 예측에 "데이터 부족으로 인한 근사치" 면책 문구 명시. Cold Start slice 별도 평가 |
| 12 | **Re-training Policy 부재** — 재학습/롤백 기준 없음 | 높음 | 아래 8.3절에 명시적 정책 추가 |
| 13 | **데이터 개정** — 경매 결과 사후 수정, 작가명 표준화 변경 | 낮음 | 학습 데이터 스냅샷 버전 고정. 변경 감지 시 파이프라인 재실행 |

### 8.3 모델 드리프트 모니터링 & 재학습 정책

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모니터링 항목 (Phase 2 서비스화 이후)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 입력 분포 드리프트
     - PSI (Population Stability Index) on ln_estimate_mid, surface_area
     - KS test on artist_avg_price 분포
     - 주간 계산, PSI > 0.2이면 경고

  2. 성능 드리프트
     - Rolling 4주 MAPE (전체 + auction_type별)
     - Rolling 4주 MdAPE, Within-20%
     - 기준: 전체 MAPE가 2주 연속 baseline+5%p 초과 시 재학습 트리거

  3. Calibration 드리프트
     - Grade별 within-20%/30% coverage 주간 계산
     - A등급 within-20%가 60% 미만이면 reliability model 재학습

  4. Parser 건전성
     - 크기/재료 파싱 실패율 주간 추적
     - 실패율 > 3%이면 정규식 패턴 검토

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
재학습 정책
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  정기: 월 1회 (새 경매 결과 누적 후)
  이벤트: 성능 트리거 충족 시 즉시
  롤백: 새 모델의 test MAPE가 기존 모델보다 나쁘면 배포하지 않음

  Champion/Challenger 운영:
    - 현재 운영 모델 = Champion
    - 새로 학습한 모델 = Challenger
    - Challenger가 동일 test set에서 Champion 대비 개선 확인 후에만 교체
    - 학습 데이터 스냅샷 + 모델 버전 고정 (재현성 보장)
```

---

## 9. 검증 전략 (Codex 리뷰 반영 추가)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
필수 검증 항목 (각 Phase 완료 전 통과 필수)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 워크포워드 백테스트
     단일 train/valid/test 한 번이 아니라, 여러 cut-off 시점에서 반복 평가.
     예: cut-off를 회차 350, 380, 410, 440으로 4번 실행하여 안정성 확인.

  2. Leakage Unit Test
     각 집계 피처가 미래 데이터 없이 생성됐는지 fold별 자동 검증.
     → CI에 포함하여 파이프라인 변경 시마다 실행.

  3. Calibration Test
     confidence A/B/C/D별 실제 ±20%, ±30% 커버리지 테이블 생성.
     → 5.2절의 필수 검증 테이블 채우기.

  4. Prediction Interval Backtest
     가격 범위(5.3절)가 실제 80%/90% 커버리지를 만족하는지 검증.

  5. Cold Start Slice Test
     신규 작가, 작자미상, 희소 매체만 따로 MAPE/MdAPE 평가.

  6. Parser Robustness Test
     크기/재료 텍스트 변형, 오타, 혼합 언어 입력에 대한 파싱 성공률.

  7. Ablation 재현 Test
     추정가 제거, 작가 제거, 동적 피처 추가 효과를 동일 split에서 비교.
     → 피처 추가/제거 효과를 정량적으로 문서화.

  8. Champion/Challenger 비교
     CatBoost 단독 vs 타깃 변환 vs Two-Step vs Stacking을
     동일 test set에서 전체/세그먼트별 비교.

  9. Human Benchmark
     내부 전문가(경매 담당자) 추정 vs 모델 추정 비교.
     → 모델이 전문가 수준에 도달했는지 정성적 평가.

  10. Shadow Mode (Phase 2 서비스화 시)
      실제 경매 입력을 받아 예측만 기록하고, 결과 확정 후
      retrospective scoring을 쌓는 구조. 온라인 A/B 이전에 필수.
```

---

## 10. 마일스톤 & 체크리스트

### Phase 1: 데이터 전처리 + Baseline 재현 + 정적 JSON

```
Sprint 0 — 데이터 전처리 + 누수 방지 파이프라인
  □ dimension_parser.py — 크기 파싱 (5개 패턴)
  □ medium_parser.py — 재료 → 매체/지지체 분류
  □ year_parser.py — 제작연도 파싱 + 결측 플래그
  □ feature_pipeline.py — fold별 snapshot 피처 생성 (3.3절 규칙 준수)
  □ 단위 테스트 (parser + leakage unit test)
  □ preprocessed_features.parquet 생성 확인

Sprint 1 — Baseline 재현 + 최소 피처 CatBoost
  □ Baseline 재현 확인 (MAPE 40.17% ± 0.5%p)
  □ 재변환 편향 검증 (가격대별 예측/실제 비율 분포)
  □ 세그먼트별 MAPE 리포트 생성
  □ Calibration 테이블 (grade별 ±20%/30% 커버리지)

Sprint 1.5 — 정적 JSON + 테스트 페이지
  □ generate_predictions.py — 작가별/호수별 예측 JSON 생성
  □ predictions.json 생성
  □ engine_test.html — 엔진 테스트 페이지
  □ Cold Start slice 별도 평가
  □ 주요 작가 10명 수동 검증
```

### Phase 1→2 전환 게이트 (모든 조건 충족 시 전환)

```
  □ 전체 MAPE < 38% AND 타입별 기준 충족 (메이저<19%, 프리미엄<30%)
  □ Leakage unit test 전체 통과
  □ Confidence calibration: A등급 within-20% ≥ 60%
  □ Parser failure rate < 1%
  □ Cold Start fallback 검증 완료 (D등급 MAPE 보고)
  □ 워크포워드 백테스트 4회 이상 안정적
  □ 추론 latency < 100ms (단건 기준)
```

### Phase 2: 모델 비교 실험 + 실시간 API

```
Sprint 2 — 모델 비교 실험 (4.2절 우선순위)
  □ 피처 고도화 (동적 피처 13개 추가)
  □ 실험 ①: CatBoost 단일모델 고도화
  □ 실험 ②: log(price/estimate_mid) 타깃 변환
  □ 실험 ③: auction_type별 분리 모델
  □ 실험 ④: Two-Step (분류→회귀)
  □ 실험 ⑤: 3-Model Stacking (필요 시)
  □ Champion/Challenger 비교 테이블 작성
  □ Optuna 최적화 (100 trials, 최종 선택 모델)

Sprint 3 — API 서비스화
  □ FastAPI 서버 구축
  □ Calibration 기반 Reliability Model (5.2절 Phase 2)
  □ engine_test.html → API 호출 전환
  □ ONNX export (추론 최적화)
  □ 드리프트 모니터링 파이프라인 (8.3절)
  □ Shadow mode 배포 (retrospective scoring 시작)
```

### Phase 2: 앙상블 + 실시간 API

```
Sprint 2 — 앙상블 구축
  □ LightGBM / XGBoost 학습
  □ 5-Fold Time Series Stacking
  □ Optuna 최적화 (100 trials)
  □ 목표 MAPE < 33% 달성 확인

Sprint 3 — API 서비스화
  □ FastAPI 서버 (src/visionai/price_engine/api/server.py)
  □ engine_test.html → API 호출 전환
  □ ONNX export (추론 최적화)
  □ 모니터링 + 리트레이닝 파이프라인
```

---

## 10. Codex 리뷰 가이드

### 10.1 PR 생성 후 Codex 리뷰 요청 프롬프트

```
이 PR은 K-Auction 경매 데이터 기반 가격 예측 엔진의 상세 기획서입니다.
아래 관점에서 **섹션별 인라인 코멘트**를 달아주세요:

1. **수학적 정확성**: 2장의 공식과 논문 인용이 정확한가?
   특히 헤도닉 모델 → CatBoost 확장 논리에 비약은 없는가?

2. **피처 엔지니어링**: 3장의 35개 피처 구성에서
   - 빠진 중요 피처가 있는가?
   - 불필요하거나 중복인 피처가 있는가?
   - 시계열 누수 방지 로직이 충분한가?

3. **모델 전략**: 4장의 CatBoost → 3-model Stacking 접근이 적절한가?
   - 다른 접근법 제안 (TabNet, Temporal Fusion Transformer 등)?
   - Two-Step 모델을 Phase 1부터 적용하는 것이 더 나은가?

4. **신뢰도 산정**: 5.2의 quality_score 공식이 합리적인가?
   - 가중치 0.84/0.16/0.00의 Ablation 근거가 충분한가?

5. **테스트 페이지**: 7장의 엔진 테스트 페이지 구성이
   - 엔진 검증에 충분한 기능을 갖추고 있는가?
   - 추가로 필요한 검증 도구가 있는가?

6. **리스크**: 8장에서 놓친 리스크는?
   - 특히 모델 배포 후 드리프트(drift) 대응이 충분한가?

각 섹션에 인라인 코멘트 + 전체 Summary 작성해주세요.
```

### 10.2 리뷰 병합 프로세스

```
1. Claude → 기획서 초안 작성 (본 문서)
2. GitHub PR 생성 → Codex에 리뷰 요청
3. Codex → 섹션별 인라인 코멘트
4. Claude → Codex 코멘트 반영 + 기획서 수정
5. 양쪽 합의 → 기획서 확정
6. 구현 착수 (Sprint 0부터)
```

---

## 참고 논문 & 출처

| # | 출처 | 본 문서 인용 위치 |
|---|------|------------------|
| 1 | Rosen (1974). "Hedonic Prices and Implicit Markets." *JPE* | 2.1 헤도닉 모델 |
| 2 | Friedman (2001). "Greedy Function Approximation: A Gradient Boosting Machine." | 2.2 GBM |
| 3 | Prokhorenkova et al. (2018). "CatBoost: unbiased boosting with categorical features." *NeurIPS* | 2.3 CatBoost |
| 4 | Kim & Kim (2024). "Two-step model based on XGBoost for predicting artwork prices." *KES* | 2.5, 8장 |
| 5 | Wolpert (1992). "Stacked Generalization." *Neural Networks* | 4.2 앙상블 |
| 6 | Lundberg & Lee (2017). "A Unified Approach to Interpreting Model Predictions." *NeurIPS* | SHAP 기여도 |
| 7 | Aubry et al. (2025). "Deep Learning for Art Market Valuation." *arXiv:2512.23078* | 멀티모달 |
| 8 | Bento et al. (2024). "Tabular Data Models for Predicting Art Auction Results." *Applied Sciences* | 모델 비교 |
| 9 | Mei & Moses (2002). "Art as an Investment." *AER* | 반복 판매 모델 |
| 10 | Cogent Economics (2018). Chinese Paintings Hedonic/Hybrid Models | 하이브리드 |
| 11 | Artwork Pricing Model Integrating Popularity and Ability (2024). *AStA* | 작가 명성 |

---

*본 기획서는 Claude(설계/수학적 근거) + Codex(검증/보완) 듀얼 리뷰를 통해 완성됩니다.*
*엔진 작동 확인은 `frontend/engine_test.html` 페이지에서 수행합니다.*
