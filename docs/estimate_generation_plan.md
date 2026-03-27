# 추정가 생성 엔진 기획서 (v8.0)

> **작성일**: 2026-03-27
> **Phase**: 3 — Estimate Price Generation
> **목표**: 추정가(최저/최고)를 자동 생성하여 현행 가격 예측 엔진의 입력 의존성 해소
> **Codex 리뷰**: 1회차~6회차 MAJOR → v2.0~v7.0, 7회차 MAJOR → v8.0 반영

---

## 1. 문제 정의

### 1.1 현행 시스템의 한계

현재 가격 예측 엔진(Target Transform CatBoost)은 추정가를 **필수 입력**으로 요구한다:

```
ŷ = estimate_mid × exp(CatBoost(X))
```

- `estimate_mid = (추정가_최저 + 추정가_최고) / 2`
- 추정가 피처 중요도: **68%** (전체 21개 피처 중 압도적 1위)
- 추정가 없이는 예측 자체가 불가능

**문제점:**
1. K-Auction 전문가가 추정가를 설정하기 전에는 예측 불가
2. 신규 작품/작가의 사전 가치 평가(Pre-valuation) 불가
3. 추정가의 적정성 검증 도구 부재
4. 독립적인 미술품 가치 평가 시스템으로 활용 불가

### 1.2 목적 분리 (Codex C1 대응)

추정가 생성 엔진은 **두 가지 독립된 목적**을 가진다. 이를 혼합하지 않고 명확히 분리한다.

| 목적 | 정의 | 타깃 | 평가 지표 |
|------|------|------|----------|
| **목적 A: 낙찰가 구간 예측** | 작품 속성으로 낙찰가의 조건부 분위수 예측 | ln(낙찰가) | Coverage, Hedonic R², 구간 MAPE |
| **목적 B: 전문가 추정가 재현** | 경매사 전문가가 설정할 추정가를 모사 | ln(추정가 중앙) | Estimate MAPE, 추정가 괴리율 |

**설계 결정:** 두 목적을 **별도 모델로 분리**하여 각각 최적화한다.

- **Model-A (Hedonic Quantile)**: 낙찰가 분위수 예측 → 독립 가치 평가, Pre-auction Valuation
- **Model-B (Estimate Regressor)**: 전문가 추정가 재현 → 기존 엔진 입력 대체, 추정가 검증

두 모델은 동일한 피처셋을 공유하되, 타깃과 손실 함수가 다르다.

### 1.3 목표

| # | 목표 | 측정 지표 |
|---|------|----------|
| 1 | 낙찰가 구간 예측 정확도 | Coverage ≥ 55%, Hedonic R² ≥ 0.65 |
| 2 | 전문가 추정가 재현 | Estimate MAPE ≤ 35% |
| 3 | 기존 엔진 통합 (재학습 포함) | 통합 MAPE ≤ 32% |
| 4 | Cold Start 대응 | 거래 이력 0건 작가도 예측 가능 (100%) |
| 5 | 생성 가능 비율 | ≥ 95% |

---

## 2. 학술적 근거

### 2.1 Hedonic Pricing Model (Rosen, 1974)

미술품 가격을 측정 가능한 속성들의 함수로 분해하는 기본 프레임워크.

**모델:**
```
ln(Pᵢₜ) = α + Σⱼ βⱼXᵢⱼ + Σₜ δₜDₜ + εᵢₜ
```

| 기호 | 의미 |
|------|------|
| Pᵢₜ | 작품 i의 시점 t 가격 |
| Xᵢⱼ | 작품 i의 속성 j (작가, 매체, 크기, 제작연도 등) |
| βⱼ | 속성 j의 암묵적 가격 (implicit price) |
| Dₜ | 시간 더미 (경매 시점 보정) |
| δₜ | 시간 계수 (시장 트렌드) |

**문헌 성능:**
- Renneboog & Spaenjers (2013, *Management Science*, 59(1), 36-53): R² = 0.65~0.80, 120만 건, 1957-2007
- Chanel, Gerard-Varet & Ginsburgh (1996, *European Economic Review*, 40(3-5), 509-519): R² = 0.70~0.85
- 일반적 범위: **R² = 0.55~0.85**

**핵심 변수와 효과 (문헌별 출처 매핑):**

| 범주 | 변수 | 전형적 효과 | 출처 |
|------|------|------------|------|
| 작가 정체 | 작가 고정효과 | 가격 분산의 30~40% 설명 | Renneboog & Spaenjers (2013), Table 3 |
| 물리적 속성 | 높이, 너비, 면적 | 100in² 당 +2~5% | Renneboog & Spaenjers (2013), Table 4 |
| 매체 | 유화, 수채, 아크릴, 판화 등 | 유화 프리미엄 +20~40% | Chanel et al. (1996), Table 2 |
| 지지체 | 캔버스, 종이, 패널 | 캔버스 프리미엄 ~10~15% | Renneboog & Spaenjers (2013) |
| 서명 | 서명 유무 | 서명 프리미엄 +10~25% | Ashenfelter & Graddy (2003), Table 1 |
| 시간 | 경매 시점 | 시장 사이클 반영 | Goetzmann (1993) |

> **참고:** Rosen, S. (1974). "Hedonic Prices and Implicit Markets: Product Differentiation in Pure Competition." *Journal of Political Economy*, 82, 34-55.

### 2.2 Quantile Regression (Koenker & Bassett, 1978)

**낙찰가 구간 예측(Model-A)의 핵심 이론.** 조건부 분위수를 추정하여 점 추정이 아닌 구간을 생성한다.

**모델:**
```
Q_τ(ln(Pᵢₜ) | Xᵢ) = α(τ) + Σⱼ βⱼ(τ) · Xᵢⱼ
```

**추정 (비대칭 손실 최소화):**
```
min_{α,β} Σᵢ ρ_τ(ln(Pᵢₜ) - α - Xᵢ'β)

         ⎧ τ · |u|      if u ≥ 0
ρ_τ(u) = ⎨
         ⎩ (1-τ) · |u|  if u < 0
```

**분위수 → 가격 구간 매핑:**

| 분위수 (τ) | 용도 | 해석 |
|------------|------|------|
| τ = 0.25 | 가격 하한 | 낙찰가의 25번째 백분위수 |
| τ = 0.50 | 중앙 추정값 | 낙찰가의 중앙값 |
| τ = 0.75 | 가격 상한 | 낙찰가의 75번째 백분위수 |

**역변환 (분위수에는 smearing 적용하지 않음):**
```
가격_하한 = exp(Q̂₀.₂₅(ln(P) | X))
가격_중앙 = exp(Q̂₀.₅₀(ln(P) | X))
가격_상한 = exp(Q̂₀.₇₅(ln(P) | X))
```

> **중요 (Codex C2 대응):** Duan (1983)의 smearing estimator는 조건부 **평균**의 log 역변환에만 적용된다. 분위수 예측값에 smearing을 곱하면 분위수의 통계적 의미가 파괴되므로, 분위수 모델에서는 `exp()` 직접 역변환만 사용한다. log 스케일에서 분위수 성질이 exp 변환에서도 보존되는 이유는 exp가 단조증가 함수이기 때문이다 (Koenker, 2005, *Quantile Regression*, Cambridge University Press, Ch. 2.3).

**Masterpiece Effect** (Scorcu & Zanola, 2011): 고가 구간과 저가 구간에서 가격 결정 메커니즘이 다르다. 분위수별 계수 βⱼ(τ)가 유의하게 다르며, 고가 작품일수록 크기보다 작가 명성이 중요해진다.

> **참고:** Koenker, R. & Bassett, G. (1978). "Regression Quantiles." *Econometrica*, 46, 33-50.
> Scorcu, A. & Zanola, R. (2011). "The Right Price for Art Collectibles: A Quantile Hedonic Regression." *J. Cultural Economics*, 35(4), 257-275.

### 2.3 한국 미술 시장 특수성

**호 단위 블록 프라이싱:**
- 한국 미술 시장은 '호(號)' 단위의 블록 가격 체계를 사용
- 약 40호(≈ 5,280cm²) 부근에서 가격 함수의 구조적 변곡점 존재
- 선형 면적-가격 관계가 아닌 비선형 부분 선형(partially linear) 모델 적합
- **출처:** Lee, Y. & Kim, S. (2011). "Price determinants and genre effects in the Korean art market: a partial linear analysis of size effect." *J. Cultural Economics*, 35(4), 301-320.

