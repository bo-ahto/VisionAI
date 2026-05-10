# D1.Z+alt: D1.Y Alternative Aggregation Analysis — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_z_alt_alternative_aggregation_prereg_20260510.md` (R1 HOLD → R2 NEEDS FIX → R3 LGTM)
> **실행일**: 2026-05-10 (~1분 wall / numpy reanalysis)
> **실행 결과**: 🔍 **HYPOTHESIS_GENERATING_for_relaxed_cycle** (analysis-only / non-binding)
> **Decision binding**: ❌ **NO** — D1.Y commit `d774938` HOLD_n32_default 결정 그대로 유지

## 1. Summary

D1.Y N=10 strict aggregate FAIL 후 같은 데이터 위 alternative aggregation 재분석 (analysis-only / R1 HOLD verdict 정합 / post hoc threshold shopping 회피):

- **D1.Z (threshold sensitivity)**: strict +0.3 / lax-1 +0.8 / lax-2 +1.0 모두 **FAIL** — threshold relaxation 단독으로 D1.Y outlier 흡수 X
- **D1.alt (bootstrap CI / hierarchical)**: cold_overall primary **PASS** (CI95 upper -0.60) — population-level negative 95% confident
- **Combined finding**: HYPOTHESIS_GENERATING_for_relaxed_cycle — 새 prospective cycle (fresh seeds + 새 rule preregister) 가설 후보 / **본 cycle 결과만으로 운영 채택 X**

## 2. R1-R3 Amendment 정합

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | HOLD (P0 + P1×2) | post hoc shopping / bootstrap ≠ guard / decision table 너무 permissive |
| R2 사전 | NEEDS FIX (2 stale lines) | "운영 채택 후보" 표현 정정 |
| R3 사전 | LGTM | analysis-only / non-binding 정합 |

## 3. Method (실행)

### 3.1 Input
- `model_test_results/d1_y_validation.json` (D1.Y commit `d774938` 산출 / 10 seed × 4 cell deltas)

### 3.2 D1.Z: Threshold sensitivity
- 3 tiers: strict (+0.3) / lax-1 (+0.8) / lax-2 (+1.0)
- G1 (cold ≤0) / G4 (warm ≤0.1) 모두 strict 그대로 / G2 / G3만 변동
- N=10 verdict 재산출 + R1 P1.1 strict aggregate (FAIL × 2 이상 → FAIL)

### 3.3 D1.alt: Bootstrap CI
- Paired percentile bootstrap on per-seed deltas
- n_boot = 5000 / random_state = 42 / 95% CI percentile method
- Per-cell mean Δ + CI95 lower / upper

### 3.4 Hierarchical interpretation (R1 Q3)
- Primary: cold_overall mean Δ CI upper ≤ 0 → PASS / (0, 0.5] → INCONCLUSIVE / >0.5 → FAIL
- Secondary: artsy / saatchi / warm CI upper > 0.5 → guard concern flag (단 PASS 차단 X)

## 4. 결과

### 4.1 D1.Z (threshold sensitivity)

| Tier | G2 / G3 | PASS | INC | FAIL | Aggregate |
|---|---|---|---|---|---|
| strict (R1 / D1.Y baseline) | +0.3 / +0.3 | 7 | 0 | 3 | **FAIL** |
| lax-1 (G2/G3 +0.8) | +0.8 / +0.8 | 8 | 0 | 2 | **FAIL** |
| lax-2 (G2/G3 +1.0) | +1.0 / +1.0 | 8 | 0 | 2 | **FAIL** |

**Per-seed verdict 변화** (lax-1 +0.8 기준):
| seed | strict | lax-1 (+0.8) | 차이 / 잔존 violation |
|---|---|---|---|
| 97 | PASS | PASS | — |
| 113 | FAIL | **FAIL** | G2 artsy +1.76 (>+0.8 / strong outlier) |
| 199 | PASS | PASS | — |
| 223 | PASS | PASS | — |
| 257 | PASS | PASS | — |
| 313 | FAIL | **PASS** | G3 saatchi +0.61 (≤ +0.8) → 흡수 |
| 367 | FAIL | **FAIL** | G1 cold_overall +0.33 + G3 saatchi +1.42 (둘 다 잔존) |
| 439 | PASS | PASS | — |
| 491 | PASS | PASS | — |
| 587 | PASS | PASS | — |

**핵심**: threshold +0.3 → +0.8 변경 시 seed=313만 흡수 (1 FAIL → PASS). seed=113 (artsy +1.76) + seed=367 (G1 +0.33 + saatchi +1.42)는 **strong outlier로 어떤 lax threshold (+0.8 / +1.0) 에서도 잔존**.

→ **G threshold 단독 완화로 D1 axis 못 살림** (R1 P1.2 정합 / threshold shopping 효과 한계).

### 4.2 D1.alt (Bootstrap CI 95%)

| Cell | mean | std | n | CI95 lower | CI95 upper | Status |
|---|---|---|---|---|---|---|
| delta_cold_overall | **-1.163** | 0.949 | 10 | -1.709 | **-0.595** | ✅ CI upper ≤ 0 |
| delta_cold_artsy | **-1.406** | 1.335 | 10 | -2.075 | -0.552 | ✅ CI upper ≤ 0 |
| delta_cold_saatchi | -0.636 | 1.204 | 10 | -1.324 | +0.093 | ⚠️ CI includes 0 |
| delta_warm | **-2.133** | 0.183 | 10 | -2.241 | **-2.027** | ✅ CI upper ≤ 0 (강력) |

