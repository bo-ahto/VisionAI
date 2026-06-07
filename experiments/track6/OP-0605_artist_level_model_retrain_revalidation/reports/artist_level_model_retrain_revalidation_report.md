# Artist-Level 모델 재학습 포함 재검증 결과

## 1. 목적

- 기존 보정/라우팅 정책이 고정 split에서만 좋아진 것인지 확인
- seed마다 작가 단위로 새 cold holdout을 만들고 모델을 다시 학습
- Warm은 같은 작가가 train에 남아 있는 행 단위 holdout으로 재학습 검증
- Cold는 작가를 통째로 train에서 제외한 calibration/test로 재학습 검증

## 2. 검증 설정

```json
{
  "seeds": [
    20260605,
    20260606,
    20260607,
    20260608,
    20260609
  ],
  "master_rows": 33892,
  "warm_features": [
    "width_cm",
    "height_cm",
    "depth_cm",
    "area_cm2",
    "log_area",
    "aspect_ratio",
    "has_depth",
    "is_3d_candidate",
    "medium_category",
    "support_category",
    "medium_support_bucket",
    "is_extreme_aspect_ratio",
    "artist_key"
  ],
  "cold_feature_count": 87,
  "cold_feature_note": "LightGBM base + artist meta + search cache + exhibition/gallery cache",
  "split_policy": {
    "cold_calibration_artist_bucket": "0-699 / 10000",
    "cold_test_artist_bucket": "700-1399 / 10000",
    "warm_calibration_row_bucket": "0-999 / 10000 within remaining train artists with >=8 rows",
    "warm_test_row_bucket": "1000-1999 / 10000 within remaining train artists with >=8 rows"
  }
}
```

## 3. 정책별 반복 지표

| route | policy | metric | mean | std | min | median | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold | baseline_retrained_lgbm_quantile | MdAPE | 0.3276 | 0.0350 | 0.2613 | 0.3372 | 0.3647 |
| cold | baseline_retrained_lgbm_quantile | MAPE | 0.6301 | 0.2092 | 0.4756 | 0.5600 | 1.0436 |
| cold | baseline_retrained_lgbm_quantile | p95_APE | 2.0126 | 0.9604 | 1.3790 | 1.4739 | 3.9087 |
| cold | baseline_retrained_lgbm_quantile | RMSE_log | 0.6454 | 0.0674 | 0.5904 | 0.6073 | 0.7749 |
| cold | baseline_retrained_lgbm_quantile | over_3x_n | 100.6000 | 46.0851 | 57.0000 | 77.0000 | 187.0000 |
| cold | baseline_retrained_lgbm_quantile | under_1_3x_n | 92.2000 | 17.4287 | 75.0000 | 85.0000 | 119.0000 |
| cold | expert_cause_aware_correction | MdAPE | 0.3290 | 0.0359 | 0.2606 | 0.3354 | 0.3637 |
| cold | expert_cause_aware_correction | MAPE | 0.6316 | 0.2073 | 0.4717 | 0.5639 | 1.0395 |
| cold | expert_cause_aware_correction | p95_APE | 2.0025 | 0.9359 | 1.3727 | 1.4882 | 3.8461 |
| cold | expert_cause_aware_correction | RMSE_log | 0.6460 | 0.0683 | 0.5897 | 0.6082 | 0.7773 |
| cold | expert_cause_aware_correction | over_3x_n | 100.6000 | 47.4283 | 54.0000 | 78.0000 | 188.0000 |
| cold | expert_cause_aware_correction | under_1_3x_n | 87.8000 | 15.7277 | 74.0000 | 84.0000 | 118.0000 |
| warm | baseline_retrained_huber | MdAPE | 0.1716 | 0.0056 | 0.1640 | 0.1742 | 0.1789 |
| warm | baseline_retrained_huber | MAPE | 0.3582 | 0.0727 | 0.2954 | 0.3275 | 0.4956 |
| warm | baseline_retrained_huber | p95_APE | 0.9409 | 0.0317 | 0.9042 | 0.9266 | 0.9913 |
| warm | baseline_retrained_huber | RMSE_log | 0.4695 | 0.0430 | 0.4122 | 0.4641 | 0.5369 |
| warm | baseline_retrained_huber | over_3x_n | 38.6000 | 7.1162 | 26.0000 | 40.0000 | 47.0000 |
| warm | baseline_retrained_huber | under_1_3x_n | 43.0000 | 7.2664 | 34.0000 | 45.0000 | 54.0000 |
| warm | expert_cause_aware_correction | MdAPE | 0.1727 | 0.0056 | 0.1657 | 0.1737 | 0.1808 |
| warm | expert_cause_aware_correction | MAPE | 0.3602 | 0.0753 | 0.2958 | 0.3269 | 0.5030 |
| warm | expert_cause_aware_correction | p95_APE | 0.9435 | 0.0329 | 0.9073 | 0.9270 | 0.9974 |
| warm | expert_cause_aware_correction | RMSE_log | 0.4696 | 0.0431 | 0.4117 | 0.4644 | 0.5366 |
| warm | expert_cause_aware_correction | over_3x_n | 38.8000 | 6.8527 | 26.0000 | 40.0000 | 46.0000 |
| warm | expert_cause_aware_correction | under_1_3x_n | 42.8000 | 7.1666 | 35.0000 | 45.0000 | 54.0000 |

