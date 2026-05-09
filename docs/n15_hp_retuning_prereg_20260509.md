# N=15 HP Retuning cycle (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: `8c9e58e` (N15.A Confirmatory / HOLD with R4 caveat) → R4 권고 follow-up
> **Decision binding**: ✅ YES — XGB@N=15 retuned best_params 의 운영 채택 결정 직접 근거.

## 1. Goal

`8c9e58e` (N15.A Confirmatory) cycle에서 XGB@N=15 cold path 시그널은 강했으나 (3/3 seed cold 개선 시그널 / Artsy cold 강한 개선), warm path에서 작은 regression (+0.10 ~ +0.29pp) 발생. R4 codex 합의:
- N15.A의 prereg rule contradiction (G4 ≤+0.3pp PASS vs warm > 0 FAIL)을 인정하되 retroactive fix X.
- N15.B에서 prospective rule fix + HP retuning으로 warm gap 해소 시도.

질문: **XGB@N=15에 맞춤 HP** (Optuna로 N=32 best_params 대신 N=15 features에 최적화한 params)이 있을 때, cold 시그널을 유지하면서 warm regression을 G4 임계 (≤ +0.3pp) 또는 0 이하로 가져올 수 있는가?

PASS 시 → retuned best_params 채택 권고 + N15.C cycle (Source-Conditional 통합) 입력으로 활용.
FAIL 시 → default 운영 best_params 유지 / N=15 migration 보류.

## 2. Method

### 2.1 Frozen N=15 features (N15.A 정합)

`docs/n15_confirmatory_prereg_20260509.md` §2.1 정의 동일 (변경 X):
```
['ln_area', 'artist_total_works', 'career_stage', 'area_cm2', 'ln_followers',
 'artist_birth_year', 'ho_x_support', 'has_seoul', 'ho', 'ho_power',
 'medium_category', 'aspect_ratio', 'ln_ho', 'for_sale_ratio', 'has_depth']
```

### 2.2 Optuna HP Search Space

**Objective**: warm MdAPE on warm-pool 5-fold CV. cold 비악화를 secondary constraint로.

**Search space** (XGBoost):

| Parameter | Range | 분포 |
|---|---|---|
| `max_depth` | [4, 10] | int uniform |
| `learning_rate` | [0.01, 0.2] | log-uniform |
| `num_boost_round` | [500, 4000] | int uniform |
| `subsample` | [0.6, 1.0] | uniform |
| `colsample_bytree` | [0.6, 1.0] | uniform |
| `min_child_weight` | [1, 20] | int uniform |
| `gamma` | [0, 0.5] | uniform |
| `reg_alpha` | [0, 1.0] | uniform |
| `reg_lambda` | [0, 5.0] | uniform |

**운영 best_params (N=32 기준 / 시작점 reference)**:
- num_boost_round=3000, max_depth=7, learning_rate=0.0401 (출처: `integrated_v3_filtered_tuned_best_params.json`)

**Sampler**: Optuna TPE (default). **Trials**: 50 (compute budget 제한 / TPE convergence 가정).

**Outer fold split**: full data (28,376 rows, both Artsy + Saatchi after filter) 위에서 `KFold(n_splits=5, shuffle=True, random_state=42)`.

**Search-time data**: warm-mask 필터 후 ≈ 27,062 rows. 5-fold inner CV (KFold).

**Trial seed**: 42 (XGBoost training seed / fold split seed 동일).

### 2.3 Search Objective (R1 P1 fix / R1 P2 fix)

**Framing**: warm-first 1차 search + downstream decision screening. **Direct adoption endpoint optimization X** (objective는 proxy로만 활용).

**Per-trial 산출 raw values** (전부 log 저장 / R1 P2 audit):
1. `warm_cv_mdape` = warm-pool 5-fold CV mean warm MdAPE (Optuna primary objective).
2. `cold_cv_mdape` = full data 5-fold CV mean cold MdAPE (constraint metric).
3. `cold_cv_mdape_artsy` = artsy 부분 cold MdAPE (constraint metric).
4. `cold_cv_mdape_saatchi` = saatchi 부분 cold MdAPE (constraint metric).

**Optuna constraint** (Optuna `study.optimize(constraints_func=...)` API 사용 / penalty heuristic 미사용):

Step 2는 **`retuned XGB@N=15 vs Ens@N=32`** (N15.A strong-adoption 정합) 이므로 c1-c3 baseline은 Ens@N=32 cold metrics로 변경 (R2 fix):

- `c1`: `cold_cv_mdape - cold_cv_mdape_default_ens_n32 - 0.5` (Step 2 G1_xgb 정합 / Ens@N=32 baseline)
- `c2`: `cold_cv_mdape_artsy - cold_cv_mdape_default_artsy_ens_n32 - 0.8` (Step 2 G2_xgb / Ens@N=32 artsy)
- `c3`: `cold_cv_mdape_saatchi - cold_cv_mdape_default_saatchi_ens_n32 - 1.0` (Step 2 G3_xgb / Ens@N=32 saatchi)
- `c4`: `cold_cv_mdape - cold_cv_mdape_default_xgb_n15 - 0.3` (Step 1 cold non-regression / default XGB@N=15 baseline)

