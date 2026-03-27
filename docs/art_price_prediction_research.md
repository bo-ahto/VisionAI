# 미술품 경매 가격 예측 리서치 보고서

> **프로젝트**: VisionAI — 가격 예측 AI 파트
> **작성일**: 2026-03-20
> **목적**: 경매 미술품 가격 예측 공식 도출을 위한 학술 논문 기반 지식 정리

---

## 1. 문제 정의: 미술품 가격 예측이란?

미술품 가격 예측(Art Price Prediction)은 경매 전(pre-auction) 또는 경매 시점에 작품의 낙찰가(hammer price)를 추정하는 문제다. 핵심적으로 두 가지 접근이 존재한다.

1. **가격 수준 예측(Price Level Prediction)**: 개별 작품이 경매에서 얼마에 낙찰될지 절대값을 예측
2. **가격 지수 추정(Price Index Estimation)**: 미술 시장 전체 또는 특정 세그먼트의 가격 변동 추세를 추적

VisionAI 프로젝트에서는 **개별 작품의 낙찰가 예측**이 핵심이며, 시계열 가격 지수는 피처로 활용한다.

---

## 2. 피처 엔지니어링: 가격을 결정하는 변수들

학술 연구에서 밝혀진 미술품 경매 가격의 주요 결정 변수를 카테고리별로 정리한다.

### 2.1 작가(Artist) 관련 피처

| 변수 | 설명 | 영향도 |
|------|------|--------|
| **작가 정체성(Artist Identity)** | 작가 고유 ID — 가격의 가장 강력한 결정인자 | ★★★★★ |
| **작가 명성(Reputation)** | 전시 이력, 수상, 미술관 소장 여부 등으로 산출 | ★★★★★ |
| **생존 여부(Living Status)** | 사망 작가의 작품이 통계적으로 유의하게 높은 가격 | ★★★★ |
| **작가 나이(Age at Creation)** | 제작 시점 작가 나이, 다항식(polynomial) 형태로 사용 | ★★★ |
| **과거 경매 이력** | 과거 낙찰률(sell-through rate), 평균 낙찰가 | ★★★★ |
| **경력 단계(Career Stage)** | 초기/중기/후기 작품 여부 | ★★★ |

**핵심 인사이트**: 작가 정체성과 과거 거래 이력이 예측력의 가장 큰 부분을 차지한다. 2025년 arxiv 논문(Deep Learning for Art Market Valuation)에서도 "artist identity and prior transaction history dominate overall predictive power"라 보고했다.

### 2.2 작품(Artwork) 물리적 특성

| 변수 | 설명 | 영향도 |
|------|------|--------|
| **크기(Dimensions)** | 높이 × 너비, 면적(surface area). 일반적으로 크기가 클수록 가격 상승 | ★★★★ |
| **매체/재료(Medium)** | 유화(oil), 아크릴(acrylic), 수채화(watercolor), 판화(print) 등 | ★★★★ |
| **지지체(Support)** | 캔버스, 종이, 패널, 혼합 등 | ★★★ |
| **장르/주제(Genre/Subject)** | 초상화, 풍경화, 추상화, 정물화 등 | ★★★ |
| **서명 여부(Signed)** | 작가 서명이 있는 경우 가격 프리미엄 | ★★★ |
| **제작 연도(Year Created)** | 절대 연도 및 작가 전체 활동기간 내 상대 위치 | ★★★ |
| **제목(Title)** | 구체적 제목 vs "Untitled" — 구체적 제목이 높은 가격 | ★★ |

### 2.3 출처/이력(Provenance) 관련 피처

| 변수 | 설명 | 영향도 |
|------|------|--------|
| **소장 이력(Ownership History)** | 유명 컬렉터/미술관 소장 여부 | ★★★★★ |
| **전시 이력(Exhibition History)** | 주요 전시 참여 횟수 및 기관 수준 | ★★★★ |
| **문헌 수록(Literature)** | 학술 논문, 카탈로그 레조네 수록 여부 | ★★★★ |
| **인증(Certification)** | 감정서, 진품 인증 여부 | ★★★ |

