# Feature Sweep — Post-hoc Amendment Cycle (별도 prereg)

> **작성일**: 2026-05-09
> **본 cycle 의 본질**: post-hoc exploratory sweep / 최적 N + 모델 조합 탐색 / record only
> **Decision binding**: ❌ X (recording only / 운영 채택 결정 = 별도 decision-binding cycle)
> **분기**: `exp/track1-feature-optimization-cycle` (동일 분기 / 본 cycle 별도 commit)
> **원본 prereg**: `docs/track1_feature_optimization_prereg_20260508.md` (round 3 GO)

> ⚠️ **본 amendment 영역 의 의무 위치**:
> - **out-of-scope of original prereg**: original cycle 영역 의 의무 영역 의 의무 = NOT CONVERGED 종료 / Phase 8 INELIGIBLE / 본 amendment = 후속 separately-labeled exploratory cycle
> - **in-scope of amendment**: feature N + 모델 조합 sweep / fold-internal ranking / 1-SE winner rule
> - **out-of-scope of amendment**: 운영 코드 / parquet / artifact 변경 / 운영 채택 결정 / HP tuning (default 또는 운영 best_params)

## 1. Goal

운영 32 features 영역 의 의무 영역 의 의무 영향도 영역 의 의무 영역 의 의무 영역 의 의무 sub-set (10-30개 영역) 영역 의 의무 영역 의 의무 영역 의 의무 다양한 비선형 모델 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = 최적 N + 모델 조합 탐색 → exploratory record (운영 채택 X).

## 2. Method (코덱스 사전 자문 P1 4 fix 적용)

### 2.1 Feature Ranking (Fold-Internal — P1 fix #1)

**의무**: 영향도 ranking 영역 의 의무 영역 의 의무 영역 의 의무 = **outer CV train fold 내부 만** 영역 의 의무 영역 의 의무 산출. 전체 데이터 영역 의 의무 영역 의 의무 ranking → 같은 데이터 평가 = **selection leakage** 영역 의 의무 영역 의 의무 영역 의 의무.

**Protocol** (cold GroupKFold-5 / outer fold 별):
1. train fold 영역 의 의무 영역 의 의무 영역 의 의무 4-method 영향도 산출:
   - CatBoost FI (PVC) — train fold retrain
   - XGBoost gain — train fold retrain
   - SHAP avg (CB SHAP + XGB SHAP 평균) — train fold
   - Permutation Importance — train fold (5000 sample × 5 repeats)
2. 4-method aggregate rank ASC = 영향도 DESC ranking
3. top-N 영역 의 의무 영역 의 의무 영역 의 의무 = same outer fold rank
4. test fold 영역 의 의무 영역 의 의무 평가 (model 학습 + predict)

### 2.2 Locked Config Space (P1 fix #2)

**N grid** (12 영역):
- N = 5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 32

**Model grid** (6 영역):
- **CatBoost** — 운영 best_params (iter 1000 / depth 8 / lr 0.0953)
- **XGBoost** — 운영 best_params (3000 round / depth 7 / lr 0.0401)
- **LightGBM** — default (post-hoc / screening only / winner 자격 X)
- **RandomForest** — default (n_estimators=500 / screening only)
- **HistGradientBoosting** — default (sklearn / screening only)
- **Ensemble** — CB + XGB 평균 (운영 정합 / winner 자격 ✓)

**Total config**: 12 N × 6 model = **72 configs**

### 2.3 CV Protocol

| Evaluation | Method | seed | 모집단 |
|---|---|---|---|
| **Cold MdAPE** | GroupKFold-5 (artist_slug) | 42 fixed | 28,376 / 1,551 artists |
| **Warm MdAPE (main)** | KFold-5 | 42 / 7 / 13 (3 seeds) | 27,062 (warm slice) |
| **Warm MdAPE (guard)** | GroupKFold-5 (artist_slug) | 42 fixed | 동일 |

> Warm multi-seed (P2) = sensitivity check / median (3 seeds) primary.

### 2.4 Locked Winner Rule (1-SE / P1 fix #3)

**Primary metric**: cold_ensemble MdAPE (median of 5 outer folds / fold-internal ranking).

**Noise band (locked)**:
- Phase 0 cold ensemble fold std = 4.734%p
- 5-fold mean SE = std / √5 = **2.117%p**
- 1-SE band = best_cold_mdape + 2.117%p

