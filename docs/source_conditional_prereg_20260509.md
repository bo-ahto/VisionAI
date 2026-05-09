# Source-Conditional Cycle — Separate Models (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**:
> - `docs/confirmatory_prereg_20260509.md` (Confirmatory FAIL / Saatchi G4 +3.19)
> - `experiments/track1_optimization/confirmatory/CONFIRMATORY_REPORT.md`
>
> **Decision binding**: ✅ **YES** (운영 채택 결정 영역)

> ⚠️ **본 cycle 영역 의 의무 위치**:
> - Confirmatory cycle FAIL → 운영 32+Ensemble 유지 / Saatchi cold +3.19 큰 악화
> - 본 cycle = source-conditional separate models 영역 의 의무 영역 의 의무 운영 채택 가능 영역 의 의무 영역 의 의무 검증

## 1. Goal

**Separate models** (Artsy-only + Saatchi-only) 영역 의 의무 영역 의 의무 운영 unified model (32+Ensemble) 대비 영역 의 의무 영역 의 의무 = unseen Holdout test → 운영 채택 결정.

**Hypothesis (preregistered)**: Source 분리 학습 영역 의 의무 영역 의 의무 영역 의 의무:
- Saatchi cold MdAPE 개선 (≤ baseline - 0.5%p / hard gate)
- Overall cold MdAPE = noise band 내 (≤ baseline + 0.8%p)
- Artsy cold MdAPE 비악화 (≤ baseline + 1.0%p / hard gate)

## 2. Method (코덱스 사전 자문 P0/P1 fix 적용)

### 2.1 Locked Holdout split — **Fresh** (P0 fix / 재사용 X)

**Confirmatory Holdout (random_state=20260509) = sealed / 본 cycle 재사용 X**.

**New split** (binding):
- artist GroupShuffleSplit (artist overlap X)
- 80% / 20%
- **random_state = 20260510** (locked / fresh)
- artist count: 1,551 → 80% (~1,240) / 20% (~311)

**Holdout 의무 (locked)**:
- ❌ 모델 학습 X / ranking X / feature selection X / HP tuning X
- ✅ Final test (1회 / verdict 결정) 만

### 2.2 Models (locked / 32 features fixed / HP fixed / P1 fix)

**Test config (BINDING)**: Separate models (source-conditional)
- **Artsy-only model**: 32 features (CB_FEATURES_BASE) + 운영 best_params (Ensemble: CatBoost + XGBoost)
  - Train data = 80% Artsy only
  - Predict: Holdout Artsy only
- **Saatchi-only model**: 32 features (CB_FEATURES_BASE) + 운영 best_params (Ensemble)
  - Train data = 80% Saatchi only
  - Predict: Holdout Saatchi only
- **Unified inference**: source 별 라우팅 (input row 의 source → 해당 model)

**Comparator (BINDING)**: Unified 32 + Ensemble (운영 정합)
- Train data = 80% all (Artsy + Saatchi 통합 / 운영 영역 의 의무 영역 의 의무 영역)
- Predict: Holdout all

⚠️ **HP / features 고정** (P1 fix): re-tune X / Top N X / ranking X / source-별 different features X.

### 2.3 CV protocol (80% subset / sanity check / non-binding)

| Evaluation | Method | seed | 모집단 |
|---|---|---|---|
| Cold MdAPE (per source) | GroupKFold-5 (artist_slug / source 별 분리) | 42 fixed | Artsy 80% / Saatchi 80% |
| Cold overall (separate routed) | source별 model → unified prediction | 42 | 80% all |

⚠️ Warm CV = **binding holdout gate 영역 의 의무 영역 의 의무 영역 의 의무 X** (artist-unseen holdout = warm 정의 conflict / Confirmatory deviation 정합) / non-binding source별 KFold-5 record.

### 2.4 Holdout test (final / 1회)

- 80% Artsy 영역 의 의무 영역 의 의무 retrain (Ensemble) → Holdout Artsy predict
- 80% Saatchi 영역 의 의무 영역 의 의무 retrain (Ensemble) → Holdout Saatchi predict
- 80% all 영역 의 의무 영역 의 의무 unified retrain (Ensemble) → Holdout all predict
- Combined separate prediction: source 별 model 결과 영역 의 의무 영역 의 의무 영역 의 의무 통합 → overall cold MdAPE