### 4.3 Hierarchical interpretation

| 항목 | 값 |
|---|---|
| Primary metric | `delta_cold_overall` |
| Primary CI upper | **-0.595** |
| Primary status | **PASS** (95% confident population mean negative) |
| Secondary guard flags | none (any cell CI upper > 0.5) |

**해석**:
- cold_overall: 95% confidence interval 전체 negative ([-1.71, -0.60]) → **population-level cold improvement statistical significant**
- delta_warm: CI 매우 좁음 [-2.24, -2.03] / 5/10 standard error 작음 / **모든 holdout split에서 일관 -2pp 개선** (cycle B와 정합)
- artsy: CI95 upper -0.55 / population mean negative confident
- saatchi: CI95 upper +0.09 (0 포함) / **directional 부정확** / mean -0.64는 negative이지만 statistical significance 부족 (split variance 큼)

### 4.4 Combined Exploratory Finding

**HYPOTHESIS_GENERATING_for_relaxed_cycle**:

근거:
- Bootstrap cold_overall PASS (statistical evidence 강함)
- Threshold relaxation 단독은 fail이지만 lax-1 +0.8에서 1 FAIL 흡수 (313 → PASS) 발견 → strong outlier (113, 367) 외에는 split variance 흡수 가능 시그널
- 모든 cell mean Δ 음수 (saatchi CI 0 포함이지만 mean -0.64)

**그러나 본 cycle 결과만으로 운영 채택 X** (R1 P0/P1.2 정합):
- Same data 재분석 / threshold shopping 회피
- Bootstrap mean-CI ≠ strict guard 의도 (single bad split user impact 빈도)
- 31% (3/10) bad-seed rate는 strict champion swap에 부적합

**후속 권고** (별도 prereg):
- **D1.Z2 (relaxed amendment + fresh seeds)**: 새 5-10 fresh seeds + lax-1 (+0.8) threshold rule preregister + run / 본 cycle은 hypothesis 제공만
- **D1.split (per-source separate cycles)**: artsy / saatchi outlier 각각 별도 분석 (artsy heavy-tailed / saatchi tail behavior)
- **D1.alt2 (bootstrap-based prereg)**: bootstrap CI를 primary endpoint로 preregister 새 cycle (mean evidence 기반 결정)

## 5. 산출물

### 5.1 Commit 대상

- `docs/d1_z_alt_alternative_aggregation_prereg_20260510.md` (R1-R3 amendment 반영 / non-binding scope)
- `docs/d1_z_alt_alternative_aggregation_results_20260510.md` (본 문서)
- `scripts/d1_z_alt_reanalysis.py` (numpy reanalysis / training 없음)

### 5.2 .gitignore (artifact)

- `model_test_results/d1_z_alt_results.json` (per-tier aggregate + bootstrap CI 상세)

## 6. 한계 / Risk (R1 정합)

- **Post hoc analysis**: 같은 데이터 재해석 / 새 evidence 아님 / 본 cycle 결과로 채택 결정 X (R1 P0).
- **Bootstrap N=10 small**: CI95 estimate 자체 variance 큼 / 단 directional signal robust.
- **Strict guards remain operationally binding**: champion swap 의도는 single-split bad outcome 회피 / mean-CI는 그 의도 충족 X (R1 P1.1).
- **Multiple testing**: 4 cell × 3 threshold tier = 다수 hypothesis / Bonferroni 미적용 / hierarchical로 우회 (R1 P1.2 정합).

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | HOLD | P0 (post hoc shopping) + P1×2 / scope downgrade 권고 |
| R2 사전 | NEEDS FIX | "운영 채택 후보" stale 문구 2 line 정정 |
| R3 사전 | LGTM | analysis-only 진입 ready |
| R4 사후 | (예정) | finding 검수 / 후속 cycle 권고 결정 |

## 8. 결론

D1.Z+alt = **analysis-only / hypothesis-generating**. 결과:
- D1.Y strict aggregate FAIL 결정 그대로 유지 (commit `d774938`)
- Threshold relaxation 단독 efficacy 작음 (strong outlier 잔존)
- Bootstrap cold_overall 95% confident negative (statistical evidence 강함)
- saatchi CI 0 포함 (split variance 큼 / directional 부정확)

**후속 권고** (별도 prereg / 본 cycle scope 외):
1. D1.Z2 (relaxed amendment + fresh seeds preregister)
2. D1.split (per-source separate analysis)
3. D1.alt2 (bootstrap-based decision rule prereg)

본 commit 시점 = D1 axis 종결 그대로 / PR-WARM-B Stage 3-5 진행 시 user impact 시작 (warm path 단독 / B winner / cold path 미변경).

**본 세션 종합 (12+1 cycles 종결)**:
- ✅ B (warm-only retune) — 유일 ADOPT (PR-WARM-B Stage 1+2 commit / Stage 3-5 pending)
- ❌ D1.X / D1.Y / D1.Z+alt — D1 axis 종결 (strict + relaxed + bootstrap 모두 FAIL or non-binding)
- ❌ D3 / D3.B — blend axis 종결
- 🔍 D1.Z+alt finding = 후속 별도 cycle 가설만 (본 cycle 자체는 운영 채택 발동 X)
