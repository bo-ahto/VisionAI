# D1: N=32 Champion HP Re-optimization (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: Codex 전략 자문 (post-N15 / 3-cycle 종결 후) → top recommendation = D1
> **Decision binding**: ✅ YES — 운영 N=32 champion 의 best_params 교체 결정 직접 근거.

## 1. Goal

본 세션 N=15 follow-up 3-cycle (`8c9e58e` HOLD / `38eab10` HOLD clean negative / `4499fe9` NEEDS_MORE_DATA) 결과 = **N=15 migration line 종결 / N=32 유지**. Codex 전략 자문 권고 = **D1 top choice** (N=15 premise 없이 champion 자체를 직접 attack).

질문: 현 운영 N=32 champion (`integrated_v3_filtered_tuned_best_params.json` 기반 / CB + XGB ensemble / 50/50 blend)의 best_params를 fair operational CV (GroupKFold cold + KFold warm) 위에서 Optuna constrained search로 retune 시, fresh multi-seed holdout에서 strict non-inferiority + warm 비악화를 만족하는 새 best_params 발견 가능한가?

PASS 시 → 운영 best_params 교체 권고 (operational migration / artifact retrain + redeploy).
FAIL 시 → 현 best_params 유지 (retune은 default를 능가 X / 본 axis terminate).

본 cycle = **N=15 premise 없는 base-model 본격 HP search**. Source-Conditional + per-source calibration scope 외 (codex R4 P1 fix / base model gain 분리 측정).

## 2. Method

### 2.1 Search target

**N=32 features 그대로** (`CB_FEATURES_BASE` from `src/visionai/price_engine/api/primary_predictor.py` / 변경 X).

**두 모델 독립 search** (joint 18-dim 대신 sequential 9+9-dim):
1. **Phase 1**: CatBoost (cold path) HP search — 50 trials.
2. **Phase 2**: XGBoost (warm path) HP search — 50 trials.

→ 본 cycle 한정 simplification. Joint optimization은 후속 cycle.

### 2.2 Search space

**CatBoost (cold path)**:

| Parameter | Range | Distribution |
|---|---|---|
| `iterations` | [500, 2000] | int uniform |
| `depth` | [4, 10] | int uniform |
| `learning_rate` | [0.01, 0.2] | log-uniform |
| `l2_leaf_reg` | [1, 10] | uniform |
| `random_strength` | [0, 5] | uniform |
| `bagging_temperature` | [0, 1] | uniform |
| `border_count` | [32, 255] | int uniform |
| `subsample` | [0.5, 1.0] | uniform (when bootstrap_type=Bernoulli) |

**XGBoost (warm path)**:

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

**Sampler**: Optuna TPE (default / `seed=42`).
**Trials**: **50 per phase** (compliant rerun / R4 P1 fix from initial 30-trial run).

### 2.3 Search-time CV

