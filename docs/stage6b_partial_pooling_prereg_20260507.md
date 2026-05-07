# Stage 6B — Partial Pooling Confirmatory Pre-registration

> **작성일**: 2026-05-07 (freeze, 코덱스 사전 자문 반영)
> **위치**: 새 Phase 2' (Stage 5 미개시 종료 + Stage 6A FAIL 후 architecture cycle) 의 **6B 1순위**
> **연계**: `docs/stage6_prereg_draft_20260507.md` v2 (전체 cycle) / `docs/stage6a_results_20260507.md` (6A FAIL — input) / `docs/stage4_short_term_track_results_20260507.md` (feature 부족 가설)

> ⚠️ **연구 목적 (코덱스 framing)**: **Fixed-feature regime 에서 partial pooling 이 6A 의 sample fragmentation harm 을 완화할 수 있는지 평가** — 즉, Mechanism-targeted follow-up study (사후 성능 최대화 X).

> **HARK Disclosure (코덱스 의무, v2 정정)**:
> - 본 6B 가설 = 6A 결과 (FAIL) 관찰 후 형성 — **registered follow-up within program** (program-level independent confirmation 아님)
> - 새 탐색 / 새 모델 family X — Stage 3 ME 구현 재활용 (`is_low_price` fixed effect 는 코덱스 P1 검수에서 타깃 누수 발견되어 **삭제**)
> - 추가 segmentation / 추가 feature / router 변경 / artist-segment interaction = **prereg 명시 배제**
> - primary threshold = 6A 와 동일 (변경 X)

> **본 prereg 의 freeze**: 가설 / metric / Holm family / PASS 기준 / Implementation fallback rule = **2026-05-07 freeze**. 결과 본 후 변경 X.

## 1. 6A FAIL Input

### 1.1 6A 결과 (sample fragmentation 정량)
| Pool | Train n | Sample efficiency |
|---|---|---|
| Baseline (전체) | 4,207 | 단일 모델 |
| Model L (price < 5M) | 1,906 (45.3%) | 절반 감소 |
| Model H (price ≥ 5M) | 2,301 (54.7%) | 절반 감소 |

→ Segmentation = sample 절반 + feature 동일 → variance 증가 + generalization 저하 → +5.23%p 악화

### 1.2 6A 핵심 메시지 (input)
- **Router quality was not the bottleneck** (recall 0.87 / Brier 0.11)
- **Segmentation reduced sample efficiency without adding new information**
- **Updates the program hypothesis from routing deficiency to feature scarcity under current inputs**

### 1.3 6B Hypothesis
> **6A 의 fragmentation harm 을 partial pooling 으로 완화 가능**:
> - Sample 통합 학습 유지 (모델 1개)
> - **Artist random intercept 만 추가** (Stage 3 ME identical, `is_low_price` fixed effect 삭제 — 코덱스 P1 타깃 누수)
> - Information sharing under heterogeneity — segmentation X

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Primary Model (Stage 3 ME 그대로 — `is_low_price` 제거)

```
log_price_ij = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
              + β4·spline(log_area_i)
              + u_j                      ← Artist j random intercept (Stage 3 ME 동일)
              + ε_ij
```

- Random intercept: artist (`MixedLM(formula, groups=artist_slug, re_formula="1")`)
- Same F4 + spline features (변경 X)
- **❌ `is_low_price` fixed effect 삭제 (코덱스 P1 — 예측 시점 price 미관측 = 타깃 누수)**

### 2.1.1 6B 의 차별점 (vs Stage 3 ME)
> Model spec 자체는 Stage 3 ME 동일. 6B 의 가치 = **6A 와의 비교 (segmented vs partial pooling) + Secondary 분석 (sparse-warm / ICC / newly-warm subgroup)**.
> Stage 3 ME LAO 결과 (cold-start 무력화 / random intercept 0 수축) 가능성 인정 (§9 정직한 기대치).

