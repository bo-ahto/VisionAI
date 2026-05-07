# v3.6 V_year_saatchi_warm Implementation 보고서

> **작성일**: 2026-05-03
> **branch**: `docs/technical-report-v2`
> **범위**: v3.6 Phase 1 (코드) + Phase 2 (monitoring infra) + Phase 3 (pre-rollout validation)
> **다음**: v3.6 Phase 4 — gated rollout 실행 (~16일 production deploy)

---

## TL;DR

v3.5 step 1 ablation 으로 채택된 **V_year_saatchi_warm variant** (offline overall MdAPE -0.74%p, cold +0.03%p) 의 production 배포 직전까지의 모든 코드 + 운영 인프라 + 검증 절차 종결.

| Phase | 작업 | commit | 상태 |
|-------|------|------:|------|
| **Phase 1** | 코드 (server / predictor / cache / schema) + 단위 test | 16 | ✅ 종결 |
| **Phase 2** | monitoring infra (SQL / Grafana / Prometheus / playbook / ETL) | 14 | ✅ 종결 |
| **Phase 3** | pre-rollout validation (DEV TEST / STAGING / Pre-canary) | 4 | ✅ 종결 |
| **합계** | | **34 commit** | |

전체 통계: **800 / 800 test pass**, lint clean, 코덱스 review 사이클 모두 통과.

---

## 1. Phase 1 — Implementation (코드)

### 1.1 산출물

| 영역 | 파일 | 기능 |
|------|------|------|
| schema | `src/visionai/price_engine/api/primary_schemas.py` | `artwork_id` / `artwork_url` / `year_made` 필드 + `MonitorResponse` / `FetchGateStats` |
| year cache | `src/visionai/price_engine/api/artwork_year_cache.py` | thread-safe LRU + TTL + `FetchGate` (token bucket / cool-down / inflight dedup / warmup-mode) |
| feature builder | `src/visionai/price_engine/api/primary_feature_builder.py` | 32 → 35 features (year_made / has_year_made / work_age) + 옵션 B disable (0.0/0/0.0) |
| predictor | `src/visionai/price_engine/api/primary_predictor.py` | `MODEL_VARIANT` env + 5-file artifact bundle + variant-aware load |
| server | `src/visionai/price_engine/api/primary_server.py` | cohort gating + year resolution + variant-aware metrics + Prometheus exporter |

### 1.2 Phase 1 주요 변경 (commit 시퀀스)

| PR | commit | 내용 |
|----|--------|------|
| PR1 | `9394433` | PredictRequest schema 확장 |
| PR3 | `494cd81` | artwork-level year cache (thread-safe LRU + TTL) |
| PR4 | `2250b5f` | feature builder year 3종 + 옵션 B disable |
| PR3+4 fix | `8c2053d` | alias cleanup + test coverage 보강 |
| PR5+6 | `20d764f` | predictor variant + 5-file bundle + MODEL_VARIANT |
| PR7 | `be3df9d` | server metrics + model_info + model_type variant-aware |
| PR8 | `b3ad573` → `989ef2a` → `4d5b71e` | 단건 cohort gating + fetch 안전화 + timeout + inflight dedup |
| PR10 | `dab0a96` → `abed9d4` → `cdc915c` | logging schema + miss_qps token bucket + spec 정합 |
| PR9 | `b187475` → `ec6e144` | batch endpoint cohort gating + latency 정정 |
| PR11 | `52d8c1c` → `b029c9a` → `3146261` | TestClient + warmup-mode + warmup anchor + /monitor stats |
| PR12 | `82e6e12` | worker_instance_id + /monitor response_model |
| PR13 | `6674501` → `3f42a20` | batch external_collector executor wrap + artist dedup + api_reference 동기화 |

### 1.3 핵심 design

**Cohort authority** (v3.5 step 2 §2.3):
```
is_saatchi_warm = is_matched
              AND match.profile.source == 'saatchi'
              AND artist_slug in warm_artist_slugs
```
→ external_collector 가 채운 profile 은 **비권위** (is_matched=False 면 무시).

**Year resolution** (manual > cache > fetch):
- `manual` (artwork_id 없음) / `manual_seed_cache_write` (cache 등록)
- `cache_hit` / `fetch_ok` / `fetch_fail` / `parse_invalid` / `no_id` / `rate_limited` / `disabled`

