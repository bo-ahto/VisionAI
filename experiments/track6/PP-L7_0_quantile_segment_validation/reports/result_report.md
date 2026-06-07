# PP-L7-0 Quantile 구간 생성 및 검증

- 실행 시각: `2026-06-02T13:51:08`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L7_0_warm_quantile_q50_segment_view` | `warm` | `0.3231` | `0.4424` | `1.2864` | `0.6058` | `519` |
| `PP-L7_0_cold_quantile_q50_segment_view` | `cold` | `0.4188` | `0.7164` | `2.4828` | `0.7193` | `2753` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L7_0_cold_quantile_q50_segment_view` | `cold` | `B1_Cold_CatBoost` | `-0.0443` | `-0.0630` | `-0.0256` | `0.0000` |
| `PP-L7_0_cold_quantile_q50_segment_view` | `cold` | `B1_Cold_CatBoost` | `-0.0540` | `-0.1214` | `0.0026` | `nan` |
| `PP-L7_0_cold_quantile_q50_segment_view` | `cold` | `B1_Cold_CatBoost` | `-0.0404` | `-0.0486` | `-0.0321` | `nan` |
| `PP-L7_0_cold_quantile_q50_segment_view` | `cold` | `B1_Cold_CatBoost` | `-0.0385` | `-0.0516` | `-0.0246` | `nan` |
| `PP-L7_0_warm_quantile_q50_segment_view` | `warm` | `B0_Warm_Huber` | `0.0257` | `-0.0244` | `0.0800` | `0.0031` |
| `PP-L7_0_warm_quantile_q50_segment_view` | `warm` | `B0_Warm_Huber` | `0.0962` | `-0.0101` | `0.2150` | `nan` |
| `PP-L7_0_warm_quantile_q50_segment_view` | `warm` | `B0_Warm_Huber` | `0.0322` | `-0.0105` | `0.0857` | `nan` |
| `PP-L7_0_warm_quantile_q50_segment_view` | `warm` | `B0_Warm_Huber` | `-0.0538` | `-0.1633` | `0.0319` | `nan` |

## 구간 기준

- `warm` `validation_quantile_width_33_66`: low_cut=`1.147675`, high_cut=`1.479165`
- `cold` `validation_quantile_width_33_66`: low_cut=`1.557597`, high_cut=`2.118603`
