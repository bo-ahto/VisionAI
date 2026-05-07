# v3.6 Production Swap — User Action Checklist (2026-05-08)

> **본 문서 성격**: 잔존 작업 6번 의 **사용자 권한 영역 standalone view**. LLM 비권한 항목 + 사용자 의무 step 만 분리.
> **연계**: `docs/v3_6_swap_readiness_report_20260508.md` (LLM 영역 evidence + Blocked 판정).
> **Owner**: 운영 swap (production rollout) 의사결정자 / DevOps / 운영팀.
> **Target swap**: `MODEL_VARIANT=v3_5_v_year_saatchi_warm` (현재 DEFAULT = `v3_filtered_tuned`).
> **권위 runbook**: `docs/v3_6_phase3_runbook.md` (state machine + preflight) / `docs/v3_5_step4_drift_monitoring.md` (drift / rollback) / `monitoring/playbooks/*.md` (6 drift scenarios).

## 0. 한 줄 요약

| 영역 | 상태 |
|---|---|
| **LLM 영역 검증** | ✅ 완료 (DEV TEST PASS / Baseline 5 file 통과) |
| **사용자 권한 영역** | ⏳ **시작점** (본 checklist) |
| **본 문서 standalone scope** | swap 절차 **reference standalone runbook** (사용자가 prerequisite 충족 후 따라할 reference) — 문서 작성 시점 (2026-05-08) 에는 swap 즉시 실행 가능 X |
| **선결 prerequisite (§2)** | (1) Swap target artifact bundle (`v3_5_v_year_saatchi_warm`) 학습 + 적재 / (2) runtime image `/app/models/` 적재 (Dockerfile.api COPY 또는 PVC) / (3-6) 운영 환경 의존성 + DB schema + monitoring wiring + secrets |
| **선행 의무** | §1 안전선 인지 → §2 prerequisite 충족 → §3 실행형 checklist → §4 reviewer signoff |

## 1. LLM 단독 금지 항목 (안전선)

본 항목은 **LLM 절대 비권한** — 사용자 / 운영팀 / DevOps 의 explicit 결정 의무.

| 항목 | LLM 권한 | 사용자 권한 |
|---|---|---|
| Production rollout 실행 | ❌ 금지 | ✅ 의무 |
| Staging deploy 실행 | ❌ 금지 | ✅ 의무 |
| Secrets / DSN / connection string 설정 | ❌ 절대 금지 | ✅ 의무 (환경변수 / vault) |
| Traffic routing (CANARY 1% → ROLLOUT 5% → 25% → FULL 100%) | ❌ 금지 | ✅ 의무 |
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

`SUPPORTED_VARIANTS["v3_5_v_year_saatchi_warm"]` (`primary_predictor.py:79-83`) 의 prefix `integrated_v3_5_v_year_saatchi_warm_*` runtime file.

**(a) Repo 적재** (학습 산출물 → `model_test_results/`):

| 5 runtime files | 현재 상태 |
|---|---|
| `integrated_v3_5_v_year_saatchi_warm_catboost.cbm` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_xgboost.json` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_warm_artists.json` | ❌ MISSING |
| `integrated_v3_5_v_year_saatchi_warm_source_calibration.json` | ❌ MISSING |

**(b) Signoff evidence artifacts** (reviewer 3 검토 의무, 별도 동반):

| File | 의무 |
|---|---|
| `integrated_v3_5_v_year_saatchi_warm_metrics.json` | reviewer 3 data/ML contract — server `/api/v1/model/info` 의 dynamic load source (없으면 fallback) |
| `integrated_v3_5_v_year_saatchi_warm.provenance.json` | canonical artifact manifest / git_dirty=false 보장 |

**학습 source**:
- `scripts/saatchi_year_made_merger.py` 의 V_year_saatchi_warm variant build → 학습 pipeline 실행
- 학습 결과로 5 runtime file + metrics.json + provenance.json 생성

**(c) Runtime image / volume 적재** (운영 container `MODEL_DIR=/app/models`):

