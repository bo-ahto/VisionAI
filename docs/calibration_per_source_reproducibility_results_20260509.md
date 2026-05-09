# Per-source Calibration 재현성 검증 결과 (Reprod cycle / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **Prereg**: `docs/calibration_per_source_reproducibility_prereg_20260509.md` (R3 LGTM)
> **Run**: `scripts/validate_per_source_calibration_reproducibility.py`
> **Results JSON**: `model_test_results/calibration_reproducibility_20260509.json`
> **Holdout indices**: `data/reproducibility_holdout_20260509/{artsy,saatchi}_holdout_indices.json`

## 1. TL;DR

**Verdict (per prereg §3.3)**:
- 전 `load_bearing` cell **FAIL** (artsy cold 2 cells) → **운영 채택 보류**.
- 전 `consistency_only` cell GUARD_OK (artsy warm 2, saatchi cold/warm 2 = 4 cells / guard implementation 정합).

**Procedure 재현성**: 5/6 cell에서 refit factor가 original과 방향 일치 + drift 작음. 단 saatchi cold 1 cell에서 guard 발동 outcome이 full-data와 80%-pool에서 달라짐 (분류는 GUARD_OK, 후술).

**Critical caveat (사전 등록 미언급)**: 본 cycle은 PR1 artifact 그대로 holdout prediction (재학습 X / prereg §2.3 + codex R1 합의). 그 결과 holdout prediction = **artifact 기준 in-sample**. holdout baseline MdAPE (artsy_gallery 3.21 / artsy_online 7.17)이 e3367ed cross-fit OOF baseline (~33)보다 압도적으로 낮음. OOF underprediction 보정 목적의 calibration factor를 in-sample 예측에 적용하면 over-correction → FAIL이 거의 구조적으로 보장됨. 본 FAIL 결과가 실제 deployment value를 직접 반영하는지는 미확정 — Reprod.C codex 사후 검수에서 method 적정성 합의 필요.

## 2. Per-cell 결과

### 2.1 Load_bearing cells (운영 채택 endpoint / Δ_original 기반)

| Cell | n_pool | n_holdout | baseline | cal_orig | Δ_orig | cal_refit | Δ_refit | drift | CI90 (Δ_orig) | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| artsy/cold/artsy_gallery | 502 | 366 | 3.21 | 8.67 | **+5.46pp** | 12.98 | +9.77pp | 0.048 | [+4.84, +6.40] | **FAIL** |
| artsy/cold/artsy_online | 5108 | 1313 | 7.17 | 7.48 | **+0.31pp** | 8.07 | +0.90pp | 0.015 | N/A (large) | **FAIL** |

FAIL 트리거: `Δ_original > 0` (prereg §3.2 / point estimate 단독 FAIL). artsy_gallery는 CI90 상한도 양수 → 통계적으로도 baseline보다 나쁨 보수적 확인. artsy_online은 large cell이라 CI 미산출, point estimate만으로 FAIL.

### 2.2 Consistency_only cells (guard 정합 점검)

| Cell | n_pool | n_holdout | baseline | cal_orig | refit | drift | Decision |
|---|---|---|---|---|---|---|---|
| artsy/warm/artsy_gallery | 639 | 139 | 5.36 | 5.36 | 0.9996 | 0.0004 | GUARD_OK |
| artsy/warm/artsy_online | 4643 | 1182 | 4.92 | 4.92 | 1.0 | 0 | GUARD_OK |
| saatchi/cold/saatchi_online | 17162 | 3925 | 12.14 | 12.14 | 0.923 ⚠️ | 0.081 | GUARD_OK |
| saatchi/warm/saatchi_online | 16367 | 4092 | 7.30 | 7.30 | 0.9985 | 0.0015 | GUARD_OK |

`cal_orig = baseline` (factor=1.0 이므로 calibration 무영향). `consistency_only` 분류 → 운영 채택 결정 X.

