# PR-HTW-FLAG Stage 3-5 Activation Runbook

> **작성일**: 2026-05-11
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: PR-HTW-FLAG (`e7a61f8`) — 29_hf_htw variant + has_total_works flag 추가
> **이전 deploy candidate**: 28_hf (deprecated as deploy target; 28_hf 파일은 historical 보존)
> **운영팀 의존**: ✅ — 본 runbook은 ops 활성화 가이드
> **Codex R1/R2/R3 검수 통과**

## 0. 본 runbook의 의미

본 세션 진화 흐름:
- PR-28F-HF runbook (`28_hf`) — 직전 deploy candidate, 본 세션에서 deprecated as deploy target
- **본 runbook (`29_hf_htw`)** — 신규 deploy candidate. has_total_works flag 추가로 첫 일관 개선 cycle

| 의사결정 축 | Variant | 특성 |
|---|---|---|
| 현행 base 내 최적화 (low-risk) | `v3_filtered_tuned_b_warm` (32f B winner) | PR-WARM-B Stage 3 별도 path |
| **Base 자체 교체 + flag 추가** | **`v3_filtered_tuned_29_hf_htw`** | **본 runbook 대상 — 일관 개선** |

## 1. 사전 조건 (Stage 3 진입 전 확인)

| 항목 | 상태 | 확인 방법 |
|---|---|---|
| Artifact bundle 7 file `integrated_v3_filtered_tuned_29_hf_htw_*` 존재 | ✅ commit `e7a61f8` | `ls model_test_results/integrated_v3_filtered_tuned_29_hf_htw_*` |
| Variant `v3_filtered_tuned_29_hf_htw` 등록 | ✅ commit `e7a61f8` | `grep v3_filtered_tuned_29_hf_htw src/visionai/price_engine/api/primary_predictor.py` |
| `has_total_works` flag serving 동작 | ✅ commit `e7a61f8` | `grep has_total_works src/visionai/price_engine/api/primary_feature_builder.py` |
| 63 variant tests passing | ✅ | `PYTHONPATH=src pytest tests/price_engine/test_primary_predictor_variants.py` |
| Deploy readiness 자동 검증 | ✅ | `PYTHONPATH=src python3 scripts/verify_29_hf_htw_deploy_readiness.py` (10 checks) |
| `predict_logs.variant_shadow_*` 컬럼 | ✅ PR2B-prereq.1 (`2d3af98`) | `\d predict_logs` in psql |
| `VARIANT_SHADOW` env var 코드 | ✅ PR-WARM-B Stage 3 옵션 A (`b14c765`) | `grep VARIANT_SHADOW src/visionai/price_engine/api/primary_server.py` |
| B winner 29_hf_htw artifact | ⏸️ 후속 PR | (Stage 4 canary 진입 전 보강 권고) |

## 2. Stage 3: Shadow Activation (7-day)

### 2.1 활성화 방식

```bash
# Production server env vars (운영팀 적용)
export MODEL_VARIANT=v3_filtered_tuned          # primary 변경 없음 (32f)
export VARIANT_SHADOW=v3_filtered_tuned_29_hf_htw   # 신규 shadow
```

Shadow inference:
- Primary (`v3_filtered_tuned`) 결과는 user에게 그대로 반환 (production 영향 zero)
- Shadow (`v3_filtered_tuned_29_hf_htw`) 결과는 `predict_logs.variant_shadow_*` 컬럼에 기록
- Fail-open: shadow load 실패 / inference 실패 시 primary 영향 X

### 2.2 Sign-off 기준 (본 세션 첫 일관 개선이지만 보수적)

| 기준 | Threshold | Isolated cycle 결과 |
|---|---|---|
| 7-day aggregate Δ_MdAPE | **≤ +0.3pp** | -0.51pp (isolated) |
| Cold slice Δ_MdAPE (Artsy / Saatchi) | **≤ +0.5pp** | -0.43 / -0.55pp |
| Warm slice Δ_MdAPE | **≤ +0.5pp** | -0.01 / -0.02pp |
| 구조적 하락 없음 | per-cohort 검증 | unmatched 작가 분포 monitoring |
| Latency P95 | **≤ primary + 10%** | shadow 추가 부담 측정 |
| Error rate / empty-output | **= primary** | regression 부재 |

**PASS 조건**: 위 6 criteria 모두 통과

### 2.3 활성화 절차

**Step 1**: 자동 사전 검증
```bash
PYTHONPATH=src python3 scripts/verify_29_hf_htw_deploy_readiness.py
# Exit 0 = READY
```

**Step 2**: Staging 검증
1. Staging instance: `MODEL_VARIANT=v3_filtered_tuned` + `VARIANT_SHADOW=v3_filtered_tuned_29_hf_htw`
2. Smoke test: 10 request 위 primary + shadow 모두 출력 확인
3. `predict_logs`에 `variant_shadow_prediction_price_krw` + `variant_shadow_variant` 기록 확인
4. Tests: `PYTHONPATH=src pytest tests/price_engine/test_variant_shadow.py` 통과 확인

