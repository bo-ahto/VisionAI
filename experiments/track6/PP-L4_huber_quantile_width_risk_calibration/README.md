# PP-L4 Huber + Quantile width 위험 구간 보정

- 실행 시각: `2026-06-02T13:51:07`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L4_warm_Huber_quantile_width_segment_median` | `warm` | `0.2167` | `0.4116` | `1.3235` | `0.6462` | `519` |
| `PP-L4_cold_Huber_quantile_width_segment_median` | `cold` | `0.4026` | `0.6063` | `1.8607` | `0.7282` | `2753` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L4_cold_Huber_quantile_width_segment_median` | `cold` | `B1_Cold_CatBoost` | `-0.1543` | `-0.1798` | `-0.1234` | `0.0000` |
| `PP-L4_cold_Huber_quantile_width_segment_median` | `cold` | `B1_Cold_CatBoost` | `-0.4188` | `-0.5068` | `-0.3433` | `nan` |
| `PP-L4_cold_Huber_quantile_width_segment_median` | `cold` | `B1_Cold_CatBoost` | `-0.0772` | `-0.0894` | `-0.0639` | `nan` |
| `PP-L4_cold_Huber_quantile_width_segment_median` | `cold` | `B1_Cold_CatBoost` | `0.0316` | `0.0175` | `0.0477` | `nan` |
| `PP-L4_warm_Huber_quantile_width_segment_median` | `warm` | `B0_Warm_Huber` | `-0.0051` | `-0.0068` | `-0.0033` | `0.0022` |
| `PP-L4_warm_Huber_quantile_width_segment_median` | `warm` | `B0_Warm_Huber` | `-0.0116` | `-0.0154` | `-0.0081` | `nan` |
| `PP-L4_warm_Huber_quantile_width_segment_median` | `warm` | `B0_Warm_Huber` | `0.0012` | `0.0005` | `0.0019` | `nan` |
| `PP-L4_warm_Huber_quantile_width_segment_median` | `warm` | `B0_Warm_Huber` | `-0.0048` | `-0.0072` | `-0.0026` | `nan` |

## 구간 기준

- `warm` `validation_quantile_width_33_66`: low_cut=`1.147675`, high_cut=`1.479165`
- `cold` `validation_quantile_width_33_66`: low_cut=`1.557597`, high_cut=`2.118603`
