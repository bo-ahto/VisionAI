# 트랙 1 vs 트랙 2 직접 비교 실험 — Pre-Registered (Descriptive / Supportive Only)

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: Cycle 1 (cold validation) 의 supportive analysis — 트랙 1 (gradient boosting family) 과 트랙 2 (hedonic regression family) 의 같은 dataset / 같은 split 의 비교
> **Decision binding**: ❌ **X** — descriptive only / supportive analysis / 운영 채택 결정 근거 X
> **사전 자문**: 코덱스 (Lane 1 vs Lane 2 / schema audit FAIL → Lane 2 권고)

> ⚠️ **Caveat (코덱스 필수 명시)**: 본 비교 = "Track 1 surrogate (stage4_full.parquet 의 13-15 features 로 재학습된 GBM) vs 트랙 2 (F4 + spline + Huber)". **운영 Track 1 직접 평가 X / decision-binding 비교 X**. 본 결과는 "GBM family vs hedonic regression family" 의 모델-패밀리 비교 supportive 자료.

## 1. 비교 실험 의 본질

### 1.1 Lane 분류 (코덱스)

- **Lane 1 (decision-grade)**: 운영 트랙 1 artifact (`integrated_v3_filtered_tuned_*.cbm/.json`) 직접 적용 → **schema audit FAIL** (트랙 1 32 features 중 6개만 stage4_full.parquet 에 직접 존재 / 26개 missing)
- **Lane 2 (descriptive / 본 cycle)**: 공통 + derivable feature subset 으로 두 모델-패밀리 재학습 비교

### 1.2 본 cycle 의 scope

- ✅ 같은 dataset (stage4_full.parquet)
- ✅ 같은 split (Random LAO 80/20 + Time-split 2024+)
- ✅ 같은 cold 정의 (train_count < 10)
- ✅ 같은 평가 metric (MdAPE + cluster bootstrap CI)
- ❌ **운영 트랙 1 직접 평가 X** (32 features 중 26개 missing → derivable subset 만 사용)
- ❌ **운영 학습 학습 데이터 (28K) 사용 X** (Stage 4 v3 모집단 8,495 만)

## 2. 모델 spec freeze

### 2.1 트랙 1 surrogate (GBM family)

| 항목 | 값 |
|---|---|
| Model | CatBoost (트랙 1 운영 의 main model 과 동일 family) |
| Loss | RMSE (log target) |
| Features | stage4_full.parquet 의 derivable 14 features |
| Target | `log(price_krw)` |
| Hyperparameters | iterations=1000 / learning_rate=0.05 / depth=6 / random_seed=42 |
| Note | 운영 트랙 1 의 Optuna tuned best_params 미적용 (stage4_full 의 schema 다름 — 운영 artifact 직접 사용 X) |

#### Surrogate features (14 / derivable from stage4_full.parquet)

1. `ln_area` (log of area_cm2)
2. `aspect_ratio` (width_cm / height_cm)
3. `is_small` (area_cm2 < 1000)
4. `has_depth` (depth_cm > 0)
5. `artist_birth_year`
6. `has_birth_year` (artist_birth_year notna)
7. `ln_followers` (log1p of artist_followers)
8. `for_sale_ratio` (artist_for_sale / artist_total_works, capped 0-1)
9. `has_seoul` (Seoul in gallery_cities)
10. `has_international` (len of gallery_cities > 1 or non-Korean cities)
11. `gallery_city_count` (count of gallery_cities)
12. `is_krw` (price_currency == 'KRW')
13. `gallery_type` (categorical)
14. `attribution_class` (categorical)

> **Surrogate caveat**: 본 14 features 는 운영 트랙 1 의 32 features 의 부분집합 + 일부 derived. `gallery_tier` / `career_stage` / `profile_completeness` / `support_factor` / `medium_category` 등 18개 features 는 **stage4_full.parquet 미포함** — 운영 트랙 1 의 정확한 reproduction X.

### 2.2 트랙 2 (Cycle 1 spec 그대로)

| 항목 | 값 |
|---|---|
| Model | sklearn HuberRegressor (Stage 3 운영 채택 spec) |
| Features | F4 (log_area / birth_year_centered / log_artist_total_works) + log_area 3-knot spline |
| Loss | Huber (`epsilon=1.35`, `alpha=0.0001`) |
| Target | `log(price_krw)` |

