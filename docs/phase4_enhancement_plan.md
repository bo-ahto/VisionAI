# Phase 4 가격 예측 고도화 기획서 (v14.0)

> **작성일**: 2026-03-28 | **개정일**: 2026-03-28 (v14.0 — Codex 리뷰 11차: fallback 법적·품질 게이트 완성)
> **목표**: MdAPE 34% → 31~33% (기본) / 29~31% (stretch) 개선 (추정가 없이)
> **기반**: Phase 3 결과 (Model-A MdAPE 34%, R² 0.621) + 학술 리서치 7편

---

## 1. 현행 시스템 한계 분석

### 1.1 Phase 3 성능

| 지표 | Phase 1-2 (추정가 있음) | Phase 3 (추정가 없음) | 격차 |
|------|----------------------|---------------------|------|
| MdAPE | ~20% | 34.1% | +14%p |
| R² | 0.936 | 0.621 | -0.315 |
| Within 30% | ~65% | 45.2% | -20%p |
| Cold Start MdAPE | — | ~50% | (Phase 3 model_test_results 기준) |

### 1.2 격차 원인 분석

추정가는 **전문가의 종합 판단**(comparable sales + 시장 심리 + consignor 협상 + 마케팅 전략)을 압축한 단일 변수였다. 이를 제거하면 해당 정보가 모두 사라진다.

**핵심 질문: 추정가에 담긴 정보를 다른 방법으로 복원할 수 있는가?**

### 1.3 이론적 상한

| 시나리오 | 달성 가능 R² | 비고 | 출처 |
|---------|------------|------|------|
| 추정가 포함 (경매사 전문가) | ~0.93 | 추정가가 지배적 변수 | Mei et al. (2025), 반복매매 데이터 |
| 반복매매 + rich features | ~0.77~0.79 | 이전 낙찰가 필수 | Mei et al. (2025), repeat-sale subset |
| Fresh-to-market, tabular only | ~0.54~0.59 | 거래 이력 없는 작품 | Mei et al. (2025) |
| Fresh-to-market, multimodal | ~0.61~0.65 | tabular + 이미지 | Mei et al. (2025) |
| 기본 Hedonic (현재 Phase 3) | ~0.40~0.62 | 데이터셋/피처에 따라 편차 큼 | 문헌 종합 |

> **주의:** MAPE/MdAPE는 논문마다 데이터셋, 가격 분포, metric 정의가 달라 직접 비교 불가. 위 R² 수치도 서양 대형 경매 데이터(Sotheby's/Christie's) 기반이므로 K-Auction 43,866건에 그대로 적용하기 어렵다. Mei et al. 세부 수치는 arXiv preprint 기반이며 테이블 단위 완전 재검증은 미완.

**현실적 목표: MdAPE 31~33% (기본), 29~31% (stretch), R² 0.64~0.68** (Tier 1+2 개선 후, 작가 레벨 통계 기반 추정이므로 실험 검증 필수)

---

## 2. 고도화 전략 (3-Tier 우선순위)

### Tier 1: 최고 영향 — MdAPE 34% → 31~33% (기존 CSV 데이터만 사용)

> **핵심 데이터 제약:** K-Auction 43,866건 중 45.9%의 작가가 1건만 보유 (sparse/cold artist). Tier 1 개선은 주로 warm artist(2건 이상)에 집중되며, cold artist에서의 효과는 제한적. 따라서 개선폭은 warm/cold 분리 측정이 필수.

#### 2.1 작가 이력 피처 고도화

**예상 효과:**
- Warm artist (54.1%): MdAPE -2~4%p (작가 레벨 통계 앵커 효과)
- Cold artist (45.9%): MdAPE -0~1%p (대부분 결측, 전역 통계 대체)
- **전체 가중 평균: -1~2.5%p**

**근거 및 한계:**
- Mei et al. (2025, *arXiv:2512.23078*): 반복매매 데이터에서 **동일 작품의 이전 낙찰가(prior transaction price)**가 R² 0.77~0.79 달성의 핵심.
- **핵심 차이:** 본 계획의 피처는 "동일 작품의 prior transaction price"가 아니라 **"작가 레벨 통계(평균, 최근 낙찰가, 모멘텀 등)"**임. 작가 레벨 정보는 동일 작품 이전 거래가보다 정보 강도가 현저히 약함. 따라서 Mei et al.의 R² 수치를 직접 개선폭 근거로 사용할 수 없으며, 방향성 참고만 가능.
- 실제 효과는 K-Auction 데이터에서 실험으로 확인 필수. warm artist 내에서도 작가별 거래 건수 분포에 따라 효과 편차 클 것으로 예상.

현재 Phase 3는 작가 통계 4개(avg/max/median/total_sold)만 사용. **10개 이상으로 확장:**

| # | 신규 피처 | 산출 방법 | 근거 |
|---|----------|----------|------|
| 1 | `artist_recent_avg_price` | 최근 3회차 평균 낙찰가 | 단기 시세 반영 |
| 2 | `artist_price_momentum` | (최근 3회차 평균) / (전체 평균) - 1 | 가격 모멘텀 |
| 3 | `artist_sale_frequency` | 회차당 평균 출품 수 | 시장 활성도 |
| 4 | `artist_auctions_since_last_sale` | 마지막 낙찰 이후 회차 수 | 희소성 시그널 |
| 5 | `artist_price_volatility` | 낙찰가 ln(price) 표준편차 | 가격 불확실성 |
| 6 | `artist_lot_count_trend` | 최근 5회차 출품 수 변화율 | 시장 관심 추세 |
| 7 | `artist_premium_ratio` | 메이저 경매 비중 | 작가 tier 시그널 |
| 8 | `artist_reappear_flag` | 동일 작가가 이전 회차에 출품 이력 있음 | 작가 시장 활성 시그널 |
| 9 | `artist_last_hammer_price` | 가장 최근 낙찰가 | warm artist 한정 앵커 |
| 10 | `artist_career_length` | 첫 출품 ~ 현재 회차 수 | 경력 성숙도 |

> **제약:** 1건 작가(45.9%)에게는 피처 1~6이 결측 또는 무의미. Bayesian shrinkage + `is_sparse_artist` 플래그로 안정화 필수.

#### 2.2 Warm/Cold 분리 평가 체계 구축

작가 이력 피처 추가 후 즉시 warm/cold slice별 MdAPE를 분리 측정. Tier 1 이후 전략 방향 결정의 핵심 근거.

```
평가 체계:
  - warm artist (거래 이력 ≥ 2건): 작가 이력 피처 전체 적용
  - cold artist (거래 이력 1건 이하): 전역 통계 대체, comp 매칭 의존
  - 분리 측정: warm MdAPE, cold MdAPE, 전체 MdAPE
  - warm 개선 < 3%p 시 피처 재설계, cold 악화 시 피처 제한
```

#### 2.3 유사 작품 매칭 (Comparable Sales) (예상 -0.5~2%p)

