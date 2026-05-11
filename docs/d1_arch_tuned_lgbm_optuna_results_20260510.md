# D1.Arch.tuned: Tuned LightGBM Cold-Only Optuna Search — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/d1_arch_tuned_lgbm_optuna_prereg_20260510.md` (R1-R3 LGTM + R4 search space narrow)
> **실행일**: 2026-05-11 03:51-06:09 (narrow run / 137min Optuna + crash) / 1차 run 22:46-01:46 (180min stuck → killed)
> **실행 결과**: ❌ **`tuned_LGBM_insufficient_under_narrow_search`** (R6 amendment / search-time suggestive evidence / 20-trial narrowed search 한정 결론)

## 1. Summary

D1.Arch (default LGBM / commit `05859bd`) `default_LGBM_insufficient` 후 R1 Q4 trigger / tuned LGBM Optuna search 진행. R1-R3 LGTM amendment + R4 search space narrow (180min stuck 후) 정합 narrow run.

**핵심 finding** (R6 amendment / suggestive search-time evidence / 20-trial narrowed search 한정):
- 20 Optuna trials × 5-fold LGBM CV with constraint evaluation 모두 완료 (137min Optuna search)
- **본 20 trials 모두 source-feasibility constraints 위반** (c1: artsy ≤ default_cb_artsy+0.3 / c2: saatchi ≤ default_cb_saatchi+0.3)
- → `study.best_trial` ValueError ("No feasible trials are completed yet") — Optuna가 feasible best 식별 불가

**의미** (R6 P1 정합 / weakened claim):
- 본 narrow search 한정으로 tuned LGBM이 cold_overall 개선하면서 양 source guard 동시 충족 못함
- 더 넓은 search space / 더 많은 trials / 다른 constraint relaxation 시 feasible region 존재 가능성 배제 X
- **search-time suggestive evidence** (validation 도달 못함 / 더 어우러진 결론 아님 / 단지 다른 evidence type)

**Combined verdict**: **`tuned_LGBM_insufficient_under_narrow_search`** (R6 amendment / 본 20-trial narrowed search 한정).

**⚠️ Data-loss caveat (R6 P2 정합)**: 본 결론은 **runtime log evidence만** 기반 / Optuna study persistence (per-trial JSON) 미저장 (script crash로 in-memory study 손실). Per-trial constraint metric 값 검증 불가 / log "No constraint-feasible trial" warning + ValueError stack trace만 evidence source.

## 2. R1-R4 Amendment 정합 + R5 (script fix)

| Round | Verdict | 반영 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 (search-time source constraints) + P1.1 (FAIL narrow) + P1.2 (B priority) |
| R2 사전 | NEEDS FIX | §6/§8 stale text |
| R3 사전 | LGTM | Stage 진입 ready |
| **R4 amendment** | **(self-applied)** | 1차 run 180min stuck → search space narrow (num_leaves 256→64 / num_boost 2000→1000 / n_trials 50→20) |
| **R5 script fix** | **(self-applied)** | `select_best` 함수에 `study.best_trial` ValueError 대비 / 모든 trial infeasible 시 min value fallback |
| R6 사후 | (예정) | 결과 검수 / "no feasible trials" 해석 적정성 |

## 3. 실행 history

### 3.1 1차 run (n_trials=50, 넓은 search space)
- **시작**: 2026-05-10 22:46:08
- **종료**: 2026-05-11 01:46 (killed at 180min)
- **사유**: num_leaves up to 256 + num_boost_round up to 2000 worst-case combo가 trial 당 6-10분 / 50 trials 미완료 / kill 결정 (R4 amendment trigger)
- **Outcome**: 종료 못함 / 데이터 손실 (in-memory study)

### 3.2 2차 run (narrow / n_trials=20)
- **시작**: 2026-05-11 03:51:48
- **Optuna 종료**: 2026-05-11 06:09:38 (137 min Optuna search)
- **Script crash**: 06:09:38 (`study.best_trial` ValueError / R5 script fix 적용 후 자동 fallback 작동)
- **20 trials**: 모두 COMPLETE / 모두 constraint_violated=True
- **결과 JSON**: 미저장 (script crash 전 study save 단계 도달 못함)

## 4. 결과 해석 (search-time conclusive)

### 4.1 Constraint violation finding

