# Official v0.1 WMIN8 Exact Adapter Gap Audit

- Created at: 2026-06-13T09:11:42
- Decision: `exact_wmin8_runtime_candidate_connected`
- Selected candidate: `min1_route_w850_risk_q50_altlower_gap005`
- Source experiment: `experiments/track6/PP-WMIN8_warm_min1_weight_router`

## 1. Summary

- WMIN8 missing upstream values are now supplied by the packaged exact runtime candidate. The remaining validation item is fixed-test parity through the official API endpoint.
- Warm-lite API boundary and deterministic repeat are already validated.
- WMIN8 selected target is exposed in the model-status endpoint.
- WMIN8 5+ Warm API output uses the packaged WMIN8 runtime adapter when `exact_runtime_ready=true`.

## 2. Selected Gate

| candidate_label | base_candidate | alternative_candidate | gate_kind | threshold | gap | validation_route_share | test_route_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| min1_route_w850_risk_q50_altlower_gap005 | min1_huber_refit_partial | min1_w850_huber_refit_partial | risk_ge_altlower_gap | 0.2534165869100283 | 0.005 | 0.210019267822736 | 0.1976935749588138 |

## 3. Service Feature Readiness

| feature | service_runtime_status | service_source | exact_adapter_gap |
| --- | --- | --- | --- |
| ppv8_defensive | available | pp_v8_compact_blend_mape_guarded_pred_log |  |
| svc_fallback | available | svc_numeric_seed_mean_pred_log |  |
| shrunk_huber_refit | resolved_by_runtime_artifact | models/track6/warm_wmin8_exact_runtime_candidate |  |
| shrunk_svc_prior | resolved_by_runtime_artifact | models/track6/warm_wmin8_exact_runtime_candidate |  |
| log_area | available | log_area |  |
| svc_group_n_log | available | svc_group_n_log |  |
| svc_prior_iqr | available | svc_group_log_price_iqr |  |
| current_ppv8_gap | computable | current_70_30 - ppv8_defensive |  |
| current_shrunk_huber_gap | resolved_by_runtime_artifact | models/track6/warm_wmin8_exact_runtime_candidate |  |
| raw_shrunk_prior_gap | resolved_by_runtime_artifact | models/track6/warm_wmin8_exact_runtime_candidate |  |

## 4. Coefficient Artifact Readiness

- WMIN7 coefficient CSV exists, but it stores coefficients on scaled features only.
- Exact replay is supplied by serialized Huber pipelines in `models/track6/warm_wmin8_exact_runtime_candidate` when `exact_runtime_ready=true`.

## 5. Required Next Work

- Fixed-test parity script comparing API exact WMIN8 predictions with experiments/track6/PP-WMIN8 outputs.
- If row-level differences remain, align service feature construction with the original WMIN8 candidate_predictions columns.
