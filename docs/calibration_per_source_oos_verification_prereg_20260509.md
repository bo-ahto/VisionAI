# Per-source Calibration OOS Verification (Retrained-artifact + Multi-seed / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: `e3367ed` (Phase 2 calibration fit) + `d0f8b88` (Reprod cycle / FAIL with in-sample caveat / R4 follow-up 권고)
> **Decision binding**: ✅ YES — Primary endpoint = procedure OOS value (직접) / Secondary endpoint = e3367ed shipped factor의 OOS non-regression (직접). 채택 권고 = Primary PASS AND Secondary not FAIL.
> **Artifact / unified bundle / runbook 변경**: 본 cycle scope X (검증만).

## 1. Goal

`d0f8b88` (Reprod cycle)의 R4 사후 검수 합의에 따라 본 cycle 진행. Reprod cycle FAIL 결과는 PR1 artifact 그대로 holdout prediction (in-sample bias)이 원인이라는 caveat 인정 → 본 cycle은 **base artifact 자체를 80% pool로 재학습**하여 **truly OOS holdout 평가** 수행.

본 cycle은 **두 endpoint 동시 평가** (codex R1 P0 합의):

1. **Primary endpoint (procedure OOS value / 직접 측정)**: e3367ed의 calibration **procedure** (cross-fit 5-fold OOF + per-cell median-ratio + per-cell guard)가 80% pool에서 산출한 per-pool refit factor가 truly out-of-sample 20% holdout에서 baseline 대비 개선을 만드는가?
2. **Secondary endpoint (shipped factor non-regression / 직접 측정)**: e3367ed가 full data로 산출한 **shipped factor** (운영 배포 candidate)를 동일 truly OOS holdout에 적용 시 baseline 대비 regression이 없는가?

채택 권고 분류 (per §3.4):
- **Strong adoption**: Primary aggregate ∈ `{PRIMARY_PASS, PRIMARY_PASS_with_caveat}` AND Secondary aggregate ∈ `{SECONDARY_PASS, SECONDARY_PASS_with_caveat}`. procedure도 OOS 개선 + shipped factor OOS non-regression.
- **Weak adoption (shipped-only)**: Primary aggregate ∈ `{PROCEDURE_NULL, PROCEDURE_NULL_likely}` AND Secondary aggregate ∈ `{SECONDARY_PASS, SECONDARY_PASS_with_caveat}`. procedure 자체는 80% pool에서 nontrivial factor 미산출 (guard fired)이나 shipped factor (full data fit)는 OOS 직접 효과 — 채택 가능하나 sample-size sensitivity caveat 명시.
- **Hold**: 위 두 조건 모두 미충족 시 (예: Primary FAIL / Secondary FAIL / Primary or Secondary INCONCLUSIVE).

FAIL/HOLD 시: procedure deployment value 부정 또는 추가 cycle 필요 (multi-seed N 확대 / 운영 shadow logging 활용 등).

## 2. Method (Retrained-artifact + Multi-seed / true OOS)

### 2.1 Multi-seed 설계

**split_seed ∈ {31337, 7, 13}** — 3 seeds 고정 / 본 cycle 한정 pre-registered.
- 31337: Reprod cycle과 동일 (cross-cycle 일관성)
- 7, 13: 추가 sensitivity (split-driven variance 측정)

각 seed × 각 source × cold/warm 독립 split + 독립 retrain + 독립 calibration.

### 2.2 Per-(source, seed) Holdout Split

각 (source, seed) 독립:
- **Cold**: `GroupShuffleSplit(test_size=0.20, random_state=seed, groups=artist_slug)` (작가 단위 누수 방지)
- **Warm**: `_warm_mask` slice 후 `train_test_split(test_size=0.20, random_state=seed, shuffle=True)` (row-level / artist-level X — e3367ed warm OOF의 plain `KFold` 정합)

### 2.3 Per-(source, seed) Base Artifact 재학습

**핵심 차이 (Reprod cycle 대비)**: PR1 artifact 사용 X / 80% pool로 base artifact 자체를 재학습.

