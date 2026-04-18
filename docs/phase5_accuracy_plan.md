# Phase 5 가격 예측 정확도 고도화 기획서 (v2.0)

> **작성일**: 2026-03-29 | **개정일**: 2026-03-29 (v2.0 — Codex 1차 리뷰 MAJOR 6건 반영)
> **목표**: Test MdAPE 34.38% → 31~32% (기본) / ≤29% (stretch), Val-Test gap 4.2%p → ≤2.5%p
> **기반**: Phase 4 최종 결과 + 논문 12편 + 상용 시스템 분석
> **핵심 원칙**: Test-first KPI, ablation 기반 누적 개선, 추정가 직접 입력 제거 (proxy 이전은 별도 트랙)

---

## 1. 현황 진단

### 1.1 Phase 4 최종 성능

| 지표 | Validation | Test | Gap |
|------|-----------|------|-----|
| MdAPE | 30.16% | 34.38% | +4.22%p |
| R² | 0.608 | 0.312 | -0.296 |
| Within 30% | 49.9% | — | — |
| Coverage | 54.6% | — | — |

### 1.2 세그먼트별 분석

| 세그먼트 | MdAPE | 비중 | 진단 |
|---------|-------|------|------|
| Warm artist | 28.82% | 94.6% | 개선 여지 제한적 |
| **Cold artist** | **62.87%** | **5.4%** | **최대 병목** |
| 메이저 | 32.82% | ~30% | 고가 작품 편차 큼 |
| 프리미엄 | 23.70% | ~40% | 가장 양호 |
| 위클리 | 29.66% | ~30% | 저가 작품 노이즈 |

### 1.3 핵심 병목 3가지

1. **Cold Artist 정보 부재**: 45.9% 작가가 K-Auction 1건만 보유. Bayesian shrinkage만으로는 개별 작가 특성 반영 불가.
2. **추정가 정보 손실**: 추정가는 전문가의 comparable sales + 시장 심리 + 전략을 압축한 변수. 제거 시 R² 0.936→0.608으로 급락.
3. **Val-Test 과적합**: 4.22%p gap은 시간에 따른 분포 변화(distribution shift) 또는 피처 누수를 시사. **원인 미분해 상태이며, Sprint 0에서 진단 필수.**

### 1.4 이론적 상한 (논문 기반)

> **주의**: 아래 R² 수치는 Mei et al. (2025)의 서양 대형 경매(Sotheby's/Christie's) 100만+ 데이터 기반. K-Auction 43,866건과 시장 규모·작가 구성·데이터 품질이 다르므로 **방향성 참고만 가능**하며, 직접 수치를 우리 목표에 대입해서는 안 된다.

| 시나리오 | 논문 Reported R² | K-Auction 추정 범위 | 출처 |
|---------|-----------------|-------------------|------|
| 추정가 포함 (전문가) | ~0.93 | 0.90~0.94 (Phase 1-2 실측) | Mei et al. (2025) |
| 반복매매 + rich features | ~0.77~0.79 | 적용 불가 (반복매매 <5%) | Mei et al. (2025) |
| Fresh-to-market, tabular | ~0.54~0.59 | 0.50~0.60 | Mei et al. (2025) |
| Fresh-to-market, multimodal | ~0.61~0.65 | 0.55~0.65 (이미지 수집 시) | Mei et al. (2025) |
| **현재 Phase 4 (V)** | — | **0.608** | **측정값** |

---

## 2. 학술 근거 (논문 12편)

### 2.1 핵심 참조 논문

