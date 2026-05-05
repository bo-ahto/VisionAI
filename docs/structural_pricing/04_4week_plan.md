# 04. 4주 Plan — Week 별 Deliverable

> **상태**: DRAFT (코덱스 12차 자문 결과 + Hedonic mixed-effects 우선순위)
> **목적**: 1개월 내 의미 있는 deliverable 산출 protocol
> **시간 예산**: ~80-100시간 (일 2-3시간 가정, 4주)

## Week 1 — 문헌 + DAG + 데이터 spec (20-25h)

### Goal
- 5편 핵심 paper 발췌 완료
- DAG visual 산출
- Hedonic formula spec 확정
- Data prep code skeleton

### Day-by-day

#### Day 1-2 (5-6h): Top 2 paper 발췌
- Rengers & Velthuis (2002) — 1차 시장 hedonic 직접 reference
- Renneboog & Spaenjers (2013) — Methodology + 변수
- 산출: 발췌 메모 (각 1-2 페이지)

#### Day 3 (3-4h): Tier 2-4 paper 발췌
- Rosen (1974), Galenson (2003), Schönfeld & Reinstaller (2007)
- 산출: 발췌 메모 + variables matrix (`02_literature_review.md` §4 채움)

#### Day 4 (3-4h): DAG 작성
- `03_causal_dag.md` 의 DAG 를 graphviz 또는 dagitty 으로 visual
- 식별 가능성 등급표 (§3) 작성
- 산출: `experiments/structural_v1/results/figures/causal_dag.png`

#### Day 5 (3-4h): Data spec 확정
- `05_data_requirements.md` 의 변수 list 확정
- Categorical 처리 / log transform / centering 결정
- Reference category 결정
- 산출: variable spec table

#### Day 6-7 (4-6h): Data prep code
- `experiments/structural_v1/data_prep.py` 작성
- V5 eval framework 재사용 (LAO split + 3 seeds)
- 산출: clean dataset (`X`, `y`, train/test split per seed)

### Week 1 Deliverable
- [ ] `02_literature_review.md` 5편 발췌 + variables matrix
- [ ] `03_causal_dag.md` DAG visual
- [ ] `experiments/structural_v1/data_prep.py` (실행 가능)
- [ ] `experiments/structural_v1/results/data_summary.json` (descriptive stats)

### Week 1 Stop conditions
- 5편 paper 의 variables matrix 추출 못 하면 → Week 2 시작 보류
- DAG 의 식별 등급표 작성 못 하면 → Week 2 OLS 시작 보류

---

## Week 2 — Hedonic OLS Baseline (20-25h)

### Goal
- Level 1 OLS hedonic regression 완료
- Coefficient table v1
- Cold/warm 분리 평가
- V3 와 동일 LAO holdout 비교

### Day-by-day

#### Day 8 (3-4h): OLS skeleton
- `experiments/structural_v1/hedonic_baseline.py` 작성
- statsmodels OLS + heteroskedasticity-robust SE (HC1)
- Cluster-robust SE (cluster on artist_slug)
- 산출: 첫 model run (전체 데이터, no split)

