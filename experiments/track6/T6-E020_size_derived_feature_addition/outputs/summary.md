# T6-E020 결과 요약

- 실험명: 크기 파생 피처 추가 실험
- 가설: 호수 외 면적, 가로/세로, 비율 피처가 추가 설명력을 줄 수 있다.
- 결론: Warm 개선폭 0.0145, Cold 개선폭 0.0027. 개선폭과 복잡도를 함께 보고 기본 피처 포함 여부를 판단.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E020 | plus_width_height_aspect | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho, width_cm, height_cm, aspect_ratio | 0.5056 | 2.8659 | 1.0054 | 0.2752 | 0.4932 | 0.8260 |
| T6-E020 | baseline | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E020 | all_size | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho, log_area, width_cm, height_cm, aspect_ratio | 0.5274 | 2.6062 | 1.0007 | 0.2646 | 0.4725 | 0.8258 |
| T6-E020 | plus_log_area | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho, log_area | 0.5280 | 2.5948 | 0.9670 | 0.2656 | 0.4689 | 0.8202 |
| T6-E020 | all_size | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho, log_area, width_cm, height_cm, aspect_ratio | 0.1801 | 0.8104 | 0.3106 | 0.7051 | 0.8703 | 0.4033 |
| T6-E020 | plus_log_area | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho, log_area | 0.1805 | 0.8290 | 0.3115 | 0.7035 | 0.8650 | 0.4048 |
| T6-E020 | plus_width_height_aspect | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho, width_cm, height_cm, aspect_ratio | 0.1817 | 0.8258 | 0.3159 | 0.6973 | 0.8642 | 0.4076 |
| T6-E020 | baseline | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho | 0.1946 | 0.8654 | 0.3249 | 0.6777 | 0.8519 | 0.4174 |
