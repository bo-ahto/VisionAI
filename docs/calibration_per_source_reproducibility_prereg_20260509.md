# Per-source Calibration 재현성 검증 (Reproducibility / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: `e3367ed` (Phase 2 calibration fit / no-op → fitted)
> **Decision binding**: ✅ YES — 운영 채택(default OFF → mode=on/canary/shadow) 결정 근거.
> Artifact (.cbm/.json) 변경은 본 cycle scope X.

## 1. Goal

`e3367ed` 시점 산출된 per-source calibration cell factor가 cross-fit OOF에 한 번도 들어가지 않은 fresh 20% holdout에서도 baseline 대비 개선되는지 확인.

기준 cell factor (e3367ed):

| Source | Path | Cell | Factor |
|---|---|---|---|
| Artsy | cold | artsy_gallery | 0.9152 |
| Artsy | cold | artsy_online | 0.9757 |
| Artsy | warm | artsy_gallery | 1.0 (guard) |
| Artsy | warm | artsy_online | 1.0 (guard) |
| Saatchi | cold | saatchi_online | 1.0 (guard) |
| Saatchi | warm | saatchi_online | 1.0 (guard) |

본 검증 = 운영 채택 권고의 1차 증거. PASS 여부에 따라 cell 단위 mode 활성화 결정으로 매핑 (운영 변경 자체는 별도 PR/runbook).

## 2. Method (Held-out 20% / decision-binding)

### 2.1 Holdout split

각 source 독립 split. **split_seed = 31337** (PR1 fold seed=42와 분리, 본 cycle 한정 고정):

- **Cold**: `GroupShuffleSplit(test_size=0.20, random_state=31337, groups=artist_slug)` — 작가 단위 누수 방지.
- **Warm**: `_warm_mask` slice 후 `train_test_split(test_size=0.20, random_state=31337, shuffle=True)`.
  ⚠️ Warm split = **row-level only** / artist-level 독립성 미강제 (e3367ed warm OOF가 plain `KFold` 사용하므로 method 정합 우선). 이 한계는 §3 cell 분류에서 흡수 — warm cell은 `consistency_only`로 분류되어 load-bearing 결정에 미사용.

산출 row index → `data/reproducibility_holdout_20260509/<source>_holdout_indices.json` (재현 가능 직렬화 / dataset fingerprint = `sha256` of sorted source rows 동봉).

### 2.2 Refit (80% pool / e3367ed 방법 동일)

남은 80% train pool 위에서 동일 절차로 calibration factor 재산출:

1. PR1 best_params 그대로 재사용 (per-source HP tuning X / Phase 3 별도)
2. Cross-fit 5-fold OOF — cold = `GroupKFold-5(artist_slug)` / warm = `KFold-5(random_state=42)` / `_warm_mask` slice
3. Cell key = `_cell_key(source, "gallery" if is_krw else "online")`
4. Cell factor = `median(y_actual / y_pred)` per cell
5. Per-cell guard 동일: `applied = proposed if cross_fit_mdape_unguarded <= baseline_mdape else 1.0`

### 2.3 Holdout 평가 (Dual-track)

20% holdout 위에서 두 종류 endpoint 산출. **Primary = 운영 채택 결정 endpoint / Secondary = procedure 재현성 진단**.

**Primary (decision-binding / 운영 채택)**:
1. PR1 artifact (`source_conditional_v1_<src>_*`) 그대로 holdout prediction (artifact 재학습 X).
2. Cell별 `baseline_mdape = median(|y_actual − y_pred| / y_actual)`.
3. Cell별 `calibrated_mdape_original = baseline 계산과 동일하나 pred *= original_factor (e3367ed shipped)`.
4. `Δ_original = calibrated_mdape_original − baseline_mdape`. **이 값이 운영 채택 1차 증거**.

**Secondary (procedure 재현성)**:
5. §2.2 80%-pool refit factor 사용한 `calibrated_mdape_refit` 계산.
6. `Δ_refit = calibrated_mdape_refit − baseline_mdape` (참고용 / 동일 절차가 fresh split에서 재생산되는지).
7. `factor_relative_drift = abs(log(refit_factor / original_factor))` per cell. log(1.3) ≈ 0.262 기준 — 초과 시 procedure drift 시그널.