```
방법:
  1. 동일 작가 + 유사 크기(±20%) + 유사 매체
     → 이전 회차까지의 낙찰가 최근 3건 평균 (strict cutoff)
  2. 동일 매체 + 유사 크기(±20%) + 유사 제작연도(±10년)
     → 이전 회차까지의 낙찰가 최근 10건 평균 (strict cutoff)
  3. 가중 평균: 작가 매칭 가중치 0.7, 매체 매칭 가중치 0.3

Backoff hierarchy (매치 미달 시):
  Level 1: 작가 + 크기 + 매체 (최소 3건)
  Level 2: 작가 + 매체 (최소 3건) — 크기 조건 완화
  Level 3: 매체 + 크기 (최소 10건) — 작가 조건 제거
  Level 4: 매체 전체 평균 — 최종 fallback

추가 메타 피처:
  - `comp_match_count`: 매칭된 유사 작품 수 (모델이 신뢰도 판단)
  - `comp_match_level`: backoff 단계 (1~4, 낮을수록 정확)
```

> **주의:** 서빙 시점에 타깃 가격을 모르므로 매칭 조건에 "가격대" 등 타깃 파생 변수 절대 불포함. 같은 회차 내 실현 낙찰가 혼입 방지를 위해 이전 회차(strict cutoff) 데이터만 사용. Sparse artist/희소 매체에서 comp 값은 noisy anchor가 될 수 있으므로 `comp_match_count`를 모델 입력에 포함하여 신뢰도 가중.
>
> **출처:** 경매사 추정가 설정의 핵심 방법론 (Sotheby's, Christie's). 기존 CSV 데이터만으로 구현 가능.

#### 2.4 시장 컨텍스트 피처 (예상 -0.5~1%p)

| # | 피처 | 산출 방법 | 근거 |
|---|------|----------|------|
| 1 | `auction_session` | 경매 회차 순서 (시간 순서 대리 변수) | 시장 추세 |
| 2 | `market_price_index` | 직전 3회차 전체 평균 낙찰가 | 시장 분위기 |
| ~~3~~ | ~~`lot_position`~~ | ~~삭제: ad-hoc 불가~~ | 향후 배치 전용 |
| ~~4~~ | ~~`same_artist_lot_count`~~ | ~~삭제: ad-hoc 불가~~ | 향후 배치 전용 |
| ~~5~~ | ~~`same_medium_lot_count`~~ | ~~삭제: ad-hoc 불가~~ | 향후 배치 전용 |

> **참고:** `auction_month`/`auction_quarter`는 현재 CSV에 회차 정보만 있고 월 매핑이 필요. 매핑 가능 시 추가, 불가 시 `auction_session`으로 대체.
>
> **근거 한계:** Li, Ma, Renneboog (2022, *European Financial Management*)는 미술 시장 수익률/리스크에서 계절 패턴과 auction house 평판 효과를 분석한 논문. `lot_position`, `same_artist_lot_count` 등 개별 피처를 직접 지지하지 않으며, 시장 컨텍스트가 가격에 영향을 줄 수 있다는 일반적 방향성의 간접 근거로만 활용. 이 피처들의 실제 효과는 실험으로 검증 필요.

### Tier 2: 중간 영향 — 추가 MdAPE -1~2%p → 29~31% (stretch)

> **Tier 2 진입 조건:** Tier 1 완료 후 warm/cold 분리 MdAPE 확인, 전체 MdAPE ≤ 33%, warm slice 개선 ≥ 2%p

#### 2.5 Two-Step 가격대별 모델 (예상 -0.5~1.5%p)

**근거:** Kim, K. & Kim, J.B. (2024). "Two-step model based on XGBoost for predicting artwork prices in auction markets." *Int. J. KES*, 28(1), 133-147. 한국 경매 데이터에서 가격 결정 요인이 가격대별로 다름을 확인. 단, 이 논문은 시각 피처를 second-level regressor에 포함하는 구조이므로 현재 순수 tabular two-step에 그대로 일반화하기 어려움. 방향성은 지지하나 동일 효과는 미보장.

**구조:**
```
Step 1: CatBoost Classifier → 가격대 분류
  - 저가 (< 500만)
  - 중가 (500만 ~ 3,000만)
  - 고가 (3,000만+)

Step 2: 가격대별 전용 CatBoost MultiQuantile Regressor
  - Phase 3 챔피언과 동일한 quantile 학습 (q10/q25/q50/q75/q90)
  - 각 가격대에서 중요한 피처가 다름
  - 저가: 매체/크기 중심
  - 고가: 작가 이력/경매유형 중심
```

> **진입 전 확인:** 3-bin 각 bin **train split 기준** 최소 2,000건 이상 확보 (전체가 아닌 CV fold 내 train 기준), bin별 작가 분포 확인. 고가 bin이 미달 시 bin 경계 재조정. Soft classification(확률 기반 가중) 적용. **Quantile 일관성:** 각 가격대 모델도 MultiQuantile 학습.

#### 2.6 앙상블 스태킹 (예상 -0.5~1%p, 효과 검증 후)

**근거:** Mauer, M. & Paszkiel, S. (2024). "Tabular Data Models for Predicting Art Auction Results." *Applied Sciences*, 14(23), 11006. prints/multiples 25,408건 기반이라 K-Auction fine-art mix에 직접 대응은 제한적. "no single approach offers consistently high accuracy"가 결론이며 스태킹 우위를 직접 증명한 논문은 아님. 방향성 참고용.

```
Level-0 (4개 base learner):
  - CatBoost MultiQuantile (현재 Champion)
  - XGBoost (quantile regression)
  - LightGBM (quantile regression)
  - RandomForest (quantile regression)

Level-1 (meta-learner):
  - Ridge Regression (K-Fold OOF predictions, q별 독립 학습)
  - Quantile monotonicity 보장: q10 ≤ q25 ≤ q50 ≤ q75 ≤ q90
    → post-hoc isotonic regression 또는 constrained Ridge로 단조성 강제
```

> **게이트:** 단일 모델(CatBoost) 대비 MdAPE 개선이 확인될 때만 채택. OOF 누수 방지를 위한 strict fold separation 필수 (시계열 기반 fold 분할). 단조성(G11) 위반 시 즉시 폐기.

### Tier 3: 실험적 — 추가 MdAPE -1~3%p (외부 데이터 필요)

#### 2.7 이미지 피처 (예상 -1~2%p, 특히 신규 작가)

**근거:** Mei et al. (2025): multimodal 모델이 fresh-to-market 작품에서 tabular-only 대비 R² +0.02~0.06 개선. 전체 데이터에서의 한계 기여는 제한적이나 거래 이력 없는 작품에 유용.

```
방법: ResNet-50 pretrained (ImageNet) → global average pooling → 2048d → Linear projection → 512d embedding
결합: tabular 피처 + image embedding → FC layer → 가격 예측

대안 (이미지 없을 경우):
  - CLIP zero-shot embedding (텍스트 설명만으로)
  - 작가 대표 이미지 1장의 embedding을 전체 작품에 적용
```

> **K-Auction 적용:** 카탈로그 이미지 현재 미보유. 웹 크롤링 수집 필요하며, 저작권/이용약관 확인 필수.

#### 2.8 제목 NLP 임베딩

```
방법: KoBERT 또는 multilingual SBERT → 제목 embedding (768d) → PCA 50d
효과: 제목에서 주제/시리즈/시대 정보 추출
```

#### 2.9 작가 지식 그래프

