# N=15 Confirmatory cycle (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: `a0a1bde` (Feature Sweep amendment / N=15 XGBoost = 1-SE winner / decision binding X)
> **Decision binding**: ✅ YES — N=15 XGBoost @ 운영 best_params (sweep winner config) 의 운영 채택 결정 직접 근거.

## 1. Goal

`a0a1bde` Feature Sweep amendment에서 1-SE rule 로 선정된 winner config (**N=15 XGBoost / 운영 best_params**) 가 fresh multi-seed holdout 위에서 N=32 baseline 대비 경쟁력 있는지 confirmatory 검증.

질문: **N=15 XGBoost @ 운영 best_params** 가 기존 운영 deployment (N=32 Ensemble = CB + XGB) 대비 OOS holdout 에서:
1. Cold MdAPE 비악화 (within parsimony tolerance)?
2. Warm MdAPE 개선 (sweep amendment 시그널: Δ_warm = −0.49pp)?
3. Per-source (artsy / saatchi) 비악화?
4. 4 Guard (Track 1 prereg locked) 모두 PASS?

PASS 시 = 운영 채택 권고 (N=32 → N=15 migration / 단순화 + warm 개선 동시).
FAIL 시 = N=32 유지 / 또는 retune 후 재시도 (N15.B cycle).

## 2. Method

### 2.1 Frozen N=15 feature set (selection 정의)

`a0a1bde` sweep 결과의 `fold_rankings_avg` (4-method aggregate rank / 5 outer fold 평균 / cold path 기준) ASC 정렬 top-15 (출처: `experiments/track1_optimization/sweep/sweep_simplified_results.json`):

| Rank | Feature | avg_rank |
|---|---|---|
| 1 | `ln_area` | 2.750 |
| 2 | `artist_total_works` | 2.900 |
| 3 | `career_stage` | 3.250 |
| 4 | `area_cm2` | 3.450 |
| 5 | `ln_followers` | 5.450 |
| 6 | `artist_birth_year` | 6.450 |
| 7 | `ho_x_support` | 8.700 |
| 8 | `has_seoul` | 10.400 |
| 9 | `ho` | 11.400 |
| 10 | `ho_power` | 12.100 |
| 11 | `medium_category` | 12.250 |
| 12 | `aspect_ratio` | 13.100 |
| 13 | `ln_ho` | 13.600 |
| 14 | `for_sale_ratio` | 14.750 |
| 15 | `has_depth` | 15.650 |

⚠️ **Selection bias caveat**: 본 ranking은 sweep amendment의 outer fold-internal ranking 평균 — 즉 같은 `integrated_v3_filtered` 데이터로 산출. 본 cycle holdout 도 같은 데이터의 새 split → fold-internal과는 다르나 **데이터 distribution 자체는 동일**. selection bias 0이 아님 (단 fold-internal 평균이라 leakage 정도는 reduced). adoption decision 시 이 caveat 명시.

### 2.2 Multi-seed Holdout split

`split_seed ∈ {31337, 7, 13}` (OOS cycle과 동일 seeds for cross-cycle 일관성).

각 seed 독립:
- **Cold split**: `GroupShuffleSplit(test_size=0.20, random_state=seed, groups=artist_slug)` (작가 단위 누수 방지)
- **Warm split**: `_warm_mask` slice 후 `train_test_split(test_size=0.20, random_state=seed, shuffle)` (warm path = row-level / e3367ed convention 정합)

### 2.3 Per-(seed) Training (R1 P0 fix / sweep winner = XGB@N=15 on both cold AND warm)

각 seed × 80% pool 위에서 in-memory 학습 (artifact 저장 X / 본 cycle 한정):

**Candidate (sweep winner / Strong adoption candidate)**: **`XGBoost @ N=15 + 운영 best_params`** — sweep amendment에서 cold metric 포함 winner-eligible로 선정됨 (delta_cold +0.033 / delta_warm −0.49). 본 cycle도 동일하게 cold + warm 양쪽 경로 평가.

**Baselines + 보조 candidates**:
1. **`Ens@N=32`** (운영 deployment): `CB@N=32 + XGB@N=32` 평균. 본 cycle primary baseline.
2. **`Ens@N=15`** (보조 / Weak adoption candidate): `CB@N=15 + XGB@N=15` 평균. ensemble 형태 유지 시 fallback.
3. **`XGB@N=32`** (model-matched 비교용): pure XGB warm Guard용.
4. **`CB@N=32`**: ensemble 구성 + cold model-matched 비교용.
5. **`CB@N=15`**: Ens@N=15 구성용.

→ 각 seed × 80% pool 마다 4 model 학습 (CB@N=15, XGB@N=15, CB@N=32, XGB@N=32). Ensemble = prediction 평균.

