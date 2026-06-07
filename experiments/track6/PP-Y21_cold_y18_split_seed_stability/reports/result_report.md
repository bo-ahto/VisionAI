# PP-Y21 Cold PP-Y18 추가 split/seed 안정성 검증

- 목적: `PP-Y18 qwidth_bin` 후보가 특정 test 구성에서만 좋아진 것인지 확인한다.
- 방식: 기존 PP-Y18 예측값은 고정하고, 평가 holdout을 row 기준과 artist 기준으로 80회 반복 재구성한다.
- 주의: 이 검증은 모델 재학습 split 검증이 아니라, 이미 생성된 예측값의 평가 구성 안정성 검증이다.

## Test 기준 결과

| candidate | policy | n | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | pp_y18_reuse_prediction | 3099 | 0.423854 | 1.00026 | 3.35528 | 0.855724 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | pp_y18_reuse_prediction | 3099 | 0.424663 | 0.991042 | 3.3053 | 0.857474 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | pp_y18_reuse_prediction | 3099 | 0.424663 | 0.991042 | 3.3053 | 0.857474 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | pp_y18_reuse_prediction | 3099 | 0.424663 | 0.991042 | 3.3053 | 0.857474 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | pp_y18_reuse_prediction | 3099 | 0.424663 | 0.991042 | 3.3053 | 0.857474 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | pp_y18_reuse_prediction | 3099 | 0.43818 | 1.09808 | 3.3512 | 0.869978 |
| component_pp_y2_baseline | baseline | 3099 | 0.442147 | 1.0484 | 3.35373 | 0.856668 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | pp_y18_reuse_prediction | 3099 | 0.443767 | 1.10827 | 2.80252 | 0.890492 |

## 반복 holdout 안정성 요약

| candidate | split_mode | delta_MdAPE_median | delta_MdAPE_prob_improve | delta_MAPE_median | delta_MAPE_prob_improve | delta_p95_APE_median | delta_p95_APE_prob_improve | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | artist_holdout | 0.0222547 | 0.85 | 0.00849121 | 0.625 | -0.0130712 | 0.4625 | 보류 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | artist_holdout | 0.0268527 | 0.8125 | 0.00318048 | 0.55 | -0.0368375 | 0.45 | 보류 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | row_holdout | 0.0308378 | 1 | -0.00222658 | 0.4 | -0.0795522 | 0.2875 | 보류 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | row_holdout | 0.0201755 | 1 | -0.00552979 | 0.225 | 0.0414212 | 0.675 | 보류 |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | artist_holdout | 0.0261653 | 0.8625 | 0.0373732 | 0.9875 | 0.0967819 | 0.875 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | artist_holdout | 0.022793 | 0.8625 | 0.0472295 | 0.9875 | 0.135578 | 0.9625 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | artist_holdout | 0.022793 | 0.8625 | 0.0472295 | 0.9875 | 0.135578 | 0.9625 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | artist_holdout | 0.022793 | 0.8625 | 0.0472295 | 0.9875 | 0.135578 | 0.9625 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | artist_holdout | 0.022793 | 0.8625 | 0.0472295 | 0.9875 | 0.135578 | 0.9625 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | row_holdout | 0.035194 | 1 | 0.0430224 | 1 | 0.14279 | 0.975 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | row_holdout | 0.0326401 | 1 | 0.0519889 | 1 | 0.191573 | 1 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | row_holdout | 0.0326401 | 1 | 0.0519889 | 1 | 0.191573 | 1 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | row_holdout | 0.0326401 | 1 | 0.0519889 | 1 | 0.191573 | 1 | 채택 후보 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | row_holdout | 0.0326401 | 1 | 0.0519889 | 1 | 0.191573 | 1 | 채택 후보 |

## 채택 판단

| candidate | decision | artist_holdout_MdAPE_prob | artist_holdout_MAPE_prob | artist_holdout_p95_prob |
| --- | --- | --- | --- | --- |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | 보류 | 0.85 | 0.625 | 0.4625 |
| stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | 보류 | 0.8125 | 0.55 | 0.45 |
| stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | 채택 후보 | 0.8625 | 0.9875 | 0.875 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min100_cap0.25 | 채택 후보 | 0.8625 | 0.9875 | 0.9625 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min150_cap0.25 | 채택 후보 | 0.8625 | 0.9875 | 0.9625 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | 채택 후보 | 0.8625 | 0.9875 | 0.9625 |
| stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min50_cap0.25 | 채택 후보 | 0.8625 | 0.9875 | 0.9625 |

## 해석

- `delta`는 `PP-Y2 기준 오차 - 후보 오차`이므로 양수일수록 후보가 좋다.
- artist holdout 개선 확률이 row holdout보다 낮으면, 작가 구성이 바뀔 때 성능 변동이 있다는 뜻이다.
- 채택 후보는 바로 서비스 확정이 아니라, Cold 개선 후보로 최종 정책 비교에 올릴 수 있다는 의미다.
