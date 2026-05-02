-- v3.6 Phase 2 — MdAPE D7 metrics (step4 §2.2 + §6.2)
-- Panel 7-9: overall / cold / saatchi_online + treatment_vs_control_diff
-- dialect: PostgreSQL 14+
-- view: v_d7_predict_sold_pairs (002_v_d7_predict_sold_pairs.sql)

-- ============================================================================
-- Panel 7: Overall MdAPE D7 (treatment vs control)
-- 목표: ≤ 9.7%, warn > 10.5%, crit > 11.5%
-- ============================================================================

-- panel_7_mdape_d7_overall
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100 AS mdape_pct,
    COUNT(*)                                                          AS n_pairs
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
GROUP BY rollout_cohort
ORDER BY rollout_cohort;

-- ============================================================================
-- Panel 8: cold cohort 만 (rollout 의 핵심 보호 지표)
-- 목표: ≤ 43%, warn > 44%, crit > 46% (cold protect fail → auto-rollback)
-- ============================================================================

-- panel_8_mdape_d7_cold
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100
        AS mdape_cold_pct,
    COUNT(*)                                                          AS n_pairs
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
    AND is_saatchi_warm = false
GROUP BY rollout_cohort
ORDER BY rollout_cohort;

-- ============================================================================
-- Panel 9: saatchi_online (sold_actuals.source 활용)
-- 목표: ≤ 9.7%, warn > 10.5%, crit > 11.5%
-- ============================================================================

-- panel_9_mdape_d7_saatchi_online
SELECT
    rollout_cohort,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_pct_error) * 100
        AS mdape_saatchi_online_pct,
    COUNT(*)                                                          AS n_pairs
FROM v_d7_predict_sold_pairs
WHERE sold_at > NOW() - INTERVAL '7 days'
    AND sold_source = 'saatchi'
GROUP BY rollout_cohort
ORDER BY rollout_cohort;

-- ============================================================================
-- Panel 12 (treatment vs control diff — rollout gate)
-- 목표: -1.0%p ~ -0.3%p (개선), warn > +0.3%p, crit > +1.0%p (rollback)
-- ============================================================================

-- panel_12_treatment_vs_control_diff
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
    AS mdape_d7_treatment_vs_control_diff;

-- ============================================================================
-- p50 / p90 predicted price ratio (D7 vs D-7) — drift 감지 (§2.2 metric 14, 15)
-- 목표: p50 0.97~1.03, p90 0.95~1.05
-- warn: p50 ±5% / p90 ±10%, crit: p50 ±10% / p90 ±15%
-- ============================================================================

-- metric_p50_p90_predicted_price_ratio_d7_dminus7
WITH d7 AS (
    SELECT
        rollout_cohort,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY predicted_price_krw) AS p50,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY predicted_price_krw) AS p90
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '7 days'
        AND timestamp <= NOW()
    GROUP BY rollout_cohort
),
dminus7 AS (
    SELECT
        rollout_cohort,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY predicted_price_krw) AS p50,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY predicted_price_krw) AS p90
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '14 days'
        AND timestamp <= NOW() - INTERVAL '7 days'
    GROUP BY rollout_cohort
)
SELECT
    d7.rollout_cohort,
    d7.p50 / NULLIF(d.p50, 0)        AS p50_ratio_d7_dminus7,
    d7.p90 / NULLIF(d.p90, 0)        AS p90_ratio_d7_dminus7
FROM d7
JOIN dminus7 d USING (rollout_cohort);