> **R1 P0 fix**: 이전 §2.3은 "XGB warm-only / cold = CB"로 표현되어 sweep winner와 estimand mismatch였음. sweep winner는 cold metric 포함 평가 (cold_ens_median / delta_cold)였으므로, 본 cycle도 XGB@N=15 cold + warm 모두 평가 (sweep winner 정합).

### 2.4 Holdout evaluation (per seed × per cell)

20% holdout 위에서:
- **Cold path** (20% cold holdout 전체):
  - `cb_n32_pred` / `cb_n15_pred` / `xgb_n32_pred` / `xgb_n15_pred` / `ensemble_n32_pred` / `ensemble_n15_pred` 모두 산출
- **Warm path** (20% warm holdout):
  - 동일 6 prediction 산출
- 각 prediction × baseline MdAPE 산출
- Per-source split (artsy / saatchi) MdAPE 별도 산출

### 2.5 Paired Bootstrap CI

각 seed × cell × (candidate vs baseline) 페어:
- `n_holdout < 500` 인 cell 한정 paired bootstrap 1000-iter / 90% CI / `Δ = candidate_mdape − baseline_mdape`.
- 결정 시 CI 상한 사용 (OOS cycle convention 정합).

## 3. Decision Criterion

### 3.1 4 Guard 두 vector (R1 P1 fix / candidate-별 적용)

본 cycle은 두 candidate (XGB@N=15 strong / Ens@N=15 weak) 동시 평가. 각 candidate 별 guard set 분리:

#### 3.1.1 Strong-adoption candidate guards (XGB@N=15)

| # | Guard | 비교 대상 | 임계 |
|---|---|---|---|
| G1_xgb | Δ Cold overall | XGB@N=15 vs Ens@N=32 | ≤ +0.5pp |
| G2_xgb | Δ Cold artsy | XGB@N=15 vs Ens@N=32 | ≤ +0.8pp |
| G3_xgb | Δ Cold saatchi | XGB@N=15 vs Ens@N=32 | ≤ +1.0pp |
| G4_xgb | Δ Warm KFold | XGB@N=15 vs XGB@N=32 | ≤ +0.3pp (model-matched) |

#### 3.1.2 Weak-adoption candidate guards (Ens@N=15 / Track 1 prereg locked)

| # | Guard | 비교 대상 | 임계 |
|---|---|---|---|
| G1_ens | Δ Cold overall | Ens@N=15 vs Ens@N=32 | ≤ +0.5pp |
| G2_ens | Δ Cold artsy | Ens@N=15 vs Ens@N=32 | ≤ +0.8pp |
| G3_ens | Δ Cold saatchi | Ens@N=15 vs Ens@N=32 | ≤ +1.0pp |
| G4_ens | Δ Warm KFold | XGB@N=15 vs XGB@N=32 | ≤ +0.3pp (공유) |

### 3.2 Per-seed verdict — Strong (XGB@N=15) (R1 P1 fix / 임계 sweep 시그널 정합)

**PASS**:
- ✅ G1_xgb-G4_xgb 모두 PASS (§3.1.1)
- ✅ Δ Cold overall (XGB@N=15 vs Ens@N=32) **≤ +0.5pp** (sweep 시그널 +0.033pp 와 정합 / parsimony 허용)
- ✅ Δ Warm (XGB@N=15 vs XGB@N=32) point estimate ≤ 0 OR bootstrap CI 상한 ≤ 0

**INCONCLUSIVE**:
- G1-G4 PASS BUT Δ Cold = (+0.5, +1.0]pp (sweep 시그널 초과 / 결정 보류)
- 또는 Δ Warm point ≤ 0 BUT bootstrap CI 상한 > 0

**FAIL**:
- 임의 G_xgb FAIL
- Δ Cold > +1.0pp (large degradation)
- Δ Warm point > 0

### 3.3 Per-seed verdict — Weak (Ens@N=15)

**PASS**:
- ✅ G1_ens-G4_ens 모두 PASS (§3.1.2)
- ✅ Δ Cold (Ens@N=15 vs Ens@N=32) ≤ +0.3pp
- ✅ Δ Warm point ≤ 0 OR CI 상한 ≤ 0

**INCONCLUSIVE**: G PASS BUT Δ Cold = (+0.3, +0.5]pp 또는 Warm CI 상한 > 0.

**FAIL**: G FAIL OR Δ Cold > +0.5pp.

### 3.4 Multi-seed aggregate (R1 P1 fix / decision-binding migration용 strict 기준)

각 candidate (XGB@N=15 strong / Ens@N=15 weak) 별도 집계:

