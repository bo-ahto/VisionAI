# PP-HCOEF13 Warm Huber 잔차 위험 원인 진단

- 작성일: 2026-06-08 00:45
- 목적: 현재 Warm 개선 후보가 아직 크게 틀리는 작품군을 기준가 신뢰도, 크기, 재료/지지체, 후보 간 gap 기준으로 정량화.
- 기준 후보: `current_70_30` = 유사 작품 기반 가격 피처 70% + 오차 안정화 후보 30%.
- 진단 후보: `hcoef2_size_reliability_cap005_s050` = 기준 후보 위에 Huber 잔차 보정을 작게 더한 현재 Warm 개선 후보.
- 주의: 이 실험은 새 보정 후보를 채택하지 않고 다음 계수 조정 실험의 원인 지도를 만든다.

## 1. 실행 결론

- 판단: 현재 Warm 개선 후보는 유지한다. HCOEF13은 후보 교체가 아니라 남은 오차 원인을 분리한 진단 실험이다.
- fixed test 성능: MdAPE `0.1388`, MAPE `0.2730`, p95_APE `0.8064`, RMSE_log `0.3988`.
- fixed test 개선폭: MdAPE `-0.0017`, MAPE `-0.0018`, p95_APE `-0.0267`.
- 0604 stress test 성능: MdAPE `0.2731`, MAPE `0.3744`, p95_APE `0.9835`.
- 다음 실험은 validation에서 확인된 위험 구간에 한정해 기준가 shrinkage, fallback, Huber cap/strength, routing을 비교하는 방식이 적절하다.

## 2. Fixed validation/test/0604 성능

| split | candidate | MdAPE | MAPE | p95_APE | RMSE_log | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | improve_count_vs_reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | current_70_30 | 0.1305 | 0.2110 | 0.6580 | 0.3292 | 0.0000 | 0.0000 | 0.0000 | 0 |
| validation | hcoef2_size_reliability_cap005_s050 | 0.1260 | 0.2082 | 0.6479 | 0.3252 | -0.0045 | -0.0028 | -0.0101 | 3 |
| test | current_70_30 | 0.1405 | 0.2748 | 0.8331 | 0.3996 | 0.0000 | 0.0000 | 0.0000 | 0 |
| test | hcoef2_size_reliability_cap005_s050 | 0.1388 | 0.2730 | 0.8064 | 0.3988 | -0.0017 | -0.0018 | -0.0267 | 3 |
| 0604_ex50 | current_70_30 | 0.2779 | 0.3774 | 0.9871 | 1.3117 | 0.0000 | 0.0000 | 0.0000 | 0 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 0.2731 | 0.3744 | 0.9835 | 1.3078 | -0.0049 | -0.0030 | -0.0036 | 3 |

## 3. HCOEF11 반복 검증 근거

- HCOEF13은 반복 검증을 새로 돌리는 실험이 아니므로 HCOEF11의 row/artist OOF 근거를 carry-forward한다.
| validation_scheme | candidate | mean_delta_MdAPE_vs_reference | mean_delta_MAPE_vs_reference | mean_delta_p95_APE_vs_reference | MdAPE_improve_prob | MAPE_improve_prob | p95_improve_prob | all3_improve_prob |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artist_oof | hcoef2_size_reliability_cap005_s050 | -0.0033 | -0.0016 | -0.0121 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| row_oof | hcoef2_size_reliability_cap005_s050 | -0.0039 | -0.0019 | -0.0121 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## 4. Validation 기준 위험 구간 상위

