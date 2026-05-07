-- v3.6 Phase 2 — Rate-limit gates metrics (step4 §2.1 + step3 §3.2.3)
-- Panel 4-6: miss_qps / concurrent / 5min_burst
-- dialect: PostgreSQL 14+
--
-- NOTE: Rate-limit metric 은 두 source 가 있음:
-- 1. server `/api/v1/monitor` 응답의 fetch_gate (실시간 instant value)
-- 2. predict_logs 의 year_made_route 분포 (시간대별 trend)
--
-- 이 파일은 (2) — predict_logs 기반. (1) 은 Prometheus / scrape job 으로 별도 수집.

-- ============================================================================
-- Panel 4: miss_qps (cache miss → fetch QPS, 1min window)
-- 목표: < 0.5 qps, warn > 1.0 qps, crit > 2.0 qps (auto-suspend)
-- 정의: cache miss → fetch 시도 (fetch_ok + fetch_fail + parse_invalid + rate_limited)
--
-- 1분 window 라 저빈도 환경에서는 noise 큰 metric — 5min rolling 으로 smoothing 권장.
-- ============================================================================

-- panel_4_miss_qps_1min
SELECT
    COUNT(*) FILTER (WHERE year_made_route IN
        ('fetch_ok', 'fetch_fail', 'parse_invalid', 'rate_limited')) * 1.0 / 60.0
        AS miss_qps_1min
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 minute';

-- panel_4_miss_qps_5min_smoothed (안정 alert 평가용)
SELECT
    COUNT(*) FILTER (WHERE year_made_route IN
        ('fetch_ok', 'fetch_fail', 'parse_invalid', 'rate_limited')) * 1.0 / 300.0
        AS miss_qps_5min_avg
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes';

-- ============================================================================
-- Panel 5: concurrent_fetch_max (1min max)
-- 목표: < 5, warn > 10, crit > 20
-- NOTE: concurrent 는 instant 값 — predict_logs 에는 못 측정.
-- /api/v1/monitor 의 fetch_gate.concurrent 를 Prometheus scrape (1초 주기) 후
-- 1분 max 집계. 이 query 는 placeholder (logs 없으면 0).
-- ============================================================================

-- panel_5_concurrent_fetch_max — Prometheus 권장:
-- max_over_time(fetch_gate_concurrent[1m])
-- (이 SQL 은 inline 측정 가능한 proxy 만 — 실 max 는 외부 monitoring 사용)

-- inflight 가 logs 에 있으면 사용 가능 (현재 logging schema 미포함). proxy:
-- 같은 second 안에 fetch 시작한 row 수 → in-flight overlap 추정 (정확 X).
-- Phase 2 후속에서 server `/monitor` scrape 로 대체 권장.

-- ============================================================================
-- Panel 6: 5min_miss_burst (5min cumulative cache miss)
-- 목표: < 50, warn > 100, crit > 200 (auto-suspend trigger)
-- ============================================================================

-- panel_6_5min_miss_burst
SELECT
    COUNT(*) FILTER (WHERE year_made_route IN
        ('fetch_ok', 'fetch_fail', 'parse_invalid', 'rate_limited'))
        AS miss_burst_5min
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes';