| Per-seed 분포 | Aggregate (strong / Ens@N=15도 동일 적용) |
|---|---|
| PASS × 3 | **PASS** (decision-binding migration 가능) |
| PASS × 2 + INCONCLUSIVE × 1 | **INCONCLUSIVE** (canary 후보로 별도 prereg / 본 cycle ADOPT 자격 X) |
| PASS × 2 + FAIL × 1 | **INCONCLUSIVE** (split-driven variance) |
| FAIL × 2 이상 | **FAIL** |
| 그 외 mixed | **INCONCLUSIVE** |

> **R1 P1 fix**: 이전 prereg는 `PASS×2+INCONCLUSIVE×1 → PASS_with_caveat`로 적용 → 본 cycle은 운영 champion 교체용 confirmatory이므로 strict 기준 (PASS×3만 ADOPT 자격). PASS_with_caveat는 별도 narrow canary cycle 결정 사항 / 본 cycle scope 외.

### 3.5 채택 결정

- **Strong ADOPT**: XGB@N=15 aggregate = **PASS** (PASS×3) → 운영 채택 권고 (N=32 Ens → N=15 XGB migration).
- **Weak ADOPT**: Ens@N=15 aggregate = **PASS** + XGB@N=15 INCONCLUSIVE → Ensemble 형태 유지하며 N=15 migration 후보.
- **Hold + canary 후보**: 둘 다 INCONCLUSIVE → N=32 유지 / 별도 narrow canary cycle 후보 (PASS 다수 seed 경우만).
- **Hold + retune**: 둘 다 FAIL or 다수 INCONCLUSIVE → N=32 유지 / **N15.B cycle (HP retuning)** 후 재시도.

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)
- `docs/n15_confirmatory_prereg_20260509.md` (본 문서)
- `docs/n15_confirmatory_results_20260509.md` (결과 분석 + 채택 결정)
- `scripts/validate_n15_confirmatory.py` (entry point)
- `data/n15_confirmatory_holdout_20260509/<source>_seed<S>_holdout_indices.json` (split index per (source, seed) × 6 files)

### 4.2 산출물 (gitignored / 재현 가능)
- `model_test_results/n15_confirmatory_20260509.json` (per-(seed, source, model, cell) metrics + aggregate verdicts)

### 4.3 Schema (개략)

```json
{
  "version": "v1-n15-confirmatory",
  "split_seeds": [31337, 7, 13],
  "fold_seed": 42,
  "frozen_n15_features": [...15 features list...],
  "n32_features": [...32 features list...],
  "guards_strong_locked": {
    "G1_xgb": {"name": "Δ Cold overall (XGB@N=15 vs Ens@N=32)", "threshold": 0.5},
    "G2_xgb": {"name": "Δ Cold artsy (XGB@N=15 vs Ens@N=32)", "threshold": 0.8},
    "G3_xgb": {"name": "Δ Cold saatchi (XGB@N=15 vs Ens@N=32)", "threshold": 1.0},
    "G4_xgb": {"name": "Δ Warm KFold (XGB@N=15 vs XGB@N=32)", "threshold": 0.3}
  },
  "guards_weak_locked": {
    "G1_ens": {"name": "Δ Cold overall (Ens@N=15 vs Ens@N=32)", "threshold": 0.5},
    "G2_ens": {"name": "Δ Cold artsy (Ens@N=15 vs Ens@N=32)", "threshold": 0.8},
    "G3_ens": {"name": "Δ Cold saatchi (Ens@N=15 vs Ens@N=32)", "threshold": 1.0},
    "G4_ens": {"name": "Δ Warm KFold (XGB@N=15 vs XGB@N=32)", "threshold": 0.3}
  },
  "per_seed": {
    "31337": {
      "n_pool_cold": 0, "n_holdout_cold": 0, "n_pool_warm": 0, "n_holdout_warm": 0,
      "models": {
        "cb_n15":  {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": null},
        "xgb_n15": {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": 0},
        "cb_n32":  {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": null},
        "xgb_n32": {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": 0},
        "ens_n15": {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": 0},
        "ens_n32": {"cold_overall_mdape": 0, "cold_artsy_mdape": 0, "cold_saatchi_mdape": 0, "warm_mdape": 0}
      },
      "deltas_strong": {"G1_xgb": 0, "G2_xgb": 0, "G3_xgb": 0, "G4_xgb": 0,
                        "delta_cold_xgb_vs_ens32": 0, "delta_warm_xgb_vs_xgb32": 0},
      "deltas_weak":   {"G1_ens": 0, "G2_ens": 0, "G3_ens": 0, "G4_ens": 0,
                        "delta_cold_ens_vs_ens32": 0, "delta_warm_xgb_vs_xgb32": 0},
      "guards_strong": {"G1_xgb": "PASS", "G2_xgb": "PASS", "G3_xgb": "PASS", "G4_xgb": "PASS"},
      "guards_weak":   {"G1_ens": "PASS", "G2_ens": "PASS", "G3_ens": "PASS", "G4_ens": "PASS"},
      "verdict_xgb_n15": "PASS",
      "verdict_ens_n15": "PASS"
    },
    "7": "...", "13": "..."
  },
  "aggregate": {
    "xgb_n15": "PASS|INCONCLUSIVE|FAIL",
    "ens_n15": "PASS|INCONCLUSIVE|FAIL"
  },
  "overall_verdict": "ADOPT_xgb|ADOPT_ens|HOLD|NEEDS_MORE_DATA"
}
```

