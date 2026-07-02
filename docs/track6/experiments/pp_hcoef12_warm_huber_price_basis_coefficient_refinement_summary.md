# PP-HCOEF12 Warm Huber 개선 후보 운영 패키징 감사

- 작성일: 2026-06-08 00:21
- 목적: HCOEF11에서 안정성이 확인된 Warm Huber 잔차 보정 후보를 재현 가능한 실험 패키지로 저장하고, 저장 모델 재로딩 후 예측 동일성을 확인.
- 기준 후보: `current_70_30`.
- 패키징 후보: `hcoef2_size_reliability_cap005_s050`.
- 패키지 파일: `experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/artifacts/warm_hcoef12_hcoef3_stable_residual_huber.joblib`.
- 주의: 이 산출물은 운영 반영 전 실험 패키지이며, production artifact를 덮어쓰지 않음.

## 1. 실행 결론

- 판단: Warm 개선 후보의 운영 전 패키징 감사 통과.
- fixed test 성능: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
- 저장 모델을 다시 불러와 validation/test/0604 예측이 direct rebuild와 동일한지 확인함.
- 다음 단계는 production v0.1 artifact에 반영할지 여부를 최신 라벨 stress test와 API/운영 정책에서 결정하는 것.

## 2. Readiness Check

| check_name | status | details | max_abs_pred_log_diff | split |
| --- | --- | --- | --- | --- |
| package_file_exists | pass | experiments/track6/PP-HCOEF12_warm_huber_price_basis_coefficient_refinement/artifacts/warm_hcoef12_hcoef3_stable_residual_huber.joblib | nan | nan |
| fixed_test_all3_improved_vs_reference | pass | test MdAPE/MAPE/p95=0.1388/0.2730/0.8064 | nan | nan |
| 0604_all3_improved_vs_reference | pass | 0604 MdAPE/MAPE/p95=0.2731/0.3744/0.9835 | nan | nan |
| row_oof_all3_prob_guard | pass | row_oof all3=1.0000 | nan | nan |
| artist_oof_all3_prob_guard | pass | artist_oof all3=1.0000 | nan | nan |
| validation_packaged_vs_direct_prediction_equal | pass | Packaged model prediction equals direct HCOEF11 rebuild prediction. | 0.0000 | validation |
| test_packaged_vs_direct_prediction_equal | pass | Packaged model prediction equals direct HCOEF11 rebuild prediction. | 0.0000 | test |
| 0604_ex50_packaged_vs_direct_prediction_equal | pass | Packaged model prediction equals direct HCOEF11 rebuild prediction. | 0.0000 | 0604_ex50 |

## 3. Fixed validation/test/0604 재현

| split | candidate | method | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | improve_count_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | reference_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 | 0 |
| validation | hcoef2_size_reliability_cap005_s050 | packaged_residual_huber | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 | 3 |
| test | current_70_30 | reference_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 | 0 |
| test | hcoef2_size_reliability_cap005_s050 | packaged_residual_huber | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 3 |
| 0604_ex50 | current_70_30 | reference_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 0 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | packaged_residual_huber | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 3 |

## 4. HCOEF11 반복 검증 근거

| source_experiment | carried_forward_by | summary_type | validation_scheme | split | candidate | metric | n_repeats | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | mean_delta_RMSE_log_vs_reference | std_delta_MdAPE_vs_reference | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | mean_improve_count | n_bootstraps | mean_delta | ci025_delta | ci975_delta | improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-HCOEF11 | PP-HCOEF12 | repeated_oof | artist_oof | validation | hcoef2_size_reliability_cap005_s050 | all | 80.0000 | -0.0033 | -0.0016 | -0.0121 | -0.0028 | 0.0012 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 | nan | nan | nan | nan | nan |
| PP-HCOEF11 | PP-HCOEF12 | repeated_oof | row_oof | validation | hcoef2_size_reliability_cap005_s050 | all | 80.0000 | -0.0039 | -0.0019 | -0.0121 | -0.0031 | 0.0010 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.0000 | nan | nan | nan | nan | nan |

## 5. Paired bootstrap 근거

