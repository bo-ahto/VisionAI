-- v3.6 Phase 2 — predict_logs + sold_actuals DDL
-- spec: docs/v3_5_step4_drift_monitoring.md §6.1
-- dialect: PostgreSQL 14+

-- ----------------------------------------------------------------------------
-- predict_logs: server _log_prediction() row 를 ETL 로 적재.
-- spec column 이름 정합 (v3.6 PR14a). server JSONL 의 deprecated alias
-- (predicted_krw, price_range_low, price_range_high) 는 ETL 단계에서 drop.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS predict_logs (
    request_id              UUID            PRIMARY KEY,  -- server 의 'id'
    timestamp               TIMESTAMPTZ     NOT NULL,     -- server 의 'ts'

    -- rollout / cohort
    rollout_cohort          VARCHAR(32),                  -- treatment_5pct | control | unknown
    matched                 BOOLEAN,
    match_profile_source    VARCHAR(16),                  -- saatchi | artsy | NULL (PR10b)
    slug_in_warm_set        BOOLEAN,
    is_saatchi_warm         BOOLEAN,
    external_collector_source VARCHAR(16),                -- saatchi | artsy | web | manual | none

    -- year resolution (v3.5 step 3 §3.2.1)
    year_made_route         VARCHAR(32),                  -- manual | manual_seed_cache_write | cache_hit
                                                          -- | fetch_ok | fetch_fail | no_id | parse_invalid
                                                          -- | disabled | rate_limited
    year_made_used          INT,
    enrichment_latency_ms   FLOAT,
    predict_total_latency_ms FLOAT,
    artwork_id              VARCHAR(64),
    artwork_url             VARCHAR(500),

    -- 예측 결과 (코덱스 step4 P0: MdAPE 계산 필수)
    predicted_price_krw     INT             NOT NULL,
    predicted_range_low_krw INT,
    predicted_range_high_krw INT,
    confidence_grade        VARCHAR(2),                   -- A / B / C / D

    -- 버전 분리 (v3.5 step 3 §3.2 코덱스 P0: 트래픽 변화 vs 설정 변화 분리)
    model_variant           VARCHAR(64),                  -- v3_filtered_tuned | v3_5_v_year_saatchi_warm
    artifact_version        VARCHAR(64),
    warm_artist_slugs_version VARCHAR(64),
    rollout_rule_version    VARCHAR(32),
    server_instance         VARCHAR(64),
    worker_instance_id      VARCHAR(64),                  -- v3.6 PR12: process-local uuid4 hex
    cache_epoch             VARCHAR(32)                   -- UTC YYYYMMDDTHHMMZ
);

CREATE INDEX IF NOT EXISTS idx_predict_logs_timestamp
    ON predict_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_predict_logs_cohort_ts
    ON predict_logs (rollout_cohort, timestamp);
CREATE INDEX IF NOT EXISTS idx_predict_logs_artifact
    ON predict_logs (artifact_version);
CREATE INDEX IF NOT EXISTS idx_predict_logs_artwork_ts
    ON predict_logs (artwork_id, timestamp);  -- D7 prediction-to-sale linkage

-- ----------------------------------------------------------------------------
-- sold_actuals: production 거래 결과 (D7 MdAPE 계산 source).
-- 외부 source (saatchi crawler / artsy / 직접 입력) 에서 적재.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sold_actuals (
    artwork_id              VARCHAR(64)     NOT NULL,
    sold_at                 TIMESTAMPTZ     NOT NULL,
    sold_price_krw          INT             NOT NULL,
    artist_slug             VARCHAR(64),
    source                  VARCHAR(16),                  -- saatchi | artsy | web | manual
    PRIMARY KEY (artwork_id, sold_at),
    -- v3.6 PR14b' (코덱스 P2): MdAPE 계산 시 0 분모 방지.
    -- abs_pct_error = ABS(predicted - sold) / sold → sold=0 이면 NULL.
    -- view 의 NULLIF 가 NULL 처리하지만 alert all-NULL window 에서 metric 누락 → CHECK 으로 ingest 단계 차단.
    CONSTRAINT sold_actuals_price_positive CHECK (sold_price_krw > 0)
);

CREATE INDEX IF NOT EXISTS idx_sold_actuals_sold_at
    ON sold_actuals (sold_at);
CREATE INDEX IF NOT EXISTS idx_sold_actuals_artist
    ON sold_actuals (artist_slug, sold_at);