| # | 논문 | 저자 | 연도 | 출판처 | 핵심 기여 |
|---|------|------|------|--------|----------|
| 1 | Deep Learning for Art Market Valuation | Mei et al. | 2025 | arXiv:2512.23078 | Multimodal R²=0.65, fresh-to-market |
| 2 | Biased Auctioneers | Spaenjers et al. | 2023 | *Journal of Finance* | ML이 추정가보다 정보 효율적 |
| 3 | Conformalized Quantile Regression | Romano et al. | 2019 | NeurIPS | 분포 무관 coverage 보장 (exchangeability 가정 하) |
| 4 | Conformal Prediction Beyond Exchangeability | Barber et al. | 2023 | *Annals of Statistics* | 비교환 시계열용 weighted conformal |
| 5 | ML Algorithms and Fine Art Pricing | Fedderke & Carugno | 2024 | *Expert Systems with Applications* | GB > Hedonic OLS, 43K SA 데이터 |
| 6 | Two-step XGBoost for Artwork Prices | Kim & Kim | 2024 | JKSU-CIS | 가격 구간 분류→구간별 회귀 |
| 7 | Distilling the Knowledge in a NN | Hinton et al. | 2015 | arXiv:1503.02531 | Knowledge Distillation 원형 |
| 8 | Social Signals Predict Art Prices | Nature SR | 2024 | *Nature Scientific Reports* | 소셜 신호 > 시각 피처 (contemporary) |
| 9 | Artist Similarity with GNN | — | 2021 | arXiv:2107.14541 | 작가 네트워크 임베딩 |
| 10 | Hedonic Pricing on Fine Art Market | — | 2020 | *MDPI Information* | Heckman Selection, 미낙찰 편향 |
| 11 | Monthly Art Market Returns | — | 2020 | *MDPI JRFM* | 매크로-미술시장 상관 |
| 12 | CatBoostLSS Probabilistic Forecasting | Uber AI | 2020 | arXiv:2001.02121 | Location-Scale-Shape 확률적 예측 |

### 2.2 논문별 대응표 (K-Auction 적용성)

| # | 데이터셋 | fresh-to-market | 반복매매 | 이미지 | metric | 우리와 다른 점 | 차용 가능 요소 |
|---|---------|-----------------|---------|--------|--------|-------------|-------------|
| 1 | Sotheby's/Christie's 100만+ | O | O | O | R² | 서양 고가 작품 중심 | multimodal fusion 구조, cold 작품 처리 |
| 2 | 100만+ paintings | X | O | X | buy-in probability | 추정가 자체 분석 | estimate 효율성 비교 방법론 |
| 3 | 합성+부동산 | X | X | X | coverage | 일반 ML, 미술 아님 | CQR 알고리즘 직접 적용 |
| 5 | SA 43K lots | O | X | X | R², MAPE | 남아공 시장 | 유사 규모 데이터, GB 우위 확인 |
| 7 | ImageNet (분류) | X | X | O | accuracy | 분류 문제 | 회귀 적응: MSE(teacher, student) |
| 8 | 120K+ listings | X | X | X | R² | 갤러리 판매, 경매 아님 | social signal 피처 (우리는 미보유) |

### 2.3 핵심 공식

**Knowledge Distillation (회귀 적응)**:
```
y_distill = β · y_true + (1-β) · f_teacher(X_with_estimate)
```
- 이는 추정가를 포함한 teacher의 함수값을 student에 압축 이전하는 것이며, "추정가 제거"가 아님
- β=0.7~0.9, Teacher 예측은 반드시 OOF 방식으로 생성 (누수 방지)

**CQR** (Romano et al., 2019):
```
C(X_new) = [q̂_α/2(X_new) - Q, q̂_(1-α/2)(X_new) + Q]
Q = (1-α)(1 + 1/n)-quantile of {E₁, ..., Eₙ}
Eᵢ = max(q̂_α/2(Xᵢ) - Yᵢ, Yᵢ - q̂_(1-α/2)(Xᵢ))
```
- **적용 조건**: exchangeability 가정 하 calibration split에서 coverage ≥ 1-α 보장
- **시계열 환경**: 별도 weighted/split-by-time conformal 설계 필요 (Barber et al., 2023)
- 자동으로 temporal shift에 대응하지 않음 — K-Auction 시계열에서 별도 검증 필수

**Enhanced Bayesian Shrinkage**:
```
현재: μ_shrunk = (n·x̄_group + m·μ_global) / (n + m), m=10
확장: μ_shrunk = (n·x̄_group + m·μ_similar_cluster) / (n + m)
```

---

## 3. 추정가 의존도 분리 (Strict / Distilled 2-트랙)

추정가 활용 범위에 따라 두 트랙을 명확히 분리한다.

