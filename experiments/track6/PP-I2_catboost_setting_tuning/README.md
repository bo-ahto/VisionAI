# PP-I2 CatBoost 설정값 조정

- 목적: 최종 후보로 남길 설정, 보정 강도, 라우팅 기준, 통합 후보를 같은 기준으로 확인한다.
- 기준: validation 기준으로 선택하고 test 결과는 재현성 확인으로만 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `baseline_depth6_lr0.04_l2_6` | `catboost_setting_grid` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |
| `cold` | `depth7_lr0.03_l2_10` | `catboost_setting_grid` | `0.4197` | `0.7289` | `2.1581` | `0.7031` |
| `cold` | `depth6_lr0.03_l2_8` | `catboost_setting_grid` | `0.4312` | `0.7441` | `2.3251` | `0.7093` |
| `cold` | `depth5_lr0.04_l2_8` | `catboost_setting_grid` | `0.4374` | `0.7678` | `2.7233` | `0.7213` |
