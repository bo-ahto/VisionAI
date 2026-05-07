# Track 1 Phase 0 — Drift Fix Amendment Memo (1-page)

> **작성일**: 2026-05-07 (Phase 0 freeze 의 baseline contract amendment)
> **연계**: `docs/track1_phase0_freeze_20260507.md` (Phase 0 mini-prereg) / `docs/track1_stage1_results_20260507.md` v3 (Stage 1 audit, 코덱스 audit 1 통합)
> **사용자 결정**: Option A (drift fix 우선 + baseline 재산출) 진행
> **코덱스 권고**: 별도 mini-prereg 불필요 / 짧은 amendment memo 만 필요 (baseline contract 변경 사전 freeze)

> ⚠️ **본 amendment 의 본질**: Phase 0 §1.5 stop rule ("Stage 1 integrity 위험 신호 1+건 발견 시 우선 fix → re-run") 정상 적용. governance 위반 X / 새 cycle X / **baseline 재산출 시 명시적 contract change 사전 freeze**.

## 1. Fix Set (코덱스 권고 — A.1, 7 drift + 2 dead 정리)

### 1.1 제거 대상 9 features (32 → 23)

**Severe train/serve drift (7 features)** — 서빙 시 hardcoded constant / 학습 actual distribution 과 mismatch:
- `is_unique` (서빙 1 always / 학습 28,340/28,376 = 1)
- `is_edition` (서빙 0 always / 학습 34/28,376 = 1)
- `has_depth` (서빙 0 always / 학습 22,839/28,376 = 1) — **매우 severe**
- `gallery_city_count` (서빙 1 always / 학습 multi-city 분포)
- `has_seoul` (서빙 0 always / 학습 6,414 = Seoul) — **매우 severe**
- `has_international` (서빙 0 always / 학습 23,394 = international) — **매우 severe**
- `attribution_class` (서빙 "Unique" always / 학습 'Unique' 28,340 / 'Limited edition' 34)

**Dead features (2 features)** — 학습도 서빙도 모두 0:
- `ho_price_level` (학습 28,376/28,376 = 0.0)
- `medium_price_level` (학습 28,376/28,376 = 0.0)

### 1.2 유지 대상 23 features (코덱스 카테고리 D — no serving-side red flag found)

`ho` / `ho_power` / `ln_ho` / `area_cm2` / `ln_area` / `aspect_ratio` / `is_small` / `support_factor` / `ho_x_support` / `artist_birth_year` / `has_birth_year` / `career_stage` / `ln_followers` / `artist_total_works` / `for_sale_ratio` / `profile_completeness` / `gallery_tier` / `is_krw` / `support_type` / `medium_category` / `gallery_type` / `price_currency` / `source`

## 2. Baseline 재산출 spec freeze

| 항목 | 값 |
|---|---|
| New variant ID | `v3_filtered_tuned_drift_fix_v1` |
| Features | **23** (위 §1.2) |
| Models | CatBoost + XGBoost (운영 spec 동일 hyperparameters, `integrated_v3_filtered_tuned_best_params.json` 그대로) |
| Training data | 28,376 rows / 1,551 artists (Phase 0 §1.2 그대로) |
| Evaluation | GroupKFold cold-start (Phase 0 §1.4 primary metric) + Source slice (Artsy / Saatchi 분리) |
| Baseline 비교 대상 | `v3_filtered_tuned` 32f (현재 서빙 / Phase 0 §1.1 anchor) |
| Calibration 재산출 | `source_calibration.json` 재계산 의무 (cell 별 multiplicative factor) |

## 3. 평가 protocol (코덱스 권고)

### 3.1 평가 split (필수 명시 — 코덱스 P1)
- **Overall** GroupKFold cold-start MdAPE
- **Artsy** split (cold)
- **Saatchi** split (cold)
- **Warm KFold** non-regression (Phase 0 §1.4 hard gate 3)

### 3.2 평가 결과 보고 형식

| Variant | Overall | Artsy | Saatchi | Warm KFold |
|---|---|---|---|---|
| v3_filtered_tuned (32f, baseline) | 39.4% (CB) / 39.1% (XGB) | (재산출) | (재산출) | (재산출) |
| v3_filtered_tuned_drift_fix_v1 (23f) | (재산출) | (재산출) | (재산출) | (재산출) |
| Δ | (계산) | (계산) | (계산) | (계산) |

### 3.3 평가 결과 해석 (Phase 0 §1.4 hard gates 적용)
- **Primary**: Δ Overall ≤ -0.7%p (improvement) / 또는 within noise → drift 가 model accuracy 에 큰 영향 X 입증
- **Hard gate 1**: Δ_low (cold) ≤ 0%p (저가 segment 악화 금지)
- **Hard gate 2**: Source 비대칭 — Artsy / Saatchi 한쪽만 개선 + 다른 쪽 큰 악화 = FAIL
- **Hard gate 3**: Warm KFold non-regression
- **Confirmatory**: Stage 4 locked holdout 1회만 (본 amendment 단독 X)

> **본 amendment 단독 = 운영 spec 변경 trigger X** (Stage 4 holdout + shadow / staged rollout 후만)

## 4. 본 amendment 의 governance 위치

- Phase 0 freeze 의 stop rule §1.5 정상 적용 (governance 위반 X)
- baseline contract 변경 사전 명시 (deviation log entry 의무)
- Stage 1B / Stage 2 진입 시 새 baseline (23f) 사용
- 본 amendment = exploratory + decision-binding 분리 그대로 적용

## 5. 다음 단계

1. ✅ Amendment memo — 본 commit
2. ⏳ **Audit 4 진행**: `v3_filtered_tuned_drift_fix_v1` (23f) OOF 재학습 + GroupKFold cold-start + Artsy / Saatchi split + Warm KFold
3. ⏳ Audit 4 결과 보고서 + 코덱스 사후 검수
4. (조건부) Stage 1B 진입 (importance + stability) — drift fix baseline 기준
5. ⏳ (다음 cycle) Stage 2 → Stage 3 → Stage 4 confirmatory holdout

## 6. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 누적 | P0×17 + P1×80 + P2×40 |
| Track 1 사전 자문 (2026-05-07) | 조건부 GO + Phase 0 freeze 우선 + 4 P0 |
| Stage 1 사후 검수 (2026-05-07) | Option A first 권고 + P0×1 (수치 단일화) + P1 다수 |
| **Option A drift fix 사전 자문 (2026-05-07)** | mini-prereg 불필요 / amendment memo 필요 / 7 drift + 2 dead 재분류 / A.1 (학습 측 제거) 권고 / Audit 4 = 단일 candidate OOF rerun |

## 7. 참조

- Phase 0 freeze: `docs/track1_phase0_freeze_20260507.md`
- Stage 1 results v3: `docs/track1_stage1_results_20260507.md`
- 운영 코드: `src/visionai/price_engine/api/primary_feature_builder.py:228-272`
- 학습 코드: `scripts/prepare_primary_market_dataset.py:262` / `scripts/prepare_saatchi_dataset.py:283`
- Methodology pipeline / Deviation log
