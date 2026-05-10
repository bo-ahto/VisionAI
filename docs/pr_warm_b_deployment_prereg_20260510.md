# PR-WARM-B: B Winner Operational Deployment (decision-binding)

> **작성일**: 2026-05-10
> **분기**: `exp/track1-feature-optimization-cycle` (또는 별도 deploy 분기 분리)
> **연계**: Stage 4 cycle B `3a27002` ADOPT_warm_retuned (5/5 PASS / 평균 Δ_warm=-1.62pp)
> **Decision binding**: ✅ YES — 운영 warm path XGB best_params 교체 (변형 variant 신설 + canary deployment).

## 1. Goal

Stage 4 cycle B 결과 = warm-only XGB retune 5/5 strict PASS. 본 PR = **운영 warm path를 B-retuned XGB로 교체** (cold path 그대로 / 부분 deployment).

질문: `warm_only_retuned_best_params.json` 적용 artifact가 운영 환경 (shadow + canary) 에서 cycle B validation과 동등 또는 유사한 -1.62pp warm 개선을 일관 보여주는가?

PASS 시: full migration (default variant 변경 또는 점진 cohort 확장).
FAIL 시: rollback + 별도 cycle (split variance 또는 production traffic mismatch 진단).

## 2. Method

### 2.1 Artifact bundle 신설

**새 variant**: `v3_filtered_tuned_b_warm` (기존 `v3_filtered_tuned`와 차이 = warm XGB params만).

**새 prefix**: `integrated_v3_filtered_tuned_b_warm`

| 파일 | 내용 | 정합 |
|---|---|---|
| `integrated_v3_filtered_tuned_b_warm_catboost.cbm` | CB cold (default tuned params) | 기존과 동일 hyperparams / random_seed=42 / 동일 데이터 → byte-identical 기대 |
| `integrated_v3_filtered_tuned_b_warm_xgboost.json` | **XGB warm (B-retuned params)** | num_boost=947 / depth=9 / lr=0.125 / min_child_weight=11 / reg_alpha=0.56 / 등 |
| `integrated_v3_filtered_tuned_b_warm_xgboost_label_maps.json` | label maps | XGB 재학습 시 산출 |
| `integrated_v3_filtered_tuned_b_warm_warm_artists.json` | warm artist set | 기존과 동일 (warm slice 정의 변경 X) |
| `integrated_v3_filtered_tuned_b_warm_metrics.json` | training metrics | GroupKFold cold + KFold warm CV |
| `integrated_v3_filtered_tuned_b_warm_best_params.json` | params bundle | catboost: default tuned / xgboost: B-retuned |

### 2.2 Predictor variant 등록

`src/visionai/price_engine/api/primary_predictor.py` `SUPPORTED_VARIANTS` 추가:

```python
"v3_filtered_tuned_b_warm": {
    "prefix": "integrated_v3_filtered_tuned_b_warm",
    "cb_features": CB_FEATURES_BASE,  # N=32 (변경 X)
    "expected_target": "v3_filtered_tuned_b_warm",
},
```

`DEFAULT_VARIANT` 변경 X (현 default = `v3_filtered_tuned` 그대로).

### 2.3 Rollout 전략 (default OFF / canary 우선)

**Stage 1 (default OFF / dev validation)**:
- artifact bundle 생성 + tests (load / predict round-trip / dimension check)
- shadow logging은 그대로 (이미 PR2B-prereq.1 인프라 존재)
- 운영 traffic 영향 X

**Stage 2 (shadow comparison / 1주)**:
- `MODEL_VARIANT=v3_filtered_tuned_b_warm` shadow path 활성화
- 기존 PR2B-prereq.1 dual-logging 위에 새 variant prediction 동시 로깅
- predict_logs DDL에 variant 컬럼 활용
- 종료 기준: warm path 전체 traffic의 90%+ shadow coverage / Δ_warm 모니터링

**Stage 4 (canary 10% / 3일)** (R1 amendment):
- cohort key = **`artist_slug` hash** (artist 단위 일관 split / 동일 artist는 동일 cohort 유지)
- fallback = `request_id` hash (artist 미보유 / 매칭 X 시)
- 분기: `mod 10 == 0` → canary
- 운영 metric (P50/P75/P90 MdAPE / latency) per-source 모니터링 (routing은 stratify X / 측정만 분리)
- 종료 기준: canary ≤ control + 0.3pp / latency ≤ +5% / 만족 시 50% → 100% 점진 확장

**Stage 4 (full migration)**:
- `DEFAULT_VARIANT` 변경 또는 100% canary 전환
- 기존 variant artifact는 fallback 유지 (rollback path)

### 2.4 Validation criteria (각 Stage / R1 amendment)

