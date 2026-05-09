# N=15 + Source-Conditional Integration cycle (decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: `8c9e58e` (N15.A Confirmatory / HOLD) + `38eab10` (N15.B HP Retune / HOLD / retuned X) + `08a6b80` (OOS verification cycle / per-source calibration shipped factor 분석)
> **Decision binding**: ✅ YES — N=15 features + 운영 best_params (N=32) + per-source artifact retrain + per-source calibration 통합 stack의 운영 채택 결정 직접 근거.

## 1. Goal

지금까지 결과 통합:
- N15.A: pure XGB@N=15 vs Ens@N=32 → HOLD (warm rule strict). 단 cold path에서 artsy 강한 개선 시그널 (-0.86 ~ -3.30pp).
- N15.B: HP retuning under proper GroupKFold CV → HOLD (negative result / retuned default 능가 X).
- OOS cycle: per-source calibration shipped factor (e3367ed) → artsy_online ADOPT_with_caveat / artsy_gallery NEEDS_MORE_DATA.

질문: **Source-Conditional v2 candidate** (`per-source artifact retrained on N=15 features + default xgb_params + per-source cross-fit calibration`)가 **Source-Conditional v1** (N=32 features 기반 PR1 artifact + e3367ed shipped factor / 본 세션 OOS cycle에서 검증된 best baseline) 대비 multi-seed OOS holdout에서 경쟁력 있는가?

PASS 시: Source-Conditional v2 (N=15) operational migration 권고 (per-source artifact 재배포 + N=15 deployment).
FAIL 시: Source-Conditional v1 (N=32) 유지.

## 2. Method (multi-seed × per-source × N=15 + Source-Conditional)

### 2.1 Frozen N=15 features (N15.A 정합)

`['ln_area', 'artist_total_works', 'career_stage', 'area_cm2', 'ln_followers', 'artist_birth_year', 'ho_x_support', 'has_seoul', 'ho', 'ho_power', 'medium_category', 'aspect_ratio', 'ln_ho', 'for_sale_ratio', 'has_depth']`

### 2.2 Multi-seed split

`split_seed ∈ {31337, 7, 13}` (OOS cycle + N15.A 정합 seeds / cross-cycle 일관성).

각 seed × source 독립:
- **Cold split**: `GroupShuffleSplit(test_size=0.20, random_state=seed, groups=artist_slug)`
- **Warm split**: `_warm_mask` slice 후 `train_test_split(test_size=0.20, random_state=seed, shuffle=True)`

### 2.3 Per-(source, seed) Artifact retrain (N=15 / default xgb_params / R5 합의)

각 (source, seed) 80% pool 위에서 in-memory 학습:
1. Per-source filter: `df[df["source"] == src]` (Artsy 7,289 / Saatchi 21,087)
2. **Default xgb_params 그대로** (N=15 retuned X / N15.B HOLD 합의):
   - CatBoost: 운영 best_params (`integrated_v3_filtered_tuned_best_params.json`)
   - XGBoost: 운영 best_params 동일
3. **N=15 features 사용**:
   - CB: cold pool 위 `_train_cb(X[N15_FEATURES], y, CAT_FEATURES_N15, cb_params)` × 1 model
   - XGB: warm pool 위 `_train_xgb(...)` × 1 model

→ 각 (source, seed) 마다 2 model 학습. 6 (source, seed) combos × 2 = 12 trainings 총.

### 2.4 Per-(source, seed) Calibration factor fit (e3367ed pattern)

각 (source, seed) 80% pool 위에서:
1. Cross-fit 5-fold OOF (cold = GroupKFold-5 / warm = KFold-5)
2. Cell factor = `median(y_actual / y_pred)` per cell (N=15 features 기반 prediction)
3. Per-cell guard: `applied = proposed if cross_fit_unguarded_mdape <= baseline_mdape else 1.0`

산출: per-(source, seed) `cell_factor_n15` (cold + warm path).

### 2.5 Holdout evaluation (per (source, seed) / R1 P0 fix / fair OOS comparison)

R1 P0 합의: v1 PR1 artifact (full-data trained / holdout 행 학습 시 본)는 v2 retrained-on-80%와 in-sample/OOS asymmetric. Reprod cycle에서 발견된 in-sample bias 동일 패턴. 본 cycle Primary는 두 candidate 모두 80% pool에 재학습한 fair OOS 비교.

**Primary (decision-binding / fair OOS)**:

각 (source, seed) 80% pool 위에서 두 candidate 모두 retrain:
1. **v2_pool (N=15 candidate)**: §2.3 retrain (N=15 features + default params).
2. **v1_pool (N=32 baseline 정합 retrain)**:
   - CB@N=32 cold pool 위 retrain (N=32 features + default params)
   - XGB@N=32 warm pool 위 retrain (N=32 features + default params)
   - Cross-fit OOF on 80% pool → cell factor (e3367ed 절차 / 본 80% pool 한정 / not e3367ed shipped)

