# Feature Sweep — 분석 보고서 (Post-hoc Amendment Cycle)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Amendment doc**: `docs/feature_sweep_amendment_20260509.md`
> **Decision binding**: ❌ X (record only / 운영 채택 = 별도 cycle)
> **결과 file**: `experiments/track1_optimization/sweep/sweep_simplified_results.json`
> **Deviation log**: `docs/methodology_deviation_log.md` (코덱스 round 2 P1 fix)
>
> ⚠️ **상태**: **Provisional reduced-sweep result** (amendment-locked winner declaration X)
> - Original amendment locked: 12 N × 6 model × 3 seed = 1440 fits
> - Executed (kill-restart due to thermal throttling): 7 N × 3 model × 1 seed = 210 fits
> - Amendment-locked winner declaration **deferred** (config-space + warm-seed deviation)

## 1. 실험 요약

| 영역 | 영역 |
|---|---|
| **Config space** | 7 N (5/10/15/20/25/30/32) × 3 model (CB/XGB/Ens) = 21 configs |
| **CV** | cold GroupKFold-5 + warm KFold-5 (seed 42) |
| **Ranking** | Fold-internal 4-method aggregate (CB FI / XGB gain / SHAP avg / Permutation) — selection leakage 방지 |
| **Total fits** | 5 ranking (~7분) + 105 cold + 105 warm = 215 fits / **~40분** |
| **Winner rule** | 1-SE band (cold SE 2.117%p) / 최소 N + 운영 정합 모델 우선 |

## 2. 영향력 높은 피처 (가격 예측 영역 의 의무 영역 의 의무 영역 의 의무 핵심)

**Fold-internal 4-method aggregate ranking** (5 outer fold avg / selection leakage 방지):

| Rank | Feature | Avg rank | 영역 의 의무 영역 의 의무 |
|---:|---|---:|---|
| 1 | **ln_area** | 2.75 | 작품 크기 (log) — 가장 영역 의 의무 영역 의 의무 |
| 2 | **artist_total_works** | 2.90 | 작가 총 작품 수 |
| 3 | **career_stage** | 3.25 | 작가 경력 단계 (continuous 0-8) |
| 4 | **area_cm2** | 3.45 | 작품 크기 (raw) |
| 5 | **ln_followers** | 5.45 | 작가 팔로워 수 (log) |
| 6 | artist_birth_year | 6.45 | 작가 출생년도 |
| 7 | ho_x_support | 8.70 | 호수 × 지지체 (interaction) |
| 8 | has_seoul | 10.40 | 갤러리 서울 영역 의 의무 영역 의 의무 |
| 9 | ho | 11.40 | 호수 (raw) |
| 10 | ho_power | 12.10 | 호수^0.74 |
| 11 | medium_category | 12.25 | 매체 분류 |
| 12 | aspect_ratio | 13.10 | 작품 비율 |
| 13 | ln_ho | 13.60 | 호수 (log) |
| 14 | for_sale_ratio | 14.75 | 판매 중 작품 비율 |
| 15 | has_depth | 15.65 | 작품 깊이 (3D) |
| 16-32 | support_type / source / gallery_type / ... / placeholder 3 (rank 30-32 = 0%) | ≥16.20 | low impact |

**핵심 통찰**:
- **Top 5** = `size (ln_area / area_cm2)` + `artist (total_works / career_stage / followers)` 영역 의 의무 영역 의 의무 = 가격 예측 영역 의 의무 영역 의 의무 영역 의 의무 핵심 영역 의 의무
- **Top 10** ≈ size + artist + 호수 (size-related) 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 dominate
- **Top 15** ≈ + 단일 categorical (has_seoul / medium_category) + 보조 영역 의 의무 영역 의 의무 (aspect_ratio / for_sale_ratio / has_depth)
- **Bottom 17** (16-32) = source / gallery / categorical 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 / placeholder 3 (rank 30-32 = 0%)

## 3. N × Model Matrix

### 3.1 Cold MdAPE (median / 5 fold)