| Stage | 측정 | 기준 |
|---|---|---|
| Stage 1 | artifact integrity | (1) `warm_artists.json` exact hash 일치 / (2) `label_maps.json` exact hash 일치 / (3) cold + warm prediction round-trip on fixed sample → max abs delta ≤ 1e-6 / MdAPE diff ≤ 0.001pp |
| Stage 3 | shadow Δ_warm | (1) 7-day aggregate Δ_warm ≤ -0.8pp / (2) 5/7 일 daily median Δ_warm ≤ -0.5pp / (3) no day Δ_warm > +0.3pp |
| Stage 4 | canary vs control P50 MdAPE | canary ≤ control + 0.3pp (strict non-inferiority) / latency ≤ +5% |
| Stage 5 | post-migration 1주 metric | 변화 없거나 개선 |

### 2.5 Rollback path (R1 amendment / 메커니즘 명시)

- Metric degradation 시:
  1. `MODEL_VARIANT` (또는 Stage 5에서 `DEFAULT_VARIANT`) 을 `v3_filtered_tuned`으로 복구
  2. **Process restart 또는 reload** — predictor의 cached model swap 보장
  3. **Smoke check**: `predictor.variant == "v3_filtered_tuned"` 확인
- Artifact 파일 삭제 X (rollback 가능 상태 유지)
- DB schema (`predict_logs.variant` 컬럼) 변경 X / metrics schema 변경 X
- Stage 5 이후 1주 안정 시 fallback artifact 정리 결정 (유지 권장)

## 3. 산출물

### 3.1 Code 변경

- `scripts/retrain_v3_filtered_b_warm.py` (신규 / B-retuned warm artifact 학습)
- `src/visionai/price_engine/api/primary_predictor.py` (SUPPORTED_VARIANTS 추가)
- (필요시) `tests/test_primary_predictor.py` (variant load/predict 테스트)

### 3.2 Artifact (model_test_results/ — gitignored / 단 manifest + best_params force-add)

- `integrated_v3_filtered_tuned_b_warm_*` 6 file (catboost.cbm / xgboost.json / xgboost_label_maps.json / warm_artists.json / metrics.json / best_params.json)
- **`integrated_v3_filtered_tuned_b_warm_manifest.json` (force-add)** — 각 파일 SHA256 + dataset fingerprint + git commit (R1 amendment / artifact provenance)
- `integrated_v3_filtered_tuned_b_warm_best_params.json` (force-add / deploy 학습용)

### 3.3 문서

- `docs/pr_warm_b_deployment_prereg_20260510.md` (본 문서)
- `docs/pr_warm_b_deployment_results_20260510.md` (artifact 학습 후 metrics + Stage 1 결과)
- `docs/pr_warm_b_rollout_runbook.md` (Stage 2-4 운영 runbook)

## 4. Out-of-scope

- ❌ Cold path 변경 (CB 또는 cold XGB params)
- ❌ Ensemble blend ratio 변경 (D3 HOLD)
- ❌ N=32 → N≠32 feature 변경
- ❌ Source-conditional warm
- ❌ DEFAULT_VARIANT 즉시 변경 (Stage 4까지 단계적)

## 5. 한계 / Risk

- **Production traffic vs validation seed split 분포 mismatch 가능성**: cycle B validation은 80/20 train_test_split 5 seed / production은 시간순 traffic / 분포 다를 수 있음. Stage 2 shadow가 1차 안전장치.
- **Bit-identical CB 검증**: 동일 hyperparams + 동일 데이터 + random_seed=42 → 이론상 byte-identical / 단 환경 (numpy/scipy 버전) 차이 시 약간 다를 수 있음 / Stage 1 prediction round-trip 비교로 검증.
- **B 5 seed validation 한계**: small sample / split variance / Stage 2 shadow가 N >> 5 traffic 검증.
- **warm_artists set 변경 X 가정**: 본 PR scope = XGB params만 변경 / warm slice 정의 (`_warm_mask` / WARM_MIN_COUNT) 동일.

## 6. 다음 단계 리스트 (Stage 별)

### Stage 1: artifact 학습 + 검증 (즉시 / ~30분 / R1 amendment 반영)
- [ ] `scripts/retrain_v3_filtered_b_warm.py` 작성 (`retrain_v3_filtered_with_existing_best_params.py` 정합 / xgboost params 만 override)
- [ ] B-merged best_params JSON 생성 (catboost 기존 / xgboost B-retuned)
- [ ] 학습 실행 (~15분 wall) — artifact bundle 6 file 산출
- [ ] **Artifact manifest 생성** (`integrated_v3_filtered_tuned_b_warm_manifest.json` / commit 대상):
  - 각 파일 SHA256 hash
  - source params (catboost from existing tuned / xgboost from B-retuned)
  - dataset fingerprint (학습 데이터 shape + sha256)
  - training timestamp + script git commit
