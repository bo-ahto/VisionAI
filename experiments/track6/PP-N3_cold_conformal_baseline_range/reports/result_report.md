# PP-N3 Cold Conformal prediction 보정

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `cold` | `range_80pct_conformal` | `baseline_point_with_conformal_range` | `0.3851` | `0.7169` | `2.0250` | `0.6901` | range_coverage=0.7999; median_range_ratio=4.9383 |
| `cold` | `range_90pct_conformal` | `baseline_point_with_conformal_range` | `0.3851` | `0.7169` | `2.0250` | `0.6901` | range_coverage=0.8997; median_range_ratio=8.3790 |
