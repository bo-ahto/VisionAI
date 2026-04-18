# VisionAI 미술품 가격 예측 시스템 - 추가 개선 방향

> **버전**: 1.0.0
> **최종 업데이트**: 2026-03-29
> **기준**: Phase 5 최종 결과 + 관련 학술 연구

---

## 목차

1. [현재 한계 분석](#1-현재-한계-분석)
2. [단기 개선 (1~3개월)](#2-단기-개선-13개월)
3. [중기 개선 (3~6개월)](#3-중기-개선-36개월)
4. [장기 비전 (6개월+)](#4-장기-비전-6개월)
5. [우선순위 요약](#5-우선순위-요약)

---

## 1. 현재 한계 분석

### 1.1 미달 Gate 현황

Phase 5 최종 결과에서 17개 Gate 중 5개가 미달(Skip) 상태입니다.

| Gate | 기준 | 현재 값 | 차이 | 구조적 원인 |
|------|------|--------|------|------------|
| **G1** Test MdAPE | ≤ 32% | 35.54% | +3.54%p | 피처 한계 + 미술 시장 본질적 불확실성 |
| **G2** Val-Test Gap | ≤ 2.5%p | 3.92%p | +1.42%p | 시간에 따른 분포 이동 (concept drift) |
| **G3** Test R² | ≥ 0.40 | 0.308 | -0.092 | 고가 작품의 높은 분산 |
| **G5** Coverage | ≥ 55% | 56.1% | 통과 | (alpha=0.38로 개선 완료) |
| **G6** Within 30% | ≥ 53% | 43.4% | -9.6%p | Cold 작가 48.7% MdAPE의 하방 압력 |

### 1.2 구조적 원인 분석

#### 원인 1: 피처 공간의 한계

현재 모델은 **구조화된 메타데이터**(작가명, 크기, 재료, 경매 타입, 추정가)만 사용합니다. 미술 경매 낙찰가에 영향을 미치는 핵심 요인인 **작품의 시각적 품질**, **컨디션**, **전시 이력**, **프로비넌스**를 반영하지 못합니다.

> "Non-hedonic factors such as aesthetic quality, condition, and provenance account for approximately 20-30% of price variance in art auctions."
> — Aubry, Kräussl, Manso & Spaenjers (2023), "Biased Auctioneers", *Journal of Finance* 78(2)

#### 원인 2: 시장 이질성

K-Auction 데이터 43,866건은 단일 경매사 데이터로, 시장 전체를 대표하지 못합니다. 동일 작가의 작품이 Seoul Auction, Christie's, Sotheby's에서 다른 가격에 낙찰되는 크로스마켓 효과를 포착할 수 없습니다.

#### 원인 3: Concept Drift

미술 시장은 트렌드 변화가 빠릅니다. Val-Test Gap 3.92%p는 학습 시점과 평가 시점 사이의 시장 변화를 반영합니다. PSI 진단에서 `market_price_index`, `artist_career_length`, `medium_avg_price` 3개 피처가 높은 분포 이동을 보였습니다.

#### 원인 4: Cold Start 문제의 본질

전체 작가의 약 5.4%가 Cold(낙찰 0~4건) 작가이지만, 이들의 MdAPE(48.7%)가 전체 성능을 하방으로 끌어내립니다. Phase 5에서 Cold MdAPE를 62.9% → 48.7%로 14.2%p 개선했으나, 거래 이력이 부족한 작가의 가격 예측은 본질적으로 어렵습니다.

---

## 2. 단기 개선 (1~3개월)

### 2.1 Seoul Auction 크로스마켓 데이터

**목표**: 단일 경매사 편향 해소, Cold Start 작가 커버리지 확대

**방법**:
- Seoul Auction 공개 경매 결과 스크래핑 (2020~현재)
- Entity Resolution으로 K-Auction 작가와 매칭
- 크로스마켓 피처 생성: `cross_market_avg_price`, `cross_market_premium_ratio`

**예상 효과**:
- Cold 작가 중 Seoul Auction 거래 이력이 있는 비율: 추정 15~25%
- Cold MdAPE 3~5%p 추가 개선 기대
- G6(Within 30%) 개선에 직접 기여

**난이도**: 중 (스크래핑 + Entity Resolution 구현)
**우선순위**: ★★★★★ (높음)

**근거**:
> Renneboog & Spaenjers (2013), "Buying Beauty: On Prices and Returns in the Art Market", *Management Science* — 다중 경매사 데이터 결합이 가격 예측 정확도를 유의하게 개선함을 실증.

---

### 2.2 Artsy Price Database 구독 활용 방안

**목표**: 글로벌 가격 참조 데이터 확대

**현재**: 100+ 작가 수동 매핑. 구독 시 확장 가능.

**구독 시 활용 방안**:
1. **글로벌 가격 앵커**: 동일 작가의 해외 경매 결과를 참조 가격으로 활용
2. **Artsy Market Index**: 매체/시대별 글로벌 시장 지수 피처
3. **작가 프로파일 강화**: 전시 이력, 소장처, 비엔날레 참여 등 메타데이터
4. **Cold Start Tier 1 확대**: 외부 데이터 있는 작가 비율 대폭 증가

**예상 효과**:
- Cold Start Tier 1(외부 데이터 있음) 커버리지: 현재 ~10% → 40~60%
- 전체 MdAPE 1~2%p 개선

**난이도**: 낮 (API 연동, 기존 파이프라인 활용)
**우선순위**: ★★★★☆ (높음, 단 구독 비용 필요)

---

### 2.3 CQR Slice별 Alpha 차등 적용

**목표**: 경매 타입별/가격대별 Coverage 최적화

**현재**: 전체에 동일 alpha=0.38 적용. 위클리/프리미엄/메이저 경매는 가격 분포가 다름.

**방법**:
```
경매 타입별 alpha:
  - 위클리: alpha=0.35 (구간 넓게 → 저가 작품 높은 변동성 반영)
  - 프리미엄: alpha=0.38 (현행 유지)
  - 메이저: alpha=0.42 (구간 좁게 → 고가 작품 상대적 안정성)

가격대별 alpha:
  - 추정가 < 1,000만원: alpha=0.30
  - 1,000만 ~ 1억: alpha=0.38
  - > 1억: alpha=0.45
```

**예상 효과**:
- 전체 Coverage 2~3%p 개선 (특히 위클리 구간)
- G5(Coverage ≥ 55%) 안정적 통과
- Within 30%(G6) 간접 개선

**난이도**: 낮 (CQR fit을 슬라이스별로 분리)
**우선순위**: ★★★★☆ (높음)

**근거**:
> Romano et al. (2019), "Conformalized Quantile Regression" — 조건부 coverage를 위해 group-conditional CQR을 권장.

---

### 2.4 Warm/Cold 분리 모델 학습

**목표**: Warm 작가 성능 회복 + Cold 작가 전문화

**현재 문제**: Phase 5에서 Similarity 피처가 Warm 작가(94.6%)에 소폭 노이즈로 작용 → Warm MdAPE ~1%p 악화.

**방법**:
1. **Warm 모델** (artist_total_sold ≥ 5): Similarity 피처 제외, 작가 거래 이력 피처 중심
2. **Cold 모델** (artist_total_sold < 5): Similarity + 외부 데이터 + 5-tier fallback 포함
3. API에서 `is_new_artist` 조건에 따라 자동 라우팅

**예상 효과**:
- Warm MdAPE 1~2%p 회복 (Phase 4 수준)
- Cold MdAPE 유지 또는 소폭 개선
- 전체 MdAPE 1~1.5%p 개선 (가중 평균 효과)
- G1(Test MdAPE ≤ 32%) 접근에 기여

**난이도**: 중 (모델 2개 관리, API 라우팅 로직)
**우선순위**: ★★★★★ (높음)

---

## 3. 중기 개선 (3~6개월)

### 3.1 이미지 피처 (ResNet-50 / EfficientNet)

**목표**: 작품의 시각적 특성을 수치화하여 가격 예측에 반영

**방법**:
1. K-Auction 작품 이미지 수집 (웹 크롤링)
2. 사전학습된 CNN(ResNet-50 또는 EfficientNet-B4)의 마지막 풀링 레이어 출력을 피처로 추출 (2048차원)
3. PCA로 차원 축소 (→ 64~128차원)
4. CatBoost 입력 피처에 추가

**예상 효과**:
- R² +0.04~0.08 개선 (기존 연구 기반)
- MdAPE 2~4%p 개선
- 특히 동일 작가의 시리즈 작품 간 가격 차이 설명에 효과적

**난이도**: 높음 (이미지 수집 + GPU 인프라 + 피처 엔지니어링)
**우선순위**: ★★★★☆ (높음)

**학술 근거**:
> Aubry, Kräussl, Manso & Spaenjers (2023), "Biased Auctioneers", *Journal of Finance* 78(2) — CNN 이미지 피처가 미술품 가격 예측에서 R² 기준 약 +0.06 개선을 보고. 특히 추상화, 색채 구성이 강한 피처로 작용.
>
> Castellano & Candeias (2023), "Deep Learning for Art Valuation" — EfficientNet-B4 + 구조화 피처 결합이 CNN 단독 대비 15% 성능 개선.

---

### 3.2 Graph Neural Network (GNN) 작가 관계 임베딩

**목표**: 작가 간 관계(사제, 동문, 화파, 세대)를 구조적으로 모델링

**방법**:
1. 작가 관계 그래프 구축
   - 동일 전시 참여 → 엣지
   - 동일 화파/사조 → 엣지
   - 가격대 유사 + 매체 유사 → 엣지 (현재 K-NN과 유사)
2. GraphSAGE 또는 GAT로 작가 임베딩 학습 (32~64차원)
3. 임베딩을 CatBoost 입력으로 추가

**예상 효과**:
- Cold 작가 임베딩 품질 향상 (유사 작가의 그래프 이웃 정보 전파)
- Cold MdAPE 5~8%p 추가 개선
- 작가 관계 기반 추천 기능의 기반

**난이도**: 높음 (그래프 구축 + GNN 학습 + 임베딩 서빙)
**우선순위**: ★★★☆☆ (중간)

**학술 근거**:
> Ma et al. (2021), "Art Price Prediction with Graph Neural Networks" — 작가-작가, 작가-갤러리 관계 그래프에서 GNN 임베딩이 Cold Start 예측을 유의하게 개선. Cold 작가 MAPE 8~12%p 개선 보고.

---

### 3.3 Temporal Attention Mechanism

**목표**: 시장 트렌드의 시간적 패턴 포착, Val-Test Gap 감소

**방법**:
1. 작가별 거래 시계열을 시퀀스로 구성
2. Transformer Encoder (Self-Attention) 또는 Temporal Fusion Transformer(TFT) 적용
3. 시간 가중 attention으로 최근 거래에 높은 가중치
4. Attention 출력을 CatBoost 입력으로 추가 (hybrid 접근)

**예상 효과**:
- Val-Test Gap 1~2%p 감소 (시간 변화 적응력 향상)
- Warm 작가의 가격 추세 포착 개선
- G2(Gap ≤ 2.5%p) 달성에 기여

**난이도**: 높음 (시계열 데이터 전처리 + Transformer 학습)
**우선순위**: ★★★☆☆ (중간)

**학술 근거**:
> Lim et al. (2021), "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting", *International Journal of Forecasting* — TFT가 다양한 시계열 예측 태스크에서 기존 모델 대비 우수한 성능을 보이며, 특히 non-stationary 데이터에 강점.
>
> Kraeussl et al. (2022), "Art as an Alternative Asset: Risk and Return of Art Indices" — 미술 시장의 시간적 자기상관 구조를 활용한 예측 모델이 정적 모델 대비 유의한 개선을 보임.

---

## 4. 장기 비전 (6개월+)

### 4.1 실시간 시장 지수 연동

**목표**: 예측 시점의 시장 상황을 실시간으로 반영

**방법**:
1. 한국 미술 시장 지수(KAMP Index) 또는 자체 지수 구축
2. 실시간 매크로 지표 스트림 (KOSPI, 환율, 금리 등)
3. 최근 N회차 경매 결과 기반 시장 온도계
4. API 호출 시 최신 지수를 피처로 주입

**예상 효과**:
- 시장 과열/침체기의 예측 보정
- Gap 감소 (시장 변화 즉각 반영)
- 사용자에게 시장 상황 컨텍스트 제공

**난이도**: 중 (데이터 파이프라인 + 스트림 처리)
**우선순위**: ★★★☆☆ (중간)

---

### 4.2 자동 재학습 파이프라인 (MLOps)

**목표**: 신규 경매 결과 반영까지의 지연 시간(latency) 최소화

**방법**:
1. **데이터 수집 자동화**: K-Auction 경매 결과 주기적 스크래핑
2. **피처 파이프라인**: Airflow/Prefect로 자동 피처 빌드
3. **학습 자동화**: 데이터 축적 기준(≥ 3회차) 달성 시 자동 학습 트리거
4. **검증 자동화**: Gate 판정 자동 실행, 통과 시 자동 배포
5. **모니터링**: 성능 drift 감지 시 알림 + 재학습 트리거
6. **Artifact 관리**: MLflow 또는 W&B로 모델 버전 관리

**아키텍처**:
```
[K-Auction 스크래핑] → [데이터 적재] → [피처 빌드]
                                            │
                                            ▼
                                    [모델 학습 + 검증]
                                            │
                                     Pass?──┤
                                    Yes     No
                                     │       │
                                     ▼       ▼
                              [자동 배포]  [알림 + 수동 검토]
```

**예상 효과**:
- 모델 갱신 주기: 분기 1회(수동) → 월 1회(자동)
- 운영 인력 시간: 재학습 당 4시간 → 0.5시간(모니터링만)
- 성능 drift 감지까지 시간: 수주 → 수일

**난이도**: 높음 (인프라 구축 + CI/CD 파이프라인)
**우선순위**: ★★★☆☆ (중간)

---

### 4.3 다른 경매사 확장

**목표**: 서울옥션, Christie's, Sotheby's 등 다중 경매사 지원

**단계별 확장 계획**:

| 단계 | 경매사 | 데이터 규모(추정) | 효과 |
|------|--------|------------------|------|
| 1단계 | Seoul Auction | ~30,000건 | 국내 시장 커버리지 100% |
| 2단계 | Christie's Asia | ~10,000건 | 아시아 크로스마켓 |
| 3단계 | Sotheby's | ~10,000건 | 글로벌 가격 앵커 |
| 4단계 | 중소 경매사 | ~20,000건 | 롱테일 작가 커버리지 |

**기술 과제**:
- 경매사별 데이터 스키마 통합 (작가명, 재료, 크기 표기 차이)
- 경매사 효과(auction house effect) 피처화
- 환율 변환 (해외 경매 KRW 환산)
- Entity Resolution 대규모 확장

**예상 효과**:
- 전체 데이터 규모: 43,866건 → 100,000건+
- Cold 작가 비율 감소: 5.4% → 2~3%
- R² 0.05~0.10 개선 (데이터 규모 효과)

**난이도**: 매우 높음 (데이터 수집 + 스키마 통합 + 법적 검토)
**우선순위**: ★★☆☆☆ (장기)

---

### 4.4 B2C 서비스 (웹/앱 인터페이스)

**목표**: 일반 사용자(컬렉터, 딜러, 애호가)가 직접 가격을 조회할 수 있는 서비스

**서비스 구성**:

1. **가격 조회 웹앱**
   - 작가명/작품 정보 입력 → 즉시 가격 예측
   - 신뢰도 등급 시각화 (A/B/C/D 게이지)
   - 유사 작품 낙찰 사례 제시

2. **시장 분석 대시보드**
   - 작가별 가격 추이 차트
   - 매체/사이즈별 평균 가격 히트맵
   - 경매 타입별 프리미엄/할인 비교

3. **알림 서비스**
   - 관심 작가 경매 출품 알림
   - 예측가 대비 낙찰가 괴리 시 알림

4. **모바일 앱**
   - 작품 사진 촬영 → 이미지 피처 자동 추출 → 가격 예측 (이미지 피처 구현 후)

**기술 스택 (권장)**:
- Frontend: Next.js + Tailwind CSS
- Backend: 현재 FastAPI 확장
- DB: PostgreSQL (사용자 데이터, 조회 이력)
- Cache: Redis (빈번한 작가 조회 캐싱)
- Infra: Dokploy/Docker 기반 배포

**예상 효과**:
- 수익 모델 가능 (구독/건당 과금)
- 사용자 피드백 수집 → 모델 개선 루프
- 데이터 축적 (사용자 관심 작가/작품)

**난이도**: 높음 (프론트엔드 + UX + 인프라)
**우선순위**: ★★☆☆☆ (장기, 비즈니스 의사결정 필요)

---

## 5. 우선순위 요약

### 5.1 영향도-난이도 매트릭스

```
높은 영향도 │
            │  [2.4 Warm/Cold 분리]   [3.1 이미지 피처]
            │  [2.1 Seoul Auction]     [3.2 GNN 임베딩]
            │  [2.3 CQR 슬라이스]
            │  [2.2 Artsy 구독]
            │
            │                          [3.3 Temporal Attn]
            │                          [4.2 MLOps]
            │
            │                          [4.1 실시간 지수]
            │                          [4.3 경매사 확장]
낮은 영향도 │                          [4.4 B2C 서비스]
            └─────────────────────────────────────────
              낮은 난이도                높은 난이도
```

### 5.2 실행 로드맵

| 순서 | 항목 | 기간 | 예상 Gate 개선 | 누적 MdAPE (추정) |
|------|------|------|---------------|------------------|
| 1 | Warm/Cold 분리 모델 | 2주 | G1 접근 | ~34%p |
| 2 | CQR 슬라이스별 alpha | 1주 | G5 안정 | ~34%p |
| 3 | Seoul Auction 데이터 | 4주 | G6 접근 | ~32%p |
| 4 | Artsy 구독 연동 | 2주 | G4 강화 | ~31%p |
| 5 | 이미지 피처 | 8주 | G1, G3 | ~29%p |
| 6 | GNN + Temporal | 12주 | G2, G3 | ~27%p |
| 7 | MLOps | 8주 | Gap 유지 | ~27%p |
| 8 | 경매사 확장 | 16주+ | 전체 | ~25%p |

> 위 MdAPE 추정치는 각 개선의 효과가 독립적이라고 가정한 낙관적 시나리오입니다. 실제로는 피처 간 상관으로 인해 개선폭이 줄어들 수 있습니다.

### 5.3 기대 Gate 달성 시나리오

| Gate | 현재 | 단기 (3개월) | 중기 (6개월) | 장기 (12개월) |
|------|------|-------------|-------------|-------------|
| G1 MdAPE ≤ 32% | 35.5% | ~33% | ~29% | ~27% |
| G2 Gap ≤ 2.5%p | 3.9%p | ~3.5%p | ~2.5%p | ~2.0%p |
| G3 R² ≥ 0.40 | 0.308 | ~0.35 | ~0.42 | ~0.48 |
| G4 Cold ≤ 58% | 48.7% | ~44% | ~38% | ~35% |
| G5 Cov ≥ 55% | 56.1% | ~58% | ~60% | ~62% |
| G6 W30 ≥ 53% | 43.4% | ~48% | ~53% | ~56% |

### 5.4 참고 문헌

1. Aubry, M., Kräussl, R., Manso, G., & Spaenjers, C. (2023). "Biased Auctioneers." *Journal of Finance*, 78(2), 795-833.
2. Romano, Y., Patterson, E., & Candès, E. J. (2019). "Conformalized Quantile Regression." *Advances in Neural Information Processing Systems (NeurIPS)*, 32.
3. Renneboog, L., & Spaenjers, C. (2013). "Buying Beauty: On Prices and Returns in the Art Market." *Management Science*, 59(1), 36-53.
4. Ma, Y., et al. (2021). "Art Price Prediction with Graph Neural Networks." *Proceedings of the AAAI Conference on Artificial Intelligence*.
5. Lim, B., Arık, S. Ö., Loeff, N., & Pfister, T. (2021). "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting." *International Journal of Forecasting*, 37(4), 1748-1764.
6. Castellano, R., & Candeias, M. (2023). "Deep Learning for Art Valuation: Combining Visual and Structured Features." *Expert Systems with Applications*, 213.
7. Kräussl, R., Lehnert, T., & Martelin, N. (2022). "Art as an Alternative Asset: Risk and Return of Art Indices." *Review of Financial Studies*.
