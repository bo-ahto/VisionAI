# 미술품 경매 가격 예측 시스템 기술 명세서

> **프로젝트**: VisionAI — 가격 예측 AI
> **버전**: v1.1
> **작성일**: 2026-03-24
> **목적**: 경매 미술품 가격 예측 모델 구현을 위한 시스템 설계, 수학적 근거, 데이터 요구사항, 아키텍처 종합 정리

---

## 1. 시스템 목표 및 범위

### 1.1 목표

경매 출품 미술품의 **낙찰가(hammer price)**를 사전에 예측하는 ML 시스템을 구축한다.

### 1.2 범위

- **입력**: 작품 메타데이터(작가, 크기, 재료, 추정가 등) + 작품 이미지(Phase 3)
- **출력**: 예측 낙찰가(원), 신뢰 구간, 추정가 대비 프리미엄/디스카운트 확률
- **성과지표**: MAPE (Mean Absolute Percentage Error)

### 1.3 단계별 목표

| Phase | 기간 | 목표 MAPE | 모델 | 데이터 |
|-------|------|-----------|------|--------|
| 1 — Baseline | 2026-03 ~ 2026-03 | < 40% | CatBoost 단독 | 현재 보유 정형 데이터 |
| 2 — 고도화 | 2026-03 ~ 2026-04 | < 30% | GBM 앙상블 | 보강 피처 추가 |
| 3 — 멀티모달 | 2026-04 이후 | < 25% | GBM + CNN Fusion | 이미지 임베딩 통합 |

---

## 2. 수학적 기반: 가격 예측 공식 및 출처

미술품 가격 예측의 수학적 근거는 경제학의 헤도닉 가격 이론에서 출발한다.

### 2.1 헤도닉 가격 모델 (Hedonic Pricing Model)

**이론적 근거**:
Rosen(1974)이 정립한 헤도닉 가격 이론은 이질적 재화(heterogeneous goods)의 가격을 구성 특성들의 함수로 분해한다. 미술품은 전형적인 이질적 재화이므로 이 프레임워크가 자연스럽게 적용된다.

**공식**:

```
ln(P_i) = α + Σ_{j=1}^{J} β_j · X_{ij} + Σ_{t=1}^{T} γ_t · D_{it} + ε_i
```

| 기호 | 의미 | 예시 |
|------|------|------|
| P_i | 작품 i의 낙찰가 | 42억 원 |
| X_{ij} | 작품 i의 j번째 특성 변수 | 크기, 매체, 작가 등 |
| D_{it} | 시간 더미 변수 | 2025-Q4 = 1, 나머지 = 0 |
| β_j | 특성 j의 암묵 가격(implicit price) | 유화 프리미엄 계수 |
| γ_t | 시간 t의 시장 가격 지수 | 2025년 시장 상황 |
| α | 절편 | 기본 가격 수준 |
| ε_i | 오차항 | N(0, σ²) |

**종속변수로 ln(P)를 사용하는 이유**:
1. 미술품 가격은 극단적 우편향(right-skewed) 분포 → 로그 변환으로 정규화
2. 계수 β_j를 "X가 1단위 증가할 때 가격이 β_j × 100% 변화"로 해석 가능
3. 이분산성(heteroscedasticity) 완화

> **출처**: Rosen, S. (1974). "Hedonic Prices and Implicit Markets: Product Differentiation in Pure Competition." *Journal of Political Economy*, 82(1), 34-55.
> https://www.scirp.org/reference/referencespapers?referenceid=1956852

---

### 2.2 반복 판매 회귀 (Repeat Sales Regression, RSR)

동일 작품의 재판매 데이터를 이용하여 시장 가격 지수를 추정하는 방법이다. Mei & Moses(2002)가 미술 시장에 본격 적용했다.

**공식**:

```
r_i = ln(P_{i,t_s}) - ln(P_{i,t_b}) = Σ_{t=t_b+1}^{t_s} γ_t · D_t + η_i
```

| 기호 | 의미 |
|------|------|
| r_i | 작품 i의 로그 수익률 |
| P_{i,t_s} | 판매 시점(t_s)의 낙찰가 |
| P_{i,t_b} | 구매 시점(t_b)의 낙찰가 |
| γ_t | 기간 t의 시장 수익률 |
| D_t | 시간 더미 |
| η_i | 오차항 |

**장점**: 작품 고유 특성이 차분으로 제거되어, 순수 시장 변동만 추정
**단점**: 재판매 데이터만 사용 가능 → 관측치 대량 손실, 선택 편향

> **출처**: Mei, J. & Moses, M. (2002). "Art as an Investment and the Underperformance of Masterpieces." *American Economic Review*, 92(5), 1656-1668.
> https://papers.ssrn.com/sol3/papers.cfm?abstract_id=311701

**본 프로젝트 활용 방안**: RSR로 직접 가격을 예측하지 않고, RSR로 추정한 **시장 가격 지수(γ_t)를 피처로 사용**하여 ML 모델에 투입한다.

---

### 2.3 Two-Step 모델 (분류 → 회귀)

Kim & Kim(2024)이 **한국 미술 경매 데이터**를 대상으로 제안한 모델이다. 미술품 가격의 극단적 비대칭 분포를 다루기 위해 2단계 접근을 사용한다.

**공식**:

```
Step 1 — 가격 클래스 분류:
  ŷ_class = Classifier(X)    → {저가, 중가, 고가}

Step 2 — 클래스별 회귀:
  P̂ = Regressor_k(X)         (k = ŷ_class)
```

| 단계 | 모델 | 입력 | 출력 |
|------|------|------|------|
| Step 1 | XGBoost Classifier | 작품 메타데이터 | 가격 클래스 (저/중/고) |
| Step 2 | XGBoost Regressor ×3 | 작품 메타데이터 | 클래스별 예측 가격 |

**성능**: 한국 경매 데이터에서 헤도닉 모델 대비 MAPE가 약 절반으로 감소

