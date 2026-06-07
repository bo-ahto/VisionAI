# PP-P3 서비스 표시 정책 통합 검증

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `range_90pct_conformal_reference_price_90pct_conformal_range` | `reference_price_90pct_conformal_range` | `0.3851` | `0.7169` | `2.0250` | `0.6901` | range_coverage=0.8997; median_range_ratio=8.3790 |
| `cold` | `quantile_width_model_routing_reference_price_with_wide_range` | `reference_price_with_wide_range` | `0.3875` | `0.6737` | `1.8166` | `0.6786` |  |
| `warm` | `quantile_width_model_routing_point_with_range` | `point_with_range` | `0.1697` | `0.3063` | `0.9460` | `0.4452` |  |
