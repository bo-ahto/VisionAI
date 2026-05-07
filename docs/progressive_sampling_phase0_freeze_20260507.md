# Progressive Sampling — Phase 0 Mini-Prereg Freeze

> **작성일**: 2026-05-07 (Phase 0, freeze)
> **위치**: 사용자 명시 진입 (옵션 A) — Multi-fidelity exploratory development with locked holdout and pre-registered hypothesis families
> **사용자 instruction**: "체크포인트 설정 후 A 로 바로 진입 해보면서 시행"
> **코덱스 사전 자문**: 조건부 GO — 3 조건 (Stage 3 transfer filter / holdout decision-binding / family cap·tie·stop rule 사전 고정)

> ⚠️ **본 cycle 의 본질 (코덱스 framing)**: HARK-safe variant of `Progressive sampling for exploratory model development, followed by a locked confirmatory evaluation`. **Stage 1-3 exploratory only / Stage 4 holdout 만 confirmatory** (단 program-internal, 외부 복제 X). Holdout PASS → **production-shadow candidate** (default 운영 변경 직접 trigger X — 별도 prereg cycle 필요).

## 1. Freeze 6항목 (코덱스 P0)

### 1.1 Primary KPI + harm metric
- **Primary**: Overall MdAPE (cold-start LAO 100-seed mean) — 운영 baseline `track2_v1_20260507` 의 stage4_full = 38.03% 기준 비교
- **Harm metric**: Low-price MdAPE (price < 5M KRW) — `Δ_low` (baseline 대비)
- **Decision rule (Stage 별, 코덱스 권고)**:
  - Stage 1 retain: Overall Δ ≤ -0.3%p AND Low Δ ≤ +0.2%p (exploratory threshold, soft)
  - Stage 2 통과: Overall Δ ≤ -0.7%p AND Low Δ ≤ 0%p
  - Stage 3 winner: Overall Δ ≤ -1.0%p AND Low Δ ≤ 0%p (full-like distribution 기준)
  - Stage 4 dev: Overall Δ ≤ -1.0%p AND Low Δ ≤ 0%p (winner 1 spec)
  - Stage 4 holdout: Overall Δ ≤ -1.0%p AND Low Δ ≤ 0%p (confirmatory 1회)

### 1.2 Locked holdout split spec
- **Source**: `stage4_full.parquet` (8,495 rows / 807 artists)
- **Ratio**: artist 20% holdout (~161 artists / ~1,640 rows 추정 — heavy skew tolerance 명시)
- **Stratify (코덱스 권고 3축)**:
  1. Artist depth bucket: `1 / 2 / 3-4 / 5-9 / 10-19 / 20+` (1순위)
  2. Artist median price bucket: `<5M / 5-20M / 20M+` (2순위)
  3. Artist low-price share: `0% / 1-50% / 51-99% / 100%` (3순위)
- **Random seed**: **42** (사전 고정)
- **Artist list hash**: SHA-16 (Phase 0 봉인 시 계산 / 봉인 후 변경 X)
- **Access 제한**: Phase 0 봉인 후 Phase 4 final 1회 evaluation 만 허용 / Phase 1-3 / Phase 4 dev = holdout 격리
- **Output**: `data/curated/progressive_sampling_locked_holdout_v1.parquet` (artist_slug list + hash)

### 1.3 가설 family roster (5 families, 코덱스 우선순위)

| 순위 | Family | 정의 | Variant cap | Tie rule | 비고 |
|---|---|---|---|---|---|
| **1** | **Geometry variants** | aspect_ratio polynomial / depth spline / shape cluster / aspect × is_3d interaction | 5 variants | 1 (또는 tied 2) | A.3 strongest 후속 |
| **2** | **Temporal engineering** | year_made × birth_year / career age / decade dummy / age × log_area | 4 variants | 1 (또는 tied 2) | 시점 정합성 명확 |
| **3** | **Cross-artist categorical interactions** | gallery × category / city × medium / attribution × is_3d | 3 variants | 1 (tie 허용 X) | A.1 categorical 확장 |
| **4** | **Artist-level statistical features (negative control)** | popularity / for_sale ratio / median price | 3 variants | 1 (tie X) | A.2 / 6B prior weak — re-test only |
| **5** | **Missingness / measurement-quality flags** | year_made_missing / depth_missing / price_currency_USD 등 | 3 variants | 1 (tie X) | low prior |

> **명시 배제 (HARK 회피)**:
> - ❌ A.1-A.5 의 frozen feature spec 변경 (기존 spec 그대로)
> - ❌ Family 외 새 axis (cohort 변경 / 모델 family 변경 / loss function 변경)
> - ❌ Hyperparameter tuning (Huber epsilon=1.35 / alpha=1e-4 고정)
> - ❌ Multiple model classes (HuberRegressor 만)

