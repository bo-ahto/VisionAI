# Stage 5C — Confirmatory Modeling Prereg (External Features)

> **작성일**: 2026-05-07 (Stage 5A 시작 전 freeze, modeling 가설 / metric / PASS 기준 사전등록)
> **목적**: External feature acquisition (5A-5B) 결과를 baseline 모델 위에 통합 → Stage 4 보류 결정 (cold-start MdAPE 24.07% / 저가 segment harm) 의 본질적 개선 검증
> **위치**: 새 Phase 2 = Stage 5 의 **3번째 단계** (5C). 5A-5B 종결 후 acquisition 결과 dataset 으로 modeling 수행.
> **연계**: `docs/stage5a_acquisition_prereg_20260507.md` (acquisition 분리) / `docs/stage4_short_term_track_results_20260507.md` (input)

> ⚠️ **HARK 회피 — acquisition 결과 보기 전 freeze**:
> - **본 prereg 의 가설 / metric / PASS 기준 / Holm family**: 본 문서 작성 시점 (2026-05-07) freeze
> - **5A-5B 결과 (matched dataset / feature dictionary)**: 향후 확정 → 본 prereg 의 feature_X / Y 자리 표기로 고정
> - 5A-5B 결과 본 후 가설 / metric 변경 시: deviation log 의무 + 새 cycle 분리
> - **본 prereg 작성 시점에는 5A 결과 미정** — feature 구체값은 placeholder (`<external_feature_set>`)

## 1. Background

### 1.1 Stage 4 + 단기 트랙 결과 (input)
- Stage 4 v3 BORDERLINE 보류 — 일반 warm 경로 `not advanced`
- 단기 트랙 작업 3: Feature 부족 가설 3/3 시그니처 (코덱스 1순위 정확)
- 본질 = 외부 source (Artsy 미사용 컬럼 모두 정보 X 입증)

### 1.2 Stage 5C 의 위치
- 5A (feasibility) → 5B (acquisition / entity resolution) → **5C (confirmatory modeling)** → 5D (deployment 결정)
- 5C primary = acquisition 효과의 통계적 + 실용적 검증

## 2. Pre-registration Items (코덱스 9 항목 + 추가)

### 2.1 Primary hypothesis (단일, unadjusted)

> **H₀**: External-feature model MdAPE ≥ baseline MdAPE (개선 없음)
> **H₁**: External-feature model MdAPE < baseline MdAPE (개선 있음)

### 2.2 Primary metric
- **Cold-start LAO 100-seed MdAPE** (Stage 3/4 동일 protocol)
- artist-cluster bootstrap CI (n=2000)
- 1-sided 95% CI

### 2.3 Practical significance (사전 fix)
- **MdAPE 차이 ≤ -2.0%p** (baseline 24.07% → 22% 이내)
- 단순 통계 유의성 만으로 부족 — 운영 도입 가치 임계

### 2.4 Baseline (변경 X)
- `track2_v1_20260507`: F4 + log_area spline + Huber (eps=1.35, alpha=1e-4)
- Stage 4 v3 와 동일 model hash + pipeline version
- (보조 비교) Global additive calibration 적용 baseline (단기 트랙 작업 4 candidate)

### 2.5 External-feature model 후보 (5A 결과 후 확정)

> **본 prereg 작성 시점에 미정** — placeholder. 5A 종결 후 dictionary 확정 시 re-freeze 의무.

| Family | 변수 후보 | Source 추정 |
|---|---|---|
| **F1: Auction price anchor** | `<auction_median_price_log>` / `<auction_price_count>` / `<auction_recency>` | 5A 1순위 (auction archives) |
| **F2: Market activity** | `<auction_total_lots>` / `<repeat_sale_indicator>` | 5A 1순위 |
| **F3: Provenance / exhibition** | `<solo_count_external>` / `<institution_count>` (Artsy 보유 + auction CV) | 5A 2순위 |
| (5A 결과 의존) | (추가 family) | (추가 source) |

### 2.6 Secondary hypotheses (Holm m=6 confirmatory, primary 와 별도 family — **2026-05-07 fix**)

> 본 6개 list 는 **2026-05-07 freeze**. 5A-5B 종결 후 변경 X (HARK 회피).
> Family 정의 = Stage 4 결과 기반 — F1/F2/F3 family 자체는 placeholder 가 아님 (구체 변수만 5A 결과 후 매핑).

