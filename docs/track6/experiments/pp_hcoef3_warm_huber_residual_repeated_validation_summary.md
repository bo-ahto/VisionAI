# PP-HCOEF3 Warm Huber 잔차 보정 반복 검증

- 작성일: 2026-06-07 22:24
- 목적: PP-HCOEF2의 보수적 잔차 보정 후보가 row/artist 반복 OOF에서도 유지되는지 확인.
- 반복 설정: row OOF 20회, artist OOF 20회, 각 5 folds.

## 1. 실행 결론

- 반복 검증 통과 후보: `hcoef2_size_reliability_cap005_s050`.
- 후보 `hcoef2_size_reliability_cap005_s050` fixed test MdAPE/MAPE/p95: `0.1388` / `0.2730` / `0.8064`.
- fixed test 개선만으로는 채택하지 않고, 반복 OOF 개선 확률을 함께 본다.

## 2. 반복 OOF 요약

| validation_scheme | candidate | mean_delta_MdAPE | mean_delta_MAPE | mean_delta_p95_APE | std_delta_MdAPE | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | mean_improve_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_oof | hcoef2_size_reliability_cap005_s050 | -0.0030 | -0.0016 | -0.0117 | 0.0015 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| artist_oof | hcoef2_gap_cap003_s075 | -0.0023 | -0.0009 | -0.0159 | 0.0011 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| artist_oof | hcoef2_size_reliability_cap003_s075 | -0.0023 | -0.0013 | -0.0125 | 0.0008 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| artist_oof | hcoef1_size_reliability_cap012_s025 | -0.0009 | -0.0017 | -0.0099 | 0.0012 | 0.7500 | 1.0000 | 1.0000 | 0.7500 | 2.7500 |
| row_oof | hcoef2_size_reliability_cap005_s050 | -0.0037 | -0.0017 | -0.0109 | 0.0012 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| row_oof | hcoef2_size_reliability_cap003_s075 | -0.0030 | -0.0015 | -0.0110 | 0.0012 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| row_oof | hcoef2_gap_cap003_s075 | -0.0027 | -0.0012 | -0.0151 | 0.0014 | 1.0000 | 0.9500 | 1.0000 | 0.9500 | 2.9500 |
| row_oof | hcoef1_size_reliability_cap012_s025 | -0.0021 | -0.0018 | -0.0080 | 0.0013 | 0.9500 | 1.0000 | 1.0000 | 0.9500 | 2.9500 |

## 3. Fixed validation/test/0604 확인

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE | delta_MAPE | delta_p95_APE | improve_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 | 0 |
| test | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 | 0 |
| 0604_ex50 | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 0 |
| validation | hcoef2_size_reliability_cap003_s075 | 0.1263 | 0.2085 | 0.6459 | 0.3255 | -0.0042 | -0.0025 | -0.0122 | 3 |
| test | hcoef2_size_reliability_cap003_s075 | 0.1392 | 0.2735 | 0.8059 | 0.3991 | -0.0013 | -0.0013 | -0.0272 | 3 |
| 0604_ex50 | hcoef2_size_reliability_cap003_s075 | 0.2749 | 0.3746 | 0.9834 | 1.3083 | -0.0031 | -0.0027 | -0.0036 | 3 |
| validation | hcoef2_size_reliability_cap005_s050 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 | 3 |
| test | hcoef2_size_reliability_cap005_s050 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 3 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 3 |
| validation | hcoef2_gap_cap003_s075 | 0.1256 | 0.2088 | 0.6369 | 0.3259 | -0.0050 | -0.0022 | -0.0211 | 3 |
| test | hcoef2_gap_cap003_s075 | 0.1406 | 0.2745 | 0.8318 | 0.4000 | 0.0001 | -0.0003 | -0.0012 | 2 |
| 0604_ex50 | hcoef2_gap_cap003_s075 | 0.2752 | 0.3749 | 0.9834 | 1.3083 | -0.0027 | -0.0025 | -0.0036 | 3 |
| validation | hcoef1_size_reliability_cap012_s025 | 0.1283 | 0.2082 | 0.6507 | 0.3251 | -0.0022 | -0.0028 | -0.0074 | 3 |
| test | hcoef1_size_reliability_cap012_s025 | 0.1378 | 0.2728 | 0.8169 | 0.3982 | -0.0026 | -0.0020 | -0.0161 | 3 |
| 0604_ex50 | hcoef1_size_reliability_cap012_s025 | 0.2698 | 0.3738 | 0.9834 | 1.3067 | -0.0082 | -0.0036 | -0.0036 | 3 |

## 4. 주요 계수

