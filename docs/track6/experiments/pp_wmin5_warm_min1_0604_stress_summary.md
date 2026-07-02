# PP-WMIN5 Warm WMIN4 min1 채택 후보 0604 stress 안전성 확인

- 작성일: 2026-06-12 22:38
- 목적: WMIN4 채택 후보 `min1_huber_refit_partial`이 0604 신규 라벨 stress에서 현행 PP258 대비 명확히 악화되는지 확인한다.
- 금지: 0604 결과로 후보나 경계값을 선택하지 않는다. 0604는 안전 확인 전용이다.
- PP258 기준: 신규 입력 raw 호환 PP258 report-layer proxy. exact PP258 upstream raw adapter가 아직 없으므로, 현재 서비스 adapter와 같은 proxy 입력 매핑을 사용한다.
- WMIN4 기준: validation에서 선택된 partial Huber refit을 그대로 학습하고 0604에는 한 번만 적용한다.

## 1. Gate 판단

- status: `pass_continue`
- reason: WMIN4 0604 stress가 PP258 proxy 대비 명확한 악화를 보이지 않음 (MAPE delta -0.057663, p95 delta -0.084486). PP-WMIN6 이후 진행 가능.
- p95 tolerance: 0.010, MAPE tolerance: 0.005

## 2. 0604 전체 지표

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | Within_30 | Within_50 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wmin4_min1_70_30_basis | 829 | 0.223930 | 0.319215 | 0.890999 | 0.946087 | 0.618818 | 0.808203 |
| wmin4_min1_huber_refit_partial | 829 | 0.214745 | 0.319691 | 0.902571 | 0.944335 | 0.621230 | 0.806996 |
| current_ppv8_service_primary | 829 | 0.229792 | 0.335885 | 0.927338 | 0.712419 | 0.599517 | 0.790109 |
| wmin5_min1_svc_numeric_seed_mean | 829 | 0.217860 | 0.365669 | 0.998117 | 1.141187 | 0.601930 | 0.767189 |
| pp258_report_layer_proxy | 829 | 0.277935 | 0.377354 | 0.987056 | 1.311738 | 0.527141 | 0.714113 |
| current_v01_70_30 | 829 | 0.277935 | 0.377354 | 0.987056 | 1.311738 | 0.527141 | 0.714113 |

## 3. WMIN4 vs PP258 proxy

| candidate_candidate | n_candidate | MdAPE_candidate | MAPE_candidate | p95_APE_candidate | RMSE_log_candidate | Within_30_candidate | Within_50_candidate | candidate_baseline | n_baseline | MdAPE_baseline | MAPE_baseline | p95_APE_baseline | RMSE_log_baseline | Within_30_baseline | Within_50_baseline | delta_MdAPE_candidate_minus_baseline | delta_MAPE_candidate_minus_baseline | delta_p95_APE_candidate_minus_baseline | delta_RMSE_log_candidate_minus_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmin4_min1_huber_refit_partial | 829 | 0.214745 | 0.319691 | 0.902571 | 0.944335 | 0.621230 | 0.806996 | pp258_report_layer_proxy | 829 | 0.277935 | 0.377354 | 0.987056 | 1.311738 | 0.527141 | 0.714113 | -0.063190 | -0.057663 | -0.084486 | -0.367403 |

## 4. svc_group_level별 악화 분해

| candidate_candidate | svc_group_level | n_candidate | MdAPE_candidate | MAPE_candidate | p95_APE_candidate | RMSE_log_candidate | Within_30_candidate | Within_50_candidate | candidate_baseline | n_baseline | MdAPE_baseline | MAPE_baseline | p95_APE_baseline | RMSE_log_baseline | Within_30_baseline | Within_50_baseline | delta_MdAPE_candidate_minus_baseline | delta_MAPE_candidate_minus_baseline | delta_p95_APE_candidate_minus_baseline | delta_RMSE_log_candidate_minus_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmin4_min1_huber_refit_partial | artist_size | 395 | 0.226104 | 0.336021 | 0.967590 | 1.105510 | 0.594937 | 0.817722 | pp258_report_layer_proxy | 224 | 0.213813 | 0.353344 | 0.848729 | 1.006227 | 0.607143 | 0.709821 | 0.012292 | -0.017324 | 0.118861 | 0.099283 |
| wmin4_min1_huber_refit_partial | artist | 166 | 0.429106 | 0.494931 | 0.950561 | 1.055632 | 0.295181 | 0.590361 | pp258_report_layer_proxy | 412 | 0.306260 | 0.377377 | 0.987056 | 1.583513 | 0.492718 | 0.740291 | 0.122847 | 0.117554 | -0.036496 | -0.527881 |
| wmin4_min1_huber_refit_partial | artist_medium_support_size | 268 | 0.124116 | 0.187080 | 0.591316 | 0.516674 | 0.861940 | 0.925373 | pp258_report_layer_proxy | 91 | 0.173476 | 0.223807 | 0.759713 | 0.771581 | 0.791209 | 0.901099 | -0.049360 | -0.036727 | -0.168397 | -0.254907 |

