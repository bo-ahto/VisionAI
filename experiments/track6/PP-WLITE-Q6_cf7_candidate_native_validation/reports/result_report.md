# PP-WLITE-Q6 CF7 Candidate Native Validation

## 1. 목적

CF7 후보를 기존 Warm-lite native 검증 설계에서 정확히 재평가한다.

## 2. 후보

- current: `qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)`
- CF7: `qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)`

## 3. Q1-like 실존 저이력 LOO Overall

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_current | delta_MAPE_minus_current | delta_p95_APE_minus_current | delta_RMSE_log_minus_current |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qavg_lgbres_s10_cap015_cf7 | 1947 | 0.112221 | 0.275745 | 0.851658 | 0.419824 | 4 | 1 | 1 | 0.004975 | -0.000028 | -0.000367 | -0.003180 |
| qavg_lgbres_s05_cap010_current | 1947 | 0.107246 | 0.275773 | 0.852026 | 0.423003 | 1 | 2 | 2 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| lgbq_full_lean_avg | 1947 | 0.107322 | 0.280449 | 0.859623 | 0.430400 | 2 | 3 | 3 | 0.000076 | 0.004676 | 0.007597 | 0.007396 |
| all6_current | 1947 | 0.109227 | 0.286566 | 0.876470 | 0.447586 | 3 | 4 | 4 | 0.001982 | 0.010793 | 0.024444 | 0.024583 |

## 4. Q1-like by history_k

| history_k | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | qavg_lgbres_s10_cap015_cf7 | 621 | 0.117432 | 0.305494 | 0.901498 | 0.484035 | 1 | 3 |
| 1 | qavg_lgbres_s05_cap010_current | 621 | 0.110652 | 0.306967 | 0.875776 | 0.486932 | 2 | 1 |
| 1 | lgbq_full_lean_avg | 621 | 0.120141 | 0.314691 | 0.878501 | 0.493957 | 3 | 2 |
| 1 | all6_current | 621 | 0.120677 | 0.341476 | 0.955881 | 0.515593 | 4 | 4 |
| 2 | all6_current | 489 | 0.118375 | 0.270704 | 0.877912 | 0.462866 | 1 | 4 |
| 2 | lgbq_full_lean_avg | 489 | 0.127925 | 0.280024 | 0.817186 | 0.410721 | 2 | 1 |
| 2 | qavg_lgbres_s05_cap010_current | 489 | 0.130034 | 0.281075 | 0.826593 | 0.404813 | 3 | 2 |
| 2 | qavg_lgbres_s10_cap015_cf7 | 489 | 0.133602 | 0.285430 | 0.827672 | 0.403589 | 4 | 3 |
| 3 | qavg_lgbres_s10_cap015_cf7 | 324 | 0.095293 | 0.253545 | 1.027374 | 0.381438 | 1 | 4 |
| 3 | all6_current | 324 | 0.105981 | 0.254102 | 0.714172 | 0.363630 | 2 | 1 |
| 3 | qavg_lgbres_s05_cap010_current | 324 | 0.090080 | 0.254148 | 0.927107 | 0.384014 | 3 | 3 |
| 3 | lgbq_full_lean_avg | 324 | 0.090867 | 0.259343 | 0.889918 | 0.389366 | 4 | 2 |
| 4 | qavg_lgbres_s10_cap015_cf7 | 513 | 0.096896 | 0.244522 | 0.764797 | 0.371705 | 1 | 1 |
| 4 | qavg_lgbres_s05_cap010_current | 513 | 0.091271 | 0.246615 | 0.799123 | 0.377811 | 2 | 3 |
| 4 | lgbq_full_lean_avg | 513 | 0.084852 | 0.252732 | 0.840919 | 0.388779 | 3 | 4 |
| 4 | all6_current | 513 | 0.092263 | 0.255719 | 0.788372 | 0.388324 | 4 | 2 |

## 5. Q1 Bootstrap vs Current

| candidate | baseline | n_boot | p_candidate_better_current_MdAPE | p_candidate_better_current_MAPE | p_candidate_better_current_p95_APE | p_candidate_better_current_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- |
| qavg_lgbres_s10_cap015_cf7 | qavg_lgbres_s05_cap010_current | 400 | 0.032500 | 0.495000 | 0.490000 | 1 |

## 6. Q2-like k=1~4 Truncation Overall

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MdAPE | rank_MAPE | rank_p95_APE | delta_MdAPE_minus_current | delta_MAPE_minus_current | delta_p95_APE_minus_current | delta_RMSE_log_minus_current |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qavg_lgbres_s10_cap015_cf7 | 7284 | 0.159414 | 0.301687 | 0.988525 | 0.480387 | 3 | 1 | 1 | 0.004940 | -0.001748 | -0.012003 | -0.001697 |
| qavg_lgbres_s05_cap010_current | 7284 | 0.154475 | 0.303435 | 1.000528 | 0.482084 | 1 | 2 | 2 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| lgbq_full_lean_avg | 7284 | 0.158527 | 0.308800 | 1.045745 | 0.487082 | 2 | 3 | 3 | 0.004052 | 0.005365 | 0.045217 | 0.004998 |
| all6_current | 7284 | 0.170119 | 0.344418 | 1.160823 | 0.502469 | 4 | 4 | 4 | 0.015644 | 0.040983 | 0.160295 | 0.020385 |

