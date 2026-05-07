# Feature Track Axis A.1 — Cheap Categorical Pre-registration

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' (Stage 6 architecture cycle 종료 후 feature/information cycle), Axis A 의 **A.1 cheap falsification step**
> **연계**: `docs/feature_track_design_20260507.md` (axis 설계 / 의사결정 8건 추천대로 승인) / `docs/stage6b_results_20260507.md` (architecture-only close) / `docs/stage4_short_term_track_results_20260507.md` (저가 feature 부족 시그니처)

> ⚠️ **연구 목적**: **Cheap falsification step** — 운영 모델 (F4 + spline + Huber) 에 cheap categorical features 4종 추가 시 저가 segment 식별력 보강 가능 여부 평가. **"Quick-win 기대" 가 아닌 "저비용 가설 반증" framing** (코덱스 P1 — Stage 4 evidence 상 정직).

> **본 prereg freeze**: 가설 / metric / family / PASS 기준 / per-step freeze 6항목 / step gate = **2026-05-07 freeze**. 결과 본 후 변경 X (HARK 회피).

## 1. Input / Hypothesis

### 1.1 의사결정 input (2026-05-07 의사결정자 승인)
- Stage 6B FAIL → architecture-only remedies under fixed-feature cold-start LAO scope 종료
- Feature track 시작 (design draft 의사결정 8건 추천대로 승인):
  1. Axis A 우선 / B 조건부
  2. Cheap falsification ladder framing
  3. Step gate B안 (escalation 허용)
  4. LAO primary family vs warm/time-split supportive family 분리
  5. Phase A 7항목 확장 (labelability / joinability / as-of-time)
  6. A.2 시점 정합성 검증 원칙
  7. A.4 / A.5 escalation 진입 (B안)
  8. Cold Phase A shadow 정의 (data availability 검증 shadow)

### 1.2 A.1 Hypothesis
> **운영 모델 F4 (`log_area + birth_year_centered + log_artist_total_works + spline`) 에 cheap categorical features 4종 추가 시 cold-start LAO MdAPE 개선 + 저가 segment harm 0?**

> **사전 evidence 상 기대 (정직 보고)**: Stage 4 단기 트랙 작업 3 = "현재 inputs 로는 feature space 분리력 부족" + 6A/6B 저가 systematic harm → A.1 PASS 가능성 **낮음** (코덱스 P1). FAIL/BORDERLINE 시 A.2 (artist popularity, 시점 정합성 검증 후) 로 escalation.

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Per-step freeze 6항목 (코덱스 P1 — HARK 회피 강화)

#### (a) Feature set — 4종 final

| Feature | Type | 비고 |
|---|---|---|
| `category` | categorical (14 unique) | one-hot encoding (drop_first) |
| `attribution_class` | categorical (4 unique) | one-hot encoding (drop_first) |
| `gallery_name` | categorical (76 unique) | **leakage-safe target encoding** (§(b) 참조) |
| `gallery_cities` | multi-categorical (30 unique, comma-separated) | top-5 city multi-hot dummy (§(b) 참조) |

> **medium_type 제거 사유 (minor deviation, 사전 freeze)**: design draft §3.1 의 5종 중 `medium_type` 은 `category` 와 분류 체계 거의 동일 (top 6 = Painting / Sculpture / Photography 등 동일) → redundancy. **`category` 만 채택** (0% missing, parsimonious spec). Deviation log entry 의무.

#### (b) Encoding — leakage-safe specification (코덱스 P0 — 모든 spec 한 줄씩 freeze)

- **One-hot (drop_first)**:
  - `category` (14 → 13 columns) — drop `Painting` (가장 빈도 높음, 5,900 rows)
  - `attribution_class` (4 → 3 columns) — drop `Unique` (가장 빈도 높음, 7,659 rows)
- **`gallery_name` target encoding (코덱스 P0 — spec freeze)**:
  - **Target**: `log_price` (raw, residual 아님 — Stage 3/6B 의 baseline 과 동일 target space)
  - **Smoothing formula**: `enc[g] = (n_g · mean_g + α · global_mean) / (n_g + α)` where **α = 10**, `global_mean = mean(log_price)` over train fold
  - **Fold assignment unit**: **row-level** (artist-cluster X — gallery 가 artist 와 부분 correlated 하나 row OOF 가 standard sklearn `KFold` spec)
  - **Fold seed**: `random_state=42` (`KFold(n_splits=5, shuffle=True, random_state=42)`)
  - **OOF spec**: 각 row 의 encoding = 본 row 가 속하지 않은 4-fold 의 smoothing-adjusted gallery mean
  - **Test (LAO held-out artists)**: full train 5-fold OOF 학습 후 → 전체 train 의 smoothing-adjusted gallery encoding 적용 / unseen gallery → `global_mean` 사용 (train overall mean)
  - **구현**: `category_encoders.TargetEncoder(smoothing=10, cv=5, handle_unknown='value')` 또는 custom OOF (canonical = category_encoders, version pin 의무)

