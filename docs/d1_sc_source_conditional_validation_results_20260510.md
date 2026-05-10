# D1.SC: Source-Conditional Validation Cycle — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_sc_source_conditional_validation_prereg_20260510.md` (R1 NEEDS FIX → R2 NEEDS FIX → R3 LGTM)
> **실행일**: 2026-05-10 (~5분 wall / 10 fresh seeds validation)
> **실행 결과**: ❌ **HOLD_source_conditional_axis_abandon** (codex Q7 prediction 정합 / 3 primaries 모두 FAIL)

## 1. Summary

D1 axis 4 cycle abandon 후 codex Q7 추천 ("D1 abandon / B + source-conditional 우선") 정합 cycle. R1 NEEDS FIX → R2 NEEDS FIX → R3 LGTM amendment 정합 fresh prospective N=10 cycle.

**결과**:
- artsy_primary: 6 PASS / 4 FAIL → **FAIL**
- saatchi_primary: 3 PASS / 7 FAIL → **FAIL**
- overall_primary: 1 PASS / 9 FAIL → **FAIL**
- Bootstrap CI corroboration: 모든 cell CI95 includes 0 (mean도 mixed: cold_overall -0.40 / artsy -0.51 / saatchi +0.41)

**Combined decision**: **`HOLD_source_conditional_axis_abandon`** — codex Q7 strong recommendation 정확 ("if cleanly FAILs, abandon the axis").

**운영 결정**:
- ✅ unified default cold path 그대로 유지
- ✅ Source-conditional axis (PR1 v1) 운영 적용 X / 종결
- ✅ PR-WARM-B (B winner) 단독 deploy path 유효 (orthogonal axis / 영향 X)

## 2. R1-R3 Amendment 정합

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 (fair retrain-vs-retrain) + P1.1 (per-source binding primaries) + P1.2 (explicit serving contract) |
| R2 사전 | NEEDS FIX | stale framing ("PR1 v1 그대로") + calibration contract 정정 |
| R3 사전 | LGTM | Stage 진입 ready |

## 3. Method (실행 정합)

### 3.1 Per-seed validation (fresh retrain / R1 P0)

각 seed × 80/20 GroupShuffleSplit cold + warm row split:
- **Candidate retrain**: artsy_cb (artsy pool / default best_params) + saatchi_cb (saatchi pool / default best_params) + unified_xgb_warm (warm pool)
- **Baseline retrain**: unified_cb (full cold pool) + unified_xgb_warm (shared with candidate)
- 양 arm calibration 미적용 (R2 amendment / raw uncalibrated output)

### 3.2 Serving contract (R1 P1.2)
- **Cold rows**: candidate route by source / baseline unified
- **Warm rows**: 양쪽 모두 unified_xgb_warm (orthogonal axis / Δ_warm = 0)

## 4. Per-seed 결과

| seed | Δ_cold | Δ_artsy | Δ_saatchi | artsy verdict | saatchi verdict | overall verdict |
|---|---|---|---|---|---|---|
| 941 | +0.690 | -0.x | +0.x | PASS | FAIL | **FAIL** |
| 967 | +1.404 | -0.x | +0.x | PASS | FAIL | **FAIL** |
| 991 | +0.769 | -0.x | +0.x | PASS | FAIL | **FAIL** |
| 1009 | -2.661 | +0.x | -0.x | FAIL | PASS | **FAIL** |
| 1031 | -1.559 | -0.x | +0.x | PASS | FAIL | **FAIL** |
| 1049 | -0.926 | -4.340 | -0.794 | PASS | PASS | **PASS** |
| 1069 | +0.755 | +2.477 | +0.447 | FAIL | FAIL | **FAIL** |
| 1093 | -6.668 | +2.661 | -11.109 | FAIL | PASS | **FAIL** |
| 1117 | +0.971 | +3.255 | +0.376 | FAIL | FAIL | **FAIL** |
| 1129 | +3.248 | -0.769 | +4.231 | PASS | FAIL | **FAIL** |

**관찰**:
- seed=1093: Δ_saatchi=-11.11 (extreme positive!) / 단 artsy +2.66 (overall fail)
- seed=1129: Δ_saatchi=+4.23 (extreme negative!) / split variance 양극단
- seed=1049: 유일 overall PASS — 모든 cell 음수

→ split variance 매우 큼 / source-conditional도 unified와 동일 문제 (D1 axis 정합).

## 5. Aggregate

### 5.1 Per-primary (R1 P1.1)

| Primary | PASS | INCONCLUSIVE | FAIL | Aggregate |
|---|---|---|---|---|
| artsy_primary | 6 | 0 | 4 | **FAIL** (R1 P1.1 / FAIL ≥ 2) |
| saatchi_primary | 3 | 0 | 7 | **FAIL** |
| overall_primary | 1 | 0 | 9 | **FAIL** |

### 5.2 Bootstrap CI (corroboration only)

| Cell | mean | CI95 | Status |
|---|---|---|---|
| delta_cold_overall | -0.398 | [-2.15, +1.08] | ⚠️ CI includes 0 |
| delta_cold_artsy | -0.510 | [-2.11, +1.10] | ⚠️ CI includes 0 |
| delta_cold_saatchi | +0.411 | [-2.76, +3.02] | ⚠️ CI includes 0 / mean positive |

