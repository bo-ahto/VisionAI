# PP-I7 모델 구조별 커스텀 보정 후속 검증

- 작성일: 2026-06-03 20:28
- 목적: 모델 구조별 약점을 반영한 최신 보정 후보가 서비스 후보로 안정적인지 확인한다.
- 원칙: validation에서 정책 후보를 고르고, test와 bootstrap은 선택 후 안정성 확인으로 사용한다.

## 1. 실행 계획 요약

- Warm: `PP-V6` 대표 후보를 기준으로 `PP-V8` 단순화 후보와 `PP-WMAPE` CatBoost residual 후보를 비교한다.
- Cold: `PP-H23/H26` 검색 보정을 전체 적용하지 않고 `recommended_action`, `qwidth_bin` 조건으로 제한 적용해 비교한다.
- 서비스 비교군 통계 피처는 누수 방지 설계가 필요하므로 이번 실행에서는 계획으로 분리하고, `PP-SVC1`로 후속 실행한다.

## 2. Warm test 결과

| candidate | source_experiment | use_case | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| warm_v6_fine_blend_mape_guarded | PP-V6 | 대표 점 예측 | 0.161296 | 0.288921 | 0.931418 | 0.407920 |
| warm_v8_compact_blend_mape_guarded | PP-V8 | 배포 단순화/평균오차 방어 | 0.163169 | 0.281619 | 0.931104 | 0.402820 |
| warm_wmape_catboost_residual_h29 | PP-WMAPE | 검색 보정 + CatBoost residual | 0.165326 | 0.282636 | 0.910442 | 0.403216 |
| warm_wmape_catboost_residual_v8 | PP-WMAPE | CatBoost residual 보정 | 0.166975 | 0.282041 | 0.883607 | 0.402910 |

## 3. Warm artist bootstrap 안정성

| candidate | delta_MdAPE_median | delta_MdAPE_prob_improve | delta_MAPE_median | delta_MAPE_prob_improve | delta_p95_APE_median | delta_p95_APE_prob_improve |
| --- | --- | --- | --- | --- | --- | --- |
| warm_v8_compact_blend_mape_guarded | -0.004016 | 0.278000 | 0.007172 | 0.882000 | 0.009883 | 0.584000 |
| warm_wmape_catboost_residual_v8 | -0.005379 | 0.184000 | 0.006415 | 0.820000 | 0.006160 | 0.594000 |
| warm_wmape_catboost_residual_h29 | -0.004038 | 0.240000 | 0.005785 | 0.818000 | 0.013438 | 0.618000 |

## 4. Warm 추천 판단

| scope | candidate | split | decision | test_MdAPE | test_MAPE | test_p95_APE | delta_MdAPE_vs_baseline | delta_MAPE_vs_baseline | delta_p95_APE_vs_baseline | artist_bootstrap_MdAPE_prob | artist_bootstrap_MAPE_prob | artist_bootstrap_p95_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warm | warm_v8_compact_blend_mape_guarded | test | 목적별 방어 후보 | 0.163169 | 0.281619 | 0.931104 | -0.001873 | 0.007302 | 0.000314 | 0.278000 | 0.882000 | 0.584000 |
| warm | warm_wmape_catboost_residual_v8 | test | 목적별 방어 후보 | 0.166975 | 0.282041 | 0.883607 | -0.005679 | 0.006879 | 0.047811 | 0.184000 | 0.820000 | 0.594000 |
| warm | warm_wmape_catboost_residual_h29 | test | 목적별 방어 후보 | 0.165326 | 0.282636 | 0.910442 | -0.004030 | 0.006285 | 0.020976 | 0.240000 | 0.818000 | 0.618000 |

## 5. Cold 제한 조건

| condition | description | validation_applied_rate | test_applied_rate |
| --- | --- | --- | --- |
| full | 전체 샘플에 보정 적용 | 1.000000 | 1.000000 |
| action_candidate_only | 검색 action이 candidate_for_h14_h18인 샘플에만 보정 적용 | 0.050854 | 0.335269 |
| qwidth_risk_only | qwidth_bin이 risk인 샘플에만 보정 적용 | 0.339993 | 0.469829 |
| qwidth_caution_risk_only | qwidth_bin이 caution 또는 risk인 샘플에만 보정 적용 | 0.669815 | 0.811229 |
| action_and_caution_risk | 검색 action 후보이면서 caution/risk인 샘플에만 보정 적용 | 0.020705 | 0.193611 |

## 6. Cold validation 선택 후보

| objective | candidate | MdAPE | MAPE | p95_APE | test_MdAPE | test_MAPE | test_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mdape_primary | cold_search_exhibition_cap0.2_full | 0.382526 | 0.535056 | 1.262930 | 0.450190 | 1.138230 | 2.763542 |
| mape_guarded | cold_search_exhibition_cap0.2_qwidth_caution_risk_only | 0.405757 | 0.529325 | 1.233585 | 0.439050 | 1.112580 | 2.763382 |
| p95_guarded | cold_search_exhibition_cap0.2_qwidth_caution_risk_only | 0.405757 | 0.529325 | 1.233585 | 0.439050 | 1.112580 | 2.763382 |