> **출처**: Kim, K. & Kim, J.B. (2024). "Two-step model based on XGBoost for predicting artwork prices in auction markets." *International Journal of Knowledge Engineering and Soft Data Paradigms (KES)*.
> https://journals.sagepub.com/doi/10.3233/KES-230041

---

### 2.4 ML 기반 비선형 예측 모델

전통적 선형 모델의 한계를 극복하기 위한 일반화된 프레임워크이다.

**공식**:

```
ln(P̂_i) = f(X_i; θ) + b
```

여기서 f는 비선형 학습 함수(GBM, Neural Network 등)이고, 학습 목표는:

```
θ* = argmin_θ  (1/N) Σ_{i=1}^{N} L(ln(P_i), f(X_i; θ))
```

**손실 함수 L 선택**:

| 손실 함수 | 공식 | 특징 |
|-----------|------|------|
| MSE | (y - ŷ)² | 이상치에 민감, 기본 |
| MAE | \|y - ŷ\| | 이상치에 강건 |
| Huber | δ²(√(1+((y-ŷ)/δ)²)-1) | MSE/MAE 절충 |
| Quantile | τ·max(y-ŷ,0) + (1-τ)·max(ŷ-y,0) | 분위수별 예측 가능 |

**본 프로젝트 권장**: log-price 타겟 + Huber Loss (미술품 가격의 이상치에 강건)

---

### 2.5 멀티모달 융합 모델

이미지, 텍스트, 정형 데이터를 단일 모델에서 결합하는 최신 접근이다.

**아키텍처 공식**:

```
v_visual  = ImageEncoder(I_i)           ∈ R^d_v     (ResNet-50 or ViT)
v_text    = TextEncoder(T_i)            ∈ R^d_t     (BERT or TF-IDF)
v_tabular = TabularEncoder(X_i)         ∈ R^d_x     (MLP or Embedding)

v_fused   = FusionLayer(v_visual, v_text, v_tabular)  ∈ R^d_f

ln(P̂_i)  = PredictionHead(v_fused)     ∈ R^1
```

**Fusion 전략 비교**:

| 전략 | 공식 | 장점 |
|------|------|------|
| Concatenation | v_f = [v_v; v_t; v_x] | 단순, 기본 |
| Attention | v_f = Σ α_k · v_k | 모달리티 중요도 학습 |
| Gated Fusion | v_f = σ(W·[v_v;v_x]) ⊙ v_v + (1-σ) ⊙ v_x | 정보 흐름 제어 |

> **출처**: Aubry, M. et al. (2025). "Deep Learning for Art Market Valuation." arXiv:2512.23078.
> https://arxiv.org/abs/2512.23078
>
> Bento, N. et al. (2024). "Tabular Data Models for Predicting Art Auction Results." *Applied Sciences*, 14(23), 11006.
> https://www.mdpi.com/2076-3417/14/23/11006

---

## 3. 성과지표 정의

### 3.1 MAPE (Mean Absolute Percentage Error)

프로젝트 로드맵에 명시된 핵심 성과지표이다.

**공식**:

```
MAPE = (100% / N) × Σ_{i=1}^{N} |P_i - P̂_i| / P_i
```

**주의사항**:
- P_i = 0인 경우(유찰 등) 제외 필요
- 저가 작품에서 MAPE가 과대 평가되는 경향 → 가격 구간별 MAPE 분리 보고 권장

### 3.2 보조 지표

| 지표 | 공식 | 용도 |
|------|------|------|
| RMSE | √(Σ(P-P̂)²/N) | 절대 오차 크기 |
| R² | 1 - SS_res/SS_tot | 설명력 |
| MdAPE | Median(\|P-P̂\|/P) | 이상치 강건 중앙값 |
| Within-20% | (\|P-P̂\|/P < 0.2인 비율) | 실용적 정확도 |
| Premium Accuracy | 추정가 대비 프리미엄 방향 적중률 | 비즈니스 지표 |

---

## 4. 데이터 수집 요구사항

### 4.1 필수 데이터 (현재 보유 확인됨)

현재 43,770건 작품 / 3,286 작가 / 705 경매 회차 데이터를 보유하고 있다.

```
┌─────────────────────────────────────────────────────────┐
│  artwork 테이블 (작품 단위 — 예측의 기본 단위)            │
├─────────────────────────────────────────────────────────┤
│  artwork_id        PK    고유 식별자                      │
│  artist_name       STR   작가명                          │
│  title_ko          STR   작품명(한글)                     │
│  title_en          STR   작품명(영문)                     │
│  medium            STR   재질/재료 (예: "캔버스에 유채")    │
│  dimensions_raw    STR   크기 원본 (예: "81×116cm")       │
│  estimate_low      INT   추정가 최저 (원)                 │
│  estimate_high     INT   추정가 최고 (원)                 │
│  hammer_price      INT   낙찰가 (원) ← TARGET 변수       │
│  auction_id        FK    경매 회차 참조                    │
│  lot_number        INT   LOT 번호                        │
│  bid_count         INT   입찰 수                         │
│  sale_status       STR   상태 (낙찰/유찰)                 │
│  auction_type      STR   타입 (메이저/온라인)              │
│  source            STR   소스 (offline_artwork 등)        │
│  image_url         STR   작품 이미지 URL                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  auction 테이블 (경매 회차 단위)                          │
├─────────────────────────────────────────────────────────┤
│  auction_id        PK    고유 식별자                      │
│  sale_no           STR   SALE NO                        │
│  auction_type      STR   유형 (ONLINE / 메이저 등)        │
│  title_ko          STR   경매 제목(한글)                  │
│  title_en          STR   경매 제목(영문)                  │
│  auction_date      DATE  경매 일자                       │
│  total_lots        INT   총 LOT 수                      │
│  sold_count        INT   낙찰 건수                       │
│  sell_through_rate FLOAT 낙찰률                          │
│  total_amount      INT   총 낙찰액                       │
│  max_price         INT   최고 낙찰가                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  artist_stats 테이블 (작가 통계 — 집계 테이블)            │
├─────────────────────────────────────────────────────────┤
│  artist_name       PK    작가명                          │
│  total_sold        INT   총 낙찰 건수                    │
│  total_amount      INT   총 낙찰액                       │
│  max_price         INT   최고 낙찰가                     │
│  avg_price         INT   평균 낙찰가                     │
└─────────────────────────────────────────────────────────┘
```