**핵심 인사이트**: Harvard 연구(Puzzling Art Market Relationships)에서 출처(Provenance)가 모든 가격 범위에서 프리미엄을 생성하며, 대형/중형/소형 경매소를 불문하고 유의미한 효과가 있음을 확인했다.

### 2.4 거래/시장(Transaction & Market) 관련 피처

| 변수 | 설명 | 영향도 |
|------|------|--------|
| **경매소(Auction House)** | Christie's/Sotheby's는 유의하게 높은 평균 낙찰가 | ★★★★ |
| **경매 일시(Auction Date)** | 시즌성(봄/가을 메이저 세일), 경기 사이클 반영 | ★★★★ |
| **경매 위치(Location)** | 뉴욕, 런던, 홍콩 등 시장별 차이 | ★★★ |
| **판매 순서(Lot Order)** | 같은 경매 내 출품 순서 | ★★ |
| **추정가(Estimate)** | 경매소 제공 사전 추정가 (low/high) — 매우 강력한 피처 | ★★★★★ |
| **거시경제 지표** | S&P500, GDP 성장률, 미술시장 지수 등 | ★★★ |

### 2.5 비전(Visual) 피처 — 멀티모달 접근

| 변수 | 설명 | 추출 방법 |
|------|------|-----------|
| **스타일 임베딩** | 작품 이미지의 고수준 스타일 벡터 | ResNet, EfficientNet, ViT |
| **색채 조화(Color Harmony)** | 색상 분포, 대비, 조화도 | CNN 또는 수동 추출 |
| **구도 균형(Composition)** | 시각적 무게 분포, 대칭성 | CNN feature map |
| **텍스처 풍부도(Texture)** | 질감의 복잡도 및 다양성 | Gabor filter, CNN |

**핵심 인사이트**: 시각 피처는 과거 거래 이력이 없는 "신규 시장 진입 작품(fresh-to-market works)"에서 특히 중요하다. 기존 거래 앵커가 없을 때 이미지 임베딩이 유의미한 기여를 한다.

---

## 3. 수학적 프레임워크: 가격 예측 공식

### 3.1 헤도닉 가격 모델 (Hedonic Pricing Model)

미술 경제학의 표준 접근법. 작품 가격을 관찰 가능한 특성들의 함수로 모델링한다.

**기본 공식:**

```
ln(P_i) = α + Σ_j β_j · X_ij + Σ_t γ_t · D_t + ε_i
```

- `P_i`: 작품 i의 낙찰가
- `X_ij`: 작품 i의 j번째 특성 변수 (크기, 매체, 작가 등)
- `D_t`: 시간 더미 변수 (시장 추세 반영)
- `β_j`: 각 특성의 가격 기여 계수
- `γ_t`: 시간별 가격 지수
- `ε_i`: 오차항

**특징:**
- 종속변수를 log-price로 사용 (분포 정규화, 해석 용이)
- 계수 β_j는 해당 특성의 가격 탄력성으로 해석 가능
- OLS(Ordinary Least Squares)로 추정하며, 분위수 회귀(Quantile Regression)로 확장 가능

### 3.2 반복 판매 모델 (Repeat Sales Model)

같은 작품이 두 번 이상 경매에 출품된 데이터를 활용한다.

**기본 공식:**

```
ln(P_i,t2) - ln(P_i,t1) = Σ_t γ_t · (D_i,t2 - D_i,t1) + η_i
```

- 같은 작품의 두 번째 판매가와 첫 번째 판매가의 로그 차이를 시간 더미에 회귀
- 작품 고유 특성이 차분으로 제거되어 순수 시장 변동만 추정
- Mei & Moses(2002)가 이 방법으로 미술품 투자 수익률을 최초 체계적으로 추정

