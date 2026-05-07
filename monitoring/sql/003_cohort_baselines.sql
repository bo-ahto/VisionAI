-- v3.6 PR14b' (코덱스 PR14b review P1 fix): cohort baseline table.
-- spec: docs/v3_5_step4_drift_monitoring.md §6.2 Panel 3 / §3.3 Trigger 2
-- dialect: PostgreSQL 14+
--
-- 목적: train_dist (saatchi_warm 0.697 등) 를 SQL 안에 hardcode 하지 말고
-- artifact_version 별 row 로 관리. retrain 후 새 artifact_version 의 row 만 추가
-- → metric query 가 자동으로 최신 baseline 사용.
--
-- 운영: artifact build pipeline 이 ablation 결과 (학습 row 의 cohort 분포) 를
-- 이 table 에 INSERT. metric query 는 latest artifact_version row 를 JOIN.

CREATE TABLE IF NOT EXISTS cohort_baselines (
    artifact_version    VARCHAR(64)     NOT NULL,
    cohort              VARCHAR(32)     NOT NULL,    -- saatchi_warm | saatchi_cold | artsy_warm | unmatched
    expected_rate       NUMERIC(5, 4)   NOT NULL,    -- [0.0, 1.0]
    n_train_rows        INT,                          -- 학습 row 수 (sanity)
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (artifact_version, cohort)
);

CREATE INDEX IF NOT EXISTS idx_cohort_baselines_artifact
    ON cohort_baselines (artifact_version);

-- ----------------------------------------------------------------------------
-- 초기 row: v3.5 step 1 ablation 결과 (V_year_saatchi_warm variant 기준)
-- 학습 데이터 28376 rows 분포 (artifact 'integrated_v3_5_v_year_saatchi_warm')
-- ----------------------------------------------------------------------------

INSERT INTO cohort_baselines (artifact_version, cohort, expected_rate, n_train_rows)
VALUES
    ('integrated_v3_5_v_year_saatchi_warm', 'saatchi_warm',  0.6970, 19773),
    ('integrated_v3_5_v_year_saatchi_warm', 'saatchi_cold',  0.0460,  1305),
    ('integrated_v3_5_v_year_saatchi_warm', 'artsy_warm',    0.2570,  7298),
    ('integrated_v3_5_v_year_saatchi_warm', 'unmatched',     0.0000,     0)
ON CONFLICT (artifact_version, cohort) DO UPDATE
    SET expected_rate = EXCLUDED.expected_rate,
        n_train_rows  = EXCLUDED.n_train_rows;

-- ----------------------------------------------------------------------------
-- 기존 variant (v3_filtered_tuned, year-disabled) — backfill 안 함.
-- 이 variant 는 cohort gating 이 없어 baseline 비교 무의미.
-- artifact_version='integrated_v3_filtered_tuned' row 는 의도적으로 삽입 X.
-- ----------------------------------------------------------------------------
