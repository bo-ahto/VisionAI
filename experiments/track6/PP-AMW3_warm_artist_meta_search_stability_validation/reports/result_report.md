# PP-AMW3 Warm 작가 메타 + 검색 피처 보정 안정성 검증

## 1. 실행 요약

- 목적: PP-AMW2 Warm 작가 메타 + 검색 피처 보정 후보의 안정성 검증
- 방식: frozen PP-V8 예측값 위에서 AMW1/H29 validation 보정값을 재구성
- 검증: row bootstrap, artist bootstrap, artist 70% subsample
- 반복 수: 1000회
- 한계: 새 split마다 PP-V8/AMW 보정값을 재학습한 full repeated split은 아님
- 운영 코드 변경: 없음

판단:
- artist bootstrap에서 MdAPE/MAPE/p95 개선 확률이 모두 높아야 운영 후보로 격상 가능
- 한 지표만 좋아지는 후보는 목적별 방어 후보로만 관리

## 2. 후보 선정

| candidate | role | selection_basis |
| --- | --- | --- |
| baseline_ppv8_compact_blend_mape_guarded | baseline | PP-V8 compact blend 기준 후보 |
| stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 |
| stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 |
| stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 |
| stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 |

## 3. 고정 validation/test 지표

| experiment_id | candidate | role | selection_basis | split | n | RMSE_log | MdAPE | MAPE | p95_APE | Within_30 | Within_50 | over_3x_n | under_1_3x_n | delta_vs_baseline_MdAPE | delta_vs_baseline_MAPE | delta_vs_baseline_p95_APE | delta_vs_baseline_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW3 | baseline_ppv8_compact_blend_mape_guarded | baseline | PP-V8 compact blend 기준 후보 | test | 607 | 0.402820 | 0.163169 | 0.281619 | 0.931104 | 0.736409 | 0.859967 | 6 | 7 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW3 | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | test | 607 | 0.402915 | 0.162370 | 0.280455 | 0.929941 | 0.731466 | 0.863262 | 6 | 7 | -0.000800 | -0.001164 | -0.001164 | 0.000094 |
| PP-AMW3 | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | test | 607 | 0.403135 | 0.160963 | 0.279194 | 0.926388 | 0.734761 | 0.863262 | 6 | 7 | -0.002206 | -0.002425 | -0.004717 | 0.000315 |
| PP-AMW3 | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | test | 607 | 0.403247 | 0.163467 | 0.279089 | 0.926927 | 0.734761 | 0.863262 | 6 | 7 | 0.000297 | -0.002529 | -0.004178 | 0.000426 |
| PP-AMW3 | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | test | 607 | 0.404228 | 0.164669 | 0.279733 | 0.926068 | 0.738056 | 0.859967 | 6 | 7 | 0.001500 | -0.001886 | -0.005037 | 0.001408 |
| PP-AMW3 | baseline_ppv8_compact_blend_mape_guarded | baseline | PP-V8 compact blend 기준 후보 | validation | 519 | 0.372063 | 0.154389 | 0.254387 | 0.808363 | 0.722543 | 0.888247 | 4 | 4 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| PP-AMW3 | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | validation | 519 | 0.372129 | 0.151647 | 0.253078 | 0.784793 | 0.728324 | 0.888247 | 4 | 4 | -0.002742 | -0.001309 | -0.023570 | 0.000066 |
| PP-AMW3 | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | validation | 519 | 0.372295 | 0.153545 | 0.251537 | 0.761076 | 0.730250 | 0.888247 | 4 | 5 | -0.000845 | -0.002851 | -0.047287 | 0.000232 |
| PP-AMW3 | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | validation | 519 | 0.372374 | 0.153603 | 0.251302 | 0.761076 | 0.732177 | 0.888247 | 4 | 5 | -0.000786 | -0.003085 | -0.047287 | 0.000310 |
| PP-AMW3 | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | validation | 519 | 0.370941 | 0.153282 | 0.249995 | 0.745821 | 0.734104 | 0.886320 | 3 | 5 | -0.001107 | -0.004393 | -0.062542 | -0.001122 |