**한계:**
- 반복 판매 데이터만 사용 가능 → 데이터 손실 큼
- 선택 편향(selection bias): 재판매되는 작품은 무작위가 아님

### 3.3 하이브리드 모델 (Hybrid/Combined Approach)

헤도닉과 반복 판매의 장점을 결합한다.

**기본 공식:**

```
ln(P_i,t) = α + Σ_j β_j · X_ij + Σ_t γ_t · D_t + λ · IMR_i + ε_i
```

- `IMR_i`: Heckman의 Inverse Mills Ratio (선택 편향 보정)
- 1단계: 반복 판매 여부를 probit/logit으로 모델링
- 2단계: IMR을 포함한 헤도닉 회귀 수행

**중국 회화 시장 연구**(Cogent Economics & Finance, 2018)에서 하이브리드 모델이 가장 신뢰할 수 있는 가격 지수 추정치를 제공한다고 보고했다.

### 3.4 머신러닝 기반 비선형 모델

전통적 선형 모델의 한계를 극복하기 위한 접근이다.

**일반화된 예측 함수:**

```
P̂_i = f(X_artist, X_artwork, X_provenance, X_market, X_visual; θ)
```

- `f`: 비선형 학습 함수 (GBM, Neural Network 등)
- `X_visual`: CNN으로 추출한 이미지 임베딩 벡터
- `θ`: 학습 파라미터

**Two-Step XGBoost 접근** (Kim & Kim, 2024):
1. Step 1: 이진 분류 — 작품이 추정가 이상으로 낙찰될지 예측
2. Step 2: 회귀 — 구간별로 분리된 데이터에서 정밀 가격 예측

### 3.5 멀티모달 딥러닝 통합 모델

가장 최신 접근으로, 이종 데이터를 하나의 모델에서 융합한다.

**아키텍처 구조:**

```
Input Layer:
  ├── Image  →  CNN Encoder (ResNet/EfficientNet/ViT)  →  v_visual
  ├── Text   →  Text Encoder (BERT/TF-IDF)             →  v_text
  └── Tabular → MLP / Embedding Layer                  →  v_tabular

Fusion Layer:
  v_fused = Concat(v_visual, v_text, v_tabular)
  또는 Attention-based Fusion

Prediction Head:
  P̂ = MLP(v_fused) 또는 LSTM(v_fused, t) for 시계열
```

**성능 보고 (문헌 기반):**

| 모델 | MAPE | 비고 |
|------|------|------|
| OLS Hedonic Regression | ~45-55% | 전통적 기준선 |
| Random Forest | ~35-40% | 비선형 포착 |
| XGBoost | ~30-35% | 범주형 피처에 강점 |
| CatBoost | ~28-33% | 범주형 자동 처리, 순서 부스팅 |
| LightGBM | ~27-32% | 대규모 데이터에 빠른 학습 |
| CNN + Tabular (멀티모달) | ~30% | 이미지 피처 포함 시 |
| CNN-LSTM Fusion | ~25-30% | 시계열 + 이미지 결합 |

> 주의: MAPE 수치는 데이터셋, 기간, 세그먼트에 따라 크게 달라진다. 위 수치는 여러 논문의 범위를 종합한 참고치다.

---

## 4. 모델 아키텍처 비교

### 4.1 Baseline: 전통 통계 모델

| 모델 | 장점 | 단점 |
|------|------|------|
| OLS Hedonic | 해석 가능성, 경제학적 기반 | 비선형 관계 포착 불가 |
| Quantile Regression | 가격 분포 전체 모델링 | 복잡한 상호작용 포착 제한 |
| Bayesian Dynamic Hedonic | 시간 변동 계수, 불확실성 정량화 | 계산 비용 높음 |

### 4.2 Gradient Boosted Trees (GBM 계열)

로드맵에 명시된 GBM/CatBoost 접근의 핵심이다.

