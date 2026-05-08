# 트랙 1 운영 artifact 재현 (B-2) — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 운영 트랙 1 (`integrated_v3_filtered_tuned`) 의 **reported metric 재현 가능성** 검증 — Lane 1 의 "operational pipeline 재현" 단계
> **Decision binding**: ❌ **X** — Cycle 1 (cold validation) 의 verdict 변경 근거 X / 운영 pipeline reproducibility 확인 만
> **사전 자문**: 코덱스 (B-2 → B-3 순서 권고 / 본 cycle 의 reproducibility 우선)

> ⚠️ **본 cycle 의 scope 명시**:
> - **B-2 (본 cycle)**: 운영 reported 38.3% (calibrated cold MdAPE) 의 재현 — 같은 데이터 / 같은 split / 같은 hyperparameter / 같은 calibration → 같은 결과 가 나오는가
> - **B-3 (조건부 후속)**: B-2 PASS 시, **새 split (Random LAO + Time-split)** 를 운영 artifact 에 적용 — Cycle 1 의 supportive evidence 강화 (decision-binding 여부 = 별도 prereg)
> - 본 cycle = B-2 만 / B-3 는 별도 prereg cycle

## 1. Goal

운영 트랙 1 의 reported 38.3% (CatBoost calibrated cold MdAPE / GroupKFold) 를 동일 환경에서 재현 가능한가?

**Hypothesis** (재현 PASS 조건):
- 재현 cold baseline MdAPE ≈ 39.4% (operational reported, ±1%p tolerance)
- 재현 cold calibrated MdAPE ≈ 38.3% (operational reported, ±1%p tolerance)
- 재현 N = 28,376 행 (artsy 7,289 + saatchi 21,087)
- 재현 cold cell breakdown (artsy_gallery 868 / artsy_online 6,421 / saatchi_online 21,087)

## 2. Data freeze

### 2.1 Source

| 파일 | 경로 | row 수 (raw) |
|---|---|---|
| Artsy primary market | `data/primary_market_dataset.parquet` | 7,640 |
| Saatchi cleaned | `data/saatchi_cleaned.parquet` | 21,721 |

### 2.2 통합 + filter rule (operational `train_primary_market_v3_filtered.py:68` `load_data()` 정확히 동일)

1. 두 parquet 읽음
2. `source` 컬럼 보장 (artsy/saatchi)
3. CB_FEATURES 호환 컬럼 보강 (`ho_price_level`, `medium_price_level`, `profile_completeness`, `ln_area`, `has_birth_year`, `support_factor`, `ho_x_support`)
4. 공통 컬럼만 유지 (`[c for c in artsy.columns if c in saatchi.columns]`)
5. `pd.concat([artsy[common], saatchi[common]], ignore_index=True)`
6. **`is_excluded_for_training == 0` filter** (operational `train_primary_market_v3_filtered.py:395`)

**기대 결과**: 28,376 행 / 1,551 artist (operational reported `_metrics.json` `data` 필드 의 "28376 = filtered from 29361 (excluded 985)" 정합)

### 2.3 Feature spec freeze (operational 32 features)

| 출처 | 컬럼 |
|---|---|
| `_best_params.json`, `_metrics.json` | "features": 32 |
| `src/visionai/price_engine/api/primary_feature_builder.py` `CB_FEATURES` | (32 컬럼 list) |

본 B-2 cycle = 운영 의 `CB_FEATURES` 32 컬럼 정확히 동일 사용 (subset 또는 변경 X).

## 3. Method

### 3.1 GroupKFold (operational `train_primary_market_v3_filtered.py:161` `cv_groupkfold()`)

| 항목 | 값 |
|---|---|
| Split | `GroupKFold(n_splits=5)` (operational default) |
| Group key | `artist_slug` |
| Loss | RMSE on log target (`ln_price`) |
| Model | CatBoost (single model — main metric path) |
| Hyperparameters | operational `_best_params.json` 의 catboost block 정확 적용 (iterations=1000, learning_rate=0.0953, depth=8, l2_leaf_reg=1.6306, bagging_temperature=0.1818) |
| Cat features | `CAT_FEATURES` (operational 정의) |
| Random seed | operational training seed (코드 inspection 후 freeze) |

### 3.2 Source-cell calibration (operational `_source_calibration.json` factor 정확 적용)

| Cell | Cold factor (applied) |
|---|---|
| `artsy_gallery` | 1.0 (skipped_due_to_regression) |
| `artsy_online` | 0.9425943416620021 |
| `saatchi_online` | 0.9568847727800011 |

**Cell 결정 rule** (operational JSON `cells_definition`): `is_krw == 1 → target_market='gallery'`, else `'online'`. Cell key = `f"{source}_{target_market}"`.

### 3.3 Cold definition (operational)

operational `_warm_artists.json` (warm artist list, 작가 작품수 ≥ 5) 와 비교 — warm 작가 = 930명. 본 B-2 의 cold/warm 영역 = operational definition 정확 동일.

> **Codex Q (해소 필요)**: operational `_metrics.json` 의 "cold_overall n=28,376 (전체)" 와 "warm_overall n=27,062 (warm slice 만)" 의 정의 = GroupKFold 의 모든 fold (cold) vs KFold warm slice (warm) → 본 reproduction 도 같은 정의 적용 의무.

