# Feature Track Axis A.2 — Artist Popularity Pre-registration

> **작성일**: 2026-05-07 (freeze)
> **위치**: 새 Phase 2'' Axis A 의 **A.2 cheap falsification step (escalation from A.1 BORDERLINE)**
> **연계**: `docs/feature_track_axis_a1_results_20260507.md` (A.1 BORDERLINE → A.2 escalation, Step gate B안) / `docs/feature_track_axis_a1_prereg_20260507.md` (Step sequence + α=0.01 operationalization) / `docs/feature_track_design_20260507.md` (axis 설계)

> ⚠️ **연구 목적**: A.1 결과 (BORDERLINE — Hard gate ✓ + practical Δ ✓ but 99% CI 미달) 후 step gate B안 (escalation) 에 따라 **artist popularity 4종 추가 시 cold-start LAO 개선 가능?** 평가. **Cheap falsification step** continuation.

> **본 prereg freeze**: 가설 / metric / family / PASS 기준 / per-step freeze 6항목 / 시점 정합성 caveat = **2026-05-07 freeze**. 결과 본 후 변경 X (HARK 회피).

> **A.1 v2 lessons 사전 반영 (코덱스)**:
> 1. **Cluster bootstrap 진짜 구현** (artist 별 indices 사전 매핑 + sample 별 concatenate with replicas) — `np.isin()` collapse bug 회피
> 2. **α=0.01 (Bonferroni 5 step) operationalization = 99% CI 상한 ≤ 0** decision rule (95% CI 는 참고만)
> 3. **Per-step freeze 6항목** (a-f) — 모든 encoding spec 한 줄씩 명시
> 4. **운영 spec 인용 정확성** — §17 warm-only 와 분리, §1-§16 cold rollout default + §3 guardrail_low_price 인용

## 1. Input / Hypothesis

### 1.1 A.1 결과 input
- A.1 100-seed mean: overall -1.34%p / 저가 -0.98%p ✓ hard gate / mid-high -1.67%p / newly-warm -4.06%p
- A.1 99% CI 상한 +3.58%p — α=0.01 decision rule 미달 → BORDERLINE
- Seed-level low violation 41/100 (분포상 robust 신호 X — 평균상 비악화)
- → A.2 escalation (Step gate B안), A.1 features drop (alternative hypothesis sequence)

### 1.2 A.2 Hypothesis
> **운영 모델 F4 + spline 에 artist popularity 4종 추가 시 cold-start LAO MdAPE 개선 + 저가 segment harm 0?**
>
> **A.2 가 추가하는 신호**: 작가 별 인기도 (followers) / 가용성 (for_sale) / P1 작가 표시 (is_p1) / 작품 제작년도 (year_made). A.1 의 작품 분류 / 갤러리 신호와 다른 axis = artist 자체의 시장 효과.

### 1.3 시점 정합성 평가 (코덱스 P1 — 사전 평가 결과)

| Feature | 시점 정합성 | 평가 결과 |
|---|---|---|
| `artist_followers` | artist 당 unique 1.00 (single snapshot) | **운영 F4 의 `artist_total_works` 와 동일 spec** (single snapshot, scrape 시점) — deployment-time consistency 가정 수용 시 진입 가능 |
| `artist_for_sale` | artist 당 unique 1.00 | 동일 |
| `artist_is_p1` | artist 당 unique 1.00 | 동일 |
| `year_made` | 작품 본질 attribute, scrape 시점 무관 | **시점 정합성 명확 OK** |

> **Honest caveat (코덱스 P1 권고)**: A.2 의 followers / for_sale / is_p1 = scrape 시점 (2025-2026 즈음) snapshot. **historical reconstruction 불가** (Artsy historical API 부재 / Stage 5 acquisition 종료로 추가 fetch X). 그러나 **운영 모델 F4 가 이미 동일 spec 의 `artist_total_works` 를 사용 중 → 자기모순 X / 동등 카테고리 feature**. 본 prereg 의 진입 = "deployment-time consistency 가정" 의존 (sale 시점 ≠ deployment 시점에서 동일 snapshot 사용 가정). 향후 historical snapshot 확보 가능 시 재평가.

