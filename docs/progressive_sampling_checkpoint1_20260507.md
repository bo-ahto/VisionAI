# Progressive Sampling — Checkpoint 1 (Phase 0 + Stage 1 결과)

> **작성일**: 2026-05-07
> **mini-freeze**: `docs/progressive_sampling_phase0_freeze_20260507.md` (Phase 0 mini-prereg)
> **실험**: `experiments/structural_v1/progressive_sampling.py` / `results/progressive_sampling_stage1.json`
> **체크포인트**: 1차 — Stage 2 진입 여부 결정 영역

> ⚠️ **본 cycle framing (코덱스)**: Stage 1 결과 = **exploratory only / decision X**. 200x20 작은 sample noise (sample sensitivity 분석 std 9.41% / IQR 12.96%) — 결과 자체 unreliable for decision-grade.

## 0. Checkpoint 1 한 줄 요약 (코덱스 사후 검수 v2 적용)

> **Phase 0 holdout 봉인 완료** (161 artists / 1,680 rows / SHA-16 hash `1933a0947a918fc9`).
>
> **Stage 1 결과**: 5 family × 18 variants 평가 — **모든 variant retain 기준 미달** (Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p / 단 4 variants SKIP — Stage 1 schema 부재).
>
> **코덱스 사후 검수 권고**: **Stage 2 진입 = HOLD**. Stage 1 = promotion evidence 너무 noisy / pruning evidence 충분히 negative. Literal stop-rule = 비트리거 (Family D Low 개선) but **operational decision = 종결**.
>
> **Family D sub-signal**:
> - `artist_popularity`: Overall +0.68%p but Low -3.33%p / High +1.78%p
> - `artist_median_proxy`: Low -1.59%p but Overall +1.61%p / High +2.25%p
> - → **artifact prior 더 높음** (small-sample noise / segment heterogeneity) — transferability 근거 X
> - 본 cycle continuation 근거 X / **별도 exploratory low-slice 가설로만 보존** (코덱스 권고)
>
> **HARK risk (코덱스 P1)**: Stage 2 진입 reasoning = "all-family triage" → "Family D rescue" 변경 시 reasoning drift. Family D = 원래 negative control prereg.

## 1. Phase 0: Locked holdout 봉인 결과

### 1.1 Holdout spec (코덱스 권고 적용)
| 항목 | 값 |
|---|---|
| Source | `stage4_full.parquet` (8,495 rows / 807 artists) |
| Holdout 비율 | 20% (artist 기준) |
| Holdout artists | **161** |
| Holdout rows | **1,680** |
| Random seed | **42** (사전 freeze) |
| Stratify 1 | Artist depth bucket (1 / 2 / 3-4 / 5-9 / 10-19 / 20+) |
| Stratify 2 | Artist median price bucket (<5M / 5-20M / 20M+) |
| Stratify 3 | Artist low-price share (0% / 1-50% / 51-99% / 100%) |
| Hash (SHA-16) | **1933a0947a918fc9** |
| File | `data/curated/progressive_sampling_locked_holdout_v1.parquet` |
| Hash file | `data/curated/progressive_sampling_locked_holdout_v1.hash.txt` |
| Access 제한 | Phase 4 final 1회만 (Phase 1-3 / Phase 4 dev = 격리) |

### 1.2 Holdout 봉인 검증
- 봉인 후 hash file 변경 X 보장
- 본 cycle 의 모든 후속 단계 (Stage 1-3 / Stage 4 dev) = holdout 격리
- Phase 4 final = locked holdout 1회 confirmatory only

## 2. Stage 1 결과 (Family × Variant)

### 2.1 종합 표 (운영 baseline F4 + spline + Huber 대비 Δ)

