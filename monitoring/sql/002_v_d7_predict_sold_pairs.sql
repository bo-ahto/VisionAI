-- v3.6 Phase 2 — D7 MdAPE 계산용 view (linkage rule)
-- spec: docs/v3_5_step4_drift_monitoring.md §6.1.1 (코덱스 P0 fix)
-- dialect: PostgreSQL 14+

-- 같은 artwork 가 여러 번 예측되거나 여러 번 sold 된 경우 attribution rule:
-- 각 sold_actual 마다 그 sale **직전의 가장 최근 prediction 1건만** 사용.
--
-- 규칙:
-- 1. p.timestamp <= s.sold_at (prediction 이 sale 이전)
-- 2. 30 days window (오래된 prediction 제외)
-- 3. DISTINCT ON (artwork_id, sold_at) ORDER BY p.timestamp DESC → 최근 1건
-- 4. 같은 prediction 이 여러 sale 에 사용 가능 (resold 등) — 의도된 동작
-- 5. view 가 sold_source 노출 (Panel 9 saatchi_online MdAPE 계산용)

CREATE OR REPLACE VIEW v_d7_predict_sold_pairs AS
SELECT DISTINCT ON (s.artwork_id, s.sold_at)
    p.request_id,
    p.predicted_price_krw,
    p.rollout_cohort,
    p.is_saatchi_warm,
    p.match_profile_source,
    p.model_variant,
    p.artifact_version,
    p.timestamp                                AS predict_at,
    s.sold_at,
    s.sold_price_krw,
    s.source                                   AS sold_source,
    s.artist_slug,
    s.sold_at - p.timestamp                    AS prediction_to_sale_lag,
    ABS(p.predicted_price_krw - s.sold_price_krw) * 1.0
        / NULLIF(s.sold_price_krw, 0)          AS abs_pct_error
FROM sold_actuals s
JOIN predict_logs p
    ON s.artwork_id = p.artwork_id
    AND p.timestamp <= s.sold_at
    AND p.timestamp > s.sold_at - INTERVAL '30 days'
ORDER BY s.artwork_id, s.sold_at, p.timestamp DESC;
