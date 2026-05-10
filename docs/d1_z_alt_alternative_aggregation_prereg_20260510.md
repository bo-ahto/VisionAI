# D1.Z+alt: D1.Y Alternative Aggregation Analysis (R1 amendment / non-binding exploratory)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: D1.Y `d774938` HOLD_n32_default (7 PASS + 3 FAIL strict aggregate)
> **Decision binding**: ❌ **NO** (R1 amendment / Codex HOLD verdict 정합 / post hoc threshold shopping 회피)
> **Cycle type**: **Analysis-only / hypothesis-generating** (binding adoption 결정 X / 본 cycle 결과는 exploratory finding only)

## 1. Goal (R1 amendment / scope downgrade)

D1.Y N=10 strict aggregate FAIL → D1 axis 종결 확정. 본 cycle = **post hoc analysis / non-binding**:

- Strict aggregate (R1 P1.1 / FAIL × 2 이상 → FAIL): **FAIL** (D1.Y commit `d774938` 기록 / 본 cycle은 이 결정 변경 X)
- Population-level mean: 모든 cell 강한 negative (Δ_cold -1.16 / Δ_artsy -1.41 / Δ_saatchi -0.84 / Δ_warm -2.13)
- 30% bad-seed rate (3/10 strict G violation)

**Codex R1 HOLD 정합 (P0 + P1×2)**:
- P0: D1.Y에서 이미 champion-swap rule lock + FAIL → 같은 데이터 위 relaxed threshold + bootstrap은 threshold shopping
- P1.1: Bootstrap mean-CI는 strict guard 의도 (single bad split user impact 빈도)와 다른 object / mean-CI PASS는 ADOPT 발동 X
- P1.2: Combined decision table에 ADOPT 포함은 logically too permissive / cap best outcome at **INCONCLUSIVE / hypothesis-generating**

본 cycle 질문:
질문 1 (exploratory): G threshold 완화 (+0.3 → +0.8 / +1.0) 시 aggregate sensitivity (informative only)
질문 2 (exploratory): Bootstrap CI on mean Δ (population-level evidence / supplementary only)

**결과 활용 범위**:
- ✅ Hypothesis-generating: 본 결과 PASS 시 → 새 prospective cycle (fresh seeds + 새 threshold rule preregister) 정합
- ❌ Adoption decision: 본 결과만으로 운영 채택 X / D1.Y FAIL 결정 그대로 유지
- ❌ Threshold relaxation 자체 결정: 본 cycle scope 외 / 별도 amendment + new prospective cycle 필요

## 2. Method (재분석 only)

### 2.1 Input data

`model_test_results/d1_y_validation.json` + `d1_y_aggregate.json` (D1.Y commit `d774938` 산출):
- N=10 per-seed deltas: cold_overall / cold_artsy / cold_saatchi / warm
- Default + retuned base predictions (운영 정합 측정 가능)

새 training / Optuna search / model 생성 X. 순수 aggregation method 변경.

### 2.2 D1.Z: G threshold sensitivity (relaxed threshold)

**현행 strict (R1)**: G2 (artsy +0.3) / G3 (saatchi +0.3) / G4 (warm +0.1) / G1 (cold ≤0)

**Tier 1 (lax-1)**: G2/G3 +0.3 → **+0.8** / G1/G4 그대로
**Tier 2 (lax-2)**: G2/G3 +0.3 → **+1.0** / G1/G4 그대로

각 tier별 N=10 verdict 재산출 + R1 P1.1 amendment aggregate (FAIL × 2 이상 → FAIL).

**근거**:
- artsy_gallery cell n_holdout 150-250 / heavy-tailed → strict +0.3 strict 한계
- D1 prereg R7 amendment에서 G2/G3 +0.8/+1.0 검토됨 (D1.X seed=113 outlier 분석 시)
- D1.Y에서 single-FAIL outlier patterns: 113 G2 +1.76 / 313 G3 +0.61 / 367 G3 +1.42

### 2.3 D1.alt: Bootstrap CI on mean Δ

**Method**:
- N=10 per-seed delta 위에서 paired bootstrap resampling
- Resample N=10 with replacement / bootstrap_iters = 5000
- Compute mean Δ per cell on each bootstrap sample
- Report: mean / std / 95% CI (2.5% / 97.5% percentile)

**Decision rule (R1 검수 시 확정)**:

**Per-cell criterion**:
- **CI upper bound ≤ 0** → cell-level PASS (95% confidence population mean 음수 / 운영 시 95% confident 개선)
- **CI upper bound ∈ (0, +0.5]** → cell-level INCONCLUSIVE (mean 음수 가능성 높음 / single seed variance)
- **CI upper bound > +0.5** → cell-level FAIL

**Joint criterion (모든 4 cell)**:
- All cells PASS → **bootstrap_PASS** (새 prospective cycle 가설 후보 / non-binding / 본 cycle 결과만으로 운영 채택 X)
- 1+ cells INCONCLUSIVE / 0 FAIL → **bootstrap_PASS_with_caveat**
- 1+ cells FAIL → **bootstrap_FAIL**