| 모델 | 특징 | 미술품 가격 예측 적합성 |
|------|------|-------------------------|
| **XGBoost** | 정규화 강함, 결측값 처리 내장 | 범주형 변수가 많은 미술 데이터에 적합 |
| **CatBoost** | 범주형 변수 자동 인코딩, 순서형 부스팅으로 과적합 방지 | ★★★★★ 작가명, 매체, 장르 등 고카디널리티 범주형 변수에 최적 |
| **LightGBM** | Leaf-wise 성장, 대규모 데이터에 빠른 학습 | 대규모 경매 데이터셋에 유리 |

**CatBoost가 미술품 도메인에서 유리한 이유:**
- 작가명(수천~수만 카테고리), 경매소, 매체, 장르 등 고카디널리티 범주형 변수가 핵심 피처
- CatBoost의 Ordered Target Encoding이 이런 변수를 자동으로 효과적으로 인코딩
- Target leakage를 방지하는 순서형 부스팅(Ordered Boosting)

### 4.3 딥러닝 모델

| 모델 | 용도 | 입력 |
|------|------|------|
| **ResNet/EfficientNet** | 이미지 피처 추출 | 작품 이미지 |
| **ViT (Vision Transformer)** | 고수준 시각 패턴 | 작품 이미지 |
| **BERT** | 텍스트 피처 (설명, 제목) | 작품 설명문 |
| **LSTM/Transformer** | 시계열 가격 추세 | 과거 경매 가격 시퀀스 |
| **MLP Fusion Head** | 멀티모달 통합 예측 | 융합된 벡터 |

### 4.4 Two-Step (분류 → 회귀) 접근

Kim & Kim(2024)의 논문에서 제안한 구조로, 미술품 가격 분포의 극단적 비대칭성을 다루는 데 효과적이다.

```
Step 1: Binary Classification
  "이 작품이 추정가(estimate) 이상으로 낙찰될 것인가?" → Yes/No

Step 2: Conditional Regression
  - Yes 그룹: 상향 프리미엄 크기 예측
  - No 그룹: 하향 할인 크기 예측
```

---

## 5. VisionAI 프로젝트 적용을 위한 제안

### 5.1 제안 예측 공식 프레임워크

VisionAI 로드맵의 "베이스라인 → 고도화" 전략에 맞춘 3단계 접근을 제안한다.

**Phase 1 — Baseline (Hedonic + GBM)**

```
ln(P̂) = CatBoost(X_artist, X_artwork, X_provenance, X_market)
```

- 피처: 정형 데이터만 사용
- 모델: CatBoost (범주형 변수 최적)
- 평가: MAPE 기준선 확보
- 일정: 2026-03-02 ~ 2026-03-13 (베이스라인 기간)

**Phase 2 — Feature Engineering & Model Enhancement**

```
ln(P̂) = Ensemble(CatBoost, LightGBM, XGBoost)(X_artist, X_artwork, X_provenance, X_market, X_derived)
```

- 추가 피처: 작가 경력 통계, 시장 트렌드 변수, 상호작용 피처
- 앙상블: Stacking 또는 Weighted Average
- 일정: 2026-03-09 ~ 2026-04-10 (피처 엔지니어링/모델 고도화 기간)

**Phase 3 — Multimodal Integration**

```
P̂ = MLP_head(
  Concat(
    CatBoost_embedding(X_tabular),
    CNN_encoder(Image),
    optional: BERT_encoder(Description)
  )
)
```

- Vision AI 결과물(이미지 임베딩)을 가격 예측에 통합
- 시계열 컴포넌트 추가 (LSTM 또는 Temporal Fusion Transformer)

### 5.2 성과지표 기준

로드맵의 성과지표가 MAPE인 점을 감안한 목표치 제안:

| 단계 | 목표 MAPE | 비고 |
|------|-----------|------|
| Baseline | < 45% | 헤도닉 회귀 수준 |
| GBM 최적화 | < 35% | CatBoost 단독 |
| 앙상블 | < 30% | 다중 모델 스태킹 |
| 멀티모달 | < 25% | 이미지 + 정형 융합 |

