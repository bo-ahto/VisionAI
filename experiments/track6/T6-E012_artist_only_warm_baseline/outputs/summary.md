# T6-E012 결과 요약

- 실험명: 작가명 only Warm 기준 실험
- 가설: Warm에서는 작가명만으로도 작가별 기본 가격대를 상당 부분 설명할 수 있다.
- 결론: 작가명 단독은 Warm 기본 가격대 설명력이 있으며, 크기 피처와 결합할 필요가 있음.

## 결과 지표

| experiment_id | variant | test_name | n | model | cat_features | num_features | median_ape | p95_ape | mape | within_30 | within_50 | rmse_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T6-E012 | artist_only | cold_test | 3005 | Ridge Hedonic Linear Regression | artist_name_ko | - | 0.7585 | 8.6608 | 1.9102 | 0.1820 | 0.3251 | 1.2206 |
| T6-E012 | artist_only | warm_test | 2445 | Ridge Hedonic Linear Regression | artist_name_ko | - | 0.4830 | 2.4741 | 0.7909 | 0.3198 | 0.5166 | 0.8185 |
