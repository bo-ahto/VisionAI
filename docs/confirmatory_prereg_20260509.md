# Confirmatory Cycle — Top 15 + XGBoost (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**:
> - `docs/track1_feature_optimization_prereg_20260508.md` (원본 cycle)
> - `docs/feature_sweep_amendment_20260509.md` (post-hoc sweep)
> - `experiments/track1_optimization/sweep/SWEEP_REPORT.md` (provisional winner)
> - `docs/methodology_deviation_log.md` (sweep deviation 기록)
>
> **Decision binding**: ✅ **YES** (운영 채택 결정 영역 의 의무 영역 의 의무 영역 의 의무 cycle)

> ⚠️ **본 cycle 영역 의 의무 위치**:
> - sweep amendment cycle 영역 의 의무 영역 의 의무 provisional winner (N=15 / XGBoost) 영역 의 의무 영역 의 의무 영역 의 의무 final unseen test
> - **운영 채택 가능** verdict 영역 의 의무 영역 의 의무 cycle (PASS = 운영 적용 / FAIL = 운영 영역 의 의무 영역 의 의무 변경 X)

## 1. Goal

**Top 15 features + XGBoost** 영역 의 의무 영역 의 의무 영역 의 의무 운영 32 features + ensemble baseline 영역 의 의무 영역 의 의무 영역 의 의무 = unseen Holdout test 영역 의 의무 영역 의 의무 검증 → 운영 채택 결정.

**Hypothesis (preregistered)**: Top 15 + XGBoost 영역 의 의무 영역 의 의무 영역 의 의무 운영 baseline (32 + ensemble) 영역 의 의무 영역 의 의무 영역 의 의무:
- cold MdAPE = noise band 내 (≈ 38.7 ± 2.117)
- warm MdAPE = 개선 (≤ 10.47 / 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)
- 모든 Guard 4 PASS

## 2. Method

### 2.1 Locked Holdout split (사전 정의 / 영역 의 의무 영역 의 의무)

**Split protocol**:
- **artist 단위 분할** (GroupShuffleSplit) — train/test 영역 의 의무 영역 의 의무 영역 의 의무 artist overlap X
- **80% / 20%**:
  - 80% = CV-eligible (모델 선택 + 학습)
  - **20% = Locked Holdout (unseen / final test 의무 영역 의 의무 영역 의 의무 영역 의 의무)**
- **random_state = 20260509** (locked)
- artist count: 1,551 → 80% (~1,240) / 20% (~311)

**Holdout 의무 (locked)**:
- ❌ 모델 학습 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 X
- ❌ 영향력 ranking 영역 의 의무 영역 의 의무 X
- ❌ feature selection 영역 의 의무 영역 의 의무 X
- ❌ HP tuning 영역 의 의무 영역 의 의무 X
- ✅ Final test (1회 / verdict 결정 영역 의 의무) 만

### 2.2 Top 15 Features — **80% 내부 재산출 의무** (P0 leakage fix)

⚠️ **코덱스 round 1 P0 fix**: 원안 영역 의 의무 영역 의 의무 영역 의 의무 = sweep amendment ranking 영역 의 의무 영역 의 의무 영역 의 의무 직접 사용 = **selection leakage** (sweep ranking 영역 의 의무 영역 의 의무 = 전체 데이터 28,376 영역 의 의무 영역 의 의무 / 영역 의 의무 영역 의 의무 Holdout 20% 영역 의 의무 영역 의 의무 영역 의 의무 = 이미 ranking 영역 의 의무 영역 의 의무 영역 의 의무 사용 영역 의 의무).

**Fix protocol**:
1. **Step 1**: Locked Holdout 20% 분리 (사전 / artist GroupShuffleSplit / random_state=20260509)
2. **Step 2**: 80% subset 영역 의 의무 영역 의 의무 영역 의 의무 fold-internal 4-method aggregate ranking 재산출 (5 fold avg / Holdout 영역 의 의무 영역 의 의무 영역 의 의무 X)
3. **Step 3**: 80% ranking 영역 의 의무 영역 의 의무 영역 의 의무 Top 15 features 영역 의 의무 영역 의 의무 영역 의 의무 = locked feature set
4. **Step 4**: Holdout 1회 final test

**Sweep amendment ranking** (전체 데이터):
- 본 prereg 영역 의 의무 영역 의 의무 = **reference only** (영역 의 의무 영역 의 의무 영역 의 의무 영역 X)
- 80% 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 영역 의 의무 ~동일 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 (sanity check / robustness 영역 의 의무 영역 의 의무 / 다만 Top 15 영역 의 의무 영역 의 의무 영역 의 의무 = 80% 결과 영역 의 의무 영역 의 의무 영역 의 의무)

