# D1.Y: D1.X N=10 Multi-seed Expansion — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_y_multiseed_n10_prereg_20260510.md` (R1 NEEDS FIX → R2 LGTM)
> **실행일**: 2026-05-10 (18:35 KST 시작 / 18:43 KST 종료 / ~8min wall)
> **실행 결과**: ❌ **FAIL → HOLD_n32_default** (7 PASS + 3 FAIL / D1 axis terminate)

## 1. Summary

D1.X (N=5 / 4 PASS + 1 FAIL / NEEDS_MORE_DATA) 확장 / N=10 single snapshot fresh validation 결과:
- **7 PASS + 3 FAIL** → R1 amendment strict aggregate FAIL (FAIL ≥ 2 → champion swap risk premium 발동)
- **D1 axis terminate** / 운영 best_params 유지

핵심 발견: D1.X seed=113 outlier는 **systematic 패턴** (single 단발 outlier 아님). D1.Y new 5 seed에서 추가 2 FAIL (313/367) 발생 / 30% bad-seed rate confirmed.

단 **population-level mean Δ는 강한 개선** (Δ_cold -1.16 / Δ_artsy -1.41 / Δ_warm -2.13) — split variance가 strict guard threshold 위반 빈도를 높임. G threshold 완화 amendment는 별도 cycle 검토 가능 / 본 cycle은 strict로 종결.

## 2. R1 Amendment 반영

R1 NEEDS FIX (P0 + P1×2) 모두 반영 후 R2 LGTM:
- ✅ P0 fix: dataset_fingerprint 단일 snapshot / D1.X JSON 결합 X / 모든 10 seed fresh rerun
- ✅ P1.1 fix: aggregate strict (FAIL × 2 → FAIL / champion swap risk premium)
- ✅ P1.2 fix: rerun all 10 (D1.X 5 seed도 D1.Y 환경에서 재실행 / 정합 보장)
- ✅ Q7 amendment: PR-WARM-B와 deployment baseline interaction 명시

D1.X seed (97/113/199/223/257) 5개 모두 D1.X와 deterministic 정합 (Δ exact match) — 환경 재현성 확인.

## 3. Validation 결과 (N=10 single snapshot)

### 3.1 Per-seed verdict

| seed | source | Δ_cold | Δ_artsy | Δ_saatchi | Δ_warm | G1 | G2 | G3 | G4 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 97 | D1.X | **-1.791** | -1.499 | -2.099 | -2.237 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | D1.X | -1.543 | **+1.759** | +0.277 | -2.132 | ✅ | ❌ | ✅ | ✅ | **FAIL** |
| 199 | D1.X | **-2.318** | -2.482 | -1.767 | -1.861 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 223 | D1.X | **-2.174** | -2.169 | -1.233 | -2.069 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 257 | D1.X | -1.530 | -2.399 | -0.241 | -2.303 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 313 | D1.Y new | -0.189 | -1.673 | **+0.611** | -2.273 | ✅ | ✅ | ❌ | ✅ | **FAIL** |
| 367 | D1.Y new | **+0.329** | -2.275 | **+1.420** | -1.975 | ❌ | ✅ | ❌ | ✅ | **FAIL** |
| 439 | D1.Y new | -0.468 | -1.669 | -0.204 | -2.124 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 491 | D1.Y new | -0.154 | +0.099 | -2.105 | -1.922 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 587 | D1.Y new | **-1.792** | -1.753 | -1.015 | -2.439 | ✅ | ✅ | ✅ | ✅ | **PASS** |

**Verdict counts**: 7 PASS + 0 INCONCLUSIVE + 3 FAIL
**Aggregate**: **FAIL** (R1 P1.1 amendment / FAIL × 2 이상 trigger)

### 3.2 Failure mode 분석

| seed | failure pattern | guard violation |
|---|---|---|
| 113 | artsy_cold +1.76 | G2 (artsy +0.3 threshold) |
| 313 | saatchi_cold +0.61 | G3 (saatchi +0.3 threshold) |
| 367 | cold_overall +0.33 + saatchi_cold +1.42 | G1 + G3 |

→ artsy / saatchi 양 source 모두에서 holdout split outlier 발생 / single source 한정 X.

### 3.3 Population-level mean (R1 P1.1 strict와 별개 record)

| Metric | Mean Δ | Std | Min | Max |
|---|---|---|---|---|
| Δ_cold_overall | **-1.163** | 0.875 | -2.318 | +0.329 |
| Δ_cold_artsy | **-1.406** | 1.187 | -2.482 | +1.759 |
| Δ_cold_saatchi | **-0.836** | 1.030 | -2.105 | +1.420 |
| Δ_warm | **-2.134** | 0.187 | -2.439 | -1.861 |