### 2.2 Implementation
- **Primary**: `statsmodels.regression.mixed_linear_model.MixedLM` (Stage 3 `stage3_mixed_effects.py` 와 동일 구조)
- **Estimation**: REML (default) — `MixedLM.fit(reml=True)` 고정
- **Fallback rule (코덱스 권고 — canonical 선택 deterministic)**:
  1. Optimizer 순서: `lbfgs` (default) → 실패 시 `bfgs` → 실패 시 `nm` (Nelder-Mead)
  2. ML/REML: REML 고정 (변경 X)
  3. **첫 성공 모델 = canonical** (이후 같은 seed/data 에서 재현 가능해야 함)
  4. statsmodels 모든 optimizer 실패 → R `lme4::lmer` (rpy2) **동일 사양** (REML / 동일 random structure)
  5. R fallback 도 실패 → **해당 seed skip + 보고 시 명시**
- **환경 pin** (실제 version 문자열, 본 prereg freeze 시점):
  * Python: 3.14
  * statsmodels: (실험 시작 시 `pip show statsmodels` 결과 명시)
  * scikit-learn / numpy / pandas: (동일)
  * (R fallback 사용 시) rpy2 / R / lme4 version 명시

### 2.3 명시 배제 (HARK 회피)
- ❌ 추가 segmentation (분리 학습)
- ❌ Router / meta-classifier
- ❌ External features (Stage 5 종료)
- ❌ Artist-segment interaction (`artist × is_low`) — 데이터 부담
- ❌ EB shrinkage 별도 (Stage 3 P3 의 Combined-shrunk 와 분리)

### 2.4 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, train 전체 / 운영 채택)
- 비교 단위: cold-start LAO 100-seed MdAPE

### 2.5 Primary Hypothesis (단일, unadjusted, 6A 동일)
- **H₀**: Partial pooling MdAPE ≥ baseline
- **H₁**: Partial pooling MdAPE < baseline
- **Test**: 1-sided 95% CI, cluster bootstrap n=2000

### 2.6 Primary Practical Significance (6A 동일 — 코덱스 권고)
- **Δ ≤ -1.0%p** (baseline 대비)
- > "6B 는 큰 효과보다 variance reduction 기반 modest improvement 기대 — but decision threshold 6A 동일 유지" (코덱스)

### 2.7 🔴 Hard Gate (6A 동일, 단일화 — 코덱스 P1)
- **Δ_low ≤ 0%p** (low-price segment 점추정 악화 X)
- 측정: 100-seed LAO 평균 (point estimate) 기준 + per-seed violation count 보조
- Hard gate 위반 = 즉시 FAIL (사전등록 §3.3 동일)

### 2.8 Secondary Hypotheses (Holm m=4 inferential + ICC mechanistic 별도 — 2026-05-07 freeze)

> 코덱스 P2 권고: Holm family 의 모든 항목은 동일한 inferential 검정 형태 필수. ICC 는 검정 형태가 다르므로 **별도 mechanistic 보조 지표**로 분리.

#### 2.8.1 Holm Family (m=4, 1-sided cluster bootstrap CI 동일 형태)

| # | 가설 | 임계 (CI 상한) |
|---|---|---|
| 1 | Low-price MdAPE non-inferiority | Δ_low CI 상한 ≤ 0%p |
| 2 | Mid/high MdAPE non-inferiority | Δ_high CI 상한 ≤ 0%p |
| 3 | **Sparse-warm artists** (train count ≤ 5) MdAPE improvement | Δ_sparse CI 상한 ≤ -1.0%p (partial pooling 핵심 가치) |
| 4 | **Newly warm artists** (Stage 3 학습 외 신규 warm) MdAPE improvement | Δ_new CI 상한 ≤ -1.0%p (Stage 4 +0.25 → 개선) |

→ Holm m=4 family-wise α=0.05 적용. **Family 자체 추가/삭제 = HARK violation**.

#### 2.8.2 Mechanistic 보조 지표 (Holm 외 — supportive only)