### 2.3 Model (locked)

**XGBoost** (운영 best_params):
```json
{
  "num_boost_round": 3000,
  "eta": 0.04010004733841803,
  "max_depth": 7,
  "gamma": 0.01149445116123669,
  "reg_alpha": 2.5637951796528347,
  "reg_lambda": 3.098963995299966,
  "subsample": 0.8702724325884353,
  "colsample_bytree": 0.9215687995219334
}
```

**Ensemble baseline** (vs 비교 영역):
- 운영 CatBoost + XGBoost (32 features / 운영 best_params) → 32_ensemble_baseline

### 2.4 CV protocol (80% subset)

| Evaluation | Method | seed | 모집단 |
|---|---|---|---|
| **Cold MdAPE** | GroupKFold-5 (artist_slug) | 42 fixed | 80% / ~22,701 rows |
| **Warm MdAPE (main)** | KFold-5 | **42 / 7 / 13 (3 seeds median)** | warm slice within 80% |
| **Warm MdAPE (guard)** | GroupKFold-5 | 42 fixed | warm slice within 80% |

⚠️ **multi-seed warm 의무** (deviation 영역 의 의무 영역 의 의무 fix / sweep 영역 의 의무 영역 의 의무 1-seed 영역 의 의무 영역 의 의무 영역 의 의무 신뢰도 약함 영역 의 의무 영역 의 의무).

### 2.5 Holdout test (final / 1회)

- 80% subset 영역 의 의무 영역 의 의무 영역 의 의무 retrain (XGBoost / Top 15) → 단일 model
- Holdout 20% 영역 의 의무 영역 의 의무 predict → final MdAPE
- Holdout 영역 의 의무 영역 의 의무 source split (Artsy / Saatchi)
- Holdout 영역 의 의무 영역 의 의무 warm slice (artist 작품수 ≥ 5 within Holdout)

### 2.6 Comparison — **Binding 1개** (P1 fix / multiple comparison 방지)

**Configs** (모두 80% retrain + Holdout test):
1. **Test config (BINDING)**: Top 15 + XGBoost (winner 후보 / decision-binding 영역)
2. **Operational baseline (BINDING comparator)**: 32 + Ensemble (CB+XGB / 운영 정합)
3. **Diagnostic only (NON-binding)**: 32 + XGBoost (size-only delta / multiple comparison 영역 의 의무 영역 의 의무 채택 verdict 영역 의 의무 영역 의 의무 X)

⚠️ **Binding decision** = **Top15+XGBoost vs 32+Ensemble 만** 영역 의 의무 영역 의 의무 (single binary decision / cherry-pick 방지).

⚠️ 32+XGBoost = diagnostic / record only / decision criterion 영역 의 의무 영역 의 의무 영역 의 의무 X.

## 3. Decision Criterion (locked / 사전 정의 / decision-binding)

### 3.1 Pass / Fail criteria

**채택 (PASS / 운영 적용)** — 모든 영역 의 의무 영역 의 의무 만족 영역 의 의무:

- ✅ **G2** Holdout cold MdAPE (Top 15 / XGBoost) − Holdout cold (32 / Ensemble) ≤ +0.8
- ✅ **G1** Holdout warm MdAPE (Top 15 / XGBoost) − Holdout warm (32 / Ensemble) ≤ +0.5
- ✅ **G3** Holdout Artsy cold (Top 15 / XGBoost) − Holdout Artsy cold (32 / Ensemble) ≤ +1.0
- ✅ **G4** Holdout Saatchi cold (Top 15 / XGBoost) − Holdout Saatchi cold (32 / Ensemble) ≤ +1.0
- ✅ **CV-Holdout gap fail-safe** (locked / P1 fix):
  - Top 15 / XGBoost 영역 의 의무 영역 의 의무 80% **cold GroupKFold-5 median** = `cv_cold`
  - Top 15 / XGBoost 영역 의 의무 영역 의 의무 Holdout cold = `holdout_cold`
  - Required: `holdout_cold ≤ cv_cold + 2.117` (Phase 0 cold ens fold std × 1 영역 의 의무 영역 의 의무 영역 의 의무)
  - Violation = overfit signal → FAIL
  - 동일 rule warm: `holdout_warm ≤ warm_kfold_median_3seed + 0.5` (warm fold std 0.16 × 3 ≈ 0.5)

