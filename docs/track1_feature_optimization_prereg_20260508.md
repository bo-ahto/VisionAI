# 트랙 1 피처 최적화 cycle — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 운영 32 features 의 iterative loop 영역 의 최적화 (DROP / KEEP / ADD) 의 단계 별 record cycle / Warm + Cold 모두
> **Decision binding**: ❌ X (피처 최적화 의 정량 record 만 / 운영 채택 결정 = 별도 prereg cycle 의 영역)
> **분기**: `exp/track1-feature-optimization-cycle`
> **다이어그램 정합**: `docs/track1_feature_optimization_detailed.html`

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: 영향도 측정 (multi-method) / iterative loop 의 record (DROP/KEEP/ADD strategy 의 정량 영향) / Warm + Cold 별 의 영향 영역 / Iteration log dump
> - **Out-of-scope**: 운영 코드 / parquet / artifact 의 변경 / 운영 채택 결정 / 모델 retraining 의 운영 적용

## 1. Goal

운영 32 features (CatBoost cold + XGBoost warm) 의 정량 record 의 영역 의 단계 별 정량 영향 의 record:
- **Warm 영역**: KFold-5 / XGBoost / 9.70% baseline 의 영향
- **Cold 영역**: GroupKFold-5 / CatBoost (calibrated) / 38.29% baseline 의 영향
- 매 iteration 의 (N_features / Δ MdAPE / 채택) 의 record / convergence 영역 의 추적

## 2. Baseline 영역 freeze

| 영역 | Operational reported | 본 cycle 의 baseline |
|---|---|---|
| Cold MdAPE (calibrated cross-fit guarded) | 38.29% | 동일 |
| Cold baseline MdAPE (GroupKFold) | 39.38% | 동일 |
| Warm KFold MdAPE (XGBoost) | 9.70% | 동일 |
| Overall ensemble | 38.7% | 동일 |
| Source segment Artsy cold | 33.5% | 동일 |
| Source segment Saatchi cold | 41.7% | 동일 |
| **N features** | **32** | **시작점** |

## 3. Method (5 Phase 의 단계)

### 3.1 Phase 0 (Setup / 1-2 일)

