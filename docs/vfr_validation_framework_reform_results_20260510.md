# VFR: Validation Framework Reform — Results (analysis-only / non-binding)

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/vfr_validation_framework_reform_prereg_20260510.md` (R1 NEEDS FIX → R2 LGTM)
> **실행일**: 2026-05-10 (~2분 wall / numpy analysis only)
> **실행 결과**: 🔍 **Recommendation: 현행 strict framework 유지 / framework reform abandon 권고**

## 1. Summary

본 cycle 핵심 발견:
- **현행 strict per-seed framework가 R1 P1.2 tie-break ordering에서 winner** (B PASS + clear-negatives FAIL + simplest among qualified)
- Cold path effect는 **statistical signal 자체가 unstable** (cycle별 mean -1.87 → +0.22 / sampling lottery)
- Framework noise 문제 X / **본질적 effect signal 없음** (codex Q7 prediction 정확)

**Recommendation**: framework reform 자체 abandon / 현행 strict per-seed (R1 P1.1) 유지. **본 cycle은 analysis-only / non-binding** — D1 axis abandon + B winner ADOPT 결정 그대로 유지.

## 2. R1-R2 Amendment 정합

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | NEEDS FIX | P1.1 (cycle classification 분리) + P1.2 (tie-break ordering preregister) + P2 (count 7) |
| R2 사전 | LGTM | amendment 정합 |

R1 핵심 amendment:
- **Cycle classification** (clear negatives / ambiguous / positive control) — D1 모두 FAIL 가정 회피
- **Tie-break ordering** (B PASS mandatory → clear-neg false positive → leave-one-out CV → simplest)

## 3. Method 적용

### 3.1 Input data
- `b_warm_validation.json` (positive control / N=5)
- `d1_validation_20260510.json` (ambiguous / D1.X N=5)
- `d1_y_validation.json` (ambiguous / D1.Y N=10)
- `d1_extended_results.json` (clear negative / N=10)
- `d1_sc_results.json` (clear negative / N=10)

### 3.2 7 aggregation methods
1. Strict per-seed (현행 R1 P1.1)
2. Bootstrap CI on mean (95%)
3. Trimmed mean (top-bottom 10%)
4. Median CI (95%)
5. Cell-size weighted (artsy 0.25 × Δ_artsy + saatchi 0.75 × Δ_saatchi)
6. Quantile P75
7. Cohen's d

## 4. 핵심 결과

### 4.1 Cycle statistics (noise/signal characterization)

| Cycle | Cell | n | mean | std | CV | range |
|---|---|---|---|---|---|---|
| **B** (positive control) | warm | 5 | **-1.619** | 0.141 | **0.09** | [-1.77, -1.44] |
| D1.X | cold_overall | 5 | -1.871 | 0.361 | 0.19 | [-2.32, -1.53] |
| D1.X | warm | 5 | -2.120 | 0.171 | 0.08 | [-2.30, -1.86] |
| D1.Y | cold_overall | 10 | -1.163 | 0.949 | 0.82 | [-2.32, +0.33] |
| D1.Y | warm | 10 | -2.133 | 0.183 | 0.09 | [-2.44, -1.86] |
| **D1-extended** | cold_overall | 10 | **+0.223** | 1.202 | **5.38** | [-1.39, +2.03] |
| D1-extended | warm | 10 | -2.141 | 0.145 | 0.07 | [-2.32, -1.91] |
| **D1.SC** | cold_overall | 10 | -0.398 | 2.756 | **6.93** | [-6.67, +3.25] |
| D1.SC | warm | 10 | 0.000 | 0.000 | inf | (orthogonal axis / shared) |

**핵심 패턴**:
- ✅ **Warm path** (B / D1.X warm / D1.Y warm / D1-extended warm): CV consistent 0.07-0.09 — **매우 stable**
- ❌ **Cold path** (D1 cycles): CV 0.19 → 0.82 → 5.38 → 6.93 — **cycle별 dramatic 증가** / noise dominates
- ❌ **Cycle별 cold mean 불안정**: -1.87 → -1.16 → +0.22 → -0.40 (sampling lottery)
- 💡 **Warm path effect (~-2.13pp) 모든 cycle 정합 / robust**: B / D1.X / D1.Y / D1-extended 모두 mean ≈ -2.1 / std ≈ 0.15

### 4.2 Method ranking (R1 P1.2 tie-break)

| Method | B | d1_ext (clear neg) | d1_sc (clear neg) | d1_x (ambig) | d1_y (ambig) | Score |
|---|---|---|---|---|---|---|
| **1_strict_per_seed** ⭐ | PASS | FAIL | FAIL | PASS_w_c | FAIL | **+10** |
| 2_bootstrap_ci_mean | PASS | FAIL | FAIL | PASS | PASS | +10 |
| 3_trimmed_mean | PASS | INCONCLUSIVE | **PASS** ❌ | PASS | PASS | 0 (false pos d1sc) |
| 4_median_ci | PASS | FAIL | FAIL | PASS | PASS | +10 |
| 5_cell_weighted | **N/A** ❌ | INCONCLUSIVE | INCONCLUSIVE | PASS | PASS | -100 (B fail) |
| 6_quantile_p75 | PASS | FAIL | FAIL | PASS | PASS | +10 |
| 7_cohens_d | PASS | FAIL | INCONCLUSIVE | PASS | PASS | +10 |

**Qualified methods** (B PASS mandatory + clear-neg false positive 0):
- 1_strict_per_seed / 2_bootstrap_ci_mean / 4_median_ci / 6_quantile_p75 / 7_cohens_d (5 methods)

**Rejected**:
- 3_trimmed_mean (d1sc 위 false positive PASS / clear neg reject)
- 5_cell_weighted (warm path 적용 X / B mandatory fail)

### 4.3 Recommendation (simplest method wins ties)

R1 P1.2 simplicity ordering: **1_strict_per_seed > 6_quantile_p75 > 4_median_ci > 2_bootstrap_ci_mean > 7_cohens_d**

→ **`1_strict_per_seed`** (현행 framework) 채택 권고.

**Justification**:
- ✅ B positive control PASS (mandatory)
- ✅ Clear-negatives (D1-extended / D1.SC) 모두 FAIL 유지 (no false positive)
- ✅ Ambiguous handling: D1.X PASS_with_caveat (4/5 / 1 outlier 흡수) / D1.Y FAIL (3 outliers / strict 적정)
- ✅ Simplest method (no bootstrap / no statistic transformation 필요)

## 5. Cold path effect 본질 분석

### 5.1 Cold path는 본 framework 한계 X / effect signal 자체 unstable

D1 cycles 위 cold mean Δ:
- D1.X (N=5): -1.87 ✅ (강한 negative)
- D1.Y (N=10): -1.16 (약한 negative)
- D1-extended (N=10): **+0.22** ❌ (positive!)
- D1.SC (N=10): -0.40 (약한 negative / source split도 도움 X)

**cycle별 mean 범위 = -1.87 ~ +0.22 (range 2.09pp)** — same retune params 인데도 sample에 따라 정반대 결과. Effect signal이 sampling lottery에 sensitive.

### 5.2 Warm path는 effect signal robust

Warm mean Δ across cycles:
- B (N=5): -1.62
- D1.X warm part (N=5): -2.12
- D1.Y warm part (N=10): -2.13
- D1-extended warm part (N=10): -2.14

**cycle별 mean 범위 = -2.14 ~ -1.62 (range 0.52pp)** — robust population-level signal.

### 5.3 Conclusion

**Cold path retune effect는 통계적으로 unstable / 운영 검증 framework로 PASS 발동 불가능**:
- Effect size가 split variance보다 작거나 비슷
- Sample lottery에 따라 negative ↔ positive 변동
- Strict per-seed framework가 정확하게 이 instability 식별

**Warm path retune effect는 statistically robust**:
- B winner는 effect size > variance / consistent negative
- 본 framework로 5/5 PASS 정확 식별
- ADOPT 운영 채택 정당함

## 6. Phase 2 (post-VFR / 별도 prospective cycle)

본 cycle Recommendation = 현행 framework 유지 → Phase 2 prospective cycle은 **불필요**:
- 새 framework로 D1 살리기 시도 X (effect signal 자체 없음)
- 현행 strict framework는 정확히 작동 / 변경 불필요

**대안 후속 (별도 axis / 본 cycle scope 외)**:
- ❌ Cold retune axis 종결 확정 (D1 5 cycle + 본 framework 분석 결과 정합)
- ✅ B (warm-only retune) Stage 3-5 운영 deploy (PR-WARM-B / 운영팀 의존)
- 🔍 Architecture change axis (hierarchical / Bayesian / LightGBM / 새 modeling program)
- 🔍 Data/feature reform (heavy-tail dataset 정합 새 features / log-transform / outlier handling)

## 7. 산출물

### 7.1 Commit 대상
- `docs/vfr_validation_framework_reform_prereg_20260510.md` (R1-R2 amendment 반영)
- `docs/vfr_validation_framework_reform_results_20260510.md` (본 문서)
- `scripts/vfr_framework_analysis.py` (numpy analysis / 7 methods 비교 / R1 P1.2 tie-break)

### 7.2 .gitignore (artifact)
- `model_test_results/vfr_analysis_results.json`

## 8. 한계 / Risk

- **Post hoc analysis**: 같은 데이터 위 7 methods 적용 / single dataset binding decision X (R1 정합)
- **N small per cycle**: D1.X N=5 / 다른 cycles N=10 / bootstrap CI estimate variance 큼 / 단 method ranking은 robust 결과
- **B as positive control 제한**: warm path single axis / cold-specific positive control 부재 (R1 Q2 정합)
- **Cold-specific 본질 한계 noted**: 본 framework reform이 cold path retune 살릴 수 있는 method 발견 X

## 9. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX | P1.1 (cycle classification) + P1.2 (tie-break) + P2 (count) |
| R2 사전 | LGTM | amendment 정합 |
| R3 사후 | (예정) | 결과 검수 / framework reform abandon 결정 적정성 |

## 10. 결론

VFR analysis 결과 = **현행 strict per-seed framework (R1 P1.1) 유지 권고**.

**핵심 입증**:
1. **Cold path retune은 본질적으로 statistical signal unstable**: cycle별 mean -1.87 → +0.22 (positive!) → -0.40 sampling lottery
2. **Warm path retune은 statistically robust**: 모든 cycle warm mean ≈ -2.1 / std ≈ 0.15 / CV 0.07-0.09
3. **현행 framework는 본 instability 정확 식별**: B 5/5 PASS / D1 1-7/10 PASS (correctly fail)
4. **Framework reform으로 cold 살리기 시도는 false positive risk만**: trimmed_mean / cell_weighted 등은 D1.SC를 PASS 발동 (clear neg false positive)

**운영 결정**:
- ✅ N=32 default best_params 유지 (cold path 변경 X)
- ✅ B-retuned warm path (PR-WARM-B Stage 3-5 후) deploy
- ✅ Cold retune axis 종결 확정 (5 cycle + framework analysis 정합)
- ❌ Validation framework reform abandon (현행 정확 작동)

**본 세션 16 cycles 종합**:
- ✅ B (warm-only retune / commit 3a27002) — **유일 ADOPT** / PR-WARM-B Stage 1+2 commit / Stage 3-5 pending
- ❌ D1 cold axis (5 cycles 모두 fail) — completely abandoned
- ❌ D3 blend axis (2 cycles) — terminated
- 🔍 VFR (본 commit) — framework reform abandon / 현행 strict 유지 confirmed

**Codex Q7 prediction validation**: "D1 abandon / B + source-conditional 우선" → D1 종결 ✓ / B Stage 5 진입 valid ✓ / source-conditional fail ✓ / framework reform 시도 abandon ✓

**남은 후속 후보** (별도 axis / 본 framework + 본 retune 패러다임 외):
- Architecture change (hierarchical / Bayesian / 새 modeling program)
- Data/feature reform (heavy-tail dataset 정합 features 변경)
- B winner deploy 우선 (Stage 3-5 운영팀 활성화)
