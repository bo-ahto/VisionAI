# 트랙 1 운영 artifact 재현 (B-2) — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 운영 트랙 1 (`integrated_v3_filtered_tuned`) 의 **reported metric reproducibility gate** — Lane 1 (decision-grade artifact) 의 prerequisite 충족 여부 확인
> **Decision binding**: ❌ **X** — Cycle 1 verdict / model validity / efficacy claim 갱신 X / artifact integrity gate 통과 의미 만
> **사전 자문**: 코덱스 (B-2 → B-3 순서 권고)

> ⚠️ **본 cycle 의 scope 명시**:
> - **B-2 (본 cycle)**: 운영 reported metric 의 재현 — 같은 데이터 / 같은 split / 같은 hyperparameter / 같은 calibration / 같은 환경 → 사실상 동일 결과 가 나오는가
> - **B-3 (별도 prereg cycle)**: B-2 PASS 후 의 **새 split (Random LAO + Time-split)** 운영 artifact 적용 — 본 prereg 미포함
> - 본 cycle = B-2 만 / B-3 는 별도 prereg

## 1. Goal

운영 트랙 1 의 reported metric (CatBoost calibrated cold MdAPE / GroupKFold) 가 동일 환경에서 사실상 동일 재현 되는가?

**Hypothesis** (PASS 조건 / §6 의 PASS 기준 과 통일):
- Total N = 28,376 (exact)
- Cell N (artsy_gallery / artsy_online / saatchi_online) = 868 / 6,421 / 21,087 (exact)
- 재현 cold baseline MdAPE ∈ [39.18, 39.58] (operational 39.38 ± 0.20)
- 재현 cold calibrated cross-fit guarded MdAPE ∈ [38.09, 38.49] (operational 38.29 ± 0.20)

> **Tolerance 정량적 근거**: 본 cycle = **`thread_count=1` freeze (§3.1)** 의 fully deterministic 환경. 같은 random_seed=42 / 같은 dataset / 같은 hyperparameter 에서 CatBoost 1.2.10 single-thread 는 deterministic 보장 (multi-thread reduction order 비결정성 제거). 기대 결과 = operational reported 와 의 차이 ≤ 0.05%p (numerical precision floor). **±0.20%p tolerance = operational artifact 가 multi-thread 로 학습 됐을 가능성 의 thread reduction-order drift 의 보수적 추가 margin**. 실제 차이 가 ±0.20%p 초과 시 = environment / library version drift 의 detection 의무 / FAIL 처리 ([설명 가능 차이] vs [reproducibility 결손] 의 경계).

## 2. Data freeze

### 2.1 Source files (SHA-256 frozen)

| 파일 | 경로 | row 수 (raw) | SHA-256 |
|---|---|---|---|
| Artsy primary market | `data/primary_market_dataset.parquet` | 7,640 | `746eb0823124c4156b62d038fa3a26d32208143a543ef54d206ff9f462445c0e` |
| Saatchi cleaned | `data/saatchi_cleaned.parquet` | 21,721 | `625dce88e78d311d4cd315646d44d794207c6743dbf97fafdd2f7e38a9388870` |

### 2.2 통합 + filter rule (단계별 row 수 기대값)

operational `train_primary_market_v3_filtered.py:68` `load_data()` + `:395` filter 정확 동일:

| 단계 | 기대 row 수 |
|---|---|
| 1. Artsy parquet read | 7,640 |
| 2. Saatchi parquet read | 21,721 |
| 3. Common-column alignment (`[c for c in artsy.columns if c in saatchi.columns]`) | 57 columns |
| 4. `pd.concat([artsy[common], saatchi[common]], ignore_index=True)` | 29,361 |
| 5. `df[df["is_excluded_for_training"] == 0]` | **28,376** ⭐ |

본 단계별 row 수 = 본 prereg 작성 시점 (`2026-05-08`) 의 운영 데이터 의 실측치 (위 SHA-256 frozen file 의 결과).

### 2.3 Operational artifact files (SHA-256 frozen)

| 파일 | SHA-256 |
|---|---|
| `_best_params.json` | `4582840c08261b0e065130e0450379d2de580b134ed43e724298b65c3563fc03` |
| `_source_calibration.json` | `43f2417c1266c406d9e3dea427f2277149f356cf1c13a44fb63d2db40a21879d` |
| `_warm_artists.json` | `284e65a73e4fe88784ff63207fd75d24eb46e96414a5d8f33db0172028eb6e51` |

### 2.4 Feature spec (32 features, operational `CB_FEATURES`)

본 B-2 cycle = `src/visionai/price_engine/api/primary_feature_builder.py` 의 `CB_FEATURES` 32 컬럼 정확 동일 사용. subset / 변경 X.