| Family | Variant | Δ_overall | Δ_low | Δ_high | Retain |
|---|---|---|---|---|---|
| **Geometry** | geom_aspect_poly | +0.49%p | -0.02%p | +0.57%p | ✗ |
| | geom_aspect_is3d | +1.83%p | +0.48%p | +1.46%p | ✗ |
| | geom_depth_spline | SKIP | — | — | — (Stage 1 schema 부재) |
| | geom_max_dim | +0.00%p | -0.00%p | +0.00%p | ✗ |
| | geom_full | +2.14%p | +2.10%p | +1.41%p | ✗ |
| **Temporal** | temp_year_birth | +2.84%p | +3.12%p | +2.84%p | ✗ |
| | temp_career_age | +0.06%p | -0.13%p | +0.86%p | ✗ |
| | temp_decade | +0.52%p | +0.54%p | +0.43%p | ✗ |
| | temp_age_x_area | +0.43%p | +0.28%p | +0.48%p | ✗ |
| **Cross-artist categorical** | cat_gallery_x_category | +4.14%p | +1.63%p | +4.28%p | ✗ |
| | cat_city_medium | +1.93%p | +3.28%p | +1.45%p | ✗ |
| | cat_attribution_x_3d | SKIP | — | — | — |
| **Artist stats (negative control)** | **artist_popularity** | **+0.68%p** | **-3.33%p** | +1.78%p | ✗ (Low 개선 but Overall 미달) |
| | artist_for_sale | +0.21%p | +0.78%p | +0.37%p | ✗ |
| | **artist_median_proxy** | **+1.61%p** | **-1.59%p** | +2.25%p | ✗ (Low 개선 but Overall 미달) |
| **Missingness** | miss_year_made | -0.00%p | -0.00%p | -0.00%p | ✗ (effect ≈ 0) |
| | miss_depth | SKIP | — | — | — (Stage 1 schema 부재) |
| | miss_proxy_USD | +2.21%p | +1.42%p | +2.95%p | ✗ |

### 2.2 Stage 1 retain logic 적용
- 5 family 별 best 1 (tied 2) 선택
- Retain 기준: Overall Δ ≤ -0.3%p **AND** Low Δ ≤ +0.2%p
- **결과**: 5 family 모두 retain 항목 **0** — 모든 family 의 best variant 도 Overall 기준 미달

### 2.3 sub-signal observations (decision-grade X — exploratory)

> ⚠️ **코덱스 framing 톤**: 본 sub-signal = **small-sample exploratory pattern**, full transferability 미검증. Stage 2/3 에서 sign reverse 가능성 큼 (composition gap).

**Sub-signal 1: artist_popularity / artist_median_proxy 의 Low specific 개선**
- artist_popularity: Low -3.33%p / High +1.78%p
- artist_median_proxy: Low -1.59%p / High +2.25%p
- 패턴: 저가 segment 에서 artist popularity feature 가 noise reduction / mid-high 에서는 noise injection
- **CAVEAT (코덱스 P0)**: Family D = negative control (Axis A.2 에서 이미 cold-start LAO 무력 입증) — 본 sub-signal 은 200x20 noise 또는 segment heterogeneity artifact 가능성

**Sub-signal 2: 모든 family 의 Overall 악화 패턴**
- 18 variants 중 17 개 Overall positive (악화)
- 패턴: Stage 1 200x20 의 small sample 에 추가 features = overfitting (degrees of freedom 증가)
- **CAVEAT**: small sample 의 add-feature negative effect 일반 패턴 — 모델 quality issue X / sample size 효과

## 3. Stop / Continue 결정 영역 (코덱스 사후 검수 v2)

### 3.1 코덱스 stop rule (Phase 0 freeze §2) 적용

**Literal vs Operational reading (코덱스 P1 분리)**:

| Reading | 본 결과 | 결론 |
|---|---|---|
| **Literal strict** (모든 family Overall near-null + Low non-harm 미달 동시) | ✗ 비트리거 (Family D Low 개선) | 종결 X |
| **Operational** (family-level retain advancement) | ✓ trigger (5 family 모두 retain 0건) | **종결 권고** |

→ **코덱스 권고: operational reading 적용 → Stage 2 진입 HOLD / 본 cycle 종결**

### 3.2 의사결정 영역 (코덱스 사후 검수 v2)

**Option A (코덱스 권고): 본 cycle 종결**
- 근거: Stage 1 family-level retain 0건 (operational stop) / Stage 1 noise (std 9.41%) = decision-grade evidence X
- Phase 0 holdout 봉인 유지 (cancel X — 향후 별도 cycle 활용 가능)
- Axis B license-first lane 우선 진입 (코덱스 종합 검수 권고와 일치)

**Option B (HARK risk): Stage 2 진입 + sub-signal rescue**
- ⚠️ **HARK risk**: 진입 reasoning = "all-family triage" → "Family D rescue" 변경 = reasoning drift
- Family D = 원래 negative control prereg / Axis A.2 (full-like) FAIL 결과와 일관
- 코덱스 권고와 충돌

