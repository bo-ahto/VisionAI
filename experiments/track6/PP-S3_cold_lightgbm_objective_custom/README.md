# PP-S3 Cold LightGBM 목적함수 커스텀

- 목적: 모델 순서 변경, 목적함수 커스텀, 메타 조합이 기존 PP-Q/PP-R 이후 추가 개선을 주는지 확인한다.
- 근거: CatBoost/LightGBM의 MAPE/Quantile/Huber 목적함수와 stacking의 모델 출력값 결합 구조를 Track6 후보에 적용한다.
- 기준: 가중치, residual 모델, meta 모델, 정책 선택은 validation에서 정하고 test에는 그대로 적용한다.

## Metrics

| 후보 | split | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `lgbm_objective_huber` | `test` | `lightgbm_objective_custom` | `0.4768` | `1.2784` | `4.3209` | `0.9435` |
| `lgbm_objective_quantile` | `test` | `lightgbm_objective_custom` | `0.4823` | `1.2731` | `4.0721` | `0.9468` |
| `lgbm_objective_mape` | `test` | `lightgbm_objective_custom` | `0.4825` | `1.2217` | `3.7901` | `0.9422` |
| `lgbm_objective_regression` | `test` | `lightgbm_objective_custom` | `0.4909` | `1.4131` | `4.8212` | `0.9687` |
| `lgbm_objective_regression_l1` | `test` | `lightgbm_objective_custom` | `0.4948` | `1.2310` | `3.9891` | `0.9366` |
| `lgbm_objective_huber` | `validation` | `lightgbm_objective_custom` | `0.3832` | `0.6529` | `1.6865` | `0.6703` |
| `lgbm_objective_regression` | `validation` | `lightgbm_objective_custom` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `lgbm_objective_mape` | `validation` | `lightgbm_objective_custom` | `0.3869` | `0.6056` | `1.5839` | `0.6663` |
| `lgbm_objective_quantile` | `validation` | `lightgbm_objective_custom` | `0.3928` | `0.6589` | `1.8027` | `0.6773` |
| `lgbm_objective_regression_l1` | `validation` | `lightgbm_objective_custom` | `0.4085` | `0.6497` | `1.7256` | `0.6778` |
