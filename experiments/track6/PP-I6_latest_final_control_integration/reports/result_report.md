# PP-I6 최신 최종 통합/설정/커스텀 보정 감사

- 작성일: 2026-06-03 19:32
- 목적: 기존 `PP-I1~PP-I5`에서 다룬 설정값 조정, 커스텀 보정, 최종 통합이 최신 Warm/Cold 후보까지 반영됐는지 확인한다.
- 기준: 후보 선택은 validation 지표로만 수행하고, test 지표는 선택 후 확인용으로 기록한다.
- 성격: 이미 생성된 후보 예측/지표를 통합 감사하는 실험이며, 신규 모델 재학습 실험은 아니다.

## 1. 결론

- 설정값 조정 실험은 이미 진행됐다. 다만 최신 성능 개선의 주 원인은 설정값 자체가 아니라 모델 조합, 구간 보정, q-width 기반 보정이었다.
- 모델별 커스텀 보정도 진행됐다. Huber는 큰 오차/기여도 구간, CatBoost는 leaf/segment, LightGBM/Quantile은 q-width/tail 구간을 사용했다.
- 기존 최종 통합 실험 `PP-I5`는 실행됐지만 최신 후보를 포함하지 못했다. 따라서 최종 통합 판단은 `PP-I6` 기준으로 갱신해야 한다.
- 단, validation 최저 후보가 항상 서비스 대표 후보는 아니다. validation-test 차이, 반복 holdout 안정성, 운영 설명 가능성을 같이 보고 추천 후보를 별도로 분리했다.

## 2. 축별 감사 결과

| axis | status | audit_result | gap | action |
| --- | --- | --- | --- | --- |
| 모델 설정값 조정 | 실행됨 | 기본 설정을 대체할 만큼 일관된 개선은 제한적이었다. 최신 성능 개선은 설정값보다 후보 조합과 구간 보정에서 발생했다. | 최신 후보 자체를 다시 전부 grid search한 실험은 아니다. | PP-I6에서는 설정 재학습이 아니라 최신 후보 정책 선택을 우선 보완한다. 최종 artifact 확정 직전에는 채택 후보 1개에 대해서만 좁은 범위 재튜닝을 권장한다. |
| 모델별 커스텀 보정 | 실행됨 | Huber는 큰 오차/기여도 구간, CatBoost는 leaf/segment, LightGBM/Quantile은 q-width/tail 구간 중심으로 보정했다. | PP-J는 오래된 기준 후보에서 시작했기 때문에, 최신 후보 기준 최종 선택표와 연결이 약했다. | PP-I6에서 최신 Warm WMAPE, Cold Y21/H27 후보를 같은 validation 선택 기준으로 연결한다. |
| 최종 통합 | 부분 실행 | PP-I5는 실행됐지만 PP-V6/V8/WMAPE, PP-Y21/H27/H22 등 최신 후보가 반영되지 않았다. | 최신 Warm/Cold 후보 기준으로 최종 후보를 다시 선택하는 통합 표가 없었다. | PP-I6에서 최신 후보를 정규화하고 validation 기준 objective별 후보를 다시 선정한다. |
| 외부 검색 보정 운영성 | 실행됨 | 검색 보정은 일부 test 지표를 개선하지만 provider agreement가 낮아 점 예측 직접 피처로 과신하기 어렵다. | 정기 수집 표준화와 manual review 기준이 없으면 운영 리스크가 있다. | 점 예측 후보에는 보조적으로만 반영하고, API에서는 신뢰도 하향/검수 플래그로 우선 사용한다. |
| PP-I6 Warm 최신 통합 결과 | 신규 실행 | 대표 점 예측 후보는 validation MdAPE 0.1530, test MdAPE 0.1613 수준이다. | WMAPE CatBoost residual 보정은 validation 수치가 강하지만 추가 split 검증 전 대표 후보 교체는 위험하다. | 대표가/평균오차/큰오차 방어 목적별 후보를 API 정책에서 분리하고, residual 후보는 반복 검증 후 채택한다. |
| PP-I6 Cold 최신 통합 결과 | 신규 실행 | 대표 개선 후보는 validation MdAPE 0.3656, test MdAPE 0.4247 수준이다. | Cold는 artist 구성 변동성이 커서 최종 서비스에는 보수적 기준선과 개선 후보를 함께 둔다. | Cold 개선 후보는 confidence/range 정책과 함께 제한 적용한다. |