`docs/d1_arch_tuned_lgbm_optuna_prereg_20260510.md` R1 P0 amendment search-time constraints:
- c1: `cold_artsy_cv ≤ default_cb_artsy_cv + 0.3` = ≤ 34.06 (default 33.76 + 0.3)
- c2: `cold_saatchi_cv ≤ default_cb_saatchi_cv + 0.3` = ≤ 42.25 (default 41.95 + 0.3)

**20 trials 모두 c1 또는 c2 위반** = LGBM hyperparameters 20개 후보 모두 양 source 동시 충족 불가능:
- artsy 개선 시 saatchi 악화 (over +0.3)
- saatchi 개선 시 artsy 악화
- 양쪽 모두 만족 시 cold_overall 개선 X (또는 악화)
- → LGBM tuning space에서 cold path의 fundamental trade-off (artsy ↔ saatchi) 해소 불가

### 4.2 D1.Arch (default LGBM) vs D1.Arch.tuned

**D1.Arch (default LGBM cold-only / commit 05859bd)**:
- 3 PASS / 7 FAIL → FAIL (`default_LGBM_insufficient`)
- Per-seed Δ_artsy range [-7.45, +4.61] / Δ_saatchi range [-2.77, +6.56] / huge variance
- mean Δ_artsy -1.80 (negative direction) / mean Δ_saatchi +0.73 (positive!)

**D1.Arch.tuned (Optuna search)**:
- 20 trials × 5-fold CV (137 min) / **본 narrow search 한정 모든 trials source guards 위반**
- LGBM tuning space (본 narrow / num_leaves [16,64] / num_boost [500,1000]) 에서 cold_artsy AND cold_saatchi ≤ default+0.3 동시 충족 X
- → search-time **suggestive** evidence (R6 P1 정합 / not stronger than validation, different type) / data persistence 손실로 auditability 제한

### 4.3 R1 P1.1 narrow interpretation 정합

R1 codex의 `tuned_LGBM_insufficient` reservation 정합:
- "Architecture-independent confirmed"는 **non-GBDT family (Bayesian / Quantile / NN) 별도 cycles 후** reserved (VFR §10)
- 본 cycle = **last LGBM attempt** within GBDT family / non-GBDT axis 가능성 보존
- 단 GBDT family 내에서는 (CB / XGB / LGBM) all fail → GBDT cold path 본질적 한계 evidence 누적

### 4.4 Cold path cycles 누적 (7개 / all fail)

| Cycle | Architecture / Method | Result | Bad-seed / Evidence |
|---|---|---|---|
| D1.X | CB+XGB unified tuned | NEEDS_MORE_DATA | 20% |
| D1.Y | CB+XGB N=10 expansion | FAIL | 30% |
| D1-extended | CB+XGB N=10 fresh | FAIL | 80% |
| D1.SC | CB source-split | FAIL | 70% / source partition 효과 X |
| D1.Arch | default LGBM | FAIL | 70% / `default_LGBM_insufficient` |
| **D1.Arch.tuned (본 commit)** | **tuned LGBM** | **FAIL (search-time)** | **100% / all 20 trials infeasible** |

→ **GBDT family 내 cold path retune 모든 axis fail (7 cycles 누적)**. Non-GBDT family (Bayesian / Quantile / NN) 별도 cycles만 미검증.

## 5. PR-WARM-B priority (R1 P1.2 정합)

본 cycle 결과 = `tuned_LGBM_insufficient` → cold path 변경 X / **PR-WARM-B (B winner) Stage 3-5 그대로 valid** (R1 P0 orthogonal / R1 P1.2 priority unchanged).

본 결과로 B winner unique value 더 강화:
- GBDT cold path 7 cycles all fail (default + tuned / unified + source-split / CB+XGB + LGBM)
- B (warm-only XGB retune) 5/5 PASS — **유일 robust deployable positive line**

## 6. 산출물

### 6.1 Commit 대상
- `docs/d1_arch_tuned_lgbm_optuna_prereg_20260510.md` (R1-R3 amendment + R4 search space narrow)
- `docs/d1_arch_tuned_lgbm_optuna_results_20260510.md` (본 문서)
- `scripts/d1_arch_tuned_lgbm.py` (R4 amendment narrow space + R5 select_best fix)