| 트랙 | 정의 | 허용 | 금지 |
|------|------|------|------|
| **Strict No-Estimate** | Train/Infer 모두 estimate-derived signal 없음 | hedonic features, macro, artist profile, similarity | estimate 관련 모든 변수, teacher prediction, global_estimate_avg |
| **Estimate-Distilled** | Infer 시 estimate 입력 없음, Train 시 teacher/external estimate aggregate 허용 | 위 + teacher soft target, global_estimate_avg (train only) | inference 시 estimate 입력 |

- **두 트랙 성능을 별도로 보고** (ablation)
- Distilled 트랙이 Strict보다 유의미하게 좋을 때만 채택 (paired t-test p<0.05)
- 외부 데이터 `global_estimate_avg`는 Strict 트랙에서 제외

---

## 4. 5대 개선 전략 (우선순위 재정렬)

> **원칙**: Gap 진단 → 데이터 정합화 → 구조 개선 → 모델 개선 순서. Distillation은 Gap 진단 완료 후 착수.

### Sprint 0 (전제): Val-Test Gap 진단 (1주)

**목적**: 4.22%p gap의 원인을 분해하여 원인별 해결책 연결

**필수 분석**:
1. **시점별 성능 곡선**: 회차별 MdAPE 플롯 (train/valid/test)
2. **세그먼트별 gap 분해**: 메이저/프리미엄/위클리 × warm/cold별 gap
3. **Feature PSI (Population Stability Index)**: 각 피처의 valid→test 분포 변화 측정
4. **Feature missingness drift**: 피처 결측률의 valid→test 변화
5. **Cold artist 비중 변화**: valid vs test의 cold 비중
6. **가격대별 drift**: 상위/하위 가격대 성능 차이
7. **Leak audit**: auction date 이후 생성 피처, rollup 범위 재검증

**원인-해결 매핑**:
| 원인 | 해결책 |
|------|--------|
| Time drift | Rolling retrain, sample decay weighting |
| Segment mix 변화 | Stratified time split |
| Missingness drift | Robust fallback feature set |
| Feature leak | Feature blacklist |
| Cold 비중 증가 | Cold-specific 모델 강화 (전략 3, 4) |

**Gate**: `최근 3개 홀드아웃 윈도우 평균 성능 < 전체 valid 성능의 1.1배`

### 전략 1: 외부 데이터 정합화 + 매크로 지표 (Sprint 1)

**목적**: 새로운 정보 소스 추가 + 시장 상황 반영

#### 1a. 매크로 지표 통합

| 지표 | 소스 | 수집 방법 | 라그 |
|------|------|----------|------|
| KOSPI 종가 | 한국거래소 | 공공 API | -1M |
| USD/KRW 환율 | 한국은행 ECOS | 공공 API | -1M |
| 서울 아파트가격지수 | KB부동산 | 공공데이터 | -1M |
| 소비자물가지수 | 통계청 KOSIS | 공공 API | -1M |
| K-Auction 회차별 낙찰률 | 내부 CSV | 내부 계산 | -1회차 |
| K-Auction 회차별 평균가 | 내부 CSV | 내부 계산 | -1회차 |

#### 1b. 글로벌 경매 데이터 정합화