`primary_server.py:441` 의 `MODEL_DIR` resolver (default `/app/models`) 가 실제 load 위치. **repo 적재만으로는 swap 실패** — Dockerfile.api COPY step 또는 K8s ConfigMap / PVC 적재 의무.

```dockerfile
# Dockerfile.api — swap target bundle 추가 (현재 baseline 만 COPY 됨)
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_catboost.cbm ./models/integrated_v3_5_v_year_saatchi_warm_catboost.cbm
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_xgboost.json ./models/integrated_v3_5_v_year_saatchi_warm_xgboost.json
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json ./models/integrated_v3_5_v_year_saatchi_warm_xgboost_label_maps.json
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_warm_artists.json ./models/integrated_v3_5_v_year_saatchi_warm_warm_artists.json
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_metrics.json ./models/integrated_v3_5_v_year_saatchi_warm_metrics.json
COPY model_test_results/integrated_v3_5_v_year_saatchi_warm_source_calibration.json ./models/integrated_v3_5_v_year_saatchi_warm_source_calibration.json
```

**검증 의무** (5 runtime file + metrics + provenance 개별 검사):
```bash
for f in catboost.cbm xgboost.json xgboost_label_maps.json warm_artists.json source_calibration.json metrics.json; do
  test -f "model_test_results/integrated_v3_5_v_year_saatchi_warm_${f}" \
    && echo "✅ ${f}" || echo "❌ ${f} MISSING"
done
test -f "model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json" \
  && echo "✅ provenance" || echo "❌ provenance MISSING"
```

### 2.2 Provenance manifest 적재 + clean state (P0)

```bash
# 적재 + git_dirty=false 강제 검증
jq -e '.git_dirty == false' model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json \
  || (echo "❌ provenance not clean" && exit 1)
```

**Caveat**: 현재 baseline manifest (`integrated_v3_filtered_tuned.provenance.json`) 의 `git_dirty=true` 는 canonical evidence 해석 주의 항목 — swap target 은 **clean state 학습 의무**.

### 2.3 운영 환경 의존성 (P1)

운영 환경 별도 install (zsh quoting 안전):

```bash
pip install 'psycopg[binary]>=3.1'
# 또는
uv sync --all-extras
```

LLM 환경 (로컬 dev) 와 운영 환경 (cron / DB connect) 별개.

### 2.4 PostgreSQL `predict_logs` schema 적재 (P1)

`monitoring/sql/` 의 SQL 운영 DB 적용 — `ETL_DB_URL` env 사용 (psql 변수, 운영 DB 연결):