### 5.3 데이터 요구사항

최소한 다음 필드를 포함하는 경매 데이터가 필요하다:

- **필수**: 작가명, 작품 제목, 매체, 크기(높이×너비), 제작 연도, 경매소, 경매 일시, 추정가(low/high), 낙찰가
- **권장**: 서명 여부, 출처(provenance) 텍스트, 전시 이력, 문헌 수록 여부, 작품 이미지
- **보강**: 작가 생몰년, 국적, 과거 경매 통계(낙찰률, 평균가), 거시경제 지표

---

## 6. 핵심 참고 논문 목록

| # | 논문/출처 | 핵심 기여 | 연도 |
|---|-----------|-----------|------|
| 1 | Deep Learning for Art Market Valuation (arXiv:2512.23078) | 딥러닝 vs 전통 모델 대규모 벤치마크, 1970-2024 데이터 | 2025 |
| 2 | Two-step model based on XGBoost (Kim & Kim, KES Journal) | 분류→회귀 2단계 접근법 | 2024 |
| 3 | Tabular Data Models for Predicting Art Auction Results (MDPI Applied Sciences) | 13개 정형 데이터 모델 비교 | 2024 |
| 4 | ML Algorithms and Fine Art Pricing (Expert Systems with Applications) | 남아공 미술시장 ML vs 회귀 비교 | 2025 |
| 5 | Machines and Masterpieces (Northeastern/HAL) | GBM 기반 경매가 예측 대규모 연구 | 2020 |
| 6 | Multimodal Approach for Painting Price Prediction (IEEE) | CNN + BERT + MLP 멀티모달 융합 | 2023 |
| 7 | Painting2Auction: Siamese CNN and LSTM (Stanford CS230) | 시각 유사도 + 시계열 결합 | 2020 |
| 8 | Hedonic, Repeat Sales, and Hybrid Models: Chinese Paintings (Cogent Economics) | 3가지 가격 지수 방법 비교 | 2018 |
| 9 | Mei & Moses Art Index | 반복 판매 기반 미술 투자 수익률 | 2002 |
| 10 | Pricing Art and the Art of Pricing (European Financial Management) | 미술 경매 수익률과 리스크 분석 | 2022 |
| 11 | Artwork Pricing Model Integrating Popularity and Ability (AStA) | 작가 명성 + 능력 통합 모델 | 2024 |
| 12 | Determinants of Price at Auctions of Contemporary Art (MDPI Arts) | 12명 현대 작가 경매가 결정 요인 | 2022 |

---

## 7. 용어 정리

| 용어 | 설명 |
|------|------|
| **Hedonic Pricing** | 재화의 가격을 구성 특성들의 함수로 분해하는 경제학적 방법론 |
| **Repeat Sales** | 동일 작품의 재판매 데이터를 이용한 가격 지수 추정 방법 |
| **MAPE** | Mean Absolute Percentage Error — 예측 오차율(%) |
| **Hammer Price** | 경매 낙찰가 (수수료 미포함) |
| **Buyer's Premium** | 낙찰가에 추가되는 경매소 수수료 |
| **Estimate** | 경매소가 사전에 제시하는 예상 가격 범위 (Low~High) |
| **Provenance** | 작품의 소유 이력 및 출처 |
| **Catalogue Raisonné** | 특정 작가의 모든 알려진 작품을 체계적으로 수록한 목록 |
| **Sell-through Rate** | 경매 출품작 중 실제 낙찰된 비율 |
| **Fresh-to-Market** | 최근 경매 이력이 없는 작품 (첫 출품 또는 장기 미출품) |

---

*본 문서는 VisionAI 가격 예측 AI 파트의 기초 리서치 자료로, 구체적인 모델 구현 및 실험 설계의 근거로 활용한다.*