각 (source, seed):
1. PR1 best_params 그대로 (`integrated_v3_filtered_tuned_best_params.json`) — per-source HP tuning X (Phase 3 별도)
2. **Cold artifact**: `CatBoostRegressor(**cb_params, random_seed=42).fit(80% pool)` — pool 전체로 학습 / 1 model
3. **Warm artifact**: `xgb.train(80% **warm-pool** subset)` — `_warm_mask`-filtered pool 으로 학습 / 1 model

> **Authoritative warm-train contract** (codex R1 P2 합의): `scripts/train_primary_market_v3_filtered.py` (warm-only XGBoost training / serving 라우팅 정합). `experiments/track1_optimization/source_conditional/run_artifact_retrain.py` 는 일반 artifact-building shape 참조용 (warm-train slice는 cite X — 거기서는 full source 학습).

→ 각 seed 마다 4개 artifact (Artsy cb+xgb 2 + Saatchi cb+xgb 2) × 3 seeds = 12 artifacts 총.
→ 모두 in-memory / disk 저장 X (본 cycle 한정 / 운영 artifact는 PR1 그대로 / runbook 변경 X).

### 2.4 Per-(source, seed) Calibration Factor Fit

각 (source, seed) 80% pool 위에서 e3367ed 동일 절차:
1. Cross-fit 5-fold OOF — cold = `GroupKFold-5(artist_slug)` / warm = `KFold-5(random_state=42)` / `_warm_mask` slice
2. 위 cross-fit OOF는 §2.3 retrained artifact가 아닌 **fold-별 train된 별도 모델**의 OOF (e3367ed convention 정합)
3. Cell key = `_cell_key(source, "gallery" if is_krw else "online")`
4. Cell factor (proposed) = `median(y_actual / y_pred_oof)` per cell
5. Per-cell guard: `applied = proposed if cross_fit_unguarded_mdape <= baseline_mdape else 1.0`

산출: per-(source, seed, path) `cell_factor` (cold path 별도 / warm path 별도).

### 2.5 Holdout Evaluation (true OOS / Dual-endpoint)

각 (source, seed) untouched 20% holdout 위에서:
1. **§2.3 retrained artifact**가 holdout prediction (artifact는 holdout 행을 학습하지 X / true OOS).
2. Cell별 `baseline_mdape = median(|y − y_pred| / y)`.
3. **Primary endpoint (per-pool refit factor)**:
   - `calibrated_mdape_refit = MdAPE(y, y_pred × applied_factor_refit)` — §2.4 per-pool refit factor 적용.
   - `Δ_refit = calibrated_mdape_refit − baseline_mdape`.
4. **Secondary endpoint (e3367ed shipped factor)**:
   - `calibrated_mdape_shipped = MdAPE(y, y_pred × shipped_factor)` — e3367ed full-data factor (artsy_gallery=0.9152, artsy_online=0.9757, 그 외=1.0) 적용.
   - `Δ_shipped = calibrated_mdape_shipped − baseline_mdape`.

`consistency_only` cell (e3367ed shipped == 1.0)은 secondary가 trivially `Δ_shipped = 0` — secondary 평가 의미 X / primary `applied_factor_refit` 만 평가.

### 2.6 Paired Bootstrap CI (작은 cell / per seed / per endpoint)

각 (source, seed) per-cell:
- `n_holdout < 500` 인 load_bearing cell 한정.
- 1000-iter paired bootstrap on holdout row index → 매 iter 동일 index 위에서 baseline / calibrated_refit / calibrated_shipped 모두 재계산.
- 산출: `Δ_refit`의 90% CI `[lo, hi]_refit` 와 `Δ_shipped`의 90% CI `[lo, hi]_shipped`.
- 결정 기준 = 각 endpoint 의 **CI 상한** (Reprod cycle 동일 convention).

## 3. Decision Criterion

### 3.1 Cell 분류 (e3367ed shipped factor 기반 / Reprod cycle 동일)

| 분류 | 조건 | 본 cycle 역할 |
|---|---|---|
| `load_bearing` | e3367ed `shipped_factor != 1.0` | adoption 결정 근거 |
| `consistency_only` | e3367ed `shipped_factor == 1.0` (guard fallback) | guard 동작 정합 점검 |

e3367ed 산출 기준 (Reprod cycle과 동일):
- `load_bearing`: `artsy_gallery` cold, `artsy_online` cold (2 cells)
- `consistency_only`: artsy warm × 2, saatchi cold/warm × 2 (4 cells)