```bash
# psql 적용 (사용자 환경 자체에서 한 번)
export ETL_DB_URL='postgresql://user:pwd@host:5432/db'
for sql in 001_predict_logs_ddl.sql 002_v_d7_predict_sold_pairs.sql \
           003_cohort_baselines.sql 010_metrics_upstream.sql \
           011_metrics_cohort.sql 012_metrics_rate_limit.sql \
           013_metrics_mdape.sql 014_metrics_audit.sql \
           020_alert_rollback_triggers.sql; do
  psql "$ETL_DB_URL" -f "monitoring/sql/$sql" || break
done
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

### 2.6 운영 환경 envs (Connection / Secrets / Required metadata)

본 영역 **LLM 절대 비권한** — 사용자 / DevOps / 운영팀 영역.

#### 2.6.1 Required envs (server logging + cohort routing)

| Env var | 사용처 | 형식 | 의무 |
|---|---|---|---|
| `MODEL_VARIANT` | `primary_predictor.py:96` | `v3_filtered_tuned` (DEFAULT) / `v3_5_v_year_saatchi_warm` (target) | swap 적용 시점에만 변경 |
| `MODEL_DIR` | `primary_server.py:441` | path (default `/app/models`) | runtime image / PVC 위치 |
| `ARTIFACT_VERSION` | `primary_server.py:66` | semver / commit sha | 배포 metadata |
| `WARM_ARTIST_SLUGS_VERSION` | `primary_server.py:67` | warm artist set version | data contract |
| `ROLLOUT_RULE_VERSION` | `primary_server.py:68` | cohort rule semver | rollout state |
| `ROLLOUT_COHORT` | `primary_server.py:69` | `treatment_5pct` / `control` | traffic 라우팅 |
| `SERVER_INSTANCE` | `primary_server.py:70` | unique per pod / worker | logging 식별자 |

#### 2.6.2 DB / connection envs (별도 영역)

| Env var | 사용처 | 본 PR scope |
|---|---|---|
| `ETL_DB_URL` (psql) | `monitoring/sql/*.sql` 적용 | 본 checklist §2.4 |
| `PG_DSN` (ETL python) | `scripts/etl_predict_logs.py:18` cron 운영 | 본 checklist §2.4 + cron 설정 |
| `POSTGRES_PROXY_URL` | `primary_server.py:133` (server-side proxy) | 본 영역 외 (server 별도 운영) |
| `POSTGRES_PROXY_API_KEY` | `primary_server.py:134` (proxy auth) | 본 영역 외 (secrets vault) |

> **Naming caveat**: psql 의 `ETL_DB_URL` 와 ETL python 의 `PG_DSN` 는 동일 DB 를 가리키지만 변수명이 다름 (코드 contract). server 의 `POSTGRES_PROXY_*` 는 별개 (server-side proxy 의 endpoint / auth). 운영 환경에서 실제 적용 시 사용 위치 별 변수명 정확히 사용.

#### 2.6.3 Cron schedule

```
# crontab 예 (cron 운영 환경, 5분 간격)
*/5 * * * * cd /opt/visionai && python -m scripts.etl_predict_logs --jsonl /app/logs/predictions.jsonl
```

## 3. 실행형 swap checklist (11 step)

본 checklist 는 §2 prerequisite **모두 충족 후** 위에서 아래로 순차 실행. **state machine 권위 = `docs/v3_6_phase3_runbook.md` §STAGING → CANARY → ROLLOUT → FULL**.

```
[ ]  1. Swap target artifact bundle file 적재 확인 (개별 파일 검사)
        for f in catboost.cbm xgboost.json xgboost_label_maps.json \
                 warm_artists.json source_calibration.json \
                 metrics.json; do
          test -f "model_test_results/integrated_v3_5_v_year_saatchi_warm_${f}" \
            && echo "✅ ${f}" || echo "❌ ${f}"
        done
        test -f "model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json" \
          && echo "✅ provenance" || echo "❌ provenance"

[ ]  2. Provenance manifest git_dirty=false 강제 검증
        jq -e '.git_dirty == false' \
          model_test_results/integrated_v3_5_v_year_saatchi_warm.provenance.json
        # 실패 시 즉시 stop

[ ]  3. 운영 환경 의존성 설치
        pip install 'psycopg[binary]>=3.1'
        # 또는 uv sync --all-extras

[ ]  4. PostgreSQL predict_logs schema 적재 (§2.4 참조)
        export ETL_DB_URL='postgresql://...'
        for sql in monitoring/sql/{001,002,003,010,011,012,013,014,020}*.sql; do
          psql "$ETL_DB_URL" -f "$sql" || break
        done

[ ]  5. Grafana dashboard + alerting + Prometheus wiring (§2.5 참조)
        - dashboard_v3_6_rollout.json import
        - prometheus scrape_config.yaml apply
        - grafana alerts + contact_points + notification_policies apply

[ ]  6. Runtime image / volume 적재 (§2.1 (c) 참조)
        - Dockerfile.api 의 COPY step 추가 (또는 K8s PVC / ConfigMap 으로 동등 적재)
        - 6 file (5 runtime + metrics) → /app/models/ 또는 $MODEL_DIR
        - container rebuild + push to registry

