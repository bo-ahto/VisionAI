# v3.6 Production Swap — User Action Checklist (2026-05-08)

> **본 문서 성격**: 잔존 작업 6번 의 **사용자 권한 영역 standalone view**. LLM 비권한 항목 + 사용자 의무 step 만 분리.
> **연계**: `docs/v3_6_swap_readiness_report_20260508.md` (LLM 영역 evidence + Blocked 판정).
> **Owner**: 운영 swap (production rollout) 의사결정자 / DevOps / 운영팀.
> **Target swap**: `MODEL_VARIANT=v3_5_v_year_saatchi_warm` (현재 DEFAULT = `v3_filtered_tuned`).

## 0. 한 줄 요약

| 영역 | 상태 |
|---|---|
| **LLM 영역 검증** | ✅ 완료 (DEV TEST PASS / Baseline 5 file 통과) |
| **사용자 권한 영역** | ⏳ **시작점** (본 checklist) |
| **현재 Blocker** | Swap target artifact bundle (`v3_5_v_year_saatchi_warm` 5 file) 부재 |
| **선행 의무** | §1 안전선 인지 → §2 prerequisite 충족 → §3 실행형 checklist → §4 reviewer signoff |

## 1. LLM 단독 금지 항목 (안전선)

본 항목은 **LLM 절대 비권한** — 사용자 / 운영팀 / DevOps 의 explicit 결정 의무.

| 항목 | LLM 권한 | 사용자 권한 |
|---|---|---|
| Production rollout 실행 | ❌ 금지 | ✅ 의무 |
| Staging deploy 실행 | ❌ 금지 | ✅ 의무 |
| Secrets / DSN / connection string 설정 | ❌ 절대 금지 | ✅ 의무 (환경변수 / vault) |
| Traffic routing (10% → 50% → 100%) | ❌ 금지 | ✅ 의무 |
| Rollback 결정 (긴급 운영) | ❌ 금지 | ✅ 의무 (oncall) |
| Cron schedule 설정 (ETL) | ❌ 금지 | ✅ 의무 |
| Grafana / Prometheus / Slack 운영 wiring | ❌ 금지 | ✅ 의무 |
| Reviewer signoff (1+2+3) | ❌ 금지 | ✅ 의무 |

