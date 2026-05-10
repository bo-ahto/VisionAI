# D1-extended: D1.Z2 + D1.split + D1.alt2 Combined Prospective Cycle — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_extended_prospective_prereg_20260510.md` (R1 HOLD → R2 NEEDS FIX → R3 LGTM amendment)
> **실행일**: 2026-05-10 (~10분 wall / 10 fresh seeds validation)
> **실행 결과**: ❌ **HOLD_D1_axis_abandon** (codex Q7 strong recommendation 정합 / 극적 reversal)

## 1. Summary

D1.Y N=10 strict aggregate FAIL → D1.Z+alt analysis-only finding (bootstrap CI cold_overall mean=-1.16 PASS) → **본 cycle fresh N=10 prospective validation 결과 정반대** (mean=+0.22 / CI95 [-0.48, +0.91] / 80% bad-seed rate).

**Codex R1 HOLD verdict (Q7 D1 axis abandon recommendation) 정확**:
- D1.Y N=10이 실제 population 비대표 (outlier-heavy lucky sample)
- D1 retuned params는 split variance에 fundamentally sensitive
- Bootstrap CI on small N=10이 fresh sample에서 정반대 결과 가능 (codex P0/P1.1 warning 검증)

**Combined decision (R1 amendment 정합)**:
- Strict primary FAIL → 무조건 HOLD (R1 P0)
- Bootstrap secondary FAIL (cold_overall CI95 upper +0.91 > 0)
- Lax-1 FAIL (canary 최소 조건 미달)
- → **HOLD_D1_axis_abandon**

**D1 axis 완전 종결 확정**. 운영 N=32 best_params 그대로 유지. PR-WARM-B (warm-only ADOPT)는 별개 axis / 영향 X.

## 2. R1-R3 Amendment 정합

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | HOLD | P0 (strict primary 유지) + P1.1 (N=5 → N=10) + P1.2 (canary lax-1 minimum) + Q7 (D1 abandon recommendation) |
| R2 사전 | NEEDS FIX (stale text) | §5 / §8 stale "N=5" / "bootstrap primary" 정정 |
| R3 사전 | LGTM | Stage 진입 ready |

## 3. Method (실행)

### 3.1 Fresh seeds
N=10: {631, 661, 691, 727, 757, 787, 821, 853, 877, 907} — 모두 prime / 이전 cycle (D1.X / D1.Y / B / D3 / D3.B / N15) 비중복.

### 3.2 Endpoints
- **Primary (binding / R1 P0)**: D1.Y rule strict per-seed aggregate
- **Secondary corroboration (not binding alone / R1 P0)**: bootstrap CI cold_overall hierarchical
- **Tertiary record (R1 P1.2)**: lax-1 (+0.8) / lax-2 (+1.0) threshold sensitivity
- **Tertiary informational**: per-source decomposition (artsy / saatchi)

### 3.3 Compute
- 10 seeds × ~50s = ~10분 wall (D1 retuned params 재사용 / search 없음)
- D1 retuned params: `n32_champion_retuned_best_params.json` (commit `d06ea22`)

## 4. Per-seed 결과

| seed | Δ_cold | Δ_artsy | Δ_saatchi | Δ_warm | strict verdict |
|---|---|---|---|---|---|
| 631 | (확인 필요 / json 참조) | | | | |

(상세 per-seed deltas는 `model_test_results/d1_extended_results.json` 참조 / gitignored)

**핵심 분포** (log 요약):
- 8 FAIL / 2 PASS (strict)
- 7 FAIL / 3 PASS (lax-1 +0.8) — 1 seed만 흡수
- 7 FAIL / 3 PASS (lax-2 +1.0) — 추가 흡수 X (strong outlier 존재)

특히 seed=907: Δ_cold=+0.918 / Δ_saatchi=+0.367 — 강한 cold regression.

## 5. Aggregate 결과

### 5.1 Strict primary (D1.Y rule)

| Tier | PASS | INCONCLUSIVE | FAIL | Aggregate |
|---|---|---|---|---|
| **strict (Primary)** | 2 | 0 | **8** | **FAIL** |
| lax-1 (+0.8) | 3 | 0 | 7 | FAIL |
| lax-2 (+1.0) | 3 | 0 | 7 | FAIL |

**80% bad-seed rate** — D1.Y의 30%보다 훨씬 높음. D1.Y가 outlier-heavy lucky sample이었음 입증.

### 5.2 Bootstrap CI secondary (corroboration)

| Cell | mean | CI95 lower | CI95 upper | Status |
|---|---|---|---|---|
| **delta_cold_overall** | **+0.2234** | -0.482 | **+0.911** | ⚠️ CI > 0 |
| delta_cold_artsy | -0.3517 | -1.431 | +0.586 | ⚠️ CI includes 0 |
| delta_cold_saatchi | +0.4590 | -0.260 | +1.183 | ⚠️ CI > 0 |
| delta_warm | **-2.1409** | -2.227 | -2.055 | ✅ (cycle B와 정합 / warm robust) |

**bootstrap_FAIL** (cold_overall CI95 upper > 0.5 → bootstrap_FAIL).

**핵심 finding**: D1.Z+alt에서 cold_overall mean=-1.16 (CI95 upper -0.60)이었던 것과 **정반대** (mean=+0.22 / CI95 upper +0.91). D1.Y N=10 sample이 실제로 outlier-light biased sample이었음.

### 5.3 Per-source decomposition (tertiary)