[ ]  7. STAGING 24h baseline (v3_6_phase3_runbook §5.2 — 소요 1.5d)
        Pre-flight checklist (권위 runbook §5.2):
        - monitoring/sql/001~020 모두 staging DB 적재 (§2.4)
        - monitoring/sql/003_cohort_baselines.sql 초기 row 적재
          (integrated_v3_5_v_year_saatchi_warm 4 cohort)
        - dashboard_v3_6_rollout.json provisioning + Datasource UID 환경별 치환
        - grafana_alerts.yaml 적용 + env vars 주입
          (SLACK_WEBHOOK_ML_ALERTS / PAGERDUTY_INTEGRATION_KEY)
        - prometheus scrape_config.yaml scrape job 추가
        - scripts/etl_predict_logs.py cron 적재 (5min interval)
        - server env (권위): MODEL_VARIANT=v3_5_v_year_saatchi_warm /
          ROLLOUT_COHORT=treatment_5pct / ARTIFACT_VERSION /
          WARM_ARTIST_SLUGS_VERSION / ROLLOUT_RULE_VERSION / SERVER_INSTANCE

        절차:
        - 1K request 가중 (production replay 또는 synthetic batch)
        - 24h 모니터링 — Grafana 12 panel + 6 alert baseline 측정
        - 정합성 검증 SQL (predict_logs row ≥ 1000 / cohort 분포 ±5%p)

        12 panel 정상 표시 검증 (v3_6_phase3_runbook §5.2 표):
        - Panel 1-6, 10-11 데이터 표시 (upstream + cohort + audit)
        - Panel 7-9, 12 (MdAPE D7 + treatment_vs_control) — 빈 결과 정상
          (sold_actuals D7 미도달 — Phase 4 ROLLOUT 5% D7 단계에서만 검증)

        6 alert baseline (D1 24h 안정):
        - T1 (5min_miss_burst > 200): D1 fire 0건
        - T2 (cohort discrepancy > 5%): D1 fire 0건
        - T2a (NO_BASELINE): cohort_baselines 적재 후 fire 0건
        - T3-7: D1 sold_actuals 적재 부족으로 fire 0건 (정상)

        산출물 (gate):
        - 24h crit alert 누적 0건 (또는 1건 이내 즉시 해결)
        - baseline 수치 기록 (cache_hit_rate / fetch_success / miss_qps avg)

[ ]  8. Pre-canary smoke (v3_6_phase3_runbook §5.3 — 소요 0.5d)
        환경: STAGING 직후 / internal team manual access

        절차 A. Manual request 100건 (다양한 cohort):
          for i in $(seq 1 100); do
            curl -X POST http://staging-api:8000/api/v1/predict \
              -H 'Content-Type: application/json' \
              -d '{"artist_name":"<saatchi_warm_or_other>", \
                   "width_cm":50, "height_cm":50, \
                   "medium":"oil", "target_market":"gallery"}'
          done

        기대:
        - 모든 응답 200 OK
        - model_info.model_type = variant prefix
          (xgboost_v3_5_v_year_saatchi_warm 또는 catboost_v3_5_v_year_saatchi_warm)

        절차 B. Saatchi 매칭 정확성 (100명 sample):
        - warm set 내부: matched=True / source=saatchi
        - warm set 외부 + saatchi: matched=True / source=saatchi (cohort=False)
        - 외부 + non-saatchi: matched=True / source=artsy
        - 미등록: matched=False

        절차 C. Cache fill rate (cache_hit ≥ 10건 유도, runbook §5.3 절차):
        - 첫 50건 = 50개 distinct artwork_id (cache miss / fetch_ok)
        - 다음 50건 = 첫 50개 중 10개 의도적 재요청 (cache hit 유도)
        - 동일 artwork_id 재요청은 30분 이내
        - 결과: cache_hit ≥ 10 PASS

        검증 SQL (권위 runbook §5.3 line 158-168 / 184-193):
        ```sql
        -- 매칭 정확성 분포 검증
        SELECT match_profile_source, slug_in_warm_set, is_saatchi_warm,
               COUNT(*) AS n
        FROM predict_logs
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY 1, 2, 3
        ORDER BY 4 DESC;

        -- year_made_route 분포 검증 (cache_hit ≥ 10 확인)
        SELECT year_made_route, COUNT(*) AS n
        FROM predict_logs
        WHERE timestamp > NOW() - INTERVAL '1 hour'
            AND is_saatchi_warm = true
        GROUP BY 1 ORDER BY 2 DESC;
        -- 기대: cache_hit ≥ 10 / fetch_ok / manual_seed_cache_write / disabled
        ```

        산출물 (gate):
        - 100건 응답 모두 200 OK
        - Saatchi 매칭 정확성 ≥ 95% (위 SQL 매칭 분포 / total ratio)
        - cache_hit ≥ 10건 (위 SQL year_made_route='cache_hit' 의 n ≥ 10)

