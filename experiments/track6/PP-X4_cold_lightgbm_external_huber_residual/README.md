# PP-X4 Cold LightGBM 전시/갤러리 + Huber 잔차 보정

- 목적: 갤러리 티어와 개인전/전시 활동 피처를 현재 최신 Cold 후보 구조에서 재검증한다.
- 기준: 기존 Track6 split은 바꾸지 않고 `_track6_row_id` 기준으로 외부 피처만 추가한다.

## Test 결과 상위

| 후보 | MdAPE | MAPE | p95_APE | RMSE_log | 정책 |
|---|---:|---:|---:|---:|---|
| `base_lightgbm_quantile_exhibition_gallery_interaction` | 0.4487 | 1.0807 | 3.6800 | 0.8827 | `external_lightgbm_quantile_base` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.15_s0.5` | 0.4512 | 1.0645 | 3.6861 | 0.8853 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.15_s0.75` | 0.4587 | 1.0595 | 3.6877 | 0.8883 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.15_s1` | 0.4588 | 1.0564 | 3.6780 | 0.8925 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.25_s0.5` | 0.4597 | 1.0670 | 3.6974 | 0.8891 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.35_s0.5` | 0.4668 | 1.0738 | 3.6975 | 0.8932 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.25_s0.75` | 0.4683 | 1.0665 | 3.7091 | 0.8962 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.35_s0.75` | 0.4683 | 1.0803 | 3.6200 | 0.9046 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.25_s1` | 0.4714 | 1.0704 | 3.6781 | 0.9058 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.5_s0.5` | 0.4714 | 1.0809 | 3.6781 | 0.8983 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.35_s1` | 0.4722 | 1.0947 | 3.6780 | 0.9199 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.5_s0.75` | 0.4733 | 1.0981 | 3.5860 | 0.9155 | `external_lightgbm_quantile_huber_residual` |
| `lightgbm_quantile_exhibition_gallery_interaction_huber_residual_cap0.5_s1` | 0.4855 | 1.1288 | 3.6780 | 0.9385 | `external_lightgbm_quantile_huber_residual` |

## 설정/피처 맵

| experiment_id | base_candidate | residual_model | cap | strength | hypothesis |
| --- | --- | --- | --- | --- | --- |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.15 | 0.5 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.15 | 0.75 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.15 | 1 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.25 | 0.5 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.25 | 0.75 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.25 | 1 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.35 | 0.5 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.35 | 0.75 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.35 | 1 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.5 | 0.5 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.5 | 0.75 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
| PP-X4 | lightgbm_quantile_exhibition_gallery_interaction | HuberRegressor | 0.5 | 1 | 전시/갤러리 피처가 포함된 중앙값 예측 이후 남은 반복 오차를 완만하게 보정 |