### 4.2 보강 필요 데이터 (우선순위순)

```
┌─────────────────────────────────────────────────────────────┐
│  🔴 우선순위 1: 작품 제작 연도                                │
│  ───────────────────────────────────────────────────────────│
│  필드: year_created (INT)                                    │
│  수집: 경매 카탈로그 크롤링 또는 DB 필드 추가                    │
│  활용: 작가 경력 내 위치, 시대별 트렌드                         │
│  예측력 기여: ★★★★                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔴 우선순위 2: 작가 생몰년 및 국적                            │
│  ───────────────────────────────────────────────────────────│
│  필드: birth_year, death_year, nationality (INT, INT, STR)   │
│  수집: 한국미술정보센터, ArtNet, Wikidata SPARQL               │
│  활용: 생존 여부(death premium), 경력 단계, 국적별 시장 차이     │
│  예측력 기여: ★★★★                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🟡 우선순위 3: 거시경제 지표                                  │
│  ───────────────────────────────────────────────────────────│
│  필드: kospi, snp500, art_market_index, usd_krw              │
│  수집: 한국은행 API, Yahoo Finance, Artnet Index              │
│  활용: 시장 사이클, 경기 민감도                                 │
│  예측력 기여: ★★★                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🟢 우선순위 4: 출처/전시 이력 (장기)                           │
│  ───────────────────────────────────────────────────────────│
│  필드: provenance_text, exhibition_count, literature_count    │
│  수집: 경매 카탈로그 상세 크롤링                                │
│  활용: 출처 프리미엄, 전시 이력 프리미엄                         │
│  예측력 기여: ★★★★★ (확보 시 강력하나 수집 난이도 높음)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 피처 엔지니어링 명세

### 5.1 원본 피처 → 모델 입력 변환

```
[크기 파싱]
  dimensions_raw: "81×116cm"
  → height_cm:     81.0       (FLOAT)
  → width_cm:      116.0      (FLOAT)
  → surface_area:  9,396.0    (height × width)
  → aspect_ratio:  0.698      (height / width)
  → size_category: "대형"      (0~2000: 소형, 2000~8000: 중형, 8000+: 대형)

  dimensions_raw: "高48"
  → height_cm:     48.0
  → width_cm:      NULL       (결측 → 3D 작품은 높이만)
  → is_3d:         True

[재질 파싱]
  medium: "캔버스에 유채"
  → medium_category: "유화"           (유화/아크릴/수채/판화/혼합/조각/기타)
  → support_category: "캔버스"         (캔버스/종이/패널/보드/기타)

  medium: "Bronze, Aluminium, Stainless Steel, Urethan paint"
  → medium_category: "조각"
  → support_category: "금속"

[추정가 파생]
  estimate_low:  100만, estimate_high: 300만
  → estimate_mid:    200만             ((low + high) / 2)
  → estimate_range:  200만             (high - low)
  → estimate_ratio:  3.0               (high / low — 불확실성 proxy)
  → ln_estimate_mid: 14.51             (log 변환)

[작가 통계 파생]
  artist_stats 조인 후:
  → artist_total_sold:     610
  → artist_total_amount:   50,292,940,000
  → artist_max_price:      1,520,000,000
  → artist_avg_price:      82,447,443
  → artist_price_tier:     "상위 1%"    (전체 작가 중 위치)

[시간 파생]
  auction_date: "2025-11-15"
  → sale_year:     2025
  → sale_month:    11
  → sale_quarter:  Q4
  → sale_season:   "가을"     (봄: 3-5, 가을: 9-11, 기타)
  → is_major_sale: True       (메이저 경매 시즌)

[제목 파생]
  title: "Untitled"
  → is_untitled:   True
  → title_lang:    "영문"
  → title_length:  8
```

### 5.2 Phase 2 고급 파생 피처

```
[작가 경력 동적 피처] — 시계열 기반, 예측 시점까지의 데이터만 사용
  → artist_recent_avg_3:    최근 3건 평균 낙찰가
  → artist_recent_avg_10:   최근 10건 평균 낙찰가
  → artist_price_trend:     최근 10건 선형 회귀 기울기 (상승/하락)
  → artist_price_volatility: 최근 20건 낙찰가 표준편차
  → artist_sell_rate:       최근 낙찰률
  → artist_days_since_last: 마지막 경매로부터 경과 일수
  → artist_annual_frequency: 연간 출품 횟수

[추정가 대비 과거 실적]
  → artist_premium_ratio_avg: 해당 작가의 역대 추정가 대비 낙찰가 비율 평균
  → artist_premium_ratio_std: 상동 표준편차

[시장 컨텍스트]
  → market_heat_30d:        최근 30일 전체 낙찰률
  → market_avg_premium_30d: 최근 30일 추정가 대비 낙찰가 비율
  → same_medium_recent_avg: 동일 매체 최근 30일 평균 낙찰가
```

### 5.3 ⚠️ 시계열 누수(Leakage) 방지 원칙

```
핵심 원칙: 예측 시점(t) 이후의 데이터는 절대 사용 불가

올바른 예시:
  2025-11-15 경매 작품 예측 시
  → artist_recent_avg_3: 2025-11-14 이전 최근 3건만 사용 ✅

잘못된 예시:
  → artist_avg_price: 전체 기간 평균 (미래 데이터 포함) ❌

