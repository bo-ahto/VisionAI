# 01. Approach Design — Hedonic Mixed-Effects Regression

> **상태**: DRAFT (코덱스 12차 자문 결과 정리)
> **목적**: 본 트랙의 핵심 접근법 정의 + 수학 정당화 + 모델 spec

## 1. 왜 Hedonic Regression?

### 이론적 근거 (Rosen 1974)
**Hedonic price theory**: 차별화된 상품 (heterogeneous good) 의 가격이 그 상품의 attribute 의 implicit price 의 합으로 표현 가능.

```
P(z) = f(z_1, z_2, ..., z_K)
```

각 attribute `z_k` 에 대해 implicit marginal price `∂P/∂z_k` (즉 elasticity).

미술품: `z = (size, medium, support, year_made, artist_attributes, gallery_attributes, ...)`

### 실증 적용 (Renneboog & Spaenjers 2013, JFE)
log-linear hedonic regression 표준 form:
```
log P_i = α + Σ_k β_k · z_{i,k} + ε_i
```

여기서 `β_k` = attribute `z_k` 의 1 unit 증가 시 가격 % 변화.

### 1차 시장 (gallery primary market) 특화 (Rengers & Velthuis 2002)
Rengers & Velthuis 의 Dutch contemporary gallery price 분석 — 본 트랙의 가장 직접적 reference. 핵심 finding:
- Size effect 강 (양 elasticity)
- Medium 효과 중 (oil > acrylic > paper)
- Artist age, gallery reputation 강 effect
- Career stage non-linear (Galenson 2003)

## 2. 우리 모델 (수학 정의)

### Level 1: OLS hedonic (baseline)
```
log P_i = α + β'X_i + ε_i,    ε_i ~ N(0, σ²)
```

`X_i` 변수 (15-25개 후보):
- **Size**: log(area_cm2), aspect_ratio, is_small (binary)
- **Medium**: medium_category dummies (oil/acrylic/paper/sculpture/ink/...), support_factor
- **Time**: year_made (centered), work_age, is_recent (binary, 5y)
- **Artist**: log(followers), career_stage dummies, age_at_creation, has_birth_year
- **Gallery**: gallery_tier dummies, gallery_city_count, has_seoul, has_international, gallery_type
- **Source**: source dummy (Artsy/Saatchi)
- **Currency**: is_krw

### Level 2: Mixed-effects hedonic (1순위 권고)
```
log P_{ij} = α + β'X_{ij} + u_{a(i)} + v_{g(j)} + ε_{ij}
```

- `u_{a(i)} ~ N(0, τ²_artist)`: artist random intercept (작가 i 의 latent quality)
- `v_{g(j)} ~ N(0, τ²_gallery)`: gallery random intercept
- `ε_{ij} ~ N(0, σ²)`: residual

**해석**:
- `β`: structural attribute 의 partial elasticity (within-group)
- `τ²_artist`: 작가 간 가격 분산 (latent quality variation)
- `τ²_gallery`: 갤러리 간 가격 분산
- ICC = `τ²_artist / (τ²_artist + τ²_gallery + σ²)`: 가격 분산 중 작가가 설명하는 비율

**Cold-start 자연 처리**: 새 작가 `a*`: `u_{a*} = 0` (population mean shrinkage). Test 시 `predict(log P_{i*j}) = α + β'X_{i*j} + v_{g(j)}`

### Level 3: Mixed-effects + random slope (선택)
```
log P_{ij} = α + β'X_{ij} + u_{a(i)} + (γ_a · log(area_{ij})) + v_{g(j)} + ε_{ij}
```

작가별 size elasticity 다른지 검증. Likelihood ratio test 로 random slope 필요 여부.

### Level 4: Quantile regression (보조)
```
Q_τ(log P_i | X_i) = α_τ + β'_τ · X_i
```

τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9} grid.

각 τ 에서 coefficient 추정 → 분포 전체에서 attribute 효과 비교.

**Use case**: heavy-tail 분포 (₩300K ~ ₩3B) 에서 mean (β_OLS) vs median (β_τ=0.5) 차이 확인.

### Level 5: Bayesian hierarchical (stretch, Week 4)
```
log P_{ij} ~ N(μ_{ij}, σ²)
μ_{ij} = α + β'X_{ij} + u_{a(i)} + v_{g(j)}

α ~ N(0, 10)
β_k ~ N(0, 1) for each k
u_a ~ N(0, τ_a),  τ_a ~ HalfNormal(1)
v_g ~ N(0, τ_g),  τ_g ~ HalfNormal(1)
σ ~ HalfNormal(1)
```

PyMC NUTS 또는 NumPyro. Posterior interval 제공 (uncertainty quantification).

## 3. 변수 design 원칙 (코덱스 권고)

### Categorical 처리
- **Dummies**: medium_category (~7 levels), career_stage (~4 levels), gallery_tier (5 levels)
- **Reference category**: oil (medium), unknown (career_stage), Tier_E (gallery_tier)
- **Avoid**: high cardinality categorical (gallery_name 1,124 levels) → random effect 으로

### Continuous 처리
- **Log transform**: area_cm2, followers (right-skewed, positivity)
- **Centering**: year_made, age (interpretation 용이)
- **Standardization**: 모든 continuous predictor (β 비교 가능)

### Interaction (선택)
- Size × medium: oil 대형 vs paper 소형 가격 형성 다를 수 있음
- Size × career_stage
- Within-artist 모델에서 추가 검토

