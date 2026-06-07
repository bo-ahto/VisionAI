# PP-M2 Warm target-encoded artist prior + Huber

- 목적: 모델별 장점을 분리해 추가 개선 가능성을 확인한다.
- 기준: validation에서 후보를 판단하고 test는 재현성 확인으로 기록한다.

## Validation 결과

| scope | 후보 | 정책 | MdAPE | MAPE | p95_APE | RMSE_log | 추가정보 |
|---|---|---|---:|---:|---:|---:|---|
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
| `warm` | `baseline_warm_huber` | `baseline` | `0.2126` | `0.4167` | `1.3194` | `0.6446` |  |
| `warm` | `artist_prior_huber_smoothing_3` | `artist_prior_feature_huber` | `0.2193` | `0.3937` | `1.1388` | `0.5922` | smoothing=3.0000 |
| `warm` | `artist_prior_huber_smoothing_8` | `artist_prior_feature_huber` | `0.2194` | `0.3937` | `1.1394` | `0.5922` | smoothing=8.0000 |
| `warm` | `artist_prior_huber_smoothing_20` | `artist_prior_feature_huber` | `0.2194` | `0.3937` | `1.1384` | `0.5921` | smoothing=20.0000 |