- 아래 표는 test가 아니라 validation에서 본 위험 구간이다. 다음 보정 후보를 고를 때 우선 참고할 수 있다.
| segment_name | segment_value | n | stable_MdAPE | stable_MAPE | stable_p95_APE | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | median_residual_log | stable_worse_than_reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| size_x_basis_n | size00 + n_10_19 | 17 | 0.2320 | 0.4923 | 1.4874 | -0.0239 | -0.0257 | -0.0630 | -0.1590 | False |
| basis_iqr_bucket | iqr_mid | 38 | 0.1830 | 0.4463 | 1.4109 | -0.0003 | -0.0014 | -0.0209 | -0.1180 | False |
| pred_x_basis_n | pred04 + n_10_19 | 13 | 0.1165 | 0.3586 | 1.0912 | -0.0218 | -0.0112 | -0.0408 | 0.0305 | False |
| risk_cause | basis_current_disagreement | 92 | 0.2252 | 0.3703 | 1.0770 | -0.0081 | -0.0022 | -0.0526 | -0.0384 | False |
| basis_level_x_gap | artist_overall + basis_pos | 72 | 0.2132 | 0.3413 | 1.0770 | -0.0166 | -0.0125 | -0.0526 | -0.0586 | False |
| basis_n_bucket | n_10_19 | 106 | 0.1189 | 0.2763 | 1.0448 | -0.0050 | -0.0038 | -0.0501 | -0.0284 | False |
| basis_level_simple | artist_overall | 149 | 0.1910 | 0.3093 | 1.0250 | -0.0146 | -0.0064 | 0.0190 | -0.0119 | True |
| size_x_basis_n | size01 + n_10_19 | 18 | 0.1465 | 0.3047 | 1.0064 | 0.0036 | -0.0056 | -0.0335 | -0.0509 | True |
| ppv8_gap_sign | ppv8_pos | 24 | 0.2540 | 0.3446 | 0.9635 | 0.0117 | 0.0094 | 0.0411 | 0.0878 | True |
| basis_gap_sign | basis_pos | 121 | 0.1761 | 0.2818 | 0.9492 | -0.0250 | -0.0080 | -0.0355 | -0.0145 | False |
| basis_level_x_gap | artist_overall + basis_neg | 59 | 0.1910 | 0.3174 | 0.9030 | 0.0123 | 0.0000 | -0.0378 | 0.0369 | True |
| size_bin | size00 | 104 | 0.1381 | 0.2860 | 0.8833 | -0.0033 | -0.0057 | -0.0029 | -0.0089 | False |
| basis_gap_sign | basis_neg | 112 | 0.1984 | 0.3117 | 0.8720 | -0.0166 | -0.0014 | -0.0044 | 0.0138 | False |
| size_x_basis_n | size04 + n_10_19 | 30 | 0.1209 | 0.2702 | 0.8682 | 0.0050 | 0.0040 | -0.0075 | -0.0378 | True |
| size_bin | size04 | 104 | 0.1409 | 0.2209 | 0.8475 | 0.0037 | -0.0003 | 0.0074 | -0.0244 | True |
| pred_bin | pred04 | 51 | 0.1094 | 0.1950 | 0.8223 | -0.0173 | -0.0080 | -0.0184 | 0.0305 | False |
| basis_iqr_bucket | iqr_high | 51 | 0.1727 | 0.2901 | 0.8221 | -0.0124 | -0.0095 | -0.0284 | 0.0039 | False |
| basis_level_x_gap | artist_detail + basis_neg | 53 | 0.1993 | 0.3054 | 0.8180 | -0.0238 | -0.0031 | -0.0285 | -0.0382 | False |
| pred_bin | pred07 | 52 | 0.1586 | 0.2804 | 0.8110 | -0.0058 | -0.0024 | 0.0245 | -0.0082 | True |
| size_x_basis_n | size00 + n_lt5 | 39 | 0.1176 | 0.2327 | 0.7960 | 0.0065 | -0.0008 | -0.0411 | 0.0556 | True |
| pred_x_basis_n | pred05 + n_10_19 | 13 | 0.0603 | 0.2005 | 0.7805 | -0.0119 | 0.0014 | 0.0440 | 0.0097 | True |
| pred_bin | pred09 | 52 | 0.1603 | 0.2357 | 0.7652 | -0.0019 | -0.0046 | -0.0003 | 0.0260 | False |
| pred_bin | pred02 | 52 | 0.1192 | 0.2023 | 0.7506 | -0.0033 | -0.0012 | 0.0432 | -0.0884 | True |
| pred_x_basis_n | pred08 + n_10_19 | 15 | 0.1304 | 0.1943 | 0.7386 | 0.0213 | 0.0079 | 0.0330 | -0.0373 | True |

## 5. 다음 실험 후보

