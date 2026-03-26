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

### 2.1 헤도닉 가격 모델 (Hedonic Pricing Model)

미술품 가격을 구성 특성들의 함수로 분해하는 경제학적 프레임워크다. 본 엔진의 이론적 출발점이다.

**공식**:
```
ln(P_i) = α + Σ_{j=1}^{J} β_j · X_{ij} + Σ_{t=1}^{T} γ_t · D_{it} + ε_i

  P_i       : 작품 i의 낙찰가 (원)
  X_{ij}    : 작품 i의 j번째 특성 (크기, 매체, 작가 통계 등)
  D_{it}    : 시간 더미 변수 (시장 트렌드 반영)
  β_j       : 특성 j의 암묵 가격 (implicit price) — "유화는 판화 대비 +β%"
  γ_t       : 시점 t의 시장 가격 지수
  ε_i       : 오차항 ~ N(0, σ²)
```

**왜 ln(P)인가?**
1. 미술품 가격은 극단적 우편향 → log 변환으로 정규 분포에 근사
2. β_j를 "X가 1단위 증가 시 가격이 β_j × 100% 변화"로 해석 가능
3. 이분산성(heteroscedasticity) 완화 — 고가 작품의 절대 오차가 자연히 조정됨

> **출처**: Rosen, S. (1974). "Hedonic Prices and Implicit Markets." *Journal of Political Economy*, 82(1), 34-55.

### 2.2 비선형 확장: Gradient Boosted Trees

헤도닉 모델은 선형이므로 피처 간 상호작용을 포착하지 못한다.
GBM(Gradient Boosted Machine)은 이를 자동으로 학습한다.

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

  이유: log-price에 RMSE를 적용하면, 원래 스케일에서의 MAPE와 근사적으로 정렬됨
        — log 공간에서 RMSE 최소화 ≈ 원래 공간에서 MAPE 최소화

  대안 검토:
    Huber Loss — 이상치에 강건하나, 미술품 초고가 "서프라이즈"를 과소학습할 위험
    Quantile Loss — 가격 범위 예측에 유용 (Phase 2에서 검토)
```

> **출처**: Friedman, J.H. (2001). "Greedy Function Approximation: A Gradient Boosting Machine." *Annals of Statistics*.

### 2.3 CatBoost가 본 도메인에 적합한 이유

```
미술 경매 데이터의 핵심 특성:
  1. 고카디널리티 범주형 변수 — 작가명 3,289개, 매체 2,154개
  2. 순서형 데이터 — 시간 순서가 있는 경매 데이터
  3. 결측값 다수 — 제작연도 38.6%, 재료 6.2%

CatBoost의 대응 메커니즘:
  1. Ordered Target Encoding — 범주형 변수를 타겟 기반으로 자동 인코딩
     (작가명을 one-hot이 아닌 "해당 작가의 과거 평균 가격"으로 치환)
  2. Ordered Boosting — 학습 데이터를 시간순으로 정렬하여 target leakage 방지
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

### 3.3 시계열 누수(Leakage) 방지 원칙

```
핵심: 예측 시점(t) 이후의 데이터는 절대 사용 불가

구현 방식 (vectorized):
  works_sorted = works.sort_values('session_number')

  for 피처 in [artist_recent_avg_3, artist_premium_avg, ...]:
    # expanding window: 해당 건의 회차 이전 데이터만 사용
    past_mask = works_sorted['session_number'] < current_session
    피처값 = compute(works_sorted[past_mask])

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

### 4.2 Phase 2: 3-Model Stacking 앙상블

```
Base Models:
  ┌───────────┬──────────────────────────────────────┐
  │ CatBoost  │ 범주형 자동 인코딩, 순서형 부스팅      │
  │ LightGBM  │ Leaf-wise 성장, 대규모 데이터 빠름     │
  │ XGBoost   │ L1/L2 정규화 강점                     │
  └───────────┴──────────────────────────────────────┘

Meta-Learner: Ridge Regression
  → Base 모델들의 예측값 3개를 입력으로 최종 예측

학습 과정:
  1. 5-Fold Time Series CV → 각 Base Model의 OOF 예측값 생성
  2. OOF 예측값(3차원)을 피처로 Meta-Learner 학습
  3. Test: 각 Base Model 예측 → Meta-Learner 최종 예측

  ┌────────────────────────────────────────┐
  │ Fold 1: Train[────] Valid[──]          │
  │ Fold 2: Train[──────] Valid[──]        │
  │ Fold 3: Train[────────] Valid[──]      │
  │ Fold 4: Train[──────────] Valid[──]    │
  │ Fold 5: Train[────────────] Valid[──]  │
  └────────────────────────────────────────┘