데이터 분할:
  학습 데이터: ~ 2024-12-31
  검증 데이터: 2025-01-01 ~ 2025-06-30
  테스트 데이터: 2025-07-01 ~
  (절대 랜덤 분할 사용 금지 — 시계열 분할 필수)
```

---

## 5-A. 결측값(Missing Value) 처리 전략 및 변수 기여도

실무에서 모든 피처가 완벽하게 수집되는 경우는 드물다. 결측 발생 시 모델 성능을 유지하기 위한 체계적인 처리 전략이 필요하다.

### 5-A.1 피처별 결측 시나리오 및 디폴트 전략

```
┌────────────────────────────────────────────────────────────────────────┐
│  결측 등급 분류                                                         │
│                                                                        │
│  Level A — 필수 피처 (결측 시 예측 불가, 반드시 수집)                       │
│  Level B — 핵심 피처 (결측 시 디폴트 대체, 정확도 하락 경고)                │
│  Level C — 보강 피처 (결측 허용, 디폴트 또는 모델 자체 처리)                │
│  Level D — 선택 피처 (결측이 일반적, 있으면 보너스)                        │
└────────────────────────────────────────────────────────────────────────┘
```

| 피처 | 결측 등급 | 예상 결측률 | 디폴트 전략 | 디폴트 값 | 근거 |
|------|----------|-----------|-----------|----------|------|
| **artist_name** | A 필수 | ~0% | 결측 시 예측 거부 | — | 가격의 최대 결정인자, 대체 불가 |
| **estimate_low/high** | A 필수 | ~5% | 결측 시 예측 거부 | — | 가장 강력한 단일 피처 |
| **hammer_price** (타겟) | A 필수 | 유찰 시 없음 | 유찰 건은 학습 데이터에서 제외 | — | 타겟 변수 |
| **dimensions** | B 핵심 | ~10% | 동일 작가 중앙값 대체 | artist_median_area | 작가별 선호 크기 존재 |
| **medium** | B 핵심 | ~5% | "기타(unknown)" 카테고리 | "unknown" | CatBoost가 카테고리로 학습 |
| **auction_date** | B 핵심 | ~0% | — | — | 경매 기본 정보 |
| **auction_type** | B 핵심 | ~0% | — | — | 경매 기본 정보 |
| **lot_number** | C 보강 | ~15% | 경매 총 LOT의 중앙값 | total_lots / 2 | 중간 순서 가정 |
| **bid_count** | C 보강 | ~20% | NaN 유지 (CatBoost 자체 처리) | NaN | 사전 예측 시 미사용 |
| **year_created** | C 보강 | ~40% | 작가 활동 중앙 연도 | (birth+death)/2+30 | 생몰년 기반 추정 |
| **birth_year** | C 보강 | ~30% | NaN 유지 + 파생 피처 비활성화 | NaN | 관련 파생 피처 스킵 |
| **nationality** | C 보강 | ~25% | "unknown" 카테고리 | "unknown" | 카테고리 학습 |
| **provenance** | D 선택 | ~80% | 바이너리: 0 (이력 없음) | 0 | 이력 있음=1, 없음=0 |
| **exhibition_count** | D 선택 | ~85% | 0 (전시 이력 없음으로 간주) | 0 | 정보 없음 ≈ 적은 이력 |
| **image_url** | D 선택 | ~60% | Phase 3에서만 사용, 없으면 스킵 | — | 정형 모델에선 불필요 |

### 5-A.2 결측 대체 공식

**원칙**: 단순 전역 평균이 아닌 **조건부 대체(conditional imputation)**를 사용한다.

```
[크기(dimensions) 결측 시]

  1순위: 동일 작가의 동일 매체 작품 크기 중앙값
         area_default = median(area | artist=A, medium=M)

  2순위: 동일 작가 전체 작품 크기 중앙값
         area_default = median(area | artist=A)

  3순위: 동일 매체 전체 크기 중앙값
         area_default = median(area | medium=M)

  4순위: 전체 데이터 크기 중앙값 (최후 수단)
         area_default = median(area)


[작가 통계(artist_stats) 결측 시 — 신규 작가]

  문제: 학습 데이터에 없는 신규 작가가 예측 시점에 등장

  전략: "Cold Start" 처리

  1순위: 동일 매체 + 유사 추정가 구간 작가들의 평균 통계
         stats_default = mean(stats | medium=M, estimate_tier=T)

  2순위: 동일 추정가 구간의 전체 작가 평균 통계
         stats_default = mean(stats | estimate_tier=T)

  추정가 구간(estimate_tier) 분류:
    · 하위: < 500만 원
    · 중하: 500만 ~ 3,000만 원
    · 중상: 3,000만 ~ 1억 원
    · 상위: 1억 ~ 10억 원
    · 최상: > 10억 원

  + 신규 작가 플래그 피처 추가:
    is_new_artist = 1 (학습 데이터에 없는 작가)


[추정가 결측 시]

  원칙: 추정가는 Level A 필수 피처이므로 결측 시 예측 거부가 기본

  예외 — 내부 추정가 생성 모델:
  추정가 자체가 없는 일부 경매소의 경우, 별도 "추정가 예측 모델"을 구축하여
  추정가를 먼저 예측한 후 가격 예측 모델에 투입하는 2단계 파이프라인 가능

  est_mid = EstimateModel(artist, medium, size, auction_type)
  → 이 경우 est_source = "predicted" 플래그 추가
  → 예측 신뢰도에 패널티 반영