```
방법: 전시 이력, 갤러리 소속, 수상 이력 → 그래프 임베딩
데이터: K-ARTMARKET, 한국예술경영지원센터
효과: 사회적 시그널 반영
```

> **출처:** Lee, K. et al. (2024, *Scientific Reports*): living contemporary artist + 외부 social metadata 기반. K-Auction fine-art mix에 직접 대응은 제한적이나, 사회적 시그널의 가격 예측 기여 방향성은 참고 가능.

---

## 3. 구현 아키텍처

### 3.0 서빙 모드: Ad-hoc 단일 경로

현재 API(`/api/v1/estimate`)는 5개 기본 입력(작가명, 매체, 크기, 제작연도, 경매유형)만 받는다. Phase 4에서도 **ad-hoc 단일 경로**를 유지한다.

**설계 결정:** 배치 모드(카탈로그 확정 후 일괄 생성)는 training-serving skew 위험이 크므로, 현 단계에서는 ad-hoc 경로만 구현. 배치 전용 모드는 향후 별도 모델+평가 경로로 확장한다.

**피처 가용성:**
- **ad-hoc에서 사용 가능**: 기존 23개 + 작가 이력 10개 + comp 5개 (최신 스냅샷 캐시)
- **ad-hoc에서 사용 불가**: lot_position, same_artist_lot_count, same_medium_lot_count → **학습에서도 제외**
- **시장 컨텍스트 (market_price_index 등)**: 주기적 캐시 갱신(월 1회)으로 ad-hoc에서도 가용

> **핵심 원칙:** 학습에 사용하는 피처 = 서빙에서 가용한 피처. Training-serving skew를 원천 차단.

### 3.1 전체 파이프라인

```
입력: 작가명, 매체, 크기, 제작연도, 경매유형 (ad-hoc 단일 경로)
  ↓
┌──────────────────────────────────────────────────┐
│  Phase 4: Enhanced Feature Engineering            │
│                                                   │
│  기존 23개 + 신규 작가 이력 10개 + 시장 5개       │
│  + 유사작품 매칭 5개 + (이미지 512d)              │
│  = ~40개 피처 (이미지 제외 시 ~30개)              │
│                                                   │
│  ┌────────────────────────────────────────┐       │
│  │ CatBoost MultiQuantile (Tier 1 기본)   │       │
│  │ 피처 고도화 + warm/cold 분리 평가       │       │
│  │ → q10/q25/q50/q75/q90 직접 학습        │       │
│  └──────────┬─────────────────────────────┘       │
│             │                                     │
│  ┌──────────▼─────────────────────────────┐       │
│  │ (Tier 2) Two-Step 가격대별 모델         │       │
│  │ 3개 CatBoost MultiQuantile             │       │
│  └──────────┬─────────────────────────────┘       │
│             │                                     │
│  ┌──────────▼─────────────────────────────┐       │
│  │ (Tier 2) 앙상블 Stacking (검증 후)     │       │
│  │ 4 base quantile → Ridge meta          │       │
│  │ + isotonic monotonicity 강제           │       │
│  └──────────┬─────────────────────────────┘       │
│             │                                     │
│  ┌──────────▼─────────────────────────────┐       │
│  │ Split Conformal Calibration + Confidence│       │
│  └──────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘
  ↓
출력: 가격 구간 (하한/중앙/상한) + 신뢰도 등급
```

> **Quantile 일관성:** 모든 단계에서 MultiQuantile 학습 유지. 스태킹 시 post-hoc isotonic regression으로 분위수 단조성(q10 ≤ q25 ≤ ... ≤ q90) 강제.
>
> **Conformal Calibration 방법론:** Split Conformal Prediction 적용. (1) 시계열 기반으로 calibration set을 분리 (최신 N회차), (2) Nonconformity score = |y - q50_hat| / (q75_hat - q25_hat) (정규화 잔차), (3) Calibration set에서 target coverage에 해당하는 quantile threshold 산출, (4) 서빙 시 해당 threshold로 구간 너비 보정. **이 단계는 MdAPE(점 예측) 개선이 아니라 coverage/interval 보정 전용.**

### 3.2 피처 설계 (30~40개, lot 3개 제외 후)

**기존 유지 (23개):** Phase 3 HEDONIC_FEATURES 전체

**신규 작가 이력 (10개):**
artist_recent_avg_price, artist_price_momentum, artist_sale_frequency, artist_auctions_since_last_sale, artist_price_volatility, artist_lot_count_trend, artist_premium_ratio, artist_reappear_flag, artist_last_hammer_price, artist_career_length

**시장 컨텍스트 (5개):**
auction_month (회차→월 매핑), auction_quarter, market_price_index (캐시)

**유사 작품 매칭 (5개):**
comp_artist_avg_price, comp_medium_avg_price, comp_weighted_price, comp_match_count, comp_match_level

**이미지 (선택, Tier 3, +512d):**
resnet50_embedding (PCA → 50d)

### 3.3 데이터 요구사항

| 데이터 | 현재 보유 | 추가 필요 |
|--------|---------|----------|
| K-Auction CSV 43,866건 | ✅ | — |
| 작가별 거래 이력 | ✅ (CSV에서 추출) | — |
| 경매 회차→월 매핑 | ⚠️ 회차만 있음 | 매핑 테이블 구축 필요 (Tier 1 내 확인) |
| 카탈로그 이미지 | ❌ | K-Auction 파트너십 협상 후 확보 필요 (Tier 3, 스크래핑 불가) |
| 작가 전시 이력 | ❌ | K-ARTMARKET 등 외부 데이터 (Tier 3) |

**Tier 1은 기존 CSV 데이터로 구현 가능** (단, `auction_month`는 매핑 필요하여 불가 시 `auction_session`으로 대체). Tier 2도 기존 데이터 기반. Tier 3은 외부 데이터 필요.

---

## 4. 게이트 조건 (조정)

| # | 게이트 | 기준 | 유형 | 근거 |
|---|--------|------|------|------|
| G1 | MdAPE (전체) | < 33% | 기본 | Phase 3 34% 대비 -1%p 이상 |
| G2 | MdAPE (메이저) | < 31% | 기본 | 고가 정확도 강화 |
| G3 | R² | ≥ 0.64 | 기본 | Phase 3 (0.621) 대비 개선 |
| G4 | Coverage (q25~q75) | ≥ 55% | 기본 | Calibration 포함 (Phase 3: 52.9%) |
| G5 | Within 30% | ≥ 48% | 기본 | Phase 3 45% 대비 +3%p |
| G6 | Tier 1 warm MdAPE | warm slice ≥ 3%p 개선 | 기본 | warm artist 효과 확인 |
| G7 | Tier 1 cold MdAPE | cold slice 악화 ≤ 1%p | 기본 | cold artist 보호 |
| G8 | Tier 2 진입 | 전체 MdAPE ≤ 33% + warm ≥ 2%p | Tier 2 | Tier 1 효과 확인 후 |
| G9 | Two-Step 개선율 | > Tier 1 단일 모델 | Tier 2 | 가격대별 분리 효과 확인 |
| G10 | 앙상블 개선율 | > 최고 단일 모델 | Tier 2 | 스태킹 효과 확인 |
| G11 | Cold Start MdAPE | < 48% | 기본 | Phase 3 baseline ~50% 대비 |
| G12 | Monotonicity | 100% | 기본 | quantile 단조성 (isotonic 강제) |
| G13 | Leakage 테스트 | 전체 통과 | 기본 | |
| G14 | Bin 분포 확인 | 각 bin train ≥ 2,000건 | Tier 2 | Two-Step 진입 전 |

