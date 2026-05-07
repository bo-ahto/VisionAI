# Structural Pricing Track — 1차 시장 가격 예측 모델 (논문 형식)

> **상태**: 신규 트랙 (DRAFT, 2026-05-05)
> **위치**: 별도 트랙 — 운영 V3/V5 cycle 영향 X
> **기간**: 4주 plan (의미 있는 deliverable 목표)
> **기원**: 코덱스 12차 자문 — 사용자 요청 "논문 처럼 공식과 인과관계를 상세하게"

## 1. 목적

Primary-market 작품 가격 예측에 대해 **interpretable econometric model + explicit causal assumptions** 기반 baseline 구축. ML black-box (V3 운영 모델) 의 보완재.

### Goal
- 변수별 elasticity / 가격 영향 메커니즘 명시
- 작가/갤러리 fixed effect / random effect
- DAG 기반 식별 가능 효과 vs 단순 상관관계 분리
- 학술 reference 기반 정당화

### Non-goal
- V3 운영 모델 대체 ❌
- 1개월 내 production deployment ❌
- 강한 causal claim (IV-grade identification) ❌
- 단독 운영 가격 결정기 ❌

## 2. 핵심 모델 (코덱스 12차 권고)

### 우선순위
1. **Hedonic mixed-effects regression** — 1순위
2. **Quantile regression** — 보조 (분포 전체)
3. **Bayesian hierarchical** — 2단계 stretch

### Main equation
```
log P_i = α + β'X_i + u_artist(i) + v_gallery(i) + ε_i
```
- `β`: hedonic coefficients (size, medium, support, year, ...)
- `u_artist`: artist random intercept (partial pooling)
- `v_gallery`: gallery random intercept
- `ε_i`: residual

### 비교 baseline
- Naive (median price)
- OLS without random effects
- V3 production (`integrated_v3_filtered_tuned`) — same LAO holdout

## 3. 인과 framing (코덱스 권고)

### DAG (간략)
```
artist_latent_quality ──┐
                        ├──> gallery_tier ───┐
                        ├──> followers ──────┤
                        ├──> medium choice ──┤
                        └──> price ◄─────────┘
gallery_tier ──> buyer pool / certification ──> price
medium ──> production cost / demand ──> price
```

### 식별 가능한 effect (within-artist)
- Within-artist within-medium: artist talent 통제 후 size/year/material effect
- Within-artist 다 갤러리: gallery effect 약한 식별
- IV: 데이터 한계로 **non-credible** (시도 X)

상세: `03_causal_dag.md`

## 4. 데이터 / 평가

### 데이터
- Artsy 7,289 + Saatchi 21,087 (V4 cycle 기준, V5 마이그레이션 후 갱신)
- Same `primary_market_dataset.parquet` + `saatchi_cleaned.parquet`

### 평가 (V5 cycle 과 공유)
- Artist-level holdout 80/20 (LAO)
- Repeated 3 seeds (42, 123, 7777)
- Metrics: MdAPE / W30 / W50 / segment-wise

### 비교 표 (예시)
| Model | Artsy holdout MdAPE | Cold-start | Warm | Note |
|---|---|---|---|---|
| Naive | 76 | — | — | reference |
| OLS hedonic | TBD | TBD | TBD | baseline |
| Mixed-effects | TBD | TBD | TBD | + RE |
| V3 (production) | 27.80 | — | — | comparison |
| V5 candidate | TBD | TBD | TBD | 진행 중 |

## 5. 4주 Deliverable (Week 별)

### Week 1 — 문헌 + DAG + 데이터 spec
- 5편 핵심 reference 발췌 (`02_literature_review.md`)
- DAG 초안 (`03_causal_dag.md`)
- Hedonic formula spec 확정 (`05_data_requirements.md`)

### Week 2 — Hedonic OLS baseline
- Robust OLS + log-area + medium + support + source + career_stage
- Coefficient table v1
- Cold/warm 분리 평가

### Week 3 — Mixed-effects 추가
- Artist random intercept
- Gallery random intercept
- Random slope 필요 여부 점검
- V3/V5 holdout 동일 protocol 비교

### Week 4 — Quantile regression + 최종 report
- Quantile τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9}
- Causal interpretation memo
- 최종 report: "what this model explains / what it cannot identify"

상세 plan: `04_4week_plan.md`

### Stretch (시간 남으면)
- Bayesian prototype (PyMC NUTS)
- Posterior interval example

## 6. 폴더 구조

### 본 트랙 (분리)
```
docs/structural_pricing/        ← 본 폴더 (이론/문헌/의사결정)
├── README.md (본 문서)
├── 01_approach_design.md
├── 02_literature_review.md
├── 03_causal_dag.md
├── 04_4week_plan.md
├── 05_data_requirements.md
└── 06_evaluation_framework.md

experiments/structural_v1/      ← 실행 코드/산출물
├── README.md
├── data_prep.py
├── hedonic_baseline.py
├── mixed_effects.py
├── quantile_regression.py
├── bayesian_proto.py (stretch)
├── notebooks/
└── results/
    ├── tables/      (coefficient tables, elasticity)
    ├── figures/     (residual plots, partial dependence)
    └── metrics/     (MdAPE/W30 per condition)
```

