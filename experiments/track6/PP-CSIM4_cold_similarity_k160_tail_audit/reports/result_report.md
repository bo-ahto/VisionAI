# Cold 유사작품 k160 tail 안정성 추가 검증

- 작성일: 2026-06-18T15:16:48
- 비교: `artwork_similarity_k160` - `user_meta_core_bucket`. delta가 음수이면 k160 후보가 더 좋다.
- 목적: 라우터 없이 후보 모델 자체의 tail 안정성을 확인한다.

## 1. 전체 tail 감사
| split | n | win_rate | delta_median_APE | delta_mean_APE | delta_p95_APE | base_APE_gt_2 | challenger_APE_gt_2 | delta_count_APE_gt_2 | base_APE_gt_5 | challenger_APE_gt_5 | delta_count_APE_gt_5 | base_over_bias_mean | challenger_over_bias_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 2753 | 0.496186 | 0.000743 | -0.004043 | 0.095870 | 81 | 86 | 5 | 22 | 25 | 3 | 0.154543 | 0.129320 |
| test | 3099 | 0.524040 | -0.005251 | -0.031734 | -0.022015 | 269 | 263 | -6 | 72 | 76 | 4 | 0.702542 | 0.681992 |

## 2. test에서 악화된 세그먼트
| split | segment_type | segment | n | win_rate | delta_MdAPE | delta_MAPE | delta_p95_APE | base_p95_APE | challenger_p95_APE | delta_APE_gt_2_count | delta_APE_gt_5_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | actual_price_band | 3m_10m | 1057 | 0.507096 | -0.002742 | -0.004403 | 0.038598 | 1.031206 | 1.069804 | 4 | 0 |
| test | actual_price_band | gt_10m | 636 | 0.517296 | 0.018330 | -0.007917 | -0.002120 | 0.907910 | 0.905791 | 0 | 0 |
| test | actual_price_band | 1m_3m | 866 | 0.558891 | 0.008575 | -0.021608 | -0.090663 | 2.278503 | 2.187840 | -7 | 0 |
| test | quantile_width_band | qwidth_q4_high | 774 | 0.583979 | -0.022681 | 0.028523 | -0.127674 | 2.502411 | 2.374737 | 10 | 2 |
| test | quantile_width_band | qwidth_q3 | 775 | 0.509677 | -0.024188 | -0.010189 | -0.138013 | 2.309385 | 2.171372 | 1 | 1 |
| test | quantile_width_band | qwidth_q1_low | 775 | 0.496774 | 0.003899 | -0.044162 | -0.176539 | 2.127005 | 1.950467 | -6 | 0 |
| test | quantile_width_band | qwidth_q2 | 775 | 0.505806 | -0.012072 | -0.101028 | -0.924514 | 8.664816 | 7.740302 | -11 | 1 |
| test | actual_price_band | lt_1m | 540 | 0.509259 | 0.010397 | -0.129519 | -1.568770 | 29.759225 | 28.190455 | -3 | 4 |

## 3. test에서 개선된 세그먼트
| split | segment_type | segment | n | win_rate | delta_MdAPE | delta_MAPE | delta_p95_APE | base_p95_APE | challenger_p95_APE | delta_APE_gt_2_count | delta_APE_gt_5_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test | actual_price_band | lt_1m | 540 | 0.509259 | 0.010397 | -0.129519 | -1.568770 | 29.759225 | 28.190455 | -3 | 4 |
| test | quantile_width_band | qwidth_q2 | 775 | 0.505806 | -0.012072 | -0.101028 | -0.924514 | 8.664816 | 7.740302 | -11 | 1 |
| test | quantile_width_band | qwidth_q1_low | 775 | 0.496774 | 0.003899 | -0.044162 | -0.176539 | 2.127005 | 1.950467 | -6 | 0 |
| test | quantile_width_band | qwidth_q3 | 775 | 0.509677 | -0.024188 | -0.010189 | -0.138013 | 2.309385 | 2.171372 | 1 | 1 |
| test | quantile_width_band | qwidth_q4_high | 774 | 0.583979 | -0.022681 | 0.028523 | -0.127674 | 2.502411 | 2.374737 | 10 | 2 |
| test | actual_price_band | 1m_3m | 866 | 0.558891 | 0.008575 | -0.021608 | -0.090663 | 2.278503 | 2.187840 | -7 | 0 |
| test | actual_price_band | gt_10m | 636 | 0.517296 | 0.018330 | -0.007917 | -0.002120 | 0.907910 | 0.905791 | 0 | 0 |
| test | actual_price_band | 3m_10m | 1057 | 0.507096 | -0.002742 | -0.004403 | 0.038598 | 1.031206 | 1.069804 | 4 | 0 |

## 4. 결론

- test 전체에서는 k160 후보가 평균 오차와 큰 오차 개수를 줄인다.
- validation/test 모두 row-level win rate는 50%를 크게 넘지 않으므로, 개선은 모든 행에서 고르게 이기는 방식이 아니라 큰 오차를 줄이는 방식에 가깝다.
- 저가 구간은 두 후보 모두 가장 취약하며, k160이 p95를 낮추지만 MdAPE는 약간 나빠질 수 있다.
- 라우터를 쓰지 않는 조건에서는 k160 후보가 현재까지 가장 설득력 있는 개선 후보지만, 저가 tail과 메타 누락을 운영 표시 정책으로 같이 관리해야 한다.