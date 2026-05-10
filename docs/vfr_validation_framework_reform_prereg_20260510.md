# VFR: Validation Framework Reform — Analysis Cycle (analysis-only / non-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: 본 세션 cold path 5 cycle 모두 fail (D1.X / D1.Y / D1-extended / D1.SC) + B (warm-only) 5/5 PASS 격차
> **Decision binding**: ❌ **NO** — analysis-only / hypothesis-generating / framework recommendation 도출만

## 1. Goal

본 세션 누적 결과 패턴:

| Cycle | Path | Aggregate (strict R1 P1.1) | Bad-seed rate |
|---|---|---|---|
| B (warm-only retune) | warm | **PASS (5/5)** | 0% |
| D1.X | cold+warm | NEEDS_MORE_DATA (4/5) | 20% |
| D1.Y | cold+warm | FAIL (7/10) | 30% |
| D1-extended | cold+warm | FAIL (2/10) | 80% |
| D1.SC (source-conditional) | cold | FAIL (1/10 overall) | 90% |

**핵심 질문**: 왜 B (warm path)는 5/5 strict PASS인데 cold path retune은 모든 axis 20-90% bad-seed rate?

가능한 원인:
- (a) **Cold path validation 자체가 본질적으로 split variance 큼**: artsy_gallery cell n_holdout 150-250 / heavy-tailed 가격 분포 / strict per-seed framework는 small-cell heavy-tail에 over-sensitive
- (b) **Cold retune이 진짜 작동 안 함**: D1 retuned params는 warm path만 개선 / cold는 noise / 운영 cold 개선 불가능
- (c) **둘 다 일부 사실**: Cold path는 (a) noise + (b) effect size 작음 — 현 framework는 두 요소 분리 X

**본 cycle 목표** (R1 codex framework-shopping warning 정합):
- ✅ Existing per-seed delta data 위 **noise/signal characterization** (cold vs warm 비교)
- ✅ 다양한 aggregation method 적용 (robust / bootstrap / cell-weighted) — 어느 method가 B 5/5 PASS를 정확히 식별하면서 D1 fail을 일관 fail로 식별하는가?
- ✅ Framework recommendation 도출 (next-cycle prereg 후보)
- ❌ **본 cycle은 운영 채택 발동 X** (post hoc framework shopping 회피)
- ❌ **본 cycle은 D1 결정 변경 X** (D1 axis abandon 결정 그대로)

본 cycle 결과 = exploratory finding only / 후속 prospective cycle (preregister NEW framework on fresh seeds with B as positive control)의 hypothesis 제공.

## 2. Method

### 2.1 Input data (existing per-seed deltas)

본 세션 commit된 cycles의 per-seed delta JSON 활용:
- `model_test_results/d1_validation_20260510.json` (D1.X / N=5)
- `model_test_results/d1_y_validation.json` (D1.Y / N=10)
- `model_test_results/d1_extended_results.json` (D1-extended / N=10)
- `model_test_results/d1_sc_results.json` (D1.SC / N=10)
- `model_test_results/b_warm_validation.json` (B / N=5)

각 cycle 별 per-seed Δ_cold_overall / Δ_cold_artsy / Δ_cold_saatchi / Δ_warm 추출.

### 2.2 Noise/signal characterization

**Per-cell statistics** (cold cells × warm cell × cycles):

각 cell × cycle 조합에서:
- Mean Δ
- Standard deviation Δ
- IQR (interquartile range)
- Coefficient of variation (CV = std / |mean|)
- Outlier count (|delta − mean| > 2σ)

**비교 측면**:
- Warm path B: small std (0.137) / small CV
- Warm path D1.X / D1.Y / D1-extended (all cycles): small std (~0.18-0.20)
- Cold path D1.X / D1.Y / D1-extended / D1.SC: large std (~0.95-1.20+)

**가설**: cold path는 warm path 대비 std ~5-10× 큼 / 같은 strict framework에서 false negative rate 높음.

### 2.3 Aggregation method comparison (R1 amendment)

**Methods (R1 P2 fix / count = 7)**:

1. **Strict per-seed (현행 R1 P1.1)**: PASS×N strict / FAIL ≥ 2 → FAIL
2. **Bootstrap CI on mean** (D1-extended secondary 정합 / 95% CI): CI upper ≤ 0 → PASS
3. **Trimmed mean** (top-bottom 10% trim): trimmed mean ≤ 0 → PASS
4. **Median CI** (median + bootstrap CI): median CI upper ≤ 0 → PASS
5. **Cell-size weighted** (artsy holdout n × Δ_artsy + saatchi n × Δ_saatchi / total n): weighted mean ≤ 0 → PASS
6. **Quantile-based (P75 robustness)**: 75th percentile of per-seed Δ ≤ +0.3 → PASS
7. **Effect size (Cohen's d)**: |mean| / std vs minimum effect threshold (e.g. d ≥ 0.3)

### 2.3.1 Cold cycle classification (R1 P1.1 amendment)

**R1 P1.1 fix**: 모든 D1 fail이 ground truth FAIL이라 가정하면 새 framework는 noise 흡수 능력을 평가 불가 (self-defeating). Cycle을 confidence별 분류:

**Clear negatives** (반드시 FAIL 유지):
- **D1-extended** (8/10 FAIL / bootstrap mean +0.22 / strong negative signal)
- **D1.SC** (1/10 overall PASS / 모든 primary FAIL / source split도 도움 X)

**Ambiguous cases** (FAIL 유지 또는 INCONCLUSIVE 이동 허용 / 새 framework가 noise 흡수했을 수 있음):
- **D1.X** (4/5 PASS / 1 outlier / 강한 cold mean -1.86)
- **D1.Y** (7/10 PASS / 3 outliers / population mean -1.16 강한)

**Positive control** (반드시 PASS 식별):
- **B** (5/5 PASS / known winner / std=0.137)

### 2.3.2 Framework selection criterion (R1 P1.2 amendment / preregistered tie-break ordering)

새 framework 평가 ranking (순서대로 binding):

1. **B positive-control PASS** (mandatory) — 본 조건 fail 시 method reject
2. **Clear-negative false positives 최소화** (D1-extended / D1.SC가 ADOPT 발동 시 method reject)
3. **Ambiguous handling stability** — D1.X / D1.Y에서 verdict가 leave-one-seed-out 시 안정적 (bootstrap CV 작음)
4. **Simplest method wins ties** — 동일 ranking 시 단순한 method 선택 (e.g. trimmed mean > bootstrap CI > effect size)

→ 본 ordering이 "적합 method" 정의 / 단일 method 선택 보장 (R1 P1.2 / tie-break preregistered).

### 2.4 Specific analyses

### 2.4.1 Analyses (Analysis A-E / 5 components)

**Analysis A**: cold vs warm noise/signal ratio
- Cold path: std/|mean| 분포 (D1 cycles 누적)
- Warm path: std/|mean| 분포 (B + D1 cycles warm 부분)
- Ratio quantification

**Analysis B**: small-cell vs large-cell variance
- artsy_gallery (n_holdout 150-250) vs artsy_online (n_holdout 1500-2000) vs saatchi_online (n_holdout 4500+)
- Cell size에 따른 std scaling 측정

**Analysis C**: B winner cross-method validation
- B per-seed deltas (5 fresh seeds / 5/5 PASS)에 7 aggregation methods 적용
- 모든 method가 PASS 발동? / 어느 method가 fail false negative?

**Analysis D**: D1 cross-method
- D1.X / D1.Y / D1-extended / D1.SC per-seed deltas에 7 methods 적용
- 어느 method가 D1 PASS (false positive)? / 어느 method가 일관 fail (true negative)?

**Analysis E**: Population mean vs sample variance trade-off
- D1 mean Δ_cold_overall = -1.16 (D1.Y) / +0.22 (D1-extended) / -0.40 (D1.SC) — sample-dependent
- B mean Δ_warm = -1.62 (5 seeds) / -2.13 (D1.Y warm 10) / -2.14 (D1-extended warm 10) — stable
- Stability ratio quantification

### 2.5 Framework recommendations 도출

본 cycle 결과로 candidate frameworks 도출:

- **Framework A (현행 R1 P1.1 strict)**: champion swap 정합 / FAIL ≥ 2 → FAIL
- **Framework B (cell-size weighted strict)**: 작은 cell의 outlier weight 감소
- **Framework C (robust per-seed)**: strict per-seed BUT outlier trimming
- **Framework D (multi-method consensus)**: 2개 이상 method PASS 시 ADOPT_canary

각 framework에 대해:
- B winner 식별 정확성
- D1 false positive rate
- 운영 risk (small bad split user impact)
- 적용 cost (compute / 복잡성)

**최종 output**: framework recommendation table → 새 prospective cycle (별도 prereg / fresh seeds + new framework preregister + B positive control) 후보.

## 3. Output

- `docs/vfr_validation_framework_reform_prereg_20260510.md` (본 문서)
- `docs/vfr_validation_framework_reform_results_20260510.md` (analysis report + recommendations)
- `scripts/vfr_framework_analysis.py` (existing JSON load + per-cell statistics + 7 aggregation methods 적용 + comparison)
- (gitignored) `model_test_results/vfr_analysis_results.json`

## 4. Out-of-scope (R1 codex framework-shopping warning 정합)

- ❌ **운영 채택 결정 변경 X** — D1 axis abandon / B-winner ADOPT 결정 그대로
- ❌ **본 cycle 결과로 새 framework 즉시 적용 X** — Phase 2 (별도 prospective preregister cycle) 권고만
- ❌ **새 model 학습 X** (existing per-seed deltas만 활용)
- ❌ **Threshold shopping X** (모든 framework는 prereg 시점 명시 / 결과 보고 method 선택 X)
- ❌ **Single dataset 결정 binding X** (post hoc analysis only / fresh seeds + B positive control은 별도 후속 cycle)

## 5. 한계 / Risk

- **Post hoc analysis risk**: 같은 데이터 여러 method 적용 / framework selection이 데이터-driven 가능성 / hypothesis-generating only로 명시
- **B as positive control 제한**: B는 warm path single axis / cold path framework validation에 부분만 적용 가능
- **Multiple method comparison risk**: family-wise error inflation / 단 본 cycle은 binding decision 발동 X / risk 작음
- **Framework reform 자체의 codex skepticism**: codex R1에서 "abandon D1" 강한 권고 → 새 framework로 D1 반전 시도 X / 본 cycle은 next-cycle prep 만

## 6. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **NEEDS FIX** | P1.1 (framework-selection self-defeating / split clear vs ambiguous) + P1.2 (tie-break ordering preregister) + P2 (count error 7 methods) |
| **R2 사전 (post-amendment)** | (예정) | amendment 정합 검증 |
| R3 사후 | (예정) | 결과 검수 / Phase 2 진입 권고 결정 |

**R1 amendment 반영 항목**:
1. **P1.1 fix (§2.3.1)**: cold cycle classification — clear negatives (D1-extended / D1.SC 반드시 FAIL) vs ambiguous (D1.X / D1.Y FAIL 또는 INCONCLUSIVE 허용) vs positive control (B 반드시 PASS)
2. **P1.2 fix (§2.3.2)**: tie-break ordering preregistered — (1) B PASS mandatory (2) clear-negative false positive 최소 (3) leave-one-seed-out CV 안정성 (4) simplest method wins ties
3. **P2 fix**: methods count 7 (전체 통일)
4. Q4 답변: framework recommendation 자체는 binding X / Phase 2 prospective preregister 필요

## 7. Phase 2 (post-VFR / 별도 prospective cycle 후보)

본 cycle 결과 따라 별도 prereg 작성:
- 새 framework preregister BEFORE running
- B (warm-only retune) on fresh seeds with NEW framework — positive control 검증
- D1 retune (or other axis) on fresh seeds with NEW framework — true test
- Decision binding only after Phase 2

본 VFR cycle은 Phase 2 framework selection의 hypothesis 제공.

## 8. 결론

VFR = **analysis-only / non-binding cycle**. Cold path 5 cycle fail vs warm path B 5/5 PASS 격차의 본질 규명. Existing per-seed delta data 위 noise/signal characterization + 7 aggregation methods 비교 + framework recommendation 도출.

**본 cycle 결과로 운영 채택 X / D1 결정 변경 X**. Phase 2 (별도 prospective preregister cycle / B positive control + fresh seeds)의 hypothesis 제공만.

**Compute**: ~2분 wall (numpy / scipy analysis on 5 JSON files / no training).