**Search-time precomputation**: `cold_cv_mdape_default_ens_n32` 등 baseline은 search 시작 전 1회 산출 (full data 5-fold CV / default Ens@N=32 = (CB@N=32 + XGB@N=32)/2 / log + 저장).

`constraint_violated = any(c_i > 0)` (Optuna trial level). 위반 trial은 best 후보에서 자동 제외.

`constraint_violated = any(c_i > 0)` (Optuna trial level). 위반 trial은 best 후보에서 자동 제외.

**Logging**: per-trial `(params, warm_cv_mdape, cold_cv_mdape, cold_cv_mdape_artsy, cold_cv_mdape_saatchi, constraint_values, constraint_violated)` JSONL 저장 (`xgb_n15_retune_optuna_study.json`).

**Trial best**: `warm_cv_mdape` 최소 trial 중 `constraint_violated == False` 만 후보. 그 중 mean warm MdAPE 최소 = `best_params_n15`.

### 2.4 Selected `best_params_n15` validation (R1 P0 fix / fresh holdout seeds)

Optuna search 종료 후 `best_params_n15` 산출. 다음 검증:

1. **Fresh holdout 위 evaluation** (multi-seed / 3 seed / **N15.A 와 독립**):
   - **새로운 split_seeds = {23, 47, 71}** (N15.A의 31337/7/13와 비중복 / decision-binding 독립성 보장)
   - 새 holdout indices = `data/n15_hp_retune_holdout_20260509/seed{23,47,71}_holdout_indices.json` (별도 dir / 본 cycle 한정)
   - 각 seed × 80% pool 위에서 retuned XGB@N=15 학습 + default XGB@N=15 동시 학습 (within-cycle 비교용)
   - 20% holdout 위 prediction → cold/warm/per-source MdAPE
   - 비교: retuned vs default (within-cycle 학습) AND retuned vs Ens@N=32 (within-cycle 학습)

> **R1 P0 합의**: N15.A holdout 재사용은 selection effect 우려 (같은 split이 N15.A HOLD를 이미 생성하고 본 cycle을 motivate함). N15.B는 fresh seed로 독립성 확보 → decision-binding 자격 유지.

2. **Per-seed PASS/INCONCLUSIVE/FAIL 판정 (R4 fix / G4-consistent)**:
   - PASS:
     - Δ_warm (retuned vs default XGB@N=15) ≤ 0 (improvement) AND
     - Δ_cold (retuned vs default XGB@N=15) ≤ +0.3pp (cold 비악화)
   - INCONCLUSIVE:
     - Δ_warm ∈ (0, +0.3pp] AND Δ_cold ≤ +0.3pp (warm 보합 / cold 비악화)
   - FAIL:
     - Δ_warm > +0.3pp OR Δ_cold > +0.3pp

3. **N15.A 비교 endpoint (secondary)**:
   - retuned XGB@N=15 vs Ens@N=32 (N15.A의 strong-adoption 비교 정합)
   - G1-G4 strong (locked / N15.A 정합) 적용 + warm rule G4-consistent (≤+0.3pp = PASS / R4 fix)

### 2.5 Multi-seed aggregate (3 seeds / N15.A 정합 strict)

| Per-seed 분포 | Aggregate |
|---|---|
| PASS × 3 | **PASS** (retuned 채택 + N15.C 입력) |
| PASS × 2 + INCONCLUSIVE × 1 | **INCONCLUSIVE** (보류 / N15.C scope 결정 보류) |
| PASS × 2 + FAIL × 1 | **INCONCLUSIVE** |
| FAIL × 2+ | **FAIL** (default 유지) |
| 기타 mixed | **INCONCLUSIVE** |

## 3. Decision Criterion

### 3.1 Two-step adoption decision

**Step 1: retuned vs default XGB@N=15** (procedure efficacy):
- Aggregate `PASS` → retuned params는 default 대비 개선 효과 있음 (warm gap 해소).
- Aggregate `FAIL` → retuning 효과 없음 / N=15 migration 가치 약함.

**Step 2 (Step 1 PASS 시): retuned XGB@N=15 vs Ens@N=32** (운영 채택):
- N15.A의 strong-adoption 기준 (G1-G4) + warm rule G4-consistent (≤+0.3pp = PASS) 재적용.
- Aggregate `PASS` → 운영 채택 권고.
- Aggregate `INCONCLUSIVE` → narrow canary 후보.
- Aggregate `FAIL` → 보류.

### 3.2 채택 결정

