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

## 3. Method (Phase 0–8)

> **Fix-1 (코덱스 1차)**: phase 별 primary metric 분리 + global cycle metric 의 영역 별도 정의.
>
> | Phase | Local primary metric | Local secondary | 비고 |
> |---|---|---|---|
> | DROP-A / B / C | Δ Cold MdAPE | Δ Warm MdAPE / Guard 4 | 악화 영역 = 채택 거부 |
> | ADD-A (interaction) | Δ Cold MdAPE OR Δ Warm MdAPE (dual-primary / exploratory) | 다른 영역 / Guard 4 | 1 영역 의 개선 + 다른 영역 비악화 → 채택 |
> | ADD-B (as-of / warm) | Δ Warm MdAPE | Cold = 영향 X 의무 / Guard 4 | warm-only primary |
> | ADD-C (engineered) | Δ Cold MdAPE | Δ Warm MdAPE / Guard 4 | source-conditional 영역 |
>
> **Cycle global primary** = Δ Cold MdAPE (cycle 의 종합 영역 의 영향 의 record).
> 이 분리 의무 = §5 의 phase PASS 의 영역 의 영향 의 정합 보장.

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

#### B-1. Multi-method consensus rule (Fix-5 / 코덱스 1차)

본 cycle 의 후보 선정 영역 의 정합 의무. 단순 산출 의무 외 의 selection rule 의 정의:

**DROP candidate consensus**:
- 2/4 method 이상 영역 에서 영향도 하위 5% (또는 ≤ 0.5%) → DROP-A/B/C 의 후보 의 자격
- placeholder 영역 (4/4 모두 = 0%) = DROP-A 의 즉시 후보

**ADD candidate consensus** (코덱스 round 2 P2 보강):
- SHAP 의 영역 의 mean(\|SHAP value\|) 영역 의 의무 ≥ 0.5% (전체 SHAP 합 영역 대비) OR Permutation Importance 영역 의 의무 ≥ 0.3% (MdAPE delta 영역) 의 1 method 이상 → ADD-A/C 의 후보 의 자격
- ADD-B 의 영역 = warm 의 SHAP 의 individual prediction 의 변동 영역 의 의무 정합 (mean(\|SHAP\|) ≥ 0.5%)
- 유의 signal 의 정량 기준 = locked (prereg)

**Tie-break rule**:
- 4 method 의 영역 의 rank 가 충돌 시 → SHAP 의 영역 (개별 prediction 영역) 의 우선 (트리 모델 의 정합 가장 높음)
- Permutation 의 영역 = robust check 의 영역 (model-agnostic)

**Iteration log 의 의무 영역**: 매 iteration 의 4 method rank 모두 dump (post-hoc 검증 의무).

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
| **⚠️ 의무** | **§3.10 의 As-of Feature Contract 의 의무 준수** (leakage 방지) |
| **Local primary** | Δ Warm MdAPE (큰 boost ≤ −0.5%p) |
| **PASS criterion** | Warm 영역 의 ≤ −0.5%p AND Cold 영역 의 비악화 (≤ +0.1%p) AND Guard 4 PASS |
| **검증** | leakage detection (test fold 의 통계 영역 의 의무 검증 / §3.10 protocol) |
| **N 변화** | 24-28 → 25-31 (warm 영역) |

### 3.7 Phase 6 (ADD-C: Engineered / 3-5 일)

| 영역 | 영역 |
|---|---|
| **목표** | domain knowledge engineered features 추가 |
| **후보** | `source_conditional_ho_power` (β=0.84 USD vs β=0.74 KRW / as-of X / 즉시 산출) / `gallery_avg_price` (**as-of / §3.10 contract 의무**) / `medium_avg_price` (**as-of / §3.10 contract 의무**) |
| **Local primary** | Δ Cold MdAPE |
| **PASS criterion** | Δ Cold MdAPE ≤ −0.1%p (개선) AND Guard 4 PASS |
| **⚠️ 의무 (Fix-3)** | **as-of feature 의 영역 (`gallery_avg_price` / `medium_avg_price`) = §3.10 As-of Feature Contract 의 의무 준수**. 비-as-of feature (`source_conditional_ho_power`) = contract 의 영역 의무 X. |
| **N 변화** | 25-31 → 26-33 |