- **`gallery_cities` multi-hot dummy (코덱스 P1 — parsing detail freeze)**:
  - **Parse**:
    1. split on `,` → list of strings
    2. `.strip()` (whitespace 제거)
    3. `.casefold()` (case normalize, 예: `SEOUL` → `seoul`)
    4. `set()` (중복 제거 — `"Seoul, Seoul"` 같은 케이스 dedup)
  - **Top-5 cities (freeze)**: Seoul / Busan / Pohang / Daegu / Incheon — **train data 전체 (`stage4_full.parquet`) 의 multi-city set frequency 기준 top-5** (train 시점 결정, LAO seed-별 재산정 X — freeze)
  - **Encoding**: 5 boolean columns (`in_seoul` / `in_busan` / `in_pohang` / `in_daegu` / `in_incheon`) — multi-hot (한 row 가 여러 city 에 속할 수 있음, 예: `"Seoul, Busan"` → `in_seoul=1, in_busan=1`)
  - **Missing + "other" 의도적 collapse**: `gallery_cities` missing (1.8%) 또는 top-5 외 city 만 보유 시 → **모든 5 boolean column = 0** (지원 sparse). Missing 자체 indicator X (의도적 — sparsity 활용 / collapse 자체가 design choice)

#### (c) Preprocessing
- Missing imputation:
  - `gallery_cities` 1.8% missing → 모든 city dummy = 0 ("unknown" indicator X — sparsity 활용)
  - 다른 features 0% missing
- Outlier handling: Huber regression 자체로 처리 (운영 모델과 동일)
- Standardization: 운영 모델과 동일 (numeric only — log_area, birth_year_centered, log_artist_total_works)

#### (d) Interaction 허용 범위 — **NONE** (additive only)
- ❌ `is_low` × feature interaction (target leakage 회피)
- ❌ feature × feature interaction (e.g., `category` × `gallery_name`)
- ❌ Polynomial / spline of new features
- ❌ Per-segment encoding

#### (e) Stop/go rule (LAO primary family — §3 적용)
- **PASS**: Δ ≤ -1.0%p AND Cluster bootstrap CI 상한 ≤ 0 AND Hard gate Δ_low ≤ 0%p → 운영 채택 후보 (이후 A.2 진입 불필요)
- **BORDERLINE**: -1.0 < Δ ≤ -0.3%p AND Hard gate ✓ → A.2 escalation
- **FAIL**: Δ > -0.3%p OR Hard gate 위반 → A.2 escalation (B안)

#### (f) 다음 step (alternative hypothesis sequence, 코덱스 P0 — multiple comparisons 정합성)
- A.1 FAIL/BORDERLINE 시 → **A.2 (artist popularity 4종, 시점 정합성 검증 후) 로 escalation**
- **A.2 prereg 에서 A.1 features 전부 drop** (model spec = **비누적 feature set** / 각 step 은 독립 model 비교)
- A.2 의 baseline = 운영 모델 F4 (A.1 features 미사용)
- **Inferential family = program-level cumulative (코덱스 P0)**: model spec 은 비누적이지만 "Axis A 5 step 중 어느 한 step PASS 시 채택 후보" 라는 program-level 주장이 누적 → multiple comparisons family 도 누적 → step α=0.01 (Bonferroni 5 step, FWER ≤ 0.05) 으로 통제 (§2.10 동일).
- 즉 **feature set 비누적 / inferential family program-level cumulative** 이 본 cycle 의 정합 문구.

### 2.2 Primary Model

```
log_price_i = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
            + β4·spline(log_area_i)
            + β5..β17·one_hot(category_i, drop_first)
            + β18..β20·one_hot(attribution_class_i, drop_first)
            + β21·gallery_target_encode_i  (leakage-safe OOF)
            + β22..β26·multi_hot(gallery_cities_i, top-5)
            + ε_i
```

