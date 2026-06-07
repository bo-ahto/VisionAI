# T6-E018 결과 요약

- 실험명: 재료 피처 추가 실험
- 가설: 재료 정보는 작품 가격 예측에서 크기 외 추가 설명력을 제공한다.
- 결론: Warm 개선폭 0.0000, Cold 개선폭 0.0620. 개선폭과 복잡도를 함께 보고 기본 피처 포함 여부를 판단.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E018 | plus_material | cold_test | 3005 | Ridge Hedonic Linear Regression | medium_category, nant_material_idx, nant_tool | ln_estimated_ho | 0.4463 | 2.8255 | 1.0100 | 0.3012 | 0.5484 | 0.8156 |
| T6-E018 | baseline | cold_test | 3005 | Ridge Hedonic Linear Regression | - | ln_estimated_ho | 0.5083 | 2.8076 | 0.9455 | 0.2722 | 0.4902 | 0.8191 |
| T6-E018 | baseline | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | ln_estimated_ho | 0.1946 | 0.8654 | 0.3249 | 0.6777 | 0.8519 | 0.4174 |
| T6-E018 | plus_material | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko, medium_category, nant_material_idx, nant_tool | ln_estimated_ho | 0.1947 | 0.8427 | 0.3237 | 0.6810 | 0.8511 | 0.4109 |
