# D1.Arch.tuned: Tuned LightGBM Cold-Only Optuna Search (R1 amendment / decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: D1.Arch (commit `05859bd`) `default_LGBM_insufficient` (R1 Q4 trigger / **last LGBM attempt** / not architecture axis last test)
> **Decision binding**: ✅ YES — Tuned LGBM cold replacement 채택 결정 (canary level cap)
> **R1 amendment 반영** (codex P0 + P1×2):
> - P0 fix: Optuna search-time source constraints (artsy / saatchi cold non-regression)
> - P1.1 fix: FAIL = **"tuned_LGBM_insufficient"** only (not architecture-independent / VFR가 non-GBDT 별도 axis 명시)
> - P1.2 fix: **PR-WARM-B는 본 cycle 결과와 무관하게 primary deployment track / D1.Arch.tuned가 preempt X**

## 1. Goal

본 세션 cold path 6 cycles 누적 fail. Codex R1 (D1.Arch) Q4 답변:
> "INCONCLUSIVE/FAIL → maybe tuned LGBM follow-up is the right reading"
> "Architecture-independent confirmed" 결론은 **tuned LGBM도 fail 시만 reserve**

본 cycle = **architecture axis last test** (D1.Arch FAIL의 narrow interpretation 해소):

질문: Optuna-tuned LGBM이 default LGBM 한계 극복 가능한가? Tuned LGBM cold replacement이 strict per-seed framework PASS인가?

PASS 시 → cold architecture matters / **PROMOTE_TO_TUNING_AND_CANARY** (LGBM HP retune 정당화 / canary deploy / 후속 implementation validation cycle).
FAIL 시 → **`architecture-independent confirmed`** (R1 P1.1 reserve 발동 / cold path 본질 한계 / cold retune 모든 axis 종결 / B-only deploy path 확정).
INCONCLUSIVE 시 → 추가 후속 cycle 또는 deeper architecture (Bayesian / Quantile) 후보.

## 2. Method

### 2.1 LGBM Optuna search (R2 amendment / search space narrowed)

**Search space (R2 amendment / 1차 run 180min stuck → narrow 후 재실행)**:

| Parameter | Range | 1차 (killed at 180min) | R2 (narrow) |
|---|---|---|---|
| `num_leaves` | int log-uniform | [16, 256] | **[16, 64]** |
| `learning_rate` | log-uniform | [0.01, 0.2] | [0.01, 0.2] (그대로) |
| `feature_fraction` | uniform | [0.6, 1.0] | [0.6, 1.0] (그대로) |
| `bagging_fraction` | uniform | [0.6, 1.0] | [0.6, 1.0] (그대로) |
| `bagging_freq` | int uniform | [1, 10] | [1, 10] (그대로) |
| `min_data_in_leaf` | int uniform | [10, 100] | [10, 100] (그대로) |
| `lambda_l1` | uniform | [0, 1.0] | [0, 1.0] (그대로) |
| `lambda_l2` | uniform | [0, 5.0] | [0, 5.0] (그대로) |
| `num_boost_round` | int uniform | [500, 2000] | **[500, 1000]** |
| **n_trials** | — | **50** | **20** |

**근거 (R2 amendment)**:
- 1차 run 180분 시점 stuck (num_leaves 256 + num_boost_round 2000 worst-case combo가 trial 당 4-6분 → 50 trials × 5-fold 미완료)
- Narrow space (num_leaves max 64 / boost max 1000) → trial 당 ~60-90s / 20 trials × 5-fold ≈ 30-40min
- LGBM standard tuning에서 num_leaves=64는 일반적 / num_boost_round=1000도 적정 / 본 dataset (28k rows)에 충분

**Optuna sampler**: TPESampler / `seed=42` / 50 trials.
**Objective**: cold_overall MdAPE on `GroupKFold-5(artist_slug)` (D1.X / D1.Arch 정합 / scalar).
**Constraints (R1 P0 amendment / search-time source feasibility)**:
- `c1`: `cold_artsy_cv ≤ default_cb_artsy_cv + 0.3` (G2 정합)
- `c2`: `cold_saatchi_cv ≤ default_cb_saatchi_cv + 0.3` (G3 정합)
- Constraint violation 시 trial reject (Optuna constraints API)
- **근거**: 본 cycle validation은 G1+G2+G3 strict / search도 같은 feasibility 적용 필요 (codex P0 / "improve aggregate while blowing up source" 회피)

**enqueue_trial**: D1.Arch default LGBM params (incumbent first-class comparison).

### 2.2 Search-time CV (R1 P0 amendment)

`GroupKFold-5(artist_slug=1551 groups)` cold만 (warm 변경 X / R1 P0 cold-only 정합):