### 3.10 As-of Feature Contract (Fix-3 + Fix-4 / 코덱스 1차)

**적용 영역**: ADD-B (Phase 5) AND ADD-C (Phase 6) 의 영역 의 as-of 통계 feature 모두.

#### A. Time anchor 정의

| 영역 | timestamp anchor | 비고 |
|---|---|---|
| **Cold 영역** | `transaction_date` (거래일) | source_calibration 영역 의 의무 정합 |
| **Warm 영역** | `transaction_date` (거래일) | 동일 |
| **동일 일자 다건 처리** | strict less-than (`<`) | 같은 날 의 영역 = 미래 의 영역 의 의무 (자기 자신 + 같은 날 의 다른 건 = 제외) |
| **fold 내 정렬** | `transaction_date` 의 ASC | 누적 통계 의 영역 의 의무 |

#### B. Fold-internal computation 의무

**핵심 의무 (코덱스 round 2 P1 fix)**: train-row 의 영역 의 as-of feature 생성 시 self / 같은 날 다른 row / 미래 train row 의 영역 = **모두 배제 의무**. test-row 의 영역 의 lookup 의 영역 = train-fold 의 영역 의 < transaction_date 만 의 영역 의 의무.

**train-row + test-row 공통 strict 의무**:
1. **strict less-than (`<`)**: 자기 자신 의 transaction_date 영역 의 의무 미만 만 의무 사용 (≤ X / strict <)
2. **self-exclusion**: 자기 자신 의 row 영역 의 의무 통계 산출 영역 의 의무 X
3. **same-day tie 처리**: 같은 날 의 영역 의 모든 row (자기 + 다른 row) 의 영역 의 의무 X
4. **시간순 순차 누적**: train fold 내부 의 영역 의 영역 의 의무 ASC 정렬 의 의무 누적 통계 (각 row 의 의무 시점 의 의무 의무 < 의무 정합)
5. **fold-cross leakage 의무 X**: 다른 fold 의 영역 의 의무 영역 의 의무 lookup table 의 영역 의 의무 X

```python
# Fix-3 + 코덱스 round 2 P1 fix: as-of feature 의 영역 의 의무 protocol
def compute_asof_for_row(target_row, source_data, group_col, time_col, stat):
    """target_row 의 의무 strict < 의무 same-group 영역 의 영역 의 통계.

    ⚠️ self-exclusion 의무: target_row.transaction_date 의 영역 의 의무 strict <
    영역 의 영역 의 의무 row 만 의 의무. 같은 날 의 영역 의 영역 (self + others) X.
    """
    same_group = source_data[source_data[group_col] == target_row[group_col]]
    past_only = same_group[same_group[time_col] < target_row[time_col]]  # strict <
    if len(past_only) < 3:
        return None  # low-count → fillna(0) + has_asof=0
    return past_only["price"].agg(stat)


for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y, groups)):
    train_data = df.iloc[train_idx].sort_values("transaction_date")  # ASC 의무
    test_data = df.iloc[test_idx]

    # ⚠️ train-row as-of: self/future train-row 모두 배제 의무
    train_asof = []
    for _, row in train_data.iterrows():
        # train_data 만 source / strict < / self-exclusion 의무
        val = compute_asof_for_row(row, train_data, "artist_slug", "transaction_date", "median")
        train_asof.append(val)

    # ⚠️ test-row as-of: train_data 의 영역 의 의무 strict < transaction_date 만
    test_asof = []
    for _, row in test_data.iterrows():
        val = compute_asof_for_row(row, train_data, "artist_slug", "transaction_date", "median")
        test_asof.append(val)

    # ⚠️ 다른 fold 의 영역 의 의무 lookup X / test 정보 의무 fit 영역 X
```

#### B-1. Train-row leakage 방지 의무 (코덱스 round 2 P1)