LLM 가능 영역 (이미 종결):
- ✅ 정적 검증 / DEV TEST 실행 결과 보고
- ✅ readiness 보고서 작성 (PR #41)
- ✅ runbook 평가 / artifact 정합 점검 / code review 의견

## 2. Critical prerequisite (Blocker — 충족 의무)

본 항목 **모두 충족 후만** §3 checklist 진입 가능.

### 2.1 Swap target artifact bundle 학습 + 적재 (P0 Blocker)

`SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]` (`primary_predictor.py:79-83`) 의 prefix `integrated_v3_5_v_year_saatchi_warm_*` 5 runtime file:

| File | 적재 위치 | 현재 상태 |
|---|---|---|
| `integrated_v3_5_v_year_saatchi_warm_catboost.cbm` | `model_test_results/` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_xgboost.json` | `model_test_results/` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json` | `model_test_results/` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_warm_artists.json` | `model_test_results/` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_source_calibration.json` | `model_test_results/` | ❌ MISSING |

**학습 source**:
- `scripts/saatchi_year_made_merger.py` 의 V_year_saatchi_warm variant build → 학습 pipeline 실행
- 학습 결과로 5 file 생성 → `model_test_results/` 적재

**검증 의무**:
```bash
# 5 file 적재 확인
/bin/ls model_test_results/ | grep "integrated_v3_5_v_year_saatchi_warm_"
# → 5 entries 출력
```

### 2.2 Provenance manifest 적재 + clean state (P0)

Swap target variant 의 provenance manifest:

```bash
# 적재 확인
/bin/ls model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json
# git_dirty=false 보장
jq .git_dirty model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json
# → false
```

**Caveat**: 현재 baseline manifest (`integrated_v3_filtered_tuned.provenance.json`) 의 `git_dirty=true` 는 canonical evidence 해석 주의 항목 — swap target 은 **clean state 학습 의무**.

### 2.3 운영 환경 의존성 (P1)

운영 환경 별도 install:

```bash
# psycopg[binary] 설치 (cron 운영 환경)
pip install psycopg[binary]>=3.1
# 또는
uv sync --all-extras
```

LLM 환경 (로컬 dev) 와 운영 환경 (cron / DB connect) 별개.

### 2.4 PostgreSQL `predict_logs` schema 적재 (P1)

`monitoring/sql/` 의 SQL 운영 DB 적용:

```bash
psql $DB_URL -f monitoring/sql/001_predict_logs_ddl.sql
psql $DB_URL -f monitoring/sql/002_v_d7_predict_sold_pairs.sql
psql $DB_URL -f monitoring/sql/003_cohort_baselines.sql
psql $DB_URL -f monitoring/sql/010_metrics_upstream.sql
psql $DB_URL -f monitoring/sql/011_metrics_cohort.sql
psql $DB_URL -f monitoring/sql/012_metrics_rate_limit.sql
psql $DB_URL -f monitoring/sql/013_metrics_mdape.sql
psql $DB_URL -f monitoring/sql/014_metrics_audit.sql
psql $DB_URL -f monitoring/sql/020_alert_rollback_triggers.sql
```

### 2.5 Grafana / Prometheus / Slack 운영 환경 wiring (P1)

운영 monitoring stack 적용:

| 항목 | 위치 | 적용 |
|---|---|---|
| Grafana dashboard | `monitoring/grafana/dashboard_v3_6_rollout.json` | import |
| Grafana alerts | `monitoring/alerting/grafana_alerts.yaml` | apply |
| Grafana contact points | `monitoring/alerting/grafana_contact_points.yaml` | apply (Slack / PagerDuty) |
| Notification policies | `monitoring/alerting/grafana_notification_policies.yaml` | apply |
| Prometheus scrape | `monitoring/prometheus/scrape_config.yaml` | apply |

### 2.6 Connection string / secrets / cron schedule (P0 — LLM 절대 비권한)

운영 환경 secrets 설정 (사용자 / DevOps 영역):
- `DATABASE_URL` (PostgreSQL `predict_logs`)
- `MODEL_VARIANT=v3_5_v_year_saatchi_warm` env var (production 적용 시점에만)
- ETL cron schedule (`scripts/etl_predict_logs.py`)
- API key / OAuth 등 (해당 시)

## 3. 실행형 swap checklist (11 step)

본 checklist 는 §2 prerequisite **모두 충족 후** 위에서 아래로 순차 실행:

```
[ ]  1. Swap target artifact bundle 5 file 적재 확인
        /bin/ls model_test_results/ | grep "integrated_v3_5_v_year_saatchi_warm_"
        → 5 entries (catboost.cbm / xgboost.json / xgboost_label_maps.json /
          warm_artists.json / source_calibration.json)

[ ]  2. Provenance manifest 적재 + git_dirty=false 확인
        jq .git_dirty model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json
        → false

[ ]  3. 운영 환경 의존성 설치
        pip install psycopg[binary]>=3.1
        또는 uv sync --all-extras

[ ]  4. PostgreSQL predict_logs schema 적재
        psql $DB_URL -f monitoring/sql/001_predict_logs_ddl.sql
        (그 후 002~020 순차 적용)

[ ]  5. Grafana dashboard + alerting + Prometheus wiring
        monitoring/grafana/dashboard_v3_6_rollout.json import
        monitoring/prometheus/scrape_config.yaml apply
        monitoring/alerting/grafana_alerts.yaml + contact_points + notification_policies apply

[ ]  6. Phase 3 STAGING 환경에서 DEV TEST 재실행
        MODEL_VARIANT=v3_5_v_year_saatchi_warm \
          python scripts/v3_6_phase3_dev_test.py
        → fallback_cases_fail=0 / gating_correctness=1.0 / passed=true

[ ]  7. Pre-canary smoke (0.3 qps cap)
        cold_rollout_shadow_runbook §Phase 3 Pre-canary 절 따라 실행
        → TestClient warmup-mode + 0.3 qps cap 검증

[ ]  8. Phase A cold shadow (D+0 ~ D+7)
        Shadow inference 활성화 (실제 트래픽 비교)
        Drift monitoring (`monitoring/playbooks/scenario-A-parser-drift.md` 등 6 시나리오)
        실제 prediction 비교 / regression 감지 시 즉시 중단

[ ]  9. D+7 판정 + reviewer 1+2+3 signoff (§4 참조)
        7-day shadow 결과 + drift report → staged rollout 결정
        reviewer 1: API/serving (primary_server / primary_predictor / Dockerfile.api)
        reviewer 2: infra/deploy (artifact bundle / env contract / rollback path)
        reviewer 3: data/ML contract (metrics / provenance / calibration)

[ ] 10. Staged rollout (10% → 50% → 100%)
        각 단계에서 monitor / alert wiring 검증
        rollback path 확보 (§5 참조)
        regression 감지 시 즉시 rollback (사용자 / oncall 권한)

[ ] 11. Final swap (MODEL_VARIANT env var production 적용)
        export MODEL_VARIANT=v3_5_v_year_saatchi_warm
        (DEFAULT_VARIANT 변경 시 별도 PR 의무 — primary_predictor.py:86)
        production 환경변수 영구 등록
```

## 4. Reviewer signoff matrix

D+7 판정 (Step 9) 시점 의무 — 3 reviewer signoff:

| Reviewer | 영역 | 검토 항목 |
|---|---|---|
| **Reviewer 1** | API / serving | `primary_server.py` / `primary_predictor.py` / Dockerfile.api / logging schema / cohort gating / batch endpoint / `/monitor` payload |
| **Reviewer 2** | Infra / deploy | Dockerfile.api COPY 대상 존재성 / 5-file artifact bundle naming / `MODEL_VARIANT` / metrics / calibration prefix 일치 / rollback path / runbook |
| **Reviewer 3** | Data / ML contract | `metrics.json` / `provenance.json` / calibration / source bundle 정합 / cell calibration 정확성 / warm artist set 일관성 |

**Deploy contract signoff**: 3 reviewer 모두 signoff 후만 swap 확정.

## 5. Rollback 시나리오 (긴급 운영)

`monitoring/playbooks/` 의 6 drift scenarios + `monitoring/sql/020_alert_rollback_triggers.sql` 의 rollback trigger.

### 5.1 Rollback 트리거 (자동 alert)

| Scenario | Trigger | 대응 |
|---|---|---|
| A. Parser drift | `playbooks/scenario-A-parser-drift.md` | upstream parser 점검 / rollback |
| B. Saatchi rate limit | `playbooks/scenario-B-saatchi-rate-limit.md` | rate limit 조정 / fallback |
| C. Cohort gating fail | `playbooks/scenario-C-cohort-gating-fail.md` | gate 임시 disable / rollback |
| D. Cache warmup spike | `playbooks/scenario-D-cache-warmup-spike.md` | cap 강화 / 트래픽 throttle |
| E. Model regression | `playbooks/scenario-E-model-regression.md` | **즉시 rollback** + drift report |
| F. Artifact corruption | `playbooks/scenario-F-artifact-corruption.md` | bundle 재학습 / rollback |

### 5.2 Rollback 실행 (사용자 / oncall 권한)

```bash
# 즉시 rollback: MODEL_VARIANT 를 baseline 으로 복귀
export MODEL_VARIANT=v3_filtered_tuned
# 또는 DEFAULT_VARIANT 사용 (env var unset)
unset MODEL_VARIANT

# 운영팀 / DevOps 환경에서 즉시 적용 (production env)
# - K8s deployment env var update + rolling restart
# - 또는 process supervisor 재시작
```

### 5.3 Rollback 후 의무

1. drift report 작성 (`docs/` 적재)
2. failure post-mortem (사용자 / 운영팀)
3. 후속 cycle 진입 (LLM cycle 가능 — readiness report 재작성 / artifact bundle 재학습)

## 6. 후속 작업 시 참조

본 checklist 외 reference:

| 문서 | 역할 |
|---|---|
| `docs/v3_6_swap_readiness_report_20260508.md` | LLM 영역 evidence + Blocked 판정 (본 checklist 의 base) |
| `docs/v3_6_phase3_runbook.md` | Phase 3 pre-rollout DEV TEST + STAGING runbook |
| `docs/cold_rollout_shadow_runbook_20260507.md` | Cold rollout shadow 운영 runbook (§Phase 3 Pre-canary 절 등) |
| `docs/phase_a_monitoring_spec_20260507.md` | Phase A monitoring spec |
| `docs/v3_6_summary_report.md` / `.html` | v3.6 종합 보고서 (외부 보고용) |
| `docs/v3_6_plan.md` | v3.6 plan (변경 사유 / 산출물 list) |
| `docs/api_reference.html` | API contract reference (PR13b /monitor 필드) |
| `README.md` §Canonical artifact manifest | 운영 v3 모델 reference anchor |
| `monitoring/playbooks/*.md` | 6 drift scenario playbook |
| `src/visionai/price_engine/api/primary_predictor.py:73-83` | SUPPORTED_VARIANTS config |
| `scripts/v3_6_phase3_dev_test.py` | DEV TEST 실행 entry |

## 7. 본 checklist 의 governance

| 항목 | 내용 |
|---|---|
| **Authority boundary** | 본 문서 = 사용자 권한 영역 standalone view (LLM 비권한 명시) |
| **LLM 가능** | checklist 작성 / 정적 검증 / readiness 보고서 (이미 완료) |
| **사용자 의무** | §2 prerequisite 충족 + §3 11 step + §4 reviewer signoff + §5 rollback 권한 |
| **본 cycle 종결 기준** | swap target bundle 학습 + 운영 환경 prerequisite 충족 + reviewer signoff 후 swap 실행 |
| **실패 시 대응** | §5 rollback + drift report + 후속 cycle (LLM cycle 가능) |

## 8. 코덱스 자문 history

| 차수 | 내용 |
|---|---|
| 잔존 작업 6번 사전 자문 (2026-05-08) | LLM 가능 / 사용자 영역 분리 + Blocked 판정 + readiness report 권고 |
| 본 checklist 사후 검수 (예정) | 본 commit 직후 |

## 9. 관련 PR

- PR #27 (`feat: v3.6 production server bundle`) — 본 checklist 의 swap source
- PR #34 (`chore: repo hygiene + canonical asset adoption`) — provenance manifest reference anchor
- PR #38 (`chore: salvage _v5_eval_framework.py`) — eval framework salvage
- PR #41 (`docs: v3.6 swap readiness report`) — 본 checklist 의 base anchor
- PR #40 (`docs: archive retention policy`) — archive cycle policy 종결