**FetchGate 안전망** (v3.5 step 3 §3.2.3 spec 충족):
- concurrent_fetch ≤ 5
- 5min_miss_burst ≤ 50
- 연속 fetch_fail 5건 → 60s cool-down (circuit breaker)
- per-key inflight dedup (stampede 방지)
- 2-mode token bucket: warmup (capacity=1, refill=0.3 qps, 첫 5분) → sustain (capacity=3, refill=0.5 qps)
- timeout 1.5s (spec v3.5 step 2 §291)

**옵션 B disable 의 model-input parity**:
- 비대상 cohort → `year_made=0.0, has_year_made=0, work_age=0.0` (학습 시 fillna(0) 와 정합)

### 1.4 Phase 1 test 통계

- 단위 + 통합 test: **730 통과** (PR1-13b 누적)
- lint: clean
- 코덱스 review 사이클: 12 PR 모두 최종 통과

---

## 2. Phase 2 — Monitoring Infra

### 2.1 산출물

```
monitoring/
├── README.md
├── sql/                          # PostgreSQL DDL + 17 metric query + 7 trigger
│   ├── 001_predict_logs_ddl.sql       (predict_logs 25 col + sold_actuals)
│   ├── 002_v_d7_predict_sold_pairs.sql (D7 MdAPE linkage view)
│   ├── 003_cohort_baselines.sql       (artifact_version 별 train_dist)
│   ├── 010_metrics_upstream.sql       (Panel 1-2 + 5 추가 metric)
│   ├── 011_metrics_cohort.sql         (Panel 3 + has_year_made / cold_disabled)
│   ├── 012_metrics_rate_limit.sql     (Panel 4-6)
│   ├── 013_metrics_mdape.sql          (Panel 7-9 + treatment_vs_control + p50/p90 ratio)
│   ├── 014_metrics_audit.sql          (Panel 10-12)
│   └── 020_alert_rollback_triggers.sql (7 trigger SQL — single source of truth)
├── alerting/                     # Grafana Alerting v10+ provisioning
│   ├── README.md
│   ├── grafana_alerts.yaml             (8 rule: 7 trigger + T2a NO_BASELINE)
│   ├── grafana_contact_points.yaml     (Slack 2 + PagerDuty + secure_settings)
│   └── grafana_notification_policies.yaml (severity → channel routing)
├── grafana/                      # Dashboard
│   ├── README.md
│   ├── dashboard_v3_6_rollout.json     (12 panel, schemaVersion 39)
│   └── dashboards_provider.yaml        (provisioning)
├── prometheus/                   # /api/v1/metrics scrape
│   ├── README.md
│   └── scrape_config.yaml              (recording rules 예시 포함)
└── playbooks/                    # 6 drift scenario + README
    ├── README.md
    ├── scenario-A-parser-drift.md
    ├── scenario-B-saatchi-rate-limit.md
    ├── scenario-C-cohort-gating-fail.md (T2a NO_BASELINE 분기 포함)
    ├── scenario-D-cache-warmup-spike.md
    ├── scenario-E-model-regression.md
    └── scenario-F-artifact-corruption.md

scripts/etl_predict_logs.py       # JSONL → predict_logs ETL (16 test)
```

### 2.2 17 metrics 매핑

| Source | metric | spec § |
|--------|--------|--------|
| upstream | enrichment_fetch_success_rate / cache_hit_rate / latency_p95 (hit, miss) / valid_year_range_rate / fallback_rate_eligible / miss_qps / concurrent_fetch_max / 5min_miss_burst / fetch_5xx_rate | §2.1 (10) |
| downstream | has_year_made_rate / cold_year_made_disabled_rate / cohort_assignment_discrepancy / p50/p90 price ratio / mdape_d7_overall+cold+saatchi_online / treatment_vs_control_diff | §2.2 (8) |
| audit | model_variant_distribution / artifact_version_consistency / cache_epoch_age | §2.3 (3) |

### 2.3 7 rollback / pause trigger (§3.3)

| Trigger | 임계 | severity | for | 행동 |
|---------|------|----------|-----|------|
| T1 5min_miss_burst | > 200 | crit | 5m | pause |
| **T2a NO_BASELINE** | cohort_baselines 부재 | crit | 1m | pause (즉시 알림) |
| T2 cohort discrepancy | > 5% | crit | 10m | pause |
| T3 mdape_d7_cold | > 46% | rollback | 1h | rollback (자동) |
| T4 treatment_vs_control_diff | > +1.0%p | rollback | 1h | rollback (자동) |
| T5 fetch_success_rate | < 90% | rollback | 1h | rollback (자동) |
| T6 cold_disabled_rate | < 95% | rollback | 30m | rollback (gating fail) |
| T7 valid_year_range_rate | < 98% | crit | 30m | pause (parser drift) |

