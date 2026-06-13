# Official v0.1 WMIN8 Exact Runtime Candidate

- Created at: 2026-06-13T09:52:59
- Status: `runtime_prerequisite_packaged`
- Selected WMIN8 candidate: `min1_route_w850_risk_q50_altlower_gap005`
- Huber pipeline replay max log diff: `3.5527136788e-15`
- Replay pass: `True`

## 1. Packaged Files

- shrinkage_runtime: `artifacts/shrinkage_runtime.json`
- shrunk_huber_refit_model: `artifacts/shrunk_huber_refit_model.joblib`
- huber_runtime: `artifacts/wmin8_huber_runtime.json`
- base_huber_refit_pipeline: `artifacts/base_w700_huber_refit_pipeline.joblib`
- alternative_huber_refit_pipeline: `artifacts/alternative_w850_huber_refit_pipeline.joblib`
- huber_pipeline_parity: `artifacts/wmin8_huber_pipeline_parity.csv`
- fixed_test_feature_store: `artifacts/fixed_test_feature_store.csv`

## 2. Huber Pipeline Parity

| role | candidate_label | eval_split | n | max_abs_log_diff | mean_abs_log_diff |
|---|---|---:|---:|---:|---:|
| base_w700 | min1_w700_huber_refit_partial | validation_oof | 519 | 3.5527136788e-15 | 4.1071834437e-16 |
| base_w700 | min1_w700_huber_refit_partial | test | 607 | 3.5527136788e-15 | 4.53600181395e-16 |
| alternative_w850 | min1_w850_huber_refit_partial | validation_oof | 519 | 1.7763568394e-15 | 3.69646509933e-16 |
| alternative_w850 | min1_w850_huber_refit_partial | test | 607 | 3.5527136788e-15 | 3.95071125732e-16 |

## 3. Fixed-Test Feature Store

- File: `artifacts/fixed_test_feature_store.csv`
- Rows: `1126`
- Validation rows: `519`
- Test rows: `607`
- Purpose: official API fixed-test parity에서 실험 당시 상류 피쳐를 `source_artwork_id` 또는 `artwork_url`로 재생한다.

## 4. API Connection Status

- official v0.1 adapter connected: `True`
- fixed-test feature store packaged: `True`
- API fixed-test parity pass: `True`
- API fixed-test max abs log diff: `5.3290705182007506e-15`
- API parity experiment: `experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity`
