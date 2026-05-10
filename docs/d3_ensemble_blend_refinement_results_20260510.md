# D3: Ensemble Blend Refinement — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d3_ensemble_blend_refinement_prereg_20260510.md` (R1 LGTM)
> **실행일**: 2026-05-10 (11:13 KST 시작 / 11:15 KST 종료 / ~3min wall)
> **실행 결과**: ❌ **HOLD_50_50** (1 PASS + 4 FAIL → aggregate=FAIL)

## 1. Summary

OOF cold prediction 위에서 `w ∈ [0, 1]` 21-point grid search → **w*=0.3** (XGB 비중 ↑) 발견. OOF cold_overall = 38.46 (default 38.79 / Δ=-0.34). 그러나 fresh 5-seed validation에서 **1 PASS + 4 FAIL** → **HOLD_50_50** verdict. 운영 blend ratio 변경 X / D3 axis terminate.

## 2. OOF Search 결과

### 2.1 Cold OOF generation

`GroupKFold-5(artist_slug=1551 groups)` / default CB + XGB params / 81.6s wall.

### 2.2 Grid search

w ∈ {0.0, 0.05, 0.10, ..., 0.95, 1.0} (21 points).

| w | cold_overall | cold_artsy | cold_saatchi | Δ_artsy | Δ_saatchi | constraint |
|---|---|---|---|---|---|---|
| 0.5 (default) | 38.79 | 33.18 | 41.21 | 0 | 0 | baseline |
| **0.3 (winner)** | **38.46** | 33.33 | 40.83 | +0.15 | -0.38 | feasible (G2 ≤+0.3 / G3 ≤+0.3) |

**Best w* = 0.3** / OOF Δ_cold = -0.34pp (XGB 비중 70% / CB 30%).

핵심 해석: cold path에서 **XGB가 CB보다 약간 더 좋은 신호** (50/50 → 30/70 / cold_overall -0.34).

## 3. Validation 결과 (5 fresh seeds)

```json
"validation_seeds": [127, 233, 269, 311, 419]
```

### 3.1 Per-seed verdict

| seed | n_pool | n_holdout | base cold | cand cold | Δ_cold | Δ_artsy | Δ_saatchi | verdict |
|---|---|---|---|---|---|---|---|---|
| 127 | 23767 | 4609 | 30.32 | 31.28 | **+0.95** | +0.03 | +1.15 | **FAIL** |
| 233 | 23276 | 5100 | 37.89 | 36.47 | -1.41 | -0.37 | -1.86 | **PASS** |
| 269 | 23356 | 5020 | 36.15 | 37.11 | **+0.96** | +1.23 | +1.00 | **FAIL** |
| 311 | 22048 | 6328 | 41.40 | 41.37 | -0.03 | **+1.95** | +0.05 | **FAIL** |
| 419 | 22547 | 5829 | 45.83 | 45.85 | +0.02 | +0.75 | -0.38 | **FAIL** |

**Aggregate**: 1 PASS + 4 FAIL → **FAIL**.

### 3.2 OOF / Validation gap 해석

OOF에서는 cold_overall -0.34pp 개선 / G2 / G3 모두 feasible. 그러나 fresh 5-seed validation 1/5 PASS only — OOF improvement이 fresh holdout 분포에서 일반화되지 X.

원인 추정:
- **OOF leakage X**: `GroupKFold(artist_slug)` 사용 / blend weight는 OOF prediction 위에서 search → search-time leakage 자체는 없음
- **Holdout 분포 차이**: fresh seed 5개 모두 train_test_split (group X) / OOF는 GroupKFold 정합 / sampling 분포 mismatch
- **Population-level w*=0.3**과 **per-split optimal w**가 다름 / split variance 흡수 X

### 3.3 G2/G3 violation 패턴

