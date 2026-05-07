# Stage 6A — Segmented Architecture Confirmatory Pre-registration

> **작성일**: 2026-05-07 (freeze, 코덱스 자문 반영)
> **위치**: 새 Phase 2' (Stage 5 미개시 종료 후 architecture cycle) 의 **6A 1순위**
> **연계**: `docs/stage6_prereg_draft_20260507.md` (전체 cycle draft) / `docs/stage4_warm_validation_results_20260507.md` (Stage 4 BORDERLINE input) / `docs/stage4_short_term_track_results_20260507.md` (저가 feature 부족 입증)

> ⚠️ **본 prereg 의 목적 / 비목적** (코덱스):
> - 목적: Segmented architecture (low vs mid/high 분리 학습 + Meta-router) 의 cold-start MdAPE 개선 + 저가 segment harm 해결 검증
> - **비목적**: 즉시 운영 도입 (PASS 시 Phase 3 shadow 진입, FAIL 시 6B Bayesian 검토)
> - 비목적: segmentation 만으로 feature 부족 (Stage 4 결과) 자동 해결 가정 X — feature shortage 가 본질, segmentation = pooled bias 감소만

> **HARK 회피**: 본 §2 의 routing 방식 / 임계 / metric / Holm family / PASS 기준 = **2026-05-07 freeze**. 결과 본 후 변경 X.

## 1. 배경

### 1.1 Input (이전 cycle 결과)
- **Stage 4 v3**: BORDERLINE 보류 (warm-only path `not advanced`) + 저가 violation +5.63%p
- **단기 트랙 작업 3** (저가 decomp): Feature 부족 가설 3/3 시그니처 (코덱스 1순위)
- **단기 트랙 작업 4** (calibration): Global additive ✓ but baseline cold path 한정
- **Stage 5 cycle 종료**: External feature acquisition 준법적 자동화 불가 → 미개시 종료

### 1.2 6A hypothesis
저가 / mid-high 분리 학습으로 baseline pooled bias 감소 → cold-start MdAPE 개선 + 저가 harm 해결.

### 1.3 6A 비-가정 (코덱스 권고)
- ❌ "Segmenting 하면 자동 해결" — 없는 가격결정 변수 만들지 못함
- ❌ Routing 재귀 (a) — circularity risk
- ❌ Heuristic routing (c) — cold-start primary 와 mismatch (artist mean log_price = warm-history prior)
- ❌ Hybrid (d) — (a)+(b) 의 단점 합산

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Routing — Meta-router (b) 고정
- **분류기**: `price_krw < 5,000,000` 이진 분류기 (LogisticRegression)
- **입력 features**: F4 + log_area spline **만** (추가 변수 사용 X — HARK 회피)
- **학습 split**: train (year ≤ 2023) **1회 학습**, val/test 에 적용 (재학습 X)
- **Threshold**: 사전 0.5 (probability threshold), sensitivity 0.4 / 0.6 부록 (PASS 결정 영향 X)
- **Meta-router 의 misclassification cost**: 비대칭 — **low → mid/high (FN) 가 더 비쌈** (저가 작품 mid/high 모델이 처리 시 +38% 과대 예측 위험, Stage 4 baseline bias 패턴)

### 2.2 Segmented model
- Model L (low-price): F4 + log_area spline + Huber, **train low (n=1,906) 만 학습**
- Model H (mid/high): F4 + log_area spline + Huber, **train mid/high (n=2,301) 만 학습**
- 운영 시: Meta-router 가 segment 결정 → Model L 또는 Model H 가 예측

### 2.3 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, **train 전체 4,207** 학습 / 운영 채택)
- 비교 단위: cold-start LAO 100-seed MdAPE

### 2.4 Primary hypothesis (단일, unadjusted)
- **H₀**: Segmented MdAPE ≥ baseline (24.07%)
- **H₁**: Segmented MdAPE < baseline
- **Test**: 1-sided 95% CI, cluster bootstrap n=2000, **단일 비교 (unadjusted)**

### 2.5 Primary practical significance (코덱스 권고)
- **Δ ≤ -1.0%p** (baseline 24.07% → 23.07% 이내)
- (Draft §3.3 의 -1.5%p 에서 -1.0%p 완화 — harm 0 hard gate 와 균형)

### 2.6 Secondary hypotheses (Holm m=4 별도 family, 2026-05-07 freeze)

| # | 가설 | 임계 |
|---|---|---|
| 1 | Low-price MdAPE 개선 | Δ_low ≤ -2.0%p (Stage 4 +5.63%p violation 해결) |
| 2 | Mid/high MdAPE 비악화 | Δ_high ≤ +0.5%p |
| 3 | **Router low-price recall** (또는 low→mid/high FN rate) | recall ≥ 0.85 (즉 FN rate ≤ 15%) |
| 4 | **Router balanced accuracy 또는 Brier score** | balanced acc ≥ 0.75 (또는 Brier ≤ 0.20) |