## 7. Q2-like by k

| k | candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | qavg_lgbres_s10_cap015_cf7 | 1821 | 0.206243 | 0.345439 | 1.116865 | 0.571496 | 1 | 1 |
| 1 | qavg_lgbres_s05_cap010_current | 1821 | 0.200164 | 0.346971 | 1.131486 | 0.572619 | 2 | 2 |
| 1 | lgbq_full_lean_avg | 1821 | 0.199530 | 0.353894 | 1.175702 | 0.577923 | 3 | 3 |
| 1 | all6_current | 1821 | 0.216741 | 0.394669 | 1.371119 | 0.591065 | 4 | 4 |
| 2 | qavg_lgbres_s10_cap015_cf7 | 1821 | 0.168044 | 0.316902 | 0.971117 | 0.475249 | 1 | 1 |
| 2 | qavg_lgbres_s05_cap010_current | 1821 | 0.163295 | 0.319186 | 0.993204 | 0.476321 | 2 | 2 |
| 2 | lgbq_full_lean_avg | 1821 | 0.165574 | 0.325264 | 1.071724 | 0.480754 | 3 | 3 |
| 2 | all6_current | 1821 | 0.178439 | 0.366070 | 1.255724 | 0.503131 | 4 | 4 |
| 3 | qavg_lgbres_s10_cap015_cf7 | 1821 | 0.141778 | 0.284545 | 0.933806 | 0.445214 | 1 | 1 |
| 3 | qavg_lgbres_s05_cap010_current | 1821 | 0.136932 | 0.286524 | 0.940715 | 0.448538 | 2 | 2 |
| 3 | lgbq_full_lean_avg | 1821 | 0.134649 | 0.291500 | 0.976585 | 0.455174 | 3 | 3 |
| 3 | all6_current | 1821 | 0.147936 | 0.321928 | 1.014404 | 0.463081 | 4 | 4 |
| 4 | qavg_lgbres_s10_cap015_cf7 | 1821 | 0.132164 | 0.259861 | 0.958227 | 0.415214 | 1 | 3 |
| 4 | qavg_lgbres_s05_cap010_current | 1821 | 0.131539 | 0.261058 | 0.944798 | 0.416724 | 2 | 1 |
| 4 | lgbq_full_lean_avg | 1821 | 0.130385 | 0.264541 | 0.954606 | 0.420347 | 3 | 2 |
| 4 | all6_current | 1821 | 0.144331 | 0.295006 | 1.018258 | 0.439268 | 4 | 4 |

## 8. Q2 Bootstrap by seed/k vs Current

| trunc_seed | k | candidate | n_boot | p_candidate_better_current_MdAPE | p_candidate_better_current_MAPE | p_candidate_better_current_p95_APE | p_candidate_better_current_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20260612 | 1 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.122500 | 0.827500 | 0.695000 | 0.870000 |
| 20260612 | 2 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.270000 | 0.865000 | 0.900000 | 0.570000 |
| 20260612 | 3 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.085000 | 0.645000 | 0.575000 | 0.865000 |
| 20260612 | 4 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.567500 | 0.742500 | 0.517500 | 0.925000 |
| 20260613 | 1 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.485000 | 0.750000 | 0.852500 | 0.907500 |
| 20260613 | 2 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.362500 | 0.980000 | 0.720000 | 0.730000 |
| 20260613 | 3 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.042500 | 0.845000 | 0.520000 | 0.992500 |
| 20260613 | 4 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.207500 | 0.545000 | 0.692500 | 0.692500 |
| 20260614 | 1 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.200000 | 0.630000 | 0.592500 | 0.187500 |
| 20260614 | 2 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.065000 | 0.590000 | 0.700000 | 0.842500 |
| 20260614 | 3 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.295000 | 0.925000 | 0.830000 | 0.995000 |
| 20260614 | 4 | qavg_lgbres_s10_cap015_cf7 | 400 | 0.380000 | 0.902500 | 0.590000 | 0.840000 |

## 9. Config

```json
{
  "created_at": "2026-06-16T15:41:01",
  "experiment_id": "PP-WLITE-Q6",
  "experiment_slug": "PP-WLITE-Q6_cf7_candidate_native_validation",
  "q1_design": "PP-WCUT5-equivalent real low-history leave-one-out, seeds [20260612, 20260613, 20260614]",
  "q2_design": "PP-WCUT6-equivalent Warm fixed-test k-truncation, seeds [20260612, 20260613, 20260614], k [1, 2, 3, 4]",
  "current_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
  "cf7_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
  "n_boot": 400,
  "seconds": 511.38
}
```