## 2. Pre-registered Items (2026-05-07 freeze)

### 2.1 Per-step freeze 6항목

#### (a) Feature set — 4종 final

| Feature | Type | 비고 |
|---|---|---|
| `artist_followers` | numeric | log1p transform (0 followers 처리) |
| `artist_for_sale` | numeric | log1p transform |
| `artist_is_p1` | boolean | 1.0/0.0 (NaN → 0) |
| `year_made` | numeric | birth_year_centered 와 동일 방식 — train mean 으로 centering (시점 정합성 OK) |

#### (b) Encoding — spec freeze (한 줄씩)
- **`artist_followers`**: `np.log1p(followers)` — 0 followers (NaN imputed to 0) 안전 / numeric column 1개
- **`artist_for_sale`**: `np.log1p(for_sale)` — NaN → 0 / numeric column 1개
- **`artist_is_p1`**: boolean → float (`True` = 1.0, `False` 또는 NaN = 0.0) / numeric column 1개
- **`year_made_centered`**: `year_made - mean(year_made_train)` — train fold mean 기준 centering (LAO 시 train fold 평균 변동 — 정상 spec) / numeric column 1개
- 4 features 모두 numeric, no categorical encoding 필요

#### (c) Preprocessing
- Missing imputation:
  - `artist_followers` 0% missing — imputation 불필요
  - `artist_for_sale` 0% missing
  - `artist_is_p1` 0% missing — but boolean conversion 시 `pd.NA` 안전 처리 (False)
  - `year_made` 0% missing
- Outlier handling: Huber regression 자체로 처리 (운영 모델과 동일)
- Standardization: 운영 모델과 동일 (raw numeric — Huber 가 robust)

#### (d) Interaction 허용 범위 — **NONE** (additive only, A.1 동일)
- ❌ `is_low` × feature interaction
- ❌ feature × feature interaction (e.g., `followers` × `is_p1`)
- ❌ Polynomial / spline of new features
- ❌ Per-segment encoding

#### (e) Stop/go rule (LAO primary family — §3 적용, A.1 v2 lessons 적용)
- **PASS**: Δ ≤ -1.0%p AND **Cluster bootstrap 99% CI 상한 ≤ 0 (α=0.01 decision rule)** AND Hard gate Δ_low ≤ 0%p → 운영 채택 후보 (이후 A.3 진입 불필요)
- **BORDERLINE**: -1.0 < Δ ≤ -0.3%p AND Hard gate ✓ → A.3 escalation
- **FAIL**: Δ > -0.3%p OR Hard gate 위반 → A.3 escalation (B안)

#### (f) 다음 step (alternative hypothesis sequence)
- A.2 FAIL/BORDERLINE 시 → **A.3 (geometry — aspect ratio + 2D vs 3D from width_cm/height_cm) 로 escalation**
- **A.3 prereg 에서 A.2 features 전부 drop** (model spec = **비누적 feature set** / 각 step 은 독립 model 비교)
- A.3 의 baseline = 운영 모델 F4 (A.1 / A.2 features 미사용)
- **Inferential family = program-level cumulative** (5 step Bonferroni α=0.01, FWER ≤ 0.05) — A.1 §2.1.f 와 동일

### 2.2 Primary Model

```
log_price_i = β0 + β1·log_area_i + β2·birth_year_centered_i + β3·log_artist_total_works_i
            + β4·spline(log_area_i)
            + β5·log1p(artist_followers_i)
            + β6·log1p(artist_for_sale_i)
            + β7·artist_is_p1_i
            + β8·year_made_centered_i
            + ε_i
```

- Estimator: `sklearn.linear_model.HuberRegressor(epsilon=1.35, alpha=1e-4)` (운영 모델 동일)
- Loss: Huber (운영 spec §1-§16 cold rollout default, §17 warm-only 와 분리 — A.1 P0 인용 정정 동일)