```

### 5-A.3 결측 처리 방법 비교 및 선택

| 방법 | 설명 | 장점 | 단점 | 적용 대상 |
|------|------|------|------|-----------|
| **CatBoost 내장 처리** | NaN을 자동으로 최적 분기에 할당 | 구현 간단, 별도 전처리 불필요 | 결측 패턴을 학습에 의존 | 수치형 피처 전체 |
| **조건부 중앙값 대체** | 그룹별 중앙값으로 대체 | 도메인 지식 반영, 편향 적음 | 그룹이 작으면 불안정 | dimensions, year_created |
| **"unknown" 카테고리** | 결측을 별도 카테고리로 처리 | 결측 자체가 정보가 됨 | 카테고리 수 증가 | 범주형 피처 (medium, nationality) |
| **플래그 + 디폴트** | is_missing 플래그 + 디폴트값 | 모델이 결측 여부를 학습 | 피처 수 2배 증가 | 기여도 높은 피처 |
| **예측 기반 대체** | 별도 모델로 결측값 예측 | 가장 정확 | 복잡도 높음, 오차 전파 위험 | 추정가 (Level A 예외) |

**본 프로젝트 권장 조합**:

```
수치형 피처:
  → CatBoost 내장 NaN 처리 (기본)
  → dimensions: 조건부 중앙값 대체 + is_size_imputed 플래그

범주형 피처:
  → "unknown" 카테고리 추가

작가 통계 (신규 작가):
  → 추정가 구간 기반 조건부 대체 + is_new_artist 플래그

추정가 (Level A):
  → 결측 시 예측 거부 (기본)
  → 옵션: 추정가 예측 서브모델 + est_source 플래그
```

### 5-A.4 변수 기여도(Feature Importance) 및 결측 시 영향도

변수 기여도를 정량화하여, 결측 시 예측 정확도 하락 정도를 사전에 파악한다.

**기여도 측정 방법**:

| 방법 | 공식/설명 | 특징 |
|------|----------|------|
| **SHAP** | φ_j = Σ_{S⊆F\{j}} \|S\|!(F-\|S\|-1)!/\|F\|! · [f(S∪{j}) - f(S)] | 게임이론 기반, 각 예측에 대한 피처별 기여도 분해. 가장 신뢰성 높음 |
| **Permutation Importance** | PI_j = score_original - score_permuted(j) | 피처 j를 랜덤 셔플 후 성능 하락 측정. 모델에 무관 |
| **CatBoost Built-in** | 분기 시 각 피처의 loss 감소량 합산 | 학습 과정에서 자동 계산. 빠름 |

> **SHAP 출처**: Lundberg, S. & Lee, S. (2017). "A Unified Approach to Interpreting Model Predictions." *NeurIPS 2017*.
> https://arxiv.org/abs/1705.07874

**예상 변수 기여도 매핑 (문헌 + 실증 종합)**:

```
┌─────────────────────────────────────────────────────────────────┐
│  피처 기여도 예상 순위 (문헌 기반)                                  │
│                                                                  │
│  기여도                                                          │
│  ████████████████████████████████  32%  ln_estimate_mid          │
│  ██████████████████               18%  artist_name (identity)    │
│  █████████████                    13%  artist_avg_price          │
│  ████████                          9%  surface_area              │
│  ███████                           7%  medium_category           │
│  ██████                            6%  auction_type              │
│  █████                             5%  artist_price_trend        │
│  ████                              4%  sale_season               │
│  ███                               3%  estimate_ratio            │
│  ██                                2%  lot_number                │
│  █                                 1%  기타 (각각 <1%)            │
│                                                                  │
│  합계                            100%                            │
│                                                                  │
│  ※ 위 비율은 Aubry et al.(2025) 및 Bento et al.(2024)의           │
│    보고에 기반한 예상치이며, 실제 학습 후 SHAP으로 검증 필요           │
└─────────────────────────────────────────────────────────────────┘
```

> **기여도 근거**:
> - 추정가(estimate)가 최대 기여: Aubry et al.(2025)에서 "prior transaction history"가 지배적이라 보고, 추정가는 경매소가 과거 거래를 반영하여 산출하므로 이를 응축한 변수임
>   https://arxiv.org/abs/2512.23078
> - 작가 정체성(artist identity)이 2위: 동일 논문에서 "artist identity dominates overall predictive power"
> - 물리적 특성(크기, 매체)의 기여: Rosen(1974) 헤도닉 이론의 핵심 변수이며, Bento et al.(2024)에서 surface_area가 상위 5 피처에 포함
>   https://www.mdpi.com/2076-3417/14/23/11006

### 5-A.5 결측 시 예측 품질 등급

결측 피처에 따라 예측의 신뢰도를 자동으로 등급화하여 API 응답에 포함한다.

```
예측 품질 산출 공식:

  quality_score = Σ (w_j × available_j)    (j = 각 피처)

  available_j = 1 (피처 존재) 또는 0 (결측)
  w_j = 해당 피처의 기여도 가중치 (SHAP 기반)

등급 분류:
  ┌──────────────────────────────────────────────────────┐
  │  quality_score ≥ 0.90  →  Grade A (고신뢰)            │
  │  필수 피처 모두 존재 + 핵심 피처 대부분 존재              │
  │  예: 추정가 ✅ 작가 ✅ 크기 ✅ 재료 ✅ 작가통계 ✅        │
  │  → 예측값 그대로 서비스                                 │
  ├──────────────────────────────────────────────────────┤
  │  quality_score ≥ 0.70  →  Grade B (보통)              │
  │  필수 피처 존재 + 일부 핵심 피처 결측                     │
  │  예: 추정가 ✅ 작가 ✅ 크기 ❌ 재료 ✅ 작가통계 ✅        │
  │  → 예측값 + "정확도 제한" 경고 표시                      │
  ├──────────────────────────────────────────────────────┤
  │  quality_score ≥ 0.50  →  Grade C (저신뢰)            │
  │  필수 피처 존재 + 다수 핵심 피처 결측                     │
  │  예: 추정가 ✅ 작가 ✅(신규) 크기 ❌ 재료 ❌              │
  │  → 예측값 + "참고용" 경고 + 신뢰구간 확대(×1.5)          │
  ├──────────────────────────────────────────────────────┤
  │  quality_score < 0.50  →  Grade D (예측 거부)          │
  │  필수 피처 결측 또는 핵심 피처 대부분 결측                 │
  │  → 예측 거부, 추가 데이터 요청 메시지 반환                │
  └──────────────────────────────────────────────────────┘