### 3.2 Per-seed Cell 단위 판정 (Dual-endpoint)

각 seed × load_bearing cell 독립 판정. 두 endpoint 별도 verdict 산출.

#### 3.2.1 Primary verdict (4-tier / per-pool refit factor 의 OOS value)

**PASS**:
- ✅ `applied_factor_refit != 1.0` (procedure가 non-trivial factor 산출)
- ✅ Holdout `Δ_refit ≤ 0` (point estimate)
- ✅ (작은 cell / `n_holdout < 500`) paired bootstrap `[lo, hi]_refit` 상한 ≤ 0

**GUARD_FIRED** (codex R1 P1 합의 / 별도 state):
- `applied_factor_refit == 1.0` (이 seed 의 80% pool에서 cross-fit unguarded > baseline → guard fallback 발동 → procedure가 nontrivial factor를 지지하지 않음)
- procedure가 non-trivial factor 를 produce 하지 못함 = 통계적 uncertainty 와 다름 (별도 state).

**INCONCLUSIVE**:
- `applied_factor_refit != 1.0` AND `Δ_refit ≤ 0` (point) BUT 작은 cell CI 상한 `> 0` (point ok / 통계적 confidence 부족)

**FAIL**:
- ❌ `Δ_refit > 0` (point estimate 단독 충분 / procedure가 OOS에서 baseline 악화)
- ❌ Per-cell guard 구현 위반 (cross-fit unguarded > baseline 인데 `applied_factor_refit != 1.0`)

#### 3.2.2 Secondary verdict (3-tier / e3367ed shipped factor 의 OOS non-regression)

(`load_bearing` cell 한정 / `consistency_only`는 trivially `Δ_shipped = 0`)

**SHIPPED_PASS**:
- ✅ Holdout `Δ_shipped ≤ 0` (point estimate)
- ✅ (작은 cell) paired bootstrap `[lo, hi]_shipped` 상한 ≤ 0

**SHIPPED_INCONCLUSIVE**:
- `Δ_shipped ≤ 0` (point) BUT 작은 cell CI 상한 `> 0`

**SHIPPED_FAIL**:
- ❌ `Δ_shipped > 0` (shipped factor가 OOS에서 baseline 악화)

#### 3.2.3 `consistency_only` 판정

Per-seed cell:
- guard fallback 발동 (`applied_factor_refit == 1.0`) → GUARD_OK
- 미발동 + cross-fit unguarded > baseline → GUARD_VIOLATION (구현 버그)
- 그 외 (factor != 1.0이지만 procedure가 non-violation 으로 고른 경우) → GUARD_OK
- secondary endpoint 평가 X (shipped == 1.0이므로 trivially Δ_shipped = 0)

### 3.3 Multi-seed Aggregate per Cell (load_bearing 한정)

#### 3.3.1 Primary aggregate (3 seeds 집계)

| Per-seed Primary 분포 | Cell Primary aggregate verdict |
|---|---|
| PASS × 3 | **PRIMARY_PASS** |
| PASS × 2 + (INCONCLUSIVE 또는 GUARD_FIRED) × 1 | **PRIMARY_PASS_with_caveat** |
| GUARD_FIRED × 3 | **PROCEDURE_NULL** (procedure가 non-trivial factor를 지지하지 않음 / 모든 seed 일관) |
| GUARD_FIRED × 2 + (INCONCLUSIVE 또는 PASS) × 1 | **PROCEDURE_NULL_likely** |
| FAIL × 2 이상 | **PRIMARY_FAIL** (procedure가 OOS에서 일관되게 baseline 악화) |
| INCONCLUSIVE × 3 | **INCONCLUSIVE** |
| 기타 mixed (PASS×2 + FAIL×1 등) | **INCONCLUSIVE** (split-driven variance) |

#### 3.3.2 Secondary aggregate (3 seeds 집계 / load_bearing 한정)

| Per-seed Secondary 분포 | Cell Secondary aggregate verdict |
|---|---|
| SHIPPED_PASS × 3 | **SECONDARY_PASS** |
| SHIPPED_PASS × 2 + SHIPPED_INCONCLUSIVE × 1 | **SECONDARY_PASS_with_caveat** |
| SHIPPED_FAIL × 2 이상 | **SECONDARY_FAIL** (shipped factor가 OOS에서 일관되게 regression) |
| SHIPPED_INCONCLUSIVE × 3 | **SECONDARY_INCONCLUSIVE** |
| 기타 mixed | **SECONDARY_INCONCLUSIVE** |

