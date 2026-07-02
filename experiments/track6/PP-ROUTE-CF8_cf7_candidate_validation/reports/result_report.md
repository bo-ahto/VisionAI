# PP-ROUTE-CF8 CF7 Candidate Validation

## 1. 목적

CF7에서 선택된 Warm-lite tail guard 후보를 full-history, k=1~6 stress, bootstrap, segment tail 관점에서 검증한다.

## 2. 후보

- 기존 Warm-lite: `qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)`
- CF7 후보: `qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)`

## 3. Full-History Test Metrics

| candidate | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MdAPE | rank_MAPE | rank_p95_APE | rank_RMSE_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm WMIN8 operational | 607 | 0.104326 | 0.235814 | 0.739416 | 0.377190 | 3 | 3 | 1 | 1 |
| Warm-lite current s0.50 cap0.10 | 607 | 0.084485 | 0.225214 | 0.803203 | 0.382171 | 1 | 2 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | 607 | 0.089227 | 0.223920 | 0.745513 | 0.379962 | 2 | 1 | 2 | 2 |

## 4. Artist-Cluster Bootstrap

| candidate_a | candidate_b | metric | n_boot | p_a_better | p_b_better | delta_a_minus_b_mean | delta_a_minus_b_q05 | delta_a_minus_b_q50 | delta_a_minus_b_q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm-lite CF7 s1.00 cap0.15 | Warm-lite current s0.50 cap0.10 | MdAPE | 2000 | 0.194500 | 0.805500 | 0.002540 | -0.003759 | 0.002825 | 0.007413 |
| Warm-lite CF7 s1.00 cap0.15 | Warm-lite current s0.50 cap0.10 | MAPE | 2000 | 0.783500 | 0.216500 | -0.001342 | -0.004244 | -0.001231 | 0.001234 |
| Warm-lite CF7 s1.00 cap0.15 | Warm-lite current s0.50 cap0.10 | p95_APE | 2000 | 0.830500 | 0.169500 | -0.018385 | -0.062107 | -0.015892 | 0.030609 |
| Warm-lite CF7 s1.00 cap0.15 | Warm-lite current s0.50 cap0.10 | RMSE_log | 2000 | 0.955000 | 0.045000 | -0.002208 | -0.004194 | -0.002206 | -0.000053 |
| Warm-lite CF7 s1.00 cap0.15 | Warm WMIN8 operational | MdAPE | 2000 | 0.991000 | 0.009000 | -0.017767 | -0.031430 | -0.017305 | -0.005242 |
| Warm-lite CF7 s1.00 cap0.15 | Warm WMIN8 operational | MAPE | 2000 | 0.959500 | 0.040500 | -0.012107 | -0.023887 | -0.012186 | -0.000763 |
| Warm-lite CF7 s1.00 cap0.15 | Warm WMIN8 operational | p95_APE | 2000 | 0.284500 | 0.715500 | 0.031099 | -0.071354 | 0.027716 | 0.121988 |
| Warm-lite CF7 s1.00 cap0.15 | Warm WMIN8 operational | RMSE_log | 2000 | 0.382500 | 0.617500 | 0.002522 | -0.012162 | 0.002615 | 0.016959 |

## 5. k=1~6 Capped-History Stress Metrics

| candidate | condition | n | MdAPE | MAPE | p95_APE | RMSE_log | rank_MAPE | rank_p95_APE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warm retrained clean stack | k=1 seed-mean | 519 | 0.228377 | 0.349077 | 0.940275 | 0.470595 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=1 seed-mean | 519 | 0.173219 | 0.311373 | 0.880311 | 0.448299 | 2 | 1 |
| Warm-lite current s0.50 cap0.10 | k=1 seed-mean | 519 | 0.172755 | 0.311118 | 0.890055 | 0.446076 | 1 | 2 |
| Warm retrained clean stack | k=2 seed-mean | 519 | 0.201354 | 0.293245 | 0.936806 | 0.431259 | 1 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=2 seed-mean | 519 | 0.157679 | 0.303237 | 0.863655 | 0.424533 | 2 | 1 |
| Warm-lite current s0.50 cap0.10 | k=2 seed-mean | 519 | 0.161448 | 0.304920 | 0.889889 | 0.423878 | 3 | 2 |
| Warm retrained clean stack | k=3 seed-mean | 519 | 0.170056 | 0.291045 | 0.887342 | 0.446368 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=3 seed-mean | 519 | 0.143756 | 0.257369 | 0.876824 | 0.430291 | 2 | 1 |
| Warm-lite current s0.50 cap0.10 | k=3 seed-mean | 519 | 0.142914 | 0.257082 | 0.877410 | 0.430237 | 1 | 2 |
| Warm retrained clean stack | k=4 seed-mean | 519 | 0.164994 | 0.271088 | 0.854571 | 0.426418 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=4 seed-mean | 519 | 0.112094 | 0.252893 | 0.781680 | 0.395508 | 1 | 1 |
| Warm-lite current s0.50 cap0.10 | k=4 seed-mean | 519 | 0.111142 | 0.255190 | 0.841395 | 0.397345 | 2 | 2 |
| Warm retrained clean stack | k=5 seed-mean | 519 | 0.156848 | 0.257445 | 0.800696 | 0.410500 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=5 seed-mean | 519 | 0.118969 | 0.230655 | 0.661499 | 0.368704 | 1 | 1 |
| Warm-lite current s0.50 cap0.10 | k=5 seed-mean | 519 | 0.119911 | 0.230864 | 0.676274 | 0.369027 | 2 | 2 |
| Warm retrained clean stack | k=6 seed-mean | 519 | 0.139844 | 0.261411 | 0.856599 | 0.425187 | 3 | 3 |
| Warm-lite CF7 s1.00 cap0.15 | k=6 seed-mean | 519 | 0.114188 | 0.225065 | 0.756899 | 0.369826 | 1 | 1 |
| Warm-lite current s0.50 cap0.10 | k=6 seed-mean | 519 | 0.114118 | 0.226295 | 0.764952 | 0.370710 | 2 | 2 |