⚠️ saatchi/cold: full-data e3367ed에서는 guard 발동 (factor=1.0 fallback / cross-fit unguarded > baseline)이었는데, 80%-pool refit에서는 guard 미발동 (refit factor=0.923 / cross-fit unguarded ≤ baseline). Guard implementation 자체는 정합 (조건이 충족되지 않아 fallback 미발동) → 분류 GUARD_OK 유지. 단 full vs 80% sample size 경계에서 guard outcome이 갈리는 것 확인 — sample-size sensitivity. 운영 영향 X (original=1.0이므로 calibration 미적용 동일).

## 3. Procedure 재현성 진단 (Secondary endpoint)

| Cell | original | refit | drift (≤ log(1.3)=0.262) | 방향 일치 |
|---|---|---|---|---|
| artsy/cold/artsy_gallery | 0.9152 | 0.8721 | 0.0483 ✅ | ✅ (둘 다 <1) |
| artsy/cold/artsy_online | 0.9757 | 0.9608 | 0.0154 ✅ | ✅ (둘 다 <1) |
| artsy/warm/artsy_gallery | 1.0 (guard) | 0.9996 | 0.0004 ✅ | ✅ (≈1.0) |
| artsy/warm/artsy_online | 1.0 (guard) | 1.0 | 0 ✅ | ✅ |
| saatchi/cold/saatchi_online | 1.0 (guard) | 0.9226 | 0.0806 ✅ | ⚠️ guard outcome 변경 |
| saatchi/warm/saatchi_online | 1.0 (guard) | 0.9985 | 0.0015 ✅ | ✅ |

**Procedure 재현성 verdict**: 절차 자체 (cross-fit OOF + 동일 cell key + per-cell guard logic)는 80% sample에서도 안정적으로 작동. drift 모두 임계 이내. 부호 반전 0건. saatchi cold guard outcome 변경은 sample-size boundary 효과로, implementation 결함 X.

## 4. 데이터 분석

### 4.1 In-sample vs OOF baseline 차이 (FAIL 원인 추정)

| Cell | In-sample holdout baseline | e3367ed full cross-fit baseline (참고) | 비율 |
|---|---|---|---|
| artsy/cold/artsy_gallery | 3.21 | ~33 (전체 cold) | ≈ 10× |
| artsy/cold/artsy_online | 7.17 | ~33 | ≈ 5× |
| saatchi/cold/saatchi_online | 12.14 | ~33 | ≈ 3× |

PR1 artifact는 source 전체 데이터 학습 → holdout 행도 학습 데이터에 포함. holdout 위 prediction은 in-sample (모델이 본 적 있는 row 위 예측). In-sample 예측은 OOF 예측보다 systematic bias가 작음. e3367ed의 calibration factor는 OOF underprediction (≈ 8-10% 수준)을 보정하도록 학습됨. 이 factor를 in-sample (이미 거의 정확한 예측)에 적용하면 over-correction → MdAPE 증가.

이는 prereg §6 "i.i.d. 가정" 한계의 실질적 발현이지만, prereg 작성 시 in-sample/OOF 분포 차이의 영향력을 충분히 가시화하지 않음. codex R1 자문에서도 "Not retraining the PR1 .cbm/.json artifact is correct for this question. Retraining would confound base-model variance with calibration reproducibility." 으로 합의됨 — 본 결과로 그 trade-off의 cost가 드러남.

### 4.2 Procedure 재현성은 강함

absolute Δ_original (FAIL 원인)와 별개로, refit factor의 안정성은 매우 강함:
- artsy_gallery: original 0.9152 vs refit 0.8721 (drift 4.8%)
- artsy_online: original 0.9757 vs refit 0.9608 (drift 1.5%)

→ "동일 절차로 80% subset 위에서 factor를 다시 fit해도 거의 같은 값이 나온다"는 의미. e3367ed의 fitting algorithm 자체는 robust.

