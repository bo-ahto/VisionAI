-- Price prediction official test v0.1 local DB schema draft.
-- Target: SQLite first, PostgreSQL-compatible naming.

CREATE TABLE IF NOT EXISTS artist_registry (
  artist_key TEXT PRIMARY KEY,
  name_ko TEXT,
  name_en TEXT,
  birth_year INTEGER,
  nationality TEXT,
  nationality_ko TEXT,
  entity_suffix TEXT,
  is_homonym INTEGER DEFAULT 0,
  valid_price_count INTEGER DEFAULT 0,
  primary_medium_category TEXT,
  primary_support_category TEXT,
  median_price_krw INTEGER,
  median_log_area REAL,
  created_at TEXT,
  updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_artist_registry_name_ko ON artist_registry(name_ko);
CREATE INDEX IF NOT EXISTS idx_artist_registry_name_en ON artist_registry(name_en);
CREATE INDEX IF NOT EXISTS idx_artist_registry_valid_price_count ON artist_registry(valid_price_count);

CREATE TABLE IF NOT EXISTS artist_aliases (
  alias_id TEXT PRIMARY KEY,
  artist_key TEXT NOT NULL,
  alias_text TEXT NOT NULL,
  alias_normalized TEXT NOT NULL,
  alias_type TEXT,
  source TEXT,
  confidence REAL DEFAULT 1.0,
  created_at TEXT,
  FOREIGN KEY (artist_key) REFERENCES artist_registry(artist_key)
);

CREATE INDEX IF NOT EXISTS idx_artist_aliases_normalized ON artist_aliases(alias_normalized);
CREATE INDEX IF NOT EXISTS idx_artist_aliases_artist ON artist_aliases(artist_key);

CREATE TABLE IF NOT EXISTS artist_profile_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  artist_key TEXT NOT NULL,
  snapshot_version TEXT NOT NULL,
  birth_year INTEGER,
  career_age REAL,
  career_stage TEXT,
  total_works INTEGER,
  for_sale_works INTEGER,
  followers INTEGER,
  for_sale_ratio REAL,
  is_p1 INTEGER,
  has_international INTEGER,
  source TEXT,
  feature_json TEXT,
  created_at TEXT,
  FOREIGN KEY (artist_key) REFERENCES artist_registry(artist_key)
);

CREATE INDEX IF NOT EXISTS idx_artist_profile_artist_version ON artist_profile_snapshots(artist_key, snapshot_version);

CREATE TABLE IF NOT EXISTS artwork_price_observations (
  observation_id TEXT PRIMARY KEY,
  track6_row_id INTEGER,
  source_artwork_id TEXT,
  source_name TEXT,
  artwork_url TEXT,
  image_url TEXT,
  artist_key TEXT,
  artist_name_ko TEXT,
  title TEXT,
  price_krw INTEGER,
  log_price_krw REAL,
  width_cm REAL,
  height_cm REAL,
  depth_cm REAL,
  area_cm2 REAL,
  log_area REAL,
  aspect_ratio REAL,
  has_depth INTEGER,
  is_3d_candidate INTEGER,
  medium_category TEXT,
  support_category TEXT,
  medium_support_bucket TEXT,
  is_training_candidate INTEGER DEFAULT 1,
  label_quality_tier TEXT,
  split_name TEXT,
  created_at TEXT,
  FOREIGN KEY (artist_key) REFERENCES artist_registry(artist_key)
);

CREATE INDEX IF NOT EXISTS idx_price_obs_artist ON artwork_price_observations(artist_key);
CREATE INDEX IF NOT EXISTS idx_price_obs_medium_support ON artwork_price_observations(medium_category, support_category);
CREATE INDEX IF NOT EXISTS idx_price_obs_area ON artwork_price_observations(log_area);
CREATE INDEX IF NOT EXISTS idx_price_obs_split ON artwork_price_observations(split_name);

CREATE TABLE IF NOT EXISTS artist_search_feature_snapshots (
  search_snapshot_id TEXT PRIMARY KEY,
  snapshot_version TEXT NOT NULL,
  artist_key TEXT,
  artist_search_name TEXT NOT NULL,
  artist_search_name_normalized TEXT,
  search_result_count INTEGER,
  search_source_count INTEGER,
  provider_coverage_count INTEGER,
  query_success_count INTEGER,
  search_art_context_count INTEGER,
  search_exhibition_context_count INTEGER,
  search_gallery_context_count INTEGER,
  search_market_context_count INTEGER,
  search_social_context_count INTEGER,
  search_homonym_context_count INTEGER,
  search_trusted_domain_count INTEGER,
  search_name_match_ratio REAL,
  search_art_match_ratio REAL,
  search_exhibition_ratio REAL,
  search_quality_score REAL,
  search_quality_grade TEXT,
  search_homonym_risk_grade TEXT,
  search_success_flag INTEGER,
  search_collected_flag INTEGER,
  raw_feature_json TEXT,
  created_at TEXT,
  FOREIGN KEY (artist_key) REFERENCES artist_registry(artist_key)
);

