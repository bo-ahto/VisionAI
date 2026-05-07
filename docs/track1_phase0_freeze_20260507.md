# Track 1 — Phase 0 Mini-Prereg Freeze (Feature Re-audit Cycle)

> 🔒 **Status: CLOSED on 2026-05-07** via Phase 0 §4 fail trigger (Audit 4 OOF 악화 + Saatchi slice 비대칭 violation). 본 cycle 종결 결정 = `docs/track1_phase0_closeout_20260507.md` (Option A). 본 freeze 문서는 immutable terminal evidence — 본문 개정 X.

> **작성일**: 2026-05-07 (Phase 0, freeze)
> **위치**: 트랙 1 (1차 시장 갤러리 가격 예측 운영 모델) 의 사전등록 method 도입 — 비선형 모델 feature 수 조정 재검수
> **사용자 instruction**: "트랙 1 도 제대로된 실험 방법론 도입 / 비선형 모델 예측도 높이는 실험 / 피처 수 조정부터 재검수"
> **코덱스 사전 자문**: 조건부 GO — Phase 0 freeze 우선 (feature selection 자체가 아닌 평가 protocol freeze 가 1순위)

> ⚠️ **본 cycle 의 본질 (코덱스 framing)**: 트랙 2 의 사전등록 governance 를 트랙 1 에 이식하되, **threshold 와 metric hierarchy 는 트랙 1 (운영 메인 모델, decision-binding) 용으로 재설계**. 본 cycle 결과 = 운영 spec 변경 trigger 가능성 큼 → 트랙 2 보다 더 엄격한 gate 적용.

## 1. Phase 0 Freeze 8항목 (코덱스 권고)

### 1.1 Baseline variant 1개 고정 (P0 #1 ambiguity 해소)

> **사용자 inventory 의 ambiguity (코덱스 P0)**: `37 features (historical integrated_v3)` vs `32 features (v3_filtered_tuned, 현재 서빙)` — **`v3_filtered_tuned` 32f 로 고정** = **operational anchor baseline** (코덱스 P1 표현 정정 — "clean baseline" 단정 X / 현재 서빙 contract 와 직접 대응하는 유일한 기준선). historical 37f 는 이미 prior cycle 에서 제거된 drift feature 5+ 포함하는 재구성 계열 (`docs/model_technical_report_v2.md:48, 65-71`) — exact serving comparator X.

| 항목 | 값 |
|---|---|
| Baseline variant | **`v3_filtered_tuned`** (현재 운영 서빙) |
| Models | CatBoost (`integrated_v3_filtered_tuned_catboost.cbm`) + XGBoost (`integrated_v3_filtered_tuned_xgboost.json`) |
| Features | **32** (CB_FEATURES_BASE, `primary_predictor.py:22-54`) |
| Calibration | `integrated_v3_filtered_tuned_source_calibration.json` (cold path only) |
| Best params | `integrated_v3_filtered_tuned_best_params.json` (HP frozen baseline) |
| Provenance | `integrated_v3_filtered_tuned.provenance.json` |

**Baseline performance** (GroupKFold cold-start):
- No model baseline: 71.9% MdAPE
- CatBoost v3_filtered_tuned: **39.4%** MdAPE
- XGBoost v3_filtered_tuned: **39.1%** MdAPE
- Ensemble: 측정 (Stage 0 사전 산출 — Phase 0 freeze 시 명시)

### 1.2 Dataset snapshot 고정
- **Train rows**: 28,376
- **Artists**: 1,551
- **Source**: 운영 학습 cohort (Artsy + Saatchi + 추가 partner sources)
- **Snapshot date**: 본 commit 시점 — `git log integrated_v3_filtered_tuned_metrics.json` provenance 명시
- **Cleansing rules**: 운영 spec 동일 (변경 X)

