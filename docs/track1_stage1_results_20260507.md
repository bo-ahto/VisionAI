# Track 1 — Stage 1 Feature Integrity Audit Results

> **작성일**: 2026-05-07
> **Phase 0 freeze**: `docs/track1_phase0_freeze_20260507.md` (mini-prereg)
> **본 단계 범위 (코덱스)**: feature integrity recheck — 코드 inspection 기반 심각한 drift / proxy 위험 신호 식별. **탈락 후보 식별만 / 채택 결정 X / Stage 1B (importance + stability) 진입 전 fix 우선순위**.

> ⚠️ **본 결과 = exploratory diagnostic only** — Phase 0 freeze §1.8 decision-binding 분리 적용. 운영 spec 변경 단독 trigger X.

## 0. 한 줄 요약

> **Stage 1 integrity audit 핵심 finding**: 32 features 중 **9 features 학습-서빙 drift 위험 (28%)** — serving code inspection 기준 hardcoded constant / placeholder. 본 위험은 reported offline cold-start metric (39.4% raw CatBoost / 38.3% calibrated production-cold reference) 가 **actual serving behavior 를 충실히 대변하지 않을 위험** 시사 (코덱스 P1 — 단정 X, 위험 표현). **Stage 1B 진입 전 학습-서빙 정합성 fix 우선** 권고.
>
> **이미 fix 이력 (코덱스 4차 / 14차 P1)**: work_age / career_age / vintage_premium / freshness_discount / gallery_name 등 5+ features 이미 drift 위험으로 제거됨 — 본 audit 의 잔존 위험 = 후속 fix 영역.

## 1. 위험 신호 분류 (코덱스 P0 #4)

### 1.1 카테고리 A: 서빙 시 hardcoded constant (severe drift, 잔존)

> **출처**: `src/visionai/price_engine/api/primary_feature_builder.py:228-272` (`build_features` 함수)

| Feature | 학습 데이터 (추정) | 서빙 hardcode | Drift 평가 |
|---|---|---|---|
| `is_unique` | actual binary (작품별 unique vs edition) | `1` (always) | **severe** — 서빙 시 모든 작품 = unique 처리, 학습 vs 서빙 distribution mismatch |
| `is_edition` | actual binary (edition 작품 0/1) | `0` (always) | **severe** — `is_unique` 와 함께 작품 attribution 신호 학습-서빙 단절 |
| `has_depth` | actual binary (3D 작품 0/1) | `0` (always) | **severe** — 3D 작품 (조각 등) 학습 시 informative, 서빙 시 모든 작품 = 0 |
| `gallery_city_count` | actual count (1-N) | `1` (always) | **severe** — multi-city 갤러리 학습 정보 서빙 X |
| `has_seoul` | actual binary | `0` (always) | **severe** |
| `has_international` | actual binary | `0` (always) | **severe** |
| `attribution_class` | actual category (Unique / Limited Edition / etc) | `"Unique"` (always) | **severe** — `is_unique` / `is_edition` 와 동일 drift category |

### 1.2 카테고리 B: 학습 시 group statistic, 서빙 시 placeholder (severe drift, 잔존)

| Feature | 학습 (추정) | 서빙 hardcode | Drift 평가 |
|---|---|---|---|
| `ho_price_level` | (직접 대조 X — 학습 시 group statistic 추정) | `0.0` (placeholder) | **severe serving-side placeholder, likely train/serve drift** (코덱스 P1 보수 표현) |
| `medium_price_level` | (직접 대조 X — 학습 시 group statistic 추정) | `0.0` (placeholder) | **severe serving-side placeholder, likely train/serve drift** |

### 1.3 카테고리 C: 이미 제거된 drift features (코덱스 fix 이력)

| Feature | 제거 사유 | Codex review 차수 |
|---|---|---|
| `work_age` | 서빙=0 드리프트 | 4차 P1 |
| `career_age` | 서빙=0 드리프트 | 4차 P1 |
| `vintage_premium` | 서빙=0 드리프트 | 미상 (코드 주석) |
| `freshness_discount` | 서빙=0 드리프트 | 미상 (코드 주석) |
| `gallery_name` | drift / privacy / cardinality | 14차 P1 |
| `RATIO_CORRECTION` (target_market='online' -0.075) | source-specific median-ratio calibration 으로 흡수 | Codex P1 (line 18-21) |

### 1.4 카테고리 D: no serving-side red flag found (코덱스 P1 — "healthy" 단정 회피)

| Feature | 평가 |
|---|---|
| `ho` / `ho_power` / `ln_ho` / `area_cm2` / `ln_area` / `aspect_ratio` / `is_small` | 학습-서빙 동일 derivation (작품 size — actual measurement) |
| `support_factor` / `ho_x_support` | medium / support 분류 기반 — 학습-서빙 동일 pipeline |
| `artist_birth_year` / `has_birth_year` | actual artist metadata |
| `career_stage` (v2, multi-factor 0-8) | 학습-서빙 동일 함수 (`career_stage_v2_score`) — Codex 보강 후 healthy |
| `ln_followers` / `artist_total_works` / `for_sale_ratio` | actual artist statistics — single snapshot 가정 (트랙 2 와 동일 caveat) |
| `profile_completeness` | actual profile score |
| `gallery_tier` | actual category — 단 `1.gallery_city_count` 와 분리 평가 필요 (gallery_tier 가 city_count 포함하지 않는다면 healthy) |
| `gallery_type` / `medium_category` / `support_type` / `price_currency` / `source` / `is_krw` | actual category / 명확한 derivation |

## 2. 핵심 시사점 (코덱스 framing 톤 — exploratory diagnostic)