**Cold (CatBoost)**:
- `GroupKFold(n_splits=5)` with `groups=artist_slug` (artist 분리 / N15.B run #3 GroupKFold fix 정합)
- 5-fold CV mean MdAPE = trial primary metric

**Warm (XGBoost)**:
- `_warm_mask` filter 후 `KFold(n_splits=5, shuffle=True, random_state=42)`
- 5-fold CV mean MdAPE = trial primary metric

### 2.4 Optuna Objective + Constraints (R1 P0 fix / ensemble metric)

> **R1 P0 fix**: 각 phase는 deployed ensemble (`(CB+XGB)/2 cold`) metric을 평가. Phase 1 = CB trial × XGB_default. Phase 2 = CB_best_phase1 × XGB trial. CB-only / XGB-only 단독 metric 사용 X (deployed structure mismatch).

**Phase 1 (CatBoost / XGB_default fixed)**:
- **Objective**: minimize `cold_ensemble_cv_mdape` = `MdAPE(y, (CB_trial_pred + XGB_default_pred)/2)` on full data 5-fold GroupKFold (cold)
- **Constraints** (`constraints_func` API / R1 P1 search-time +0.1pp tolerance):
  - `c1`: `cold_ensemble_cv ≤ default_ens_cold + 0.1pp` (search-time loose / validation strict)
  - `c2`: `cold_ensemble_artsy ≤ default_ens_artsy + 0.4pp` (G2 +0.1pp slack)
  - `c3`: `cold_ensemble_saatchi ≤ default_ens_saatchi + 0.4pp` (G3 +0.1pp slack)

**Phase 2 (XGBoost / CB_best_phase1 fixed)**:
- **Objective**: minimize `warm_cv_mdape` = `MdAPE(y_warm, XGB_trial_pred)` on warm-only 5-fold KFold (warm)
- **Constraints** (Phase 1과 cold ensemble guard 구조 동일 / R2 fix):
  - `c1`: `warm_cv ≤ default_xgb_warm + 0.1pp` (search-time loose)
  - `c2`: `cold_ensemble_cv = MdAPE((CB_best_phase1_pred + XGB_trial_pred)/2) ≤ default_ens_cold + 0.1pp` (overall cold non-regression / Phase 1 정합)
  - `c3`: `cold_ensemble_artsy_cv ≤ default_ens_artsy + 0.4pp` (Artsy non-regression)
  - `c4`: `cold_ensemble_saatchi_cv ≤ default_ens_saatchi + 0.4pp` (Saatchi non-regression)

**Best params** = constraint-feasible trial 중 objective minimum (각 phase 별).

**Initial trial** (R1 P2 fix): `study.enqueue_trial(default_params)` Phase 1+2 각각에서 incumbent로 추가. TPE sampler가 default를 first-class trial로 비교.

**CB subsample 활성화 시 bootstrap_type=Bernoulli 고정** (R1 note / underspecified avoid).

### 2.5 Validation (fresh multi-seed / R4 expansion)

`split_seed ∈ {97, 113, 199, 223, 257}` — **N=5 fresh seeds** (R4 권고 multi-seed 확대 / 이전 세션 31337-7-13 / 23-47-71 / 비중복 / 추가 223, 257).

Multi-seed N=3 → N=5 확대 motivation: per-source guard split variance 흡수 (이전 30-trial run에서 PASS×1+FAIL×2 결과의 split variance 본질 진단).

각 seed × 80% pool 위:
1. **Baseline retrain (current best_params / N=32)**:
   - CB cold pool / XGB warm pool / `integrated_v3_filtered_tuned_best_params.json` 그대로
2. **Candidate retrain (new best_params / Phase 1+2 결과)**:
   - CB cold pool with retuned CB params / XGB warm pool with retuned XGB params
3. **20% holdout prediction**:
   - Cold ensemble = (CB + XGB)/2 — both N=32
   - Warm = XGB only

Per-seed metrics:
- `Δ_cold_overall`, `Δ_cold_artsy`, `Δ_cold_saatchi`, `Δ_warm` (candidate − baseline)
- 4 Guard 적용 (Track 1 prereg locked thresholds / N15.A 정합)

### 2.6 Paired Bootstrap CI (REMOVED per R4 P0 amendment)

> **R4 P0 amendment (compliant rerun)**: 본 cycle의 per-source delta granularity (cold_artsy n~1413 / cold_saatchi n~4087 / warm n~5400) 모두 n > 500 → CI threshold 미발동 / sub-cell drill-down (artsy_gallery 등) 본 prereg 範위 외. **Paired bootstrap CI path 본 cycle scope 외**. small-sample uncertainty는 multi-seed N=5 확대 (§2.5)로 흡수.

## 3. Decision Criterion

### 3.1 Per-seed verdict (3-tier / R1 P1 fix / validation strict)

**Validation-time (search-time과 분리)**: search-time +0.1pp tolerance는 exploration용 / validation은 strict 정합.

**PASS**:
- ✅ G1 (Δ_cold_ensemble_overall ≤ 0pp / strict non-inferiority on deployed metric)
- ✅ G2 (Δ_cold_ensemble_artsy ≤ +0.3pp)
- ✅ G3 (Δ_cold_ensemble_saatchi ≤ +0.3pp)
- ✅ G4 (Δ_warm ≤ +0.1pp / warm strict)
- ✅ Δ_cold_ensemble_overall ≤ 0 (strict improvement or zero / migration motivation)

**INCONCLUSIVE**:
- G1-G4 PASS BUT Δ_cold_ensemble_overall ∈ (0, +0.3]pp (no improvement / not strict regression)

**FAIL**:
- 임의 G FAIL
- Δ_cold_ensemble_overall > +0.3pp (regression)
- Δ_warm > +0.1pp (warm regression)

### 3.2 Multi-seed aggregate (R4 amendment / 5 seeds)

| Per-seed 분포 (5 seeds) | Aggregate |
|---|---|
| PASS × 5 | **PASS** (champion 교체 strict 권고) |
| PASS × 4 + INCONCLUSIVE × 1 | **PASS_with_caveat** |
| PASS × 4 + FAIL × 1 | **INCONCLUSIVE** (split variance / 1 outlier) |
| PASS × 3 + 나머지 | **INCONCLUSIVE** (majority pass / split variance significant) |
| FAIL × 3 이상 | **FAIL** |
| 기타 | **INCONCLUSIVE** |

### 3.3 채택 결정 (R6 P1 fix / PASS_with_caveat 매핑 명시)

- **Aggregate PASS** (PASS × 5 strict) → 운영 N=32 best_params 교체 권고 (full champion migration).
- **Aggregate PASS_with_caveat** (PASS × 4 + INCONCLUSIVE × 1) → **canary deployment 후보** (guarded migration / mode=canary 활성화 + shadow logging 비교 후 full migration 결정 / 별도 narrow PR).
- **Aggregate FAIL** → 현 best_params 유지 / **D axis (HP optimization) terminate**.
- **Aggregate INCONCLUSIVE** → multi-seed N 확대 후속 cycle 또는 다른 axis 전환 (선택).

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)
- `docs/d1_n32_champion_hp_reoptimization_prereg_20260510.md` (본 문서)
- `docs/d1_n32_champion_hp_reoptimization_results_20260510.md` (결과 + 채택 결정)
- `scripts/optuna_n32_champion_retune.py` (entry / 2-phase Optuna + validation)
- `model_test_results/n32_champion_retuned_best_params.json` (Phase 1+2 best_params)
- `data/d1_holdout_20260510/seed{97,113,199}_holdout_indices.json` (3 files)

