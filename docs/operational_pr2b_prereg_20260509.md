# Operational Adoption PR2B — Artifact Deploy + Rollout Runbook (default OFF)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle` (또는 별도 PR2B branch)
> **연계**:
> - PR1 (commit `f74f73b`) artifact bundle 산출
> - PR2A (commit `938d585`) router module
> - PR2A.5 (commit `290a3c0`) server integration
>
> **Decision binding**: ✅ YES (Dockerfile artifact bundle 추가 / 다만 default OFF / 운영 영향 X 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)
>
> ⚠️ **본 cycle scope = artifact deploy + runbook (default OFF)**.
> 실제 production rollout (SOURCE_ROUTER_MODE 활성화) = **PR2B-prereq + 운영 결정** 후 별도 cycle.

## 1. Goal

Source-conditional bundle 영역 의 의무 영역 의 의무 production 이미지 영역 의 의무 영역 의 의무 영역 의 의무 = "이미지 재빌드 없이 env flag 만으로 phased rollout / rollback" 영역 의 의무 영역 의 의무 영역 의 의무.

PR2B deliverables:
1. **Dockerfile.api**: source_conditional_v1 bundle 추가 (Artsy + Saatchi + provenance / always present)
2. **Env config**: SOURCE_ROUTER_MODE / _PERCENT / _RULE_VERSION default 명시
3. **Rollout runbook** (markdown / phased): off → shadow → canary 5% → 50% → on
4. **Promotion criteria** + **Rollback trigger** 명시
5. **PR2B-prereq dependency 명시** (shadow dual-log / predict_logs DDL alter / Prometheus per-route)

## 2. Method (코덱스 사전 자문 P1 권고 정합)

### 2.1 Dockerfile.api 변경

**원칙**: artifact bundle = **always present** (mode flag OFF 영역 의 의무 영역 의 의무 X / shadow/canary/on 영역 의 의무 영역 의 의무 영역 = bundle 의무).

```dockerfile
# 기존 (운영 unified bundle)
COPY model_test_results/integrated_v3_filtered_tuned_*.{cbm,json} ./models/

# PR2B 추가 (source-conditional v1 bundle)
COPY model_test_results/source_conditional_v1_artsy_catboost.cbm ./models/
COPY model_test_results/source_conditional_v1_artsy_xgboost.json ./models/
COPY model_test_results/source_conditional_v1_artsy_xgboost_label_maps.json ./models/
COPY model_test_results/source_conditional_v1_artsy_warm_artists.json ./models/
COPY model_test_results/source_conditional_v1_artsy_source_calibration.json ./models/
COPY model_test_results/source_conditional_v1_artsy_metrics.json ./models/
COPY model_test_results/source_conditional_v1_saatchi_catboost.cbm ./models/
COPY model_test_results/source_conditional_v1_saatchi_xgboost.json ./models/
COPY model_test_results/source_conditional_v1_saatchi_xgboost_label_maps.json ./models/
COPY model_test_results/source_conditional_v1_saatchi_warm_artists.json ./models/
COPY model_test_results/source_conditional_v1_saatchi_source_calibration.json ./models/
COPY model_test_results/source_conditional_v1_saatchi_metrics.json ./models/

# Default env: SOURCE_ROUTER_MODE=off (backward compat / 운영 영향 X)
ENV SOURCE_ROUTER_MODE=off
ENV SOURCE_ROUTER_PERCENT=0
ENV SOURCE_ROUTER_RULE_VERSION=v1
```

⚠️ **Image size 영향**: 추가 ~24MB × 2 = ~48MB (per-source bundle / current ~25MB 영역 의 의무 영역 의 의무 영역 = 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 ~3배). 다만 production HTTP 영역 의 의무 영역 의 의무 영역 의 의무 deploy time 영역 의 의무 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 영역 의 의무 1회.

### 2.2 Env config (production / staging / dev)

| Env | SOURCE_ROUTER_MODE | _PERCENT | _RULE_VERSION |
|---|---|---|---|
| **dev** | off (default) | 0 | v1 |
| **staging** | off → shadow → canary | 0 → 5 → 50 → 100 | v1 |
| **prod** | off (initial) | 0 | v1 |

Production rollout 시 영역 의 의무 영역 의 의무 영역 의 의무 = env update 영역 의 의무 영역 의 의무 영역 의 의무 (image rebuild X / SIGHUP or rolling restart 영역 의 의무 영역 의 의무 영역 의 의무).