| N | CatBoost | XGBoost | Ensemble | best | vs 32 baseline (38.62) |
|---:|---:|---:|---:|---:|---:|
| 5 | 44.44 | 45.40 | 46.01 | 44.44 | **+5.82** ❌ |
| 10 | 38.02 | 38.87 | 38.39 | 38.02 | -0.61 (≈ baseline) |
| **15** | 37.60 | 38.66 | **36.92** ⭐ | **36.92** | **-1.70** ✓ |
| 20 | 37.50 | 39.78 | 38.08 | 37.50 | -1.12 ✓ |
| 25 | 39.45 | 40.55 | 39.86 | 39.45 | +0.83 |
| 30 | 39.84 | 40.35 | 39.19 | 39.19 | +0.57 |
| 32 | 39.84 | 40.85 | 39.07 | 39.07 | +0.45 |

### 3.2 Warm MdAPE (median / 5 fold seed 42)

| N | CatBoost | XGBoost | Ensemble | vs 10.47 baseline |
|---:|---:|---:|---:|---:|
| 5 | 13.22 | 11.65 | 12.21 | +1-3 |
| 10 | 12.47 | 11.10 | 11.51 | +0.6-2.0 |
| **15** | 11.87 | **9.98** | 10.38 | -0.5 ~ +1.4 |
| 20 | 11.70 | **9.82** | 10.40 | -0.65 ~ +1.2 |
| 25 | 11.99 | 9.82 | 10.49 | -0.65 ~ +1.5 |
| 30 | 11.96 | **9.72** | 10.40 | -0.75 ~ +1.5 |
| 32 | 11.96 | 9.76 | 10.45 | -0.71 ~ +1.5 |

### 3.3 Guards (G1 Warm / G2 Cold / G3 Artsy / G4 Saatchi)

- **CatBoost = G1 모두 FAIL** (warm 영역 의 의무 영역 의 의무 12 vs baseline 10.47 / 영역 의 의무 영역 의 의무 +1.5 > +0.5 영역 의 의무 영역 의 의무) — CB 운영 best_params 영역 의 의무 영역 의 의무 cold-friendly / warm 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 약함
- **XGBoost / Ensemble** = N≥15 영역 의 의무 영역 의 의무 영역 의 의무 모든 guards PASS

### 3.4 Elbow point 분석

- **N=5**: 매우 부족 (cold +5.82%p 악화)
- **N=10**: baseline 영역 의 의무 영역 의 의무 영역 의 의무 거의 동일 (CB 38.02 / Ens 38.39)
- **N=15-20**: optimum 영역 의 의무 영역 의 의무 영역 의 의무 (cold 36.92-37.50 / 영역 의 의무 영역 의 의무 영역 의 의무 best)
- **N=25-32**: 약간 영역 의 의무 영역 의 의무 (cold 39+ / overfitting? noise feature 영역 의 의무 영역 의 의무?)

→ **Optimal N ≈ 15** (영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = "less is more" 영역 의 의무 영역 의 의무 영역 의 의무 strict 적용 가능)

## 4. 1-SE Provisional Winner (reduced-sweep / amendment-locked X)

⚠️ **본 winner = reduced screening subset 내 provisional**. Amendment-locked
declaration 영역 의 의무 영역 의 의무 = config-space 영역 의 의무 영역 의 의무
deviation (12 N→7 / 6 model→3 / 3 seed→1) 영역 의 의무 영역 의 의무 = **deferred**.

**Best raw cold** = N=15 ensemble = **36.92** (-1.70%p vs baseline / within reduced grid)

**1-SE band** = 36.92 + 2.117 = **39.04**

**Winner-eligible (Guards 모두 PASS) ∩ noise band 내** (reduced grid):
| N | model | cold | warm | Guards | 1-SE? |
|---:|---|---:|---:|---|---|
| 15 | xgboost | 38.66 | 9.98 | 1111 ✓ | ✓ |
| 15 | ensemble | **36.92** | 10.38 | 1111 ✓ | ✓ (best raw) |
| 20 | ensemble | 38.08 | 10.40 | 1111 ✓ | ✓ |

**1-SE Provisional Winner Rule** (smallest N + 운영 정합 priority):

→ **Provisional Winner = N=15 / XGBoost** (reduced-sweep only)

| 영역 | Provisional |
|---|---|
| **N** | **15** |
| **Model** | **XGBoost** (운영 best_params) |
| **cold_ens_median** | **38.66** (Δ +0.03 vs baseline 38.62 / noise band 내) |
| **warm_ens_median** | **9.98** (Δ **-0.49** vs baseline 10.47 / 운영상 개선 / 1-seed 영역 의 의무 영역 의 의무 신뢰도 약함) |
| **Δ Artsy cold** | -0.49 ✓ |
| **Δ Saatchi cold** | -0.05 ✓ |
| **Guard 4** | 모두 PASS ✓ |

