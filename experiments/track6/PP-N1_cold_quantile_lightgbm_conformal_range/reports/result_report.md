# PP-N1 Cold Quantile LightGBM 범위 보수화

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `baseline_cold_lightgbm` | `baseline` | `0.3851` | `0.7169` | `2.0250` | `0.6901` |  |
| `cold` | `quantile_lgbm_q50_conformal_range` | `quantile_q50_with_conformal_range` | `0.3972` | `0.6618` | `1.7709` | `0.6798` | range_coverage=0.8042; median_range_ratio=5.0923 |