### 3.4 Per-cell Adoption 결정 (Primary × Secondary 조합)

각 load_bearing cell 의 (Primary aggregate, Secondary aggregate) 조합 :

| Primary | Secondary | Cell 채택 결정 |
|---|---|---|
| PRIMARY_PASS | SECONDARY_PASS | **ADOPT** (가장 강한 증거) |
| PRIMARY_PASS | SECONDARY_PASS_with_caveat | **ADOPT_with_caveat** |
| PRIMARY_PASS_with_caveat | SECONDARY_PASS or SECONDARY_PASS_with_caveat | **ADOPT_with_caveat** |
| PROCEDURE_NULL or PROCEDURE_NULL_likely | SECONDARY_PASS or SECONDARY_PASS_with_caveat | **ADOPT_shipped_only** (procedure 자체는 fire X / shipped factor만 OOS 개선 보임 / weak adoption) |
| Any | SECONDARY_FAIL | **HOLD** (shipped factor가 OOS에서 regression) |
| PRIMARY_FAIL | Any | **HOLD** (procedure가 OOS에서 baseline 악화) |
| INCONCLUSIVE (Primary or Secondary) | Any | **NEEDS_MORE_DATA** (multi-seed N 확대 또는 별도 cycle) |

`consistency_only` cell의 per-seed GUARD_VIOLATION 1건이라도 발생 시: 별도 incident (구현 버그 검토 / 본 cycle 결정과 분리).

### 3.5 Per-source / 전체 verdict

**Per-source** (Artsy / Saatchi 별도):
- 모든 load_bearing cell `ADOPT` or `ADOPT_with_caveat` or `ADOPT_shipped_only` → **source-level ADOPT 권고**
- 임의 load_bearing cell `HOLD` → **해당 cell mode off / 나머지 cell 채택 가능**
- 임의 cell `NEEDS_MORE_DATA` → **추가 cycle 권고 (multi-seed N 확대)**

**전체 verdict**:
- 모든 source ADOPT → e3367ed shipped factor 채택 권고 (default OFF → mode 활성화 후보)
- 임의 source HOLD → 부분 채택 / 별도 PR/runbook
- 전체 NEEDS_MORE_DATA → 본 cycle 결과로 결정 X / 후속 cycle 필요

## 4. Output / Artifacts

### 4.1 산출물 (commit 대상)

- `docs/calibration_per_source_oos_verification_prereg_20260509.md` — 본 문서
- `scripts/validate_per_source_calibration_oos.py` — entry point
- `data/oos_holdout_20260509/<source>_seed<S>_holdout_indices.json` — split index per (source, seed)
- `model_test_results/calibration_oos_20260509.json` — per-(source, seed, cell) metrics + aggregate (gitignored / 재현 가능)
- `docs/calibration_per_source_oos_verification_results_20260509.md` — 결과 분석 + R4 후속 채택 결정

### 4.2 Metrics JSON 스키마 (개략)

