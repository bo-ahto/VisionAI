# PR-WARM-B Stage 1+2: B Winner Operational Deployment — Results

> **분기**: `exp/track1-feature-optimization-cycle`
> **prereg**: `docs/pr_warm_b_deployment_prereg_20260510.md` (R1 LGTM with minor)
> **실행일**: 2026-05-10 (~30분 wall)
> **실행 결과**: ✅ **Stage 1+2 완료** — artifact bundle + variant 등록 완료 / Stage 3 shadow 진입 ready

## 1. Summary

Cycle B (commit `3a27002`) ADOPT_warm_retuned 운영 적용 1단계+2단계 완료:
- ✅ Stage 1: B-retuned warm artifact bundle 생성 (7 file / cold path bit-identical / warm path B-retuned)
- ✅ Stage 2: predictor `SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm"]` 등록 + tests 추가 + 운영 load 시뮬레이션 통과
- ⏳ Stage 3-5: shadow logging (1주) → canary 10% (3일) → full migration

운영 traffic 영향 = **X** (Stage 1-2 / default OFF / `MODEL_VARIANT=v3_filtered_tuned_b_warm` 환경변수로만 활성화).

## 2. Stage 1: Artifact Bundle 학습

### 2.1 설계 결정 (Stage 1 첫 run 결과 fix)

**문제 발견**: 첫 run에서 CB를 default tuned 동일 hyperparams + random_seed=42로 재학습했으나 **byte-different** 결과 (4.31MB → 4.29MB / cold prediction max abs delta 0.27 in log-scale).

**원인 추정**: CatBoost 비결정성 (parallelism / data ordering / library version 미세 차이). random_seed=42는 sample-level seed이지만 multi-thread training 순서까지 보장 X.

**Fix 결정**: CB는 default tuned에서 **COPY** (shutil.copyfile) → cold path bit-for-bit identical 보장. XGB만 B-retuned params로 신규 학습 (warm slice).

→ R1 codex Q2 (prediction parity 우선) + Q5 (exact equality for same-data retrain) 정합. Variant Q1 A (새 variant 신설) 유지.

### 2.2 산출 artifact (7 file / `integrated_v3_filtered_tuned_b_warm_*`)

| 파일 | 산출 방식 | SHA256 (12자) | byte-identical vs default |
|---|---|---|---|
| `catboost.cbm` | COPY | `a8b909735beb...` | ✅ |
| `xgboost.json` | NEW (B-retuned) | (deploy artifact) | (X — B-retuned 의도) |
| `xgboost_label_maps.json` | COPY | `(default와 동일)` | ✅ |
| `warm_artists.json` | COPY | `(default와 동일)` | ✅ |
| `source_calibration.json` | COPY + `model_target` rename | (rename only) | ✅ (cells 동일) |
| `metrics.json` | NEW (CV) | — | (NEW) |
| `best_params.json` | NEW (provenance) | — | (NEW) |
| `manifest.json` | NEW (R1 amendment) | — | (NEW / commit 대상) |

### 2.3 CV metrics (5-fold)

**GroupKFold cold path** (N=28376):
- catboost (CB only): MdAPE = **39.40%** (default 그대로 / cold serving 정합)
- xgboost (XGB only): MdAPE = 40.10%
- ensemble (CB+XGB)/2: MdAPE = 39.00%

**KFold warm slice** (N=27062):
- catboost: 11.90%
- xgboost: **8.00%** ← cycle B best_warm_cv 8.01%와 정합 ✅
- ensemble: 9.50%

→ XGB warm CV 8.00% ≈ cycle B 8.01% (Δ < 0.01) — B-retuned XGB artifact가 cycle B winner와 정합 확인.

### 2.4 Prediction parity verification

**CB cold prediction** (100 sample / log-scale):
- max abs delta: **0.0** (exact match / bit-identical)
- mean abs delta: **0.0**
- `numpy.array_equal`: **True**

**XGB warm prediction** (100 warm sample):
- default mean: 14.80 / b_warm mean: 14.71
- signed delta mean: -0.0876 / std: 0.127 (B-retuned 효과 expected)

→ 운영 라우팅 정합:
- Cold path (CB only): **bit-for-bit unchanged**
- Warm path (XGB only): B-retuned (cycle B 효과 적용)

### 2.5 Calibration carry-forward

`integrated_v3_filtered_tuned_source_calibration.json` 내용 그대로 + `model_target` 만 `"integrated_v3_filtered_tuned"` → `"v3_filtered_tuned_b_warm"` rename.