공식:
  ŷ_final = Ridge(ŷ_catboost, ŷ_lightgbm, ŷ_xgboost)
  = w₁·ŷ_cat + w₂·ŷ_lgb + w₃·ŷ_xgb + bias

목표: 전체 MAPE 40.17% → 33~35%
```

> **출처**: Wolpert, D.H. (1992). "Stacked Generalization." *Neural Networks*.

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

### 5.2 신뢰도 등급 산정 공식

```
신뢰도는 데이터 품질과 예측 근거의 풍부함으로 결정한다:

quality_score = w₁·S_estimate + w₂·S_artist + w₃·S_physical

  w₁ = 0.84  (추정가 가중치 — Ablation 실측 기반)
  w₂ = 0.16  (작가 통계 가중치)
  w₃ = 0.00  (크기 — 추정가에 이미 내포, 기여도 ~0)

각 항목 스코어 (0~1):
  S_estimate:
    추정가 있음 = 1.0
    추정가 없음 = 0.0  (예측 거부)

  S_artist:
    작가 과거 낙찰 건수 ≥ 20건 = 1.0
    작가 과거 낙찰 건수 6~19건 = 0.7
    작가 과거 낙찰 건수 2~5건  = 0.4
    작가 과거 낙찰 건수 1건    = 0.2
    신규/미상 작가             = 0.0

신뢰도 등급:
  quality_score ≥ 0.90  →  A  "예측 오차 ±20% 이내 기대"
  quality_score ≥ 0.70  →  B  "예측 오차 ±30% 이내 기대"
  quality_score ≥ 0.40  →  C  "예측 오차 ±50% 이내, 참고용"
  quality_score <  0.40  →  D  "근사 추정, 데이터 부족"
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

| # | 리스크 | 심각도 | 완화 전략 | 논문 근거 |
|---|--------|--------|----------|----------|
| 1 | **추정가 지배력** — 모델이 추정가 복사기가 됨 | 높음 | 추정가 제외 모델도 병행 학습. Ablation으로 독립 기여도 확인. 프론트에서 추정가 없는 케이스도 대응 | Baseline Ablation: 제거 시 +11.85%p |
| 2 | **저가 MAPE 과대** — <100만 구간 56.44% | 중간 | 가격대별 MAPE 분리 보고. 신뢰도 등급(A~D) 표시. MdAPE 병행 | 연구 문헌 공통 — 저가 MAPE 과대 현상 |
| 3 | **Cold Start** — 45.9% 작가가 1건만 | 중간 | estimate_tier + auction_type 그룹 평균 fallback. is_new_artist 플래그 | Kim & Kim(2024) Cold Start 전략 |
| 4 | **유찰 데이터 부재** — 선택 편향 | 낮음 | 현재 "낙찰 기준" 명시. 유찰 데이터 확보 시 Heckman IMR 보정 | Cogent Economics(2018) 하이브리드 모델 |
| 5 | **회차 ≠ 시간** — 시계열 근사 | 중간 | auction_date 필드 확보 추진. 현재는 회차로 근사 | Implementation Strategy 리스크 1 |
| 6 | **고가 서프라이즈** — 추정가 상단 초과 예측 불가 | 중간 | Phase 2에서 작가별 동적 프리미엄 피처 추가. 추정가 초과 확률 분류기 검토 | Two-Step Model (Kim & Kim, 2024) |

---

## 9. 마일스톤 & 체크리스트

### Phase 1: 데이터 전처리 + 모델 개선 + 정적 JSON

```
Sprint 0 — 데이터 전처리 파이프라인
  □ src/visionai/price_engine/preprocessing/dimension_parser.py
  □ src/visionai/price_engine/preprocessing/medium_parser.py
  □ src/visionai/price_engine/preprocessing/year_parser.py
  □ src/visionai/price_engine/preprocessing/feature_pipeline.py
  □ tests/price_engine/test_dimension_parser.py
  □ tests/price_engine/test_medium_parser.py
  □ tests/price_engine/test_feature_pipeline.py
  □ preprocessed_features.parquet 생성 확인

Sprint 1 — 모델 개선 + 정적 JSON
  □ Baseline 재현 확인 (MAPE 40.17%)
  □ Phase 2 동적 피처 13개 추가 (artist_premium_avg 등)
  □ 개선 모델 학습 (목표 MAPE < 38%)
  □ scripts/generate_predictions.py — 작가별/호수별 예측 JSON 생성
  □ frontend/data/predictions.json 생성
  □ frontend/engine_test.html — 엔진 테스트 페이지 작성

Sprint 1.5 — 엔진 테스트 검증
  □ 주요 작가 10명 수동 검증 (예측 vs 실제)
  □ 세그먼트별 MAPE 리포트 생성
  □ 신뢰도 등급 분포 확인
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
