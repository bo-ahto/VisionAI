# 02. Literature Review — Hedonic Art Price Modeling

> **상태**: DRAFT (Week 1 발췌 작업 대상)
> **목적**: 본 트랙 모델 spec 의 학술 근거 + 비교 baseline + 인과 framing 정당화

## 1. 핵심 references (코덱스 12차 자문 추천)

### Tier 1 — 본 트랙의 직접 reference

#### ⭐ Rengers & Velthuis (2002) "Determinants of Prices for Contemporary Art in Dutch Galleries"
- **Journal**: Journal of Cultural Economics 26(1)
- **URL**: https://ideas.repec.org/a/kap/jculte/v26y2002i1p1-28.html
- **왜 핵심**: **1차 시장 (gallery primary market) 특화** — 본 트랙의 가장 직접적 reference
- **핵심 발견**:
  - Hedonic regression 적용
  - Size effect 강함 (양 elasticity)
  - Medium 효과 (oil > acrylic)
  - Artist career stage / age 강 effect
  - Gallery reputation 효과
- **활용**: Level 1 OLS hedonic spec 의 변수 선택 / coefficient sign 검증

#### ⭐ Renneboog & Spaenjers (2013) "Buying Beauty: On Prices and Returns in the Art Market"
- **Journal**: Journal of Financial Economics
- **URL**: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1352363
- **왜 핵심**: 2차 시장 hedonic 의 modern reference
- **핵심 발견**:
  - 1957-2007 art auction price index
  - Hedonic regression + price index construction
  - Size, medium, period, signature 효과
  - Risk-adjusted return 분석
- **활용**: Hedonic methodology + 변수 design

#### ⭐ Rosen (1974) "Hedonic Prices and Implicit Markets"
- **Journal**: Journal of Political Economy 82(1)
- **URL**: https://ideas.repec.org/a/ucp/jpolec/v82y1974i1p34-55.html
- **왜 핵심**: Hedonic regression 의 theoretical foundation
- **핵심 contribution**:
  - Differentiated product 의 implicit price 이론
  - Equilibrium hedonic price function
  - Identification: supply / demand 균형의 envelope curve
- **활용**: Methodological 정당화 + 한계 명시

### Tier 2 — Career stage / artist 변수 정당화

#### Galenson (2003) "The Life Cycles of Modern Artists"
- **Source**: NBER Working Paper 9539
- **URL**: https://www.nber.org/papers/w9539
- **핵심 가설**: 작가 경력 단계 (early/mid/late) 가 가격에 non-linear 영향
- **두 유형**:
  - **Conceptual innovator** (early peak): Picasso, Pollock — 30대 peak
  - **Experimental innovator** (late peak): Cézanne, Rothko — 50-60대 peak
- **활용**:
  - `career_stage` × `age_at_creation` interaction 정당화
  - Peak age non-linear term 추가 검토

### Tier 3 — Quantile / distribution 모델링

#### Koenker & Hallock (2001) "Quantile Regression"
- **Journal**: Journal of Economic Perspectives 15(4)
- **URL**: https://www.aeaweb.org/articles?id=10.1257/jep.15.4.143
- **왜 핵심**: Quantile regression methodology
- **활용**: Level 4 quantile regression methodology 정당화 (heavy-tail 가격 분포)

### Tier 4 — Auction / 2차 시장 비교 (background)

#### Beggs & Graddy (2009) "Anchoring Effects: Evidence from Art Auctions"
- **Journal**: American Economic Review 99(3)
- **URL**: https://www.aeaweb.org/articles?id=10.1257/aer.99.3.1027
- **핵심**: Auction estimate 가 final hammer price 에 anchoring effect
- **활용**: 1차 vs 2차 시장 가격 형성 메커니즘 차이 명시 (1차 = 갤러리 fixed pricing, 2차 = 입찰 dynamics)

#### Mei & Moses (2002) "Art as an Investment and the Underperformance of Masterpieces"
- **Journal**: American Economic Review 92(5)
- **URL**: https://archive.nyu.edu/handle/2451/26539
- **핵심**: Repeated sales index methodology
- **활용**: 본 트랙의 cross-section data 한계 (repeated sale 불가) 명시

#### Goetzmann (1993) "Accounting for Taste: Art and the Financial Markets"
- **Journal**: American Economic Review 83(5)
- **URL**: https://ideas.repec.org/a/aea/aecrev/v83y1993i5p1370-76.html
- **핵심**: Art price index 와 stock market 비교
- **활용**: Art market 의 본질적 noise 수준 reference

#### Schönfeld & Reinstaller (2007) "The Effects of Gallery and Artist Reputation on Prices in the Primary Market for Art"
- **Journal**: Journal of Cultural Economics 31(2)
- **URL**: https://ideas.repec.org/a/kap/jculte/v31y2007i2p143-153.html
- **왜 핵심**: **1차 시장 reputation effect** 특화
- **핵심 발견**:
  - Gallery reputation (membership, exhibition history) 양 effect
  - Artist reputation (review count, exhibitions) 강 effect
  - Reputation × experience interaction
