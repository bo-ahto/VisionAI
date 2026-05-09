# Operational Adoption — Source-conditional Rollout Runbook (PR2B)

> **작성일**: 2026-05-09
> **대상 cycle**: PR2B-rollout (artifact deploy 후 운영 결정)
> **연계**:
> - PR1 artifact bundle (commit `f74f73b`)
> - PR2A router module (commit `938d585`)
> - PR2A.5 server integration (commit `290a3c0`)
> - PR2B artifact deploy + Dockerfile (본 commit)
> - **⚠️ PR2B-prereq dependency** (shadow dual-log + DDL alter / 별도 cycle)

> ⚠️ **본 runbook = production rollout 영역 의 의무 영역 의 의무 영역 의 의무 절차**.
> PR2B-prereq 영역 의 의무 영역 의 의무 영역 의 의무 fix 후 운영 결정 영역 의 의무 영역 의 의무 의무.

## Phase Overview

```
deploy with default OFF
  ↓ (1주 안정)
Shadow (logging only)
  ↓ (PR2B-prereq 후 / shadow dual-log 영역 의 의무 영역 의 의무)
Canary 5%
  ↓ (1주)
Canary 50%
  ↓ (1주)
Full Rollout (on)
```

**Rollout 영역 의 의무 영역 의 의무 영역 의 의무**: env update 영역 의 의무 영역 의 의무 영역 의 의무 (image rebuild X / SIGHUP or rolling restart 영역 의 의무 영역 의 의무 영역 의 의무).

## Phase 0: Deploy with Default OFF

**Objective**: Source-conditional bundle 영역 의 의무 영역 의 의무 production image 영역 의 의무 영역 의 의무 영역 의 의무 / 운영 동작 영역 의 의무 영역 의 의무 영역 의 의무 변경 X.

**Steps**:
1. Build new image: `docker build -f Dockerfile.api -t visionai-api:pr2b .`
2. Deploy with env: `SOURCE_ROUTER_MODE=off`
3. Verify:
   - Server starts (lifespan / unified만 load / artsy/saatchi=None)
   - `/health` 200 OK
   - `/api/v1/predict` 정상 / `routing_source=unified` / `routing_reason=router_off`
   - `/api/v1/model/info`: `router_mode=off` / `default_variant=v3_filtered_tuned`

**Promotion criterion (Phase 0 → 1)**:
- 1주 안정 운영 (no startup error / no regression)
- Image size 영역 의 의무 영역 의 의무 영역 의 의무 += ~48MB / deploy time impact 영역 의 의무 영역 의 의무 영역 의 의무 정상

**Rollback**: image rollback (이전 PR2A.5 image / artifact bundle 미포함) — 다만 default OFF 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 동일 동작 / rollback 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 X.

## Phase 1: Shadow (logging only)

⚠️ **Dependency: PR2B-prereq 영역 의 의무 영역 의 의무 영역 의 의무 fix 의무**:
1. **Shadow dual-logging** 구현 (source_router.py + primary_server.py): shadow_routing_source / shadow_routed_variant / shadow_prediction 영역 의 의무 영역 의 의무 별도 log
2. **predict_logs DDL alter**: routing_source / routing_reason / routed_variant / router_mode / cohort_in_canary / shadow_* columns 추가
3. **ETL/dashboard** 정합

**PR2B-prereq 종료 후 진행**:

**Steps**:
1. Env update: `SOURCE_ROUTER_MODE=shadow` (rolling restart)
2. Verify:
   - Server starts (3 predictor load / artsy + saatchi + unified)
   - `/api/v1/predict`: serving = unified (변경 X) / `routing_reason=shadow_mode_primary_unified`
   - shadow log 영역 의 의무 영역 의 의무 별도 (shadow_routed_variant / shadow_prediction)
3. Monitor (1주):
   - **Shadow vs primary decision agreement** ≥ 95%
   - **Shadow MdAPE within ±2.117%p** of primary (per source / per artist segment)
   - No latency increase > 10% (parallel inference 영역 의 의무 영역 의 의무)

**Promotion criterion (Phase 1 → 2)**:
- Shadow agreement ≥ 95%
- Shadow MdAPE 정합 (Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 우선 / no regression)
- No anomaly in cohort distribution

**Rollback**: env update `SOURCE_ROUTER_MODE=off` / 즉시 backward compat.

## Phase 2: Canary 5%