```json
{
  "version": "v1-source-conditional-oos",
  "split_seeds": [31337, 7, 13],
  "fold_seed": 42,
  "drift_threshold_log": 0.262,
  "small_cell_n_threshold": 500,
  "bootstrap_iterations": 1000,
  "bootstrap_ci_pct": 0.90,
  "dataset_fingerprint": {"artsy": "...", "saatchi": "..."},
  "per_source": {
    "artsy": {
      "n_total": 7289,
      "per_seed": {
        "31337": {
          "n_train_pool_cold": 0,
          "n_holdout_cold": 0,
          "n_artists_pool_cold": 0,
          "n_artists_holdout_cold": 0,
          "n_train_pool_warm": 0,
          "n_holdout_warm": 0,
          "fitted_factors": {
            "cold": {"artsy_gallery": 0.0, "artsy_online": 0.0},
            "warm": {...}
          },
          "holdout_per_cell": {
            "cold": {
              "artsy_gallery": {
                "category": "load_bearing",
                "n_train_pool": 0, "n_holdout": 0,
                "n_artists_train_pool": 0, "n_artists_holdout": 0,
                "applied_factor_refit": 0.0,
                "shipped_factor": 0.9152,
                "baseline_mdape": 0.0,
                "calibrated_mdape_refit": 0.0,
                "calibrated_mdape_shipped": 0.0,
                "delta_refit_pp": 0.0,
                "delta_shipped_pp": 0.0,
                "bootstrap_computed": true,
                "paired_bootstrap_ci90_delta_refit": [0.0, 0.0],
                "paired_bootstrap_ci90_delta_shipped": [0.0, 0.0],
                "decision_primary_per_seed": "PASS",
                "decision_secondary_per_seed": "SHIPPED_PASS"
              }
            },
            "warm": {}
          }
        },
        "7": {...}, "13": {...}
      },
      "aggregate_per_cell": {
        "cold": {
          "artsy_gallery": {
            "primary_decisions_per_seed": ["PASS", "PASS", "PASS"],
            "secondary_decisions_per_seed": ["SHIPPED_PASS", "SHIPPED_PASS", "SHIPPED_PASS"],
            "primary_aggregate": "PRIMARY_PASS",
            "secondary_aggregate": "SECONDARY_PASS",
            "cell_adoption": "ADOPT"
          }
        }
      }
    },
    "saatchi": {...}
  },
  "per_source_verdict": {"artsy": "ADOPT", "saatchi": "ADOPT"},
  "overall_verdict": "ADOPT|HOLD|NEEDS_MORE_DATA",
  "evaluated_at": "..."
}
```

스키마 핵심 필드:
- `decision_primary_per_seed` ∈ `{"PASS", "GUARD_FIRED", "INCONCLUSIVE", "FAIL"}` (load_bearing) / `{"GUARD_OK", "GUARD_VIOLATION"}` (consistency_only)
- `decision_secondary_per_seed` ∈ `{"SHIPPED_PASS", "SHIPPED_INCONCLUSIVE", "SHIPPED_FAIL"}` (load_bearing only / consistency_only는 N/A)
- `primary_aggregate` ∈ `{"PRIMARY_PASS", "PRIMARY_PASS_with_caveat", "PROCEDURE_NULL", "PROCEDURE_NULL_likely", "PRIMARY_FAIL", "INCONCLUSIVE"}`
- `secondary_aggregate` ∈ `{"SECONDARY_PASS", "SECONDARY_PASS_with_caveat", "SECONDARY_FAIL", "SECONDARY_INCONCLUSIVE"}`
- `cell_adoption` ∈ `{"ADOPT", "ADOPT_with_caveat", "ADOPT_shipped_only", "HOLD", "NEEDS_MORE_DATA"}`

## 5. Out-of-scope

- ❌ Per-source HP tuning (Phase 3 / Optuna 별도)
- ❌ 운영 `integrated_v3_filtered_tuned_source_calibration.json` (unified bundle) 변경
- ❌ Cell mode toggle 자동화 / runbook 반영 (본 cycle = 검증만)
- ❌ PR1 artifact 자체 변경 / `source_conditional_v1_*` 재배포
- ❌ Multi-seed 확장 (3 seeds 고정 / 결과 INCONCLUSIVE 시 후속 cycle에서 N 확대)
- ❌ 운영 shadow logging 데이터 활용 (`2d3af98` 인프라 / 별도 cycle 후보)
- ❌ Different metric (MAPE 등) 시험 — MdAPE 고정 (e3367ed convention 정합)

## 6. 한계 / Risk

