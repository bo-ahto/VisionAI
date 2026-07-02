# PP-WLITE-Q3 Warm-lite Quantile 잔차 보정 검증

## 1. 목적

Warm-lite Quantile 후보 위에 CatBoost/LightGBM 잔차 보정층을 붙였을 때 Q1/Q2보다 추가 개선되는지 확인한다.

## 2. 누수 방지 설계

- 잔차 target은 in-sample q50이 아니라 5-fold OOF q50 full/lean 평균으로 계산
- residual = 실제 로그가격 - OOF(q50 full/lean 평균)
- 평가행에는 final Quantile 모델 예측값과 residual 모델 예측값을 사용
- residual 보정값은 `clip(strength * residual_pred, -cap, +cap)`로 제한

## 3. Q1-like 실존 저이력 leave-one-out overall

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qavg_lgbres_s05_cap010 | 1947 | 0.107246 | 0.275773 | 0.852026 | 5 | 1 | 1 | -0.001981 | -0.010793 | -0.024444 |
| qavg_lgbres_s05_cap005 | 1947 | 0.107155 | 0.277368 | 0.856712 | 4 | 2 | 2 | -0.002072 | -0.009198 | -0.019758 |
| qavg_lgbres_s10_cap005 | 1947 | 0.108546 | 0.278008 | 0.859193 | 7 | 3 | 3 | -0.000681 | -0.008558 | -0.017277 |
| qavg_cbres_s05_cap010 | 1947 | 0.105628 | 0.278785 | 0.873310 | 2 | 4 | 8 | -0.003599 | -0.007781 | -0.003160 |
| qavg_cbres_s05_cap005 | 1947 | 0.106452 | 0.279205 | 0.873310 | 3 | 5 | 8 | -0.002775 | -0.007361 | -0.003160 |
| qavg_cbres_s10_cap005 | 1947 | 0.110500 | 0.279439 | 0.870172 | 9 | 6 | 7 | 0.001273 | -0.007127 | -0.006298 |
| lgbq_full_q50 | 1947 | 0.105429 | 0.280085 | 0.868004 | 1 | 7 | 6 | -0.003798 | -0.006481 | -0.008466 |
| lgbq_full_lean_avg | 1947 | 0.107322 | 0.280449 | 0.859623 | 6 | 8 | 4 | -0.001905 | -0.006117 | -0.016847 |
| lgbq_lean_q50 | 1947 | 0.112892 | 0.285207 | 0.863341 | 10 | 9 | 5 | 0.003665 | -0.001359 | -0.013129 |
| all6_current | 1947 | 0.109227 | 0.286566 | 0.876470 | 8 | 10 | 10 | 0.000000 | 0.000000 | 0.000000 |

## 4. Q1-like by history_k

| history_k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | qavg_lgbres_s05_cap010 | 621 | 0.110652 | 0.306967 | 0.875776 | 1 | 1 | 3 |
| 1 | qavg_lgbres_s05_cap005 | 621 | 0.112660 | 0.310064 | 0.877291 | 3 | 3 | 4 |
| 1 | qavg_cbres_s05_cap005 | 621 | 0.117762 | 0.313423 | 0.893714 | 5 | 5 | 6 |
| 1 | lgbq_full_lean_avg | 621 | 0.120141 | 0.314691 | 0.878501 | 7 | 7 | 5 |
| 1 | all6_current | 621 | 0.120677 | 0.341476 | 0.955881 | 8 | 10 | 10 |
| 2 | all6_current | 489 | 0.118375 | 0.270704 | 0.877912 | 1 | 1 | 10 |
| 2 | qavg_cbres_s05_cap005 | 489 | 0.130957 | 0.278730 | 0.835822 | 5 | 4 | 4 |
| 2 | lgbq_full_lean_avg | 489 | 0.127925 | 0.280024 | 0.817186 | 2 | 6 | 1 |
| 2 | qavg_lgbres_s05_cap005 | 489 | 0.128853 | 0.280140 | 0.836556 | 3 | 7 | 6 |
| 2 | qavg_lgbres_s05_cap010 | 489 | 0.130034 | 0.281075 | 0.826593 | 4 | 8 | 2 |
| 3 | all6_current | 324 | 0.105981 | 0.254102 | 0.714172 | 10 | 1 | 1 |
| 3 | qavg_lgbres_s05_cap010 | 324 | 0.090080 | 0.254148 | 0.927107 | 3 | 2 | 10 |
| 3 | qavg_lgbres_s05_cap005 | 324 | 0.092035 | 0.255417 | 0.889540 | 8 | 5 | 3 |
| 3 | qavg_cbres_s05_cap005 | 324 | 0.090792 | 0.256824 | 0.923539 | 4 | 8 | 6 |
| 3 | lgbq_full_lean_avg | 324 | 0.090867 | 0.259343 | 0.889918 | 6 | 9 | 4 |
| 4 | qavg_lgbres_s05_cap010 | 513 | 0.091271 | 0.246615 | 0.799123 | 8 | 1 | 2 |
| 4 | qavg_lgbres_s05_cap005 | 513 | 0.087747 | 0.249010 | 0.812903 | 5 | 2 | 4 |
| 4 | qavg_cbres_s05_cap005 | 513 | 0.083872 | 0.252371 | 0.835311 | 2 | 4 | 8 |
| 4 | lgbq_full_lean_avg | 513 | 0.084852 | 0.252732 | 0.840919 | 4 | 6 | 10 |
| 4 | all6_current | 513 | 0.092263 | 0.255719 | 0.788372 | 9 | 10 | 1 |