- `median_residual_log`가 양수이면 과소예측 경향, 음수이면 과대예측 경향이다.
- 이 표는 바로 적용할 보정식이 아니라 다음 HCOEF 실험의 후보 리스트다.
| segment_name | segment_keys | segment_value | n | stable_MdAPE | stable_MAPE | stable_p95_APE | delta_MdAPE_vs_reference | delta_MAPE_vs_reference | delta_p95_APE_vs_reference | median_residual_log | ape_gt_100pct_rate | priority_score | recommended_next_step | guard_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| size_x_basis_n | size_bin+basis_n_bucket | size00 + n_10_19 | 17 | 0.2320 | 0.4923 | 1.4874 | -0.0239 | -0.0257 | -0.0630 | -0.1590 | 0.1765 | 2.1388 | 기준가 표본 수 기반 shrinkage/fallback 재조정 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| basis_iqr_bucket | basis_iqr_bucket | iqr_mid | 38 | 0.1830 | 0.4463 | 1.4109 | -0.0003 | -0.0014 | -0.0209 | -0.1180 | 0.1579 | 1.9752 | IQR 큰 구간의 기준가 영향도 축소 또는 p95 방어 cap 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| ppv8_gap_sign | ppv8_gap_sign | ppv8_pos | 24 | 0.2540 | 0.3446 | 0.9635 | 0.0117 | 0.0094 | 0.0411 | 0.0878 | 0.0417 | 1.6459 | 후보 간 예측 gap이 큰 구간의 routing 또는 보수형 fallback 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |
| size_x_basis_n | size_bin+basis_n_bucket | size01 + n_10_19 | 18 | 0.1465 | 0.3047 | 1.0064 | 0.0036 | -0.0056 | -0.0335 | -0.0509 | 0.0556 | 1.6120 | 기준가 표본 수 기반 shrinkage/fallback 재조정 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |
| basis_level_simple | basis_level_simple | artist_overall | 149 | 0.1910 | 0.3093 | 1.0250 | -0.0146 | -0.0064 | 0.0190 | -0.0119 | 0.0537 | 1.5961 | 반복 과대예측 구간의 작은 하향 residual 보정 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |
| basis_level_x_gap | basis_level_simple+basis_gap_sign | artist_overall + basis_neg | 59 | 0.1910 | 0.3174 | 0.9030 | 0.0123 | 0.0000 | -0.0378 | 0.0369 | 0.0508 | 1.5072 | 후보 간 예측 gap이 큰 구간의 routing 또는 보수형 fallback 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |
| risk_cause | risk_cause | basis_current_disagreement | 92 | 0.2252 | 0.3703 | 1.0770 | -0.0081 | -0.0022 | -0.0526 | -0.0384 | 0.0761 | 1.4857 | 후보 간 예측 gap이 큰 구간의 routing 또는 보수형 fallback 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| pred_x_basis_n | pred_bin+basis_n_bucket | pred04 + n_10_19 | 13 | 0.1165 | 0.3586 | 1.0912 | -0.0218 | -0.0112 | -0.0408 | 0.0305 | 0.0769 | 1.4802 | 기준가 표본 수 기반 shrinkage/fallback 재조정 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| basis_level_x_gap | basis_level_simple+basis_gap_sign | artist_overall + basis_pos | 72 | 0.2132 | 0.3413 | 1.0770 | -0.0166 | -0.0125 | -0.0526 | -0.0586 | 0.0694 | 1.4769 | 후보 간 예측 gap이 큰 구간의 routing 또는 보수형 fallback 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| size_x_basis_n | size_bin+basis_n_bucket | size04 + n_10_19 | 30 | 0.1209 | 0.2702 | 0.8682 | 0.0050 | 0.0040 | -0.0075 | -0.0378 | 0.0333 | 1.4262 | 기준가 표본 수 기반 shrinkage/fallback 재조정 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |
| basis_n_bucket | basis_n_bucket | n_10_19 | 106 | 0.1189 | 0.2763 | 1.0448 | -0.0050 | -0.0038 | -0.0501 | -0.0284 | 0.0566 | 1.3496 | 기준가 표본 수 기반 shrinkage/fallback 재조정 실험 | 현재 최고 후보도 기준보다 낫지만 잔차가 큰 구간이므로 보정 후보로 검증 가능 |
| pred_bin | pred_bin | pred07 | 52 | 0.1586 | 0.2804 | 0.8110 | -0.0058 | -0.0024 | 0.0245 | -0.0082 | 0.0192 | 1.3496 | 예측 가격대/크기 구간별 Huber cap-strength 민감도 실험 | 현재 최고 후보가 기준 70:30보다 나쁜 구간이므로 routing 후보로 검증 필요 |