## 7. Cold test 상위 결과

| candidate | policy | MdAPE | MAPE | p95_APE | RMSE_log |
| --- | --- | --- | --- | --- | --- |
| cold_search_news_cap0.2_qwidth_caution_risk_only | search_restricted_qwidth_caution_risk_only | 0.417895 | 0.946161 | 3.140513 | 0.834143 |
| cold_search_gallery_museum_cap0.2_qwidth_caution_risk_only | search_restricted_qwidth_caution_risk_only | 0.424033 | 0.941260 | 3.138994 | 0.834062 |
| cold_search_news_cap0.2_full | search_restricted_full | 0.425322 | 0.953420 | 3.154187 | 0.833754 |
| cold_search_news_cap0.2_qwidth_risk_only | search_restricted_qwidth_risk_only | 0.428048 | 1.033219 | 3.219591 | 0.854643 |
| cold_search_gallery_museum_cap0.2_qwidth_risk_only | search_restricted_qwidth_risk_only | 0.429322 | 1.036945 | 3.219591 | 0.855541 |
| cold_search_gallery_museum_cap0.2_full | search_restricted_full | 0.431277 | 0.928508 | 3.138994 | 0.837833 |
| cold_search_risk_qwidth_action_cap0.2_qwidth_caution_risk_only | search_restricted_qwidth_caution_risk_only | 0.432808 | 1.011861 | 3.182145 | 0.855930 |
| cold_search_risk_qwidth_action_cap0.2_qwidth_risk_only | search_restricted_qwidth_risk_only | 0.434298 | 1.035721 | 3.182145 | 0.859413 |
| cold_search_risk_qwidth_action_cap0.2_full | search_restricted_full | 0.435175 | 1.009412 | 3.182145 | 0.857119 |
| cold_search_news_cap0.2_action_and_caution_risk | search_restricted_action_and_caution_risk | 0.435841 | 0.968598 | 3.154187 | 0.835215 |
| cold_search_news_cap0.2_action_candidate_only | search_restricted_action_candidate_only | 0.436631 | 0.975445 | 3.154187 | 0.834186 |
| cold_search_exhibition_cap0.2_action_candidate_only | search_restricted_action_candidate_only | 0.438653 | 1.176238 | 3.353732 | 0.873083 |
| cold_search_exhibition_cap0.2_qwidth_caution_risk_only | search_restricted_qwidth_caution_risk_only | 0.439050 | 1.112580 | 2.763382 | 0.886622 |
| cold_search_exhibition_cap0.2_action_and_caution_risk | search_restricted_action_and_caution_risk | 0.439289 | 1.153152 | 3.353732 | 0.871060 |
| cold_pp_y2_base | baseline | 0.442147 | 1.048405 | 3.353732 | 0.856668 |
| cold_search_risk_qwidth_action_cap0.2_action_and_caution_risk | search_restricted_action_and_caution_risk | 0.444814 | 1.030807 | 3.353732 | 0.854840 |
| cold_search_risk_qwidth_action_cap0.2_action_candidate_only | search_restricted_action_candidate_only | 0.445625 | 1.027867 | 3.353732 | 0.855225 |
| cold_search_gallery_museum_cap0.2_action_and_caution_risk | search_restricted_action_and_caution_risk | 0.445889 | 0.963697 | 3.138994 | 0.835134 |
| cold_search_exhibition_cap0.2_qwidth_risk_only | search_restricted_qwidth_risk_only | 0.446298 | 1.017936 | 2.763382 | 0.868660 |
| cold_search_gallery_museum_cap0.2_action_candidate_only | search_restricted_action_candidate_only | 0.448053 | 0.950533 | 3.138994 | 0.838263 |

## 8. Cold artist bootstrap 안정성

| candidate | delta_MdAPE_median | delta_MdAPE_prob_improve | delta_MAPE_median | delta_MAPE_prob_improve | delta_p95_APE_median | delta_p95_APE_prob_improve |
| --- | --- | --- | --- | --- | --- | --- |
| cold_search_risk_qwidth_action_cap0.2_qwidth_caution_risk_only | 0.007323 | 0.842000 | 0.035947 | 1.000000 | 0.171587 | 1.000000 |
| cold_search_risk_qwidth_action_cap0.2_full | 0.003186 | 0.672000 | 0.038318 | 1.000000 | 0.171587 | 1.000000 |
| cold_search_gallery_museum_cap0.2_qwidth_caution_risk_only | 0.014857 | 0.902000 | 0.107094 | 1.000000 | 0.199545 | 0.994000 |
| cold_search_exhibition_cap0.2_qwidth_risk_only | -0.001200 | 0.446000 | 0.032278 | 1.000000 | 0.220016 | 0.846000 |
| cold_search_risk_qwidth_action_cap0.2_qwidth_risk_only | 0.002919 | 0.726000 | 0.012879 | 1.000000 | 0.073977 | 0.768000 |
| cold_search_news_cap0.2_qwidth_risk_only | 0.010126 | 0.912000 | 0.015258 | 1.000000 | 0.055575 | 0.734000 |
| cold_search_gallery_museum_cap0.2_qwidth_risk_only | 0.008766 | 0.858000 | 0.011270 | 0.998000 | 0.051823 | 0.728000 |
| cold_search_news_cap0.2_qwidth_caution_risk_only | 0.019819 | 0.958000 | 0.101925 | 0.992000 | 0.199545 | 0.854000 |
| cold_search_gallery_museum_cap0.2_full | 0.010035 | 0.756000 | 0.117195 | 0.988000 | 0.217427 | 0.998000 |
| cold_search_news_cap0.2_full | 0.017371 | 0.906000 | 0.096369 | 0.874000 | 0.199545 | 0.730000 |
| cold_search_exhibition_cap0.2_qwidth_caution_risk_only | 0.007110 | 0.654000 | -0.060330 | 0.304000 | 0.173586 | 0.676000 |
| cold_search_exhibition_cap0.2_full | -0.002452 | 0.462000 | -0.083971 | 0.238000 | 0.045257 | 0.536000 |