> 스키마 핵심: `aggregate` 값은 **PASS×3 only → PASS** (PASS_with_caveat 없음 / R1 P1 fix). PASS×2+INCONCLUSIVE×1은 `INCONCLUSIVE`.

## 5. Out-of-scope

- ❌ HP retuning for N=15 (N15.B cycle 별도)
- ❌ Source-Conditional + N=15 통합 (N15.C cycle 별도)
- ❌ Per-source HP tuning (Phase 3)
- ❌ 운영 artifact / parquet / runbook 변경 (decision-binding 채택 권고만 / 운영 PR 별도)
- ❌ Multi-seed N 확대 (3 seeds 고정 / INCONCLUSIVE 시 후속 cycle)
- ❌ Different feature ranking 방법 (fold_rankings_avg 고정 / sensitivity analysis는 별도 cycle)
- ❌ N≠15 시험 (N=10, 20 등 / 본 cycle = sweep winner 검증만)

## 6. 한계 / Risk

- **Selection bias**: N=15 features는 sweep amendment data로 ranked → 본 cycle holdout이 같은 dataset 의 새 split. fold-internal averaging이 leakage 정도 reduce 하지만 0 X. CI에 caveat 명시.
- **운영 best_params 사용**: N=32 기준으로 tuned best_params를 N=15에 그대로 사용. N=15에 최적화된 HP는 N15.B cycle에서. 본 cycle은 "default params parity test".
- **Ensemble 비교 비대칭**: N=15 winner는 pure XGBoost. operational deployment는 Ensemble. pure XGB vs Ensemble 비교 시 ensemble의 variance reduction 이점 잃음 — strong-adoption PASS 임계 ≤ +0.5pp / FAIL > +1.0pp로 sweep 시그널 (+0.033pp) 정합 흡수 (R1 P1 fix).
- **Multi-seed N=3**: split-driven variance fully cover 부족. INCONCLUSIVE 시 N=5/7 후속 cycle.
- **Compute**: 6 (3 seed × 2 source) iteration × (CB@N=15 + XGB@N=15 + CB@N=32 + XGB@N=32) 4 model 학습 ≈ ~30-60분 wall time.
- **Saatchi 작은 effect**: sweep delta_saatchi = −0.05 (negligible). saatchi에서 N=15 채택 motivation 약함 / artsy + warm 개선이 본 cycle motivation.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 1차 사전 자문 (`019e0bb1` resume) | NEEDS FIX → 반영 완료 | P0: candidate estimand mismatch (XGB warm-only로 표현됨 → sweep winner는 cold 포함 평가) → §2.3 정정. P1×3: Guard table candidate-별 분리 (§3.1.1/§3.1.2) / Δ Cold tolerance sweep 시그널 정합 (+0.5pp / FAIL >+1.0pp) / multi-seed aggregate strict (PASS×3만 ADOPT). |
| 2차 verification (resume) | NEEDS FIX → 반영 완료 | P2: schema에 `PASS_with_caveat` enum 잔존 → strict aggregate 정합으로 정정. P2: schema model 예시 `xgb_n15: warm-only` → cold + warm 모두 산출. P2: §6 risk note `parsimony tolerance (+1.0pp)` → 새 thresholds (≤+0.5pp PASS / >+1.0pp FAIL) 정합. |
| 3차 verification (resume) | **LGTM** | schema enum / model fields / §6 risk note 모두 정합 → **prereg 잠금 / 구현 진입** |
| 4차 사후 검수 (resume) | **NEEDS DECISION ALIGNMENT → 합의** | Implementation 정합 / 결정 logic 정합. Rule contradiction 인정 (G4 ≤+0.3pp PASS vs warm > 0 FAIL) — retroactive fix X / commit as HOLD + caveat. N15.B prospective justified (post rule-fix). N15.C scope narrow (Artsy XGB-focused). 상세: `n15_confirmatory_results_20260509.md` §3 |