**낙찰 실패 시그널링 효과:**
- 유찰 이력이 있는 작품은 재경매 시 총 수익률이 약 14.4%p 하락 (repeat-sales 모델 기준)
- 유찰은 K-Auction/서울옥션 1998-2024 데이터에서 통계적으로 유의한 부정적 시그널
- **출처:** Park, J. et al. (2025). "The paradox of being unsold: hidden signaling value of bought-in in Korean art auction." *J. Cultural Economics*, 49(1), 89-112.

**한국 시장 추가 특수성 (Codex M7 대응):**

| 요소 | 설명 | 피처 반영 방안 |
|------|------|---------------|
| 작가 세대 | 1세대(김환기 등) vs 현대 작가 가격 격차 | `artist_generation` (데이터 가용 시) |
| 국내/해외 작가 | 국내 블루칩 vs 해외 작가 프리미엄 구조 차이 | 현재 데이터에서 구분 불가 → v2 검토 |
| 단색화/민중미술 | 장르별 가격 프리미엄이 시기별로 변동 | `medium_category`로 부분 반영 |
| 에디션 유무 | 판화/사진의 에디션 번호가 가격에 영향 | Sprint 0에서 제목 regex 파싱 시도: `(\d+)/(\d+)` 패턴. 파싱 성공률 ≥ 80% 시 `has_edition` 이진 피처 추가, 미달 시 제외 |
| 경매사별 정책 | K-Auction 단일 소스이므로 현재 해당 없음 | 향후 서울옥션 데이터 추가 시 반영 |

> **현재 데이터 제약:** K-Auction 단일 소스(43,866건)에서 추출 가능한 정보만 사용. 외부 데이터(전시 이력, 갤러리 소속 등)는 현재 미보유.

### 2.4 Machine Learning 기반 미술품 가치 평가

**Two-Step XGBoost** (Kim, K. & Kim, J.B., 2024, *Int. J. Knowledge-based and Intelligent Engineering Systems*, 28(1), 1-14):
- 1단계: 가격대 분류 (Classifier)
- 2단계: 가격대별 전용 회귀 모델
- 한국 경매 데이터에서 단일 모델 대비 우수 성능

**Tabular Data Models** (Kuzma, E. et al., 2024, *Applied Sciences*, 14(23), 11006):
- RandomForest, XGBoost, CatBoost, LightGBM 비교 (43,354건)
- RandomForest가 Hedonic 회귀 및 CNN 대비 우수

**Social Signals** (Fraiberger, S. et al., 2024, *Scientific Reports*, 14, 11615):
- 전시 이력, 갤러리 소속, 기관 인정이 시각적 특징보다 가격 예측력 우수
- 신흥 시장(한국 포함)에서 효과가 특히 강함
- 현재 K-Auction 데이터에서는 사용 불가 → 향후 외부 데이터 연동 시 적용

### 2.5 Cold Start 해결: 계층적 그룹 Fallback (Codex C4 대응)

거래 이력이 적거나 없는 작가를 위한 Partial Pooling 개념:

```
ln(Pᵢⱼ) = αⱼ + Xᵢ'β + εᵢⱼ
αⱼ ~ N(μ_g(j), σ²_g)
```

| 기호 | 의미 |
|------|------|
| αⱼ | 작가 j의 고유 효과 |
| g(j) | 작가 j가 속한 그룹 (매체, 시대, 국적) |
| μ_g(j) | 그룹 평균 (prior) |

**실제 구현 설계 (CatBoost 프레임 내):**

CatBoost는 범주형 피처에 대해 내부적으로 target statistics (ordered target encoding)를 수행하므로, 거래 0건 작가에 대해서도 자동 smoothing이 적용된다. 이에 더하여:

1. **작가 통계 피처의 NaN 처리**: 거래 0건 작가의 `artist_avg_price`, `artist_median_price` 등은 NaN으로 설정 → CatBoost의 네이티브 NaN 처리 활용
2. **3-tier 그룹 기반 fallback 피처 (품질 방어 설계 — Codex 3회차 MAJOR 대응)**:

   | Tier | 그룹 키 | min_count | Shrinkage | 발동 조건 |
   |------|--------|-----------|-----------|----------|
   | **1** | `medium_category × auction_type` | ≥ 30 | Bayesian shrinkage on ln(price): (nᵢx̄ᵢ + m·μ₀) / (nᵢ + m), m=10 | 해당 조합 거래 ≥ 30건 |
   | **2** | `medium_category` | ≥ 50 | 동일 shrinkage (ln scale) | Tier 1 min_count 미달 시 |
   | **3** | `auction_type` | 항상 가용 | 없음 (전체 ln(price) 평균) | Tier 2 min_count 미달 시 |

   - **Shrinkage 공식 (log-price 스케일에서 수행 — Codex 4회차 MAJOR 대응):**
     ```
     smoothed_ln_price = (n × group_mean_ln + m × global_mean_ln) / (n + m)
     ```
     - n = 그룹 내 샘플 수, m = shrinkage 강도 (기본값 10)
     - `group_mean_ln` = 그룹 내 `ln(낙찰가)` 평균, `global_mean_ln` = 전체 `ln(낙찰가)` 평균
     - **log-price 스케일에서 연산하는 이유:** 미술품 가격은 heavy-tailed 분포이므로, 원래 가격 스케일의 산술 평균은 블루칩 이상치에 의해 왜곡된다. log 스케일 평균은 기하 평균에 해당하여 이상치 영향을 크게 줄인다.
     - 소규모 그룹은 global mean 방향으로 수축하여 극단 추정 방지
   - 거래 0건 작가는 Tier 1 → Tier 2 → Tier 3 순서로 가용한 가장 구체적인 그룹 prior를 활용
   - **품질 방어 vs 생성 보장 구분**: 100% 생성은 CatBoost NaN 처리로 보장. 품질 방어는 tier별 MAPE를 Sprint 1에서 측정하여 tier별 성능 하한(예: Tier 3 MAPE < 60%) 설정
   - **Fallback 발동률 모니터링**: 전체 Test set 중 Tier 1/2/3 각각의 비율 보고
3. **`is_new_artist` 플래그**: 거래 0건 작가 여부를 명시적으로 전달 → 모델이 Cold Start 경로를 학습
4. **`medium_x_auction_avg`** (신규 추가): `medium_category × auction_type` 교차 그룹 평균 낙찰가 → Cold Start에서 가장 구체적인 prior 역할
5. **Fallback 보장**: 모든 피처가 NaN이더라도 CatBoost는 예측값 반환 → 100% 생성 보장

**검증 (Codex 2회차 MAJOR 대응):**
- Cold Start 작가(거래 0건) 전용 테스트셋 구성
- Cold Start MAPE 별도 보고 + 신뢰도 D등급 부여
- 3-tier fallback 각 단계별 MAPE 비교 → 그룹 prior가 실제로 품질을 방어하는지 정량 검증
- Cold Start 비중이 높은 위클리 경매에서 별도 slice 분석

---

## 3. 아키텍처 설계

### 3.1 전체 파이프라인

```
┌──────────────────────────────────────────────────────────┐
│  Phase 3: 추정가 생성 엔진 (Estimate Generator)           │
│                                                           │
│  입력: 작가, 매체, 크기, 제작연도, 경매유형               │
│  (추정가 없이도 동작)                                     │
│                                                           │
│  ┌─────────────────────────┐  ┌─────────────────────────┐│
│  │  Model-A: Quantile      │  │  Model-B: Estimate      ││
│  │  ln(낙찰가) 분위수 예측  │  │  ln(추정가중앙) 평균 예측││
│  │  τ=0.25, 0.50, 0.75    │  │  RMSE 손실              ││
│  └──────────┬──────────────┘  └──────────┬──────────────┘│
│             │                            │                │
│  ┌──────────▼──────────────┐  ┌──────────▼──────────────┐│
│  │  Quantile Calibration   │  │  Segment Calibration    ││
│  │  additive 보정 (3.2.1)  │  │  가격대별 편향 보정     ││
│  └──────────┬──────────────┘  └──────────┬──────────────┘│
│             │                            │                │
│  ┌──────────▼──────────────┐  ┌──────────▼──────────────┐│
│  │  (라운딩 없음)           │  │  호 단위 라운딩          ││
│  │  연속값 그대로 출력      │  │  시장 관행 반영          ││
│  └──────────┬──────────────┘  └──────────┬──────────────┘│
│             ▼                            ▼                │
│  예측 구간 (하한/중앙/상한)    추정가 (최저/중앙/최고)     │
└────────────┬─────────────────────────────┬───────────────┘
             │                             │
             ▼                             ▼
┌────────────────────────┐  ┌──────────────────────────────┐
│  독립 가치 평가 결과     │  │  기존 가격 예측 엔진 (v2)    │
│  (Pre-auction 용도)     │  │  생성 추정가 기반 재학습 버전  │
│                         │  │  → 낙찰가 예측               │
└─────────────────────────┘  └──────────────────────────────┘
```

