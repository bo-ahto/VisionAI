-- v3.6 Phase 2 — Upstream ops metrics (step4 §2.1)
-- 10 metrics: cache_hit / fetch_success / latency / valid_year / fallback / fetch_5xx
-- + Panel 1 (cache hit rate by hour) + Panel 2 (latency p95 by route)
-- dialect: PostgreSQL 14+

-- ============================================================================
-- Panel 1: cache_hit_rate (시간대별, 7d window)
-- 목표: D1 ≥ 30%, D7 ≥ 50%, D30 ≥ 80%
-- ============================================================================
-- :rollout_cohort 변수 (treatment_5pct | control)
-- 사용: psql -v rollout_cohort="'treatment_5pct'" -f 010_metrics_upstream.sql

-- panel_1_cache_hit_rate_by_hour
SELECT
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) FILTER (WHERE year_made_route = 'cache_hit') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('cache_hit', 'fetch_ok', 'fetch_fail')), 0)
        AS cache_hit_rate,
    COUNT(*) FILTER (WHERE is_saatchi_warm = true) AS eligible_count
FROM predict_logs
WHERE rollout_cohort = 'treatment_5pct'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour;

-- ============================================================================
-- Panel 2: enrichment p95 latency by route (5min window)
-- 목표: hit ≤ 5ms, miss ≤ 600ms
-- ============================================================================

-- panel_2_p95_latency_by_route
SELECT
    year_made_route,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY enrichment_latency_ms) AS p95_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY enrichment_latency_ms) AS p50_ms,
    COUNT(*) AS n
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY year_made_route
ORDER BY p95_ms DESC;

-- ============================================================================
-- enrichment_fetch_success_rate (5min window)
-- 목표: ≥ 98%, warn < 95%, crit < 90%
-- ============================================================================

-- metric_enrichment_fetch_success_rate
SELECT
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_ok') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('fetch_ok', 'fetch_fail')), 0)
        AS enrichment_fetch_success_rate,
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_ok') AS n_ok,
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_fail') AS n_fail
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes';

-- ============================================================================
-- valid_year_range_rate (parse 성공한 year 가 [1800, 2030] 안)
-- 목표: 100%, warn < 99.5%, crit < 98%
-- inverse 정의: 1 - parse_invalid / parse_total
-- ============================================================================

-- metric_valid_year_range_rate (1h window)
SELECT
    1.0 - COUNT(*) FILTER (WHERE year_made_route = 'parse_invalid') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('parse_invalid', 'fetch_ok')), 0)
        AS valid_year_range_rate
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour';

-- ============================================================================
-- fallback_rate_eligible (eligible 요청 중 fallback)
-- 목표: ≤ 5%, warn > 10%, crit > 20%
-- v3.6 PR10b: rate_limited 포함
-- ============================================================================

-- metric_fallback_rate_eligible (24h window)
SELECT
    COUNT(*) FILTER (WHERE year_made_route IN
        ('fetch_fail', 'parse_invalid', 'no_id', 'rate_limited')) * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE is_saatchi_warm = true), 0)
        AS fallback_rate_eligible,
    -- rate_limited 별도 (§3.2.2 metric)
    COUNT(*) FILTER (WHERE year_made_route = 'rate_limited') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE is_saatchi_warm = true), 0)
        AS rate_limited_rate
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- ============================================================================
-- fetch_5xx_rate (saatchi-side issue 감지, 5min window)
-- NOTE: 현재 logging schema 가 5xx 별도 표기 안 함 (year_made_route='fetch_fail'
-- 안에 통합). saatchi_detail_enricher 가 future 에 fetch_status='5xx' 별도
-- column 추가 시 이 query 갱신.
-- 임시: fetch_fail 전체를 5xx 로 간주 (over-estimation, alert 보수적).
-- ============================================================================

-- metric_fetch_5xx_rate (5min window — 임시 정의)
SELECT
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_fail') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN
            ('fetch_ok', 'fetch_fail')), 0)
        AS fetch_5xx_rate_proxy
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes';
