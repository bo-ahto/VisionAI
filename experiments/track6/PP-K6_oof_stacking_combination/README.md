# PP-K6 OOF stacking 조합

- 목적: 기본 후처리 이후 추가 조합 또는 보조 정책이 실제 개선을 주는지 확인한다.
- 기준: 새로 학습한 실험은 validation에서 기준을 정하고 test에 그대로 적용한다. 중복 실험은 기존 PP-L/PP-J 결과를 참조한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log |
|---|---|---|---:|---:|---:|---:|
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |
| `cold` | `ridge_oof_stack_cold_catboost_lightgbm` | `oof_stacking` | `0.3880` | `0.7417` | `2.0858` | `0.6977` |