### 2.4 Prometheus exporter (Panel 5)

server `/api/v1/metrics` (PlainTextResponse) 가 11 metric 노출 (gauge 8 + counter 3). label = `worker / server / variant`.

```promql
# Panel 5 — server/variant 합산 후 1min max (worker hard cap=5 회피)
max_over_time(
    sum by (server, variant) (visionai_fetch_gate_concurrent)[1m:]
)
```

### 2.5 ETL idempotency

`scripts/etl_predict_logs.py`:
- byte offset 추적 (재실행 안전)
- partial line 보호 (newline 없는 마지막 line 은 다음 run 으로 미룸)
- `ON CONFLICT (request_id) DO NOTHING`
- malformed line → dead-letter file (counter + 원본 보존)
- alias drop (predicted_krw / price_range_low|high / total_ms)
- `--dry-run` mode (DB 없이 schema 검증)

### 2.6 Phase 2 commit 시퀀스

| PR | commit | 내용 |
|----|--------|------|
| PR14a/b | `7157392` | logging spec 정합 + SQL infrastructure |
| PR14b' | `7ef995f` | matched + train_dist + sold_price + cache_epoch UTC |
| PR14b'' | `9363365` | active_artifact window 일치 + NO_BASELINE explicit |
| PR15 | `a639b13` | ETL JSONL → predict_logs |
| PR15a | `3bd226b` | partial line + dead-letter + psycopg extra |
| PR14c | `29d9279` → `86eaa1a` → `27c6719` | Grafana Alerting + secure_settings + T2a 분리 + traffic-0 분기 |
| PR16 | `c3f62bb` → `72a6a1e` | Prometheus exporter + label escape + PromQL 집계 |
| PR14d | `c1e007c` | Grafana dashboard JSON (12 panel) |
| PR14e | `97bf66b` | drift scenarios playbook (6 markdown) |

---

## 3. Phase 3 — Pre-rollout Validation

### 3.1 산출물

- `scripts/v3_6_phase3_dev_test.py` (synthetic 10K cohort gating + 11 fallback cases + Phase 3 gate 자동 평가)
- `tests/test_v3_6_phase3_dev_test.py` (11 단위 test)
- `docs/v3_6_phase3_runbook.md` (DEV / STAGING / Pre-canary 절차)

### 3.2 11 fallback cases (v3.5 step 2 §4 + parse_invalid 추가)

1. unmatched
2. **unmatched + ext_saatchi 비권위** (cohort authority 정확 검증)
3. artsy_warm
4. saatchi_cold
5. saatchi_warm + manual valid → `manual_seed_cache_write`
6. saatchi_warm + manual no_artwork_id → `manual`
7. saatchi_warm + cache_hit
8. saatchi_warm + fetch_ok
9. saatchi_warm + fetch_fail
10. **saatchi_warm + parse_invalid** (year out of [1800, 2030])
11. saatchi_warm + no artwork_id/url → `no_id`

### 3.3 Phase 3 gate 결과 (mock 환경)

```json
{
  "n_total": 10000,
  "cohort_distribution": {
    "saatchi_warm": 6700, "saatchi_cold": 400,
    "artsy_warm": 2500, "unmatched": 400
  },
  "gating_correctness": 1.0,
  "fallback_cases_pass": 11,
  "fallback_cases_fail": 0,
  "p95_latency_ms": {"fetch_ok": 0.15, "disabled": 0.0, ...},
  "phase3_gate": {
    "fallback_cases_pass": true,
    "gating_correctness_100": true,
    "cache_hit_p95_under_5ms": true,
    "fetch_ok_p95_under_600ms": true
  },
  "passed": true
}
```

### 3.4 Phase 3 commit

| PR | commit | 내용 |
|----|--------|------|
| PR17a/b | `9088232` | DEV TEST script + STAGING/Pre-canary runbook |
| PR17c | `a6db500` | helper drift + parse_invalid + 분포 여유 |
| PR17d | `54d35c0` | runbook 실패 섹션 정합 + docstring |

---

## 4. Logging schema (predict_logs DDL 정합)