| Field | 값 |
|---|---|
| cold_factors.artsy_gallery | 1.0 (guard) |
| cold_factors.artsy_online | 0.9426 |
| cold_factors.saatchi_online | 0.9569 |
| warm_factors.artsy_gallery | 0.99999 |
| warm_factors.artsy_online | 1.0050 |
| warm_factors.saatchi_online | 1.0 (guard) |

**Cold factors**: CB COPY → cold prediction 동일 → cold_factors 그대로 적용 가능 (별도 재추정 불필요).

**Warm factors**: XGB 변경 → warm prediction 다름 → warm_factors 재추정 권고 (현 carry-forward는 conservative baseline / warm_factors 모두 ~1.0 이라 no-op-ish 영향 작음). 본 PR scope 외로 deferred → Stage 3 shadow에서 warm factor drift 측정 후 별도 calibrate-fit cycle.

### 2.6 Manifest (R1 amendment)

`integrated_v3_filtered_tuned_b_warm_manifest.json`:
- 7 file SHA256
- dataset fingerprint (n_rows=28376 / n_cols=83 / sha256 prefix=4aed424b2f60)
- git_commit: 3a27002 (cycle B HEAD)
- integrity check: CB / label_maps / warm_artists 모두 byte-identical match=True
- CV summary
- Prediction parity test 결과

## 3. Stage 2: Predictor variant 등록

### 3.1 코드 변경

**`src/visionai/price_engine/api/primary_predictor.py`** `SUPPORTED_VARIANTS` 추가:

```python
"v3_filtered_tuned_b_warm": {
    "prefix": "integrated_v3_filtered_tuned_b_warm",
    "cb_features": CB_FEATURES_BASE,  # N=32
    "expected_target": "v3_filtered_tuned_b_warm",
},
```

`DEFAULT_VARIANT` 변경 X (현 default = `v3_filtered_tuned` 그대로 / Stage 5에서 변경).

### 3.2 Tests 추가

**`tests/price_engine/test_primary_predictor_variants.py`**:
- `test_v3_filtered_tuned_b_warm_config()` — prefix / expected_target / cb_features 검증

```bash
$ pytest tests/price_engine/test_primary_predictor_variants.py -k "config or supported"
4 passed in 1.52s
```

### 3.3 운영 load 시뮬레이션

```python
os.environ["MODEL_VARIANT"] = "v3_filtered_tuned_b_warm"
p = PrimaryPredictor()
p.load_models(Path("model_test_results"))
# Output:
# variant: v3_filtered_tuned_b_warm
# warm artist count: 930
# cb_features count: 32
# cold_calibration cells: ['artsy_gallery', 'artsy_online', 'saatchi_online']
```

→ ✅ schema 검증 통과 / model_target 검증 통과 / artifact 7 file 모두 load OK / fail-closed 트리거 X.

## 4. 다음 단계 리스트 (Stage 3-5)

### Stage 3: Shadow Comparison (1주 / 운영 환경)

**조건**: 본 PR commit 후 → Stage 2 R3 codex review LGTM 후 활성화.

**활성화 절차**:
1. PR2B-prereq.1 dual-logging 인프라 ON 확인 (`predict_logs` table + variant column)
2. shadow path config 추가: `MODEL_VARIANT_SHADOW=v3_filtered_tuned_b_warm` 또는 dual-prediction config flag
3. 1주 일별 metric report:
   - per-day median Δ_warm (b_warm - default)
   - per-source Δ_warm (artsy_gallery / artsy_online / saatchi_online)
   - error rate / latency comparison

**Sign-off (R1 amendment / cycle B 정합)**:
- ✅ 7-day aggregate Δ_warm ≤ -0.8pp
- ✅ 5/7 daily medians Δ_warm ≤ -0.5pp
- ✅ no day Δ_warm > +0.3pp
- ✅ no latency degradation (>+5%) / no error rate spike

**Codex R4**: shadow 1주 결과 + Stage 4 canary 진입 결정.

### Stage 4: Canary 10% → 50% → 100% (3일)

**Cohort key (R1 amendment)**: `artist_slug` hash (artist 단위 일관 split / 동일 artist 동일 cohort) / fallback `request_id`.

**점진 확장**:
1. 10% canary / 24시간 안정 모니터링 → metric OK 확인
2. 50% canary / 24시간 → metric OK 확인
3. 100% canary / 24시간 → metric OK 확인

