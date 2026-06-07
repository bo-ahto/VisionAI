# PP-F1 Warm 가격 범위 검증

- 목적: 단일 가격 예측을 서비스에서 어떤 범위와 신뢰도 문구로 보여줄지 검증한다.
- 기준: 범위 폭과 등급 기준은 validation에서 정하고 test에는 그대로 적용한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | 포함률 | 범위비 중앙값 |
|---|---|---|---:|---:|---:|---:|---:|
| `warm` | `baseline_point_prediction` | `point_prediction` | `0.2126` | `0.4167` | `1.3194` | `nan` | `nan` |
| `warm` | `range_70pct` | `global_abs_residual_quantile` | `0.2126` | `0.4167` | `1.3194` | `0.6994` | `2.4309` |
| `warm` | `range_80pct` | `global_abs_residual_quantile` | `0.2126` | `0.4167` | `1.3194` | `0.7996` | `3.3200` |
| `warm` | `range_90pct` | `global_abs_residual_quantile` | `0.2126` | `0.4167` | `1.3194` | `0.8998` | `6.5219` |