## 5. 채택 결정 (per prereg §3.3)

**전 load_bearing cell FAIL → 채택 보류** (prereg §3.3 4번째 bullet: "모든 load_bearing cell FAIL → 채택 보류 / 다른 seed·holdout 추가 검증 필요").

### 5.1 권고 (Reprod.C codex 사후 검수 R4 합의)

**Codex R4 verdict (사후 검수)**: LGTM-with-caveat / **View B 지지**. 실행은 prereg 정합 / 결정 logic 정합. 단 본 cycle 결과는 **deployment value의 clean test가 아님** — 본 cycle FAIL은 "이 cycle 한정 운영 binding" 역할이지 "calibration이 OOS value를 갖지 않는다"의 강한 증거 X.

1. **즉시**: e3367ed의 per-source calibration을 운영 mode (on/canary/shadow)에서 활성화 X. default OFF 유지 (prereg + R4 일치).
2. **본 cycle commit**: prereg + results + script + JSON + indices를 그대로 commit. FAIL verdict는 operational binding이지만 deployment value의 정의적 부정은 X — 본 caveat 명시.
3. **확정된 후속 cycle (codex R4 권고)**:
   - **Retrained-artifact + multi-seed cycle**: 각 80% pool로 base artifact 재학습 → pool OOF 위에서 calibration factor 학습 → untouched 20% holdout 위에서 baseline vs calibrated 평가. Multi-seed (split_seed 다중) 도 함께 실행. positive adoption claim은 이 cycle 통과 후에만 가능.
4. **참고 후순위 후보** (R4에서 우선순위 미확정):
   - 운영 shadow logging 활용 (PR2B-prereq.1 `2d3af98` 기반) — 실제 production prediction 위 calibration 효과 누적 측정. 별도 cycle 후보.

### 5.2 운영 unified bundle 영향

- `model_test_results/integrated_v3_filtered_tuned_source_calibration.json` 변경 X (prereg §5 out-of-scope).
- PR2B (commit `c2cc240`) artifact deploy + rollout runbook은 default OFF 상태이므로 운영 영향 0.

## 6. 코덱스 자문 이력 (이어서)

prereg §7의 R1/R2/R3 LGTM 후 본 cycle 실행. R4 사후 검수 결과:

| Round | Verdict | 핵심 |
|---|---|---|
| 4차 사후 검수 (`019e0bb1` resume) | **LGTM-with-caveat** | Implementation prereg-faithful / 결정 logic 정합. View B 지지: 본 결과는 prereg 실행으로는 valid하나 deployment value의 clean test가 아님 (in-sample vs OOF 분포 mismatch). Commit as-is + 채택 OFF 유지 + caveat 명시. saatchi cold guard outcome 변경은 sensitivity note (misclassification X / GUARD_OK 유지). 후속 cycle = retrained artifact + multi-seed 묶음. |

### 6.1 R4 합의 사항

- **본 cycle commit**: prereg + script + results JSON + holdout indices + 본 결과 문서 → 단일 commit. decision-binding 결과 = 채택 보류.
- **saatchi cold guard outcome 변경**: 별도 incident 처리 X / GUARD_OK 분류 유지. 후속 cycle prereg에서 sample-size sensitivity 명시 권고.
- **Positive adoption claim 조건**: retrained artifact + multi-seed cycle 통과 후만 가능. 본 cycle 단독으로는 "calibration deployment value 없음" 결론 도출 X.

## 7. 산출물

- ✅ `docs/calibration_per_source_reproducibility_prereg_20260509.md` (218 lines / R3 LGTM)
- ✅ `docs/calibration_per_source_reproducibility_results_20260509.md` (본 문서)
- ✅ `scripts/validate_per_source_calibration_reproducibility.py`
- ✅ `data/reproducibility_holdout_20260509/{artsy,saatchi}_holdout_indices.json`
- ✅ `model_test_results/calibration_reproducibility_20260509.json`