### 1.3 Feature dictionary + 결측 규칙
- 32 features (CB_FEATURES_BASE) 그대로 — 1 page mapping `docs/data_feature_mapping.md` 참조
- 결측 처리: 운영 spec 동일 (CatBoost native handling / XGBoost imputation 변경 X)
- **Feature integrity recheck (P0 #4)**: Stage 1 첫 작업 — `aspect_ratio` 등 기존 audit 위험 신호 재점검

### 1.4 Primary metric + Hard gates (코덱스 권고 — 트랙 2 보다 엄격)

| 영역 | Metric | 임계 |
|---|---|---|
| **Primary** | Cold-start GroupKFold Overall MdAPE Δ | **≤ -0.7%p** (improvement, 코덱스 P1 — confirmatory 진입 전 단일 숫자 고정) |
| **🔴 Hard gate 1** | Cold low-price MdAPE Δ_low | ≤ 0%p (저가 segment 악화 금지) |
| **🔴 Hard gate 2** | Source slice 비대칭 | Artsy / Saatchi cold 한쪽만 좋아지고 다른 쪽 크게 악화 시 FAIL |
| **🔴 Hard gate 3** | Warm path KFold non-regression | Warm slice MdAPE 악화 금지 |
| **Confirmatory** | Locked holdout artist-cluster 99% CI 상한 | ≤ 0 (α=0.01, 최종 1회만 적용) |

> **트랙 2 vs 트랙 1 차이 (코덱스)**: 트랙 2 = exploratory 단계도 α=0.01 99% CI 적용 / 트랙 1 = α=0.01 최종 confirmatory holdout gate 만 — exploratory stage 강제 X.

### 1.5 Stop rule (Stage 별)
- **Stage 1**: feature integrity 위험 신호 1+건 발견 시 우선 fix → re-run / importance ranking + stability score 산출만 (탈락 후보 식별 only / **채택 결정 X**)
- **Stage 2**: subset family 비교 — 5-10 family 중 retain 0건 시 cycle 중단 (트랙 2 동일 패턴)
- **Stage 3**: HP sensitivity (Stage 2 winner 1-2 만) — search budget 사전 고정
- **Stage 4**: locked holdout 1회 confirmatory — primary + 모든 hard gate 동시 판정

### 1.6 Subset family cap (Stage 2 사전 등록)

코덱스 권고 — semantic group 단위 5-10 family:

| 순위 | Family (예비 — Stage 1 결과 후 확정) | 32 features 중 매칭 |
|---|---|---|
| 1 | **Size group** | ho / ho_power / ln_ho / area_cm2 / ln_area / aspect_ratio / is_small / has_depth |
| 2 | **Material/medium group** | support_factor / ho_x_support / is_unique / is_edition / support_type / medium_category / attribution_class |
| 3 | **Artist profile group** | artist_birth_year / has_birth_year / career_stage / ln_followers / artist_total_works / for_sale_ratio / profile_completeness |
| 4 | **Gallery group** | gallery_tier / gallery_city_count / has_seoul / has_international / gallery_type |
| 5 | **Source-derived / level proxy** | ho_price_level / medium_price_level / source / price_currency / is_krw |

> **Stage 1 결과 후 확정**: integrity recheck + importance ranking + stability score 결과로 family 정의 fine-tune. 본 freeze 의 5 family = 예비. Stage 1 결과 후 **명시적 deviation log entry + Stage 2 prereg 진입 전 family confirm**.

### 1.7 Locked holdout 봉인 spec
- **Source**: 28,376 rows / 1,551 artists (운영 학습 data)
- **Ratio**: artist 20% — 약 310 artists / 추정 5,675 rows
- **Stratify**: artist depth × source × price segment (3축, 트랙 2 패턴)
- **Random seed**: **42** (사전 freeze)
- **Hash**: SHA-16 (**계산 예정** — Stage 1B 진입 또는 Option A drift fix 후 baseline 재산출 시점에 봉인 + hash 기록 / 본 Phase 0 freeze 시점에는 spec 만 freeze, 실제 holdout 봉인 X)
- **Output**: `data/curated/track1_locked_holdout_v1.parquet` + hash file
- **Access 제한**: Phase 4 final 1회만

### 1.8 Decision-binding 분리

| 단계 | Language | Action ladder |
|---|---|---|
| Stage 1 | exploratory diagnostic only | feature integrity / importance / stability — 탈락 후보 식별만 |
| Stage 2 | exploratory subset comparison | family ablation — pruning |
| Stage 3 | exploratory HP sensitivity | Stage 2 winner 1-2 fine-tune |
| Stage 4 | **confirmatory** (program-internal) | Locked holdout 1회 — primary + hard gates 동시 |
| Production trigger | offline 통과 후 shadow → staged rollout | 별도 의사결정 gate (본 cycle 외) |

## 2. 코덱스 권고 적용 (트랙 2 → 트랙 1 이식 vs 재설계)

| 항목 | 트랙 2 → 트랙 1 |
|---|---|
| Locked holdout sealed | 그대로 도입 (artist-level) |
| Hypothesis family prereg | 그대로 도입 (5 family cap) |
| Stage-wise retain rule | 그대로 (모델 갱신 X / 후보 탈락 중심) |
| α=0.01 99% CI Bonferroni | **재설계** — 최종 confirmatory holdout 만 적용 / exploratory 강제 X |
| Cluster bootstrap CI | **artist cluster** (row bootstrap X — 트랙 2 동일) |
| Decision-binding 분리 | 그대로 |
| Threshold | **재설계** — 트랙 1 hard gate (low/source/warm) 추가 |
| Multiple comparisons | exploratory stage = soft retain / confirmatory stage 만 strict |

## 3. 본 cycle Risk + Honesty caveats

- **운영 spec contamination risk**: 트랙 1 = 운영 메인 모델 / 본 cycle 결과 = 운영 변경 trigger 가능 → exploratory ≠ decision-binding 강력 분리
- **Multiple comparisons**: 32 features × N variants × M HP — sequential testing + family pre-registration 필수
- **Composition gap risk (트랙 2 lessons)**: train cohort = 28K / holdout = 5.7K — distribution shift 미관찰 (트랙 1 운영 학습 일관 가정)
- **Feature integrity unknown**: Stage 1 첫 단계 = 점검 필수 (`aspect_ratio` 등 audit 위험 신호 재확인)
- **트랙 2 와 병행**: Axis B license-first lane 운영팀/법무팀 회신 대기 — 트랙 1 = LLM 가능 영역 큼 (병행 OK, 단 결정 로그 분리)

## 4. 다음 단계

1. ✅ Phase 0 freeze — 본 commit
2. ⏳ **Stage 1 진입** — feature integrity recheck + permutation importance + stability selection
   - 진행 방식 (cycle 종결 후 사후 정정, 2026-05-08 P0 hygiene): 본 cycle 의 Stage 1 은 **운영 코드 inspection 기반** 으로 진행됨 (`src/visionai/price_engine/api/primary_feature_builder.py:228-272` + `scripts/prepare_primary_market_dataset.py:262` + `scripts/prepare_saatchi_dataset.py:283` 의 학습 actual 분포 vs 서빙 hardcode 비교). 별도 audit script 미작성.
   - Result doc: `docs/track1_stage1_results_20260507.md`
3. ⏳ 코덱스 사후 검수 (Stage 1 결과)
4. (조건부) Stage 2 / 3 / 4 진입

## 5. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 (Stage 6B / Axis A / Axis B / sample sensitivity / progressive sampling) | P0×16 + P1×72 + P2×38 |
| **Track 1 사전 자문 (2026-05-07)** | 조건부 GO + Phase 0 freeze 우선 + 4 P0 (baseline 고정 / evaluation redesign / cold-warm gate 분리 / feature integrity recheck) |

## 6. 참조

- 운영 코드: `src/visionai/price_engine/api/primary_predictor.py:22-54` (CB_FEATURES_BASE 32 features)
- Baseline metrics: `model_test_results/integrated_v3_filtered_tuned_metrics.json`
- 기술 보고서: `docs/model_technical_report.md`
- 운영 spec: `docs/트랙2_production_통합_spec_20260507.md` (트랙 2 운영 spec, 트랙 1 baseline path 와 통합)
- Track 2 lessons: `docs/progressive_sampling_phase0_freeze_20260507.md` (governance reference)
- Methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md`
- Deviation log: `docs/methodology_deviation_log.md`
