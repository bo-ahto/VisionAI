# T6-E011 결과 요약

- 실험명: 호수 only Warm/Cold 기준 실험
- 가설: 작가명 없이 호수만으로도 Warm/Cold 가격대의 최소 신호를 확인할 수 있다.
- 결론: 호수 단독은 Cold 최소 baseline으로 유지 가능하지만 Warm에서는 작가명 포함 baseline보다 약함.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E011 | ho_only_log | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E011 | ho_only_log | warm_test | 2445 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5431 | 2.6801 | 0.8577 | 0.3076 | 0.4695 | 0.8938 |