[ ]  9. CANARY 1% (24h, v3_6_phase3_runbook §Phase 3 gate 통과 후)
        - 트래픽 1% 만 treatment_5pct cohort 라우팅
        - drift / regression 모니터링 24h
        - baseline 수치 (cache_hit_rate / fetch_success / miss_qps avg) 기록
        - Phase 3 gate 통과 시점 = STAGING + Pre-canary 완료 후 진입

[ ] 10. ROLLOUT 5% — D1 / D3 / D7 단계 + reviewer signoff (v3.5 step 4 §3.2)
        - 트래픽 5% routing
        - D1 / D3 / D7 시점 fetch_success / miss_qps / mdape drift 점검
        - D7 gate criterion (v3.5 step 4 §3.2):
          * cache hit ≥ 50%
          * mdape_d7_treatment_vs_control_diff ≤ -0.3%p (개선 입증)
        - reviewer 1+2+3 signoff (§4) — D7 판정 시점 의무
        - D7 미달 → 5% 단계 추가 1주 또는 abort (rollback)

[ ] 11. ROLLOUT 25% → FULL 100% + Final swap (governance rule)
        - 트래픽 25% routing → 검증 → 100% routing
        - 각 단계 monitor / alert wiring 검증 + rollback path 확보 (§5 참조)
        - regression 감지 시 즉시 rollback (oncall 권한)
        - DEFAULT_VARIANT 변경 시 별도 PR 의무 (governance rule):
          primary_predictor.py:86 의 DEFAULT_VARIANT="v3_5_v_year_saatchi_warm"
          변경 = code change → PR review + main merge 의무
        - 100% 적용 후 Phase 5 (운영 안정화) 진입