## 6. k=1~6 Paired Shares

| k | n | cf7_better_than_current_share | current_better_than_cf7_share | cf7_better_than_warm_share | warm_better_than_cf7_share | mean_ape_delta_current_minus_cf7 | mean_ape_delta_warm_minus_cf7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 519 | 0.487476 | 0.512524 | 0.578035 | 0.421965 | -0.000254 | 0.037704 |
| 2 | 519 | 0.470135 | 0.529865 | 0.589595 | 0.410405 | 0.001683 | -0.009992 |
| 3 | 519 | 0.468208 | 0.531792 | 0.552987 | 0.447013 | -0.000287 | 0.033676 |
| 4 | 519 | 0.497110 | 0.502890 | 0.616570 | 0.383430 | 0.002297 | 0.018195 |
| 5 | 519 | 0.479769 | 0.520231 | 0.597303 | 0.402697 | 0.000209 | 0.026790 |
| 6 | 519 | 0.487476 | 0.512524 | 0.641618 | 0.358382 | 0.001230 | 0.036346 |

## 7. Segment Metrics

| segment_axis | segment | current_n | current_MAPE | current_p95_APE | cf7_MAPE | cf7_p95_APE | warm_MAPE | warm_p95_APE | cf7_minus_current_MAPE | cf7_minus_current_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| history_bin | 11-20 | 156 | 0.323840 | 1.039864 | 0.321580 | 1.164978 | 0.317787 | 0.943440 | -0.002261 | 0.125114 |
| history_bin | 21-50 | 123 | 0.197136 | 0.749615 | 0.193675 | 0.729303 | 0.211755 | 0.908862 | -0.003461 | -0.020312 |
| history_bin | 5 | 88 | 0.231540 | 0.939474 | 0.230926 | 0.937179 | 0.252917 | 0.895909 | -0.000614 | -0.002295 |
| history_bin | 51+ | 69 | 0.131318 | 0.460771 | 0.130974 | 0.459444 | 0.125078 | 0.415977 | -0.000344 | -0.001327 |
| history_bin | 6-10 | 171 | 0.190067 | 0.745871 | 0.190480 | 0.709380 | 0.214218 | 0.689173 | 0.000413 | -0.036491 |
| price_bin | price_q1_low | 152 | 0.239152 | 0.864145 | 0.235447 | 0.849178 | 0.244000 | 0.875177 | -0.003705 | -0.014967 |
| price_bin | price_q2 | 152 | 0.182478 | 0.584143 | 0.183072 | 0.575980 | 0.194949 | 0.579833 | 0.000593 | -0.008163 |
| price_bin | price_q3 | 151 | 0.325339 | 1.190485 | 0.321730 | 1.182470 | 0.345796 | 1.363850 | -0.003609 | -0.008014 |
| price_bin | price_q4_high | 152 | 0.154545 | 0.564378 | 0.156074 | 0.562127 | 0.159234 | 0.668717 | 0.001529 | -0.002250 |
| qwidth_bin | width_q1_low | 152 | 0.049298 | 0.160894 | 0.051093 | 0.163033 | 0.071206 | 0.214121 | 0.001795 | 0.002138 |
| qwidth_bin | width_q2 | 152 | 0.119175 | 0.399292 | 0.119785 | 0.413276 | 0.125032 | 0.456527 | 0.000610 | 0.013984 |
| qwidth_bin | width_q3 | 151 | 0.251776 | 0.812927 | 0.247998 | 0.792776 | 0.258859 | 0.769429 | -0.003779 | -0.020152 |
| qwidth_bin | width_q4_high | 152 | 0.480781 | 1.356029 | 0.476961 | 1.278974 | 0.488311 | 1.386852 | -0.003820 | -0.077055 |
| correction_direction | down | 378 | 0.240701 | 0.822876 | 0.235636 | 0.753294 | 0.252997 | 0.819798 | -0.005065 | -0.069583 |
| correction_direction | up | 229 | 0.199650 | 0.744153 | 0.204580 | 0.745171 | 0.207451 | 0.692840 | 0.004930 | 0.001018 |