## 5. Q1-like bootstrap vs all6_current

| candidate | n_boot | p_candidate_better_all6_MdAPE | p_candidate_better_all6_MAPE | p_candidate_better_all6_p95_APE | p_all6_better_candidate_MdAPE | p_all6_better_candidate_MAPE | p_all6_better_candidate_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lgbq_full_q50 | 400 | 0.742500 | 0.735000 | 0.592500 | 0.257500 | 0.265000 | 0.407500 |
| lgbq_lean_q50 | 400 | 0.315000 | 0.627500 | 0.575000 | 0.685000 | 0.372500 | 0.425000 |
| lgbq_full_lean_avg | 400 | 0.717500 | 0.752500 | 0.660000 | 0.282500 | 0.247500 | 0.340000 |
| qavg_cbres_s05_cap005 | 400 | 0.722500 | 0.745000 | 0.502500 | 0.277500 | 0.255000 | 0.497500 |
| qavg_cbres_s05_cap010 | 400 | 0.742500 | 0.750000 | 0.510000 | 0.257500 | 0.250000 | 0.490000 |
| qavg_cbres_s10_cap005 | 400 | 0.492500 | 0.752500 | 0.517500 | 0.507500 | 0.247500 | 0.482500 |
| qavg_lgbres_s05_cap005 | 400 | 0.737500 | 0.810000 | 0.692500 | 0.262500 | 0.190000 | 0.307500 |
| qavg_lgbres_s05_cap010 | 400 | 0.700000 | 0.825000 | 0.792500 | 0.300000 | 0.175000 | 0.207500 |
| qavg_lgbres_s10_cap005 | 400 | 0.587500 | 0.770000 | 0.705000 | 0.412500 | 0.230000 | 0.295000 |

## 6. Q2-like k-truncation overall

| candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_all6 | delta_MAPE_minus_all6 | delta_p95_APE_minus_all6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qavg_lgbres_s05_cap010 | 7284 | 0.154475 | 0.303435 | 1.000528 | 1 | 1 | 1 | -0.015644 | -0.040983 | -0.160295 |
| qavg_lgbres_s05_cap005 | 7284 | 0.155200 | 0.304895 | 1.010105 | 2 | 2 | 2 | -0.014919 | -0.039523 | -0.150718 |
| qavg_lgbres_s10_cap005 | 7284 | 0.156313 | 0.305089 | 1.010724 | 3 | 3 | 3 | -0.013806 | -0.039329 | -0.150099 |
| lgbq_full_lean_avg | 7284 | 0.158527 | 0.308800 | 1.045745 | 5 | 4 | 7 | -0.011592 | -0.035618 | -0.115078 |
| qavg_cbres_s05_cap005 | 7284 | 0.158983 | 0.309038 | 1.043453 | 6 | 5 | 6 | -0.011136 | -0.035380 | -0.117370 |
| qavg_cbres_s05_cap010 | 7284 | 0.158520 | 0.309216 | 1.032895 | 4 | 6 | 4 | -0.011599 | -0.035202 | -0.127928 |
| qavg_cbres_s10_cap005 | 7284 | 0.160072 | 0.309606 | 1.036836 | 9 | 7 | 5 | -0.010047 | -0.034812 | -0.123987 |
| lgbq_lean_q50 | 7284 | 0.159569 | 0.310490 | 1.053802 | 8 | 8 | 8 | -0.010550 | -0.033928 | -0.107021 |
| lgbq_full_q50 | 7284 | 0.159341 | 0.311049 | 1.058687 | 7 | 9 | 9 | -0.010778 | -0.033369 | -0.102136 |
| all6_current | 7284 | 0.170119 | 0.344418 | 1.160823 | 10 | 10 | 10 | 0.000000 | 0.000000 | 0.000000 |

## 7. Q2-like by k

