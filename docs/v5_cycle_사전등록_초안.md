# V5 Cycle Pre-registration (초안 — 분포-비의존 항목 사전 작성)

> **상태**: 초안 (DRAFT). 본 마이그레이션 데이터 도착 후 분포-의존 항목 (X cell drop threshold, segment 최소 n) 확정하여 commit.
>
> **작성 시점**: 2026-05-04 (마이그레이션 전)
>
> **본 등록 규율**: 코덱스 7차 자문 권고 — 사전등록은 본 데이터 기준 confirmatory commitment. 본 초안의 분포-비의존 항목은 변경 시 deviation log 기록.
>
> **Pilot 분리 명시**: This preregistration was finalized after exploratory pilot diagnostics on a separate pre-migration sample (V4 cycle data, Artsy 7,289 + Saatchi 21,087 = 28,376건).

## 0) Metadata
- **Cycle**: V5
- **Date (draft)**: 2026-05-04
- **Date (finalized)**: ____ (본 마이그레이션 후)
- **Owners**: Bo
- **Related PRs**:
  - Eval framework PR: ____ (예정 — `feature/v5-eval-framework` branch)
  - Experiment PR(s): ____
- **Baseline (fixed)**: `v3-filtered_tuned`
  - Model: CatBoost + XGBoost ensemble
  - Feature count: 32 (CB_FEATURES_BASE)
- **Scope (pre-registered)**:
  - A: image retrieval prior (visual kNN prior, frozen DINOv2-base)
  - C-lite: GPBoost mixed-effects (sequential residualization)
  - A + C-lite (통합)
- **Out of scope unless deviation logged**:
  - 새 model family (TabPFN 등 challenger 만 허용)
  - 새 segment 정의
  - 추가 tuning round
  - 새 holdout scheme

## 1) Hypotheses

### A. Image Retrieval Prior

- **H_A1**: Cold-start 작가 (0-shot exposure) 의 holdout MdAPE 가 baseline 대비 일관되게 (3 seeds 모두 동일 방향) 감소한다.
- **H_A2**: 시각 nearest neighbor 의 가격 통계량 (NN_median, NN_IQR, distance-weighted avg) 이 baseline 의 cold-start 예측 RMSE 를 보완한다 (memorization 아닌 일반화).
- **H_A3**: Visual cluster 단위 가격 분산이 global 분산보다 유의하게 작다 (cluster-conditional variance).

### C-lite. GPBoost Mixed-Effects

- **H_C1**: Seen-artist (1-3, 4-10, 10+ exposure) 의 MdAPE 가 baseline 대비 감소한다 (random intercept partial pooling 효과).
- **H_C2**: Cold-start 작가 (0-shot) 의 MdAPE 가 baseline 대비 악화되지 않는다 (b_artist=0 자연 수축).
- **H_C3**: 학습 runtime 이 baseline 의 4x 이내 (운영 적용 가능).

### Full Integration

- **H_Full1**: A + C-lite 통합 모델의 overall MdAPE 가 baseline 대비 일관 개선.
- **H_Full2**: Cold-start gain 이 A 단독 gain 의 80% 이상 유지된다 (negative interaction 없음).
- **H_Full3**: Seen-artist gain 이 C-lite 단독 gain 의 80% 이상 유지된다.

## 2) Validation Setup

- **Primary split**: artist-level GroupShuffleSplit 80/20 holdout
- **Repeats**: **3 seeds**, pre-fixed:
  - `seed_1 = 42`
  - `seed_2 = 123`
  - `seed_3 = 7777`
- **Inner CV** (Optuna, fairness): 5-fold KFold on training subset only
- **Outer eval**: 80% Train fit → 20% Holdout MdAPE
- **Hyperparameter policy**:
  - Baseline: fixed (current production hyperparams)
  - A: pre-specified only (분포-의존 hyperparam 은 본 데이터 도착 후 확정)
  - C-lite: pre-specified only (GPBoost variance components fitted, no manual tuning)
  - **No additional tuning after first evaluation unless logged as deviation**
- **Comparison units**:
  - Baseline (32 features) vs A (33 features = 32 + retrieval features)
  - Baseline vs C-lite (32 features + random intercept)
  - Baseline vs A + C-lite (full)

## 3) Metrics

### Primary
- **Cold-start MdAPE** on artist-level holdout (0-shot exposure bucket)

### Secondary
- Overall MdAPE / Seen-artist MdAPE
- W30 (예측이 ±30% 이내 비율)
- W50 (예측이 ±50% 이내 비율)
- MAE
- Segment-wise MdAPE for all pre-registered segments (48 cells)

### Diagnostic-only (decision 영향 X)
- Prediction variance across seeds
- Coverage / missingness-sensitive subgroup counts

## 4) Pre-registered Segments

**4-axis grid**:
- **Exposure** (artist 학습 작품 수): `0-shot` / `1-3` / `4-10` / `10+`
- **Marketplace**: `Artsy` / `Saatchi`
- **Price**: `tercile_1` / `tercile_2` / `tercile_3` (train-only quantile 기반)
- **Career stage availability**: `available` / `missing`

**Total cells**: 4 × 2 × 3 × 2 = **48**

**Reporting rule**:
- 모든 cell 을 출력 표에 enumerate
- `n < X` cell 은 `dropped (underpowered)` 표시 + pass/fail 해석 제외
- **`X = ____`** (본 데이터 첫 run 전 확정. 권고: 30 또는 50)

