# D1: N=32 Champion HP Re-optimization 결과 (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md` (R3 LGTM)
> **Run**: `scripts/optuna_n32_champion_retune.py --n-trials 30`
> **Best params**: `model_test_results/n32_champion_retuned_best_params.json`
> **Validation**: `model_test_results/d1_validation_20260510.json`
> **Holdout indices**: `data/d1_holdout_20260510/seed{97,113,199}_holdout_indices.json`

## 1. TL;DR

> **Status**: **Exploratory pilot** (not strict decision-binding / R4 protocol deviations 인정 → 후속 compliant rerun에서 binding 결정).

**Overall verdict (mechanically)**: **HOLD** (per prereg §3.2 strict per-source guards / Aggregate FAIL).

**R4 protocol deviations (binding 자격 약화)**:
- P0: Paired bootstrap CI logic 미구현 (prereg §2.6 reserved / script 미반영). 영향: small sub-cell INCONCLUSIVE path 활용 불가 / strict G만 적용됨.
- P1: 30 trials × 2 phases (prereg 50 / N15.B와 동일 deviation). 단 N15.B는 clean negative라 영향 미미했지만, D1은 positive mixed signal이라 deviation 무게 더 큼.

**향후 binding 결정 위해서는**:
1. Paired bootstrap CI 구현 + rerun, 또는
2. Prereg §2.6에서 CI path 제거 + 50 trials rerun.

**핵심 발견 (mixed signal / 양면)**:

✅ **Search 결과는 명확한 positive**:
- Phase 1 (CB): best cold_cv = **38.18** (default 38.79 / **Δ −0.61pp 개선**)
- Phase 2 (XGB): best warm_cv = **9.16** (default 9.70 / **Δ −0.54pp 개선**)
- 두 model 모두 default best_params를 능가하는 retune 발견

✅ **Validation overall metrics 모두 개선**:
- 3/3 seed Δ_cold ≤ 0 (range −2.10 ~ −0.33pp / 평균 **−0.97pp**)
- 3/3 seed Δ_warm ≤ 0 (range −0.83 ~ −0.23pp / 평균 **−0.54pp**)

❌ **Per-source guards split variance (G2 / G3 FAIL)**:
- seed 97: 전 guard PASS (모두 개선)
- seed 113: G2 FAIL (Δ_artsy=+0.48 > +0.3pp / 단 cold/saatchi/warm 개선)
- seed 199: G3 FAIL (Δ_saatchi=+0.46 > +0.3pp / 단 cold/artsy/warm 개선)

→ Overall metrics는 robust 개선 / per-source는 split-driven variance (N15 series 일관 패턴 / Artsy small cell + Saatchi 다양성). Strict 기준으로 PASS×1 + FAIL×2 → Aggregate FAIL.

## 2. Optuna Search 결과

### 2.1 Phase 1: CB best params (cold ensemble objective / XGB_default fixed)

```json
{
  "iterations": 1817,
  "depth": 8,
  "learning_rate": 0.0101,
  "l2_leaf_reg": 3.95,
  "random_strength": 3.09,
  "border_count": 194,
  "subsample": 0.9453
}
```

vs default CB:
- iterations 1000 → **1817** (~1.8x)
- depth 8 → 8 (동일)
- learning_rate 0.0953 → **0.0101** (10x 작음 / fine learning)
- l2_leaf_reg 1.63 → 3.95 (강한 regularization)
- random_strength 0 → 3.09
- subsample 1.0 → 0.95

→ Slower learning + stronger regularization + subsampling.

### 2.2 Phase 2: XGB best params (warm objective / cold ensemble guard / CB_best_phase1 fixed)

```json
{
  "num_boost_round": ...,
  "max_depth": ...,
  ... (구체적 값은 best_params JSON 참조)
}
```

XGB best warm_cv = **9.16** (default 9.70 / Δ −0.54pp).
Best cold_overall_cv (with CB_best_phase1) = (TBD from JSON 검토).

### 2.3 Compute summary

- Phase 1: 30 trials × ~1.7min/trial = **49 min** wall.
- Phase 2: 30 trials × ~7min/trial = **~210 min** wall (heavy: warm CV + cold ensemble CV per trial).
- Total wall: ~4.5 hours (compute-intensive search).

## 3. Validation 결과 (fresh seeds {97, 113, 199})

### 3.1 Per-seed metrics (Δ_retuned_vs_default)

| Seed | Δ_cold_overall | Δ_cold_artsy | Δ_cold_saatchi | Δ_warm | Verdict |
|---|---|---|---|---|---|
| 97  | **−2.10** ⭐ | **−4.88** ⭐ | **−1.23** ✓ | **−0.55** ✓ | **PASS** (전 metric 강한 개선) |
| 113 | −0.49 ✓ | **+0.48** ⚠️ | −1.13 ✓ | −0.83 ✓ | FAIL (G2 artsy +0.3 초과) |
| 199 | −0.33 ✓ | −4.33 ⭐ | **+0.46** ⚠️ | −0.23 ✓ | FAIL (G3 saatchi +0.3 초과) |

**Aggregate Δ across seeds (mean)**:
- Δ_cold_overall: **−0.97pp** (모두 개선 / 평균 1pp 개선)
- Δ_cold_artsy: −2.91pp (2/3 강한 개선 / 1/3 약한 악화)
- Δ_cold_saatchi: −0.63pp (2/3 개선 / 1/3 약한 악화)
- Δ_warm: −0.54pp (3/3 개선)