- [ ] artifact integrity tests (R1 amendment):
  - **`warm_artists.json` exact hash 일치** (기존 vs 신규 / 동일 데이터 가정 / 불일치 시 fail-stop)
  - **`label_maps.json` exact hash 일치**
  - cold prediction round-trip (fixed 100 rows): max abs Δ ≤ 1e-6 / MdAPE diff ≤ 0.001pp
  - warm prediction round-trip (fixed 100 rows): retuned vs default warm artifact 비교 (cycle B 정합 약 -1.62pp 평균 / 단 prediction은 다름이 expected — degenerate 검증만)
- [ ] CV metrics 기록 (GroupKFold cold / KFold warm)

### Stage 2: predictor variant 등록 + tests (1-2시간)
- [ ] `SUPPORTED_VARIANTS["v3_filtered_tuned_b_warm"]` 추가
- [ ] `tests/test_primary_predictor.py` 신규 variant load/predict test
- [ ] `mypy src/` / `ruff check src/` / `pytest tests/` 통과
- [ ] commit (default OFF / 운영 traffic 영향 X)

### Stage 3: shadow comparison (1주 / 운영 환경)
- [ ] PR2B-prereq.1 dual-logging 위에 신규 variant predict 동시 로깅 활성화
- [ ] predict_logs `variant` 컬럼에 `v3_filtered_tuned_b_warm` 기록
- [ ] daily metric report: per-day median Δ_warm
- [ ] sign-off 기준: 7일 중 5일 이상 -1.0pp ~ -2.5pp 범위 / latency degradation X

### Stage 4: canary 10% (3일)
- [ ] cohort hash 기반 10% 분기 (request_id mod 10)
- [ ] canary metric monitoring: MdAPE / latency / error rate
- [ ] sign-off 기준: canary ≤ control + 0.3pp / latency ≤ +5%
- [ ] 만족 시 50% → 100% 점진 확장

### Stage 5: full migration + cleanup (1주)
- [ ] `DEFAULT_VARIANT = "v3_filtered_tuned_b_warm"` 변경 (또는 100% canary 유지)
- [ ] 1주 안정 모니터링
- [ ] fallback artifact 정리 결정 (유지 권장 / rollback path 보존)

### 후속 cycle 후보 (별도 PR)
- [ ] D1.Y multi-seed N=10 확장 (D1.X NEEDS_MORE_DATA → cold path retune binding 결정)
- [ ] D3.B Stacking meta-learner (D3 scalar w 종결 / advanced blend 별도)

## 7. 코덱스 자문

| Round | Verdict | 비고 |
|---|---|---|
| **R1 사전** | **LGTM with minor (2026-05-10)** | Q1 variant A 채택 / Q2 hash+prediction parity / Q3 KPI 완화 / Q4 artist_slug hash cohort / Q5 exact equality / Q6 rollback mechanics 명시 / Q7 commit B / Q8 schedule 적정 |
| R2 사후 (Stage 1 종료 후) | (예정) | artifact parity + manifest 검수 / Stage 2 진입 결정 |
| R3 사후 (Stage 2 commit 후) | (예정) | predictor variant 등록 코드 / default OFF wiring 검수 |
| R4 사후 (Stage 3 종료 후) | (예정) | shadow 1주 metric 검수 / Stage 4 canary 결정 |
| R5 사후 (Stage 4 종료 후) | (예정) | canary metric 검수 / Stage 5 full migration 결정 |

**R1 amendment 반영 항목** (본 prereg §2.4 / §2.5 / §3.2 / §6 Stage 1 갱신):
1. Stage 3 KPI 완화: 7-day aggregate ≤ -0.8pp / 5/7 daily median ≤ -0.5pp / no day > +0.3pp
2. Stage 4 cohort key: artist_slug hash + request_id fallback (artist 단위 일관 split)
3. Stage 1: warm_artists.json + label_maps.json **exact hash equality** required
4. Stage 1: artifact **manifest 생성** (SHA256 + dataset fingerprint + git commit / commit 대상)
5. Rollback mechanics 명시: env var revert + process restart + smoke-check `predictor.variant`

## 8. 결론

본 PR = cycle B (3a27002) ADOPT verdict의 운영 적용. **단계적 rollout (default OFF → shadow → canary → full migration) + 각 Stage별 명시 sign-off 기준**. 인프라 (variant 시스템 + shadow logging + dual-prediction) 이미 존재하므로 본 PR scope = artifact 신설 + variant 등록 + 운영 monitoring orchestration.

운영 영향 X (Stage 1-2 단계까지) / Stage 3 shadow는 read-only / Stage 4 canary부터 사용자 영향 시작 / 모든 단계 rollback path 유지.