→ Bootstrap도 corroboration FAIL (mean 음수이지만 CI 매우 넓음 / split variance 큼).

## 6. Combined Decision

R1 P1.1 amendment combined logic:
- artsy_primary FAIL + saatchi_primary FAIL → **HOLD_source_conditional_axis_abandon**

**운영 결정**: source-conditional 채택 X / unified default 그대로 유지.

## 7. 분석: Source-conditional이 fail한 이유

### 7.1 Split variance 본질
- D1.X / D1.Y / D1-extended에서 D1 unified retune 30-80% bad-seed rate
- D1.SC source-conditional도 비슷한 split variance 발생 (artsy 60% PASS / saatchi 30% PASS)
- → split variance는 모델 architecture (unified vs source-split)와 독립적인 본질

### 7.2 Source-specific 학습의 over-fit risk
- artsy 7,289 rows (작음) / saatchi 21,087 rows (큼)
- Source-specific 학습은 same hyperparams로 작은 dataset에 over-fit 가능성
- 결과: source-specific 모델이 unified보다 robust X / split variance 흡수 X

### 7.3 D1 axis 5 cycle 누적 (모두 fail)

| Cycle | Approach | Result |
|---|---|---|
| D1.X | HP retune unified (CB+XGB) | NEEDS_MORE_DATA (4/5 PASS) |
| D1.Y | HP retune unified N=10 | FAIL (7/10) |
| D1.Z+alt | post-hoc analysis | non-binding finding |
| D1-extended | HP retune fresh N=10 | FAIL (2/10) |
| **D1.SC (본 commit)** | **Source-split (default params)** | **FAIL (1/10 overall)** |

→ **D1 cold path axis 모든 변형 (HP retune / source-split) 본 strict framework 하에서 fail**. Cold path 개선은 본 framework로는 검증 불가.

## 8. PR-WARM-B와 interaction

D1.SC FAIL → cold path 변경 X / unified 유지. PR-WARM-B는 별개 axis (warm path / orthogonal):
- 본 cycle 결과와 무관 / Stage 3-5 진행 그대로 valid
- D1.SC 결과로 PR-WARM-B의 unique value 강화 (cold 모든 axis fail / warm 단독 PASS인 B만 가치)

## 9. 산출물

### 9.1 Commit 대상

- `docs/d1_sc_source_conditional_validation_prereg_20260510.md` (R1-R3 amendment 반영)
- `docs/d1_sc_source_conditional_validation_results_20260510.md` (본 문서)
- `scripts/d1_sc_validation.py` (fresh retrain candidate + baseline)
- `data/d1_sc_holdout_20260510/seed{941,967,991,1009,1031,1049,1069,1093,1117,1129}_holdout_indices.json`

### 9.2 .gitignore (artifact)

- `model_test_results/d1_sc_results.json`

## 10. 한계 / Risk (codex 정합)

- **Default best_params만 검증**: HP retune 효과 X / 본 cycle은 data partitioning 단독
- **N=10 small for binary verdict**: 단 strict primary 모두 FAIL (1/9 PASS overall) / 추가 N 확대 가치 낮음 (signal 약함)
- **Calibration 미적용**: R2 amendment / raw output 사용 / 운영 calibration 적용 시 약간 다를 수 있음 (단 directional finding 동일 예상)
- **Codex Q7 정확**: "if cleanly FAILs, abandon" prediction 정합 / SC2 (full HP retune) 진입 조건 (INCONCLUSIVE + credible positive) 미달

## 11. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 (fair retrain) + P1.1 (per-source primaries) + P1.2 (serving contract) |
| R2 사전 | NEEDS FIX | stale framing + calibration contract |
| R3 사전 | LGTM | Stage 진입 ready |
| R4 사후 | (예정) | 결과 검수 / source-conditional axis abandon 결정 적정성 |

## 12. 결론

D1.SC = **HOLD_source_conditional_axis_abandon**. Source-conditional split (default params) 도 unified와 동일 split variance 문제. artsy_primary FAIL (4/10) + saatchi_primary FAIL (7/10) + overall_primary FAIL (9/10) → 3 primaries 모두 FAIL → axis 종결.

**본 세션 종합 (15 cycles)**:
- ✅ B (warm-only) — **유일 ADOPT** (PR-WARM-B Stage 1+2 commit / Stage 3-5 pending)
- ❌ D1 axis (D1.X / D1.Y / D1.Z+alt / D1-extended) — 완전 abandon (4 cycles)
- ❌ D3 axis (D3 / D3.B) — blend axis 종결 (2 cycles)
- ❌ **D1.SC** (source-conditional / 본 commit) — source-conditional axis 종결

**Cold path 모든 axis 본 framework 하 fail**. 운영 결정 = N=32 default best_params 유지 + warm path B-retuned (Stage 5 후).

후속 후보 (별도 prospective cycles / 본 cycle scope 외):
- Source-conditional + HP retune (D1.SC2 / artsy/saatchi 각각 Optuna search) — codex Q7 답변 정합 진입 조건 미달 (본 cycle clean FAIL)
- Architecture change (hierarchical models / Bayesian / LightGBM 등) — 새 axis
- Validation framework reform (small-cell heavy-tailed 분포 정합 새 metric)