| Leakage type | 차단 의무 |
|---|---|
| **self leakage** (자기 row 의 자기 통계 영역) | `strict <` + self-exclusion |
| **same-day leakage** (같은 날 의 다른 row 영역) | `strict <` (≤ X / 같은 날 모두 X) |
| **future train-row leakage** (미래 train row 영역) | `strict <` (자기 transaction_date 미만 만) |
| **fold-cross leakage** (다른 fold 의 영역 영역) | fold 내 source 만 의무 / cross-fold lookup X |

**leakage detection smoke test** 의 의무:
1. 매 train row 의 영역 의 의무 lookup row 의 영역 의 의무 transaction_date < target.transaction_date 의 의무 정합 검증
2. self row 의 영역 의 의무 lookup 의 의무 X 검증
3. 같은 날 의 영역 의 row 영역 의 의무 lookup 의 의무 X 검증

#### C. Calibration 의 영역 의 영향

- **Cold 영역**: source_calibration 의 적용 = as-of feature 의 산출 **이전**. 즉 raw price 의 영역 의 통계 의 영역 의 의무 (calibration 의 영역 의 leakage 방지).
- **Warm 영역**: warm 의 영역 = source_calibration 의 영역 X (운영 정합).

#### D. 결측 처리

- as-of lookup 의 영역 의 결측 (train-fold 에 해당 group 영역 X / count < min_count) → fillna(0) + has_asof flag = 0
- has_asof flag = 0 의 영역 = model 영역 의 의무 (정보 영역 의 의무 분리)

#### E. Low-count shrinkage (코덱스 round 2 P2 보강 / 통계별 분리)

| stat | shrinkage 영역 의 의무 |
|---|---|
| **median (median price)** | `count < 3` → fillna(0) + has_asof=0 (median 의 영역 의 영역 = shrinkage 영역 의 의무 robust X / NaN flag 의무) |
| **mean (mean price)** | `count < 3` → Bayesian shrinkage: `(count × group_mean + 5 × global_mean) / (count + 5)` |
| **std (price std)** | `count < 5` → fillna(0) + has_asof=0 (std 의 영역 = small sample 영역 의 의무 unreliable) |
| **count (transaction count)** | shrinkage X / raw count 영역 의 의무 사용 (의미 영역 = 데이터 영역 의 의무 정합) |

#### F. Leakage detection 의 의무

매 iteration 의 영역 의 의무 영역 (Phase 5 + Phase 6):

1. **smoke test**: test row 의 영역 의 transaction_date 의 영역 의 의무 의 train-fold 의 의무 정렬 의 의무 검증 (모든 row 영역)
2. **future-leakage test**: test row 의 영역 의 의무 lookup value 의 영역 의 의무 의 train-fold 의 영역 의 의무 < transaction_date 의 의무 정합
3. **fold-cross leakage**: 다른 fold 의 영역 의 의무 lookup table 영역 X (의무 검증)
4. **iteration log dump**: leakage check 결과 의 의무 record (PASS / FAIL).

### 3.8 Phase 7 (수렴 검사 / 1 일)

- **수렴 criterion (locked / 코덱스 round 2 P1 fix)**:
  - 최근 3 iter 의 \|Δ Cold MdAPE\| **< 0.1%p** (locked / 참고: cold fold std × 0.25)
  - AND 최근 3 iter 의 \|Δ Warm MdAPE\| **< 0.05%p** (locked / 참고: warm fold std × 0.25)
  - 본 cycle 동안 의 의무 변경 X (§4.2 B 의 의무 정합)
- **YES**: 수렴 / Phase 8 진입
- **NO**: 다른 strategy 의 의무 / Phase 1-6 의 추가 iteration

#### Iteration cap (Fix-7 / 코덱스 1차)

타이트 일정 의 의무 보호 의 의무:
- 매 phase 의 영역 의 의무 max iter cap = 5 (DROP-A) / 8 (DROP-B) / 5 (DROP-C) / 6 (ADD-A) / 6 (ADD-B) / 6 (ADD-C)
- cap 영역 의 의무 도달 의 영역 의 영역 의 의무 = phase 종료 (수렴 의 의무 X 영역 의 의무 다음 phase 영역)
- 전체 cap = 36 iter (17-28 일 의 영역 의 영역 정합)

