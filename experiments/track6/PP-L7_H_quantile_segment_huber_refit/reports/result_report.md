# PP-L7-H Quantile 구간별 Huber 상세 학습

- 실행 시각: `2026-06-02T13:51:08`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `PP-L7-H_warm_segment_huber_refit` | `warm` | `0.2430` | `0.4812` | `1.4643` | `0.6609` | `519` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L7-H_cold_segment_huber_refit` | `cold` | `0.4381` | `0.8151` | `3.2200` | `0.7591` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L7-H_cold_segment_huber_refit` | `cold` | `B1_Cold_CatBoost` | `0.0544` | `0.0224` | `0.0872` | `0.0010` |
| `PP-L7-H_warm_segment_huber_refit` | `warm` | `B0_Warm_Huber` | `0.0645` | `0.0203` | `0.1190` | `0.5654` |

## 구간 기준