20% holdout 위:
- v2 prediction × v2 cell factor → `calibrated_v2_mdape`
- v1_pool prediction × v1_pool cell factor → `calibrated_v1_mdape`
- `Δ_v2_v1 = calibrated_v2_mdape − calibrated_v1_mdape` per cell — **decision-binding endpoint**

**Secondary (deployed-benchmark / 참고용)**:
- v1_shipped: PR1 artifact (full-data / 운영 그대로) + e3367ed shipped factor → `calibrated_v1_shipped_mdape`
- `Δ_v2_v1_shipped = calibrated_v2_mdape − calibrated_v1_shipped_mdape` per cell — 참고 (in-sample bias caveat 포함 / 운영 deployed artifact와의 직접 비교)
- 본 endpoint는 secondary / decision binding X / 단 reporting

## 3. Decision Criterion

### 3.1 Cell 분류 (e3367ed 정합)

- `load_bearing`: e3367ed shipped factor != 1.0 → artsy_gallery cold / artsy_online cold (2 cells)
- `consistency_only`: shipped factor = 1.0 → artsy warm × 2 + saatchi cold/warm × 2 (4 cells)

### 3.2 Per-(seed, cell) verdict (load_bearing / R1 P2 정합)

> **Operational migration tradeoff (R1 P2)**: N=32 → N=15 변경은 feature pipeline 단순화 (50% feature 축소 / serving payload 감소 / schema 단순화). 따라서 `+0.5pp` mild non-inferiority band은 단순화 trade-off 기반 — strict `Δ ≤ 0` 적용 시 migration이 사실상 불가능. `+1.0pp` 이상은 명백한 regression.

**PASS** (Source-Conditional v2 채택 후보):
- ✅ `calibrated_v2_mdape ≤ calibrated_v1_pool_mdape + 0.5pp` (operational migration tolerance / R1 P2)
- ✅ (작은 cell `n_holdout < 500`) paired bootstrap CI 상한 ≤ +0.5pp

**INCONCLUSIVE**:
- `calibrated_v2_mdape ∈ (v1_pool + 0.5, v1_pool + 1.0]pp` 범위
- 또는 점추정 OK BUT CI 상한 `> +0.5pp`

**FAIL**:
- `calibrated_v2_mdape > calibrated_v1_pool_mdape + 1.0pp` (large degradation)

### 3.3 Per-(seed, cell) verdict (consistency_only / R1 P1 + R2 fix)

R1 P1 합의: consistency_only cell에도 **3-tier verdict 적용** + safety gate. **비교 대상 = `calibrated_v1_pool` (load_bearing과 동일)** (R2 fix: v1_pool refit도 cross-fit OOF + per-cell guard로 cell factor 산출 — 항상 1.0 보장 X / 따라서 calibrated_v1_pool 사용 정합).

**PASS**: `calibrated_v2_mdape ≤ calibrated_v1_pool_mdape + 0.5pp`.
**INCONCLUSIVE**: `(calibrated_v1_pool + 0.5, calibrated_v1_pool + 1.0]pp` 범위.
**FAIL**: `> calibrated_v1_pool + 1.0pp`.

> R2 합의: consistency_only는 e3367ed shipped factor=1.0 cell이지만, v1_pool refit (본 cycle 80% pool) 위에서는 cross-fit OOF + per-cell guard 동작으로 cell factor가 1.0이 아닐 수 있음. v1_pool baseline 대신 calibrated_v1_pool로 비교 baseline 일관 유지. consistency_only 라벨은 adoption decision에서의 역할만 영향 (load_bearing과 분리해 safety gate 적용).

**Safety gate** (R1 P1): 임의 consistency_only cell FAIL → 해당 source 전체 **HOLD** (warm path 또는 Saatchi degradation 무시 X).

### 3.4 Multi-seed aggregate

| Per-seed 분포 (load_bearing per cell × 3 seeds) | Aggregate |
|---|---|
| PASS × 3 | **PASS** |
| PASS × 2 + INCONCLUSIVE × 1 | **INCONCLUSIVE** (split-driven variance) |
| FAIL × 2 이상 | **FAIL** |
| 기타 | **INCONCLUSIVE** |

### 3.5 Per-source verdict (load_bearing cell aggregate + safety gate)

**Adoption driver**: load_bearing cell aggregate verdicts.
**Safety gate**: consistency_only cell aggregate에 임의 FAIL → source HOLD (R1 P1 합의).

- 모든 load_bearing cell PASS AND 모든 consistency_only cell PASS or INCONCLUSIVE → source-level **ADOPT**
- 임의 load_bearing cell FAIL OR 임의 consistency_only cell FAIL → source-level **HOLD**
- 임의 load_bearing cell INCONCLUSIVE → **NEEDS_MORE_DATA**

