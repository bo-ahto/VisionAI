# B: Warm-only Path Optimization (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: Codex 전략 자문 B (post-N15 / third priority / conditional)
> **Decision binding**: ✅ YES — 운영 warm path 단독 deployment 결정 (cold path 변경 X).

## 1. Goal

운영 stack은 cold path (CB+XGB ensemble) + warm path (XGB only). 본 cycle = **cold path 동결 / warm path만 retune** → warm-only 단독 deployment 후보 평가. Codex 전략 자문 B priority — cold/warm 분리 deployment 가능 시 product value 명확.

질문: warm-only XGB Optuna search (cold constraint 없음 / warm objective only)에서 default warm best_params (warm CV 9.70)를 능가하는 새 best_params 발견 가능한가? PASS 시 운영 warm path 단독 retune.

본 cycle = **cold path 영향 X** (CB / XGB cold prediction 변경 X). **Warm path만 별도 deployment**. N=32 features 고정.

## 2. Method

### 2.1 Search target

**XGBoost warm-only HP search**:
- 운영 deployed warm path = XGB만 사용 (e3367ed convention / `_warm_mask` filtered training)
- Warm CV objective only (no cold constraints / no ensemble metric / clean single-objective)

**Cold path 동결**:
- 본 cycle은 cold path 모델 변경 X / 평가 X
- 운영 ensemble = (CB_default + XGB_default)/2 cold + XGB_warm_retuned warm

### 2.2 Search space (N15.B / D1과 동일)

| Parameter | Range | Distribution |
|---|---|---|
| `num_boost_round` | [500, 4000] | int uniform |
| `max_depth` | [4, 10] | int uniform |
| `learning_rate` | [0.01, 0.2] | log-uniform |
| `subsample` | [0.6, 1.0] | uniform |
| `colsample_bytree` | [0.6, 1.0] | uniform |
| `min_child_weight` | [1, 20] | int uniform |
| `gamma` | [0, 0.5] | uniform |
| `reg_alpha` | [0, 1.0] | uniform |
| `reg_lambda` | [0, 5.0] | uniform |

**Sampler**: TPE / `seed=42` / Optuna constraints API.
**Trials**: **50** (D1 compliant 정합).
**enqueue_trial**: default warm params.

### 2.3 Search-time CV

**Warm CV**: `_warm_mask` filter 후 `KFold-5(random_state=42)` (e3367ed warm convention 정합).

### 2.4 Objective + Constraints

**Objective**: minimize `warm_cv_mdape` (5-fold KFold mean).

**Constraints**:
- `c1`: `warm_cv ≤ default_warm + 0.1pp` (search-time loose / strict +0 validation)

**No cold constraints**: cold path 영향 X / 평가 X / 본 cycle scope 외.

### 2.5 Validation (fresh multi-seed N=5)

`split_seed ∈ {541, 619, 743, 829, 947}` — **새 seeds** (D1, D3 비중복).

각 seed × 80% warm pool 위:
1. **Baseline retrain**: warm pool로 default params XGB warm 학습.
2. **Candidate retrain**: warm pool로 retuned params XGB warm 학습.
3. **20% warm holdout 위** prediction:
   - baseline_warm_mdape
   - candidate_warm_mdape
4. **Δ_warm = candidate − baseline** per seed.

### 2.6 Per-source warm metrics (보조 / record)

Per-source warm MdAPE (artsy_warm / saatchi_warm) 별도 record. 본 cycle decision-binding은 overall warm. per-source는 후속 분석용.

## 3. Decision Criterion

### 3.1 Per-seed verdict

**PASS**:
- ✅ Δ_warm ≤ 0 (strict non-inferiority on warm-only)

**INCONCLUSIVE**:
- Δ_warm ∈ (0, +0.1pp] (small regression / acceptable margin)

**FAIL**:
- Δ_warm > +0.1pp

### 3.2 Multi-seed aggregate (5 seeds)

| Per-seed 분포 | Aggregate |
|---|---|
| PASS × 5 | **PASS** (warm migration full) |
| PASS × 4 + INCONCLUSIVE × 1 | **PASS_with_caveat** (canary) |
| FAIL × 3 이상 | **FAIL** |
| 기타 | **INCONCLUSIVE** |

### 3.3 채택 결정

- PASS → 운영 warm path retune (XGB warm best_params 변경) / cold path 변경 X.
- PASS_with_caveat → warm canary deployment.
- FAIL → 운영 warm 유지 / B axis terminate.
- INCONCLUSIVE → multi-seed 확대 후속 cycle.

## 4. Output

- `docs/b_warm_only_optimization_prereg_20260510.md` (본 문서)
- `docs/b_warm_only_optimization_results_20260510.md`
- `scripts/optuna_warm_only_retune.py`
- `model_test_results/warm_only_retuned_best_params.json` (commit 대상)
- `data/b_warm_holdout_20260510/seed{541,619,743,829,947}_holdout_indices.json`
- (gitignored) `model_test_results/warm_only_optuna_study.json`
- (gitignored) `model_test_results/b_warm_validation.json`

## 5. Out-of-scope

- ❌ Cold path 변경 (cold model / cold params / cold features)
- ❌ Ensemble blend ratio (D3 별도)
- ❌ N≠32 (D1과 동일 feature contract)
- ❌ Source-conditional warm
- ❌ Multi-objective Pareto

## 6. 한계 / Risk

- **No cold sanity check**: cold path 영향 X 가정 / 단 retuned warm이 ensemble cold path에 영향 미칠 가능성 X (XGB warm은 별도 path / cold ensemble = (CB_cold + XGB_cold)/2와 분리). 본 cycle은 deployed warm-only path 변경.
- **Single objective + no constraints**: clean / simple. constraint-feasible space empty risk 없음.
- **N=5 multi-seed**: D1 amendment 정합.
- **Compute estimate**: warm CV는 cold ensemble보다 light. 50 trials × ~30s/trial = ~25 min. validation 5 seeds × ~10s = ~1 min. Total ~30 min wall.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | B = third priority | 본 cycle motivation |
| 1차 사전 자문 | (예정) | 본 prereg 작성 직후 |
| 2차 verification | (if NEEDS FIX) | R1 반영 |
| 3차 사후 검수 | (예정) | B 결과 후 / 채택 결정 |
