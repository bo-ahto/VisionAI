-- VisionAI 가격 예측 API 데이터베이스 초기화
-- postgres-proxy를 통해 실행: /db/visionai_dev/query

-- pg_trgm 확장 (fuzzy 매칭용)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. artists (작가 마스터)
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    name_ko VARCHAR(100),
    name_en VARCHAR(100),
    name_normalized VARCHAR(200) NOT NULL,
    name_variants JSONB DEFAULT '[]',
    birth_year INT,
    nationality VARCHAR(50),
    gender VARCHAR(10),
    source VARCHAR(20) NOT NULL,
    artsy_slug VARCHAR(100),
    saatchi_id INT,
    is_in_training BOOLEAN DEFAULT false,
    training_count INT DEFAULT 0 CHECK (training_count >= 0),
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_artists_name_normalized_trgm ON artists USING gin (name_normalized gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_artists_name_en ON artists (name_en);
CREATE INDEX IF NOT EXISTS idx_artists_name_ko ON artists (name_ko);
CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_artsy_slug ON artists (artsy_slug) WHERE artsy_slug IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_saatchi_id ON artists (saatchi_id) WHERE saatchi_id IS NOT NULL;

-- 2. artist_profiles (외부 프로필 캐시)
CREATE TABLE IF NOT EXISTS artist_profiles (
    id SERIAL PRIMARY KEY,
    artist_id INT NOT NULL REFERENCES artists(id),
    source VARCHAR(20) NOT NULL CHECK (source IN ('artsy', 'saatchi', 'web')),
    birth_year_from_source INT,
    nationality_from_source VARCHAR(50),
    total_works INT DEFAULT 0,
    followers INT DEFAULT 0,
    solo_count INT DEFAULT 0 CHECK (solo_count >= 0),
    group_count INT DEFAULT 0 CHECK (group_count >= 0),
    fair_count INT DEFAULT 0 CHECK (fair_count >= 0),
    career_stage INT CHECK (career_stage BETWEEN 1 AND 4),
    bio TEXT,
    education TEXT,
    exhibitions TEXT,
    profile_completeness INT DEFAULT 0 CHECK (profile_completeness BETWEEN 0 AND 3),
    raw_data JSONB,
    status VARCHAR(10) NOT NULL DEFAULT 'success' CHECK (status IN ('success', 'failed', 'stale')),
    error_message TEXT,
    retry_after TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE (artist_id, source)
);

CREATE INDEX IF NOT EXISTS idx_artist_profiles_expires ON artist_profiles (expires_at);
CREATE INDEX IF NOT EXISTS idx_artist_profiles_status ON artist_profiles (status);

-- 3. model_versions (모델 메타 — CB+XGB 쌍)
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    catboost_hash VARCHAR(64),
    xgboost_hash VARCHAR(64),
    training_count INT,
    artist_count INT,
    new_candidates_count INT DEFAULT 0,
    mdape_groupkfold FLOAT,
    mdape_kfold FLOAT,
    mdape_prev_diff FLOAT,
    features JSONB,
    activated_at TIMESTAMPTZ,
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 동시에 활성 버전은 1개만
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_versions_active
    ON model_versions (activated_at)
    WHERE activated_at IS NOT NULL AND deactivated_at IS NULL;

-- 4. predictions (예측 로그)
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artist_id INT REFERENCES artists(id),
    artist_name_input VARCHAR(200),
    width_cm FLOAT,
    height_cm FLOAT,
    ho INT,
    medium_input VARCHAR(200),
    medium_category VARCHAR(20),
    target_market VARCHAR(20),
    predicted_krw INT CHECK (predicted_krw > 0),
    price_range_low INT,
    price_range_high INT,
    confidence_grade CHAR(1) CHECK (confidence_grade IN ('A', 'B', 'C', 'D')),
    model_version_id INT REFERENCES model_versions(id),
    is_known_artist BOOLEAN,
    feature_completeness FLOAT CHECK (feature_completeness BETWEEN 0 AND 1),
    external_sources_used VARCHAR[],
    cache_hit BOOLEAN,
    db_lookup_ms INT,
    external_fetch_ms INT,
    prediction_ms INT,
    total_ms INT,
    warnings JSONB,
    actual_price INT,
    request_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_predictions_artist ON predictions (artist_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions (created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_grade ON predictions (confidence_grade);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions (model_version_id);

-- 5. training_candidates (학습 후보 적재)
CREATE TABLE IF NOT EXISTS training_candidates (
    id SERIAL PRIMARY KEY,
    artist_id INT REFERENCES artists(id),
    artist_name VARCHAR(200) NOT NULL,
    width_cm FLOAT CHECK (width_cm > 0),
    height_cm FLOAT CHECK (height_cm > 0),
    medium VARCHAR(200),
    price_krw INT CHECK (price_krw > 0),
    price_source VARCHAR(50),
    gallery_name VARCHAR(100),
    market_source VARCHAR(20) CHECK (market_source IN ('artsy', 'saatchi', 'gallery', 'online', 'other')),
    ingestion_channel VARCHAR(20),
    sale_date DATE,
    external_profile_snapshot JSONB,
    prediction_id UUID REFERENCES predictions(id),
    raw_data JSONB,
    dedupe_key VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'trained')),
    reject_reason TEXT,
    review_notes TEXT,
    reviewed_by VARCHAR(50),
    reviewed_at TIMESTAMPTZ,
    trained_in_version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_training_candidates_dedupe ON training_candidates (dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_training_candidates_status ON training_candidates (status);
CREATE INDEX IF NOT EXISTS idx_training_candidates_created ON training_candidates (created_at);
CREATE INDEX IF NOT EXISTS idx_training_candidates_artist ON training_candidates (artist_id);

-- 초기 모델 버전 등록
INSERT INTO model_versions (version, training_count, artist_count, mdape_groupkfold, mdape_kfold, features, activated_at)
VALUES (
    'v3',
    29361,
    1589,
    38.7,
    11.7,
    '["ho","ho_power","ln_ho","area_cm2","ln_area","aspect_ratio","is_small","support_factor","ho_x_support","is_unique","is_edition","work_age","has_depth","artist_birth_year","has_birth_year","career_age","career_stage","ln_followers","artist_total_works","for_sale_ratio","profile_completeness","gallery_tier","gallery_city_count","has_seoul","has_international","is_krw","vintage_premium","freshness_discount","support_type","medium_category","attribution_class","gallery_name","gallery_type","price_currency","source","ho_price_level","medium_price_level"]',
    now()
);