### 3.2 Model-A: Hedonic Quantile Model (낙찰가 구간 예측)

**목적:** 추정가 없이 작품 속성만으로 낙찰가의 조건부 분위수를 예측.

**타깃:** `y = ln(낙찰가)` (Hedonic 표준, Rosen 1974)

**손실 함수:** CatBoost `Quantile:alpha=τ`

```python
# 단일 Multi-Quantile 모델 또는 3개 독립 모델
# Crossing 완화를 위해 Multi-Quantile 우선 시도
CatBoostRegressor(
    loss_function="MultiQuantile:alpha=0.25,0.5,0.75",
    iterations=2000,
    depth=8,
    learning_rate=0.05,
    cat_features=CAT_FEATURE_INDICES,
)
```

> **Codex M5 대응 — Quantile Crossing 완화:**
> CatBoost의 `MultiQuantile` 손실은 단일 모델에서 여러 분위수를 동시에 학습하여 crossing 확률을 크게 줄인다. 만약 `MultiQuantile`이 지원되지 않는 경우, 독립 모델 + 후처리 isotonic 정렬을 적용한다. 단순 min/max 클리핑 대신, non-crossing quantile regression (Bondell et al., 2010, *Biometrics*)의 isotonic rearrangement를 사용:
> ```
> (q̂₂₅, q̂₅₀, q̂₇₅) → isotonic_regression([q̂₂₅, q̂₅₀, q̂₇₅])
> ```

**역변환 (smearing 없음):**
```
가격_하한 = exp(q̂₀.₂₅)
가격_중앙 = exp(q̂₀.₅₀)
가격_상한 = exp(q̂₀.₇₅)
```

exp는 단조증가 함수이므로, log 스케일 분위수의 역변환은 원래 스케일 분위수를 정확히 보존한다 (Koenker, 2005, Ch. 2.3).

#### 3.2.1 Prediction Interval Calibration (Codex 4회차/5회차/7회차 대응)

> **용어 정의 (Codex 7회차 MAJOR 대응):**
> - **Raw Quantile**: CatBoost MultiQuantile이 출력하는 τ=0.25, 0.50, 0.75 조건부 분위수. 이론적 coverage = 50%.
> - **Calibrated Prediction Interval**: Raw Quantile에 additive shift를 적용하여 실무 목표 coverage(≥ 55%)를 달성한 구간. 이 시점에서 출력은 더 이상 엄밀한 q25/q75가 아니며, **예측 구간(prediction interval)**이다.
>
> 문서 전체에서 calibration 이후 출력은 "예측 구간(하한/중앙/상한)"으로 지칭하며, "q25/q75"는 calibration 이전의 raw output에만 사용한다.

Calib set에서 각 분위수 τ에 대해 **휴리스틱 additive 보정**을 수행한다. 이 방법은 split conformal prediction과 달리 finite-sample coverage를 이론적으로 보장하지 않으며, empirical calibration에 해당한다.

```
보정된 구간 하한(X) = q̂₀.₂₅(X) + Δ_low
보정된 구간 상한(X) = q̂₀.₇₅(X) + Δ_high
보정된 중앙값(X)   = q̂₀.₅₀(X) + Δ_mid
```

**보정 절차:**
1. Calib set에서 각 raw quantile τ별 잔차 계산: `rᵢ = yᵢ - q̂_τ(Xᵢ)` (y = ln(낙찰가))
2. 실제 coverage 계산: `coverage_actual = P(q̂₂₅ ≤ y ≤ q̂₇₅)` on Calib set
3. 목표 coverage(**게이트 기준 55%**, G1 참조)와 실제 coverage 차이에 따라 보정:
   - `Δ_low = quantile(r₀.₂₅, α_low)` — 하한을 실제 잔차 분포에 맞게 이동
   - `Δ_high = quantile(r₀.₇₅, α_high)` — 상한을 실제 잔차 분포에 맞게 이동
   - α_low, α_high는 목표 coverage를 달성하도록 Calib set에서 grid search
4. 중앙값에 대해서는 median 잔차로 bias 보정: `Δ_mid = median(r₀.₅₀)`

**보정 전/후 구분:**
- 게이트 A1(Pinball Loss), A6(Quantile Calibration)은 **raw quantile** 기준으로 평가
- 게이트 A2(Interval Score), A3(Coverage Rate), A5(Range Width)는 **calibrated prediction interval** 기준으로 평가

**한계 및 보완:**
- 이 방법은 분포 안정성(stationarity)을 전제한다. 시장 사이클 변동이 클 경우 Δ 값이 불안정할 수 있다.
- **Validation에서 반드시 coverage 유효성 검증**: Calib에서 학습한 Δ가 Validation에서도 coverage ≥ 55%를 충족하는지 확인한다.
- Coverage가 Validation에서 미달 시, Calib 크기 확대 또는 slice별 보정(메이저/위클리)을 검토한다.
- 향후 split conformal prediction (Vovk et al., 2005)으로 전환 시 finite-sample 보장이 가능하나, 현 단계에서는 구현 복잡성 대비 실용적 coverage 달성을 우선한다.

### 3.3 Model-B: Estimate Regressor (전문가 추정가 재현)

**목적:** 경매사 전문가가 설정할 추정가(중앙)를 재현. 기존 엔진의 입력으로 사용.

**타깃:** `y = ln(추정가 중앙)` = `ln((추정가_최저 + 추정가_최고) / 2)`

**손실 함수:** CatBoost `RMSE` (조건부 평균 예측)

```python
CatBoostRegressor(
    loss_function="RMSE",
    iterations=2000,
    depth=8,
    learning_rate=0.05,
    cat_features=CAT_FEATURE_INDICES,
)
```

**역변환 (세그먼트별 Duan smearing 적용 — Codex 2회차 MAJOR 대응):**
```
추정가_중앙 = exp(ŷ) × smearing_factor(segment)
```

가격대별 이분산이 크므로, smearing factor를 **세그먼트별로 분리** 계산한다:
```
smearing_factor(s) = (1/nₛ) × Σᵢ∈s exp(êᵢ)    (ê: Calib set residuals, s: 가격 세그먼트)
```

> **후처리 파라미터 학습 위치 통일 원칙 (Codex 4회차 MAJOR 대응):**
> 모든 후처리 파라미터(smearing_factor, segment_ratios, quantile calibration)는 **Calib set**에서 학습한다 (6.3절 4-way 분할의 Calib 블록). OOF 체인(4.2.1절) 내에서는 각 Fold의 **Calib_B_k**가 이 역할을 수행한다. 본 문서 전체에서 후처리 학습 위치를 "Calib"로 통일한다.

**세그먼트 설계 (Codex 3회차 MAJOR 대응):**

세그먼트 경계는 **Calib set의 실제 추정가 분포의 분위수**로 설정하여 각 bin의 샘플 수를 균등화한다. 고정 가격대 bin 대신 adaptive quantile bin을 사용:

```python
# 예: 5-quantile bin (각 bin에 ~20% 데이터)
boundaries = np.quantile(calib_est_mid, [0.2, 0.4, 0.6, 0.8])
segments = np.digitize(predicted_est_mid, boundaries)
```

| 세그먼트 | 정의 | 비고 |
|---------|------|------|
| S1 | < Q20 | 최저가 ~20% |
| S2 | Q20 ~ Q40 | |
| S3 | Q40 ~ Q60 | |
| S4 | Q60 ~ Q80 | |
| S5 | ≥ Q80 | 최고가 ~20% |

**장점:**
- 각 bin에 충분한 샘플 보장 (nₛ ≈ N/5)
- 고가 구간도 ~20% 데이터 확보 → global fallback 불필요
- 경계값 불연속 완화: 예측값이 아닌 calib set 분위수 기반

**Fallback**: 만약 특정 bin nₛ < 30이면 인접 bin과 병합. Global fallback은 최후 수단.

**안정성 검증:**
- 세그먼트별 `E[exp(e)|segment]`의 bootstrap 95% CI 계산
- CI 폭이 ±0.1 이내인지 확인
- Fold별 세그먼트 경계 변동률 CV < 0.2

> **Codex C2 완전 해소:** smearing은 조건부 **평균** 예측(Model-B)에만 적용. 분위수 예측(Model-A)에는 적용하지 않음.

**추정가 범위 생성:**
```
추정가(최저) = 추정가_중앙 × ratio_low(segment)
추정가(최고) = 추정가_중앙 × ratio_high(segment)
```

`ratio_low`, `ratio_high`는 **Calib set**에서 세그먼트별로 학습:
```
ratio_low(s)  = median(추정가_최저 / 추정가_중앙) for samples in segment s
ratio_high(s) = median(추정가_최고 / 추정가_중앙) for samples in segment s
```