> 코덱스 권고: 3번을 raw accuracy 가 아닌 low recall (FN cost 비대칭). 4번을 composition-shift 신규 warm 효과 → router 품질 지표로 대체.

### 2.7 Sample 분할 (Stage 4 v3 동일)
- Train ≤ 2023 (4,207 작품 / 555 작가 / warm 120명)
- Val == 2024 (1,953 / 376)
- Test == 2025 (2,335 / 402, **2026+ 제외**)
- LAO 100-seed (Stage 3/4 동일 protocol)

### 2.8 Segment harm budget (Stage 4 v3 동일)
| Segment | 허용 악화 |
|---|---|
| **저가 (price < 5M)** | **0%p (hard gate)** |
| 중가 / 고가 | +0.5 / +1.0%p |
| Depth 10-14 / 15-24 / 25+ | +1.5 / +1.0 / +0.5%p |

### 2.9 Canonical artifact triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `f4_spline_v1_20260506` (Meta-router + Model L + Model H 모두 동일)
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`
- Routing hash: `meta_router_v1_20260507` (LogisticRegression / threshold 0.5 / F4+spline 입력)
- Segmented hash: `stage6a_segmented_v1_20260507` (Model L + Model H + Router)

## 3. PASS / BORDERLINE / FAIL 결정 (코덱스 강화)

### 3.1 PASS (Phase 3 shadow 진입 후보)
- **Primary**: CI 상한 ≤ 0 (1-sided 95% CI cluster bootstrap)
- **Practical**: Δ ≤ -1.0%p (점추정)
- **🔴 Hard gate**: 저가 segment harm = **0 violations** (Δ_low ≤ +0%p, 절대 악화 X)
- **Secondary** (Holm m=4 보정 후, 권장): Mid/high 비악화 + Router 품질 지표 ≥ 임계

### 3.2 BORDERLINE (보류, 6B 검토)
- 🔴 Hard gate (저가 harm 0) **만족** AND
- Primary CI 상한 또는 practical Δ **1개만 미달**
- 다른 segment harm violation 0건 (depth bin 등)

### 3.3 FAIL (6A 미채택, 6B Bayesian 우선 검토)
- 🔴 Hard gate **위반** (저가 harm ≥ 1 violation) — 즉시 FAIL
- 또는 Primary CI 상한 + practical Δ **둘 다 미달**

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Feature shortage 본질 (Stage 4 winner=feature) | segmentation 자동 해결 X — 사실 인정 + 6B Bayesian 우선 |
| Router misclassification cost 비대칭 (low→high FN) | Secondary 3 = low recall (보정 metric) |
| 5M 경계 근처 불안정성 | Threshold 0.5 freeze + sensitivity 0.4/0.6 부록 |
| Cold-start LAO 에서 routing 정확도 약화 | Sample size 와 split 충분 (n=4,207, 1.9K low/2.3K high) |
| HARK risk (결과 본 후 임계 변경) | 본 prereg freeze 의무, deviation log + 새 cycle 분리 |

## 5. 일정 / 산출물

| 단계 | 일정 | 산출물 |
|---|---|---|
| Prereg freeze | 2026-05-07 | 본 문서 |
| 실험 (LLM) | 1-2일 | `experiments/structural_v1/stage6a_segmented.py` + JSON |
| 결과 보고 | 1일 | `docs/stage6a_results_20260507.md` |
| 코덱스 검토 + 판정 | 1일 | PASS/BORDERLINE/FAIL |

## 6. Sensitivity / Exploratory (Primary 결정 X)

> **사전등록 외 — 결과 보고 시 별도 명시**:
> - Routing (a) Naive first-pass / (c) Heuristic / (d) Hybrid — exploratory comparison
> - Threshold 0.4 / 0.6 sensitivity (router)
> - Splits 2022 / 2023 / 2024 rolling (Stage 4 v3 동일)

## 7. 후속 cycle 시나리오

| 시나리오 | 액션 |
|---|---|
| **PASS** | 6A 운영 채택 후보 → Phase 3 shadow 진입 + Spec §17 routing 로직 추가 |
| **BORDERLINE** | 6B Bayesian / hierarchical 검토 (cold/warm 경계 + sparse artist) |
| **FAIL** (저가 harm) | 6A 폐기 + 6B / 6C 우선 검토 |
| **FAIL** (CI / practical) | 6A 폐기 + 6B 우선 |

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 5 종료 자문 | Stage 6 1순위 = Segmented architecture 권고 |
| **본 prereg 사전 자문 (2026-05-07)** | Routing (b) Meta-router / Δ ≤ -1.0%p / Secondary 3-4 수정 / harm 0 hard gate |
| 6A 결과 검토 (예정) | PASS/BORDERLINE/FAIL 판정 + 후속 cycle 권고 |