- Step 1 PASS + Step 2 PASS → **ADOPT retuned XGB@N=15** + N15.C 입력으로 활용.
- Step 1 PASS + Step 2 INCONCLUSIVE → **N15.C 진행 가치 있음** (Source-Conditional 통합 시 추가 개선 가능성) / 운영 채택은 N15.C 후로 보류.
- Step 1 FAIL OR Step 2 FAIL → **HOLD** / N=32 default 유지 / N15.C scope 재논의 (Artsy XGB-only path 단독 가치).

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)
- `docs/n15_hp_retuning_prereg_20260509.md` (본 문서)
- `docs/n15_hp_retuning_results_20260509.md` (결과 + 채택 결정)
- `scripts/optuna_xgb_n15_retune.py` (entry / Optuna search + validation)
- `model_test_results/xgb_n15_retuned_best_params.json` (산출 best_params + provenance)

### 4.2 산출물 (gitignored / 재현 가능)
- `model_test_results/xgb_n15_retune_optuna_study.json` (study trials / 50 trial × params + value)
- `model_test_results/n15_hp_retune_validation_20260509.json` (validation 결과)

### 4.3 best_params Schema

```json
{
  "version": "v1-xgb-n15-retuned",
  "model_target": "xgb_n15_warm_optimized",
  "frozen_n15_features": [...],
  "search_space": {...},
  "n_trials": 50,
  "best_params": {
    "num_boost_round": 0,
    "max_depth": 0,
    "learning_rate": 0.0,
    "subsample": 0.0,
    "colsample_bytree": 0.0,
    "min_child_weight": 0,
    "gamma": 0.0,
    "reg_alpha": 0.0,
    "reg_lambda": 0.0
  },
  "best_value_warm_mdape": 0.0,
  "n32_baseline_warm_mdape": 0.0,
  "search_seed": 42,
  "elapsed_sec": 0,
  "git_commit": "<hash>",
  "evaluated_at": "..."
}
```

## 5. Out-of-scope

- ❌ CB retuning (cold path / N15.A에서 CB@N=15 weakness 확인 / 별도 cycle 또는 Source-Conditional 영역)
- ❌ Ensemble retuning (Pure XGB candidate만 / R4 합의)
- ❌ Source-Conditional 통합 (N15.C cycle)
- ❌ N=32 default params 변경 (운영 영향 X / 본 cycle = N=15 retune only)
- ❌ Different search space / sampler (TPE 50 trials 고정 / sensitivity 별도 cycle)
- ❌ Multi-seed N 확대 (3 seeds 고정 / N15.A 정합)
- ❌ N≠15 시험 (N=15 전용)

## 6. 한계 / Risk

- **HP search overfitting**: 50 trial Optuna가 5-fold CV mean에 overfitting 가능. holdout 위 validation으로 cross-check.
- **Single objective (warm MdAPE)**: cold-non-regression은 constraint penalty로 처리 / multi-objective Pareto 미사용. 결과 cold 시그널 정량 보존 X 가능 / validation 단계에서 검증.
- **Compute budget**: 50 trial × 5-fold = 250 XGBoost training. 추정 ~30-60분 wall.
- **Feature set 변경 X**: N=15 frozen 유지 / feature 추가/제거 sensitivity 후속 cycle에서.
- **R4 rule-fix prospective only**: G4-consistent warm rule (≤+0.3pp = PASS)은 본 cycle 한정 / N15.A retroactive 적용 X.
- **3 seeds 한정**: split-driven variance fully cover 부족. PASS×3 strict 후 N15.C 진입.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 1차 사전 자문 (`019e0bb1` resume) | NEEDS FIX → 반영 완료 | P0: N15.A holdout 재사용 → decision-binding 독립성 부족 → fresh seeds {23, 47, 71} 변경. P1: search objective와 adoption endpoint mismatch → Step 1/2 구체 cold constraints 명시 (G1 ≤+0.5pp / G2 ≤+0.8pp / G3 ≤+1.0pp / Step1 cold ≤+0.3pp). P2: penalty heuristic → Optuna constraints API + raw values JSONL audit log. |
| 2차 verification (resume) | NEEDS FIX → 반영 완료 | P0: §2.3 c1-c3 baseline이 default_xgb_n32였으나 Step 2는 Ens@N=32 vs retuned이므로 baseline을 default_ens_n32로 변경. c4 (default_xgb_n15)는 정합 유지. |
| 3차 verification (resume) | **LGTM** | c1-c3 Ens@N=32 baseline 정합 / c4 default XGB@N=15 baseline 유지 → **prereg 잠금 / 구현 진입** |
| 4차 사후 검수 (run #1) | NEEDS FIX (P0) → fix 완료 | search-time cold CV가 KFold → GroupKFold 정정 / run #1 무효화 / run #3 재실행. |
| 5차 사후 검수 (run #3) | NEEDS FIX (P1+P2) → deviation 인정 + 문서 수정 / **HOLD verdict commit 가능** | P1: n_trials=30 vs prereg 50 (documented deviation / negative result robust). P2: feasible count 5/30 정확화. 상세: `n15_hp_retuning_results_20260509.md` §6 |