K-Auction 실데이터에서 추정가 비율은 가격대별로 안정적인 패턴을 보인다.

### 3.4 피처 설계 (추정가 제외)

추정가를 입력으로 사용할 수 없으므로, 추정가 관련 4개 피처를 제거하고 대체 피처를 추가한다.

**제거 피처 (4개):**
- `estimate_mid`, `estimate_range`, `estimate_ratio`, `ln_estimate_mid`

**유지 피처 (15개) — 시계열 누수 방지 명시 (Codex M6 대응):**

| 피처 | 누수 방지 규칙 |
|------|---------------|
| `artist_clean` | 범주형 — CatBoost ordered encoding, 학습 시 자동 분리 |
| `artist_avg_price` | **strict < cutoff 회차만 사용** (기존 artist_stats_snapshot과 동일) |
| `artist_max_price` | **strict < cutoff 회차만 사용** |
| `artist_total_sold` | **strict < cutoff 회차만 사용** |
| `is_new_artist` | cutoff 이전 거래 0건 여부 |
| `height_cm`, `width_cm`, `surface_area`, `aspect_ratio` | 물리적 속성 — 시간 독립 |
| `is_size_imputed` | 파싱 성공 여부 — 시간 독립 |
| `medium_category`, `support_category`, `is_3d` | 재료 속성 — 시간 독립 |
| `회차` | 경매 회차 번호 — 시간 변수 자체 |
| `is_untitled` | 제목 속성 — 시간 독립 |

> **동일 회차 내 타 lot 정보 혼입 방지:** 작가 통계는 반드시 `회차 < 현재_회차` 조건으로 산출. 동일 회차 내 다른 lot의 낙찰 결과는 사용하지 않는다. 이는 기존 `compute_artist_stats_snapshot`의 strict cutoff 로직과 동일.

**신규 추가 피처 (8개):**

| # | 피처명 | 산출 방법 | 누수 방지 | 근거 |
|---|--------|----------|----------|------|
| 1 | `artist_median_price` | strict < cutoff 작가별 낙찰가 중앙값 | fold 기준 | Renneboog & Spaenjers (2013), Table 3 |
| 2 | `artist_price_trend` | 최근 5회차 vs 이전 평균 변화율 | strict < cutoff | Garay et al. (2022), Bayesian Dynamic Hedonic |
| 3 | `medium_avg_price` | strict < cutoff 매체별 평균 낙찰가 | fold 기준 | Chanel et al. (1996), Table 2 |
| 4 | `size_ho` | surface_area → 호수 변환 (1호 ≈ 132cm²) | 시간 독립 | Lee & Kim (2011), p.308 |
| 5 | `size_ho_above40` | max(0, size_ho - 40): 40호 초과분. 변곡점 비선형성 반영 | 시간 독립 | Lee & Kim (2011), 40호 변곡점 |
| 6 | `auction_type_factor` | strict < cutoff 경매유형별 평균 낙찰가 비율 | fold 기준 | K-Auction 내부 데이터 |
| 7 | `artist_unsold_rate` | strict < cutoff 작가별 유찰률 | fold 기준 | Park et al. (2025), Table 3 |
| 8 | `medium_x_auction_avg` | strict < cutoff 매체×경매유형 교차그룹 평균 ln(낙찰가) | fold 기준 | Cold Start prior (2.5절), Tier 1 그룹 |

**총 피처: 23개** (15 유지 + 8 신규)

> **Sparse-history 피처 안정화 규칙 (Codex 7회차 MINOR 대응):**
> 거래 이력이 적은 작가(1~4건)의 통계 피처는 노이즈가 크므로 아래 규칙을 적용한다:
> - `artist_price_trend`: 거래 < 5건이면 NaN 처리 (추세 계산 불가)
> - `artist_unsold_rate`: 출품 < 3건이면 NaN 처리 (유찰률 신뢰 불가)
> - `artist_median_price`, `artist_avg_price`, `artist_max_price`: 거래 < 3건이면 Cold Start와 동일한 Bayesian shrinkage (log-price 스케일, m=10) 적용
> - `auction_type_factor`, `medium_avg_price`, `medium_x_auction_avg`: 그룹 내 샘플 < 30건이면 전체 평균으로 shrinkage
> 이 규칙은 Cold Start(0건)과 일반 작가(충분한 이력) 사이의 "near-cold start" 구간에서 피처 노이즈를 억제한다.

> **40호 변곡점 반영 (Codex 4회차 MINOR 대응):** Lee & Kim (2011)이 보고한 약 40호 부근의 구조적 변곡점을 명시적으로 반영하기 위해 `size_ho_above40 = max(0, size_ho - 40)` hinge 피처를 추가한다. CatBoost가 비선형성을 자동 학습할 수 있지만, 문헌에서 확인된 변곡점을 명시적 피처로 제공하면 학습 효율이 향상된다. Sprint 1에서 해당 피처의 importance를 확인하고, 기여가 미미하면 제거한다.

### 3.5 추정가 범위 생성 로직

```python
def generate_estimate_range(model_a, model_b, X, segment_ratios, smearing_factor):
    """Model-A(가격 구간) + Model-B(추정가 재현) 결합."""

    # === Model-A: 예측 구간 (독립 가치 평가) ===
    q25, q50, q75 = model_a.predict(X)  # MultiQuantile raw 출력
    # calibration shift 적용 (3.2.1절)
    price_low  = np.exp(q25 + delta_low)    # smearing 없음, 라운딩 없음
    price_mid  = np.exp(q50 + delta_mid)
    price_high = np.exp(q75 + delta_high)
    # Note: Model-A 출력은 연속값 — 호 단위 라운딩 적용하지 않음

    # === Model-B: 전문가 추정가 재현 (기존 엔진 입력용) ===
    ln_est_mid = model_b.predict(X)
    est_mid = np.exp(ln_est_mid) * smearing_factor  # 평균 예측 → smearing 적용

    # 세그먼트별 최저/최고 비율 적용
    est_low  = est_mid * segment_ratios['low']   # 예: 0.80
    est_high = est_mid * segment_ratios['high']  # 예: 1.20

    # 호 단위 라운딩 (low, mid, high 모두 적용 — Codex m11 대응)
    est_low  = round_to_market_unit(est_low)
    est_mid  = round_to_market_unit(est_mid)
    est_high = round_to_market_unit(est_high)

    return {
        'price_range': (price_low, price_mid, price_high),   # 독립 가치 평가
        'estimate': (est_low, est_mid, est_high),            # 추정가 재현
    }
```

### 3.6 호 단위 라운딩 (Market Unit Rounding) — Model-B 전용

K-Auction 추정가는 특정 단위로 라운딩된다. **Model-B 출력(추정가)의 low, mid, high에만 적용.** Model-A 출력(예측 구간)은 연속값으로 유지하여 coverage/interval score 해석을 보존한다 (Codex 7회차 MINOR 대응).

| 가격대 | 라운딩 단위 | 예시 |
|--------|-----------|------|
| < 100만 | 10만 | 80만 → 80만 |
| 100만~500만 | 50만 | 350만 → 350만 |
| 500만~1,000만 | 100만 | 750만 → 800만 |
| 1,000만~5,000만 | 500만 | 3,200만 → 3,000만 |
| 5,000만~1억 | 1,000만 | 7,500만 → 8,000만 |
| 1억 이상 | 5,000만 | 2.3억 → 2.5억 |

```python
def round_to_market_unit(price: float) -> int:
    """K-Auction 추정가 관행에 맞춰 라운딩."""
    if price < 1_000_000:
        return round(price / 100_000) * 100_000
    elif price < 5_000_000:
        return round(price / 500_000) * 500_000
    elif price < 10_000_000:
        return round(price / 1_000_000) * 1_000_000
    elif price < 50_000_000:
        return round(price / 5_000_000) * 5_000_000
    elif price < 100_000_000:
        return round(price / 10_000_000) * 10_000_000
    else:
        return round(price / 50_000_000) * 50_000_000
```

---

## 4. 기존 엔진 통합 전략 (Codex C3 대응)

### 4.1 Covariate Shift 문제

기존 가격 예측 엔진은 **전문가 추정가** 분포를 입력으로 학습되었다. AI가 생성한 추정가는 전문가 추정가와 분포가 다를 수 있으므로, 그대로 기존 엔진에 넣으면 **covariate shift**가 발생한다.

추정가의 피처 중요도가 68%이므로, 생성 추정가의 체계적 편향이 최종 예측에 증폭될 위험이 크다.

### 4.2 통합 옵션 비교