## 3. Decision Criterion (locked / decision-binding)

### 3.1 Pass / Fail criteria (Holdout binding)

**채택 (PASS / 운영 적용)** — 모든 gate 만족:

- ✅ **Primary (overall)**: Holdout overall cold MdAPE (separate routed) − unified ≤ +0.8%p (G2 noise band)
- ✅ **Hard gate 1 (Artsy)**: Holdout Artsy cold (Artsy-only) − Holdout Artsy cold (unified) ≤ +1.0%p (G3)
- ✅ **Hard gate 2 (Saatchi)**: Holdout Saatchi cold (Saatchi-only) − Holdout Saatchi cold (unified) **≤ -0.5%p** (P1 fix / **개선 요구** / separate serving complexity 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)

**비채택 (FAIL / 운영 변경 X)**:
- ❌ Primary > +0.8 OR Artsy > +1.0 OR Saatchi > -0.5 (개선 미달)

### 3.2 Decision matrix

| Holdout 결과 | Decision | 운영 영향 |
|---|---|---|
| 모든 gate PASS + Saatchi Δ ≤ -0.5%p | **CHAMPION** | Source-conditional 운영 적용 의무 |
| Saatchi Δ > -0.5%p (insufficient improvement) | **TIE/FAIL** | 운영 unified 유지 |
| Primary > +0.8 OR Artsy > +1.0 violation | **FAIL** | 운영 unified 유지 |

⚠️ **Saatchi 개선 의무** (P1 fix): separate serving 복잡도 (source routing / source별 calibration) 정당화 의무. 단순 non-inferiority X.

## 4. Locked rules (코덱스 사전 자문 P2 fix)

- **Metric**: cold MdAPE (낮을수록 좋음)
- **HP**: 운영 best_params 고정 (re-tune X / source-별 다른 HP X)
- **Features**: CB_FEATURES_BASE (32) 고정 / Top N / ranking / source-별 다른 features X
- **Preprocessing**: 80% 내부 fit / Holdout apply only (label encode source-별 분리)
- **Warm**: binding 영역 의 의무 영역 의 의무 X / CV guard 영역 의 의무 영역 의 의무 record only
- **Diagnostic**: 32+XGBoost only (32+Ensemble unified) 영역 의 의무 영역 의 의무 영역 의 의무 = binding comparator
- **Multiple comparison 방지**: binding family = **separate vs unified 1개만**

## 5. 한계 / Risk

- **Separate serving complexity**: source routing / source별 calibration 영역 의 의무 영역 의 의무 = 운영 복잡도 증가
- **Source routing 오류**: input row 의 source 영역 의 의무 영역 의 의무 영역 의 의무 영역 = 잘못된 model 라우팅 risk
- **Artsy 표본 작음** (7,640 vs Saatchi 21,721): Artsy split variance 큼
- **Source effect 가설**: "진짜 source regime" vs "누락 패턴/측정 차이" — 본 cycle 영역 의 의무 영역 의 의무 영역 의 의무 검증 X (다음 cycle 영역 의 의무 영역 의 의무 의무)
- **Holdout 1회 test**: noise 가능
- **Calibration**: source-cell calibration 영역 의 의무 영역 의 의무 영역 의 의무 본 cycle scope X (별도 cycle / 운영 채택 후)

## 6. 진행 일정

| 단계 | 영역 | 시간 |
|---|---|---:|
| prereg doc | 본 doc | 0.5 시간 |
| 코덱스 사전 자문 | round 2 (fix 후) | 0.5 |
| Script + Holdout split | 80%/20% / Artsy + Saatchi 분리 / Ensemble | 0.5 |
| 80% CV (sanity check) | source별 GKF-5 | ~30분 |
| Holdout test (final) | 3 retrain (Artsy / Saatchi / unified) + Holdout predict | ~10분 |
| 사후 검수 + 결정 | 코덱스 + 사용자 | 0.5 |
| **합계** | — | **~2-3 시간** |

## 7. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P0 holdout 재사용 + P0 family search + P1 warm conflict) → fix |
| 2차 사전 자문 (예정) | 본 doc commit 직후 |
| 3차 사후 검수 (예정) | Holdout test 종료 직후 |
