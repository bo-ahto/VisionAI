# PP-M3 Warm 작가 기준선 + CatBoost residual

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
| `warm` | `artist_median_plus_catboost_residual` | `artist_baseline_then_catboost_residual` | `0.3512` | `0.5411` | `1.6900` | `0.6152` |  |
