-- v3.6 Phase 2 — Rollback / pause trigger 단일 표 (step4 §3.3)
-- 7 trigger row, alert manager polling 1분 주기 평가 권장.
-- dialect: PostgreSQL 14+
--
-- 행동 분류:
-- - pause: rollout 단계 유지, fetch suspend / 조사
-- - rollback: 단계 후퇴 (자동 / manual confirm)
-- - 자동: 즉시 액션, 수동: ops 확인 후 트리거
--
-- 각 query 는 boolean (트리거 발동 여부) 또는 측정값 (임계 비교) 반환.
-- alert manager 는 결과를 임계와 비교 → fire / resolve.

-- ============================================================================
-- Trigger 1: 5min_miss_burst > 200 (5분 지속) → 자동 pause (fetch suspend 5분)
--
-- NOTE (v3.6 PR14b' 코덱스 P1): "5분 지속" 은 alert manager 의 `for: 5m` 옵션
-- 으로 보강. 이 SQL 은 단발 평가 (현재 5min window 누적값) → alert manager 가
-- 연속 5분간 임계 초과 유지 시에만 fire. PR14c 에서 `for: 5m` 명시 필요.
-- ============================================================================

-- trigger_1_5min_miss_burst_critical
SELECT
    COUNT(*) FILTER (WHERE year_made_route IN
        ('fetch_ok', 'fetch_fail', 'parse_invalid', 'rate_limited'))
        AS miss_burst_5min,
    CASE
        WHEN COUNT(*) FILTER (WHERE year_made_route IN
            ('fetch_ok', 'fetch_fail', 'parse_invalid', 'rate_limited')) > 200
        THEN 'TRIGGER_PAUSE'
        ELSE 'OK'
    END AS action
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '5 minutes';

-- ============================================================================
-- Trigger 2: cohort_assignment_discrepancy_pct > 5% → 자동 pause + manual rollback
-- ============================================================================

-- trigger_2_cohort_discrepancy_critical (24h window)
-- v3.6 PR14b'/14b'' (코덱스 P1 fix):
-- - cohort_baselines 동적 조회 (train_dist 분리)
-- - active_artifact + prod_dist 둘 다 24h window 일치 (mixed traffic 차단)
-- - prod_dist 도 artifact_version filter
-- - baseline missing → 'NO_BASELINE' 명시 (silent false negative 차단)
WITH active_artifact AS (
    SELECT artifact_version
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours'
        AND rollout_cohort = 'treatment_5pct'
    GROUP BY artifact_version
    ORDER BY COUNT(*) DESC
    LIMIT 1
),
train_dist AS (
    SELECT b.cohort, b.expected_rate
    FROM cohort_baselines b
    JOIN active_artifact a USING (artifact_version)
),
prod_dist AS (
    SELECT
        CASE
            WHEN matched = false THEN 'unmatched'
            WHEN is_saatchi_warm THEN 'saatchi_warm'
            WHEN matched AND match_profile_source = 'saatchi'
                AND slug_in_warm_set = false THEN 'saatchi_cold'
            WHEN matched AND match_profile_source = 'artsy' THEN 'artsy_warm'
            ELSE 'other'
        END AS cohort,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS rate
    FROM predict_logs p
    JOIN active_artifact a USING (artifact_version)  -- PR14b'' window 일치
    WHERE p.timestamp > NOW() - INTERVAL '24 hours'
        AND p.rollout_cohort = 'treatment_5pct'
    GROUP BY 1
),
baseline_check AS (
    SELECT EXISTS (SELECT 1 FROM train_dist) AS has_baseline
),
discrepancy AS (
    SELECT MAX(ABS(t.expected_rate - COALESCE(p.rate, 0))) AS max_discrepancy
    FROM train_dist t
    LEFT JOIN prod_dist p USING (cohort)
)
SELECT
    d.max_discrepancy,
    CASE
        WHEN NOT b.has_baseline THEN 'NO_BASELINE'  -- silent OK 차단
        WHEN d.max_discrepancy > 0.05 THEN 'TRIGGER_PAUSE'
        ELSE 'OK'
    END AS action
FROM discrepancy d, baseline_check b;

-- ============================================================================
-- Trigger 3: mdape_d7_cold > 46% → 자동 rollback (no manual confirm)
-- 코덱스 step4 §3.3 — cold 보호 핵심 trigger
-- ============================================================================

-- trigger_3_mdape_cold_critical
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100
        AS mdape_cold_pct,
    CASE
        WHEN PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 > 46
        THEN 'TRIGGER_ROLLBACK'
        ELSE 'OK'
    END AS action
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
    AND is_saatchi_warm = false
    AND rollout_cohort = 'treatment_5pct';

-- ============================================================================
-- Trigger 4: mdape_d7_treatment_vs_control_diff > +1.0%p → 자동 rollback
-- ============================================================================

-- trigger_4_treatment_vs_control_critical
WITH per_cohort AS (
    SELECT
        rollout_cohort,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100
            AS mdape_pct
    FROM v_d7_predict_sold_pairs
    WHERE sold_at > NOW() - INTERVAL '7 days'
    GROUP BY rollout_cohort
)
SELECT
    (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'treatment_5pct')
    - (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'control')
        AS diff_pct,
    CASE
        WHEN (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'treatment_5pct')
             - (SELECT mdape_pct FROM per_cohort WHERE rollout_cohort = 'control') > 1.0
        THEN 'TRIGGER_ROLLBACK'
        ELSE 'OK'
    END AS action;

-- ============================================================================
-- Trigger 5: enrichment_fetch_success_rate < 90% (1h 지속) → 자동 rollback
-- ============================================================================

-- trigger_5_fetch_success_critical (1h window)
SELECT
    COUNT(*) FILTER (WHERE year_made_route = 'fetch_ok') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('fetch_ok', 'fetch_fail')), 0)
        AS fetch_success_rate,
    CASE
        WHEN COUNT(*) FILTER (WHERE year_made_route = 'fetch_ok') * 1.0 /
             NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('fetch_ok', 'fetch_fail')), 0) < 0.90
        THEN 'TRIGGER_ROLLBACK'
        ELSE 'OK'
    END AS action
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour';

