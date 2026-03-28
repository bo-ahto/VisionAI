# Phase 4 가격 예측 고도화 기획서 (v8.0)

> **작성일**: 2026-03-28 | **개정일**: 2026-03-28 (v8.0 — Codex 리뷰 7차 반영)
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
| 카탈로그 이미지 | ❌ | K-Auction 웹사이트에서 수집 필요 (Tier 3) |
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

---

## 8. 요약

**핵심 전략: 기존 CSV 데이터에서 추출 가능한 작가 이력 피처를 warm/cold 분리 평가와 함께 극대화하고, 유사 작품 매칭(backoff hierarchy 포함)을 추가한 후, 가격대별 모델 분리 + 앙상블을 검증적으로 적용.**

| Tier | 개선 방법 | 예상 MdAPE | 추가 데이터 |
|------|----------|-----------|-----------|
| **현재** | Phase 3 기본 | 34% | — |
| **Tier 1** | 작가 이력 + warm/cold 평가 + 유사 매칭 + 시장 피처 | 31~33% | 불필요 |
| **Tier 2** | + Two-Step + 앙상블 (검증 후) | 29~31% (stretch) | 불필요 |
| **Tier 3** | + 이미지 + NLP | 28~30% | 이미지 필요 |

**가장 중요한 한 가지: 작가의 최근 낙찰가(`artist_last_hammer_price`)가 warm artist에서 가장 강력한 앵커.** 단, 전체 작가의 45.9%가 cold artist이므로 warm/cold 분리 전략이 Phase 4의 성패를 결정.

---

*본 기획서는 학술 문헌 7편 + Codex 리뷰 권고를 기반으로 작성되었으며, Codex 리뷰 대상입니다.*

### 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.0 | 2026-03-28 | 초안 작성 |
| v2.0 | 2026-03-28 | Codex 리뷰 1차: 목표치 보수적 조정, 문헌 인용 정리, 우선순위 재정렬, 리스크 확장, 게이트 현실화 |
| v3.0 | 2026-03-28 | Codex 리뷰 2차: comp sales 순환참조 제거, 참고문헌 저자명 정정, quantile 일관성 명시, 변수명 정정, 리스크 14개 확장 |
| v4.0 | 2026-03-28 | Codex 리뷰 3차: 목표 재조정, warm/cold 분리 평가 추가, comp backoff hierarchy, 서지 정정, 스태킹 단조성 보장, Cold Start baseline 명시, Tier 2 진입 게이트 추가, Sprint 기간 현실화, 리스크 16개 확장 |
| v5.0 | 2026-03-28 | Codex 리뷰 4차: 근거-개선폭 연결 보정, 서빙 모드 듀얼 아키텍처, Split Conformal Calibration, 리스크 20개 확장 |
| v6.0 | 2026-03-28 | Codex 리뷰 5차: G14 bin 기준 5,000→2,000건 (고가 bin 3,618건 현실 반영), 서빙 모드를 ad-hoc 단일 평가 경로로 통일 (배치 모드는 향후 확장, 현 단계에서는 training-serving skew 방지 우선) |