## 5. svc_coverage_tier별 악화 분해

| candidate_candidate | svc_coverage_tier | n_candidate | MdAPE_candidate | MAPE_candidate | p95_APE_candidate | RMSE_log_candidate | Within_30_candidate | Within_50_candidate | candidate_baseline | n_baseline | MdAPE_baseline | MAPE_baseline | p95_APE_baseline | RMSE_log_baseline | Within_30_baseline | Within_50_baseline | delta_MdAPE_candidate_minus_baseline | delta_MAPE_candidate_minus_baseline | delta_p95_APE_candidate_minus_baseline | delta_RMSE_log_candidate_minus_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmin4_min1_huber_refit_partial | medium_n | 68 | 0.223642 | 0.289446 | 0.851075 | 0.605181 | 0.632353 | 0.808824 | pp258_report_layer_proxy | 155 | 0.237578 | 0.341655 | 0.885100 | 0.743507 | 0.554839 | 0.709677 | -0.013935 | -0.052209 | -0.034024 | -0.138326 |
| wmin4_min1_huber_refit_partial | low_n | 759 | 0.214745 | 0.322821 | 0.912858 | 0.970096 | 0.619236 | 0.806324 | pp258_report_layer_proxy | 569 | 0.253729 | 0.353368 | 0.964523 | 1.467864 | 0.567663 | 0.764499 | -0.038984 | -0.030547 | -0.051665 | -0.497769 |
| wmin4_min1_huber_refit_partial | high_n | 2 | 0.160354 | 0.160354 | 0.240684 | 0.209644 | 1.000000 | 1.000000 | pp258_report_layer_proxy | 87 | 0.454364 | 0.539289 | 1.114341 | 1.001775 | 0.321839 | 0.505747 | -0.294010 | -0.378935 | -0.873657 | -0.792131 |

## 6. svc_group_n_bin별 악화 분해

| candidate_candidate | svc_group_n_bin | n_candidate | MdAPE_candidate | MAPE_candidate | p95_APE_candidate | RMSE_log_candidate | Within_30_candidate | Within_50_candidate | candidate_baseline | n_baseline | MdAPE_baseline | MAPE_baseline | p95_APE_baseline | RMSE_log_baseline | Within_30_baseline | Within_50_baseline | delta_MdAPE_candidate_minus_baseline | delta_MAPE_candidate_minus_baseline | delta_p95_APE_candidate_minus_baseline | delta_RMSE_log_candidate_minus_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wmin4_min1_huber_refit_partial | 10_19 | 89 | 0.254882 | 0.429649 | 0.940954 | 0.727200 | 0.561798 | 0.719101 | pp258_report_layer_proxy | 199.000000 | 0.285392 | 0.392213 | 0.884966 | 0.756956 | 0.537688 | 0.728643 | -0.030510 | 0.037436 | 0.055988 | -0.029756 |
| wmin4_min1_huber_refit_partial | 5_9 | 243 | 0.214745 | 0.307423 | 0.926944 | 1.082514 | 0.604938 | 0.806584 | pp258_report_layer_proxy | 435.000000 | 0.248369 | 0.335213 | 0.987056 | 1.634665 | 0.570115 | 0.760920 | -0.033625 | -0.027790 | -0.060113 | -0.552151 |
| wmin4_min1_huber_refit_partial | 20_49 | 50 | 0.095351 | 0.265689 | 0.742309 | 0.562125 | 0.660000 | 0.800000 | pp258_report_layer_proxy | 90.000000 | 0.197901 | 0.335054 | 0.896495 | 0.625974 | 0.600000 | 0.766667 | -0.102550 | -0.069364 | -0.154186 | -0.063849 |
| wmin4_min1_huber_refit_partial | 50_plus | 2 | 0.160354 | 0.160354 | 0.240684 | 0.209644 | 1.000000 | 1.000000 | pp258_report_layer_proxy | 105.000000 | 0.532539 | 0.560037 | 1.087982 | 1.045434 | 0.266667 | 0.447619 | -0.372185 | -0.399682 | -0.847298 | -0.835790 |
| wmin4_min1_huber_refit_partial | 1_4 | 445 | 0.210971 | 0.311183 | 0.905796 | 0.938045 | 0.635955 | 0.824719 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |

## 산출물

- `outputs/0604_candidate_predictions.csv`
- `outputs/0604_overall_metrics.csv`
- `outputs/0604_wmin4_vs_pp258_comparison.csv`
- `outputs/0604_slice_*_comparison.csv`
- `artifacts/run_config.json`
