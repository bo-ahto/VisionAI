# PP-N2 Cold CatBoost Quantile 손실 비교

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `catboost_quantile_q50` | `catboost_quantile_q50` | `0.4087` | `0.6591` | `2.0189` | `0.6893` | range_coverage=0.8195; median_range_ratio=5.1760 |
| `cold` | `baseline_cold_catboost` | `baseline` | `0.4194` | `0.7332` | `2.2053` | `0.7037` |  |