**Sign-off**: canary ≤ control + 0.3pp / latency ≤ +5% / per-source 분석 (artsy / saatchi 별도)

**Codex R5**: canary metric 검수 + Stage 5 full migration 결정.

### Stage 5: Full Migration + Cleanup (1주)

1. `DEFAULT_VARIANT = "v3_filtered_tuned_b_warm"` 변경 (또는 100% canary 유지)
2. 1주 안정 모니터링
3. fallback artifact (`integrated_v3_filtered_tuned_*`) 보존 결정 (유지 권장)
4. **별도 후속**: warm calibration 재추정 cycle (B-retuned XGB 위에서 warm_factors 재산출)

### 후속 cycle 후보 (별도 PR)

- D1.Y multi-seed N=10 확장 (D1.X NEEDS_MORE_DATA / cold path retune binding 결정)
- D3.B Stacking meta-learner (D3 scalar w 종결 / advanced blend)
- Warm calibration re-fit (B-retuned 위 warm_factors 재추정)

## 5. Rollback Path (R1 amendment / 메커니즘 명시)

Stage 3 이후 metric degradation 감지 시:
1. **`MODEL_VARIANT` (또는 Stage 5에서 `DEFAULT_VARIANT`) revert** to `v3_filtered_tuned`
2. **Process restart 또는 reload** — predictor의 cached model swap 보장 (`load_models()` 다시 호출)
3. **Smoke check**: `predictor.variant == "v3_filtered_tuned"` 확인 + sample prediction round-trip
4. **Artifact retention**: 모든 b_warm artifact 파일 삭제 X (rollback 가능 상태 유지)
5. **DB schema**: `predict_logs.variant` 컬럼 변경 X / metrics schema 변경 X

## 6. 산출물

### 6.1 Commit 대상

**Code 변경**:
- `src/visionai/price_engine/api/primary_predictor.py` (SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm"] 추가)
- `scripts/retrain_v3_filtered_b_warm.py` (신규 / Stage 1 학습 script / COPY + B-retuned XGB)
- `tests/price_engine/test_primary_predictor_variants.py` (신규 variant test 추가)

**문서**:
- `docs/pr_warm_b_deployment_prereg_20260510.md` (R1 LGTM 정합)
- `docs/pr_warm_b_deployment_results_20260510.md` (본 문서)

**Artifact (force-add)**:
- `model_test_results/integrated_v3_filtered_tuned_b_warm_best_params.json` (deploy 학습용 / provenance)
- `model_test_results/integrated_v3_filtered_tuned_b_warm_manifest.json` (R1 amendment / SHA256 + integrity)

### 6.2 .gitignore (artifact 본체)

- `integrated_v3_filtered_tuned_b_warm_catboost.cbm` (COPY → 재현 가능)
- `integrated_v3_filtered_tuned_b_warm_xgboost.json` (script 재실행 시 재현)
- `*_label_maps.json / *_warm_artists.json / *_source_calibration.json` (COPY → 재현 가능)
- `*_metrics.json` (CV result)

## 7. 코덱스 자문 이력

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전 (2026-05-10)** | **LGTM with minor** | Q1-Q8 답변 / 4 amendments 반영 (KPI 완화 / artist_slug cohort / exact equality / manifest) |
| R2 사후 (Stage 1 종료 후 / 본 commit 후) | (예정) | artifact parity + manifest 검수 |
| R3 사후 (Stage 2 commit 후 / 본 commit 후) | (예정) | predictor variant 등록 코드 / default OFF wiring 검수 |
| R4 사후 (Stage 3 종료 후) | (예정) | shadow 1주 metric 검수 / Stage 4 canary 결정 |
| R5 사후 (Stage 4 종료 후) | (예정) | canary metric 검수 / Stage 5 full migration 결정 |

## 8. 결론

PR-WARM-B Stage 1+2 완료. Cold path bit-identical (CB COPY) + warm path B-retuned (cycle B 정합 / XGB warm CV 8.00 ≈ 8.01) + variant 시스템 정합 + 운영 load 시뮬레이션 통과. 본 commit 후 R2/R3 codex 사후 검수 → Stage 3 shadow 1주 활성화 결정.

**운영 traffic 영향**: 본 commit 시점 = **X** (default OFF / 환경변수로만 활성화 가능). Stage 3 shadow 진입 후부터 read-only 모니터링 / Stage 4 canary 진입 후부터 사용자 영향 시작. 모든 단계 rollback path 유지.