**G14 실측 근거 (K-Auction 낙찰 43,866건 기준):**

| Bin | 전체 건수 | Train (~70%) | G14 충족 |
|-----|----------|-------------|---------|
| 저가 (<500만) | 32,382 | ~22,667 | ✅ |
| 중가 (500만~3,000만) | 8,094 | ~5,665 | ✅ |
| 고가 (3,000만+) | 3,390 | ~2,373 | ✅ (2,000건 초과) |

> **Stretch goal:** MdAPE < 31% (전체), R² ≥ 0.68 (Tier 2 + Tier 3 성공 시)

---

## 5. 개발 계획

### Sprint 구성

| Sprint | 내용 | 기간 | 기대 MdAPE |
|--------|------|------|-----------|
| Sprint 0 | 작가 이력 피처 10개 + warm/cold 분리 평가 | 3일 | 32~34% |
| Sprint 0.5 | 유사 매칭 5개 + 시장 피처 5개 (회차→월 매핑 확인) | 2일 | 31~33% |
| Sprint 1 | Two-Step 가격대별 모델 (3-bin, MultiQuantile) + 실험 | 3일 | 30~32% |
| Sprint 2 | 앙상블 스태킹 (4 base quantile + meta, 효과 검증) + 단조성 확인 | 3일 | 29~31% |
| Sprint 3 | Split Conformal Calibration + 신뢰도 등급 (coverage 보정, MdAPE 변동 없음) | 1일 | 29~31% (점 예측 동일) |
| Sprint 4 | (선택) 이미지 피처 + NLP | 3일 | 28~30% |

**Tier 1 (Sprint 0~0.5): 5일, 기존 CSV 데이터 — 가장 큰 효과 기대**
**Tier 2 (Sprint 1~3): 7일, 기존 데이터 기반 — 구조적 개선 (Tier 1 효과 확인 후)**
**Tier 3 (Sprint 4): 3일, 외부 데이터 필요 — 선택적**

---

## 6. 리스크 및 완화

| # | 리스크 | 심각도 | 완화 |
|---|--------|--------|------|
| 1 | 작가 피처 과적합 (인기 작가 편향) | 높음 | Bayesian shrinkage + sparse-history 안정화 |
| 2 | Sparse history (45.9% 작가 1건) | 높음 | `is_sparse_artist` 플래그, 결측 시 전역 통계로 대체, warm/cold 분리 측정 |
| 3 | Warm/cold slice 효과 편차 | 높음 | warm/cold 분리 측정 필수, cold 악화 ≤ 1%p 게이트(G7), cold 악화 시 피처 제한 |
| 4 | Sold-only survivorship bias | 높음 | `artist_unsold_rate` 피처 반영, 저유동성 작가 예측 구간 1.3배 확장 (Phase 3 기존 조치 계승) |
| 5 | Comp 매칭 시 같은 회차 낙찰가 혼입 | 높음 | 이전 회차(strict cutoff) 데이터만 사용, 서빙 시 동일 규칙 적용 |
| 6 | Comp 매칭에 타깃 파생 변수 사용 | 높음 | 매칭 조건에 "가격대" 등 타깃 파생 변수 절대 불포함 |
| 7 | Comp noisy anchor (sparse artist/희소 매체) | 중간 | backoff hierarchy + `comp_match_count`/`comp_match_level` 메타 피처로 모델이 신뢰도 판단 |
| 8 | Two-Step 분류 오류 전파 | 중간 | Soft classification (확률 기반), 3-bin, 각 bin ≥ 2,000건 확인(G14) |
| 9 | 가격대별 표본 불균형 | 중간 | bin 경계 조정으로 최소 표본 확보, bin별 작가 분포 확인 |
| 10 | Quantile stacking 단조성 위반 | 높음 | post-hoc isotonic regression 또는 constrained Ridge, G12 100% 강제, 위반 시 즉시 폐기 |
| 11 | 앙상블 복잡도 증가 | 중간 | 추론 latency 100ms 이내 확인, 효과 미미 시 단일 모델 유지 |
| 12 | Stacking OOF 누수 | 높음 | Strict fold separation, 시계열 기반 fold 분할 (미래 데이터 불포함) |
| 13 | Cold-start 성능 악화 | 중간 | 신규 작가 전용 게이트(G11), 이미지 피처(Tier 3)로 보완 |
| 14 | 이미지 데이터 수집 불가/권리 문제 | 낮음 | Tier 3 선택 사항, 미수집 시 Tier 1~2만으로 진행 |
| 15 | 유사 작품 매칭 지연 | 낮음 | 사전 계산 + 캐시 |
| 16 | 시계열 누수 | 높음 | Phase 3과 동일한 strict cutoff + 8개 규칙 유지 |
| 17 | 서빙 입력 계약 불일치 | 높음 | **ad-hoc 단일 경로로 통일.** 시장 컨텍스트 피처(market_price_index 등)는 주기적 캐시 갱신(월 1회)으로 ad-hoc에서도 가용. 배치 전용 모델은 향후 확장 시 별도 평가 경로 추가. |
| 18 | ~~카탈로그 피처~~ | 삭제 | lot_position 등 3개 피처를 ad-hoc 불가로 제거함에 따라 해소 |
| 19 | Comp 매칭 시 edition/condition/provenance 미반영 | 중간 | K-Auction CSV에 해당 정보 부재, comp anchor가 동일 작가의 다른 조건 작품과 혼합될 수 있음. match_count 메타 피처로 간접 완화 |
| 20 | Bin population failure (고가 bin 미달) | 중간 | train split 기준 2,000건 미달 시 bin 경계 재조정 또는 2-bin으로 축소 |

---

## 7. 참고 문헌

1. Mei, J. et al. (2025). "Deep Learning for Art Market Valuation." *arXiv:2512.23078*. — 반복매매 R² 0.77~0.79, fresh-to-market tabular R² 0.54~0.59, multimodal R² 0.61~0.65. Sotheby's/Christie's 기반, K-Auction 직접 적용에 한계.
2. Kim, K. & Kim, J.B. (2024). "Two-step model based on XGBoost for predicting artwork prices in auction markets." *Int. J. KES*, 28(1), 133-147. — 한국 경매 가격대별 모델 분리. 시각 피처 포함 구조이므로 순수 tabular two-step에 그대로 일반화는 제한적.
3. Lee, K. et al. (2024). "Social signals predict contemporary art prices better than visual features, particularly in emerging markets." *Scientific Reports*, 14, 11615. — living contemporary artist + 외부 social metadata 기반. K-Auction fine-art mix에 직접 대응 제한적.
4. Mauer, M. & Paszkiel, S. (2024). "Tabular Data Models for Predicting Art Auction Results." *Applied Sciences*, 14(23), 11006. — prints/multiples 25,408건 기반. RF/XGBoost 비교, 일관된 최고 모델 없음.
5. Li, Y., Ma, X. & Renneboog, L. (2022). "Pricing art and the art of pricing: On returns and risk in art auction markets." *European Financial Management*. — 미술 시장 수익률/리스크 분석. 계절 패턴/auction house 효과 간접 근거. 개별 피처(lot_position 등) 직접 지지는 아님.
6. Hwang, J., Ryu, K. & Hong, K. (2025). "The paradox of being unsold: hidden signaling value of bought-in in Korean art auction." *J. Cultural Economics*, 49(3). — 한국 경매 유찰 분석
7. Renneboog, L. & Spaenjers, C. (2013). "Buying Beauty." *Management Science*, 59(1), 36-53. — Hedonic 모델 기반 미술 가격 분석
8. Aubry, M. et al. (2025). "Visual Features and Art Market Prices." *Working Paper*. — 이미지 피처가 거래 이력 없는 작품에서 R² +0.04~0.12 개선. Source 3b 근거