| k | candidate | n | MdAPE | MAPE | p95_APE | rank_MdAPE | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | qavg_lgbres_s05_cap010 | 1821 | 0.200164 | 0.346971 | 1.131486 | 5 | 1 | 1 |
| 1 | qavg_lgbres_s05_cap005 | 1821 | 0.197875 | 0.349512 | 1.135835 | 3 | 2 | 2 |
| 1 | lgbq_full_lean_avg | 1821 | 0.199530 | 0.353894 | 1.175702 | 4 | 4 | 7 |
| 1 | qavg_cbres_s05_cap005 | 1821 | 0.200257 | 0.354554 | 1.136850 | 6 | 5 | 3 |
| 1 | all6_current | 1821 | 0.216741 | 0.394669 | 1.371119 | 10 | 10 | 10 |
| 2 | qavg_lgbres_s05_cap010 | 1821 | 0.163295 | 0.319186 | 0.993204 | 2 | 1 | 1 |
| 2 | qavg_lgbres_s05_cap005 | 1821 | 0.163367 | 0.320903 | 1.000415 | 3 | 2 | 2 |
| 2 | qavg_cbres_s05_cap005 | 1821 | 0.167078 | 0.325030 | 1.045304 | 6 | 5 | 6 |
| 2 | lgbq_full_lean_avg | 1821 | 0.165574 | 0.325264 | 1.071724 | 5 | 6 | 8 |
| 2 | all6_current | 1821 | 0.178439 | 0.366070 | 1.255724 | 10 | 10 | 10 |
| 3 | qavg_lgbres_s05_cap010 | 1821 | 0.136932 | 0.286524 | 0.940715 | 3 | 1 | 2 |
| 3 | qavg_lgbres_s05_cap005 | 1821 | 0.137728 | 0.287440 | 0.940715 | 7 | 2 | 2 |
| 3 | qavg_cbres_s05_cap005 | 1821 | 0.137338 | 0.290973 | 0.970001 | 4 | 4 | 6 |
| 3 | lgbq_full_lean_avg | 1821 | 0.134649 | 0.291500 | 0.976585 | 1 | 6 | 9 |
| 3 | all6_current | 1821 | 0.147936 | 0.321928 | 1.014404 | 10 | 10 | 10 |
| 4 | qavg_lgbres_s05_cap010 | 1821 | 0.131539 | 0.261058 | 0.944798 | 7 | 1 | 3 |
| 4 | qavg_lgbres_s05_cap005 | 1821 | 0.131905 | 0.261723 | 0.944798 | 9 | 2 | 3 |
| 4 | lgbq_full_lean_avg | 1821 | 0.130385 | 0.264541 | 0.954606 | 2 | 4 | 5 |
| 4 | qavg_cbres_s05_cap005 | 1821 | 0.131523 | 0.265595 | 0.958929 | 6 | 6 | 6 |
| 4 | all6_current | 1821 | 0.144331 | 0.295006 | 1.018258 | 10 | 10 | 10 |

## 8. Q2-like bootstrap summary vs all6_current

| candidate | conditions | mean_p_candidate_better_all6_MdAPE | mean_p_candidate_better_all6_MAPE | mean_p_candidate_better_all6_p95_APE | conditions_p_candidate_better_all6_MdAPE_ge_0_90 | conditions_p_candidate_better_all6_MAPE_ge_0_90 | conditions_p_candidate_better_all6_p95_APE_ge_0_90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lgbq_full_lean_avg | 12 | 0.859167 | 0.998750 | 0.840000 | 6 | 12 | 5 |
| qavg_cbres_s05_cap005 | 12 | 0.845833 | 0.995000 | 0.840208 | 7 | 12 | 5 |
| qavg_lgbres_s05_cap005 | 12 | 0.866042 | 1.000000 | 0.866667 | 9 | 12 | 8 |
| qavg_lgbres_s05_cap010 | 12 | 0.860000 | 0.999583 | 0.886667 | 6 | 12 | 9 |

## 9. Config

{
  "experiment_id": "PP-WLITE-Q3",
  "experiment_slug": "PP-WLITE-Q3_quantile_residual_correction_validation",
  "model_seed": 20260612,
  "q1_design": "PP-WCUT5-equivalent real low-history leave-one-out, seeds [20260612, 20260613, 20260614]",
  "q2_design": "PP-WCUT6-equivalent frozen Warm-lite k-truncation follow-up",
  "residual_target": "actual_log - OOF(lgbq_full_lean_avg)",
  "residual_models": [
    "CatBoostRegressor",
    "LightGBMRegressor objective=huber"
  ],
  "residual_candidate_rule": "qavg + clip(strength * residual_pred, -cap, +cap)",
  "candidates": [
    "all6_current",
    "lgbq_full_q50",
    "lgbq_lean_q50",
    "lgbq_full_lean_avg",
    "qavg_cbres_s05_cap005",
    "qavg_cbres_s05_cap010",
    "qavg_cbres_s10_cap005",
    "qavg_lgbres_s05_cap005",
    "qavg_lgbres_s05_cap010",
    "qavg_lgbres_s10_cap005"
  ],
  "q1_best_by_metric": {
    "MdAPE": "lgbq_full_q50",
    "MAPE": "qavg_lgbres_s05_cap010",
    "p95_APE": "qavg_lgbres_s05_cap010"
  },
  "q2_best_by_metric": {
    "MdAPE": "qavg_lgbres_s05_cap010",
    "MAPE": "qavg_lgbres_s05_cap010",
    "p95_APE": "qavg_lgbres_s05_cap010"
  },
  "n_boot": 400,
  "prohibitions": [
    "0604 사용 금지"
  ]
}