- Estimator: `sklearn.linear_model.HuberRegressor(epsilon=1.35, alpha=1e-4)` (운영 모델 동일 hyperparameters)
- Loss: Huber (운영 spec §1-§16 cold rollout default 와 동일 — §17 warm-only path 와 분리, 코덱스 P0 인용 정정)

### 2.3 Implementation
- 환경 pin: Stage 6B prereg 와 동일 (Python 3.14 / scikit-learn / category_encoders / numpy / pandas — 실험 시작 시 version 명시)
- Random seed: 100-seed LAO (Stage 3 / 6A / 6B 동일 seed range 0-99)
- Code path: `experiments/structural_v1/feature_track_axis_a1.py` (신설)
- Train data: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5` (변경 X)

### 2.4 명시 배제 (HARK 회피)
- ❌ medium_type / 다른 design draft inventory features (A.2 / A.3 / A.4 / A.5)
- ❌ Interaction (위 §2.1.d 동일)
- ❌ Per-segment encoding (low / mid-high 별 다른 encoding)
- ❌ Re-fit on test fold (cross-fitting 5-fold 만 허용)
- ❌ Hyperparameter tuning (epsilon / alpha 운영 모델 그대로 고정)

### 2.5 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, 운영 채택 모델)
- 비교 단위: cold-start LAO 100-seed MdAPE (Stage 3 / 4 / 6A / 6B 동일 split 방식)

### 2.6 Primary Hypothesis (단일, step-internal unadjusted, 코덱스 P1 — 분리 명시)
- H₀: A.1 모델 overall MdAPE ≥ baseline (Stage 3 100-seed mean = 38.05%)
- H₁: A.1 모델 overall MdAPE < baseline AND 저가 harm 없음
- **"unadjusted" 분리 의미**: 본 §2.6 의 "unadjusted" = **step-internal** (A.1 단일 가설 단일 metric 기준, secondary Holm m=3 보정 전). **Program-level cumulative** family (5 step) 의 Bonferroni α=0.01 통제는 §2.10 동일 적용.

### 2.7 Practical Significance
- Δ ≤ -1.0%p (운영 채택 임계 — Stage 3/6A/6B 동일 cold rollout default 임계, 코덱스 P0 인용 정정)
- **Cluster bootstrap 99% CI 상한 ≤ 0** (n=2000 cluster bootstrap on rep seed=0, **α=0.01 Bonferroni 5 step decision rule, 코덱스 P0 사후 operationalization** — minor deviation 명시 / 결과 본 후 정정 = 사후 정정 risk 인정 / 95% / 99% 둘 다 미달이므로 결정 영향 X / deviation log entry 의무)

### 2.8 🔴 Hard Gate
- Δ_low ≤ 0%p (점추정 기준 — 6A/6B prereg 동일 hard gate 정의)
- 운영 spec §3 의 `guardrail_low_price` (예측가 < 5,000,000 KRW) 와 정합 / 6A/6B 의 cold rollout hard gate 이력과 동일 (코덱스 P0 인용 정정 — §17 warm-only 와 분리)
- 위반 시 즉시 FAIL — primary 결과 무관

### 2.9 LAO Secondary Family (Holm m=3, supportive)
1. Low (`price_krw < 5,000,000`) MdAPE
2. Mid-high (`price_krw ≥ 5,000,000`) MdAPE
3. Newly-warm (Stage 3 cohort 외) MdAPE

> sparse-warm 측정 X (LAO 정의상 모순 — 6B 결과 deviation 교훈). Time-split supportive family 는 본 cycle 비포함 (A.1 cheap step → time-split 별도 비용 — A.4/A.5 escalation 시 재검토).

### 2.10 Multiple Comparisons (program-level α 분배)
- 5 step gatekeeping sequence: A.1 → A.2 → A.3 → A.4 → A.5
- **A.1 step α = 0.01** (Bonferroni 5 step, FWER ≤ 0.05)
- 단일 step 단일 가설 단일 metric 적용 (overall LAO MdAPE)
- LAO secondary Holm m=3 = step 내 보정 (α=0.01 base)

### 2.11 Stratification + Subgroup
- Price segment: low / mid-high (§2.8 hard gate)
- Newly-warm: not in Stage 3 cohort (§2.9 LAO secondary)

### 2.12 Canonical Artifact Triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `f4_spline_v1_20260506` + A.1 features = `feature_track_a1_v1_20260507`
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`

## 3. PASS / BORDERLINE / FAIL 결정