| 옵션 | 방법 | 장점 | 단점 |
|------|------|------|------|
| **A: 기존 엔진 재학습** | Model-B 출력을 추정가로 사용하여 기존 엔진을 재학습 | 분포 일치, 안정적 | 재학습 비용, 성능 하락 가능 |
| **B: Stacking** | Model-A 출력 + Model-B 출력 + 기타 피처 → 2nd-level 모델 | 최적 조합 가능 | 복잡도 증가, 과적합 위험 |
| **C: 직접 예측** | Model-A의 q50을 최종 낙찰가 예측으로 직접 사용 | 단순, 기존 엔진 불필요 | 기존 엔진 대비 정확도 하락 가능 |

**선택: 옵션 A (재학습) + 옵션 C (직접 예측) 병행**

1. **Phase 3a**: Model-A/B 학습 + 독립 평가
2. **Phase 3b**: Model-B **OOF(Out-of-Fold) 생성 추정가**로 기존 엔진 재학습 (v2)
3. **비교**: 직접 예측(Model-A q50) vs 재학습 엔진(Model-B → 기존 엔진 v2) MAPE 비교
4. **Champion 선택**: 더 나은 쪽을 Champion으로 채택

### 4.2.1 OOF 생성 추정가 절차 (Codex 2회차 CRITICAL 대응)

기존 엔진 v2의 학습 입력으로 사용할 추정가는 **반드시 OOF(Out-of-Fold)** 방식으로 생성해야 한다. Model-B가 학습에 사용한 동일 샘플에 대해 생성한 추정가를 v2 학습에 재사용하면, 학습/추론 시점의 입력 분포가 인위적으로 일치하여 오프라인 성능이 과대평가된다.

**절차 — 후처리 포함 완전한 생성 체인 (Codex 3회차 CRITICAL 대응):**

v2 학습 입력으로 넣는 값은 `smearing + ratio` 후처리를 모두 적용한 **최종 추정가(low/mid/high)**이다. 서빙 시 생성 체인과 동일해야 오프라인-서빙 분포 일치가 보장된다.

```
Step 1. 시계열 기반 Expanding-Window K-Fold (예: 5-fold, 회차 순서 유지)
   Fold 1: Train_B=[회차 1~20], Calib_B=[회차 21~23], Predict=[회차 24~25]
   Fold 2: Train_B=[회차 1~25], Calib_B=[회차 26~28], Predict=[회차 29~30]
   ...

Step 2. 각 Fold k에서:
   a. Train_B_k로 Model-B_k 학습 (CatBoost RMSE, 타깃=ln(추정가 중앙))
   b. Calib_B_k에 대해 Model-B_k 예측 → fold-local 후처리 파라미터 산출:
      - smearing_factor_k(segment) = (1/nₛ) × Σᵢ∈s exp(êᵢ)  (Calib_B_k residuals)
      - ratio_low_k(segment) = median(추정가_최저/추정가_중앙)  (Calib_B_k)
      - ratio_high_k(segment) = median(추정가_최고/추정가_중앙) (Calib_B_k)
   c. Predict 구간에 대해 Model-B_k + fold-local 후처리 적용:
      - ln_est_mid = Model-B_k.predict(X)
      - est_mid = exp(ln_est_mid) × smearing_factor_k(segment)
      - est_low = est_mid × ratio_low_k(segment)
      - est_high = est_mid × ratio_high_k(segment)
      - round_to_market_unit(est_low, est_mid, est_high)

Step 3. 전체 Train 구간에 OOF 추정가 할당:
   각 샘플의 추정가 = 해당 샘플이 Predict에 속한 Fold의 모델+후처리가 생성한 값
   → est_low_oof, est_mid_oof, est_high_oof

Step 4. 기존 엔진 v2 학습:
   - 입력 피처 (기존 엔진의 추정가 관련 4개 피처를 OOF 생성값으로 대체):
     * estimate_mid      = est_mid_oof
     * estimate_range    = est_high_oof - est_low_oof
     * estimate_ratio    = est_high_oof / est_low_oof
     * ln_estimate_mid   = ln(est_mid_oof)
     + 기타 17개 피처 (기존 엔진과 동일, 추정가 무관 피처)
   - 타깃: ln(낙찰가 / est_mid_oof) (기존 Target Transform 방식)
   - 즉, v2는 기존 엔진과 동일한 21개 피처 구조를 유지하되,
     전문가 추정가 → OOF 생성 추정가로 대체한 것만 다르다.

Step 5. Validation/Test (4-way 분할과 일관된 경로 — Codex 5회차 CRITICAL 대응):
   - 분할: Train | Calib | Validation | Test (6.3절 4-way 분할)
   - Model-B_full: Train으로 학습
   - 후처리 파라미터: Calib에서만 산출 (smearing, ratio, segment 경계)
   - Validation 평가: Model-B_full + Calib 후처리 → Validation에 적용하여 성능 평가
   - Model-B_final: Train+Calib로 학습 (Validation/Test 미포함)
   - Test 평가: Model-B_final + Calib_final(=Validation)에서 산출한 후처리 → Test에 적용

   > **핵심:** Validation은 성능 평가에만 사용한다. Model-B_final의 Test 경로에서
   > Calib_final로 Validation 데이터를 사용하는 것은 **모델 학습에 Validation을
   > 포함하지 않기 때문에** 정보 누수가 아니다. Model-B_final은 Train+Calib로
   > 학습하고, Validation은 후처리 파라미터 산출(Calib_final 역할)에만 사용한다.
   > 이 구조는 시계열에서 expanding window의 표준 관행과 동일하다.
```

**핵심 원칙:** 각 Fold에서 후처리 파라미터는 해당 Fold의 **Calib 블록**에서만 산출한다. Predict 블록의 정보는 절대 사용하지 않는다. 이로써 OOF 추정가의 생성 체인이 서빙 시 체인과 동일해진다.

**분포 정렬 검증:**
- OOF 추정가 분포 vs 서빙 시 추정가 분포의 PSI < 0.1
- 세그먼트별 median(OOF 추정가 / 실제 추정가) 모니터링
- Fold별 smearing_factor 변동 CV < 0.15 확인

### 4.3 통합 시나리오

**시나리오 A: 독립 가치 평가 (추정가 없는 경우)**
```
작품 정보 → Model-A → 가격 구간 (하한/중앙/상한)
                     → 독립적 낙찰가 예측 (q50)
```

**시나리오 B: 추정가 검증 (추정가 있는 경우)**
```
작품 정보 → Model-B → AI 추정가 생성
         → |AI 추정가 - K-Auction 추정가| / K-Auction 추정가
         → 세그먼트별 차등 경고 기준 적용:
           - 메이저 + 고가(>3000만): 괴리율 > 20% → 경고
           - 프리미엄: 괴리율 > 30% → 경고
           - 위클리 + 저가(<500만): 괴리율 > 40% → 경고
```
> **Codex m12 대응:** 경고 기준을 일률 30%에서 세그먼트별 차등으로 변경.

**시나리오 C: 기존 엔진 연동 (재학습 버전)**
```
작품 정보 → Model-B → 생성 추정가
         → 기존 엔진 v2 (재학습) → 낙찰가 예측
```

**시나리오 D: 사전 가치 평가 (Pre-auction)**
```
작가 + 작품 속성 → Model-A → 예상 가격 구간
                            → 출품 여부 의사결정 참고
```

---

## 5. 평가 지표 및 게이트 조건 (Codex M8, M9 대응)

### 5.1 평가 지표 — 목적별 분리

**Model-A 지표 (낙찰가 구간 예측):**

| # | 지표 | 정의 | 목적 |
|---|------|------|------|
| A1 | **Pinball Loss (주 지표)** | Σᵢ ρ_τ(yᵢ - q̂_τ,ᵢ), τ별 합산 | quantile proper scoring |
| A2 | **Interval Score** | IS = (q̂₇₅ - q̂₂₅) + (2/α)(q̂₂₅ - y)⁺ + (2/α)(y - q̂₇₅)⁺ | 구간 질 종합 평가 |
| A3 | Coverage Rate | 낙찰가 ∈ [exp(q̂₂₅), exp(q̂₇₅)] 비율 | 구간 포함 정확도 |
| A4 | Hedonic R² (q50, 보조) | q50 예측의 결정 계수 | 점 추정 정확도 |
| A5 | Range Width | (exp(q̂₇₅) - exp(q̂₂₅)) / exp(q̂₅₀) | 구간 너비 적정성 |
| A6 | Quantile Calibration | 실제 coverage가 이론적 coverage에 근접하는지 | 분위수 신뢰도 |

**Model-B 지표 (추정가 재현):**