---

## 8. 요약

**핵심 전략: 기존 CSV 데이터에서 추출 가능한 작가 이력 피처를 warm/cold 분리 평가와 함께 극대화하고, 유사 작품 매칭(backoff hierarchy 포함)을 추가한 후, 가격대별 모델 분리 + 앙상블을 검증적으로 적용.**

| Phase | 개선 방법 | Tier 대응 | 예상 MdAPE | 이전 대비 증분 | 추가 데이터 |
|-------|----------|----------|-----------|--------------|-----------|
| **현재** | Phase 3 기본 | — | 34% | — | — |
| **4a** | 기존 데이터 최적화 | Tier 1+2 | 29~31% | -3~5%p | 불필요 |
| **4b (기본)** | + K-ARTMARKET + Artsy 소셜 시그널 | Tier 3 일부 | 27~30% | -1~3%p (증분) | K-ARTMARKET, Artsy API |
| **4b (fallback)** | + Artsy 소셜 시그널만 | Tier 3 축소 | 28~31% | -0.5~1%p (증분) | Artsy API만 |
| **4c** | + K-Auction 이미지 CNN (WikiArt pretrain) | Tier 3 이미지 | 25~28% | -1~2%p (증분) | K-Auction 이미지 |
| **최대** | + Artnet/Artprice + 지식 그래프 | 전체 | 23~26% | -1~3%p (증분) | 유료 구독 |

**가장 중요한 한 가지: 작가의 최근 낙찰가(`artist_last_hammer_price`)가 warm artist에서 가장 강력한 앵커.** 단, 전체 작가의 45.9%가 cold artist이므로 warm/cold 분리 전략이 Phase 4의 성패를 결정.

---

## 9. 외부 데이터 수집 전략

### 9.1 수집 대상 요약

| 우선순위 | 데이터 소스 | 수집 항목 | 방법 | 난이도 | 주요 제약 | 비용 |
|---------|-----------|----------|------|--------|----------|------|
| **1** | K-ARTMARKET | 8만건 경매 이력 (10개 경매사) | 웹 수집 / 공공데이터 요청 | **중~높** | 공공데이터 요청 응답 1~4주, 웹 구조 변경·차단 리스크 | 무료 |
| **2** | Artsy API | 작가 프로필 + 전시 이력 + 갤러리 정보 | REST API | **중** | rate limit (~1,000 req/day), 한국 작가 커버리지 30~50%, 2차 활용·재배포 제한 | 무료 |
| **3** | WikiArt | 25만+ 이미지 (**사전학습 전용**) | Kaggle/HuggingFace 다운로드 | **낮** | 상업 배포 시 개별 저작권 확인 필요, 캐시/재배포 금지 | 무료 |
| **4** | 공공데이터포털 | MMCA 전시 프로그램, 박물관 데이터 | REST API | **낮~중** | 일 호출 제한 1,000건, 데이터 갱신 주기 불규칙 | 무료 |
| **3b** | K-Auction 이미지 (→ Source 3b 상세) | 카탈로그 이미지 (43,866건) | 파트너십 협상 | **높** | 스크래핑 금지, 파트너십 협상 수개월 소요 가능 | 무료/협상 |
| **5** | Artnet/Artprice | 글로벌 경매 이력 (한국 작가) | 유료 구독 API | **중** | API 호출 제한, 데이터 캐시·재배포 금지, 라이선스 범위 제한 | $150~2,000/년 |

### 9.2 데이터별 기대 피처와 영향

**Source 1: K-ARTMARKET (80,000건 추가 경매 이력)**

현재 K-Auction 43,866건 → **K-ARTMARKET 합산 ~120,000건.** 데이터 2.7배 확대.

| 기대 피처 | 효과 |
|----------|------|
| 서울옥션/마이아트옥션 거래 이력 포함 | Cold artist 비율 감소 (45.9% → ~30%) |
| 교차 경매사 작가 통계 | 작가 이력 피처 정확도 향상 |
| 10개 경매사 데이터 | 경매사별 프리미엄 효과 학습 가능 |

> **예상 개선 (단독 효과):** Cold artist 비율 감소 → MdAPE -2~4%p (단독). **주의:** Tier 1 작가 이력 피처와 설명력 중복 가능. Tier 1 이후 증분 효과는 -1~3%p로 축소 예상. **검증 계획:** B-5 완료 후 K-ARTMARKET 통합 전후 cold artist 비율 실측, 통합 모델 vs 4a 모델 A/B 비교로 증분 효과 확인.

**Source 2: Artsy API (작가 소셜 시그널)**

| 기대 피처 | 피처명 | 효과 | 비고 |
|----------|--------|------|------|
| 전시 이력 | `artist_exhibition_count` | 작가 명성 직접 지표 | Artsy 고유 |
| 갤러리 소속 | `gallery_tier` (국제/국내/없음) | 시장 접근성 | Artsy 고유 |
| 소속 갤러리 수 | `gallery_count` | 시장 활성도 | Artsy 고유 |
| 작가 국적 | `artist_nationality` | 가격 구조 차이 | Artsy 고유 |

> **참고:** `auction_appearance_freq` (경매 출현 빈도)는 K-Auction/K-ARTMARKET 경매 이력에서 직접 산출하는 피처이며, Artsy에서 제공되지 않음. Tier 1 `artist_sale_frequency`와 유사하나, K-ARTMARKET 통합 시 교차 경매사 출현 빈도로 확장.

> **출처:** Lee et al. (2024, *Scientific Reports*): 사회적 시그널이 시각 피처보다 가격 예측력 우수, 특히 신흥 시장(한국)에서 효과 극대화.
> **예상 개선 (단독 효과):** Cold artist에서 특히 유효 → MdAPE -2~3%p (단독). **K-ARTMARKET 병행 시 증분 효과 -1~2%p** (작가 이력과 전시 이력 간 상관 r≈0.4~0.6 추정, 통합 후 상관 분석으로 실측 예정).

**Source 3: WikiArt (사전학습 전용, 25만+ 이미지)**

