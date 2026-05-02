# v3.6 Phase 3 — Pre-rollout Validation Runbook

**spec**: `docs/v3_6_plan.md` §5
**소요**: 약 3일 (DEV 0.5d + STAGING 1.5d + Pre-canary 0.5d + buffer)

Phase 1 (코드 PR1-13) + Phase 2 (monitoring infra PR14a-e + PR15a + PR16a) 종결 후 production rollout (Phase 4) 진입 직전 검증.

## Phase 3 gate (§5.4 — 모두 PASS 필요)

| Gate | 기준 | Source |
|------|------|--------|
| **DEV TEST** | 10 fallback case 100% PASS + cohort gating 100% (10K) + latency 충족 | scripts/v3_6_phase3_dev_test.py |
| **STAGING** | real saatchi 1K request 24h 안정 + 12 panel 정상 + 6 alert baseline | 본 runbook §5.2 |
| **Pre-canary smoke** | manual 100건 + saatchi 매칭 100명 sample + cache fill ≥ 10건 | 본 runbook §5.3 |

---

## 5.1 DEV TEST (소요 0.5d)

### 환경
- DEV 워크스테이션 (개발자 local 또는 CI runner)
- DB / saatchi 의존성 X (모두 mock)

### 절차
```bash
# 1. v3.6 코드 baseline 확인
git rev-parse HEAD  # 97bf66b 이후 commit

# 2. 단위 + 통합 test
pytest tests/price_engine/  # 730+ tests
pytest tests/test_etl_predict_logs.py  # 16 tests
pytest tests/test_v3_6_phase3_dev_test.py  # 11 tests

# 3. Phase 3 DEV TEST script
python -m scripts.v3_6_phase3_dev_test --n 10000 --seed 42
# 기대 출력: "passed": true (exit 0)
```

### 산출물
- 모든 pytest GREEN (730 + 16 + 11 = 757 tests)
- DEV TEST script JSON 의 `phase3_gate.fallback_cases_pass=true`,
  `gating_correctness_100=true`, latency 모두 true

### 실패 시
- 단위 test 실패: 해당 file 의 단위 test commit 추적 (git bisect) → fix → 재실행.
- DEV TEST gate 실패: helper logic (`_decide_saatchi_warm_cohort` /
  `_resolve_year_sync`) 또는 PRODUCTION_DISTRIBUTION sanity 점검.

---

## 5.2 STAGING (소요 1.5d, 24h 안정 포함)

### 환경
- production-like (별도 staging deploy)
- real saatchi traffic 일부 (1K request 가중)
- staging Postgres + Grafana + Prometheus instance

### Pre-flight checklist
- [ ] `monitoring/sql/001_predict_logs_ddl.sql` ~ `020_alert_rollback_triggers.sql`
      모두 staging DB 에 적용됨
- [ ] `monitoring/sql/003_cohort_baselines.sql` 의 초기 row 적재
      (`integrated_v3_5_v_year_saatchi_warm` 4 cohort)
- [ ] `monitoring/grafana/dashboard_v3_6_rollout.json` provisioning
      적용 — Datasource UID 환경별 치환
- [ ] `monitoring/alerting/grafana_alerts.yaml` 적용 — env vars 주입
      (SLACK_WEBHOOK_ML_ALERTS / PAGERDUTY_INTEGRATION_KEY)
- [ ] `monitoring/prometheus/scrape_config.yaml` 의 scrape job 추가
- [ ] `scripts/etl_predict_logs.py` cron 적재 (5min interval)
- [ ] server env: `MODEL_VARIANT=v3_5_v_year_saatchi_warm`,
      `ROLLOUT_COHORT=treatment_5pct`, `ARTIFACT_VERSION` 등

### 절차 (1K request 검증)
1. **트래픽 주입**: production replay traffic 또는 synthetic batch
   (`scripts/v3_6_phase3_dev_test.py` 의 generate_dataset 활용 가능)