### 3.9 Phase 8 (최종 보고 / 1-2 일)

- 최종 N* features 의 정량 record
- Iteration log 의 dump (JSON + CSV)
- 결과 보고서 + 코덱스 검수
- PR 작성

## 4. CV protocol (모든 phase 영역 의 동일)

| Evaluation | 영역 | 모집단 |
|---|---|---|
| **Cold MdAPE** | GroupKFold-5 (artist_slug) + Source-cell calibration | 28,376 rows / 1,551 artists |
| **Warm MdAPE (main)** | KFold-5 (random_state=42) | 27,062 rows (warm slice / 작품수 ≥ 5) |
| **Warm MdAPE (guard)** | GroupKFold-5 (artist_slug) | 위 동일 |
| **Overall ensemble** | 0.5 × cold + 0.5 × warm (운영 영역 정합) | full |
| **Source segment** | 위 영역 의 Artsy / Saatchi 분리 record | 7,289 / 21,087 |

> **모든 CV** = `random_seed=42` 의 fixed (reproducibility 의무).

### 4.1 Warm CV 의 영역 정의 (Fix-2 / 코덱스 1차)

**Warm 영역 의 정의**: 작품수 ≥ 5 의 seen artist 의 영역 의 영역 의 영역 (학습 시 영역 의 영역 의 영역). 운영 의 영역 정합.

**Warm KFold-5 의 영역 (main)**:
- 운영 정합 (작가 단위 의 영역 X / row 단위 영역 의 영역). Production deployment 의 영역 = 작가 의 영역 의 의무 작품 의 영역 의 영역 의 영역 의 영역 (이미 학습 영역 의 작가 의 의무 새 작품 영역).
- 즉 KFold = "seen artist 의 영역 의 새 작품 영역" 의 영역 의 영역 정합.

**Warm GroupKFold-5 의 영역 (guard)**:
- 동일 artist 의 의무 train/test 의 의무 영역 X (artist-level signal leakage 방지).
- 의무: 매 iteration 의 영역 의 영역 의 의무 record (낙관편향 의 의무 정량화).

**의무 영역** (코덱스 round 2 P2 보강 / escalation rule):
- ADD-B 의 영역 (artist 통계 추가) 의 영역 의 KFold ↔ GroupKFold 의 의무 gap 의 의무 정합 검증.
- **escalation rule (locked)**:
  - gap ≤ +0.5%p → 정상 (낙관편향 의 영역 의 영역 작음)
  - +0.5%p < gap ≤ +1.0%p → 경고 / iteration log 의 영역 의 의무 record + 코덱스 의 영역 의 의무 영역
  - gap > +1.0%p → **phase 의 의무 ADD-B 채택 거부** (낙관편향 의 영역 의 영역 큼 / leakage 의 의무 의심) + 코덱스 검수 의 의무 영역

### 4.2 Baseline 변동성 (Fix-4 / 코덱스 1차 + round 2 P1)

Guard / convergence threshold 의 영역 의 의무 근거 의 의무 baseline run 의 영역 의 fold-level 변동성 의 의무.

#### A. baseline 의 의무 fold-level metric dump

Phase 0 의 영역 의 의무:
- **Cold MdAPE fold std**: GroupKFold-5 의 5 fold 의 영역 의 의무 std (예상: 0.3-0.7%p / B-2 reproduction PASS 의무 정합)
- **Warm MdAPE fold std (KFold)**: 5 fold 의 영역 의 의무 std (예상: 0.1-0.3%p)
- **Warm MdAPE fold std (GroupKFold guard)**: 동일

#### B. Threshold prereg locking (코덱스 round 2 P1 fix)

본 prereg 의 의무 = **고정 threshold 영역 (primary)** + **fold std 의 영역 의 의무 참고치 영역 (reference only)**. 사후 조정 재량 의무 = X.