```

**API 응답 확장 예시**:

```json
{
  "predicted_price": 3200000000,
  "prediction_quality": {
    "grade": "B",
    "score": 0.82,
    "missing_features": ["dimensions"],
    "imputed_features": [
      {
        "feature": "surface_area",
        "method": "artist_median",
        "imputed_value": 15120.0,
        "confidence_penalty": 0.09
      }
    ],
    "message": "크기 정보가 누락되어 작가 중앙값으로 대체했습니다. 정확도가 약간 제한될 수 있습니다."
  },
  "confidence_interval": {
    "low": 2200000000,
    "high": 4500000000
  }
}
```

### 5-A.6 Ablation Study 계획 — 피처 제거 시 성능 영향 측정

학습 완료 후, 각 피처 그룹을 체계적으로 제거하며 성능 변화를 측정한다. 이를 통해 결측 시 실제 영향을 정량화할 수 있다.

```
실험 설계:

  Baseline: 모든 피처 사용 → MAPE_full

  실험 1: 추정가 제거        → MAPE_no_est    → Δ₁ = MAPE_no_est - MAPE_full
  실험 2: 작가 통계 제거     → MAPE_no_artist  → Δ₂
  실험 3: 크기 피처 제거     → MAPE_no_size    → Δ₃
  실험 4: 재료 피처 제거     → MAPE_no_medium  → Δ₄
  실험 5: 시간 피처 제거     → MAPE_no_time    → Δ₅
  실험 6: 경매소 피처 제거   → MAPE_no_auction → Δ₆
  실험 7: 시장 컨텍스트 제거 → MAPE_no_market  → Δ₇

  각 Δ가 해당 피처 그룹의 "결측 시 예측 정확도 하락폭"

목적:
  - 결측 시 quality_score 가중치(w_j)를 실증적으로 보정
  - 데이터 수집 우선순위 재조정 근거 확보
  - Phase 2 피처 엔지니어링 방향 결정
```

> **Ablation Study 참고**: 머신러닝에서의 ablation study는 각 구성 요소의 기여도를 실증적으로 검증하는 표준 방법론이다.
> Meyes, R. et al. (2019). "Ablation Studies in Artificial Neural Networks." arXiv:1901.08644.
> https://arxiv.org/abs/1901.08644

---

## 6. 시스템 아키텍처

### 6.1 전체 파이프라인

```
┌──────────────────────────────────────────────────────────────────┐
│                     Art Price Prediction System                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐     │
│  │ Data Sources │    │ Feature Store│    │  Model Registry  │     │
│  │             │    │              │    │                  │     │
│  │ ·경매 DB     │───▶│ ·Raw 피처    │───▶│ ·CatBoost v1     │     │
│  │ ·작가 통계   │    │ ·파생 피처    │    │ ·LightGBM v1     │     │
│  │ ·작품 목록   │    │ ·시계열 피처  │    │ ·Ensemble v1     │     │
│  │ ·이미지 저장소│    │ ·이미지 임베딩│    │ ·Multimodal v1   │     │
│  │ ·외부 API   │    │              │    │                  │     │
│  └─────────────┘    └──────────────┘    └────────┬─────────┘     │
│                                                   │               │
│                                          ┌────────▼─────────┐    │
│                                          │  Prediction API   │    │
│                                          │                   │    │
│                                          │  POST /predict    │    │
│                                          │  ├─ 예측 낙찰가    │    │
│                                          │  ├─ 신뢰 구간      │    │
│                                          │  └─ 프리미엄 확률  │    │
│                                          └───────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Phase 1 — CatBoost Baseline 아키텍처

```
┌────────────────────────────────────────────────┐
│              Phase 1: CatBoost Baseline          │
├────────────────────────────────────────────────┤
│                                                  │
│  Input Features (22개)                           │
│  ─────────────────                               │
│  [범주형 — CatBoost 자동 인코딩]                    │
│   · artist_name          (3,286 카테고리)          │
│   · medium_category      (7 카테고리)              │
│   · support_category     (5 카테고리)              │
│   · auction_type         (2: 메이저/온라인)         │
│   · source               (경매소)                  │
│   · sale_season           (3: 봄/가을/기타)         │
│   · size_category        (3: 소/중/대)             │
│                                                  │
│  [수치형]                                         │
│   · ln_estimate_mid      (추정가 중앙값 로그)       │
│   · estimate_ratio       (추정가 범위 비율)         │
│   · height_cm, width_cm, surface_area             │
│   · aspect_ratio                                  │
│   · lot_number                                    │
│   · artist_total_sold                             │
│   · artist_avg_price                              │
│   · artist_max_price                              │
│   · artist_price_tier                             │
│   · auction_sell_rate                             │
│   · auction_total_lots                            │
│   · sale_year, sale_month                         │
│   · is_untitled                                   │
│                                                  │
│          │                                       │
│          ▼                                       │
│  ┌──────────────────┐                            │
│  │    CatBoost       │                            │
│  │  Regressor        │                            │
│  │                   │                            │
│  │  target: ln(P)    │                            │
│  │  loss: RMSE       │                            │
│  │  iterations: 3000 │                            │
│  │  depth: 8         │                            │
│  │  l2_reg: 5        │                            │
│  │  cat_features: 자동│                            │
│  └────────┬─────────┘                            │
│           │                                      │
│           ▼                                      │
│  Output: ln(P̂) → exp(ln(P̂)) = P̂ (원)           │
│                                                  │
└────────────────────────────────────────────────┘
```

**CatBoost 선택 근거**:
- 작가명(3,286 카테고리)처럼 고카디널리티 범주형 변수를 자동 처리
- Ordered Target Statistics로 target leakage 방지
- Ordered Boosting으로 과적합 억제