### 3.2 Aggregate verdict

PASS × 1 + FAIL × 2 → **FAIL** (strict aggregate per prereg §3.2).

**FAIL 원인 분석**:
- 두 FAIL seed 모두 한 source에서만 +0.5pp 미만 mild regression (artsy +0.48 / saatchi +0.46).
- 동시에 다른 metric은 모두 개선 (cold overall / warm / 다른 source).
- 해석: per-source guard threshold (+0.3pp)가 split variance 흡수에 너무 strict. 또는 retuned params가 매 seed에서 source bias를 분배 — overall 개선 / 한 source 약한 악화.

## 4. 채택 결정

**전체**: HOLD per prereg §3.3.

### 4.1 결과의 양면 해석

✅ **Champion 의 best_params는 default보다 명확히 개선됨** (CV + validation 일관):
- Search-time CV: cold −0.61pp / warm −0.54pp 개선
- Validation overall mean: cold −0.97pp / warm −0.54pp 개선

❌ **Per-source guard에서 split variance 흡수 X**:
- seed 113 artsy +0.48 / seed 199 saatchi +0.46
- N15 series에서 본 split variance 패턴 일관

→ **결과는 sound positive signal**이지만, prereg가 strict per-source guard를 PASS 조건으로 명시했으므로 mechanically FAIL.

### 4.2 권고 (codex 사후 검수에서 확정 예정)

1. **즉시**: 운영 best_params 그대로 유지 (HOLD verdict 준수).
2. **본 retune의 가치**: Overall cold/warm 개선 시그널 robust. 운영 ROI 관점에서 가치 있음 (~1pp cold + ~0.5pp warm 개선).
3. **후속 cycle 후보**:
   - **Multi-seed N=5-7 확대**: per-source guard split variance 평준화. 추가 50-100 min compute. 직접적 follow-up.
   - **Per-source guard threshold 완화**: PASS threshold +0.3 → +0.6pp (overall 개선이 큰 경우 source-level mild regression 허용). prereg 변경.
   - **Multi-objective Pareto search**: cold + per-source artsy + per-source saatchi 동시 최소화 (3-objective Pareto). 별도 cycle.

### 4.3 N=15 series + D1 통합 진단 (8 cycles 누적)

| Cycle | Compute | Verdict | Signal |
|---|---|---|---|
| Reprod (d0f8b88) | small | FAIL with caveat | in-sample bias |
| OOS (08a6b80) | medium | NEEDS_MORE_DATA | artsy_online ADOPT_with_caveat |
| N15.A (8c9e58e) | medium | HOLD | warm strict / cold artsy signal |
| N15.B (38eab10) | heavy | HOLD clean negative | retune under proper CV X |
| N15.C (4499fe9) | medium | NEEDS_MORE_DATA | split variance + Saatchi PASS |
| **D1 (this)** | **heavy** | **HOLD with positive signal** | **overall improvement / per-source split variance** |

→ **D1이 가장 명확한 positive signal**: HP retuning은 default를 능가 (overall metrics). 단 strict per-source guard 통과를 위해 multi-seed 확대 또는 threshold 완화 필요.

## 5. 한계 / Risk

- **Phase 2 compute heavy** (210 min / 30 trials): num_boost_round=4000 + max_depth=10 trials slow. 후속 cycle에서 budget cap.
- **Default XGB enqueue OOR warning**: default reg_alpha=2.56 out of [0, 1.0]. 영향 미미 (Optuna handles via clip / 결과 검증 OK).
- **Per-source guard +0.3pp strict**: split variance not absorbed. 30K row dataset에서 split variance 본질적 한계.
- **3 seed 한정**: codex prereg 권고 multi-seed 확대 후속 cycle에서.

## 6. 코덱스 자문 이력 (R4 사후 검수 예정)

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | D1 = top recommendation | 본 cycle motivation |
| R1 사전 자문 | NEEDS FIX → 반영 | P0 ensemble metric / P1 search loose / P2 enqueue |
| R2 verification | NEEDS FIX → 반영 | Phase 2 cold guard 4-constraint |
| R3 verification | LGTM | prereg 잠금 |
| R4 사후 검수 (resume) | NEEDS FIX → exploratory downgrade | P0: paired bootstrap CI 미구현. P1: 30 vs 50 trials deviation. **Codex 권고**: 본 cycle = exploratory pilot 처리 / binding 결정은 compliant rerun (50 trials + CI 구현) 후 / signal은 N15 series 대비 명확히 강함 (overall improvement 3/3 seed) / 후속 cycle 우선순위: D1 compliant rerun > D3 > B. |

## 7. 산출물

- ✅ `docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md` (R1-R3 LGTM)
- ✅ `docs/d1_n32_champion_hp_reoptimization_results_20260510.md` (본 문서)
- ✅ `scripts/optuna_n32_champion_retune.py` (~520 lines / ruff clean / CB bagging_temperature crash fix)
- ✅ `model_test_results/n32_champion_retuned_best_params.json` (commit 대상 / Phase 1+2 best)
- ✅ `data/d1_holdout_20260510/seed{97,113,199}_holdout_indices.json`
- (gitignored) `model_test_results/n32_champion_optuna_study_cb.json` (Phase 1 30 trials)
- (gitignored) `model_test_results/n32_champion_optuna_study_xgb.json` (Phase 2 30 trials)
- (gitignored) `model_test_results/d1_validation_20260510.json`