원본 factor와 refit factor 비교 (방향 / drift) = procedure 재현성 진단 / 운영 채택 결정과 분리.

### 2.4 Bootstrap CI (작은 cell)

`artsy_gallery` (n_holdout ≈ 174 추정) 처럼 표본 작은 cell 한정:

- **Paired bootstrap** — row index를 1000-iter resample (with replacement). 매 iter마다 동일 index 위에서 baseline / calibrated_original / calibrated_refit 모두 재계산.
- 산출: `Δ_original`의 90% CI `[lo, hi]`. 결정 기준은 **CI 상한 (`hi`)** — `hi ≤ 0` 이면 "calibrated가 baseline보다 통계적으로 나쁘지 않음" 보수적 보장.
- 참고: 단순(unpaired) bootstrap은 baseline / calibrated 표본을 독립 추출 — paired보다 분산 큼. 본 cycle = paired 고정.

## 3. Decision Criterion

### 3.1 Cell 분류

| 분류 | 조건 | 본 cycle 역할 |
|---|---|---|
| `load_bearing` | `original_factor != 1.0` | 운영 채택 결정 근거 |
| `consistency_only` | `original_factor == 1.0` (guard fallback) | guard 동작 정합 점검 (채택 결정 X) |

e3367ed 산출 기준:
- `load_bearing`: `artsy_gallery` cold (0.9152), `artsy_online` cold (0.9757) — **2 cells**
- `consistency_only`: Artsy warm × 2, Saatchi cold/warm `saatchi_online` × 2 — **4 cells**

### 3.2 Cell 단위 판정 (3-tier)

**PASS** (load_bearing 전제):
- ✅ Holdout `Δ_original ≤ 0` (point estimate / 원본 factor 적용 시 calibrated가 baseline 이하) — **load-bearing endpoint**
- ✅ (작은 cell / `n_holdout < 500`) paired bootstrap **CI 상한 ≤ 0** (`hi ≤ 0`) — small cell 통계적 confidence 보강
- ✅ Procedure drift OK: `factor_relative_drift = abs(log(refit/original)) ≤ log(1.3)` (≈ 0.262)

**INCONCLUSIVE** (load_bearing 전제):
- `Δ_original ≤ 0` (point) BUT 작은 cell CI 상한 `> 0` (CI가 0 가로지름) — operational benefit 점추정은 있지만 통계적 신뢰 부족
- 또는 `Δ_original ≤ 0` BUT procedure drift `> log(1.3)` (운영 개선은 있지만 procedure 재현성 약함)

**FAIL** (load_bearing 전제):
- ❌ Holdout `Δ_original > 0` (point estimate 단독으로 충분 / 운영 시 holdout regression — large cell도 동일 적용)
- ❌ Refit factor 방향 반전 (원본 `<1`인데 refit `>1` 등 / point `Δ_original` ≤ 0이어도 FAIL)
- ❌ Per-cell guard 구현 위반 (cross-fit unguarded MdAPE > baseline 인데 factor ≠ 1.0)

> Note: CI 상한 `> 0`은 small cell 한정 INCONCLUSIVE 트리거 (FAIL 게이트 X). large cell (`n_holdout ≥ 500`)은 CI 미산출 / point estimate `Δ_original`만으로 PASS·FAIL 판정.

**`consistency_only` cell**:
- 별도 점검: holdout에서도 cross-fit unguarded MdAPE > baseline 이고 guard fallback (refit factor=1.0) 발동 → guard 정합 OK.
- 운영 채택 결정에 영향 없음 (모두 factor=1.0 → calibration 미적용).

### 3.3 전체 판정

- 전 `load_bearing` cell PASS → 운영 채택 권고 (해당 cell mode on 후보)
- 일부 `load_bearing` cell PASS / 일부 INCONCLUSIVE → cell 단위 채택 가능 / INCONCLUSIVE는 추가 검증 후 결정
- 임의 `load_bearing` cell FAIL → 해당 cell mode off 권고
- 모든 `load_bearing` cell FAIL → 채택 보류 (e3367ed 결과 split 우연 가능성 / 다른 seed/holdout 추가 검증 필요)
- `consistency_only` cell guard 위반 → 별도 incident (구현 버그 가능성 / 본 cycle 결정과 분리)

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)