## 6. Huber 계수 해석

- 계수는 표준화된 피처 기준이다. 실제 가격 단위 계수가 아니라 방향성과 상대 영향 비교용이다.
- 현재 후보는 기준가를 크게 바꾸기보다, 유사 표본 수와 기준가 분산을 참고해 잔차 보정폭을 작게 제한한다.
| candidate | feature | feature_role | coefficient_on_scaled_feature | abs_coefficient | direction | alpha | cap | strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hcoef2_size_reliability_cap005_s050 | svc_fallback | 유사 작품 기반 가격 피처 | -0.4718 | 0.4718 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | shrunk_svc_prior | 완화된 유사 작품 기준가 | 0.2221 | 0.2221 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | current_shrunk_huber_gap | 현재 후보와 Huber 기준선 차이 | 0.1308 | 0.1308 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | ppv8_defensive | 오차 안정화 후보 | 0.1081 | 0.1081 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | shrunk_huber_refit | Huber 기준 예측값 | 0.0877 | 0.0877 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | raw_shrunk_prior_gap | 원 기준가와 완화 기준가 차이 | -0.0580 | 0.0580 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | log_area | 작품 크기 | 0.0570 | 0.0570 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | current_ppv8_gap | 현재 후보와 오차 안정화 후보 차이 | 0.0491 | 0.0491 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | svc_group_n_log | 유사 표본 수 신뢰도 | -0.0121 | 0.0121 | 가격 보정값을 낮추는 방향 | 0.0100 | 0.0500 | 0.5000 |
| hcoef2_size_reliability_cap005_s050 | svc_prior_iqr | 유사 표본 가격 분산 | 0.0008 | 0.0008 | 가격 보정값을 올리는 방향 | 0.0100 | 0.0500 | 0.5000 |

## 7. 잔차/큰 오차 요약

| split | candidate | n | median_residual_log | mean_residual_log | residual_std | ape_median | ape_mean | ape_p95 | ape_gt_50pct_n | ape_gt_100pct_n | over_2x_n | under_half_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | current_70_30 | 829 | 0.0782 | 0.3370 | 1.2677 | 0.2779 | 0.3774 | 0.9871 | 237 | 30 | 30 | 153 |
| 0604_ex50 | hcoef2_size_reliability_cap005_s050 | 829 | 0.0608 | 0.3278 | 1.2660 | 0.2731 | 0.3744 | 0.9835 | 240 | 26 | 26 | 152 |
| test | current_70_30 | 607 | -0.0006 | -0.0119 | 0.3994 | 0.1405 | 0.2748 | 0.8331 | 74 | 24 | 24 | 17 |
| test | hcoef2_size_reliability_cap005_s050 | 607 | -0.0039 | -0.0148 | 0.3985 | 0.1388 | 0.2730 | 0.8064 | 72 | 26 | 26 | 17 |
| validation | current_70_30 | 519 | 0.0027 | 0.0209 | 0.3285 | 0.1305 | 0.2110 | 0.6580 | 48 | 9 | 9 | 11 |
| validation | hcoef2_size_reliability_cap005_s050 | 519 | 0.0021 | 0.0181 | 0.3247 | 0.1260 | 0.2082 | 0.6479 | 46 | 9 | 9 | 10 |

## 8. 큰 오차 작품 예시

