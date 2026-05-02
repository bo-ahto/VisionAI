-- v3.6 Phase 2 — Cohort downstream signal metrics (step4 §2.2)
-- has_year_made_rate / cold_year_made_disabled_rate / cohort_assignment_discrepancy_pct
-- + Panel 3 (cohort assignment discrepancy)
-- dialect: PostgreSQL 14+

-- ============================================================================
-- Panel 3: Cohort assignment discrepancy (학습 분포 vs production 분포)
-- 코덱스 step4 §6.2 P0 fix — unmatched 분리.
-- 목표: < 1% (모든 cohort), warn > 1%, crit > 5%
-- ============================================================================

-- panel_3_cohort_discrepancy
-- v3.6 PR14b'' (코덱스 PR14b' review P1 fix):
-- - prod_dist 가 active_artifact 의 artifact_version 만 필터 (window mismatch 차단)
-- - active_artifact / prod_dist 모두 24h window 일치
-- - cohort_baselines 비면 NO_BASELINE 명시 (silent false negative 차단)
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
            WHEN matched
                AND match_profile_source = 'saatchi'
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
)
-- baseline missing 명시: cohort_baselines 비면 status='NO_BASELINE' row 노출
SELECT
    'NO_BASELINE'::text                            AS cohort,
    NULL                                            AS expected_rate,
    NULL                                            AS prod_rate,
    NULL                                            AS diff
WHERE NOT EXISTS (SELECT 1 FROM train_dist)
UNION ALL
SELECT
    t.cohort,
    t.expected_rate,
    COALESCE(p.rate, 0)                            AS prod_rate,
    ABS(t.expected_rate - COALESCE(p.rate, 0))     AS diff
FROM train_dist t
LEFT JOIN prod_dist p USING (cohort)
UNION ALL
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
