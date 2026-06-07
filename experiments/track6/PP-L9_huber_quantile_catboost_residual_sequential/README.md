# PP-L9 Huber-Quantile-CatBoost residual 순차 학습

- 실행 시각: `2026-06-02T13:51:09`
- 데이터 기준: `data/track6_split` 고정 train / validation / test
- 기준 피처: `data/track6/artifacts/track6_artifact_manifest.json`의 Warm Huber, Cold CatBoost 피처셋
- 보정/경계/가중치/라우팅 기준은 validation에서 산정 후 test에 그대로 적용

## Validation 결과

| 후보 | scope | MdAPE | MAPE | p95_APE | RMSE_log | n |
|---|---|---:|---:|---:|---:|---:|
| `PP-L9_warm_huber_quantile_residual_catboost_remaining` | `warm` | `0.1824` | `0.3294` | `1.1614` | `0.4863` | `519` |
| `B0_Warm_Huber` | `warm` | `0.2126` | `0.4167` | `1.3194` | `0.6446` | `519` |
| `B1_Cold_CatBoost` | `cold` | `0.4370` | `0.7606` | `2.5140` | `0.7153` | `2753` |
| `PP-L9_cold_huber_quantile_residual_catboost_remaining` | `cold` | `0.4770` | `0.8122` | `2.7049` | `0.7707` | `2753` |

## 통계 검증 요약

- `mean_ape_delta`는 후보 APE - 기준 APE이다. 음수이면 후보가 평균 절대비율오차를 줄인 것이다.
- bootstrap CI는 validation paired bootstrap 기준이다.

| 후보 | scope | 기준 | mean delta | CI low | CI high | Wilcoxon p |
|---|---|---|---:|---:|---:|---:|
| `PP-L9_cold_huber_quantile_residual_catboost_remaining` | `cold` | `B1_Cold_CatBoost` | `0.0516` | `0.0386` | `0.0662` | `0.0000` |
| `PP-L9_warm_huber_quantile_residual_catboost_remaining` | `warm` | `B0_Warm_Huber` | `-0.0872` | `-0.1234` | `-0.0487` | `0.0000` |

## 구간 기준

- `warm` `validation_residual_width_33_66`: low_cut=`0.663160`, high_cut=`1.070025`
- `cold` `validation_residual_width_33_66`: low_cut=`1.523337`, high_cut=`2.008211`