- `docs/calibration_per_source_reproducibility_prereg_20260509.md` — 본 문서
- `scripts/validate_per_source_calibration_reproducibility.py` — entry point
- `data/reproducibility_holdout_20260509/{artsy,saatchi}_holdout_indices.json` — split index
- `model_test_results/calibration_reproducibility_20260509.json` — per-cell metrics
- `docs/calibration_per_source_reproducibility_results_20260509.md` — Reprod.B 결과 + 채택 결정 근거

### 4.2 Metrics JSON 스키마

```json
{
  "version": "v1-source-conditional-reproducibility",
  "split_seed": 31337,
  "fold_seed": 42,
  "drift_threshold_log": 0.262,
  "small_cell_n_threshold": 500,
  "dataset_fingerprint": {
    "artsy": "<sha256 of sorted source rows>",
    "saatchi": "<sha256 of sorted source rows>"
  },
  "per_source": {
    "artsy": {
      "n_total": 0,
      "n_train_pool": 0,
      "n_holdout": 0,
      "n_artists_pool": 0,
      "n_artists_holdout": 0,
      "refit_factors": {
        "cold": {"artsy_gallery": 0.0, "artsy_online": 0.0},
        "warm": {"artsy_gallery": 0.0, "artsy_online": 0.0}
      },
      "original_factors": {
        "cold": {"artsy_gallery": 0.9152, "artsy_online": 0.9757},
        "warm": {"artsy_gallery": 1.0, "artsy_online": 1.0}
      },
      "holdout_per_cell": {
        "cold": {
          "artsy_gallery": {
            "category": "load_bearing",
            "n_train_pool": 0,
            "n_holdout": 0,
            "n_artists_train_pool": 0,
            "n_artists_holdout": 0,
            "baseline_mdape": 0.0,
            "calibrated_mdape_original": 0.0,
            "calibrated_mdape_refit": 0.0,
            "delta_original_pp": 0.0,
            "delta_refit_pp": 0.0,
            "factor_relative_drift": 0.0,
            "bootstrap_computed": true,
            "paired_bootstrap_ci90_delta_original": [0.0, 0.0],
            "decision": "PASS"
          },
          "artsy_online": {
            "category": "load_bearing",
            "n_train_pool": 0,
            "n_holdout": 0,
            "n_artists_train_pool": 0,
            "n_artists_holdout": 0,
            "baseline_mdape": 0.0,
            "calibrated_mdape_original": 0.0,
            "calibrated_mdape_refit": 0.0,
            "delta_original_pp": 0.0,
            "delta_refit_pp": 0.0,
            "factor_relative_drift": 0.0,
            "bootstrap_computed": false,
            "paired_bootstrap_ci90_delta_original": null,
            "decision": "PASS"
          }
        },
        "warm": {}
      }
    },
    "saatchi": {}
  }
}
```

스키마 핵심 필드:
- `decision` ∈ `{"PASS", "INCONCLUSIVE", "FAIL"}` (load_bearing) / `{"GUARD_OK", "GUARD_VIOLATION"}` (consistency_only)
- `bootstrap_computed`: small cell (`n_holdout < 500`) → `true` + CI 산출. large cell → `false` + `paired_bootstrap_ci90_delta_original = null`. CI는 small cell INCONCLUSIVE 트리거 한정 / FAIL 게이트 X.
- `paired_bootstrap_ci90_delta_original` = §2.4 paired bootstrap 결과. 결정 시 상한 (`[1]`) 사용 (small cell only).
- `factor_relative_drift` = `abs(log(refit_factor / original_factor))`. `> log(1.3)` AND `Δ_original ≤ 0` → INCONCLUSIVE.
- per-cell `n_train_pool` / `n_artists_train_pool` / `n_artists_holdout` = §3 결정 + sample-size disclosure.

## 5. Out-of-scope

- ❌ PR1 artifact (`.cbm` / `.json`) 재학습
- ❌ Per-source HP tuning (Phase 3 / Optuna 별도 cycle)
- ❌ 운영 unified `integrated_v3_filtered_tuned_source_calibration.json` 변경
- ❌ Cell mode toggle 자동화 / runbook 반영 (본 cycle = 검증 only)
- ❌ Multi-seed sensitivity (split_seed 1개 한정 / 별도 cycle에서 확장)