#### Day 9 (3-4h): Variable selection
- 15-25 변수 spec 확인 (Day 5 spec 이용)
- Multicollinearity check (VIF)
- Outlier detection (Cook's distance)
- 산출: clean OLS run + diagnostic

#### Day 10 (3-4h): LAO holdout 평가
- V5 eval framework 재사용 → 3 seeds artist-level holdout
- Train fit → test predict
- MdAPE / W30 / W50 per seed + mean ± std
- 산출: `experiments/structural_v1/results/metrics/ols_holdout.json`

#### Day 11 (3-4h): Cold/warm 분리 + Tier segment
- Test set 의 cold-start (0-shot) 와 warm 분리
- Tier B/C/D/E segment 별 MdAPE
- 산출: cold/warm/tier-segment metric 표

#### Day 12 (3-4h): V3 비교
- 동일 LAO holdout 으로 V3 production model run (cached predictions)
- OLS hedonic vs V3 MdAPE 비교 표
- 산출: `experiments/structural_v1/results/tables/v3_comparison.csv`

#### Day 13-14 (4-6h): Coefficient table + diagnostic
- Coefficient table format (paper-style)
- Residual plot (QQ, scale-location, leverage)
- Partial dependence plot per variable
- 산출:
  - `experiments/structural_v1/results/tables/ols_coefficients.csv`
  - `experiments/structural_v1/results/figures/residual_diagnostic.png`

### Week 2 Deliverable
- [ ] OLS hedonic regression (15-25 변수)
- [ ] Coefficient table (β + SE + p-value)
- [ ] Holdout MdAPE per 3 seeds
- [ ] Cold/warm/tier segment 비교 표
- [ ] V3 comparison 표
- [ ] Diagnostic plots

### Week 2 Pass criteria
- OLS holdout MdAPE 가 naive median 보다 명백히 좋음 (< 70 정도)
- Major coefficient signs 가 literature 와 일치 (size + ; medium oil + 등)
- Multicollinearity 통제됨 (VIF < 10)

### Week 2 Stop conditions
- OLS 실행 시 numerical instability → 변수 spec 재검토
- Cluster SE 계산 실패 → 단순 OLS SE 로 진행 + caveat 명시

---

## Week 3 — Mixed-Effects (20-25h)

### Goal
- Level 2 mixed-effects (artist + gallery RE)
- Variance decomposition (artist / gallery / residual)
- Within-artist effect 식별
- Hausman test (RE vs FE)
- V3 / V5 cycle 동일 LAO 비교

### Day-by-day

#### Day 15 (3-4h): Mixed-effects skeleton
- `experiments/structural_v1/mixed_effects.py` 작성
- statsmodels MixedLM 또는 pymer4 (R lme4 wrapper)
- artist random intercept first
- 산출: ME 첫 run

#### Day 16 (3-4h): Gallery RE 추가
- artist + gallery 두 RE
- ICC 계산 (artist / gallery / residual variance)
- 산출: variance decomposition table

#### Day 17 (3-4h): Within-artist FE 비교
- Fixed effect (within-artist) 모델
- Hausman test (RE vs FE)
- 산출: identification 강도 검증 결과

#### Day 18 (3-4h): Random slope 검토
- log(area) random slope by artist
- Likelihood ratio test (random slope 필요?)
- 산출: model selection memo

#### Day 19 (3-4h): LAO holdout + V3/V5 비교
- 동일 protocol 로 ME holdout MdAPE
- OLS / ME / V3 / V5 (가능 시) 비교 표
- 산출: holdout metric per condition

#### Day 20-21 (4-6h): Coefficient + variance + report
- ME coefficient table (β + RE variance)
- Variance decomposition figure (stacked bar)
- Within-artist effect 표
- 산출:
  - `experiments/structural_v1/results/tables/me_coefficients.csv`
  - `experiments/structural_v1/results/tables/variance_decomp.csv`
  - `experiments/structural_v1/results/figures/variance_pie.png`

### Week 3 Deliverable
- [ ] Mixed-effects model (artist + gallery RE)
- [ ] Variance decomposition (ICC)
- [ ] Within-artist FE 비교 + Hausman test
- [ ] Holdout MdAPE 비교 (OLS / ME / V3 / V5)
- [ ] Coefficient table + variance figure

### Week 3 Pass criteria
- ME holdout MdAPE ≤ OLS holdout (RE shrinkage 효과 있음)
- ICC > 0.20 (artist effect 의미 있음)
- Within-artist FE 결과와 RE 결과 비슷 (CIA 약 충족 신호)

---

## Week 4 — Quantile Regression + 최종 Report (20-25h)

### Goal
- Level 4 quantile regression (τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9})
- Causal interpretation memo
- 최종 report 작성

### Day-by-day

#### Day 22 (3-4h): Quantile regression
- `experiments/structural_v1/quantile_regression.py` 작성
- statsmodels QuantReg per τ
- 산출: τ × variable coefficient grid

#### Day 23 (3-4h): Quantile heatmap + interpretation
- Heatmap: 변수 × τ
- 분포 형태 변화 효과 (heavy-tail 변수 식별)
- 산출: `experiments/structural_v1/results/figures/quantile_heatmap.png`

#### Day 24 (3-4h): Causal interpretation memo
- `06_evaluation_framework.md` 의 식별 등급표 (실제 결과 채움)
- "What we identify" vs "What we don't" 명시
- Within-artist 결과와 cross-section 결과 비교
- 산출: causal memo (markdown 1-2 페이지)