**Winner selection** (사전 정의 / locked):
1. 모든 72 config 영역 의 의무 영역 의 의무 cold_ensemble median + warm_main median dump (전체 보고)
2. **noise band 내 dominant set** = `cold ≤ best_cold + 2.117%p`
3. **band 내 우선순위**:
   - (a) 가장 작은 N 우선 (parsimony principle)
   - (b) 동일 N 영역 의 의무 영역 의 의무 = 운영 정합 모델 우선 (CatBoost > XGBoost > Ensemble > LightGBM > HistGradientBoosting > RandomForest)
   - (c) LightGBM / RF / HGB = screening only / winner 자격 X (default params 영역 의 의무)
4. **Secondary tiebreak** (P1 fix #3): same selected config 영역 의 의무 영역 의 의무 model-matched warm metric (warm_kfold_xgboost 영역 의 의무 영역 의 의무 X / config 의 의무 영역 의 의무 매칭 영역 의 의무)

### 2.5 Guard 4 (locked / 원본 prereg 정합)

| # | Guard | 임계 (locked) |
|---|---|---|
| G1 | Warm KFold MdAPE 악화 | ≤ +0.5%p (vs Phase 0) |
| G2 | Overall ensemble 악화 | ≤ +0.8%p |
| G3 | Artsy segment cold 악화 | ≤ +1.0%p |
| G4 | Saatchi segment cold 악화 | ≤ +1.0%p |

> winner 영역 의 의무 영역 의 의무 = Guard 4 모두 PASS 의무 (record 영역 의 의무 영역 의 의무 표 영역 의 의무 영역 의 의무 영역 의 의무 dump).

## 3. Decision binding

❌ **본 amendment cycle = record only**:

| 항목 | 영향 |
|---|---|
| 운영 코드 / parquet / artifact | **변경 X** |
| 운영 채택 결정 | **본 cycle 영역 X** (별도 decision-binding cycle 의무) |
| 본 cycle winner | **추천 후보 record 만** (운영 채택 = 별도 cycle 영역 의 의무) |

## 4. Reporting

### 4.1 Full matrix dump (모든 72 config)

JSON + CSV format:
```
N, model, cold_ens_median, cold_ens_q1, cold_ens_q3,
warm_kfold_median, warm_groupkfold_median, artsy_cold, saatchi_cold,
guard_g1_pass, guard_g2_pass, guard_g3_pass, guard_g4_pass,
in_noise_band_dominant
```

### 4.2 Winner declaration

- (final) winner config (N, model)
- noise band dominant set 영역 의 의무 영역 의 의무 영역 의 의무 list
- 1-SE rule 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 trace (왜 이 영역 의 의무 영역 의 의무 winner)
- baseline 영역 의 의무 영역 의 의무 영역 의 의무 = Phase 0 (32 features / 38.62 cold ens)

### 4.3 Sensitivity dump

- warm 3 seeds (median + range)
- per-source breakdown (Artsy / Saatchi / Saatchi guard FAIL 가능성 영역 의 의무)

## 5. 진행 일정

| 단계 | 영역 | 일수 |
|---|---|---:|
| amendment doc 작성 + 코덱스 사전 자문 | 본 doc + 사전 GO | 0.5 |
| Fold-internal sweep script | 5 outer fold × (4-method ranking + 12 N × 6 model retrain) | 0.5 |
| Background run | ~3-4 시간 | 1 |
| 분석 + 1-SE winner + 코덱스 사후 | matrix + winner declaration | 1 |
| **합계** | — | **~3 일** |

## 6. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1 4 영역) → 본 doc 영역 의 의무 영역 의 의무 fix 적용 |
| 2차 사전 자문 (예정) | 본 doc commit 직후 / GO 의무 |
| 3차 사후 검수 (예정) | sweep run 종료 직후 |

## 7. 한계 (사전 명시)

- post-hoc / exploratory / decision binding ❌ X
- LightGBM / RF / HGB = default params (운영 best_params HP 외 / 공정 비교 X / screening only)
- holdout 분리 X (CV-only / 다음 decision-binding cycle 영역 의 의무 영역 의 의무 의무)
- 1-SE band 내 winner = "tied with baseline" 가능성 영역 의 의무 영역 의 의무 = 본 cycle 영역 의 의무 영역 의 의무 단정 X
- N grid 5-32 영역 의 의무 영역 의 의무 = 운영 32 features 의 의무 영역 의 의무 영역 의 의무 hard-coded (다른 변형 영역 의 의무 영역 의 의무 X)