### 4.2 산출물 (gitignored)
- `model_test_results/n32_champion_optuna_study_cb.json` (Phase 1 trials)
- `model_test_results/n32_champion_optuna_study_xgb.json` (Phase 2 trials)
- `model_test_results/d1_validation_20260510.json`

## 5. Out-of-scope

- ❌ N=15 candidate (3-cycle 종결 / 본 cycle = N=32 only)
- ❌ Source-Conditional + calibration 통합 (codex R4 P1 fix / 별도 cycle / 본 cycle = base model gain 분리)
- ❌ Ensemble blend ratio 변경 (D3 cycle 별도)
- ❌ Joint CB+XGB 18-dim Optuna (sequential 9+9 / 본 cycle 한정)
- ❌ Multi-seed N 확대 (3 seeds 고정)
- ❌ Different model architecture (D2 / 별도)

## 6. 한계 / Risk

- **Trial budget 50**: codex 일반 권고 100-200. 50은 lower bound acceptable / TPE convergence 가정. 결과 NEEDS_MORE_DATA 시 100 trials 후속 sensitivity 가능.
- **Sequential 9+9 vs joint 18-dim**: cold-warm interaction 무시 / 단순화. 별도 cycle에서 joint search 검증 가능.
- **Strict non-inferiority (Δ_cold ≤ 0)**: 강한 기준. champion vs candidate 둘 다 같은 80% pool 학습 → 통계적 noise 흡수 X 가능. NEEDS_MORE_DATA 시 +0.1pp 완화 후 재시도.
- **Validation 3 seeds 한정**: split-driven variance fully cover X (N15 series에서 학습됨). PASS×3 strict 통과 시 robust.
- **Default best_params 시작점 not used as Optuna initial trial**: TPE는 random initial / default 사전 정보 없음. enqueue_trial로 default 추가 가능 (개선).
- **Compute estimate**: Phase 1 (CB) ~30-60min / Phase 2 (XGB) ~30-60min / Validation ~30min = ~1.5-2.5시간 wall.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 전략 자문 (post-N15) | D1 = top choice / D3 second / B third / A·C·D2 skip | 본 prereg = D1 진행 |
| 1차 사전 자문 (`019e0bb1` resume) | NEEDS FIX → 반영 완료 | P0: search 객체가 deployed metric mismatch (CB-only / XGB-only 대신 ensemble metric 평가). Phase 1 = CB_trial+XGB_default ensemble cold / Phase 2 = CB_best_phase1+XGB_trial ensemble cold sanity check + warm objective. P1: search-time constraint loose (+0.1pp) / validation strict (+0). P2: enqueue_trial(default_params) incumbent first-class. CB subsample 시 bootstrap_type=Bernoulli 고정. |
| 2차 verification (resume) | NEEDS FIX → 반영 완료 | R2: §2.4 Phase 2 cold ensemble guard structure 가 Phase 1과 inconsistent → c2 (overall +0.1pp) + c3 (artsy +0.4pp) + c4 (saatchi +0.4pp) 추가. |
| 3차 verification (resume) | **LGTM** | Phase 2 constraints 정합 / Phase 1과 cold ensemble guard structure 일관 → **prereg 잠금 / 구현 진입** |
| 4차 사후 검수 (resume) | NEEDS FIX → exploratory pilot downgrade | P0: paired bootstrap CI 미구현 / P1: 30 vs 50 trials deviation. 본 cycle = exploratory pilot / compliant rerun 후 binding. signal 강함 (overall 개선 3/3) / 후속 D1 rerun > D3 > B 우선순위. 상세: results §1, §6 |
| 5차 amendment (compliant rerun prereg fix) | 진행 | P0 fix: §2.6 CI path 제거 (per-source delta n>500이라 미발동 / sub-cell scope 외). P1 fix: 50 trials per phase. R4 expansion: multi-seed N=5 (97/113/199/223/257). §3.2 5-seed aggregate logic. |
| 6차 verification (예정) | (예정) | amendment 5번 검증 후 LGTM 확인 |
| 7차 사후 검수 (compliant rerun) | (예정) | 50-trial × 5-seed 결과 후 binding 결정 |