- **Multi-seed N=3 한정**: split-driven variance를 fully cover하기에는 작은 N. 3 seed가 모두 같은 verdict면 robust 가정 / 갈리면 INCONCLUSIVE → N 확대 후속 cycle 권고.
- **Compute cost**: 6 (source, seed) × (1 base retrain + 5 cross-fit + holdout eval) ≈ 40-60 min wall time. CI/CD 자동화 시 budget 확보 필요.
- **PR1 best_params 고정**: per-source HP tuning이 본 결과에 영향 가능 (특히 작은 source / 작은 cell). Phase 3 cycle scope.
- **Shipped factor 평가의 artifact-mismatch caveat**: 본 cycle은 shipped factor (e3367ed full-data factor)를 holdout에 직접 적용해 secondary endpoint로 평가 (R1 P0 합의로 추가). 단 holdout prediction은 80%-pool로 재학습된 artifact의 출력 — **운영 배포 artifact (PR1 / full-data 학습) 자체의 prediction은 아님**. 가정: 80%-pool artifact와 full-data artifact의 OOS 예측 패턴이 systematic하게 같음 (sample size effect 미미). 이 가정이 깨지면 본 cycle의 shipped factor verdict가 운영 배포 시 효과와 갈릴 수 있음. 후속 검증 후보: 운영 shadow logging (`2d3af98` 인프라) 으로 PR1 artifact 직접 prediction 위 calibration 효과 측정.
- **Holdout n 작은 cell**: artsy_gallery (예상 n_holdout ≈ 174 per seed) — bootstrap CI로 통계적 보정. CI 폭이 ±5pp 이상이면 results 문서에 신뢰도 명시.
- **Warm split row-level only**: 동일 caveat (Reprod cycle §6) — warm cell이 모두 `consistency_only`이므로 영향 제한적.
- **Saatchi cold guard outcome boundary**: Reprod cycle에서 발견된 "full-data와 80%-pool 사이 guard 결정 변경" 가능. 본 cycle multi-seed에서 어느 정도 빈도인지 측정 가능 (`consistency_only` decision 집계로 가시화).

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| 1차 사전 자문 (`019e0bb1` resume) | NEEDS FIX → 반영 완료 | P0: estimand mismatch → dual-endpoint (Primary refit / Secondary shipped). P1: `applied_factor==1.0` → 별도 GUARD_FIRED state (4-tier) + PROCEDURE_NULL aggregate. P2: warm-train contract reference 수정 (train_primary_market_v3_filtered.py). |
| 2차 사전 자문 verification (resume) | NEEDS FIX → 반영 완료 | P1: §1과 §3.4/§3.5 adoption gate 모순 (PROCEDURE_NULL+SECONDARY_PASS의 ADOPT_shipped_only) → §1을 Strong/Weak adoption 분류로 정렬. P2: §3.4 라벨 typo (SECONDARY_PASS_with_caveat). P2: §6 stale text "shipped factor 직접 평가 X" → artifact-mismatch caveat로 갱신. |
| 3차 사전 자문 verification (resume) | NEEDS FIX → 반영 완료 | P2: §3.4 label typo (PRIMARY_PASS_with_caveat row의 SECONDARY_PASS_with_caveat). |
| 4차 사전 자문 verification (resume) | **LGTM** | §3.4 matrix bug-free / §1·§3.4·§3.5 adoption gate 정합 → **prereg 잠금 / 구현 진입** |
| 5차 사후 검수 (resume) | **NEEDS DECISION ALIGNMENT → Strategy A** | Implementation prereg-faithful / 결정 logic mechanically correct / R4 in-sample bias caveat 해소 확인. Strategy A 채택: 본 cycle NEEDS_MORE_DATA 그대로 commit + 전 채택 OFF / artsy_online narrow canary 별도 PR / artsy_gallery multi-seed N 확대. 상세: `calibration_per_source_oos_verification_results_20260509.md` §6.1 |

### 7.1 자문 반영 매핑

| Round | Finding | Severity | 반영 위치 |
|---|---|---|---|
| R1 | Dual-endpoint (Primary refit / Secondary shipped non-regression) | P0 | §1, §2.5, §2.6, §3.2.1+§3.2.2, §3.3, §3.4, §4.2 schema |
| R1 | `GUARD_FIRED` 별도 state (4-tier) + `PROCEDURE_NULL` aggregate | P1 | §3.2.1, §3.3.1, §3.4 |
| R1 | Warm-train contract reference 정정 (`train_primary_market_v3_filtered.py`) | P2 | §2.3 |
| R2 | §1 adoption gate를 §3.4와 정렬 (Strong / Weak ADOPT_shipped_only 분류) | P1 | §1 |
| R2 | §3.4 라벨 typo (SECONDARY_PASS_with_caveat) | P2 | §3.4 |
| R2 | §6 stale text "shipped factor 직접 평가 X" → artifact-mismatch caveat | P2 | §6 |
| R3 | §3.4 라벨 typo (`PRIMARY_PASS_with_caveat` row) | P2 | §3.4 |