### 2.4 Decision (R1 amendment / non-binding cap)

**R1 P1.2 fix**: 본 cycle 결과는 binding adoption 발동 X / best possible outcome **INCONCLUSIVE / hypothesis-generating**:

| D1.Z relaxed (+0.8 / +1.0) | D1.alt bootstrap (hierarchical primary cold_overall) | Combined exploratory finding |
|---|---|---|
| PASS at +0.8 OR +1.0 | bootstrap cold_overall CI upper ≤ 0 | **HYPOTHESIS_GENERATING_for_relaxed_cycle** — 새 prospective cycle (fresh seeds + threshold relax preregister) 권고 |
| FAIL at +0.8 AND +1.0 | bootstrap CI > 0 | **D1 axis terminate confirmed** — strict + relaxed + statistical 모두 fail |
| 기타 | 기타 | **EXPLORATORY_INCONCLUSIVE** — 추가 분석 가치 검토 |

**중요 (R1 P0 / P1.1)**:
- 본 cycle 자체는 **운영 채택 발동 X**
- D1.Y commit `d774938` HOLD_n32_default 결정 그대로 유지
- 결과 PASS 시 → 새 cycle prereg + fresh seeds 권고 (post hoc 회피)
- Bootstrap CI는 **supplementary** evidence only / strict guards가 binding 우선

### 2.5 Hierarchical bootstrap interpretation (R1 Q3)

R1 답변: 4/4 multiple-testing-adjusted PASS 요구 X / hierarchical:

- **Primary** (cold_overall mean Δ CI): bootstrap 평가 대상
- **Secondary guards** (artsy / saatchi / warm CI): record only / 강한 conflict 시만 flag

→ 본 cycle bootstrap interpretation은 cold_overall에 집중 / 다른 cell은 sanity record.

## 3. Output

- `docs/d1_z_alt_alternative_aggregation_prereg_20260510.md` (본 문서)
- `docs/d1_z_alt_alternative_aggregation_results_20260510.md`
- `scripts/d1_z_alt_reanalysis.py` (D1.Y json load + threshold sensitivity + bootstrap CI)
- (gitignored) `model_test_results/d1_z_alt_results.json` (per-tier aggregate + bootstrap CI)

## 4. Out-of-scope

- ❌ 새 training / Optuna search (D1.Y per-seed 결과 그대로 사용)
- ❌ Threshold 자체 결정-binding amendment (본 cycle = sensitivity analysis / 채택 결정 시 codex 자문)
- ❌ Validation seed 추가 / N>10 확장 (별도 cycle)

## 5. 한계 / Risk

- **Threshold 완화는 strict champion swap 의도와 충돌**: +0.3 → +0.8/1.0은 single seed에서 +0.5pp까지 regression 허용 / 운영 trust 약화 가능. 단 D1.X / D1.Y 모두 mean 강한 negative라 trade-off 합리.
- **Bootstrap N=10 resample**: small sample / CI95 estimate variance 큼 / 단 directional signal 충분.
- **Multiple testing**: 4 cell × 2 threshold tier × bootstrap = 다수 hypothesis / Bonferroni 등 검토 필요 (R1 검수 시).
- **본 cycle 결과 자체로 운영 채택은 신중**: relaxed threshold + bootstrap PASS여도 strict R1 framework와 conflict / R7 amendment 정합 별도 PR 필요할 수 있음.

## 6. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전 (2026-05-10)** | **HOLD** | P0 (post hoc threshold shopping) + P1.1 (bootstrap ≠ guard 의도) + P1.2 (decision table 너무 permissive) — Concrete fix: analysis-only / non-binding / cap at INCONCLUSIVE |
| **R2 사전 (post-amendment)** | (예정) | scope downgrade 정합 검증 |
| R3 사후 | (예정) | exploratory 결과 검수 |

**R1 amendment 반영 항목**:
1. **Decision binding ❌ NO** (heading 변경)
2. **Cycle type = analysis-only / hypothesis-generating** 명시
3. **Best outcome cap = INCONCLUSIVE / hypothesis-generating** (ADOPT / ADOPT_canary 옵션 제거)
4. **Bootstrap = supplementary** only (Q1 c 답변)
5. **Hierarchical interpretation** (Q3 / cold_overall primary / others guards)
6. **Result PASS 시 = 새 prospective cycle 권고** (Q6 / fresh seeds + amendment)
7. **PR-WARM-B와 deployment conflict** (Q7) 인정 — D1 retuned warm vs B-retuned warm 다름

## 7. 결론

D1.Z+alt = **D1.Y 재분석 cycle / analysis-only / non-binding** (training 없음). G threshold sensitivity + Bootstrap CI 두 lens로 D1 strict aggregate FAIL 결과 재해석. PASS 시 = 새 prospective cycle 가설 후보 (fresh seeds + threshold relax preregister 권고 / non-binding) / FAIL 시 D1 axis 종결 확정. **본 cycle 결과 자체로 운영 채택 발동 X**.

**Compute**: ~1분 wall (json load + numpy bootstrap).
