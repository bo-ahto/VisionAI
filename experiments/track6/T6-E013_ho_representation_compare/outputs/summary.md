# T6-E013 결과 요약

- 실험명: 호수 표현 방식 비교
- 가설: 호수는 원값보다 로그값, 구간값, 대형 플래그 등으로 표현할 때 더 안정적일 수 있다.
- 결론: 호수 표현은 Warm `ho_log_bucket_flags`, Cold `ho_log`가 가장 안정적임.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E013 | ho_log | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E013 | ho_log_bucket_flags | cold_test | 3005 | Ridge Hedonic Linear Regression | ho_bucket | ln_estimated_ho, is_large_ho, is_extra_large_ho | 0.5259 | 2.7463 | 0.9655 | 0.2689 | 0.4839 | 0.8215 |
| T6-E013 | ho_bucket | cold_test | 3005 | Ridge Hedonic Linear Regression | ho_bucket | - | 0.5414 | 2.7574 | 1.0381 | 0.2629 | 0.4346 | 0.8706 |
| T6-E013 | ho_raw | cold_test | 3005 | Ridge Hedonic Linear Regression | - | estimated_ho | 0.5670 | 4.9249 | 6.9017 | 0.2905 | 0.4489 | 1.0209 |
| T6-E013 | large_flags | cold_test | 3005 | Ridge Hedonic Linear Regression | - | is_large_ho, is_extra_large_ho | 0.5877 | 5.8279 | 1.3084 | 0.2413 | 0.4359 | 0.9909 |
| T6-E013 | ho_log_bucket_flags | warm_test | 2445 | Ridge Hedonic Linear Regression | ho_bucket | ln_estimated_ho, is_large_ho, is_extra_large_ho | 0.5306 | 2.6877 | 0.8559 | 0.3055 | 0.4765 | 0.8875 |
| T6-E013 | ho_bucket | warm_test | 2445 | Ridge Hedonic Linear Regression | ho_bucket | - | 0.5378 | 2.9153 | 0.9048 | 0.2879 | 0.4630 | 0.9079 |
| T6-E013 | ho_raw | warm_test | 2445 | Ridge Hedonic Linear Regression | - | estimated_ho | 0.5423 | 4.1302 | 2.6168 | 0.2875 | 0.4597 | 1.0355 |
| T6-E013 | ho_log | warm_test | 2445 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5431 | 2.6801 | 0.8577 | 0.3076 | 0.4695 | 0.8938 |
| T6-E013 | large_flags | warm_test | 2445 | Ridge Hedonic Linear Regression | - | is_large_ho, is_extra_large_ho | 0.5936 | 4.1726 | 1.1027 | 0.2524 | 0.4258 | 1.0306 |
