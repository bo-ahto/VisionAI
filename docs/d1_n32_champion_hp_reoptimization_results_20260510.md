# D1: N=32 Champion HP Re-optimization — Results (compliant rerun)

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md` (R7 amendment LGTM)
> **실행일**: 2026-05-10 (08:48 KST 시작 / 11:12 KST 종료 / 2h 24min wall)
> **실행 결과**: ⚠️ **NEEDS_MORE_DATA** (4 PASS + 1 FAIL aggregate=INCONCLUSIVE)

## 1. Summary

R7 amendment 정합 compliant rerun:
- ✅ 50 trials × 2 phase (Phase 1 CB / Phase 2 XGB)
- ✅ Multi-seed N=5 validation (97 / 113 / 199 / 223 / 257) — D1 R6 expansion
- ✅ Both phase ensemble metric optimization (R4 P0 fix)
- ✅ CI path 제거 (R6 amendment / 모든 cell n_holdout > 500 / CI 본질적 적용 X)
- ✅ enqueue_trial(default) for incumbent first-class

Search CV는 양 phase 모두 강한 개선 (cold Δ=-0.68 / warm Δ=-2.20). Validation 5 seed 중 4개 (97, 199, 223, 257)는 강한 PASS, **seed=113만 G2 (artsy_cold) +1.76pp 위반 → FAIL**. Aggregate INCONCLUSIVE → overall **NEEDS_MORE_DATA**.

## 2. Search 결과

### 2.1 Phase 1: CB Optuna (50 trials / 4551s)

**Default CB**: `{iterations: 1000, depth: 8, lr: 0.0953, l2: 1.63, bagging_temperature: 0.18}`

**Best CB**:
```json
{
  "iterations": 1012,
  "depth": 8,
  "learning_rate": 0.01145,
  "l2_leaf_reg": 1.0926,
  "random_strength": 0.1266,
  "border_count": 237,
  "subsample": 0.8540
}
```

| Cell | Default CV | Best CV | Δ |
|---|---|---|---|
| cold_overall | 38.79 | **38.11** | **-0.68** |
| cold_artsy | 33.18 | 33.24 | +0.06 |
| cold_saatchi | 41.21 | 40.61 | -0.59 |

핵심 변화: lr 약 8.3× 감소 (0.0953 → 0.0114) + iter 거의 동일 → 더 작은 step의 strong fit. random_strength 도입 (default=0).

### 2.2 Phase 2: XGB Optuna (50 trials / 3724s)

**Default XGB**: `{n_round: 3000, depth: 7, eta: 0.0401, gamma: 0.0115, alpha: 2.56, lambda: 3.10, subsample: 0.870, colsample: 0.922}`

**Best XGB**:
```json
{
  "num_boost_round": 1876,
  "max_depth": 8,
  "learning_rate": 0.0865,
  "subsample": 0.9034,
  "colsample_bytree": 0.9274,
  "min_child_weight": 9,
  "gamma": 0.0009,
  "reg_alpha": 0.4492,
  "reg_lambda": 1.9961
}
```

| Cell | Default CV | Best CV | Δ |
|---|---|---|---|
| warm | 9.70 | **7.50** | **-2.20** |
| cold_overall (CB_best+XGB_retuned) | — | 38.77 | (Phase 1 baseline 회복 / minor regression) |

핵심 변화: lr 2.2× 증가 / iter 0.6× 감소 (3000 → 1876 / 빠른 수렴) / depth +1 / min_child_weight 1→9 (regularization) / reg_alpha 5.7× 감소 / gamma 12× 감소.

### 2.3 Search-time vs Validation 정합

R4 P0 fix 검증 — 양 phase 모두 ensemble metric optimization:
- Phase 1 CB search → cold ensemble metric 개선 / Validation 5/5 cold delta 음수 (-1.5 ~ -2.3pp)
- Phase 2 XGB search → warm CV 개선 / Validation 5/5 warm delta 음수 (-1.86 ~ -2.30pp)

→ Phase 1, Phase 2 모두 holdout에서도 CV에서 본 개선이 일관됨. R4 P0 fix 효과 확인.

### 2.4 R4 P0 (paired bootstrap CI) 처리

R6 amendment에서 CI path 제거 결정:
- 본 cycle 모든 cell n_holdout > 500 (artsy ~1500 / saatchi ~4500 / warm ~5400) → CI 본질적 적용 X
- 향후 small-sub-cell (n < 500) cycle 등장 시 별도 amendment

## 3. Validation 결과 (5 seed)

```json
"validation_seeds": [97, 113, 199, 223, 257]
```

### 3.1 Per-seed verdict

| seed | Δ_cold_overall | Δ_artsy | Δ_saatchi | Δ_warm | G1 | G2 | G3 | G4 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 97 | -1.79 | -1.50 | -2.10 | -2.24 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 113 | -1.54 | **+1.76** | +0.28 | -2.13 | ✅ | ❌ | ✅ | ✅ | **FAIL** |
| 199 | -2.32 | -2.48 | -1.77 | -1.86 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 223 | -2.17 | -2.17 | -1.23 | -2.07 | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 257 | -1.53 | -2.40 | -0.24 | -2.30 | ✅ | ✅ | ✅ | ✅ | **PASS** |

**Aggregate**: 4 PASS + 1 FAIL → **INCONCLUSIVE**.

### 3.2 seed=113 anomaly 분석

| | default | retuned |
|---|---|---|
| cold_overall | 50.34 | 48.80 |
| cold_artsy | 31.46 | 33.22 |
| cold_saatchi | 54.55 | 54.83 |

해당 seed의 default ens cold_overall = 50.34 (다른 seed의 36~37 대비 +13~14pp 높음). seed=113 holdout split이 outlier-heavy / 어려운 작가 구성. retuned는 cold_overall은 -1.54 개선했으나 artsy 부분에서만 +1.76pp regression.

→ 본 outlier seed에서만 search-time CV improvement가 holdout split variance 흡수 X. 4/5 seed에서는 강한 일관 개선.

### 3.3 G2 violation 해석

- G2 threshold = +0.8pp (artsy cold)
- seed=113 artsy_cold: +1.76pp (위반) — 단 1 seed
- 다른 4 seed artsy_cold: -1.50 / -2.48 / -2.17 / -2.40 (모두 강한 음수)
- 평균 artsy_cold delta = (-1.50 + 1.76 - 2.48 - 2.17 - 2.40) / 5 = **-1.36pp** (강한 평균 개선)

→ Population-level mean improvement / split-variance outlier 1건 발생.

## 4. 종합 verdict 및 채택 결정

### 4.1 Aggregate

| 항목 | 값 |
|---|---|
| Per-seed 분포 | 4 PASS + 1 FAIL |
| Aggregate (R6 logic) | INCONCLUSIVE |
| Overall verdict | **NEEDS_MORE_DATA** |

### 4.2 채택 결정

prereg §3.3 정합:
- ❌ PASS / 운영 best_params 교체 권고 — 미충족 (1 seed FAIL)
- ❌ PASS_with_caveat / canary deployment — 미충족 (FAIL은 INCONCLUSIVE 아님)
- ❌ FAIL / D1 axis terminate — 미충족 (4/5 PASS 강한 신호)
- ✅ **NEEDS_MORE_DATA / Multi-seed 추가 확장 후속 cycle** — 본 verdict

**운영 결정**: 현 best_params 유지 / D1 axis는 종결 X / multi-seed 확대 후속 cycle 권고.

### 4.3 후속 cycle 권고

**D1.Y (multi-seed 확장)**:
- N=10 또는 N=15 expansion seed
- seed=113 outlier 분석 (해당 split 외부 검증 / split fingerprint 보존됨)
- Bootstrap aggregation: per-seed delta 분포 평균/CI를 결정 근거로 (현행 PASS×N strict aggregate 대신)
- 비용: 추가 ~5-7시간 wall (current artifact 기준)

**대안 D1.alt (G2 threshold relaxation)**:
- artsy 변동성 high 작가 다수 → split variance 자체가 큰 cell
- G2 threshold +0.8 → +1.5 (50%↑) 고려 가능 / amendment 필요

## 5. 산출물

### 5.1 Commit 대상 (PR 후보)

- `docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md` (R7 amendment 포함)
- `docs/d1_n32_champion_hp_reoptimization_results_20260510.md` (본 문서)
- `scripts/optuna_n32_champion_retune.py` (R6 amendment compliant)
- `model_test_results/n32_champion_retuned_best_params.json` (1.7KB)
- `data/d1_holdout_20260510/seed{97,113,199,223,257}_holdout_indices.json` (3.4MB total)

### 5.2 .gitignore (artifact)

- `model_test_results/n32_champion_optuna_study_cb.json` (32KB / 50 trials)
- `model_test_results/n32_champion_optuna_study_xgb.json` (40KB / 50 trials)
- `model_test_results/d1_validation_20260510.json` (validation 상세)

## 6. 한계 및 caveat

- **Sequential 9+9 search**: joint 18-dim Pareto가 아님 / 본 cycle simplification (prereg §2.1).
- **TPE seed=42**: Optuna sampler seed 고정 / TPE 자체 stochasticity는 search 결과 약간 변동 가능.
- **N=5 multi-seed**: small sample / split variance 영향력 큼 / 본 cycle 1 outlier seed 있음.
- **Search CV vs Validation gap**: search holdout split와 validation holdout split는 다름 (KFold vs train_test_split / random_state 다름) → CV 개선이 모든 split에 일반화되지 X.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | D1 = top priority | 본 cycle motivation |
| R1 사전 | LGTM | Phase 1 / Phase 2 plan 승인 |
| R2 follow-up | LGTM | search space / constraint 정합 |
| R3 final pre | LGTM | enqueue_trial / non-determinism 보강 |
| R4 사후 (1차 run) | NEEDS FIX (P0 ×2 / P1 ×1) | (1) ensemble metric mismatch (2) CI 미구현 (3) trial 30/50 mismatch |
| R5 amendment | LGTM | R4 P0 (1) ensemble metric fix |
| R6 amendment | LGTM | R4 P0 (2) CI removed / R4 P1 trial=50 / N=5 expansion |
| R7 amendment | LGTM | §3.3 PASS_with_caveat → canary mapping 명시 |
| R8 사후 (compliant rerun) | (예정) | 본 결과 검수 / NEEDS_MORE_DATA verdict 적정성 |

## 8. 결론

D1 compliant rerun 결과 = **NEEDS_MORE_DATA**. Search-time CV 강한 개선 (cold -0.68 / warm -2.20) + Validation 4/5 seed 강한 PASS (population-level improvement 명확) — 단 seed=113에서 G2 artsy 1 seed FAIL 발생. 운영 best_params 즉시 교체 X / D1 axis 종결 X / **multi-seed 확장 후속 cycle 권고**.