## 9. Cold 추천 판단

| scope | candidate | split | decision | test_MdAPE | test_MAPE | test_p95_APE | delta_MdAPE_vs_baseline | delta_MAPE_vs_baseline | delta_p95_APE_vs_baseline | artist_bootstrap_MdAPE_prob | artist_bootstrap_MAPE_prob | artist_bootstrap_p95_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | cold_search_gallery_museum_cap0.2_full | test | 대표 교체 후보 | 0.431277 | 0.928508 | 3.138994 | 0.010871 | 0.119897 | 0.214738 | 0.756000 | 0.988000 | 0.998000 |
| cold | cold_search_gallery_museum_cap0.2_qwidth_caution_risk_only | test | 대표 교체 후보 | 0.424033 | 0.941260 | 3.138994 | 0.018115 | 0.107145 | 0.214738 | 0.902000 | 1.000000 | 0.994000 |
| cold | cold_search_news_cap0.2_qwidth_caution_risk_only | test | 대표 교체 후보 | 0.417895 | 0.946161 | 3.140513 | 0.024253 | 0.102244 | 0.213219 | 0.958000 | 0.992000 | 0.854000 |
| cold | cold_search_news_cap0.2_full | test | 대표 교체 후보 | 0.425322 | 0.953420 | 3.154187 | 0.016826 | 0.094985 | 0.199545 | 0.906000 | 0.874000 | 0.730000 |
| cold | cold_search_risk_qwidth_action_cap0.2_full | test | 대표 교체 후보 | 0.435175 | 1.009412 | 3.182145 | 0.006973 | 0.038993 | 0.171587 | 0.672000 | 1.000000 | 1.000000 |
| cold | cold_search_risk_qwidth_action_cap0.2_qwidth_caution_risk_only | test | 대표 교체 후보 | 0.432808 | 1.011861 | 3.182145 | 0.009339 | 0.036544 | 0.171587 | 0.842000 | 1.000000 | 1.000000 |
| cold | cold_search_news_cap0.2_qwidth_risk_only | test | 대표 교체 후보 | 0.428048 | 1.033219 | 3.219591 | 0.014099 | 0.015186 | 0.134142 | 0.912000 | 1.000000 | 0.734000 |
| cold | cold_search_risk_qwidth_action_cap0.2_qwidth_risk_only | test | 대표 교체 후보 | 0.434298 | 1.035721 | 3.182145 | 0.007850 | 0.012684 | 0.171587 | 0.726000 | 1.000000 | 0.768000 |
| cold | cold_search_gallery_museum_cap0.2_qwidth_risk_only | test | 대표 교체 후보 | 0.429322 | 1.036945 | 3.219591 | 0.012826 | 0.011460 | 0.134142 | 0.858000 | 0.998000 | 0.728000 |
| cold | cold_search_exhibition_cap0.2_qwidth_risk_only | test | 목적별 방어 후보 | 0.446298 | 1.017936 | 2.763382 | -0.004151 | 0.030469 | 0.590351 | 0.446000 | 1.000000 | 0.846000 |
| cold | cold_search_exhibition_cap0.2_qwidth_caution_risk_only | test | 목적별 방어 후보 | 0.439050 | 1.112580 | 2.763382 | 0.003098 | -0.064175 | 0.590351 | 0.654000 | 0.304000 | 0.676000 |
| cold | cold_search_exhibition_cap0.2_full | test | 목적별 방어 후보 | 0.450190 | 1.138230 | 2.763542 | -0.008043 | -0.089826 | 0.590191 | 0.462000 | 0.238000 | 0.536000 |

## 10. 다음 실행

- Warm `PP-WMAPE` residual 후보가 MdAPE를 악화시키고 MAPE/p95만 개선한다면 대표 후보가 아니라 방어 후보로 둔다.
- Cold 검색 보정은 전체 적용보다 제한 적용이 안전한지 보고, 신뢰도/API 정책으로 연결한다.
- 다음 신규 학습 축은 `PP-SVC1` 서비스 비교군 통계 피처다. train 기준 비교군 통계를 만들고 Warm/Cold 모델 입력과 API 표시값을 동시에 검증한다.
