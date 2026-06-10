# PP-HCOEF23 Warm Huber 남은 오차 원인 분석

- 작성일: 2026-06-08 04:24
- 목적: 현재 Warm 1순위 후보 `hcoef_stable`이 남기는 오차를 validation/OOF 기준으로 분해.
- 최소 비교 기준: `current_70_30`.
- 이 실험은 새 보정값을 test/0604에서 고르지 않음.

## 1. 실험 설계

- 입력: HCOEF22의 후보 예측 산출물.
- 기준 후보: `hcoef_stable`.
- 비교 후보: `current_70_30`, HCOEF22 목적별 라우팅 후보.
- 분석 축:
  - 유사 표본 수와 coverage.
  - quantile width.
  - 후보 간 예측 gap.
  - 작품 크기.
  - 재료/지지체 bucket.
  - service confidence tier.
- validation row OOF와 artist OOF에서 위험 구간을 먼저 찾고, fixed test/0604는 확인용으로만 사용.

## 2. 전체 성능 재확인

| scope | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_stable | delta_MAPE_vs_stable | delta_p95_APE_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | hcoef22_route_mape_guard | 829 | 0.2672 | 0.3694 | 0.9790 | 1.3069 | -0.0059 | -0.0050 | -0.0045 |
| 0604_stress | hcoef22_route_p95_guard | 829 | 0.2724 | 0.3712 | 0.9836 | 1.3068 | -0.0006 | -0.0032 | 0.0001 |
| 0604_stress | hcoef_stable | 829 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | 0.0000 | 0.0000 | 0.0000 |
| 0604_stress | hcoef22_route_any2_guard | 829 | 0.2748 | 0.3719 | 0.9790 | 1.3063 | 0.0017 | -0.0024 | -0.0045 |
| 0604_stress | current_70_30 | 829 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0049 | 0.0030 | 0.0036 |
| fixed_confirmation | hcoef_stable | 607 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | 0.0000 | 0.0000 | 0.0000 |
| fixed_confirmation | current_70_30 | 607 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0017 | 0.0018 | 0.0267 |
| fixed_confirmation | hcoef22_route_any2_guard | 607 | 0.1408 | 0.2732 | 0.8100 | 0.3990 | 0.0019 | 0.0002 | 0.0036 |
| fixed_confirmation | hcoef22_route_p95_guard | 607 | 0.1412 | 0.2734 | 0.8161 | 0.3991 | 0.0024 | 0.0005 | 0.0097 |
| fixed_confirmation | hcoef22_route_mape_guard | 607 | 0.1448 | 0.2726 | 0.8164 | 0.3988 | 0.0060 | -0.0004 | 0.0101 |
| validation_oof_artist | hcoef22_route_mape_guard | 519 | 0.1250 | 0.2068 | 0.6397 | 0.3231 | -0.0010 | -0.0015 | -0.0083 |
| validation_oof_artist | hcoef22_route_any2_guard | 519 | 0.1258 | 0.2067 | 0.6398 | 0.3232 | -0.0002 | -0.0015 | -0.0082 |
| validation_oof_artist | hcoef_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_artist | hcoef22_route_p95_guard | 519 | 0.1277 | 0.2074 | 0.6397 | 0.3237 | 0.0017 | -0.0008 | -0.0083 |
| validation_oof_artist | current_70_30 | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |
| validation_oof_row | hcoef22_route_mape_guard | 519 | 0.1250 | 0.2068 | 0.6394 | 0.3224 | -0.0010 | -0.0014 | -0.0085 |
| validation_oof_row | hcoef_stable | 519 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | 0.0000 | 0.0000 | 0.0000 |
| validation_oof_row | hcoef22_route_any2_guard | 519 | 0.1263 | 0.2070 | 0.6398 | 0.3233 | 0.0003 | -0.0012 | -0.0082 |
| validation_oof_row | hcoef22_route_p95_guard | 519 | 0.1290 | 0.2076 | 0.6394 | 0.3233 | 0.0030 | -0.0006 | -0.0085 |
| validation_oof_row | current_70_30 | 519 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0045 | 0.0028 | 0.0101 |

## 3. validation 기준 위험 구간

