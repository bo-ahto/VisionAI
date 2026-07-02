# PP-HCOEF11 Warm Huber 안정 후보 확장 검증

- 작성일: 2026-06-08 00:08
- 목적: 현재 Warm 70:30 기준 후보 위에 작은 Huber 잔차 보정을 더한 후보가 반복 검증과 bootstrap에서도 안정적인지 확인.
- 기준 후보: `current_70_30`.
- 검증 후보: `hcoef2_size_reliability_cap005_s050`.
- 반복 설정: row OOF 80회, artist OOF 80회, 각 5 folds.
- paired bootstrap: split별 row/artist 단위 2000회.

## 1. 실행 결론

- 판단: Warm 개선 후보로 유지한다. fixed test와 반복 OOF에서 기준 후보 대비 개선이 재현된다.
- fixed test 성능: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
- fixed test 개선폭: MdAPE `-0.0017`, MAPE `-0.0018`, p95_APE `-0.0267`.
- 0604 외부 테스트 성능: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
- 해석: 이 후보는 새 기준가를 크게 바꾸는 실험이 아니라, 70:30 기준 후보가 남긴 잔차 중 크기/기준가 신뢰도 축으로 설명되는 작은 방향만 Huber가 계수로 보정하는 방식이다.

## 2. 반복 OOF 요약

| summary_type | validation_scheme | split | candidate | metric | n_repeats | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | mean_delta_RMSE_log_vs_reference | std_delta_MdAPE_vs_reference | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | mean_improve_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| repeated_oof | artist_oof | validation | hcoef2_size_reliability_cap005_s050 | all | 80 | -0.0033 | -0.0016 | -0.0121 | -0.0028 | 0.0012 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |
| repeated_oof | row_oof | validation | hcoef2_size_reliability_cap005_s050 | all | 80 | -0.0039 | -0.0019 | -0.0121 | -0.0031 | 0.0010 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 |

## 3. Fixed validation/test/0604 확인

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | improve_count_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 | 0 |
| validation | hcoef2_size_reliability_cap005_s050 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 | 3 |
| test | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 | 0 |
| test | hcoef2_size_reliability_cap005_s050 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 3 |
| 0604_ex50 | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 0 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 3 |

## 4. Paired bootstrap 요약

- `delta`가 음수이면 검증 후보가 기준 후보보다 좋다는 뜻이다.
| summary_type | validation_scheme | split | candidate | metric | n_repeats | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | mean_delta_RMSE_log_vs_reference | std_delta_MdAPE_vs_reference | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | mean_improve_count | n_bootstraps | mean_delta | ci025_delta | ci975_delta | improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0101 | 0.0056 | 0.7925 |
| paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0028 | -0.0047 | -0.0010 | 0.9995 |
| paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0058 | -0.0407 | 0.0417 | 0.6645 |
| paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0040 | -0.0056 | -0.0024 | 1.0000 |
| paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0029 | -0.0107 | 0.0064 | 0.7650 |
| paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0029 | -0.0050 | -0.0007 | 0.9935 |
| paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0043 | -0.0411 | 0.0435 | 0.6310 |
| paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0041 | -0.0059 | -0.0019 | 0.9995 |
| paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0000 | -0.0089 | 0.0087 | 0.5210 |
| paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0018 | -0.0037 | 0.0001 | 0.9710 |
| paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0034 | -0.0390 | 0.0498 | 0.4665 |
| paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0008 | -0.0027 | 0.0008 | 0.8285 |
| paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0005 | -0.0083 | 0.0092 | 0.4785 |
| paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0018 | -0.0039 | 0.0003 | 0.9585 |
| paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0037 | -0.0390 | 0.0498 | 0.4460 |
| paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0009 | -0.0027 | 0.0010 | 0.8130 |
| paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0028 | -0.0156 | 0.0169 | 0.6830 |
| paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0047 | -0.0014 | 1.0000 |
| paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0049 | -0.0201 | 0.0039 | 0.8850 |
| paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0040 | -0.0053 | -0.0027 | 1.0000 |
| paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0019 | -0.0158 | 0.0189 | 0.6400 |
| paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0054 | -0.0005 | 0.9925 |
| paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0049 | -0.0482 | 0.0182 | 0.7470 |
| paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0041 | -0.0060 | -0.0020 | 0.9995 |

## 5. Huber 계수 해석

- 계수는 표준화된 피처 기준이다. 절대 가격 공식의 원 단위 계수가 아니라 방향성과 상대 영향 비교용이다.
- `svc_fallback` 계수가 음수이고 `shrunk_svc_prior` 계수가 양수인 것은, 단순 fallback 기준가를 그대로 믿기보다 완화된 기준가와 기존 후보의 차이를 작게 조정한다는 의미다.
- `log_area`, `svc_group_n_log`, `svc_prior_iqr`는 직접 가격을 크게 바꾸는 주 피처라기보다 보정 신뢰도와 크기 관련 잔차 방향을 제한하는 보조 피처다.
| candidate | source_candidate | feature | coefficient_on_scaled_feature | abs_coefficient | alpha | cap | strength | experiment_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_fallback | -0.4718 | 0.4718 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_svc_prior | 0.2221 | 0.2221 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_shrunk_huber_gap | 0.1308 | 0.1308 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | ppv8_defensive | 0.1081 | 0.1081 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_huber_refit | 0.0877 | 0.0877 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | log_area | 0.0570 | 0.0570 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_ppv8_gap | 0.0491 | 0.0491 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_group_n_log | -0.0121 | 0.0121 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_prior_iqr | 0.0008 | 0.0008 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF11 |

## 6. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_50pct_n | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 237 | 30 | 30 | 153 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3744 | 0.9835 | 240 | 26 | 26 | 152 |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3994 | 0.1405 | 0.2748 | 0.8331 | 74 | 24 | 24 | 17 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3985 | 0.1388 | 0.2730 | 0.8064 | 72 | 26 | 26 | 17 |
| validation | current_70_30 | 519 | 0.0027 | 0.0209 | 0.3285 | 0.1305 | 0.2110 | 0.6580 | 48 | 9 | 9 | 11 |
| validation | hcoef2_size_reliability_cap005_s050 | 519 | 0.0021 | 0.0181 | 0.3247 | 0.1260 | 0.2082 | 0.6479 | 46 | 9 | 9 | 10 |
| validation_artist_oof_repeat0 | hcoef2_size_reliability_cap005_s050 | 519 | 0.0028 | 0.0181 | 0.3261 | 0.1280 | 0.2094 | 0.6493 | 46 | 9 | 9 | 10 |
| validation_row_oof_repeat0 | hcoef2_size_reliability_cap005_s050 | 519 | 0.0006 | 0.0186 | 0.3253 | 0.1264 | 0.2085 | 0.6497 | 46 | 9 | 9 | 10 |

## 7. 다음 보정 방향

- HCOEF3 안정 후보는 Warm 개선 후보로 유지한다.
- HCOEF4~HCOEF10에서 확인된 공격형 basis-Huber, segmented median, risk-gated 구조는 기본 후보를 넘지 못했으므로 동일 구조를 반복하지 않는다.
- 다음 실험은 이 후보를 운영 패키징하거나, 작품별 큰 오차 원인 진단 리포트를 보강하는 방향이 우선이다.

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/fold_metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `artifacts/experiment_config.json`