## 3. Method

### 3.1 Environment freeze

| 항목 | 값 |
|---|---|
| Python | 3.14.2 |
| pandas | 3.0.1 |
| numpy | 2.4.3 |
| catboost | 1.2.10 |
| `random_seed` | 42 (operational `train_primary_market_v3_filtered.py:177`) |
| GPU | 미사용 (CPU only) |
| `thread_count` | **1 (deterministic freeze)** — multi-thread reduction order 비결정성 제거 / 같은 머신 재실행 시 fully deterministic (operational artifact 와 의 차이 가 thread drift 영역 인지 vs 재현성 결손 인지 의 경계 명확화) |
| Git commit (재현 시점) | 본 cycle PR merge commit SHA (실행 시 기록 의무) |

### 3.2 GroupKFold (operational `cv_groupkfold()` 정확 동일)

| 항목 | 값 |
|---|---|
| `n_splits` | 5 (operational `train_primary_market_v3_filtered.py:165`) |
| Group key | `artist_slug` |
| Loss | RMSE on log target (`ln_price`) |
| Model | CatBoost (single model — main metric path) |
| Hyperparameters | operational `_best_params.json` 의 `catboost` block 정확 적용 (iterations=1000 / learning_rate=0.0953 / depth=8 / l2_leaf_reg=1.6306 / bagging_temperature=0.1818) |
| Cat features | operational `CAT_FEATURES` 정의 (`primary_feature_builder.py`) |
| `verbose` | 0 |
| `allow_writing_files` | False |
| Eval set | None (operational의 fold-internal early stopping 미사용) |

### 3.3 Cold/warm 정의 (primary analysis = cold / warm = out of scope)

**본 B-2 cycle 의 primary analysis 영역 = GroupKFold OOF 전체 28,376 행 의 cold MdAPE**.

operational `_metrics.json` 의 `groupkfold` 영역 의 모든 행 = artist 단위 holdout 이므로 정의상 cold 영역. 본 cycle = 위 영역 의 reproducibility 확인 만.

**Warm metric (KFold warm slice 27,062 행) = out of scope** — 본 cycle 의 PASS / FAIL 기준 미적용 (별도 cycle 의 영역).

### 3.4 Source-cell calibration (operational `calibrate_source_bias.py:_cross_fit_eval()` 정확 재현)

operational cross-fit guarded calibration 의 알고리즘:

1. **OOF prediction 생성**: GroupKFold 5-fold 에서 각 fold 의 held-out 의 prediction (`pred_price`) + `fold_id` 기록 (operational `calibrate_source_bias.py:84` `_cold_oof_with_fold_id()`)
2. **Cell key 결정**: 각 row 의 `cell = f"{source}_{target_market}"` 계산
   - `target_market = 'gallery' if is_krw == 1 else 'online'`
   - `is_krw` 결측/비0-1 처리 = operational 코드 의 정확 reproduction (별도 처리 X — operational 도 raw bool/int 전제)
3. **Cross-fit factor 추정**: 각 fold k 마다:
   - `train_mask = (fold_ids != k) & (fold_ids >= 0)` 의 row 만 사용
   - 각 cell 마다 `factor_cell = median(actual_price / pred_price)` 추정 (operational `calibrate_source_bias.py:_cross_fit_eval()`)
4. **Calibrated prediction 적용**: held-out fold k 의 row i 마다
   - `cell_i` 의 factor 가 train fold 에서 추정 된 값
   - `calibrated_pred[i] = pred_price[i] * factor_cell_i`
5. **Per-cell guard (cross-fit 악화 cell skip)**: cell 별
   - `applied_factor = 1.0 if calibrated_mdape_cell > baseline_mdape_cell else proposed_factor`
   - operational `_source_calibration.json` 의 `cold_breakdown.{cell}.skipped_due_to_regression` 와 정확 동일 결과 의무
6. **Final guarded MdAPE**: applied_factor 가 1.0 인 cell 은 baseline_pred 로 revert / 그 외 cell 은 calibrated_pred 사용 → final overall MdAPE

> **Operational `_source_calibration.json` 의 reported `applied_factor`**:
> - artsy_gallery: 1.0 (skipped — cross-fit 시 악화)
> - artsy_online: 0.9425943416620021 (적용)
> - saatchi_online: 0.9568847727800011 (적용)
>
> 본 reproduction 도 위 applied_factor 가 정확 동일 결과 도출 의무 (PASS 조건 의 implicit 영역).