| Threshold | **prereg 고정값 (primary)** | fold std × 계수 (reference / 사후 조정 X) |
|---|---|---|
| **Guard G1** | **+0.5%p (Warm KFold MdAPE 악화)** | warm fold std × 1.75 (참고 / 의무 X) |
| **Guard G2** | **+0.8%p (Overall ensemble 악화)** | overall fold std × 1.75 (참고 / 의무 X) |
| **Guard G3** | **+1.0%p (Artsy segment cold 악화)** | Artsy fold std × 1.75 (참고 / 의무 X) |
| **Guard G4** | **+1.0%p (Saatchi segment cold 악화)** | Saatchi fold std × 1.75 (참고 / 의무 X) |
| **Convergence cold** | **\|Δ Cold\| < 0.1%p (3 iter)** | cold fold std × 0.25 (참고 / 의무 X) |
| **Convergence warm** | **\|Δ Warm\| < 0.05%p (3 iter)** | warm fold std × 0.25 (참고 / 의무 X) |

**의무 영역**:
- prereg 고정값 = **불변 (locked)**. 본 cycle 동안 의 변경 의무 X.
- fold std × 계수 = **참고 metric only**. 산출 의무 (record) / threshold 의 영역 의 변경 의무 X.
- 만약 fold std 영역 의 의무 매우 큰 영역 (예: cold > 0.8%p / 고정 threshold + std × 1.75 의 영역 의 의무 정합 X) = **본 cycle 종료 후 의 별도 prereg 영역 의 의무 영역** (본 cycle 의 의무 변경 X).

#### C. fold-level std 의 영역 의 의무 record only

Phase 0 의 영역 의 의무 영역 의 의무 fold-level std 산출 → iteration log 의 영역 의 의무 record. **threshold 영역 의 변경 의무 X**. 사후 분석 / 후속 cycle 의 의무 입력 영역 만.

## 5. Guard metric (every phase / 4 영역)

**프리레그 고정 (locked / 코덱스 round 2 P1 fix)**: 본 cycle 동안 의 의무 변경 X.

| # | Guard | **임계 (locked)** | 참고 (reference / 의무 X) |
|---|---|---|---|
| **G1** | Warm KFold MdAPE 악화 | **≤ +0.5%p** | warm fold std × 1.75 |
| **G2** | Overall ensemble 악화 | **≤ +0.8%p** | overall fold std × 1.75 |
| **G3** | Artsy segment cold 악화 | **≤ +1.0%p** | Artsy fold std × 1.75 |
| **G4** | Saatchi segment cold 악화 | **≤ +1.0%p** | Saatchi fold std × 1.75 |

> 1 phase 의 채택 = **Local primary metric (§3 의 Fix-1)** PASS AND Guard 4 영역 모두 PASS.
> Local primary 는 phase 별 영역 (§3 상단 의 영역 정합).
>
> **임계 의무**: 위 4 영역 의 임계 영역 = **prereg 고정 (locked)**. 사후 조정 재량 의무 X (§4.2 B 의 의무 정합).

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
| 1차 사전 자문 (commit ec93513 직후) | NEEDS FIX / 5 영역 (§3 phase primary / §4 Warm CV / §3.10 As-of Contract / §4.2 baseline 변동성 / §3.1 multi-method consensus) |
| 1차 fix patch (commit 687bbe7) | §3 Fix-1 (phase primary 분리) / §3.1 B-1 Fix-5 (consensus rule) / §3.10 Fix-3 (As-of Contract) / §4.1 Fix-2 (Warm CV 정의 + GroupKFold guard) / §4.2 Fix-4 (baseline 변동성) / §3.8 Fix-7 (iteration cap) |
| 2차 사후 검수 (round 2) | NEEDS FIX (P1 2 영역) / §3.10 train-row leakage 차단 명시 / §4.2 + §5 threshold prereg locking + P2 3 영역 |
| 2차 fix patch (본 commit) | §3.10 B/B-1 (train-row self/future/same-day leakage 차단 + smoke test) / §4.2 B + §5 (threshold locking / prereg 고정) / §3.1 B-1 (ADD signal 정량 ≥ 0.5%) / §4.1 escalation rule / §3.10 E shrinkage 통계별 분리 |
| 3차 사후 검수 (예정) | 본 fix commit 직후 / GO 의무 |
