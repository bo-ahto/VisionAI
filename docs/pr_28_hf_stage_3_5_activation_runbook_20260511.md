# PR-28F-HF Stage 3-5 Activation Runbook

> **작성일**: 2026-05-11
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: 본 세션 4 PR (`c1d76d9` PR-29F → `5cefff4` PR-28F → `6d993aa` PR-FOLLOWERS-FALLBACK → `cde6c52` PR-GALLERY-TIER)
> **운영팀 의존**: ✅ — 본 runbook은 ops 활성화 가이드 / 본 세션 scope = code + docs prep
> **Codex R1 검수 통과**: 본 runbook은 PR-WARM-B Stage 3 pattern 재사용 (variant naming만 28_hf로 매핑)

## 0. 본 deploy의 의미 (Codex Q2 정합)

| 의사결정 축 | Variant | 특성 |
|---|---|---|
| 현행 base 내 최적화 (low-risk incremental) | `v3_filtered_tuned_b_warm` (32f B winner) | PR-WARM-B Stage 3 진행 중 |
| **Base 자체 교체 (strategic replacement)** | **`v3_filtered_tuned_28_hf`** | **본 runbook 대상** |

두 path는 병행 가능하나 **운영 판단은 분리**. 본 runbook은 후자 (28_hf base replacement) 전용.

## 1. 사전 조건 (Stage 3 진입 전 확인)

| 항목 | 상태 | 확인 방법 |
|---|---|---|
| Artifact bundle 7 file `integrated_v3_filtered_tuned_28_hf_*` 존재 | ✅ commit `cde6c52` | `ls model_test_results/integrated_v3_filtered_tuned_28_hf_*` |
| Artifact bundle 8 file `integrated_v3_filtered_tuned_b_warm_28_hf_*` 존재 | ✅ commit `cde6c52` | `ls model_test_results/integrated_v3_filtered_tuned_b_warm_28_hf_*` |
| Variant `v3_filtered_tuned_28_hf` / `_b_warm_28_hf` 등록 | ✅ commit `cde6c52` | `grep v3_filtered_tuned_28_hf src/visionai/price_engine/api/primary_predictor.py` |
| 55 variant tests passing | ✅ | `PYTHONPATH=src pytest tests/price_engine/test_primary_predictor_variants.py` |
| `predict_logs` DDL with `shadow_variant` 컬럼 | ✅ PR2B-prereq.1 (`2d3af98`) | `\d predict_logs` in psql |
| `VARIANT_SHADOW` env var 코드 변경 | ✅ PR-WARM-B Stage 3 옵션 A (`b14c765`) | `grep VARIANT_SHADOW src/visionai/price_engine/api/primary_server.py` |
| Prometheus per-route metrics | ✅ PR2B-prereq.2 (`c60708a`) | Prometheus endpoint 확인 |

**모든 prereq ✅ → Stage 3 활성화 ready**

## 2. Stage 3: Shadow Activation (7-day)

### 2.1 활성화 방식

PR-WARM-B Stage 3 옵션 A (VARIANT_SHADOW env var) **그대로 재사용**.

```bash
# Production server env vars (운영팀 적용)
export MODEL_VARIANT=v3_filtered_tuned          # primary 변경 없음 (32f)
export VARIANT_SHADOW=v3_filtered_tuned_28_hf   # 신규 shadow (28_hf default)
```

Shadow inference:
- Primary (`v3_filtered_tuned`) 결과는 user에게 그대로 반환 (production 영향 zero)
- Shadow (`v3_filtered_tuned_28_hf`) 결과는 `predict_logs.variant_shadow_*` 컬럼에 기록
- Fail-open: shadow load 실패 / inference 실패 시 primary 영향 X

### 2.2 Sign-off 기준 (Codex R1 권고 — Non-inferior 기준)

본 세션 isolated cycle 결과가 거의 noise level이므로, shadow는 **"개선 입증"이 아니라 "운영 regression 부재 확인"** 기준 적용.

| 기준 | Threshold | 비고 |
|---|---|---|
| 7-day aggregate Δ_MdAPE | **≤ +0.3pp** | non-inferior 기준 (isolated +0.13pp 정합) |
| Cold slice Δ_MdAPE (Artsy / Saatchi) | **≤ +0.5pp** | isolated 결과 +0.63/+0.39 → 운영에서도 유사 예상 |
| Warm slice Δ_MdAPE | **≤ +0.5pp** | isolated +0.04pp 정합 (거의 동일 예상) |
| 구조적 하락 없음 | per-cohort 검증 | Top-N artist / source cohort breakdown |
| Latency P95 | **≤ primary + 10%** | shadow 추가 inference 부담 측정 |
| Error rate / empty-output | **= primary** | regression 부재 |

**PASS 조건**: 위 6 criteria 모두 통과

### 2.3 활성화 절차

**Step 1**: Staging 검증 (운영팀 적용 전)
1. Staging instance: `MODEL_VARIANT=v3_filtered_tuned` + `VARIANT_SHADOW=v3_filtered_tuned_28_hf`
2. Smoke test: 10 request 위 primary + shadow 모두 출력 확인
3. `predict_logs`에 `variant_shadow_prediction_price_krw` + `variant_shadow_variant` 기록 확인
4. Tests: `PYTHONPATH=src pytest tests/price_engine/test_variant_shadow.py` 통과 확인