#### A. Baseline 영역 의 정량 freeze
- 운영 artifact 의 sha-256 freeze (B-2 PR #49 의 reproduction PASS 정합)
- baseline metrics 의 record (위 §2)

#### B. 영향도 측정 의 4 method 의 산출 (multi-method ensemble)

| Phase | Method | 도구 | 영역 |
|---|---|---|---|
| **A (빠른)** | CatBoost FI (PVC) | `cb.get_feature_importance()` | 즉시 / 합계 100% |
| **A (빠른)** | XGBoost gain/weight/cover | `xgb.get_score(importance_type=...)` | 즉시 |
| **B (정확)** | SHAP (TreeSHAP) | `shap.TreeExplainer` | 개별 prediction 의 분해 |
| **C (객관)** | Permutation Importance | `sklearn.inspection.permutation_importance` | model-agnostic / CV 영향 |

> 본 cycle 의 영향도 record = 4 method 모두 산출 의무 / 단일 method 의 의존 X.

#### C. Iteration log format 정의

```json
{
  "iter": 0,
  "phase": "baseline",
  "strategy": null,
  "n_features": 32,
  "features_dropped": [],
  "features_added": [],
  "cold_mdape": 38.29,
  "warm_mdape": 9.70,
  "delta_cold": 0.00,
  "delta_warm": 0.00,
  "guard_check": {"warm_ok": true, "overall_ok": true, "segment_ok": true},
  "verdict": "baseline",
  "codex_review": null,
  "timestamp": "2026-05-08T..."
}
```

### 3.2 Phase 1 (DROP-A: Zero-Importance / 1-2 일)

| 영역 | 영역 |
|---|---|
| **목표** | 영향도 0% feature 의 즉시 제거 + 정량 record |
| **후보** | placeholder 3: `ho_price_level`, `medium_price_level`, `profile_completeness` (운영 = 0% 정합) |
| **검증** | 재학습 + 5-Fold CV / Δ Cold MdAPE / Δ Warm MdAPE |
| **PASS criterion** | Δ Cold MdAPE ≤ +0.1%p AND Δ Warm MdAPE ≤ +0.1%p (악화 X) |
| **예상 영향** | 거의 동일 (placeholder = 0% influence) |
| **N 변화** | 32 → 29 |

### 3.3 Phase 2 (DROP-B: Low-Importance / 2-3 일)

| 영역 | 영역 |
|---|---|
| **목표** | 영향도 < 0.1% feature 의 신중 제거 + CV 검증 |
| **후보** | `is_edition` (0%) → `is_unique` (0.02%) → `attribution_class` (0.03%) → `is_krw` (0.05%) → ... |
| **방식** | 1 feature / 1 iteration 의 의무 (한 번에 multiple 제거 X) |
| **PASS criterion** | Δ Cold MdAPE ≤ +0.05%p AND Δ Warm MdAPE ≤ +0.05%p |
| **종료** | 1 iter 의 Δ > +0.1%p 시 = phase 종료 |
| **N 변화** | 29 → 25-28 (예상) |

### 3.4 Phase 3 (DROP-C: Correlated / 2-3 일)

| 영역 | 영역 |
|---|---|
| **목표** | correlated features 영역 의 redundant 제거 |
| **후보 영역** | ho ↔ ln_ho ↔ ho_power (호수 영역) / area_cm2 ↔ ln_area (면적 영역) / artist_birth_year ↔ has_birth_year |
| **검증** | corr matrix 의 \|corr\| > 0.95 의 영역 식별 + 영향 작은 영역 제거 |
| **PASS criterion** | Δ Cold MdAPE ≤ +0.1%p AND Δ Warm MdAPE ≤ +0.1%p |
| **예상 영향** | 트리 모델 의 영역 = correlated 의 영향 작음 (단 검증 의무) |
| **N 변화** | 25-28 → 23-26 (예상) |

### 3.5 Phase 4 (ADD-A: Interaction / 3-5 일)

| 영역 | 영역 |
|---|---|
| **목표** | interaction term 의 추가 (가설 H4: endorsement effect) |
| **후보** | `career_stage × gallery_tier` / `artist_total_works × ho` / `ln_followers × medium_category` |
| **방식** | 1 interaction / 1 iteration |
| **PASS criterion** | Δ Cold MdAPE ≤ −0.1%p (개선) OR Δ Warm MdAPE ≤ −0.1%p |
| **검증** | SHAP interaction effect 의 정량 |
| **N 변화** | 23-26 → 24-28 |

### 3.6 Phase 5 (ADD-B: As-of Stats / 3-5 일 / Warm only)

| 영역 | 영역 |
|---|---|
| **목표** | 작가 가격 통계 의 추가 (warm only / leakage 방지) |
| **후보** | `artist_price_median` / `artist_price_std` / `artist_price_count` |
| **⚠️ 의무** | **train-fold 만 fit / test-fold 미사용** (leakage 방지 의무) |
| **PASS criterion** | Warm 영역 의 큰 boost (Δ Warm MdAPE ≤ −0.5%p) / Cold 영역 = 영향 X |
| **검증** | leakage detection (test fold 의 통계 영역 의 의무 검증) |
| **N 변화** | 24-28 → 25-31 (warm 영역) |

### 3.7 Phase 6 (ADD-C: Engineered / 3-5 일)

| 영역 | 영역 |
|---|---|
| **목표** | domain knowledge engineered features 추가 |
| **후보** | `source_conditional_ho_power` (β=0.84 USD vs β=0.74 KRW) / `gallery_avg_price` (as-of) / `medium_avg_price` (as-of) |
| **PASS criterion** | Δ Cold MdAPE ≤ −0.1%p (개선) |
| **N 변화** | 25-31 → 26-33 |

### 3.8 Phase 7 (수렴 검사 / 1 일)

- **수렴 criterion**: 최근 3 iter 의 \|Δ Cold MdAPE\| < 0.1%p AND \|Δ Warm MdAPE\| < 0.05%p
- **YES**: 수렴 / Phase 8 진입
- **NO**: 다른 strategy 의 의무 / Phase 1-6 의 추가 iteration

### 3.9 Phase 8 (최종 보고 / 1-2 일)

- 최종 N* features 의 정량 record
- Iteration log 의 dump (JSON + CSV)
- 결과 보고서 + 코덱스 검수
- PR 작성

## 4. CV protocol (모든 phase 영역 의 동일)

| Evaluation | 영역 | 모집단 |
|---|---|---|
| **Cold MdAPE** | GroupKFold-5 (artist_slug) + Source-cell calibration | 28,376 rows / 1,551 artists |
| **Warm MdAPE** | KFold-5 (random_state=42) | 27,062 rows (warm slice / 작품수 ≥ 5) |
| **Overall ensemble** | 0.5 × cold + 0.5 × warm (운영 영역 정합) | full |
| **Source segment** | 위 영역 의 Artsy / Saatchi 분리 record | 7,289 / 21,087 |

> **모든 CV** = `random_seed=42` 의 fixed (reproducibility 의무).

## 5. Guard metric (every phase / 4 영역)

| # | Guard | 임계 |
|---|---|---|
| **G1** | Warm KFold MdAPE 악화 | ≤ +0.5%p |
| **G2** | Overall ensemble 악화 | ≤ +0.8%p |
| **G3** | Artsy segment cold 악화 | ≤ +1.0%p |
| **G4** | Saatchi segment cold 악화 | ≤ +1.0%p |

> 1 phase 의 채택 = Primary (Δ Cold) PASS AND Guard 4 영역 모두 PASS.

## 6. Decision binding

❌ **본 cycle = record only**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| 운영 코드 (`prepare_*` / `train_*` / `primary_*`) | **변경 X** |
| 운영 parquet (`*.parquet`) | **변경 X** |
| 운영 artifact (catboost.cbm / xgboost.json / etc) | **변경 X** |
| 운영 채택 결정 | **본 cycle 영역 X** (별도 decision-binding cycle 의무) |
| 다른 cycle 의 verdict | **모두 변경 X** |

**본 cycle 의 영향 영역 만**:
- ✅ 4 method 영향도 의 정량 record (Phase A/B/C)
- ✅ 단계 iteration 의 정량 record (DROP-A/B/C / ADD-A/B/C)
- ✅ Warm + Cold 별 의 영향 영역 의 record
- ✅ 최적 N* features 의 후보 record (운영 채택 결정 영역 의 정량 입력)

## 7. 코덱스 검수 의 의무 영역

| 영역 | 코덱스 검수 영역 |
|---|---|
| Phase 0 | Baseline 의 정량 정합 / iteration log format / multi-method ensemble |
| Phase 1-6 의 매 iteration | 영향도 method 의 정합 / leakage 영역 의 검증 / CV protocol / Guard PASS |
| Phase 7 (수렴) | 수렴 criterion 의 정합 / 다른 strategy 의 의무 영역 |
| Phase 8 (최종) | 결과 보고서 / 운영 채택 결정 영역 의 별도 cycle 의 의무 명시 |

## 8. 진행 일정 (예상)

| Phase | 영역 | 일수 | 의무 |
|---|---|---:|---|
| 0 | Setup + multi-method 영향도 | 1-2 | baseline freeze |
| 1 | DROP-A (zero) | 1-2 | placeholder 3 |
| 2 | DROP-B (low) | 2-3 | 1 feature / iter |
| 3 | DROP-C (correlated) | 2-3 | corr matrix |
| 4 | ADD-A (interaction) | 3-5 | 1 interaction / iter |
| 5 | ADD-B (as-of / warm) | 3-5 | leakage 방지 ⚠️ |
| 6 | ADD-C (engineered) | 3-5 | source-conditional |
| 7 | 수렴 검사 | 1 | criterion |
| 8 | 최종 보고 | 1-2 | PR |
| **합계** | — | **17-28 일** | |

## 9. PASS / FAIL 기준 (cycle 종료 영역)

### 9.1 PASS (cycle 종료 + 정량 record 산출)

- ✅ 모든 phase 의 iteration log 의 dump (JSON + CSV)
- ✅ 4 method 영향도 의 record (Phase A/B/C)
- ✅ 최종 N* features 의 후보 record (Warm + Cold 별)
- ✅ Guard 4 영역 의 매 phase 의 PASS record
- ✅ 운영 코드 / parquet / artifact 변경 X (read-only / sha-256 unchanged)
- ✅ 코덱스 검수 round 모두 GO

### 9.2 FAIL (cycle 종료 X / 디버깅)

위 중 하나 미충족 → 별도 디버깅 / cycle 의 의무.

## 10. 후속 cycle (조건부 / 사용자 결정)

본 cycle 의 PASS 후 의 후속 영역 (모두 별도 prereg / decision-binding cycle 의무):

1. **운영 채택 cycle**: 본 cycle 의 N* features 의 운영 적용 / 모델 retraining / source_calibration 재생성
2. **Saatchi 영역 의 별도 cycle**: source-conditional 의 별도 추정 (코덱스 권고 의 후속)
3. **Optuna re-tune cycle**: 새 N* features 의 hyperparameter 재 optimize

## 11. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