## 4. 기준선 대비 보정 정책 변화량

| route | delta_MdAPE_mean | delta_MdAPE_std | delta_MdAPE_min | delta_MdAPE_max | delta_MAPE_mean | delta_MAPE_std | delta_MAPE_min | delta_MAPE_max | delta_p95_APE_mean | delta_p95_APE_std | delta_p95_APE_min | delta_p95_APE_max | delta_RMSE_log_mean | delta_RMSE_log_std | delta_RMSE_log_min | delta_RMSE_log_max | delta_over_3x_n_mean | delta_over_3x_n_std | delta_over_3x_n_min | delta_over_3x_n_max | delta_under_1_3x_n_mean | delta_under_1_3x_n_std | delta_under_1_3x_n_min | delta_under_1_3x_n_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cold | 0.0014 | 0.0042 | -0.0018 | 0.0084 | 0.0015 | 0.0074 | -0.0041 | 0.0134 | -0.0101 | 0.0324 | -0.0625 | 0.0185 | 0.0006 | 0.0012 | -0.0007 | 0.0025 | 0.0000 | 3.8730 | -5 | 4 | -4.4000 | 8.7636 | -20 | 1 |
| warm | 0.0012 | 0.0010 | -0.0006 | 0.0019 | 0.0020 | 0.0031 | -0.0006 | 0.0074 | 0.0026 | 0.0022 | 0.0004 | 0.0061 | 0.0001 | 0.0006 | -0.0005 | 0.0011 | 0.2000 | 1.0954 | -1 | 2 | -0.2000 | 0.8367 | -1 | 1 |

## 5. seed별 변화량