## 6. 한계 / Risk

- **load_bearing cell이 2개뿐 (artsy cold)**: Artsy cold (`artsy_gallery`, `artsy_online`)만 운영 채택 결정 근거. Saatchi 전체 + warm 전체 = `consistency_only` (guard fallback) — 본 cycle 결과로는 채택 불가, guard 동작 정합만 확인.
- **artsy_gallery n_holdout ≈ 174 (추정)**: 작은 표본 / paired bootstrap CI로 변동성 흡수. CI 폭이 ±5pp 이상이면 결정 신뢰도 낮음 → results 문서에 명시.
- **Warm split row-level only**: §2.1 — warm holdout이 artist-level 누수 미강제. e3367ed warm OOF가 plain `KFold` 사용한 method 정합 유지 위함. 본 cycle에서는 warm cell이 모두 `consistency_only`이므로 영향 제한적이나, 향후 warm factor가 fitted (not 1.0)로 바뀌면 warm holdout split 재설계 필요.
- **Holdout 1회**: split_seed 단일 (31337). 결과의 split 우연 가능성 존재 → 본 cycle scope X. multi-seed sensitivity는 후속 cycle.
- **데이터 분포 가정**: train pool과 holdout이 i.i.d. 가정 (PR1 dataset = single-snapshot). temporal drift 없음 전제.
- **Procedure drift 임계값 `log(1.3)`**: 30% 상대 변화 = arbitrary cutoff. 더 엄격(`log(1.2)`) / 관대(`log(1.5)`) 선택 가능. 본 cycle = `log(1.3)` 고정 / 사후 ablation X (pre-registered).

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 1차 사전 자문 (`019e0bb1-...`) | NEEDS FIX → 반영 완료 | P0×1 (primary endpoint = original factor / dual-track), P1×3 (warm artist-leak / decision 3-tier + CI upper / load_bearing vs consistency_only), P2×1 (metadata 보강) |
| 2차 사전 자문 verification (resume) | NEEDS FIX → 반영 완료 | P1: FAIL 게이트에서 `AND CI upper > 0` 제거 / large cell point-estimate FAIL 가능 / "refit 일치 BUT Δ_original > 0" INCONCLUSIVE bullet 삭제. P2: per-cell `n_train_pool`·artist counts + `bootstrap_computed` flag 추가. |
| 3차 사전 자문 verification (resume) | **LGTM** | §3.2 self-consistent / §4.2 per-cell provenance + bootstrap encoding 정합 / §2.4·§3.3 cross-reference 일치 → **prereg 잠금 / 구현 진입** |
| 4차 사후 검수 (resume) | **LGTM-with-caveat** | Implementation prereg-faithful / 결정 logic 정합. View B 지지 (본 결과는 prereg-valid 실행이지만 deployment value clean test 아님 / in-sample vs OOF 분포 mismatch). Commit + 채택 OFF + 후속 cycle (retrained artifact + multi-seed) 권고. 상세: `calibration_per_source_reproducibility_results_20260509.md` §6.1 |

### 7.1 자문 반영 매핑

| Round | Finding | Severity | 반영 위치 |
|---|---|---|---|
| R1 | Primary endpoint = shipped factor (refit ≠ adoption decision) | P0 | §2.3 Dual-track / §3.2 PASS / §4.2 schema |
| R1 | Warm split artist-leak 미강제 명시 | P1 | §2.1 / §6 |
| R1 | Decision rule (CI upper bound / 3-tier PASS·INCONCLUSIVE·FAIL) | P1 | §3.2 / §2.4 |
| R1 | `load_bearing` vs `consistency_only` 분리 | P1 | §3.1 / §3.3 / §6 |
| R1 | Metadata 보강 (n_artists, dataset fingerprint, per-cell n) | P2 | §2.1 / §4.2 |
| R2 | FAIL 게이트에서 CI 의존 제거 (point estimate `Δ_original > 0` 단독 FAIL) | P1 | §3.2 |
| R2 | Per-cell `n_train_pool` / artist counts + `bootstrap_computed` flag | P2 | §4.2 |