| # | 지표 | 정의 | 목적 |
|---|------|------|------|
| B1 | Estimate MAPE | \|생성 중앙 - 실제 추정가 중앙\| / 실제 추정가 중앙 | 추정가 재현 정확도 |
| B2 | Estimate Bias | median(생성 / 실제) 가격대별 | 체계적 편향 |
| B3 | 통합 MAPE | 생성 추정가 → 재학습 엔진 → 최종 낙찰가 MAPE | 파이프라인 정확도 |

**공통 지표:**

| # | 지표 | 정의 | 목적 |
|---|------|------|------|
| C1 | Cold Start MAPE | 거래 0건 작가 slice의 MAPE | Cold Start 품질 |
| C2 | Leakage Test | 시계열 누수 단위 테스트 | 데이터 무결성 |

### 5.2 게이트 조건 (12개) — 근거 명시 (Codex M9, 4회차, 6회차 대응)

| # | 게이트 | 기준 | 근거 |
|---|--------|------|------|
| G1 | Coverage Rate (전체) | ≥ 55% | q25-q75 이론적 baseline 50% + 라운딩/calibration 마진 5%p |
| G2 | Coverage Rate (메이저) | ≥ 58% | 메이저는 데이터 풍부 → 더 높은 기대 |
| G3 | Hedonic R² (보조, 전체) | ≥ 0.65 | 추정가 없는 순수 Hedonic 모델. 문헌 범위 0.55~0.85에서 보수적 하한. 주 지표는 Pinball Loss |
| G4 | Range Width 적정성 | 0.3 ≤ median ≤ 1.2 | Model-A의 예측 구간 폭 = (exp(q̂₇₅) - exp(q̂₂₅)) / exp(q̂₅₀). 하한 0.3은 의미 있는 불확실성 표현, 상한 1.2는 과도하게 넓은 구간 방지. Sprint 1 실험에서 실제 분포 기반 조정 (Codex 6회차 MAJOR 대응) |
| G5 | Estimate MAPE (전체) | < 35% | 전문가 추정가 재현 — 추정가 자체의 불확실성 반영 |
| G6 | Estimate MAPE (메이저) | < 25% | 메이저 작가 데이터 충분 → 더 높은 정확도 기대 |
| G7 | 통합 MAPE | < 32% | 기존 엔진(27%) 대비 +5%p 허용 (재학습 degradation) |
| G8 | Cold Start 생성 보장 | 100% | CatBoost NaN 처리 + 그룹 피처 보장 |
| G9 | Cold Start 품질 하한 | MAPE < 60% | 거래 0건 작가 slice의 MAPE 하한 (Codex 4회차 MINOR 대응) |
| G10 | Leakage test | 전체 통과 | 8개 규칙 (피처 4 + 후처리 4, 6.3절 참조) |
| G11 | 저유동성 작가 slice MAPE | < 50% | artist_unsold_rate > 50% 작가 slice 별도 평가 (Codex 6회차 MAJOR 대응) |
| G12 | Monotonicity | low ≤ mid ≤ high 100% | MultiQuantile 또는 isotonic 후처리 |

> **R² ≥ 0.65 근거:** 기존 엔진은 추정가 포함 R² = 0.936. 추정가(68% 중요도) 제거 시 R²는 대폭 하락이 예상된다. 문헌의 0.55~0.85 범위에서 K-Auction 데이터 특성(한국 시장 단일 소스, 제한된 외부 피처)을 고려하여 0.65를 설정. Sprint 1에서 실험 후 상향 조정 가능.

---

## 6. 개발 계획

### 6.1 Sprint 구성 (Codex m13 대응 — 일정 조정)

| Sprint | 내용 | 기간 | 비고 |
|--------|------|------|------|
| Sprint 0 | 피처 엔지니어링 (추정가 제외 피처셋 + 신규 8개 + 누수 테스트) | 3일 | 시계열 누수 방지 검증 포함 |
| Sprint 1 | Model-A (Quantile) + Model-B (Estimate) 학습 + 개별 평가 | 3일 | 두 모델 독립 평가 |
| Sprint 2 | Quantile Calibration + Segment Calibration + 라운딩 | 2일 | coverage 보정 + 라운딩 검증 |
| Sprint 3 | 기존 엔진 재학습(v2) + 통합 파이프라인 테스트 | 2일 | covariate shift 검증 |
| Sprint 4 | API 확장 + 문서화 + 최종 검증 | 2일 | 게이트 전체 확인 |

**총: 12일** (이전 7일에서 상향)

### 6.2 코드 산출물

```
src/visionai/price_engine/
├── estimate_generator/               # 신규 모듈
│   ├── __init__.py
│   ├── hedonic_features.py          # 추정가-독립 피처 빌더
│   ├── quantile_model.py            # Model-A: CatBoost MultiQuantile
│   ├── estimate_model.py            # Model-B: CatBoost RMSE (추정가 재현)
│   ├── quantile_calibrator.py       # coverage 기반 분위수 보정
│   ├── estimate_calibrator.py       # 가격대별 편향 보정
│   ├── market_rounder.py            # 호 단위 라운딩
│   └── generator.py                 # Model-A + Model-B 통합 파이프라인
├── features/
│   └── hedonic_stats.py             # 신규: artist_median, trend, unsold_rate 등
├── models/
│   └── target_transform_v2.py       # 기존 엔진 재학습 버전 (생성 추정가 기반)

tests/price_engine/
├── test_hedonic_features.py
├── test_quantile_model.py
├── test_estimate_model.py
├── test_market_rounder.py
├── test_estimate_generator.py       # 통합 테스트
├── test_estimate_leakage.py         # 누수 방지 테스트 (8개 규칙)
└── test_cold_start_estimate.py      # Cold Start 전용 테스트

scripts/
├── train_estimate_models.py         # Model-A + Model-B 학습
├── validate_estimate_models.py      # 개별 + 통합 평가
└── retrain_price_engine_v2.py       # 기존 엔진 재학습
```

### 6.3 데이터 분할 전략

기존 Phase 1~2의 시계열 분할을 **4-way로 확장** (Codex 3회차 MAJOR 대응 — 후처리 낙관 편향 방지):

- **Train**: 초기 ~ 회차 N-3 (모델 학습)
- **Calib**: 회차 N-2 (후처리 파라미터 학습: smearing, ratio, quantile calibration)
- **Validation**: 회차 N-1 (성능 평가 — 후처리 학습에 사용하지 않음)
- **Test**: 회차 N (최종 검증)

> **핵심 원칙:** 후처리 파라미터는 **Calib**에서만 학습하고, **Validation**에서 평가한다. Validation에서 후처리를 학습하고 동일 Validation에서 평가하면 낙관 편향이 발생한다.

**누수 방지 규칙 (8개) — 피처 + 후처리 파라미터 포함 (Codex 2회차 MAJOR 대응):**

**피처 누수 방지 (4개):**
1. 작가/매체/경매유형 통계: strict < cutoff 회차만 사용
2. 동일 회차 내 타 lot 정보 혼입 금지
3. Test set의 낙찰가/추정가를 Train/Valid에 사용 금지
4. Model-B의 추정가 타깃은 Test set에서 평가에만 사용

**후처리 파라미터 누수 방지 (4개):**
5. `smearing_factor(segment)`: **평가 대상보다 시간적으로 이전인 데이터**에서만 계산
6. `segment_ratios (ratio_low/high)`: 동일 원칙 — 평가 대상보다 이전 데이터에서만 학습
7. `quantile_calibration 파라미터`: 동일 원칙
8. 기존 엔진 v2의 OOF 추정가: Train 내부 K-Fold OOF로 생성 (4.2.1절 참조)

**원칙 (Codex 6회차 CRITICAL 대응 — Step 5 모순 완전 해소):**

후처리 파라미터는 **평가 대상 세트와 독립인 시간적 이전 블록**에서 학습한다. 4-way 분할에서 각 경로의 후처리 학습 위치는 아래와 같이 **단일 정의**로 통일한다:

| 평가 경로 | 모델 학습 범위 | 후처리 학습 블록 | 평가 대상 |
|----------|--------------|----------------|----------|
| Validation 평가 | Train | **Calib** | Validation |
| Test 평가 | Train + Calib | **Validation** (Calib_final) | Test |

- Validation 평가 시: 후처리는 Calib에서 학습, Validation에서 평가
- Test 평가 시: 모델은 Train+Calib로 재학습, 후처리는 **Validation(Calib_final)**에서 학습, Test에서 평가
- Validation을 Test 경로의 Calib_final로 재사용하는 것은 **모델 선택/게이트 판단 이후**에 수행되므로, 모델 선택 편향을 유발하지 않는다. 이 시점에서 Validation의 역할은 "성능 평가 완료 → 후처리 파라미터 산출 원천"으로 전환된다.
- Test set 정보는 어떤 경로에서도 후처리 파라미터에 유입되지 않는다.