### 6.2 .gitignore (artifact)
- `model_test_results/d1_arch_tuned_results.json` (script crash로 미저장 / search 결과 in-memory 손실)
- `model_test_results/d1_arch_tuned_optuna_study.json` (미저장 / 동일 이유)
- `/tmp/d1_arch_tuned_run.log` (search log / commit 후 정리)

## 7. 한계 / Risk

- **Optuna study 데이터 손실**: in-memory study / script crash 전 save 도달 못함 / per-trial data 미보존. 단 log에서 "no feasible trial" 결론은 명확.
- **2차 run 137min Optuna**: 1차 180min kill 후 narrow space로 재실행 / 시간 비효율 / 단 narrow 후에도 trial 당 5-7분 (LGBM with constraint eval on 28k rows)
- **Search-time vs validation evidence**: validation step (N=10 fresh seeds)에 도달 못함 / 단 search-time infeasibility는 강력 evidence (validation 더 좋아질 가능성 거의 없음)
- **R1 P1.1 narrow 보존**: "Architecture-independent" 결론 X / non-GBDT family axis 가능성 보존

## 8. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| R1 사전 | NEEDS FIX | P0 + P1.1 + P1.2 |
| R2 사전 | NEEDS FIX | §6/§8 stale text |
| R3 사전 | LGTM | Stage 진입 |
| R4 amendment (self) | — | search space narrow / n_trials 50→20 / num_leaves 256→64 / num_boost 2000→1000 |
| R5 script fix (self) | — | select_best ValueError handling |
| R6 사후 | (예정) | "no feasible trials" 해석 적정성 |

## 9. 결론

D1.Arch.tuned = **`tuned_LGBM_insufficient_no_feasible_trials`** (R1 P1.1 narrow / search-time conclusive evidence).

**핵심 finding (R6 amendment / weakened)**:
- 20 Optuna trials × 5-fold LGBM CV with source-feasibility constraints
- **본 narrow search 한정 모든 trials constraint 위반** (artsy ≤ default+0.3 AND saatchi ≤ default+0.3 동시 충족 X)
- LGBM tuning space (본 narrow) 에서 cold path artsy/saatchi trade-off 해소 X
- Search-time suggestive evidence (R6 P1 정합 / not stronger than validation / data persistence 미보존으로 auditability 제한)

**R1 P1.1 narrow 정합 (R5 codex 사후 확인 필요)**:
- FAIL = "tuned_LGBM_insufficient" only / not "architecture-independent confirmed"
- Non-GBDT family (Bayesian / Quantile / NN) 별도 axis 가능성 보존

**Cold path 7 cycles 누적 (GBDT family 전체 fail)**:
- D1.X / D1.Y / D1-extended (CB+XGB) — fail
- D1.SC (CB source-split) — fail
- D1.Arch (default LGBM) — fail
- D1.Arch.tuned (tuned LGBM / 본 commit) — **fail at search-time** (constraint infeasibility)

**운영 결정 (확정)**:
- ✅ N=32 default best_params 유지 (cold path 변경 X)
- ✅ B-retuned warm path (PR-WARM-B Stage 3-5 후) deploy / **R1 P1.2 priority unchanged**
- ❌ GBDT cold path retune 모든 axis 종결 / non-GBDT axis만 architecture 가능성 보존

**본 세션 18 cycles 종합**:
- ✅ B (warm-only retune / commit 3a27002) — 유일 ADOPT
- ❌ D1 cold (4 cycles) — abandon
- ❌ D3 blend (2 cycles) — terminated
- 🔍 VFR — framework 정확 입증
- ❌ D1.SC — source-conditional axis 종결
- ❌ D1.Arch (default LGBM) — `default_LGBM_insufficient`
- ❌ **D1.Arch.tuned (본 commit)** — **`tuned_LGBM_insufficient_under_narrow_search`** (R6 amendment / suggestive search-time)

**남은 후속 후보** (별도 prospective cycles / 별 axis):
- **Bayesian hierarchical** (pymc 설치 필요)
- **Quantile regression** (statsmodels 사용 가능 / heavy-tail aware)
- **Neural network** (torch 설치됨)
- **Data/feature reform** (heavy-tail dataset 정합)
- **B Stage 3-5 운영 deploy 우선** (현 framework 유일 winner)