| 역할 | 활용 방법 | 비고 |
|------|----------|------|
| **사전학습 (pretraining)** | ResNet-50을 WikiArt 25만장으로 domain-adaptive pretraining | ImageNet → WikiArt fine-tune으로 미술 도메인 특화 |
| CLIP zero-shot 대안 | 이미지 없이 텍스트 설명 기반 embedding | K-Auction 이미지 확보 전 대안 |

> **한계:** WikiArt은 서양 미술 중심이며 한국 작가 커버리지 낮음 (~500명 추정). 사전학습에만 사용하고 직접 학습 데이터로는 사용 불가.
> **필요 해상도:** 224x224 (ResNet-50) / 384x384 (ViT)

**Source 3b: K-Auction 이미지 (실제 학습용, Phase 4c 전용)**

| 역할 | 활용 방법 | 효과 |
|------|----------|------|
| **실제 학습 (fine-tuning)** | WikiArt-pretrained ResNet-50 → K-Auction 이미지로 fine-tune | tabular + 512d image embedding |
| tabular fusion | K-Auction 이미지 embedding + tabular 피처 결합 | R² +0.04~0.12 (fresh-to-market) |
| `image_style_cluster` | Embedding K-Means 클러스터 (20~50개) | 스타일 기반 comp 매칭 보강 |
| `image_colorfulness` | 색상 다양성 수치 (low-level feature) | 장식성/선호도 시그널 |

> **병목:** K-Auction 이미지는 파트너십 협상 또는 제한적 수집 필요 (난이도 높음). 이미지 확보 불가 시 Phase 4c 전체 진행 불가.
> **파이프라인:** WikiArt pretrain → K-Auction fine-tune → tabular fusion. **WikiArt 단독으로는 K-Auction 가격 예측에 직접 기여 불가** (도메인 불일치).
> **출처:** Aubry et al. (2025): 이미지 피처는 거래 이력 없는 작품에서 가장 유효 (+0.12 R²).
> **예상 개선:** K-Auction 이미지 확보 시 cold artist에서 → MdAPE -1~3%p (증분)

**Source 4: 공공데이터포털 (MMCA 전시)**

| 기대 피처 | 효과 |
|----------|------|
| MMCA 전시 참여 여부 | 기관 인정 시그널 |
| 전시 횟수 | 작가 활동 수준 |

> **예상 개선:** 보조적 → MdAPE -0.5~1%p (증분)

**Source 5: Artnet/Artprice (글로벌 경매 이력, 유료)**

| 기대 피처 | 피처명 | 효과 |
|----------|--------|------|
| 글로벌 경매 이력 | `artist_global_auction_count` | 국제 시장 활동 수준 |
| 글로벌 평균 낙찰가 | `artist_global_avg_price` | 국제 가격 앵커 |
| 글로벌 가격 추세 | `artist_global_price_trend` | 국제 시장 모멘텀 |

> **제약:** 유료 구독 ($150~2,000/년), API 호출 제한, 데이터 캐시·재배포 금지. 한국 작가 커버리지 10~30% (국제 활동 작가 한정).
> **예상 개선:** 국제 활동 작가 subset에서 MdAPE -0.5~1.5%p (증분). 전체 효과 제한적.

### 9.3 수집 실행 계획

**Phase-Tier 매핑 및 정량 게이트:**

| Phase | Tier 대응 | 진입 조건 | 완료 게이트 |
|-------|----------|----------|------------|
| **4a** | Tier 1+2 | — (즉시 시작) | G1: MdAPE < 33%, G3: R² ≥ 0.64, G6: warm ≥ 3%p, G7: cold 악화 ≤ 1%p |
| **4b (기본)** | Tier 3 일부 (외부 데이터) | 4a 완료 + G1 통과 + 법적 STOP/GO 완료 + K-ARTMARKET 확보 | (1) DQ1~DQ5 통과, (2) 4a 대비 MdAPE ≥ 1%p 추가 개선, (3) cold artist 비율 < 40% |
| **4b (fallback)** | Tier 3 축소 (K-ARTMARKET 미확보) | 4a 완료 + G1 통과 + K-ARTMARKET 포기 판정 + **Artsy 법적 STOP/GO GO 판정** | (1) DQ-F1~F3 통과 (아래 참조), (2) Artsy 소셜 피처로 4a 대비 MdAPE ≥ 0.5%p 개선, (3) cold artist 비율 제약 해제 (K-Auction 단독이므로 비율 변동 없음) |
| **4c** | Tier 3 이미지 | 4b 완료 + K-Auction 파트너십 확보(C-0) | 4b 대비 cold MdAPE ≥ 2%p 개선 |

**4b 데이터 통합 품질 게이트 (B-5 완료 조건):**

| # | 게이트 | 기준 | 미달 시 조치 |
|---|--------|------|------------|
| DQ1 | 작가 자동 매칭 precision | ≥ 95% (샘플 500건 수동 검증) | precision 미달 시 매칭 규칙 재설계 |
| DQ2 | 작가 자동 매칭 recall | ≥ 80% | recall 미달 시 fuzzy matching threshold 완화 + 수동 보완 |
| DQ3 | 수동 검증 필요 비율 | ≤ 20% | 초과 시 매칭 규칙 개선 또는 미매칭 작가 제외 |
| DQ4 | 통합 후 usable artist coverage | K-Auction 작가 중 ≥ 60% 매칭 | 미달 시 외부 데이터 효과 재산정, 효과 < 1%p면 통합 포기 |
| DQ5 | 동명이인 오매칭률 | ≤ 2% (생몰년·매체 교차 검증) | 초과 시 해당 작가 제외 |

**4b fallback 데이터 품질 게이트 (Artsy 단독 통합 시):**

| # | 게이트 | 기준 | 미달 시 조치 |
|---|--------|------|------------|
| DQ-F1 | Artsy 작가 매칭 precision | ≥ 90% (샘플 200건 수동 검증) | 매칭 규칙 재설계 또는 Artsy 통합 포기 |
| DQ-F2 | Artsy 매칭 커버리지 | K-Auction 작가 중 ≥ 30% 매칭 | 미달 시 Artsy 효과 재산정, 효과 < 0.5%p면 통합 포기 |
| DQ-F3 | 오매칭률 | ≤ 3% | 초과 시 해당 작가 제외 |

> **참고:** fallback은 Artsy 소셜 시그널만 사용하므로 DQ1~DQ5(K-ARTMARKET 다중 소스 통합)보다 기준이 완화되어 있으나, 최소 precision·coverage·오매칭률 게이트는 유지.

**Phase 4a: 기존 데이터 최적화 (외부 데이터 없이, 6일)**
→ Tier 1+2 구현: MdAPE 34% → 29~31%

**Phase 4b: 외부 데이터 수집 + 통합 (작업일 13~17일, 대기 포함 최대 5주)**

> **일정 구조:** B-1(K-ARTMARKET)은 공공데이터 요청 시 응답 대기 1~4주 발생. 대기 기간 중 B-2~B-4를 병행 처리. 대기 1주 초과 시 fallback 발동 (아래 참조).

