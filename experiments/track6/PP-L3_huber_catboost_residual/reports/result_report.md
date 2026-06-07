# PP-L3 Huber 선행 + CatBoost residual 보정

- 실행 시각: `2026-06-02T13:51:06`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `B4_warm_Huber_CatBoost_residual` | `warm` | `0.2198` | `0.3752` | `1.2590` | `0.5205` | `519` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `B4_cold_Huber_CatBoost_residual` | `cold` | `0.4558` | `0.8541` | `3.1908` | `0.7864` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `B4_cold_Huber_CatBoost_residual` | `cold` | `B1_Cold_CatBoost` | `0.0935` | `0.0767` | `0.1096` | `0.0000` |
| `B4_warm_Huber_CatBoost_residual` | `warm` | `B0_Warm_Huber` | `-0.0415` | `-0.0774` | `-0.0018` | `0.0005` |

## 구간 기준