```

## 4. Reviewer signoff matrix

§3 Step 10 (ROLLOUT 5% D7 판정) 시점 의무 — 3 reviewer signoff:

| Reviewer | 영역 | 검토 항목 |
|---|---|---|
| **Reviewer 1** | API / serving | `primary_server.py` / `primary_predictor.py` / Dockerfile.api / logging schema / cohort gating / batch endpoint / `/api/v1/monitor` payload |
| **Reviewer 2** | Infra / deploy | Dockerfile.api COPY 대상 존재성 / 6 file artifact bundle naming (5 runtime + metrics.json) / `MODEL_DIR` PVC / K8s deployment env / rollback path / runbook 정합 |
| **Reviewer 3** | Data / ML contract | `metrics.json` (P1 evidence — server `/api/v1/model/info` source) / `provenance.json` (`git_dirty=false`) / calibration cell 정확성 / warm artist set 일관성 / source bundle 정합 |

**Deploy contract signoff**: 3 reviewer 모두 signoff 후만 ROLLOUT 25% / FULL 100% 진행.

## 5. Rollback 시나리오 (긴급 운영)

`monitoring/playbooks/` 의 6 drift scenarios + `monitoring/sql/020_alert_rollback_triggers.sql` 의 rollback trigger.

### 5.1 Rollback 트리거 (자동 alert)

| Scenario | Trigger | 권위 대응 (playbook) |
|---|---|---|
| A. Parser drift | `playbooks/scenario-A-parser-drift.md` | upstream parser 점검 + 필요 시 rollback |
| B. Saatchi rate limit | `playbooks/scenario-B-saatchi-rate-limit.md` | rate limit 조정 + fallback |
| C. Cohort gating fail | `playbooks/scenario-C-cohort-gating-fail.md` | **rollback + reload + regression test → 원인분석** (gate 임의 disable 비권고) |
| D. Cache warmup spike | `playbooks/scenario-D-cache-warmup-spike.md` | cap 강화 + 트래픽 throttle |
| E. Model regression | `playbooks/scenario-E-model-regression.md` | **즉시 rollback** + drift report |
| F. Artifact corruption | `playbooks/scenario-F-artifact-corruption.md` | bundle 재학습 + rollback |

### 5.2 Rollback 실행 (사용자 / oncall 권한)

> **Caveat**: 실제 운영 오케스트레이터 (K8s / ECS / Nomad / 운영팀 ops cli 등) 에 따라 명령 다름. 본 절은 환경 별 representative 명령 — **운영팀 표준 SOP 와 정합 의무 / 실제 production 적용 전 dry-run 검증 의무**.

#### 핵심 invariant (모든 환경 공통)

긴급 rollback 의 본질 = 다음 3 가지 동시 적용:

1. `MODEL_VARIANT` env 를 baseline 으로 복귀 (`v3_filtered_tuned`) — 또는 unset (DEFAULT 적용)
2. `ROLLOUT_COHORT` env 를 `control` 로 복귀 (트래픽 100% baseline cohort routing)
3. 모든 worker / pod / instance 재시작 (env 적용 보장)

#### 환경 별 명령

**K8s (Deployment + rolling restart)**:
```bash
kubectl set env deployment/<service> \
  MODEL_VARIANT=v3_filtered_tuned \
  ROLLOUT_COHORT=control
kubectl rollout restart deployment/<service>
kubectl rollout status deployment/<service> --timeout=5m
# 검증: kubectl exec <pod> -- curl localhost:8000/api/v1/model/info | jq '.model_version'
# 기대: "v3-filtered-tuned" 또는 baseline prefix 포함된 model_version 문자열
```

**ECS (task definition + force redeploy)**:
```bash
# task definition 의 environment 영역 update (콘솔 또는 register-task-definition)
# - MODEL_VARIANT=v3_filtered_tuned
# - ROLLOUT_COHORT=control
aws ecs update-service \
  --cluster <cluster> --service <service> \
  --force-new-deployment
