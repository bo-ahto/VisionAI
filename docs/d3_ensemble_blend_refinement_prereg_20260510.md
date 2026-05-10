# D3: Ensemble Blend/Stacking Refinement (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: Codex 전략 자문 D3 (post-N15 / second priority) → D1 compliant rerun 후 진행
> **Decision binding**: ✅ YES — 운영 ensemble blend ratio 변경 결정 직접 근거.

## 1. Goal

현 운영 ensemble = **`(CB_pred + XGB_pred) / 2`** (50/50 blend / arbitrary). Codex 전략 자문 권고: "current `(CB + XGB) / 2` is arbitrary. Weighting or simple stacking could produce gain without feature-contract drama."

질문: OOF blend-weight search로 50/50보다 나은 weight `w*` 발견 가능한가? `(w * CB + (1−w) * XGB)`에서 `w ∈ [0, 1]` scalar 또는 더 복잡한 stacking meta-learner.

PASS 시: 운영 blend ratio 변경 (50/50 → `w*` / 50)).
FAIL 시: 50/50 유지 / D3 axis terminate.

본 cycle = **default base_params 그대로** (D1 retune 별도 / blend axis 분리). N=32 feature contract 그대로.

## 2. Method

### 2.1 Search target

**Blend weight scalar** `w ∈ [0, 1]`:
- Cold ensemble = `w * cb_cold_pred + (1-w) * xgb_cold_pred`
- Warm path 변경 X (XGB-only / e3367ed convention 정합)

**Stacking meta-learner (보조 endpoint / 본 cycle scope 외 / record-only)**:
- 본 cycle은 scalar w만 binding. 별도 advanced stacking은 후속 cycle (e.g., source-conditional w / category-conditional 등).

### 2.2 OOF Generation (default params / N=32 features)

5-fold cross-validated OOF predictions on full data:
- **Cold OOF**: `GroupKFold-5(artist_slug)` / CB (default params) train+predict on each fold → cb_oof_cold[N]
- **Cold XGB OOF**: 같은 fold split / XGB (default params) → xgb_oof_cold[N]
- **Warm OOF**: `_warm_mask` filter + `KFold-5(random_state=42)` / XGB → xgb_oof_warm[N_warm]

### 2.3 Blend weight 1D Search

Cold OOF 위에서 `w` grid search:
- `w ∈ {0.0, 0.05, 0.10, ..., 0.95, 1.0}` (21-point grid)
- objective: `MdAPE(y_price, w * cb_oof + (1-w) * xgb_oof)` (overall cold)
- 추가 record (per-source): cold_artsy_mdape / cold_saatchi_mdape per w
- **Best w** = overall cold MdAPE 최소 + per-source non-regression constraint

### 2.4 Per-source non-regression constraint

`w*` 후보 trial 별도 평가:
- `cold_artsy(w*) ≤ cold_artsy(0.5) + 0.3pp` (G2)
- `cold_saatchi(w*) ≤ cold_saatchi(0.5) + 0.3pp` (G3)

Constraint 위반 시 해당 w trial reject. 만족하는 w 중 cold overall 최소 = `w*`.

### 2.5 Validation (fresh multi-seed N=5)

`split_seed ∈ {127, 233, 269, 311, 419}` — **새 seeds** (이전 사이클 비중복 / D1, OOS, N15 series 모두 사용 X).

각 seed × 80% pool 위:
1. 80% pool로 default params CB + XGB 학습 (D1 baseline retrain과 동일 방법론)
2. 20% holdout 위 predict
3. Two ensemble computations:
   - **baseline_ens** = `0.5 * cb_pred + 0.5 * xgb_pred` (현 운영)
   - **candidate_ens** = `w* * cb_pred + (1-w*) * xgb_pred` (D3 winner)
4. Per-cell MdAPE: cold_overall / cold_artsy / cold_saatchi / warm (warm = XGB only / 변경 X)
5. Δ_blend = candidate − baseline per cell

## 3. Decision Criterion

### 3.1 Per-seed verdict (3-tier)

**PASS**:
- ✅ G1 (Δ_cold_overall ≤ 0pp / strict) 
- ✅ G2 (Δ_cold_artsy ≤ +0.3pp)
- ✅ G3 (Δ_cold_saatchi ≤ +0.3pp)
- (G4 warm 변경 X / 평가 X)

**INCONCLUSIVE**:
- G1-G3 PASS BUT Δ_cold_overall ∈ (0, +0.3]pp

**FAIL**:
- 임의 G FAIL
- Δ_cold_overall > +0.3pp

### 3.2 Multi-seed aggregate (5 seeds)

| Per-seed 분포 | Aggregate |
|---|---|
| PASS × 5 | **PASS** (full migration) |
| PASS × 4 + INCONCLUSIVE × 1 | **PASS_with_caveat** (canary) |
| FAIL × 3 이상 | **FAIL** |
| 기타 | **INCONCLUSIVE** |

### 3.3 채택 결정

- PASS → 운영 blend ratio 변경 (50/50 → w*).
- PASS_with_caveat → canary deployment + shadow logging.
- FAIL → 50/50 유지.
- INCONCLUSIVE → multi-seed 확대 또는 다른 방법 (stacking 등).

## 4. Output

- `docs/d3_ensemble_blend_refinement_prereg_20260510.md` (본 문서)
- `docs/d3_ensemble_blend_refinement_results_20260510.md`
- `scripts/d3_blend_search.py`
- `data/d3_holdout_20260510/seed{127,233,269,311,419}_holdout_indices.json`
- (gitignored) `model_test_results/d3_blend_search_results.json`

## 5. Out-of-scope

- ❌ HP retuning (D1 별도)
- ❌ Stacking meta-learner (linear regression / xgboost stacker / 등 / 별도 cycle)
- ❌ Source-conditional blend weight (artsy w_a / saatchi w_s / 별도)
- ❌ Warm path blend (XGB only / 변경 X)
- ❌ Different feature N

## 6. 한계 / Risk

- **Scalar w only**: 1D search라 단순. category-conditional 또는 stacking은 후속.
- **Default base params**: D1 결과 X / blend axis 분리. D1+D3 결합 cycle은 후속.
- **OOF leakage 주의**: blend weight는 OOF predictions 위에서 search → fold-level leakage 없음. 단 validation은 OOF가 아닌 fresh holdout으로 분리.
- **Compute light**: ~30 min wall (5-fold OOF generation + 21-point grid search + 5-seed validation).

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | D3 = second priority | 본 cycle motivation |
| 1차 사전 자문 | (예정) | 본 prereg 작성 직후 |
| 2차 verification | (if NEEDS FIX) | R1 반영 |
| 3차 사후 검수 | (예정) | D3 결과 후 / 채택 결정 |