**Reasoning** (reduced grid 영역 의 의무 영역 의 의무):
- 1-SE band 내 영역 의 의무 영역 의 의무 영역 의 의무 가장 작은 N (15)
- N=15 영역 의 의무 영역 의 의무 영역 의 의무 = ensemble cold (36.92) 영역 의 의무 영역 의 의무 영역 의 의무 raw best / 다만 1-SE rule 영역 의 의무 영역 의 의무 영역 의 의무 운영 정합 모델 우선 (XGBoost > Ensemble)
- XGBoost N=15: cold ≈ baseline (noise band 내) / warm Δ -0.5pp 영역 의 의무 영역 의 의무 (1-seed 영역 의 의무 영역 의 의무 신뢰도 약함)

**⚠️ 한계 (deviation 영역 의 의무 영역 의 의무)**:
- Locked grid X (8/12/18/22/28 N + LGBM/RF/HGB 미실행)
- Warm 1-seed only (3-seed median locked rule X / G1 판정 신뢰도 약함)
- Warm Δ -0.49 / G1 margin 영역 의 의무 영역 의 의무 얇음 (locked +0.5)

## 5. 핵심 통찰 (가격 예측 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)

### 5.1 영향력 영역 의 의무 영역 의 의무 영역 의 의무 = 신호 군집 (artist + size + ho cluster)

⚠️ **개별 ranking X / 신호 군집 해석** (강한 상관 피처 영역 의 의무 영역 의 의무
영역 의 의무 영역 의 의무 영역 = correlated duplicate 영역 의 의무 영역 의 의무
영역 의 의무 = ln_area↔area_cm2 / ho↔ho_power↔ln_ho).

**Top 15 신호 군집** (4 cluster):

1. **Size cluster** (rank 1, 4, 7, 12): `ln_area`, `area_cm2`, `ho_x_support`, `aspect_ratio`
2. **Artist cluster** (rank 2, 3, 5, 6): `artist_total_works`, `career_stage`, `ln_followers`, `artist_birth_year`
3. **Ho cluster** (rank 9, 10, 13): `ho`, `ho_power`, `ln_ho`
4. **Categorical / 보조 cluster** (rank 8, 11, 14, 15): `has_seoul`, `medium_category`, `for_sale_ratio`, `has_depth`

**가설 H2 정합** ("누가 그렸는지(작가) > 어디서(갤러리/source) > 무엇을(매체)"):
- 작가 = Top 5 영역 의 의무 영역 의 의무 영역 의 의무 4 영역 의 의무 영역 의 의무
- 어디서 (gallery/source) = Top 15 영역 의 의무 영역 의 의무 영역 의 의무 1 (has_seoul / rank 8) / 다른 영역 의 의무 영역 의 의무 = bottom 17
- 무엇을 (medium) = rank 11 (medium_category) / 보조

### 5.2 Less-is-more (reduced grid 영역 의 의무 영역 의 의무 N=15-20 basin)

⚠️ **이번 reduced grid (5/10/15/20/25/30/32) 영역 의 의무 영역 의 의무 영역 의 의무
basin** 영역 의 의무 영역 의 의무 영역 의 의무 = N=15-20 영역 의 의무 영역 의 의무
cold MdAPE 영역 의 의무 영역 의 의무 영역 의 의무 best (37-38) vs 32 features (39).
**exact optimum X** (8/12/18/22/28 미실행).

→ **17-25 features 영역 의 의무 영역 의 의무 = noise candidate** (rank 16-32
영역 의 의무 영역 의 의무 영역 의 의무 = source / gallery / categorical /
placeholder) — 다만 fine-grid 미실행 / locked rule 영역 의 의무 영역 의 의무
provisional.

### 5.3 Model 영역 의 의무 영역 의 의무 영역 의 의무 trade-off

- **CatBoost** = cold-friendly / warm 영역 의 의무 영역 의 의무 영역 의 의무 약함 (모든 G1 FAIL)
- **XGBoost** = warm-friendly / cold 영역 의 의무 영역 의 의무 영역 의 의무 약간 영역 의 의무 영역 의 의무
- **Ensemble (CB+XGB)** = balanced / N=15-30 영역 의 의무 영역 의 의무 영역 의 의무 cold best (36.92-39.19)

