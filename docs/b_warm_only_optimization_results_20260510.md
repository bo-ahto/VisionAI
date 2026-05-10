# B: Warm-only Path Optimization — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/b_warm_only_optimization_prereg_20260510.md` (R1 LGTM)
> **실행일**: 2026-05-10 (11:16 KST 시작 / 11:29 KST 종료 / ~13.5min wall)
> **실행 결과**: ✅ **ADOPT_warm_retuned** (5/5 PASS / 평균 Δ_warm=-1.62pp)

## 1. Summary

Cold path 동결 / XGB warm-only Optuna 50 trials. 모든 5 fresh seed (541, 619, 743, 829, 947)에서 **strict Δ_warm ≤ 0 PASS** + 평균 -1.62pp 개선. 운영 warm path 단독 retune 강한 권고.

D1 / D3 대비 본 cycle 성공 차이:
- D1 = ensemble metric / cold + warm joint search → search-time CV 강함, validation 4/5 PASS (1 seed FAIL)
- D3 = blend ratio scalar w → OOF 개선 / fresh seed 일반화 실패 (1/5 PASS)
- **B = warm-only single objective → 깨끗한 PASS** (5/5 / population-level 일관)

## 2. Search 결과

### 2.1 Optuna TPE 50 trials (706s wall)

**Default XGB warm**:
```json
{
  "num_boost_round": 3000,
  "eta": 0.0401,
  "max_depth": 7,
  "gamma": 0.0115,
  "reg_alpha": 2.564,
  "reg_lambda": 3.099,
  "subsample": 0.870,
  "colsample_bytree": 0.922
}
```

**Best XGB warm**:
```json
{
  "num_boost_round": 947,
  "max_depth": 9,
  "learning_rate": 0.1254,
  "subsample": 0.7273,
  "colsample_bytree": 0.8572,
  "min_child_weight": 11,
  "gamma": 0.0088,
  "reg_alpha": 0.5637,
  "reg_lambda": 0.8911
}
```

| Cell | Default CV | Best CV | Δ |
|---|---|---|---|
| warm | 9.70 | **8.01** | **-1.69** |

핵심 변화:
- **num_boost_round**: 3000 → 947 (0.32× / 빠른 수렴)
- **learning_rate**: 0.040 → 0.125 (3.1× / 큰 step)
- **max_depth**: 7 → 9 (+2 / 더 깊은 tree)
- **min_child_weight**: 1 → 11 (강한 leaf regularization)
- **reg_alpha / reg_lambda**: 큰 폭 감소 (2.56→0.56 / 3.10→0.89)

종합: 더 큰 step + 더 깊은 tree + leaf-level regularization (min_child_weight) 위주의 warm-specific HP. cold path 평균 weight 적용 X.

### 2.2 D1 Phase 2 비교

D1 Phase 2 best XGB (CB_best fixed / cold+warm joint metric):
- num_boost_round 1876 / depth 8 / lr 0.0865 / min_child_weight 9 / warm_cv = 7.50

B best XGB (warm-only / cold 무관):
- num_boost_round 947 / depth 9 / lr 0.125 / min_child_weight 11 / warm_cv = 8.01

→ D1 joint-optimized XGB가 warm CV는 더 좋음 (7.50 vs 8.01) — **cold ensemble 기여 (CB+XGB blend)** 때문이지 XGB 자체가 warm에 더 좋아서가 아님. B는 warm-only path (XGB single)에서 best.

운영 deploy 측면:
- **B (warm-only)**: warm path → XGB(B-retuned) / cold path → CB(default)+XGB(default) 그대로 / **부분 deployment 가능**
- **D1 (joint)**: cold + warm 모두 변경 → 통합 deployment / 단 D1은 NEEDS_MORE_DATA

## 3. Validation 결과 (5 fresh seeds)

```json
"validation_seeds": [541, 619, 743, 829, 947]
```

### 3.1 Per-seed verdict

| seed | n_pool_warm | n_holdout_warm | warm_default | warm_retuned | Δ_warm | verdict |
|---|---|---|---|---|---|---|
| 541 | 21649 | 5413 | 9.578 | 8.143 | **-1.435** | ✅ PASS |
| 619 | 21649 | 5413 | 9.749 | 8.214 | **-1.535** | ✅ PASS |
| 743 | 21649 | 5413 | 9.761 | 8.147 | **-1.614** | ✅ PASS |
| 829 | 21649 | 5413 | 9.514 | 7.774 | **-1.741** | ✅ PASS |
| 947 | 21649 | 5413 | 9.860 | 8.089 | **-1.771** | ✅ PASS |