| Column | Type | source |
|--------|------|--------|
| request_id | UUID | server `id` (uuid4) |
| timestamp | TIMESTAMPTZ | server `ts` |
| **rollout_cohort** | VARCHAR(32) | env `ROLLOUT_COHORT` (treatment_5pct \| control \| unknown) |
| **matched** | BOOLEAN | `is_matched` |
| match_profile_source | VARCHAR(16) | match.profile.source (saatchi / artsy / NULL — PR10b 정합) |
| slug_in_warm_set | BOOLEAN | predictor.is_warm_artist |
| is_saatchi_warm | BOOLEAN | cohort 결정 결과 |
| external_collector_source | VARCHAR(16) | sources_used[0] / 'none' |
| year_made_route | VARCHAR(32) | 9 enum (manual / manual_seed_cache_write / cache_hit / fetch_ok / fetch_fail / no_id / parse_invalid / disabled / rate_limited) |
| year_made_used | INT | resolve 결과 |
| enrichment_latency_ms | FLOAT | year resolve 단계 측정 |
| predict_total_latency_ms | FLOAT | item end-to-end (PR9b) |
| artwork_id / artwork_url | VARCHAR | request 그대로 |
| **predicted_price_krw** / range_low_krw / range_high_krw | INT | spec column 이름 (PR14a) |
| confidence_grade | VARCHAR(2) | A / B / C / D |
| model_variant | VARCHAR(64) | predictor.variant |
| artifact_version / warm_artist_slugs_version / rollout_rule_version | VARCHAR | env var (deploy pipeline 주입) |
| server_instance | VARCHAR(64) | env `SERVER_INSTANCE` |
| **worker_instance_id** | VARCHAR(64) | uuid4 hex (PR12 — multi-worker 식별) |
| cache_epoch | VARCHAR(32) | UTC `YYYYMMDDTHHMMZ` (lifespan startup) |

기존 client 호환을 위해 alias dual-write (`predicted_krw / price_range_low|high / total_ms`) 도 logging row 에 포함 (deprecated, ETL 단계 drop).

---

## 5. 코덱스 review 결과 정리

총 **17 review 사이클** (각 PR + 보정 commit 별):

| Phase | 통과 | 조건부 | 불통과 (보정 후 통과) |
|-------|-----:|-------:|----------------------:|
| Phase 1 | 4 | 6 | 2 |
| Phase 2 | 2 | 5 | 0 |
| Phase 3 | 1 | 1 | 0 |
| **합** | **7** | **12** | **2** |

모든 코덱스 P0/P1/P2 issue 종결. 잔여 **Nit** (별도 PR backlog):
- runbook 의 일부 modal verb 정정 (소소)
- 운영 환경별 datasource UID templating (PR14d 시 명시)

---

## 6. 통계

| 항목 | 값 |
|------|---:|
| 총 commit | 34 |
| 누적 test pass | 800 |
| lint errors | 0 |
| monitoring/ 파일 | 26 |
| 신규 dir | 5 (`monitoring/{sql,alerting,grafana,prometheus,playbooks}`) |
| spec 정합 컬럼 (predict_logs) | 25 |
| Grafana panel | 12 |
| Grafana alert rule | 8 (7 trigger + T2a NO_BASELINE) |
| drift scenario playbook | 6 |
| Prometheus metric | 11 (gauge 8 + counter 3) |

---

## 7. 다음 단계 — Phase 4 (gated rollout)

`docs/v3_6_plan.md` §6 + `docs/v3_5_step4_drift_monitoring.md` §3 state machine 그대로 운영.

### 7.1 일정 (~16일)

```
CANARY 1% (24h) ──┐
   │ gate (24h)   │
   ▼              │
ROLLOUT 5% (D1/D3/D7 체크포인트, 7d)
   │ gate (D7)   │
   ▼             │
ROLLOUT 25% (24h)
   │              │
   ▼              │
FULL 100% (1주)  ─┘
```

### 7.2 D7 gate (ROLLOUT 5% 승급)

- cache_hit_rate ≥ 50%
- mdape_d7_treatment_vs_control_diff ≤ -0.3%p (offline -0.74 향)
- mdape_d7_cold ≤ 43%
- crit alert 누적 ≤ 1건 (24h 내 즉시 해결)

### 7.3 자동 rollback 발동 시 (§3.3 trigger)

post-mortem 24h 내 RCA + 재발 방지 PR. 3회 자동 rollback 시 v3.6 abort.

---

## 관련 문서

- spec plan: `docs/v3_6_plan.md`
- v3.5 step 1-4: `docs/v3_5_step1_cohort_gating_results.md` ~ `docs/v3_5_step4_drift_monitoring.md`
- Phase 3 runbook: `docs/v3_6_phase3_runbook.md`
- monitoring infra: `monitoring/`
- v3.0 진단 보고서 (§15 v3.4-v3.6 부록): `docs/v3_0_diagnostics_보고서_20260430.html`