---

## 7. 리스크 및 완화 전략

| # | 리스크 | 영향 | 완화 |
|---|--------|------|------|
| 1 | 추정가 없이 R² 하락 | Hedonic 모델 정확도 저하 | 신규 피처 6개 + 작가 통계 강화 |
| 2 | **목적함수 불일치** (C1) | 낙찰가 학습 vs 추정가 평가 괴리 | Model-A/B 목적 분리로 해소 |
| 3 | **Covariate shift** (C3) | 생성 추정가→기존 엔진 정확도 하락 | 기존 엔진 재학습(v2) + 직접 예측 병행 |
| 4 | **Smearing 오용** (C2) | 분위수 의미 파괴 | Model-A: smearing 없음, Model-B만 적용 |
| 5 | **Cold Start fallback 부재** (C4) | 신규 작가 예측 실패 | CatBoost NaN 처리 + 그룹 피처 + D등급 |
| 6 | 분위수 교차 (M5) | 비논리적 결과 | MultiQuantile 또는 isotonic rearrangement |
| 7 | 시계열 누수 (M6) | 과적합, 실전 성능 하락 | 8개 누수 방지 규칙 + 단위 테스트 |
| 8 | 한국 시장 과소 반영 (M7) | 실무 적합성 저하 | 추가 피처(size_ho, unsold_rate) + 향후 확장 |
| 9 | 평가 지표 혼합 (M8) | 모델 선택 혼란 | 목적별 지표 분리 (A/B/C 그룹) |
| 10 | 호 라운딩 후 범위 왜곡 (m11) | Coverage 하락, mid 불일치 | low/mid/high 모두 라운딩 |
| 11 | 일정 리스크 (m13) | 품질 저하 | 12일로 상향 조정 |
| 12 | **유찰 selection bias** (5회차) | 낙찰 작품만 학습 → 저유동성 작가/Cold Start 작가에서 상향 편향 | `artist_unsold_rate` 피처 + 리스크 표시 (아래 상세) |

> **유찰 selection bias 상세 (Codex 5회차 MAJOR 대응):**
> Model-A/B는 낙찰(sold)된 작품의 가격만 학습한다. 유찰(unsold) 작품은 관측된 가격이 없어 학습에서 제외되므로, 모델은 "경매에 출품되어 팔린 작품"의 조건부 분포만 학습한다. 이는 저유동성 작가나 비인기 장르에서 체계적 상향 편향을 유발할 수 있다 (survivorship bias).
>
> **현재 완화 조치 (Codex 7회차 MAJOR 대응 — 예측 수준 보정 추가):**
> 1. `artist_unsold_rate` 피처로 유찰 경향을 간접 반영
> 2. **예측 구간 자동 확장 (prediction-level 보정):** 저유동성 작가(artist_unsold_rate > 50% 또는 해당 그룹 유찰률 > 40%)의 예측 구간을 **1.3배 확장**한다. 이는 sold-only 학습에서 발생하는 상향 편향의 불확실성을 구간 너비에 반영하기 위한 보수적 조치이다.
>   ```
>   if artist_unsold_rate > 0.5 or group_unsold_rate > 0.4:
>       interval_width *= 1.3  # 구간 확장
>       confidence_grade = max(confidence_grade, 'C')  # C등급 이하로 하향
>   ```
> 3. Pre-auction valuation (시나리오 D)에서 유찰률이 높은 작가(>50%)는 신뢰도 C등급 이하 + 경고 표시
> 4. Cold Start 작가의 경우, 해당 `medium_category × auction_type` 그룹의 유찰률도 함께 보고
>
> **향후 개선 (v2 검토):**
> - Heckman selection model 또는 Two-Part model (sale probability + conditional price)로 selection bias 직접 보정
> - 유찰 데이터를 censored observation으로 취급하는 Tobit/survival model 검토

---

## 8. 참고 문헌

1. Rosen, S. (1974). "Hedonic Prices and Implicit Markets: Product Differentiation in Pure Competition." *J. Political Economy*, 82, 34-55.
2. Koenker, R. & Bassett, G. (1978). "Regression Quantiles." *Econometrica*, 46, 33-50.
3. Renneboog, L. & Spaenjers, C. (2013). "Buying Beauty: On Prices and Returns in the Art Market." *Management Science*, 59(1), 36-53.
4. Goetzmann, W. (1993). "Accounting for Taste: Art and the Financial Markets Over Three Centuries." *American Economic Review*, 83(5), 1370-1376.
5. Mei, J. & Moses, M. (2002). "Art as an Investment and the Underperformance of Masterpieces." *American Economic Review*, 92(5), 1656-1668.
6. Scorcu, A. & Zanola, R. (2011). "The Right Price for Art Collectibles: A Quantile Hedonic Regression Investigation of Picasso Paintings." *J. Cultural Economics*, 35(4), 257-275.
7. Duan, N. (1983). "Smearing Estimate: A Nonparametric Retransformation Method." *JASA*, 78(383), 605-610.
8. Koenker, R. (2005). *Quantile Regression*. Cambridge University Press. (Ch. 2.3: Equivariance properties)
9. Kim, K. & Kim, J.B. (2024). "Two-step model based on XGBoost for predicting artwork prices in auction markets." *Int. J. Knowledge-based and Intelligent Engineering Systems*, 28(1), 1-14.
10. Garay, U., Puggioni, G., Molina, G. & ter Horst, E. (2022). "A Bayesian dynamic hedonic regression model for art prices." *J. Business Research*, 151, 310-323.
11. Fraiberger, S., Sinatra, R., Resch, M., Riedl, C. & Barabasi, A.-L. (2018). "Quantifying reputation and success in art." *Science*, 362(6416), 825-829.
12. Lee, Y. & Kim, S. (2011). "Price determinants and genre effects in the Korean art market: a partial linear analysis of size effect." *J. Cultural Economics*, 35(4), 301-320.
13. Park, J. et al. (2025). "The paradox of being unsold: hidden signaling value of bought-in in Korean art auction." *J. Cultural Economics*, 49(1), 89-112.
14. Mei, J., Moses, M., Walty, J. & Yang, Y. (2025). "Deep Learning for Art Market Valuation." *arXiv:2512.23078*.
15. Fraiberger, S. et al. (2024). "Social signals predict contemporary art prices better than visual features." *Scientific Reports*, 14, 11615.
16. Kuzma, E. et al. (2024). "Tabular Data Models for Predicting Art Auction Results." *Applied Sciences*, 14(23), 11006.
17. Bondell, H., Reich, B. & Wang, H. (2010). "Noncrossing quantile regression curve estimation." *Biometrics*, 66(4), 1055-1065.
18. Chanel, O., Gerard-Varet, L.-A. & Ginsburgh, V. (1996). "The relevance of hedonic price indices." *European Economic Review*, 40(3-5), 509-519.
19. Ashenfelter, O. & Graddy, K. (2003). "Auctions and the Price of Art." *J. Economic Literature*, 41(3), 763-787.

---

## 9. 요약

**핵심 아이디어:**
- **목적 분리**: Model-A (낙찰가 분위수) + Model-B (추정가 재현) 독립 최적화
- Hedonic Pricing (Rosen, 1974) 기반, 추정가 없이 작품 속성만으로 가격 예측
- Model-A: CatBoost MultiQuantile (τ=0.25, 0.50, 0.75), smearing 없이 exp 직접 역변환
- Model-B: CatBoost RMSE로 ln(추정가 중앙) 예측, Duan smearing 적용
- 기존 엔진 통합 시 **covariate shift 대응**: 재학습(v2) 필수
- 한국 시장 특수성: 호 단위 블록 프라이싱, 유찰 시그널링, 세그먼트별 차등 경고
- Cold Start: CatBoost NaN 처리 + 그룹 피처 + 신뢰도 D등급

**기대 효과:**
1. 추정가 없이도 독립적 가치 평가 가능 (Model-A)
2. K-Auction 전문가 추정가의 적정성 검증 도구 (Model-B vs 실제)
3. 기존 엔진과 안전한 통합 (재학습으로 covariate shift 해소)
4. 사전 경매 가치 평가(Pre-auction Valuation) 지원
5. Cold Start 작가 포함 전체 작품 커버리지

---

## 10. Codex 리뷰 이력