> **출처**: Prokhorenkova, L. et al. (2018). "CatBoost: unbiased boosting with categorical features." *NeurIPS 2018*.
> https://arxiv.org/abs/1706.09516

### 6.3 Phase 2 — GBM 앙상블 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│           Phase 2: Stacking Ensemble                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Input Features (35개 — Phase 1 + 파생 피처 13개 추가)      │
│                                                           │
│         ┌──────────┬──────────┬──────────┐               │
│         │          │          │          │               │
│         ▼          ▼          ▼          ▼               │
│   ┌──────────┐┌──────────┐┌──────────┐┌──────────┐      │
│   │ CatBoost ││ LightGBM ││ XGBoost  ││ Optional:│      │
│   │          ││          ││          ││ Ridge Reg│      │
│   │ depth:8  ││ leaves:  ││ depth:8  ││          │      │
│   │ iter:5k  ││ 255      ││ iter:5k  ││          │      │
│   └────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘      │
│        │           │           │           │             │
│        └───────┬───┘───────┬───┘───────────┘             │
│                │           │                             │
│                ▼           ▼                             │
│        ┌─────────────────────────┐                       │
│        │   Meta-Learner (Ridge)   │                       │
│        │                         │                       │
│        │   P̂_final = w1·P̂_cat    │                       │
│        │           + w2·P̂_lgb    │                       │
│        │           + w3·P̂_xgb    │                       │
│        │           + w4·P̂_ridge  │                       │
│        └────────────┬────────────┘                       │
│                     │                                    │
│                     ▼                                    │
│             Output: ln(P̂) → P̂ (원)                      │
│                                                           │
│  학습 방법: 5-Fold Time Series CV                          │
│  Meta-Learner 입력: OOF(Out-of-Fold) 예측값               │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 6.4 Phase 3 — 멀티모달 융합 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              Phase 3: Multimodal Fusion                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │  작품 이미지   │  │  작품 설명    │  │  정형 데이터        │     │
│  │  (224×224)   │  │  (텍스트)    │  │  (35개 피처)       │     │
│  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘     │
│         │                │                   │               │
│         ▼                ▼                   ▼               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐     │
│  │ Image Encoder│ │ Text Encoder │ │ Tabular Encoder  │     │
│  │              │ │              │ │                  │     │
│  │ EfficientNet │ │ KoBERT       │ │ CatBoost의       │     │
│  │ -B0 (frozen) │ │ (frozen)     │ │ leaf index 또는  │     │
│  │ → FC(512)    │ │ → FC(256)    │ │ MLP(256)         │     │
│  │              │ │              │ │                  │     │
│  │ v_img ∈ R^512│ │ v_txt ∈ R^256│ │ v_tab ∈ R^256    │     │
│  └──────┬──────┘ └──────┬──────┘ └────────┬─────────┘     │
│         │                │                   │               │
│         └────────────────┼───────────────────┘               │
│                          │                                   │
│                          ▼                                   │
│                 ┌─────────────────┐                          │
│                 │  Fusion Layer    │                          │
│                 │                 │                          │
│                 │  Concat → 1024  │                          │
│                 │  → BatchNorm    │                          │
│                 │  → Dropout(0.3) │                          │
│                 │  → FC(512)      │                          │
│                 │  → ReLU         │                          │
│                 │  → FC(256)      │                          │
│                 │  → ReLU         │                          │
│                 └────────┬────────┘                          │
│                          │                                   │
│                          ▼                                   │
│                 ┌─────────────────┐                          │
│                 │ Prediction Head  │                          │
│                 │                 │                          │
│                 │ FC(256) → FC(1) │                          │
│                 │ → ln(P̂)        │                          │
│                 └─────────────────┘                          │
│                                                               │
│  학습:                                                        │
│   · Loss: Huber(δ=1.0)                                       │
│   · Optimizer: AdamW (lr=1e-4, wd=1e-2)                      │
│   · Scheduler: CosineAnnealing                                │
│   · Image Encoder: 첫 10 epoch freeze → fine-tune             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

> **출처**: Aubry, M. et al. (2025)는 ResNet-50과 ViT-Small을 이미지 인코더로 벤치마크했으며, 시각 임베딩이 fresh-to-market 작품에서 유의미한 기여를 보고함.
> https://arxiv.org/abs/2512.23078

---

## 7. 학습 및 평가 파이프라인

### 7.1 데이터 분할 전략

```
전체 데이터: 43,770건 (낙찰 건만 사용)
──────────────────────────────────────────────────

시간순 정렬 후:

  ├── Train ──────────────┤── Valid ───┤── Test ──┤
  │   ~ 2024-06-30        │ 2024-07-01 │ 2025-01 │
  │   약 34,000건          │ ~ 2024-12  │ ~ 현재   │
  │                       │ 약 5,000건  │약 4,770건│
  └───────────────────────┴────────────┴─────────┘

  ❌ 절대 금지: 랜덤 셔플 분할 (시계열 누수 발생)
  ✅ 필수: 시간순 분할 (temporal split)
```

### 7.2 교차 검증: Time Series Expanding Window

```
Fold 1: Train [───────]  Valid [──]
Fold 2: Train [─────────]  Valid [──]
Fold 3: Train [───────────]  Valid [──]
Fold 4: Train [─────────────]  Valid [──]
Fold 5: Train [───────────────]  Valid [──]

각 Fold의 학습 데이터가 점점 커지는 Expanding Window 방식
→ 실제 서비스 상황(과거 데이터로 미래 예측)을 시뮬레이션
```

### 7.3 하이퍼파라미터 튜닝

```
도구: Optuna (Bayesian Optimization)

CatBoost 탐색 범위:
  iterations:      [1000, 10000]
  depth:           [4, 10]
  learning_rate:   [0.01, 0.3]
  l2_leaf_reg:     [1, 10]
  bagging_temp:    [0.0, 1.0]
  random_strength: [0.0, 10.0]

최적화 목표: Validation MAPE 최소화
Trial 수: 100~200
```