## 8. Top CF7 Tail Rows

| _track6_row_id | artist_key | actual_price | full_train_artist_history_n | warm_lite_cf7_ape | warm_lite_current_ape | warm_wmin8_ape | quantile_uncertainty_width_log | cf7_correction_log | history_bin | price_bin | qwidth_bin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 17485 | gunsun kim | 5865000 | 11 | 8.757156 | 8.998999 | 9.441273 | 0.807532 | -0.048968 | 11-20 | price_q3 | width_q4_high |
| 17486 | gunsun kim | 6527400 | 11 | 6.303267 | 6.806922 | 7.950497 | 0.877156 | -0.133378 | 11-20 | price_q3 | width_q4_high |
| 15419 | taedong lee | 234600 | 18 | 3.230978 | 3.285942 | 1.494089 | 1.046989 | -0.025814 | 11-20 | price_q1_low | width_q4_high |
| 14260 | digital d | 6582600 | 6 | 2.563491 | 2.286347 | 2.392971 | 1.151378 | 0.150000 | 6-10 | price_q3 | width_q4_high |
| 24336 | beomsik won | 7000000 | 13 | 2.493111 | 2.513695 | 2.339919 | 0.510219 | -0.011751 | 11-20 | price_q3 | width_q3 |
| 24417 | beomsik won | 7000000 | 13 | 2.493111 | 2.513695 | 2.339919 | 0.510219 | -0.011751 | 11-20 | price_q3 | width_q3 |
| 21794 | yeun song | 552000 | 5 | 2.217740 | 2.266851 | 2.388876 | 1.279187 | -0.030295 | 5 | price_q1_low | width_q4_high |
| 17271 | chang beom son | 1159200 | 15 | 1.782661 | 1.749193 | 1.822683 | 0.872241 | 0.024200 | 11-20 | price_q1_low | width_q4_high |
| 42707 | a jihye | 3500000 | 5 | 1.681038 | 1.553724 | 1.351806 | 1.043696 | 0.097303 | 5 | price_q3 | width_q4_high |
| 15553 | marina ogai | 2180400 | 49 | 1.420659 | 1.443738 | 0.929956 | 0.555662 | -0.018978 | 21-50 | price_q2 | width_q3 |
| 22225 | do ha ham | 3174000 | 10 | 1.401112 | 1.342575 | 1.375893 | 0.443867 | 0.049362 | 6-10 | price_q3 | width_q2 |
| 22201 | jae yun lee | 6900000 | 5 | 1.320407 | 1.475769 | 1.592303 | 0.677358 | -0.129617 | 5 | price_q3 | width_q3 |
| 5939 | seon yoo | 2133480 | 31 | 1.281074 | 1.335109 | 1.381722 | 0.926395 | -0.046825 | 21-50 | price_q2 | width_q4_high |
| 28919 | shine l si in yang | 552000 | 13 | 1.277256 | 1.178071 | 1.446576 | 1.742060 | 0.089064 | 11-20 | price_q1_low | width_q4_high |
| 11782 | ej koh | 262200 | 12 | 1.261326 | 1.250420 | 1.393121 | 0.980009 | 0.009669 | 11-20 | price_q1_low | width_q4_high |
| 8326 | bomin kim | 1076400 | 7 | 1.227945 | 1.381598 | 1.171551 | 1.289847 | -0.133384 | 6-10 | price_q1_low | width_q4_high |
| 3550 | seon yoo | 1945800 | 31 | 1.138555 | 1.144899 | 1.350902 | 1.107116 | -0.005924 | 21-50 | price_q2 | width_q4_high |
| 2969 | injung kwon | 1476600 | 17 | 1.132862 | 0.993795 | 0.606009 | 0.939804 | 0.134850 | 11-20 | price_q2 | width_q4_high |
| 21901 | song yu jeong | 4140000 | 7 | 1.044534 | 1.022438 | 1.030862 | 1.552264 | 0.021732 | 6-10 | price_q3 | width_q4_high |
| 1327 | soo hee kim | 2797260 | 8 | 1.033210 | 1.045253 | 0.862589 | 0.430721 | -0.011812 | 6-10 | price_q2 | width_q2 |

## 9. Config

```json
{
  "created_at": "2026-06-16T15:30:08",
  "experiment_id": "PP-ROUTE-CF8",
  "experiment_slug": "PP-ROUTE-CF8_cf7_candidate_validation",
  "source_experiments": [
    "experiments/track6/PP-ROUTE-CF5_unified_warm_lite_operational_comparison",
    "experiments/track6/PP-ROUTE-CF7_warm_lite_tail_guard"
  ],
  "candidate_formula": "qavg + clip(1.00 * LightGBM Huber residual, -0.15, +0.15)",
  "baseline_formula": "qavg + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)",
  "n_boot": 2000,
  "bootstrap_unit": "artist_key cluster bootstrap",
  "seconds": 1.17
}
```