| 회차 | 결과 | 주요 피드백 | 대응 |
|------|------|-----------|------|
| 1회 | MAJOR revision | C1~C4 (4 CRITICAL), M5~M10 (6 MAJOR), m11~m13 (3 MINOR) | v2.0 전면 개정 |
| 2회 | MAJOR revision | 1 CRITICAL (OOF 절차), 3 MAJOR (Cold Start 품질, 세그먼트 smearing, 후처리 누수), 2 MINOR (G9 불일치, pinball loss) | v3.0 개정 |
| 3회 | MAJOR revision | 1 CRITICAL (OOF 후처리 체인), 3 MAJOR (Cold Start shrinkage, bin 설계, calib/eval 분리), 1 MINOR (규칙 수 불일치) | v4.0 개정 |
| 4회 | MAJOR revision | 3 MAJOR (후처리 학습 위치 충돌, v2 입력 정의 미완, Cold Start 평균 이상치), 3 MINOR (40호 변곡점, quantile calibration 미정의, Cold Start 품질 게이트 부재) | v5.0 개정 |
| 5회 | MAJOR revision | 1 CRITICAL (Step5 Valid 재사용), 2 MAJOR (quantile calibration conformal 과장, selection bias 미반영), 2 MINOR (피처 수 불일치, 에디션 파싱 미명시) | v6.0 개정 |
| 6회 | MAJOR revision | 1 CRITICAL (Step5 Valid 모순 잔존), 4 MAJOR (calibration-gate 목표 불일치, medium_x_auction_avg 피처 누락, Range Width 근거 오류, selection bias 게이트 부재) | v7.0 개정 |
| 7회 | MAJOR revision | 2 MAJOR (quantile vs prediction interval 혼용, selection bias 예측 수준 미보정), 2 MINOR (Model-A 라운딩 불일치, sparse-history 안정화 미명시) | v8.0 개정 |

**1회차 CRITICAL 해소 확인 (2회차 검증):**
- C1 (타깃/평가 불일치) → ✅ 해소 (Model-A/B 목적 분리)
- C2 (smearing 오용) → ✅ 해소 (분위수에 smearing 없음)
- C3 (covariate shift) → ⚠️ 부분 → v3.0에서 OOF 절차 + 분포 정렬 검증 추가
- C4 (Cold Start 설계 부재) → ⚠️ 부분 → v3.0에서 3-tier fallback + 품질 검증 추가

**2회차 대응 요약:**
- CRITICAL (OOF 부재) → 4.2.1절 OOF 생성 추정가 절차 신설 + 분포 정렬 PSI 검증
- MAJOR (Cold Start 품질) → 3-tier 그룹 fallback (매체×경매유형 → 매체 → 전체) + slice 분석
- MAJOR (Global smearing) → 세그먼트별 smearing factor + bootstrap 안정성 검증
- MAJOR (후처리 누수) → 누수 방지 규칙 6개 → 8개 확장 (후처리 4개 추가)
- MINOR (G9 불일치) → "8개 규칙" 으로 수정
- MINOR (pinball loss) → Pinball Loss + Interval Score를 주 지표로 승격, R²는 보조

**3회차 대응 요약:**
- CRITICAL (OOF 후처리 체인 미정의) → 4.2.1절 완전 재작성: Fold별 Calib 블록에서 후처리 파라미터 산출 → Predict에 적용하는 완전한 생성 체인 정의. v2 학습 입력 = smearing+ratio 적용된 최종 추정가
- MAJOR (Cold Start shrinkage) → Tier별 min_count(30/50), Bayesian shrinkage 공식, 발동률 모니터링, 품질 방어 vs 생성 보장 명시 구분
- MAJOR (Segment bin 설계) → 고정 가격대 bin → adaptive quantile bin (각 ~20% 데이터). 인접 bin 병합으로 희소 구간 해소
- MAJOR (Calib/Eval 분리) → 3-way(Train/Valid/Test) → 4-way(Train/Calib/Valid/Test). 후처리는 Calib에서 학습, Valid에서 평가
- MINOR (규칙 수 불일치) → 코드/리스크 표 모두 "8개" 통일

**7회차 대응 요약:**
- MAJOR (quantile vs prediction interval 혼용) → 3.2.1절 완전 재작성: "Raw Quantile"과 "Calibrated Prediction Interval" 용어 분리. calibration 이후 출력은 "예측 구간"으로 지칭. 게이트 평가 기준도 raw/calibrated 분리 명시 (Pinball Loss는 raw, Coverage/Range Width는 calibrated)
- MAJOR (selection bias 예측 수준 미보정) → 저유동성 작가(unsold_rate > 50%)에 대해 예측 구간 1.3배 자동 확장 + 신뢰도 C등급 이하 하향. 예측 자체를 보정하는 prediction-level 메커니즘 추가
- MINOR (Model-A 라운딩 불일치) → 파이프라인 다이어그램에서 Model-A를 "(라운딩 없음)"으로 수정. 3.6절 제목도 "Model-B 전용"으로 변경. 생성 코드에 "라운딩 없음" 주석 추가
- MINOR (sparse-history 안정화) → 신규 피처별 min_count, NaN 처리, shrinkage 규칙 명시. near-cold start(1~4건) 구간의 노이즈 억제 규칙 추가

**6회차 대응 요약:**
- CRITICAL (Step5 Valid 모순 잔존) → 6.3절 후처리 누수 방지 규칙을 "평가 경로별 후처리 학습 위치 표"로 완전 재작성. Validation 평가 경로(Calib에서 학습)와 Test 평가 경로(Validation=Calib_final에서 학습)를 단일 표로 명시. Validation의 이중 역할(성능 평가 → Calib_final 전환)의 정당성을 모델 선택 이후 시점 전환으로 설명
- MAJOR (calibration-gate 목표 불일치) → calibration grid search 목표를 이론적 50%에서 게이트 기준 55%로 상향. 메이저 slice 58% 별도 보정 검토 추가
- MAJOR (medium_x_auction_avg 누락) → 피처 목록에 #8로 추가 (총 23개 = 15 유지 + 8 신규). Cold Start prior와 피처 스키마 연결 완료
- MAJOR (Range Width 근거 오류) → G4 근거를 "추정가 범위 ratio"에서 "Model-A 예측 구간 폭"으로 수정. 상한 0.8→1.2로 조정 (예측 구간은 추정가 범위보다 넓을 수 있음)
- MAJOR (selection bias 게이트 부재) → G11 신설: artist_unsold_rate > 50% 작가 slice MAPE < 50%. 게이트 12개로 확장

**5회차 대응 요약:**
- CRITICAL (Step5 Valid 재사용) → Step 5 완전 재작성: 4-way 분할(Train/Calib/Valid/Test)에서 Valid는 성능 평가에만 사용. Model-B_final은 Train+Calib로 학습, Validation은 Calib_final 역할(후처리 파라미터 산출)에만 사용하며 모델 학습에 포함하지 않음을 명시
- MAJOR (quantile calibration conformal 과장) → "conformal-style" 용어를 "휴리스틱 additive 보정"으로 수정. finite-sample coverage 미보장 한계 명시. 향후 split conformal 전환 가능성 언급
- MAJOR (selection bias 미반영) → 리스크 #12 신설 (유찰 selection bias). 현재 완화 조치(unsold_rate, 신뢰도 경고) + 향후 Heckman/Two-Part model 검토 명시
- MINOR (피처 수 불일치) → "신규 6개" → "신규 7개"로 통일, Sprint 0 설명도 수정
- MINOR (에디션 파싱) → 에디션 파싱 regex 패턴, 성공률 기준(≥80%), 미달 시 제외 규칙 명시

**4회차 대응 요약:**
- MAJOR (후처리 학습 위치 충돌) → 3.3/6.3 모두 "Calib set" 기준으로 통일. 후처리 파라미터 학습 위치 통일 원칙 신설
- MAJOR (v2 입력 정의 미완) → Step 4에서 OOF 추정가로 대체되는 4개 파생 피처(estimate_mid, estimate_range, estimate_ratio, ln_estimate_mid)를 명시. v2는 기존 엔진과 동일한 21개 피처 구조 유지
- MAJOR (Cold Start 평균 이상치) → shrinkage를 log-price 스케일에서 수행하도록 변경. heavy-tailed 분포에서 기하 평균 효과로 이상치 영향 완화
- MINOR (40호 변곡점) → `size_ho_above40 = max(0, size_ho - 40)` hinge 피처 추가 (총 22개 피처)
- MINOR (quantile calibration 미정의) → 3.2.1절 신설: conformal-style additive 보정 절차 명시
- MINOR (Cold Start 품질 게이트 부재) → G9 (Cold Start MAPE < 60%) 신설 → 게이트 11개로 확장

---

*본 기획서는 학술 문헌 19편의 근거를 바탕으로 작성되었으며, Codex 7회 리뷰를 반영한 v8.0입니다.*
