# PP-Y18 Cold PP-Y16 test 상위 후보 안정성 검증

- 목적: Cold 후속 실험에서 남은 validation 고정/재현성 gap을 닫는다.
- 원칙: test 결과만 보고 후보를 새로 고르지 않고, validation/OOF 또는 bootstrap 근거를 함께 기록한다.

## Test 결과 상위

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---:|---:|---:|---:|
| `stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25` | `y16_candidate_stability` | 0.4239 | 1.0003 | 3.3553 | 0.8557 |
| `stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25` | `y16_candidate_stability` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25` | `y16_candidate_stability` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25` | `y16_candidate_stability` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25` | `y16_candidate_stability` | 0.4247 | 0.9910 | 3.3053 | 0.8575 |
| `stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15` | `y16_candidate_stability` | 0.4382 | 1.0981 | 3.3512 | 0.8700 |
| `component_pp_y2_baseline` | `stability_component` | 0.4421 | 1.0484 | 3.3537 | 0.8567 |
| `stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35` | `y16_candidate_stability` | 0.4438 | 1.1083 | 2.8025 | 0.8905 |

## Map / Bootstrap

| experiment_id | candidate | source_candidate | row_bootstrap_MdAPE_delta_median | row_bootstrap_MdAPE_delta_ci_low | row_bootstrap_MdAPE_delta_ci_high | row_bootstrap_MdAPE_prob_improve | row_bootstrap_MAPE_delta_median | row_bootstrap_MAPE_delta_ci_low | row_bootstrap_MAPE_delta_ci_high | row_bootstrap_MAPE_prob_improve | row_bootstrap_p95_APE_delta_median | row_bootstrap_p95_APE_delta_ci_low | row_bootstrap_p95_APE_delta_ci_high | row_bootstrap_p95_APE_prob_improve | artist_bootstrap_MdAPE_delta_median | artist_bootstrap_MdAPE_delta_ci_low | artist_bootstrap_MdAPE_delta_ci_high | artist_bootstrap_MdAPE_prob_improve | artist_bootstrap_MAPE_delta_median | artist_bootstrap_MAPE_delta_ci_low | artist_bootstrap_MAPE_delta_ci_high | artist_bootstrap_MAPE_prob_improve | artist_bootstrap_p95_APE_delta_median | artist_bootstrap_p95_APE_delta_ci_low | artist_bootstrap_p95_APE_delta_ci_high | artist_bootstrap_p95_APE_prob_improve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-Y18 | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | 0.00151131 | -0.0161549 | 0.0176231 | 0.56875 | -0.0614186 | -0.0878669 | -0.0347171 | 0 | 0.551213 | 0.146026 | 1.03285 | 0.99 | 0.000342252 | -0.0363869 | 0.0380058 | 0.51125 | -0.0509932 | -0.179265 | 0.0205715 | 0.1275 | -0.0280775 | -0.606463 | 1.09532 | 0.4775 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | 0.00562231 | -0.00884061 | 0.0187693 | 0.76875 | -0.0509165 | -0.0716094 | -0.0294659 | 0 | 0.00252767 | -0.187857 | 0.53066 | 0.675 | 0.00857502 | -0.0179077 | 0.0374537 | 0.7275 | -0.0435438 | -0.161696 | 0.0147116 | 0.16875 | -0.0192681 | -0.520834 | 0.706759 | 0.43 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | 0.0220882 | 0.00744898 | 0.0353725 | 0.9975 | 0.0480574 | 0.0400394 | 0.0565497 | 1 | 0.0897447 | -0.0572822 | 0.414755 | 0.62125 | 0.0177155 | -0.00938671 | 0.0540597 | 0.87625 | 0.0454487 | 0.0123785 | 0.0964987 | 0.9975 | 0.159773 | -0.0960999 | 0.515154 | 0.78875 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | 0.0196027 | 0.00583344 | 0.0331201 | 0.99375 | 0.0572763 | 0.0487765 | 0.0668361 | 1 | 0.192025 | 0.0484348 | 0.52426 | 0.99875 | 0.0160615 | -0.0143883 | 0.0534986 | 0.84875 | 0.0543735 | 0.0180276 | 0.11075 | 0.99875 | 0.20333 | -0.0396711 | 0.643731 | 0.95125 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | 0.0196027 | 0.00583344 | 0.0331201 | 0.99375 | 0.0572763 | 0.0487765 | 0.0668361 | 1 | 0.192025 | 0.0484348 | 0.52426 | 0.99875 | 0.0160615 | -0.0143883 | 0.0534986 | 0.84875 | 0.0543735 | 0.0180276 | 0.11075 | 0.99875 | 0.20333 | -0.0396711 | 0.643731 | 0.95125 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | 0.0196027 | 0.00583344 | 0.0331201 | 0.99375 | 0.0572763 | 0.0487765 | 0.0668361 | 1 | 0.192025 | 0.0484348 | 0.52426 | 0.99875 | 0.0160615 | -0.0143883 | 0.0534986 | 0.84875 | 0.0543735 | 0.0180276 | 0.11075 | 0.99875 | 0.20333 | -0.0396711 | 0.643731 | 0.95125 |
| PP-Y18 | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | 0.0196027 | 0.00583344 | 0.0331201 | 0.99375 | 0.0572763 | 0.0487765 | 0.0668361 | 1 | 0.192025 | 0.0484348 | 0.52426 | 0.99875 | 0.0160615 | -0.0143883 | 0.0534986 | 0.84875 | 0.0543735 | 0.0180276 | 0.11075 | 0.99875 | 0.20333 | -0.0396711 | 0.643731 | 0.95125 |