---

## 8. 추론(Inference) API 설계

### 8.1 엔드포인트

```
POST /predict_price

Request:
{
  "artist_name": "김환기",
  "title": "22-X-73 #325",
  "medium": "코튼에 유채",
  "dimensions": "182×132cm",
  "estimate_low": 3000000000,
  "estimate_high": 5000000000,
  "auction_type": "메이저",
  "auction_date": "2026-05-15",
  "source": "서울옥션",
  "lot_number": 36,
  "image_url": "https://..." (optional, Phase 3)
}

Response:
{
  "predicted_price": 3200000000,
  "predicted_price_formatted": "32.0억",
  "confidence_interval": {
    "low": 2400000000,
    "high": 4200000000
  },
  "premium_probability": {
    "above_high_estimate": 0.15,
    "within_estimate": 0.62,
    "below_low_estimate": 0.23
  },
  "model_version": "ensemble-v2.1",
  "feature_importance_top5": [
    {"feature": "ln_estimate_mid", "importance": 0.32},
    {"feature": "artist_avg_price", "importance": 0.18},
    {"feature": "surface_area", "importance": 0.09},
    {"feature": "artist_recent_avg_3", "importance": 0.08},
    {"feature": "medium_category", "importance": 0.06}
  ]
}
```

### 8.2 추론 최적화 (로드맵: Inference 최적화 파트)

| 항목 | 방법 | 목표 |
|------|------|------|
| 모델 포맷 | CatBoost → ONNX 변환 | 추론 속도 2~5배 향상 |
| 배치 추론 | NumPy 배치 처리 | 대량 예측 시 효율 |
| 캐시 | 작가 통계/피처 Redis 캐시 | 피처 계산 시간 단축 |
| 사전 계산 | 정적 피처 오프라인 계산 | 실시간 부하 감소 |
| 목표 지표 | p50 < 50ms, p95 < 200ms | API 응답 시간 |

---

## 9. 프로젝트 디렉토리 구조

```
VisionAI/
├── src/visionai/
│   ├── price_prediction/
│   │   ├── __init__.py
│   │   ├── config.py              # 설정 (dataclass)
│   │   ├── features/
│   │   │   ├── __init__.py
│   │   │   ├── dimension_parser.py # 크기 파싱
│   │   │   ├── medium_parser.py    # 재질 파싱
│   │   │   ├── artist_features.py  # 작가 통계 피처
│   │   │   ├── market_features.py  # 시장 컨텍스트 피처
│   │   │   ├── time_features.py    # 시간 파생 피처
│   │   │   └── pipeline.py         # 전체 피처 파이프라인
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── baseline.py         # CatBoost baseline
│   │   │   ├── ensemble.py         # Stacking ensemble
│   │   │   ├── multimodal.py       # CNN + Tabular fusion
│   │   │   └── two_step.py         # 분류→회귀 2단계
│   │   ├── evaluation/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py          # MAPE, RMSE 등
│   │   │   └── reports.py          # 평가 리포트 생성
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py           # 데이터 로딩
│   │   │   ├── splitter.py         # 시계열 분할
│   │   │   └── preprocessor.py     # 전처리
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── server.py           # FastAPI 서버
│   │       └── schemas.py          # 요청/응답 스키마
│   └── ...
├── tests/
│   └── test_price_prediction/
│       ├── test_features.py
│       ├── test_models.py
│       └── test_api.py
├── scripts/
│   ├── train_baseline.py
│   ├── train_ensemble.py
│   ├── evaluate_model.py
│   └── export_onnx.py
├── checkpoints/
│   └── price_prediction/           # 모델 체크포인트
└── docs/
    ├── art_price_prediction_research.md
    ├── data_feature_mapping.md
    └── price_prediction_system_spec.md   ← 본 문서
```

---

## 10. 핵심 참고 문헌

| # | 출처 | 주제 | URL |
|---|------|------|-----|
| 1 | Rosen (1974), *J. Political Economy* | 헤도닉 가격 이론 원본 | https://www.scirp.org/reference/referencespapers?referenceid=1956852 |
| 2 | Mei & Moses (2002), *AER* | 반복 판매 기반 미술품 투자 수익률 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=311701 |
| 3 | Kim & Kim (2024), *KES Journal* | Two-Step XGBoost 한국 경매 데이터 | https://journals.sagepub.com/doi/10.3233/KES-230041 |
| 4 | Prokhorenkova et al. (2018), *NeurIPS* | CatBoost 알고리즘 | https://arxiv.org/abs/1706.09516 |
| 5 | Aubry et al. (2025), *arXiv* | 딥러닝 + 시각 피처 미술 시장 가치 평가 | https://arxiv.org/abs/2512.23078 |
| 6 | Bento et al. (2024), *Applied Sciences* | 13개 정형 데이터 모델 경매 결과 예측 비교 | https://www.mdpi.com/2076-3417/14/23/11006 |
| 7 | Li et al. (2022), *European Financial Mgmt* | 미술 경매 수익률과 리스크 | https://onlinelibrary.wiley.com/doi/10.1111/eufm.12348 |
| 8 | Pownall & Graddy (2016), *Handbook* | 미술 시장 경매 메커니즘 | https://dash.harvard.edu/bitstreams/81f49de4-f38c-40d3-ab8a-c90d3483e4a8/download |
| 9 | Zhang et al. (2018), *Cogent Economics* | 헤도닉/반복판매/하이브리드 모델 비교 | https://www.tandfonline.com/doi/full/10.1080/23322039.2018.1443372 |
| 10 | MDPI Arts (2022) | 현대미술 12작가 경매가 결정 요인 | https://www.mdpi.com/2076-0752/11/3/66 |

---

*본 문서는 VisionAI 가격 예측 AI 시스템의 구현 기술 명세서로, 팀 내 공유 및 개발 착수를 위한 기준 문서로 활용한다.*