→ **모든 metric 평균 음수** (population-level 강한 개선) / 단 strict guard threshold 위반 빈도 (30% bad-seed rate)가 aggregate FAIL trigger.

특히 Δ_warm = -2.13 ± 0.19 — **모든 10 seed Δ_warm 음수** / warm path는 강한 robust 개선 (cycle B와 정합 / 본 cycle에서는 cold + warm joint이라 운영 적용 X).

## 4. 종합 verdict 및 채택 결정

### 4.1 Aggregate

| 항목 | 값 |
|---|---|
| Per-seed | 7 PASS + 0 INCONCLUSIVE + 3 FAIL |
| Aggregate (R1 amendment strict) | **FAIL** |
| Overall verdict | **HOLD_n32_default** |

R1 P1.1 strict logic: FAIL × 2 이상 → FAIL aggregate (champion swap risk premium). 본 cycle 적용.

### 4.2 채택 결정

prereg §2.6 정합:
- ❌ PASS / 운영 best_params 교체 — 미충족
- ❌ PASS_with_caveat / canary deployment — 미충족 (FAIL × 3)
- ✅ **FAIL / D1 axis terminate** — 본 verdict
- ❌ INCONCLUSIVE — 미충족

**운영 결정**: 현 best_params (`integrated_v3_filtered_tuned_best_params.json`) 그대로 유지. **D1 axis 종결** (D1.X / D1.Y 종합 결과 / 본 prereg G threshold 하에서는 channel 닫힘).

### 4.3 D1 axis 종결 의미

D1.X (1 FAIL / 5 seed) → "1 outlier 흡수 가능" 가정으로 N=10 확장. 단 D1.Y에서 추가 2 FAIL → "outlier가 systematic" 결론. 30% bad-seed rate는 strict champion swap에 부적합.

**대안 후속 cycle 후보** (별도 prereg 필요):
- **D1.Z (G threshold 완화)**: G2 / G3 +0.3 → +0.8 (D1.X R7 amendment 시 고려된 lax threshold) / population-level mean 강한 negative라 적정 가능
- **D1.alt (Bootstrap aggregation)**: per-seed strict aggregate 대신 mean Δ + CI95 기반 결정 / 분포 전체 평가
- **D1.split (Per-source separate retune)**: artsy / saatchi split variance 크기 본질 / source-conditional retune (PR1 정합)

본 cycle = **D1 strict champion swap path 종결** / 다른 axis는 별도 결정.

## 5. 산출물

### 5.1 Commit 대상

- `docs/d1_y_multiseed_n10_prereg_20260510.md` (R1 amendment 반영)
- `docs/d1_y_multiseed_n10_results_20260510.md` (본 문서)
- `scripts/d1_y_validation_only.py` (R1 amendment / single snapshot rerun + strict aggregate)
- `data/d1_y_holdout_20260510/seed{313,367,439,491,587}_holdout_indices.json` (5 new seed)
- (D1.X seeds 97/113/199/223/257 holdout는 기존 d1_holdout_20260510/ 그대로 / overwriting X)

### 5.2 .gitignore (artifact)

- `model_test_results/d1_y_validation.json` (per-seed 상세)
- `model_test_results/d1_y_aggregate.json` (N=10 aggregate)

## 6. 한계 / Risk

- **Strict G threshold (artsy / saatchi +0.3)**: small cell + heavy-tailed 분포 / 30% violation rate가 채택 막음 / G threshold 완화 시 aggregate 다를 수 있음.
- **N=10도 small sample**: artsy_gallery cell n_holdout 150-250 / split variance 본질적 한계.
- **Single retuned param set**: D1.X single Optuna search 결과 / search seed 변경 시 다른 best_params 가능 (단 본 cycle은 search 검증이 아닌 validation 분산 검증).
- **Validation = artist-grouped 80/20 + warm row-split 80/20 / 운영 traffic은 시간순 / 분포 다를 수 있음**.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX (P0 + P1×2) | dataset_fingerprint policy / aggregate strict / rerun all 10 |
| R2 사전 | LGTM | amendment 정합 |
| R3 사후 | (예정) | 결과 검수 / D1 axis 종결 결정 적정성 |

## 8. 결론

D1.Y N=10 strict aggregate FAIL → **D1 axis 종결**. Search-time CV 강한 개선 + per-seed mean Δ 모두 음수 / 단 split variance 큰 strict G threshold 위반 빈도 30% / champion swap에 부적합. 운영 best_params 유지.

**중요**: warm path는 모든 10 seed Δ_warm 음수 (mean -2.13 / std 0.19) — robust 개선. PR-WARM-B (cycle B / warm-only retune)는 별개 cycle / 본 D1 axis 종결과 무관. PR-WARM-B Stage 3 shadow 진행은 그대로 valid.
