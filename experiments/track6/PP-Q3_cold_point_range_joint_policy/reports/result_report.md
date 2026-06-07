# PP-Q3 Cold 점 예측 + 가격 범위 joint policy

- 목적: 모델별 장점을 조합하고 커스텀해 Cold 성능 개선 가능성을 확인한다.
- 기준: validation에서 선택한 조합/가중치/정책을 test에 그대로 적용한다.

## Validation 결과

| 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | coverage | range ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| `q2_mdape_point__n1_quantile_conformal_range` | `point_range_joint_policy` | `0.3820` | `0.6850` | `1.8897` | `0.6803` | `0.8042` | `5.0923` |
| `q2_mdape_point__n2_catboost_quantile_range` | `point_range_joint_policy` | `0.3820` | `0.6850` | `1.8897` | `0.6803` | `0.8195` | `5.1760` |
| `q2_mdape_point__n3_conformal_80_range` | `point_range_joint_policy` | `0.3820` | `0.6850` | `1.8897` | `0.6803` | `0.7999` | `4.9383` |
| `q2_mdape_point__n3_conformal_90_range` | `point_range_joint_policy` | `0.3820` | `0.6850` | `1.8897` | `0.6803` | `0.8997` | `8.3790` |
| `q1_mdape_point__n1_quantile_conformal_range` | `point_range_joint_policy` | `0.3875` | `0.6737` | `1.8166` | `0.6786` | `0.8042` | `5.0923` |
| `q1_mdape_point__n2_catboost_quantile_range` | `point_range_joint_policy` | `0.3875` | `0.6737` | `1.8166` | `0.6786` | `0.8195` | `5.1760` |
| `q1_mdape_point__n3_conformal_80_range` | `point_range_joint_policy` | `0.3875` | `0.6737` | `1.8166` | `0.6786` | `0.7999` | `4.9383` |
| `q1_mdape_point__n3_conformal_90_range` | `point_range_joint_policy` | `0.3875` | `0.6737` | `1.8166` | `0.6786` | `0.8997` | `8.3790` |
| `q1_mape_point__n1_quantile_conformal_range` | `point_range_joint_policy` | `0.3962` | `0.6544` | `1.7209` | `0.6773` | `0.8042` | `5.0923` |
| `q1_mape_point__n2_catboost_quantile_range` | `point_range_joint_policy` | `0.3962` | `0.6544` | `1.7209` | `0.6773` | `0.8195` | `5.1760` |
| `q1_mape_point__n3_conformal_80_range` | `point_range_joint_policy` | `0.3962` | `0.6544` | `1.7209` | `0.6773` | `0.7999` | `4.9383` |
| `q1_mape_point__n3_conformal_90_range` | `point_range_joint_policy` | `0.3962` | `0.6544` | `1.7209` | `0.6773` | `0.8997` | `8.3790` |
| `q2_mape_point__n1_quantile_conformal_range` | `point_range_joint_policy` | `0.3974` | `0.6293` | `1.7765` | `0.6710` | `0.8042` | `5.0923` |
| `q2_mape_point__n2_catboost_quantile_range` | `point_range_joint_policy` | `0.3974` | `0.6293` | `1.7765` | `0.6710` | `0.8195` | `5.1760` |
| `q2_mape_point__n3_conformal_80_range` | `point_range_joint_policy` | `0.3974` | `0.6293` | `1.7765` | `0.6710` | `0.7999` | `4.9383` |
| `q2_mape_point__n3_conformal_90_range` | `point_range_joint_policy` | `0.3974` | `0.6293` | `1.7765` | `0.6710` | `0.8997` | `8.3790` |
