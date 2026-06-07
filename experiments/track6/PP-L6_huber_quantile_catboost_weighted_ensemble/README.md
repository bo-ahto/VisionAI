# PP-L6 Huber / Quantile / CatBoost 가중 앙상블

- 실행 시각: `2026-06-02T13:51:07`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `PP-L6_warm_validation_weighted_ensemble` | `warm` | `0.1930` | `0.3563` | `1.1304` | `0.5209` | `519` |
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `B2_warm_Quantile_q50` | `warm` | `0.3231` | `0.4424` | `1.2864` | `0.6058` | `519` |
| `B2_cold_Quantile_q50` | `cold` | `0.4188` | `0.7164` | `2.4828` | `0.7193` | `2753` |
| `PP-L6_cold_validation_weighted_ensemble` | `cold` | `0.4188` | `0.7164` | `2.4828` | `0.7193` | `2753` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `B2_cold_Quantile_q50` | `cold` | `B1_Cold_CatBoost` | `-0.0443` | `-0.0630` | `-0.0256` | `0.0000` |
| `PP-L6_cold_validation_weighted_ensemble` | `cold` | `B1_Cold_CatBoost` | `-0.0443` | `-0.0630` | `-0.0256` | `0.0000` |
| `B2_warm_Quantile_q50` | `warm` | `B0_Warm_Huber` | `0.0257` | `-0.0244` | `0.0800` | `0.0031` |
| `PP-L6_warm_validation_weighted_ensemble` | `warm` | `B0_Warm_Huber` | `-0.0603` | `-0.0904` | `-0.0281` | `0.0000` |
| `B2_warm_Quantile_q50` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_warm_Quantile_q50` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_warm_Quantile_q50` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_warm_Quantile_q50` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_cold_Quantile_q50` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_cold_Quantile_q50` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_cold_Quantile_q50` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `B2_cold_Quantile_q50` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |

## 구간 기준

