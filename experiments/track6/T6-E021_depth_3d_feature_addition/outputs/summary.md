# T6-E021 결과 요약

- 실험명: 3D/depth 피처 실험
- 가설: 3D 작품은 면적보다 depth/부피성 피처가 가격 설명에 더 중요할 수 있다.
- 결론: Warm 개선폭 0.0000, Cold 개선폭 0.0615. 개선폭과 복잡도를 함께 보고 기본 피처 포함 여부를 판단.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E021 | plus_depth_3d | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho, depth_cm, has_depth, is_3d_candidate | 0.4468 | 2.9637 | 0.9530 | 0.3354 | 0.5474 | 0.7864 |
| T6-E021 | baseline | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E021 | baseline | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho | 0.1946 | 0.8654 | 0.3249 | 0.6777 | 0.8519 | 0.4174 |
| T6-E021 | plus_depth_3d | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho, depth_cm, has_depth, is_3d_candidate | 0.1970 | 0.8555 | 0.3241 | 0.6781 | 0.8532 | 0.4135 |