1. **Low-price segment harm 감소**: Stage 4 baseline-vs-FE +5.63%p → external model 에서 +1%p 이내
2. **Depth 15-24 harm 감소**: Stage 4 +6.76%p → +1%p 이내
3. **Composition-shift 개선** (신규 warm 작가 효과): Stage 4 신규 +0.25%p → external model 에서 -2%p 이상
4. **F1 family (Auction price anchor) 단독 효과**: external model − baseline ≤ -1.0%p
5. **F2 family (Market activity) 단독 효과**: external model − baseline ≤ -1.0%p
6. **F3 family (Provenance / exhibition) 단독 효과**: external model − baseline ≤ -1.0%p

> **m=6 Holm family-wise α=0.05** 적용. **5A 결과 후 변경 가능한 것 = 각 family 의 구체 변수 명** 만 (예: `auction_median_price_log` ↔ `auction_mean_price_log` 등). family 자체 추가/삭제 = HARK violation → deviation log + 새 cycle.

### 2.7 Sample 분할 (변경 X)
- Train ≤ 2023 / Val 2024 / Test 2025 (Stage 4 v3 동일)
- Cluster bootstrap unit: artist
- Rolling sensitivity: cutoff 2022 / 2023 / 2024 (3개)

### 2.8 Stratification
- warm artist depth bin (10-14 / 15-24 / 25+) — Stage 4 동일
- low-price (price_krw < 5M) vs mid-high — 단기 트랙 동일

### 2.9 Seed 안정성
- 10 seed × n_boot=500
- std ≤ 0.5%p 요구

### 2.10 본실험 제외 모델 (Stage 4 동일)
- gallery_tier dummy / interaction (Stage 3 재탐색 결과 기준)
- medium_category, 다중 interaction, Core 5 조합 (선형 모델 권고 검증 결과)

### 2.11 Canonical artifact triple

| 항목 | 값 |
|---|---|
| Model hash (baseline) | `track2_v1_20260507` |
| Feature pipeline version (baseline) | `f4_spline_v1_20260506` |
| External feature dictionary | `<stage5b_feature_dict>` (5A-5B 종결 시 확정) |
| External feature pipeline version | `f4_external_v1_<YYYYMMDD>` (5C 시작 시 freeze) |
| Train data hash | `data/curated/stage5_*.parquet` (5C 시작 시 freeze) |

## 3. PASS / BORDERLINE / FAIL 결정 (사전 fix)

### 3.1 PASS (운영 채택 후보 진입)
- Primary CI 상한 ≤ 0
- Practical Δ ≤ -2.0%p (point estimate)
- Seed std ≤ 0.5%p
- Segment harm 0 violations (Stage 4 동일 임계)
- 신규 warm 작가 generalization (composition-shift) 개선 또는 동등
- → Phase 3 (Production validation) shadow 진입 자격

### 3.2 BORDERLINE (보류 + 재검토)
- Primary CI 상한 ∈ (0, +1%p]
- Practical Δ ∈ (-2.0, -0.8]%p
- Segment harm 1-2 violations
- → Stage 6 추가 검토 또는 segmented architecture 검토

### 3.3 FAIL (External feature acquisition 실효성 입증 X)
- Primary 점추정 양수 또는 ±0%p 근처
- Practical Δ > -0.8%p (실용 의미 X)
- Segment harm 3+ violations
- → External feature 영향 X 결론, baseline 유지 + 다른 전략 (Bayesian / segmented model) 검토

## 4. Statistical Plan

### 4.1 Cluster bootstrap CI
- Primary: n=2000, 1-sided 95% CI
- Secondary: n=1000, Holm m=N

### 4.2 100-seed evaluation
- LAO 100-seed (Stage 3 동일 protocol)
- mean + std

### 4.3 Subgroup pre-defined
- Price tertile (저가 / 중가 / 고가)
- Depth bin (10-14 / 15-24 / 25+)
- 신규 warm vs 기존 warm
- Source: Artsy only (Saatchi 제외 동일)

### 4.4 PASS 보고 의무 항목
- 합격 조건 5 항목 (§3.1: CI 상한 / practical Δ / seed std / segment harm / composition-shift) 모두 결과 명시
- effect heterogeneity (subgroup CI) 동시 보고
- 실패 항목 있으면 BORDERLINE 또는 FAIL 분류

## 5. HARK Control (코덱스 권고)

### 5.1 5A-5B vs 5C prereg 분리 (이미 적용)
- 5A-5B = acquisition 자체 (가설 / metric X)
- 5C = modeling 가설 / metric / PASS 사전등록

### 5.2 5A 결과 후 frozen data dictionary
- 5A-5B 종결 시 `docs/stage5b_feature_dictionary.md` 작성 (확정 feature 명세)
- 본 5C prereg 의 placeholder (`<external_feature_set>`) → 확정 feature list 로 re-freeze
- Re-freeze 시 deviation log entry 의무