| Source | mean | CI95 | Status |
|---|---|---|---|
| cold_artsy | -0.352 | [-1.43, +0.59] | ⚠️ |
| cold_saatchi | +0.459 | [-0.26, +1.18] | ⚠️ |

**saatchi side가 더 강한 regression** — D1.Y에서는 artsy outlier (113)였는데 본 cycle에서는 saatchi side outlier 추가 발생. Source-conditional 단순 이론과 다름.

### 5.4 Warm path (record only)

`delta_warm` mean=-2.14 / CI95 [-2.23, -2.06] — 매우 robust negative. 본 D1 axis fail와 별개로 warm path는 일관 -2pp 개선. **PR-WARM-B (warm-only retune ADOPT) 정당성 재확인**.

## 6. Combined decision

R1 amendment combined rule:
- **Strict primary**: FAIL (8/10 FAIL)
- **Bootstrap secondary**: bootstrap_FAIL (cold_overall CI95 upper > +0.5)
- **Lax-1**: FAIL (7/10 FAIL)

→ **`HOLD_D1_axis_abandon`** (R1 P0 / strict primary FAIL → 무조건 HOLD).

## 7. D1 axis 종결 확정 (codex Q7 정합)

**3 cycle 누적 결과 (D1 axis)**:
| Cycle | N | Verdict | 비고 |
|---|---|---|---|
| D1.X (commit d06ea22) | 5 | NEEDS_MORE_DATA | 4/5 PASS / 1 outlier |
| D1.Y (commit d774938) | 10 | FAIL | 7/10 PASS / 3 outliers |
| D1.Z+alt (commit a564e2e) | re-analysis | hypothesis-generating | bootstrap CI cold_overall PASS (analysis-only) |
| **D1-extended (본 commit)** | **10 fresh** | **HOLD_abandon** | **2/10 PASS / 8 outliers** ⚡ |

**Key insight**: bootstrap CI on small samples (N=10) is unreliable for champion swap binding decision (codex P0/P1.1 warning 정확). D1.Y가 더 좋아 보였던 결과는 sampling lottery / not generalizable.

**운영 결정**: D1 retune **완전 abandon**. 현 N=32 default best_params 유지. 본 axis는 본 cycle로 종결.

## 8. PR-WARM-B와 conflict 해소

D1 abandon 결정 → PR-WARM-B (B winner) 단독 deploy path 유효:
- Cold path: default best_params (CB) 그대로 / D1 retune 채택 X
- Warm path: B-retuned XGB (PR-WARM-B Stage 5 후 deploy)

**PR-WARM-B는 본 D1-extended 결과와 무관 / Stage 3-5 진행 그대로 valid** (D1-extended에서도 warm 모든 10 seed Δ_warm 음수 confirm).

## 9. 산출물

### 9.1 Commit 대상

- `docs/d1_extended_prospective_prereg_20260510.md` (R1-R3 amendment 반영)
- `docs/d1_extended_prospective_results_20260510.md` (본 문서)
- `scripts/d1_extended_validation.py` (10 fresh seed validation + bootstrap + threshold + per-source)
- `data/d1_extended_holdout_20260510/seed{631,661,691,727,757,787,821,853,877,907}_holdout_indices.json`

### 9.2 .gitignore (artifact)

- `model_test_results/d1_extended_results.json` (per-seed + bootstrap + threshold + per-source 종합)

## 10. 한계 / Risk (codex Q7 정합 검증)

- **D1.Y N=10이 unrepresentative**: 80% vs 30% bad-seed rate gap이 sampling lottery 입증 / single sample bootstrap CI 신뢰 X
- **N=20 (D1.Y + 본 cycle 결합) 가능성**: dataset_fingerprint 동일 시 N=20 record 가능 / 단 본 cycle 결과만으로도 D1 axis abandon 충분 / 별도 기록만
- **Codex Q7 strong recommendation 정확**: "D1 axis abandon / B + source-conditional 우선" — 정확히 본 결과로 입증

## 11. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | HOLD | P0 + P1×2 + Q7 D1 abandon recommendation |
| R2 사전 | NEEDS FIX (stale text) | §5 / §8 정정 |
| R3 사전 | LGTM | Stage 진입 ready |
| R4 사후 | (예정) | 결과 검수 / D1 axis 종결 결정 적정성 / Q7 prediction 검증 |

## 12. 결론

D1-extended fresh N=10 prospective cycle 결과 = **HOLD_D1_axis_abandon**.

**운영 결정**:
- ✅ N=32 default best_params 그대로 유지
- ✅ D1 axis 완전 종결 (3 cycle 누적 fail / codex Q7 정합)
- ✅ PR-WARM-B (B winner) 단독 deploy path 유효 (D1과 conflict 없음)

**Codex R1 HOLD verdict 정당성 입증**:
- Bootstrap mean-CI on small N → fresh sample에서 정반대 결과 가능 (P0/P1.1 warning)
- D1.Y outlier-light sample이었음 (P1.1 underpower 우려)
- "D1 abandon / clean B + source-conditional 우선" recommendation 정확 (Q7)

**본 세션 14 cycles 종합**:
- ✅ B (warm-only) — 유일 ADOPT (PR-WARM-B Stage 1+2 commit / Stage 3-5 pending)
- ❌ D1 axis (D1.X / D1.Y / D1.Z+alt / D1-extended) — 완전 abandon 확정
- ❌ D3 axis (D3 / D3.B) — blend axis 종결

운영 트랙1 모델 = **N=32 default tuned + warm path B-retuned (Stage 5 후) + per-source calibration shipped**.
