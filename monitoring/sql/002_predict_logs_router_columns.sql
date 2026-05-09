-- PR2B-prereq.1: Source-conditional router + shadow logging columns
-- 영역 의 의무 영역 의 의무: predict_logs (existing / 001_predict_logs_ddl.sql)
-- 코덱스 자문 P1 fix: routing 5 + shadow 4 = 9 columns additive
-- backward compat: 기존 column 변경 X / append only

-- ----------------------------------------------------------------------------
-- predict_logs router/shadow columns (additive)
-- ----------------------------------------------------------------------------

ALTER TABLE predict_logs
    ADD COLUMN IF NOT EXISTS routing_source           VARCHAR(16),       -- artsy | saatchi | unified
    ADD COLUMN IF NOT EXISTS routing_reason           VARCHAR(64),       -- matched_artsy | unmatched_fallback | router_off | 등
    ADD COLUMN IF NOT EXISTS routed_variant           VARCHAR(64),       -- v3_filtered_tuned | source_conditional_v1_artsy | 등
    ADD COLUMN IF NOT EXISTS router_mode              VARCHAR(16),       -- off | shadow | canary | on
    ADD COLUMN IF NOT EXISTS cohort_in_canary         BOOLEAN,           -- canary mode 영역 의 의무 영역 의 의무 cohort 영역 의 의무 영역 의 의무

    -- Shadow dual-logging (mode=shadow only / NULL otherwise)
    ADD COLUMN IF NOT EXISTS shadow_routed_variant    VARCHAR(64),       -- mode=on simulate routed variant
    ADD COLUMN IF NOT EXISTS shadow_routing_source    VARCHAR(16),       -- artsy | saatchi | unified
    ADD COLUMN IF NOT EXISTS shadow_routing_reason    VARCHAR(64),       -- matched_artsy | unmatched_fallback | 등
    ADD COLUMN IF NOT EXISTS shadow_prediction_price_krw INT,            -- shadow predict price (primary와 비교)

    -- PR2B-prereq.2: source_router_rule_version (routing matrix pin / rollout_rule_version 영역 의 의무 영역 의 의무 분리)
    ADD COLUMN IF NOT EXISTS source_router_rule_version VARCHAR(32);     -- v1 | v2 | 등

-- Index for routing analysis (slice drift / cohort agreement)
CREATE INDEX IF NOT EXISTS idx_predict_logs_routing_ts
    ON predict_logs (routed_variant, timestamp);
CREATE INDEX IF NOT EXISTS idx_predict_logs_router_mode_ts
    ON predict_logs (router_mode, timestamp);
CREATE INDEX IF NOT EXISTS idx_predict_logs_routing_source_ts
    ON predict_logs (routing_source, timestamp);
