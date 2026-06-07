# PP-L1 CatBoost MAPE 목적 최적화

- 실행 시각: `2026-06-02T13:51:05`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `0.3144` | `0.4303` | `1.2845` | `0.5972` | `519` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `0.3144` | `0.4303` | `1.2845` | `0.5972` | `519` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `0.3144` | `0.4330` | `1.3884` | `0.5767` | `519` |
| `PP-L1_B_eval_metric_MAPE_warm` | `warm` | `0.3144` | `0.4330` | `1.3884` | `0.5767` | `519` |
| `PP-L1_C_low_price_weight_warm` | `warm` | `0.3269` | `0.4307` | `1.2877` | `0.5941` | `519` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `0.4162` | `0.7038` | `2.3873` | `0.7131` | `2753` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `0.4162` | `0.7038` | `2.3873` | `0.7131` | `2753` |
| `PP-L1_C_low_price_weight_cold` | `cold` | `0.4272` | `0.6598` | `2.2242` | `0.6974` | `2753` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L1_B_eval_metric_MAPE_cold` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `B1_Cold_CatBoost` | `0.0000` | `0.0000` | `0.0000` | `1.0000` |
| `PP-L1_B_eval_metric_MAPE_cold` | `cold` | `B1_Cold_CatBoost` | `0.0000` | `0.0000` | `0.0000` | `1.0000` |
| `PP-L1_C_low_price_weight_cold` | `cold` | `B1_Cold_CatBoost` | `-0.1008` | `-0.1134` | `-0.0882` | `0.0000` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `B1_Cold_CatBoost` | `-0.0568` | `-0.0756` | `-0.0390` | `0.0000` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `B1_Cold_CatBoost` | `-0.0568` | `-0.0756` | `-0.0390` | `0.0000` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `B0_Warm_Huber` | `0.0163` | `-0.0323` | `0.0647` | `0.0035` |
| `PP-L1_B_eval_metric_MAPE_warm` | `warm` | `B0_Warm_Huber` | `0.0163` | `-0.0323` | `0.0647` | `0.0035` |
| `PP-L1_C_low_price_weight_warm` | `warm` | `B0_Warm_Huber` | `0.0140` | `-0.0346` | `0.0647` | `0.0019` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `B0_Warm_Huber` | `0.0136` | `-0.0359` | `0.0664` | `0.0127` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `B0_Warm_Huber` | `0.0136` | `-0.0359` | `0.0664` | `0.0127` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_warm` | `warm` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_A_existing_CatBoost_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_MAE_loss_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |
| `PP-L1_D_Quantile_050_cold` | `cold` | `` | `nan` | `nan` | `nan` | `nan` |

## 구간 기준