### 2.3 Implementation
- 환경 pin: A.1 동일 (Python 3.14 / scikit-learn / numpy / pandas)
- Random seed: 100-seed LAO (Stage 3 / 6A / 6B / A.1 동일 seed range 0-99)
- Code path: `experiments/structural_v1/feature_track_axis_a2.py` (신설)
- Train data: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5` (변경 X)
- **Cluster bootstrap = A.1 v2 fix 그대로 사용** (artist 별 indices 사전 매핑 + sample 별 concatenate with replicas)

### 2.4 명시 배제 (HARK 회피)
- ❌ A.1 features (category / attribution_class / gallery_name / gallery_cities) — alternative hypothesis sequence
- ❌ Interaction (위 §2.1.d)
- ❌ Per-segment encoding
- ❌ 다른 design draft inventory features (A.3 / A.4 / A.5)
- ❌ Hyperparameter tuning (epsilon / alpha 운영 모델 그대로 고정)

### 2.5 Baseline 비교
- Baseline = `track2_v1_20260507` (F4 + spline + Huber, 운영 채택 모델, A.1 features 미사용)
- 비교 단위: cold-start LAO 100-seed MdAPE

### 2.6 Primary Hypothesis (단일, step-internal unadjusted)
- H₀: A.2 모델 overall MdAPE ≥ baseline (Stage 3 100-seed mean = 38.05%)
- H₁: A.2 모델 overall MdAPE < baseline AND 저가 harm 없음
- "unadjusted" = step-internal (A.2 단일 가설 단일 metric 기준). Program-level cumulative family (5 step Bonferroni α=0.01) = §2.10 동일.

### 2.7 Practical Significance
- Δ ≤ -1.0%p (운영 채택 임계 — Stage 3/6A/6B/A.1 동일 cold rollout default)
- **Cluster bootstrap 99% CI 상한 ≤ 0** (α=0.01 Bonferroni 5 step decision rule, A.1 v2 lessons 사전 적용 — 95% CI 는 참고만)

### 2.8 🔴 Hard Gate
- Δ_low ≤ 0%p (점추정 기준 — 6A/6B/A.1 동일)
- 운영 spec §3 `guardrail_low_price` (예측가 < 5,000,000 KRW) 와 정합 / cold rollout hard gate 이력과 동일
- 위반 시 즉시 FAIL — primary 결과 무관

### 2.9 LAO Secondary Family (Holm m=3, supportive)
1. Low (`price_krw < 5,000,000`) MdAPE
2. Mid-high (`price_krw ≥ 5,000,000`) MdAPE
3. Newly-warm (Stage 3 cohort 외) MdAPE

> sparse-warm 측정 X (LAO 정의상 모순 — A.1 동일).

### 2.10 Multiple Comparisons (program-level α 분배)
- 5 step gatekeeping sequence: A.1 → A.2 → A.3 → A.4 → A.5
- **A.2 step α = 0.01** (Bonferroni 5 step, FWER ≤ 0.05) — A.1 동일
- 99% CI 상한 ≤ 0 = decision rule (A.1 v2 lessons)
- LAO secondary Holm m=3 = step 내 보정 (α=0.01 base)

### 2.11 Stratification + Subgroup
- Price segment: low / mid-high (§2.8 hard gate)
- Newly-warm: not in Stage 3 cohort (§2.9 LAO secondary)

### 2.12 Canonical Artifact Triple
- Model hash (baseline): `track2_v1_20260507`
- Feature pipeline version: `f4_spline_v1_20260506` + A.2 features = `feature_track_a2_v1_20260507`
- Train data hash: `data/curated/stage4_full.parquet` SHA-16 = `b7b51b81d3a033b5`

## 3. PASS / BORDERLINE / FAIL 결정

### 3.1 PASS (운영 채택 후보)
- **Primary**: Δ ≤ -1.0%p AND Cluster bootstrap **99% CI** 상한 ≤ 0
- **🔴 Hard gate**: Δ_low ≤ 0%p
- **LAO Secondary (Holm m=3, α=0.01)**: supportive (PASS 결정 영향 X)
- → Phase 3 cold shadow 진입 검토 / A.3 진입 불필요

### 3.2 BORDERLINE (A.3 escalation)
- 🔴 Hard gate ✓ AND Primary -1.0 < Δ ≤ -0.3%p
- 또는 Primary 점추정 ≤ -1.0%p but **99% CI** 상한 > 0
- → A.3 prereg 진입 (A.2 features drop, alternative hypothesis)

### 3.3 FAIL (A.3 escalation)
- 🔴 Hard gate 위반 (Δ_low > 0) — 즉시 FAIL
- 또는 Primary Δ > -0.3%p
- → A.3 prereg 진입 (B안 — escalation 허용)

## 4. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Single snapshot artist feature (followers/for_sale/is_p1) → historical leakage 가능성 | **운영 F4 의 `artist_total_works` 와 동일 spec** (운영 채택 시점에 이미 인정된 가정) / deployment-time consistency 가정 honesty caveat 명시 (§1.3) |
| `year_made` numeric 처리 — 비선형 관계 가능성 | A.4-A.5 escalation 시 spline / interaction 추가 검토 (본 cycle 명시 배제) |
| `is_p1` boolean 의 imbalance (P1 작가 비율) | Huber regression 자체로 robust / β 추정값 sensitivity 사후 검토 |
| Step α=0.01 의 power 손실 | 정직 보고 (A.1 동일) — power 자체보다 effect stability 우선 |
| A.2 PASS but 운영 spec §1-§16 변경 부담 | offline PASS → Phase 3 cold shadow gate (§4.0 calibration shadow KPI 형식) → canary → 단계적 운영 적용 |

## 5. Step Gate (B안 확정, A.1 동일)

```
A.1 (cheap categorical 4종) — BORDERLINE (2026-05-07)
  ↓ FAIL/BORDERLINE