**Step 3**: Production 활성화
1. Production env: `VARIANT_SHADOW=v3_filtered_tuned_29_hf_htw` 적용
2. Server restart (rolling)
3. 첫 1시간 logs 모니터링 — load 성공 + shadow inference 동작 확인
4. Prometheus alerts 확인

**Step 4**: Daily monitoring (7-day)
```bash
python3 scripts/pr_29_hf_htw_daily_shadow_metric.py --days 7
```

### 2.4 7-day 종료 시

**PASS** → Stage 4 (canary) 진입 검토 (단, B winner 29_hf_htw 학습 권고)
**INCONCLUSIVE** → 7-day 추가 monitoring
**FAIL** → 본 deploy 보류, isolated cycle 추가 조사

## 3. Stage 4: Canary Rollout (점진적, ~2주)

### 3.1 Cohort hash 기반 progressive rollout

```bash
export MODEL_VARIANT=v3_filtered_tuned
export VARIANT_CANARY=v3_filtered_tuned_29_hf_htw
export VARIANT_CANARY_PERCENT=5  # 5% → 10% → 25% → 50% → 100%
```

Cohort hash: `scripts/canary_cohort.py` (SHA256 mod 100 / artist_slug primary + request_id fallback)

### 3.2 단계별 진행

| Step | Percent | Sign-off (29_hf_htw로 routed traffic only) | Duration |
|---|---|---|---|
| 4.1 | 5% | aggregate Δ ≤ +0.3pp, slice Δ ≤ +0.5pp | 3-day min |
| 4.2 | 10% | 위 동일 | 3-day |
| 4.3 | 25% | 위 동일 | 5-day |
| 4.4 | 50% | 위 동일 | 5-day |
| 4.5 | 100% | (= Stage 5 진입 검토) | — |

### 3.3 Rollback path

```bash
export VARIANT_CANARY_PERCENT=0
# Server restart
```

## 4. Stage 5: Full Migration

### 4.1 Default variant 변경

`primary_predictor.py:159`:
```python
DEFAULT_VARIANT = "v3_filtered_tuned_29_hf_htw"  # was "v3_filtered_tuned"
```

코드 commit + production deploy.

### 4.2 Legacy variant cleanup (별도 PR, 점진적)

- `v3_filtered_tuned` (32f legacy) — retain 3개월 (rollback 가능성)
- `v3_filtered_tuned_b_warm` (32f B winner) — retain (별도 axis)
- 본 세션 중간 variants (29f / 28f / 29f_hf / 28_hf) — Codex R3 권고: cleanup PR로 별도 처리

## 5. 후속 (Stage 5 후)

### 5.1 B winner 29_hf_htw

본 PR scope는 default only. B winner 29_hf_htw 학습 후속 PR:
- Default 29_hf_htw 안정 후 학습 (warm-only XGB retune)
- 검증 후 `v3_filtered_tuned_b_warm_29_hf_htw` variant 추가

### 5.2 Continuous monitoring

- predict_logs aggregation daily (자동화)
- variant별 MdAPE drift detection
- artist cohort 분포 변경 감지

## 6. 본 세션 deliverable 정리

| 항목 | 상태 |
|---|---|
| 코드: variant 등록 + serving 변경 | ✅ commit `e7a61f8` |
| Artifacts: default 7 file | ✅ `model_test_results/integrated_v3_filtered_tuned_29_hf_htw_*` |
| Tests: 63 unit tests | ✅ commit `e7a61f8` |
| Runbook | ✅ 본 문서 |
| Monitoring script | ✅ `scripts/pr_29_hf_htw_daily_shadow_metric.py` |
| Verification script | ✅ `scripts/verify_29_hf_htw_deploy_readiness.py` (10 checks) |
| Production 활성화 | ⏸️ 운영팀 수동 (본 runbook 따라) |
| B winner 29_hf_htw | ⏸️ 후속 PR |

## 7. Codex R2 검수 quote

> "PASS — 전 metric 일관 개선이고 변동성 기준으로도 문제 없어 R2는 통과가 맞습니다."

> "29_hf_htw — 현재 증거만 보면 28_hf보다 29_hf_htw가 default candidate입니다."

> "variant 추가만 — 이번 PR은 variant 추가 commit만 넣고, B winner 반영은 후속 PR로 분리하는 쪽이 검증/롤백/리뷰 모두 깔끔합니다."

## 8. 28_hf runbook (deprecated as deploy target)

이전 deploy candidate 28_hf 관련 파일들은 historical reference로 유지:
- `docs/pr_28_hf_stage_3_5_activation_runbook_20260511.md`
- `scripts/pr_28_hf_daily_shadow_metric.py`
- `scripts/verify_28_hf_deploy_readiness.py`

28_hf는 default OFF였고 production deploy 안 됨. 본 deploy 진행 시 28_hf 관련 file 사용 X.

## 9. 참고 자료

- 본 세션 종합 audit: `docs/track1_session_complete_20260511.html`
- PR-WARM-B 패턴 참조: `docs/pr_warm_b_stage_3_5_activation_runbook_20260511.md`
- Variant shadow code: `src/visionai/price_engine/api/primary_server.py` (`_init_variant_shadow_predictor`)
- Cohort hash utility: `scripts/canary_cohort.py`