- 계수는 표준화된 피처 기준이다. 방향성과 상대 영향 비교용이다.
| candidate | source_candidate | feature | coefficient_on_scaled_feature | abs_coefficient | alpha | cap | strength |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | svc_fallback | -0.4769 | 0.4769 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | svc_fallback | -0.4769 | 0.4769 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_fallback | -0.4718 | 0.4718 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | svc_fallback | -0.3812 | 0.3812 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | shrunk_svc_prior | 0.2222 | 0.2222 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | shrunk_svc_prior | 0.2222 | 0.2222 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_svc_prior | 0.2221 | 0.2221 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | shrunk_svc_prior | 0.1570 | 0.1570 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | current_shrunk_huber_gap | 0.1314 | 0.1314 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | current_shrunk_huber_gap | 0.1314 | 0.1314 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_shrunk_huber_gap | 0.1308 | 0.1308 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | ppv8_defensive | 0.1156 | 0.1156 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | ppv8_defensive | 0.1105 | 0.1105 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | ppv8_defensive | 0.1105 | 0.1105 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | ppv8_defensive | 0.1081 | 0.1081 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | current_shrunk_huber_gap | 0.1077 | 0.1077 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | shrunk_huber_refit | 0.1015 | 0.1015 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | shrunk_huber_refit | 0.0902 | 0.0902 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | shrunk_huber_refit | 0.0902 | 0.0902 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_huber_refit | 0.0877 | 0.0877 | 0.0100 | 0.0500 | 0.5000 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | raw_shrunk_prior_gap | -0.0579 | 0.0579 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | log_area | 0.0571 | 0.0571 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | log_area | 0.0571 | 0.0571 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | log_area | 0.0570 | 0.0570 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | current_ppv8_gap | 0.0521 | 0.0521 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | current_ppv8_gap | 0.0498 | 0.0498 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | current_ppv8_gap | 0.0498 | 0.0498 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_ppv8_gap | 0.0491 | 0.0491 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_gap_cap003_s075 | residual_huber_resid_basis_gap_alpha0.0001_cap0.03_s0.75 | svc_group_n_log | -0.0131 | 0.0131 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_group_n_log | -0.0121 | 0.0121 | 0.0100 | 0.0500 | 0.5000 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | svc_group_n_log | -0.0121 | 0.0121 | 0.0001 | 0.1200 | 0.2500 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | svc_group_n_log | -0.0121 | 0.0121 | 0.0001 | 0.0300 | 0.7500 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_prior_iqr | 0.0008 | 0.0008 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap003_s075 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.03_s0.75 | svc_prior_iqr | 0.0008 | 0.0008 | 0.0001 | 0.0300 | 0.7500 |
| hcoef1_size_reliability_cap012_s025 | residual_huber_resid_basis_size_reliability_alpha0.0001_cap0.12_s0.25 | svc_prior_iqr | 0.0008 | 0.0008 | 0.0001 | 0.1200 | 0.2500 |

## 5. 잔차/큰 오차 요약

| split | candidate | median_residual_log | mean_residual_log | residual_std | over_2x_n | under_half_n | ape_gt_100pct_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| validation | hcoef2_size_reliability_cap003_s075 | 0.0004 | 0.0182 | 0.3250 | 9 | 10 | 9 |
| test | hcoef2_size_reliability_cap003_s075 | -0.0023 | -0.0148 | 0.3988 | 26 | 17 | 26 |
| 0604_ex50 | hcoef2_size_reliability_cap003_s075 | 0.0633 | 0.3287 | 1.2663 | 27 | 152 | 27 |
| validation | hcoef2_size_reliability_cap005_s050 | 0.0021 | 0.0181 | 0.3247 | 9 | 10 | 9 |
| test | hcoef2_size_reliability_cap005_s050 | -0.0039 | -0.0148 | 0.3985 | 26 | 17 | 26 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.0608 | 0.3278 | 1.2660 | 26 | 152 | 26 |
| validation | hcoef2_gap_cap003_s075 | 0.0004 | 0.0185 | 0.3254 | 9 | 10 | 9 |
| test | hcoef2_gap_cap003_s075 | -0.0048 | -0.0150 | 0.3997 | 26 | 17 | 26 |
| 0604_ex50 | hcoef2_gap_cap003_s075 | 0.0633 | 0.3285 | 1.2663 | 27 | 151 | 27 |
| validation | hcoef1_size_reliability_cap012_s025 | 0.0005 | 0.0188 | 0.3246 | 9 | 10 | 9 |
| test | hcoef1_size_reliability_cap012_s025 | -0.0050 | -0.0142 | 0.3980 | 26 | 17 | 26 |
| 0604_ex50 | hcoef1_size_reliability_cap012_s025 | 0.0558 | 0.3259 | 1.2654 | 26 | 151 | 26 |

## 6. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `artifacts/experiment_config.json`