- `qwidth_band = qwidth_extreme`: validation 평균 MAPE 악화 `0.0874`, p95 악화 `0.3066`, 방향 `방향성 약함`.
- `gap_band = gap_020_plus`: validation 평균 MAPE 악화 `0.0825`, p95 악화 `0.2198`, 방향 `방향성 약함`.
- `svc_group_n_band = n_10_19`: validation 평균 MAPE 악화 `0.0448`, p95 악화 `0.3015`, 방향 `방향성 약함`.
- `svc_group_level = artist`: validation 평균 MAPE 악화 `0.0560`, p95 악화 `0.2241`, 방향 `방향성 약함`.
- `pred_spread_band = spread_extreme`: validation 평균 MAPE 악화 `0.0562`, p95 악화 `0.2215`, 방향 `방향성 약함`.

| segment_col | segment_value | n_row | n_artist | validation_mean_delta_MAPE | validation_mean_delta_p95 | validation_mean_over50 | bias_direction | risk_reason | fixed_confirm_delta_MAPE | fixed_confirm_delta_p95 | stress0604_confirm_delta_MAPE | stress0604_confirm_delta_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwidth_band | qwidth_extreme | 104 | 104 | 0.0874 | 0.3066 | 0.1346 | 방향성 약함 | p95 큰 오차 위험 | 0.1451 | 1.1304 | 0.0637 | 0.0125 |
| gap_band | gap_020_plus | 76 | 76 | 0.0825 | 0.2198 | 0.1711 | 방향성 약함 | p95 큰 오차 위험 | 0.1853 | 0.8870 | 0.1303 | 0.0165 |
| svc_group_n_band | n_10_19 | 160 | 160 | 0.0448 | 0.3015 | 0.1437 | 방향성 약함 | p95 큰 오차 위험 | 0.0503 | 0.4992 | 0.0173 | -0.1194 |
| svc_group_level | artist | 252 | 252 | 0.0560 | 0.2241 | 0.1270 | 방향성 약함 | p95 큰 오차 위험 | 0.0682 | 0.3255 | 0.0022 | 0.0033 |
| pred_spread_band | spread_extreme | 104 | 104 | 0.0562 | 0.2215 | 0.1250 | 방향성 약함 | p95 큰 오차 위험 | 0.1405 | 0.5673 | 0.1286 | 0.0165 |
| qwidth_band | qwidth_high | 73 | 73 | -0.0110 | 0.0332 | 0.0959 | 방향성 약함 | 상대 위험 | 0.0242 | -0.0419 | 0.0014 | 0.0033 |
| gap_band | gap_003_005 | 55 | 55 | -0.0376 | 0.0424 | 0.0727 | 방향성 약함 | 상대 위험 | -0.1015 | -0.3649 | -0.1899 | -0.4661 |
| stable_pred_price_band | (2979253.356, 7498463.56] | 129 | 129 | 0.0120 | 0.0033 | 0.0930 | 방향성 약함 | 상대 위험 | -0.0222 | 0.0204 | 0.0326 | 0.2249 |
| stable_pred_price_band | (7498463.56, inf] | 130 | 130 | 0.0027 | 0.0277 | 0.0769 | 방향성 약함 | 상대 위험 | 0.0918 | 0.7648 | -0.0337 | -0.0402 |
| stable_pred_price_band | (-inf, 1264575.052] | 130 | 130 | 0.0104 | -0.0341 | 0.1000 | 방향성 약함 | 상대 위험 | -0.0477 | -0.2062 | 0.0089 | 0.0033 |
| gap_band | gap_010_020 | 134 | 134 | 0.0143 | -0.0401 | 0.0821 | 방향성 약함 | 상대 위험 | 0.0184 | -0.0529 | -0.0350 | -0.1106 |
| log_area_band | area_q1 | 16 | 16 | -0.0184 | -0.0601 | 0.1250 | 주로 낮게 예측 | 상대 위험 | -0.1588 | -0.5552 | 0.0384 | -0.0067 |
| log_area_band | area_q4 | 15 | 15 | 0.0128 | -0.1066 | 0.0667 | 주로 낮게 예측 | 상대 위험 | 0.0846 | 0.5116 | -0.0492 | -0.1045 |
| medium_support_bucket_grouped | __MISSING__ | 458 | 458 | 0.0050 | 0.0000 | 0.0917 | 방향성 약함 | 상대 위험 | 0.0063 | 0.0011 |  |  |
| log_area_band | area_unknown | 458 | 458 | 0.0050 | 0.0000 | 0.0917 | 방향성 약함 | 상대 위험 | 0.0052 | 0.0000 | 0.3190 | 0.0165 |
| service_confidence_tier | __MISSING__ | 458 | 458 | 0.0050 | 0.0000 | 0.0917 | 방향성 약함 | 상대 위험 | 0.0063 | 0.0011 |  |  |
| svc_coverage_tier | low_n | 421 | 421 | 0.0022 | 0.0003 | 0.0974 | 방향성 약함 | 상대 위험 | 0.0251 | 0.2038 | -0.0243 | -0.0189 |
| stable_pred_price_band | (1264575.052, 2979253.356] | 130 | 130 | -0.0249 | -0.0274 | 0.0846 | 방향성 약함 | 상대 위험 | -0.0262 | -0.0725 | -0.0009 | -0.0778 |
| pred_spread_band | spread_high | 73 | 73 | -0.0116 | -0.0095 | 0.0822 | 방향성 약함 | 상대 위험 | 0.1028 | 0.7881 | -0.0974 | -0.1886 |
| service_confidence_tier | low | 26 | 26 | 0.0010 | -0.0594 | 0.0769 | 방향성 약함 | 상대 위험 | -0.0018 | 0.2141 | -0.0219 | -0.0115 |

