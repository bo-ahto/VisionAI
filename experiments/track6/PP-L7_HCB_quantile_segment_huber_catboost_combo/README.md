# PP-L7-HCB Quantile 구간별 Huber + CatBoost 결합

- 실행 시각: `2026-06-02T13:51:09`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L7_HCB_warm_segment_huber_catboost` | `warm` | `0.2212` | `0.4112` | `1.3250` | `0.5457` | `519` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L7_HCB_cold_segment_huber_catboost` | `cold` | `0.4459` | `0.8273` | `3.1908` | `0.7784` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L7_HCB_cold_segment_huber_catboost` | `cold` | `B1_Cold_CatBoost` | `0.0666` | `0.0496` | `0.0828` | `0.0000` |
| `PP-L7_HCB_warm_segment_huber_catboost` | `warm` | `B0_Warm_Huber` | `-0.0055` | `-0.0325` | `0.0247` | `0.1099` |

## 구간 기준