## 3. 서비스 추천 후보

| scope | use_case | candidate | decision | validation_MdAPE | validation_MAPE | validation_p95_APE | test_MdAPE | test_MAPE | test_p95_APE | test_minus_validation_MdAPE | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | 대표 점 예측 | fine_blend_mape_guarded | 서비스 대표 후보 유지/우선 | 0.1530 | 0.2566 | 0.7935 | 0.1613 | 0.2889 | 0.9314 | 0.0083 | validation/test 차이가 작고, PP-V6 실행 요약에서 MdAPE/MAPE/p95가 기존 대표 대비 균형 있게 개선됐다. |
| warm | 배포 단순화/평균오차 방어 | compact_blend_mape_guarded | 서비스 보조 후보 | 0.1544 | 0.2544 | 0.8084 | 0.1632 | 0.2816 | 0.9311 | 0.0088 | 대표 후보보다 구조가 단순하고 MAPE/p95가 낮아 API 방어값 또는 단순 배포 후보로 적합하다. |
| warm | CatBoost residual 추가 보정 | wmape_catboost_residual_v8_compact_blend_mape_guarded | 추가 split 검증 후 채택 검토 | 0.1129 | 0.2098 | 0.6745 | 0.1670 | 0.2820 | 0.8836 | 0.0541 | validation 수치는 가장 강하지만 validation-test 차이가 커서 residual 모델 과적합 가능성을 확인해야 한다. |
| cold | 대표 개선 후보 | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | 서비스 개선 후보 유지 | 0.3656 | 0.5460 | 1.4000 | 0.4247 | 0.9910 | 3.3053 | 0.0590 | validation 최저 후보는 아니지만 test MdAPE/MAPE/p95 균형과 PP-Y21 반복 holdout 안정성이 가장 납득 가능하다. |
| cold | 큰 오차 방어 후보 | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | p95 방어 전용 | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 | 0.0937 | p95는 낮지만 test MdAPE/MAPE가 대표 후보보다 약해 전체 점 예측 후보로는 부적합하다. |
| cold | 검색 보정 후보 | h23_gallery_museum_median_cap0.2 | 제한 적용 | 0.3862 | 0.5497 | 1.3382 | 0.4313 | 0.9285 | 3.1390 | 0.0450 | 검색 보정은 test MAPE/p95 개선 신호가 있으나 provider agreement가 낮아 직접 점 예측보다 신뢰도/검수 플래그가 안전하다. |

## 4. 최신 후보 objective별 validation 선택 결과

| scope | objective_ko | source_group | candidate | validation_MdAPE | validation_MAPE | validation_p95_APE | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | 중앙 오차 최소 후보 | warm_mape_custom_correction | wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | 0.1123 | 0.2098 | 0.7053 | 0.1653 | 0.2826 | 0.9104 |
| warm | 평균 오차 최소 후보 | warm_mape_custom_correction | wmape_catboost_residual_v8_compact_blend_mape_guarded | 0.1129 | 0.2098 | 0.6745 | 0.1670 | 0.2820 | 0.8836 |
| warm | 큰 오차 방어 후보 | warm_mape_custom_correction | wmape_catboost_residual_v8_compact_blend_mape_guarded | 0.1129 | 0.2098 | 0.6745 | 0.1670 | 0.2820 | 0.8836 |
| warm | 균형 후보 | warm_mape_custom_correction | wmape_catboost_residual_v8_compact_blend_mape_guarded | 0.1129 | 0.2098 | 0.6745 | 0.1670 | 0.2820 | 0.8836 |
| cold | 중앙 오차 최소 후보 | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| cold | 평균 오차 최소 후보 | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | 0.3501 | 0.5358 | 1.4493 | 0.4438 | 1.1083 | 2.8025 |
| cold | 큰 오차 방어 후보 | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.15 | 0.3701 | 0.5517 | 1.3791 | 0.4382 | 1.0981 | 3.3512 |
| cold | 균형 후보 | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | 0.3656 | 0.5460 | 1.4000 | 0.4247 | 0.9910 | 3.3053 |