**Steps**:
1. Env update: `SOURCE_ROUTER_MODE=canary`, `SOURCE_ROUTER_PERCENT=5`
2. Verify:
   - 5% cohort (deterministic hash on artist_slug or fingerprint) → routed
   - 95% → unified fallback
   - `/api/v1/predict`: cohort_in_canary boolean / routed_variant 영역 의 의무 영역 의 의무 영역 의 의무
3. Monitor (1주):
   - **Error rate** ≤ baseline + 0.5% (5xx / prediction failure)
   - **p99 latency** ≤ baseline + 10%
   - **per-source cold MdAPE drift** ≤ +1.0%p:
     * Artsy cohort: holdout MdAPE 영역 의 의무 영역 의 의무 영역 의 의무 정합
     * **Saatchi cohort: cold MdAPE ≤ baseline (Saatchi gap monitoring 영역 의 의무 영역 의 의무 영역 의 의무)**
   - **cohort fairness**: 5% cohort 분포 = 균등 (deterministic hash / no skew)

**Promotion criterion (Phase 2 → 3)**:
- 1주 안정 (모든 metric within thresholds)
- Saatchi cohort 영역 의 의무 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 SourceCond CHAMPION 정합 (cold MdAPE ≤ baseline -0.85)

**Rollback trigger**:
- Error rate > baseline + 0.5%
- p99 latency > baseline + 10%
- Per-source MdAPE drift > +1.0%p
- → 즉시 `SOURCE_ROUTER_MODE=off` / artifact bundle 영역 의 의무 영역 의 의무 영역 의 의무 X (mode flag만)

## Phase 3: Canary 50%

**Steps**:
1. Env update: `SOURCE_ROUTER_PERCENT=50`
2. Monitor (1주):
   - 동일 metric (Phase 2)
   - **Slice drift detection**: artist-level / artwork-level MdAPE 분포 비교 (cohort vs control)
   - **Cohort fairness**: 50% cohort = 균등 / source 분포 정합

**Promotion criterion (Phase 3 → 4)**:
- 1주 안정 + slice drift no anomaly
- Saatchi cohort 영역 의 의무 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 안정

## Phase 4: On (full rollout)

**Steps**:
1. Env update: `SOURCE_ROUTER_MODE=on`
2. Monitor (1주):
   - 모든 metric within thresholds
   - No rollback trigger
3. Promotion = on / persistent

**Post-rollout 의무**:
- Phase 5+ cycle: per-source calibration 재산출 (현재 no-op)
- 재현성 검증 (또 다른 fresh holdout split)
- per-source HP tuning (Optuna re-tune)

## Rollback Plan (locked / immediate)

**즉시 rollback** 영역 의 의무 영역 의 의무:

| Trigger | Threshold |
|---|---|
| Error rate (5xx / prediction failure) | > baseline + 0.5% |
| p99 latency | > baseline + 10% |
| per-source cold MdAPE | > baseline + 1.0%p (특히 Saatchi) |
| fail-closed RuntimeError | startup 시 artsy/saatchi load 실패 |

**Rollback 영역 의 의무 영역 의 의무**:
- Env update: `SOURCE_ROUTER_MODE=off`
- SIGHUP or rolling restart (image rebuild X)
- Artifact bundle = **제거 X** (image 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 / mode flag 만 영역 의 의무)
- 즉시 backward compat (default OFF = unified / 사전 운영 동작)

## Monitoring Metrics (PR2B-prereq 후 가용)

⚠️ 본 metrics 영역 의 의무 영역 의 의무 영역 의 의무 PR2B-prereq (Prometheus per-route + DDL alter) 영역 의 의무 영역 의 의무 영역 의 의무 의무.

**Prometheus** (PR2B-prereq):
- `prediction_total_by_routed_variant{variant}` counter
- `prediction_latency_by_routed_variant_seconds` histogram (p50 / p95 / p99)
- `routing_decision_total{routing_source, routing_reason}` counter
- `cohort_in_canary` distribution

**Warehouse SQL** (PR2B-prereq):
- per-source cold MdAPE (daily / weekly)
- routing decision 분포 (matched_artsy / matched_saatchi / unmatched_fallback / matched_unknown_source_fallback)
- cohort agreement (canary 5% / 50%)

## Post-rollout 후속 cycle

| Cycle | 영역 |
|---|---|
| **Phase 2: Per-source calibration 재산출** | source_calibration_artsy + saatchi 재 fit (현재 no-op) |
| **Phase 3: 재현성 검증** | 또 다른 fresh holdout split (CHAMPION robust 검증) |
| **Phase 4: Per-source HP tuning** | Optuna re-tune for Artsy + Saatchi |
| **Phase 5: Source effect 가설 검증** | "진짜 source regime" vs "측정 차이" |