## 4. 식별 가능한 효과 vs 단순 상관

### Within-artist 식별 가능 (코덱스 권고)
- 같은 작가의 다른 작품 비교 시 → artist FE 통제 후
- **Size, year_made, support, medium** 의 상대 effect 식별 가능 (작가 talent 통제 후)

### Within-artist within-medium robustness
- 같은 작가의 같은 medium 작품 비교 → 작가 + medium 둘 다 통제
- Size, year, support 의 더 강한 식별

### 식별 어려움 (의도적 약한 주장)
- **Gallery effect**: selection bias (better artists in better galleries) → IV 없으면 weak claim
- **Reputation (followers)**: reverse causality (high price → reputation)
- **Medium choice**: artist 의 latent style preference 와 confound

→ **본 트랙은 within-artist design 까지 식별 + 그 외는 descriptive/associational 로 명시**

## 5. 추정 / inference

### 추정 방법
- OLS (Level 1): scikit-learn `LinearRegression` + sandwich SE
- Mixed-effects (Level 2-3): `statsmodels.MixedLM` 또는 `lme4` via `pymer4`
- Quantile (Level 4): `statsmodels.QuantReg`
- Bayesian (Level 5): `pymc` NUTS

### Inference (불확실성)
- OLS: heteroskedasticity-robust SE (HC1)
- Cluster-robust SE (cluster on artist_slug)
- Mixed-effects: profile likelihood CI
- Bayesian: posterior credible interval

## 6. 평가 protocol (V5 와 동일)

### Split (Hold-out)
- Artist-level GroupShuffleSplit 80/20
- Repeated 3 seeds (42, 123, 7777)
- LAO hard gate: artist_slug overlap=0

### Metrics
- **Primary**: cold-start MdAPE
- **Secondary**: overall MdAPE, W30, W50, MAE
- **Diagnostic**: residual plots, QQ-plot, partial dependence

### 비교 대상
| Model | 학습 데이터 | 비교 의미 |
|---|---|---|
| Naive (median) | train | reference floor |
| OLS hedonic | train | structural baseline |
| Mixed-effects | train | + RE shrinkage |
| V3 production | full | production benchmark |

### Segment 보고
- Tier × Source × Career stage (V5 의 48-cell 일부 재사용)
- Cold (0-shot) vs Warm artist 분리

## 7. 한계 명시 (writeup 시)

### 본 모델의 explicit limitation
- Artist FE 가 `artist_latent_quality` 흡수 — Skew 작가군에 weak generalization
- Heavy-tail 가격 분포 → log-linear 가정 위반 가능 (잔차 진단 필수)
- Cross-section data — 시점 변동 (가격 트렌드, 작가 명성 변화) 명시적 모델링 X
- Within-artist 1-2건 작가는 RE shrinkage 강 → cold-start 개선 효과 약함

### Out-of-scope (의도적)
- 강한 causal claim (IV)
- 운영 도입 (V3 와 별도 트랙)
- Real-time inference 최적화

## 8. 산출물 (Week 4 종료 시)

### 학술 형식 outputs
1. **Coefficient table** (paper Table format) — Level 1 OLS / Level 2 ME 비교
2. **Elasticity summary** — 변수별 1σ 변화 시 가격 % 변화
3. **Within-artist effect** — 작가 통제 후 size/year/medium effect
4. **Variance decomposition** — artist vs gallery vs residual 분산
5. **Cold-start comparison table** — Naive / OLS / ME / V3 / V5 holdout MdAPE
6. **Residual diagnostic** — QQ-plot, scale-location, leverage
7. **Quantile coefficient grid** — τ × variable heatmap

### Causal interpretation memo
- DAG (`03_causal_dag.md`)
- 식별 가능한 효과 등급표
- 식별 어려움 변수의 명시적 caveat

### 최종 report
- "What this model explains" — coefficient + elasticity + RE
- "What it cannot identify" — gallery causal effect, reputation causal effect
- "When to use this model" — interpretable baseline, sensitivity check, V3 의 SHAP-like 보완

## 9. 코드 구조 (experiments/structural_v1/)

### 파일 분담
```
experiments/structural_v1/
├── data_prep.py          # Artsy/Saatchi 로드 + feature engineering
├── hedonic_baseline.py   # Level 1 OLS
├── mixed_effects.py      # Level 2-3 (artist + gallery RE)
├── quantile_regression.py # Level 4
├── bayesian_proto.py     # Level 5 (stretch)
├── evaluation.py         # V5 eval framework re-use
└── reporting.py          # Coefficient table + figures
```

### 의존성
- statsmodels (OLS, MixedLM, QuantReg)
- pymer4 (R lme4 wrapper, optional)
- pymc + arviz (Bayesian, optional)
- 기존 `src/visionai/price_engine/_v5_eval_framework.py` 재사용

## 10. 다음 단계

본 design 의 implementation 은 4주 plan (`04_4week_plan.md`) 에 따라 진행.
- Week 1: spec 확정 (본 문서) + 문헌 발췌
- Week 2: Level 1 OLS
- Week 3: Level 2-3 ME
- Week 4: Level 4 Quantile + 최종 report

DAG / 인과 framing: `03_causal_dag.md`
데이터 spec: `05_data_requirements.md`
평가 framework: `06_evaluation_framework.md`