## 4. 잔차 계수 감사

- `signed_residual_log`: 양수면 실제 가격이 예측보다 높아 낮게 예측되는 방향.
- `abs_residual_log`: 양수면 남은 오차 크기가 커지는 위험 방향.
- 아래 계수는 validation/OOF에서만 학습한 해석용 계수이며, 가격 예측 후보로 직접 채택하지 않음.

| scope | target | feature | standardized_coefficient | direction | interpretation |
| --- | --- | --- | --- | --- | --- |
| validation_oof_artist | abs_residual_log | quantile_width | 0.0580 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | stable_ppv8_gap_abs | 0.0520 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | log_area | -0.0385 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | log_area_band_area_q4 | 0.0383 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | l10_price_range_ratio | -0.0348 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | svc_group_level_artist_medium_support_size | -0.0321 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | ppv8_svc_gap_abs | -0.0304 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | log_area_band_area_q3 | 0.0272 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | svc_group_n | 0.0221 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | gap_band_gap_020_plus | 0.0220 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | service_confidence_tier_medium | -0.0173 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_oil__linen | 0.0154 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | gap_band_gap_003_005 | -0.0146 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | qwidth_band_qwidth_low | 0.0139 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | log_area_band_area_q2 | 0.0133 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | svc_group_n_band_n_50_plus | -0.0132 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_other__paper | -0.0128 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | gap_band_gap_005_010 | -0.0125 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | log_area_band_area_unknown | 0.0119 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | stable_svc_gap_abs | -0.0118 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_watercolor__paper | -0.0115 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | svc_group_level_artist_size | -0.0113 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | qwidth_band_qwidth_high | -0.0107 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_other_bucket | -0.0104 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | stable_current_gap_abs | 0.0100 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_oil__canvas | -0.0089 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | qwidth_band_qwidth_mid | 0.0064 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | svc_group_n_band_n_5_9 | 0.0055 | 오차 위험 증가 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_oil__panel | -0.0054 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |
| validation_oof_artist | abs_residual_log | medium_support_bucket_grouped_mixed__other | -0.0051 | 오차 위험 감소 | 양수 계수는 해당 피처가 남은 오차 크기를 키우는 경향을 의미 |

## 5. 후보별 bootstrap 확인