#### Day 25-26 (6-8h): 최종 report 작성
- Paper-style structure:
  1. Abstract / Introduction
  2. Data
  3. Methodology (OLS / ME / Quantile)
  4. Results (coefficient / variance / quantile)
  5. Causal framing
  6. Comparison with V3 / V5
  7. Limitations + Future work
- 산출: `docs/structural_pricing/final_report.md` (10-15 페이지)

#### Day 27-28 (4-6h): Stretch (Bayesian prototype)
- 시간 남으면 PyMC NUTS 1 model run
- Posterior interval example
- 산출: `experiments/structural_v1/bayesian_proto.py` + interval figure

### Week 4 Deliverable
- [ ] Quantile regression τ × variable grid
- [ ] Quantile heatmap
- [ ] Causal interpretation memo
- [ ] 최종 paper-style report (10-15 페이지)
- [ ] (Stretch) Bayesian prototype + posterior interval

### Week 4 Pass criteria
- Final report 가 학술 paper 형식에 가깝고 인용 가능 수준
- Coefficient signs 가 literature 와 대체로 일치
- V3 비교에서 "structural baseline 으로 가치 있음" 증명

---

## Stretch Goals (시간 여유 시)

### Bayesian hierarchical (Day 27-28)
- PyMC NUTS 또는 NumPyro
- artist + gallery + medium random effects
- Posterior credible interval
- Convergence diagnostic (R-hat)

### Within-artist within-medium robustness (Week 4 추가)
- 작가 + medium FE
- 더 엄격한 식별
- Coefficient stability check

### Korean art market 한정 분석
- 한국 작가 (artist_country == "KR") subsample
- Korean buyer 시장 특성 검토

---

## 실패 / 보류 시 fallback

### Week 2 OLS 실패 (변수 spec 문제)
- → Week 3 직접 ME 시작 (OLS skip)
- 단 coefficient table 단순화

### Week 3 ME convergence 실패
- → statsmodels MixedLM 대신 pymer4 (R lme4)
- 또는 GPBoost (V5 cycle 의 C-lite 기반)

### Week 4 시간 부족
- Quantile regression skip → OLS / ME 만 final
- Bayesian stretch 폐기

---

## 주별 시간 분배 (~80-100h total)

| Week | 작업 | 시간 |
|---|---|---|
| 1 | 문헌 + DAG + 데이터 spec | 20-25h |
| 2 | OLS hedonic baseline | 20-25h |
| 3 | Mixed-effects | 20-25h |
| 4 | Quantile + 최종 report | 20-25h |
| **Total** | | **80-100h** |

---

## 검증 protocol (V5 cycle 표준 적용)

### LAO holdout (V5 와 공유)
- Artist-level GroupShuffleSplit 80/20
- Repeated 3 seeds: 42, 123, 7777
- Hard gate: artist_slug overlap=0
- 평가: `src/visionai/price_engine/_v5_eval_framework.py` 재사용

### Metric 보고 의무
- Primary: holdout MdAPE
- Secondary: W30 / W50 / MAE
- Segment: cold/warm × Artsy/Saatchi × Tier
- Comparison: Naive / OLS / ME / V3 / V5 (가능 시)

### 학술 형식 보고 의무
- Coefficient table (β + SE + p)
- Residual diagnostic (QQ + scale-location + leverage)
- Variance decomposition (ICC)
- 식별 등급표 (causal vs descriptive)

---

## 종료 시점 self-evaluation

Week 4 종료 시 다음 self-evaluation:

1. **학술 baseline 확립** ✅ / ❌
   - OLS / ME / Quantile coefficient 표 완성
   - V3 와 비교 가능 metric

2. **Cold-start regime baseline** ✅ / ❌
   - Cold-start MdAPE 측정 (V3 와 비교)
   - Within-artist 식별 결과

3. **이론적 방어 가능 문서** ✅ / ❌
   - 5+ paper reference 명시
   - 식별 가능성 등급표
   - 한계 명시

≥ 2/3 ✅ → 트랙 가치 입증, 후속 cycle 가능
< 2/3 → 트랙 보류 또는 재설계