**Mandatory aggregate reports**:
- By exposure bucket (4 levels)
- By marketplace (2 levels)
- By price tercile (3 levels)
- By career stage availability (2 levels)

**Forbidden**:
- Post-hoc segment 추가
- Bucket 경계 변경 (post-hoc)
- Career stage 정의 변경

## 5) Pass / Fail Gates (사전 확정 — 코덱스 7차 자문)

### A Pass
- Cold-start mean ΔMdAPE ≤ **-max(0.8pp, baseline의 3%)**
- 3/3 seeds 같은 방향 (모두 negative)
- Seed std ≤ 0.6pp
- 다른 segment 악화 ≤ +1.0pp

### C-lite Pass
- Seen-artist mean ΔMdAPE ≤ **-max(0.5pp, baseline의 2%)**
- 3/3 seeds 같은 방향
- Cold-start 악화 ≤ +0.5pp (3 seeds 평균)
- Tail (P90 APE) 악화 없음
- Runtime ≤ 4x baseline

### 통합 (A + C-lite) Pass
- Overall ΔMdAPE ≤ -max(0.8pp, baseline의 3%)
- Cold-start gain ≥ 80% of A 단독 유지
- Seen-artist gain ≥ 80% of C-lite 단독 유지
- Max segment degradation ≤ +1.0pp

## 6) Stop Conditions

- **A cut**: Day 4 진단 6단계 (LAO split / image-only / retrieval sanity / memorization audit / cluster variance / retrieval features) 중 ≥2 fail
- **A cut**: Seed instability — pre-registered consistency gate 위반
- **C-lite cut**: Seed 민감도 큼 (direction unstable across 3 seeds)
- **C-lite cut**: 추가 tuning 후만 개선 (사전등록 외 hyperparameter search)
- **Integration cut**: Component gain 이 결합 후 사라짐, 또는 segment harm 초과
- **All cycles**: 결과 관찰 후 retry/retune/re-split 은 모두 post-hoc

## 7) Analysis Plan

### Main Comparisons
- Baseline vs A
- Baseline vs C-lite
- Baseline vs A + C-lite

### Estimands
- Mean ΔMdAPE across 3 seeds
- Segment-wise ΔMdAPE
- Per-seed ΔMdAPE (paired comparison)

### Uncertainty Reporting
- 95% bootstrap CI on primary metric Δ
- Paired seed-wise comparison (descriptive)

### Statistical Decision Rule
- **Pass/fail 은 사전등록 gate 우선** (p-value 보다 우선)
- Inferential statistics 는 supportive (gate 충족 후 보고)

### Mandatory Reporting
- Primary metric (cold-start MdAPE)
- All secondary metrics
- All mandatory aggregates (4 levels × 4 axes)
- All 48 segment cells (dropped 포함, 이유 명시)

### Forbidden Post-hoc Practices
- Best seed cherry-pick
- Replacing baseline after seeing results
- Narrowing report to favorable segments
- Changing bucket boundaries after result inspection

## 8) Deviation Log

| Date | Item changed | Why | Pre-registered/Post-hoc | Expected impact | Approved by |
|---|---|---|---|---|---|
| 2026-05-04 | 본 사전등록 초안 작성 | Cycle 시작 전 분포-비의존 항목 고정 | Pre-registered | n/a | Bo |
| YYYY-MM-DD | | | | | |

## 9) Governance / Review Linkage

- 본 사전등록 파일은 `PR-eval-framework` 와 **함께 merge**
- merge 후 변경 시:
  - PR diff (markdown)
  - Linked commit
  - Short ADR / decision note
- Result write-up 분리 의무:
  - **Pre-registered findings**
  - **Post-hoc exploration**

## 10) Deviation Risk Controls

- A 가 unexpectedly 큰 gain → 추가 ablation 은 **post-hoc only** (pass/fail 변경 X)
- C-lite fail → 추가 hyperparameter search 는 **사전등록 결과로 X** (새 cycle 시 가능)
- Segment 정의 missingness → **원 정의 보고 유지**, fallback aggregation 은 additive 로만

## 11) Pre-migration Pilot Notes (V4 cycle data 기반)

본 사전등록 초안은 V4 cycle (Artsy 7,289 + Saatchi 21,087) 데이터로 진행한 **exploratory pilot diagnostics** 결과를 바탕으로 작성됨:

- Pilot 결과 V5 plan 의 A (image retrieval prior) 와 C-lite (GPBoost) 가 가장 viable 한 방향으로 판단 (코덱스 6차/7차 자문)
- **Pilot 은 scope selection 용도** (include/exclude decision)
- **Pilot metric 은 main study confirmatory 결과로 사용 X**
- Confirmatory threshold 와 evaluation protocol 은 본 데이터 기준으로 다시 고정

## 12) 미확정 항목 (본 데이터 후 확정 예정)

다음 항목들은 본 데이터 분포 의존이라 본 마이그레이션 도착 후 확정:

- **X cell drop threshold** (segment 최소 n) — 권고: 30 또는 50
- **Segment 최소 n 기준 per axis**
- **Train/holdout 분포 차이 acceptable threshold**
- **Career stage availability 의 정확한 정의** (현재 기준: 비공란 + non-"unknown")
- **Bootstrap CI iteration 수** (권고: 1000 또는 2000)

이 항목들이 확정되면 본 문서 §0 Metadata 의 `Date (finalized)` 기록 + Deviation Log 에 추가.
