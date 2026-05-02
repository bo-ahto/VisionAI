-- v3.6 Phase 2 — Audit / governance metrics (step4 §2.3)
-- Panel 10-12: model_variant 분포 / artifact_version 일관성 / cache_epoch age
-- dialect: PostgreSQL 14+

-- ============================================================================
-- Panel 10: model_variant_distribution (요청 별 사용 variant 분포)
-- 목표: rollout % 와 정합 (treatment_5pct cohort 의 5% 가 v3.5 variant 사용)
-- ============================================================================

-- panel_10_model_variant_distribution (1h window)
SELECT
    rollout_cohort,
    model_variant,
    COUNT(*)                                                  AS n,
    COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY rollout_cohort)
        AS share_within_cohort
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY rollout_cohort, model_variant
ORDER BY rollout_cohort, n DESC;

-- ============================================================================
-- Panel 11: artifact_version_consistency
-- 같은 server_instance + worker_instance_id 가 동일 artifact_version 만 사용 검증.
-- 목표: 100% (단일 worker 안에서 artifact_version mix 없음 — fail-closed bundle 보장)
-- ============================================================================

-- panel_11_artifact_version_consistency (1h window)
SELECT
    server_instance,
    worker_instance_id,
    COUNT(DISTINCT artifact_version)                          AS distinct_artifact_versions,
    COUNT(DISTINCT warm_artist_slugs_version)                 AS distinct_warm_set_versions,
    COUNT(*)                                                  AS n_requests
FROM predict_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY server_instance, worker_instance_id
HAVING COUNT(DISTINCT artifact_version) > 1
    OR COUNT(DISTINCT warm_artist_slugs_version) > 1
ORDER BY n_requests DESC;
-- 결과 row 가 있으면 inconsistency — alert.

-- ============================================================================
-- Panel 12: cache_epoch_age_hours (server_instance 별 cold restart 감지)
-- 목표: < 168h (7d, cache TTL 정합). 더 오래된 cache_epoch 는 cold restart 미발생
-- 또는 server 가 idle 한 상태.
-- ============================================================================

-- panel_12_cache_epoch_age (현재 active worker 별)
WITH latest_per_worker AS (
    SELECT DISTINCT ON (server_instance, worker_instance_id)
        server_instance,
        worker_instance_id,
        cache_epoch,
        timestamp                                             AS last_seen_at
    FROM predict_logs
    WHERE timestamp > NOW() - INTERVAL '1 hour'  -- 최근 1h 안에 active
    ORDER BY server_instance, worker_instance_id, timestamp DESC
)
SELECT
    server_instance,
    worker_instance_id,
    cache_epoch,
    last_seen_at,
    -- cache_epoch 형식: YYYYMMDDTHHMMZ → timestamp 변환 후 age 계산
    EXTRACT(EPOCH FROM (NOW() - TO_TIMESTAMP(cache_epoch, 'YYYYMMDD"T"HH24MI"Z"')))
        / 3600.0                                              AS cache_epoch_age_hours
FROM latest_per_worker
ORDER BY cache_epoch_age_hours DESC;