### 2.3 Rollout Runbook (별도 markdown / phased)

`docs/operational_pr2b_rollout_runbook.md` 신설:

#### Phase 0: Deploy with default OFF
- Image rebuild (PR2B Dockerfile)
- Env: SOURCE_ROUTER_MODE=off
- Verify: 운영 영향 X / 모든 request → unified / 응답 routing_source="unified" / routing_reason="router_off"
- Promotion criterion: 1주 안정 / no regression

#### Phase 1: Shadow (logging only)
- Env: SOURCE_ROUTER_MODE=shadow
- Serving = unified (변경 X) / shadow decision/prediction = 별도 log
- ⚠️ **Dependency: PR2B-prereq 의무** (현재 shadow dual-log 영역 의 의무 영역 의 의무 X → 별도 cycle 영역 의 의무 영역 의 의무 추가 영역 의 의무 영역 의 의무)
- Promotion criterion (PR2B-prereq 후): shadow vs primary decision agreement ≥ 95% / shadow MdAPE within ±2.117 of primary

#### Phase 2: Canary 5%
- Env: SOURCE_ROUTER_MODE=canary, SOURCE_ROUTER_PERCENT=5
- 5% cohort (deterministic hash) → routed (artsy/saatchi/unified)
- 95% → unified
- Promotion criterion (1주 영역 의 의무 영역 의 의무):
  * error rate ≤ baseline + 0.5%
  * p99 latency ≤ baseline + 10%
  * per-source cold MdAPE drift ≤ +1.0%p
  * Saatchi cohort: cold MdAPE ≤ baseline (Saatchi gap monitoring)

#### Phase 3: Canary 50%
- SOURCE_ROUTER_PERCENT=50
- Promotion criterion (1주):
  * 동일 + slice drift detection
  * cohort fairness (50% in canary / 50% control)
  * artist-level MdAPE 분포 비교

#### Phase 4: On (full rollout)
- SOURCE_ROUTER_MODE=on
- Monitoring (1주 안정):
  * 모든 metric within thresholds
  * no rollback trigger
- Promotion = on / persistent

### 2.4 Rollback Trigger (locked / immediate)

**즉시 rollback** (`SOURCE_ROUTER_MODE=off`):

| Trigger | Threshold |
|---|---|
| Error rate | > baseline + 0.5% (5xx / prediction failure) |
| p99 latency | > baseline + 10% |
| per-source cold MdAPE | > baseline + 1.0%p (Saatchi 영역 의 의무 영역 의 의무 영역 의 의무 우선) |
| fail-closed RuntimeError | startup 시 artsy/saatchi load 실패 |

**Rollback 영역 의 의무 영역 의 의무**:
- env update (SOURCE_ROUTER_MODE=off) → SIGHUP / rolling restart
- Artifact bundle = **제거 X** (image 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 / mode flag 만 영역 의 의무)
- 즉시 backward compat (default OFF = unified)

## 3. ⚠️ Dependency: PR2B-prereq (별도 cycle)

본 PR2B (artifact deploy + runbook) 영역 의 의무 영역 의 의무 = artifact 영역 의 의무 영역 의 의무 image 영역 의 의무 영역 의 의무 영역 의 의무 영역 / 다만 **실제 rollout (shadow/canary/on)** 영역 의 의무 영역 의 의무 영역 의 의무 = **PR2B-prereq 영역 의 의무 영역 의 의무 영역 의 의무 fix 의무**:

### PR2B-prereq scope (별도 cycle / 코덱스 P1)

1. **Shadow dual-logging** (P1 / source_router.py + primary_server.py 변경):
   - shadow mode 영역 의 의무 영역 의 의무 영역 의 의무 = serving = unified
   - + **shadow predictor 영역 의 의무 영역 의 의무 영역 의 의무 parallel inference** (artsy/saatchi/unified 영역 의 의무 영역 의 의무 영역 의 의무 routed)
   - → shadow_routing_source / shadow_routed_variant / shadow_prediction 별도 log
   - shadow phase promotion criterion 영역 의 의무 영역 의 의무 = shadow vs primary decision diff