| Step | 작업 | 기간 | 산출물 | 불확실성 |
|------|------|------|--------|----------|
| B-1 | K-ARTMARKET 데이터 수집 (STOP/GO 통과 경로만 실행) | 3~7일 (대기 별도) | ~80,000건 추가 경매 이력 CSV | **높음**: 정식 요청 시 응답 대기 1~4주. STOP/GO에서 확정된 경로(공공데이터 요청 or 웹 수집)만 진행 |
| B-2 | Artsy API 작가 프로필 수집 (K-Auction 작가 매칭) | 2~4일 | 작가별 전시/갤러리 JSON | **중간**: rate limit (1,000 req/day 추정), 한국 작가 커버리지 30~50% |
| B-3 | *(삭제: WikiArt는 4c 선행준비로 이동, 아래 C-1 참조)* | — | — | — |
| B-4 | 공공데이터포털 MMCA 전시 데이터 수집 | 1~2일 | 전시 이력 CSV | **낮음**: 공식 API, 일 1,000건 호출 제한 |
| B-5 | **데이터 통합 (작가명 정규화 + 매칭)** | 3일 | 통합 마스터 테이블 | **높음**: 아래 통합 난제 참조 |
| B-6 | 피처 빌드 + 학습 | 2일 | 통합 모델 | 중간 |
| B-7 | 게이트 판정 + 성능 비교 | 1일 | 최종 리포트 | 낮음 |

**B-1 Fallback 계획 (K-ARTMARKET 수집 실패/지연 시):**
1. **1주 초과 지연** → 대기 계속하되, B-2~B-4를 병행 완료. 2주 시점에서 재판단
2. **2주 초과 또는 접근 차단** → K-ARTMARKET 포기 → **4b fallback 경로** 전환: K-Auction 기존 43,866건 + Artsy 소셜 시그널만으로 진행. 완료 게이트는 fallback 기준 적용 (cold artist 비율 제약 해제, MdAPE ≥ 0.5%p 개선). **서울옥션 등 타 경매사 직접 수집은 스크래핑 금지 원칙에 따라 대상에서 제외**
3. **부분 수집 (50% 미만)** → 수집된 데이터만으로 cold artist 비율 재산정, 효과가 MdAPE -1%p 미만이면 통합 포기 후 fallback 경로 전환

**B-5 데이터 통합 난제:**
- **작가명 정규화**: 한글/영문/한자 혼용, 띄어쓰기 불일치 (예: "이우환" vs "Lee Ufan" vs "李禹煥")
- **동명이인 처리**: 생몰년·매체·활동 시기로 disambiguation, 자동 매칭 후 수동 검증 필요
- **Alias 매칭**: 호(號), 필명, 영문 표기 변형 → fuzzy matching + 수동 사전 구축 (예상 500~1,000건)
- **경매사 간 필드 불일치**: 매체 분류 체계, 크기 단위, 가격 통화 차이 → 정규화 매핑 테이블 필요
- **예상 매칭률**: 자동 80~85%, 수동 검증 필요 15~20% → **3일 소요 근거**

**Phase 4c: 이미지 모델 (선택, K-Auction 이미지 확보 시)**

> **전제:** C-0(파트너십 협상)은 Phase 4a 시작과 동시에 병행 착수. 협상 타결까지 수주~수개월 소요 가능.

| Step | 작업 | 기간 | 비고 |
|------|------|------|------|
| C-0 | K-Auction 파트너십 협상 (4a와 병행) | 수주~수개월 | **Phase 4c 착수 전제 조건.** 협상 실패 시 Phase 4c 전체 포기 |
| C-0.5 | WikiArt 이미지 다운로드 (사전학습 전용, C-0 대기 중 병행) | 1일 | Kaggle/HF 정적 다운로드. 4b 필수 아님, 4c 선행준비 |
| C-1 | K-Auction 이미지 다운로드 + 전처리 (파트너십 확보 후) | 2~3일 | 파트너십 API 또는 허용 범위 내 수집 |
| C-2 | WikiArt pretrain + K-Auction fine-tune + tabular fusion | 3일 | GPU 환경 필요 |
| C-3 | 평가 + 게이트 (4b 대비 cold MdAPE ≥ 2%p) | 1일 | |

### 9.4 외부 데이터 포함 예상 성능

> **중복 설명력 고려:** 각 단계의 MdAPE 개선은 **이전 단계 대비 증분**으로 표기. 단독 효과 합산이 아닌, 중복 설명력을 감안한 보수적 추정.

| 단계 | 방법 | Tier 대응 | MdAPE | 이전 대비 증분 | R² | 정량 게이트 |
|------|------|----------|-------|--------------|-----|-----------|
| **현재** | Phase 3 기본 | — | 34% | — | 0.62 | — |
| **4a** | 기존 데이터 최적화 (Tier 1+2) | Tier 1+2 | 29~31% | -3~5%p | 0.64~0.68 | G1~G14 전체 |
| **4b (기본)** | + K-ARTMARKET + Artsy (증분) | Tier 3 일부 | 27~30% | -1~3%p (증분) | 0.66~0.72 | DQ1~5 + 4a 대비 MdAPE ≥ 1%p |
| **4b (fallback)** | + Artsy만 (K-ARTMARKET 미확보) | Tier 3 축소 | 28~31% | -0.5~1%p (증분) | 0.64~0.69 | DQ-F1~3 + 4a 대비 MdAPE ≥ 0.5%p |
| **4c** | + K-Auction 이미지 (증분) | Tier 3 이미지 | 25~28% | -1~2%p (증분) | 0.68~0.74 | 4b 대비 cold MdAPE ≥ 2%p 개선 |
| **이론적 상한** | + Artnet/Artprice + 지식 그래프 | 전체 | 23~26% | -1~3%p (증분) | 0.70~0.76 | — |

> **주의:** 4a는 tabular 중심이므로 section 1.3의 fresh-to-market tabular 상한(R² 0.54~0.59) 대비 낙관적. 단, K-Auction 데이터는 warm artist 54.1%를 포함하므로 fresh-to-market 전용 상한보다 높은 R²가 가능. 0.64~0.68은 warm/cold 혼합 데이터 기준 추정이며 실험 검증 필수. 4b/4c는 외부 데이터 품질·커버리지에 따라 편차 큼.

### 9.5 법적 고려사항 (수집 → 학습 → 배포 3단계)