**A.2 (artist popularity 4종)** — 본 prereg
  ↓ FAIL/BORDERLINE
A.3 (geometry — aspect ratio + 2D vs 3D)
  ↓ FAIL/BORDERLINE
A.4 (title text embedding, multilingual BERT)
  ↓ FAIL/BORDERLINE
A.5 (image embedding, CLIP/ResNet)
  ↓ FAIL
Axis A 전체 종료 → Axis B (Phase A pre-screen 통과 시) 또는 program-level 재설계
```

## 6. 일정 (LLM-only 추정)

| 단계 | 일정 | 산출물 |
|---|---|---|
| 본 prereg 코덱스 검수 (option) | 1-2일 | P0/P1 적용 후 freeze 확정 |
| `feature_track_axis_a2.py` 구현 | 1-2일 (A.1 코드 기반 derivative) | 100-seed LAO + cluster bootstrap |
| 실험 실행 | 0.5일 | `results/feature_track_axis_a2.json` |
| 결과 보고서 + 코덱스 검수 | 1-2일 | `docs/feature_track_axis_a2_results_20260507.md` |
| 의사결정 (PASS / BORDERLINE / FAIL) | 1일 | A.3 escalation 또는 운영 채택 후보 |

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Stage 6B 결과 최종 검수 (2026-05-07) | architecture-only close → feature track |
| Feature track design draft 검수 (2026-05-07) | P0×2 / P1×6 / P2×1 |
| A.1 prereg freeze 검수 (2026-05-07) | HOLD → P0×3 + P1×4 + P2×1 fix → GO |
| A.1 결과 보고 검수 (2026-05-07) | HOLD → P0×2 (bootstrap bug + α operationalization) + P1×4 fix → v2 |
| **본 A.2 prereg freeze (2026-05-07)** | A.1 v2 lessons 사전 반영 + 시점 정합성 평가 caveat 명시 |
| **A.2 prereg 검수 (선택, 사용자 결정)** | per-step freeze 6항목 / 시점 정합성 spec / α=0.01 99% CI |

## 8. 참조

- A.1 prereg: `docs/feature_track_axis_a1_prereg_20260507.md`
- A.1 결과: `docs/feature_track_axis_a1_results_20260507.md` (BORDERLINE → A.2 escalation)
- Feature track design: `docs/feature_track_design_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