- HCOEF11 결과를 운영 후보 감사 근거로 carry-forward함.
- `delta`가 음수이면 패키징 후보가 기준 후보보다 좋다는 뜻임.
| source_experiment | carried_forward_by | summary_type | validation_scheme | split | candidate | metric | n_repeats | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | mean_delta_RMSE_log_vs_reference | std_delta_MdAPE_vs_reference | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob | mean_improve_count | n_bootstraps | mean_delta | ci025_delta | ci975_delta | improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0101 | 0.0056 | 0.7925 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0028 | -0.0047 | -0.0010 | 0.9995 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0058 | -0.0407 | 0.0417 | 0.6645 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0040 | -0.0056 | -0.0024 | 1.0000 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0029 | -0.0107 | 0.0064 | 0.7650 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0029 | -0.0050 | -0.0007 | 0.9935 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0043 | -0.0411 | 0.0435 | 0.6310 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | validation | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0041 | -0.0059 | -0.0019 | 0.9995 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0000 | -0.0089 | 0.0087 | 0.5210 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0018 | -0.0037 | 0.0001 | 0.9710 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0034 | -0.0390 | 0.0498 | 0.4665 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0008 | -0.0027 | 0.0008 | 0.8285 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0005 | -0.0083 | 0.0092 | 0.4785 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0018 | -0.0039 | 0.0003 | 0.9585 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | 0.0037 | -0.0390 | 0.0498 | 0.4460 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | test | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0009 | -0.0027 | 0.0010 | 0.8130 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0028 | -0.0156 | 0.0169 | 0.6830 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0047 | -0.0014 | 1.0000 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0049 | -0.0201 | 0.0039 | 0.8850 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | row_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0040 | -0.0053 | -0.0027 | 1.0000 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MdAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0019 | -0.0158 | 0.0189 | 0.6400 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_MAPE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0030 | -0.0054 | -0.0005 | 0.9925 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_p95_APE_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0049 | -0.0482 | 0.0182 | 0.7470 |
| PP-HCOEF11 | PP-HCOEF12 | paired_bootstrap | artist_bootstrap | 0604_ex50 | hcoef2_size_reliability_cap005_s050 | delta_RMSE_log_vs_reference | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | 2000.0000 | -0.0041 | -0.0060 | -0.0020 | 0.9995 |

## 6. Huber 계수 해석

- 계수는 표준화된 피처 기준. 절대 가격 단위 계수가 아니라 방향성과 상대 영향 비교용.
- `svc_fallback`은 단순 fallback 기준가를 그대로 밀어주는 역할이 아니라 과한 기준가 방향을 낮추는 보정축으로 작동.
- `shrunk_svc_prior`, `current_shrunk_huber_gap`, `ppv8_defensive`는 완화된 기준가와 오차 안정화 후보를 반영하는 축.
- `log_area`, `svc_group_n_log`, `svc_prior_iqr`는 보정 신뢰도와 크기 관련 잔차 방향을 제한하는 보조축.
| candidate | source_candidate | feature | coefficient_on_scaled_feature | abs_coefficient | alpha | cap | strength | experiment_id | feature_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_fallback | -0.4718 | 0.4718 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | price_basis |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_svc_prior | 0.2221 | 0.2221 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | price_basis |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_shrunk_huber_gap | 0.1308 | 0.1308 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | basis_gap |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | ppv8_defensive | 0.1081 | 0.1081 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | reliability_or_shape |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | shrunk_huber_refit | 0.0877 | 0.0877 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | reliability_or_shape |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | raw_shrunk_prior_gap | -0.0580 | 0.0580 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | basis_gap |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | log_area | 0.0570 | 0.0570 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | reliability_or_shape |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | current_ppv8_gap | 0.0491 | 0.0491 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | basis_gap |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_group_n_log | -0.0121 | 0.0121 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | reliability_or_shape |
| hcoef2_size_reliability_cap005_s050 | residual_huber_resid_basis_size_reliability_alpha0.01_cap0.05_s0.50 | svc_prior_iqr | 0.0008 | 0.0008 | 0.0100 | 0.0500 | 0.5000 | PP-HCOEF12 | reliability_or_shape |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_50pct_n | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 237 | 30 | 30 | 153 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3744 | 0.9835 | 240 | 26 | 26 | 152 |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3994 | 0.1405 | 0.2748 | 0.8331 | 74 | 24 | 24 | 17 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3985 | 0.1388 | 0.2730 | 0.8064 | 72 | 26 | 26 | 17 |
| validation | current_70_30 | 519 | 0.0027 | 0.0209 | 0.3285 | 0.1305 | 0.2110 | 0.6580 | 48 | 9 | 9 | 11 |
| validation | hcoef2_size_reliability_cap005_s050 | 519 | 0.0021 | 0.0181 | 0.3247 | 0.1260 | 0.2082 | 0.6479 | 46 | 9 | 9 | 10 |

## 8. 산출물

- `artifacts/warm_hcoef12_hcoef3_stable_residual_huber.joblib`
- `artifacts/operational_candidate_manifest.json`
- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/operational_readiness_checks.csv`