### 1.4 Stage별 pruning / stop rule

| Stage | Dataset | 역할 | Output |
|---|---|---|---|
| **Stage 1** | stage1_200x20 | 가설 발굴 / family triage | family 별 best 1 variant (tie 시 2) → 5-10 variants |
| **Stage 2** | stage2_500x50 | family 간 비교 | 1-2 family pruning |
| **Stage 3** | **stage4_full holdout-제외 stratified subset (~1000-2000 rows)** (코덱스 P0 — curated-uniform X / **full-like transfer filter**) | 단일 family 단일 spec 확정 | 1 winner spec |
| **Stage 4 dev** | stage4_full (holdout 제외, ~6800 rows) | winner 1 spec full dev 평가 | 평가 결과 |
| **Stage 4 holdout** | locked holdout (~1640 rows) | confirmatory 1회 | PASS / FAIL |

> **코덱스 P0 — Stage 3 = full-like transferability filter (curated-uniform 사용 X)**: 사용자 원안의 stage3_1000x100 (curated cohort) 변경 → stage4_full 에서 stratified subset 사용 (composition gap 회피).

### 1.5 불변 pipeline (freeze)
- Baseline: `track2_v1_20260507` (F4 + spline + Huber)
- Preprocessing: 운영 spec 동일 (Stage 6B / A.1-A.5 동일)
- Model class: `HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=2000)` (변경 X)
- Cluster bootstrap: 진짜 구현 (artist 별 indices 사전 매핑 + with replicas, A.1 v2 fix)
- Decision rule: α=0.01 99% CI Bonferroni (Stage 4 holdout 만)

### 1.6 Decision-binding 분리 (코덱스 P0)

| 단계 | Language | Action ladder |
|---|---|---|
| Stage 1-3 | **exploratory uplift** | family triage / pruning (decision X) |
| Stage 4 dev | **exploratory winner identification** | winner 1 spec 확정 (decision X) |
| Stage 4 holdout | **program-internal confirmatory uplift** | PASS → **production-shadow candidate** (별도 prereg cycle 필요) / **default 운영 변경 직접 trigger X** |

## 2. Stop / Pivot rule (코덱스 권고)

본 cycle 즉시 중단 또는 pivot:
- Stage 1: 모든 family 가 `Overall near-null + Low non-harm 미달` → 중단
- Stage 2: winner family 가 seed/sample 교체마다 자주 뒤집힘 → 중단
- Stage 3: winner 가 full-like sample 에서 sign reverse → 중단
- Stage 4 dev: winner 가 baseline 대비 `Overall ≥ 0` OR `Low > 0` → 중단
- Stage 4 holdout: PASS but effect size 미미 → default 변경 X / shadow only

## 3. 본 cycle 명시 한계 (코덱스 P1 caveat)

- **본 cycle = program-internal confirmatory** — 외부 복제 X
- Stage 3 transfer filter 적용 후 결과도 **현재 정보조건 (curated Artsy + F4 spec) 한정**
- 새 정보축 (Axis B license-first lane) 진입 후 결과 변동 가능
- Family D (artist stats) = negative control — main winner 후보 X
- holdout PASS = production-shadow candidate (default 운영 변경 trigger 아님)

## 4. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Axis A / Axis B Round 1-3 / HTML v2 / Sample sensitivity) | P0×16 + P1×56 + P2×27 + sample sensitivity (P0×0 + P1×3 + P2×3) = P0×16 + P1×59 + P2×30 |
| Iterative method 자문 (2026-05-07) | HARK-safe variant 권고 (locked holdout + 3-way split + family pre-registration) |
| **Phase 0 freeze 사전 자문 (2026-05-07)** | 조건부 GO + 3 조건 (Stage 3 transfer filter / holdout decision-binding / family cap·tie·stop rule) |

## 5. 다음 단계

1. ✅ Phase 0 freeze — 본 commit
2. ⏳ Locked holdout 봉인 (stage4_full 에서 stratified artist 20% 샘플링 + hash + parquet 저장)
3. ⏳ Phase 1 / Stage 1 (200x20) exploration — family 별 variant generation + best 1-2 selection
4. ⏳ 체크포인트 1 — Stage 1 결과 검토 + Stage 2 진입 여부 결정 + 코덱스 사후 검수
5. (조건부) Phase 2-3-4 dev-holdout

## 6. 참조

- Sample sensitivity 결과: `docs/sample_size_sensitivity_results_20260507.md` (composition gap 입증)
- Axis A 5 step prereg + 결과: `docs/feature_track_axis_a*_*_20260507.md`
- Stage 6B close: `docs/stage6b_results_20260507.md`
- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md`
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