- 실제 가격 구간은 운영 시점에 알 수 없으므로 진단용으로만 사용한다.
| split | _track6_row_id | artist_key | artist_name_ko | actual_price | pred_price | ape | residual_log | risk_cause | pred_bin | size_bin | basis_n_bucket | basis_iqr_bucket | basis_level_simple | basis_gap_sign | medium_support_bucket_clean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0604_ex50 | 4098 | yeun song | Yeun Song | 552000.0000 | 2858558.4132 | 4.1785 | -1.6445 | basis_current_disagreement | pred04 | size00 | n_5_9 | iqr_low | artist_detail | basis_neg | other__metal |
| 0604_ex50 | 928 | beomsik won | Beomsik Won | 690000.0000 | 3018801.3822 | 3.3751 | -1.4759 | basis_current_disagreement | pred05 | size00 | n_10_19 | iqr_mid | artist_overall | basis_pos | other__paper |
| 0604_ex50 | 4165 | gyul e kim | Gyul E Kim | 3864000.0000 | 16788670.0510 | 3.3449 | -1.4690 | basis_current_disagreement | pred08 | size04 | n_10_19 | iqr_low | artist_detail | basis_neg | oil__canvas |
| 0604_ex50 | 6143 | nam june paik | Nam June Paik | 6900000.0000 | 28129374.7080 | 3.0767 | -1.4053 | basis_high_spread | pred09 | size01 | n_10_19 | iqr_high | artist_detail | basis_pos | other__paper |
| 0604_ex50 | 6144 | nam june paik | Nam June Paik | 6900000.0000 | 28129374.7080 | 3.0767 | -1.4053 | basis_high_spread | pred09 | size01 | n_10_19 | iqr_high | artist_detail | basis_pos | other__paper |
| 0604_ex50 | 5407 | hanna kim | Hanna Kim | 1035000.0000 | 3392177.7265 | 2.2775 | -1.1871 | basis_low_sample | pred05 | size01 | n_lt5 | iqr_low | artist_detail | basis_pos | pencil__paper |
| 0604_ex50 | 5408 | hanna kim | Hanna Kim | 1035000.0000 | 3392177.7265 | 2.2775 | -1.1871 | basis_low_sample | pred05 | size01 | n_lt5 | iqr_low | artist_detail | basis_pos | pencil__paper |
| 0604_ex50 | 5409 | hanna kim | Hanna Kim | 1035000.0000 | 3392177.7265 | 2.2775 | -1.1871 | basis_low_sample | pred05 | size01 | n_lt5 | iqr_low | artist_detail | basis_pos | pencil__paper |
| 0604_ex50 | 3645 | sohyun park | Sohyun Park | 1518000.0000 | 4602169.6455 | 2.0317 | -1.1091 | basis_current_disagreement | pred06 | size04 | n_10_19 | iqr_mid | artist_overall | basis_neg | acrylic__paper |
| 0604_ex50 | 152 | mi young um | Mi Young Um | 372600.0000 | 1119326.5680 | 2.0041 | -1.1000 | basis_high_spread | pred02 | size00 | n_5_9 | iqr_high | artist_overall | basis_pos | mixed__canvas |
| 0604_ex50 | 5118 | jeong yeon kim | Jeong Yeon Kim | 4374600.0000 | 12324799.8284 | 1.8174 | -1.0358 | basis_high_spread | pred08 | size04 | n_5_9 | iqr_high | artist_overall | basis_neg | acrylic__canvas |
| 0604_ex50 | 24 | dahee yang | Dahee Yang | 151800.0000 | 391027.4387 | 1.5759 | -0.9462 | basis_current_disagreement | pred00 | size00 | n_5_9 | iqr_mid | artist_overall | basis_pos | oil__canvas |
| 0604_ex50 | 4698 | a jihye | A Jihye | 3500000.0000 | 8711806.5081 | 1.4891 | -0.9119 | basis_current_disagreement | pred07 | size03 | n_5_9 | iqr_low | artist_overall | basis_neg | acrylic__paper |
| 0604_ex50 | 5403 | nina park | Nina Park | 2070000.0000 | 5050799.8733 | 1.4400 | -0.8920 | no_primary_risk | pred06 | size03 | n_ge20 | iqr_mid | market_medium | basis_flat | acrylic__canvas |
| 0604_ex50 | 2868 | kim hyun jung | Kim Hyun Jung | 2760000.0000 | 6729064.4072 | 1.4381 | -0.8912 | no_primary_risk | pred07 | size03 | n_ge20 | iqr_low | market_medium | basis_neg | oil__canvas |
| 0604_ex50 | 42 | kwon oon | Kwon Oon | 372600.0000 | 848025.4432 | 1.2760 | -0.8224 | basis_low_sample | pred01 | size00 | n_lt5 | iqr_low | artist_detail | basis_neg | other__panel |
| 0604_ex50 | 2869 | do su kim | Do Su Kim | 1449000.0000 | 3199857.8007 | 1.2083 | -0.7922 | basis_current_disagreement | pred05 | size03 | n_5_9 | iqr_low | artist_overall | basis_neg | oil__canvas |
| 0604_ex50 | 2870 | do su kim | Do Su Kim | 1449000.0000 | 3199857.8007 | 1.2083 | -0.7922 | basis_current_disagreement | pred05 | size03 | n_5_9 | iqr_low | artist_overall | basis_neg | oil__canvas |
| 0604_ex50 | 5402 | nina park | Nina Park | 2484000.0000 | 5398298.4628 | 1.1732 | -0.7762 | no_primary_risk | pred06 | size03 | n_ge20 | iqr_mid | market_medium | basis_flat | acrylic__canvas |
| 0604_ex50 | 47 | lim hong | Lim Hong | 745200.0000 | 1603566.1939 | 1.1519 | -0.7663 | basis_current_disagreement | pred03 | size01 | n_5_9 | iqr_low | artist_overall | basis_pos | oil__canvas |
| 0604_ex50 | 48 | lim hong | Lim Hong | 745200.0000 | 1603566.1939 | 1.1519 | -0.7663 | basis_current_disagreement | pred03 | size01 | n_5_9 | iqr_low | artist_overall | basis_pos | oil__canvas |
| 0604_ex50 | 2867 | kim hyun jung | Kim Hyun Jung | 2760000.0000 | 5800589.5634 | 1.1017 | -0.7427 | no_primary_risk | pred06 | size03 | n_ge20 | iqr_low | market_medium | basis_flat | oil__canvas |
| 0604_ex50 | 4532 | hari im | Hari Im | 4800000.0000 | 9776415.8142 | 1.0368 | -0.7114 | basis_low_sample | pred08 | size04 | n_lt5 | iqr_low | artist_overall | basis_neg | acrylic__canvas |
| 0604_ex50 | 4527 | hari im | Hari Im | 1400000.0000 | 2849186.1108 | 1.0351 | -0.7106 | basis_low_sample | pred04 | size02 | n_lt5 | iqr_low | artist_overall | basis_flat | acrylic__canvas |
| 0604_ex50 | 4528 | hari im | Hari Im | 1400000.0000 | 2836476.3097 | 1.0261 | -0.7061 | basis_low_sample | pred04 | size02 | n_lt5 | iqr_low | artist_overall | basis_flat | acrylic__canvas |
| 0604_ex50 | 4529 | hari im | Hari Im | 1400000.0000 | 2836476.3097 | 1.0261 | -0.7061 | basis_low_sample | pred04 | size02 | n_lt5 | iqr_low | artist_overall | basis_flat | acrylic__canvas |
| 0604_ex50 | 5756 | bahk younghoon | Bahk Younghoon | 40000000.0000 | 1000.0000 | 1.0000 | 18.9555 | basis_low_sample | pred00 | size04 | n_lt5 | iqr_low | artist_detail | basis_pos | mixed__panel |
| 0604_ex50 | 5760 | bahk younghoon | Bahk Younghoon | 20700000.0000 | 1000.0000 | 1.0000 | 10.9622 | basis_low_sample | pred00 | size04 | n_lt5 | iqr_low | artist_detail | basis_pos | mixed__panel |
| 0604_ex50 | 5761 | bahk younghoon | Bahk Younghoon | 20700000.0000 | 1000.0000 | 1.0000 | 10.7694 | basis_low_sample | pred00 | size04 | n_lt5 | iqr_low | artist_detail | basis_pos | mixed__panel |
| 0604_ex50 | 5762 | bahk younghoon | Bahk Younghoon | 20700000.0000 | 1000.0000 | 1.0000 | 10.7694 | basis_low_sample | pred00 | size04 | n_lt5 | iqr_low | artist_detail | basis_pos | mixed__panel |

## 9. 산출물

- `outputs/metrics.csv`
- `outputs/candidate_predictions.csv`
- `outputs/feature_coefficients.csv`
- `outputs/residual_analysis.csv`
- `outputs/bootstrap_or_repeated_split_summary.csv`
- `outputs/risk_segment_summary.csv`
- `outputs/next_experiment_candidates.csv`
- `outputs/largest_errors.csv`
- `artifacts/experiment_config.json`