| seed | G2 (artsy +0.3 thr) | G3 (saatchi +0.3 thr) | G1 (cold +0pp) |
|---|---|---|---|
| 127 | OK (+0.03) | **❌ +1.15** | **❌ +0.95** |
| 233 | OK | OK | OK |
| 269 | **❌ +1.23** | **❌ +1.00** | **❌ +0.96** |
| 311 | **❌ +1.95** | OK | OK |
| 419 | **❌ +0.75** | OK | OK |

artsy violation 3건 / saatchi violation 2건 / cold_overall violation 2건. artsy는 OOF에서도 +0.15 marginal feasible이었음 → fresh split에서 random outlier 다수 등장.

## 4. 종합 verdict 및 채택 결정

### 4.1 Aggregate

| 항목 | 값 |
|---|---|
| OOF best | w*=0.3 / cold Δ=-0.34 |
| Validation per-seed | 1 PASS + 4 FAIL |
| Aggregate | **FAIL** (FAIL ≥ max(3, n-2) = 3) |
| Overall verdict | **HOLD_50_50** |

### 4.2 채택 결정

prereg §3.3 정합:
- ❌ PASS / 운영 blend 변경 — 미충족
- ❌ PASS_with_caveat / canary — 미충족
- ✅ **FAIL / 50/50 유지** — 본 verdict
- ❌ INCONCLUSIVE — 미충족

**운영 결정**: 운영 ensemble blend = `(CB + XGB) / 2` 50/50 그대로 유지. D3 axis는 **scalar w blend 한정 종결**.

### 4.3 후속 cycle 권고 (별도 axis)

D3 scalar w는 fail. 그러나 OOF가 -0.34 개선을 보여준 점은 의미 있음 — search method 또는 model space 확대 필요:

- **D3.B (stacking meta-learner)**: linear regression / xgboost stacker / GBM 위에서 (cb_pred, xgb_pred, source) → final blend. 현 1D scalar 대체 / 후속 cycle.
- **D3.C (source-conditional blend)**: artsy `w_a` / saatchi `w_s` 별도 / 4D Pareto.
- **D3.D (per-cell blend)**: warm `w_w` 추가 / 운영 ensemble layer 확장.

본 cycle 종결 후 별도 prereg + codex 자문 필요.

## 5. 산출물

### 5.1 Commit 대상

- `docs/d3_ensemble_blend_refinement_prereg_20260510.md` (R1 LGTM)
- `docs/d3_ensemble_blend_refinement_results_20260510.md` (본 문서)
- `scripts/d3_blend_search.py`
- `data/d3_holdout_20260510/seed{127,233,269,311,419}_holdout_indices.json`

### 5.2 .gitignore (artifact)

- `model_test_results/d3_blend_winner.json` (6.6KB / OOF grid 21-point all records)
- `model_test_results/d3_blend_search_results.json` (3.3KB / validation 상세)

## 6. 한계 및 caveat

- **Scalar w only**: 1D simple search / category-conditional 또는 stacking은 별도 후속.
- **OOF / validation 분리**: blend weight는 OOF에서 search → fold-level leakage 없음 / 단 fresh split 분포 mismatch 노출.
- **N=5 multi-seed**: small sample / split variance 영향력 큼 / 4 FAIL은 우연이 아닌 일반화 실패 신호.
- **Default base params**: D1 retuned params + D3 결합은 별도 cycle (D1+D3 joint).

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | D3 = second priority | 본 cycle motivation |
| R1 사전 (B와 combined) | LGTM | 본 prereg 작성 직후 / 본 결과 위 검수 ready |
| R2 사후 | (예정) | D3 결과 위 검수 / HOLD verdict 적정성 |

## 8. 결론

D3 ensemble blend scalar w 결과 = **HOLD_50_50**. OOF에서 w*=0.3이 cold -0.34pp 개선했으나 fresh 5-seed validation 1/5 PASS만 (4개 FAIL) → 일반화 실패. 운영 50/50 ensemble 유지 / 본 axis (scalar w) 종결. Stacking / source-conditional blend는 별도 cycle 검토 가능.
