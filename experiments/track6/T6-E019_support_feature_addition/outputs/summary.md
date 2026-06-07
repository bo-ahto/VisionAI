# T6-E019 결과 요약

- 실험명: 지지체 피처 추가 실험
- 가설: 캔버스/종이/패널 등 지지체 정보는 가격 차이를 설명할 수 있다.
- 결론: Warm 개선폭 0.0021, Cold 개선폭 0.0271. 개선폭과 복잡도를 함께 보고 기본 피처 포함 여부를 판단.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E019 | plus_support | cold_test | 3005 | Ridge Hedonic Linear Regression | support_category, nant_support | ln_estimated_ho | 0.4812 | 2.7746 | 1.0850 | 0.2722 | 0.5155 | 0.8027 |
| T6-E019 | baseline | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E019 | plus_support | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko, support_category, nant_support | ln_estimated_ho | 0.1925 | 0.8206 | 0.3274 | 0.6773 | 0.8556 | 0.4153 |
| T6-E019 | baseline | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho | 0.1946 | 0.8654 | 0.3249 | 0.6777 | 0.8519 | 0.4174 |
