-- v3.6 Phase 2 — Cohort downstream signal metrics (step4 §2.2)
-- has_year_made_rate / cold_year_made_disabled_rate / cohort_assignment_discrepancy_pct
-- + Panel 3 (cohort assignment discrepancy)
-- dialect: PostgreSQL 14+

-- ============================================================================
-- Panel 3: Cohort assignment discrepancy (학습 분포 vs production 분포)
-- 코덱스 step4 §6.2 P0 fix — unmatched 분리.
-- 목표: < 1% (모든 cohort), warn > 1%, crit > 5%
-- ============================================================================

-- panel_3_cohort_discrepancy (v3.6 PR14b' 코덱스 P1 fix: train_dist 를 cohort_baselines table 로 분리)
-- 사용 artifact_version 은 production 의 latest active 또는 query parameter 로 명시.
WITH active_artifact AS (
    SELECT artifact_version
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '1 hour'
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
            WHEN matched = false THEN 'unmatched'  -- 의도된 fallback (step2 §6.2)
            WHEN is_saatchi_warm THEN 'saatchi_warm'
            WHEN matched
                AND match_profile_source = 'saatchi'
                AND slug_in_warm_set = false THEN 'saatchi_cold'
            WHEN matched AND match_profile_source = 'artsy' THEN 'artsy_warm'
            ELSE 'other'  -- catch-all (anomaly)
        END AS cohort,
        COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS rate
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours'
        AND rollout_cohort = 'treatment_5pct'
    GROUP BY 1
)
SELECT
    t.cohort,
    t.expected_rate,
    COALESCE(p.rate, 0)                            AS prod_rate,
    ABS(t.expected_rate - COALESCE(p.rate, 0))     AS diff
FROM train_dist t
LEFT JOIN prod_dist p USING (cohort)
UNION ALL
-- production-only cohort (other = anomaly)
SELECT
    p.cohort,
    NULL                                            AS expected_rate,
    p.rate                                          AS prod_rate,
    NULL                                            AS diff
FROM prod_dist p
WHERE p.cohort = 'other';

-- ============================================================================
-- has_year_made_rate_treatment
-- 목표: rollout traffic 의 ~50% (saatchi-warm 비율)
-- warn: -10%p baseline / crit: -25%p baseline
-- baseline 은 학습 시 saatchi-warm 비율 (~69.7%) — 운영에서 cohort 정의 따라 조정
-- ============================================================================

-- metric_has_year_made_rate_treatment (1h window)
SELECT
    COUNT(*) FILTER (WHERE year_made_used IS NOT NULL) * 1.0 /
        NULLIF(COUNT(*), 0) AS has_year_made_rate
FROM predict_logs
WHERE rollout_cohort = 'treatment_5pct'
    AND timestamp > NOW() - INTERVAL '1 hour';

-- ============================================================================
-- cold_year_made_disabled_rate (gating correctness)
-- 목표: 100% (cold 작가는 모두 disabled), warn < 99%, crit < 95%
-- = 옵션 B disable 의 정합성 검증 (학습/서빙 mismatch 감지)
-- ============================================================================

-- metric_cold_year_made_disabled_rate (1h window)
-- cold = matched + match_profile_source='saatchi' + slug_in_warm_set=false
-- 또는: matched + match_profile_source='artsy' (artsy 는 cohort 외 — disable 대상)
-- 또는: matched=false (unmatched — disable 대상)
SELECT
    COUNT(*) FILTER (WHERE year_made_route = 'disabled') * 1.0 /
        NULLIF(COUNT(*), 0) AS cold_disabled_rate
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
    AND rollout_cohort = 'treatment_5pct'
    AND is_saatchi_warm = false;  -- cohort=False 인 것들이 모두 disabled 여야 함