> **Missing/unknown cell 처리**: operational 시점 데이터 의 cell = {artsy_gallery, artsy_online, saatchi_online} 3 종 만 존재. 본 reproduction 의 28,376 행 도 위 3 cell 만 — 다른 cell 발생 시 = data drift detection 의무 (PASS 조건 위반 / FAIL 처리).

## 4. PASS / FAIL 기준 (Primary)

### 4.1 PASS (모두 충족)

- ✅ Total N = 28,376 (exact)
- ✅ Cell N (artsy_gallery / artsy_online / saatchi_online) = 868 / 6,421 / 21,087 (exact)
- ✅ 재현 cold baseline MdAPE ∈ [39.18, 39.58]
- ✅ 재현 cold calibrated cross-fit guarded MdAPE ∈ [38.09, 38.49]
- ✅ Per-cell `applied_factor` direction (skipped vs applied) 가 operational 과 정확 동일:
  - artsy_gallery: `skipped_due_to_regression == True` (factor=1.0)
  - artsy_online: `skipped_due_to_regression == False` (factor ∈ [0.9376, 0.9476], operational 0.9426 ± 0.005)
  - saatchi_online: `skipped_due_to_regression == False` (factor ∈ [0.9519, 0.9619], operational 0.9569 ± 0.005)
  - **Tolerance ±0.005 근거**: median(actual/pred) 의 thread_count drift 영역 의 보수적 영역 (median 은 ranking-based 으로 robust 하지만 boundary row 이동 가능)

### 4.2 FAIL

위 중 하나라도 미충족 → reproducibility 결손. FAIL 시 는 operational pipeline 의 environment / dependency / data drift 의 detection — 별도 디버깅 cycle 의무 (본 prereg 미포함).

### 4.3 Secondary metric (PASS / FAIL 판정 불사용 / sanity check 만)

operational reported sanity 비교 (판정 영향 X):
- GroupKFold cold W30 ≈ 39.8%
- GroupKFold cold W50 ≈ 59.8%
- ratio ≈ 1.31

본 영역 = 결과 보고 시 의 sanity check 자료 만 / PASS / FAIL 판정 미적용.

## 5. Decision binding

❌ **본 cycle = decision-binding X / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | 변경 X |
| 트랙 1 model validity / efficacy claim | 갱신 X |
| 트랙 2 model validity / efficacy claim | 갱신 X |
| 운영 채택 결정 | 영향 X |
| 외부 보고서 | 본 cycle 결과 미반영 영역 |

**B-2 PASS 의 의미 = 운영 artifact integrity / reproducibility gate 통과 만**. B-3 cycle (Random LAO + Time-split 운영 artifact 적용) 의 운영 prerequisite 만 / 분석적 증거 업데이트 X.

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ 재현 코드 작성 (`experiments/structural_v1/track1_artifact_reproduction_b2.py`)
   - operational `load_data()` 동일 spec re-implement
   - operational `_best_params.json` 의 catboost block load
   - GroupKFold(5) re-run
   - cross-fit guarded calibration 적용 (operational `_cross_fit_eval()` 알고리즘 동일)
   - cold MdAPE / W30 / W50 / cell N 계산
3. ⏳ 실행 결과 → `experiments/structural_v1/results/track1_artifact_reproduction_b2.json`
4. ⏳ 결과 보고서 작성 (PASS / FAIL 명시 + Hypothesis 충족 / 미충족 영역 + per-cell applied_factor 비교)
5. ⏳ 결과 보고서 코덱스 사후 검수
6. ⏳ PR 작성 + merge

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| B-2 → B-3 사전 자문 (2026-05-08) | B-2 (reproducibility) → B-3 (new split) 순서 권고 / 본 cycle 의 28,376 행 + GroupKFold + calibrated CatBoost 가 main metric path |
| 본 prereg round 1 사후 검수 (2026-05-08, NEEDS FIX) | P0×1 (§9 supportive evidence 표현 오염) / P1×5 (cold/warm 정의 미해결, env freeze 결손, tolerance 근거 결손, calibration 절차 미완성, 데이터 hash 결손) / P2×4 (Hypothesis 통일, 단계별 row 수, secondary metric 무관 명시, B-3 prerequisite 명시) |
| 본 prereg round 2 사후 검수 (2026-05-08, NEEDS FIX) | P1×2 (thread_count freeze 결손 / tolerance 근거 방어 불가능) — round 2 fix: thread_count=1 deterministic freeze + tolerance 근거 재서술 (operational multi-thread → 본 single-thread drift 의 ±0.20%p 보수적 margin) + per-cell factor exact → ±0.005 tolerance (median robustness) |
| 본 prereg round 3 사후 검수 (예정) | round 2 fix commit 직후 |
