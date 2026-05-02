# v3.6 Monitoring Infrastructure

v3.5 step 4 (`docs/v3_5_step4_drift_monitoring.md`) spec 의 실 구현. v3.6 Phase 2 산출물.

## 디렉토리 구조

```
monitoring/
├── README.md                  # 이 파일 — 개요 + 운영 절차
├── sql/                       # PostgreSQL DDL / view / metric query
│   ├── 001_predict_logs_ddl.sql      # predict_logs + sold_actuals 테이블
│   ├── 002_v_d7_predict_sold_pairs.sql  # D7 MdAPE 계산용 view (linkage rule)
│   ├── 010_metrics_upstream.sql      # Panel 1-2 (cache_hit / latency)
│   ├── 011_metrics_cohort.sql        # Panel 3 (cohort discrepancy)
│   ├── 012_metrics_rate_limit.sql    # Panel 4-6 (miss_qps / concurrent / 5min_burst)
│   ├── 013_metrics_mdape.sql         # Panel 7-9 + treatment vs control diff
│   ├── 014_metrics_audit.sql         # Panel 10-12 (variant 분포 / artifact 일관성 / cache_epoch age)
│   └── 020_alert_rollback_triggers.sql  # §3.3 rollback trigger 단일 표 (7 trigger)
└── (이후 PR14c) alerts/, playbooks/, grafana/
```

## SQL dialect

PostgreSQL 14+ (코덱스 step4 §6.2 fix 명시). `FILTER (WHERE ...)`, `INTERVAL '7 days'`, `PERCENTILE_CONT(...) WITHIN GROUP`, `DISTINCT ON` 사용.
BigQuery / Snowflake 로 warehouse 변경 시 별도 변환 필요.

## 적재 source

`predict_logs` 의 row 는 server `_log_prediction()` 이 JSONL 로 작성한 record 를 ETL 로 적재. server 가 직접 PostgreSQL 에 INSERT 하지 않음 (decoupled).

JSONL → PostgreSQL ETL (예: Vector / Fluent Bit / Logstash 또는 cron job) 은 Phase 2 의 별도 작업.

## 17 metrics 매핑 (step4 §2)

### 2.1 Upstream ops (10)
1. `enrichment_fetch_success_rate` — 010 panel (cache_hit_rate 와 함께)
2. `cache_hit_rate` — 010 panel 1
3. `enrichment_p95_latency_ms_hit` — 010 panel 2
4. `enrichment_p95_latency_ms_miss` — 010 panel 2
5. `valid_year_range_rate` — 010 추가 query
6. `fallback_rate_eligible` — 010 추가 query (rate_limited 포함)
7. `miss_qps` — 012 panel 4
8. `concurrent_fetch_max` — 012 panel 5 (server `/monitor` 의 fetch_gate 도 source)
9. `5min_miss_burst` — 012 panel 6
10. `fetch_5xx_rate` — 010 추가 (saatchi-side issue)

### 2.2 Downstream signal (8)
11. `has_year_made_rate_treatment` — 011 추가
12. `cold_year_made_disabled_rate` — 011 추가 (gating correctness)
13. `cohort_assignment_discrepancy_pct` — 011 panel 3
14. `p50_predicted_price_ratio_d7_dminus7` — 013 추가
15. `p90_predicted_price_ratio_d7_dminus7` — 013 추가
16. `mdape_d7_saatchi_online` — 013 panel 9
17. `mdape_d7_cold` — 013 panel 8
18. `mdape_d7_treatment_vs_control_diff` — 013 panel 12

### 2.3 Audit (3)
19. `model_variant_distribution` — 014
20. `artifact_version_consistency` — 014
21. `cache_epoch_age_hours` — 014

## Rollback trigger (step4 §3.3, 7 row 표)

`020_alert_rollback_triggers.sql` 의 single source of truth. 각 trigger 는 alert manager 가 polling 으로 평가 (1분 주기 권장). 자동 rollback / pause / fetch suspend 는 alert payload → ops 자동화 (Phase 2 alerts/ 단계).

## Phase 2 후속 PR

- **PR14c** alert config (Slack / PagerDuty alertmanager YAML)
- **PR14d** Grafana dashboard JSON (12 panel)
- **PR14e** 6 drift scenarios playbook (markdown)
- **PR15** ETL (JSONL → PostgreSQL) batch job

## 검증 절차 (코덱스 권장)

1. SQL 파일 별 syntax check: `psql --variable ON_ERROR_STOP=1 -f <file>` (test DB)
2. View 결과 sanity: 학습 데이터 backfill → 같은 cohort 분포 비교
3. Rollback trigger backtest: v3.5 step 1 ablation 결과 (overall -0.74%p / cold +0.03%) 가 trigger 임계 안 침범 확인

## 관련 문서

- spec: `docs/v3_5_step4_drift_monitoring.md`
- logging schema: `docs/v3_5_step3_enrichment_tradeoff.md` §3.2.1
- code: `src/visionai/price_engine/api/primary_server.py` (`_log_prediction`)