| 소스 | 수집 단계 | 학습 단계 | 배포 단계 |
|------|----------|----------|----------|
| K-ARTMARKET (공공데이터 요청) | 정보공개청구 또는 공공데이터 포털 정식 요청 | 공공데이터법에 따라 학습 가능 | 모델 가중치 배포 가능. 원본 데이터 재배포는 이용 허락 범위 확인 후 |
| K-ARTMARKET (웹 수집) | robots.txt 준수, 연구 목적 한정. **STOP/GO**: robots.txt 또는 이용약관에서 수집 금지 시 즉시 중단 | **STOP/GO**: 웹 수집 데이터의 ML 학습 허용 여부 이용약관 확인 필수. 미확인 시 학습 금지 | 웹 수집 데이터 기반 모델은 이용약관 확인 완료 후에만 배포. **DB 구축권 미확인 시 배포 보류** |
| Artsy API | API Terms 준수, rate limit 내 수집. 2차 활용 제한 확인 필요 | **STOP/GO**: ML 학습 허용 여부 Terms 확인 완료 전까지 학습 금지. 확인 후 허용 시만 진행 | **학습 STOP/GO 통과 시** 모델 가중치 배포 가능 (파생물). 미통과 시 Artsy 피처 전체 제외. **원본 데이터 캐시·재배포 금지** |
| WikiArt | Kaggle/HF 정적 다운로드 (교육/연구 목적) | **사전학습 전용** 허용 (교육 목적). 상업 학습 시 개별 이미지 저작권 확인 | 모델 가중치 배포 가능. **원본 이미지 재배포 불가** |
| K-Auction/서울옥션 | **스크래핑 금지** → 공식 파트너십 협상 필수 | 파트너십 계약 범위 내 학습 | 파트너십 계약에 따라 모델 배포 범위 결정. 이미지 재배포 불가 |
| Artnet/Artprice | 유료 구독 API, 라이선스 계약 | **STOP/GO**: 라이선스 계약서에서 ML 학습·파생물 배포 허용 확인 후만 진행. **데이터 캐시 기간 제한** (보통 24h) | **라이선스 확인 통과 시** 모델 가중치 배포 가능. 미확인 시 해당 소스 제외. **원본 데이터 캐시·재배포 절대 금지** |
| 공공데이터포털 | 공식 API, 자유 이용 가능 (공공데이터법) | 제한 없음 | 출처 표기 시 자유 배포 |

> **핵심 원칙:** (1) **상업 API·이용약관 제한 소스**의 원본 데이터는 재배포 불가, (2) **공공데이터법 적용 소스**(공공데이터포털, K-ARTMARKET 정식 요청분)는 출처 표기 시 자유 배포 가능 (소스별 정책 우선), (3) 모델 가중치(파생물)는 법적 STOP/GO 통과 후에만 배포 가능, (4) STOP/GO 미통과 소스는 피처 전체 제외하고 나머지로 진행.
>
> **법적 STOP/GO 프로세스 (Phase 4b 착수 전 완료):**
> 1. **K-ARTMARKET**: 공공데이터 정식 요청 경로 확보 여부 확인. 정보공개청구 승인 시 GO, 미승인 시 웹 수집 이용약관 확인 → 웹 수집 금지 시 NO-GO
> 2. **Artsy API**: Terms of Service에서 ML 학습 목적 허용 여부 확인. 명시적 허용 또는 비금지 시 GO, 명시적 금지 시 NO-GO
> 3. **Artnet/Artprice**: 라이선스 계약서에서 ML 학습·파생물 배포 허용 확인. 확인 완료 시 GO, 미확인 시 NO-GO
> 각 소스별 GO/NO-GO를 **B-1 시작 전까지** 완료. NO-GO 소스는 일정·성능 목표에서 제외 후 재산정.

---

*본 기획서는 학술 문헌 7편 + 외부 데이터 소스 리서치 + Codex 리뷰 권고를 기반으로 작성되었으며, Codex 리뷰 대상입니다.*

### 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.0 | 2026-03-28 | 초안 작성 |
| v2.0 | 2026-03-28 | Codex 리뷰 1차: 목표치 보수적 조정, 문헌 인용 정리, 우선순위 재정렬, 리스크 확장, 게이트 현실화 |
| v3.0 | 2026-03-28 | Codex 리뷰 2차: comp sales 순환참조 제거, 참고문헌 저자명 정정, quantile 일관성 명시, 변수명 정정, 리스크 14개 확장 |
| v4.0 | 2026-03-28 | Codex 리뷰 3차: 목표 재조정, warm/cold 분리 평가 추가, comp backoff hierarchy, 서지 정정, 스태킹 단조성 보장, Cold Start baseline 명시, Tier 2 진입 게이트 추가, Sprint 기간 현실화, 리스크 16개 확장 |
| v5.0 | 2026-03-28 | Codex 리뷰 4차: 근거-개선폭 연결 보정, 서빙 모드 듀얼 아키텍처, Split Conformal Calibration, 리스크 20개 확장 |
| v6.0 | 2026-03-28 | Codex 리뷰 5차: G14 bin 기준 5,000→2,000건 (고가 bin 3,618건 현실 반영), 서빙 모드를 ad-hoc 단일 평가 경로로 통일 (배치 모드는 향후 확장, 현 단계에서는 training-serving skew 방지 우선) |
| v7.0~v9.0 | 2026-03-28 | 외부 데이터 수집 전략(Section 9) 추가 |
| v10.0 | 2026-03-28 | Codex 리뷰 7차: (C1) K-ARTMARKET 수집 불확실성+fallback 계획, (C2) WikiArt/K-Auction 이미지 역할 분리(사전학습 vs 실제학습), (M1) 외부 소스 난이도 현실화(rate limit/재배포 제한), (M2) 개선폭 중복 설명력 고려→증분 표기, (M3) 9.4 성능표-Tier 목표 통일, (M4) auction_appearance_freq 소스 정정, (M5) 법적 리스크 수집/학습/배포 3단계 분리, (M6) 데이터 통합 난제(작가명 정규화/동명이인/alias) 일정 반영, (m1) Source 5·6 상세 추가, (m2) Phase-Tier 매핑+정량 게이트 추가 |
| v11.0 | 2026-03-28 | Codex 리뷰 8차: (M1) 법적 STOP/GO 프로세스 추가—Artsy/Artnet 학습·배포 단정 표현 제거, (M2) 4b 일정에 대기 기간 명시(작업일 13~17일, 대기 포함 최대 5주), (M3) Phase 4c C-0 파트너십 협상 선행 조건 분리(수주~수개월), (M4) 데이터 통합 품질 게이트 5개(DQ1~DQ5) 추가, (m1) Source 3b/5 중복 해소, (m2) 4a R² 상한 설명 보정(tabular 기준), (m3) 추정치 검증 계획 추가 |
| v12.0 | 2026-03-28 | Codex 리뷰 9차: (M1) fallback에서 서울옥션 직접 수집 제외(스크래핑 금지 원칙 정합), (M2) K-ARTMARKET 법적 STOP/GO를 공공데이터 요청/웹 수집 분기로 분리, (m1) Aubry et al. (2025) 참고문헌 추가, (m2) Source 3b/5 완전 통합—9.1 테이블 번호 정리 |
| v13.0 | 2026-03-28 | Codex 리뷰 10차: (C1) 4b fallback 경로에 별도 게이트 추가(cold artist 비율 제약 해제, MdAPE ≥ 0.5%p), (M1) Section 3.3 이미지 확보 문구를 파트너십 전제로 통일, (M2) STOP/GO 프로세스에 K-ARTMARKET 추가·B-1 절차 중복 해소, (M3) 법적 원칙 문구를 소스별 정책 우선으로 수정(공공데이터 자유배포 인정), (m1) WikiArt을 4b에서 4c 선행준비(C-0.5)로 이동 |
| v14.0 | 2026-03-28 | Codex 리뷰 11차: (M1) fallback 진입 조건에 Artsy 법적 STOP/GO GO 판정 추가, (M2) fallback 전용 데이터 품질 게이트 DQ-F1~F3 추가(precision ≥ 90%, 커버리지 ≥ 30%, 오매칭 ≤ 3%), (m1) Section 8 및 9.4 성능표에 fallback 경로 별도 행 추가 |