| scope | candidate | n | p_improve_MdAPE | p_improve_MAPE | p_improve_p95_APE | p_improve_all3 | mean_delta_MdAPE_vs_stable | mean_delta_MAPE_vs_stable | mean_delta_p95_APE_vs_stable | mean_delta_RMSE_log_vs_stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_stress | hcoef22_route_mape_guard | 829 | 0.8033 | 1.0000 | 0.7800 | 0.6233 | -0.0048 | -0.0050 | -0.0052 | -0.0010 |
| 0604_stress | hcoef22_route_any2_guard | 829 | 0.6367 | 1.0000 | 0.7233 | 0.4700 | -0.0012 | -0.0023 | -0.0031 | -0.0016 |
| 0604_stress | hcoef22_route_p95_guard | 829 | 0.6167 | 1.0000 | 0.4467 | 0.2733 | -0.0015 | -0.0032 | -0.0028 | -0.0009 |
| 0604_stress | current_70_30 | 829 | 0.3233 | 0.0000 | 0.1300 | 0.0000 | 0.0025 | 0.0031 | 0.0049 | 0.0041 |
| fixed_confirmation | hcoef22_route_mape_guard | 607 | 0.2667 | 0.7033 | 0.3600 | 0.0900 | 0.0030 | -0.0005 | 0.0016 | 0.0000 |
| fixed_confirmation | hcoef22_route_any2_guard | 607 | 0.2300 | 0.3800 | 0.3600 | 0.0467 | 0.0018 | 0.0003 | 0.0015 | 0.0002 |
| fixed_confirmation | hcoef22_route_p95_guard | 607 | 0.2300 | 0.2600 | 0.3867 | 0.0233 | 0.0030 | 0.0005 | 0.0036 | 0.0003 |
| fixed_confirmation | current_70_30 | 607 | 0.4900 | 0.0300 | 0.5500 | 0.0100 | -0.0002 | 0.0019 | -0.0036 | 0.0008 |
| validation_oof_artist | hcoef22_route_mape_guard | 519 | 0.7300 | 0.9500 | 0.5433 | 0.3867 | -0.0022 | -0.0015 | -0.0009 | -0.0021 |
| validation_oof_artist | hcoef22_route_p95_guard | 519 | 0.6100 | 0.8667 | 0.5467 | 0.3233 | -0.0010 | -0.0008 | -0.0004 | -0.0015 |
| validation_oof_artist | hcoef22_route_any2_guard | 519 | 0.6333 | 0.9933 | 0.4633 | 0.2767 | -0.0008 | -0.0015 | 0.0015 | -0.0020 |
| validation_oof_artist | current_70_30 | 519 | 0.2567 | 0.0000 | 0.3667 | 0.0000 | 0.0027 | 0.0028 | 0.0056 | 0.0040 |
| validation_oof_row | hcoef22_route_mape_guard | 519 | 0.6533 | 0.9200 | 0.6233 | 0.3800 | -0.0016 | -0.0014 | -0.0039 | -0.0028 |
| validation_oof_row | hcoef22_route_p95_guard | 519 | 0.4133 | 0.7967 | 0.6367 | 0.2233 | 0.0010 | -0.0007 | -0.0047 | -0.0020 |
| validation_oof_row | hcoef22_route_any2_guard | 519 | 0.3667 | 0.9500 | 0.4967 | 0.1700 | 0.0010 | -0.0012 | -0.0013 | -0.0018 |
| validation_oof_row | current_70_30 | 519 | 0.2167 | 0.0000 | 0.3500 | 0.0000 | 0.0032 | 0.0029 | 0.0052 | 0.0040 |

## 6. 판단

- HCOEF23은 새 운영 기본 후보를 만들기 위한 실험이 아니라, 다음 기준가/계수 조정 실험의 원인 근거를 만드는 실험임.
- 현재 운영 기본 후보는 `hcoef_stable` 유지.
- 위험 구간이 validation row OOF와 artist OOF에서 동시에 반복되면 HCOEF24/HCOEF25에서만 보정 후보로 사용.
- fixed test 또는 0604에서만 보이는 위험은 보정 기준으로 사용하지 않고 운영 stress risk로만 기록.

## 7. 다음 실험 방향

- HCOEF24:
  - validation에서 확인된 위험 구간을 기준으로 기준가 생성 방식을 세분화.
  - 작가 전체, 작가+크기, 작가+재료/지지체, 작가+크기+재료/지지체 기준가와 fallback 순서를 비교.
- HCOEF25:
  - Huber 계수 조정형 잔차 보정.
  - 기준가 신뢰도, 후보 간 gap, quantile width, medium/support bucket을 저차원 피처로 사용.
  - cap/strength를 작게 제한하고 반복 OOF를 우선 적용.

## 8. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/risk_segments.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `reports/result_report.md`
- `reports/result_report.html`