### V3/V5 와의 관계 (코덱스 권고: Comparative + Independent)
- 데이터 공유 ✓
- 평가 framework 공유 ✓ (`src/visionai/price_engine/_v5_eval_framework.py`)
- 개발 코드 분리 ✓
- 운영 inference path 비연결 ✓

## 7. 성공 기준 (4주 후)

### Minimum viable deliverable (반드시 달성)
- [ ] OLS hedonic baseline + coefficient table (15-25 변수)
- [ ] Mixed-effects (artist + gallery RE) baseline
- [ ] Cold-start vs warm 분리 metric
- [ ] V3 와 동일 LAO holdout 비교
- [ ] DAG + identification 가능성 등급표

### Stretch goal
- [ ] Quantile regression τ grid
- [ ] Bayesian prototype (PyMC)
- [ ] Posterior interval example
- [ ] Within-artist within-medium robustness check

### 의미 있는 성과 (사용자 정의)
- "**해석 가능한 baseline 확립**" — V3 black-box 의 보완재 역할
- "**cold-start regime 에서 V3/V5 와 비교 가능한 구조적 baseline**"
- "**이론적으로 방어 가능한 문서화**" — 학술 논문 형식 가까운 보고

## 8. 운영 / V3/V5 와의 관계 정리

| 차원 | 본 트랙 | V3 운영 | V5 cycle |
|---|---|---|---|
| 목적 | 해석 + 학술 baseline | production | cold-start 개선 |
| 모델 | Hedonic mixed-effects | GBM ensemble | GBM + retrieval |
| 인과 | DAG + within-artist | black-box | structured retrieval |
| 평가 | LAO 80/20 | KFold + LAO | LAO 80/20 ×3 seeds |
| 도입 | 도입 의도 X | 운영 중 | 4-7주 검증 후 |
| 통합 시점 | 미정 (성숙 시 SHAP-like) | 현재 | TBD |

## 9. References (코덱스 12차 자문 추천)

핵심 5+ 논문, 자세한 발췌는 `02_literature_review.md` 참조:

| # | Paper | URL | 핵심 |
|---|---|---|---|
| 1 | Rosen (1974) "Hedonic Prices and Implicit Markets" | [JPE](https://ideas.repec.org/a/ucp/jpolec/v82y1974i1p34-55.html) | Hedonic regression theoretical foundation |
| 2 | Renneboog & Spaenjers (2013) "Buying Beauty: On Prices and Returns in the Art Market" | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1352363) | Art market hedonic, JFE published |
| 3 | Galenson (2003) "The Life Cycles of Modern Artists" | [NBER](https://www.nber.org/papers/w9539) | Age-creativity, career stage 변수 정당화 |
| 4 | Koenker & Hallock (2001) "Quantile Regression" | [JEP](https://www.aeaweb.org/articles?id=10.1257/jep.15.4.143) | Quantile regression core reference |
| 5 | Beggs & Graddy (2009) "Anchoring Effects: Evidence from Art Auctions" | [AER](https://www.aeaweb.org/articles?id=10.1257/aer.99.3.1027) | Auction price reference (1차 시장 비교용) |
| 6 | Mei & Moses (2002) "Art as an Investment" | [NYU archive](https://archive.nyu.edu/handle/2451/26539) | Repeated sales index |
| 7 | Schönfeld & Reinstaller (2007) "Modern Art Auctions" | [JCE](https://ideas.repec.org/a/kap/jculte/v31y2007i2p143-153.html) | Cultural goods hedonic |
| 8 | Goetzmann (1993) "Accounting for Taste: Art and the Financial Markets" | [AER](https://ideas.repec.org/a/aea/aecrev/v83y1993i5p1370-76.html) | Art market price index |
| 9 | Rengers & Velthuis (2002) "Determinants of Prices for Contemporary Art in Dutch Galleries" | [JCE](https://ideas.repec.org/a/kap/jculte/v26y2002i1p1-28.html) | **1차 시장 (gallery) 특화** ⭐ |

⭐ Rengers & Velthuis (2002) 가 본 트랙의 가장 직접적인 reference (Dutch gallery primary market hedonic).

## 10. 다음 액션

1. Week 1 시작 시 `02_literature_review.md` 의 5편 paper 발췌 읽기
2. `03_causal_dag.md` 의 DAG draft → 작가/갤러리/medium 변수 mapping
3. `experiments/structural_v1/data_prep.py` skeleton 작성 (V5 eval framework 재사용)
4. `04_4week_plan.md` 의 Week 1 deliverable 산출

## 11. 코덱스 자문 12차 참조

본 트랙 plan 의 모든 권고는 코덱스 자문 12차 (2026-05-05) 결과:
- Q1: Hedonic mixed-effects 1순위
- Q2: 9편 논문 (위 §9)
- Q3: A+ deliverable realistic (1개월)
- Q4: Within-artist design 권고 (IV non-credible)
- Q5: 폴더 구조 (옵션 A/B 혼합)
- Q6: Comparative + Independent (V3/V5 와)