- **활용**: Gallery_tier / artist_followers 변수 정당화

## 2. Reading priority (Week 1 발췌)

| Order | Paper | 발췌 시간 | Focus |
|---|---|---|---|
| 1 | Rengers & Velthuis (2002) | 2-3h | 1차 시장 hedonic spec 그대로 참조 |
| 2 | Renneboog & Spaenjers (2013) | 2-3h | Methodology + 변수 list |
| 3 | Rosen (1974) | 1-2h | Theoretical foundation 인용 |
| 4 | Galenson (2003) | 1h | Career stage non-linear |
| 5 | Schönfeld & Reinstaller (2007) | 1h | Gallery / artist reputation effect |

총 7-10시간 → Week 1 시간 budget 내 (약 20시간 가용 가정).

### 발췌 시 추출할 정보
1. **Variables list**: 각 paper 가 사용한 RHS variables (그대로 / 비슷)
2. **Coefficient signs**: 우리 결과와 비교할 expected sign
3. **Methodology**: OLS / FE / quantile / IV 등
4. **Sample size**: 우리 28K 와 비교
5. **Reported metrics**: R² / RMSE / MAPE — 우리 evaluation 비교
6. **인용할 quote**: 본 트랙 report 에 인용할 1-2 줄

## 3. Beyond Tier 1-4 — 추가 가능 references

### Korean art market (있으면 추가)
- 한국 미술 시장 hedonic 연구 (KCI / RISS 검색 — Week 1 작업)
- 한국 갤러리 vs 해외 갤러리 가격 차이
- Galenson 의 한국 작가 적용 (있다면)

### Methodological extensions
- Frey & Pommerehne (1989) "Muses and Markets" — 미술품 경제학 책
- Pesando (1993) — Modern prints market hedonic
- Velthuis (2005) "Talking Prices" — Gallery pricing strategy 정성 분석

### Causal inference
- Card & Krueger 변형 — within-comparison
- Cunningham (2021) "Causal Inference: The Mixtape" — 한국어 번역 있음
- Pearl (2009) "Causality" — DAG + identification

## 4. 문헌 매트릭스 (작성 후 채울 표)

| Paper | Year | Sample | Method | Key vars | Reported R² | Sign of size | Sign of medium oil |
|---|---|---|---|---|---|---|---|
| Rosen (1974) | — | theoretical | — | — | — | — | — |
| Rengers & Velthuis | 2002 | TBD | TBD | TBD | TBD | TBD | TBD |
| Renneboog & Spaenjers | 2013 | TBD | TBD | TBD | TBD | TBD | TBD |
| Galenson | 2003 | TBD | TBD | TBD | TBD | TBD | TBD |
| Schönfeld & Reinstaller | 2007 | TBD | TBD | TBD | TBD | TBD | TBD |

(Week 1 발췌 후 채움)

## 5. 본 트랙의 학술적 contribution (잠정)

### 가능한 contribution
1. **Korean primary art market hedonic** — Rengers & Velthuis (Dutch) 의 한국 시장 적용
2. **Cold-start (new artist) 가격 예측** — Galenson 의 career stage 통합
3. **ML vs Hedonic 비교** — V3 (GBM) vs Mixed-effects 의 cold-start 성능 비교
4. **Mixed-effects with high-cardinality artists** (1,240 artists) — random effect identifiability

### 학술 publishability (장기)
- 4주 deliverable 자체는 internal report 수준
- 후속 작업 시 KCI / 한국 미술경제학회 / 국제 conference 가능성 있음
- Renneboog & Spaenjers 형식 paper 으로 evolve 가능

## 6. Week 1 발췌 작업 protocol

### Per paper checklist
- [ ] PDF 다운로드 (또는 SSRN/journal link 확보)
- [ ] Abstract + intro + methodology section 정독
- [ ] Variables list 추출 → `02_literature_review_variables.csv` (Week 1 산출)
- [ ] Reported coefficient signs 메모
- [ ] 본 트랙 report 인용할 1-2 quote 추출
- [ ] Methodology 비교 표 (위 §4) 한 row 추가

### Week 1 종료 시 산출물
- 5편 paper 발췌 메모 (각 1-2 페이지)
- 변수 매트릭스 (CSV)
- 본 README.md 의 §1 references list 가 완성됨

## 7. References 활용 protocol (Week 2-4)

### Week 2 OLS 결과 보고 시
- coefficient sign / magnitude 비교: "우리 size β_log_area = 0.45 vs Rengers & Velthuis 0.32" 
- 차이 발견 시 그 이유 검토 (sample 차이 / market 차이)

### Week 3 Mixed-effects 결과 보고 시
- Random effect variance: "artist ICC = 0.45 vs Schönfeld & Reinstaller 0.38"
- Within-artist effect 비교

### Week 4 최종 report 작성 시
- Reference matrix (위 §4) 완성
- 각 finding 의 학술 근거 명시
- 한계 / future work 섹션에서 명시