2. **24h 모니터링**: Grafana 12 panel + 6 alert baseline 측정
3. **정합성 검증**:
   ```sql
   -- predict_logs row 수 ≥ 1000
   SELECT COUNT(*) FROM predict_logs
   WHERE timestamp > NOW() - INTERVAL '24 hours'
       AND rollout_cohort = 'treatment_5pct';

   -- cohort 분포 sanity (학습 baseline ±5%p)
   -- 011_metrics_cohort.sql Panel 3 query 실행
   ```

### 12 panel 정상 표시 검증

| Panel | 정상 조건 | 비정상 시 |
|-------|---------|---------|
| 1. cache_hit_rate by hour | 7d ≥ 30% | 0% — ETL ingest fail |
| 2. p95 latency by route | hit ≤ 5ms, miss ≤ 600ms | 초과 시 saatchi 응답 lag |
| 3. cohort discrepancy | 모든 cohort diff < 5% | NO_BASELINE 시 T2a alert |
| 4. miss_qps | < 0.5 sustained | spike 발생 시 token bucket 동작 |
| 5. concurrent_fetch_max | < 5 (Prometheus) | exporter 부재 시 빈 panel |
| 6. 5min_miss_burst | < 50 | 200 초과 시 T1 fire |
| 7-9. MdAPE D7 | sold_actuals 적재 후만 | empty result 정상 (D7 미도달) |
| 10. variant 분포 | rollout 정책 정합 | mix 시 deploy bug |
| 11. artifact_version 일관 | 0 row | mix row 발견 시 즉시 점검 |
| 12. treatment vs control diff | (D7 후만) | 1주 동안 빈 결과 |

### 6 alert baseline (D1 24h 안정)
- T1 (5min_miss_burst > 200): D1 fire 0건
- T2 (cohort discrepancy > 5%): D1 fire 0건 (baseline 정상 시)
- T2a (NO_BASELINE): cohort_baselines 적재 후 fire 0건
- T3-7: D1 sold_actuals 적재 부족으로 fire 0건 (정상)

### 산출물
- 24h 동안 crit alert 누적 0건 (또는 1건 이내 즉시 해결)
- Panel 1-6, 10-11 데이터 표시 (upstream + cohort + audit — D1 측정 가능)
- Panel 7-9, 12 (MdAPE D7 + treatment_vs_control) — STAGING 24h 만으로는
  sold_actuals 적재 부족 → **빈 결과 정상**. 본 panel 들의 정상 표시는 Phase 4
  D7 이후 검증 (CANARY 24h + ROLLOUT 5% D1/D3/D7 단계).
- baseline 수치 (D1 cache hit rate / fetch_success rate / miss_qps avg) 기록

### 실패 시
- T1 fire (miss_burst): warmup-mode 정상 동작 + traffic burst 진단.
- 12 panel 빈 결과: ETL `etl_predict_logs.py` 의 offset / dead_letter 점검.
- alert 발사 누락: contact_points env vars / Grafana provisioning reload 점검.

---

## 5.3 Pre-canary smoke (소요 0.5d)

### 환경
- STAGING 과 동일 (직후)
- internal team manual access

### 절차

#### A. Manual request 100건
```bash
# /api/v1/predict 100건 — 다양한 cohort 분포
for i in $(seq 1 100); do
  curl -X POST http://staging-api:8000/api/v1/predict \
    -H 'Content-Type: application/json' \
    -d "{\"artist_name\":\"<saatchi_warm_or_other>\", \
         \"width_cm\":50, \"height_cm\":50, \
         \"medium\":\"oil\", \"target_market\":\"gallery\"}"
done
```

기대:
- 모든 응답 200 OK
- `model_info.model_type` 가 variant prefix (`xgboost_v3_5_v_year_saatchi_warm` 또는
  `catboost_v3_5_v_year_saatchi_warm`)