**Entity Resolution 규칙**:
- `artist_id_canonical`: K-Auction 작가명 → 정규화 (한글 기준, 영문 별칭 매핑)
- `name_match_confidence`: fuzzy match score ≥ 0.85만 사용
- `price_with_premium_flag`: hammer price 통일 (buyer's premium 제외)
- `currency` + `fx_rate_at_sale_month`: 경매 월 기준 환율 변환
- `unsold_flag`: 미낙찰 lot 분리 (selection bias 통제)
- `source_url` + `scrape_timestamp`: 수집 이력 추적

**중복 제거 규칙**:
- (작가, 작품제목, 경매일, 경매사)가 동일하면 1건만 유지
- 동일 작품 다른 경매사 → 별도 건으로 유지 (cross-market premium 계산용)

**KPI**: "K-Auction cold artist 중 매칭 성공률 ≥ 30%, high-confidence match precision ≥ 95%"

### 전략 2: Artist Similarity + Cold Start 5-tier (Sprint 2)

**목적**: Cold artist MdAPE 62.87% → 55~58% (기본)

**Cold Start 계층 확장 (3-tier → 5-tier)**:

| Tier | 조건 | Fallback 소스 | 최소 건수 |
|------|------|-------------|----------|
| 0 | K-Auction 거래 ≥ 5건 | 작가 자체 통계 | 5 |
| 1 | 글로벌/타경매사 데이터 있음 | 외부 가격 통계 | 3 |
| 2 | K-NN 유사 작가 매칭 | 유사 작가 가중 평균 | K≥3 |
| 3 | medium × auction_type | Bayesian shrinkage | 30 |
| 4 | medium only / global | 전역 통계 | 50 |

**Artist Similarity 구현**:
1. **Candidate generation**: 동일 매체 카테고리 작가 필터
2. **Hard filters**: 가격대 ±1 tier (저/중/고), 활동 기간 겹침
3. **Weighted pooling**: `w_i = 1 / (1 + d_i²)`, d는 [매체비율, 평균크기, 가격대, 경매타입비율, 활동기간] 거리

**Gate**: `cold subgroup별 coverage ≥ 90%`, `fallback 사용률 < 40%`

### 전략 3: Knowledge Distillation (Sprint 3, Estimate-Distilled 트랙)

**목적**: Phase 1-2 모델의 추정가 해석 능력을 Phase 3 모델에 간접 이전

**방법**:
1. **Teacher**: Phase 1-2 CatBoost (22 features, 추정가 포함)
2. **Student**: Phase 3 CatBoost (49+ hedonic features, 추정가 없음)
3. **OOF Teacher Prediction**: expanding window으로 train 데이터에만 teacher 예측 생성
4. **Student 학습**: `y_distill = β · ln(낙찰가) + (1-β) · ln(teacher_pred_oof)`, β=0.7~0.9

**필수 검증**:
- G11: Test set에 teacher prediction 미사용 확인
- Student feature attribution drift: teacher 의존도가 과도하지 않은지 SHAP 분석
- Strict vs Distilled 성능 paired t-test (p<0.05)

### 전략 4: Conformalized Quantile Regression (Sprint 3)

**목적**: 현재 additive shift calibration 대체

**구현**:
```python
# Calib set에서 conformity score 계산
E_i = max(q_low_i - y_i, y_i - q_high_i)
Q = np.quantile(E, (1 - alpha) * (1 + 1/n))
# Prediction interval
C(X_new) = [q_low(X_new) - Q, q_high(X_new) + Q]
```

**시계열 적용 주의**:
- 기본 CQR는 exchangeability 가정이므로, K-Auction 시계열에 직접 적용 시 coverage drift 가능
- **Split-by-time conformal**: calib set을 시간순으로 최근 N 회차로 제한
- **Weighted conformal** (Barber et al., 2023): 최근 데이터에 높은 가중치
- **검증**: 3개 이상의 시간 윈도우에서 coverage 측정, 전체/slice별 모두 검증

**Gate**: `CQR coverage ≥ (1-α)를 최근 3개 홀드아웃 윈도우 모두에서 달성`

### 전략 5: 매크로/시장 지표 → Sprint 1에 통합

(전략 1a에 포함, 별도 Sprint 아님)

---

## 5. 외부 데이터 수집 계획

### 5.1 실현 가능성 평가

| 소스 | 수집 방법 | 난이도 | 예상 건수 | 법적/ToS 리스크 | Cold fill-rate |
|------|----------|--------|----------|---------------|---------------|
| **한국은행 ECOS** | REST API (인증키) | 하 | 월별 300건 | 없음 (공공 API) | N/A (전체 적용) |
| **KB부동산지수** | 공공데이터 다운로드 | 하 | 월별 300건 | 없음 (공공) | N/A |
| **KOSIS 통계청** | REST API | 하 | 월별 300건 | 없음 (공공 API) | N/A |
| **Artsy 경매 확장** | MCP Playwright | 중 | 3K~5K건 | 낮음 (robots.txt 준수) | ~15% |
| **Seoul Auction** | 웹 스크래핑 | 중 | 10K~20K건 | 낮음 (공개 낙찰결과, rate limit 준수) | ~20% |
| **NamuWiki 작가** | API (CC BY-NC-SA) | 하 | 500~1K명 | 낮음 (라이선스 준수) | ~25% |
| **K-ARTMARKET** | 공공데이터포털 | 하~중 | 30K건 | 없음 | ~10% |
| **ARKO 예술위원회** | 공공데이터 | 하 | 전시/지원 | 없음 | ~5% |

### 5.2 수집 우선순위

**즉시 수집 (1주)**:
1. 한국은행 ECOS → KOSPI, 환율, CPI
2. KB부동산지수, KOSIS 통계
3. K-Auction 내부 회차별 통계

**단기 수집 (2~3주)**:
4. Artsy 확장 (K-Auction cold artist slug 매핑 → 스크래핑)
5. NamuWiki 작가 프로필
6. Seoul Auction 공개 결과 (robots.txt 확인 후)

**중기 수집 (1~2개월)**:
7. K-ARTMARKET 공공데이터 요청
8. ARKO 공공데이터

### 5.3 데이터 스키마

**글로벌 경매 (artsy_auctions_expanded.csv)**:
```
artist_id_canonical, artist_name_local, artist_slug, artwork_title, medium,
width_cm, height_cm, hammer_price_usd, estimate_low_usd, estimate_high_usd,
auction_house_norm, auction_date, sale_title, lot_number,
currency, fx_rate_at_sale_month, price_with_premium_flag,
unsold_flag, name_match_confidence, source_url, scrape_timestamp
```

**Seoul Auction (seoul_auction_results.csv)**:
```
artist_id_canonical, artist_name, artwork_title, medium, size_description,
width_cm, height_cm, estimate_low_krw, estimate_high_krw, hammer_price_krw,
auction_date, auction_type, lot_number, unsold_flag,
name_match_confidence, source_url, scrape_timestamp
```

**작가 프로필 (artist_profiles.csv)**:
```
artist_id_canonical, artist_name, birth_year, death_year, nationality, education,
education_tier, major_awards, award_count, museum_exhibitions_count,
gallery_representation, art_movement, active_period_start, active_period_end,
source, scrape_timestamp
```

**매크로 지표 (macro_monthly.csv)**:
```
year_month, kospi_close, kospi_mom_3m, usd_krw, apartment_index,
cpi, art_market_avg_price, art_market_sold_rate
```

### 5.4 소스별 정합화 규칙

| 소스 | 매칭 규칙 | 중복 제거 | 통화 변환 | Premium 통일 |
|------|----------|----------|----------|-------------|
| Artsy | slug 매핑 + fuzzy name ≥ 0.85 | (작가,제목,날짜,경매사) unique | USD→KRW 경매월 환율 | hammer only |
| Seoul Auction | 정확 매칭 (동일 한글명) | (작가,제목,날짜) unique | KRW 원본 | hammer only |
| NamuWiki | 정확 매칭 → fuzzy 보완 | 1인 1건 | N/A | N/A |
| ECOS/KOSIS | 월 키 매핑 | 자동 | 원본 | N/A |

---

## 6. 구현 로드맵

### Sprint 0: Val-Test Gap 진단 (1주)
- 시점별/세그먼트별 성능 곡선
- Feature PSI + missingness drift
- Cold 비중 변화 + 가격대 drift
- Leak audit
- **산출물**: gap 원인 보고서 + 원인별 해결책 매핑

### Sprint 1: 외부 데이터 수집 + 매크로 통합 (2~3주)
- 공공 API 수집 (ECOS, KOSIS, KB)
- Artsy 확장, Seoul Auction 스크래핑
- NamuWiki 작가 프로필
- Entity resolution + 정합화
- 피처 통합 + 재학습
- **검증**: Strict 트랙 ablation

### Sprint 2: Artist Similarity + Cold Start 5-tier (2주)
- K-NN similarity 구현
- Cold Start 5-tier fallback
- Cold MdAPE 개선 측정
- **검증**: cold subgroup별 coverage

### Sprint 3: Distillation + CQR (2주)
- OOF teacher prediction 생성
- Distilled 트랙 학습
- Split-by-time CQR 구현
- **검증**: Strict vs Distilled ablation, CQR coverage

### Sprint 4: 통합 + 최종 검증 (1~2주)
- 전 전략 통합 모델
- 3개 홀드아웃 윈도우 expanding window 검증
- 최종 Gate 통과 확인
- 결과 보고서

---

## 7. 성능 목표 + Gate 기준 (Test-first)

### 7.1 KPI 목표

| 지표 | Phase 4 현재 | Phase 5 기본 | Phase 5 Stretch |
|------|-------------|-------------|----------------|
| **Test MdAPE** | **34.38%** | **≤ 31~32%** | **≤ 29%** |
| Val MdAPE | 30.16% | ≤ 29% | ≤ 27% |
| **V-T Gap** | **4.22%p** | **≤ 2.5%p** | **≤ 2%p** |
| **Test R²** | **0.312** | **≥ 0.40~0.45** | **≥ 0.50** |
| Val R² | 0.608 | ≥ 0.62 | ≥ 0.65 |
| **Cold MdAPE** | **62.87%** | **≤ 55~58%** | **≤ 50%** |
| Coverage | 54.6% | ≥ 55% | ≥ 58% |
| Within 30% | 49.9% | ≥ 53% | ≥ 56% |

> **원칙**: 전략별 기대효과 합산 금지. Ablation 기반 누적 개선치만 표에 반영.

### 7.2 Quality Gate (17개)

| Gate | 기준 | 유형 | 검증 시점 |
|------|------|------|----------|
| G1 | Test MdAPE ≤ 32% | 필수 | Sprint 4 |
| G2 | Val-Test Gap ≤ 2.5%p | 필수 | Sprint 4 |
| G3 | Test R² ≥ 0.40 | 필수 | Sprint 4 |
| G4 | Cold MdAPE ≤ 58% | 필수 | Sprint 2+ |
| G5 | Coverage ≥ 55% | 필수 | Sprint 3+ |
| G6 | Within 30% ≥ 53% | 필수 | Sprint 4 |
| G7 | Leakage test ALL PASS | 필수 | 매 Sprint |
| G8 | Monotonicity ≥ 0.99 | 필수 | Sprint 4 |
| G9 | Cold Start 생성률 = 100% | 필수 | Sprint 2+ |
| G10 | Distillation test set 미사용 확인 | 필수 | Sprint 3 |
| G11 | CQR coverage ≥ (1-α), 최근 3윈도우 모두 | 필수 | Sprint 3 |
| G12 | OOF teacher prediction only (time-split) | 필수 | Sprint 3 |
| G13 | Student feature attribution drift < 0.3 | 필수 | Sprint 3 |
| G14 | 최근 3개 홀드아웃 평균 성능 < 전체 valid의 1.1배 | 필수 | Sprint 0, 4 |
| G15 | 외부 데이터 매칭 precision ≥ 95% | 참조 | Sprint 1 |
| G16 | 매크로 지표 12개월+ | 참조 | Sprint 1 |
| G17 | Cold subgroup별 coverage ≥ 90% | 참조 | Sprint 2 |

---

## 8. 리스크 및 완화

| # | 리스크 | 확률 | 영향 | 완화 | 탐지 지표 | Rollback 조건 |
|---|--------|------|------|------|----------|-------------|
| R1 | Distillation 효과 미미 | 중 | MdAPE 목표 미달 | β grid search, Strict 트랙과 비교 | Strict vs Distilled 차이 < 0.5%p | Strict 트랙으로 복귀 |
| R2 | Seoul Auction 스크래핑 차단 | 중 | 외부 데이터 부족 | Rate limiting, robots.txt 준수, 수동 수집 | HTTP 403/429 빈도 | Artsy + NamuWiki만으로 진행 |
| R3 | CQR 구간 과도 확장 | 저 | Coverage↑ 구간 무의미 | α 최적화, interval width 상한 설정 | median interval width > 2x Phase 4 | Additive shift 복귀 |
| R4 | Val-Test gap 미해소 | 중 | Test 성능 정체 | Sprint 0 진단 결과에 따른 원인별 대응 | Gap > 3%p after Sprint 4 | Feature selection + regularization |
| R5 | Cold artist 매칭률 저조 | 중 | Cold MdAPE 정체 | 이름 정규화 개선, 복수 소스 교차 | 매칭 성공률 < 15% | Similarity fallback 강화 |
| R6 | **작가명 매칭 오류 → 잘못된 통계 이전** | 중 | 모델 성능 저하 | Confidence threshold ≥ 0.85, 수동 검증 상위 100명 | Feature importance 이상 변동 | 외부 피처 전체 제거 |
| R7 | **Hammer vs total price 정의 불일치** | 중 | 가격 비교 왜곡 | Premium 포함 여부 명시, hammer only 통일 | 국가간 가격 비율 이상치 | Premium flag로 필터 |
| R8 | **환율/물가 보정 누락** | 저 | 글로벌 가격 왜곡 | 경매월 기준 fx_rate 일괄 적용 | 환율 급변 월 성능 저하 | Inflation adjustment 추가 |
| R9 | **미낙찰 lot 누락 (selection bias)** | 중 | 가격 과대 추정 | unsold_flag 분리, Heckman Selection 모델 검토 | 경매사별 sold rate 불일치 | unsold 포함 robust 학습 |
| R10 | **스크래핑 ToS 위반** | 저 | 법적 리스크 | robots.txt 준수, rate limit, 공개 데이터만 | ToS 변경 모니터링 | 해당 소스 수집 중단 |
| R11 | **Cold segment 표본 작아 개선폭 추정 분산 큼** | 고 | 효과 과대/과소 추정 | Bootstrap CI로 개선폭 보고 | Cold n < 100 | 95% CI 포함 보고 |
| R12 | **CQR coverage 충족하나 interval 과도** | 저 | 실용성 없음 | Width gate 추가 | width > 기존 1.5x | α 재조정 |

---

## 9. 추정가 직접 입력 제거 전략 요약

Phase 1-2에서 추정가가 담당했던 역할을 Phase 5에서 대체하는 구조:

| 추정가 역할 | Strict 트랙 대체 | Distilled 트랙 추가 |
|-----------|----------------|-------------------|
| **시장 가격 앵커** | Comparable sales + 글로벌 데이터 | + Teacher soft target |
| **Comparable sales** | K-Auction + Seoul Auction + Artsy 가격 | 동일 |
| **작가 평판** | Artist Similarity + NamuWiki 프로필 | 동일 |
| **시장 상황** | 매크로 지표 (KOSPI, 환율, 부동산) | 동일 |
| **불확실성** | CQR (조건부 coverage 보장) | 동일 |

**궁극적 목표**: Strict 트랙에서 Test MdAPE ≤ 32%, Distilled 트랙에서 ≤ 29~31% 달성.

---

## 부록 A: 참조 논문

1. Mei, J. et al. (2025). "Deep Learning for Art Market Valuation." *arXiv:2512.23078*
2. Spaenjers, C. et al. (2023). "Biased Auctioneers." *Journal of Finance* 78(2)
3. Romano, Y. et al. (2019). "Conformalized Quantile Regression." *NeurIPS 2019*
4. Barber, R.F. et al. (2023). "Conformal Prediction Beyond Exchangeability." *Annals of Statistics*
5. Fedderke, J. & Carugno, A. (2024). "ML Algorithms and Fine Art Pricing." *Expert Systems with Applications*
6. Kim, T. & Kim, J. (2024). "Two-step XGBoost for Artwork Prices." *JKSU-CIS*
7. Hinton, G. et al. (2015). "Distilling the Knowledge in a Neural Network." *arXiv:1503.02531*
8. "Social Signals Predict Contemporary Art Prices." (2024). *Nature Scientific Reports*
9. "Artist Similarity with Graph Neural Networks." (2021). *arXiv:2107.14541*
10. "Hedonic Pricing on the Fine Art Market." (2020). *MDPI Information*
11. "Monthly Art Market Returns." (2020). *MDPI JRFM*
12. "CatBoostLSS: Probabilistic Forecasting." (2020). Uber AI, *arXiv:2001.02121*

## 부록 B: 구현 파일 목록 (신규)

| 파일 | 용도 | Sprint |
|------|------|--------|
| `features/macro_indicators.py` | 매크로 지표 피처 | 1 |
| `features/artist_similarity.py` | K-NN 유사 작가 | 2 |
| `estimate_generator/distillation.py` | Knowledge Distillation | 3 |
| `estimate_generator/conformal_calibrator.py` | CQR | 3 |
| `scripts/collectors/collect_macro_data.py` | 공공 API 수집 | 1 |
| `scripts/collectors/scrape_seoul_auction.py` | Seoul Auction | 1 |
| `scripts/diagnose_gap.py` | Val-Test gap 진단 | 0 |
| `scripts/train_distilled_model.py` | Distillation 학습 | 3 |