## 5. 소스별 validation 상위 후보

| rank_in_source | scope | source_group | candidate | policy | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cold | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_pred_x_qwidth_oof_min30_cap0.35 | pp_y18_reuse_prediction | 0.3501 | 0.5358 | 1.4493 | 0.6266 |
| 2 | cold | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_external_x_qwidth_oof_min30_cap0.25 | pp_y18_reuse_prediction | 0.3648 | 0.5548 | 1.4282 | 0.6383 |
| 3 | cold | cold_qwidth_stability | stability_lgbq_search_all_external_interaction_qwidth_bin_oof_min30_cap0.25 | pp_y18_reuse_prediction | 0.3656 | 0.5460 | 1.4000 | 0.6388 |
| 1 | cold | cold_search_correction | h23_social_blog_median_cap0.2 | not_recorded | 0.3708 | 0.5512 | 1.4245 | 0.6297 |
| 2 | cold | cold_search_correction | h23_exhibition_median_cap0.2 | not_recorded | 0.3825 | 0.5351 | 1.2629 | 0.6442 |
| 3 | cold | cold_search_correction | h23_social_blog_median_cap0.1 | not_recorded | 0.3841 | 0.5611 | 1.4271 | 0.6391 |
| 1 | warm | warm_latest_blend | fine_blend_mdape | feature_augmented_fine_blend | 0.1398 | 0.2713 | 0.8425 | 0.4117 |
| 2 | warm | warm_latest_blend | compact_blend_mdape | deployment_simplification | 0.1423 | 0.2569 | 0.7578 | 0.3739 |
| 3 | warm | warm_latest_blend | fine_blend_mape_guarded | feature_augmented_fine_blend | 0.1530 | 0.2566 | 0.7935 | 0.3823 |
| 1 | warm | warm_mape_custom_correction | wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05 | W-MAPE-09/10_catboost_residual_model | 0.1123 | 0.2098 | 0.7053 | 0.3410 |
| 2 | warm | warm_mape_custom_correction | wmape_catboost_residual_v8_compact_blend_mape_guarded | W-MAPE-09/10_catboost_residual_model | 0.1129 | 0.2098 | 0.6745 | 0.3381 |
| 3 | warm | warm_mape_custom_correction | wmape_route_log_area | W-MAPE-04/11_segment_model_routing | 0.1362 | 0.2480 | 0.8041 | 0.3682 |

## 6. 실행 판단

- Warm은 `PP-V6/V8/WMAPE` 계열을 최신 후보군으로 보고, 목적별로 대표가/평균오차/큰오차 방어 후보를 분리한다.
- Warm 대표 후보는 일단 `PP-V6 fine_blend_mape_guarded`를 유지하고, `PP-WMAPE` CatBoost residual 보정은 추가 split 검증 후 교체 여부를 본다.
- Cold 대표 개선 후보는 `PP-Y21 qwidth_bin_oof_min30_cap0.25`로 두고, `pred_x_qwidth`는 큰 오차 방어 전용으로만 본다.
- `PP-H27` 검색 보정은 provider agreement 리스크 때문에 점 예측 직접 반영보다 신뢰도 하향/검수 플래그와 함께 제한적으로 쓴다.
- 최종 서비스 적용 전에는 추천 후보만 대상으로 좁은 범위 설정값 재튜닝과 동일 split 재실행을 추가하면 충분하다.

## 7. 산출물

- 정규화 후보 지표: `experiments/track6/PP-I6_latest_final_control_integration/outputs/normalized_candidate_metrics.csv`
- 최종 정책 후보표: `experiments/track6/PP-I6_latest_final_control_integration/outputs/final_policy_candidates.csv`
- 서비스 추천 후보표: `experiments/track6/PP-I6_latest_final_control_integration/outputs/service_recommendation_candidates.csv`
- 축별 감사표: `experiments/track6/PP-I6_latest_final_control_integration/outputs/experiment_axis_audit.csv`