| seed | route | baseline_MdAPE | expert_MdAPE | delta_MdAPE | baseline_MAPE | expert_MAPE | delta_MAPE | baseline_p95_APE | expert_p95_APE | delta_p95_APE | baseline_RMSE_log | expert_RMSE_log | delta_RMSE_log | baseline_over_3x_n | expert_over_3x_n | delta_over_3x_n | baseline_under_1_3x_n | expert_under_1_3x_n | delta_under_1_3x_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20260605 | cold | 0.2613 | 0.2606 | -0.0007 | 0.4756 | 0.4717 | -0.0039 | 1.4736 | 1.4593 | -0.0143 | 0.5904 | 0.5897 | -0.0007 | 57 | 54 | -3 | 85 | 84 | -1 |
| 20260605 | warm | 0.1742 | 0.1737 | -0.0006 | 0.4956 | 0.5030 | 0.0074 | 0.9042 | 0.9073 | 0.0031 | 0.4934 | 0.4944 | 0.0011 | 47 | 46 | -1 | 45 | 45 | 0 |
| 20260606 | cold | 0.3430 | 0.3514 | 0.0084 | 1.0436 | 1.0395 | -0.0041 | 3.9087 | 3.8461 | -0.0625 | 0.7749 | 0.7773 | 0.0025 | 187 | 188 | 1 | 76 | 77 | 1 |
| 20260606 | warm | 0.1789 | 0.1808 | 0.0019 | 0.3650 | 0.3665 | 0.0015 | 0.9913 | 0.9974 | 0.0061 | 0.5369 | 0.5366 | -0.0003 | 43 | 43 | 0 | 54 | 54 | 0 |
| 20260607 | cold | 0.3318 | 0.3337 | 0.0019 | 0.5601 | 0.5735 | 0.0134 | 1.4739 | 1.4882 | 0.0143 | 0.6073 | 0.6078 | 0.0005 | 75 | 78 | 3 | 106 | 86 | -20 |
| 20260607 | warm | 0.1660 | 0.1673 | 0.0014 | 0.2954 | 0.2958 | 0.0003 | 0.9266 | 0.9270 | 0.0004 | 0.4122 | 0.4117 | -0.0005 | 26 | 26 | 0 | 34 | 35 | 1 |
| 20260608 | cold | 0.3372 | 0.3354 | -0.0018 | 0.5112 | 0.5094 | -0.0018 | 1.3790 | 1.3727 | -0.0063 | 0.6472 | 0.6471 | -0.0001 | 77 | 72 | -5 | 119 | 118 | -1 |
| 20260608 | warm | 0.1746 | 0.1762 | 0.0016 | 0.3073 | 0.3087 | 0.0014 | 0.9198 | 0.9215 | 0.0017 | 0.4641 | 0.4644 | 0.0003 | 37 | 39 | 2 | 46 | 45 | -1 |
| 20260609 | cold | 0.3647 | 0.3637 | -0.0011 | 0.5600 | 0.5639 | 0.0039 | 1.8279 | 1.8464 | 0.0185 | 0.6072 | 0.6082 | 0.0010 | 107 | 111 | 4 | 75 | 74 | -1 |
| 20260609 | warm | 0.1640 | 0.1657 | 0.0017 | 0.3275 | 0.3269 | -0.0006 | 0.9626 | 0.9642 | 0.0016 | 0.4408 | 0.4410 | 0.0002 | 40 | 40 | 0 | 36 | 35 | -1 |

## 6. split 크기

| seed | train | warm_calibration | warm_test | cold_calibration | cold_test |
| --- | --- | --- | --- | --- | --- |
| 20260605 | 24875 | 2449 | 2349 | 2166 | 2053 |
| 20260606 | 23484 | 2201 | 2167 | 3522 | 2518 |
| 20260607 | 24406 | 2441 | 2447 | 1874 | 2724 |
| 20260608 | 24402 | 2318 | 2410 | 2258 | 2504 |
| 20260609 | 24093 | 2342 | 2324 | 2575 | 2558 |

## 7. 해석 기준

- `delta_*`가 음수이면 보정 정책이 기준선보다 개선
- Cold에서 `under_1_3x_n` 증가가 반복되면 과소 예측 리스크가 커진 것으로 해석
- 이 실험은 모델을 다시 학습하는 artist-level 검증이므로, 이전 보정값 재분할 검증보다 최종 채택 판단에 더 가깝다

## 8. 실행 결론

- Warm 재학습 기준선은 평균 MdAPE `0.1716`, MAPE `0.3582`, p95_APE `0.9409`였다.
- Warm 원인별 보정 적용 후 평균 MdAPE `0.1727`, MAPE `0.3602`, p95_APE `0.9435`로 기준선보다 좋아지지 않았다.
- Cold 재학습 기준선은 평균 MdAPE `0.3276`, MAPE `0.6301`, p95_APE `2.0126`였다.
- Cold 원인별 보정 적용 후 평균 MdAPE `0.3290`, MAPE `0.6316`, p95_APE `2.0025`로 p95는 소폭 좋아졌지만 MdAPE/MAPE가 나빠졌다.
- 따라서 이번 원인별 보정/라우팅 후보는 v0.1 기본 정책으로 바로 채택하지 않는다.
- 기존 v0.1 Warm 1순위인 `PP-SVC3 70:30 결합`은 bootstrap 검증에서 개선 신호가 강하지만, 이번 스크립트의 재학습 검증 대상은 아니다.
- 기존 v0.1 Cold 기준인 `PP-Y18 LightGBM Quantile + qwidth 보정`은 `PP-Y21`에서 예측값 재사용 기준 반복 holdout 검증을 통과했지만, 모델 재학습 포함 검증은 별도 보강 대상이다.
- 이번 결과는 “추가 보정 정책을 붙이면 무조건 좋아진다”가 아니라, 모델을 다시 학습하면 보정 효과가 줄거나 방향이 바뀔 수 있음을 보여준다.