본 cycle 1 의 학습 spec 그대로 사용.

## 3. 평가 protocol

### 3.1 Split spec (cycle 1 동일)

- **Random LAO 80/20** (artist-level GroupShuffleSplit, random_state=42, test_size=0.20)
- **Out-of-time split** (train: `year_made` ≤ 2023 / test: ≥ 2024)

### 3.2 Cold/Warm 정의 (cycle 1 동일)

- **Cold**: 학습 데이터 작가 이력 < 10건
- **Warm**: ≥ 10건

### 3.3 Bootstrap hygiene (cycle 1 동일)

- artist-cluster bootstrap (with replacement on artists)
- n_boot = 2,000
- Internal seed = `range(2000)`
- Percentile CI (2.5% / 97.5%)

## 4. 비교 metric

| Metric | 영역 | 계산 |
|---|---|---|
| Cold MdAPE (point) | Random LAO test fold | `median(|exp(pred) - exp(actual)| / exp(actual))` |
| Cold MdAPE 95% CI (point) | Random LAO | artist-cluster bootstrap |
| Cold MdAPE | Time-split test (cold subset) | 동일 |
| Cold MdAPE 95% CI (Time-split) | Time-split test | 동일 |
| Time-split degradation | Test cold − Train cold | 동일 |

비교 형식:

| 영역 | 트랙 1 surrogate | 트랙 2 (Cycle 1) | Δ (T2 - T1) |
|---|---|---|---|
| Random LAO cold | (계산) | 36.18% | (계산) |
| Time-split cold | (계산) | 43.15% | (계산) |
| Time-split degradation | (계산) | +4.08%p | (계산) |

## 5. Decision binding

❌ **본 cycle = decision-binding X**:
- 트랙 1 surrogate ≠ 운영 트랙 1 (32 features 중 14 만 / 운영 학습 데이터 X / Optuna best_params X)
- 결과 의 모든 직접 비교 = "GBM family vs hedonic family" 의 모델-패밀리 비교 만
- "트랙 1 < 트랙 2" 또는 반대 결론 = 운영 의사결정 근거 X
- 운영 채택 결정 = 별도 prereg cycle (Lane 1 schema audit + Saatchi 통합 등) 의무

## 6. 운영 reported metric 와 의 관계

| 트랙 1 reported | 값 | 본 cycle 비교 가능성 |
|---|---|---|
| 운영 calibrated cold (CatBoost) | 38.3% | **직접 비교 X** (운영 학습 28K + calibration / 본 cycle 8,495 surrogate) |
| 운영 offline ensemble cold | 38.7% | **직접 비교 X** (동일 사유) |
| 운영 warm slice (XGBoost KFold) | 10.30% | **직접 비교 X** (운영 학습 spec) |

본 cycle 의 surrogate metric 은 위 reported metric 을 직접 reproduce X — 단순 "surrogate spec 의 cold MdAPE" 만.

## 7. 본 cycle 의 가치

✅ 사용자 의문 ("트랙 1 vs 트랙 2 어느 게 cold 영역 우위?") 의 **descriptive 답변** — 같은 dataset / 같은 split 의 fair 비교 (모델-패밀리 한정)

❌ 운영 의사결정 근거 X — Lane 1 (운영 artifact 직접 평가) 은 schema gap 보강 후만 가능

## 8. 진행 protocol

1. ✅ 본 prereg 작성 + 코덱스 검수
2. ⏳ 비교 실험 코드 작성 (`experiments/structural_v1/track1_vs_track2_comparison.py`)
3. ⏳ 실험 실행
4. ⏳ 결과 보고서 작성 (caveat 의무 — decision-binding X / surrogate caveat / spec mismatch)
5. ⏳ Cycle 1 결과 보고서 §3.3 reconcile 영역 보강

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 트랙 1 비교 실험 사전 자문 (2026-05-08) | Lane 1 (artifact direct) vs Lane 2 (surrogate) / schema audit FAIL → Lane 2 권고 / 3 caveat (모집단 / split / metric 문맥) |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