### 3.1 PASS (운영 채택 후보)
- **Primary**: Δ ≤ -1.0%p AND Cluster bootstrap CI 상한 ≤ 0
- **🔴 Hard gate**: Δ_low ≤ 0%p
- **LAO Secondary (Holm m=3, α=0.01)**: supportive (PASS 결정 영향 X)
- → Phase 3 shadow 진입 검토 / A.2 진입 불필요

### 3.2 BORDERLINE (A.2 escalation)
- 🔴 Hard gate ✓ AND Primary -1.0 < Δ ≤ -0.3%p
- 또는 Primary 점추정 ≤ -1.0%p but CI 상한 > 0
- → A.2 prereg 진입 (A.1 features drop, alternative hypothesis)

### 3.3 FAIL (A.2 escalation)
- 🔴 Hard gate 위반 (Δ_low > 0) — 즉시 FAIL
- 또는 Primary Δ > -0.3%p
- → A.2 prereg 진입 (B안 — escalation 허용)

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| `gallery_name` target encoding leakage (artist holdout 이지 gallery holdout X) | 5-fold OOF cross-fitting + bayesian smoothing α=10 / unseen gallery → train 평균 / artist holdout 시 gallery 는 일부 train 에 등장 가능 (정상 — gallery holdout 은 본 cycle 비목표) |
| Multicollinearity (`category` × `gallery_name`) | Huber regression 의 자동 handling / Variance Inflation Factor 사후 보고 (informative, 결정 영향 X) |
| Step α=0.01 의 power 손실 | 정직 보고 — power 자체보다 effect stability 우선 (코덱스 Stage 4 권고) |
| A.1 PASS but 운영 spec 변경 부담 (cold rollout default §1-§16) | offline PASS → Phase 3 cold shadow gate (운영 spec §4.0 calibration shadow 와 동일 KPI 형식 — low MdAPE 개선 ≥ -1.0%p / overall 악화 ≤ +0.5%p / segment harm 0 violations) → canary → 단계적 운영 적용 (분기 B calibration only 와 분리) |

## 5. Step Gate (B안 확정)

> 의사결정자 승인 (2026-05-07): Step gate B안 (escalation 허용) 채택.

```
A.1 (cheap categorical 4종)
  ↓ FAIL/BORDERLINE
A.2 (artist popularity 4종, 시점 정합성 검증 후)
  ↓ FAIL/BORDERLINE
A.3 (geometry — aspect ratio + 2D vs 3D)
  ↓ FAIL/BORDERLINE
A.4 (title text embedding, multilingual BERT)
  ↓ FAIL/BORDERLINE
A.5 (image embedding, CLIP/ResNet)
  ↓ FAIL
Axis A 전체 종료 → Axis B (Phase A pre-screen 통과 시) 또는 program-level 재설계
```

> 각 step PASS 시 즉시 운영 채택 후보 + 이후 step 진입 불필요.

## 6. 일정 (LLM-only 추정)

| 단계 | 일정 | 산출물 |
|---|---|---|
| 본 prereg 코덱스 검수 | 1-2일 | P0/P1 적용 후 freeze 확정 |
| `feature_track_axis_a1.py` 구현 | 2-3일 | 100-seed LAO + cluster bootstrap |
| 실험 실행 | 0.5일 (statsmodels MixedLM 보다 가벼움) | `results/feature_track_axis_a1.json` |
| 결과 보고서 | 1일 | `docs/feature_track_axis_a1_results_20260507.md` |
| 코덱스 결과 검수 | 1-2일 | P0/P1/P2 fix |
| 의사결정 (PASS / BORDERLINE / FAIL) | 1일 | A.2 escalation 또는 운영 채택 후보 |

> 총 1주 (LLM-only) — design draft §6 일정 후보와 일치.

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | architecture-only close → feature track |
| Feature track design draft 검수 (2026-05-07) | P0×2 / P1×6 / P2×1 — 본 prereg 에 모두 반영 |
| **A.1 prereg freeze 검수 1차 (2026-05-07)** | **HOLD** — P0 ×3 (multiple comparisons family / target encoding spec freeze / 운영 spec §17 인용 잘못) + P1 ×4 + P2 ×1 |
| **A.1 prereg freeze 검수 — fix 후 GO 예정** | P0 3건 본 commit 일괄 반영 → 구현 진입 가능 |

## 8. 참조

- Feature track design draft: `docs/feature_track_design_20260507.md`
- Stage 6B close: `docs/stage6b_results_20260507.md`
- Stage 4 단기 트랙: `docs/stage4_short_term_track_results_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