**Aggregate**: 5 PASS → **PASS** (full migration).

### 3.2 통계 요약

| 통계량 | 값 |
|---|---|
| Δ_warm 평균 | **-1.620** |
| Δ_warm 표준편차 | 0.137 |
| Δ_warm min | -1.771 |
| Δ_warm max | -1.435 |
| 모든 seed 음수 | ✅ Yes (population-level consistent) |

### 3.3 Search CV vs Validation 정합

- Search CV warm: 9.70 → 8.01 (Δ=-1.69pp)
- Validation 5-seed mean Δ_warm: -1.62pp
- **차이**: -0.07pp (4.1% / 매우 작음)

→ Search-time CV improvement이 fresh holdout에서 거의 그대로 유지. 일반화 우수.

## 4. 종합 verdict 및 채택 결정

### 4.1 Aggregate

| 항목 | 값 |
|---|---|
| Per-seed | 5 PASS / 0 FAIL / 0 INCONCLUSIVE |
| Aggregate (R1 logic) | PASS (full migration) |
| Overall verdict | **ADOPT_warm_retuned** |

### 4.2 채택 결정

prereg §3.3 정합:
- ✅ **PASS / 운영 warm path retune** — 본 verdict
- ❌ PASS_with_caveat / canary — 미충족 (단일 seed inconclusive 없음)
- ❌ FAIL — 미충족
- ❌ INCONCLUSIVE — 미충족

**운영 결정**: warm path XGB best_params 변경 (default → B-retuned). cold path 변경 X / cold ensemble (CB+XGB) 그대로 유지.

### 4.3 운영 적용 가이드

1. `model_test_results/warm_only_retuned_best_params.json` → 운영 warm artifact 학습 시 XGB params 교체
2. cold ensemble (CB + XGB) artifact는 변경 X
3. Warm path는 e3327ed convention `_warm_mask` filter 후 XGB 단독 학습 / inference 시 `_is_warm_path` 분기에서 새 artifact 사용
4. Shadow logging 권장 (PR2B-prereq.1 정합) — 1주 모니터링 후 default OFF → ON 전환

### 4.4 후속 cycle (선택적)

- **B+D3 결합**: B의 warm retune + D3의 blend ratio 결합 / 단 D3은 본 cycle FAIL → 후속은 stacking meta-learner 등 advanced blend 별도 cycle
- **B 다른 seed multi-seed 확대 검증**: 5 seed 모두 PASS / 추가 N=10 확장은 over-validation 가능성

## 5. 산출물

### 5.1 Commit 대상

- `docs/b_warm_only_optimization_prereg_20260510.md` (R1 LGTM)
- `docs/b_warm_only_optimization_results_20260510.md` (본 문서)
- `scripts/optuna_warm_only_retune.py`
- `model_test_results/warm_only_retuned_best_params.json` (1.0KB / 운영 warm artifact 학습용)
- `data/b_warm_holdout_20260510/seed{541,619,743,829,947}_holdout_indices.json`

### 5.2 .gitignore (artifact)

- `model_test_results/warm_only_optuna_study.json` (50 trials log)
- `model_test_results/b_warm_validation.json` (validation 상세)

## 6. 한계 및 caveat

- **Cold path 영향 X 가정**: warm path는 inference에서 `_is_warm_path` branch로 분리됨 / cold path artifact 변경 없음 / 단 `warm_only_retuned_best_params.json`은 warm artifact 학습 시 default XGB params를 override.
- **TPE seed=42**: stochasticity / re-run 시 best_params 약간 다를 수 있음.
- **N=5 multi-seed**: D1 / D3와 동일 / 본 cycle은 5 PASS 강한 신호.
- **단일 objective**: warm-only / cold metric은 평가 X / 본 cycle scope 외.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | B = third priority | 본 cycle motivation |
| R1 사전 (D3와 combined) | LGTM | 본 prereg 작성 직후 / D3 LGTM과 함께 |
| R2 사후 | (예정) | B 결과 위 검수 / ADOPT verdict 적정성 |

## 8. 결론

B warm-only XGB retune 결과 = **ADOPT_warm_retuned**. Search-time CV 개선 -1.69pp / Validation 5 seed 모두 PASS / 평균 Δ_warm = -1.62pp consistent. 운영 warm path XGB best_params 교체 권고 / cold path 변경 X. 본 cycle은 후속 후보 3건 중 **유일한 운영 적용 가능한 winner**.