**Option C (HARK 위반): Stage 2 + family 재정의** — 비추천 그대로

## 4. Honesty Caveats (코덱스 사후 검수 v2 — 추가 P2 caveat 3건)

- **Stage 1 200x20 = small sample noise**: sample sensitivity std 9.41% / IQR 12.96% (가장 unstable) — Stage 1 결과 자체 unreliable for decision-grade
- **Sub-signal (artist_popularity Low 개선)**: small-sample exploratory pattern, **full transferability 미검증** (composition gap + Family D negative control prior)
- **18 variants 중 17 Overall positive**: small sample + new features = overfitting 일반 패턴 (degrees of freedom)
- **Phase 0 holdout 봉인**: 본 결과 무관 / 봉인 유지 / Phase 4 final 1회만 사용
- **Decision-grade evidence X**: 본 결과는 운영 spec 변경 trigger 아님 / Stage 2 진입 여부 자체가 의사결정 영역

### 4.1 추가 honesty caveats (코덱스 P2)
- **SKIP variants 존재 (4건)**: geom_depth_spline / cat_attribution_x_3d / miss_depth / (geom_full 일부 dim) — Stage 1 schema (depth_cm 부재) → "모든 preregistered variant 가 공정하게 졌다" X / **"평가 가능한 variant 들에서 advancement evidence 없음"** 이 정확
- **Family D = 원래 negative control prereg**: Phase 0 freeze §1.3 "main winner 후보 X / re-test only" — 본 cycle 진입 reasoning = Family D rescue 가 되면 reasoning drift / HARK risk
- **A.2 FAIL (full-like) vs Stage 1 median_proxy 완전 동일 가설 X**: A.2 = 4 features bundle (followers/for_sale/is_p1/year_made) full-like dataset / Stage 1 median_proxy = followers + for_sale 단순 조합 / 200x20 — 본 결과 = A.2 재해석 근거 X

## 5. 다음 단계 (사용자 결정 영역, 코덱스 사후 검수 v2 적용)

> **코덱스 사후 검수 권고 (Stage 2 진입): HOLD** — operational decision = 종결.
> **사용자 보고 framing (코덱스)**: "Checkpoint 1 에서는 Stage 1 이 decision-grade 승급 근거를 제공하지 못했다. Literal stop-rule 은 엄밀히는 비트리거지만, family-level retain 0건과 Stage 1 의 높은 noise 를 고려하면 operational decision 은 HOLD/종결이 타당하다. artist_popularity·artist_median_proxy 의 low 개선은 본 cycle continuation 근거가 아니라, 별도 exploratory low-slice 가설로만 보존한다."

| 옵션 | 본질 | 코덱스 권고 v2 |
|---|---|---|
| **A. 본 cycle 종결** | family retain 0건 / advancement evidence X / Axis B license-first 우선 | **권고** ✓ |
| B. Stage 2 진입 (sub-signal rescue) | HARK risk (Family D rescue reasoning drift) | **비추천** |
| C. Stage 2 + family 재정의 | HARK 위반 | 비추천 |
| D. 별도 exploratory sub-cycle (low-slice 가설 보존) | sub-signal 보존 only / 본 cycle continuation 아님 | 가능 (별도 freeze) |

## 6. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 | P0×16 + P1×59 + P2×30 |
| Phase 0 사전 자문 | 조건부 GO + 3 조건 (Stage 3 transfer filter / holdout decision-binding / family cap·tie·stop rule) |
| **Checkpoint 1 사후 검수 (2026-05-07)** | **Stage 2 진입 HOLD 권고 / 본 cycle 종결**. P0 없음. P1×4 (literal vs operational stop reading / sub-signal artifact prior / HARK risk Family D rescue / Stage 1 noise decision-grade X) + P2×3 (SKIP variants 명시 / Family D negative control prereg / A.2 vs median_proxy 완전 동일 X) — 본 v2 commit 일괄 반영 |

## 7. 참조

- Phase 0 freeze: `docs/progressive_sampling_phase0_freeze_20260507.md`
- Sample sensitivity: `docs/sample_size_sensitivity_results_20260507.md`
- Axis A 5 step 종결: `docs/feature_track_axis_a*_*_20260507.md`
- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md`
- Methodology pipeline / Deviation log