### 2.1 본 finding 의 의미 (코덱스 P1 보수 표현)
- **카테고리 A + B 합 = 9 features (32 features 의 28%)** — serving code inspection 기준 hardcoded constant / placeholder
- 이는 reported offline cold-start metric (39.4% raw CatBoost / 38.3% calibrated production-cold reference, `docs/model_technical_report_v2.md:53`) 이 **actual serving behavior 를 충실히 대변하지 않을 위험** 시사
  - 학습 시 informative features 가 서빙 시 무력 → production MdAPE 더 높을 가능성
  - 또는 학습 시 noise 학습 → production 시 reduced noise 로 더 좋을 가능성 (덜 likely)
  - 실제 방향성은 별도 audit (학습 데이터 distribution 비교 / serving log 검증) 필요
- 이미 Codex fix 이력 5+ → drift 인지된 issue / 본 audit 의 잔존 9 features = **다음 fix 후보**

### 2.2 Stage 1B 진입 전 권고 (코덱스)
- **Drift fix 우선** vs **Stage 1B (importance + stability) 평행 진행** 결정 필요
- Drift fix 우선 시:
  - 카테고리 A (7) + 카테고리 B (2) features 의 학습-서빙 정합성 평가
  - 옵션: (a) 서빙 시 actual value 추출 가능한 features → 학습 그대로 유지 / (b) 추출 불가능 → 학습에서도 제거 (Codex 4차 패턴 따라)
  - **가장 정직한 path**: 추출 불가 features = 학습 dataset 에서 제거 후 baseline metric 재산출
- Stage 1B 평행 진행 시:
  - 현재 baseline 그대로 importance / stability 평가
  - drift features 의 importance 가 높게 나오면 Stage 1B 결과 자체 unreliable (학습 noise)
  - drift features 의 importance 가 낮으면 fix 후 재평가 부담 X

### 2.3 사용자 결정 영역
- **Option A: Drift fix 우선 + baseline 재산출** (코덱스 권고)
  - 카테고리 A + B 9 features = 학습 dataset 에서도 제거 또는 actual value 추출
  - baseline 재학습 + GroupKFold MdAPE 재산출
  - 새 baseline 기준으로 Stage 1B 진입
- **Option B: 평행 진행** (시간 절약)
  - 현재 baseline 으로 Stage 1B 진입
  - drift features 의 importance 결과 후 fix 결정
  - Stage 1B 결과 자체가 drift features 영향 받을 수 있음 (caveat 강함)
- **Option C: 별도 cycle 분리**
  - Drift fix = 별도 prereg + 별도 cycle (트랙 1 운영 영향 큼 — 신중한 변경)
  - Stage 1B 는 본 cycle 의 다음 stage 로 진행 (drift caveat 인지)

### 2.4 코덱스 사후 검수 권고 (Option A 우선 / B/C 동등 대안 X)

> **코덱스 P0 권고**: Option B (평행 진행) 와 Option C (분리 cycle) 는 가능하나 **동등 대안 아님**. 권고 = **Option A (drift fix 우선 + baseline 재산출)**.

**권고 추가 audit (Option A 진행 시)**:
1. Training dataset reconstruction → 9 features 실제 분포 확인
2. Train-side feature generation code ↔ serve-side contract 1:1 매핑 검증
3. 최근 serving log 샘플에서 9 features 실제 입력값 분포
4. OOF 에서 "9 features 제거 전 / 후" 재산출 → metric 민감도 측정

## 3. 운영 영향 (코덱스 P0 — decision-binding 분리)

- 본 stage 1 결과 = **exploratory diagnostic only** — 운영 spec 변경 단독 trigger X
- 잠재 drift features 의 학습 dataset 제거 = **별도 confirmatory cycle 필수** (Stage 4 holdout 까지 진행 후 production trigger gate)
- **운영 영향 X (현 시점)**: 운영 spec §1-§16 변경 X / `v3_filtered_tuned` 운영 그대로 유지

## 4. 다음 단계

1. ✅ Stage 1 integrity audit — 본 commit
2. ⏳ **사용자 결정**: Option A (drift fix 우선) / Option B (평행 Stage 1B) / Option C (분리)
3. ⏳ 코덱스 사후 검수
4. (조건부) Stage 1B (importance + stability selection) 진입 또는 drift fix prereg 진입

## 5. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 | P0×16 + P1×72 + P2×38 |
| Track 1 사전 자문 (2026-05-07) | 조건부 GO + Phase 0 freeze 우선 + P0×4 (baseline ambiguity / evaluation redesign / cold-warm gate / **feature integrity recheck**) |
| **Stage 1 결과 검수 (2026-05-07)** | **Option A (drift fix 우선) 권고**. P0 1건 (수치 표기 단일화: 9 features) + P1 다수 (primary threshold 단일 숫자 / "healthy" → "no serving-side red flag found" / drift severity 보수 표현 / 카테고리 B 학습 시 group statistic = 추정만 / 32f = "operational anchor baseline") + P2 (RATIO_CORRECTION 분리 / locked holdout hash 명시) — 본 v2 commit 일괄 반영 |

## 6. 참조

- Phase 0 freeze: `docs/track1_phase0_freeze_20260507.md`
- 운영 코드: `src/visionai/price_engine/api/primary_feature_builder.py:228-272` (`build_features`)
- 운영 코드: `src/visionai/price_engine/api/primary_predictor.py:22-54` (CB_FEATURES_BASE 32)
- Baseline metrics: `model_test_results/integrated_v3_filtered_tuned_metrics.json`
- 기술 보고서: `docs/model_technical_report.md`
- Codex review history: 4차 / 14차 P1 fix 이력 (코드 주석 기반)