-- ============================================================================
-- Trigger 6: cold_year_made_disabled_rate < 95% → 자동 rollback (gating fail)
-- ============================================================================

-- trigger_6_cold_disabled_critical (1h window)
SELECT
    COUNT(*) FILTER (WHERE year_made_route = 'disabled') * 1.0 /
        NULLIF(COUNT(*), 0)                                AS cold_disabled_rate,
    CASE
        WHEN COUNT(*) FILTER (WHERE year_made_route = 'disabled') * 1.0 /
             NULLIF(COUNT(*), 0) < 0.95
        THEN 'TRIGGER_ROLLBACK'
        ELSE 'OK'
    END AS action
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
    AND rollout_cohort = 'treatment_5pct'
    AND is_saatchi_warm = false;

-- ============================================================================
-- Trigger 7: valid_year_range_rate < 98% → 자동 pause (parser drift 의심)
-- ============================================================================

-- trigger_7_parser_drift_critical (1h window)
SELECT
    1.0 - COUNT(*) FILTER (WHERE year_made_route = 'parse_invalid') * 1.0 /
        NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('parse_invalid', 'fetch_ok')), 0)
        AS valid_year_range_rate,
    CASE
        WHEN 1.0 - COUNT(*) FILTER (WHERE year_made_route = 'parse_invalid') * 1.0 /
             NULLIF(COUNT(*) FILTER (WHERE year_made_route IN ('parse_invalid', 'fetch_ok')), 0) < 0.98
        THEN 'TRIGGER_PAUSE'
        ELSE 'OK'
    END AS action
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour';