**Step 2**: Production 활성화
1. Production env: `VARIANT_SHADOW=v3_filtered_tuned_28_hf` 적용
2. Server restart (rolling)
3. 첫 1시간 logs 모니터링 — load 성공 + shadow inference 동작 확인
4. Prometheus alerts 확인 (variant_shadow 별 metrics)

**Step 3**: Daily monitoring (7-day)
1. Daily: `python3 scripts/pr_28_hf_daily_shadow_metric.py --days 1`
2. 7-day aggregate: `python3 scripts/pr_28_hf_daily_shadow_metric.py --days 7`
3. JSON output: `model_test_results/pr_28_hf_daily_shadow_report.json`

### 2.4 7-day 종료 시

**PASS** → Stage 4 (canary) 진입 검토
**INCONCLUSIVE** → 7-day 추가 monitoring 또는 root cause analysis
**FAIL** → 28_hf base replacement 보류, isolated cycle 추가 조사

## 3. Stage 4: Canary Rollout (점진적, ~2주)

### 3.1 Cohort hash 기반 progressive rollout

```bash
# Production env vars (단계적 활성화)
export MODEL_VARIANT=v3_filtered_tuned          # 여전히 primary (대부분 traffic)
export VARIANT_CANARY=v3_filtered_tuned_28_hf   # canary variant
export VARIANT_CANARY_PERCENT=5                 # 5% → 10% → 25% → 50% → 100%
```

Cohort hash: `scripts/canary_cohort.py` (SHA256 mod 100 / artist_slug primary + request_id fallback)

### 3.2 단계별 진행 (각 단계 7-day monitoring)

| Step | Percent | Sign-off (28_hf로 routed traffic only) | Duration |
|---|---|---|---|
| 4.1 | 5% | aggregate Δ ≤ +0.3pp, slice Δ ≤ +0.5pp, latency/error OK | 3-day min |
| 4.2 | 10% | 위 동일 | 3-day |
| 4.3 | 25% | 위 동일 | 5-day |
| 4.4 | 50% | 위 동일 | 5-day |
| 4.5 | 100% | (= Stage 5 진입 검토) | — |

각 단계 PASS → 다음 진행. FAIL → rollback 이전 단계.

### 3.3 Rollback path

```bash
export VARIANT_CANARY_PERCENT=0  # 즉시 0% (Primary만 사용)
# Server restart
```

## 4. Stage 5: Full Migration

### 4.1 Default variant 변경

`primary_predictor.py:159`:
```python
DEFAULT_VARIANT = "v3_filtered_tuned_28_hf"  # was "v3_filtered_tuned"
```

코드 commit + production deploy.

### 4.2 Legacy variant cleanup (별도 PR, 점진적)

- `v3_filtered_tuned` (32f legacy) — retain 3개월 (rollback 가능성)
- `v3_filtered_tuned_b_warm` (32f B winner) — retain (별도 axis)
- 본 세션 중간 variants (29f / 28f / 29f_hf) — Codex R3 권고: cleanup PR로 별도 처리

## 5. 후속 (Stage 5 후)

### 5.1 B winner 28_hf path 검토

`v3_filtered_tuned_b_warm_28_hf` (28_hf + warm-retuned XGB) 도 별도 검증:
- Default 28_hf 안정 후 6-month 시점에 b_warm_28_hf shadow 활성화
- 또는 PR-WARM-B Stage 3 결과와 비교 후 결정

### 5.2 Continuous monitoring

- predict_logs aggregation daily (자동화)
- variant별 MdAPE drift detection
- artist cohort 분포 변경 감지

## 6. 본 세션 deliverable 정리

| 항목 | 상태 |
|---|---|
| 코드: variant 등록 + serving 변경 | ✅ commit `cde6c52` |
| Artifacts: 28_hf default + B winner 8 file each | ✅ `model_test_results/integrated_v3_filtered_tuned_28_hf_*` |
| Tests: 55 unit tests | ✅ commit `cde6c52` |
| Runbook | ✅ 본 문서 |
| Monitoring script | ✅ `scripts/pr_28_hf_daily_shadow_metric.py` (PR-WARM-B 패턴) |
| Production 활성화 | ⏸️ 운영팀 수동 (본 runbook 따라) |

## 7. Codex R1 검수 quotes

> "첫 shadow는 `v3_filtered_tuned_28_hf`가 맞습니다. default migration 후보를 가장 직접 검증하고 해석도 가장 깔끔."

> "PR-WARM-B보다 약간 더 보수적으로. 이번 isolated 결과가 거의 noise 수준이라, shadow는 '개선 입증'보다 '운영 regression 부재 확인' 기준으로 두는 게 맞습니다."

> "이번 세션 scope는 runbook + monitoring script까지로 닫고, 실제 활성화와 production env 변경은 수동 운영 절차로 남기는 게 적절합니다."

## 8. 참고 자료

- 본 세션 종합 audit: `docs/layer_audit_session_summary_20260511.html`
- PR-WARM-B 패턴 참조: `docs/pr_warm_b_stage_3_5_activation_runbook_20260511.md`
- Variant shadow code: `src/visionai/price_engine/api/primary_server.py` (`_init_variant_shadow_predictor`)
- Cohort hash utility: `scripts/canary_cohort.py`
