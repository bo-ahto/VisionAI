# PP-L5 Huber + Quantile + CatBoost 라우팅

- 실행 시각: `2026-06-02T13:51:07`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L5_warm_low_huber_mid_calibrated_high_residual` | `warm` | `0.2252` | `0.4096` | `1.3225` | `0.5453` | `519` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L5_cold_low_huber_mid_calibrated_high_residual` | `cold` | `0.4491` | `0.8465` | `3.1908` | `0.7777` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L5_cold_low_huber_mid_calibrated_high_residual` | `cold` | `B1_Cold_CatBoost` | `0.0859` | `0.0692` | `0.1023` | `0.0000` |
| `PP-L5_cold_low_huber_mid_calibrated_high_residual` | `cold` | `B1_Cold_CatBoost` | `0.2463` | `0.2069` | `0.2888` | `nan` |
| `PP-L5_cold_low_huber_mid_calibrated_high_residual` | `cold` | `B1_Cold_CatBoost` | `-0.0207` | `-0.0297` | `-0.0111` | `nan` |
| `PP-L5_cold_low_huber_mid_calibrated_high_residual` | `cold` | `B1_Cold_CatBoost` | `0.0316` | `0.0175` | `0.0477` | `nan` |
| `PP-L5_warm_low_huber_mid_calibrated_high_residual` | `warm` | `B0_Warm_Huber` | `-0.0071` | `-0.0343` | `0.0230` | `0.0021` |
| `PP-L5_warm_low_huber_mid_calibrated_high_residual` | `warm` | `B0_Warm_Huber` | `-0.0162` | `-0.0994` | `0.0731` | `nan` |
| `PP-L5_warm_low_huber_mid_calibrated_high_residual` | `warm` | `B0_Warm_Huber` | `0.0000` | `0.0000` | `0.0000` | `nan` |
| `PP-L5_warm_low_huber_mid_calibrated_high_residual` | `warm` | `B0_Warm_Huber` | `-0.0048` | `-0.0072` | `-0.0026` | `nan` |

## 구간 기준