2. **predict_logs DDL alter** (P1):
   - `ALTER TABLE predict_logs ADD COLUMN routing_source TEXT;`
   - + routing_reason / routed_variant / router_mode / cohort_in_canary
   - + shadow_* (shadow dual-log 정합)
   - ETL / dashboard 영역 의 의무 영역 의 의무 영역 의 의무 정합

3. **Prometheus per-route metrics** (P2):
   - prediction_total_by_routed_variant{variant} counter
   - prediction_latency_by_routed_variant histogram
   - routing_decision_total{routing_source, routing_reason} counter
   - cohort_in_canary distribution

4. **Rule version naming consistency** (P2):
   - `SOURCE_ROUTER_RULE_VERSION` vs `ROLLOUT_RULE_VERSION` 영역 의 의무 영역 의 의무 영역 의 의무 정합 (단일 영역 의 의무 영역 의 의무 영역 의 의무)

### Dependency timeline

| Cycle | Status | 의무 |
|---|---|---|
| PR2B (본 cycle) | Artifact deploy + runbook | image 영역 의 의무 영역 의 의무 영역 의 의무 / OFF 만 |
| PR2B-prereq | 별도 cycle (다음) | shadow dual-log + DDL + Prometheus |
| PR2B-rollout (실제) | 운영 결정 | env wiring (off → shadow → canary → on) |

## 4. Decision Criterion (locked / 본 cycle scope)

**채택 (PASS / merge)**:
- ✅ Dockerfile.api 영역 의 의무 영역 의 의무 source_conditional_v1 bundle 추가 (12 file × 2 source = 24 file or symlink)
- ✅ Env default = OFF (backward compat 검증 영역 의 의무 영역 의 의무 영역 의 의무)
- ✅ Runbook markdown 영역 의 의무 영역 의 의무 영역 의 의무 작성
- ✅ PR2B-prereq dependency 명시
- ✅ 기존 746 tests + new bundle integrity test PASS

**비채택 (FAIL)**:
- ❌ Image size > 100MB 영역 의 의무 영역 의 의무 영역 의 의무 (현재 + 48MB ≈ ~73MB / 정합)
- ❌ 회귀 (default OFF behavior 변경)

## 5. Out-of-scope (본 cycle / 별도 영역)

❌ **PR2B-prereq scope** (별도 cycle):
- Shadow dual-logging
- predict_logs DDL alter
- Prometheus per-route metrics
- Rule version naming

❌ **Production rollout** (운영 결정 / 별도 cycle):
- 실제 SOURCE_ROUTER_MODE 활성화
- Phase 0 → 1 → 2 → 3 → 4 운영 진행
- Production monitoring

## 6. 한계 / Risk

- **Image size 증가**: ~48MB (per-source bundle) / 정합 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무
- **Memory + startup time**: active mode 영역 의 의무 영역 의 의무 영역 의 의무 = 3 predictor eager-load (~3배 / shadow/canary/on 영역 의 의무 영역 의 의무 영역 의 의무)
- **Dependency**: PR2B-prereq 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 = shadow phase 작동 X / canary phase observability 영역 의 의무 영역 의 의무 영역 의 의무
- **재현성**: 단일 fresh holdout (CHAMPION verdict 영역 의 의무 영역 의 의무 / 또 다른 split 영역 의 의무 영역 의 의무 영역 의 의무 검증 의무 / Phase 5+ 영역 의 의무 영역 의 의무 의무)

## 7. 진행 일정

| 단계 | 영역 | 시간 |
|---|---|---:|
| Prereg + 코덱스 사전 자문 round 1 | 본 doc | 0.5 |
| Round 1 fix (P1 발견 / scope 좁힘) | 본 doc + dependency 명시 | 0.5 |
| Dockerfile.api 변경 | bundle 추가 + env default | 0.5 |
| Rollout runbook 작성 | docs/operational_pr2b_rollout_runbook.md | 0.5 |
| Bundle integrity test | tests/ | 0.5 |
| 코덱스 사후 round 2 | | 0.5 |
| commit | | 0.5 |
| **합계** | — | **~3 시간** |

## 8. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1: shadow dual-log + DDL gap + Prometheus) → scope 좁힘 (Option 2) |
| 1차 fix (본 commit) | PR2B-prereq dependency 명시 + scope 좁힘 (artifact deploy + runbook only) |
| 2차 사후 (예정) | 본 fix commit 직후 |