각 fold:
1. Train LGBM on 80% fold_train (with trial params)
2. Predict on 20% fold_test
3. Per-fold MdAPE collect: cold_overall / cold_artsy / cold_saatchi
4. Trial objective = mean cold_overall MdAPE across 5 folds (single scalar)
5. **Constraints (R1 P0)**: c1 = mean cold_artsy ≤ default_cb_artsy + 0.3 / c2 = mean cold_saatchi ≤ default_cb_saatchi + 0.3 / 위반 시 reject

**Search-time validation 정합 보존**: validation에서 G2 (artsy ≤+0.3) / G3 (saatchi ≤+0.3) 적용되므로 search도 same feasibility / codex P0 "blowing up source" 회피.

### 2.3 Fresh seeds (N=10 / D1.Arch와 다른 seeds)

`split_seed ∈ {1301, 1303, 1307, 1319, 1321, 1327, 1361, 1373, 1381, 1399}` — 모두 prime / 이전 cycle 비중복:

| Seed | D1.X | D1.Y | B | D3 | D3.B | D1-ext | D1.SC | D1.Arch | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| 1301-1399 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 모두 fresh |

### 2.4 Validation 절차 (D1.Arch / D1.SC 정합)

각 seed × 80/20 split (cold: GroupShuffleSplit / warm: row split):

**Candidate (Tuned LGBM cold + freeze warm)**:
- LGBM cold = LGBM 학습 on 80% cold pool with **Optuna best_params**
- Warm = default XGB freeze (R1 P0 / B와 orthogonal)
- Cold inference: LGBM cold (CB 대체)
- Warm inference: default XGB warm

**Baseline (default CB cold + freeze warm)**:
- CB cold = default CB on 80% cold pool
- Warm = default XGB freeze (shared with candidate)

**Per-cell MdAPE (cold만 / warm Δ=0 by design / D1.SC / D1.Arch 정합)**:
- cold_overall / cold_artsy / cold_saatchi
- Δ_cell = candidate − baseline

### 2.5 Strict Primary endpoint (D1.Y / D1.Arch 정합)

Per-seed verdict (G1-G3 / G4 무관 / warm freeze):
- PASS: G1 (Δ_cold_overall ≤ 0) + G2 (artsy ≤+0.3) + G3 (saatchi ≤+0.3)
- INCONCLUSIVE: Δ_cold_overall ∈ (0, +0.3] + G2/G3 PASS
- FAIL: 임의 G FAIL

N=10 aggregate (D1.Y R1 P1.1):
- PASS × 10 → PASS
- PASS × 9 + 1 outlier → PASS_with_caveat
- PASS × 8 + INCONCLUSIVE × 2 (FAIL=0) → PASS_with_caveat
- FAIL × 2 이상 → FAIL
- 기타 → INCONCLUSIVE

### 2.6 Bootstrap CI Secondary corroboration (VFR / D1.Arch 정합)

N=10 paired percentile bootstrap on mean Δ per cell / hierarchical (cold_overall primary) / not binding alone.

### 2.7 Combined decision (R1 amendment 정합 / cap at canary)

**D1.Arch와 동일 cap (codex P1.2 정합)**:

| Strict Primary | Bootstrap | Combined |
|---|---|---|
| PASS | bootstrap_PASS | **PROMOTE_TO_TUNING_AND_CANARY** (canary deploy + implementation validation cycle 후속) |
| PASS | bootstrap_INC/FAIL | ADOPT_lgbm_canary (보수적) |
| PASS_with_caveat | bootstrap_PASS | ADOPT_lgbm_canary |
| INCONCLUSIVE | any | NEEDS_MORE_DATA / 후속 deeper architecture 후보 |
| **FAIL** | any | **`tuned_LGBM_insufficient`** (R1 P1.1 narrow / non-GBDT family axis 후보 / cold path 완전 abandon X) |

**핵심 (R1 P1.1 amendment / narrow scope)**:
- D1.Arch FAIL = "default LGBM insufficient" only
- D1.Arch.tuned FAIL = **`tuned_LGBM_insufficient`** only (codex P1.1 narrow)
- "Architecture-independent" claim은 **non-GBDT family (Bayesian / Quantile / NN) 별도 cycles 후** reserved
- VFR §10에서 architecture change axis 항목 다양 명시 (LGBM은 그 중 하나)
- 본 cycle은 **last LGBM attempt** (not architecture last test)

## 3. PR-WARM-B priority (R1 P1.2 amendment / strong statement)

**🔒 PR-WARM-B는 본 cycle 결과와 무관하게 primary deployment track / D1.Arch.tuned가 preempt X**:

본 cycle은 cold-only speculative axis / B는 5/5 PASS unique winner / 본 cycle이 어떤 결과 (PASS / FAIL / INCONCLUSIVE)이든 **B Stage 3-5 운영 deploy priority 변경 없음**:

| D1.Arch.tuned 결과 | Cold path 영향 | B (PR-WARM-B) 영향 |
|---|---|---|
| PASS | tuned LGBM cold canary / 별도 implementation cycle | **변경 X / Stage 3-5 그대로 priority** |
| FAIL (`tuned_LGBM_insufficient`) | cold default 유지 / non-GBDT axis 후속 후보 | **변경 X / Stage 3-5 그대로 priority** |
| INCONCLUSIVE | 추가 cycle 검토 | **변경 X / Stage 3-5 그대로 priority** |

**Orthogonal 보존** (R1 P0 정합):
- D1.Arch.tuned = cold-only / warm = default XGB freeze
- B = warm-only retune / cold = default 유지
- 운영 deploy 시 (PASS 시) tuned LGBM cold + B-retuned warm 결합 가능 / 단 B priority 우선 / D1 cold는 sequential

## 4. Output

- `docs/d1_arch_tuned_lgbm_optuna_prereg_20260510.md` (본 문서)
- `docs/d1_arch_tuned_lgbm_optuna_results_20260510.md`
- `scripts/d1_arch_tuned_lgbm.py` (Optuna 50 trials + N=10 validation)
- `data/d1_arch_tuned_holdout_20260510/seed{1301-1399}_holdout_indices.json`
- (gitignored) `model_test_results/d1_arch_tuned_optuna_study.json`
- (gitignored) `model_test_results/d1_arch_tuned_results.json`
- (force-add 후보) `model_test_results/lgbm_tuned_best_params.json` (PASS 시 deploy artifact)

## 5. Out-of-scope

- ❌ Cold + warm joint LGBM tuning (cold-only / R1 P0 정합 / D1.Arch 정합)
- ❌ Calibration 적용 (raw output / D1.SC / D1.Arch 정합)
- ❌ Source-conditional LGBM (D1.SC fail 정합 / 별도 cycle 후보)
- ❌ Architecture 외 axis (Bayesian / Quantile 별도)

## 6. 한계 / Risk

- **Last LGBM attempt 무게** (R2 amendment): 본 cycle FAIL = "tuned_LGBM_insufficient" only / "cold path 완전 abandon" 결정 X / non-GBDT family (Bayesian / Quantile / NN) axis 별도 cycles 후 architecture-axis 종합 결정
- **N=10 small**: split variance 큼 / 단 D1.Arch와 동일 framework
- **Compute**: Optuna 50 trials × 5-fold CV ≈ ~25-30분 / N=10 validation ≈ ~5-7분 / total ~30-40분
- **artsy direction promising in D1.Arch**: mean -1.80 / tuned LGBM도 artsy negative 가능성 / 단 saatchi side 위험 (D1.Arch +0.73)
- **Codex Q7 strong recommendation context**: D1 abandon / B Stage 5 priority / 본 cycle은 last LGBM attempt (not architecture last test) / FAIL 가능성 큼 (default 결과 정합) BUT non-GBDT axis 가능성 보존

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **NEEDS FIX** | P0 (search-time source constraints) + P1.1 (FAIL narrow / tuned LGBM only) + P1.2 (B priority 명시) |
| **R2 사전 (post-amendment)** | **LGTM** | amendment 정합 |
| **R3 사전 (stale text 정정)** | **LGTM** | §6 / §8 정정 |
| R4 (search space narrow / 1차 180min stuck 후) | (정합) | n_trials 50→20 / num_leaves max 256→64 / boost max 2000→1000 / 시간 효율성 / search 효과 보존 |
| R5 사후 | (예정) | 결과 검수 / 채택 결정 |

**R1 amendment 반영 항목**:
1. **P0 fix (§2.1 / §2.2)**: Optuna search-time source constraints 추가 (c1: artsy ≤ default+0.3 / c2: saatchi ≤ default+0.3 / Optuna constraints API)
2. **P1.1 fix (§2.7)**: FAIL = "tuned_LGBM_insufficient" only / "architecture-independent confirmed"는 non-GBDT family (Bayesian / Quantile / NN) 별도 cycles 후 reserved
3. **P1.2 fix (§3)**: PR-WARM-B priority strong statement / 본 cycle 결과 무관하게 B Stage 3-5 그대로

## 8. 결론 (R1 amendment 정합)

D1.Arch.tuned = **last LGBM attempt** (D1.Arch FAIL의 narrow → tuned로 R1 Q4 trigger 해소).

PASS 시 → tuned LGBM cold matters / canary deploy + implementation validation 후속 / **단 B priority 그대로**.
FAIL 시 → **`tuned_LGBM_insufficient`** (R1 P1.1 narrow / not architecture-independent) / non-GBDT family (Bayesian / Quantile / NN) 별도 axis 후보.
INCONCLUSIVE → 추가 cycle 또는 non-GBDT architecture 후보.

**🔒 PR-WARM-B priority unchanged** (R1 P1.2 / 어떤 결과이든 B Stage 3-5 그대로).

**Compute**: ~30-40분 wall (Optuna 50 trials cold-only with constraints / N=10 validation).