### 3.6 Overall verdict

- 모든 source ADOPT (or N/A_no_load_bearing) → **ADOPT_v2** (Source-Conditional v2 with N=15 operational migration)
- 임의 source HOLD → **HOLD** (Source-Conditional v1 유지)
- 그 외 → **NEEDS_MORE_DATA**

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)
- `docs/n15_source_conditional_integration_prereg_20260509.md` (본 문서)
- `docs/n15_source_conditional_integration_results_20260509.md` (결과 + 채택 결정)
- `scripts/validate_n15_source_conditional_integration.py` (entry / multi-seed × per-source)
- `data/n15_sc_integration_holdout_20260509/{artsy,saatchi}_seed{31337,7,13}_holdout_indices.json` (6 files)

### 4.2 산출물 (gitignored / 재현 가능)
- `model_test_results/n15_sc_integration_20260509.json` (per-(seed, source, cell) metrics)

### 4.3 JSON Schema

```json
{
  "version": "v1-n15-sc-integration",
  "split_seeds": [31337, 7, 13],
  "frozen_n15_features": [...],
  "default_cb_params": {...},
  "default_xgb_params": {...},
  "shipped_factors_v1": {
    "artsy": {"cold": {"artsy_gallery": 0.9152, "artsy_online": 0.9757}, "warm": {...}},
    "saatchi": {...}
  },
  "per_source": {
    "artsy": {
      "fingerprint": "...",
      "per_seed": {
        "31337": {
          "n_pool_cold": 0, "n_holdout_cold": 0, "n_pool_warm": 0, "n_holdout_warm": 0,
          "v2_fitted_factors": {"cold": {...}, "warm": {...}},
          "holdout_per_cell": {
            "cold": {
              "artsy_gallery": {
                "category": "load_bearing",
                "baseline_n32_mdape": 0,
                "calibrated_v1_mdape": 0,
                "calibrated_v2_mdape": 0,
                "delta_v2_v1": 0,
                "decision_v2_per_seed": "PASS|INCONCLUSIVE|FAIL"
              }
            }
          }
        }
      },
      "aggregate_per_cell": {...},
      "source_verdict": "ADOPT|HOLD|NEEDS_MORE_DATA"
    },
    "saatchi": {...}
  },
  "overall_verdict": "ADOPT_v2|HOLD|NEEDS_MORE_DATA"
}
```

## 5. Out-of-scope

- ❌ Retuned xgb_params (N15.B HOLD 합의 / default 사용)
- ❌ Per-source HP tuning (Phase 3 별도)
- ❌ 운영 unified bundle / runbook 변경 (decision-binding 권고만 / 운영 PR 별도)
- ❌ N≠15 시험 (N=15 전용)
- ❌ Multi-seed N 확대 (3 seeds 고정)
- ❌ Different feature ranking (frozen 고정)
- ❌ Different metric (MdAPE 고정)

## 6. 한계 / Risk

- **Sample size 작은 cell**: artsy_gallery (n_holdout ≈ 174 per seed). Bootstrap CI 보정.
- **Variance accumulation**: N15.A에서 cold cell artsy 시그널 ~−1pp ~ +1.5pp (split variance). N15.C는 calibration 추가 → 추가 variance.
- **운영 deployment 복잡성**: N=15 migration은 schema 변경 / serving feature pipeline 변경 / 별도 PR 필요. 본 cycle은 verification only.
- **Codex multi-round budget**: 본 cycle은 최종 cycle / R1-R3 prereg + R4-R5 사후 패턴 유지하되 더 강한 결과 확인 시 빠른 통과 기대.

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 1차 사전 자문 (`019e0bb1` resume) | NEEDS FIX → 반영 완료 | P0: v1 (full-data PR1) vs v2 (80% pool retrain) in-sample/OOS asymmetric → v1_pool 80% retrain primary, v1_shipped (full-data PR1) secondary. P1: consistency_only cell 3-tier + safety gate (consistency_only FAIL → source HOLD). P2: +0.5pp tradeoff statement 추가. |
| 2차 verification (resume) | NEEDS FIX → 반영 완료 | R2: §3.3 consistency_only baseline을 v1_pool baseline → `calibrated_v1_pool` 변경 (load_bearing과 일관 / v1_pool refit이 1.0 보장 X). |
| 3차 verification (resume) | **LGTM** | §3.3 baseline 일관 → **prereg 잠금 / 구현 진입** |
| 4차 사후 검수 (resume) | **LGTM-with-caveat** | Implementation prereg-faithful / NEEDS_MORE_DATA mechanically correct. Seed 7 +12.08 outlier = small-cell tail real / impl bug X. **추천 D: N=15 migration line 종결** (3-cycle 통합 negative evidence 충분). 후속 다른 cycle (N=18/20/25 sweep) 또는 다른 방향 (warm-only path optimization 등). |