#### B. Saatchi 매칭 정확성 (100명 sample)
- Saatchi 작가 100명 (warm set 외부 + 내부 혼합) 의 `artist_name` 으로 /predict 요청
- 응답의 `is_known_artist` 와 `match_profile_source` 가 spec 정합:
  - warm set 내부: matched=True, source=saatchi
  - warm set 외부: matched=True, source=saatchi (cohort=False)
  - 외부 + non-saatchi: matched=True, source=artsy
  - 미등록: matched=False

```sql
-- Pre-canary smoke 의 predict_logs 분석
SELECT
    match_profile_source,
    slug_in_warm_set,
    is_saatchi_warm,
    COUNT(*) AS n
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1, 2, 3
ORDER BY 4 DESC;
```

#### C. Cache fill rate (D1 추정)
- 100건 중 saatchi_warm 약 67% 예상 (PRODUCTION_DISTRIBUTION).
- 그 중 `artwork_id` 있는 요청만 cache 등록 가능.
- 첫 시간: cache_hit_rate ≈ 0% (cold start), 누적 후 점진 상승.
- spec §5.4 gate: cache_hit ≥ 10건 이면 PASS (warm-up 동작 확인).

**cache hit 유도 절차** (v3.6 PR17c — 코덱스 P2): 1시간 smoke 안에 cache_hit
≥ 10 자연 보장 안 됨. 절차 명시:
1. 첫 50건은 50개 distinct `artwork_id` (warm-up — 모두 cache miss / fetch_ok).
2. 다음 50건은 첫 50개 중 10개를 의도적으로 재요청 (cache hit 유도).
3. 동일 `artwork_id` 재요청 30분 안 진행 (TTL 7d 안 — 자연 cache hit).
4. 결과 query 에서 `cache_hit ≥ 10` 확인 → PASS.

```sql
SELECT
    year_made_route,
    COUNT(*) AS n
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
    AND is_saatchi_warm = true
GROUP BY 1
ORDER BY 2 DESC;
```

기대 분포 (100 saatchi_warm 기준):
- `manual_seed_cache_write`: client 가 year_made 보낸 비율 × ~70%
- `fetch_ok`: artwork_url 으로 saatchi fetch — 첫 시도
- `cache_hit`: 같은 artwork_id 재요청 — 자연 발생 ≥ 10건
- `disabled`: cohort=False 인 30%

### 산출물
- 100건 응답 모두 200 OK
- saatchi 매칭 정확성 ≥ 95% (spec 비공식 기준 — production 검증)
- cache_hit ≥ 10건 (spec §5.4 gate)

### 실패 시
- 매칭 정확성 < 95%: artist_matcher 의 fuzzy match threshold 또는 normalize_name
  검토.
- cache_hit < 10건: artwork_id field 가 client 측에서 누락되거나, Saatchi URL
  pattern mismatch 가능성. `_extract_artwork_id_from_url` 로직 점검.

---

## Phase 3 gate 통과 시

1. STAGING baseline 수치 (cache_hit_rate, fetch_success, miss_qps) 를
   `monitoring/sql/003_cohort_baselines.sql` 의 비고 또는 별도 wiki 에 기록.
2. Phase 4 (Gated rollout) 진입 — `docs/v3_6_plan.md` §6 의 state machine 시작.
3. CANARY 1% (24h) 부터 트래픽 일부 (1%) 만 treatment_5pct cohort 라우팅.

## Phase 3 gate 실패 시

1. 실패 원인 식별 (위 §5.1/5.2/5.3 의 "실패 시" 절차 따름).
2. 필요 시 코드 PR (Phase 1 변경 영향 범위) 또는 monitoring infra 변경.
3. Phase 3 재실행 — DEV TEST 부터 다시.
4. 3회 이상 재실행 시 v3.6 abort 검토 (`docs/v3_6_plan.md` §8 참조).

---

## 관련 문서
- spec plan: `docs/v3_6_plan.md`
- v3.5 step 4 monitoring: `docs/v3_5_step4_drift_monitoring.md`
- v3.5 step 2 serve-path spec: `docs/v3_5_step2_serve_path_spec.md`
- DEV TEST script: `scripts/v3_6_phase3_dev_test.py`
- monitoring infra: `monitoring/`