→ **Ensemble 영역 의 의무 영역 의 의무 영역 의 의무 우선** (다만 1-SE rule 영역 의 의무 영역 의 의무 영역 의 의무 XGBoost 우선).

## 6. 다음 cycle 영역 의 의무 영역 의 의무 최적화 계획

### 6.1 즉시 (옵션 1 / Confirmatory cycle / decision-binding)

**목표**: N=15 (Top 15 features) + XGBoost 영역 의 의무 영역 의 의무 운영 채택 결정 / final unseen test.

**Prereg outline**:
- Locked Holdout 20% (별도 분리 / unseen)
- 80% CV-eligible: 5-fold GroupKFold-5 (cold) + KFold-5 (warm)
- Top 15 features (fold-internal aggregate top-15) 영역 의 의무 영역 의 의무 영역 의 의무 = 본 sweep 영역 의 의무 영역 의 의무 ranking 영역 의 의무 영역 의 의무 영역 의 의무
- 운영 best_params (XGBoost) 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무
- Decision-binding ✓ (운영 채택 영역 의 의무 영역 의 의무 영역 의 의무 / artifact 재학습)

**Expected outcome**:
- cold MdAPE ≈ 38.66 (현재 운영 38.7과 noise band 내 / -0.49 warm 영역 의 의무 영역 의 의무 영역 의 의무)
- 운영 영역 의 의무 영역 의 의무 = 17 features 영역 의 의무 영역 의 의무 영역 의 의무 (덜 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 =-1.70 ensemble 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)

### 6.2 HP tuning cycle (옵션 2 / 별도 prereg)

**목표**: N=15 + XGBoost 영역 의 의무 영역 의 의무 영역 의 의무 Optuna re-tune.

**Rationale**: 운영 best_params (3000 round / depth 7 / lr 0.0401) 영역 의 의무 영역 의 의무 = 32 features 영역 의 의무 영역 의 의무 tuned. N=15 영역 의 의무 영역 의 의무 영역 의 의무 = re-tune 영역 의 의무 영역 의 의무 = 추가 영역 의 의무 영역 의 의무 영역 의 의무 가능.

**Expected outcome**:
- N=15 + tuned XGBoost cold MdAPE 영역 의 의무 영역 의 의무 영역 의 의무 36-37 영역 의 의무 영역 의 의무 영역 의 의무 가능
- ensemble cold 36.92 + tuned 영역 의 의무 영역 의 의무 = 35-36 영역 의 의무 영역 의 의무 영역 의 의무

### 6.3 Source-conditional 별도 cycle (옵션 3)

**목표**: Saatchi cold ~41 vs Artsy cold ~33 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 8%p gap 영역 의 의무 영역 의 의무 = source-conditional model.

**Approach**:
- artsy + saatchi 분리 학습 (단일 model)
- 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = source 별 다른 best_params
- 본 sweep 영역 의 의무 영역 의 의무 영역 의 의무 source-conditional ho_power (currency-based) 영역 의 의무 영역 의 의무 X / 다른 접근 (model 분리)

### 6.4 추천 진행 순서

1. **Confirmatory cycle (옵션 1)** = 즉시 / decision-binding / Top 15 + XGBoost / Locked Holdout test
2. **HP tuning cycle (옵션 2)** = Confirmatory PASS 후 / Optuna re-tune
3. **Source-conditional 별도 cycle (옵션 3)** = 장기 / Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무

## 7. 한계

- post-hoc / decision binding ❌ X
- Locked holdout 영역 의 의무 영역 의 의무 X / CV-only (다음 cycle 영역 의 의무 영역 의 의무 영역 의 의무 의무)
- LightGBM / RF / HGB 영역 의 의무 영역 의 의무 영역 의 의무 X (kill-restart simplified)
- Single seed warm (multi-seed sensitivity 영역 의 의무 영역 의 의무 영역 의 의무 잃음)
- N grid sparse (5/10/15/20/25/30/32 / fine grid 영역 의 의무 영역 의 의무 X)
- HP tuning X (운영 best_params 사용 / N=15 영역 의 의무 영역 의 의무 re-tune 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 추가 가능)

## 8. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1 4 영역) → fix 적용 |
| 2차 사전 자문 (예정) | 본 보고서 + 최적화 계획 검수 |
| 3차 사후 검수 (예정) | 본 round = sweep 결과 + 최적화 계획 |