## 4. Primary metric

| Metric | 영역 | Operational reported | Reproduction tolerance |
|---|---|---|---|
| **GroupKFold cold MdAPE (CatBoost baseline)** | n=28,376 | **39.38%** (`_source_calibration.json` `cold_overall.baseline_mdape`) | ±1.0%p |
| **GroupKFold cold MdAPE (CatBoost calibrated cross-fit guarded)** | n=28,376 | **38.29%** (`_source_calibration.json` `cold_overall.calibrated_mdape_cross_fit_guarded`) | ±1.0%p |
| GroupKFold cold cell N (artsy_gallery / artsy_online / saatchi_online) | breakdown | 868 / 6,421 / 21,087 | exact |
| Total N | full | 28,376 | exact |

Secondary (sanity check):
- GroupKFold cold W30 ≈ 39.8%
- GroupKFold cold W50 ≈ 59.8%
- ratio ≈ 1.31

## 5. Decision binding

❌ **본 cycle = decision-binding X**:
- 본 cycle = 운영 pipeline 재현 가능성 의 reproducibility 확인 만
- Cycle 1 (cold validation) 의 FAIL verdict 변경 근거 X (Cycle 1 = 트랙 2 의 baseline 24.07% 대비 cold validation)
- 본 결과 = 운영 환경 의 reproducibility 만 확인 (PASS = 운영 pipeline 정상, FAIL = environment / dependency 변경 점검 의무)
- B-3 (Random LAO + Time-split 운영 artifact 적용) = 별도 prereg cycle

## 6. PASS / FAIL 기준

### 6.1 PASS

모든 다음 조건 충족 시:
- ✅ Total N = 28,376 (exact)
- ✅ Cell N (artsy_gallery / artsy_online / saatchi_online) = 868 / 6,421 / 21,087 (exact)
- ✅ cold baseline MdAPE ∈ [38.4, 40.4] (39.38 ± 1.0)
- ✅ cold calibrated cross-fit guarded MdAPE ∈ [37.3, 39.3] (38.29 ± 1.0)

### 6.2 FAIL

위 중 하나라도 미충족 시:
- N mismatch → 데이터 source / filter rule 변경 점검 (예: parquet 의 `is_excluded_for_training` 컬럼 변경 / 신규 row 추가 / 누락)
- MdAPE mismatch → CatBoost 라이브러리 버전 / 환경 변경 / random seed 영향 점검
- Cell N mismatch → `is_krw` 정의 변경 / `source` 컬럼 영향 점검

FAIL 시 = 운영 pipeline 의 reproducibility 결손 — 별도 디버깅 cycle 의무 (본 prereg 미포함).

## 7. Bootstrap CI (옵션 / not primary)

operational `_source_calibration.json` 의 reported MdAPE 는 point estimate 만 — CI 미포함. 본 reproduction 도 point estimate 만 1차 비교. Cluster bootstrap CI (n_boot=2000) = optional secondary (B-3 cycle 의 main analysis 영역).

## 8. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ 재현 코드 작성 (`experiments/structural_v1/track1_artifact_reproduction_b2.py`)
   - operational `load_data()` 그대로 (또는 동일 spec re-implement)
   - operational `_best_params.json` 의 catboost block load
   - GroupKFold(5) re-run
   - Cell-by-cell calibration factor 적용 (cold_factors)
   - cold MdAPE / W30 / W50 / cell N 계산
3. ⏳ 실행 결과 → `experiments/structural_v1/results/track1_artifact_reproduction_b2.json`
4. ⏳ 결과 보고서 작성 (PASS / FAIL 명시 + Hypothesis 충족 / 미충족 영역)
5. ⏳ 결과 보고서 코덱스 사후 검수
6. ⏳ PR 작성 + merge

## 9. 운영 reproducibility 시 의 가치

✅ **PASS 시**: 운영 pipeline 의 reproducibility 확인 — B-3 cycle 의 prerequisite 충족 / Cycle 1 의 supportive evidence 강화 (Lane 1 진입 가능)

✅ **FAIL 시**: 운영 pipeline 의 environment / dependency 변경 의 detection — 별도 디버깅 cycle 의무 (운영 의사결정 영향 가능 영역)

❌ **본 cycle 의 결과 = Cycle 1 (cold validation) 의 verdict 변경 근거 X**

## 10. 후속 cycle (B-3, 조건부)

B-2 PASS 시 후속 (별도 prereg):
- 운영 artifact (`integrated_v3_filtered_tuned_*.cbm/.json`) 에 **새 split (Random LAO 80/20 + Time-split 2024+)** 적용
- Cycle 1 의 트랙 2 결과 (Random LAO cold 36.18% / Time-split cold 43.15%) 와 동일 모집단 / 동일 split 의 트랙 1 운영 artifact 결과 비교
- decision-binding 여부 = B-3 prereg 의 별도 정의 영역

## 11. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| B-2 → B-3 사전 자문 (2026-05-08) | B-2 (reproducibility) → B-3 (new split) 순서 권고 / B-2 의 28,376 행 + GroupKFold + calibrated CatBoost 가 main metric path |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