- **ICC (intra-class correlation)**: cluster bootstrap 95% CI lower bound
- 기준: **ICC CI 하한 > 0** (partial pooling 작동 검증) / 권장 ICC 점추정 ≥ 0.05 (Stage 3: 0.541)
- 본 지표 = mechanism 입증용 / **PASS 결정 영향 X** (단, FAIL 시 partial pooling 자체 불작동 신호로 해석)

### 2.9 Sample 분할 (Stage 3/4 동일)
- Train ≤ 2023 / Val 2024 / Test 2025 (Stage 4 v3 동일)
- Cold-start LAO 100-seed (Stage 3 ME 와 동일 protocol)
- Cluster bootstrap unit: artist
- **Val 2024 역할** (코덱스 Nit): **monitor only, decision unused** — 본 prereg 의 PASS / Holm 결정에 사용 X (튜닝 X)

### 2.10 Stratification + Subgroup
- Price segment: low / mid-high (사전등록 §2.7 hard gate)
- Artist depth bin: 10-14 / 15-24 / 25+
- **Sparse-warm**: train count ≤ 5 (Secondary 3 의 mechanism)
- Existing vs new warm (Secondary 5)

### 2.11 Canonical Artifact Triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `f4_spline_v1_20260506` (변경 X)
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`
- Partial pooling hash: `stage6b_partial_pooling_v2_20260507` (**Stage 3 ME identical — `is_low_price` fixed effect 제거 후 frozen spec**)

> **v2 frozen spec 단일 line (코덱스 P0 통일)**: 6B model = Stage 3 ME identical = `log_price ~ log_area + birth_year_centered + log_artist_total_works + log_area_spline + (1|artist)`. 어떠한 fixed effect 도 추가 X. 차별점은 단지 (a) 6A 와의 비교 + (b) Secondary 분석 (sparse-warm / ICC / newly-warm).

## 3. PASS / BORDERLINE / FAIL 결정 (코덱스)

### 3.1 PASS (6B 운영 채택 후보 진입 — 코덱스 단일화)
- **Primary**: Δ ≤ -1.0%p (점추정) AND Cluster bootstrap CI 상한 ≤ 0
- **🔴 Hard gate**: Δ_low ≤ 0%p (점추정)
- **Secondary**: supportive only (Holm reject 권장이지만 PASS 결정 영향 X)
- **ICC mechanism**: supportive only (해석 보조)
- → Phase 3 shadow 진입 검토

> **PASS 단순화 (코덱스)**: Primary + Hard gate **만** PASS 결정. Secondary / Mechanism = 해석 보조.

### 3.2 BORDERLINE (보류, 추가 cycle 검토)
- 🔴 Hard gate (저가 harm 0) **만족** AND
- Primary Δ 점추정 **소폭 개선** (-1.0 < Δ ≤ -0.3%p)
- 또는 Primary CI 만 미달 (점추정 ≤ -1.0%p but CI 상한 > 0)
- → 6C (new-information) 우선 검토

### 3.3 FAIL (6B 미채택, Stage 6 architecture-only 트랙 종료)
- 🔴 Hard gate **위반** (Low-price Δ > 0) — 즉시 FAIL
- 또는 Primary Δ > -0.3%p (소폭 개선 미달)
- → Architecture-only 트랙 모두 종료 → 6C (new-information) 만 남음 또는 운영 calibration only 유지

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| **Cold LAO 에서 random intercept 무력화** (Stage 3 ME 패턴 반복) | 사전등록 §1.3 명시: cold-start 대폭 개선은 주가설 X. Variance reduction 만 기대. |
| Effect size 미세 (-0.5%p 수준) → BORDERLINE | BORDERLINE 명시 — 6C 진입 결정 |
| MixedLM 수렴 실패 / Python 3.14 호환성 | 사전등록 §2.2 fallback rule (optimizer 변경 → re_formula 단순화 → R lme4) |
| Sparse-warm 효과 측정 시 sample 부족 | Secondary 3 = exploratory 성격, mechanism 검증용 |
| HARK risk (6A 결과 본 후 6B 설계) | §0 / §1.3 framing 의무 명시: registered follow-up |
| Random intercept 가 global mean 으로 수축 | Secondary 4 (ICC > 0) 로 mechanism 검증 — 0 이면 partial pooling 작동 X 입증 |

## 5. 일정 / 산출물

| 단계 | 일정 | 산출물 |
|---|---|---|
| Prereg freeze | 2026-05-07 | 본 문서 |
| 환경 점검 (statsmodels MixedLM Python 3.14 호환) | 1일 | (실험 시작 전) |
| 실험 (LLM) | 1-2일 | `experiments/structural_v1/stage6b_partial_pooling.py` + JSON |
| 결과 보고 | 1일 | `docs/stage6b_results_20260507.md` |
| 코덱스 검토 + 판정 | 1일 | PASS / BORDERLINE / FAIL |

## 6. Sensitivity / Exploratory (Primary 결정 X)

> 사전등록 외 — 결과 보고 시 별도 명시:
> - Random slope (artist × log_area) — Stage 3 ME 와 동일 후 점검
> - Time weights (Stage 3 P3 와 동일)
> - is_low_price threshold sensitivity (3M / 5M / 7M KRW)

## 7. 후속 cycle 시나리오

| 시나리오 | 액션 |
|---|---|
| **PASS** | Phase 3 shadow 진입 + Spec §17 partial pooling fixed effect 추가 |
| **BORDERLINE** | 6C (new-information, pre-screen 통과 시) 우선 + 6B 결과 mechanistic 가치 (ICC) 별도 보고 |
| **FAIL (저가 harm)** | Architecture-only 트랙 종료 — 6C 만 남음 또는 calibration only 유지 |
| **FAIL (Δ 미달)** | 동일 — Stage 6 cycle 종료 검토 |

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6A FAIL 검수 (2026-05-07) | "Architecture-only 6A 종료, 6B = shared-modeling, 6C = new-information 두 축" |
| **본 prereg 사전 자문 (2026-05-07)** | statsmodels MixedLM (a) / Stage 3 ME 재사용 / Δ 6A 동일 / Secondary Holm m=5 (router 제외 + ICC + sparse-warm) / fallback rule |
| 본 prereg 검수 (2026-05-07 v2) | P1: `is_low_price` 타깃 누수 → 삭제 / Hard gate 단일화 / Fallback canonical / Secondary Holm m=4 + ICC 분리 / Val 2024 monitor only |
| 6B 결과 (예정) | PASS / BORDERLINE / FAIL 판정 + 후속 cycle |

## 9. 핵심 메시지 (코덱스)

> **본 6B 의 정직한 기대치**:
> - 큰 효과 (-2.0%p+) 기대 X — feature shortage 본질 미해결
> - 기대 = **Variance reduction 기반 modest improvement (-0.5 ~ -1.5%p)** + low-price harm 완화 + sparse-warm 처리
> - **Cold-start 대폭 개선 = 주가설 아님** (Stage 3 ME 패턴 인정)
> - **Mechanism 검증 (ICC) 가 architecture 가치 입증의 핵심**

## 10. 다음 액션

1. ✅ 본 prereg freeze (2026-05-07) — 본 문서
2. ⏳ 환경 점검: statsmodels MixedLM Python 3.14 호환성 확인 + version pin
3. ⏳ 6B 실험: `stage6b_partial_pooling.py` 작성 + 100-seed LAO + cluster bootstrap
4. ⏳ 결과 보고서 + 코덱스 검토
5. ⏳ (별도) 6C pre-screen 4 항목 병행 준비 (코덱스 — 결정은 6B 후)

## 11. 참조

- 6A 결과: `docs/stage6a_results_20260507.md`
- 6A prereg: `docs/stage6a_segmented_prereg_20260507.md`
- Stage 6 cycle draft v2: `docs/stage6_prereg_draft_20260507.md`
- 단기 트랙 (저가 feature 부족): `docs/stage4_short_term_track_results_20260507.md`
- Stage 3 ME (재사용 base): `experiments/structural_v1/stage3_mixed_effects.py`
- Stage 3 P3 (composition-shift 결과): `experiments/structural_v1/stage3_warm_p3_validation.py`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