## 4. 추천 판단

| candidate | role | decision | test_MdAPE | test_MAPE | test_p95_APE | delta_MdAPE_vs_baseline | delta_MAPE_vs_baseline | delta_p95_APE_vs_baseline | artist_bootstrap_MdAPE_prob | artist_bootstrap_MAPE_prob | artist_bootstrap_p95_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | 반복 검증 후보 | 0.162370 | 0.280455 | 0.929941 | -0.000800 | -0.001164 | -0.001164 | 0.694000 | 1.000000 | 0.847000 |
| stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | 반복 검증 후보 | 0.160963 | 0.279194 | 0.926388 | -0.002206 | -0.002425 | -0.004717 | 0.756000 | 1.000000 | 0.869000 |
| stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | 평균/큰오차 방어 후보 | 0.163467 | 0.279089 | 0.926927 | 0.000297 | -0.002529 | -0.004178 | 0.696000 | 1.000000 | 0.868000 |
| stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | 평균/큰오차 방어 후보 | 0.164669 | 0.279733 | 0.926068 | 0.001500 | -0.001886 | -0.005037 | 0.522000 | 0.923000 | 0.723000 |

## 5. bootstrap 요약

| experiment_id | split | candidate | role | selection_basis | bootstrap_mode | iterations | median_n | delta_MdAPE_median | delta_MdAPE_ci_low | delta_MdAPE_ci_high | delta_MdAPE_prob_improve | delta_MAPE_median | delta_MAPE_ci_low | delta_MAPE_ci_high | delta_MAPE_prob_improve | delta_p95_APE_median | delta_p95_APE_ci_low | delta_p95_APE_ci_high | delta_p95_APE_prob_improve | delta_RMSE_log_median | delta_RMSE_log_ci_low | delta_RMSE_log_ci_high | delta_RMSE_log_prob_improve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-AMW3 | test | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | artist_bootstrap | 1000 | 607.000000 | 0.001458 | -0.005032 | 0.004444 | 0.694000 | 0.001140 | 0.000651 | 0.001711 | 1.000000 | 0.006736 | -0.001528 | 0.014749 | 0.847000 | -0.000082 | -0.000686 | 0.000470 | 0.380000 |
| PP-AMW3 | test | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | artist_subsample_70pct | 1000 | 425.000000 | 0.001435 | -0.004702 | 0.004313 | 0.751000 | 0.001159 | 0.000751 | 0.001510 | 1.000000 | 0.005269 | -0.001309 | 0.012971 | 0.846000 | -0.000109 | -0.000483 | 0.000317 | 0.334000 |
| PP-AMW3 | test | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | row_bootstrap | 1000 | 607.000000 | 0.001455 | -0.004938 | 0.004444 | 0.710000 | 0.001171 | 0.000703 | 0.001618 | 1.000000 | 0.006398 | -0.001316 | 0.014749 | 0.824000 | -0.000062 | -0.000580 | 0.000405 | 0.384000 |
| PP-AMW3 | test | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | artist_bootstrap | 1000 | 607.000000 | 0.002374 | -0.004246 | 0.006834 | 0.756000 | 0.002369 | 0.001240 | 0.003654 | 1.000000 | 0.013362 | -0.003426 | 0.041999 | 0.869000 | -0.000297 | -0.001699 | 0.001017 | 0.339000 |
| PP-AMW3 | test | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | artist_subsample_70pct | 1000 | 425.000000 | 0.002633 | -0.002110 | 0.006128 | 0.844000 | 0.002408 | 0.001516 | 0.003255 | 1.000000 | 0.009276 | -0.002673 | 0.037712 | 0.874000 | -0.000343 | -0.001249 | 0.000686 | 0.279000 |
| PP-AMW3 | test | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | row_bootstrap | 1000 | 607.000000 | 0.002543 | -0.003620 | 0.006902 | 0.793000 | 0.002441 | 0.001383 | 0.003451 | 1.000000 | 0.012292 | -0.002922 | 0.037767 | 0.834000 | -0.000233 | -0.001432 | 0.000840 | 0.328000 |
| PP-AMW3 | test | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | artist_bootstrap | 1000 | 607.000000 | 0.001776 | -0.004743 | 0.006487 | 0.696000 | 0.002474 | 0.001232 | 0.003886 | 1.000000 | 0.013399 | -0.004942 | 0.042055 | 0.868000 | -0.000408 | -0.002036 | 0.001117 | 0.322000 |
| PP-AMW3 | test | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | artist_subsample_70pct | 1000 | 425.000000 | 0.001933 | -0.002798 | 0.005793 | 0.753000 | 0.002501 | 0.001502 | 0.003422 | 1.000000 | 0.008985 | -0.003534 | 0.037712 | 0.864000 | -0.000469 | -0.001498 | 0.000738 | 0.243000 |
| PP-AMW3 | test | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | row_bootstrap | 1000 | 607.000000 | 0.001729 | -0.004119 | 0.006733 | 0.723000 | 0.002525 | 0.001365 | 0.003681 | 1.000000 | 0.012292 | -0.003534 | 0.043345 | 0.834000 | -0.000328 | -0.001823 | 0.000940 | 0.310000 |
| PP-AMW3 | test | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | artist_bootstrap | 1000 | 607.000000 | 0.000215 | -0.008146 | 0.008401 | 0.522000 | 0.001922 | -0.000802 | 0.004533 | 0.923000 | 0.012417 | -0.021303 | 0.076676 | 0.723000 | -0.001228 | -0.004124 | 0.001368 | 0.189000 |
| PP-AMW3 | test | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | artist_subsample_70pct | 1000 | 425.000000 | -0.000005 | -0.007008 | 0.005964 | 0.500000 | 0.001930 | 0.000224 | 0.003400 | 0.984000 | 0.011336 | -0.019726 | 0.061855 | 0.803000 | -0.001478 | -0.003067 | 0.000601 | 0.103000 |
| PP-AMW3 | test | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | row_bootstrap | 1000 | 607.000000 | 0.000180 | -0.008559 | 0.007516 | 0.520000 | 0.001871 | -0.000331 | 0.004078 | 0.946000 | 0.015150 | -0.019689 | 0.071960 | 0.782000 | -0.001335 | -0.003414 | 0.000682 | 0.093000 |
| PP-AMW3 | validation | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | artist_bootstrap | 1000 | 519.000000 | 0.000041 | -0.003605 | 0.004446 | 0.508000 | 0.001325 | 0.000821 | 0.001846 | 1.000000 | 0.006741 | -0.001680 | 0.025423 | 0.820000 | -0.000037 | -0.000662 | 0.000521 | 0.458000 |
| PP-AMW3 | validation | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | artist_subsample_70pct | 1000 | 364.000000 | 0.000318 | -0.003450 | 0.004015 | 0.540000 | 0.001302 | 0.000944 | 0.001673 | 1.000000 | 0.006900 | -0.001408 | 0.023555 | 0.917000 | -0.000091 | -0.000422 | 0.000396 | 0.350000 |
| PP-AMW3 | validation | stack_amw11_h2913_wa0.5_wh0.5_cap0p03 | conservative_balanced | validation에서 세 지표가 모두 개선되고 보정 폭이 작은 후보 | row_bootstrap | 1000 | 519.000000 | 0.000184 | -0.003534 | 0.004440 | 0.525000 | 0.001298 | 0.000814 | 0.001772 | 1.000000 | 0.006741 | -0.001659 | 0.025423 | 0.824000 | -0.000080 | -0.000617 | 0.000424 | 0.385000 |
| PP-AMW3 | validation | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | artist_bootstrap | 1000 | 519.000000 | 0.000432 | -0.006258 | 0.007813 | 0.542000 | 0.002870 | 0.001722 | 0.004090 | 1.000000 | 0.013862 | -0.004281 | 0.054500 | 0.832000 | -0.000169 | -0.001607 | 0.001155 | 0.418000 |
| PP-AMW3 | validation | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | artist_subsample_70pct | 1000 | 364.000000 | 0.000428 | -0.004630 | 0.006286 | 0.590000 | 0.002838 | 0.001991 | 0.003674 | 1.000000 | 0.014316 | -0.002455 | 0.049480 | 0.917000 | -0.000287 | -0.001054 | 0.000834 | 0.307000 |
| PP-AMW3 | validation | stack_amw05_h2913_wa1_wh1_cap0p05 | test_all_metric_exploratory | test에서 MdAPE/MAPE/p95가 모두 개선된 탐색 후보 | row_bootstrap | 1000 | 519.000000 | 0.000421 | -0.006301 | 0.007803 | 0.558000 | 0.002821 | 0.001670 | 0.003940 | 1.000000 | 0.013685 | -0.004970 | 0.054084 | 0.830000 | -0.000255 | -0.001543 | 0.000919 | 0.344000 |
| PP-AMW3 | validation | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | artist_bootstrap | 1000 | 519.000000 | 0.000011 | -0.006717 | 0.008035 | 0.504000 | 0.003113 | 0.001779 | 0.004548 | 1.000000 | 0.014011 | -0.004915 | 0.069261 | 0.835000 | -0.000209 | -0.002005 | 0.001324 | 0.415000 |
| PP-AMW3 | validation | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | artist_subsample_70pct | 1000 | 364.000000 | -0.000046 | -0.005351 | 0.006336 | 0.498000 | 0.003074 | 0.002098 | 0.004020 | 1.000000 | 0.014342 | -0.002455 | 0.055227 | 0.917000 | -0.000398 | -0.001264 | 0.000970 | 0.287000 |
| PP-AMW3 | validation | stack_amw01_h2913_wa1_wh1_cap0p05 | test_mape_exploratory | test MAPE 기준 상위 탐색 후보 | row_bootstrap | 1000 | 519.000000 | 0.000029 | -0.006738 | 0.008236 | 0.509000 | 0.003047 | 0.001715 | 0.004320 | 1.000000 | 0.014011 | -0.005031 | 0.070830 | 0.833000 | -0.000345 | -0.001895 | 0.001062 | 0.340000 |
| PP-AMW3 | validation | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | artist_bootstrap | 1000 | 519.000000 | 0.001093 | -0.008085 | 0.012931 | 0.567000 | 0.004389 | 0.001831 | 0.006991 | 0.999000 | 0.027941 | -0.007196 | 0.067212 | 0.920000 | 0.001156 | -0.001136 | 0.003464 | 0.834000 |
| PP-AMW3 | validation | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | artist_subsample_70pct | 1000 | 364.000000 | 0.001019 | -0.005710 | 0.010757 | 0.602000 | 0.004394 | 0.002544 | 0.006154 | 1.000000 | 0.031764 | -0.000712 | 0.063404 | 0.971000 | 0.001065 | -0.000426 | 0.002798 | 0.912000 |
| PP-AMW3 | validation | stack_amw01_h2901_wa1_wh1_cap0p05 | validation_mape_selected | validation에서 MAPE 우선으로 선택한 후보 | row_bootstrap | 1000 | 519.000000 | 0.000984 | -0.006873 | 0.012644 | 0.585000 | 0.004339 | 0.002163 | 0.006569 | 0.999000 | 0.028308 | -0.005740 | 0.065350 | 0.923000 | 0.001100 | -0.000786 | 0.002955 | 0.873000 |

## 6. 산출물

- `outputs/candidate_selection.csv`
- `outputs/reconstructed_predictions.csv`
- `outputs/point_metrics.csv`
- `outputs/bootstrap_samples.csv`
- `outputs/bootstrap_summary.csv`
- `outputs/recommendations.csv`
- `reports/result_report.md`
- `reports/result_report.html`