**비채택 (FAIL / 운영 변경 X)**:
- ❌ G1/G2/G3/G4 영역 의 의무 영역 의 의무 영역 의 의무 1 영역 의 의무 영역 의 의무 violation
- ❌ CV-Holdout gap fail-safe violation (overfit)

### 3.2 Decision matrix

| Holdout 결과 | Decision | 운영 영향 |
|---|---|---|
| 모든 Guard PASS + cold ≈ baseline + warm 개선 | **CHAMPION** | 운영 적용 의무 |
| 모든 Guard PASS + 비슷 | **TIE** | 운영 영역 의 의무 영역 의 의무 변경 X (단순화 영역 의 의무 영역 의 의무 영역 의 의무 가능 / 사용자 결정) |
| Guard 1 영역 의 의무 영역 의 의무 violation | **FAIL** | 운영 변경 X |
| Multi-violation | **FAIL** | 운영 변경 X / sweep 결과 = noise verdict |

### 3.3 Locked rules (코덱스 round 2 P2 fix)

- **Metric orientation**: MdAPE (Median Absolute Percentage Error) — **낮을수록 좋음** / 부등호 영역 의 의무 영역 의 의무 영역 의 의무 정합
- **Top 15 tie-break**: 80% fold-internal aggregate rank ASC 정렬 시 경계 동률 영역 의 의무 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 알파벳 ASC (sorted feature name 영역 의 의무 영역 의 의무) — deterministic
- **Preprocessing scope** (80% 내부 fit / Holdout apply only / leakage 방지):
  - label encoding (categorical) = train fold 내부 fit
  - SHAP / Permutation = train fold 내부
  - HP fix (운영 best_params / re-tune X)
  - missing imputation = NaN 그대로 (CatBoost native / XGBoost = NaN handling)
- **Diagnostic 비개입**: 32+XGBoost / sweep reference 결과 = **참고 record only** / 최종 verdict / 예외 규칙 생성 영역 의 의무 영역 의 의무 영역 의 의무 X

## 4. 한계 / Risk

- **Holdout 1회 test**: 다수 비교 X / 결과 noise 영역 의 의무 영역 의 의무 영역 의 의무 가능
- **Top 15 ranking** = §2.2 정합 / 본 Confirmatory 영역 의 의무 영역 의 의무 80% 내부 fold-internal 4-method 재산출 (Holdout 영역 의 의무 영역 의 의무 영역 의 의무 X / selection leakage 방지 ✓ / sweep amendment ranking = reference only)
- **Holdout warm 정의 conflict** (P2 / 본 cycle 영역 의 의무 영역 의 의무 명시): warm = "작품수 ≥ 5" 정의 / 다만 Holdout = artist GroupShuffleSplit (unseen artist) → "warm slice within Holdout" 영역 의 의무 영역 의 의무 영역 의 의무 = 모든 row cold-equivalent / G1 warm verdict 영역 의 의무 영역 의 의무 영역 의 의무 포함 / 해석력 낮음 / 다음 cycle 영역 의 의무 영역 의 의무 재정의 의무
- **HP tuning X**: 32 features 운영 best_params 영역 의 의무 영역 의 의무 = N=15 영역 의 의무 영역 의 의무 영역 의 의무 sub-optimal 영역 의 의무 영역 의 의무 영역 의 의무 가능 (다만 본 cycle scope X / 별도 cycle)
- **Ensemble vs XGBoost only**: provisional winner = XGBoost / ensemble Top 15 영역 의 의무 영역 의 의무 영역 의 의무 별도 비교 영역 의 의무 영역 의 의무 가능 (post-hoc note 영역 의 의무 영역 의 의무 영역 의 의무 record)

## 5. 진행 일정

| 단계 | 영역 | 영역 |
|---|---|---:|
| prereg doc | 본 doc | 0.5 시간 |
| 코덱스 사전 자문 | 본 doc 검수 | 0.5 |
| Holdout split + script | 80%/20% / Top 15 / XGBoost | 0.5 |
| 80% CV (sanity check) | 5 fold cold + 3 seed warm | ~30분 |
| Holdout test (final) | 80% retrain + Holdout predict | ~5분 |
| 사후 검수 + 결정 | 코덱스 + 사용자 | 0.5 |
| **합계** | — | **~2-3 시간** |

## 6. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P0 + P1 3 영역) → fix 적용 |
| 1차 fix patch (본 commit) | §2.2 (Top 15 80% 재산출 / leakage fix) / §2.6 (binding 1개) / §3.1 (CV-Holdout gap rule) |
| 2차 사전 자문 (예정) | 본 fix commit 직후 |
| 3차 사후 검수 (예정) | Holdout test 종료 직후 |
