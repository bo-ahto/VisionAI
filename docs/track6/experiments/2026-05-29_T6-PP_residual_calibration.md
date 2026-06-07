# T6-PP residual calibration

- 날짜: `2026-05-29`
- 목적: Warm Huber / Cold CatBoost+LightGBM 후보의 validation residual 보정 효과 검증
- 원칙: validation 예측에서만 보정값을 만들고 test에는 고정 적용
- 결과 CSV: `data/track6/results/t6_pp_residual_calibration_metrics.csv`
- 보정 규칙 CSV: `data/track6/results/t6_pp_residual_calibration_rules.csv`

## Best Test Result

| scope | model | best method | baseline MdAPE | best MdAPE | baseline p95 | best p95 | decision |
|---|---|---|---:|---:|---:|---:|---|
| `cold_catboost` | `catboost_cold__base_medium_shape` | `medium_category_median_residual` | `0.4839` | `0.4880` | `4.7974` | `4.7974` | 보류 |
| `cold_lightgbm` | `lightgbm_cold__base_support_size` | `size_bucket_median_residual` | `0.4859` | `0.4873` | `4.7612` | `4.3762` | 보류 |
| `cold_tail` | `lightgbm_cold__base_large_flags` | `medium_category_median_residual` | `0.4921` | `0.4888` | `4.7924` | `4.2089` | 채택 |
| `warm` | `huber_warm_artist__base_existing_combo` | `pred_bin_median_residual` | `0.2274` | `0.2211` | `2.0130` | `2.0006` | 채택 |

## Decision Rule

- 채택: MdAPE가 개선되고 p95_APE가 악화되지 않는 경우
- 보류: MdAPE만 좋아지고 p95_APE가 악화되는 경우
- 중단: baseline보다 MdAPE가 나빠지는 경우