aws ecs wait services-stable --cluster <cluster> --services <service>
# 검증: curl https://<service-url>/api/v1/model/info | jq '.model_version'
```

**Docker Compose (ops cli or manual)**:
```bash
# .env 또는 docker-compose.yml 의 environment 영역 update
# - MODEL_VARIANT=v3_filtered_tuned
# - ROLLOUT_COHORT=control
docker compose up -d --no-deps --force-recreate <service>
# 검증: curl http://localhost:8000/api/v1/model/info | jq '.model_version'
```

**운영팀 ops cli (canonical, 해당 시)**:
```bash
# 운영팀 표준 SOP 의 rollback 명령 — 실제 명령은 ops 팀 wiki 참조
ops cli swap rollback --target v3_filtered_tuned --cohort control
```

> **Critical**: 위 명령 모두 본 checklist 의 representative example. **실제 production 적용 전** = 운영팀 표준 SOP 와 정합 + STAGING dry-run 검증 의무. 본 명령 단독 실행 = LLM 권한 X.

### 5.3 Rollback 후 의무

1. drift report 작성 (`docs/` 적재, `cycle_*_rollback_report.md` 형식 권고)
2. failure post-mortem (사용자 / 운영팀)
3. 후속 cycle 진입 (LLM cycle 가능 — readiness report 재작성 / artifact bundle 재학습)

## 6. 후속 작업 시 참조

본 checklist 외 reference:

| 문서 | 역할 |
|---|---|
| `docs/v3_6_swap_readiness_report_20260508.md` | LLM 영역 evidence + Blocked 판정 (본 checklist 의 base) |
| `docs/v3_6_phase3_runbook.md` | **state machine 권위** (STAGING → CANARY 1% → ROLLOUT 5% → 25% → FULL 100%) + preflight |
| `docs/v3_5_step4_drift_monitoring.md` | drift state machine + monitoring spec |
| `docs/v3_6_summary_report.md` / `.html` | v3.6 종합 보고서 (외부 보고용) |
| `docs/v3_6_plan.md` | v3.6 plan (변경 사유 / 산출물 list) |
| `docs/api_reference.html` | API contract reference (PR13b /monitor 필드) |
| `README.md` §Canonical artifact manifest | 운영 v3 모델 reference anchor |
| `monitoring/playbooks/*.md` | 6 drift scenario playbook (권위 대응) |
| `src/visionai/price_engine/api/primary_predictor.py:73-83` | SUPPORTED_VARIANTS config |
| `src/visionai/price_engine/api/primary_server.py:441` | MODEL_DIR resolver |
| `src/visionai/price_engine/api/primary_server.py:64-70` | required env vars (ARTIFACT_VERSION 등) |
| `Dockerfile.api` | runtime image COPY contract (현재 baseline 만 / target 추가 의무) |
| `scripts/v3_6_phase3_dev_test.py` | DEV TEST 실행 entry |
| `scripts/etl_predict_logs.py:18` | `PG_DSN` ETL python 변수명 |

> Note: `docs/cold_rollout_shadow_runbook_20260507.md` 는 Track 2 shadow 영역 — v3.6 swap 직접 권위 X.

## 7. 본 checklist 의 governance

| 항목 | 내용 |
|---|---|
| **Authority boundary** | 본 문서 = 사용자 권한 영역 standalone view (LLM 비권한 명시) |
| **LLM 가능** | checklist 작성 / 정적 검증 / readiness 보고서 (이미 완료) |
| **사용자 의무** | §2 prerequisite 충족 + §3 11 step + §4 reviewer signoff + §5 rollback 권한 |
| **본 cycle 종결 기준** | swap target bundle 학습 + 운영 환경 prerequisite 충족 + reviewer signoff 후 ROLLOUT 25% / FULL 100% 실행 |
| **실패 시 대응** | §5 rollback (placeholder) + drift report + 후속 cycle (LLM cycle 가능) |
| **State machine 권위** | `docs/v3_6_phase3_runbook.md` (STAGING → CANARY 1% → ROLLOUT 5% → 25% → FULL 100%) — 본 checklist 와 충돌 시 권위 runbook 우선 |
| **DEFAULT_VARIANT 변경** | governance rule — code 변경 (`primary_predictor.py:86`) 시 별도 PR + reviewer signoff 의무 |

## 8. 코덱스 자문 history

| 차수 | 내용 |
|---|---|
| 잔존 작업 6번 사전 자문 (2026-05-08) | LLM 가능 / 사용자 영역 분리 + Blocked 판정 + readiness report 권고 |
| 본 checklist 사후 검수 (round 1, 2026-05-08) | P0×2 (state machine 불일치 / runtime image 적재 누락) + P1×7 + P2×2 — 모두 fix 적용 |
| 본 checklist 사후 검수 (round 2, 예정) | round 1 fix 후 재검수 |

## 9. 관련 PR

- PR #27 (`feat: v3.6 production server bundle`) — 본 checklist 의 swap source
- PR #34 (`chore: repo hygiene + canonical asset adoption`) — provenance manifest reference anchor
- PR #38 (`chore: salvage _v5_eval_framework.py`) — eval framework salvage
- PR #41 (`docs: v3.6 swap readiness report`) — 본 checklist 의 base anchor
- PR #40 (`docs: archive retention policy`) — archive cycle policy 종결