### 5.3 Modeling 결과 후 추가 분석 금지
- 본 prereg 의 secondary 외 추가 분석 = exploratory (별도 보고)
- 새 secondary 추가 = HARK violation

## 6. 산출물 / 일정 (5A-5B 종결 후)

| 단계 | 작업 | 산출물 |
|---|---|---|
| 5C-W1 | 5A-5B 결과 dictionary 검토 + 본 prereg re-freeze | re-freeze entry |
| 5C-W2 | Cleansing pipeline 적용 (external + Artsy 통합) | `data/curated/stage5_*.parquet` |
| 5C-W3 | Power simulation 재실행 (external feature 분포 기반) | power 결과 |
| 5C-W4 | Modeling 실험 (primary + secondary + composition + harm) | `experiments/structural_v1/stage5_modeling.py` 결과 |
| 5C-W5 | 결과 보고서 + 코덱스 자문 + PASS/BORDERLINE/FAIL 판정 | 보고서 |

## 7. 후속 액션 시나리오

### 7.1 PASS 시
- 5D Deployment / legal / monitoring decision
- Production spec §17 / §1-§16 통합 검토

### 7.2 BORDERLINE 시
- Stage 6 = segmented architecture 또는 Bayesian model 검토
- 5C 결과 기반 추가 source 보강 (Stage 5 확장)

### 7.3 FAIL 시
- External feature 영향 X 결론
- 운영 안전장치 (단기 트랙 작업 4 calibration) 만 채택
- 모델 family 변경 (Bayesian / hierarchical / GBM) Stage 6 검토

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 4 단기 트랙 종결 | Stage 5 = "external feature acquisition" 중심 권고 |
| 본 prereg 사전 자문 (2026-05-07) | 사전등록 9 항목 + Conformal / Bayesian 후순위 + 저가 분리 모델 추후 |
| 5A 종결 후 (예정) | feature dictionary 확정 + 본 prereg re-freeze 자문 |
| 5C 결과 (예정) | PASS/BORDERLINE/FAIL 판정 + 후속 cycle 권고 |

## 9. 위험 + 대응

| 위험 | 대응 |
|---|---|
| 5A REJECT (모든 source FAIL) | 본 5C prereg 자동 폐기 / Stage 5 종결 |
| External feature 통합 후에도 PASS 미달 | BORDERLINE / FAIL 판정 → Stage 6 또는 운영 calibration 만 채택 |
| Re-freeze 시 가설 변경 시도 (HARK) | Deviation log 의무 + 새 cycle 분리 |
| Composition-shift 본질적 미해결 | 운영 정책 강화 (신규 warm 자동 fallback, 이미 spec §17.7 적용) |

## 11. 본 prereg 자동 폐기 (Stage 5A Week 2 결과 후, 2026-05-07)

> ⚠️ **본 prereg cycle 종결**: Stage 5A Week 2 결과 — Artsy 자동화 fetch 0/10 차단 + TOS 위험 → 사전등록 §6.3 적용 (모든 candidate REJECT). F1/F2/F3 family 모두 실현 불가 → 본 prereg §9 위험 표 첫 row "5A REJECT — 본 5C prereg 자동 폐기" 적용.
>
> **운영 적용 영향**: 분기 B 활성화 (`docs/stage5a_week3_decision_memo_20260507.md` 참조) — Calibration only 운영 적용, Stage 6 (segmented architecture / new family) 별도 decision gate.
>
> 결과 보고: `docs/stage5a_week2_results_20260507.md`

## 10. 현 prereg 기준 PASS 기대 (5A Week 1 결과 후 추가, 코덱스 권고 — 참고)

> **2026-05-07 Stage 5A Week 1 결과 후 명시**: Auction archives 4 source 모두 REJECT (Stage 4 cohort cover 0/6) → **F1 (auction price anchor) family 실현 가능성 ✗**.
>
> ⚠️ **현 prereg 기준 PASS 기대 낮음**: F1 부재 시 F2 (market activity) + F3 (provenance) 만 가능. Primary Δ ≤ -2.0%p 임계 도달 어려울 수 있음.
>
> **임계 완화 X** (사전등록 변경 = major deviation, HARK violation). 대신:
> - Week 3 의사결정에서 BORDERLINE / FAIL 판정 시 Stage 5 종결 + calibration only 분기 (`docs/stage5a_week3_decision_memo_20260507.md` 분기 B)
> - 또는 Stage 6 새 prereg (segmented architecture / Bayesian / new model family)