CREATE INDEX IF NOT EXISTS idx_search_snap_artist ON artist_search_feature_snapshots(artist_key);
CREATE INDEX IF NOT EXISTS idx_search_snap_name ON artist_search_feature_snapshots(artist_search_name_normalized);
CREATE INDEX IF NOT EXISTS idx_search_snap_version ON artist_search_feature_snapshots(snapshot_version);

CREATE TABLE IF NOT EXISTS artist_search_results (
  result_id TEXT PRIMARY KEY,
  search_snapshot_id TEXT,
  artist_search_name TEXT,
  provider TEXT,
  query_text TEXT,
  rank INTEGER,
  title TEXT,
  snippet TEXT,
  url TEXT,
  domain TEXT,
  source_group TEXT,
  has_result INTEGER,
  is_art_context INTEGER,
  is_exhibition_context INTEGER,
  is_gallery_context INTEGER,
  is_market_context INTEGER,
  is_homonym_context INTEGER,
  artist_name_in_result INTEGER,
  collected_at TEXT,
  FOREIGN KEY (search_snapshot_id) REFERENCES artist_search_feature_snapshots(search_snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_search_results_snapshot ON artist_search_results(search_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_search_results_artist_name ON artist_search_results(artist_search_name);

CREATE TABLE IF NOT EXISTS similar_artwork_stats_cache (
  stats_id TEXT PRIMARY KEY,
  cache_version TEXT NOT NULL,
  scope TEXT NOT NULL,
  artist_key TEXT,
  medium_category TEXT,
  support_category TEXT,
  size_bucket TEXT,
  log_area_min REAL,
  log_area_max REAL,
  sample_count INTEGER,
  median_price_krw INTEGER,
  q25_price_krw INTEGER,
  q75_price_krw INTEGER,
  median_log_price REAL,
  median_krw_per_ho INTEGER,
  q25_krw_per_ho INTEGER,
  q75_krw_per_ho INTEGER,
  coverage_tier TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_similar_stats_lookup
  ON similar_artwork_stats_cache(cache_version, scope, artist_key, medium_category, support_category, size_bucket);

CREATE TABLE IF NOT EXISTS similar_artist_cache (
  similar_artist_id TEXT PRIMARY KEY,
  cache_version TEXT NOT NULL,
  target_artist_key TEXT NOT NULL,
  candidate_artist_key TEXT NOT NULL,
  similarity_score REAL,
  numeric_similarity REAL,
  categorical_similarity REAL,
  price_history_count INTEGER,
  match_reasons_json TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_similar_artist_target ON similar_artist_cache(cache_version, target_artist_key);

CREATE TABLE IF NOT EXISTS model_artifact_registry (
  artifact_id TEXT PRIMARY KEY,
  service_version TEXT NOT NULL,
  route TEXT NOT NULL,
  artifact_role TEXT NOT NULL,
  display_name TEXT,
  internal_trace_id TEXT,
  artifact_path TEXT,
  artifact_hash TEXT,
  feature_schema_version TEXT,
  metrics_json TEXT,
  active_flag INTEGER DEFAULT 0,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_model_artifacts_active ON model_artifact_registry(service_version, route, active_flag);

CREATE TABLE IF NOT EXISTS prediction_events (
  prediction_id TEXT PRIMARY KEY,
  request_id TEXT,
  service_version TEXT NOT NULL,
  route TEXT,
  display_route TEXT,
  artist_key TEXT,
  artist_match_score REAL,
  same_artist_training_price_count INTEGER,
  input_snapshot_json TEXT,
  input_quality_json TEXT,
  prediction_price_krw INTEGER,
  range_low_krw INTEGER,
  range_high_krw INTEGER,
  confidence_tier TEXT,
  model_artifacts_json TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_prediction_events_created ON prediction_events(created_at);
CREATE INDEX IF NOT EXISTS idx_prediction_events_artist ON prediction_events(artist_key);
CREATE INDEX IF NOT EXISTS idx_prediction_events_route ON prediction_events(route);

CREATE TABLE IF NOT EXISTS warm_feature_snapshots (
  warm_feature_id TEXT PRIMARY KEY,
  prediction_id TEXT NOT NULL,
  feature_schema_version TEXT,
  artist_key TEXT,
  pp252_log REAL,
  pp252_stability_log REAL,
  prob_hist35_pp252 REAL,
  resid_huber_pp252 REAL,
  quantile_width REAL,
  l10_price_range_ratio REAL,
  svc_group_n INTEGER,
  component_prediction_spread REAL,
  confidence_tier TEXT,
  stable_price_band TEXT,
  row_risk REAL,
  applied_cap_log REAL,
  applied_correction_log REAL,
  final_log_price REAL,
  feature_json TEXT,
  created_at TEXT,
  FOREIGN KEY (prediction_id) REFERENCES prediction_events(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_warm_features_prediction ON warm_feature_snapshots(prediction_id);

CREATE TABLE IF NOT EXISTS cold_feature_snapshots (
  cold_feature_id TEXT PRIMARY KEY,
  prediction_id TEXT NOT NULL,
  feature_schema_version TEXT,
  artist_key TEXT,
  search_snapshot_id TEXT,
  y18_qwidth_pred_log REAL,
  lgb_q40_pred_log REAL,
  quantile_width_log REAL,
  guard_applied INTEGER,
  guard_pred_log REAL,
  search_delta_log REAL,
  search_covered INTEGER,
  review_flag INTEGER,
  confidence_tier TEXT,
  final_log_price REAL,
  feature_json TEXT,
  created_at TEXT,
  FOREIGN KEY (prediction_id) REFERENCES prediction_events(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_cold_features_prediction ON cold_feature_snapshots(prediction_id);
CREATE INDEX IF NOT EXISTS idx_cold_features_search ON cold_feature_snapshots(search_snapshot_id);

CREATE TABLE IF NOT EXISTS prediction_calculation_steps (
  step_id TEXT PRIMARY KEY,
  prediction_id TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  step_name TEXT,
  step_role TEXT,
  formula_text TEXT,
  input_json TEXT,
  output_json TEXT,
  display_flag INTEGER DEFAULT 1,
  created_at TEXT,
  FOREIGN KEY (prediction_id) REFERENCES prediction_events(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_calc_steps_prediction ON prediction_calculation_steps(prediction_id, step_order);

CREATE TABLE IF NOT EXISTS sale_price_feedback (
  feedback_id TEXT PRIMARY KEY,
  prediction_id TEXT NOT NULL,
  actual_sale_price_krw INTEGER NOT NULL,
  sale_date TEXT,
  sale_channel TEXT,
  evidence_status TEXT DEFAULT 'partial',
  consent_for_training INTEGER DEFAULT 1,
  review_status TEXT DEFAULT 'needs_review',
  review_note TEXT,
  created_at TEXT,
  reviewed_at TEXT,
  FOREIGN KEY (prediction_id) REFERENCES prediction_events(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_prediction ON sale_price_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_feedback_review_status ON sale_price_feedback(review_status);

CREATE TABLE IF NOT EXISTS training_candidates (
  candidate_id TEXT PRIMARY KEY,
  feedback_id TEXT NOT NULL,
  prediction_id TEXT NOT NULL,
  route_at_prediction TEXT,
  artist_key TEXT,
  label_price_krw INTEGER,
  quality_score REAL,
  candidate_status TEXT,
  feature_snapshot_json TEXT,
  created_at TEXT,
  FOREIGN KEY (feedback_id) REFERENCES sale_price_feedback(feedback_id),
  FOREIGN KEY (prediction_id) REFERENCES prediction_events(prediction_id)
);

CREATE INDEX IF NOT EXISTS idx_training_candidates_status ON training_candidates(candidate_status);
CREATE INDEX IF NOT EXISTS idx_training_candidates_route ON training_candidates(route_at_prediction);

CREATE TABLE IF NOT EXISTS external_feature_review_queue (
  review_candidate_id TEXT PRIMARY KEY,
  candidate_version TEXT NOT NULL,
  candidate_type TEXT NOT NULL,
  artist_key TEXT,
  artist_name_ko TEXT,
  artist_name_en TEXT,
  normalized_artist_name TEXT,
  source_system TEXT,
  source_record_id TEXT,
  source_url TEXT,
  source_domain TEXT,
  source_record_hash TEXT,
  duplicate_group_key TEXT,
  duplicate_status TEXT,
  improvement_status TEXT,
  existing_record_ref TEXT,
  existing_record_hash TEXT,
  quality_score REAL,
  evidence_count INTEGER,
  improved_fields_json TEXT,
  conflict_fields_json TEXT,
  candidate_payload_json TEXT,
  review_status TEXT NOT NULL,
  review_reasons_json TEXT,
  created_at TEXT,
  reviewed_at TEXT,
  reviewed_by TEXT,
  review_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_feature_review_status
  ON external_feature_review_queue(candidate_version, review_status);
CREATE INDEX IF NOT EXISTS idx_feature_review_artist
  ON external_feature_review_queue(artist_key);
CREATE INDEX IF NOT EXISTS idx_feature_review_duplicate
  ON external_feature_review_queue(duplicate_group_key, duplicate_status);
CREATE INDEX IF NOT EXISTS idx_feature_review_source_hash
  ON external_feature_review_queue(source_record_hash);

CREATE TABLE IF NOT EXISTS external_feature_review_decisions (
  review_decision_id TEXT PRIMARY KEY,
  review_candidate_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  decision_reason TEXT,
  reviewer TEXT,
  decided_at TEXT,
  promotion_target TEXT,
  promoted_record_id TEXT,
  FOREIGN KEY (review_candidate_id) REFERENCES external_feature_review_queue(review_candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_feature_review_decisions_candidate
  ON external_feature_review_decisions(review_candidate_id);
